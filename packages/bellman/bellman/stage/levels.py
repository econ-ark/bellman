"""The two levels of a stage and the reading of an addition (specification
0.6 §1; specification 0.7 §4 rules 5 and 6, §6, D8).

A stage is elaborated from one tree, the stage file's own or its union with
its additions (`bellman.syntax.union`), and every item of the tree carries
the file it was written in, which the span table of the parse records
(`SourceSpan.file`). A block whose method component holds a solution method
and to which an addition appends lines that are not derivative lines is read
at two levels: at the declared level the block holds the stage file's lines,
and at the operative level, `stage.builder`, the appended lines stand in
place of them as the method's rows; a derivative line stands at both levels,
and a solution method with no appended row leaves the declared lines. A
block whose method component holds no solution method reads every appended
line as an authored line of the block. `operative_level` is that reading on
the parsed union, and `construct` builds the fields of a stage from a tree
with both levels: the stage holds the declared definitions and graphs, and
the rows of the operative level as the `BoundBlock` records of
`bindings.blocks`, from which `grains.construction_table` makes the
operative table and the operative builders graph is derived.

`declared_version` is the stage as its stage file declares it, which
`stage.declared` reads: for a stage into which additions have been read, the
stage file elaborated alone (rule 6, the erasure), and otherwise the stage
with its bindings left out. `read_addition` is the one reader of an
addition, a `.bl` file by its path or a mapping holding its text, and
`load_additions` reads every addition a methods source names, which the
construction and `methodize` union with the stage file's tree; the record of
each addition in a version's provenance is `addition_records`.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

from bellman.fold.wire_terms import stated_derivative
from bellman.native.frozen import freeze
from bellman.native.identity import Identity
from bellman.native.records import BoundBlock, refuse_at_entry
from bellman.native.versions import kept_answer, replace_stage, stored
from bellman.refusals import ConstructionError
from bellman.stage.construction import stage_fields
from bellman.stage.explicit import check_addition, check_explicit, formula_only, method_entry
from bellman.stage.grains import construction_table, declared_definitions, declared_table
from bellman.stage.method_table import is_solution_method, row_of
from bellman.stage.representations import bound_families
from bellman.syntax import terms as T
from bellman.syntax.lower import ParsedFile, item_addresses, parse_with_spans

__all__ = (
    "addition_records",
    "construct",
    "declared_version",
    "holds_additions",
    "is_declared_version",
    "load_additions",
    "methods_location",
    "methods_source",
    "operative_definitions",
    "operative_level",
    "read_addition",
    "source_texts",
    "supplies_addition",
)


# --- the construction at two levels ---


def operative_level(parsed):
    """The parsed union of a stage file and its additions at the operative
    level (specification 0.7 §4 rule 5 as decided, D8): in a top-level block
    whose own method component holds a solution method of the catalogue and
    whose body holds a row of another file, a line that is neither a nested
    block nor a derivative line, the stage file's rows are left out, since
    the addition's rows compute the builder's output in their place; the
    block's nested blocks and derivative lines stay. Every other item stays,
    and the span table is rebuilt at the kept items' addresses. A pair to
    which no addition brings such rows is answered as given."""
    term, spans = parsed
    files = _files(term, spans)
    rows = _appended_rows(term, files)
    if not rows:
        return parsed
    return ParsedFile(*_operative_tree(term, spans, files, rows))


def construct(cls, term, spans):
    """The fields of the stage of `term`, of the class `cls`, at its declared
    level, with the rows of its operative level under `bindings.blocks`
    where a block's method component holds a solution method and the tree
    appends rows to it (D8). `spans` is the span table of the tree, whose
    files tell an appended line from one of the stage file, or None for a
    decoded term, which holds no appended line.

    The bindings keep the record of each representation family the typing
    entries name, as it stands now (`representations.bound_families`). A
    builder whose method is `!explicit` is checked on the declared level,
    before the operative level is constructed, for the lines an addition
    appends to the block of its id (`explicit.check_addition`), and its
    operative lines are then checked as an explicit solution, each refusal
    at the position of the line at fault (`explicit.check_explicit`); a
    builder whose method is `!egm` or `!time_iteration` and whose operative
    lines are a complete formula-only block is refused under
    `explicit-solution`, naming `!explicit` (AMD-MT-003 build contract
    §5)."""
    files = _files(term, spans)
    rows = _appended_rows(term, files)
    fields = stage_fields(*_declared_tree(term, spans, files, rows))
    fields["bindings"] = dataclasses.replace(
        fields["bindings"], families=bound_families(fields["definitions"])
    )
    methods = _builder_methods(fields["definitions"])
    if not rows:
        if methods:
            declared = cls(**fields)
            for block, word in methods.items():
                if word == "explicit":
                    check_addition(declared, block, ())
            _check_solutions(declared, methods, spans)
        return fields
    declared = cls(**fields)
    for block, word in methods.items():
        if word == "explicit":
            check_addition(declared, block, _rows_of(term, files, block, rows))
    operative = _operative_tree(term, spans, files, rows)
    reading = cls(**stage_fields(*operative, replaced=rows))
    _check_solutions(reading, methods, operative[1])
    table = construction_table(reading)
    blocks = MappingProxyType(
        {block: _bound(declared, reading, table, block, word) for block, word in rows.items()}
    )
    fields["definitions"] = operative_definitions(declared, tuple(blocks.values()))
    fields["bindings"] = dataclasses.replace(fields["bindings"], blocks=blocks)
    return fields


# the solution methods whose lines iterate on a value input, under which a
# block of explicit formulas alone is the block of `!explicit`
_ITERATIVE = ("egm", "time-iteration")


def _builder_methods(definitions):
    """The builders whose method component is `!explicit`, `!egm` or
    `!time_iteration`, each with the word written there, by the typing
    entries among `definitions`, in table order."""
    return {
        str(record.identity.address): record.equations[0].name
        for record in definitions.values()
        if record.kind == "typing"
        and record.identity.field == "method"
        and isinstance(record.equations[0], T.Word)
        and record.equations[0].name.replace("_", "-") in ("explicit", *_ITERATIVE)
        and "." not in str(record.identity.address)
    }


def _check_solutions(reading, methods, spans):
    """The checks of the builders `methods` names on `reading`, the stage at
    its operative level, whose span table is `spans`: an explicit solution
    for `!explicit`, and for `!egm` and `!time_iteration` the refusal of a
    complete formula-only block, which is the block of `!explicit`."""
    for block, word in methods.items():
        if word == "explicit":
            check_explicit(reading, block, spans)
        elif formula_only(reading, block):
            _refuse_formula_only(reading, block, word)


def _rows_of(term, files, block, rows):
    """The rows an addition appends to the top-level block `block` of the
    tree, in their order; empty where the block is not among `rows`, the
    blocks whose own method component holds a solution method and to which
    an addition appends a row."""
    if block not in rows:
        return ()
    held = next(
        item for address, item in item_addresses(term)
        if address == block and isinstance(item, T.Block)
    )
    return tuple(line for line in held.body if _is_row(line) and _appended(line, files))


def _refuse_formula_only(stage, block, word):
    """The refusal of a builder under `!egm` or `!time_iteration` whose
    operative lines define every output by an explicit expression and read
    no value input: such lines are an explicit solution, which `!explicit`
    types, and the method named iterates on nothing."""
    refuse_at_entry(
        stage,
        block,
        method_entry(stage, block),
        "explicit-solution",
        f"the block of the builder under !{word} defines every output by an explicit "
        f"expression of its states and parameters and reads no value input, so it states an "
        f"explicit solution, on which !{word} has nothing to iterate; type !explicit on the "
        f"builder for such a block, or write the lines !{word} solves, which read the "
        "continuation value or its derivative",
        write=f"Type `{block}.method : !explicit` in place of `{block}.method : !{word}`",
        kind="builder",
    )


def _files(term, spans):
    """The file each item of the tree was written in, by the item, and under
    the key `None` the stage file's, the file of the `@stage` line; empty for
    a tree with no span table."""
    if spans is None:
        return {}
    files = {}
    for address, item in item_addresses(term):
        span = spans.get(address)
        if span is not None:
            files[id(item)] = span.file
            if isinstance(item, T.Metadata) and item.key == "stage":
                files[None] = span.file
    return files


def _appended(line, files):
    """Whether a line of a block's body was written in a file other than the
    stage file's."""
    return bool(files) and files.get(id(line), files.get(None)) != files.get(None)


