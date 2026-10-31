"""The two builders graphs of a stage, and the four graphs its construction
stores.

`construct_graphs` builds the four stored graphs when the stage is constructed:
the backward and the forward initial diagram, cut from the undirected graph of
the whole stage with every block a bubble around its statement graph, and the
builder grain of the backward and of the forward builders graph, each a
`Refusal` where it cannot be constructed. The undirected graph and the
construction table are not stored. The other grains of a builders graph,
primitive, sub-builder (`node`), combined and factored, are built by
`builders_graph_by_grain` when the graph queries ask for them, from the
construction table folded again from the definitions table.

A box of a builders graph is a row of the table, named by the row's identity,
carrying the references its kind takes and wired to the other boxes by the
identities of the wires it reads and writes. A builder is a `Builder` bubble
around its rows, with data `()`; an authored `!node` of a backward block is a
bubble around the rows the fold marks with its address, closed at the
sub-builder grain and open at the primitive grain; an authored node of a
forward or policy block is a bubble around the rows of its statements.
`interior_at` gives one piece of either kind of graph at a grain as the bubble
of its kind, and `bundles` the value bundles of a graph. A function that reads
the wire table of `wire_sorts.py` takes it as its first argument, `wires`.
"""

from __future__ import annotations

from discopy.frobenius import Box, Bubble

from bellman.fold.block_lines import blocks_of
from bellman.fold.table import ConstructionTable
from bellman.graphs.initial_diagrams import (
    GRAINS,
    cut_initial_diagrams,
    initial_diagram_from_lines,
    initial_diagram_inputs_and_outputs,
    undirected_graph,
)
from bellman.graphs.wire_sorts import (
    WiredBox,
    WireTable,
    captures,
    connect,
    group_inputs_outputs,
    needed,
    wired_boxes,
)
from bellman.native.hypergraphs import BellmanHypergraph, Block, Builder
from bellman.native.identity import box_identity, piece_identity
from bellman.native.labels import is_wiring
from bellman.native.records import Builders, InitialDiagrams, Refusal, with_identity
from bellman.refusals import NotConstructed
from bellman.syntax.lower import span_at
from bellman.syntax.vocabulary import ARRIVAL, VALUE_ROLES

# --- the four stored graphs ---


def construct_graphs(stage, table: ConstructionTable, spans=None):
    """The four stored graphs of a stage, as the pair of an `InitialDiagrams`
    and a `Builders` record: the backward and the forward initial diagram,
    the blocks of each direction on field wires, and the builder grain of
    the backward and of the forward builders graph, each a `Refusal` where
    it cannot be constructed. The undirected graph of the
    whole stage is built here, the two initial diagrams are cut from it, and
    it is not kept. `graph_of(stage, level, direction, grain)` of
    `bellman.stage.grains` derives every other grain when it is asked
    for."""
    wires = WireTable(stage, table)
    bubbles = {}
    for direction in ("forward", "backward"):
        try:
            graph = initial_diagram_from_lines(wires, direction, grains=("builder",))["builder"]
        except NotConstructed:
            continue
        bubbles.update({box.name: box for box in graph.boxes})
    undirected = undirected_graph(stage, bubbles, wires)
    try:
        initial = cut_initial_diagrams(stage, undirected)
    except NotConstructed as error:
        facts = _facts(error, spans)
        refusal = Refusal(reason=facts.pop("message"), diagnostic=facts)
        # neither graph then holds the blocks, so they are kept beside the two
        # refusals, where `block_lines.blocks_of` reads them
        initial = InitialDiagrams(
            backward=refusal, forward=refusal, refused_blocks=tuple(undirected.boxes)
        )
    builders = {}
    for direction in ("backward", "forward"):
        try:
            builders[direction] = builders_graph_by_grain(wires, direction, grains=("builder",))[
                "builder"
            ]
        except NotConstructed as error:
            facts = _facts(error, spans)
            builders[direction] = Refusal(reason=facts.pop("message"), diagnostic=facts)
    return initial, Builders(**builders)


def _facts(error, spans):
    """The facts a `Refusal` records of the refusal `error`: its message,
    stage, address and rule, and its file position, read from `spans` where
    they hold the refusal's address."""
    facts = {
        name: getattr(error, name)
        for name in (
            "message",
            "stage",
            "address",
            "rule",
            "file",
            "line",
            "column",
            "end_line",
            "end_column",
        )
    }
    # the address is the item's term address, and the file position it was
    # written at where the refusal was raised at a definition record of a
    # top-level item; the item is the same under either name
    span = span_at(error.address, spans)
    if span is not None:
        facts.update(
            (name, getattr(span, name))
            for name in ("file", "line", "column", "end_line", "end_column")
        )
    return facts


