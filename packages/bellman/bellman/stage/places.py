"""The places of a stage and the components typed at them (specification 0.7
§4 rule 7, §5; the ruling "On structure"; D2, D4).

A place is the written address of an operator of the stage: a builder by its
block id, `policy`; a line by its address, `policy.InvEuler`, a `!node` line
among them; the occurrences of an operator head in one line,
`dcsn_to_arvl.value.E_ψ_ξ`, in one block, `dcsn_to_arvl.E_ψ_ξ`, or in the
whole stage, `E_ψ_ξ` (F3, F62); the Evaluation that closes a builder,
`policy.evaluate`, and each object it stores, `dcsn_to_arvl.evaluate[V[<]]`,
`dcsn_to_arvl.evaluate[D_{k}V[<]]`, `policy.evaluate[c]` (D4); the Evaluation
of a `!node` line, `policy.InvEuler.evaluate`; and a definition by its name,
`𝑑𝑢𝑖𝑛𝑣`. A line of a branch is addressed under its label,
`dcsn_to_cntn.keep.cash_on_hand`. `stage.places()` lists them with their
kinds, which are read from the objects of the stage, whatever is typed at
them. The derivative operator `D` and its occurrences are listed and admit no
typing (F44).

A typing entry, `policy.method : !egm`, `evaluate[V[<]].grid :
!Cartesian(…)` or `policy.handler : "cons-port:egm"`, is a record of the
definitions table of kind `typing` whose identity names the place and the
component. `typings` resolves every such record to its place, once per
version, and refuses one that names no place (`name-in-scope`), one at the
derivative operator (`no-method-for-derivative`), a method word no row of the
catalogue holds (`syntax`), a word at a place of a kind its row does not admit
(`method-admission`), and a component typed twice at one place, by two
entries, by the whole of an Evaluation beside one of its objects, or by an
operator head beside one of its occurrences (`component-typed-twice`). The
components at a place are the `Components` record `components_by_place`
answers, which `methods` at every level, the printed signatures, the cards
and the settings table read; nothing is stored beside the typing records.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

from bellman.display.printed_records import Rows
from bellman.fold.block_lines import (
    blocks_in_file_order,
    blocks_of,
    property_owners,
    require_stage,
)
from bellman.fold.stage_names import lines_of
from bellman.fold.wire_terms import derivative_text, stated_derivative
from bellman.native.identity import Identity, piece_identity
from bellman.native.records import Components, typing_text
from bellman.native.versions import kept_answer
from bellman.refusals import TARGET_NOT_FOUND, ConstructionError, Location, TargetError
from bellman.stage.grains import construction_table
from bellman.stage.levels import is_declared_version
from bellman.stage.method_table import METHOD_TYPES, row_of
from bellman.syntax import terms as T
from bellman.syntax.lower import file_position
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import DOC, NODE, WRITTEN_MARK

# the components a typing entry types, in the order the signature prints them
COMPONENTS = ("method", "grid", "handler")

# the operator written as the Evaluation of a builder or of a node
EVALUATE = "evaluate"

# the derivative operator, whose places admit no typing (F44)
DERIVATIVE = "D"


@dataclasses.dataclass(frozen=True)
class Place:
    """One place of a stage: its `address` as written, its `kind` as the
    listing prints it (`builder`, `node`, `statement`, `operator <head>`,
    `definition`), the `block` that holds it or None, the operator `head`
    where it is an operator place, and `keys`, the pairs of the box that
    realizes it and the object stored there: `(box, None)` for every place
    but an Evaluation, `(box, <object>)` for each object the Evaluation
    stores, so that the whole of an Evaluation and one of its objects share
    a key and an operator head shares the keys of its occurrences."""

    address: str
    kind: str
    block: str | None
    keys: tuple
    head: str | None = None

    @property
    def admission_kind(self):
        """The kind as the `admits` column of a catalogue row writes it:
        the pair `("operator", <head>)` for an operator place, the kind
        word otherwise."""
        return ("operator", self.head) if self.head is not None else self.kind

    @property
    def boxes(self):
        """The boxes that realize the place, each once."""
        return tuple(dict.fromkeys(box for box, _ in self.keys))


@dataclasses.dataclass(frozen=True)
class Typing:
    """One typing entry resolved: the `record` of the definitions table, the
    `place` it types, the `component` and its `value`, the method word, the
    grid or the handler's program."""

    record: object
    place: Place
    component: str
    value: object


