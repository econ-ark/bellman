"""The acceptance file of lane A of the internal developer release 0.01, the
rename of the package kikku to asva (the lean implementation rule, layer 2):
one test for each of the items 1 to 5 of section 7 of the lane's brief,
`asva.md`, named `test_item_<n>_<claim>`, deleted when the next change to
asva is accepted.

Item 6 is AAS's reading and no test: he reads the changelog entry with its
provenance line (asva is the package of the repository bright-forest/kikku at
a54619c, renamed on the date of the rename commit), row A6 of the decisions
file of AMD-FAC-002 struck, the row of the status table, the row of the
private-release checklist and the item of the session note.

This file names the retired package and its deleted subpackage as data, in
the pattern of item 4 and in the imports item 1 forbids, and item 4's sweep
therefore leaves it out.
"""
import ast
import configparser
import os
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest

from bellman.stage import elaborate_stage, load_stage

ASVA = Path(__file__).resolve().parents[1]
ROOT = ASVA.parents[1]
MODULES = sorted((ASVA / "asva").rglob("*.py"))

# the packages no module of asva imports: the archived dolo and dolang, the
# graph library of the deleted subpackage, the old name, and bellman (AS8)
FORBIDDEN = {"bellman", "dolang", "dolo", "kikku", "networkx"}

# the rename commit moved each module of the old package that the lane keeps,
# old path to new path; types.py and make_test.py came in with the live
# revision a54619c, one commit before it, and were not present at 5413c170d
OLD = "packages/kikku/kikku"
NEW = "packages/asva/asva"
MOVED = {f"{OLD}/asva/{name}": f"{NEW}/{name}"
         for name in ("__init__.py", "compose_interp.py", "egm_1d.py", "numerics.py", "simulate.py")}
MOVED |= {f"{OLD}/run/{name}": f"{NEW}/run/{name}"
          for name in ("__init__.py", "estimate.py", "io.py", "make_test.py", "metrics.py", "moments.py", "mpi.py",
                       "sweep.py", "types.py")}
# the commit that added the old package to this repository
FIRST = "5413c170d"

# item 4: the pattern of the plan's sweep, read case-sensitively, over the
# lane's scope; the changelog and this file are left out, and the lines the
# review of the plan marks "leave" are history
PATTERN = re.compile(r"(?<!what-to-do-with-)\bkikku\b|\bdynx\b")
AI_README = Path("AI", "README.md").as_posix()
SCOPE = ("docs", "tutorials", "applications", "packages", "README.md", "pytest.ini", "install-dev.sh", AI_README)
LEFT_OUT = {"docs/changelog.md", Path(__file__).resolve().relative_to(ROOT).as_posix()}
# the decision records, which state the rules of their time with the names of
# their time, kikku among them (RH200), were left out while they stood under
# docs/decisions/; since 29 September 2026 they stand in the internal folder,
# outside the scope, and need no exclusion
LEAVE = ((AI_README, "Removed 19 Jul 2026: `dynx/`"), (AI_README, "`dyno.py/` and `dynx/` checkouts"),
         ("README.md", "the factory-module restructure (kikku migration)"))

# item 5: the stage folders of the retirement application and the handler of
# its endogenous grid entries
STAGE_FOLDERS = ROOT / "applications" / "retirement-choice" / "declaration" / "stages"
HANDLER = "asva:make_egm_1d"


def _git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def _environment():
    """The environment of a child process: this checkout's asva first on the
    path, as an editable install of `packages/asva` places it, and no setting
    of the pytest run that starts the child."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")}
    environment["PYTHONPATH"] = os.pathsep.join(p for p in (str(ASVA), os.environ.get("PYTHONPATH", "")) if p)
    return environment


def test_item_1_asva_installs_alone_its_modules_import_and_none_imports_dolo_networkx_or_the_old_package(tmp_path):
    """pip builds the distribution of a copy of `packages/asva`, fetching
    nothing: it is named asva, declares numpy, numba and pandas and not
    bellman, and holds the package asva and its modules alone, not its tests.
    Installed from that build, the five modules of the item import in a fresh
    interpreter, which then holds none of the forbidden packages; and no
    module's source imports one."""
    project = tomllib.loads((ASVA / "pyproject.toml").read_text())
    assert project["project"]["name"] == "asva" and project["project"]["version"] == "0.1.0"
    declared = {re.split(r"[\s<>=!~\[;]", requirement)[0] for requirement in project["project"]["dependencies"]}
    assert {"numpy", "numba", "pandas"} <= declared and "bellman" not in declared
    optional = project["project"].get("optional-dependencies", {})
    assert not any(requirement.startswith("bellman") for extra in optional.values() for requirement in extra)

    shutil.copytree(ASVA, tmp_path / "source", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "build"))
    subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "--no-index", "-q",
                    "-w", str(tmp_path / "wheel"), str(tmp_path / "source")], check=True, capture_output=True)
    (wheel,) = (tmp_path / "wheel").glob("asva-0.1.0-*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        archive.extractall(tmp_path / "installed")
    assert {name.split("/")[0] for name in names} == {"asva", "asva-0.1.0.dist-info"}
    assert sorted(name for name in names if name.endswith(".py")) == \
        sorted(module.relative_to(ASVA).as_posix() for module in MODULES)

    probe = ("import sys\n"
             "import asva.egm_1d, asva.compose_interp, asva.numerics, asva.simulate, asva.run\n"
             "print(sys.modules['asva'].__file__)\n"
             f"print(sorted(m for m in sys.modules if m.split('.')[0] in {sorted(FORBIDDEN)!r}))\n")
    child = subprocess.run([sys.executable, "-c", probe], cwd=tmp_path, capture_output=True, text=True,
                           env={**_environment(), "PYTHONPATH": str(tmp_path / "installed")})
    assert child.returncode == 0, child.stderr
    location, loaded = child.stdout.splitlines()
    assert Path(location) == tmp_path / "installed" / "asva" / "__init__.py"
    assert loaded == "[]"

    imported = set()
    for module in MODULES:
        for node in ast.walk(ast.parse(module.read_text(), filename=str(module))):
            if isinstance(node, ast.Import):
                imported |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add(node.module.split(".")[0])
    assert imported & FORBIDDEN == set()


def test_item_2_pytest_from_the_root_collects_the_tests_of_asva_one_for_each_of_its_modules():
    """The root's pytest.ini names the tests folder of asva, which holds no
    `__init__.py`, and not the package itself, whose module `run/make_test.py`
    the name pattern of a test file would match; a collection from the root
    succeeds and holds a test named for each module of asva."""
    config = configparser.ConfigParser()
    config.read(ROOT / "pytest.ini")
    assert "packages/asva/tests" in config["pytest"]["testpaths"].split()
    assert "packages/kikku" not in config["pytest"].get("addopts", "")
    assert not (ASVA / "tests" / "__init__.py").exists()

    # verbosity -1 lists one test per line, whatever options pytest.ini adds
    collected = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "--verbosity=-1", "-p",
                                "no:cacheprovider"], cwd=ROOT, env=_environment(), capture_output=True, text=True)
    assert collected.returncode == 0, collected.stdout[-3000:]
    ours = [line for line in collected.stdout.splitlines() if line.startswith("packages/asva/tests/")]
    for module in MODULES:
        if module.name == "__init__.py":
            continue
        prefix = "run_" if module.parent.name == "run" else ""
        assert any(f"::test_{prefix}{module.stem}_" in line for line in ours), module


