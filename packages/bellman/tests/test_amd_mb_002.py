"""The acceptance file of AMD-MB-002, the written place of a representation:
one test for each of the items 1 to 5 of the amendment's §6, named
`test_item_<n>_<claim>`, on the stage files and the methods files of
`applications/buffer-stock` and `applications/cons-port`. Item 6, the suites
compared by the names of their failures with those of `main`, is verified by
the runs the build's report records. The decisions the build took are the rows
MB-X of the development repository's decisions file
`MB-X-the-written-place-of-a-representation.md`.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import ROOT, fresh_stage

from bellman.refusals import (
    REPRESENTATION_ON_BUILDER,
    REPRESENTATION_ON_DERIVATIVE_LINE,
    RULE_E,
    RULE_G,
    RULE_I,
    TargetError,
)
from bellman.stage.sources import load_methods

BUFFER_STOCK = ROOT / "applications/buffer-stock/declaration"
CONS_PORT = ROOT / "applications/cons-port/declaration"
BUFFER_STOCK_STAGE = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
CONS_STAGE = "applications/cons-port/declaration/stages/cons/cons.bl"
PORT_STAGE = "applications/cons-port/declaration/stages/port/port.bl"
HOOKS = ROOT / "docs/_hooks"
# the grid of the consumption stage's representation, as cons.yml writes it
# (AMD-MB-003)
CARTESIAN = {"grid": "!Cartesian", "orders": {"m": "n_m"}, "bounds": {"m": ["m_min", "m_max"]}}
# the exogenous grid of savings of `!egm`, as buffer_stock.yml writes it
SAVINGS = {"grid": "!Cartesian", "orders": {"a": "n_a"}, "bounds": {"a": ["a_min", "a_max"]}}
# the buffer-stock method block with its last line an authored
# `evaluate(m[>], c[>], m)`
AUTHORED_EVALUATE = """@methods: buffer_stock

[id=egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c    = evaluate(m[>], c[>], m)  :: [id=cons_choice]
}
"""


def _printed(stage):
    """The place and the method of each line `stage.methods` prints."""
    return [line.split()[:2] for line in str(stage.methods).splitlines()]


def test_item_1_the_buffer_stock_methods_file_as_aas_wrote_it_binds():
    """`!egm` stands on the policy builder and `!Linear` at its Evaluation,
    written `policy.evaluate`; the arrival builder's Evaluation holds the
    marginal block and one `!Linear`, which the entries for the value and for
    the stated derivative both name; `stage.places()` lists the three written
    addresses, of the kind `operator evaluate`."""
    stage = fresh_stage(BUFFER_STOCK_STAGE)
    stage.methodize(BUFFER_STOCK / "methods/buffer_stock.yml")
    printed = _printed(stage)
    assert ["policy", "!egm"] in printed
    assert ["policy:Evaluation", "!Linear"] in printed
    assert ["dcsn_to_arvl:Evaluation", "!marginals"] in printed
    assert printed.count(["dcsn_to_arvl:Evaluation", "!Linear"]) == 1
    value = stage.methods["dcsn_to_arvl.evaluate.value"]
    assert value == stage.methods["dcsn_to_arvl.evaluate.marginal"]
    assert (value.tag, stage.methods["policy.evaluate"].tag) == ("Linear", "Linear")
    places = {row["address"]: row["kind"] for row in stage.places()}
    for address in (
        "policy.evaluate",
        "dcsn_to_arvl.evaluate.value",
        "dcsn_to_arvl.evaluate.marginal",
    ):
        assert places[address] == "operator evaluate", address


@pytest.mark.parametrize(
    ("stage_file", "entries", "rule", "words"),
    [
        (
            BUFFER_STOCK_STAGE,
            [{"on": "policy", "method": "!Linear"}],
            REPRESENTATION_ON_BUILDER,
            ("attached to the Evaluation of a builder", "`on: policy.evaluate`"),
        ),
        (
            CONS_STAGE,
            [
                {
                    "on": "cntn_to_dcsn",
                    "method": "!marginals",
                    "block": str(CONS_PORT / "methods/cons_egm.bl"),
                },
                {"on": "cntn_to_dcsn.envelope", "method": "!Linear", "settings": CARTESIAN},
            ],
            REPRESENTATION_ON_DERIVATIVE_LINE,
            ("cntn_to_dcsn.envelope is a derivative line", "`on: cntn_to_dcsn.evaluate.marginal`"),
        ),
        (
            PORT_STAGE,
            [{"on": "evaluate", "method": "!Linear"}],
            RULE_G,
            ("authors no `evaluate` occurrence", "`on: cntn_to_dcsn.evaluate.value`"),
        ),
        (
            BUFFER_STOCK_STAGE,
            [{"on": "policy.evaluate.value", "method": "!Linear"}],
            RULE_I,
            ("writes the policy and neither a value nor its derivative", "`on: policy.evaluate`"),
        ),
        (
            BUFFER_STOCK_STAGE,
            [{"on": "dcsn_to_arvl.evaluate.marginal", "method": "!Linear"}],
            RULE_I,
            ("no derivative line stands", "`on: dcsn_to_arvl.evaluate.value`"),
        ),
        (
            BUFFER_STOCK_STAGE,
            [
                {
                    "on": "policy",
                    "method": "!egm",
                    "block": str(BUFFER_STOCK / "methods/buffer_stock_egm.bl"),
                    "settings": SAVINGS,
                },
                {"on": "policy.cons_choice.evaluate", "method": "!Linear"},
            ],
            RULE_E,
            ("which carries none", "`on: policy.evaluate`"),
        ),
    ],
    ids=[
        "a representation on a bare builder",
        "a representation on a derivative line",
        "evaluate where the stage authors none",
        "the value of the policy builder",
        "a marginal where no derivative line stands",
        "an evaluate on a line that carries none",
    ],
)
def test_item_2_the_retired_and_the_unwritable_forms_are_refused_naming_the_written_address(
    stage_file, entries, rule, words
):
    """Each retired form, and each written form that names what its builder
    does not write, is refused under its rule, the sentence naming the
    address to write."""
    with pytest.raises(TargetError) as refused:
        fresh_stage(stage_file).methodize({"methods": entries})
    assert refused.value.rule == rule
    for word in words:
        assert word in str(refused.value), (word, str(refused.value))


def test_item_3_an_authored_evaluate_keeps_its_address_and_its_method(tmp_path):
    """With the method block that reads the consumption function by an
    authored `evaluate(m[>], c[>], m)`, the occurrence is a place of its own,
    `policy.cons_choice.evaluate`, distinct from the policy builder's
    Evaluation; a method named there, or by `evaluate` alone, the stage's one
    authored occurrence, is bound at the line's own box."""
    (tmp_path / "egm.bl").write_text(AUTHORED_EVALUATE, encoding="utf-8")
    egm = {"on": "policy", "method": "!egm", "block": str(tmp_path / "egm.bl"), "settings": SAVINGS}
    for target in ("policy.cons_choice.evaluate", "evaluate"):
        stage = fresh_stage(BUFFER_STOCK_STAGE)
        stage.methodize({"methods": [egm, {"on": target, "method": "!Linear"}]})
        assert ["policy.cons_choice", "!Linear"] in _printed(stage), target
        assert ["policy:Evaluation", "!Linear"] not in _printed(stage), target
    places = {row["address"]: row["kind"] for row in stage.places()}
    assert places["policy.cons_choice.evaluate"] == "operator evaluate"
    assert places["policy.evaluate"] == "operator evaluate"
    assert places["evaluate"] == "operator evaluate"


