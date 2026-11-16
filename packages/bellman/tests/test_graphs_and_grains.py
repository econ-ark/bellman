"""The graphs of a stage at each grain: their boxes, wires, ports, bubbles,
signatures and denotations, and the diagnostics and obligations of a stage."""

import gc
import re
import weakref
from collections import Counter, defaultdict
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest
from application_files import COPIED_FILES_FOLDER, CORPUS, ROOT, stage_file_id
from discopy.frobenius import Box, Bubble, Hypergraph, Spider, Ty
from snapshot.record import ELABORATED_FILES
from stage_builders import stage_from_file, stage_from_text
from stage_graphs import (
    boxes_with_wires,
    graphs_inside,
    graphs_of,
    interior_of,
    port_wires,
    wire_sorts,
)
from stage_texts import (
    TWO_PARENT_SHOCKS_TEXT,
    UNADMITTED_FAMILY_AT_ARRIVAL,
    Y_IDENTITY,
    bundles_text,
    corpus_text,
    two_nodes_text_with_changes,
)
from two_sets import one_row_by_default

from bellman.display.drawing import to_drawing
from bellman.fold.stage_names import StageNames
from bellman.native.hypergraphs import copy_native
from bellman.native.records import Sort
from bellman.refusal_examples import TWO_NODES
from bellman.refusals import NotConstructed
from bellman.stage import elaborate_stage, load_stage
from bellman.stage.carriers import bound_variable_number
from bellman.stage.grains import graph_of, kind_of, wire_table
from bellman.syntax import terms
from bellman.typing import typed_expressions

# The roles of the fields that a line of a backward initial diagram reads at
# the perch of its own output, and that no box writes. A field of one of
# these roles at that perch is a coordinate of the function that the line
# writes: in the builders graphs of `cons_obs.bl`, the sort of
# `cons_obs:function:cntn:c` has the coordinates `cons_obs:cntn:a` and
# `cons_obs:cntn:μ`.
ROLES_READ_WITHOUT_A_WRITER = ("state", "multiplier")


# the law of the shock `y` as `cons_savings_iid.bl` writes it, which two
# tests replace by a finite mixture
CONS_SAVINGS_IID_LAW = "Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_y, σ_y)))"


# the lines of the block `dcsn_to_arvl` of `BUNDLES` with the arrival value
# divided by `β - R` inside its expectation
ARRIVAL_VALUE_DIVIDED_BY_BETA_MINUS_R = (
    "    V[<]     = E_{y,z}(V/(β - R))   :: [id=value]\n"
    "    D_{k}V[<] = E_{y,z}(R*D_{k_d}V)  :: [id=marginal]\n"
)


# A label of a measure's wire that is followed by coordinates: `μ`, then a
# subscript `_` with the measure's field where it has one, then a perch mark
# where it has one, then an opening parenthesis.
MEASURE_LABEL_WITH_COORDINATES = re.compile(r'μ(?:_[^\s"(]+)?[≺∼≻]?\(')


# The label of a measure's wire in a drawing: a label that opens with `μ`,
# followed by a tooltip that names the identity of a measure.
MEASURE_WIRE_LABEL = re.compile(r'label="μ[^"]*" tooltip="[^"]*:measure:')


# The bases at which the test of `bound_variable_number` binds coordinates,
# of the size of those that the package gives the function, which range from
# 100 to 800, with 101 beside 100: two coordinates at the bases 100 and 101
# receive one number unless each base is stretched by more than the number of
# ports.
COORDINATE_BASES = (100, 101, 130, 150, 200, 300, 310, 500, 600, 700)


def repeated_wire_identities(graph, name):
    """Each identity that two or more wires carry, in the graph or in a graph
    inside one of its bubbles. The package wires a graph by identity, with
    one wire for each identity (`connect` of
    `bellman/graphs/wire_sorts.py`)."""
    violations = []
    for where, held in graphs_inside(graph, name):
        counts = Counter(str(sort.identity) for sort in wire_sorts(held))
        violations += [
            f"{where}: {count} wires carry the identity {identity}"
            for identity, count in counts.items()
            if count > 1
        ]
    return violations


def wires_at_no_port(graph, name):
    """Each wire that stands at no input or output of the graph and at no
    input or output of a box, in the graph or in a graph inside one of its
    bubbles. The package makes a wire only for an identity that it meets at
    an input or an output of the graph or of a box (`connect` of
    `bellman/graphs/wire_sorts.py`)."""
    violations = []
    for where, held in graphs_inside(graph, name):
        sorts = wire_sorts(held)
        inputs, outputs = port_wires(held)
        at_a_port = set(inputs) | set(outputs)
        for _, read, written in boxes_with_wires(held):
            at_a_port |= set(read) | set(written)
        violations += [
            f"{where}: the wire of {sorts[wire].identity} stands at no port"
            for wire in range(len(sorts))
            if wire not in at_a_port
        ]
    return violations


def wires_read_and_not_written(graph, name, roles_read_without_a_writer=()):
    """Each wire that a box reads, that no box writes and that the graph does
    not take as an input, in the graph or in a graph inside one of its
    bubbles. A field whose role is among `roles_read_without_a_writer` and
    that stands at the perch of one of the reading box's outputs is no
    violation: it is a coordinate of the function that the box writes. The
    package gives a builder, a builders graph and a group of lines marked
    `!node` as inputs their declared inputs and each wire that their boxes
    read and none of them writes (`captures` and `group_inputs_outputs` of
    `bellman/graphs/wire_sorts.py`), and gives an initial diagram and its
    blocks the inputs that the headers of the blocks declare."""
    violations = []
    for where, held in graphs_inside(graph, name):
        sorts = wire_sorts(held)
        inputs, _ = port_wires(held)
        boxes = boxes_with_wires(held)
        written = set(inputs).union(*(outputs for _, _, outputs in boxes))
        for box, read, outputs in boxes:
            perches = {sorts[wire].perch for wire in outputs}
            for wire in read:
                sort = sorts[wire]
                excused = sort.role in roles_read_without_a_writer and sort.perch in perches
                if wire not in written and not excused:
                    violations.append(
                        f"{where}: {box.name} reads {sort.identity}, which no box writes"
                    )
    return violations


