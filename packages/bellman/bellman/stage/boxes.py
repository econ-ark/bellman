"""One box of a stage read at the place it stands
(AMD-SG-007 §2; AMD-SG-010 §4).

A box is reached from the piece that contains it, and every question about it
is answered from the row of the construction table that produced it, read
from the table folded again from the definitions table once per version
(`grains.construction_table`), so that the fold is written once. `_place_of`
finds where one box stands, deriving the graphs of its own level and direction
and no others; `piece_and_place` reads a name among every place and refuses a
name that names two boxes, and `bubble_at` gives one piece at a grain as the
bubble of its kind. What a box denotes and its card are `denotations`; the
kernels a box applies are `kernels`.
"""

from __future__ import annotations

import dataclasses
from typing import NamedTuple

from discopy.frobenius import Box, Bubble

from bellman.display.printed_records import (
    Listing,
    ListingEntry,
    Methods,
    NamedListing,
    Obligations,
)
from bellman.fold.block_lines import doc_lines, header_wire_sorts, require_stage
from bellman.fold.stage_names import lines_of
from bellman.graphs.builders_graphs import interior_at
from bellman.native.hypergraphs import Block, Builder, freeze_native
from bellman.native.identity import OPERATOR_KINDS, Identity, box_identity
from bellman.native.labels import (
    box_label,
    function_name,
    function_wire_name,
    is_wiring,
    italic,
    wire_spelling,
)
from bellman.native.provenance import source_file
from bellman.native.records import Definition, Refusal, bound_at
from bellman.native.versions import kept_answer
from bellman.refusals import (
    TARGET_AMBIGUOUS,
    TARGET_NOT_FOUND,
    TARGET_VERSION,
    NotConstructed,
    TargetError,
    construction_error,
)
from bellman.stage.grains import (
    DIRECTIONS,
    LEVELS,
    GraphAtGrain,
    block_id_of,
    chain_order,
    construction_table,
    grain_token,
    graph_of,
    is_primitive_operator,
    kind_of,
    pieces_in_dependency_order,
    stored_graph,
    wire_table,
)
from bellman.stage.method_targets import block_box
from bellman.syntax.vocabulary import PERCH_MARK

# --- the conditions a piece owns ---


def box_obligations(stage, box):
    """The conditions the construction could not discharge that this box owns:
    those recorded under its own identity and, for a box merged across
    authored lines, those of its member occurrences, each naming the line it
    came from (AMD-SG-011 §3).

    The answer is the `Obligations` record the stage answers with, empty or
    not, so that one question has one form of answer at every level and no
    answer's print opens with a constructor call."""
    require_stage(stage)
    # the merged lines are a primitive operator's; a bubble, a bubble derived
    # at a finer grain included, holds none and stands in no stored graph
    lines = set(merged_lines(stage, box)) if is_primitive_operator(box) else set()
    kind = box_identity(box).kind
    if isinstance(box, Bubble):
        # a builder owns the conditions named on its lines marked `!doc`,
        # which form no piece (AMD-SG-034 §3 `declared`)
        identities = {box_identity(box)}
        identities.update(definition.identity for definition in doc_lines(stage, box.name))
        for part in boxes_inside(box):
            identities.add(box_identity(part))
            if not isinstance(part, Bubble):
                try:
                    row = row_of(stage, part)
                except (KeyError, TypeError, ValueError):
                    continue
                identities.update(row.outputs)
                identities.update(
                    stage.definitions[address].identity
                    for address in row.statements
                    if address in stage.definitions
                )
        return Obligations(
            item
            for item in stage.obligations()
            if any(
                identity in identities
                for identity in item.entries
                if isinstance(identity, Identity)
            )
        )
    identities = {box.identity}
    try:
        row = row_of(stage, box)
    except (KeyError, TypeError, ValueError):
        row = None
    if row is not None:
        identities.update(row.outputs)
        identities.update(
            stage.definitions[address].identity
            for address in row.statements
            if address in stage.definitions
        )
        if row.definition is not None:
            identities.add(row.definition)
    # a condition a line marked `!doc` names is the builder's, the piece
    # whose correctness depends on it being the whole construction
    declared = {definition.identity for definition in doc_lines(stage, box_identity(box).block)}

    def owns(item):
        first = item.entries[0]
        if isinstance(first, Identity) and first.kind in OPERATOR_KINDS:
            # a condition recorded on an operation is that operation's alone,
            # the line it represents being shared with the other operations of
            # the line; a merged box owns its member occurrences' conditions:
            # among the boxes of the builder representing the line with this
            # kind, the one carrying the occurrence's number where one does,
            # the merged box without a number otherwise
            if first == box.identity:
                return True
            if not names_merged_line(first, lines, kind):
                return False
            named = [
                row.identity
                for row in _sibling_rows(stage, box)
                if row.identity.kind == first.kind and first.address in row.statements
            ]
            owner = next(
                (identity for identity in named if identity.occurrence == first.occurrence), None
            )
            if owner is None:
                owner = next((identity for identity in named if identity.occurrence is None), None)
            return owner == box.identity
        return any(
            identity in identities for identity in item.entries if isinstance(identity, Identity)
        )

    return Obligations(
        item
        for item in stage.obligations()
        if item.entries
        and not any(
            identity in declared for identity in item.entries if isinstance(identity, Identity)
        )
        and owns(item)
    )


