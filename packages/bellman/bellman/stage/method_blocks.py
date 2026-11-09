"""The method blocks and the marginal blocks of a stage (specification 0.6
§§4, 4.1, 5, 7).

A methods entry that names a block file under `block:` opens the builder its
`on:` names: the file, written in the stage file's syntax, holds definitions
and blocks, and the block that joins the builder's perches and writes its
outputs computes the builder's output. An entry with `!marginals` adds the
lines of a marginal block, the block that joins a value builder's perches and
writes marginal values alone, to that builder's own lines. `block_source`
reads a file; `read_blocks` checks each block's header against its builder
(`block-header-mismatch`) and the functions its lines call
(`block-name-undefined`), and elaborates every block a binding holds in one
term: the stage file's term, each method block in place of its builder's block
under the builder's name, each marginal block's lines after its builder's
lines and its added fields on its builder's header, and the block files'
definitions after the stage file's items, read by `construction.stage_fields`,
the one elaboration of a stage file, into a stage of the stage's own class.
Nothing is differentiated: a marginal row is the fold of a line the author
wrote. The answer for each block is a `BoundBlock`, which the bindings hold
under its builder: the rows of the builder, the definitions they read, the
sorts of the fields the header adds, the obligations of its rows and the
positions of its lines in its own file; a marginal block whose lines read a
marginal value nothing supplies holds the builder's declared rows and names
the value.

The stage holds one definitions table and one construction table for each of
two levels (specification 0.6 §1): `declared_definitions` and the declared
construction table are those the stage file states, and the operative ones
add what each bound block adds. `declared_version` is the stage as its stage
file declares it, holding the same initial diagrams and the same stored
builders graphs, which `stage.declared` reads. For a stage written as a
stage file and its additions (specification 0.7 §4), `operative_level` reads
the union of the files at the operative level: in a block whose method
component is typed by a solution method and whose additions bring rows, the
stage file's lines are left out, and `declared_version` is the stage file
elaborated alone.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple

from bellman.fold.block_lines import blocks_in_file_order, header_of, header_wire_sorts
from bellman.fold.wire_terms import stated_derivative, term_nodes
from bellman.native.frozen import freeze
from bellman.native.identity import Identity
from bellman.native.records import BoundBlock
from bellman.native.versions import kept_answer, replace_stage, stored
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage.construction import stage_fields
from bellman.stage.grains import (
    construction_table,
    declared_definitions,
    declared_table,
)
from bellman.syntax import terms as T
from bellman.syntax.lower import ParsedFile, item_addresses, parse_with_spans
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    ARRIVAL,
    CONTINUATION,
    CONTROL,
    DECISION,
    VALUE,
)
from bellman.typing.line_unknowns import CALL_OPERATORS, role_word
from bellman.typing.primitive_definitions import primitive_definition

__all__ = (
    "block_source",
    "declared_definitions",
    "declared_version",
    "held_source",
    "is_declared_version",
    "operative_level",
    "read_blocks",
)


# --- the reading of a block file ---


def block_source(method, builder, base, condition=None, *, marginal=False):
    """The block file `method.block` names for the builder `builder`, read
    from its folder: `base` is the folder of the methods file, against which
    the path is read, or None for a methods source given as a mapping, whose
    paths are read as written; `condition` is the name of the condition the
    method's row of the method table requires; `marginal` says whether its
    block is a marginal block, bound by `!marginals`, whose lines are added
    to the builder's own (specification 0.6 §5.1). Refused under
    `readable-file` where the file cannot be read."""
    written = method.block
    path = Path(written) if base is None else Path(base) / written
    text = _block_text(path, written, builder)
    return BlockSource(written, str(path), text, method.tag, condition, marginal)


def held_source(block):
    """The block file of a bound block, from the text the block holds."""
    return BlockSource(
        block.path, block.origin, block.text, block.tag, block.condition, block.marginal
    )


class BlockSource(NamedTuple):
    """A block file as a methods entry names it: the path as written, the
    path as read, its text, the method's tag, the condition its row
    requires, and whether its block is a marginal block."""

    written: str
    origin: str
    text: str
    tag: str
    condition: str | None
    marginal: bool


class _Placement(NamedTuple):
    """One block of a block file as it stands in the term the blocks are
    read in: the builder it opens or adds lines to, the block, its id, the
    block file's term and span table, the path as read, and whether it is a
    marginal block, whose lines are added to the builder's own."""

    builder: str
    block: object
    block_id: str
    term: object
    spans: Mapping
    origin: str
    marginal: bool


