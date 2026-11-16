"""Field equations: the law of motion g and the value aggregator G of a stage,
function aliases and named functions, and the law that each pullback refers
to."""

from collections import defaultdict

import pytest
from application_files import CORPUS, stage_file_id
from discopy.frobenius import Box, Hypergraph
from printed_text import rule_text
from snapshot.record import ELABORATED_FILES
from stage_builders import stage_from_file, stage_from_text
from stage_graphs import GRAINS, boxes_with_wires, graphs_inside, graphs_of, wire_sorts
from stage_texts import ARGMAX_DOC_LINE, corpus_text, two_nodes_text_with_changes
from two_sets import one_row_by_default

from bellman.display.cards import Rule
from bellman.native.identity import box_identity
from bellman.refusals import ConstructionError, NotConstructed
from bellman.stage.grains import block_id_of, kind_of, operators_of
from bellman.stage.kernels import affine
from bellman.typing.typed_expressions import (
    Compose,
    Unresolved,
    format_expression,
    obligation_entry,
)

# three backward lines of the stage text of `two_nodes_text_with_changes`, a
# stage with two shocks y and z, in which a second node, a line marked `!node`,
# is equal to the first and the value is the second node
NODE_CHAIN = (
    "    N1 = E_{y,z}(V[>]) :: [id=first, !node]\n    N2 = N1 :: [id=second, !node]\n    V = N2\n"
)


# the two stage files of the deaths of cagetti-denardi-2006, whose forward
# builders graph the construction refuses: the law of a shock is written
# with the family `Invariant`, whose set of results is not declared, so that
# neither stage holds a push-forward
NO_FORWARD_GRAPH = (
    "cagetti-denardi-2006/declaration/stages/entrepreneur_death/entrepreneur_death.bl",
    "cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl",
)


# the stage files that elaborate with both builders graphs
FILES_WITH_BOTH_GRAPHS = [
    src for src in ELABORATED_FILES if stage_file_id(src) not in NO_FORWARD_GRAPH
]


def aggregation_operator_of(stage, block):
    """The primitive aggregation box of the builder of the block `block`, as
    `operators_of` lists it."""
    return next(
        box
        for box in operators_of(stage)
        if block_id_of(box) == block and box_identity(box).kind == "Aggregation"
    )


def laws_of_motion(box):
    """The references of kind g, the laws of motion, among a box's data."""
    return {reference for reference in box.data if getattr(reference, "kind", None) == "g"}


def push_forward_laws(forward):
    """For each perch, the laws of motion of the push-forwards of the forward
    builders graph `forward` that write their measure at that perch, the
    boxes inside bubbles included."""
    laws = defaultdict(set)
    for _, held in graphs_inside(forward, "forward"):
        sorts = wire_sorts(held)
        for box, _, written in boxes_with_wires(held):
            if kind_of(box) == "Pushforward":
                for wire in written:
                    laws[sorts[wire].perch] |= laws_of_motion(box)
    return laws


def pullback_laws(backward, name):
    """`(where, box, perches, law)` for each law of motion that a pullback of
    the backward builders graph `backward`, named `name`, refers to, the
    boxes inside bubbles included: the graph that holds the pullback, the
    pullback, the perches of the wires that it reads and the law."""
    for where, held in graphs_inside(backward, name):
        sorts = wire_sorts(held)
        for box, read, _ in boxes_with_wires(held):
            if kind_of(box) == "Pullback":
                perches = sorted({sorts[wire].perch for wire in read})
                for law in laws_of_motion(box):
                    yield where, box, perches, law


def laws_without_a_push_forward(backward, forward, name):
    """Each law of motion that a pullback of the backward builders graph
    `backward`, named `name`, refers to, and to which no push-forward of the
    forward builders graph `forward` that writes its measure at the perch
    where the pullback reads its function refers. The two graphs are of one
    grain; the boxes inside bubbles are read. The package folds each pullback
    along the law of motion of the forward builder that writes the perch of
    the pullback's value inputs, and makes that forward builder's
    push-forward refer to the same law (`backward_block` of
    `bellman/fold/backward.py` and `block_rows_of` of
    `bellman/fold/stage_fold.py`)."""
    laws_into = push_forward_laws(forward)
    return [
        f"{where}: {box.name} reads a function at {perch} and refers to {law}, "
        f"to which no push-forward into {perch} refers"
        for where, box, perches, law in pullback_laws(backward, name)
        for perch in perches
        if law not in laws_into[perch]
    ]


