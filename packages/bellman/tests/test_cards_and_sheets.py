"""The printed forms of a stage: its sheet, the cards of its pieces, the short
forms of its handles, the printing of terms with precedence and brackets, and
the breaking of long lines within the width of a card."""

import gc
import weakref

import pytest
from application_files import (
    COPIED_FILES_FOLDER,
    FIRST_CALIBRATIONS,
    METHODS_SOURCES_BY_STAGE,
    PORT_METHODS,
    ROOT,
    SETTINGS_SOURCES_BY_STAGE,
    stage_file_id,
)
from discopy.frobenius import Spider
from printed_text import WIDTH, PrintedStage, cards_of_every_handle, parse_every_sheet, split_sets
from snapshot.record import ELABORATED_FILES
from stage_builders import corpus_stage, name_term, stage_from_text
from stage_texts import changed, corpus_text, two_nodes_text_with_changes
from two_sets import one_row_by_default

from bellman.native import predicates
from bellman.native.hypergraphs import copy_native
from bellman.refusals import NotConstructed, TargetError
from bellman.stage import denotations
from bellman.syntax import layout, terms
from bellman.syntax.lower import parse_with_spans
from bellman.typing import typed_expressions


def sheet_sections(text):
    """The sections of a sheet by their labels, each with its lines that are
    not blank: a section opens at a line at column zero that holds a hairline
    or a dashed rule and is not the heavy line under the title."""
    found, label = {}, None
    for line in text.splitlines():
        if (
            line
            and not line.startswith(" ")
            and ("─" in line or "┄" in line)
            and not line.startswith("━")
        ):
            label = line.split("─")[0].split("┄")[0].strip()
            found[label] = []
        elif label is not None:
            found[label].append(line)
    return {label: [line for line in lines if line.strip()] for label, lines in found.items()}


def headings_of(card):
    """The headings of the sections of a card in their order: the words before
    two spaces of each line at column zero under the title, apart from the
    heavy and the light line."""
    return [
        line.split("  ")[0]
        for line in card.splitlines()[1:]
        if line and not line[0].isspace() and line[0] not in "━─"
    ]


def declared_and_initial_cards(stage):
    """The cards of a stage that no binding changes, by kind: the card of each
    declared builder by its pair of perches, of each block of the two initial
    diagrams, of each line of those blocks, and of the two initial
    diagrams."""
    diagrams = {"backward": stage.initial.backward, "forward": stage.initial.forward}
    return {
        "declared builders": {
            pair: str(handle.denote()) for pair, handle in stage.declared.items()
        },
        "blocks": {
            (direction, block): str(diagram[block].denote())
            for direction, diagram in diagrams.items()
            for block in diagram.list().names
        },
        "lines": {
            (direction, block, line): str(diagram[block][line].denote())
            for direction, diagram in diagrams.items()
            for block in diagram.list().names
            for line in diagram[block].list().names
        },
        "initial diagrams": [str(diagram.denote()) for diagram in diagrams.values()],
    }


# The handles through which the printed text of a stage holds the card of a
# primitive, of a sub-builder and of a line.
THROUGH_PRIMITIVES = "builder.primitives[key]"


THROUGH_SUB_BUILDERS = "builder.sub_builders[key]"


THROUGH_DEFINITIONS = "stage.definitions.denote(identity)"


def title_of(*keys):
    """The title of a piece reached by `keys`, one key or a tuple of keys for
    each level, joined with ` / ` as the printed text joins them."""
    flat = []
    for key in keys:
        flat += list(key) if isinstance(key, tuple) else [key]
    return " / ".join(flat)


def builder_cards(direction, name, builder):
    """`(title, handle, card, other handle, other card)` for each piece of
    one builder that a second handle reaches, `builder` being the builder's
    handle: each primitive and each sub-builder that `builder.list()` gives,
    through `builder[key]`, and each primitive that
    `builder.sub_builders.list()` gives, through `builder.sub_builders[key]`.
    The other card is that of the piece of the same whole name through
    `builder.primitives` or, for a sub-builder, through
    `builder.sub_builders`; it is None when no piece of that name stands
    there."""
    opened, sub_builders = builder.primitives, builder.sub_builders
    stored = {entry.name: str(opened[entry.key]) for entry in opened.list().entries}
    stored_sub_builders = {
        entry.name: str(sub_builders[entry.key])
        for entry in sub_builders.list().entries
        if entry.kind == "sub-builder"
    }
    for handle, reached in (("builder[key]", builder), (THROUGH_SUB_BUILDERS, sub_builders)):
        for entry in reached.list().entries:
            title = f"{direction} {title_of(name, entry.key)}"
            if entry.kind == "primitive":
                other = stored.get(entry.name)
                yield title, handle, str(reached[entry.key]), THROUGH_PRIMITIVES, other
            elif entry.kind == "sub-builder" and reached is builder:
                other = stored_sub_builders.get(entry.name)
                yield title, handle, str(reached[entry.key]), THROUGH_SUB_BUILDERS, other


def line_cards(stage, direction, block, keys):
    """`(title, handle, card, other handle, other card)` for each line that
    the block `block` lists, and that each block it lists lists in turn,
    through `block[key]`, with the card of the line's definition, read by
    the line's whole name, as the other card; `keys` are the keys that reach
    `block` from the initial diagram. For a line that reads no wire the
    package makes one record, which both handles reach, so that the two
    cards of such a line are one computation printed twice."""
    for entry in block.list().entries:
        title = f"initial {direction} {title_of(*keys, entry.key)}"
        if entry.kind == "line":
            other = str(stage.definitions.denote(entry.name))
            yield title, "block[key]", str(block[entry.key]), THROUGH_DEFINITIONS, other
        elif entry.kind == "block":
            yield from line_cards(stage, direction, block[entry.key], keys + (entry.key,))


def cards_through_two_handles(stage):
    """`(title, handle, card, other handle, other card)` for each piece of
    `stage` that two handles reach: the pieces of each builder of the two
    builders graphs, as `builder_cards` gives them, and the lines of each
    block of the two initial diagrams, as `line_cards` gives them. The other
    handle is the one through which the printed text of the stage holds the
    piece's card. A graph whose construction is refused gives no piece."""
    for direction, graph in (("backward", stage.builder.bwd), ("forward", stage.builder.fwd)):
        try:
            names = graph.list()
        except NotConstructed:
            continue
        for name in names:
            yield from builder_cards(direction, name, graph[name])
    for direction, diagram in (
        ("backward", stage.initial.backward),
        ("forward", stage.initial.forward),
    ):
        try:
            blocks = diagram.list()
        except NotConstructed:
            continue
        for block in blocks:
            yield from line_cards(stage, direction, diagram[block], (block,))


def pieces_with_two_cards(cards):
    """Each piece among `cards`, given as `cards_through_two_handles` yields
    them, whose card through one handle differs from its card through the
    other. The package reads the boxes of one name at several places as one
    piece when they are equal, reads the box of a line in an initial diagram
    as the record of the line that the box displays, and titles a builder's
    piece by the pair of perches that the builder joins, whatever handle
    reached the piece."""
    return [
        f"{title}: the card through {handle} differs from the card through {other_handle}"
        for title, handle, printed, other_handle, other in cards
        if printed != other
    ]


@pytest.fixture(scope="module")
def retire():
    """The stage of `retire.bl` of the model of Gourinchas and Parker (2002),
    a terminal stage with no continuation perch whose two initial diagrams
    and two builders graphs are refused under the rule `not-constructed`."""
    path = f"{COPIED_FILES_FOLDER}/gourinchas-parker-2002/retire.bl"
    return stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)