# --- the places ---


def block_box(stage, block_id):
    """The box of the block named `block_id`, or a `TargetError` naming the
    blocks the stage has."""
    for box in blocks_of(stage):
        if box.name == block_id:
            return box
    names = tuple(box.name for box in blocks_of(stage))
    raise TargetError(
        target=block_id,
        stage=stage.name,
        rule=TARGET_NOT_FOUND,
        candidates=names,
        message=f"stage {stage.name!r}: {block_id!r} is the id of no block; the blocks are "
        f"{', '.join(names) or 'none'}",
    )


def inventory(stage):
    """Every place of the stage in source order, each a `Place`: each
    builder; its named lines, a line without an id passed over and a
    property of a line with it; the occurrences of each operator head in a
    named line; the Evaluation of a `!node` line; the occurrences of each
    head in the block; the Evaluation of the builder and each object it
    stores; then each operator head of the stage, in first-occurrence order;
    then each definition. Kept for the version."""
    require_stage(stage)
    return kept_answer(stage, "place inventory", lambda: tuple(_inventory(stage)))


def places(stage):
    """The places of the stage as read-only address and kind rows, the
    listing `stage.places()` prints, bound as the method `places` of the
    stage.

    See `docs/Bellman-Sym/API/stage/07-methods.md` §1."""
    return Rows(
        [MappingProxyType({"address": place.address, "kind": place.kind}) for place in inventory(stage)]
    )


def _inventory(stage):
    table = construction_table(stage)
    heads = {}  # stage-wide head -> keys, in first-occurrence order
    for box in blocks_in_file_order(stage):
        block = box.name
        yield Place(block, "builder", block, ((block, None),))
        lines = lines_of(stage, box)
        properties = property_owners(record.address for _, record in lines)
        in_block = {}
        for holder, record in lines:
            if record.address in properties:
                continue
            named = _has_id(record)
            by_head = {}
            for position, occurrence in enumerate(record.operators):
                key = (_occurrence_box(stage, table, block, record, position, occurrence), None)
                by_head.setdefault(occurrence.stage_wide_name, []).append(key)
                heads.setdefault(occurrence.stage_wide_name, []).append(key)
                in_block.setdefault(occurrence.stage_wide_name, []).append(key)
            if not named:
                continue
            kind = "node" if record.role == NODE else "statement"
            yield Place(record.address, kind, block, ((piece_identity(record.address), None),))
            for name, keys in by_head.items():
                yield Place(
                    f"{record.address}.{name}", f"operator {_head_of(name)}", block,
                    tuple(dict.fromkeys(keys)), head=_head_of(name),
                )
            if record.role == NODE:
                evaluation = Identity("Evaluation", address=record.address)
                yield Place(
                    f"{record.address}.{EVALUATE}", f"operator {EVALUATE}", block,
                    ((evaluation, None),), head=EVALUATE,
                )
        for name, keys in in_block.items():
            yield Place(
                f"{block}.{name}", f"operator {_head_of(name)}", block,
                tuple(dict.fromkeys(keys)), head=_head_of(name),
            )
        objects = _stored_objects(stage, table, box)
        if objects:
            evaluation = Identity("Evaluation", address=block)
            yield Place(
                f"{block}.{EVALUATE}", f"operator {EVALUATE}", block,
                tuple((evaluation, written) for written in objects), head=EVALUATE,
            )
            for written in objects:
                yield Place(
                    f"{block}.{EVALUATE}[{written}]", f"operator {EVALUATE}", block,
                    ((evaluation, written),), head=EVALUATE,
                )
    for name, keys in heads.items():
        yield Place(name, f"operator {_head_of(name)}", None, tuple(dict.fromkeys(keys)), head=_head_of(name))
    for definition in stage.definitions.values():
        if definition.kind in ("function", "function_alias", "correspondence"):
            yield Place(
                definition.identity.field, "definition", None, ((definition.identity, None),)
            )


