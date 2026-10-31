"""The two initial diagrams of a stage: its blocks on the fields they read
and write, cut from the undirected graph the construction builds.

The backward initial diagram holds the blocks that compute values and the
policy; the forward initial diagram holds the blocks that state the laws of
motion. They are two separate graphs, each with its own inputs and outputs,
and are never joined into one picture. The authored stage is unchanged: each
block keeps its declared inputs and outputs on its retained header, and a cut
exposes a state, shock or value the other direction supplies; a control a
block names is its coordinate and no wire.

Every step of an initial diagram stands here. At construction each block's
statements are boxes on their field wires, grouped in the bubbles of its
authored nodes and branches, and each block is a `Block` bubble on the wires
of its header (`initial_diagram_from_lines`); the undirected graph of the
whole stage holds those bubbles (`undirected_graph`), and the two diagrams
are cut from it (`cut_initial_diagrams`). A finer grain of a stored diagram
is derived when it is asked for, by opening its bubbles
(`initial_diagram_grains`). A function that reads the wire table of
`wire_sorts.py` takes it as its first argument, `wires`.
"""

from __future__ import annotations

from typing import NamedTuple

from discopy.frobenius import Box, Bubble, Ty

from bellman.fold.block_lines import (
    block_coordinates,
    block_direction,
    blocks,
    blocks_of,
    header_of,
    header_wire_sorts,
    node_address,
    property_owners,
    unread_inputs_of,
    working_hypergraph,
)
from bellman.fold.stage_names import lines_of
from bellman.graphs.wire_sorts import WiredBox, connect, group_inputs_outputs, needed, wired_boxes
from bellman.native.hypergraphs import BellmanHypergraph, Block, freeze_native
from bellman.native.identity import Identity, box_identity, piece_identity
from bellman.native.records import BlockHeader, InitialDiagrams, Sort, with_identity
from bellman.native.versions import StageVersion, stored
from bellman.refusals import NotConstructed
from bellman.syntax.vocabulary import VALUE_ROLES

# --- the grains and the records of a block ---

# the five grains of either kind of graph
GRAINS = ("builder", "primitive", "node", "combined", "factored")


class BlockParts(NamedTuple):
    """One block of an initial diagram as `initial_diagram_at_grains` reads it:
    the block's box or stored bubble, its statement boxes, the groups of its
    authored nodes and branches by address, and the identities of its input
    and output wires."""

    block: object
    boxes: list
    groups: dict
    inputs: tuple
    outputs: tuple


class NodeGroup(NamedTuple):
    """The statements of one authored node or one branch of a nested block:
    the identity of its bubble and the addresses of its lines."""

    identity: object
    addresses: list


# --- the initial diagrams at construction ---


def initial_diagram_from_lines(wires, direction, grains=GRAINS):
    """The graphs of a direction's initial diagram at construction, from the
    typed lines of the working stage: every statement a box on its field
    wires, the authored nodes grouped (`statement_boxes`), each block on
    exactly the wires of its header."""
    declared_in, declared_out = initial_diagram_inputs_and_outputs(wires, direction)
    per_builder = {}
    for box in blocks_of_direction(wires, direction):
        boxes, groups = statement_boxes(wires, box)
        dom, cod = _header_wires(wires, box)
        per_builder[box.name] = BlockParts(
            block=box, boxes=boxes, groups=groups, inputs=dom, outputs=cod
        )
    return initial_diagram_at_grains(
        wires, per_builder, declared_in=declared_in, declared_out=declared_out, grains=grains
    )


def initial_diagram_inputs_and_outputs(wires, direction):
    """The inputs and outputs of the initial diagram of a direction: the
    stored diagram of a `StageVersion`, the cut of the `WorkingStage` while the
    stage is constructed."""
    if wires.initial is None:
        wires.initial = (
            stored(wires.stage, "initial")
            if isinstance(wires.stage, StageVersion)
            else cut_initial_diagrams(wires.stage)
        )
    graph = getattr(wires.initial, direction)
    return (
        tuple(ob.identity for ob in graph.dom.inside),
        tuple(ob.identity for ob in graph.cod.inside),
    )


def blocks_of_direction(wires, direction):
    """The blocks of a direction's initial diagram, in file order; refused
    when the direction has none."""
    selected = []
    for box in wires.blocks:
        if box.name in wires.refusals:
            raise wires.refusals[box.name]
        if wires.direction[box.name] == direction:
            selected.append(box)
    if not selected:
        raise NotConstructed(
            f"no builder of the initial {direction} view",
            stage=wires.name,
            address="stage",
            rule="not-constructed",
        )
    return selected


