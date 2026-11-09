"""The graphs of a stage and their grains (AMD-SG-010 §§1, 4; AMD-SG-006 §5).

One stored graph is read by its level, `initial` or `builders`, and its
direction, `backward` or `forward`; a finer grain — the primitive operators,
the sub-builders, the combined and the factored grains — is derived from the
construction table by the wire table and kept for the version. The wiring
query `chain_order` says whether the pieces of a composite form a chain and
in what order; a bubble of one piece at a grain is `boxes.bubble_at`.

The kind of a box, the builder that holds it and the primitive operators of a
direction are read here, since each is a question about a graph. So is the
reading a row of the construction table takes beyond its kind: whether its
output is its own unknown (`is_relation`), the explicit function that
relation holds, where it holds one (`explicit_side`), and the row that
answers a wire, which for the output of an Evaluation is the row that
answers the wire the Evaluation reads (`answering_row`). What one box says
of itself is `boxes`; what the stage says is `stage_answers`.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType
from typing import NamedTuple

from discopy.frobenius import Bubble

from bellman.fold.block_lines import require_stage
from bellman.fold.stage_fold import fold_stage
from bellman.fold.stage_names import StageNames
from bellman.fold.wire_terms import term_nodes
from bellman.graphs.builders_graphs import builders_graph_by_grain
from bellman.graphs.initial_diagrams import GRAINS, initial_diagram_grains
from bellman.graphs.wire_sorts import WireTable
from bellman.native.hypergraphs import freeze_native
from bellman.native.identity import box_identity
from bellman.native.records import Refusal
from bellman.native.versions import StageVersion, kept_answer, replace_stage, stored
from bellman.refusals import NotConstructed
from bellman.stage.term_operations import relation_of
from bellman.syntax import terms as T

# --- the graphs of a stage and their grains ---

LEVELS = ("initial", "builders")
DIRECTIONS = ("backward", "forward")


# the documented spelling of the grain at which sub-builders are closed, and
# its code token
GRAIN_SPELLINGS = {"sub-builder": "node"}


def graph_of(stage, level, direction, grain="builder"):
    """One graph of the stage at a grain (AMD-SG-010 §1). `level` is `initial`
    or `builders`, `direction` `backward` or `forward`, `grain` one of
    `builder`, `primitive`, `sub-builder` (the code token `node`, the two
    being one value), `combined` and `factored`. At the builder grain the
    answer is the stored graph itself; a finer grain opens the bubbles — of a
    builders graph by the fold of the definitions table, a sub-builder's
    adjacent pointwise segments merging when it is opened (AMD-SG-005 §1a
    rule 5), of an initial diagram by the stored statement graphs — and prunes
    by AMD-SG-004 §10.4. Memoized on the stage. A graph the construction
    refused raises its `Refusal` as `NotConstructed` (AMD-SG-001 §2)."""
    require_stage(stage)
    level, direction = stored_graph_name(level, direction)
    grain = grain_token(grain)

    def compute():
        held = _stored_graph(stage, level, direction)
        if isinstance(held, Refusal):
            raise NotConstructed(held.reason, **held.diagnostic)
        if grain == "builder" and not (level == "builders" and _opened(stage, direction)):
            # the stored graph itself, the declared builders, while no
            # solution method's rows open a builder of this direction
            # (specification 0.6 §7)
            return held
        derived = (
            builders_graph_by_grain(wire_table(stage), direction, grains=(grain,))[grain]
            if level == "builders"
            else initial_diagram_grains(wire_table(stage), direction, grains=(grain,))[grain]
        )
        return freeze_native(derived)

    return kept_answer(stage, ("graph", level, direction, grain), compute)


def stored_graph_name(level, direction):
    """One stored graph named: the level `initial`, the initial diagrams, or
    `builders`, the builders graphs, and the direction `backward` or
    `forward` (AMD-SG-010 §1)."""
    if level not in LEVELS:
        raise ValueError(f"level must be 'initial' or 'builders'; got {level!r}")
    if direction not in DIRECTIONS:
        raise ValueError(
            f"the {level} graphs require direction='forward' or 'backward'; got {direction!r}"
        )
    return level, direction


def grain_token(grain):
    """The code token of a grain: `sub-builder`, the documented spelling of
    the grain at which sub-builders are closed (AMD-SG-006 §6a), is the
    token `node`; the two are one value."""
    grain = GRAIN_SPELLINGS.get(grain, grain)
    if grain not in GRAINS:
        raise ValueError(
            f"grain must be one of {GRAINS!r}; 'sub-builder' is the spelling of 'node'"
        )
    return grain


def wire_table(stage):
    """The wire table of the stage from its construction table, the operative
    one (`construction_table`), made once per stage."""
    return kept_answer(stage, "wire_table", lambda: WireTable(stage, construction_table(stage)))


def construction_table(stage):
    """The construction table of the stage's operative builders: the declared
    table (`declared_table`) while no method block is bound, and otherwise
    that table with the rows of each bound block in place of the rows of the
    builder it opens, and the block's obligations added (specification 0.6
    §7), made once per stage."""
    blocks = bound_blocks(stage)
    if not blocks:
        return declared_table(stage)
    return kept_answer(
        stage, "operative table", lambda: operative_table(declared_table(stage), blocks)
    )


def declared_table(stage):
    """The construction table of the declared builders, the rows the blocks
    of the stage file fold to, folded once per stage from the declared
    definitions table and the blocks (`stage_fold.fold_stage`): on a stage
    with bound blocks, the fold reads a version holding the definitions the
    stage file states and no block, so that a version read back from its
    pickle, which keeps no answer, folds the same rows. A binding keeps it."""

    def compute():
        if not bound_blocks(stage):
            return fold_stage(stage)
        bindings = stored(stage, "bindings")
        return fold_stage(
            replace_stage(
                stage,
                definitions=declared_definitions(stage),
                bindings=dataclasses.replace(bindings, blocks=None),
            )
        )

    return kept_answer(stage, "table", compute)


def declared_definitions(stage):
    """The definitions table the stage file states: the stage's table without
    the records the bound blocks add, and with the records they replaced."""
    table = stored(stage, "definitions")
    blocks = bound_blocks(stage)
    if not blocks:
        return table
    restored = {record.identity: record for block in blocks for record in block.replaced}
    added = {record.identity for block in blocks for record in block.definitions} - set(restored)
    return MappingProxyType(
        {
            identity: restored.get(identity, record)
            for identity, record in table.items()
            if identity not in added
        }
    )


def bound_blocks(stage):
    """The method blocks bound to the stage, each a `BoundBlock`, in the
    order they were bound; none for the stage under construction."""
    if not isinstance(stage, StageVersion):
        return ()
    blocks = stored(stage, "bindings").blocks
    return tuple(blocks.values()) if blocks else ()


def operative_table(declared, blocks):
    """The construction table `declared` with the rows of each bound block
    in place of the rows of the builder it opens, at the place those rows
    stood, the definitions the rows read added and the obligations of the
    rows after the declared ones (specification 0.6 §7; specification 0.7
    D8)."""
    rows, closed = list(declared.primitive_rows), dict(declared.sub_builder_rows)
    definitions = {record.identity: record for record in declared.definitions}
    obligations = list(declared.obligations)
    for block in blocks:
        at = next(
            (index for index, row in enumerate(rows) if row.builder == block.builder), len(rows)
        )
        rows = [row for row in rows if row.builder != block.builder]
        rows[at:at] = block.rows
        if block.sub_builder_rows:
            closed[block.builder] = block.sub_builder_rows
        else:
            closed.pop(block.builder, None)
        definitions.update((record.identity, record) for record in block.definitions)
        # a condition recorded at a declared row the method's rows replace
        # holds of no operative row, and the declared table keeps it
        removed = {row.identity for row in declared.primitive_rows if row.builder == block.builder}
        obligations = [item for item in obligations if not (item[1] and item[1][0] in removed)]
        obligations.extend(item for item in block.obligations if item not in obligations)
    return dataclasses.replace(
        declared,
        primitive_rows=tuple(rows),
        sub_builder_rows=tuple(closed.items()),
        definitions=tuple(definitions.values()),
        obligations=tuple(obligations),
    )


def _opened(stage, direction):
    """Whether a solution method's rows open a builder of `direction`, so
    that the operative builders graph of that direction is built from the
    operative rows rather than read from the stored record."""
    blocks = bound_blocks(stage)
    if not blocks:
        return False
    directions = wire_table(stage).direction
    return any(directions.get(block.builder) == direction for block in blocks)


def graph_refusal(stage, level, direction):
    """The `Refusal` held in the place of one graph of the stage, or None where
    the graph was constructed. `level` and `direction` name the graph as
    `graph_of` names it. This is the question a printed sheet asks before it
    reads a graph: a sheet states a refusal it finds, and reads the held
    record to find it rather than calling `graph_of` and catching what it
    raises. The held record is the `Refusal` of AMD-SG-006 §4."""
    require_stage(stage)
    level, direction = stored_graph_name(level, direction)
    held = _stored_graph(stage, level, direction)
    return held if isinstance(held, Refusal) else None


def stored_graph(stage, level, direction):
    """The stored graph of one level and direction, read from the version's
    own record and kept nowhere, or None where the construction refused it.
    A place is looked for in the stored graphs before any grain is derived, so
    that asking one box where it stands derives no graph of another direction
    (AMD-SG-018 §4)."""
    held = _stored_graph(stage, level, direction)
    return None if isinstance(held, Refusal) else held


def _stored_graph(stage, level, direction):
    """What the version holds in the place of one graph: the graph, or the
    `Refusal` the construction left there."""
    return getattr(stored(stage, "_builders" if level == "builders" else "initial"), direction)


# --- the boxes of a graph ---


def kind_of(box):
    """The kind segment of a box's identity or, for a wiring box, of the
    first wire's identity. A primitive operator therefore gives
    `Pullback`, `Aggregation`, `Expectation`, `Evaluation`, `Argmax`,
    `DistributionExtension`, `PolicyInsertion` or `Pushforward`; None for a
    builder, a sub-builder or a statement box; a wiring box may give a
    qualifier such as `arvl` or `function`."""
    identity = getattr(box, "identity", None)
    if identity is None:
        # a box of the wiring — a spider, a swap, a cup, a cap — which DisCoPy
        # names after the wires it joins and not after an identity; its kind
        # is the second segment of its first wire's identity (AMD-SG-016 §3)
        wires = tuple(box.dom.inside) + tuple(box.cod.inside)
        return wires[0].identity.second_segment if wires else None
    return None if identity.kind in ("block", "line") else identity.kind


def block_id_of(box):
    """The block a box belongs to: the block its identity is rooted at, and for
    a box born of a line the block of the line's address."""
    return box_identity(box).block