def _head_of(name):
    """The operator head of a stage-wide name: `E` of `E_ψ_ξ`, the name
    itself for every other operator."""
    return "E" if name == "E" or name.startswith("E_") else name


def _has_id(record):
    """Whether the line carries `[id=…]`, so that its address is its id and
    not its position."""
    return any(tag.startswith("id=") for tag in record.tags)


def _occurrence_box(stage, table, block, record, position, occurrence):
    """The identity of the box that realizes an occurrence: the expectation
    row born of the line, numbered among the line's expectations, or the
    one box the fold merges the expectations of several lines into
    (AMD-SG-011 §3), which answers for every one of them; for a `solve` or
    an `argmax`, the row of the builder born at the line whose outputs are
    its own unknowns; the line itself for `evaluate`, `upper_env` and `D`,
    which the fold carries inside the line's map."""
    if occurrence.head == "E":
        for row in table.by_builder(block):
            if row.kind == "Expectation" and len(row.statements) > 1 and record.address in row.statements:
                return row.identity
        n = 1 + sum(1 for other in record.operators[:position] if other.head == "E")
        return Identity("Expectation", address=record.address, occurrence=n)
    if occurrence.head in ("solve", "argmax"):
        own = [
            row
            for row in table.by_builder(block)
            if row.identity.address == record.address and row.unknowns
        ]
        if len(own) == 1:
            return own[0].identity
    return piece_identity(record.address)


def _stored_objects(stage, table, box):
    """The objects the Evaluation of a builder stores, each as the stage file
    writes it: the policy functions of a policy builder by their names, the
    value a backward value builder writes with its perch mark, `V` or `V[<]`,
    and each derivative term its derivative lines state, `D_{m_d}V` (D4,
    F47); none for a forward builder, which closes with no Evaluation."""
    evaluation = next(
        (row for row in table.by_builder(box.name) if row.identity == Identity("Evaluation", address=box.name)),
        None,
    )
    if evaluation is None:
        return ()
    objects = []
    for output in evaluation.outputs:
        if output.kind == "Evaluation":
            objects.append(output.field)
        else:
            objects.append(output.field + WRITTEN_MARK.get(output.perch, ""))
    for _, record in lines_of(stage, box):
        if record.role == DOC or record.core is None:
            continue
        parts = stated_derivative(record.core)
        if parts is not None and parts[0] in objects:
            core = record.core.core if isinstance(record.core, T.Slack) else record.core
            objects.append(derivative_text(core.lhs))
    return tuple(dict.fromkeys(objects))


# --- the typing entries resolved ---


def typings(stage, spans=None):
    """Every typing record of the definitions table resolved to its place,
    as `Typing` records in table order, kept for the version. A record that
    names no place, one at the derivative operator, a method word the
    catalogue does not hold, a word at a place its row does not admit, and a
    component typed twice are refused here, so that a stage holds no typing
    entry its signatures do not carry. On the declared version of a stage
    whose operative level holds a solution method's rows, an entry on an
    operator of those rows names no place of the declared builders and is
    passed over, the operative stage having checked it. `spans`, the span
    table of the parse the stage was constructed from, is given by the
    construction (`make_stage`, `methodized_version`), so that a refusal is
    positioned at the range of its entry and names the entry's term address;
    a later query reads the kept answer."""
    require_stage(stage)
    return kept_answer(stage, "typings", lambda: tuple(_typings(stage, spans)))


