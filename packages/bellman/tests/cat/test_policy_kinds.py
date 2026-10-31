"""The acceptance file of lane K of the internal developer release 0.01, the
kinds of the policy block's rows and the places of its methods (the second
layer of the tests, `packages/bellman/README.md` §8): one test for each of the
six items the release's implementation plan states for lane K (its §3).

The rows of a builder take the kinds `Pullback`, `Aggregation`,
`Expectation`, `Evaluation` and `Argmax`: an operative `argmax` line forms an
`Argmax` row, a relational line or a `solve` line an `Aggregation` carrying
its relation, and the identification line of the endogenous grid the
`Pullback` of the policy along the coordinate map; the kinds `Selection`,
`Inversion` and `Solution` are retired with their definitions. `cons_argmax`
is spelling A restated, a twin text of `conftest.py`: its argmax line is
operative and the first-order condition is attached to it as its property,
`optimality.euler`. Item 6 is closed by the recorded guard and by AAS's
reading of the policy cards in the notebook the lane's build record names;
its test holds the recorded guard to the kinds. The last assertion of
item 2, like item 6, reads the recordings, and passes after the snapshot
and the stored encodings are re-recorded.

Item 1 sweeps the stage files of the core applications and carries the mark
`sweep`, which a run given no marker expression, or `-m 'not sweep'`, leaves
out. It runs by `pytest packages/bellman/tests/cat/test_policy_kinds.py -m
sweep -n 4` after the snapshot and the stored encodings are re-recorded, and
it is part of the lane's acceptance run; the other five items run in the fast
core.
"""
import json
import re
from pathlib import Path

import numpy
import pytest

from bellman.native.hypergraphs import copy_native

from bellman.refusal_catalogue import refusal_of
from bellman.refusal_examples import EXAMPLES
from bellman.refusals import ConstructionError, NotConstructed, TargetError
from conftest import CORPUS_CALIBRATIONS, DURABLES, ROOT, SA_SAVINGS_CALIBRATIONS, flat, section
from snapshot.record import CORPUS_RECORDINGS, recording_path

APPLICATIONS = ROOT / "applications"
# the stage files of the core applications, each in its stage folder,
# `declaration/stages/<key>/<key>.bl`
CORE = sorted(APPLICATIONS.glob("*/declaration/stages/*/*.bl"))
# the stored recordings of the core applications' stage files, the parsed
# terms and the encodings
STORED = sorted(CORPUS_RECORDINGS.glob("*/*.json"))
# the recording of the snapshot guard
SNAPSHOT = Path(__file__).resolve().parents[1] / "snapshot"
# a retired kind named as a word: the key of a row, the identity of a box, a
# label, or a kind in an encoding
RETIRED = re.compile(r"\b(?:Selection|Inversion|Solution)")
# the header of a block, whose id names the builder its lines fold to
BLOCK = re.compile(r"^\[id=(?P<block>[^,\]\s]+)")
# a line whose right side is an argmax, and the tags of its annotation
ARGMAX_WRITTEN = re.compile(r"=\s*argmax_\{.*::\s*\[(?P<tags>[^\]]*)\]")
# the five operative argmax lines the lane's brief names, by stage file and
# line; the fifth file, housing_choice.bl, is refused at elaboration under
# `family-selection` and forms no row
NAMED = {
    "applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl": 37,
    "applications/epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl": 31,
    "applications/durables/declaration/stages/tenure/tenure.bl": 47,
    "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl": 25,
    "applications/housing-owner/declaration/stages/housing_choice/housing_choice.bl": 41,
}
# the declared maximization of `cons.bl`, which prints with its operator head
# and its binder, the kind `Argmax` being keyed apart from the head `argmax`
DECLARED = {
    "applications/portfolio-choice/declaration/stages/cons/cons.bl": "𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]",
}


def argmax_lines(path):
    """`(line number, block id, line id, declared)` of every argmax line of a
    stage file: an argmax on the right of its equation, the line's id from its
    annotation, and whether the annotation marks the line `!doc`."""
    block, found = None, []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        opened = BLOCK.match(line)
        block = opened["block"] if opened else block
        written = ARGMAX_WRITTEN.search(line)
        if written:
            identity = re.search(r"\bid=([^,\]\s]+)", written["tags"])[1]
            found.append((number, block, identity, "!doc" in written["tags"]))
    return found


