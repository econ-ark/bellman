"""The rows that the side panel of Model Explorer shows for a node and for a
layer of a builders graph in the view of a stage: the rows read from the
card of a primitive, the signature of a builder, the methods, the local
abbreviations, the parameters, the settings and the feasible sets; and the
sections of a card, from which those rows are read."""

import re

import pytest
from application_files import ROOT
from model_explorer_views import (
    attributes,
    builders_graphs,
    direction_rows,
    graph_named,
    needs_viewer,
    stage_rows,
)
from stage_builders import control_branching_stage, stage_from_text
from stage_graphs import operator_boxes
from stage_texts import corpus_text

from bellman.display.cards import WORDS, SourceLine
from bellman.factory.model_explorer import piece_handle
from bellman.native.identity import box_identity
from bellman.stage import box_attributes, card_sections, source_lines
from bellman.stage.kernels import kernel

# the durables keeper's consumption stage, and the methods file beside it
KEEPER_CONS = "applications/durables/declaration/stages/keeper_cons/keeper_cons.bl"
KEEPER_CONS_METHODS = "applications/durables/declaration/stages/keeper_cons/methods.bl"

# the methods file beside the stage file of the house choice
HOUSE_CHOICE_METHODS = "applications/housing-frictions/declaration/stages/house_choice/methods.bl"


# the stages on whose rows the numbering of several values is checked
NUMBERED_STAGES = (
    "cons",
    "cons_obs",
    "port",
    "ret_choice",
    "house_choice",
    "house_choice_methodized",
    "sa_savings",
    "adjuster_saving",
    "keeper_cons_methodized",
    "cons_methodized_without_calibration",
    "cons_configured",
)


def box_named(stage, direction, name):
    """The primitive box of one builders graph that has this whole name."""
    return next(box for box in operator_boxes(stage, direction) if box.name == name)


def boxes_before(stage, direction, box):
    """The primitive boxes of the builders graph of `direction` that write a
    wire `box` reads."""
    read = {ob.identity for ob in box.dom.inside}
    return [
        other
        for other in operator_boxes(stage, direction)
        if read & {ob.identity for ob in other.cod.inside}
    ]


def printed_side(signature, word):
    """One side of a signature as it prints it, its entries separated by
    `, `."""
    return ", ".join(str(line) for side, line in signature.entries if side == word)


def printed_sections(card):
    """The sections of a printed card, read from its text as a reader reads
    it, each its heading line and its rows: the lines between the heavy line
    under the title and the heavy line that closes the card, without the
    blank lines and the light line before the footer; a heading stands at
    column zero, and a row is a line at the section's least indentation with
    the deeper lines after it."""
    lines = card.splitlines()
    heavy = [place for place, line in enumerate(lines) if line.startswith("━")]
    found = []
    for line in lines[heavy[0] + 1 : heavy[-1]]:
        if not line.strip() or line.startswith("─"):
            continue
        if not line.startswith(" "):
            found.append((line, []))
        else:
            found[-1][1].append(line)
    sections = []
    for heading, content in found:
        column = min((len(line) - len(line.lstrip(" ")) for line in content), default=0)
        rows = []
        for line in content:
            if not rows or len(line) - len(line.lstrip(" ")) == column:
                rows.append([line])
            else:
                rows[-1].append(line)
        sections.append((heading, tuple(tuple(row) for row in rows)))
    return sections


def one_line(row):
    """A row of a printed card on one line: its lines without their
    indentation, joined by one space."""
    return " ".join(line.strip() for line in row)


def with_single_spaces(text):
    """A text with every run of spaces written as one space, so that two
    texts are compared apart from the columns a card aligns them in."""
    return " ".join(text.split())


def printed_rules(card):
    """The rules of a printed card's `Rule` section as a reader reads them:
    each row on one line, a row that holds only the region a rule holds on,
    `on (m_f, m_h) ∈ …`, joined to the row before it, and every run of
    spaces written as one space."""
    rules = []
    for heading, held in printed_sections(card):
        if heading != "Rule":
            continue
        for row in held:
            text = with_single_spaces(one_line(row))
            if text.startswith("on ") and rules:
                rules[-1] = f"{rules[-1]} {text}"
            else:
                rules.append(text)
    return rules


