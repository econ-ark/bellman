"""The policy builder: the operations its lines form, the properties of a
maximization, the methods it admits, the kernels of its rows, the lines marked
`!doc`, the law of motion at the policy, and the grid lines and systems of its
candidates."""

import functools
import json
import re

import numpy
import pytest
from application_files import (
    ADJUSTER_CONS_WITH_EGM_LINES_FILE,
    DURABLES,
    FIRST_CALIBRATIONS,
    ROOT,
    SA_SAVINGS_CALIBRATIONS,
    STAGE_FILES,
    stage_file_id,
)
from printed_text import PrintedStage, card_section_lines, flat, rule_text
from snapshot.record import ELABORATED_FILES, compared_suffixes, recording_path
from stage_builders import methodized_copy, stage_from_text
from stage_texts import ARGMAX_DOC_LINE, CONS_RISKY_ASSET_PORT_TEXT
from two_sets import one_row_by_default

from bellman.native.hypergraphs import copy_native
from bellman.native.predicates import Member
from bellman.refusal_examples import INVERSE_EULER
from bellman.refusals import ConstructionError
from bellman.stage.kernels import compile_kernel, kernel
from bellman.syntax.terms import Mul, Operator, Sub, Tuple
from bellman.typing.typed_expressions import (
    Apply,
    Compose,
    Lambda,
    format_expression,
    free_identities,
    variable_identity,
)

# a word that begins with `Selection`, `Inversion` or `Solution`, which no key
# of a row, identity of a box, label or kind of an encoding holds: a row of a
# card is of one of eight kinds of operation, and none of the three words
# names one of them
NOT_A_KIND_OF_OPERATION = re.compile(r"\b(?:Selection|Inversion|Solution)")


# the header of a block, whose id names the builder its lines fold to
BLOCK_HEADER = re.compile(r"^\[id=(?P<block>[^,\]\s]+)")


# a line whose right side is an argmax, and the tags of its annotation
ARGMAX_EQUATION = re.compile(r"=\s*argmax_\{.*::\s*\[(?P<tags>[^\]]*)\]")


# five stage files that each write an argmax line not marked `!doc`; the
# construction of the housing-owner stage is refused, and only its text is read
FILES_WITH_AN_OPERATIVE_ARGMAX = [
    ROOT / "applications" / path
    for path in (
        "smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl",
        "epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl",
        "durables/declaration/stages/tenure/tenure.bl",
        "retirement-choice/declaration/stages/ret_choice/ret_choice.bl",
        "housing-owner/declaration/stages/housing_choice/housing_choice.bl",
    )
]


def argmax_lines(path):
    """`(line number, block id, line id, doc)` of every argmax line of a
    stage file: an argmax on the right of its equation, the line's id from its
    annotation, and whether the annotation marks the line `!doc`."""
    block, found = None, []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        opened = BLOCK_HEADER.match(line)
        block = opened["block"] if opened else block
        written = ARGMAX_EQUATION.search(line)
        if written:
            identity = re.search(r"\bid=([^,\]\s]+)", written["tags"])[1]
            found.append((number, block, identity, "!doc" in written["tags"]))
    return found


@functools.cache
def files_with_an_argmax_line():
    """The stage files that elaborate and write an argmax line, operative or
    marked `!doc`, in the order of `ELABORATED_FILES`; each has a policy
    block, and the others have none."""
    return [src for src in ELABORATED_FILES if argmax_lines(src)]


def pytest_generate_tests(metafunc):
    """Gives each test that the mapping below names its rows `argmax_file`,
    read from the stage files when pytest collects the tests, with the file
    of the consumption stage in the default set."""
    # the name of each test with these rows, mapped to the function that
    # gives the rows
    rows = dict.fromkeys(
        (
            "test_no_output_of_a_stage_with_a_maximization_writes_selection_inversion_or_solution",
            "test_no_output_of_a_stage_with_a_maximization_writes_the_kind_argmax_with_a_subscript",
            "test_the_argmax_operations_of_a_stage_are_its_argmax_lines_not_marked_doc",
            "test_the_card_of_each_builder_with_an_argmax_line_prints_the_head_argmax",
            "test_no_encoding_of_a_stage_with_a_maximization_holds_an_optimality_obligation",
        ),
        files_with_an_argmax_line,
    ).get(metafunc.function.__name__)
    if rows is not None:
        metafunc.parametrize("argmax_file", one_row_by_default(rows()), ids=stage_file_id)


def printed_outputs(stage):
    """`(what, text)` of everything a stage prints or encodes: the stage's
    card; the listing and the drawing of each builders graph at the builder,
    sub-builder and primitive grains, and the card of each builder and of each
    of its primitives; the drawings of the two initial diagrams; the card of
    each definition; and the encoding."""
    yield "the stage's card", str(stage.denote())
    for direction, graph in (("backward", stage.builder.bwd), ("forward", stage.builder.fwd)):
        for grain in (graph, graph.primitives, graph.sub_builders):
            drawing = grain.diagram()
            yield f"a {direction} listing", str(grain.list())
            yield f"a {direction} drawing", "\n".join(drawing.labels) + "\n" + drawing.source
        for name in graph.list():
            builder = graph[name]
            yield f"the card of {name}", str(builder)
            for key in builder.primitives.list():
                yield f"the card of {name} / {key}", str(builder.primitives[key])
    for direction in ("backward", "forward"):
        drawing = getattr(stage.initial, direction).diagram()
        yield (
            f"the {direction} initial diagram",
            "\n".join(drawing.labels) + "\n" + drawing.source,
        )
    listing = stage.definitions.list()
    for kind in listing:
        for identity in listing[kind]:
            yield f"the card of {identity}", str(stage.definitions.denote(identity))
    yield "the encoding", json.dumps(stage.encoding(), ensure_ascii=False)


@pytest.fixture(scope="module")
def application_outputs(read_only_stage_from_file):
    """`application_outputs(src)`: the `printed_outputs` of the stage of the
    stage file `src`, computed once for each file."""
    return functools.cache(lambda src: tuple(printed_outputs(read_only_stage_from_file(src))))


def holds_the_optimality_obligation(value):
    """Whether a value of an encoding, at any depth of its dictionaries and
    lists, holds an obligation of the condition `optimality`: a dictionary
    whose field `condition` is that word."""
    if isinstance(value, dict):
        return value.get("condition") == "optimality" or any(
            map(holds_the_optimality_obligation, value.values())
        )
    if isinstance(value, list):
        return any(map(holds_the_optimality_obligation, value))
    return False


@pytest.mark.parametrize(
    "src",
    one_row_by_default(FILES_WITH_AN_OPERATIVE_ARGMAX, default=FILES_WITH_AN_OPERATIVE_ARGMAX[3]),
    ids=stage_file_id,
)
def test_argmax_lines_finds_a_line_not_marked_doc_in_each_of_five_maximizing_files(src):
    """`argmax_lines`, which the tables of this file read, finds in each of
    five stage files that maximize an argmax line not marked `!doc`."""
    lines = argmax_lines(src)
    assert any(not doc for _, _, _, doc in lines)