def outputs(stage):
    """`(what, text)` of everything a stage prints or encodes: the stage's
    card; the listing and the drawing of each builders graph at the builder,
    sub-builder and primitive grains, and the card of each builder and of each
    of its primitives; the drawings of the two initial diagrams; the card of
    each definition; and the encoding. A graph the construction refused is
    left out, since the snapshot and the corpus test hold its refusal."""
    yield "the stage's card", str(stage.denote())
    for direction, graph in (("backward", stage.builder.bwd), ("forward", stage.builder.fwd)):
        try:
            names = graph.list()
        except NotConstructed:
            continue
        for grain in (graph, graph.primitives, graph.sub_builders):
            drawing = grain.diagram()
            yield f"a {direction} listing", str(grain.list())
            yield f"a {direction} drawing", "\n".join(drawing.labels) + "\n" + drawing.source
        for name in names:
            builder = graph[name]
            yield f"the card of {name}", str(builder)
            for key in builder.primitives.list():
                yield f"the card of {name} / {key}", str(builder.primitives[key])
    for direction in ("backward", "forward"):
        try:
            drawing = getattr(stage.initial, direction).diagram()
        except NotConstructed:
            continue
        yield f"the {direction} initial diagram", "\n".join(drawing.labels) + "\n" + drawing.source
    listing = stage.definitions.list()
    for kind in listing:
        for identity in listing[kind]:
            yield f"the card of {identity}", str(stage.definitions.denote(identity))
    yield "the encoding", json.dumps(stage.encoding(), ensure_ascii=False)


def holds_the_optimality_obligation(value):
    """Whether a recorded JSON value holds an obligation of the condition
    `optimality`: an encoded condition whose field `condition` is that word,
    or a condition as the snapshot records it, the word, then the list of its
    entries, then its status."""
    if isinstance(value, dict):
        return value.get("condition") == "optimality" or any(map(holds_the_optimality_obligation, value.values()))
    if isinstance(value, list):
        return ((len(value) >= 3 and value[0] == "optimality" and isinstance(value[1], list))
                or any(map(holds_the_optimality_obligation, value)))
    return False


@pytest.mark.sweep
@pytest.mark.parametrize("src", CORE, ids=lambda path: path.relative_to(APPLICATIONS).as_posix())
def test_item_1_no_output_of_a_core_application_names_a_retired_kind_and_each_operative_argmax_line_forms_an_argmax_row(
        src, elaborate_text):
    relative = src.relative_to(ROOT).as_posix()
    lines = argmax_lines(src)
    if relative in NAMED:
        assert NAMED[relative] in [number for number, _, _, declared in lines if not declared]
    # the pattern of every recording of the stage file: its parsed term and
    # its encodings
    pattern = recording_path(src, ".*json")
    for stored in sorted(pattern.parent.glob(pattern.name)):
        assert not RETIRED.search(stored.read_text(encoding="utf-8")), stored.name
    try:
        stage = elaborate_text(src.read_text(encoding="utf-8"), relative)
    except ConstructionError as refused:
        pytest.skip(f"the construction refuses the file under {refused.rule}, which the corpus test holds")
    printed = list(outputs(stage))
    assert [(what, match.group()) for what, text in printed for match in RETIRED.finditer(text)] == []
    assert [what for what, text in printed if "Argmax_{" in text] == []
    keys = [str(key) for key in stage.builder.bwd.primitives.list()] if lines else []
    assert sorted(key for key in keys if key.endswith("Argmax")) == sorted(
        f"{block}.{line}:Argmax" for _, block, line, declared in lines if not declared)
    for _, block, _, _ in lines:
        assert "argmax_{" in flat(str(stage.builder.bwd[block])), block
    if relative in DECLARED:
        assert flat(DECLARED[relative]) in flat(str(stage.builder.policy))