def merged_lines(stage, box):
    """The authored lines a merged box represents, read from the row's own
    `statements` — the same source the `source` line of its card prints. The
    merged expectation of `cons_savings_iid.bl` represents `dcsn_to_arvl.value`
    and `dcsn_to_arvl.marginal`; a box that represents one line, and a box that
    represents none, such as a pullback or an evaluation, answer with nothing.
    The obligations and the methods of a merged box are those of its lines
    (AMD-SG-011 §3)."""
    try:
        target, entry = operator_target(stage, box, "merged_lines")
        row = row_at(stage, target, entry)
    except (KeyError, TypeError, ValueError):
        return ()
    return tuple(row.statements) if len(row.statements) > 1 else ()


def names_merged_line(identity, lines, kind):
    """Whether an obligation or a method identity names an occurrence, of this
    box's kind, of one of the lines the box merges:
    `dcsn_to_arvl.value:Expectation:1` belongs to the merged expectation of
    `dcsn_to_arvl.value` and `dcsn_to_arvl.marginal`, and
    `dcsn_to_arvl.marginal:Aggregation:1` does not, since that is another box.
    """
    return isinstance(identity, Identity) and identity.address in lines and identity.kind == kind


def _sibling_rows(stage, box):
    """The rows of the fold a box stands in, the boxes beside it at its
    grain: the fold with the sub-builders open at the primitive grain, closed
    at the other grains, both where the place is unknown."""
    try:
        entry = _place_of(stage, box)
    except (KeyError, TypeError, ValueError):
        entry = None
    folds = _folds_at(stage, box, entry)
    return tuple(folds[0]) + tuple(
        row for fold in folds[1:] for row in fold if row not in folds[0]
    )


# --- the bindings within a piece ---


def methods_within(stage, piece):
    """Every binding within one piece (AMD-SG-021 §2.3), as the
    `Methods` record; empty before `methodize`. It is what `methods` answers at
    every level and what the `method` clause of a card prints.

    At a primitive operator: the entry bound at the box and the entries bound
    at the authored lines it represents, a box merged across lines answering
    with what its member lines bound (AMD-SG-011 §3). At a builder or a
    sub-builder: the entries bound at it, at the boxes inside it and at the
    lines of the block of its name, so that `cntn_to_dcsn.methods` answers the
    grids two of its lines carry. At a block: the entries bound at it and at
    its lines. At a graph: those within its boxes, `piece` being the boxes of
    the graph and not one box."""
    bound = stage.bindings.methods
    if bound is None:
        return Methods({})
    boxes = (piece,) if isinstance(piece, Box) else tuple(piece)
    names, lines, kinds = set(), set(), set()
    for box in boxes:
        names |= _names_bound_within(stage, box)
        held = set(merged_lines(stage, box)) if is_primitive_operator(box) else set()
        if held:
            lines |= held
            kinds.add(box_identity(box).kind)
    return methods_bound_within(
        stage,
        {
            bound_at(key)
            for key in bound
            if bound_at(key) in names
            or any(names_merged_line(bound_at(key), lines, kind) for kind in kinds)
        },
    )


def _names_bound_within(stage, box):
    """The names a binding within one box can stand under: the box itself and
    every box, line and sub-builder inside it, together with the lines of the
    block a builder is built from and the authored lines a primitive
    operator represents."""
    if isinstance(box, Bubble):
        names = set(names_within(box))
        if is_block(box):
            for address in _line_names_of(box):
                if address in stage.definitions:
                    names.update(methods_of_line(stage, stage.definitions[address]))
        block = _block_realised_by(stage, box)
        return names | _line_names_of(block) if block is not None else names
    if is_primitive_operator(box):
        return {box.name} | {record.address for record in _represented_lines(stage, box)}
    if box.name in stage.definitions and stage.definitions[box.name].kind == "line":
        return {box.name} | set(methods_of_line(stage, stage.definitions[box.name]))
    return {box.name}


def names_within(box):
    """The name of a bubble and of every box, line and sub-builder inside it,
    at any depth. `.methods` is filtered by these names (AMD-SG-010 §4): a
    block and the builder of the same name
    hold different boxes and so answer with different entries."""
    found = {box.name}
    for held in boxes_inside(box):
        found |= names_within(held) if isinstance(held, Bubble) else {held.name}
    return found


