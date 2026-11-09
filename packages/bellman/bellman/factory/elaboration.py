"""The construction of a stage from its source record, the mapping
`load_stage` returns: `elaborate_stage` for a record and `elaborate_text`
for a text and its origin; `source_spans` for the span table of a text, and
`bind_stage` for the binding of a stage from a record's three sources with a
report of what bound. A record may carry additions, the `.bl` methods files
of the stage, each as its text and its origin: `construct_stage` parses the
stage text and each addition, unions the parsed files (`bellman.syntax.union`)
and constructs the one term, so that the elaborator reads every entry and
line of an addition as if the stage file had written it; the provenance of
the version records each addition. `elaborate_stage` binds, unless its
keyword `bind` is false, every source the record supplies, by the inner forms
of the three binding verbs (`bellman.stage.binding_verbs`), which copy
nothing, and copies the stage once, at the end. A text the parser or the
lowering cannot read is refused under the rule `syntax`.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from traceback import clear_frames
from typing import NamedTuple

from lark.exceptions import LarkError

from bellman.native.frozen import freeze
from bellman.native.hypergraphs import copy_native
from bellman.native.provenance import grammar_versions, source_description
from bellman.native.versions import replace_stage
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage.binding_verbs import (
    calibrated_version,
    configured_version,
    methodized_version,
    methods_folder,
)
from bellman.stage.elaborated import make_stage
from bellman.stage.method_blocks import operative_level
from bellman.stage.method_table import solution_words
from bellman.stage.sources import load_methods
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.parse import expected_forms, grammar_sentence, marked_line, place_at
from bellman.syntax.union import union

# --- the stage of a record and the symbolic stage of a text ---


def elaborate_stage(record, *, bind=True):
    """The stage of one source record, the mapping `load_stage` returns: its
    text parsed and constructed at its origin and, where `bind` is true, as
    it is by default, every source the record supplies bound, in the order
    calibrate, methodize, configure. A non-empty `calibration` is bound as
    `calibrate` binds it, a `methods` mapping from which `load_methods` reads
    at least one entry as `methodize` binds it, and a non-empty `settings` as
    `configure` binds it. An empty source is no source: the record
    `load_stage` returns, whose calibration and settings are `{}` and whose
    methods are `{"methods": []}`, answers the symbolic stage, and so does
    any record with `bind=False`. The additions a record carries under
    `additions`, each its text and its origin, are unioned with the stage
    text before the construction (`construct_stage`). Each binding is made
    by the inner form of its verb, which copies nothing, and the stage is
    copied once, at the end, by `copy_native`; its provenance records the
    additions and the bindings as the three verbs record them. Reads no
    file. A path string, or a mapping that is no record, is refused under
    `record-shape`; a `bind` that is not True or False is refused; a source
    is refused as its verb refuses it, and settings supplied without methods
    as `configure` refuses them.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §1."""
    if type(bind) is not bool:
        raise TypeError(
            f"elaborate_stage: bind is {bind!r}, which is not True or False; bind says whether "
            "the sources the record supplies are bound; write bind=False for the symbolic "
            "stage, or leave bind out to bind them"
        )
    source = stage_text_of(record)
    version = stage_occurrence(
        record,
        construct_stage(source.text, source.origin, source.additions),
        address="record",
        version_record=grammar_versions(),
    )
    if bind:
        # each source the record supplies, by the inner form of its verb; an
        # empty source binds nothing, and no version before the last is copied
        if record["calibration"]:
            version = calibrated_version(version, record["calibration"])
        if load_methods(record["methods"])["methods"]:
            version = methodized_version(version, record["methods"])
        if record["settings"]:
            version = configured_version(version, record["settings"])
    return copy_native(version)


def elaborate_text(text, origin):
    """The symbolic stage of a stage text with `origin` recorded as its
    source, as `elaborate_stage` builds it from the record of the text with
    empty calibration, settings and methods sources: the one reader of a text
    that the dossier, the refusal catalogue and the command line elaborate.
    Its methods source is the empty mapping `{}`, from which the digest that
    `--encoding` prints is computed; the mapping `load_stage` writes,
    `{"methods": []}`, would give another digest."""
    return elaborate_stage(
        {
            "stage": {"text": text, "origin": origin},
            "calibration": {},
            "settings": {},
            "methods": {},
        }
    )


# --- the stage text of a record ---

_REQUIRED = ("stage", "calibration", "settings", "methods")


class Addition(NamedTuple):
    """One addition of a source record: the text of a methods file, its
    origin and the SHA-256 digest of the text."""

    text: str
    origin: str
    digest: str


class StageText(NamedTuple):
    """The stage text of a source record: the text, its origin, the SHA-256
    digest of the text, the provenance entries the record supplies, and the
    additions the record carries, in order."""

    text: str
    origin: str
    digest: str
    supplied: Mapping
    additions: tuple = ()

    @property
    def construction(self):
        """What the construction of the record depends on: the digest and the
        origin of the stage text and those of each addition, by which two
        records that construct one stage are told to."""
        return (self.digest, self.origin) + tuple(
            (addition.digest, addition.origin) for addition in self.additions
        )


def stage_text_of(record, address="record"):
    """The `StageText` of a source record, the mapping `load_stage` returns.
    Refused under `record-shape` where the record is a path string or no
    mapping, lacks a field, holds a field of the wrong form, writes its stage
    as a path, supplies a location or a digest that disagrees with its
    source, or carries an addition that is not the text and the origin of a
    methods file."""
    if not isinstance(record, Mapping):
        what = (
            f"the path string {record!r}"
            if isinstance(record, str)
            else f"a {type(record).__name__}"
        )
        raise FactoryError(
            f"{what} is no record; a record is the mapping load_stage returns, holding the "
            "stage's text and origin and its three mappings",
            rule="record-shape",
            address=address,
            written=repr(record)[:80],
            write="elaborate_stage(load_stage(path))",
        )
    missing = sorted(name for name in _REQUIRED if name not in record)
    unknown = sorted(record.keys() - set(_REQUIRED) - {"label", "provenance", "additions"})
    if missing or unknown:
        raise FactoryError(
            f"missing fields {missing!r}; unknown fields {unknown!r}",
            rule="record-shape",
            address=address,
            written=repr(sorted(record)),
            write="a record with stage, calibration, settings "
            "and methods, and optionally label, provenance and additions",
        )
    for name in ("calibration", "settings", "methods", "provenance"):
        if not isinstance(record.get(name, {}), Mapping):
            raise FactoryError(
                f"{name} must be a mapping",
                rule="record-shape",
                address=f"{address}.{name}",
                written=repr(record[name])[:80],
                write=f"{name}: {{...}}",
            )
    if "label" in record and not isinstance(record["label"], str):
        raise FactoryError(
            "label must be a string",
            rule="record-shape",
            address=f"{address}.label",
            written=repr(record["label"]),
            write="label: <text>",
        )
    source = record["stage"]
    if isinstance(source, str):
        raise FactoryError(
            f"stage is the path string {source!r}; a verb of the factory reads no file, and the "
            "record holds the text",
            rule="record-shape",
            address=f"{address}.stage",
            written=source,
            write="elaborate_stage(load_stage(path))",
        )
    if (
        not isinstance(source, Mapping)
        or set(source) != {"text", "origin"}
        or not isinstance(source["text"], str)
        or not isinstance(source["origin"], str)
        or not source["origin"]
    ):
        raise FactoryError(
            "stage requires exactly text and origin, both strings",
            rule="record-shape",
            address=f"{address}.stage",
            written=repr(source)[:80],
            write="stage: {text: <the file's text>, origin: <its path>}",
        )
    text, origin = source["text"], source["origin"]
    digest = sha256(text.encode("utf-8")).hexdigest()
    additions = []
    for number, addition in enumerate(record.get("additions") or (), 1):
        if (
            not isinstance(addition, Mapping)
            or set(addition) != {"text", "origin"}
            or not isinstance(addition["text"], str)
            or not isinstance(addition["origin"], str)
            or not addition["origin"]
        ):
            raise FactoryError(
                f"addition {number} requires exactly text and origin, both strings",
                rule="record-shape",
                address=f"{address}.additions",
                written=repr(addition)[:80],
                write="additions: [{text: <the methods file's text>, origin: <its path>}]",
            )
        additions.append(
            Addition(
                addition["text"],
                addition["origin"],
                sha256(addition["text"].encode("utf-8")).hexdigest(),
            )
        )
    supplied = record.get("provenance", {})
    location = {name: supplied[name] for name in ("path", "origin") if name in supplied}
    if location and location != {"origin": origin}:
        raise FactoryError(
            f"the supplied module location {location!r} does not match the stage source "
            f'{{"origin": {origin!r}}}',
            rule="record-shape",
            address=f"{address}.provenance",
            written=repr(location),
            write=f"origin: {origin!r}, or no location in the provenance",
        )
    if "sha256" in supplied and supplied["sha256"] != digest:
        raise FactoryError(
            "the supplied module hash disagrees with the text read",
            rule="record-shape",
            address=f"{address}.provenance",
            written=supplied["sha256"],
            write=f"sha256: {digest}, or no sha256 in the provenance",
        )
    return StageText(
        text=text, origin=origin, digest=digest, supplied=supplied, additions=tuple(additions)
    )


# --- the stage occurrence and the construction of a text ---


def stage_occurrence(record, initial, *, address, version_record, position=None):
    """The version of `initial`, the stage the record's text constructs, whose
    provenance holds the record's own entries (its `source_lists` among them,
    unread), the origin, the text, the digest, the origin, the text and the
    digest of each addition under `additions` where the record carries one,
    the description of each of its three mappings under `sources`, the
    `versions` record given, the record's `label` and `position` where
    given. The caller copies it with `copy_native`, so that no two positions
    share a version."""
    source = stage_text_of(record, address)
    text, origin, digest, supplied = source.text, source.origin, source.digest, source.supplied
    sources = {
        name: source_description(record[name], supplied.get(name))
        for name in ("methods", "settings", "calibration")
    }
    provenance = {
        **supplied,
        "origin": origin,
        "text": text,
        "sha256": digest,
        "sources": sources,
        "versions": version_record,
    }
    if source.additions:
        provenance["additions"] = tuple(
            {"origin": addition.origin, "text": addition.text, "sha256": addition.digest}
            for addition in source.additions
        )
    if position is not None:
        provenance["position"] = position
    if "label" in record:
        provenance["label"] = record["label"]
    return replace_stage(initial, provenance=freeze(provenance))


def construct_stage(text, origin, additions=()):
    """The stage a text constructs at `origin`, with the `additions`, each an
    `Addition`, unioned into it in order, or its refusal: a text the parser
    or the lowering cannot read is refused under `syntax` in its own file,
    the union refuses as `bellman.syntax.union` refuses, the union is read
    at the operative level (`operative_level`, with the solution words of
    the catalogue), and the construction reads the one term. The frames of
    the parser and the construction are cleared, so that no refusal holds a
    parsed AST."""
    parsed = unioned = None
    try:
        failure = None
        files = [(text, origin), *((each.text, each.origin) for each in additions)]
        parsed = []
        for held_text, held_origin in files:
            try:
                parsed.append(parse_with_spans(held_text, filename=held_origin))
            except (LarkError, ValueError) as error:
                failure = _syntax_refusal(error, held_text, held_origin)
                clear_frames(error.__traceback__)
                break
        # Raising outside the handler keeps parser state out of __context__.
        if failure is not None:
            raise failure from None
        try:
            unioned = operative_level(union(parsed[0], parsed[1:]), origin, solution_words())
            return make_stage(unioned.term, unioned.spans)
        except ConstructionError as error:
            if error.file is None:
                error.file = origin
            raise
    except Exception as error:
        # Completed parser and builder frames can otherwise retain their ASTs.
        pending, seen = [error], set()
        while pending:
            current = pending.pop()
            if id(current) in seen:
                continue
            seen.add(id(current))
            clear_frames(current.__traceback__)
            pending.extend(
                value for value in (current.__cause__, current.__context__) if value is not None
            )
        raise
    finally:
        parsed = unioned = None


# --- the refusal of a text the parser or the lowering cannot read ---


class SyntaxParts(NamedTuple):
    """The three parts a refusal under the rule `syntax` writes its message
    from, which the catalogue of refusals prints each under its own heading:
    `why`, what the file writes there and what the language admits; `what`,
    the line of the file with a mark under the column; `write`, what to write
    instead."""

    why: str
    what: str
    write: str


def _syntax_refusal(error, text, origin):
    """The refusal of a text the parser or the lowering cannot read, under the
    rule `syntax` or the rule the lowering names, in the four parts of a refusal.

    Where: the file, the line and the column, which `ConstructionError` writes
    before the message. What: the line of the file with a mark under the
    column. Why: what the file writes there and, for a refusal of the parser,
    the forms the language admits at that place, each terminal of the grammar
    read once from `syntax.parse.FORMS`. What to write: the sentence of the
    grammar's own comment for the place the position falls inside, where it
    falls inside a block header or an operator's subscript, and the sentence
    the lowering supplies where the lowering refuses. No token name and no
    rule name of Lark is written."""
    line = getattr(error, "line", None)
    column = getattr(error, "column", None)
    line = line if type(line) is int else None
    column = column if type(column) is int else None
    forms = expected_forms(
        getattr(error, "accepts", None)
        or getattr(error, "expected", None)
        or getattr(error, "allowed", None)
        or ()
    )
    advice = getattr(error, "advice", None)
    if forms:
        # a spelling of the language is quoted; a phrase that says what may
        # stand there, `a name`, is written as it reads
        quoted = [form if " " in form else f"`{form}`" for form in forms]
        admitted = " or ".join([", ".join(quoted[:-1]), quoted[-1]] if len(quoted) > 1 else quoted)
        why = f"{_written(error)}, and the language admits {admitted} at this place"
        place = None if line is None else place_at(text, line, column)
        if place is not None:
            advice = f"{place}: {grammar_sentence(place)}"
    else:
        # the lowering refuses in its own sentence, which quotes what it read
        # (`syntax.lower._refusal`)
        why = error.message if isinstance(error, ConstructionError) else str(error)
    marked = "" if line is None else marked_line(text, line, column)
    parts = SyntaxParts(why=why, what=marked, write=advice or "")
    refusal = ConstructionError(
        "\n".join(part for part in parts if part),
        file=origin,
        line=line,
        column=column,
        # a refusal of the lowering keeps the rule it names, `syntax` or
        # `marginal-role-retired`; a refusal of the parser is under `syntax`
        rule=error.rule if isinstance(error, ConstructionError) else "syntax",
    )
    # the three parts the message is written from, which the catalogue of the
    # rules (`refusal_catalogue.py`) shows each under its own heading
    refusal.parts = parts
    return refusal


def _written(error):
    """What the file writes where the parser stopped, in one short piece: the
    first line of the text the parser read there, shortened where it is long,
    or the end of the line or of the file where it read none."""
    token = getattr(error, "token", None)
    written = str(token) if token is not None else (getattr(error, "char", None) or "")
    if getattr(token, "type", None) == "$END":
        return "the file ends here"
    head = written.split("\n")[0].strip()
    if not head:
        return "the line ends here"
    return f"the file writes `{head if len(head) <= 24 else head[:24] + '…'}` here"


# --- the spans of a text, and the binding of a stage from a record ---


def source_spans(text, origin):
    """The span table of a stage text: a read-only mapping from the address
    of each authored item to its `SourceSpan`, the file as `origin` names
    it, the line and the column of the item's first character and those
    just after its last, counted from one, the column in code points
    (`bellman.syntax.lower.parse_with_spans`). A top-level item is
    addressed by its position among the file's top-level items, counted
    from one, or, where it is a block whose header writes an id, by that
    id. An item inside a block is addressed under the block's address:
    `<block>.<id>` where its annotation or its header writes an id,
    `<block>.<label>` where a nested block's header writes a label and no
    id, and `<block>.<n>` otherwise, n its position in the block's body,
    counted from one (`bellman.syntax.lower.item_addresses`). After the
    authored items, the table holds the place of each side of a block
    header, `<block>.in` and `<block>.out`, each field the side lists,
    `<block>.in.<field>`, and each component of that field's typing,
    `<block>.in.<field>.domain`, `.role` and `.perch` (unit T of the model
    interface specification 0.3, the classification table). A text the
    parser or the lowering cannot read is refused as `elaborate_text`
    refuses it, under the rule `syntax` at the refused position, so that an
    editor marks one place for the spans and for the elaboration."""
    try:
        return parse_with_spans(text, filename=origin).spans
    except (LarkError, ValueError) as error:
        refusal = _syntax_refusal(error, text, origin)
        clear_frames(error.__traceback__)
    raise refusal from None


class Binding(NamedTuple):
    """What `bind_stage` answers: `stage`, the stage bound by every verb that
    succeeded, in the order calibrate, methodize, configure, and the stage
    given where none bound; `bound`, the verbs applied; `skipped`, the verbs
    whose source binds nothing; and `failed`, each verb that refused its
    source, with the refusal's sentence."""

    stage: object
    bound: tuple
    skipped: tuple
    failed: dict


