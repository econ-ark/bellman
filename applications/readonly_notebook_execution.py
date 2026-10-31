"""Read-only execution of a copied notebook (spec 0.3c, task N01).

The runner never executes a notebook at its source path. It copies the
target notebook into an overlay under an external temporary root,
reproduces the repository layout around the copy with absolute symlinks,
and executes the copy inside a macOS sandbox (``/usr/bin/sandbox-exec``)
whose profile permits writes only under that temporary root. Before the
first source cell it runs a probe cell in the same kernel that attempts
to write into the repository; the probe must fail with ``PermissionError``
or the source notebook is not executed. The result JSON at
``<output_dir>/execution-result.json`` records digests, the overlay
layout, the profile, the probe, ordered cell results, and the before and
after repository comparison.

Two entry points share this file: ``execute_notebook_readonly`` (and the
command-line interface around it) runs in the caller's process and owns
the temporary root; ``--sandbox-driver`` is the same file re-invoked by
the sandboxed interpreter to start the kernel and execute cells.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

RESULT_VERSION = 1
RESULT_FILENAME = "execution-result.json"
PROFILE_FILENAME = "sandbox-profile.sb"
DRIVER_REQUEST_FILENAME = "driver-request.json"
DRIVER_RESULT_FILENAME = "driver-result.json"
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
KERNEL_NAME = "python3"
KERNEL_TRANSPORT = "ipc"
CELL_TIMEOUT_SECONDS = 3600
# macOS limits a Unix-domain socket path to 104 bytes; jupyter_client appends
# "-<n>" to the prefix for each of the five kernel channels.
MAX_SOCKET_PREFIX_BYTES = 90
TEMPORARY_ROOT_TOKEN = "<temporary-root>"
REPOSITORY_TOKEN = "<repository>"
PROBE_UUID_TOKEN = "<probe-uuid>"
PROBE_PREFIX = ".readonly-notebook-probe-"
PROBE_CWD_MARKER = "READONLY_PROBE_CWD="

# Relative to the temporary root; created before the sandboxed process starts.
ENVIRONMENT_SUBDIRECTORIES = {
    "HOME": "home",
    "TMPDIR": "runtime",
    "XDG_CACHE_HOME": "cache",
    "IPYTHONDIR": "home/.ipython",
    "JUPYTER_CONFIG_DIR": "home/.jupyter",
    "JUPYTER_DATA_DIR": "home/jupyter-data",
    "JUPYTER_RUNTIME_DIR": "runtime/jupyter",
    "MPLCONFIGDIR": "cache/matplotlib",
}

PROFILE_TEMPLATE = (
    "(version 1)\n"
    "(deny default)\n"
    '(import "system.sb")\n'
    "(allow process*)\n"
    "(allow file-read*)\n"
    '(allow file-write* (subpath "{root}"))\n'
    '(allow network* (local unix-socket (subpath "{root}")) '
    '(remote unix-socket (subpath "{root}")))\n'
)

PROBE_SOURCE_TEMPLATE = (
    "import os as __readonly_os\n"
    "from pathlib import Path as __readonly_Path\n"
    "print({marker!r} + __readonly_os.getcwd())\n"
    "__readonly_Path({probe_path!r}).write_text('probe', encoding='utf-8')\n"
)


class ReadOnlyExecutionError(RuntimeError):
    """A safety check failed; the result JSON, if written, records which."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sandbox_profile(root: Path) -> str:
    """The exact profile text for one temporary root."""
    return PROFILE_TEMPLATE.format(root=str(root))


def canonical_profile() -> str:
    """The profile with the temporary root replaced by its token."""
    return PROFILE_TEMPLATE.format(root=TEMPORARY_ROOT_TOKEN)


def sandbox_environment(root: Path) -> dict[str, str]:
    """Environment overrides that keep every kernel-side write under root."""
    overrides = {
        name: str(root / relative)
        for name, relative in ENVIRONMENT_SUBDIRECTORIES.items()
    }
    overrides["PYTHONDONTWRITEBYTECODE"] = "1"
    return overrides