def grains_with_other_inputs_or_outputs(graphs):
    """Each graph among `graphs`, given as `graphs_of` yields them, whose
    ordered inputs or ordered outputs differ from those of the first graph
    of the same level and direction. Two sorts are equal when their
    identities are equal. The package builds the graph of one level and
    direction at every grain on one list of inputs and one list of outputs
    (`builders_graph_by_grain` of `bellman/graphs/builders_graphs.py` and
    `initial_diagram_at_grains` of `bellman/graphs/initial_diagrams.py`)."""
    first = {}
    violations = []
    for level, direction, grain, graph in graphs:
        first_grain, first_graph = first.setdefault((level, direction), (grain, graph))
        for side, ours, theirs in (
            ("inputs", graph.dom, first_graph.dom),
            ("outputs", graph.cod, first_graph.cod),
        ):
            if ours != theirs:
                violations.append(
                    f"{level} {direction} {grain}: other {side} than the {first_grain} grain"
                )
    return violations


def bubbles_with_other_inputs_or_outputs(graph, name):
    """Each bubble whose ordered inputs or ordered outputs differ from those
    of the graph inside it, in the graph or in a graph inside one of its
    bubbles. Two sorts are equal when their identities are equal. The
    package builds each bubble and the graph inside it on one list of inputs
    and one list of outputs (`_builder_bubble` and `interior_at` of
    `bellman/graphs/builders_graphs.py`, `block_bubble` and
    `grouped_statements` of `bellman/graphs/initial_diagrams.py`)."""
    violations = []
    for where, held in graphs_inside(graph, name):
        for box in held.boxes:
            interior = interior_of(box)
            if interior is None:
                continue
            for side, ours, theirs in (
                ("inputs", box.dom, interior.dom),
                ("outputs", box.cod, interior.cod),
            ):
                if ours != theirs:
                    violations.append(
                        f"{where}: the bubble {box.name} has other {side} than the graph inside it"
                    )
    return violations


def identities_with_two_sorts(graphs):
    """Each identity that wires carry with sorts of two or more different
    `repr` among `graphs`, given as `graphs_of` yields them, the graphs
    inside bubbles included. An identity carries one typing, which the
    package checks only while it types a stage (`type_stage` of
    `bellman/typing/context.py`), so the graphs of the grains that it builds
    after the typing need this property."""
    sorts = defaultdict(set)
    for level, direction, grain, graph in graphs:
        if isinstance(graph, NotConstructed):
            continue
        for _, held in graphs_inside(graph, f"{level} {direction} {grain}"):
            for sort in wire_sorts(held):
                sorts[str(sort.identity)].add(repr(sort))
    return [
        f"the identity {identity} carries {len(printed_sorts)} sorts"
        for identity, printed_sorts in sorts.items()
        if len(printed_sorts) > 1
    ]


def without_box(graph, name):
    """The hypergraph `graph` without its box called `name`, the box's wires
    left in place."""
    kept = [index for index, box in enumerate(graph.boxes) if box.name != name]
    return Hypergraph(
        graph.dom,
        graph.cod,
        tuple(graph.boxes[index] for index in kept),
        (graph.dom_wires, tuple(graph.box_wires[index] for index in kept), graph.cod_wires),
    )


@pytest.fixture(scope="module")
def stage_of_a_family_not_admitted():
    """The stage of `UNADMITTED_FAMILY_AT_ARRIVAL`, whose shock `z` is drawn
    from the family `Weird`, for which the package constructs no forward
    measure."""
    return stage_from_text(UNADMITTED_FAMILY_AT_ARRIVAL)


@pytest.fixture(scope="module")
def stage_with_an_external_call_in_its_utility(cons_with_egm_lines_text):
    """The consumption stage with an explicit policy, whose utility calls
    `neverdef`, a function that no definition of the stage declares."""
    return stage_from_text(cons_with_egm_lines_text.replace("c^(1-ρ)/(1-ρ)", "neverdef(c)/(1-ρ)"))


@pytest.fixture(scope="module")
def stage_with_an_external_call_in_a_shock_law():
    """The stage of `TWO_NODES`, whose backward block holds two lines marked
    `!node`, with its shock `y` drawn from `N(log(1),1)`, a law whose mean
    calls `log`, which no definition of the stage declares."""
    # the last argument, 1, replaces the first law of the text alone, the law
    # of `y`
    return stage_from_text(TWO_NODES.replace("N(0,1)", "N(log(1),1)", 1))


@pytest.fixture(scope="module")
def stage_with_a_shock_of_an_external_family():
    """The stage of `TWO_NODES`, whose backward block holds two lines marked
    `!node`, with its shock `y` drawn from `Density(0,1)`, a family that
    neither the stage nor the package defines."""
    return stage_from_text(
        two_nodes_text_with_changes(declarations="y ~ Density(0,1)\nz : ℝ\nz ~ N(0,1)\n"),
        "external.bl",
    )


@pytest.fixture(scope="module")
def bundle_stage():
    """The stage of `BUNDLES`, whose block `dcsn_to_arvl` states a value and
    its derivative, each an expectation over the shocks `y` and `z`, and
    whose policy chooses over the correspondence `Γ` that the stage
    defines."""
    return stage_from_text(bundles_text(), "bundles.bl")


@pytest.fixture(scope="module")
def two_parent_shocks_stage():
    """The stage of `TWO_PARENT_SHOCKS_TEXT`, whose shock laws carry
    descriptions: `s` a Markov chain, and `θ` a law that reads `s` through a
    selection by a key."""
    return stage_from_text(TWO_PARENT_SHOCKS_TEXT, "selected_law.bl")


@pytest.fixture(scope="module")
def stage_with_a_finite_mixture():
    """The stage of `cons_savings_iid.bl` with its shock `y` drawn from the
    finite mixture `Mixture((0.25, 0), (0.75, 1))`."""
    return stage_from_text(
        corpus_text("cons_savings_iid").replace(
            CONS_SAVINGS_IID_LAW, "Mixture((0.25, 0), (0.75, 1))"
        )
    )


@pytest.fixture(scope="module")
def backward_drawing_of_sa_savings(sa_savings):
    """The source of the drawing of the backward builders graph of
    `sa_savings.bl` at the sub-builder grain."""
    return to_drawing(sa_savings.builder.bwd.sub_builders.graph).source


