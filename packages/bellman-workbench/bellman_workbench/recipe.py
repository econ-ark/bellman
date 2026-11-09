"""The recipe and the bindings of a model folder, for Bellman Workbench
(model interface specification 0.3, §2.2 rule 1, §3.2 and §3.3): the part of
the backend that §7 names "recipe and bindings", beside `model.py` and
`trellis.py`, and like them free of Solara; with it, the values of the
BellmanType panel (AMD-MI-002 §5 rules 3 to 6): the rows of its Parameters,
Settings and Methods tabs, the place at which a file writes each value, and
the writes of a typed value and of a method's tag.

A folder's trellis has a source: a recipe in the folder's `declaration/`,
the folder that holds every file the language reads (the page Model
directory layout), `declaration/spec.yml` or a variant
`declaration/spec.<name>.yml` beside it, which `load_recipe` reads in its own
folder with the trellis file its key `trellis:` names; or, in a folder whose
`declaration/` holds no recipe, a trellis file whose records name their
stage files and their mappings, which `load_trellis` reads, as
`applications/cons-port/declaration/trellis.port-cons-vfi.yml` does. The
source's syntactic trellis holds one record per stage occurrence; a buffer
of a stage file is elaborated with the origin its occurrence's record
writes and bound as that occurrence by the package's `bind_stage`. Every
file is read by the package's readers; this module composes their answers
and computes none of its own.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

from bellman.native.records import bound_at
from bellman.refusals import ConstructionError, FactoryError
from bellman.stage import admitted_methods, bind_stage, method_types, to_source
from bellman.trellis import (
    append_to_mapping,
    entry_span,
    entry_value,
    load_recipe,
    load_trellis,
    remove_from_mapping,
    replace_entry,
    written_at,
)
from bellman_workbench import model

__all__ = [
    "KINDS",
    "Source",
    "model_sources",
    "trellis_file",
    "source_of",
    "read_source",
    "relative",
    "positions_of",
    "Found",
    "model_of_declaration",
    "declaration_note",
    "find_occurrence",
    "uses_of",
    "Bound",
    "bind_occurrence",
    "record_files",
    "watched_files",
    "Entry",
    "BindingLine",
    "Cell",
    "Row",
    "table",
    "Slot",
    "slots",
    "trellis_entry",
    "Choice",
    "choices",
    "written_name",
    "Written",
    "choose",
    "write_periods",
    "UNVALUED",
    "NO_RECIPE",
    "Place",
    "ParameterRow",
    "SettingRow",
    "MethodRow",
    "Tab",
    "value_place",
    "parameters_tab",
    "settings_tab",
    "methods_tab",
    "write_value",
    "write_method",
]

# the three kinds of binding source, in the order of the columns of the
# Recipe tab (design pass 9 §3)
KINDS = ("calibration", "settings", "methods")

# the verb `bind_stage` reports for each kind, in the order it applies them
_VERBS = (("calibration", "calibrate"), ("methods", "methodize"), ("settings", "configure"))

# the endings of a YAML file
_YAML = (".yml", ".yaml")

# a period range of a recipe's list, `lo-hi`, the terminal period being 0
_RANGE_KEY = re.compile(r"(\d+)-(\d+)")

# the refusals the factory's readers raise, which a reading of the folder
# reports and does not raise: the classes `trellis.py` counts, a LookupError
# among them
_REFUSALS = (ConstructionError, FactoryError, ValueError, LookupError, TypeError)

# the refusals the readers of a file raise: a file that cannot be read, a
# text that is no UTF-8 or no YAML, and an address the text does not hold
_UNREAD = (OSError, UnicodeDecodeError, ValueError, KeyError)


# --- the sources of a folder's trellis ---


class Source(NamedTuple):
    """The source of a folder's trellis: `kind`, `recipe` for a recipe that
    `load_recipe` reads with the trellis file its key `trellis:` names, or
    `trellis` for a trellis file that `load_trellis` reads; `path`, the
    file's path relative to the folder, in posix form."""

    kind: str
    path: str


def _text(folder: model.Folder, relpath, texts=None) -> str:
    """The text of the file at `relpath` under the folder: the text the
    mapping of unsaved texts `texts` holds for its resolved path, where it
    holds one, and else the file's (spec 0.4 §3.1)."""
    path = folder.root / relpath
    held = texts.get(str(path.resolve())) if texts else None
    return held if held is not None else path.read_text(encoding="utf-8")


def _tagged_trellis(folder: model.Folder, relpath: str) -> bool:
    """Whether the YAML file at `relpath` is a trellis file: its document,
    read by the package's reader, carries the tag `!trellis`."""
    try:
        document = entry_value(_text(folder, relpath))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    return isinstance(document, dict) and document.get("__yaml_tag__") == "trellis"


def model_sources(folder: model.Folder, tree=None) -> list[Source]:
    """The sources of the folder's trellis, in the order the window offers
    them (specification §3.3; decision B-D5): each recipe of the folder's
    `declaration/` (`model.FACTORY_FOLDER`), a file there that
    `model.folder_tree` gives the role `recipe`, the folder's main recipe
    first, the one whose stem is `model.RECIPE_STEM`, `declaration/spec.yml`,
    and its variants `declaration/spec.<name>.yml` after it in name order,
    so that the window opens on `declaration/spec.yml` (AAS, 2 October
    2026); and, where `declaration/` holds no recipe, each YAML file of the
    tree tagged `!trellis`, nearest the folder's top first and each level in
    name order, none from a folder named `model.OUTPUT_FOLDER`, which holds
    the saved copies of a Matsya job's returned files, each a model of its
    own (amendment 06 of spec 0.4, §2 item 21). A recipe at the folder's
    top, where the earlier layout kept it, is not offered, since the
    Workbench reads a folder's recipe in `declaration/` alone (the page
    Model directory layout): a folder that
    holds `model.RECIPE` at its top and no recipe in `declaration/` offers
    no source, and `find_occurrence` says why. A folder that holds neither a
    recipe nor a trellis file has no trellis. This function reads the
    recipe's name and its folder from `model.py` alone, through
    `model._role`, `model.RECIPE_STEM`, `model.RECIPE` and
    `model.FACTORY_FOLDER`. `tree` is the folder's tree, the list
    `model.folder_tree` answers, which leaves the hidden names out; it is
    read where it is not given."""
    if tree is None:
        tree = model.folder_tree(folder)
    held = next(
        (entry for entry in tree if entry["path"] == model.FACTORY_FOLDER),
        {"children": []},
    )
    recipes = sorted(
        (
            entry["path"]
            for entry in held["children"]
            if entry["kind"] == "file" and entry["role"] == "recipe"
        ),
        key=lambda path: (Path(path).stem != model.RECIPE_STEM, path),
    )
    if recipes:
        return [Source("recipe", path) for path in recipes]
    if any(entry["kind"] == "file" and entry["path"] == model.RECIPE for entry in tree):
        return []
    found = []

    def walk(entries, depth):
        for entry in entries:
            if entry["kind"] == "folder" and entry["name"] == model.OUTPUT_FOLDER:
                continue
            if entry["kind"] == "folder":
                walk(entry["children"], depth + 1)
            elif Path(entry["path"]).suffix in _YAML:
                found.append((depth, entry["path"]))

    walk(tree, 0)
    return [Source("trellis", path) for _, path in sorted(found) if _tagged_trellis(folder, path)]


def trellis_file(folder: model.Folder, source: Source, texts=None) -> str | None:
    """The trellis file a source reads, relative to the folder: a trellis
    file is its own; a recipe reads the file the package's reader read, which
    its syntactic trellis records under `provenance["trellis"]["path"]`
    (`read_source`). Where the factory refuses the recipe, the answer is the
    path its key `trellis:` writes, joined to the recipe's folder; it is None
    where the recipe writes no path there or does not read. The package
    refuses a recipe that names no trellis file (`recipe-shape`), and no
    file is assumed in its place. The recipe is read through the mapping of
    unsaved texts `texts` (spec 0.4 §3.1)."""
    if source.kind == "trellis":
        return source.path
    try:
        syntactic = read_source(folder, source, texts)
    except _REFUSALS:
        try:
            named = entry_value(_text(folder, source.path, texts), "trellis")
        except (OSError, ValueError, KeyError):
            return None
        if not isinstance(named, str) or not named.strip():
            return None
        return (Path(source.path).parent / named).as_posix()
    return relative(folder, syntactic["provenance"]["trellis"]["path"])


def source_of(folder: model.Folder, relpath: str, sources=None) -> Source | None:
    """The source a click on the file `relpath` shows (specification §2.1):
    the file itself where it is a source of the folder, the recipe that
    reads it where it is a recipe's trellis file; None for any other file,
    which opens as text with the view unchanged. `sources` is the list
    `model_sources` answered, read again where it is not given."""
    for source in model_sources(folder) if sources is None else sources:
        if relpath in (source.path, trellis_file(folder, source)):
            return source
    return None