def matplotlib_font_caches() -> list[Path]:
    """The font-cache files, ``fontlist-v*.json``, of this interpreter's matplotlib
    cache directory (``matplotlib.get_cachedir()``); none when matplotlib is absent."""
    try:
        import matplotlib
    except ImportError:
        return []
    return sorted(Path(matplotlib.get_cachedir()).glob("fontlist-v*.json"))


def repository_status(repository: Path) -> dict:
    """HEAD and the complete porcelain status, untracked files listed singly."""
    def git(*args: str) -> tuple[int, str]:
        completed = subprocess.run(
            ["git", "-C", str(repository), *args],
            capture_output=True, text=True,
        )
        return completed.returncode, completed.stdout
    code, head = git("rev-parse", "HEAD")
    code2, porcelain = git("status", "--porcelain", "--untracked-files=all")
    if code2 != 0:
        raise ReadOnlyExecutionError(
            f"repository status is unavailable: {repository} is not a git work tree"
        )
    return {
        "head": head.strip() if code == 0 else None,
        "porcelain": sorted(line for line in porcelain.splitlines() if line),
    }


def build_overlay(repository: Path, notebook_relative: Path, overlay: Path) -> tuple[Path, list[dict]]:
    """Reproduce the notebook's repository path under overlay.

    At each ancestor of the notebook path the next ancestor is a real
    directory and every other direct child of the corresponding repository
    directory is an absolute symlink. In the notebook's own directory the
    notebook is copied and every sibling is a symlink. Returns the copied
    notebook's path and the ordered overlay entries.
    """
    entries: list[dict] = []
    parts = notebook_relative.parts
    for depth in range(len(parts) - 1):
        source_dir = repository.joinpath(*parts[:depth])
        target_dir = overlay.joinpath(*parts[:depth])
        next_name = parts[depth]
        (target_dir / next_name).mkdir()
        entries.append({"path": str(Path(*parts[: depth + 1])), "kind": "directory"})
        for child in sorted(source_dir.iterdir(), key=lambda p: p.name):
            if child.name == next_name:
                continue
            os.symlink(str(child), str(target_dir / child.name))
            entries.append({
                "path": str(Path(*parts[:depth]) / child.name) if depth else child.name,
                "kind": "symlink",
                "target": str(child),
            })
    notebook_dir_source = repository.joinpath(*parts[:-1])
    notebook_dir_target = overlay.joinpath(*parts[:-1])
    copied = notebook_dir_target / parts[-1]
    shutil.copyfile(repository / notebook_relative, copied)
    entries.append({"path": str(notebook_relative), "kind": "copied-notebook"})
    for child in sorted(notebook_dir_source.iterdir(), key=lambda p: p.name):
        if child.name == parts[-1]:
            continue
        os.symlink(str(child), str(notebook_dir_target / child.name))
        entries.append({
            "path": str(Path(*parts[:-1]) / child.name),
            "kind": "symlink",
            "target": str(child),
        })
    return copied, entries


def sandbox_prefix(profile: Path) -> list[str]:
    """The command prefix that places the interpreter inside the sandbox."""
    return [str(SANDBOX_EXEC), "-f", str(profile)]


