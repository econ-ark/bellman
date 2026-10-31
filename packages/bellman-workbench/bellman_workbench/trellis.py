"""The trellis of a model folder, for Bellman Workbench (model interface
specification 0.3, §3.1): the part of the backend that §7 names "trellis",
beside `model.py` and `recipe.py`, and like them free of Solara.

The trellis of a source is read by the package's reader of that source. It
is elaborated and bound in one call of `specify_trellis`, with the trellis
shown before as its `previous`, so that a changed stage text alone is
constructed again and each occurrence is copied once. Where only stage
files and binding source files changed since the trellis shown before was
read, the occurrences whose record changed are bound again alone, by
`respecify_trellis`, and the others are kept as that trellis holds them
(`bind_changed_stages`; unit L, Task 20). The kinds bound are
those some record binds; a kind the package refuses is reported and left
out of the next call, so that the other kinds still bind (decision B-D3).
The bound trellis is drawn by `to_model_explorer`, restricted to the
occurrences the view's bar selects, or, where the package refuses that
selection, to those of the restriction it accepted last for the source.
Where the trellis shown before is of the same source and no file read for
it holds another text, on disk or in the unsaved buffer the reading takes,
that trellis is drawn again and the source is not read again. Where no
trellis of the same source was shown before, the binding is read from the
file in which a reading of the same syntactic trellis by the same code
kept it, under the user's cache folder (`read_binding`), and is otherwise
bound; the page keeps the binding of such a reading there once it holds
the outcome (`keep_binding`). The functions here compose the package's
answers and compute none of their own.
"""

from __future__ import annotations

import contextlib
import dataclasses
import functools
import hashlib
import importlib.metadata
import importlib.util
import itertools
import json
import logging
import os
import pickle
import re
import shutil
import stat
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import NamedTuple

from bellman.factory.model_explorer import BOUNDARY_KINDS, ROUTE_KEY
from bellman.factory.trellis_drawings import join_label
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage import (
    INITIAL_IDS,
    arvl,
    branches,
    cntn,
    elaborate_stage,
    load_stage,
    source_spans,
    to_source,
)
from bellman.stage.boxes import piece_named
from bellman.stage.stage_answers import entry_perch
from bellman.stage.builder_pairs import BACKWARD_PAIRS, FORWARD_PAIRS, builder_pairs
from bellman.syntax.vocabulary import PERCH_SIGN, PERCH_WORD
from bellman.trellis import (
    BOUNDARY_IDS,
    LAYER_ID_ENDING,
    append_to_mapping,
    append_to_sequence,
    changed_positions,
    connector_entry,
    connection_report,
    Selection,
    trellis_selection,
    entry_span,
    entry_value,
    insert_in_sequence,
    layers_to_open,
    node_place,
    read_trellis_file,
    remove_from_mapping,
    remove_from_sequence,
    respecify_trellis,
    specify_trellis,
    to_model_explorer,
    unpaired_joins,
    written_at,
    written_spans,
)
from bellman_workbench import creation, model, recipe

__all__ = [
    "TRELLIS_DEPTH",
    "opening_restriction",
    "SHAPE_RULE",
    "Restriction",
    "parse_restriction",
    "MENU_RANGE_ENDS",
    "RestrictionChoice",
    "restriction_menu",
    "selects",
    "TrellisBinding",
    "bind_trellis",
    "bind_changed_stages",
    "binding_notes",
    "relative_sentence",
    "code_digest",
    "code_version",
    "binding_entry",
    "read_binding",
    "keep_binding",
    "Unsaved",
    "texts_of",
    "TrellisShown",
    "TrellisOutcome",
    "files_read",
    "files_of_refusal",
    "files_before_reading",
    "file_digests",
    "inputs_current",
    "show_trellis",
    "address_place",
    "PORT_KEYS",
    "Subject",
    "port_rows",
    "occurrence_positions",
    "listed_periods",
    "view_periods",
    "describe_node",
    "block_line",
    "occurrence_file",
    "Link",
    "Use",
    "Line",
    "Cells",
    "OccurrenceRows",
    "JoinRows",
    "line_text",
    "use_rows",
    "occurrence_rows",
    "join_rows",
    "JoinLinks",
    "refusal_links",
    "restoring_edit",
    "typed_line",
    "reading_record",
    "unjoined_ports",
    "PAIRING_SUFFIXES",
    "pairing_names",
    "connectable_ports",
    "Gesture",
    "gesture_sentence",
    "connector_edit",
    "stage_items",
    "period_controls",
    "moved_ranges",
    "drop_edits",
    "added_stage_joins",
    "unjoined_count",
    "missing_joins",
    "without_occurrence",
    "refused_bindings",
    "join_wires",
    "removal_edit",
    "stage_removal_edit",
    "period_removal_edit",
]

# the depth of the namespaces the trellis view opens: the periods and their
# occurrences (specification §2.3)
TRELLIS_DEPTH = 2
# A trellis of more than this many periods opens the occurrence layers of
# its last three periods alone, periods 0 to 2, and the other periods as
# closed layers, so that the page draws a long trellis in seconds; a click
# opens any other period (AAS, 3 October 2026: the trellis's load time
# first).
OPEN_PERIODS_WHOLE = 6
OPEN_OCCURRENCES_UP_TO = 2


def opening_restriction(syntactic: dict) -> str | None:
    """The text the view's bar opens with for the syntactic trellis
    `syntactic` (specification §3.1): for a trellis of more than
    `OPEN_PERIODS_WHOLE` periods, the restriction to periods 0 to
    `OPEN_OCCURRENCES_UP_TO`, `periods 0–2`, the terminal period and the
    two before it, so that a long trellis is first drawn in part (AAS, 3
    October 2026: the trellis's load time first); None for a shorter
    trellis, which opens whole."""
    if len(syntactic["periods"]) <= OPEN_PERIODS_WHOLE:
        return None
    return f"periods 0–{OPEN_OCCURRENCES_UP_TO}"


# the rule of a refusal of the trellis file's own shape, whose address names
# an entry of the file by its position and not a period of the trellis
SHAPE_RULE = "trellis-file-shape"

# the three trellis verbs in the order they bind, each with the name the
# report uses and the kind of binding source it binds, the kind
# `specify_trellis` takes and names in the note of a refusal
_TRELLIS_VERBS = (
    ("calibrate", "calibration"),
    ("methodize", "methods"),
    ("configure", "settings"),
)

# the refusals the factory raises, which a reading reports and does not
# raise; a target a methods file names and the stage lacks is a
# `TargetError`, a LookupError, which `bind_stage` catches too
_REFUSALS = (ConstructionError, FactoryError, ValueError, LookupError, TypeError)

# The page's log, as `app.LOG` is: an exception of no class of the package's
# refusals that a reading of the trellis meets is written there with its
# traceback (unit L, Task 21; defect 18 of the UX simulation).
LOG = logging.getLogger(__name__)

# the keys of a port's row in the panel of a node of a trellis view: the
# stage view's, and the three a join adds
PORT_KEYS = model._PORT_KEYS + ("join", "paired by", "outside")


# --- the restriction typed in the view's bar ---


class Restriction(NamedTuple):
    """What the view's bar selects (specification §3.1): `periods`, the
    indices of the periods, None for every period; `stages`, the stage keys,
    None for every key; and `text`, the selection as the status line names
    it, `periods 0–1, stages cons`."""

    periods: tuple[int, ...] | None
    stages: tuple[str, ...] | None
    text: str


# a clause of the restriction begins at the word `periods` or `stages`,
# after a comma or a semicolon and the spaces around it
_CLAUSE = re.compile(r"\s*[,;]\s*(?=(?:periods|stages)\b)")
# a period range, `0–2` or `0-2`, or one period, `3`
_RANGE = re.compile(r"(\d+)(?:\s*[–-]\s*(\d+))?")
# a stage key, as the recipe and the trellis files write one
_KEY = re.compile(r"\w+(?:\.\w+)*")


def parse_restriction(text: str) -> Restriction | None:
    """The restriction typed in the view's bar: a period range, `periods
    0–2`, or one period, `periods 3`; stage keys, `stages cons, port`; or
    both, joined by a comma or a semicolon, `periods 0–1, stages cons`; the
    spaces around a comma or a semicolon, and a comma after the last key,
    are read as nothing. An empty text answers None, the whole trellis.
    Anything else is refused with a ValueError in one line that names what
    is wrong and, where that alone does not say it, what to write; a period
    or a key the trellis does not hold is the package's to refuse."""
    written = " ".join(text.split())
    if not written:
        return None
    periods = stages = None
    for clause in _CLAUSE.split(written):
        word, _, rest = clause.partition(" ")
        if word == "periods" and periods is None:
            found = _RANGE.fullmatch(rest)
            if found is None:
                raise ValueError(
                    f"`{clause}` is no period range; write `periods 0–2` or `periods 3`"
                )
            low, high = int(found[1]), int(found[2] or found[1])
            if low > high:
                raise ValueError(f"the range `{rest}` runs from {low} down to {high}")
            periods = tuple(range(low, high + 1))
        elif word == "stages" and stages is None:
            # the empty text a comma after the last key leaves is no key
            keys = [key.strip() for key in rest.split(",") if key.strip()]
            if not keys or not all(_KEY.fullmatch(key) for key in keys):
                raise ValueError(f"`{clause}` names no stage keys; write `stages cons, port`")
            stages = tuple(dict.fromkeys(keys))
        else:
            raise ValueError(
                f"`{clause}` is neither `periods 0–2` nor `stages cons, port`, each written once"
            )
    return Restriction(periods, stages, _restriction_text(periods, stages))


def _restriction_text(periods: tuple[int, ...] | None, stages: tuple[str, ...] | None) -> str:
    """The text of the restriction to the range of periods `periods` and the
    stage keys `stages`, each None for all, as `parse_restriction` writes
    it: `periods 0–1, stages cons`, `periods 3`, or the empty text for the
    whole trellis."""
    parts = []
    if periods is not None:
        parts.append(f"periods {periods[0]}" + (f"–{periods[-1]}" if len(periods) > 1 else ""))
    if stages is not None:
        parts.append("stages " + ", ".join(stages))
    return ", ".join(parts)


# the last period of each range the restriction's menu offers, every range
# running from the terminal period, periods[0] (unit K, K-D17)
MENU_RANGE_ENDS = (2, 5, 10, 20)


class RestrictionChoice(NamedTuple):
    """One item of the restriction's menu (unit K, K-D17; design pass 2 §3):
    `label`, the words it prints, a range `0–2`, `all 51` or a stage key;
    `text`, the restriction its choice writes, as `parse_restriction` reads
    it, None for the one stage key ticked, which cannot be unticked; and
    `chosen`, whether the restriction that stands has the item's range, or
    ticks the item's key."""

    label: str
    text: str | None
    chosen: bool


def restriction_menu(
    restriction: Restriction | None, syntactic: dict | None
) -> tuple[list[RestrictionChoice], list[RestrictionChoice]]:
    """The items of the restriction's menu (unit K, K-D17; design pass 2 §3)
    for the restriction that stands, `restriction`, None for the whole
    trellis, and the syntactic trellis `syntactic`, None where none is
    read: the ranges, then the checks. The ranges run from the terminal
    period, `0–2`, `0–5`, `0–10` and `0–20`, each listed where the trellis
    holds its last period, and `all`, with the count of periods where a
    trellis is read; a range keeps the stage keys that stand. The checks
    are the trellis's stage keys in the order in which the periods from the
    terminal one first list them, each ticked where the restriction holds
    it; a key ticked or unticked keeps the periods that stand, every key
    ticked writing no stage clause. Every text is one of spec 0.4 §2.6's
    grammar, which `parse_restriction` reads."""
    periods = None if restriction is None else restriction.periods
    stages = None if restriction is None else restriction.stages
    if syntactic is None:
        return [RestrictionChoice("all", _restriction_text(None, stages), periods is None)], []
    count = len(syntactic["periods"])
    ranges = [
        RestrictionChoice(
            f"0–{last}",
            _restriction_text(tuple(range(last + 1)), stages),
            periods == tuple(range(last + 1)),
        )
        for last in MENU_RANGE_ENDS
        if last < count
    ]
    ranges.append(
        RestrictionChoice(f"all {count}", _restriction_text(None, stages), periods is None)
    )
    keys = list(dict.fromkeys(key for period in syntactic["periods"] for key in period["stages"]))
    ticked = [key for key in keys if stages is None or key in stages]
    checks = []
    for key in keys:
        kept = [other for other in keys if (other in ticked) != (other == key)]
        if not kept:
            text = None
        else:
            text = _restriction_text(periods, None if kept == keys else tuple(kept))
        checks.append(RestrictionChoice(key, text, key in ticked))
    return ranges, checks


def _selection(restriction: Restriction | None) -> dict:
    """The keyword arguments with which `to_model_explorer` and
    `unpaired_joins` select the occurrences of `restriction`: none for the
    whole trellis."""
    if restriction is None:
        return {}
    return {"periods": restriction.periods, "stages": restriction.stages}


def selects(restriction: Restriction | None, h: int, key: str) -> bool:
    """Whether a restriction holds the occurrence at `(h, key)`; the whole
    trellis, None, holds every occurrence."""
    return restriction is None or (
        (restriction.periods is None or h in restriction.periods)
        and (restriction.stages is None or key in restriction.stages)
    )


# --- the binding of a trellis ---


class TrellisBinding(NamedTuple):
    """The binding of a trellis, as `bind_trellis` answers it: `trellis`, the
    trellis `specify_trellis` answers with the kinds of every verb that
    succeeded; `bound`, those verbs, among `calibrate`, `methodize` and
    `configure`, in that order; `skipped`, the verbs to which no record
    gives a mapping to bind; and `failed`, each verb the package refused,
    with the refusal's sentence and the position it names."""

    trellis: dict
    bound: tuple
    skipped: tuple
    failed: dict


def _binds_something(kind: str, record: dict) -> bool:
    """Whether a record's mapping of `kind` binds something: a calibration or
    a settings mapping that is not empty, a methods mapping whose list
    `methods` is not empty, the form `load_recipe` and `load_trellis` write
    for a slot or a source left unbound."""
    mapping = record.get(kind) or {}
    return bool(mapping.get("methods")) if kind == "methods" else bool(mapping)


def bind_trellis(elaborated: dict | None, syntactic: dict) -> TrellisBinding:
    """The `TrellisBinding` of the syntactic trellis `syntactic`
    (specification §3.1; decision B-D3), answered by
    `specify_trellis(syntactic, elaborated, kinds)`. `elaborated`, a trellis
    elaborated or bound before, or None, is the `previous` of
    `specify_trellis`: its occurrences of an unchanged stage text are taken
    as they stand, so that an occurrence taken from a bound trellis keeps
    its binding of a kind this call skips or refuses, and is bound again
    under a kind it binds where the record's mapping of that kind differs
    from what the occurrence holds. `kinds` are the kinds of binding source
    some record binds; a verb whose kind no record binds is skipped. A
    refusal whose notes name a kind, `Binding kind: <kind>`, records that
    kind's verb as failed, with the package's sentence in the form
    `model.refusal_of` gives it: the refusal's message, the words it says to
    write on a line of their own, and its other notes on a line each, the
    position among them (AMD-MI-002 §6a; ruling R51); `specify_trellis` is
    then called again with the kinds less that one, so that the other verbs
    still bind. A refusal that names no kind, a refusal of the elaboration,
    is raised. The package binds every position under a kind or refuses, so
    a failed verb binds no occurrence."""
    skipped = _skipped_verbs(syntactic)
    verbs = [(verb, kind) for verb, kind in _TRELLIS_VERBS if verb not in skipped]
    failed = {}
    while True:
        try:
            specified = specify_trellis(syntactic, elaborated, [kind for _, kind in verbs])
        except _REFUSALS as refusal:
            notes = getattr(refusal, "__notes__", ())
            refused = [(verb, kind) for verb, kind in verbs if f"Binding kind: {kind}" in notes]
            if not refused:
                raise
            verb, kind = refused[0]
            found = model.diagnostic_of(refusal)
            failed[verb] = "\n".join(
                [
                    found.message,
                    *([found.advice] if found.advice else []),
                    *(note for note in notes if note != f"Binding kind: {kind}"),
                ]
            )
            verbs.remove((verb, kind))
        else:
            return TrellisBinding(specified, tuple(verb for verb, _ in verbs), skipped, failed)


def _skipped_verbs(syntactic: dict) -> tuple:
    """The verbs, in their order, to whose kind no record of the syntactic
    trellis `syntactic` gives a mapping that binds something
    (`_binds_something`)."""
    records = [
        record
        for period in syntactic["periods"]
        for record in period["stages"].values()
        if isinstance(record, dict)
    ]
    return tuple(
        verb
        for verb, kind in _TRELLIS_VERBS
        if not any(_binds_something(kind, record) for record in records)
    )


def bind_changed_stages(
    binding: TrellisBinding, before: dict, syntactic: dict
) -> TrellisBinding | None:
    """The `TrellisBinding` of the syntactic trellis `syntactic` that
    `bind_trellis(None, syntactic)` answers, made from `binding`, the one it
    answered for the syntactic trellis `before`, or that this function
    answered for it, by binding again the stage occurrences whose record
    changed alone, each other occurrence kept as `binding` holds it
    (`respecify_trellis`; unit L, Task 20; defect 14 of the UX simulation):
    a change of one stage's sources, its text, a value, a method or a
    setting, binds that stage's occurrences and no other. The verbs bound,
    skipped and failed are those of `binding`, each failed verb with its
    sentence. None where the whole binding could answer otherwise, so that
    the caller binds the whole trellis: where a verb `binding` skips is not
    skipped for `syntactic`, or the reverse; where the stage occurrence a
    failed verb's sentence names (`_OCCURRENCE_NOTE`) is one whose record
    changed, or stands after one, since the whole binding meets that
    record first; where the package refuses a verb `binding` bound at an
    occurrence whose record changed, since the whole binding then binds no
    occurrence under that verb; and where the package refuses the two
    syntactic trellises as differing in more than their records, or the
    trellis of `binding` as bound under other kinds, as when a file was
    saved while it was read. Any other refusal is raised, as `bind_trellis`
    raises it: a refusal of the elaboration, which the whole binding raises
    alike, since an unchanged record raised none before."""
    if _skipped_verbs(syntactic) != binding.skipped:
        return None
    kinds = [kind for verb, kind in _TRELLIS_VERBS if verb in binding.bound]
    try:
        trellis = respecify_trellis(binding.trellis, before, syntactic, kinds)
    except _REFUSALS as refusal:
        notes = getattr(refusal, "__notes__", ())
        if any(note.startswith("Binding kind: ") for note in notes):
            return None
        if isinstance(refusal, FactoryError) and refusal.rule in _FRAME_RULES and not notes:
            return None
        raise
    order = [(h, key) for h, period in enumerate(syntactic["periods"]) for key in period["stages"]]
    first = min(map(order.index, changed_positions(binding.trellis, trellis)), default=len(order))
    for sentence in binding.failed.values():
        named = _OCCURRENCE_NOTE.search(sentence)
        position = None if named is None else (int(named[1]), named[3])
        if position not in order or order.index(position) >= first:
            return None
    return TrellisBinding(trellis, binding.bound, binding.skipped, binding.failed)


# The rules under which `respecify_trellis` refuses arguments that do not
# stand in the relation it requires: two syntactic trellises that differ in
# more than their records, and a trellis bound under other kinds.
_FRAME_RULES = ("trellis-file-shape", "record-shape")


def binding_notes(binding: TrellisBinding) -> list[str]:
    """One note for each verb the package refused in the trellis's binding,
    in the verbs' order, the package's sentence and nothing added
    (AMD-MI-002 §6a rule 2). A verb skipped, to whose kind no record gives
    a mapping that binds something, as while every source of that kind is a
    slot or an empty file, is no refusal and has no note: a slot is a
    parameter of the load (K-D29), and the list under the error mark holds
    refusals alone (unit L, Task 21; defect 17 of the UX simulation)."""
    return [binding.failed[verb] for verb, _ in _TRELLIS_VERBS if verb in binding.failed]


# --- the paths a sentence writes ---

# An absolute path that a sentence writes (unit K's decision K-D11): a slash
# at the start of the sentence or after a space, a quotation mark, an opening
# bracket or `=`, and two names or more, each after a slash, each ending
# before a space, a quotation mark, a comma, a semicolon or a bracket. A
# slash after any other character, as in `1/ρ`, begins no path. A full stop
# or a colon at the path's end belongs to the sentence.
_ABSOLUTE_PATH = re.compile(r"(?<![^\s'\"`(\[{=])(?:/[^\s'\"`,;()\[\]{}<>/]+){2,}(?<![.:])")


def relative_sentence(folder: model.Folder, sentence: str) -> str:
    """`sentence`, as the page prints it, with each absolute path it writes
    (`_ABSOLUTE_PATH`) printed relative to the model folder `folder` and
    every other character kept (usability walkthrough §4 item 6; unit K's
    decision K-D11): a path inside the folder from the folder,
    `declaration/trellis.yml`, the characters after the file's name, as the
    line of `tenure.bl:3`, kept; the folder itself by its name; and a path
    outside it by `..` steps, as `recipe.relative` names a file the model
    reads there (decision B-D6). A path whose parent folder this machine does
    not hold is left as written, since it names no file of the model."""
    root = folder.root

    def relative(match) -> str:
        written = Path(match.group())
        # the path as written, then with its links resolved, since the
        # folder's root is resolved
        for path in (written, written.resolve()):
            if path == root:
                return root.name
            if path.is_relative_to(root):
                return path.relative_to(root).as_posix()
        if not written.parent.is_dir():
            return match.group()
        return Path(os.path.relpath(written.resolve(), root)).as_posix()

    return _ABSOLUTE_PATH.sub(relative, sentence)


# --- the binding kept on disk ---

# The binding that `bind_trellis(None, syntactic)` answers is kept on disk,
# one file, its entry, for each syntactic trellis, so that a later start of
# the Workbench on unchanged files reads it in place of binding the trellis
# again (AAS, 5 October 2026: an exception to the rule that no step of the
# pipeline is skipped, for a cache that can be deleted at any time; ruling
# G-R81). The entries stand in `bellman-workbench/bindings/<code version>/`
# under the user's cache folder, beside the stage views that the package
# keeps in `bellman-workbench/views/`.
_BINDINGS_FOLDER = ("bellman-workbench", "bindings")
# the number of entries a write leaves in the folder of the code version
_ENTRIES_KEPT = 8
# the name of a distribution at the start of a requirement, `numpy` of
# `numpy==2.3.5`, and the word `extra` in a requirement's marker
_DISTRIBUTION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_EXTRA = re.compile(r"\bextra\b")


def _add_file(digest, name: str, path: Path) -> None:
    """Adds the file `path` to `digest` under `name`: the name and the
    number of bytes, then the bytes, so that two different sets of files
    never give one sequence of bytes."""
    content = path.read_bytes()
    digest.update(f"{name}\0{len(content)}\0".encode("utf-8"))
    digest.update(content)


def _add_sources(digest, folder: Path, suffixes: tuple, label: str) -> None:
    """Adds to `digest` every file under `folder` whose suffix is one of
    `suffixes`, each named by `label`, a slash and its posix path relative
    to `folder`, in the order of the paths (`_add_file`)."""
    names = sorted(
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.suffix in suffixes and path.is_file()
    )
    for name in names:
        _add_file(digest, f"{label}/{name}", folder / name)


def _installed_versions() -> dict:
    """Python's major and minor version under `python`, and the installed
    version of the distribution `bellman` and of each distribution its
    metadata requires outside an extra, by name, as `importlib.metadata`
    reads them. A distribution that is not installed raises
    `PackageNotFoundError`."""
    names = ["bellman"]
    for requirement in importlib.metadata.requires("bellman") or []:
        written, _, marker = requirement.partition(";")
        if not _EXTRA.search(marker):
            names.append(_DISTRIBUTION.match(written.strip())[0])
    versions = {"python": f"{sys.version_info.major}.{sys.version_info.minor}"}
    for name in names:
        versions[name] = importlib.metadata.version(name)
    return versions


def code_digest(package: Path, workbench: Path, versions: dict) -> str:
    """The SHA-256 digest of the code that computes a binding: every `.py`,
    `.lark` and `.asdl` file under the folder `package`, each by its path
    relative to that folder and its bytes, in the order of the paths; the
    `pyproject.toml` beside that folder, where one stands there; every
    `.py` file under the folder `workbench`, the same way; and the mapping
    `versions`, as JSON. Raises the `OSError` of a file that cannot be
    read."""
    digest = hashlib.sha256()
    _add_sources(digest, package, (".py", ".lark", ".asdl"), "bellman")
    project = package.parent / "pyproject.toml"
    if project.is_file():
        _add_file(digest, "pyproject.toml", project)
    _add_sources(digest, workbench, (".py",), "bellman_workbench")
    # a JSON object holds no NUL byte, so the versions are never read as a
    # file's name and number of bytes
    digest.update(json.dumps(versions).encode("utf-8"))
    return digest.hexdigest()


@functools.cache
def code_version() -> str | None:
    """The name of the folder of the entries: `code_digest` of the folder
    of the package `bellman`, the folder of `bellman_workbench`, and
    Python's major and minor version with the installed versions of the
    distribution `bellman` and of the distributions it requires outside an
    extra (`_installed_versions`). Computed once in a process, as this
    module is imported, so that it describes the code the process loaded.
    None where a file or a version cannot be read; no entry is then read or
    written."""
    try:
        package = Path(importlib.util.find_spec("bellman").origin).resolve().parent
        workbench = Path(__file__).resolve().parent
        return code_digest(package, workbench, _installed_versions())
    # a file that cannot be read, a package found with no file, a
    # requirement with no name, and a distribution not installed
    except (OSError, ValueError, TypeError, AttributeError, ImportError):
        return None


# The code version is computed now, as the module is imported: computed at
# the first reading instead, it would describe files changed after the
# process loaded its code, and the bindings this process computes with its
# older code would be written into the folder named for the newer files.
code_version()


def _cache_home() -> Path:
    """The user's cache folder, read from the environment at each call: the
    folder `XDG_CACHE_HOME` names where that is an absolute path, and
    `~/.cache` where it is unset, empty or relative, as the XDG Base
    Directory Specification has it and as the package's stage views
    follow."""
    named = Path(os.environ.get("XDG_CACHE_HOME", ""))
    return named if named.is_absolute() else Path.home() / ".cache"


def binding_entry(syntactic: dict) -> Path | None:
    """The file that keeps the binding of the syntactic trellis `syntactic`:
    `bellman-workbench/bindings/<code version>/<key>.pickle` under the
    user's cache folder, `<key>` the SHA-256 of `syntactic` as `repr` writes
    it, in UTF-8. The syntactic trellis holds the text of every stage, every
    mapping bound and the absolute path of every file read, and the binding
    reads no file of the model after it, so that the key and the code
    version name what `bind_trellis(None, syntactic)` answers. None where
    there is no code version (`code_version`)."""
    version = code_version()
    if version is None:
        return None
    key = hashlib.sha256(repr(syntactic).encode("utf-8")).hexdigest()
    return _cache_home().joinpath(*_BINDINGS_FOLDER, version, f"{key}.pickle")


def _users_alone(path: Path) -> bool:
    """Whether the file or folder `path` is owned by the user who runs the
    process (`os.getuid`) and writable by no other user, its mode holding
    neither the group's nor the others' write bit. True where the system
    has no `os.getuid`, as on Windows. Raises the `OSError` of `path.stat`."""
    if not hasattr(os, "getuid"):
        return True
    status = path.stat()
    return status.st_uid == os.getuid() and not status.st_mode & (stat.S_IWGRP | stat.S_IWOTH)


def read_binding(syntactic: dict) -> TrellisBinding | None:
    """The binding of the syntactic trellis `syntactic` kept on disk
    (`binding_entry`), read in place of `bind_trellis(None, syntactic)`,
    its entry marked as used by setting the entry's modification time; None
    where no entry stands or there is no code version. An entry is read by
    `pickle`, which runs code a file can name, and so only where the entry
    and its folder are the user's alone (`_users_alone`); otherwise, or
    where either cannot be examined, None is answered and nothing is
    deleted. A file that cannot be read as a `TrellisBinding`, for any
    error of the read or of `pickle` or for an object of another type, is
    deleted, and None is answered, so that the trellis is bound. A stage
    version read from an entry has none of the answers the package keeps
    beside its graphs, each computed again when first asked."""
    entry = binding_entry(syntactic)
    if entry is None:
        return None
    try:
        if not (_users_alone(entry.parent) and _users_alone(entry)):
            return None
    except OSError:  # no entry, or a folder that cannot be searched
        return None
    try:
        kept = pickle.loads(entry.read_bytes())
    except FileNotFoundError:
        return None
    except Exception:  # any error of the read or of pickle
        kept = None
    if not isinstance(kept, TrellisBinding):
        with contextlib.suppress(OSError):
            entry.unlink()
        return None
    with contextlib.suppress(OSError):
        os.utime(entry)
    return kept