def quoted_lines(card):
    """The file and the line numbers of the printed card's `Source` section,
    `("cons.bl", [22, 23])`: the file its heading names and the number each
    row begins with; None where the card prints no `Source` section."""
    for heading, held in printed_sections(card):
        if heading.startswith("Source"):
            return heading[len("Source") :].strip(), [int(row[0].split()[0]) for row in held]
    return None


def named_lines(lines):
    """The file and the line numbers that a row `lines` names,
    `("house_choice.bl", [18, 19, 22])` for `house_choice.bl 18–19, 22`, each
    run of numbers written out; None for the empty text."""
    if not lines:
        return None
    file, _, runs = lines.partition(" ")
    numbers = []
    for run in runs.split(", "):
        first, _, last = run.partition("–")
        numbers.extend(range(int(first), int(last or first) + 1))
    return file, numbers


def values_of(attrs, word):
    """The values of one row of a node or of a layer, in order: the row
    `word` where it has one value, and the rows `word 1`, `word 2`, … where
    it has several."""
    if word in attrs:
        return [attrs[word]]
    return [attrs[key] for key in attrs if re.fullmatch(rf"{word} \d+", key)]


def words_numbered_wrongly(attrs):
    """The words of the numbered rows `word 1`, `word 2`, … of a node or a
    layer whose numbers do not run from one with no gap in their order, that
    number one value alone, or that stand beside a row named by the word
    alone."""
    numbers = {}
    for key in attrs:
        found = re.fullmatch(r"(.+) (\d+)", key)
        if found:
            numbers.setdefault(found[1], []).append(int(found[2]))
    return [
        word
        for word, held in numbers.items()
        if held != list(range(1, len(held) + 1)) or len(held) == 1 or word in attrs
    ]


@pytest.fixture(scope="module")
def keeper_cons_methodized():
    """The durables keeper's consumption stage bound with the methods file
    beside it, whose lines of the endogenous grid method open its policy
    builder."""
    stage = stage_from_text((ROOT / KEEPER_CONS).read_text(encoding="utf-8"), KEEPER_CONS)
    stage.methodize(ROOT / KEEPER_CONS_METHODS)
    return stage


@pytest.fixture(scope="module")
def house_choice_methodized():
    """The house choice bound with the methods file beside it, whose
    derivative lines name the continuation coordinates of the keep
    branch."""
    stage = control_branching_stage("house_choice")
    stage.methodize(ROOT / HOUSE_CHOICE_METHODS)
    return stage


# The signature of a builder on its layer


@needs_viewer
def test_a_builders_layer_shows_first_the_signature_that_the_builder_prints(cons, view_of):
    """The policy layer of `cons` shows the two sides of the builder's
    signature as the builder prints them, before its feasible set and its
    parameter."""
    signature = cons.builder.bwd["policy"].signature()
    shown = graph_named(view_of(cons), "backward").groupNodeAttributes["policy"]
    assert list(shown) == ["inputs", "outputs", "feasible set", "parameter"]
    assert {side: shown[side] for side in ("inputs", "outputs")} == {
        "inputs": printed_side(signature, "in"),
        "outputs": printed_side(signature, "out"),
    }
    assert shown["inputs"] == "𝑉≻ : Xa → [−∞, ∞)"


@needs_viewer
def test_the_nodes_inputs_and_outputs_show_the_signature_of_the_whole_graph(cons, view_of):
    """The nodes `Inputs` and `Outputs` of a builders graph show the two
    sides of the graph's signature as the builders handle prints it."""
    nodes = {n.id: n for n in graph_named(view_of(cons), "backward").nodes}
    whole = cons.builder.bwd.signature()
    assert attributes(nodes["GraphInputs"]) == {"inputs": printed_side(whole, "in")}
    assert attributes(nodes["GraphOutputs"]) == {"outputs": printed_side(whole, "out")}
    assert attributes(nodes["GraphInputs"]) == {"inputs": "𝑉≻ : Xa → [−∞, ∞)"}


@needs_viewer
def test_a_sub_builders_layer_shows_the_outputs_that_the_sub_builder_prints(sa_savings, view_of):
    """The layer of the sub-builder `risk_ce` of `sa_savings` shows the
    outputs of its signature as the sub-builder prints them."""
    shown = graph_named(view_of(sa_savings), "backward").groupNodeAttributes
    risk = sa_savings.builder.bwd["cntn_to_dcsn"]["risk_ce"].signature()
    assert shown["cntn_to_dcsn/risk_ce"]["outputs"] == printed_side(risk, "out")