def _line_names_of(block):
    """The names of the line boxes of a block: the boxes inside it with no
    interior, at any depth. A sub-block is a bubble and stands here for its own
    lines alone, and the block's own name is no line of it."""
    found = set()
    for box in block.arg.boxes:
        if is_wiring(box):
            continue
        found |= _line_names_of(box) if isinstance(box, Bubble) else {box.name}
    return found


def _block_realised_by(stage, bubble):
    """The block or sub-block of an initial diagram that a builder or a
    sub-builder is built from: the bubble of its name among the version's
    stored initial diagrams, read before any grain is derived. A block id is
    unique across the two directions (AMD-SG-010 §4), so the direction need not
    be named; a block itself answers None, holding its own lines."""
    if is_block(bubble):
        return None
    for direction in DIRECTIONS:
        graph = stored_graph(stage, "initial", direction)
        found = None if graph is None else _bubble_named(graph.boxes, bubble.name)
        if found is not None:
            return found
    return None


def _bubble_named(boxes, name):
    """The bubble of that name among these boxes or inside one of them."""
    for box in boxes:
        if not isinstance(box, Bubble):
            continue
        if box.name == name:
            return box
        found = _bubble_named(box.arg.boxes, name)
        if found is not None:
            return found
    return None


def _represented_lines(stage, box):
    """The authored lines a primitive operator represents, as records: those
    the field `origins` of its `kernel()` holds, and where an origin is a law
    of motion or a value aggregator, the lines its own equations name, which on
    a merged aggregation are the lines the file wrote. Every line is reached
    through the records the box refers to; no address is read for its parts."""
    table = stage.definitions
    found, seen = [], set()

    def keep(record):
        if record.kind == "line" and record.identity not in seen:
            seen.add(record.identity)
            found.append(record)

    for record in origins(stage, box):
        if record.kind == "line":
            keep(record)
            continue
        for address in record.equations:
            if isinstance(address, str) and address in table:
                keep(table[address])
    return tuple(found)


def methods_bound_within(stage, names):
    """The entries of the version's `bindings.methods` bound at one of
    `names`, in binding order, as the `Methods` record, a read-only mapping
    that prints one line per entry (AMD-SG-020 §3.4); empty before
    `methodize`. Each handle's `methods` passes through this function."""
    bound = stage.bindings.methods
    if bound is None:
        return Methods({})
    return Methods({key: method for key, method in bound.items() if bound_at(key) in names})


def methods_of_line(stage, definition):
    """Methods attached to a line or to the Evaluation of its named output."""
    names = {definition.address}
    if not stage.bindings.methods:
        return methods_bound_within(stage, names)
    for direction in DIRECTIONS:
        graph = stored_graph(stage, "initial", direction)
        block = None if graph is None else _bubble_named(graph.boxes, definition.identity.block)
        if block is None:
            continue
        for _, line in lines_of(stage, block):
            if line.address == definition.address and line.role in ("output", "node"):
                address = line.address if line.role == "node" else block.name
                names.add(Identity("Evaluation", address=address))
        break
    return methods_bound_within(stage, names)


# --- the row a box was made from ---


def row_of(stage, box):
    """The row of the construction table that produced a box, folded again
    from the stage: its kind, builder, statements, wires, references,
    coordinates and map. A box of this version is read at the grain it
    stands at; a name several rows carry is matched by the box's wires; a box
    that no one row matches is refused, never answered by the first row of
    its name (AMD-SG-007 §2)."""
    require_stage(stage)
    if not is_primitive_operator(box):
        raise TypeError(f"{box.name!r} is not a primitive operator box")
    return row_at(stage, box, _place_of(stage, box))


def rows_of(stage, block_id):
    """The rows of the construction table of one builder, folded again from
    the stage: those with its sub-builders closed, then those with them open,
    a row of both folds once."""
    require_stage(stage)
    rows_open, rows_closed = builder_rows_of(stage, block_id)
    found = list(rows_closed)
    found.extend(row for row in rows_open if row not in found)
    return tuple(found)


def row_at(stage, box, entry):
    """The row that produced a box at the place it stands: the fold with the
    sub-builders open at the primitive grain, closed at the other grains, and
    both folds for a box whose place is unknown."""
    found = []
    for rows in _folds_at(stage, box, entry):
        found.extend(row for row in rows if row.identity == box.name and row not in found)
    if len(found) == 1:
        return found[0]
    wires = (
        tuple(ob.identity for ob in box.dom.inside),
        tuple(ob.identity for ob in box.cod.inside),
    )
    matching = [row for row in found if (row.inputs, row.outputs) == wires]
    if len(matching) == 1:
        return matching[0]
    if not found:
        raise KeyError(f"no row of the construction table is named {box.name!r}")
    raise KeyError(
        f"{len(matching)} of the {len(found)} rows named {box.name!r} have the inputs "
        f"{wires[0]!r} and the outputs {wires[1]!r}; pass the box from the view it stands in"
    )