# --- the builders graphs at every grain ---


def builders_graph_by_grain(wires, direction, grains=GRAINS):
    """The graphs of a direction's builders at the given grains (all five
    by default), by grain: the builder grain with every builder a bubble,
    the primitive grain with every row a box (a sub-builder opened, its
    adjacent pointwise segments merged by the fold), the sub-builder grain
    (`node`) with the authored nodes closed, the combined grain keeping the
    boxes an output depends on, the factored grain opening a sub-builder
    that holds a method target."""
    if wires.refusal is not None:
        raise wires.refusal
    per_builder = wires.rows(direction)
    if not per_builder:
        raise NotConstructed(
            f"no {direction} builder", stage=wires.name, address="stage", rule="not-constructed"
        )
    closed_rows = {box.name: rows for box, rows in wires.rows(direction, closed=True)}
    signatures = {
        box.name: wires.builder_inputs_and_outputs(box, direction, rows)
        for box, rows in per_builder
    }
    inputs, outputs = (
        _forward_inputs_outputs(signatures)
        if direction == "forward"
        else _backward_inputs_outputs(wires, per_builder, signatures)
    )
    graphs = {}
    for grain in grains:
        boxes = []
        for box, rows in per_builder:
            dom, cod = signatures[box.name]
            exported = set(cod) | set(outputs)
            if grain == "builder":
                # a backward block holds its sub-builders as bubbles inside
                # its own; a block without one, a forward block among them,
                # holds the boxes of its operator rows, which the primitive
                # grain may merge further
                held = closed_rows[box.name]
                if any(op.node is not None for op, _, _ in held):
                    inside = operator_boxes(wires, held, "node", block=box.name, exported=exported)
                else:
                    inside = operator_boxes(wires, held, "primitive")
                boxes.append(_builder_bubble(wires, box.name, inside, inputs=dom, outputs=cod))
            elif grain == "primitive":
                boxes.extend(operator_boxes(wires, rows, grain, block=box.name, exported=exported))
            else:
                boxes.extend(
                    operator_boxes(
                        wires, closed_rows[box.name], grain, block=box.name, exported=exported
                    )
                )
        if grain == "combined":
            boxes = needed(boxes, outputs)
        graphs[grain] = connect(wires, boxes, inputs=inputs, outputs=outputs)
    return graphs


def _forward_inputs_outputs(signatures):
    """The inputs and outputs of the forward builders graph, from the inputs
    and outputs of its builders: every input of a builder but a measure
    another builder writes, and every measure written at the last perch the
    builders reach."""
    produced_measures = {m for _, cod in signatures.values() for m in cod}
    inputs = tuple(
        dict.fromkeys(
            i
            for dom, _ in signatures.values()
            for i in dom
            if i.kind != "measure" or i not in produced_measures
        )
    )
    # the graph ends at the last perch the forward builders reach, at every
    # measure written there, one per label of a branching block
    order = {"arvl": 0, "dcsn": 1, "cntn": 2}
    last = max(
        (m.perch for _, cod in signatures.values() for m in cod), key=lambda p: order.get(p, -1)
    )
    outputs = tuple(
        dict.fromkeys(m for _, cod in signatures.values() for m in cod if m.perch == last)
    )
    return inputs, outputs


def _backward_inputs_outputs(wires, per_builder, signatures):
    """The inputs and outputs of the backward builders graph: those of the
    backward initial diagram as the wires the graph carries, then the
    captures of its builders; among the outputs, after the arrival values,
    the arrival marginal values a bound marginal block adds (specification
    0.6 §7, addition 3)."""
    declared_in, declared_out = initial_diagram_inputs_and_outputs(wires, "backward")
    added = tuple(
        identity
        for outputs in wires.added_outputs.values()
        for identity in outputs
        if identity.perch == ARRIVAL and identity not in declared_out
    )
    if added:
        at = max(
            (
                place + 1
                for place, identity in enumerate(declared_out)
                if identity.perch == ARRIVAL
            ),
            default=0,
        )
        declared_out = (*declared_out[:at], *added, *declared_out[at:])
    # a control among the diagram's inputs is no input wire of the builders
    # graph; a control the policy builder writes stays among the outputs
    declared_in = wires.backward_inputs(declared_in)
    declared_out = wires.backward_outputs(declared_out)
    produced = {o for _, cod in signatures.values() for o in cod} | {
        o for _, rows in per_builder for _, _, outs in rows for o in outs
    }
    consumed = [i for dom, _ in signatures.values() for i in dom]
    return declared_in + captures(consumed, produced, declared_in), declared_out