@needs_viewer
def test_a_sub_builders_layer_shows_its_signature_alone(sa_savings, view_of):
    """The layer of a sub-builder shows the two sides of its signature and
    no other row."""
    layers = graph_named(view_of(sa_savings), "backward").groupNodeAttributes
    # sa_savings has two sub-builders, its authored nodes
    assert any("/" in namespace for namespace in layers)
    for namespace, shown in layers.items():
        if "/" in namespace:
            assert list(shown) == ["inputs", "outputs"], namespace


@needs_viewer
def test_a_layer_shows_a_signature_that_the_printing_breaks_on_one_line(adjuster_saving, view_of):
    """The outputs of the policy layer of `adjuster_saving`, whose policy is
    a pair chosen from a set that the printing breaks at the width of a card,
    are the printed outputs of the signature with their line breaks and
    indentation removed."""
    signature = adjuster_saving.builder.bwd["policy"].signature()
    printed = [str(line) for side, line in signature.entries if side == "out"]
    # the printing breaks the outputs over several lines
    assert any("\n" in line for line in printed)
    layers = graph_named(view_of(adjuster_saving), "backward").groupNodeAttributes
    assert layers["policy"]["outputs"] == ", ".join(one_line(line.split("\n")) for line in printed)


@pytest.mark.parametrize(("name", "direction"), direction_rows("cons", "port", "ret_choice"))
def test_no_row_of_a_primitive_holds_a_line_break(name, direction, request):
    """No row of a primitive, as `box_attributes` gives it, holds a line
    break."""
    stage = request.getfixturevalue(name)
    for box in operator_boxes(stage, direction):
        attrs = box_attributes(stage, direction, box)
        assert all("\n" not in value for value in attrs.values()), box.name


@needs_viewer
@pytest.mark.parametrize(
    "name", stage_rows("cons_methodized_without_calibration", "adjuster_saving")
)
def test_no_value_of_the_view_holds_a_line_break(name, request, view_of):
    """No row of a node, of a port or of a layer of the view holds a line
    break."""
    for graph in view_of(request.getfixturevalue(name)).graphs:
        for node in graph.nodes:
            items = [node, *node.inputsMetadata, *node.outputsMetadata]
            assert all("\n" not in pair.value for item in items for pair in item.attrs), node.id
        for shown in (graph.groupNodeAttributes or {}).values():
            assert all("\n" not in value for value in shown.values())


# The rows of a primitive


@needs_viewer
def test_the_row_kind_of_a_node_is_the_kind_of_its_box(
    cons_methodized_without_calibration, view_of
):
    """The row `kind` of the node of each primitive is the kind of the
    operator of its box."""
    nodes = {
        n.id: n
        for n in graph_named(view_of(cons_methodized_without_calibration), "backward").nodes
    }
    for box in operator_boxes(cons_methodized_without_calibration, "backward"):
        node = nodes[str(box_identity(box))]
        assert attributes(node)["kind"] == box_identity(box).kind, box.name


@needs_viewer
def test_a_node_held_at_a_policy_shows_the_policy_in_its_row_policy(
    cons_methodized_without_calibration, view_of
):
    """The pullback of the decision builder, which is held at the policy 𝑐,
    shows 𝑐 in its row `policy`."""
    nodes = {
        n.id: n
        for n in graph_named(view_of(cons_methodized_without_calibration), "backward").nodes
    }
    assert attributes(nodes["cntn_to_dcsn:Pullback"])["policy"] == "𝑐"


@pytest.mark.parametrize(("name", "direction"), direction_rows("cons", "port", "ret_choice"))
def test_the_kernel_rows_of_a_primitive_are_the_lines_that_its_kernel_prints(
    name, direction, request
):
    """The rows `kernel` of a primitive are, one to a line, the lines that
    `kernel()` prints."""
    stage = request.getfixturevalue(name)
    for box in operator_boxes(stage, direction):
        attrs = box_attributes(stage, direction, box)
        assert "\n".join(values_of(attrs, "kernel")) == str(kernel(stage, box)), box.name