class BuilderRows(NamedTuple):
    """The rows of the construction table of one builder: `opened`, those
    with its sub-builders open, and `closed`, those with them closed."""

    opened: tuple
    closed: tuple


def _folds_at(stage, box, place):
    """The folds of the builder of a box that are read at the box's `Place`:
    the rows with the sub-builders open at the primitive grain, closed at the
    other grains, and both, the closed first, where the place is unknown."""
    rows = builder_rows_of(stage, block_id_of(box))
    grain = place.grain if place is not None else None
    if grain == "primitive":
        return (rows.opened,)
    if grain is not None:
        return (rows.closed,)
    return (rows.closed, rows.opened)


def builder_rows_of(stage, block):
    """The `BuilderRows` of one builder, read from the table the stage folds
    again once per version (`grains.construction_table`). A name that is no
    block of the stage is refused, as `block_box` refuses it."""
    block_box(stage, block, block)
    table = construction_table(stage)
    return BuilderRows(table.by_builder(block), table.by_builder(block, grain="node"))


def origins(stage, box):
    """The retained definitions a box reads, excluding supplied
    field functions."""
    require_stage(stage)
    table = stage.definitions
    if not isinstance(box.data, tuple):
        raise TypeError(
            "a box of a constructed stage carries a tuple "
            f"of references; got {type(box.data).__name__}"
        )
    fields = header_wire_sorts(stage)
    supplied = {
        reference
        for reference in box.data
        if isinstance(reference, Identity)
        and reference.kind == "function"
        and reference.perch is not None
        and Identity("field", stage=stage.name, perch=reference.perch, field=reference.field)
        in fields
    }
    missing = [
        reference for reference in box.data if reference not in table and reference not in supplied
    ]
    if missing:
        raise KeyError(
            f"the box {box.name!r} refers to {missing!r}, "
            "which the definitions table does not hold"
        )
    return tuple(table[reference] for reference in box.data if reference not in supplied)


# --- finding a piece by its name or by the object ---


def bubble_at(stage, box, grain):
    """One builder, one block or one sub-builder at a grain, as the bubble of
    the same kind (AMD-SG-012 §1). The bubble is derived from the graph at that
    grain and made once per version, so that two handles for one piece of one
    version hold one object and compare equal. A sub-builder has no sub-builder
    inside it, so at that grain it is itself."""
    target, entry = piece_and_place(stage, box)
    if entry is None:
        raise TypeError(
            f"{getattr(box, 'name', box)!r} stands in no graph of this version, so it has no grain"
        )
    level, direction = entry.level, entry.direction
    grain = grain_token(grain)
    if grain == "node" and target.identity.kind == "line":
        return target

    def compute():
        dom = tuple(ob.identity for ob in target.dom.inside)
        cod = tuple(ob.identity for ob in target.cod.inside)
        # `interior_at` is given the two graphs it reads, since it stands
        # beneath these queries (AMD-SG-018 §5)
        made = freeze_native(
            interior_at(
                wire_table(stage),
                level,
                target.identity,
                inputs=dom,
                outputs=cod,
                graph=graph_of(stage, level, direction, grain),
                builder_graph=graph_of(stage, level, direction, "builder"),
            )
        )
        # the bubble stands in no stored graph, so it carries the place it was
        # derived at and `derived_graph_at_grain` reads it from the bubble
        # itself rather than searching the version's cache (AMD-SG-018 §4)
        object.__setattr__(made, "_bellman_place", GraphAtGrain(level, direction, grain))
        return made

    return kept_answer(stage, ("bubble", level, direction, target.name, grain), compute)