@pytest.fixture(scope="module")
def forward_drawings(sa_savings, tenure):
    """The source of the drawing of the forward builders graph at the
    primitive grain, of `sa_savings.bl` and of `tenure.bl`, by the name of
    the fixture of each stage."""
    return {
        name: to_drawing(stage.builder.fwd.primitives.graph).source
        for name, stage in (("sa_savings", sa_savings), ("tenure", tenure))
    }


@pytest.fixture
def answer_of_a_collected_stage():
    """The answer of `denote()` of the backward builder `cntn_to_dcsn` of a
    stage of `cons.bl`, held after the stage is deleted and collected, with
    a weak reference to the stage and the inputs, outputs, pieces and hash of
    the first input wire that the answer gave before the deletion."""
    stage = stage_from_text(corpus_text("cons"), "detached.bl")
    answer = stage.builder.bwd["cntn_to_dcsn"].denote()
    held = SimpleNamespace(
        stage=weakref.ref(stage),
        answer=answer,
        inputs=answer.inputs,
        outputs=answer.outputs,
        pieces=answer.pieces,
        wire=answer.inputs[0],
        wire_hash=hash(answer.inputs[0]),
    )
    del stage
    gc.collect()
    return held


# --- the query of a graph ---


@pytest.mark.parametrize(
    ("level", "direction", "grain", "message"),
    [
        pytest.param(
            "diagram",
            "backward",
            "builder",
            "level must be 'initial' or 'builders'",
            id="an-unknown-level",
        ),
        pytest.param("builders", None, "builder", "require direction=", id="no-direction"),
        pytest.param(
            "builders", "backward", "fine", "grain must be one of", id="an-unknown-grain"
        ),
    ],
)
def test_graph_of_refuses_a_level_a_direction_or_a_grain_that_names_no_graph(
    cons, level, direction, grain, message
):
    """`graph_of` refuses with a `ValueError` a level, a direction or a grain
    that names no graph of a stage."""
    with pytest.raises(ValueError, match=message):
        graph_of(cons, level, direction, grain)


def test_a_forward_builders_graph_that_the_package_refuses_raises_not_constructed(
    stage_of_a_family_not_admitted,
):
    """Reading the forward builders graph of a stage whose shock is drawn from
    a family that the package does not admit raises `NotConstructed`."""
    with pytest.raises(NotConstructed):
        stage_of_a_family_not_admitted.builder.fwd.graph


# --- the labels of the wires in a drawing ---


@pytest.mark.parametrize(
    ("identity", "label"),
    [
        pytest.param(
            "sa_savings:function:cntn:V", "𝑉≻(a)", id="continuation-value-at-an-input-of-the-graph"
        ),
        pytest.param(
            "sa_savings:function:dcsn:CE",
            "𝐶𝐸(m_d, ν)",
            id="certainty-equivalent-at-a-state-and-a-shock-between-two-boxes",
        ),
        pytest.param(
            "sa_savings:function:dcsn:AMB",
            "𝐴𝑀𝐵(m_d)",
            id="ambiguity-certainty-equivalent-at-a-state-between-two-boxes",
        ),
        pytest.param(
            "sa_savings:function:dcsn:V", "𝑉(m_d)", id="decision-value-at-an-output-of-the-graph"
        ),
    ],
)
def test_a_function_wire_is_labeled_by_its_function_at_the_coordinates_of_its_sort(
    backward_drawing_of_sa_savings, identity, label
):
    """In the drawing of the backward builders graph of `sa_savings.bl` at the
    sub-builder grain, the wire of a function carries as its label and in its
    tooltip the function at the coordinates that its sort holds."""
    assert f'label="{label}" tooltip="{identity} — {label}"' in backward_drawing_of_sa_savings


@pytest.mark.parametrize(
    ("stage_name", "identity", "label"),
    [
        pytest.param(
            "sa_savings",
            "sa_savings:measure:dcsn",
            "μ",
            id="sa-savings-decision-measure-at-an-input-of-the-graph",
        ),
        pytest.param(
            "sa_savings",
            "sa_savings:measure:cntn",
            "μ≻",
            id="sa-savings-continuation-measure",
        ),
        pytest.param("tenure", "tenure:measure:arvl", "μ≺", id="tenure-arrival-measure"),
        pytest.param(
            "tenure",
            "tenure:measure:dcsn",
            "μ",
            id="tenure-decision-measure-between-two-boxes",
        ),
        pytest.param(
            "tenure",
            "tenure:measure:cntn:keep",
            "μ_keep≻",
            id="tenure-continuation-measure-of-the-branch-keep",
        ),
        pytest.param(
            "tenure",
            "tenure:measure:cntn:adjust",
            "μ_adjust≻",
            id="tenure-continuation-measure-of-the-branch-adjust",
        ),
    ],
)
def test_a_measure_wire_is_labeled_mu_with_its_field_and_its_perch_mark(
    forward_drawings, stage_name, identity, label
):
    """In the drawing of the forward builders graph at the primitive grain,
    the wire of a measure carries as its label and in its tooltip `μ`, with
    its field as a subscript and the mark of its perch where it has them."""
    assert f'label="{label}" tooltip="{identity} — {label}"' in forward_drawings[stage_name]


@pytest.mark.parametrize(
    "stage_name",
    [
        pytest.param("sa_savings", id="sa-savings"),
        pytest.param("tenure", id="tenure-with-an-arrival-measure-and-two-branches"),
    ],
)
def test_no_measure_wire_is_labeled_with_coordinates(forward_drawings, stage_name):
    """In the drawing of the forward builders graph at the primitive grain,
    no label of the wire of a measure is followed by coordinates."""
    # `sa_savings.bl` has no arrival perch, and so no arrival measure; the
    # first assert statement checks that the drawing labels a measure's wire
    assert MEASURE_WIRE_LABEL.search(forward_drawings[stage_name]) is not None
    assert MEASURE_LABEL_WITH_COORDINATES.findall(forward_drawings[stage_name]) == []


# --- the diagnostics of a stage ---