def test_item_2_cons_argmax_prints_its_property_under_the_argmax_row_as_no_row_no_address_and_no_method_place(
        cons_argmax, cons, cons_kt, cons_obs, port):
    policy = cons_argmax.builder.policy
    assert [str(key) for key in policy.primitives.list()] == [
        "Pullback", "optimality:Aggregation", "optimality:Argmax", "Evaluation"]
    # the property prints under the Argmax row, labeled by its id and read at
    # the point, before the Evaluation; the file's line stands in the source
    # below it
    card = str(policy)
    lines = card.splitlines()
    row = next(i for i, line in enumerate(lines) if "optimality:Argmax" in line)
    label = next(i for i, line in enumerate(lines) if "optimality.euler" in line)
    closing = next(i for i, line in enumerate(lines) if i > row and "Evaluation" in line)
    assert row <= label < closing
    assert flat("𝑑𝑢(𝑐(m_d)) = 𝑑𝑉≻(𝑔≻(m_d, 𝑐(m_d)))") in flat(card)
    assert flat("⟂ 𝑔≻(m_d, 𝑐(m_d)) ≥ 0") in flat(card)
    # no box at any grain of the builders graph or of the initial diagram, and
    # no method place, carries the property's id
    backward = cons_argmax.builder.bwd
    addresses = [str(key) for grain in (backward.primitives, backward.sub_builders, policy.primitives, policy.sub_builders,
                                        cons_argmax.initial.backward.primitives) for key in grain.list()]
    places = [row["address"] for row in cons_argmax.places()]
    assert [address for address in addresses + places if "euler" in address] == []
    with pytest.raises(TargetError):
        copy_native(cons_argmax).methodize({"stage": "cons_argmax", "methods": [
            {"on": "policy.optimality.euler", "method": "!root-find"}]})
    # the obligation `optimality` stands on no stage and in no recording
    for stage in (cons_argmax, cons, cons_kt, cons_obs, port):
        assert "optimality" not in {item.condition for item in stage.obligations()}, stage.name
    recordings = sorted(SNAPSHOT.glob("*.json")) + STORED
    assert [path.name for path in recordings
            if holds_the_optimality_obligation(json.loads(path.read_text(encoding="utf-8")))] == []


# the rows of five policy builders that have an explicit constituent
# function: a pullback's law of motion, a value aggregation, or a side of a
# relation that is the output's name alone against a closed expression; every
# other row of these builders has none
EXPLICIT = {
    "cons": ("InvEuler:Aggregation", "endoggrid:Aggregation"),
    "cons_argmax": ("Pullback", "optimality:Aggregation"),
    "adjuster_cons": ("InvEuler:Aggregation", "endoggrid:Aggregation", "Pullback"),
    "port": ("Pullback", "foc:Aggregation:1"),
    "sa_savings": ("Pullback", "objective:Aggregation:2", "objective:Aggregation:1", "objective:Aggregation"),
}
# among the others, one row of each kind that has none: the identification,
# a joint solve's residual system, a choice, an expectation and an evaluation
WITHOUT = {
    "cons": ("cons_choice:Pullback", "Evaluation"),
    "adjuster_cons": ("choice:Aggregation",),
    "cons_argmax": ("optimality:Argmax",),
    "sa_savings": ("objective:Expectation:1",),
}