@pytest.mark.parametrize("src", one_row_by_default(STAGE_FILES), ids=stage_file_id)
def test_no_recording_of_a_stage_file_writes_selection_inversion_or_solution(src):
    """No recording of a stage file that the corpus tests compare, its parsed
    term or its printed text, holds a word that begins with `Selection`,
    `Inversion` or `Solution`."""
    for suffix in compared_suffixes(src):
        stored = recording_path(src, suffix)
        assert not NOT_A_KIND_OF_OPERATION.search(stored.read_text(encoding="utf-8")), stored.name


# rows: one for each stage file of the applications that elaborates and writes
# an argmax line, operative or marked `!doc`, given by `pytest_generate_tests`
def test_no_output_of_a_stage_with_a_maximization_writes_selection_inversion_or_solution(
    argmax_file, application_outputs
):
    """No card, listing, drawing or encoding of the stage of a stage file that
    writes an argmax line holds a word that begins with `Selection`,
    `Inversion` or `Solution`."""
    printed = application_outputs(argmax_file)
    assert [
        (what, match.group())
        for what, text in printed
        for match in NOT_A_KIND_OF_OPERATION.finditer(text)
    ] == []


# rows: one for each stage file of the applications that elaborates and writes
# an argmax line, operative or marked `!doc`, given by `pytest_generate_tests`
def test_no_output_of_a_stage_with_a_maximization_writes_the_kind_argmax_with_a_subscript(
    argmax_file, application_outputs
):
    """No output of the stage of a stage file that writes an argmax line holds
    `Argmax_{`: a maximization prints with the operator head `argmax`, and
    `Argmax` is the kind of the row it forms."""
    printed = application_outputs(argmax_file)
    assert [what for what, text in printed if "Argmax_{" in text] == []


# rows: one for each stage file of the applications that elaborates and writes
# an argmax line, operative or marked `!doc`, given by `pytest_generate_tests`
def test_the_argmax_operations_of_a_stage_are_its_argmax_lines_not_marked_doc(
    argmax_file, read_only_stage_from_file
):
    """The backward builders graph of the stage of a stage file has one
    `Argmax` operation for each argmax line not marked `!doc`, keyed by the
    line's block and id, and none for a line marked `!doc`."""
    lines = argmax_lines(argmax_file)
    stage = read_only_stage_from_file(argmax_file)
    keys = [str(key) for key in stage.builder.bwd.primitives.list()]
    assert sorted(key for key in keys if key.endswith("Argmax")) == sorted(
        f"{block}.{line}:Argmax" for _, block, line, doc in lines if not doc
    )


# rows: one for each stage file of the applications that elaborates and writes
# an argmax line, operative or marked `!doc`, given by `pytest_generate_tests`
def test_the_card_of_each_builder_with_an_argmax_line_prints_the_head_argmax(
    argmax_file, read_only_stage_from_file
):
    """The card of each backward builder whose block writes an argmax line
    prints the maximization with the operator head `argmax` and its subscript
    under `Operations` or under `Declared`."""
    stage = read_only_stage_from_file(argmax_file)
    # the section `Source` quotes the line as the file writes it, so it is
    # left out: the head must stand where the card prints the maximization
    cards = {block: str(stage.builder.bwd[block]) for _, block, _, _ in argmax_lines(argmax_file)}
    shown = {
        block: flat(
            "\n".join(
                card_section_lines(card, "Operations") + card_section_lines(card, "Declared")
            )
        )
        for block, card in cards.items()
    }
    assert [block for block, text in shown.items() if "argmax_{" not in text] == []


def test_the_policy_card_of_cons_prints_its_maximization_with_the_binder_of_its_control(cons):
    """The card of the policy builder of `cons` prints the maximization of its
    stage file with the operator head `argmax`, the binder `cp ∈ Γ(m_d)` of
    its control and the policy 𝑐 on the left."""
    assert flat("𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]") in flat(
        str(cons.builder.policy)
    )


def test_the_policy_builder_of_a_maximization_with_a_property_lists_four_operations(
    cons_argmax,
):
    """The policy builder of `cons_argmax`, whose operative argmax line
    carries the first-order condition as its property, lists a pullback, an
    aggregation, an `Argmax` and an evaluation, and no operation for the
    property."""
    policy = cons_argmax.builder.policy
    assert [str(key) for key in policy.primitives.list()] == [
        "Pullback",
        "optimality:Aggregation",
        "optimality:Argmax",
        "Evaluation",
    ]


def test_the_policy_card_prints_the_property_of_an_argmax_under_its_row(cons_argmax):
    """The card of the policy builder of `cons_argmax` prints the property
    `optimality.euler`, with its clause, under the `Argmax` row and before the
    evaluation."""
    card = str(cons_argmax.builder.policy)
    lines = card.splitlines()
    row = next(i for i, line in enumerate(lines) if "optimality:Argmax" in line)
    label = next(i for i, line in enumerate(lines) if "optimality.euler" in line)
    closing = next(i for i, line in enumerate(lines) if i > row and "Evaluation" in line)
    assert row <= label < closing
    assert flat("optimality.euler: 𝑑𝑢(𝑐(m_d))") in flat(card)
    assert flat("⟂ m_d − 𝑐(m_d) ≥ 0") in flat(card)


def test_the_property_of_an_argmax_is_no_box_and_no_method_place(cons_argmax):
    """No box of the backward builders graph, of the policy builder or of the
    backward initial diagram, at any grain, and no method place of
    `cons_argmax` carries the id of the property."""
    backward = cons_argmax.builder.bwd
    policy = cons_argmax.builder.policy
    # the property stands on the stage: its card prints it under the Argmax row
    assert flat("optimality.euler: 𝑑𝑢(𝑐(m_d))") in flat(str(policy))
    grains = (
        backward.primitives,
        backward.sub_builders,
        policy.primitives,
        policy.sub_builders,
        cons_argmax.initial.backward.primitives,
    )
    addresses = [str(key) for grain in grains for key in grain.list()]
    places = [row["address"] for row in cons_argmax.places()]
    assert [address for address in addresses + places if "euler" in address] == []


def test_a_method_typed_at_the_property_of_an_argmax_is_refused(cons_argmax):
    """`methodize` refuses a method typed at the property `optimality.euler`
    as a name that is not in scope."""
    # the property stands on the stage: its card prints it under the Argmax row
    assert flat("optimality.euler: 𝑑𝑢(𝑐(m_d))") in flat(str(cons_argmax.builder.policy))
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(cons_argmax, "policy.optimality.euler.method : !root_find\n")
    assert refused.value.rule == "name-in-scope"
    assert "policy.optimality.euler" in str(refused.value)


