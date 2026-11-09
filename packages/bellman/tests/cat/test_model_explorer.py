"""The semgraph exported to Model Explorer's graph: the two builders graphs as
nested layers, every wire an edge carrying its label, perch, type and role,
the identity strings as ids, and each layer's signature among its attributes;
a primitive's card text and its bound method in the side panel, and an
output's label, perch, type and role as its input shows them; the three
perch overlays, unlabeled and carried in no graph; the two JSON files of a
view, and the viewer's server reached on one port (`serve`); and the view
of a trellis, a layer for each period and each stage
occurrence, the joins as edges between the occurrences' wires, and the
backward graph refused where an occurrence refuses it (the
brief semgraph-model-explorer.md §3, §6, §8 items 1 to 4 and 6). The tests
named by a line of the proposal state that line of §6 of the study of the
minimal view of 30 September 2026, model-explorer-minimal-view.md."""

import contextlib
import dataclasses
import http.server
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from importlib import metadata
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote, unquote

import pytest
from conftest import ROOT, branching_stage, corpus_text

from bellman.stage import elaborate_stage, load_stage
from bellman.stage.stage_answers import entry_perch
from bellman.trellis import accrete, connection_report, elaborate_trellis, load_recipe
from bellman.display.cards import WORDS, SourceLine, card_sections, source_lines
from bellman.display.drawing import box_symbol, drawn_sorts, wire_label
from bellman.factory import model_explorer as me
from bellman.native.identity import box_identity
from bellman.native.labels import is_wiring, value_aggregations_of
from bellman.refusals import FactoryError, NotConstructed
from bellman.stage.grains import DIRECTIONS, graph_of, wire_table
from bellman.stage.kernels import kernel
from bellman.stage.pieces import drawing_arguments
from bellman.typing import typed_expressions as S

# The tests that read the viewer's classes are skipped where the extra
# `explore` is not installed; the others run in either case.
needs_viewer = pytest.mark.skipif(
    importlib.util.find_spec("model_explorer") is None,
    reason="the extra `explore` is not installed",
)

# a stage with two forward blocks and no backward block, whose backward
# builders graph the construction refuses (tests/cat/test_builder_pairs.py)
BACKWARD_REFUSED = """@stage: forward_only
[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=dcsn_to_cntn, (x_d) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d
}
"""


def operator_boxes(stage, direction):
    """The primitive operators of one builders graph, which the primitive
    grain holds with no bubble around them."""
    graph = graph_of(stage, "builders", direction, grain="primitive")
    return [box for box in graph.boxes if not is_wiring(box)]


def attributes(item):
    """The attributes of a node or of a port, by key."""
    return {pair.key: pair.value for pair in item.attrs}


# the four graphs of a stage view, in the order the collection lists them:
# the two initial diagrams, then the two builders graphs
STAGE_GRAPHS = ["backward initial diagram", "forward initial diagram", "backward", "forward"]


def graph_named(collection, graph_id):
    """The graph of a collection by its id."""
    return next(graph for graph in collection.graphs if graph.id == graph_id)


def builders_graphs(collection):
    """The two builders graphs of a collection, `backward` and `forward`."""
    return [graph_named(collection, direction) for direction in DIRECTIONS]


def reached(stage, direction, namespace, identity):
    """The identity of the box the stage's handles reach by the segments of
    a namespace, a builder and then a sub-builder, and then by the key of
    the box within the last of them."""
    handle = stage.builder.bwd if direction == "backward" else stage.builder.fwd
    for segment in namespace.split("/"):
        handle = handle[segment]
    return box_identity(handle[identity.key_within(handle.box.name)].box)


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


def spaced(text):
    """A text with every run of spaces written as one space, so that two
    texts are compared apart from the columns a card aligns them in."""
    return " ".join(text.split())


def printed_rules(card):
    """The rules of a printed card's `Rule` section as a reader reads them:
    each row on one line, a row that holds only the region a rule holds on,
    `on (m_f, m_h) ∈ …`, joined to the row before it, and every run of
    spaces written as one space (`spaced`)."""
    rules = []
    for heading, held in printed_sections(card):
        if heading != "Rule":
            continue
        for row in held:
            text = spaced(one_line(row))
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


def expanded(lines):
    """The file and the line numbers an attribute `lines` names,
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


def boxes_before(stage, direction, box):
    """The primitive boxes of the builders graph of `direction` that write a
    wire `box` reads."""
    read = {ob.identity for ob in box.dom.inside}
    return [
        other
        for other in operator_boxes(stage, direction)
        if read & {ob.identity for ob in other.cod.inside}
    ]


def numbered(attrs, word):
    """The values of the attributes of one section or of a kernel, in order:
    the attribute `word` alone where there is one value, and `word 1`,
    `word 2`, … where there are several, whose numbers run from one with no
    gap; never both, and never one numbered value."""
    keys = [key for key in attrs if re.fullmatch(rf"{word} \d+", key)]
    if word in attrs:
        assert not keys, keys
        return [attrs[word]]
    assert keys == [f"{word} {n}" for n in range(1, len(keys) + 1)], keys
    assert len(keys) != 1, keys  # one value is not numbered
    return [attrs[key] for key in keys]


def box_named(stage, direction, name):
    """The primitive box of one builders graph that has this whole name."""
    return next(box for box in operator_boxes(stage, direction) if box.name == name)


def in_viewer_classes(collection):
    """A view as the viewer's own Python classes hold it: its JSON form read
    back by dacite, which leaves out the fields the viewer's page reads and
    those classes do not declare, the color of a node's label and the colors
    of a layer (`me._NodeStyle`, `me._LayerConfig`)."""
    import dacite
    from model_explorer import graph_builder as gb

    return dacite.from_dict(gb.GraphCollection, dataclasses.asdict(collection))


def as_json(collection):
    """A view's collection as its file holds it, read back as JSON."""
    return json.loads(json.dumps(dataclasses.asdict(collection)))


def colors_in(document):
    """Every color a JSON document holds, as `(key, value)`: the value of
    each key that names a color, `backgroundColor`, `edgeColor` and the
    like, where it is set."""
    if isinstance(document, dict):
        for key, value in document.items():
            if key.endswith("Color"):
                if value is not None:
                    yield key, value
            else:
                yield from colors_in(value)
    elif isinstance(document, list):
        for item in document:
            yield from colors_in(item)


def contrast(first, second):
    """The contrast ratio of two colors written `#RRGGBB`, as WCAG 2.2
    defines it: the lighter relative luminance plus 0.05 over the darker
    plus 0.05."""

    def luminance(color):
        channels = [int(color[at : at + 2], 16) / 255 for at in (1, 3, 5)]
        red, green, blue = (
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        )
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def layers_of(graph):
    """The namespaces of the layers the viewer draws for a graph: every
    leading part of a node's namespace, `periods[2]`, `periods[2]/cons` and
    `periods[2]/cons/policy` for a node in `periods[2]/cons/policy`."""
    return {
        "/".join(parts[:count])
        for parts in (node.namespace.split("/") for node in graph.nodes if node.namespace)
        for count in range(1, len(parts) + 1)
    }


def as_the_viewer_applies(configs, namespace):
    """The layout and the fill, border and label colors the viewer's page
    gives the layer `namespace` from a graph's layer configurations
    `configs`: the layout of the first configuration whose pattern it finds
    in the namespace (`RegExp.test`), and each color from the first such
    configuration that sets that color; None for what none gives."""
    found = [config for config in configs if re.search(config.namespaceRegex, namespace)]
    applied = [found[0].layoutDirection if found else None]
    for color in ("backgroundColor", "borderColor", "textColor"):
        given = [getattr(config, color) for config in found if getattr(config, color) is not None]
        applied.append(given[0] if given else None)
    return tuple(applied)


@pytest.fixture(scope="module")
def port_cons_view(port_cons):
    """The view of the lesson's trellis with its initial diagrams (design
    pass 14 §7), built once for the module."""
    return me.to_model_explorer(port_cons, initial=True)


def occurrence_of(node_id):
    """The period and the key of the stage occurrence a node of a trellis
    view stands in, `("periods[1]", "disc")`, read from the prefix of its
    id; None for a boundary node, `start:periods[5]/port/…`, which stands
    at the graph's root."""
    parts = node_id.split("/")
    return tuple(parts[:2]) if parts[0].startswith("periods[") else None


def boundary_ports(graph, kind):
    """The ids of the ports of the boundary nodes of kind `kind` of a graph
    of a trellis view (design pass 10 §6), in the order of the nodes: the
    wires that enter or leave the graph there."""
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


@needs_viewer
def test_item_1_two_graphs_one_node_per_primitive_in_its_builders_namespace(cons, sa_savings):
    from model_explorer import graph_builder as gb

    collection = me.to_model_explorer(cons)
    assert isinstance(collection, gb.GraphCollection) and collection.label == "cons"
    assert [graph.id for graph in collection.graphs] == STAGE_GRAPHS
    for stage in (cons, sa_savings):
        for graph in builders_graphs(me.to_model_explorer(stage)):
            boxes = operator_boxes(stage, graph.id)
            op_nodes = {node.id: node for node in graph.nodes if node.id not in me.BOUNDARY_IDS}
            assert set(op_nodes) == {str(box_identity(box)) for box in boxes}
            for box in boxes:
                # the namespace names the builder and the sub-builder that
                # hold the box: the handles reach the box by its segments
                identity = box_identity(box)
                namespace = op_nodes[str(identity)].namespace
                assert reached(stage, graph.id, namespace, identity) == identity
    namespaces = {n.id: n.namespace for n in graph_named(collection, "backward").nodes}
    # `InvEuler` is a statement of the policy builder of cons.bl, and no
    # sub-builder, so its aggregation stands directly in the builder
    assert namespaces["policy.InvEuler:Aggregation"] == "policy"
    backward = graph_named(me.to_model_explorer(sa_savings), "backward")
    namespaces = {n.id: n.namespace for n in backward.nodes}
    # `risk_ce` is an authored `!node`, a sub-builder of `cntn_to_dcsn`;
    # `objective` is a statement of the policy builder
    assert namespaces["cntn_to_dcsn.risk_ce:Pullback"] == "cntn_to_dcsn/risk_ce"
    assert namespaces["policy.objective:Argmax"] == "policy"


@needs_viewer
def test_a_layer_is_crossed_by_the_wires_its_primitives_read_and_shows_its_signature(
    cons, sa_savings
):
    graph = graph_named(me.to_model_explorer(cons), "backward")
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
    # the policy builder takes 𝑉≻, which its primitives read
    assert crossing_in == {"cons:function:cntn:V"}
    assert crossing_out == {"policy:Evaluation:c:result"}
    # the builder's signature, as it prints, stands in the layer's attributes,
    # before what the builder's primitives share
    signature = cons.builder.bwd["policy"].signature()
    shown = graph.groupNodeAttributes["policy"]
    assert list(shown) == ["inputs", "outputs", "feasible set", "parameter"]
    assert {side: shown[side] for side in ("inputs", "outputs")} == {
        "inputs": printed_side(signature, "in"),
        "outputs": printed_side(signature, "out"),
    }
    assert shown["inputs"] == "𝑉≻ : Xa → [−∞, ∞)"
    assert set(graph.groupNodeAttributes) == {"cntn_to_dcsn", "dcsn_to_arvl", "policy"}
    # the graph's own signature, the wires as one object, on its two nodes
    # `Inputs` and `Outputs`, whose ports give the wires one by one
    nodes = {n.id: n for n in graph.nodes}
    whole = cons.builder.bwd.signature()
    assert attributes(nodes["GraphInputs"]) == {"inputs": printed_side(whole, "in")}
    assert attributes(nodes["GraphOutputs"]) == {"outputs": printed_side(whole, "out")}
    assert attributes(nodes["GraphInputs"]) == {"inputs": "𝑉≻ : Xa → [−∞, ∞)"}
    # a sub-builder's layer shows the sub-builder's signature
    shown = graph_named(me.to_model_explorer(sa_savings), "backward").groupNodeAttributes
    risk = sa_savings.builder.bwd["cntn_to_dcsn"]["risk_ce"].signature()
    assert shown["cntn_to_dcsn/risk_ce"]["outputs"] == printed_side(risk, "out")


@needs_viewer
def test_item_1_every_wire_is_an_edge_with_its_label_perch_type_and_role(cons):
    graph = graph_named(me.to_model_explorer(cons), "backward")
    nodes = {n.id: n for n in graph.nodes}
    hypergraph = graph_of(cons, "builders", "backward", grain="primitive")
    identities = {str(identity): identity for identity in drawn_sorts(hypergraph)}
    wires = wire_table(cons)
    edges = [(n.id, e) for n in graph.nodes for e in n.incomingEdges]
    # one edge for each wire a box reads and each wire the graph gives
    reads = sum(len(box.dom.inside) for box in operator_boxes(cons, "backward"))
    assert len(edges) == reads + len(hypergraph.cod.inside)
    for target_id, edge in edges:
        assert edge.sourceNodeId in nodes
        assert edge.sourceNodeOutputId == edge.targetNodeInputId  # one wire, one port id
        source_meta = {m.id: m for m in nodes[edge.sourceNodeId].outputsMetadata}
        target_meta = {m.id: m for m in nodes[target_id].inputsMetadata}
        assert edge.sourceNodeOutputId in source_meta and edge.targetNodeInputId in target_meta
        for item in (source_meta[edge.sourceNodeOutputId], target_meta[edge.targetNodeInputId]):
            attrs = attributes(item)
            assert "__tensor_tag" in attrs and attrs["__tensor_tag"]
            assert "type" in attrs
            # a wire at a perch names it, and a wire at none, the result of
            # an operation, writes no empty row
            identity = identities[item.id]
            assert attrs.get("perch") == identity.perch
            assert attrs.get("perch", "arvl") in ("arvl", "dcsn", "cntn")
            # the role the wire table gives the wire; the endogenous grid
            # `m_d[>]` carries the role of its field, a state
            assert attrs.get("role") == (wires.sort_of(identity).role or None)
    # the type of a port is the type the builder's signature prints
    ports = {m.id: attributes(m) for n in graph.nodes for m in n.inputsMetadata}
    for key in ("cntn_to_dcsn", "dcsn_to_arvl", "policy"):
        signature = cons.builder.bwd[key].signature()
        for wire in signature.inputs + signature.outputs:
            assert ports[str(wire.identity)]["type"] == wire.type, wire.identity
    # the wire the pullback writes is read by one box, the aggregation
    readers = [(t, e) for t, e in edges if e.sourceNodeId == "cntn_to_dcsn:Pullback"]
    assert [t for t, _ in readers] == ["cntn_to_dcsn:Aggregation"]
    # a wire two boxes read, `𝑐≻`: one edge to each, from the one output item
    # its writer holds for it
    readers = [(t, e) for t, e in edges if e.sourceNodeOutputId == "cons:function:cntn:c"]
    assert sorted(t for t, _ in readers) == [
        "policy.cons_choice:Pullback",
        "policy.endoggrid:Aggregation",
    ]
    assert {e.sourceNodeId for _, e in readers} == {"policy.InvEuler:Aggregation"}
    written = [m.id for m in nodes["policy.InvEuler:Aggregation"].outputsMetadata]
    assert written.count("cons:function:cntn:c") == 1


@needs_viewer
def test_an_output_shows_the_wires_label_perch_type_and_role_as_its_input_does(cons):
    # the side panel names an output that one node reads by that node's
    # label and lists no key of an output that begins with two underscores,
    # so each port holds the wire's label under `label` as well as under
    # `__tensor_tag`, the key that names an input
    graph = graph_named(me.to_model_explorer(cons), "backward")
    nodes = {n.id: n for n in graph.nodes}
    fields = ("label", "perch", "type", "role")
    compared = 0
    for node in graph.nodes:
        inputs = {m.id: attributes(m) for m in node.inputsMetadata}
        for edge in node.incomingEdges:
            outputs = {m.id: attributes(m) for m in nodes[edge.sourceNodeId].outputsMetadata}
            output, input_ = outputs[edge.sourceNodeOutputId], inputs[edge.targetNodeInputId]
            assert [output.get(f) for f in fields] == [input_.get(f) for f in fields], edge
            assert output["label"] == input_["__tensor_tag"], edge
            compared += 1
    assert compared == sum(len(n.incomingEdges) for n in graph.nodes) > 0
    # the one output of `Inputs`, which one node reads
    shown = [attributes(m) for m in nodes["GraphInputs"].outputsMetadata]
    assert [tuple(s[f] for f in fields) for s in shown] == [
        ("𝑉≻(a)", "cntn", "Xa → [−∞, ∞)", "value"),
    ]