def test_item_3_compile_kernel_answers_the_explicit_side_of_the_inverse_euler_row_and_refuses_each_row_without_one(
        cons_calibrated, cons_argmax, adjuster_cons, port, sa_savings):
    versions = {
        "cons": cons_calibrated,
        "cons_argmax": copy_native(cons_argmax).calibrate(CORPUS_CALIBRATIONS["cons"]),
        "adjuster_cons": copy_native(adjuster_cons).calibrate(str(DURABLES / "calibration/durables.yml")),
        "port": copy_native(port).calibrate(CORPUS_CALIBRATIONS["port"]),
        "sa_savings": copy_native(sa_savings).calibrate(SA_SAVINGS_CALIBRATIONS[0]),
    }
    for name, version in versions.items():
        policy = version.builder.policy
        keys = [str(key) for key in policy.primitives.list()]
        assert set(EXPLICIT[name]) | set(WITHOUT.get(name, ())) <= set(keys), name
        for key in keys:
            if key in EXPLICIT[name]:
                assert callable(policy[key].compile_kernel()), (name, key)
                continue
            with pytest.raises(ConstructionError) as refused:
                policy[key].compile_kernel()
            assert refused.value.rule == "kernel-target", (name, key)
    # at a positive saving the row answers its explicit side,
    # 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) = 𝑑𝑉≻(a)^(−1/ρ), with its arguments the marginal value and
    # the saving, as the cons-port tool composes it
    ρ = cons_calibrated.par["ρ"].value
    inverse = cons_calibrated.builder.policy["InvEuler:Aggregation"].compile_kernel()
    marginal, saving = numpy.array([2.0, 0.25, 0.8]), numpy.array([0.5, 1.0, 4.0])
    assert numpy.allclose(numpy.asarray(inverse(marginal, saving, ρ)), marginal ** (-1 / ρ))
    # while the row's relation keeps its clause, and with it the segment of
    # candidates below 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(0)) at zero saving
    row = str(cons_calibrated.builder.policy["InvEuler:Aggregation"])
    assert flat("𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) ⟂ a ≥ 0") in flat(row)


# the cons stage's `methods.yml` entry that binds the endogenous grid method
EGM = {"on": "policy", "method": "!egm", "handler": "cons-port:egm"}


def method_of(example):
    """The method tag a refusal example's methods entry writes, without its `!`."""
    return str(example.entry.get("method", "")).removeprefix("!")


def written_by(example):
    """The stage text a refusal example writes, or the lines it writes into a
    corpus stage file."""
    return example.text + "".join(changed for _, changed in example.changes)


def operations_of(stage):
    """The `Operations` section of the card of a stage's policy builder, its
    white space removed."""
    return flat("\n".join(section(str(stage.builder.policy), "Operations")))


def test_item_4_egm_binds_at_the_evaluation_of_cons_and_at_the_argmax_row_of_cons_argmax_and_is_refused_on_port(
        cons, cons_argmax, port, sa_savings, text_of, elaborate_text):
    for stage, box in ((cons, "policy:Evaluation"), (cons_argmax, "policy.optimality:Argmax")):
        methodized = stage.methodize({"stage": stage.name, "methods": [EGM]})
        assert [(str(bound), method.tag) for bound, method in methodized.bindings.methods.items()] == [(box, "egm")]
    # `cons.bl` is spelling C of the sub-brief (`spellings/spelling-C.bl`) up
    # to the spacing of its line 33: the policy card's operation column reads
    # the four rows of the sub-brief's §6 item 1, and the binding of `!egm` at
    # the Evaluation leaves every rule of the card's operations as it was
    methodized = copy_native(cons).methodize({"stage": "cons", "methods": [EGM]})
    assert [str(key) for key in methodized.builder.policy.primitives.list()] == [
        "InvEuler:Aggregation", "endoggrid:Aggregation", "cons_choice:Pullback", "Evaluation"]
    assert operations_of(methodized) == operations_of(cons)
    # port's policy block writes no grid line and holds no Argmax row
    with pytest.raises(TargetError) as refused:
        copy_native(port).methodize({"stage": "port", "methods": [EGM]})
    assert refused.value.rule == "method-attachment" and "grid line" in str(refused.value)
    # !vfi hands a whole backward decision builder to a toolkit and stands on
    # no Argmax row, named by its box or by its operator occurrence
    for target in ("policy.objective:Argmax", "policy.objective.argmax"):
        with pytest.raises(TargetError) as refused:
            copy_native(sa_savings).methodize({"stage": "sa_savings", "methods": [{"on": target, "method": "!vfi"}]})
        assert target in str(refused.value)
    # a dotted id whose owner is no line of its block, as `cons.bl` wrote at
    # 476c31134
    text = text_of("cons")
    for written, changed in (("[id=InvEuler]", "[id=argmax.FOC]"),
                             ("[id=endoggrid]", "[id=argmax.inverse_dcsn_kernal]")):
        assert text.count(written) == 1
        text = text.replace(written, changed)
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text, "applications/portfolio-choice/declaration/stages/cons/cons.bl")
    assert "argmax.FOC" in str(refused.value)
    # a refusal example of the package's catalogue for each of the three
    examples = [
        [example for example in EXAMPLES.values() if example.provokes == "methodize" and method_of(example) == "egm"
         and "port" in (example.corpus, Path(example.origin).stem)],
        [example for example in EXAMPLES.values() if example.provokes == "methodize" and method_of(example) == "vfi"
         and example.entry.get("on") in ("policy.objective:Argmax", "policy.objective.argmax")],
        [example for example in EXAMPLES.values() if "argmax.FOC" in written_by(example)],
    ]
    for found in examples:
        assert found and all(refusal_of(example) is not None for example in found)