@pytest.mark.parametrize(
    "name", ["cons_argmax", "cons", "cons_obs", "port", "cons_with_egm_lines"]
)
def test_no_obligation_of_a_stage_with_a_maximization_has_the_condition_optimality(request, name):
    """No obligation of a stage that writes a maximization, operative or
    marked `!doc`, has the condition `optimality`: neither a maximization nor
    its property introduces one."""
    stage = request.getfixturevalue(name)
    assert "optimality" not in {item.condition for item in stage.obligations()}


# rows: one for each stage file of the applications that elaborates and writes
# an argmax line, operative or marked `!doc`, given by `pytest_generate_tests`
def test_no_encoding_of_a_stage_with_a_maximization_holds_an_optimality_obligation(
    read_only_stage_from_file, argmax_file
):
    """The encoding of the stage of a stage file that writes an argmax line
    holds no obligation of the condition `optimality`: a property of a
    maximization introduces no obligation of its own."""
    assert not holds_the_optimality_obligation(read_only_stage_from_file(argmax_file).encoding())


# the rows of five policy builders whose rule has an explicit side, which
# `compile_kernel` compiles: a pullback, whose side is the law of motion, a
# value aggregation, or a relation one of whose sides is the output's name
# alone and the other an explicit function of the row's inputs; every other
# row of these builders has none
ROWS_WITH_AN_EXPLICIT_SIDE = {
    "cons": ("InvEuler:Aggregation", "grid:Aggregation"),
    "cons_argmax": ("Pullback", "optimality:Aggregation"),
    "adjuster_cons": ("InvEuler:Aggregation", "endoggrid:Aggregation", "Pullback"),
    "port": ("Pullback", "foc:Aggregation:1"),
    "sa_savings": (
        "Pullback",
        "objective:Aggregation:2",
        "objective:Aggregation:1",
        "objective:Aggregation",
    ),
}


# among the other rows, one of each kind that has no explicit side: the
# identification, the residual system of a joint solve, an Argmax, an
# expectation and an evaluation
ROWS_WITHOUT_AN_EXPLICIT_SIDE = {
    "cons": ("identification:Pullback", "Evaluation"),
    "adjuster_cons": ("choice:Aggregation",),
    "cons_argmax": ("optimality:Argmax",),
    "sa_savings": ("objective:Expectation:1",),
}


@pytest.fixture(scope="module")
def calibrated_stages(
    cons_methodized, cons_argmax, adjuster_cons_with_egm_lines, port, sa_savings
):
    """The five calibrated stages whose policy rows the kernel tests read, by
    stage name, each calibrated on a copy of its own."""
    return {
        "cons": cons_methodized,
        "cons_argmax": copy_native(cons_argmax).calibrate(FIRST_CALIBRATIONS["cons"]),
        "adjuster_cons": copy_native(adjuster_cons_with_egm_lines).calibrate(
            str(DURABLES / "calibration/durables.yml")
        ),
        "port": copy_native(port).calibrate(FIRST_CALIBRATIONS["port"]),
        "sa_savings": copy_native(sa_savings).calibrate(SA_SAVINGS_CALIBRATIONS[0]),
    }


@pytest.mark.parametrize("name", list(ROWS_WITH_AN_EXPLICIT_SIDE))
def test_compile_kernel_compiles_a_policy_row_exactly_where_its_rule_has_an_explicit_side(
    calibrated_stages, name
):
    """`compile_kernel` compiles each row of the policy builder of a
    calibrated stage whose rule has an explicit side, and refuses every other
    row of the builder under the rule `kernel-target`."""
    policy = calibrated_stages[name].builder.policy
    keys = [str(key) for key in policy.primitives.list()]
    explicit = ROWS_WITH_AN_EXPLICIT_SIDE[name]
    assert set(explicit) | set(ROWS_WITHOUT_AN_EXPLICIT_SIDE.get(name, ())) <= set(keys)
    assert [key for key in explicit if not callable(policy[key].compile_kernel())] == []
    for key in keys:
        if key in explicit:
            continue
        with pytest.raises(ConstructionError) as refused:
            policy[key].compile_kernel()
        assert refused.value.rule == "kernel-target", key


def test_the_inverse_euler_kernel_of_cons_answers_its_explicit_side(cons_methodized):
    """At a positive saving, the kernel of the inverse Euler row of `cons`
    answers 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) = D_{a}𝑉≻(a)^(−1/ρ)."""
    ρ = cons_methodized.par["ρ"].value
    inverse = cons_methodized.builder.policy["InvEuler:Aggregation"].compile_kernel()
    marginal, saving = numpy.array([2.0, 0.25, 0.8]), numpy.array([0.5, 1.0, 4.0])
    # the kernel's arguments in order: the value 𝑉≻, which the explicit side
    # does not read, the saving a, the marginal value D_{a}𝑉≻ and the
    # parameter ρ
    assert numpy.allclose(
        numpy.asarray(inverse(numpy.zeros_like(saving), saving, marginal, ρ)),
        marginal ** (-1 / ρ),
    )


def test_the_inverse_euler_row_of_cons_keeps_its_clause(cons_methodized):
    """The card of the inverse Euler row of `cons` keeps the relation with its
    clause `⟂ a ≥ 0`, which admits the candidates below 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(0)) at
    zero saving."""
    row = str(cons_methodized.builder.policy["InvEuler:Aggregation"])
    assert flat("𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0") in flat(row)


@pytest.mark.parametrize(
    ("name", "target", "word", "admitted"),
    [
        ("cons_with_egm_lines", "policy", "egm", True),
        ("cons_argmax", "policy.optimality.argmax", "egm", True),
        ("port", "policy", "egm", True),
        ("cons_argmax", "policy.optimality.argmax", "root_find", True),
        ("adjuster_cons_with_egm_lines", "policy.choice.solve", "root_find", True),
        ("cons_argmax", "cntn_to_dcsn", "vfi", True),
        ("cons_argmax", "policy", "vfi", True),
        ("cons_argmax", "dcsn_to_arvl", "vfi", True),
        ("adjuster_cons_with_egm_lines", "cntn_to_dcsn", "vfi", True),
        ("adjuster_cons_with_egm_lines", "policy", "egm", True),
        ("cons_with_egm_lines", "policy.evaluate", "egm", False),
        ("sa_savings", "policy.objective.argmax", "vfi", False),
        ("cons_argmax", "policy", "root_find", False),
        ("adjuster_cons_with_egm_lines", "policy.choice.solve", "vfi", False),
    ],
    ids=[
        "egm-at-the-policy-builder-of-cons_candidate",
        "egm-at-the-argmax-of-cons_argmax",
        "egm-at-the-policy-builder-of-port",
        "root_find-at-the-argmax-of-cons_argmax",
        "root_find-at-the-joint-solve-of-adjuster_cons",
        "vfi-at-cntn_to_dcsn-of-cons_argmax",
        "vfi-at-the-policy-builder-of-cons_argmax",
        "vfi-at-dcsn_to_arvl-of-cons_argmax",
        "vfi-at-cntn_to_dcsn-of-adjuster_cons",
        "egm-at-the-policy-builder-of-adjuster_cons",
        "refused-egm-at-the-evaluation-of-cons_candidate",
        "refused-vfi-at-the-argmax-of-sa_savings",
        "refused-root_find-at-the-policy-builder-of-cons_argmax",
        "refused-vfi-at-the-joint-solve-of-adjuster_cons",
    ],
)
def test_methodize_admits_a_method_word_only_at_a_place_of_its_kind(
    request, name, target, word, admitted
):
    """`methodize` binds `!vfi` at a builder, `!root_find` at an operation
    and `!egm` at a policy builder or at an argmax, and refuses each word at a
    place of another kind under the rule `method-admission`, naming the
    place."""
    stage = request.getfixturevalue(name)
    if admitted:
        bound = methodized_copy(stage, f"{target}.method : !{word}\n")
        assert bound.methods[target].word == "!" + word
        return
    with pytest.raises(ConstructionError) as refused:
        methodized_copy(stage, f"{target}.method : !{word}\n")
    assert refused.value.rule == "method-admission"
    assert target in str(refused.value)