@pytest.fixture(scope="module")
def specified_sheet(cons_configured):
    """The sheet of `cons` bound by the calibration, the methods file and the
    settings of its application."""
    return str(cons_configured)


@pytest.fixture(scope="module")
def bindings_section(specified_sheet):
    """The lines of the section `BINDINGS` of the sheet of the specified
    `cons`."""
    return sheet_sections(specified_sheet)["BINDINGS"]


@pytest.fixture(scope="module")
def long_aggregation():
    """The aggregation of the backward builder `cntn_to_dcsn` of the two-node
    stage `TWO_NODES` of `bellman/refusal_examples.py`, whose state is k,
    whose control c lies in [0, 1] and whose shocks y and z are normal, here
    with the one value line `V = E_{y,z}(β*V[>]*(c*y + (1-c)*R + z))`. The
    line reads the control, so that the input and the output of the
    signature of the aggregation are too wide for one line of its card."""
    stage = stage_from_text(
        two_nodes_text_with_changes(
            backward="    V = E_{y,z}(β*V[>]*(c*y + (1-c)*R + z)) :: [id=value]\n",
            header="(V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
        ),
        "t.bl",
    )
    return stage.builder.bwd.primitives["cntn_to_dcsn.value:Aggregation:1"]


@pytest.fixture(scope="module")
def decision_builder_of_cons(cons):
    """The decision builder `cntn_to_dcsn` of the backward builders graph of
    `cons`."""
    return cons.builder.bwd["cntn_to_dcsn"]


@pytest.fixture(scope="module")
def backward_builders_graph_of_cons(cons):
    """The backward builders graph of `cons`."""
    return cons.builder.bwd


@pytest.fixture(scope="module")
def keep_branch_of_tenure(tenure):
    """The branch `keep` of the block `dcsn_to_cntn` of the forward initial
    diagram of `tenure`."""
    return tenure.initial.forward["dcsn_to_cntn"]["dcsn_to_cntn.keep"]


@pytest.fixture(scope="module")
def decision_builder_of_sa_savings(sa_savings):
    """The decision builder `cntn_to_dcsn` of the backward builders graph of
    `sa_savings`, whose operations hold the sub-builder `risk_ce`."""
    return sa_savings.builder.bwd["cntn_to_dcsn"]


@pytest.fixture(scope="module")
def policy_card_of_cons(cons_methodized):
    """The card of the policy builder of `cons`, calibrated and bound with
    its addition, the methods file of its application."""
    return str(cons_methodized.builder.policy.denote())


@pytest.fixture(scope="module")
def decision_card_of_port(port):
    """The card of the decision builder of a copy of `port` bound with its
    methods file, which types value function iteration on the builder, a
    quadrature with keyword arguments on its expectation and a
    representation on its Evaluation."""
    return str(copy_native(port).methodize(str(PORT_METHODS)).builder["cntn", "dcsn"].denote())


@pytest.fixture(scope="module")
def stage_with_a_union_and_a_difference():
    """The stage of `cons_obs.bl` with ρ declared in a union and a parameter
    σ declared in a difference."""
    text = changed(
        corpus_text("cons_obs"), ("ρ : [1, inf)\n", "ρ : (0,1) \\/ (1, inf)\nσ : ℝ₊₊ \\ {1}\n")
    )
    return stage_from_text(text, "cons_obs.bl")


@pytest.fixture(scope="module")
def cards_of_the_stage_with_a_union_and_a_difference(stage_with_a_union_and_a_difference):
    """The text of each card that the printed text of
    `stage_with_a_union_and_a_difference` holds, by its title."""
    printed = PrintedStage(stage_with_a_union_and_a_difference)
    return {title: text for title, text, _ in printed.cards}


def test_a_stage_whose_graphs_are_refused_prints_its_sheet_within_the_width_with_the_refusal(
    retire,
):
    """The sheet of `retire.bl`, whose four graphs are refused, prints within
    the width and states the refusal under the rule `not-constructed`."""
    text = str(retire)
    assert max(len(line) for line in text.splitlines()) <= WIDTH
    assert "refused under not-constructed" in text


def test_the_card_of_a_refused_initial_diagram_states_the_refusal_and_its_source(retire):
    """Once the sheet of `retire.bl` is printed, the card of its refused
    backward initial diagram names the file once, in its `Source` section,
    and gives the rule, the line and the name of the block, and the reason
    of the refusal."""
    # the premise: the sheet is printed first, and printing it must leave
    # the refused diagram as it was
    str(retire)
    diagram = str(retire.initial.backward)
    flat = " ".join(diagram.split())
    assert diagram.splitlines()[0] == "STAGE retire / BACKWARD INITIAL DIAGRAM"
    assert "\nSource  retire.bl\n" in diagram
    assert diagram.count("retire.bl") == 1
    assert "rule not-constructed" in flat and " 24 cntn_to_dcsn " in flat
    assert (
        "no rule assigns this block to the backward or the forward initial diagram: "
        "its output roles and its declared input and output perches match none"
    ) in flat


@pytest.mark.parametrize("verb", ["list", "signature"])
def test_a_verb_of_a_refused_initial_diagram_raises_the_refusal_that_it_holds(retire, verb):
    """Once the sheet of `retire.bl` is printed, the verb `list` or
    `signature` of its refused backward initial diagram raises the refusal
    under the rule `not-constructed`."""
    # the premise: the sheet is printed first, and printing it must leave
    # the refused diagram as it was
    str(retire)
    with pytest.raises(NotConstructed) as refusal:
        getattr(retire.initial.backward, verb)()
    assert refusal.value.rule == "not-constructed"


def test_the_view_of_a_stage_is_its_printed_text(cons):
    """`stage.view()` answers the text that `str(stage)` prints."""
    assert cons.view() == str(cons)


@pytest.mark.parametrize(
    ("version", "stamp"),
    [
        pytest.param("cons_calibrated", "[VERSION = CALIBRATED]", id="calibrated"),
        pytest.param("cons_methodized", "[VERSION = METHODIZED]", id="calibrated-and-methodized"),
        pytest.param("cons_configured", "[VERSION = SPECIFIED]", id="bound-by-the-three-verbs"),
        pytest.param(
            "cons_methodized_without_calibration", "[VERSION = METHODS]", id="methodized-alone"
        ),
    ],
)
def test_the_first_line_of_a_sheet_names_the_version_of_the_stage(request, version, stamp):
    """The first line of the sheet of a version of `cons` ends with its
    version: the last verb where the bindings follow the order calibration,
    methodization, configuration from its start, and the bindings present
    otherwise."""
    assert str(request.getfixturevalue(version)).splitlines()[0].endswith(stamp)


def test_the_sheet_of_a_specified_stage_is_within_the_width(specified_sheet):
    """No line of the sheet of the specified `cons` is wider than the
    width."""
    assert max(len(line) for line in specified_sheet.splitlines()) <= WIDTH


def test_the_rule_of_the_bindings_section_is_a_hairline_once_the_three_verbs_have_bound(
    specified_sheet,
):
    """The rule of the section `BINDINGS` of the sheet of the specified
    `cons` is a hairline, not the dashed rule of a section that is not
    complete."""
    rule = [line for line in specified_sheet.splitlines() if line.startswith("BINDINGS")][0]
    assert "┄" not in rule and "─" in rule


def test_the_bindings_section_lists_the_value_that_the_calibration_binds(bindings_section):
    """The section `BINDINGS` of the sheet of the specified `cons` lists the
    value 6.0 that the calibration binds to ρ."""
    assert "ρ = 6.0" in " ".join(bindings_section)


