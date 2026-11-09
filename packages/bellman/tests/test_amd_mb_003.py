"""The acceptance file of AMD-MB-003, the grid as a tagged setting: one test
for each of the items 1 to 5 of the amendment's §5, named
`test_item_<n>_<claim>`, on the stage files, the methods files and the
settings files of `applications/buffer-stock` and `applications/cons-port`,
and on the pages that quote them. The comparison of the suites' failing
tests by name with those of `main`, the second part of item 5, is verified
by the runs the build's report records. The decisions the build took are the
rows MB-Y of the development repository's decisions file
`MB-Y-the-grid-as-a-tagged-setting.md`.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from conftest import ROOT, fresh_stage

from bellman.refusals import GRID_KIND_AS_METHOD, GRID_UNDER_EGM, GRID_WITHOUT_KIND, TargetError
from bellman.stage.sources import TagPreservingLoader, entry_key, load_methods, read_yaml_mapping

BUFFER_STOCK = ROOT / "applications/buffer-stock/declaration"
CONS_PORT = ROOT / "applications/cons-port/declaration"
BUFFER_STOCK_STAGE = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
HOOKS = ROOT / "docs/_hooks"
# the entries of the buffer-stock methods file as §1 of the amendment writes
# them, the settings of a grid in the flow form AAS wrote on 31 October 2026
SECTION_1 = """methods:
  - on: policy
    method: !egm
    block: buffer_stock_egm.bl
    settings: {grid: !Cartesian, orders: {a: n_a}, bounds: {a: [a_min, a_max]}}
  - on: policy.evaluate
    method: !Linear
  - on: cntn_to_dcsn
    method: !marginals
    block: marginals.bl
  - on: dcsn_to_arvl
    method: !marginals
    block: marginals.bl
  - on: E_ψ_ξ
    method: !gauss-hermite
    settings: {n_nodes: [n_ψ_nodes, n_ξ_nodes]}
  - on: dcsn_to_arvl.evaluate.marginal
    method: !Linear
    settings: {grid: !Cartesian, orders: {k: n_k}, bounds: {k: [k_min, k_max]}}
  - on: dcsn_to_arvl.evaluate.value
    method: !Linear
    settings: {grid: !Cartesian, orders: {k: n_k}, bounds: {k: [k_min, k_max]}}
