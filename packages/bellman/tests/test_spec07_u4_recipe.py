"""The acceptance file of unit U4 of the build of specification 0.7, the
recipe and the trellis: one test for each of the three acceptance items of
§U4 of the implementation specification, named `test_item_<n>_<claim>`. The
corpus: the trellis files of the two new applications, beside their stage
files and additions under `tests/additions/new-applications/`, and the
declaration folder of the cons-port application, whose recipes and trellis
files name additions beside each stage file.
"""

from __future__ import annotations

import shutil

import pytest
from conftest import CONS_PORT, NEW_APPLICATIONS

from bellman.factory.trellis import positions
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.stage_answers import entry_perch
from bellman.trellis import (
    derivative_missing,
    elaborate_trellis,
    load_recipe,
    load_trellis,
    methodize_trellis,
    specify_trellis,
    trellis_selection,
)


def additions_of(stage):
    """The file names of the additions read into a stage occurrence."""
    return [held["path"].rsplit("/", 1)[1] for held in stage.provenance.get("additions", ())]


def words(trellis):
    """The printed word of every occurrence, by position."""
    return {
        (h, key): repr(stage).split(", ", 1)[1][:-1] for h, key, _, stage in positions(trellis)
    }


def test_item_1_application_a_elaborates_with_two_addition_stacks_and_its_connector_binds():
    """Application A's trellis, six occurrences of one stage file, the last
    working period with the additions `pension.bl` and `vfi.bl` and the five
    earlier periods with `pension.bl` and `egm.bl`, elaborates; each
    occurrence holds the additions its record names, in order, and the
    methods they type; the inter-period connector `{a: k, q: p}` binds `a`
    to `k` and `q` to `p` on every pair, since the structural addition is
    read at every occurrence (F42), and every route is certified; the
    derivative `D_{a}V[>]` the endogenous grid method's line reads is stated
    by the supplying occurrence, so no reading is left unmet (F49). With the
    structural addition left out at the last occurrence, the connector names
    a field that occurrence lacks, and the selection reports it under
    `endpoint-unresolved`, naming the occurrence."""
    syntactic = load_trellis(NEW_APPLICATIONS / "A-buffer-stock-pension/trellis.yml")
    elaborated = elaborate_trellis(syntactic)
    assert words(elaborated) == {(h, "buffer_stock"): "methods" for h in range(6)}
    stages = [elaborated["periods"][h]["stages"]["buffer_stock"] for h in range(6)]
    assert additions_of(stages[0]) == ["pension.bl", "vfi.bl"]
    assert all(additions_of(stage) == ["pension.bl", "egm.bl"] for stage in stages[1:])
    assert stages[0].methods["cntn_to_dcsn"].word == "!vfi" and "policy" not in stages[0].methods
    assert all(
        stage.methods["policy"].word == "!egm" and "cntn_to_dcsn" not in stage.methods
        for stage in stages[1:]
    )
    selection = trellis_selection(elaborated)
    pairs = {(pair.writing.field, pair.reading.field) for pair in selection.pairs}
    assert pairs == {("a", "k"), ("q", "p")}
    assert [route.status for route in selection.routes] == ["certified"] * 5
    assert selection.diagnostics == () and derivative_missing(elaborated, selection) == ()
    # the methods verb binds nothing at the trellis: the additions are the
    # construction's
    assert methodize_trellis(elaborated, syntactic) == elaborated
    # the structural addition left out at the last occurrence (F42)
    partial = {**syntactic, "periods": [dict(period) for period in syntactic["periods"]]}
    record = partial["periods"][0]["stages"]["buffer_stock"]
    partial["periods"][0] = {
        **partial["periods"][0],
        "stages": {"buffer_stock": {**record, "methods": []}},
    }
    unresolved = [
        diagnostic
        for diagnostic in trellis_selection(elaborate_trellis(partial)).diagnostics
        if diagnostic.rule == "endpoint-unresolved"
    ]
    assert [diagnostic.address for diagnostic in unresolved] == ["inter_connectors[0]"]
    assert "'p' names no arrival state field of periods[0]" in unresolved[0].message


def test_item_2_application_b_elaborates_with_its_terminal_period_and_the_added_arrival_builder():
    """Application B's trellis, fifteen periods of the worker's saving stage,
    the choice stage and the retiree's saving stage, with the terminal stage
    in the terminal period, elaborates with every occurrence holding its
    addition. The choice stage's file alone is entered at its decision
    perch; its addition adds the arrival builders whole, so the unioned
    stage is entered at the arrival perch and the period's connector
    `{y_f: a, y_p: p}` reaches the fields the addition adds (F43); the
    terminal period's connector reaches the terminal stage from both
    branches of the choice and from the retiree's stage, and those routes
    are certified."""
    folder = NEW_APPLICATIONS / "B-retirement-choice-pension"
    syntactic = load_trellis(folder / "trellis.yml")
    elaborated = elaborate_trellis(syntactic)
    assert len(positions(elaborated)) == 46
    held = {word for (h, key), word in words(elaborated).items() if key != "terminal"}
    assert held == {"methods"}
    assert words(elaborated)[0, "terminal"] == "symbolic"
    alone = elaborate_stage(load_stage(folder / "stage/choice.bl"))
    choice = elaborated["periods"][1]["stages"]["ret_choice"]
    assert (entry_perch(alone), entry_perch(choice)) == ("dcsn", "arvl")
    assert "dcsn_to_arvl" in choice.builder.bwd.list()
    assert "dcsn_to_arvl" not in alone.builder.bwd.list()
    assert additions_of(choice) == ["pension_choice.bl"]
    selection = trellis_selection(elaborated)
    into_choice = {
        pair.reading.field for pair in selection.pairs if pair.reading.key == "ret_choice"
    }
    assert into_choice == {"a", "p"}
    terminal = [route for route in selection.routes if route.destination == (0, "terminal")]
    assert [route.status for route in terminal] == ["certified"] * 3
    assert {route.source[1] for route in terminal} == {"ret_choice", "retiree_saving"}


