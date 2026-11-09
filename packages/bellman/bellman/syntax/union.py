"""The union of a stage file and its additions, on their parsed trees.

A methods file is an addition to its stage file: a `.bl` file whose first line
is `@methods: <stage>`, read by the stage grammar, whose items the union adds
to the items of the stage file (specification 0.7 §4, the eight rules as
decided on 4 November 2026). `union` takes the parsed stage file and its parsed
additions, each the pair `(term, spans)` that `parse_with_spans` answers, and
answers the same pair for the unioned file: one `FILE` term, which the
construction reads as if every entry and line had been written in the stage
file, and the span table that names, for every item, the file and the position
it was written at. That provenance is what defines the declared level of the
stage, the stage file's own tree, the tables of the parameters and of the
settings, and the erasure of the additions.

The rules, each on the constructors of the term and on nothing else:

1. The stage file names itself, `@stage: x`, and each addition names that
   stage, `@methods: x`; the addition's line is consumed, and a metadata line
   of another key is one with the stage file's line of that key or is refused.
2. A file-level declaration, assignment, law or function definition of an
   addition is appended after the stage file's items; an item equal to one an
   earlier file holds is one item, and a name defined in two files with
   different content is refused.
3. A block of an addition whose `id` the union holds merges with that block;
   a block with an id the union lacks is kept whole; a nested block merges by
   its `label` under its parent, and a label the parent lacks is refused.
4. The entries of a header are a keyed collection: a tag by its text, a pair by
   its key, a typing entry or a handler binding by the path of the component
   it types, read relative to the block and refused when its first segment
   names another block, and the signature coordinate by coordinate with
   identity by field name, the stage's typing kept, a differing type refused,
   an empty side adding nothing and a perch word on a side agreeing. Two
   entries with one key and equal content are one; with different content
   they are refused.
5. The lines of an addition's block are appended after the block's lines; a
   line id written twice in one block is refused. The reading of a block
   under the word of its method component at two levels is the elaborator's
   (`bellman.stage.levels.operative_level`), so that this module
   knows no word of the vocabulary.
6. The erasure: the stage file's own tree is the parsed pair the caller gave,
   and every item of the union carries its file, so that the items whose
   file is the stage file's are the stage file's items.
7. A typing entry or a handler binding written at file level is attached to
   the annotation of the innermost block its path names, a nested block by its
   label among them, with the rest of the path relative to that block; one
   whose first segment names no block stays at file level, keyed by its path.
8. An entry is appended to the annotation it is attached to; a coordinate is
   appended to the side of the signature its arrow names.

A typing entry or a handler binding the stage file itself writes, in a header
or at file level, is kept and attached as an addition's is (rules 7 and 8), the
explicit way of writing the same entries, and the construction binds it with
the additions' entries (`bellman.stage.places`).
The refusals of the union are `ConstructionError`s under `declared-twice`,
`label-not-in-parent`, `type-conflict` and `metadata-mismatch`, each positioned
at the item of the later file, naming the position of the earlier item in its
sentence and carrying that item as a related location under the role
`original declaration` (Model Interface 0.9 §4).
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from types import MappingProxyType

from bellman.refusals import construction_error, location
from bellman.syntax import terms as T
from bellman.syntax.lower import ParsedFile, item_addresses
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import PERCH_OF_SIDE, ROLE_WORD, VALUE_ROLES, WRITTEN_MARK

__all__ = ("ADDITION_KEY", "STAGE_KEY", "is_typing_entry", "union")

# the metadata key of a stage file and that of an addition
STAGE_KEY = "stage"
ADDITION_KEY = "methods"


def union(stage, additions=()):
    """The union of the parsed stage file `stage` and the parsed `additions`,
    in order, as a `ParsedFile`: the stage file is the left unit, and each
    addition is added to the union of the files before it by the eight rules
    of the module docstring. Refuses as the module docstring says."""
    files = [stage, *additions]
    working = _Union(files)
    working.read_stage()
    for number in range(1, len(files)):
        working.add(number)
    return working.result()


# --- the union while it is built ---


@dataclasses.dataclass
class _Entry:
    """One entry of a block's annotation as the union holds it: the key it is
    compared by, the entry term with its subject relative to the block, the
    entry as its file wrote it, for a sentence that names it, the file it
    came from and the key of its position in that file's span table, None
    where its position is the block's."""

    key: object
    entry: object
    text: str
    source: int
    span_key: str | None