@pytest.mark.parametrize(("name", "direction"), direction_rows("cons", "port", "ret_choice"))
def test_the_rule_rows_of_a_primitive_are_the_rules_of_its_card(name, direction, request):
    """The rows `rule` of a primitive are the rules of its card's `Rule`
    section, each with the region it holds on, an evaluation leaving out a
    rule that a box before it states."""
    stage = request.getfixturevalue(name)
    for box in operator_boxes(stage, direction):
        identity = box_identity(box)
        expected = printed_rules(str(piece_handle(stage, direction, box).denote()))
        if identity.kind == "Evaluation":
            before = {
                rule
                for other in boxes_before(stage, direction, box)
                for rule in printed_rules(str(piece_handle(stage, direction, other).denote()))
            }
            expected = [rule for rule in expected if rule not in before]
        rules = values_of(box_attributes(stage, direction, box), "rule")
        assert ["".join(rule.split()) for rule in rules] == [
            "".join(rule.split()) for rule in expected
        ], identity


@pytest.mark.parametrize(
    ("name", "direction"),
    direction_rows(
        "cons", "port", "ret_choice", "cons_methodized_without_calibration", "house_choice"
    ),
)
def test_the_row_lines_names_the_file_and_the_lines_that_the_card_quotes(name, direction, request):
    """The row `lines` of a primitive names the file and the numbers of the
    lines that the `Source` section of its card quotes."""
    stage = request.getfixturevalue(name)
    for box in operator_boxes(stage, direction):
        card = str(piece_handle(stage, direction, box).denote())
        attrs = box_attributes(stage, direction, box)
        assert named_lines(attrs.get("lines")) == quoted_lines(card), box.name


@pytest.mark.parametrize(
    ("name", "direction"), direction_rows("cons_methodized_without_calibration", "house_choice")
)
def test_source_lines_answers_the_file_and_the_lines_that_the_printed_card_quotes(
    name, direction, request
):
    """`source_lines` answers, from the record of a card, the file and the
    numbers of the lines that the printed `Source` section of the card
    quotes."""
    stage = request.getfixturevalue(name)
    for box in operator_boxes(stage, direction):
        record = piece_handle(stage, direction, box).denote()
        quoted = quoted_lines(str(record))
        if quoted is not None:
            file, numbers = quoted
            assert source_lines(record) == tuple(SourceLine(file, n) for n in numbers)


@pytest.mark.parametrize(("name", "direction"), direction_rows("ret_choice", "house_choice"))
def test_a_primitive_shows_no_row_where(name, direction, request):
    """No primitive shows a row `where`, although the cards of the primitives
    print a `Where` section."""
    stage = request.getfixturevalue(name)
    cards = [
        str(piece_handle(stage, direction, box).denote())
        for box in operator_boxes(stage, direction)
    ]
    # the cards of the primitives print a `Where` section
    assert any(heading == "Where" for card in cards for heading, _ in printed_sections(card))
    for box in operator_boxes(stage, direction):
        assert not values_of(box_attributes(stage, direction, box), "where"), box.name


@pytest.mark.parametrize(("name", "direction"), direction_rows("cons", "port", "ret_choice"))
def test_a_primitive_shows_no_call_that_prints_its_card(name, direction, request):
    """No primitive shows a row `card`, the call that prints its card."""
    stage = request.getfixturevalue(name)
    for box in operator_boxes(stage, direction):
        assert "card" not in box_attributes(stage, direction, box), box.name


@pytest.mark.parametrize("name", stage_rows("cons", "port", "ret_choice"))
def test_a_primitive_shows_none_of_the_conditions_that_its_card_prints(name, request):
    """No primitive of a backward builders graph shows a row of the
    `Conditions` section that its card prints."""
    stage = request.getfixturevalue(name)
    conditions = 0
    for box in operator_boxes(stage, "backward"):
        attrs = box_attributes(stage, "backward", box)
        assert not [key for key in attrs if key.startswith("condition")], box.name
        card = str(piece_handle(stage, "backward", box).denote())
        conditions += sum(
            len(held)
            for heading, held in printed_sections(card)
            if heading.split("  ")[0] == "Conditions"
        )
    # the cards print conditions, which the view leaves out
    assert conditions > 0


def test_an_evaluation_omits_the_rule_of_the_box_before_it_although_printed_differently(
    cons_obs,
):
    """The policy evaluation of `cons_obs` leaves out the rule that the box
    before it states, although the two cards print the names of its region
    differently."""
    box = box_named(cons_obs, "backward", "policy:Evaluation")
    evaluation = box_attributes(cons_obs, "backward", box)
    assert values_of(evaluation, "rule") == ["𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)"]