def laws_without_a_record(backward, definitions, name):
    """Each law of motion that a pullback of the backward builders graph
    `backward`, named `name`, refers to, and for which `definitions`, the
    definitions of the stage, hold no record of kind g. The boxes inside
    bubbles are read. The package takes the law of motion of a pullback from
    the record of kind g that the definitions hold for the forward builder
    that writes the perch of the pullback's value inputs (the method
    `law_of_motion` in `bellman/fold/stage_fold.py`)."""
    violations = []
    for where, box, _, law in pullback_laws(backward, name):
        record = definitions.get(law)
        if record is None or record.kind != "g":
            violations.append(
                f"{where}: {box.name} refers to {law}, for which the definitions "
                "hold no record of kind g"
            )
    return violations


@pytest.fixture(scope="module")
def stage_without_documentary_line(cons_with_egm_lines_text):
    """The explicit consumption stage without its documentary maximization,
    so that the file declares no correspondence of its control."""
    return stage_from_text(
        cons_with_egm_lines_text.replace(ARGMAX_DOC_LINE, ""), "cons_without_documentation.bl"
    )


@pytest.fixture(scope="module")
def stage_with_a_node_chain():
    """The stage text of `two_nodes_text_with_changes` with the backward lines
    `NODE_CHAIN`."""
    return stage_from_text(two_nodes_text_with_changes(backward=NODE_CHAIN))


def test_without_a_documentary_line_the_domain_of_the_law_of_motion_is_its_image_in_its_target(
    cons_with_egm_lines_text, stage_without_documentary_line
):
    """Where the file declares no correspondence of the control, the feasible
    set in the type of the law of motion is the law's image in its declared
    target, held by reference, and names neither the saving nor Γ."""
    # the documentary line stands once in the stage text, so that its removal
    # takes effect
    assert cons_with_egm_lines_text.count(ARGMAX_DOC_LINE) == 1
    stage = stage_without_documentary_line
    [law] = stage.definitions.denote("cons:g:dcsn_to_cntn").denoted
    domain = str(law.mathematical_type)
    assert "𝑔(m_d, c) ∈ Xa" in domain
    assert "(m_d − c)" not in domain and "Γ" not in domain


def test_without_a_documentary_line_the_range_of_the_law_is_established_by_its_output_set(
    cons_with_egm_lines_text, stage_without_documentary_line
):
    """Where the file declares no correspondence of the control, the
    condition range-compatibility of the law of motion's line is established
    by the restriction to the output set that the law declares."""
    # the documentary line stands once in the stage text, so that its removal
    # takes effect
    assert cons_with_egm_lines_text.count(ARGMAX_DOC_LINE) == 1
    stage = stage_without_documentary_line
    [condition] = [
        item
        for item in stage.obligations()
        if item.condition == "range-compatibility" and str(item.entries[0]) == "dcsn_to_cntn.1"
    ]
    assert condition.status == "established"
    assert condition.evidence == (
        "restriction to the declared output set in D_g at dcsn_to_cntn.1",
    )


def test_without_a_documentary_line_the_compiled_push_forward_computes_the_law_of_motion(
    cons_with_egm_lines_text,
):
    """Where the file declares no correspondence of the control, the compiled
    kernel of the push-forward from decision to continuation computes the law
    of motion a = m_d − c."""
    # the documentary line stands once in the stage text, so that its removal
    # takes effect
    assert cons_with_egm_lines_text.count(ARGMAX_DOC_LINE) == 1
    # the stage is built here, since a calibration binds the stage that it is
    # called on
    stage = stage_from_text(
        cons_with_egm_lines_text.replace(ARGMAX_DOC_LINE, ""), "cons_without_documentation.bl"
    )
    calibrated = stage.calibrate({"ρ": 2.0})
    law = calibrated.builder.fwd["dcsn_to_cntn"]["pushforward"].compile_kernel()
    # the arguments are m_d and c
    assert law(2.0, 1.0) == 1.0
    assert law(1.0, 2.0) == -1.0


