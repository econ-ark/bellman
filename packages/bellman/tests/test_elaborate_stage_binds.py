"""The acceptance file of the brief of 30 September 2026 in which
`elaborate_stage` binds the sources its record supplies (the second layer of
the tests, `packages/bellman/README.md` §8): one test for each of the brief's
six acceptance items, on the corpus stages `cons` and `ez_savings`, the files
of the portfolio-consumption application, the two-stage durables registry and
the trellis files of the portfolio-consumption application. The rulings the
build took are the rows EB of the unit's decisions file,
`elaborate-stage-binds-decisions.md`. The snapshot guard is unchanged, since
no symbolic stage changes.
"""

from __future__ import annotations

import json
import sys

import pytest
from conftest import CONS_METHODS, CONS_PORT, CORPUS, CORPUS_CALIBRATIONS, DURABLES, ROOT, TWO_STAGES

from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import (
    assemble_trellis,
    calibrate_trellis,
    changed_positions,
    configure_trellis,
    elaborate_trellis,
    load_trellis,
    methodize_trellis,
)
from bellman.factory.elaboration import elaborate_text
from bellman.factory.trellis import positions
from bellman.native import hypergraphs
from bellman.native.provenance import source_description
from bellman.refusals import FactoryError
from bellman.stage.levels import methods_source
from bellman.stage.sources import load_calibration, load_settings

# the files the language reads of the portfolio-consumption application
APPLICATION = ROOT / "applications/cons-port/declaration"
# the values and the settings of the consumption stage in the
# portfolio-consumption application, the files lesson 04 reads, and the
# addition of the consumption stage in the form of specification 0.7
VALUES = load_calibration(APPLICATION / "calibration/portfolio.yml")
METHODS = str(CONS_METHODS)
ADDITION = {"text": CONS_METHODS.read_text(encoding="utf-8"), "origin": METHODS}
SETTINGS = load_settings(APPLICATION / "settings/cons.yml")
LESSON = ROOT / "tutorials/getting-started/04-parameters-methods-and-settings.ipynb"


def test_item_1_a_record_holding_the_calibration_files_values_answers_the_calibrated_stage(
    text_of,
):
    """A record whose `calibration` holds the values of
    `applications/cons-port/declaration/calibration/portfolio.yml` answers the
    calibrated stage: `par.ρ` is the file's 6.0, and the provenance records
    one binding, `calibrate`, of an in-memory source whose digest is that of
    the values."""
    stage = elaborate_stage(
        {
            "stage": {"text": text_of("cons"), "origin": CORPUS["cons"]},
            "calibration": VALUES,
            "settings": {},
            "methods": {},
        }
    )
    assert repr(stage) == "ElaboratedStage('cons', calibrated)"
    assert stage.par.ρ == 6.0
    bindings, provenance = [], stage.provenance
    while "operation" in provenance:
        bindings.append((provenance["operation"], dict(provenance["source"])))
        provenance = provenance["parent"]
    assert bindings == [
        ("calibrate", {"origin": "in-memory", "sha256": source_description(VALUES)["sha256"]})
    ]


def test_item_2_a_record_with_three_sources_answers_the_stage_the_chain_of_the_verbs_makes(
    text_of,
):
    """A record with calibration, the addition and settings answers the
    stage that `elaborate_stage(record, bind=False).calibrate(c).methodize(m)
    .configure(s)` makes of the same sources: the same graphs, definitions,
    bindings and tables of parameters, settings and methods. The two
    provenances differ in the verbs they record alone: the record route
    reads the addition with the stage text (specification 0.7 §6), so its
    chain holds the calibration and the settings, and the chained route the
    three verbs."""
    from conftest import graphs_differ

    record = {
        "stage": {"text": text_of("cons"), "origin": CORPUS["cons"]},
        "calibration": VALUES,
        "settings": SETTINGS,
        "methods": [ADDITION],
    }
    bound = elaborate_stage(record)
    chained = (
        elaborate_stage(record, bind=False)
        .calibrate(VALUES)
        .methodize(METHODS)
        .configure(SETTINGS)
    )
    assert repr(bound) == repr(chained) == "ElaboratedStage('cons', specified)"
    assert graphs_differ(bound, chained) == [] and bound.definitions == chained.definitions
    assert bound.bindings == chained.bindings
    assert [str(bound.par), str(bound.settings), str(bound.methods)] == [
        str(chained.par),
        str(chained.settings),
        str(chained.methods),
    ]

    def verbs(stage):
        held, provenance = [], stage.provenance
        while "operation" in provenance:
            held.append(provenance["operation"])
            provenance = provenance["parent"]
        return held

    assert (verbs(bound), verbs(chained)) == (["configure", "calibrate"], ["configure", "methodize", "calibrate"])
    assert bound.provenance["additions"] == chained.provenance["additions"]


