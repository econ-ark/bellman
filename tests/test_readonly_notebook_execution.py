"""Tests for the read-only notebook runner (spec 0.3c, task N01).

The runner is exercised against a synthetic git repository built under the
pytest temporary directory: it holds a package one directory above the
notebook, a data sibling the notebook reads through a relative path, and
a `venv` symlink to this repository's virtual environment so that the
runner's rule "invoke the repository's venv/bin/python" is followed
literally. The real repository is never the execution target here.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import nbformat
import pytest

REPO = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO / "applications" / "readonly_notebook_execution.py"
NOTEBOOK_RELATIVE = Path("apps/demo/notebooks/nb.ipynb")


def _load_runner():
    spec = importlib.util.spec_from_file_location("readonly_notebook_execution", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_runner()

if not runner.SANDBOX_EXEC.exists():
    pytest.fail(f"{runner.SANDBOX_EXEC} is absent: N01 has no unsandboxed fallback", pytrace=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.org", *args],
        check=True, capture_output=True, text=True,
    ).stdout


def make_repo(base: Path) -> Path:
    """A synthetic repository: package above the notebook, sibling beside it."""
    repo = base / "synthetic-repo"
    (repo / "packages" / "mypkg").mkdir(parents=True)
    (repo / "packages" / "mypkg" / "__init__.py").write_text("VALUE = 42\n")
    (repo / "apps" / "demo" / "data").mkdir(parents=True)
    (repo / "apps" / "demo" / "data" / "sibling.txt").write_text("sibling-ok\n")
    (repo / "apps" / "demo" / "notebooks").mkdir()
    (repo / "apps" / "demo" / "notebooks" / "helper.txt").write_text("helper\n")
    (repo / "apps" / "other").mkdir()
    (repo / "apps" / "other" / "note.txt").write_text("other\n")
    (repo / "README.md").write_text("synthetic\n")
    os.symlink(str(REPO / "venv"), str(repo / "venv"))

    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "venv", "language": "python"}
    nb.cells.append(nbformat.v4.new_markdown_cell("# Synthetic notebook"))
    nb.cells.append(nbformat.v4.new_code_cell(
        "from pathlib import Path\n"
        "print('SIBLING=' + Path('../data/sibling.txt').read_text().strip())\n"
    ))
    nb.cells.append(nbformat.v4.new_code_cell(
        "import sys\n"
        "from pathlib import Path\n"
        "root = next(p for p in Path.cwd().parents if (p / 'packages' / 'mypkg').exists())\n"
        "sys.path.insert(0, str(root / 'packages'))\n"
        "import mypkg\n"
        "print('PACKAGE_VALUE=' + str(mypkg.VALUE))\n"
        "print('PACKAGE_ROOT=' + str(root))\n"
    ))
    nb.cells.append(nbformat.v4.new_code_cell("print('NO_ID_CELL')\n"))
    nbformat.write(nb, str(repo / NOTEBOOK_RELATIVE))
    # A format-4.5 cell without an id, as several repository notebooks have;
    # nbformat's writer would add one, so the field is removed from the JSON.
    raw = json.loads((repo / NOTEBOOK_RELATIVE).read_text())
    del raw["cells"][3]["id"]
    (repo / NOTEBOOK_RELATIVE).write_text(json.dumps(raw, indent=1))

    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "synthetic repository")
    return repo.resolve()


def _short_tmp(request) -> Path:
    """A short-pathed temporary root: the kernel's Unix sockets live under it,
    and macOS caps a socket path at 104 bytes, which pytest's own tmp paths
    exceed. Removed when the requesting scope ends."""
    root = Path(tempfile.mkdtemp(prefix="n01.", dir="/private/tmp"))
    request.addfinalizer(lambda: shutil.rmtree(root, ignore_errors=True))
    return root


@pytest.fixture(scope="module")
def short_tmp_module(request) -> Path:
    return _short_tmp(request)


@pytest.fixture
def short_tmp(request) -> Path:
    return _short_tmp(request)


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> Path:
    return make_repo(tmp_path_factory.mktemp("n01"))


@pytest.fixture(scope="module")
def completed_run(repo, short_tmp_module):
    """One successful execution shared by the read-only assertions below."""
    out = short_tmp_module / "run"
    result = runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, out)
    return repo, out, result


def _outputs_text(cell) -> str:
    return "".join(o.get("text", "") for o in cell.get("outputs", []) if o.get("output_type") == "stream")


def test_overlay_reproduces_repository_layout(completed_run):
    repo, out, result = completed_run
    overlay = out / "overlay"
    copied = overlay / NOTEBOOK_RELATIVE
    assert copied.is_file() and not copied.is_symlink()
    for real_dir in ("apps", "apps/demo", "apps/demo/notebooks"):
        assert (overlay / real_dir).is_dir() and not (overlay / real_dir).is_symlink()
    for link, target in {
        "packages": repo / "packages",
        "README.md": repo / "README.md",
        "venv": repo / "venv",
        ".git": repo / ".git",
        "apps/other": repo / "apps" / "other",
        "apps/demo/data": repo / "apps" / "demo" / "data",
        "apps/demo/notebooks/helper.txt": repo / "apps" / "demo" / "notebooks" / "helper.txt",
    }.items():
        assert (overlay / link).is_symlink(), link
        assert os.readlink(overlay / link) == str(target), link
    kinds = {entry["path"]: entry["kind"] for entry in result["overlay"]}
    assert kinds[str(NOTEBOOK_RELATIVE)] == "copied-notebook"
    assert kinds["apps"] == "directory" and kinds["packages"] == "symlink"
    for name in ("home", "cache", "runtime"):
        assert (out / name).is_dir()


def test_relative_sibling_and_parent_package_resolve_inside_overlay(completed_run):
    repo, out, result = completed_run
    executed = nbformat.read(str(out / "overlay" / NOTEBOOK_RELATIVE), as_version=4)
    assert "SIBLING=sibling-ok" in _outputs_text(executed.cells[1])
    assert "PACKAGE_VALUE=42" in _outputs_text(executed.cells[2])
    package_root = _outputs_text(executed.cells[2]).split("PACKAGE_ROOT=")[1].strip()
    assert Path(package_root) == (out / "overlay").resolve()
    assert [c["status"] for c in result["cells"]] == ["not-code", "ok", "ok", "ok"]
    assert [c["id"] for c in result["cells"]][3] is None, "the id-less cell is reported without an id"
    assert all(c["id"] for c in result["cells"][:3])


def test_kernel_working_directory_is_the_copied_notebook_directory(completed_run):
    repo, out, result = completed_run
    expected = (out / "overlay" / NOTEBOOK_RELATIVE.parent).resolve()
    assert Path(result["kernel_working_directory"]).resolve() == expected
    assert Path(result["working_directory"]) == expected


def test_environment_paths_lie_under_the_temporary_root(completed_run):
    repo, out, result = completed_run
    root = out.resolve()
    env = result["environment"]
    for name in ("HOME", "TMPDIR", "XDG_CACHE_HOME", "IPYTHONDIR", "JUPYTER_CONFIG_DIR",
                 "JUPYTER_DATA_DIR", "JUPYTER_RUNTIME_DIR", "MPLCONFIGDIR"):
        assert Path(env[name]).is_relative_to(root), name
        assert Path(env[name]).is_dir(), name
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert result["kernel"] == {
        "name": "python3", "transport": "ipc",
        "ipc_socket_prefix": str(root / "runtime" / "kernel"),
        "cell_timeout_seconds": runner.CELL_TIMEOUT_SECONDS,
    }


def test_the_sandbox_matplotlib_cache_holds_the_interpreters_font_cache_files(completed_run):
    repo, out, result = completed_run
    folder = Path(result["environment"]["MPLCONFIGDIR"])
    for cached in runner.matplotlib_font_caches():
        assert (folder / cached.name).read_bytes() == cached.read_bytes(), cached.name


def test_sandbox_profile_is_the_prescribed_text(completed_run):
    repo, out, result = completed_run
    root = out.resolve()
    expected = (
        "(version 1)\n"
        "(deny default)\n"
        '(import "system.sb")\n'
        "(allow process*)\n"
        "(allow file-read*)\n"
        f'(allow file-write* (subpath "{root}"))\n'
        f'(allow network* (local unix-socket (subpath "{root}")) (remote unix-socket (subpath "{root}")))\n'
    )
    assert (out / runner.PROFILE_FILENAME).read_text() == expected
    assert result["sandbox"]["profile"] == expected
    assert result["sandbox"]["profile_sha256"] == hashlib.sha256(expected.encode()).hexdigest()
    canonical = expected.replace(str(root), "<temporary-root>")
    assert result["sandbox"]["canonical_profile_sha256"] == hashlib.sha256(canonical.encode()).hexdigest()
    assert result["sandbox"]["command"][:3] == ["/usr/bin/sandbox-exec", "-f", str(out / runner.PROFILE_FILENAME)]
    assert result["sandbox"]["command"][3] == str(repo / "venv" / "bin" / "python")


def test_source_notebook_and_repository_are_unchanged(completed_run):
    repo, out, result = completed_run
    source = repo / NOTEBOOK_RELATIVE
    assert result["source_notebook_sha256_before"] == result["source_notebook_sha256_after"] == sha256(source)
    assert result["source_notebook_unchanged"] is True
    assert result["repository_unchanged"] is True
    assert result["repository_status_before"]["porcelain"] == []
    assert _git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert nbformat.read(str(source), as_version=4).cells[1].get("outputs") == []


def test_probe_failed_with_permission_error_before_the_first_cell(completed_run):
    repo, out, result = completed_run
    probe = result["probe"]
    assert probe["exception_class"] == "PermissionError"
    assert probe["path"].startswith(str(repo / runner.PROBE_PREFIX))
    assert probe["exists_after"] is False and not Path(probe["path"]).exists()
    assert probe["execution_count"] == 1
    first_code_cell = next(c for c in result["cells"] if c["cell_type"] == "code")
    assert first_code_cell["execution_count"] == 2
    assert result["status"] == "completed" and result["failures"] == []
    assert json.loads((out / runner.RESULT_FILENAME).read_text()) == result


def test_two_equivalent_runs_have_identical_canonical_comparison(completed_run, short_tmp):
    repo, out, result = completed_run
    second = runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, short_tmp / "second")
    assert second["canonical_comparison"] == result["canonical_comparison"]
    assert second["temporary_root"] != result["temporary_root"]
    assert second["probe"]["path"] != result["probe"]["path"]
    canonical = result["canonical_comparison"]
    assert canonical["probe"]["path"] == "<repository>/" + runner.PROBE_PREFIX + "<probe-uuid>"
    assert canonical["working_directory"] == "<temporary-root>/overlay/apps/demo/notebooks"
    assert all(e.get("target", "<repository>").startswith("<repository>") for e in canonical["overlay"])
    assert str(out) not in json.dumps(canonical) and str(repo) not in json.dumps(canonical)


def test_final_cell_is_appended_to_the_copy_only(repo, short_tmp):
    source_text = "print('FINAL_CELL_RAN')\n"
    result = runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, short_tmp / "out", final_cell_source=source_text)
    digest = hashlib.sha256(source_text.encode()).hexdigest()
    assert result["final_cell_sha256"] == digest
    assert result["final_cell"] == {"index": 4, "sha256": digest}
    executed = nbformat.read(str(short_tmp / "out" / "overlay" / NOTEBOOK_RELATIVE), as_version=4)
    assert len(executed.cells) == 5
    assert executed.cells[4].source == source_text
    assert executed.cells[4].metadata["readonly_notebook_execution"] == {"final_cell_sha256": digest}
    assert "FINAL_CELL_RAN" in _outputs_text(executed.cells[4])
    assert len(nbformat.read(str(repo / NOTEBOOK_RELATIVE), as_version=4).cells) == 4
    assert result["cells"][4]["status"] == "ok"
    assert result["cells"][4]["id"] == f"final-cell-{digest[:12]}"
    assert not any(p.name != "nb.ipynb" and p.suffix == ".ipynb" for p in (repo / NOTEBOOK_RELATIVE).parent.iterdir())


def test_cli_runs_and_reports_the_result_path(repo, short_tmp):
    source_file = short_tmp / "final.py"
    source_file.write_text("print('CLI_FINAL')\n")
    out = short_tmp / "cli-out"
    completed = subprocess.run(
        [str(REPO / "venv" / "bin" / "python"), str(RUNNER_PATH), "--repository", str(repo),
         "--notebook", str(NOTEBOOK_RELATIVE), "--output-dir", str(out),
         "--final-cell-source-file", str(source_file)],
        capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(out.resolve() / runner.RESULT_FILENAME)
    result = json.loads((out / runner.RESULT_FILENAME).read_text())
    assert result["status"] == "completed"
    assert result["final_cell_sha256"] == hashlib.sha256(b"print('CLI_FINAL')\n").hexdigest()


def test_cli_rejects_a_final_cell_source_file_inside_the_repository(repo, tmp_path):
    inside = repo / "final.py"
    inside.write_text("print('no')\n")
    try:
        completed = subprocess.run(
            [str(REPO / "venv" / "bin" / "python"), str(RUNNER_PATH), "--repository", str(repo),
             "--notebook", str(NOTEBOOK_RELATIVE), "--output-dir", str(tmp_path / "out"),
             "--final-cell-source-file", str(inside)],
            capture_output=True, text=True,
        )
    finally:
        inside.unlink()
    assert completed.returncode == 2
    assert "must be outside the repository" in completed.stderr
    assert not (tmp_path / "out").exists()


def test_invalid_notebook_paths_are_rejected_before_anything_is_created(repo, tmp_path):
    out = tmp_path / "out"
    with pytest.raises(ValueError, match="does not exist"):
        runner.execute_notebook_readonly(repo, "apps/demo/notebooks/missing.ipynb", out)
    outside = tmp_path / "outside.ipynb"
    nbformat.write(nbformat.v4.new_notebook(), str(outside))
    with pytest.raises(ValueError, match="not inside the repository"):
        runner.execute_notebook_readonly(repo, outside, out)
    with pytest.raises(ValueError, match="not an .ipynb"):
        runner.execute_notebook_readonly(repo, "README.md", out)
    assert not out.exists() or not any(out.iterdir())


def test_nonempty_or_repository_contained_output_directories_are_rejected(repo, tmp_path):
    nonempty = tmp_path / "nonempty"
    nonempty.mkdir()
    (nonempty / "leftover").write_text("x")
    with pytest.raises(ValueError, match="not empty"):
        runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, nonempty)
    with pytest.raises(ValueError, match="inside the repository"):
        runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, repo / "scratch-out")
    assert not (repo / "scratch-out").exists()
    with pytest.raises(ValueError, match="contains the repository"):
        runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, repo.parent)
    too_long = tmp_path / ("x" * 60) / "out"
    with pytest.raises(ValueError, match="too long for the kernel's Unix-domain sockets"):
        runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, too_long)
    assert not too_long.exists()


def test_probe_that_unexpectedly_succeeds_stops_before_the_source_cells(tmp_path, short_tmp, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(runner, "sandbox_prefix", lambda profile: [])
    out = short_tmp / "out"
    with pytest.raises(runner.ReadOnlyExecutionError, match="did not fail with PermissionError"):
        runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, out)
    result = json.loads((out / runner.RESULT_FILENAME).read_text())
    assert result["status"] == "failed"
    assert result["probe"]["exception_class"] is None
    assert result["driver_status"] == "probe-failed"
    assert result["cells"] == []
    assert result["probe"]["exists_after"] is True
    assert any("probe file exists" in f for f in result["failures"])
    assert any("repository status changed" in f for f in result["failures"])
    executed = nbformat.read(str(out / "overlay" / NOTEBOOK_RELATIVE), as_version=4)
    assert all(c.get("outputs") == [] for c in executed.cells if c.cell_type == "code")


def test_source_digest_change_during_execution_is_reported(tmp_path, short_tmp, monkeypatch):
    repo = make_repo(tmp_path)
    source = repo / NOTEBOOK_RELATIVE
    original_run = runner.subprocess.run

    def run_then_touch_source(*args, **kwargs):
        completed = original_run(*args, **kwargs)
        if args and args[0][:1] == [str(runner.SANDBOX_EXEC)]:
            source.write_text(source.read_text() + "\n")
        return completed

    monkeypatch.setattr(runner.subprocess, "run", run_then_touch_source)
    with pytest.raises(runner.ReadOnlyExecutionError, match="source notebook changed"):
        runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, short_tmp / "out")
    result = json.loads((short_tmp / "out" / runner.RESULT_FILENAME).read_text())
    assert result["source_notebook_unchanged"] is False
    assert result["source_notebook_sha256_before"] != result["source_notebook_sha256_after"]
    assert result["probe"]["exception_class"] == "PermissionError"


def test_repository_status_change_during_execution_is_reported(tmp_path, short_tmp, monkeypatch):
    repo = make_repo(tmp_path)
    original_run = runner.subprocess.run

    def run_then_add_file(*args, **kwargs):
        completed = original_run(*args, **kwargs)
        if args and args[0][:1] == [str(runner.SANDBOX_EXEC)]:
            (repo / "apps" / "stray.txt").write_text("stray\n")
        return completed

    monkeypatch.setattr(runner.subprocess, "run", run_then_add_file)
    with pytest.raises(runner.ReadOnlyExecutionError, match="repository status changed"):
        runner.execute_notebook_readonly(repo, NOTEBOOK_RELATIVE, short_tmp / "out")
    result = json.loads((short_tmp / "out" / runner.RESULT_FILENAME).read_text())
    assert result["repository_unchanged"] is False
    assert result["repository_status_before"]["porcelain"] == []
    assert result["repository_status_after"]["porcelain"] == ["?? apps/stray.txt"]
    assert result["source_notebook_unchanged"] is True