def _validate(repository: Path, notebook: Path, output_dir: Path) -> tuple[Path, Path, Path, Path]:
    if not repository.is_dir():
        raise ValueError(f"repository is not a directory: {repository}")
    notebook_path = notebook if notebook.is_absolute() else repository / notebook
    notebook_path = notebook_path.resolve()
    if not notebook_path.is_file():
        raise ValueError(f"notebook does not exist: {notebook_path}")
    if notebook_path.suffix != ".ipynb":
        raise ValueError(f"notebook is not an .ipynb file: {notebook_path}")
    if not notebook_path.is_relative_to(repository):
        raise ValueError(f"notebook is not inside the repository: {notebook_path}")
    if output_dir.is_relative_to(repository):
        raise ValueError(f"output directory is inside the repository: {output_dir}")
    if repository.is_relative_to(output_dir):
        raise ValueError(f"output directory contains the repository: {output_dir}")
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"output directory is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise ValueError(f"output directory is not empty: {output_dir}")
    socket_prefix = str(output_dir / "runtime" / "kernel")
    if len(socket_prefix.encode("utf-8")) > MAX_SOCKET_PREFIX_BYTES:
        raise ValueError(
            "output directory path is too long for the kernel's Unix-domain sockets "
            f"({len(socket_prefix.encode('utf-8'))} bytes for {socket_prefix}; the limit is "
            f"{MAX_SOCKET_PREFIX_BYTES}); use a shorter directory, for example one made by "
            "`mktemp -d /private/tmp/XXXXXX`"
        )
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    python = repository / "venv" / "bin" / "python"
    if not python.exists():
        raise ValueError(f"the repository has no venv/bin/python: {python}")
    if not SANDBOX_EXEC.exists():
        raise ReadOnlyExecutionError(f"{SANDBOX_EXEC} is absent; the notebook is not executed")
    return notebook_path, notebook_path.relative_to(repository), output_dir, python


def _canonical(text: str, root: Path, repository: Path, probe_uuid: str) -> str:
    return (
        text.replace(str(root), TEMPORARY_ROOT_TOKEN)
        .replace(str(repository), REPOSITORY_TOKEN)
        .replace(probe_uuid, PROBE_UUID_TOKEN)
    )


