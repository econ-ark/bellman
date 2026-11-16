"""The view of a trellis in Model Explorer: its collection of graphs, the
layers of its periods and stage occurrences, the joins and the boundary of
its builders graphs, its initial diagrams, its restricted views, the place of
a node, and its files and its page."""

import json
from urllib.parse import unquote

import pytest
from model_explorer_views import (
    FORWARD_ONLY_STAGE,
    answering_server,
    applied_layer_style,
    attribute_of,
    attributes,
    collection_as_json,
    collection_in_viewer_classes,
    graph_named,
    layers_of,
    needs_viewer,
    occurrence_of,
    two_period_lesson_trellis,
)
from stage_builders import stage_from_text

from bellman.factory.model_explorer import (
    PAIRING_RULES,
    VIEWER_HEALTH,
    _trellis_collection,
    _write_view,
    serve,
)
from bellman.refusals import FactoryError
from bellman.trellis import (
    BOUNDARY_IDS,
    LAYER_ID_ENDING,
    NODE_STYLE,
    accrete,
    explore,
    node_place,
    to_model_explorer,
    trellis_selection,
    write_model_explorer,
)

# the four graphs of a trellis view drawn with its initial diagrams
TRELLIS_GRAPHS = ["backward", "forward", "backward initial diagram", "forward initial diagram"]

# the ids of the rows of a table over those graphs
TRELLIS_GRAPH_IDS = [graph_id.replace(" ", "-") for graph_id in TRELLIS_GRAPHS]

# the perch at which each stage of the cons-port trellis is entered, where a
# join from another occurrence arrives: the arrival perch where the stage
# declares one, else the decision perch, since port and cons declare none
ENTRY_PERCH = {"port": "dcsn", "cons": "dcsn", "disc": "arvl"}


def entry_perch_of(field):
    """The entry perch of the stage of the occurrence that a field node of
    the cons-port trellis's initial diagram stands in."""
    return ENTRY_PERCH[field.namespace.split("/")[1]]


def boundary_ports(graph, kind):
    """The ids of the ports of the boundary nodes of kind `kind` of a graph
    of a trellis view, in the order of the nodes: the wires that enter or
    leave the graph there."""
    return [
        m.id
        for node in graph.nodes
        if not node.namespace and attributes(node).get("kind") == kind
        for m in (*node.outputsMetadata, *node.inputsMetadata)
    ]


def join_edges(graph):
    """The edges of a graph of a trellis view that join two stage
    occurrences, each as the occurrence it leaves, the occurrence it enters,
    the attribute `join` of the reading port, and the wires of its two ends,
    each without the prefix of its occurrence."""
    found = []
    for node in graph.nodes:
        ports = {m.id: attributes(m) for m in node.inputsMetadata}
        for edge in node.incomingEdges:
            source, target = occurrence_of(edge.sourceNodeId), occurrence_of(node.id)
            if source and target and source != target:
                wires = (edge.sourceNodeOutputId, edge.targetNodeInputId)
                found.append(
                    (source, target, ports[edge.targetNodeInputId]["join"])
                    + tuple(wire.split("/", 2)[2] for wire in wires)
                )
    return found


def routed_edges(graph):
    """The edges of a graph that carry a route record, each with the node
    it enters."""
    return [
        (node, edge)
        for node in graph.nodes
        for edge in node.incomingEdges
        if attribute_of(edge, "route") is not None
    ]


def outside_marks(view, graph_id, side):
    """Each port on `side` of the `outside` nodes of a graph of a view, with
    its join, its outside occurrence and the node's label and target."""
    return [
        (
            port.id,
            attributes(port).get("join"),
            attributes(port).get("outside"),
            node.label,
            attributes(node)["target"],
        )
        for node in graph_named(view, graph_id).nodes
        if not node.namespace and attributes(node).get("kind") == "outside"
        for port in getattr(node, side)
    ]


@pytest.fixture(scope="module")
def port_cons_view(bound_port_cons_trellis):
    """The view of the cons-port trellis with its two initial diagrams."""
    return to_model_explorer(bound_port_cons_trellis, initial=True)


@pytest.fixture(scope="module")
def port_cons_selection(bound_port_cons_trellis):
    """The selection of the connections of the cons-port trellis."""
    return trellis_selection(bound_port_cons_trellis)


@pytest.fixture(scope="module")
def restricted_view(bound_port_cons_trellis):
    """The view of the cons-port trellis restricted to the consumption
    stage of periods 0 and 1."""
    return to_model_explorer(bound_port_cons_trellis, periods=range(0, 2), stages=["cons"])


@pytest.fixture(scope="module")
def one_period_view(one_period_cons_trellis):
    """The view of the trellis of one period with no registry."""
    return to_model_explorer(one_period_cons_trellis)


@pytest.fixture(scope="module")
def one_period_view_with_age(cons):
    """The view of a trellis of one period whose registry's calibration
    gives the last age, 64, as the registry of a trellis that a recipe
    assembles does; `periods[0]` is the last period."""
    trellis = accrete(
        {"periods": [], "inter_connectors": [], "registry": {"calibration": {"last_age": 64}}},
        {"stages": {"consumption": cons}, "connectors": []},
    )
    return to_model_explorer(trellis)


@pytest.fixture(scope="module")
def cons_methodized_without_calibration_view(cons_methodized_without_calibration):
    """The view of the consumption stage with its methods bound."""
    return to_model_explorer(cons_methodized_without_calibration)


@pytest.fixture(scope="module")
def retiree_death_view(retiree_death):
    """The view of the stage `retiree_death`, a branching stage whose
    forward builders graph is refused."""
    return to_model_explorer(retiree_death)