def read_source(folder: model.Folder, source: Source, texts=None) -> dict:
    """The syntactic trellis of a source: for a recipe, `load_recipe` of
    the recipe's own folder and its name, as the page Model directory layout
    gives the registry, so that the paths it writes are read from that
    folder, `declaration/`, with no fill, so that no keyword binds a
    slot; `load_trellis` of the file for a trellis file. Each reader is
    given `texts`, the mapping from a file's resolved path to the text of
    its unsaved buffer, which the package reads in place of the recipe, the
    trellis file or a period file (spec 0.4 §3.1). The factory's refusal
    propagates."""
    if source.kind == "recipe":
        recipe = folder.root / source.path
        return load_recipe(recipe.parent, recipe.name, texts)
    return load_trellis(folder.root / source.path, texts)


def relative(folder: model.Folder, path) -> str:
    """The path of a file relative to the folder, in posix form; a file the
    model reads outside the folder by `..` steps (decision B-D6)."""
    return Path(os.path.relpath(Path(path).resolve(), folder.root)).as_posix()


# --- the occurrence a buffer is bound as ---


def positions_of(syntactic: dict, stage_path) -> list[tuple[int, str]]:
    """The positions `(h, key)` of a syntactic trellis whose record's stage
    origin is the file `stage_path`, both resolved, in the order of the
    periods and of each period's keys."""
    target = Path(stage_path).resolve()
    return [
        (h, key)
        for h, period in enumerate(syntactic["periods"])
        for key, record in period["stages"].items()
        if Path(record["stage"]["origin"]).resolve() == target
    ]


class Found(NamedTuple):
    """The occurrence a buffer of a stage file is bound as: `source`;
    `position`, `(h, key)`, None where no source binds the file; `record`,
    the occurrence's record; `origin`, the origin the buffer is elaborated
    with, the one the record writes (`load_recipe` and `load_trellis` write
    the path they read), else the file's path relative to the folder;
    `notes`, the sentence refusing the source, or the sentence that the
    source holds no occurrence of the file; `positions`, every position of
    the file in the source, in the order of `positions_of`, none where no
    source binds it (AMD-MI-002 §3 rule 5: the breadcrumb counts the periods
    that hold them); and `refusal`, the `model.Diagnostic` of the source's
    refused reading, whose message is then the one note, so that the list
    under the error mark links its file and line (ruling R51), None where
    the source reads."""

    source: Source | None
    position: tuple[int, str] | None
    record: dict | None
    origin: str
    notes: list[str]
    positions: tuple = ()
    refusal: model.Diagnostic | None = None


def _recipe_at_top(folder: model.Folder) -> bool:
    """Whether the folder holds `model.RECIPE` at its top, where the
    earlier layout kept it, and no `model.factory_path(model.RECIPE)`,
    `declaration/spec.yml`, where the Workbench reads a recipe (the page
    Model directory layout)."""
    root = folder.root
    return (root / model.RECIPE).is_file() and not (
        root / model.factory_path(model.RECIPE)
    ).is_file()


def model_of_declaration(folder: model.Folder) -> Path | None:
    """The model folder above `folder` where `folder` is that model's
    `declaration/` opened by itself, as the desktop application opens a
    folder chosen in its dialog: a folder named `model.FACTORY_FOLDER` that
    holds `model.RECIPE` at its top and no
    `model.factory_path(model.RECIPE)` (`_recipe_at_top`); the folder above
    then holds the recipe at `declaration/spec.yml`, where the Workbench
    reads it. None for any other folder (unit L, Task 28; AAS, L-D23)."""
    if folder.root.name != model.FACTORY_FOLDER or not _recipe_at_top(folder):
        return None
    return folder.root.parent


def declaration_note(above: Path) -> str:
    """The note of a model's `declaration/` opened by itself, which names
    the model folder `above` and says to open it, `this folder is the
    declaration/ of portfolio-choice; open portfolio-choice`; the page's
    button `open portfolio-choice` beside it opens that folder (unit L,
    Task 28; AAS, L-D23)."""
    return f"this folder is the {model.FACTORY_FOLDER}/ of {above.name}; open {above.name}"


def find_occurrence(
    folder: model.Folder, source, stage_relpath: str, wanted=None, texts=None
) -> Found:
    """The `Found` of a buffer of the stage file `stage_relpath`
    (specification §2.2 rule 1): with a source, the occurrence `wanted`,
    `(h, key)`, where it is one of the file's, else the file's first
    occurrence, with its record and the origin the record writes, so that
    the buffer's stage and the trellis's occurrence agree on provenance,
    and with every position of the file in the source. Without a source
    the origin is the path and nothing is noted, apart from a folder that
    holds `model.RECIPE` at its top, where the earlier layout kept it, and
    holds no `model.factory_path(model.RECIPE)`, `declaration/spec.yml`
    (`_recipe_at_top`), which gets one note: for a model's `declaration/`
    opened by itself, the note that names the model folder above and says
    to open it (`model_of_declaration`, `declaration_note`); for any other
    such folder, `spec.yml stands at the folder's top, not at
    declaration/spec.yml; the Workbench reads a recipe at
    declaration/spec.yml` (the page Model directory layout; unit L, Task 28,
    AAS, L-D23). A folder that holds both recipes gets no note. A source
    that does not read is one note, the sentence of its refusal
    (`model.refusal_of`), whose `Diagnostic` the `Found` keeps, and a source
    that holds no occurrence of the file is one note too; the origin is
    then the path. The source is read through the mapping of unsaved texts
    `texts` (`read_source`; spec 0.4 §3.1)."""
    if source is None:
        notes = []
        above = model_of_declaration(folder)
        if above is not None:
            notes.append(declaration_note(above))
        elif _recipe_at_top(folder):
            read_at = model.factory_path(model.RECIPE)
            notes.append(
                f"{model.RECIPE} stands at the folder's top, not at {read_at}; "
                f"the Workbench reads a recipe at {read_at}"
            )
        return Found(None, None, None, stage_relpath, notes)
    try:
        syntactic = read_source(folder, source, texts)
    except _REFUSALS as error:
        # an exception of no class of the package's refusals is printed in
        # the source's file (unit L, Task 21)
        refusal = model.refusal_of(error, source.path, str((folder.root / source.path).resolve()))
        return Found(source, None, None, stage_relpath, [refusal.message], refusal=refusal)
    held = positions_of(syntactic, folder.root / stage_relpath)
    if not held:
        note = f"{source.path} holds no occurrence of {stage_relpath}"
        return Found(source, None, None, stage_relpath, [note])
    position = wanted if wanted in held else held[0]
    record = syntactic["periods"][position[0]]["stages"][position[1]]
    return Found(source, position, record, record["stage"]["origin"], [], tuple(held))


def uses_of(
    folder: model.Folder, sources, stage_relpath: str, texts=None
) -> list[tuple[Source, tuple]]:
    """Where the stage file `stage_relpath` is used (AMD-MI-002 §3 rule 6):
    each source of `sources`, in their order, with every position `(h,
    key)` of the file in it, in the order of `positions_of`, read from the
    source's syntactic trellis (`read_source`), through the mapping of
    unsaved texts `texts` (spec 0.4 §3.1). A source the factory refuses
    holds no position here; `find_occurrence` notes the refusal of the
    tab's own."""
    target = folder.root / stage_relpath
    uses = []
    for source in sources:
        try:
            syntactic = read_source(folder, source, texts)
        except _REFUSALS:
            uses.append((source, ()))
            continue
        uses.append((source, tuple(positions_of(syntactic, target))))
    return uses


class Bound(NamedTuple):
    """A buffer's stage bound as its occurrence: `stage`, the version bound;
    `position`, `(h, key)`, and `occurrence`, `periods[h] / <key>`, the head
    the folder region prints, both None where no source binds the file;
    `notes`, one for each verb failed, after those of the `Found`; and
    `record`, the occurrence's record, None where none."""

    stage: object
    position: tuple[int, str] | None
    occurrence: str | None
    notes: list[str]
    record: dict | None


def bind_occurrence(stage, found: Found) -> Bound:
    """The stage bound as `found` binds it: the package's `bind_stage` on the
    occurrence's record, which applies `calibrate`, `methodize` and
    `configure` in that order, each skipped where its mapping binds nothing,
    a failure leaving the object as the verbs before it made it; one note
    per verb failed, in that order, the package's sentence and nothing
    added (AMD-MI-002 §6a rule 2). A verb skipped, whose kind the source
    lists as a slot or as a file that binds nothing, is no refusal and has
    no note, the tab of that kind saying where no source is listed
    (`_no_source`): a slot is a parameter of the load (K-D29), and the list
    under the error mark holds refusals alone (unit L, Task 21; defect 17 of
    the UX simulation). Without a record the stage is answered as it is,
    with the notes of `found`."""
    if found.record is None:
        return Bound(stage, None, None, list(found.notes), None)
    report = bind_stage(stage, found.record)
    failed = [report.failed[verb] for _, verb in _VERBS if verb in report.failed]
    notes = list(found.notes) + failed
    h, key = found.position
    return Bound(report.stage, found.position, f"periods[{h}] / {key}", notes, found.record)


def record_files(record: dict | None) -> list[Path]:
    """The binding source files a record names, each with the files of its
    parent chain (`provenance["source_lists"]`), in order."""
    if record is None:
        return []
    paths = []
    for kind in KINDS:
        for entry in record["provenance"]["source_lists"].get(kind, []):
            paths += [
                Path(name) for name in (entry.get("path"), *entry.get("parents", [])) if name
            ]
    return paths