@pytest.mark.parametrize(
    ("place", "method"),
    [
        pytest.param("cntn_to_dcsn.evaluate", "!Linear", id="evaluation-of-the-decision-builder"),
        pytest.param("policy", "!egm", id="policy-builder"),
    ],
)
def test_the_bindings_section_writes_each_place_and_its_method_at_the_start_of_one_line(
    bindings_section, place, method
):
    """The section `BINDINGS` of the sheet of the specified `cons` writes a
    place and the method that the methods file binds there together, not
    abbreviated, at the start of one line of its methods."""
    # a setting's line names the place that reads it after the setting and
    # its value, so that only the line of the methods starts with the place
    lines = [line for line in bindings_section if line.split()[:2] == [place, method]]
    assert len(lines) == 1


def test_an_aggregation_with_a_long_signature_types_its_output_by_the_state_and_two_shocks(
    long_aggregation,
):
    """The record of the aggregation of the two-node stage types its output,
    a function of the state and the two shocks, as `ℝ × ℝ × ℝ → ℝ`, whatever
    the line at which its card breaks."""
    assert long_aggregation.denote().outputs[0].type == "ℝ × ℝ × ℝ → ℝ"


def test_the_kernel_of_an_aggregation_with_a_long_signature_keeps_the_control_and_its_set(
    long_aggregation,
):
    """The type of the kernel of the aggregation of the two-node stage keeps
    the control `c` among its coordinates and the feasible set `Γ(k_d)` of
    the control, whatever the line at which its card breaks."""
    raw_kernel = long_aggregation.denote().kernel.denoted[0]
    assert " ".join(raw_kernel.type.split()) == (
        "{V≻, k_d, c, y, z ∈ ℝ × ℝ × [0, 1] × ℝ × ℝ | c ∈ Γ(k_d)} → UNRESOLVED[𝐺; result set]"
    )


def test_the_card_of_a_primitive_holds_no_section_of_wires(long_aggregation):
    """No section of the card of the aggregation of the two-node stage is
    headed `WIRES`: a card names the wires of a primitive in its `Signature`
    section."""
    assert "WIRES" not in headings_of(str(long_aggregation))


def test_the_card_of_a_long_signature_breaks_its_lines_within_the_width(long_aggregation):
    """Each line of the card of the aggregation of the two-node stage, whose
    signature is too wide for one line, stands within the width."""
    # the statement also asks that no line end in an arrow; the layout breaks
    # a signature before `↦` and before `:` and sets each set of maps on one
    # line, so that no line of this card ends in an arrow unless the layout
    # breaks inside a set that fits on its line
    card = str(long_aggregation)
    assert all(len(line) <= WIDTH and not line.endswith("→") for line in card.splitlines())


def test_the_settings_of_the_bindings_section_name_the_place_that_reads_each_in_one_column(
    bindings_section,
):
    """In the section `BINDINGS` of the sheet of the specified `cons`, each
    of the settings `n_m`, `m_min` and `m_max` ends with the place
    `cntn_to_dcsn.evaluate` and its method `!Linear`, which stand in one
    column."""
    first = next(index for index, line in enumerate(bindings_section) if "n_m " in line)
    # the three settings n_m, m_min and m_max stand on three lines in turn
    settings = bindings_section[first : first + 3]
    assert all(line.endswith("cntn_to_dcsn.evaluate   !Linear") for line in settings)
    assert len({line.index("cntn_to_dcsn.evaluate") for line in settings}) == 1


def test_the_components_of_a_place_too_wide_for_one_line_break_at_spaces_under_one_column(
    bindings_section,
):
    """In the section `BINDINGS` of the sheet of the specified `cons`, the
    components of the place `cntn_to_dcsn.evaluate`, too wide for one line,
    break at their spaces onto lines within the width that all start at one
    column."""
    evaluate = next(
        index
        for index, line in enumerate(bindings_section)
        if line.split()[:1] == ["cntn_to_dcsn.evaluate"]
    )
    policy = next(
        index for index, line in enumerate(bindings_section) if line.split()[:1] == ["policy"]
    )
    components = bindings_section[evaluate:policy]
    assert len(components) > 1 and all(len(line) <= WIDTH for line in components)
    assert " ".join(" ".join(components).split()) == (
        "cntn_to_dcsn.evaluate !Linear !Cartesian(m_d=(m_min, m_max, n_m)) "
        '"cons-port:_make_interp"'
    )
    assert len({len(line) - len(line.lstrip()) for line in components}) == 1


def test_a_product_of_eleven_intervals_breaks_within_the_width_and_keeps_each_interval_whole():
    """The definitions listing of a parameter declared in a product of eleven
    intervals `[0,1]`, wider than one line, prints the eleven intervals on
    lines within the width and splits none of them."""
    # eleven factors `[0, 1]` joined by ` × ` take 96 columns, more than the
    # width of 78
    rates = stage_from_text("@stage: t\nrates : " + " × ".join(["[0,1]"] * 11) + "\n")
    listing = str(rates.definitions.list()).splitlines()
    assert sum(line.count("[0, 1]") for line in listing) == 11
    assert split_sets(listing) == []
    assert all(len(line) <= WIDTH for line in listing)


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_every_sheet_of_a_stage_file_reads_back_by_the_grammar_of_sheets(
    src, read_only_stage_from_file
):
    """Each stage file under `applications/` that elaborates prints at least
    one sheet, and every sheet reads back by the grammar of sheets and cards,
    is within the width, ends no line in a space and splits no set whose
    print holds a space."""
    report = parse_every_sheet(read_only_stage_from_file(src))
    assert report["sheets"] > 0
    faults = ("unparsed", "over_width", "trailing", "split_set")
    assert {fault: report[fault] for fault in faults} == {fault: [] for fault in faults}


def test_the_policy_signature_writes_the_two_controls_as_one_tuple_in_one_policy_set(
    adjuster_cons_with_egm_lines,
):
    """The signature of the policy builder of the durables adjuster writes
    its two controls as one tuple, each name as the author spelled it, in
    one set of policies `𝒫`."""
    signature = str(adjuster_cons_with_egm_lines.builder.bwd["policy"].signature())
    assert "(𝑐(m, z_d), ℎ_choice(m, z_d)) : 𝒫(" in signature
    assert signature.count("𝒫(") == 1


def test_the_card_of_a_two_control_policy_builder_leaves_no_joint_set_unresolved(
    adjuster_cons_with_egm_lines,
):
    """The card of the policy builder of the durables adjuster, whose policy
    chooses two controls jointly, writes no `joint relation projection`, the
    reason that the package gives for the set of one control that it cannot
    project from the set of joint policies."""
    card = str(adjuster_cons_with_egm_lines.builder.bwd["policy"].denote())
    # the reasons that the package writes in an unresolved set where it
    # cannot project the set of joint policies onto the set of one control,
    # and where it cannot represent the candidate of a joint solution; the
    # second stands only in the formula of an operator and in the expression
    # of an operator's output wires, neither of which the card of a builder
    # prints, so that only the first can reach this card
    reasons = ("joint relation projection", "joint solution candidate representation")
    assert [reason for reason in reasons if reason in card] == []


def test_the_card_of_a_two_control_policy_builder_is_within_78_columns(
    adjuster_cons_with_egm_lines,
):
    """No line of the card of the policy builder of the durables adjuster is
    wider than 78 columns."""
    card = str(adjuster_cons_with_egm_lines.builder.bwd["policy"].denote())
    assert all(len(line) <= 78 for line in card.splitlines())