def test_the_decision_aggregation_of_cons_shows_its_rows_in_reading_order_with_their_values(
    cons,
):
    """The aggregation of the decision builder of `cons` shows its kind, its
    policy, its rule, the two lines of its kernel and its line of the file,
    in that order."""
    aggregation = box_named(cons, "backward", "cntn_to_dcsn:Aggregation")
    attrs = box_attributes(cons, "backward", aggregation)
    # the order an economist reads: what the box is, the policy it is held
    # at, the rules it states, the function it computes, and the lines; a
    # method bound within the box stands before the lines
    assert list(attrs) == ["kind", "policy", "rule", "kernel 1", "kernel 2", "lines"]
    assert attrs["kind"] == "Aggregation"
    assert values_of(attrs, "kernel") == [
        "𝐺 of cntn_to_dcsn: 𝐺(V≻, m_d, c) = 𝑢(c) + V≻",
        "output V; unused m_d",
    ]
    assert values_of(attrs, "rule") == [
        "𝑉(m_d) = 𝑢(𝑐(m_d)) + 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))",
    ]
    assert attrs["lines"] == "cons.bl 21"


def test_a_rule_that_the_card_breaks_over_several_lines_is_one_row(ret_choice):
    """Each rule of the push-forward of the branching stage `ret_choice`,
    which its card breaks over three lines, is one row on one line."""
    pushforward = box_named(ret_choice, "forward", "dcsn_to_cntn:Pushforward")
    attrs = box_attributes(ret_choice, "forward", pushforward)
    assert values_of(attrs, "rule") == [
        "μ_work≻(B) = μ({a_d ∈ ℝ₊ | 𝑑(a_d) = work ∧ 𝑔_work≻(a_d) ∈ B})",
        "μ_retire≻(B) = μ({a_d ∈ ℝ₊ | 𝑑(a_d) = retire ∧ 𝑔_retire≻(a_d) ∈ B})",
    ]


def test_a_section_of_one_row_or_a_kernel_of_one_line_is_named_by_its_word_alone(ret_choice):
    """The rule section of one row and the kernel of one line of the argmax
    of `ret_choice` are each one row named by its word alone."""
    argmax = box_named(ret_choice, "backward", "policy.choice:Argmax")
    attrs = box_attributes(ret_choice, "backward", argmax)
    assert attrs["rule"] == (
        "𝑑(a_d) ∈ argmax_{d ∈ {work, retire}} [(𝑉_w≻(𝑔_work≻(a_d)) − δ, 𝑉_r≻(𝑔_retire≻(a_d)))[d]]"
    )
    assert attrs["kernel"] == str(kernel(ret_choice, argmax))
    assert not {"rule 1", "kernel 1"} & set(attrs)


def test_a_primitive_whose_card_prints_no_rule_shows_no_rule(keeper_cons_methodized):
    """The identification `c = c[>]` of the keeper's consumption stage, the
    one primitive of the stages of the applications whose card prints no
    `Rule` section, shows no row `rule`."""
    stage = keeper_cons_methodized
    box = box_named(stage, "backward", "policy.cons_choice:Pullback")
    # the card prints no `Rule` section
    assert printed_rules(str(piece_handle(stage, "backward", box).denote())) == []
    assert not values_of(box_attributes(stage, "backward", box), "rule")


def test_an_identification_shows_the_equation_and_the_unknowns_of_its_kernel(
    keeper_cons_methodized,
):
    """The identification `c = c[>]` of the keeper's consumption stage shows
    the two lines of its kernel, its equation and its unknowns."""
    stage = keeper_cons_methodized
    box = box_named(stage, "backward", "policy.cons_choice:Pullback")
    attrs = box_attributes(stage, "backward", box)
    assert values_of(attrs, "kernel") == ["equation c = c[>]", "unknowns c"]


@pytest.mark.parametrize(("name", "direction"), direction_rows(*NUMBERED_STAGES))
def test_several_values_of_one_row_of_a_primitive_are_numbered_from_one(name, direction, request):
    """The values of one row of a primitive are numbered from one with no gap
    where they are several, and one value is named by the word of the row
    alone."""
    stage = request.getfixturevalue(name)
    shown = [box_attributes(stage, direction, box) for box in operator_boxes(stage, direction)]
    assert [words for words in map(words_numbered_wrongly, shown) if words] == []