def piece_and_place(stage, target, primitive=False):
    """The one retained object of this version a target names, with the place
    it stands at (AMD-SG-007 §2): a `Definition` record of `definitions`, or a
    box of one of the version's graphs, given as the object itself or by an
    unambiguous name. The boxes of one name at several places are one choice
    when they are equal boxes, with one kind, one set of references and equal
    typed inputs and outputs; a statement box of an initial diagram is the
    `line` record it displays. With `primitive`, a name that names a primitive
    operator box is read among those boxes only, the targets of `kernel` and
    `compile` (§3.1). A record or box of another version, a name that names
    nothing and a name that names two choices are refused as `TargetError`."""
    require_stage(stage)
    table = stage.definitions
    if isinstance(target, Definition):
        if table.get(target.identity) is not target:
            raise TargetError(
                target=target.identity,
                stage=stage.name,
                rule=TARGET_VERSION,
                candidates=(target.identity,),
                message=f"stage {stage.name!r}: the definition record {target.identity!r} passed "
                "is not the record this version holds; a query reads the records of the version "
                "it is asked of, and versions share no object (AMD-SG-007 §2, rule "
                "target-version); ask the version that holds the "
                f"record, or pass the identity {target.identity!r}",
            )
        return target, None
    if isinstance(target, Box):
        entry = _place_of(stage, target)
        if entry is not None:
            return target, entry
        raise TargetError(
            target=target.name,
            stage=stage.name,
            rule=TARGET_VERSION,
            candidates=(target.name,),
            message=f"stage {stage.name!r}: the box {target.name!r} passed is no box of a graph "
            "of this version; a query reads the boxes of the version it is asked of, and versions "
            "share no object (AMD-SG-007 §2, rule target-version); ask the version "
            "whose view holds the box, or pass a box of this version's view",
        )
    if not isinstance(target, str) or not target:
        raise TypeError(
            "a target is a box, a definition record, or "
            f"the name of one; got {type(target).__name__}"
        )
    places = _places(stage)
    boxes = []
    for entry in places:
        box = entry.box
        if box.name != target:
            continue
        if not isinstance(box, Bubble) and kind_of(box) is None and target in table:
            continue  # a statement box displays its line record
        for choice in boxes:
            if type(choice[0]) is type(box) and choice[0] == box:
                choice[1].append(entry)
                break
        else:
            boxes.append((box, [entry]))
    choices = ([(table[target], [])] if target in table else []) + boxes
    if primitive and any(is_primitive_operator(choice[0]) for choice in choices):
        choices = [choice for choice in choices if is_primitive_operator(choice[0])]
    if not choices:
        names = tuple(dict.fromkeys(tuple(table) + tuple(entry.box.name for entry in places)))
        raise TargetError(
            target=target,
            stage=stage.name,
            rule=TARGET_NOT_FOUND,
            candidates=names,
            message=f"stage {stage.name!r}: {target!r} names no box of the version's views and no "
            "record of its definitions table; a printed view, a kernel and a compiled kernel read "
            "an actual box or definition (AMD-SG-007 §2, rule target-not-found); write a box "
            "name that stage.builder.bwd.primitives.list() or "
            "stage.builder.fwd.primitives.list() shows, or an identity of stage.definitions",
        )
    if len(choices) > 1:
        listed = [_choice_text(choice, entries) for choice, entries in choices]
        raise TargetError(
            target=target,
            stage=stage.name,
            rule=TARGET_AMBIGUOUS,
            candidates=tuple(listed),
            message=f"stage {stage.name!r}: {target!r} names {len(choices)} different targets — "
            f"{' | '.join(listed)}; one name selects one target only when the boxes it names are "
            "equal (AMD-SG-007 §2, rule target-ambiguous); pass "
            "the box itself from the view and grain you mean",
        )
    choice, entries = choices[0]
    return choice, (entries[0] if entries else None)


def operator_target(stage, box, verb):
    """The primitive operator box a `kernel`, `compile` or `affine` target
    names, with its place; a target that is no primitive operator is refused
    under `kernel-target`."""
    target, entry = piece_and_place(stage, box, primitive=True)
    if not is_primitive_operator(target):
        what = (
            f"the definition {target.identity!r} ({target.kind})"
            if isinstance(target, Definition)
            else f"the box {target.name!r}, which is no primitive operator"
        )
        raise construction_error(
            f"stage {stage.name!r}: {verb} reads the kernel of a primitive operator box, and "
            f"{what} applies none of its own (AMD-SG-007 §3.1, rule kernel-target); a builder, a "
            "sub-builder, a source line and a definition are read with view(stage, target); "
            "pass a box that stage.builder.bwd.primitives.list() or "
            "stage.builder.fwd.primitives.list() names",
            stage=stage.name,
            address=target.address if isinstance(target, Definition) else target.name,
            span=None,
            rule="kernel-target",
            file=source_file(stage),
        )
    return target, entry


# the grains a name is looked for at, in the order a list of candidates
# names them
_GRAIN_WORDS = ("builder", "sub-builder", "primitive", "combined", "factored")


@dataclasses.dataclass(frozen=True)
class Place:
    """Where one box of a version stands: the box, the level and the direction
    of the graph that holds it, the grain it is read at, and the builder or
    block it belongs to; a frozen record, which the copy of a version copies
    with the answers the version carries."""

    box: object
    level: str
    direction: str
    grain: str
    builder: str


