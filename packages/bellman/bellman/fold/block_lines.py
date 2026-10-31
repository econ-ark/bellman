"""The blocks of a stage and what their headers declare, read from the
`WorkingStage` during construction and from the stage version, a
`StageVersion`, afterwards.

A block is the authored group of lines that denotes one builder. This module
reads the blocks in file order, the direction of each, the inputs and outputs
its header declares (`DeclaredSides`) and the coordinate it is read at; the
sort of every wire, the fields with the edge that draws each shock and the
pairings of the marginal values; the declared set of every parameter and the
symbol groups; the forward chain between two perches; the holder a line
stands in; the lines a dotted id attaches to another line; and the lines
marked `!doc`. The lines themselves, whose roles and operator occurrences are
read with the names of the stage, are read in `fold/stage_names.py`.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import NamedTuple

from discopy.frobenius import Bubble

from bellman.distributions.edges import drawn_edges
from bellman.native.hypergraphs import BellmanHypergraph, Block
from bellman.native.identity import Identity
from bellman.native.records import BlockData, BlockHeader, NodeData, Refusal, Sort, setting_names
from bellman.native.versions import StageVersion, WorkingStage, stored
from bellman.refusals import ConstructionError, NotConstructed
from bellman.syntax.vocabulary import (
    CONTROL,
    PERCHES,
    SHCK,
    SHOCK,
    STATE,
    VALUE,
    VALUE_ROLES,
)

# --- the stage and its blocks ---


def require_stage(stage) -> None:
    """The check that `stage` is an `ElaboratedStage`, a `StageVersion`, or the
    `WorkingStage` of a construction in progress, the only other value a query
    reads a stage from; a `TypeError` otherwise."""
    if not isinstance(stage, (StageVersion, WorkingStage)):
        raise TypeError(
            f"expected an ElaboratedStage, the stage make_stage returns; got "
            f"{type(stage).__name__}"
        )


def blocks(stage):
    """The blocks of a stage in file order, the stage checked first and every
    block required to be an authored block's box."""
    require_stage(stage)
    blocks = blocks_in_file_order(stage)
    if any(not (isinstance(box.data, BlockData) or isinstance(box, Block)) for box in blocks):
        _fail(stage, "stage", "an initial diagram requires the authored block boxes")
    return blocks


def blocks_in_file_order(stage):
    """The blocks of a stage in file order: the `WorkingStage`'s own
    `block_order` while the stage is constructed; on a `StageVersion`,
    `blocks_of`, which orders them by the `line` records of the
    definitions table."""
    boxes = blocks_of(stage)
    if isinstance(stage, StageVersion):
        return boxes
    order = stage.data.get("block_order")
    actual = {box.name: box for box in boxes}
    if (
        not isinstance(order, tuple)
        or not all(isinstance(name, str) for name in order)
        or len(order) != len(set(order))
        or set(order) != set(actual)
        or len(actual) != len(boxes)
    ):
        raise NotConstructed(
            "missing or malformed authored block_order (I18)",
            stage=stage.name,
            address="stage",
            rule="not-constructed",
        )
    return tuple(actual[name] for name in order)


def blocks_of(stage):
    """Every block of the stage as its `Block` bubble, in file order: the boxes
    of the `WorkingStage`'s hypergraph while the stage is constructed; on a
    `StageVersion`, the boxes of the two initial diagrams, each block in
    exactly one of them, ordered by the `line` records of the
    definitions table, which hold the lines in file order, a block that
    holds no line after them."""
    if not isinstance(stage, StageVersion):
        return tuple(stage.hypergraph.boxes)
    record = stored(stage, "initial")
    found = {}
    for direction in ("backward", "forward"):
        graph = getattr(record, direction)
        if isinstance(graph, Refusal):
            continue
        for box in graph.boxes:
            found.setdefault(box.name, box)
    for box in record.refused_blocks:
        found.setdefault(box.name, box)
    named = dict.fromkeys(d.identity.block for d in stage.definitions.values() if d.kind == "line")
    ordered = [found[name] for name in named if name in found]
    return tuple(ordered + [box for name, box in found.items() if name not in named])