@needs_viewer
def test_item_1_a_node_shows_the_symbol_with_the_cards_law_and_its_ports_as_drawn(
    cons,
):
    nodes = {n.id: n for n in graph_named(me.to_model_explorer(cons), "backward").nodes}
    hypergraph = graph_of(cons, "builders", "backward", grain="primitive")
    # the names the drawing is given, from the one function that gives
    # them, and the sorts and value aggregations it reads itself
    names = drawing_arguments(cons, hypergraph)["wire_names"]
    sorts, aggregations = drawn_sorts(hypergraph), value_aggregations_of(hypergraph)
    for box in operator_boxes(cons, "backward"):
        node = nodes[str(box_identity(box))]
        # the kind over the drawing's symbol, composed with the name the
        # box's card gives the law of motion the box references, where it
        # references one (AMD-MI-001, rules 1 and 3)
        record = cons.builder.bwd.primitives[box.name].denote()
        named = {held.identity: held.symbol for held in record.definitions}
        law = next((named[ref] for ref in box.data if getattr(ref, "kind", None) == "g"), None)
        assert attributes(node)["kind"] == box_identity(box).kind, box.name
        assert node.label == box_symbol(box, aggregations, law), box.name
        for wires, items in (
            (box.dom.inside, node.inputsMetadata),
            (box.cod.inside, node.outputsMetadata),
        ):
            ports = {m.id: attributes(m) for m in items}
            for ob in wires:
                label = wire_label(sorts[ob.identity], names.get(ob.identity))
                assert ports[str(ob.identity)]["__tensor_tag"] == label
    # the symbol alone on the box, the law named as the card names it, the
    # statement an aggregation is born at, and the policy as an attribute
    assert nodes["cntn_to_dcsn:Pullback"].label == "𝑉≻ ∘ 𝑔≻"
    assert attributes(nodes["cntn_to_dcsn:Pullback"])["policy"] == "𝑐"
    assert nodes["policy.InvEuler:Aggregation"].label == "𝐺 · InvEuler"
    output = nodes["cntn_to_dcsn:Pullback"].outputsMetadata[0]
    assert attributes(output)["__tensor_tag"] == "𝑉≻(𝑔(m_d, 𝑐(m_d)))"


@needs_viewer
def test_an_identification_that_reads_no_coordinate_function_shows_the_drawings_symbol(
    elaborate_text,
):
    # `cons.bl` without its line `endoggrid`, which defines the coordinate
    # function m_d[>]: the identification `c = c[>]` then reads no state
    # wire and references the policy block's G, no law of motion (ruling
    # MI1-K2), and the construction accepts the stage
    text = "\n".join(
        line for line in corpus_text("cons").split("\n") if "[id=endoggrid]" not in line
    )
    stage = elaborate_text(text, "cons.bl")
    collection = me.to_model_explorer(stage)
    # no graph of the view is refused: no node holds the attribute `refusal`
    held = [node for graph in collection.graphs for node in graph.nodes]
    assert not any("refusal" in attributes(node) for node in held)
    # the node's label is the symbol the drawing of the same graph
    # shows for the box, the label of its DOT statement before its tooltip
    source = stage.builder.bwd.primitives.diagram().source
    drawn = re.search(r'\[label="([^"]*)" tooltip="policy\.cons_choice:Pullback — ', source)
    nodes = {node.id: node for node in graph_named(collection, "backward").nodes}
    assert nodes["policy.cons_choice:Pullback"].label == drawn.group(1)


@needs_viewer
def test_a_refused_direction_is_one_node_saying_why(elaborate_text):
    stage = elaborate_text(BACKWARD_REFUSED, "refused.bl")
    with pytest.raises(NotConstructed):
        graph_of(stage, "builders", "backward")
    collection = me.to_model_explorer(stage)
    backward, forward = builders_graphs(collection)
    assert len(backward.nodes) == 1
    assert backward.nodes[0].label == "backward builders graph refused (not-constructed)"
    assert attributes(backward.nodes[0])["refusal"] == (
        "address 'stage': no backward builder (rule not-constructed)"
    )
    assert len(forward.nodes) > 1
    # the stage has no backward block, so its backward initial diagram holds
    # no field and no block and is not refused: a graph of no node and no layer
    initial = graph_named(collection, "backward initial diagram")
    assert initial.nodes == [] and initial.groupNodeAttributes == {}
    # the forward diagram: the three states, each in the layer of its perch,
    # and the two blocks outside the layers
    forward_initial = graph_named(collection, "forward initial diagram")
    assert [(n.id, n.namespace) for n in forward_initial.nodes] == [
        ("forward_only:arvl:x", "arvl"),
        ("forward_only:dcsn:x_d", "dcsn"),
        ("forward_only:cntn:a", "cntn"),
        ("arvl_to_dcsn", ""),
        ("dcsn_to_cntn", ""),
    ]
    # an initial diagram the construction refused is one node, named as the
    # documentation names the diagram
    unbuilt = NotConstructed("no blocks", rule="not-constructed")
    refused = me._refused_graph(
        me._viewer(),
        me.INITIAL_IDS["backward"],
        me._refused_label("backward", unbuilt, "initial"),
        {"refusal": str(unbuilt)},
    )
    assert [n.id for n in refused.nodes] == ["backward initial diagram:refused"]
    assert refused.nodes[0].label == "backward initial diagram refused (not-constructed)"


def test_a_refused_direction_is_labeled_by_the_rule_its_refusal_names():
    # the rule the refusal names, which its text writes in its closing
    # parenthesis; the direction alone where the refusal names no rule
    named = NotConstructed("no forward builder", rule="not-constructed")
    assert str(named).endswith("(rule not-constructed)")
    assert (
        me._refused_label("forward", named) == "forward builders graph refused (not-constructed)"
    )
    unnamed = NotConstructed("no backward builder")
    assert me._refused_label("backward", unnamed) == "backward builders graph refused"
    assert me._refused_label("backward", unnamed, "initial") == "backward initial diagram refused"


@needs_viewer
def test_a_branching_forward_decision_builder_keeps_every_branch_output(ret_choice):
    forward = graph_named(me.to_model_explorer(ret_choice), "forward")
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
    given = {edge.targetNodeInputId for edge in nodes[me.BOUNDARY_IDS[1]].incomingEdges}
    assert written <= given
    # each branch's measure is labeled by its branch on the decision builder's
    # output ports
    labels = [
        attributes(m)["__tensor_tag"] for m in nodes["dcsn_to_cntn:Pushforward"].outputsMetadata
    ]
    assert labels == ["μ_work≻", "μ_retire≻"]


@needs_viewer
def test_the_style_follows_the_level_and_the_builders_outputs(sa_savings):
    white, navy, ultramarine = "#FFFFFF", "#172A52", "#214EDA"
    ice_2, ice_3 = "#C5E5F1", "#91BED7"
    backward = graph_named(me.to_model_explorer(sa_savings), "backward")
    # the builder a node stands in, the first part of its namespace
    builders = {node.id: node.namespace.split("/")[0] for node in backward.nodes}
    # the nodes that write a wire read by a node of another builder or by
    # `Outputs`, read from the graph's edges
    output_writers = {
        edge.sourceNodeId
        for node in backward.nodes
        for edge in node.incomingEdges
        if edge.sourceNodeId != me.BOUNDARY_IDS[0]
        and (node.id == me.BOUNDARY_IDS[1] or builders[node.id] != builders[edge.sourceNodeId])
    }
    # the evaluation that ends each builder; the stage has no arrival perch,
    # so no builder ends there (decision MB-V49)
    assert output_writers == {
        "cntn_to_dcsn:Evaluation",
        "policy:Evaluation",
    }
    for node in backward.nodes:
        style = node.style
        # white with a navy label
        assert (style.backgroundColor, style.textColor) == (white, navy)
        # an ultramarine border where the node writes a builder's output, navy
        # under the pointer; a navy one elsewhere, `Inputs` and `Outputs`
        # among them, ultramarine under the pointer
        if node.id in output_writers:
            assert (style, style.borderColor, style.hoveredBorderColor) == (
                me.OUTPUT_STYLE,
                ultramarine,
                navy,
            ), node.id
        else:
            assert (style, style.borderColor, style.hoveredBorderColor) == (
                me.NODE_STYLE,
                navy,
                ultramarine,
            ), node.id
    # each layer as the viewer applies the configurations: a builder on the
    # second step of the ice and a sub-builder on the third, top to bottom,
    # each with a navy border and a navy label
    configs = backward.groupNodeConfigs
    applied = {layer: as_the_viewer_applies(configs, layer) for layer in layers_of(backward)}
    assert applied == {
        "cntn_to_dcsn": (0, ice_2, navy, navy),
        "cntn_to_dcsn/ambiguity_ce": (0, ice_3, navy, navy),
        "cntn_to_dcsn/risk_ce": (0, ice_3, navy, navy),
        "policy": (0, ice_2, navy, navy),
    }
    # a configuration lays out the graph's root, which is no layer, so that
    # Bellman Workbench turns the root with the layers (`model.oriented`)
    assert as_the_viewer_applies(configs, "")[0] == 0


@needs_viewer
def test_a_bound_version_is_labeled_by_its_bindings(cons_methods_only):
    assert me.to_model_explorer(cons_methods_only).label == "cons methodized"


def test_a_wire_with_two_writers_or_with_none_is_refused():
    # a wire of a hypergraph has one writer, and every wire a box reads is
    # written; the view refuses a graph that breaks either rather than lose
    # an edge without saying so
    def wires(names):
        return SimpleNamespace(inside=[SimpleNamespace(identity=name) for name in names])

    def part(identity, reads=(), writes=()):
        return SimpleNamespace(identity=identity, dom=wires(reads), cod=wires(writes))

    graph = part("graph")
    two = [part("a:Pullback", writes=["w"]), part("b:Pullback", writes=["w"])]
    with pytest.raises(ValueError, match="w is written by both a:Pullback and b:Pullback"):
        me._writers(graph, two)
    with pytest.raises(ValueError, match="w that a:Pullback reads is written by no node"):
        me._writers(graph, [part("a:Pullback", reads=["w"])])


def test_without_the_viewer_the_module_refuses_in_one_sentence(cons, monkeypatch):
    # an entry of None in `sys.modules` makes the import of that name fail,
    # whether or not the viewer is installed
    # each module the view imports is hidden, since a module that an earlier
    # test imported is found under its own name
    for name in (
        "model_explorer",
        "model_explorer.graph_builder",
        "model_explorer.apis",
        "model_explorer.config",
    ):
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(ImportError) as refusal:
        me.to_model_explorer(cons)
    assert "pip install" in str(refusal.value) and "explore" in str(refusal.value)
    # the server is refused in the same sentence
    with pytest.raises(ImportError) as refusal:
        me.serve("cons.graph.json")
    assert "pip install" in str(refusal.value) and "explore" in str(refusal.value)


def test_the_card_module_answers_the_sections_the_card_prints(
    cons, port, ret_choice, cons_methods_only
):
    # every card of each stage, the stage's own, each builder's and each
    # primitive's, the methodized cons among them for `Method` and `Options`
    for stage in (cons, port, ret_choice, cons_methods_only):
        records = [stage.denote()]
        for word in ("bwd", "fwd"):
            graph = getattr(stage.builder, word)
            for name in graph.list():
                records.append(graph[name].denote())
                pieces = graph[name].primitives
                records.extend(pieces[key].denote() for key in pieces.list())
        for record in records:
            sections = card_sections(record)
            assert [(s.heading, s.rows) for s in sections] == printed_sections(str(record))
            assert all(s.heading.startswith(WORDS[s.label]) for s in sections)


def test_item_2_a_primitives_attributes_are_its_cards_rows_one_line_each(cons, port, ret_choice):
    for stage in (cons, port, ret_choice):
        for direction in DIRECTIONS:
            for box in operator_boxes(stage, direction):
                identity = box_identity(box)
                attrs = me.box_attributes(stage, direction, box)
                card = str(me.piece_handle(stage, direction, box).denote())
                assert all("\n" not in value for value in attrs.values()), identity
                # one attribute to a line of what `kernel()` prints
                assert "\n".join(numbered(attrs, "kernel")) == str(kernel(stage, box)), identity
                # one attribute to a rule of the card's `Rule`, the region it
                # holds on in its row; an evaluation lists no rule that a box
                # before it states
                expected = printed_rules(card)
                if identity.kind == "Evaluation":
                    before = {
                        rule
                        for other in boxes_before(stage, direction, box)
                        for rule in printed_rules(
                            str(me.piece_handle(stage, direction, other).denote())
                        )
                    }
                    expected = [rule for rule in expected if rule not in before]
                assert [spaced(rule) for rule in numbered(attrs, "rule")] == expected, identity
                # `lines`: the file and the numbers of the lines the card's
                # `Source` section quotes
                assert expanded(attrs.get("lines")) == quoted_lines(card), identity
                # the rows of `Where` stand on the builder's layer
                assert not numbered(attrs, "where"), identity
                assert "method" not in attrs  # a symbolic version binds no method
    attrs = me.box_attributes(
        cons, "backward", box_named(cons, "backward", "cntn_to_dcsn:Aggregation")
    )
    assert attrs["kind"] == "Aggregation"
    assert numbered(attrs, "kernel") == [
        "𝐺 of cntn_to_dcsn: 𝐺(V≻, m_d, c) = 𝑢(c) + V≻",
        "output V; unused m_d",
    ]
    assert numbered(attrs, "rule") == [
        "𝑉(m_d) = 𝑢(𝑐(m_d)) + 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))",
    ]
    assert attrs["lines"] == "cons.bl 21"
    # the branching stage: a rule the card breaks over three lines, on one
    pushforward = box_named(ret_choice, "forward", "dcsn_to_cntn:Pushforward")
    attrs = me.box_attributes(ret_choice, "forward", pushforward)
    assert numbered(attrs, "rule") == [
        "μ_work≻(B) = μ({a_d ∈ ℝ₊ | 𝑑(a_d) = work ∧ 𝑔_work≻(a_d) ∈ B})",
        "μ_retire≻(B) = μ({a_d ∈ ℝ₊ | 𝑑(a_d) = retire ∧ 𝑔_retire≻(a_d) ∈ B})",
    ]
    # a section of one row, and a kernel of one line, is one attribute named
    # by its word alone
    argmax = box_named(ret_choice, "backward", "policy.choice:Argmax")
    attrs = me.box_attributes(ret_choice, "backward", argmax)
    assert attrs["rule"] == (
        "𝑑(a_d) ∈ argmax_{d ∈ {work, retire}} [(𝑉_w≻(𝑔_work≻(a_d)) − δ, 𝑉_r≻(𝑔_retire≻(a_d)))[d]]"
    )
    assert attrs["kernel"] == str(kernel(ret_choice, argmax))
    assert not {"rule 1", "kernel 1"} & set(attrs)


def test_a_primitive_shows_no_card_call_and_no_condition_rows(cons, port, ret_choice):
    # AAS, 30 September 2026: the call that prints the card and the rows of
    # the card's `Conditions` are not among a primitive's attributes
    conditions = 0
    for stage in (cons, port, ret_choice):
        for direction in DIRECTIONS:
            for box in operator_boxes(stage, direction):
                attrs = me.box_attributes(stage, direction, box)
                assert "card" not in attrs, box.name
                assert not [key for key in attrs if key.startswith("condition")], box.name
                card = str(me.piece_handle(stage, direction, box).denote())
                conditions += sum(
                    len(held)
                    for heading, held in printed_sections(card)
                    if heading.split("  ")[0] == "Conditions"
                )
    # the cards print conditions, which the view leaves out
    assert conditions > 0
    # the order an economist reads: what the box is, the rules it states,
    # the function it computes, the policy it is held at, the method bound
    # within it, the lines
    aggregation = box_named(cons, "backward", "cntn_to_dcsn:Aggregation")
    assert list(me.box_attributes(cons, "backward", aggregation)) == [
        "kind",
        "policy",
        "rule",
        "kernel 1",
        "kernel 2",
        "lines",
    ]


def test_a_primitive_whose_card_prints_no_rule_carries_no_rule(elaborate_text):
    # the identification of `keeper_cons.bl`'s policy builder, which the method
    # block of `keeper_cons_egm.bl` opens once the stage is bound with its
    # methods file, is the one primitive of the core stages whose card has no
    # `Rule` section (decision MB-U15)
    path = "applications/durables/declaration/stages/keeper_cons/keeper_cons.bl"
    stage = elaborate_text((ROOT / path).read_text(encoding="utf-8"), path)
    stage.methodize(ROOT / "applications/durables/declaration/stages/keeper_cons/methods.yml")
    box = box_named(stage, "backward", "policy.cons_choice:Pullback")
    attrs = me.box_attributes(stage, "backward", box)
    assert not numbered(attrs, "rule")
    assert numbered(attrs, "kernel") == ["equation c = c[>]", "unknowns c"]