def read_blocks(stage, sources):
    """The `BoundBlock` of each block file of `sources`, pairs of a builder
    and its `BlockSource` in the order bound, read together: the blocks
    stand in one term, each method block in place of its builder's block and
    each marginal block's lines after its builder's own, so that a marginal
    value one block writes or declares is in scope for another, and the term
    is elaborated once (specification 0.6 §§4.1, 5.1). Refused where a file
    holds no block whose header matches its builder's
    (`block-header-mismatch`), where a line calls a function neither the
    stage file nor the block file defines (`block-name-undefined`), and as a
    stage file is refused where the lines break a rule of construction. A
    marginal block whose lines read a marginal value that the stage and the
    other blocks neither receive nor write is bound without its lines: its
    builder keeps its declared rows until a block or a declared line writes
    the value, and the block names the value (`BoundBlock.missing`)."""
    stage_text, stage_origin = _stage_text(stage)
    stage_term, stage_spans = parse_with_spans(stage_text, stage_origin)
    parsed = {}
    for builder, source in sources:
        block_term, block_spans = parse_with_spans(source.text, source.origin)
        declared = _block_named(stage, stage_term, builder)
        matching = _matching_marginal_block if source.marginal else _matching_block
        chosen = matching(stage, block_term, declared, builder, source.written)
        parsed[builder] = (source, block_term, block_spans, declared, chosen, _block_id(chosen))
    for builder, (source, block_term, block_spans, declared, chosen, chosen_id) in parsed.items():
        declared_part = (declared, stage_text, stage_spans)
        block_part = (chosen, chosen_id, source.text, block_spans)
        if not source.marginal:
            _check_header(stage, builder, declared_part, block_part, source.written)
            continue
        supplied = {
            place
            for other, (_, _, _, _, block, _) in parsed.items()
            if other != builder
            for place in _header_fields(stage, block)
        }
        _check_marginal_header(stage, builder, declared_part, block_part, source.written, supplied)
    for source, block_term, _, _, chosen, chosen_id in parsed.values():
        definitions = [
            item for item in block_term.items if not isinstance(item, (T.Metadata, T.Block))
        ]
        _check_names(stage, chosen, chosen_id, definitions, source.written)
    placements = [
        _Placement(
            builder, chosen, chosen_id, block_term, block_spans, source.origin, source.marginal
        )
        for builder, (source, block_term, block_spans, _, chosen, chosen_id) in parsed.items()
    ]
    term, spans, positions = _combined(stage_term, stage_spans, placements)
    # the stage of the term, of the stage's own class
    reading = type(stage)(**stage_fields(term, spans))
    table = construction_table(reading)
    return {
        builder: _bound(stage, reading, table, (builder, source, chosen_id), spans, positions, parsed)
        for builder, (source, _, _, _, _, chosen_id) in parsed.items()
    }


def _header_fields(stage, block):
    """The controls and the marginal values a block's header writes, or
    declares with a set and a role among its inputs, as pairs of a name and
    a perch: what the block supplies to the marginal blocks of the term it
    is read in. A field's role is the one its header writes, or else the one
    the stage file declares for it."""
    signature = _signature(block)
    listed = [*signature.target.coordinates] + [
        coordinate
        for coordinate in signature.source.coordinates
        if _declares_set_and_role(coordinate)
    ]
    sorts = header_wire_sorts(stage)
    found = set()
    for coordinate in listed:
        place = (coordinate.stem, _PERCH_OF_MARK[_coordinate_key(coordinate)[1]])
        role = next(
            (role_word(c.kind) for c in coordinate.classifiers if isinstance(c, T.Role)), None
        )
        if role is None:
            held = sorts.get(Identity("field", stage=stage.name, perch=place[1], field=place[0]))
            role = held.role if held is not None else None
        if role in _SUPPLIED_ROLES:
            found.add(place)
    return found


# the roles of the fields a marginal block may read from the stage's headers
# and the other blocks of its reading, beside the inputs of its builder: a
# control, at which its lines are read (decision SC-21; AMD-MB-001 R2
# retires the marginal roles)
_SUPPLIED_ROLES = (CONTROL,)