def _fail(stage, address, message):
    """The refusal `not-constructed` of a block the initial diagrams cannot
    hold."""
    raise NotConstructed(message, stage=stage.name, address=address, rule="not-constructed")


def working_hypergraph(stage):
    """The undirected graph of the whole stage, a working object of the
    construction only: the `WorkingStage`'s own hypergraph, every block a
    bubble around its statement graph, from which the two initial diagrams
    are cut. It is not an attribute of the constructed stage and is never
    drawn or printed (AMD-SG-010 §1); a `StageVersion` answers `blocks_of`."""
    if isinstance(stage, StageVersion):
        raise TypeError(
            "the undirected stage graph is a working object of the "
            "construction; a constructed stage holds the backward and the "
            "forward initial diagram, and its blocks are blocks_of(stage)"
        )
    return stage.hypergraph


def block_direction(stage, box, ports):
    """The direction of a block, `backward` or `forward`, read from the roles
    of its outputs and the perches its sides relate; refused where no rule
    assigns one."""
    controls = _outputs(box, ports, {"control"})
    values = _outputs(box, ports, VALUE_ROLES)
    states = _outputs(box, ports, {"state"})
    before, after = perches_of(box, ports)
    if states and (values or controls):
        _fail(
            stage,
            box.name,
            "a block whose outputs mix states with values or controls belongs to "
            "neither initial diagram",
        )
    if controls and all(port.perch == "dcsn" for port in controls):
        return "backward"
    if values and before in PERCHES and after in PERCHES:
        if PERCHES.index(before) > PERCHES.index(after):
            return "backward"
    if states and before in PERCHES and after in PERCHES:
        if PERCHES.index(before) < PERCHES.index(after):
            return "forward"
    _fail(
        stage,
        box.name,
        "no rule assigns this block to the backward or the forward initial "
        "diagram: its output roles and its declared input and output perches match none",
    )


def _outputs(box, ports, role):
    """The sorts of a block's outputs whose role is one of `role`."""
    return tuple(
        ports[identity]
        for identity in _identities(box.cod)
        if identity in ports and ports[identity].role in role
    )


def _identities(typ):
    """The names of the wires on one side of a box, which are their
    identities."""
    return tuple(ob.name for ob in typ.inside)


# --- what a block's header declares ---


def header_of(box):
    """The inputs and outputs a block's header declares, as two tuples of
    sorts: the retained `BlockHeader` where the box carries one, and the box's
    own wires otherwise. A block of an initial diagram has no input wire for a
    control its header names, so its declared inputs are read from the retained
    record (AMD-SG-013 §3). The declared outputs are the box's own wires on
    every block — the cut reduces the domain alone — so they are read from the
    box and the record does not hold them (AMD-SG-014 §2)."""
    data = getattr(box, "data", None)
    if isinstance(data, BlockHeader):
        return DeclaredSides(inputs=data.inputs, outputs=tuple(box.cod.inside))
    return DeclaredSides(inputs=tuple(box.dom.inside), outputs=tuple(box.cod.inside))


def unread_inputs_of(box):
    """The sorts of the value inputs a block's header lists and no line of
    the block reads, in header order (AAS, 17 October 2026): held by the
    retained `BlockHeader` on a block of an initial diagram and by the
    working `BlockData` on a builder box under construction, and none on any
    other box. They are no inputs of the block, so `header_of` does not
    answer them; the stage records each as a diagnostic."""
    data = getattr(box, "data", None)
    if isinstance(data, BlockHeader):
        return data.unread
    if isinstance(data, BlockData):
        return data.unread_inputs
    return ()


class DeclaredSides(NamedTuple):
    """The two sides a block's header declares, its inputs and its outputs,
    as sorts (`header_of`) or as their identities
    (`wire_terms.header_identities`)."""

    inputs: tuple
    outputs: tuple