def watched_files(folder: model.Folder, found: Found, texts=None) -> list[Path]:
    """The files whose change on disk binds the open buffer again
    (specification §2.2 rule 1): the source and the trellis file it reads,
    where it names one (`trellis_file`, given the mapping of unsaved texts
    `texts`), and each binding source file the occurrence's record names
    with the files of its parent chain, each once and resolved; none
    without a source."""
    if found.source is None:
        return []
    named = (found.source.path, trellis_file(folder, found.source, texts))
    paths = [folder.root / name for name in named if name is not None]
    return list(dict.fromkeys(path.resolve() for path in paths + record_files(found.record)))


# --- the recipe as a table ---


class Entry(NamedTuple):
    """One entry of a binding's sources as the file that writes it writes
    it: `text`, the name written, `calibration/portfolio`, `$cons_method`,
    or `{}` and `{…}` for a mapping written in place; `slot`, whether it is
    a slot, `$<name>`, a place for values supplied by the keyword `<name>`
    when the recipe is loaded (the factory page, §3.3); `file`, the file
    that writes it, relative to the folder; `address`, its address there, at
    which a choice replaces it; and `range`, the period range of its list,
    `0-0`, None for `all` and for the one value of a trellis file's
    record."""

    text: str
    slot: bool
    file: str
    address: str
    range: str | None


class BindingLine(NamedTuple):
    """One line of a binding of a stage of `table`, one list of the
    binding (AAS, L-D10): `name`, the list's key as the recipe writes it,
    `all` or a range `0-2`, None for the one value of a trellis file's
    record; `holds_for`, the periods the list holds for as the block prints
    them, `all`, or `periods 0–2` for the range `0-2` (`_holds_for`), the
    empty text for a record's value, which holds for no range the recipe
    writes; `entries`, the list's entries in their order; and `at_head`,
    whether the list is a range list that holds the head's period."""

    name: str | None
    holds_for: str
    entries: tuple
    at_head: bool


class Cell(NamedTuple):
    """One cell of `table`, a binding of a stage, which the Recipe tab
    draws as a column (design pass 9 §3): `kind`; `entries`, the sources
    that apply at the head's period in the order they merge, a later one
    over an earlier; `lists`, every list the file writes for the stage and
    the kind, in the file's order, by its key, which the tab draws; and
    `lines`, one per list in the same order (`BindingLine`; AAS, L-D10),
    none where the file writes no list."""

    kind: str
    entries: tuple
    lists: dict
    lines: tuple = ()


class Row(NamedTuple):
    """One row of `table`, a stage of the source: the stage's `key`;
    `active`, whether the stage occurs in the head's period; its `cells` by
    kind; `stage`, the `Entry` of the stage file as the file writes it, a
    recipe's `stages.<key>.stage` or the `stage` of a trellis file's record,
    None where none is written; and `periods`, for a recipe, the `Entry` of
    the stage's own periods, `stages.<key>.periods`, its text `lo–hi`
    (`_periods_text`), None where the recipe writes none, which the package
    reads as every period the trellis lists the stage in (the Recipe tab's
    field; design pass 9 §3)."""

    key: str
    active: bool
    cells: dict
    stage: Entry | None
    periods: Entry | None = None


def _shown(value) -> str:
    """The text of a value as the Recipe tab and the Methods tab of the
    panel under the editor print it: a name as it reads, and any other
    scalar as Python prints it; a tag, read as `entry_value` reads one,
    `{"__yaml_tag__": "egm", "value": ""}`, as YAML writes it, `!egm` or
    `!path grid.yml`, and a tagged mapping as its tag and `{…}`; a mapping
    written in place as `{}` where it is empty and `{…}` where it is
    not."""
    if isinstance(value, dict) and "__yaml_tag__" in value:
        tag = f"!{value['__yaml_tag__']}"
        held = {key: item for key, item in value.items() if key != "__yaml_tag__"}
        if set(held) == {"value"}:
            return tag if held["value"] == "" else f"{tag} {_shown(held['value'])}"
        return f"{tag} {_shown(held)}"
    if isinstance(value, dict):
        return "{…}" if value else "{}"
    return str(value)


def _printed_value(text: str, address) -> str:
    """The value at `address` of a YAML text as the Recipe tab and the
    Methods tab print it (`_shown`), the printer with which `choose` checks
    an entry of the recipe and `_rewrite` a method's tag. An address the
    text does not hold is refused with a KeyError."""
    return _shown(entry_value(text, address))


def _reason(error: Exception) -> str:
    """The sentence of a refusal: its message, without the quotes that the
    text of a KeyError writes around it."""
    if isinstance(error, KeyError) and error.args:
        return str(error.args[0])
    return str(error)


def _in_range(name: str, h: int) -> bool:
    """Whether the list `name` of a recipe is a range list, `lo-hi`, that
    holds the period `h`."""
    found = _RANGE_KEY.fullmatch(name)
    return found is not None and int(found[1]) <= h <= int(found[2])


def _holds_for(name: str) -> str:
    """The periods the list `name` of a recipe holds for, as a stage's block
    prints them (AAS, L-D10): `periods 0–2` for the range `0-2`, its hyphen
    printed as the dash of the page's other ranges; the key as written for
    any other list, `all`, and a key the factory refuses."""
    found = _RANGE_KEY.fullmatch(name)
    return name if found is None else f"periods {found[1]}–{found[2]}"


def _recipe_cells(source: Source, key: str, block, h: int) -> dict:
    """The cells of one stage of a recipe at the period `h`: for each kind,
    the lists the stage's block writes, each entry at its address; the
    entries of `all` and of the range that holds `h`; and one line per list,
    with the periods it holds for and whether it is the range that holds
    `h` (AAS, L-D10). A block or a kind that is no mapping, a shape the
    factory refuses, is read as empty, and so is a list written with no
    value, `all:`, which the factory reads as the empty list."""
    cells = {}
    for kind in KINDS:
        written = block.get(kind) if isinstance(block, dict) else None
        if not isinstance(written, dict):
            written = {}
        lists = {
            str(name): tuple(
                Entry(
                    str(item),
                    str(item).startswith("$"),
                    source.path,
                    f"stages.{key}.{kind}.{name}[{number}]",
                    None if name == "all" else str(name),
                )
                # an empty list written `all:` reads as None
                for number, item in enumerate(
                    [] if items is None else items if isinstance(items, list) else [items]
                )
            )
            for name, items in written.items()
        }
        applying = list(lists.get("all", ()))
        for name, entries in lists.items():
            if _in_range(name, h):
                applying += entries
        lines = tuple(
            BindingLine(name, _holds_for(name), entries, _in_range(name, h))
            for name, entries in lists.items()
        )
        cells[kind] = Cell(kind, tuple(applying), lists, lines)
    return cells


def _recipe_stage(source: Source, key: str, block) -> Entry | None:
    """The stage file one stage's entry of a recipe writes, `stage: <path>`,
    as written, at `stages.<key>.stage`; None where the entry writes none."""
    if not isinstance(block, dict) or "stage" not in block:
        return None
    return Entry(_shown(block["stage"]), False, source.path, f"stages.{key}.stage", None)


def _periods_text(value) -> str:
    """The text of a stage's periods as the Recipe tab's field prints it
    (design pass 9 §3): `lo–hi` for the two integers the package reads,
    `[0, 0]` printed `0–0`; any other value as `_shown` prints it, so that
    a value the package refuses is shown as written."""
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(bound, int) and not isinstance(bound, bool) for bound in value)
    ):
        return f"{value[0]}–{value[1]}"
    return _shown(value)


def _recipe_periods(source: Source, key: str, block) -> Entry | None:
    """The periods one stage's entry of a recipe writes, `periods: [lo,
    hi]`, at `stages.<key>.periods`, its text `lo–hi` (`_periods_text`);
    None where the entry writes none."""
    if not isinstance(block, dict) or "periods" not in block:
        return None
    address = f"stages.{key}.periods"
    return Entry(_periods_text(block["periods"]), False, source.path, address, None)


def _record_entry(
    folder: model.Folder, source: Source, h: int, key: str, name: str, texts=None
) -> Entry | None:
    """The one value the record of `periods[h] / <key>` of a trellis file
    writes under `name`, at the address `written_at` gives in the trellis
    file or in the period file of its entry; None where none is written.
    Both files are read through the mapping of unsaved texts `texts` (spec
    0.4 §3.1)."""
    file, address = written_at(
        folder.root / source.path, f"periods[{h}].stages.{key}.{name}", texts
    )
    written = relative(folder, file)
    try:
        value = entry_value(_text(folder, written, texts), address)
    except KeyError:
        return None
    return Entry(_shown(value), False, written, address, None)