def execute_notebook_readonly(repository, notebook, output_dir, final_cell_source=None) -> dict:
    """Execute a copy of ``notebook`` read-only and return the result record.

    ``repository`` is the repository root; ``notebook`` is a path inside it
    (absolute or repository-relative); ``output_dir`` is an empty or absent
    directory outside the repository that becomes the temporary root;
    ``final_cell_source``, if given, is reviewed Python source appended as a
    final code cell of the copy only. The sandbox's matplotlib cache folder
    starts with copies of this interpreter's font-cache files, where they
    exist, so that matplotlib does not rebuild its font cache at every run.
    The result is also written to ``<output_dir>/execution-result.json``. A
    failed safety check raises ``ReadOnlyExecutionError`` after that file has
    been written.
    """
    repository = Path(repository).resolve()
    root = Path(output_dir).resolve()
    notebook_path, notebook_relative, root, python = _validate(repository, Path(notebook), root)

    status_before = repository_status(repository)
    source_sha_before = sha256_file(notebook_path)

    for name in ("home", "cache", "runtime", "overlay"):
        (root / name).mkdir()
    environment = sandbox_environment(root)
    for value in environment.values():
        if value.startswith(str(root)):
            Path(value).mkdir(parents=True, exist_ok=True)
    for cached in matplotlib_font_caches():
        shutil.copyfile(cached, Path(environment["MPLCONFIGDIR"]) / cached.name)
    (root / "runtime" / "jupyter").mkdir(parents=True, exist_ok=True)

    overlay = root / "overlay"
    copied, overlay_entries = build_overlay(repository, notebook_relative, overlay)
    copied_sha = sha256_file(copied)
    working_directory = copied.parent

    profile = root / PROFILE_FILENAME
    profile_text = sandbox_profile(root)
    profile.write_text(profile_text, encoding="utf-8")

    probe_uuid = uuid.uuid4().hex
    probe_path = repository / f"{PROBE_PREFIX}{probe_uuid}"
    final_cell_sha = sha256_text(final_cell_source) if final_cell_source is not None else None

    request = {
        "repository": str(repository),
        "notebook_copy": str(copied),
        "working_directory": str(working_directory),
        "probe_path": str(probe_path),
        "probe_cwd_marker": PROBE_CWD_MARKER,
        "kernel_name": KERNEL_NAME,
        "transport": KERNEL_TRANSPORT,
        "ipc_socket_prefix": str(root / "runtime" / "kernel"),
        "cell_timeout_seconds": CELL_TIMEOUT_SECONDS,
        "final_cell_source": final_cell_source,
        "final_cell_sha256": final_cell_sha,
        "result_path": str(root / DRIVER_RESULT_FILENAME),
    }
    request_path = root / DRIVER_REQUEST_FILENAME
    request_path.write_text(json.dumps(request, indent=2), encoding="utf-8")

    command = [*sandbox_prefix(profile), str(python), str(Path(__file__).resolve()),
               "--sandbox-driver", str(request_path)]
    child_env = dict(os.environ)
    child_env.update(environment)
    completed = subprocess.run(command, env=child_env, cwd=str(root), capture_output=True, text=True)

    driver_result_path = root / DRIVER_RESULT_FILENAME
    driver = json.loads(driver_result_path.read_text(encoding="utf-8")) if driver_result_path.exists() else None

    status_after = repository_status(repository)
    source_sha_after = sha256_file(notebook_path) if notebook_path.exists() else None
    probe_exists_after = probe_path.exists()
    executed_sha = sha256_file(copied) if copied.exists() else None

    failures: list[str] = []
    if completed.returncode != 0 or driver is None:
        failures.append(f"the sandboxed driver did not complete (exit code {completed.returncode})")
    probe = (driver or {}).get("probe") or {}
    if probe.get("exception_class") != "PermissionError":
        failures.append(
            "the repository write probe did not fail with PermissionError "
            f"(observed: {probe.get('exception_class')!r})"
        )
    if probe_exists_after:
        failures.append(f"the probe file exists after execution: {probe_path}")
    kernel_cwd = (driver or {}).get("kernel_working_directory")
    if kernel_cwd is None or os.path.realpath(kernel_cwd) != os.path.realpath(working_directory):
        failures.append(f"the kernel working directory was {kernel_cwd!r}, not the copied notebook's directory")
    if source_sha_after != source_sha_before:
        failures.append("the source notebook changed during execution")
    if status_after != status_before:
        failures.append("the repository status changed during execution")
    if driver is not None and driver.get("status") != "completed":
        failures.append(f"the driver stopped with status {driver.get('status')!r}: {driver.get('error')}")

    cells = (driver or {}).get("cells", [])
    canonical_cells = [
        {k: cell.get(k) for k in ("index", "id", "cell_type", "status", "execution_count", "ename")}
        for cell in cells
    ]
    canonical_overlay = [
        {**entry, **({"target": _canonical(entry["target"], root, repository, probe_uuid)} if "target" in entry else {})}
        for entry in overlay_entries
    ]
    canonical_comparison = {
        "notebook": str(notebook_relative),
        "source_notebook_sha256": source_sha_before,
        "final_cell_sha256": final_cell_sha,
        "canonical_profile_sha256": sha256_text(canonical_profile()),
        "environment": {k: _canonical(v, root, repository, probe_uuid) for k, v in environment.items()},
        "working_directory": _canonical(str(working_directory), root, repository, probe_uuid),
        "kernel_working_directory": _canonical(os.path.realpath(kernel_cwd), root, repository, probe_uuid) if kernel_cwd else None,
        "overlay": canonical_overlay,
        "probe": {
            "path": _canonical(str(probe_path), root, repository, probe_uuid),
            "exception_class": probe.get("exception_class"),
            "exists_after": probe_exists_after,
        },
        "kernel": {"name": KERNEL_NAME, "transport": KERNEL_TRANSPORT},
        "cells": canonical_cells,
        "source_notebook_unchanged": source_sha_after == source_sha_before,
        "repository_unchanged": status_after == status_before,
        "status": "completed" if not failures else "failed",
    }
    result = {
        "version": RESULT_VERSION,
        "status": "completed" if not failures else "failed",
        "failures": failures,
        "repository": str(repository),
        "notebook": str(notebook_relative),
        "source_notebook_path": str(notebook_path),
        "source_notebook_sha256_before": source_sha_before,
        "source_notebook_sha256_after": source_sha_after,
        "source_notebook_unchanged": source_sha_after == source_sha_before,
        "temporary_root": str(root),
        "overlay": overlay_entries,
        "copied_notebook_path": str(copied),
        "copied_notebook_sha256": copied_sha,
        "executed_copy_sha256": executed_sha,
        "working_directory": str(working_directory),
        "kernel_working_directory": kernel_cwd,
        "kernel": {"name": KERNEL_NAME, "transport": KERNEL_TRANSPORT,
                   "ipc_socket_prefix": request["ipc_socket_prefix"],
                   "cell_timeout_seconds": CELL_TIMEOUT_SECONDS},
        "environment": environment,
        "sandbox": {
            "profile_path": str(profile),
            "profile": profile_text,
            "profile_sha256": sha256_text(profile_text),
            "canonical_profile_sha256": sha256_text(canonical_profile()),
            "command": command,
            "returncode": completed.returncode,
            "stderr_tail": completed.stderr[-4000:],
        },
        "probe": {
            "path": str(probe_path),
            "exception_class": probe.get("exception_class"),
            "exception_value": probe.get("exception_value"),
            "execution_count": probe.get("execution_count"),
            "exists_after": probe_exists_after,
        },
        "cells": cells,
        "final_cell": (driver or {}).get("final_cell") if final_cell_source is not None else None,
        "final_cell_sha256": final_cell_sha,
        "driver_status": (driver or {}).get("status"),
        "driver_error": (driver or {}).get("error"),
        "repository_status_before": status_before,
        "repository_status_after": status_after,
        "repository_unchanged": status_after == status_before,
        "canonical_comparison": canonical_comparison,
    }
    (root / RESULT_FILENAME).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if failures:
        raise ReadOnlyExecutionError("; ".join(failures))
    return result