@pytest.mark.parametrize("direction", ["bwd", "fwd"], ids=["backward", "forward"])
def test_no_kernel_of_a_two_control_builder_at_the_decision_writes_an_unresolved_projection(
    adjuster_cons_with_egm_lines, direction
):
    """No kernel of the backward or the forward builder at the decision perch
    of the durables adjuster writes `joint relation projection`, the reason
    that the package gives for the set of one of two controls that it leaves
    unresolved."""
    # a kernel reads the sets that the stage file declares for the controls,
    # not the set of joint policies, so that the package can fail this test
    # only by writing an unresolved set into a kernel
    answer = getattr(adjuster_cons_with_egm_lines.dcsn.builder, direction).denote()
    kernels = [
        str(piece.record.kernel) for piece in answer.pieces if piece.record.kernel is not None
    ]
    # the premise: the builder has a kernel, so that the row compares one
    assert kernels != []
    assert all("joint relation projection" not in kernel for kernel in kernels)


# The fixture `cons_with_egm_lines` is the explicit consumption stage:
# `cons.bl` with the inverse marginal utility 𝑑𝑢𝑖𝑛𝑣 and the lines of the
# endogenous grid method written in its policy block, beside the argmax kept as
# documentation.
@pytest.mark.parametrize(
    ("identity", "expected"),
    [
        pytest.param("cons:function:𝑢", "c^(1 − ρ)/(1 − ρ)", id="utility"),
        # a quotient under a sign keeps no parentheses of its own
        pytest.param("cons:function:𝑑𝑢𝑖𝑛𝑣", "x^(−1/ρ)", id="inverse-marginal-utility"),
    ],
)
def test_the_body_of_a_function_prints_a_parenthesis_only_where_a_child_binds_looser(
    cons_with_egm_lines, identity, expected
):
    """The body of a function of the explicit consumption stage prints a
    parenthesis only where a child binds looser than the position that it
    stands in."""
    [function] = cons_with_egm_lines.definitions.denote(identity).denoted
    assert typed_expressions.format_expression(function.expression.body, width=None) == expected


@pytest.mark.parametrize(
    ("identity", "expected"),
    [
        pytest.param("cons:function:𝑢", "c ↦ c^(1 − ρ)/(1 − ρ)", id="utility"),
        pytest.param("cons:correspondence:Γ", "x ↦ (0, x]", id="feasible-correspondence"),
    ],
)
def test_a_function_or_a_correspondence_prints_as_a_map_from_its_argument_by_name(
    cons_with_egm_lines, identity, expected
):
    """A function or a correspondence of the explicit consumption stage
    prints as a map from its argument, named as the stage file names it."""
    [definition] = cons_with_egm_lines.definitions.denote(identity).denoted
    assert typed_expressions.format_expression(definition.expression, width=None) == expected


def test_the_law_of_motion_of_the_consumption_stage_prints_its_body_as_m_d_minus_c(
    cons_with_egm_lines,
):
    """The body of the law of motion `a = m_d - c` of the explicit
    consumption stage prints as `m_d − c`."""
    [law] = cons_with_egm_lines.definitions.denote("cons:g:dcsn_to_cntn").denoted
    assert typed_expressions.format_expression(law.expression.body, width=None) == "m_d − c"


def test_the_aggregation_names_the_continuation_value_with_the_mark_of_its_perch(
    cons_with_egm_lines,
):
    """The kernel types of the aggregation of the explicit consumption stage
    name the continuation value `V≻`, with the mark of its perch after the
    letter, in place of `V[>]` or of a name that holds the law of motion as
    `∘𝑔`."""
    aggregation = cons_with_egm_lines.builder.bwd["cntn_to_dcsn", "Aggregation"].denote()
    carriers = "\n".join(str(denoted.mathematical_type) for denoted in aggregation.kernel.denoted)
    # the composition with the law of motion is a term of its own, `V≻ ∘ 𝑔`,
    # so the argument of the aggregator is `V≻`
    assert "V≻" in carriers and "∘𝑔" not in carriers and "[>]" not in carriers


# Each row: the printed text and the term, built from the classes of the
# terms: `terms.Sub(x, y)` is x − y, `terms.Div` a quotient, `terms.Mul` a
# product, `terms.Neg` a sign, `terms.Pow` a power, `terms.Rel` a relation,
# `predicates.And`, `Or`, `Not`, `Compare` and `Member` a conjunction, a
# disjunction, a negation, a comparison and a membership.
PARENTHESES = [
    pytest.param(
        "a − (b − c)",
        terms.Sub(name_term("a"), terms.Sub(name_term("b"), name_term("c"))),
        id="subtraction-as-the-right-operand-of-a-subtraction",
    ),
    pytest.param(
        "a/(b · c)",
        terms.Div(name_term("a"), terms.Mul(name_term("b"), name_term("c"))),
        id="product-as-the-right-operand-of-a-quotient",
    ),
    pytest.param(
        "a/(b/c)",
        terms.Div(name_term("a"), terms.Div(name_term("b"), name_term("c"))),
        id="quotient-as-the-right-operand-of-a-quotient",
    ),
    # an integer exponent prints as superscript digits
    pytest.param(
        "(−c)²",
        terms.Pow(terms.Neg(name_term("c")), terms.Number(2)),
        id="sign-as-the-base-of-a-power",
    ),
    pytest.param(
        "c^(−ρ)",
        terms.Pow(name_term("c"), terms.Neg(name_term("ρ"))),
        id="sign-as-the-exponent-of-a-power",
    ),
    pytest.param(
        "a − (b + c)",
        terms.Sub(name_term("a"), terms.Add(name_term("b"), name_term("c"))),
        id="sum-as-the-right-operand-of-a-subtraction",
    ),
    pytest.param(
        "argmax_{c ∈ Γ(a)} [𝑢(c) + b]",
        terms.Operator(
            "argmax",
            (terms.In("c", terms.Call("Γ", (name_term("a"),))),),
            (terms.Add(terms.Call("𝑢", (name_term("c"),)), name_term("b")),),
        ),
        id="objective-of-an-argmax",
    ),
    pytest.param(
        "∀ x ∈ ℝ₊₊: (a = b ∧ b ≤ c)",
        terms.Operator(
            "forall",
            (terms.In("x", terms.Named("ℝ₊₊")),),
            (
                terms.Rel(name_term("a"), terms.Eq(), name_term("b")),
                terms.Rel(name_term("b"), terms.Le(), name_term("c")),
            ),
        ),
        id="body-of-a-quantifier",
    ),
    pytest.param(
        "a − b − c",
        terms.Sub(terms.Sub(name_term("a"), name_term("b")), name_term("c")),
        id="subtraction-as-the-left-operand-of-a-subtraction",
    ),
    pytest.param(
        "a/b/c",
        terms.Div(terms.Div(name_term("a"), name_term("b")), name_term("c")),
        id="quotient-as-the-left-operand-of-a-quotient",
    ),
    pytest.param(
        "a/b · c",
        terms.Mul(terms.Div(name_term("a"), name_term("b")), name_term("c")),
        id="quotient-as-the-left-operand-of-a-product",
    ),
    pytest.param(
        "−c²",
        terms.Neg(terms.Pow(name_term("c"), terms.Number(2))),
        id="power-under-a-sign",
    ),
    pytest.param(
        "−a · b",
        terms.Mul(terms.Neg(name_term("a")), name_term("b")),
        id="sign-as-the-left-operand-of-a-product",
    ),
    pytest.param(
        "a − b + c",
        terms.Add(terms.Sub(name_term("a"), name_term("b")), name_term("c")),
        id="subtraction-as-the-left-operand-of-a-sum",
    ),
    pytest.param(
        "a − b = 0",
        terms.Rel(terms.Sub(name_term("a"), name_term("b")), terms.Eq(), terms.Number(0)),
        id="subtraction-as-a-side-of-a-relation",
    ),
    pytest.param(
        "a = b ∧ b ≤ c",
        predicates.And(
            predicates.Compare(name_term("a"), "=", name_term("b")),
            predicates.Compare(name_term("b"), "<=", name_term("c")),
        ),
        id="comparisons-in-a-conjunction",
    ),
    pytest.param(
        "(a = b ∨ b = c) ∧ c = a",
        predicates.And(
            predicates.Or(
                predicates.Compare(name_term("a"), "=", name_term("b")),
                predicates.Compare(name_term("b"), "=", name_term("c")),
            ),
            predicates.Compare(name_term("c"), "=", name_term("a")),
        ),
        id="disjunction-in-a-conjunction",
    ),
    pytest.param(
        "¬(1 − ρ = 0)",
        predicates.Not(
            predicates.Compare(terms.Sub(terms.Number(1), name_term("ρ")), "=", terms.Number(0))
        ),
        id="comparison-under-a-negation",
    ),
    pytest.param(
        "a − b ∈ ℝ₊",
        predicates.Member(terms.Sub(name_term("a"), name_term("b")), terms.Named("ℝ₊")),
        id="subtraction-as-the-element-of-a-membership",
    ),
    pytest.param(
        "a + (−b)",
        terms.Add(name_term("a"), terms.Neg(name_term("b"))),
        id="sign-as-the-right-operand-of-a-sum",
    ),
    pytest.param(
        "−(−a)",
        terms.Neg(terms.Neg(name_term("a"))),
        id="sign-under-a-sign",
    ),
    pytest.param(
        "(a^b)^c",
        terms.Pow(terms.Pow(name_term("a"), name_term("b")), name_term("c")),
        id="power-as-the-base-of-a-power",
    ),
    pytest.param(
        "pi ∈ (ℝ₊₊ → ℝ₊₊)",
        predicates.Member(
            name_term("pi"), typed_expressions.FunctionSet(terms.Named("ℝ₊₊"), terms.Named("ℝ₊₊"))
        ),
        id="set-of-functions-as-the-set-of-a-membership",
    ),
    pytest.param(
        "(ℝ₊₊ → ℝ) × (ℝ₊₊ → ℝ₊₊)",
        terms.Product(
            (
                typed_expressions.FunctionSet(terms.Named("ℝ₊₊"), terms.Named("ℝ")),
                typed_expressions.FunctionSet(terms.Named("ℝ₊₊"), terms.Named("ℝ₊₊")),
            )
        ),
        id="sets-of-functions-as-the-factors-of-a-product",
    ),
]