@pytest.fixture(scope="module")
def two_period_lesson_trellis_view(cons_methodized_without_calibration, port):
    """The view of a trellis of two periods of the stages port, cons and
    disc."""
    return to_model_explorer(two_period_lesson_trellis(cons_methodized_without_calibration, port))


@pytest.fixture
def trellis_builds(monkeypatch, bound_port_cons_trellis, port_cons_view):
    """The list of the builds of the view of the cons-port trellis, each as
    its selection, while the view already built is returned in place of each
    such build;
    the view of another trellis is built as before."""
    built = []

    def build(graph_builder, trellis, *selection):
        if trellis is not bound_port_cons_trellis:
            return _trellis_collection(graph_builder, trellis, *selection)
        built.append(selection)
        return port_cons_view

    monkeypatch.setattr("bellman.factory.model_explorer._trellis_collection", build)
    return built


@pytest.fixture
def served_pages(monkeypatch):
    """The keyword arguments of each call of `serve`, which then starts no
    server and answers an address, while no browser window opens."""
    served = []
    monkeypatch.setattr(
        "bellman.factory.model_explorer.serve",
        lambda *args, **kwargs: served.append(kwargs) or "http://localhost:0/",
    )
    monkeypatch.setattr("webbrowser.open", lambda url, *args, **kwargs: None)
    return served


@pytest.fixture
def written_trellis_files(trellis_builds, bound_port_cons_trellis, tmp_path):
    """The paths of the two files that `write_model_explorer` writes for
    the cons-port trellis."""
    return write_model_explorer(bound_port_cons_trellis, tmp_path)


@needs_viewer
def test_the_view_of_a_trellis_whole_or_restricted_is_labeled_trellis(
    port_cons_view, restricted_view
):
    """The collection of a trellis view, whole or restricted to some of its
    occurrences, is labeled `trellis`."""
    assert port_cons_view.label == "trellis"
    assert restricted_view.label == port_cons_view.label


@needs_viewer
def test_a_trellis_view_holds_its_two_initial_diagrams_only_when_asked(bound_port_cons_trellis):
    """The view of a trellis holds its two builders graphs, followed by its
    two initial diagrams only where the keyword `initial` asks for them."""
    assert [graph.id for graph in to_model_explorer(bound_port_cons_trellis).graphs] == [
        "backward",
        "forward",
    ]
    assert [
        graph.id for graph in to_model_explorer(bound_port_cons_trellis, initial=True).graphs
    ] == [
        "backward",
        "forward",
        "backward initial diagram",
        "forward initial diagram",
    ]


@needs_viewer
@pytest.mark.parametrize(
    ("period", "key", "keywords", "fixtures", "match"),
    [
        pytest.param(
            2, "cons", {"initial": True}, {}, "holds its initial diagrams always", id="initial"
        ),
        pytest.param(
            0, "cons", {"periods": [0]}, {}, "selects no periods and no stages", id="periods"
        ),
        pytest.param(
            0, "cons", {"stages": ["cons"]}, {}, "selects no periods and no stages", id="stages"
        ),
        pytest.param(
            0,
            "cons",
            {},
            {"selection": "port_cons_selection"},
            "selects no periods and no stages",
            id="selection",
        ),
        pytest.param(0, "disc", {"unjoined": True}, {}, "marks no unjoined field", id="unjoined"),
    ],
)
def test_the_view_of_a_stage_refuses_each_keyword_of_a_trellis_view(
    request, bound_port_cons_trellis, period, key, keywords, fixtures, match
):
    """The view of a stage version refuses with a TypeError, in the sentence
    of its row, each of the five keywords that only a trellis view takes; a
    view drawn in place of the refusal fails the test."""
    stage = bound_port_cons_trellis["periods"][period]["stages"][key]
    # a keyword whose value a fixture gives reads it by the fixture's name
    given = keywords | {name: request.getfixturevalue(value) for name, value in fixtures.items()}
    with pytest.raises(TypeError, match=match):
        to_model_explorer(stage, **given)


@needs_viewer
def test_the_backward_graph_of_a_trellis_has_one_layer_for_each_period(
    bound_port_cons_trellis, port_cons_view
):
    """The nodes of the backward graph of a trellis view stand in one layer
    for each period of the trellis, some of them three layers deep, in a
    builder of an occurrence."""
    namespaces = {n.namespace for n in graph_named(port_cons_view, "backward").nodes}
    periods = {ns.split("/")[0] for ns in namespaces if ns.startswith("periods[")}
    assert len(periods) == len(bound_port_cons_trellis["periods"])
    assert any(ns.count("/") >= 2 for ns in namespaces)  # periods[h]/<stage>/<builder>


@needs_viewer
@pytest.mark.parametrize("graph_id", TRELLIS_GRAPHS, ids=TRELLIS_GRAPH_IDS)
def test_the_nodes_of_each_graph_of_a_trellis_view_have_distinct_ids(port_cons_view, graph_id):
    """The nodes of each graph of a trellis view have distinct ids, those
    of two occurrences of one stage among them."""
    graph = graph_named(port_cons_view, graph_id)
    nodes = {n.id: n for n in graph.nodes}
    assert len(nodes) == len(graph.nodes)


@needs_viewer
@pytest.mark.parametrize("graph_id", TRELLIS_GRAPHS, ids=TRELLIS_GRAPH_IDS)
def test_each_edge_of_a_trellis_view_joins_an_output_of_its_source_to_an_input_of_its_target(
    port_cons_view, graph_id
):
    """Each edge of each graph of a trellis view leaves a port among the
    outputs of its source node and enters a port among the inputs of the
    node that holds it."""
    graph = graph_named(port_cons_view, graph_id)
    nodes = {n.id: n for n in graph.nodes}
    for node in graph.nodes:
        inputs = {m.id for m in node.inputsMetadata}
        for edge in node.incomingEdges:
            outputs = {m.id for m in nodes[edge.sourceNodeId].outputsMetadata}
            assert edge.sourceNodeOutputId in outputs and edge.targetNodeInputId in inputs