def keep_binding(shown: TrellisShown | None, previous: TrellisShown | None) -> None:
    """Writes the binding of the trellis `shown` to its entry
    (`binding_entry`), so that a later reading of the same syntactic
    trellis, in this process or another, reads it (`read_binding`): only
    where the reading answered a trellis, `shown`, and was given no trellis
    of the same source as `previous`, so that the binding is the one
    `bind_trellis(None, syntactic)` answers, and only where `os.path.exists`
    finds no entry for its key. The binding is written first to a
    temporary file in the entry's folder, which one `os.replace` then puts
    in the entry's place, so that another process finds the whole entry or
    none; the folders `bindings/` and `bindings/<code version>/` are
    created with mode 0o700, the user's alone. A binding that cannot be
    written, as where a folder above the entry cannot be searched, keeps no
    entry, leaves no temporary file this function can remove, and raises
    nothing. After a write, the other folders under
    `bindings/` and all but the entries most recently read or written are
    removed (`_prune`)."""
    if shown is None or (previous is not None and previous.source == shown.source):
        return
    entry = binding_entry(shown.syntactic)
    # `os.path.exists` answers False for a path under a folder that cannot be
    # searched, for which `Path.exists` raises on Python 3.12 and 3.13
    if entry is None or os.path.exists(entry):
        return
    try:
        entry.parent.parent.parent.mkdir(parents=True, exist_ok=True)
        for folder in (entry.parent.parent, entry.parent):
            folder.mkdir(mode=0o700, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(suffix=".tmp", dir=entry.parent)
    except OSError:
        return
    try:
        with os.fdopen(descriptor, "wb") as file:
            pickle.dump(shown.binding, file, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(temporary, entry)
    except Exception:  # a binding pickle refuses, or a disk that refuses the file
        with contextlib.suppress(OSError):
            os.remove(temporary)
        return
    _prune(entry)


def _prune(entry: Path) -> None:
    """After the write of `entry`: every folder under `bindings/` but the
    entry's own, the folders of other code versions, removed, and of the
    entries of the entry's folder all but the `_ENTRIES_KEPT` most recently
    read or written, by their modification times. A file or a folder that
    cannot be removed is left as it stands."""
    folder = entry.parent
    with contextlib.suppress(OSError):
        for other in folder.parent.iterdir():
            if other != folder and other.is_dir():
                shutil.rmtree(other, ignore_errors=True)
    entries = []
    with contextlib.suppress(OSError):
        for path in folder.glob("*.pickle"):
            with contextlib.suppress(OSError):
                entries.append((path.stat().st_mtime_ns, path))
    for _, path in sorted(entries, reverse=True)[_ENTRIES_KEPT:]:
        with contextlib.suppress(OSError):
            path.unlink()


# --- one reading of the trellis ---


class Unsaved(NamedTuple):
    """The unsaved buffer of a file, as the trellis's reading is given it
    (spec 0.4 §3.1, §3.3): `text`, the buffer's text, and `revision`, the
    number of texts the buffer has held, which changes whenever its text
    changes."""

    text: str
    revision: int


def texts_of(unsaved: dict | None) -> dict[str, str]:
    """The mapping the package's readers take (spec 0.4 §3.1): the text of
    each `Unsaved` of `unsaved`, by the same key, a file's resolved path as
    a string; empty where `unsaved` is None."""
    return {path: held.text for path, held in (unsaved or {}).items()}


def _within(texts: dict, paths) -> dict[str, str]:
    """The texts of the mapping `texts` whose path, as a string, is one of
    `paths`."""
    return {name: texts[name] for name in map(str, paths) if name in texts}


# The number of the next reading that binds a trellis, one counter for the
# process (spec 0.4 §3.2; J-D22).
_readings = itertools.count(1)


@dataclasses.dataclass(eq=False)
class TrellisShown:
    """The trellis the view draws: its `source`; the `syntactic` trellis read
    from it; the bound `trellis` and its `binding`; the `restriction` the
    view is drawn under, one the package accepted, None for the whole
    trellis; the `collection` of the view, as a plain dictionary; the
    `layers` opened per graph, the periods and their
    occurrences; `files`, the SHA-256 of each file the trellis reads, by its
    path, as the reading read it, of the text of an unsaved buffer where the
    reading took that text; `changed`, the positions `(h, key)` whose
    occurrence this reading constructed or bound anew against the trellis
    shown before; `counts`, `periods`, `occurrences` and `shown`, the
    occurrences the view holds; `seconds`, the time of the whole reading;
    `number`, the number of the reading that bound the trellis, which a
    trellis drawn again under another restriction keeps (spec 0.4 §3.2;
    J-D22); `buffered`, the revision of each unsaved buffer the reading
    took in its file's place, by the file's resolved path, as the syntactic
    trellis's provenance names the paths taken (spec 0.4 §3.3); `texts`,
    the text of each of those buffers by the same key, which the recipe
    region under the tree reads in the file's place, so that it reads the
    recipe as this reading read it (`recipe.table`; AAS, M-D7); `made`,
    the moment the reading made it (`time.monotonic`), the moment of its
    binding's notes and of its refused graphs in the page's list of
    refusals (AMD-MI-002 §6a rule 1); and `alone`, the keys of the stages
    whose occurrences the reading bound again alone, the other occurrences
    kept from the trellis shown before (`bind_changed_stages`; unit L, Task
    20), in the order of their first positions, empty where the reading
    bound the whole trellis, read its binding from disk or bound
    nothing. `selection` is the package connection result for this exact
    reading, reused by drawings, source links and occurrence details.
    `view_refusal` records a refused drawing of this constructed trellis;
    its collection is empty, while its model and diagnostics remain current."""

    source: recipe.Source
    syntactic: dict
    trellis: dict
    binding: TrellisBinding
    restriction: Restriction | None
    collection: dict
    layers: dict
    files: dict
    changed: list
    counts: dict
    seconds: float
    number: int
    buffered: dict
    texts: dict
    made: float = dataclasses.field(default_factory=time.monotonic)
    alone: tuple = ()
    selection: Selection | None = None
    view_refusal: model.Diagnostic | None = None


class TrellisOutcome(NamedTuple):
    """What one reading of a trellis answered: `shown`, the `TrellisShown`
    the reading answers, the one shown before itself where the reading is
    not repeated and the restriction is unchanged, None where the reading
    was refused; `refusal`, the `model.Diagnostic` of the package's refusal
    to read or elaborate the source; `restricted`, the package's sentence
    where it refused the restriction asked, the trellis then drawn under the
    restriction it accepted last for the source, or whole; `seconds`;
    `files`, the SHA-256 of each file whose change reads the trellis again,
    by its path, taken as the reading read the file, which the page's
    watcher compares (`show_trellis`); `made`, the moment the page
    recorded the outcome (`time.monotonic`), the moment of its refusals in
    the page's list of refusals (AMD-MI-002 §6a rule 1), 0.0 for an
    outcome no page recorded; and `takeable`, the resolved paths, as
    strings, of the files whose unsaved text the package's readers take in
    place of the file, the source, the trellis file and the period files,
    with whose buffers the watcher compares them, every other file being
    compared on disk (spec 0.4 §3.3; ruling J-P2)."""

    shown: TrellisShown | None
    refusal: model.Diagnostic | None
    restricted: str | None
    seconds: float
    files: dict
    made: float = 0.0
    takeable: tuple = ()


def _takeable_files(
    folder: model.Folder, source: recipe.Source, trellis_path, texts=None
) -> list[Path]:
    """The files of the trellis of `source` whose unsaved text the package's
    readers take in place of the file (spec 0.4 §3.1; ruling J-P2), each
    once and resolved: the source; the trellis file `trellis_path`; and each
    period file an entry of that file names under `template`, the entries
    read from the text the mapping `texts` holds for the trellis file, else
    from the file (the brief's review, finding 3). A trellis file that
    cannot be read, or whose `periods` is no list, names no period file."""
    trellis_path = Path(trellis_path)
    paths = [folder.root / source.path, trellis_path]
    try:
        entries = entry_value(recipe._text(folder, trellis_path, texts), "periods")
    except (OSError, ValueError, KeyError):
        entries = []
    paths += [
        trellis_path.parent / str(entry["template"])
        for entry in (entries if isinstance(entries, list) else [])
        if isinstance(entry, dict) and "template" in entry
    ]
    return list(dict.fromkeys(path.resolve() for path in paths))


def files_read(
    folder: model.Folder, source: recipe.Source, syntactic: dict, texts=None
) -> list[Path]:
    """The files the trellis of `source` reads, each once and resolved, which
    the page's watcher compares (specification §3.1: the trellis
    re-elaborates when any file the model reads is saved): the source; the
    trellis file the package's reader read, which the syntactic trellis
    records under `provenance["trellis"]["path"]`, and each period file an
    entry of that file names under `template`, read through the mapping of
    unsaved texts `texts` (`_takeable_files`); each stage file a record
    names; and each binding source file a record names, with the files of
    its parent chain."""
    trellis_path = Path(syntactic["provenance"]["trellis"]["path"])
    paths = _takeable_files(folder, source, trellis_path, texts)
    for period in syntactic["periods"]:
        for record in period["stages"].values():
            paths.append(Path(record["stage"]["origin"]))
            paths += recipe.record_files(record)
    return list(dict.fromkeys(path.resolve() for path in paths))


def files_of_refusal(
    folder: model.Folder,
    source: recipe.Source,
    refusal: model.Diagnostic,
    held=None,
    texts=None,
) -> list[Path]:
    """The files whose change on disk reads a refused trellis again
    (specification §3.1: the trellis re-elaborates when any file the model
    reads is saved), each once and resolved: the source; the trellis file it
    reads, where it names one (`recipe.trellis_file`, given the mapping of
    unsaved texts `texts`); the file the refusal names, where it names one;
    and each file of `held`, the trellis shown before, where it is of the
    same source, since a reading after a correction reads them again."""
    named = (source.path, recipe.trellis_file(folder, source, texts))
    paths = [folder.root / name for name in named if name is not None]
    if refusal.file:
        paths.append(folder.root / refusal.file)
    if held is not None and held.source == source:
        paths += [Path(name) for name in held.files]
    return list(dict.fromkeys(path.resolve() for path in paths))


def files_before_reading(folder: model.Folder, source: recipe.Source, previous=None) -> list[Path]:
    """The files a reading of `source` names before it reads one, each once
    and resolved: the source and, where `previous`, the trellis shown
    before, is of the same source, each file its reading read."""
    paths = [folder.root / source.path]
    if previous is not None and previous.source == source:
        paths += [Path(name) for name in previous.files]
    return list(dict.fromkeys(path.resolve() for path in paths))


def file_digests(paths, texts=None) -> dict[str, str]:
    """The SHA-256 of each file of `paths`, by its path as a string: of the
    UTF-8 bytes of the text the mapping `texts` holds for the file's
    resolved path, where it holds one, and else of the file's bytes (spec
    0.4 §3.3: the effective text); a file that cannot be read is left out,
    so that its removal is a change."""
    found = {}
    for path in paths:
        held = texts.get(str(Path(path).resolve())) if texts else None
        if held is not None:
            found[str(path)] = hashlib.sha256(held.encode("utf-8")).hexdigest()
            continue
        try:
            found[str(path)] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError:
            continue
    return found


def inputs_current(shown: TrellisShown, texts) -> bool:
    """Whether every file the reading `shown` read holds the text it read
    (spec 0.4 §3.3): `file_digests(shown.files, texts)` equals
    `shown.files`, `texts` being the mapping of every unsaved buffer, so
    that the unsaved buffer of a file the reading did not take from a
    buffer, a stage or binding file's among them, makes the inputs not
    current."""
    return file_digests(shown.files, texts) == shown.files


def _as_read(before: dict, paths, texts=None) -> dict[str, str]:
    """The digest of each file of `paths` as a reading read it: the digest
    `before` holds, taken before the package read the file, where it holds
    one, and else the digest the file has now, of the text `texts` holds
    for it where it holds one (`file_digests`); a file that could be read
    neither then nor now is left out."""
    now = file_digests(paths, texts)
    found = {}
    for name in map(str, paths):
        digest = before.get(name, now.get(name))
        if digest is not None:
            found[name] = digest
    return found


def _opened_layers(collection, graph_id: str, periods: int) -> list:
    """The layers the view opens at first: every layer to `TRELLIS_DEPTH`,
    the periods and their occurrences, and in an initial diagram of the
    trellis the occurrences' perches as well (design pass 14 §7), for a
    trellis of at most
    `OPEN_PERIODS_WHOLE` periods; for a longer one, every period's layer and
    the occurrence layers of periods 0 to `OPEN_OCCURRENCES_UP_TO` alone, the
    terminal period and the two before it, the other periods closed until
    a click opens them."""
    # the trellis's initial diagram opens its occurrences' perch layers as
    # well, the fields being its authored surface (design pass 14 §7)
    depth = TRELLIS_DEPTH + 1 if graph_id in INITIAL_IDS.values() else TRELLIS_DEPTH
    opened = list(layers_to_open(collection, graph_id, depth))
    if periods <= OPEN_PERIODS_WHOLE:
        return opened
    kept = []
    for layer in opened:
        head, _, rest = layer.partition("/")
        period = head.startswith("periods[") and head.endswith("]")
        number = int(head[len("periods[") : -1]) if period else None
        if not rest or number is None or number <= OPEN_OCCURRENCES_UP_TO:
            kept.append(layer)
    return kept


def holds_initial_diagrams(shown: TrellisShown) -> bool:
    """Whether the view `shown` holds the trellis's two initial diagrams
    (design pass 14 §7; S-D30)."""
    held = {graph["id"] for graph in shown.collection["graphs"]}
    return all(name in held for name in INITIAL_IDS.values())


def with_initial_diagrams(shown: TrellisShown) -> TrellisShown:
    """The view `shown` with the trellis's two initial diagrams after its
    builders graphs, drawn under the same restriction and selection
    (`to_model_explorer` with `initial`), and the layers each opens
    (`_opened_layers`): computed once the Initial view is chosen in the
    trellis, since the diagrams of a long trellis are large, 22,000 nodes
    for the eighty-five periods of the life-cycle model (design pass 14 §7;
    S-D30). `shown` itself where it holds them already and where its
    drawing was refused."""
    if shown.view_refusal is not None or holds_initial_diagrams(shown):
        return shown
    view = to_model_explorer(
        shown.trellis,
        unjoined=True,
        selection=shown.selection,
        initial=True,
        **_selection(shown.restriction),
    )
    added = [
        graph for graph in dataclasses.asdict(view)["graphs"] if graph["id"] in INITIAL_IDS.values()
    ]
    collection = {**shown.collection, "graphs": [*shown.collection["graphs"], *added]}
    periods = len(shown.trellis["periods"])
    layers = {
        **shown.layers,
        **{graph["id"]: _opened_layers(collection, graph["id"], periods) for graph in added},
    }
    return dataclasses.replace(shown, collection=collection, layers=layers)


def _reading_refusal(
    folder: model.Folder, source: recipe.Source, error: Exception, syntactic: dict | None = None
) -> model.Diagnostic:
    """The `Diagnostic` of the refusal `error` of a reading of `source`
    (`model.refusal_of`). An exception of no class of the package's
    refusals (`model.is_refusal`) is written to the page's log with its
    traceback, and is printed in the file of the text whose reading raised
    it (unit L, Task 21; defect 18 of the UX simulation): where its notes
    name a stage occurrence (`_OCCURRENCE_NOTE`, `_CONSTRUCTION_NOTE`) that
    the syntactic trellis `syntactic` records, that occurrence's stage file,
    at the line of the address its message names in the span table of the
    text the reading constructed, as the loop prints the same exception for
    that text; else the source's file, with no line."""
    if model.is_refusal(error):
        return model.refusal_of(error, source.path)
    path = str((folder.root / source.path).resolve())
    LOG.error(model.EXCEPTION_LOGGED, path, exc_info=error)
    notes = "\n".join(getattr(error, "__notes__", ()))
    named = _OCCURRENCE_NOTE.search(notes) or _CONSTRUCTION_NOTE.search(notes)
    periods = syntactic["periods"] if syntactic is not None else []
    if named is None or int(named[1]) >= len(periods):
        return model.refusal_of(error, source.path, path)
    record = periods[int(named[1])]["stages"].get(named[3])
    if not isinstance(record, dict):
        # a stage object, which the reading did not construct
        return model.refusal_of(error, source.path, path)
    text, origin = record["stage"]["text"], record["stage"]["origin"]
    try:
        spans = source_spans(text, origin)
    except ValueError:
        spans = None
    return model.refusal_of(error, source.path, origin, spans)


def show_trellis(
    folder: model.Folder,
    source: recipe.Source,
    restriction=None,
    previous=None,
    unsaved=None,
    initial: bool = False,
) -> TrellisOutcome:
    """One reading of the trellis of `source` (specification §3.1): the
    syntactic trellis read by the package, its view drawn with the trellis's
    two initial diagrams where `initial` asks for them, as the page asks
    while its Initial view is shown (design pass 14 §7; S-D30;
    `with_initial_diagrams`); `bind_trellis` with the trellis
    `previous` shows where it is of the same source, so that a changed
    stage text alone is constructed again, once in each call of
    `specify_trellis`, and every occurrence of it replaced; the view of the
    bound trellis restricted by `restriction` and the
    layers it opens, the periods and their occurrences; the files the
    trellis reads with their digests; and the positions constructed or
    bound anew. Where a verb that bound `previous` is skipped or refused in
    this reading, the trellis is bound again without `previous`, whose
    occurrences taken as they stand would keep that verb's bindings, so that
    a reading with `previous` answers the trellis a reading without it
    answers.

    Where `previous` is of the same source and every file that changed
    since it was read is a stage file or a binding source file, none of the
    files whose buffers the reading of `previous` could take (the source,
    the trellis file and the period files), the occurrences whose record
    changed are bound again alone and the others kept as `previous` holds
    them (`bind_changed_stages`; unit L, Task 20; defect 14 of the UX
    simulation): a change of one stage's text, values, methods or settings
    binds that stage's occurrences alone, and the trellis shown records
    their keys under `alone`. Where `bind_changed_stages` answers None, and
    where the source, the trellis file or a period file changed, the
    trellis is bound whole as stated above.

    Where `previous` is of the same source and each file it read has the
    digest it had then, the reading, the elaboration and the binding are not
    repeated: the trellis `previous` holds is drawn under the restriction
    asked, with no position changed, and where that restriction is the one
    `previous` was drawn under, `previous` itself is answered.

    Where `previous` is not of the same source, the binding is read from
    the entry in which a reading of the same syntactic trellis by the same
    code kept it on disk (`read_binding`), and `bind_trellis` is called
    only where no entry can be read; the caller keeps the binding of such a
    reading once it holds the outcome (`keep_binding`).

    The digests are those of the files as the reading read them: each file
    `files_before_reading` names is digested before the package reads it,
    and every other file the syntactic trellis names just after the
    reading, before the elaboration and the binding, which read no file; so
    a file saved after its digest was taken differs from it, and the watcher
    reads the trellis again. A file of the second kind saved between the
    package's read and the digest taken just after it is recorded with its
    new digest, and the trellis stays as read until the next save of a file
    it reads. A refusal of the reading answers the refusal and the digests
    of the files `files_of_refusal` names; a refusal of the elaboration,
    those of the files the reading read and of the file the refusal names;
    neither answers a trellis. Each such refusal is `_reading_refusal`'s. A
    restriction the package refuses answers its sentence, and the view is
    drawn under the restriction `previous` was drawn under, the one the
    package accepted last for the source, or else whole.

    `unsaved` maps the resolved path of each unsaved buffer of the tab to
    its `Unsaved`, the text and the revision (spec 0.4 §3.1, §3.3). The
    package's readers take the text of the source, of the trellis file and
    of a period file in place of the file; a stage file or a binding source
    file is read from disk. Each digest is that of the text used: of a
    buffer the syntactic trellis's provenance names under `texts` as taken,
    and of the file otherwise, so that the record never names a buffer the
    package did not read; the digests taken before the reading compare the
    buffers of the files `previous` could take (`_takeable_files`). The
    trellis shown records the revision of each buffer taken, `buffered`, its
    text, `texts`, and the number of the reading that bound it, `number`,
    which a trellis drawn
    again under another restriction keeps (J-D22). Every view is made with
    the keyword `unjoined`, which marks the state fields no join reaches in
    the forward graph (spec 0.4 §3.4)."""
    started = time.perf_counter()
    texts = texts_of(unsaved)
    same = previous if previous is not None and previous.source == source else None
    held = same.trellis if same is not None else None
    # the files whose buffers the reading of `previous` could take, the
    # source alone with no such reading
    takeable = (
        _takeable_files(folder, source, same.syntactic["provenance"]["trellis"]["path"], texts)
        if same is not None
        else [(folder.root / source.path).resolve()]
    )
    before = file_digests(files_before_reading(folder, source, same), _within(texts, takeable))
    # whether every file that changed since the reading of `previous` is a
    # stage file or a binding source file, none of those its buffers could
    # give, the source, the trellis file and the period files
    read_then = same.files if same is not None else {}
    moved = {name for name, digest in read_then.items() if before.get(name) != digest}
    sources_alone = same is not None and not moved & set(_names(takeable))
    number, alone = None, ()
    if same is not None and before == same.files:
        # no file the reading of `previous` read holds another text since
        if restriction == same.restriction:
            seconds = time.perf_counter() - started
            return TrellisOutcome(same, None, None, seconds, same.files, takeable=_names(takeable))
        syntactic, binding, files, changed = same.syntactic, same.binding, same.files, []
        number, buffered, used = same.number, same.buffered, same.texts
    else:
        try:
            syntactic = recipe.read_source(folder, source, texts)
        except _REFUSALS as error:
            refusal = _reading_refusal(folder, source, error)
            named = recipe.trellis_file(folder, source, texts)
            if named is not None:
                takeable = _takeable_files(folder, source, folder.root / named, texts)
            files = _as_read(
                before,
                files_of_refusal(folder, source, refusal, same, texts),
                _within(texts, takeable),
            )
            seconds = time.perf_counter() - started
            return TrellisOutcome(None, refusal, None, seconds, files, takeable=_names(takeable))
        # the texts the package's readers took in their files' places
        used = {name: texts[name] for name in syntactic["provenance"].get("texts", [])}
        buffered = {name: unsaved[name].revision for name in used}
        takeable = _takeable_files(
            folder, source, syntactic["provenance"]["trellis"]["path"], texts
        )
        files = _as_read(before, files_read(folder, source, syntactic, texts), used)
        try:
            # a change of stage or binding source files alone: the
            # occurrences whose record changed are bound again alone
            binding = (
                bind_changed_stages(same.binding, same.syntactic, syntactic)
                if sources_alone
                else None
            )
            bound_alone = binding is not None
            if binding is None:
                # with no trellis of the same source, the binding an earlier
                # reading of the same syntactic trellis kept on disk
                binding = read_binding(syntactic) if held is None else None
            if binding is None:
                binding = bind_trellis(held, syntactic)
            if held is not None and not set(same.binding.bound) <= set(binding.bound):
                # the occurrences taken from `previous` keep the bindings of a
                # verb this reading skips or refuses
                binding = bind_trellis(None, syntactic)
        except _REFUSALS as error:
            refusal = _reading_refusal(folder, source, error, syntactic)
            if refusal.file:
                named = [(folder.root / refusal.file).resolve()]
                files = {**file_digests(named, used), **files}
            seconds = time.perf_counter() - started
            return TrellisOutcome(None, refusal, None, seconds, files, takeable=_names(takeable))
        changed = changed_positions(held, binding.trellis) if held is not None else []
        if bound_alone:
            alone = tuple(dict.fromkeys(key for _, key in changed))
    selected = same.selection if number is not None else trellis_selection(binding.trellis)
    # the restriction asked, then the one the package accepted last for the
    # source, then the whole trellis
    accepted = same.restriction if same is not None else None
    tried = [None] if restriction is None else list(dict.fromkeys((restriction, accepted, None)))
    sentence, view_refusal = None, None
    for drawn in tried:
        try:
            view = to_model_explorer(
                binding.trellis, unjoined=True, selection=selected, initial=initial, **_selection(drawn)
            )
        except FactoryError as error:
            if drawn is None:
                # The model was constructed, but this reading has no drawable graph.
                view_refusal = model.refusal_of(error, source.path)
                break
            if drawn is restriction:
                sentence = error.message
            continue
        break
    collection = {"graphs": []} if view_refusal is not None else dataclasses.asdict(view)
    positions = [
        (h, key) for h, period in enumerate(binding.trellis["periods"]) for key in period["stages"]
    ]
    shown = TrellisShown(
        source=source,
        syntactic=syntactic,
        trellis=binding.trellis,
        binding=binding,
        restriction=drawn,
        collection=collection,
        layers={
            graph["id"]: _opened_layers(collection, graph["id"], len(binding.trellis["periods"]))
            for graph in collection["graphs"]
        },
        files=files,
        changed=changed,
        counts={
            "periods": len(binding.trellis["periods"]),
            "occurrences": len(positions),
            "shown": sum(1 for h, key in positions if selects(drawn, h, key)),
        },
        seconds=time.perf_counter() - started,
        number=next(_readings) if number is None else number,
        buffered=buffered,
        texts=used,
        alone=alone,
        selection=selected,
        view_refusal=view_refusal,
    )
    return TrellisOutcome(shown, None, sentence, shown.seconds, files, takeable=_names(takeable))


def _names(paths) -> tuple[str, ...]:
    """The paths `paths`, each as a string, in their order."""
    return tuple(map(str, paths))


def address_place(
    folder: model.Folder, file, address, expanded: bool = True, texts=None
) -> tuple[str, int] | None:
    """The file, relative to the folder, and the line at which a structural
    address of a model's file stands, so that the editor opens the file
    there (specification §2.2 rule 2; D11): an address of the expanded
    trellis, `expanded`, moved to the file that writes it (`written_at`),
    then the line of its entry (`entry_span`). Both read the text the
    mapping of unsaved texts `texts` holds for a file, where it holds one,
    so that the line is counted in the buffer's text (spec 0.4 §3.1). A
    refusal under `SHAPE_RULE` names the trellis file's own entries and is
    given with `expanded` false. None where no file or no address is given,
    where the file writes no such entry, and where it is of a shape the
    factory refuses, on which `written_at` raises a TypeError or an
    AttributeError, as the recipe under the tree reads such a file
    (`recipe.table`)."""
    if not file or address is None:
        return None
    try:
        place = written_at(file, address, texts) if expanded else (str(file), address)
        span = entry_span(recipe._text(folder, place[0], texts), place[1])
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return recipe.relative(folder, place[0]), span.line


# --- the panel of a node of the trellis view ---


class Subject(NamedTuple):
    """What the panel of the trellis view shows for a node (specification
    §2.4 and §3.1): `kind`, `period`, `occurrence`, `piece` for a box or a
    builder of an occurrence, `inputs` or `outputs` for a boundary node of
    the trellis or an occurrence's own node, or `refusal`; `node_id` and
    `graph`; `occurrence`, the occurrence's address, `periods[1]/cons`, or
    the period's, `periods[1]`; `position`, `(h, key)` of the occurrence;
    `rows`, the attributes of the layer or the node as the exporter writes
    them; `ports`, the rows of the ports (`port_rows`); `piece`, the
    occurrence's `model.Piece` of the node; and `occurrences`, the
    occurrences of a period the view holds, in the view's order, each
    `(address, position)`."""

    kind: str
    node_id: str
    graph: str
    occurrence: str
    position: tuple | None
    rows: dict
    ports: dict
    piece: object
    occurrences: tuple


def port_rows(collection: dict, graph: str, node_id: str) -> dict:
    """The rows of the ports of a node of a trellis view, `{"inputs": [...],
    "outputs": [...]}`, each row the attributes `PORT_KEYS`, the empty text
    for one the exporter did not write (`model._port_rows`)."""
    node = model._node(collection, graph, node_id)
    return {
        "inputs": model._port_rows(node.get("inputsMetadata") or [], PORT_KEYS),
        "outputs": model._port_rows(node.get("outputsMetadata") or [], PORT_KEYS),
    }


def _place(collection: dict, graph: str, node_id: str) -> tuple[str, str]:
    """The occurrence and the block of a node of the trellis view: the
    package's `node_place`."""
    return tuple(node_place(collection, graph, node_id))


def occurrence_positions(shown: TrellisShown) -> dict:
    """The position `(h, key)` of each stage occurrence of the trellis
    `shown` holds, by the occurrence's address, `periods[1]/cons`, which is
    the occurrence `node_place` answers for a node of the trellis view."""
    return {
        f"periods[{h}]/{key}": (h, key)
        for h, period in enumerate(shown.trellis["periods"])
        for key in period["stages"]
    }


def listed_periods(shown: TrellisShown) -> dict:
    """The periods each stage key is listed in, in the whole trellis `shown`
    holds whatever its view draws, by key, read from the positions of its
    occurrences (`occurrence_positions`) and written as ranges (`_runs`):
    `0–50`, `0` for a stage of the terminal period alone, `17, 36` for one
    that stands in two periods apart (AAS, L-D10). A key no period lists is
    not held."""
    held = {}
    for h, key in occurrence_positions(shown).values():
        held.setdefault(key, []).append(h)
    return {key: _runs(sorted(periods)) for key, periods in held.items()}


def view_periods(shown: TrellisShown) -> list[int]:
    """The periods the view of `shown` draws, from the terminal one: each
    period of the trellis that holds an occurrence the view's restriction
    selects (`selects`), every period where the view is not restricted
    (AAS, L-D11)."""
    return [
        h
        for h, period in enumerate(shown.trellis["periods"])
        if any(selects(shown.restriction, h, key) for key in period["stages"])
    ]


# The words of the policy builder's box in the trellis view, its pair and
# its hover (AAS, L-D7).
POLICY_WORD = "policy"
# The layer of a builder of a stage occurrence in a graph of the trellis
# view, `periods[1]/cons/dcsn_to_cntn`: its period's index, its key and the
# builder's name.
_BUILDER_LAYER = re.compile(r"periods\[(\d+)\]/([^/]+)/([^/]+)")


def stage_order(shown: TrellisShown) -> list[str]:
    """The stage keys of the trellis `shown` holds, in the order the
    recipe's `stages:` list writes them as the trellis's periods hold them:
    each key at its first position in the periods, from the terminal period,
    `periods[0]`, each period holding its stages in its file's order, which
    for the durables model is `tenure`, `keeper_cons`, `adjuster_cons`,
    `bequest`, the Recipe tab's rows. The graph region stands every period's
    occurrences in rows by this order in both graphs, and a card's plugs in
    the order of the cards they reach (the fix wave Q3a of unit Q, item 2,
    which amends K-D12)."""
    order = []
    for period in shown.trellis["periods"]:
        for key in period["stages"]:
            if key not in order:
                order.append(key)
    return order


def builder_records(shown: TrellisShown) -> dict:
    """The record of each builder of each stage occurrence the view `shown`
    draws, in either graph, by the namespace of its layer,
    `periods[1]/cons/dcsn_to_cntn`, which the graph region draws as a box
    coded by the pair of perches its signature joins (spec 0.4 §5.3, as
    AAS's ruling L-D7 amends it): `pair`, the pair as `dcsn,cntn`, or
    `policy` for the policy builder; `place`, the pair's place in the order
    of its direction, 0 for `arvl,dcsn` and `cntn,dcsn`, 1 for `dcsn,cntn`
    and `dcsn,arvl`, None for the policy builder; `signs`, the pair's perch
    signs, `∼≻`, empty for the policy builder; and `words`, the pair in
    words, `decision to continuation`, or `policy`. The pair is the
    package's (`builder_pairs`), read from the stage's wire table and never
    from the block id, so that a builder its author names `solve` keeps the
    pair it joins; the occurrences of one stage version share one
    reading."""
    pairs_of = {}
    found = {}
    for graph in shown.collection["graphs"]:
        for namespace in graph.get("groupNodeAttributes") or {}:
            match = _BUILDER_LAYER.fullmatch(namespace)
            if match is None or namespace in found:
                continue
            h, key, name = int(match[1]), match[2], match[3]
            stage = shown.trellis["periods"][h]["stages"].get(key)
            if stage is None:
                continue
            if id(stage) not in pairs_of:
                pairs, policies, _ = builder_pairs(stage)
                named = {
                    piece_named(box, None): pair for pair, held in pairs.items() for box in held
                }
                named.update({piece_named(box, None): POLICY_WORD for box in policies})
                pairs_of[id(stage)] = named
            pair = pairs_of[id(stage)].get(name)
            if pair is None:
                continue
            if pair == POLICY_WORD:
                found[namespace] = {
                    "pair": POLICY_WORD,
                    "place": None,
                    "signs": "",
                    "words": POLICY_WORD,
                }
                continue
            order = FORWARD_PAIRS if pair in FORWARD_PAIRS else BACKWARD_PAIRS
            found[namespace] = {
                "pair": ",".join(map(str, pair)),
                "place": order.index(pair) if pair in order else None,
                "signs": "".join(PERCH_SIGN.get(perch, "") for perch in pair),
                "words": " to ".join(PERCH_WORD.get(perch, str(perch)) for perch in pair),
            }
    return found


def _boundary_of(collection: dict, graph: str, node_id: str) -> dict | None:
    """The node `node_id` of the graph `graph` of a trellis view where it is
    one of the trellis's boundary nodes, which stand at the graph's root
    with an attribute `kind` among the package's `BOUNDARY_KINDS` (design
    pass 10 §6; unit N, Task 6); None for any other node, and for a graph
    or a node the view does not hold."""
    for entry in collection["graphs"]:
        if entry["id"] != graph:
            continue
        for node in entry["nodes"]:
            if node["id"] == node_id:
                kind = next(
                    (pair["value"] for pair in node.get("attrs") or [] if pair["key"] == "kind"),
                    None,
                )
                held = not node.get("namespace") and kind in BOUNDARY_KINDS
                return node if held else None
    return None


def describe_node(shown: TrellisShown, graph: str, node_id: str, stage_views: dict) -> Subject:
    """The `Subject` of the node `node_id` of the graph `graph` of the
    trellis view: the refusing node with its rows; a boundary node of the
    trellis (`_boundary_of`; design pass 10 §6), with its attributes and
    its ports, the one wire of a `start` or an `end` node and every wire of
    an `outside` node (design pass 12 §2), as `inputs` where its wires
    enter the graph and as `outputs` where they leave; a period's layer
    with its rows and the occurrences of it the view holds, in the order the view's
    layers list them, the forward order the exporter computes from the
    joins; an occurrence's layer with its rows; an occurrence's own
    `Inputs` or `Outputs` with their ports; and a box or a builder of an
    occurrence as the piece of the occurrence's own stage view
    (`model.piece`), a box's ports read from the trellis view, so that its
    joins and their pairing rules are listed. `stage_views` is the page's
    dictionary of each occurrence's stage view by its address, filled on
    first use (`model.collection`). A node the view does not hold is
    refused with a KeyError naming it, among them a node of a period or an
    occurrence whose layer the view does not hold: one a restriction leaves
    out, and every layer of a refused graph, which holds none."""
    collection = shown.collection
    if node_id == f"{graph}:refused":
        rows = model.node_attributes(collection, graph, node_id)
        return Subject("refusal", node_id, graph, "", None, rows, {}, None, ())
    boundary = _boundary_of(collection, graph, node_id)
    if boundary is not None:
        kind = "inputs" if boundary.get("outputsMetadata") else "outputs"
        rows = model.node_attributes(collection, graph, node_id)
        ports = port_rows(collection, graph, node_id)
        return Subject(kind, node_id, graph, "", None, rows, ports, None, ())
    positions = occurrence_positions(shown)
    found = next((entry for entry in collection["graphs"] if entry["id"] == graph), None)
    if found is None:
        # a graph of a stage's view, which the trellis view does not hold
        raise KeyError(f"the view holds no graph named {graph!r}")
    # the layers the view holds, by namespace, in the order the exporter
    # writes them; a refused graph holds none
    layers = found.get("groupNodeAttributes") or {}
    occurrence, _ = _place(collection, graph, node_id)
    if occurrence not in layers:
        raise KeyError(f"the trellis view holds no node {node_id!r}")
    if occurrence not in positions:
        # a period's layer, whose occurrences are those of the view's layers
        # that are occurrences of the period, in the view's order
        held = tuple(
            (address, positions[address])
            for address in layers
            if address in positions and address.startswith(f"{occurrence}/")
        )
        rows = dict(layers[occurrence])
        return Subject("period", node_id, graph, occurrence, None, rows, {}, None, held)
    position = positions[occurrence]
    if node_id == occurrence + LAYER_ID_ENDING:
        rows = dict(layers[occurrence])
        return Subject("occurrence", node_id, graph, occurrence, position, rows, {}, None, ())
    inner = node_id[len(occurrence) + 1 :]
    if inner in BOUNDARY_IDS:
        kind = "inputs" if inner == BOUNDARY_IDS[0] else "outputs"
        ports = port_rows(collection, graph, node_id)
        return Subject(kind, node_id, graph, occurrence, position, {}, ports, None, ())
    h, key = position
    stage = shown.trellis["periods"][h]["stages"][key]
    if occurrence not in stage_views:
        stage_views[occurrence] = model.collection(stage)
    piece = model.piece(stage, graph, inner, stage_views[occurrence])
    if piece.kind == "box":
        piece = piece._replace(ports=port_rows(collection, graph, node_id))
    return Subject("piece", node_id, graph, occurrence, position, {}, {}, piece, ())


def block_line(stage_view: dict, block: str) -> int | None:
    """The line of the header of `block` in an occurrence's stage file, from
    the `lines` row of the block's node in the initial diagram that holds it
    (`model.header_line_of`); None where neither diagram holds it."""
    for graph_id in INITIAL_IDS.values():
        try:
            return model.header_line_of(model.node_attributes(stage_view, graph_id, block))
        except KeyError:
            continue
    return None


def occurrence_file(folder: model.Folder, shown: TrellisShown, position) -> str:
    """The stage file of the occurrence at `position`, `(h, key)`, relative
    to the folder: the origin its record writes."""
    h, key = position
    origin = shown.syntactic["periods"][h]["stages"][key]["stage"]["origin"]
    return recipe.relative(folder, origin)


def field_places(folder: model.Folder, shown: TrellisShown, uses, texts=None) -> dict:
    """Source declarations of native field uses, read once per stage file.

    The existing text reader locates each current header or branch listing.
    No classification table, stage or graph is constructed.
    """
    read, found = {}, {}
    for use in uses:
        path = occurrence_file(folder, shown, (use.h, use.key))
        if path not in read:
            text = recipe._text(folder, path, texts)
            try:
                listings = model._listed_in_text(source_spans(text, path), text.split("\n"))
                read[path] = {}
                for listing in listings:
                    read[path].setdefault((listing.placed or listing.side, listing.stem),
                                          listing.listing.at.line)
            except (ValueError, KeyError, TypeError):
                read[path] = {}
        found[use] = path, read[path].get((use.perch, use.field), 1)
    return found


class Link(NamedTuple):
    """A link of the panel to a line of a file of the model: `text`, what it
    reads; `path`, the file, relative to the folder; and `line`."""

    text: str
    path: str
    line: int


# --- Details for a selected stage occurrence (design pass §2; unit K) ---


class Use(NamedTuple):
    """One recipe of the rows `periods` and `also` of Details (design pass
    §2; K-D2): `text`, the periods at which the recipe holds the stage file,
    as ranges, `0–4, 7–50`, after the recipe's path in `also`; `source`, the
    recipe; and `position`, `(h, key)`, the occurrence at which its link
    shows the recipe's trellis (`show_occurrence` of the page)."""

    text: str
    source: recipe.Source
    position: tuple


class Line(NamedTuple):
    """One line of a row of Details (design pass §2): `head`, the words
    printed before its parts, a stage occurrence's name or a perch's sign,
    the empty text where none; and `parts`, each a text, a `Link` or a
    `Use`, printed in order with ` · ` between two of them (`line_text`)."""

    head: str
    parts: tuple


class Cells(NamedTuple):
    """One line of a table in a row of Details (design pass §2, "A join
    wire"): `cells`, the texts of its cells, in order."""

    cells: tuple


class OccurrenceRows(NamedTuple):
    """Details of a selected stage occurrence (design pass §2, "A stage
    occurrence"; K-D2): `key`, the stage's key; `place`, its period and the
    period's age where the exporter writes one, `periods[1] · age 69`; and
    `rows`, each `(label, lines)`, a label of §2's vocabulary and a tuple
    of `Line`."""

    key: str
    place: str
    rows: tuple


class JoinRows(NamedTuple):
    """Details of a selected join wire (design pass §2, "A join wire";
    K-D2): `place`, its writing and its reading stage occurrence by their
    addresses, `periods[1]/adjuster_cons → periods[0]/tenure`; `rows`,
    each `(label, lines)` as in `OccurrenceRows`, the lines of `fields`
    each a `Cells`; `names`, the arrival fields of its joins by equal
    names, which `rename` offers (unit L, Task 15); and `removable`,
    whether an entry of a file writes a join of it, which `remove` takes
    out."""

    place: str
    rows: tuple
    names: tuple = ()
    removable: bool = True


def line_text(line: Line | Cells) -> str:
    """The text of one line of Details as the page prints it: the head, a
    space, and the parts' texts with ` · ` between two of them; a line of a
    table, its cells with a space between two of them."""
    if isinstance(line, Cells):
        return " ".join(line.cells)
    parts = " · ".join(part if isinstance(part, str) else part.text for part in line.parts)
    return f"{line.head} {parts}" if line.head else parts


def use_rows(uses, own, position) -> list:
    """The rows `periods` and `also` of Details (design pass §2; K-D2), for
    the stage file whose positions in each recipe `uses` lists, `[(source,
    positions)]` as `recipe.uses_of` answers them: `periods`, the periods
    at which the recipe `own`, the tab's, holds the file, as ranges
    (`_runs`); `also`, one line for each other recipe that holds it, its
    path and its periods. Each is one `Use`, whose link shows the recipe's
    trellis at `position`, `(h, key)`, where the recipe holds it, and at
    the recipe's first position otherwise. A recipe that holds no position
    has no line, and a row with no line is left out."""
    rows, others = [], []
    for source, held in uses:
        if not held:
            continue
        target = position if position in held else held[0]
        periods = _runs(sorted({h for h, _ in held}))
        if source == own:
            rows.append(("periods", (Line("", (Use(periods, source, target),)),)))
        else:
            others.append(Line("", (Use(f"{source.path} · periods {periods}", source, target),)))
    if others:
        rows.append(("also", tuple(others)))
    return rows


def _occurrence_joins(shown: TrellisShown, position) -> list[tuple]:
    """The selected field pairs reaching one stage occurrence, each
    `(writer, field, reader, arrival)`, from this reading's selection."""
    return [
        ((p.writing.h, p.writing.key), p.writing.field,
         (p.reading.h, p.reading.key), p.reading.field)
        for p in shown.selection.pairs
        if position in ((p.writing.h, p.writing.key), (p.reading.h, p.reading.key))
    ]


def _join_lines(shown: TrellisShown, position, joins: list, side: int) -> tuple:
    """The lines of the row `from` (`side` 0, the joins' writers) or `to`
    (`side` 2, their readers) of the occurrence at `position`: one line for
    each other occurrence, in the order of its first join, headed by its
    key where it stands in the same period and by its address otherwise,
    then, where every continuation field it joins stands in one branch of
    the writer (`branches`), that branch's label; its parts are the joins,
    each the field where both ends have one name and `field → arrival`
    otherwise."""
    h = position[0]
    groups = {}
    for join in joins:
        groups.setdefault(join[side], []).append(join)
    lines = []
    for (other, key), held in groups.items():
        name = key if other == h else f"periods[{other}]/{key}"
        (hw, kw) = held[0][0]
        writer = shown.trellis["periods"][hw]["stages"][kw]
        identities = {i.field: str(i) for i in writer.fields() if i.perch == cntn}
        labels = {str(i): label for label, found in branches(writer).items() for i in found}
        held_labels = {labels.get(identities.get(field)) for _, field, _, _ in held}
        if len(held_labels) == 1 and None not in held_labels:
            name = f"{name} ({held_labels.pop()})"
        parts = tuple(
            field if field == arrival else f"{field} → {arrival}" for _, field, _, arrival in held
        )
        lines.append(Line(name, parts))
    return tuple(lines)


def _field_lines(stage) -> tuple:
    """The lines of the row `fields`: one for each perch that holds a field
    the BellmanType panel's Fields tab lists (`model.TABLE_PERCHES`,
    `model.ROLE_CLASS`), headed by the perch's sign (`PERCH_SIGN`), each
    field in the order `stage.fields()` lists them, with its declared set
    and, unless it is a state, its role's mark (`model.role_word`)."""
    by_perch = {perch: [] for perch in model.TABLE_PERCHES}
    for identity, sort in stage.fields().items():
        if sort.perch not in by_perch or sort.role not in model.ROLE_CLASS:
            continue
        words = [identity.field]
        if sort.domain is not None:
            words.append(to_source(sort.domain))
        if model.ROLE_CLASS[sort.role] != "state":
            words.append(model.role_word(sort.role))
        by_perch[sort.perch].append(" ".join(words))
    return tuple(
        Line(PERCH_SIGN[perch], tuple(fields)) for perch, fields in by_perch.items() if fields
    )


def _tuple_lines(stage) -> list[tuple]:
    """The rows `inputs`, `outputs` and `policies` of Details of a stage
    occurrence (design pass 10 §8): `inputs`, one line of the arrival state
    fields, each with its declared set, `a ℝ₊`; `outputs`, one line per
    branch of the continuation state fields, headed by the branch's label
    where the stage branches (`branches`); and `policies`, one line of the
    controls, each with its set. A row with no field is left out."""
    found = []
    try:
        labels = {str(i): label for label, held in branches(stage).items() for i in held}
    except _REFUSALS:
        labels = {}

    def words(identity, sort):
        return " ".join([identity.field] + ([to_source(sort.domain)] if sort.domain is not None else []))

    arrivals, controls, outputs = [], [], {}
    for identity, sort in stage.fields().items():
        if sort.role not in model.ROLE_CLASS:
            continue
        if model.ROLE_CLASS[sort.role] == "control":
            controls.append(words(identity, sort))
        elif model.ROLE_CLASS[sort.role] == "state" and identity.perch == arvl:
            arrivals.append(words(identity, sort))
        elif model.ROLE_CLASS[sort.role] == "state" and identity.perch == cntn:
            outputs.setdefault(labels.get(str(identity), ""), []).append(words(identity, sort))
    if arrivals:
        found.append(("inputs", (Line("", tuple(arrivals)),)))
    if outputs:
        found.append(("outputs", tuple(Line(label, tuple(fields)) for label, fields in outputs.items())))
    if controls:
        found.append(("policies", (Line("", tuple(controls)),)))
    return found


def occurrence_rows(
    folder: model.Folder,
    shown: TrellisShown,
    graph: str,
    position,
    sources=(),
    refusal: model.Diagnostic | None = None,
    texts=None,
) -> OccurrenceRows:
    """Details of the stage occurrence at `position`, `(h, key)`, selected
    in the graph `graph` of the trellis view `shown` (design pass §2, "A
    stage occurrence"; K-D2), each row read from a record of the package:
    `file`, its stage file (`occurrence_file`), a link to its first line;
    `refused`, while `refusal`, the refusal of the trellis's last reading,
    names that file, its line, its column and its rule, a link to its line;
    `bound`, the words after the stage's name in the label the exporter
    writes on the occurrence's layer, the bindings the version holds;
    `periods` and `also`, the periods at which the recipe shown and each
    other recipe of `sources` hold the stage file (`use_rows`), read
    through the mapping of unsaved texts `texts`; `from` and `to`, the
    joins into and out of it (`_occurrence_joins`); `fields`, the stage's
    fields by perch (`_field_lines`); `inputs`, the arrival state fields
    with their sets, `outputs`, the continuation state fields by branch,
    each branch's label the head of its line, and `policies`, the
    controls, what the occurrence's own `Inputs` and `Outputs` held
    (`_tuple_lines`; design pass 10 §8); `methods`, each method the version
    binds, its tag, or its handler where it has none, and its target
    (`stage.methods`); and `sources`, the binding source files its record
    names (`recipe.record_files`), relative to the folder, one a line. A
    row with nothing to print is left out, `fields` alone excepted. The
    head's place reads the age the exporter writes on the period's
    layer."""
    h, key = position
    address = f"periods[{h}]/{key}"
    layers = next(
        (
            found.get("groupNodeAttributes") or {}
            for found in shown.collection["graphs"]
            if found["id"] == graph
        ),
        {},
    )
    age = (layers.get(f"periods[{h}]") or {}).get("age")
    place = f"periods[{h}] · age {age}" if age else f"periods[{h}]"
    stage = shown.trellis["periods"][h]["stages"][key]
    record = shown.syntactic["periods"][h]["stages"][key]
    path = occurrence_file(folder, shown, position)
    rows = [("file", (Line("", (Link(path, path, 1),)),))]
    origin = Path(record["stage"]["origin"]).resolve()
    if refusal is not None and refusal.file and Path(refusal.file).resolve() == origin:
        where = path
        if refusal.line is not None:
            column = f":{refusal.column}" if refusal.column is not None else ""
            where = f"{path} {refusal.line}{column}"
        text = f"{where} · {refusal.rule}" if refusal.rule else where
        part = text if refusal.line is None else Link(text, path, refusal.line)
        rows.append(("refused", (Line("", (part,)),)))
    # the label is the stage's name followed by a word for each binding
    bound = (layers.get(address) or {}).get("stage", "").split()[1:]
    if bound:
        rows.append(("bound", (Line("", tuple(bound)),)))
    others = [source for source in sources if source != shown.source]
    uses = [(shown.source, tuple(recipe.positions_of(shown.syntactic, origin)))]
    rows += use_rows(uses + recipe.uses_of(folder, others, path, texts), shown.source, position)
    joins = _occurrence_joins(shown, position)
    for label, side in (("from", 0), ("to", 2)):
        reaching = [join for join in joins if join[2 - side] == position]
        if reaching:
            rows.append((label, _join_lines(shown, position, reaching, side)))
    rows.append(("fields", _field_lines(stage)))
    for label, lines in _tuple_lines(stage):
        rows.append((label, lines))
    methods = tuple(
        f"{f'!{method.tag}' if method.tag else method.handler} {target}"
        for target, method in stage.methods.items()
    )
    if methods:
        rows.append(("methods", (Line("", methods),)))
    files = dict.fromkeys(recipe.relative(folder, file) for file in recipe.record_files(record))
    if files:
        rows.append(("sources", tuple(Line("", (file,)) for file in files)))
    return OccurrenceRows(key, place, tuple(rows))


# --- Details for a selected join wire (design pass §2; unit K, Task 4) ---


def _set_texts(stage, perch: str) -> dict:
    """The declared set of each field of `stage` at the perch `perch`, as
    the stage file writes it (`to_source`), by the field's name; the empty
    text for a field declared with none."""
    return {
        identity.field: to_source(sort.domain) if sort.domain is not None else ""
        for identity, sort in stage.fields().items()
        if identity.perch == perch
    }


def _pair_runs(pairs: list) -> str:
    """The periods of the adjacent pairs `pairs`, in order, each pair `p`
    joining `periods[p + 1]` to `periods[p]`: each run of consecutive pairs
    written as the range of the periods it joins, `2–3` for the pair 2
    alone, `0–3, 5–6` for the pairs 0 to 2 and 5."""
    runs = []
    for p in pairs:
        if runs and p == runs[-1][1] + 1:
            runs[-1][1] = p
        else:
            runs.append([p, p])
    return ", ".join(f"{first}–{last + 1}" for first, last in runs)


# the words of the row `written` of Details for the joins of a wire that
# equal names make and no entry writes (unit L, Task 15)
BY_THE_NAMES = "joined by the names"


def join_rows(folder: model.Folder, shown: TrellisShown, wire: dict, texts=None) -> JoinRows:
    """Details of the join wire `wire` of the forward graph the view `shown`
    holds, as `join_wires` answers it (design pass §2, "A join wire"; K-D2;
    unit J's decisions J-D33 and J-D42), each row read from a record of the
    package or of the file that writes the join, through the mapping of
    unsaved texts `texts`:

    - `route`, the cable's route in the words of design pass 10 §8: its
      branch, `branch keep`, where it has one, and its two occurrences with
      the perches' signs, `periods[2]/tenure ≻ → periods[2]/keeper_cons ≺`,
      one line per route for the piece of a pair of periods;
    - `status`, the route's status in the package's words, `certified`, or
      `not certified` followed by the obligations that withhold the
      certificate;
    - `wires`, one line per pair of the route in the route's order, the
      wire, `w_kp → w_kp`, then the declared set, the continuation field's
      followed by `→` and the arrival field's where the two differ, and its
      origin, `inferred`, or `authored, trellis.yml 14` as a link to the
      entry's line (`address_place`);
    - `written`, each entry of a file that writes a join of the wire
      (`_pair_entries`), its file relative to the folder and its address, a
      link to its line (`address_place`); then, where joins of the wire are
      made by equal names (`_name_joins`), the line `joined by the names`,
      followed by those joins' arrival fields where an entry writes the
      wire's other joins (unit L, Task 15);
    - for a wire between two periods, `pairs`, the adjacent pairs of periods
      whose inter-period mapping stands where that of the wire's pair
      stands, `every adjacent pair (50)` where every pair of the trellis is
      one, else their number of all and the periods they join (`_pair_runs`);
      for a wire within a period, `periods`, the periods whose connectors
      list stands where that of the wire's period stands, as ranges;
    - `measure`, the label of the writing port and, after `→`, that of the
      reading port (`_port_label`), the continuation and the arrival
      measure as the exporter writes them, `μ≻` and `μ≺`, with no fields
      (AAS, M-D1);
    - `fields`, a table of the joins from the writing to the reading
      occurrence the package answers (`_occurrence_joins`), one line each:
      the join, `field → arrival`, or the field alone where both ends have
      one name; the declared set, the continuation field's, followed by `→`
      and the arrival field's where the two differ; and, where more than
      one join reaches the arrival field, the number of its sources (J-D42);
    - `also`, the other occurrences whose joins to the same reading
      occurrence an entry of the wire writes, each with those joins
      (`_join_lines`).

    A row with nothing to print is left out. A wire whose occurrences the
    trellis does not hold is refused with a KeyError naming them. The
    answer's `names` holds the arrival fields of the joins by equal names,
    and its `removable` whether an entry writes a join of the wire.

    For the record of a pair of periods (`join_wires`, its writing key
    None; unit K's decision K-D5), the rows are those of the pair's wires
    together (`_pair_joins`): the place is the writers' period and the
    reading occurrence, `periods[1] → periods[0]/tenure`; `measure` prints
    each writer's measure before the reading one; `fields` and `written`
    hold the joins and the entries of every writer of the pair, and `also`
    the other occurrences alone. A pair the trellis no longer draws is
    refused with a KeyError.

    For the record of a cable of the backward graph (`join_wires` with that
    graph), the rows are its route, its status and its wires, then the
    entries that write its authored pairs (`_backward_join_rows`)."""
    texts = texts or {}
    if wire.get("graph") not in (None, _FORWARD):
        return _backward_join_rows(folder, shown, wire, texts)
    reader = (wire["reading"]["h"], wire["reading"]["key"])
    target = f"periods[{reader[0]}]/{reader[1]}"
    if wire["writing"]["key"] is None:
        # the writers of the pair's wires, and the port each writes from
        ids = ("source", "sourceHandle", "target", "targetHandle")
        members = next(
            (
                found["members"]
                for found in _pair_joins(_wire_joins(shown, texts))
                if all(found[k] == wire[k] for k in ids)
            ),
            [],
        )
        writers = list(dict.fromkeys(member["writing"] for member in members))
        handles = list(dict.fromkeys(member["sourceHandle"] for member in members))
        place = f"periods[{wire['writing']['h']}] → {target}"
        if not writers:
            raise KeyError(f"the trellis holds no pair of periods {place}")
    else:
        writers = [(wire["writing"]["h"], wire["writing"]["key"])]
        handles = [wire["sourceHandle"]]
        place = f"periods[{writers[0][0]}]/{writers[0][1]} → {target}"
    writer = writers[0]
    positions = set(occurrence_positions(shown).values())
    if reader not in positions or any(each not in positions for each in writers):
        raise KeyError(f"the trellis holds no join wire {place}")
    periods = shown.trellis["periods"]
    file = shown.trellis["provenance"]["trellis"]["path"]
    places = {}
    carried = _pairs_by_wire(shown)
    held = {pair for handle in handles for pair in carried.get((handle, reader), ())}
    selected = tuple(pair for pair in shown.selection.pairs if pair in held)
    entries = [
        entry for each in writers for entry in _pair_entries(shown, each, reader, places, texts, selected)
    ]
    names = tuple(pair.reading.field for pair in selected if pair.origin == "inferred") if wire["writing"]["key"] is not None else ()
    # the route, its status and its wires (design pass 10 §8)
    routes = [
        route for route in shown.selection.routes
        if any(pair in selected for pair in route.pairs)
    ]
    rows = _route_rows(folder, shown, routes, selected, reader, texts)
    links = [
        Line("", (Link(f"{path} · {address}", path, line),))
        for path, address, line in _entry_places(folder, entries, texts)
    ]
    if names:
        # the joins by equal names, which no entry writes, named after the
        # entries' links where an entry writes the wire's other joins (unit
        # L, Task 15)
        links.append(Line("", (BY_THE_NAMES, *(names if entries else ()))))
    if links:
        rows.append(("written", tuple(links)))
    if writer[0] != reader[0]:
        mappings = []
        for p in range(len(periods) - 1):
            address = f"inter_connectors[{p}]"
            if address not in places:
                places[address] = _place_of(file, address, texts)
            mappings.append(places[address])
        hr = reader[0]
        pairs = [p for p, at in enumerate(mappings) if at is not None and at == mappings[hr]]
        if pairs and len(pairs) == len(mappings):
            rows.append(("pairs", (Line("", (f"every adjacent pair ({len(pairs)})",)),)))
        elif pairs:
            parts = (f"{len(pairs)} of {len(mappings)}", f"periods {_pair_runs(pairs)}")
            rows.append(("pairs", (Line("", parts),)))
    else:
        reached = sorted({h for entry in entries for h in entry.periods})
        if reached:
            rows.append(("periods", (Line("", (_runs(reached),)),)))
    writing_labels = [_port_label(shown, handle) for handle in handles]
    reading_label = _port_label(shown, wire["targetHandle"])
    if all(writing_labels) and reading_label:
        lines = tuple(Line("", (label,)) for label in writing_labels)
        rows.append(("measure", (*lines, Line("→", (reading_label,)))))
    joins = _occurrence_joins(shown, reader)
    sources = {}
    for join in joins:
        if join[2] == reader:
            sources[join[3]] = sources.get(join[3], 0) + 1
    writing_sets = {
        each: _set_texts(periods[each[0]]["stages"][each[1]], cntn) for each in writers
    }
    reading_sets = _set_texts(periods[reader[0]]["stages"][reader[1]], arvl)
    table = []
    for pair in selected:
        source = (pair.writing.h, pair.writing.key)
        field, arrival = pair.writing.field, pair.reading.field
        # the two declared sets, the second only where it differs
        declared = dict.fromkeys(
            (writing_sets[source].get(field, ""), reading_sets.get(arrival, ""))
        )
        cells = (
            field if field == arrival else f"{field} → {arrival}",
            " → ".join(text for text in declared if text),
        )
        if sources[arrival] > 1:
            cells += (f"{sources[arrival]} sources",)
        table.append(Cells(cells))
    if table:
        rows.append(("fields", tuple(table)))
    if selected:
        rows.append(("compatibility", tuple(Line("", (
            f"{p.writing.key}.{p.writing.field} → {p.reading.key}.{p.reading.field}: "
            f"{p.compatibility}; {p.reason}",
        )) for p in selected)))
    obligations = tuple(dict.fromkeys(
        reason for route in shown.selection.routes
        if any(pair in selected for pair in route.pairs)
        for reason in route.obligations
    ))
    if obligations:
        rows.append(("composition", tuple(Line("", (reason,)) for reason in obligations)))
    own = {(entry.path, entry.item or entry.mapping) for entry in entries}
    others = []
    for other in dict.fromkeys(join[0] for join in joins if join[2] == reader):
        if other in writers:
            continue
        for entry in _pair_entries(shown, other, reader, places, texts):
            if (entry.path, entry.item or entry.mapping) in own:
                others.append((other, entry.field, reader, entry.arrival))
    if others:
        rows.append(("also", _join_lines(shown, writer, others, 0)))
    return JoinRows(place, tuple(rows), names, bool(entries))


def _backward_join_rows(folder: model.Folder, shown: TrellisShown, wire: dict, texts) -> JoinRows:
    """Details of the cable `wire` of the backward graph, as `join_wires`
    answers it with that graph (design pass 10 §8; the brief, § Wires,
    cables and connections): the rows `route`, `status` and `wires` of the
    route the record names (`_route_rows`), then `written`, the entries that
    write its authored pairs, each a link to its line; nothing is renamed or
    removed from the backward graph. A route the trellis no longer holds is
    refused with a KeyError naming it."""
    writer = (wire["writing"]["h"], wire["writing"]["key"])
    reader = (wire["reading"]["h"], wire["reading"]["key"])
    place = f"periods[{writer[0]}]/{writer[1]} → periods[{reader[0]}]/{reader[1]}"
    branch = wire.get("branch") or None
    routes = [
        route for route in shown.selection.routes
        if route.source == writer and route.destination == reader and (route.branch or None) == branch
    ]
    if not routes:
        raise KeyError(f"the trellis holds no route {place}")
    selected = tuple(pair for route in routes for pair in route.pairs)
    rows = _route_rows(folder, shown, routes, selected, reader, texts)
    places: dict = {}
    entries = _pair_entries(shown, writer, reader, places, texts, selected)
    links = [
        Line("", (Link(f"{path} · {address}", path, line),))
        for path, address, line in _entry_places(folder, entries, texts)
    ]
    if links:
        rows.append(("written", tuple(links)))
    return JoinRows(place, tuple(rows), (), False)


def _route_rows(folder: model.Folder, shown: TrellisShown, routes: list, selected: tuple, reader: tuple, texts) -> list:
    """The rows `route`, `status` and `wires` of Details of a cable (design
    pass 10 §8), as `join_rows` describes them, for the routes `routes` of
    the selection into the occurrence `reader`, each wire one of the
    selected pairs `selected`; an empty list where no route is given."""
    periods = shown.trellis["periods"]
    file = shown.trellis["provenance"]["trellis"]["path"]
    rows: list = []
    if routes:
        lines = []
        for route in routes:
            where = (
                f"periods[{route.source[0]}]/{route.source[1]} {PERCH_SIGN[cntn]} → "
                f"periods[{route.destination[0]}]/{route.destination[1]} {PERCH_SIGN[arvl]}"
            )
            lines.append(Line(f"branch {route.branch}" if route.branch else "", (where,)))
        rows.append(("route", tuple(lines)))
        rows.append(("status", tuple(
            Line("", (route.status,) if route.status == "certified"
                 else ("not certified", *route.obligations))
            for route in routes
        )))
        wires = []
        for route in routes:
            for pair in route.pairs:
                if pair not in selected:
                    continue
                source = (pair.writing.h, pair.writing.key)
                declared = dict.fromkeys((
                    _set_texts(periods[source[0]]["stages"][source[1]], cntn).get(pair.writing.field, ""),
                    _set_texts(periods[reader[0]]["stages"][reader[1]], arvl).get(pair.reading.field, ""),
                ))
                sets = " → ".join(text for text in declared if text)
                origin: object = "inferred"
                if pair.origin == "authored":
                    at = _place_of(file, pair.source_address, texts)
                    where = address_place(folder, at[0], at[1], False, texts=texts) if at else None
                    if where is not None:
                        origin = Link(f"authored, {Path(where[0]).name} {where[1]}", where[0], where[1])
                    else:
                        origin = "authored"
                wires.append(Line(f"{pair.writing.field} → {pair.reading.field}", tuple(part for part in (sets, origin) if part)))
        if wires:
            rows.append(("wires", tuple(wires)))
    return rows


class JoinLinks(NamedTuple):
    """One join that leaves a wire unpaired, with its links: `label`,
    `source` and `target` as the package's `UnpairedJoin` holds them, and
    `links`, to the header that declares each wire it leaves unpaired and
    to the connector that makes it."""

    label: str
    source: str
    target: str
    links: tuple


def refusal_links(
    folder: model.Folder, shown: TrellisShown, graph: str = "backward", texts=None
) -> list[JoinLinks]:
    """The links of the refusing node of the trellis view's graph `graph`
    (specification §3.1: a refusing trellis node links to the unpaired
    wire's header declaration and to the connector): for each join the
    package's `unpaired_joins` answers for the view, restricted as the view
    is, a link to the header line of each wire it leaves unpaired, in the
    occurrence's stage file, and a link to the connector that makes it, in
    the file that writes it at the line of its address (`address_place`),
    where the source names a trellis file (`recipe.trellis_file`); a join by
    equal names has no connector to link. Both read the mapping of unsaved
    texts `texts` (spec 0.4 §3.1)."""
    written = recipe.trellis_file(folder, shown.source, texts)
    found = []
    for join in unpaired_joins(shown.trellis, graph, selection=shown.selection, **_selection(shown.restriction)):
        links = [
            Link(
                f"{Path(wire.file).name} {wire.line} {wire.name}",
                recipe.relative(folder, wire.file),
                wire.line,
            )
            for wire in join.wires
            if wire.file and wire.line is not None
        ]
        if join.connector and written is not None:
            place = address_place(folder, folder.root / written, join.connector, texts=texts)
            if place is not None:
                links.append(Link(f"{Path(place[0]).name} {join.connector}", place[0], place[1]))
        found.append(JoinLinks(join.label, join.source, join.target, tuple(links)))
    return found


# --- the gestures of the trellis graph (unit J) ---


def _position(text: str, offset: int) -> tuple[int, int]:
    """The line and the column, each counted from one, of the code-point
    offset `offset` of `text`."""
    start = text.rfind("\n", 0, offset) + 1
    return text.count("\n", 0, offset) + 1, offset - start + 1


def restoring_edit(before: str, after: str) -> dict:
    """The one replacement that turns the text `after` into the text
    `before` (spec 0.4 §3.3; brief rule 8, J-D19): the span of `after`
    between the longest common prefix and the longest common suffix of the
    two texts, the suffix taken from what the prefix leaves, replaced by the
    text of `before` between them; `{line, column, end_line, end_column,
    text}`, counted from one in code points as `model.Replacement` counts
    them. Given the text a gesture made as `after`, it takes the gesture's
    line out; with the arguments exchanged, it types the line. Two equal
    texts give an empty replacement at their end."""
    shorter = min(len(before), len(after))
    prefix = 0
    while prefix < shorter and before[prefix] == after[prefix]:
        prefix += 1
    suffix = 0
    while suffix < shorter - prefix and before[-1 - suffix] == after[-1 - suffix]:
        suffix += 1
    line, column = _position(after, prefix)
    end_line, end_column = _position(after, len(after) - suffix)
    replaced = model.Replacement(
        line, column, end_line, end_column, before[prefix : len(before) - suffix]
    )
    return replaced._asdict()


def typed_line(before: str, after: str) -> int:
    """The line, counted from one, that a gesture typed when it turned the
    text `before` into the text `after` (spec 0.4 §3.1, the typed line): the
    first line of `after` that differs from the line of `before` at the
    same position, each text divided into lines at its line ends; the last
    line of `after` where no line before it differs. Unlike the first line
    of `restoring_edit`, it is the typed line also where `before` ends
    without a line end and the gesture's text begins with one."""
    old, new = before.split("\n"), after.split("\n")
    line = 1
    while line < len(new) and line <= len(old) and old[line - 1] == new[line - 1]:
        line += 1
    return line


# the one graph in which a drag between two unjoined ports is admitted
# (spec 0.4 §3.1)
_FORWARD = "forward"


def _drawn(shown: TrellisShown) -> dict:
    """The source, the graph and the elaboration number of the reading
    `shown`, as the record of a reading names them (spec 0.4 §3.2)."""
    return {"source": shown.source.path, "graph": _FORWARD, "number": shown.number}


def reading_record(folder: model.Folder, shown: TrellisShown) -> dict:
    """The record of the reading `shown` that the graph region is given with
    the unjoined ports and returns unchanged with the event of a drag (spec
    0.4 §3.2, §3.3; J-D18): `source`, the source's path relative to the
    folder `folder`; `graph`, `forward`; `number`, the number of the
    elaboration drawn; and `inputs`, each file the reading read, in the
    order of `shown.files`, by the path the editor names it by,
    `recipe.relative`, relative to the folder in posix form and by `..`
    steps for a file outside it (decision B-D6), so that the region can
    tell an edit of one of them from the editor's notice (unit J's plan,
    Task 9)."""
    inputs = [recipe.relative(folder, name) for name in shown.files]
    return {**_drawn(shown), "inputs": inputs}


def _field_ports(shown: TrellisShown) -> list[dict]:
    """`{"id", "node", "side", "h", "key", "field", "label", "unjoined",
    "sources"}` of each port of the forward graph of the view `shown` holds
    that stands for one state field, the ports the exporter adds with its
    keyword `unjoined` (spec 0.4 §3.4; J-D16; unit J's decisions J-D41 to
    J-D43): an output of a node is a writing port and an input a reading
    port; `(h, key)` is the position of the occurrence `node_place` answers
    for the port's node; `field` is the field's name as its stage file
    writes it and `label` the port's label in the graph; `unjoined` is
    whether no join reaches the field, the exporter's mark; `sources`
    is the number of joins that reach a reading port, none for a writing
    port or an unjoined one; and `branch` is the branch a continuation
    field leaves by, the word before `: ` in its label, `keep: w_kp≻`, the
    empty text for a field of no branch and for an arrival field (design
    pass 10 §6)."""
    positions = occurrence_positions(shown)
    found = []
    for graph in shown.collection["graphs"]:
        if graph["id"] != _FORWARD:
            continue
        for node in graph["nodes"]:
            for side, items in (
                ("writing", node.get("outputsMetadata")),
                ("reading", node.get("inputsMetadata")),
            ):
                for item in items or []:
                    attributes = {pair["key"]: pair["value"] for pair in item.get("attrs") or []}
                    if "field" not in attributes:
                        continue
                    place = node_place(shown.collection, _FORWARD, node["id"])
                    h, key = positions[place.occurrence]
                    label = attributes.get("label", attributes["field"])
                    found.append(
                        {
                            "id": item["id"],
                            "node": node["id"],
                            "side": side,
                            "h": h,
                            "key": key,
                            "field": attributes["field"],
                            "label": label,
                            "unjoined": "unjoined" in attributes,
                            "sources": int(attributes.get("sources", 0)),
                            "branch": label.split(": ", 1)[0] if side == "writing" and ": " in label else "",
                        }
                    )
    return found


def _place_of(file, address: str, texts):
    """`written_at(file, address, texts)`, the file and the address at which
    the trellis file `file` writes `address`; None where it writes no such
    place or cannot be read."""
    try:
        return written_at(file, address, texts)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def _pairs_reached(places: list, pair: int) -> list[int]:
    """The periods, in order, of every adjacent pair whose inter-period
    mapping stands where that of the pair `pair` stands, `places` holding
    each pair's place; none where the trellis holds no pair `pair` or its
    file writes no mapping for it."""
    if not 0 <= pair < len(places) or places[pair] is None:
        return []
    return sorted(
        {h for p, place in enumerate(places) if place == places[pair] for h in (p, p + 1)}
    )


def unjoined_ports(shown: TrellisShown, texts=None) -> list[dict]:
    """The unjoined ports of the forward graph that the view of `shown`
    draws, each `{"id", "node", "side", "h", "key", "field", "periods",
    "periods_between"}` (spec 0.4 §3.2; ruling J-P7): the port's id and its
    node in the graph JSON; `side`, `writing` for a continuation field and
    `reading` for an arrival field; the position `(h, key)` of its stage
    occurrence and the field's name. `periods` holds the periods whose
    `connectors` list stands where that of `periods[h]` stands, the place
    `written_at` answers for `periods[h].connectors`, which the region marks
    while a drag stays in the port's period. `periods_between` holds the
    periods of every pair whose inter-period mapping stands where the
    mapping a drag between periods would extend stands: the mapping of the
    pair of `periods[h]` and `periods[h - 1]` for a writing port, and of
    `periods[h + 1]` and `periods[h]` for a reading port, each place the
    one `written_at` answers for `inter_connectors[…]`; it is empty where
    the trellis file writes no such mapping. Both read the trellis file
    through `texts`, the mapping of unsaved texts (spec 0.4 §3.1)."""
    unjoined = [port for port in _field_ports(shown) if port["unjoined"]]
    return _drag_records(shown, unjoined, texts)


def _drag_records(shown: TrellisShown, ports: list, texts) -> list[dict]:
    """The records `unjoined_ports` describes of the field ports `ports` of
    the view `shown` (`_field_ports`), the trellis file read through
    `texts`."""
    file = shown.trellis["provenance"]["trellis"]["path"]
    count = len(shown.trellis["periods"])
    within = [_place_of(file, f"periods[{h}].connectors", texts) for h in range(count)]
    between = [_place_of(file, f"inter_connectors[{p}]", texts) for p in range(count - 1)]
    found = []
    for port in ports:
        h = port["h"]
        periods = (
            [p for p in range(count) if within[p] == within[h]] if within[h] is not None else [h]
        )
        pair = h - 1 if port["side"] == "writing" else h
        record = {name: port[name] for name in ("id", "node", "side", "h", "key", "field", "branch")}
        found.append(
            {
                **record,
                "joined": not port["unjoined"],
                "periods": periods,
                "periods_between": _pairs_reached(between, pair),
            }
        )
    return found


def _sources_title(label: str, sources: int) -> str:
    """The hover of a reading port that joins reach, its label and the
    number of its sources, `a_bq≺ · 2 sources` (unit J's decision J-D42)."""
    return f"{label} · {sources} {'source' if sources == 1 else 'sources'}"


# The suffixes that a continuation field's name may carry beyond the name of
# the arrival field it pairs with (unit K's decision K-D8).
PAIRING_SUFFIXES = ("next", "nxt", "kp", "adj")


def pairing_names(field: str, labels=()) -> tuple[str, ...]:
    """The names of the arrival fields with which the continuation field
    `field` pairs, in the order in which a pairing prefers them (unit K's
    decision K-D8): the name itself; then the name with a suffix `_next`,
    `_nxt`, `_kp`, `_adj` or `_<label>`, for a label of `labels`, the branch
    labels of the field's stage, dropped from its end; then that name with
    another such suffix dropped, until no such suffix ends the name, the
    longest suffix dropped first where two end it. A suffix that is the
    whole name is not dropped: `a_nxt_kp` pairs with `a_nxt_kp`, `a_nxt`
    and `a`."""
    endings = sorted({f"_{suffix}" for suffix in (*PAIRING_SUFFIXES, *labels)}, key=len)
    names = [field]
    while True:
        name = names[-1]
        ending = next(
            (end for end in reversed(endings) if name.endswith(end) and len(name) > len(end)),
            None,
        )
        if ending is None:
            return tuple(names)
        names.append(name[: -len(ending)])


def _stage_labels(shown: TrellisShown, h: int, key: str) -> tuple[str, ...]:
    """The branch labels of the stage of the occurrence `(h, key)` of the
    trellis `shown` holds (`branches`), none for a stage without branches
    or one the package does not read as a stage."""
    try:
        return tuple(branches(shown.trellis["periods"][h]["stages"][key]))
    except _REFUSALS:
        return ()


def _field_sets(shown: TrellisShown):
    """The declared sets of the fields of the stage occurrences of the
    trellis `shown` holds, which the pairing lists print beside each field
    (unit K's decision K-D25): a function of an occurrence's position `(h,
    key)` and a port's side, `writing` for the continuation fields and
    `reading` for the fields of the entry perch, the arrival perch where the
    stage declares one and the decision perch otherwise (`entry_perch`;
    decision MB-U31), that answers the set of each field of that side by its
    name, as the stage file writes it and the Fields tab prints it
    (`_set_texts`), the empty text for a field declared with none; each
    occurrence and side read once, and none for an occurrence the package
    does not read as a stage."""
    found: dict[tuple, dict] = {}

    def sets(h: int, key: str, side: str) -> dict:
        if (h, key, side) not in found:
            try:
                stage = shown.trellis["periods"][h]["stages"][key]
                perch = cntn if side == "writing" else entry_perch(stage)
                found[h, key, side] = _set_texts(stage, perch)
            except _REFUSALS:
                found[h, key, side] = {}
        return found[h, key, side]

    return sets


def _paired(shown: TrellisShown, records: list[dict]) -> list[dict]:
    """The records `records` of `connectable_ports`, each writing record
    given `pairs` (unit K's decision K-D8): for each stage occurrence that
    a drag from the writing port can reach, another of its period or one of
    the period after it in time, `periods[h - 1]`, and that holds an
    unjoined arrival field whose name pairs with the continuation field's
    (`pairing_names`, under the branch labels of the writing occurrence's
    stage), the id of that field's port, by the occurrence's namespace in
    the graph JSON, `periods[2]/cons`; where several of its arrival fields
    pair, the one whose name `pairing_names` gives first. A reading port
    that joins reach is offered as a further source (J-D41) and never paired
    here, so that the pairing proposes only a first join.

    Each writing record is given also `equal`, the pair the package would
    select on its own, which a cable's list pre-fills (design pass 10 §7;
    AMD-COMP-001 §§3.2–3.3): by the occurrence's namespace, the id of the
    arrival field's port where the selection's candidate groups name this
    continuation use as the one candidate of that arrival field, an equal
    name no other admissible source offers, and no rejection names the
    pair. The candidates are the package's, computed on the text read, so
    the eligibility and the compatibility are the package's checks and not
    a comparison of names made here."""
    arrivals: dict[int, dict[str, dict[str, str]]] = {}
    every: dict[int, dict[str, dict[str, str]]] = {}
    for record in records:
        if record["side"] == "reading":
            every.setdefault(record["h"], {}).setdefault(record["key"], {})[record["field"]] = record["id"]
            if "sources" not in record:
                fields = arrivals.setdefault(record["h"], {}).setdefault(record["key"], {})
                fields[record["field"]] = record["id"]
    # the writing uses the package's candidate groups offer for each arrival
    # use, and the candidate pairs it rejected
    offers: dict[tuple, list] = {}
    for group in shown.selection.candidates:
        for candidate in group.candidates:
            for writing, reading in candidate.pairs:
                offers.setdefault((reading.h, reading.key, reading.field), []).append(
                    (writing.h, writing.key, writing.field)
                )
    rejected = {
        ((r.writing.h, r.writing.key, r.writing.field), (r.reading.h, r.reading.key, r.reading.field))
        for r in shown.selection.rejected
    }
    labels: dict[tuple, tuple] = {}
    found = []
    for record in records:
        if record["side"] != "writing":
            found.append(record)
            continue
        h, key = record["h"], record["key"]
        if (h, key) not in labels:
            labels[(h, key)] = _stage_labels(shown, h, key)
        names = pairing_names(record["field"], labels[(h, key)])
        pairs, equal = {}, {}
        for h2 in (h, h - 1):
            for key2, fields in arrivals.get(h2, {}).items():
                if h2 == h and key2 == key:
                    continue
                port = next((fields[name] for name in names if name in fields), None)
                if port is not None:
                    pairs[f"periods[{h2}]/{key2}"] = port
            # the pair the package would select on its own: the arrival field
            # of the continuation field's name whose one candidate, in the
            # package's groups, is this use, and which no rejection names
            # (design pass 10 §7; AMD-COMP-001 §3.2)
            for key2, fields in every.get(h2, {}).items():
                if (h2 == h and key2 == key) or record["field"] not in fields:
                    continue
                use, arrival = (h, key, record["field"]), (h2, key2, record["field"])
                if offers.get(arrival) == [use] and (use, arrival) not in rejected:
                    equal[f"periods[{h2}]/{key2}"] = fields[record["field"]]
        found.append({**record, "pairs": pairs, "equal": equal})
    return found


def connectable_ports(shown: TrellisShown, texts=None) -> list[dict]:
    """The ports of the forward graph that the view of `shown` draws and a
    drag can take, which the graph region is given (spec 0.4 §3.2, as unit
    J's decision J-D41 amends §3.1): every unjoined port, as
    `unjoined_ports` answers it, a drag starting at an unjoined writing
    port, since a continuation field joins one arrival field; and every
    reading port that joins reach, at which a drag ends as a further
    source, its record holding also `sources`, the number of those joins,
    and `title`, its hover, `a_bq≺ · 2 sources` (J-D42); and every joined
    continuation field, `joined`, which a cable's list offers among its
    branch's fields (design pass 10 §7). Every record holds `branch`, the
    branch a continuation field leaves by, the empty text for none. Each
    writing record holds also `pairs`, the arrival fields its name pairs
    with, which the list a drag between two frames opens proposes
    (`_paired`; unit K's decision K-D8), and `equal`, the arrival field
    the package's selection names as the one candidate of this use in each
    occurrence a drag can reach, the pair the package would select on its
    own, which a cable's list pre-fills (design pass 10 §7; `_paired`).
    Every record holds also `set`, the declared
    set of its field as the Fields tab prints it, the empty text where none
    is declared, which the lists of a drag between two frames and of a move
    print beside the field (`_field_sets`; unit K's decision K-D25). The
    trellis file is read through `texts`, the mapping of unsaved texts
    (spec 0.4 §3.1)."""
    fields = _field_ports(shown)
    reached = [port for port in fields if port["side"] == "reading" and not port["unjoined"]]
    found = _drag_records(shown, [port for port in fields if port["unjoined"]], texts)
    for port, record in zip(reached, _drag_records(shown, reached, texts)):
        title = _sources_title(port["label"], port["sources"])
        found.append({**record, "sources": port["sources"], "title": title})
    # every joined continuation field too, `joined`, which a cable's list
    # offers among its branch's fields and a move of a writing end may land
    # on, the write releasing its pair (design pass 10 §7)
    joined = [port for port in fields if port["side"] == "writing" and not port["unjoined"]]
    found.extend(_drag_records(shown, joined, texts))
    sets = _field_sets(shown)
    return [
        {
            **record,
            "set": sets(record["h"], record["key"], record["side"]).get(record["field"], ""),
        }
        for record in _paired(shown, found)
    ]


class Gesture(NamedTuple):
    """What a gesture of the trellis graph answers (spec 0.4 §3.3; brief
    rule 6): `edits`, the new text of each existing file the gesture edits,
    by the file's resolved path, the key of the mapping of unsaved texts
    (ruling J-P6); `read`, the text each edit was made from, by the same
    paths; `new_files`, the files the gesture writes to disk, each as a pair
    (its path relative to the model folder, its text), none for a connector;
    `note`, the status line of what was written and where; `sentence`, the
    Workbench's sentence of a gesture that types nothing (brief §5); `file`
    and `address`, the resolved path of the file and the address the
    gesture names, those of the line it types or of its sentence, the
    address None where the sentence names the file alone; and
    `restriction`, the text for the restriction's input after a period is
    added between two periods, `periods 2–4` or the empty text, None where
    no index moved (spec 0.4 §3.6); and `deleted`, the files and folders a
    removal deletes from disk once the files that named them are saved, by
    their paths from the model folder, none for every other gesture (unit
    L, Task 25; AAS, L-D18). At most one of `edits` and `sentence` is
    given, the other None, and a gesture with neither writes nothing and
    prints nothing (ruling J-P16)."""

    edits: dict | None
    read: dict | None
    new_files: tuple
    note: str | None
    sentence: str | None
    file: str | None
    address: str | None
    restriction: str | None = None
    deleted: tuple = ()


# the verb of "A shared name" for each perch the package names in
# `ConnectorEntry.held`
_HOLDING = {"cntn": "continue to", "arvl": "arrive at"}


def _place_words(entry) -> str:
    """The name of the file `entry` names and the address in it,
    `trellis.yml, periods[0].connectors`, or the name alone where the
    address is empty or None."""
    name = Path(entry.file).name
    return f"{name}, {entry.address}" if entry.address else name


def gesture_sentence(
    reason: str, entry, writing, reading, removal: str | None = None, rename: bool = False
) -> str:
    """The Workbench's sentence of a drag that types nothing, in the error
    mark's list (spec 0.4 §3.1; brief rule 8 and §5; J-D4): the file and
    the address, what was not written, why, and what to do, in the file's
    words, a field as the file writes it, a stage occurrence by its key and
    its period, and no rule or decision code. `entry` is the drag's
    `ConnectorEntry`; for the reasons `not-applied` and `old-graph`, which
    read only its `file` and `address`, any record with those two, a
    `Gesture` among them. `writing` and `reading` are the two ports, each
    `(h, key, field)`. `removal` names what a removal removes, `join` for a
    join (J-D33) and `stage` for a stage occurrence taken out of its period
    (unit K's decision K-D14), None for a drag: a removal is no drag, so
    the last sentence of "An edit not applied" and "An old graph" then asks
    for the join, or the stage, to be removed again (unit J's plan, Task
    17). `rename` marks the rename of the reading field of a join by equal
    names (unit L, Task 15), which is no drag either: those two sentences
    then ask for the field to be renamed again. The sentences, by
    `reason`:

    - `name-shared`, "A shared name": the period `entry.shared` names and,
      as `entry.held` gives them, the first two occurrences of that period
      that hold the shared name, `entry.shared`'s among them, the name, and
      the verb of its perch, `continue to` or `arrive at`.
    - `no-mapping` between two periods, "No mapping".
    - `no-mapping` within one period, the sentence of the plan's decision
      J-D25, which brief §5 does not hold: the period writes no
      `connectors` list.
    - `not-applied`, "An edit not applied".
    - any other reason, `old-graph`, or `port-joined` and `not-adjacent`,
      which no current graph answers: "An old graph", whose first word is
      the name of the file, the trellis file."""
    place = _place_words(entry)
    if reason == "source-authored":
        return (f"{place}: the entry {entry.text} was not written. This mapping already "
                "has an entry with a source name needed for this connection. Edit or remove that entry first.")
    if reason == "name-shared":
        if entry.shared is None:
            return (f"{place}: the entry {entry.text} was not written. "
                    "No single endpoint spelling selects this connection in every period "
                    "reached by the source entry. Write separate period mappings.")
        h = entry.shared[0]
        perch, name, keys = entry.held
        return (
            f"{place}: the entry {entry.text} was not written. In periods[{h}] both {keys[0]} and "
            f"{keys[1]} {_HOLDING[perch]} {name}. No single endpoint spelling selects this "
            "connection in every period reached by the source entry. Write separate period mappings."
        )
    if reason == "no-mapping" and writing[0] != reading[0]:
        return (
            f"{place}: the entry {entry.text} was not written. The file writes no inter-period "
            "mapping. Type one mapping for every pair, or one for each pair."
        )
    if reason == "no-mapping":
        return (
            f"{place}: the connector {entry.text} was not written. The period writes no "
            "connectors list. Type connectors: [{}] in it."
        )
    if reason == "not-applied" and rename:
        return (
            f"{place}: nothing was written. The text changed after the rename read it. "
            "Rename the field again."
        )
    if reason == "not-applied" and removal:
        return (
            f"{place}: nothing was written. The text changed after the removal read it. "
            f"Remove the {removal} again."
        )
    if reason == "not-applied":
        return (
            f"{place}: nothing was written. The text changed after the drag read it. Drag again."
        )
    again = (
        "Rename the field again"
        if rename
        else f"Remove the {removal} again"
        if removal
        else "Drag again"
    )
    return (
        f"{Path(entry.file).name}: nothing was written. The graph was drawn from an earlier "
        f"text. {again} in the graph now drawn."
    )


def _old_graph(shown: TrellisShown, removal: str | None = None, rename: bool = False) -> Gesture:
    """The `Gesture` of an event that the reading `shown` does not admit:
    the sentence "An old graph" of brief §5 at the trellis file, for the
    removal of what `removal` names, `join` or `stage`, where it is given,
    or, with `rename`, for the rename of a reading field (unit L, Task 15;
    `gesture_sentence`)."""
    file = str(Path(shown.trellis["provenance"]["trellis"]["path"]).resolve())
    place = Gesture(None, None, (), None, None, file, None)
    sentence = gesture_sentence("old-graph", place, None, None, removal, rename)
    return place._replace(sentence=sentence)


def _of_reading(shown: TrellisShown, event) -> bool:
    """Whether `event` is a record whose `reading` names the source, the
    graph and the elaboration number of the reading `shown` (spec 0.4
    §3.3)."""
    drawn = event.get("reading") if isinstance(event, dict) else None
    return isinstance(drawn, dict) and all(
        drawn.get(name) == value for name, value in _drawn(shown).items()
    )


def _event_ports(shown: TrellisShown, event) -> tuple | None:
    """The writing port and the reading port, each its record of
    `_field_ports`, that the event `connected` names (spec 0.4 §3.3): where
    the event's `reading` names the source, the graph and the number of
    `shown`, and its `sourceHandle` and `targetHandle` are the ids of a
    writing port and a reading port of the view `shown` holds that each
    stand for one state field, joined or not. None otherwise, a record that
    is no event included."""
    if not _of_reading(shown, event):
        return None
    ports = {port["id"]: port for port in _field_ports(shown)}
    handles = (event.get("sourceHandle"), event.get("targetHandle"))
    if not all(isinstance(handle, str) and handle in ports for handle in handles):
        return None
    source, target = (ports[handle] for handle in handles)
    if (source["side"], target["side"]) != ("writing", "reading"):
        return None
    return source, target


def _field_of(port: dict) -> tuple:
    """`(h, key, field)` of the field port `port` (`_field_ports`), as the
    package's `connector_entry` names a port."""
    return port["h"], port["key"], port["field"]


def _joined_writing(shown: TrellisShown, port: dict, texts) -> Gesture:
    """The `Gesture` of a drag from the writing port `port` that a join
    already reads (unit J's decision J-D41): nothing typed, since a
    continuation field joins one arrival field, and the sentence `The port
    <label> is joined. A continuation field joins one arrival field.` after
    the file and the address of the entry that writes that join, as
    `_pair_entries` finds it, read through the mapping of unsaved texts
    `texts`, or after the trellis file's name alone for a join by equal
    names, which no entry writes. The port is named by its field as the
    file writes it, `a_nxt_kp`, not by its label in the graph, `a_nxt_kp≻`
    (spec 0.4 §3.1; unit J's plan, Task 17)."""
    trellis, (h, key, field) = shown.trellis, _field_of(port)
    periods = trellis["periods"]
    path = str(Path(trellis["provenance"]["trellis"]["path"]).resolve())
    address = None
    for pair in shown.selection.pairs:
        if (pair.writing.h, pair.writing.key, pair.writing.field) != (h, key, field):
            continue
        entries = _pair_entries(shown, (h, key), (pair.reading.h, pair.reading.key), {}, texts)
        written = [entry for entry in entries if entry.field == field]
        if written:
            path, address = written[0].path, written[0].item or written[0].mapping
        break
    return _continuation_joined(path, address, field)


def _continuation_joined(path: str, address: str | None, field: str) -> Gesture:
    """The `Gesture` of a line that would start at the continuation field
    `field`, which a join already reads (unit J's decision J-D41): nothing
    typed, and the sentence `The port <field> is joined. A continuation
    field joins one arrival field.` after the name of the file `path` and
    the address `address`, or after the file's name alone where `address`
    is None."""
    place = f"{Path(path).name}, {address}" if address else Path(path).name
    sentence = (
        f"{place}: nothing was written. The port {field} is joined. "
        "A continuation field joins one arrival field."
    )
    return Gesture(None, None, (), None, sentence, path, address)


def _value_text(line: str, key: str) -> str:
    """The text of the value at `key` of the mapping written on the one line
    `line`, as written there: `m` in `{m_next: m}`, `{m_next: m}` as the
    value of `fields` (`entry_span`, whose columns count code points)."""
    span = entry_span(line, (key,))
    return line[span.column - 1 : span.end_column - 1]


def _typed(text: str, entry) -> str:
    """`text` with the line of the `ConnectorEntry` `entry` typed at its
    address by the package's text writers, every other character kept (spec
    0.4 §3.1; ruling J-P1): appended as one item through
    `append_to_sequence` where a list stands at the address; otherwise each
    entry of the line, a mapping, appended in order through
    `append_to_mapping` to the mapping that stands there, the first empty
    mapping of a `connectors` list or an inter-period mapping. A writer's
    refusal is its ValueError, and an address the text does not hold a
    KeyError."""
    if isinstance(entry_value(text, entry.address), list):
        return append_to_sequence(text, entry.address, entry.text)
    for key in entry_value(entry.text):
        text = append_to_mapping(text, entry.address, key, _value_text(entry.text, key))
    return text


def _read_text(path: str) -> str:
    """The text of the file at `path`, read as UTF-8 with its line ends as
    written, as `model.read_file` reads a buffer's file."""
    with open(path, encoding="utf-8", newline="") as stream:
        return stream.read()


def _runs(periods) -> str:
    """The periods `periods`, in order, each run of consecutive periods
    written as a range, `0–5`, and a period alone by its number, `0–2, 4`."""
    runs = []
    for h in periods:
        if runs and h == runs[-1][1] + 1:
            runs[-1][1] = h
        else:
            runs.append([h, h])
    return ", ".join(f"{first}–{last}" if last > first else f"{first}" for first, last in runs)


def _checked_edit(shown: TrellisShown, gesture: Gesture, texts, expected=(), released=(), end="reading") -> Gesture:
    """Validate the complete proposed source with the package, preserving
    existing draft diagnostics and permitting incremental incomplete routes.
    No stage is constructed or copied for this check. `expected` are the
    pairs the proposed source must select, each `(writing, reading)` of
    field positions `(h, key, field)`; `released` are the pairs it must no
    longer select, those of a whole cable's route that stand on another
    occurrence than the one its moved end, `end`, now stands on (design
    pass 10 §7): where the package would select one of them again, by an
    equal name the ticked rows left unpaired, a moved reading end would
    leave the branch on two destinations and a moved writing end would
    leave the arrival tuple reading two sources, which the brief forbids,
    and nothing is written (AMD-COMP-001 §3.2)."""
    if not gesture.edits:
        return gesture
    try:
        proposed = _with_connectors(shown, {**texts, **gesture.edits})
        selected = trellis_selection(proposed)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return gesture._replace(edits=None, read=None, note=None, sentence=f"Nothing was written. {error}")
    # The package records the bindings a comparison actually read. If an
    # earlier binding remains, a refused replacement cannot authorize its use.
    if "calibrate" in shown.binding.failed:
        earlier_pairs, earlier_routes = set(shown.selection.pairs), set(shown.selection.routes)
        affected = (set(selected.pairs) - earlier_pairs) | (set(selected.routes) - earlier_routes)
        if any(item.basis for item in affected):
            return gesture._replace(edits=None, read=None, note=None, sentence=(
                "Nothing was written. This connection depends on retained calibration values, "
                "but the requested calibration was refused. " + shown.binding.failed["calibrate"]
            ))
    prior = {(d.rule, d.address, d.message) for d in shown.selection.diagnostics}
    refused = next((d for d in selected.diagnostics
                    if d.rule != "route-incomplete"
                    and (d.rule, d.address, d.message) not in prior), None)
    # the draft the edit leaves, an incomplete route the package reports
    # under Problems, named in the note in the package's sentence (design
    # pass 10 §7)
    drafts = [d.message for d in selected.diagnostics
              if d.rule == "route-incomplete" and (d.rule, d.address, d.message) not in prior]
    present = {((p.writing.h, p.writing.key, p.writing.field),
                (p.reading.h, p.reading.key, p.reading.field)) for p in selected.pairs}
    if refused is not None:
        return gesture._replace(edits=None, read=None, note=None,
                                sentence=refused.message)
    if any(pair not in present for pair in expected):
        return gesture._replace(edits=None, read=None, note=None,
                                sentence="Nothing was written. The proposed source does not select every requested connection.")
    kept = [pair for pair in released if pair in present]
    if kept:
        (writing, reading), *_ = sorted(kept)
        arrow = f"{writing[1]}.{writing[2]} → {reading[1]}.{reading[2]}"
        if writing[0] != reading[0]:
            arrow = f"periods[{writing[0]}].{writing[1]}.{writing[2]} → periods[{reading[0]}].{reading[1]}.{reading[2]}"
        outcome = ("the branch would stand on two destinations" if end == "reading"
                   else "the arrival tuple would read two sources")
        return gesture._replace(edits=None, read=None, note=None, sentence=(
            f"Nothing was written. The proposed source still selects {arrow}, so {outcome}."
        ))
    previous = {((p.writing.h, p.writing.key, p.writing.field),
                 (p.reading.h, p.reading.key, p.reading.field)) for p in shown.selection.pairs}
    changes = []
    # the pairs the edit deselects and selects, where it deselects any
    deselected = previous - present
    for label, pairs in ((("no longer selected", deselected), ("now selected", present - previous)) if deselected else ()):
        groups = {}
        for writing, reading in sorted(pairs):
            if writing[0] == reading[0]:
                arrow = f"{writing[1]}.{writing[2]} → {reading[1]}.{reading[2]}"
                groups.setdefault(arrow, []).append(writing[0])
            else:
                arrow = (f"periods[{writing[0]}].{writing[1]}.{writing[2]} → "
                         f"periods[{reading[0]}].{reading[1]}.{reading[2]}")
                groups[arrow] = []
        if groups:
            changes.append(label + ": " + ", ".join(
                arrow + (f" in periods {_runs(periods)}" if periods else "")
                for arrow, periods in groups.items()
            ))
    # the first draft's sentence, and the count of the others, one per period
    # a shared entry reaches
    drafts = list(dict.fromkeys(drafts))
    if drafts:
        changes.append(f"draft: {drafts[0]}" + (f" (and {len(drafts) - 1} more)" if len(drafts) > 1 else ""))
    if not changes:
        return gesture
    return gesture._replace(note="; ".join(part for part in (gesture.note, *changes) if part))


def connector_edit(shown: TrellisShown, event, texts) -> Gesture:
    """The `Gesture` of the event `connected`, a drag from a writing port
    to a reading port of the forward trellis graph drawn from the reading
    `shown`, a function of its arguments that reads no state of the page
    and raises nothing (spec 0.4 §3.1, §3.3; brief rules 1, 6 and 8; unit
    J's decisions J-D41 and J-D42). `texts` is the mapping of every unsaved
    buffer of the tab, by resolved path. In order:

    1. Where the event's `reading` names another source, graph or
       elaboration number than `shown`, where a file `shown` read now holds
       another text on disk or in `texts` (`inputs_current`), or where
       either handle is not the id of a port of the view that stands for
       one state field on the side the event gives it, the answer is the
       sentence "An old graph".
    2. Where a join already reads the writing port, nothing is typed, since
       a continuation field joins one arrival field: the sentence `The port
       <label> is joined. A continuation field joins one arrival field.`
       (`_joined_writing`).
    3. The package's `connector_entry(shown.trellis, writing, reading,
       texts)` names the file, the address, the text and the periods of the
       line, a reading port that joins reach taking a further source; its
       reasons `port-joined` and `not-adjacent`, which no current graph
       answers, and a file it can no longer read, also answer "An old
       graph", and its other reasons the sentence `gesture_sentence` writes.
       Where the two stage occurrences stand in one period and a connector
       of its list already joins them, the line is a key of that connector
       (`connector_entry`; unit L, Task 19).
    4. Otherwise the text of that file is taken from `texts`, else from
       disk, and the line typed by the package's text writers (`_typed`): a
       writer's refusal answers the sentence "An edit not applied".
    5. The note names the file, the address, the text, its form, `flat` or
       `keyed` within a period and `entry` between two, and the periods it
       reaches, as ranges where consecutive: `trellis.yml,
       periods[0].connectors[0]: {m_next: m} written, flat, periods 0–5`.
       Where joins already reach the reading port and the line is a further
       key of a mapping that holds keys, the note names no form:
       `trellis.yml, periods[0].connectors[0]: {a_nxt_adj: a_bq} written,
       periods 0` (J-D42).

    An event that holds `pairs` in place of the two handles, the button
    `join` of the list that a drag between the frames of two stage
    occurrences opens, is answered by `_frame_edit`, which types the pairs
    as one mapping (unit K's decision K-D8). Nothing is written: the edit
    is answered for the buffer of its file."""
    texts = texts or {}
    if isinstance(event, dict) and "pairs" in event:
        return _frame_edit(shown, event, texts)
    ports = _event_ports(shown, event)
    if ports is None or not inputs_current(shown, texts):
        return _old_graph(shown)
    if not ports[0]["unjoined"]:
        # a drag from a joined continuation port is the move of its cable's
        # reading end (design pass 10 §7; `_cable_move`)
        return _cable_move(shown, event, [ports], texts)
    writing, reading = (_field_of(port) for port in ports)
    try:
        entry = connector_entry(shown.trellis, writing, reading, texts, selection=shown.selection)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        # a file the reading read no longer reads as it read it
        return _old_graph(shown)
    if entry.reason in ("port-joined", "not-adjacent"):
        return _old_graph(shown)
    path = str(Path(entry.file).resolve())
    if entry.reason is not None:
        sentence = gesture_sentence(entry.reason, entry, writing, reading)
        return Gesture(None, None, (), None, sentence, path, entry.address)
    try:
        before = texts[path] if path in texts else _read_text(path)
        held = entry_value(before, entry.address)
        after = _typed(before, entry)
    except (OSError, ValueError, KeyError, TypeError):
        # a TypeError: a name of the line that YAML reads as no string
        sentence = gesture_sentence("not-applied", entry, writing, reading)
        return Gesture(None, None, (), None, sentence, path, entry.address)
    if not ports[1]["unjoined"] and isinstance(held, dict) and held:
        # a further source, a key added to the mapping of a join that
        # reaches the arrival (J-D42)
        form = ""
    else:
        within = "keyed, " if _keyed(entry) else "flat, "
        form = "entry, " if writing[0] != reading[0] else within
    note = f"{_place_words(entry)}: {entry.text} written, {form}periods {_runs(entry.periods)}"
    return _checked_edit(shown, Gesture({path: after}, {path: before}, (), note, None, path, entry.address), texts, ((writing, reading),))


def _cable_move(shown: TrellisShown, event, pairs: list, texts) -> Gesture:
    """The `Gesture` of a drag that starts at a joined continuation port,
    the move of the reading end of the cable that port's route draws
    (design pass 10 §7; the brief, § Wires, cables and connections): the
    pairs `pairs`, each `(writing, reading)` of port records, become the
    event `moved` of the join wire whose field pairs the first writing port
    stands in, marked `cable`, each pair with the reading port its writing
    field leaves where the wire holds one, and `_moved_pairs` answers it.
    Where no join wire of the view holds that writing field, the sentence
    of `_joined_writing` stands, since the port is joined by a wire the
    view does not draw."""
    writing = pairs[0][0]
    for wire in _wire_joins(shown, texts, names=True):
        if wire["writing"] != (writing["h"], writing["key"]):
            continue
        left = {
            (pair.writing.h, pair.writing.key, pair.writing.field): pair.reading
            for pair in wire["pairs"]
        }
        if _field_of(writing) not in left:
            continue
        ports = {(port["side"], port["h"], port["key"], port["field"]): port["id"] for port in _field_ports(shown)}
        records = []
        for source, target in pairs:
            record = {"sourceHandle": source["id"], "targetHandle": target["id"]}
            use = left.get(_field_of(source))
            if use is not None:
                record["replaced"] = ports.get(("reading", use.h, use.key, use.field))
            records.append(record)
        moved = {
            "reading": event.get("reading"),
            "join": {name: wire[name] for name in ("source", "sourceHandle", "target", "targetHandle")},
            "end": "reading",
            "pairs": records,
            "cable": True,
        }
        return removal_edit(shown, moved, texts)
    return _joined_writing(shown, writing, texts)


def _frame_ports(shown: TrellisShown, event) -> list[tuple] | None:
    """The pairs `(writing, reading)` of ports, each its record of
    `_field_ports`, that the event `connected` of the join of two frames
    names (unit K's decision K-D8): where the event's `reading` names the
    source, the graph and the number of `shown`, and its `pairs` is a list
    of one or more records `{sourceHandle, targetHandle}`, each the id of a
    writing port and the id of a reading port of the view `shown` holds
    that stand for one state field each; the writing ports distinct and all
    of one stage occurrence, and the reading ports all of one other stage
    occurrence. None otherwise."""
    pairs = event.get("pairs") if _of_reading(shown, event) else None
    if not isinstance(pairs, list) or not pairs:
        return None
    ports = {port["id"]: port for port in _field_ports(shown)}
    found = []
    for pair in pairs:
        if not isinstance(pair, dict):
            return None
        handles = (pair.get("sourceHandle"), pair.get("targetHandle"))
        if not all(isinstance(handle, str) and handle in ports for handle in handles):
            return None
        source, target = (ports[handle] for handle in handles)
        if (source["side"], target["side"]) != ("writing", "reading"):
            return None
        found.append((source, target))
    writers = {(source["h"], source["key"]) for source, _ in found}
    readers = {(target["h"], target["key"]) for _, target in found}
    if len(writers) != 1 or len(readers) != 1 or writers == readers:
        return None
    if len({source["id"] for source, _ in found}) != len(found):
        return None
    return found


def _mapping_text(fields) -> str:
    """The mapping of the pairs `fields`, each `(continuation field, arrival
    field)`, written on one line in the flow form, `{m_next: m, a: k}`."""
    return "{" + ", ".join(f"{field}: {arrival}" for field, arrival in fields) + "}"


def _keyed(entry) -> bool:
    """Whether the line of the `ConnectorEntry` `entry` is written in the
    keyed form, or targets the `fields` mapping of a keyed connector."""
    return str(entry.address).endswith(".fields") or "fields" in entry_value(entry.text)


def _group_line(items: list, held) -> tuple[str, str, str]:
    """For the pairs `items` that the package places at one address, each
    `(entry, writing, reading, unjoined)`, with `held` the value that stands
    at that address (`_frame_edit`, step 3): the line typed there, its words
    in the note and the word of its form followed by a comma, empty where
    the line adds keys to a mapping that writes a join reaching each of its
    arrival fields (J-D42), as `connector_edit` writes them for one pair.
    Within a period, keys added to a connector that holds keys are the flat
    mapping of the pairs, the connector's form named, `keyed` where it is
    the `fields` of a keyed connector (unit L, Task 19)."""
    _, writing, reading, _ = items[0]
    fields = []
    for item in items:
        mapping = entry_value(item[0].text)
        fields.extend((mapping.get("fields") or mapping).items())
    flat = _mapping_text(fields)
    between = writing[0] != reading[0]
    words = ", ".join(f"{field}: {arrival}" for field, arrival in fields) if between else flat
    if not any(item[3] for item in items) and isinstance(held, dict) and held:
        return flat, words, ""
    if between:
        return flat, words, "entry, " if len(fields) == 1 else "entries, "
    if isinstance(held, dict) and held:
        # keys added to the connector the two occurrences share
        return flat, flat, "keyed, " if any(_keyed(item[0]) for item in items) else "flat, "
    return flat, flat, "flat, "


def _frame_edit(shown: TrellisShown, event, texts: dict) -> Gesture:
    """The `Gesture` of the event `connected` of the join of two frames,
    the button `join` of the list that a drag from the frame of one stage
    occurrence to the frame of another opens (unit K's decision K-D8; spec
    0.4 §3.1, §3.3): the pairs the author ticked there, typed as one
    mapping; `texts` is the mapping of unsaved texts. In order:

    1. Where `_frame_ports` reads no pairs from the event, or a file `shown`
       read now holds another text (`inputs_current`), the answer is "An
       old graph"; where a join already reads a writing port of a pair, the
       sentence `_joined_writing` gives for the first such port.
    2. The package's `connector_entry` names the file, the address and the
       form of each pair, as for a drag between its two ports; its reasons
       `port-joined` and `not-adjacent`, and a file it can no longer read,
       answer "An old graph", and its other reasons, for the first pair it
       refuses, the sentence `gesture_sentence` writes, nothing being typed
       for any pair.
    3. The pairs that the package places at one address form one line,
       typed there by the package's text writers (`_typed`): within a
       period the flat connector `{m_next: m, a: k}`, the keyed connector
       `{from: port, to: cons, fields: {m_next: m}}` where the package keys
       any of its pairs (§3.1), or the keys added to the mapping that
       writes a join reaching each of its arrival fields (J-D42) or to the
       connector the two stage occurrences already share
       (`connector_entry`; unit L, Task 19); between two periods the
       entries added to the inter-period mapping. A writer's refusal
       answers the sentence "An edit not applied".
    4. The note names, for each line, the file, the address, the text, its
       form and the periods it reaches, as `connector_edit`'s note does,
       with `entries` in place of `entry` for two or more entries:
       `trellis.yml, inter_connectors[0]: y_f_ret: y_f_r, y_p_ret: y_p_r
       written, entries, periods 0–14`; the notes of two lines are joined by
       a semicolon.

    The join of one pair answers what the drag between its two ports
    answers. Nothing is written: the edits are answered for the buffers."""
    pairs = _frame_ports(shown, event)
    if pairs is None or not inputs_current(shown, texts):
        return _old_graph(shown)
    joined = next((source for source, _ in pairs if not source["unjoined"]), None)
    if joined is not None:
        # pairs from a joined continuation port move its cable (design pass
        # 10 §7; `_cable_move`)
        return _cable_move(shown, event, pairs, texts)
    # the pairs by the resolved path of the file and the address the
    # package names for each, in the order of the pairs
    groups: dict[tuple, list] = {}
    for source, target in pairs:
        writing, reading = _field_of(source), _field_of(target)
        try:
            entry = connector_entry(shown.trellis, writing, reading, texts, selection=shown.selection)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # a file the reading read no longer reads as it read it
            return _old_graph(shown)
        if entry.reason in ("port-joined", "not-adjacent"):
            return _old_graph(shown)
        path = str(Path(entry.file).resolve())
        if entry.reason is not None:
            sentence = gesture_sentence(entry.reason, entry, writing, reading)
            return Gesture(None, None, (), None, sentence, path, entry.address)
        item = (entry, writing, reading, target["unjoined"])
        groups.setdefault((path, entry.address), []).append(item)
    read, edits, notes = {}, {}, []
    for (path, address), items in groups.items():
        entry, writing, reading, _ = items[0]
        try:
            if path not in read:
                read[path] = texts[path] if path in texts else _read_text(path)
                edits[path] = read[path]
            line, words, form = _group_line(items, entry_value(read[path], address))
            edits[path] = _typed(edits[path], entry._replace(text=line))
        except (OSError, ValueError, KeyError, TypeError):
            # a TypeError: a name of the line that YAML reads as no string
            sentence = gesture_sentence("not-applied", entry, writing, reading)
            return Gesture(None, None, (), None, sentence, path, address)
        notes.append(
            f"{_place_words(entry)}: {words} written, {form}periods {_runs(entry.periods)}"
        )
    path, address = next(iter(groups))
    return _checked_edit(shown, Gesture(edits, read, (), "; ".join(notes), None, path, address), texts, tuple((_field_of(w), _field_of(r)) for w, r in pairs))


# --- the drops of the trellis graph (spec 0.4 §§3.5, 3.6; unit J) ---

# the heading of the folder's own stages in the stage list: the list's
# heading for a trellis written as records (brief §5), and the section of
# those stages for a trellis read from a recipe (AAS, L-D9); the page's
# words, in sentence case (design pass 13 §3; C14)
_FOLDER_STAGES_HEADING = "This folder's stages"
# the headings of the sections of the stage list of a trellis read from a
# recipe, the corpus's templates and the stages of the library (AAS, L-D6)
_TEMPLATES_HEADING = "Templates"
_LIBRARY_HEADING = "Library"
# the hover text and the accessible name of a `+ period` control (spec 0.4
# §3.6; brief §5)
_ADD_A_PERIOD = "add a period"
# the target of a drop on the `+ period` control at the earliest end (spec
# 0.4 §3.2)
_EARLIEST_END = "earliest end"
# the target of a drop on the `+ period` control between two periods, the
# earlier in time first, `between periods[3] and periods[2]` (spec 0.4 §3.2)
_BETWEEN = re.compile(r"between periods\[(\d+)\] and periods\[(\d+)\]")
# the target of a drop on a period, its layer's id (spec 0.4 §3.2)
_PERIOD_LAYER = re.compile(r"periods\[(\d+)\]" + re.escape(LAYER_ID_ENDING))
# a period's layer, by its namespace in the graph JSON
_PERIOD_NAMESPACE = re.compile(r"periods\[(\d+)\]")
# the address of the `stages` of an entry of the trellis file's `periods`,
# as `written_at` answers it, with the entry's own address
_ENTRY_STAGES = re.compile(r"(periods\[\d+\])\.stages")
# The item that ends the stage list of a trellis read from a recipe, after
# the templates (unit K's decision K-D26): its id and its kind, `folder`, and
# its words, printed where an item prints its key; dropped on a period or
# sent to it, it opens the form "add stage" on a folder of the disk.
_FOLDER_ITEM = {
    "id": "folder",
    "kind": "folder",
    "key": "From a folder…",
    "title": "",
    "model_folder": "",
    "calibration": [],
    "periods_listed": [],
    "section": None,
}


def _text_at(path, texts) -> str:
    """The text of the file `path`: the text the mapping of unsaved texts
    `texts` holds for its resolved path, else the file's, read with its line
    ends as written (`_read_text`)."""
    resolved = str(Path(path).resolve())
    return texts[resolved] if resolved in texts else _read_text(resolved)


def _stage_places(shown: TrellisShown, texts) -> list:
    """For each period of the trellis `shown` holds, in order, the file and
    the address at which its `stages` are written, the place the package's
    `written_at` answers for `periods[h].stages` through the mapping of
    unsaved texts `texts`: a period file's `stages`, or the `stages` of an
    entry of the trellis file that writes its own (spec 0.4 §3.3, §3.5), so
    that the Workbench keeps no second reading of repeats, templates and
    overrides; None where it answers none."""
    file = shown.trellis["provenance"]["trellis"]["path"]
    count = len(shown.trellis["periods"])
    return [_place_of(file, f"periods[{h}].stages", texts) for h in range(count)]


def _listed(place, texts) -> set:
    """The stage keys the `stages` at `place`, `(file, address)`, write, read
    through the mapping of unsaved texts `texts`: the keys of a list of keys
    or of one-key mappings, or of a mapping of records; none where `place`
    is None or its stages cannot be read so."""
    if place is None:
        return set()
    try:
        value = entry_value(_text_at(place[0], texts), place[1])
    except (OSError, ValueError, KeyError):
        return set()
    if isinstance(value, dict):
        return set(value)
    if isinstance(value, list):
        return {key for item in value for key in (item if isinstance(item, dict) else [str(item)])}
    return set()


def _entries(places: list) -> list[list[int]]:
    """The periods each place of `places` writes together, one list for each
    place, in the order of its first period; a period with no place stands
    alone."""
    groups = {}
    for h, place in enumerate(places):
        groups.setdefault(place if place is not None else (None, h), []).append(h)
    return list(groups.values())


def _model_folder(shown: TrellisShown) -> Path:
    """The model folder of the trellis `shown`, a resolved path: the folder
    from which the source's path, relative to the folder, leads to the
    recipe or the trellis file its provenance names."""
    path = Path(shown.trellis["provenance"][shown.source.kind]["path"]).resolve()
    return path.parents[len(PurePosixPath(shown.source.path).parts) - 1]


def _recipe_of(shown: TrellisShown) -> tuple[Path, Path] | None:
    """The model folder and the recipe of the trellis `shown`, each a
    resolved path, for a trellis read from a recipe: the folder
    (`_model_folder`) and the recipe its provenance names; None for a
    trellis read from a trellis file."""
    if shown.source.kind != "recipe":
        return None
    return _model_folder(shown), Path(shown.trellis["provenance"]["recipe"]["path"]).resolve()


def _occurrence_stage(shown: TrellisShown, key: str):
    """The stage of the first occurrence of the key `key` in the trellis
    `shown` holds, the elaborated stage version a period's `stages` hold;
    None for a key no period of it holds."""
    for period in shown.trellis["periods"]:
        if key in period["stages"]:
            return period["stages"][key]
    return None


def _declared(shown: TrellisShown, key: str) -> list[str]:
    """The names of the parameters the stage `key` declares, which its
    calibration must give, as `creation.StageTemplate.calibration` names a
    template's: those of its first occurrence in the trellis `shown` holds
    (`_occurrence_stage`); none for a key no period of it holds (J-I166)."""
    stage = _occurrence_stage(shown, key)
    return list(stage.par.keys()) if stage is not None else []


def model_folder_name(stage: Path) -> str:
    """The name of the folder a template's stage file `stage` comes from,
    which the stage list prints after the template's key (AAS, L-D9): the
    model folder that holds it at `<model folder>/declaration/stages/<key>/`,
    the layout `creation.folder_template` reads, `portfolio-choice` for the
    corpus's `cons`; else the folder that holds the stage's own folder, the
    library's folder for a stage of the library."""
    folder = stage.parent
    in_layout = (
        folder.parent.name == "stages" and folder.parents[1].name == creation.FACTORY_FOLDER
    )
    return (folder.parents[2] if in_layout else folder.parent).name


def stage_items(folder: model.Folder, shown: TrellisShown, texts=None) -> dict:
    """The records of the stage list the forward trellis graph of `shown`
    opens from its head (spec 0.4 §3.5; brief §5; unit J's plan, Task 14),
    read through the mapping of unsaved texts `texts`: `heading`, None for a
    trellis read from a recipe and `This folder's stages` for a trellis
    written as records, the heading of the folder's own stages; `items`, the
    folder's own stages, then, for a trellis read from a recipe, the
    templates of the application corpus, the stages of the library (AAS,
    L-D6) and the item `From a folder…`; and `entries`, the periods each
    list of stages writes together, in the order of their first period,
    which the region marks together during a drag (§3.2).

    Each item is `{"id", "kind", "key", "title", "model_folder",
    "calibration", "periods_listed", "section"}`: for a stage of the folder,
    its key as `id` and `key`, the kind `stage`, the folder's title
    (`creation._model_title`), or, where the source is a variant's recipe
    `spec.<name>.yml`, that recipe's name, since a variant's labels come
    from its own recipe (unit L, Task 13; defect 19 of the UX simulation),
    and the folder's name, the parameters its stage file
    declares (`_declared`), the periods whose list holds it, and, for a
    trellis read from a recipe, the section `This folder's stages`, which a
    trellis written as records gives as the list's heading in its place; for
    a template (`creation.stage_templates`), its id, the kind `template`,
    the key it proposes, its model's title, the name of the folder its stage
    file comes from (`model_folder_name`), its parameters, no period and
    the section `Templates`; for a stage of the library
    (`creation.library_templates`), its full path as its id, the kind
    `library`, its folder's name as its key, its title, the name of the
    library's folder that holds it, its parameters, no period and the
    section `Library`; and for the item that opens the form "add stage" on a
    folder of the disk (unit K's decision K-D26), the id and the kind
    `folder`, its words `From a folder…` as its key, no title, no folder
    name, no parameter, no period and no section. The list prints each item
    on one line, the title and the parameters in its hover, and a section's
    heading line before its first item (AAS, L-D6, L-D9). The folder's
    stages are the keys of the recipe the source names
    (`creation.recipe_keys`), or, for a trellis written as records, the keys
    any period writes as records (`creation.record_stages`); each period's
    list is the place the package's `written_at` answers for its `stages`
    (`_stage_places`). A checkout that holds no corpus offers no template,
    and a library that does not exist no stage of the library."""
    texts = texts or {}
    places = _stage_places(shown, texts)
    lists = {place: _listed(place, texts) for place in places if place is not None}
    from_recipe = shown.source.kind == "recipe"
    if from_recipe:
        keys = creation.recipe_keys(folder.root, Path(shown.source.path).name, texts)
    else:
        keys = creation.record_stages(shown.trellis["provenance"]["trellis"]["path"], texts)
    recipe_name = Path(shown.source.path).name if from_recipe else None
    if recipe_name is not None and recipe_name != creation.RECIPE:
        title = recipe_name
    else:
        title = creation._model_title(folder.root)
    items = [
        {
            "id": key,
            "kind": "stage",
            "key": key,
            "title": title,
            "model_folder": folder.root.name,
            "calibration": _declared(shown, key),
            "periods_listed": [h for h, place in enumerate(places) if key in lists.get(place, ())],
            "section": _FOLDER_STAGES_HEADING if from_recipe else None,
        }
        for key in keys
    ]
    if from_recipe:
        try:
            templates = creation.stage_templates()
        except ValueError:
            templates = ()
        sections = (
            ("template", _TEMPLATES_HEADING, templates),
            ("library", _LIBRARY_HEADING, creation.library_templates()),
        )
        items += [
            {
                "id": template.id,
                "kind": kind,
                "key": template.key,
                "title": template.model,
                "model_folder": model_folder_name(template.stage),
                "calibration": list(template.calibration),
                "periods_listed": [],
                "section": heading,
            }
            for kind, heading, found in sections
            for template in found
        ]
        # a copy whose lists no other answer shares
        items.append(dict(_FOLDER_ITEM, calibration=[], periods_listed=[]))
    heading = None if from_recipe else _FOLDER_STAGES_HEADING
    return {"heading": heading, "items": items, "entries": _entries(places)}


def _periods_drawn(shown: TrellisShown) -> set[int]:
    """The periods whose layer the forward graph of the view `shown` holds,
    those the view's restriction leaves in it; none where that graph is
    refused."""
    for graph in shown.collection["graphs"]:
        if graph["id"] == _FORWARD:
            layers = graph.get("groupNodeAttributes") or {}
            return {
                int(found[1]) for name in layers if (found := _PERIOD_NAMESPACE.fullmatch(name))
            }
    return set()


def period_controls(shown: TrellisShown) -> list[dict]:
    """The `+ period` controls of the forward trellis graph of `shown` (spec
    0.4 §3.6; brief §5), each `{"target", "after", "name"}`: `target`, the
    target the event `dropped` names for it (§3.2), `earliest end` or
    `between periods[h] and periods[h−1]` written with the two numbers;
    `after`, the id of the layer of the period it stands beside,
    `periods[h]___group___`, the earlier of the two periods, or the earliest
    period for the control at the earliest end; and `name`, its hover text
    and accessible name, `add a period`. One control stands at the earliest
    end where the earliest period is drawn, and one between each two
    periods adjacent in the whole trellis that the view both draws, in the
    order of the periods from the earliest; none stands at the terminal end,
    since a period added after the terminal one is the author's to type."""
    count = len(shown.trellis["periods"])
    drawn = _periods_drawn(shown)
    places = [(_EARLIEST_END, count - 1)] if count - 1 in drawn else []
    places += [
        (f"between periods[{h}] and periods[{h - 1}]", h)
        for h in range(count - 1, 0, -1)
        if h in drawn and h - 1 in drawn
    ]
    return [
        {"target": target, "after": f"periods[{h}]{LAYER_ID_ENDING}", "name": _ADD_A_PERIOD}
        for target, h in places
    ]


def moved_ranges(folder: model.Folder, shown: TrellisShown, texts=None) -> list[str]:
    """Each range and range key of the recipe of `shown` that a period typed
    at the head of `periods`, a new terminal period, would move, which
    Details lists for the terminal period (spec 0.4 §3.6, decision 28):
    since such a period raises every period's index by one, every range
    `periods: [lo, hi]` a stage's block writes, `stages.port.periods: [0,
    5]`, and every range key `lo-hi` of its calibration, settings or methods
    lists, `stages.cons.calibration: 3-5`, as the recipe writes them and in
    its order, the forms the status line writes after an insertion. The
    recipe is read through the mapping of unsaved texts `texts`; none for a
    trellis written as records, which has no recipe, or a recipe that does
    not read."""
    if shown.source.kind != "recipe":
        return []
    try:
        stages = entry_value(recipe._text(folder, shown.source.path, texts), "stages")
    except (OSError, ValueError, KeyError):
        return []
    found = []
    for stage, block in stages.items() if isinstance(stages, dict) else ():
        for name, value in block.items() if isinstance(block, dict) else ():
            address = creation._dotted(("stages", stage, name))
            if name == "periods" and (bounds := creation._bounds(value)) is not None:
                found.append(f"{address}: [{bounds[0]}, {bounds[1]}]")
            elif name in creation.KINDS and isinstance(value, dict):
                found += [
                    f"{address}: {key}"
                    for key in value
                    if isinstance(key, str) and creation._RANGE_KEY.fullmatch(key)
                ]
    return found


def _dropped(shown: TrellisShown, event) -> tuple | None:
    """`(item, kind, h, control)` of the event `dropped` (spec 0.4 §3.2),
    where the event's `reading` names the source, the graph and the number
    of `shown` and its target names a period of the trellis or a `+ period`
    control `period_controls` draws on the whole trellis: for a drop on a
    period's layer, `periods[h]___group___`, its index `h` and `control`
    False; for a drop on a control, `control` True and `h` None at the
    earliest end, else the index the new period takes, the earlier of the
    two periods. A drop on a period needs an item and a kind, `stage`,
    `template`, `library` (AAS, L-D6) or `folder` (unit K's decision
    K-D26); Enter on a control sends no item, and its kind is then None.
    The item `From a folder…` chosen in the list the button `stages` opens
    is sent with no target,
    and answers `h` None and `control` False (AAS, L-D5). None otherwise, a
    record that is no event included."""
    if not isinstance(event, dict):
        return None
    drawn = event.get("reading")
    if not isinstance(drawn, dict):
        return None
    if any(drawn.get(name) != value for name, value in _drawn(shown).items()):
        return None
    target, item, kind = event.get("target"), event.get("item"), event.get("kind")
    if target is None and kind == "folder" and isinstance(item, str):
        return item, kind, None, False
    if not isinstance(target, str):
        return None
    count = len(shown.trellis["periods"])
    on_period, between = _PERIOD_LAYER.fullmatch(target), _BETWEEN.fullmatch(target)
    if on_period is not None and int(on_period[1]) < count:
        h, control = int(on_period[1]), False
    elif target == _EARLIEST_END:
        h, control = None, True
    elif (
        between is not None
        and 1 <= int(between[1]) < count
        and int(between[2]) == int(between[1]) - 1
    ):
        h, control = int(between[1]), True
    else:
        return None
    if control and item is None:
        return None, None, h, True
    if kind not in ("stage", "template", "library", "folder") or not isinstance(item, str):
        return None
    return item, kind, h, control


def _added_gesture(added, place) -> Gesture:
    """The `Gesture` of what a creation writer answered, `added`, a
    `creation.Added`, at `place`, `(file, address)`, the list of stages or
    the list of periods it edits: its edits, the texts it read, its new
    files, its notes joined by "; " as the status line and its restriction;
    no edit and no note where it answered none (ruling J-P16)."""
    path = str(Path(place[0]).resolve())
    if not added.edits:
        return Gesture(None, None, (), None, None, path, place[1])
    note = "; ".join(added.notes)
    return Gesture(
        added.edits, added.read, added.new_files, note, None, path, place[1], added.restriction
    )


def _refused(file: Path, root: Path, error) -> Gesture:
    """The `Gesture` of a text writer's refusal of an edit of `file`, which
    writes nothing: its sentence, the file by its path from the model folder
    `root` and the writer's reason, as the creation unit names a refused
    edit (`creation._edits`)."""
    reason = error.args[0] if isinstance(error, KeyError) else str(error)
    relative = Path(os.path.relpath(file, root)).as_posix()
    return Gesture(None, None, (), None, f"{relative}: {reason}", str(file), None)


# the word of the status line's note for a stage added with no connection
# selected (unit N, Task 5; design pass 10 §7)
UNCONNECTED = "unconnected"


def _template_stage(template):
    """The symbolic stage of the stage file of `template`, a
    `creation.StageTemplate`, as the package elaborates the file with no
    source bound (`elaborate_stage`): the fields a copy of it under another
    key declares, since a copy changes its `@stage:` line alone
    (`creation._stage_copy`); None where the package refuses the file or it
    cannot be read."""
    try:
        return elaborate_stage(load_stage(str(template.stage)), bind=False)
    except (OSError, *_REFUSALS):
        return None


def _joins_received(shown: TrellisShown, h: int, key: str, stage, texts) -> str | None:
    """Authored pairs selected when `stage` is added under `key` in period
    `h`, grouped by their source mapping. The source tokens retain any
    stage qualification. Inferred pairs have no source entry to name.
    The stage is added to every period whose list of stages is period
    `h`'s (`_stage_places`), as the list's edit adds it, so that a pair
    between two of those periods is found too; a pair is named once.
    Where the package selects no pair at all for the added occurrences,
    authored or inferred, the part is `<key> unconnected` (unit N, Task 5;
    design pass 10 §7), since its cards are then drawn with no wire."""
    trellis = _with_connectors(shown, texts)
    periods = trellis["periods"]
    if stage is None or not 0 <= h < len(periods) or key in periods[h]["stages"]:
        return None
    places = _stage_places(shown, texts)
    reached = {h} | {
        p for p, place in enumerate(places) if place is not None and place == places[h]
    }
    added = [
        {**period, "stages": {**period["stages"], key: stage}} if p in reached else period
        for p, period in enumerate(periods)
    ]
    try:
        selected = trellis_selection({**trellis, "periods": added})
    except _REFUSALS:
        return None
    occurrences = {(p, key) for p in reached}
    touching = [
        pair
        for pair in selected.pairs
        if {(pair.writing.h, pair.writing.key), (pair.reading.h, pair.reading.key)} & occurrences
    ]
    if not touching:
        return f"{key} {UNCONNECTED}"
    file = trellis["provenance"]["trellis"]["path"]
    found: dict[str, list[str]] = {}
    for pair in touching:
        written = f"{pair.source_key}: {pair.source_value}"
        if pair.origin == "authored" and written not in found.get(pair.source_address, ()):
            found.setdefault(pair.source_address, []).append(written)
    parts = []
    for address, pairs in found.items():
        place = _place_of(file, address, texts)
        name, written = (Path(place[0]).name, place[1]) if place else (Path(file).name, address)
        parts.append(f"{name}, {written}: {', '.join(pairs)} now join {key}")
    return "; ".join(parts) or None


def standing_mapping_joins(shown: TrellisShown | None, at, keys, texts) -> bool:
    """Whether the standing mapping remains valid at both interfaces of
    an inserted period. The proposed period reuses the held stages named
    by `keys`; the package selects and checks the complete proposal once.
    Unresolved entries and uncertified routes at either interface prevent
    preservation of the standing mapping."""
    if shown is None or isinstance(at, bool) or not isinstance(at, int):
        return False
    if not 1 <= at < len(shown.trellis["periods"]) or not inputs_current(shown, texts):
        return False
    trellis = _with_connectors(shown, texts)
    periods, mappings = trellis["periods"], trellis["inter_connectors"]
    stages = {}
    for key in keys:
        stage = next((p["stages"][key] for p in periods if key in p["stages"]), None)
        if stage is None:
            return False
        stages[key] = stage
    added = {"stages": stages, "connectors": [{}]}
    mapping = mappings[at - 1]
    proposed = {
        **trellis,
        "periods": periods[:at] + [added] + periods[at:],
        "inter_connectors": mappings[:at] + [mapping] + mappings[at:],
    }
    try:
        selected = trellis_selection(proposed)
    except _REFUSALS:
        return False
    addresses = (f"inter_connectors[{at - 1}]", f"inter_connectors[{at}]")
    if any(any(address in item.address for address in addresses) for item in selected.diagnostics):
        return False
    return all(
        route.status == "certified" for route in selected.routes
        if (route.source[0], route.destination[0]) in ((at, at - 1), (at + 1, at))
    )


def _with_joins_received(gesture, shown: TrellisShown, h: int, key: str, stage_of, texts):
    """The answer `gesture` of a drop that adds the stage `key` to period
    `h`, a `Gesture` or the form it opens, with the joins that entries
    already written give the stage (`_joins_received`) after its note,
    joined by "; ", the stage version answered by `stage_of()`, which is
    called only where the gesture writes; the answer itself where it writes
    nothing or no entry joins the stage."""
    if not isinstance(gesture, Gesture) or not gesture.edits:
        return gesture
    received = _joins_received(shown, h, key, stage_of(), texts)
    if received is None:
        return gesture
    return gesture._replace(note="; ".join(part for part in (gesture.note, received) if part))


def added_stage_joins(
    shown: TrellisShown | None, root, period_file: str, entry: str, key: str, template, texts
) -> str | None:
    """The joins that entries already written give a stage the form "add
    stage" adds (unit L, Task 14; defect 16 of the UX simulation), as the
    part of the form's status line that `_joins_received` writes: the stage
    `key`, a copy of `template`, a template's id or a
    `creation.StageTemplate`, a stage folder of the disk's among them,
    added to the list of stages of the entry `entry` of `period_file`, as
    the form names them (`_list_file_and_entry`) in the model folder
    `root`, at the first period whose list that is in the trellis `shown`,
    read through the mapping of unsaved texts `texts` (`list_period`). None
    where no trellis is shown, no period of it has that list or the template
    is not offered; where the package selects no pair for the stage, the
    part `<key> unconnected` (unit N, Task 5)."""
    if shown is None:
        return None
    try:
        if not isinstance(template, creation.StageTemplate):
            template = creation.template_of(template)
    except ValueError:
        return None
    h = list_period(shown, root, period_file, entry, texts)
    if h is None:
        return None
    return _joins_received(shown, h, key, _template_stage(template), texts)


def list_period(shown: TrellisShown, root, period_file: str, entry: str, texts) -> int | None:
    """The first period of the trellis `shown` whose list of stages is the
    `stages` of the entry `entry` of `period_file`, as the creation unit's
    `add_stage` names a list (`_list_file_and_entry`) in the model folder
    `root`, the empty entry for a period file's own `stages`, read through
    the mapping of unsaved texts `texts`; None where no period has that
    list. The Recipe tab's stage list adds an item there as a drop on that
    period does (unit N, Task 5)."""
    named = (period_file, entry)
    root = Path(root).resolve()
    return next(
        (
            p
            for p, place in enumerate(_stage_places(shown, texts or {}))
            if place is not None and _list_file_and_entry(root, place) == named
        ),
        None,
    )


def _records_drop(shown: TrellisShown, item, kind, h, control: bool, texts) -> Gesture:
    """The `Gesture` of a drop on the forward graph of `shown`, a trellis
    written as records with no recipe (spec 0.4 §3.5; J-D24): a folder stage
    on a period, the record another period writes for it copied into the
    period's `stages` (`creation.add_record_stage`); on a `+ period` control,
    an inline entry with a neighbor's stages and one empty connector mapping
    (`creation.add_record_period`), no form being opened, since no label is
    asked. A template, a stage of the library, the item `From a folder…`,
    or a key no period writes as a record, is no item the list offers, and
    answers "An old graph"; a refusal of the creation unit answers its own
    sentence. The note of a stage added names the joins that entries
    already written give it (`_with_joins_received`; unit L, Task 14)."""
    trellis_file = Path(shown.trellis["provenance"]["trellis"]["path"]).resolve()
    if kind in ("template", "library", "folder") or (
        item is not None and item not in creation.record_stages(trellis_file, texts)
    ):
        return _old_graph(shown)
    try:
        if control:
            added = creation.add_record_period(trellis_file, h, texts)
            return _added_gesture(added, (trellis_file, "periods"))
        added = creation.add_record_stage(trellis_file, item, h, texts)
    except ValueError as error:
        return Gesture(None, None, (), None, str(error), None, None)
    place = _place_of(trellis_file, f"periods[{h}].stages", texts)
    gesture = _added_gesture(added, place if place is not None else (trellis_file, None))
    return _with_joins_received(
        gesture, shown, h, item, lambda: _occurrence_stage(shown, item), texts
    )


def _folder_stage_drop(
    shown: TrellisShown, root: Path, recipe_path: Path, key: str, h: int, place, texts
) -> Gesture:
    """The `Gesture` of the recipe's stage `key` dropped on period `h` of
    the trellis `shown`, whose list of stages stands at `place` (spec 0.4
    §3.5; brief rule 1, its fourth row): no edit and no sentence where the
    list holds the key; otherwise the key appended to the list
    (`append_to_sequence`), and, where the recipe restricts the stage to a
    range that excludes `h`, the range widened to include it
    (`creation.range_widened`; ruling J-P8). The note names the list's file,
    its address, the key and every period the list writes, then the range
    written, in the forms of brief §5: `period.yml, stages: housing written,
    periods 1–5; spec.yml, stages.housing.periods: [1, 3] now [1, 4]`, and
    last the joins that entries already written give the stage by its
    fields' names, its version that of its first occurrence in the trellis
    (`_joins_received`; unit L, Task 14), `trellis.yml,
    periods[0].connectors[0]: a_s: a_bq, h_s: h_bq now join bequest`. A
    writer's refusal answers its sentence, and nothing is written."""
    path = Path(place[0]).resolve()
    if key in _listed(place, texts):
        return Gesture(None, None, (), None, None, str(path), place[1])
    reached = [p for p, other in enumerate(_stage_places(shown, texts)) if other == place]
    text = _text_at(path, texts)
    try:
        typed = append_to_sequence(text, place[1], key)
    except (KeyError, ValueError) as error:
        return _refused(path, root, error)
    edits, read = {str(path): typed}, {str(path): text}
    notes = [f"{path.name}, {place[1]}: {key} written, periods {_runs(reached)}"]
    written = _text_at(recipe_path, texts)
    try:
        widened, range_note = creation.range_widened(written, key, h)
    except (KeyError, ValueError) as error:
        return _refused(recipe_path, root, error)
    if range_note is not None:
        edits[str(recipe_path)], read[str(recipe_path)] = widened, written
        notes.append(f"{recipe_path.name}, {range_note}")
    gesture = Gesture(edits, read, (), "; ".join(notes), None, str(path), place[1])
    return _with_joins_received(
        gesture, shown, h, key, lambda: _occurrence_stage(shown, key), texts
    )


def _list_file_and_entry(root: Path, place) -> tuple[str, str]:
    """The period's list of stages at `place`, `(file, address)`, as the
    creation unit's `add_stage` names it for the model folder `root`: the
    name in the factory's folder of the file that writes the list, and the
    address of its entry there, the empty address for a period file's own
    `stages`."""
    folder = root / creation.FACTORY_FOLDER
    period_file = Path(os.path.relpath(Path(place[0]).resolve(), folder)).as_posix()
    found = _ENTRY_STAGES.fullmatch(place[1])
    return period_file, found[1] if found is not None else ""


def _template_drop(root: Path, recipe_path: Path, keys, template, place, texts) -> Gesture | dict:
    """The `Gesture` of the template `template`, a `creation.StageTemplate`
    of the corpus or of the library (AAS, L-D6), dropped on a period whose
    list of stages stands at `place` (spec 0.4 §3.5; brief rule 1, its fifth
    row): the edits "add stage" makes with the template's own key, in the
    file and at the entry of that list (`creation.add_stage`), the
    template's stage file and companions as new files, and, for a stage of
    the library, its origin in answers.yml where the folder holds it, as for
    a stage folder of the disk (unit K's decision K-D26). Where the recipe,
    whose keys are `keys`, or the stage folder holds the key, the form "add
    stage" opens with the name in the factory's folder of the file that
    writes the list and its entry (`_list_file_and_entry`), the key alone
    left to type: for a template of the corpus, `{"form": "add stage",
    "fill": {"template", "period", "entry"}}`, the template chosen; for a
    stage of the library, the form from a folder on the stage's folder,
    `{"form": "add stage", "fill": {"folder", "period", "entry"}}`. A
    refusal of the creation unit answers its own sentence."""
    period_file, entry = _list_file_and_entry(root, place)
    key = template.key
    if key in keys or (root / creation.factory_path(creation.stage_folder(key))).exists():
        if template.origin is None:
            fill = {"template": template.id, "period": period_file, "entry": entry}
        else:
            fill = {"folder": template.origin, "period": period_file, "entry": entry}
        return {"form": "add stage", "fill": fill}
    try:
        added = creation.add_stage(
            root, key, template, period_file, entry=entry, recipe=recipe_path.name, texts=texts
        )
    except (OSError, ValueError) as error:
        return Gesture(None, None, (), None, str(error), None, None)
    return _added_gesture(added, place)


def _recipe_drop(shown: TrellisShown, item, kind, h, control: bool, texts) -> Gesture | dict:
    """The answer to a drop on the forward graph of `shown`, a trellis read
    from a recipe (spec 0.4 §§3.5, 3.6): on a period, a folder stage
    (`_folder_stage_drop`), or a template or a stage of the library (AAS,
    L-D6), each copied as a template is (`_template_drop`), the period's
    list being the place the package's `written_at` answers for its
    `stages`; on a `+ period` control, the form "add period", `{"form": "add
    period", "fill": {"head", "at", "keys"}}`, headed by the place it adds
    at, `before periods[5]` at the earliest end or `between periods[3] and
    periods[2]`, with `at` the index the new period takes, None at the
    earliest end, and the dropped stage of the recipe chosen; a template, a
    stage of the library or the item `From a folder…` dropped there, or
    Enter on the control, chooses none. The item `From a folder…` dropped on
    a period opens the form "add stage" on a folder of the disk
    (`_disk_folder_form`), and chosen in the list the button `stages` opens,
    with no period, the same form with the periods to choose from
    (`_periods_folder_form`). A key the recipe does not hold, an id no
    template has, an id that is the path of no stage of the library
    (`creation.library_templates`), or a kind `folder` with another id than
    the item's, is no item the list offers, and answers "An old graph"."""
    root, recipe_path = _recipe_of(shown)
    keys = creation.recipe_keys(root, recipe_path.name, texts)
    template = None
    if kind == "stage" and item not in keys:
        return _old_graph(shown)
    if kind == "folder" and item != _FOLDER_ITEM["id"]:
        return _old_graph(shown)
    if kind == "template":
        try:
            template = creation.template_of(item)
        except ValueError:
            return _old_graph(shown)
    if kind == "library":
        template = next((each for each in creation.library_templates() if each.id == item), None)
        if template is None:
            return _old_graph(shown)
    if control:
        count = len(shown.trellis["periods"])
        if h is None:
            head = f"before periods[{count - 1}]"
        else:
            head = f"between periods[{h}] and periods[{h - 1}]"
        chosen = [item] if kind == "stage" else []
        return {"form": "add period", "fill": {"head": head, "at": h, "keys": chosen}}
    if h is None:
        # the item `From a folder…` of the list `stages` opens (L-D5)
        return _periods_folder_form(shown, root, texts)
    place = _place_of(
        shown.trellis["provenance"]["trellis"]["path"], f"periods[{h}].stages", texts
    )
    if place is None:
        return _old_graph(shown)
    if kind == "folder":
        return _disk_folder_form(root, place)
    if template is None:
        return _folder_stage_drop(shown, root, recipe_path, item, h, place, texts)
    dropped = _template_drop(root, recipe_path, keys, template, place, texts)
    # a copy changes the stage file's `@stage:` line alone, so the joins it
    # receives are those of the template's fields (unit L, Task 14)
    return _with_joins_received(
        dropped, shown, h, template.key, lambda: _template_stage(template), texts
    )


def _disk_folder_form(root: Path, place) -> dict:
    """The form "add stage" that the item `From a folder…` of the stage list
    opens when it is dropped on a period, or sent to it, whose list of
    stages stands at `place` (unit K's decision K-D26; the plan of unit K,
    Task 25): `{"form": "add stage", "fill": {"folder", "period",
    "entry"}}`, the folder of the disk the form's chooser opens on, the
    first folder of the library where one exists (`creation.library_folders`;
    AAS, L-D6), else the folder that holds the model folder `root`, beside
    which the author's other projects stand, and the period's list as a
    template's form names it (`_list_file_and_entry`). Nothing is read from
    that folder here."""
    period_file, entry = _list_file_and_entry(root, place)
    libraries = creation.library_folders()
    opening = libraries[0] if libraries else root.parent
    return {
        "form": "add stage",
        "fill": {"folder": str(opening), "period": period_file, "entry": entry},
    }


def _periods_folder_form(shown: TrellisShown, root: Path, texts) -> Gesture | dict:
    """The form "add stage" that the item `From a folder…` opens when it is
    clicked, or chosen with Enter, in the list the button `stages` opens,
    which names no period (AAS, L-D5): `{"form": "add stage", "fill":
    {"folder", "periods"}}`, the folder the form of a drop on a period opens
    on, and for each period the forward graph of `shown` draws, the
    terminal period first, `{"name", "period", "entry"}`, its name,
    `periods[0]`, and its list of stages as the form of a drop on its layer
    names it (`_disk_folder_form`), among which the form's select `period`
    chooses. A period whose list the package places nowhere is left out;
    where none is left, the answer is "An old graph"."""
    file = shown.trellis["provenance"]["trellis"]["path"]
    fills = []
    for h in sorted(_periods_drawn(shown)):
        place = _place_of(file, f"periods[{h}].stages", texts)
        if place is not None:
            fills.append((h, _disk_folder_form(root, place)["fill"]))
    if not fills:
        return _old_graph(shown)
    periods = [
        {"name": f"periods[{h}]", "period": fill["period"], "entry": fill["entry"]}
        for h, fill in fills
    ]
    return {"form": "add stage", "fill": {"folder": fills[0][1]["folder"], "periods": periods}}


def drop_edits(shown: TrellisShown, event, texts, refused: bool = False) -> Gesture | dict:
    """The answer to the event `dropped`, a stage of the stage list dropped
    on a period or on a `+ period` control of the forward trellis graph
    drawn from the reading `shown`, Enter on such a control, or the item
    `From a folder…` chosen in the list the button `stages` opens, which
    names no period (AAS, L-D5), a function of its arguments that reads no
    state of the page, writes nothing and raises nothing (spec 0.4 §§3.2,
    3.3, 3.5, 3.6; brief rules 1, 6 and 9).
    `texts` is the mapping of every unsaved buffer of the tab, by resolved
    path. The answer is a `Gesture`, as `connector_edit` answers one, or,
    where the drop opens one of the creation unit's forms, `{"form": "add
    stage" | "add period", "fill": {…}}`, the form's own refusals then
    standing in the form.

    The event is checked as a connector's is: where its `reading` names
    another source, graph or elaboration number than `shown`, where a file
    `shown` read now holds another text (`inputs_current`), or where its
    target, kind or item names nothing the graph and its stage list offer
    (`_dropped`), the answer is the sentence "An old graph". `refused` says
    that `shown` is the last graph the package constructed and that the
    reading of the texts `texts` stands refused (unit L, Task 14; defect 2
    of the UX simulation): the stage list then opens on that graph, and a
    drop on a period, or the item `From a folder…` sent with no period, is
    admitted though the texts differ from those `shown` read, and edits
    them as any drop does, since the period's list is read from them; a
    drop on a `+ period` control, which does not act while the reading
    stands refused, is still "An old graph". The period's
    list is the place the package's `written_at` answers for its `stages`,
    so that the Workbench keeps no second reading of templates and repeats.
    For a trellis read from a recipe, `_recipe_drop`; for a trellis written
    as records, `_records_drop`. A drop that writes nothing, a stage the
    period's list already holds, answers a gesture with no edit and no
    sentence (ruling J-P16); a refusal of the creation unit or of a text
    writer answers its sentence, and nothing is written."""
    texts = texts or {}
    dropped = _dropped(shown, event)
    if dropped is None:
        return _old_graph(shown)
    on_period = not dropped[3]
    if not (refused and on_period) and not inputs_current(shown, texts):
        return _old_graph(shown)
    try:
        if shown.source.kind == "recipe":
            return _recipe_drop(shown, *dropped, texts)
        return _records_drop(shown, *dropped, texts)
    except (OSError, UnicodeDecodeError):
        # a file the reading read can no longer be read as text
        return _old_graph(shown)


# --- the removal and the move of a join (spec 0.4 §3.1; unit J, Task 19) ---

# an address that names an item of a list, `periods[0].connectors[2]`: the
# list's address and the item's index
_ITEM = re.compile(r"(.*)\[(\d+)\]")
# a line break as the package's reader of YAML files counts lines
_LINE_BREAKS = re.compile(r"\r\n|[\r\n\x85  ]")


# --- what the model lacks, as the folder's checklist lists it (unit K) ---

# The note the factory adds to the refusal of a binding, naming the stage
# occurrence refused, `Stage occurrence: periods[0].stages['disc']`: the
# period's index, the quote and the stage's key.
_OCCURRENCE_NOTE = re.compile(
    r"^Stage occurrence: periods\[(\d+)\]\.stages\[(['\"])(.*)\2\]$", re.MULTILINE
)
# The note the factory adds to a refusal of the construction of a stage
# text, naming the stage occurrences that hold that text, `Affected stage
# occurrences: periods[4].stages['contribution'], periods[5].stages[…]`: the
# first occurrence's period index, the quote and the stage's key.
_CONSTRUCTION_NOTE = re.compile(
    r"^Affected stage occurrences: periods\[(\d+)\]\.stages\[(['\"])(.*?)\2\]", re.MULTILINE
)


def without_occurrence(sentence: str) -> str:
    """`sentence`, a refusal's sentence, with the line the factory adds
    naming the stage occurrence refused (`_OCCURRENCE_NOTE`) or the stage
    occurrences whose text it refused to construct (`_CONSTRUCTION_NOTE`)
    taken out, so that one refusal reads as one sentence (unit L, Task 21;
    defects 17 and 18 of the UX simulation): a binding's, which a stage's
    binding gives without that line and the trellis's binding with it, and
    a stage text's, which the loop gives without that line and the
    trellis's reading with it; `sentence` itself where it holds no such
    line."""
    lines = sentence.split("\n")
    return "\n".join(
        line
        for line in lines
        if not (_OCCURRENCE_NOTE.fullmatch(line) or _CONSTRUCTION_NOTE.match(line))
    )


def _place_or_first_line(
    folder: model.Folder, file, address: str | None, expanded: bool, texts
) -> tuple[str, int]:
    """The file, relative to the folder, and the line at which `file` writes
    `address`, as `address_place` answers them; the file's first line where
    no address is given or the file writes none there."""
    found = address_place(folder, file, address, expanded, texts)
    return found if found is not None else (recipe.relative(folder, file), 1)


def _missing_fields(shown: TrellisShown) -> dict:
    """Unjoined arrival fields of the whole model, grouped by stage and name.

    Initial-period inputs are exterior fields, not missing internal joins.
    The native report uses the held selection, independently of the graph
    drawn or its restriction. No stage is constructed or bound here.
    """
    report = connection_report(shown.trellis, selection=shown.selection)
    held = {}
    for h, key, field in report.unjoined["internal"]["reading"]:
        held.setdefault((key, field), set()).add(h)
    return held


def unjoined_count(shown: TrellisShown) -> int:
    """The distinct unjoined internal arrival fields of the whole model."""
    return len(_missing_fields(shown))


def missing_joins(folder: model.Folder, shown: TrellisShown, texts=None) -> list[dict]:
    """The whole model's unjoined arrival fields and their connector sources,
    by the native report's rule of `_missing_fields`. One record for each stage key and
    field, in the order of the graph's ports, `{"key", "field", "periods",
    "file", "line"}`: the periods at which the field is unjoined, as
    ranges, `0–4`, and the file, relative to the folder, and the line of
    the `connectors` list of the first of them, where a join within that
    period is written, else the trellis file's first line. The trellis file
    and the period files are read through `texts`, the mapping of unsaved
    texts (spec 0.4 §3.1)."""
    file = shown.trellis["provenance"]["trellis"]["path"]
    found = []
    for (key, field), periods in _missing_fields(shown).items():
        address = f"periods[{min(periods)}].connectors"
        path, line = _place_or_first_line(folder, file, address, True, texts)
        found.append(
            {
                "key": key,
                "field": field,
                "periods": _runs(sorted(periods)),
                "file": path,
                "line": line,
            }
        )
    return found


def refused_bindings(folder: model.Folder, shown: TrellisShown, texts=None) -> list[dict]:
    """The bindings the package refused in the reading `shown`
    (`TrellisBinding.failed`), in the verbs' order, which the folder's
    checklist lists (unit K's decision K-D10): each `{"kind", "key",
    "sentence", "file", "line"}`, the kind of the binding; the key of the
    stage occurrence the package's note names (`_OCCURRENCE_NOTE`), None
    where none is named; the package's sentence, as `binding_notes` gives
    it; and the file, relative to the folder, and the line at which the
    source names the sources of that kind for that occurrence, a recipe's
    `stages.<key>.<kind>` or a trellis file's `periods[h].stages.<key>.<kind>`
    where that file or its period file writes it, else the source's first
    line. The files are read through `texts`, the mapping of unsaved
    texts."""
    source = str(folder.root / shown.source.path)
    found = []
    for verb, kind in _TRELLIS_VERBS:
        sentence = shown.binding.failed.get(verb)
        if sentence is None:
            continue
        named = _OCCURRENCE_NOTE.search(sentence)
        key = named[3] if named else None
        if named is None:
            address, expanded = None, False
        elif shown.source.kind == "recipe":
            address, expanded = f"stages.{key}.{kind}", False
        else:
            address, expanded = f"periods[{named[1]}].stages.{key}.{kind}", True
        path, line = _place_or_first_line(folder, source, address, expanded, texts)
        places = []
        if named is not None:
            record = shown.syntactic["periods"][int(named[1])]["stages"][key]
            entries = record.get("provenance", {}).get("source_lists", {}).get(kind, ())
            for entry in entries:
                if supplied := entry.get("path"):
                    places.append(_place_or_first_line(folder, supplied, kind, False, texts))
        places.append((path, line))
        found.append({"kind": kind, "key": key, "sentence": sentence, "file": path,
                      "line": line, "places": tuple(dict.fromkeys(places))})
    return found


class _Entry(NamedTuple):
    """The entry of a file that writes one join of the trellis (J-D33):
    `path`, the file's resolved path; `item`, the address of the connector's
    item in a `connectors` list, None for an inter-period mapping;
    `mapping`, the address of the mapping whose key `key` writes the join,
    the item itself for a flat connector, its `fields` for a keyed one, or
    the inter-period mapping; `field` and `arrival`, the two fields the join
    joins; `key` and `value`, their exact authored endpoint spellings; and
    `periods`, the periods the entry reaches."""

    path: str
    item: str | None
    mapping: str
    key: str
    arrival: str
    periods: tuple
    field: str
    value: str


def _name_joins(shown: TrellisShown, writer, reader) -> tuple[str, ...]:
    """The inferred arrival fields between two occurrences in this reading."""
    return tuple(
        p.reading.field for p in shown.selection.pairs
        if p.origin == "inferred"
        and (p.writing.h, p.writing.key) == writer
        and (p.reading.h, p.reading.key) == reader
    )


def _position_of(shown: TrellisShown, positions: dict, node_id: str):
    """The position `(h, key)` of the stage occurrence that holds the node
    `node_id` of the forward graph of the view `shown` holds, as
    `node_place` places it; None for a node it places in no occurrence."""
    try:
        return positions.get(node_place(shown.collection, _FORWARD, node_id).occurrence)
    except (KeyError, ValueError):
        return None


def _pair_entries(shown: TrellisShown, writer, reader, places: dict, texts, pairs=None) -> list[_Entry]:
    """The exact source entries of selected authored pairs between two
    occurrences, restricted to `pairs` when supplied. Source tokens and
    resolved field names remain distinct."""
    periods, file = shown.trellis["periods"], shown.trellis["provenance"]["trellis"]["path"]

    def place(address):
        if address not in places:
            places[address] = _place_of(file, address, texts)
        return places[address]

    found = []
    for pair in shown.selection.pairs if pairs is None else pairs:
        if pair.origin != "authored" or (pair.writing.h, pair.writing.key) != writer or (
            pair.reading.h, pair.reading.key
        ) != reader:
            continue
        at = place(pair.source_address)
        if at is None:
            continue
        hw, hr = pair.writing.h, pair.reading.h
        if hw == hr:
            item = place(pair.address)
            lists = [place(f"periods[{h}].connectors") for h in range(len(periods))]
            reached = tuple(h for h in range(len(periods)) if lists[h] == lists[hw])
        else:
            item = None
            mappings = [place(f"inter_connectors[{h}]") for h in range(len(periods) - 1)]
            reached = tuple(_pairs_reached(mappings, hr))
        found.append(_Entry(
            str(Path(at[0]).resolve()), item[1] if item else None, at[1],
            pair.source_key, pair.reading.field, reached,
            pair.writing.field, pair.source_value,
        ))
    return found


def _edge_route(edge: dict) -> dict | None:
    """The record of the route an edge of the graph JSON carries under the
    package's `ROUTE_KEY` (design pass 10 §6; unit N, Task 6): its branch,
    its two occurrences, its two state tuples, its pairs, its status and
    its law; None for an edge no route establishes."""
    held = edge.get("attrs") or []
    return next((pair["value"] for pair in held if pair["key"] == ROUTE_KEY), None)


def _pairs_by_wire(shown: TrellisShown) -> dict:
    """Selected pairs by source measure port and destination occurrence,
    `(port id, (h, key))`, for each edge of the forward graph the view
    `shown` holds that carries a route's record (`_edge_route`): the pairs
    the record names, each the native pair of the selection with its two
    uses, in the selection's order. No index outlives the query."""
    uses = {
        (
            f"periods[{pair.writing.h}]/{pair.writing.key}",
            pair.writing.field,
            f"periods[{pair.reading.h}]/{pair.reading.key}",
            pair.reading.field,
        ): (order, pair)
        for order, pair in enumerate(shown.selection.pairs)
    }
    positions, found = occurrence_positions(shown), {}
    for graph in shown.collection["graphs"]:
        if graph["id"] != _FORWARD:
            continue
        for node in graph["nodes"]:
            for edge in node.get("incomingEdges") or []:
                route = _edge_route(edge)
                if route is None or route["destination"] not in positions:
                    continue
                key = (edge["sourceNodeOutputId"], positions[route["destination"]])
                if key in found:
                    continue
                source, destination = route["source"], route["destination"]
                named = [
                    (source, pair["source_field"], destination, pair["destination_field"])
                    for pair in route["pairs"]
                ]
                held = sorted(uses[each] for each in named if each in uses)
                found[key] = tuple(pair for _, pair in held)
    return found


def _pairs_text(pairs) -> str:
    """The native drawing labels of the selected pairs, each printed once."""
    ordered = pairs
    if pairs and all(pair.writing.h == pair.reading.h for pair in pairs):
        ordered = sorted(pairs, key=lambda p: (p.writing.key, p.writing.field, p.reading.key, p.reading.field))
    return "; ".join(dict.fromkeys(
        (f"{pair.address} " if pair.writing.h != pair.reading.h else "")
        + join_label({"from": (pair.writing.key, pair.writing.field),
                      "to": (pair.reading.key, pair.reading.field)})
        for pair in ordered
    ))


def _wire_joins(shown: TrellisShown, texts, names: bool = False) -> list[dict]:
    """Each wire of the forward graph the view `shown` holds that carries a
    route's record (`_edge_route`; unit N, Task 6) and a join written by an
    entry of a file, `{"source", "sourceHandle", "target", "targetHandle",
    "join", "writing", "reading", "entries"}`: the wire's two nodes and two
    ports, by their ids in the graph JSON; the join labels of the pairs its
    route's record names (`_pairs_by_wire`); the positions `(h, key)` of the
    writing and of the reading stage occurrence; and the entries that write
    this wire's selected pairs (`_pair_entries`), read through the mapping
    of unsaved texts `texts`. A wire whose joins are all by equal names,
    which no entry writes, is left out, and with `names` it is kept, its
    entries none (unit L, Task 15; `_name_joins`)."""
    positions, places, entries, found = occurrence_positions(shown), {}, {}, []
    occurrence, carried = {}, _pairs_by_wire(shown)

    def position(node_id):
        if node_id not in occurrence:
            occurrence[node_id] = _position_of(shown, positions, node_id)
        return occurrence[node_id]

    for graph in shown.collection["graphs"]:
        if graph["id"] != _FORWARD:
            continue
        for node in graph["nodes"]:
            for edge in node.get("incomingEdges") or []:
                if _edge_route(edge) is None:
                    continue
                writer, reader = position(edge["sourceNodeId"]), position(node["id"])
                if writer is None or reader is None or writer == reader:
                    continue
                key = (edge["sourceNodeOutputId"], reader)
                pairs = carried.get(key, ())
                if key not in entries:
                    entries[key] = _pair_entries(shown, writer, reader, places, texts, pairs)
                if not entries[key] and (not names or not pairs):
                    continue
                found.append(
                    {
                        "source": edge["sourceNodeId"],
                        "sourceHandle": edge["sourceNodeOutputId"],
                        "target": node["id"],
                        "targetHandle": edge["targetNodeInputId"],
                        "join": _pairs_text(pairs),
                        "writing": writer,
                        "reading": reader,
                        "entries": entries[key],
                        "pairs": pairs,
                        "route": _edge_route(edge),
                    }
                )
    return found


def _pair_joins(wires: list[dict]) -> list[dict]:
    """The pairs of periods of the join wires `wires`, as `_wire_joins`
    answers them, whose wires the graph region draws as one between the two
    periods (unit K's decision K-D5): for each port of a stage occurrence
    that two or more wires from occurrences of the period before it in time
    read, `{"source", "sourceHandle", "target", "targetHandle", "join",
    "writing", "reading", "entries", "members"}`: the writers' period's
    namespace, `periods[2]`, and no port; the reading node and port, by
    their ids in the graph JSON; the reading port's join text; the position
    `(h, None)` of the writers' period and `(h, key)` of the reading
    occurrence; the entries that write the joins of every wire, each once;
    and those wires."""
    groups = {}
    for wire in wires:
        if wire["writing"][0] == wire["reading"][0]:
            continue
        # the writers' period and the reading port
        key = (wire["writing"][0], wire["target"], wire["targetHandle"])
        groups.setdefault(key, []).append(wire)
    return [
        {
            "source": f"periods[{h}]",
            "sourceHandle": None,
            "target": target,
            "targetHandle": handle,
            "join": _pairs_text(tuple(pair for member in members for pair in member["pairs"])),
            "writing": (h, None),
            "reading": members[0]["reading"],
            "entries": list(dict.fromkeys(e for member in members for e in member["entries"])),
            "members": members,
            "route": None,
        }
        for (h, target, handle), members in groups.items()
        if len(members) > 1
    ]


def _entry_places(folder: model.Folder, entries, texts) -> list[tuple[str, str, int]]:
    """For each place of a file that writes an entry of `entries`, once and
    in their order, `(path, address, line)`: the file relative to the
    folder `folder`, the address of the entry's connector item or of its
    mapping, and the line at which that address stands (`address_place`),
    read through the mapping of unsaved texts `texts`; a place whose line
    cannot be found is left out."""
    found = []
    for path, address in dict.fromkeys(
        (entry.path, entry.item or entry.mapping) for entry in entries
    ):
        place = address_place(folder, path, address, False, texts=texts)
        if place is not None:
            found.append((place[0], address, place[1]))
    return found


def _field_pairs(wire: dict) -> list[tuple]:
    """The native selected pairs of a wire and their occurrence positions."""
    return [
        (pair, member["writing"], member["reading"])
        for member in wire.get("members") or [wire]
        for pair in member["pairs"]
    ]


def _proposed_reading(names, fields: dict) -> str | None:
    """The id of the arrival field's port, of `fields`, arrival fields of
    one stage occurrence by name, whose name comes first in `names`
    (`pairing_names` of a continuation field, after the arrival field's own
    name for a field pair moved); None where no name pairs."""
    return next((fields[name] for name in names if name in fields), None)


def _proposed_writing(arrival: str, fields: dict, labels: tuple, taken: set) -> str | None:
    """The id of the continuation field's port, of `fields`, the unjoined
    continuation fields of one stage occurrence by name, whose name pairs
    with the arrival field `arrival` (`pairing_names` under the branch
    labels `labels` of the occurrence's stage) with the fewest suffixes
    dropped, the first in the occurrence's order where two do; a port of
    `taken`, which another field pair of the wire proposes, is not
    proposed, since a continuation field joins one arrival field (J-D41).
    None where no name pairs."""
    ranked = [
        (pairing_names(field, labels).index(arrival), order, port)
        for order, (field, port) in enumerate(fields.items())
        if port not in taken and arrival in pairing_names(field, labels)
    ]
    return min(ranked)[2] if ranked else None


def _move_fields(
    wire: dict, ports: dict, free: dict, reads: dict, labels_of, sets_of
) -> list[dict] | None:
    """The field pairs of the join wire `wire`, or of the piece of a pair of
    periods (`_field_pairs`), as the list a move of its end opens lists
    them (unit K's decision K-D23): for each, `{"writing", "reading",
    "field", "arrival", "field_set", "arrival_set", "readers", "writers"}`,
    the ids of the ports of its continuation field and of its arrival field
    in the graph JSON, the two fields' names, their declared sets, which the
    list prints beside them, as `sets_of(h, key, side)` answers them
    (`_field_sets`; unit K's decision K-D25), and the ports a move proposes,
    by the namespace of the stage occurrence that holds them,
    `periods[0]/tenure`: `readers`, for a moved reading end, the arrival
    field of each occurrence of the reading end's period, another than the
    writer where the wire stays within a period, joined or not, that bears
    the name of the pair's own arrival field, else whose name pairs with
    the continuation field's; and `writers`, for a moved writing end, the
    unjoined continuation field of each occurrence of the writing end's
    period, another than the reader where the wire stays within a period,
    that bears the name of the pair's own continuation field, else whose
    name pairs with the arrival field's, none for a pair's piece, whose
    writing end does not move. The pairing is K-D8's (`pairing_names`); a
    move ticks by name, the end moved keeping its field's name where the
    occurrence dropped on holds it, and a reading port that joins reach is
    proposed as an unjoined one is (unit L, Task 19; defect 13 of the UX
    simulation; rows K-I215 and K-I216 amended). The port a pair already
    joins is never proposed for it. `ports` holds the field ports of the
    view by `(side, h, key, field)`, `free` the unjoined ones by `(side,
    h)`, then by occurrence key, then by field, `reads` every reading port,
    joined or not, by period, then by occurrence key, then by field, and
    `labels_of(h, key)` answers the branch labels of an occurrence's stage
    (`_stage_labels`). None where a field of the wire has no port in the
    view."""
    piece, found, taken = "members" in wire, [], {}
    for entry, (hw, kw), (hr, kr) in _field_pairs(wire):
        writing = ports.get(("writing", hw, kw, entry.writing.field))
        reading = ports.get(("reading", hr, kr, entry.reading.field))
        if writing is None or reading is None:
            return None
        names = (entry.reading.field, *pairing_names(entry.writing.field, labels_of(hw, kw)))
        readers = {}
        for key, fields in reads.get(hr, {}).items():
            offered = {name: port for name, port in fields.items() if port != reading["id"]}
            port = None if hw == hr and key == kw else _proposed_reading(names, offered)
            if port is not None:
                readers[f"periods[{hr}]/{key}"] = port
        writers, candidates = {}, {} if piece else free.get(("writing", hw), {})
        for key, fields in candidates.items():
            namespace = f"periods[{hw}]/{key}"
            held = taken.setdefault(namespace, set())
            own = fields.get(entry.writing.field)
            port = (
                None
                if hw == hr and key == kr
                else own
                if own is not None and own not in held
                else _proposed_writing(entry.reading.field, fields, labels_of(hw, key), held)
            )
            if port is not None:
                writers[namespace] = port
                held.add(port)
        found.append(
            {
                "writing": writing["id"],
                "reading": reading["id"],
                "field": entry.writing.field,
                "arrival": entry.reading.field,
                "field_set": sets_of(hw, kw, "writing").get(entry.writing.field, ""),
                "arrival_set": sets_of(hr, kr, "reading").get(entry.reading.field, ""),
                "readers": readers,
                "writers": writers,
            }
        )
    return found


def _backward_join_wires(shown: TrellisShown, graph: str) -> list[dict]:
    """The records of the cables of the graph `graph` of the view `shown`,
    the backward graph, as `join_wires` answers them with that graph: one
    per edge that carries a route's record (`_edge_route`), the edge's two
    nodes and two ports by their ids in the graph JSON, each edge once, the
    route's source and destination as `from` and `to` and as the positions
    `writing` and `reading`, its pairs' text as `join`, its branch and its
    status, and no movable end, no field pair and nothing removable."""
    found, seen = [], set()
    for held in shown.collection["graphs"]:
        if held["id"] != graph:
            continue
        for node in held["nodes"]:
            for edge in node.get("incomingEdges") or []:
                route = _edge_route(edge)
                ids = (edge["sourceNodeId"], edge["sourceNodeOutputId"], node["id"], edge["targetNodeInputId"])
                if route is None or ids in seen:
                    continue
                seen.add(ids)
                source, destination = route["source"], route["destination"]
                writer = _OCCURRENCE_ADDRESS.match(source)
                reader = _OCCURRENCE_ADDRESS.match(destination)
                if writer is None or reader is None:
                    continue
                found.append(
                    {
                        "source": edge["sourceNodeId"],
                        "sourceHandle": edge["sourceNodeOutputId"],
                        "target": node["id"],
                        "targetHandle": edge["targetNodeInputId"],
                        "join": "; ".join(
                            f"{pair['source_field']} → {pair['destination_field']}" for pair in route["pairs"]
                        ),
                        "from": source,
                        "to": destination,
                        "writing": {"h": int(writer.group(1)), "key": writer.group(2)},
                        "reading": {"h": int(reader.group(1)), "key": reader.group(2)},
                        "between": writer.group(1) != reader.group(1),
                        "movable": [],
                        "fields": [],
                        "others": [],
                        "file": None,
                        "removable": False,
                        "branch": route.get("branch"),
                        "status": route.get("status"),
                        "graph": graph,
                    }
                )
    return found


# the address of a stage occurrence in the graph JSON, `periods[2]/tenure`,
# its period's index and its key
_OCCURRENCE_ADDRESS = re.compile(r"^periods\[(\d+)\]/([^/]+)$")


def join_wires(shown: TrellisShown, texts=None, graph: str = _FORWARD) -> list[dict]:
    """The join wires of the forward trellis graph the view `shown` holds,
    which the graph region lets the reader select, remove and move (unit
    J's decisions J-D33 and J-D39; amendment 02, ruling 11): each wire
    that carries a route's record (`_wire_joins`), read through the
    mapping of unsaved texts `texts`, as `{"source", "sourceHandle",
    "target", "targetHandle", "join", "from", "to", "writing", "reading",
    "between", "movable", "fields", "others", "file", "removable",
    "branch", "status"}`: the wire's nodes and ports by their ids in the
    graph JSON; the join's name; the branch of its route and the route's
    status, as the record its edge carries names them, which the cable's
    label and Details print (design pass 10 §§6 and 8); the addresses of its two stage
    occurrences, `periods[2]/port`; their positions `{h, key}`; whether the
    join runs from one period to the next in time; the ends of the wire
    that a drag can move, `writing` and `reading` (unit K's decision
    K-D23); its field pairs, as the list a move opens lists them, each with
    its two fields' declared sets (`_move_fields`; unit K's decision
    K-D25); the name of the file that writes it; whether an entry of a
    file writes it, which a removal takes out; and `others`, the rows the
    list of a move of its reading end offers beside its field pairs (unit
    L, Task 19; defect 13 of the UX simulation): each other unjoined
    continuation field of its writing occurrence, `{"writing", "field",
    "field_set", "readers"}`, its port's id, its name, its declared set and
    the arrival field of each occurrence of the reading end's period,
    another than the writer, joined or not, whose name pairs with its own
    (K-D8's `pairing_names`), none for a wire whose reading end does not
    move or whose writer is a period. Details prints the links to
    the entries (`join_rows`). An end of a wire of one entry moves as unit
    J built it (J-D33), and an end of a wire of several entries through the
    list; a wire of several entries one of whose fields has no port in the
    view, which the list could not name, moves by no end.

    A wire whose joins are all by equal names, which no entry writes, is a
    join wire like any other, selected by a click, and Details offers the
    rename of its reading field. Either end can move by authoring its
    replacement, and its field pairs come from the same package selection.
    It is not removable, since there is no entry to take out.

    After the wires, one record for each pair of periods whose wires into
    one port the region draws as one between the two periods (unit K's
    decision K-D5; `_pair_joins`), in the same form: its `source` and
    `from` the writers' period, `periods[2]`, its `sourceHandle` None, its
    `writing` `{h, "key": None}`, its field pairs those of every wire of the
    pair, and its reading end alone movable, through the list, since its
    writing end is a period.

    With `graph` the backward graph's id, the cables of the backward graph
    instead (design pass 10 §§6 and 8; the brief, § Wires, cables and
    connections): one record per edge that carries a route's record, in the
    same form, its `from` and `to` the route's source and destination, its
    `join` the route's pairs, `movable` empty, `fields` and `others` empty
    and `removable` false, since no gesture acts in the backward graph, and
    `graph` the graph's id, so that selecting the cable reveals its route,
    its status and its ordered wires in Details (`join_rows`) and nothing
    else."""
    texts = texts or {}
    if graph != _FORWARD:
        return _backward_join_wires(shown, graph)
    wires = _wire_joins(shown, texts, names=True)
    drawn = _field_ports(shown)
    ports = {(port["side"], port["h"], port["key"], port["field"]): port for port in drawn}
    free: dict[tuple, dict] = {}
    reads: dict[int, dict] = {}
    for port in drawn:
        if port["unjoined"]:
            fields = free.setdefault((port["side"], port["h"]), {}).setdefault(port["key"], {})
            fields[port["field"]] = port["id"]
        if port["side"] == "reading":
            reads.setdefault(port["h"], {}).setdefault(port["key"], {})[port["field"]] = port["id"]
    labels: dict[tuple, tuple] = {}

    def labels_of(h, key):
        if (h, key) not in labels:
            labels[h, key] = _stage_labels(shown, h, key)
        return labels[h, key]

    sets_of = _field_sets(shown)
    found = []
    for wire in wires + _pair_joins(wires):
        (hw, kw), (hr, kr) = wire["writing"], wire["reading"]
        written = bool(wire["entries"])
        route = wire.get("route") or {}
        fields = _move_fields(wire, ports, free, reads, labels_of, sets_of)
        ends = ["reading"] if kw is None else ["writing", "reading"]
        if fields is None:
            ends = []
        others = []
        if kw is not None and "reading" in ends:
            for field, port in free.get(("writing", hw), {}).get(kw, {}).items():
                names = pairing_names(field, labels_of(hw, kw))
                readers = {}
                for key, held in reads.get(hr, {}).items():
                    proposed = None if hw == hr and key == kw else _proposed_reading(names, held)
                    if proposed is not None:
                        readers[f"periods[{hr}]/{key}"] = proposed
                field_set = sets_of(hw, kw, "writing").get(field, "")
                others.append(
                    {"writing": port, "field": field, "field_set": field_set, "readers": readers}
                )
        found.append(
            {
                "source": wire["source"],
                "sourceHandle": wire["sourceHandle"],
                "target": wire["target"],
                "targetHandle": wire["targetHandle"],
                "join": wire["join"],
                "from": wire["source"] if kw is None else f"periods[{hw}]/{kw}",
                "to": f"periods[{hr}]/{kr}",
                "writing": {"h": hw, "key": kw},
                "reading": {"h": hr, "key": kr},
                "between": hw != hr,
                "movable": ends,
                "fields": fields or [],
                "others": others,
                "file": Path(wire["entries"][0].path).name if written else None,
                "removable": written,
                # the branch of the wire's route and the route's status, as the
                # record its edge carries names them (design pass 10 §§6 and 8)
                "branch": route.get("branch"),
                "status": route.get("status"),
            }
        )
    return found


def _event_wire(shown: TrellisShown, event, texts) -> dict | None:
    """The join wire (`_wire_joins`, a wire whose joins are all by equal
    names among them, its entries none), or the pair of periods
    (`_pair_joins`; unit K's decision K-D5), that the event `removed`,
    `moved` or `renamed` names by its two nodes and its two ports under
    `join` (unit J's decision J-D33; unit L, Task 15), a pair by its
    writers' period and no port, where the event's `reading` names the
    source, the graph and the number of `shown`; None otherwise, a record
    that is no event included."""
    if not isinstance(event, dict) or not isinstance(event.get("reading"), dict):
        return None
    if any(event["reading"].get(name) != value for name, value in _drawn(shown).items()):
        return None
    named = event.get("join")
    if not isinstance(named, dict):
        return None
    ids = ("source", "sourceHandle", "target", "targetHandle")
    wires = _wire_joins(shown, texts, names=True)
    return next(
        (wire for wire in wires + _pair_joins(wires) if all(wire[k] == named.get(k) for k in ids)),
        None,
    )


def _written_text(text: str, address: str) -> str:
    """The text of the value at `address` of the YAML text `text`, as
    written, its lines joined by one space where it spans several (the
    package's `entry_span`, whose columns count code points)."""
    span = entry_span(text, address)
    lines = _LINE_BREAKS.split(text)
    if span.line == span.end_line:
        return lines[span.line - 1][span.column - 1 : span.end_column - 1]
    parts = [lines[span.line - 1][span.column - 1 :], *lines[span.line : span.end_line - 1]]
    parts.append(lines[span.end_line - 1][: span.end_column - 1])
    return " ".join(part.strip() for part in parts)


def _whole_items(texts: dict, entries) -> set:
    """The connector items, each `(path, address)`, every pair of which an
    entry of `entries` writes, so that the removal of those entries takes
    the item out of its list, read in the texts `texts` by resolved path."""
    items = {}
    for entry in entries:
        if entry.item is not None:
            items.setdefault((entry.path, entry.item, entry.mapping), set()).add(entry.key)
    whole = set()
    for (path, item, mapping), keys in items.items():
        written = entry_value(texts[path], mapping)
        if isinstance(written, dict) and set(written) <= keys:
            whole.add((path, item))
    return whole


def _without(texts: dict, entries) -> dict:
    """The texts `texts`, by resolved path, with the entries `entries` taken
    out by the package's writers (unit J's decisions J-D33 and J-D34): a
    connector's item whose every pair goes, out of its `connectors` list
    (`remove_from_sequence`), the items of one list from the last up, the
    list's only item left `{}` in its place (`insert_in_sequence` before
    it), so that a drag can fill it again; each other key out of its
    mapping (`remove_from_mapping`), an inter-period mapping left `{}` where
    its last key goes, so that the number of mappings never changes. A
    writer's refusal is its ValueError, and an address the text no longer
    holds a KeyError."""
    texts = dict(texts)
    whole = _whole_items(texts, entries)
    for entry in entries:
        if (entry.path, entry.item) not in whole:
            texts[entry.path] = remove_from_mapping(texts[entry.path], entry.mapping, entry.key)

    def last_first(place):
        listed, number = _ITEM.fullmatch(place[1]).groups()
        return place[0], listed, -int(number)

    for path, item in sorted(whole, key=last_first):
        listed, number = _ITEM.fullmatch(item).groups()
        at = int(number)
        if len(entry_value(texts[path], listed)) > 1:
            texts[path] = remove_from_sequence(texts[path], listed, at)
        else:
            placed = insert_in_sequence(texts[path], listed, at, "{}")
            texts[path] = remove_from_sequence(placed, listed, at + 1)
    return texts


def _removed_words(texts: dict, entries, whole_mappings: bool = False) -> list[tuple]:
    """For the status line of a removal or a move (amendment 02, rulings 13
    and 14), `(path, address, text, periods)` of each part of the file the
    entries `entries` write, in the texts `texts` before the removal: a
    connector's item that goes whole, by its address and its text as
    written, `{m_next: m}`; otherwise the mapping that loses keys, by its
    address and its pairs, `a: k`; each with the periods its entry
    reaches. Where `whole_mappings`, as for the removal of a pair of
    periods (unit K's decision K-D5), a mapping every key of which goes is
    named as an entry, by its address and its text as written."""
    whole, words, keys = _whole_items(texts, entries), {}, {}
    for entry in entries:
        if (entry.path, entry.item) in whole:
            place = (entry.path, entry.item)
            words[place] = [_written_text(texts[entry.path], entry.item), entry.periods]
        else:
            place = (entry.path, entry.item if entry.item == entry.mapping else entry.mapping)
            keys.setdefault(place, set()).add(entry.key)
            pair = f"{entry.key}: {entry.value}"
            if place in words:
                words[place][0] += f", {pair}"
            else:
                words[place] = [pair, entry.periods]
    if whole_mappings:
        for (path, address), taken in keys.items():
            written = entry_value(texts[path], address)
            if isinstance(written, dict) and set(written) <= taken:
                words[path, address][0] = _written_text(texts[path], address)
    return [(path, address, text, periods) for (path, address), (text, periods) in words.items()]


def _with_connectors(shown: TrellisShown, texts, around: int | None = None) -> dict:
    """The proposed source connectors on the existing stage occurrences.
    The package expands every shared source once; `around` does not limit
    validation to nearby periods."""
    trellis = shown.trellis
    read = read_trellis_file(trellis["provenance"]["trellis"]["path"], texts)
    if len(read["periods"]) != len(trellis["periods"]):
        raise ValueError("the period list changed after the graph was read")
    return {
        **trellis,
        "periods": [{**period, "connectors": source["connectors"]}
                    for period, source in zip(trellis["periods"], read["periods"])],
        "inter_connectors": read["inter_connectors"],
    }


def _port_label(shown: TrellisShown, port_id) -> str | None:
    """The label of the port `port_id` of the forward graph the view
    `shown` holds, as the graph draws it on its box; None where no port of
    that graph has that id."""
    for graph in shown.collection["graphs"]:
        if graph["id"] != _FORWARD:
            continue
        for node in graph["nodes"]:
            for item in (node.get("inputsMetadata") or []) + (node.get("outputsMetadata") or []):
                if item["id"] == port_id:
                    attributes = {pair["key"]: pair["value"] for pair in item.get("attrs") or []}
                    return attributes.get("label", port_id)
    return None


def _joined(path: str, address: str, name: str, end: str) -> Gesture:
    """The `Gesture` of a move to a port that is joined (unit J's plan, Task
    19, its rulings; amendment 02, ruling 14): nothing typed, and the
    sentence `the port <name> is joined` in the Workbench's four parts, at
    the file and the address of the join that was to move, `name` being a
    field as the file writes it, or the label of a port that stands for no
    field. What to do follows the end moved, `end` (unit J's plan, Task
    17): a writing end goes to a port marked unjoined, since a continuation
    field joins one arrival field, and a reading end to a field's port,
    joined or not, since an arrival field takes several sources (J-D42)."""
    where = "a port marked unjoined" if end == "writing" else "a field's port"
    sentence = (
        f"{Path(path).name}, {address}: nothing was written. The port {name} is joined. "
        f"Move the end to {where}."
    )
    return Gesture(None, None, (), None, sentence, path, address)


def _move_ports(shown: TrellisShown, wire: dict, event) -> list[tuple] | None:
    """The moves that the event `moved` of the join wire `wire`, or of the
    piece of a pair of periods, names by `pairs` (unit K's decision K-D23),
    each `(entry, writing, reading)`: the entry of one field pair of the
    wire (`_field_pairs`) and the new pair's writing and reading ports, each
    its record of `_field_ports`. The event's `end` is `reading` or
    `writing`, `reading` alone for a pair's piece, and `pairs` a list of one
    or more records `{sourceHandle, targetHandle, replaced}`, the ids of the
    new pair's writing and reading ports and of the port of the moved end
    that the field pair leaves. Each record keeps the port of the end not
    moved and names a field pair of the wire, each field pair once; its new
    port stands on the side `end` names; the new ports stand on one stage
    occurrence, in the period of the end kept or the adjacent one in time,
    a reading end in the writer's period or the next and a writing end in
    the reader's period or the one before (design pass 10 §7), and, within
    one period, another than the occurrence of the end kept; and new
    writing ports are distinct, since a continuation field joins one
    arrival field (J-D41).

    A record without `replaced`, which a row of the writer's other unjoined
    continuation fields sends where the reading end of a wire from one
    stage occurrence moves (`others` of `join_wires`; unit L, Task 19;
    defect 13 of the UX simulation), names a new pair and no field pair of
    the wire, its entry None: its writing port is an unjoined port of the
    wire's writing occurrence that no other record of the event names, and
    its reading port stands where the other new ports stand. Where the
    writing end of a wire moves, such a record names a new pair from a
    continuation field of the branch dropped on to an arrival field of the
    wire's reading occurrence that the wire did not reach (the cable's
    list; design pass 10 §7): its reading port is a port of that
    occurrence that no other record names. None otherwise, a record that is
    no such event included."""
    end, pairs = event.get("end"), event.get("pairs")
    piece = "members" in wire
    if end not in (("reading",) if piece else ("reading", "writing")):
        return None
    if not isinstance(pairs, list) or not pairs:
        return None
    drawn = _field_ports(shown)
    ports = {port["id"]: port for port in drawn}
    by_field = {(port["side"], port["h"], port["key"], port["field"]): port for port in drawn}
    fields = {}
    for entry, (hw, kw), (hr, kr) in _field_pairs(wire):
        writing = by_field.get(("writing", hw, kw, entry.writing.field))
        reading = by_field.get(("reading", hr, kr, entry.reading.field))
        if writing is not None and reading is not None:
            fields[writing["id"], reading["id"]] = (entry, writing, reading)
    moves, named, fresh = [], set(), set()
    for record in pairs:
        if not isinstance(record, dict):
            return None
        ids = record.get("sourceHandle"), record.get("targetHandle")
        if not all(isinstance(port, str) for port in ids):
            return None
        kept, new = ids if end == "reading" else ids[::-1]
        if new not in ports or ports[new]["side"] != end:
            return None
        if "replaced" not in record:
            if end == "writing":
                # a new pair into an arrival field of the wire's reading
                # occurrence that the wire did not reach (design pass 10 §7)
                target = ports.get(kept)
                if (
                    piece
                    or target is None
                    or target["side"] != "reading"
                    or (target["h"], target["key"]) != tuple(wire["reading"])
                    or kept in fresh
                ):
                    return None
                fresh.add(kept)
                moves.append((None, ports[new], target))
                continue
            # a new pair from another unjoined continuation field of the
            # wire's writing occurrence
            source = ports.get(kept)
            if (
                piece
                or source is None
                or source["side"] != "writing"
                or not source["unjoined"]
                or (source["h"], source["key"]) != tuple(wire["writing"])
                or kept in fresh
            ):
                return None
            fresh.add(kept)
            moves.append((None, source, ports[new]))
            continue
        replaced = record.get("replaced")
        if not isinstance(replaced, str):
            return None
        old = (kept, replaced) if end == "reading" else (replaced, kept)
        if old not in fields or old in named:
            return None
        named.add(old)
        entry, writing, reading = fields[old]
        moves.append(
            (entry, writing, ports[new]) if end == "reading" else (entry, ports[new], reading)
        )
    side = 2 if end == "reading" else 1
    places = {(move[side]["h"], move[side]["key"]) for move in moves}
    (hw, kw), (hr, kr) = wire["writing"], wire["reading"]
    if len(places) != 1:
        return None
    ((h, key),) = places
    # the new occurrence stands in the kept end's period or the adjacent one
    # in time, a reading end in the writer's period or the next, periods[hw
    # − 1], and a writing end in the reader's period or the one before,
    # periods[hr + 1]; within one period, another occurrence than the kept
    # end's (design pass 10 §7; §3.1 as J-D41 amends it)
    if end == "reading":
        if h not in (hw, hw - 1) or (h == hw and key == kw):
            return None
    elif h not in (hr, hr + 1) or (h == hr and key == kr):
        return None
    if end == "writing" and len({move[1]["id"] for move in moves}) != len(moves):
        return None
    return moves


def _moved_pairs(shown: TrellisShown, wire: dict, event, texts) -> Gesture:
    """Author the requested replacement pairs as one validated source edit.
    Unmoved source entries are preserved; inferred pairs have no entry to
    remove. The package releases only the inferred pairs being replaced.

    An event marked `cable`, the button `join` of a cable's list (design
    pass 10 §7), moves the whole cable: every pair of the wire's route is
    released in the same write, the authored entries taken out and the
    inferred pairs named to the package as replaced, whether or not a
    ticked row writes its field again, so that no branch is split across
    two destinations; a field left unpaired stands unjoined, and the
    package reports the incomplete route under Problems. Where the package
    would select a released pair again on another occurrence than the one
    the moved end now stands on, the write is refused (`_checked_edit`); a
    cable dropped on its own destination keeps the pairs its list leaves
    unpaired, since they stand on that one destination. A new writing
    port that a pair already reads is released too, its authored entry
    taken out or its inferred pair named as replaced, since a continuation
    field joins one arrival field (AMD-COMP-001 §3.2)."""
    moves = _move_ports(shown, wire, event)
    if moves is None:
        return _old_graph(shown)
    whole = bool(event.get("cable"))
    changed = [(pair, w, r) for pair, w, r in moves if pair is None or
               (_field_of(w), _field_of(r)) != (
                   (pair.writing.h, pair.writing.key, pair.writing.field),
                   (pair.reading.h, pair.reading.key, pair.reading.field))]
    if not changed:
        return Gesture(None, None, (), None, None, None, None)
    if all(pair is None for pair, _, _ in changed) and not whole:
        return connector_edit(shown, event, texts)
    route_pairs = [pair for pair, _, _ in _field_pairs(wire)]
    # the occurrence the moved end now stands on, and the pairs of the route
    # the list keeps unchanged there: a cable dropped on its own destination
    # keeps them, their entries untouched (design pass 10 §7)
    end = event.get("end")
    side = 2 if end == "reading" else 1
    ((landed_h, landed_key),) = {(move[side]["h"], move[side]["key"]) for move in moves}
    changed_pairs = {(pair.writing, pair.reading) for pair, _, _ in changed if pair is not None}
    kept = {
        (pair.writing, pair.reading) for pair, _, _ in moves
        if pair is not None and (pair.writing, pair.reading) not in changed_pairs
        and ((pair.reading.h, pair.reading.key) if end == "reading" else (pair.writing.h, pair.writing.key))
        == (landed_h, landed_key)
    }
    authored = [pair for pair, _, _ in changed if pair is not None and pair.origin == "authored"]
    if whole:
        authored = [pair for pair in route_pairs
                    if pair.origin == "authored" and (pair.writing, pair.reading) not in kept]
    # the pairs that read a new writing port, which the write releases
    new_writing = {_field_of(w) for _, w, _ in changed}
    landing = [pair for pair in shown.selection.pairs
               if (pair.writing.h, pair.writing.key, pair.writing.field) in new_writing
               and pair not in route_pairs]
    entries = list(dict.fromkeys(
        entry for member in wire.get("members") or [wire] for entry in member["entries"]
        if any((pair.writing.h, pair.writing.key) == member["writing"]
               and (pair.reading.h, pair.reading.key) == member["reading"]
               and pair.source_key == entry.key and pair.writing.field == entry.field
               and pair.reading.field == entry.arrival for pair in authored)
    ))
    places: dict = {}
    for pair in landing:
        if pair.origin != "authored":
            continue
        writer, reader = (pair.writing.h, pair.writing.key), (pair.reading.h, pair.reading.key)
        for entry in _pair_entries(shown, writer, reader, places, texts, [pair]):
            if entry not in entries:
                entries.append(entry)
    try:
        before = {entry.path: _text_at(entry.path, texts) for entry in entries}
        after = _without(before, entries)
        remaining = _with_connectors(shown, {**texts, **after}) if entries else shown.trellis
        selected = trellis_selection(remaining) if entries else shown.selection
    except (OSError, ValueError, KeyError, TypeError):
        return _old_graph(shown)
    old = {(pair.writing, pair.reading) for pair, _, _ in changed if pair is not None}
    if whole:
        old |= {(pair.writing, pair.reading) for pair in route_pairs} - kept
    released = {pair.writing for pair in authored} | {pair.writing for pair in landing}
    replacing = tuple(pair for pair in selected.pairs
                      if pair.origin == "inferred"
                      and ((pair.writing, pair.reading) in old or pair.writing in released))
    groups = {}
    left = {**texts, **after}
    for _, writing, reading in changed:
        ends = _field_of(writing), _field_of(reading)
        try:
            line = connector_entry(remaining, *ends, left, selection=selected, replacing=replacing)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return _old_graph(shown)
        if line.reason in ("not-adjacent", "port-joined"):
            return _joined_writing(shown, writing, texts)
        path = str(Path(line.file).resolve()) if line.file else None
        if line.reason is not None:
            return Gesture(None, None, (), None, gesture_sentence(line.reason, line, *ends), path, line.address)
        groups.setdefault((path, line.address), []).append((line, *ends, reading["unjoined"]))
    read, typed, lines, periods = dict(before), dict(after), [], set()
    for (path, address), items in groups.items():
        line = items[0][0]
        try:
            if path not in read:
                read[path] = typed[path] = _text_at(path, texts)
            text, words, _ = _group_line(items, entry_value(typed[path], address))
            typed[path] = _typed(typed[path], line._replace(text=text))
        except (OSError, ValueError, KeyError, TypeError):
            return Gesture(None, None, (), None, gesture_sentence("not-applied", line, None, None), path, address)
        lines.append(words)
        periods.update(line.periods)
    path, address = next(iter(groups))
    note = f"{Path(path).name}, {address}: {', '.join(lines)} written, periods {_runs(sorted(periods))}"
    edits = {name: text for name, text in typed.items() if text != read[name]}
    gesture = Gesture(edits, {name: read[name] for name in edits}, (), note, None, path, address)
    # a whole cable's write is refused where the package would select a pair
    # of the route again on another occurrence than the one the moved end
    # now stands on, since the branch would then stand on two destinations,
    # or the arrival tuple read two sources (design pass 10 §7; AMD-COMP-001
    # §3.2); a pair that stands on that occurrence is no split, so a cable
    # dropped on its own destination keeps the pairs its list leaves
    # unpaired
    released = tuple(sorted(
        ((w.h, w.key, w.field), (r.h, r.key, r.field)) for w, r in old
        if ((r.h, r.key) if end == "reading" else (w.h, w.key)) != (landed_h, landed_key)
    )) if whole else ()
    return _checked_edit(shown, gesture, texts, tuple((_field_of(w), _field_of(r)) for _, w, r in changed), released, end)


def removal_edit(shown: TrellisShown, event, texts) -> Gesture:
    """The `Gesture` of the event `removed` or `moved` of a join wire of the
    forward trellis graph drawn from the reading `shown` (unit J's decisions
    J-D33 and J-D34; amendment 02, rulings 13 and 14), a function of its
    arguments that reads no state of the page, writes nothing and raises
    nothing. `texts` is the mapping of every unsaved buffer of the tab, by
    resolved path. The event names the wire by its two nodes and its two
    ports under `join`, beside the record of the reading; a move also names
    the end moved, `end`, `reading` or `writing`, and either the new port's
    id, `handle`, for a wire of one entry, or `pairs`, the field pairs the
    author ticked in the list a move of a wire of several entries opens,
    which `_moved_pairs` answers (unit K's decision K-D23).

    Where the event's `reading` names another source, graph or elaboration
    number than `shown`, where a file `shown` read now holds another text
    (`inputs_current`), where the wire is no join wire of the view
    (`join_wires`), or where a move that names `handle` names a wire that
    more than one entry writes, or a pair of periods, the answer is the
    sentence "An old graph". A wire whose joins are all by equal names,
    which no entry writes, is not removed. Moving it authors its replacement
    through the same path as a written connection. Otherwise the entries
    that write the wire's joins are taken out of the texts of their files,
    from `texts`, else from disk, by the package's writers (`_without`): a
    removal needs no port to be unjoined, leaves a `connectors` list `- {}`
    where its last item goes and an inter-period mapping `{}` where its last
    key goes, and its note is `period.yml, connectors[0]: {m_next: m}
    removed, periods 0–5`. A move then types the new line (`_moved`), its
    note `trellis.yml, inter_connectors[0]: a: k changed to a: m, periods
    0–5`. A writer's refusal answers the sentence "An edit not applied". A
    trellis left with fields unjoined is no refusal: the package reads it
    as it reads any text. A move is a drag, and a removal, an event that
    names no end and no port, is not: the last sentence of "An old graph"
    and "An edit not applied" asks the reader to drag again or to remove
    the join again (`gesture_sentence`; unit J's plan, Task 17).

    An event that names a pair of periods by its writers' period
    (`_pair_joins`; unit K's decision K-D5) removes the entries of the
    joins of every wire of the pair, and a mapping all of whose keys go is
    named in the note as the entry it is, `trellis.yml, inter_connectors[0]:
    {a_nxt_kp: a, …} removed, periods 0–50`, the mapping left `{}`; its
    reading end is moved through the list (`_moved_pairs`)."""
    texts = texts or {}
    moving = isinstance(event, dict) and any(name in event for name in ("end", "handle", "pairs"))
    # what the sentences of a removal ask to remove again; a move is a drag
    removal = None if moving else "join"
    wire = _event_wire(shown, event, texts)
    if wire is None or not inputs_current(shown, texts):
        return _old_graph(shown, removal=removal)
    if moving:
        if "pairs" not in event:
            pairs = _field_pairs(wire)
            if len(pairs) != 1:
                return _old_graph(shown)
            pair = pairs[0][0]
            ports = {(p["side"], p["h"], p["key"], p["field"]): p for p in _field_ports(shown)}
            writing = ports.get(("writing", pair.writing.h, pair.writing.key, pair.writing.field))
            reading = ports.get(("reading", pair.reading.h, pair.reading.key, pair.reading.field))
            if writing is None or reading is None or event.get("end") not in ("writing", "reading"):
                return _old_graph(shown)
            end = event["end"]
            event = {**event, "pairs": [{
                "sourceHandle": event.get("handle") if end == "writing" else writing["id"],
                "targetHandle": event.get("handle") if end == "reading" else reading["id"],
                "replaced": writing["id"] if end == "writing" else reading["id"],
            }]}
        return _moved_pairs(shown, wire, event, texts)
    if not wire["entries"]:
        return Gesture(None, None, (), None, None, None, None)
    pair = "members" in wire
    first = wire["entries"][0]
    place = Gesture(None, None, (), None, None, first.path, first.item or first.mapping)
    try:
        before = {entry.path: _text_at(entry.path, texts) for entry in wire["entries"]}
        after = _without(before, wire["entries"])
        words = _removed_words(before, wire["entries"], whole_mappings=pair)
    except (OSError, ValueError, KeyError, TypeError):
        sentence = gesture_sentence("not-applied", place, None, None, removal=removal)
        return place._replace(sentence=sentence)
    note = "; ".join(
        f"{Path(path).name}, {address}: {text} removed, periods {_runs(periods)}"
        for path, address, text, periods in words
    )
    edits = {path: text for path, text in after.items() if text != before[path]}
    read = {path: before[path] for path in edits}
    return Gesture(edits, read, (), note, None, words[0][0], words[0][1])


# --- the reading field of a join by equal names renamed (unit L, Task 15) ---

# a name of the language as a stage file writes a field: a letter, then
# letters, digits and underscores
_FIELD_NAME = re.compile(r"[^\W\d_]\w*")


def _declared_besides(stage, field: str) -> bool:
    """Whether the stage `stage` declares the name `field` as anything
    beside its arrival state field of that name: a field of another perch
    or of another role, or a definition, a parameter, a set, a function or
    a distribution's subject among them, the definitions of a name as
    `model.name_report` reads them."""
    for identity, sort in stage.fields().items():
        if identity.field == field and (sort.perch != arvl or sort.role != "state"):
            return True
    return any(
        identity.field == field or field in identity.subjects
        for identity in stage.definitions.keys()
    )


def rename_edit(shown: TrellisShown, event, texts) -> Gesture:
    """The `Gesture` of the event `renamed`, the button `rename` of Details
    for a join wire of the forward trellis graph drawn from the reading
    `shown` (unit L, Task 15; defect 3 of the UX simulation; J-D33 and
    J-D39 extended to joins by equal names), a function of its arguments
    that reads no state of the page, writes nothing and raises nothing.
    `texts` is the mapping of every unsaved buffer of the tab, by resolved
    path. The event names the wire by its two nodes and its two ports under
    `join`, beside the record of the reading; `field`, an arrival field of
    the reading stage occurrence that a join of the wire reaches by equal
    names (`_name_joins`); and `name`, the name typed in Details.

    Where the event's `reading` names another source, graph or elaboration
    number than `shown`, where a file `shown` read now holds another text
    (`inputs_current`), where the wire is no join wire of the view, or
    where `field` is no arrival field the wire joins by equal names, the
    answer is the sentence "An old graph", which asks for the field to be
    renamed again. A name equal to the field's writes and prints nothing.
    The reading stage's file, the origin its record names, is read from
    `texts`, else from disk, and nothing is written, the sentence naming
    the file, where `name`, read without the spaces around it, is no name
    of the language (`_FIELD_NAME`); where the file already writes `name`
    as a whole word, so that two fields would take one name; where the
    stage declares `field` as anything beside that arrival field
    (`_declared_besides`), which a rename of the word would rename too; and
    where the file writes `field` nowhere as a whole word. Otherwise every
    whole word `field` of the file, as `model.occurrences` finds them, in
    the block headers that list it and in the lines that read it, is
    written `name`, and nothing else of the file changes: a name built on
    the field's, `V_w_c`, is another word and keeps its name. The note
    names the file and the lines changed,
    `allocation.bl, lines 22–23: w_c renamed to w_in`. The edit is of the
    reading stage's file alone, the trellis file, the writing stage's file
    and every other file keeping their texts, and it holds for every
    occurrence of that stage file; it stands in the file's unsaved text,
    which the trellis reads once it is saved, as after any edit of a stage
    file."""
    texts = texts or {}
    wire = _event_wire(shown, event, texts)
    if wire is None or not inputs_current(shown, texts):
        return _old_graph(shown, rename=True)
    field, name = event.get("field"), event.get("name")
    named = _name_joins(shown, wire["writing"], wire["reading"])
    if not isinstance(field, str) or not isinstance(name, str) or field not in named:
        return _old_graph(shown, rename=True)
    name = name.strip()
    if name == field:
        return Gesture(None, None, (), None, None, None, None)
    h, key = wire["reading"]
    path = str(Path(shown.syntactic["periods"][h]["stages"][key]["stage"]["origin"]).resolve())
    try:
        before = _text_at(path, texts)
    except OSError:
        return _old_graph(shown, rename=True)
    places = model.occurrences(before, field)
    if not name:
        why = "No name was typed. Type a name that begins with a letter."
    elif not _FIELD_NAME.fullmatch(name):
        why = f"{name} is no name of the language. Type a name that begins with a letter."
    elif model.occurrences(before, name):
        why = f"The stage file already writes {name}. Type another name."
    elif _declared_besides(shown.trellis["periods"][h]["stages"][key], field):
        why = f"The stage file declares {field} beside the arrival field. Rename it in the text."
    elif not places:
        why = f"The stage file writes {field} nowhere as one word. Rename it in the text."
    else:
        why = None
    if why is not None:
        return Gesture(
            None, None, (), None, f"{Path(path).name}: nothing was written. {why}", path, None
        )
    word = re.compile(rf"(?<!\w){re.escape(field)}(?!\w)")
    after = word.sub(lambda _: name, before)
    lines = sorted({line for line, _ in places})
    counted = "line" if len(lines) == 1 else "lines"
    note = f"{Path(path).name}, {counted} {_runs(lines)}: {field} renamed to {name}"
    return Gesture({path: after}, {path: before}, (), note, None, path, None)


# --- a stage occurrence removed from its period (unit K's decision K-D14) ---

# the layer of a stage occurrence in the forward graph, the id the event
# `removed` names it by, `periods[2]/port___group___`: its period and its key;
# the page reads it for Backspace that cannot act (unit N, Task 5)
OCCURRENCE_LAYER = re.compile(r"periods\[(\d+)\]/([^/]+)" + re.escape(LAYER_ID_ENDING))


def _occurrences_drawn(shown: TrellisShown) -> set[str]:
    """The addresses `periods[h]/<key>` of the stage occurrences that hold a
    node of the forward graph of the view `shown`, those its restriction
    leaves in it; none where that graph is refused."""
    for graph in shown.collection["graphs"]:
        if graph["id"] == _FORWARD:
            parts = ((node.get("namespace") or "").split("/") for node in graph["nodes"])
            return {"/".join(names[:2]) for names in parts if len(names) >= 2}
    return set()


def _event_occurrence(shown: TrellisShown, event) -> tuple | None:
    """The position `(h, key)` of the stage occurrence whose layer the event
    `removed` names under `occurrence` (unit K's decision K-D14), where the
    event's `reading` names the source, the graph and the number of `shown`
    and the forward graph of the view `shown` draws that occurrence of the
    trellis; None otherwise, a record that is no event included."""
    if not isinstance(event, dict) or not isinstance(event.get("reading"), dict):
        return None
    if any(event["reading"].get(name) != value for name, value in _drawn(shown).items()):
        return None
    named = event.get("occurrence")
    found = OCCURRENCE_LAYER.fullmatch(named) if isinstance(named, str) else None
    if found is None:
        return None
    address = f"periods[{found[1]}]/{found[2]}"
    if address not in _occurrences_drawn(shown):
        return None
    return occurrence_positions(shown).get(address)


def _declares(stage, perch: str, name: str) -> bool:
    """Whether the stage version `stage` declares a state field named `name`
    at the perch `perch`, `arvl` or `cntn`."""
    return any(
        sort.perch == perch and sort.role == "state" and identity.field == name
        for identity, sort in stage.fields().items()
    )


def _occurrence_entries(shown: TrellisShown, h: int, key: str, texts) -> list[_Entry]:
    """The entries of files that write joins of the stage occurrence `key`
    of period `h` of the trellis `shown` and that the package would refuse
    once the occurrence is gone (unit L, Task 14; K-D14 amended), in the
    order of the selected pairs. The entries that write them are found
    as for a join wire (`_pair_entries`), through
    the mapping of unsaved texts `texts`. An entry is refused where it names
    the removed occurrence by its key, a keyed connector, or where no other
    stage of period `h` declares a state field of the name it gives on the
    occurrence's side, the arrival field of a join into it or the
    continuation field of a join out of it (the package's rule
    `connector-names-no-field`); an entry that another stage's field of
    that name still takes, such as an inter-period mapping that then joins
    the stage before it in the period, stands. A join by equal names has
    no entry. No entry where the package refuses a period, as no current
    reading does."""
    periods = shown.trellis["periods"]
    pairs = dict.fromkeys(
        ((pair.writing.h, pair.writing.key), (pair.reading.h, pair.reading.key))
        for pair in shown.selection.pairs
        if (h, key) in ((pair.writing.h, pair.writing.key), (pair.reading.h, pair.reading.key))
    )
    others = [stage for other, stage in periods[h]["stages"].items() if other != key]
    places, found = {}, []
    for writer, reader in pairs:
        reading = reader == (h, key)
        for entry in _pair_entries(shown, writer, reader, places, texts):
            keyed = entry.item is not None and entry.mapping != entry.item
            perch, name = (arvl, entry.arrival) if reading else (cntn, entry.field)
            if keyed or "." in (entry.value if reading else entry.key) or not any(_declares(stage, perch, name) for stage in others):
                found.append(entry)
    return list(dict.fromkeys(found))


def occurrence_removal_edit(shown: TrellisShown, event, texts) -> Gesture:
    """The `Gesture` of the event `removed` of a stage occurrence of the
    forward trellis graph drawn from the reading `shown`, Backspace or
    Delete on its card selected (unit K's decision K-D14; Task 15), or
    `Remove from periods` of its Details (unit N, Task 5; design pass 10
    §7), a function of its arguments that reads no state of the page, writes
    nothing and raises nothing. `texts` is the mapping of every unsaved
    buffer of the tab, by resolved path. The event names the occurrence by
    its layer's id, `periods[2]/port___group___`, under `occurrence`,
    beside the record of the reading.

    Where the event's `reading` names another source, graph or elaboration
    number than `shown`, where a file `shown` read now holds another text
    (`inputs_current`), or where the layer is no stage occurrence the view
    draws (`_event_occurrence`), the answer is the sentence "An old graph",
    which asks for the stage to be removed again. Otherwise the stage's key
    is taken out of the list of the entry that writes the period, the
    place the package's `written_at` answers for `periods[h].stages`, as a
    drop on the period appends it there (`drop_edits`), by the package's
    writers (`creation.without_stage`), from `texts`, else from disk;
    every period that list writes loses the stage. The joins the
    occurrence had go with its key (unit L, Task 14; defect 2 of the UX
    simulation; K-D14
    amended): the entries that write them and that the package would
    refuse once the occurrence is gone (`_occurrence_entries`) are taken
    out as a join's removal takes them (`_without`; J-D33), in the same
    change of each file's text, so that the trellis stays constructed and
    one undo restores the key with its joins. The note is the drop's with
    `removed` for `written`, followed for each entry taken out by a join's
    removal note (J-D39), the parts joined by "; ", as for `port` removed
    from the file `trellis.cons-port.yml` of cons-port:
    `trellis.cons-port.yml, periods[0].stages: port removed, periods 0–5;
    trellis.cons-port.yml, periods[0].connectors[0]: {a: k} removed,
    periods 0–5; trellis.cons-port.yml, inter_connectors[0]: m_next: m
    removed, periods 0–5`. A join by equal names, which no
    entry writes, goes with the key alone. Where the trellis is read from a
    recipe and the list is the last of the trellis that holds the stage
    (`_last_list_row`; unit N, Task 5; N-D8), the stage's row of the recipe
    and answers.yml's records of it leave in the same change
    (`creation.without_row`), so that the next reading is not refused under
    `recipe-template-agreement` and one undo restores the row with the key;
    the row's parts then follow the list's in the note, `period.yml,
    stages: port removed, periods 0–5; spec.yml, stages: port removed`. A
    refusal of the package's
    writers to take the key out answers its own sentence, the file by its
    path from the model folder, as a drop's does (`_refused`; unit K's
    final judgment, §6 item 9), and a refusal of the creation unit to take
    the row out its own sentence; a file that cannot be read, or a refusal of
    the writers to take an entry out, answers the sentence "An edit not
    applied"."""
    texts = texts or {}
    position = _event_occurrence(shown, event)
    if position is None or not inputs_current(shown, texts):
        return _old_graph(shown, removal="stage")
    h, key = position
    trellis_file = shown.trellis["provenance"]["trellis"]["path"]
    place = _place_of(trellis_file, f"periods[{h}].stages", texts)
    if place is None:
        return _old_graph(shown, removal="stage")
    path = str(Path(place[0]).resolve())
    at = Gesture(None, None, (), None, None, path, place[1])
    try:
        text = _text_at(path, texts)
        removed = creation.without_stage(text, place[1], key)
    except (KeyError, ValueError) as error:
        return _refused(Path(path), _model_folder(shown), error)
    except (OSError, TypeError):
        return at._replace(sentence=gesture_sentence("not-applied", at, None, None, "stage"))
    if removed is None:
        return _old_graph(shown, removal="stage")
    try:
        row = _last_list_row(shown, place, key, texts)
    except (OSError, ValueError) as error:
        return at._replace(sentence=str(error))
    entries = _occurrence_entries(shown, h, key, texts)
    try:
        before = {path: text, **row.read}
        for entry in entries:
            if entry.path not in before:
                before[entry.path] = _text_at(entry.path, texts)
        after = _without({**before, path: removed, **row.edits}, entries)
        words = _removed_words(before, entries)
    except (OSError, ValueError, KeyError, TypeError):
        return at._replace(sentence=gesture_sentence("not-applied", at, None, None, "stage"))
    reached = [p for p, other in enumerate(_stage_places(shown, texts)) if other == place]
    notes = [f"{Path(path).name}, {place[1]}: {key} removed, periods {_runs(reached)}"]
    notes += list(row.notes)
    notes += [
        f"{Path(file).name}, {address}: {written} removed, periods {_runs(periods)}"
        for file, address, written, periods in words
    ]
    edits = {file: written for file, written in after.items() if written != before[file]}
    read = {file: before[file] for file in edits}
    return Gesture(edits, read, (), "; ".join(notes), None, path, place[1])


def occurrence_list(shown: TrellisShown, position, texts=None) -> tuple[str, str] | None:
    """The list of stages that writes the period of the stage occurrence
    `position`, `(h, key)`, of the trellis `shown`, the scope that Details'
    control `Remove from periods` names (unit N, Task 5; design pass 10
    §7): the name of the file that writes the list and the periods the list
    writes, each run of consecutive periods as a range, `("period.yml",
    "1–50")`, the place the package's `written_at` answers for
    `periods[h].stages` through the mapping of unsaved texts `texts`
    (`_stage_places`), as the removal reads it; None where it answers no
    place for that period."""
    places = _stage_places(shown, texts or {})
    h = position[0]
    if not 0 <= h < len(places) or places[h] is None:
        return None
    reached = [p for p, other in enumerate(places) if other == places[h]]
    return Path(places[h][0]).name, _runs(reached)


def _last_list_row(shown: TrellisShown, place, key: str, texts) -> creation.Added:
    """What the removal of the stage `key` from the list of stages at
    `place`, `(file, address)`, takes out of the recipe beside the key
    (unit N, Task 5; N-D8): where the trellis `shown` is read from a recipe
    (`_recipe_of`) and no other list of its periods holds the key
    (`_stage_places`, `_listed`, read through the mapping of unsaved texts
    `texts`), the stage's row and answers.yml's records of it
    (`creation.without_row`); otherwise an answer with no edit and no note.
    The creation unit's refusal is its ValueError."""
    found = _recipe_of(shown)
    others = {other for other in _stage_places(shown, texts) if other not in (None, place)}
    if found is None or any(key in _listed(other, texts) for other in others):
        return creation.Added((), {}, {}, ())
    root, recipe_file = found
    return creation.without_row(root, key, recipe=recipe_file.name, texts=texts)


# --- a stage or a period removed from the model (unit L, Task 25; L-D18) ---


def _removal_place(shown: TrellisShown, event) -> tuple[Path, Path] | None:
    """The model folder and the recipe, each a resolved path, of the
    trellis `shown` for the event of a stage's or a period's removal, where
    the event's `reading` names the source, the graph and the elaboration
    number of `shown` and the trellis is read from a recipe (`_recipe_of`);
    None otherwise, a record that is no event included."""
    return _recipe_of(shown) if _of_reading(shown, event) else None


def stage_removal_edit(shown: TrellisShown, event, texts) -> Gesture:
    """The `Gesture` of `remove stage` (unit L, Task 25; AAS, L-D18), the
    button of a stage's block of the recipe region or of Details of one of
    its occurrences, `{reading, stage}`, for the trellis drawn from the
    reading `shown` and read from a recipe; a function of its arguments that
    reads no state of the page, writes nothing and raises nothing. `texts`
    is the mapping of every unsaved buffer of the tab, by resolved path.

    Where the event's `reading` names another source, graph or elaboration
    number than `shown`, where the trellis is read from a trellis file, or
    where a file `shown` read now holds another text (`inputs_current`), the
    answer is the sentence "An old graph", which asks for the stage to be
    removed again. Otherwise the recipe's row, the key in every period's
    list and answers.yml's records leave the texts as the creation unit
    answers them (`creation.remove_stage`), and, in the same change of each
    file's text, the entries of the connectors that write joins of the
    stage's occurrences and that the package would refuse once the stage is
    gone, found for each period that lists it as a stage occurrence's
    removal finds them (`_occurrence_entries`) and taken out as a join's
    removal takes them (`_without`; J-D33), so that one undo restores the
    row, the keys and the joins. The note is the creation unit's parts, the
    recipe's row and each list, then each connector entry's part in J-D39's
    form, and last the files and folders `deleted on save`, which the
    gesture's `deleted` lists (`creation.remove_stage`); the gesture names
    the recipe at its `stages`, so that the recipe opens at the row's line.
    A refusal of the creation unit answers its own sentence, and a refusal
    of the writers to take an entry out the sentence "An edit not
    applied"."""
    texts = texts or {}
    place = _removal_place(shown, event)
    key = event.get("stage") if isinstance(event, dict) else None
    if place is None or not isinstance(key, str) or not inputs_current(shown, texts):
        return _old_graph(shown, removal="stage")
    root, recipe_file = place
    path = str(recipe_file)
    at = Gesture(None, None, (), None, None, path, "stages")
    try:
        removed = creation.remove_stage(root, key, recipe=recipe_file.name, texts=texts)
    except (OSError, ValueError) as error:
        return at._replace(sentence=str(error))
    entries = []
    for h, period in enumerate(shown.trellis["periods"]):
        if key in period["stages"]:
            entries += _occurrence_entries(shown, h, key, texts)
    entries = list(dict.fromkeys(entries))
    try:
        before = dict(removed.read)
        for entry in entries:
            if entry.path not in before:
                before[entry.path] = _text_at(entry.path, texts)
        made = {**before, **removed.edits}
        after = _without(made, entries)
        words = _removed_words(made, entries)
    except (OSError, ValueError, KeyError, TypeError):
        return at._replace(sentence=gesture_sentence("not-applied", at, None, None, "stage"))
    notes = list(removed.notes)
    # the part of the files deleted on save stands last
    last = [notes.pop()] if removed.deleted else []
    notes += [
        f"{Path(file).name}, {address}: {written} removed, periods {_runs(periods)}"
        for file, address, written, periods in words
    ]
    edits = {file: written for file, written in after.items() if written != before[file]}
    read = {file: before[file] for file in edits}
    note = "; ".join(notes + last)
    return Gesture(edits, read, (), note, None, path, "stages", None, removed.deleted)


def period_removal_edit(shown: TrellisShown, event, texts) -> Gesture:
    """The `Gesture` of `remove period` (unit L, Task 25; AAS, L-D18), the
    button of Details of a selected period, `{reading, period}`, the
    period's index in the whole trellis, for the trellis drawn from the
    reading `shown` and read from a recipe; a function of its arguments
    that reads no state of the page, writes nothing and raises nothing.
    `texts` is the mapping of every unsaved buffer of the tab, by resolved
    path. An event of another reading, a trellis read from a trellis file,
    an index that is no period of the trellis, and inputs that hold
    another text than the reading read answer the sentence "An old graph",
    which asks for the period to be removed again. Otherwise the trellis
    file's entry leaves its text, or its repeat falls by one, the recipe's
    ranges are lowered and answers.yml's record follows, as the creation
    unit answers them (`creation.remove_period`), with its notes, the
    period file it lists as `deleted on save` and the text for the
    restriction's input; the gesture names the trellis file at its
    `periods`. A refusal of the creation unit answers its own sentence."""
    texts = texts or {}
    place = _removal_place(shown, event)
    h = event.get("period") if isinstance(event, dict) else None
    count = len(shown.trellis["periods"])
    whole = isinstance(h, int) and not isinstance(h, bool) and 0 <= h < count
    if place is None or not whole or not inputs_current(shown, texts):
        return _old_graph(shown, removal="period")
    root, recipe_file = place
    path = str(Path(shown.trellis["provenance"]["trellis"]["path"]).resolve())
    try:
        removed = creation.remove_period(root, h, recipe=recipe_file.name, texts=texts)
    except (OSError, ValueError) as error:
        return Gesture(None, None, (), None, str(error), path, "periods")
    note = "; ".join(removed.notes)
    return Gesture(
        removed.edits,
        removed.read,
        (),
        note,
        None,
        path,
        "periods",
        removed.restriction,
        removed.deleted,
    )