def test_item_4_the_cons_port_folder_reproduces_its_reference_in_both_orders():
    """The cons-port methods files write each representation at the
    Evaluation of its builder, and the solve of both orders against the fixed
    reference, `applications/cons-port/tests/test_reference_solve.py`,
    passes with them."""
    for path in sorted((CONS_PORT / "methods").glob("*.yml")):
        for entry in load_methods(path)["methods"]:
            parts = entry["on"].split(".")
            assert entry["on"] != "evaluate" and "envelope" not in parts, (path.name, entry)
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


def test_item_5_the_pages_state_the_written_form_and_quote_the_files_as_they_stand():
    """The methodization page quotes the entries of the consumption stage's
    methods file as the file writes them, the listings of the pages of
    methods and places and of refusals and the table of method types are
    what the package prints, and no page writes an entry on `evaluate` alone
    or on a derivative line's id."""
    page = (ROOT / "docs/Bellman-Sym/04-methodization.md").read_text(encoding="utf-8")
    written = (CONS_PORT / "methods/cons.yml").read_text(encoding="utf-8")
    entries = written[written.index("methods:\n") :].split("\n\n")[0] + "\n"
    assert f"```yaml\n{entries}```" in page
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
    # an entry on `evaluate` alone or on a derivative line's id, and a
    # representation entry on a bare builder
    retired = re.compile(
        r"^\s*- on: (evaluate|\w+\.\w*(?:envelope|marginal)\w*)\s*(?:#.*)?$", re.MULTILINE
    )
    on_builder = re.compile(
        r"^\s*- on: (?:policy|cntn_to_dcsn|dcsn_to_arvl)\s*\n"
        r"\s*method: !(?:Linear|Cartesian|pchip)\b",
        re.MULTILINE,
    )
    for path in sorted(Path(ROOT / "docs").rglob("*.md")):
        if path.name == "changelog.md":
            continue
        text = path.read_text(encoding="utf-8")
        assert retired.search(text) is None, path
        assert on_builder.search(text) is None, path