@pytest.mark.parametrize(
    ("stage_name", "perch", "affine_in"),
    [
        pytest.param("cons", "dcsn", "V in V≻", id="the decision value of cons"),
        # the identity aggregation of the arrival perch of cons.bl, since
        # ez_savings.bl has no arrival perch
        pytest.param("cons", "arvl", "V in V", id="the arrival value of cons"),
        pytest.param(
            "ez_savings",
            "dcsn",
            "none in E_{Ψ}(V[>]^(1 - γ))",
            id="the decision value of ez_savings, affine in no input",
        ),
    ],
)
def test_the_denotation_of_an_aggregation_states_the_value_input_in_which_its_map_is_affine(
    stage_name, perch, affine_in, request
):
    """The denotation of an aggregation states, under `affine`, in which of
    its value inputs its map is affine, or `none`."""
    # a box that writes one output states one line, whether its map is affine
    # or not; the map is named V, the name that the evaluation after the
    # aggregation gives it
    stage = request.getfixturevalue(stage_name)
    assert getattr(stage, perch).builder.bwd["aggregation"].denote().affine == affine_in


@pytest.mark.parametrize(
    ("stage_name", "block", "is_affine"),
    [
        pytest.param("cons", "cntn_to_dcsn", True, id="the decision builder of cons"),
        pytest.param("cons", "dcsn_to_arvl", True, id="the arrival builder of cons"),
        pytest.param("ez_savings", "cntn_to_dcsn", False, id="the decision builder of ez_savings"),
    ],
)
def test_affine_answers_whether_the_map_of_an_aggregation_is_affine_in_a_value_input(
    stage_name, block, is_affine, request
):
    """The function `affine` of the package, which the denotation of an
    aggregation reads, answers whether the map of the aggregation of a
    builder is affine in a value input."""
    stage = request.getfixturevalue(stage_name)
    assert affine(stage, aggregation_operator_of(stage, block)) is is_affine


def test_the_kernel_of_a_pullback_holds_the_record_of_the_law_of_motion_that_it_applies(cons):
    """The kernel of the pullback of the decision builder of the consumption
    stage holds among its origins the record of the law of motion from
    decision to continuation, the declaration that the pullback applies."""
    pullback = cons.dcsn.builder.bwd["pullback"]
    assert [record.identity for record in pullback.kernel().origins] == ["cons:g:dcsn_to_cntn"]


def test_the_conditions_of_a_function_body_stand_once_on_the_definition_that_carries_the_body():
    """The conditions of the arithmetic of the body of a function stand once,
    on the definition that carries the body, in that definition's own
    letters; an alias is followed to that definition, and the card of the
    aggregation that applies the function repeats none of them."""
    source = corpus_text("cons").replace(
        "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)", "base(x : ℝ₊₊) := x^(1-ρ)/(1-ρ)\n𝑢 := base"
    )
    stage = stage_from_text(source)
    # an entry of a condition holds its place, the condition and then the
    # node; the first two identify the condition here
    said = [
        tuple(obligation_entry(entry) for entry in o.entries[:2])
        for o in stage.obligations()
        if o.condition == "arithmetic-definedness"
    ]
    assert ("cons:function:base", "¬(1 - ρ = 0)") in said
    assert all(entries[0] == "cons:function:base" for entries in said)
    # the card of the aggregation that applies the function repeats none of
    # the conditions of its body
    face = str(stage.builder.bwd["cntn_to_dcsn"]["aggregation"].denote())
    assert "1 - ρ = 0" not in face and "x^(1 - ρ)" not in face