@needs_viewer
@pytest.mark.parametrize("graph_id", ["backward", "forward"])
def test_every_input_port_of_a_builders_graph_of_a_trellis_view_has_an_edge(
    port_cons_view, graph_id
):
    """Every input port of a node of a builders graph of a trellis view is
    entered by an edge."""
    for node in graph_named(port_cons_view, graph_id).nodes:
        inputs = {m.id for m in node.inputsMetadata}
        assert inputs == {e.targetNodeInputId for e in node.incomingEdges}, node.id


@needs_viewer
@pytest.mark.parametrize("graph_id", ["backward", "forward"])
def test_the_viewer_lays_out_and_colors_each_layer_of_a_trellis_graph_by_its_depth(
    port_cons_view, graph_id
):
    """The layer configurations of a builders graph of a trellis view give
    each layer the layout and the colors of its depth, as the viewer's page
    applies them."""
    graph = graph_named(port_cons_view, graph_id)
    # each as (layout, fill, border color, label color), the layout 1 left to
    # right and 0 top to bottom: the periods side by side, each white, its
    # stages in forward order; an occurrence on the lightest of the three
    # pale blues and a builder on the second, each with a navy border and
    # label
    configs, navy = graph.groupNodeConfigs, "#172A52"
    assert {
        (namespace.count("/") + 1, applied_layer_style(configs, namespace))
        for namespace in layers_of(graph)
    } == {
        (1, (1, "#FFFFFF", navy, navy)),
        (2, (0, "#EDF7FC", navy, navy)),
        (3, (0, "#C5E5F1", navy, navy)),
    }
    # the root, which is no layer, laid out left to right; a sub-builder,
    # which no stage of this trellis holds, on the third and darkest blue
    assert applied_layer_style(configs, "") == (1, None, None, None)
    assert applied_layer_style(configs, "periods[0]/sa/cntn_to_dcsn/risk_ce") == (
        0,
        "#91BED7",
        navy,
        navy,
    )


@needs_viewer
@pytest.mark.parametrize(
    ("view", "graph_id", "period", "shown"),
    [
        *[
            pytest.param(
                "port_cons_view",
                graph_id,
                "periods[2]",
                {},
                id=f"cons-port-{graph_id.replace(' ', '-')}",
            )
            for graph_id in TRELLIS_GRAPHS
        ],
        *[
            pytest.param(
                "one_period_view_with_age",
                graph_id,
                "periods[0]",
                {"age": "64"},
                id=f"last-age-64-{graph_id}",
            )
            for graph_id in ("backward", "forward")
        ],
        *[
            pytest.param(
                "one_period_view", graph_id, "periods[0]", {}, id=f"no-registry-{graph_id}"
            )
            for graph_id in ("backward", "forward")
        ],
    ],
)
def test_a_period_layer_shows_an_age_only_where_the_registry_gives_one(
    request, view, graph_id, period, shown
):
    """The layer of a period shows an age only where the calibration of the
    trellis's registry gives one, the last age for the last period."""
    graph = graph_named(request.getfixturevalue(view), graph_id)
    assert graph.groupNodeAttributes[period] == shown


@needs_viewer
@pytest.mark.parametrize(
    ("view", "graph_id", "layer", "shown"),
    [
        *[
            pytest.param(
                "port_cons_view",
                graph_id,
                "periods[2]/cons",
                {"stage": "cons calibrated methodized configured"},
                id=f"bound-cons-{graph_id.replace(' ', '-')}",
            )
            for graph_id in TRELLIS_GRAPHS
        ],
        *[
            pytest.param(
                "one_period_view_with_age",
                graph_id,
                "periods[0]/consumption",
                {"stage": "cons"},
                id=f"symbolic-cons-{graph_id}",
            )
            for graph_id in ("backward", "forward")
        ],
    ],
)
def test_an_occurrence_layer_shows_its_stage_with_the_bindings_it_holds(
    request, view, graph_id, layer, shown
):
    """The layer of a stage occurrence, named by its period and its key,
    shows the name of its stage with the bindings that the occurrence
    holds."""
    graph = graph_named(request.getfixturevalue(view), graph_id)
    assert graph.groupNodeAttributes[layer] == shown


@needs_viewer
@pytest.mark.parametrize("graph_id", ["backward", "forward"])
def test_an_occurrence_holds_the_boxes_and_layers_of_its_stage_view(
    bound_port_cons_trellis, port_cons_view, graph_id
):
    """An occurrence in a builders graph of a trellis view holds the layers
    and the boxes of the view of its stage alone, each id and namespace under
    the occurrence's address, its own `Outputs` aside."""
    graph = graph_named(port_cons_view, graph_id)
    prefix = "periods[2]/cons/"
    alone = graph_named(
        to_model_explorer(bound_port_cons_trellis["periods"][2]["stages"]["cons"]), graph_id
    )
    layers = graph.groupNodeAttributes
    inner = {ns[len(prefix) :]: shown for ns, shown in layers.items() if ns.startswith(prefix)}
    assert inner == alone.groupNodeAttributes
    held = {
        n.id[len(prefix) :]: n
        for n in graph.nodes
        if n.id.startswith(prefix) and n.id[len(prefix) :] not in BOUNDARY_IDS
    }
    boxes = [n for n in alone.nodes if n.id not in BOUNDARY_IDS]
    assert set(held) == {n.id for n in boxes}
    for node in boxes:
        copy = held[node.id]
        assert (copy.label, copy.attrs, copy.style) == (node.label, node.attrs, node.style)
        assert copy.namespace == prefix + node.namespace