def test_the_diagnostics_of_the_consumption_stage_answer_with_nothing_missing(cons):
    """`diagnostics()` answers the nine questions on the completeness of
    `cons.bl` with nothing missing, exposed, unused, external or unread, and
    the stage ready for interpretation."""
    # `forward_map` names the lines that read a field of a later perch through
    # a transition that the stage does not write, and `builder_choice` the
    # pairs of perches that several builders could serve; `unread_inputs`
    # names the value inputs that a backward header lists and no line reads,
    # and the policy header of `cons.bl` lists `V[>]` alone, which its lines
    # read
    assert dict(cons.diagnostics()) == {
        "complete_signature": True,
        "missing_builders": (),
        "exposed_inputs": (),
        "unused_outputs": (),
        "forward_map": (),
        "builder_choice": (),
        "external_calls": (),
        "unread_inputs": (),
        "ready_for_interpretation": True,
    }


@pytest.mark.parametrize(
    ("stage_name", "ready"),
    [
        pytest.param("cons", True, id="the-consumption-stage"),
        pytest.param(
            "stage_of_a_family_not_admitted", False, id="a-forward-builders-graph-refused"
        ),
        pytest.param(
            "stage_with_an_external_call_in_its_utility",
            False,
            id="an-external-call-in-a-function",
        ),
        pytest.param(
            "stage_with_an_external_call_in_a_shock_law",
            False,
            id="an-external-call-in-a-shock-law",
        ),
    ],
)
def test_readiness_for_interpretation_needs_the_forward_builders_graph_and_no_external_call(
    request, stage_name, ready
):
    """A stage whose forward builders graph the package refuses, or one of
    whose lines calls a function that no definition of the stage declares,
    is not ready for interpretation, and the consumption stage is."""
    stage = request.getfixturevalue(stage_name)
    assert stage.diagnostics()["ready_for_interpretation"] is ready


@pytest.mark.parametrize(
    ("stage_name", "calls"),
    [
        pytest.param(
            "stage_with_an_external_call_in_its_utility",
            [("neverdef", 1)],
            id="in-the-body-of-a-function",
        ),
        pytest.param(
            "stage_with_an_external_call_in_a_shock_law",
            [("log", 1)],
            id="in-a-parameter-of-a-shock-law",
        ),
    ],
)
def test_a_function_that_no_definition_declares_is_listed_among_the_external_calls(
    request, stage_name, calls
):
    """A call of a function that no definition of the stage declares is
    listed among the external calls of the diagnostics with its count of
    arguments."""
    external_calls = request.getfixturevalue(stage_name).diagnostics()["external_calls"]
    # each entry is the address of the call, the name of the function and
    # the count of its arguments
    assert [entry[1:] for entry in external_calls] == calls


def test_a_shock_law_with_an_external_call_keeps_its_forward_builders_graph(
    stage_with_an_external_call_in_a_shock_law,
):
    """The package constructs the forward builders graph of a stage whose
    shock law calls a function that no definition of the stage declares."""
    graph = stage_with_an_external_call_in_a_shock_law.builder.fwd.graph
    assert isinstance(graph, Hypergraph)


def test_an_inverse_written_with_inv_is_read_as_the_inverse_of_a_declared_function(
    cons_with_egm_lines_text,
):
    """The package reads `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)` as the inverse of the declared
    function `𝑑𝑢`, with the obligation on the domain of an inverse, and not
    as the call of a function that no definition declares."""
    inverse = stage_from_text(
        cons_with_egm_lines_text.replace("𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)", "𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)")
    )
    assert inverse.diagnostics()["external_calls"] == ()
    assert not any("external:Inv" in str(item.entries) for item in inverse.obligations())
    assert any(item.condition == "inverse-function-domain" for item in inverse.obligations())


# --- the obligations of a stage ---


def test_a_shock_law_of_an_external_family_records_an_obligation_on_the_family(
    stage_with_a_shock_of_an_external_family,
):
    """A shock drawn from a family that neither the stage nor the package
    defines records the obligation on an external callable, which names the
    family and the distribution of the shock."""
    external = [
        item
        for item in stage_with_a_shock_of_an_external_family.obligations()
        if item.condition == "external-callable-signature-and-provider"
    ]
    assert [item.entries for item in external] == [("external:Density", Y_IDENTITY)]


@pytest.mark.parametrize(
    "stage_name",
    [
        pytest.param(
            "stage_with_a_shock_of_an_external_family", id="a-distribution-and-its-two-shocks"
        ),
        pytest.param("buffer_stock", id="a-derived-parameter-and-an-inverse-function"),
    ],
)
def test_an_obligation_placed_in_the_stage_names_a_definition_or_a_field_of_it(
    request, stage_name
):
    """Each obligation whose first entry is an identity of the stage names a
    definition of the stage's definitions table or one of its fields, and no
    position of an item in the file."""
    stage = request.getfixturevalue(stage_name)
    places = [
        str(item.entries[0])
        for item in stage.obligations()
        if item.entries and str(item.entries[0]).startswith(f"{stage.name}:")
    ]
    assert places != []
    assert [
        place for place in places if place not in stage.definitions and place not in stage.fields()
    ] == []


def test_an_obligation_that_one_line_gives_rise_to_several_times_is_held_once():
    """The stage of `BUNDLES` whose arrival value is divided by `β - R` holds
    no pair of condition and entries twice, although its construction records
    the condition that `β - R` is not zero four times for that one line."""
    # the line `V[<] = E_{y,z}(V/(β - R))` gives rise to the condition on
    # its divisor as a line and as an equation of the aggregator of
    # `dcsn_to_arvl`, and for the aggregation of that block once inside the
    # binder of the expectation and once at its integrand outside it
    stage = stage_from_text(
        bundles_text(arrival=ARRIVAL_VALUE_DIVIDED_BY_BETA_MINUS_R), "bundles.bl"
    )
    held = [(item.condition, item.entries) for item in stage.obligations()]
    assert [entries for condition, entries in held if condition == "arithmetic-definedness"] != []
    assert len(held) == len(set(held))


def test_no_function_that_the_stage_defines_is_held_as_an_external_callable(bundle_stage):
    """No obligation on an external callable of the stage of `BUNDLES` names
    a function, a function alias or a correspondence that the stage
    defines."""
    defined = {
        definition.identity.field
        for definition in bundle_stage.definitions.values()
        if definition.kind in ("function", "function_alias", "correspondence")
    }
    assert not [
        item
        for item in bundle_stage.obligations()
        if item.condition == "external-callable-signature-and-provider"
        and item.entries[0].field in defined
    ]