def block_coordinates(box, ports):
    """The identities of the controls a block's header names among its inputs:
    the coordinates at which the block's lines are read, and wires of no
    initial diagram at any grain (AMD-SG-013 §3). The rule is written here and
    nowhere else: the cut, the line boxes, the block's interior and the
    printed card all call this function."""
    inputs, _ = header_of(box)
    return tuple(
        sort.identity
        for sort in inputs
        if sort.identity in ports and ports[sort.identity].role == "control"
    )


def perches_of(box, ports):
    """The perches related by a builder's value or state fields.

    Value inputs determine a backward builder's source perch. State and
    control inputs can also name the coordinates at which it is evaluated.
    Their own perches remain on their wires and do not change that source.
    """
    declared_in, declared_out = header_of(box)
    inputs = tuple(sort.identity for sort in declared_in)
    outputs = tuple(sort.identity for sort in declared_out)
    value_inputs = tuple(i for i in inputs if i in ports and ports[i].role in VALUE_ROLES)
    if value_inputs and any(
        i in ports and ports[i].role in VALUE_ROLES + (CONTROL,) for i in outputs
    ):
        return side_perch(value_inputs, ports), side_perch(outputs, ports)
    data = box.data
    if isinstance(data, BlockData):
        return data.perch_from, data.perch_to
    return side_perch(inputs, ports), side_perch(outputs, ports)


def side_perch(identities, ports):
    """The perch of one side of a block, read from its wires: the one perch
    of its fields other than shocks and controls; the decision perch when only
    controls place it; None when nothing does."""
    perches = {
        ports[i].perch
        for i in identities
        if i in ports and ports[i].role not in (SHOCK, CONTROL) and ports[i].perch != SHCK
    }
    if len(perches) == 1:
        return next(iter(perches))
    if not perches and any(i in ports and ports[i].role == "control" for i in identities):
        return "dcsn"
    return None


# --- the wires and the fields ---


def header_wire_sorts(stage):
    """The sort of every field wire by identity (AMD-SG-006 §3): the fields
    and the shocks the block headers list, in first-listing order, that is
    the builders in file order and each builder's inputs then its outputs.
    The `WorkingStage`'s own table while the stage is constructed; on a
    `StageVersion`, the wires of the blocks of the two initial diagrams.

    These are the wires. `fields()` answers these and, besides them, a shock
    the file declares and no header lists (AMD-SG-021 §4.1), which is no wire
    of any block and belongs in no table of wires."""
    if not isinstance(stage, StageVersion):
        return dict(stage.field_sorts)
    return _wire_sorts_of_headers(stage)


def _wire_sorts_of_headers(stage):
    """The sort of every field wire the block headers list, by identity, in
    first-listing order: the builders in file order and each builder's inputs
    then its outputs."""
    found = {}
    for box in blocks_in_file_order(stage):
        declared_in, declared_out = header_of(box)
        for sort in declared_in + declared_out:
            found.setdefault(sort.identity, sort)
    return found


def wire_sorts(stage):
    """The sort of every wire of the stage: the field wires of
    `header_wire_sorts`, then the local wires inside each builder and inside
    each of its authored nodes (the aliases a `!node` line defines or a node's
    slice holds): the `WorkingStage`'s own table while the stage is
    constructed, and on a `StageVersion` the wires of its blocks' bubbles."""
    if not isinstance(stage, StageVersion):
        return dict(stage.sorts)
    found = header_wire_sorts(stage)
    pending = [box for box in blocks_in_file_order(stage) if isinstance(box, Bubble)]
    while pending:
        bubble = pending.pop(0)
        for typ in BellmanHypergraph.from_diagram(bubble.arg).spider_types:
            for sort in typ.inside:
                found.setdefault(sort.identity, sort)
        pending.extend(part for part in bubble.arg.boxes if isinstance(part, Bubble))
    return found