def _builder_bubble(wires, name, inside, *, inputs, outputs):
    """A builder or a sub-builder named `name` as a native `Builder` bubble
    around the boxes `inside`, on the wires `inputs` and `outputs`."""
    interior = connect(wires, inside, inputs=inputs, outputs=outputs)
    return WiredBox(
        with_identity(
            Builder(
                interior.to_diagram(),
                name=name,
                dom=wires.tensor_of_sorts(inputs),
                cod=wires.tensor_of_sorts(outputs),
                data=(),
            ),
            piece_identity(name),
        ),
        inputs,
        outputs,
    )


# the operator kinds whose rows stand as a box at the factored grain, the
# sub-builder that holds one opened: an expectation and the maximization an
# operative `argmax` line forms, each a place a method attaches to
TARGET_KINDS = ("Expectation", "Argmax")


def operator_boxes(wires, rows, grain, *, block=None, exported=()):
    """The boxes of a builder's rows at a grain: every row a box carrying
    its references; at the node, combined and factored grains the rows of
    an authored node are one bubble, placed where its first row stands.
    A sub-builder of a backward block is the group of rows the fold marked
    with its address; a node of a forward or policy block is the group of
    rows the fold wrote for its statements."""
    if grain not in ("node", "combined", "factored") or block is None:
        return [_operator_box(wires, row) for row in rows]
    marked = any(op.node is not None for op, _, _ in rows)
    groups = wires.nodes.get(block, {})
    by_address = {a: name for name, addresses in groups.items() for a in addresses}
    if not marked and not groups:
        return [_operator_box(wires, row) for row in rows]
    grouped, order = {}, []
    # the factored grain opens a sub-builder that holds a method target:
    # every row of that sub-builder stands as a box, its evaluate included
    opened = (
        {op.node for op, _, _ in rows if op.node is not None and op.kind in TARGET_KINDS}
        if grain == "factored" and marked
        else set()
    )
    for row in rows:
        op = row.row
        owner = (
            op.node
            if marked
            else next((by_address[a] for a in op.statements if a in by_address), None)
        )
        if owner is None or owner in opened or (grain == "factored" and op.kind in TARGET_KINDS):
            order.append(("box", _operator_box(wires, row)))
        else:
            if owner not in grouped:
                order.append(("group", owner))
            grouped.setdefault(owner, []).append(row)
    boxes = []
    for kind, item in order:
        if kind == "box":
            boxes.append(item)
            continue
        members = grouped[item]
        member_rows = {member.row for member in members}
        dom, cod = group_inputs_outputs(
            members, [row for row in rows if row.row not in member_rows], exported
        )
        boxes.append(
            _builder_bubble(
                wires,
                item,
                [_operator_box(wires, member) for member in members],
                inputs=dom,
                outputs=cod,
            )
        )
    return boxes


def _operator_box(wires, row):
    """A row of a builder as a box carrying its references, on the sorts of
    the wires it reads and writes."""
    op, ins, outs = row
    return WiredBox(
        with_identity(
            Box(
                str(op.identity),
                wires.tensor_of_sorts(ins),
                wires.tensor_of_sorts(outs),
                data=op.references,
            ),
            op.identity,
        ),
        ins,
        outs,
    )


# --- one piece at a grain ---


def interior_at(wires, level, identity, *, inputs, outputs, graph, builder_graph):
    """The interior of one builder, one block or one sub-builder at a
    grain, as a bubble of the same kind on that piece's own inputs and
    outputs: the boxes of the whole graph at that grain rooted at the
    piece's address, by the one rule `Identity.key_within` states, wired by
    the same `connect` the builder grain uses. The bubble is named by
    `identity`, the stored piece's own, so that a nested block opened at a
    finer grain keeps its kind. `inputs` and `outputs` are the piece's own
    wires, so that a sub-builder keeps the signature the sub-builder grain
    gives it.

    A merge of boxes at the finer grain across the piece's edge can absorb a
    box that wrote one of the piece's own wires: opening `risk_ce` of
    `sa_savings.bl` leaves its identity evaluation, which wrote the node's
    output `CE`, in the neighboring builder. The boxes the piece stores
    that write a wire none of the boxes taken from the graph writes are
    added back, so that the node's own output and its identity evaluation
    stand inside it. The boxes are the graph's own objects, so a box of a
    derived bubble answers `denote()` and `kernel()` as the graph's
    boxes do.

    `graph` is the whole graph at that grain and `builder_graph` the same
    graph at the builder grain; the caller reads both from the graph
    queries of `bellman.stage`, which this module does not import."""

    name = identity.address
    entries = [
        entry
        for entry in wired_boxes(graph)
        if not is_wiring(entry.box) and box_identity(entry.box).key_within(name) is not None
    ]
    entries.extend(_absorbed(name, entries, builder_graph))
    interior = connect(wires, entries, inputs=inputs, outputs=outputs)
    made = Block if level == "initial" else Builder
    # a block keeps the header its author wrote at every grain, so that its
    # `header` line and its `coordinate` lines read the same there
    stored = next((box for box in blocks_of(wires.stage) if box.name == name), None)
    header = getattr(stored, "data", None) if level == "initial" and made is Block else None
    return with_identity(
        made(
            interior.to_diagram(),
            name=name,
            dom=wires.tensor_of_sorts(inputs),
            cod=wires.tensor_of_sorts(outputs),
            data=header if header is not None else (),
        ),
        identity,
    )