def test_item_3_the_rename_commit_lists_every_moved_module_as_a_rename_and_follow_reaches_the_first_commit():
    """The rename commit is the one that added `packages/asva/asva/egm_1d.py`;
    its summary with rename detection (`git show -M`, read here by its status
    letters) lists each kept module as a rename to its new path, and `git log
    --follow` of each module present at 5413c170d reaches that commit."""
    if subprocess.run(["git", "cat-file", "-e", f"{FIRST}^{{commit}}"], cwd=Path(__file__).resolve().parents[3],
                      capture_output=True).returncode != 0:
        pytest.skip("the first commit and the rename commit are not in this history: the public repository, "
                    "econ-ark/bellman, starts from a root commit")
    added = _git("log", "--format=%H", "--diff-filter=A", "--", f"{NEW}/egm_1d.py").split()
    assert len(added) == 1
    renames = {}
    for line in _git("show", "-M", "--name-status", "--format=", added[0]).splitlines():
        status, *paths = line.split("\t")
        if status.startswith("R"):
            renames[paths[0]] = paths[1]
    assert {old: renames.get(old) for old in MOVED} == MOVED

    first = _git("rev-parse", f"{FIRST}^{{commit}}").strip()
    at_first = set(_git("ls-tree", "-r", "--name-only", first, "--", OLD).split())
    present = [new for old, new in MOVED.items() if old in at_first]
    assert len(present) == 12
    for new in present:
        assert first in _git("log", "--follow", "--format=%H", "--", new).split(), new


def test_item_4_the_old_names_occur_in_the_lane_scope_only_in_the_lines_left_as_history():
    """Every tracked text file of the scope is read line by line; a line that
    matches the pattern is admitted only where the review of the plan leaves it
    as history (the README's line on the factory's restructure, two lines of
    the README of the folder AI on folders removed in May and July 2026)."""
    hits = []
    for name in _git("ls-files", "-z", "--", *SCOPE).split("\0"):
        if not name or name in LEFT_OUT:
            continue
        data = (ROOT / name).read_bytes()
        if b"\0" in data[:8000]:
            continue
        for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            if PATTERN.search(line) and not any(name == path and text in line for path, text in LEAVE):
                hits.append(f"{name}:{number}: {line.strip()[:120]}")
    assert hits == []


def test_item_5_the_retirement_choice_page_quotes_both_methods_files_and_the_application_methodizes_with_them():
    """The page quotes each methods file byte for byte in a YAML block, and
    each binds as the page states under "Binding each file to its stage": the
    retiree's and the worker's with their endogenous grid entry at the
    Evaluation that closes the policy block, `policy:Evaluation`, and the
    handler asva:make_egm_1d; the worker's block writes the grid line
    `w[>] = b + c[>]`, so the entry that was refused before the kinds of the
    policy block's rows changed (lane K of the internal developer release
    0.01) now binds."""
    page = (ROOT / "docs" / "examples" / "retirement_choice.md").read_text()
    methods = {name: STAGE_FOLDERS / name / "methods.yml" for name in ("worker_cons", "retiree_cons")}
    for name, path in methods.items():
        text = path.read_text()
        assert f"handler: {HANDLER}\n" in text
        assert f"```yaml\n{text}```" in page, name

    retiree = elaborate_stage(load_stage(STAGE_FOLDERS / "retiree_cons" / "retiree_cons.bl"))
    bound = retiree.methodize(methods["retiree_cons"])
    assert [method.handler for method in bound.methods.values() if method.tag == "egm"] == [HANDLER]

    worker = elaborate_stage(load_stage(STAGE_FOLDERS / "worker_cons" / "worker_cons.bl"))
    bound = worker.methodize(methods["worker_cons"])
    assert [(str(place), method.handler) for place, method in bound.methods.items()
            if method.tag == "egm"] == [("policy:Evaluation", HANDLER)]
    assert "worker_cons   binds" in page and "retiree_cons  binds" in page