@needs_viewer
def test_item_3_every_bound_method_stands_in_its_nodes_row_and_mark_or_on_its_layer(
    cons, cons_methods_only
):
    def showing(collection, keys):
        """The ids of the nodes and the namespaces of the layers that show
        one of these attributes."""
        found = set()
        for graph in collection.graphs:
            found |= {n.id for n in graph.nodes if keys & set(attributes(n))}
            layers = (graph.groupNodeAttributes or {}).items()
            found |= {namespace for namespace, shown in layers if keys & set(shown)}
        return found

    def marked(collection):
        """The tag the label of each node marks, by node id: the text after
        the last ` · ` of the label's last line where it begins with `!`,
        and the empty text where the label marks no tag."""
        found = {}
        for graph in collection.graphs:
            for n in graph.nodes:
                _, mark, tag = n.label.split("\n")[-1].rpartition(" · ")
                found[n.id] = tag if mark and tag.startswith("!") else ""
        return found

    # the plain version shows no method on any node, layer or label
    plain = me.to_model_explorer(cons)
    assert showing(plain, {"method", "handler"}) == set()
    assert set(marked(plain).values()) == {""}
    # every binding the builders graphs answer stands on one node or on one
    # layer, a binding with a handler and no tag included
    bound = me.to_model_explorer(cons_methods_only)
    graphs = (cons_methods_only.builder.bwd, cons_methods_only.builder.fwd)
    targets = {str(target) for graph in graphs for target in graph.methods}
    assert showing(bound, {"method", "handler"}) == targets
    for graph in bound.graphs:
        assert all("\n" not in value for n in graph.nodes for value in attributes(n).values())
        layers = (graph.groupNodeAttributes or {}).values()
        assert all("\n" not in value for shown in layers for value in shown.values())
    # the label of a node marks the tag its `method` row holds, and the label
    # of a node with no `method` row marks none
    rows = {n.id: attributes(n).get("method", "") for g in bound.graphs for n in g.nodes}
    assert marked(bound) == rows
    # two backward evaluations hold a tag, since the methods of the forward
    # graph are bound at its builders alone
    assert {node_id: tag for node_id, tag in rows.items() if tag} == {
        "cntn_to_dcsn:Evaluation": "!Linear",
        "policy:Evaluation": "!egm",
    }
    # a bound method colors no node: each node keeps the style it has in the
    # plain version
    styles = {n.id: n.style for g in plain.graphs for n in g.nodes}
    assert {n.id: n.style for g in bound.graphs for n in g.nodes} == styles
    # the node shows the card's `Method` row as its tag and its handler, and
    # one attribute to a row of the card's `Options`
    nodes = {n.id: n for n in graph_named(bound, "backward").nodes}
    evaluation = attributes(nodes["cntn_to_dcsn:Evaluation"])
    assert evaluation["handler"] == "cons-port:_make_interp"
    box = box_named(cons_methods_only, "backward", "cntn_to_dcsn:Evaluation")
    card = str(me.piece_handle(cons_methods_only, "backward", box).denote())
    (options,) = [held for heading, held in printed_sections(card) if heading == "Options"]
    assert numbered(evaluation, "option") == [one_line(row) for row in options]
    assert numbered(evaluation, "option") == [
        "grid = !Cartesian",
        "orders = {'m_d': 'n_m'}",
        "bounds = {'m_d': ('m_min', 'm_max')}",
    ]
    assert not numbered(evaluation, "setting")  # this version configures no setting
    # `!egm` names its exogenous grid of savings (AMD-MB-003 §1)
    assert numbered(attributes(nodes["policy:Evaluation"]), "option") == [
        "grid = !Cartesian",
        "orders = {'a': 'n_a'}",
        "bounds = {'a': ('a_min', 'a_max')}",
    ]
    # a method bound at a builder, and at none of its primitives, stands on
    # the builder's layer
    layers = graph_named(bound, "forward").groupNodeAttributes
    assert layers["arvl_to_dcsn"]["method"] == "!deterministic"
    assert layers["dcsn_to_cntn"]["handler"] == "cons-port:transition_fwd"
    assert "method" not in layers["dcsn_to_cntn"]


def test_a_configured_version_shows_the_settings_its_options_name(cons_configured):
    box = box_named(cons_configured, "backward", "cntn_to_dcsn:Evaluation")
    attrs = me.box_attributes(cons_configured, "backward", box)
    # the card writes the configured values into the options
    assert numbered(attrs, "option") == [
        "grid = !Cartesian",
        "orders = {'m_d': 8000}",
        "bounds = {'m_d': (0.01, 2000.0)}",
    ]
    # one attribute to a setting the options name, as the version's settings
    # print it
    assert numbered(attrs, "setting") == [
        str(cons_configured.settings[name]) for name in ("n_m", "m_min", "m_max")
    ]
    assert attrs["setting 1"] == (
        "n_m = 8000, read at cntn_to_dcsn:Evaluation by !Linear for its grid !Cartesian")
    # the method's rows stand after the kernel and before the lines
    assert list(attrs) == [
        "kind",
        "rule 1",
        "rule 2",
        "kernel",
        "method",
        "handler",
        "option 1",
        "option 2",
        "option 3",
        "setting 1",
        "setting 2",
        "setting 3",
    ]


@needs_viewer
def test_the_perch_overlays_paint_every_wire_at_its_perch(cons):
    import dacite
    from model_explorer import graph_builder as gb

    overlays = me.perch_overlays(cons)
    assert [o.name for o in overlays] == ["arrival", "decision", "continuation"]
    # navy, the orange of a line and ultramarine, the stylesheet's perch
    # tokens `--bf-arvl`, `--bf-accent-line` and `--bf-cntn-line`
    assert [o.edgeColor for o in overlays] == ["#172A52", "#C45C1D", "#214EDA"]
    collection = me.to_model_explorer(cons)
    # every edge of both graphs whose wire lives at a perch, in the order of
    # the nodes and of their ports
    expected = {"arvl": [], "dcsn": [], "cntn": []}
    for graph in collection.graphs:
        for node in graph.nodes:
            ports = {m.id: attributes(m) for m in node.inputsMetadata}
            for edge in node.incomingEdges:
                perch = ports[edge.targetNodeInputId].get("perch", "")
                if perch in expected:
                    expected[perch].append((edge.sourceNodeId, node.id))
    assert all(expected.values())  # cons has wires at all three perches
    for overlay, perch in zip(overlays, expected):
        assert [(e.sourceNodeId, e.targetNodeId) for e in overlay.edges] == expected[perch]
    # an overlay edge has no label, and no graph carries the overlays, since
    # the viewer draws an overlay edge as a straight line between two nodes
    # (AAS, 30 September 2026)
    assert all(e.label is None for overlay in overlays for e in overlay.edges)
    assert all(graph.tasksData is None for graph in collection.graphs)
    # the overlays load into the viewer's classes
    loaded = dacite.from_dict(
        gb.EdgeOverlaysData,
        dataclasses.asdict(gb.EdgeOverlaysData(name="perches", overlays=overlays)),
    )
    assert loaded.overlays == overlays


@needs_viewer
def test_no_value_of_the_view_holds_a_line_break(adjuster_saving):
    # the policy of `adjuster_saving.bl` is a pair chosen from a set whose
    # carrier the printing breaks at the width of a card
    collection = me.to_model_explorer(adjuster_saving)
    for graph in collection.graphs:
        for node in graph.nodes:
            items = [node, *node.inputsMetadata, *node.outputsMetadata]
            assert all("\n" not in pair.value for item in items for pair in item.attrs), node.id
        for shown in (graph.groupNodeAttributes or {}).values():
            assert all("\n" not in value for value in shown.values())
    # the layer's side is the printed signature with its line breaks and
    # indentation removed
    signature = adjuster_saving.builder.bwd["policy"].signature()
    printed = [str(line) for side, line in signature.entries if side == "out"]
    assert any("\n" in line for line in printed)
    outputs = graph_named(collection, "backward").groupNodeAttributes["policy"]["outputs"]
    assert outputs == ", ".join(one_line(line.split("\n")) for line in printed)


@needs_viewer
def test_every_color_the_view_writes_is_a_token_of_the_palette(
    cons_methods_only, port_cons, tmp_path
):
    # each token of the palette has the value the brand's stylesheet gives
    # the custom property it is named by
    stylesheet = (ROOT / "docs/_stylesheets/bellman.css").read_text(encoding="utf-8")
    for name, value in me.PALETTE.items():
        assert f"{name}:{value}" in stylesheet, name
    tokens = set(me.PALETTE.values())
    # every color of the two files of a bound stage and of a trellis: the
    # nodes, the layers and the overlays
    written = []
    for view, folder in ((cons_methods_only, "stage"), (port_cons, "trellis")):
        for path in me.write_model_explorer(view, tmp_path / folder):
            written += colors_in(json.loads(path.read_text(encoding="utf-8")))
    keys = {key for key, _ in written}
    assert keys == {
        "backgroundColor",
        "borderColor",
        "hoveredBorderColor",
        "textColor",
        "edgeColor",
    }
    assert {value for _, value in written} <= tokens
    # and every color the module can write, a refused graph's node among
    # them
    styles = [me.NODE_STYLE, me.OUTPUT_STYLE, me.REFUSAL_STYLE]
    tables = [
        *(dataclasses.astuple(style) for style in styles),
        *me.LAYER_COLORS.values(),
        me.PERCH_COLORS.values(),
    ]
    assert {color for table in tables for color in table} <= tokens
    # the three perch overlays keep three distinct colors
    assert len(set(me.PERCH_COLORS.values())) == 3
    # every label can be read on its fill, at the ratio WCAG 2.2 asks of
    # text, and every overlay's edges, drawn in its color, on the page's
    # white, at the ratio it asks of a graphical object
    for style in styles:
        assert contrast(style.backgroundColor, style.textColor) >= 4.5, style
    for fill, _, label in me.LAYER_COLORS.values():
        assert contrast(fill, label) >= 4.5
    for color in me.PERCH_COLORS.values():
        assert contrast(color, me.PALETTE["--bf-face"]) >= 3, color


@needs_viewer
def test_item_4_the_two_files_load_through_dacite_into_the_viewers_dataclasses(
    cons, cons_methods_only, tmp_path
):
    import dacite
    from model_explorer import graph_builder as gb

    def read(path):
        """A file the view is written to, read as JSON."""
        return json.loads(path.read_text(encoding="utf-8"))

    graph_path, overlays_path = me.write_model_explorer(cons, tmp_path)
    assert [graph_path.name, overlays_path.name] == ["cons.graph.json", "cons.edge-overlays.json"]
    collection = dacite.from_dict(gb.GraphCollection, read(graph_path))
    assert [g.id for g in collection.graphs] == STAGE_GRAPHS
    # the file holds the collection, the fields the viewer's page reads and
    # its classes do not declare among them, and loads into those classes
    # with those fields left out
    assert read(graph_path) == as_json(me.to_model_explorer(cons))
    assert collection == in_viewer_classes(me.to_model_explorer(cons))
    # each file holds ASCII alone, its mathematical letters written as
    # escapes, so that the viewer's server, which opens a file in the
    # system's default encoding, reads it alike under a Windows code page
    for path in (graph_path, overlays_path):
        assert path.read_bytes().isascii(), path.name
        assert json.loads(path.read_text(encoding="cp1252")) == read(path)
    overlays = read(overlays_path)
    assert [o["name"] for o in overlays["overlays"]] == ["arrival", "decision", "continuation"]
    assert dacite.from_dict(gb.EdgeOverlaysData, overlays) == gb.EdgeOverlaysData(
        name="perches", overlays=me.perch_overlays(cons)
    )
    # a version's bindings name its files, each space written as a hyphen
    paths = me.write_model_explorer(cons_methods_only, tmp_path / "methodized")
    assert [p.name for p in paths] == [
        "cons-methodized.graph.json",
        "cons-methodized.edge-overlays.json",
    ]


@needs_viewer
def test_explore_writes_the_files_and_serves_them_on_one_port(cons, tmp_path, monkeypatch, capsys):
    served, opened, browsed = [], [], threading.Event()
    monkeypatch.setattr(
        me,
        "serve",
        lambda *args, **kwargs: served.append((args, kwargs)) or "http://localhost:0/",
    )

    def open_page(url, *args, **kwargs):
        """The browser, replaced by a record of the address it is given and
        of whether the thread that gives it is a daemon."""
        opened.append((url, threading.current_thread().daemon))
        browsed.set()

    # the test opens no browser
    monkeypatch.setattr(me.webbrowser, "open", open_page)
    paths, url = me.explore(cons, folder=tmp_path, open_browser=False)
    assert all(p.exists() for p in paths) and served == [] and url is None
    paths, url = me.explore(cons, folder=tmp_path, open_browser=True)
    assert url == "http://localhost:0/"
    # the graph file is served on the one port, the graph `backward` shown
    # with its three builders opened
    ((args, kwargs),) = served
    assert args == paths[:1] and (kwargs["port"], kwargs["graph_id"]) == (8080, "backward")
    assert set(kwargs["layers"]) == {"cntn_to_dcsn", "dcsn_to_arvl", "policy"}
    # two sentences, the address and how to see the mathematical labels
    assert capsys.readouterr().out.splitlines() == [
        "The view is at http://localhost:0/.",
        me.SVG_TEXT_SENTENCE,
    ]
    # the browser opens the address from a daemon thread
    assert browsed.wait(5) and opened == [(url, True)]


@contextlib.contextmanager
def answering(text, status=200):
    """A standard-library server on a free port of this machine that answers
    every request with `status` and `text`, run in a daemon thread; yields
    its port. No viewer is needed."""

    class Handler(http.server.BaseHTTPRequestHandler):
        """A handler that answers every request alike."""

        def do_GET(self):
            self.send_response(status)
            self.end_headers()
            self.wfile.write(text.encode("utf-8"))

        def log_message(self, *args):
            """Nothing is logged, so the test prints nothing."""

    server = http.server.HTTPServer(("localhost", 0), Handler)
    # the server asks every twentieth of a second whether it is to stop
    threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
    ).start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