@needs_viewer
@pytest.mark.parametrize("graph_id", ["backward", "forward"])
def test_a_builders_graph_of_a_trellis_view_carries_no_perch_overlay(port_cons_view, graph_id):
    """A builders graph of a trellis view carries no perch overlay."""
    assert graph_named(port_cons_view, graph_id).tasksData is None


@needs_viewer
@pytest.mark.parametrize(("key", "control"), [("port", "ς"), ("cons", "c")], ids=["port", "cons"])
def test_each_policy_ends_at_an_outputs_node_in_the_layer_of_its_occurrence(
    port_cons_view, key, control
):
    """In each of the six periods, the policy of an occurrence that chooses
    a control ends at a node `Outputs` in the occurrence's own layer, whose
    one input its own evaluation writes."""
    nodes = {n.id: n for n in graph_named(port_cons_view, "backward").nodes}
    # the cons-port trellis holds six periods, periods[0] to periods[5]
    own = {h: nodes[f"periods[{h}]/{key}/GraphOutputs"] for h in range(6)}
    assert {h: (n.label, n.namespace, n.style) for h, n in own.items()} == {
        h: ("Outputs", f"periods[{h}]/{key}", NODE_STYLE) for h in range(6)
    }
    assert {h: [m.id for m in n.inputsMetadata] for h, n in own.items()} == {
        h: [f"periods[{h}]/{key}/policy:Evaluation:{control}:result"] for h in range(6)
    }
    assert {h: [e.sourceNodeId for e in n.incomingEdges] for h, n in own.items()} == {
        h: [f"periods[{h}]/{key}/policy:Evaluation"] for h in range(6)
    }


@needs_viewer
def test_an_occurrence_that_chooses_no_control_has_no_outputs_node(port_cons_view):
    """No occurrence of `disc`, which chooses no control, has a node
    `Outputs` in the backward graph of the cons-port trellis."""
    nodes = {n.id for n in graph_named(port_cons_view, "backward").nodes}
    # the six periods of the cons-port trellis
    assert [h for h in range(6) if f"periods[{h}]/disc/GraphOutputs" in nodes] == []


@needs_viewer
def test_the_forward_graph_of_a_trellis_view_holds_no_outputs_node(port_cons_view):
    """The forward graph of a trellis view, which gives no policy, holds no
    node `Outputs`."""
    forward = graph_named(port_cons_view, "forward")
    assert not [n.id for n in forward.nodes if n.id.endswith("/GraphOutputs")]


@needs_viewer
def test_the_forward_joins_of_a_trellis_are_labeled_by_the_pairs_they_join(port_cons_view):
    """Each join of the forward graph of the cons-port trellis is an edge
    between two occurrences, labeled on its reading port by the pair of
    fields that the connector, the equal name or the inter-period mapping
    joins."""
    forward = graph_named(port_cons_view, "forward")
    joins = [join[:3] for join in join_edges(forward)]
    # from disc in one period to port in the next in time, which has the
    # lower index, by the inter-period mapping of the lower index: five
    # mappings between the six periods
    between = [join for join in joins if join[0][0] != join[1][0]]
    assert sorted(between) == sorted(
        ((f"periods[{h + 1}]", "disc"), (f"periods[{h}]", "port"), f"inter_connectors[{h}] a → k")
        for h in range(5)
    )
    # within each of the six periods, port to cons by the connector and cons
    # to disc by the equal name
    within = sorted(join for join in joins if join[0][0] == join[1][0])
    assert within == sorted(
        [((f"periods[{h}]", "port"), (f"periods[{h}]", "cons"), "w → m") for h in range(6)]
        + [((f"periods[{h}]", "cons"), (f"periods[{h}]", "disc"), "a") for h in range(6)]
    )


@needs_viewer
def test_each_backward_join_reads_the_value_at_the_entry_perch_of_the_later_occurrence(
    port_cons_view,
):
    """Each join of the backward graph of the cons-port trellis is an edge
    from the value at the entry perch of the later occurrence to the
    continuation value of the earlier one, labeled as the forward join."""
    # two joins within each of the six periods, and one between each two
    # adjacent periods by the five inter-period mappings
    labeled = (
        [((f"periods[{h}]", "cons"), (f"periods[{h}]", "port"), "w → m") for h in range(6)]
        + [((f"periods[{h}]", "disc"), (f"periods[{h}]", "cons"), "a") for h in range(6)]
        + [
            (
                (f"periods[{h}]", "port"),
                (f"periods[{h + 1}]", "disc"),
                f"inter_connectors[{h}] a → k",
            )
            for h in range(5)
        ]
    )
    assert set(join_edges(graph_named(port_cons_view, "backward"))) == {
        (
            later,
            earlier,
            label,
            f"{later[1]}:function:{ENTRY_PERCH[later[1]]}:V",
            f"{earlier[1]}:function:cntn:V",
        )
        for later, earlier, label in labeled
    }


@needs_viewer
def test_each_backward_join_names_the_rule_that_paired_its_wire(port_cons_view):
    """The reading port of each join of the backward graph names the rule
    that paired its wire, one of the package's two rules, one wire per role
    and equal name, the value's rule being one wire per role."""
    rules = {}
    for node in graph_named(port_cons_view, "backward").nodes:
        for port in node.inputsMetadata:
            shown = attributes(port)
            if "join" in shown:
                rules[port.id] = shown["paired by"]
    assert rules and set(rules.values()) <= set(PAIRING_RULES)
    assert PAIRING_RULES == ("one wire per role", "equal name")
    assert rules["periods[1]/cons/cons:function:cntn:V"] == "one wire per role"