@pytest.mark.parametrize(
    "grain", ["sub_builders", "primitives"], ids=["the sub-builder grain", "the primitive grain"]
)
def test_a_chain_of_nodes_adds_no_input_that_no_builder_supplies(grain, stage_with_a_node_chain):
    """Where a backward block writes a node equal to another node, the
    backward builders graph at the sub-builder grain and at the primitive
    grain reads the continuation value as its one input, and no input that
    no builder supplies."""
    inputs = getattr(stage_with_a_node_chain.builder.bwd, grain).signature().inputs
    assert [str(wire.identity) for wire in inputs] == ["two_nodes:function:cntn:V"]
    # the signature writes "supplied by no builder" in the note of such an
    # input, which is no part of the identity and the type that a wire
    # unpacks into
    assert [str(wire) for wire in inputs if "supplied by no builder" in wire.note] == []


def test_the_kernel_of_the_aggregation_after_a_chain_of_nodes_reads_the_last_node(
    stage_with_a_node_chain,
):
    """Where a backward block writes a node equal to another node, the kernel
    of its aggregation reads the last node of the chain."""
    aggregation = stage_with_a_node_chain.builder.bwd["cntn_to_dcsn"]["aggregation"]
    assert str(aggregation.kernel()).splitlines()[0] == "𝐺 of cntn_to_dcsn: 𝐺(N2, k_d, c) = N2"


def test_an_alias_of_a_function_to_the_inverse_of_another_is_denoted_by_its_wording(
    cons_with_egm_lines_text,
):
    """The definition `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)`, an alias of a function that the
    package does not derive as an expression, is denoted by its rule held as
    its wording, marked `[textual]`."""
    source = cons_with_egm_lines_text
    written = "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)"
    assert source.count(written) == 1
    source = source.replace(written, "𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)")
    stage = stage_from_text(source, "function_alias.bl")
    answer = stage.definitions.denote("cons:function:𝑑𝑢𝑖𝑛𝑣")
    [denoted] = answer.denoted
    assert denoted.rule == "Inv(𝑑𝑢) [textual]"


@pytest.mark.parametrize(
    ("stage_name", "law"),
    [
        pytest.param(
            "adjuster_cons_with_egm_lines",
            "(a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔(m, z_d, c, h_choice)",
            id="the durables adjuster, a joint solve",
        ),
        pytest.param(
            "worker_saving",
            "(y_f, y_p) = 𝑔(m_f, m_p, w_d, c, c_p)",
            id="the pension worker, two complementarity lines",
        ),
    ],
)
def test_the_record_of_a_policy_of_two_controls_states_its_law_once_under_where_and_no_alias_of_it(
    stage_name, law, request
):
    """The record of a policy builder of two controls states the law of
    motion that its pullback reads, at no policy, once under `where`, with
    its several outputs on the left, and defines no alias of the law."""
    record = request.getfixturevalue(stage_name).builder.bwd["policy"].denote()
    [outputs] = [item for item in record.where if isinstance(item, Rule)]
    assert rule_text(outputs) == law
    assert not [
        item
        for item in record.where
        if getattr(item, "identity", None) is not None and item.identity.kind == "alias"
    ]


def test_a_joint_solve_is_one_aggregation_headed_by_its_unknowns_after_its_residual_lines(
    adjuster_cons_with_egm_lines,
):
    """The line `solve_{c, h_choice}(r₁, r₂)` of the durables adjuster forms
    one aggregation, whose two outputs are its unknowns, each holding the
    residual lines and then the head, and which has no residual input; the
    residuals read the outputs of the law by their names under `where`, and
    the last carries the region of the solve."""
    solve = adjuster_cons_with_egm_lines.builder.bwd["policy"]["choice:Aggregation"].denote()
    *residuals, head = solve.outputs[0].rules
    assert rule_text(head) == "(c, h_choice) = solve_{c, h_choice}(r₁, r₂)"
    assert solve.outputs[1].rules == solve.outputs[0].rules
    assert not [wire for wire in solve.inputs if wire.residuals]
    assert [rule_text(line) for line in residuals] == [
        "r₁ = c − c≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)",
        "r₂ = (1 + τ) · 𝑢_c(c) − 𝑢_h(h_choice) − β · D_{h_nxt_adj}V≻(a_nxt_adj, h_nxt_adj, "
        "z_nxt_adj)  on (m, z_d, c, h_choice) ∈ ℝ₊₊ × ℝ₊₊ × ℝ₊₊ × ℝ₊₊",
    ]