def operators_of(stage, direction=None):
    """The primitive operator boxes of the builders graphs in dependency order
    (AMD-SG-007 §3; AMD-SG-010 §2): with no direction those of the backward
    graph and then of the forward graph, a graph the construction refused being
    skipped; with `'backward'` or `'forward'` those of that one graph, whose
    refusal is raised. Any other argument is refused. A box's kind is
    `kind_of(box)`, its builder `block_id_of(box)`, its wires `box.dom` and
    `box.cod`, its references `box.data`."""
    require_stage(stage)
    if direction is not None and direction not in DIRECTIONS:
        raise ValueError(
            f"operators_of reads no direction, 'backward' or 'forward'; got {direction!r}; the "
            "boxes of one builder are those whose block_id_of(box) names it"
        )
    boxes = []
    for selected in DIRECTIONS if direction is None else (direction,):
        try:
            graph = graph_of(stage, "builders", selected, "primitive")
        except NotConstructed:
            if direction is not None:
                raise
            continue
        boxes.extend(box for box in graph.boxes if is_primitive_operator(box))
    return tuple(boxes)


def is_primitive_operator(box):
    """Whether a box is a primitive operator: a box, not a bubble, whose data
    are references and whose name carries an operator kind."""
    return (
        not isinstance(box, Bubble)
        and isinstance(getattr(box, "data", None), tuple)
        and kind_of(box) is not None
    )