@needs_viewer
def test_no_port_of_the_forward_graph_names_a_rule(port_cons_view):
    """No port of the forward graph names a rule, since a forward join
    carries a measure along the identification of its fields."""
    for node in graph_named(port_cons_view, "forward").nodes:
        for port in node.inputsMetadata:
            assert "paired by" not in attributes(port)


@needs_viewer
def test_the_forward_graph_starts_at_the_first_entry_measure_and_ends_at_the_last_one(
    port_cons_view,
):
    """The forward graph of the cons-port trellis starts at the measure at
    the entry perch of the first period in time and ends at the continuation
    measure of the last, each at a boundary node first or last among the
    nodes."""
    forward = graph_named(port_cons_view, "forward")
    assert boundary_ports(forward, "start") == ["periods[5]/port/port:measure:dcsn"]
    assert boundary_ports(forward, "end") == ["periods[0]/disc/disc:measure:cntn"]
    assert [m.id for m in forward.nodes[0].outputsMetadata] == boundary_ports(forward, "start")
    assert [m.id for m in forward.nodes[-1].inputsMetadata] == boundary_ports(forward, "end")


@needs_viewer
def test_the_backward_graph_starts_at_the_continuation_value_of_the_last_stage(port_cons_view):
    """The backward graph of the cons-port trellis starts at the
    continuation value of the last stage of the last period, which the
    terminal value supplies, at a boundary node first among the nodes."""
    backward = graph_named(port_cons_view, "backward")
    assert boundary_ports(backward, "start") == [
        "periods[0]/disc/disc:function:cntn:V",
    ]
    assert [m.id for n in backward.nodes[:1] for m in n.outputsMetadata] == boundary_ports(
        backward, "start"
    )


@needs_viewer
def test_the_backward_graph_ends_at_the_decision_value_of_the_first_stage_in_time(
    port_cons_view,
):
    """The backward graph of the cons-port trellis ends at the value that
    its first stage in time exports, the decision value of `port`, which
    declares no arrival perch, written by that occurrence."""
    backward = graph_named(port_cons_view, "backward")
    given = [n for n in backward.nodes if attributes(n).get("kind") == "end"]
    assert boundary_ports(backward, "end") == [
        "periods[5]/port/port:function:dcsn:V",
    ]
    assert {occurrence_of(e.sourceNodeId) for n in given for e in n.incomingEdges} == {
        ("periods[5]", "port")
    }


@needs_viewer
@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_the_initial_diagram_of_a_trellis_holds_field_and_block_nodes_alone(
    port_cons_view, direction
):
    """The initial diagram of a whole trellis view holds field nodes and
    block nodes alone."""
    initial = graph_named(port_cons_view, f"{direction} initial diagram")
    kinds = {attribute_of(n, "kind") for n in initial.nodes}
    assert kinds <= {"field", "block"}, kinds


@needs_viewer
@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_each_node_of_a_trellis_initial_diagram_stands_in_the_layer_of_its_kind(
    port_cons_view, direction
):
    """Each field node of a trellis's initial diagram stands in a perch
    layer within its occurrence's layer, each block or shock node in the
    occurrence's layer, every layer within an occurrence's layer being a
    perch."""
    initial = graph_named(port_cons_view, f"{direction} initial diagram")
    for node in initial.nodes:
        parts = node.namespace.split("/")
        if attribute_of(node, "kind") == "field" and ":shck:" not in node.id:
            assert len(parts) == 3 and parts[2] in ("arvl", "dcsn", "cntn"), node.namespace
        else:
            # a block, or a shock, which belongs to no perch
            assert len(parts) == 2, node.namespace
    layers = initial.groupNodeAttributes
    assert {ns.split("/")[2] for ns in layers if ns.count("/") == 2} <= {"arvl", "dcsn", "cntn"}


@needs_viewer
def test_the_backward_initial_diagram_draws_as_many_join_wires_as_there_are_route_edges(
    port_cons_view,
):
    """The backward initial diagram of a trellis draws as many join wires as
    the backward builders graph has route edges with distinct ports, since
    that graph draws a wire once for each box that reads it."""
    given = [edge for _, edge in routed_edges(graph_named(port_cons_view, "backward"))]
    routed = routed_edges(graph_named(port_cons_view, "backward initial diagram"))
    assert given
    ports = {(edge.sourceNodeOutputId, edge.targetNodeInputId): edge for edge in given}
    assert len(routed) == len(ports), (len(routed), len(ports))


@needs_viewer
def test_the_forward_initial_diagram_draws_as_many_join_wires_as_its_routes_have_pairs(
    port_cons_view,
):
    """The forward initial diagram of a trellis draws as many join wires as
    the routes on the edges of the forward builders graph have pairs."""
    given = [edge for _, edge in routed_edges(graph_named(port_cons_view, "forward"))]
    routed = routed_edges(graph_named(port_cons_view, "forward initial diagram"))
    assert given
    ports = {(edge.sourceNodeOutputId, edge.targetNodeInputId): edge for edge in given}
    assert len(routed) == sum(len(attribute_of(edge, "route")["pairs"]) for edge in ports.values())