def notebook_cell_ids(path: Path) -> list:
    """Cell ids as stored in the file, None where a cell has none.

    nbformat assigns a random id to an id-less cell when it reads a
    format-4.5 notebook, so ids must be taken from the raw JSON to be stable.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [cell.get("id") for cell in raw.get("cells", [])]


def _cell_record(index: int, cell, stored_id) -> dict:
    record = {
        "index": index,
        "id": stored_id,
        "cell_type": cell.cell_type,
        "status": "not-code",
        "execution_count": None,
        "ename": None,
        "evalue": None,
    }
    if cell.cell_type != "code":
        return record
    record["execution_count"] = cell.get("execution_count")
    errors = [o for o in cell.get("outputs", []) if o.get("output_type") == "error"]
    if errors:
        record["status"] = "error"
        record["ename"] = errors[0].get("ename")
        record["evalue"] = (errors[0].get("evalue") or "")[:500]
    else:
        record["status"] = "ok"
    return record


def _sandbox_driver(request_path: str) -> int:
    """Runs inside the sandbox: probe first, then the copied notebook's cells."""
    import nbformat
    from jupyter_client import KernelManager
    from nbclient import NotebookClient

    request = json.loads(Path(request_path).read_text(encoding="utf-8"))
    result_path = Path(request["result_path"])
    result: dict = {"status": "not-started", "probe": None, "kernel_working_directory": None,
                    "cells": [], "final_cell": None, "error": None}

    def write() -> None:
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    try:
        copy = Path(request["notebook_copy"])
        stored_ids = notebook_cell_ids(copy)
        nb = nbformat.read(str(copy), as_version=4)
        if request["final_cell_source"] is not None:
            final_cell = nbformat.v4.new_code_cell(request["final_cell_source"])
            final_cell["id"] = f"final-cell-{request['final_cell_sha256'][:12]}"
            final_cell.metadata["readonly_notebook_execution"] = {
                "final_cell_sha256": request["final_cell_sha256"],
            }
            nb.cells.append(final_cell)
            stored_ids.append(final_cell["id"])
            result["final_cell"] = {"index": len(nb.cells) - 1, "sha256": request["final_cell_sha256"]}

        # nbclient writes each executed cell back to nb.cells[index], so the
        # probe occupies index 0 of the working list during execution and is
        # removed before the executed copy is written.
        probe_cell = nbformat.v4.new_code_cell(PROBE_SOURCE_TEMPLATE.format(
            marker=request["probe_cwd_marker"], probe_path=request["probe_path"],
        ))
        nb.cells.insert(0, probe_cell)

        km = KernelManager(kernel_name=request["kernel_name"], transport=request["transport"])
        km.ip = request["ipc_socket_prefix"]
        client = NotebookClient(
            nb, km=km, timeout=request["cell_timeout_seconds"], allow_errors=True,
            resources={"metadata": {"path": request["working_directory"]}},
        )
        client.reset_execution_trackers()
        with client.setup_kernel():
            client.execute_cell(nb.cells[0], 0)
            probe_cell = nb.cells[0]
            marker = request["probe_cwd_marker"]
            for output in probe_cell.get("outputs", []):
                if output.get("output_type") == "stream":
                    for line in output.get("text", "").splitlines():
                        if line.startswith(marker):
                            result["kernel_working_directory"] = line[len(marker):]
            errors = [o for o in probe_cell.get("outputs", []) if o.get("output_type") == "error"]
            result["probe"] = {
                "path": request["probe_path"],
                "exception_class": errors[0].get("ename") if errors else None,
                "exception_value": (errors[0].get("evalue") or "")[:500] if errors else None,
                "execution_count": probe_cell.get("execution_count"),
            }
            if result["probe"]["exception_class"] != "PermissionError":
                result["status"] = "probe-failed"
                write()
                return 3
            for index in range(1, len(nb.cells)):
                client.execute_cell(nb.cells[index], index)
                result["cells"].append(_cell_record(index - 1, nb.cells[index], stored_ids[index - 1]))
                write()
        nb.cells.pop(0)
        nbformat.write(nb, str(copy))
        result["status"] = "completed"
        write()
        return 0
    except Exception as error:  # the parent reports the driver's failure
        result["status"] = "driver-exception"
        result["error"] = f"{type(error).__name__}: {error}"
        write()
        return 4


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--sandbox-driver"]:
        return _sandbox_driver(argv[1])
    parser = argparse.ArgumentParser(description="Execute a copied notebook read-only (spec 0.3c N01).")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--notebook", required=True, help="path inside the repository")
    parser.add_argument("--output-dir", required=True, help="empty directory outside the repository")
    parser.add_argument("--final-cell-source-file", default=None,
                        help="reviewed Python source, in a file outside the repository")
    args = parser.parse_args(argv)
    repository = Path(args.repository).resolve()
    final_cell_source = None
    if args.final_cell_source_file is not None:
        source_file = Path(args.final_cell_source_file).resolve()
        if source_file.is_relative_to(repository):
            parser.error(f"the final-cell source file must be outside the repository: {source_file}")
        if not source_file.is_file():
            parser.error(f"the final-cell source file does not exist: {source_file}")
        final_cell_source = source_file.read_text(encoding="utf-8")
    try:
        result = execute_notebook_readonly(repository, args.notebook, args.output_dir, final_cell_source)
    except ValueError as error:
        parser.error(str(error))
    except ReadOnlyExecutionError as error:
        print(f"read-only execution failed: {error}", file=sys.stderr)
        return 1
    print(Path(result["temporary_root"]) / RESULT_FILENAME)
    return 0


if __name__ == "__main__":
    sys.exit(main())