def _is_row(line):
    """Whether a line of a body may be a solution method's row: a statement
    that is no derivative line."""
    return isinstance(line, T.Statement) and stated_derivative(line.core) is None


def _appended_rows(term, files):
    """The top-level blocks whose method component holds a solution method
    and to which an addition appends at least one row, each with the
    method's word: the blocks read at two levels."""
    rows = {}
    for address, item in item_addresses(term):
        if not isinstance(item, T.Block) or "." in address:
            continue
        word = _solution_word(item, address)
        if word is not None and any(
            _is_row(line) and _appended(line, files) for line in item.body
        ):
            rows[address] = word
    return rows


def _solution_word(block, address):
    """The word of the block's own method component where it names a
    solution method: the entry `<id>.method : !word` or `method : !word` of
    the block's header."""
    for entry in block.tag.entries:
        if not isinstance(entry, T.Typer) or not isinstance(entry.typing, T.Declaration):
            continue
        subject = entry.typing.subject
        if not isinstance(subject, T.Path) or any(s.selectors for s in subject.segments):
            continue
        if tuple(s.name for s in subject.segments) not in (("method",), (address, "method")):
            continue
        classifier = entry.typing.classifiers[0]
        if isinstance(classifier, T.Method) and is_solution_method(classifier.m.name):
            return classifier.m.name
    return None