@pytest.mark.parametrize(
    ("name", "target"),
    [
        ("cons_with_egm_lines", "policy"),
        ("cons_argmax", "policy.optimality.argmax"),
        ("port", "policy"),
    ],
    ids=[
        "the-policy-builder-of-cons_candidate",
        "the-argmax-of-cons_argmax",
        "the-policy-builder-of-port",
    ],
)
def test_binding_egm_leaves_the_operations_of_the_policy_builder_unchanged(request, name, target):
    """Binding `!egm` at a policy builder or at its argmax leaves the listing
    of the policy builder as it was."""
    stage = request.getfixturevalue(name)
    bound = methodized_copy(stage, f"{target}.method : !egm\n")
    assert bound.methods[target].word == "!egm"
    assert [str(key) for key in bound.builder.policy.list()] == [
        str(key) for key in stage.builder.policy.list()
    ]


def test_a_line_whose_dotted_id_names_no_line_of_its_block_is_refused(cons_with_egm_lines_text):
    """A line whose dotted id names as its parent no line of its block is
    refused, and the refusal names the id."""
    text = cons_with_egm_lines_text.replace("[id=InvEuler]", "[id=argmax.FOC]")
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(text, "cons.bl")
    assert "argmax.FOC" in str(refused.value)


def test_a_maximization_with_no_set_ranges_over_the_declared_set_of_its_control(
    cons_with_egm_lines_text,
):
    """A binder written without a set ranges over the declared set of its
    control, read by identity, and not over the correspondence `Γ`, which the
    stage still declares."""
    stage = stage_from_text(
        cons_with_egm_lines_text.replace("argmax_{cp : Γ(m_d)}", "argmax_{c}").replace(
            "𝑢(cp)", "𝑢(c)"
        )
    )
    [declared] = stage.builder.bwd["policy"].denote().doc
    statement = format_expression(declared.statement, width=None)
    assert statement == "c(m_d) ∈ argmax_{c ∈ ℝ₊₊} [𝑢(c) + V≻(𝑔(m_d, c))]"
    assert "UNRESOLVED" not in statement


@pytest.fixture(scope="module")
def risky_portfolio():
    """The calibrated stage of the portfolio choice with one risky asset,
    whose objective is an expectation over the return shock φ and whose law
    of motion is k_next = (R + ς·(φ − R))·w_d."""
    return stage_from_text(CONS_RISKY_ASSET_PORT_TEXT).calibrate(
        {"R": 1.03, "φ_mean": 1.08, "σ_φ": 0.2}
    )


def test_the_doc_statement_of_a_portfolio_choice_keeps_the_expectation_of_its_objective(
    risky_portfolio,
):
    """The policy builder of the portfolio choice holds its `!doc` line as a
    membership in an argmax of the expectation over φ of the continuation
    value read at the law of motion of the point (w_d, ς, φ)."""
    [declared] = risky_portfolio.builder.bwd["policy"].denote().doc
    assert isinstance(declared.statement, Member)
    maximization = declared.statement.set
    assert isinstance(maximization, Operator) and maximization.head == "argmax"
    [expectation] = maximization.args
    assert isinstance(expectation, Operator) and expectation.head == "E"
    assert [sub.name for sub in expectation.subs] == ["φ"]
    value = expectation.args[0]
    assert isinstance(value, Apply) and isinstance(value.args[0], Apply)
    objective_point = value.args[0].args[0]
    assert isinstance(objective_point, Tuple)
    assert [
        variable_identity(item).field
        if not isinstance(variable_identity(item), str)
        else variable_identity(item)
        for item in objective_point.items
    ] == ["w_d", "ς", "φ"]


def test_the_first_order_condition_of_a_portfolio_choice_reads_the_pullback(risky_portfolio):
    """The expectation of the first-order condition of the portfolio choice
    reads the output of its aggregation, which reads an output of the
    pullback of the continuation value."""
    backward = risky_portfolio.builder.bwd
    pullback = backward["policy", "Pullback"].denote()
    aggregation = backward["policy", "foc:Aggregation:1"].denote()
    foc = backward["policy", "foc:Expectation:1"].denote()
    assert aggregation.inputs[0].identity in {wire.identity for wire in pullback.outputs}
    assert foc.inputs[0].identity == aggregation.outputs[0].identity


def test_the_first_order_aggregation_multiplies_the_excess_return_the_state_and_the_marginal_value(
    risky_portfolio,
):
    """The aggregation of the first-order condition of the portfolio choice
    is (φ − R) · w_d · D_{k_next}V≻(𝑔(w_d, ς, φ)), reading the shock φ, the
    parameter R and the state w_d by their names."""
    aggregation = risky_portfolio.builder.bwd["policy", "foc:Aggregation:1"].denote()
    formula = aggregation.outputs[0].expression.body
    assert isinstance(formula, Mul) and isinstance(formula.left, Mul)
    assert isinstance(formula.left.left, Sub)
    assert variable_identity(formula.left.left.left).field == "φ"
    assert variable_identity(formula.left.left.right).field == "R"
    assert variable_identity(formula.left.right).field == "w_d"
    assert format_expression(formula.right, width=None) == "D_{k_next}V≻(𝑔(w_d, ς, φ))"