@dataclasses.dataclass
class _Node:
    """One item of the union: the item as its file wrote it, the file and the
    item's address in that file's span table, which for a block is its address
    in the union as well, since a block is addressed by its id and a nested
    block by its label; for a block, its entries and its body, from which the
    block is rebuilt."""

    item: object
    source: int
    address: str
    entries: list = dataclasses.field(default_factory=list)
    body: list = dataclasses.field(default_factory=list)

    @property
    def label(self):
        """The label of a nested block, None for every other item."""
        return _entry(self.item.tag, "label") if isinstance(self.item, T.Block) else None

    def nested(self, label):
        """The nested block of this block labeled `label`, or None."""
        return next((node for node in self.body if node.label == label), None)

    def line_ids(self):
        """The ids of the lines of this block, each with its node."""
        return {
            _entry(node.item.annot, "id"): node
            for node in self.body
            if isinstance(node.item, (T.Statement, T.Declare))
            and _entry(node.item.annot, "id") is not None
        }


class _Union:
    """The union of the files, built file by file."""

    def __init__(self, files):
        self.files = files
        self.items = []
        self.blocks = {}
        self.defined = {}
        self.metadata = {}
        self.stage_name = None
        # the ids of the top-level blocks of every file, by which a path's
        # first segment is known to name another block (rule 7)
        self.block_ids = {
            _entry(item.tag, "id")
            for parsed in files
            for item in parsed.term.items
            if isinstance(item, T.Block) and _entry(item.tag, "id") is not None
        }

    # --- the stage file ---

    def read_stage(self):
        """The stage file, the left unit of the union: its items in order,
        the entries of its headers keyed as an addition's are (rule 4), and a
        typing entry or a handler binding written at its file level routed
        after its blocks are read, as an addition's is (rule 7)."""
        deferred = []
        for address, item in _top_level(self.files[0].term):
            if isinstance(item, T.Metadata):
                if item.key == STAGE_KEY:
                    self.stage_name = item.value
                self.metadata[item.key] = (item.value, 0, address)
                self.items.append(_Node(item, 0, address))
            elif isinstance(item, T.Block):
                node = self.new_block(0, address, item, _path_of(item))
                self.items.append(node)
                if _entry(item.tag, "id") is not None:
                    self.blocks[_entry(item.tag, "id")] = node
            elif _is_typing_entry(item):
                deferred.append((address, item))
            else:
                self.add_definition(0, address, item)
        for address, item in deferred:
            self.route(0, address, item)

    # --- an addition ---

    def add(self, number):
        items = _top_level(self.files[number].term)
        self.check_metadata(number, items)
        deferred = []
        for address, item in items:
            if isinstance(item, T.Metadata):
                continue
            if _is_typing_entry(item):
                deferred.append((address, item))
            elif isinstance(item, T.Block):
                self.place_block(number, address, item)
            else:
                self.add_definition(number, address, item)
        for address, item in deferred:
            self.route(number, address, item)

    def check_metadata(self, number, items):
        """Rule 1: the addition names the stage, and a metadata line of another
        key agrees with the stage file's line of that key or is appended."""
        named = [(address, item) for address, item in items if isinstance(item, T.Metadata)]
        first_line = (
            None
            if self.stage_name is None
            else f"Write `@methods: {self.stage_name}` as the file's first line"
        )
        if not any(item.key == ADDITION_KEY for _, item in named):
            raise self.refuse(
                "metadata-mismatch",
                number,
                items[0][0],
                "the file names no stage: an addition begins with `@methods: <stage>`, the "
                "name of the stage file it adds to",
                write=first_line,
            )
        for address, item in named:
            if item.key == ADDITION_KEY:
                if self.stage_name is not None and item.value != self.stage_name:
                    _, source, held = self.metadata[STAGE_KEY]
                    raise self.refuse(
                        "metadata-mismatch",
                        number,
                        address,
                        f"the addition names the stage {item.value!r}, and the stage file names "
                        f"itself {self.stage_name!r} at {self.where(source, held)}; an addition's "
                        f"first line is `@methods: <stage>` with the name of the stage file it "
                        f"adds to",
                        related=(self.location(source, held),),
                        write=f"Write `@methods: {self.stage_name}`",
                    )
            elif item.key == STAGE_KEY:
                raise self.refuse(
                    "metadata-mismatch",
                    number,
                    address,
                    f"the file names itself a stage, `@stage: {item.value}`; an addition names "
                    f"the stage it adds to, `@methods: {item.value}`, and a stage file is added "
                    f"to no stage",
                    write=None if first_line is None else f"Remove the `@stage` line; {first_line}",
                )
            elif item.key in self.metadata:
                value, source, held = self.metadata[item.key]
                if value != item.value:
                    raise self.refuse(
                        "metadata-mismatch",
                        number,
                        address,
                        f"the metadata line `@{item.key}` carries {item.value!r} here and "
                        f"{value!r} at {self.where(source, held)}; a key is written once over "
                        f"the files of a stage, or identically in each file",
                        related=(self.location(source, held),),
                        write=f"Write `@{item.key}: {value}`, or remove the line",
                    )
            else:
                self.metadata[item.key] = (item.value, number, address)
                self.items.append(_Node(item, number, address))

    def add_definition(self, number, address, item):
        """Rule 2: a file-level item, by the names it defines. Two items of one
        file are left to the construction, whose rule `declared-once` judges
        them."""
        node = _Node(item, number, address)
        for key in _defined_names(item):
            held = self.defined.get(key)
            if held is None or held.source == number:
                continue
            if held.item == item:
                return
            # a law is keyed by its subjects, and named by them
            defined = (
                f"definition of {key!r}"
                if isinstance(key, str)
                else f"distribution declaration of {', '.join(map(str, key[1]))}"
            )
            raise self.refuse(
                "declared-twice",
                number,
                address,
                f"the name {key!r} is defined in two files with different content: at "
                f"{self.where(held.source, held.address)} and here; a name defined in both "
                f"files is one definition, written once or identically in each file",
                related=(self.location(held.source, held.address),),
                write=(
                    f"Remove the {defined} from one of the two files, or write it identically "
                    f"in both"
                ),
            )
        for key in _defined_names(item):
            self.defined.setdefault(key, node)
        self.items.append(node)

    def place_block(self, number, address, block):
        """Rule 3: a block of an addition, merged by its id or kept whole."""
        block_id = _entry(block.tag, "id")
        held = self.blocks.get(block_id) if block_id is not None else None
        if held is not None:
            self.merge(held, number, address, block, (block_id,))
            return
        node = self.new_block(number, address, block, _path_of(block))
        self.items.append(node)
        if block_id is not None:
            self.blocks[block_id] = node

    def new_block(self, number, address, block, path):
        """A block kept whole: its nested blocks placed under it, then its
        entries keyed, each typing entry read relative to the block."""
        node = _Node(block, number, address)
        for n, item in enumerate(block.body, 1):
            if isinstance(item, T.Block):
                label = _entry(item.tag, "label") or _entry(item.tag, "id")
                nested = self.new_block(number, f"{address}.{label or n}", item, path + (label,))
                node.body.append(nested)
            else:
                node.body.append(_Node(item, number, f"{address}.{_entry(item.annot, 'id') or n}"))
        for entry in block.tag.entries:
            self.attach(node, entry, number, address, path)
        return node

    def merge(self, base, number, address, block, path):
        """Rules 3, 4 and 5: the block `block` of the addition merged into the
        block `base` the union holds at the same id or label."""
        for entry in block.tag.entries:
            self.attach(base, entry, number, address, path)
        ids = base.line_ids()
        for n, item in enumerate(block.body, 1):
            if isinstance(item, T.Block):
                label = _entry(item.tag, "label")
                nested_address = f"{address}.{label or n}"
                nested = base.nested(label) if label is not None else None
                if nested is None:
                    labels = [node.label for node in base.body if node.label is not None]
                    raise self.refuse(
                        "label-not-in-parent",
                        number,
                        nested_address,
                        f"the nested block `label={label}` has no branch of that label in block "
                        f"{base.address!r}, whose header stands at "
                        f"{self.where(base.source, base.address)}; a nested block of an "
                        f"addition merges with the branch of the same label under its parent, "
                        f"and the union adds no branch",
                        related=(self.location(base.source, base.address),),
                        write=(
                            f"Write the nested block under one of the labels block "
                            f"{base.address!r} holds: {', '.join(labels)}"
                            if labels
                            else None
                        ),
                    )
                self.merge(nested, number, nested_address, item, path + (label,))
                continue
            line_id = _entry(item.annot, "id")
            line_address = f"{address}.{line_id or n}"
            if line_id is not None and line_id in ids:
                held = ids[line_id]
                raise self.refuse(
                    "declared-twice",
                    number,
                    line_address,
                    f"the line id {line_id!r} is written twice in block {base.address!r}: at "
                    f"{self.where(held.source, held.address)} and here; an id names one line "
                    f"of a block over the files of a stage, so give this line another id",
                    related=(self.location(held.source, held.address),),
                    write=f"Give this line an id other than {line_id!r}",
                )
            node = _Node(item, number, line_address)
            base.body.append(node)
            if line_id is not None:
                ids[line_id] = node

    # --- the entries of a header ---

    def attach(self, node, entry, number, address, path):
        """Rule 4: one entry of a header, keyed, merged with the entry of the
        same key the block holds or appended; a typing entry is attached to
        the innermost block its path names (rule 7)."""
        if isinstance(entry, T.Typer) and isinstance(entry.typing, T.Signature):
            self.attach_signature(node, entry, number, address)
            return
        span_key, text = None, _entry_text(entry)
        if isinstance(entry, T.Typer) and is_typing_entry(entry.typing):
            span_key = f"{address}.{to_source(entry.typing.subject)}"
            node, relative = self.resolve(node, path, entry.typing.subject, number, span_key)
            entry = T.Typer(dataclasses.replace(entry.typing, subject=relative))
            key = ("typing", relative)
        elif isinstance(entry, T.KeyValue):
            key = ("key", entry.key)
        elif isinstance(entry, T.Tag):
            key = ("tag", entry.tag)
        elif isinstance(entry, T.Tagged):
            key = ("tagged", entry.tag.name)
        else:
            key = ("marked", type(entry).__name__, type(getattr(entry, "typing", None)).__name__)
        self.keep(node, _Entry(key, entry, text, number, span_key), address)

    def keep(self, node, placed, address):
        """The entry `placed` kept on `node`: one with an entry of the same key
        and content the block holds, refused beside one of different
        content, and appended otherwise."""
        held = next((other for other in node.entries if other.key == placed.key), None)
        if held is None:
            node.entries.append(placed)
            return
        if held.entry == placed.entry:
            return
        what = (
            f"the component `{to_source(placed.key[1])}`"
            if placed.key[0] == "typing"
            else f"the entry `{placed.text}`"
        )
        raise self.refuse(
            "declared-twice",
            placed.source,
            placed.span_key or address,
            f"{what} of block {node.address!r} is written twice with different content: "
            f"`{held.text}` at {self.where(held.source, held.span_key or node.address)} and "
            f"`{placed.text}` here; a component holds one entry over the files of a stage, "
            f"so keep one of the two",
            related=(self.location(held.source, held.span_key or node.address),),
            write=f"Keep one of the two entries, `{held.text}` or `{placed.text}`",
        )

    def resolve(self, node, path, subject, number, span_key):
        """The block a path names and the path relative to it: the block's
        own address, or in a nested block its label alone, is removed from
        the front of the path; a first segment that names another block is
        refused; a first segment that names a nested block of the block
        descends into it."""
        segments = list(subject.segments)
        for prefix in (path, path[-1:] if len(path) > 1 else ()):
            n = len(prefix)
            if (
                n
                and len(segments) > n
                and all(s.name == name and not s.selectors for s, name in zip(segments, prefix))
            ):
                segments = segments[n:]
                break
        if segments[0].name in self.block_ids and not segments[0].selectors:
            other = self.blocks.get(segments[0].name)
            where = (
                f", whose header stands at {self.where(other.source, other.address)}"
                if other is not None
                else ""
            )
            raise self.refuse(
                "label-not-in-parent",
                number,
                span_key,
                f"the entry `{to_source(subject)}` of block {node.address!r} names the block "
                f"{segments[0].name!r} by its first segment{where}; a path inside a block names "
                f"a line or an operator of that block, so write the entry in block "
                f"{segments[0].name!r} or at file level",
                related=() if other is None else (self.location(other.source, other.address),),
                write=f"Write the entry in block {segments[0].name!r} or at file level",
            )
        return self.descend(node, segments)

    def descend(self, node, segments):
        """The innermost nested block the leading segments of a path name,
        and the path relative to it."""
        while len(segments) > 1 and not segments[0].selectors:
            nested = node.nested(segments[0].name)
            if nested is None:
                break
            node, segments = nested, segments[1:]
        return node, T.Path(tuple(segments))

    def route(self, number, address, item):
        """Rule 7: a typing entry or a handler binding written at file level,
        attached to the block its first segment names, or kept at file level
        where its first segment names no block."""
        typing = item.declaration
        segments = list(typing.subject.segments)
        block = self.blocks.get(segments[0].name) if not segments[0].selectors else None
        if block is None:
            key = ("entry", typing.subject)
            held = self.defined.get(key)
            if held is not None and held.source != number:
                if held.item == item:
                    return
                raise self.refuse(
                    "declared-twice",
                    number,
                    address,
                    f"the component `{to_source(typing.subject)}` is typed twice at file level "
                    f"with different content: at {self.where(held.source, held.address)} and "
                    f"here; a component holds one entry over the files of a stage",
                    related=(self.location(held.source, held.address),),
                    write=(
                        f"Keep one of the two entries, "
                        f"`{_entry_text(T.Typer(held.item.declaration))}` or "
                        f"`{_entry_text(T.Typer(typing))}`"
                    ),
                )
            node = _Node(item, number, address)
            self.defined.setdefault(key, node)
            self.items.append(node)
            return
        node, relative = self.descend(block, segments[1:])
        entry = T.Typer(dataclasses.replace(typing, subject=relative))
        placed = _Entry(("typing", relative), entry, _entry_text(T.Typer(typing)), number, address)
        self.keep(node, placed, address)

    def attach_signature(self, node, entry, number, address):
        """Rule 4 on the signature: the addition's signature unioned into the
        block's coordinate by coordinate, or taken whole where the block
        states none."""
        held = next((other for other in node.entries if other.key == ("signature",)), None)
        if held is None:
            node.entries.append(_Entry(("signature",), entry, "the signature", number, None))
            return
        merged = held.entry.typing
        for side, subject, types in (
            ("in", "source", "source_types"),
            ("out", "target", "target_types"),
        ):
            base, added = getattr(merged, subject), getattr(entry.typing, subject)
            coordinates = list(base.coordinates)
            index = {
                _written(c): i for i, c in enumerate(coordinates) if isinstance(c, T.Coordinate)
            }
            for coordinate in added.coordinates:
                if not isinstance(coordinate, T.Coordinate) or _written(coordinate) not in index:
                    coordinates.append(coordinate)
                    if isinstance(coordinate, T.Coordinate):
                        index[_written(coordinate)] = len(coordinates) - 1
                    continue
                at = index[_written(coordinate)]
                stated = coordinates[at]
                if not coordinate.classifiers:
                    continue
                if not stated.classifiers:
                    coordinates[at] = dataclasses.replace(
                        stated, classifiers=coordinate.classifiers
                    )
                    continue
                if not _same_typing(stated.classifiers, coordinate.classifiers):
                    field = f"{side}.{_written(coordinate)}"
                    raise self.refuse(
                        "type-conflict",
                        number,
                        f"{address}.{field}",
                        f"the coordinate {_written(coordinate)!r} on the {_SIDE_WORD[side]} side "
                        f"of block {node.address!r} is typed `{_typing_text(stated.classifiers)}` "
                        f"at {self.where(held.source, f'{node.address}.{field}')} and "
                        f"`{_typing_text(coordinate.classifiers)}` here; the field names "
                        f"determine the signature and the stage's typing is kept, so write the "
                        f"coordinate without a type or with the stage's",
                        related=(self.location(held.source, f"{node.address}.{field}"),),
                        write=(
                            f"Write `{_written(coordinate)}` without a type, or with the "
                            f"stage's, `{_written(coordinate)} : "
                            f"{_typing_text(stated.classifiers)}`"
                        ),
                    )
            base_types, added_types = getattr(merged, types), getattr(entry.typing, types)
            if added_types and base_types and added_types != base_types:
                raise self.refuse(
                    "type-conflict",
                    number,
                    f"{address}.{side}",
                    f"the {_SIDE_WORD[side]} side of block {node.address!r} carries the perch "
                    f"word `{_typing_text(added_types)}` here and `{_typing_text(base_types)}` "
                    f"at {self.where(held.source, f'{node.address}.{side}')}; the perch of a side "
                    f"is the stage's, so write the side with the stage's perch word or without "
                    f"one",
                    related=(self.location(held.source, f"{node.address}.{side}"),),
                    write=(
                        f"Write the side with the stage's perch word, "
                        f"`{_typing_text(base_types)}`, or without one"
                    ),
                )
            merged = dataclasses.replace(
                merged,
                **{
                    subject: dataclasses.replace(base, coordinates=tuple(coordinates)),
                    types: base_types or added_types,
                },
            )
        held.entry = T.Typer(merged)

    # --- the refusals and the positions ---

    def span(self, source, key):
        """The span of `key` in the table of file `source`, or None."""
        return self.files[source].spans.get(key) if key is not None else None

    def where(self, source, key):
        """The position of an item of file `source`, as a sentence names a
        second item: `file:line:column (term address 'x')`."""
        span = self.span(source, key)
        if span is None:
            return f"term address {key!r}"
        return f"{span.file}:{span.line}:{span.column} (term address {key!r})"

    def location(self, source, key):
        """The `Location` of an item of file `source`, the earlier item of a
        pair a refusal names beside the item it is raised at, under the role
        `original declaration`."""
        span = self.span(source, key)
        return location(
            "original declaration",
            address=key,
            span=span,
            file=None if span is not None else _file_of(self.files[source]),
        )

    def refuse(self, rule, source, key, message, *, related=(), write=None):
        """The refusal under `rule` at the item `key` of file `source`, with
        the `related` locations its sentence names and the action `write`
        where the union establishes the edit."""
        span = self.span(source, key)
        return construction_error(
            message,
            stage=self.stage_name,
            address=key,
            span=span,
            rule=rule,
            file=None if span is not None else _file_of(self.files[source]),
            related=related,
            write=write,
        )

    # --- the result ---

    def result(self):
        """The unioned `ParsedFile`: the term rebuilt from the nodes, and the
        span table of every item, of every typing entry of a header and of
        every side and field of a header."""
        term = T.FILE(tuple(_rebuilt(node) for node in self.items))
        placed = [each for node in self.items for each in _flattened(node)]
        addresses = item_addresses(term)
        if len(addresses) != len(placed):
            raise AssertionError("the items of the union and their addresses disagree")
        table = {}
        for (address, _), node in zip(addresses, placed):
            span = self.span(node.source, node.address)
            if span is not None:
                table[address] = span
        for (address, _), node in zip(addresses, placed):
            if not isinstance(node.item, T.Block):
                continue
            for each in node.entries:
                span = self.span(each.source, each.span_key)
                if span is not None and each.key[0] == "typing":
                    table.setdefault(f"{address}.{to_source(each.key[1])}", span)
            prefix = f"{address}."
            for parsed in self.files:
                for key, span in parsed.spans.items():
                    if key.startswith(prefix) and key[len(prefix) :].split(".", 1)[0] in _SIDES:
                        table.setdefault(key, span)
        return ParsedFile(term, MappingProxyType(table))