def _bound(stage, reading, table, named, spans, positions, parsed):
    """The `BoundBlock` of one block of a reading: the rows of its builder,
    the definitions its builder and its file add or rewrite, the sorts of
    the fields its builder's header adds to the stage's, the obligations of
    its builder's rows, and the positions of its lines and its file's
    definitions in the block file."""
    builder, source, chosen_id = named
    held, read = declared_definitions(stage), stored(reading, "definitions")
    own = positions.get(source.origin, frozenset())
    added = [
        record
        for identity, record in read.items()
        if identity not in held
        and (_of_builder(record, builder) or _written_in(record, source.origin))
    ]
    rewritten = [
        record
        for identity, record in read.items()
        if identity in held and record != held[identity] and _of_builder(record, builder)
    ]
    ports = header_wire_sorts(stage)
    header = next(box for box in blocks_in_file_order(reading) if box.name == builder)
    listed = {
        sort.identity: sort for sort in (*header_of(header).inputs, *header_of(header).outputs)
    }
    declared_obligations = declared_table(stage).obligations
    elsewhere = set(parsed) - {builder}
    return BoundBlock(
        path=source.written,
        origin=source.origin,
        text=source.text,
        block=chosen_id,
        builder=builder,
        tag=source.tag,
        condition=source.condition,
        rows=table.by_builder(builder),
        sub_builder_rows=dict(table.sub_builder_rows).get(builder, ()),
        definitions=tuple(added + rewritten),
        replaced=tuple(held[record.identity] for record in rewritten),
        ports=tuple(sort for identity, sort in listed.items() if identity not in ports),
        obligations=tuple(
            item
            for item in table.obligations
            if item not in declared_obligations and _owner_block(item) not in elsewhere
        ),
        # the places in the block file alone: a marginal block's builder keeps
        # its own lines, whose places the stage file's span table holds, so
        # that the record does not depend on how the stage file's path is
        # spelled (decision SD-58)
        spans=MappingProxyType(
            {
                key: span
                for key, span in spans.items()
                if (_under(key, builder) or key in own) and span.file == source.origin
            }
        ),
        declared_lines=()
        if source.marginal
        else tuple(
            record.address
            for record in held.values()
            if record.kind == "line"
            and record.address.split(".", 1)[0] == builder
            and "!doc" not in (record.tags or ())
        ),
        marginal=source.marginal,
    )


def _written_in(record, origin):
    """Whether a record of the definitions table is a definition the block
    file at `origin` writes: its address is the file and the line it was
    written at, `methods/cons_egm.bl:2`."""
    file, _, line = str(record.address).rpartition(":")
    return bool(file) and line.isdigit() and Path(file).resolve() == Path(origin).resolve()


def _owner_block(item):
    """The block an obligation of the construction table belongs to: the
    block of its first identity, or None."""
    first = item[1][0] if len(item) > 1 and item[1] else None
    return first.block if isinstance(first, Identity) else None


def _block_text(path, written, builder):
    """The text of the block file at `path`, refused under `readable-file`
    where it cannot be read."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise FactoryError(
            f"the block file {written} cannot be read at {path}: {error.strerror}",
            rule="readable-file",
            file=str(path),
            address=builder,
            written=written,
            write="the path of a block file that exists, relative to the methods file",
        ) from None


def _stage_text(stage):
    """The stage file's text and origin, as the provenance holds them; a
    stage built from a term whose text the provenance does not hold has no
    declarations to read a block with."""
    text = stage.provenance.get("text")
    if not text:
        raise ValueError(
            f"stage {stage.name!r}: its provenance holds no stage text, and a method block is "
            "read with the stage file's declarations in scope (specification 0.6 §4.1); "
            "elaborate the stage from its file with elaborate_stage(load_stage(path))"
        )
    return text, stage.provenance.get("path") or stage.provenance.get("origin")


def _block_id(block):
    """The id a block's header writes, `egm` of `[id=egm, …]`."""
    return next(
        entry.value
        for entry in block.tag.entries
        if isinstance(entry, T.KeyValue) and entry.key == "id"
    )


def _signature(block):
    """The signature a block's header writes: its two sides and their
    perches."""
    return next(entry.typing for entry in block.tag.entries if isinstance(entry, T.Typer))


def _block_named(stage, term, builder):
    """The block of the stage file whose id is the builder's name."""
    for item in term.items:
        if isinstance(item, T.Block) and _block_id(item) == builder:
            return item
    raise ValueError(
        f"stage {stage.name!r}: the stage file writes no block {builder!r}; a method block "
        "opens a builder the stage file's blocks denote"
    )


def _coordinate_key(coordinate):
    """A field listed on a side of a header, by its name and its mark: `V[>]`
    as `("V", "Continuation")`, an unmarked `c` as `("c", None)`."""
    return (coordinate.stem, type(coordinate.at.side).__name__ if coordinate.at else None)


def _declares_set_and_role(coordinate):
    """Whether a header lists a field with a set and a role,
    `dV[>] : ℝ₊₊ @ !mrgnvl`."""
    kinds = {type(classifier) for classifier in coordinate.classifiers}
    return T.Domain in kinds and T.Role in kinds