@pytest.mark.parametrize(
    ("target", "point", "value"),
    [
        # the arguments (w_d, ς, φ) = (2, 0.3, 1.2), then the parameter R =
        # 1.03: the law of motion (1.03 + 0.3 × (1.2 − 1.03)) × 2 = 2.162
        ("policy:Pullback", (2.0, 0.3, 1.2), 2.162),
        # the arguments (𝑉≻, w_d, ς, φ, D_{k_next}𝑉≻) = (0, 2, 0.3, 1.2, 4),
        # then R = 1.03: (φ − R) · w_d · D_{k_next}𝑉≻ = 0.17 × 2 × 4 = 1.36
        ("policy.foc:Aggregation:1", (0.0, 2.0, 0.3, 1.2, 4.0), 1.36),
    ],
    ids=["pullback", "first-order-aggregation"],
)
def test_a_policy_kernel_of_a_portfolio_choice_reads_the_share_and_gives_its_value_at_a_point(
    risky_portfolio, target, point, value
):
    """The kernel of a row of the policy builder of the portfolio choice
    takes the share ς among its arguments and gives its value at one point."""
    assert "ς" in [name for name, _ in kernel(risky_portfolio, target).arguments]
    values = kernel(risky_portfolio, target).parameter_values
    assert compile_kernel(risky_portfolio, target)(*point, *values) == pytest.approx(value)


def test_the_solve_of_the_first_order_condition_compiles_to_no_kernel(risky_portfolio):
    """`compile_kernel` refuses the aggregation that solves the first-order
    condition of the portfolio choice, since no side of its relation is an
    explicit function of its inputs."""
    with pytest.raises(ConstructionError, match="kernel") as refused:
        compile_kernel(risky_portfolio, "policy.foc:Aggregation")
    assert refused.value.rule == "kernel-target"


def test_the_pullback_at_the_policy_and_the_pullback_at_no_policy_differ_in_type(
    risky_portfolio,
):
    """The pullback of the decision builder of the portfolio choice, read at
    the policy ς, and the pullback of its policy builder, which keeps the
    share as a coordinate, have outputs of different types."""
    decision = risky_portfolio.builder.bwd["cntn_to_dcsn", "Pullback"].denote()
    policy = risky_portfolio.builder.bwd["policy", "Pullback"].denote()
    assert decision.outputs[0].mathematical_type != policy.outputs[0].mathematical_type


def test_the_listing_of_the_decision_builder_names_each_operation_and_its_output(
    cons_with_egm_lines,
):
    """The listing of the decision builder of `cons` with explicit policy
    lines prints each primitive under its kind and what it produces by name: a
    pullback that produces no named function, then an aggregation and an
    evaluation that produce 𝑉."""
    assert str(cons_with_egm_lines.builder.bwd["cntn_to_dcsn"].list()) == (
        "1  Pullback     primitive\n2  Aggregation  primitive  → 𝑉\n3  Evaluation   primitive  → 𝑉"
    )


def test_the_listing_of_the_policy_builder_of_cons_begins_with_the_inverse_euler_row(
    cons_with_egm_lines,
):
    """The first entry of the listing of the policy builder of `cons` with
    explicit policy lines is the inverse Euler aggregation, a primitive that
    produces the candidate 𝑐≻."""
    listing = cons_with_egm_lines.builder.bwd["policy"].list()
    assert listing.entries[0][:4] == (
        "InvEuler:Aggregation",
        "policy.InvEuler:Aggregation",
        "primitive",
        "𝑐≻",
    )


def test_the_listing_of_the_policy_builder_numbers_its_entries_from_one(cons_with_egm_lines):
    """The listing of the policy builder of `cons` with explicit policy lines
    numbers its entries from one, in order."""
    listing = cons_with_egm_lines.builder.bwd["policy"].list()
    assert len(listing) > 0
    assert [entry.number for entry in listing.entries] == list(range(1, len(listing) + 1))


def test_the_forward_push_forward_reads_the_policy_and_the_law_of_motion_by_identity(cons):
    """The push-forward of the forward decision builder of `cons` reads the
    policy and the law of motion by identity, with no abbreviation of either
    and no unresolved reference."""
    push_forward = cons.dcsn.builder.fwd["Pushforward"].denote()
    identities = {str(identity) for identity in free_identities(push_forward.expression)}
    assert {"cons:function:dcsn:c", "cons:g:dcsn_to_cntn"} <= identities
    assert not any(":alias:" in identity for identity in identities)
    assert push_forward.where == ()
    assert "UNRESOLVED" not in str(push_forward.expression)


def test_the_push_forward_gives_an_event_the_measure_of_its_preimage(cons):
    """The push-forward of `cons` states, in its rule and on its card, that an
    event has the measure of its preimage under the law of motion at the
    policy, written with no indicator function and no measurable set."""
    push_forward = cons.dcsn.builder.fwd["Pushforward"].denote()
    [rule] = push_forward.outputs[0].rules
    assert rule_text(rule) == "μ≻(B) = μ({m_d ∈ Xm | 𝑔(m_d, c(m_d)) ∈ B})"
    assert "μ≻(B) = μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})" in str(push_forward)
    assert "indicator" not in str(push_forward) and "measurable-set" not in str(push_forward)


def test_the_state_choice_measure_reads_the_policy_by_identity(cons):
    """The joint measure of the decision state and the control that the
    forward decision builder of `cons` gives, `state_choice_measure()`, reads
    the policy by identity, with no unresolved reference."""
    choice = cons.dcsn.builder.fwd.state_choice_measure()
    assert "cons:function:dcsn:c" in {str(identity) for identity in free_identities(choice)}
    assert "UNRESOLVED" not in str(choice)


@pytest.fixture(scope="module")
def cons_without_the_doc_line(cons_with_egm_lines_text):
    """The stage of `cons` with explicit policy lines and with its `!doc`
    line removed."""
    return stage_from_text(
        cons_with_egm_lines_text.replace(ARGMAX_DOC_LINE, ""), "without_documentation.bl"
    )


def test_the_doc_line_changes_neither_the_inputs_nor_the_rule_of_the_identification(
    cons_with_egm_lines_text, cons_with_egm_lines, cons_without_the_doc_line
):
    """The identification of the policy builder of `cons` with explicit
    policy lines reads the same two inputs, the candidate 𝑐≻ and the
    coordinate map 𝑚_d≻, and declares the same one rule, with the `!doc` line
    and without it."""
    assert cons_with_egm_lines_text.count(ARGMAX_DOC_LINE) == 1
    documented = cons_with_egm_lines.builder.bwd["policy", "cons_choice:Pullback"].denote()
    undocumented = cons_without_the_doc_line.builder.bwd["policy", "cons_choice:Pullback"].denote()
    assert len(documented.inputs) == 2
    assert documented.inputs == undocumented.inputs
    assert documented.outputs[0].rules == undocumented.outputs[0].rules
    assert len(documented.outputs[0].rules) == 1


def test_the_doc_line_changes_the_set_of_the_output_of_the_identification(
    cons_with_egm_lines, cons_without_the_doc_line
):
    """The output of the identification of the policy builder of `cons` with
    explicit policy lines lies in another set with the `!doc` line than
    without it."""
    documented = cons_with_egm_lines.builder.bwd["policy", "cons_choice:Pullback"].denote()
    undocumented = cons_without_the_doc_line.builder.bwd["policy", "cons_choice:Pullback"].denote()
    assert format_expression(
        documented.outputs[0].mathematical_type.carrier, width=None
    ) != format_expression(undocumented.outputs[0].mathematical_type.carrier, width=None)