def _place_of(stage, box):
    """The `Place` of one box of this version, or None where no graph of the
    version holds it. The graphs
    derived are those of the level and the direction the box belongs to, at
    the grains up to the one it stands at, and no others, so that one box's
    card leaves the cache holding no graph of a grain or a direction the box
    does not stand in (AMD-SG-018 §4). The answer is the first place `_places`
    would name, since the order of the walk is the same."""
    for level, direction in _standing(stage, box):
        for grain in _GRAIN_WORDS:
            try:
                graph = graph_of(stage, level, direction, grain)
            except NotConstructed:
                continue
            for entry in _walk_places(graph.boxes, GraphAtGrain(level, direction, grain)):
                if entry.box is box:
                    return entry
    return None


def _places(stage):
    """Every box of the graphs of this version with where it stands, each a
    `Place`: the builders graphs and the
    initial diagrams of each direction at every grain. Memoized on the
    version; a graph the construction refused holds no place. This is what a
    name is resolved among; a box object names its own place (`_place_of`)."""

    def compute():
        found = []
        for level in LEVELS:
            for direction in DIRECTIONS:
                for grain in _GRAIN_WORDS:
                    try:
                        graph = graph_of(stage, level, direction, grain)
                    except NotConstructed:
                        continue
                    found.extend(_walk_places(graph.boxes, GraphAtGrain(level, direction, grain)))
        return tuple(found)

    return kept_answer(stage, "places", compute)


def _walk_places(boxes, graph, builder=None):
    """The `Place` of every box of one graph, `graph` its `GraphAtGrain`: the
    boxes inside a bubble after the bubble, the wiring passed over."""
    found = []
    for box in boxes:
        if is_wiring(box):
            continue
        owner = builder or box_identity(box).block
        found.append(
            Place(
                box=box,
                level=graph.level,
                direction=graph.direction,
                grain=graph.grain,
                builder=owner,
            )
        )
        if isinstance(box, Bubble):
            found.extend(_walk_places(box.arg.boxes, graph, owner))
    return tuple(found)


def _standing(stage, box):
    """The levels and directions a box can stand in, in the order `_places`
    walks them: the level the box's own kind names, and the direction whose
    stored graph holds the block the box belongs to, read from the version's
    record before any grain is derived."""
    try:
        block = box_identity(box).block
    except Exception:
        block = None
    every = tuple((level, direction) for level in _levels_of(box) for direction in DIRECTIONS)
    if block is None:
        return every
    named = []
    for level, direction in every:
        graph = stored_graph(stage, level, direction)
        if graph is not None and any(getattr(held, "name", None) == block for held in graph.boxes):
            named.append((level, direction))
    return tuple(named) or every


def _levels_of(box):
    """The levels a box can stand in, in the order `_places` walks them: a
    block stands in an initial diagram, a builder and a primitive operator in
    a builders graph, and a statement box, which names its line, is looked
    for in both."""
    if isinstance(box, Block):
        return ("initial",)
    if isinstance(box, Builder) or is_primitive_operator(box):
        return ("builders",)
    return LEVELS


def _choice_text(target, entries):
    """One candidate of a name for a refusal: a definition by its identity and
    kind, a box by its name, the graphs and grains it stands in and its
    builder."""
    if isinstance(target, Definition):
        return f"the definition {target.identity} ({target.kind})"
    places = {}
    for entry in entries:
        where = (
            f"the {'initial diagram' if entry.level == 'initial' else 'builders graph'}, "
            f"{entry.direction}"
        )
        places.setdefault((where, entry.builder), []).append(entry.grain)
    return "; ".join(
        f"the box {target.name} in {where} at the grain "
        f"{', '.join(dict.fromkeys(grains))}, builder {builder}"
        for (where, builder), grains in places.items()
    )


# --- the listings `list()` prints ---


def level_listing(record):
    """What is inside the two initial diagrams, which `stage.initial.list()`
    answers: each block's name with the word `block` and the direction of the
    diagram that holds it, `block, backward`, printed as two columns
    (AMD-SG-012 §1)."""
    found = {}
    for direction in record.MEMBERS:
        graph = getattr(record, direction)
        if isinstance(graph, Refusal):
            continue
        for box in graph.boxes:
            found[box.name] = f"block, {direction}"
    return NamedListing(found)


# the kind column of a listing (AMD-SG-034 §3), one word per project word of
# `piece_word`, read from the same class and identity
_KIND_WORDS = {
    "Block": "block",
    "Builder": "builder",
    "SubBuilder": "sub-builder",
    "Line": "line",
    "Operator": "primitive",
}