def _outputs(signature):
    return sorted(map(_coordinate_key, signature.target.coordinates))


def _matching_block(stage, block_term, declared, builder, written):
    """The block of the block file that the methods entry opens the builder
    with: the one that joins the builder's perches and writes its outputs. A
    block that joins the perches and writes other outputs, or any block where
    none joins them, is given to the header check, which refuses it with the
    two signatures; a file that holds no block, or two blocks that each match,
    is refused here."""
    signature = _signature(declared)
    blocks = [item for item in block_term.items if isinstance(item, T.Block)]
    joining = [
        block
        for block in blocks
        if _signature(block).source_types == signature.source_types
        and _signature(block).target_types == signature.target_types
    ]
    writing = [block for block in joining if _outputs(_signature(block)) == _outputs(signature)]
    if len(writing) > 1:
        raise ConstructionError(
            f"stage {stage.name!r}: the blocks {', '.join(repr(_block_id(b)) for b in writing)} "
            f"of {written} each join the perches of the builder {builder!r} and write its "
            "outputs, and a methods entry opens a builder with one block (specification 0.6 "
            "§4); write one such block in the file",
            rule="block-header-mismatch",
            stage=stage.name,
            file=written,
            address=_block_id(writing[1]),
        )
    if writing:
        return writing[0]
    if joining or blocks:
        return (joining or blocks)[0]
    raise ConstructionError(
        f"stage {stage.name!r}: {written} holds no block, and a methods entry with `block:` "
        f"opens the builder {builder!r} with a block of that file (specification 0.6 §4); "
        "write the block in the file",
        rule="block-header-mismatch",
        stage=stage.name,
        file=written,
        address=builder,
    )


def _check_header(stage, builder, declared_part, block_part, written):
    """The refusal of a block whose header does not match the builder it
    opens (specification 0.6 §4.1; AMD-MB-001 §5.1): the block joins the
    builder's perches, writes the builder's outputs, and reads inputs that
    are among the builder's inputs, there being no extended signature; a
    derivative of a value it lists is read as a term of its lines. The
    refusal quotes the two signatures as their files write them."""
    declared, stage_text, stage_spans = declared_part
    chosen, chosen_id, text, block_spans = block_part
    signature, own = _signature(declared), _signature(chosen)
    inputs = {_coordinate_key(coordinate) for coordinate in signature.source.coordinates}
    reasons = _declaration_reasons(stage, own, inputs)
    if (
        own.source_types == signature.source_types
        and own.target_types == signature.target_types
        and _outputs(own) == _outputs(signature)
        and all(_coordinate_key(coordinate) in inputs for coordinate in own.source.coordinates)
        and not reasons
    ):
        return
    raise ConstructionError(
        f"stage {stage.name!r}: the block {chosen_id!r} of {written} has the signature "
        f"{_header(text, block_spans, chosen_id)}, and the builder {builder!r} it opens has the "
        f"signature {_header(stage_text, stage_spans, builder)}; "
        + "".join(reason + "; " for reason in reasons)
        + "a method block joins the "
        "builder's perches, writes the builder's outputs, and reads the builder's inputs and "
        "no other field; a derivative of a value it lists is written as a term of its lines, "
        "`D_{a}V[>]` (specification 0.6 §4.1; AMD-MB-001 §5.1); write the builder's outputs "
        "on the block's output side and its inputs on the input side",
        rule="block-header-mismatch",
        stage=stage.name,
        file=written,
        address=chosen_id,
    )


def _declaration_reasons(stage, signature, inputs):
    """Why a block's header disagrees with the stage file, one sentence each:
    a field the stage file declares that the header gives another set or
    another role, and an input the builder does not have, declared with a
    set and a role (decision SA-15; AMD-MB-001 §5.1, no extended signature).
    `inputs` are the builder's inputs by name and mark."""
    sorts = header_wire_sorts(stage)
    reasons = []
    for coordinate in (*signature.source.coordinates, *signature.target.coordinates):
        key = _coordinate_key(coordinate)
        domain = next((c.space for c in coordinate.classifiers if isinstance(c, T.Domain)), None)
        role = next(
            (role_word(c.kind) for c in coordinate.classifiers if isinstance(c, T.Role)), None
        )
        identity = Identity("field", stage=stage.name, perch=_PERCH_OF_MARK[key[1]], field=key[0])
        held, field = sorts.get(identity), f"`{_written_field(coordinate)}`"
        if held is not None and domain is not None and domain != held.domain:
            reasons.append(
                f"the header declares {field} in {to_source(domain)}, and the stage file "
                f"declares it in {to_source(held.domain)}"
            )
        if held is not None and role is not None and role != held.role:
            reasons.append(
                f"the header declares {field} as a {role}, and the stage file as a {held.role}"
            )
        if (
            coordinate in signature.source.coordinates
            and held is None
            and key not in inputs
            and role is not None
        ):
            reasons.append(
                f"{field} is an input the builder does not have and is declared as a {role}; "
                "a block's inputs are among the builder's own, and a derivative of a value it "
                "lists is a term of its lines"
            )
    return reasons