def test_item_5_root_find_binds_at_the_argmax_row_and_vfi_on_the_backward_decision_builder_alone(
        cons_argmax, adjuster_cons):
    def bound(stage, entry):
        methodized = stage.methodize({"stage": stage.name, "methods": [entry]})
        return [(str(box), method.tag) for box, method in methodized.bindings.methods.items()]

    assert bound(cons_argmax, {"on": "policy.optimality.argmax", "method": "!root-find"}) == [
        ("policy.optimality:Argmax", "root-find")]
    assert bound(cons_argmax, {"on": "cntn_to_dcsn", "method": "!vfi"}) == [("cntn_to_dcsn", "vfi")]
    for target in ("policy", "dcsn_to_arvl"):
        with pytest.raises(TargetError) as refused:
            copy_native(cons_argmax).methodize({"stage": "cons_argmax", "methods": [{"on": target, "method": "!vfi"}]})
        assert refused.value.rule == "method-attachment", target
    # the durables adjuster's method choice of the factory's acceptance
    # (test_amd_fac_002.py, item 3), on the adjuster's backward decision
    # builder
    choice = {"on": "cntn_to_dcsn", "method": "!vfi", "handler": "fues-durables:make_adjuster_vfi"}
    assert bound(adjuster_cons, choice) == [("cntn_to_dcsn", "vfi")]
    with pytest.raises(TargetError):
        copy_native(adjuster_cons).methodize({"stage": "adjuster_cons", "methods": [{**choice, "on": "policy"}]})
    # on the adjuster's policy block (the sub-brief's §6 item 3) a computing
    # method binds at the Aggregation of the joint solve, the row whose output
    # is the pair (𝑐, ℎ_choice), and `!egm` at the Evaluation
    assert bound(adjuster_cons, {"on": "policy.choice.solve", "method": "!root-find"}) == [
        ("policy.choice:Aggregation", "root-find")]
    egm = {"on": "policy", "method": "!egm", "handler": "fues-durables:make_adjuster_ops"}
    assert bound(adjuster_cons, egm) == [("policy:Evaluation", "egm")]


def test_item_6_the_recorded_guard_names_the_new_rows_and_no_retired_kind():
    recordings = sorted(SNAPSHOT.glob("*.json")) + STORED
    assert [path.name for path in recordings if RETIRED.search(path.read_text(encoding="utf-8"))] == []
    for name, rows in (("sa_savings", ("policy.objective:Argmax",)),
                       ("ez_savings", ("policy.objective:Argmax",)),
                       ("tenure", ("policy.choice:Argmax",))):
        recorded = (SNAPSHOT / f"{name}.json").read_text(encoding="utf-8")
        assert [row for row in rows if row not in recorded] == [], name
    # the rows of the inverse Euler form, in the recording of the inverse
    # Euler stage, since the corpus `cons.bl` writes the maximization alone
    # (MB-T217)
    from bellman.refusal_examples import INVERSE_EULER
    from conftest import stage_from_text
    from snapshot.record import recording_of
    recorded = json.dumps(recording_of(stage_from_text(INVERSE_EULER, "t.bl")), ensure_ascii=False)
    rows = ("policy.InvEuler:Aggregation", "policy.identification:Pullback")
    assert [row for row in rows if row not in recorded] == []
    assert not RETIRED.search(recorded)