def released_port():
    """A port of this machine just released, at which no server listens."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("localhost", 0))
        return probe.getsockname()[1]


def graph_file(folder):
    """A graph file of one collection, `cons`, with the graphs `backward`
    and `forward`, which `serve` reads for the graph and the label it
    shows."""
    path = folder / "cons.graph.json"
    graphs = [{"id": "backward", "nodes": []}, {"id": "forward", "nodes": []}]
    path.write_text(json.dumps({"label": "cons", "graphs": graphs}), encoding="utf-8")
    return path


def stub_viewer(monkeypatch, started):
    """The viewer's server and configuration, replaced by records that start
    nothing: each call of the server appends to `started` whether its thread
    is a daemon and its arguments, and the configuration writes an empty
    address."""
    config = SimpleNamespace(
        add_model_from_path=lambda path: None,
        to_url_param_value=lambda: quote("{}"),
    )

    def visualize_from_config(**kwargs):
        started.append((threading.current_thread().daemon, kwargs))

    apis = SimpleNamespace(visualize_from_config=visualize_from_config)
    viewer_config = SimpleNamespace(ModelExplorerConfig=lambda: config)
    monkeypatch.setattr(me, "_viewer_server", lambda: (apis, viewer_config))


def test_serve_uses_a_viewer_that_answers_and_refuses_another_program(tmp_path, monkeypatch):
    started = []
    stub_viewer(monkeypatch, started)
    graph = graph_file(tmp_path)
    # a port at which the viewer's server answers is used, whichever process
    # started it: no server is started
    with answering(me.VIEWER_HEALTH) as port:
        url = me.serve(graph, port=port)
    assert url.startswith(f"http://localhost:{port}/?data=") and started == []
    # a port at which another program answers is refused in one sentence that
    # names the port and the argument that chooses another
    with answering("another program") as port:
        with pytest.raises(ValueError, match=rf"port {port}; .* port="):
            me.serve(graph, port=port)
    with answering("", status=404) as port:
        with pytest.raises(ValueError, match=rf"port {port}"):
            me.serve(graph, port=port)
    assert started == []
    # where nothing listens, the server is started in a daemon thread of this
    # process on the port given, and opens no browser
    monkeypatch.setattr(me, "_wait_until_answered", lambda page: True)
    port = released_port()
    me.serve(graph, port=port)
    deadline = time.monotonic() + 5
    while not started and time.monotonic() < deadline:
        time.sleep(0.01)
    ((daemon, kwargs),) = started
    assert daemon and (kwargs["host"], kwargs["port"], kwargs["no_open_in_browser"]) == (
        "localhost",
        port,
        True,
    )


@needs_viewer
def test_the_address_names_the_graph_file_the_graph_and_the_layers_opened(
    cons_methods_only, tmp_path
):
    # a version within which a method is bound
    graph, _ = me.write_model_explorer(cons_methods_only, tmp_path)
    with answering(me.VIEWER_HEALTH) as port:
        url = me.serve(graph, port=port, layers=("cntn_to_dcsn", "policy"))
        forward = me.serve(graph, port=port, graph_id="forward")
    page, _, data = url.partition("?data=")
    assert page == f"http://localhost:{port}/"
    # the configuration the viewer's own server writes, which names the
    # graph file by its path and no other file, and the state of the page
    decoded = json.loads(unquote(data))
    assert set(decoded) == {"models", "uiState"}
    assert decoded["models"] == [{"url": os.path.abspath(graph)}]
    assert decoded["uiState"] == {
        "paneStates": [
            {
                "deepestExpandedGroupNodeIds": ["cntn_to_dcsn___group___", "policy___group___"],
                "selectedNodeId": "",
                "selectedGraphId": "backward",
                "selectedCollectionLabel": "cons methodized",
                "widthFraction": 1,
                "flattenLayers": False,
            }
        ]
    }
    # the graph named is the graph shown
    (pane,) = json.loads(unquote(forward.partition("?data=")[2]))["uiState"]["paneStates"]
    assert pane["selectedGraphId"] == "forward" and pane["deepestExpandedGroupNodeIds"] == []


@needs_viewer
def test_the_server_is_started_in_a_daemon_thread_where_nothing_listens(
    tmp_path, monkeypatch, capsys
):
    # the module `config`, which the package's name `config`, a function,
    # hides from `from model_explorer import config`
    viewer_config = importlib.import_module("model_explorer.config")
    # the viewer's function that runs the server, replaced by one that
    # records how it is called and returns
    calls, called = [], threading.Event()

    def visualize_from_config(**kwargs):
        calls.append((threading.current_thread().daemon, kwargs))
        called.set()

    apis = SimpleNamespace(visualize_from_config=visualize_from_config)
    monkeypatch.setattr(me, "_viewer_server", lambda: (apis, viewer_config))
    # no server answers, so the call waits the whole time
    monkeypatch.setattr(me, "SERVER_WAIT_SECONDS", 0.2)
    graph = graph_file(tmp_path)
    port = released_port()
    url = me.serve(graph, port=port)
    assert called.wait(5)
    ((daemon, kwargs),) = calls
    assert daemon
    assert (kwargs["host"], kwargs["port"], kwargs["no_open_in_browser"]) == (
        "localhost",
        port,
        True,
    )
    # the server is given the configuration whose graph file the address names
    config = kwargs["config"]
    written = json.loads(unquote(config.to_url_param_value()))
    decoded = json.loads(unquote(url.partition("?data=")[2]))
    assert {key: decoded[key] for key in written} == written
    assert url.startswith(f"http://localhost:{port}/?data=")
    # the server has not answered, which one printed sentence says
    assert f"port {port}" in capsys.readouterr().out
    # a port at which another program listens without answering is refused
    # before any server is started
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind(("localhost", 0))
        busy.listen()
        port = busy.getsockname()[1]
        with pytest.raises(ValueError, match=f"port {port}"):
            me.serve(graph, port=port)
    assert len(calls) == 1


@pytest.mark.parametrize("status", [200, 500])
def test_a_server_that_answers_ends_the_wait_whatever_its_status(status):
    # a standard-library server on a free port; no viewer is needed
    with answering("", status=status) as port:
        assert me._wait_until_answered(f"http://localhost:{port}/")


def test_the_wait_ends_unanswered_where_no_server_listens(monkeypatch):
    monkeypatch.setattr(me, "SERVER_WAIT_SECONDS", 0.3)
    port = released_port()
    began = time.monotonic()
    assert not me._wait_until_answered(f"http://localhost:{port}/")
    # the wait lasts its time, and the last request adds at most one second
    assert 0.3 <= time.monotonic() - began < 1.5


def test_a_server_that_has_not_answered_is_named_in_one_printed_sentence(
    tmp_path, monkeypatch, capsys
):
    started = []
    stub_viewer(monkeypatch, started)
    graph = graph_file(tmp_path)
    monkeypatch.setattr(me, "_wait_until_answered", lambda page: False)
    port = released_port()
    url = me.serve(graph, port=port)
    # a slow start may still succeed: the call answers the address and warns
    assert url.startswith(f"http://localhost:{port}/?data=")
    printed = capsys.readouterr().out
    assert printed.count("\n") == 1 and f"port {port}" in printed
    monkeypatch.setattr(me, "_wait_until_answered", lambda page: True)
    me.serve(graph, port=released_port())
    assert capsys.readouterr().out == ""


def test_the_default_folder_stands_beside_the_stage_file(cons, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # the origin
    # `applications/portfolio-choice/declaration/stages/cons/cons.bl` names no
    # file from this working directory
    assert me._default_folder(cons) == Path("model-explorer")
    source = tmp_path / "stages" / "cons.bl"
    source.parent.mkdir()
    source.write_text(
        (ROOT / "applications/portfolio-choice/declaration/stages/cons/cons.bl").read_text(
            encoding="utf-8"),
        encoding="utf-8",
    )
    stage = elaborate_stage(load_stage(str(source)))
    assert me._default_folder(stage) == source.parent / "model-explorer"


@needs_viewer
def test_a_trellis_is_four_graphs_with_a_layer_per_period_and_per_occurrence(
    port_cons, port_cons_view
):
    """The two builders graphs, then the two initial diagrams of design pass
    14 §7 (S-D12), which `test_a_trellis_s_initial_diagram_joins_the_fields_
    of_its_occurrences` reads; the builders graphs as before."""
    collection = port_cons_view
    assert collection.label == "trellis"
    assert [g.id for g in collection.graphs] == [
        "backward",
        "forward",
        "backward initial diagram",
        "forward initial diagram",
    ]
    namespaces = {n.namespace for n in graph_named(collection, "backward").nodes}
    periods = {ns.split("/")[0] for ns in namespaces if ns.startswith("periods[")}
    assert len(periods) == len(port_cons["periods"])
    assert any(ns.count("/") >= 2 for ns in namespaces)  # periods[h]/<stage>/<builder>
    for graph in collection.graphs[:2]:
        nodes = {n.id: n for n in graph.nodes}
        # two occurrences of one stage have distinct ids
        assert len(nodes) == len(graph.nodes)
        for node in graph.nodes:
            inputs = {m.id for m in node.inputsMetadata}
            for edge in node.incomingEdges:
                outputs = {m.id for m in nodes[edge.sourceNodeId].outputsMetadata}
                assert edge.sourceNodeOutputId in outputs and edge.targetNodeInputId in inputs
            # every input port has an edge
            assert inputs == {e.targetNodeInputId for e in node.incomingEdges}, node.id
        # each layer as the viewer applies the configurations, by the number
        # of parts of its namespace: the periods side by side, each white, its
        # stages in forward order; an occurrence on the first step of the ice
        # and a builder on the second, top to bottom, each with a navy border
        # and a navy label
        configs, navy = graph.groupNodeConfigs, "#172A52"
        assert {
            (namespace.count("/") + 1, as_the_viewer_applies(configs, namespace))
            for namespace in layers_of(graph)
        } == {
            (1, (1, "#FFFFFF", navy, navy)),
            (2, (0, "#EDF7FC", navy, navy)),
            (3, (0, "#C5E5F1", navy, navy)),
        }
        # the root, which is no layer, laid out left to right; a sub-builder,
        # which no stage of this trellis holds, on the third step of the ice
        assert as_the_viewer_applies(configs, "") == (1, None, None, None)
        assert as_the_viewer_applies(configs, "periods[0]/sa/cntn_to_dcsn/risk_ce") == (
            0,
            "#91BED7",
            navy,
            navy,
        )
        # a period's index stands in its layer's name and in no attribute; an
        # occurrence's layer shows its stage, labeled by the bindings it
        # holds, and the fixture's occurrences are calibrated, methodized and
        # configured (decision SD-63)
        layers = graph.groupNodeAttributes
        assert layers["periods[2]"] == {}
        assert layers["periods[2]/cons"] == {"stage": "cons calibrated methodized configured"}
        # an occurrence holds its builders exactly as the stage view does,
        # every id and namespace under the occurrence's address
        prefix = "periods[2]/cons/"
        (alone,) = [
            g
            for g in me.to_model_explorer(port_cons["periods"][2]["stages"]["cons"]).graphs
            if g.id == graph.id
        ]
        inner = {ns[len(prefix) :]: shown for ns, shown in layers.items() if ns.startswith(prefix)}
        assert inner == alone.groupNodeAttributes
        # the occurrence's own `Outputs`, which holds its policy, aside
        held = {
            n.id[len(prefix) :]: n
            for n in graph.nodes
            if n.id.startswith(prefix) and n.id[len(prefix) :] not in me.BOUNDARY_IDS
        }
        boxes = [n for n in alone.nodes if n.id not in me.BOUNDARY_IDS]
        assert set(held) == {n.id for n in boxes}
        for node in boxes:
            copy = held[node.id]
            assert (copy.label, copy.attrs, copy.style) == (node.label, node.attrs, node.style)
            assert copy.namespace == prefix + node.namespace
        # the graph carries no perch overlay
        assert graph.tasksData is None
    # the joins of the forward graph, each an edge from the continuation
    # measure's writer in one occurrence to the arrival measure's reader in
    # another, labeled on the reading port as the trellis drawing labels it
    forward = graph_named(collection, "forward")
    joins = [join[:3] for join in join_edges(forward)]
    between = [join for join in joins if join[0][0] != join[1][0]]
    assert sorted(between) == sorted(
        ((f"periods[{h + 1}]", "disc"), (f"periods[{h}]", "port"), f"inter_connectors[{h}] a → k")
        for h in range(5)
    )
    # within each period, port continues to cons by the connector and cons to
    # disc by the equal name
    within = sorted(join for join in joins if join[0][0] == join[1][0])
    assert within == sorted(
        [((f"periods[{h}]", "port"), (f"periods[{h}]", "cons"), "w → m") for h in range(6)]
        + [((f"periods[{h}]", "cons"), (f"periods[{h}]", "disc"), "a") for h in range(6)]
    )
    # the wires that enter and leave the trellis, each at a boundary node of
    # its own, those entering first among the nodes and those leaving last
    # (design pass 10 §6): forward, the arrival measure of the first period
    # in time and the continuation measure of the last
    assert boundary_ports(forward, "start") == ["periods[5]/port/port:measure:dcsn"]
    assert boundary_ports(forward, "end") == ["periods[0]/disc/disc:measure:cntn"]
    assert [m.id for m in forward.nodes[0].outputsMetadata] == boundary_ports(forward, "start")
    assert [m.id for m in forward.nodes[-1].inputsMetadata] == boundary_ports(forward, "end")
    # backward, the continuation value of the last period's last stage,
    # which the terminal value supplies
    backward = graph_named(collection, "backward")
    assert boundary_ports(backward, "start") == [
        "periods[0]/disc/disc:function:cntn:V",
    ]
    assert [m.id for n in backward.nodes[:1] for m in n.outputsMetadata] == boundary_ports(
        backward, "start"
    )
    # the joins of the backward graph, each an edge from the wire at the
    # entry perch of the later occurrence, its arrival perch or, for the
    # demonstration's consumption stage, which declares none, its decision
    # perch (AMD-MB-001 D8, the plan's P2), to the continuation wire of the
    # earlier one that the rule pairs with it: the one value of each side
    def entry(occurrence):
        period, key = occurrence
        return entry_perch(port_cons["periods"][int(period[8:-1])]["stages"][key])

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
    assert set(join_edges(backward)) == {
        (
            later,
            earlier,
            label,
            f"{later[1]}:function:{entry(later)}:{name}",
            f"{earlier[1]}:function:cntn:{name}",
        )
        for later, earlier, label in labeled
        for name in ("V",)
    }


class WireIdentity(SimpleNamespace):
    """A wire's identity as a join reads it, its field and its perch, which
    prints as its field, as an identity prints as its spelling."""

    def __str__(self):
        return str(self.field)


@dataclasses.dataclass(frozen=True, eq=False)
class WireRecord:
    """A wire's record as a join reads it, its identity, role and
    coordinates; each record is a key of its own, as a sort is."""

    identity: WireIdentity
    role: str
    coordinates: tuple



def _attribute_of(item, key):
    """The value of the attribute `key` of a node, a port or an edge, None
    where it has none."""
    return next((pair.value for pair in (getattr(item, "attrs", None) or []) if pair.key == key), None)


def test_a_trellis_s_initial_diagrams_are_drawn_when_asked_and_a_stage_s_always(port_cons):
    """Design pass 14 §7 (S-D30). The collection of a trellis holds its two
    builders graphs, and with `initial` its two initial diagrams after
    them, which the page asks for once its Initial view is chosen; a stage
    version holds its initial diagrams always and refuses `initial`."""
    assert [graph.id for graph in me.to_model_explorer(port_cons).graphs] == ["backward", "forward"]
    assert [graph.id for graph in me.to_model_explorer(port_cons, initial=True).graphs] == [
        "backward",
        "forward",
        "backward initial diagram",
        "forward initial diagram",
    ]
    with pytest.raises(TypeError):
        me.to_model_explorer(port_cons["periods"][2]["stages"]["cons"], initial=True)


def test_node_place_in_a_trellis_s_initial_diagram_names_the_occurrence_and_the_block(port_cons_view):
    """Design pass 14 §7, rule 6 (S-D21). In a trellis's initial diagram a
    field's node and a perch's layer stand in the occurrence their namespace
    opens with, a block's node is its own block, its id under the
    occurrence, and the occurrence's and the period's layers answer as the
    builders graph's do, so that the page's Details lists a selected field
    or block under its occurrence."""
    initial = graph_named(port_cons_view, "backward initial diagram")
    place = me.node_place
    field = next(
        node
        for node in initial.nodes
        if _attribute_of(node, "kind") == "field" and node.namespace.startswith("periods[0]/cons/")
    )
    block = next(
        node
        for node in initial.nodes
        if _attribute_of(node, "kind") == "block" and node.namespace == "periods[0]/cons"
    )
    assert place(port_cons_view, initial.id, field.id) == ("periods[0]/cons", "")
    assert place(port_cons_view, initial.id, block.id) == ("periods[0]/cons", block.id[len("periods[0]/cons/") :])
    assert place(port_cons_view, initial.id, field.namespace + me.LAYER_ID_ENDING) == ("periods[0]/cons", "")
    assert place(port_cons_view, initial.id, "periods[0]/cons" + me.LAYER_ID_ENDING) == ("periods[0]/cons", "")
    assert place(port_cons_view, initial.id, "periods[0]" + me.LAYER_ID_ENDING) == ("periods[0]", "")


def test_a_trellis_s_initial_diagram_joins_the_fields_of_its_occurrences(port_cons, port_cons_view):
    """Design pass 14 §7 (S-D12, S-D13). The trellis's initial diagram of a
    direction holds each occurrence's fields in perch layers under the
    occurrence's layer and its blocks in that layer, nothing else but the
    `outside` nodes of a restricted view; a join is one wire from the field
    it reads to the field it supplies, carrying the route's record as the
    builders graph's edge does: backward one wire for each route edge of
    the builders graph, forward one for each pair of each route; the two
    fields carry the wire's ports, and the reading port names the join."""
    collection = port_cons_view
    for direction in ("backward", "forward"):
        builders = graph_named(collection, direction)
        initial = graph_named(collection, f"{direction} initial diagram")
        nodes = {n.id: n for n in initial.nodes}
        assert len(nodes) == len(initial.nodes)
        kinds = {_attribute_of(n, "kind") for n in initial.nodes}
        assert kinds <= {"field", "block"}, kinds
        for node in initial.nodes:
            parts = node.namespace.split("/")
            if _attribute_of(node, "kind") == "field" and ":shck:" not in node.id:
                assert len(parts) == 3 and parts[2] in ("arvl", "dcsn", "cntn"), node.namespace
            else:
                # a block, or a shock, which belongs to no perch, in the occurrence's layer
                assert len(parts) == 2, node.namespace
        # the ports of every edge stand on its two nodes
        for node in initial.nodes:
            inputs = {m.id for m in node.inputsMetadata}
            for edge in node.incomingEdges:
                outputs = {m.id for m in nodes[edge.sourceNodeId].outputsMetadata}
                assert edge.sourceNodeOutputId in outputs and edge.targetNodeInputId in inputs
        routed = [
            (node, edge)
            for node in initial.nodes
            for edge in node.incomingEdges
            if _attribute_of(edge, "route") is not None
        ]
        given = [
            edge
            for node in builders.nodes
            for edge in node.incomingEdges
            if _attribute_of(edge, "route") is not None
        ]
        assert given, direction
        # a wire the builders graph draws once for each box that reads it is
        # one wire between two fields: the routes' edges by their two ports
        ports = {(edge.sourceNodeOutputId, edge.targetNodeInputId): edge for edge in given}
        if direction == "backward":
            # each route edge carries a value, which joins two fields
            assert len(routed) == len(ports), (len(routed), len(ports))
        else:
            assert len(routed) == sum(
                len(_attribute_of(edge, "route")["pairs"]) for edge in ports.values()
            )
        # a route joins a stage at its entry perch, the arrival perch where
        # the stage declares one and the decision perch else, as the
        # demonstration's consumption stage is entered (AMD-MB-001 D8, the
        # plan's P2)
        def entry(field):
            period, key = field.namespace.split("/")[:2]
            return entry_perch(port_cons["periods"][int(period[8:-1])]["stages"][key])

        for node, edge in routed:
            source = nodes[edge.sourceNodeId]
            assert _attribute_of(node, "kind") == "field" and _attribute_of(source, "kind") == "field"
            assert node.namespace.split("/")[2] == ("cntn" if direction == "backward" else entry(node))
            assert source.namespace.split("/")[2] == (entry(source) if direction == "backward" else "cntn")
            port = next(m for m in node.inputsMetadata if m.id == edge.targetNodeInputId)
            assert _attribute_of(port, "join"), port
            assert any(_attribute_of(edge, "route") == _attribute_of(e, "route") for e in given)
        # the layers: the periods, the occurrences with their stage, the perches;
        # an occurrence's stage is labeled by the bindings it holds, and the
        # fixture's occurrences are calibrated, methodized and configured
        # (decision SD-63)
        layers = initial.groupNodeAttributes
        assert layers["periods[2]"] == {} and layers["periods[2]/cons"] == {
            "stage": "cons calibrated methodized configured"
        }
        assert {ns.split("/")[2] for ns in layers if ns.count("/") == 2} <= {"arvl", "dcsn", "cntn"}