def _typings(stage, spans):
    by_address = {place.address: place for place in inventory(stage)}
    lenient = is_declared_version(stage)
    resolved = []
    for record in stage.definitions.values():
        if record.kind != "typing":
            continue
        place = by_address.get(record.identity.address)
        if place is None:
            if lenient:
                continue
            _refuse_no_place(stage, record, by_address, spans)
        component = record.identity.field
        value = record.equations[0]
        if place.head == DERIVATIVE:
            _refuse(
                stage,
                record,
                "no-method-for-derivative",
                f"the entry `{typing_text(record)}` types the {component} component of the "
                f"derivative operator `D`, which admits no typing: nothing is differentiated by "
                f"a method, and a definition by `D` is an authored expression or a handler's; "
                f"remove the entry",
                spans=spans,
                write=f"Remove the entry `{typing_text(record)}`",
            )
        if component == "method":
            _check_admission(stage, record, place, value, spans, by_address)
        resolved.append(Typing(record, place, component, value))
    _check_typed_once(stage, resolved, spans)
    return resolved


def _check_admission(stage, record, place, word, spans, by_address):
    """A method word is one of the catalogue and admits the kind of its
    place (specification 0.7 §5, "Admission"). The refusal of a word at a
    place its row does not admit offers the place of the same block the row
    admits (`_admitted_neighbour`) where there is one; `by_address` holds the
    places of the stage by their addresses."""
    row = row_of(word.name)
    if row is None:
        _refuse(
            stage,
            record,
            "syntax",
            f"the entry `{typing_text(record)}` names the method `!{word.name}`, which no row of the "
            f"catalogue holds; the methods are {', '.join('!' + tag for tag in METHOD_TYPES)}",
            spans=spans,
        )
    if place.admission_kind not in row.admits:
        admitted = ", ".join(
            " ".join(kind) if isinstance(kind, tuple) else kind for kind in row.admits
        )
        named = (
            " ".join(place.admission_kind)
            if isinstance(place.admission_kind, tuple)
            else place.admission_kind
        )
        neighbour = _admitted_neighbour(place, row, by_address)
        retyped = f"give `{place.address}` a word that admits the kind {named}"
        _refuse(
            stage,
            record,
            "method-admission",
            f"the entry `{typing_text(record)}` types `{place.address}`, a place of the kind "
            f"{named}, with `!{word.name}`, whose row of the catalogue admits {admitted}; write "
            f"the word at a place of a kind it admits, or a word that admits this place",
            spans=spans,
            write=(
                f"Write the entry at `{neighbour.address}`, `{neighbour.address}."
                f"{record.identity.field} : {to_source(T.Method(word))}`, or {retyped}"
                if neighbour is not None
                else f"Write the entry at a place of a kind `!{word.name}` admits, or {retyped}"
            ),
        )


def _admitted_neighbour(place, row, by_address):
    """The place of the block of `place` that the row `row` admits: the
    Evaluation that closes the block, for a word typed at the builder or at
    one of its operators, and otherwise the builder; None where the place
    stands in no block or the row admits neither."""
    if place.block is None:
        return None
    for address in (f"{place.block}.{EVALUATE}", place.block):
        other = by_address.get(address)
        if other is not None and other is not place and other.admission_kind in row.admits:
            return other
    return None