@needs_viewer
@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_each_join_of_a_trellis_initial_diagram_is_a_wire_between_the_fields_it_joins(
    port_cons_view, direction
):
    """Each join wire of a trellis's initial diagram runs between the
    continuation field of one occurrence and the field at the entry perch of
    the other."""
    initial = graph_named(port_cons_view, f"{direction} initial diagram")
    nodes = {n.id: n for n in initial.nodes}
    routed = routed_edges(initial)
    assert routed, direction
    for node, edge in routed:
        source = nodes[edge.sourceNodeId]
        assert attribute_of(node, "kind") == "field" and attribute_of(source, "kind") == "field"
        assert node.namespace.split("/")[2] == (
            "cntn" if direction == "backward" else entry_perch_of(node)
        )
        assert source.namespace.split("/")[2] == (
            entry_perch_of(source) if direction == "backward" else "cntn"
        )


@needs_viewer
@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_the_reading_port_of_each_join_wire_of_a_trellis_initial_diagram_names_its_join(
    port_cons_view, direction
):
    """The reading port of each join wire of a trellis's initial diagram
    carries the attribute `join`."""
    routed = routed_edges(graph_named(port_cons_view, f"{direction} initial diagram"))
    assert routed, direction
    for node, edge in routed:
        port = next(m for m in node.inputsMetadata if m.id == edge.targetNodeInputId)
        assert attribute_of(port, "join"), port


@needs_viewer
@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_each_join_wire_of_a_trellis_initial_diagram_carries_a_route_of_the_builders_graph(
    port_cons_view, direction
):
    """Each join wire of a trellis's initial diagram carries the route
    record of an edge of the builders graph of its direction."""
    given = [edge for _, edge in routed_edges(graph_named(port_cons_view, direction))]
    routed = routed_edges(graph_named(port_cons_view, f"{direction} initial diagram"))
    assert routed, direction
    for _, edge in routed:
        assert any(attribute_of(edge, "route") == attribute_of(e, "route") for e in given)


@needs_viewer
@pytest.mark.parametrize("graph_id", ["backward", "forward"])
def test_a_restricted_trellis_view_holds_the_occurrences_selected_under_the_whole_views_ids(
    restricted_view, port_cons_view, graph_id
):
    """The view of the cons-port trellis restricted to the consumption stage
    of periods 0 and 1 holds those two occurrences alone, each node but an
    `outside` node under the id that the whole view gives it."""
    graph = graph_named(restricted_view, graph_id)
    occurrences = {ns for ns in graph.groupNodeAttributes if ns.count("/") == 1}
    assert occurrences == {"periods[0]/cons", "periods[1]/cons"}, graph.id
    whole = {node.id for node in graph_named(port_cons_view, graph.id).nodes}
    assert {node.id for node in graph.nodes if attributes(node).get("kind") != "outside"} <= whole


# each mark as the port, its join, its outside occurrence, and the label and
# the target of its node, the last three each the occurrence outside the view
@needs_viewer
@pytest.mark.parametrize(
    ("graph_id", "side", "marks"),
    [
        pytest.param(
            "backward",
            "outputsMetadata",
            [
                (f"periods[{h}]/cons/cons:function:cntn:V", "a", *[f"periods[{h}]/disc"] * 3)
                for h in (1, 0)
            ],
            id="backward-continuation-value",
        ),
        # the consumption stage declares no arrival perch and is entered at
        # its decision perch
        pytest.param(
            "backward",
            "inputsMetadata",
            [
                (f"periods[{h}]/cons/cons:function:dcsn:V", "w → m", *[f"periods[{h}]/port"] * 3)
                for h in (1, 0)
            ],
            id="backward-decision-value",
        ),
        pytest.param(
            "forward",
            "outputsMetadata",
            [
                (f"periods[{h}]/cons/cons:measure:dcsn", "w → m", *[f"periods[{h}]/port"] * 3)
                for h in (1, 0)
            ],
            id="forward-decision-measure",
        ),
        pytest.param(
            "forward",
            "inputsMetadata",
            [
                (f"periods[{h}]/cons/cons:measure:cntn", "a", *[f"periods[{h}]/disc"] * 3)
                for h in (1, 0)
            ],
            id="forward-continuation-measure",
        ),
    ],
)
def test_a_join_that_leaves_a_restricted_view_is_marked_at_an_outside_node(
    restricted_view, graph_id, side, marks
):
    """Each join that leaves a restricted trellis view is a port of an
    `outside` node at the graph's root, labeled and targeted with the
    occurrence outside the view, the port carrying the join's label and that
    occurrence."""
    assert outside_marks(restricted_view, graph_id, side) == marks


@needs_viewer
def test_a_trellis_view_restricted_to_every_occurrence_is_the_whole_view(
    bound_port_cons_trellis, port_cons_view
):
    """The view of a trellis restricted to every period and every stage key
    of the trellis is the whole view."""
    every_period = range(len(bound_port_cons_trellis["periods"]))
    assert collection_as_json(
        to_model_explorer(
            bound_port_cons_trellis,
            periods=every_period,
            stages=["cons", "disc", "port"],
            initial=True,
        )
    ) == collection_as_json(port_cons_view)


@needs_viewer
@pytest.mark.parametrize(
    ("selection", "sentence"),
    [
        pytest.param(
            {"periods": [7]},
            "the trellis holds 6 periods, and periods[7] is none of them",
            id="period-the-trellis-does-not-hold",
        ),
        pytest.param(
            {"stages": ["nope"]},
            "the periods selected hold no stage 'nope'; they hold cons, disc, port",
            id="stage-no-period-holds",
        ),
        pytest.param(
            {"periods": []},
            "the selection holds no stage occurrence of the trellis",
            id="no-period",
        ),
    ],
)
def test_a_restriction_that_holds_no_occurrence_is_refused_in_one_sentence(
    bound_port_cons_trellis, selection, sentence
):
    """A restriction of a trellis view to an index or a stage key that the
    trellis does not hold, or to no occurrence, is refused under the rule
    `trellis-file-shape` in one sentence."""
    with pytest.raises(FactoryError) as refused:
        to_model_explorer(bound_port_cons_trellis, **selection)
    assert (refused.value.rule, refused.value.message) == ("trellis-file-shape", sentence)