def test_a_join_carries_the_wires_its_route_pairs_and_leaves_a_reader_no_component_supplies_unpaired():
    """`_route_pairs` reads the wires a join carries from the route of the
    selection whose pairs hold it and adds no rule of its own (AMD-COMP-001
    §3.3): backward, each component of the route pairs the wire the source
    requires with the wire the destination supplies, named with the
    component's rule and status, a component without a supplied wire leaves
    its reader unpaired, and a reader two routes supply is unpaired as well;
    forward, the route's joint law supplies the arrival measure whose
    coordinates hold the join's field, two laws into one measure both
    supply it, and a route without a law leaves the measure unpaired."""
    from bellman.factory.connections import Component, FieldUse, Pair, Route

    def wire(name, role, perch, *fields):
        """A wire's record as a join reads it: its name, perch, role and
        coordinates."""
        points = tuple(SimpleNamespace(perch=perch, field=field) for field in fields)
        return WireRecord(WireIdentity(field=name, perch=perch), role, points)

    def graph(reads=(), writes=()):
        return SimpleNamespace(
            dom=SimpleNamespace(inside=reads), cod=SimpleNamespace(inside=writes)
        )

    def pair(key, field, key2, field2):
        return Pair(
            FieldUse(0, key, "cntn", field, None),
            FieldUse(0, key2, "arvl", field2, None),
            "authored",
            "periods[0].connectors[0]",
        )

    def route(pairs, components=(), law=None):
        return Route(
            source=(0, pairs[0].writing.key),
            branch=None,
            destination=(0, pairs[0].reading.key),
            source_fields=(),
            destination_fields=(),
            pairs=tuple(pairs),
            permutation=(),
            inverse=(),
            state="complete",
            compatibility="compatible",
            law=law,
            components=tuple(components),
            backward="compatible",
            status="certified",
            obligations=(),
            basis=(),
        )

    def join(key, field, key2, arrival):
        return me._Join(
            f"periods[0]/{key}", field, f"periods[0]/{key2}", arrival, f"{field} → {arrival}", ""
        )

    def component(required, supplied, role, status, rule):
        return Component(
            str(required.identity),
            None if supplied is None else str(supplied.identity),
            role,
            status,
            "",
            (),
            rule,
        )

    reads = [
        wire("V_w", "value", "cntn", "a_w"),
        wire("V_a", "value", "cntn", "a_w"),
        wire("V_h", "value", "cntn", "a_w"),
    ]
    writes = [
        wire("V", "value", "arvl", "a"),
        wire("V_a", "value", "arvl", "a"),
        wire("V_h", "value", "arvl", "a"),
    ]
    graphs = {"periods[0]/early": graph(reads=reads), "periods[0]/late": graph(writes=writes)}
    components = [
        component(reads[0], writes[0], "value", "compatible", "one wire per role"),
        component(reads[1], writes[1], "value", "incompatible", "equal name"),
        component(reads[2], None, "value", "not-established", ""),
    ]
    one = [join("early", "a_w", "late", "a")]
    selection = SimpleNamespace(routes=[route([pair("early", "a_w", "late", "a")], components)])
    supplied, undetermined = me._route_pairs(one, graphs, "backward", selection)
    assert {
        reader[1]: [(writer[1], [(s.label, s.rule, s.status) for s in feed]) for writer, feed in feeds.items()]
        for reader, feeds in supplied.items()
    } == {
        str(reads[0].identity): [(str(writes[0].identity), [("a_w → a", "one wire per role", "compatible")])],
        str(reads[1].identity): [(str(writes[1].identity), [("a_w → a", "equal name", "incompatible")])],
    }
    ((found, unpaired),) = undetermined
    assert found is one[0] and [sort.identity.field for sort in unpaired] == ["V_h"]
    # a value read at a continuation perch that two routes supply from two
    # different writers is unpaired as well
    value = wire("V", "value", "cntn", "a")
    keep, sell = wire("V", "value", "arvl", "a"), wire("V", "value", "arvl", "a")
    graphs = {
        "periods[0]/early": graph(reads=[value]),
        "periods[0]/keep": graph(writes=[keep]),
        "periods[0]/sell": graph(writes=[sell]),
    }
    selection = SimpleNamespace(
        routes=[
            route([pair("early", "a", "keep", "a")], [component(value, keep, "value", "compatible", "one wire per role")]),
            route([pair("early", "a", "sell", "a")], [component(value, sell, "value", "compatible", "one wire per role")]),
        ]
    )
    two = [join("early", "a", "keep", "a"), join("early", "a", "sell", "a")]
    _, undetermined = me._route_pairs(two, graphs, "backward", selection)
    assert [(found.target, len(unpaired)) for found, unpaired in undetermined] == [("periods[0]/sell", 1)]
    # forward, the laws of two routes into one arrival measure both supply it,
    # and a route without a law leaves the measure unpaired
    work, retire = wire("work", "measure", "cntn", "a"), wire("retire", "measure", "cntn", "a")
    arrival = wire(None, "measure", "arvl", "a")
    graphs = {
        "periods[0]/work": graph(writes=[work]),
        "periods[0]/retire": graph(writes=[retire]),
        "periods[0]/next": graph(reads=[arrival]),
    }
    selection = SimpleNamespace(
        routes=[
            route([pair("work", "a", "next", "a")], law=str(work.identity)),
            route([pair("retire", "a", "next", "a")], law=str(retire.identity)),
        ]
    )
    forward = [join("work", "a", "next", "a"), join("retire", "a", "next", "a")]
    supplied, undetermined = me._route_pairs(forward, graphs, "forward", selection)
    assert undetermined == []
    (feeds,) = supplied.values()
    assert {writer[1] for writer in feeds} == {str(work.identity), str(retire.identity)}
    assert all(s.rule == me.LAW_RULE for feed in feeds.values() for s in feed)
    lawless = SimpleNamespace(routes=[route([pair("work", "a", "next", "a")])])
    supplied, undetermined = me._route_pairs(forward[:1], graphs, "forward", lawless)
    assert supplied == {} and [sort.role for _, unpaired in undetermined for sort in unpaired] == ["measure"]


@needs_viewer
def test_a_trellis_whose_occurrence_refuses_a_direction_refuses_that_graph(elaborate_text):
    stage = elaborate_text(BACKWARD_REFUSED, "refused.bl")
    trellis = accrete(
        {"periods": [], "inter_connectors": []}, {"stages": {"only": stage}, "connectors": []}
    )
    backward, forward = me.to_model_explorer(trellis).graphs
    (node,) = backward.nodes
    assert node.label == "backward builders graph refused (not-constructed)"
    assert attributes(node)["refusal"].startswith("periods[0]/only: ")
    # the other direction is drawn
    assert len(forward.nodes) > 1


@needs_viewer
def test_a_trellis_is_built_once_for_its_two_files_and_opened_at_its_periods(
    port_cons, port_cons_view, tmp_path, monkeypatch, capsys
):
    import dacite
    from model_explorer import graph_builder as gb

    # the view already built stands for every build, which is counted
    built = []
    monkeypatch.setattr(
        me, "_trellis_collection", lambda *args: built.append(args) or port_cons_view
    )
    paths = me.write_model_explorer(port_cons, tmp_path)
    assert len(built) == 1
    assert [p.name for p in paths] == ["trellis.graph.json", "trellis.edge-overlays.json"]
    graph_text, overlays_text = (p.read_text(encoding="utf-8") for p in paths)
    assert json.loads(graph_text) == as_json(port_cons_view)
    assert dacite.from_dict(gb.GraphCollection, json.loads(graph_text)) == in_viewer_classes(
        port_cons_view
    )
    # the overlays file paints edges of the two graphs alone, with no label
    overlays = dacite.from_dict(gb.EdgeOverlaysData, json.loads(overlays_text))
    edges = {
        (e.sourceNodeId, n.id)
        for g in port_cons_view.graphs
        for n in g.nodes
        for e in n.incomingEdges
    }
    painted = [(e.sourceNodeId, e.targetNodeId) for o in overlays.overlays for e in o.edges]
    assert painted and set(painted) <= edges
    assert all(e.label is None for o in overlays.overlays for e in o.edges)
    # `explore` opens the graph `backward` at its six periods, located on the
    # first period after the terminal one
    served = []
    monkeypatch.setattr(
        me, "serve", lambda *args, **kwargs: served.append(kwargs) or "http://localhost:0/"
    )
    monkeypatch.setattr(me.webbrowser, "open", lambda url, *args, **kwargs: None)
    me.explore(port_cons, folder=tmp_path, open_browser=True)
    ((kwargs,),) = [served]
    assert kwargs["layers"] == tuple(f"periods[{h}]" for h in range(5, -1, -1))
    assert kwargs["located"] == "periods[1]"
    assert kwargs["graph_id"] == "backward" and len(built) == 2
    capsys.readouterr()


@needs_viewer
def test_a_period_layer_shows_the_age_the_trellis_registry_gives(cons):
    # a trellis of one period whose registry's calibration gives the last age,
    # as a trellis a recipe assembles does; `periods[0]` is the last period
    trellis = accrete(
        {"periods": [], "inter_connectors": [], "registry": {"calibration": {"last_age": 64}}},
        {"stages": {"consumption": cons}, "connectors": []},
    )
    for graph in me.to_model_explorer(trellis).graphs:
        layers = graph.groupNodeAttributes
        # the period's index stands in the layer's name and is not written
        # again
        assert layers["periods[0]"] == {"age": "64"}
        # the occurrence's layer is named by its key and shows its stage
        assert layers["periods[0]/consumption"] == {"stage": "cons"}
    plain = accrete(
        {"periods": [], "inter_connectors": []},
        {"stages": {"consumption": cons}, "connectors": []},
    )
    for graph in me.to_model_explorer(plain).graphs:
        assert graph.groupNodeAttributes["periods[0]"] == {}


# --- the lines of the proposal of the minimal view, 30 September 2026 ---


@needs_viewer
def test_line_2_the_where_rows_stand_once_on_the_layer_of_their_builder(
    house_choice, ret_choice, sa_savings
):
    # the local abbreviations of the rules, which the cards of a builder's
    # primitives repeat, stand once on the builder's layer and on no node
    for stage in (house_choice, ret_choice, sa_savings):
        for graph in builders_graphs(me.to_model_explorer(stage)):
            word = "bwd" if graph.id == "backward" else "fwd"
            layers = graph.groupNodeAttributes
            assert not [n.id for n in graph.nodes if numbered(attributes(n), "where")]
            for namespace, shown in layers.items():
                rows = numbered(shown, "where")
                if "/" in namespace:
                    # a sub-builder's layer repeats no row of its builder
                    assert not rows, namespace
                    continue
                # the rows of the `Where` section of the builder's own card
                card = str(getattr(stage.builder, word)[namespace].denote())
                assert rows == [
                    one_line(row)
                    for heading, held in printed_sections(card)
                    if heading == "Where"
                    for row in held
                ], namespace
            # every row a primitive's card prints under `Where` stands on the
            # layer of its builder, apart from the columns it is aligned in
            for box in operator_boxes(stage, graph.id):
                card = str(me.piece_handle(stage, graph.id, box).denote())
                builder = {
                    spaced(row) for row in numbered(layers[box_identity(box).block], "where")
                }
                for heading, held in printed_sections(card):
                    if heading == "Where":
                        assert {spaced(one_line(row)) for row in held} <= builder, box.name
    # the keep branch's two continuation coordinates, which the derivative
    # lines of the marginal block of `marginals_house_choice.bl` name, stand
    # once under the law's own row, on the stage bound with its methods file
    # (decision MB-U37)
    bound = branching_stage("house_choice")
    bound.methodize(ROOT / "applications/housing-frictions/declaration/stages/house_choice/methods.yml")
    layers = graph_named(me.to_model_explorer(bound), "backward").groupNodeAttributes
    assert numbered(layers["cntn_to_dcsn"], "where") == [
        "𝑔_keep≻    : ℝ₊₊ × ℝ₊₊ → ℝ₊₊ × ℝ₊₊,  𝑔_keep≻(m_f, m_h) = 𝑔≻(m_f, m_h, keep)",
        "(w_kp, h_kp) = 𝑔_keep≻(m_f, m_h)",
        "𝑔_adjust≻  : ℝ₊₊ × ℝ₊₊ → ℝ₊₊,  𝑔_adjust≻(m_f, m_h) = 𝑔≻(m_f, m_h, adjust)",
    ]


def test_line_3_lines_name_the_file_and_the_numbers_of_the_lines_the_card_quotes(
    cons, house_choice
):
    def lines(stage, direction, name):
        """The attribute `lines` of the primitive of this name, or None."""
        box = box_named(stage, direction, name)
        return me.box_attributes(stage, direction, box).get("lines")

    # neither the address, which the id's first segment names, nor the quoted
    # text, which the rules restate
    assert lines(cons, "backward", "cntn_to_dcsn:Aggregation") == "cons.bl 21"
    assert lines(cons, "backward", "policy.cons_choice:Pullback") == "cons.bl 35"
    # a run of consecutive lines by its first and last, the others after a
    # comma
    assert lines(house_choice, "backward", "cntn_to_dcsn:Pullback:keep") == (
        "house_choice.bl 18–19, 22"
    )
    # an expectation quotes the declaration of its distribution as well
    assert lines(house_choice, "backward", "dcsn_to_arvl.value:Expectation:1") == (
        "house_choice.bl 9, 31"
    )
    # an evaluation of a builder quotes no line and has no `lines`
    assert lines(cons, "backward", "policy:Evaluation") is None
    # the numbers are those the printed `Source` section begins its rows
    # with, read from the card's record (`cards.source_lines`)
    for stage in (cons, house_choice):
        for direction in DIRECTIONS:
            for box in operator_boxes(stage, direction):
                record = me.piece_handle(stage, direction, box).denote()
                quoted = quoted_lines(str(record))
                attrs = me.box_attributes(stage, direction, box)
                assert expanded(attrs.get("lines")) == quoted, box.name
                if quoted is not None:
                    file, numbers = quoted
                    assert source_lines(record) == tuple(SourceLine(file, n) for n in numbers)


def test_line_4_the_region_of_a_rule_stands_on_the_row_of_its_rule(cons, house_choice):
    aggregation = box_named(house_choice, "backward", "cntn_to_dcsn:Aggregation")
    region = "on (m_f, m_h) ∈ ℝ₊₊ × ℝ₊₊"
    # the card sets each region on a row of its own, under its rule
    card = str(me.piece_handle(house_choice, "backward", aggregation).denote())
    (rows,) = [held for heading, held in printed_sections(card) if heading == "Rule"]
    assert [one_line(row) for row in rows][1::2] == [region]
    # the view writes it after its rule and two spaces, as one rule
    attrs = me.box_attributes(house_choice, "backward", aggregation)
    assert numbered(attrs, "rule") == [
        f"𝑉 = (𝑉_kp≻(𝑔_keep≻(m_f, m_h)), 𝑉_adj≻(𝑔_adjust≻(m_f, m_h)))[𝑑]  {region}",
    ]
    # a region the card sets at the right margin of its rule's line stands
    # after the same two spaces
    pullback = box_named(cons, "backward", "policy.cons_choice:Pullback")
    assert me.box_attributes(cons, "backward", pullback)["rule"] == (
        "𝑐(𝑚_d≻(a)) = 𝑐≻(a)  on 𝑚_d≻(Xa)"
    )
    # no rule of any primitive is a region alone
    for stage in (cons, house_choice):
        for direction in DIRECTIONS:
            for box in operator_boxes(stage, direction):
                rules = numbered(me.box_attributes(stage, direction, box), "rule")
                assert not [rule for rule in rules if rule.startswith("on ")], box.name


