"""The behaviour file, the third of the three layers of the tests
(`packages/bellman/README.md` §8).

What the public operations return on the corpus stages and what each verb
refuses: `load_stage`, `elaborate_stage` and `elaborate_trellis`; the
bindings `methodize`, `calibrate` and `configure`; the graph selector `graph_of`,
the record `semgraph.record` and the drawing
`to_drawing`; the queries `view`, `kernel` and `compile_kernel`; the navigation
of AMD-SG-010 §4; the target inventory; and the six questions AMD-SG-020 §3.1
leaves on the stage, each also a method of it (AMD-SG-007 §10 item 2, kept
here after acceptance). The ten names that amendment removed and the three
verbs it merged are read through the verbs that state their facts. The graphs of the four symbolic corpus stages, their
printed descriptions, definitions and
conditions are the snapshot's and are not asserted here; a claim below that
reads the recording states that another route to a stage gives the recorded
graphs.
"""
import hashlib
import inspect
import math
import re
import json
import subprocess
import sys
import time
from dataclasses import FrozenInstanceError, asdict
from operator import attrgetter
from pathlib import Path

import numpy
import pytest
import yaml

from conftest import (BRANCHING, BUNDLES, JOINT_CHOICE, FINITE_STATE, TWO_NODES, SEQUENTIAL_G, TARGET_STATE_G,
                      SELECTED_LAW, RISKY_PORT, NAMED_CONTROLS, HAFISCAL, SA_SAVINGS_CALIBRATIONS,
                      SMALL_REGISTRY, SHARED_REGISTRY, CORPUS_CALIBRATIONS, SECOND_CALIBRATIONS, CORPUS_METHODS, CORPUS_SETTINGS,
                      CONS_METHODS, PORT_METHODS,
                      SELECTIONS, DURABLES, SHOCK_BRANCHING, TWO_STAGES, ROOT, PRELIMINARY,
                      STAGE_FILES,
                      apart_from_the_address,
                      cons_obs_text, corpus_stage, corpus_text, branching, declarations_copy, flat,
                      emptied_connector_port_cons, emptied_pension, emptied_port_cons,
                      emptied_portfolio, emptied_portfolio_entry,
                      five_mappings_port_cons, graphs_differ,
                      joint_normal, shock_branching, stage_from_text, two_cons_period, two_nodes,
                      GRID_VALUES)
from snapshot.record import recording_path

import bellman
from bellman.stage import elaborate_stage, load_stage, make_stage, method_types
from bellman.trellis import (
    accrete,
    assemble_trellis,
    calibrate_trellis,
    changed_positions,
    configure_trellis,
    elaborate_trellis,
    load_recipe,
    load_trellis,
    methodize_trellis,
    specify_trellis,
)
from bellman.factory.trellis import positions
from bellman.stage import stage_answers
from bellman.stage.elaborated import ElaboratedStage
from bellman.fold.block_lines import symbols
from bellman.refusals import ConstructionError, FactoryError, NotConstructed, TargetError
from bellman.display.drawing import to_drawing
from bellman.native.hypergraphs import copy_native
from bellman.native.identity import Identity, box_identity
from bellman.syntax.source import to_source
from copy import deepcopy
from dataclasses import replace
from bellman.display.answer_encoding import encode_answer
from bellman.native.records import ResolvedName, ExpressionType
from bellman.typing import typed_expressions as S
from bellman.syntax import terms as T
from bellman.stage.boxes import kind_of, origins
from bellman.stage.kernels import affine
from bellman.stage.denotations import box_signature, card, graph_signature
from bellman.stage.grains import block_id_of, graph_of, operators_of
from bellman.stage.kernels import compile_kernel, kernel
from bellman.stage.stage_answers import (
    branches, combination, diagnostics, fields, kind, obligations)
from bellman.factory.joins import period_joins
from bellman.stage.elaborated import BINDING_VERBS, QUERY_METHODS, STAGE_VERBS
from bellman.syntax.decode import from_json
from bellman.stage import binding_verbs
from bellman.stage.levels import declared_version, holds_additions
from bellman.syntax import terms as T
from bellman.typing import typed_expressions as S
from bellman.syntax.lower import item_addresses, parse_with_spans, to_json
from bellman.stage.binding_verbs import calibrate, configure, methodize

STAGES = ("cons", "port", "ez_savings", "cons_savings_iid")
# the nine pages of the stage object's API, one for each level of the way in,
# whose listings `docs/_hooks/stage_object_page.py` prints from the package
STAGE_OBJECT_PAGES = tuple(f"docs/Bellman-Sym/API/stage/{name}.md" for name in (
    "01-the-stage", "02-initial", "03-build", "04-builder", "05-piece", "06-par-and-settings",
    "07-methods", "08-definitions", "09-binding-verbs"))
# a stage whose forward measures are refused: its shock is declared with a
# family the extension does not admit (AMD-SG-010 §3 admits the three discrete
# families, so no corpus stage is refused any longer)
OPAQUE_FAMILY = """@stage: opaque_family
z : ℝ₊
z ~ Weird(0.2, 0.8)
[id=arvl_to_dcsn, (x : ℝ₊, z) : !arvl -> (y : ℝ₊) : !dcsn] { y = x + z }
[id=cntn_to_dcsn, (W : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
 V = E_{z}(W) :: [id=average]
}
"""

# a stage whose value block authors a node: the expectation of W over the income shock
ARRIVAL = """@stage: arrival_value
β : (0,1)
R : ℝ₊₊
y : ℝ₊
y ~ LogNormal(0, 1)
[id=income, (a : ℝ₊, y) : !arvl -> (m : ℝ₊) : !dcsn] {
    m = R*a + y
}
[id=expected_value, (W : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    EW = E_{y}(W) :: [id=integrate, !node]
    V[<] = β*EW
}
"""


def aggregation_box(stage, block):
    return next(box for box in operators_of(stage)
                if block_id_of(box) == block and box_identity(box).kind == "Aggregation")


def as_a_decoded_term_carries_it(table):
    """A definitions table for comparison with one built from a saved AST.

    The address is set aside, since a decoded term is parsed with no span table
    and carries no file position (AMD-SG-017 §4), and so are the declared tags
    of a set and of a function alias, since the saved encodings still record
    the term before §3 of that amendment, in which the lowering dropped the
    annotation of an assignment; the amendment's integration rewrites them
    (§6b)."""
    import dataclasses
    return {identity: dataclasses.replace(
        record, address="", tags=() if record.kind in ("set", "function_alias") else record.tags)
        for identity, record in table.items()}


# load_stage, elaborate_stage, load_trellis, elaborate_trellis and accrete

def test_elaborate_trellis_keeps_the_trellis_and_records_the_source_of_each_new_stage_occurrence(text_of):
    text = text_of("cons")
    occurrence = {"stage": {"text": text, "origin": "cons.bl"}, "methods": {}, "settings": {}, "calibration": {}}
    result = elaborate_trellis({"periods": [{"stages": {"cons": occurrence}, "connectors": []}], "inter_connectors": []})
    stage = result["periods"][0]["stages"]["cons"]
    assert (result["periods"][0]["connectors"], result["inter_connectors"]) == ([], [])
    assert repr(stage) == "ElaboratedStage('cons', symbolic)"
    assert stage.provenance["origin"] == "cons.bl"
    assert stage.provenance["sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_the_four_stopping_points_of_d36_are_elaborate_trellis_and_the_three_verbs(text_of):
    """The four calls of D36 stand: `elaborate_trellis`, then the verbs in
    the order calibrate, methodize, configure. The addition a record names is
    read with the stage text, so the elaborated occurrence holds its methods
    from the first call, the calibration makes it the methodized version,
    `methodize_trellis` changes nothing, and the settings make it the
    specified version."""
    from conftest import CONS_METHODS, CONS_SETTINGS
    from bellman.stage.sources import load_settings
    addition = {"text": CONS_METHODS.read_text(encoding="utf-8"), "origin": str(CONS_METHODS)}
    occurrence = {"stage": {"text": text_of("cons"), "origin": "cons.bl"}, "methods": [addition],
                  "settings": load_settings(CONS_SETTINGS), "calibration": {"ρ": 6.0}}
    trellis = {"periods": [{"stages": {"cons": occurrence}, "connectors": []}], "inter_connectors": []}
    elaborated = elaborate_trellis(trellis)
    calibrated = calibrate_trellis(elaborated, trellis)
    methodized = methodize_trellis(calibrated, trellis)
    specified = configure_trellis(methodized, trellis)
    # the stopping points follow the order of D36: calibrate, methodize, configure
    assert [repr(t["periods"][0]["stages"]["cons"]) for t in (elaborated, calibrated, methodized, specified)] == [
        "ElaboratedStage('cons', methods)", "ElaboratedStage('cons', methodized)",
        "ElaboratedStage('cons', methodized)", "ElaboratedStage('cons', specified)"]
    assert changed_positions(calibrated, methodized) == []


def test_elaborate_trellis_refuses_a_trellis_that_is_no_mapping_and_a_stage_occurrence_without_its_bindings():
    with pytest.raises(FactoryError, match="periods"):
        elaborate_trellis([])
    with pytest.raises(FactoryError, match=r"the record holds no calibration, methods or settings fields"):
        elaborate_trellis({"periods": [{"stages": {"cons": {"stage": {"text": "", "origin": "cons.bl"}}}, "connectors": []}],
                           "inter_connectors": []})


def test_load_stage_reads_a_stage_file_into_its_record_and_elaborate_stage_builds_the_symbolic_stage(path_of, cons):
    record = load_stage(path_of("cons"))
    assert set(record) == {"stage", "calibration", "settings", "methods", "provenance"}
    # the methods of a record are its additions, none for a stage file read alone
    assert (record["calibration"], record["settings"], record["methods"]) == ({}, {}, [])
    assert record["stage"]["origin"] == str(path_of("cons")) and record["provenance"]["origin"] == str(path_of("cons"))
    assert record["provenance"]["sha256"] == hashlib.sha256(record["stage"]["text"].encode("utf-8")).hexdigest()
    stage = elaborate_stage(record)
    assert repr(stage) == "ElaboratedStage('cons', symbolic)"
    assert stage.provenance["origin"] == str(path_of("cons")) and "position" not in stage.provenance
    assert {kind: dict(description) for kind, description in stage.provenance["sources"].items()} == {
        # no addition is described as every empty source is, by the digest of the empty mapping
        "methods": {"origin": "in-memory", "sha256": hashlib.sha256(b'["mapping",[]]').hexdigest()},
        "settings": {"origin": "in-memory", "sha256": hashlib.sha256(b'["mapping",[]]').hexdigest()},
        "calibration": {"origin": "in-memory", "sha256": hashlib.sha256(b'["mapping",[]]').hexdigest()}}
    assert (graphs_differ(stage, cons), apart_from_the_address(stage.definitions) == apart_from_the_address(cons.definitions)) == ([], True)
    # `load_stage` is given the path in the file system and the fixture the path in the repository,
    # and each record of a top-level item is addressed by the file position under the name its own
    # caller wrote (AMD-SG-017 §4)
    def rho(version):
        return next(record.address for record in version.definitions.values()
                    if record.kind == "parameter" and record.identity.field == "ρ")
    assert (rho(stage), rho(cons)) == (
        f"{path_of('cons')}:6", "applications/portfolio-choice/declaration/stages/cons/cons.bl:6")


def test_load_stage_refuses_another_file_type_and_a_missing_file_and_elaborate_stage_a_text_that_does_not_parse(tmp_path):
    with pytest.raises(FactoryError, match=r"\.bl") as refused:
        load_stage(tmp_path / "stage.yaml")
    assert str(tmp_path / "stage.yaml") in str(refused.value) and refused.value.rule == "readable-file"
    with pytest.raises(FactoryError, match="missing.bl") as refused:
        load_stage(tmp_path / "missing.bl")
    assert (refused.value.rule, refused.value.written) == ("readable-file", "missing.bl")
    broken = tmp_path / "broken.bl"
    broken.write_text("@stage: broken\n[id=step] { y = }\n", encoding="utf-8")
    with pytest.raises(ValueError) as refused:
        elaborate_stage(load_stage(broken))
    # the refusal of a text the parser cannot read carries the file, the line and the column
    # as its own fields, under the rule `syntax` (AMD-SG-022 §2)
    assert str(broken) in str(refused.value)
    assert (refused.value.rule, refused.value.file, refused.value.line) == ("syntax", str(broken), 2)


def test_elaborate_stage_refuses_a_path_string_a_mapping_that_is_no_record_and_a_digest_that_disagrees(text_of):
    with pytest.raises(FactoryError) as refused:
        elaborate_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    assert (refused.value.rule, refused.value.write) == ("record-shape", "elaborate_stage(load_stage(path))")
    with pytest.raises(FactoryError, match=r"the record holds no calibration, methods or settings fields") as refused:
        elaborate_stage({"stage": {"text": text_of("cons"), "origin": "cons.bl"}})
    assert refused.value.rule == "record-shape"
    with pytest.raises(FactoryError, match="the supplied module hash disagrees with the text read"):
        elaborate_stage({"stage": {"text": text_of("cons"), "origin": "cons.bl"}, "methods": {}, "settings": {},
                         "calibration": {}, "provenance": {"sha256": "0" * 64}})
    with pytest.raises(FactoryError, match="path string"):
        elaborate_stage({"stage": "applications/portfolio-choice/declaration/stages/cons/cons.bl",
                         "methods": {}, "settings": {}, "calibration": {}})


def test_elaborate_trellis_elaborates_the_records_copies_the_elaborated_stage_occurrences_and_keeps_the_other_keys(path_of, cons):
    record = load_stage(path_of("cons"))
    trellis = {"periods": [{"stages": {"first": record, "second": dict(record)}, "connectors": []},
                           {"stages": {"held": cons}, "connectors": []}],
               "inter_connectors": [{"a": "m"}], "solutions": [], "registry": {"calibration": {"first_age": 20}}}
    elaborated = elaborate_trellis(trellis)
    first, second, held = (elaborated["periods"][0]["stages"]["first"], elaborated["periods"][0]["stages"]["second"],
                           elaborated["periods"][1]["stages"]["held"])
    assert repr(first) == "ElaboratedStage('cons', symbolic)" and dict(first.provenance["position"]) == {"h": 0, "key": "first"}
    assert first is not second and dict(second.provenance["position"]) == {"h": 0, "key": "second"}
    assert first.provenance["versions"] == second.provenance["versions"] and first.bindings.calibration is None
    # the stage object placed by hand is copied and the copy records its position (A62)
    assert held is not cons and graphs_differ(held, cons) == [] and held.definitions == cons.definitions
    assert held.bindings == cons.bindings and dict(held.provenance["position"]) == {"h": 1, "key": "held"}
    assert {name: value for name, value in held.provenance.items() if name != "position"} == dict(cons.provenance)
    assert (elaborated["inter_connectors"], elaborated["solutions"]) == ([{"a": "m"}], [])
    assert elaborated["registry"] == trellis["registry"] and elaborated["registry"] is not trellis["registry"]
    assert graphs_differ(first, cons) == []
    with pytest.raises(FactoryError) as refused:
        elaborate_trellis({"periods": [{"stages": {"cons": {**record, "provenance": {"sha256": "0" * 64}}}, "connectors": []}],
                           "inter_connectors": []})
    assert refused.value.__notes__ == ["Stage occurrence: periods[0].stages['cons']"]
    with pytest.raises(FactoryError, match="periods") as refused:
        elaborate_trellis([])
    assert refused.value.rule == "trellis-file-shape"
    # one mapping per adjacent pair: three periods take two, not one standing for every pair
    with pytest.raises(FactoryError, match="1 inter-period mappings for 3 periods") as refused:
        elaborate_trellis({"periods": [{"stages": {"cons": record}, "connectors": []}] * 3, "inter_connectors": [{"a": "m"}]})
    assert (refused.value.rule, refused.value.address) == ("trellis-file-shape", "inter_connectors")
    broken = {**record, "stage": {"text": record["stage"]["text"].replace("m_d = m", "m_d = "), "origin": "cons.bl"}, "provenance": {}}
    with pytest.raises(ConstructionError) as refused:
        elaborate_trellis({"periods": [{"stages": {"x": broken, "y": dict(broken)}, "connectors": []}], "inter_connectors": []})
    assert refused.value.__notes__ == ["Affected stage occurrences: periods[0].stages['x'], periods[0].stages['y']"]


def test_elaborate_trellis_with_a_second_argument_copies_the_stage_occurrences_of_an_unchanged_file(path_of, text_of):
    record = load_stage(path_of("cons"))
    syntactic = {"periods": [{"stages": {"cons": record}, "connectors": []}, {"stages": {"cons": dict(record)}, "connectors": []}],
                 "inter_connectors": [{"a": "m"}]}
    elaborated = elaborate_trellis(syntactic)
    # the held trellis carries a version bound by hand at the terminal period
    held = elaborated["periods"][0]["stages"]["cons"].calibrate({"ρ": 2.0})
    held_trellis = {**elaborated, "periods": [{"stages": {"cons": held}, "connectors": []}, elaborated["periods"][1]]}
    # the changed file halves the law of motion and writes the grid line as the halved law solved for m_d
    changed = {**record, "stage": {"text": text_of("cons").replace("    a = m_d - c\n", "    a = (m_d - c)/2\n")
                                           .replace("    m_d[>] = a + c[>]                :: [id=endoggrid]",
                                                    "    m_d[>] = 2*a + c[>]              :: [id=endoggrid]"),
                                   "origin": str(path_of("cons"))},
               "provenance": {}}
    again = elaborate_trellis({**syntactic, "periods": [syntactic["periods"][0], {"stages": {"cons": changed}, "connectors": []}]},
                              held_trellis)
    # the unchanged file's stage occurrence is a copy of the held one, its binding included; the changed file's is new
    assert again["periods"][0]["stages"]["cons"] == held and again["periods"][0]["stages"]["cons"] is not held
    assert repr(again["periods"][1]["stages"]["cons"]) == "ElaboratedStage('cons', symbolic)"
    assert again["periods"][1]["stages"]["cons"].provenance["sha256"] != record["provenance"]["sha256"]


def test_accrete_appends_the_period_earlier_in_time_with_its_mapping_and_rewrites_no_record(cons, port):
    trellis = accrete({"periods": [], "inter_connectors": []}, {"stages": {"cons": cons}, "connectors": []})
    # port, appended second and earlier in time, continues to m_next, which the mapping joins to cons's m (A59)
    later = accrete(trellis, {"stages": {"port": port}, "connectors": []}, {"m_next": "m"})
    assert [list(period["stages"]) for period in later["periods"]] == [["cons"], ["port"]] and later["inter_connectors"] == [{"m_next": "m"}]
    assert trellis["periods"][0]["stages"]["cons"] is later["periods"][0]["stages"]["cons"]
    appended = later["periods"][1]["stages"]["port"]
    assert appended is not port and graphs_differ(appended, port) == [] and appended.definitions == port.definitions
    assert dict(appended.provenance["position"]) == {"h": 1, "key": "port"}
    assert (len(trellis["periods"]), trellis["inter_connectors"]) == (1, [])
    # a mapping whose endpoints name no field of the two periods is no refusal since AMD-COMP-001 §3:
    # the trellis is a draft, and its connection report names each unresolved endpoint at the mapping
    from bellman.trellis import connection_report
    draft = accrete(trellis, {"stages": {"port": port}, "connectors": []}, {"a": "k"})
    diagnostics = connection_report(draft).diagnostics
    assert [(d.rule, d.address) for d in diagnostics] == [("endpoint-unresolved", "inter_connectors[0]")] * 2
    assert "'a'" in diagnostics[0].message and "continuation" in diagnostics[0].message
    assert draft["inter_connectors"] == [{"a": "k"}] and connection_report(draft).pairs == ()
    # the earlier period's dictionary is copied, so a write into the result changes no argument
    later["periods"][0]["stages"]["extra"] = port
    assert list(trellis["periods"][0]["stages"]) == ["cons"]
    record = {"stage": {"text": "@stage: t\n", "origin": "t.bl"}, "calibration": {}, "settings": {}, "methods": {}}
    with_records = accrete(later, {"stages": {"t": record}, "connectors": []})
    assert with_records["periods"][2]["stages"]["t"] == record and with_records["periods"][2]["stages"]["t"] is not record
    assert with_records["inter_connectors"] == [{"m_next": "m"}, {}]
    with pytest.raises(FactoryError, match="terminal period") as refused:
        accrete({"periods": [], "inter_connectors": []}, {"stages": {}, "connectors": []}, {"a": "k"})
    assert (refused.value.rule, refused.value.address) == ("trellis-file-shape", "inter_connectors")
    with pytest.raises(FactoryError, match="a mapping from continuation fields") as refused:
        accrete(trellis, {"stages": {}, "connectors": []}, ["a", "k"])
    assert refused.value.write == "{<continuation field>: <arrival field>}"


def test_respecify_trellis_binds_the_changed_records_alone_and_answers_what_specify_trellis_answers():
    """`respecify_trellis(specified, before, syntactic)` answers the trellis
    `specify_trellis(syntactic)` answers, where `specified` is
    `specify_trellis(before)` (model interface specification 0.4, unit L,
    Task 20): every stage occurrence byte for byte as the standard pickle
    writes it, and every other entry, with the keys in the same order, on
    the trellis file of the portfolio-consumption application with the
    settings of `cons` changed in every period, with the text of `disc`
    changed, and with nothing changed. A position whose record is unchanged
    holds the very occurrence `specified` holds; every other holds a new
    one, which `changed_positions` names. A binding refused at a changed
    record is refused as `specify_trellis` refuses it, with the same notes.
    Two syntactic trellises that differ in a connector are refused under
    `trellis-file-shape`, and a trellis bound under other kinds than those
    given under `record-shape`."""
    import pickle

    from bellman.trellis import respecify_trellis

    before = load_recipe(ROOT / "applications/cons-port/declaration", "spec.port-cons.yml")
    specified = specify_trellis(before)

    def edited(edit):
        syntactic = deepcopy(before)
        for period in syntactic["periods"]:
            edit(period["stages"])
        return syntactic

    def byte_for_byte(left, right):
        def rest(trellis):
            return {**trellis, "periods": [{**period, "stages": list(period["stages"])}
                                           for period in trellis["periods"]]}
        assert pickle.dumps(rest(left)) == pickle.dumps(rest(right))
        assert [list(period) for period in left["periods"]] == [list(period) for period in right["periods"]]
        for one, two in zip(left["periods"], right["periods"]):
            for key in one["stages"]:
                assert pickle.dumps(one["stages"][key]) == pickle.dumps(two["stages"][key]), key

    def settings(stages):
        stages["cons"]["settings"] = {**stages["cons"]["settings"], "n_m": 32000}

    def text(stages):
        written = stages["disc"]["stage"]["text"] + "\n"
        stages["disc"]["stage"] = {**stages["disc"]["stage"], "text": written}
        digest = hashlib.sha256(written.encode("utf-8")).hexdigest()
        stages["disc"]["provenance"] = {**stages["disc"]["provenance"], "sha256": digest}

    for edit, key in ((settings, "cons"), (text, "disc")):
        syntactic = edited(edit)
        again = respecify_trellis(specified, before, syntactic)
        byte_for_byte(again, specify_trellis(syntactic))
        renewed = [(place.h, place.key) for place in positions(again) if place.key == key]
        assert changed_positions(specified, again) == renewed and len(renewed) == 6
        for place in positions(again):
            held = specified["periods"][place.h]["stages"][place.key]
            assert (place.stage is held) == (place.key != key), (place.h, place.key)
    unchanged = respecify_trellis(specified, before, deepcopy(before))
    byte_for_byte(unchanged, specified)
    assert all(place.stage is held.stage for place, held in zip(positions(unchanged), positions(specified)))

    # A changed addition is checked during reconstruction, before binding.
    def refused_method(stages):
        entries = stages["cons"]["methods"]
        stages["cons"]["methods"] = [
            {**entry, "text": entry["text"] + "\narvl_to_dcsn.method : !root_find\n"}
            for entry in entries]

    syntactic = edited(refused_method)
    with pytest.raises(Exception) as whole:
        specify_trellis(syntactic)
    with pytest.raises(Exception) as alone:
        respecify_trellis(specified, before, syntactic)
    assert (type(alone.value), str(alone.value), alone.value.__notes__) == (
        type(whole.value), str(whole.value), whole.value.__notes__)
    assert alone.value.__notes__ == ["Affected stage occurrences: " + ", ".join(
        f"periods[{h}].stages['cons']" for h in range(len(before["periods"])))]

    connectors = deepcopy(before)
    connectors["periods"][0]["connectors"] = []
    with pytest.raises(FactoryError) as refused:
        respecify_trellis(specified, before, connectors)
    assert (refused.value.rule, refused.value.address) == ("trellis-file-shape", "periods[0]")
    with pytest.raises(FactoryError) as refused:
        respecify_trellis(specify_trellis(before, kinds=("methods", "settings")), before, edited(settings))
    assert (refused.value.rule, refused.value.address) == ("record-shape", "periods[0].stages['port']")


def test_load_trellis_reads_a_file_that_writes_every_period_and_stage_out(path_of, tmp_path):
    from conftest import CONS_METHODS
    (tmp_path / "ρ.yml").write_text("calibration:\n  ρ: 4.0\n", encoding="utf-8")
    # the template's record writes no methods, which read as no addition
    (tmp_path / "period.yml").write_text(
        "stages:\n  cons: {stage: " + str(path_of("cons")) + ", calibration: ρ.yml, settings: {n_m: 10}}\n"
        "connectors: []\n", encoding="utf-8")
    (tmp_path / "trellis.yml").write_text(
        "periods:\n  - stages:\n      cons:\n        stage: " + str(path_of("cons")) + "\n        calibration: ρ.yml\n"
        "        settings: {n_m: 10}\n        methods: [" + str(CONS_METHODS) + "]\n"
        "    connectors: []\n  - {template: period.yml, repeat: 2}\ninter_connectors:\n  - {a: m}\n", encoding="utf-8")
    syntactic = load_trellis(tmp_path / "trellis.yml")
    assert len(syntactic["periods"]) == 3 and syntactic["inter_connectors"] == [{"a": "m"}, {"a": "m"}]
    record = syntactic["periods"][0]["stages"]["cons"]
    assert record["stage"]["origin"] == str(path_of("cons")) and record["calibration"] == {"ρ": 4.0} and record["settings"] == {"n_m": 10}
    assert record["provenance"]["source_lists"]["calibration"][0]["path"] == str(tmp_path / "ρ.yml")
    assert [addition["origin"] for addition in record["methods"]] == [str(CONS_METHODS)]
    assert syntactic["periods"][1]["stages"]["cons"]["methods"] == []
    assert record["provenance"]["source_lists"]["settings"] == []
    assert syntactic["periods"][2]["stages"]["cons"]["methods"] == []
    assert syntactic["provenance"]["trellis"]["path"] == str(tmp_path / "trellis.yml")
    # one standing mapping is read at `repeat: 1` as well, where it stands for no pair
    (tmp_path / "one.yml").write_text("periods:\n  - {template: period.yml, repeat: 1}\ninter_connectors:\n  - {a: m}\n",
                                      encoding="utf-8")
    one = load_trellis(tmp_path / "one.yml")
    assert (len(one["periods"]), one["inter_connectors"]) == (1, [])
    (tmp_path / "no-periods.yml").write_text("stages: []\n", encoding="utf-8")
    with pytest.raises(FactoryError) as refused:
        load_trellis(tmp_path / "no-periods.yml")
    assert refused.value.rule == "trellis-file-shape" and "periods" in refused.value.message


def test_load_trellis_reads_a_records_methods_as_the_additions_it_names(path_of, tmp_path):
    """A record's `methods` names one `.bl` addition or a list of them, read
    into the record as their texts and origins in the order named, each with
    its provenance entry (specification 0.7, D3 and F76); a mapping, the
    retired inline selection, is refused under `trellis-file-shape`."""
    from conftest import CONS_METHODS
    head = ("!trellis\nperiods:\n  - stages:\n      cons:\n        stage: " + str(path_of("cons"))
            + "\n        calibration: {}\n        settings: {}\n")
    tail = "    connectors: []\ninter_connectors: []\n"
    (tmp_path / "trellis.yml").write_text(
        head + "        methods: [" + str(CONS_METHODS) + "]\n" + tail, encoding="utf-8")
    record = load_trellis(tmp_path / "trellis.yml")["periods"][0]["stages"]["cons"]
    assert record["methods"] == [{"text": CONS_METHODS.read_text(encoding="utf-8"), "origin": str(CONS_METHODS)}]
    assert [entry["path"] for entry in record["provenance"]["source_lists"]["methods"]] == [str(CONS_METHODS)]
    (tmp_path / "one.yml").write_text(head + "        methods: " + str(CONS_METHODS) + "\n" + tail, encoding="utf-8")
    assert load_trellis(tmp_path / "one.yml")["periods"][0]["stages"]["cons"]["methods"] == record["methods"]
    (tmp_path / "inline.yml").write_text(
        head + "        methods:\n          stage: cons\n          methods:\n"
        "            - on: policy\n              method: !egm\n" + tail, encoding="utf-8")
    with pytest.raises(FactoryError) as refused:
        load_trellis(tmp_path / "inline.yml")
    assert refused.value.rule == "trellis-file-shape" and "`.bl` addition" in refused.value.message


# the trellis verbs, assemble_trellis and changed_positions

def test_each_trellis_verb_reads_its_kind_from_the_syntactic_trellis_and_binds_every_position_in_order(registry):
    syntactic = load_recipe(registry, "spec.yml")
    elaborated = elaborate_trellis(syntactic)
    # the addition the recipe names is read with the stage text, so the elaborated occurrences hold
    # their methods before any verb (specification 0.7, F42 and F43)
    assert [repr(s) for _, _, _, s in positions(elaborated)] == ["ElaboratedStage('two_nodes', methods)"] * 3
    calibrated = calibrate_trellis(elaborated, syntactic)
    assert [dict(s.bindings.calibration) for _, _, _, s in positions(calibrated)] == [
        {"β": 0.96, "R": 1.04}, {"β": 0.96, "R": 1.02}, {"β": 0.96, "R": 1.02}]
    assert changed_positions(elaborated, calibrated) == [(0, "two_nodes"), (1, "two_nodes"), (2, "two_nodes")]
    methodized = methodize_trellis(calibrated, syntactic)
    assert changed_positions(calibrated, methodized) == []
    specified = configure_trellis(methodized, syntactic)
    assert [repr(s) for _, _, _, s in positions(specified)] == ["ElaboratedStage('two_nodes', specified)"] * 3
    assert dict(specified["periods"][0]["stages"]["two_nodes"].bindings.settings) == {"n_k": 10}
    # the ordered sources of the record stand on the version, unread by the verbs
    lists = specified["periods"][0]["stages"]["two_nodes"].provenance["source_lists"]["calibration"]
    assert [entry.get("source", entry.get("slot")) for entry in lists] == ["calibration/main", "fill", "calibration/terminal", "terminal"]
    # settings bind at every position without methods (specification 0.7, S1)
    alone = configure_trellis(elaborated, syntactic)
    assert dict(alone["periods"][0]["stages"]["two_nodes"].bindings.settings) == {"n_k": 10}
    # the same mapping again: every position copied, none bound
    again = calibrate_trellis(specified, syntactic)
    assert changed_positions(specified, again) == []
    assert again["periods"][0]["stages"]["two_nodes"] is not specified["periods"][0]["stages"]["two_nodes"]
    assert assemble_trellis(registry, "spec.yml")["periods"][2]["stages"]["two_nodes"] == specified["periods"][2]["stages"]["two_nodes"]


def test_a_verb_binds_where_the_mapping_differs_and_copies_a_position_the_syntactic_trellis_holds_a_stage_at(registry):
    syntactic = load_recipe(registry, "spec.yml")
    model = assemble_trellis(registry, "spec.yml")
    changed = deepcopy(syntactic)
    changed["periods"][1]["stages"]["two_nodes"]["calibration"] = {"β": 0.5, "R": 1.02}
    partly = calibrate_trellis(model, changed)
    assert changed_positions(model, partly) == [(1, "two_nodes")]
    assert dict(partly["periods"][1]["stages"]["two_nodes"].bindings.calibration) == {"β": 0.5, "R": 1.02}
    assert repr(partly["periods"][1]["stages"]["two_nodes"]) == "ElaboratedStage('two_nodes', specified)"
    assert dict(model["periods"][1]["stages"]["two_nodes"].bindings.calibration) == {"β": 0.96, "R": 1.02}   # the earlier trellis is untouched
    # a period built by hand: the syntactic trellis holds a stage object at the key, so there is no mapping to bind with
    by_hand = {**syntactic, "periods": [*syntactic["periods"][:2], {"stages": {"two_nodes": model["periods"][2]["stages"]["two_nodes"]}, "connectors": []}]}
    assert changed_positions(model, calibrate_trellis(model, by_hand)) == []


def test_a_verb_refuses_two_trellises_of_different_positions_and_a_first_argument_holding_a_record(registry):
    syntactic = load_recipe(registry, "spec.yml")
    elaborated = elaborate_trellis(syntactic)
    with pytest.raises(FactoryError) as refused:
        calibrate_trellis(elaborated, {"periods": syntactic["periods"][:2], "inter_connectors": [{}]})
    assert refused.value.rule == "trellis-file-shape" and "second argument" in str(refused.value)
    with pytest.raises(FactoryError) as refused:
        calibrate_trellis(syntactic, syntactic)
    assert refused.value.rule == "record-shape"


def test_a_fill_a_verb_binds_stands_in_the_new_version_source_lists_marked_bound(registry):
    model = assemble_trellis(registry, "spec.yml")
    filled = load_recipe(registry, "spec.yml", fill={"β": 0.9})
    recalibrated = calibrate_trellis(model, filled)
    lists = recalibrated["periods"][1]["stages"]["two_nodes"].provenance["source_lists"]
    # the record's calibration list, its slot marked bound, stands on the version the verb bound (A52)
    assert [(entry.get("source", entry.get("slot")), entry.get("bound")) for entry in lists["calibration"]] == [
        ("calibration/main", None), ("fill", True)]
    # the elaboration's lists stand for the other kinds, where the slot was unbound
    assert [entry["bound"] for entry in lists["settings"] if "slot" in entry] == [False]


def test_a_list_valued_parameter_is_bound_again_only_when_a_fill_changes_its_entries(tmp_path):
    from bellman.refusal_examples import REGISTRY_FILES, write_registry
    # a parameter over a product set is written as a list, which `calibrate` holds as a tuple; a fill of the
    # same entries changes no binding, and a fill of other entries binds every position (found on the
    # Benhabib registry, whose `wage_fn` and `R_vec` are such parameters)
    path = "stages/two_nodes/two_nodes.bl"
    stage = REGISTRY_FILES[path].replace("R : ℝ₊₊\n", "R : ℝ₊₊\nw : ℝ × ℝ\n")
    directory = write_registry(tmp_path / "listed", {**SMALL_REGISTRY, path: stage,
                                                     "calibration/main.yml": "calibration:\n  β: 0.96\n  R: 1.02\n  w: [1.0, 2.0]\n"})
    model = assemble_trellis(directory, "spec.yml")
    assert model["periods"][0]["stages"]["two_nodes"].bindings.calibration["w"] == (1.0, 2.0)
    same = load_recipe(directory, "spec.yml", fill={"w": [1.0, 2.0]})
    assert changed_positions(model, calibrate_trellis(model, same)) == []
    other = load_recipe(directory, "spec.yml", fill={"w": [1.0, 3.0]})
    assert len(changed_positions(model, calibrate_trellis(model, other))) == 3


def test_a_parameter_two_stages_of_a_period_declare_is_one_parameter_of_the_period_supplied_once(shared_registry, tmp_path):
    """A parameter name two stages of one period declare names one parameter
    of the period (AMD-COMP-001 §2.3): the registry's two-node stage declares
    `β` in ℝ₊₊ and its calibration file supplies it, the discounting stage
    declares `β` in (0,1) and its calibration list holds a slot alone, and
    both are bound with the file's value; the sets agree in their meet, (0,1),
    so a value in it binds both whichever stage's source supplies it; an equal
    value supplied by both sources agrees; and the same spelling in another
    period is another parameter, which takes that period's value."""
    from bellman.refusal_examples import write_registry
    from bellman.factory.trellis import already_bound
    model = assemble_trellis(shared_registry, "spec.yml")
    for period in model["periods"]:
        assert [dict(s.bindings.calibration) for s in period["stages"].values()] == [{"β": 0.96, "R": 1.02}, {"β": 0.96}]
        assert period["stages"]["disc"].par["β"].value == 0.96
    # the same value from both sources, and a value in the meet from the discounting stage's slot alone
    agreed = assemble_trellis(shared_registry, "spec.yml", disc_fill={"β": 0.96})
    assert [[dict(s.bindings.calibration) for s in p["stages"].values()] for p in agreed["periods"]] == [
        [dict(s.bindings.calibration) for s in p["stages"].values()] for p in model["periods"]]
    both = assemble_trellis(shared_registry, "spec.yml", fill={"β": 0.5}, disc_fill={"β": 0.5})
    assert [s.par["β"].value for s in both["periods"][0]["stages"].values()] == [0.5, 0.5]
    # direct calibration of the elaborated trellis and the source-loaded specification agree
    filled = load_recipe(shared_registry, "spec.yml", fill={"β": 0.9})
    direct = calibrate_trellis(elaborate_trellis(filled), filled)
    assert [dict(s.bindings.calibration) for s in direct["periods"][1]["stages"].values()] == [{"β": 0.9, "R": 1.02}, {"β": 0.9}]
    assert all(already_bound(direct["periods"][h]["stages"][key], "calibration",
                             specify_trellis(filled, kinds=["calibration"])["periods"][h]["stages"][key].bindings.calibration)
               for h in range(2) for key in ("two_nodes", "disc"))
    # the same spelling in two periods: the discounting stage stands in the terminal period alone, with its
    # own value there, and the two-node stage keeps the file's value in the period before it
    apart = write_registry(tmp_path / "apart", {
        **SHARED_REGISTRY,
        "calibration/terminal.yml": "calibration:\n  β: 0.5\n",
        "period.yml": "name: one\nstages: [two_nodes]\nconnectors: []\n",
        "trellis.yml": "periods:\n  - {stages: [two_nodes, disc], connectors: []}\n  - {template: period.yml, repeat: 1}\n"
                       "inter_connectors:\n  - {a: k}\n",
        "spec.yml": SHARED_REGISTRY["spec.yml"].replace(
            "calibration: {all: [calibration/main, $fill]}", "calibration: {all: [calibration/main, $fill], '0-0': [calibration/terminal]}"
        ).replace("stage: stages/disc/disc.bl\n", "stage: stages/disc/disc.bl\n    periods: [0, 0]\n")})
    periods = assemble_trellis(apart, "spec.yml")["periods"]
    assert [s.par["β"].value for s in periods[0]["stages"].values()] == [0.5, 0.5]
    assert [s.par["β"].value for s in periods[1]["stages"].values()] == [0.96]


def test_a_changed_supplier_of_a_shared_parameter_binds_every_stage_of_the_period_that_declares_it_again(shared_registry):
    """A fill that changes the value of `β` through the two-node stage's list
    rebinds the discounting stage of each period too, whose own record is
    unchanged: `respecify_trellis` names both at every period among the
    positions changed and answers what `specify_trellis` answers, stage
    occurrence by stage occurrence as the standard pickle writes them; a fill
    of the value both hold, which changes the two-node stage's record alone,
    rebinds that stage alone and keeps the discounting stage's occurrences."""
    import pickle
    from bellman.trellis import respecify_trellis
    before = load_recipe(shared_registry, "spec.yml")
    model = specify_trellis(before)
    after = load_recipe(shared_registry, "spec.yml", fill={"β": 0.9})
    again = respecify_trellis(model, before, after)
    assert changed_positions(model, again) == [(0, "two_nodes"), (0, "disc"), (1, "two_nodes"), (1, "disc")]
    assert [s.par["β"].value for s in again["periods"][1]["stages"].values()] == [0.9, 0.9]
    whole = specify_trellis(after)
    for h in range(2):
        for key in ("two_nodes", "disc"):
            assert pickle.dumps(again["periods"][h]["stages"][key]) == pickle.dumps(whole["periods"][h]["stages"][key]), (h, key)
    same = respecify_trellis(model, before, load_recipe(shared_registry, "spec.yml", fill={"β": 0.96}))
    assert changed_positions(model, same) == [(0, "two_nodes"), (1, "two_nodes")]
    assert all(same["periods"][h]["stages"]["disc"] is model["periods"][h]["stages"]["disc"] for h in range(2))


def test_the_bindings_retained_after_a_refused_calibration_are_told_from_the_values_requested(shared_registry):
    """A reading that binds the other kinds after the package refuses a
    calibration, as Bellman Workbench reads a trellis, keeps the occurrences
    of the trellis shown before with the values they held; those values are
    not the ones the syntactic trellis requests, and `already_bound` says so
    at every position, so that no reader reports them as the request's."""
    from bellman.factory.trellis import already_bound
    model = specify_trellis(load_recipe(shared_registry, "spec.yml"))
    requested = load_recipe(shared_registry, "spec.yml", disc_fill={"β": 0.5})
    with pytest.raises(FactoryError) as refused:
        specify_trellis(requested, model)
    assert refused.value.rule == "period-parameter-agreement"
    assert refused.value.__notes__ == ["Stage occurrence: periods[0].stages['disc']", "Binding kind: calibration"]
    retained = specify_trellis(requested, model, ["methods", "settings"])
    assert changed_positions(model, retained) == []
    for h, period in enumerate(retained["periods"]):
        for key, stage in period["stages"].items():
            assert stage.par["β"].value == 0.96
            assert not already_bound(stage, "calibration", requested["periods"][h]["stages"][key]["calibration"]) or key == "two_nodes"
    assert not already_bound(retained["periods"][0]["stages"]["disc"], "calibration", requested["periods"][0]["stages"]["disc"]["calibration"])


def test_a_verb_reads_the_second_argument_by_position_whatever_the_order_of_the_keys_of_a_period(path_of, tmp_path):
    record = load_stage(path_of("cons"))
    other = tmp_path / "other.bl"
    other.write_text(path_of("cons").read_text(encoding="utf-8").replace("ρ", "σ"), encoding="utf-8")
    first = {**record, "calibration": {"ρ": 6.0}}
    second = {**load_stage(other), "calibration": {"σ": 2.0}}
    elaborated = elaborate_trellis({"periods": [{"stages": {"first": first, "second": second}, "connectors": []}],
                                    "inter_connectors": []})
    # the same records listed in the other order name the same positions
    reordered = {"periods": [{"stages": {"second": second, "first": first}, "connectors": []}], "inter_connectors": []}
    calibrated = calibrate_trellis(elaborated, reordered)
    assert [(key, dict(stage.bindings.calibration)) for _, key, _, stage in positions(calibrated)] == [
        ("first", {"ρ": 6.0}), ("second", {"σ": 2.0})]


def test_a_replacing_selection_named_in_the_recipe_constructs_the_occurrence_anew(registry):
    """A change of selection is another addition named in the recipe
    (specification 0.7, D3): a syntactic trellis whose records name the
    replacing selection `methods.other.bl` in place of `methods.bl` is
    another construction at every position, which `specify_trellis` makes
    anew with the other handler, the graphs, the calibration, the settings
    and the position kept; `methodize_trellis` refuses it under
    `record-shape`, since a verb binds no other additions than those the
    occurrence was constructed with."""
    from bellman.refusal_examples import write_registry
    model = assemble_trellis(registry, "spec.yml")
    switched = load_recipe(
        write_registry(registry.parent / "switched", {
            **SMALL_REGISTRY,
            "spec.yml": SMALL_REGISTRY["spec.yml"].replace("stages/two_nodes/methods.bl", "stages/two_nodes/methods.other.bl"),
        }),
        "spec.yml",
    )
    with pytest.raises(FactoryError) as refused:
        methodize_trellis(model, switched)
    assert refused.value.rule == "record-shape" and "other additions" in refused.value.message
    rebuilt = specify_trellis(switched, model)
    assert changed_positions(model, rebuilt) == [(0, "two_nodes"), (1, "two_nodes"), (2, "two_nodes")]
    for (_, _, _, old), (_, _, _, new) in zip(positions(model), positions(rebuilt)):
        assert repr(new) == "ElaboratedStage('two_nodes', specified)"
        assert graphs_differ(old, new) == [] and dict(new.bindings.calibration) == dict(old.bindings.calibration)
        assert dict(new.bindings.settings) == dict(old.bindings.settings)
        assert (old.methods["cntn_to_dcsn"].handler, new.methods["cntn_to_dcsn"].handler) == ("test:backward", "test:other")
        assert dict(new.provenance["position"]) == dict(old.provenance["position"])
    assert changed_positions(rebuilt, specify_trellis(switched, rebuilt)) == []
    assert changed_positions(rebuilt, methodize_trellis(rebuilt, switched)) == []


def test_a_trellis_verb_binds_each_distinct_version_and_mapping_once_and_copies_the_result_to_their_other_positions(registry, monkeypatch):
    """A trellis verb applies the stage verb once for each distinct pair of the
    version at a position and the mapping the syntactic trellis holds there,
    and places at the other positions of the pair a copy that records its own
    position, parent and source lists (A62; the review of the stage object
    under repeated use, 25 September 2026, §4 item 4). Every position equals
    the stage's own verb applied to the version there alone, provenance
    included, is written alike, the order of each mapping's keys, a method's
    settings among them, and the type of each value counting, and holds its
    own object. The stage verbs are counted by wrapping the entries of the
    trellis module's table `_VERBS`, the calibration's and the settings';
    the methods of an occurrence are the additions read with its text, so
    `methodize_trellis` applies no stage verb and changes no position."""
    import bellman.factory.trellis as trellis_module
    from bellman.native.versions import stored
    calls = dict.fromkeys(trellis_module._VERBS, 0)
    assert set(calls) == {"calibration", "settings"}

    def written(stage):
        """The provenance, which holds the additions read, and the two bound mappings of a version as `repr`
        writes them, every mapping and every provenance record of the chain a dictionary in its own order."""
        def thawed(value):
            if hasattr(value, "items"):
                return {key: thawed(item) for key, item in value.items()}
            return [thawed(item) for item in value] if isinstance(value, (list, tuple)) else value
        return repr(thawed({"provenance": stage.provenance, "calibration": stage.bindings.calibration,
                            "settings": stage.bindings.settings}))

    def counted(kind, verb):
        # the settings' inner form takes the record's settings files as a keyword
        def bind(stage, mapping, **options):
            calls[kind] += 1
            return verb(stage, mapping, **options)
        return bind

    for kind, verb in dict(trellis_module._VERBS).items():
        monkeypatch.setitem(trellis_module._VERBS, kind, counted(kind, verb))
    steps = (("calibration", "calibrate", calibrate_trellis), ("settings", "configure", configure_trellis))
    # the recipe gives period 0 the terminal calibration and periods 1 and 2 one record, so each verb meets two
    # pairs, the versions of period 0 holding another calibration at the settings; with the terminal slot
    # filled with the main values, the three records differ in their source lists alone: one pair; with the
    # settings of period 2 written in another order, which its version prints, the settings meet two
    filled = load_recipe(registry, "spec.yml", terminal={"R": 1.02})
    reordered = deepcopy(filled)
    for h, settings in enumerate(({"n_k": 10, "extra": 1}, {"n_k": 10, "extra": 1}, {"extra": 1, "n_k": 10})):
        reordered["periods"][h]["stages"]["two_nodes"]["settings"] = settings
    for syntactic, pairs in ((load_recipe(registry, "spec.yml"), (2, 2)), (filled, (1, 1)), (reordered, (1, 2))):
        records = {(h, key): record for h, key, _, record in positions(syntactic)}
        trellis = elaborate_trellis(syntactic)
        for (kind, verb_name, trellis_verb), count in zip(steps, pairs):
            calls[kind] = 0
            bound = trellis_verb(trellis, syntactic)
            assert calls[kind] == count, (kind, count)
            for h, key, _, stage in positions(trellis):
                alone, held = getattr(stage, verb_name)(records[h, key][kind]), bound["periods"][h]["stages"][key]
                # the graphs, the bindings and the provenance, the last two also as written
                assert held == alone and written(held) == written(alone), (kind, h)
            trellis = bound
            if kind == "calibration":
                before = dict(calls)
                methodized = methodize_trellis(trellis, syntactic)
                assert changed_positions(trellis, methodized) == [] and calls == before
                trellis = methodized
        assert len({id(stored(stage, "_builders")) for _, _, _, stage in positions(trellis)}) == 3
    # the versions of the plain recipe meet one mapping at the three positions of the filled trellis, but the
    # version of period 0 records another calibration source, so it is bound on its own
    calls["calibration"] = 0
    calibrate_trellis(elaborate_trellis(load_recipe(registry, "spec.yml")), filled)
    assert calls["calibration"] == 2


def test_a_trellis_verb_leaves_the_kept_answers_of_a_stage_object_placed_at_two_positions_as_they_were(registry):
    """One stage object of the caller's, placed by hand at two positions whose
    records hold different calibrations, answers `denote()` with the object
    it answered before a trellis verb, or `specify_trellis` with it as
    `previous`, bound both positions."""
    syntactic = load_recipe(registry, "spec.yml")
    first, second = (syntactic["periods"][h]["stages"]["two_nodes"] for h in (0, 1))
    assert first["calibration"] != second["calibration"]
    small = {"periods": [{"stages": {"two_nodes": record}, "connectors": []} for record in (first, second)],
             "inter_connectors": [{}]}
    for bind in (lambda held: calibrate_trellis(held, small),
                 lambda held: specify_trellis(small, previous=held, kinds=("calibration",))):
        # the occurrence as the record constructs it, its addition read and nothing bound
        stage = elaborate_stage({**first, "calibration": {}, "settings": {}})
        denotation = stage.denote()
        held = {"periods": [{"stages": {"two_nodes": stage}, "connectors": []}] * 2, "inter_connectors": [{}]}
        bound = bind(held)
        assert [dict(p.stage.bindings.calibration) for p in positions(bound)] == [
            first["calibration"], second["calibration"]]
        assert stage.denote() is denotation


def test_a_stage_made_from_the_saved_ast_of_a_corpus_file_has_the_recorded_views(request, path_of):
    for name in STAGES:
        path = path_of(name)
        saved = json.loads(recording_path(path, ".ast.json").read_text(encoding="utf-8"))
        stage, fixture = make_stage(from_json(saved), None), request.getfixturevalue(name)
        assert (graphs_differ(stage, fixture),
                as_a_decoded_term_carries_it(stage.definitions)
                == as_a_decoded_term_carries_it(fixture.definitions)) == ([], True), name
        # the decoded term is parsed with no span table, so a record of a
        # top-level item keeps the term position where the stage built from the
        # text carries the file position of the same item (AMD-SG-017 §4)
        from bellman.native.records import DEFINITION_KINDS_AT_TOP_LEVEL
        top_level = [(record.address, fixture.definitions[identity].address)
                     for identity, record in stage.definitions.items()
                     if record.kind in DEFINITION_KINDS_AT_TOP_LEVEL]
        assert top_level and all(decoded.isdigit() and f"/{path.name}:" in written
                                 for decoded, written in top_level), name
    # a stage made from a term without spans carries no source positions: a
    # refusal names the rule and the term position only
    without_spans = make_stage(from_json(to_json(parse_with_spans(OPAQUE_FAMILY).term)), None)
    with pytest.raises(NotConstructed) as refused:
        graph_of(without_spans, "builders", "forward")
    assert (refused.value.rule, refused.value.address, refused.value.line, refused.value.file) == (
        "not-constructed", "3", None, None)


# methodize

def test_a_representation_method_accepts_declared_functions_and_function_aliases(cons_savings_iid):
    """A representation is typed at a declared function and at a function
    alias, each with a grid on the function's coordinate; the alias
    `𝑑𝑢 := D_{c}(𝑢)` has the coordinate of `𝑢`, and the inverse
    `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)` names no coordinate, so a grid written at it is
    refused and its grid is the default."""
    declared = "c_min : ℝ\nc_max : ℝ\nn_c : ℕ\n"
    entries = "".join(
        f"{name}.method : !Linear\n{name}.grid : !Cartesian(c=(c_min, c_max, n_c))\n"
        for name in ("𝑢", "𝑑𝑢")
    ) + "𝑑𝑢𝑖𝑛𝑣.method : !Linear\n"
    version = copy_native(cons_savings_iid).methodize(
        {"text": "@methods: cons_savings_iid\n" + declared + entries, "origin": "functions.methods.bl"}
    )
    assert {place: str(held) for place, held in version.methods.items()} == {
        "𝑢": "!Linear   !Cartesian(c=(c_min, c_max, n_c))",
        "𝑑𝑢": "!Linear   !Cartesian(c=(c_min, c_max, n_c))",
        "𝑑𝑢𝑖𝑛𝑣": "!Linear",
    }
    with pytest.raises(ConstructionError) as refused:
        copy_native(cons_savings_iid).methodize({
            "text": "@methods: cons_savings_iid\n" + declared
            + "𝑑𝑢𝑖𝑛𝑣.method : !Linear\n𝑑𝑢𝑖𝑛𝑣.grid : !Cartesian(c=(c_min, c_max, n_c))\n",
            "origin": "functions.methods.bl"})
    assert (refused.value.rule, refused.value.address) == ("grid-coordinate", "𝑑𝑢𝑖𝑛𝑣")


def test_methodize_refuses_an_entry_at_no_place_a_component_typed_twice_and_a_malformed_source(cons, cons_sources, tmp_path):
    text = cons_sources["methods"].read_text(encoding="utf-8")

    def changed(written, rewritten):
        assert text.count(written) == 1, written
        path = tmp_path / f"{len(list(tmp_path.iterdir()))}.bl"
        path.write_text(text.replace(written, rewritten), encoding="utf-8")
        return path
    # an entry at file level whose first segment is no block, definition or operator
    nowhere = changed("arvl_to_dcsn.method : !deterministic\n", "nowhere.method : !deterministic\n")
    with pytest.raises(ConstructionError, match="'nowhere' is no block, no definition and no operator") as refused:
        methodize(copy_native(cons), nowhere)
    assert "the blocks are arvl_to_dcsn, dcsn_to_cntn, cntn_to_dcsn, dcsn_to_arvl, policy" in str(refused.value)
    assert refused.value.file == str(nowhere)
    # an entry whose path names a block and then no place of it
    inside = changed("cntn_to_dcsn.evaluate.method : !Linear\n", "cntn_to_dcsn.nowhere.method : !Linear\n")
    with pytest.raises(ConstructionError, match="`cntn_to_dcsn.nowhere`, which is no place of the block 'cntn_to_dcsn'"):
        methodize(copy_native(cons), inside)
    # a component typed twice at one place by two entries of one path is
    # refused by the union (specification 0.7 §4 rule 4); typed by the whole
    # of an Evaluation beside one of its objects, two keys of the union and
    # one place, it is refused where the entries are resolved
    twice = changed("arvl_to_dcsn.method : !deterministic\n",
                    "arvl_to_dcsn.method : !deterministic\narvl_to_dcsn.method : !identity\n")
    with pytest.raises(ConstructionError) as refused:
        methodize(copy_native(cons), twice)
    assert refused.value.rule == "declared-twice"
    assert "the component `method` of block 'arvl_to_dcsn' is written twice" in str(refused.value)
    whole_and_object = changed("cntn_to_dcsn.evaluate.method : !Linear\n",
                               "cntn_to_dcsn.evaluate.method : !Linear\n"
                               "cntn_to_dcsn.evaluate[V].method : !pchip\n")
    with pytest.raises(ConstructionError) as refused:
        methodize(copy_native(cons), whole_and_object)
    assert refused.value.rule == "component-typed-twice"
    assert "the method component is typed twice" in str(refused.value)
    # a source that is no addition: a mapping of the retired form, a YAML
    # file and a file that does not exist
    with pytest.raises(TypeError, match="an addition is the path of a `.bl` file"):
        methodize(copy_native(cons), {"stage": "cons", "methods": [{"on": "policy", "method": "egm"}]})
    yaml = tmp_path / "methods.yml"
    yaml.write_text("methods: [{on: policy, method: egm}]\n", encoding="utf-8")
    with pytest.raises(ConstructionError, match="is no `.bl` file") as refused:
        methodize(copy_native(cons), yaml)
    assert refused.value.rule == "readable-form" and str(yaml) in str(refused.value)
    with pytest.raises(ConstructionError, match="cannot be read") as refused:
        methodize(copy_native(cons), tmp_path / "absent.bl")
    assert refused.value.rule == "readable-form"


# calibrate and configure

def test_calibrate_binds_a_value_to_each_declared_parameter_from_a_file_or_a_mapping(cons_methodized, cons_calibrated, cons_sources):
    assert repr(cons_calibrated) == "ElaboratedStage('cons', calibrated)"
    assert dict(cons_calibrated.bindings.calibration) == {"ρ": 6.0}       # the file values other names too
    values = yaml.safe_load(cons_sources["calibration"].read_text(encoding="utf-8"))
    from_mapping = calibrate(copy_native(cons_methodized), values)
    assert from_mapping.bindings.calibration == cons_calibrated.bindings.calibration
    # the version records the binding and the digest of its source, the same for the file and its mapping
    assert cons_calibrated.provenance["operation"] == from_mapping.provenance["operation"] == "calibrate"
    assert cons_calibrated.provenance["source"]["sha256"] == from_mapping.provenance["source"]["sha256"]


def test_calibrate_refuses_a_parameter_without_a_value_and_a_value_outside_its_declared_set(cons):
    # the refusal cites the parameter's record, whose address is the file
    # position of its declaration (AMD-SG-017 §4)
    with pytest.raises(ValueError, match=r"parameter 'ρ' \(address "
                                         r"'applications/portfolio-choice/declaration/stages/cons/cons\.bl:6'\): "
                                         r"the calibration source supplies no value for it.*write `ρ: <value>`"):
        calibrate(copy_native(cons), {})
    with pytest.raises(ValueError, match=r"the value 0.5 lies outside the declared set \[1, inf\).*write a value in \[1, inf\)"):
        calibrate(copy_native(cons), {"ρ": 0.5})


def test_a_derived_parameter_is_evaluated_after_those_it_reads_and_its_kernel_text_uses_numpy(
        derived_parameters):
    """A derived parameter is evaluated after the derived parameters it reads,
    whatever their order in the file, and a power whose exponent takes an
    integer value takes its value at a negative base, although the exponent's
    declared set holds nonintegers: the one condition the derived parameter
    owns is established at the value its definition takes; the definitions
    listing and the stage sheet print each derived parameter by its
    definition, and its card lists under `Definitions referenced` each
    parameter its definition reads, a name printed before a superscript
    exponent, `Γ²`, among them; and a compiled kernel writes a derived
    parameter through its definition, log and exp as NumPy's functions, with
    the declared parameters as its arguments (AMD-MT-003, build contract
    §5)."""
    stage = derived_parameters.stage(
        ("h := 1/(1 - Γ/R)", "h := 1/(1 - q)\nq := Γ/R\nz := (-q)^ρ"),
        ("R_n := R/Γ", "R_n := exp(log(R) - log(Γ))"),
    )
    assert list(stage.par)[4:] == ["h", "q", "z", "R_n"]
    stage.calibrate({"calibration": derived_parameters.calibration})
    q = 1.02 / 1.04
    assert stage.par["h"].value == pytest.approx(1 / (1 - q))
    assert stage.par["z"].value == pytest.approx(q**2)
    condition, = [item for item in stage.obligations()
                  if item.entries and str(item.entries[0]).endswith(":derived:z")]
    assert condition.status == "established"
    assert condition.evidence == (f"calibration z = {stage.par['z'].value!r}",)
    assert "DERIVED PARAMETERS 4" in str(stage.definitions.list())
    assert "derived parameters       4   h := 1/(1 - q), q := Γ/R, z := (-q)^ρ" in str(stage)
    squared = str(derived_parameters.stage(("h := 1/(1 - Γ/R)", "h := Γ^2"))
                  .definitions.denote("perfect_foresight:derived:h"))
    assert "  h  := Γ²\n" in squared
    assert squared.split("Definitions referenced\n")[1].splitlines()[:-1] == [
        "  Γ     perfect_foresight:parameter:Γ"]
    law = stage.builder["arvl", "dcsn"]["Pushforward"]
    kernel = law.kernel()
    assert kernel.parameters == ("R", "Γ")
    assert "    R_n = np.exp(np.log(R) - np.log(Γ))\n" in kernel.python
    assert law.compile_kernel()(numpy.array([1.0]), *kernel.parameter_values) == pytest.approx(
        [1.04 / 1.02 + 1]
    )


def test_configure_binds_the_settings_the_attached_methods_name_from_a_file_or_a_mapping(cons_methodized, cons_configured, cons_sources):
    assert repr(cons_configured) == "ElaboratedStage('cons', specified)"
    assert {"n_m", "m_min", "m_max"} <= set(cons_configured.bindings.settings)
    values = yaml.safe_load(cons_sources["settings"].read_text(encoding="utf-8"))
    assert configure(copy_native(cons_methodized), values).bindings.settings == cons_configured.bindings.settings


def test_configure_binds_a_version_without_methods_and_refuses_a_source_missing_a_named_setting(cons, cons_methodized):
    # a version without methods and without declared settings binds the
    # values given and nothing else (specification 0.7, S1)
    assert dict(configure(copy_native(cons), {"n_k": 8}).bindings.settings) == {"n_k": 8}
    with pytest.raises(ValueError, match=r"setting 'm_min': the settings source supplies no value for it.*write `m_min: <value>`"):
        configure(copy_native(cons_methodized), {"n_m": 10, "n_a": 10, "a_min": 0.1, "a_max": 1.0})




@pytest.mark.parametrize("name", STAGES)
def test_l1_a_verb_binds_once_from_a_complete_source_and_refuses_one_that_values_fewer_names(request, name):
    # the calibration binds a stage of its own (specification 0.6 decision 1 and R4)
    stage = request.getfixturevalue(name)
    bound = calibrate(copy_native(stage), CORPUS_CALIBRATIONS[name])
    assert dict(bound.bindings.calibration) == CORPUS_CALIBRATIONS[name]
    first = next(iter(CORPUS_CALIBRATIONS[name]))
    with pytest.raises(ValueError, match=f"parameter '{first}'"):
        calibrate(stage, {k: v for k, v in CORPUS_CALIBRATIONS[name].items() if k != first})


@pytest.mark.parametrize("name", STAGES)
def test_l2_the_last_calibration_stands_and_the_first_leaves_no_trace_in_bindings_or_graphs(request, name):
    # each binding binds a stage of its own, since a verb binds the stage it
    # is called on (specification 0.6 decision 1 and R4)
    stage = request.getfixturevalue(name)
    twice = calibrate(
        calibrate(copy_native(stage), CORPUS_CALIBRATIONS[name]), SECOND_CALIBRATIONS[name]
    )
    once = calibrate(copy_native(stage), SECOND_CALIBRATIONS[name])
    assert dict(twice.bindings.calibration) == dict(once.bindings.calibration) == SECOND_CALIBRATIONS[name]
    assert graphs_differ(twice, once) == [] and twice.definitions == once.definitions
    assert (twice.bindings.blocks, twice.bindings.settings) == (None, None)
    assert not holds_additions(twice)


@pytest.mark.parametrize("name", STAGES)
def test_l2_the_last_settings_stand_on_each_methodized_corpus_stage(request, name):
    from bellman.stage.sources import load_settings
    # each binding binds a stage of its own (specification 0.6 decision 1 and R4)
    methodized = methodize(copy_native(request.getfixturevalue(name)), CORPUS_METHODS[name])
    first = configure(copy_native(methodized), CORPUS_SETTINGS[name])
    changed = {**load_settings(CORPUS_SETTINGS[name]), "n_m": 33}
    twice, once = configure(copy_native(first), changed), configure(copy_native(methodized), changed)
    assert dict(twice.bindings.settings) == dict(once.bindings.settings) and twice.bindings.settings["n_m"] == 33
    assert graphs_differ(twice, once) == [] and twice.definitions == once.definitions
    assert str(twice.methods) == str(first.methods)
    assert list(twice.bindings.blocks or {}) == list(first.bindings.blocks or {})




# load_recipe

def test_load_recipe_merges_each_source_list_and_writes_the_merged_mapping_into_every_period(registry):
    syntactic = load_recipe(registry, "spec.yml")
    assert len(syntactic["periods"]) == 3 and syntactic["inter_connectors"] == [{"a": "k"}, {"a": "k"}]
    terminal, later = (syntactic["periods"][h]["stages"]["two_nodes"] for h in (0, 1))
    # the record's keys stand in the order of AMD-FAC-002 §2, and an unrestricted stage records no interval
    assert list(terminal) == ["stage", "calibration", "settings", "methods", "provenance"]
    assert "active" not in terminal["provenance"]
    # the range source '0-0' stands after the `all` sources, so its R stands at the terminal period alone
    assert (terminal["calibration"], later["calibration"]) == ({"β": 0.96, "R": 1.04}, {"β": 0.96, "R": 1.02})
    assert terminal["settings"] == {"n_k": 10}
    # the methods of a record are the additions its list names, each its text and its origin
    addition = registry / "stages/two_nodes/methods.bl"
    assert terminal["methods"] == [{"text": addition.read_text(encoding="utf-8"), "origin": str(addition)}]
    assert [entry["source"] for entry in terminal["provenance"]["source_lists"]["methods"]] == ["stages/two_nodes/methods.bl"]
    assert terminal["stage"]["origin"] == str(registry / "stages/two_nodes/two_nodes.bl")
    assert terminal["provenance"]["origin"] == terminal["stage"]["origin"]
    assert terminal["provenance"]["sha256"] == hashlib.sha256(terminal["stage"]["text"].encode("utf-8")).hexdigest()
    # each record is its own dictionary: a change to one period changes no other
    later["calibration"]["β"] = 0.5
    assert syntactic["periods"][2]["stages"]["two_nodes"]["calibration"] == {"β": 0.96, "R": 1.02}


def test_load_recipe_puts_each_fill_in_its_slot_and_the_later_source_stands_where_two_assign(registry):
    filled = load_recipe(registry, "spec.yml", fill={"calibration": {"β": 0.9}, "settings": {"n_k": 20}},
                         terminal={"calibration": {"R": 1.05}})
    terminal, later = (filled["periods"][h]["stages"]["two_nodes"] for h in (0, 1))
    assert (terminal["calibration"], later["calibration"]) == ({"β": 0.9, "R": 1.05}, {"β": 0.9, "R": 1.02})
    assert terminal["settings"] == {"n_k": 20}
    # an unbound slot contributes nothing
    assert load_recipe(registry, "spec.yml")["periods"][1]["stages"]["two_nodes"]["calibration"] == {"β": 0.96, "R": 1.02}


def test_a_parent_chain_of_a_calibration_file_merges_beneath_it(registry, tmp_path):
    from bellman.refusal_examples import write_registry
    recipe = ("trellis: trellis.yml\nstages:\n  two_nodes:\n"
              "    stage: stages/two_nodes/two_nodes.bl\n"
              "    calibration: {all: [calibration/child]}\n"
              "    settings: {all: [settings/main]}\n    methods: {all: [stages/two_nodes/methods.bl]}\n")
    directory = write_registry(tmp_path / "chained", {**SMALL_REGISTRY, "spec.yml": recipe})
    record = load_recipe(directory, "spec.yml")["periods"][0]["stages"]["two_nodes"]
    # the child's R stands over the parent's and the parent's β is kept, the parent key beside the top key unwrapped
    assert record["calibration"] == {"β": 0.96, "R": 1.03}


def test_load_recipe_reads_a_file_by_its_top_key_and_refuses_one_of_another_kind_in_a_list(registry, tmp_path):
    from bellman.refusal_examples import write_registry
    recipe = ("trellis: trellis.yml\nstages:\n  two_nodes:\n"
              "    stage: stages/two_nodes/two_nodes.bl\n"
              "    calibration: {all: [settings/main]}\n"
              "    settings: {all: [settings/main]}\n    methods: {all: [stages/two_nodes/methods.bl]}\n")
    directory = write_registry(tmp_path / "kinds", {**SMALL_REGISTRY, "spec.yml": recipe})
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert refused.value.rule == "recipe-source"
    assert "settings/main" in refused.value.message and "calibration" in refused.value.message
    assert str(refused.value).endswith("(rule recipe-source)")


def test_each_record_carries_the_ordered_sources_of_each_mapping_with_the_slots_marked(registry):
    syntactic = load_recipe(registry, "spec.yml", fill={"calibration": {"β": 0.9}})
    lists = syntactic["periods"][0]["stages"]["two_nodes"]["provenance"]["source_lists"]
    assert [entry.get("source", entry.get("slot")) for entry in lists["calibration"]] == [
        "calibration/main", "fill", "calibration/terminal", "terminal"]
    assert [entry.get("range") for entry in lists["calibration"]] == [None, None, "0-0", "0-0"]
    assert [entry["bound"] for entry in lists["calibration"] if "slot" in entry] == [True, False]
    assert lists["calibration"][0]["sha256"] == hashlib.sha256((registry / "calibration/main.yml").read_bytes()).hexdigest()
    later = syntactic["periods"][1]["stages"]["two_nodes"]["provenance"]["source_lists"]["calibration"]
    assert [entry.get("source", entry.get("slot")) for entry in later] == ["calibration/main", "fill"]
    assert syntactic["provenance"]["recipe"]["path"] == str(registry / "spec.yml")
    assert syntactic["provenance"]["trellis"]["path"] == str(registry / "trellis.yml")


def test_the_registry_block_is_carried_as_data_and_is_bound_to_no_stage(registry, tmp_path):
    from bellman.refusal_examples import write_registry
    recipe = SMALL_REGISTRY["spec.yml"] + "registry:\n  calibration: [calibration/ages]\n"
    directory = write_registry(tmp_path / "registry", {**SMALL_REGISTRY, "spec.yml": recipe,
                                                        "calibration/ages.yml": "calibration:\n  first_age: 20\n  last_age: 70\n"})
    syntactic = load_recipe(directory, "spec.yml")
    assert syntactic["registry"] == {"calibration": {"first_age": 20, "last_age": 70}}
    assert syntactic["provenance"]["registry"]["calibration"][0]["source"] == "calibration/ages"
    assert "first_age" not in syntactic["periods"][0]["stages"]["two_nodes"]["calibration"]


def test_a_flat_fill_is_read_against_the_declarations_of_the_receiving_stages(registry):
    flat = load_recipe(registry, "spec.yml", fill={"β": 0.9})
    assert flat["periods"][1]["stages"]["two_nodes"]["calibration"] == {"β": 0.9, "R": 1.02}
    assert flat["periods"][1]["stages"]["two_nodes"]["settings"] == {"n_k": 10}
    flat = load_recipe(registry, "spec.yml", fill={"n_k": 4})
    assert flat["periods"][1]["stages"]["two_nodes"]["settings"] == {"n_k": 4}
    assert flat["periods"][1]["stages"]["two_nodes"]["calibration"] == {"β": 0.96, "R": 1.02}


def test_a_flat_fill_of_a_setting_is_read_against_the_selection_of_each_period(tmp_path):
    """A stage whose methods block names a selection in one range and its
    replacing selection in another declares, for a flat fill, the settings
    of each selection read as it applies at its own periods, and not the two
    unioned with each other, which no occurrence takes: the fixture recipe
    of cons-port with the portfolio stage's `methods.bl` at the periods 0 to
    2 and `methods.reference.bl` at 3 to 5 loads with `fill={"n_k": 30}` as
    it loads without a fill, the value standing in every portfolio record
    and each period's record naming its own selection."""
    import shutil
    from conftest import CONS_PORT
    registry = tmp_path / "declaration"
    shutil.copytree(CONS_PORT, registry)
    recipe = (registry / "spec.port-cons.yml").read_text(encoding="utf-8")
    ranged = recipe.replace(
        "settings: {all: [settings/port_wide]}, methods: {all: [stages/port/methods.bl]}",
        "settings: {all: [settings/port_wide, $fill]}, "
        "methods: {all: [], '0-2': [stages/port/methods.bl], '3-5': [stages/port/methods.reference.bl]}",
    )
    assert ranged != recipe
    (registry / "spec.ranged.yml").write_text(ranged, encoding="utf-8")
    filled = load_recipe(registry, "spec.ranged.yml", fill={"n_k": 30})
    ports = [period["stages"]["port"] for period in filled["periods"]]
    assert [record["settings"]["n_k"] for record in ports] == [30] * 6
    named = [[entry["source"] for entry in record["provenance"]["source_lists"]["methods"]] for record in ports]
    assert named == [["stages/port/methods.bl"]] * 3 + [["stages/port/methods.reference.bl"]] * 3


def test_a_fill_in_a_range_list_binds_at_those_periods_only(registry):
    filled = load_recipe(registry, "spec.yml", terminal={"R": 2.0})
    assert [p["stages"]["two_nodes"]["calibration"]["R"] for p in filled["periods"]] == [2.0, 1.02, 1.02]
    with pytest.raises(FactoryError) as refused:
        load_recipe(registry, "spec.yml", terminal={"n_k": 4})
    # the slot stands in a calibration list alone, so a setting names nothing there; a flat key of
    # no kind is answered with both kinds' declarations
    assert refused.value.rule == "fill-names-nothing" and "n_k" in refused.value.message
    assert "as a parameter (two_nodes declares β, R)" in refused.value.message
    assert "as a setting (no stage receives it in a settings list)" in refused.value.message


def test_a_stage_restricted_to_an_interval_is_absent_elsewhere_and_its_records_say_the_interval(registry, tmp_path):
    from bellman.refusal_examples import write_registry
    recipe = SMALL_REGISTRY["spec.yml"].replace("  two_nodes:\n", "  two_nodes:\n    periods: [0, 1]\n")
    directory = write_registry(tmp_path / "interval", {**SMALL_REGISTRY, "spec.yml": recipe})
    syntactic = load_recipe(directory, "spec.yml")
    assert [list(period["stages"]) for period in syntactic["periods"]] == [["two_nodes"], ["two_nodes"], []]
    assert syntactic["periods"][0]["stages"]["two_nodes"]["provenance"]["active"] == [0, 1]


def test_a_key_listed_twice_in_a_template_and_a_methods_list_naming_no_addition_are_refused_with_their_names(registry, tmp_path):
    """A methods list names `.bl` additions and nothing else: a name of the
    retired YAML form, `methods/two_nodes`, is refused under `recipe-source`
    at the list's address, and a slot in a methods list under `recipe-shape`,
    since a change of selection is another addition named in the list
    (specification 0.7, D3)."""
    from bellman.refusal_examples import write_registry
    directory = write_registry(tmp_path / "twice", {**SMALL_REGISTRY,
                                                     "period.yml": "name: one_stage\nstages: [two_nodes, two_nodes]\nconnectors: []\n"})
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.address, refused.value.written) == ("recipe-shape", "periods[0].stages", "two_nodes")
    for name, rule, address in (("methods/two_nodes", "recipe-source", "stages.two_nodes.methods.all"),
                                ("$method_switch", "recipe-shape", "stages.two_nodes.methods.all")):
        directory = write_registry(tmp_path / name.strip("$").replace("/", "-"), {
            **SMALL_REGISTRY,
            "methods/two_nodes.yml": "stage: two_nodes\nmethods:\n  - on: cntn_to_dcsn\n",
            "spec.yml": SMALL_REGISTRY["spec.yml"].replace("stages/two_nodes/methods.bl", name)})
        with pytest.raises(FactoryError) as refused:
            load_recipe(directory, "spec.yml")
        assert (refused.value.rule, refused.value.address, refused.value.written) == (rule, address, name)
        assert "addition" in refused.value.message and refused.value.write


def test_a_fill_of_a_registry_name_stands_in_the_registry_mapping_and_in_no_record(registry, tmp_path):
    from bellman.refusal_examples import write_registry
    recipe = SMALL_REGISTRY["spec.yml"] + "registry:\n  calibration: [calibration/ages]\n"
    directory = write_registry(tmp_path / "registry", {**SMALL_REGISTRY, "spec.yml": recipe,
                                                        "calibration/ages.yml": "calibration:\n  first_age: 20\n"})
    filled = load_recipe(directory, "spec.yml", fill={"first_age": 25, "β": 0.9})
    assert filled["registry"] == {"calibration": {"first_age": 25}}
    assert filled["periods"][0]["stages"]["two_nodes"]["calibration"] == {"β": 0.9, "R": 1.04}
    assert filled["provenance"]["registry"]["calibration"][-1] == {"slot": "fill", "bound": True, "names": ["first_age"]}
    # the record's entry for the slot names what the stage declares of the fill (A57)
    assert filled["periods"][0]["stages"]["two_nodes"]["provenance"]["source_lists"]["calibration"][1] == {
        "slot": "fill", "bound": True, "names": ["β"]}
    keyed = load_recipe(directory, "spec.yml", fill={"calibration": {"first_age": 30}})
    assert keyed["registry"]["calibration"]["first_age"] == 30
    assert "first_age" not in keyed["periods"][0]["stages"]["two_nodes"]["calibration"]


def test_a_slot_entry_names_the_fill_names_of_its_kind_that_the_stage_declares():
    """A57: after a fill keyed by kind, the entry of the slot in a stage's
    calibration list names the fill's parameters that stage declares and the
    entry in its settings list the fill's settings its settings files and
    methods name; the bequest, which declares neither β nor n_a, names
    nothing. Each `names` is a list."""
    filled = load_recipe(DURABLES, TWO_STAGES, fill={"calibration": {"β": 0.93}, "settings": {"n_a": 500}})
    stages = filled["periods"][0]["stages"]
    assert stages["bequest"]["provenance"]["source_lists"]["calibration"][1] == {"slot": "fill", "bound": True, "names": []}
    adjuster = stages["adjuster_cons"]["provenance"]["source_lists"]
    assert adjuster["calibration"][1] == {"slot": "fill", "bound": True, "names": ["β"]}
    assert adjuster["settings"][1] == {"slot": "fill", "bound": True, "names": ["n_a"]}
    assert all(type(entry["names"]) is list for entries in adjuster.values() for entry in entries if "slot" in entry)


@pytest.mark.parametrize("fills, rule, word", [
    ({"fill": "β: 0.9"}, "slot-value-not-a-mapping", "'fill'"),
    ({"fill": {"beta": 0.9}}, "fill-names-nothing", "'beta'"),
    ({"fill": {"β": 0.9, "n_k": 4}}, "fill-mixes-kinds", "n_k"),
    ({"filling": {"β": 0.9}}, "recipe-slot-unknown", "'filling'"),
    # the slot $fill stands in no methods list, so a methods part given to it is bound to no stage
    ({"fill": {"methods": [{"on": "cntn_to_dcsn", "handler": "test:other"}]}}, "fill-names-nothing", "methods list"),
])
def test_a_fill_is_refused_where_it_is_no_mapping_names_nothing_mixes_kinds_or_names_no_slot(registry, fills, rule, word):
    with pytest.raises(FactoryError) as refused:
        load_recipe(registry, "spec.yml", **fills)
    assert refused.value.rule == rule and word in refused.value.message and refused.value.write


def test_a_recipe_and_a_template_that_disagree_on_a_stage_are_refused(registry, tmp_path):
    from bellman.refusal_examples import write_registry
    named_by_no_period = (SMALL_REGISTRY["spec.yml"]
                          + "  other:\n    stage: stages/other.bl\n    calibration: {all: [calibration/main]}\n")
    directory = write_registry(tmp_path / "a", {**SMALL_REGISTRY, "spec.yml": named_by_no_period,
                                                 "stages/other.bl": TWO_NODES.replace("two_nodes", "other")})
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.address) == ("recipe-template-agreement", "other")
    assert "trellis.yml" in refused.value.message and "spec.yml" in str(refused.value)
    # the period comes from the template file period.yml, which the refusal names beside the trellis file and the recipe
    held_by_a_period = "name: one_stage\nstages: [two_nodes, other]\nconnectors: []\n"
    directory = write_registry(tmp_path / "b", {**SMALL_REGISTRY, "period.yml": held_by_a_period,
                                                 "stages/other.bl": TWO_NODES.replace("two_nodes", "other")})
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert (refused.value.rule, refused.value.address) == ("recipe-template-agreement", "periods[0].other")
    assert f"periods[0] of {directory / 'period.yml'}, named by {directory / 'trellis.yml'}" in refused.value.message
    assert str(directory / "spec.yml") in refused.value.message


def test_a_stage_active_at_no_period_is_refused(registry, tmp_path):
    from bellman.refusal_examples import write_registry
    recipe = SMALL_REGISTRY["spec.yml"].replace("  two_nodes:\n", "  two_nodes:\n    periods: [5, 9]\n")
    directory = write_registry(tmp_path / "c", {**SMALL_REGISTRY, "spec.yml": recipe})
    with pytest.raises(FactoryError) as refused:
        load_recipe(directory, "spec.yml")
    assert refused.value.rule == "recipe-template-agreement" and "5-9" in refused.value.message and "3 periods" in refused.value.message


# the joins of a period

def test_the_joins_of_a_period_follow_equal_names_and_connectors_and_the_order_follows_the_joins(cons, port, elaborate_text,
                                                                                                  text_of):
    from bellman.factory.joins import (backward_order, computable_together, forward_order,
        period_joins)
    # port continues to m_next and cons arrives at m: no join by equal name, and both continuation fields leave the period
    assert period_joins({"stages": {"cons": cons, "port": port}, "connectors": []}) == {
        "joins": [], "outputs": [("cons", "a"), ("port", "m_next")]}
    # the connector {m_next: m} joins the two, whatever the list order
    period = {"stages": {"cons": cons, "port": port}, "connectors": [{"m_next": "m"}]}
    assert period_joins(period)["joins"] == [{"from": ("port", "m_next"), "to": ("cons", "m")}]
    assert period_joins(period)["outputs"] == [("cons", "a")]
    assert forward_order(period) == ["port", "cons"] and backward_order(period) == ["cons", "port"]
    listed_the_other_way = {"stages": {"port": port, "cons": cons}, "connectors": [{"m_next": "m"}]}
    assert period_joins(listed_the_other_way) == period_joins(period)
    assert forward_order(listed_the_other_way) == ["port", "cons"]
    assert computable_together(period) == [["port"], ["cons"]]
    # a connector written as {from, to, fields} that restates the inferred equal-name pair is admitted
    # since AMD-COMP-001 §3: the authored pair claims the two uses, the inference is excluded, and the one
    # join is the authored one; the equal-name pair is that of a copy of port.bl continuing to m
    port_to_m = elaborate_text(text_of("port").replace("m_next", "m"), "port.bl")
    written = {"stages": {"cons": cons, "port": port_to_m},
               "connectors": [{"from": "port", "to": "cons", "fields": {"m": "m"}}]}
    assert period_joins(written, "periods[0]")["joins"] == [{"from": ("port", "m"), "to": ("cons", "m")}]
    assert period_joins({**written, "connectors": []}, "periods[0]") == period_joins(written, "periods[0]")


def test_a_connector_naming_a_field_no_stage_declares_and_a_cycle_among_the_joins_are_refused(cons, port):
    from bellman.factory.joins import forward_order, period_joins
    from bellman.trellis import connection_report, elaborate_trellis
    # a connector naming a field no stage declares makes no join and refuses nothing (AMD-COMP-001 §3):
    # the period's joins are answered, and the trellis's connection report names the unresolved endpoint
    named = {"stages": {"cons": cons}, "connectors": [{"a": "q"}]}
    assert period_joins(named, "periods[0]") == {"joins": [], "outputs": [("cons", "a")]}
    (diagnostic,) = connection_report(elaborate_trellis({"periods": [named], "inter_connectors": []})).diagnostics
    assert (diagnostic.rule, diagnostic.address) == ("endpoint-unresolved", "periods[0].connectors[0]")
    assert "'q'" in diagnostic.message and "m" in diagnostic.message
    # two connectors close a cycle: cons's a joins port's k, and port's m_next joins cons's m
    with pytest.raises(FactoryError) as refused:
        forward_order({"stages": {"cons": cons, "port": port}, "connectors": [{"a": "k"}, {"m_next": "m"}]}, "periods[0]")
    assert refused.value.rule == "period-join-cycle" and "remove or redirect an authored connector" in refused.value.write
    assert all(word in refused.value.message for word in ("port continues to 'm_next'", "cons arrives at 'm'", "'a'", "'k'"))
    # a syntactic period holds records, which have no fields
    with pytest.raises(FactoryError, match="elaborate_trellis") as refused:
        period_joins({"stages": {"cons": {"stage": {"text": "", "origin": "cons.bl"}}}, "connectors": []}, "periods[0]")
    assert (refused.value.rule, refused.value.address) == ("record-shape", "periods[0].stages['cons']")
    # a self-pair remains a diagnostic, while an ordering request refuses it
    self_pair = {"stages": {"cons": cons}, "connectors": [{"a": "m"}]}
    assert period_joins(self_pair, "periods[0]")["joins"] == []
    with pytest.raises(FactoryError) as refused:
        forward_order(self_pair, "periods[0]")
    assert refused.value.rule == "period-join-cycle" and "cons" in refused.value.message and "'a'" in refused.value.message
    # two connectors contending for one continuation field remain inspectable;
    # an ordering request cannot use the disputed dependency
    duplicate = {"stages": {"cons": cons, "port": port}, "connectors": [{"a": "k"}, {"a": "k"}]}
    assert period_joins(duplicate, "periods[0]")["joins"] == [
        {"from": ("cons", "a"), "to": ("port", "k")}
    ]
    with pytest.raises(FactoryError) as refused:
        forward_order(duplicate, "periods[0]")
    assert "periods[0].connectors[0] and periods[0].connectors[1] both map the continuation field 'a' of cons" in refused.value.message
    assert (refused.value.rule, refused.value.address) == ("connector-names-no-field", "periods[0].connectors[1]")
    # the keyed form with a key beside from, to and fields
    with pytest.raises(FactoryError) as refused:
        period_joins({"stages": {"cons": cons, "port": port},
                      "connectors": [{"from": "cons", "to": "port", "fields": {"a": "k"}, "label": "x"}]}, "periods[0]")
    assert "'label'" in refused.value.message and refused.value.rule == "connector-names-no-field"


def test_an_inter_period_mapping_joins_the_fields_that_leave_the_period(cons, port):
    from bellman.stage import elaborate_stage, load_stage
    from bellman.trellis import accrete, diagram_trellis
    from bellman.factory.joins import inter_period_joins
    disc = elaborate_stage(load_stage(str(
        ROOT / "applications/portfolio-choice/declaration/stages/disc/disc.bl")))
    from bellman.trellis import connection_report
    period = {"stages": {"port": port, "cons": cons, "disc": disc}, "connectors": [{"m_next": "m"}]}
    # cons and disc both continue to a, so the bare name resolves to no use between the periods and makes
    # no join (AMD-COMP-001 §3); the stage key before the field names disc's a, which leaves the period
    assert inter_period_joins({"a": "k"}, period, period) == []
    assert inter_period_joins({"disc.a": "k"}, period, period) == [{"from": ("disc", "a"), "to": ("port", "k")}]
    trellis = accrete(accrete({"periods": [], "inter_connectors": []}, period), period, {"disc.a": "k"})
    assert diagram_trellis(trellis).source.count("inter_connectors[0]") == 1
    # a connector of periods[1] naming no field refuses nothing: the trellis is drawn as the draft it is, and
    # its connection report names the unresolved endpoint at that period's address
    faulty = {**trellis, "periods": [trellis["periods"][0], {**trellis["periods"][1], "connectors": [{"q": "m"}]}]}
    assert repr(diagram_trellis(faulty)) == repr(diagram_trellis(trellis))
    diagnostics = connection_report(faulty).diagnostics
    assert any((item.rule, item.address) == ("endpoint-unresolved", "periods[1].connectors[0]")
               for item in diagnostics)
    assert [(item.rule, item.address) for item in diagnostics] == [
        ("endpoint-unresolved", "periods[1].connectors[0]"),
        ("route-incomplete", "periods[0].connectors[0]")]
    # the inter-period projection leaves a disputed source on the draft;
    # strict selection still refuses the second claim
    assert inter_period_joins({"m_next": "m"}, period, period, "inter_connectors[0]") == []
    from bellman.factory.joins import checked_selection
    with pytest.raises(FactoryError) as refused:
        checked_selection([period, period], [{"m_next": "m"}], 0)
    assert (refused.value.rule, refused.value.address) == ("connector-names-no-field", "inter_connectors[0]")
    assert "periods[1].connectors[0] and inter_connectors[0] both map the continuation field 'm_next' of port" in refused.value.message


def test_diagram_period_draws_the_stages_in_forward_order_joined_by_their_fields(cons, port):
    from bellman.period import diagram_period
    drawing = diagram_period({"periods": [{"stages": {"cons": cons, "port": port}, "connectors": [{"m_next": "m"}]}],
                           "inter_connectors": []}, 0)
    assert repr(drawing) == "Drawing of 2 boxes"
    assert drawing.labels == ("port: port", "cons: cons")
    assert '"port" -> "cons" [label="m_next → m"]' in drawing.source and 'label="a"' in drawing.source
    # a box prints its key once where the key is the stage's name; the wire to the plain label of
    # a continuation field no stage takes carries no label of its own
    assert '"cons" [label="cons"];' in drawing.source and '"cons" -> "out0";' in drawing.source
    renamed = diagram_period({"periods": [{"stages": {"consumption": cons}, "connectors": []}], "inter_connectors": []}, 0)
    assert '"consumption" [label="consumption\\n(cons)"];' in renamed.source


def test_diagram_trellis_draws_the_periods_with_their_inter_period_connectors_under_the_index_convention(registry):
    from bellman.trellis import diagram_trellis
    elaborated = elaborate_trellis(load_recipe(registry, "spec.yml"))
    drawing = diagram_trellis({**elaborated, "registry": {"calibration": {"last_age": 65}}})
    assert repr(drawing) == "Drawing of 3 boxes"
    # the boxes are listed as the trellis lists its periods, the terminal period first
    assert drawing.labels == ("periods[0] two_nodes: two_nodes", "periods[1] two_nodes: two_nodes",
                              "periods[2] two_nodes: two_nodes")
    source = drawing.source
    # each period a cluster labeled by its index and its age, periods[h] being age last_age - h (D15)
    for h, age in ((0, 65), (1, 64), (2, 63)):
        assert f"periods[{h}]: h = {h}, age {age}" in source
    assert (source.index('"periods[2] two_nodes"') < source.index('"periods[1] two_nodes"')
            < source.index('"periods[0] two_nodes"'))
    # each mapping inter_connectors[h] a wire from the continuation field a of periods[h + 1] to the
    # arrival field k of periods[h], labeled with its index and its field pair
    assert '"periods[1] two_nodes" -> "periods[0] two_nodes" [label="inter_connectors[0]\\na → k"]' in source
    assert '"periods[2] two_nodes" -> "periods[1] two_nodes" [label="inter_connectors[1]\\na → k"]' in source
    assert "economic time runs left to right" in source and "the backward computation right to left" in source
    assert 'style="invis"' not in source                          # the wires alone order the three periods


def test_diagram_trellis_draws_the_periods_listed_and_the_wires_between_them_alone(registry):
    from bellman.trellis import diagram_trellis
    elaborated = elaborate_trellis(load_recipe(registry, "spec.yml"))
    drawing = diagram_trellis(elaborated, periods=[0, 1])
    assert repr(drawing) == "Drawing of 2 boxes" and "periods[2]" not in drawing.source
    assert "inter_connectors[0]" in drawing.source and "inter_connectors[1]" not in drawing.source
    assert ", age " not in drawing.source                                # the smallest registry names no last_age
    # two periods that are no neighbors are drawn with no wire between them, an invisible edge
    # keeping the earlier period at the left
    apart = diagram_trellis(elaborated, periods=[0, 2]).source
    assert "inter_connectors" not in apart and '-> "periods[0] two_nodes" [style="invis"]' in apart
    with pytest.raises(FactoryError) as refused:
        diagram_trellis(elaborated, periods=[3])
    assert (refused.value.rule, refused.value.address) == ("trellis-file-shape", "periods")


# the queries and the binding verbs as methods (AMD-SG-007 §3; §10 item 2)

def sample_calls(stage):
    """One call of each stage-first query on a stage: the arguments after the
    stage, read from the stage itself."""
    calls = {"fields": (), "denote": (), "obligations": (), "diagnostics": (),
             "places": (), "encoding": ()}
    assert set(calls) == set(QUERY_METHODS)
    return calls




def test_completing_stage_dot_lists_the_six_public_attributes_the_queries_and_the_binding_verbs_but_not_the_stored_record(
        cons):
    # `builder` and the three perch handles `arvl`, `dcsn` and `cntn` are properties, as `par`
    # and `settings` are, and not among the seven attributes; the seventh, the stored record
    # `_builders`, is private and is not listed
    assert [entry for entry in dir(cons) if not entry.startswith("_")] == sorted(
        {"name", "metadata", "definitions", "initial", "bindings", "provenance", "builder",
         "arvl", "dcsn", "cntn"}
        | set(QUERY_METHODS) | set(BINDING_VERBS) | set(STAGE_VERBS))
    assert "_builders" not in dir(cons) and not hasattr(cons, "build")
    # a query that takes a box as its argument is bound as no method (AMD-SG-010 §4),
    # and the ten names AMD-SG-020 §3.1 removed and the three verbs its §3.2
    # merged resolve on no stage, no graph, no bubble and no box
    assert not any(hasattr(cons, name) for name in ("kernel", "compile_kernel", "builders_graph",
                                                    "initial_diagram", "to_drawing", "graph_inputs_and_outputs",
                                                    "builder_signature", "box_signature"))
    removed = ("transition_map", "aggregator", "policy_relation", "selection", "expectations",
               "methods_of", "definitions_of", "symbols", "kind", "branches",
               "origins", "affine", "directions")
    for piece in (cons, cons.builder.bwd, cons.builder.bwd["cntn_to_dcsn"],
                  cons.builder.bwd["cntn_to_dcsn", "Pullback"], cons.initial.backward):
        assert not any(hasattr(piece, name) for name in removed), piece
    assert cons.view() == str(cons)
    # Python's own protocol names stay listed beside them (AMD-SG-007 §3)
    assert {"__eq__", "__hash__", "__repr__", "__str__"} <= set(dir(cons))


def test_a_backward_value_builder_reads_a_decision_state_as_a_coordinate_of_its_kernel(elaborate_text, text_of):
    # the value line reads the decision state m_d, which the header does not
    # list: a state of the perch at which the output stands is a coordinate of
    # the output and of the kernel, not a wire (AAS, 12 October 2026)
    source = text_of("cons_obs").replace("V        = 𝑢(c) + V[>]", "V        = m_d*𝑢(c) + V[>]")
    stage = elaborate_text(source, "cons_obs.bl").calibrate({"ρ": 2})
    stage.builder.bwd
    G = compile_kernel(stage, "cntn_to_dcsn:Aggregation")
    values = kernel(stage, "cntn_to_dcsn:Aggregation").parameter_values
    assert float(G(4, 2, 1, *values)) == 2.0


def test_compile_evaluates_g_and_G_with_the_arguments_of_their_printed_kernels_then_the_parameters_they_read(cons):
    calibrated = copy_native(cons).calibrate({"ρ": 2.0})
    substitution, aggregation = "cntn_to_dcsn:Pullback", "cntn_to_dcsn:Aggregation"
    assert kernel(calibrated, substitution) == "𝑔 of dcsn_to_cntn: 𝑔(m_d, c) = m_d - c"
    assert kernel(calibrated, aggregation) == (
        "𝐺 of cntn_to_dcsn: 𝐺(V≻, m_d, c) = 𝑢(c) + V≻\n"
        "output V; unused m_d")
    g, G = compile_kernel(calibrated, substitution), compile_kernel(calibrated, aggregation)
    # the kernel's arguments in printed order, then each parameter the
    # kernel reads; the law of motion reads none
    assert (str(inspect.signature(g)), str(inspect.signature(G))) == ("(m_d, c)", "(V_cntn, m_d, c, ρ)")
    assert (kernel(calibrated, substitution).parameters, kernel(calibrated, aggregation).parameters) == ((), ("ρ",))
    assert kernel(calibrated, aggregation).parameter_values == (2.0,)
    assert float(g(2, 0.5)) == 1.5                                  # savings when resources are 2 and consumption 0.5
    assert float(G(4, 2, 0.5, 2.0)) == 2.0
    # Python integers, as the parameter's value and as arguments, are read
    # by Python's own arithmetic
    assert float(G(4, 2, 1, 2)) == 3.0
    # the text's header names the stage, the box, the stage file, the
    # printed kernel, the parameters' declared sets and the Python names,
    # and holds no value
    text = kernel(calibrated, aggregation).python
    for words in ("cons, cntn_to_dcsn:Aggregation", "cons.bl sha256 " + cons.provenance["sha256"],
                  "output V", "ρ ∈ [1, inf)", "V_cntn is V≻", "u is 𝑢"):
        assert words in text, words
    assert text == kernel(cons, aggregation).python
    assert inspect.getsource(G) == text[text.index("\ndef ") + 1:]
    # a box and its name reach one kernel
    box = next(box for box in operators_of(calibrated) if box.name == aggregation)
    assert float(compile_kernel(calibrated, box)(4, 2, 0.5, 2.0)) == 2.0


def test_a_changed_equation_gives_a_new_text_and_a_changed_calibration_new_values_for_the_same_function(cons, elaborate_text, text_of):
    calibrated = copy_native(cons).calibrate({"ρ": 2.0})
    g, G = compile_kernel(calibrated, "cntn_to_dcsn:Pullback"), compile_kernel(calibrated, "cntn_to_dcsn:Aggregation")
    # the law of motion halved, and the grid line written as the halved law solved for m_d
    halved = elaborate_text(text_of("cons").replace("    a = m_d - c\n", "    a = (m_d - c)/2\n")
                            .replace("    m_d[>] = a + c[>]                :: [id=endoggrid]",
                                     "    m_d[>] = 2*a + c[>]              :: [id=endoggrid]"), "cons.bl")
    halved = halved.calibrate({"ρ": 2.0})
    assert kernel(halved, "cntn_to_dcsn:Pullback") == "𝑔 of dcsn_to_cntn: 𝑔(m_d, c) = (m_d - c)/2"
    assert kernel(halved, "cntn_to_dcsn:Pullback").python != kernel(calibrated, "cntn_to_dcsn:Pullback").python
    assert (float(compile_kernel(halved, "cntn_to_dcsn:Pullback")(2, 0.5)), float(g(2, 0.5))) == (0.75, 1.5)
    # a new calibration gives the same text and new values, passed to the
    # function already made
    recalibrated = copy_native(cons).calibrate({"ρ": 3.0})
    again = kernel(recalibrated, "cntn_to_dcsn:Aggregation")
    assert again.python == kernel(calibrated, "cntn_to_dcsn:Aggregation").python
    assert again.parameter_values == (3.0,)
    assert float(G(4, 2, 1, *again.parameter_values)) == 3.5
    assert float(G(4, 2, 1, 2.0)) == 3.0
    # a symbolic version gives the same text, no values, and compiles too
    symbolic = kernel(cons, "cntn_to_dcsn:Aggregation")
    assert (symbolic.python, symbolic.parameters, symbolic.parameter_values) == (again.python, ("ρ",), None)
    assert float(compile_kernel(cons, "cntn_to_dcsn:Aggregation")(4, 2, 1, 3.0)) == 3.5


def test_compile_writes_a_closed_form_function_reached_through_an_alias_and_refuses_a_derivative_one(elaborate_text, text_of):
    written = "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)"
    assert text_of("cons").count(written) == 1

    def calibrated(definitions):
        return elaborate_text(text_of("cons").replace(written, definitions), "cons.bl").calibrate({"ρ": 2.0})
    aliased = calibrated("utility(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)\n𝑢 := utility")
    G = compile_kernel(aliased, "cntn_to_dcsn:Aggregation")
    assert float(G(4, 2, 0.5, 2.0)) == 2.0
    # the inner function takes the name of the definition the alias reaches
    assert "utility is 𝑢" in kernel(aliased, "cntn_to_dcsn:Aggregation").python
    with pytest.raises(ConstructionError) as refused:
        compile_kernel(calibrated("utility(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)\n𝑢 := D_{c}(utility)"), "cntn_to_dcsn:Aggregation")
    assert refused.value.rule == "kernel-form" and "𝑢 := D_{c}(utility)" in refused.value.message
    # the kernel of a form the text cannot write answers no text
    derivative = calibrated("utility(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)\n𝑢 := D_{c}(utility)")
    assert kernel(derivative, "cntn_to_dcsn:Aggregation").python is None


def test_a_compiled_kernel_broadcasts_arrays_and_leaves_shapes_that_do_not_combine_to_numpy(cons):
    calibrated = copy_native(cons).calibrate({"ρ": 2.0})
    G = compile_kernel(calibrated, "cntn_to_dcsn:Aggregation")
    value = G(numpy.array([4.0, 5.0]), 2.0, 0.5, 2.0)
    assert (numpy.shape(value), value.tolist()) == ((2,), [2.0, 3.0])
    # given numbers, the function returns a number: it converts no argument
    # to an array
    saved = compile_kernel(calibrated, "cntn_to_dcsn:Pullback")(2.0, 0.5)
    assert isinstance(saved, float) and saved == 1.5
    # the function checks no shape; NumPy refuses arrays whose shapes do
    # not broadcast
    with pytest.raises(ValueError, match="could not be broadcast"):
        G(numpy.ones(2), 2.0, numpy.ones(3), 2.0)


def test_settings_and_definitions_of_read_the_bindings_and_the_table_in_their_order(cons, cons_configured):
    assert cons.settings.list() == ()
    rows = cons_configured.settings.list()
    # the settings the addition declares first, in declaration order, then
    # the names the configuration bound that no file declares (S1)
    declared = ["n_a", "a_min", "a_max", "n_m", "m_min", "m_max"]
    assert [row["name"] for row in rows] == declared + [
        name for name in cons_configured.bindings.settings if name not in declared]
    assert all(row["value"] == cons_configured.bindings.settings[row["name"]] for row in rows)
    with pytest.raises(TypeError):
        rows[0]["name"] = "renamed"
    # the fact the retired `definitions_of` stated: the records of one kind are
    # the listing's section read through the table, one visible composition at
    # the call site (AMD-SG-020 §3.1, §6 choice 2)
    listing = cons.definitions.list()
    assert list(listing["correspondence"]) == ["cons:correspondence:Γ"]
    assert "distribution" not in listing
    assert all(cons.definitions[identity].identity == identity for identity in listing["function"])


# the graph queries and the drawing



def test_a_graph_query_refuses_an_unknown_level_or_grain_and_raises_a_refusal_as_not_constructed(cons, cons_savings_iid):
    with pytest.raises(ValueError, match="level must be 'initial' or 'builders'"):
        graph_of(cons, "diagram", "backward")
    with pytest.raises(ValueError, match="require direction="):
        graph_of(cons, "builders", None)
    with pytest.raises(ValueError, match="grain must be one of"):
        graph_of(cons, "builders", "backward", "fine")
    with pytest.raises(NotConstructed):
        graph_of(stage_from_text(OPAQUE_FAMILY), "builders", "forward")


def test_the_drawing_of_a_graph_lists_its_boxes_under_the_labels_of_its_printed_listing(ez_savings):
    from discopy.frobenius import Bubble

    def bubbles(diagram):
        return sum(1 + bubbles(box.arg) for box in diagram.boxes if isinstance(box, Bubble))
    for grain in ("builder", "sub-builder", "primitive"):
        graph = graph_of(ez_savings, "builders", "backward", grain)
        drawing = to_drawing(graph)
        assert str(graph).splitlines() == list(drawing.labels), grain
        assert drawing.source.startswith("digraph {") and drawing.source.count("subgraph ") == bubbles(graph.to_diagram())


def test_a_function_wire_is_labeled_at_its_coordinates_and_a_measure_wire_by_its_perch_alone(
        sa_savings, tenure):
    """A function's wire is labeled at the coordinates its sort retains,
    `𝑉≻(a)`; a measure's wire is `μ`, with its field as a subscript where it
    has one and its perch mark, and no coordinates, `μ≺`, `μ_keep≻` (AAS,
    M-D1), in the label and in the tooltip."""
    backward = to_drawing(graph_of(sa_savings, "builders", "backward", "sub-builder")).source
    for label in ("𝑉≻(a)", "𝐶𝐸(m_d, ν)", "𝐴𝑀𝐵(m_d)", "𝑉(m_d)"):
        assert f'label="{label}"' in backward, label
    with_coordinates = re.compile(r'μ(?:_[^\s"(]+)?[≺∼≻]?\(')
    # sa_savings.bl has no arrival perch, so no arrival measure (decision
    # MB-V49)
    for stage, measures in ((sa_savings, ("μ", "μ≻")),
                            (tenure, ("μ≺", "μ", "μ_keep≻", "μ_adjust≻"))):
        forward = to_drawing(graph_of(stage, "builders", "forward", "primitive")).source
        for label in measures:
            assert f'label="{label}"' in forward, label
        assert with_coordinates.findall(forward) == [], measures


def test_a_drawn_occurrence_result_names_the_value_its_line_defines(cons_savings_iid, port):
    # the result of the value line's expectation is one wire, known by no
    # weight of its own (P21-1 drops the `penwidth="3"`), whose tooltip prints
    # the held expression, whose bound variables are the coordinates, the
    # state `b` and the shock `y` (AMD-SG-034 §4 item 2): the expectation
    # reads the Pullback's output, printed as the composite
    source = cons_savings_iid.builder.bwd.primitives.diagram().source
    named = [line for line in source.splitlines()
             if 'tooltip="dcsn_to_arvl.value:Expectation:1:result' in line]
    assert len(named) == 1
    label, tooltip = named[0].split(' tooltip="', 1)
    assert "𝑉(𝑔(b, y))" in tooltip
    assert 'class="wire-' in named[0] and 'penwidth="3"' not in named[0]
    # a line whose left side is a control, the objective of an argmax, names its
    # result by the statement it realises, so that the two expectation results of
    # `port.bl`'s policy never carry one label
    policy = port.builder.bwd.primitives.diagram().source
    objective = [line for line in policy.splitlines()
                 if 'tooltip="policy.objective:Expectation:1:result' in line]
    foc = [line for line in policy.splitlines()
           if 'tooltip="policy.foc:Expectation:1:result' in line]
    # the objective's expectation forms no piece (AMD-SG-034 §11 item 1), so
    # the residual's alone is drawn
    assert len(objective) == 0 and len(foc) == 1
    # the two shocks of the joint law are bound by their names under the
    # expectation as the file writes it, `E_{Ψ, θ}`, and read by name, no
    # component of a joint variable (AMD-SG-034 §4 item 7; critique F1); the
    # expectation reads its aggregation's result by reference, and that
    # wire's own label holds the integrand (T5)
    assert "E_{Ψ, θ}[policy.foc:Aggregation:1(k_d, ς, Ψ, θ)]" in foc[0]
    integrand = [line for line in policy.splitlines()
                 if 'tooltip="policy.foc:Aggregation:1:result' in line]
    assert len(integrand) == 1
    assert "D_{m_next}𝑉≻(𝑔(k_d, ς, Ψ, θ)) · (Ψ − R)" in integrand[0]
    assert "(Ψ, θ)[1]" not in foc[0] and "(Ψ, θ)[1]" not in integrand[0]






def test_a_shock_a_joint_declaration_names_is_drawn_where_its_listed_component_is_drawn(elaborate_text):
    # structure review C3 (map/distributions F1): the edge that draws a shock
    # was derived three ways, and `fields()` followed the shock arguments of
    # a declaration alone, so on a stage whose forward builder lists `y` of
    # `(y, z) ~ N(…)` it omitted `z`, which the fold draws with `y` (AMD-SG-009
    # §2); the one assignment of the distributions folder now serves both
    from conftest import two_nodes
    text = two_nodes(transition="    a = y\n",
                     declarations="z : ℝ\nr : [-1,1]\n(y, z) ~ N((0,0),((1,r),(r,1)))\n",
                     backward="    V = E_{y,z}(V[>]) :: [id=value]\n")
    listed = "(k_d, c : !ctrl @ [0,1], y, z) : !dcsn"
    assert text.count(listed) == 1
    stage = elaborate_text(text.replace(listed, "(k_d, c : !ctrl @ [0,1], y) : !dcsn"), "one_listed.bl")
    fields = stage.fields()
    assert [identity.field for identity, sort in fields.items() if sort.role == "shock"] == ["y", "z"]
    assert {identity.field: edge for identity, edge in fields.edges.items()} == {
        "y": ("dcsn", "cntn"), "z": ("dcsn", "cntn")}
    assert "y, z drawn after decision, before continuation" in str(stage)


def test_the_recipe_reads_the_parameters_the_declaration_pass_classifies(elaborate_text):
    # structure review C3 (map/surface S5): the recipe read a fill against
    # its own rule for the parameters of a stage text, the coordinates of
    # top-level declarations that carry no value and that no law makes a
    # shock, which counts a field a header lists; the declaration pass, whose
    # answer stage.par prints, does not (rule parameter-or-field)
    from conftest import two_nodes
    from bellman.factory.recipe import declared_parameters
    text = two_nodes()
    assert text.count("R : ℝ₊₊\n") == 1
    text = text.replace("R : ℝ₊₊\n", "R : ℝ₊₊\nk_d : ℝ\n")
    stage = elaborate_text(text, "declared_field.bl")
    assert [row["name"] for row in stage.par.list()] == ["β", "R"]
    assert tuple(declared_parameters(text, "declared_field.bl")) == ("β", "R")




def test_a_method_bound_on_an_argmax_is_stored_under_the_box_the_fold_names(ez_savings):
    # structure review C3 (map/fold F1; decision S7 of the cleanup): a method
    # bound on `policy.objective.argmax` was once stored under a key no piece
    # answers to, because the fold and the method table named the box of an
    # argmax line differently. The fold names that row Argmax (lane K of the
    # internal developer release 0.01), and the method table reads the box an
    # argmax occurrence binds from the row the fold forms from its line, so the
    # box that realizes an argmax is named once, Argmax
    bound = copy_native(ez_savings).methodize({
        "text": "@methods: ez_savings\npolicy.objective.argmax.method : !golden_section\n",
        "origin": "ez_savings.methods.bl"})
    assert list(bound.methods) == ["policy.objective.argmax"]
    argmax = bound.builder.policy["objective:Argmax"]
    assert [str(held) for held in argmax.methods.values()] == ["!golden_section"]
    assert "!golden_section" in str(argmax)
    assert "policy.objective.argmax" in str(bound.view())


def test_the_package_version_is_read_by_one_rule(monkeypatch, elaborate_text, text_of):
    # structure review C3 (audit H5; decision S9 of the cleanup): the
    # provenance read the installed distribution's metadata, else answered
    # `unreleased`, while the encoding read the pyproject.toml above the
    # imported package; on a checkout that is not installed, the condition
    # of a fresh clone, one document then stated two versions
    import importlib.metadata as metadata

    def none_installed(name):
        raise metadata.PackageNotFoundError(name)
    monkeypatch.setattr(metadata, "version", none_installed)
    stage = elaborate_text(text_of("cons"), "cons.bl")
    document = stage.encoding()
    assert document["package_version"] == document["provenance"]["versions"]["package"] != "unreleased"






# the source printer

def test_every_statement_and_distribution_declaration_of_the_corpus_prints_to_source_that_lowers_to_an_equal_term(text_of):
    for name in STAGES:
        term, _ = parse_with_spans(text_of(name))
        statements = [(address, item) for address, item in item_addresses(term) if isinstance(item, T.Statement)]
        assert statements, name
        for address, item in statements:
            printed = to_source(item.core)
            if "." in address:   # a line of a block, read back as the one line of a block
                text = "@stage: x\n[id=b, (x) : !dcsn -> (y) : !dcsn] {\n    " + printed + "\n}\n"
                relowered = parse_with_spans(text).term.items[1].body[0].core
            else:                # a declaration, a definition or an assignment, read back as the one item after @stage
                relowered = parse_with_spans("@stage: x\n" + printed + "\n").term.items[1].core
            assert to_json(relowered) == to_json(item.core), (name, address, printed)


# the target inventory and the queries of AMD-SG-006 §5



def test_fields_carry_the_meet_of_the_sets_a_field_is_declared_with(elaborate_text):
    def domains(text):
        return {identity: None if sort.domain is None else to_source(sort.domain)
                for identity, sort in fields(elaborate_text(text)).items()}
    # the named set Xa is defined by a comprehension, a form the rules of the
    # meet do not decide; a set a typing names is defined (rule name-in-scope)
    narrowed = domains("@stage: t\nXa := {q : ℝ | q >= 1}\n"
                       "[id=b, (x : ℝ, y : [0, 2), z : Xa) : !arvl -> (w : ℝ) : !dcsn] {\n    w = x\n}\n"
                       "[id=d, (x : R++, y : (1, 3], z : Xa) : !arvl -> (v : ℝ) : !dcsn] {\n    v = x\n}\n")
    assert (narrowed["t:arvl:x"], narrowed["t:arvl:y"], narrowed["t:arvl:z"]) == ("ℝ₊₊", "(1, 2)", "Xa")
    assert domains("@stage: t\n[id=b, (x : [-inf, inf)) : !arvl -> (w : ℝ) : !dcsn] {\n    w = x\n}\n"
                   "[id=d, (x : ℝ) : !arvl -> (v : ℝ) : !dcsn] {\n    v = x\n}\n")["t:arvl:x"] == "ℝ"
    # a pair the rules do not meet leaves the field without a set
    assert domains("@stage: t\nXa := {q : ℝ | q >= 1}\n[id=b, (x : Xa) : !arvl -> (w : ℝ) : !dcsn] {\n    w = x\n}\n"
                   "[id=d, (x : ℝ₊) : !arvl -> (v : ℝ) : !dcsn] {\n    v = x\n}\n")["t:arvl:x"] is None








def test_diagnostics_answer_the_nine_questions_of_the_construction_and_a_refused_graph_is_not_ready(cons):
    # the key `obligations` became the two keys `forward_map` and
    # `builder_choice`, the tags its entries carried, so that the word
    # obligation names one object (AMD-SG-020 §3.3); `unread_inputs` names
    # the value inputs a backward header lists and no line reads, of which the
    # policy header of `cons.bl`, listing `V[>]` alone, has none
    assert dict(diagnostics(cons)) == {
        "complete_signature": True, "missing_builders": (), "exposed_inputs": (), "unused_outputs": (),
        "forward_map": (), "builder_choice": (), "external_calls": (),
        "unread_inputs": (),
        "ready_for_interpretation": True}
    # a family the extension does not admit leaves the forward measures refused
    assert diagnostics(stage_from_text(OPAQUE_FAMILY))["ready_for_interpretation"] is False


def test_operators_of_lists_the_primitive_boxes_of_a_builders_graph_and_refuses_another_argument(cons):
    # one evaluation on the value bundle, not one per component (AMD-SG-011 §2)
    assert [box.name for box in operators_of(cons) if block_id_of(box) == "cntn_to_dcsn"] == [
        "cntn_to_dcsn:Pullback", "cntn_to_dcsn:Aggregation", "cntn_to_dcsn:Evaluation"]
    assert operators_of(cons) == operators_of(cons, "backward") + operators_of(cons, "forward")
    with pytest.raises(ValueError, match="no direction, 'backward' or 'forward'"):
        operators_of(cons, "initial")
    opaque = stage_from_text(OPAQUE_FAMILY)
    with pytest.raises(NotConstructed):
        operators_of(opaque, "forward")
    assert operators_of(opaque) == operators_of(opaque, "backward")




def test_the_kernel_of_a_pullback_of_one_branch_holds_the_kernel_of_the_branch_s_section(
        tenure, ret_choice, old_choice):
    """A pullback of one branch applies the complete law of motion, whose
    `kernel()` prints every branch's components with the label coordinate
    `d` unused; the record holds under `section` the kernel of the law read
    at the branch's label, the section the card's `Where` section defines,
    `𝑔_keep≻`: the law's title, the law's arguments but `d`, the components
    of the fields the branch writes, and their outputs, unused arguments and
    reads by the law's rules, which name no output of a section of one
    output; it holds the box's origins and no Python text. Every other
    operator holds None (unit K of model interface spec 0.4, Task 14;
    decision K-I203)."""
    expected = (
        (tenure, "cntn_to_dcsn:Pullback:keep",
         "𝑔 of dcsn_to_cntn: 𝑔_keep≻(a_d, h_d, z_d) = (R*a_d + 𝑦(z_d), (1 - δ)*h_d, z_d)\n"
         "outputs (w_kp≻, h_kp≻, z_kp≻); w_kp≻ reads a_d, z_d; h_kp≻ reads h_d; z_kp≻ reads z_d"),
        (ret_choice, "policy:Pullback:work", "𝑔 of dcsn_to_cntn: 𝑔_work≻(a_d) = a_d"),
        (old_choice, "cntn_to_dcsn:Pullback:retiree",
         "𝑔 of dcsn_to_cntn: 𝑔_retiree≻(a, θ) = a\nunused θ"),
    )
    for stage, key, text in expected:
        piece = stage.builder.bwd.primitives[key]
        whole, section = piece.kernel(), piece.kernel().section
        assert str(section) == text, key
        assert "unused d" in str(whole)
        assert str(section).split(": ", 1)[0] == str(whole).split(": ", 1)[0]
        assert [name for name, _ in section.arguments] == [
            name for name, _ in whole.arguments if name != "d"]
        assert set(section.outputs) < set(whole.outputs)
        assert section.origins == whole.origins
        assert (section.python, section.parameters, section.section) == (None, (), None)
        # the section's name is the one the card defines under `Where`
        assert str(section).split(": ", 1)[1].split("(")[0] in str(piece.denote())
    assert tenure.builder.bwd.primitives["cntn_to_dcsn:Aggregation"].kernel().section is None
    assert tenure.builder.fwd.primitives["dcsn_to_cntn:Pushforward"].kernel().section is None








def test_a_transition_without_a_documentary_choice_set_uses_the_law_domain(
        elaborate_text, text_of, explicit_cons_text):
    source = explicit_cons_text
    documentary = (
        "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   "
        ":: [id=optimality, !doc]\n"
    )
    assert source.count(documentary) == 1
    stage = elaborate_text(source.replace(documentary, ""), "cons_without_documentation.bl")
    [law] = stage.definitions.denote("cons:g:dcsn_to_cntn").denoted
    domain = str(law.mathematical_type)
    # the feasibility a file without a correspondence declares is the law's
    # image in its declared target, held by reference (AMD-SG-034 §10 item 4)
    assert "𝑔(m_d, c) ∈ Xa" in domain
    assert "(m_d − c)" not in domain and "Γ" not in domain
    [condition] = [item for item in stage.obligations()
                   if item.condition == "range-compatibility"
                   and str(item.entries[0]) == "dcsn_to_cntn.1"]
    assert condition.status == "established"
    assert condition.evidence == (
        "restriction to the declared output set in D_g at dcsn_to_cntn.1",)
    law = compile_kernel(stage.calibrate({"ρ": 2.0}), "dcsn_to_cntn:Pushforward")
    assert law(2.0, 1.0) == 1.0
    assert law(1.0, 2.0) == -1.0


def test_joint_choice_restrictions_establish_the_transition_range(adjuster_cons):
    [condition] = [item for item in adjuster_cons.obligations()
                   if item.condition == "range-compatibility"
                   and str(item.entries[0]) == "dcsn_to_cntn.savings"]
    assert condition.status == "established"
    assert condition.evidence == (
        "declared choice set for adjuster_cons:dcsn:c: (0, m]",
        "declared choice set for adjuster_cons:dcsn:h_choice: "
        "(0, (m − c)/(1 + τ)]",
        "arithmetic range inclusion at dcsn_to_cntn.savings",
    )
    tau, resources, consumption, housing = 1.0, 10.0, 4.0, 3.0
    assert 0 < consumption <= resources
    assert 0 < housing <= (resources - consumption) / (1 + tau)
    stage = copy_native(adjuster_cons).calibrate({
        "β": 0.96, "α": 0.5, "γ_c": 2.0, "γ_h": 2.0, "κ": 1.0, "τ": tau,
    })
    law = compile_kernel(stage, "dcsn_to_cntn:Pushforward")
    assert kernel(stage, "dcsn_to_cntn:Pushforward").parameter_values == (tau,)
    assert tuple(map(float, law(resources, 2.0, consumption, housing, tau))) == (0.0, 3.0, 2.0)
    assert float(law(resources, 2.0, consumption, housing + 1.0, tau)[0]) < 0


def test_identification_and_evaluation_hold_one_feasibility_by_the_declared_correspondence(
        cons, elaborate_text, text_of, explicit_cons_text, cons_explicit):
    """One feasibility per output, by the correspondence where the file
    declares one and by the law's image otherwise, the same on the
    identification, the Pullback whose output is the policy, and on the
    Evaluation (AMD-SG-034 §4 items 3 and 5, §10 item 4)."""
    cons = cons_explicit
    policy = cons.builder.policy
    identification = policy["cons_choice:Pullback"].denote().outputs[0]
    evaluation = policy["Evaluation"].denote().outputs[0]
    assert identification.mathematical_type == evaluation.mathematical_type
    # the Evaluation holds the rules of the operation it names, before any
    # rule of its own
    assert evaluation.rules[:len(identification.rules)] == identification.rules
    assert identification.definition == evaluation.definition
    carrier = S.format_expression(identification.mathematical_type.carrier, width=None)
    assert carrier == "𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})"
    # the coordinate stands free in the condition, read at every point
    assert "∀" not in carrier
    documentary = "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality, !doc]\n"
    without = elaborate_text(explicit_cons_text.replace(documentary, ""), "cons_law_image.bl")
    undocumented = without.builder.policy["cons_choice:Pullback"].denote().outputs[0]
    assert S.format_expression(undocumented.mathematical_type.carrier, width=None) == (
        "𝒫({c ∈ (Xm → ℝ₊₊) | 𝑔(m_d, c(m_d)) ∈ Xa})")


def test_a_joint_policy_carries_one_set_and_keeps_its_declared_correspondence(adjuster_cons):
    # The two outputs are one joint policy, and each carries the one set of
    # joint policies the Argmax determines (AMD-SG-030 §1). A declared
    # correspondence remains visible in its public definition, and is assigned
    # independently to no component output.
    plain = stage_from_text(NAMED_CONTROLS, "two_controls.bl")
    outputs = plain.builder.policy.signature().outputs
    assert len(outputs) == 2
    assert all("joint relation projection" not in str(wire.mathematical_type) for wire in outputs)
    assert S.alpha_equivalent(outputs[0].mathematical_type.carrier,
                              outputs[1].mathematical_type.carrier)
    declared = stage_from_text(
        NAMED_CONTROLS.replace("@stage: joint_choice", "@stage: joint_choice\nΓ(x : ℝ) := (0,1]")
                      .replace("argmax_{c,l}", "argmax_{c, l : Γ(x_d)}"),
        "two_controls_feasible.bl")
    outputs = declared.builder.policy.signature().outputs
    assert len(outputs) == 2
    assert all("joint relation projection" not in str(wire.mathematical_type) for wire in outputs)
    assert S.alpha_equivalent(outputs[0].mathematical_type.carrier,
                              outputs[1].mathematical_type.carrier)
    [correspondence] = declared.definitions.denote(
        "joint_choice:correspondence:Γ").denoted
    assert str(correspondence.mathematical_type) == "ℝ ⇉ ℝ"
    assert str(correspondence.expression) == "x ↦ (0, 1]"
    choice = declared.definitions["policy.choice"].equations[0].rhs
    assert isinstance(choice, T.Operator) and choice.head == "argmax"
    assert isinstance(choice.subs[0], T.Var) and choice.subs[0].name == "c"
    assert isinstance(choice.subs[1], T.In) and choice.subs[1].var == "l"
    assert S.format_expression(choice.subs[1].set, width=None) == "Γ(x_d)"
    # both controls are the coordinates their blocks are read at, in both
    # directions, and are wires of neither initial diagram (AMD-SG-013 §3)
    for block in (plain.initial.backward["cntn_to_dcsn"],
                  plain.initial.forward["dcsn_to_cntn"]):
        assert [(item.symbol, str(item.mathematical_type))
                for item in block.denote().coordinate] == [("c", "ℝ"), ("l", "ℝ")]
        inputs = [identity for identity, _ in block.signature().inputs]
        assert "joint_choice:dcsn:c" not in inputs and "joint_choice:dcsn:l" not in inputs

    controls = tuple(wire for wire in adjuster_cons.builder.policy.signature().outputs
                     if wire.sort.role == "control")
    assert len(controls) == 2
    for wire in controls:
        assert tuple(identity.field for identity in wire.controls) == ("c", "h_choice")
        assert "UNRESOLVED" not in str(wire.mathematical_type)
    assert S.alpha_equivalent(controls[0].mathematical_type.carrier,
                              controls[1].mathematical_type.carrier)
    for name in ("c", "h_choice"):
        projected = controls[0].component(name)
        assert "UNRESOLVED" not in str(projected) and "∃" in str(projected)
    with pytest.raises(KeyError):
        controls[0].component("not_a_control")


def test_a_joint_choice_reads_one_correspondence_for_each_control_it_writes():
    # a joint choice over several controls writes the ordered tuple on the left
    # (AMD-SG-008 §7); where every control carries a set the subscript in the
    # control's own position is that control's, whatever letter it names
    # (AMD-SG-013 §2)
    declared = NAMED_CONTROLS.replace(
        "@stage: joint_choice", "@stage: joint_choice\nΓ(x : ℝ) := (0,1]\nΛ(x : ℝ) := (0,2]")
    own = stage_from_text(declared.replace(
        "argmax_{c,l}(-c^2-4*l^2+V[>])", "argmax_{cp : Γ(x_d), lp : Λ(x_d)}(-cp^2-4*lp^2+V[>])"),
        "joint_own_letters.bl")
    outputs = own.builder.policy.signature().outputs
    assert len(outputs) == 2
    assert all("joint relation projection" not in str(wire.mathematical_type) for wire in outputs)
    assert S.alpha_equivalent(outputs[0].mathematical_type.carrier,
                              outputs[1].mathematical_type.carrier)
    choice = own.definitions["policy.choice"].equations[0].rhs
    assert isinstance(choice, T.Operator) and choice.head == "argmax"
    assert [(sub.var, S.format_expression(sub.set, width=None))
            for sub in choice.subs if isinstance(sub, T.In)] == [
        ("cp", "Γ(x_d)"), ("lp", "Λ(x_d)")]
    for name, expression in (("Γ", "x ↦ (0, 1]"),
                             ("Λ", "x ↦ (0, 2]")):
        [correspondence] = own.definitions.denote(
            f"joint_choice:correspondence:{name}").denoted
        assert str(correspondence.mathematical_type) == "ℝ ⇉ ℝ"
        assert str(correspondence.expression) == expression

    # Where one control alone has a binder, the joint set is the same object on
    # both outputs and the definition records which control reads the set.
    mixed = stage_from_text(declared.replace("argmax_{c,l}", "argmax_{c, l : Γ(x_d)}"),
                            "joint_one_set.bl")
    outputs = mixed.builder.policy.signature().outputs
    assert len(outputs) == 2
    assert all("joint relation projection" not in str(wire.mathematical_type) for wire in outputs)
    assert S.alpha_equivalent(outputs[0].mathematical_type.carrier,
                              outputs[1].mathematical_type.carrier)
    choice = mixed.definitions["policy.choice"].equations[0].rhs
    assert isinstance(choice.subs[0], T.Var) and choice.subs[0].name == "c"
    assert isinstance(choice.subs[1], T.In) and choice.subs[1].var == "l"
    assert S.format_expression(choice.subs[1].set, width=None) == "Γ(x_d)"


def test_the_feasibility_condition_is_read_from_a_subscript_that_names_its_own_letter():
    # the author may bind a letter of his own on the operative line,
    # `c = argmax_{cp : Γ(k_d)}(…)`, and the single subscript of a line whose
    # left side is the control is that control's, on a documentary line and on
    # an operative one alike (AMD-SG-013 §2)
    stage = stage_from_text(BUNDLES, "bundles.bl")
    evaluation = stage.builder.policy["Evaluation"].denote().outputs[0]
    assert str(evaluation.identity) == "policy:Evaluation:c:result"
    [correspondence] = stage.definitions.denote(
        "bundles:correspondence:Γ").denoted
    assert str(correspondence.mathematical_type) == "ℝ ⇉ ℝ₊₊"
    assert str(correspondence.expression) == "k ↦ (0, 1]"
    objective = stage.definitions["policy.objective"].equations[0].rhs
    assert isinstance(objective, T.Operator) and objective.head == "argmax"
    assert len(objective.subs) == 1 and isinstance(objective.subs[0], T.In)
    assert (objective.subs[0].var,
            S.format_expression(objective.subs[0].set, width=None)) == (
        "cp", "Γ(k_d)")
    # Evaluation is exact identity. The specialised pullback writes the law
    # at the supplied policy out (RL14): no `where` entry names it, its
    # output is `𝑉≻ ∘ 𝑔≻(·, 𝑐)` and its rule reads the policy at the point;
    # the correspondence and its binder are checked above through their
    # public answers.
    pullback = stage.dcsn.builder.bwd["pullback"]
    assert pullback.denote().where == ()
    printed = str(pullback)
    assert "out  𝑉≻ ∘ 𝑔≻(·, 𝑐)" in printed and "Where" not in printed
    assert "(𝑉≻ ∘ 𝑔≻(·, 𝑐))(k_d) = 𝑉≻(𝑔≻(k_d, 𝑐(k_d)))" in printed


def test_an_aggregation_states_in_its_denotation_the_value_its_map_is_affine_in(cons, ez_savings):
    """The two verbs AMD-SG-020 §3.2 merged. `affine()` is a line of the
    aggregation's denotation, one line per output where the box writes several
    (AMD-SG-011 §2), and `origins()` is the field `origins` of the record
    `kernel()` answers. The two functions beneath them stay as implementation
    (AMD-SG-010 §4)."""
    aggregation = cons.dcsn.builder.bwd["aggregation"].denote()
    assert aggregation.affine == "V in V≻"
    assert affine(cons, aggregation_box(cons, "cntn_to_dcsn")) is True
    # a box that writes one output records the one map, affine or not affine;
    # Evaluation, rather than Aggregation, gives that map its evaluated name
    # the identity arrival aggregation of cons.bl, since ez_savings.bl has no
    # arrival perch (decision MB-V45)
    assert cons.arvl.builder.bwd["aggregation"].denote().affine == "V in V"
    assert ez_savings.dcsn.builder.bwd["aggregation"].denote().affine == (
        "none in E_{Ψ}(V[>]^(1 - γ))")
    assert affine(ez_savings, aggregation_box(ez_savings, "cntn_to_dcsn")) is False
    assert affine(cons, aggregation_box(cons, "dcsn_to_arvl")) is True
    # the declaration a pullback applies is the record its kernel carries
    assert [record.identity for record in cons.dcsn.builder.bwd["pullback"].kernel().origins] == [
        "cons:g:dcsn_to_cntn"]


def test_the_reader_surface_and_the_register_are_what_the_documents_state(cons):
    """The document checks of the retired acceptance file of AMD-SG-012,
    items 1, 2 and 6 (the third layer of the tests,
    `packages/bellman/README.md` §8)."""
    root = Path(__file__).resolve().parents[3]
    pages = STAGE_OBJECT_PAGES + ("docs/Bellman-Sym/01-stage.md",
                                  "docs/overview/05-semantics.md")
    calculus = ("docs/bellman-calculus/02-Illustrative example.md",
                "docs/bellman-calculus/03-Stages and perches.md",
                "docs/bellman-calculus/04-fields, functions and types.md",
                "docs/bellman-calculus/05-Operators and builders.md",
                "docs/Bellman-Sym/reference/symbols-conventions.md")

    def text_of(path):
        return (root / path).read_text(encoding="utf-8")

    # the reader reaches a grain by an attribute; the string grain and the
    # retired stage query resolve nowhere and are named on no page
    assert not hasattr(cons.builder.bwd, "at") and not hasattr(cons.dcsn.builder.bwd, "at")
    assert not hasattr(cons, "operators_of")
    # and the thirteen names AMD-SG-020 retires, each as the call form a reader
    # would write: the ten questions §3.1 removes from the stage and the three
    # handle verbs §3.2 merges into the verbs that state their facts. A form
    # that could also stand in ordinary prose — `selection(`, `kind(`,
    # `origins(` and the rest — is written with the dot of its receiver
    retired_names = (".at(", "at(grain)", "operators_of",
                     "transition_map(", "aggregator(", "policy_relation(", "methods_of(",
                     "definitions_of(", "expectations(", ".selection(", ".symbols(",
                     ".kind(", ".branches(", ".origins(", ".affine(", ".directions(")
    for path in pages:
        shown = text_of(path)
        for retired in retired_names:
            assert retired not in shown, (path, retired)
    # a function is italic and a field roman, on the pages as in the package
    for path in calculus:
        shown = text_of(path)
        for form in (r"\mathrm v(", r"\mathrm v_\succ(", r"\mathrm g(", r"\mathrm G(",
                     r"\mathrm r(", r"\mathrm u("):
            assert form not in shown, (path, form)
    note = text_of("docs/bellman-calculus/02-Illustrative example.md")
    assert "roman letters denote functions" not in note
    for phrase in ("A function is italic", "A field is a roman capital", "A variable is italic"):
        assert phrase in note
    agents = text_of("AGENTS.md")
    assert "Pullback of the function 𝑉 along the law of motion 𝑔" in agents
    for path in ("AGENTS.md", "docs/wiki/semgraph.md", "docs/wiki/builder.md",
                 "docs/wiki/operator.md", "docs/wiki/elaborated_stage.md"):
        assert "Function maker" not in text_of(path), path




def test_product_selection_compiles_in_g_and_G_with_batch_axes_last(elaborate_text):
    stage = elaborate_text(JOINT_CHOICE).calibrate({})
    g = compile_kernel(stage, 'cntn_to_dcsn:Pullback')
    G = compile_kernel(stage, 'cntn_to_dcsn:Aggregation')
    assert str(inspect.signature(g)) == '(x_d, u)'
    assert str(inspect.signature(G)) == '(V_cntn, x_d, u)'
    numpy.testing.assert_array_equal(g(numpy.array([10,20]), [[1,2],[3,4]]), [13,27])
    numpy.testing.assert_array_equal(G(numpy.array([10,30]), [10,20], [[1,2],[3,4]]), [5,5])
    assert float(g(10, (1,2))) == 13
    # the function checks no declared shape: the third component is not read
    assert float(g(10, (1,2,3))) == 13

def test_fixed_family_selection_uses_declared_labels_and_takes_each_calibration_as_arguments(elaborate_text):
    symbolic = elaborate_text(FINITE_STATE)
    stage = symbolic.calibrate({'prices': (5,7)})
    target = 'cntn_to_dcsn:Pullback'
    g = compile_kernel(stage, target)
    held = kernel(stage, target)
    assert str(inspect.signature(g)) == '(x_d, z_d, u, prices)'
    assert held.parameter_values == ((5, 7),)
    assert 'unused z_d' not in held
    numpy.testing.assert_array_equal(g(numpy.array([10,20]), ['high','low'], [[1,2],[3,4]], *held.parameter_values), [18,28])
    numpy.testing.assert_array_equal(g(10, ['high','low'], (1,2), *held.parameter_values), [18,16])
    # the labels are compared in the order of the declared set
    assert held.python.index("np.asarray(z_d) == 'low'") < held.python.index("np.asarray(z_d) == 'high'")
    again = kernel(symbolic.calibrate({'prices': (50,70)}), target)
    assert again.python == held.python
    assert (float(g(10,'high',(1,2), *again.parameter_values)), float(g(10,'high',(1,2), *held.parameter_values))) == (81,18)
    # the function checks no label: a label outside the declared set selects
    # no value
    assert numpy.isnan(g(10,'missing',(1,2), *held.parameter_values))
    named = FINITE_STATE.replace('prices : ℝ × ℝ','Prices := ℝ × ℝ\nprices : Prices')
    assert float(compile_kernel(elaborate_text(named).calibrate({'prices':(5,7)}), target)(10,'high',(1,2),(5,7))) == 18
    called = FINITE_STATE.replace('prices : ℝ × ℝ','prices : ℝ × ℝ\nprice(state : Z) := prices[state]').replace('prices[z_d]','price(z_d)')
    assert float(compile_kernel(elaborate_text(called).calibrate({'prices':(5,7)}), target)(10,'high',(1,2),(5,7))) == 18

def test_diagnostics_reads_function_bodies_and_distribution_arguments(elaborate_text, text_of, explicit_cons_text):
    source = explicit_cons_text.replace('c^(1-ρ)/(1-ρ)','neverdef(c)/(1-ρ)')
    stage = elaborate_text(source)
    report = stage.diagnostics()
    assert [entry[1:] for entry in report['external_calls']] == [('neverdef',1)]
    assert not report['ready_for_interpretation']
    law = elaborate_text(TWO_NODES.replace('N(0,1)','N(log(1),1)',1))
    assert [entry[1:] for entry in law.diagnostics()['external_calls']] == [('log',1)]
    assert not law.diagnostics()['ready_for_interpretation']
    law.builder.fwd
    inverse = elaborate_text(explicit_cons_text.replace('𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)','𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)'))
    assert inverse.diagnostics()['external_calls'] == ()
    assert not any('external:Inv' in str(o.entries) for o in inverse.obligations())
    assert any(o.condition == 'inverse-function-domain' for o in inverse.obligations())

def test_bare_maximisation_displays_the_controls_declared_set(elaborate_text, text_of, explicit_cons_text):
    stage = elaborate_text(explicit_cons_text.replace('argmax_{cp : Γ(m_d)}','argmax_{c}').replace('𝑢(cp)','𝑢(c)'))
    [declared] = stage.builder.bwd["policy"].denote().doc
    # a binder written without a set ranges over the control's declared set,
    # read by identity, even when the source writes no correspondence name
    # (AMD-SG-034 §3 `declared`, §4 item 2)
    statement = S.format_expression(declared.statement, width=None)
    assert statement == "c(m_d) ∈ argmax_{c ∈ ℝ₊₊} [𝑢(c) + V≻(𝑔(m_d, c))]"
    assert "UNRESOLVED" not in statement


def test_a_product_control_retains_its_coupled_correspondence(elaborate_text):
    source = JOINT_CHOICE.replace(
        "@stage: joint_choice", "@stage: joint_choice\nΓ(x : ℝ) := {u : ℝ × ℝ | u[1]+u[2] < x}").replace(
        "argmax_{u}", "argmax_{u : Γ(x_d)}")
    stage = elaborate_text(source)
    assert "u[1] + u[2] < x" in str(
        stage.definitions.denote(stage.definitions.list()["correspondence"][0]))


def test_sequential_transition_outputs_and_target_states_compile(elaborate_text):
    stage = elaborate_text(SEQUENTIAL_G).calibrate({'k': 2})
    numpy.testing.assert_allclose(compile_kernel(stage, 'arvl_to_dcsn:Pushforward')(1., .5, 2), (2.5, 3.5))
    stage = elaborate_text(TARGET_STATE_G).calibrate({'k': 2})
    assert compile_kernel(stage, 'cntn_to_dcsn:Aggregation')(1., 3.) == 3
    values = kernel(stage, 'dcsn_to_arvl.value:Aggregation:1').parameter_values
    assert compile_kernel(stage, 'dcsn_to_arvl.value:Aggregation:1')(1., 1., .5, *values) == 2.5


def test_selection_keys_preserve_distribution_and_transition_dependence(elaborate_text):
    stage = elaborate_text(SELECTED_LAW)
    conditional = stage.definitions.denote(
        "key_selection_reads:distribution:θ").denoted[0]
    assert conditional.symbol == "P_{θ|η, s}"
    assert isinstance(conditional.mathematical_type.carrier, S.StochasticKernelSet)
    assert isinstance(conditional.expression, S.Lambda)
    law = conditional.expression.body
    assert isinstance(law, S.Apply) and S.format_expression(law.function) == "LogNormal"
    eta, scale = law.args
    # the parent shock is read by its own bound variable, `η`, and the
    # two-point state by the authored key selection (AMD-SG-034 §4 item 2)
    assert isinstance(eta, T.Sym) and S.variable_identity(eta).field == "η"
    assert isinstance(scale, T.Select) and isinstance(scale.sel, T.Key) and scale.sel.at == "s"

    expectation = stage.builder.bwd[
        "dcsn_to_arvl", "value:Expectation:1"].denote()
    assert expectation.inputs[0].name == "𝑉∘𝑔"
    assert isinstance(expectation.inputs[0].mathematical_type.carrier, S.MeasurableMapSet)
    # the kernel denotes the three declarations the expectation integrates
    # against, by reference (critique F1): the law of θ as its own card holds
    # it, reading η by its own bound variable and s through the key selection
    laws = {str(item.identity): item for item in expectation.kernel.denoted}
    assert set(laws) == {"key_selection_reads:distribution:s", "key_selection_reads:distribution:η",
                         "key_selection_reads:distribution:θ"}
    theta = laws["key_selection_reads:distribution:θ"]
    assert isinstance(theta.expression, S.Lambda)
    conditional_call = theta.expression.body
    assert isinstance(conditional_call, S.Apply)
    assert S.format_expression(conditional_call.function) == "LogNormal"
    assert S.format_expression(conditional_call.args[0]) == "η"
    scale = conditional_call.args[1]
    assert isinstance(scale, T.Select) and isinstance(scale.sel, T.Key) and scale.sel.at == "s"
    # the expectation binds the three shocks one variable each under their
    # names, `E_{s, θ, η}[…]`, and the transition reads the state `k` and the
    # shocks `s` and `θ` by name, no component of a joint variable
    output = expectation.outputs[0].expression
    assert isinstance(output, S.Lambda) and isinstance(output.body, T.Operator)
    assert output.body.head == "E"
    assert {S.variable_identity(sub.name).field for sub in output.body.subs} == {"s", "θ", "η"}
    value = output.body.args[0]
    assert isinstance(value, S.Apply) and isinstance(value.args[0], S.Apply)
    point = value.args[0].args[0]
    assert isinstance(point, T.Tuple)
    assert [S.variable_identity(item).field for item in point.items] == ["k", "s", "θ"]
    calibrated = stage.calibrate({'β': .9, 'γ': 2, 'R': 1, 'P': .3, 'σ': .5})
    g = compile_kernel(calibrated, 'arvl_to_dcsn:Pushforward')
    values = kernel(calibrated, 'arvl_to_dcsn:Pushforward').parameter_values
    assert (g(2., 'lo', 3., *values), g(2., 'hi', 3., *values)) == (5, 8)


def test_policy_objective_retains_transition_integrand_and_control(cons, elaborate_text, text_of, cons_explicit):
    cons = cons_explicit
    stage = elaborate_text(RISKY_PORT).calibrate({'R': 1.03, 'φ_mean': 1.08, 'σ_φ': .2})
    pullback = stage.builder.bwd["policy", "Pullback"].denote()
    aggregation = stage.builder.bwd[
        "policy", "foc:Aggregation:1"].denote()
    foc = stage.builder.bwd["policy", "foc:Expectation:1"].denote()
    # the objective's expectation forms no piece: the line marked `!doc` is
    # held on the builder with the constructed output substituted, its
    # expectation as the file writes it, integrating the shock under its own
    # name, and its integrand reading the continuation value at the law of
    # motion of the point (w_d, ς, φ) (AMD-SG-034 §3 `declared`, §11 item 1)
    assert "optimality:Expectation:1" not in list(stage.builder.bwd["policy"].primitives.list())
    [declared] = stage.builder.bwd["policy"].denote().doc
    from bellman.native.predicates import Member
    assert isinstance(declared.statement, Member)
    maximisation = declared.statement.set
    assert isinstance(maximisation, T.Operator) and maximisation.head == "argmax"
    [expectation] = maximisation.args
    assert isinstance(expectation, T.Operator) and expectation.head == "E"
    assert [sub.name for sub in expectation.subs] == ["φ"]
    value = expectation.args[0]
    assert isinstance(value, S.Apply) and isinstance(value.args[0], S.Apply)
    objective_point = value.args[0].args[0]
    assert isinstance(objective_point, T.Tuple)
    assert [S.variable_identity(item).field if not isinstance(S.variable_identity(item), str) else S.variable_identity(item)
            for item in objective_point.items] == ["w_d", "ς", "φ"]
    assert aggregation.inputs[0].identity in {wire.identity for wire in pullback.outputs}
    assert foc.inputs[0].identity == aggregation.outputs[0].identity
    # the first-order condition's kernel reads the shock and the state by
    # their names, (φ − R) · w_d · D_{k_next}V[>](g(w_d, ς, φ))
    formula = aggregation.outputs[0].expression.body
    assert isinstance(formula, T.Mul) and isinstance(formula.left, T.Mul)
    assert isinstance(formula.left.left, T.Sub)
    assert S.variable_identity(formula.left.left.left).field == "φ"
    assert S.variable_identity(formula.left.right).field == "w_d"
    for target, arguments, value in (('policy:Pullback', (2., .3, 1.2), 2.162),
                                     ('policy.foc:Aggregation:1', (0., 2., .3, 1.2, 4.), 1.36)):
        values = kernel(stage, target).parameter_values
        assert compile_kernel(stage, target)(*arguments, *values) == pytest.approx(value)
    # the solve of the first-order condition is an Aggregation whose relation
    # has no side that is an explicit function of its inputs, so it compiles
    # to no kernel
    with pytest.raises(ConstructionError, match='kernel') as refused:
        compile_kernel(stage, 'policy.foc:Aggregation')
    assert refused.value.rule == 'kernel-target'

    # the policy builder of cons pulls back no value function once the
    # documentary objective forms no piece; the pullback at no policy is the
    # one of the risky portfolio's residual, whose carrier is the pullback at
    # a policy's
    decision = cons.builder.bwd["cntn_to_dcsn", "Pullback"].denote()
    policy = stage.builder.bwd["policy", "Pullback"].denote()
    assert decision.outputs[0].mathematical_type != policy.outputs[0].mathematical_type
    # the two pullbacks are told apart on their cards, not in the listing,
    # which prints each primitive under its key, its kind word and what it
    # produces by name (AMD-SG-034 §3): the decision builder's pullback is
    # its first operation and produces no named function; the policy
    # builder's first is the inverse Euler aggregation, which produces the
    # candidate 𝑐≻, the documentary line forming no piece (AMD-SG-034 §11
    # item 1), and its one Pullback is the identification, which pulls the
    # policy 𝑐 back along 𝑚_d≻
    assert str(cons.builder.bwd["cntn_to_dcsn"].list()) == (
        "1  Pullback     primitive\n"
        "2  Aggregation  primitive  → 𝑉\n"
        "3  Evaluation   primitive  → 𝑉")
    listing = cons.builder.bwd["policy"].list()
    assert [key for key in cons.builder.bwd["policy"].primitives.list()
            if key.endswith("Pullback")] == ["cons_choice:Pullback"]
    assert listing.entries[0][:4] == (
        "InvEuler:Aggregation", "policy.InvEuler:Aggregation", "primitive", "𝑐≻")
    assert [entry.number for entry in listing.entries] == list(range(1, len(listing) + 1))




def test_decision_and_conditional_kernels_reference_the_supplied_policy_function(cons, elaborate_text):
    builder = cons.dcsn.builder.bwd
    # the pulled-back function is the composition with the law of motion at
    # the policy written out, `m_d ↦ 𝑔≻(m_d, 𝑐(m_d))`, which reads the law
    # and the policy directly and which no abbreviation names (RL14;
    # AMD-SG-034 §4 item 6); the aggregation reads the policy directly; the
    # evaluation reads neither
    pullback = builder["Pullback"].denote()
    identities = {str(identity) for identity in S.free_identities(pullback.expression)}
    assert {"cons:function:dcsn:c", "cons:g:dcsn_to_cntn"} <= identities
    assert not any(":alias:" in identity for identity in identities)
    assert pullback.where == ()
    for name in ("Aggregation", "Evaluation"):
        identities = {str(identity) for identity in
                      S.free_identities(builder[name].denote().expression)}
        assert ("cons:function:dcsn:c" in identities) == (name != "Evaluation")

    source = two_nodes(
        declarations="y ~ N(c,1)\nz : ℝ\nz ~ N(0,1)\n",
        header="(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
    ).replace("argmax_{c : Γ(k_d)}(E_{y,z}(V[>]))", "argmax_{c : Γ(k_d)}(-c^2)")
    stage = elaborate_text(source)
    cases = (
        (stage.dcsn.builder.bwd.primitives, "Expectation"),
        (stage.dcsn.builder.fwd.primitives, "DistributionExtension"),
    )
    for handle, kind in cases:
        records = [handle[name].denote() for name in handle.list()
                   if kind_of(handle[name].box) == kind]
        assert records
        if kind == "Expectation":
            # the expectation is held as the file declares it, `E_{y}[…]`,
            # the law by reference: the kernel `y ~ N(c, 1)` stands under
            # `definitions`, its reading of the policy on its own card, and
            # no measure is constructed at the policy (critique F1)
            for record in records:
                held = record.outputs[0].expression.body
                assert isinstance(held, T.Operator) and held.head == "E"
                assert "two_nodes:distribution:y" in {str(item.identity) for item in record.definitions}
                assert "two_nodes:function:dcsn:c" not in {
                    str(identity) for identity in S.free_identities(record.expression)}
            continue
        identities = [{str(identity) for identity in S.free_identities(record.expression)}
                      for record in records]
        assert any("two_nodes:function:dcsn:c" in found for found in identities)
        assert all("two_nodes:dcsn:c" not in found for found in identities)


def test_forward_measure_expressions_reference_the_supplied_policy(cons):
    builder = cons.dcsn.builder.fwd
    push_forward = builder["Pushforward"].denote()
    # the push-forward reads the law at the policy written out, each
    # control read as its policy at the point, and names no abbreviation
    # (RL14; critique F8, as the Pullback of AMD-SG-034 §4 item 6), and
    # holds on its measure the rule at an event, the preimage of the event;
    # the state–choice measure reads the policy directly
    identities = {str(identity) for identity in S.free_identities(push_forward.expression)}
    assert {"cons:function:dcsn:c", "cons:g:dcsn_to_cntn"} <= identities
    assert not any(":alias:" in identity for identity in identities)
    assert push_forward.where == ()
    [rule] = push_forward.outputs[0].rules
    assert _rule_text(rule) == "μ≻(B) = μ({m_d ∈ Xm | 𝑔(m_d, c(m_d)) ∈ B})"
    assert "μ≻(B) = μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})" in str(push_forward)
    assert "indicator" not in str(push_forward) and "measurable-set" not in str(push_forward)
    choice = builder.state_choice_measure()
    assert "cons:function:dcsn:c" in {str(identity) for identity in S.free_identities(choice)}
    assert "UNRESOLVED" not in str(push_forward.expression) and "UNRESOLVED" not in str(choice)


def interior_cons():
    """The explicit consumption stage with its inverse-Euler line written as an
    equality without its clause `⟂ a >= 0`: the interior variant of
    `docs/Bellman-Sym/03-field-equations.md` §3."""
    from conftest import C_LINES, twin_text
    text = twin_text('cons', C_LINES)
    assert text.count('c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0') == 1
    return text.replace('c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0', 'c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])')




def test_inverse_euler_lines_form_one_policy_kernel_on_the_saving_grid_and_the_identification_remains_a_relation(elaborate_text):
    stage = elaborate_text(interior_cons()).calibrate({'ρ': 2.0})
    # the two explicit lines on the continuation grid are one pointwise G of the marginal value read at the
    # saving a and of a itself: G(w, a) = (h(w), a + h(w)) with h the declared inverse marginal utility
    assert kernel(stage, 'policy.endoggrid:Aggregation').splitlines() == [
        '𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(V≻, a, D_{a}(V≻)) = '
        '(𝑑𝑢𝑖𝑛𝑣(D_{a}(V≻)), a + 𝑑𝑢𝑖𝑛𝑣(D_{a}(V≻)))',
        'outputs (c≻, m_d≻); unused V≻; c≻ reads D_{a}(V≻); m_d≻ reads a, D_{a}(V≻)']
    G = compile_kernel(stage, 'policy.endoggrid:Aggregation')
    assert str(inspect.signature(G)) == '(V_cntn, a, argument, ρ)'
    assert tuple(map(float, G(0.0, 3.0, 4.0, 2.0))) == (0.5, 3.5)
    assert tuple(map(float, G(17.0, 3.0, 4.0, 2.0))) == (0.5, 3.5)
    face = card(stage, 'policy.endoggrid:Aggregation')
    assert 'c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])' in face and 'm_d[>] = a + c[>]' in face
    # the candidates keep their fields' sets
    answer = stage.builder.bwd["policy", "endoggrid:Aggregation"].denote()
    assert [(wire.name, wire.type) for wire in answer.inputs] == [("𝑉≻", "Xa → [−∞, ∞)")]
    assert [(wire.name, wire.type) for wire in answer.outputs] == [
        ("𝑐≻", "Xa → ℝ₊₊"), ("𝑚_d≻", "Xa → Xm")]
    # the policy on resources remains the relation c = c[>], read through the
    # coordinate function m_d[>]: the identification Pullback states it, and
    # no side of it is an explicit function of the row's inputs
    relation = stage.builder.bwd["policy", "cons_choice:Pullback"].box
    with pytest.raises(ConstructionError) as refused:
        compile_kernel(stage, relation)
    assert refused.value.rule == 'kernel-target'
    # the documentary argmax forms no piece and compiles to no kernel; the
    # builder holds it as the condition on its output (AMD-SG-034 §3 `declared`)
    [declared] = stage.builder.bwd["policy"].denote().doc
    assert S.format_expression(declared.statement, width=None) == (
        "c(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + V≻(𝑔(m_d, cp))]")
    # a candidate computed from the coordinate alone reads no value input, formal or otherwise
    rule = elaborate_text(interior_cons().replace('c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])', 'c[>]   = a/2')).calibrate({'ρ': 2.0})
    assert kernel(rule, 'policy.endoggrid:Aggregation').splitlines() == [
        '𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(a) = (a/2, a + a/2)', 'outputs (c≻, m_d≻)']
    G = compile_kernel(rule, 'policy.endoggrid:Aggregation')
    assert str(inspect.signature(G)) == '(a)'
    assert tuple(map(float, G(3.0))) == (1.5, 4.5)
    # a local name is pending arithmetic, folded where it is read, on the reader's coordinates
    text = interior_cons()
    line = next(line for line in text.splitlines() if '[id=InvEuler]' in line)
    assert text.count(line) == 1
    scaled = elaborate_text(text.replace(line, '    x      = 2*D_{a}V[>]                 :: [id=scale]\n'
                                         + line.replace('𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])', '𝑑𝑢𝑖𝑛𝑣(x)    '))).calibrate({'ρ': 2.0})
    assert kernel(scaled, 'policy.endoggrid:Aggregation').splitlines()[0] == (
        '𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(V≻, a, D_{a}(V≻)) = '
        '(𝑑𝑢𝑖𝑛𝑣(2*D_{a}(V≻)), a + 𝑑𝑢𝑖𝑛𝑣(2*D_{a}(V≻)))')
    scaled_answer = scaled.builder.bwd["policy", "endoggrid:Aggregation"].denote()
    assert [(str(line.address), line.text) for line in scaled_answer.kernel.statements
            if str(line.address) == "policy.scale"] == [
        ("policy.scale", "x      = 2*D_{a}V[>]                 :: [id=scale]")]
    assert tuple(map(float, compile_kernel(scaled, 'policy.endoggrid:Aggregation')(0.0, 3.0, 2.0, 2.0))) == (0.5, 3.5)
    # A candidate must be a control or a decision state (F39).
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text.replace('c[>]', 'cc[>]'))
    assert (refused.value.rule, refused.value.address) == ('candidate-coordinate', 'policy.InvEuler')
    # a value input of the saving grid read on the grid of another perch, and a field defined twice, are refused
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text.replace(line, line + '\n    x[<]   = D_{a}V[>]                   :: [id=arrival_read]'))
    assert (refused.value.rule, refused.value.address) == ('not-constructed', 'policy.arrival_read')
    assert 'reads V[>], a function of (a)' in refused.value.message
    endoggrid = '    m_d[>] = a + c[>]                :: [id=endoggrid]'
    assert text.count(endoggrid) == 1
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text.replace(endoggrid, endoggrid + '\n    m_d[>] = a + 1                   :: [id=again]'))
    assert (refused.value.rule, refused.value.address) == ('defined-once', 'policy.again')




def test_policy_expectations_in_aliases_keep_their_integrand_and_are_shared_by_reference(elaborate_text):
    old = '    ς = solve_{ς}(E_{φ}((φ - R)*w_d*D_{k_next}V[>]))  :: [id=foc]'
    assert RISKY_PORT.count(old) == 1
    alias = '    q = E_{φ}((φ - R)*w_d*D_{k_next}V[>])          :: [id=residual]\n'
    values = {'R': 1.03, 'φ_mean': 1.08, 'σ_φ': .2}
    stage = elaborate_text(RISKY_PORT.replace(old, alias + '    ς = solve_{ς}(q)   :: [id=foc]')).calibrate(values)
    residual = stage.builder.bwd[
        "policy", "residual:Aggregation:1"].denote()
    expectation = stage.builder.bwd[
        "policy", "residual:Expectation:1"].denote()
    assert expectation.inputs[0].identity == residual.outputs[0].identity
    # The snapshot owns the retired `E_[·] of residual` display alias. The
    # result remains attached to the authored residual occurrence.
    assert str(expectation.outputs[0].identity) == "policy.residual:Expectation:1:result"
    assert expectation.kernel.kind == "shock probability distribution"
    assert expectation.kernel.symbol == "P_φ"
    # the kernel denotes the declaration it integrates against, by reference
    # (critique F1): the law of `φ` as its own card holds it, read from the
    # fields of its identity and not from its spelling (AMD-SG-016 §3)
    [law] = expectation.kernel.denoted
    assert (law.identity.kind, law.identity.subjects) == ("distribution", ("φ",))
    assert isinstance(law.mathematical_type.carrier, S.ProbabilityMeasureSet)
    # the operand of an expectation follows its head directly (AMD-SG-034 critique, second round, K5)
    assert S.format_expression(expectation.outputs[0].expression, width=None).startswith(
        "(w_d, ς) ↦ E_{φ}[")
    # the residual's kernel reads the shock and the state by their names,
    # (φ − R) · w_d · D_{k_next}V[>](g(w_d, ς, φ)) (AMD-SG-034 §4 item 2)
    formula = residual.outputs[0].expression.body
    assert isinstance(formula, T.Mul) and isinstance(formula.left, T.Mul)
    assert isinstance(formula.left.left, T.Sub)
    assert S.variable_identity(formula.left.left.left).field == "φ"
    assert S.variable_identity(formula.left.right).field == "w_d"
    # the objective's expectation forms no piece (AMD-SG-034 §11 item 1), so
    # the residual's expectation stands alone, unmerged, on its own occurrence
    assert "policy:Expectation" not in list(stage.builder.bwd.primitives.list())
    assert [str(wire.identity) for wire in expectation.inputs] == [
        "policy.residual:Aggregation:1:result"]
    assert [str(wire.identity) for wire in expectation.outputs] == [
        "policy.residual:Expectation:1:result"]
    residual = kernel(stage, 'policy.residual:Aggregation:1').parameter_values
    assert compile_kernel(stage, 'policy.residual:Aggregation:1')(0., 2., .3, 1.2, 4., *residual) == pytest.approx(1.36)
    # two reads of q share its one occurrence; a separately authored occurrence is another expectation
    shared = elaborate_text(RISKY_PORT.replace(old, alias + '    ς = solve_{ς}(q + q)   :: [id=foc]')).calibrate(values)
    shared_aggregation = shared.builder.bwd[
        "policy", "foc:Aggregation"].denote()
    assert [str(wire.identity) for wire in shared_aggregation.inputs] == [
        "policy.residual:Expectation:1:result"]
    # the solve's Aggregation denotes the relation its line states, the set of
    # policies at which the residual vanishes, and its output holds the
    # residual line before the head: `r₁ = …`, then `ς = solve_{ς}(r₁)`
    assert isinstance(shared_aggregation.expression.body, T.Comprehension)
    residual_line, head = shared_aggregation.outputs[0].rules
    assert S.format_expression(head.statement, width=None) == "ς = solve_{ς}(r₁)"
    shared_formula = residual_line.statement.right
    assert isinstance(shared_formula, T.Add)
    assert shared_formula.left == shared_formula.right
    # The separately authored occurrence is another argument of the solve.
    twice = elaborate_text(RISKY_PORT.replace(
        old, alias + '    ς = solve_{ς}(q - E_{φ}((φ - R)*w_d*D_{k_next}V[>]))   :: [id=foc]')).calibrate(values)
    twice_aggregation = twice.builder.bwd[
        "policy", "foc:Aggregation"].denote()
    assert [str(wire.identity) for wire in twice_aggregation.inputs] == [
        "policy.residual:Expectation:1:result",
        "policy.foc:Expectation:1:result",
    ]
    twice_formula = twice_aggregation.outputs[0].rules[0].statement.right
    assert isinstance(twice_formula, T.Sub)
    assert twice_formula.left != twice_formula.right


def test_policy_node_cuts_divide_the_kernel_at_the_sub_builder_grain_and_compose_at_the_primitive_grain(elaborate_text):
    text = interior_cons().replace(':: [id=InvEuler]', ':: [id=InvEuler, !node]')
    stage = elaborate_text(text).calibrate({'ρ': 2.0})
    candidate = stage.builder.policy["InvEuler", "Aggregation"].compile_kernel()
    assert float(candidate(0.0, 3.0, 4.0, 2.0)) == 0.5
    grid = stage.builder.policy["endoggrid:Aggregation"]
    assert grid.kernel().splitlines() == [
        '𝐺 of policy, segment policy.endoggrid:Aggregation: 𝐺(c, a) = a + c', 'output m_d≻']
    resources = stage.builder.bwd.primitives["policy.endoggrid:Aggregation"].compile_kernel()
    assert float(resources(candidate(0.0, 3.0, 4.0, 2.0), 3.0)) == 3.5




def test_named_function_conditions_are_recorded_once_on_the_function(elaborate_text, text_of):
    """The conditions of a function's body are recorded once, on the function,
    with its parameters' declared sets as the operands' sets, and are not
    recorded again where the function is applied (AMD-SG-017 §4). An alias is
    followed to the function it names, and the condition stands on the
    definition that carries the body, in that definition's own letters."""
    from bellman.typing.typed_expressions import obligation_entry
    source = text_of('cons').replace('𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)',
        'base(x : ℝ₊₊) := x^(1-ρ)/(1-ρ)\n𝑢 := base')
    stage = elaborate_text(source)
    # the node stands as a third entry, so that the piece holding it is
    # found (second round, R2); the place and the condition key it here
    said = [tuple(obligation_entry(entry) for entry in o.entries[:2])
            for o in stage.obligations() if o.condition == 'arithmetic-definedness']
    assert ('cons:function:base', '¬(1 - ρ = 0)') in said
    assert all(entries[0] == 'cons:function:base' for entries in said)
    # the application carries the body's conditions to its argument through the
    # inclusion, and repeats none of them on the aggregation's card
    face = card(stage, 'cntn_to_dcsn:Aggregation')
    assert '1 - ρ = 0' not in face and 'x^(1 - ρ)' not in face


def test_joint_control_spellings_preserve_the_objective_and_order(elaborate_text):
    variants = (
        NAMED_CONTROLS,
        NAMED_CONTROLS.replace('c : ℝ @ !ctrl, l : ℝ @ !ctrl', '(c,l) : !ctrl @ ℝ × ℝ'),
        NAMED_CONTROLS.replace('id=choice', 'id=choice, !node'),
        NAMED_CONTROLS.replace('argmax_{c,l}(-c^2-4*l^2+V[>])',
                              'argmax_{cp,lp}(-cp^2-4*lp^2+V[>])'),
    )
    for source in variants:
        stage = elaborate_text(source).calibrate({})
        # the third spelling marks the line a node, so the Argmax stands
        # inside a sub-builder; at the primitive grain its name is the same
        argmax = stage.builder.bwd.primitives["policy.choice:Argmax"]
        candidates = argmax.denote().image
        # Separate component projections have no derived joint relation until
        # the tuple-output construction of AMD-SG-030.
        assert "UNRESOLVED" in str(candidates)
        evaluation = stage.builder.bwd.primitives["policy:Evaluation"].denote()
        assert tuple(output.identity.field for output in evaluation.outputs) == ('c', 'l')
        assert tuple(output.name for output in evaluation.outputs) == ('𝑐(x_d)', '𝑙(x_d)')
        G = compile_kernel(stage, 'policy.choice:Aggregation')
        assert float(G(10, 8, 1, 2)) == -7
        for handle in (stage.builder.bwd, stage.builder.bwd.sub_builders,
                       stage.builder.bwd.primitives):
            handle.graph
    with pytest.raises(ConstructionError, match='different order') as refused:
        elaborate_text(NAMED_CONTROLS.replace('argmax_{c,l}', 'argmax_{l,c}'))
    assert refused.value.address == 'policy.choice'


def test_markov_matrix_rows_retain_distinct_expression_scopes(elaborate_text):
    stage = elaborate_text(HAFISCAL)
    stage.initial.backward.graph
    stage.builder.bwd.graph
    # the categorical row Π[z_prev] is the family of z, and the forward measures
    # are extended by it (AMD-SG-010 §3)
    extension = next(box for box in operators_of(stage, 'forward')
                     if box.name == 'arvl_to_dcsn:DistributionExtension:z')
    assert 'Categorical' in kernel(stage, extension)


def test_identity_node_chains_do_not_introduce_external_function_inputs(elaborate_text):
    stage = elaborate_text(two_nodes(backward=(
        "    N1 = E_{y,z}(V[>]) :: [id=first, !node]\n"
        "    N2 = N1 :: [id=second, !node]\n"
        "    V = N2\n")))
    for handle in (stage.builder.bwd.sub_builders, stage.builder.bwd.primitives):
        # no input of either grain is one that no builder supplies (AMD-SG-012 §5)
        assert [text for _, text in handle.signature().inputs if 'supplied by no builder' in text] == []
    primitive = stage.builder.bwd.primitives
    aggregation = next(box for box in primitive.graph.boxes if box.name == 'cntn_to_dcsn:Aggregation')
    assert kernel(stage, aggregation).splitlines()[0] == (
        '𝐺 of cntn_to_dcsn: 𝐺(N2, k_d, c) = N2')


def test_elaborate_when_the_package_is_not_installed(monkeypatch):
    """A checkout imported by path, with no distribution metadata in the
    interpreter, still elaborates: the provenance records the version of the
    pyproject.toml above the package, the one rule of `package_version`
    (structure review C3; decision S9 of the cleanup), and no longer the word
    `unreleased`."""
    from importlib import metadata
    from bellman.native import provenance

    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(provenance.metadata, "version", missing)
    assert provenance.grammar_versions()["package"] == provenance.package_version() != "unreleased"
    record = load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl")
    assert repr(elaborate_stage(record)) == "ElaboratedStage('cons', symbolic)"


def test_every_obligation_records_a_place_that_resolves(elaborate_text, buffer_stock):
    """An obligation names the place it stands at by an identity of the
    definitions table or by the address of an authored line, and by no ordinal
    of an item in the file (AMD-SG-014 §3)."""
    stage = elaborate_text(two_nodes(declarations="y ~ Density(0,1)\nz : ℝ\nz ~ N(0,1)\n"), "external.bl")
    external = [item for item in stage.obligations()
                if item.condition == "external-callable-signature-and-provider"]
    assert [item.entries for item in external] == [("external:Density", "two_nodes:distribution:y")]
    for version in (stage, buffer_stock):
        for item in version.obligations():
            place = str(item.entries[0]) if item.entries else ""
            if place.startswith(f"{version.name}:"):
                assert place in version.definitions or place in version.fields(), (
                    version.name, item.condition, place)

    from conftest import bundles
    local = elaborate_text(bundles(), "bundles.bl")
    defined = {definition.identity.field for definition in local.definitions.values()
               if definition.kind in ("function", "function_alias", "correspondence")}
    held = [(item.condition, item.entries) for item in local.obligations()]
    assert len(held) == len(set(held))
    assert not [item for item in local.obligations()
                if item.condition == "external-callable-signature-and-provider"
                and item.entries[0].field in defined]


def test_the_documents_carry_the_words_and_the_passages_of_the_amendments():
    """The standing document checks of AMD-SG-013 §8 items 4 and 5, kept here
    when its acceptance file was retired (the second layer of the tests,
    `packages/bellman/README.md` §8). The words AMD-SG-014 retires are
    searched in its own acceptance file."""
    pages = STAGE_OBJECT_PAGES + ("docs/Bellman-Sym/01-stage.md",
                                  "docs/overview/05-semantics.md")
    wiki = ("docs/wiki/semgraph.md", "docs/wiki/builder.md", "docs/wiki/operator.md",
            "docs/wiki/elaborated_stage.md")
    calculus = ("docs/bellman-calculus/02-Illustrative example.md",
                "docs/bellman-calculus/03-Stages and perches.md",
                "docs/bellman-calculus/04-fields, functions and types.md",
                "docs/bellman-calculus/05-Operators and builders.md")
    symbols = "docs/Bellman-Sym/reference/symbols-conventions.md"
    root = Path(__file__).resolve().parents[3]

    for path in pages + wiki + ("AGENTS.md",):
        text = (root / path).read_text(encoding="utf-8")
        for line in text.splitlines():
            assert not line.startswith(("parameters  ", "defined in  ")), (path, line)
        for retired in ("parameter of a builder", "parameterised builder", "parameter of this box",
                        "parameter of the builder", "as parameters", "in Γ("):
            assert retired not in text, (path, retired)
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert ("`signature()` answers one record with two parts, `inputs` and `outputs`; a decision "
            "builder's or a decision push-forward's is the signature of the operator at a policy") in agents
    assert ("the policy is typed once, on the policy builder's output; a decision builder or a "
            "decision push-forward is the operator at a policy") in agents
    stages = (root / calculus[1]).read_text(encoding="utf-8")
    assert ("the family $\\pi \\mapsto \\mathbb T_{\\succ,\\pi}$ is a map "
            "$\\Pi_\\Gamma \\to [\\mathsf V_\\succ \\to \\mathsf V_\\sim]$") in stages
    assert ("the family $\\pi \\mapsto \\mathbb M_{\\succ,\\pi}$ is a map "
            "$\\Pi_\\Gamma \\to [\\mathsf M_\\sim \\to \\mathsf M_\\succ]$") in stages
    operators = (root / calculus[3]).read_text(encoding="utf-8")
    assert "**The builder at a policy and the policy layer.**" in operators
    assert ("the decision builder is the operator at a policy, its signature the inputs and outputs "
            "of $\\mathbb T_{\\succ,\\pi}$") in operators
    for path in (calculus[1], calculus[3]):
        text = (root / path).read_text(encoding="utf-8")
        for retired in (r"\mathbb T_{\succ,\cdot}", r"\mathbb M_{\succ,\cdot}"):
            assert retired not in text, (path, retired)
    assert "The policy is written as a subscript" in (root / symbols).read_text(encoding="utf-8")
    # a roman letter applied to arguments is a function written in the wrong
    # type (AMD-SG-012 §2)
    for path in calculus + (symbols,):
        text = (root / path).read_text(encoding="utf-8")
        for form in (r"\mathrm v(", r"\mathrm v_\succ(", r"\mathrm g(", r"\mathrm G(",
                     r"\mathrm r(", r"\mathrm u("):
            assert form not in text, (path, form)




# --- the standing claims of the retired acceptance file of AMD-SG-027 --------

def test_a_denotation_answer_is_detached_and_its_wires_are_frozen(
        elaborate_text, text_of):
    import gc
    import weakref

    stage = elaborate_text(text_of("cons"), "detached.bl")
    reference = weakref.ref(stage)
    answer = stage.builder.bwd["cntn_to_dcsn"].denote()
    inputs, outputs, pieces = answer.inputs, answer.outputs, answer.pieces
    wire = inputs[0]
    original_hash = hash(wire)
    del stage
    gc.collect()
    assert reference() is None
    assert (answer.inputs, answer.outputs, answer.pieces) == (inputs, outputs, pieces)
    with pytest.raises(FrozenInstanceError):
        wire.identity = outputs[0].identity
    assert hash(wire) == original_hash


def test_documentation_changes_neither_input_nor_rule_of_the_two_input_identification(
        cons, elaborate_text, text_of, explicit_cons_text, cons_explicit):
    cons = cons_explicit
    source = explicit_cons_text
    line = "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality, !doc]\n"
    assert source.count(line) == 1
    without = elaborate_text(source.replace(line, ""), "without_documentation.bl")
    documented = cons.builder.bwd["policy", "cons_choice:Pullback"].denote()
    undocumented = without.builder.bwd["policy", "cons_choice:Pullback"].denote()
    # the identification reads the candidate 𝑐≻ and the coordinate map 𝑚_d≻
    assert len(documented.inputs) == 2
    assert documented.inputs == undocumented.inputs
    # the rule the identification declares, the grid relation on its image,
    # is the same with or without the documentary line; the feasibility of
    # the returned policies is by the correspondence the line declares and by
    # the law's image without it (AMD-SG-034 §10 item 4)
    assert documented.outputs[0].rules == undocumented.outputs[0].rules
    assert len(documented.outputs[0].rules) == 1
    assert (S.format_expression(documented.outputs[0].mathematical_type.carrier, width=None)
            != S.format_expression(undocumented.outputs[0].mathematical_type.carrier, width=None))


def test_an_unsupported_function_alias_is_retained_as_textual(elaborate_text, text_of, explicit_cons_text):
    source = explicit_cons_text
    written = "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)"
    assert source.count(written) == 1
    source = source.replace(written, "𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)")
    stage = elaborate_text(source, "function_alias.bl")
    answer = stage.definitions.denote("cons:function:𝑑𝑢𝑖𝑛𝑣")
    [denoted] = answer.denoted
    assert denoted.rule.endswith("[textual]")


def test_a_signature_wire_is_the_public_identity_and_displayed_type_pair(cons):
    [wire] = cons.builder.bwd["cntn_to_dcsn"].signature().inputs
    identity, displayed_type = wire
    assert identity == wire.identity
    assert displayed_type == str(wire.mathematical_type)
    assert wire == (identity, displayed_type)
    assert (identity, displayed_type) == wire
    assert hash(wire) == hash((identity, displayed_type))


# --- the standing claims of the retired acceptance file of AMD-SG-028 --------



def test_a_configured_method_card_preserves_an_authored_option_with_a_colliding_setting_name(
        cons, cons_configured):
    """The `Options` row of a keyword argument prints the configured value
    of the setting the argument names, and not the value of a setting whose
    name is the keyword's own; the `Method` row prints the grid as the
    addition writes it, whatever the settings are named."""
    configured = copy_native(cons).methodize({
        "text": "@methods: cons\npoints : ℕ\ntolerance : ℝ₊₊\npolicy.method : !vfi(n_c=points, tol=tolerance)\n",
        "origin": "cons.methods.bl",
    }).configure({"n_c": 17, "points": 8000, "tol": 3, "tolerance": 1e-06})
    card = str(configured.builder.policy.denote())
    assert "n_c = 8000" in card and "tol = 1e-06" in card
    assert "n_c = 17" not in card and "tol = 3" not in card
    gridded = copy_native(cons_configured).configure({"orders": 17})
    card = str(gridded.builder.bwd["cntn_to_dcsn"].denote())
    assert "!Cartesian(m_d=(m_min, m_max, n_m))" in card and "orders = 17" not in card


# --- the standing claims of the retired acceptance file of AMD-SG-014 --------
# AMD-SG-015 retires `tests/cat/test_amd_sg_014.py` as the lean rule requires.
# Its printed cards are carried by the snapshot; the claims below are about the
# public queries and the documents, so they stand here.

_ROOT_014 = Path(__file__).resolve().parents[3]
# the pages whose listings the generator prints from the package, and the
# overview that describes the same object in words
_PAGES_014 = STAGE_OBJECT_PAGES + ("docs/overview/05-semantics.md",)
_WIKI_014 = tuple(f"docs/wiki/{name}.md" for name in
                  ("semgraph", "builder", "operator", "elaborated_stage", "perch"))
_SOURCE_014 = tuple(sorted(path.relative_to(_ROOT_014).as_posix()
                           for path in (_ROOT_014 / "packages/bellman/bellman").rglob("*.py")))
# AMD-SG-014 §4 retired the label `read at`, the phrase "selection condition"
# and the phrase "the argmax binder of" from the printed surface. The bare word
# "binder" returns with AMD-SG-015 §4.6, where the listing states that a
# correspondence's range is read from the binder that applies it, so the word
# itself is not retired and only the phrase is checked in the source. The
# AMD-SG-025 settings query now requires `read at` as a structured row key;
# AMD-SG-014's prohibition still applies to prose and rendered labels, not to
# that source-level key.
_RETIRED_WORDS_014 = ("`read at`", "selection condition", "the argmax binder of")
_RETIRED_IN_SOURCE_014 = ("selection condition", "the argmax binder of")
_RETIRED_LABELS_014 = (re.compile(r"^read at +\S"), re.compile(r"^signature +\(.*\) -> \("))


def _read_text_014(path):
    return (_ROOT_014 / path).read_text(encoding="utf-8")


def test_a_declared_description_is_kept_and_an_obligation_names_the_function(buffer_stock, cons):
    assert buffer_stock.definitions.denote(
        "buffer_stock:parameter:β").describes == ("discount factor",)
    # a derived parameter keeps its description as a declared one does
    assert buffer_stock.definitions.denote(
        "buffer_stock:derived:μ_ξ").describes == (
            "log-mean of the positive transitory draw, at which E[ξ] = 1",)
    selected = stage_from_text(SELECTED_LAW, "selected_law.bl")
    assert selected.definitions.denote(
        "key_selection_reads:distribution:s").describes == (
            "a two-point state; an admitted family, so that the forward view is constructed",)
    assert selected.definitions.denote(
        "key_selection_reads:distribution:θ").describes == (
            "a shock whose law reads η directly and s through a key selection",)
    # the obligation records the identity of the function whose inverse is
    # taken, where it recorded the ordinal of the item in the file
    inverse = [item for item in buffer_stock.obligations() if item.condition == "inverse-function-domain"]
    assert [item.entries[0] for item in inverse] == ["buffer_stock:function:𝑑𝑢𝑖𝑛𝑣"]
    assert all(place in buffer_stock.definitions or place in buffer_stock.fields()
               for place in (str(item.entries[0]) for item in buffer_stock.obligations() if item.entries)
               if place.startswith(f"{buffer_stock.name}:"))
    assert cons.definitions.denote("cons:parameter:ρ").describes == ()
    assert cons.definitions.denote("cntn_to_dcsn.value").describes == ()






def test_the_retired_words_stand_nowhere_and_the_rows_read_as_the_amendments_wrote_them():
    documents = {path: _read_text_014(path) for path in _PAGES_014 + _WIKI_014}
    source = {path: _read_text_014(path) for path in _SOURCE_014}
    for path, text in documents.items():
        for retired in _RETIRED_WORDS_014:
            assert retired not in text, (path, retired)
    for path, text in source.items():
        for retired in _RETIRED_IN_SOURCE_014:
            assert retired not in text, (path, retired)
    for path, text in (documents | source).items():
        for line in text.splitlines():
            for label in _RETIRED_LABELS_014:
                assert not label.match(line), (path, line)
    agents = _read_text_014("AGENTS.md")
    assert ("Construct this in the native semgraph: the parameters and the policy are references in a "
            "box's data and are drawn as no wire, and the renderer draws what the graph holds.") in agents


# --- standing claims that the snapshot cannot carry --------------------------
# The test-only pass of 18 September 2026 brings the suite to the three layers
# of `packages/bellman/README.md` §8: `tests/cat/test_amd_sg_015.py` is the
# one acceptance file, and those of AMD-SG-006 to AMD-SG-010 are retired. The
# claims below read the public operations on stages the corpus does not hold,
# or numbers and pages no recording can carry, so they stand here.
# The report of the pass, kept in the project's internal records, gives one
# row per retired test.

_ROOT = Path(__file__).resolve().parents[3]
_NOPORT = _ROOT / "applications/portfolio-choice/declaration/stages/noport/noport.bl"
# relative tolerance of the comparisons with closed forms (AMD-SG-009 §6):
# every value is a few elementary operations from its formula
RELATIVE = 1e-12


def inside(graph, name):
    """The boxes inside the bubble `name` of a graph, by name. `graph` is the
    handle of AMD-SG-010 §4 or the DisCoPy object it names."""
    boxes = getattr(graph, "graph", graph).boxes
    return {box.name: box for box in next(box for box in boxes if box.name == name).arg.boxes}


def names(sorts):
    return tuple(identity.field for sort in sorts for identity in sort.coordinates)


def test_header_spellings_chain_conditioning_and_compound_bernoulli_remain_public_behaviour(
        cons, elaborate_text, text_of):
    written = "(V[>] : [-inf, inf) @ !vlu, c) : !cntn ->"
    no_perch = "(V[>] : [-inf, inf) @ !vlu, c) ->"
    variants = (
        written.replace(", c)", ", c : !cntn)"),
        written.replace(", c)", ", c : !dcsn)"),
        no_perch,
        no_perch.replace(", c)", ", c : !cntn)"),
        no_perch.replace(", c)", ", c : !dcsn)"),
    )
    source = text_of("cons")
    assert source.count(written) == 1
    for variant in variants:
        changed = elaborate_text(source.replace(written, variant), "cons.bl")
        assert changed.dcsn.builder.bwd.signature() == cons.dcsn.builder.bwd.signature()

    chains = (
        (f"{PRELIMINARY}/ma-stachurski-toda-2020/cons.bl",
         "cons:distribution:z", "Z → probability measure on Z"),
        (f"{PRELIMINARY}/benhabib-bisin-zhu-2011/generation.bl",
         "generation:distribution:z_q", "Rstate → probability measure on Rstate × Ystate"),
        (f"{PRELIMINARY}/bloom-2009/unit.bl",
         "unit:distribution:s", "Sigma → probability measure on Sigma"),
    )
    for path, identity, expected in chains:
        stage = elaborate_text((_ROOT / path).read_text(encoding="utf-8"), path)
        [distribution] = stage.definitions.denote(identity).denoted
        assert str(distribution.mathematical_type) == expected

    bernoulli = elaborate_text(two_nodes(
        declarations="χ : [0,1]\ny ~ Bernoulli(1 - χ)\nz : ℝ\nz ~ N(0,1)\n"))
    weights = [item.explanation for item in bernoulli.obligations()
               if item.condition == "distribution-weights-are-a-probability-vector"]
    assert len(weights) == 1
    assert ("gives its subject the value 1 with probability 1 - χ and the value 0 with probability "
            "1 - (1 - χ)") in weights[0]


def test_relations_types_and_definitions_keep_non_snapshot_semantics(
        cons, cons_savings_iid, cons_methodized, elaborate_text, text_of):
    relation_path = f"{PRELIMINARY}/rendahl-2015/growth.bl"
    relation_stage = elaborate_text((_ROOT / relation_path).read_text(encoding="utf-8"), relation_path)
    retained = [item for item in relation_stage.obligations() if item.condition == "retained-relation"]
    assert [str(item.entries[0]) for item in retained] == ["cntn_to_dcsn.slackness"]
    assert "no operator of the builder realises it" in retained[0].explanation

    answer = cons.dcsn.builder.bwd.signature().inputs[0].mathematical_type
    bound = cons_methodized.dcsn.builder.bwd.signature().inputs[0].mathematical_type
    assert answer == bound and hash(answer) == hash(bound)
    with pytest.raises(AttributeError):
        answer.carrier = None

    original = cons.definitions.denote("cons:function:𝑢").denoted[0].expression
    renamed = elaborate_text(text_of("cons").replace(
        "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)", "𝑢(d : ℝ₊₊) := d^(1-ρ)/(1-ρ)"))
    assert renamed.definitions.denote("cons:function:𝑢").denoted[0].expression == original

    unspecified = elaborate_text(text_of("cons").replace("c^(-ρ)", "unknown(c)"))
    marginal = unspecified.definitions.denote("cons:function:𝑑𝑢").denoted[0]
    assert "UNRESOLVED" in str(marginal.mathematical_type) and "ℝ₊₊" in str(marginal.mathematical_type)

    unsupported = elaborate_text(text_of("cons").replace("c^(-ρ)", "log(c,c)"))
    marginal = unsupported.definitions.denote("cons:function:𝑑𝑢").denoted[0]
    assert "UNRESOLVED" in str(marginal.expression)
    assert "one argument for log" in str(marginal.expression)

    family = "Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_y, σ_y)))"
    finite = elaborate_text(text_of("cons_savings_iid").replace(
        family, "Mixture((0.25, 0), (0.75, 1))"))
    definition = finite.definitions.denote(
        "cons_savings_iid:distribution:y").denoted[0]
    expectation = finite.builder.bwd[
        "dcsn_to_arvl", "value:Expectation:1"].denote()
    # the declared law is held as the file writes it, the rule applied to the
    # written pairs with a numeric atom left as the number the rule
    # interprets (AMD-SG-034 §4 item 7); the expectation's kernel denotes
    # that declaration by reference, the one place the law is written
    # (critique F1), and constructs no measure from its atoms
    declared = definition.expression
    assert isinstance(declared, S.Apply) and S.format_expression(declared.function) == "Mixture"
    assert len(declared.args) == 2 and all(isinstance(pair, T.Tuple) for pair in declared.args)
    weights, atoms = zip(*((pair.items[0], pair.items[1]) for pair in declared.args))
    assert tuple(S.format_expression(weight) for weight in weights) == ("0.25", "0.75")
    assert tuple(S.format_expression(atom) for atom in atoms) == ("0", "1")
    [law] = expectation.kernel.denoted
    assert str(law.identity) == "cons_savings_iid:distribution:y"
    assert law.expression == declared
    assert "measure on" not in S.format_expression(law.expression, width=None)
    held = expectation.outputs[0].expression
    assert isinstance(held, S.Lambda) and isinstance(held.body, T.Operator) and held.body.head == "E"

    unsupported_law = elaborate_text(text_of("cons_savings_iid").replace(
        family, "Mixture((0.5, -1), (0.5, 1))"))
    support = [item for item in unsupported_law.obligations() if item.condition == "law-support"]
    assert [str(item.entries[0]) for item in support] == ["cons_savings_iid:shck:y"]
    assert "gives probability only to values in the declared shock set" in support[0].explanation


def test_a_grid_typed_in_a_methods_file_names_the_settings_configure_binds(elaborate_text):
    """A grid is the grid component of a place, `<place>.grid : !Cartesian(...)`,
    its kind the word and its factors beside it; the names a factor's bounds
    and count write are settings `configure` binds, and the kind names none
    (specification 0.7 D5)."""
    stage = elaborate_text(_NOPORT.read_text(encoding="utf-8"),
                           "applications/portfolio-choice/declaration/stages/noport/noport.bl")
    methodized = methodize(stage, {
        "text": ("@methods: noport\n"
                 "wealth_min : ℝ\nwealth_max : ℝ\nwealth_points : ℕ\n"
                 "cntn_to_dcsn.evaluate.method : !Linear\n"
                 'cntn_to_dcsn.evaluate.handler : "factory"\n'
                 "cntn_to_dcsn.evaluate.grid : !Cartesian(k_d=(wealth_min, wealth_max, wealth_points))\n"),
        "origin": "noport.methods.bl"})
    held = methodized.methods["cntn_to_dcsn.evaluate"]
    assert str(held) == '!Linear   !Cartesian(k_d=(wealth_min, wealth_max, wealth_points))   "factory"'
    assert (held.word, held.handler) == ("!Linear", "factory")
    # a keyword the row does not list is admitted and kept for the handler
    extra = methodize(elaborate_text(_NOPORT.read_text(encoding="utf-8"), "noport.bl"), {
        "text": '@methods: noport\ncntn_to_dcsn.evaluate.method : !Linear(vendor_flag="on")\n',
        "origin": "noport.methods.bl"})
    assert str(extra.methods["cntn_to_dcsn.evaluate"]) == '!Linear(vendor_flag="on")'
    assert "vendor_flag" not in method_types["!Linear"].keywords
    assert symbols(methodized)["settings"] == ("wealth_min", "wealth_max", "wealth_points")
    with pytest.raises(ValueError, match="wealth_min"):
        configure(methodized, {})
    configured = configure(methodized, {"wealth_points": 3, "wealth_min": 0.5, "wealth_max": 2.0})
    assert configured.bindings.settings["wealth_points"] == 3
    assert [str(configured.settings[name]) for name in ("wealth_min", "wealth_points")] == [
        "wealth_min = 0.5 : ℝ, read at cntn_to_dcsn.evaluate by !Linear for its grid !Cartesian",
        "wealth_points = 3 : ℕ, read at cntn_to_dcsn.evaluate by !Linear for its grid !Cartesian",
    ]


def test_public_method_types_and_stage_places_retain_their_contract(cons):
    tags = tuple(method_types)
    assert {"!Linear", "!root-find", "!vfi"} <= set(tags)
    assert not {"!linear", "!rootfind", "!value-iteration"}.intersection(tags)
    for tag, rule in method_types.items():
        assert tag.startswith("!")
        assert tuple(rule) == ("admits", "keywords")
        assert dict(rule) == {"admits": rule.admits, "keywords": rule.keywords}
        assert rule.admits and isinstance(hash(rule), int)
        assert all(repr(keyword) == str(keyword) for keyword in rule.keywords.values())
        assert all(len(line) <= 78 for line in str(rule).splitlines())
        with pytest.raises((AttributeError, FrozenInstanceError, TypeError)):
            rule.admits = ()
        with pytest.raises(TypeError):
            rule.keywords["other"] = object()
    assert not hasattr(bellman, "MethodOption")

    # the hyphenated tag is read from the underscore spelling of a stage file
    quadrature = method_types["!gauss_hermite"]
    assert quadrature is method_types["!gauss-hermite"]
    assert quadrature.keywords["n_<shock>"].kind == "positive integer"
    assert quadrature.keywords["n_<shock>"].required is True
    assert all(word in str(quadrature) for word in
               ("METHOD !gauss-hermite", "\nAdmits\n", "\nKeywords\n", "\nGrid\n"))
    assert "requires" not in str(quadrature) and "claim" not in str(quadrature)

    rows = cons.places()
    assert rows and {"address", "kind"} == set(rows[0])
    assert any(row["address"] == "policy" and row["kind"] == "builder" for row in rows)
    assert any(row["address"] == "cntn_to_dcsn.value" for row in rows)
    with pytest.raises(TypeError):
        rows[0]["kind"] = "changed"


def test_a_quadrature_adds_no_condition_and_a_solution_method_adds_its_own(cons, port):
    """A quadrature typed at an expectation adds no condition to the stage; a
    solution method typed on a builder adds the condition its row of the
    catalogue names, `egm-eligibility` for `!egm`, and nothing else."""
    egm = copy_native(cons).methodize({
        "text": '@methods: cons\npolicy.method : !egm\npolicy.handler : "test:egm"\n',
        "origin": "cons.methods.bl"})
    quadrature = copy_native(port).methodize({
        "text": "@methods: port\nnodes : ℕ\nE_Ψ_θ.method : !gauss_hermite(n_Ψ=nodes, n_θ=nodes)\n",
        "origin": "port.methods.bl"})
    assert [item.condition for item in egm.obligations()] == [
        *[item.condition for item in cons.obligations()], "egm-eligibility"]
    assert quadrature.obligations() == port.obligations()
    assert quadrature.configure({"settings": {"nodes": 7}})


def test_typed_configuration_lists_readers_and_unread_settings(cons):
    source = {"text": ("@methods: cons\n"
                       "n_m : ℕ\nm_min : ℝ₊\nm_max : ℝ₊\n"
                       "cntn_to_dcsn.evaluate.method : !Linear\n"
                       "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))\n"),
              "origin": "cons.methods.bl"}
    specified = copy_native(cons).methodize(source).configure({"settings": {
        "n_m": 8, "m_min": 0.1, "m_max": 10.0, "unused": 99,
    }})
    rows = specified.settings.list()
    assert [row["name"] for row in rows] == ["n_m", "m_min", "m_max", "unused"]
    for row in rows[:3]:
        assert (row["read at"], row["by"], row["grid"]) == (
            "cntn_to_dcsn.evaluate", "!Linear", "!Cartesian")
    assert (rows[3]["read at"], rows[3]["by"], rows[3]["grid"]) == ("", "", "")
    assert all(name in str(specified) for name in ("n_m", "m_min", "m_max", "unused"))


def test_method_choices_leave_graphs_types_and_equations_unchanged(cons):
    """A solution method typed on a builder with no rows of its own and a
    representation typed at an Evaluation change no graph, no type and no
    equation: `!egm` on the policy builder with its savings grid, then `!vfi`
    on the backward decision builder, each beside a representation of what
    the decision builder's Evaluation stores; the obligations gain the
    method's own condition and the representation's `evaluation-domain`, that
    it is evaluated where its nodes support the function (AMD-MT-003 build
    contract §§3, 4), alone."""
    for target, solver, representation in (("policy", "egm", "Linear"), ("cntn_to_dcsn", "vfi", "pchip")):
        grid = (
            "a_min : ℝ₊\na_max : ℝ₊\nn_a : ℕ\npolicy.grid : !Cartesian(a=(a_min, a_max, n_a))\n"
            if solver == "egm" else ""
        )
        version = copy_native(cons).methodize({
            "text": (f"@methods: cons\n{target}.method : !{solver}\n{grid}"
                     "m_min : ℝ₊\nm_max : ℝ₊\nn_m : ℕ\n"
                     f"cntn_to_dcsn.evaluate.method : !{representation}\n"
                     "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))\n"),
            "origin": "cons.methods.bl",
        }).configure({"settings": {"n_m": 8, "m_min": 0.1, "m_max": 10.0,
                                   "n_a": 8, "a_min": 0.1, "a_max": 10.0}})
        assert graphs_differ(version, cons) == []
        for kind in ("Pullback", "Aggregation", "Evaluation"):
            before = cons.builder.bwd["cntn_to_dcsn", kind].denote()
            after = version.builder.bwd["cntn_to_dcsn", kind].denote()
            assert after.expression == before.expression
            assert tuple(w.mathematical_type for w in after.inputs + after.outputs) == tuple(
                w.mathematical_type for w in before.inputs + before.outputs)
        assert [item.condition for item in version.obligations()] == [
            *[item.condition for item in cons.obligations()],
            *(["egm-eligibility"] if solver == "egm" else []), "evaluation-domain"]


def test_the_bindings_return_the_stage_they_bind_with_its_graphs_and_table(cons, cons_sources):
    """Each binding verb returns the stage it is called on, and one binding
    changes per call, against the bindings held before it. `calibrate` and
    `configure` keep the graphs and the definitions table as the objects
    held before the call; `methodize` elaborates the stage file's tree with
    the addition anew and writes the records over the stage's, the declared
    graphs equal to those held before (specification 0.6 decision 1 and R4;
    specification 0.7 §6)."""
    stage = copy_native(cons)
    views = ("initial.backward", "initial.forward", "builder.bwd", "builder.fwd")

    def held():
        return {"calibration": stage.bindings.calibration, "settings": stage.bindings.settings,
                "methods": stage.provenance.get("additions")}

    for verb, source, name in ((methodize, cons_sources["methods"], "methods"),
                               (configure, cons_sources["settings"], "settings"),
                               (calibrate, cons_sources["calibration"], "calibration")):
        graphs = [attrgetter(view)(stage).graph for view in views]
        records = tuple(stage.definitions.values())
        before = held()
        assert verb(stage, source) is stage
        if name == "methods":
            assert graphs_differ(declared_version(stage), cons) == []
        else:
            assert all(attrgetter(view)(stage).graph is graph for view, graph in zip(views, graphs))
            assert all(a is b for a, b in zip(stage.definitions.values(), records, strict=True))
        after = held()
        assert [key for key in before if after[key] != before[key]] == [name]


def test_the_standard_pickle_reads_back_a_version_and_a_trellis_equal_before_and_after_a_query(registry):
    """`pickle.dumps` and `pickle.loads` of the standard library write and read
    back a stage version, before and after it has answered queries, and a
    trellis, before and after one of its stages has answered a query. What is
    read back equals what was written: a version by the equality of stages, a
    trellis as a dictionary, and so at every position by the equality of the
    stage objects there. A version read back holds none of the answers the
    written one kept, and it answers a query afresh with the same answer (the
    review of the stage object under repeated use, §6, decision 2)."""
    import pickle
    version = stage_from_text(corpus_text("cons"), "pickled.bl")
    assert pickle.loads(pickle.dumps(version)) == version
    listing = str(version.builder.bwd.primitives.list())
    version.obligations()
    back = pickle.loads(pickle.dumps(version))
    assert back == version and "_kept" not in vars(back)
    assert str(back.builder.bwd.primitives.list()) == listing
    trellis = assemble_trellis(registry, "spec.yml")
    assert pickle.loads(pickle.dumps(trellis)) == trellis
    trellis["periods"][1]["stages"]["two_nodes"].obligations()
    assert pickle.loads(pickle.dumps(trellis)) == trellis


# a complete calibration of each of the eight stages the snapshot records, for the
# answers a bound version carries: the four of CORPUS_CALIBRATIONS, the first of the
# smooth-ambiguity stage, and values inside the declared sets for the other three, the
# tenure stage's from the durables calibration and the retiree's of the shock-branching tests
CARRYING_VALUES = {**CORPUS_CALIBRATIONS, "cons_obs": {"ρ": 6.0}, "sa_savings": SA_SAVINGS_CALIBRATIONS[0],
                   "tenure": {"R": 1.045, "R_H": 1.0, "δ": 0.0, "ρ_z": 0.82, "σ_z": 0.11, "Y": 1.0, "y_R": 0.0},
                   "retiree_death": {"β": 0.95, "η": 0.5, "π_o": 0.9, "P_y": 0.5, "y_grid": 1.0, "ρ_θ0": 0.9,
                                     "ρ_θ1": 0.8, "θ_e": 1.0}}


def asked(version):
    """Ask `version` for every graph at every grain, the kernel of every
    primitive operator by its name, the primitive operators and the card of
    every builder, its conditions and its diagnostics, so that it keeps those
    answers."""
    for level, direction, grain in SELECTIONS:
        try:
            graph_of(version, level, direction, grain)
        except NotConstructed:
            continue
    for box in operators_of(version):
        kernel(version, box.name)
    for graph in (version.builder.bwd, version.builder.fwd):
        try:
            builders = graph.graph.boxes
        except NotConstructed:
            continue
        for box in builders:
            graph[box.name].primitives.list()
            str(graph[box.name].denote())
    version.obligations()
    version.diagnostics()


# the bindings of the equality test: `calibrate` on each of the eight stages, and
# `methodize` and `configure` on the consumption stage, whose sources the corpus holds
CARRYING_BINDINGS = ([(name, "calibrate", values) for name, values in CARRYING_VALUES.items()]
                     + [("cons", "methodize", CORPUS_METHODS["cons"]), ("cons", "configure", CORPUS_SETTINGS["cons"])])




def test_a_bound_version_carries_answers_that_hold_its_own_boxes_and_wires_and_none_of_its_argument():
    """The answers a version `calibrate` returns carries refer to the objects
    of that version: its wire table names it and holds its stored blocks; the
    builder grain of each builders graph is its stored graph; the
    construction table holds its definition records; every box the places
    list is a box of its graph at that grain, and every box but the wiring
    inside a carried bubble a box of its graph at the bubble's grain; the
    initial diagrams at the finer grains hold its stored statement boxes, as
    many as the argument's held of its own. No object an answer holds is an
    object of the argument, whose records and answers are left as they were
    (the review of the stage object under repeated use, §6, decision 1)."""
    import gc
    import types
    from discopy.frobenius import Bubble
    from bellman.native.labels import is_wiring
    from bellman.native.versions import stored
    version = stage_from_text(corpus_text("tenure"), "tenure.bl")
    asked(version)
    # `calibrate` binds the stage it is called on (specification 0.6 decision
    # 1 and R4), so the version made from it is the copy `copy_native` makes
    bound = copy_native(version.calibrate(CARRYING_VALUES["tenure"]))
    kept = vars(bound)["_kept"]
    rendering = kept["wire_table"]
    assert rendering.stage is bound
    blocks = [box for direction in ("backward", "forward")
              for box in getattr(stored(bound, "initial"), direction).boxes]
    assert rendering.blocks and all(any(block is held for held in blocks) for block in rendering.blocks)
    for direction in ("backward", "forward"):
        assert kept[("graph", "builders", direction, "builder")] is getattr(stored(bound, "_builders"), direction)
    assert all(record is stored(bound, "definitions")[record.identity] for record in kept["table"].definitions)

    def boxes_in(graph):
        """Every box of a graph, the boxes inside its bubbles included."""
        found, pending = [], list(graph.boxes)
        while pending:
            box = pending.pop()
            found.append(box)
            if isinstance(box, Bubble):
                pending.extend(box.arg.boxes)
        return found

    def one_of(box, boxes):
        return any(box is other for other in boxes)

    assert kept["places"] and all(
        one_of(place.box, boxes_in(graph_of(bound, place.level, place.direction, place.grain)))
        for place in kept["places"])
    bubbles = [(key, bubble) for key, bubble in kept.items() if isinstance(key, tuple) and key[0] == "bubble"]
    assert bubbles and all(one_of(box, boxes_in(graph_of(bound, key[1], key[2], key[4])))
                           for key, bubble in bubbles for box in bubble.arg.boxes if not is_wiring(box))
    for direction in ("backward", "forward"):
        for grain in ("primitive", "node", "combined", "factored"):
            key = ("graph", "initial", direction, grain)
            ours = [box for box in boxes_in(kept[key])
                    if one_of(box, boxes_in(getattr(stored(bound, "initial"), direction)))]
            theirs = [box for box in boxes_in(vars(version)["_kept"][key])
                      if one_of(box, boxes_in(getattr(stored(version, "initial"), direction)))]
            assert ours and len(ours) == len(theirs), key

    def held(value):
        """The ids of the objects `value` holds, itself included; strings,
        numbers, classes, functions, modules and the empty containers Python
        shares excepted."""
        shared = (str, bytes, int, float, complex, type, type(None), types.FunctionType, types.BuiltinFunctionType,
                  types.MethodType, types.ModuleType)
        found, pending = set(), [value]
        while pending:
            item = pending.pop()
            if (isinstance(item, shared) or type(item) in (tuple, frozenset) and not item
                    or id(item) in found):
                continue
            found.add(id(item))
            pending.extend(gc.get_referents(item))
        return found

    assert held(kept) & held(vars(version)) == set()
    assert vars(version)["_kept"]["wire_table"].stage is version


def test_a_refusal_the_wire_table_holds_is_carried_with_notes_of_its_own():
    """A refusal the wire table of a version holds is carried to a version a
    verb returns without the notes a caller added to the one its argument
    raised, and a note added to either stays on it. No stage the snapshot
    records holds one; `retire.bl` of the Gourinchas and Parker application
    holds one for its block `cntn_to_dcsn`, which no rule assigns to a
    direction, and its wire table raises it when asked for its rows (the
    review of the stage object under repeated use, §6, decision 1)."""
    from bellman.stage.grains import wire_table
    stage = elaborate_stage(load_stage(
        ROOT / PRELIMINARY / "gourinchas-parker-2002/retire.bl"))
    with pytest.raises(NotConstructed) as held:
        wire_table(stage).rows("backward")
    held.value.add_note("Stage occurrence: periods[0].stages['retire']")
    # `methodize` binds the stage it is called on (specification 0.6 decision
    # 1 and R4), so the version made from it is the copy `copy_native` makes
    bound = copy_native(stage.methodize([]))
    with pytest.raises(NotConstructed) as carried:
        wire_table(bound).rows("backward")
    assert carried.value is not held.value and str(carried.value) == str(held.value)
    assert getattr(carried.value, "__notes__", []) == []
    carried.value.add_note("Stage occurrence: periods[1].stages['retire']")
    assert held.value.__notes__ == ["Stage occurrence: periods[0].stages['retire']"]


def test_a_shock_stays_active_through_a_sibling_input_a_constant_is_extended_and_every_path_is_integrated():
    joined = stage_from_text(two_nodes(backward="    W1 = E_{y}(V[>])\n    W2 = V[>]\n    V = E_{y,z}(W1 + W2) :: [id=value]\n"))
    boxes = {box.name: box for box in operators_of(joined, "backward")}
    assert kernel(joined, boxes["cntn_to_dcsn.value:Expectation:1"]).splitlines()[:2] == [
        "distribution of (y, z): y ~ N(0, 1) · z ~ N(0, 1)",
        "conditioned on none declared; drawn on the edge dcsn_to_cntn; in cntn_to_dcsn at each point of k_d, "
        "integrates y, z; declared at two_nodes:distribution:y, two_nodes:distribution:z"]
    constant = stage_from_text(two_nodes(backward="    V = E_{y,z}(V[>]) + E_{y}(1) :: [id=value]\n"))
    boxes = {box.name: box for box in operators_of(constant, "backward")}
    assert kernel(constant, boxes["cntn_to_dcsn.value:Aggregation:2"]).splitlines() == [
        "𝐺 of cntn_to_dcsn, segment cntn_to_dcsn.value:Aggregation:2: 𝐺(V≻, k_d, c) = 1",
        "output 1; unused V≻, k_d, c"]
    # the read of z integrates only z on its path, although V[>]'s path integrates both shocks
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(two_nodes(backward="    V = E_{y,z}(V[>]) + E_{z}(z) :: [id=value]\n",
                                  header="(V[>] : ℝ @ !vlu, z) : !cntn -> (V : ℝ @ !vlu) : !dcsn]"))
    assert (refused.value.rule, refused.value.address) == ("shock-observed", "cntn_to_dcsn.value")
    assert "from the shock z read in cntn_to_dcsn.value by a path that integrates z and not y" in refused.value.message


def test_separate_declarations_are_a_product_and_a_hierarchy_states_no_independence_of_its_children():
    independent = stage_from_text(two_nodes())
    [factorization] = [item for item in independent.obligations() if item.condition == "joint-distribution-factorization"]
    assert factorization.entries == ("two_nodes:distribution:y", "two_nodes:distribution:z", "dcsn_to_cntn")
    assert factorization.explanation == (
        "The joint distribution for dcsn_to_cntn is assumed to be the product of the declared conditional "
        "distributions given their named parents and the source coordinates: y given (k_d, c) by "
        "two_nodes:distribution:y; z given (k_d, c) by two_nodes:distribution:z; "
        "y and z are conditionally independent given (k_d, c).")
    assert kernel(independent, "cntn_to_dcsn.first:Expectation:1").splitlines()[0] == (
        "distribution of (y, z): y ~ N(0, 1) · z ~ N(0, 1)")
    text = two_nodes(declarations="y ~ N(0,1)\nz : ℝ\nz ~ N(y,1)\nw : ℝ\nw ~ N(y,1)\n",
                     transition="    a = k_d*(c*z + (1-c)*R) + w\n",
                     backward="    V = E_{y,z,w}(V[>]) :: [id=value]\n")
    text = text.replace("(k_d, c : !ctrl @ [0,1], y, z) : !dcsn", "(k_d, c : !ctrl @ [0,1], z, w) : !dcsn").replace(
        "E_{y,z}(V[>])) :: [id=objective]", "E_{y,z,w}(V[>])) :: [id=objective]")
    hierarchy = stage_from_text(text)
    [factorization] = [item for item in hierarchy.obligations() if item.condition == "joint-distribution-factorization"]
    assert factorization.explanation.endswith(
        "y given (k_d, c) by two_nodes:distribution:y; z given y and (k_d, c) by two_nodes:distribution:z; "
        "w given y and (k_d, c) by two_nodes:distribution:w.")


def test_a_partial_expectation_uses_the_joint_normal_conditional_and_the_outer_one_the_marginal():
    r = 0.5
    stage = calibrate(stage_from_text(joint_normal()), {"β": 0.96, "R": 1.03, "r": r})
    inner, outer = kernel(stage, "cntn_to_dcsn.value:Expectation:2"), kernel(stage, "cntn_to_dcsn.value:Expectation:1")
    assert inner.splitlines() == [
        "distribution of y: y | z ~ N(r*z, 1 - r*r)",
        "conditioned on z; drawn on the edge dcsn_to_cntn; in cntn_to_dcsn at each point of (k_d, z), "
        "integrates y; declared at two_nodes:distribution:y_z",
        f"at the calibration: y | z ~ N({r / 1.0!r}*z, {1.0 - r * r / 1.0!r})"]
    assert outer.splitlines() == [
        "distribution of z: z ~ N(0, 1)",
        "conditioned on none declared; drawn on the edge dcsn_to_cntn; in cntn_to_dcsn at each point of k_d, "
        "integrates z; declared at two_nodes:distribution:y_z",
        "at the calibration: z ~ N(0.0, 1.0)"]
    # with v(a) = a and a = y the inner result is r·z and the outer one r·E[z] = 0, not r²·y
    marginal = stage_from_text(joint_normal(backward="    V = E_{y,z}(V[>]) :: [id=value]\n"))
    assert kernel(marginal, "cntn_to_dcsn.value:Expectation:1").splitlines()[0] == (
        "distribution of (y, z): (y, z) ~ N((0, 0), ((1, r), (r, 1)))")
    # a zero conditional variance with an invertible conditioning block, and a singular joint unconditioned, are admitted
    one = calibrate(stage_from_text(joint_normal()), {"β": 0.96, "R": 1.03, "r": 1.0})
    assert kernel(one, "cntn_to_dcsn.value:Expectation:2").splitlines()[2] == "at the calibration: y | z ~ N(1.0*z, 0.0)"
    stage_from_text(joint_normal(covariance="((1,0),(0,0))", backward="    V = E_{y,z}(V[>]) :: [id=value]\n"))
    # the calibration path checks the covariance the values determine, and the
    # refusal is raised at the distribution record, whose address is the file
    # position of its declaration (AMD-SG-017 §4)
    with pytest.raises(ConstructionError) as refused:
        calibrate(stage_from_text(joint_normal(r_set="ℝ")), {"β": 0.96, "R": 1.03, "r": 2.0})
    assert (refused.value.rule, refused.value.address) == ("distribution-domain", "t.bl:7")
    assert "not positive semidefinite" in refused.value.message


def test_compiled_kernels_with_analytic_expectation_inputs_reproduce_ce_amb_and_the_ces_value(sa_savings):
    largest = 0.0

    def close(value, reference):
        nonlocal largest
        assert math.isfinite(value) and value > 0 and reference > 0
        error = abs(value - reference) / abs(reference)
        largest = max(largest, error)
        assert error <= RELATIVE, (value, reference)
    for values in SA_SAVINGS_CALIBRATIONS:
        stage = calibrate(copy_native(sa_savings), values)
        β, ρ, γ, η, κ, σν, σΨ = (values[name] for name in ("β", "ρ", "γ", "η", "κ_1", "σ_ν", "σ_Ψ"))
        sub = stage.builder.bwd.sub_builders
        risk, ambiguity = inside(sub, "cntn_to_dcsn.risk_ce"), inside(sub, "cntn_to_dcsn.ambiguity_ce")
        primitive = {box.name: box for box in stage.builder.bwd.primitives.graph.boxes}

        def made(box, stage=stage):
            # the kernel's function, given the calibration's values after
            # the kernel's arguments
            function, bound = compile_kernel(stage, box), kernel(stage, box).parameter_values
            return lambda *arguments: function(*arguments, *bound)
        g = made(risk["cntn_to_dcsn.risk_ce:Pullback"])
        power_γ = made(risk["cntn_to_dcsn.risk_ce:Aggregation:1"])
        root_γ = made(risk["cntn_to_dcsn.risk_ce:Aggregation"])
        power_η = made(ambiguity["cntn_to_dcsn.ambiguity_ce:Aggregation:1"])
        root_η = made(ambiguity["cntn_to_dcsn.ambiguity_ce:Aggregation"])
        ces = made(next(box for box in sub.graph.boxes if box.name == "cntn_to_dcsn:Aggregation"))
        merged_power = made(primitive["cntn_to_dcsn.ambiguity_ce:Aggregation:1"])
        merged_ces = made(primitive["cntn_to_dcsn:Aggregation"])
        for m_d in (0.5, 1.0, 2.0):
            for share in (0.2, 0.5, 0.8):
                c = share * m_d
                s = m_d - c
                for ν in (κ - σν, κ, κ + σν):
                    for z in (-1.0, 0.0, 1.0):
                        Ψ = math.exp(ν + σΨ * z)
                        close(g(m_d, c, Ψ), s * Ψ)
                        close(power_γ(s * Ψ, m_d, c, Ψ), (s * Ψ) ** (1 - γ))
                    M_γ = s ** (1 - γ) * math.exp((1 - γ) * ν + (1 - γ) ** 2 * σΨ ** 2 / 2)
                    CE = root_γ(M_γ, m_d, c, ν)
                    close(CE, s * math.exp(ν + (1 - γ) * σΨ ** 2 / 2))
                    close(power_η(CE, m_d, c, ν), CE ** (1 - η))
                    composed = merged_power(root_γ(M_γ, m_d, c, ν), m_d, c, ν)
                    close(composed, power_η(root_γ(M_γ, m_d, c, ν), m_d, c, ν))
                    if η == γ:
                        close(composed, M_γ)
                M_η = s ** (1 - η) * math.exp((1 - η) * (κ + (1 - γ) * σΨ ** 2 / 2) + (1 - η) ** 2 * σν ** 2 / 2)
                AMB = root_η(M_η, m_d, c)
                AMB_reference = s * math.exp(κ + (1 - η) * σν ** 2 / 2 + (1 - γ) * σΨ ** 2 / 2)
                close(AMB, AMB_reference)
                CE_predictive = s * math.exp(κ + (1 - γ) * (σν ** 2 + σΨ ** 2) / 2)
                close(AMB / CE_predictive, math.exp((γ - η) * σν ** 2 / 2))
                close(ces(AMB, m_d, c), ((1 - β) * c ** (1 - ρ) + β * AMB_reference ** (1 - ρ)) ** (1 / (1 - ρ)))
                close(merged_ces(root_η(M_η, m_d, c), m_d, c), ces(root_η(M_η, m_d, c), m_d, c))
    assert abs(math.exp((5.0 - 8.0) * 0.05 ** 2 / 2) - 0.996257022469171) < 1e-15
    assert largest <= RELATIVE


def test_the_three_discrete_families_construct_their_forward_graphs(cons_savings_iid, elaborate_text):
    extensions = [box.name for box in operators_of(cons_savings_iid, "forward")
                  if box_identity(box).kind == "DistributionExtension"
                  and box_identity(box).subjects == ("y",)]
    assert extensions == ["arvl_to_dcsn:DistributionExtension:y"]
    assert ("y ~ Mixture((p_zero, point mass at 0), (1 - p_zero, LogNormal(μ_y, σ_y)))"
            in kernel(cons_savings_iid, extensions[0]))
    buffer_stock_file = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
    buffer_stock = elaborate_text((_ROOT / buffer_stock_file).read_text(encoding="utf-8"),
                                  buffer_stock_file)
    assert [box.name for box in buffer_stock.builder.fwd.graph.boxes] == ["arvl_to_dcsn", "dcsn_to_cntn"]
    assert "Mixture" in kernel(buffer_stock, "arvl_to_dcsn:DistributionExtension:ξ")
    # a Categorical and a Bernoulli declaration of the preliminary corpus
    for source, box, family in (
            (f"{PRELIMINARY}/HAFiscal/HAFiscal.bl",
             "arvl_to_dcsn:DistributionExtension:z", "Categorical"),
            (f"{PRELIMINARY}/ConsPortfolio/cons.bl",
             "arvl_to_dcsn:DistributionExtension:Adjust", "Bernoulli")):
        stage = elaborate_text((_ROOT / source).read_text(encoding="utf-8"), source)
        assert stage.builder.fwd.graph.boxes, source
        assert box in [operator.name for operator in operators_of(stage, "forward")], source
        assert family in kernel(stage, box), source
    # the weights carry one obligation, in words, recorded symbolically and
    # decided when calibration supplies the numbers
    weights = [item for item in cons_savings_iid.obligations() if "weight" in item.condition]
    assert [item.entries for item in weights] == [("cons_savings_iid:distribution:y",)]
    assert "in [0, 1]" in weights[0].explanation and "sum to one" in weights[0].explanation
    # a Bernoulli records its two-point support as an obligation, not as its result set;
    # a Categorical that selects a row of a named matrix records one for the rows
    for source, words in (
            (f"{PRELIMINARY}/ConsPortfolio/cons.bl", ("value 1 with probability", "in [0, 1]")),
            (f"{PRELIMINARY}/AlganRagotMoney/returns.bl", ("each row of", "sums to one"))):
        stage = elaborate_text((_ROOT / source).read_text(encoding="utf-8"), source)
        recorded = [item for item in stage.obligations() if "weight" in item.condition]
        assert recorded, source
        for word in words:
            assert word in recorded[0].explanation, (source, word)


def test_the_navigation_is_the_interface_and_the_box_queries_are_implementation(
        cons, sa_savings, cons_methodized):
    builder = cons.dcsn.builder.bwd
    assert str(builder) == card(cons, builder.box)
    box = builder["pullback"]
    assert (str(box), box.kernel()) == (card(cons, box.box), kernel(cons, box.box))
    calibrated = copy_native(cons).calibrate({"ρ": 2.0})
    assert float(calibrated.dcsn.builder.bwd["pullback"].compile_kernel()(2, 0.5)) == 1.5
    # a node id is a key, never an attribute; a pair of keys walks one level down
    nested = sa_savings.dcsn.builder.bwd["risk_ce", "expectation:1"]
    assert nested.kernel() == kernel(sa_savings, nested.box)
    with pytest.raises(AttributeError):
        sa_savings.dcsn.builder.bwd.risk_ce
    # a key that names nothing refuses, listing what is inside
    with pytest.raises(KeyError) as missing:
        cons.dcsn.builder.bwd["no_such_box"]
    assert "no_such_box" in str(missing.value)
    block = cons.initial.backward["cntn_to_dcsn"]
    assert str(block["cntn_to_dcsn.value"]) == card(cons, "cntn_to_dcsn.value")
    # a navigation object is made when it is asked for, so two of them for one
    # piece of one version are two objects that compare equal
    assert cons.dcsn.builder.bwd is not cons.dcsn.builder.bwd
    assert cons.dcsn.builder.bwd == cons.dcsn.builder.bwd
    assert cons.builder.bwd == cons.builder.bwd
    assert cons.initial.backward["cntn_to_dcsn"] != cons.dcsn.builder.bwd
    assert cons_methodized.builder.bwd != cons.builder.bwd     # a different version
    # a definition is a level: the table lists its records by kind and prints one card
    assert cons.definitions.list()["g"] == ("cons:g:arvl_to_dcsn", "cons:g:dcsn_to_cntn")
    assert str(cons.definitions.denote("cons:G:cntn_to_dcsn")) == card(cons, cons.definitions["cons:G:cntn_to_dcsn"])
    # .methods is a read-only mapping at every level, the places typed within the handle
    assert cons.dcsn.builder.bwd.methods == {} and box.methods == {}
    assert {name: held.word for name, held in cons_methodized.dcsn.builder.bwd.methods.items()} == {
        "cntn_to_dcsn.evaluate": "!Linear"}
    assert {name: held.word for name, held in cons_methodized.builder.policy.methods.items()} == {
        "policy": "!egm"}
    assert cons_methodized.builder.policy["Evaluation"].methods == {}
    assert {name: held.word for name, held in cons_methodized.arvl.builder.fwd.methods.items()} == {
        "arvl_to_dcsn": "!deterministic"}
    # a query that takes a box as its argument is implementation: bound as no
    # method of the stage, and shown on no page
    for retired in ("view", "kernel", "compile_kernel", "builders_graph", "initial_diagram", "to_drawing"):
        if retired == "view":
            assert cons.view() == str(cons)          # the stage prints its own screen
            continue
        assert not hasattr(cons, retired), retired
    for path in STAGE_OBJECT_PAGES:
        text = (_ROOT / path).read_text(encoding="utf-8")
        for call in ("to_drawing(", "builders_graph(", "initial_diagram(", "graph_of(",
                     "semgraph.record(", "card(stage", "kernel(stage", "compile_kernel(stage",
                     "stage.origins(", "stage.affine("):
            assert call not in text, (path, call)
        # a verb of the stage takes no argument: `stage.view()` is the screen,
        # `stage.view(box)` is the retired form
        for name in ("stage", "cons", "sa", "iid", "joint", "calibrated", "methodized", "equal", "halved"):
            for verb in ("view", "kernel", "compile_kernel"):
                for found in re.finditer(re.escape(f"{name}.{verb}("), text):
                    assert text[found.end()] == ")", (path, f"{name}.{verb}(", text[found.end():found.end() + 40])


def test_every_public_answer_names_its_api_page_and_the_words_are_in_the_documents(cons):
    """The docstring of every public record, handle and verb of a stage names
    the page of the API that documents it, the index or one of the nine pages
    of the stage object, and its section (DR-0742), and the words the
    amendments retired stand in no document. That every listing of the nine pages is what the package prints
    is item 2 of `tests/cat/test_docs_shape.py`, which runs
    `stage_object_page.py --check` on every page of the API."""
    from bellman.display import drawing, printed_records, sheets
    from bellman.stage.encoding import StageEncoding
    from bellman.display.printed_records import Fields, Diagnostics, Methods
    from bellman.stage.kernels import Kernel
    from bellman.stage.pieces import Definitions, Graphs, GraphHandle, BubbleHandle, BoxHandle, LineHandle

    documenting = STAGE_OBJECT_PAGES + ("docs/Bellman-Sym/API/index.md",)
    # the printed records, each read from the module that holds it: the sheets and
    # listings print, and the answers a card and an encoding present are the
    # records of the card (AMD-SG-027 §2)
    from bellman.display import cards
    records = [sheets.Sheet, drawing.Drawing] + [getattr(printed_records, name) for name in (
        "Rows", "Listing", "NamedListing", "SectionedListing", "Obligations", "Signature")]
    records += [getattr(cards, name) for name in (
        "TitleBlock", "Wire", "Statement", "Denoted", "Hypothesis", "KernelClause",
        "ImageByName", "ImageAtPoint", "ImageSet", "OperatorCard", "Piece", "Composite", "AuthoredCard",
        "DefinitionCard", "StageDenotation")]
    public = records + [type(cons), type(cons.metadata), type(cons.provenance), type(cons.bindings),
        Definitions, Graphs, GraphHandle, BubbleHandle, BoxHandle, LineHandle,
        Fields, Diagnostics, Methods, Kernel, StageEncoding]
    answers = [(held.__name__, held) for held in public]
    for held in public:
        answers.extend((held.__name__ + "." + name, member)
                       for name, member in vars(held).items() if not name.startswith("_")
                       and (inspect.isfunction(member) or isinstance(member, property))
                       and inspect.getdoc(member))
    answers.extend(("stage." + name, getattr(cons, name)) for name in dir(cons)
                   if not name.startswith("_") and callable(getattr(cons, name)))
    for name, answer in answers:
        wording = inspect.getdoc(answer)
        assert wording and "AMD-" not in wording, (name, wording)
        assert any(page in wording for page in documenting) and "§" in wording, (name, wording)
        for retired in ("definitions.view(", "piece.view(", "operators_of(", "at(grain)"):
            assert retired not in wording, (name, retired)
    for attribute in ("name", "metadata", "definitions", "initial", "_builders", "bindings", "provenance"):
        assert "`" + attribute + "`" in inspect.getdoc(type(cons)), attribute
    assert (_ROOT / "CLAUDE.md").is_symlink()                  # one project memory, not two
    documents = {path: (_ROOT / path).read_text(encoding="utf-8") for path in (
        "AGENTS.md", "docs/wiki/semgraph.md", "docs/wiki/builder.md",
        "docs/wiki/elaborated_stage.md", "docs/wiki/operator.md", "docs/changelog.md")}
    assert "docs/Bellman-Sym/API/stage/" in documents["docs/changelog.md"]
    assert "Pullback of the function 𝑉 along the law of motion 𝑔" in documents["AGENTS.md"]
    # the retired word is replaced by "value bundle" (AMD-SG-011 §5)
    assert "n initial diagram, a builders graph, a grain or a value bundle" in documents["AGENTS.md"]
    for path, text in documents.items():
        if path == "docs/changelog.md":
            # a dated entry records what was released that day; the entry of 14
            # September carries one line saying that its names were renamed,
            # and only the entry this pass adds is read for the new words
            assert "The names in this entry were renamed on 15 September" in text
            head, _, rest = text.partition("### 2026-09-15 — The stage object")
            text = rest.split("\n### ", 1)[0]
            assert text and "initial_diagrams" in text
        assert "Substitution of the law of motion" not in text, path
        for retired in ("face(", "compile(", ".views", "semgraph.view(", "view_boundary",
                        "graph_boundary", "builders_graph", "initial_diagram(",
                        # the signature words and the parameter reading of the
                        # policy, retired by AMD-SG-013 §§2, 4
                        "parameter of a builder", "parameterised builder", "parameter of this box",
                        "parameter of the builder", "as parameters", "in Γ("):
            assert retired not in text, (path, retired)




def test_item_1_each_public_name_is_imported_from_the_object_it_concerns():
    """The import rules (import-rules.md §1 and §2; spec 0.3 of the model
    interface, §12, P item 1): a name is imported from the namespace of the
    object it concerns, each table maps a name to the module that defines
    it, and a name of the view is one object in two tables."""
    from importlib import import_module
    import bellman.period
    import bellman.stage
    import bellman.trellis
    from bellman.factory import elaboration, joins, loading, model_explorer, trellis, trellis_drawings
    from bellman.period import diagram_period, period_joins
    from bellman.stage import elaborate_stage, elaborate_text, load_stage
    from bellman.trellis import elaborate_trellis, explore, load_trellis
    assert (load_stage, elaborate_stage, elaborate_text) == (
        loading.load_stage, elaboration.elaborate_stage, elaboration.elaborate_text)
    assert (period_joins, diagram_period) == (joins.period_joins, trellis_drawings.diagram_period)
    assert (load_trellis, elaborate_trellis, explore) == (
        loading.load_trellis, trellis.elaborate_trellis, model_explorer.explore)
    assert bellman.stage.explore is bellman.trellis.explore
    assert bellman.stage.write_model_explorer is bellman.trellis.write_model_explorer
    for namespace in (bellman.stage, bellman.period, bellman.trellis):
        assert list(namespace.__all__) == list(namespace._EXPORTS)
        for name in namespace.__all__:
            assert getattr(import_module(namespace._EXPORTS[name]), name) is getattr(namespace, name), name
        with pytest.raises(AttributeError):
            namespace.no_such_name
    with pytest.raises(ImportError):
        from bellman.stage import no_such_name  # noqa: F401
    import bellman.stage.grains  # a submodule is still imported as one
    # the same submodule, read through `from ... import` in a fresh
    # interpreter, where `__getattr__`'s fallback would run if the import
    # system did not set it as an attribute of `bellman.stage` first
    subprocess.run(
        [sys.executable, "-c",
         "from bellman.stage import grains; import bellman.stage; "
         "assert bellman.stage.grains is grains"],
        check=True)
    assert (bellman.stage.arvl, bellman.stage.dcsn, bellman.stage.cntn) == ("arvl", "dcsn", "cntn")
    assert {"load_recipe", "accrete"} <= set(bellman.trellis.__all__)
    assert not {"load_recipe", "accrete", "period_joins"} & set(bellman.stage.__all__)
    # the root exports nothing (brief §1): a name of the root is refused
    assert bellman.__all__ == [] and not hasattr(bellman, "_EXPORTS")
    with pytest.raises(ImportError):
        from bellman import load_stage  # noqa: F401
    with pytest.raises(AttributeError):
        bellman.load_stage








def test_parameters_prints_a_declared_parameter_unbound_and_then_the_value_calibration_binds(cons, cons_calibrated):
    """A parameter row carries its name, the set its declaration names and its
    value, which is the word `unbound` until a calibration supplies one
    (AMD-SG-007 §10 item 3)."""
    assert [(row["name"], to_source(row["domain"]), row["value"]) for row in cons_calibrated.par.list()] == [
        ("ρ", "[1, inf)", 6.0)]
    assert [(row["name"], to_source(row["domain"]), row["value"]) for row in cons.par.list()] == [
        ("ρ", "[1, inf)", "unbound")]


def test_the_printed_listing_of_an_authored_nodes_graphs_names_the_operators_of_its_drawing_alike(elaborate_text):
    """The listing of every graph of the inline `arrival_value` stage equals
    the labels of its drawing, and its forward graph extends the measure by the
    distribution of the income shock (AMD-SG-006 §10 items 8 and 9). The same
    claim for the corpus stages is the `listing` of the recording; this stage
    is not recorded."""
    # the labels by the kind of the box: the terminology table's description of
    # the operator, in the register ruled on 10 September
    expected_labels = {"backward": ["integrate → 𝐸𝑊(a)", "Evaluation of 𝐸𝑊≺"],
                       "forward": ["Extension of the measure by the distribution of y"]}
    stage = elaborate_text(ARRIVAL)
    labels = {"backward": set(), "forward": set()}
    for direction in ("backward", "forward"):
        for grain in ("builder", "sub-builder", "primitive"):
            try:
                graph = graph_of(stage, "builders", direction, grain)
            except NotConstructed:
                continue
            lines = str(graph).splitlines()
            assert lines == list(to_drawing(graph).labels), (direction, grain)
            assert lines and not any(line.strip().startswith(("Cup(", "Cap(")) for line in lines)
            labels[direction].update(line.strip() for line in lines)
    for direction, expected in expected_labels.items():
        assert set(expected) <= labels[direction], (direction, labels[direction])
    # each initial diagram lists its blocks and, inside each, its statements by address
    for direction in ("backward", "forward"):
        diagram = getattr(stage.initial, direction).graph
        assert str(diagram).splitlines() == list(to_drawing(diagram).labels)




# --- the standing claims of the retired acceptance file of AMD-SG-015 --------
# AMD-SG-016 brief 1 retires `tests/cat/test_amd_sg_015.py` as the lean rule
# requires. The stage sheet of `cons` and the two operator cards it pins are
# carried by the snapshot (`tests/snapshot/cons.json` key `stage`, field
# `description`; `tests/snapshot/cons.json` and `sa_savings.json`, the box
# views under the `builders/` and `initial/` keys). The claims below read a
# sheet the recording does not hold — a graph handle's sheet, the definitions
# listing, a bound version, a stage outside the corpus, or the parse check —
# so they stand here, with their assertions unchanged.

# the printed width of every sheet (AMD-SG-015 §2)
WIDTH = 78


def sections(text):
    """The sections of a sheet by their labels: every line under a section rule,
    which is what AMD-SG-015 §2 promises a machine."""
    found, label = {}, None
    for line in text.splitlines():
        if line and not line.startswith(" ") and ("─" in line or "┄" in line) and not line.startswith("━"):
            label = line.split("─")[0].split("┄")[0].strip()
            found[label] = []
        elif label is not None:
            found[label].append(line)
    return {label: [line for line in lines if line.strip()] for label, lines in found.items()}



def test_item_1_a_refused_graph_is_stated_on_the_sheet_and_does_not_stop_it(elaborate_text):
    """A stage that elaborates while a graph is refused prints its sheet, and a
    refused graph is a fact the sheet states rather than an error of printing
    (§3: "The graphs section says which graphs are present or refused").

    `retire.bl` of `gourinchas-parker-2002` is a terminal stage with no
    continuation perch: it elaborates, and its two initial diagrams and its two
    builders graphs are held as refusals under the rule `not-constructed`.
    Before this the directions section asked for the chains of a refused diagram
    and raised the held refusal, so no sheet was written at all."""
    import conftest
    from bellman.refusals import NotConstructed

    path = f"{PRELIMINARY}/gourinchas-parker-2002/retire.bl"
    stage = elaborate_text((conftest.ROOT / path).read_text(encoding="utf-8"), path)
    text = str(stage)
    assert max(len(line) for line in text.splitlines()) <= WIDTH
    assert "refused under not-constructed" in text
    # A refused graph's card retains the rule, authored block, source position
    # and reason in its `Source` section, which names the file once.
    diagram = str(stage.initial.backward)
    flat = " ".join(diagram.split())
    assert diagram.splitlines()[0] == "STAGE retire / BACKWARD INITIAL DIAGRAM"
    assert "\nSource  retire.bl\n" in diagram
    assert "rule not-constructed" in flat and " 24 cntn_to_dcsn " in flat
    assert ("no rule assigns this block to the backward or the forward initial diagram: "
            "its output roles and its declared input and output perches match none") in flat
    # the verbs of a refused graph are unchanged: each raises the held refusal.
    # `directions()` is no longer among them; its lines are a section of the
    # diagram's own sheet (AMD-SG-020 §3.2 item 3)
    for verb in (stage.initial.backward.list,
                 stage.initial.backward.signature):
        with pytest.raises(NotConstructed) as refusal:
            verb()
        assert refusal.value.rule == "not-constructed"


def test_item_1_the_bound_sheet_stamps_the_version_and_lists_each_binding(cons, cons_sources):
    bound = configure(methodize(calibrate(copy_native(cons), cons_sources["calibration"]),
                                cons_sources["methods"]), cons_sources["settings"])
    assert repr(bound) == "ElaboratedStage('cons', specified)"
    lines = str(bound).splitlines()
    assert lines[0].endswith("[VERSION = SPECIFIED]")
    assert max(len(line) for line in lines) <= WIDTH
    body = sections(str(bound))
    # the bindings rule is a hairline once all three are bound
    rule = [line for line in str(bound).splitlines() if line.startswith("BINDINGS")][0]
    assert "┄" not in rule and "─" in rule
    assert "ρ = 6.0" in " ".join(body["BINDINGS"])
    assert "!egm" in " ".join(body["BINDINGS"])
    # every entry of a bound source on its own line, nothing abbreviated: the
    # components of a place on the methods line that names the place
    assert sum(1 for line in body["BINDINGS"]
               if line.split()[:2] == ["cntn_to_dcsn.evaluate", "!Linear"]) == 1
    # the stamp of a version whose bindings are an initial segment of D36's order
    assert str(calibrate(copy_native(cons), cons_sources["calibration"])).splitlines()[0].endswith("[VERSION = CALIBRATED]")
    assert str(methodize(calibrate(copy_native(cons), cons_sources["calibration"]), cons_sources["methods"])).splitlines()[0].endswith("[VERSION = METHODIZED]")
    # otherwise the bindings present, in D36's order
    only_methods = methodize(copy_native(cons), cons_sources["methods"])
    assert only_methods.__str__().splitlines()[0].endswith("[VERSION = METHODS]")








def test_item_4_a_bound_method_stands_on_every_card_of_what_it_realises(cons, cons_sources):
    """A representation typed at the Evaluation that stores what a builder
    writes is answered by the builder, by its initial block and by the
    Evaluation, and by neither the Aggregation before it nor a line of the
    block; the solution method typed on the policy builder is answered by
    the builder and by none of its rows."""
    bound = configure(methodize(calibrate(copy_native(cons), cons_sources["calibration"]),
                                cons_sources["methods"]), cons_sources["settings"])
    representation = {"cntn_to_dcsn.evaluate"}
    assert set(bound.initial.backward["cntn_to_dcsn"].methods) == representation
    assert set(bound.builder.bwd["cntn_to_dcsn"].methods) == representation
    assert bound.builder.bwd["cntn_to_dcsn"]["Aggregation"].methods == {}
    assert set(bound.builder.bwd["cntn_to_dcsn"]["Evaluation"].methods) == representation
    held = bound.builder.bwd["cntn_to_dcsn"]["Evaluation"].methods["cntn_to_dcsn.evaluate"]
    assert str(held) == '!Linear   !Cartesian(m_d=(m_min, m_max, n_m))   "cons-port:_make_interp"'
    assert bound.bindings.settings["n_m"] == 8000
    assert str(bound.builder.policy.methods["policy"]) == (
        '!egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"')
    assert all(bound.builder.policy[key].methods == {} for key in bound.builder.policy.list())
    block = bound.initial.backward["cntn_to_dcsn"]
    assert all(block[address].methods == {} for address in ("cntn_to_dcsn.value", "cntn_to_dcsn.marginal"))
    # a card with no component within it prints no `method` clause
    assert bound.arvl.builder.bwd["Aggregation"].methods == {}




def test_sound_ranges_discharge_only_decided_obligations(
        cons, elaborate_text, text_of, explicit_cons_text, cons_explicit):
    cons = cons_explicit
    aggregation = cons.dcsn.builder.bwd["Aggregation"].denote()
    assert aggregation.outputs[0].type == "Xm → [−∞, ∞)"

    obligations = tuple(cons.obligations())
    assert not any(item.condition == "finite-real-arithmetic"
                   and str(item.entries[0]) == "cntn_to_dcsn"
                   for item in obligations)
    assert any(item.condition == "finite-real-arithmetic"
               and str(item.entries[0]) == "policy"
               for item in obligations)
    assert not any(item.condition == "range-compatibility"
                   and str(item.entries[0]) in {
                       "cntn_to_dcsn.marginal", "policy.optimality"}
                   for item in obligations)
    assert not any(item.condition in {
                       "binding-domain", "function-argument-domain-inclusion"}
                   and "policy.optimality" in tuple(map(str, item.entries))
                   for item in obligations)
    # a range compatibility is the membership of the written field at the
    # point and no inclusion of a computed range (second round, R1); the one
    # on `dcsn_to_arvl.value` is one condition with the admissibility of the
    # aggregation writing `𝑉≺` (R4)
    assert not any(item.predicate is not None
                   and "⊆" in S.format_expression(item.predicate, width=None)
                   for item in obligations)
    assert [str(item.entries[0]) for item in obligations if item.predicate is not None
            and S.format_expression(item.predicate, width=None) == "V≺(m, l) ∈ ℝ"] == [
        "dcsn_to_arvl:Aggregation"]
    # `c = c[>]` declares no range on its right side, so no condition is formed
    # on it (AAS's ruling of 22 September 2026 on finding F3 of the build review)
    assert not any(item.condition == "range-compatibility"
                   and str(item.entries[0]) == "policy.cons_choice"
                   for item in obligations)

    source = explicit_cons_text
    feasible = "Γ(x : ℝ₊₊) := (0, x]"
    assert source.count(feasible) == 1
    unrestricted = elaborate_text(
        source.replace(feasible, "Γ(x : ℝ₊₊) := [-10, 10]"),
        "unrestricted_correspondence.bl")
    unresolved = tuple(unrestricted.obligations())
    range_item, = [item for item in unresolved
                   if item.condition == "range-compatibility"
                   and str(item.entries[0]) == "policy.optimality"]
    assert tuple(map(S.format_expression, range_item.entries[1:3])) == ("[−10, 10]", "ℝ₊₊")
    argument_item, = [item for item in unresolved
                      if item.condition == "function-argument-domain-inclusion"
                      and "policy.optimality" in tuple(map(str, item.entries))]
    assert tuple(map(S.format_expression, argument_item.entries[-2:])) == ("[−10, 10]", "ℝ₊₊")

    extended = elaborate_text(
        source.replace(feasible, "Γ(x : [0,inf]) := (0, x]"),
        "extended_correspondence.bl")
    extended_obligations = tuple(extended.obligations())
    extended_range, = [item for item in extended_obligations
                       if item.condition == "range-compatibility"
                       and str(item.entries[0]) == "policy.optimality"]
    assert tuple(map(S.format_expression, extended_range.entries[1:3])) == ("(0, x]", "ℝ₊₊")
    extended_argument, = [item for item in extended_obligations
                          if item.condition == "function-argument-domain-inclusion"
                          and "policy.optimality" in tuple(map(str, item.entries))]
    assert tuple(map(S.format_expression, extended_argument.entries[-2:])) == ("(0, x]", "ℝ₊₊")


# the five corpus stages whose every sheet the two sweeps of item 2 read, one
# test for each stage
SHEET_STAGES = ("cons", "port", "ez_savings", "cons_savings_iid", "sa_savings")




def test_item_2_a_wrapped_column_wraps_under_itself_and_keeps_a_set_whole(
        cons_configured, elaborate_text):
    """A wrapped column wraps under itself, no line ends in a space, and a set
    whose print contains a space is never broken across lines (§2; the
    economist's reading, corrections 7 and 8), on the cases the corpus
    reaches only by the length of one name and on the bound settings; the
    sheets of the corpus stages are read by the sweep above."""
    import conftest
    from sheets_parse import split_sets

    # the corpus reaches the case only by the length of one name, so the case is
    # built here: a wire whose name is long enough to force the wrap, on the card
    # of the aggregation that produces it. The wrap falls before the set, and the
    # identity stands against the right margin of the line it falls on; the line
    # that carries `undeclared` carries it whole
    built = elaborate_text(conftest.two_nodes(
        backward="    V = E_{y,z}(\u03b2*V[>]*(c*y + (1-c)*R + z)) :: [id=value]\n",
        header="(V[>] : \u211d @ !vlu, c) : !cntn -> (V : \u211d @ !vlu) : !dcsn]"), "t.bl")
    handle = built.builder.bwd.primitives["cntn_to_dcsn.value:Aggregation:1"]
    answer = handle.denote()
    card = str(handle)
    # The output is a function of the state and two shocks. Its public carrier
    # states that fact independently of the line at which the card wraps.
    assert answer.outputs[0].type == "ℝ × ℝ × ℝ → ℝ"
    # The raw kernel retains the control coordinate and its feasible set.
    raw_kernel = answer.kernel.denoted[0]
    # Its semantic content is independent of a display line break.
    assert " ".join(raw_kernel.type.split()) == (
        "{V≻, k_d, c, y, z ∈ ℝ × ℝ × [0, 1] × ℝ × ℝ | c ∈ Γ(k_d)} "
        "→ UNRESOLVED[𝐺; result set]")
    assert "WIRES" not in sections(card)
    assert all(len(line) <= WIDTH and not line.endswith("→")
               for line in card.splitlines())
    # the third column of the bound settings entries aligns under itself, and
    # the components of a place too wide for one line are broken at their
    # spaces, each continuation at the content column; the bound version is
    # the session's (AMD-SG-034 plan-addendum item 20)
    body = sections(str(cons_configured))["BINDINGS"]
    first = next(index for index, line in enumerate(body) if "n_m " in line)
    settings = body[first:first + 3]
    assert all(line.endswith("cntn_to_dcsn.evaluate   !Linear") for line in settings)
    assert len({line.index("cntn_to_dcsn.evaluate") for line in settings}) == 1
    evaluate = next(index for index, line in enumerate(body) if line.split()[:1] == ["cntn_to_dcsn.evaluate"])
    policy = next(index for index, line in enumerate(body) if line.split()[:1] == ["policy"])
    components = body[evaluate:policy]
    assert len(components) > 1 and all(len(line) <= WIDTH for line in components)
    assert " ".join(" ".join(components).split()) == (
        'cntn_to_dcsn.evaluate !Linear !Cartesian(m_d=(m_min, m_max, n_m)) "cons-port:_make_interp"')
    assert len({len(line) - len(line.lstrip()) for line in components}) == 1

    rates = elaborate_text("@stage: t\nrates : " + " × ".join(["[0,1]"] * 11) + "\n")
    listing = str(rates.definitions.list()).splitlines()
    assert sum(line.count("[0, 1]") for line in listing) == 11
    assert split_sets(listing) == []
    assert all(len(line) <= WIDTH for line in listing)


def test_item_5_the_stopping_points_and_the_short_form_follow_d36(cons, cons_sources):
    assert repr(cons) == "ElaboratedStage('cons', symbolic)"
    calibrated = calibrate(copy_native(cons), cons_sources["calibration"])
    assert repr(calibrated) == "ElaboratedStage('cons', calibrated)"
    methodized = methodize(calibrated, cons_sources["methods"])
    assert repr(methodized) == "ElaboratedStage('cons', methodized)"
    assert repr(configure(methodized, cons_sources["settings"])) == "ElaboratedStage('cons', specified)"
    # a version whose bindings are no initial segment lists them in D36's order
    assert repr(methodize(copy_native(cons), cons_sources["methods"])) == "ElaboratedStage('cons', methods)"




def core_stage_files():
    """The stage files of the core folders of `applications/`, every folder
    directly under it (AMD-SG-034 plan-addendum item 19, AAS: "don't test
    across the dozens of prelim applications, just stick to the core ones"):
    each stage file `STAGE_FILES` lists, as its path in the repository, in
    sorted order; an addition beside a stage file is not listed."""
    return sorted(path.relative_to(ROOT).as_posix() for path in STAGE_FILES)


@pytest.mark.sweep
@pytest.mark.parametrize("relative", core_stage_files())
def test_every_sheet_of_every_stage_file_that_elaborates_is_within_the_grammar(relative, application_stage):
    """The sweep of AMD-SG-015 §1 over the core folders of `applications/`,
    one test for each stage file of `core_stage_files`: every sheet of the
    stage file, if it elaborates, is read back, the file prints at least one
    sheet, and no line is wider than the width, ends in a space or splits a
    set whose print contains a space. A file the elaborator refuses has no
    sheet and is skipped; the next test holds that at least twelve files
    elaborate. The five corpus stages are held above as well, so that a
    wrapping rule is stated once and holds everywhere."""
    from sheets_parse import parse_every_sheet

    try:
        stage = application_stage(ROOT / relative)
    except Exception:
        pytest.skip(f"the elaborator refuses {relative}, which has no sheet")
    report = parse_every_sheet(stage)
    assert report["sheets"] > 0, relative
    for fault in ("unparsed", "over_width", "trailing", "split_set"):
        assert report[fault] == [], (fault, report[fault][:3])




# --- the table of typings of one construction (AMD-SG-016 §3) ----------------

def test_two_constructions_open_at_once_keep_separate_tables_of_typings():
    """A sort is validated against the table of typings of the construction
    that builds it. While a second construction is open in another thread and
    has given the same identity another role, the first construction builds
    its own sort of that identity again and is not refused."""
    import threading
    from bellman.native.identity import Identity
    from bellman.native.records import Sort, construction_typing_table

    identity = Identity("field", stage="s", perch="arvl", field="a")
    first_has_built, second_has_built, first_has_finished = (threading.Event() for _ in range(3))
    refusals = []

    def first():
        try:
            with construction_typing_table():
                Sort(identity, "field", perch="arvl", role="state")
                first_has_built.set()
                assert second_has_built.wait(timeout=30)
                Sort(identity, "field", perch="arvl", role="state")
        except Exception as error:
            refusals.append(("first", error))
        finally:
            first_has_finished.set()

    def second():
        try:
            assert first_has_built.wait(timeout=30)
            with construction_typing_table():
                Sort(identity, "field", perch="arvl", role="control")
                second_has_built.set()
                assert first_has_finished.wait(timeout=30)
        except Exception as error:
            refusals.append(("second", error))
        finally:
            second_has_built.set()

    threads = [threading.Thread(target=first), threading.Thread(target=second)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert refusals == []

    with construction_typing_table():
        Sort(identity, "field", perch="arvl", role="state")
        with pytest.raises(ValueError, match="one typing"):
            Sort(identity, "field", perch="arvl", role="control")


def test_an_identity_reads_a_line_s_branch_and_a_measure_carries_its_label():
    """A line inside a nested block is addressed under its label (D02), which
    `Identity.branch` reads as `block` reads the first segment; a measure on
    one branch carries the label in its field (E3, E5)."""
    from bellman.native.identity import Identity
    line = Identity("line", address="dcsn_to_cntn.keep.cash_on_hand")
    assert (line.block, line.branch, line.key_within("dcsn_to_cntn.keep")) == ("dcsn_to_cntn", "keep", "cash_on_hand")
    assert Identity("line", address="policy.choice").branch is None
    keep = Identity("measure", stage="s", perch="cntn", field="keep")
    assert str(keep) == "s:measure:cntn:keep" and keep != Identity("measure", stage="s", perch="cntn")


@pytest.mark.parametrize("binder", ("cp", "q", "ρ"))
def test_calibration_reads_each_free_parameter_in_its_own_scope(elaborate_text, text_of, binder, explicit_cons_text):
    source = explicit_cons_text.replace("𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])", "𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) + 1/(ρ-6)")
    source = source.replace("argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])",
                            f"argmax_{{{binder} : Γ(m_d)}}(𝑢({binder}) + V[>])")
    stage = elaborate_text(source)
    with pytest.raises(ValueError, match="ρ [-−] 6"):
        stage.calibrate({"ρ": 6.0})
    # the calibration binds a copy, so that `stage` stays symbolic
    version = copy_native(stage).calibrate({"ρ": 7.0})
    condition, = [item for item in version.obligations()
                  if item.condition == "arithmetic-definedness" and item.entries[0].block == "policy"]
    assert condition.status == "established" and condition.evidence == ("calibration ρ = 7.0",)
    arithmetic = [item for item in stage.obligations()
                  if item.condition == "arithmetic-definedness"]
    assert len(arithmetic) == 2 and all(item.status == "required" for item in arithmetic)
    assert any(item.condition == "range-compatibility"
               and item.status == "established"
               and str(item.entries[0]) == "dcsn_to_cntn.1"
               for item in stage.obligations())


def test_calibration_checks_free_occurrences_even_when_a_bound_occurrence_is_undecided(elaborate_text, text_of, explicit_cons_text):
    source = explicit_cons_text.replace("argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])",
        "argmax_{ρ : Γ(m_d)}(𝑢(ρ) + V[>] + 1/(ρ-6))")
    bound_only = elaborate_text(source).calibrate({"ρ": 6.0})
    assert all(item.status == "required" for item in bound_only.obligations()
               if item.condition == "arithmetic-definedness" and item.entries[0].block == "policy")
    mixed = elaborate_text(source.replace("𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])", "𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) + 1/(ρ-6)"))
    with pytest.raises(ValueError, match="ρ [-−] 6"):
        mixed.calibrate({"ρ": 6.0})
    # two occurrences of `1/(ρ − 6)` on two lines are two conditions (second
    # round, R2 and R4): the free one, owned by the piece realising the
    # InvEuler line, is decided by the calibration; the bound one, on the
    # line marked `!doc`, is not
    conditions = {str(item.entries[0]): item.status
                  for item in mixed.calibrate({"ρ": 7.0}).obligations()
                  if item.condition == "arithmetic-definedness" and item.entries[0].block == "policy"}
    assert conditions == {"policy.InvEuler:Aggregation": "established", "policy.optimality": "required"}


@pytest.mark.parametrize("denominator,r,s", (
    ("r/1-s", 2**53 + 1, 2**53),
    ("r/2-s/2", 2**53 + 1, 2**53),
    ("1/r-1/s", 10**400 + 1, 10**400),
    ("r^(-1)-s^(-1)", 2**53 + 1, 2**53),
    ("r-s", 10**400 + 1, 10**400),
), ids=("integer-division", "rational-difference", "large-reciprocals", "negative-powers", "large-integers"))
def test_calibration_preserves_integer_and_rational_truth(elaborate_text, denominator, r, s):
    source = ("@stage: parameters\nr : ℝ\ns : ℝ\n"
              "[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n"
              f" y = x + 1/({denominator}) :: [id=value]\n}}\n")
    stage = elaborate_text(source)
    with pytest.raises(ValueError, match="calibration"):
        stage.calibrate({"r": s, "s": s})
    # the calibration binds a stage of its own, so that `stage` stays symbolic
    # (specification 0.6 decision 1 and R4)
    version = copy_native(stage).calibrate({"r": r, "s": s})
    assert dict(version.bindings.calibration) == {"r": r, "s": s}
    assert all(type(value) is int for value in version.bindings.calibration.values())
    conditions = [item for item in version.obligations() if item.condition == "arithmetic-definedness"]
    assert conditions and all(item.status == "established" for item in conditions)
    assert any(item.evidence == (f"calibration r = {r!r}, s = {s!r}",) for item in conditions)
    assert all(item.status == "required" for item in stage.obligations())


@pytest.mark.parametrize("value,domain,spelling", (
    (float("inf"), "[0, inf]", "inf"),
    (float("-inf"), "[-inf, 0]", "-inf"),
))
def test_encoding_keeps_admitted_infinities_in_strict_json(elaborate_text, value, domain, spelling):
    import json
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    source = (f"@stage: parameters\nr : {domain}\n"
              "[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n    y = x\n}\n")
    stage = elaborate_text(source).calibrate({"r": value})
    assert stage.bindings.calibration["r"] == value
    answer = stage.encoding()
    assert answer["bindings"]["calibration"]["r"] == {"$bellman": ["float", spelling]}
    assert json.loads(json.dumps(answer, allow_nan=False)) == json.loads(str(answer)) == answer
    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    Draft202012Validator(schema).validate(answer)


@pytest.mark.parametrize("spelling", ("inf", "-inf", "nan"))
def test_encoding_distinguishes_nonfinite_provenance_strings_and_reserved_mappings(path_of, spelling):
    import json
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    tag = {"$bellman": ["float", spelling]}
    escaped = {"$bellman": ["mapping", [["$bellman", ["float", spelling]]]]}
    escaped_again = {"$bellman": ["mapping", [["$bellman", escaped["$bellman"]]]]}
    nested = {"plain": [float(spelling), spelling, tag], "$bellman": escaped}
    expected_nested = {"$bellman": ["mapping", [
        ["plain", [tag, spelling, escaped]],
        ["$bellman", escaped_again],
    ]]}
    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    validator = Draft202012Validator(schema)
    encodings = []
    for value, expected in ((float(spelling), tag), (spelling, spelling),
                            (tag, escaped), (nested, expected_nested)):
        stage = elaborate_stage({**load_stage(path_of("cons")), "provenance": {"review_value": value}})
        answer = stage.encoding()
        assert answer["provenance"]["review_value"] == expected
        strict = json.dumps(answer, allow_nan=False, sort_keys=True)
        assert json.loads(strict) == json.loads(str(answer)) == answer
        validator.validate(answer)
        encodings.append(strict)
    assert len(set(encodings)) == len(encodings)


@pytest.mark.parametrize("spelling", ("inf", "-inf", "nan"))
def test_encoding_recurses_through_reserved_method_and_configured_values(cons, spelling):
    import json
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    # the components typed at the decision builder's Evaluation, the grid
    # naming the settings, and a configured value that is no finite number
    # beside a mapping holding the reserved key
    stage = copy_native(cons).methodize({
        "text": ("@methods: cons\n"
                 "n_points : ℕ\nm_min : ℝ₊\nm_max : ℝ₊\n"
                 "cntn_to_dcsn.evaluate.method : !Linear\n"
                 'cntn_to_dcsn.evaluate.handler : "test:interpolate"\n'
                 "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_points))\n"),
        "origin": "cons.methods.bl"})
    tag = {"$bellman": ["float", spelling]}
    configured = stage.configure({"n_points": 8, "m_min": 0.1, "m_max": 10.0, "n_m": float(spelling),
                                  "extra": {"$bellman": ["float", spelling]}})
    answer = configured.encoding()
    assert answer["bindings"]["settings"] == {
        "n_points": 8, "m_min": 0.1, "m_max": 10.0, "n_m": tag,
        "extra": {"$bellman": ["mapping", [["$bellman", ["float", spelling]]]]}}
    # the components by place: the method word and the grid as terms, the
    # handler's program; and the same within the builder's box, at the place
    components = answer["bindings"]["methods"]["cntn_to_dcsn.evaluate"]
    assert components["method"] == {"__class__": "Word", "name": "Linear", "arguments": []}
    assert components["grid"]["__class__"] == "Cartesian"
    assert [factor["coordinate"] for factor in components["grid"]["factors"]] == ["m_d"]
    assert components["handler"] == "test:interpolate"
    builder = next(box for box in answer["builders"]["backward"]["boxes"]
                   if box["name"] == "cntn_to_dcsn")
    assert builder["methods"] == [{"at": "cntn_to_dcsn.evaluate", **components}]
    assert json.loads(json.dumps(answer, allow_nan=False)) == json.loads(str(answer)) == answer
    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    validator = Draft202012Validator(schema)
    validator.validate(answer)
    builder["methods"][0]["$bellman"] = ["float", spelling]
    assert not validator.is_valid(answer)


# the versions whose encodings the freshness sweep reads, one test for each:
# the five symbolic corpus stages and the four bound versions of `cons`, each
# a fixture of the session (AMD-SG-034 plan-addendum item 20)
ENCODED_VERSIONS = ("cons", "port", "ez_savings", "cons_savings_iid", "sa_savings",
                    "cons_calibrated", "cons_methodized", "cons_configured", "cons_methods_only")


@pytest.mark.sweep
@pytest.mark.parametrize("name", ENCODED_VERSIONS)
def test_encodings_are_fresh_strict_json_for_symbolic_and_bound_stages(name, request):
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    stage = request.getfixturevalue(name)
    answer = stage.encoding()
    assert json.loads(json.dumps(answer, allow_nan=False)) == json.loads(str(answer)) == answer
    validator.validate(answer)
    assert repr(answer) == str(answer)
    assert str(answer) == json.dumps(answer, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
    again = stage.encoding()
    assert again == answer and again is not answer
    answer["definitions"].clear()
    assert stage.encoding() == again


def test_the_methods_and_configured_versions_encode_their_components_and_bindings(
        cons_configured, cons_methods_only):
    """The encoding of the methods-only version of `cons` names its version
    and, within the decision builder's box, the components typed at its
    Evaluation with the grid the addition writes. The configured version
    records the bound settings and is a valid document under the schema."""

    # the methods-only version is the session's (AMD-SG-034 plan-addendum item 20)
    methods_only = cons_methods_only
    encoded = methods_only.encoding()
    assert encoded["version"] == "methods"
    builder = next(box for box in encoded["builders"]["backward"]["boxes"]
                   if box["name"] == "cntn_to_dcsn")
    components = builder["methods"][0]
    assert (components["at"], components["method"]["name"]) == ("cntn_to_dcsn.evaluate", "Linear")
    assert [factor["coordinate"] for factor in components["grid"]["factors"]] == ["m_d"]
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    configured = cons_configured.encoding()
    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    Draft202012Validator(schema).validate(configured)
    assert configured["version"] == "specified"
    assert configured["bindings"]["settings"] == dict(cons_configured.bindings.settings)


def test_encoding_schema_rejects_unknown_fields_and_inconsistent_method_versions(cons, cons_configured):
    from importlib.resources import files
    from jsonschema import Draft202012Validator

    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    validator = Draft202012Validator(schema)
    symbolic = cons.encoding()
    symbolic["builders"]["backward"]["boxes"][0]["methods"] = []
    assert not validator.is_valid(symbolic)
    bound = cons_configured.encoding()
    del bound["builders"]["backward"]["boxes"][0]["methods"]
    assert not validator.is_valid(bound)
    bound = cons_configured.encoding()
    bound["provenance"]["parent"]["text"] = "source text"
    assert not validator.is_valid(bound)
    for path in ((), ("definitions", 0), ("definitions", 0, "equations", 0),
                 ("builders", "backward", "boxes", 0), ("builders", "backward", "wires", 0),
                 ("bindings",), ("obligations", 0), ("diagnostics",)):
        changed = cons.encoding()
        target = changed
        for key in path:
            target = target[key]
        target["unknown"] = None
        assert not validator.is_valid(changed), path


def test_calibration_reports_evidence_and_preserves_pending_conditions(
        cons, port, ez_savings, cons_savings_iid, sa_savings, cons_calibrated, cons_methodized):
    from bellman.native import predicates as P

    for stage, status in ((cons, "required"), (cons_calibrated, "established")):
        item, = [o for o in stage.obligations() if o.condition == "arithmetic-definedness"
                 and str(o.entries[0]) == "cons:function:𝑢"]
        assert item.status == status
        assert item.evidence == (("calibration ρ = 6.0",) if status == "established" else ())
        predicate = item.entries[1]
        assert isinstance(predicate, P.Not)
        assert S.format_expression(predicate, width=None) == "¬(1 − ρ = 0)"
    forbidden = {
        "single-valuedness", "measurable-selection", "reverse-solution-coverage",
        "measurable-law-of-motion", "measurable-policy",
        "input-derivative-compatibility", "total-mass-preservation",
    }
    pending_conditions = {"expectation-integrability", "aggregation-admissibility", "optimality"}
    for stage in (cons, port, ez_savings, cons_savings_iid, sa_savings, cons_calibrated, cons_methodized):
        listing = " ".join(str(stage.obligations()).split())
        for item in stage.obligations():
            # a condition is listed by the term it holds, and by its sentence
            # where it holds none (AMD-SG-034 §10 item 5)
            text = (S.format_expression(item.predicate, width=None) if item.predicate is not None
                    else item.explanation)
            assert text
            assert item.condition in listing and " ".join(text.split()) in listing
            if item.condition in pending_conditions:
                assert item.status == "required"
        assert not {item.condition for item in stage.obligations()} & forbidden


def test_calibration_leaves_state_predicates_required_and_preserves_prior_evidence(elaborate_text):
    from bellman.native import predicates as P

    source = """@stage: parameters
ρ : ℝ
η : ℝ
[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {
    y = 1/(ρ-η) + 1/x :: [id=value]
}
"""
    stage = elaborate_text(source)
    bound = stage.calibrate({"ρ": 3.0, "η": 2.0, "x": 4.0})
    arithmetic = [o for o in bound.obligations() if o.condition == "arithmetic-definedness"]
    assert {o.status for o in arithmetic} == {"required", "established"}
    proved, = [o for o in arithmetic if o.status == "established"]
    assert proved.evidence == ("calibration ρ = 3.0, η = 2.0",)
    assert isinstance(proved.entries[1], P.Not)
    assert S.format_expression(proved.entries[1], width=None) == "¬(ρ − η = 0)"
    pending, = [o for o in arithmetic if o.status == "required"]
    assert pending.evidence == ()
    assert isinstance(pending.entries[1], P.Not)
    # the condition is owned by the push-forward and spelled as its card
    # spells the arrival state (second round, R2)
    assert S.format_expression(pending.entries[1], width=None) == "¬(x≺ = 0)"
    for version in (stage, bound):
        with pytest.raises(ValueError, match="ρ.*η"):
            version.calibrate({"ρ": 2.0, "η": 2.0})
    assert proved.evidence == ("calibration ρ = 3.0, η = 2.0",)
    assert [o for o in bound.obligations() if o.condition == "arithmetic-definedness"] == arithmetic


def test_calibration_decides_parameter_powers_and_leaves_input_predicates_required(elaborate_text):
    source = """@stage: parameters
ρ : ℝ
η : ℝ
[id=b, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {
    y = ρ^η + x :: [id=value]
}
"""
    power = elaborate_text(source)
    # the exponent's declared range ℝ leaves a non-integer exponent possible,
    # so the condition is the base's positivity (AMD-SG-034 second round,
    # R2): a positive base is established, a zero or negative base refused
    # whatever the exponent's value
    for rho, eta in ((2.0, 0.5), (2.0, 2.0)):
        version = power.calibrate({"ρ": rho, "η": eta})
        arithmetic = [o for o in version.obligations() if o.condition == "arithmetic-definedness"]
        assert arithmetic and all(o.status == "established" for o in arithmetic)
    for rho, eta in ((0.0, 0.0), (0.0, -1.0), (-2.0, 0.5), (0.0, 2.0), (-2.0, 2.0)):
        with pytest.raises(ValueError):
            power.calibrate({"ρ": rho, "η": eta})
    extended = elaborate_text(source.replace("ρ : ℝ", "ρ : ℝ̄"))
    decided = [o for o in extended.calibrate({"ρ": 2.0, "η": 0.5}).obligations()
               if o.condition == "arithmetic-definedness"]
    assert decided and all(o.status == "established" for o in decided)
    for text in (source.replace("ρ^η + x", "x^ρ"),
                 source.replace("[id=b", "f(ρ : ℝ) := 1/ρ\n[id=b").replace("ρ^η + x", "f(x)")):
        version = elaborate_text(text).calibrate({"ρ": 2.0, "η": 1.0})
        arithmetic = [o for o in version.obligations() if o.condition == "arithmetic-definedness"]
        assert arithmetic and all(o.status == "required" for o in arithmetic)


def test_command_prints_the_public_view_encoding_dossier_and_refusal_catalogue(cons, path_of):
    from bellman.refusal_catalogue import catalogue
    from bellman.dossier import dossier
    from conftest import ROOT

    path = path_of("cons").relative_to(ROOT)
    command = [sys.executable, "-m", "bellman"]
    for arguments, expected in (
        ([str(path)], cons.view() + "\n"),
        ([str(path), "--encoding"], str(cons.encoding()) + "\n"),
        ([str(path), "--dossier"], "\n".join(dossier(ROOT / path, with_source=True)) + "\n"),
        (["--refusals"], str(catalogue()) + "\n"),
    ):
        answer = subprocess.run(command + arguments, cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", timeout=60)
        assert answer.returncode == 0, answer.stderr
        assert not answer.stderr
        assert answer.stdout == expected
        if "--encoding" in arguments:
            assert json.loads(answer.stdout) == cons.encoding()


def test_the_dossier_reports_a_period_file_that_writes_a_key_twice_on_its_period_line(tmp_path):
    import shutil
    from bellman.dossier import period_lines

    (tmp_path / "stages" / "disc").mkdir(parents=True)
    shutil.copy(ROOT / "applications/portfolio-choice/declaration/stages/disc/disc.bl",
                tmp_path / "stages" / "disc" / "disc.bl")
    once, twice = tmp_path / "once.yml", tmp_path / "twice.yml"
    once.write_text("stages: [disc]\nconnectors: []\n", encoding="utf-8")
    twice.write_text("stages: [disc]\nconnectors: []\nconnectors: []\n", encoding="utf-8")
    assert period_lines(once)[-1].endswith("the stages the period names elaborate")
    # the one YAML reader refuses a key written twice, which YAML alone reads as its last value
    assert period_lines(twice)[-1].endswith("the period is refused under the rule trellis-file-shape")


def test_the_dossier_reads_the_stage_files_of_a_period_at_the_paths_its_recipe_writes():
    """The period file of the durables registry names `tenure`, `keeper_cons`
    and `adjuster_cons`, whose files stand in their stage folders under
    `stages/` and not beside the period file; the recipe whose trellis file
    names the period file writes their paths, and the period line says that
    the three stages elaborate as one period. The period file of the
    two-stage route is named by the other recipe's trellis file, and is read
    through that recipe."""
    from bellman.dossier import period_lines

    folder = ROOT / "applications/durables/declaration"
    for key in ("tenure", "keeper_cons", "adjuster_cons"):
        assert (folder / "stages" / key / f"{key}.bl").is_file() and not (folder / f"{key}.bl").exists()
    for period in ("period.yml", "period.two-stages.yml"):
        assert period_lines(folder / period)[-1].endswith("the stages the period names elaborate")


# --- The mathematical encoding (AMD-SG-029) and the joint policy (AMD-SG-030):
# moved from their acceptance files with their
# assertions unchanged, as the second layer of the tests
# (`packages/bellman/README.md` §8) requires once the next amendment is merged
# (22 September 2026).

def _trees_of_encoding(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _trees_of_encoding(child)
    elif isinstance(value, list):
        for child in value:
            yield from _trees_of_encoding(child)


def _variable_of_encoding(name):
    return ResolvedName(name, value_type=ExpressionType("scalar", "primitive:real"), role="state", perch=None)


def _nested_of_encoding(first, second, returned):
    x, y = _variable_of_encoding(first), _variable_of_encoding(second)
    return S.Lambda(((x, T.Named("ℝ")),), S.Lambda(((y, T.Named("ℝ")),),
                    T.Sym(T.Constant(returned))))


def _exact_of_encoding(value):
    if isinstance(value, list):
        return [_exact_of_encoding(item) for item in value]
    if isinstance(value, dict):
        if set(value) == {"identities", "value"}:
            part = _exact_of_encoding(value["value"])
            table = {row["id"]: row for row in value["identities"]}
            names = {node["id"] for node in _trees_of_encoding(part) if node.get("ref") == "document"}
            pending = list(names)
            while pending:
                for node in _trees_of_encoding(table[pending.pop()]):
                    if node.get("ref") == "document" and node["id"] not in names:
                        names.add(node["id"])
                        pending.append(node["id"])
            return {"value": part, "identities": [table[name] for name in sorted(names)]}
        return {key: _exact_of_encoding(item) for key, item in value.items() if key not in ("method", "methods")}
    return value


def test_operator_parts_and_bound_scopes_are_preserved(
        cons, port, ez_savings, cons_savings_iid, sa_savings, corpus_encodings):
    from bellman.display.encoding_checks import operators

    # the encodings are the session's (AMD-SG-034 plan-addendum item 20)
    for name, stage in zip(("cons", "port", "ez_savings", "cons_savings_iid", "sa_savings"),
                           (cons, port, ez_savings, cons_savings_iid, sa_savings)):
        document = json.loads(json.dumps(corpus_encodings[name], allow_nan=False))
        rows = {row["address"]: row for row in operators(document)}
        for graph in (stage.builder.bwd, stage.builder.fwd):
            for name in graph.primitives.list():
                answer = graph.primitives[name].denote()
                parts = encode_answer(answer)["value"]["fields"]
                row = rows[answer.title.address]
                assert row["rule"] == parts["expression"]
                assert row["inputs"] == parts["inputs"]
                assert row["outputs"] == parts["outputs"]
                assert row["conditions"] == parts["conditions"]
        aliases = [node for node in _trees_of_encoding(document["derived"])
                   if node.get("node") == "records.WireType"]
        for node in aliases:
            assert all(name.get("ref") == "document"
                       for name, _ in node["fields"]["declarations"])
    outer = encode_answer(_nested_of_encoding("x", "y", "x"))
    inner = encode_answer(_nested_of_encoding("x", "y", "y"))
    renamed = encode_answer(_nested_of_encoding("a", "b", "a"))
    assert outer != inner
    assert outer == renamed
    assert {"ref": "bound", "depth": 1, "position": 0} in list(_trees_of_encoding(outer))
    x = _variable_of_encoding("x")
    integral = S.Integral((x, T.Named("ℝ")), T.Sym(T.Constant("x")),
                          T.Sym(T.Constant("x")))
    data = encode_answer(integral)["value"]
    assert data["outside"][1]["fields"]["symbol"]["fields"]["name"]["ref"] == "unresolved"
    assert data["body"][0]["fields"]["symbol"]["fields"]["name"]["ref"] == "bound"
    for head in ("forall", "exists"):
        quantified = T.Operator(head, (T.In(x, T.Named("ℝ")),),
                                (T.Sym(T.Constant("x")),))
        renamed = T.Operator(head, (T.In(_variable_of_encoding("y"), T.Named("ℝ")),),
                             (T.Sym(T.Constant("y")),))
        assert encode_answer(quantified) == encode_answer(renamed)
    bounded = T.Comprehension(x, T.Named("ℝ"),
                             (T.Rel(T.Sym(T.Constant("x")), T.Ge(), T.Number(0)),
                              T.Rel(T.Sym(T.Constant("x")), T.Le(), T.Number(1))))
    assert encode_answer(bounded) != encode_answer(replace(bounded, conds=bounded.conds[::-1]))
    for head in ("D", "E", "argmax", "solve"):
        left = T.Operator(head, (T.Var("x"),), (T.Sym(T.Constant("f")),))
        right = replace(left, subs=(T.Var("y"),))
        assert encode_answer(left) != encode_answer(right)
        assert encode_answer(left)["value"]["node"] == "terms.Operator"
        assert "fields" in encode_answer(left)["value"]
        enclosed = encode_answer(S.Lambda(((_variable_of_encoding("x"), T.Named("ℝ")),), left))
        index = enclosed["value"]["body"][0]["fields"]["subs"][0]["fields"]["name"]
        assert index == {"ref": "unresolved", "target": "x", "reason": "definition not retained"}

    x, y, z, w = map(_variable_of_encoding, ("x", "y", "z", "w"))
    second_domain = T.Add(T.Sym(T.Constant("z")), T.Sym(T.Constant("x")))
    quantified = T.Operator(
        "forall", (T.In(z, T.Named("ℝ")), T.In(w, second_domain)),
        (T.Sym(T.Constant("w")),))
    nested = S.Lambda(
        ((x, T.Named("ℝ")),),
        T.Comprehension(T.Group(y, (quantified,)), T.Named("ℝ"), ()))
    comprehension = encode_answer(nested)["value"]["body"][0]
    operator = comprehension["shape"]["fields"]["classifiers"][0]
    references = [(node["depth"], node["position"]) for node in _trees_of_encoding(operator["outside"][2])
                  if node.get("ref") == "bound"]
    assert references == [(0, 0), (2, 0)]
    coordinate = T.Coordinate(_variable_of_encoding("x"), None, ())
    positive = replace(coordinate, stem=replace(coordinate.stem,
        value_type=ExpressionType("scalar", "primitive:positive-real")))
    assert encode_answer(coordinate) != encode_answer(positive)
    joint = T.Operator("argmax", (T.In("c", T.Named("C")),
        T.In("h", T.Comprehension("x", T.Named("ℝ"), (
            T.Rel(T.Sym(T.Constant("x")), T.Le(), T.Sym(T.Constant("c"))),)))),
        (T.Add(T.Sym(T.Constant("c")), T.Sym(T.Constant("h"))),))
    later_domain = encode_answer(joint)["value"]["outside"][2]
    assert {"ref": "bound", "depth": 1, "position": 0} in list(_trees_of_encoding(later_domain))
    renamed = T.Operator("argmax", (T.In("a", T.Named("C")),
        T.In("b", T.Comprehension("x", T.Named("ℝ"), (
            T.Rel(T.Sym(T.Constant("x")), T.Le(), T.Sym(T.Constant("a"))),)))),
        (T.Add(T.Sym(T.Constant("a")), T.Sym(T.Constant("b"))),))
    assert encode_answer(joint) == encode_answer(renamed)


def test_validation_rejects_bad_references_scopes_and_graph_inputs(
        cons, port, ez_savings, cons_savings_iid, sa_savings, corpus_encodings):
    from bellman.display.encoding_checks import validate_encoding

    # the encodings are the session's (AMD-SG-034 plan-addendum item 20); the
    # broken copies below are deep copies of the original
    for name in ("cons", "port", "ez_savings", "cons_savings_iid", "sa_savings"):
        validate_encoding(corpus_encodings[name])
    original = corpus_encodings["cons"]
    initial = original["initial_diagrams"]["backward"]
    policy = next(index for index, box in enumerate(initial["boxes"]) if box["name"] == "policy")
    broken = deepcopy(original)
    ref = next(node for node in _trees_of_encoding(broken["derived"]) if node.get("ref") == "document")
    ref["id"] = "missing-declaration"
    with pytest.raises(ValueError):
        validate_encoding(broken)
    broken = deepcopy(original)
    scoped = next(node for node in _trees_of_encoding(broken["derived"])
                  if node.get("node") == "semantic.Lambda")
    scoped["outside"].append(None)
    with pytest.raises(ValueError):
        validate_encoding(broken)
    broken = deepcopy(original)
    scoped = next(node for node in _trees_of_encoding(broken["derived"])
                  if node.get("node") == "semantic.Lambda")
    scoped["shape"] = [None]
    with pytest.raises(ValueError):
        validate_encoding(broken)
    broken = deepcopy(original)
    broken["derived"]["structural_sources"]["builders"]["backward"].append(
        {"path": [], "kind": "Spider", "outputs": []})
    with pytest.raises(ValueError):
        validate_encoding(broken)
    broken = deepcopy(original)
    record = next(node for node in _trees_of_encoding(broken["derived"])
                  if node.get("node") == "records.WireType")
    record["fields"]["invented"] = None
    with pytest.raises(ValueError):
        validate_encoding(broken)
    broken = deepcopy(original)
    ref = next(node for node in _trees_of_encoding(broken["derived"]) if node.get("ref") == "bound")
    ref["depth"] = 999
    with pytest.raises(ValueError):
        validate_encoding(broken)
    broken = deepcopy(original)
    broken["builders"]["backward"]["boxes"][0]["in"].append("missing-wire")
    with pytest.raises(ValueError):
        validate_encoding(broken)
    broken = deepcopy(original)
    table = broken["derived"]["stage"]["identities"]
    duplicate = deepcopy(table[0])
    duplicate["fields"]["stage"] = "different-stage"
    table.append(duplicate)
    with pytest.raises(ValueError):
        validate_encoding(broken)


def test_the_standalone_reader_needs_no_bellman_import(cons, tmp_path):
    from bellman.display import encoding_checks
    import jsonschema

    path = tmp_path / "cons.json"
    path.write_text(json.dumps(cons.encoding(), ensure_ascii=False))
    program = ("import importlib.util,runpy,sys; sys.path.append(sys.argv.pop(1)); "
               "assert importlib.util.find_spec('bellman') is None; "
               "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')")
    result = subprocess.run([sys.executable, "-I", "-S", "-c", program,
                             str(Path(jsonschema.__file__).parents[1]),
                             str(Path(encoding_checks.__file__)), str(path)],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    rows = json.loads(result.stdout)
    address = cons.builder.bwd["cntn_to_dcsn", "Pullback"].denote().title.address
    row = next(row for row in rows if row["address"] == address)
    assert row["kind"] == "Pullback"
    assert row["rule"]["node"] == "semantic.Lambda"
    assert row["inputs"] and row["outputs"]


def test_calibration_preserves_encoded_equations_and_changed_rules_remain_distinct(cons, cons_calibrated):
    symbolic = cons.encoding()
    calibrated = cons_calibrated.encoding()
    assert symbolic["definitions"] == calibrated["definitions"]
    assert symbolic["bindings"]["calibration"] != calibrated["bindings"]["calibration"]
    assert symbolic["obligations"] != calibrated["obligations"]
    from bellman.display.encoding_checks import operators
    assert [row["rule"] for row in operators(symbolic)] == [
        row["rule"] for row in operators(calibrated)]
    answer = cons.builder.bwd["cntn_to_dcsn", "Pullback"].denote()
    changed = replace(answer, expression=T.Number(0))
    assert _exact_of_encoding(encode_answer(answer)) != _exact_of_encoding(encode_answer(changed))


def test_detached_encoding_uses_no_display(cons, monkeypatch):
    answer = cons.builder.bwd["cntn_to_dcsn"].denote()
    expected = encode_answer(answer)

    def forbidden(*args, **kwargs):
        pytest.fail("mathematical encoding invoked a display")

    monkeypatch.setattr(S, "format_expression", forbidden)
    from bellman.display import cards
    from bellman.syntax import layout
    monkeypatch.setattr(layout, "render", forbidden)
    monkeypatch.setattr(cards, "card_body_lines", forbidden)
    monkeypatch.setattr(cards, "card_of", forbidden)
    assert encode_answer(answer) == expected
    assert json.loads(json.dumps(expected, allow_nan=False)) == expected




def test_the_controls_are_written_as_one_bundle(adjuster_cons):
    policy = adjuster_cons.builder.bwd["policy"]
    signature = str(policy.signature())
    # a name prints as the author spelled it, the subscript not italicised (AMD-SG-034 critique F11)
    assert "(𝑐(m, z_d), ℎ_choice(m, z_d)) : 𝒫(" in signature
    assert signature.count("𝒫(") == 1
    card = str(policy.denote())
    assert "joint relation projection" not in card
    assert "joint solution candidate representation" not in card
    assert all(len(line) <= 78 for line in card.splitlines())
    for builder in (adjuster_cons.dcsn.builder.bwd, adjuster_cons.dcsn.builder.fwd):
        answer = builder.denote()
        assert all("joint relation projection" not in str(piece.record.kernel)
                   for piece in answer.pieces if piece.record.kernel is not None)


# --- AMD-SG-034 §4 items 1, 10, 11 and 12: precedence and the layout engine ---


def _sym(name):
    return T.Sym(T.Constant(name))


def test_expressions_print_with_precedence(cons, cons_explicit):
    """A parenthesis stands only where a child binds looser than the position
    it is in (AMD-SG-034 §4 item 1): `𝑢` of cons prints `c^(1 − ρ)/(1 − ρ)`,
    a map prints its binders by name (§4 item 12) and a name at a perch carries
    its mark directly after the letter (§4 item 11)."""
    cons = cons_explicit
    [utility] = cons.definitions.denote("cons:function:𝑢").denoted
    assert S.format_expression(utility.expression.body, width=None) == "c^(1 − ρ)/(1 − ρ)"
    assert S.format_expression(utility.expression, width=None) == "c ↦ c^(1 − ρ)/(1 − ρ)"
    [inverse] = cons.definitions.denote("cons:function:𝑑𝑢𝑖𝑛𝑣").denoted
    # a quotient under a sign keeps no parentheses of its own (critique F12)
    assert S.format_expression(inverse.expression.body, width=None) == "x^(−1/ρ)"
    [correspondence] = cons.definitions.denote("cons:correspondence:Γ").denoted
    assert S.format_expression(correspondence.expression, width=None) == "x ↦ (0, x]"
    [law] = cons.definitions.denote("cons:g:dcsn_to_cntn").denoted
    assert S.format_expression(law.expression.body, width=None) == "m_d − c"
    aggregation = cons.builder.bwd["cntn_to_dcsn", "Aggregation"].denote()
    carriers = "\n".join(str(denoted.mathematical_type) for denoted in aggregation.kernel.denoted)
    # the composition with the law of motion is a held term, `V≻ ∘ 𝑔`, and
    # no suffix of a name (unit 2), so the aggregator's argument is `V≻`
    assert "V≻" in carriers and "∘𝑔" not in carriers and "[>]" not in carriers


def test_the_eight_asymmetric_cases_keep_their_parentheses():
    """The parentheses the tree needs remain (§4 item 1): the right operand of
    a subtraction or a division, a sign inside a power and a power's base under
    a sign, a subtraction inside a subtraction, the objective of an argmax and
    the body of a quantifier; the mirror image of each drops them."""
    from bellman.native import predicates as P
    a, b, c, rho = (_sym(letter) for letter in "abcρ")
    one, two = T.Number(1), T.Number(2)
    kept = {
        "a − (b − c)": T.Sub(a, T.Sub(b, c)),
        "a/(b · c)": T.Div(a, T.Mul(b, c)),
        "a/(b/c)": T.Div(a, T.Div(b, c)),
        "(−c)²": T.Pow(T.Neg(c), two),            # an integer exponent as superscript digits (critique F12)
        "c^(−ρ)": T.Pow(c, T.Neg(rho)),
        "a − (b + c)": T.Sub(a, T.Add(b, c)),
        "argmax_{c ∈ Γ(a)} [𝑢(c) + b]": T.Operator(
            "argmax", (T.In("c", T.Call("Γ", (a,))),), (T.Add(T.Call("𝑢", (c,)), b),)),
        "∀ x ∈ ℝ₊₊: (a = b ∧ b ≤ c)": T.Operator(
            "forall", (T.In("x", T.Named("ℝ₊₊")),),
            (T.Rel(a, T.Eq(), b), T.Rel(b, T.Le(), c))),
    }
    dropped = {
        "a − b − c": T.Sub(T.Sub(a, b), c),
        "a/b/c": T.Div(T.Div(a, b), c),
        "a/b · c": T.Mul(T.Div(a, b), c),
        "−c²": T.Neg(T.Pow(c, two)),
        "−a · b": T.Mul(T.Neg(a), b),
        "a − b + c": T.Add(T.Sub(a, b), c),
        "a − b = 0": T.Rel(T.Sub(a, b), T.Eq(), T.Number(0)),
        "a = b ∧ b ≤ c": P.And(P.Compare(a, "=", b), P.Compare(b, "<=", c)),
        "(a = b ∨ b = c) ∧ c = a": P.And(
            P.Or(P.Compare(a, "=", b), P.Compare(b, "=", c)), P.Compare(c, "=", a)),
        "¬(1 − ρ = 0)": P.Not(P.Compare(T.Sub(one, rho), "=", T.Number(0))),
        "a − b ∈ ℝ₊": P.Member(T.Sub(a, b), T.Named("ℝ₊")),
        "a + (−b)": T.Add(a, T.Neg(b)),
        "−(−a)": T.Neg(T.Neg(a)),
        "(a^b)^c": T.Pow(T.Pow(a, b), c),
        "pi ∈ (ℝ₊₊ → ℝ₊₊)": P.Member(_sym("pi"), S.FunctionSet(T.Named("ℝ₊₊"), T.Named("ℝ₊₊"))),
        "(ℝ₊₊ → ℝ) × (ℝ₊₊ → ℝ₊₊)": T.Product(
            (S.FunctionSet(T.Named("ℝ₊₊"), T.Named("ℝ")), S.FunctionSet(T.Named("ℝ₊₊"), T.Named("ℝ₊₊")))),
    }
    for expected, term in {**kept, **dropped}.items():
        assert S.format_expression(term, width=None) == expected
    assert len(kept) == 8


def test_the_argmax_objective_stands_in_square_brackets(cons, cons_explicit):
    """The maximand of `argmax`, `max` and `sup` and the operand of a sum, an
    expectation and an integral stand in square brackets (§10 item 2); any
    other operator keeps its parentheses."""
    objective = cons.definitions["policy.optimality"].equations[0].rhs
    assert S.format_expression(objective, width=None) == "argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + V[>]]"
    expectation = T.Operator("E", (T.Var("y"), T.Var("z")), (T.Mul(_sym("β"), _sym("W")),))
    # the operand of an expectation follows its head directly (critique, second round, K5)
    assert S.format_expression(expectation, width=None) == "E_{y, z}[β · W]"
    solve = T.Operator("solve", (T.Var("ς"),), (T.Sub(_sym("a"), _sym("b")),))
    assert S.format_expression(solve, width=None) == "solve_{ς}(a − b)"
    # the one relation definition, which the identification instantiates over
    # the admitted pairs, writes the truth of its relation as a supremum
    identification = next(piece.record for piece in cons_explicit.builder.bwd["policy"].denote().pieces
                          if piece.record.kind == "Pullback")
    text = S.format_expression(identification.expression, width=None)
    assert "sup_{truth ∈ " in text and "} [truth]" in text and "} (truth)" not in text


def test_render_breaks_before_a_relation_with_the_continuation_under_the_right_hand_side():
    """The layout engine (§4 item 10): a relation that does not fit breaks
    before its sign, the continuation stands two columns in under the
    right-hand side and never at column zero, an inner group that fits stays on
    one line, and a margin note is set flush right where the line leaves room
    for it and on a line of its own under the text it notes where it does not,
    as the region note of a rule stands (`card-redesign.md` §2, change 2); the
    heavy line and the light line are drawn across the card (change 5)."""
    from bellman.syntax import layout
    left = T.Call("𝑐", (T.Call("𝑚_d≻", (_sym("a"),)),))
    term = T.Add(T.Call("𝑢", (_sym("cp"),)),
                 T.Call("𝑉≻", (T.Call("𝑔≻", (_sym("m_d"), _sym("cp"))),)))
    relation = T.Rel(left, T.Eq(), T.Add(T.Add(term, term), term))
    entry = layout.concat(" " * 14, layout.nest(14, S.format_document(relation)))
    lines = layout.render(entry, width=78).split("\n")
    assert lines[0] == " " * 14 + "𝑐(𝑚_d≻(a))"
    # a chain of sums is one group: its summands stay on one line while they
    # fit and break together, before every sign, when they do not (the
    # second round's K4)
    assert lines[1] == " " * 16 + "= 𝑢(cp)"
    assert lines[2] == " " * 18 + "+ 𝑉≻(𝑔≻(m_d, cp))"
    # a sum standing as a right operand keeps its parentheses (§4 item 1)
    assert lines[3] == lines[4] == " " * 18 + "+ (𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp)))" and len(lines) == 5
    assert all(len(line) <= 78 and line[0] == " " and not line.endswith(" ") for line in lines)
    short = T.Rel(left, T.Eq(), T.Call("𝑐≻", (_sym("a"),)))
    assert layout.render(S.format_document(short), width=78) == "𝑐(𝑚_d≻(a)) = 𝑐≻(a)"
    # the rule of the grid relation at the column of a rule's text, eleven,
    # with its region note against the right margin, as the drawing of
    # `cons.bl` sets it
    note = "on 𝑚_d≻(Xa)"
    noted = layout.render(layout.concat(" " * 11, layout.nest(
        11, S.format_document(short), layout.margin(note))), width=78)
    rule = "𝑐(𝑚_d≻(a)) = 𝑐≻(a)"
    assert noted == " " * 11 + rule + " " * (78 - 11 - len(rule) - len(note)) + note
    # a rule whose last line leaves no room for the note: the note stands on a
    # line of its own under the first character of the rule
    wide = T.Rel(left, T.Eq(), T.Add(_sym("a"), _sym("b" * 56)))
    bare = layout.render(layout.concat(" " * 11, layout.nest(11, S.format_document(wide))), width=78)
    assert len(bare.split("\n")[-1]) > 78 - 2 - len(note)
    own_line = layout.render(layout.concat(" " * 11, layout.nest(
        11, S.format_document(wide), layout.margin(note))), width=78).split("\n")
    assert own_line[:-1] == bare.split("\n") and own_line[-1] == " " * 11 + note
    assert layout.horizontal_line(layout.HEAVY) == "━" * 78 and layout.horizontal_line(layout.LIGHT) == "─" * 78
    assert layout.flat(S.format_document(relation)) == S.format_expression(relation, width=None)


# --- AMD-SG-034 unit 2: the policy's rules at the point; laws, distributions and the local abbreviations


def _rule_text(rule):
    """A held `Rule` printed as its statement, its clauses and its set."""
    text = S.format_expression(rule.statement, width=None)
    if rule.where:
        text += "  where " + " and ".join(S.format_expression(part, width=None) for part in rule.where)
    if rule.on is not None:
        text += "  on " + S.format_expression(rule.on, width=None)
    return text




def test_the_law_at_the_policy_is_written_out_and_the_builder_is_at_the_policy(cons, port):
    """The pulled-back value is the composition with the law of motion at
    the policy written out as a map of the point, `m_d ↦ 𝑔≻(m_d, 𝑐(m_d))`,
    which the card names `𝑉≻ ∘ 𝑔≻(·, 𝑐)`, a dot for each coordinate of the
    point and each policy by its name in the law's order; no abbreviation
    names the law or the aggregator at the policy, and no `where` entry
    defines one (RL14); each rule reads the composite written out; the
    builder is `at` the policy, typed as the policy builder types it
    (AMD-SG-034 §2 item 1, §4 item 6, §10 item 3)."""
    builder = cons.builder.bwd["cntn_to_dcsn"]
    record = builder.denote()
    [at] = record.at
    assert at.symbol == "𝑐" and str(at.identity) == "cons:function:dcsn:c"
    assert S.format_expression(at.mathematical_type.carrier, width=None) == (
        "{c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)}")
    assert record.where == ()
    pullback = builder["Pullback"].denote()
    composite = pullback.outputs[0].expression
    assert isinstance(composite, S.Compose) and isinstance(composite.inner, S.Lambda)
    assert S.format_expression(composite.inner.body, width=None) == "𝑔(m_d, c(m_d))"
    assert S.format_expression(composite, width=None) == "V≻ ∘ 𝑔(·, c)"
    [rule] = pullback.outputs[0].rules
    assert _rule_text(rule) == "(V≻ ∘ 𝑔(·, c))(m_d) = V≻(𝑔(m_d, c(m_d)))"
    aggregation = builder["Aggregation"].denote()
    assert S.format_expression(aggregation.outputs[0].expression, width=None) == (
        "m_d ↦ 𝑢(c(m_d)) + V≻(𝑔(m_d, c(m_d)))")
    printed = str(builder)
    for line in ("     in: 𝑉≻                             out: 𝑉≻ ∘ 𝑔≻(·, 𝑐)",
                 "     rule: (𝑉≻ ∘ 𝑔≻(·, 𝑐))(m_d) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))",
                 "     rule: 𝑉(m_d) = 𝑢(𝑐(m_d)) + 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))"):
        assert line in printed.splitlines(), line
    assert "Where" not in printed
    # the forward push-forward at the policy writes the same law out on its
    # own point, and its builder is at the same policy
    forward = cons.builder.fwd["dcsn_to_cntn"].denote()
    assert forward.where == () and forward.at == record.at
    # a point of several coordinates opens each of them where the law reads
    # it, the policy standing where the law reads the control: the
    # portfolio share read at the saving alone
    printed = str(port.builder.bwd["cntn_to_dcsn"]["Pullback"])
    assert "  out  𝑉≻ ∘ 𝑔≻(·, 𝜍, ·, ·)" in printed.splitlines()
    assert "  (𝑉≻ ∘ 𝑔≻(·, 𝜍, ·, ·))(k_d, Ψ, θ) = 𝑉≻(𝑔≻(k_d, 𝜍(k_d), Ψ, θ))" in printed.splitlines()


def test_no_printed_surface_names_the_law_at_the_policy(cons, port, printed_cards):
    """RL14 on every printed surface of `cons` and `port`: no card, no listing
    of a builder or of its pieces and no drawing of a graph or of a builder
    names a law of motion or an aggregator at the policy by a perch mark
    followed directly by a comma and the policy, the form the cards printed
    before RL14. The listings and the drawings
    write the law as they write it at no policy, `𝑔`, with the point left
    open, `𝑉≻∘𝑔(·, 𝑐)` and `𝑉≻ ∘ 𝑔(·, 𝑐)`, the push-forward along it,
    `𝑔(·, 𝑐)∗μ`, and the law read at the point, `𝑉≻(𝑔(m_d, 𝑐(m_d)))`; a
    drawing writes the aggregator at the policy the same way, a dot for
    each argument left open, `𝐺(·, ·, 𝑐)`."""
    named = re.compile(r"[≺≻],[^\s]")
    for stage in (cons, port):
        texts = [text for _, text, _ in printed_cards(stage.name)]
        for graph in (stage.builder.bwd, stage.builder.fwd):
            texts += [graph.diagram().source, graph.primitives.diagram().source]
            for name in graph.list():
                builder = graph[name]
                texts += [str(builder.signature()), str(builder.primitives.list()),
                          builder.diagram().source]
                texts += [str(builder.primitives[key].signature())
                          for key in builder.primitives.list()]
        found = [match.group(0) for text in texts for match in named.finditer(text)]
        assert found == [], (stage.name, found[:6])
    pullback = str(cons.builder.bwd["cntn_to_dcsn"]["Pullback"].signature())
    assert "𝑉≻∘𝑔(·, 𝑐) : Xm → [−∞, ∞)" in pullback
    backward = cons.builder.bwd.diagram().source
    for label in ("𝑉≻ ∘ 𝑔(·, 𝑐)", "𝐺(·, ·, 𝑐)"):
        assert f'label="{label}"' in backward, label
    # the pulled-back function read at the point, its label wrapped at the
    # drawing's width of a wire's label
    assert 'label="𝑉≻(𝑔(m_d,\\n𝑐(m_d)))"' in backward
    assert 'label="𝑔(·, 𝑐)∗μ"' in cons.builder.fwd.diagram().source
    assert 'label="𝑉≻ ∘ 𝑔(·, 𝜍, ·, ·)"' in port.builder.bwd.diagram().source
    assert 'label="𝐺(·, ·, 𝜍)"' in port.builder.bwd.diagram().source


def test_a_law_with_several_outputs_names_them_and_a_joint_solve_is_headed_by_its_unknowns(adjuster_cons):
    """The outputs of a law of motion are the continuation coordinates,
    stated once under `where`; a joint solve is one Aggregation headed by its
    unknowns, its residual lines named on its outputs before the head; the
    feasibility of a joint policy names each component by its control and
    the correspondences with the file's arguments (AMD-SG-034 §4 items 4, 6,
    8 and 9)."""
    from bellman.display.cards import Rule
    policy = adjuster_cons.builder.bwd["policy"]
    record = policy.denote()
    [outputs] = [item for item in record.where if isinstance(item, Rule)]
    assert _rule_text(outputs) == "(a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔(m, z_d, c, h_choice)"
    # the line forms one Aggregation, whose outputs are its two unknowns and
    # which has no residual input: each output holds the residual lines and
    # then the head (lane K of the internal developer release 0.01, KM1)
    solve = policy["choice:Aggregation"].denote()
    *residuals, head = solve.outputs[0].rules
    assert _rule_text(head) == "(c, h_choice) = solve_{c, h_choice}(r₁, r₂)"
    assert solve.outputs[1].rules == solve.outputs[0].rules
    assert not [wire for wire in solve.inputs if wire.residuals]
    # the residuals read the law's outputs by the names the line under Where
    # gives them, and the last residual carries the point of the solve in its
    # region note (lane C of the internal developer release 0.01, CL155)
    assert [_rule_text(line) for line in residuals] == [
        "r₁ = c − c≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)",
        "r₂ = (1 + τ) · 𝑢_c(c) − 𝑢_h(h_choice) − β · D_{h_nxt_adj}V≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)  on (m, z_d, c, h_choice) ∈ ℝ₊₊ × ℝ₊₊ × ℝ₊₊ × ℝ₊₊"]
    carrier = S.format_expression(solve.outputs[0].mathematical_type.carrier, width=None)
    assert carrier.endswith("| c(m, z_d) ∈ Γ_c(m) ∧ h_choice(m, z_d) ∈ Γ_h(m − c(m, z_d))})")
    assert "[1]" not in carrier and "[2]" not in carrier
    # no projection of the law's image is written anywhere on the builder
    pullback = policy["Pullback"].denote()
    for wire in pullback.outputs:
        assert isinstance(wire.expression, S.Compose)
        assert "[1]" not in S.format_expression(wire.definition, width=None)


def test_a_distribution_is_held_by_its_declared_law(buffer_stock, port):
    """An unconditional law is the law as the file writes it, a member of the
    probability measures on its support, with a `Mixture` unexpanded and no
    convention sentence; a conditioned law stays a kernel (AMD-SG-034 §4
    item 7, §10 item 7)."""
    # since 20 October 2026 a scalar law of a family the definitions define
    # denotes a second object, its measure at the written parameters
    [psi, psi_measure] = buffer_stock.definitions.denote("buffer_stock:distribution:ψ").denoted
    assert psi.symbol == "ψ" and str(psi.mathematical_type) == "probability measure on ℝ₊₊"
    assert S.format_expression(psi.expression, width=None) == "LogNormal(−σ_ψ²/2, σ_ψ)"
    assert psi_measure.symbol == "P_ψ" and isinstance(psi_measure.expression, S.Measure)
    [xi] = buffer_stock.definitions.denote("buffer_stock:distribution:ξ").denoted
    assert str(xi.mathematical_type) == "probability measure on ℝ₊"
    assert S.format_expression(xi.expression, width=None) == (
        "Mixture((p_zero, 0), (1 − p_zero, LogNormal(μ_ξ, σ_ξ)))")
    answer = buffer_stock.definitions.denote("buffer_stock:distribution:ψ")
    from bellman.display.cards import Textual
    assert not any(isinstance(item.expression, Textual) for item in answer.denoted)
    card = str(answer)
    assert re.search(r"^Defines\n  ψ\s+~\s+", card, re.M) and "(−σ_ψ²/2, σ_ψ)" in card
    assert "indicator" not in card
    # the joint law of port is held as the file writes it, its vector and
    # matrix parameters included (critique F1); the measure it constructs
    # is what stays outside the scalar rule
    [joint] = port.definitions.denote("port:distribution:Ψ_θ").denoted
    assert joint.symbol == "(Ψ, θ)"
    assert S.format_expression(joint.expression, width=None) == (
        "LogNormal((μ_Ψ, μ_θ), ((σ_Ψ², ρ_ζ · σ_Ψ · σ_θ), (ρ_ζ · σ_Ψ · σ_θ, σ_θ²)))")


def test_the_saving_stages_hold_two_control_policies_and_two_output_laws(
        worker_saving, retiree_saving, keeper_saving, adjuster_saving):
    """The four saving stages of Dobrescu and Shanker (2024) elaborate; their
    policies bind one function per control and their laws of motion name
    two outputs (AMD-SG-034 plan addendum item 18). The worker's two clause
    statements form one system whose rule reads the law of motion by
    reference, so the policy block defines no alias of the law (AMD-SG-035
    §3, E15), and the primitive definition of the system's Aggregation,
    euler_financial:Aggregation, stays unresolved (E19)."""
    from bellman.display.cards import Rule
    worker = worker_saving.builder.bwd["policy"].denote()
    carrier = S.format_expression(worker.outputs[0].mathematical_type.carrier, width=None)
    assert carrier.endswith("| c(m_f, m_p, w_d) ∈ Γ_c(m_f) ∧ c_p(m_f, m_p, w_d) ∈ Γ_p(w_d)})")
    # the outputs of the law the Pullback reads, at no policy (AMD-SG-034
    # §4 item 6)
    [outputs] = [item for item in worker.where if isinstance(item, Rule)]
    assert _rule_text(outputs) == "(y_f, y_p) = 𝑔(m_f, m_p, w_d, c, c_p)"
    assert not [item for item in worker.where if getattr(item, "identity", None) is not None
                and item.identity.kind == "alias"]
    assert isinstance(worker.outputs[0].definition, S.Unresolved)
    for stage in (retiree_saving, keeper_saving, adjuster_saving):
        record = stage.builder.bwd["cntn_to_dcsn"].denote()
        assert len(record.at) == 1
        assert [item for item in record.where if isinstance(item, Rule)]


def test_coordinate_occurrences_never_meet_for_any_number_of_ports(cons):
    """Two coordinates bound at different bases or places, or a coordinate
    and a variable at a literal position, never share an identity, whatever
    the number of ports (AMD-SG-034 unit 2, item f)."""
    from bellman.fold.stage_names import StageNames
    from bellman.stage.carriers import COORDINATE_OCCURRENCE_BASE, bound_variable_number
    ctx = StageNames(cons)
    ports = len(ctx.ports)
    seen = {}
    for base in (100, 130, 150, 200, 300, 310, 500, 600, 700):
        for place in range(ports + 1):
            occurrence = bound_variable_number(ctx, base, place)
            assert occurrence >= COORDINATE_OCCURRENCE_BASE
            assert occurrence not in seen, (seen[occurrence], (base, place))
            seen[occurrence] = (base, place)


# --- AMD-SG-034 unit 3: the doc line forms no piece; every condition a term; encoding 2.1


def test_the_doc_line_forms_no_piece_and_is_held_on_the_builder(cons, port, adjuster_cons, cons_explicit):
    """A line marked `!doc` forms no operation: no Argmax, and no Pullback of
    the value function or Aggregation of the objective that would serve one,
    is a piece of the policy builder of cons, and the objective's expectation
    is no piece of port's. The builder holds the line under `doc`, as written
    beside the line with the constructed output substituted, and no record
    holds it as a condition, since the obligation `optimality` is retired
    (AMD-SG-034 §3 `declared`, §10 item 1, §11 item 1; plan addendum item 2;
    lane K of the internal developer release 0.01, sub-brief §4)."""
    cons = cons_explicit
    policy = cons.builder.bwd["policy"]
    # a builder's doc line is not listed (unit 5, J17); it is reached by its key
    assert list(policy.primitives.list()) == [
        "InvEuler:Aggregation", "endoggrid:Aggregation", "cons_choice:Pullback", "Evaluation"]
    [declared] = policy.denote().doc
    assert declared.source.address == "policy.optimality" and declared.source.doc
    assert declared.source.text.startswith("c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])")
    assert S.format_expression(declared.statement, width=None) == (
        "c(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + V≻(𝑔(m_d, cp))]")
    assert not [item for item in cons.obligations() if item.condition == "optimality"]
    listing = str(cons.obligations())
    assert "maximisers" not in listing and "solutions of" not in listing
    assert "optimality" not in {item.condition for item in policy.denote().conditions}
    assert "optimality" not in {
        item.condition for item in policy["cons_choice:Pullback"].denote().conditions}
    # the feasibility the line declares is still read from it (§4 item 5)
    carrier = policy["Evaluation"].denote().outputs[0].mathematical_type.carrier
    assert S.format_expression(carrier, width=None) == "𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})"
    # port: the expectation of the objective stands in the statement as the
    # file writes it, and forms no piece
    port_policy = port.builder.bwd["policy"]
    assert not any("objective" in key for key in port_policy.primitives.list() if "Expectation" in key)
    [objective] = port_policy.denote().doc
    assert S.format_expression(objective.statement, width=None) == (
        "ς(k_d) ∈ argmax_{ς ∈ Γ_ς(k_d)} [E_{Ψ, θ}[V≻(𝑔(k_d, ς, Ψ, θ))]]")
    # a joint choice: the components by their controls and the correspondences
    # with the file's arguments (§4 items 4 and 8)
    [joint] = adjuster_cons.builder.bwd["policy"].denote().doc
    assert S.format_expression(joint.statement, width=None) == (
        "(c(m, z_d), h_choice(m, z_d)) ∈ argmax_{c ∈ Γ_c(m), h_choice ∈ Γ_h(m − c)}"
        " [𝑢(c, h_choice) + β · V≻(𝑔(m, z_d, c, h_choice))]")




@pytest.mark.sweep
@pytest.mark.parametrize("name", ("buffer_stock", "adjuster_cons", "worker_saving",
                                  "retiree_saving", "keeper_saving", "adjuster_saving"))
def test_the_encoding_names_the_one_schema_and_validates(name, request):
    """The encoding of each stage of the corpus outside the five recorded
    ones, one test for each, names the one schema, 2.6, and validates under it
    (the five are held by
    `test_validation_rejects_bad_references_scopes_and_graph_inputs`)."""
    from bellman.display.encoding_checks import validate_encoding
    document = request.getfixturevalue(name).encoding()
    assert document["schema"].endswith("/stage-encoding/2.6")
    validate_encoding(document)


# the two spellings (AMD-SG-035)

def test_a_body_declaration_and_a_two_bound_clause_lower_print_and_decode(cons_kt_text):
    term, _ = parse_with_spans(cons_obs_text(), "cons_obs.bl")
    declaration = dict(item_addresses(term))["policy.slackness"]
    assert isinstance(declaration, T.Declare) and isinstance(declaration.declaration, T.Complementary)
    assert to_source(declaration.declaration) == "μ[>] : ℝ₊ ⟂ a >= 0"
    chained = cons_kt_text.replace("⟂ m_d - c >= 0", "⟂ 0 <= m_d - c <= 1")
    core = dict(item_addresses(parse_with_spans(chained, "t.bl").term))["policy.euler"].core
    assert isinstance(core.bound, T.Between)
    assert to_source(core) == "𝑑𝑢(c) = D_{a}V[>] ⟂ 0 <= m_d - c <= 1"
    assert S.format_expression(core.bound) == "0 ≤ m_d − c ≤ 1"
    for text in (cons_obs_text(), chained):
        parsed, _ = parse_with_spans(text, "t.bl")
        assert from_json(to_json(parsed)) == parsed


def test_kuhn_tucker_states_the_sign_table_of_each_bound():
    """The slack of each kind of bound and the Kuhn–Tucker system of a
    relation and its bound, one line per kind of bound (AMD-SG-035 §2
    "Signs", §3; D13 for an inequality core)."""
    from bellman.stage.term_operations import kuhn_tucker
    from bellman.stage.term_operations import slack
    x, b, l, r = (T.Sym(T.Constant(name)) for name in ("x", "b", "l", "r"))
    zero = T.Number(0)
    assert slack(T.Rel(x, T.Ge(), zero)) == x
    assert slack(T.Rel(x, T.Le(), b)) == T.Sub(b, x)
    assert slack(T.Between(zero, T.Le(), x, T.Le(), b)) == (x, T.Sub(b, x))
    printed = lambda core, bound: S.format_expression(kuhn_tucker(core, bound), width=None)
    assert printed(T.Equation(l, r), T.Rel(x, T.Ge(), zero)) == "l − r ≥ 0 ∧ x ≥ 0 ∧ (l − r) · x = 0"
    assert printed(T.Equation(l, r), T.Rel(x, T.Le(), b)) == (
        "l − r ≤ 0 ∧ b − x ≥ 0 ∧ (l − r) · (b − x) = 0")
    assert printed(T.Equation(l, r), T.Between(zero, T.Le(), x, T.Le(), b)) == (
        "x ≥ 0 ∧ b − x ≥ 0 ∧ (l − r) · x ≤ 0 ∧ (l − r) · (b − x) ≥ 0")
    assert printed(T.Inequality(l, T.Le(), r), T.Rel(x, T.Ge(), zero)) == (
        "l − r ≤ 0 ∧ x ≥ 0 ∧ (l − r) · x = 0")


def test_the_two_spellings_encode_under_the_one_schema(cons_kt, worker_saving):
    """The encodings of the stages written with a clause name the one schema
    and validate against its file and by the reader (AMD-SG-035 review focus
    6)."""
    from importlib.resources import files
    from jsonschema import Draft202012Validator
    from bellman.display.encoding_checks import validate_encoding
    schema = json.loads(files("bellman.display").joinpath("stage-encoding-2.6.schema.json").read_text())
    for stage in (cons_kt, worker_saving):
        document = json.loads(json.dumps(stage.encoding()))
        assert document["schema"].endswith("/stage-encoding/2.6")
        Draft202012Validator(schema).validate(document)
        validate_encoding(document)


def test_a_clause_on_an_inequality_keeps_the_sign_the_line_writes(cons, cons_explicit):
    """D13: on the inequality candidate line of cons.bl, the rule of the
    line's Aggregation keeps the sign `≤` the line writes and holds the
    clause read at the grid point."""
    cons = cons_explicit
    card = str(cons.builder.policy)
    assert "     rule: 𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0\n" in card


def test_the_observable_domain_holds_a_bound_that_names_a_parameter():
    """D4, D11: a declaration's bound that names a parameter enters the
    observable set as written, beside the product of the multiplier with the
    bound's slack, on a continuation set on which the bound is not implied."""
    text = (cons_obs_text().replace("Xa := ℝ₊", "Xa := ℝ\nθ : ℝ₊")
            .replace("μ[>]   : ℝ₊ ⟂ a >= 0", "μ[>]   : ℝ₊ ⟂ a >= -θ"))
    card = str(stage_from_text(text, "cons_obs.bl").builder.policy)
    # the printer's spelling: the name of a set in roman (E39), the
    # coordinates bound as variables with no perch mark and listed as a
    # comprehension lists them (E38), the slack of `a ≥ −θ` as `a − (−θ)`
    assert "A≻,policy = {a, μ ∈ Xa × ℝ₊ | a ≥ −θ ∧ μ · (a − (−θ)) = 0}" in card


def test_a_multiplier_is_a_coordinate_of_its_block_alone_and_no_wire():
    """D3, §5: a declared multiplier is a field of the continuation perch with
    the role `multiplier` and a record of its own; it is a coordinate of its
    declaring block's grid alone, forms no wire, and its line prints once in
    the policy builder's `source` block."""
    stage = stage_from_text(cons_obs_text(), "cons_obs.bl")
    assert fields(stage)["cons_obs:cntn:μ"].role == "multiplier"
    assert [str(i) for i in stage.definitions.list()["multiplier"]] == ["cons_obs:multiplier:μ"]
    assert "μ[>]   : ℝ₊ ⟂ a >= 0" in str(stage.definitions.denote("cons_obs:multiplier:μ"))
    policy = stage.builder.policy
    assert [str(k) for k in policy.primitives.list()] == [
        "endoggrid:Aggregation", "cons_choice:Pullback", "Evaluation"]
    assert str(policy).count("μ[>]   : ℝ₊ ⟂ a >= 0") == 1
    from sheets_parse import parse_card, signature_wires
    decision = parse_card(str(stage.builder.bwd["cntn_to_dcsn"]))["sections"]["Signature"]
    assert ("in", "𝑉≻", "Xa → [−∞, ∞)") in signature_wires(decision)
    for name in stage.builder.bwd.list():
        if name != "policy":
            assert "μ" not in str(stage.builder.bwd[name])
    wires = [str(w.identity) for w in policy.signature().inputs + policy.signature().outputs]
    assert "cons_obs:cntn:μ" not in wires


def test_the_egm_row_keeps_two_parts_and_prints_no_derivation(port):
    """D6 as lane K of the internal developer release 0.01 restates it
    (sub-brief §3): the `!egm` row keeps the two public parts of AMD-SG-025
    §1, and its card prints what the method admits and no prose derivation.
    The requirement that replaces the derivation, a block that writes the
    grid line, is stated by the placement rule where the method is
    refused."""
    row = method_types["!egm"]
    assert len(row) == 2 and list(row) == ["admits", "keywords"]
    printed = str(row)
    # the card's section headings as lane P prints them
    assert "\nAdmits\n" in printed and "argmax" in printed
    assert "Derivation" not in printed and "Theorem 2" not in printed
    # the method component of a policy block whose lines are not the
    # method's: both levels hold the declared lines, and the eligibility
    # stands among the obligations as the condition of the method
    bound = copy_native(port).methodize({"text": "@methods: port\npolicy.method : !egm\n", "origin": "port.methods.bl"})
    assert str(bound.methods["policy"]) == "!egm"
    assert list(bound.builder.policy.list()) == list(bound.declared.policy.list())
    assert "egm-eligibility" in {item.condition for item in bound.obligations()}


def test_egm_on_the_declared_multiplier_binds_the_policy_evaluation(cons_obs):
    """`methodize` with `!egm` on the policy block of `cons_obs`, which
    writes the grid line, binds the block's closing Evaluation, which stores
    the policy (lane K of the internal developer release 0.01, sub-brief §3,
    which supersedes AMD-SG-035 §7), and changes no rule, no condition and
    no obligation."""
    methodized = copy_native(cons_obs).methodize({
        "text": ("@methods: cons_obs\n"
                 "a_min : ℝ₊\na_max : ℝ₊\nn_a : ℕ\n"
                 "policy.method : !egm\n"
                 'policy.handler : "cons-port:egm"\n'
                 "policy.grid : !Cartesian(a=(a_min, a_max, n_a))\n"),
        "origin": "cons_obs.methods.bl"})
    assert [place for place, held in methodized.builder.bwd.methods.items() if held.word == "!egm"] == ["policy"]
    from sheets_parse import parse_card
    before, after = parse_card(str(cons_obs.builder.policy)), parse_card(str(methodized.builder.policy))
    # the operations as before, the conditions as before with the method's
    # eligibility after them, the method's section after the conditions, the
    # grid of savings on its row (specification 0.7 D5)
    assert after["sections"]["Operations"] == before["sections"]["Operations"]
    held = before["sections"]["Conditions"]
    assert after["sections"]["Conditions"][:len(held)] == held
    assert "egm-eligibility" in "".join(after["sections"]["Conditions"][len(held):])
    last = before["order"].index("Conditions") + 1
    assert after["order"] == before["order"][:last] + ["Method"] + before["order"][last:]
    assert "!Cartesian(a=(a_min, a_max, n_a))" in "".join(after["sections"]["Method"])
    assert [i.condition for i in obligations(methodized)] == [
        *[i.condition for i in obligations(cons_obs)], "egm-eligibility"]


# --- the first build of branching (step F): the six conditions of the review focus, and how the branches combine

def test_a_nested_line_is_addressed_under_its_label_and_keeps_its_own_term(tenure, elaborate_text):
    """Layer audit H2: the definitions table is keyed by `item_addresses`, so a
    nested line without an id keeps its own term under its label, and one
    statement id written in two branches is two lines told apart by their
    addresses (branching-unified.md §3 item 3)."""
    table = tenure.definitions
    assert to_source(table["dcsn_to_cntn.keep.3"].equations[0]) == "z_kp = z_d"
    assert [str(record.identity) for record in table.values()
            if record.kind == "line" and record.identity.block == "dcsn_to_cntn"] == [
        "dcsn_to_cntn.keep.cash_on_hand", "dcsn_to_cntn.keep.housing_kept", "dcsn_to_cntn.keep.3",
        "dcsn_to_cntn.adjust.total_wealth", "dcsn_to_cntn.adjust.2"]
    twice = elaborate_text(branching(("[id=working]", "[id=assets]"), ("[id=retiring]", "[id=assets]")))
    assert [str(record.identity) for record in twice.definitions.values()
            if record.kind == "line" and record.identity.block == "dcsn_to_cntn"] == [
        "dcsn_to_cntn.work.assets", "dcsn_to_cntn.retire.assets"]


def test_an_elaborated_branching_stage_placed_by_hand_is_admitted(tenure):
    """The guard of `elaborate_trellis` is lifted (§3 item 9): a period holding
    an elaborated branching stage elaborates, and its outputs are the branch
    fields at the continuation perch."""
    trellis = accrete({"periods": [], "inter_connectors": []}, {"stages": {"tenure": tenure}, "connectors": []})
    assert period_joins(elaborate_trellis(trellis)["periods"][0])["outputs"] == [
        ("tenure", name) for name in ("h_kp", "w_adj", "w_kp", "z_adj", "z_kp")]


def test_a_branch_a_shock_selects_placed_by_hand_in_a_period_is_admitted(retiree_death):
    """A draw whose forward builders the family `Invariant` refuses still elaborates in a period,
    and its outputs are the branch fields."""
    trellis = accrete({"periods": [], "inter_connectors": []},
                      {"stages": {"retiree_death": retiree_death}, "connectors": []})
    assert period_joins(elaborate_trellis(trellis)["periods"][0])["outputs"] == [
        ("retiree_death", name) for name in ("a_rd_rt", "a_rd_yc", "y_rd_yc", "θ_rd_yc")]


def test_a_branch_is_a_bubble_of_the_initial_diagram_and_of_no_builders_graph(tenure):
    """E23: a branch is a bubble of the forward initial diagram, reached by its
    label from its block and its lines by their ids from it; the forward
    builder holds no branch at any grain, its branches being wires and boxes
    of the existing kinds."""
    block = tenure.initial.forward["dcsn_to_cntn"]
    assert [repr(block["keep"]), repr(block["keep"]["cash_on_hand"]), repr(block["adjust"]["2"])] == [
        "Block('tenure', 'dcsn_to_cntn.keep')", "Line('tenure', 'dcsn_to_cntn.keep.cash_on_hand')",
        "Line('tenure', 'dcsn_to_cntn.adjust.2')"]
    builder = tenure.dcsn.builder.fwd
    for handle in (builder, builder.sub_builders, builder.primitives):
        for label in ("keep", "adjust"):
            with pytest.raises(KeyError):
                handle[label]


def test_the_conservation_of_mass_follows_the_range_conditions_of_the_branch_lines(elaborate_text):
    """E3: the masses of the branch measures sum to the mass of μ where the
    policy sends each state to one label and each branch line writes into its
    field's set; established where every such range condition is, required
    where one is not, and printed on no card, the range condition carrying it."""
    def conservation(stage):
        return [item.status for item in stage.obligations() if item.condition == "mass-conservation"]
    assert conservation(elaborate_text(BRANCHING)) == ["established"]
    shifted = elaborate_text(branching(("a_w = a_d ", "a_w = a_d - 1 ")))
    assert conservation(shifted) == ["required"]
    card = str(shifted.builder.fwd["dcsn_to_cntn"])
    assert "a_d − 1 ∈ ℝ₊" in card and "mass" not in card


def test_the_forward_builders_graph_ends_at_the_branch_measures(tenure):
    """The forward builders graph of a branching stage ends at every branch
    measure, not at the first of them (E3): the outputs of its signature are
    the two branch measures, read by the names the signature's record holds."""
    assert [wire.name for wire in tenure.builder.fwd.signature().outputs] == ["μ_keep≻", "μ_adjust≻"]


def test_combination_answers_how_the_branches_combine(tenure, cons):
    """E27: the key of the retained selection is a control, so the branches
    combine by the choice; a stage without branches answers nothing."""
    assert (combination(tenure), combination(cons)) == ("choice", None)


# --- the second build of branching (step F): a branch a shock selects, the review focus

def test_the_definition_and_the_compiled_kernel_of_a_draw_state_the_weighted_case_operation(elaborate_text, fecundity):
    """Review focus 2 (E13): the aggregator of a draw denotes Σ_j p_j · Q_j, a Bernoulli's p going
    to the second label (AMD-SG-010 §3; Q19); compiled, it is vectorized over the evaluation
    points; the printed kernel counts the coordinates the law reads as read."""
    stage = elaborate_text(shock_branching(("Categorical((π, 1 - π))", "Bernoulli(π)")))
    assert "↦(1−π)·V_y≻+π·V_o≻" in flat(str(stage.definitions.denote("t:G:cntn_to_dcsn")))
    aggregation = (elaborate_text(SHOCK_BRANCHING).calibrate({"π": 0.25})
                   .builder.bwd["cntn_to_dcsn"].primitives["Aggregation"])
    G, values = aggregation.compile_kernel(), aggregation.kernel().parameter_values
    assert values == (0.25,)
    assert numpy.allclose(G(numpy.array([4.0, 8.0]), numpy.array([8.0, 4.0]), numpy.array([1.0, 1.0]), *values),
                          [7.0, 5.0])
    # the one output's line lists the unused coordinate alone, so `age_fecd`,
    # which the law reads, is counted as read
    printed = str(fecundity.builder.bwd["cntn_to_dcsn"].primitives["Aggregation"].kernel())
    assert printed.splitlines()[1] == "output V; unused a_fecd"


def test_the_forward_builder_of_a_draw_routes_the_extended_measure_by_the_label(elaborate_text):
    """Review focus 3 (E34): the extension by the law of `s`, then one push-forward with one
    measure per label, the section read at the decision states."""
    builder = elaborate_text(SHOCK_BRANCHING).builder.fwd["dcsn_to_cntn"]
    assert [str(key) for key in builder.primitives.list()] == ["DistributionExtension:s", "Pushforward"]
    from sheets_parse import operations_entries, parse_card
    entries = operations_entries(parse_card(str(builder))["sections"]["Operations"])
    rules = "".join(flat("".join(entry["rule"])) for entry in entries)
    for label in ("young", "old"):
        assert f"μ_{label}≻(B)=μ⊗P_s({{a_d,s∈ℝ₊×{{young,old}}|s={label}∧𝑔_{label}≻(a_d)∈B}})" in rules


def test_the_conservation_of_mass_of_a_draw_follows_the_weights_of_its_law(elaborate_text):
    """Review focus 4 (E3, E13): required while a weight is a parameter, established by numbers
    that sum to one, refused at calibration where the values do not."""
    def conservation(stage):
        return [(item.status, str(item.named_identities[1])) for item in stage.obligations()
                if item.condition == "mass-conservation"]
    assert conservation(elaborate_text(SHOCK_BRANCHING)) == [("required", "t:distribution:s")]
    assert conservation(elaborate_text(shock_branching(("(π, 1 - π)", "(0.5, 0.5)")))) == [
        ("established", "t:distribution:s")]
    two = elaborate_text(shock_branching(("π : [0,1]", "p : [0,1]\nq : [0,1]"), ("(π, 1 - π)", "(p, q)")))
    with pytest.raises(ConstructionError) as refused:
        two.calibrate({"p": 0.3, "q": 0.6})
    assert refused.value.rule == "distribution-domain" and "not to one" in str(refused.value)


# --- the structure review's C5: the printed corrections (decision S10 of the cleanup)







def test_a_kernel_line_names_the_edge_that_draws_the_shocks(port, tenure):
    """map/distributions P2: an expectation's kernel line said `drawn in
    cntn_to_dcsn`, the builder that integrates the shocks, while they are
    drawn on the edge of the forward builder that lists them, `dcsn_to_cntn`,
    and on `tenure` `drawn in dcsn_to_arvl` for a shock of the arrival edge;
    the line names the edge that draws the shocks, and the builder that
    integrates them under the verb `integrates`."""
    primitives = port.builder.bwd.primitives
    assert str(primitives["cntn_to_dcsn.value:Expectation:1"].kernel()).splitlines()[1] == (
        "conditioned on none declared; drawn on the edge dcsn_to_cntn; in cntn_to_dcsn at each point of k_d, "
        "integrates Ψ, θ; declared at port:distribution:Ψ_θ")
    assert "; drawn on the edge dcsn_to_cntn; in policy at each point of (k_d, ς), integrates Ψ, θ;" in str(
        primitives["policy.foc:Expectation:1"].kernel())
    assert "; drawn on the edge arvl_to_dcsn; in dcsn_to_arvl at each point of (a, h, z), integrates ε;" in str(
        tenure.builder.bwd.primitives["dcsn_to_arvl.value:Expectation:1"].kernel())


def test_the_refusals_say_backward_block_law_of_motion_edge_and_distribution(catalogue_entries):
    """map/fold P7 and form/typing §8 (decision S16 of the cleanup): refusal
    sentences said `value block`, which the terminology forbids, `transition`
    for the law of motion and for the edge a shock is drawn on, and `law`
    alone for a shock's distribution; every refusal the catalogue provokes,
    and the refusals of a distribution declared twice or not at all, say
    backward block, law of motion, edge and distribution."""
    from bellman.refusal_examples import EXAMPLES
    from bellman.refusal_catalogue import refusal_of
    refused_words = re.compile(r"value block|value builder|transition g\b|\btransition (?:from|defines)"
                               r"|\bforward transition|(?<!-)\blaws?\b(?! of motion)")
    said = {item.rule: item.why for item in catalogue_entries}
    for text in (two_nodes(declarations="y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\ny ~ N(0,2)\n"),
                 two_nodes(declarations="y ~ N(0,1)\nz : ℝ\n(y, z) ~ N((0,0),((1,0),(0,1)))\n"),
                 two_nodes(declarations="y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\nq : ℝ\n",
                           backward="    V = E_{q}(V[>]) :: [id=value]\n")):
        with pytest.raises(ConstructionError) as refused:
            stage_from_text(text)
        said[text] = refused.value.message
    assert [message for message in said.values() if refused_words.search(message)] == []
    assert said["transition-without-expectation"].endswith(
        "through the law of motion 𝑔 and takes no expectation; write the integration in a backward block")
    assert "; the edge from the arvl perch to the dcsn perch draws the shock y," in said["shock-observed"]
    assert "Write the cntn-perch field the law of motion defines" in said["forward-composite"]
    assert "has no distribution; the branches are weighted by the distribution of the shock" in said["branch-law"]


def test_the_short_form_of_a_piece_at_a_finer_grain_names_its_grain(cons, tenure, sa_savings):
    """The review's R5 (§5.3): a piece opened at a finer grain printed as the
    piece it came from, `Builder('cons', 'cntn_to_dcsn')`, although the two
    compare unequal, and a graph at the sub-builder grain printed `'node'`, the
    code's word for the grain; the short form names the grain by the attribute
    that reaches it."""
    builder = cons.builder.bwd["cntn_to_dcsn"]
    assert [repr(builder), repr(builder.primitives), repr(builder.sub_builders)] == [
        "Builder('cons', 'cntn_to_dcsn')", "Builder('cons', 'cntn_to_dcsn', primitives)",
        "Builder('cons', 'cntn_to_dcsn', sub_builders)"]
    graph = cons.builder.bwd
    assert [repr(graph), repr(graph.primitives), repr(graph.sub_builders)] == [
        "BuildersGraph('cons', 'backward')", "BuildersGraph('cons', 'backward', primitives)",
        "BuildersGraph('cons', 'backward', sub_builders)"]
    nested = tenure.initial.forward["dcsn_to_cntn"]["dcsn_to_cntn.keep"]
    assert repr(nested.primitives) == "Block('tenure', 'dcsn_to_cntn.keep', primitives)"

    for opened in (builder.primitives, builder.sub_builders):
        assert opened.obligations() == builder.obligations()
        assert str(opened.denote()) == str(opened)
        assert "cntn_to_dcsn" in str(opened)
    assert "FORWARD BLOCK dcsn_to_cntn / keep" in str(nested.primitives)
    assert nested.primitives.obligations() == nested.obligations()
    assert list(nested.primitives.list()) == list(nested.list()) != []
    assert str(nested.primitives.signature()) == str(nested.signature())

    operations = sa_savings.builder.bwd["cntn_to_dcsn"]
    assert operations.list()[1] == ("risk_ce", "Pullback")
    for handle in (operations, operations.sub_builders, operations.primitives, operations["risk_ce"]):
        listing = handle.list()
        assert [handle[key].box.name for key in listing] == list(listing.names)
    numbered = [(entry.name, entry.number) for entry in operations.list().entries if entry.number is not None]
    assert numbered == [(entry.name, entry.number) for entry in operations.primitives.list().entries]
    assert str(operations["Evaluation"].list()) == "none"
    graph = sa_savings.builder.bwd
    opened = {entry.name: entry.number for entry in graph.primitives.list().entries}
    for name in graph.list():
        own = graph[name].primitives.list()
        assert [opened[entry.name] for entry in own.entries] == [entry.number for entry in own.entries]




# --- the structure review's unit C10: the authored nodes are handed to the typing on the boxes




# --- performance unit P1: a stored diagram opened with the package's hypergraph class




# --- the tests' time (lane T0 of the internal developer release 0.01): the
# records a card prints, kept for the version that was asked for them


def _every_card(stage):
    """Every card of a version with the record it prints, in one order: the
    stage card; each builders graph's and each initial diagram's, followed by
    the same graph's cards at the primitive grain and at the sub-builder
    grain; each builder's and each block's, followed by its cards at the
    sub-builder grain and at the primitive grain and by the cards of the
    builder's primitives and of the block's lines; and each definition's."""
    made = [("stage", stage.denote())]
    for graph in (stage.builder.bwd, stage.builder.fwd, stage.initial.backward, stage.initial.forward):
        made.append((repr(graph), graph.denote()))
        for opened in (graph.primitives, graph.sub_builders):
            made.append((repr(opened), opened.denote()))
        for name in graph.list():
            piece = graph[name]
            made.append((repr(piece), piece.denote()))
            made.append((f"{piece!r} sub_builders", piece.sub_builders.denote()))
            made.append((f"{piece!r} primitives", piece.primitives.denote()))
            opened = piece.primitives
            for key in opened.list():
                made.append((f"{piece!r} {key}", opened[key].denote()))
    listing = stage.definitions.list()
    for group in listing:
        for identity in listing[group]:
            made.append((str(identity), stage.definitions.denote(identity)))
    return [(title, str(record), record) for title, record in made]


def test_the_cards_of_a_bound_version_are_those_of_a_fresh_elaboration_bound_alike():
    """A version keeps the record each card prints, and a binding verb carries
    none of them to the version it returns, since a card prints the bindings
    of its own version (the final review of the plan of the internal developer
    release 0.01, finding 14). The symbolic version of `cons.bl` and its
    calibrated version print every card before the next verb binds them; the
    version `calibrate` and `methodize` return holds, before it is asked
    anything, only answers of `versions.CARRIED`, and prints every card, with
    its record, as the same file elaborated afresh and bound with the same
    calibration and methods, whose versions printed nothing before binding.
    The value of ρ printed on the bound version shows that its cards are its
    own and not its argument's."""
    from bellman.native.versions import CARRIED
    values, methods = CORPUS_CALIBRATIONS["cons"], CORPUS_METHODS["cons"]
    symbolic = corpus_stage("cons")
    before = _every_card(symbolic)
    calibrated = symbolic.calibrate(values)
    _every_card(calibrated)
    bound = calibrated.methodize(methods)
    kept = vars(bound).get("_kept", {})
    assert {key if isinstance(key, str) else key[0] for key in kept} <= CARRIED
    fresh = corpus_stage("cons").calibrate(values).methodize(methods)
    printed = _every_card(bound)
    assert printed == _every_card(fresh)
    parameter = [text for title, text, _ in printed if title == "cons:parameter:ρ"]
    assert len(parameter) == 1 and "ρ  ∈ [1, ∞),  = 6.0" in parameter[0]
    assert [text for title, text, _ in before if title == "cons:parameter:ρ"] != parameter


def test_a_version_whose_cards_are_kept_is_collected_once_no_name_refers_to_it():
    """The records a version keeps for its cards hold nothing that refers to
    the version, so the memo keeps no version alive (the final review of the
    plan of the internal developer release 0.01, finding 14): a symbolic and a
    bound version of `cons.bl`, each asked for every card, are collected once
    the names that refer to them are deleted and the collector has run, and
    the records they answered print as before."""
    import gc
    import weakref
    symbolic = corpus_stage("cons")
    bound = symbolic.calibrate(CORPUS_CALIBRATIONS["cons"]).methodize(CORPUS_METHODS["cons"])
    cards = _every_card(symbolic) + _every_card(bound)
    assert all("stage denotation" in vars(version)["_kept"] for version in (symbolic, bound))
    references = [weakref.ref(symbolic), weakref.ref(bound)]
    del symbolic, bound
    gc.collect()
    assert [reference() for reference in references] == [None, None]
    assert [str(record) for _, _, record in cards] == [text for _, text, _ in cards]


# --- the card sweeps of AMD-SG-034 §8, items 1, 4, 5 and 6, moved here from
# its acceptance file when the card took the form of the internal developer
# release 0.01 (BN1 of the release's decisions); item 2 stands in
# `cat/test_card_form.py`. Items 1, 4 and 5 are sweeps, one test for each stage
# of `CARD_STAGES`; each reads the stage's cards and their records from the
# fixture `printed_cards` of `conftest.py`, which prints them once in a
# process, and prints none itself. Item 6 reads the source of the card modules.

# the thirteen stages of the card sweeps: the seven stages of the critique of
# AMD-SG-034 (§9), the four saving stages of Dobrescu and Shanker (2024) added
# to it (its plan addendum, item 18), and the branching stages of the two
# builds of step F, whose cards the guards read as well; each is the name of a
# stage fixture of `conftest.py`
CARD_STAGES = ("cons", "port", "ez_savings", "cons_savings_iid", "sa_savings", "buffer_stock",
               "adjuster_cons", "worker_saving", "retiree_saving", "keeper_saving", "adjuster_saving",
               "tenure", "worker_ageing")






# the words of a status, which a condition prints with none of
STATUS_WORDS = ("[textual]", "required by the exact operation", "; required", "; assumed")




def _isinstance_calls(source):
    """The second argument of every `isinstance` call of a module, as text."""
    import ast
    found = []
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "isinstance" and len(node.args) == 2):
            found.append(ast.get_source_segment(source, node.args[1]) or "")
    return found


TERM_MODULES = ("S.", "T.", "P.", "semantic.", "terms.", "predicates.")

# the functions moved from `display/printers.py` into modules whose other
# functions rewrite terms by design, read by name, with the three written from
# their code (`_nodes`, `drawn_wire_names`, `drawn_laws`): the text of an
# obligation's entries and of a predicate in `typing/typed_expressions.py`, the lines
# after `applies` in `stage/kernels.py`, the names of wires, measures
# and results, and the names a drawing is given, in
# `stage/defining_expressions.py`, the titles and the coordinates of a card in
# `stage/denotations.py`, the key of a piece in `stage/boxes.py`
# and the descriptions of a record in `stage/stage_answers.py`. The item reads
# no other function of these modules.
PRINTED_TEXT_FUNCTIONS = {
    "bellman.typing.typed_expressions": (
        "obligation_entry", "_term_text", "_holds_semantic", "_nodes", "predicate_text", "clauses",
        "_group"),
    "bellman.stage.kernels": (
        "_applied_lines", "_kernel_lines", "_conditional_expectation_lines", "_drawn_and_integrated",
        "_side_points", "stems_of", "coordinates_of", "integrated_shocks", "conditioning",
        "distribution_arguments", "_declaration_text", "_point_masses", "_feasibility_lines",
        "_feasible_controls", "_feasible_set_and_origin", "_binder_of"),
    "bellman.stage.defining_expressions": (
        "wire_name", "_applied_name", "result_labels", "_wire_expression_text",
        "_wire_expression_names", "distribution_symbol", "_measure_name", "_declared_law_names",
        "_distribution_factors", "_result_name", "_law_symbol", "_law_arguments_at_policy",
        "_aggregator_symbol", "drawn_wire_names", "drawn_laws", "_blocks_drawn"),
    "bellman.stage.denotations": (
        "written_at", "_card_coordinate_names", "_doc_coordinates", "_arrowed", "_grain_stamp",
        "_statements_of_block", "_coordinate_sorts", "_marks", "_line_coordinates"),
    "bellman.stage.boxes": ("piece_named",),
    "bellman.stage.stage_answers": ("descriptions",),
}


def _rewrites_no_term(source, name):
    """The checks item 6 makes of a whole module, made of one source text."""
    assert "substitute(" not in source, name
    # `dataclasses.replace` and a bare `replace` make a new term from an
    # old one; `.replace` on a string of the title is no term
    assert "dataclasses.replace(" not in source, name
    assert not re.search(r"(?<![\w.])replace\(", source), name
    assert not re.search(r"stage\.name\s*==|\.stage(?:_name)?\s*==\s*['\"]|\bname\s*==\s*['\"]",
                         source), name
    assert "type(term)(" not in source, name




def test_item_4_the_spans_of_a_text_are_the_lowerings_positions_on_the_corpus(text_of):
    """`source_spans` answers the span table of `parse_with_spans` for each
    corpus stage (spec 0.3 §12, P item 4), read-only, and refuses a text as
    `elaborate_text` refuses it: the parser's refusal under `syntax` at its
    line and column, and the lowering's refusal of one id on two lines."""
    from conftest import CORPUS
    from bellman.stage import elaborate_text, source_spans

    def with_line(text, number, line):
        lines = text.split("\n")
        lines[number - 1] = line
        return "\n".join(lines)

    for name in ("cons", "port", "ez_savings", "cons_savings_iid"):
        spans = source_spans(text_of(name), CORPUS[name])
        assert dict(spans) == dict(parse_with_spans(text_of(name), filename=CORPUS[name]).spans)
    spans = source_spans(text_of("cons"), CORPUS["cons"])
    policy = spans["policy"]
    assert (policy.file, policy.line, policy.column, policy.end_line, policy.end_column) == (
        CORPUS["cons"], 29, 1, 31, 2)
    assert spans["policy.optimality"].line == 30
    with pytest.raises(TypeError):
        spans["policy"] = None
    unreadable = with_line(text_of("cons"), 17, "    a = m_d - - c")
    with pytest.raises(ConstructionError) as refused:
        source_spans(unreadable, CORPUS["cons"])
    assert (refused.value.rule, refused.value.file, refused.value.line, refused.value.column) == (
        "syntax", CORPUS["cons"], 17, 15)
    # elaborate_text refuses the text with the same rule, place and message
    rule_place_and_message = attrgetter(
        "rule", "file", "line", "column", "end_line", "end_column", "message")
    with pytest.raises(ConstructionError) as elaborated:
        elaborate_text(unreadable, CORPUS["cons"])
    assert rule_place_and_message(elaborated.value) == rule_place_and_message(refused.value)
    id_on_two_lines = with_line(
        text_of("cons"), 22, "    D_{m_d}V = 𝑑𝑢(c)                :: [id=value]")
    with pytest.raises(ConstructionError) as refused:
        source_spans(id_on_two_lines, CORPUS["cons"])
    assert refused.value.rule == "syntax"
    # the lowering's sentence stands on the first line of the message
    assert refused.value.message.startswith(
        f"the address 'cntn_to_dcsn.value' names two items, the first at {CORPUS['cons']}:21:5 "
        "and the second here; an id names one block, one line of a block or one nested block, "
        "and a label one nested block\n")
    # elaborate_text refuses the text with the same rule, place and message
    with pytest.raises(ConstructionError) as elaborated:
        elaborate_text(id_on_two_lines, CORPUS["cons"])
    assert rule_place_and_message(elaborated.value) == rule_place_and_message(refused.value)


def test_item_5_a_binding_report_names_the_failure_and_the_two_successes(cons, cons_sources):
    """`bind_stage` applies the three verbs from a record's sources in their
    order, reports the verbs applied, skipped and failed, and answers the
    stage the successes made (spec 0.3 §12, P item 5)."""
    from bellman.stage import bind_stage
    source = {"calibration": str(cons_sources["calibration"]),
              "methods": str(cons_sources["methods"]), "settings": {"nonsense": 1}}
    source_before, stage_before = deepcopy(source), cons.encoding()
    report = bind_stage(cons, source)
    assert (report.bound, report.skipped, list(report.failed)) == (("calibrate", "methodize"), (), ["configure"])
    # the first setting the addition declares and the source leaves without
    # a value, refused at the declaration's position in the addition
    failed = report.failed["configure"]
    assert failed.startswith(
        f"{cons_sources['methods']}:21:1: stage 'cons', setting 'n_a': the settings source "
        "supplies no value for it; every setting the methods file declares is valued when "
        "settings are bound; write `n_a: <value>` in the settings source")
    assert failed.endswith("; rule setting-unvalued)")
    assert report.stage is not cons
    assert report.stage.bindings.calibration is not None
    assert holds_additions(report.stage)
    assert report.stage.bindings.settings is None
    assert report.stage.bindings.calibration == copy_native(cons).calibrate(str(cons_sources["calibration"])).bindings.calibration
    captured, retained = [], {}

    def retain_refusal(error, verb):
        captured.append((error, verb))
        return retained

    with_record = bind_stage(cons, source, on_refusal=retain_refusal)
    assert len(captured) == 1
    error, verb = captured[0]
    assert isinstance(error, ConstructionError) and error.rule == "setting-unvalued"
    assert verb == "configure" and error.file == str(cons_sources["methods"]) and error.line == 21
    assert with_record.failed["configure"] is retained
    assert (with_record.bound, with_record.skipped) == (report.bound, report.skipped)
    assert with_record.stage.bindings == report.stage.bindings
    assert holds_additions(with_record.stage) and with_record.stage.bindings.settings is None
    assert source == source_before and cons.encoding() == stage_before
    # nothing supplied, in either empty form: the stage itself, the three verbs skipped
    for methods in ({}, []):
        empty = bind_stage(cons, {"calibration": {}, "methods": methods, "settings": {}})
        assert empty == (cons, (), ("calibrate", "methodize", "configure"), {})
    # a failed verb leaves the object as the verbs before it made it; the next verb is still applied
    broken = bind_stage(cons, {"calibration": {"ρ": 0.5}, "methods": str(cons_sources["methods"]), "settings": {}})
    assert (broken.bound, broken.skipped, list(broken.failed)) == (("methodize",), ("configure",), ["calibrate"])
    assert broken.stage.bindings.calibration is None
    assert holds_additions(broken.stage)
    # settings without methods are bound, the value listed with no reader
    alone = bind_stage(cons, {"calibration": {}, "methods": {}, "settings": {"n_m": 8}})
    assert alone.stage is not cons and alone.failed == {}
    assert (alone.bound, alone.skipped) == (("configure",), ("calibrate", "methodize"))
    assert dict(alone.stage.bindings.settings) == {"n_m": 8}
    # a methods source that is no addition is reported under methodize, not raised
    malformed = bind_stage(cons, {"calibration": {}, "methods": {"methods": "nonsense"}, "settings": {}})
    assert malformed.failed == {
        "methodize": "an addition is the path of a `.bl` file or a mapping {text, origin} holding "
                     "its text; got dict"}
    assert malformed.stage is cons


def test_an_entry_of_a_models_file_is_found_read_and_replaced_keeping_the_rest_of_the_text():
    """`entry_span`, `entry_value` and `replace_entry` of `bellman.trellis` on
    the pension recipe, `declaration/spec.yml`, and its trellis file: the
    slot `$fill` of the worker's calibration stands at its line and columns
    and reads as written; replaced by a name, the text changes on that line
    alone and only there, its comments kept, and reads back as the name; a
    name that would read as another type is written in double quotes; the
    document's tag is read beside its keys; an address the text does not
    hold, and a text that does not read, are refused (the model interface's
    specification 0.3, §3.2), a text that does not read including one with
    a value its core tag cannot build, `!!bool abc`, whose constructor in
    PyYAML raises its own error, so that a string that would read so plain,
    `!!timestamp abc`, is written in double quotes."""
    from bellman.trellis import entry_span, entry_value, replace_entry

    declaration = ROOT / "applications/pension-retirement/declaration"
    recipe = (declaration / "spec.yml").read_text(encoding="utf-8")
    address = "stages.worker_saving.calibration.all[0]"
    assert entry_value(recipe, address) == "$fill"
    span = entry_span(recipe, address)
    line = recipe.split("\n")[span.line - 1]
    assert span.end_line == span.line and line[span.column - 1 : span.end_column - 1] == "$fill"
    written = replace_entry(recipe, address, "calibration/worker")
    before, after = recipe.split("\n"), written.split("\n")
    assert len(before) == len(after)
    assert [n for n, (a, b) in enumerate(zip(before, after)) if a != b] == [span.line - 1]
    assert after[span.line - 1] == line[: span.column - 1] + "calibration/worker" + line[span.end_column - 1 :]
    assert entry_value(written, address) == "calibration/worker"
    assert entry_value(written, "stages.retiree_saving.calibration.all[0]") == "$fill"
    quoted = replace_entry(recipe, "stages.worker_saving.methods.all[0]", "null")
    assert entry_value(quoted, "stages.worker_saving.methods.all[0]") == "null" and '"null"' in quoted
    trellis = (declaration / "trellis.yml").read_text(encoding="utf-8")
    assert entry_value(trellis)["__yaml_tag__"] == "trellis"
    assert entry_value(trellis, "periods[1]") == {"template": "period.yml", "repeat": 14}
    with pytest.raises(KeyError):
        entry_span(trellis, "periods[0].nothing")
    with pytest.raises(ValueError):
        entry_value("a: [1, 2")
    # a float written in base 60 with 175 parts, whose constructor
    # multiplies its first part by 60**174, more than a float holds
    sexagesimal = "1" + ":0" * 174 + "."
    # the constructors raise KeyError, IndexError, AttributeError, TypeError
    # and OverflowError for these values
    for unbuilt in ("!!bool abc", "!!int ''", "!!timestamp abc", "!!set [1]", sexagesimal):
        with pytest.raises(ValueError, match="^the text does not read as YAML"):
            entry_value(unbuilt)
    tagged = replace_entry(recipe, address, "!!timestamp abc")
    assert entry_value(tagged, address) == "!!timestamp abc" and '"!!timestamp abc"' in tagged
    overflowing = replace_entry(recipe, address, sexagesimal)
    assert entry_value(overflowing, address) == sexagesimal and f'"{sexagesimal}"' in overflowing


def test_a_text_nested_deeper_than_the_reader_can_follow_does_not_read_and_is_written_quoted():
    """A YAML text nested as many levels deep as the interpreter's recursion
    limit, which the reader's composer cannot follow, since it calls itself
    at least once for each level, does not read: `entry_value` and
    `entry_span` of `bellman.trellis` refuse it with a ValueError, as they
    refuse any text that does not read (the model interface's specification
    0.3, §3.2). Given that text as a string, `replace_entry` does not write
    its plain form, which does not read, and writes it in double quotes,
    where it reads back as the string, the comment after the value kept
    (AMD-MI-002 §5)."""
    from bellman.trellis import entry_span, entry_value, replace_entry

    depth = sys.getrecursionlimit()
    deep = "{a: " * depth + "1" + "}" * depth
    with pytest.raises(ValueError, match="^the text does not read as YAML"):
        entry_value(deep)
    with pytest.raises(ValueError, match="^the text does not read as YAML"):
        entry_span(deep, "a")
    text = "settings:\n  upper_envelope: FUES  # the method\n"
    written = replace_entry(text, "settings.upper_envelope", deep)
    assert written == text.replace("FUES", f'"{deep}"')
    assert entry_value(written, "settings.upper_envelope") == deep


def test_replacing_a_value_builds_no_mapping_its_plain_form_merges_through_aliases():
    """`replace_entry` of `bellman.trellis` reads a candidate text whole only
    where its entry composes to the scalar it writes, so that the reader
    does not build the mappings that the plain form of a value merges
    through aliases, whose entries it copies once for each alias: seven
    levels of ten aliases make 10**8 entries, some 15 seconds and 2 GB of
    memory. Such a string is written in double quotes, where it reads back
    as the string, the comment after the value kept, and a tag with that
    value is refused, its plain form writing a mapping. A tag whose value
    writes those levels after a line break, as keys of the document, or
    after a comma within a flow mapping, as keys beside the entry, is
    refused, since its plain form writes a scalar that ends before the form
    does; all within a second (AMD-MI-002 §5)."""
    from bellman.trellis import entry_value, replace_entry

    levels = ["l0: &l0 {" + ", ".join(f"k{i}: {i}" for i in range(10)) + "}"]
    levels += [f"l{k}: &l{k} {{<<: [" + ", ".join([f"*l{k - 1}"] * 10) + "]}" for k in range(1, 8)]
    merged = "{" + ", ".join(levels) + "}"
    text = "settings:\n  upper_envelope: FUES  # the method\n  outer: !egm\n"
    started = time.perf_counter()
    written = replace_entry(text, "settings.upper_envelope", merged)
    assert written == text.replace("FUES", f'"{merged}"')
    assert entry_value(written, "settings.upper_envelope") == merged
    with pytest.raises(ValueError, match="cannot be written as a tag at 'settings.outer'$"):
        replace_entry(text, "settings.outer", {"__yaml_tag__": "egm", "value": merged})
    beside = {"__yaml_tag__": "egm", "value": "x\n" + "\n".join(levels)}
    with pytest.raises(ValueError, match="cannot be written as a tag at 'settings.outer'$"):
        replace_entry(text, "settings.outer", beside)
    flow = "settings: {upper_envelope: FUES, outer: !egm grid}\n"
    beside = {"__yaml_tag__": "egm", "value": "x, " + ", ".join(levels)}
    with pytest.raises(ValueError, match="cannot be written as a tag at 'settings.outer'$"):
        replace_entry(flow, "settings.outer", beside)
    assert time.perf_counter() - started < 1.0


def test_written_at_moves_an_address_of_the_expanded_trellis_to_the_file_that_writes_it():
    """An address of the trellis `load_recipe` or `load_trellis` expands
    stands in the trellis file or in the period file its entry names:
    `periods[0]` of the pension trellis is written out, `periods[5]` repeats
    `period.yml`, every `inter_connectors[h]` is the one mapping the file
    writes, and `periods[4]` of `trellis.port-cons.yml` is its one entry
    repeated six times; another address is answered as given, and a period
    the file does not write is refused."""
    from bellman.trellis import entry_span, written_at

    pension = ROOT / "applications/pension-retirement/declaration/trellis.yml"
    assert written_at(pension, "periods[0].connectors[0]") == (str(pension), "periods[0].connectors[0]")
    assert written_at(pension, "periods[5].connectors[0]") == (str(pension.parent / "period.yml"), "connectors[0]")
    assert written_at(pension, "inter_connectors[7]") == (str(pension), "inter_connectors[0]")
    assert written_at(pension, "stages.worker_saving") == (str(pension), "stages.worker_saving")
    port_cons = ROOT / "applications/cons-port/declaration/trellis.port-cons.yml"
    assert written_at(port_cons, "periods[4].stages.cons.methods") == (
        str(port_cons),
        "periods[0].stages.cons.methods",
    )
    with pytest.raises(KeyError):
        written_at(pension, "periods[15].connectors[0]")
    text = pension.read_text(encoding="utf-8")
    assert entry_span(text, "periods[0].connectors[0]").line == 20
    assert entry_span(text, "inter_connectors[0]").line == 31


def test_written_at_agrees_with_the_loader_on_a_period_files_repeat_and_on_absent_inter_period_mappings(tmp_path):
    """`written_at` counts the periods and the adjacent pairs of a trellis
    file as `read_trellis_file` expands them. A `repeat` written in a period
    file counts where the entry that names the file writes none, and the
    entry's own `repeat` stands over it: for every period of the expansion,
    the place answered holds the stages the loader reads there. Where the
    file writes no inter-period mapping, the loader reads an empty mapping
    for each pair, which no file writes, and the address is refused. One
    mapping stands for every pair, a file that writes one mapping for each
    pair answers each pair's own, and a pair outside the expansion is
    refused."""
    from bellman.factory.loading import read_trellis_file
    from bellman.trellis import entry_value, written_at

    def written(name, text):
        """The path of the file `name` in `tmp_path`, written with `text`."""
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    def held(trellis, address):
        """The value at the place `written_at` answers for `address`."""
        file, place = written_at(trellis, address)
        return entry_value(Path(file).read_text(encoding="utf-8"), place)

    def places(trellis):
        """The place `written_at` answers for the stages of each period the
        loader expands, each checked to hold the stages the loader reads."""
        expanded = read_trellis_file(trellis)["periods"]
        for h, period in enumerate(expanded):
            assert held(trellis, f"periods[{h}].stages") == period["stages"], h
        return [written_at(trellis, f"periods[{h}].stages") for h in range(len(expanded))]

    period = written(
        "period.yml",
        "!period\nstages: [worker, retiree]\nconnectors:\n  - {}\nrepeat: 3\n",
    )
    terminal = "  - stages: [worker, retiree, terminal]\n    connectors: []\n"
    # three periods by the period file's `repeat: 3`, and a fourth written out
    trellis = written("trellis.yml", "!trellis\nperiods:\n  - {template: period.yml}\n" + terminal)
    assert places(trellis) == [(str(period), "stages")] * 3 + [(str(trellis), "periods[1].stages")]
    with pytest.raises(KeyError):
        written_at(trellis, "periods[4].stages")
    # the entry's own `repeat: 2` stands over the period file's `repeat: 3`
    twice = written(
        "twice.yml", "!trellis\nperiods:\n  - {template: period.yml, repeat: 2}\n" + terminal
    )
    assert places(twice) == [(str(period), "stages")] * 2 + [(str(twice), "periods[1].stages")]
    with pytest.raises(KeyError):
        written_at(twice, "periods[3].stages")

    # two periods written out and no inter-period mapping, the key absent or
    # an empty list: the loader reads one empty mapping, which no file writes
    two = "!trellis\nperiods:\n  - stages: [worker]\n  - stages: [worker]\n"
    for name, text in (("absent.yml", two), ("empty.yml", two + "inter_connectors: []\n")):
        bare = written(name, text)
        assert read_trellis_file(bare)["inter_connectors"] == [{}]
        with pytest.raises(KeyError):
            written_at(bare, "inter_connectors[0]")
    # one period and one mapping: the loader reads no pair
    single = written(
        "single.yml", "!trellis\nperiods:\n  - stages: [worker]\ninter_connectors:\n  - {a: k}\n"
    )
    assert read_trellis_file(single)["inter_connectors"] == []
    with pytest.raises(KeyError):
        written_at(single, "inter_connectors[0]")
    # three periods by the period file's `repeat: 3`, and one mapping that
    # stands for both pairs
    standing = written(
        "standing.yml",
        "!trellis\nperiods:\n  - {template: period.yml}\ninter_connectors:\n  - {a: k}\n",
    )
    mappings = read_trellis_file(standing)["inter_connectors"]
    assert len(mappings) == 2
    for h, mapping in enumerate(mappings):
        assert written_at(standing, f"inter_connectors[{h}]") == (
            str(standing),
            "inter_connectors[0]",
        )
        assert held(standing, f"inter_connectors[{h}]") == mapping
    with pytest.raises(KeyError):
        written_at(standing, "inter_connectors[2]")
    # the four periods of `trellis.yml`, one mapping for each pair
    each = written(
        "each.yml",
        trellis.read_text(encoding="utf-8")
        + "inter_connectors:\n  - {a: k}\n  - {b: k}\n  - {c: k}\n",
    )
    mappings = read_trellis_file(each)["inter_connectors"]
    assert len(mappings) == 3
    for h, mapping in enumerate(mappings):
        assert written_at(each, f"inter_connectors[{h}]") == (str(each), f"inter_connectors[{h}]")
        assert held(each, f"inter_connectors[{h}]") == mapping
    with pytest.raises(KeyError):
        written_at(each, "inter_connectors[3]")


def test_a_block_style_entry_ends_at_its_last_item_and_its_replacement_keeps_the_comments():
    """A value written in block style ends at its last character, not at the
    comment or the key that follows it: a mapping on the lines below its key,
    or a list written at its key's indentation, ends where its last item
    ends, and a text after "|" before its trailing line breaks. Replaced by a
    name, the last entry of a file keeps the comment and the final line break
    after it, and an entry in mid-file keeps the comment after it and leaves
    the next key as written (the model interface's specification 0.3, §3.2)."""
    from bellman.trellis import entry_span, entry_value, replace_entry

    text = (
        "worker:\n"
        "  calibration: calibration/worker.yml\n"
        "  methods: methods/worker.yml\n"
        "# the retiree's sources\n"
        "retiree:\n"
        "  calibration: calibration/retiree.yml\n"
        "# no methods file is written yet\n"
    )
    assert entry_span(text, "worker") == (2, 3, 3, 30)
    assert entry_span(text, "retiree") == (6, 3, 6, 39)
    last = replace_entry(text, "retiree", "sources/retiree.yml")
    assert last == text.replace("calibration: calibration/retiree.yml", "sources/retiree.yml")
    assert entry_value(last, "retiree") == "sources/retiree.yml"
    middle = replace_entry(text, "worker", "sources/worker.yml")
    assert middle == text.replace(
        "calibration: calibration/worker.yml\n  methods: methods/worker.yml", "sources/worker.yml"
    )
    assert entry_value(middle) == {
        "worker": "sources/worker.yml",
        "retiree": {"calibration": "calibration/retiree.yml"},
    }
    notes = (
        "stages:\n"
        "- worker\n"
        "- retiree\n"
        "# the stages\n"
        "label: |\n"
        "  the pension model\n"
        "\n"
        "# the label\n"
    )
    assert entry_span(notes, "stages") == (2, 1, 3, 10)
    assert entry_span(notes, "label") == (5, 8, 6, 20)
    labeled = replace_entry(notes, "label", "pension")
    assert labeled == notes.replace("|\n  the pension model", "pension")


def test_a_quoted_value_replaced_keeps_its_quotes_and_every_other_character_of_the_file():
    """`replace_entry` of `bellman.trellis` writes one scalar anew as text
    and keeps every other character: the `trellis:` line of the pension
    recipe, `declaration/spec.yml`, and the `template:` of a flow-style
    entry of its trellis file; a value written in single quotes keeps its
    quotes and the comment after it, a quote within the new value doubled
    as YAML writes it there, and a value written in double quotes, in a
    text whose lines end with a carriage return and a line feed, keeps its
    quotes and those line ends; an address the text does not hold is
    refused with a KeyError. These are the claims of the test of the layout
    unit's `replace_scalar`, which the package's writer meets, that test
    and the writer having been removed when unit B merged the layout unit.
    Where that writer refused, the package answers otherwise: a plain value
    that would read as another type is written in double quotes; a
    double-quoted value with an escape is written anew within its double
    quotes; a plain value written over two lines is replaced whole; a
    mapping, the recipe's block mapping `stages` or a flow mapping, is
    replaced whole by the string, as a choice for a cell holding `{}`
    replaces it; and a tagged value is replaced whole, its tag dropped. A
    single-quoted value that would read as another type stays within its
    quotes, as both writers write it. Both refuse an anchored value that an
    alias reads (the model interface's specification 0.3, §3.2 and §6)."""
    from bellman.trellis import replace_entry

    declaration = ROOT / "applications/pension-retirement/declaration"
    recipe = (declaration / "spec.yml").read_text(encoding="utf-8")
    assert replace_entry(recipe, "trellis", "trellis.x.yml") == recipe.replace(
        "trellis: trellis.yml\n", "trellis: trellis.x.yml\n"
    )
    trellis = (declaration / "trellis.yml").read_text(encoding="utf-8")
    assert replace_entry(trellis, "periods[1].template", "period.x.yml") == trellis.replace(
        "{template: period.yml,", "{template: period.x.yml,"
    )
    quoted = "trellis: 't.yml'  # quoted\n"
    assert replace_entry(quoted, "trellis", "u.yml") == "trellis: 'u.yml'  # quoted\n"
    assert replace_entry(quoted, "trellis", "it's.yml") == "trellis: 'it''s.yml'  # quoted\n"
    assert replace_entry('a: "x"\r\nb: 1\r\n', "a", "y") == 'a: "y"\r\nb: 1\r\n'
    with pytest.raises(KeyError, match="no key 'registry'"):
        replace_entry(recipe, "registry", "x")
    assert replace_entry("trellis: t.yml\n", "trellis", "2026") == 'trellis: "2026"\n'
    assert replace_entry("trellis: 't.yml'\n", "trellis", "2026") == "trellis: '2026'\n"
    assert replace_entry("trellis: t\n  u.yml\nstages: {}\n", "trellis", "v.yml") == (
        "trellis: v.yml\nstages: {}\n"
    )
    # the block mapping `stages` is replaced from its first key to the end of
    # its last entry, the comments before it and the line end after it kept
    assert replace_entry(recipe, "stages", "x") == (
        recipe[: recipe.index("worker_saving:  {")] + "x\n"
    )
    assert replace_entry("a: {}\nb: 1\n", "a", "x.yml") == "a: x.yml\nb: 1\n"
    # a double-quoted value with an escape is written anew within its quotes
    escaped = 'trellis: "t\\u0041.yml"\n'
    assert replace_entry(escaped, "trellis", "v.yml") == 'trellis: "v.yml"\n'
    # a tagged value is replaced whole, and its tag is not written again
    assert replace_entry("trellis: !path t.yml\n", "trellis", "v.yml") == "trellis: v.yml\n"
    with pytest.raises(ValueError, match="cannot be written as a string at 'trellis'"):
        replace_entry("trellis: &t t.yml\nother: *t\n", "trellis", "v.yml")


def test_a_number_a_boolean_and_a_tag_are_written_plain_and_every_other_character_is_kept():
    """`replace_entry` of `bellman.trellis` writes a number, a boolean and a
    tag, each as `entry_value` reads it, plain, and keeps every other
    character of the text: a number in place of a number, the comment after
    it kept, and in place of a value written in double quotes, whose quotes
    it drops; a float as YAML writes it, `1.0e-05`, which reads back as that
    number; a boolean; and a tag in place of a tag, `!pchip` for `!Linear`,
    and a tag with a value, written after one space. A number in place of
    an anchored value that an alias reads does not read back as the text
    with that one value replaced, and is refused with a ValueError, as is a
    list, a mapping or a tag on a list given as the value, the refusal
    naming the value's kind and not its text, so that a list read through
    aliases, whose text grows tenfold with each level of aliases, is
    refused in the sentence of any list (the model interface's amendment
    AMD-MI-002, §5)."""
    from bellman.trellis import entry_value, replace_entry

    text = (
        "calibration:\n"
        "  R: 1.045  # the gross return\n"
        '  β: "0.95"\n'
        "settings:\n"
        "  n_a: 300\n"
        "  tol: 0.001\n"
        "  verbose: false\n"
        "methods:\n"
        "  - on: cntn_to_dcsn.value\n"
        "    method: !Linear\n"
    )
    assert replace_entry(text, "calibration.R", 1.05) == text.replace("R: 1.045", "R: 1.05")
    assert replace_entry(text, "calibration.β", 0.95) == text.replace('β: "0.95"', "β: 0.95")
    assert replace_entry(text, "settings.n_a", 400) == text.replace("n_a: 300", "n_a: 400")
    small = replace_entry(text, "settings.tol", 1e-05)
    assert small == text.replace("tol: 0.001", "tol: 1.0e-05")
    assert entry_value(small, "settings.tol") == 1e-05
    assert replace_entry(text, "settings.verbose", True) == text.replace("false", "true")
    pchip = {"__yaml_tag__": "pchip", "value": ""}
    assert replace_entry(text, "methods[0].method", pchip) == text.replace("!Linear", "!pchip")
    grid = {"__yaml_tag__": "path", "value": "grid.yml"}
    assert replace_entry(text, "methods[0].method", grid) == text.replace(
        "!Linear", "!path grid.yml"
    )
    with pytest.raises(ValueError, match="cannot be written as a number at 'a'"):
        replace_entry("a: &x 1\nb: *x\n", "a", 2)
    # six levels, each a list of ten aliases of the level below
    expansion = entry_value(
        "[&l0 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "
        + ", ".join(f"&l{k} [" + ", ".join([f"*l{k - 1}"] * 10) + "]" for k in range(1, 6))
        + "]"
    )
    for value, named in (
        ([1.05], "a list"),
        (expansion, "a list"),
        ({"a": 1}, "a mapping"),
        ({"__yaml_tag__": "egm", "value": [[1]]}, "a tag on a collection"),
    ):
        with pytest.raises(ValueError) as refused:
            replace_entry(text, "calibration.R", value)
        assert str(refused.value) == (
            f"{named} is no string, int, float, boolean or tag, and cannot be written at "
            "'calibration.R'"
        )


def test_an_entry_is_appended_to_a_mapping_or_a_list_of_a_models_file_keeping_every_other_line():
    """`append_to_mapping` and `append_to_sequence` of `bellman.trellis` add
    one entry as text: in block style on a line of its own after the
    collection's last entry, where `entry_span` ends the collection, at the
    indentation of its keys or the column of its dashes; in flow style
    before the closing brace or bracket, after a comma where the collection
    holds an entry. Every other line is unchanged, comments included, and
    the new line ends as the line it follows does, with a carriage return
    and a line feed in a file whose lines end so. On the recipe, the period
    file and the trellis file of applications/pension-retirement/declaration/,
    on flow forms, on a text after "|" as the last entry, on a file whose
    lines end so, on two tagged texts, whose tags the package's reader
    keeps, and on refusals (the model interface's specification 0.3, §3.2)."""
    from bellman.trellis import append_to_mapping, append_to_sequence, entry_value

    pension = ROOT / "applications/pension-retirement/declaration"
    recipe = (pension / "spec.yml").read_text(encoding="utf-8")
    old = recipe.split("\n")
    new = append_to_mapping(recipe, ("stages",), "x", "{methods: {all: [stages/x/methods.bl]}}")
    terminal = (
        "  terminal:       {stage: stages/terminal/terminal.bl,             "
        "methods: {all: [stages/terminal/methods.bl]}, periods: [0, 0]}"
    )
    at = old.index(terminal) + 1
    assert new.split("\n") == old[:at] + ["  x: {methods: {all: [stages/x/methods.bl]}}"] + old[at:]
    period = (pension / "period.yml").read_text(encoding="utf-8")
    old = period.split("\n")
    at = old.index("  - retiree_saving") + 1
    new = append_to_sequence(period, ("stages",), "x")
    assert new.split("\n") == old[:at] + ["  - x"] + old[at:]
    trellis = (pension / "trellis.yml").read_text(encoding="utf-8")
    old = trellis.split("\n")
    at = old.index("  - {template: period.yml, repeat: 14}") + 1
    new = append_to_sequence(trellis, ("periods",), "{template: p.yml, repeat: 1}")
    assert new.split("\n") == old[:at] + ["  - {template: p.yml, repeat: 1}"] + old[at:]
    assert append_to_sequence("connectors: []\n", "connectors", "{m_next: m}") == (
        "connectors: [{m_next: m}]\n"
    )
    assert append_to_sequence("stages: [a, b]  # two\n", "stages", "c") == (
        "stages: [a, b, c]  # two\n"
    )
    assert append_to_mapping("stages: {a: 1}\n", "stages", "b", "2") == "stages: {a: 1, b: 2}\n"
    # a text after "|" ends before its line breaks, so the new key follows
    # its last line and the next key of the file keeps its place
    noted = "stages:\n  a: 1\n  note: |\n    a note\nregistry: 2\n"
    assert append_to_mapping(noted, "stages", "b", "2") == noted.replace(
        "a note\n", "a note\n  b: 2\n"
    )
    crlf = "!period\r\nname: p\r\nstages:\r\n  - a\r\n  - b\r\nconnectors:\r\n  - {}\r\n"
    new = append_to_sequence(crlf, "stages", "c")
    assert new == crlf.replace("  - b\r\n", "  - b\r\n  - c\r\n")
    assert entry_value(new, "stages") == ["a", "b", "c"]
    # the tagged root of a trellis file, and a list whose entries carry
    # method tags, the last a tag with no value: every tag reads back
    two = "!trellis\nperiods:\n  - stages: [worker]\n  - stages: [worker]\n"
    new = append_to_mapping(two, (), "inter_connectors", "[{a: k}]")
    assert new == two + "inter_connectors: [{a: k}]\n"
    assert entry_value(new) == {
        "__yaml_tag__": "trellis",
        "periods": [{"stages": ["worker"]}, {"stages": ["worker"]}],
        "inter_connectors": [{"a": "k"}],
    }
    # a list of tagged entries written inline, each tag with no value and the
    # list closed by comment lines, as the YAML methods files were written
    # before the additions replaced them
    tagged = (
        "name: tagged\n"
        "# three tagged entries\n"
        "entries:\n"
        "  - on: policy\n"
        "    method: !egm\n"
        "    settings: {grid: !Cartesian, orders: {a: n_a}, bounds: {a: [a_min, a_max]}}\n"
        "  - on: cntn_to_dcsn\n"
        "    method: !vfi\n"
        "  - on: cntn_to_dcsn.evaluate\n"
        "    method: !Linear\n"
        "    settings: {grid: !Cartesian, orders: {m: n_m}, bounds: {m: [m_min, m_max]}}\n"
        "\n"
        "# the comment lines that close the file\n"
        "# stand after the list\n"
    )
    new = append_to_sequence(tagged, "entries", "{on: dcsn_to_cntn}")
    # the entry stands after the list's last entry, before the comment lines that close the file
    last = "    settings: {grid: !Cartesian, orders: {m: n_m}, bounds: {m: [m_min, m_max]}}\n"
    assert tagged.count(last) == 1
    assert new == tagged.replace(last, last + "  - {on: dcsn_to_cntn}\n")
    read = entry_value(new, "entries")
    assert read == [*entry_value(tagged, "entries"), {"on": "dcsn_to_cntn"}]
    # the three tags in order, each read back as the tag of its entry
    assert [entry["method"]["__yaml_tag__"] for entry in read[:-1]] == ["egm", "vfi", "Linear"]
    with pytest.raises(ValueError, match="holds the key 'worker_saving'"):
        append_to_mapping(recipe, ("stages",), "worker_saving", "{}")
    with pytest.raises(ValueError, match="is no mapping"):
        append_to_mapping(period, ("stages",), "x", "1")
    with pytest.raises(KeyError, match="no key 'registry'"):
        append_to_sequence(recipe, ("registry",), "x")
    with pytest.raises(ValueError, match="is no list"):
        append_to_sequence(recipe, ("stages",), "x")


@pytest.mark.parametrize(
    ("text", "appender", "entry"),
    [
        (
            "stages:\n  a: 1\n  note: |+\n    a note\n\nregistry: 2\n",
            "append_to_mapping",
            ("b", "2"),
        ),
        ("stages: [\n  a,\n  b,\n]\n", "append_to_sequence", ("c",)),
        (
            "defaults: &d\n  x: 1\nstages:\n  a: 1\n  b: *d\n",
            "append_to_mapping",
            ("c", "3"),
        ),
    ],
    ids=["kept-line-breaks-last", "trailing-comma", "alias-last"],
)
def test_an_append_whose_result_does_not_hold_the_former_entries_and_the_new_one_is_refused(
    text, appender, entry
):
    """Each appender reads its result back, and refuses with a ValueError
    naming the address a result that does not read or in which the
    collection does not hold its former entries and then the new one: a
    text after "|+" as the last entry of the mapping, whose value keeps the
    blank line that the new line would cut from it; a trailing comma in a
    multi-line flow list; and an alias as the last entry of a block
    mapping, whose anchor stands in another mapping (the model interface's
    specification 0.3, §3.2)."""
    with pytest.raises(ValueError, match="at stages cannot be extended as text"):
        getattr(bellman.trellis, appender)(text, ("stages",), *entry)


def test_the_component_spans_of_a_header_slice_the_text_written(text_of):
    """After the authored items, the span table holds the place of each side
    of a block header, of each field the side lists and of each component
    of that field's typing (unit T of the model interface specification
    0.3, the classification table, §3): on `cons.bl` the continuation value
    is listed with its set and its role word on line 21 and again on line
    31, the control `c` writes its role word before its set on line 17, and
    its bare listing on line 21 has no component; on every stage file of
    the applications, at
    `applications/<model>/declaration/stages/<key>/<key>.bl`, the items
    keep their addresses and their order, and each entry after them slices
    the text written."""
    from conftest import CORPUS
    from bellman.syntax.vocabulary import ROLE_WORD

    def written(text, span):
        assert span.line == span.end_line
        return text.split("\n")[span.line - 1][span.column - 1 : span.end_column - 1]

    text = text_of("cons")
    term, spans = parse_with_spans(text, filename=CORPUS["cons"])
    items = [address for address, _ in item_addresses(term)]
    assert list(spans)[: len(items)] == items and len(spans) == len(items) + 39
    assert {address: written(text, spans[address]) for address in (
        "cntn_to_dcsn.in", "cntn_to_dcsn.in.V[>]", "cntn_to_dcsn.in.V[>].domain",
        "cntn_to_dcsn.in.V[>].role", "cntn_to_dcsn.in.c", "policy.in.V[>].domain",
        "dcsn_to_cntn.in.c.role", "dcsn_to_cntn.in.c.domain", "dcsn_to_cntn.out")} == {
        "cntn_to_dcsn.in": "(V[>] : [-inf, inf) @ !vlu, c) : !cntn",
        "cntn_to_dcsn.in.V[>]": "V[>] : [-inf, inf) @ !vlu",
        "cntn_to_dcsn.in.V[>].domain": "[-inf, inf)",
        "cntn_to_dcsn.in.V[>].role": "!vlu",
        "cntn_to_dcsn.in.c": "c",
        "policy.in.V[>].domain": "[-inf, inf)",
        "dcsn_to_cntn.in.c.role": "!ctrl",
        "dcsn_to_cntn.in.c.domain": "ℝ₊₊",
        "dcsn_to_cntn.out": "(a : Xa) : !cntn",
    }
    domain = spans["cntn_to_dcsn.in.V[>].domain"]
    assert (domain.file, domain.line, domain.column, domain.end_line, domain.end_column) == (
        CORPUS["cons"], 20, 27, 20, 38)
    assert not {"cntn_to_dcsn.in.c.domain", "cntn_to_dcsn.in.c.role"} & set(spans)
    roles = {"!" + word for word in ROLE_WORD.values()}
    assert len(STAGE_FILES) > 30
    for path in STAGE_FILES:
        text = path.read_text(encoding="utf-8")
        term, spans = parse_with_spans(text, filename=str(path.relative_to(ROOT)))
        items = [address for address, _ in item_addresses(term)]
        assert list(spans)[: len(items)] == items, path
        for address in list(spans)[len(items):]:
            parts = address.split(".")
            text_written = written(text, spans[address])
            assert {"in", "out"} & set(parts), (path, address)
            if parts[-1] == "domain":
                assert text_written and not text_written.startswith("!"), (path, address)
            elif parts[-1] == "role":
                assert text_written in roles, (path, address)
            elif parts[-1] == "perch":
                assert text_written in {"!arvl", "!dcsn", "!cntn"}, (path, address)
            elif parts[-1] not in ("in", "out"):
                assert text_written.startswith(parts[-1]), (path, address)


# --- unit J of the model interface specification 0.4: the readers take the
# texts of unsaved buffers (spec 0.4 §3.1; the unit's brief, rule 2) ----------


def test_the_readers_take_an_unsaved_text_in_place_of_its_file(tmp_path):
    """Given a mapping from a file's resolved path to a text, the readers
    read the text in the file's place (spec 0.4 §3.1). With texts of the
    portfolio model's trellis file and of `trellis.port-cons.yml` that write
    `repeat: 5`, `read_trellis_file` and `load_recipe` answer five periods of
    the first and `load_trellis` five of the second; each records the digest
    of the text it read and, under `texts`, the one path it took of the two
    the mapping holds; `written_at` counts five periods; neither file on
    disk changes."""
    from bellman.factory.loading import read_trellis_file
    from bellman.trellis import written_at

    registry, port_cons = declarations_copy(tmp_path)
    trellis = registry / "trellis.yml"
    on_disk = {path: path.read_text(encoding="utf-8") for path in (trellis, port_cons)}
    texts = {}
    for path, text in on_disk.items():
        assert text.count("repeat: 6") == 1, path
        texts[str(path.resolve())] = text.replace("repeat: 6", "repeat: 5")
    key, port_key = str(trellis.resolve()), str(port_cons.resolve())

    def digest(path):
        """The SHA-256 of the UTF-8 bytes of the text the mapping holds for `path`."""
        return hashlib.sha256(texts[path].encode("utf-8")).hexdigest()

    read = read_trellis_file(trellis, texts=texts)
    assert (len(read["periods"]), read["sha256"], read["texts"]) == (5, digest(key), [key])
    syntactic = load_recipe(registry, "spec.yml", texts)
    assert len(syntactic["periods"]) == 5
    assert syntactic["provenance"]["trellis"]["sha256"] == digest(key)
    assert syntactic["provenance"]["texts"] == [key]
    loaded = load_trellis(port_cons, texts=texts)
    assert len(loaded["periods"]) == 5
    assert loaded["provenance"]["trellis"]["sha256"] == digest(port_key)
    assert loaded["provenance"]["texts"] == [port_key]
    # the sixth period is written on disk and not in the text
    assert written_at(trellis, "periods[5].connectors[0]") == (
        str(registry / "period.yml"),
        "connectors[0]",
    )
    with pytest.raises(KeyError):
        written_at(trellis, "periods[5].connectors[0]", texts)
    assert {path: path.read_text(encoding="utf-8") for path in on_disk} == on_disk


def test_a_period_file_and_a_recipe_are_read_from_the_mapping(tmp_path):
    """A text of the period file and a text of the recipe are read in their
    files' places (spec 0.4 §3.1), each path resolved by the package, here
    reached through `stages/..`: the period file's text with a second
    connector is read by `period_and_repeat` and by `load_recipe`, and the
    recipe's text with a `registry` block by `load_recipe`, which records the
    digest of the recipe's text and both paths under `texts`; `written_at`
    answers the period file for the second connector of period 3."""
    from bellman.factory.loading import period_and_repeat
    from bellman.trellis import written_at

    registry, _ = declarations_copy(tmp_path)
    directory = registry / "stages" / ".."
    period, recipe = registry / "period.yml", registry / "spec.yml"
    period_text = period.read_text(encoding="utf-8") + "  - {}\n"
    recipe_text = recipe.read_text(encoding="utf-8") + (
        "registry:\n  calibration: [calibration/portfolio]\n"
    )
    texts = {str(period.resolve()): period_text, str(recipe.resolve()): recipe_text}

    expanded, repeat = period_and_repeat(
        {"template": "period.yml", "repeat": 6},
        directory,
        directory / "trellis.yml",
        "periods[0]",
        texts,
    )
    assert (expanded["connectors"], repeat) == ([{"m_next": "m"}, {}], 6)
    assert load_recipe(directory, "spec.yml")["registry"] == {}
    syntactic = load_recipe(directory, "spec.yml", texts)
    assert [each["connectors"] for each in syntactic["periods"]] == [[{"m_next": "m"}, {}]] * 6
    assert list(syntactic["registry"]) == ["calibration"] and syntactic["registry"]["calibration"]
    assert (
        syntactic["provenance"]["recipe"]["sha256"]
        == hashlib.sha256(recipe_text.encode("utf-8")).hexdigest()
    )
    assert syntactic["provenance"]["texts"] == sorted(texts)
    assert written_at(registry / "trellis.yml", "periods[3].connectors[1]", texts) == (
        str(period),
        "connectors[1]",
    )


def test_a_reading_without_texts_answers_what_it_answered(tmp_path):
    """A reading given no text it takes answers what it answers without the
    mapping (spec 0.4 §3.1): `load_recipe`, `load_trellis` and
    `read_trellis_file`, given the empty mapping or a mapping of a file they
    do not read and of stage files and binding sources, which the readers
    never take from it, answer as they answer with no mapping, and no
    answer holds the key `texts`."""
    from bellman.factory.loading import read_trellis_file

    registry, port_cons = declarations_copy(tmp_path)
    trellis = registry / "trellis.yml"
    untaken = {
        str((registry / "notes.yml").resolve()): "periods: []\n",
        str((registry / "stages/cons/cons.bl").resolve()): "@stage: cons\n",
        str((registry / "calibration/portfolio.yml").resolve()): "calibration: {}\n",
        str((port_cons.parent / "calibration/portfolio.yml").resolve()): "{}\n",
    }
    recipe = load_recipe(registry, "spec.yml")
    loaded = load_trellis(port_cons)
    read = read_trellis_file(trellis)
    assert not {"texts"} & (set(recipe["provenance"]) | set(loaded["provenance"]) | set(read))
    for texts in ({}, untaken):
        assert load_recipe(registry, "spec.yml", texts) == recipe
        assert load_trellis(port_cons, texts=texts) == loaded
        assert read_trellis_file(trellis, texts=texts) == read


def test_load_recipe_refuses_texts_given_as_a_keyword(tmp_path):
    """The mapping of texts is the third positional argument of
    `load_recipe`, which no slot can name; given as the keyword `texts`, it
    is read as a slot the recipe does not write and refused under
    `recipe-slot-unknown` (the unit's decision J-D1)."""
    registry, _ = declarations_copy(tmp_path)
    with pytest.raises(FactoryError) as refused:
        load_recipe(registry, "spec.yml", texts={})
    assert refused.value.rule == "recipe-slot-unknown"


# --- unit J of the model interface specification 0.4: the queries that name
# where a connector line is written and which entry writes each period (spec
# 0.4 §3.1; the unit's brief, rule 3) ------------------------------------------


def test_connector_entry_answers_the_flat_connector_in_the_entry_that_writes_the_period(
    tmp_path,
):
    """A drag within a period from `port`'s continuation field, `w` in
    cons-port's copy and `m_next` in the portfolio registry's, to `cons`'s
    `m`, each name held by one stage occurrence in every period, is answered
    as the flat connector `{w: m}` or `{m_next: m}` in the first empty mapping of the
    `connectors` list that writes the period, a line that reaches the six
    periods that list writes (spec 0.4 §3.1): in the trellis file's entry
    where the trellis writes its periods out; in the period file the entry
    names where the entry writes no `connectors`; and in the trellis file's
    entry where it writes `connectors` over those of its period file."""
    from bellman.factory.file_entries import connector_entry

    port_cons = emptied_port_cons(tmp_path / "port-cons")
    portfolio = emptied_portfolio(tmp_path / "portfolio")
    entry = emptied_portfolio_entry(tmp_path / "entry")
    six = (0, 1, 2, 3, 4, 5)
    for trellis, file, address, field in (
        (specify_trellis(load_trellis(port_cons)), port_cons, "periods[0].connectors[0]", "w"),
        (specify_trellis(load_recipe(portfolio, "spec.yml")), portfolio / "period.yml",
         "connectors[0]", "m_next"),
        (specify_trellis(load_recipe(entry, "spec.yml")), entry / "trellis.yml",
         "periods[0].connectors[0]", "m_next"),
    ):
        assert connector_entry(trellis, (2, "port", field), (2, "cons", "m")) == (
            str(file), address, six, f"{{{field}: m}}", None, None, None)


def test_connector_entry_appends_where_no_mapping_is_empty(tmp_path):
    """Where the `connectors` list that writes the period holds no empty
    mapping, the line is appended to the list, and the answer is the list's
    address (spec 0.4 §3.1). In a copy of `trellis.port-cons.yml` whose
    list holds the one filled connector `{w: m}` and whose five
    inter-period mappings are empty, a drag within a period from `disc`'s
    `a` to `port`'s `k` writes the stage key before `a`, since `cons`
    continues to `a` as well (AMD-COMP-001 §3). That line closes a cycle of
    the period's pairs through the inferred pair of `port`'s `w` and
    `cons`'s `m`, which the selection withdraws when it reads the typed
    line; the query names only where the line is written. In a text of the
    emptied copy whose list is written `[]`, the flat connector is appended
    to that list."""
    from bellman.factory.file_entries import connector_entry

    six = (0, 1, 2, 3, 4, 5)
    five = five_mappings_port_cons(tmp_path / "five")
    assert connector_entry(
        specify_trellis(load_trellis(five)), (2, "disc", "a"), (2, "port", "k")
    ) == (str(five), "periods[0].connectors", six,
          "{disc.a: k}", None, (2, "cons"),
          ("cntn", "a", ("cons", "disc")))
    port_cons = emptied_port_cons(tmp_path / "port-cons")
    text = port_cons.read_text(encoding="utf-8")
    assert text.count("connectors:\n      - {}\n") == 1
    texts = {
        str(port_cons.resolve()): text.replace("connectors:\n      - {}\n", "connectors: []\n")
    }
    trellis = specify_trellis(load_trellis(port_cons, texts=texts))
    assert connector_entry(trellis, (2, "port", "w"), (2, "cons", "m"), texts) == (
        str(port_cons), "periods[0].connectors", six, "{w: m}", None, None, None)


def test_connector_entry_answers_no_mapping_where_the_period_writes_no_connectors_list(tmp_path):
    """Where neither the period's entry nor the period file it names writes
    a `connectors` list, the drag within the period is answered as
    `no-mapping` at the address of the entry, with the line that was not
    written and the periods the entry writes (the plan's decision J-D25):
    the entry `periods[0]` of a text of `trellis.port-cons.yml` with no
    `connectors`, and the empty address of a text of `period.yml` with
    none."""
    from bellman.factory.file_entries import connector_entry

    six = (0, 1, 2, 3, 4, 5)
    port_cons = emptied_port_cons(tmp_path / "port-cons")
    registry = emptied_portfolio(tmp_path / "portfolio")
    for file, written, address, syntactic, field in (
        (port_cons, "    connectors:\n      - {}\n", "periods[0]",
         lambda texts: load_trellis(port_cons, texts=texts), "w"),
        (registry / "period.yml", "connectors:\n  - {}\n", "",
         lambda texts: load_recipe(registry, "spec.yml", texts), "m_next"),
    ):
        text = file.read_text(encoding="utf-8")
        assert text.count(written) == 1
        texts = {str(file.resolve()): text.replace(written, "")}
        assert connector_entry(
            specify_trellis(syntactic(texts)), (2, "port", field), (2, "cons", "m"), texts
        ) == (str(file), address, six, f"{{{field}: m}}", "no-mapping", None, None)


def test_connector_entry_answers_the_inter_period_mapping_and_the_pairs_it_reaches(tmp_path):
    """A drag from `disc`'s `a` in `periods[3]` to `port`'s `k` in
    `periods[2]`, the period after it in time, is answered as the entry
    `disc.a: k` of the inter-period mapping that joins the two periods,
    qualified because `cons` also continues to `a` (spec 0.4
    §3.1): `inter_connectors[0]`, reaching every period, where the trellis
    file writes the one mapping that stands for every pair;
    `inter_connectors[2]`, reaching the two periods of the pair alone, where
    it writes one mapping for each of its five pairs; and the reason
    `no-mapping` at the address `inter_connectors`, reaching no period,
    where the text read in the trellis file's place writes no mapping."""
    from bellman.factory.file_entries import connector_entry

    standing = emptied_port_cons(tmp_path / "standing")
    five = five_mappings_port_cons(tmp_path / "five")
    writing, reading = (3, "disc", "a"), (2, "port", "k")
    assert connector_entry(specify_trellis(load_trellis(standing)), writing, reading) == (
        str(standing), "inter_connectors[0]", (0, 1, 2, 3, 4, 5), "disc.a: k", None,
        (3, "cons"), ("cntn", "a", ("cons", "disc")))
    assert connector_entry(specify_trellis(load_trellis(five)), writing, reading) == (
        str(five), "inter_connectors[2]", (2, 3), "disc.a: k", None,
        (3, "cons"), ("cntn", "a", ("cons", "disc")))
    text = standing.read_text(encoding="utf-8")
    assert text.count("inter_connectors:\n  - {}\n") == 1
    texts = {str(standing.resolve()): text.replace("inter_connectors:\n  - {}\n", "")}
    trellis = specify_trellis(load_trellis(standing, texts=texts))
    assert connector_entry(trellis, writing, reading, texts) == (
        str(standing), "inter_connectors", (), "a: k", "no-mapping", None, None)


def test_connector_entry_qualifies_a_shared_name_within_a_period_and_between_periods(
    tmp_path,
):
    """In periods holding `cons_one` and `cons_two`, two occurrences of
    `cons.bl` that both arrive at `m`, a drag within `periods[1]` from
    `port`'s `m_next` to `cons_one`'s `m` writes the stage key before the
    colliding endpoint alone, `{m_next: cons_one.m}`, which resolves to the
    two dragged and no other (AMD-COMP-001 §3), `shared` naming `cons_two`
    in that period and `held` the perch `arvl`, the name `m` and the two
    occurrences that hold it; a drag to the same port from `disc`'s `a` in
    `periods[2]` writes both keys, since `cons` continues to `a` as well
    and two stages arrive at `m`, and the line resolves at every pair the
    mapping joins. The spelling is chosen on every period the `connectors`
    list writes: in texts of the portfolio model's trellis file, with two
    entries naming `period.yml`, the second listing `cons_two` beside
    `cons`, and of its recipe, which adds `cons_two`, a drag within
    `periods[0]`, which holds `cons` alone, qualifies `m`, `shared` naming
    `cons_two` in `periods[3]`. Under the one mapping that stands for every
    pair, a drag between two periods qualifies the endpoint another pair
    shares, and `held` names what that pair's occurrences hold: from
    `disc`'s `a` in `periods[3]` to `cons`'s `m` in `periods[2]`, the two
    occurrences of `periods[3]` that arrive at `m`, in the pair of
    `periods[4]` and `periods[3]`; and, where the second entry lists
    `port_two` beside `port`, from `port`'s `m_next` in `periods[2]` to
    `cons`'s `m` in `periods[1]`, the two occurrences of `periods[3]` that
    continue to `m_next`."""
    from bellman.factory.file_entries import connector_entry

    file = two_cons_period(tmp_path / "two-cons")
    trellis = specify_trellis(load_trellis(file))
    six = (0, 1, 2, 3, 4, 5)
    arriving = ("arvl", "m", ("cons_one", "cons_two"))
    assert connector_entry(trellis, (1, "port", "w"), (1, "cons_one", "m")) == (
        str(file), "periods[0].connectors[0]", six,
        "{w: cons_one.m}", None, (1, "cons_two"), arriving)
    assert connector_entry(trellis, (2, "disc", "a"), (1, "cons_one", "m")) == (
        str(file), "inter_connectors[0]", six, "disc.a: cons_one.m", None, (1, "cons_two"), arriving)
    registry = emptied_portfolio(tmp_path / "portfolio")
    entries, recipe = registry / "trellis.yml", registry / "spec.yml"
    entry = "- {template: period.yml, repeat: 6}"
    assert entries.read_text(encoding="utf-8").count(entry) == 1
    # the occurrence the second entry adds, the stages it lists, the stage
    # folder of the added occurrence, and each drag with its answer
    for key, stages, stage, drags in (
        ("cons_two", "port, cons, cons_two, disc", "cons", [
            ((0, "port", "m_next"), (0, "cons", "m"), (
                str(registry / "period.yml"), "connectors[0]", six,
                "{m_next: cons.m}", None, (3, "cons_two"),
                ("arvl", "m", ("cons", "cons_two")))),
            ((3, "disc", "a"), (2, "cons", "m"), (
                str(entries), "inter_connectors[0]", six, "disc.a: cons.m", None,
                (3, "cons_two"), ("arvl", "m", ("cons", "cons_two")))),
        ]),
        ("port_two", "port, port_two, cons, disc", "port", [
            ((2, "port", "m_next"), (1, "cons", "m"), (
                str(entries), "inter_connectors[0]", six, "port.m_next: m", None,
                (3, "port_two"), ("cntn", "m_next", ("port", "port_two")))),
        ]),
    ):
        texts = {
            str(entries.resolve()): entries.read_text(encoding="utf-8").replace(
                entry,
                "- {template: period.yml, repeat: 3}\n"
                f"  - {{template: period.yml, repeat: 3, stages: [{stages}]}}",
            ),
            str(recipe.resolve()): recipe.read_text(encoding="utf-8")
            + f"  {key}: {{stage: stages/{stage}/{stage}.bl, calibration: "
            f"{{all: [calibration/portfolio]}}, settings: {{all: [settings/{stage}]}}, "
            f"methods: {{all: [stages/{stage}/methods]}}}}\n",
        }
        trellis = specify_trellis(load_recipe(registry, "spec.yml", texts))
        for writing, reading, answer in drags:
            assert connector_entry(trellis, writing, reading, texts) == answer, (writing, reading)


def test_connector_entry_refuses_a_joined_port_and_a_period_that_is_not_adjacent(tmp_path):
    """A gesture the rule of spec 0.4 §3.1 does not admit is answered as a
    fact and raises nothing (the unit's decision J-D4): `port-joined` where
    a join reads the writing port, since a continuation field joins one
    arrival field, or where a port names no state field of the trellis, as
    a field no stage declares or a period the trellis does not hold;
    `not-adjacent` where the reading port stands neither in the writing
    port's period nor in the period after it in time, or on the writing
    port's own stage occurrence. Neither answer names a file, an address, a
    period or a text. A reading port that a join reaches is admitted (unit
    J's decision J-D41): `disc`'s `a`, which `cons`'s `a` reaches by equal
    names, a join no entry writes, takes a new connector, as an arrival no
    join reaches does (J-D42)."""
    from bellman.factory.file_entries import connector_entry

    file = emptied_port_cons(tmp_path)
    trellis = specify_trellis(load_trellis(file))
    joined = (None, None, (), None, "port-joined", None, None)
    apart = (None, None, (), None, "not-adjacent", None, None)
    six = (0, 1, 2, 3, 4, 5)
    for writing, reading, answer in (
        # a join by name reads `cons`'s `a` and reaches `disc`'s `a`
        ((2, "cons", "a"), (2, "port", "k"), joined),
        ((2, "port", "w"), (2, "disc", "a"),
         (str(file), "periods[0].connectors[0]", six, "{w: a}", None, None, None)),
        ((2, "port", "z"), (2, "cons", "m"), joined),
        ((9, "disc", "a"), (8, "port", "k"), joined),
        ((3, "disc", "a"), (1, "port", "k"), apart),
        ((2, "disc", "a"), (3, "port", "k"), apart),
        ((2, "port", "w"), (2, "port", "k"), apart),
    ):
        assert connector_entry(trellis, writing, reading) == answer, (writing, reading)


def test_j_a_reached_arrival_takes_a_further_key_of_the_mapping_that_joins_it():
    """Branching in (unit J's decisions J-D41 and J-D42; spec 0.4 §3.1 as
    J-D41 amends it): an arrival field that a join already reaches takes a
    further source, and `connector_entry` answers a further key of the
    mapping whose entry writes that join, so that the count of mappings
    never changes. In the durables model read with its trellis file's text
    changed (`load_recipe`'s texts): with `a_nxt_adj: a_bq` taken out of the
    terminal period's flat connector, the drag from `adjuster_cons`'s
    `a_nxt_adj` to `bequest`'s `a_bq`, which `keeper_cons`'s `a_nxt_kp`
    still reaches, is the key `a_nxt_adj: a_bq` of that connector; with
    `a_nxt_adj: a` taken out of the standing inter-period mapping, the drag
    from `adjuster_cons`'s `a_nxt_adj` in `periods[2]` to `tenure`'s `a` in
    `periods[1]` is the key `a_nxt_adj: a` of that mapping, reaching every
    period. A continuation field that a join reads starts no second line:
    `keeper_cons`'s `a_nxt_kp` is `port-joined`. In the pension model, whose
    terminal connector is written keyed from `retire_choice` to `terminal`
    for `y_f_wk` and flat for the other sources, the drag from
    `retire_choice`'s `y_f_rt` to `terminal`'s `y_f_T` is a further key of
    the keyed connector's `fields`, the first of the list that writes a
    join reaching `y_f_T`."""
    from conftest import PENSION

    from bellman.factory.file_entries import connector_entry

    file = DURABLES / "trellis.yml"
    text = file.read_text(encoding="utf-8")
    connector = (
        "{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, "
        "a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}"
    )
    mapping = "{a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}"
    assert text.count(connector) == 1 and text.count(mapping) == 1
    for old, new, writing, reading, answer in (
        (
            connector,
            connector.replace(" a_nxt_adj: a_bq,", ""),
            (0, "adjuster_cons", "a_nxt_adj"),
            (0, "bequest", "a_bq"),
            (str(file), "periods[0].connectors[0]", (0,), "{a_nxt_adj: a_bq}") + (None,) * 3,
        ),
        (
            mapping,
            mapping.replace(" a_nxt_adj: a,", ""),
            (2, "adjuster_cons", "a_nxt_adj"),
            (1, "tenure", "a"),
            (str(file), "inter_connectors[0]", tuple(range(51)), "a_nxt_adj: a") + (None,) * 3,
        ),
    ):
        texts = {str(file.resolve()): text.replace(old, new)}
        trellis = elaborate_trellis(load_recipe(DURABLES, "spec.yml", texts))
        assert connector_entry(trellis, writing, reading, texts) == answer, reading
        kept = (writing[0], "keeper_cons", "a_nxt_kp")
        assert connector_entry(trellis, kept, reading, texts) == (
            None, None, (), None, "port-joined", None, None)

    pension = PENSION / "trellis.yml"
    text = pension.read_text(encoding="utf-8")
    flat = (
        "- {y_f_wk: y_f_T, y_p_wk: y_p_T, y_f_rt: y_f_T, y_p_rt: y_p_T, "
        "y_f_ret: y_f_T, y_p_ret: y_p_T}"
    )
    keyed = (
        "- {from: retire_choice, to: terminal, fields: {y_f_wk: y_f_T}}\n"
        "      - {y_p_wk: y_p_T, y_p_rt: y_p_T, y_f_ret: y_f_T, y_p_ret: y_p_T}"
    )
    assert text.count(flat) == 1
    texts = {str(pension.resolve()): text.replace(flat, keyed)}
    trellis = elaborate_trellis(load_recipe(PENSION, "spec.yml", texts))
    assert connector_entry(
        trellis, (0, "retire_choice", "y_f_rt"), (0, "terminal", "y_f_T"), texts
    ) == (str(pension), "periods[0].connectors[0].fields", (0,), "{y_f_rt: y_f_T}") + (None,) * 3


def test_period_entries_answers_each_periods_file_address_and_periods(tmp_path):
    """`period_entries` answers in one reading, for each period of the
    expanded trellis, the file that writes the period, the address of its
    entry in that file and every period that entry writes (the unit's
    brief, rule 3, and its review's finding 10): the entry `periods[0]` of
    `trellis.port-cons.yml` for the six periods it writes out; the period
    file, at the empty address, for the six periods of the portfolio model,
    whether or not the entry writes its own `connectors`; and for the
    pension model the terminal period written out in the trellis file and
    the fourteen earlier periods from `period.yml`. A text of the trellis
    file in the mapping of unsaved texts is read in the file's place."""
    from bellman.factory.file_entries import period_entries

    port_cons = emptied_port_cons(tmp_path / "port-cons")
    six = (0, 1, 2, 3, 4, 5)
    assert period_entries(port_cons) == [(str(port_cons), "periods[0]", six)] * 6
    for registry in (
        emptied_portfolio(tmp_path / "portfolio"),
        emptied_portfolio_entry(tmp_path / "entry"),
    ):
        assert period_entries(registry / "trellis.yml") == [
            (str(registry / "period.yml"), "", six)] * 6
    pension = ROOT / "applications/pension-retirement/declaration/trellis.yml"
    assert period_entries(pension) == [(str(pension), "periods[0]", (0,))] + [
        (str(pension.parent / "period.yml"), "", tuple(range(1, 15)))] * 14
    text = port_cons.read_text(encoding="utf-8")
    assert text.count("repeat: 6") == 1
    texts = {str(port_cons.resolve()): text.replace("repeat: 6", "repeat: 4")}
    assert period_entries(port_cons, texts) == [(str(port_cons), "periods[0]", (0, 1, 2, 3))] * 4


def test_unjoined_fields_holds_the_two_ends_of_a_complete_trellis(tmp_path):
    """In the complete trellis of `trellis.port-cons.yml` the one
    continuation state field no join reads is `disc`'s `a` in the terminal
    period, and the one arrival state field no join reaches is `port`'s `k`
    in the earliest period: the two ends of the trellis (the unit's brief,
    §1). Every other arrival state field keeps the address of the entry that
    writes each join reaching it (unit J's decisions J-D41 and J-D42):
    `cons`'s `m` the period's connector, `port`'s `k` the inter-period
    mapping that joins the period before it, and `disc`'s `a`, joined by
    equal names, none. With the connector and the inter-period mapping
    emptied, every period holds `disc`'s `a` and `port`'s `w` among the
    first and `cons`'s `m` and `port`'s `k` among the second, and `disc`'s
    `a` alone is reached."""
    from bellman.factory.joins import unjoined_fields

    _, complete = declarations_copy(tmp_path / "complete")
    assert unjoined_fields(specify_trellis(load_trellis(complete))) == {
        "writing": [(0, "disc", "a")],
        "reading": [(5, "port", "k")],
        "sources": {
            **{(h, "cons", "m"): (f"periods[{h}].connectors[0]",) for h in range(6)},
            **{(h, "disc", "a"): (None,) for h in range(6)},
            **{(h, "port", "k"): (f"inter_connectors[{h}]",) for h in range(5)},
        },
    }
    emptied = specify_trellis(load_trellis(emptied_port_cons(tmp_path / "emptied")))
    assert unjoined_fields(emptied) == {
        "writing": sorted((h, key, field) for h in range(6)
                          for key, field in (("disc", "a"), ("port", "w"))),
        "reading": sorted((h, key, field) for h in range(6)
                          for key, field in (("cons", "m"), ("port", "k"))),
        "sources": {(h, "disc", "a"): (None,) for h in range(6)},
    }


def test_insert_in_sequence_places_an_item_and_keeps_the_layout():
    """`insert_in_sequence` of `bellman.trellis` places one item before the
    item at an index of a list (model interface spec 0.4 §3.6): in block
    style on a line of its own just before the line of that item's dash, at
    the dash's column, the new line ending as that line ends; in flow style
    before that item, followed by a comma. The first, a middle and the last
    index are taken, the last being the append of `append_to_sequence`. A
    comment after an item stays on that item's line and a comment line
    stays where it stands; every other character is kept. Refused: an
    address at which no list stands, an address the text does not hold,
    with a KeyError, an index that is no whole number within the list, an
    item that does not read as YAML, a dash that is not the first character
    of its line, and an item that does not compose in the list as it
    composes alone."""
    from bellman.trellis import append_to_sequence, entry_value, insert_in_sequence

    block = "!period\nname: p\nstages:\n  - a  # the first\n  - b\n  # before c\n  - c\nconnectors:\n  - {}\n"
    assert insert_in_sequence(block, "stages", 0, "x") == block.replace("  - a  #", "  - x\n  - a  #")
    assert insert_in_sequence(block, "stages", 1, "x") == block.replace("  - b\n", "  - x\n  - b\n")
    assert insert_in_sequence(block, "stages", 2, "x") == block.replace("  - c\n", "  - x\n  - c\n")
    assert insert_in_sequence(block, "stages", 3, "x") == append_to_sequence(block, "stages", "x")
    assert entry_value(insert_in_sequence(block, "stages", 1, "x"), "stages") == ["a", "x", "b", "c"]
    crlf = block.replace("\n", "\r\n")
    assert insert_in_sequence(crlf, "stages", 1, "x") == crlf.replace("  - b\r\n", "  - x\r\n  - b\r\n")
    # a list written at its key's indentation
    flush = "stages:\n- a\n- b\n"
    assert insert_in_sequence(flush, "stages", 1, "x") == "stages:\n- a\n- x\n- b\n"
    flow = "stages: [a, b, c]  # three\n"
    assert insert_in_sequence(flow, "stages", 0, "x") == "stages: [x, a, b, c]  # three\n"
    assert insert_in_sequence(flow, "stages", 2, "x") == "stages: [a, b, x, c]  # three\n"
    assert insert_in_sequence(flow, "stages", 3, "x") == "stages: [a, b, c, x]  # three\n"
    assert insert_in_sequence("connectors: []\n", "connectors", 0, "{m_next: m}") == (
        "connectors: [{m_next: m}]\n"
    )
    # a period entry placed between the two entries of the pension model's
    # trellis file, the second followed by comment lines
    pension = (ROOT / "applications/pension-retirement/declaration/trellis.yml").read_text(
        encoding="utf-8"
    )
    old = pension.split("\n")
    at = old.index("  - {template: period.yml, repeat: 14}")
    new = insert_in_sequence(pension, "periods", 1, "{template: period.new.yml, repeat: 1}")
    assert new.split("\n") == old[:at] + ["  - {template: period.new.yml, repeat: 1}"] + old[at:]
    with pytest.raises(ValueError, match="the entry name is no list"):
        insert_in_sequence(block, "name", 0, "x")
    with pytest.raises(KeyError, match="no key 'registry'"):
        insert_in_sequence(block, "registry", 0, "x")
    for index in (-1, 4, 1.0, True):
        with pytest.raises(ValueError, match="lies outside the list stages of length 3"):
            insert_in_sequence(block, "stages", index, "x")
    with pytest.raises(ValueError, match="does not read as YAML"):
        insert_in_sequence(block, "stages", 1, "[x")
    # the dashes of a list nested in a list's item follow another dash
    with pytest.raises(ValueError, match=r"at stages\[0\] cannot be extended as text"):
        insert_in_sequence("stages:\n  - - a\n    - b\n", "stages[0]", 0, "x")
    # alone, `x: 1, y` is one mapping; within a flow list, two items
    with pytest.raises(ValueError, match="at stages cannot be extended as text"):
        insert_in_sequence(flow, "stages", 1, "x: 1, y")


def test_split_entry_divides_a_repeated_entry_in_two():
    """`split_entry` of `bellman.trellis` writes the entry at an address, an
    item of a list that writes `repeat: n`, twice in its place, the first
    with `repeat: at` and the second with `repeat: n - at` (model interface
    spec 0.4 §3.6): an entry in flow style within a block list and within a
    flow list; the block-style entry of `trellis.port-cons.yml`, whose lines
    are written twice; and the last entry of the pension model's trellis
    file, followed by comment lines, which stay after the second entry.
    Every other character is kept. Refused: an address that names no item
    of a list, an index outside the list, a scalar read as a list, an entry
    that writes no integer `repeat`, among them one whose repeat its period
    file gives (the plan's ruling of Task 3), an `at` that is no whole
    number from one to `n - 1`, and a dash that is not the first character
    of its line."""
    from bellman.trellis import entry_value, split_entry

    flow_entry = "!trellis\nperiods:\n  - {template: period.yml, repeat: 6}\ninter_connectors:\n  - {a: k}\n"
    assert split_entry(flow_entry, "periods[0]", 3) == flow_entry.replace(
        "  - {template: period.yml, repeat: 6}\n",
        "  - {template: period.yml, repeat: 3}\n  - {template: period.yml, repeat: 3}\n",
    )
    assert entry_value(split_entry(flow_entry, "periods[0]", 2), "periods") == [
        {"template": "period.yml", "repeat": 2},
        {"template": "period.yml", "repeat": 4},
    ]
    flow_list = "periods: [{template: period.yml, repeat: 6}, {template: last.yml}]  # two\n"
    assert split_entry(flow_list, "periods[0]", 1) == (
        "periods: [{template: period.yml, repeat: 1}, {template: period.yml, repeat: 5}, "
        "{template: last.yml}]  # two\n"
    )
    # the trellis file of records of the portfolio-first order that remains since the two cons-port folders
    # became one (28 October 2026); the order's own file lists stage keys for its recipe
    port_cons = (ROOT / "applications/cons-port/declaration/trellis.port-cons-vfi.yml").read_text(
        encoding="utf-8"
    )
    start = port_cons.index("  - stages:\n")
    end = port_cons.index("    repeat: 6\n") + len("    repeat: 6\n")
    entry = port_cons[start:end]
    new = split_entry(port_cons, "periods[0]", 2)
    assert new == (
        port_cons[:start]
        + entry.replace("repeat: 6", "repeat: 2")
        + entry.replace("repeat: 6", "repeat: 4")
        + port_cons[end:]
    )
    read = entry_value(port_cons, "periods[0]")
    assert entry_value(new, "periods") == [{**read, "repeat": 2}, {**read, "repeat": 4}]
    pension = (ROOT / "applications/pension-retirement/declaration/trellis.yml").read_text(
        encoding="utf-8"
    )
    assert split_entry(pension, "periods[1]", 4) == pension.replace(
        "  - {template: period.yml, repeat: 14}\n",
        "  - {template: period.yml, repeat: 4}\n  - {template: period.yml, repeat: 10}\n",
    )
    with pytest.raises(ValueError, match="the entry periods is no item of a list"):
        split_entry(flow_entry, "periods", 3)
    with pytest.raises(ValueError, match=r"index 1 lies outside the list periods of length 1"):
        split_entry(flow_entry, "periods[1]", 3)
    with pytest.raises(ValueError, match="the entry name is no list"):
        split_entry("name: p\n", "name[0]", 3)
    for text in (
        "periods:\n  - {template: period.yml}\n",
        "periods:\n  - {template: period.yml, repeat: six}\n",
        "periods:\n  - period.yml\n",
    ):
        with pytest.raises(ValueError, match=r"the entry periods\[0\] writes no integer repeat"):
            split_entry(text, "periods[0]", 1)
    for at in (0, 6, 7, 2.5):
        with pytest.raises(ValueError, match=r"writes repeat: 6, which cannot be split at"):
            split_entry(flow_entry, "periods[0]", at)
    with pytest.raises(ValueError, match=r"at periods\[0\] cannot be extended as text"):
        split_entry("periods:\n  - - {template: p.yml, repeat: 6}\n", "periods[0][0]", 3)


def test_remove_from_sequence_takes_one_item_out_and_keeps_the_layout():
    """`remove_from_sequence` of `bellman.trellis`, the object of
    `factory/file_entries.py`, takes the item at an index of a list out
    (unit J's decisions J-D33 and J-D34): in block style the item's lines,
    with the comment ending its last line and, for an item after the first,
    the comment line just above it, which describes it; the first item's
    comment line above it stays; in flow style the item with its comma.
    The first, a middle and the last index are taken; a list's only item
    leaves `[]`; every other character is kept, line ends included. Refused:
    an address at which no list stands, an address the text does not hold,
    with a KeyError, an index that is no whole number within the list, and
    a dash that is not the first character of its line."""
    import bellman.trellis
    from bellman.factory import file_entries
    from bellman.trellis import entry_value, remove_from_sequence

    assert bellman.trellis.remove_from_sequence is file_entries.remove_from_sequence
    assert "remove_from_sequence" in bellman.trellis.__all__
    block = (
        "!period\nname: p\nstages:\n  # the list\n  - a  # the first\n  - b\n  # before c\n"
        "  - c\nconnectors:\n  - {}\n"
    )
    assert remove_from_sequence(block, "stages", 0) == block.replace("  - a  # the first\n", "")
    assert remove_from_sequence(block, "stages", 1) == block.replace("  - b\n", "")
    assert remove_from_sequence(block, "stages", 2) == block.replace("  # before c\n  - c\n", "")
    assert entry_value(remove_from_sequence(block, "stages", 1), "stages") == ["a", "c"]
    crlf = block.replace("\n", "\r\n")
    assert remove_from_sequence(crlf, "stages", 1) == crlf.replace("  - b\r\n", "")
    # a list written at its key's indentation, and an item of several lines
    flush = "stages:\n- a\n- {from: port, to: cons,\n   fields: {m_next: m}}\n- b\n"
    assert remove_from_sequence(flush, "stages", 1) == "stages:\n- a\n- b\n"
    # the last line of a text that ends with no line break
    assert remove_from_sequence("stages:\n  - a\n  - b", "stages", 1) == "stages:\n  - a\n"
    flow = "stages: [a, b, c]  # three\n"
    assert remove_from_sequence(flow, "stages", 0) == "stages: [b, c]  # three\n"
    assert remove_from_sequence(flow, "stages", 1) == "stages: [a, c]  # three\n"
    assert remove_from_sequence(flow, "stages", 2) == "stages: [a, b]  # three\n"
    # the only item, in each style, its comments kept
    assert remove_from_sequence("connectors: [{m_next: m}]\n", "connectors", 0) == (
        "connectors: []\n"
    )
    assert remove_from_sequence(
        "connectors:\n  # one\n  - {m_next: m}  # the join\nrepeat: 6\n", "connectors", 0
    ) == "connectors:\n  # one\n  []  # the join\nrepeat: 6\n"
    # the inline connector of lesson 05's trellis file, its only item
    port_cons = (ROOT / "applications/cons-port/declaration/trellis.port-cons.yml").read_text(
        encoding="utf-8"
    )
    new = remove_from_sequence(port_cons, "periods[0].connectors", 0)
    assert new == port_cons.replace("    connectors:\n      - {w: m}\n", "    connectors:\n      []\n")
    assert entry_value(new, "periods[0].connectors") == []
    with pytest.raises(ValueError, match="the entry name is no list"):
        remove_from_sequence(block, "name", 0)
    with pytest.raises(KeyError, match="no key 'registry'"):
        remove_from_sequence(block, "registry", 0)
    for index in (-1, 3, 1.0, True):
        with pytest.raises(ValueError, match="the list stages of length 3 holds no item"):
            remove_from_sequence(block, "stages", index)
    # the dashes of a list nested in a list's item follow another dash
    with pytest.raises(ValueError, match=r"at stages\[0\] does not admit the removal as text"):
        remove_from_sequence("stages:\n  - - a\n    - b\n", "stages[0]", 0)


def test_remove_from_mapping_takes_one_key_out_and_leaves_an_empty_mapping_written():
    """`remove_from_mapping` of `bellman.trellis`, the object of
    `factory/file_entries.py`, takes one key of a mapping out with its
    value (unit J's decisions J-D33 and J-D34): in block style the entry's
    lines, with the comment ending its last line and, for a key after the
    first, the comment line just above it; the first key of a mapping on a
    list's dash with everything up to the next key, which then stands on the
    dash; in flow style the entry with its comma, on one line and across
    two. The mapping's only key leaves `{}`, so that an inter-period mapping
    stays in its list and the list keeps its length; every other character
    is kept. Refused: an address at which no mapping stands, a key the
    mapping does not hold, an address the text does not hold, with a
    KeyError, and a key after the first that does not begin its line."""
    import bellman.trellis
    from bellman.factory import file_entries
    from bellman.trellis import entry_value, remove_from_mapping

    assert bellman.trellis.remove_from_mapping is file_entries.remove_from_mapping
    assert "remove_from_mapping" in bellman.trellis.__all__
    block = "fields:\n  a: k  # the first\n  # the second\n  m_next: m\n  h: h\nname: p\n"
    assert remove_from_mapping(block, "fields", "a") == block.replace("  a: k  # the first\n", "")
    assert remove_from_mapping(block, "fields", "m_next") == block.replace(
        "  # the second\n  m_next: m\n", ""
    )
    assert remove_from_mapping(block, "fields", "h") == block.replace("  h: h\n", "")
    crlf = block.replace("\n", "\r\n")
    assert remove_from_mapping(crlf, "fields", "h") == crlf.replace("  h: h\r\n", "")
    on_dash = "inter_connectors:\n  - a: k  # a\n    m_next: m\n"
    assert remove_from_mapping(on_dash, "inter_connectors[0]", "a") == (
        "inter_connectors:\n  - m_next: m\n"
    )
    assert remove_from_mapping(on_dash, "inter_connectors[0]", "m_next") == (
        "inter_connectors:\n  - a: k  # a\n"
    )
    flow = "inter_connectors:\n  - {a: k, m_next: m, h: h}  # three\n"
    assert remove_from_mapping(flow, "inter_connectors[0]", "a") == flow.replace("a: k, ", "")
    assert remove_from_mapping(flow, "inter_connectors[0]", "m_next") == flow.replace(
        "m_next: m, ", ""
    )
    assert remove_from_mapping(flow, "inter_connectors[0]", "h") == flow.replace(", h: h", "")
    across = "inter_connectors:\n  - {a: k, m_next: m,\n     h: h}\n"
    assert remove_from_mapping(across, "inter_connectors[0]", "h") == (
        "inter_connectors:\n  - {a: k, m_next: m}\n"
    )
    # the only key, in each style: the mapping stays, written `{}`
    keyed = "connectors:\n  - {from: port, to: cons, fields: {m_next: m}}\n"
    assert remove_from_mapping(keyed, "connectors[0].fields", "m_next") == (
        "connectors:\n  - {from: port, to: cons, fields: {}}\n"
    )
    assert remove_from_mapping("inter_connectors:\n  - a: k  # a\n", "inter_connectors[0]", "a") == (
        "inter_connectors:\n  - {}  # a\n"
    )
    port_cons = (ROOT / "applications/cons-port/declaration/trellis.port-cons.yml").read_text(
        encoding="utf-8"
    )
    new = remove_from_mapping(port_cons, "inter_connectors[0]", "disc.a")
    assert new == port_cons.replace("inter_connectors:\n  - {disc.a: k}\n", "inter_connectors:\n  - {}\n")
    assert entry_value(new, "inter_connectors") == [{}]
    with pytest.raises(ValueError, match="the entry name is no mapping"):
        remove_from_mapping(block, "name", "a")
    with pytest.raises(ValueError, match="the mapping fields holds no key 'z'"):
        remove_from_mapping(block, "fields", "z")
    with pytest.raises(KeyError, match="no key 'registry'"):
        remove_from_mapping(block, "registry", "a")
    # the second key written on the line of the first
    with pytest.raises(ValueError, match="at fields does not admit the removal as text"):
        remove_from_mapping("fields:\n  ? a\n  : k\n  ? b\n  : c\n", "fields", "b")


def test_the_trellis_namespace_exports_the_five_names_of_unit_j():
    """`bellman.trellis` exports the two queries of unit J, `connector_entry`
    and `period_entries`, the record `ConnectorEntry` and the two text
    writers `insert_in_sequence` and `split_entry`, each the object of
    `factory/file_entries.py` (model interface spec 0.4 §3.6, §7; the unit's
    brief, §3)."""
    import bellman.trellis
    from bellman.factory import file_entries

    for name in ("connector_entry", "ConnectorEntry", "period_entries", "insert_in_sequence", "split_entry"):
        assert getattr(bellman.trellis, name) is getattr(file_entries, name), name
        assert name in bellman.trellis.__all__, name


# --- unit J of the model interface specification 0.4: the exporter's keyword
# `unjoined` (spec 0.4 §3.4; the unit's brief, rule 4) ------------------------


def _unjoined_ports(collection, direction):
    """The ports of the graph `direction` of a view that the exporter marks
    `unjoined`, as `{(node id, port id): {key: value}}`."""
    (graph,) = [graph for graph in collection.graphs if graph.id == direction]
    return {
        (node.id, item.id): {pair.key: pair.value for pair in item.attrs}
        for node in graph.nodes
        for item in (*node.inputsMetadata, *node.outputsMetadata)
        if any(pair.key == "unjoined" for pair in item.attrs)
    }


def _wires(collection, direction):
    """Every edge of the graph `direction` of a view, as `(target node,
    source node, source port, target port)`, sorted."""
    (graph,) = [graph for graph in collection.graphs if graph.id == direction]
    return sorted(
        (node.id, edge.sourceNodeId, edge.sourceNodeOutputId, edge.targetNodeInputId)
        for node in graph.nodes
        for edge in node.incomingEdges
    )


def test_the_exporter_marks_each_unjoined_state_field_on_request(tmp_path):
    """With `unjoined=True` the forward graph of a trellis holds one port for
    each state field that no join reaches, marked `unjoined` and named by
    the field's identity (spec 0.4 §3.4; decision J-D16): an arrival field
    among the inputs of its stage occurrence's own `Inputs`, a continuation
    field among the outputs of its own `Outputs`, each node made in the
    occurrence's layer where the occurrence has none. In the complete
    trellis of `trellis.port-cons.yml` the two such fields are the two ends
    of the trellis, `disc`'s `a` in the terminal period and `port`'s `k` in
    the earliest, and the backward graph holds no such port. No edge names
    a port, and every edge, the measure wires among them, is the edge of the
    view without the keyword. With the period's connector emptied, each
    period adds `port`'s `w` and `cons`'s `m`. A stage version given
    the keyword is refused with a TypeError, as a selection is."""
    pytest.importorskip("model_explorer")
    from bellman.trellis import to_model_explorer

    _, file = declarations_copy(tmp_path)
    trellis = specify_trellis(load_trellis(file))
    marked = to_model_explorer(trellis, unjoined=True)
    assert _unjoined_ports(marked, "backward") == {}
    assert _unjoined_ports(marked, "forward") == {
        ("periods[0]/disc/GraphOutputs", "periods[0]/disc/unjoined:disc:cntn:a"): {
            "label": "a≻", "perch": "cntn", "role": "state", "field": "a", "unjoined": "true"},
        ("periods[5]/port/GraphInputs", "periods[5]/port/unjoined:port:dcsn:k"): {
            "label": "k", "perch": "dcsn", "role": "state", "field": "k", "unjoined": "true"},
    }
    (forward,) = [graph for graph in marked.graphs if graph.id == "forward"]
    assert {
        node.id: (node.label, node.namespace)
        for node in forward.nodes
        if node.id in ("periods[0]/disc/GraphOutputs", "periods[5]/port/GraphInputs")
    } == {
        "periods[0]/disc/GraphOutputs": ("Outputs", "periods[0]/disc"),
        "periods[5]/port/GraphInputs": ("Inputs", "periods[5]/port"),
    }
    for direction in ("backward", "forward"):
        assert _wires(marked, direction) == _wires(to_model_explorer(trellis), direction)

    emptied = specify_trellis(load_trellis(emptied_connector_port_cons(tmp_path / "emptied")))
    ports = _unjoined_ports(to_model_explorer(emptied, unjoined=True), "forward")
    assert sorted(ports) == sorted(
        [("periods[0]/disc/GraphOutputs", "periods[0]/disc/unjoined:disc:cntn:a"),
         ("periods[5]/port/GraphInputs", "periods[5]/port/unjoined:port:dcsn:k")]
        + [(f"periods[{h}]/port/GraphOutputs", f"periods[{h}]/port/unjoined:port:cntn:w")
           for h in range(6)]
        + [(f"periods[{h}]/cons/GraphInputs", f"periods[{h}]/cons/unjoined:cons:dcsn:m")
           for h in range(6)]
    )
    with pytest.raises(TypeError, match="marks no unjoined field"):
        to_model_explorer(trellis["periods"][0]["stages"]["disc"], unjoined=True)


def test_a_stage_with_two_continuation_states_shows_two_unjoined_ports(tmp_path):
    """Where a stage has two continuation states, one measure wire carries
    both, and each state field no join reads takes a port of its own (spec
    0.4 §3.4). In the pension model with its standing inter-period mapping
    emptied (decision J-D11), `retiree_saving` in `periods[1]`, the period
    before the terminal one in time, shows `y_f_ret` and `y_p_ret` among the
    outputs of its own `Outputs`, each with its `field`, beside the one
    measure wire of its continuation, which leaves the graph at an `end`
    node (design pass 10 §6). In the terminal period the connector joins
    both to the terminal stage, and the occurrence's own `Outputs` holds no
    unjoined port. The forward graph holds 144 unjoined ports, the two ends
    of the trellis counted."""
    pytest.importorskip("model_explorer")
    from bellman.trellis import to_model_explorer

    trellis = elaborate_trellis(load_recipe(emptied_pension(tmp_path), "spec.yml"))
    marked = to_model_explorer(trellis, unjoined=True)
    ports = _unjoined_ports(marked, "forward")
    # Each of the fourteen periods of `period.yml` leaves ten state fields
    # unjoined: `worker_saving`'s arrival fields `y_f_w` and `y_p_w`,
    # `retire_choice`'s four continuation fields, and `retiree_saving`'s two
    # arrival and two continuation fields. The terminal period leaves four:
    # the arrival fields of `worker_saving` and `retiree_saving`. The
    # earliest period's arrival fields, one end of the trellis, are among
    # the 140; the terminal stage, the other end, declares no continuation
    # state.
    assert len(ports) == 14 * 10 + 4
    assert {
        port: attributes["field"]
        for (node, port), attributes in ports.items()
        if node == "periods[1]/retiree_saving/GraphOutputs"
    } == {
        "periods[1]/retiree_saving/unjoined:retiree_saving:cntn:y_f_ret": "y_f_ret",
        "periods[1]/retiree_saving/unjoined:retiree_saving:cntn:y_p_ret": "y_p_ret",
    }
    assert not [port for (node, port) in ports if node == "periods[0]/retiree_saving/GraphOutputs"]
    (forward,) = [graph for graph in marked.graphs if graph.id == "forward"]
    ends = [
        node
        for node in forward.nodes
        if not node.namespace and {"key": "kind", "value": "end"} in map(asdict, node.attrs)
    ]
    assert [
        item.id
        for node in ends
        for item in node.inputsMetadata
        if item.id.startswith("periods[1]/retiree_saving/")
    ] == ["periods[1]/retiree_saving/retiree_saving:measure:cntn"]


def test_the_keyword_off_changes_no_view_and_no_cached_stage_view(tmp_path, cache_folder):
    """With the keyword off the view equals the view the exporter answers
    without it, and the ports the keyword adds are never written into a
    stage view kept in memory or in the cache folder, since which fields no
    join reaches is a fact of the trellis and not of the stage version that
    keys the cache (spec 0.4 §3.4): after a call with `unjoined=True`, every
    stage view kept in `_VIEW_CACHE` equals what it was before the call, and
    no node of one and no file of the cache folder holds the text
    `unjoined`. The views in memory are dropped first, so that the call
    without the keyword reads or writes the entries of the cache folder."""
    pytest.importorskip("model_explorer")
    from bellman.factory import model_explorer
    from bellman.trellis import to_model_explorer

    _, file = declarations_copy(tmp_path)
    trellis = specify_trellis(load_trellis(file))
    model_explorer._VIEW_CACHE.clear()
    plain = to_model_explorer(trellis)
    assert to_model_explorer(trellis, unjoined=False) == plain
    kept = {key: asdict(view) for key, view in model_explorer._VIEW_CACHE.items()}
    assert kept
    assert to_model_explorer(trellis, unjoined=True) != plain
    assert {key: asdict(view) for key, view in model_explorer._VIEW_CACHE.items()} == kept
    assert not [
        node.id
        for view in model_explorer._VIEW_CACHE.values()
        for node in view.nodes
        if "unjoined" in json.dumps(asdict(node), ensure_ascii=False)
    ]
    files = [path for path in Path(cache_folder).rglob("*") if path.is_file()]
    assert files
    assert not [path for path in files if "unjoined" in path.read_text(encoding="utf-8")]


def test_j_a_port_whose_join_leaves_a_restricted_view_is_not_unjoined(tmp_path):
    """Review focus 1 of unit J's plan: the unjoined ports are computed on
    the whole trellis before a view is restricted (spec 0.4 §3.4), so that a
    port whose partner the restriction hides reads `outside` and is never
    drawn unjoined. In `trellis.port-cons.yml` with the period's connector
    emptied, the view of `periods=[0, 1]` holds the unjoined ports of the
    whole trellis that lie in those two periods. `port`'s `k` in
    `periods[1]`, which the inter-period mapping joins to `disc`'s `a` in
    `periods[2]`, outside the view, reads `outside` on the port of the
    `outside` node at which its measure enters the graph (design pass 10
    §6), and is not among them."""
    pytest.importorskip("model_explorer")
    from bellman.factory.joins import unjoined_fields
    from bellman.trellis import to_model_explorer

    trellis = specify_trellis(load_trellis(emptied_connector_port_cons(tmp_path)))
    whole = unjoined_fields(trellis)
    sides = (whole["writing"], whole["reading"])
    assert sorted(field for side in sides for field in side if field[0] in (0, 1)) == [
        (0, "cons", "m"),
        (0, "disc", "a"),
        (0, "port", "w"),
        (1, "cons", "m"),
        (1, "port", "w"),
    ]
    view = to_model_explorer(trellis, periods=[0, 1], unjoined=True)
    assert sorted(port for _, port in _unjoined_ports(view, "forward")) == [
        "periods[0]/cons/unjoined:cons:dcsn:m",
        "periods[0]/disc/unjoined:disc:cntn:a",
        "periods[0]/port/unjoined:port:cntn:w",
        "periods[1]/cons/unjoined:cons:dcsn:m",
        "periods[1]/port/unjoined:port:cntn:w",
    ]
    (forward,) = [graph for graph in view.graphs if graph.id == "forward"]
    assert {
        (node.id, item.id, pair.value)
        for node in forward.nodes
        if not node.namespace
        for item in node.outputsMetadata
        for pair in item.attrs
        if pair.key == "outside"
    } == {
        (
            "outside:periods[1]/port:periods[2]/disc",
            "periods[1]/port/port:measure:dcsn",
            "periods[2]/disc",
        )
    }


def test_j_every_state_field_is_a_port_and_a_reached_arrival_counts_its_sources():
    """With `unjoined=True`, every state field of a stage occurrence at its
    arrival and its continuation perch is a port of its own `Inputs` or
    `Outputs` (unit J's decisions J-D41 to J-D43): a field no join reaches
    marked `unjoined`, as before; a field joins reach under the id
    `joined:<identity>`, an arrival field counting the joins in `sources`.
    In the durables model's forward graph of `periods[0]` and `periods[1]`,
    `bequest`'s three arrival fields each take two sources, the two
    consumption stages, and `tenure`'s three in `periods[1]` two each from
    the period before. `tenure`, a branching stage, carries the label of
    each continuation field's branch in the field's own, `keep: w_kp≻`, its
    ports grouped by branch in the order of the labels; `keeper_cons`,
    which has no branches, keeps the labels and the order by name it had.
    No edge names a field port."""
    pytest.importorskip("model_explorer")
    from bellman.trellis import to_model_explorer

    trellis = elaborate_trellis(load_recipe(DURABLES, "spec.yml"))
    view = to_model_explorer(trellis, periods=[0, 1], unjoined=True)
    (forward,) = [graph for graph in view.graphs if graph.id == "forward"]
    nodes = {node.id: node for node in forward.nodes}

    def ports(node_id, side):
        return [
            (item.id.rsplit("/", 1)[1], {pair.key: pair.value for pair in item.attrs})
            for item in getattr(nodes[node_id], side)
        ]

    assert ports("periods[0]/bequest/GraphInputs", "inputsMetadata") == [
        (f"joined:bequest:arvl:{name}",
         {"label": f"{name}≺", "perch": "arvl", "role": "state", "field": name, "sources": "2"})
        for name in ("a_bq", "h_bq", "z_bq")
    ]
    assert [
        (port, attrs["sources"]) for port, attrs in ports("periods[1]/tenure/GraphInputs",
                                                          "inputsMetadata")
    ] == [(f"joined:tenure:arvl:{name}", "2") for name in ("a", "h", "z")]
    assert [attrs["label"] for _, attrs in ports("periods[1]/tenure/GraphOutputs",
                                                 "outputsMetadata")] == [
        "keep: w_kp≻", "keep: h_kp≻", "keep: z_kp≻", "adjust: w_adj≻", "adjust: z_adj≻"]
    assert ports("periods[0]/keeper_cons/GraphOutputs", "outputsMetadata")[-3:] == [
        (f"joined:keeper_cons:cntn:{name}",
         {"label": f"{name}≻", "perch": "cntn", "role": "state", "field": name})
        for name in ("a_nxt_kp", "h_nxt_kp", "z_nxt_kp")
    ]
    assert not [
        edge
        for node in forward.nodes
        for edge in node.incomingEdges
        if "joined:" in edge.targetNodeInputId or "joined:" in edge.sourceNodeOutputId
    ]


# --- the connections of a trellis (AMD-COMP-001 §3 and §5; runs 2 to 4 of its plan) ---
# The finer claims of the selection of the connections, recast from the provisional file of
# runs 2 and 3 as tests of the public operations: `connection_report` of an elaborated
# trellis answers the selection, `period_joins` and the orders project it, and the
# transports read a certified route. `select_connections` is called directly where the
# effective bindings are given as mappings. An authored cycle remains on a
# constructed draft and refuses an order or a transport that requires it.

from conftest import BOUNDED, DISC_TEXT, MERGE, NO_LAW, PENSION, THREE_FIELDS, TWO_FIELDS, UNCHANGED, relay  # noqa: E402
from bellman.factory.connection_maps import pull_back, transport_atoms, transport_hessian, transport_point, transport_vector  # noqa: E402
from bellman.factory.connections import select_connections  # noqa: E402
from bellman.trellis import connection_report  # noqa: E402


def comp_period(stages, connectors=()):
    """One period of the stage occurrences `stages`, by key, with its authored connectors."""
    return {"stages": dict(stages), "connectors": list(connectors)}


def comp_selection(periods, inter_connectors=()):
    """The selection the report of the elaborated trellis of `periods` answers."""
    return connection_report(elaborate_trellis({"periods": list(periods), "inter_connectors": list(inter_connectors)})).selection


def comp_pairs(selection):
    """The pairs of a selection as `(writing, reading, address)`, each use printed `periods[h].key.field`."""
    return [(str(pair.writing), str(pair.reading), pair.address) for pair in selection.pairs]


def comp_candidates(selection):
    """The candidate groups as `{destination: {source: [(writing field, reading field, branch)]}}`."""
    return {group.destination: {candidate.source: [(w.field, r.field, w.branch) for w, r in candidate.pairs]
                                for candidate in group.candidates}
            for group in selection.candidates}


def comp_route(selection, source, branch, destination):
    """The one route of a selection from `source` on `branch` into `destination`."""
    (route,) = [route for route in selection.routes
                if (route.source, route.branch, route.destination) == (source, branch, destination)]
    return route


def comp_rejected(selection):
    return sorted((str(r.writing), str(r.reading), r.rule) for r in selection.rejected)


def test_comp_report_names_unproved_inference_and_open_fields_by_position():
    """A missing symbolic bound is visible as an unselected candidate; open
    state fields distinguish an internal gap from a possible exterior port."""
    bounded = stage_from_text(
        BOUNDED.replace("(a : [a_min, inf)) : !arvl", "(x : [a_min, inf)) : !arvl")
        .replace("a_d = a\n", "a_d = x\n"),
        "bounded.bl",
    )
    other = stage_from_text(
        UNCHANGED.replace("(a : ℝ₊) : !cntn", "(y : ℝ₊) : !cntn")
        .replace("    a = a_d\n", "    y = a_d\n"),
        "unchanged.bl",
    )
    trellis = elaborate_trellis({
        "periods": [comp_period({"S": bounded, "T": other}),
                    comp_period({"U": other})],
        "inter_connectors": [{}],
    })
    report = connection_report(trellis, periods=[0])
    assert report.pairs == () and report.diagnostics == ()
    assert [(r.rule, str(r.writing), str(r.reading)) for r in report.rejected] == [
        ("candidate-not-established", "periods[0].S.a", "periods[0].T.a")
    ]
    assert "a_min" in report.rejected[0].message
    assert (0, "T", "a") in report.unjoined["internal"]["reading"]
    assert (0, "S", "a") in report.unjoined["exterior"]["writing"]
    assert all(h == 0 for scope in report.unjoined.values()
               for fields in scope.values() for h, _, _ in fields)
    assert "rejected inference" in str(report)


def test_comp_diagnostics_retain_each_authored_source_entry(tmp_path):
    """An unresolved keyed endpoint names its exact mapping in a repeated
    period; a route written by two entries retains both source spellings."""
    from bellman.trellis import written_at

    (tmp_path / "two_fields.bl").write_text(TWO_FIELDS, encoding="utf-8")
    period_file = tmp_path / "period.yml"
    period_file.write_text(
        yaml.safe_dump({
            "stages": {key: {"stage": "two_fields.bl"} for key in ("S", "T")},
            "connectors": [{"from": "S", "to": "T", "fields": {"a": "b", "b": "q"}}],
        }, sort_keys=False), encoding="utf-8",
    )
    trellis_file = tmp_path / "trellis.yml"
    trellis_file.write_text(
        "periods:\n  - {template: period.yml, repeat: 2}\ninter_connectors: []\n",
        encoding="utf-8",
    )
    report = connection_report(elaborate_trellis(load_trellis(trellis_file)), periods=[1])
    unresolved = next(d for d in report.diagnostics if d.rule == "endpoint-unresolved")
    assert unresolved.source_entries == (("periods[1].connectors[0].fields", "b", "q"),)
    assert written_at(report.file, unresolved.source_entries[0][0]) == (
        str(period_file), "connectors[0].fields"
    )
    nonnegative = stage_from_text(TWO_FIELDS, "two_fields.bl")
    positive = stage_from_text(TWO_FIELDS.replace("ℝ₊", "ℝ₊₊"), "positive.bl")
    other = connection_report(elaborate_trellis({
        "periods": [comp_period(
            {"S": nonnegative, "T": positive},
            [{"S.a": "T.a"}, {"S.b": "T.b"}],
        )],
        "inter_connectors": [],
    }))
    route_diagnostic = next(d for d in other.diagnostics if d.rule == "route-incompatible")
    assert route_diagnostic.source_entries == (
        ("periods[0].connectors[0]", "S.a", "T.a"),
        ("periods[0].connectors[1]", "S.b", "T.b"),
    )
    assert route_diagnostic.address == "periods[0].connectors[0]"


@pytest.mark.parametrize("source, target, keyed, between", [
    ("S", "T", False, False),
    ("S", "T", True, False),
    ("S.inner", "T.inner", False, False),
    ("S.inner", "T.inner", False, True),
])
def test_comp_authored_pairs_retain_the_source_mapping_and_endpoint_spellings(
    tmp_path, source, target, keyed, between,
):
    """A qualified or keyed pair locates its exact YAML entry after period
    expansion; removing and restoring it preserves its resolved endpoints."""
    from bellman.trellis import append_to_mapping, entry_value, remove_from_mapping, written_at

    (tmp_path / "two_fields.bl").write_text(TWO_FIELDS, encoding="utf-8")
    source_key, source_value = ("a", "b") if keyed else (f"{source}.a", f"{target}.b")
    mapping = {source_key: source_value}
    mapping.update({"b": "a"} if keyed else {f"{source}.b": f"{target}.a"})
    connector = {"from": source, "to": target, "fields": mapping} if keyed else mapping
    period_file = tmp_path / "period.yml"
    period_text = yaml.safe_dump({
        "stages": {key: {"stage": "two_fields.bl"} for key in (source, target)},
        "connectors": [] if between else [connector],
    }, sort_keys=False)
    period_file.write_text(period_text, encoding="utf-8")
    trellis_file = tmp_path / "trellis.yml"
    trellis_text = yaml.safe_dump({
        "periods": [{"template": "period.yml", "repeat": 3}],
        "inter_connectors": [mapping] if between else [],
    }, sort_keys=False)
    trellis_file.write_text(trellis_text, encoding="utf-8")
    selected = connection_report(elaborate_trellis(load_trellis(trellis_file))).selection
    pair = next(pair for pair in selected.pairs if pair.writing.h == 2 and pair.writing.field == "a")
    suffix = ".fields" if keyed else ""
    connector_address = "inter_connectors[1]" if between else "periods[2].connectors[0]"
    assert (pair.address, pair.source_address, pair.source_key, pair.source_value) == (
        connector_address, f"{connector_address}{suffix}", source_key, source_value,
    )
    path, address = written_at(trellis_file, pair.source_address)
    source_file, source_text = (trellis_file, trellis_text) if between else (period_file, period_text)
    assert (path, address) == (
        str(source_file), "inter_connectors[0]" if between else f"connectors[0]{suffix}",
    )
    assert entry_value(source_text, address)[pair.source_key] == pair.source_value
    removed = remove_from_mapping(source_text, address, pair.source_key)
    assert pair.source_key not in entry_value(removed, address)
    restored = append_to_mapping(removed, address, pair.source_key, pair.source_value)
    reopened = connection_report(elaborate_trellis(load_trellis(
        trellis_file, {str(source_file.resolve()): restored},
    ))).selection
    assert sorted((p.writing, p.reading) for p in reopened.pairs) == sorted(
        (p.writing, p.reading) for p in selected.pairs
    )
    assert source_file.read_text(encoding="utf-8") == source_text


@pytest.fixture(scope="module")
def comp_two_fields():
    return stage_from_text(TWO_FIELDS, "two_fields.bl")


@pytest.fixture(scope="module")
def comp_three_fields():
    return stage_from_text(THREE_FIELDS, "three_fields.bl")


@pytest.fixture(scope="module")
def comp_unchanged():
    return stage_from_text(UNCHANGED, "unchanged.bl")


@pytest.fixture(scope="module")
def comp_positive():
    """The unchanged-field stage with its state in ℝ₊₊."""
    return stage_from_text(UNCHANGED.replace("ℝ₊", "ℝ₊₊"), "positive.bl")


@pytest.fixture(scope="module")
def comp_bounded():
    return stage_from_text(BOUNDED, "bounded.bl")


@pytest.fixture(scope="module")
def comp_disc():
    """The discounting stage, which arrives at `a` and continues to `k_next`."""
    return stage_from_text(DISC_TEXT, "disc.bl")


# the pension model's retirement choice with the arrival builders it had
# before they were removed, whose arrival states the worker's post-states
# join by equal names, the inference the tests of `comp_pension` read; the
# application's stage file is entered at its decision perch and joined by a
# connector (decision MB-V43)
RETIRE_CHOICE_WITH_ARRIVAL = Path(__file__).parent / "fixtures/spec_0_6/retire_choice_with_arrival.bl"


@pytest.fixture(scope="module")
def comp_pension():
    syntactic = load_recipe(PENSION, "spec.yml")
    text = RETIRE_CHOICE_WITH_ARRIVAL.read_text(encoding="utf-8")
    for period in syntactic["periods"]:
        record = period["stages"]["retire_choice"]
        record["stage"] = {"text": text, "origin": "retire_choice_with_arrival.bl"}
        record["provenance"] = {**record["provenance"], "origin": "retire_choice_with_arrival.bl",
                                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        period["connectors"] = [mapping for mapping in period["connectors"]
                                if mapping != {"y_f": "y_f_d", "y_p": "y_p_d"}] or [{}]
    return elaborate_trellis(syntactic)


@pytest.fixture(scope="module")
def comp_durables():
    return elaborate_trellis(load_recipe(DURABLES, "spec.yml"))


def test_comp_an_inferred_arrow_can_be_replaced_by_a_written_connector(
    tmp_path, comp_positive, comp_unchanged, monkeypatch
):
    """The writer releases only the named inference and reuses its eligible uses."""
    from bellman.factory import connections
    from bellman.trellis import append_to_mapping, append_to_sequence, connector_entry, entry_value

    third_text = re.sub(r"\ba\b", "b", UNCHANGED)
    third = stage_from_text(third_text, "third.bl")
    for key, text in (("S", UNCHANGED.replace("ℝ₊", "ℝ₊₊")),
                      ("T", UNCHANGED), ("U", third_text)):
        (tmp_path / f"{key}.bl").write_text(text)
    source = tmp_path / "trellis.yml"
    source.write_text(
        "periods:\n  - stages: {S: {stage: S.bl}, T: {stage: T.bl}, U: {stage: U.bl}}\n"
        "    connectors: []\ninter_connectors: []\n"
    )
    trellis = elaborate_trellis({
        "periods": [comp_period({"S": comp_positive, "T": comp_unchanged, "U": third})],
        "inter_connectors": [],
        "provenance": {"trellis": {"path": str(source)}},
    })
    selection = connection_report(trellis).selection
    (old,) = selection.pairs
    assert (old.writing.key, old.reading.key, old.origin) == ("S", "T", "inferred")
    assert connector_entry(trellis, (0, "S", "a"), (0, "U", "b")).reason == "port-joined"

    def unexpected(*args, **kwargs):
        pytest.fail("the source writer must reuse the selection's eligible uses")

    with monkeypatch.context() as held:
        held.setattr(connections, "_uses", unexpected)
        held.setattr(connections, "_Types", unexpected)
        written = connector_entry(trellis, (0, "S", "a"), (0, "U", "b"),
                                  selection=selection, replacing=(old,))
    assert written.reason is None and written.text == "{S.a: b}"
    proposed = {**trellis, "periods": [dict(trellis["periods"][0], connectors=[yaml.safe_load(written.text)])]}
    (pair,) = connection_report(proposed).pairs
    assert (pair.writing.key, pair.reading.key, pair.reading.field) == ("S", "U", "b")
    source.write_text(append_to_sequence(source.read_text(), written.address, written.text))
    reopened = elaborate_trellis(load_trellis(source))
    (reread,) = connection_report(reopened).pairs
    assert (reread.writing, reread.reading, reread.origin) == (pair.writing, pair.reading, pair.origin)
    assert source.read_text().endswith("inter_connectors: []\n")
    with pytest.raises(ValueError, match="inferred pair"):
        connector_entry(trellis, (0, "S", "a"), (0, "U", "b"),
                        selection=selection, replacing=(old._replace(origin="authored"),))

    # Another coordinate between the same stages extends their existing mapping.
    (tmp_path / "two_fields.bl").write_text(TWO_FIELDS)
    grouped_file = tmp_path / "grouped.yml"
    for connector, destination, expected in (
        ("{S.a: T.b}", "periods[0].connectors[0]", "{S.b: T.a}"),
        ("{from: S, to: T, fields: {a: b}}", "periods[0].connectors[0].fields", "{b: a}"),
    ):
        grouped_file.write_text(
            "periods:\n  - stages: {S: {stage: two_fields.bl}, T: {stage: two_fields.bl}}\n"
            f"    connectors: [{connector}]\n    repeat: 2\ninter_connectors: []\n"
        )
        grouped = elaborate_trellis(load_trellis(grouped_file))
        entry = connector_entry(grouped, (0, "S", "b"), (0, "T", "a"))
        assert (entry.address, entry.periods, entry.text, entry.reason) == (
            destination, (0, 1), expected, None
        )
        text = grouped_file.read_text()
        for field, arrival in yaml.safe_load(entry.text).items():
            text = append_to_mapping(text, entry.address, field, arrival)
        grouped_file.write_text(text)
        again = elaborate_trellis(load_trellis(grouped_file))
        assert all(len(period["connectors"]) == 1 for period in again["periods"])
        assert connection_report(again).counts["certified"] == 2

    # A failed authored target still keeps its source entry; no extension replaces it.
    for connector, destination in (
        ("{S.a: T.b, S.b: q}", "periods[0].connectors[0]"),
        ("{from: S, to: T, fields: {a: b, b: q}}", "periods[0].connectors[0].fields"),
    ):
        text = (
            "periods:\n  - stages: {S: {stage: two_fields.bl}, T: {stage: two_fields.bl}}\n"
            f"    connectors: [{connector}]\n    repeat: 2\ninter_connectors: []\n"
        )
        grouped_file.write_text(text)
        grouped = elaborate_trellis(load_trellis(grouped_file))
        before = connection_report(grouped)
        entry = connector_entry(grouped, (0, "S", "b"), (0, "T", "a"))
        assert (entry.address, entry.reason) == (destination, "source-authored")
        assert grouped_file.read_text() == text
        assert all(period["connectors"] == [yaml.safe_load(connector)]
                   for period in grouped["periods"])
        assert connection_report(grouped).diagnostics == before.diagnostics
        assert [item.rule for item in before.diagnostics].count("endpoint-unresolved") == 2

    text = (
        "periods:\n  - stages: {S: {stage: two_fields.bl}, T: {stage: two_fields.bl}}\n"
        "    connectors: []\n    repeat: 2\n"
        "inter_connectors: [{S.a: T.b, S.b: q}]\n"
    )
    grouped_file.write_text(text)
    grouped = elaborate_trellis(load_trellis(grouped_file))
    before = connection_report(grouped)
    entry = connector_entry(grouped, (1, "S", "b"), (0, "T", "a"))
    assert (entry.address, entry.reason) == ("inter_connectors[0]", "source-authored")
    assert grouped_file.read_text() == text
    assert grouped["inter_connectors"] == [{"S.a": "T.b", "S.b": "q"}]
    assert connection_report(grouped).diagnostics == before.diagnostics
    assert [item.rule for item in before.diagnostics].count("endpoint-unresolved") == 1

    # A distinct qualified key may be added while an older ambiguous key stays authored.
    for between in (False, True):
        connector = "{S.a: T.b, b: q}"
        text = (
            "periods:\n  - stages: {S: {stage: two_fields.bl}, T: {stage: two_fields.bl}}\n"
            f"    connectors: {'[]' if between else '[' + connector + ']'}\n    repeat: 2\n"
            f"inter_connectors: {'[' + connector + ']' if between else '[]'}\n"
        )
        grouped_file.write_text(text)
        grouped = elaborate_trellis(load_trellis(grouped_file))
        before = connection_report(grouped)
        entry = connector_entry(grouped, (int(between), "S", "b"), (0, "T", "a"))
        assert entry.reason is None
        added = yaml.safe_load(entry.text)
        assert added == {"S.b": "T.a"}
        after_text = append_to_mapping(text, entry.address, "S.b", "T.a")
        assert entry_value(after_text, entry.address) == {"S.a": "T.b", "b": "q", "S.b": "T.a"}
        grouped_file.write_text(after_text)
        again = connection_report(elaborate_trellis(load_trellis(grouped_file)))
        assert [d for d in again.diagnostics if d.rule.startswith("endpoint-")] == [
            d for d in before.diagnostics if d.rule.startswith("endpoint-")
        ]
        assert any((p.writing.key, p.writing.field, p.reading.key, p.reading.field)
                   == ("S", "b", "T", "a") for p in again.pairs)


def test_comp_a_bare_endpoint_resolves_to_one_use_and_an_ambiguous_or_absent_one_to_a_diagnostic(comp_disc, comp_unchanged):
    """In a period where `S` carries `a` unchanged and `T` and `U` arrive at `a`, `{a: a}` names three
    arrival uses, so it makes no pair and a diagnostic names the address and the candidates; `{a: T.a}`
    resolves, as does the keyed `{from: S, to: U, fields: {a: a}}`; a second connector claiming `S.a` is
    refused under `connector-names-no-field`, and a connector from a stage to itself under
    `period-join-cycle`; `{a: q}` names no arrival field and the diagnostic lists the period's arrival
    fields; a dotted prefix that is no key resolves to nothing. Each resolved pair records its authored
    origin and its address."""
    stages = {"S": comp_unchanged, "T": comp_disc, "U": comp_disc}
    ambiguous = comp_selection([comp_period(stages, [{"a": "a"}])])
    assert comp_pairs(ambiguous) == []
    (diagnostic,) = ambiguous.diagnostics
    assert (diagnostic.rule, diagnostic.address) == ("endpoint-ambiguous", "periods[0].connectors[0]")
    assert [str(use) for use in diagnostic.candidates] == ["periods[0].S.a", "periods[0].T.a", "periods[0].U.a"]
    assert "S.a, T.a, U.a" in diagnostic.message and "`<key>.<field>`" in diagnostic.message
    resolved = comp_selection([comp_period(stages, [{"a": "T.a"}])])
    assert comp_pairs(resolved) == [("periods[0].S.a", "periods[0].T.a", "periods[0].connectors[0]")]
    assert all(pair.origin == "authored" for pair in resolved.pairs)
    duplicate = comp_selection([comp_period(
        stages, [{"a": "T.a"}, {"from": "S", "to": "U", "fields": {"a": "a"}}],
    )])
    assert (duplicate.diagnostics[0].rule, duplicate.diagnostics[0].address) == (
        "use-claimed-twice", "periods[0].connectors[1]"
    )
    assert "both map the continuation field 'a' of S" in duplicate.diagnostics[0].message
    assert duplicate.diagnostics[0].source_entries == (
        ("periods[0].connectors[0]", "a", "T.a"),
        ("periods[0].connectors[1].fields", "a", "a"),
    )
    keyed = comp_selection([comp_period(stages, [{"from": "S", "to": "U", "fields": {"a": "a"}}])])
    assert comp_pairs(keyed) == [("periods[0].S.a", "periods[0].U.a", "periods[0].connectors[0]")]
    self_pair = comp_selection([comp_period(stages, [{"S.a": "S.a"}])])
    assert self_pair.diagnostics[0].rule == "authored-cycle"
    assert "a stage cannot take a field it produces" in self_pair.diagnostics[0].message
    absent = comp_selection([comp_period(stages, [{"a": "q"}])])
    (diagnostic,) = absent.diagnostics
    assert diagnostic.rule == "endpoint-unresolved" and "'q' names no arrival state field" in diagnostic.message
    assert diagnostic.message.endswith("the arrival state fields there are a")
    missing = comp_selection([comp_period({"foo.bar": comp_unchanged, "T": comp_disc}, [{"bar.a": "T.a"}])])
    assert [d.rule for d in missing.diagnostics] == ["endpoint-unresolved"]


def test_comp_two_unchanged_field_stages_with_no_authored_direction_are_competing_candidates_and_no_pair(comp_unchanged):
    """Two occurrences of the stage that carries `a` unchanged, with no authored connector, give one
    candidate in each direction; each is compatible and the one candidate of its arrival use, and
    together they close a cycle, so neither is selected, both are recorded as rejected for the cycle,
    and no diagnostic stands: the name alone settles no direction (amendment §3.2, §4)."""
    selection = comp_selection([comp_period({"S": comp_unchanged, "T": comp_unchanged})])
    assert comp_pairs(selection) == []
    assert comp_candidates(selection) == {(0, "S"): {(0, "T"): [("a", "a", None)]}, (0, "T"): {(0, "S"): [("a", "a", None)]}}
    assert selection.diagnostics == () and selection.counts["cycles"] == 0 and selection.routes == ()
    assert comp_rejected(selection) == [("periods[0].S.a", "periods[0].T.a", "inference-cycle"),
                                        ("periods[0].T.a", "periods[0].S.a", "inference-cycle")]


def test_comp_an_authored_endpoint_stays_reserved_when_its_other_endpoint_fails(comp_two_fields):
    """A missing or ambiguous endpoint leaves the resolved side unconnected;
    inference cannot supply a different arrow in place of the authored one."""
    for source, target in (("S.b", "T.q"), ("S.q", "T.b"), ("S.b", "b"), ("b", "T.b")):
        selected = comp_selection([comp_period(
            {"S": comp_two_fields, "T": comp_two_fields},
            [{"S.a": "T.a", source: target}],
        )])
        assert [(str(pair.writing), str(pair.reading), pair.origin) for pair in selected.pairs] == [
            ("periods[0].S.a", "periods[0].T.a", "authored")
        ]
        assert selected.diagnostics[0].rule in ("endpoint-unresolved", "endpoint-ambiguous")
        assert selected.routes[0].state == "incomplete"
        assert selected.routes[0].status == "uncertified"


def test_comp_an_authored_chain_excludes_every_reverse_inference_and_two_opposite_pairs_are_a_cycle(comp_unchanged):
    """With `S → T` and `T → U` authored on the unchanged field `a`, no candidate runs against the chain,
    not `T → S`, not `U → T` and not `U → S`, which would reverse the path; the two authored pairs stand.
    Two authored pairs in opposite directions remain as a diagnosed cycle;
    an order request refuses the cycle with each pair named."""
    stages = {"S": comp_unchanged, "T": comp_unchanged, "U": comp_unchanged}
    chain = comp_selection([comp_period(stages, [{"S.a": "T.a"}, {"T.a": "U.a"}])])
    assert comp_pairs(chain) == [("periods[0].S.a", "periods[0].T.a", "periods[0].connectors[0]"),
                                 ("periods[0].T.a", "periods[0].U.a", "periods[0].connectors[1]")]
    assert comp_candidates(chain) == {} and chain.counts["cycles"] == 0 and chain.counts["excluded"] >= 3
    cyclic = comp_selection([comp_period(
        {"S": comp_unchanged, "T": comp_unchanged},
        [{"S.a": "T.a"}, {"T.a": "S.a"}],
    )])
    assert cyclic.counts["certified"] == 0
    assert "authored-cycle" in [d.rule for d in cyclic.diagnostics]
    from bellman.factory.joins import forward_order
    with pytest.raises(FactoryError) as refused:
        forward_order(comp_period(
            {"S": comp_unchanged, "T": comp_unchanged},
            [{"S.a": "T.a"}, {"T.a": "S.a"}],
        ), "periods[0]")
    assert (refused.value.rule, refused.value.address) == ("period-join-cycle", "periods[0]")
    assert "S continues to 'a' and T arrives at 'a'; T continues to 'a' and S arrives at 'a'" in refused.value.message


def test_comp_a_destination_s_coordinates_from_one_source_stay_one_candidate_and_are_selected_together(comp_pension):
    """In the pension model `worker_saving` continues to `y_f` and `y_p` and `retire_choice` arrives at
    both: the candidate group of `retire_choice` holds one candidate from `worker_saving` with the two
    coordinates together; `retiree_saving`, whose continuation fields bear other names, offers none. The
    candidate is compatible and unique, so both coordinates are selected as one certified route."""
    selection = connection_report(comp_pension).selection
    assert comp_candidates(selection)[(1, "retire_choice")] == {(1, "worker_saving"): [("y_f", "y_f", None), ("y_p", "y_p", None)]}
    route = comp_route(selection, (1, "worker_saving"), None, (1, "retire_choice"))
    assert route.status == "certified" and [p.origin for p in route.pairs] == ["inferred"] * 2
    assert all((p.source_address, p.source_key, p.source_value) == (None, None, None) for p in route.pairs)
    assert selection.rejected == ()


def test_comp_a_stage_whose_fields_match_nothing_stays_present_and_unconnected(comp_two_fields, comp_unchanged):
    """A period that holds `W`, whose fields `a` and `b` no other stage reads or writes under those names
    after the authored pairs claim them, keeps `W` among the uses with no pair, no candidate and no
    diagnostic: an unconnected stage is not an error of the selection. The
    direct selector also shows the authored cycle in the first case."""
    stages = {"S": comp_unchanged, "T": comp_unchanged, "W": comp_two_fields}
    selection = select_connections([comp_period(stages, [{"S.a": "T.a"}, {"W.a": "S.a"}, {"T.a": "W.a"}])], [])
    assert [str(use) for use in selection.uses if use.key == "W"] == ["periods[0].W.a", "periods[0].W.b", "periods[0].W.a", "periods[0].W.b"]
    assert len(selection.pairs) == 3 and selection.counts["cycles"] == 1
    lone = comp_selection([comp_period({"W": comp_two_fields})])
    assert lone.pairs == () and lone.candidates == () and lone.diagnostics == ()
    assert [use.field for use in lone.uses] == ["a", "b", "a", "b"]


def test_comp_a_branch_join_keeps_each_route_and_the_branch_of_each_writing_use(comp_durables):
    """In the terminal period of the durables model both consumption stages continue to the bequest's
    three arrival fields through one authored connector: six pairs, two per arrival use; the tenure stage's
    continuation fields carry the label of the branch whose block writes them in the pairs of the period's
    other connector, which joins them to the decision states of the two consumption stages, each stage's
    entry perch, and leaves no pair to be inferred; the inter-period mapping resolves at every one of the
    fifty pairs, and every one of the model's 204 routes is certified (decision MB-U28)."""
    selection = connection_report(comp_durables).selection
    terminal = [(w, r) for w, r, address in comp_pairs(selection) if address == "periods[0].connectors[0]"]
    assert sorted(terminal) == sorted([
        ("periods[0].keeper_cons.a_nxt_kp", "periods[0].bequest.a_bq"),
        ("periods[0].keeper_cons.h_nxt_kp", "periods[0].bequest.h_bq"),
        ("periods[0].keeper_cons.z_nxt_kp", "periods[0].bequest.z_bq"),
        ("periods[0].adjuster_cons.a_nxt_adj", "periods[0].bequest.a_bq"),
        ("periods[0].adjuster_cons.h_nxt_adj", "periods[0].bequest.h_bq"),
        ("periods[0].adjuster_cons.z_nxt_adj", "periods[0].bequest.z_bq")])
    branches = sorted((pair.writing.field, pair.reading.field, pair.writing.branch, pair.reading.key)
                      for pair in selection.pairs if pair.address == "periods[0].connectors[1]")
    assert branches == [
        ("h_kp", "h_d", "keep", "keeper_cons"), ("w_adj", "m", "adjust", "adjuster_cons"),
        ("w_kp", "w_d", "keep", "keeper_cons"), ("z_adj", "z_d", "adjust", "adjuster_cons"),
        ("z_kp", "z_d", "keep", "keeper_cons")]
    assert comp_candidates(selection) == {}
    assert selection.diagnostics == () and selection.rejected == ()
    assert sum(1 for pair in selection.pairs if pair.address.startswith("inter_connectors")) == 300
    assert selection.counts["routes"] == selection.counts["certified"] == 204 and selection.counts["inferred"] == 0
    keep = comp_route(selection, (0, "tenure"), "keep", (0, "keeper_cons"))
    adjust = comp_route(selection, (0, "tenure"), "adjust", (0, "adjuster_cons"))
    assert keep.source_fields == ("w_kp", "h_kp", "z_kp") and keep.permutation == (0, 1, 2)
    assert keep.destination_fields == ("w_d", "h_d", "z_d")
    assert keep.law == "tenure:measure:cntn:keep" and [p.origin for p in keep.pairs] == ["authored"] * 3
    assert adjust.source_fields == ("w_adj", "z_adj") and adjust.law == "tenure:measure:cntn:adjust"
    assert [(c.required, c.supplied, c.rule) for c in keep.components] == [
        ("tenure:function:cntn:V_kp", "keeper_cons:function:dcsn:V", "one wire per role")]
    for key in ("keeper_cons", "adjuster_cons"):
        route = comp_route(selection, (0, key), None, (0, "bequest"))
        assert route.status == "certified" and route.destination_fields == ("a_bq", "h_bq", "z_bq")
        assert [p.origin for p in route.pairs] == ["authored"] * 3
    assert transport_atoms(keep, (((1, 2, 3), 0.3),)) == (((1, 2, 3), 0.3),)


def test_comp_the_selection_records_the_bindings_it_was_given_and_changes_nothing(comp_unchanged):
    """The digests of the effective calibrations given stand under `bindings`, by position, None for a
    position with no mapping; the periods and mappings given are not changed by the selection."""
    periods = [comp_period({"S": comp_unchanged, "T": comp_unchanged}, [{"S.a": "T.a"}])]
    before = deepcopy(periods)
    selection = select_connections(periods, [], {(0, "S"): {"β": 0.9}, (0, "T"): None})
    assert set(selection.bindings) == {(0, "S"), (0, "T")}
    assert selection.bindings[(0, "T")] is None and len(selection.bindings[(0, "S")]) == 64
    assert periods == before and select_connections(periods, []).bindings == {}


def test_comp_the_inferred_pairs_of_overlapping_cycles_are_withdrawn_together_whatever_the_order():
    """Three relay stages whose fields pair `A → B`, `B → C`, `C → A` and `A → C` by inference lie in one
    strongly connected component: every inferred pair is on a cycle, all four are withdrawn, and the answer
    is the same when the stages are read in another order. With `A → B` authored the three inferred pairs
    still lie on cycles and are withdrawn, and the authored pair stands, its route a projection of A's two
    continuation fields onto B's one arrival field and so not certified."""
    a = stage_from_text(relay("relay_a", ["ca"], ["ab", "ac"]), "relay_a.bl")
    b = stage_from_text(relay("relay_b", ["ab"], ["bc"]), "relay_b.bl")
    c = stage_from_text(relay("relay_c", ["ac", "bc"], ["ca"]), "relay_c.bl")
    expected = [("periods[0].A.ab", "periods[0].B.ab", "inference-cycle"),
                ("periods[0].A.ac", "periods[0].C.ac", "inference-cycle"),
                ("periods[0].B.bc", "periods[0].C.bc", "inference-cycle"),
                ("periods[0].C.ca", "periods[0].A.ca", "inference-cycle")]
    for stages in ({"A": a, "B": b, "C": c}, {"C": c, "B": b, "A": a}):
        selection = comp_selection([comp_period(stages)])
        assert selection.pairs == () and selection.routes == () and comp_rejected(selection) == expected
        assert all("among the stages A, B, C" in r.message for r in selection.rejected)
    authored = comp_selection([comp_period({"A": a, "B": b, "C": c}, [{"A.ab": "B.ab"}])])
    assert comp_pairs(authored) == [("periods[0].A.ab", "periods[0].B.ab", "periods[0].connectors[0]")]
    assert comp_rejected(authored) == expected[1:] and authored.counts["cycles"] == 0
    (route,) = authored.routes
    assert (route.state, route.status, route.permutation) == ("incomplete", "uncertified", ())
    assert any("the continuation coordinate ac of periods[0].A is mapped to no arrival coordinate" in said for said in route.obligations)


def test_comp_a_three_cycle_of_authored_pairs_tells_the_permutation_and_the_pullbacks_compose(comp_three_fields):
    """A three-cycle of authored pairs tells the forward permutation of a point from the inverse that
    carries a derivative's components, and the pullback along two routes composes in reverse order
    (amendment §5)."""
    chain = {"S": comp_three_fields, "T": comp_three_fields, "U": comp_three_fields}
    cycle = comp_selection([comp_period(chain, [{"S.a": "T.b", "S.b": "T.c", "S.c": "T.a"},
                                                {"T.a": "U.a", "T.b": "U.c", "T.c": "U.b"}])])
    first = comp_route(cycle, (0, "S"), None, (0, "T"))
    second = comp_route(cycle, (0, "T"), None, (0, "U"))
    assert first.status == second.status == "certified"
    assert first.permutation == (2, 0, 1) and first.inverse == (1, 2, 0)
    assert transport_point(first, (1, 2, 3)) == (3, 1, 2)
    assert transport_vector(first, ("ga", "gb", "gc")) == ("gb", "gc", "ga")
    hessian = ((11, 12, 13), (21, 22, 23), (31, 32, 33))
    assert transport_hessian(first, hessian) == ((22, 23, 21), (32, 33, 31), (12, 13, 11))
    pulled = pull_back(first, pull_back(second, lambda a, b, c: (a, b, c)))
    assert pulled(1, 2, 3) == transport_point(second, transport_point(first, (1, 2, 3))) == (3, 2, 1)
    for mass in (-0.5, float("nan"), float("inf"), -float("inf")):
        with pytest.raises(ValueError, match="nonnegative number"):
            transport_atoms(first, (((1, 2, 3), mass),))


def test_comp_atom_transport_preserves_exact_mass_and_refuses_overflow(comp_two_fields):
    """Finite integers and fractions keep their exact mass; combining
    floating masses must not produce an infinite atom."""
    from fractions import Fraction

    selected = comp_selection([comp_period(
        {"S": comp_two_fields, "T": comp_two_fields},
        [{"S.a": "T.b", "S.b": "T.a"}],
    )])
    route = comp_route(selected, (0, "S"), None, (0, "T"))
    large = 10**400
    fraction = Fraction(large, 3)
    assert transport_atoms(route, (((1, 2), large), ((1, 2), large))) == (
        ((2, 1), 2 * large),
    )
    assert transport_atoms(route, (((1, 2), fraction), ((1, 2), large))) == (
        ((2, 1), fraction + large),
    )
    unsigned = numpy.uint64(2**64 - 1)
    assert transport_atoms(route, (((1, 2), unsigned), ((1, 2), unsigned))) == (
        ((2, 1), 2 * int(unsigned)),
    )
    for masses in ((1e308, 1e308), (large, 0.5)):
        with pytest.raises(ValueError, match="accumulated mass.*finite"):
            transport_atoms(route, tuple(((1, 2), mass) for mass in masses))


def test_comp_an_incomplete_tuple_and_a_mixed_branch_tuple_certify_no_route_and_transport_nothing(comp_pension):
    """One coordinate of the terminal stage's two supplied from the work branch leaves the route incomplete,
    its obligation naming the missing coordinate; one coordinate from the work branch and one from the retire
    branch leave both routes incomplete, each obligation naming the mutually exclusive branches (amendment
    §3.3, §8 item 2); an uncertified route transports nothing."""
    stages = comp_pension["periods"][0]["stages"]
    partial = comp_selection([comp_period(stages, [{"y_f_wk": "y_f_T"}])])
    route = comp_route(partial, (0, "retire_choice"), "work", (0, "terminal"))
    assert (route.state, route.status, route.permutation) == ("incomplete", "uncertified", ())
    assert any("no selected pair supplies the arrival coordinate y_p_T" in said for said in route.obligations)
    assert [d.rule for d in partial.diagnostics if d.address == "periods[0].connectors[0]"] == ["route-incomplete"]
    with pytest.raises(ValueError, match="not certified"):
        transport_point(route, (1.0, 2.0))
    with pytest.raises(ValueError, match="not certified"):
        transport_atoms(route, (((1.0, 2.0), 1.0),))
    mixed = comp_selection([comp_period(stages, [{"y_f_wk": "y_f_T", "y_p_rt": "y_p_T"}])])
    work = comp_route(mixed, (0, "retire_choice"), "work", (0, "terminal"))
    retire = comp_route(mixed, (0, "retire_choice"), "retire", (0, "terminal"))
    assert work.state == retire.state == "incomplete"
    assert any("mutually exclusive branches work and retire" in said for said in work.obligations)
    assert any("mutually exclusive branches retire and work" in said for said in retire.obligations)
    assert all(pair.compatibility == "compatible" for pair in work.pairs + retire.pairs)


def test_comp_an_explicit_branch_merge_certifies_each_route_and_keeps_each_branch_s_mass():
    """Two branches of one occurrence into one destination, each branch's value paired with the
    destination's value: each route is certified with its own law, and each branch's atoms keep their
    mass."""
    merge = stage_from_text(MERGE, "merge.bl")
    both = comp_selection([comp_period({"S": merge, "T": merge},
                                       [{"S.x_up": "T.x", "S.y_up": "T.y", "S.x_dn": "T.x", "S.y_dn": "T.y"}])])
    up = comp_route(both, (0, "S"), "up", (0, "T"))
    down = comp_route(both, (0, "S"), "down", (0, "T"))
    assert up.status == down.status == "certified" and both.diagnostics == ()
    assert (up.law, down.law) == ("merge:measure:cntn:up", "merge:measure:cntn:down")
    assert [(c.required.rsplit(":", 1)[1], c.supplied.rsplit(":", 1)[1]) for c in up.components] == [
        ("V_up", "V")]
    of_up = transport_atoms(up, (((1.0, 2.0), 0.3), ((3.0, 4.0), 0.1)))
    of_down = transport_atoms(down, (((1.0, 2.0), 0.6),))
    assert of_up == (((1.0, 2.0), 0.3), ((3.0, 4.0), 0.1)) and of_down == (((1.0, 2.0), 0.6),)
    assert sum(mass for _, mass in of_up) + sum(mass for _, mass in of_down) == 1.0


def test_comp_every_branch_route_in_an_authored_cycle_loses_its_transport_certificate():
    """A cycle witness can omit a branch edge that also lies on a cycle;
    all routes within the cyclic group must refuse transport."""
    merge = stage_from_text(MERGE, "merge.bl")
    connectors = [
        {f"A.{source}": f"B.{target}" for source, target in (("x_up", "x"), ("y_up", "y"))},
        {f"B.{source}": f"C.{target}" for source, target in (("x_up", "x"), ("y_up", "y"))},
        {f"C.{source}": f"A.{target}" for source, target in (("x_up", "x"), ("y_up", "y"))},
        {f"A.{source}": f"C.{target}" for source, target in (("x_dn", "x"), ("y_dn", "y"))},
    ]
    trellis = elaborate_trellis({
        "periods": [comp_period({"A": merge, "B": merge, "C": merge}, connectors)],
        "inter_connectors": [],
    })
    report = connection_report(trellis)
    down = comp_route(report.selection, (0, "A"), "down", (0, "C"))
    assert down.state == "complete" and down.compatibility == "compatible"
    assert down.law == "merge:measure:cntn:down"
    assert down.status == "uncertified"
    assert any("authored cycle" in obligation for obligation in down.obligations)
    assert all(route.status == "uncertified" for route in report.routes)
    with pytest.raises(ValueError, match="not certified"):
        transport_point(down, (1, 2))


def test_comp_a_stage_that_writes_no_joint_law_on_its_continuation_state_certifies_no_route(comp_unchanged):
    """A stage whose forward builders graph is held as a refusal, its law of motion drawing a shock of a
    family the package does not construct, writes no forward joint law on its continuation state: its
    authored pair is compatible, the route is complete, and the certificate is withheld for the law
    (amendment §3.3). A continuation state declared on a backward header alone, the case this test read
    before AAS's ruling of 12 October 2026, is refused under `header-coordinate` and no longer exists."""
    no_law = stage_from_text(NO_LAW, "no_law.bl")
    selection = comp_selection([comp_period({"S": no_law, "T": comp_unchanged}, [{"S.a": "T.a"}])])
    (pair,) = [pair for pair in selection.pairs if pair.origin == "authored"]
    assert pair.compatibility == "compatible"
    (route,) = selection.routes
    assert (route.state, route.law, route.status) == ("complete", None, "uncertified")
    assert any("is not constructed, so no joint law on (a) is written" in said for said in route.obligations)
    assert [d.rule for d in selection.diagnostics] == ["route-no-law"]
    with pytest.raises(ValueError, match="no joint law"):
        transport_atoms(route, (((1.0,), 1.0),))


def test_comp_state_set_inclusion_selects_the_compatible_direction_and_a_named_set_resolves_within_its_stage(comp_unchanged, comp_positive):
    """Two unchanged-field stages whose states lie in ℝ₊₊ and in ℝ₊ have one compatible direction, from the
    smaller set into the larger, which is selected; the other is rejected as incompatible. A type makes no
    bare endpoint unambiguous. A set named `X` is read through its own stage's definition, so `X := ℝ₊` in
    one stage and `X := ℝ₊₊` in another are two sets, and an authored pair from the first into the second
    is incompatible with its diagnostic; two finite sets of labels are compared by their members, so a
    writing set that lies in the reading set is compatible and one that does not is incompatible."""
    selection = comp_selection([comp_period({"S": comp_positive, "T": comp_unchanged})])
    assert comp_pairs(selection) == [("periods[0].S.a", "periods[0].T.a", "periods[0]")]
    (pair,) = selection.pairs
    assert pair.origin == "inferred" and pair.compatibility == "compatible"
    assert "ℝ₊₊, lies in" in pair.reason and pair.reason.endswith("ℝ₊")
    assert comp_rejected(selection) == [("periods[0].T.a", "periods[0].S.a", "candidate-incompatible")]
    assert selection.counts["certified"] == 1 and selection.diagnostics == ()
    bare = comp_selection([comp_period({"S": comp_positive, "T": comp_unchanged, "U": comp_unchanged}, [{"a": "T.a"}])])
    assert bare.pairs == () and [d.rule for d in bare.diagnostics] == ["endpoint-ambiguous"]
    named = UNCHANGED.replace("β : (0,1)\n", "β : (0,1)\nX := ℝ₊\n").replace("a : ℝ₊", "a : X")
    nonnegative = stage_from_text(named, "nonnegative.bl")
    strictly = stage_from_text(named.replace("X := ℝ₊\n", "X := ℝ₊₊\n"), "strictly.bl")
    authored = comp_selection([comp_period({"S": nonnegative, "T": strictly}, [{"S.a": "T.a"}])])
    (pair,) = authored.pairs
    assert pair.compatibility == "incompatible" and "ℝ₊, does not lie in" in pair.reason and pair.reason.endswith("ℝ₊₊")
    assert [d.rule for d in authored.diagnostics] == ["pair-incompatible", "route-incompatible"]
    assert authored.routes[0].status == "uncertified"
    finite = stage_from_text(UNCHANGED.replace("ℝ₊", "{low, high}"), "finite.bl")
    wider = stage_from_text(UNCHANGED.replace("ℝ₊", "{low, high, mid}"), "wider.bl")
    same = comp_selection([comp_period({"S": finite, "T": finite}, [{"S.a": "T.a"}])])
    assert same.pairs[0].compatibility == "compatible"
    other = comp_selection([comp_period({"S": finite, "T": wider}, [{"S.a": "T.a"}])])
    assert other.pairs[0].compatibility == "compatible" and "{low, high}, lies in" in other.pairs[0].reason
    assert other.diagnostics == ()
    narrower = comp_selection([comp_period({"S": wider, "T": finite}, [{"S.a": "T.a"}])])
    assert narrower.pairs[0].compatibility == "incompatible" and "does not lie in" in narrower.pairs[0].reason
    assert [d.rule for d in narrower.diagnostics] == ["pair-incompatible", "route-incompatible"]


def test_comp_a_bound_named_by_a_parameter_is_one_bound_within_a_period_and_proves_nothing_across_periods(
    comp_bounded, monkeypatch
):
    """Two occurrences of the stage whose state lies in `[a_min, inf)` in one period write one bound, since
    `a_min` is one parameter of the period, and their pair is compatible without a value; in two periods the
    same spelling names two parameters, so without values the pair is not established, and with values it
    is decided at them, the result naming the bindings it read; a value missing on one side, and an infinite
    one, leave it not established; a negative bound is decided as the negation of its magnitude. The
    bindings are given as mappings, so the selector is read directly."""
    within = comp_selection([comp_period({"S": comp_bounded, "T": comp_bounded}, [{"S.a": "T.a"}])])
    (pair,) = within.pairs
    assert pair.compatibility == "compatible" and pair.basis == () and "a_min names one parameter of periods[0]" in pair.reason
    assert within.counts["certified"] == 1
    periods = [comp_period({"T": comp_bounded}), comp_period({"S": comp_bounded})]
    across = comp_selection(periods, [{"a": "a"}])
    (pair,) = across.pairs
    assert pair.compatibility == "not-established" and pair.basis == () and "names two parameters" in pair.reason
    assert "a_min of periods[0].T and a_min of periods[1].S have no finite value" in pair.reason
    assert [d.rule for d in across.diagnostics] == ["pair-not-established", "route-not-established"]
    bound = select_connections(periods, [{"a": "a"}], {(1, "S"): {"a_min": 1.0}, (0, "T"): {"a_min": 0.0}})
    (pair,) = bound.pairs
    assert pair.compatibility == "compatible" and "[1, inf) against [0, inf)" in pair.reason
    assert pair.basis == ((1, "S", bound.bindings[(1, "S")]), (0, "T", bound.bindings[(0, "T")]))
    (route,) = bound.routes
    assert route.status == "certified" and route.basis == pair.basis
    lower = select_connections(periods, [{"a": "a"}], {(1, "S"): {"a_min": 0.0}, (0, "T"): {"a_min": 1.0}})
    assert lower.pairs[0].compatibility == "incompatible" and lower.routes[0].status == "uncertified"
    half = select_connections(periods, [{"a": "a"}], {(1, "S"): {"a_min": 0.0}, (0, "T"): None})
    assert half.pairs[0].compatibility == "not-established" and "the bound a_min of periods[0].T has no finite value" in half.pairs[0].reason
    negative = select_connections(periods, [{"a": "a"}], {(1, "S"): {"a_min": -1.0}, (0, "T"): {"a_min": 0.0}})
    assert negative.pairs[0].compatibility == "incompatible" and "[-1, inf) against [0, inf)" in negative.pairs[0].reason
    below = select_connections(periods, [{"a": "a"}], {(1, "S"): {"a_min": -1.0}, (0, "T"): {"a_min": -2.5}})
    assert below.pairs[0].compatibility == "compatible" and "[-2.5, inf)" in below.pairs[0].reason
    infinite = select_connections(periods, [{"a": "a"}], {(1, "S"): {"a_min": float("-inf")}, (0, "T"): {"a_min": 0.0}})
    assert infinite.pairs[0].compatibility == "not-established" and "a_min of periods[1].S has no finite value" in infinite.pairs[0].reason

    # Each selection reads one formal field table per text in each native phase,
    # while separate period bindings still decide the pairs independently.
    from bellman.factory import connections
    # each calibration binds a stage of its own (specification 0.6 decision 1 and R4)
    zero = copy_native(comp_bounded).calibrate({"a_min": 0.0, "β": 0.9})
    one = copy_native(comp_bounded).calibrate({"a_min": 1.0, "β": 0.9})
    field_reads = []
    native_fields = connections.fields

    def counted_fields(stage):
        field_reads.append(stage.provenance["sha256"])
        return native_fields(stage)

    with monkeypatch.context() as count:
        count.setattr(connections, "fields", counted_fields)
        for number, (stages, expected) in enumerate((
            ((zero, one, zero), ["compatible", "incompatible"]),
            ((one, zero, one), ["incompatible", "compatible"]),
        ), 1):
            report = connection_report({
                "periods": [comp_period({"B": stage}) for stage in stages],
                "inter_connectors": [{"a": "a"}, {"a": "a"}],
            })
            # One read in _uses and one in the compatibility reading, per call.
            assert len(field_reads) == 2 * number and len(set(field_reads)) == 1
            assert [p.compatibility for p in report.pairs] == expected
            for pair in report.pairs:
                positions = ((pair.writing.h, "B"), (pair.reading.h, "B"))
                assert pair.basis == tuple((*position, report.bindings[position])
                                           for position in positions)
                assert pair.basis[0][2] != pair.basis[1][2]


def test_comp_an_undecided_competitor_leaves_an_arrival_use_disputed_until_a_value_decides_it(comp_unchanged, comp_positive, comp_bounded):
    """Where `T` arrives at `a` in ℝ₊ and both `S`, continuing in ℝ₊₊, and `U`, continuing in `[a_min, inf)`,
    offer it, the compatible candidate is not selected while the other is undecided: the two are disputed,
    the message naming the bound without a value. At a value that makes `U` compatible the two compete
    still; at one that makes it incompatible, `S` alone remains and is selected. The bindings are given as
    mappings, so the selector is read directly."""
    stages = {"S": comp_positive, "T": comp_unchanged, "U": comp_bounded}
    selection = comp_selection([comp_period(stages)])
    assert selection.pairs == ()
    disputed = [(str(r.writing), str(r.reading), r.rule) for r in selection.rejected if r.reading.key == "T"]
    assert sorted(disputed) == [("periods[0].S.a", "periods[0].T.a", "inference-disputed"),
                                ("periods[0].U.a", "periods[0].T.a", "inference-disputed")]
    (message,) = {r.message for r in selection.rejected if r.reading.key == "T"}
    assert "periods[0].U.a (not established: " in message and "a_min of periods[0].U" in message
    valued = select_connections([comp_period(stages)], [], {(0, "U"): {"a_min": 0.0}})
    assert valued.pairs == () and all(r.rule == "inference-disputed" for r in valued.rejected if r.reading.key == "T")
    excluded = select_connections([comp_period(stages)], [], {(0, "U"): {"a_min": -1.0}})
    assert [(str(p.writing), str(p.reading)) for p in excluded.pairs] == [("periods[0].S.a", "periods[0].T.a")]
    assert excluded.counts["certified"] == 1


def test_written_spans_resolves_repeated_origins_once_and_reads_current_text(tmp_path, monkeypatch):
    """Many expanded origins retain scalar-query locations and fresh source lines."""
    from bellman.factory import file_entries
    from bellman.trellis import entry_span, written_at, written_spans

    period = tmp_path / "period.yml"
    period.write_text("stages: [S, T]\nconnectors:\n  - {S.a: T.b, S.b: T.a}\n")
    file = tmp_path / "trellis.yml"
    file.write_text(
        "periods:\n  - {template: period.yml, repeat: 40}\n"
        "  - template: period.yml\n    connectors: [{from: S, to: T, fields: {a: b}}]\n"
        "inter_connectors: [{S.a: T.b}]\n"
    )
    addresses = tuple(f"periods[{h}].connectors[0]['S.a']" for h in range(40)) + (
        "periods[40].connectors[0].fields.a", "inter_connectors[39]['S.a']",
        "periods[39].stages[0]", "periods[99].stages", "periods[0].connectors[0].missing", None,
    )
    def scalar(address, texts=None):
        if address is None:
            return None
        try:
            path, at = written_at(file, address, texts)
            text = (texts or {}).get(str(Path(path).resolve()), Path(path).read_text())
            return path, entry_span(text, at)
        except (KeyError, ValueError):
            return None

    expected = tuple(scalar(address) for address in addresses)
    reads, compositions = [], []
    read, compose = file_entries._trellis_read, file_entries._composed
    def counted_read(*args):
        reads.append(args[0])
        return read(*args)
    def counted_compose(text):
        compositions.append(text)
        return compose(text)
    monkeypatch.setattr(file_entries, "_trellis_read", counted_read)
    monkeypatch.setattr(file_entries, "_composed", counted_compose)
    assert written_spans(file, addresses) == expected
    assert reads == [file] and len(compositions) == 2

    texts = {str(period.resolve()): "# unsaved source\n" + period.read_text()}
    reads.clear(); compositions.clear()
    refreshed = written_spans(file, addresses, texts)
    assert reads == [file] and len(compositions) == 2
    assert refreshed[0][1].line == expected[0][1].line + 1
    assert refreshed[40:42] == expected[40:42]
    assert refreshed[42][1].line == expected[42][1].line + 1
    assert refreshed[43:] == (None, None, None)
    assert written_spans(file, addresses) == expected
    assert not period.read_text().startswith("# unsaved")
    assert written_spans(file, (addresses[0], 17, "periods[bad]", addresses[40])) == (
        expected[0], None, None, expected[40],
    )

    broken = {str(period.resolve()): "stages: [\n"}
    mixed = written_spans(file, (addresses[0], "inter_connectors", None), broken)
    assert mixed == (None, (str(file), entry_span(file.read_text(), "inter_connectors")), None)
    assert written_spans(file, (addresses[0], "inter_connectors"),
                         {str(file.resolve()): "periods: [\n"}) == (None, None)


def test_an_addition_read_into_one_stage_file_under_two_spellings_of_its_path_binds_alike():
    """An addition's lines record the positions of their own file and not
    the stage file's path, so one stage file read under two spellings of its
    path, as a trellis file and a caller write it, binds the same places,
    the same rows and the same cards (decision SD-58)."""
    folder = Path(__file__).parent / "fixtures" / "spec_0_6"
    plain, roundabout = folder / "cons.bl", folder / ".." / "spec_0_6" / "cons.bl"
    bound = [
        elaborate_stage(load_stage(str(path))).methodize(str(CONS_METHODS))
        for path in (plain, roundabout)
    ]
    assert bound[0].provenance["origin"] != bound[1].provenance["origin"]
    assert str(bound[0].methods) == str(bound[1].methods)
    assert list(bound[0].bindings.blocks) == list(bound[1].bindings.blocks) == ["policy"]
    assert [row.kind for row in bound[0].bindings.blocks["policy"].rows] == [
        row.kind for row in bound[1].bindings.blocks["policy"].rows]
    assert str(bound[0].builder.policy.denote()) == str(bound[1].builder.policy.denote())


# --- specification 0.7: the components of the signatures, the places and the verbs ---


def test_methodize_reads_an_addition_as_the_whole_selection_and_refuses_another_stage_or_a_yaml_mapping(
        cons, cons_sources, tmp_path):
    """`methodize` reads a `.bl` addition, by its path or as a mapping of its
    text and origin, into the stage it is called on: the components of the
    signatures are those the stage file and the addition type, and a second
    call replaces the whole selection. An addition naming another stage is
    refused by the union under `metadata-mismatch`, and a YAML selection is
    no addition."""
    from bellman.stage.binding_verbs import methodize

    stage = copy_native(cons)
    assert methodize(stage, cons_sources["methods"]) is stage
    assert list(stage.methods) == ["arvl_to_dcsn", "dcsn_to_cntn", "cntn_to_dcsn.evaluate", "policy"]
    assert repr(stage) == "ElaboratedStage('cons', methods)"
    # the second call replaces the selection: one place typed, the rows gone
    methodize(stage, {"text": "@methods: cons\ncntn_to_dcsn.method : !vfi\n", "origin": "vfi.bl"})
    assert list(stage.methods) == ["cntn_to_dcsn"]
    assert str(stage.methods["cntn_to_dcsn"]) == "!vfi"
    assert list(stage.builder.policy.list()) == list(stage.declared.policy.list())
    with pytest.raises(ConstructionError) as refused:
        methodize(stage, {"text": "@methods: port\npolicy.method : !egm\n", "origin": "port.bl"})
    assert refused.value.rule == "metadata-mismatch"
    with pytest.raises(TypeError):
        methodize(stage, {"stage": "cons", "methods": [{"on": "policy", "method": "!egm"}]})
    missing = tmp_path / "none.bl"
    with pytest.raises(ConstructionError) as refused:
        methodize(stage, missing)
    assert refused.value.rule == "readable-form"


def test_configure_binds_every_setting_the_components_name_and_refuses_a_missing_one(cons_methodized):
    """`configure` binds a value to every name a keyword argument of a
    method word or a factor of a grid writes, lists each with the places
    that read it, and refuses a source that leaves one without a value."""
    from bellman.stage.binding_verbs import configure

    stage = copy_native(cons_methodized)
    assert tuple(symbols(stage)["settings"]) == ("n_a", "a_min", "a_max", "n_m", "m_min", "m_max")
    with pytest.raises(ValueError) as refused:
        configure(stage, {"n_a": 10, "a_min": 0.0, "a_max": 5.0, "n_m": 10, "m_min": 0.1})
    assert "setting 'm_max': the settings source supplies no value for it" in str(refused.value)
    assert stage.bindings.settings is None
    configure(stage, {"n_a": 10, "a_min": 0.0, "a_max": 5.0, "n_m": 10, "m_min": 0.1, "m_max": 9.0})
    assert str(stage.settings["n_a"]) == "n_a = 10 : ℕ, read at policy by !egm for its grid !Cartesian"
    assert [row["read at"] for row in stage.settings.list() if row["name"] == "m_min"] == [
        "cntn_to_dcsn.evaluate"]
    assert repr(stage) == "ElaboratedStage('cons', specified)"


def test_places_lists_a_place_per_stored_object_and_answers_on_the_branching_stages(
        cons, tenure, retiree_death, ret_choice, house_choice):
    """`places()` lists each builder, its named lines and their operators,
    the operators of each block and of the stage, the Evaluation of each
    builder with every object it stores and each definition; the branching
    stages answer, a branch line under its label (F12)."""
    addresses = [row["address"] for row in cons.places()]
    assert addresses == [
        "arvl_to_dcsn", "dcsn_to_cntn", "cntn_to_dcsn", "cntn_to_dcsn.value", "cntn_to_dcsn.marginal",
        "cntn_to_dcsn.evaluate", "cntn_to_dcsn.evaluate[V]", "cntn_to_dcsn.evaluate[D_{m_d}V]",
        "dcsn_to_arvl", "dcsn_to_arvl.value", "dcsn_to_arvl.evaluate", "dcsn_to_arvl.evaluate[V[<]]",
        "policy", "policy.optimality", "policy.optimality.argmax", "policy.argmax", "policy.evaluate",
        "policy.evaluate[c]", "argmax", "𝑢", "𝑑𝑢", "Γ"]
    kinds = {row["address"]: row["kind"] for row in cons.places()}
    assert (kinds["policy"], kinds["policy.optimality.argmax"], kinds["policy.evaluate[c]"], kinds["𝑢"]) == (
        "builder", "operator argmax", "operator evaluate", "definition")
    for stage in (tenure, retiree_death, ret_choice, house_choice):
        listed = [row["address"] for row in stage.places()]
        assert listed and any(address.count(".") == 2 and "evaluate" not in address for address in listed), stage.name


def test_methods_at_every_level_and_the_signature_carry_the_components(cons_methodized):
    """Every piece answers the components typed within it, read from the
    typing records of the stage; the signature of a builder or an operator
    prints its own after the field component; a place is read by its address
    or by the name of the box that realizes it."""
    stage = cons_methodized
    assert list(stage.builder.bwd.methods) == ["cntn_to_dcsn.evaluate", "policy"]
    assert list(stage.builder.fwd.methods) == ["arvl_to_dcsn", "dcsn_to_cntn"]
    assert list(stage.builder["cntn", "dcsn"].methods) == ["cntn_to_dcsn.evaluate"]
    evaluation = stage.builder["cntn", "dcsn"].primitives["cntn_to_dcsn:Evaluation"]
    assert list(evaluation.methods) == ["cntn_to_dcsn.evaluate"]
    assert str(evaluation.signature()).splitlines()[2:] == [
        "method     !Linear",
        "grid       !Cartesian(m_d=(m_min, m_max, n_m))",
        'handler    "cons-port:_make_interp"',
    ]
    assert stage.methods["cntn_to_dcsn:Evaluation"] is stage.methods["cntn_to_dcsn.evaluate"]
    assert stage.initial.methods["policy"].word == "!egm"
    # the declared level is the stage file alone, which types no component
    assert list(stage.declared.policy.methods) == []
    with pytest.raises(KeyError):
        stage.methods["dcsn_to_arvl"]
    assert "dcsn_to_arvl" not in stage.methods
    assert list(stage.builder["dcsn", "arvl"].methods) == []


def test_admitted_methods_answers_the_words_a_place_admits_by_its_kind(cons, tenure):
    """`admitted_methods` answers the words of the catalogue whose row
    admits the kind of the place, each spelled as a `.bl` entry writes it,
    none at the derivative operator, and refuses a name that is no place."""
    from bellman.stage import admitted_methods

    assert {"!Linear", "!gauss_hermite"}.isdisjoint(admitted_methods(cons, "arvl_to_dcsn"))
    assert "!egm" in admitted_methods(cons, "policy")
    assert "!vfi" in admitted_methods(cons, "cntn_to_dcsn")
    # the representation families of the registry, the closed form among
    # them (AMD-MT-003 build contract §3)
    assert admitted_methods(cons, "cntn_to_dcsn.evaluate[V]") == (
        "!Linear", "!pchip", "!closed_form")
    assert "!gauss_hermite" in admitted_methods(tenure, "E_ε")
    assert "!max" in admitted_methods(tenure, "policy")
    # a line of a branch is a place under its label, and the expectation of
    # the branching stage admits the quadratures (F12; unit U3c)
    assert "dcsn_to_cntn.keep.cash_on_hand" in [row["address"] for row in tenure.places()]
    expectations = tuple(
        tag.replace("-", "_")
        for tag in method_types
        if ("operator", "E") in method_types[tag]["admits"]
    )
    assert admitted_methods(tenure, "E_ε") == expectations
    # a line of a branch with an id, and a line that holds the derivative
    # operator twice, is one place answering both occurrences, listed once
    # (F12, F62); the derivative operator admits no method
    choice_value = "    V = (V_w[>], V_r[>])[d]                :: [id=choice_value]\n"
    stage = stage_from_text(branching((choice_value, choice_value
                                       + "    D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]  :: [id=marginal]\n")))
    assert isinstance(admitted_methods(stage, "dcsn_to_cntn.work.working"), tuple)
    assert admitted_methods(stage, "cntn_to_dcsn.marginal.D") == ()
    assert [row["address"] for row in stage.places()].count("cntn_to_dcsn.marginal.D") == 1
    with pytest.raises(TargetError):
        admitted_methods(cons, "no_such_block")


def test_the_registry_of_representation_families_registers_removes_and_refuses_a_taken_word(cons):
    """`register` adds a family whose row the method table then reads, with
    the family's typed arguments as its keywords and its places as its
    admission; `unregister` removes it and refuses a word that names no
    family; a word another family or another method names, spelled with a
    hyphen or an underscore, is refused, and so are a record that is no
    family, a family that samples its own nodes and refuses a grid, a data
    source outside the four and an argument of a kind configuration does not
    check. `families()` is a read-only view in registration order
    (AMD-MT-003 build contract §3)."""
    from bellman.native.records import MethodOption
    from bellman.stage import admitted_methods
    from bellman.stage.representations import RepresentationFamily, families, register, unregister

    record = RepresentationFamily(
        "kinked",
        {"n_knots": MethodOption("positive integer", description="The number of knots.")},
        ("table", "own nodes"), derivatives=(1,), stored="The values at the knots.")
    assert register(record) is record
    try:
        assert list(families())[-1] == "kinked"
        row = method_types["!kinked"]
        assert (row.kind, dict(row.keywords), row.admits, row.grid) == (
            "representation", {"n_knots": record.parameters["n_knots"]}, record.admits, "output")
        assert "!kinked" in admitted_methods(cons, "cntn_to_dcsn.evaluate")
        with pytest.raises(ValueError, match="already names a registered"):
            register(record)
        with pytest.raises(TypeError):
            families()["other"] = record
    finally:
        assert unregister("kinked") is record
    assert "!kinked" not in method_types and "!kinked" not in admitted_methods(
        cons, "cntn_to_dcsn.evaluate")
    with pytest.raises(KeyError, match="names no registered"):
        unregister("kinked")
    with pytest.raises(ValueError, match="names the method !golden_section"):
        register(RepresentationFamily("golden-section", {}, ("own nodes",), (), "nodes"))
    with pytest.raises(TypeError):
        register("Linear")
    with pytest.raises(ValueError, match="accepts its own nodes reads a grid"):
        RepresentationFamily("gridless", {}, ("own nodes",), (), "nodes", grid=None)
    with pytest.raises(ValueError, match="at least one data source"):
        RepresentationFamily("fitted", {}, ("weights",), (), "weights")
    with pytest.raises(ValueError, match="configure checks the kinds"):
        register(RepresentationFamily(
            "odd", {"shape": MethodOption("matrix")}, ("own nodes",), (), "nodes"))


def test_a_table_on_two_coordinates_beside_a_grid_on_them_is_compared_exactly():
    """An authored table evaluated at a tuple of names, `evaluate(K2, Y2,
    (m, z))`, beside an optional grid that discretizes those coordinates in
    that order, a `!Cartesian` grid whatever the order of its factors or a
    `!Points` grid, is admitted, and configuration compares the two finite
    supports exactly, the Cartesian support taken in the order of the
    coordinates: equal supports establish `table-grid-support` and a
    different support is refused (AMD-MT-003 build contract §§1, 3, 4)."""
    from bellman.refusals import ConstructionError
    from conftest import TWO_STATE_GRID_STAGE, stage_from_text

    stage = stage_from_text(TWO_STATE_GRID_STAGE, "grids.bl")
    table = (
        "K2 : X2 × X2 × X2 × X2\nY2 : ℝ × ℝ × ℝ × ℝ\n[id=cntn_to_dcsn] {\n"
        "    W = evaluate(K2, Y2, (m, z))    :: [id=table]\n}\n"
        "cntn_to_dcsn.table.evaluate.method : !Linear\n"
    )
    knots = [[1.0, -1.0], [1.0, 1.0], [2.0, -1.0], [2.0, 1.0]]
    nodes = {"MN": [1.0, 2.0], "ZN": [-1.0, 1.0]}
    for grid, declared, settings in (
        ("!Cartesian(z=ZN, m=MN)", "MN : ℝ × ℝ\nZN : ℝ × ℝ\n", nodes),
        ("!Points(nodes=P2)", "P2 : X2 × X2 × X2 × X2\n", {"P2": knots[::-1]}),
    ):
        bound = copy_native(stage).methodize({
            "text": f"@methods: grids\n{declared}{table}"
            f"cntn_to_dcsn.table.evaluate.grid : {grid}\n",
            "origin": "table.bl",
        })
        assert bound.methods["cntn_to_dcsn.table.evaluate"].source == "table"
        different = copy_native(bound)
        bound.configure({"settings": {"K2": knots, "Y2": [1.0, 2.0, 3.0, 4.0], **settings}})
        assert [item.status for item in bound.obligations()
                if item.condition == "table-grid-support"] == ["established"], grid
        changed = {name: [*value[:-1], [9.0, 9.0] if name == "P2" else 9.0]
                   for name, value in settings.items()}
        with pytest.raises(ConstructionError) as refused:
            different.configure({"settings": {"K2": knots, "Y2": [1.0, 2.0, 3.0, 4.0], **changed}})
        assert refused.value.rule == "representation-source"
        assert "exactly the table's finite support" in refused.value.message


def test_a_node_reads_an_authored_table_as_its_data_only_where_the_table_is_its_function():
    """A `!node` line's head `<node>` and its Evaluation `<node>.evaluate`
    read one source, selected at the place a typing entry resolves to: the
    node's Evaluation, and at `<block>.evaluate` the Evaluation that closes
    the builder, whose representation samples its own grid. Where the line
    defines its name by an authored table alone, the table is the node's
    function: the source is `table`, a `!Points` or a `!Cartesian` grid
    beside it is compared with the table's knots on the coordinates of the
    node's Evaluation at configuration, also where the representation is
    typed at the node's line and the grid at its Evaluation, the two entries
    being one assignment, and the closed form is refused as a family that
    accepts no table. The methods answer an entry by its address and by the
    box of the place it resolves to, the node's Evaluation for
    `<node>.evaluate`. Where the table is one term of the node's expression,
    the table gives no values of the node's function, which is sampled on
    its own grid, five points beside a table of three knots (AMD-MT-003
    build contract §3, case 1 and the canonical resolution)."""
    from bellman.refusals import ConstructionError
    from conftest import (
        PERFECT_FORESIGHT_CALIBRATION,
        methodized,
        perfect_foresight_text,
        stage_from_text,
    )

    growth ='Γ : ℝ₊₊          :: ["permanent income growth factor"]\n'
    value = "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
    calibration = {**PERFECT_FORESIGHT_CALIBRATION, "K": [0.0, 1.0, 2.0], "Y": [1.0, 2.0, 4.0]}
    table = "cntn_to_dcsn.table.evaluate"

    def node_stage(lines):
        return stage_from_text(perfect_foresight_text(
            (growth, growth + "K : ℝ × ℝ × ℝ\nY : ℝ × ℝ × ℝ\n"), (value, lines),
        ), "perfect_foresight.bl")

    # the line defines the block's output by the table alone
    whole = node_stage("    V = evaluate(K, Y, m)    :: [id=table, !node]\n")
    for place in ("cntn_to_dcsn.table", table):
        assert methodized(whole, f"{place}.method : !Linear\n").methods[place].source == "table"
    closing = methodized(whole, "cntn_to_dcsn.evaluate.method : !Linear\n")
    assert closing.methods["cntn_to_dcsn.evaluate"].source == "own nodes"
    for grid, nodes in (("!Points(nodes=P)", "P"), ("!Cartesian(m=KN)", "KN")):
        typed = methodized(whole, f"{nodes} : ℝ × ℝ × ℝ\n{table}.method : !Linear\n"
                                  f"{table}.grid : {grid}\n")
        assert typed.methods[table].source == "table"
        assert typed.methods["cntn_to_dcsn.table:Evaluation"] is typed.methods[table]
        assert "cntn_to_dcsn.table" not in typed.methods
        typed.calibrate({"calibration": calibration})
        different = copy_native(typed)
        typed.configure({"settings": {nodes: [0.0, 1.0, 2.0]}})
        assert [item.status for item in typed.obligations()
                if item.condition == "table-grid-support"] == ["established"], grid
        with pytest.raises(ConstructionError) as refused:
            different.configure({"settings": {nodes: [0.0, 1.0, 3.0]}})
        assert refused.value.rule == "representation-source", grid
        assert "exactly the table's finite support" in refused.value.message
    # the representation typed at the node's line and the grid at its
    # Evaluation, one assignment read at the Evaluation
    split = methodized(whole, f"P : ℝ × ℝ × ℝ\ncntn_to_dcsn.table.method : !Linear\n"
                              f"{table}.grid : !Points(nodes=P)\n")
    assert split.methods["cntn_to_dcsn.table"].source == "table"
    assert str(split.methods["cntn_to_dcsn.table:Evaluation"]) == "!Points(nodes=P)"
    split.calibrate({"calibration": calibration})
    different = copy_native(split)
    split.configure({"settings": {"P": [0.0, 1.0, 2.0]}})
    assert [item.status for item in split.obligations()
            if item.condition == "table-grid-support"] == ["established"]
    with pytest.raises(ConstructionError) as refused:
        different.configure({"settings": {"P": [0.0, 1.0, 3.0]}})
    assert (refused.value.rule, refused.value.address) == ("representation-source", table)
    assert "exactly the table's finite support" in refused.value.message
    with pytest.raises(ConstructionError) as refused:
        methodized(whole, f"{table}.method : !closed_form\n")
    assert refused.value.rule == "representation-source"
    assert "accepts no table" in refused.value.message

    # the table is one term of the node's expression
    summand = node_stage("    W = β*V[>] + evaluate(K, Y, m)    :: [id=table, !node]\n"
                         "    V = 𝑢(c) + W                      :: [id=value]\n")
    for place in ("cntn_to_dcsn.table", table):
        held = methodized(summand, f"{place}.method : !Linear\n")
        assert held.methods[place].source == "own nodes"
    typed = methodized(summand, f"KN : ℝ × ℝ × ℝ × ℝ × ℝ\n{table}.method : !Linear\n"
                                f"{table}.grid : !Cartesian(m=KN)\n")
    typed.calibrate({"calibration": calibration})
    typed.configure({"settings": {"KN": [0.0, 0.5, 1.0, 1.5, 2.0]}})
    assert "table-grid-support" not in {item.condition for item in typed.obligations()}


def test_the_support_of_a_law_is_decided_at_the_value_of_a_derived_parameter_it_reads():
    """A law whose argument is a derived parameter has its support decided at
    the derived parameter's value, which the evidence of an established
    `law-support` and the refusal of a support outside the declared set both
    name with the parameters the law reads, the names among the symbols of
    its term: w, and not the derived parameter r := R - 1, whose name is a
    letter of the law's printed text (AMD-MT-003 build contract §5)."""
    from conftest import stage_from_text

    text = (
        "@stage: t\nΓ : ℝ₊₊\nR : ℝ₊₊\nw := 2*Γ\nr := R - 1\nξ : [0, 2]\n"
        "ξ ~ TruncatedLogNormal(0, 0.1, 0.5, w)\n"
        "[id=arvl_to_dcsn, (k : ℝ, ξ) : !arvl -> (m : ℝ) : !dcsn] {\n    m = k + ξ\n}\n"
    )
    stage = stage_from_text(text)
    stage.calibrate({"calibration": {"Γ": 0.9, "R": 1.04}})
    support, = [item for item in stage.obligations() if item.condition == "law-support"]
    assert support.status == "established"
    assert support.evidence[0] == "calibration w = 1.8; the support [0.5, 1.8] lies within [0, 2]"
    with pytest.raises(ValueError) as refused:
        stage_from_text(text).calibrate({"calibration": {"Γ": 1.02, "R": 1.04}})
    assert "calibration w = 2.04 gives the distribution of ξ the support [0.5, 2.04]" in str(
        refused.value)


def test_supports_equal_compares_two_finite_supports_exactly():
    """`supports_equal` compares two sets of points with no tolerance: each
    coordinate is converted exactly, so that distinct large integers stay
    distinct and an integer equals a float only where the float is that
    integer; the two signed zeros are one point; the order and the
    repetition of points do not matter; points of different dimensions
    differ; and a coordinate that is not finite or not real is refused
    (AMD-MT-003 build contract §4)."""
    from fractions import Fraction

    from bellman.stage.representations import supports_equal

    assert supports_equal([0.0, 1.0, 2.0], [2, 1, -0.0, 1.0])
    assert supports_equal([0.1], [numpy.float64(0.1)])
    assert not supports_equal([0.1], [Fraction(1, 10)])
    assert not supports_equal([2**60 + 1], [2**60])
    assert not supports_equal([2**53 + 1], [float(2**53 + 1)])
    assert supports_equal([numpy.int64(3)], [3.0])
    assert supports_equal([(0.0, 1.0), (1.0, 2.0)], numpy.array([[1.0, 2.0], [0.0, 1.0]]))
    assert not supports_equal([(0.0, 1.0)], [0.0]) and supports_equal([], ())
    for point in (float("nan"), float("-inf"), "1.0", True, 1j):
        with pytest.raises(ValueError):
            supports_equal([point], [1.0])


@pytest.mark.parametrize("name", ("cons", "port"))
def test_the_declared_and_initial_cards_print_alike_after_every_binding(request, name):
    """The cards of every declared builder, of every block of the two
    initial diagrams and of every line of those blocks print byte for byte
    alike before any binding and after the addition, the calibration and
    the settings are bound, and before the binding the declared builders
    print as the operative ones do (decisions SC-13 and SC-22)."""
    stage = copy_native(request.getfixturevalue(name))

    def printed():
        declared = {pair: str(handle.denote()) for pair, handle in stage.declared.items()}
        blocks = {(graph, block): str(getattr(stage.initial, graph)[block].denote())
                  for graph in ("backward", "forward")
                  for block in getattr(stage.initial, graph).list().names}
        lines = {(graph, block, line): str(getattr(stage.initial, graph)[block][line].denote())
                 for graph in ("backward", "forward")
                 for block in getattr(stage.initial, graph).list().names
                 for line in getattr(stage.initial, graph)[block].list().names}
        diagrams = [str(stage.initial.backward.denote()), str(stage.initial.forward.denote())]
        return declared, blocks, lines, diagrams

    before = printed()
    assert before[0] == {pair: str(handle.denote()) for pair, handle in stage.builder.items()}
    stage.methodize(CORPUS_METHODS[name])
    assert printed() == before
    stage.calibrate(CORPUS_CALIBRATIONS[name])
    stage.configure(CORPUS_SETTINGS[name])
    assert printed() == before


def test_the_declared_level_is_the_stage_file_alone_and_answers_the_components_it_carries(
        cons, cons_sources, elaborate_text, text_of):
    """The declared level of a stage into which an addition has been read is
    the stage file elaborated alone (specification 0.7 §4 rule 6; the
    implementation specification §U2): it answers no component the addition
    types and its cards print as before the binding, while the operative
    builders answer the components and print the method clause and the
    method's condition. A typing entry the stage file itself writes is no
    binding: a stage whose own file types `!vfi` on the decision builder is
    its own declared version, holds one box at both levels and answers
    `cntn_to_dcsn   !vfi` at both (decisions SC-13 and SC-24)."""
    stage = copy_native(cons)
    before = str(stage.declared["cntn", "dcsn"].denote()), str(stage.declared.policy.denote())
    stage.methodize({"text": "@methods: cons\ncntn_to_dcsn.method : !vfi\n", "origin": "cons.methods.bl"})
    declared, operative = stage.declared["cntn", "dcsn"], stage.builder["cntn", "dcsn"]
    assert list(declared.methods) == [] and str(operative.methods) == "cntn_to_dcsn   !vfi"
    assert str(declared.denote()) == before[0]
    assert "!vfi" in str(operative.denote())
    stage = copy_native(cons)
    stage.methodize(cons_sources["methods"])
    assert list(stage.declared.methods) == []
    assert str(stage.builder.policy.methods).startswith(
        'policy   !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"')
    assert str(stage.declared.policy.denote()) == before[1]
    assert "egm-eligibility" in str(stage.builder.policy.denote())
    inline = elaborate_text(
        text_of("cons").replace("@stage: cons\n", "@stage: cons\ncntn_to_dcsn.method : !vfi\n"),
        "cons.bl")
    declared, operative = inline.declared["cntn", "dcsn"], inline.builder["cntn", "dcsn"]
    assert declared.box is operative.box
    assert str(declared.methods) == str(operative.methods) == "cntn_to_dcsn   !vfi"


def test_the_bound_builders_print_their_sections_in_order_and_the_source_of_each_file(cons_methodized, port):
    """Bound with its addition, the policy builder of `cons` prints
    `Signature`, `Declared`, `Operations`, `Conditions`, `Method`, one
    `Source` section per file, the stage file's first, and `Definitions
    referenced`, which names the addition's file and line for the function
    the addition defines; the decision builder of `port`, with `!vfi`, a
    quadrature and a representation typed within it, prints one `Method`
    section per place, the keyword arguments under `Options`; no line is
    wider than 78 columns and every operation prints its rule (the
    controller's judgment of the printed set, 22 October 2026)."""

    def headings(card):
        return [line.split("  ")[0] for line in card.splitlines()[1:]
                if line and not line[0].isspace() and line[0] not in "━─"]

    policy = str(cons_methodized.builder.policy.denote())
    assert headings(policy) == ["Signature", "Declared", "Operations", "Conditions", "Method", "Source",
                                "Source", "Definitions referenced"]
    assert [line for line in policy.splitlines() if line.startswith("Source  ")] == [
        "Source  cons.bl", "Source  methods.bl"]
    assert ["𝑑𝑢𝑖𝑛𝑣", "cons:function:𝑑𝑢𝑖𝑛𝑣", "methods.bl:19"] in [line.split() for line in policy.splitlines()]
    method = next(line for line in policy.splitlines() if line.startswith("  !egm"))
    assert method.startswith('  !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"') and method.endswith("policy")
    decision = str(copy_native(port).methodize(str(PORT_METHODS)).builder["cntn", "dcsn"].denote())
    assert headings(decision) == ["Signature", "At", "Operations", "Conditions", "Method", "Method", "Options",
                                  "Method", "Source", "Definitions referenced"]
    assert "  n_Ψ = n_Ψ_nodes\n  n_θ = n_θ_nodes\n" in decision
    for card in (policy, decision):
        assert max(len(line) for line in card.splitlines()) <= 78
        operations = card.split("\nOperations\n", 1)[1].split("\nConditions\n", 1)[0]
        numbered = [line for line in operations.splitlines() if line[:4].strip().isdigit()]
        assert len(numbered) >= 4 and operations.count("rule: ") == len(numbered)


def test_an_addition_cannot_define_a_second_policy_without_a_solution_method(path_of):
    """Policy equations added without a solution method keep the declared
    maximization, so a second definition of the policy is refused."""
    with pytest.raises(ConstructionError) as refused:
        elaborate_stage(load_stage(path_of("cons"), [{
            "text": "@methods: cons\n[id=policy] {\n"
                    "    c = 𝑑𝑢(1)    :: [id=again]\n}\n",
            "origin": "again.bl",
        }]))
    assert refused.value.rule == "defined-once"
    assert refused.value.address == "policy.again"
    assert "policy" in refused.value.message


# the consumption stage's addition of the package's corpus of specification
# 0.7, whose header types the policy builder's method, grid and handler
CONS_ADDITION = ROOT / "applications/cons-port/declaration/stages/cons/methods.bl"


def test_a_typing_entry_of_an_addition_is_located_and_written_back_as_text():
    """`typing_entries` answers every typing entry and handler binding of a
    `.bl` text by the address it types, a header entry under its block, and
    `write_typing_entry` answers the text with one entry's value replaced
    and every other character kept, or with the entry appended at file level
    where the text writes none; a value the grammar does not read is refused
    under `syntax` before anything is written, and an entry whose place the
    parser does not record, since a line of its block carries its address
    as its id, is refused with the advice to write it in the editor
    (specification 0.7 §6, the writer of the `.bl` declaration)."""
    from bellman.refusals import ConstructionError
    from bellman.stage import typing_entries, write_typing_entry

    text = CONS_ADDITION.read_text(encoding="utf-8")
    entries = typing_entries(text, str(CONS_ADDITION))
    assert list(entries) == [
        "policy.method",
        "policy.handler",
        "policy.grid",
        "cntn_to_dcsn.evaluate.method",
        "cntn_to_dcsn.evaluate.grid",
    ]
    evaluation = entries["cntn_to_dcsn.evaluate.method"]
    assert (evaluation.subject, evaluation.value, evaluation.span.line) == ("evaluate.method", "!Linear", 38)
    written = write_typing_entry(text, str(CONS_ADDITION), "cntn_to_dcsn.evaluate", "method", "!pchip")
    assert written.replace("evaluate.method : !pchip", "evaluate.method : !Linear", 1) == text
    appended = write_typing_entry(text, str(CONS_ADDITION), "arvl_to_dcsn", "method", "!deterministic")
    assert appended == text + "arvl_to_dcsn.method : !deterministic\n"
    assert typing_entries(appended)["arvl_to_dcsn.method"].value == "!deterministic"
    with pytest.raises(ConstructionError) as refused:
        write_typing_entry(text, str(CONS_ADDITION), "policy", "method", "!egm(")
    assert refused.value.rule == "syntax"
    # the line `m[>] = a + c[>] :: [id=grid]` of the block policy carries the
    # address of the header entry `grid`, so the entry's place is unrecorded
    assert entries["policy.grid"].span is None
    with pytest.raises(ValueError, match="write the entry in the editor"):
        write_typing_entry(text, str(CONS_ADDITION), "policy", "grid", "!Cartesian(a=(a_min, a_max, n_a))")


def test_boolean_settings_keep_boolean_membership_separate_from_numbers(cons):
    """Boolean literals are booleans; Python's False == 0 is not membership."""
    for domain, accepted, refused in (
        ("{true, false}", (False, True), (0, 1)),
        ("{true}", (True,), (False, 1)),
    ):
        addition = {
            "text": f"@methods: cons\nflag : {domain}\n"
                    "policy.evaluate.method : !Linear(option=flag)\n",
            "origin": "booleans.methods.bl",
        }
        for value in accepted:
            stage = copy_native(cons).methodize(addition).configure({"flag": value})
            assert stage.settings["flag"].value is value
        for value in refused:
            stage = copy_native(cons).methodize(addition)
            with pytest.raises(ConstructionError) as error:
                stage.configure({"flag": value})
            assert error.value.rule == "setting-outside-set"
            assert "flag" in error.value.message


def test_a_grid_whose_feasible_set_reads_a_derived_parameter_is_built_at_its_value(grid_stage):
    """The fibred grid of example E09 with the feasible set Γ_c(m) = [0, s*m],
    where s := q/2 is a derived parameter, is built at the value of s the
    calibration q = 4 gives, s = 2: the pairs (1, 0), (1, 2), (2, 0) and
    (2, 4), while the stored calibration keeps the declared q alone
    (AMD-MT-003 build contract §§2, 5; shared contract §8)."""
    from conftest import GRID_STAGE, GRID_VALUES

    text = GRID_STAGE.replace(
        "Γ_c(m : Xm) := [0, m]\n", "q : ℝ₊₊\ns := q/2\nΓ_c(m : Xm) := [0, s*m]\n"
    )
    stage = grid_stage(
        "cntn_to_dcsn.method : !vfi\ncntn_to_dcsn.grid : "
        "!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))\n",
        text=text,
    )
    stage.calibrate({"calibration": {"q": 4.0}})
    stage.configure({"settings": GRID_VALUES})
    grid = stage.builder["cntn", "dcsn"].kernels().grids["cntn_to_dcsn"]
    assert (grid.coordinates, grid.points) == (("m", "c"), ((1, 0), (1, 2), (2, 0), (2, 4)))
    assert dict(stage.bindings.calibration) == {"q": 4.0}


def test_kernels_holds_the_realized_grid_of_each_place_of_the_builder_that_types_one(grid_stage):
    """A builder's `kernels()` holds, under `grids`, the grid each of its
    places types, constructed at the bound settings: None before a
    configuration, then a `RealizedGrid` or the `Refusal` that says why the
    construction cannot establish the grid, each printed on a row of the
    record and read back equal by the standard pickle (AMD-MT-003 build
    contract §2)."""
    import pickle

    from bellman.native.records import Refusal

    stage = grid_stage(
        "cntn_to_dcsn.method : !vfi\n"
        "cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))\n"
        "cntn_to_dcsn.evaluate.method : !Linear\n"
        "cntn_to_dcsn.evaluate.grid : !Cartesian(c=(Γ_c, n_c))\n"
    )
    assert stage.builder["cntn", "dcsn"].kernels().grids is None
    stage.configure(GRID_VALUES)
    record = stage.builder["cntn", "dcsn"].kernels()
    joint, family = record.grids["cntn_to_dcsn"], record.grids["cntn_to_dcsn.evaluate"]
    assert str(joint) == "!Fibred on (m, c), 4 points: (1, 0), (1, 1), (2, 0), (2, 2)"
    assert isinstance(family, Refusal) and family.diagnostic["rule"] == "grid-requirement"
    assert "a family of grids of the control c, one at each state" in family.reason
    assert (family.diagnostic["file"], family.diagnostic["line"]) == ("methods.bl", 12)
    printed = str(record).splitlines()
    assert printed[-2] == f"grids        cntn_to_dcsn  {joint}"
    assert printed[-1].startswith("             cntn_to_dcsn.evaluate  not constructed: stage")
    back = pickle.loads(pickle.dumps(record.grids))
    assert back["cntn_to_dcsn"] == joint
    assert (back["cntn_to_dcsn.evaluate"].reason, back["cntn_to_dcsn.evaluate"].diagnostic) == (
        family.reason, family.diagnostic)
    assert stage.builder["dcsn", "cntn"].kernels().grids == {}


def test_same_grid_compares_two_finite_supports_exactly_in_a_common_valid_context():
    """`same_grid` compares the supports of two realized grids as exact
    rational points, whatever their order and their construction: signed
    zeros are equal, distinct large integers remain distinct, and a refused
    grid or two grids on different coordinates admit no comparison."""
    from bellman.native.records import Refusal
    from bellman.stage.grids import RealizedGrid, same_grid

    first = RealizedGrid("Points", ("m",), ((0.0,), (1,), (2**53 + 1,)))
    assert same_grid(first, RealizedGrid("Cartesian", ("m",), ((2**53 + 1,), (-0.0,), (1.0,))))
    assert not same_grid(first, RealizedGrid("Points", ("m",), ((0,), (1,), (2**53,))))
    with pytest.raises(ValueError, match="common valid context"):
        same_grid(first, RealizedGrid("Points", ("z",), ((0,),)))
    refused = Refusal(
        reason="no grid",
        diagnostic={"stage": "t", "address": "b", "rule": "grid-requirement"},
    )
    with pytest.raises(ValueError, match="valid in no context"):
        same_grid(first, refused)
    with pytest.raises(TypeError):
        same_grid(first, ((0,), (1,)))