def _absorbed(name, entries, builder_graph):
    """The primitive boxes the piece `name` stores that write a wire none
    of `entries` writes, in stored order: what a merge of the finer graph
    took out of the piece. A bubble is opened rather than taken, so that
    only primitive boxes are added."""
    written = {wire for _, _, outs in entries for wire in outs}
    held = next(
        (
            box
            for box in builder_graph.boxes
            if getattr(box, "name", None) == piece_identity(name).block
        ),
        None,
    )
    if held is None or not hasattr(held, "arg"):
        return ()

    def walk(graph):
        for entry in wired_boxes(graph):
            if is_wiring(entry.box):
                continue
            if hasattr(entry.box, "arg"):
                yield from walk(BellmanHypergraph.from_diagram(entry.box.arg))
            else:
                yield entry

    found = []
    for entry in walk(BellmanHypergraph.from_diagram(held.arg)):
        if box_identity(entry.box).address == name and not set(entry.outputs) & written:
            found.append(entry)
            written |= set(entry.outputs)
    return tuple(found)


# --- the value bundles ---


def bundles(graph):
    """The value bundles of a graph: each maximal set of two or
    more parallel wires that share their base coordinates, are written by one
    box and are read by one box, as a mapping from each wire to the tuple of
    the bundle's wires in the order the writing box lists them. Derived from
    the graph and stored nowhere; every wire keeps its own identity, role and
    domain. The wires a graph declares as its own inputs or outputs are grouped
    likewise, the graph standing for the box that would write or read them.

    A bundle holds value wires only. Two functions that merely stand side by
    side are not one: on `cons_savings_iid.bl` the policy builder writes the
    endogenous-grid consumption `c[>]` and the grid point `w[>]` from one box
    to one box on one base, and they are a control and a state, not the
    components of a value object. A branch tuple is never a bundle either: its
    components are functions on different state spaces."""

    def carried(ob):
        """Whether a wire is a value wire, the only kind a bundle holds."""
        return getattr(ob, "kind", None) == "function" and getattr(ob, "role", None) in VALUE_ROLES

    written = {
        ob.identity: (("declared", None), index) for index, ob in enumerate(graph.dom.inside)
    }
    read = {ob.identity: {("declared", None)} for ob in graph.cod.inside}
    coordinates = {
        ob.identity: getattr(ob, "coordinates", ())
        for ob in graph.dom.inside + graph.cod.inside
        if carried(ob)
    }

    def walk(part):
        # only the operator boxes write and read: a bubble repeats the wires of
        # the boxes inside it, and its inputs and outputs are not a further
        # reader
        for box in part.to_diagram().boxes if hasattr(part, "to_diagram") else part.boxes:
            if is_wiring(box):
                continue
            if isinstance(box, Bubble):
                walk(box.arg)
                continue
            for ob in box.dom.inside:
                if carried(ob):
                    read.setdefault(ob.identity, set()).add(("box", box.name))
                    coordinates[ob.identity] = getattr(ob, "coordinates", ())
            for index, ob in enumerate(box.cod.inside):
                if carried(ob):
                    written[ob.identity] = (("box", box.name), index)
                    coordinates[ob.identity] = getattr(ob, "coordinates", ())

    walk(graph)
    groups = {}
    for name, (writer, position) in written.items():
        readers = read.get(name, set())
        if len(readers) != 1 or name not in coordinates:
            continue
        groups.setdefault((writer, next(iter(readers)), coordinates[name]), []).append(
            (position, name)
        )
    found = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        ordered = tuple(name for _, name in sorted(members))
        found.update({name: ordered for name in ordered})
    return found