def test_line_5_an_evaluation_lists_its_typing_rows_and_no_rule_of_the_box_before_it(
    cons, house_choice, cons_obs, cons_methods_only
):
    def rules(stage, name):
        """The rules the node of the backward primitive `name` lists."""
        box = box_named(stage, "backward", name)
        return numbered(me.box_attributes(stage, "backward", box), "rule")

    assert rules(cons, "cntn_to_dcsn:Evaluation") == ["𝑉 : Xm → [−∞, ∞)", "D_{m_d}𝑉(m_d) = 𝑑𝑢(𝑐(m_d))"]
    assert rules(cons, "policy:Evaluation") == ["𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)"]
    assert rules(house_choice, "cntn_to_dcsn:Evaluation") == [
        "𝑉 : ℝ₊₊ × ℝ₊₊ → ℝ",
        "𝑑𝑉_f : ℝ₊₊ × ℝ₊₊ → ℝ₊₊",
        "𝑑𝑉_h : ℝ₊₊ × ℝ₊₊ → ℝ₊₊",
    ]
    # the evaluation's card spells the abbreviation of the region of the rule
    # it repeats otherwise than the card of the box before it, since its
    # record does not define that abbreviation; the rule is known as a copy
    # by its record, not by its printing
    assert rules(cons_obs, "policy:Evaluation") == ["𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)"]
    for name, region in (
        ("policy:Evaluation", "on 𝑚_d≻(𝐴≻,𝑝𝑜𝑙𝑖𝑐𝑦)"),
        ("policy.cons_choice:Pullback", "on 𝑚_d≻(A≻,policy)"),
    ):
        card = str(
            me.piece_handle(cons_obs, "backward", box_named(cons_obs, "backward", name)).denote()
        )
        assert printed_rules(card)[0].endswith(region), name
    evaluations = 0
    for stage in (cons, house_choice, cons_obs):
        for direction in DIRECTIONS:
            for box in operator_boxes(stage, direction):
                if box_identity(box).kind != "Evaluation":
                    continue
                evaluations += 1
                # the kernel of an evaluation is the identity
                assert str(kernel(stage, box)).startswith("identity at "), box.name
                # the rules its record holds and no box that writes a wire it
                # reads holds, each a membership that types an output
                earlier = {
                    rule
                    for other in boxes_before(stage, direction, box)
                    for wire in me.piece_handle(stage, direction, other).denote().outputs
                    for rule in wire.rules
                }
                record = me.piece_handle(stage, direction, box).denote()
                own = [rule for wire in record.outputs for rule in wire.rules]
                kept = [rule for rule in own if rule not in earlier]
                assert len(kept) < len(own), box.name
                assert all(S.membership_parts(rule.statement) is not None for rule in kept)
                # one row each, among the rows the evaluation's card prints,
                # `name : carrier`
                listed = [
                    spaced(rule)
                    for rule in numbered(me.box_attributes(stage, direction, box), "rule")
                ]
                assert len(listed) == len(kept), box.name
                assert set(listed) <= set(printed_rules(str(record))), box.name
                assert all(" : " in rule for rule in listed), box.name
    assert evaluations > 0
    # the method rows of an evaluation within which a method is bound stay
    evaluation = box_named(cons_methods_only, "backward", "policy:Evaluation")
    attrs = me.box_attributes(cons_methods_only, "backward", evaluation)
    assert {key: attrs[key] for key in ("rule", "method", "handler")} == {
        "rule": "𝑐 : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)",
        "method": "!egm",
        "handler": "cons-port:egm",
    }


@needs_viewer
def test_line_7_a_builders_layer_lists_the_parameters_its_primitives_read_and_every_setting(
    cons, cons_configured, house_choice, sa_savings
):
    # each parameter with its declared set, as `stage.par` prints it; the
    # decision builder reads ρ through 𝑢 and 𝑑𝑢, and the identity reads none
    layers = graph_named(me.to_model_explorer(cons), "backward").groupNodeAttributes
    assert layers["cntn_to_dcsn"]["parameter"] == str(cons.par["ρ"]) == "ρ : [1, inf), unbound"
    assert layers["policy"]["parameter"] == str(cons.par["ρ"])
    assert not numbered(layers["dcsn_to_arvl"], "parameter")
    # a symbolic version binds no setting
    assert not [namespace for namespace, shown in layers.items() if numbered(shown, "setting")]
    # read through a law of motion and a distribution, in the file's order
    layers = graph_named(me.to_model_explorer(house_choice), "backward").groupNodeAttributes
    assert numbered(layers["dcsn_to_arvl"], "parameter") == [
        "r : ℝ₊, unbound",
        "W : ℝ₊₊, unbound",
        "η_lo : ℝ₊₊, unbound",
        "η_hi : ℝ₊₊, unbound",
    ]
    # the calibrated, methodized and configured version: the value from
    # `stage.par`, and every setting on every builder's layer as
    # `stage.settings` prints it, a setting no method names among them
    bound = me.to_model_explorer(cons_configured)
    layers = graph_named(bound, "backward").groupNodeAttributes
    assert layers["cntn_to_dcsn"]["parameter"] == str(cons_configured.par["ρ"])
    assert layers["cntn_to_dcsn"]["parameter"] == "ρ = 6.0 : [1, inf)"
    settings = [str(cons_configured.settings[name]) for name in cons_configured.settings]
    assert "n_k = 800" in settings
    for graph in builders_graphs(bound):
        for namespace, shown in graph.groupNodeAttributes.items():
            assert numbered(shown, "setting") == settings, namespace
    # the method bound at a builder lists no setting of its own there
    forward = graph_named(bound, "forward")
    assert forward.groupNodeAttributes["arvl_to_dcsn"]["method"] == "!deterministic"
    # a sub-builder's layer holds its signature alone
    backward = graph_named(me.to_model_explorer(sa_savings), "backward")
    for namespace, shown in backward.groupNodeAttributes.items():
        if "/" in namespace:
            assert list(shown) == ["inputs", "outputs"], namespace


@needs_viewer
def test_line_8_the_policy_layer_lists_the_definition_of_each_feasible_set_its_policy_names(
    cons, adjuster_saving, house_choice
):
    # the correspondence the policy of `cons.bl` is chosen from, as its line
    # 11 declares it
    layers = graph_named(me.to_model_explorer(cons), "backward").groupNodeAttributes
    assert layers["policy"]["feasible set"] == "Γ(x : ℝ₊₊) := (0, x]"
    source = (ROOT / "applications/portfolio-choice/declaration/stages/cons/cons.bl").read_text(
        encoding="utf-8")
    assert source.splitlines()[10] == layers["policy"]["feasible set"]
    assert [namespace for namespace, shown in layers.items() if "feasible set" in shown] == [
        "policy"
    ]
    # a policy of two controls names two
    backward = graph_named(me.to_model_explorer(adjuster_saving), "backward")
    shown = backward.groupNodeAttributes["policy"]
    assert numbered(shown, "feasible set") == [
        "Γ_c(x : ℝ₊₊) := (0, x]",
        "Γ_h(x : ℝ₊) := (0, x/(1 + τ)]",
    ]
    # a choice over a finite set names no correspondence
    backward = graph_named(me.to_model_explorer(house_choice), "backward")
    shown = backward.groupNodeAttributes["policy"]
    assert not numbered(shown, "feasible set")


@needs_viewer
def test_line_12_each_occurrences_policy_ends_at_an_outputs_node_inside_its_layer(
    port_cons_view,
):
    backward, forward = builders_graphs(port_cons_view)
    nodes = {n.id: n for n in backward.nodes}
    # the wire that leaves the trellis, at an `end` node, is the value its
    # first stage in time exports: its decision value, since the portfolio
    # stage declares no arrival perch (28 October 2026)
    given = [n for n in backward.nodes if attributes(n).get("kind") == "end"]
    assert boundary_ports(backward, "end") == [
        "periods[5]/port/port:function:dcsn:V",
    ]
    assert {occurrence_of(e.sourceNodeId) for n in given for e in n.incomingEdges} == {
        ("periods[5]", "port")
    }
    # each occurrence's policy ends at a node `Outputs` in its own layer,
    # from the occurrence's own evaluation
    for h in range(6):
        for key, control in (("port", "ς"), ("cons", "c")):
            address = f"periods[{h}]/{key}"
            own = nodes[f"{address}/GraphOutputs"]
            assert (own.label, own.namespace, own.style) == ("Outputs", address, me.NODE_STYLE)
            assert [m.id for m in own.inputsMetadata] == [
                f"{address}/policy:Evaluation:{control}:result"
            ]
            assert [e.sourceNodeId for e in own.incomingEdges] == [f"{address}/policy:Evaluation"]
        # `disc` chooses no control
        assert f"periods[{h}]/disc/GraphOutputs" not in nodes
    # the forward graph gives no policy
    assert not [n.id for n in forward.nodes if n.id.endswith("/GraphOutputs")]


@needs_viewer
def test_line_14_the_view_of_a_trellis_opens_located_on_the_first_period_after_the_terminal_one(
    cons, port_cons, port_cons_view, tmp_path, monkeypatch, capsys
):
    # the page's state selects the layer named and fits the window to it
    paths = me._write_view(port_cons_view, tmp_path / "view")
    with answering(me.VIEWER_HEALTH) as port:
        url = me.serve(paths[0], port=port, layers=("periods[1]",), located="periods[1]")
        fitted = me.serve(paths[0], port=port)
    (pane,) = json.loads(unquote(url.partition("?data=")[2]))["uiState"]["paneStates"]
    assert pane["selectedNodeId"] == "periods[1]___group___"
    (pane,) = json.loads(unquote(fitted.partition("?data=")[2]))["uiState"]["paneStates"]
    assert pane["selectedNodeId"] == ""
    # `explore` locates a trellis on `periods[1]`, and a stage, or a trellis
    # of one period, on nothing
    served = []
    monkeypatch.setattr(
        me, "serve", lambda *args, **kwargs: served.append(kwargs) or "http://localhost:0/"
    )
    monkeypatch.setattr(me.webbrowser, "open", lambda url, *args, **kwargs: None)
    build = me._trellis_collection
    monkeypatch.setattr(
        me,
        "_trellis_collection",
        lambda graph_builder, trellis, *selection: (
            port_cons_view if trellis is port_cons else build(graph_builder, trellis, *selection)
        ),
    )
    one = accrete(
        {"periods": [], "inter_connectors": []},
        {"stages": {"consumption": cons}, "connectors": []},
    )
    for view, folder in ((port_cons, "trellis"), (cons, "stage"), (one, "one")):
        me.explore(view, folder=tmp_path / folder, open_browser=True)
    assert [kwargs["located"] for kwargs in served] == [me.LOCATED_PERIOD, None, None]
    assert me.LOCATED_PERIOD == "periods[1]"
    capsys.readouterr()


def edges_of(graph):
    """Every edge of a graph as the node it leaves, the node it enters and
    the wire it carries, in the order of the nodes and of their edges."""
    return [
        (e.sourceNodeId, n.id, e.targetNodeInputId) for n in graph.nodes for e in n.incomingEdges
    ]


@needs_viewer
def test_the_initial_diagrams_stand_first_with_the_fields_as_nodes_in_their_perches(
    cons, sa_savings, cons_methods_only
):
    from model_explorer import graph_builder as gb

    from bellman.syntax.source import to_source

    collection = me.to_model_explorer(cons)
    assert [g.id for g in collection.graphs] == STAGE_GRAPHS
    assert me.INITIAL_IDS == {
        "backward": "backward initial diagram",
        "forward": "forward initial diagram",
    }
    # the perches in the order a direction reads them, the order of the layers
    assert me.PERCH_ORDER == {
        "forward": ("arvl", "dcsn", "cntn"),
        "backward": ("cntn", "dcsn", "arvl"),
    }
    for stage in (cons, sa_savings, cons_methods_only):
        for direction in DIRECTIONS:
            graph = graph_named(me.to_model_explorer(stage), me.INITIAL_IDS[direction])
            hypergraph = graph_of(stage, "initial", direction)
            blocks = [box for box in hypergraph.boxes if not is_wiring(box)]
            sorts = {str(identity): sort for identity, sort in drawn_sorts(hypergraph).items()}
            names = drawing_arguments(stage, hypergraph)["wire_names"]
            written = {str(ob.identity): b.name for b in blocks for ob in b.cod.inside}
            read = {str(ob.identity) for b in blocks for ob in b.dom.inside}
            nodes = {n.id: n for n in graph.nodes}
            # the fields are the nodes, then the blocks; no `Inputs` and no
            # `Outputs`, since a field no block writes is one the diagram
            # takes and a field no block reads one it gives
            fields = [n for n in graph.nodes if attributes(n).get("kind") == "field"]
            block_nodes = [n for n in graph.nodes if attributes(n).get("kind") == "block"]
            assert [n.id for n in graph.nodes] == [n.id for n in fields + block_nodes]
            assert not set(nodes) & set(me.BOUNDARY_IDS)
            # one node per field wire at the block grain, the wires the
            # diagram takes and the wires its blocks write; the wires inside
            # the blocks' bubbles, which `drawn_sorts` reads as well, are none
            taken = [str(ob.identity) for ob in hypergraph.dom.inside]
            assert {n.id for n in fields} == set(taken) | set(written) <= set(sorts)
            assert [n.id for n in block_nodes] == [b.name for b in blocks]
            # a field stands in the layer of its perch, a shock outside the
            # layers, the perches in the order the direction reads them and
            # the shocks after them
            perches = [n.namespace for n in fields]
            order = [p for p in me.PERCH_ORDER[direction] if p in perches] + [""]
            assert perches == sorted(perches, key=order.index)
            # the layers are the perches that hold a field, each with no
            # attribute, on the first step of the ice with navy, every layer
            # and the root laid out left to right
            assert list(graph.groupNodeAttributes) == [p for p in order if p]
            assert all(shown == {} for shown in graph.groupNodeAttributes.values())
            assert graph.groupNodeConfigs == [
                me._layer_config(".*", gb.LayoutDirection.LEFT_RIGHT, me.LAYER_COLORS["stage"])
            ]
            for node in fields:
                sort = sorts[node.id]
                perch = sort.identity.perch
                assert node.namespace == (perch if perch in ("arvl", "dcsn", "cntn") else "")
                # labeled as the drawing labels the wire, white with a navy
                # border
                assert node.label == wire_label(sort, names.get(sort.identity))
                assert node.style == me.NODE_STYLE
                assert node.style.backgroundColor == me.PALETTE["--bf-face"]
                # the field's rows, each a fact of the fields table
                shown = attributes(node)
                assert shown["kind"] == "field"
                assert shown.get("role") == (sort.role or None)
                assert shown.get("set") == (
                    None if sort.domain is None else to_source(sort.domain)
                )
                if node.namespace:
                    assert shown["perch"] == perch and "edge" not in shown
                else:
                    assert "perch" not in shown and shown["edge"]
                assert re.fullmatch(r"\S+\.bl \d+", shown["lines"]), node.id
                # an edge from the block that writes the field, none where
                # the diagram takes it; the wire's port on each side that has
                # an edge
                if node.id in written:
                    assert [
                        (e.sourceNodeId, e.sourceNodeOutputId, e.targetNodeInputId)
                        for e in node.incomingEdges
                    ] == [(written[node.id],) + (node.id,) * 2]
                    assert [m.id for m in node.inputsMetadata] == [node.id]
                else:
                    assert node.incomingEdges == [] and node.inputsMetadata == []
                assert [m.id for m in node.outputsMetadata] == (
                    [node.id] if node.id in read else []
                )
                for port in node.inputsMetadata + node.outputsMetadata:
                    assert not {"field", "type"} & set(attributes(port))
                    assert set(attributes(port)) <= {
                        "__tensor_tag",
                        "label",
                        "perch",
                        "role",
                        "set",
                    }
            for box in blocks:
                node = nodes[box.name]
                assert (node.label, node.namespace) == (box.name, "")
                assert node.style == me.NODE_STYLE
                # the ports are the wires of the block's header, the fields
                # it reads and writes, a control among none of them
                reads = [str(ob.identity) for ob in box.dom.inside]
                writes = [str(ob.identity) for ob in box.cod.inside]
                assert [m.id for m in node.inputsMetadata] == reads
                assert [m.id for m in node.outputsMetadata] == writes
                # an edge from the node of each field the block reads
                assert [
                    (e.sourceNodeId, e.sourceNodeOutputId, e.targetNodeInputId)
                    for e in node.incomingEdges
                ] == [(w, w, w) for w in reads]
                # the diagram carries no method
                assert not {"method", "handler"} & set(attributes(node))
            # every input port has its edge
            for node in graph.nodes:
                assert {m.id for m in node.inputsMetadata} == {
                    e.targetNodeInputId for e in node.incomingEdges
                }, node.id
    # the block's attributes, from its record: its kind, its header as the
    # file writes it, its statements as the card quotes them with their line
    # numbers, and its lines, the header's line first
    backward = graph_named(collection, "backward initial diagram")
    nodes = {n.id: n for n in backward.nodes}
    shown = attributes(nodes["cntn_to_dcsn"])
    record = cons.initial.backward["cntn_to_dcsn"].denote()
    assert list(shown) == ["kind", "header", "statement 1", "statement 2", "lines"]
    assert shown["kind"] == "block"
    assert shown["header"] == record.header[0]
    assert shown["header"] == (
        "(V[>] : [-inf, inf) @ !vlu, c) : !cntn -> "
        "(V : [-inf, inf) @ !vlu) : !dcsn"
    )
    source = (ROOT / "applications/portfolio-choice/declaration/stages/cons/cons.bl").read_text(
        encoding="utf-8")
    assert source.splitlines()[20] == f"[id=cntn_to_dcsn, {shown['header']}] {{"
    assert numbered(shown, "statement") == [
        "21  V        = 𝑢(c) + V[>]  :: [id=value]",
        "22  D_{m_d}V = 𝑑𝑢(c)        :: [id=marginal]",
    ]
    assert shown["lines"] == "cons.bl 20–22"
    # a `!doc` line, which forms no operation, is still a statement of its
    # block
    statements = numbered(attributes(nodes["policy"]), "statement")
    assert statements[0].endswith("[id=optimality, !doc]")
    assert attributes(nodes["policy"])["lines"] == "cons.bl 31–35"
    # a port of a field: the label the drawing prints, its perch, its role
    # and its declared set as the fields table prints it; no `type` and no
    # `field`, since the field's node carries the name
    (port,) = nodes["cntn_to_dcsn"].inputsMetadata
    assert attributes(port) == {
        "__tensor_tag": "V≻",
        "label": "V≻",
        "perch": "cntn",
        "role": "value",
        "set": "[-inf, inf)",
    }
    assert attributes(port)["set"] == to_source(cons.fields().get("cons:cntn:V").domain)
    # the field's node: its rows in the order the fields table prints them,
    # the line of the header that first lists the field last
    assert attributes(nodes["cons:cntn:V"]) == {
        "kind": "field",
        "perch": "cntn",
        "role": "value",
        "set": "[-inf, inf)",
        "lines": "cons.bl 21",
    }
    # the control `c` is listed by the header of the forward block at line
    # 17, among the inputs it is read at, before the policy writes it at line
    # 31
    assert attributes(nodes["cons:dcsn:c"])["lines"] == "cons.bl 17"
    lines = source.splitlines()
    assert lines[16].startswith("[id=dcsn_to_cntn, (m_d, c : !ctrl")
    assert lines[30].startswith("[id=policy, (V[>]")
    # the forward diagram: the block `dcsn_to_cntn` on its state and no port
    # for the control its header names
    forward = graph_named(collection, "forward initial diagram")
    assert attributes({n.id: n for n in forward.nodes}["dcsn_to_cntn"]) == {
        "kind": "block",
        "header": "(m_d, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : Xa) : !cntn",
        "statement": "18  a = m_d - c",
        "lines": "cons.bl 17–18",
    }
    # a shock belongs to no perch: its node stands outside the layers, and
    # its row `edge` is the pair of perches the fields table draws it on
    forward = graph_named(me.to_model_explorer(sa_savings), "forward initial diagram")
    shock = {n.id: n for n in forward.nodes}["sa_savings:shck:Ψ"]
    assert (shock.namespace, shock.label) == ("", "Ψ")
    assert attributes(shock) == {
        "kind": "field",
        "edge": "∼→≻",
        "role": "shock",
        "set": "ℝ₊₊",
        "lines": "sa_savings.bl 22",
    }
    assert sa_savings.fields().edges["sa_savings:shck:Ψ"] == ("dcsn", "cntn")
    assert [e.sourceNodeId for e in forward.nodes[-1].incomingEdges] == [
        "sa_savings:dcsn:m_d",
        "sa_savings:shck:Ψ",
    ]
    # the view opens on the backward builders graph, not on the first graph
    assert me.OPENED_GRAPH == "backward"