def fields_of(stage):
    """What `fields()` answers, as two mappings: the sort of every field
    wire by identity, in first-listing order, followed by the declared shocks
    no header lists, then the multipliers the block bodies declare, which no
    header lists either; and the edge that draws each shock, as the pair of
    perches of the transition that draws it."""
    require_stage(stage)
    found = _wire_sorts_of_headers(stage)
    edges = shock_edges(stage, found)
    sets = _declared_shock_sets(stage)
    for identity in edges:
        if identity not in found:
            found[identity] = Sort(
                identity, "field", perch=SHCK, role="shock", domain=sets.get(identity.field)
            )
    for identity, sort in multiplier_sorts(stage).items():
        found.setdefault(identity, sort)
    return found, edges


def shock_edges(stage, ports):
    """The edge that draws each shock the file declares, as the pair of
    perches of the forward builder it is drawn on: `('arvl', 'dcsn')` for a
    shock the arrival block lists among its inputs, `('dcsn', 'cntn')` for one
    the decision block lists. A shock is a random variable supplied on an edge
    between two perches, available at the later perch and not assumed known
    earlier (Appendix C §1.1; `docs/overview/03-language.md` §2.2), so the
    edge and not a perch is what the stage knows about it.

    A shock no block lists is drawn where the shocks its declaration is
    connected with are drawn: `ν` of `sa_savings.bl`, which the law of `Ψ`
    reads and `E_{ν}` integrates, and `z` of `(y, z) ~ N(…)` where a forward
    builder lists `y` alone. The assignment is the one composition
    `distributions.edges.drawn_edges`, which the fold reads for the edges of
    its plan (AMD-SG-009 §2), so `fields()` prints the edge the construction
    drew on. The answer is in declaration order, the subjects of the
    distribution declarations in file order first. The `Sort` record holds
    none of this (AMD-SG-021 §4.1, §12 item 2)."""
    perches, forward = {}, []
    for box in blocks_in_file_order(stage):
        declared_in, declared_out = header_of(box)
        before = side_perch(tuple(ob.identity for ob in declared_in), ports)
        after = side_perch(tuple(ob.identity for ob in declared_out), ports)
        if before is None or after is None:
            continue
        perches[box.name] = (before, after)
        if PERCHES.index(before) < PERCHES.index(after):
            forward.append(
                (
                    box.name,
                    tuple(
                        ob.identity.field
                        for ob in declared_in
                        if ob.identity in ports and ports[ob.identity].role == SHOCK
                    ),
                )
            )
    definitions = tuple(stage.definitions.values())
    subjects = {
        name for d in definitions if d.kind == "distribution" for name in d.equations[0].subjects
    }

    def refuse(rule, address, message):
        raise ConstructionError(message, stage=stage.name, address=address, rule=rule)

    def is_shock(name):
        sort = ports.get(_shock_identity(stage, name))
        return name in subjects or (sort is not None and sort.role == SHOCK)

    owners, _, assignment = drawn_edges(definitions, is_shock, tuple(forward), refuse)
    order = [name for owner in owners for name in owner.subjects] + list(assignment)
    found = {}
    for name in order:
        if name in assignment and assignment[name] in perches:
            found.setdefault(_shock_identity(stage, name), perches[assignment[name]])
    return found


def _shock_identity(stage, name):
    """The identity of a declared shock, `sa_savings:shck:ν`."""
    return Identity("field", stage=stage.name, perch=SHCK, field=name)


def _declared_shock_sets(stage):
    """The set each shock is declared in, by name, read from the coordinates
    of the distribution declarations that name it: `ν : ℝ` of `sa_savings.bl`,
    which stands in the declaration of `Ψ` and on no header."""
    found = {}
    for definition in stage.definitions.values():
        if definition.kind != "distribution":
            continue
        for name, term in definition.coordinates:
            if term is not None:
                found.setdefault(name, term)
    return found