# the roles of the names a line reads that are no wire of an initial diagram
WIRE_ROLES_EXCLUDED = ("parameter", "function", "argument")


def statement_boxes(wires, box):
    """Every statement of a block as a box on its resolved field wires
    (parameters and functions are not wires), and the authored nodes and the
    branches of a nested block as groups of addresses, each with the identity
    of its bubble. A line marked `!doc` and a line a dotted id attaches to
    another line as its property form no box. A control the block's header
    names among its inputs is the coordinate the line is read at and is no
    input of the line's box, so a line whose only field input is such a
    control reads no wire at all.

    A shock a line reads that the block's header does not list — ν of
    `Ψ ~ LogNormal(ν, σ_Ψ)`, which the sub-block that integrates Ψ reads
    through that distribution — is a coordinate at which the line is read
    and a wire of no initial diagram at any grain, as a control the header
    names is. The block integrates the shock within itself and no box of the
    diagram writes it, so it stands among the coordinates of the function the
    line defines, `𝐶𝐸(m_d, c, ν)`, and on no wire with one end."""
    held = tuple(lines_of(wires.stage, box))
    coordinates = _coordinates_of_lines(wires, box, held)
    properties = property_owners(record.address for _, record in held)
    boxes, groups = [], {}
    for holder, record in held:
        if record.role == "doc" or record.address in properties:
            continue
        boxes.append(_line_box(wires, record, coordinates))
        if holder is not box:
            address = node_address(holder)
            groups.setdefault(address, NodeGroup(piece_identity(address), [])).addresses.append(
                record.address
            )
        elif Identity("line", address=record.address).branch is not None:
            # a line of a nested block stands in its branch's bubble, an
            # authored block and no sub-block
            nested = record.address.rsplit(".", 1)[0]
            groups.setdefault(
                nested, NodeGroup(Identity("block", address=nested), [])
            ).addresses.append(record.address)
    return boxes, groups


def _coordinates_of_lines(wires, box, held):
    """The coordinates at which the lines `held` of a block are read, which
    are wires of no initial diagram: the controls the block's header names
    among its inputs, and each shock a line reads that the header does not
    list."""
    coordinates = set(block_coordinates(box, wires.ports))
    listed = {sort.identity for side in header_of(box) for sort in side}
    for _, record in held:
        for port in record.inputs:
            if port.role == "shock" and port.identity not in listed:
                coordinates.add(port.identity)
    return coordinates


def _line_box(wires, record, coordinates):
    """One typed line of a block as a box on the field wires it reads and
    writes, less the `coordinates` at which it is read; the sort of a local
    value it names is added to the wire table where none is held."""
    if record.core is None:
        raise NotConstructed(
            f"statement {record.address} has no retained equation",
            stage=wires.name,
            address=record.address,
            rule="not-constructed",
        )
    outputs = {o.identity for o in record.outputs}
    ins = tuple(
        dict.fromkeys(
            p.identity
            for p in record.inputs
            if p.role not in WIRE_ROLES_EXCLUDED
            and p.identity.kind != "function"
            and p.identity not in outputs
            and p.identity not in coordinates
        )
    )
    outs = tuple(p.identity for p in record.outputs)
    for port in tuple(record.inputs) + tuple(record.outputs):
        # a local value the typing pass resolved is a wire of the block's
        # interior; its sort is built only where none is held, since an
        # identity carries one typing, and the wire's own sort, which carries
        # its declared set, is the first
        if port.identity not in wires.sorts:
            wires.sorts[port.identity] = Sort(
                port.identity, "field", perch=port.perch, role=port.role
            )
    return WiredBox(
        with_identity(
            Box(record.address, wires.tensor_of_sorts(ins), wires.tensor_of_sorts(outs), data=()),
            Identity("line", address=record.address),
        ),
        ins,
        outs,
    )


def _header_wires(wires, box):
    """The identities of a block's input and output wires in an initial
    diagram: those its header declares, less the controls it names among its
    inputs, which are coordinates."""
    coordinates = set(block_coordinates(box, wires.ports))
    header_in, header_out = header_of(box)
    return (
        tuple(ob.identity for ob in header_in if ob.identity not in coordinates),
        tuple(ob.identity for ob in header_out),
    )