@needs_viewer
def test_a_trellis_whose_occurrence_refuses_a_direction_refuses_that_graph_alone():
    """A trellis whose one occurrence refuses its backward builders graph
    draws that graph alone as one node that names the refusal at the
    occurrence."""
    stage = stage_from_text(FORWARD_ONLY_STAGE, "refused.bl")
    trellis = accrete(
        {"periods": [], "inter_connectors": []}, {"stages": {"only": stage}, "connectors": []}
    )
    backward, forward = to_model_explorer(trellis).graphs
    (node,) = backward.nodes
    assert node.label == "backward builders graph refused (not-constructed)"
    assert attributes(node)["refusal"].startswith("periods[0]/only: ")
    # the other direction is drawn
    assert len(forward.nodes) > 1


# the rows of the table of `node_place`: the view by the name of its
# fixture, the graph, the id of a node or of a layer, and the place that
# `node_place` answers
NODE_PLACES = [
    # in a stage view a namespace opens with the block
    pytest.param(
        "cons_methodized_without_calibration_view",
        "backward",
        "policy.InvEuler:Aggregation",
        ("", "policy"),
        id="stage-box-of-a-sub-builder",
    ),
    pytest.param(
        "cons_methodized_without_calibration_view",
        "backward",
        "cntn_to_dcsn:Pullback",
        ("", "cntn_to_dcsn"),
        id="stage-box-of-a-backward-builder",
    ),
    pytest.param(
        "cons_methodized_without_calibration_view",
        "backward",
        "policy:Evaluation",
        ("", "policy"),
        id="stage-box-of-the-policy-builder",
    ),
    pytest.param(
        "cons_methodized_without_calibration_view",
        "backward",
        "GraphInputs",
        ("", ""),
        id="stage-inputs-node",
    ),
    pytest.param(
        "cons_methodized_without_calibration_view",
        "backward",
        "policy" + LAYER_ID_ENDING,
        ("", "policy"),
        id="stage-layer-of-a-builder",
    ),
    # in an initial diagram a block's node is its own block, and a
    # field's node has none
    pytest.param(
        "cons_methodized_without_calibration_view",
        "backward initial diagram",
        "policy",
        ("", "policy"),
        id="stage-initial-diagram-block",
    ),
    pytest.param(
        "cons_methodized_without_calibration_view",
        "backward initial diagram",
        "cons:dcsn:c",
        ("", ""),
        id="stage-initial-diagram-field",
    ),
    pytest.param(
        "retiree_death_view", "forward", "forward:refused", ("", ""), id="stage-refused-graph"
    ),
    # in a trellis view a namespace opens with the period and the key
    pytest.param(
        "two_period_lesson_trellis_view",
        "backward",
        "periods[0]/cons/policy.InvEuler:Aggregation",
        ("periods[0]/cons", "policy"),
        id="trellis-box-of-a-sub-builder",
    ),
    pytest.param(
        "two_period_lesson_trellis_view",
        "backward",
        "periods[0]/cons/GraphOutputs",
        ("periods[0]/cons", ""),
        id="trellis-outputs-node",
    ),
    pytest.param(
        "two_period_lesson_trellis_view",
        "backward",
        "periods[1]/port" + LAYER_ID_ENDING,
        ("periods[1]/port", ""),
        id="trellis-layer-of-an-occurrence",
    ),
    pytest.param(
        "two_period_lesson_trellis_view",
        "backward",
        "periods[1]" + LAYER_ID_ENDING,
        ("periods[1]", ""),
        id="trellis-layer-of-a-period",
    ),
    # a boundary node of a trellis stands at the graph's root
    pytest.param(
        "two_period_lesson_trellis_view",
        "backward",
        "start:periods[0]/disc/disc:function:cntn:V",
        ("", ""),
        id="trellis-boundary-node",
    ),
    # in a trellis's initial diagram a block's id stands under its
    # occurrence
    pytest.param(
        "port_cons_view",
        "backward initial diagram",
        "periods[0]/cons/cons:cntn:V",
        ("periods[0]/cons", ""),
        id="trellis-initial-diagram-field",
    ),
    pytest.param(
        "port_cons_view",
        "backward initial diagram",
        "periods[0]/cons/cntn_to_dcsn",
        ("periods[0]/cons", "cntn_to_dcsn"),
        id="trellis-initial-diagram-block",
    ),
    pytest.param(
        "port_cons_view",
        "backward initial diagram",
        "periods[0]/cons/cntn" + LAYER_ID_ENDING,
        ("periods[0]/cons", ""),
        id="trellis-initial-diagram-layer-of-a-perch",
    ),
    pytest.param(
        "port_cons_view",
        "backward initial diagram",
        "periods[0]/cons" + LAYER_ID_ENDING,
        ("periods[0]/cons", ""),
        id="trellis-initial-diagram-layer-of-an-occurrence",
    ),
    pytest.param(
        "port_cons_view",
        "backward initial diagram",
        "periods[0]" + LAYER_ID_ENDING,
        ("periods[0]", ""),
        id="trellis-initial-diagram-layer-of-a-period",
    ),
]


@needs_viewer
@pytest.mark.parametrize(("view", "graph_id", "node_id", "place"), NODE_PLACES)
def test_node_place_reads_the_occurrence_and_the_block_of_a_node_from_its_namespace(
    request, view, graph_id, node_id, place
):
    """`node_place` answers the stage occurrence and the block that a node
    or a layer of a view stands in, read from the namespace that the view
    holds for a node, or from the id of a layer."""
    assert node_place(request.getfixturevalue(view), graph_id, node_id) == place