# --- the reading of a row beyond its kind ---


def is_relation(row):
    """Whether a row's output is its own unknown: the row states a relation
    its output satisfies, and does not map its inputs to its output. Such a
    row carries the unknowns its relation is solved for, `row.unknowns`: an
    inequality or a complementarity on a candidate, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>])
    ⟂ a >= 0`; a line holding its output on both sides, `𝑑𝑢(c) = dV[>]`; a
    joint solve; the identification of the policy with its candidate,
    `c = c[>]`. A row of an explicit line carries none. An `Argmax` row
    carries its controls and is no relation: it is read by its own
    definition, and every query that reads a row by its kind tests the kind
    `Argmax` first, then this predicate, then the other kinds."""
    return bool(row.unknowns) and row.kind != "Argmax"


def explicit_side(stage, row):
    """The explicit function a relation holds, as the side of its line that
    stands against the output's name alone: `𝑑𝑢𝑖𝑛𝑣(dV[>])` of
    `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0`, with or without the clause. The row
    is a relation (`is_relation`) of kind `Aggregation`, which reads its
    inputs at the point of its own output, with one output, one authored
    line and one map, the map being that side folded; one side of the line
    is the output's name alone and the other is closed: it names no unknown
    of the row and holds no `solve` and no `argmax`. None where no side is
    explicit: the identification, a `Pullback`, reads the policy at the
    grid point and not at its own point; a joint solve names its unknowns
    under `solve`; a line holding its output on both sides, `𝑑𝑢(c) =
    dV[>]`, has no closed side. The relation itself, its clause included,
    is the row's rule; this function is the part of it an operator computes
    (`kernels.compile_kernel`)."""
    if (
        not is_relation(row)
        or row.kind != "Aggregation"
        or len(row.outputs) != 1
        or len(row.maps) != 1
        or len(row.statements) != 1
        or row.statements[0] not in stage.definitions
    ):
        return None
    line = stage.definitions[row.statements[0]]
    if not line.equations:
        return None
    relation = relation_of(line.equations[0])
    if not isinstance(relation, (T.Equation, T.Inequality)):
        return None
    ctx = StageNames(stage)
    unknowns = set(row.unknowns)

    def alone(side):
        return isinstance(side, T.Sym) and set(ctx.mentioned(side, row.builder)) == unknowns

    def closed(side):
        return not (set(ctx.mentioned(side, row.builder)) & unknowns) and not any(
            isinstance(node, T.Operator) and node.head in ("solve", "argmax")
            for node in term_nodes(side)
        )

    for name, other in ((relation.lhs, relation.rhs), (relation.rhs, relation.lhs)):
        if alone(name) and closed(other):
            return other
    return None