def initial_diagram_at_grains(wires, per_builder, *, declared_in, declared_out, grains):
    """The graphs of an initial diagram at the given grains, from the parts
    of each block (`BlockParts`): its statement boxes, its node groups and
    its inputs and outputs."""
    inputs, outputs = declared_in, declared_out
    graphs = {}
    for grain in grains:
        outer = []
        for box, boxes, groups, dom, cod in per_builder.values():
            grouped = (
                grouped_statements(wires, boxes, groups, exported=cod, grain=grain)
                if grain != "primitive"
                else boxes
            )
            if grain == "builder":
                outer.append(
                    WiredBox(block_bubble(wires, box, grouped, inputs=dom, outputs=cod), dom, cod)
                )
            else:
                outer.extend(grouped)
        if grain == "combined":
            outer = needed(outer, outputs)
        graphs[grain] = connect(wires, outer, inputs=inputs, outputs=outputs)
    return graphs


def grouped_statements(wires, boxes, groups, *, exported=(), grain="node"):
    """Statement boxes with each authored node's statements enclosed in a
    node bubble, and each branch's in a bubble of kind `block`, on the
    wires the group consumes and produces; at the
    factored grain a statement carrying an operator occurrence (a method
    target) stands beside its node."""
    if not groups:
        return boxes
    membership = {
        address: name for name, (_, addresses) in groups.items() for address in addresses
    }
    if grain == "factored":
        with_operators = {
            record.address
            for box in wires.blocks
            for _, record in lines_of(wires.stage, box)
            if record.operators
        }
        targets = {b.name for b, _, _ in boxes if b.name in with_operators}
        membership = {a: n for a, n in membership.items() if a not in targets}
        groups = {
            name: NodeGroup(identity, [a for a in addresses if a not in targets])
            for name, (identity, addresses) in groups.items()
        }
        groups = {name: group for name, group in groups.items() if group.addresses}
    out, emitted = [], set()
    for entry in boxes:
        name = membership.get(entry.box.name)
        if name is None:
            out.append(entry)
            continue
        if name in emitted:
            continue
        emitted.add(name)
        identity, addresses = groups[name]
        members = [entry for entry in boxes if entry.box.name in addresses]
        outside = [entry for entry in boxes if entry.box.name not in addresses]
        dom, cod = group_inputs_outputs(members, outside, exported)
        interior = connect(wires, members, inputs=dom, outputs=cod)
        out.append(
            WiredBox(
                with_identity(
                    Block(
                        interior.to_diagram(),
                        name=name,
                        dom=wires.tensor_of_sorts(dom),
                        cod=wires.tensor_of_sorts(cod),
                        data=(),
                    ),
                    identity,
                ),
                dom,
                cod,
            )
        )
    return out


def block_bubble(wires, box, grouped, *, inputs, outputs):
    """A block of an initial diagram as a native `Block` bubble around its
    statement graph, carrying the header the author wrote; the stored
    bubble of a constructed stage keeps its interior and its header as they
    are."""
    if isinstance(box, Bubble):
        return with_identity(
            Block(
                box.arg,
                name=box.name,
                dom=wires.tensor_of_sorts(inputs),
                cod=wires.tensor_of_sorts(outputs),
                data=box.data,
            ),
            piece_identity(box.name),
        )
    header = BlockHeader(inputs=tuple(header_of(box).inputs), unread=tuple(unread_inputs_of(box)))
    interior = connect(wires, grouped, inputs=inputs, outputs=outputs)
    return with_identity(
        Block(
            interior.to_diagram(),
            name=box.name,
            dom=wires.tensor_of_sorts(inputs),
            cod=wires.tensor_of_sorts(outputs),
            data=header,
        ),
        piece_identity(box.name),
    )


# --- the undirected graph and the cut ---


def undirected_graph(stage, bubbles, wires=None):
    """The undirected graph of the whole stage, the working object the two
    initial diagrams are cut from: the working stage's hypergraph with every
    block a native ``Block`` bubble around its statement graph, keeping the
    authored outer signature and the original wiring, every bubble on the
    wires of its block's header, and a block no direction contains with its
    bubble on its declared inputs and outputs. It is not stored on the stage
    and is never drawn."""
    boxes = []
    for source in blocks_of(stage):
        bubble = bubbles.get(source.name)
        if bubble is None and wires is not None:
            try:
                bubble = undirected_block_bubble(wires, source)
            except NotConstructed:
                bubble = None
        if bubble is None:
            boxes.append(source)
            continue
        if (bubble.dom, bubble.cod) != (source.dom, source.cod):
            bubble = with_identity(
                Block(
                    bubble.arg, name=bubble.name, dom=source.dom, cod=source.cod, data=bubble.data
                ),
                piece_identity(bubble.name),
            )
        boxes.append(bubble)
    original = working_hypergraph(stage)
    return freeze_native(
        BellmanHypergraph(
            dom=original.dom,
            cod=original.cod,
            boxes=tuple(boxes),
            wires=original.wires,
            spider_types=original.spider_types,
            offsets=original.offsets,
        )
    )