def test_item_3_cons_ports_files_bind_their_occurrences_and_a_stacked_pair_is_refused(tmp_path):
    """Each of cons-port's eight trellis files, the two orders through their
    recipes and the six files of records directly, binds every occurrence
    with the addition beside its stage file that the file names in place of
    the YAML selection: every occurrence is specified, every route
    certified, nothing reported, and no derivative reading unmet. The
    occurrence's additions are the file's, `methods.vfi.bl` for the
    consumption stage of the value-iteration order and `methods.reference.bl`
    for the portfolio stage of the reference files. With the portfolio
    selection that states no derivative in the reference file's record, the
    consumption stage's endogenous grid line reads `D_{a}V[>]` of a value
    that carries none, which the selection reports under
    `derivative-missing` at each supplying portfolio occurrence and refuses
    nowhere (F49, through an addition's line). The portfolio stage's
    selection stacked with its reference variant at one occurrence is
    refused under `declared-twice`, the refusal naming both files, at the
    stage and through a recipe, which names the occurrence."""
    plain, vfi_file, reference = "methods.bl", "methods.vfi.bl", "methods.reference.bl"
    vfi_reference = "methods.vfi_reference.bl"
    expected = {
        "spec.cons-port.yml": {"cons": plain, "disc": plain, "port": plain},
        "spec.port-cons.yml": {"cons": plain, "disc": plain, "port": plain},
        "trellis.port-cons-vfi.yml": {"cons": vfi_file, "disc": plain, "port": plain},
        "trellis.reference-cons-only.yml": {"cons": reference, "disc": plain, "noport": plain},
        "trellis.reference-cons-port.yml": {"cons": reference, "disc": plain, "port": reference},
        "trellis.reference-port-cons.yml": {"cons": reference, "disc": plain, "port": reference},
        "trellis.reference-port-cons-vfi.yml": {
            "cons": vfi_reference, "disc": plain, "port": reference
        },
        "trellis.reference-port-only.yml": {"disc": plain, "port": reference},
    }
    for name, selections in expected.items():
        if name.startswith("spec."):
            syntactic = load_recipe(CONS_PORT, name)
        else:
            syntactic = load_trellis(CONS_PORT / name)
        specified = specify_trellis(syntactic)
        assert set(words(specified).values()) == {"specified"}, name
        for h, key, _, stage in positions(specified):
            assert additions_of(stage) == [selections[key]], (name, h, key)
        selection = trellis_selection(specified)
        assert {route.status for route in selection.routes} == {"certified"}, name
        assert selection.diagnostics == (), name
        assert derivative_missing(specified, selection) == (), name
    vfi = specify_trellis(load_trellis(CONS_PORT / "trellis.port-cons-vfi.yml"))
    assert vfi["periods"][0]["stages"]["cons"].methods["cntn_to_dcsn"].word == "!vfi"
    egm = specify_trellis(load_recipe(CONS_PORT, "spec.port-cons.yml"))
    assert egm["periods"][0]["stages"]["cons"].methods["policy"].word == "!egm"
    # the portfolio selection without the envelope line and without the
    # representation of its value, at every portfolio occurrence of the
    # reference trellis: the reading of the period after each is reported at
    # it, and the terminal period's own reading falls to the terminal data
    registry = tmp_path / "declaration"
    shutil.copytree(CONS_PORT, registry)
    without_marginals = registry / "trellis.reference-port-cons.yml"
    without_marginals.write_text(
        without_marginals.read_text(encoding="utf-8").replace(
            "stages/port/methods.reference.bl", "stages/port/methods.without_marginals.bl"
        ),
        encoding="utf-8",
    )
    reported = derivative_missing(specify_trellis(load_trellis(without_marginals)))
    assert [(item.rule, item.address) for item in reported] == [
        ("derivative-missing", f"periods[{h}].stages['port']") for h in range(5)
    ]
    assert all(
        "block 'policy' reads `D_{a}V[>]`" in item.message
        and "through the pass-through of disc" in item.message
        for item in reported
    )
    assert {item.candidates for item in reported} == {("port:function:dcsn:V", "k")}
    # the stacked pair, at the stage and through a recipe
    port = CONS_PORT / "stages/port"
    stacked = [port / "methods.bl", port / "methods.reference.bl"]
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(load_stage(port / "port.bl", stacked))
    assert refused.value.rule == "declared-twice"
    assert "methods.bl:26" in str(refused.value)
    assert "methods.reference.bl:20" in str(refused.value)
    recipe = (registry / "spec.port-cons.yml").read_text(encoding="utf-8")
    (registry / "spec.stacked.yml").write_text(
        recipe.replace(
            "methods: {all: [stages/port/methods.bl]}",
            "methods: {all: [stages/port/methods.bl, stages/port/methods.reference.bl]}",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConstructionError) as refused:
        elaborate_trellis(load_recipe(registry, "spec.stacked.yml"))
    assert refused.value.rule == "declared-twice" and "methods.reference.bl" in str(refused.value)
    occurrences = ", ".join(f"periods[{h}].stages['port']" for h in range(6))
    assert refused.value.__notes__ == ["Affected stage occurrences: " + occurrences]