def answers_function_set(stage, row):
    """Whether a row answers the set of the functions of its unknowns that
    its statement admits, and not one function: an `Argmax` row, whose
    answer is the set of the maximizers, and a relation with no explicit
    side (`explicit_side`), whose answer is the set of the solutions of its
    relation. A relation with an explicit side answers that function, and
    its relation holds on the function as its rule."""
    return row.kind == "Argmax" or (is_relation(row) and explicit_side(stage, row) is None)


def answering_row(stage, identity):
    """The row that answers a wire: the row that writes it, or, where that
    row is an `Evaluation`, which names what the operation before it made,
    the row that answers the wire the Evaluation reads; None where no row
    writes the wire. The fold makes of the identification line marked
    `!node`, `c = c[>] :: [id=cons_choice, !node]`, an Evaluation of the
    node whose output the builder's closing Evaluation reads; the row that
    answers both is the identification's `Pullback`. Where this row answers
    a set of functions (`answers_function_set`), its unknowns are the
    controls by which an Evaluation's rule names the policy
    (`defining_expressions.output_rules`) and which a card's wire lists
    (`denotations.wire_records`)."""
    rendering = wire_table(stage)
    row = rendering.produced.get(identity)
    while row is not None and row.kind == "Evaluation":
        identity = row.inputs[tuple(row.outputs).index(identity)]
        row = rendering.produced.get(identity)
    return row