def undirected_block_bubble(wires, box):
    """The bubble of a block neither initial diagram contains, on the wires
    its header declares less the controls it names as coordinates."""
    boxes, groups = statement_boxes(wires, box)
    dom, cod = _header_wires(wires, box)
    return block_bubble(
        wires, box, grouped_statements(wires, boxes, groups, exported=cod), inputs=dom, outputs=cod
    )


def cut_initial_diagrams(stage, graph=None):
    """The two initial diagrams of a `WorkingStage`, cut from its undirected
    graph: the backward blocks on one graph and the forward blocks on another,
    each holding the very block boxes of the graph it is cut from. `graph` is
    that undirected graph; by default the `WorkingStage`'s own hypergraph,
    whose boxes carry no interior, and at construction the graph whose blocks
    are the `Block` bubbles.

    A cut exposes state, shock or value fields required from the other
    direction. A policy control is an output of the backward diagram and an
    input of no block: a control a block names among its inputs is the
    coordinate at which its lines are read, so the cut drops that incidence and
    retains the authored header on the block's box. The
    direction of each block is read from the original box, before the cut.
    """
    authored, ports = blocks(stage), header_wire_sorts(stage)
    graph = working_hypergraph(stage) if graph is None else graph
    indices = {box.name: index for index, box in enumerate(graph.boxes)}
    selected = {"forward": [], "backward": []}
    for box in authored:
        selected[block_direction(stage, box, ports)].append(indices[box.name])
    graph = _without_coordinates(graph, ports)
    forward = _subgraph(graph, selected["forward"], _wire_priority(ports, "forward"))
    backward = _subgraph(graph, selected["backward"], _wire_priority(ports, "backward"))
    return InitialDiagrams(backward=freeze_native(backward), forward=freeze_native(forward))


def _without_coordinates(graph, ports):
    """The same graph with every block's control inputs dropped, the header
    retained on each box that loses one. A control a block
    names among its inputs is the coordinate at which the block's lines are
    read, so the box has no input wire for it and the diagram's inputs and
    outputs are computed without that incidence."""
    boxes, box_wires, reduced = [], [], False
    for box, (ins, outs) in zip(graph.boxes, graph.box_wires):
        declared = tuple(box.dom.inside)
        coordinates = set(block_coordinates(box, ports))
        keep = tuple(
            index for index, sort in enumerate(declared) if sort.identity not in coordinates
        )
        if len(keep) == len(declared):
            boxes.append(box)
            box_wires.append((ins, outs))
            continue
        reduced = True
        boxes.append(
            _on_domain(box, Ty(*(declared[index] for index in keep)), _retained_header(box))
        )
        box_wires.append((tuple(ins[index] for index in keep), outs))
    if not reduced:
        return graph
    return BellmanHypergraph(
        dom=graph.dom,
        cod=graph.cod,
        boxes=tuple(boxes),
        wires=(graph.dom_wires, tuple(box_wires), graph.cod_wires),
        spider_types=graph.spider_types,
    )


def _on_domain(box, inputs, data):
    """The same block box on a smaller domain, keeping its interior and its
    name and carrying the retained header. DisCoPy refuses a box whose input
    wires do not match its domain, so dropping a control incidence means a new
    box."""
    if isinstance(box, Block):
        return with_identity(
            Block(box.arg, name=box.name, dom=inputs, cod=box.cod, data=data), box.identity
        )
    return with_identity(Box(box.name, inputs, box.cod, data=data), box.identity)


def _retained_header(box):
    """The header to retain on a block whose box loses a control input: the
    record the box already carries, kept as the same object so that two boxes
    built from it stay equal, or the sorts the author declared, which the
    reduced box no longer carries."""
    data = getattr(box, "data", None)
    if isinstance(data, BlockHeader):
        return data
    return BlockHeader(header_of(box).inputs, unread=tuple(unread_inputs_of(box)))


def _wire_priority(ports, direction):
    """The key that orders the inputs or the outputs of the diagram cut for
    `direction`, given the spider type of a wire and its side, `input` or
    `output`: first the fields that begin or end the direction, the states at
    arrival for the forward inputs and the value fields at arrival for the
    backward outputs, the continuation perch on the other side; then every
    other field, each in the order of `ports`; then a wire that is no
    field."""
    field_order = {identity: index for index, identity in enumerate(ports)}

    def priority(typ, side):
        port = ports.get(typ.inside[0].name)
        if port is None:
            return 1, len(field_order)
        perch = (
            "arvl"
            if (direction, side) in (("forward", "input"), ("backward", "output"))
            else "cntn"
        )
        role = {"state"} if direction == "forward" else VALUE_ROLES
        return (0 if port.perch == perch and port.role in role else 1), field_order[port.identity]

    return priority