# --- the terms rebuilt from the nodes ---


def _rebuilt(node):
    """The item of a node: a block from its entries and its body."""
    if not isinstance(node.item, T.Block):
        return node.item
    return T.Block(
        T.Annotation(tuple(each.entry for each in node.entries)),
        tuple(_rebuilt(child) for child in node.body),
    )


def _flattened(node):
    """The node and, for a block, the nodes of its body, in the order
    `item_addresses` visits the rebuilt items."""
    yield node
    if isinstance(node.item, T.Block):
        for child in node.body:
            yield from _flattened(child)


# --- what the rules read of a term ---

_SIDES = ("in", "out")
_SIDE_WORD = {"in": "input", "out": "output"}


def _top_level(term):
    """The top-level items of a term with their addresses."""
    return [(address, item) for address, item in item_addresses(term) if "." not in address]


def _entry(annotation, key):
    """The value of the first `key=` entry of an annotation, or None."""
    if annotation is None:
        return None
    for e in annotation.entries:
        if isinstance(e, T.KeyValue) and e.key == key:
            return e.value
    return None


def _path_of(block):
    """The address of a top-level block as a path of segments: its id, or
    nothing for a block without one."""
    block_id = _entry(block.tag, "id")
    return (block_id,) if block_id is not None else ()