def _states_derivatives(block):
    """Whether every line of a block is a derivative line, `D_{m_d}V =
    𝑑𝑢(c)`, which makes the block a marginal block (AMD-MB-001 §3)."""
    return bool(block.body) and all(
        stated_derivative(statement.core) is not None for statement in block.body
    )


def _joins(block, signature):
    """Whether a block joins the perches a builder's signature joins."""
    own = _signature(block)
    return (
        own.source_types == signature.source_types and own.target_types == signature.target_types
    )


def _matching_marginal_block(stage, block_term, declared, builder, written):
    """The marginal block of the block file that a `!marginals` entry adds to
    the builder: the one that joins the builder's perches and whose lines
    are derivative lines of the value the builder writes (AMD-MB-001 §3).
    Any other block, where none does, is given to the header check, which
    refuses it with the two signatures; a file that holds no block, or two
    blocks that each match, is refused here."""
    signature = _signature(declared)
    blocks = [item for item in block_term.items if isinstance(item, T.Block)]
    joining = [block for block in blocks if _joins(block, signature)]
    writing = [block for block in joining if _states_derivatives(block)]
    if len(writing) > 1:
        raise ConstructionError(
            f"stage {stage.name!r}: the blocks {', '.join(repr(_block_id(b)) for b in writing)} "
            f"of {written} each join the perches of the builder {builder!r} and state "
            "derivatives of its value, and a `!marginals` entry adds one marginal block to a "
            "builder (specification 0.6 §5.1); write one such block in the file",
            rule="block-header-mismatch",
            stage=stage.name,
            file=written,
            address=_block_id(writing[1]),
        )
    if writing:
        return writing[0]
    if joining or blocks:
        return (joining or blocks)[0]
    raise ConstructionError(
        f"stage {stage.name!r}: {written} holds no block, and a `!marginals` entry adds a "
        f"marginal block of that file to the builder {builder!r} (specification 0.6 §5.1); "
        "write the block in the file",
        rule="block-header-mismatch",
        stage=stage.name,
        file=written,
        address=builder,
    )


_PERCH_OF_MARK = {None: DECISION, "Continuation": CONTINUATION, "Arrival": ARRIVAL}


def _check_marginal_header(stage, builder, declared_part, block_part, written, supplied):
    """The refusal of a marginal block whose header does not match the
    builder it adds lines to (specification 0.6 §5.1; AMD-MB-001 §3): the
    block joins the builder's perches; its header is the builder's own
    restricted to what its lines read, so each output is an output of the
    builder, written by name, `(V)`, and each input is an input of the
    builder, or a control at which the builder's lines are read, declared by
    the stage's headers or by another block of the reading (`supplied`), as
    pairs of a name and a perch; every line is a derivative line of the
    value. No field beside these, there being no extended signature. The
    refusal quotes the two signatures as their files write them."""
    declared, stage_text, stage_spans = declared_part
    chosen, chosen_id, text, block_spans = block_part
    signature, own = _signature(declared), _signature(chosen)
    inputs = {_coordinate_key(coordinate) for coordinate in signature.source.coordinates}
    outputs = {_coordinate_key(coordinate) for coordinate in signature.target.coordinates}
    supplied = set(supplied) | {
        (identity.field, identity.perch)
        for identity, sort in header_wire_sorts(stage).items()
        if sort.role in _SUPPLIED_ROLES
    }
    reasons = _declaration_reasons(stage, own, inputs)
    matched = _joins(chosen, signature) and _states_derivatives(chosen) and not reasons
    matched = matched and all(_coordinate_key(c) in outputs for c in own.target.coordinates)
    for coordinate in own.source.coordinates:
        key = _coordinate_key(coordinate)
        place = (coordinate.stem, _PERCH_OF_MARK[key[1]])
        if key in inputs or place in supplied:
            continue
        matched = False
    if matched:
        return ()
    raise ConstructionError(
        f"stage {stage.name!r}: the marginal block {chosen_id!r} of {written} has the signature "
        f"{_header(text, block_spans, chosen_id)}, and the builder {builder!r} it adds lines to "
        f"has the signature {_header(stage_text, stage_spans, builder)}; "
        + "".join(reason + "; " for reason in reasons)
        + "a marginal block joins the builder's perches, writes the builder's value by name, "
        "`(V)`, reads the builder's inputs or the controls at which its lines are read, and "
        "no other field, and every line of it is a derivative line of the value, "
        "`D_{m_d}V = 𝑑𝑢(c)` (specification 0.6 §5.1; AMD-MB-001 §3); write the block between "
        "the builder's perches with that header",
        rule="block-header-mismatch",
        stage=stage.name,
        file=written,
        address=chosen_id,
    )