def table(folder: model.Folder, source: Source, syntactic: dict, h: int, texts=None) -> list[Row]:
    """The recipe as a table at the head's period `h` (specification §3.2).
    For a recipe, one row per stage its `stages` block writes, in the file's
    order, each cell holding the entries of the stage's list of that kind,
    `all` and then the range that holds `h`, every list opened, and one
    line per list with the periods it holds for, the range that holds `h`
    marked (AAS, L-D10). For a trellis file, one row per stage of
    `periods[h]`, each cell the one value the record writes, a file's path
    or a mapping in place, at the address `written_at` gives in the trellis
    file or in the period file of its entry, as its one line. Each row
    holds the stage file as the file writes it, None where
    none is written. Every value is read by the package's reader of YAML
    text. The recipe, the trellis file and the period files are read
    through the mapping of unsaved texts `texts`, as `read_source` reads
    them (spec 0.4 §3.1): the Recipe tab gives the texts the reading of
    the trellis shown took, so that its rows and the trellis read one
    recipe (AAS, M-D7; design pass 9 §4). The table is total (specification
    §2.2 rule 4): a file that no longer reads gives no rows, as does a
    trellis file whose periods `written_at` cannot follow, and a recipe's
    `stages`, block or kind that is no mapping is read as empty."""
    periods = syntactic["periods"]
    held = periods[h]["stages"] if 0 <= h < len(periods) else {}
    if source.kind == "recipe":
        try:
            stages = entry_value(_text(folder, source.path, texts), "stages")
        except _UNREAD:
            return []
        if not isinstance(stages, dict):
            return []
        return [
            Row(
                str(key),
                key in held,
                _recipe_cells(source, str(key), block, h),
                _recipe_stage(source, str(key), block),
                _recipe_periods(source, str(key), block),
            )
            for key, block in stages.items()
        ]
    rows = []
    try:
        for key in held:
            cells = {}
            for kind in KINDS:
                entry = _record_entry(folder, source, h, key, kind, texts)
                cells[kind] = (
                    Cell(kind, (), {})
                    if entry is None
                    else Cell(
                        kind,
                        (entry,),
                        {"value": (entry,)},
                        (BindingLine(None, "", (entry,), False),),
                    )
                )
            stage = _record_entry(folder, source, h, key, "stage", texts)
            rows.append(Row(key, True, cells, stage))
    except _UNREAD + (TypeError, AttributeError):
        # `written_at` raises TypeError or AttributeError on periods of a
        # shape the factory refuses
        return []
    return rows


class Slot(NamedTuple):
    """One slot of a recipe (the factory page, §3.3): `keyword`, the name
    of the keyword of `load_recipe` that binds it, the slot's name without
    its `$`, `fill` for `$fill`; and `lists`, each source list of the recipe
    that writes it, in the order `slots` reads them, as its stage and kind,
    `tenure · calibration`, followed by its period range where the list is
    a range list, `cons · calibration · 0-0`."""

    keyword: str
    lists: tuple


def slots(rows: list[Row]) -> list[Slot]:
    """The slots the rows `rows` of `table` hold, each once,
    in the order in which the recipe first writes it: by the rows' order,
    the kinds of `KINDS` and the order of each stage's lists, each with
    every list that writes it (unit K's decision K-D29). Each slot is an
    entry the recipe writes as `$<name>`, read from the recipe's text, so
    that the keywords are those `load_recipe` takes. A trellis file's rows
    hold no slot."""
    found = {}
    for row in rows:
        for kind in KINDS:
            for name, entries in row.cells[kind].lists.items():
                named = f"{row.key} · {kind}" + ("" if name == "all" else f" · {name}")
                for entry in entries:
                    if entry.slot:
                        held = found.setdefault(entry.text[1:], [])
                        if named not in held:
                            held.append(named)
    return [Slot(keyword, tuple(lists)) for keyword, lists in found.items()]


def trellis_entry(folder: model.Folder, source: Source, texts=None) -> Entry | None:
    """The trellis file a recipe names at its top, `trellis: <path>`, as the
    recipe writes it, at the address `trellis` (AAS, 2 October 2026: a
    recipe names every file it reads by a path relative to its own folder).
    Nothing is answered where nothing is written: None for a recipe that
    writes no key `trellis:`, which the package refuses (`recipe-shape`), so
    that the page shows the refusal and the table no trellis file; None for
    a trellis file, which is its own trellis file; and None also for a
    recipe that no longer reads, so that the answer is total (specification
    §2.2 rule 4). The recipe is read through the mapping of unsaved texts
    `texts`, as `table` reads it (spec 0.4 §3.1; AAS, M-D7)."""
    if source.kind != "recipe":
        return None
    try:
        value = entry_value(_text(folder, source.path, texts), "trellis")
    except _UNREAD:
        return None
    return Entry(_shown(value), False, source.path, "trellis", None)


class Choice(NamedTuple):
    """A file a cell may take: `path`, relative to the folder; `comment`,
    its first comment line; for a methods file, the `stage` it names and the
    `targets` it binds a method at, its entries `on`; and `unread`, the
    sentence that the file cannot be read, None where it reads."""

    path: str
    comment: str
    stage: str
    targets: tuple
    unread: str | None


def _choice_paths(folder: model.Folder, kind: str) -> list[Path]:
    """The files a cell of `kind` may take, unsorted, where the one layout
    of a model folder places them (the page Model directory layout, §§1 and
    2.3): for `stage`, the stage files under `declaration/stages/`; for
    `trellis`, the YAML files of `declaration/` itself tagged `!trellis`
    (`_tagged_trellis`); for a kind of `KINDS`, the YAML files under the
    folder `<kind>/` of `declaration/` (`model.factory_path`) and, for the
    methods, the methods file `methods.yml` of each stage's folder and each
    addition beside a stage file, `methods.bl` or a replacing selection
    `methods.<variant>.bl` (decision S7-W2), which is never a stage."""
    declaration = folder.root / model.FACTORY_FOLDER
    stages = declaration / "stages"
    if kind == "stage":
        held = stages.rglob("*.bl") if stages.is_dir() else ()
        return [path for path in held if not model.is_addition_file(path)]
    if kind == "trellis":
        held = declaration.glob("*") if declaration.is_dir() else ()
        return [
            path
            for path in held
            if path.is_file()
            and path.suffix in _YAML
            and _tagged_trellis(folder, path.relative_to(folder.root).as_posix())
        ]
    base = folder.root / model.factory_path(kind)
    paths = [path for path in base.rglob("*") if path.suffix in _YAML] if base.is_dir() else []
    if kind == "methods":
        paths += stages.glob("*/methods.yml")
        paths += (
            path
            for pattern in ("*/methods.bl", "*/methods.*.bl")
            for path in stages.glob(pattern)
            if model.is_addition_file(path)
        )
    return paths