@pytest.mark.parametrize(("expected", "term"), PARENTHESES)
def test_a_term_prints_the_parentheses_that_its_tree_needs_and_no_others(expected, term):
    """A term prints a parenthesis where its tree needs one, such as around
    the right operand of a subtraction, and none where the order of
    operations gives the tree, such as around its left operand."""
    assert typed_expressions.format_expression(term, width=None) == expected


def test_the_maximand_of_the_argmax_of_the_consumption_stage_prints_in_square_brackets(cons):
    """The maximand of the argmax of the policy line of `cons` prints in
    square brackets after the subscript of the argmax."""
    objective = cons.definitions["policy.optimality"].equations[0].rhs
    assert (
        typed_expressions.format_expression(objective, width=None)
        == "argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + V[>]]"
    )


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        pytest.param(
            terms.Operator(
                "E", (terms.Var("y"), terms.Var("z")), (terms.Mul(name_term("β"), name_term("W")),)
            ),
            "E_{y, z}[β · W]",
            id="expectation-brackets-its-operand",
        ),
        pytest.param(
            terms.Operator(
                "solve", (terms.Var("ς"),), (terms.Sub(name_term("a"), name_term("b")),)
            ),
            "solve_{ς}(a − b)",
            id="solve-keeps-parentheses",
        ),
    ],
)
def test_an_operator_prints_its_operand_in_square_brackets_or_parentheses_by_its_head(
    term, expected
):
    """The operand of an expectation stands in square brackets directly after
    its head, and the operand of `solve`, which is no maximization, sum,
    expectation or integral, stands in parentheses."""
    assert typed_expressions.format_expression(term, width=None) == expected


def test_the_pullback_of_the_explicit_policy_writes_the_truth_of_its_relation_in_brackets(
    cons_with_egm_lines,
):
    """The pullback of the policy builder of the explicit consumption stage,
    the one relation that the identification instantiates over the admitted
    pairs, writes the truth of its relation as a supremum whose operand
    stands in square brackets."""
    identification = next(
        piece.record
        for piece in cons_with_egm_lines.builder.bwd["policy"].denote().pieces
        if piece.record.kind == "Pullback"
    )
    text = typed_expressions.format_expression(identification.expression, width=None)
    assert "sup_{truth ∈ " in text and "} [truth]" in text and "} (truth)" not in text


# 𝑐(𝑚_d≻(a)), the left-hand side of the relations that the layout tests
# render
CONSUMPTION_AT_THE_GRID = terms.Call("𝑐", (terms.Call("𝑚_d≻", (name_term("a"),)),))


# 𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp)), the objective at a candidate cp
OBJECTIVE = terms.Add(
    terms.Call("𝑢", (name_term("cp"),)),
    terms.Call("𝑉≻", (terms.Call("𝑔≻", (name_term("m_d"), name_term("cp"))),)),
)


# 𝑐(𝑚_d≻(a)) = OBJECTIVE + OBJECTIVE + OBJECTIVE, too wide for one line of 78
# columns
WIDE_RELATION = terms.Rel(
    CONSUMPTION_AT_THE_GRID, terms.Eq(), terms.Add(terms.Add(OBJECTIVE, OBJECTIVE), OBJECTIVE)
)


# 𝑐(𝑚_d≻(a)) = 𝑐≻(a), the relation of the grid of the endogenous grid method,
# which fits on one line
GRID_RELATION = terms.Rel(CONSUMPTION_AT_THE_GRID, terms.Eq(), terms.Call("𝑐≻", (name_term("a"),)))


# In the layout tests, `layout.concat(" " * n, layout.nest(n, document))`
# sets a document at column n, the column at which its continuations nest,
# and `layout.render(..., width=78)` renders it within the 78 columns of a
# card.


def test_a_relation_wider_than_the_line_breaks_before_its_sign_and_before_each_summand():
    """A relation wider than 78 columns, set at column 14, breaks before its
    sign, two columns in, and before each summand of its right-hand side,
    two columns further in, on lines within the width that start with a
    space and end in none."""
    entry = layout.concat(
        " " * 14, layout.nest(14, typed_expressions.format_document(WIDE_RELATION))
    )
    lines = layout.render(entry, width=78).split("\n")
    assert lines[0] == " " * 14 + "𝑐(𝑚_d≻(a))"
    assert lines[1] == " " * 16 + "= 𝑢(cp)"
    # a chain of sums is one group, which breaks before every sign together
    assert lines[2] == " " * 18 + "+ 𝑉≻(𝑔≻(m_d, cp))"
    # a sum that stands as a right operand keeps its parentheses
    assert lines[3] == lines[4] == " " * 18 + "+ (𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp)))" and len(lines) == 5
    assert all(len(line) <= 78 and line[0] == " " and not line.endswith(" ") for line in lines)