def multiplier_sorts(stage):
    """The sort of each multiplier a block body declares (AMD-SG-035 §5): a
    field of the continuation perch with role `multiplier` and its declared
    set, listed on no header and so absent from `header_wire_sorts`, read from
    a `StageVersion`'s definitions table; `{}` for a `WorkingStage`, whose own
    table already holds it."""
    if not isinstance(stage, StageVersion):
        return {}
    return {
        Identity("field", stage=stage.name, perch="cntn", field=d.identity.field): Sort(
            Identity("field", stage=stage.name, perch="cntn", field=d.identity.field),
            "field",
            perch="cntn",
            role="multiplier",
            domain=d.coordinates[0][1],
        )
        for d in stage.definitions.values()
        if d.kind == "multiplier"
    }


# --- the symbol groups and the parameters ---


def symbol_groups(stage):
    """The symbol groups of a stage: the `WorkingStage`'s own table while the
    stage is constructed, and on a `StageVersion` the query `symbols`."""
    if not isinstance(stage, StageVersion):
        return stage.symbols
    return symbols(stage)


def symbols(stage):
    """The symbol groups of the stage (spec 0.3c §3.3), a query on its blocks
    and the definitions table: the named sets; the fields listed on
    the arrival input sides (`arvl_states`), the decision states, the fields
    listed on the continuation output sides (`cntn_states`), the controls,
    the shocks, the values and the marginal values, each name once in
    first-listing order; the parameters and the functions in file order; the
    setting names the attached methods reference."""
    require_stage(stage)
    table, _ = fields_of(stage)
    ports = header_wire_sorts(stage)
    builders = tuple(blocks_in_file_order(stage))

    def stem(identity):
        return identity.field

    def with_role(*roles):
        return tuple(dict.fromkeys(stem(i) for i, s in table.items() if s.role in roles))

    def side_members(perch, side):
        out = []
        for box in builders:
            declared_in, declared_out = header_of(box)
            wires = declared_in if side == "input" else declared_out
            out.extend(
                stem(ob.identity)
                for ob in wires
                if ports[ob.identity].perch == perch and ports[ob.identity].role != "shock"
            )
        return tuple(dict.fromkeys(out))

    # the shocks in declaration order: the subjects of the distribution
    # declarations in file order, then a shock listed with `!shck` and given
    # no distribution, in first-listing order
    declared = _distribution_subjects(stage)
    exogenous = tuple(
        dict.fromkeys(
            [name for subjects in declared for name in subjects] + list(with_role(SHOCK))
        )
    )
    definitions = tuple(stage.definitions.values())
    functions = tuple(
        d.identity.field
        for d in definitions
        if d.kind in ("function", "function_alias", "correspondence")
    )
    settings = []
    for method in (stage.bindings.methods or {}).values():
        settings.extend(setting_names(method.settings))
    return MappingProxyType(
        {
            "spaces": tuple(d.identity.field for d in definitions if d.kind == "set"),
            "arvl_states": side_members("arvl", "input"),
            "dcsn_states": tuple(
                dict.fromkeys(
                    stem(i) for i, s in table.items() if s.perch == "dcsn" and s.role == "state"
                )
            ),
            "cntn_states": side_members("cntn", "output"),
            "controls": with_role(CONTROL),
            "exogenous": exogenous,
            "values": with_role(VALUE),
            "parameters": tuple(parameter_sets(stage)),
            "settings": tuple(dict.fromkeys(settings)),
            "functions": functions,
        }
    )


def _distribution_subjects(stage):
    """The subjects of every distribution declaration in file order, each in
    the authored order: the laws the `WorkingStage` holds while the stage is
    constructed, and on a `StageVersion` the declarations of its definitions
    table."""
    if not isinstance(stage, StageVersion):
        return tuple(stage.law_terms)
    return tuple(
        tuple(d.equations[0].subjects)
        for d in stage.definitions.values()
        if d.kind == "distribution"
    )