@needs_viewer
@pytest.mark.parametrize("name", stage_rows(*NUMBERED_STAGES))
def test_several_values_of_one_row_of_a_layer_are_numbered_from_one(name, request, view_of):
    """The values of one row of a layer are numbered from one with no gap
    where they are several, and one value is named by the word of the row
    alone."""
    view = view_of(request.getfixturevalue(name))
    shown = [
        rows for graph in builders_graphs(view) for rows in graph.groupNodeAttributes.values()
    ]
    assert [words for words in map(words_numbered_wrongly, shown) if words] == []


@pytest.mark.parametrize(
    "name",
    [
        *stage_rows("cons", "port", "ret_choice", "cons_methodized_without_calibration"),
        pytest.param("sa_savings", id="sa_savings, a builder that holds sub-builders"),
    ],
)
def test_card_sections_answers_the_sections_that_the_card_prints(name, request):
    """The sections that `card_sections` answers for every card of a stage,
    each builder's and each primitive's, are those that the printed card
    shows, each under a heading that begins with the word of its label."""
    stage = request.getfixturevalue(name)
    records = [stage.denote()]
    for word in ("bwd", "fwd"):
        graph = getattr(stage.builder, word)
        for builder in graph.list():
            records.append(graph[builder].denote())
            pieces = graph[builder].primitives
            records.extend(pieces[key].denote() for key in pieces.list())
    for record in records:
        sections = card_sections(record)
        assert [(s.heading, s.rows) for s in sections] == printed_sections(str(record))
        assert all(s.heading.startswith(WORDS[s.label]) for s in sections)


# The methods of a bound version


@needs_viewer
@pytest.mark.parametrize("name", stage_rows("cons", "port", "ret_choice"))
def test_a_symbolic_version_shows_no_method(name, request, view_of):
    """No node of the view of a version that no methods file binds shows a
    method, a grid or a handler."""
    plain = view_of(request.getfixturevalue(name))
    assert all(
        not {"method", "handler", "grid"} & set(attributes(n))
        for graph in plain.graphs
        for n in graph.nodes
    )


@needs_viewer
def test_a_method_bound_within_a_primitive_stands_in_the_rows_of_its_node(
    cons_methodized_without_calibration, view_of
):
    """The method bound within the evaluation of the decision builder stands
    in the rows of its node: its word, its grid, its handler and the settings
    that its grid names."""
    nodes = {
        n.id: n
        for n in graph_named(view_of(cons_methodized_without_calibration), "backward").nodes
    }
    evaluation = attributes(nodes["cntn_to_dcsn:Evaluation"])
    assert evaluation["method"] == "!Linear"
    assert evaluation["grid"] == "!Cartesian(m_d=(m_min, m_max, n_m))"
    assert evaluation["handler"] == "cons-port:_make_interp"
    assert values_of(evaluation, "setting") == [
        str(cons_methodized_without_calibration.settings[name])
        for name in ("m_min", "m_max", "n_m")
    ]


@needs_viewer
def test_a_method_bound_at_a_builder_stands_on_its_layer_and_not_on_its_evaluation(
    cons_methodized_without_calibration, view_of
):
    """The method bound at the policy builder stands on the builder's layer,
    with its handler and its grid, and not on the node of its evaluation."""
    backward = graph_named(view_of(cons_methodized_without_calibration), "backward")
    nodes = {n.id: n for n in backward.nodes}
    policy = backward.groupNodeAttributes["policy"]
    assert (policy["method"], policy["handler"], policy["grid"]) == (
        "!egm",
        "cons-port:egm",
        "!Cartesian(a=(a_min, a_max, n_a))",
    )
    assert "method" not in attributes(nodes["policy:Evaluation"])


@needs_viewer
def test_the_method_bound_at_a_forward_builder_stands_on_its_layer(
    cons_methodized_without_calibration, view_of
):
    """The method `!deterministic`, bound at the forward arrival builder,
    stands on the builder's layer."""
    forward = graph_named(
        view_of(cons_methodized_without_calibration), "forward"
    ).groupNodeAttributes
    assert forward["arvl_to_dcsn"]["method"] == "!deterministic"


@needs_viewer
def test_a_handler_bound_with_no_method_word_stands_on_its_layer_alone(
    cons_methodized_without_calibration, view_of
):
    """The handler of the forward decision builder, which takes no method
    word, stands on the builder's layer with no row `method`."""
    forward = graph_named(
        view_of(cons_methodized_without_calibration), "forward"
    ).groupNodeAttributes
    assert forward["dcsn_to_cntn"]["handler"] == "cons-port:transition_fwd"
    assert "method" not in forward["dcsn_to_cntn"]