def test_item_3_bind_false_the_record_of_load_stage_and_elaborate_text_answer_the_symbolic_stage(
    cons, text_of, path_of
):
    """`bind=False` on a record holding values and the addition, the record
    `load_stage` returns for the stage file alone and `elaborate_text` each
    answer the symbolic stage: every parameter unbound, no binding made, no
    addition read, and the provenance of elaboration alone, the description
    of each of the record's three sources under `sources`, the methods by
    the addition's path, and no verb. A record's methods are the additions
    `load_stage` read, their texts and origins; a path in their place is
    refused under `record-shape`, since a verb of the factory reads no file.
    `elaborate_text` answers the corpus stage the fixtures build."""
    record = {
        "stage": {"text": text_of("cons"), "origin": CORPUS["cons"]},
        "calibration": VALUES,
        "settings": SETTINGS,
        "methods": [ADDITION],
    }
    for stage, written in (
        (elaborate_stage(record, bind=False), record),
        (elaborate_stage(load_stage(path_of("cons"))), load_stage(path_of("cons"))),
        (elaborate_text(text_of("cons"), CORPUS["cons"]), None),
    ):
        assert repr(stage) == "ElaboratedStage('cons', symbolic)"
        assert str(stage.par["ρ"]) == "ρ : [1, inf), unbound"
        assert (stage.bindings.calibration, stage.bindings.blocks, stage.bindings.settings) == (
            None,
            None,
            None,
        )
        assert "additions" not in stage.provenance
        assert sorted(stage.provenance) == ["origin", "sha256", "sources", "text", "versions"]
        if written is not None:
            location = {"path": METHODS} if written["methods"] else {"origin": "in-memory"}
            assert {kind: dict(held) for kind, held in stage.provenance["sources"].items()} == {
                kind: {**(location if kind == "methods" else {"origin": "in-memory"}),
                       "sha256": source_description(
                           methods_source(written[kind]) if kind == "methods" else written[kind]
                       )["sha256"]}
                for kind in ("methods", "settings", "calibration")
            }
    assert elaborate_text(text_of("cons"), CORPUS["cons"]) == cons
    with pytest.raises(FactoryError) as refused:
        elaborate_stage({**record, "methods": METHODS})
    assert refused.value.rule == "record-shape" and "reads no file" in refused.value.message


def test_item_4_one_copy_for_the_call_and_one_for_each_occurrence_of_a_trellis(
    text_of, monkeypatch
):
    """`copy_native` runs once for a call of `elaborate_stage` that binds all
    three sources, counted by replacing it in every module of the package
    that holds it. `elaborate_trellis` runs it once for each occurrence of
    the trellis `trellis.reference-port-cons.yml` given the records of
    `trellis.reference-port-cons-vfi.yml`, where the six occurrences of the
    consumption stage are constructed anew with the replacing selection and
    the others taken from the trellis given; and `assemble_trellis` runs it
    once for each stage occurrence of the two-stage durables registry, the
    registry the API index assembles, since no recipe assembles the
    portfolio-consumption trellis (EB8)."""
    copies = []
    original = hypergraphs.copy_native

    def counted(value):
        copies.append(type(value).__name__)
        return original(value)

    for name, module in list(sys.modules.items()):
        if name.startswith("bellman") and getattr(module, "copy_native", None) is original:
            monkeypatch.setattr(module, "copy_native", counted)
    elaborate_stage(
        {
            "stage": {"text": text_of("cons"), "origin": CORPUS["cons"]},
            "calibration": VALUES,
            "settings": SETTINGS,
            "methods": [ADDITION],
        }
    )
    assert copies == ["ElaboratedStage"]
    syntactic = load_trellis(CONS_PORT / "trellis.reference-port-cons.yml")
    specified = configure_trellis(
        methodize_trellis(
            calibrate_trellis(elaborate_trellis(syntactic), syntactic), syntactic
        ),
        syntactic,
    )
    changed = load_trellis(CONS_PORT / "trellis.reference-port-cons-vfi.yml")
    copies.clear()
    remade = elaborate_trellis(changed, specified)
    assert len(copies) == len(positions(remade)) == 18
    assert [key for _, key in changed_positions(specified, remade)] == ["cons"] * 6
    copies.clear()
    assembled = assemble_trellis(DURABLES, TWO_STAGES)
    assert len(copies) == len(positions(assembled)) == 103