def _header(text, spans, block_id):
    """The two sides of a block's header as its file writes them,
    `(V[>]) : !cntn -> (c) : !dcsn`."""
    return (
        f"{_written(text, spans[block_id + '.in'])} -> {_written(text, spans[block_id + '.out'])}"
    )


def _written(text, span):
    """The text a span covers in `text`."""
    lines = text.splitlines(keepends=True)[span.line - 1 : span.end_line]
    if len(lines) == 1:
        return lines[0][span.column - 1 : span.end_column - 1]
    lines[0], lines[-1] = lines[0][span.column - 1 :], lines[-1][: span.end_column - 1]
    return " ".join(line.strip() for line in lines)


def _check_names(stage, chosen, chosen_id, definitions, written):
    """The refusal of a line of the block that calls a function neither the
    stage file nor the block file defines (specification 0.6 §4.1): a name a
    line calls is a function or correspondence of the stage's definitions
    table, a name the block file defines, a primitive function of the
    language, or an operator the grammar writes as a call, `upper_env` or
    `evaluate`."""
    defined = {_defined_name(record) for record in declared_definitions(stage).values()}
    defined |= {name for item in definitions for name in _names_defined(item)}
    for position, statement in enumerate(chosen.body, 1):
        for node in term_nodes(statement.core):
            if not isinstance(node, T.Call) or not isinstance(node.fun, str):
                continue
            if node.fun in defined or primitive_definition(node.fun) is not None:
                continue
            if node.fun in CALL_OPERATORS:
                continue
            raise ConstructionError(
                f"stage {stage.name!r}: the line {_line_address(chosen_id, statement, position)} "
                f"of {written} calls {node.fun!r}, which neither the stage file nor the block "
                "file defines; a method block reads the stage's definitions and the block "
                "file's own (specification 0.6 §4.1); define "
                f"{node.fun} in the block file, or call a function the stage file defines",
                rule="block-name-undefined",
                stage=stage.name,
                file=written,
                address=_line_address(chosen_id, statement, position),
            )


def _defined_name(record):
    """The name a record of the definitions table defines, the last segment
    of its identity, `𝑢` of `cons:function:𝑢`."""
    return str(record.identity).rsplit(":", 1)[-1]


def _names_defined(item):
    """The names a top-level item of the block file defines: the left side of
    a definition, `𝑑𝑢` of `𝑑𝑢 := D_{c}(𝑢)`, or the name of a declared
    function, `𝑢` of `𝑢(c : ℝ₊₊) := …`, which the parser reads as a
    `FuncDef` holding its name (decision SD-24)."""
    core = getattr(item, "core", None)
    if isinstance(core, T.FuncDef) and isinstance(core.name, str):
        yield core.name
        return
    target = getattr(core, "target", None)
    for node in term_nodes(target) if target is not None else ():
        name = getattr(node, "name", None) or getattr(node, "fun", None)
        if isinstance(name, str):
            yield name


def _line_address(block_id, statement, position):
    """A line's address in its block file, `egm.InvEuler`, or its position in
    the block where the line carries no id."""
    entries = getattr(statement.annot, "entries", ()) or ()
    named = next((e.value for e in entries if isinstance(e, T.KeyValue) and e.key == "id"), None)
    return f"{block_id}.{named or position}"


def _under(key, name):
    """Whether a span table's key is the address `name` or an address in it."""
    return key == name or key.startswith(name + ".")


