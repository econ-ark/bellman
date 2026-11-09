"""The acceptance file of unit D2 of the implementation plan of Model
Interface 0.9, the package record of a refusal: one test for each of the six
acceptance items of the plan's §2 D2, named `test_item_<n>_<claim>`.

The record is `bellman.refusals`. A `ConstructionError` carries, beside the
item it is raised at, the related locations the sentence names (`related`,
each a `Location` with its role, its file, its range and its address) and
the action where the check establishes the edit (`write`), both printed on
lines after the sentence; a `FactoryError` carries the line and the column
of a refused YAML key; a connection `Diagnostic` names the finding it rests
on (`depends_on`). The examples are those of `bellman.refusal_examples`,
provoked as the catalogue provokes them.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest
from conftest import ROOT

from bellman.__main__ import main
from bellman.factory.connections import connection_report
from bellman.refusal_catalogue import refusal_of, text_of
from bellman.refusal_examples import CORPUS, EXAMPLES
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage import load_stage
from bellman.trellis import elaborate_trellis, load_trellis, specify_trellis

# the four refusals of the union of a stage file with its additions, each
# positioned at the later item and carrying the earlier one as a related
# location: the rule, the later item's file, range and address, and the
# earlier item's file and address
UNION_REFUSALS = [
    ("declared-twice", ("m.bl", 2, 29, 2, 49, "policy.policy.method"), ("m.bl", "policy.method")),
    ("label-not-in-parent", ("m.bl", 3, 5, 5, 6, "dcsn_to_cntn.rent"), ("t.bl", "dcsn_to_cntn")),
    ("type-conflict", ("m.bl", 2, 26, 2, 38, "cntn_to_dcsn.out.V"), ("t.bl", "cntn_to_dcsn.out.V")),
    ("metadata-mismatch", ("m.bl", 1, 1, 1, 15, "1"), ("t.bl", "1")),
]


def position(error):
    """The file, the range and the address of a refusal."""
    return error.file, error.line, error.column, error.end_line, error.end_column, error.address


def test_item_1_a_union_refusal_carries_the_earlier_item_as_a_related_location():
    for rule, later, (file, address) in UNION_REFUSALS:
        error = refusal_of(EXAMPLES[rule])
        assert (error.rule, position(error)) == (rule, later)
        (earlier,) = error.related
        assert (earlier.role, earlier.file, earlier.address) == ("original declaration", file, address)
        assert None not in (earlier.line, earlier.column, earlier.end_line, earlier.end_column)
        # the sentence is as it was: it names the earlier item's position in
        # words, and the related location follows it on a line of its own
        assert f"{earlier.file}:{earlier.line}:{earlier.column} (term address {address!r})" in error.message
        assert str(error).splitlines()[0].endswith(f"(address {later[-1]!r}; rule {rule})")
        assert f"\n  {earlier}" in str(error)
    error = refusal_of(EXAMPLES["metadata-mismatch"])
    assert tuple(error.related[0]) == ("original declaration", "t.bl", 1, 1, 1, 13, "1")
    assert error.write == "Write `@methods: cons`"
    assert str(error).endswith("\n  original declaration: t.bl:1:1-1:13 (address '1')\n  write: Write `@methods: cons`")


def test_item_2_a_duplicate_yaml_key_and_a_setting_outside_its_set_are_positioned(tmp_path, with_addition):
    trellis = tmp_path / "trellis.yml"
    trellis.write_text(
        f"periods:\n  - stages:\n      cons: {{stage: {ROOT / CORPUS['cons']}}}\n    connectors: []\n"
        "periods: []\ninter_connectors: []\n",
        encoding="utf-8",
    )
    with pytest.raises(FactoryError) as refused:
        load_trellis(trellis)
    error = refused.value
    # the second key, with the first as a related location
    assert (error.rule, error.file, error.line, error.column, error.address) == (
        "trellis-file-shape", str(trellis), 5, 1, "periods")
    assert tuple(error.related[0]) == ("original declaration", str(trellis), 1, 1, None, None, "periods")
    assert str(error).startswith(f"{trellis}:5:1: address 'periods': the key 'periods' is written twice")
    assert str(error).endswith(f"\n  original declaration: {trellis}:1:1 (address 'periods')")
    # a value outside a declared setting's set: at the declaration in the
    # addition, with the key of the settings file as a related location
    example = EXAMPLES["setting-outside-set"]
    stage = with_addition(text_of(example), example.additions[0][1])
    settings = tmp_path / "settings.yml"
    settings.write_text("settings:\n  n_a: 30\n  a_min: -1.0\n  a_max: 20.0\n", encoding="utf-8")
    with pytest.raises(ConstructionError) as refused:
        stage.configure(settings)
    error = refused.value
    assert (error.rule, error.file, error.line, error.address) == (
        "setting-outside-set", "methods.bl", 3, "methods.bl:3")
    assert tuple(error.related[0]) == ("rejected setting", str(settings), 3, 3, None, None, "a_min")
    # a declared setting the file leaves without a value: the file itself
    unvalued = tmp_path / "unvalued.yml"
    unvalued.write_text("settings:\n  a_min: 0.0\n  a_max: 20.0\n", encoding="utf-8")
    with pytest.raises(ConstructionError) as refused:
        stage.configure(unvalued)
    assert refused.value.rule == "setting-unvalued"
    assert tuple(refused.value.related[0]) == ("settings source", str(unvalued), None, None, None, None, None)
    # the trellis route: a record naming the stage file, the addition and the
    # settings file is bound by `specify_trellis` with the record's files, so
    # that the refusal carries the same key
    (tmp_path / "t.bl").write_text(text_of(example), encoding="utf-8")
    (tmp_path / "methods.bl").write_text(example.additions[0][1], encoding="utf-8")
    bound = tmp_path / "bound.yml"
    bound.write_text(
        "periods:\n  - stages:\n      t: {stage: t.bl, methods: methods.bl, settings: settings.yml}\n"
        "    connectors: []\ninter_connectors: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ConstructionError) as refused:
        specify_trellis(load_trellis(bound))
    assert (refused.value.rule, refused.value.address) == ("setting-outside-set", f"{tmp_path / 'methods.bl'}:3")
    assert tuple(refused.value.related[0]) == ("rejected setting", str(settings), 3, 3, None, None, "a_min")


def test_item_3_a_syntax_refusal_carries_the_token_s_end_and_a_typing_entry_refusal_its_span(elaborate_text):
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\n[id=b, (x : ℝ) : !contrl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n")
    error = refused.value
    assert (error.rule, position(error)) == ("syntax", ("t.bl", 2, 18, 2, 25, None))
    # the lowering's refusal: the end of the token it refuses, and the action
    # as the refusal's own field, which the message does not repeat
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\n\n[id=b, (v) : !cntn -> (w) : !dcsn] {\n    w = v[keep][~]\n}\n")
    error = refused.value
    assert (error.rule, error.line, error.column, error.end_line, error.end_column) == ("syntax", 4, 17, 4, 18)
    assert error.write == "write one perch mark first, as `v[~][keep]`"
    assert error.write not in error.message
    # a typing entry: the entry's range and its term address in the
    # constructed term, the first entry of a pair as a related location
    error = refusal_of(EXAMPLES["no-method-for-derivative"])
    assert (error.rule, position(error)) == ("no-method-for-derivative", ("t.bl", 3, 1, 3, 19, "7"))
    error = refusal_of(EXAMPLES["component-typed-twice"])
    assert position(error) == ("t.bl", 10, 35, 10, 62, "cntn_to_dcsn.evaluate[V].method")
    assert tuple(error.related[0]) == (
        "original declaration", "t.bl", 10, 7, 10, 32, "cntn_to_dcsn.evaluate.method")
    assert "at t.bl:10:7 and by" in error.message


def test_item_4_a_route_finding_beside_an_authored_cycle_names_the_cycle_s_address():
    stages = {key: load_stage(ROOT / CORPUS[key]) for key in ("disc", "port")}
    cycle = elaborate_trellis({
        "periods": [{"stages": stages, "connectors": [{"disc.a": "port.k"}, {"port.m_next": "disc.a"}]}],
        "inter_connectors": [],
    })
    diagnostics = connection_report(cycle).diagnostics
    (authored,) = [held for held in diagnostics if held.rule == "authored-cycle"]
    routes = [held for held in diagnostics if held.rule.startswith("route-")]
    assert (authored.address, authored.depends_on) == ("periods[0].connectors[0]", None)
    assert [held.depends_on for held in routes] == [authored.address, authored.address]
    # a use two entries claim: the route rests on the claim's finding
    stages = {key: load_stage(ROOT / CORPUS[name]) for key, name in (("S", "disc"), ("T", "port"), ("U", "port"))}
    claimed = elaborate_trellis({
        "periods": [{"stages": stages, "connectors": [{"S.a": "T.k"}, {"S.a": "U.k"}]}],
        "inter_connectors": [],
    })
    diagnostics = connection_report(claimed).diagnostics
    (claim,) = [held for held in diagnostics if held.rule == "use-claimed-twice"]
    routes = [held for held in diagnostics if held.rule.startswith("route-")]
    assert claim.address == "periods[0].connectors[1]" and claim.depends_on is None
    assert routes and all(held.depends_on == claim.address for held in routes)


def test_item_5_the_replaced_examples_reach_their_own_rules_and_the_binder_is_refused(elaborate_text):
    # the two examples that reached another rule before this unit; that every
    # entry of the catalogue reaches its own rule is asserted by the
    # parametrized case of test_refusals.py
    error = refusal_of(EXAMPLES["one-implicit-statement"])
    assert (error.rule, error.address) == ("one-implicit-statement", "policy.second")
    error = refusal_of(EXAMPLES["value-input-role"])
    assert (error.rule, error.address) == ("value-input-role", "cntn_to_dcsn.value")
    # the expectation binder that an enclosing operator already binds, a
    # `ValueError` of the typing walk before this unit
    with pytest.raises(ConstructionError) as refused:
        elaborate_text("@stage: t\nz ~ N(0,1)\nw ~ N(E_{z}(E_{z}(z)), 1)\n")
    error = refused.value
    assert (error.rule, error.address, error.line) == ("declared-once", "3", 3)
    assert "binds 'z', a name already bound where it stands" in error.message


def test_item_6_the_standalone_command_prints_the_first_line_unchanged(tmp_path):
    example = EXAMPLES["header-coordinate"]
    file = tmp_path / "t.bl"
    file.write_text(text_of(example), encoding="utf-8")
    error = refusal_of(example)
    assert error.write == "Remove x_d from the header: `(V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu) : !dcsn`"
    out = io.StringIO()
    with redirect_stdout(out):
        assert main([str(file)]) == 1
    first, *after = out.getvalue().splitlines()
    # the first line is the position, the sentence, the address and the
    # rule, as before the fields; the action follows on a line of its own
    assert first == (
        f"{file}:5:1-7:2: {error.message} (address 'cntn_to_dcsn'; rule header-coordinate)"
    )
    assert after == [f"  write: {error.write}"]