def test_the_obligation_on_the_domain_of_an_inverse_names_the_function_by_its_identity(
    buffer_stock,
):
    """The obligation on the domain of the inverse that `buffer_stock.bl`
    declares as `Inv(𝑑𝑢)` names the function `𝑑𝑢𝑖𝑛𝑣` by its identity."""
    inverse = [
        item for item in buffer_stock.obligations() if item.condition == "inverse-function-domain"
    ]
    assert [item.entries[0] for item in inverse] == ["buffer_stock:function:𝑑𝑢𝑖𝑛𝑣"]


def test_a_relation_that_no_operator_realizes_is_retained_with_an_obligation_on_its_line():
    """The complementarity `λ >= 0 ⟂ k_nxt >= (1-δ)*k_d` of the stage file
    `rendahl-2015/growth.bl` that the tests keep, which no operator of its
    builder realizes, records the obligation `retained-relation`, which names
    its line and says that no operator realizes it."""
    path = f"{COPIED_FILES_FOLDER}/rendahl-2015/growth.bl"
    stage = stage_from_text((ROOT / path).read_text(encoding="utf-8"), path)
    retained = [item for item in stage.obligations() if item.condition == "retained-relation"]
    assert [str(item.entries[0]) for item in retained] == ["cntn_to_dcsn.slackness"]
    assert "no operator of the builder realises it" in retained[0].explanation


def test_the_elaboration_leaves_an_atom_outside_the_shock_set_to_the_obligation_on_support():
    """The elaboration does not refuse a finite mixture of
    `cons_savings_iid.bl` with the atom −1 outside the shock set `Y := ℝ₊`:
    the stage records, as for every law, the obligation that the law gives
    probability only to values in that set, named by the shock."""
    text = corpus_text("cons_savings_iid")
    assert text.count(CONS_SAVINGS_IID_LAW) == 1
    stage = stage_from_text(text.replace(CONS_SAVINGS_IID_LAW, "Mixture((0.5, -1), (0.5, 1))"))
    support = [item for item in stage.obligations() if item.condition == "law-support"]
    assert [str(item.entries[0]) for item in support] == ["cons_savings_iid:shck:y"]
    assert "gives probability only to values in the declared shock set" in support[0].explanation


# --- denotations, signatures, descriptions and types ---


def test_the_answer_of_denote_keeps_its_inputs_outputs_and_pieces_after_its_stage_is_collected(
    answer_of_a_collected_stage,
):
    """The answer of `denote()` holds no reference to its stage, which is
    collected once deleted, and answers afterwards the inputs, outputs and
    pieces that it answered before."""
    held = answer_of_a_collected_stage
    assert held.stage() is None
    assert (held.answer.inputs, held.answer.outputs, held.answer.pieces) == (
        held.inputs,
        held.outputs,
        held.pieces,
    )


def test_a_wire_of_the_answer_of_denote_refuses_a_new_identity_and_keeps_its_hash(
    answer_of_a_collected_stage,
):
    """An assignment to the identity of a wire of the answer of `denote()`
    raises `FrozenInstanceError` and leaves the hash of the wire as it
    was."""
    held = answer_of_a_collected_stage
    with pytest.raises(FrozenInstanceError):
        held.wire.identity = held.outputs[0].identity
    assert hash(held.wire) == held.wire_hash


def test_a_wire_of_a_signature_is_the_pair_of_its_identity_and_its_printed_type(cons):
    """The input wire of the signature of the backward builder `cntn_to_dcsn`
    unpacks, compares and hashes as the pair of its identity and its
    mathematical type as printed."""
    [wire] = cons.builder.bwd["cntn_to_dcsn"].signature().inputs
    identity, displayed_type = wire
    assert identity == wire.identity
    assert displayed_type == str(wire.mathematical_type)
    assert wire == (identity, displayed_type)
    assert (identity, displayed_type) == wire
    assert hash(wire) == hash((identity, displayed_type))


@pytest.mark.parametrize(
    ("stage_name", "identity", "description"),
    [
        pytest.param(
            "buffer_stock", "buffer_stock:parameter:β", ("discount factor",), id="a-parameter"
        ),
        pytest.param(
            "buffer_stock",
            "buffer_stock:derived:μ_ξ",
            ("log-mean of the positive transitory draw, at which E[ξ] = 1",),
            id="a-derived-parameter",
        ),
        pytest.param(
            "two_parent_shocks_stage",
            "key_selection_reads:distribution:s",
            ("a two-point state; an admitted family, so that the forward view is constructed",),
            id="a-shock-law",
        ),
        pytest.param(
            "two_parent_shocks_stage",
            "key_selection_reads:distribution:θ",
            ("a shock whose law reads η directly and s through a key selection",),
            id="a-shock-law-with-a-selection-by-a-key",
        ),
    ],
)
def test_a_definition_holds_the_description_that_its_declaration_writes(
    request, stage_name, identity, description
):
    """The denotation of a definition holds the description that the author
    wrote on its declaration."""
    stage = request.getfixturevalue(stage_name)
    assert stage.definitions.denote(identity).describes == description


@pytest.mark.parametrize(
    "identity",
    [
        pytest.param("cons:parameter:ρ", id="a-parameter"),
        pytest.param("cntn_to_dcsn.value", id="a-line-of-a-block"),
    ],
)
def test_a_definition_whose_declaration_writes_no_description_holds_none(cons, identity):
    """The denotation of a definition whose declaration in `cons.bl` carries
    no description holds none."""
    assert cons.definitions.denote(identity).describes == ()


def test_a_calibrated_and_methodized_stage_keeps_the_type_of_its_decision_builders_input(
    cons, cons_methodized
):
    """The mathematical type of the input of the backward decision builder of
    `cons.bl` is equal, with an equal hash, on the symbolic stage and on a
    calibrated and methodized stage of the same file."""
    symbolic = cons.dcsn.builder.bwd.signature().inputs[0].mathematical_type
    bound = cons_methodized.dcsn.builder.bwd.signature().inputs[0].mathematical_type
    assert symbolic == bound
    assert hash(symbolic) == hash(bound)


def test_a_mathematical_type_refuses_an_assignment_to_its_carrier(cons):
    """An assignment to the carrier of the mathematical type of the input of
    the backward decision builder of `cons.bl` raises `AttributeError`."""
    mathematical_type = cons.dcsn.builder.bwd.signature().inputs[0].mathematical_type
    with pytest.raises(AttributeError):
        mathematical_type.carrier = None