def _combined(stage_term, stage_spans, placements):
    """The term a block is read in and its span table: the stage file's
    items, each placed block standing at its builder's block, a method block
    in place of it under the builder's name and a marginal block's lines
    after the builder's own, with its header's added fields on the
    builder's header (`_merged`); then the definitions of each block file
    once. The positions are the stage file's for its items and the block
    file's for the blocks and their definitions. The third answer maps the
    path of each block file to the positions of its definitions in the
    term."""
    items = list(stage_term.items)
    spans = dict(stage_spans)
    positions = {}
    for placement in placements:
        index = next(
            place
            for place, item in enumerate(items)
            if isinstance(item, T.Block) and _block_id(item) == placement.builder
        )
        if placement.marginal:
            items[index], moved = _merged(items[index], placement)
        else:
            items[index] = _renamed(placement.block, placement.builder)
            spans = {
                key: span for key, span in spans.items() if not _under(key, placement.builder)
            }
            moved = {
                key: placement.builder + key[len(placement.block_id) :]
                for key in placement.spans
                if _under(key, placement.block_id)
            }
        for key, address in moved.items():
            spans[address] = placement.spans[key]
        if placement.origin in positions:
            continue
        held = positions[placement.origin] = set()
        for place, item in enumerate(placement.term.items, 1):
            if not isinstance(item, (T.Metadata, T.Block)):
                items.append(item)
                held.add(str(len(items)))
                spans[str(len(items))] = placement.spans[str(place)]
    term = dataclasses.replace(stage_term, items=tuple(items))
    return (
        term,
        MappingProxyType(spans),
        {origin: frozenset(held) for origin, held in positions.items()},
    )


def _renamed(block, builder):
    """The block under the builder's name, its id replaced."""
    return dataclasses.replace(
        block,
        tag=dataclasses.replace(
            block.tag,
            entries=tuple(
                T.KeyValue("id", builder)
                if isinstance(entry, T.KeyValue) and entry.key == "id"
                else entry
                for entry in block.tag.entries
            ),
        ),
    )


def _merged(declared, placement):
    """The builder's block with a marginal block's lines after its own and
    the fields the marginal block's header lists and the builder's does not
    on the builder's header, inputs and outputs; and the addresses its lines
    and its added fields take in the merged block, by their addresses in the
    block file. A line the block file writes without an id takes its
    position after the builder's lines."""
    signature, own = _signature(declared), _signature(placement.block)
    listed_in = {_coordinate_key(c) for c in signature.source.coordinates}
    listed_out = {_coordinate_key(c) for c in signature.target.coordinates}
    added = {
        "in": tuple(c for c in own.source.coordinates if _coordinate_key(c) not in listed_in),
        "out": tuple(c for c in own.target.coordinates if _coordinate_key(c) not in listed_out),
    }
    merged = dataclasses.replace(
        signature,
        source=dataclasses.replace(
            signature.source, coordinates=signature.source.coordinates + added["in"]
        ),
        target=dataclasses.replace(
            signature.target, coordinates=signature.target.coordinates + added["out"]
        ),
    )
    tag = dataclasses.replace(
        declared.tag,
        entries=tuple(
            T.Typer(merged) if isinstance(entry, T.Typer) else entry
            for entry in declared.tag.entries
        ),
    )
    block = dataclasses.replace(declared, tag=tag, body=declared.body + placement.block.body)
    written = {
        side: {_written_field(coordinate) for coordinate in coordinates}
        for side, coordinates in added.items()
    }
    lines, moved = len(declared.body), {}
    for key in placement.spans:
        if not key.startswith(placement.block_id + "."):
            continue
        first, _, rest = key[len(placement.block_id) + 1 :].partition(".")
        if first in written:
            if rest.split(".", 1)[0] in written[first]:
                moved[key] = f"{placement.builder}.{first}.{rest}"
            continue
        address = str(lines + int(first)) if first.isdigit() else first
        moved[key] = ".".join(filter(None, (placement.builder, address, rest)))
    return block, moved


def _written_field(coordinate):
    """A field as a span table's key names it, `dV[>]` or `dV`."""
    mark = type(coordinate.at.side).__name__ if coordinate.at else None
    return coordinate.stem + {"Continuation": "[>]", "Arrival": "[<]"}.get(mark, "")


def _of_builder(record, builder):
    """Whether a record of the definitions table belongs to the builder: its
    value aggregator or one of its lines."""
    return record.address == builder or record.address.startswith(builder + ".")


# --- the two levels of the stage ---