"""
# the kind of a grid as the reader holds the tag `!Cartesian` written alone
CARTESIAN = {"__yaml_tag__": "Cartesian", "value": ""}
# the grids the refusals are provoked with, on the buffer-stock stage
SAVINGS = {"grid": "!Cartesian", "orders": {"a": "n_a"}, "bounds": {"a": ["a_min", "a_max"]}}
ASSETS = {"orders": {"k": "n_k"}, "bounds": {"k": ["k_min", "k_max"]}}
# a fenced YAML block of a page
FENCE = re.compile(r"```ya?ml\n(.*?)```", re.DOTALL)


def _entries(value):
    """The methods entries a YAML block holds, at any depth: each mapping that
    names a target under `on` and a method or settings."""
    if isinstance(value, dict):
        if "on" in value and ("method" in value or "settings" in value):
            yield value
        for item in value.values():
            yield from _entries(item)
    elif isinstance(value, list):
        for item in value:
            yield from _entries(item)


def _rows(stage):
    """The settings listing as (name, read at, by, grid) quadruples."""
    return [(row["name"], row["read at"], row["by"], row["grid"]) for row in stage.settings.list()]


def test_item_1_the_buffer_stock_methods_file_of_section_1_binds_and_lists_its_grids(tmp_path):
    """The buffer-stock methods file writes the entries of the amendment's §1,
    whose flow form the reader reads as it reads the block form, the kind a
    tag written alone and the entry's key that of its target and its kind;
    bound and configured with the settings file, `stage.settings` lists
    `n_a`, `a_min` and `a_max` read at `policy` by `!egm` and `n_k`, `k_min`
    and `k_max` read at the arrival builder's Evaluation by `!Linear`, each
    a field of a grid of the kind `!Cartesian`."""
    written = (BUFFER_STOCK / "methods/buffer_stock.yml").read_text(encoding="utf-8")
    assert written.endswith(SECTION_1)
    (tmp_path / "flow.yml").write_text(SECTION_1, encoding="utf-8")
    block = SECTION_1.replace(
        "    settings: {grid: !Cartesian, orders: {a: n_a}, bounds: {a: [a_min, a_max]}}\n",
        "    settings:\n      grid: !Cartesian\n"
        "      orders: {a: n_a}\n      bounds: {a: [a_min, a_max]}\n",
    )
    (tmp_path / "block.yml").write_text(block, encoding="utf-8")
    flow = read_yaml_mapping(tmp_path / "flow.yml", rule="readable-file", address=None)
    assert flow == read_yaml_mapping(tmp_path / "block.yml", rule="readable-file", address=None)
    entries = load_methods(BUFFER_STOCK / "methods/buffer_stock.yml")["methods"]
    assert entries == flow["methods"]
    assert entries[0]["settings"]["grid"] == CARTESIAN
    assert [entry_key(entry) for entry in (entries[0], entries[1], entries[6])] == [
        ("policy", "solution"),
        ("policy.evaluate", "representation"),
        ("dcsn_to_arvl.evaluate.value", "representation"),
    ]
    stage = fresh_stage(BUFFER_STOCK_STAGE)
    stage.methodize(BUFFER_STOCK / "methods/buffer_stock.yml")
    stage.configure(BUFFER_STOCK / "settings/buffer_stock.yml")
    rows = _rows(stage)
    for name in ("n_a", "a_min", "a_max"):
        assert (name, "policy", "!egm", "!Cartesian") in rows, name
    for name in ("n_k", "k_min", "k_max"):
        assert (name, "dcsn_to_arvl:Evaluation", "!Linear", "!Cartesian") in rows, name
    assert str(stage.settings["n_a"]) == (
        "n_a = 960, read at policy by !egm for its grid !Cartesian"
    )


@pytest.mark.parametrize(
    ("entries", "rule", "words"),
    [
        (
            [{"on": "dcsn_to_arvl.evaluate.value", "method": "!Cartesian", "settings": ASSETS}],
            GRID_KIND_AS_METHOD,
            ("!Cartesian is a kind of grid and not a method", "`method: !Linear`",
             "`grid: !Cartesian`"),
        ),
        (
            [{"on": "dcsn_to_arvl.evaluate.value", "method": "!Linear", "settings": ASSETS}],
            GRID_WITHOUT_KIND,
            ("!Linear writes `orders` and `bounds` without the setting `grid`",
             "write `grid: !Cartesian`"),
        ),
        (
            [
                {
                    "on": "policy",
                    "method": "!egm",
                    "block": str(BUFFER_STOCK / "methods/buffer_stock_egm.bl"),
                    "settings": SAVINGS,
                },
                {"on": "policy.evaluate", "method": "!Linear", "settings": SAVINGS},
            ],
            GRID_UNDER_EGM,
            ("the pairs of the decision state and the control that !egm computes",
             "the entry writes no grid"),
        ),
    ],
    ids=[
        "a kind of grid as a method",
        "the fields beside a basis",
        "a grid where egm stores knots",
    ],
)
def test_item_2_the_three_retired_or_unwritable_grids_are_refused_in_one_sentence(
    entries, rule, words
):
    """`!Cartesian` written as a method, `orders` and `bounds` written beside
    a basis without `grid`, and a grid written on `policy.evaluate` under
    `!egm` are each refused under its rule, in one sentence that names the
    tagged form or the reason, and the stage is left as it was."""
    stage = fresh_stage(BUFFER_STOCK_STAGE)
    with pytest.raises(TargetError) as refused:
        stage.methodize({"methods": entries})
    assert refused.value.rule == rule
    sentence = str(refused.value).split(": ", 1)[1]
    assert re.search(r"\.\s+[A-Z]", sentence) is None, sentence
    for word in words:
        assert word in sentence, (word, sentence)
    assert repr(stage) == "ElaboratedStage('buffer_stock', symbolic)"


def test_item_3_the_cons_port_folder_reproduces_its_reference_in_both_orders():
    """The cons-port methods files write each representation by its basis with
    the grid tagged `!Cartesian` beside its order and bounds, and no entry
    writes `!Cartesian` as its method; the `!egm` entry names its exogenous
    grid of savings the same way; and the solve of both orders against the
    fixed reference, `applications/cons-port/tests/test_reference_solve.py`,
    passes with them."""
    representations = 0
    for path in sorted((CONS_PORT / "methods").glob("*.yml")):
        for entry in load_methods(path)["methods"]:
            tag = (entry.get("method") or {}).get("__yaml_tag__")
            assert tag != "Cartesian", (path.name, entry)
            if tag in ("Linear", "pchip", "egm"):
                settings = entry["settings"]
                assert settings["grid"] == CARTESIAN, (path.name, entry)
                assert set(settings["orders"]) == set(settings["bounds"]), (path.name, entry)
                representations += tag != "egm"
    assert representations == 5
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(ROOT / "applications/cons-port/tests/test_reference_solve.py"),
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr


def test_item_4_the_pages_quote_the_files_as_they_stand():
    """The buffer-stock page quotes the methods and settings files whole and
    the methodization page the entries of cons-port's `cons.yml`, as the
    files write them; the table of method types and the listings of the
    pages of methods and places and of refusals are what the package
    prints; and no page writes `!Cartesian` as a method or `orders` beside a
    representation's method without the setting `grid`. The strict site
    build is run by the build's report."""
    page = (ROOT / "docs/examples/buffer-stock/buffer_stock.md").read_text(encoding="utf-8")
    for written in ("methods/buffer_stock.yml", "settings/buffer_stock.yml"):
        assert f"```yaml\n{(BUFFER_STOCK / written).read_text(encoding='utf-8')}```" in page
    methodization = (ROOT / "docs/Bellman-Sym/04-methodization.md").read_text(encoding="utf-8")
    cons = (CONS_PORT / "methods/cons.yml").read_text(encoding="utf-8")
    entries = cons[cons.index("methods:\n") :].split("\n\n")[0] + "\n"
    assert f"```yaml\n{entries}```" in methodization
    for script, pages in (
        (
            "stage_object_page.py",
            ("docs/Bellman-Sym/API/stage/07-methods.md", "docs/Bellman-Sym/reference/refusals.md"),
        ),
        ("reference_pages.py", ("docs/Bellman-Sym/reference/methods.md",)),
    ):
        arguments = [argument for name in pages for argument in ("--page", name)]
        run = subprocess.run(
            [sys.executable, str(HOOKS / script), "--check", *arguments],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert run.returncode == 0, f"{script}\n{run.stdout}\n{run.stderr}"
    for path in sorted(Path(ROOT / "docs").rglob("*.md")):
        if path.name == "changelog.md":
            continue
        for block in FENCE.findall(path.read_text(encoding="utf-8")):
            for entry in _entries(yaml.load(block, Loader=TagPreservingLoader)):
                method = entry.get("method")
                tag = method.get("__yaml_tag__") if isinstance(method, dict) else method
                settings = entry.get("settings") or {}
                assert tag not in ("Cartesian", "!Cartesian"), (path, entry)
                assert "grid" not in entry, (path, entry)
                if tag in ("Linear", "pchip", "egm") and {"orders", "bounds"} & set(settings):
                    assert "grid" in settings, (path, entry)


def test_item_5_no_methods_file_and_no_test_writes_a_retired_grid():
    """The part of item 5 a test asserts: the suites run on files that hold no
    retired form of a grid; the suites and their files hold no retired form:
    no methods file under `applications/` or among the Workbench's fixtures
    writes `!Cartesian` as a method, the key `grid` beside `method`, or
    `orders` and `bounds` beside a representation or `!egm` without the
    setting `grid`; and no test of the package, of the Workbench or of an
    application names `!Cartesian` as a method. The comparison of the
    suites' failures with main's stays with the report."""
    files = sorted(ROOT.glob("applications/*/declaration/**/*.yml")) + sorted(
        ROOT.glob("packages/bellman-workbench/tests/fixtures/**/methods.yml")
    )
    checked = 0
    for path in files:
        mapping = read_yaml_mapping(path, rule="readable-file", address=None)
        if not isinstance(mapping.get("methods"), list):
            continue
        for entry in load_methods(path)["methods"]:
            checked += 1
            tag = (entry.get("method") or {}).get("__yaml_tag__")
            assert tag != "Cartesian" and "grid" not in entry, (path, entry)
            if tag in ("Linear", "pchip", "egm"):
                assert entry.get("settings", {}).get("grid") == CARTESIAN or (
                    tag == "Linear" and entry["on"] == "policy.evaluate"
                ), (path, entry)
    assert checked > 100
    retired = re.compile(r"""["']method["']: ["']!?Cartesian["']|method: !Cartesian\b""")
    folders = [ROOT / "packages/bellman/tests", ROOT / "packages/bellman-workbench/tests"]
    folders += sorted(ROOT.glob("applications/*/tests")) + sorted(
        ROOT.glob("applications/*/code/tests")
    )
    for folder in folders:
        for path in sorted(folder.rglob("*.py")):
            if path.name == Path(__file__).name:
                continue
            assert retired.search(path.read_text(encoding="utf-8")) is None, path