def test_a_relation_that_fits_in_the_line_renders_on_one_line():
    """A relation that fits in 78 columns renders on one line."""
    rendered = layout.render(typed_expressions.format_document(GRID_RELATION), width=78)
    assert rendered == "𝑐(𝑚_d≻(a)) = 𝑐≻(a)"


def test_a_margin_note_stands_against_the_right_margin_where_the_line_leaves_room():
    """The margin note of a rule set at column eleven, the column of the text
    of a rule on a card, stands against the right margin of 78 columns on
    the line of the rule, where that line leaves room for it."""
    # the margin note of the grid relation, the set on which it holds, as the
    # card of the policy builder of `cons` sets it
    note = "on 𝑚_d≻(Xa)"
    noted = layout.render(
        layout.concat(
            " " * 11,
            layout.nest(11, typed_expressions.format_document(GRID_RELATION), layout.margin(note)),
        ),
        width=78,
    )
    rule = "𝑐(𝑚_d≻(a)) = 𝑐≻(a)"
    # the spaces between the rule and the note fill the 78 columns
    assert noted == " " * 11 + rule + " " * (78 - 11 - len(rule) - len(note)) + note


def test_a_margin_note_stands_on_a_line_of_its_own_where_the_last_line_leaves_no_room():
    """The margin note of a rule set at column eleven stands on a line of its
    own under the first character of the rule, where the last line of the
    rule leaves no room for it."""
    note = "on 𝑚_d≻(Xa)"
    # a relation whose right-hand side holds a name of 56 letters, so that
    # its last line is too long for the note
    wide = terms.Rel(
        CONSUMPTION_AT_THE_GRID, terms.Eq(), terms.Add(name_term("a"), name_term("b" * 56))
    )
    document = typed_expressions.format_document(wide)
    bare = layout.render(layout.concat(" " * 11, layout.nest(11, document)), width=78)
    # the guard: the last line leaves less than the note and two spaces
    assert len(bare.split("\n")[-1]) > 78 - 2 - len(note)
    own_line = layout.render(
        layout.concat(" " * 11, layout.nest(11, document, layout.margin(note))), width=78
    ).split("\n")
    assert own_line[:-1] == bare.split("\n") and own_line[-1] == " " * 11 + note


@pytest.mark.parametrize(
    ("line", "character"),
    [
        pytest.param(layout.HEAVY, "━", id="heavy"),
        pytest.param(layout.LIGHT, "─", id="light"),
    ],
)
def test_a_horizontal_line_of_a_card_is_drawn_across_its_78_columns(line, character):
    """The heavy line and the light line of a card are drawn across its 78
    columns."""
    assert layout.horizontal_line(line) == character * 78


def test_the_flat_rendering_of_a_relation_is_its_expression_printed_on_one_line():
    """The document of a relation, rendered flat, is the text that the printer
    of expressions writes on one line."""
    document = typed_expressions.format_document(WIDE_RELATION)
    assert layout.flat(document) == typed_expressions.format_expression(WIDE_RELATION, width=None)


@pytest.mark.parametrize(
    ("handle", "short_forms"),
    [
        pytest.param(
            "decision_builder_of_cons",
            [
                "Builder('cons', 'cntn_to_dcsn')",
                "Builder('cons', 'cntn_to_dcsn', primitives)",
                "Builder('cons', 'cntn_to_dcsn', sub_builders)",
            ],
            id="builder",
        ),
        pytest.param(
            "backward_builders_graph_of_cons",
            [
                "BuildersGraph('cons', 'backward')",
                "BuildersGraph('cons', 'backward', primitives)",
                "BuildersGraph('cons', 'backward', sub_builders)",
            ],
            id="builders-graph",
        ),
    ],
)
def test_the_short_form_of_a_handle_names_the_grain_at_which_it_is_opened(
    request, handle, short_forms
):
    """A builder and a builders graph print a short form that names neither
    grain, and the same handle opened at the primitive or the sub-builder
    grain prints one that names the grain by the attribute that reaches
    it."""
    piece = request.getfixturevalue(handle)
    assert [repr(piece), repr(piece.primitives), repr(piece.sub_builders)] == short_forms


def test_a_branch_opened_at_the_primitive_grain_prints_a_short_form_that_names_the_grain(
    keep_branch_of_tenure,
):
    """The branch `keep` of the forward initial diagram of `tenure`, opened
    at the primitive grain, prints a short form that names the grain."""
    assert (
        repr(keep_branch_of_tenure.primitives)
        == "Block('tenure', 'dcsn_to_cntn.keep', primitives)"
    )


@pytest.mark.parametrize(
    ("handle", "grain"),
    [
        pytest.param("decision_builder_of_cons", "primitives", id="builder-at-the-primitives"),
        pytest.param("decision_builder_of_cons", "sub_builders", id="builder-at-the-sub-builders"),
        pytest.param("keep_branch_of_tenure", "primitives", id="branch-at-the-primitives"),
    ],
)
def test_a_piece_opened_at_a_finer_grain_answers_the_obligations_of_the_piece(
    request, handle, grain
):
    """A builder or a branch opened at a finer grain answers the obligations
    that the builder or the branch answers."""
    piece = request.getfixturevalue(handle)
    assert getattr(piece, grain).obligations() == piece.obligations()


@pytest.mark.parametrize("grain", ["primitives", "sub_builders"])
def test_a_builder_opened_at_a_finer_grain_prints_the_record_that_it_denotes(
    decision_builder_of_cons, grain
):
    """The decision builder of `cons` opened at the primitive or the
    sub-builder grain prints the record that its `denote()` answers."""
    opened = getattr(decision_builder_of_cons, grain)
    assert str(opened.denote()) == str(opened)


@pytest.mark.parametrize(
    ("handle", "grain", "title"),
    [
        pytest.param(
            "decision_builder_of_cons",
            "primitives",
            "cntn_to_dcsn",
            id="builder-at-the-primitives",
        ),
        pytest.param(
            "decision_builder_of_cons",
            "sub_builders",
            "cntn_to_dcsn",
            id="builder-at-the-sub-builders",
        ),
        pytest.param(
            "keep_branch_of_tenure",
            "primitives",
            "FORWARD BLOCK dcsn_to_cntn / keep",
            id="branch-at-the-primitives",
        ),
    ],
)
def test_the_card_of_a_piece_opened_at_a_finer_grain_names_the_piece(
    request, handle, grain, title
):
    """The card of a builder or a branch opened at a finer grain names the
    builder or the branch."""
    assert title in str(getattr(request.getfixturevalue(handle), grain))


def test_a_branch_opened_at_the_primitive_grain_lists_the_entries_of_the_branch(
    keep_branch_of_tenure,
):
    """The branch `keep` of the forward initial diagram of `tenure`, opened
    at the primitive grain, lists the entries, not none, that the branch
    lists."""
    branch = keep_branch_of_tenure
    assert list(branch.primitives.list()) == list(branch.list()) != []


def test_a_branch_opened_at_the_primitive_grain_prints_the_signature_of_the_branch(
    keep_branch_of_tenure,
):
    """The branch `keep` of the forward initial diagram of `tenure`, opened
    at the primitive grain, prints the signature of the branch."""
    branch = keep_branch_of_tenure
    assert str(branch.primitives.signature()) == str(branch.signature())