def choices(folder: model.Folder, kind: str) -> list[Choice]:
    """The files a cell of `kind` may take (specification §3.2; design pass
    9 §3), a kind of `KINDS`, `stage` or `trellis` (`_choice_paths`), in
    path order, names beginning with "." left out, each with its first
    comment line and, for a methods file, the stage it names and its
    targets, read by the package's reader of YAML text; an addition names
    neither, since the Workbench reads nothing of it (decision S7-W1). The
    listing is total (specification §2.2 rule 4): a file that is no UTF-8
    text is listed with the sentence that it cannot be read, and a methods
    file whose `methods` is no list names no target."""
    declaration = folder.root / model.FACTORY_FOLDER
    found = []
    for path in sorted(_choice_paths(folder, kind)):
        inside = path.relative_to(declaration).parts
        if not path.is_file() or any(p.startswith(".") for p in inside):
            continue
        relpath = path.relative_to(folder.root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            found.append(Choice(relpath, "", "", (), f"the file cannot be read: {error}"))
            continue
        comment = next(
            (line.lstrip("#").strip() for line in text.split("\n") if line.startswith("#")), ""
        )
        stage, targets = "", ()
        if kind == "methods" and path.suffix in _YAML:
            try:
                document = entry_value(text)
            except ValueError:
                document = None
            if isinstance(document, dict):
                stage = str(document.get("stage", ""))
                methods = document.get("methods")
                targets = tuple(
                    str(item.get("on", ""))
                    for item in (methods if isinstance(methods, list) else [])
                    if isinstance(item, dict)
                )
        found.append(Choice(relpath, comment, stage, targets, None))
    return found


def _names_a_file(entry: Entry) -> bool:
    """Whether `entry` is a recipe's `trellis` or a stage's `stage`, which
    the recipe writes with the file's extension, `trellis.yml` and
    `stages/tenure/tenure.bl`, where it writes a source without it."""
    return entry.address == "trellis" or entry.address.endswith(".stage")


def written_name(folder: model.Folder, source: Source, entry: Entry, chosen: str) -> str:
    """The name a choice writes for the file `chosen`, relative to the
    folder, at `entry`: its path relative to the directory of the file that
    writes the entry, from which the package reads that file's paths; in a
    recipe without its extension, `calibration/portfolio` or
    `stages/cons/methods` in `declaration/spec.yml`, as a recipe names a
    source, but with it for the trellis file, a stage file
    (`_names_a_file`), `trellis.yml`, `stages/tenure/tenure.bl`, and an
    addition, `stages/cons/methods.bl`, since the package reads a name
    without its extension as a YAML file; and in a trellis file or a period
    file with it, `methods/cons.yml`, as `load_trellis` reads it."""
    base = (folder.root / entry.file).parent
    name = Path(os.path.relpath(folder.root / chosen, base))
    keeps = source.kind != "recipe" or _names_a_file(entry) or name.suffix == ".bl"
    return (name if keeps else name.with_suffix("")).as_posix()


class Written(NamedTuple):
    """What a write from the BellmanType panel did:
    `saved`; `text`, the file's text after the call; `digest`, its SHA-256,
    both the empty text where the file cannot be read or nothing was read;
    and `reason`, one sentence where nothing was written."""

    saved: bool
    text: str
    digest: str
    reason: str | None


def _save(folder: model.Folder, file: str, current: model.FileText, text: str) -> Written:
    """Writes `text` to the file `file`, relative to the folder, in place
    of `current`, the text read with its digest, by `model.save_file`,
    which writes nothing where the file on disk no longer has that digest;
    a file that cannot be written is refused in one sentence."""
    try:
        result = model.save_file(folder, file, text, current.digest)
    except (OSError, UnicodeDecodeError) as error:
        return Written(False, current.text, current.digest, f"the file cannot be written: {error}")
    if result.saved:
        return Written(True, text, result.digest, None)
    return Written(False, result.text or "", result.digest, result.reason)


def _rewrite(
    folder: model.Folder, file: str, address: str, shown: str, written, printed
) -> Written:
    """Replaces the value at `address` of the file `file`, relative to the
    folder, by `written`, a string, a number, a boolean or a tag, where the
    file still writes `shown` there as `printed` prints the value at
    `address` of its text, the printer of the rows that showed it:
    `_printed_value` for an entry of the recipe and a method's tag,
    `_written_value` for a value of the Parameters and the Settings tabs.
    It is the step that the panel's writes (`write_value`, `write_method`)
    share (specification §3.2; AMD-MI-002 §5 rule 6). The file is read with
    its digest (`model.read_file`), the package's `replace_entry` changes the
    value's characters alone, keeping the other entries, the comments and
    the layout, and `model.save_file` writes the new text with the digest
    of the text read (`_save`), so that a file changed on disk in between is
    not overwritten. Where the file no longer writes `shown` at `address`,
    nothing is written and the write is refused in one sentence, so that a
    row read before the file changed replaces no value it did not show. A
    file that cannot be read or written, and a value `replace_entry` refuses
    to write, such as an anchored value an alias reads, are refused in one
    sentence too, so that every write is total (specification §2.2 rule
    4)."""
    try:
        current = model.read_file(folder, file)
    except (OSError, UnicodeDecodeError) as error:
        return Written(False, "", "", f"the file cannot be read: {error}")
    try:
        now = printed(current.text, address)
    except (KeyError, ValueError):
        now = None
    if now != shown:
        reason = f"the file no longer writes {shown} at {address}"
        return Written(False, current.text, current.digest, reason)
    try:
        text = replace_entry(current.text, address, written)
    except (KeyError, ValueError) as error:
        return Written(False, current.text, current.digest, _reason(error))
    return _save(folder, file, current, text)


def _plain_collection(value) -> bool:
    """Whether `value`, as `entry_value` reads it, is a list, or a mapping
    that is no tag, whose entries are numbers, strings, booleans, nulls or
    such lists and mappings, with no tag at any depth: a value that YAML's
    writer writes in flow style (`_yaml_text`) as a text that reads back as
    the value itself."""
    if isinstance(value, dict) and "__yaml_tag__" not in value:
        return all(_plain_collection(item) or _plain_scalar(item) for item in value.values())
    if isinstance(value, list):
        return all(_plain_collection(item) or _plain_scalar(item) for item in value)
    return False


def _plain_scalar(value) -> bool:
    """Whether `value` is a number, a string, a boolean or a null."""
    return value is None or isinstance(value, (bool, int, float, str))


def _add(folder: model.Folder, file: str, mapping: tuple, key: str, written) -> Written:
    """Adds the entry `<key>: <written>`, `written` a number, a boolean, a
    tag, a string, or a list or a mapping of such values, at the end of the
    mapping at the address `mapping`, its keys and indices, of the file
    `file`, relative to the folder (A2-D8; ruling R34; unit L, Task 16). The
    package's `append_to_mapping` adds the entry, keeping every other
    character and refusing a key the mapping holds. A list or a mapping
    with no tag (`_plain_collection`), which `replace_entry` writes in no
    place, is added in the flow form in which YAML's writer writes it
    (`_yaml_text`), `[[0.6, 0.4], [0.3, 0.7]]`, a text that reads back as
    the value typed; every other value is added with the value `null`, and
    the package's `replace_entry` writes `written` in its place as it
    writes a replaced value, plain, `1.05` or `!pchip`, and reads the text
    back, so that it is added only where the entry reads back as
    `written`. So an added value is written as the writer writes it and not
    as it was typed. The file is read and saved as `_rewrite` reads and
    saves it; every refusal is the package's sentence or one sentence of
    the file's reading or writing, and leaves the file as it was."""
    try:
        current = model.read_file(folder, file)
    except (OSError, UnicodeDecodeError) as error:
        return Written(False, "", "", f"the file cannot be read: {error}")
    try:
        if _plain_collection(written):
            text = append_to_mapping(current.text, mapping, key, _yaml_text(written))
        else:
            added = append_to_mapping(current.text, mapping, key, "null")
            text = replace_entry(added, _address((*mapping, key)), written)
    except (KeyError, ValueError) as error:
        return Written(False, current.text, current.digest, _reason(error))
    return _save(folder, file, current, text)


def choose(folder: model.Folder, source: Source, entry: Entry, chosen: str, text: str) -> str:
    """The text `text` of the file that writes `entry`, its unsaved buffer
    or its file, with `entry` replaced by `chosen` (specification §3.2;
    design pass 9 §4): a slot, `$fill`, written as it is, and else a file,
    relative to the folder, written by its name (`written_name`). The
    package's `replace_entry` changes the entry's characters alone, keeping
    the other sources, the ranges, the comments and the layout; the
    Workbench applies the text answered as one edit of the file's buffer.
    Where `text` no longer writes the entry's text at its address, read as
    the table reads it, the choice is refused with a ValueError in one
    sentence, so that an entry of a table read before the text changed
    replaces no entry the table did not show; an entry `replace_entry`
    refuses to replace, such as an anchored value an alias reads, is
    refused in the package's sentence, so that the choice is total
    (specification §2.2 rule 4). The stage file is not touched and no fill
    is written."""
    name = chosen if chosen.startswith("$") else written_name(folder, source, entry, chosen)
    try:
        now = _printed_value(text, entry.address)
    except (KeyError, ValueError):
        now = None
    if now != entry.text:
        raise ValueError(f"the file no longer writes {entry.text} at {entry.address}")
    try:
        return replace_entry(text, entry.address, name)
    except (KeyError, ValueError) as error:
        raise ValueError(_reason(error)) from None


# the periods typed in the Recipe tab's field: `lo–hi`, `lo-hi`, `lo` or
# `[lo, hi]`, each bound a whole number
_TYPED_PERIODS = re.compile(r"\[?\s*(\d+)\s*(?:[-–,]\s*(\d+)\s*)?\]?")


def write_periods(text: str, key: str, typed: str, shown: str | None) -> str:
    """The recipe's text `text` with the periods of the stage `key` written
    as `typed` in the Recipe tab's field (design pass 9 §4): `lo–hi`,
    `lo-hi`, `[lo, hi]` or `lo` writes `periods: [lo, hi]`, the two numbers
    replaced by the package's `replace_entry` where the stage's block writes
    the key, and the entry added at the end of the block by
    `append_to_mapping` where it does not; the empty text takes the key out
    (`remove_from_mapping`), so that the stage holds in every period the
    trellis lists it in. The bounds are written as typed, the package's
    reading of the recipe refusing `lo > hi` in its own sentence. Refused
    with a ValueError: a text that is no such range, in the page's sentence;
    a block that no longer writes `shown`, the text the field showed (None
    for no key), as `choose` refuses a stale entry; and a layout the
    package's writers cannot change, in their sentence."""
    address = f"stages.{key}.periods"
    typed = typed.strip()
    found = _TYPED_PERIODS.fullmatch(typed)
    if typed and found is None:
        raise ValueError(f"{typed} is no range of periods; write lo–hi")
    try:
        now = _periods_text(entry_value(text, address))
    except KeyError:
        now = None
    except ValueError as error:
        raise ValueError(_reason(error)) from None
    if now != shown:
        raise ValueError(f"the file no longer writes {shown or 'no periods'} at {address}")
    try:
        if not typed:
            return text if now is None else remove_from_mapping(text, f"stages.{key}", "periods")
        lo, hi = int(found[1]), int(found[2] if found[2] is not None else found[1])
        if now is None:
            return append_to_mapping(text, f"stages.{key}", "periods", f"[{lo}, {hi}]")
        written = entry_value(text, address)
        if not isinstance(written, list) or len(written) != 2:
            raise ValueError(f"the entry {address} is not [lo, hi]; write it in the editor")
        return replace_entry(replace_entry(text, f"{address}[0]", lo), f"{address}[1]", hi)
    except (KeyError, ValueError) as error:
        raise ValueError(_reason(error)) from None


# --- the values of the BellmanType panel ---


# the value a row of the Parameters tab shows for a parameter that no
# source of the shown occurrence values (AMD-MI-002 §5 rule 3)
UNVALUED = "unvalued"

# the words of each value tab of a stage shown without a recipe, symbolic,
# and the refusal of a write asked there (AMD-MI-002 §5 rule 3; ruling R28)
NO_RECIPE = "no recipe values them"

# the words of the Methods tab of an occurrence whose methods source is an
# addition of which the stage binds no method, until the package reads
# additions (specification 0.7, unit U3)
ADDITION_UNREAD = "addition, not read yet"

# the addresses of the mapping that the package's reader of a calibration
# or a settings source reads in its file, in the order in which
# `load_calibration` and `load_settings` of `bellman.stage.sources` look
# for them, the document itself last
_MAPPINGS = {
    "calibration": (("calibration", "parameters"), ("calibration",), ("parameters",), ()),
    "settings": (("settings",), ("calibration", "settings"), ()),
}

# a key that an address writes within quotes, as the factory writes one
_QUOTED = re.compile(r"[.\[\]]")

# the words a refusal of a value typed in the Settings tab gives a kind
# (`_kind`), and `number`, the kind wanted where any number is taken, after
# "reads as"; a kind not listed is written as its word, `text` or `null`
_READ_AS = {
    "number": "a number",
    "integer": "an integer",
    "real": "a real number",
    "boolean": "a boolean",
    "tag": "a tag",
    "list": "a list",
    "mapping": "a mapping",
}

# the kinds a value typed in the Settings tab may read as where they differ
# from the kind wanted: `number`, the kind of a setting where the file writes
# a number or no value, since the package types settings nowhere, takes an
# integer or a real number (ruling R30; AMD-MI-002 §5 rule 4)
_ACCEPTED = {"number": ("integer", "real")}


class Place(NamedTuple):
    """Where a file writes a value of an occurrence or the method of a
    target: `file`, relative to the folder; `address`, the entry's address
    there, `calibration.R` or `methods[1].method`; and `line`, the line of
    the value, counted from one, at which a row links the file."""

    file: str
    address: str
    line: int


class ParameterRow(NamedTuple):
    """One row of the Parameters tab (AMD-MI-002 §5 rule 3): `name`, as the
    stage declares it; `domain`, the set it is declared in, as the stage's
    text writes it (`to_source`), the empty text where none is declared;
    `value`, its value at the shown occurrence as the file that writes it
    writes it (`_written_value`), a value no file of the list writes as
    YAML's writer writes it (`_yaml_text`), `unvalued` where no source
    values it, None where the stage is shown without a recipe; and `place`,
    where a file writes the value (`value_place`), None where none does."""

    name: str
    domain: str
    value: str | None
    place: Place | None


class SettingRow(NamedTuple):
    """One row of the Settings tab (AMD-MI-002 §5 rule 4): `name`; `kind`,
    the kind of its value (`_kind`), `integer`, `real`, `boolean` or `text`
    among them; `value`, as the file that writes it writes it
    (`_written_value`), a value no file of the list writes as YAML's writer
    writes it (`_yaml_text`); and `place`, where a file writes it
    (`value_place`), None where none does."""

    name: str
    kind: str
    value: str
    place: Place | None


class MethodRow(NamedTuple):
    """One row of the Methods tab (AMD-MI-002 §5 rule 5), one method the
    stage binds (`stage.methods`): `target`, the target of the one YAML
    entry of the occurrence's methods that binds it (`_written_target`),
    else the place it is bound at, as the package prints it (`bound_at`);
    `tag`, the method as that entry writes it, printed `!Linear`
    (`_shown`), the empty text where the entry writes none, and the method
    bound where no entry binds it; `bound`, the method bound, printed as
    its tag or as `handler only`; `choices`, the tags the package admits at
    the entry's target (`admitted_methods` of `bellman.stage`), none where
    no entry binds it; and `place`, the entry's method, or the entry where
    it names none, in the last methods file that names its target
    (`_method_entry`), None where no file names it."""

    target: str
    tag: str
    bound: str
    choices: tuple
    place: Place | None


class Tab(NamedTuple):
    """One of the tabs Parameters, Settings and Methods of the BellmanType
    panel (AMD-MI-002 §5 rules 3 to 6): `rows`, in order; `file`, the last
    file the occurrence's list of the tab's kind names, relative to the
    folder, which the tab names, None where the list names no file and the
    tab takes no value; and `sentence`, the tab's one sentence, None where
    none applies."""

    rows: tuple
    file: str | None
    sentence: str | None


def _kind(value) -> str:
    """The kind of a value read from a YAML file, which a row of the
    Settings tab prints and a typed value must read as (AMD-MI-002 §5 rules
    3 and 4): `boolean`; `integer`; `real`; `text`; `tag`; `list`;
    `mapping`; `null` for an empty value; else the name of the value's
    type."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "real"
    if isinstance(value, str):
        return "text"
    if isinstance(value, dict):
        return "tag" if "__yaml_tag__" in value else "mapping"
    if isinstance(value, list):
        return "list"
    return "null" if value is None else type(value).__name__


def _yaml_text(value) -> str:
    """A value as YAML's writer writes it, in flow style and on one line
    where the value holds no line break, the form in which `replace_entry`
    writes a number or a boolean: `1.0e-05`, `400`, `true`, `null`; a string
    plain where it reads back as itself and within quotes where it does
    not, `'1.0'`; a list or a mapping with its entries in their order,
    `[1, 2]`, `{a: 1}`; a tag as `_shown` prints it, `!egm`. The text reads
    back, by `entry_value`, as the value, a tagged mapping apart."""
    if isinstance(value, dict) and "__yaml_tag__" in value:
        return _shown(value)
    written = yaml.safe_dump(
        value, default_flow_style=True, allow_unicode=True, sort_keys=False, width=float("inf")
    )
    # YAML's writer ends a document that holds one plain scalar with the
    # marker "..."
    return written.removesuffix("\n").removesuffix("\n...")


def _written_value(text: str, address) -> str:
    """The value at `address` of a YAML text as the file writes it, the
    printer of a row of the Parameters and the Settings tabs (AMD-MI-002 §5
    rule 6): where the value is written on one line, its characters from
    the first to the last as `entry_span` places them, `1.0e-05` where the
    file writes `fues_eps_d: 1.0e-05`, with no comment after it; a value
    written over several lines, a block list or mapping, as YAML's writer
    writes it (`_yaml_text`). Either reads back, by `entry_value`, as the
    value, unless the file writes an alias there. An address the text does
    not hold is refused with a KeyError, as `entry_span` refuses it."""
    span = entry_span(text, address)
    if span.end_line != span.line:
        return _yaml_text(entry_value(text, address))
    # the line as the YAML reader counts its columns, which count no byte
    # order mark; a text the reader reads holds no character at which
    # `splitlines` breaks a line and YAML does not
    line = text.splitlines()[span.line - 1].replace("\ufeff", "")
    return line[span.column - 1 : span.end_column - 1]


def _address(keys: tuple) -> str:
    """An address written from its keys as the factory writes one, the keys
    joined by "." and a key that holds a "." or a bracket within quotes,
    `settings['tol.inner']`, and an index of a list in brackets,
    `methods[1].method`."""
    written = ""
    for key in keys:
        if isinstance(key, int):
            written += f"[{key}]"
        elif _QUOTED.search(key):
            written += f"['{key}']"
        else:
            written += f".{key}" if written else key
    return written


def _no_source(kind: str, key: str | None) -> str:
    """The words of a tab whose occurrence's list of `kind` names no file
    (AMD-MI-002 §5 rule 6, brought to §6a rule 2)."""
    return f"the recipe lists no {kind} source for {key}"


def _list_files(record: dict, kind: str) -> list[str]:
    """The files the record's list of `kind` names, the last first and each
    before the files of its parent chain, since a later source stands over
    an earlier one (the factory page, §3.2) and a file over its parents; a
    slot is no file."""
    return [
        path
        for entry in reversed(record["provenance"]["source_lists"].get(kind, []))
        for path in (entry.get("path"), *entry.get("parents", []))
        if path
    ]


def _last_file(record: dict, kind: str) -> str | None:
    """The last file the record's list of `kind` names, its path as the
    record writes it, the file the tab names and to which a value no file
    writes is added (A2-D8); None where the list names no file, a slot
    being no file."""
    paths = [
        entry["path"]
        for entry in record["provenance"]["source_lists"].get(kind, [])
        if entry.get("path")
    ]
    return paths[-1] if paths else None


def _mapping_read(text: str, kind: str) -> tuple[tuple, dict]:
    """The address of the mapping that the package's reader of a `kind`
    source, `calibration` or `settings`, reads in a file's text, the first
    of `_MAPPINGS[kind]` that the text writes, with that mapping. A text
    that does not read as YAML, and a value there that is no mapping, are
    refused with a ValueError, as the reader refuses them."""
    for address in _MAPPINGS[kind]:
        try:
            found = entry_value(text, address)
        except KeyError:
            continue
        # the first address the text writes; the last, the document itself,
        # is written in every text
        break
    if not isinstance(found, dict):
        raise ValueError(f"the file holds no {kind} mapping")
    return address, found


def _sources(record: dict, kind: str) -> list[tuple]:
    """Each file of the record's list of `kind`, `calibration` or
    `settings`, in the order of `_list_files`, as its path, its text, and
    the address and the contents of the mapping that the package's reader
    reads there (`_mapping_read`); a file that cannot be read, or holds no
    such mapping, is left out."""
    found = []
    for path in _list_files(record, kind):
        try:
            text = Path(path).read_text(encoding="utf-8")
            found.append((path, text, *_mapping_read(text, kind)))
        except _UNREAD:
            continue
    return found


def _value_at(folder: model.Folder, sources: list, name: str):
    """The `Place` at which the first of `sources` (`_sources`) that writes
    `name` writes it, with the value written there and its text as the file
    writes it (`_written_value`); None where none does."""
    for path, text, address, values in sources:
        if name not in values:
            continue
        keys = (*address, name)
        try:
            line = entry_span(text, keys).line
            written = _written_value(text, keys)
        except (KeyError, ValueError):
            continue
        return Place(relative(folder, path), _address(keys), line), values[name], written
    return None


def value_place(folder: model.Folder, record: dict | None, kind: str, name: str) -> Place | None:
    """The place at which the sources of an occurrence write the value of
    `name`, a parameter for `kind` `calibration` and a setting for
    `settings` (AMD-MI-002 §5 rules 3 and 4; the reference view of
    specification §3.2): of the files the record's list of that kind names,
    the last that writes it, a file before its parents, at its entry in the
    mapping that the package's reader of that kind reads there,
    `calibration.R` or `settings.n_a`, with the file relative to the folder
    and the line of the value (`entry_span`). None where no file writes it,
    as for a parameter that the recipe values by a slot `$fill` that no
    keyword binds in the Workbench, and where no record is given."""
    if record is None:
        return None
    found = _value_at(folder, _sources(record, kind), name)
    return None if found is None else found[0]


def parameters_tab(folder: model.Folder, stage, record: dict | None, key: str | None) -> Tab:
    """The Parameters tab of the BellmanType panel for a stage shown as the
    occurrence `key` that `record` binds (AMD-MI-002 §5 rule 3): one row per
    parameter the stage declares, in declaration order
    (`stage.par.list()`), with the set it is declared in as the stage's
    text writes it (`to_source`), its value at the occurrence as the file
    that writes it writes it, the value of the record's `calibration` as
    YAML's writer writes it where no file of the list writes it, or
    `unvalued` where the sources the recipe lists value none, as a slot
    `$fill` that no keyword binds in the Workbench values none, and the
    place a file writes its value (`value_place`). The tab names the last
    file of the occurrence's calibration list, to which a value no file
    writes is added (`write_value`). Where the list names
    no file the rows are kept and the tab, its file None, takes no value and
    says `the recipe lists no calibration source for <key>` (§5 rule 6);
    where the stage is shown without a recipe, `record` None, the rows have
    no value and the tab says `no recipe values them`. The package's refusal
    of the stage's queries is the tab's sentence, nothing added, with no
    row, so that the tab is total."""
    if record is None:
        file, sentence, sources = None, NO_RECIPE, []
    else:
        last = _last_file(record, "calibration")
        file = None if last is None else relative(folder, last)
        sentence = _no_source("calibration", key) if last is None else None
        sources = _sources(record, "calibration")
    try:
        declared = [
            (row["name"], "" if row["domain"] is None else to_source(row["domain"]))
            for row in stage.par.list()
        ]
    except _REFUSALS + (NotImplementedError,) as error:
        return Tab((), file, _reason(error))
    rows = []
    for name, domain in declared:
        found = _value_at(folder, sources, name)
        if record is None:
            value = None
        elif found is not None:
            value = found[2]
        elif name in record["calibration"]:
            value = _yaml_text(record["calibration"][name])
        else:
            value = UNVALUED
        rows.append(ParameterRow(name, domain, value, None if found is None else found[0]))
    return Tab(tuple(rows), file, sentence)


def settings_tab(folder: model.Folder, record: dict | None, key: str | None) -> Tab:
    """The Settings tab of the BellmanType panel for the occurrence `key`
    that `record` binds (AMD-MI-002 §5 rule 4): one row per setting of the
    record's `settings`, the merge of the settings sources the recipe lists
    for the occurrence, in its order, with the kind of its value (`_kind`),
    the value as the file that writes it writes it, or as YAML's writer
    writes a value no file of the list writes, and the place a file writes
    it (`value_place`). The tab
    names the last file of the occurrence's settings list. Where the list
    names no file the tab has no row and says `the recipe lists no settings
    source for <key>` (§5 rule 6); where no record is given, `no recipe
    values them`."""
    if record is None:
        return Tab((), None, NO_RECIPE)
    last = _last_file(record, "settings")
    if last is None:
        return Tab((), None, _no_source("settings", key))
    sources = _sources(record, "settings")
    rows = []
    for name, value in record["settings"].items():
        found = _value_at(folder, sources, name)
        if found is None:
            row = SettingRow(str(name), _kind(value), _yaml_text(value), None)
        else:
            place, held, written = found
            row = SettingRow(str(name), _kind(held), written, place)
        rows.append(row)
    return Tab(tuple(rows), relative(folder, last), None)


def _method_entry(folder: model.Folder, record: dict, target: str):
    """The entry of the last methods file of the record's list that names
    `target` under `on`, a file before its parents (`_list_files`), in which
    a choice of method is written (AMD-MI-002 §5 rule 5): its `Place`, at
    the entry's `method` where it names one and else at the entry itself,
    its index in the file's `methods`, and the entry as the file writes it;
    None where no file names the target, a file that cannot be read naming
    none. It reads the YAML form alone, which goes when the corpus moves to
    additions (decision S7-W6)."""
    for path in _list_files(record, "methods"):
        try:
            text = Path(path).read_text(encoding="utf-8")
            methods = entry_value(text, "methods")
        except _UNREAD:
            continue
        for index, entry in enumerate(methods if isinstance(methods, list) else []):
            if not isinstance(entry, dict) or entry.get("on") != target:
                continue
            address = f"methods[{index}]" + (".method" if "method" in entry else "")
            try:
                line = entry_span(text, address).line
            except (KeyError, ValueError):
                break
            return Place(relative(folder, path), address, line), index, entry
    return None


def _written_target(stage, entries: list, place: str, method) -> str | None:
    """The target of the YAML entry among `entries`, the record's methods,
    that binds `method`, which the stage binds at `place`: the entry that
    names `place` itself, else the one entry whose target the package
    resolves to that method (`stage.methods[target]`), as `E_ε` resolves to
    the expectation it names; None where no entry or several do, as the
    value and the marginal of one Evaluation, at one of which a choice
    would leave the two apart. The YAML entries go when the corpus moves to
    additions (decision S7-W6)."""
    targets = [entry["on"] for entry in entries]
    if place in targets:
        return place
    reaching = []
    for target in targets:
        try:
            if stage.methods[target] is method:
                reaching.append(target)
        except _REFUSALS:
            # the target names no method, or several
            continue
    return reaching[0] if len(reaching) == 1 else None


def methods_tab(folder: model.Folder, stage, record: dict | None, key: str | None) -> Tab:
    """The Methods tab of the BellmanType panel for a stage shown as the
    occurrence `key` that `record` binds (AMD-MI-002 §5 rule 5): one row per
    method the stage binds, read from the package's answer `stage.methods`
    in its order, so that the tab shows nothing the elaboration does not
    answer (decision S7-W1). Where the occurrence's last methods file is a
    YAML file, a row whose method one YAML entry of the occurrence binds is
    named by that entry's target, once for all the places the entry binds,
    offers the tags the package admits there (`admitted_methods` of
    `bellman.stage`) and links the entry, at which a choice is written
    (`_written_target`, `_method_entry`, `write_method`); every other row
    is named by the place the method is bound at and shows it as text.
    Where that file is an addition, each row shows its method as text with
    no choice, since no writer of the `.bl` declaration exists yet
    (decision S7-W3), and where the stage binds no method the tab says
    `addition, not read yet` (`ADDITION_UNREAD`). The tab names the last
    file of the occurrence's methods list. Where the list names no file the
    tab has no row and says `the recipe lists no methods source for <key>`
    (§5 rule 6); where no record is given, `no recipe values them`. A
    refusal of `methodize` stands under the error mark (`bind_occurrence`),
    and the stage then binds no method."""
    if record is None:
        return Tab((), None, NO_RECIPE)
    last = _last_file(record, "methods")
    if last is None:
        return Tab((), None, _no_source("methods", key))
    addition = model.is_addition_file(Path(last))
    entries = [] if addition else record["methods"]["methods"]
    rows = []
    for name, method in stage.methods.items():
        place = str(bound_at(name))
        bound = f"!{method.tag}" if method.tag else "handler only"
        target = _written_target(stage, entries, place, method)
        if target is not None and any(row.target == target for row in rows):
            # one entry that binds several places is one row
            continue
        held = None if target is None else _method_entry(folder, record, target)
        if held is None:
            rows.append(MethodRow(place, bound, bound, (), None))
            continue
        written, _, entry = held
        try:
            choices = admitted_methods(stage, target)
        except _REFUSALS:
            choices = ()
        tag = _shown(entry["method"]) if "method" in entry else ""
        rows.append(MethodRow(target, tag, bound, choices, written))
    sentence = ADDITION_UNREAD if addition and not rows else None
    return Tab(tuple(rows), relative(folder, last), sentence)


def places_refusal(stage) -> str | None:
    """The package's refusal to list the places of `stage` at which methods
    are bound: the sentence of the refusal `stage.places()` raises, nothing
    added (`_reason`); None where it lists them. The page lists that
    sentence once under the error mark while the stage is shown
    (`standing_refusals` of app.py; AMD-MI-002 §6a rule 1), and the Methods
    tab prints it nowhere (unit L, Task 18; the issue
    `places-refuses-the-branching-tenure-stage.md`)."""
    try:
        stage.places()
    except _REFUSALS + (NotImplementedError,) as error:
        return _reason(error)
    return None


def _anchored(typed: str) -> str | None:
    """The refusal of a text typed in the BellmanType panel that writes an
    anchor or an alias, found by the YAML scanner's tokens before the text
    is read, since a typed value is one value written without anchors or
    aliases (ruling R35): `*a writes an alias, which a typed value may not`,
    naming the first that the scanner finds. The package's reader copies
    the entries of a mapping merged through an alias once for each alias,
    so that seven levels of ten aliases, a text of 542 characters, would
    make it copy 10**8 entries before any kind is checked. The scanner
    reads the text into tokens and builds no value; it is the scanner of
    the package's reader of YAML files, a SafeLoader that changes only how
    values are built. A text the
    scanner refuses is refused as `<typed> does not read as YAML`, as any
    text that does not read, and so is a text whose flow collections nest
    deeper than half the interpreter's recursion limit, where the scan
    stops: the reader's composer calls itself through a second function
    for each level and cannot follow such a text, and the scanner's time
    for each token grows with the collections open on its line, up to
    1,024 of them. An anchor is written after "&" and an alias after "*",
    so that a text holding neither character is not scanned and is read
    by the reader alone. None where the scanner finds neither."""
    if "&" not in typed and "*" not in typed:
        return None
    deepest, depth = sys.getrecursionlimit() // 2, 0
    try:
        for token in yaml.scan(typed, Loader=yaml.SafeLoader):
            if isinstance(token, (yaml.AnchorToken, yaml.AliasToken)):
                held = "an anchor" if isinstance(token, yaml.AnchorToken) else "an alias"
                return f"{typed} writes {held}, which a typed value may not"
            if isinstance(token, (yaml.FlowSequenceStartToken, yaml.FlowMappingStartToken)):
                depth += 1
            elif isinstance(token, (yaml.FlowSequenceEndToken, yaml.FlowMappingEndToken)):
                # a closing bracket with none open, which the reader refuses,
                # leaves the count at zero
                depth = max(depth - 1, 0)
            if depth > deepest:
                return f"{typed} does not read as YAML"
    except (yaml.YAMLError, ValueError):
        # a YAML error of the reader or the scanner, and the ValueError of
        # `chr` for an escape beyond the last code point, `"\UFFFFFFFF"`
        return f"{typed} does not read as YAML"
    return None


def _setting_refusal(typed: str, value, found) -> str | None:
    """The refusal of the value `value`, read from the text `typed`, for a
    row of the Settings tab whose value `found` (`_value_at`) shows, None
    where the value is taken (AMD-MI-002 §5 rule 4; ruling R30). The value
    must read as a value of the kind the file writes there (`_kind`), and
    where a number is written there, or no value is, a null included, as an
    integer or a real number, since the package types settings nowhere, the
    type of the method option the setting supplies being checked by
    `configure` when the loop binds the stage again. So `1e-5`, which reads
    as text, is refused where a number stands; the number the file writes,
    typed back as the row shows it, is taken as it stands."""
    held = None if found is None else found[1]
    reads = _kind(value)
    # a number stands there, or no value does
    wanted = "number" if _kind(held) in ("integer", "real", "null") else _kind(held)
    # the number the file writes, typed back, is taken as it stands
    typed_back = found is not None and reads in ("integer", "real") and reads == _kind(held)
    if (typed_back and value == held) or reads in _ACCEPTED.get(wanted, (wanted,)):
        return None
    said = typed or "the empty text"
    return f"{said} reads as {_READ_AS.get(reads, reads)}, not as {_READ_AS.get(wanted, wanted)}"


def write_value(
    folder: model.Folder,
    record: dict | None,
    key: str | None,
    kind: str,
    name: str,
    shown: str,
    typed: str,
) -> Written:
    """Writes the value typed for `name` in a row of the Parameters tab,
    `kind` `calibration`, or of the Settings tab, `settings`, of the
    occurrence `key` that `record` binds, the row showing the value as
    `shown` (AMD-MI-002 §5 rules 3, 4 and 6; A2-D8). The typed text must
    read as YAML, by `entry_value`, and write no anchor or alias, which is
    refused before it is read (`_anchored`, ruling R35). A parameter's value
    is then written whatever it reads as, a number, a text, a list or a
    matrix, and the package's reader of the calibration file judges it
    against the set the parameter's declaration names when the loop binds
    the stage again, its refusal standing under the error mark and on the
    row (unit L, Task 16; defects 4 and 5 of the UX simulation); the tab
    composes no sentence about the value's form. A setting's value must read
    as the kind `_setting_refusal` admits (ruling R30). Where a file of the
    occurrence's list writes the value (`value_place`), the value is
    replaced there by the package's `replace_entry`, the file still writing
    `shown` as the row printed it (`_rewrite`, `_written_value`), so that a
    list in place of a written value is refused in the package's sentence;
    otherwise, where the row showed `unvalued`, the entry `<name>: <value>`
    is added at the end of the mapping that the package's reader reads in
    the last file of the list, a slot being no file, the number written as
    the package's writer writes it, `1.05` for `--- 1.05`, and kept only
    where it reads back as the number typed, a list or a mapping in YAML's
    flow form (`_add`, ruling R34). A stage shown without a recipe, a list
    that names no file, and a value shown that no file of the list writes
    as an entry of its own, a value written through a merge key or no
    longer written, are refused in one sentence, as is every refusal of
    `_rewrite` and `_add`; a refused write leaves the file as it was, and
    no typed text raises."""
    if record is None:
        return Written(False, "", "", NO_RECIPE)
    last = _last_file(record, kind)
    if last is None:
        return Written(False, "", "", _no_source(kind, key))
    typed = typed.strip()
    refused = _anchored(typed)
    if refused is not None:
        return Written(False, "", "", refused)
    try:
        value = entry_value(typed)
    except ValueError:
        return Written(False, "", "", f"{typed} does not read as YAML")
    sources = _sources(record, kind)
    found = _value_at(folder, sources, name)
    refused = _setting_refusal(typed, value, found) if kind == "settings" else None
    if refused is not None:
        return Written(False, "", "", refused)
    if found is not None:
        place = found[0]
        return _rewrite(folder, place.file, place.address, shown, value, _written_value)
    if shown != UNVALUED:
        # the files of the list write the value through a merge key, or no
        # longer write it, as the row read before showed
        refused = f"no {kind} file of {key} writes {name} as an entry of its own"
        return Written(False, "", "", refused)
    mapping = next((held[2] for held in sources if held[0] == last), None)
    if mapping is None:
        return Written(False, "", "", f"{relative(folder, last)} does not read as a {kind} source")
    return _add(folder, relative(folder, last), mapping, name, value)


def write_method(
    folder: model.Folder,
    record: dict | None,
    key: str | None,
    target: str,
    shown: str,
    tag: str,
) -> Written:
    """Writes the method tag `tag`, `!pchip`, one of a row's choices, for
    `target` in the Methods tab, whose row shows its method as `shown`
    (AMD-MI-002 §5 rule 5): the tag alone, in the entry of the last methods
    file of the occurrence's list that names `target` (`_method_entry`).
    Where the entry names a method, its tag is replaced, a value written
    after the tag kept, the file still writing `shown` there (`_rewrite`);
    where it names none, `method: <tag>` is added to the entry (`_add`). A
    stage shown without a recipe, a list that names no file, a text that
    writes an anchor or an alias (`_anchored`, ruling R35), a tag that the
    method table `method_types` does not hold, and a target that no file
    names are refused in one sentence, as is every refusal of `_rewrite` and
    `_add`, among them a method written as a tagged mapping, whose tag
    `replace_entry` does not replace alone."""
    if record is None:
        return Written(False, "", "", NO_RECIPE)
    if _last_file(record, "methods") is None:
        return Written(False, "", "", _no_source("methods", key))
    refused = _anchored(tag)
    if refused is not None:
        return Written(False, "", "", refused)
    if tag not in method_types:
        return Written(False, "", "", f"{tag} is no tag of the method table")
    held = _method_entry(folder, record, target)
    if held is None:
        return Written(False, "", "", f"no methods file the recipe lists for {key} names {target}")
    place, index, entry = held
    # the tag as `entry_value` reads a tag written alone, `!pchip`
    alone = {"__yaml_tag__": tag[1:], "value": ""}
    if "method" not in entry:
        return _add(folder, place.file, ("methods", index), "method", alone)
    method = entry["method"]
    if isinstance(method, dict) and "__yaml_tag__" in method:
        written = {**method, "__yaml_tag__": tag[1:]}
    else:
        written = alone
    return _rewrite(folder, place.file, place.address, shown, written, _printed_value)