def _declared_tree(term, spans, files, rows):
    """The tree and its span table with the appended rows of each block of
    `rows` removed: the declared level."""
    if not rows:
        return term, spans
    return _rebuilt(term, spans, lambda address, line: not (
        address in rows and _is_row(line) and _appended(line, files)
    ))


def _operative_tree(term, spans, files, rows):
    """The tree and its span table with the stage file's rows of each block
    of `rows` removed, so that the appended rows stand in their place: the
    operative level. A line marked `!doc` documents the declared
    construction and stands at the declared level alone."""
    return _rebuilt(term, spans, lambda address, line: not (
        address in rows and _is_row(line) and not _appended(line, files)
    ))


def _rebuilt(term, spans, keep):
    """The tree with each statement of a top-level block for which
    `keep(block address, statement)` is false removed, and its span table
    at the kept items' addresses, each item's span found again by the item
    itself, since the position of an unnamed line in its block changes with
    the lines before it; the keys that are no item's address, the sides and
    the fields of the headers and the typing entries of the headers, keyed
    by the block and the text as written, stay as they are."""
    by_item = {id(item): spans.get(address) for address, item in item_addresses(term)}
    addresses = {id(item): address for address, item in item_addresses(term)}
    items = []
    for item in term.items:
        if isinstance(item, T.Block):
            address = addresses[id(item)]
            body = tuple(
                line for line in item.body
                if not isinstance(line, T.Statement) or keep(address, line)
            )
            rebuilt_block = dataclasses.replace(item, body=body)
            by_item[id(rebuilt_block)] = by_item.get(id(item))
            item = rebuilt_block
        items.append(item)
    rebuilt = dataclasses.replace(term, items=tuple(items))
    table = {}
    for address, item in item_addresses(rebuilt):
        span = by_item.get(id(item))
        if span is not None:
            table[address] = span
    was_item = set(addresses.values())
    for key, span in spans.items():
        if key not in was_item:
            table.setdefault(key, span)
    return rebuilt, MappingProxyType(table)