def test_item_5_the_verbs_refusals_stand_and_bind_is_true_or_false(text_of):
    """A calibration missing `β`, a value outside its declared set and an
    unknown method are each refused with the sentence the verb gives on the
    symbolic stage; `bind` given anything but `True` or `False` is refused
    before the record is read."""
    without_beta = {
        name: value for name, value in CORPUS_CALIBRATIONS["ez_savings"].items() if name != "β"
    }
    unknown = {"text": "@methods: cons\npolicy.method : !no_such_method\n", "origin": "cons.methods.bl"}
    cases = (
        ("ez_savings", "calibration", without_beta, "calibrate", "supplies no value for it"),
        ("cons", "calibration", {"ρ": 0.5}, "calibrate", "lies outside the declared set"),
        ("cons", "methods", unknown, "methodize",
         "names the method `!no_such_method`, which no row of the catalogue holds"),
    )
    for name, kind, source, verb, words in cases:
        record = {
            "stage": {"text": text_of(name), "origin": CORPUS[name]},
            "calibration": {},
            "settings": {},
            "methods": [],
            kind: [source] if kind == "methods" else source,
        }
        # the refusal of a calibration or of settings is a ValueError, and
        # that of a method at its target a TargetError, a LookupError
        with pytest.raises((ValueError, LookupError)) as bound:
            elaborate_stage(record)
        with pytest.raises((ValueError, LookupError)) as chained:
            getattr(elaborate_stage(record, bind=False), verb)(source)
        assert (type(bound.value), str(bound.value)) == (type(chained.value), str(chained.value))
        assert words in str(bound.value), (verb, str(bound.value))
    for written in ("yes", 1, None):
        with pytest.raises(TypeError) as refused:
            elaborate_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl",
                            bind=written)
        assert str(refused.value) == (
            f"elaborate_stage: bind is {written!r}, which is not True or False; bind says "
            "whether the sources the record supplies are bound; write bind=False for the "
            "symbolic stage, or leave bind out to bind them"
        )


def test_item_6_lesson_04_shows_the_calibrated_stage_one_call_makes():
    """Lesson 04 holds, after the passage that constructs `cons_described`,
    a sentence and a code cell that hands `elaborate_stage` the same text
    with `portfolio.yml` read into `calibration`, and the cell's recorded
    output is the table of parameters with ρ at 6.0 beside its description.
    That the lesson stands as its record describes it is the test of
    `tutorials/tests/test_lessons.py`, and the runs of the fast core, the
    sweeps, the root suite and the strict build of the site are reported in
    the build record."""
    cells = json.loads(LESSON.read_text(encoding="utf-8"))["cells"]
    ids = [cell.get("id") for cell in cells]
    constructed = ids.index("l4-c-describes-stage")
    # the first such cell: the lesson's cell 55 elaborates and calibrates a stage of its own for the second
    # methods file, since a binding binds the stage it is called on (SB-10, SD-54)
    index = next(
        index
        for index, cell in enumerate(cells)
        if cell["cell_type"] == "code"
        and "elaborate_stage" in "".join(cell["source"])
        and "calibration/portfolio.yml" in "".join(cell["source"])
    )
    assert index > constructed and cells[index - 1]["cell_type"] == "markdown"
    assert "symbolic" in "".join(cells[index - 1]["source"])
    (output,) = cells[index]["outputs"]
    # the lesson reads the demonstration's consumption stage, which declares ρ in (1, inf), since AAS's
    # instruction of 21 October 2026 that cons-port use the endogenous grid method purely as a method (SD-36)
    assert "".join(output["data"]["text/plain"]) == (
        "name  set       value  describes\nρ     (1, inf)  6.0    relative risk aversion"
    )