def test_the_feasibility_of_a_joint_solve_names_each_control_with_its_correspondence(
    adjuster_cons_with_egm_lines,
):
    """The set of the policies of the joint solve of the durables adjuster
    names each control with its correspondence and the arguments that the
    file writes, and no component of a projection."""
    solve = adjuster_cons_with_egm_lines.builder.bwd["policy"]["choice:Aggregation"].denote()
    carrier = format_expression(solve.outputs[0].mathematical_type.carrier, width=None)
    assert carrier.endswith("| c(m, z_d) ∈ Γ_c(m) ∧ h_choice(m, z_d) ∈ Γ_h(m − c(m, z_d))})")
    assert "[1]" not in carrier and "[2]" not in carrier


def test_the_pullback_of_a_joint_solve_composes_with_the_law_and_writes_no_projection_of_its_image(
    adjuster_cons_with_egm_lines,
):
    """Each output of the pullback of the policy builder of the durables
    adjuster is a function composed with the law of motion, and its
    definition writes no component of a projection of the law's image."""
    pullback = adjuster_cons_with_egm_lines.builder.bwd["policy"]["Pullback"].denote()
    # the two outputs, the continuation policy and the continuation value
    # pulled back, so that the loop below compares each
    assert len(pullback.outputs) == 2
    for wire in pullback.outputs:
        assert isinstance(wire.expression, Compose)
        assert "[1]" not in format_expression(wire.definition, width=None)


def test_the_feasibility_of_the_worker_policy_names_each_control_with_its_correspondence(
    worker_saving,
):
    """The set of the policies of the saving stage of the pension worker binds
    one function to each of its two controls, each in its own
    correspondence."""
    worker = worker_saving.builder.bwd["policy"].denote()
    carrier = format_expression(worker.outputs[0].mathematical_type.carrier, width=None)
    assert carrier.endswith("| c(m_f, m_p, w_d) ∈ Γ_c(m_f) ∧ c_p(m_f, m_p, w_d) ∈ Γ_p(w_d)})")


def test_the_definition_of_the_worker_policy_stays_unresolved(worker_saving):
    """The two complementarity lines of the pension worker form one system,
    whose rule reads the law of motion by reference and whose primitive
    definition the package does not resolve, so that the definition of the
    first output of the policy builder is unresolved."""
    worker = worker_saving.builder.bwd["policy"].denote()
    assert isinstance(worker.outputs[0].definition, Unresolved)


@pytest.mark.parametrize(
    "stage_name",
    ["retiree_saving", "keeper_saving", "adjuster_saving"],
    ids=["the pension retiree", "the housing keeper", "the housing adjuster"],
)
def test_the_decision_builder_of_a_saving_stage_is_read_at_one_policy_and_states_its_law(
    stage_name, request
):
    """The record of the backward decision builder of each of three saving
    stages is read at one policy and states the law of motion under
    `where`."""
    record = request.getfixturevalue(stage_name).builder.bwd["cntn_to_dcsn"].denote()
    assert len(record.at) == 1
    assert [item for item in record.where if isinstance(item, Rule)]


@pytest.mark.parametrize("src", one_row_by_default(FILES_WITH_BOTH_GRAPHS), ids=stage_file_id)
def test_a_pullback_refers_to_the_law_of_motion_of_the_push_forward_into_its_perch(
    read_only_stage_from_file, src
):
    """At every grain, a pullback of the backward builders graph that refers
    to a law of motion, and reads its function at a perch, refers to the law
    of motion of a push-forward of the forward builders graph that writes its
    measure at that perch, the law that the forward builder owns."""
    stage = read_only_stage_from_file(src)
    graphs = {
        (level, direction, grain): graph for level, direction, grain, graph in graphs_of(stage)
    }
    compared = []
    violations = []
    for grain in GRAINS:
        backward = graphs["builders", "backward", grain]
        forward = graphs["builders", "forward", grain]
        if isinstance(backward, NotConstructed) or isinstance(forward, NotConstructed):
            continue
        name = f"builders backward {grain}"
        compared += list(pullback_laws(backward, name))
        violations += laws_without_a_push_forward(backward, forward, name)
    # some pullback refers to a law of motion, so that the row compares one
    assert compared != []
    assert violations == []