@needs_viewer
def test_a_configured_version_shows_on_an_evaluation_its_grid_and_the_settings_it_names(
    cons_configured, view_of
):
    """The evaluation of the decision builder of configured `cons` shows its
    grid and the three settings that the grid names, with their values, as
    `stage.settings` prints them."""
    graph = graph_named(view_of(cons_configured), "backward")
    evaluation = next(n for n in graph.nodes if n.id == "cntn_to_dcsn:Evaluation")
    attrs = attributes(evaluation)
    assert attrs["grid"] == "!Cartesian(m_d=(m_min, m_max, n_m))"
    assert values_of(attrs, "setting") == [
        str(cons_configured.settings[name]) for name in ("m_min", "m_max", "n_m")
    ]
    assert "m_min = 0.01 : Xm" in attrs["setting 1"]
    assert "n_m = 8000 : ℕ" in attrs["setting 3"]


# The rows `where` of a builder's layer


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), direction_rows("ret_choice", "house_choice"))
def test_a_builders_layer_shows_the_where_rows_of_the_builders_card(
    name, direction, request, view_of
):
    """The rows `where` of each builder's layer are the rows of the `Where`
    section of the builder's card, the local abbreviations of the rules that
    the cards of its primitives repeat."""
    stage = request.getfixturevalue(name)
    layers = graph_named(view_of(stage), direction).groupNodeAttributes
    word = "bwd" if direction == "backward" else "fwd"
    expected = {
        namespace: [
            one_line(row)
            for heading, held in printed_sections(
                str(getattr(stage.builder, word)[namespace].denote())
            )
            if heading == "Where"
            for row in held
        ]
        for namespace in layers
    }
    # the card of a builder prints a `Where` section
    assert any(expected.values())
    for namespace, shown in layers.items():
        assert values_of(shown, "where") == expected[namespace], namespace


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), direction_rows("ret_choice", "house_choice"))
def test_every_where_row_of_a_primitives_card_stands_on_the_layer_of_its_builder(
    name, direction, request, view_of
):
    """Every row that the card of a primitive prints under `Where` stands on
    the layer of its builder, apart from the columns it is aligned in."""
    stage = request.getfixturevalue(name)
    layers = graph_named(view_of(stage), direction).groupNodeAttributes
    boxes = operator_boxes(stage, direction)
    cards = {box.name: str(piece_handle(stage, direction, box).denote()) for box in boxes}
    # the cards of the primitives print a `Where` section
    assert any(
        heading == "Where" for card in cards.values() for heading, _ in printed_sections(card)
    )
    for box in boxes:
        card = cards[box.name]
        builder = {
            with_single_spaces(row) for row in values_of(layers[box_identity(box).block], "where")
        }
        for heading, held in printed_sections(card):
            if heading == "Where":
                assert {with_single_spaces(one_line(row)) for row in held} <= builder, box.name


@needs_viewer
def test_the_continuation_coordinates_of_a_branch_stand_once_under_the_row_of_its_law(
    house_choice_methodized, view_of
):
    """The two continuation coordinates of the keep branch of the house
    choice, which the derivative lines of its methods file name, stand once
    on the layer of the decision builder, under the row of the branch's law
    of motion."""
    layers = graph_named(view_of(house_choice_methodized), "backward").groupNodeAttributes
    assert values_of(layers["cntn_to_dcsn"], "where") == [
        "𝑔_keep≻    : ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊,  𝑔_keep≻(m_f, m_h) = 𝑔≻(m_f, m_h, keep)",
        "(w_kp, h_kp) = 𝑔_keep≻(m_f, m_h)",
        "𝑔_adjust≻  : ℝ₊₊ × ℝ₊₊ → ℝ₊₊,  𝑔_adjust≻(m_f, m_h) = 𝑔≻(m_f, m_h, adjust)",
    ]


# The parameters, the settings and the feasible sets of a builder's layer


@needs_viewer
def test_a_builders_layer_lists_the_parameter_that_its_primitives_read(cons, view_of):
    """Each builder's layer of `cons` lists the parameter ρ, as `stage.par`
    prints it, where its primitives read it: the decision builder and the
    policy builder read it through 𝑢 and 𝑑𝑢, and the arrival builder, whose
    rule is the identity V[<] = V, reads none."""
    layers = graph_named(view_of(cons), "backward").groupNodeAttributes
    assert layers["cntn_to_dcsn"]["parameter"] == str(cons.par["ρ"]) == "ρ : [1, inf), unbound"
    assert layers["policy"]["parameter"] == str(cons.par["ρ"])
    assert not values_of(layers["dcsn_to_arvl"], "parameter")