def test_the_evaluation_of_the_policy_builder_of_cons_carries_the_set_its_doc_line_declares(
    cons_with_egm_lines,
):
    """The evaluation of the policy builder of `cons` with explicit policy
    lines places the policy in the set of policies whose values lie in
    Γ(m_d), the set that the binder of its `!doc` line declares."""
    policy = cons_with_egm_lines.builder.bwd["policy"]
    carrier = policy["Evaluation"].denote().outputs[0].mathematical_type.carrier
    assert format_expression(carrier, width=None) == "𝒫({c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)})"


def test_the_decision_builder_is_at_the_policy(cons):
    """The decision builder of `cons` is at the policy 𝑐, typed as the policy
    builder types it, as the set of policies whose value lies in Γ(m_d)."""
    record = cons.builder.bwd["cntn_to_dcsn"].denote()
    [at] = record.at
    assert at.symbol == "𝑐" and str(at.identity) == "cons:function:dcsn:c"
    assert format_expression(at.mathematical_type.carrier, width=None) == (
        "{c ∈ (Xm → ℝ₊₊) | c(m_d) ∈ Γ(m_d)}"
    )


def test_the_decision_builder_defines_no_abbreviation_of_the_law_at_the_policy(cons):
    """The decision builder of `cons` defines no abbreviation of the law of
    motion or of the aggregator at the policy: its record has no `where`
    entry and its card no `Where` section."""
    builder = cons.builder.bwd["cntn_to_dcsn"]
    record = builder.denote()
    assert record.at != ()
    assert record.where == ()
    printed = str(builder)
    assert "Where" not in printed


def test_the_pullback_of_the_decision_builder_writes_out_the_law_at_the_policy(cons):
    """The pullback of the decision builder of `cons` composes 𝑉≻ with the
    law of motion at the policy written out as a map of the point,
    `m_d ↦ 𝑔(m_d, c(m_d))`, and its rule reads the composite written out."""
    pullback = cons.builder.bwd["cntn_to_dcsn"]["Pullback"].denote()
    composite = pullback.outputs[0].expression
    assert isinstance(composite, Compose) and isinstance(composite.inner, Lambda)
    assert format_expression(composite.inner.body, width=None) == "𝑔(m_d, c(m_d))"
    assert format_expression(composite, width=None) == "V≻ ∘ 𝑔(·, c)"
    [rule] = pullback.outputs[0].rules
    assert rule_text(rule) == "(V≻ ∘ 𝑔(·, c))(m_d) = V≻(𝑔(m_d, c(m_d)))"


def test_the_aggregation_of_the_decision_builder_reads_the_law_at_the_policy(cons):
    """The aggregation of the decision builder of `cons` is the map
    `m_d ↦ 𝑢(c(m_d)) + V≻(𝑔(m_d, c(m_d)))`."""
    aggregation = cons.builder.bwd["cntn_to_dcsn"]["Aggregation"].denote()
    assert format_expression(aggregation.outputs[0].expression, width=None) == (
        "m_d ↦ 𝑢(c(m_d)) + V≻(𝑔(m_d, c(m_d)))"
    )


@pytest.mark.parametrize(
    "line",
    [
        "     in: 𝑉≻                             out: 𝑉≻ ∘ 𝑔≻(·, 𝑐)",
        "     rule: (𝑉≻ ∘ 𝑔≻(·, 𝑐))(m_d) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))",
        "     rule: 𝑉(m_d) = 𝑢(𝑐(m_d)) + 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))",
    ],
    ids=["pullback-input-and-output", "pullback-rule", "aggregation-rule"],
)
def test_the_card_of_the_decision_builder_writes_out_the_law_at_the_policy(cons, line):
    """The card of the decision builder of `cons` writes the law of motion at
    the policy out on the line of the pullback's input and output and in the
    rules of the pullback and of the aggregation."""
    printed = str(cons.builder.bwd["cntn_to_dcsn"])
    assert line in printed.splitlines()


def test_the_forward_decision_builder_defines_no_abbreviation_of_the_law_at_the_policy(cons):
    """The record of the forward builder of `cons` from the decision perch
    has no `where` entry."""
    forward = cons.builder.fwd["dcsn_to_cntn"].denote()
    assert forward.at != ()
    assert forward.where == ()


def test_the_forward_decision_builder_is_at_the_policy_of_the_backward_one(cons):
    """The forward builder of `cons` from the decision perch is at the same
    policy as the backward decision builder."""
    record = cons.builder.bwd["cntn_to_dcsn"].denote()
    forward = cons.builder.fwd["dcsn_to_cntn"].denote()
    assert record.at != ()
    assert forward.at == record.at


def test_the_pullback_of_port_opens_each_coordinate_of_its_point(port):
    """The card of the pullback of the decision builder of `port` opens each
    coordinate of its point and puts the policy 𝜍 where the law of motion
    reads the control, read at the saving alone."""
    printed = str(port.builder.bwd["cntn_to_dcsn"]["Pullback"])
    assert "  out  𝑉≻ ∘ 𝑔≻(·, 𝜍, ·, ·)" in printed.splitlines()
    assert "  (𝑉≻ ∘ 𝑔≻(·, 𝜍, ·, ·))(k_d, Ψ, θ) = 𝑉≻(𝑔≻(k_d, 𝜍(k_d), Ψ, θ))" in printed.splitlines()


# a law of motion or an aggregator named at the policy by a perch mark
# followed directly by a comma and the policy, a form the package does not
# print
PERCH_MARK_AND_COMMA = re.compile(r"[≺≻],[^\s]")


@pytest.mark.parametrize("name", ["cons", "port"])
def test_no_printed_surface_names_the_law_at_the_policy_by_a_perch_mark_and_a_comma(request, name):
    """No card, listing, signature or drawing of a stage names a law of
    motion or an aggregator at the policy by a perch mark followed directly
    by a comma."""
    stage = request.getfixturevalue(name)
    texts = [text for _, text, _ in PrintedStage(stage)]
    for graph in (stage.builder.bwd, stage.builder.fwd):
        texts += [graph.diagram().source, graph.primitives.diagram().source]
        for builder_name in graph.list():
            builder = graph[builder_name]
            texts += [
                str(builder.signature()),
                str(builder.primitives.list()),
                builder.diagram().source,
            ]
            texts += [
                str(builder.primitives[key].signature()) for key in builder.primitives.list()
            ]
    found = [match.group(0) for text in texts for match in PERCH_MARK_AND_COMMA.finditer(text)]
    assert found == [], (stage.name, found[:6])


def test_the_signature_of_the_decision_pullback_writes_the_law_with_a_dot(cons):
    """The signature of the pullback of the decision builder of `cons` writes
    its output as the law of motion at the policy with a dot for the point
    left open, `𝑉≻∘𝑔(·, 𝑐)`."""
    pullback = str(cons.builder.bwd["cntn_to_dcsn"]["Pullback"].signature())
    assert "𝑉≻∘𝑔(·, 𝑐) : Xm → [−∞, ∞)" in pullback