def graph_listing(graph):
    """The pieces of one graph, which a graph's `list()` answers (AMD-SG-012
    §1; AMD-SG-034 §3): one entry per box in order of application, keyed by
    the whole name, with the kind word, what the box produces by name and its
    number — a builder its position among the builders of the graph, which
    the stage card's `operations` block numbers, and a primitive its position
    among the primitives of its own builder, the sub-builders opened, which
    the builder's card numbers; a sub-builder and a block carry none. At the
    node and the primitive grains the rows of several builders stand together
    and each builder's count runs on its own."""
    entries, builders, counted = [], 0, {}
    for box in _applied_order(box for box in graph.boxes if not is_wiring(box)):
        kind = _KIND_WORDS[piece_word(box)]
        number = None
        if kind == "builder":
            builders += 1
            number = builders
        elif kind in ("sub-builder", "primitive"):
            block = box_identity(box).block
            counted[block] = counted.get(block, 0) + (
                _primitives_within(box) if kind == "sub-builder" else 1
            )
            number = None if kind == "sub-builder" else counted[block]
        entries.append(
            ListingEntry(
                key=box.name,
                name=box.name,
                kind=kind,
                produced=_produced(box),
                depth=0,
                number=number,
            )
        )
    return Listing(entries)


def _applied_order(pieces):
    """The pieces of one interior in the order of application their composite
    record lists them in (`Composite.pieces`, `denotations._composite`):
    the chain where the wiring gives one, else the dependency order, ties
    broken by the order of the graph."""
    pieces = tuple(pieces)
    order = chain_order(pieces)
    return order if order is not None else pieces_in_dependency_order(pieces).pieces


# the project's word for each piece a handle holds (AMD-SG-021 §4.6), read
# from the class of the box and the kind of its identity: a block of an
# initial diagram, a builder of a builders graph, a sub-builder born of an
# authored `!node` line, an authored line, and a primitive operator
def piece_word(box):
    """The project's word for the piece a handle holds, which its short form
    prints: `Block` for a block of an initial diagram, `Builder` for a bubble
    of a builders graph, `SubBuilder` for a bubble born of an authored `!node`
    line, `Line` for an authored line and `Operator` for a primitive operator.
    Read from the class of the box and the kind of its identity and never from
    a name's text (AMD-SG-021 §4.6)."""
    born_of_a_line = box_identity(box).kind == "line"
    if isinstance(box, Bubble):
        return "Block" if is_block(box) else ("SubBuilder" if born_of_a_line else "Builder")
    return "Line" if born_of_a_line else "Operator"


def _primitives_within(box):
    """The number of primitive operators inside a bubble at any depth: what a
    sub-builder's row counts for in a numbering it carries no number in."""
    return sum(
        _primitives_within(held) if isinstance(held, Bubble) else int(is_primitive_operator(held))
        for held in boxes_inside(box)
    )


def _produced(box):
    """What a piece produces, by name, for the arrow column of a listing
    (AMD-SG-034 §3): a sub-builder the function it creates with its
    coordinates, `𝐶𝐸(m_d, ν)`, as its label names it (AMD-SG-012 §2); any other
    piece its named outputs, `𝑉, 𝑑𝑉`; a piece whose outputs carry no name, the
    empty string."""
    if isinstance(box, Bubble) and box_identity(box).kind == "line":
        return ", ".join(
            f"{italic(function_wire_name(ob.identity))}("
            f"{', '.join(a.stem for a in ob.coordinates)})"
            if getattr(ob, "kind", None) == "function"
            else ob.identity.stem
            for ob in box.cod.inside
        )
    names = [_named_output(ob.identity) for ob in box.cod.inside]
    return ", ".join(name for name in names if name is not None)


def _named_output(identity):
    """The name a wire carries, or None where it carries a construction and
    no name: a function or a choice at a perch, by its field and perch mark,
    `𝑉[>]`; a result the file names, `𝑐`; a field of an initial diagram,
    `V[<]`; the intermediate result a marked statement defines, `𝐶𝐸`; the
    measure of a perch, `μ[>]`. A composite with the law of motion (the mark
    `g`), an unnamed occurrence result, a selection and a measure extended by
    a distribution or a policy carry no name."""
    if (
        identity.kind in ("function", "choice")
        and identity.perch is not None
        and identity.mark is None
    ):
        return function_name(identity.field, identity.perch)
    if identity.is_result and identity.field is not None:
        return function_name(identity.field)
    if identity.kind == "field":
        return wire_spelling(identity)
    if identity.kind == "alias":
        return function_name(identity.field)
    if identity.kind == "measure" and identity.mark is None and not identity.subjects:
        return (
            "μ"
            + (f"_{identity.field}" if identity.field else "")
            + PERCH_MARK.get(identity.perch, "")
        )
    return None