def _subgraph(graph, selected, wire_priority=None):
    """The subgraph of `graph` that holds the boxes at the indices
    `selected`: its inputs are the wires those boxes read that none of them
    writes, or that the graph or a box outside writes, and its outputs the
    wires they write that none of them reads, or that the graph or a box
    outside reads; each side ordered by `wire_priority`, then by the wire's
    first appearance."""
    selected = tuple(selected)
    selected_set = set(selected)
    box_wires = tuple(graph.box_wires[index] for index in selected)
    consumed = {wire for inputs, _ in box_wires for wire in inputs}
    produced = {wire for _, outputs in box_wires for wire in outputs}
    outside_reads = {
        wire
        for index, (inputs, _) in enumerate(graph.box_wires)
        if index not in selected_set
        for wire in inputs
    }
    outside_writes = {
        wire
        for index, (_, outputs) in enumerate(graph.box_wires)
        if index not in selected_set
        for wire in outputs
    }
    inputs = (consumed - produced) | (consumed & (set(graph.dom_wires) | outside_writes))
    outputs = (produced - consumed) | (produced & (set(graph.cod_wires) | outside_reads))
    ranking = {wire: index for index, wire in enumerate(dict.fromkeys(graph.flat_wires))}
    sort = lambda wires, side: tuple(
        sorted(
            wires,
            key=lambda wire: (
                (wire_priority(graph.spider_types[wire], side) if wire_priority else 0),
                ranking[wire],
            ),
        )
    )
    dom, cod = sort(inputs, "input"), sort(outputs, "output")
    boxes = tuple(graph.boxes[index] for index in selected)
    included = inputs | outputs | consumed | produced
    types = {wire: graph.spider_types[wire] for wire in included}
    result = BellmanHypergraph(
        dom=Ty().tensor(*(graph.spider_types[wire] for wire in dom)),
        cod=Ty().tensor(*(graph.spider_types[wire] for wire in cod)),
        boxes=boxes,
        wires=(dom, box_wires, cod),
        spider_types=types,
    )
    return result


# --- the finer grains of a stored diagram ---


def initial_diagram_grains(wires, direction, grains=GRAINS):
    """The graphs of a direction's initial diagram, derived from its
    stored graph: at the builder grain the blocks of the
    direction, each block's bubble on the inputs and outputs of its
    header; the other grains open the bubbles: the
    primitive grain every bubble,
    with the statements in the order of the lines; the sub-builder grain
    (`node`) the blocks, keeping the sub-blocks; the combined grain the boxes
    an output depends on; the factored grain a statement carrying an operator
    beside its node."""
    stored = {box.name: box for box in blocks_of(wires.stage)}
    declared_in, declared_out = initial_diagram_inputs_and_outputs(wires, direction)
    per_builder = {}
    for box in blocks_of_direction(wires, direction):
        bubble = stored[box.name]
        interior = BellmanHypergraph.from_diagram(bubble.arg)
        entries = wired_boxes(interior)
        groups = {}
        for part, _, _ in entries:
            # every bubble inside a block, an authored node or a branch,
            # regrouped with its identity: the node grain keeps it closed
            # and the primitive grain opens it
            if isinstance(part, Bubble):
                groups[part.name] = NodeGroup(
                    box_identity(part),
                    [
                        inner.name
                        for inner, _, _ in wired_boxes(BellmanHypergraph.from_diagram(part.arg))
                    ],
                )
        dom = tuple(ob.identity for ob in interior.dom.inside)
        cod = tuple(ob.identity for ob in interior.cod.inside)
        order = {
            record.address: index for index, (_, record) in enumerate(lines_of(wires.stage, box))
        }
        per_builder[box.name] = BlockParts(
            block=bubble, boxes=opened(entries, order), groups=groups, inputs=dom, outputs=cod
        )
    return initial_diagram_at_grains(
        wires, per_builder, declared_in=declared_in, declared_out=declared_out, grains=grains
    )


def opened(entries, order):
    """The statement boxes of a block's interior with every bubble inside
    it opened, in the order of the lines."""
    flat = []
    for entry in entries:
        if isinstance(entry.box, Bubble):
            flat.extend(opened(wired_boxes(BellmanHypergraph.from_diagram(entry.box.arg)), order))
        else:
            flat.append(entry)
    return sorted(flat, key=lambda entry: order[entry.box.name])