def is_typing_entry(typing):
    """Whether a `Typer`'s typing is a typing entry or a handler binding of
    specification 0.7, `policy.method : !egm`, `policy.grid : !Cartesian(…)`
    or `policy.handler : "cons-port:egm"`: a `Handler`, or a `Declaration`
    whose subject is a `Path`; a signature and a field's declaration are
    neither. The one predicate, read by the union, the declaration pass, the
    fold and the writer of the typing entries."""
    return isinstance(typing, T.Handler) or (
        isinstance(typing, T.Declaration) and isinstance(typing.subject, T.Path)
    )


def _is_typing_entry(item):
    """Whether a file-level item is a typing entry or a handler binding."""
    return isinstance(item, T.Declare) and is_typing_entry(item.declaration)


def _defined_names(item):
    """The keys a file-level item defines: each declared name, the target of
    an assignment, the name of a function or correspondence definition, the
    subjects of a law; none for an item that defines no name."""
    if isinstance(item, T.Declare) and isinstance(item.declaration, T.Declaration):
        return tuple(_stems(item.declaration.subject))
    if isinstance(item, T.Statement):
        core = item.core
        if isinstance(core, T.Assignment) and isinstance(core.target, T.Constant):
            return (core.target.name,)
        if isinstance(core, (T.FuncDef, T.CorrDef)):
            return (core.name,)
        if isinstance(core, T.Law):
            return (("law", core.subjects),)
    return ()


