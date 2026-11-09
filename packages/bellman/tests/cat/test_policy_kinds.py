"""Policy operations, compilation, and authored method places.

An operative maximization forms an Argmax operation; a relation or joint
solution forms an Aggregation. A property of a maximization has no separate
operation or method place. Numerical checks retain explicit kernels and
refusals for operations without a function. Methods stay at their authored
builder or operator, under the catalogue's admitted kinds.
"""
import json
import re
from pathlib import Path

import numpy
import pytest

from bellman.native.hypergraphs import copy_native

from bellman.refusals import ConstructionError, NotConstructed
from conftest import (CORPUS_CALIBRATIONS, DURABLES, ROOT, SA_SAVINGS_CALIBRATIONS, STAGE_FILES,
                      flat)
from snapshot.record import CORPUS_RECORDINGS, recording_path

APPLICATIONS = ROOT / "applications"
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
# The named applications contain operative maximizations. The housing-owner
# stage is refused before construction, as the corpus recording specifies.
NAMED = {
    "applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl",
    "applications/epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl",
    "applications/durables/declaration/stages/tenure/tenure.bl",
    "applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
    "applications/housing-owner/declaration/stages/housing_choice/housing_choice.bl",
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
@pytest.mark.parametrize("src", STAGE_FILES,
                         ids=lambda path: path.relative_to(APPLICATIONS).as_posix())
def test_item_1_no_output_of_a_core_application_names_a_retired_kind_and_each_operative_argmax_line_forms_an_argmax_row(
        src, elaborate_text):
    relative = src.relative_to(ROOT).as_posix()
    lines = argmax_lines(src)
    if relative in NAMED:
        assert any(not declared for _, _, _, declared in lines), relative
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
    assert flat("optimality.euler: 𝑑𝑢(𝑐(m_d))") in flat(card)
    assert flat("⟂ m_d − 𝑐(m_d) ≥ 0") in flat(card)
    # no box at any grain of the builders graph or of the initial diagram, and
    # no method place, carries the property's id
    backward = cons_argmax.builder.bwd
    addresses = [str(key) for grain in (backward.primitives, backward.sub_builders, policy.primitives, policy.sub_builders,
                                        cons_argmax.initial.backward.primitives) for key in grain.list()]
    places = [row["address"] for row in cons_argmax.places()]
    assert [address for address in addresses + places if "euler" in address] == []
    with pytest.raises(ConstructionError) as refused:
        copy_native(cons_argmax).methodize({
            "text": "@methods: cons_argmax\npolicy.optimality.euler.method : !root_find\n",
            "origin": "cons_argmax.methods.bl"})
    assert refused.value.rule == "name-in-scope"
    assert "policy.optimality.euler" in str(refused.value)
    # No separate optimality obligation is introduced by the property.
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
    "cons": ("InvEuler:Aggregation", "grid:Aggregation"),
    "cons_argmax": ("Pullback", "optimality:Aggregation"),
    "adjuster_cons": ("InvEuler:Aggregation", "endoggrid:Aggregation", "Pullback"),
    "port": ("Pullback", "foc:Aggregation:1"),
    "sa_savings": ("Pullback", "objective:Aggregation:2", "objective:Aggregation:1", "objective:Aggregation"),
}
# among the others, one row of each kind that has none: the identification,
# a joint solve's residual system, a choice, an expectation and an evaluation
WITHOUT = {
    "cons": ("identification:Pullback", "Evaluation"),
    "adjuster_cons": ("choice:Aggregation",),
    "cons_argmax": ("optimality:Argmax",),
    "sa_savings": ("objective:Expectation:1",),
}


def test_item_3_compile_kernel_answers_the_explicit_side_of_the_inverse_euler_row_and_refuses_each_row_without_one(
        cons_methodized, cons_argmax, adjuster_cons, port, sa_savings):
    versions = {
        "cons": cons_methodized,
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
    # 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) = D_{a}𝑉≻(a)^(−1/ρ), with its arguments the marginal value and
    # the saving, as the cons-port tool composes it
    ρ = cons_methodized.par["ρ"].value
    inverse = cons_methodized.builder.policy["InvEuler:Aggregation"].compile_kernel()
    marginal, saving = numpy.array([2.0, 0.25, 0.8]), numpy.array([0.5, 1.0, 4.0])
    assert numpy.allclose(numpy.asarray(inverse(numpy.zeros_like(saving), saving, marginal, ρ)), marginal ** (-1 / ρ))
    # while the row's relation keeps its clause, and with it the segment of
    # candidates below 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(0)) at zero saving
    row = str(cons_methodized.builder.policy["InvEuler:Aggregation"])
    assert flat("𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0") in flat(row)


def test_item_4_egm_stands_at_its_authored_builder_or_argmax_and_refuses_an_evaluation(
        cons_candidate, cons_argmax, port, sa_savings, elaborate_text):
    for stage, target in ((cons_candidate, "policy"), (cons_argmax, "policy.optimality.argmax"),
                          (port, "policy")):
        bound = copy_native(stage).methodize({
            "text": f"@methods: {stage.name}\n{target}.method : !egm\n",
            "origin": f"{stage.name}.methods.bl"})
        assert bound.methods[target].word == "!egm"
        if target == "policy":
            assert any(item.condition == "egm-eligibility" for item in bound.obligations())
        assert [str(key) for key in bound.builder.policy.list()] == [
            str(key) for key in stage.builder.policy.list()]
    for stage, target, word in ((cons_candidate, "policy.evaluate", "egm"),
                                (sa_savings, "policy.objective.argmax", "vfi")):
        with pytest.raises(ConstructionError) as refused:
            copy_native(stage).methodize({
                "text": f"@methods: {stage.name}\n{target}.method : !{word}\n",
                "origin": f"{stage.name}.methods.bl"})
        assert refused.value.rule == "method-admission"
        assert target in str(refused.value)
    # A property must name an authored parent line.
    from conftest import C_LINES, twin_text
    text = twin_text("cons", C_LINES).replace("[id=InvEuler]", "[id=argmax.FOC]")
    with pytest.raises(ConstructionError) as refused:
        elaborate_text(text, "cons.bl")
    assert "argmax.FOC" in str(refused.value)


def test_item_5_root_find_is_an_operator_method_and_vfi_is_a_builder_method(
        cons_argmax, adjuster_cons):
    for stage, target, word in (
        (cons_argmax, "policy.optimality.argmax", "root_find"),
        (adjuster_cons, "policy.choice.solve", "root_find"),
        (cons_argmax, "cntn_to_dcsn", "vfi"),
        (cons_argmax, "policy", "vfi"),
        (cons_argmax, "dcsn_to_arvl", "vfi"),
        (adjuster_cons, "cntn_to_dcsn", "vfi"),
        (adjuster_cons, "policy", "egm"),
    ):
        bound = copy_native(stage).methodize({
            "text": f"@methods: {stage.name}\n{target}.method : !{word}\n",
            "origin": f"{stage.name}.methods.bl"})
        assert bound.methods[target].word == "!" + word
    for stage, target, word in ((cons_argmax, "policy", "root_find"),
                               (adjuster_cons, "policy.choice.solve", "vfi")):
        with pytest.raises(ConstructionError) as refused:
            copy_native(stage).methodize({
                "text": f"@methods: {stage.name}\n{target}.method : !{word}\n",
                "origin": f"{stage.name}.methods.bl"})
        assert refused.value.rule == "method-admission"
        assert target in str(refused.value)