def bubble_listing(stage, box):
    """The pieces inside a bubble, which a bubble's `list()` answers
    (AMD-SG-012 §1; AMD-SG-020 §3.5 item 2, §6 choice 6; AMD-SG-034 §3
    "Listings"): for a builder or a sub-builder a tree in order of application
    at every level, for a block the rows of `_block_listing`.

    The key of an entry is what `__getitem__` accepts: the part of the name
    after the holder's segment, and for a piece inside a sub-builder the tuple
    of keys that walks to it, one per level, `("risk_ce", "Pullback")`. So
    every entry keeps its key at the grain the bubble is read at: at the
    stored and the node grains the sub-builders stand with their primitives
    under them, and at the primitive grain, where the sub-builders are opened,
    the primitives stand alone under the keys that grain accepts,
    `risk_ce:Pullback`, with the same numbers. A primitive's number is its
    position in order of application among the primitives of the builder, the
    sub-builders opened, which is the number the builder's card gives it; a
    sub-builder's row carries its key, the kind word and the function it
    creates, and no number. A builder's `!doc` line forms no piece and is not
    listed (AMD-SG-034 §3, `declared`)."""
    if is_block(box):
        return _block_listing(stage, box)
    entries, counted = [], 0

    def walk(holder, prefix, depth):
        nonlocal counted
        for held in _applied_order(boxes_inside(holder)):
            key = piece_named(held, holder.name)
            kind = _KIND_WORDS[piece_word(held)]
            number = None
            if kind == "primitive":
                counted += 1
                number = counted
            entries.append(
                ListingEntry(
                    key=prefix + (key,) if prefix else key,
                    name=held.name,
                    kind=kind,
                    produced=_produced(held),
                    depth=depth,
                    number=number,
                )
            )
            if isinstance(held, Bubble):
                walk(held, prefix + (key,), depth + 1)

    walk(box, (), 0)
    return Listing(entries)


def _block_listing(stage, block):
    """The pieces directly inside a block of an initial diagram, which the
    block's `list()` answers: its lines and node groups in the order of its
    interior, keyed by the part of the name after the block's segment, with
    the kind word and the field each produces. A line that reads no wire
    (`!doc`) is named too, so that every line the block's card prints is
    reached by its name (AMD-SG-021 §4.5); it stands where the file writes it,
    before the first box whose own line the file writes after it. No row is
    numbered: a block's card has no `operations` block."""
    wireless = lines_with_no_wire(stage, block)
    written = {
        definition.address: place for place, definition in enumerate(stage.definitions.values())
    }
    pending = [
        (written.get(definition.address, len(written)), key, definition)
        for key, definition in wireless.items()
    ]
    entries = []
    for held in boxes_inside(block):
        at = written.get(held.name, len(written))
        while pending and pending[0][0] < at:
            _, key, definition = pending.pop(0)
            entries.append(
                ListingEntry(
                    key=key,
                    name=definition.address,
                    kind="line",
                    produced="",
                    depth=0,
                    number=None,
                )
            )
        entries.append(
            ListingEntry(
                key=piece_named(held, block.name),
                name=held.name,
                kind=_KIND_WORDS[piece_word(held)],
                produced=_produced(held),
                depth=0,
                number=None,
            )
        )
    entries.extend(
        ListingEntry(
            key=key, name=definition.address, kind="line", produced="", depth=0, number=None
        )
        for _, key, definition in pending
    )
    return Listing(entries)


def lines_with_no_wire(stage, box):
    """The authored lines of a block or a builder that are no box of it, by
    the key that names them: a line marked `!doc` reads no wire and forms no
    piece, so the construction puts it in no graph, while the block's card and
    the builder's card print it (AMD-SG-021 §4.5; AMD-SG-015 §5 item 7;
    AMD-SG-034 §3 `declared`). The mapping is in file order and is empty for a
    sub-builder and for a block every line of which is a box."""
    if is_block(box):
        named = {held.name for held in boxes_inside(box)}
        lines = tuple(
            definition
            for definition in stage.definitions.values()
            if definition.kind == "line"
            and definition.address not in named
            and definition.address.split(".", 1)[0] == box.name
        )
    else:
        lines = doc_lines(stage, box.name)
    return {
        definition.identity.key_within(box.name) or definition.address: definition
        for definition in lines
    }


def piece_named(box, holder):
    """The navigation's key for a piece: the part of its name after the
    holder's, which `Identity.key_within` gives, so that two pieces of one
    kind stay apart (`value:Aggregation:1`); the whole name for a builder of
    a graph."""
    identity = box_identity(box)
    return (identity.key_within(holder) or str(identity)) if holder else str(identity)


# --- the pieces inside a bubble ---


def boxes_inside(box):
    """The boxes directly inside a bubble, in the order of its interior, the
    wiring skipped: the primitive operators and the sub-builders of a builder,
    the authored lines and the node groups of a block."""
    inner = tuple(held for held in box.arg.boxes if not is_wiring(held))
    if is_block(box):
        return inner
    return tuple(held for held in inner if is_primitive_operator(held) or isinstance(held, Bubble))


def is_block(box):
    """Whether a bubble is a box of an initial diagram rather than of a
    builders graph."""
    return isinstance(box, Block)