def operative_level(parsed, origin, solution):
    """The union of a stage file and its additions at the operative level
    (specification 0.7 §4 rule 5 as decided, D8): `parsed` is the pair of
    term and span table that `bellman.syntax.union.union` answers, `origin`
    the stage file's origin, which the spans of its items name, and
    `solution` the method words, in the spelling of a stage file, whose row
    is of the kind solution. In a top-level block whose own method component
    is typed by one of those words and whose body holds a row of another
    file, a line that is neither a nested block nor a derivative line
    (`stated_derivative`), the stage file's rows are left out at the
    operative level, since the addition's rows compute the builder's output
    in their place; the block's nested blocks and derivative lines stay.
    Every other item stays, and the span table is rebuilt at the kept items'
    addresses. A pair with no such block is answered as given."""
    term, spans = parsed
    addressed = item_addresses(term)
    left_out = set()
    for address, item in addressed:
        if "." in address or not _solution_block(item, solution):
            continue
        rows = [(key, line) for key, line in _direct(addressed, address) if _is_row(line)]
        if any(_file_of(spans, key) != origin for key, _ in rows):
            left_out.update(key for key, _ in rows if _file_of(spans, key) == origin)
    if not left_out:
        return parsed
    items = tuple(
        T.Block(
            item.tag,
            tuple(line for key, line in _direct(addressed, address) if key not in left_out),
        )
        if isinstance(item, T.Block) and any(key.startswith(address + ".") for key in left_out)
        else item
        for address, item in addressed
        if "." not in address
    )
    kept = T.FILE(items)
    renamed = {
        before: after
        for (before, _), (after, _) in zip(
            [(key, item) for key, item in addressed if key not in left_out], item_addresses(kept)
        )
    }
    table = {
        _kept_key(key, renamed): span for key, span in spans.items() if key not in left_out
    }
    return ParsedFile(kept, MappingProxyType(table))


# the subject of the typing entry of a block's own method component
_OWN_METHOD = T.Path((T.Segment("method", ()),))


def _solution_block(item, solution):
    """Whether `item` is a block whose own method component is typed by a
    word of `solution`."""
    if not isinstance(item, T.Block):
        return False
    for entry in item.tag.entries:
        typing = getattr(entry, "typing", None)
        if isinstance(typing, T.Declaration) and typing.subject == _OWN_METHOD:
            word = typing.classifiers[0] if typing.classifiers else None
            return isinstance(word, T.Method) and word.m.name in solution
    return False


def _is_row(line):
    """Whether a line of a block is a row: neither a nested block nor a
    derivative line."""
    return not isinstance(line, T.Block) and not (
        isinstance(line, T.Statement) and stated_derivative(line.core) is not None
    )


def _direct(addressed, address):
    """The addressed items of the body of the block at `address`: its lines
    and its nested blocks, in order, without the items of a nested block."""
    prefix = address + "."
    return [
        (key, item)
        for key, item in addressed
        if key.startswith(prefix) and "." not in key[len(prefix) :]
    ]


def _file_of(spans, key):
    """The file the span of the item at `key` names, or None."""
    span = spans.get(key)
    return span.file if span is not None else None


def _kept_key(key, renamed):
    """A key of the span table at the kept items' addresses: an item's key
    is its new address, and a key under a block's address, the place of a
    side, a field or a typing entry of its header, keeps its tail under the
    block's new address."""
    parts = key.split(".")
    for n in range(len(parts), 0, -1):
        head = ".".join(parts[:n])
        if head in renamed:
            return renamed[head] + key[len(head) :]
    return key


def operative_definitions(stage, blocks):
    """The definitions table of `stage` with the bound blocks `blocks`: the
    declared table with each block's records written into it, a record
    replacing the declared one of its identity in place."""
    table = dict(declared_definitions(stage))
    for block in blocks:
        for record in block.definitions:
            table[record.identity] = record
    return MappingProxyType(table)


def declared_version(stage):
    """The stage as its stage file declares it and elaboration builds it:
    for a stage built from the union of its stage file and its additions,
    whose provenance records the additions, the stage file's own text
    elaborated alone, with no binding (specification 0.7 §4 rule 6, the
    erasure); otherwise `stage` itself while it holds no binding, and
    otherwise a version holding the same initial diagrams and stored
    builders graphs, the declared definitions table and the methods the
    stage binds, with no block, calibration or settings, kept for the version
    (specification 0.6 §7). `stage.declared` reads it, so that `methods` at
    the declared level answers the methods the stage binds (decision SC-24);
    its cards print no binding (`is_declared_version`), and the cards of the
    blocks and the lines of the initial diagrams read it, so that no binding
    changes them (decisions SC-13 and SC-22)."""
    if stage.provenance.get("additions"):
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


# the four mappings a stage's bindings hold, and the level a declared
# version's provenance records
_BINDING_NAMES = ("calibration", "methods", "settings", "blocks")
_DECLARED = "declared"


def _declared_alone(stage):
    """The stage file of `stage` elaborated alone, the declared level of a
    stage built from a union, under the stage's provenance without the
    additions and marked as the declared level, so that the declared version
    of a declared version is itself."""
    term, spans = parse_with_spans(stage.provenance["text"], stage.provenance["origin"])
    alone = type(stage)(**stage_fields(term, spans))
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
