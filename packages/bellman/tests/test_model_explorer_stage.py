"""The view of a stage in Model Explorer: its graphs, nodes, edges, ports,
layers, labels, colors and overlays, its initial diagrams, its refusals, the
functions that read a view back, and the labels of the evaluations in the
drawings of the builders graphs."""

import dataclasses
import functools
import json
import re
from types import SimpleNamespace

import pytest
from application_files import CONS_METHODS, CORPUS
from model_explorer_views import (
    FORWARD_ONLY_STAGE,
    STAGE_GRAPHS,
    applied_layer_style,
    attributes,
    builders_graphs,
    direction_rows,
    graph_named,
    layers_of,
    needs_viewer,
    reached_box_identity,
    stage_rows,
    two_period_lesson_trellis,
)
from stage_builders import stage_from_text
from stage_graphs import operator_boxes
from stage_texts import corpus_text

from bellman.display.drawing import box_symbol, drawn_sorts, wire_label
from bellman.factory.model_explorer import (
    OPENED_GRAPH,
    PALETTE,
    PERCH_ORDER,
    SHORT_LABELS,
    _layer_config,
    _refused_graph,
    _refused_label,
    _viewer,
    _writers,
    label_sources,
    port_label,
)
from bellman.native.identity import box_identity
from bellman.native.labels import is_wiring, value_aggregations_of
from bellman.refusals import NotConstructed
from bellman.stage import (
    BOUNDARY_IDS,
    INITIAL_IDS,
    LAYER_COLORS,
    NODE_STYLE,
    OUTPUT_STYLE,
    layers_to_open,
    perch_overlays,
    to_model_explorer,
    to_source,
    wire_counts,
    write_model_explorer,
)
from bellman.stage.grains import graph_of, wire_table
from bellman.stage.pieces import drawing_arguments

# the colors of the view, each with its token in the stylesheet of Bellman
# Workbench
WHITE = "#FFFFFF"  # --bf-face
FIRST_ICE = "#EDF7FC"  # --bl-ice, the first step of the ice
SECOND_ICE = "#C5E5F1"  # --bl-ice-2, the second step of the ice
THIRD_ICE = "#91BED7"  # --bl-ice-3, the third step of the ice
NAVY = "#172A52"  # --bl-navy
ULTRAMARINE = "#214EDA"  # --bl-ultramarine
ORANGE_LINE = "#C45C1D"  # --bf-accent-line, the orange of a line


# the four lines of `cons.bl` that `with_three_values` replaces
REPLACED_LINES = (
    "(V : [-inf, inf) @ !vlu) : !dcsn]",
    "V        = 𝑢(c) + V[>]          :: [id=value]",
    "(V) : !dcsn -> (V[<] : ℝ @ !vlu)",
    "V[<] = V                        :: [id=value]",
)


# the rows of the tables over the initial diagrams
INITIAL_ROWS = direction_rows("cons", "sa_savings", "cons_methodized_without_calibration")


def with_three_values(text, second, third):
    """The text of `cons.bl` with each line of `REPLACED_LINES` replaced, so
    that its decision builder and its arrival builder write the values
    `second` and `third` beside V."""
    replacements = (
        f"(V : [-inf, inf) @ !vlu, {second} : ℝ @ !vlu, {third} : ℝ @ !vlu) : !dcsn]",
        f"V = 𝑢(c) + V[>]\n    {second} = V\n    {third} = V",
        f"(V, {second}, {third}) : !dcsn -> "
        f"(V[<] : ℝ @ !vlu, {second}[<] : ℝ @ !vlu, {third}[<] : ℝ @ !vlu)",
        f"V[<] = V\n    {second}[<] = {second}\n    {third}[<] = {third}",
    )
    for before, after in zip(REPLACED_LINES, replacements):
        text = text.replace(before, after)
    return text


def ports_at_edges(graph):
    """The edges of a graph, each with the output port of its source node
    and the input port of its target node."""
    nodes = {node.id: node for node in graph.nodes}
    for node in graph.nodes:
        inputs = {port.id: port for port in node.inputsMetadata}
        for edge in node.incomingEdges:
            outputs = {port.id: port for port in nodes[edge.sourceNodeId].outputsMetadata}
            yield edge, outputs[edge.sourceNodeOutputId], inputs[edge.targetNodeInputId]


def output_labels(graph):
    """The label of each output port of a graph, by the port's id."""
    return {
        port.id: attributes(port)["label"] for node in graph.nodes for port in node.outputsMetadata
    }


def distinct_wires(collection):
    """The number of distinct wires of each builders graph of a view, counted
    from its edges as the pairs of a source node and its output port."""
    return {
        graph.id: len(
            {
                (edge.sourceNodeId, edge.sourceNodeOutputId)
                for node in graph.nodes
                for edge in node.incomingEdges
            }
        )
        for graph in builders_graphs(collection)
    }


def color_values(path):
    """The values of every key of a JSON file whose name ends with `Color`,
    gathered from each object as the file is read."""
    found = set()

    def gathered(pairs):
        found.update(value for key, value in pairs if key.endswith("Color") and value is not None)
        return dict(pairs)

    json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=gathered)
    return found


def box_record(identity, reads=(), writes=()):
    """An object with the identity, the wires read and the wires written of a
    box of a hypergraph, each wire named by its identity alone."""

    def wires(names):
        return SimpleNamespace(inside=[SimpleNamespace(identity=name) for name in names])

    return SimpleNamespace(identity=identity, dom=wires(reads), cod=wires(writes))


@pytest.fixture(scope="module")
def three_value_outputs():
    """The consumption stage whose decision builder and arrival builder write
    the values W and Z beside V."""
    return stage_from_text(
        with_three_values(corpus_text("cons"), "W", "Z"), "three_value_outputs.bl"
    )


@pytest.fixture(scope="module")
def long_value_outputs():
    """The consumption stage whose decision builder and arrival builder write
    the values Welfare and Zenith beside V, so that the labels of their
    evaluations are longer than two lines of a box."""
    text = with_three_values(corpus_text("cons"), "Welfare", "Zenith")
    return stage_from_text(text, "long_value_outputs.bl")


@pytest.fixture(scope="module")
def forward_only():
    """The stage of `FORWARD_ONLY_STAGE`, which has two forward blocks and no
    backward block."""
    return stage_from_text(FORWARD_ONLY_STAGE, "refused.bl")


@pytest.fixture(scope="module")
def cons_without_grid_line():
    """The consumption stage bound with its methods file less the line
    `[id=grid]`, which defines the coordinate function m_d[>] of the
    endogenous grid."""
    addition = "\n".join(
        line for line in CONS_METHODS.read_text().splitlines() if "[id=grid]" not in line
    )
    stage = stage_from_text(corpus_text("cons"), "cons.bl")
    return stage.methodize({"text": addition, "origin": str(CONS_METHODS)})


@pytest.fixture(scope="module")
def initial_diagram(view_of):
    """`initial_diagram(stage, direction)`: the initial diagram of one
    direction in the view of a stage, with the hypergraph it is drawn from and
    what the drawing of that hypergraph reads, made once for the module."""

    @functools.cache
    def diagram(stage, direction):
        hypergraph = graph_of(stage, "initial", direction)
        blocks = [box for box in hypergraph.boxes if not is_wiring(box)]
        graph = graph_named(view_of(stage), INITIAL_IDS[direction])
        return SimpleNamespace(
            graph=graph,
            hypergraph=hypergraph,
            blocks=blocks,
            sorts={str(identity): sort for identity, sort in drawn_sorts(hypergraph).items()},
            names=drawing_arguments(stage, hypergraph)["wire_names"],
            # the block that writes each field, and the fields that the blocks
            # read
            written={str(ob.identity): block.name for block in blocks for ob in block.cod.inside},
            read={str(ob.identity) for block in blocks for ob in block.dom.inside},
            fields=[node for node in graph.nodes if attributes(node).get("kind") == "field"],
            block_nodes=[node for node in graph.nodes if attributes(node).get("kind") == "block"],
        )

    return diagram