@pytest.mark.parametrize(
    "handle", ["builder", "sub-builder grain", "primitive grain", "sub-builder risk_ce"]
)
def test_each_key_of_a_listing_reaches_the_box_of_the_name_listed_with_it(
    decision_builder_of_sa_savings, handle
):
    """Each key of the listing of the decision builder of `sa_savings`, of
    the builder at its sub-builder and its primitive grain, and of its
    sub-builder `risk_ce`, reaches the box of the name that the listing gives
    with the key."""
    builder = decision_builder_of_sa_savings
    # the premise: the builder lists the pullback `risk_ce` second, a
    # sub-builder, so that its listings at the two grains differ and the last
    # row reads a sub-builder
    assert builder.list()[1] == ("risk_ce", "Pullback")
    reached = {
        "builder": builder,
        "sub-builder grain": builder.sub_builders,
        "primitive grain": builder.primitives,
        "sub-builder risk_ce": builder["risk_ce"],
    }[handle]
    listing = reached.list()
    assert [reached[key].box.name for key in listing] == list(listing.names)


def test_a_builders_listing_numbers_each_primitive_as_its_primitive_grain_does(
    decision_builder_of_sa_savings,
):
    """The listing of the decision builder of `sa_savings` gives each
    primitive that it numbers the number that the listing of the builder at
    its primitive grain gives it."""
    builder = decision_builder_of_sa_savings
    # the premise: the builder lists the pullback `risk_ce` second, a
    # sub-builder, which carries no number, beside its primitives
    assert builder.list()[1] == ("risk_ce", "Pullback")
    numbered = [
        (entry.name, entry.number) for entry in builder.list().entries if entry.number is not None
    ]
    assert numbered == [(entry.name, entry.number) for entry in builder.primitives.list().entries]


def test_the_listing_of_a_primitive_prints_none(decision_builder_of_sa_savings):
    """The listing of the Evaluation, a primitive of the decision builder of
    `sa_savings`, prints `none`."""
    assert str(decision_builder_of_sa_savings["Evaluation"].list()) == "none"


def test_each_builder_numbers_its_primitives_as_the_primitive_grain_of_its_graph_does(
    sa_savings,
):
    """Each builder of the backward builders graph of `sa_savings`, at its
    primitive grain, numbers its primitives as the graph at its primitive
    grain numbers them."""
    graph = sa_savings.builder.bwd
    opened = {entry.name: entry.number for entry in graph.primitives.list().entries}
    for name in graph.list():
        own = graph[name].primitives.list()
        assert [opened[entry.name] for entry in own.entries] == [
            entry.number for entry in own.entries
        ]


def test_the_records_kept_for_the_cards_of_a_version_refer_to_no_version():
    """The records that a symbolic and a bound version of `cons.bl` keep for
    their cards refer to neither version: the two versions are collected
    once no name refers to them while those records are held, and the records
    print as before."""
    symbolic = corpus_stage("cons")
    bound = (
        corpus_stage("cons")
        .calibrate(FIRST_CALIBRATIONS["cons"])
        .methodize(METHODS_SOURCES_BY_STAGE["cons"])
    )
    cards = cards_of_every_handle(symbolic) + cards_of_every_handle(bound)
    # the premise: each version keeps the record of its stage card, so that
    # `denote()` answers the same record when it is asked again
    assert all(version.denote() is version.denote() for version in (symbolic, bound))
    references = [weakref.ref(symbolic), weakref.ref(bound)]
    del symbolic, bound
    gc.collect()
    assert [reference() for reference in references] == [None, None]
    assert [str(record) for _, _, record in cards] == [text for _, text, _ in cards]


@pytest.mark.parametrize("name", one_row_by_default(("cons", "port")))
def test_before_any_binding_each_declared_builder_prints_the_card_of_its_operative_builder(
    request, name
):
    """Before any binding, each declared builder of a copy of a corpus stage
    prints the card of the operative builder of the same pair of perches."""
    stage = copy_native(request.getfixturevalue(name))
    before = declared_and_initial_cards(stage)
    assert before["declared builders"] == {
        pair: str(handle.denote()) for pair, handle in stage.builder.items()
    }


# the source that each binding verb reads, by the verb, then by the stage
SOURCES = {
    "methodize": METHODS_SOURCES_BY_STAGE,
    "calibrate": FIRST_CALIBRATIONS,
    "configure": SETTINGS_SOURCES_BY_STAGE,
}


@pytest.mark.parametrize(
    ("name", "verbs"),
    [
        pytest.param("cons", ("methodize",), id="cons-methodized"),
        pytest.param(
            "cons", ("methodize", "calibrate", "configure"), id="cons-bound-by-the-three-verbs"
        ),
        pytest.param("port", ("methodize",), id="port-methodized", marks=pytest.mark.complete_set),
        pytest.param(
            "port",
            ("methodize", "calibrate", "configure"),
            id="port-bound-by-the-three-verbs",
            marks=pytest.mark.complete_set,
        ),
    ],
)
def test_a_binding_changes_none_of_the_declared_and_initial_cards(request, name, verbs):
    """The cards of the declared builders, of the blocks and lines of the two
    initial diagrams and of the diagrams of a copy of a corpus stage print
    byte for byte as before, once its methods, or its methods, calibration
    and settings, are bound."""
    stage = copy_native(request.getfixturevalue(name))
    before = declared_and_initial_cards(stage)
    for verb in verbs:
        getattr(stage, verb)(SOURCES[verb][name])
    assert declared_and_initial_cards(stage) == before


@pytest.mark.parametrize(
    ("card", "headings"),
    [
        pytest.param(
            "policy_card_of_cons",
            [
                "Signature",
                "Declared",
                "Operations",
                "Conditions",
                "Method",
                "Source",
                "Source",
                "Definitions referenced",
            ],
            id="policy-builder-of-cons",
        ),
        # one `Method` section for each place that the methods file types,
        # the keyword arguments of the quadrature under `Options`
        pytest.param(
            "decision_card_of_port",
            [
                "Signature",
                "At",
                "Operations",
                "Conditions",
                "Method",
                "Method",
                "Options",
                "Method",
                "Source",
                "Definitions referenced",
            ],
            id="decision-builder-of-port",
        ),
    ],
)
def test_the_card_of_a_bound_builder_prints_its_sections_in_order(request, card, headings):
    """The card of a builder bound with its methods file prints its sections
    in the order of a card."""
    assert headings_of(request.getfixturevalue(card)) == headings


def test_the_policy_builder_of_cons_prints_a_source_section_for_each_file_the_stage_first(
    policy_card_of_cons,
):
    """The card of the policy builder of `cons` bound with its addition
    prints one `Source` section for each file that writes its lines, the
    stage file first."""
    assert [line for line in policy_card_of_cons.splitlines() if line.startswith("Source  ")] == [
        "Source  cons.bl",
        "Source  methods.bl",
    ]


def test_the_definitions_referenced_by_the_policy_builder_name_the_file_of_the_addition(
    policy_card_of_cons,
):
    """The section `Definitions referenced` of the card of the policy builder
    of `cons` gives the file and the line of the addition at which it defines
    the function `𝑑𝑢𝑖𝑛𝑣`."""
    rows = [line.split() for line in policy_card_of_cons.splitlines()]
    assert ["𝑑𝑢𝑖𝑛𝑣", "cons:function:𝑑𝑢𝑖𝑛𝑣", "methods.bl:19"] in rows


def test_the_method_section_of_the_policy_builder_writes_its_method_grid_implementation_and_place(
    policy_card_of_cons,
):
    """The section `Method` of the card of the policy builder of `cons`
    writes the method `!egm`, its grid, its implementation and, at the end
    of the line, its place `policy`."""
    method = next(line for line in policy_card_of_cons.splitlines() if line.startswith("  !egm"))
    assert method.startswith(
        '  !egm   !Cartesian(a=(a_min, a_max, n_a))   "cons-port:egm"'
    ) and method.endswith("policy")