def parameter_sets(stage):
    """The declared set of every parameter of the stage as a retained term,
    by name, in file order: from the `parameter` records of a `StageVersion`'s
    definitions table, or from the `WorkingStage`'s own table while the stage
    is constructed."""
    if not isinstance(stage, StageVersion):
        return dict(stage.parameter_sets)
    return {
        d.identity.field: (d.equations[0] if d.equations else None)
        for d in stage.definitions.values()
        if d.kind == "parameter"
    }


# --- the forward chain between two perches ---


def forward_chain_reads(stage, perch_from, perch_to, outputs, ports):
    """True when a forward transition block between `perch_from` and the
    later perch `perch_to` declares a wire of `outputs` among its inputs and
    every block before it on that chain exists; False otherwise."""
    if (
        perch_from not in PERCHES
        or perch_to not in PERCHES
        or PERCHES.index(perch_to) <= PERCHES.index(perch_from)
    ):
        return False
    for i in range(PERCHES.index(perch_from), PERCHES.index(perch_to)):
        block = transition_between(stage, PERCHES[i], PERCHES[i + 1], ports)
        if block is None:
            return False
        if any(ob.identity in outputs for ob in header_of(block).inputs):
            return True
    return False


def transition_between(stage, perch_from, perch_to, ports=None):
    """The unique forward builder from `perch_from` to `perch_to` with a state
    output, or None."""
    ports = ports or header_wire_sorts(stage)
    found = [
        box
        for box in blocks_of(stage)
        if perches_of(box, ports) == (perch_from, perch_to)
        and any(
            ports[i].role == "state" for i in (ob.identity for ob in box.cod.inside) if i in ports
        )
    ]
    return found[0] if len(found) == 1 else None


# --- the holder a line stands in ---


def is_node(box):
    """Whether a holder is an authored node: a construction-time node record,
    or a bubble whose identity is of kind `line`; a bubble of kind `block`, a
    nested block, is no node; a bubble with no identity is read by the dot in
    its name."""
    if isinstance(box, NodeData):
        return True
    if not isinstance(box, Bubble):
        return False
    identity = getattr(box, "identity", None)
    return identity.kind == "line" if identity is not None else "." in box.name


def node_address(holder) -> str:
    """The address of the holder a line stands in: a node record's own address
    during construction, a box's or a bubble's name afterwards."""
    return holder.node_id if isinstance(holder, NodeData) else holder.name


# The head of the `solve` an implicit statement records, a target name with a
# rule of its own.
SOLVE = "solve"


def is_implicit_solve(occurrence) -> bool:
    """Whether an occurrence is the `solve` an implicit statement records:
    head `solve` at the empty position, the statement itself and no
    sub-expression."""
    return occurrence.head == SOLVE and occurrence.position == ()


# --- the lines a dotted id attaches to another line ---


def property_owners(addresses) -> dict:
    """The line each property line of a block is attached to, by the
    property's address, in the order of `addresses`, the addresses of the
    block's lines. A line whose id is dotted, `optimality.euler`, states a
    property of the line whose id stands before the last dot, `optimality`:
    it forms no operation, no address of its own and no place for a method,
    and the row of the line it is attached to holds it. A line of a nested
    block, `dcsn_to_cntn.keep.cash_on_hand`, stands under the nested block
    and under no line, so it is no property."""
    held = tuple(addresses)
    lines = set(held)
    return {address: owner for address in held if (owner := address.rpartition(".")[0]) in lines}


# --- the lines marked `!doc` ---


def doc_lines(stage, block=None):
    """The lines marked `!doc` of a stage, or of one block: the declarations
    of what a policy builder's construction is to reach, which form no piece
    (AMD-SG-034 §3 `declared`, §11 item 1)."""
    return tuple(
        definition
        for definition in stage.definitions.values()
        if definition.kind == "line"
        and "!doc" in (definition.tags or ())
        and (block is None or definition.identity.block == block)
    )