@pytest.fixture(scope="module")
def cons_overlays(cons, model_explorer_package):
    """The three perch overlays of the view of `cons`."""
    return perch_overlays(cons)


@pytest.fixture(scope="module")
def backward_graph_with_short_labels(cons_methodized_without_calibration, model_explorer_package):
    """The backward builders graph of the view of methodized `cons`, made
    with the switch `SHORT_LABELS` of the view on."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("bellman.factory.model_explorer.SHORT_LABELS", True)
        return graph_named(to_model_explorer(cons_methodized_without_calibration), "backward")


@pytest.fixture(scope="module")
def cons_drawing(cons):
    """The DOT source of the drawing of the backward builders graph of
    `cons`."""
    return cons.builder.bwd.diagram().source


# The collection and its graphs


@needs_viewer
def test_the_view_of_a_stage_is_a_collection_of_the_viewers_class(
    cons_methodized_without_calibration, view_of
):
    """The view of a stage is a `GraphCollection` of the viewer's own
    module."""
    from model_explorer import graph_builder

    assert isinstance(view_of(cons_methodized_without_calibration), graph_builder.GraphCollection)


@needs_viewer
@pytest.mark.parametrize("name", stage_rows("cons", "cons_methodized_without_calibration"))
def test_a_view_holds_the_two_initial_diagrams_and_then_the_two_builders_graphs(
    name, request, view_of
):
    """The view of a stage holds its backward and its forward initial
    diagrams and then its backward and its forward builders graphs."""
    collection = view_of(request.getfixturevalue(name))
    assert [graph.id for graph in collection.graphs] == STAGE_GRAPHS


def test_each_initial_diagram_is_named_by_its_direction():
    """The initial diagram of each direction is named by that direction."""
    assert INITIAL_IDS == {
        "backward": "backward initial diagram",
        "forward": "forward initial diagram",
    }


def test_the_constant_opened_graph_names_the_backward_builders_graph():
    """The constant `OPENED_GRAPH`, the graph that the page of a view opens on
    where no graph is named, is the backward builders graph."""
    assert OPENED_GRAPH == "backward"


@needs_viewer
def test_the_view_of_a_bound_version_is_labeled_by_the_stage_and_its_binding(
    cons_methodized_without_calibration, view_of
):
    """The view of methodized `cons` is labeled `cons methodized`."""
    assert view_of(cons_methodized_without_calibration).label == "cons methodized"


# The nodes of a builders graph and their namespaces


@needs_viewer
@pytest.mark.parametrize(
    ("name", "direction"), direction_rows("cons_methodized_without_calibration", "sa_savings")
)
def test_a_builders_graph_has_one_node_for_each_primitive_operator(
    name, direction, request, view_of
):
    """The nodes of a builders graph, apart from `Inputs` and `Outputs`, are
    its primitive operators, each under the identity of its box."""
    stage = request.getfixturevalue(name)
    graph = graph_named(view_of(stage), direction)
    operator_nodes = {node.id for node in graph.nodes if node.id not in BOUNDARY_IDS}
    assert operator_nodes == {str(box_identity(box)) for box in operator_boxes(stage, direction)}


@needs_viewer
@pytest.mark.parametrize(
    ("name", "direction"), direction_rows("cons_methodized_without_calibration", "sa_savings")
)
def test_the_namespace_of_a_node_reaches_its_box_through_the_handles_of_the_stage(
    name, direction, request, view_of
):
    """The namespace of a node names the builder and the sub-builder that
    hold its box, by which the handles of the stage reach the box."""
    stage = request.getfixturevalue(name)
    graph = graph_named(view_of(stage), direction)
    namespaces = {node.id: node.namespace for node in graph.nodes}
    for box in operator_boxes(stage, direction):
        identity = box_identity(box)
        assert (
            reached_box_identity(stage, direction, namespaces[str(identity)], identity) == identity
        )


@needs_viewer
@pytest.mark.parametrize(
    ("name", "node", "namespace"),
    [
        pytest.param(
            "cons_methodized_without_calibration",
            "policy.InvEuler:Aggregation",
            "policy",
            id="a statement of the policy builder of cons",
        ),
        pytest.param(
            "sa_savings",
            "cntn_to_dcsn.risk_ce:Pullback",
            "cntn_to_dcsn/risk_ce",
            id="a box of an authored node of sa_savings",
        ),
        pytest.param(
            "sa_savings",
            "policy.objective:Argmax",
            "policy",
            id="a statement of the policy builder of sa_savings",
        ),
    ],
)
def test_the_namespace_of_a_node_names_its_builder_and_its_sub_builder(
    name, node, namespace, request, view_of
):
    """The namespace of the node of a statement's box is its builder, and
    that of a box of an authored `!node` is its builder followed by the
    sub-builder that the `!node` forms."""
    backward = graph_named(view_of(request.getfixturevalue(name)), "backward")
    assert {n.id: n.namespace for n in backward.nodes}[node] == namespace


# The layers of a builders graph


@needs_viewer
def test_the_edges_that_cross_the_border_of_a_layer_carry_the_wires_of_its_builder(cons, view_of):
    """The edges that cross the border of the policy layer of `cons` carry
    the wire 𝑉≻, which the primitives of the builder read, and the policy 𝑐,
    which the builder gives."""
    graph = graph_named(view_of(cons), "backward")
    layer = {n.id for n in graph.nodes if n.namespace.split("/")[0] == "policy"}
    crossing_in = {
        e.targetNodeInputId
        for n in graph.nodes
        if n.id in layer
        for e in n.incomingEdges
        if e.sourceNodeId not in layer
    }
    crossing_out = {
        e.sourceNodeOutputId
        for n in graph.nodes
        if n.id not in layer
        for e in n.incomingEdges
        if e.sourceNodeId in layer
    }
    assert crossing_in == {"cons:function:cntn:V"}
    assert crossing_out == {"policy:Evaluation:c:result"}


@needs_viewer
def test_each_builder_of_a_builders_graph_is_one_layer(cons, view_of):
    """The layers of the backward builders graph of `cons` are its three
    builders."""
    graph = graph_named(view_of(cons), "backward")
    assert set(graph.groupNodeAttributes) == {"cntn_to_dcsn", "dcsn_to_arvl", "policy"}


# The edges and the ports of a builders graph


@needs_viewer
def test_a_builders_graph_has_one_edge_for_each_wire_that_a_box_reads_or_the_graph_gives(
    cons_methodized_without_calibration, view_of
):
    """A builders graph has one edge for each wire that a box reads and one
    for each wire that the graph gives to `Outputs`."""
    graph = graph_named(view_of(cons_methodized_without_calibration), "backward")
    hypergraph = graph_of(
        cons_methodized_without_calibration, "builders", "backward", grain="primitive"
    )
    edges = [(n.id, e) for n in graph.nodes for e in n.incomingEdges]
    reads = sum(
        len(box.dom.inside)
        for box in operator_boxes(cons_methodized_without_calibration, "backward")
    )
    assert len(edges) == reads + len(hypergraph.cod.inside)


@needs_viewer
def test_each_edge_joins_an_output_port_to_an_input_port_under_the_id_of_its_wire(
    cons_methodized_without_calibration, view_of
):
    """Each edge joins an output port of its source node to an input port of
    its target node, both under the id of the one wire it carries."""
    graph = graph_named(view_of(cons_methodized_without_calibration), "backward")
    nodes = {n.id: n for n in graph.nodes}
    for node in graph.nodes:
        for edge in node.incomingEdges:
            assert edge.sourceNodeId in nodes
            assert edge.sourceNodeOutputId == edge.targetNodeInputId  # one wire, one port id
            source_meta = {m.id: m for m in nodes[edge.sourceNodeId].outputsMetadata}
            target_meta = {m.id: m for m in node.inputsMetadata}
            assert edge.sourceNodeOutputId in source_meta and edge.targetNodeInputId in target_meta


@needs_viewer
@pytest.mark.parametrize("end", ["output port", "input port"])
def test_each_port_of_an_edge_shows_a_label_a_type_and_the_perch_and_the_role_of_its_wire(
    end, cons_methodized_without_calibration, view_of
):
    """Each port at an end of an edge shows a label and a type, the perch
    where its wire stands at one, and the role of its wire."""
    graph = graph_named(view_of(cons_methodized_without_calibration), "backward")
    hypergraph = graph_of(
        cons_methodized_without_calibration, "builders", "backward", grain="primitive"
    )
    identities = {str(identity): identity for identity in drawn_sorts(hypergraph)}
    wires = wire_table(cons_methodized_without_calibration)
    for _, output, input_ in ports_at_edges(graph):
        item = output if end == "output port" else input_
        attrs = attributes(item)
        # `__tensor_tag` is the row that holds the label by which the viewer
        # names a port
        assert "__tensor_tag" in attrs and attrs["__tensor_tag"]
        assert "type" in attrs
        # a wire at a perch names it, and a wire at none, the result of an
        # operation, writes no empty row
        identity = identities[item.id]
        assert attrs.get("perch") == identity.perch
        assert attrs.get("perch", "arvl") in ("arvl", "dcsn", "cntn")
        # the role of the wire's sort, which `wire_table` records; the
        # endogenous grid `m_d[>]` carries the role of its field, a state
        assert attrs.get("role") == (wires.sort_of(identity).role or None)


@needs_viewer
@pytest.mark.parametrize("builder", ["cntn_to_dcsn", "dcsn_to_arvl", "policy"])
def test_the_type_of_a_port_is_the_type_that_the_builders_signature_prints(
    builder, cons_methodized_without_calibration, view_of
):
    """The type of the port of each wire of a builder's signature is the
    type that the signature prints for the wire."""
    graph = graph_named(view_of(cons_methodized_without_calibration), "backward")
    ports = {m.id: attributes(m) for n in graph.nodes for m in n.inputsMetadata}
    signature = cons_methodized_without_calibration.builder.bwd[builder].signature()
    for wire in signature.inputs + signature.outputs:
        assert ports[str(wire.identity)]["type"] == wire.type, wire.identity


@needs_viewer
def test_a_wire_has_one_edge_to_each_box_that_reads_it_from_the_one_port_of_its_writer(
    cons_methodized_without_calibration, view_of
):
    """A wire has one edge to each box that reads it, each from the one
    output port that its writer holds for it."""
    graph = graph_named(view_of(cons_methodized_without_calibration), "backward")
    nodes = {n.id: n for n in graph.nodes}
    edges = [(n.id, e) for n in graph.nodes for e in n.incomingEdges]
    # the wire the pullback writes is read by one box, the aggregation
    readers = [(t, e) for t, e in edges if e.sourceNodeId == "cntn_to_dcsn:Pullback"]
    assert [t for t, _ in readers] == ["cntn_to_dcsn:Aggregation"]
    # a wire two boxes read, `𝑐≻`
    readers = [(t, e) for t, e in edges if e.sourceNodeOutputId == "cons:function:cntn:c"]
    assert sorted(t for t, _ in readers) == [
        "policy.grid:Aggregation",
        "policy.identification:Pullback",
    ]
    assert {e.sourceNodeId for _, e in readers} == {"policy.InvEuler:Aggregation"}
    written = [m.id for m in nodes["policy.InvEuler:Aggregation"].outputsMetadata]
    assert written.count("cons:function:cntn:c") == 1


@needs_viewer
def test_the_output_port_of_an_edge_shows_its_wire_as_the_input_port_does(cons, view_of):
    """The output port at the start of each edge shows the label, the perch,
    the type and the role of its wire as the input port at its end does."""
    # the side panel names an output that one node reads by that node's
    # label and lists no row of an output whose key begins with two
    # underscores, so each port holds the wire's label under `label` as well
    # as under `__tensor_tag`
    graph = graph_named(view_of(cons), "backward")
    fields = ("label", "perch", "type", "role")
    compared = 0
    for edge, output_port, input_port in ports_at_edges(graph):
        output, input_ = attributes(output_port), attributes(input_port)
        assert [output.get(f) for f in fields] == [input_.get(f) for f in fields], edge
        assert output["label"] == input_["__tensor_tag"], edge
        compared += 1
    assert compared == sum(len(n.incomingEdges) for n in graph.nodes) > 0


@needs_viewer
def test_the_node_inputs_of_cons_gives_the_continuation_value(cons, view_of):
    """The node `Inputs` of the backward builders graph of `cons` has one
    output port, the continuation value 𝑉≻(a), with its perch, its type and
    its role."""
    nodes = {n.id: n for n in graph_named(view_of(cons), "backward").nodes}
    shown = [attributes(m) for m in nodes["GraphInputs"].outputsMetadata]
    assert [tuple(s[f] for f in ("label", "perch", "type", "role")) for s in shown] == [
        ("𝑉≻(a)", "cntn", "Xa → [−∞, ∞)", "value"),
    ]


# The labels of the nodes and the ports


@needs_viewer
def test_the_label_of_a_node_is_the_symbol_that_the_drawing_gives_its_box(
    cons_methodized_without_calibration, view_of
):
    """The label of a node, less the mark of its method, is the symbol that
    the drawing gives its box, with the law of motion named as the card of
    the box names it."""
    nodes = {
        n.id: n
        for n in graph_named(view_of(cons_methodized_without_calibration), "backward").nodes
    }
    hypergraph = graph_of(
        cons_methodized_without_calibration, "builders", "backward", grain="primitive"
    )
    aggregations = value_aggregations_of(hypergraph)
    for box in operator_boxes(cons_methodized_without_calibration, "backward"):
        node = nodes[str(box_identity(box))]
        # the name the box's card gives the law of motion the box
        # references, where it references one
        record = cons_methodized_without_calibration.builder.bwd.primitives[box.name].denote()
        named = {held.identity: held.symbol for held in record.definitions}
        law = next((named[ref] for ref in box.data if getattr(ref, "kind", None) == "g"), None)
        mark = " · " + attributes(node).get("method", "")
        assert node.label.removesuffix(mark) == box_symbol(box, aggregations, law), box.name


@needs_viewer
@pytest.mark.parametrize("side", ["inputs", "outputs"])
def test_the_label_of_a_port_is_the_label_that_the_drawing_gives_its_wire(
    side, cons_methodized_without_calibration, view_of
):
    """The label of each port of a node is the label that the drawing gives
    its wire."""
    nodes = {
        n.id: n
        for n in graph_named(view_of(cons_methodized_without_calibration), "backward").nodes
    }
    hypergraph = graph_of(
        cons_methodized_without_calibration, "builders", "backward", grain="primitive"
    )
    # the names the drawing is given, from the one function that gives
    # them, and the sorts it reads itself
    names = drawing_arguments(cons_methodized_without_calibration, hypergraph)["wire_names"]
    sorts = drawn_sorts(hypergraph)
    for box in operator_boxes(cons_methodized_without_calibration, "backward"):
        node = nodes[str(box_identity(box))]
        wires, items = (
            (box.dom.inside, node.inputsMetadata)
            if side == "inputs"
            else (box.cod.inside, node.outputsMetadata)
        )
        ports = {m.id: attributes(m) for m in items}
        for ob in wires:
            label = wire_label(sorts[ob.identity], names.get(ob.identity))
            assert ports[str(ob.identity)]["__tensor_tag"] == label


@needs_viewer
def test_the_output_of_the_decision_pullback_is_labeled_by_the_value_at_the_law_of_motion(
    cons_methodized_without_calibration, view_of
):
    """The output port of the pullback of the decision builder of methodized
    `cons` is labeled 𝑉≻(𝑔(m_d, 𝑐(m_d))), the continuation value at the law of
    motion at the policy."""
    nodes = {
        n.id: n
        for n in graph_named(view_of(cons_methodized_without_calibration), "backward").nodes
    }
    output = nodes["cntn_to_dcsn:Pullback"].outputsMetadata[0]
    assert attributes(output)["__tensor_tag"] == "𝑉≻(𝑔(m_d, 𝑐(m_d)))"


@needs_viewer
@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        pytest.param(
            "backward",
            {
                "GraphInputs": "Inputs",
                "cntn_to_dcsn:Pullback": "𝑉≻ ∘ 𝑔≻",
                "cntn_to_dcsn:Aggregation": "𝐺",
                "cntn_to_dcsn:Evaluation": "𝑉(m_d) · !Linear",
                "dcsn_to_arvl:Pullback": "𝑉 ∘ 𝑔≺",
                "dcsn_to_arvl:Aggregation": "𝐺",
                # the arrival value reads `m` alone and is no function of `l`
                "dcsn_to_arvl:Evaluation": "𝑉≺(m)",
                "policy.InvEuler:Aggregation": "𝐺 · InvEuler",
                "policy.grid:Aggregation": "𝐺 · grid",
                "policy.identification:Pullback": "𝑐 ∘ 𝑚_d≻",
                "policy:Evaluation": "𝑐(m_d)",
                "GraphOutputs": "Outputs",
            },
            id="backward",
        ),
        pytest.param(
            "forward",
            {
                "GraphInputs": "Inputs",
                "arvl_to_dcsn:Pushforward": "𝑔≺∗μ",
                "dcsn_to_cntn:Pushforward": "𝑔≻∗μ",
                "GraphOutputs": "Outputs",
            },
            id="forward",
        ),
    ],
)
def test_each_node_of_methodized_cons_is_labeled_by_the_symbol_of_its_box(
    direction, expected, cons_methodized_without_calibration, view_of
):
    """Each node of a builders graph of methodized `cons` is labeled by the
    symbol of its box, followed after a dot by the statement it is born at or
    by the method bound within it."""
    graph = graph_named(view_of(cons_methodized_without_calibration), direction)
    assert {node.id: node.label for node in graph.nodes} == expected


@needs_viewer
@pytest.mark.parametrize("name", stage_rows(*CORPUS))
def test_no_label_of_a_node_holds_the_words_at_the_output_or_a_law_written_out_at_a_policy(
    name, request, view_of
):
    """No label of a node of the view of a stage file holds the words `at the
    output`, or `(·`, a law of motion or an aggregator written out at a
    policy."""
    for graph in view_of(request.getfixturevalue(name)).graphs:
        for node in graph.nodes:
            assert "at the output" not in node.label, (name, node.id)
            assert "(·" not in node.label, (name, node.id)


@needs_viewer
def test_an_identification_that_reads_no_coordinate_function_shows_the_drawings_symbol(
    cons_without_grid_line, view_of
):
    """The node of the identification `c = c[>]` of `cons` bound without the
    line that defines m_d[>], in a view that refuses no graph, shows the
    symbol that the drawing of the same graph shows for its box."""
    # without that line the identification reads no state wire and
    # references the aggregator of the policy builder, and no law of motion;
    # no graph of the view is refused: no node holds the row `refusal`
    held = [node for graph in view_of(cons_without_grid_line).graphs for node in graph.nodes]
    assert not any("refusal" in attributes(node) for node in held)
    source = cons_without_grid_line.builder.bwd.primitives.diagram().source
    # the label of the box's DOT statement, which stands before its tooltip
    drawn = re.search(r'\[label="([^"]*)" tooltip="policy\.identification:Pullback — ', source)
    backward = graph_named(view_of(cons_without_grid_line), "backward")
    nodes = {node.id: node for node in backward.nodes}
    assert nodes["policy.identification:Pullback"].label == drawn.group(1)


# The refusals


@needs_viewer
def test_a_refused_builders_graph_is_one_node_that_states_the_refusal(forward_only, view_of):
    """The builders graph of a direction that the construction refuses is one
    node, labeled by the direction and the rule of the refusal, whose row
    `refusal` holds the text of the refusal."""
    with pytest.raises(NotConstructed):
        graph_of(forward_only, "builders", "backward")
    backward = graph_named(view_of(forward_only), "backward")
    assert len(backward.nodes) == 1
    assert backward.nodes[0].label == "backward builders graph refused (not-constructed)"
    assert attributes(backward.nodes[0])["refusal"] == (
        "address 'stage': no backward builder (rule not-constructed)"
    )


@needs_viewer
def test_the_refusal_of_one_direction_leaves_the_graph_of_the_other(forward_only, view_of):
    """The forward builders graph of a stage whose backward builders graph is
    refused holds its nodes."""
    with pytest.raises(NotConstructed):
        graph_of(forward_only, "builders", "backward")
    assert len(graph_named(view_of(forward_only), "forward").nodes) > 1


@needs_viewer
def test_the_backward_initial_diagram_of_a_stage_with_no_backward_block_is_empty(
    forward_only, view_of
):
    """The backward initial diagram of a stage with no backward block holds
    no field and no block, and so no node and no layer, and is not
    refused."""
    initial = graph_named(view_of(forward_only), "backward initial diagram")
    assert initial.nodes == [] and initial.groupNodeAttributes == {}


@needs_viewer
def test_the_forward_initial_diagram_holds_each_state_in_its_perch_and_the_blocks_outside(
    forward_only, view_of
):
    """The forward initial diagram of the stage with no backward block holds
    its three states, each in the layer of its perch, and its two blocks
    outside the layers."""
    forward_initial = graph_named(view_of(forward_only), "forward initial diagram")
    assert [(n.id, n.namespace) for n in forward_initial.nodes] == [
        ("forward_only:arvl:x", "arvl"),
        ("forward_only:dcsn:x_d", "dcsn"),
        ("forward_only:cntn:a", "cntn"),
        ("arvl_to_dcsn", ""),
        ("dcsn_to_cntn", ""),
    ]


@needs_viewer
def test_the_node_of_a_refused_initial_diagram_has_the_id_and_the_label_of_the_diagram():
    """The graph that states the refusal of a backward initial diagram is one
    node, whose id and label name the diagram as the documentation names
    it."""
    unbuilt = NotConstructed("no blocks", rule="not-constructed")
    refused = _refused_graph(
        _viewer(),
        INITIAL_IDS["backward"],
        _refused_label("backward", unbuilt, "initial"),
        {"refusal": str(unbuilt)},
    )
    assert [n.id for n in refused.nodes] == ["backward initial diagram:refused"]
    assert refused.nodes[0].label == "backward initial diagram refused (not-constructed)"


@pytest.mark.parametrize(
    ("direction", "refusal", "level", "label"),
    [
        pytest.param(
            "forward",
            NotConstructed("no forward builder", rule="not-constructed"),
            "builders",
            "forward builders graph refused (not-constructed)",
            id="a refusal that names its rule",
        ),
        pytest.param(
            "backward",
            NotConstructed("no backward builder"),
            "builders",
            "backward builders graph refused",
            id="a refusal that names no rule",
        ),
        pytest.param(
            "backward",
            NotConstructed("no backward builder"),
            "initial",
            "backward initial diagram refused",
            id="an initial diagram",
        ),
    ],
)
def test_the_label_of_a_refused_graph_names_the_graph_and_the_rule_of_the_refusal(
    direction, refusal, level, label
):
    """The label of the node that states the refusal of a graph names the
    graph by its direction and its level, and the rule of the refusal where
    the refusal names one."""
    assert _refused_label(direction, refusal, level) == label


@pytest.mark.parametrize(
    ("boxes", "message"),
    [
        pytest.param(
            [box_record("a:Pullback", writes=["w"]), box_record("b:Pullback", writes=["w"])],
            "w is written by both a:Pullback and b:Pullback",
            id="a wire with two writers",
        ),
        pytest.param(
            [box_record("a:Pullback", reads=["w"])],
            "w that a:Pullback reads is written by no node",
            id="a wire with no writer",
        ),
    ],
)
def test_the_writers_of_the_wires_refuse_a_wire_with_two_writers_or_with_none(boxes, message):
    """The function that finds the node writing each wire refuses a wire that
    two boxes write and a wire that a box reads and none writes, so that the
    view loses no edge without saying so."""
    with pytest.raises(ValueError, match=message):
        _writers(box_record("graph"), boxes)


# A branching decision builder


@needs_viewer
def test_each_branch_measure_of_a_branching_decision_builder_is_given_to_outputs(
    ret_choice, view_of
):
    """Each of the two measures that the forward decision builder of
    `ret_choice` writes, one for each branch, is an output port of a node and
    is given to `Outputs`."""
    forward = graph_named(view_of(ret_choice), "forward")
    nodes = {n.id: n for n in forward.nodes}
    outputs_of = {n.id: [m.id for m in n.outputsMetadata] for n in forward.nodes}
    decision_boxes = [
        box
        for box in operator_boxes(ret_choice, "forward")
        if box_identity(box).block == "dcsn_to_cntn"
    ]
    assert decision_boxes
    written = {str(ob.identity) for box in decision_boxes for ob in box.cod.inside}
    assert len(written) == 2  # one measure for each branch, work and retire
    assert written <= {port for ports in outputs_of.values() for port in ports}
    given = {edge.targetNodeInputId for edge in nodes[BOUNDARY_IDS[1]].incomingEdges}
    assert written <= given


@needs_viewer
def test_each_branch_measure_is_labeled_by_its_branch(ret_choice, view_of):
    """The output ports of the push-forward of the decision builder of
    `ret_choice` are labeled by the measure of each branch."""
    nodes = {n.id: n for n in graph_named(view_of(ret_choice), "forward").nodes}
    labels = [
        attributes(m)["__tensor_tag"] for m in nodes["dcsn_to_cntn:Pushforward"].outputsMetadata
    ]
    assert labels == ["μ_work≻", "μ_retire≻"]


# The colors of the nodes and the layers


@needs_viewer
def test_every_node_of_a_builders_graph_is_white_with_a_navy_label(sa_savings, view_of):
    """Every node of the backward builders graph of `sa_savings` is white
    with a navy label."""
    for node in graph_named(view_of(sa_savings), "backward").nodes:
        assert (node.style.backgroundColor, node.style.textColor) == (WHITE, NAVY)


@needs_viewer
def test_a_node_has_an_ultramarine_border_where_it_writes_its_builders_outputs_and_navy_elsewhere(
    sa_savings, view_of
):
    """A node that writes a wire which a node of another builder or `Outputs`
    reads has an ultramarine border, navy under the pointer, and every other
    node a navy border, ultramarine under the pointer."""
    backward = graph_named(view_of(sa_savings), "backward")
    # the builder a node stands in, the first part of its namespace
    builders = {node.id: node.namespace.split("/")[0] for node in backward.nodes}
    output_writers = {
        edge.sourceNodeId
        for node in backward.nodes
        for edge in node.incomingEdges
        if edge.sourceNodeId != BOUNDARY_IDS[0]
        and (node.id == BOUNDARY_IDS[1] or builders[node.id] != builders[edge.sourceNodeId])
    }
    # the evaluation that ends each builder; the stage has no arrival perch,
    # so no builder ends there
    assert output_writers == {"cntn_to_dcsn:Evaluation", "policy:Evaluation"}
    for node in backward.nodes:
        style = node.style
        if node.id in output_writers:
            assert (style, style.borderColor, style.hoveredBorderColor) == (
                OUTPUT_STYLE,
                ULTRAMARINE,
                NAVY,
            ), node.id
        else:
            assert (style, style.borderColor, style.hoveredBorderColor) == (
                NODE_STYLE,
                NAVY,
                ULTRAMARINE,
            ), node.id


@needs_viewer
def test_each_layer_is_laid_out_from_top_to_bottom_in_the_colors_of_its_level(sa_savings, view_of):
    """Each layer, as the viewer applies the configurations, has the second
    step of the ice for a builder and the third for a sub-builder, a navy
    border, a navy label and the layout from top to bottom."""
    backward = graph_named(view_of(sa_savings), "backward")
    configs = backward.groupNodeConfigs
    applied = {layer: applied_layer_style(configs, layer) for layer in layers_of(backward)}
    # each entry: the layout, the fill, the border and the label; the layout
    # 0 is from top to bottom, the viewer's `LayoutDirection.TOP_BOTTOM`
    assert applied == {
        "cntn_to_dcsn": (0, SECOND_ICE, NAVY, NAVY),
        "cntn_to_dcsn/ambiguity_ce": (0, THIRD_ICE, NAVY, NAVY),
        "cntn_to_dcsn/risk_ce": (0, THIRD_ICE, NAVY, NAVY),
        "policy": (0, SECOND_ICE, NAVY, NAVY),
    }


@needs_viewer
def test_a_configuration_lays_out_the_root_of_a_builders_graph(sa_savings, view_of):
    """A configuration lays out the root of the graph, which is no layer, so
    that Bellman Workbench gives the root the layout of the layers."""
    configs = graph_named(view_of(sa_savings), "backward").groupNodeConfigs
    # the empty namespace is the root; the first entry is the layout, and the
    # layout 0 is from top to bottom, the viewer's `LayoutDirection.TOP_BOTTOM`
    assert applied_layer_style(configs, "")[0] == 0


@needs_viewer
def test_the_files_of_a_bound_stage_and_of_a_trellis_use_seven_colors(
    cons_methodized_without_calibration, bound_port_cons_trellis, tmp_path
):
    """The files that `write_model_explorer` writes for a bound stage and for
    a trellis use seven colors: white, the three steps of the ice, navy,
    ultramarine and the orange of a line."""
    written = {
        value
        for view, folder in (
            (cons_methodized_without_calibration, "stage"),
            (bound_port_cons_trellis, "trellis"),
        )
        for path in write_model_explorer(view, tmp_path / folder)
        for value in color_values(path)
    }
    assert written == {WHITE, FIRST_ICE, SECOND_ICE, THIRD_ICE, NAVY, ULTRAMARINE, ORANGE_LINE}


@needs_viewer
def test_the_nodes_of_cons_with_an_ultramarine_border_are_its_evaluations_and_push_forwards(
    cons, view_of
):
    """The nodes of the view of `cons` with an ultramarine border are its
    three evaluations and its two push-forwards, each of which writes the
    outputs of its builder."""
    assert {
        (graph.id, node.id)
        for graph in view_of(cons).graphs
        for node in graph.nodes
        if node.style.borderColor == ULTRAMARINE
    } == {
        ("backward", "cntn_to_dcsn:Evaluation"),
        ("backward", "dcsn_to_arvl:Evaluation"),
        ("backward", "policy:Evaluation"),
        ("forward", "arvl_to_dcsn:Pushforward"),
        ("forward", "dcsn_to_cntn:Pushforward"),
    }


# The initial diagrams


def test_each_direction_reads_the_perches_in_its_own_order():
    """The forward direction reads the perches from the arrival to the
    continuation, and the backward direction in the reverse order."""
    assert PERCH_ORDER == {
        "forward": ("arvl", "dcsn", "cntn"),
        "backward": ("cntn", "dcsn", "arvl"),
    }


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), INITIAL_ROWS)
def test_the_nodes_of_an_initial_diagram_are_its_fields_by_perch_and_then_its_blocks(
    name, direction, request, initial_diagram
):
    """The nodes of an initial diagram are one for each field that it takes
    or that a block writes, in the order in which the direction reads their
    perches with the shocks last, then one for each block, and no `Inputs`
    or `Outputs` node."""
    diagram = initial_diagram(request.getfixturevalue(name), direction)
    # a field that no block writes is one the diagram takes, and a field that
    # no block reads is one it gives
    assert not {n.id for n in diagram.graph.nodes} & set(BOUNDARY_IDS)
    # the wires inside the blocks' bubbles, which `drawn_sorts` reads as
    # well, give no node
    taken = [str(ob.identity) for ob in diagram.hypergraph.dom.inside]
    assert (
        {n.id for n in diagram.fields} == set(taken) | set(diagram.written) <= set(diagram.sorts)
    )
    assert [n.id for n in diagram.block_nodes] == [b.name for b in diagram.blocks]
    assert [n.id for n in diagram.graph.nodes] == [
        n.id for n in diagram.fields + diagram.block_nodes
    ]
    perches = [n.namespace for n in diagram.fields]
    order = [p for p in PERCH_ORDER[direction] if p in perches] + [""]
    assert perches == sorted(perches, key=order.index)


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), INITIAL_ROWS)
def test_the_layers_of_an_initial_diagram_are_its_perches_with_fields_empty_and_left_to_right(
    name, direction, request, initial_diagram
):
    """The layers of an initial diagram are the perches that hold a field, in
    the order in which the direction reads them, each with no row, on the
    first step of the ice and laid out from left to right."""
    from model_explorer import graph_builder

    diagram = initial_diagram(request.getfixturevalue(name), direction)
    perches = [n.namespace for n in diagram.fields]
    order = [p for p in PERCH_ORDER[direction] if p in perches] + [""]
    assert list(diagram.graph.groupNodeAttributes) == [p for p in order if p]
    assert all(shown == {} for shown in diagram.graph.groupNodeAttributes.values())
    assert diagram.graph.groupNodeConfigs == [
        _layer_config(".*", graph_builder.LayoutDirection.LEFT_RIGHT, LAYER_COLORS["stage"])
    ]


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), INITIAL_ROWS)
def test_a_field_is_a_node_in_the_layer_of_its_perch_labeled_as_drawn_with_its_fields_table_rows(
    name, direction, request, initial_diagram
):
    """Each field of an initial diagram is a node in the layer of its perch,
    or outside the layers for a shock, labeled as the drawing labels its
    wire, whose rows are facts of the fields table."""
    diagram = initial_diagram(request.getfixturevalue(name), direction)
    for node in diagram.fields:
        sort = diagram.sorts[node.id]
        perch = sort.identity.perch
        assert node.namespace == (perch if perch in ("arvl", "dcsn", "cntn") else "")
        assert node.label == wire_label(sort, diagram.names.get(sort.identity))
        shown = attributes(node)
        assert shown["kind"] == "field"
        assert shown.get("role") == (sort.role or None)
        assert shown.get("set") == (None if sort.domain is None else to_source(sort.domain))
        if node.namespace:
            assert shown["perch"] == perch and "edge" not in shown
        else:
            assert "perch" not in shown and shown["edge"]
        assert re.fullmatch(r"\S+\.bl \d+", shown["lines"]), node.id


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), INITIAL_ROWS)
def test_a_field_has_an_edge_from_the_block_that_writes_it_and_a_port_where_a_block_reads_it(
    name, direction, request, initial_diagram
):
    """The node of a field has an edge from the block that writes it, and
    none where the diagram takes it, and an output port where a block reads
    it."""
    diagram = initial_diagram(request.getfixturevalue(name), direction)
    for node in diagram.fields:
        if node.id in diagram.written:
            assert [
                (e.sourceNodeId, e.sourceNodeOutputId, e.targetNodeInputId)
                for e in node.incomingEdges
            ] == [(diagram.written[node.id],) + (node.id,) * 2]
            assert [m.id for m in node.inputsMetadata] == [node.id]
        else:
            assert node.incomingEdges == [] and node.inputsMetadata == []
        assert [m.id for m in node.outputsMetadata] == (
            [node.id] if node.id in diagram.read else []
        )


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), INITIAL_ROWS)
def test_the_ports_of_a_field_show_only_its_label_perch_role_and_set(
    name, direction, request, initial_diagram
):
    """The ports of the node of a field show no row but its label, its
    perch, its role and its set, so no row `field` and no row `type`."""
    diagram = initial_diagram(request.getfixturevalue(name), direction)
    for node in diagram.fields:
        for port in node.inputsMetadata + node.outputsMetadata:
            assert set(attributes(port)) <= {"__tensor_tag", "label", "perch", "role", "set"}


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), INITIAL_ROWS)
def test_every_node_of_an_initial_diagram_is_white_with_a_navy_border(
    name, direction, request, initial_diagram
):
    """Every node of an initial diagram, a field's or a block's, is white
    with a navy border."""
    diagram = initial_diagram(request.getfixturevalue(name), direction)
    for node in diagram.fields:
        assert node.style == NODE_STYLE
        assert node.style.backgroundColor == PALETTE["--bf-face"]
    for node in diagram.block_nodes:
        assert node.style == NODE_STYLE


@needs_viewer
@pytest.mark.parametrize(("name", "direction"), INITIAL_ROWS)
def test_a_block_is_a_node_outside_the_layers_named_by_it_with_the_ports_and_edges_of_its_header(
    name, direction, request, initial_diagram
):
    """Each block of an initial diagram is a node outside the layers,
    labeled by its name, whose ports are the fields that its header reads
    and writes, a control among none of them, with an edge from the node of
    each field that it reads."""
    diagram = initial_diagram(request.getfixturevalue(name), direction)
    nodes = {n.id: n for n in diagram.graph.nodes}
    for box in diagram.blocks:
        node = nodes[box.name]
        assert (node.label, node.namespace) == (box.name, "")
        reads = [str(ob.identity) for ob in box.dom.inside]
        writes = [str(ob.identity) for ob in box.cod.inside]
        assert [m.id for m in node.inputsMetadata] == reads
        assert [m.id for m in node.outputsMetadata] == writes
        assert [
            (e.sourceNodeId, e.sourceNodeOutputId, e.targetNodeInputId) for e in node.incomingEdges
        ] == [(w, w, w) for w in reads]


@needs_viewer
@pytest.mark.parametrize(
    ("name", "direction"), direction_rows("cons_methodized_without_calibration")
)
def test_no_block_of_an_initial_diagram_shows_a_method(name, direction, request, initial_diagram):
    """No block of an initial diagram of a methodized version shows a method
    or a handler, although methods are bound at its builders."""
    diagram = initial_diagram(request.getfixturevalue(name), direction)
    nodes = {n.id: n for n in diagram.graph.nodes}
    for box in diagram.blocks:
        assert not {"method", "handler"} & set(attributes(nodes[box.name]))


@needs_viewer
def test_a_shock_is_a_node_outside_the_layers_that_names_the_perches_it_is_drawn_between(
    sa_savings, initial_diagram
):
    """The shock Ψ of `sa_savings`, which belongs to no perch, is a node
    outside the layers whose row `edge` is the pair of perches that the
    fields table draws it between, from the decision to the continuation."""
    forward = initial_diagram(sa_savings, "forward").graph
    shock = {n.id: n for n in forward.nodes}["sa_savings:shck:Ψ"]
    assert (shock.namespace, shock.label) == ("", "Ψ")
    assert attributes(shock) == {
        "kind": "field",
        "edge": "∼→≻",
        "role": "shock",
        "set": "ℝ₊₊",
        "lines": "sa_savings.bl 18",
    }
    assert sa_savings.fields().edges["sa_savings:shck:Ψ"] == ("dcsn", "cntn")


@needs_viewer
def test_the_block_that_reads_a_shock_has_an_edge_from_the_node_of_the_shock(
    sa_savings, initial_diagram
):
    """The forward decision block of `sa_savings`, the last node of its
    forward initial diagram, has an edge from the decision state m_d and one
    from the shock Ψ."""
    forward = initial_diagram(sa_savings, "forward").graph
    assert [e.sourceNodeId for e in forward.nodes[-1].incomingEdges] == [
        "sa_savings:dcsn:m_d",
        "sa_savings:shck:Ψ",
    ]


# The perch overlays


@needs_viewer
def test_the_three_perch_overlays_are_named_and_colored_by_their_perches(cons_overlays):
    """The perch overlays are the arrival, the decision and the continuation,
    in navy, the orange of a line and ultramarine, the colors of the three
    perches in the stylesheet."""
    assert [o.name for o in cons_overlays] == ["arrival", "decision", "continuation"]
    assert [o.edgeColor for o in cons_overlays] == [NAVY, ORANGE_LINE, ULTRAMARINE]


@needs_viewer
def test_a_perch_overlay_holds_every_edge_whose_wire_stands_at_its_perch(
    cons, cons_overlays, view_of
):
    """Each perch overlay holds every edge of the four graphs of the view
    whose wire stands at its perch, in the order of the nodes and of their
    ports."""
    expected = {"arvl": [], "dcsn": [], "cntn": []}
    for graph in view_of(cons).graphs:
        for node in graph.nodes:
            ports = {m.id: attributes(m) for m in node.inputsMetadata}
            for edge in node.incomingEdges:
                perch = ports[edge.targetNodeInputId].get("perch", "")
                if perch in expected:
                    expected[perch].append((edge.sourceNodeId, node.id))
    assert all(expected.values())  # cons has wires at all three perches
    for overlay, perch in zip(cons_overlays, expected):
        assert [(e.sourceNodeId, e.targetNodeId) for e in overlay.edges] == expected[perch]


@needs_viewer
def test_an_edge_of_a_perch_overlay_has_no_label(cons_overlays):
    """No edge of a perch overlay has a label, since the viewer draws an
    overlay edge as a straight line between two nodes."""
    # each overlay holds edges
    assert all(overlay.edges for overlay in cons_overlays)
    assert all(e.label is None for overlay in cons_overlays for e in overlay.edges)


@needs_viewer
def test_no_graph_of_the_view_carries_the_perch_overlays(cons, view_of):
    """No graph of the view carries the perch overlays, which
    `write_model_explorer` writes to a file of their own."""
    assert all(graph.tasksData is None for graph in view_of(cons).graphs)


# The switch of the shorter labels of the ports


@needs_viewer
def test_by_default_the_port_of_a_result_is_labeled_by_the_expression_it_denotes(
    cons_methodized_without_calibration, view_of
):
    """With the switch `SHORT_LABELS` off, as it is by default, the port of
    a result is labeled by the expression that it denotes, as the drawing
    prints it."""
    assert SHORT_LABELS is False
    labels = output_labels(graph_named(view_of(cons_methodized_without_calibration), "backward"))
    assert labels["cntn_to_dcsn:Aggregation:V:result"] == "m_d ↦ 𝑢(𝑐(m_d)) + 𝑉≻(𝑔(m_d, 𝑐(m_d)))"


@needs_viewer
def test_the_switch_of_the_shorter_labels_changes_no_label_of_a_node(
    cons_methodized_without_calibration, backward_graph_with_short_labels, view_of
):
    """With the switch `SHORT_LABELS` on, every node keeps its label."""
    # the view of `view_of` is made with the switch off, its default
    assert SHORT_LABELS is False
    nodes = {
        n.id: n.label
        for n in graph_named(view_of(cons_methodized_without_calibration), "backward").nodes
    }
    assert {n.id: n.label for n in backward_graph_with_short_labels.nodes} == nodes


@needs_viewer
@pytest.mark.parametrize(
    ("port", "label"),
    [
        pytest.param("cntn_to_dcsn:Aggregation:V:result", "𝑉(m_d)", id="the decision value"),
        pytest.param("dcsn_to_arvl:Aggregation:V:result", "𝑉(m, l)", id="the arrival value"),
        pytest.param("policy:Evaluation:c:result", "𝑐(m_d)", id="the policy"),
    ],
)
def test_with_the_shorter_labels_a_result_is_labeled_by_its_function_at_its_coordinates(
    port, label, backward_graph_with_short_labels
):
    """With the switch `SHORT_LABELS` on, the port of a result that is a
    function is labeled by that function at its coordinates."""
    assert output_labels(backward_graph_with_short_labels)[port] == label


@needs_viewer
def test_with_the_shorter_labels_a_set_of_candidate_policies_keeps_its_expression(
    backward_graph_with_short_labels,
):
    """With the switch `SHORT_LABELS` on, the port of a result that is a set
    of candidate policies keeps its expression."""
    labels = output_labels(backward_graph_with_short_labels)
    assert labels["policy.identification:Pullback:c:result"].startswith("{f ∈ {c ∈ (Xm → ℝ₊₊)")


@needs_viewer
def test_with_the_shorter_labels_a_pulled_back_wire_keeps_its_name(
    backward_graph_with_short_labels,
):
    """With the switch `SHORT_LABELS` on, the port of a pulled-back wire,
    which is no result, keeps its name."""
    assert (
        output_labels(backward_graph_with_short_labels)["cons:function:cntn:V:g"]
        == "𝑉≻(𝑔(m_d, 𝑐(m_d)))"
    )


# The functions that read a view back


@needs_viewer
@pytest.mark.parametrize(
    ("direction", "layers"),
    [
        pytest.param("backward", ("cntn_to_dcsn", "dcsn_to_arvl", "policy"), id="backward"),
        pytest.param("forward", ("arvl_to_dcsn", "dcsn_to_cntn"), id="forward"),
    ],
)
def test_layers_to_open_names_the_builders_of_a_stage_at_depth_one(
    direction, layers, cons, view_of
):
    """At depth one, `layers_to_open` names the builders of a builders graph
    of a stage, the first parts of the namespaces of its nodes."""
    # the arguments: the view, the graph and the depth
    assert layers_to_open(view_of(cons), direction, 1) == layers


@needs_viewer
def test_layers_to_open_reads_a_written_graph_file_as_it_reads_the_view(cons, view_of, tmp_path):
    """`layers_to_open` names the same layers from the document of the graph
    file that `write_model_explorer` writes as from the view."""
    graph_path, _ = write_model_explorer(cons, tmp_path)
    document = json.loads(graph_path.read_text(encoding="utf-8"))
    assert layers_to_open(document, "backward", 1) == layers_to_open(view_of(cons), "backward", 1)


@needs_viewer
def test_layers_to_open_refuses_a_graph_that_the_view_does_not_hold(cons, view_of):
    """`layers_to_open` refuses the name of a graph that the view does not
    hold."""
    with pytest.raises(ValueError, match="none named 'sideways'"):
        layers_to_open(view_of(cons), "sideways", 1)


@needs_viewer
def test_layers_to_open_names_each_stage_of_each_period_of_a_trellis_at_depth_two(cons, port):
    """At depth two, `layers_to_open` names each stage of each period of a
    trellis of two periods, the later period first."""
    collection = to_model_explorer(two_period_lesson_trellis(cons, port))
    assert layers_to_open(collection, "backward", 2) == tuple(
        f"periods[{h}]/{key}" for h in (1, 0) for key in ("port", "cons", "disc")
    )


@needs_viewer
def test_wire_counts_counts_the_distinct_wires_of_each_builders_graph(
    cons_methodized_without_calibration, view_of
):
    """`wire_counts` counts the distinct wires of each builders graph, which
    are fewer than its edges, since a wire that two boxes read is two
    edges."""
    collection = view_of(cons_methodized_without_calibration)
    expected = distinct_wires(collection)
    assert wire_counts(collection) == expected
    backward = graph_named(collection, "backward")
    assert sum(len(node.incomingEdges) for node in backward.nodes) > expected["backward"]


@needs_viewer
def test_wire_counts_reads_the_dictionary_of_a_view_as_it_reads_the_view(
    cons_methodized_without_calibration, view_of
):
    """`wire_counts` gives the same counts from a view written as a
    dictionary, as its file holds it, as from the view."""
    collection = view_of(cons_methodized_without_calibration)
    assert wire_counts(dataclasses.asdict(collection)) == distinct_wires(collection)


@needs_viewer
def test_wire_counts_counts_no_wire_of_a_refused_builders_graph(retiree_death, view_of):
    """`wire_counts` counts no wire of the forward builders graph of
    `retiree_death`, which the construction refuses."""
    with pytest.raises(NotConstructed):
        graph_of(retiree_death, "builders", "forward")
    assert wire_counts(view_of(retiree_death))["forward"] == 0


# The labels of the evaluations in the drawings


@pytest.mark.parametrize(
    ("name", "label"),
    [
        pytest.param("cntn_to_dcsn:Evaluation", "𝑉(m_d)", id="the decision value"),
        pytest.param("dcsn_to_arvl:Evaluation", "𝑉≺(m)", id="the arrival value"),
        pytest.param("policy:Evaluation", "𝑐(m_d)", id="the policy"),
    ],
)
def test_the_drawing_labels_an_evaluation_by_its_output(name, label, cons_drawing):
    """The drawing of the backward builders graph of `cons` labels each
    evaluation by its output at the states that the output depends on."""
    # the DOT statement of a box writes its label and then its tooltip,
    # which names the box before an em dash
    assert f'[label="{label}" tooltip="{name} — ' in cons_drawing, name


def test_the_drawing_of_cons_holds_no_label_with_the_words_at_the_output(cons_drawing):
    """The drawing of the backward builders graph of `cons` holds no label
    with the words `at the output`."""
    assert "at the output" not in cons_drawing


@pytest.mark.parametrize(
    ("name", "lines", "outputs"),
    [
        pytest.param(
            "cntn_to_dcsn:Evaluation",
            ("𝑉(m_d),", "𝑊(m_d)", "and 1 more"),
            "𝑉, 𝑊, 𝑍",
            id="the decision values",
        ),
        pytest.param(
            "dcsn_to_arvl:Evaluation",
            ("𝑉≺(m),", "𝑊≺(m)", "and 1 more"),
            "𝑉≺, 𝑊≺, 𝑍≺",
            id="the arrival values",
        ),
    ],
)
def test_an_evaluation_with_three_outputs_is_drawn_as_two_and_a_count_with_a_tooltip_naming_each(
    name, lines, outputs, three_value_outputs
):
    """An evaluation with three outputs, longer than one line of its box, is
    drawn as its first two outputs and the count of the third on three
    lines, which DOT separates by `\\n`, with a tooltip that names every
    output."""
    # each line that `with_three_values` replaces stands once in `cons.bl`
    text = corpus_text("cons")
    assert [line for line in REPLACED_LINES if text.count(line) != 1] == []
    source = three_value_outputs.builder.bwd.diagram().source
    label = "\\n".join(lines)
    assert f'[label="{label}" tooltip="{name} — Evaluation of {outputs}"' in source, name


# three_value_outputs: evaluations of three outputs, whose third is counted
@pytest.mark.parametrize(
    "name",
    [
        *stage_rows(*(name for name in CORPUS if name != "tenure"), "three_value_outputs"),
        pytest.param(
            "tenure",
            marks=pytest.mark.xfail(
                strict=True,
                reason="The test expects the symbol of each evaluation of `tenure` to be the "
                "labels of its output ports, which write the age as 𝑎𝑔𝑒(). Today the drawing "
                "names the value of a constant, which has no coordinates, by the identity of "
                "its wire, `tenure:function:dcsn:age`.",
            ),
            id="tenure",
        ),
    ],
)
def test_the_symbol_of_an_evaluation_is_the_labels_of_its_output_ports(name, request):
    """The symbol of each evaluation of a backward builders graph at the
    primitive grain, the grain of the view, is the labels that the view
    gives its output ports, the first two joined by a comma and the others
    counted."""
    # each line that `with_three_values` replaces stands once in `cons.bl`
    text = corpus_text("cons")
    assert [line for line in REPLACED_LINES if text.count(line) != 1] == []
    stage = request.getfixturevalue(name)
    graph = stage.builder.bwd.primitives.graph
    sources = label_sources(stage, graph)
    evaluations = [
        box for box in graph.boxes if not is_wiring(box) and box_identity(box).kind == "Evaluation"
    ]
    assert evaluations  # the graph holds an evaluation
    for box in evaluations:
        ports = [port_label(sources, ob.identity) for ob in box.cod.inside]
        named = ", ".join(ports[:2])
        if len(ports) > 2:
            named += f" and {len(ports) - 2} more"
        assert box_symbol(box, sources.value_aggregations) == named, (name, box.name)


@pytest.mark.parametrize("grain", ["builder", "sub-builder", "primitive"])
def test_a_long_label_of_an_evaluation_is_not_cut_in_a_drawing(grain, long_value_outputs):
    """The label of an evaluation that is longer than two lines of its box is
    not cut with `…` in the drawing of a backward builders graph at the
    builder, the sub-builder or the primitive grain."""
    # each line that `with_three_values` replaces stands once in `cons.bl`
    text = corpus_text("cons")
    assert [line for line in REPLACED_LINES if text.count(line) != 1] == []
    builders = long_value_outputs.builder.bwd
    grains = {
        "builder": builders,
        "sub-builder": builders.sub_builders,
        "primitive": builders.primitives,
    }
    lines = [
        line for line in grains[grain].diagram().source.splitlines() if " — Evaluation of " in line
    ]
    assert lines  # the drawing holds an evaluation
    for line in lines:
        assert "…" not in line.split(' tooltip="')[0], line