def _bound(declared, reading, table, builder, word):
    """The `BoundBlock` of one builder opened by a solution method's rows:
    the rows of the builder in the operative reading, the definitions the
    reading adds for it or rewrites, the obligations of its rows, and the
    addresses of its declared lines."""
    held, read = declared_definitions(declared), stored(reading, "definitions")
    added = tuple(
        record
        for identity, record in read.items()
        if identity not in held and _of_builder(record, builder)
    )
    rewritten = tuple(
        record
        for identity, record in read.items()
        if identity in held and record != held[identity] and _of_builder(record, builder)
    )
    declared_obligations = declared_table(declared).obligations
    row = row_of(word)
    return BoundBlock(
        builder=builder,
        method=word,
        condition=row.condition if row is not None else None,
        rows=table.by_builder(builder),
        sub_builder_rows=dict(table.sub_builder_rows).get(builder, ()),
        definitions=added + rewritten,
        replaced=tuple(held[record.identity] for record in rewritten),
        obligations=tuple(
            item
            for item in table.obligations
            if item not in declared_obligations and _owner_block(item) in (builder, None)
        ),
        declared_lines=tuple(
            record.address
            for record in held.values()
            if record.kind == "line"
            and record.address.split(".", 1)[0] == builder
            and "!doc" not in (record.tags or ())
        ),
    )


def _of_builder(record, builder):
    """Whether a record of the definitions table belongs to the builder: its
    value aggregator, its law of motion or one of its lines."""
    return record.kind != "typing" and (
        record.address == builder or str(record.address).startswith(builder + ".")
    )


def _owner_block(item):
    """The block an obligation of the construction table belongs to: the
    block of its first identity, or None."""
    first = item[1][0] if len(item) > 1 and item[1] else None
    return first.block if isinstance(first, Identity) else None


def operative_definitions(stage, blocks):
    """The definitions table of `stage` with the bound blocks `blocks`: the
    declared table with each block's records written into it, a record
    replacing the declared one of its identity in place."""
    table = dict(declared_definitions(stage))
    for block in blocks:
        for record in block.definitions:
            table[record.identity] = record
    return MappingProxyType(table)


# --- the additions a methods source names ---


def read_addition(source):
    """One addition as `(text, origin)`: the path of a `.bl` file, whose text
    is read and whose origin is the path as written, or a mapping `{"text":
    …, "origin": …}` holding the text of an addition, as a source record
    carries it. A path that names no `.bl` file, or a file that cannot be
    read as UTF-8 text, is refused under `readable-form`, and any other
    source with a TypeError. The one reader of an addition: the verbs, the
    stage loader, the trellis file and the recipe read through it."""
    if isinstance(source, (str, Path)):
        if Path(source).suffix != ".bl":
            raise ConstructionError(
                f"the addition {source} is no `.bl` file; an addition is a `.bl` file of typing "
                f"entries and lines, read by its path or as a mapping holding its text and its "
                f"origin",
                file=str(source),
                rule="readable-form",
            )
        try:
            return Path(source).read_text(encoding="utf-8"), str(source)
        except OSError as error:
            raise ConstructionError(
                f"the addition {source} cannot be read: {error.strerror}; an addition is read by "
                f"its path, or as a mapping holding its text and its origin",
                file=str(source),
                rule="readable-form",
            ) from None
        except UnicodeDecodeError:
            raise ConstructionError(
                f"the addition {source} is not UTF-8 text; an addition is a `.bl` file saved as "
                f"UTF-8 text",
                file=str(source),
                rule="readable-form",
            ) from None
    if (
        isinstance(source, Mapping)
        and set(source) == {"text", "origin"}
        and all(isinstance(source[key], str) for key in ("text", "origin"))
    ):
        return source["text"], source["origin"]
    raise TypeError(
        "an addition is the path of a `.bl` file or a mapping {text, origin} holding its text; "
        f"got {type(source).__name__}"
    )


def load_additions(source):
    """The additions a methods source names, each as `(text, origin)`, in
    order: none for an empty source (None, an empty mapping or an empty
    sequence), one for a path or a `{text, origin}` mapping
    (`read_addition`), and each of a list or tuple of them, the form a
    source record holds under `methods`."""
    if source is None or (isinstance(source, (Mapping, list, tuple)) and not source):
        return ()
    if isinstance(source, (list, tuple)):
        return tuple(read_addition(held) for held in source)
    return (read_addition(source),)


def methods_source(source):
    """The mapping a methods source is described and digested by
    (`provenance.source_description`): the empty mapping where the source
    names no addition, so that a stage elaborated from its file alone
    describes its methods as every empty source is described, and
    otherwise `{"additions": [{"path": origin, "text": text}, ...]}`, the
    additions the source names with their texts, so that two sources naming
    the same files with the same texts have one digest."""
    read = load_additions(source)
    if not read:
        return {}
    return {"additions": [{"path": origin, "text": text} for text, origin in read]}