def _check_typed_once(stage, resolved, spans):
    """Each component is typed once at each box and object: two entries at
    one place, the whole of an Evaluation beside one of its objects, and an
    operator head beside one of its occurrences are refused naming both
    (specification 0.7 §4 rule 4; D4; F21, F26)."""
    held = {}
    for typing in resolved:
        for key in typing.place.keys:
            first = held.setdefault((typing.component, key), typing)
            if first is typing:
                continue
            _, written = key
            # the places that share a key are an operator head's and its
            # occurrences' or an Evaluation's and its objects', so one of the
            # pair names a head; both may be stage-wide places, `E_y_z` beside
            # `E_y` on one merged box, so the block is read from the place of
            # the block that holds the key
            pair = (first.place, typing.place)
            head = next(place.head for place in pair if place.head is not None)
            block = _block_of_key(stage, pair, key)
            operator = f"the operator `{head}` of block {block!r}"
            where = f"at `{first.place.address}`" if first.place.address == typing.place.address else (
                f"at `{first.place.address}` and at `{typing.place.address}`, which both reach "
                + (f"the object `{written}` stored at {operator}" if written else operator)
            )
            _refuse(
                stage,
                typing.record,
                "component-typed-twice",
                f"the {typing.component} component is typed twice, by `{typing_text(first.record)}` "
                f"at {first.record.address} and by `{typing_text(typing.record)}` here, "
                f"{where}; a component is typed by one entry; remove one of the two",
                spans=spans,
                related=(_entry_location(first.record, spans),),
                write=(
                    f"Remove one of the two entries, `{typing_text(first.record)}` or "
                    f"`{typing_text(typing.record)}`"
                ),
            )


def _block_of_key(stage, pair, key):
    """The block that holds the box of `key`: the block of a place of `pair`
    where one stands in a block, and otherwise of the place of the inventory
    that holds the key and stands in a block, which exists because every key
    of a stage-wide place is a key of an occurrence in a block."""
    return next(
        place.block
        for place in (*pair, *inventory(stage))
        if place.block is not None and key in place.keys
    )


def _refuse_no_place(stage, record, by_address, spans):
    """The refusal of an entry whose path names no place, naming what the
    first segment is and the places that stand under it."""
    address = record.identity.address
    first = address.split("[", 1)[0].split(".", 1)[0]
    blocks = [box.name for box in blocks_in_file_order(stage)]
    written = typing_text(record)
    if first in blocks:
        rest = address[len(first) + 1 :].split("[", 1)[0].split(".", 1)[0]
        if rest in blocks:
            reason = (
                f"the entry `{written}`, written inside the block {first!r}, names the block "
                f"{rest!r}; a subject inside a block names a line, an operator or the "
                f"Evaluation of that block, and an entry for another block is written at file "
                f"level or inside that block"
            )
        else:
            under = [place for place in by_address if place.startswith(first + ".")]
            reason = (
                f"the entry `{written}` names `{address}`, which is no place of the block "
                f"{first!r}; the places of the block are {', '.join(under) or 'none'}"
            )
    else:
        heads = [place for place in by_address if place.split("[", 1)[0] == place and "." not in place]
        reason = (
            f"the entry `{written}` names `{address}`, and {first!r} is no block, no definition "
            f"and no operator of the stage; the blocks are {', '.join(blocks)}, and the "
            f"operators and definitions {', '.join(name for name in heads if name not in blocks) or 'none'}"
        )
    _refuse(stage, record, "name-in-scope", reason, spans=spans)


def _refuse(stage, record, rule, message, *, spans, related=(), write=None):
    """The refusal of a typing record under `rule`, at the range of its entry
    and with the entry's term address where the span table `spans` holds
    them (`_entry_position`), with the `related` locations the sentence
    names and the action `write` where the check establishes the edit."""
    file, line, column, end_line, end_column, address = _entry_position(record, spans)
    raise ConstructionError(
        message,
        stage=stage.name,
        file=file,
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
        address=address,
        rule=rule,
        related=related,
        write=write,
    )


def _entry_location(record, spans):
    """The `Location` of a typing record's entry, the first of the two entries
    a refusal names, under the role `original declaration`."""
    file, line, column, end_line, end_column, address = _entry_position(record, spans)
    return Location("original declaration", file, line, column, end_line, end_column, address)