@needs_viewer
def test_node_place_puts_a_box_of_one_branch_in_its_block(retiree_death_view):
    """`node_place` puts a box of one branch of a branching block,
    `<block>:<operator>:<branch>`, in that block."""
    place = node_place(retiree_death_view, "backward", "cntn_to_dcsn:Pullback:survive")
    assert place.block == "cntn_to_dcsn"


@needs_viewer
@pytest.mark.parametrize(
    ("graph_id", "node_id", "error", "match"),
    [
        pytest.param(
            "backward",
            "no:such",
            KeyError,
            "the graph 'backward' holds no node 'no:such'",
            id="node-the-graph-does-not-hold",
        ),
        pytest.param(
            "sideways",
            "GraphInputs",
            ValueError,
            "and none named 'sideways'",
            id="graph-the-view-does-not-hold",
        ),
    ],
)
def test_node_place_refuses_a_node_or_a_graph_that_the_view_does_not_hold(
    cons_methodized_without_calibration_view, graph_id, node_id, error, match
):
    """`node_place` refuses a node that the graph does not hold, or a graph
    that the view does not hold, with the error and the sentence of its row;
    an answer in place of the refusal fails the test."""
    with pytest.raises(error, match=match):
        node_place(cons_methodized_without_calibration_view, graph_id, node_id)


@needs_viewer
def test_the_view_of_a_trellis_is_built_once_for_its_two_files(
    trellis_builds, written_trellis_files
):
    """`write_model_explorer` writes the two files of a trellis,
    `trellis.graph.json` and `trellis.edge-overlays.json`, from one build of
    its view."""
    assert len(trellis_builds) == 1
    assert [p.name for p in written_trellis_files] == [
        "trellis.graph.json",
        "trellis.edge-overlays.json",
    ]


@needs_viewer
def test_the_graph_file_of_a_trellis_holds_its_view_in_the_viewers_classes(
    port_cons_view, written_trellis_files
):
    """The graph file of a trellis holds its view as JSON, which reads back
    into the viewer's own classes as the view does."""
    # the viewer, an optional extra, is imported where a test needs it
    import dacite
    from model_explorer import graph_builder

    graph_text = written_trellis_files[0].read_text(encoding="utf-8")
    assert json.loads(graph_text) == collection_as_json(port_cons_view)
    assert dacite.from_dict(graph_builder.GraphCollection, json.loads(graph_text)) == (
        collection_in_viewer_classes(port_cons_view)
    )


@needs_viewer
def test_the_overlays_file_of_a_trellis_paints_edges_of_its_view_with_no_label(
    port_cons_view, written_trellis_files
):
    """The overlays file of a trellis paints only edges of its view, at
    least one, each with no label."""
    import dacite
    from model_explorer import graph_builder

    overlays_text = written_trellis_files[1].read_text(encoding="utf-8")
    overlays = dacite.from_dict(graph_builder.EdgeOverlaysData, json.loads(overlays_text))
    edges = {
        (e.sourceNodeId, n.id)
        for g in port_cons_view.graphs
        for n in g.nodes
        for e in n.incomingEdges
    }
    painted = [(e.sourceNodeId, e.targetNodeId) for o in overlays.overlays for e in o.edges]
    assert painted and set(painted) <= edges
    assert all(e.label is None for o in overlays.overlays for e in o.edges)


@needs_viewer
def test_explore_opens_the_backward_graph_of_a_trellis_at_its_periods(
    bound_port_cons_trellis, trellis_builds, served_pages, tmp_path
):
    """`explore` opens the backward graph of a trellis, from one build of
    its view, with the layers of its six periods, the first in time first."""
    explore(bound_port_cons_trellis, folder=tmp_path, open_browser=True)
    ((kwargs,),) = [served_pages]
    assert kwargs["layers"] == tuple(f"periods[{h}]" for h in range(5, -1, -1))
    assert kwargs["graph_id"] == "backward" and len(trellis_builds) == 1


@needs_viewer
@pytest.mark.parametrize(
    ("view", "located"),
    [
        pytest.param("bound_port_cons_trellis", "periods[1]", id="trellis-of-six-periods"),
        pytest.param("cons", None, id="stage"),
        pytest.param("one_period_cons_trellis", None, id="trellis-of-one-period"),
    ],
)
def test_explore_locates_a_trellis_on_the_first_period_after_the_terminal_one(
    request, trellis_builds, served_pages, tmp_path, view, located
):
    """`explore` locates the page on `periods[1]`, the first period after
    the terminal one, only for a trellis of several periods, not for a stage
    or a trellis of one period."""
    explore(request.getfixturevalue(view), folder=tmp_path, open_browser=True)
    assert [kwargs["located"] for kwargs in served_pages] == [located]


@needs_viewer
def test_the_page_selects_the_layer_located_and_none_where_none_is_located(
    port_cons_view, tmp_path
):
    """The state of the page that `serve` writes into its address selects
    the layer on which the view is located, or no node where it is located
    on none."""
    paths = _write_view(port_cons_view, tmp_path / "view")
    with answering_server(VIEWER_HEALTH) as port:
        url = serve(paths[0], port=port, layers=("periods[1]",), located="periods[1]")
        fitted = serve(paths[0], port=port)
    (pane,) = json.loads(unquote(url.partition("?data=")[2]))["uiState"]["paneStates"]
    assert pane["selectedNodeId"] == "periods[1]___group___"
    (pane,) = json.loads(unquote(fitted.partition("?data=")[2]))["uiState"]["paneStates"]
    assert pane["selectedNodeId"] == ""