def methods_location(read):
    """Where a methods source stands, for its description: the path of the
    one addition `read` holds, the origins of several joined by commas under
    `origin`, and None where it holds none, which the description names
    `in-memory`."""
    if not read:
        return None
    if len(read) == 1:
        return {"path": read[0][1]}
    return {"origin": ", ".join(origin for _, origin in read)}


def addition_records(read):
    """The record of each addition of `read`, `(text, origin)` pairs, as the
    provenance of a version holds them under `additions`: its path, the
    SHA-256 digest of its text and the text, from which the union of the
    files is made again."""
    return tuple(
        {"path": origin, "sha256": sha256(text.encode("utf-8")).hexdigest(), "text": text}
        for text, origin in read
    )


def supplies_addition(source):
    """Whether a methods source names at least one addition, so that a
    record's methods are bound (`bind_stage`); an empty source binds
    nothing."""
    return bool(load_additions(source))


def holds_additions(stage):
    """Whether additions have been read into the stage, with its text at its
    construction or by `methodize`, which its provenance records under
    `additions`."""
    return bool(stage.provenance.get("additions"))


def source_texts(stage):
    """The stage file's text with its origin and each addition's text with
    its origin, as the provenance records them, from which the parsed union
    of the files is made again."""
    text = stage.provenance.get("text")
    origin = stage.provenance.get("path") or stage.provenance.get("origin")
    additions = tuple(
        (held["text"], held["path"]) for held in stage.provenance.get("additions", ())
    )
    return text, origin, additions


# --- the declared version ---


def declared_version(stage):
    """The stage as its stage file declares it and elaboration builds it:
    for a stage into which additions have been read, the stage file's own
    text elaborated alone, with no binding (specification 0.7 §4 rule 6, the
    erasure; the implementation specification §U2); otherwise `stage` itself
    while it holds no binding, and otherwise a version holding the same
    initial diagrams and stored builders graphs, the declared definitions
    table and the typing entries the stage file writes, with no block,
    calibration or settings, kept for the version (specification 0.6 §7).
    `stage.declared` reads it: its cards print no binding, no method clause
    and no condition of a method (`is_declared_version`), and the cards of
    the blocks and the lines of the initial diagrams read it, so that no
    binding changes them (decisions SC-13 and SC-22); a typing entry the
    stage file itself writes is no binding, and `methods` at the declared
    level answers it (decision SC-24)."""
    if holds_additions(stage):
        return kept_answer(stage, "declared version", lambda: _declared_alone(stage))
    bindings = stored(stage, "bindings")
    if all(getattr(bindings, name) is None for name in _BINDING_NAMES):
        return stage
    return kept_answer(stage, "declared version", lambda: _declared(stage))


def is_declared_version(stage):
    """Whether `stage` is the version `declared_version` makes of a stage
    that holds a binding, whose provenance records the level `declared` and
    whose cards print no binding."""
    return stage.provenance.get("level") == _DECLARED


# the three mappings a stage's bindings hold, and the level a declared
# version's provenance records
_BINDING_NAMES = ("calibration", "settings", "blocks")
_DECLARED = "declared"


def _declared_alone(stage):
    """The stage file of `stage` elaborated alone, the declared level of a
    stage into which additions have been read, under the stage's provenance
    without the additions and marked as the declared level, so that the
    declared version of a declared version is itself."""
    text, origin, _ = source_texts(stage)
    term, spans = parse_with_spans(text, origin)
    alone = type(stage)(**construct(type(stage), term, spans))
    provenance = {key: value for key, value in stage.provenance.items() if key != "additions"}
    return replace_stage(alone, provenance=freeze({**provenance, "level": _DECLARED}))


def _declared(stage):
    bindings = stored(stage, "bindings")
    return replace_stage(
        stage,
        definitions=declared_definitions(stage),
        bindings=dataclasses.replace(bindings, calibration=None, settings=None, blocks=None),
        provenance=freeze({**stage.provenance, "level": _DECLARED}),
    )