def test_the_options_section_of_the_decision_builder_of_port_writes_each_keyword_argument(
    decision_card_of_port,
):
    """The section `Options` of the card of the decision builder of `port`
    writes each keyword argument of its quadrature on a line of its own."""
    assert "  n_Ψ = n_Ψ_nodes\n  n_θ = n_θ_nodes\n" in decision_card_of_port


@pytest.mark.parametrize(
    "card", ["policy_card_of_cons", "decision_card_of_port"], ids=["policy", "decision"]
)
def test_the_card_of_a_bound_builder_is_within_78_columns(request, card):
    """No line of the card of a builder bound with its methods file is wider
    than 78 columns."""
    assert max(len(line) for line in request.getfixturevalue(card).splitlines()) <= 78


@pytest.mark.parametrize(
    "card", ["policy_card_of_cons", "decision_card_of_port"], ids=["policy", "decision"]
)
def test_each_numbered_operation_of_a_bound_builder_prints_its_rule(request, card):
    """Each of the four or more numbered entries of the section `Operations`
    of the card of a builder bound with its methods file prints its rule."""
    text = request.getfixturevalue(card)
    operations = text.split("\nOperations\n", 1)[1].split("\nConditions\n", 1)[0]
    # the number of an entry stands in the first four columns of its line
    numbered = [line for line in operations.splitlines() if line[:4].strip().isdigit()]
    assert len(numbered) >= 4 and operations.count("rule: ") == len(numbered)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("ρ", "ρ : (0, 1) \\/ (1, inf), unbound", id="union"),
        pytest.param("σ", "σ : ℝ₊₊ \\ {1}, unbound", id="difference"),
    ],
)
def test_the_record_of_a_parameter_prints_a_union_or_a_difference_with_the_signs_of_the_file(
    stage_with_a_union_and_a_difference, name, expected
):
    """The record of a parameter declared in a union or a difference prints
    its set with the signs that a stage file writes, `\\/` and `\\`."""
    assert str(stage_with_a_union_and_a_difference.par[name]) == expected


@pytest.mark.parametrize(
    "declaration",
    [
        pytest.param("ρ : (0, 1) \\/ (1, inf)", id="union"),
        pytest.param("σ : ℝ₊₊ \\ {1}", id="difference"),
    ],
)
def test_the_sheet_prints_a_union_or_a_difference_with_the_signs_of_the_file(
    stage_with_a_union_and_a_difference, declaration
):
    """The sheet of a stage prints a parameter declared in a union or a
    difference with the signs that a stage file writes, `\\/` and `\\`."""
    assert declaration in stage_with_a_union_and_a_difference.view()


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        pytest.param("cons_obs:parameter:ρ", "ρ  ∈ (0, 1) ∪ (1, ∞)", id="union"),
        pytest.param("cons_obs:parameter:σ", "σ  ∈ ℝ₊₊ ∖ {1}", id="difference"),
    ],
)
def test_the_card_of_a_parameter_prints_a_union_or_a_difference_with_mathematical_signs(
    cards_of_the_stage_with_a_union_and_a_difference, title, expected
):
    """The card of a parameter declared in a union or a difference prints its
    set with the signs of mathematics, `∪` and `∖`."""
    assert expected in cards_of_the_stage_with_a_union_and_a_difference[title]


def test_no_card_names_the_class_of_a_union_or_a_difference_in_place_of_the_set(
    cards_of_the_stage_with_a_union_and_a_difference,
):
    """No card of the stage with a union and a difference names the class of
    a union or of a difference of sets in place of the set."""
    cards = cards_of_the_stage_with_a_union_and_a_difference
    classes = ("SetUnion", "SetDifference")
    assert [title for title, text in cards.items() if any(name in text for name in classes)] == []


@pytest.mark.parametrize(
    ("written", "printed"),
    [
        pytest.param("ℝ \\ {0} \\/ {5}", "(ℝ ∖ {0}) ∪ {5}", id="difference-in-a-union"),
        pytest.param(
            "(0,1) \\/ (2,3) \\ {5}", "((0, 1) ∪ (2, 3)) ∖ {5}", id="union-in-a-difference"
        ),
        pytest.param(
            "{1, …, 2} → (0,1) \\/ (1, 2)",
            "{1, …, 2} → (0, 1) ∪ (1, 2)",
            id="union-as-the-set-of-values-of-a-map-keeps-no-parentheses",
        ),
        # `⊂` would otherwise be read as a claim about the whole set
        pytest.param(
            "ℝ \\ {θ} ⊂ (0, 1)",
            "ℝ ∖ ({θ} ⊂ (0, 1))",
            id="listed-set-within-a-set-in-a-difference",
        ),
        pytest.param(
            "{θ} ⊂ (0, 1) \\/ (2, 3)",
            "(2, 3) ∪ ({θ} ⊂ (0, 1))",
            id="listed-set-within-a-set-in-a-union",
        ),
    ],
)
def test_an_operand_of_a_union_or_a_difference_prints_in_parentheses_where_it_is_compound(
    written, printed
):
    """A declared set prints in parentheses each operand of a union or a
    difference that is itself a union, a difference or a listed set with the
    set its members lie in, and a union that is the set of values of a map
    in none."""
    term, _ = parse_with_spans(f"β : {written}\n", "t.bl")
    (domain,) = [
        classifier
        for classifier in term.items[-1].declaration.classifiers
        if isinstance(classifier, terms.Domain)
    ]
    assert typed_expressions.format_expression(domain.space) == printed


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_a_piece_prints_one_card_whichever_handle_reaches_it(read_only_stage_from_file, src):
    """Each primitive and each sub-builder that a builder's listing gives,
    each primitive that its sub-builders' listing gives, and each line that a
    block of an initial diagram lists, at any depth, prints the card that the
    printed text of the stage holds for the piece of the same name."""
    stage = read_only_stage_from_file(src)
    # for a line that reads no wire both handles reach one record, so that
    # its two cards are one computation printed twice
    assert pieces_with_two_cards(cards_through_two_handles(stage)) == []


def test_the_comparison_of_two_cards_reports_a_piece_whose_card_has_one_symbol_changed(cons):
    """When the card of the pullback of the policy builder of `cons` through
    `builder.sub_builders[key]` has its first `𝑉` changed to `𝑊`, the
    comparison of the cards through two handles reports that piece."""
    title = "backward policy / Pullback"
    changed = [
        (name, handle, printed.replace("𝑉", "𝑊", 1), other_handle, other)
        if (name, handle) == (title, THROUGH_SUB_BUILDERS)
        else (name, handle, printed, other_handle, other)
        for name, handle, printed, other_handle, other in cards_through_two_handles(cons)
    ]
    assert pieces_with_two_cards(changed) == [
        f"{title}: the card through {THROUGH_SUB_BUILDERS} differs from the card through "
        f"{THROUGH_PRIMITIVES}"
    ]


def test_the_card_of_a_box_of_the_wiring_is_refused_under_the_rule_target_version(retiree_death):
    """The card of a box of the wiring, the spider that joins wires inside
    the block `dcsn_to_cntn` of the forward initial diagram of
    `retiree_death`, is refused with a `TargetError` under the rule
    `target-version`, since the package places no box of the wiring in a
    graph of the stage."""
    # the test reads this stage because its forward builders graph is
    # refused, which the query for the card of a box passes over
    graph = retiree_death.initial.forward.graph
    block = next(box for box in graph.boxes if box.name == "dcsn_to_cntn")
    spider = next(box for box in block.arg.boxes if isinstance(box, Spider))
    with pytest.raises(TargetError) as refused:
        denotations.card(retiree_death, spider)
    assert refused.value.rule == "target-version"