def _entry_position(record, spans):
    """The position of a typing record's entry: the file, the line and the
    column its address holds, `<file>:<line>:<column>`, then the end of the
    entry and its term address, read from the span of the span table `spans`
    of the parse that writes that position (`file_position`), the entry's
    own. The end is None and the address the record's own without the table,
    or where no span writes the position."""
    file, line, column = _position(record.address)
    for key, span in (spans or {}).items():
        if f"{file_position(span)}:{span.column}" == record.address:
            return file, line, column, span.end_line, span.end_column, key
    return file, line, column, None, None, record.address


def _position(address):
    """The file, the line and the column a typing record's address writes,
    each None where the address holds no position."""
    file, _, column = str(address).rpartition(":")
    file, _, line = file.rpartition(":")
    if not (line.isdigit() and column.isdigit()):
        return None, None, None
    return file or None, int(line), int(column)


# --- the components read off the typing entries ---


def components_by_place(stage):
    """The components typed at each place, by the place's address in the
    order of the inventory, as a read-only mapping from address to
    `Components`; a place with no entry has no row. Kept for the version."""

    def compute():
        held = {}
        for typing in typings(stage):
            held.setdefault(typing.place.address, {})[typing.component] = typing.value
        order = {place.address: n for n, place in enumerate(inventory(stage))}
        return MappingProxyType(
            {
                address: Components(**held[address])
                for address in sorted(held, key=lambda a: order.get(a, len(order)))
            }
        )

    return kept_answer(stage, "components", compute)


def is_methodized(stage):
    """Whether the version is methodized: an operator's signature carries a
    method component (specification 0.7, decision S7-W7). A grid or a
    handler typed alone leaves the version symbolic, since neither names a
    method. The stage sheet and the version word (`inventory.py`) and the
    collection label of Model Explorer read this one answer."""
    return any(held.method is not None for held in components_by_place(stage).values())


def components_at(stage, keys):
    """The places whose keys meet `keys`, pairs of a box and an object, with
    the components typed at each, as `(Place, Components)` pairs in the order
    of the inventory; empty where nothing is typed there."""
    wanted = set(keys)
    by_place = components_by_place(stage)
    return tuple(
        (place, by_place[place.address])
        for place in inventory(stage)
        if place.address in by_place and any(key in wanted for key in place.keys)
    )


def components_of_box(stage, box_name):
    """The places realized by the box named `box_name`, the name of a builder
    or the identity of a row, with the components typed at each, as
    `(Place, Components)` pairs; the whole of an Evaluation and each object
    typed at it among them."""
    by_place = components_by_place(stage)
    return tuple(
        (place, by_place[place.address])
        for place in inventory(stage)
        if place.address in by_place and any(box == box_name for box, _ in place.keys)
    )


def places_within(stage, names):
    """The places whose keys name one of the boxes `names`, builder names and
    row identities, with the components typed at each."""
    wanted = set(names)
    by_place = components_by_place(stage)
    return tuple(
        (place, by_place[place.address])
        for place in inventory(stage)
        if place.address in by_place and any(box in wanted for box, _ in place.keys)
    )


def admitted_methods(stage, address):
    """The method words of the catalogue, in its order, that a typing entry
    may name at the place `address`, each spelled as a `.bl` entry writes
    it, `!gauss_hermite` for the catalogue's `gauss-hermite`: each method
    whose row admits the kind of the place; none at the derivative operator.
    A name that is no place is refused with the places the stage has. The
    Methods tab of Bellman Workbench offers these words at a place."""
    place = next((held for held in inventory(stage) if held.address == address), None)
    if place is None:
        raise TargetError(
            target=address,
            stage=stage.name,
            rule=TARGET_NOT_FOUND,
            candidates=tuple(held.address for held in inventory(stage)),
            message=f"stage {stage.name!r}: {address!r} is no place of the stage; "
            f"stage.places() lists them",
        )
    if place.head == DERIVATIVE:
        return ()
    return tuple(
        f"!{tag.replace('-', '_')}"
        for tag, row in METHOD_TYPES.items()
        if place.admission_kind in row.admits
    )