@dataclasses.dataclass(frozen=True)
class GraphAtGrain:
    """One graph of a version at a grain: its level, `initial` or `builders`,
    its direction, `backward` or `forward`, and the grain it is read at. A
    bubble `bubble_at` derives carries the one it was derived at; a frozen
    record, which the copy of a version copies with the bubble."""

    level: str
    direction: str
    grain: str


def derived_graph_at_grain(stage, box):
    """The `GraphAtGrain` of a bubble `bubble_at` made, or None for
    anything else. A derived bubble stands in no stored graph, so
    `piece_and_place` refuses it; it carries the place it was derived at, which
    `bubble_at` writes on it, and nothing is searched for. A `WorkingStage`
    holds no derived bubble, only a `StageVersion` does."""
    if not isinstance(stage, StageVersion) or not hasattr(box, "arg"):
        return None
    return getattr(box, "_bellman_place", None)


# --- the order of the pieces of a composite ---


def chain_order(pieces):
    """The order in which the pieces of a composite are applied where they form
    a chain, and None where they do not (§3 rule 3): each piece's outputs are
    the next piece's inputs, the same wires in the same order, and no wire is
    copied. The query reads the graph's wires and never `list()` or a printed
    name. It stands beside the other queries and is reached through the verb
    alone."""
    if not pieces:
        return None
    reads = {box: tuple(sort.identity for sort in box.dom.inside) for box in pieces}
    writes = {box: tuple(sort.identity for sort in box.cod.inside) for box in pieces}
    taken = [identity for box in pieces for identity in reads[box]]
    if len(taken) != len(set(taken)):
        return None  # a wire two pieces read is copied
    written = {writes[box] for box in pieces}
    opening = [box for box in pieces if reads[box] not in written]
    if len(opening) != 1:
        return None
    by_input = {}
    for box in pieces:
        by_input.setdefault(reads[box], []).append(box)
    order = [opening[0]]
    while len(order) < len(pieces):
        following = by_input.get(writes[order[-1]], ())
        if len(following) != 1 or following[0] in order:
            return None
        order.append(following[0])
    return tuple(order)


class ApplicationOrder(NamedTuple):
    """The pieces of a composite in an order of application, and its kind:
    `application` where the wiring orders them, `listing` where the graph is
    not causal and the order of `list()` stands."""

    pieces: tuple
    kind: str


def pieces_in_dependency_order(pieces):
    """The pieces of a composite that form no chain, in an order of application
    (AMD-SG-021 §3.4): each piece after every piece that writes a wire it
    reads, ties broken by the order of `list()`, and that order alone where the
    graph is not causal. The dependency counts the wires alone, so a free name,
    which is no wire (AMD-SG-013 §1), orders no piece. The query reads the
    graph's wires and never `list()` alone or a printed name. It stands beside
    `chain_order` and is reached through the verb `denote()`."""
    pieces = list(pieces)
    writes = {}
    for place, box in enumerate(pieces):
        for sort in box.cod.inside:
            writes.setdefault(sort.identity, set()).add(place)
    needs = [
        {
            other
            for sort in box.dom.inside
            for other in writes.get(sort.identity, ())
            if other != place
        }
        for place, box in enumerate(pieces)
    ]
    order, taken = [], set()
    while len(order) < len(pieces):
        ready = [
            place for place in range(len(pieces)) if place not in taken and needs[place] <= taken
        ]
        if not ready:
            return ApplicationOrder(tuple(pieces), "listing")
        order.append(ready[0])
        taken.add(ready[0])
    return ApplicationOrder(tuple(pieces[place] for place in order), "application")