@pytest.mark.parametrize(
    ("name", "direction", "label"),
    [
        ("cons", "bwd", "𝑉≻ ∘ 𝑔(·, 𝑐)"),
        ("cons", "bwd", "𝐺(·, ·, 𝑐)"),
        ("cons", "bwd", "𝑉≻(𝑔(m_d,\\n𝑐(m_d)))"),
        ("cons", "fwd", "𝑔(·, 𝑐)∗μ"),
        ("port", "bwd", "𝑉≻ ∘ 𝑔(·, 𝜍, ·, ·)"),
        ("port", "bwd", "𝐺(·, ·, 𝜍)"),
    ],
    ids=[
        "cons-backward-pulled-back-value",
        "cons-backward-aggregator",
        "cons-backward-value-at-the-point-wrapped",
        "cons-forward-push-forward",
        "port-backward-pulled-back-value",
        "port-backward-aggregator",
    ],
)
def test_a_drawing_labels_a_wire_with_the_policy_where_the_law_or_aggregator_reads_the_control(
    request, name, direction, label
):
    """A drawing of a builders graph labels a wire with the law of motion or
    the aggregator at the policy, the policy standing where it reads the
    control and a dot for each argument left open, or with the pulled-back
    value read at the point, wrapped at the width of a wire's label."""
    graph = getattr(request.getfixturevalue(name).builder, direction)
    assert f'label="{label}"' in graph.diagram().source


def test_the_doc_line_of_cons_forms_no_operation_of_its_policy_builder(cons_with_egm_lines):
    """The policy builder of `cons` with explicit policy lines, whose
    maximization is marked `!doc`, lists its inverse Euler and grid
    aggregations, its identification and its evaluation, and no `Argmax` and
    no pullback or aggregation that would serve one."""
    assert list(cons_with_egm_lines.builder.bwd["policy"].primitives.list()) == [
        "InvEuler:Aggregation",
        "endoggrid:Aggregation",
        "cons_choice:Pullback",
        "Evaluation",
    ]


@pytest.mark.parametrize(
    "name", ["port", "risky_portfolio"], ids=["port", "the-portfolio-choice-with-one-risky-asset"]
)
def test_the_doc_line_of_a_portfolio_choice_forms_no_operation_of_its_policy_builder(
    request, name
):
    """The policy builder of a portfolio choice lists the operations of its
    first-order condition and its evaluation alone, and none for the
    maximization and the expectation that its `!doc` line writes."""
    keys = request.getfixturevalue(name).builder.bwd["policy"].primitives.list()
    assert list(keys) == [
        "Pullback",
        "foc:Aggregation:1",
        "foc:Expectation:1",
        "foc:Aggregation",
        "Evaluation",
    ]


def test_the_policy_builder_holds_its_doc_line_with_its_source(cons_with_egm_lines):
    """The policy builder of `cons` with explicit policy lines holds its
    `!doc` line under `doc`, with the line's address, its mark and its text as
    the file writes it."""
    [declared] = cons_with_egm_lines.builder.bwd["policy"].denote().doc
    assert declared.source.address == "policy.optimality" and declared.source.doc
    assert declared.source.text.startswith("c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])")


@pytest.mark.parametrize(
    ("name", "statement"),
    [
        ("cons_with_egm_lines", "c(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + V≻(𝑔(m_d, cp))]"),
        ("port", "ς(k_d) ∈ argmax_{ς ∈ Γ_ς(k_d)} [E_{Ψ, θ}[V≻(𝑔(k_d, ς, Ψ, θ))]]"),
        (
            "adjuster_cons_with_egm_lines",
            "(c(m, z_d), h_choice(m, z_d)) ∈ argmax_{c ∈ Γ_c(m), h_choice ∈ Γ_h(m − c)}"
            " [𝑢(c, h_choice) + β · V≻(𝑔(m, z_d, c, h_choice))]",
        ),
    ],
    ids=["cons", "port", "adjuster_cons_with_egm_lines"],
)
def test_the_doc_statement_writes_the_maximization_at_the_constructed_output(
    request, name, statement
):
    """The policy builder holds the statement of its `!doc` line with the
    constructed output substituted, an expectation as the file writes it,
    and a joint choice by its components and its correspondences at the
    file's arguments."""
    [declared] = request.getfixturevalue(name).builder.bwd["policy"].denote().doc
    assert format_expression(declared.statement, width=None) == statement


def test_the_printed_obligations_of_cons_name_no_maximisers_and_no_solutions(cons_with_egm_lines):
    """The printed obligations of `cons` with explicit policy lines name no
    `maximisers` and no `solutions of` a condition, words that the package
    does not print, since it states no obligation that a maximization be
    optimal."""
    listing = str(cons_with_egm_lines.obligations())
    assert "maximisers" not in listing and "solutions of" not in listing


def test_no_condition_of_the_policy_builder_of_cons_or_of_its_identification_is_optimality(
    cons_with_egm_lines,
):
    """No condition that the policy builder of `cons` with explicit policy
    lines or its identification states has the name `optimality`."""
    policy = cons_with_egm_lines.builder.bwd["policy"]
    assert "optimality" not in {item.condition for item in policy.denote().conditions}
    assert "optimality" not in {
        item.condition for item in policy["cons_choice:Pullback"].denote().conditions
    }


# the grid line and the law of motion of the inverse Euler form of the
# consumption stage, `INVERSE_EULER`, whose policy block writes the grid line
# `m[>] = a + c[>]`
INVERSE_EULER_GRID_LINE = "    m[>] = a + c[>]        :: [id=grid]"
INVERSE_EULER_LAW = "    a = m - c\n"


def changed_grid_line(right):
    """The change of the grid line of the inverse Euler form to the line
    whose right side is `right`, as a pair of the line written and the line
    that replaces it."""
    return (INVERSE_EULER_GRID_LINE, f"    m[>] = {right}    :: [id=grid]")


def with_changes(text, changes):
    """`text` with each pair `(line written, line that replaces it)` of
    `changes` applied in order."""
    for written, changed in changes:
        text = text.replace(written, changed)
    return text


@pytest.fixture(scope="module")
def inverse_euler_text():
    """The inverse Euler form of the consumption stage, `INVERSE_EULER`."""
    return INVERSE_EULER


@pytest.fixture(scope="module")
def adjuster_text():
    """The text of the stage file of the durables adjuster whose policy block
    holds lines of the endogenous grid method and whose law of motion has
    several outputs."""
    return (ROOT / ADJUSTER_CONS_WITH_EGM_LINES_FILE).read_text(encoding="utf-8")


# the grid line of the durables adjuster as its stage file writes it
ADJUSTER_GRID_LINE = "m[>]          = a_nxt_adj + c[>] + (1 + τ)*h_nxt_adj"