def test_the_law_of_motion_check_reports_a_pullback_along_another_law():
    """When the pullback of the decision builder refers to the law of motion
    of the arrival builder, it refers to a law to which no push-forward into
    the continuation perch refers."""
    stage = stage_from_file(CORPUS["cons"])
    backward = stage.builder.bwd.primitives.graph
    boxes = {box.name: box for box in backward.boxes}
    pullback = boxes["cntn_to_dcsn:Pullback"]
    other_law = boxes["dcsn_to_arvl:Pullback"].data
    changed = Box(pullback.name, pullback.dom, pullback.cod, data=other_law)
    # `kind_of` reads the kind of a box from the box's identity
    changed.identity = pullback.identity
    rewired = Hypergraph(
        backward.dom,
        backward.cod,
        tuple(changed if box is pullback else box for box in backward.boxes),
        backward.wires,
    )
    forward = stage.builder.fwd.primitives.graph
    assert laws_without_a_push_forward(rewired, forward, "changed") == [
        "changed: cntn_to_dcsn:Pullback reads a function at cntn and refers to "
        "cons:g:arvl_to_dcsn, to which no push-forward into cntn refers"
    ]


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_definitions_hold_a_record_of_kind_g_for_each_law_of_a_pullback(
    read_only_stage_from_file, src
):
    """At every grain, the definitions of the stage hold a record of kind g
    for each law of motion that a pullback of the backward builders graph
    refers to."""
    stage = read_only_stage_from_file(src)
    compared = []
    violations = []
    for level, direction, grain, graph in graphs_of(stage):
        if (level, direction) != ("builders", "backward") or isinstance(graph, NotConstructed):
            continue
        name = f"builders backward {grain}"
        compared += list(pullback_laws(graph, name))
        violations += laws_without_a_record(graph, stage.definitions, name)
    # some pullback refers to a law of motion, so that the row compares one
    assert compared != []
    assert violations == []


def test_the_record_check_reports_a_law_of_motion_missing_from_the_definitions():
    """When the definitions lack the record of the law of motion of the
    arrival builder, the pullback of the arrival builder refers to a law for
    which they hold no record of kind g."""
    stage = stage_from_file(CORPUS["cons"])
    backward = stage.builder.bwd.primitives.graph
    definitions = {
        identity: record
        for identity, record in stage.definitions.items()
        if str(identity) != "cons:g:arvl_to_dcsn"
    }
    assert laws_without_a_record(backward, definitions, "changed") == [
        "changed: dcsn_to_arvl:Pullback refers to cons:g:arvl_to_dcsn, for which the "
        "definitions hold no record of kind g"
    ]


def test_a_written_zero_divisor_in_a_function_body_is_refused_at_the_definition():
    """A divisor written as zero in the body of a function is refused under
    `divisor-nonzero` at the position of the function's definition."""
    # the example of `divisor-nonzero` divides in a line of a block; a
    # function body is refused at the file position of its definition record
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(
            "@stage: t\n𝑓(x : ℝ₊) := x/0\n"
            "[id=b, (v : ℝ₊) : !arvl -> (w : ℝ) : !dcsn] {\n    w = 𝑓(v)\n}\n"
        )
    error = refused.value
    # the address is the origin t.bl and line 2, which is also the line; the
    # column is 1
    assert (error.rule, error.address, error.line, error.column) == (
        "divisor-nonzero",
        "t.bl:2",
        2,
        1,
    )
    assert "`x/0` divides by zero" in error.message
