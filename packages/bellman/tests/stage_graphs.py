"""The graphs of a stage at each level, direction and grain, the graphs inside
their bubbles, and the boxes, wires, ports and sorts that a graph holds."""

# the two levels of the graphs of a stage
LEVELS = ("initial", "builders")


# the two directions in which a graph of each level is read
DIRECTIONS = ("backward", "forward")


# the five grains of a graph
GRAINS = ("builder", "sub-builder", "primitive", "combined", "factored")


GRAPH_TRIPLES = tuple((v, d, g) for v in LEVELS for d in DIRECTIONS for g in GRAINS)


# the pullback of the backward decision builder, which applies the law of
# motion 𝑔
DECISION_PULLBACK = "cntn_to_dcsn:Pullback"


def graphs_of(stage):
    """Each graph of `stage` as `(level, direction, grain, graph)`, in the
    order of `GRAPH_TRIPLES`: the two initial diagrams and the two builders
    graphs, each at the five grains.

    The builder, sub-builder and primitive grains are read through the
    handles of the stage, `stage.initial.backward`, `stage.initial.forward`,
    `stage.builder.bwd` and `stage.builder.fwd`, and their attributes
    `sub_builders` and `primitives`; the combined and factored grains, which
    no handle names, through `semgraph.record`. A graph that the package
    refuses to construct is yielded as its refusal, the `NotConstructed`
    error, in place of the graph: a caller tells the two apart by
    `isinstance(graph, NotConstructed)`."""
    from bellman.refusals import NotConstructed
    from bellman.stage import semgraph

    for level, direction, grain in GRAPH_TRIPLES:
        handle = graph_handle(stage, level, direction)
        try:
            if grain == "builder":
                graph = handle.graph
            elif grain == "sub-builder":
                graph = handle.sub_builders.graph
            elif grain == "primitive":
                graph = handle.primitives.graph
            else:
                graph = semgraph.record(stage, level=level, direction=direction, grain=grain).graph
        except NotConstructed as refusal:
            graph = refusal
        yield level, direction, grain, graph


def graph_handle(stage, level, direction):
    """The handle of the graph of `stage` at `level` and `direction`:
    `stage.initial.backward`, `stage.initial.forward`, `stage.builder.bwd`
    or `stage.builder.fwd`."""
    if level == "initial":
        return stage.initial.backward if direction == "backward" else stage.initial.forward
    return stage.builder.bwd if direction == "backward" else stage.builder.fwd


def operator_boxes(stage, direction):
    """The primitive operators of one builders graph, which the primitive
    grain holds with no bubble around them."""
    from bellman.native.labels import is_wiring
    from bellman.stage.grains import graph_of

    graph = graph_of(stage, "builders", direction, grain="primitive")
    return [box for box in graph.boxes if not is_wiring(box)]


def aggregation_box(version, builder="cntn_to_dcsn"):
    """The aggregation box of a backward builder, holding the value line."""
    primitives = version.builder.bwd[builder].primitives
    (name,) = [key for key in primitives.list() if key.split(":")[-1] == "Aggregation"]
    return primitives[name]


def pushforward_box(version, builder="arvl_to_dcsn"):
    """The push-forward box of a forward builder, with the law of motion."""
    primitives = version.builder.fwd[builder].primitives
    (name,) = [key for key in primitives.list() if key.split(":")[-1] == "Pushforward"]
    return primitives[name]


def interior_of(box):
    """The graph inside a bubble, as a hypergraph; None for any other box."""
    from discopy.frobenius import Bubble, Hypergraph

    return Hypergraph.from_diagram(box.arg) if isinstance(box, Bubble) else None


def graphs_inside(graph, name):
    """`(name, graph)` for the graph, then for every graph inside one of its
    bubbles, to any depth, named by the graph's name and the bubble's."""
    yield name, graph
    for box in graph.boxes:
        interior = interior_of(box)
        if interior is not None:
            yield from graphs_inside(interior, f"{name} / {box.name}")


def wire_sorts(graph):
    """The sort of each wire of a graph, by the wire's number: the sort of
    the wire numbered `w` is `wire_sorts(graph)[w]`."""
    return tuple(types.inside[0] for types in graph.spider_types)


def port_wires(graph):
    """`(inputs, outputs)`: the wires at the input ports of a graph and the
    wires at its output ports, each in the order of the ports."""
    return tuple(graph.dom_wires), tuple(graph.cod_wires)


def boxes_with_wires(graph):
    """`(box, read, written)` for each box of a graph: the wires at its input
    ports and the wires at its output ports, each in the order of the
    ports."""
    return [
        (box, tuple(read), tuple(written))
        for box, (read, written) in zip(graph.boxes, graph.box_wires)
    ]