# Each row: the fixture of the text, its changes, and either the name of the
# stage that the changed text elaborates to, `t` for the inverse Euler form,
# or the address of the refusal with the phrases of its message.
GRID_LINES = [
    pytest.param(
        "inverse_euler_text",
        (changed_grid_line("c[>] + a"),),
        "t",
        None,
        id="a-sum-in-another-order",
    ),
    pytest.param(
        "inverse_euler_text",
        (changed_grid_line("(a + c[>])*1"),),
        "t",
        None,
        id="a-product-with-one",
    ),
    pytest.param(
        "inverse_euler_text",
        (changed_grid_line("2*(a + c[>]) - a - c[>]"),),
        "t",
        None,
        id="a-sum-whose-terms-cancel",
    ),
    # a decimal literal is read as the rational number its spelling denotes,
    # so that 0.9 and 10/9 are reciprocal in the comparison
    pytest.param(
        "inverse_euler_text",
        (changed_grid_line("10*a/9 + c[>]"), (INVERSE_EULER_LAW, "    a = 0.9*(m - c)\n")),
        "t",
        None,
        id="a-decimal-literal-in-the-law-of-motion",
    ),
    # a grid line that agrees with the law of motion only under an identity
    # among declared functions is refused, and the message says so
    pytest.param(
        "inverse_euler_text",
        (changed_grid_line("a + 𝑑𝑢𝑖𝑛𝑣(𝑑𝑢(c[>]))"),),
        None,
        (
            "policy.grid",
            (
                "the grid line m[>] = a + 𝑑𝑢𝑖𝑛𝑣(𝑑𝑢(c[>]))",
                "the law of motion gives m[>] = a + c[>]",
                "it applies the functions 𝑑𝑢, 𝑑𝑢𝑖𝑛𝑣",
                "assumes no identity",
            ),
        ),
        id="refused-an-identity-of-declared-functions",
    ),
    pytest.param(
        "inverse_euler_text",
        (changed_grid_line("a + 2*c[>]"),),
        None,
        (
            "policy.grid",
            (
                "the grid line m[>] = a + 2*c[>]",
                "the law of motion gives m[>] = a + c[>]",
                "does not reduce to",
            ),
        ),
        id="refused-a-candidate-doubled",
    ),
    # a law of motion with several outputs is solved through its other lines:
    # the housing line gives the control without a candidate
    pytest.param("adjuster_text", (), "adjuster_cons", None, id="a-law-of-several-outputs"),
    pytest.param(
        "adjuster_text",
        ((ADJUSTER_GRID_LINE, "m[>]          = a_nxt_adj + c[>] + h_nxt_adj         "),),
        None,
        (
            "policy.endoggrid",
            (
                "the grid line m[>] = a_nxt_adj + c[>] + h_nxt_adj",
                "its lines a_nxt_adj = m - c - (1 + τ)*h_choice and h_nxt_adj = h_choice "
                "solved for m and h_choice at the candidate c[>]",
                "the law of motion gives m[>] = a_nxt_adj + c[>] + (1 + τ)*h_nxt_adj",
                "does not reduce to",
            ),
        ),
        id="refused-a-term-left-out-of-a-law-of-several-outputs",
    ),
    pytest.param(
        "cons_obs_file_text", (), "cons_obs", None, id="the-grid-line-of-the-stage-file-cons_obs"
    ),
]


@pytest.mark.parametrize(("text", "changes", "name", "refusal"), GRID_LINES)
def test_a_grid_line_is_accepted_only_where_the_solved_law_of_motion_gives_it(
    request, text, changes, name, refusal
):
    """A grid line whose right side reduces, by algebraic simplification, to
    the law of motion solved for the decision state at the candidates is
    accepted however it is spelled, and any other grid line is refused under
    `grid-line-consistency` with a message that names the line and the
    solved law."""
    written = request.getfixturevalue(text)
    assert [line for line, _ in changes if written.count(line) != 1] == []
    changed = with_changes(written, changes)
    if refusal is None:
        assert stage_from_text(changed).name == name
        return
    address, phrases = refusal
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(changed)
    assert (refused.value.rule, refused.value.address) == ("grid-line-consistency", address)
    assert [phrase for phrase in phrases if phrase not in refused.value.message] == []


def test_a_law_of_motion_that_is_not_affine_in_the_decision_state_is_not_solved():
    """A law of motion in which the decision state occurs other than once and
    affinely is not solved, so the grid line is not checked and no kind of
    condition is added in the place of the check."""
    changes = (changed_grid_line("a + 5*c[>]"), (INVERSE_EULER_LAW, "    a = m*m - c\n"))
    assert [line for line, _ in changes if INVERSE_EULER.count(line) != 1] == []
    unsolved = stage_from_text(with_changes(INVERSE_EULER, changes))
    assert {item.condition for item in unsolved.obligations()} == {
        item.condition for item in stage_from_text(INVERSE_EULER).obligations()
    }


# a policy block whose one operative statement, the first-order condition,
# has two unknowns, c and h: one equation cannot determine two unknowns, and
# the refusal names both counts and the spelling `solve_{…}`
ONE_STATEMENT_IN_TWO_UNKNOWNS = """@stage: two

Xa := ℝ₊₊

β : (0,1)
γ : (1, inf)

𝑢(c : ℝ₊₊) := c^(1-γ)/(1-γ)
𝑑𝑢(c : ℝ₊₊) := c^(-γ)
Γ(m : ℝ₊₊) := (0, m]

[id=arvl_to_dcsn, (m : ℝ₊₊) : !arvl -> (m_d : ℝ₊₊) : !dcsn] {
    m_d = m
}

[id=dcsn_to_cntn, (m_d, c : ℝ₊₊ @ !ctrl, h : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m_d - c - h
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c, h) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + 𝑢(h) + β*V[>]
}

[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl, h : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(m_d)}(𝑢(c) + β*V[>])   :: [id=optimality, !doc]
    𝑑𝑢(c) + 𝑑𝑢(h) = β*D_{a}V[>]              :: [id=euler]
}
"""


def test_a_system_with_fewer_statements_than_unknowns_is_refused():
    """A system of one statement in the two unknowns `c` and `h` is refused,
    and the refusal names both counts and the spelling `solve_{…}`."""
    # the one equation of the block mentions the two outputs c and h and no
    # other statement defines either, so the system has one statement and two
    # unknowns and determines neither
    with pytest.raises(ConstructionError) as refused:
        stage_from_text(ONE_STATEMENT_IN_TWO_UNKNOWNS, "two.bl")
    error = refused.value
    assert (error.rule, error.address) == ("not-constructed", "policy.euler")
    assert "1 statement of builder 'policy' (policy.euler) states" in error.message
    assert "a relation in 2 unknowns (c, h)" in error.message
    assert "`c, h = solve_{c, h}(…)`" in error.message