@needs_viewer
def test_a_layer_lists_the_parameters_read_through_a_law_of_motion_in_the_files_order(
    house_choice, view_of
):
    """The arrival builder's layer of the house choice lists the parameters
    that its primitives read through a law of motion and a distribution, in
    the order in which the file declares them."""
    layers = graph_named(view_of(house_choice), "backward").groupNodeAttributes
    assert values_of(layers["dcsn_to_arvl"], "parameter") == [
        "r : ℝ₊, unbound",
        "W : ℝ₊₊, unbound",
        "η_lo : ℝ₊₊, unbound",
        "η_hi : ℝ₊₊, unbound",
    ]


@needs_viewer
def test_no_layer_of_a_symbolic_version_lists_a_setting(cons, view_of):
    """No layer of the backward builders graph of a version that no
    configuration binds lists a setting."""
    layers = graph_named(view_of(cons), "backward").groupNodeAttributes
    assert not [namespace for namespace, shown in layers.items() if values_of(shown, "setting")]


@needs_viewer
def test_the_layer_of_a_calibrated_version_lists_the_value_of_its_parameter(
    cons_configured, view_of
):
    """The decision builder's layer of `cons` calibrated, methodized and
    configured lists the value of the parameter ρ as `stage.par` prints
    it."""
    layers = graph_named(view_of(cons_configured), "backward").groupNodeAttributes
    assert layers["cntn_to_dcsn"]["parameter"] == str(cons_configured.par["ρ"])
    assert layers["cntn_to_dcsn"]["parameter"] == "ρ = 6.0 : [1, inf)"


@needs_viewer
def test_every_builders_layer_of_a_configured_version_lists_every_setting_it_binds(
    cons_configured, view_of
):
    """Every builder's layer of configured `cons` lists every setting that
    the version binds, as `stage.settings` prints it, a setting that no
    method names among them and none of its own for a method bound at the
    builder."""
    bound = view_of(cons_configured)
    settings = [str(cons_configured.settings[name]) for name in cons_configured.settings]
    # a setting that no method names
    assert "n_k = 800" in settings
    # a method bound at a builder, which lists no setting of its own there
    forward = graph_named(bound, "forward")
    assert forward.groupNodeAttributes["arvl_to_dcsn"]["method"] == "!deterministic"
    for graph in builders_graphs(bound):
        for namespace, shown in graph.groupNodeAttributes.items():
            assert values_of(shown, "setting") == settings, namespace


@needs_viewer
@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("cons", ["Γ(x : ℝ₊₊) := (0, x]"], id="cons, one control"),
        pytest.param(
            "adjuster_saving",
            ["Γ_c(x : ℝ₊₊) := (0, x]", "Γ_h(x : ℝ₊) := (0, x/(1 + τ)]"],
            id="adjuster_saving, two controls",
        ),
        pytest.param("house_choice", [], id="house_choice, a choice over a finite set"),
    ],
)
def test_the_policy_layer_lists_the_definition_of_each_feasible_set_that_its_policy_names(
    name, expected, request, view_of
):
    """The policy layer lists the definition of the correspondence from which
    each control of the policy is chosen, and none for a choice over a finite
    set."""
    backward = graph_named(view_of(request.getfixturevalue(name)), "backward")
    assert values_of(backward.groupNodeAttributes["policy"], "feasible set") == expected


@needs_viewer
def test_the_feasible_set_of_cons_is_listed_as_its_stage_file_writes_it(cons, view_of):
    """The feasible set that the policy layer of `cons` lists is the line of
    `cons.bl` that declares it."""
    layers = graph_named(view_of(cons), "backward").groupNodeAttributes
    source = corpus_text("cons")
    assert layers["policy"]["feasible set"] in source.splitlines()


@needs_viewer
def test_only_the_layer_of_the_policy_builder_lists_a_feasible_set(cons, view_of):
    """Of the layers of the backward builders graph of `cons`, the policy
    layer alone lists a feasible set."""
    layers = graph_named(view_of(cons), "backward").groupNodeAttributes
    assert [namespace for namespace, shown in layers.items() if "feasible set" in shown] == [
        "policy"
    ]