@needs_viewer
def test_the_field_diagrams_of_cons_read_the_fields_through_the_blocks(cons):
    # the forward diagram of
    # `applications/portfolio-choice/declaration/stages/cons/cons.bl`: the
    # three states, one in each perch's layer, from arrival to continuation,
    # and the two blocks outside the layers
    collection = me.to_model_explorer(cons)
    forward = graph_named(collection, "forward initial diagram")
    assert [(n.id, n.namespace, n.label) for n in forward.nodes] == [
        ("cons:arvl:m", "arvl", "m≺"),
        ("cons:dcsn:m_d", "dcsn", "m_d"),
        ("cons:cntn:a", "cntn", "a≻"),
        ("arvl_to_dcsn", "", "arvl_to_dcsn"),
        ("dcsn_to_cntn", "", "dcsn_to_cntn"),
    ]
    assert list(forward.groupNodeAttributes) == ["arvl", "dcsn", "cntn"]
    # the edges read m → arvl_to_dcsn → m_d → dcsn_to_cntn → a, each
    # carrying the wire of the field at its end
    assert sorted(edges_of(forward)) == sorted(
        [
            ("cons:arvl:m", "arvl_to_dcsn", "cons:arvl:m"),
            ("arvl_to_dcsn", "cons:dcsn:m_d", "cons:dcsn:m_d"),
            ("cons:dcsn:m_d", "dcsn_to_cntn", "cons:dcsn:m_d"),
            ("dcsn_to_cntn", "cons:cntn:a", "cons:cntn:a"),
        ]
    )
    # the backward diagram: the layers from continuation to arrival; the
    # policy writes the control `c` at the decision perch, and the
    # continuation value `V≻` is read by the decision block and the policy
    backward = graph_named(collection, "backward initial diagram")
    assert list(backward.groupNodeAttributes) == ["cntn", "dcsn", "arvl"]
    nodes = {n.id: n for n in backward.nodes}
    assert [n.id for n in backward.nodes if n.namespace == "dcsn"] == [
        "cons:dcsn:V",
        "cons:dcsn:c",
    ]
    c = nodes["cons:dcsn:c"]
    assert (c.label, attributes(c)["role"]) == ("c", "control")
    assert [e.sourceNodeId for e in c.incomingEdges] == ["policy"]
    value = nodes["cons:cntn:V"]
    assert (value.label, value.incomingEdges, value.inputsMetadata) == ("V≻", [], [])
    assert sorted(t for s, t, _ in edges_of(backward) if s == "cons:cntn:V") == [
        "cntn_to_dcsn",
        "policy",
    ]


@needs_viewer
def test_the_shorter_port_label_waits_behind_the_switch(cons, monkeypatch):
    # off, the default, the recorded form, which the drawing prints: a
    # result wire by the expression it denotes
    assert me.SHORT_LABELS is False
    backward = graph_named(me.to_model_explorer(cons), "backward")
    nodes = {n.id: n.label for n in backward.nodes}
    labels = {m.id: attributes(m)["label"] for n in backward.nodes for m in n.outputsMetadata}
    assert labels["cntn_to_dcsn:Aggregation:V:result"] == "m_d ↦ 𝑢(𝑐(m_d)) + 𝑉≻(𝑔(m_d, 𝑐(m_d)))"
    # on, the proposed form, line 6 of the study of 30 September; the
    # switch changes no node's label
    monkeypatch.setattr(me, "SHORT_LABELS", True)
    backward = graph_named(me.to_model_explorer(cons), "backward")
    assert {n.id: n.label for n in backward.nodes} == nodes
    labels = {m.id: attributes(m)["label"] for n in backward.nodes for m in n.outputsMetadata}
    assert labels["cntn_to_dcsn:Aggregation:V:result"] == "𝑉(m_d)"
    assert labels["dcsn_to_arvl:Aggregation:V:result"] == "𝑉(m)"
    assert labels["policy:Evaluation:c:result"] == "𝑐(m_d)"
    # a result that carries a set of candidate policies keeps its
    # expression, and a pulled-back wire, no result, keeps its name
    assert labels["policy.cons_choice:Pullback:c:result"].startswith("{f ∈ {c ∈ (Xm → ℝ₊₊)")
    assert labels["cons:function:cntn:V:g"] == "𝑉≻(𝑔(m_d, 𝑐(m_d)))"


@needs_viewer
def test_a_backward_join_names_the_rule_that_paired_its_wire(port_cons_view):
    backward, forward = builders_graphs(port_cons_view)
    rules = {}
    for node in backward.nodes:
        for port in node.inputsMetadata:
            shown = attributes(port)
            if "join" in shown:
                rules[port.id] = shown["paired by"]
    assert rules and set(rules.values()) <= set(me.PAIRING_RULES)
    assert me.PAIRING_RULES == ("one wire per role", "equal name")
    # the value, one wire of its role on each side
    assert rules["periods[1]/cons/cons:function:cntn:V"] == "one wire per role"
    # a forward join carries a measure along the identification and names
    # no rule
    for node in forward.nodes:
        for port in node.inputsMetadata:
            assert "paired by" not in attributes(port)


def test_the_two_namespaces_export_explore_and_write_model_explorer_and_not_serve():
    import bellman.stage
    import bellman.trellis
    for namespace in (bellman.stage, bellman.trellis):
        assert (namespace.explore, namespace.write_model_explorer) == (me.explore, me.write_model_explorer)
        # `serve` stays a function of the module, which `explore` calls
        assert "serve" not in namespace.__all__


@needs_viewer
def test_a_restricted_trellis_view_holds_the_occurrences_selected_and_marks_the_joins_that_leave_them(
    port_cons, port_cons_view
):
    """The restriction `periods 0–1, stages cons` of the model interface's
    specification 0.3, §3.1: the view holds the two consumption occurrences
    and their nodes, which the whole view holds under the same ids, and
    every join that leaves them is marked by an `outside` node at the
    graph's root, labeled with the occurrence outside the view, whose port
    carries the join's label and that occurrence (design pass 10 §6)."""
    view = me.to_model_explorer(port_cons, periods=range(0, 2), stages=["cons"])
    assert view.label == port_cons_view.label
    for graph in view.graphs:
        occurrences = {ns for ns in graph.groupNodeAttributes if ns.count("/") == 1}
        assert occurrences == {"periods[0]/cons", "periods[1]/cons"}, graph.id
        whole = {node.id for node in graph_named(port_cons_view, graph.id).nodes}
        assert {
            node.id for node in graph.nodes if attributes(node).get("kind") != "outside"
        } <= whole

    def marks(graph_id, side):
        """Each port of the `outside` nodes of a graph of the view on
        `side`, with its join, its outside occurrences and the node's
        label and target."""
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

    assert marks("backward", "outputsMetadata") == [
        (f"periods[{h}]/cons/cons:function:cntn:{wire}", "a", *[f"periods[{h}]/disc"] * 3)
        for h in (1, 0)
        for wire in ("V",)
    ]
    # the consumption stage declares no arrival perch and is entered at its
    # decision perch (AMD-MB-001 D8, the plan's P2)
    assert marks("backward", "inputsMetadata") == [
        (f"periods[{h}]/cons/cons:function:dcsn:{wire}", "w → m", *[f"periods[{h}]/port"] * 3)
        for h in (1, 0)
        for wire in ("V",)
    ]
    assert marks("forward", "outputsMetadata") == [
        (f"periods[{h}]/cons/cons:measure:dcsn", "w → m", *[f"periods[{h}]/port"] * 3)
        for h in (1, 0)
    ]
    assert marks("forward", "inputsMetadata") == [
        (f"periods[{h}]/cons/cons:measure:cntn", "a", *[f"periods[{h}]/disc"] * 3)
        for h in (1, 0)
    ]
    # the whole view is the view of every occurrence, as before the
    # restriction existed
    assert as_json(me.to_model_explorer(port_cons, periods=None, stages=None, initial=True)) == as_json(
        port_cons_view
    )


@pytest.fixture(scope="module")
def durables():
    """The durables model's trellis of 51 periods, elaborated from its
    recipe once for the module, and the connection report of its whole
    selection."""
    trellis = elaborate_trellis(
        load_recipe(str(ROOT / "applications/durables/declaration"), "spec.yml")
    )
    return trellis, connection_report(trellis)


def boundary_nodes(graph):
    """The boundary nodes of a graph of a trellis view (design pass 10 §6),
    each as its id, its attributes, the ids of its ports and its edges,
    `(source node, source port, target port)`, sorted by id."""
    return sorted(
        (
            node.id,
            attributes(node),
            [m.id for m in (*node.outputsMetadata, *node.inputsMetadata)],
            [
                (e.sourceNodeId, e.sourceNodeOutputId, e.targetNodeInputId)
                for e in node.incomingEdges
            ],
        )
        for node in graph.nodes
        if not node.namespace and attributes(node).get("kind") in me.BOUNDARY_KINDS
    )


def edges_from(graph, node_id):
    """The edges of a graph that leave the node `node_id`, each as the node
    it enters and its two ports."""
    return sorted(
        (node.id, e.sourceNodeOutputId, e.targetNodeInputId)
        for node in graph.nodes
        for e in node.incomingEdges
        if e.sourceNodeId == node_id
    )


@needs_viewer
def test_the_trellis_graphs_mark_the_data_that_enter_or_leave_them_and_hold_no_root_container(
    durables,
):
    """Design pass 10 §6 (unit N, Task 6; N-D7): the root `Inputs` and
    `Outputs` leave both graphs of the durables trellis, and each wire they
    held is a `boundary` node at the root, `kind` `start`, `end` or
    `outside`, labeled by the word of its role and the wire's own label, or
    by the occurrence it reaches outside the view, with the edge to or from
    the occurrence's port. The whole forward graph marks the arrival
    measure of the first occurrence in time and the measure the last one
    gives, the backward graph the terminal value of `bequest` and the
    arrival value of the first `tenure`. Restricted
    to periods 0 to 2, the wires that the joins between `tenure` of
    periods[2] and an occurrence of `periods[3]` carry enter or leave at one `outside`
    node for each occurrence they reach, naming it, which holds one port
    for each of those wires (design pass 12 §2): one node for each
    occurrence the connection report names in each graph, the backward
    graph's holding the value and the two marginal values; no node is
    invented."""
    trellis, report = durables
    whole = me.to_model_explorer(trellis, selection=report.selection)
    first, last = "periods[50]/tenure", "periods[0]/bequest"
    for graph in whole.graphs:
        assert not [
            node.id
            for node in graph.nodes
            if not node.namespace and node.id.endswith(("GraphInputs", "GraphOutputs"))
        ], graph.id
    backward, forward = builders_graphs(whole)
    forward_start = f"{first}/tenure:measure:arvl"
    forward_end = f"{last}/bequest:measure:dcsn"
    assert boundary_nodes(forward) == [
        (
            f"end:{forward_end}",
            {"kind": "end", "label": "terminal μ"},
            [forward_end],
            [(f"{last}/arvl_to_dcsn:Pushforward", forward_end, forward_end)],
        ),
        (
            f"start:{forward_start}",
            {"kind": "start", "label": "starting data μ≺"},
            [forward_start],
            [],
        ),
    ]
    assert edges_from(forward, f"start:{forward_start}") == [
        (f"{first}/arvl_to_dcsn:DistributionExtension:ε", forward_start, forward_start)
    ]
    terminal = f"{last}/bequest:function:cntn:V"
    results = [
        (f"{first}/tenure:function:arvl:{name}", label)
        for name, label in (
            ("V", "𝑉≺(a, h, z)"),
        )
    ]
    # the terminal value's node, whose edge leaves for bequest's aggregation
    terminal_node = (
        f"start:{terminal}",
        {"kind": "start", "label": "terminal condition 𝑉≻()"},
        [terminal],
        [],
    )
    assert boundary_nodes(backward) == [
        (
            f"end:{port}",
            {"kind": "end", "label": f"result {label}"},
            [port],
            [(f"{first}/dcsn_to_arvl:Evaluation", port, port)],
        )
        for port, label in results
    ] + [terminal_node]
    assert edges_from(backward, f"start:{terminal}") == [
        (f"{last}/cntn_to_dcsn:Aggregation", terminal, terminal)
    ]

    # restricted to periods 0 to 2: the joins to periods[3], the outside
    # occurrences of the routes the report of the three periods names
    chosen = {(h, key) for h in range(3) for key in trellis["periods"][h]["stages"]}
    three = connection_report(trellis, periods=range(3), selection=report.selection)
    reached = sorted(
        {
            f"periods[{h}]/{key}"
            for route in three.routes
            for h, key in (route.source, route.destination)
            if (route.source in chosen) != (route.destination in chosen) and (h, key) not in chosen
        }
    )
    assert reached == ["periods[3]/adjuster_cons", "periods[3]/keeper_cons"]
    shown = me.to_model_explorer(trellis, periods=range(3), selection=report.selection)
    backward, forward = builders_graphs(shown)
    tenure = "periods[2]/tenure"
    measure = f"{tenure}/tenure:measure:arvl"
    assert boundary_nodes(forward) == [
        (
            f"end:{forward_end}",
            {"kind": "end", "label": "terminal μ"},
            [forward_end],
            [(f"{last}/arvl_to_dcsn:Pushforward", forward_end, forward_end)],
        )
    ] + [
        (
            f"outside:{tenure}:{where}",
            {"kind": "outside", "label": where, "target": where},
            [measure],
            [],
        )
        for where in reached
    ]
    for where in reached:
        assert edges_from(forward, f"outside:{tenure}:{where}") == [
            (f"{tenure}/arvl_to_dcsn:DistributionExtension:ε", measure, measure)
        ]
    # one node for each occurrence reached, its one wire its port, with the
    # edge from the writer of its wire (design pass 12 §2)
    leaving = [f"{tenure}/tenure:function:arvl:{name}" for name in ("V",)]
    assert boundary_nodes(backward) == sorted(
        [
            (
                f"outside:{tenure}:{where}",
                {"kind": "outside", "label": where, "target": where},
                leaving,
                [(f"{tenure}/dcsn_to_arvl:Evaluation", port, port) for port in leaving],
            )
            for where in reached
        ]
        + [terminal_node]
    )


def route_of(edge):
    """The route record an edge of a trellis view carries under its
    attribute `route`, None for an edge that carries none."""
    return next((pair.value for pair in getattr(edge, "attrs", ()) if pair.key == "route"), None)