def test_the_expression_of_a_function_does_not_depend_on_the_name_of_its_argument(cons):
    """The utility of `cons.bl` with its argument renamed from `c` to `d`
    denotes the expression that the utility of `cons.bl` denotes."""
    text = corpus_text("cons")
    utility = "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)"
    assert text.count(utility) == 1
    renamed = stage_from_text(text.replace(utility, "𝑢(d : ℝ₊₊) := d^(1-ρ)/(1-ρ)"))
    original = cons.definitions.denote("cons:function:𝑢").denoted[0].expression
    assert renamed.definitions.denote("cons:function:𝑢").denoted[0].expression == original


def test_an_external_call_leaves_the_type_of_a_function_unresolved_on_its_domain():
    """The mathematical type of the marginal utility of `cons.bl`, whose body
    calls `unknown`, a function that no definition declares, is printed as
    unresolved on the domain `ℝ₊₊`."""
    stage = stage_from_text(corpus_text("cons").replace("c^(-ρ)", "unknown(c)"))
    marginal = stage.definitions.denote("cons:function:𝑑𝑢").denoted[0]
    printed = str(marginal.mathematical_type)
    assert [phrase for phrase in ("UNRESOLVED", "ℝ₊₊") if phrase not in printed] == []


def test_a_call_of_log_with_two_arguments_leaves_the_expression_unresolved_with_the_reason():
    """The expression of the marginal utility of `cons.bl` whose body calls
    `log(c,c)` is printed as unresolved, with the reason that `log` takes one
    argument."""
    stage = stage_from_text(corpus_text("cons").replace("c^(-ρ)", "log(c,c)"))
    marginal = stage.definitions.denote("cons:function:𝑑𝑢").denoted[0]
    printed = str(marginal.expression)
    assert [
        phrase for phrase in ("UNRESOLVED", "one argument for log") if phrase not in printed
    ] == []


def test_a_declared_law_is_held_as_its_family_applied_to_the_pairs_the_file_writes(
    stage_with_a_finite_mixture,
):
    """The declaration of the shock `y` is held as `Mixture` applied to its
    two written pairs, each weight and each atom the number that the file
    writes."""
    declared = (
        stage_with_a_finite_mixture.definitions.denote("cons_savings_iid:distribution:y")
        .denoted[0]
        .expression
    )
    assert isinstance(declared, typed_expressions.Apply)
    assert typed_expressions.format_expression(declared.function) == "Mixture"
    assert len(declared.args) == 2 and all(isinstance(pair, terms.Tuple) for pair in declared.args)
    weights, atoms = zip(*((pair.items[0], pair.items[1]) for pair in declared.args))
    assert tuple(typed_expressions.format_expression(weight) for weight in weights) == (
        "0.25",
        "0.75",
    )
    assert tuple(typed_expressions.format_expression(atom) for atom in atoms) == ("0", "1")


def test_the_kernel_of_an_expectation_denotes_the_declared_law_by_reference(
    stage_with_a_finite_mixture,
):
    """The kernel of the expectation of the backward builder `dcsn_to_arvl`
    denotes the law of the shock `y` by the identity and the expression of
    its declaration, with no measure constructed from its atoms."""
    stage = stage_with_a_finite_mixture
    declared = stage.definitions.denote("cons_savings_iid:distribution:y").denoted[0].expression
    expectation = stage.builder.bwd["dcsn_to_arvl", "value:Expectation:1"].denote()
    [law] = expectation.kernel.denoted
    assert str(law.identity) == "cons_savings_iid:distribution:y"
    assert law.expression == declared
    assert "measure on" not in typed_expressions.format_expression(law.expression, width=None)


def test_the_output_of_an_expectation_is_a_function_whose_body_is_the_operator_e(
    stage_with_a_finite_mixture,
):
    """The expectation of the backward builder `dcsn_to_arvl` holds its output
    as a function whose body is the operator `E`."""
    expectation = stage_with_a_finite_mixture.builder.bwd[
        "dcsn_to_arvl", "value:Expectation:1"
    ].denote()
    held = expectation.outputs[0].expression
    assert (
        isinstance(held, typed_expressions.Lambda)
        and isinstance(held.body, terms.Operator)
        and held.body.head == "E"
    )


# --- the wire table and the numbers of coordinates ---


@pytest.mark.parametrize(
    "methodized",
    [
        pytest.param(False, id="a-copy-that-carries-the-wire-table"),
        pytest.param(True, id="a-copy-of-the-methodized-stage-that-builds-its-wire-table-again"),
    ],
)
def test_a_copy_of_a_stage_raises_its_wire_tables_refusal_anew_with_notes_of_its_own(
    methodized,
):
    """A copy of a stage raises the refusal that its wire table holds as an
    error of its own with the same text, without the notes that a caller
    added to the error of the first stage, and a note added to one error
    stays on it."""
    # the stage file `gourinchas-parker-2002/retire.bl` that the tests keep
    # holds such a refusal, for its block `cntn_to_dcsn`, which no rule
    # assigns to a direction; the table of the sorts of its wires,
    # `wire_table`, raises it when asked for the rows of the backward
    # direction
    stage = elaborate_stage(
        load_stage(ROOT / COPIED_FILES_FOLDER / "gourinchas-parker-2002/retire.bl")
    )
    with pytest.raises(NotConstructed) as held:
        wire_table(stage).rows("backward")
    held.value.add_note("Stage occurrence: periods[0].stages['retire']")
    # a copy that `copy_native` makes of the stage carries the wire table
    # that the stage keeps, with a copy of its refusal; `methodize` binds the
    # stage that it is called on, answers it and leaves it no wire table, so
    # a copy of the methodized stage builds its wire table again
    copy = copy_native(stage.methodize([]) if methodized else stage)
    with pytest.raises(NotConstructed) as carried:
        wire_table(copy).rows("backward")
    assert carried.value is not held.value and str(carried.value) == str(held.value)
    assert getattr(carried.value, "__notes__", []) == []
    carried.value.add_note("Stage occurrence: periods[1].stages['retire']")
    assert held.value.__notes__ == ["Stage occurrence: periods[0].stages['retire']"]