def _stems(subject):
    """The names a subject lists, a tuple's names among them."""
    for coordinate in getattr(subject, "coordinates", ()):
        if isinstance(coordinate, T.Coordinate):
            yield coordinate.stem
        elif isinstance(coordinate, T.Group):
            yield from _stems(coordinate.inner)


def _written(coordinate):
    """A listed field as the file writes it, its stem with its perch mark,
    `V[>]`, `V[<]` or `c`, the identity of a coordinate in a signature."""
    if coordinate.at is None:
        return coordinate.stem
    return coordinate.stem + WRITTEN_MARK[PERCH_OF_SIDE[type(coordinate.at.side)]]


def _canonical(classifier):
    """A classifier as the comparison of two typings reads it: a finite set
    of labels by its members and not by their order, every other classifier
    as the term it is."""
    if isinstance(classifier, T.Domain) and isinstance(classifier.space, T.FiniteSet):
        return ("labels", frozenset(classifier.space.members))
    return classifier


def _same_typing(held, added):
    """Whether two typings of one coordinate agree, as unordered conjunctions
    of their classifiers."""
    return Counter(map(_canonical, held)) == Counter(map(_canonical, added))


def _typing_text(classifiers):
    """A typing as written, `ℝ @ !vlu`."""
    return " @ ".join(_classifier_text(c) for c in classifiers)