@needs_viewer
def test_each_edge_a_route_establishes_carries_the_route_its_fields_and_its_pairs(durables):
    """Design pass 10 §6 (unit N, Task 6): each edge of a trellis graph that
    joins two stage occurrences carries, under its attribute `route`, the
    record of the native route that establishes it, read from the
    selection and from nothing else: its branch, its source and its
    destination occurrence, the source's continuation fields and the
    destination's arrival fields in the route's order, its pairs with
    their origin and address, its status and its law. In the durables
    trellis, whole and at periods 0 to 2, every route whose two occurrences
    the view holds is carried by its edges, forward from the source to the
    destination and backward the other way; no other edge carries one; and
    each record equals the route of the connection report, its pairs'
    origins among it. Two records stand in full: the route of the branch
    `keep` within periods[2], whose pairs the period's connector writes to
    the keeper's decision states, its entry perch's, and the route between
    periods[2] and periods[1], whose pairs the inter-period mapping writes
    (decision MB-U28)."""
    trellis, report = durables

    def address(position):
        return f"periods[{position[0]}]/{position[1]}"

    routes = {
        (address(route.source), route.branch, address(route.destination)): route
        for route in report.routes
    }
    for view in (
        me.to_model_explorer(trellis, selection=report.selection),
        me.to_model_explorer(trellis, periods=range(3), selection=report.selection),
    ):
        for graph in view.graphs:
            held = {ns for ns in graph.groupNodeAttributes if ns.count("/") == 1}
            carried = set()
            for node in graph.nodes:
                for edge in node.incomingEdges:
                    record = route_of(edge)
                    ends = occurrence_of(edge.sourceNodeId), occurrence_of(node.id)
                    if None in ends or ends[0] == ends[1]:
                        assert record is None, (graph.id, node.id, edge)
                        continue
                    key = (record["source"], record["branch"], record["destination"])
                    route = routes[key]
                    assert record == {
                        "branch": route.branch,
                        "source": key[0],
                        "destination": key[2],
                        "source_fields": list(route.source_fields),
                        "destination_fields": list(route.destination_fields),
                        "pairs": [
                            {
                                "source_field": pair.writing.field,
                                "destination_field": pair.reading.field,
                                "origin": pair.origin,
                                "address": pair.address,
                            }
                            for pair in route.pairs
                        ],
                        "status": route.status,
                        "law": route.law,
                    }
                    drawn = tuple("/".join(end) for end in ends)
                    along = (key[0], key[2]) if graph.id == "forward" else (key[2], key[0])
                    assert drawn == along, (graph.id, drawn, key)
                    carried.add(key)
            assert carried == {
                key for key in routes if key[0] in held and key[2] in held
            }, graph.id

    # two records in full: the route of the branch `keep` within periods[2]
    # and the route between periods[2] and periods[1], both authored
    shown = me.to_model_explorer(trellis, periods=range(3), selection=report.selection)
    records = {
        (record["source"], record["destination"]): record
        for graph in shown.graphs
        for node in graph.nodes
        for edge in node.incomingEdges
        if (record := route_of(edge)) is not None
    }
    assert records["periods[2]/tenure", "periods[2]/keeper_cons"] == {
        "branch": "keep",
        "source": "periods[2]/tenure",
        "destination": "periods[2]/keeper_cons",
        "source_fields": ["w_kp", "h_kp", "z_kp"],
        "destination_fields": ["w_d", "h_d", "z_d"],
        "pairs": [
            {
                "source_field": f"{name}_kp",
                "destination_field": f"{name}_d",
                "origin": "authored",
                "address": "periods[2].connectors[0]",
            }
            for name in ("w", "h", "z")
        ],
        "status": "certified",
        "law": "tenure:measure:cntn:keep",
    }
    assert records["periods[2]/keeper_cons", "periods[1]/tenure"] == {
        "branch": None,
        "source": "periods[2]/keeper_cons",
        "destination": "periods[1]/tenure",
        "source_fields": ["a_nxt_kp", "h_nxt_kp", "z_nxt_kp"],
        "destination_fields": ["a", "h", "z"],
        "pairs": [
            {
                "source_field": f"{name}_nxt_kp",
                "destination_field": name,
                "origin": "authored",
                "address": "inter_connectors[1]",
            }
            for name in ("a", "h", "z")
        ],
        "status": "certified",
        "law": "keeper_cons:measure:cntn",
    }


@needs_viewer
def test_a_restriction_that_holds_no_occurrence_is_refused_in_one_sentence(port_cons):
    """An index the trellis does not hold, a key no period selected holds and
    a selection of no occurrence are refused under `trellis-file-shape`, each
    in one sentence; a stage version takes no selection."""
    for selection, sentence in (
        ({"periods": [7]}, "the trellis holds 6 periods, and periods[7] is none of them"),
        (
            {"stages": ["nope"]},
            "the periods selected hold no stage 'nope'; they hold cons, disc, port",
        ),
        ({"periods": []}, "the selection holds no stage occurrence of the trellis"),
    ):
        with pytest.raises(FactoryError) as refused:
            me.to_model_explorer(port_cons, **selection)
        assert (refused.value.rule, refused.value.message) == ("trellis-file-shape", sentence)
    with pytest.raises(TypeError):
        me.to_model_explorer(port_cons["periods"][0]["stages"]["cons"], periods=[0])


def two_periods(cons, port):
    """The trellis of two periods of lesson 05: port, cons and disc in each,
    the arrival `m` joined to `m_next` within a period and the saving `a` to
    `k` between the periods."""
    disc = elaborate_stage(load_stage(str(
        ROOT / "applications/portfolio-choice/declaration/stages/disc/disc.bl")))
    period = {
        "stages": {"port": port, "cons": cons, "disc": disc},
        "connectors": [{"m_next": "m"}],
    }
    return accrete(accrete({"periods": [], "inter_connectors": []}, period), period, {"a": "k"})


@needs_viewer
def test_layers_to_open_names_the_first_parts_of_the_namespaces(cons, port, tmp_path):
    collection = me.to_model_explorer(cons)
    assert me.layers_to_open(collection, "backward", 1) == (
        "cntn_to_dcsn",
        "dcsn_to_arvl",
        "policy",
    )
    assert me.layers_to_open(collection, "forward", 1) == ("arvl_to_dcsn", "dcsn_to_cntn")
    graph_path, _ = me.write_model_explorer(cons, tmp_path)
    document = json.loads(graph_path.read_text(encoding="utf-8"))
    assert me.layers_to_open(document, "backward", 1) == me.layers_to_open(
        collection, "backward", 1
    )
    with pytest.raises(ValueError):
        me.layers_to_open(collection, "sideways", 1)
    assert me.layers_to_open(
        me.to_model_explorer(two_periods(cons, port)), "backward", 2
    ) == tuple(f"periods[{h}]/{key}" for h in (1, 0) for key in ("port", "cons", "disc"))


@needs_viewer
def test_node_place_reads_the_occurrence_and_the_block_from_the_namespace(
    cons, port, retiree_death
):
    collection = me.to_model_explorer(cons)
    place = me.node_place
    assert place(collection, "backward", "policy.InvEuler:Aggregation") == ("", "policy")
    assert place(collection, "backward", "cntn_to_dcsn:Pullback") == ("", "cntn_to_dcsn")
    assert place(collection, "backward", "policy:Evaluation") == ("", "policy")
    assert place(collection, "backward", "GraphInputs") == ("", "")
    assert place(collection, "backward", "policy" + me.LAYER_ID_ENDING) == ("", "policy")
    assert place(collection, "backward initial diagram", "policy") == ("", "policy")
    assert place(collection, "backward initial diagram", "cons:dcsn:c") == ("", "")
    retiree = me.to_model_explorer(retiree_death)
    assert place(retiree, "forward", "forward:refused") == ("", "")
    # a box of one branch of a branching block, `<block>:<operator>:<branch>`,
    # stands in that block
    assert place(retiree, "backward", "cntn_to_dcsn:Pullback:survive").block == "cntn_to_dcsn"
    two = me.to_model_explorer(two_periods(cons, port))
    assert place(two, "backward", "periods[0]/cons/policy.InvEuler:Aggregation") == (
        "periods[0]/cons",
        "policy",
    )
    assert place(two, "backward", "periods[0]/cons/GraphOutputs") == ("periods[0]/cons", "")
    assert place(two, "backward", "periods[1]/port" + me.LAYER_ID_ENDING) == (
        "periods[1]/port",
        "",
    )
    assert place(two, "backward", "periods[1]" + me.LAYER_ID_ENDING) == ("periods[1]", "")
    # a boundary node of a trellis stands at the graph's root
    assert place(two, "backward", "start:periods[0]/disc/disc:function:cntn:V") == ("", "")
    with pytest.raises(KeyError):
        place(collection, "backward", "no:such")
    with pytest.raises(ValueError):
        place(collection, "sideways", "GraphInputs")


@needs_viewer
def test_wire_counts_count_distinct_wires_of_the_two_builders_graphs(cons, retiree_death):
    collection = me.to_model_explorer(cons)
    # 20 wires for cons.bl, the count spec 0.3 §2.5 states: a wire two boxes
    # read counts once
    assert me.wire_counts(collection) == {"backward": 17, "forward": 3}
    assert me.wire_counts(dataclasses.asdict(collection)) == {"backward": 17, "forward": 3}
    backward = next(graph for graph in collection.graphs if graph.id == "backward")
    assert sum(len(node.incomingEdges) for node in backward.nodes) == 18
    assert me.wire_counts(me.to_model_explorer(retiree_death))["forward"] == 0


def test_the_folder_of_the_views_is_named_by_the_versions_of_python_and_its_distributions(
    monkeypatch,
):
    """The folder of the stage views kept between processes is named by the
    package's version and a digest (`_source_version`, ruling R25) that
    covers Python's major and minor version and the installed version of
    each distribution a stage view's computation imports, as
    `importlib.metadata.version` reads it: another installed version of
    `discopy` gives another name, and so does `discopy` not installed, which
    raises nothing. With the reading of the versions restored, the name is
    the first one again."""
    reading = metadata.version

    def another_discopy(name):
        """The installed version of `name`, and 0.0.1 for `discopy`."""
        return "0.0.1" if name == "discopy" else reading(name)

    def no_discopy(name):
        """The installed version of `name`; `discopy` is not installed."""
        if name == "discopy":
            raise metadata.PackageNotFoundError(name)
        return reading(name)

    me._source_version.cache_clear()
    try:
        named = me._source_version()
        changed = []
        for stand_in in (another_discopy, no_discopy):
            with monkeypatch.context() as patch:
                patch.setattr(metadata, "version", stand_in)
                me._source_version.cache_clear()
                changed.append(me._source_version())
        me._source_version.cache_clear()
        assert len({named, *changed}) == 3
        assert me._source_version() == named
    finally:
        # the next test reads the value computed with the versions installed
        me._source_version.cache_clear()


# The script of the test of the time the folder's name is computed, run in a
# fresh process on a copy of the package whose folder its first argument
# names: the exporter imported, a comment appended to a source file of the
# copy, and three lines printed, the exporter's file, the name the process
# holds, and the name the changed files give once the held name is cleared.
CHANGED_AFTER_IMPORT = """\
import sys
from pathlib import Path

from bellman.factory import model_explorer

source = Path(sys.argv[1]) / "bellman" / "refusals.py"
source.write_text(source.read_text(encoding="utf-8") + "\\n# a comment\\n", encoding="utf-8")
print(model_explorer.__file__)
print(model_explorer._source_version())
model_explorer._source_version.cache_clear()
print(model_explorer._source_version())
"""


def test_the_folder_of_the_views_is_named_by_the_files_as_the_process_imported_them(tmp_path):
    """The name of the folder of the views is computed when the exporter is
    imported (`_source_version`), so that it describes the package's files
    as the process loaded its code: in a fresh process on a copy of the
    package, a comment appended to a source file after the import leaves the
    name the process holds as it was, and the changed files give another
    name."""
    package = tmp_path / "package"
    shutil.copytree(
        ROOT / "packages/bellman/bellman",
        package / "bellman",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copyfile(ROOT / "packages/bellman/pyproject.toml", package / "pyproject.toml")
    # the folder a process starts in stands first on its path, so the child
    # starts in the test's own folder and not in the one pytest runs from
    run = subprocess.run(
        [sys.executable, "-c", CHANGED_AFTER_IMPORT, str(package)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(package), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    imported, held, changed = run.stdout.splitlines()
    # the process ran the copy's exporter
    assert Path(imported).is_relative_to(package)
    assert held != changed


@needs_viewer
def test_the_export_keeps_no_folder_of_views_where_its_name_cannot_be_computed(
    cons, monkeypatch, tmp_path
):
    """Where a file of the package or a distribution's metadata cannot be
    read as the name of the folder of the views is computed
    (`_source_version`), the process has no folder of the views and the
    exporter still imports: the name is None, and a trellis of one
    occurrence of `cons` is exported, its two stage views computed, with no
    file read or written under the cache folder. The two cases are a source
    file of the package whose reading raises a PermissionError and a
    distribution whose metadata raises a UnicodeDecodeError, the error of a
    METADATA file that is no UTF-8."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    reading, version = Path.read_bytes, metadata.version

    def unreadable(path):
        """The bytes of the file `path`; a PermissionError for the package's
        `refusals.py`."""
        if path == me._PACKAGE_FOLDER / "refusals.py":
            raise PermissionError(13, "Permission denied", str(path))
        return reading(path)

    def undecodable(name):
        """The installed version of `name`; for `lark`, the error of a
        METADATA file that is no UTF-8."""
        if name == "lark":
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        return version(name)

    computed = []
    compute = me._graph

    def counted(graph_builder, stage, direction):
        """`_graph`, each call recorded."""
        computed.append(direction)
        return compute(graph_builder, stage, direction)

    monkeypatch.setattr(me, "_graph", counted)
    trellis = accrete(
        {"periods": [], "inter_connectors": []},
        {"stages": {"consumption": cons}, "connectors": []},
    )
    try:
        for owner, name, stand_in in (
            (Path, "read_bytes", unreadable),
            (metadata, "version", undecodable),
        ):
            me._source_version.cache_clear()
            with monkeypatch.context() as patch:
                patch.setattr(owner, name, stand_in)
                assert me._source_version() is None
            me._VIEW_CACHE.clear()
            computed.clear()
            assert graph_named(me.to_model_explorer(trellis), "backward").nodes
            assert sorted(computed) == ["backward", "forward"]
            assert list(tmp_path.iterdir()) == []
    finally:
        # the next test reads the name the files and the versions installed
        # give, and no view kept under a name of None
        me._source_version.cache_clear()
        me._VIEW_CACHE.clear()


@needs_viewer
def test_the_stage_views_drawn_with_and_without_the_short_labels_are_kept_apart(
    cons, monkeypatch, tmp_path
):
    """Ruling R27: the stage views' key, in memory and in the cache folder,
    holds the value of the switch `SHORT_LABELS`, which the labels of a view
    read, so that a trellis drawn with the proposed label forms and one
    drawn with the recorded forms keep their stage views apart. A trellis of
    one occurrence of `cons` is drawn without the switch, with it and
    without it again: the views of the two directions are computed for each
    of the first two drawings and for no other, and each drawing holds its
    own form of the label of the first aggregation's value port, the label
    the switch chooses: the expression the wire denotes without the switch,
    and the function at its coordinates, `𝑉(m_d)`, with it. With the views
    in memory dropped, each value of the switch reads its own two entries of
    the cache folder, four in all. The switch is restored after each
    drawing."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    computed = []
    compute = me._graph

    def counted(graph_builder, stage, direction):
        """`_graph`, each call recorded."""
        computed.append(direction)
        return compute(graph_builder, stage, direction)

    monkeypatch.setattr(me, "_graph", counted)
    trellis = accrete(
        {"periods": [], "inter_connectors": []},
        {"stages": {"consumption": cons}, "connectors": []},
    )

    def drawn(short):
        """The label of the value port of the backward graph's first
        aggregation, the trellis drawn with the switch at `short`, and the
        number of stage views the drawing computed."""
        computed.clear()
        with monkeypatch.context() as patch:
            patch.setattr(me, "SHORT_LABELS", short)
            backward = graph_named(me.to_model_explorer(trellis), "backward")
        labels = {
            port.id: attributes(port)["label"]
            for node in backward.nodes
            for port in node.outputsMetadata
        }
        return labels["periods[0]/consumption/cntn_to_dcsn:Aggregation:V:result"], len(computed)

    # the port's label in the recorded form and in the proposed form
    recorded, proposed = "m_d ↦ 𝑢(𝑐(m_d)) + 𝑉≻(𝑔(m_d, 𝑐(m_d)))", "𝑉(m_d)"
    me._VIEW_CACHE.clear()
    assert drawn(False) == (recorded, 2)
    assert drawn(True) == (proposed, 2)
    assert drawn(False) == (recorded, 0)
    me._VIEW_CACHE.clear()
    assert drawn(True) == (proposed, 0)
    assert drawn(False) == (recorded, 0)
    assert len(list(tmp_path.rglob("*.json"))) == 4
    assert me.SHORT_LABELS is False