def test_bound_variable_number_gives_each_base_and_place_its_own_number_from_1000_up(cons):
    """On the ports of `cons.bl`, `bound_variable_number` gives each pair of a
    base and a place its own number, none below 1000."""
    # the package binds every variable at a literal position below 1000
    names = StageNames(cons)
    # the arguments of `bound_variable_number`: the names of the stage, the
    # base, and the place among the ports, from 0 to the number of ports
    numbers = {
        (base, place): bound_variable_number(names, base, place)
        for base in COORDINATE_BASES
        for place in range(len(names.ports) + 1)
    }
    assert [pair for pair, number in numbers.items() if number < 1000] == []
    assert [number for number, count in Counter(numbers.values()).items() if count > 1] == []


# --- the wires, ports, bubbles and sorts of every graph ---


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_no_two_wires_of_a_graph_carry_one_identity(read_only_stage_from_file, src):
    """In every graph of the stage, at every grain, and in every graph inside
    a bubble, no two wires carry the same identity."""
    violations = []
    for level, direction, grain, graph in graphs_of(read_only_stage_from_file(src)):
        if isinstance(graph, NotConstructed):
            continue
        violations += repeated_wire_identities(graph, f"{level} {direction} {grain}")
    assert violations == []


def test_repeated_wire_identities_reports_an_input_whose_reader_takes_a_new_wire():
    """The helper `repeated_wire_identities` of this file reports that two
    wires carry the input's identity when the policy's pullback reads a new
    wire in place of the input of the backward builders graph."""
    graph = stage_from_file(CORPUS["cons"]).builder.bwd.primitives.graph
    reader = [box.name for box in graph.boxes].index("policy:Pullback")
    box_wires = list(graph.box_wires)
    box_wires[reader] = ((len(graph.spider_types),), box_wires[reader][1])
    split = Hypergraph(
        graph.dom, graph.cod, graph.boxes, (graph.dom_wires, tuple(box_wires), graph.cod_wires)
    )
    assert repeated_wire_identities(split, "split") == [
        "split: 2 wires carry the identity cons:function:cntn:V"
    ]


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_every_wire_of_a_graph_stands_at_a_port(read_only_stage_from_file, src):
    """In every graph of the stage, at every grain, and in every graph inside
    a bubble, every wire stands at an input or an output of the graph or of
    a box."""
    violations = []
    for level, direction, grain, graph in graphs_of(read_only_stage_from_file(src)):
        if isinstance(graph, NotConstructed):
            continue
        violations += wires_at_no_port(graph, f"{level} {direction} {grain}")
    assert violations == []


def test_wires_at_no_port_reports_a_wire_added_at_no_port(cons):
    """The helper `wires_at_no_port` of this file reports a wire at no port
    that the backward builders graph at the primitive grain gains, carrying
    the sort of the arrival measure of the forward builders graph."""
    graph = cons.builder.bwd.primitives.graph
    measure = next(
        sort
        for sort in wire_sorts(cons.builder.fwd.primitives.graph)
        if str(sort.identity) == "cons:measure:arvl"
    )
    added = Hypergraph(
        graph.dom, graph.cod, graph.boxes, graph.wires, graph.spider_types + (Ty(measure),)
    )
    assert wires_at_no_port(added, "added") == [
        "added: the wire of cons:measure:arvl stands at no port"
    ]


def test_a_box_of_the_wiring_gives_the_perch_of_its_field_as_its_kind(cons):
    """The spider inside the block `cntn_to_dcsn` of the backward initial
    diagram, a box of the wiring on the field `cons:dcsn:V`, gives as its
    kind the second segment of the identity of its first wire, the perch
    `dcsn`."""
    graph = cons.initial.backward.graph
    block = next(box for box in graph.boxes if box.name == "cntn_to_dcsn")
    spider = next(box for box in block.arg.boxes if isinstance(box, Spider))
    assert kind_of(spider) == "dcsn"


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_every_wire_that_a_box_reads_is_written_in_its_graph(read_only_stage_from_file, src):
    """Every wire that a box reads is written by a box of the same graph or
    is an input of the graph, at every grain and inside every bubble, apart
    from a field of `ROLES_READ_WITHOUT_A_WRITER` that a line of a backward
    initial diagram reads at the perch of its own output, which is a
    coordinate of the function that the line writes."""
    violations = []
    for level, direction, grain, graph in graphs_of(read_only_stage_from_file(src)):
        if isinstance(graph, NotConstructed):
            continue
        initial_backward = (level, direction) == ("initial", "backward")
        roles = ROLES_READ_WITHOUT_A_WRITER if initial_backward else ()
        violations += wires_read_and_not_written(graph, f"{level} {direction} {grain}", roles)
    assert violations == []


def test_wires_read_and_not_written_reports_a_wire_whose_writer_is_removed():
    """The helper `wires_read_and_not_written` of this file reports the wire
    that the aggregation of the decision builder reads once the pullback
    before it is removed."""
    graph = stage_from_file(CORPUS["cons"]).builder.bwd.primitives.graph
    removed = without_box(graph, "cntn_to_dcsn:Pullback")
    assert wires_read_and_not_written(removed, "removed") == [
        "removed: cntn_to_dcsn:Aggregation reads cons:function:cntn:V:g, which no box writes"
    ]


def test_wires_read_and_not_written_reports_a_wire_in_a_bubble_whose_writer_is_removed():
    """The helper `wires_read_and_not_written` of this file reports, inside
    the bubble of the decision builder at the builder grain, the wire that
    the aggregation reads once the pullback before it is removed."""
    graph = stage_from_file(CORPUS["cons"]).builder.bwd.graph
    bubble = next(box for box in graph.boxes if box.name == "cntn_to_dcsn")
    interior = without_box(Hypergraph.from_diagram(bubble.arg), "cntn_to_dcsn:Pullback")
    diagram = interior.to_diagram()
    changed_bubble = Bubble(diagram, dom=bubble.dom, cod=bubble.cod, name=bubble.name)
    changed = Hypergraph(
        graph.dom,
        graph.cod,
        tuple(changed_bubble if box is bubble else box for box in graph.boxes),
        graph.wires,
    )
    assert wires_read_and_not_written(changed, "changed") == [
        "changed / cntn_to_dcsn: cntn_to_dcsn:Aggregation reads cons:function:cntn:V:g, "
        "which no box writes"
    ]