def bind_stage(stage, record):
    """The `Binding` of `stage` from the three sources of `record`, the
    `calibration`, `methods` and `settings` of a record `load_stage` or
    `load_recipe` returns, each a mapping or the path of a YAML file. Each
    source is applied as `elaborate_stage` applies it, in that order, by the
    inner form of its verb: a calibration or a settings source that is a path
    or a non-empty mapping, and a methods source from which `load_methods`
    reads at least one entry; an empty source is skipped. A verb that refuses
    its source leaves the stage as the verbs before it made it, and its
    sentence stands in `failed` under the verb's name; the next verb is still
    applied, so settings after a failed methodize are refused as the verb
    refuses settings without methods. The inner forms bind a version of
    the stage's own, holding its records, so that the stage given is left as
    it was; that version is copied once, at the end, where a verb bound, and
    otherwise the answer holds the stage given. A source given as a path is
    read as its verb reads it."""
    # the block paths of a methods mapping are read beside the methods file
    # the record's provenance names (decision SC-16)
    folder = methods_folder(record.get("provenance") or {})
    verbs = (
        ("calibrate", "calibration", lambda source: bool(source), calibrated_version),
        (
            "methodize",
            "methods",
            lambda source: bool(load_methods(source)["methods"]),
            lambda version, source: methodized_version(version, source, base=folder),
        ),
        ("configure", "settings", lambda source: bool(source), configured_version),
    )
    version, bound, skipped, failed = replace_stage(stage), [], [], {}
    for verb, kind, supplied, inner_form in verbs:
        source = record[kind]
        try:
            if not supplied(source):
                skipped.append(verb)
                continue
            version = inner_form(version, source)
        except (ValueError, LookupError, TypeError) as refusal:
            failed[verb] = str(refusal)
            continue
        bound.append(verb)
    return Binding(stage=copy_native(version) if bound else stage,
                   bound=tuple(bound), skipped=tuple(skipped), failed=failed)