def _classifier_text(classifier):
    """One classifier as written: a set, a role word or a perch word."""
    if isinstance(classifier, T.Domain):
        return to_source(classifier.space)
    if isinstance(classifier, T.Role):
        kind = classifier.kind
        if isinstance(kind, T.Value):
            return "!" + ROLE_WORD[VALUE_ROLES[kind.order]]
        return "!" + ROLE_WORD[type(kind).__name__.lower()]
    if isinstance(classifier, T.Infoset):
        return "!" + PERCH_OF_SIDE[type(classifier.side)]
    return to_source(classifier)


def _entry_text(entry):
    """An entry of a header as written, `method : !egm`, `id=policy`."""
    if isinstance(entry, T.Typer) and isinstance(entry.typing, T.Handler):
        return f'{to_source(entry.typing.subject)} : "{entry.typing.program}"'
    if isinstance(entry, T.Typer) and isinstance(entry.typing, T.Declaration):
        return f"{to_source(entry.typing.subject)} : {to_source(entry.typing.classifiers[0])}"
    if isinstance(entry, T.KeyValue):
        return f"{entry.key}={entry.value}"
    if isinstance(entry, T.Tag):
        return str(entry.tag)
    if isinstance(entry, T.Tagged):
        return to_source(entry.tag)[1:]
    return type(entry).__name__


def _file_of(parsed):
    """The file the spans of a parsed file name, or None."""
    return next((span.file for span in parsed.spans.values()), None)