def test_wires_read_and_not_written_reports_a_state_read_at_another_perch_than_the_output():
    """The helper `wires_read_and_not_written` of this file, given
    `ROLES_READ_WITHOUT_A_WRITER`, reports the read of the decision state,
    which no box writes, by a line made to write the arrival value at the
    arrival perch."""
    graph = stage_from_file(CORPUS["cons"]).initial.backward.primitives.graph
    sorts = wire_sorts(graph)
    arrival_value = [str(sort.identity) for sort in sorts].index("cons:arvl:V")
    index = [box.name for box in graph.boxes].index("policy.optimality")
    policy = graph.boxes[index]
    moved = Box(policy.name, policy.dom, Ty(sorts[arrival_value]))
    box_wires = list(graph.box_wires)
    box_wires[index] = (box_wires[index][0], (arrival_value,))
    changed = Hypergraph(
        graph.dom,
        graph.cod,
        tuple(moved if box is policy else box for box in graph.boxes),
        (graph.dom_wires, tuple(box_wires), graph.cod_wires),
    )
    assert wires_read_and_not_written(changed, "changed", ROLES_READ_WITHOUT_A_WRITER) == [
        "changed: policy.optimality reads cons:dcsn:m_d, which no box writes"
    ]


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_the_five_grains_of_a_graph_have_the_same_inputs_and_outputs(
    read_only_stage_from_file, src
):
    """For each level and direction, the graphs at the five grains have the
    same ordered inputs and the same ordered outputs."""
    graphs = [
        (level, direction, grain, graph)
        for level, direction, grain, graph in graphs_of(read_only_stage_from_file(src))
        if not isinstance(graph, NotConstructed)
    ]
    assert grains_with_other_inputs_or_outputs(graphs) == []


def test_grains_with_other_inputs_or_outputs_reports_a_grain_without_its_last_output():
    """The helper `grains_with_other_inputs_or_outputs` of this file reports
    the backward builders graph at the primitive grain when it loses its last
    output, so that its outputs differ from those of the builder grain."""
    stage = stage_from_file(CORPUS["cons"])
    primitive = stage.builder.bwd.primitives.graph
    shorter = Hypergraph(
        primitive.dom,
        primitive.cod[:-1],
        primitive.boxes,
        (primitive.dom_wires, primitive.box_wires, primitive.cod_wires[:-1]),
    )
    graphs = [
        (level, direction, grain, shorter if grain == "primitive" else graph)
        for level, direction, grain, graph in graphs_of(stage)
        if (level, direction) == ("builders", "backward")
    ]
    assert grains_with_other_inputs_or_outputs(graphs) == [
        "builders backward primitive: other outputs than the builder grain"
    ]


# the default row is adjuster_cons.bl, which holds a bubble with two outputs
@pytest.mark.parametrize(
    "src",
    one_row_by_default(
        ELABORATED_FILES,
        default=ROOT / "applications/durables/declaration/stages/adjuster_cons/adjuster_cons.bl",
    ),
    ids=stage_file_id,
)
def test_every_bubble_has_the_inputs_and_outputs_of_the_graph_inside_it(
    read_only_stage_from_file, src
):
    """In every graph of the stage, at every grain, and in every graph inside
    a bubble, each bubble has the ordered inputs and the ordered outputs of
    the graph inside it."""
    violations = []
    for level, direction, grain, graph in graphs_of(read_only_stage_from_file(src)):
        if isinstance(graph, NotConstructed):
            continue
        violations += bubbles_with_other_inputs_or_outputs(graph, f"{level} {direction} {grain}")
    assert violations == []


def test_bubbles_with_other_inputs_or_outputs_reports_a_graph_inside_with_inputs_reversed(cons):
    """The helper `bubbles_with_other_inputs_or_outputs` of this file reports
    the block `arvl_to_dcsn` of the forward initial diagram when the graph
    inside it takes its two inputs in the other order."""
    graph = cons.initial.forward.graph
    block = next(box for box in graph.boxes if box.name == "arvl_to_dcsn")
    interior = Hypergraph.from_diagram(block.arg)
    exchanged = Hypergraph(
        Ty(*reversed(interior.dom.inside)),
        interior.cod,
        interior.boxes,
        (tuple(reversed(interior.dom_wires)), interior.box_wires, interior.cod_wires),
    )
    changed_block = Bubble(exchanged.to_diagram(), dom=block.dom, cod=block.cod, name=block.name)
    changed = Hypergraph(
        graph.dom,
        graph.cod,
        tuple(changed_block if box is block else box for box in graph.boxes),
        graph.wires,
    )
    assert bubbles_with_other_inputs_or_outputs(changed, "changed") == [
        "changed: the bubble arvl_to_dcsn has other inputs than the graph inside it"
    ]


@pytest.mark.parametrize("src", one_row_by_default(ELABORATED_FILES), ids=stage_file_id)
def test_one_identity_has_one_sort_in_every_graph_of_a_stage(read_only_stage_from_file, src):
    """Across every graph of the stage, at every grain and inside every
    bubble, the wires that carry one identity carry sorts of one `repr`."""
    assert identities_with_two_sorts(graphs_of(read_only_stage_from_file(src))) == []


def test_identities_with_two_sorts_reports_an_identity_given_another_role():
    """The helper `identities_with_two_sorts` of this file reports that the
    input's identity carries two sorts when the input wire of the backward
    builders graph at the primitive grain carries a sort with another role."""
    stage = stage_from_file(CORPUS["cons"])
    primitive = stage.builder.bwd.primitives.graph
    sorts = wire_sorts(primitive)
    [wire], _ = port_wires(primitive)
    held = sorts[wire]
    other = Sort(
        held.identity,
        held.kind,
        perch=held.perch,
        role="state",
        domain=held.domain,
        coordinates=held.coordinates,
        derivatives=held.derivatives,
    )
    types = tuple(Ty(other) if number == wire else Ty(sort) for number, sort in enumerate(sorts))
    changed = Hypergraph(primitive.dom, primitive.cod, primitive.boxes, primitive.wires, types)
    graphs = [
        (level, direction, grain, changed if grain == "primitive" else graph)
        for level, direction, grain, graph in graphs_of(stage)
        if (level, direction) == ("builders", "backward")
    ]
    assert identities_with_two_sorts(graphs) == [
        "the identity cons:function:cntn:V carries 2 sorts"
    ]
