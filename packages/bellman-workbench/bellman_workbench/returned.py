"""A saved copy of the files a Matsya job returned, in the model folder that
downloaded it (specification 0.6, unit G3; amendment 06 of spec 0.4, §2
items 21 to 24 and §4): the copy opened and constructed as a model of its
own; the plan of an adoption, with the reviewed versions, the destinations
and the line differences; the adoption itself, recorded before its first
write and after each write, with the originals kept for recovery; the
restoring of those originals or the completion of a stopped adoption; the
commit offered after a recorded adoption; and the import of a copy's changed
binding files as a variant beside the baseline. The module imports no
Solara.

A saved copy is a folder under `model.OUTPUT_FOLDER`, written once by unit
G2's `matsya_work.download` and never written into (`model.read_only`). A
returned file's destination is its original path, which the prepared record
of its job names under the name the service read it by (unit G2's
`matsya_work.prepare`), and the entry the preparation rewrote, a named
recipe's `trellis:`, is written back to its original value (decision
SG3-19); only the files the language reads, `.bl`, `.yml` and `.yaml`, are
adopted (decision SG3-18). A variant import compares each returned file with
the file at the same path. Every model file is written by the guarded save
`model.save_file`, given the digest the review recorded, so that a file
changed since the review is not overwritten.

The record, by its path in the model folder:

`.bellman-matsya/adoptions/<id>/record.json`, one adoption, written before
the first model file is written and replaced after each write, completed
or failed, and after each file a restore reaches: a JSON object with
  `format`, 1;
  `id`, the adoption's identifier, 32 hexadecimal characters;
  `copy`, the saved copy's path from the folder;
  `first`, whether this plan creates the folder's first declaration;
  `job`, `iteration`, `revision` and `configuration`, the job's identifier,
    the cycles it ran, the session's revision it read and its configuration
    identifier, as the copy's `record.json` gives them, each null where it
    gives none;
  `files`, one object per file of the plan, in the order written:
    `source`, its path in the copy from the folder; `destination`, from the
    folder, the file's original path; `source_sha256`, of the copy's text
    as reviewed; `before_sha256`, of the destination at the review, null
    for a file that did not stand; `rewritten`, each entry written back to
    its original value, `{"entry", "returned", "written"}`;
    `editor_sha256`, of the editor's buffer of the
    destination when the writes began, null where the editor held none;
    `after_sha256`, of the text written, null until it is written;
    `outcome`, `pending`, `written` or `failed`; `sentence`, why a write
    failed, else null; `recovery`, the original's path within the
    adoption's folder, `recovery/<destination>`, null for a file that did
    not stand; and `restored`, `restored` or `failed` once a restore
    reached the file, else null;
  `retained`, each dependency of the copy's model kept as it stands in the
    folder, `{"destination", "sha256", "identical"}`;
  `conflicts`, the sentences of the failures that stand unresolved;
  `state`, `writing`, `adopted`, `stopped`, `restored` or `restore
    failed`; and
  `created_at` and `updated_at`, UTC times in ISO 8601.

`.bellman-matsya/adoptions/<id>/recovery/<destination>`, the original text
of each destination that stood, written before the first model file is
written.
"""

from __future__ import annotations

import datetime
import difflib
import hashlib
import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import NamedTuple

from filelock import FileLock, Timeout

from bellman.stage import graph_refusal
from bellman.syntax.vocabulary import CONTINUATION, VALUE_ROLES, WRITTEN_MARK
from bellman.trellis import entry_value, replace_entry
from bellman_workbench import creation, matsya_work, model, recipe, trellis

ADOPTIONS_FOLDER = ".bellman-matsya/adoptions"
RECORD = "record.json"
RECOVERY = "recovery"
FORMAT = 1

# the rules of the package's refusals that name a file the reading did not
# find: a source named in the registry, and a file that does not exist
MISSING_RULES = ("recipe-source", "readable-file")

# the kinds of file a variant import copies under the variant's name
_BINDING_KINDS = ("calibration", "settings", "methods")


class Inspected(NamedTuple):
    """A saved copy constructed as a model of its own (`inspect`): `copy`,
    its path from the folder; `folder`, the copy as a model folder; its
    `sources`, as `recipe.model_sources` reads them in the copy; `source`,
    the one constructed, the first, None where it holds none; `shown`, the
    trellis constructed, None where the construction was refused;
    `missing`, one sentence per dependency the copy's model reads and the
    copy does not hold; `construction`, one sentence per refusal of the
    copy's local construction and binding; `service`, the job as the
    copy's `record.json` holds it, the service's comparison among its
    results, None where the copy holds no record; and `terminal_inputs`,
    the continuation values read outside the selected terminal-period routes."""

    copy: str
    folder: model.Folder
    sources: tuple
    source: recipe.Source | None
    shown: trellis.TrellisShown | None
    missing: tuple
    construction: tuple
    service: dict | None
    terminal_inputs: tuple[str, ...] = ()


class Planned(NamedTuple):
    """The plan of an adoption (`plan`): `copy`, the saved copy's path
    from the folder; `files`, one object per file selected, `{"source",
    "destination", "source_sha256", "before_sha256", "rewritten",
    "difference", "unsaved"}`, `rewritten` the entries written back to
    their original values, the difference the unified line difference from
    the destination to the text to be written and `unsaved` that from the
    destination on disk to the editor's buffer, None where the buffer holds
    no unsaved text; `retained`, the dependencies kept as they stand,
    `{"destination", "sha256", "identical"}`; and `refusals`, one sentence
    per reason the plan cannot be adopted."""

    copy: str
    files: tuple
    retained: tuple
    refusals: tuple
    first: bool = False


class Adoption(NamedTuple):
    """What `adopt`, `restore` and `complete` answered: `id`, the
    adoption's identifier, None where nothing was recorded; `record`, the
    record as it stands; `changed`, the destinations this call wrote; and
    `refusals`, one sentence per reason it wrote nothing or stopped."""

    id: str | None
    record: dict | None
    changed: tuple
    refusals: tuple


class Imported(NamedTuple):
    """What `import_variant` answered: `files`, the files written, from the
    folder; `copied`, one object per returned file copied under the
    variant's name, `{"source", "base", "written"}`; `shared`, the
    baseline's files the variant names as they stand; `rewritten`, each
    entry of the variant's recipe that now names a copy, `{"file",
    "address", "written", "now"}`; `retained_recipe`, whether the variant's
    recipe is the baseline's, the copy holding none; `baseline`, the
    SHA-256 of each file the baseline's recipe reads, by its path, as they
    stand after the import; and `refusals`, one sentence per reason nothing
    was written."""

    files: tuple
    copied: tuple
    shared: tuple
    rewritten: tuple
    retained_recipe: bool
    baseline: dict
    refusals: tuple


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


def _text(path: Path) -> str:
    """The text of the file at `path`, read as UTF-8 with its newlines as
    written, as `model.read_file` reads it."""
    with open(path, encoding="utf-8", newline="") as stream:
        return stream.read()


def _difference(before: str, after: str, old: str, new: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True), after.splitlines(keepends=True), old, new
        )
    )


def _service(copied: model.Folder) -> dict | None:
    """The job as the copy's `record.json` holds it, None where the copy
    holds no such file."""
    path = copied.root / "record.json"
    return json.loads(_text(path)) if path.is_file() else None


# the endings of the files of `declaration/` the language reads: a stage
# file, and the YAML files of a recipe, a trellis, a period and the bindings
_MODEL_ENDINGS = (".bl", ".yml", ".yaml")


def _copy_files(copied: model.Folder) -> list[str]:
    """The files of the copy's `declaration/` the language reads (`.bl`,
    `.yml` and `.yaml`), by their paths from the copy, in path order, names
    beginning with "." left out; a note the job's writer left beside a
    stage, a Markdown file, is reviewed in the copy and never adopted or
    imported (decision SG3-18)."""
    base = copied.root / model.FACTORY_FOLDER
    found = []
    for path in sorted(base.rglob("*")) if base.is_dir() else []:
        relative = path.relative_to(copied.root)
        if (
            path.is_file()
            and path.suffix in _MODEL_ENDINGS
            and not any(part.startswith(".") for part in relative.parts)
        ):
            found.append(relative.as_posix())
    return found


# --- the copy as a model of its own ---


def _terminal_inputs(shown: trellis.TrellisShown) -> tuple[str, ...]:
    """List the continuation values the terminal period takes as data."""
    periods = shown.trellis["periods"]
    if not periods:
        return ()
    routed = {
        (route.source[1], component.required)
        for route in shown.selection.routes
        if route.source[0] == 0
        for component in route.components
    }
    inputs = []
    for key, stage in periods[0]["stages"].items():
        if graph_refusal(stage, "builders", "backward") is not None:
            continue
        for wire in stage.builder.bwd.signature().inputs:
            if (
                wire.sort.perch == CONTINUATION
                and wire.sort.role in VALUE_ROLES
                and (key, str(wire.identity)) not in routed
            ):
                name = wire.identity.field + WRITTEN_MARK[CONTINUATION]
                inputs.append(f"{name} · {key}")
    return tuple(inputs)


def inspect(folder: model.Folder, copy: str) -> Inspected:
    """The saved copy at `copy`, its path from the folder, opened under its
    own root and constructed from its first source by the reading the page
    makes (`trellis.show_trellis`), so that its recipe, its dependencies and
    its bindings are its own (amendment 06 §2 item 21). A refusal of the
    reading whose rule names a file not found (`MISSING_RULES`), and each
    file read outside the copy, is a missing dependency; every other
    refusal, and each binding note, is a construction error. Neither is
    mixed with the service's comparison, which `service` keeps as the copy's
    record gives it. The backward signatures and selected routes identify
    the terminal inputs. Writes nothing."""
    copied = model.open_folder(folder.root / copy)
    sources = tuple(recipe.model_sources(copied))
    service = _service(copied)
    if not sources:
        missing = (
            f"{copy} holds no recipe in {model.FACTORY_FOLDER}/ and no trellis file, so it "
            "constructs no model",
        )
        return Inspected(copy, copied, (), None, None, missing, (), service)
    source = sources[0]
    outcome = trellis.show_trellis(copied, source)
    missing, construction = [], []
    if outcome.refusal is not None:
        sentence = trellis.relative_sentence(copied, outcome.refusal.message)
        (missing if outcome.refusal.rule in MISSING_RULES else construction).append(sentence)
    shown = outcome.shown if outcome.refusal is None else None
    if shown is not None:
        for path in shown.files:
            if not Path(path).resolve().is_relative_to(copied.root):
                missing.append(
                    f"{recipe.relative(copied, path)} lies outside the saved copy, which holds "
                    "no file of that name"
                )
        notes = trellis.binding_notes(shown.binding)
        construction += [trellis.relative_sentence(copied, note) for note in notes]
    return Inspected(
        copy, copied, sources, source, shown, tuple(missing), tuple(construction), service,
        _terminal_inputs(shown) if shown is not None else (),
    )


# --- the plan of an adoption ---


# a stage file as the client's `job files` places it in a copy,
# `declaration/stages/<key>/<key>.bl`
_STAGE_FILE = re.compile(rf"{model.FACTORY_FOLDER}/stages/([^/]+)/\1\.bl")


def _sent_name(path: str) -> str:
    """The name under which the service read and returned the file that the
    client's `job files` wrote at `path`, its path in the copy: a stage file
    `declaration/stages/<key>/<key>.bl` as `<key>.bl`, and every other file
    by its path within `declaration/`, the names unit G2's prepared record
    lists (`matsya_work.prepare`)."""
    stage = _STAGE_FILE.fullmatch(path)
    if stage is not None:
        return f"{stage.group(1)}.bl"
    return path.removeprefix(f"{model.FACTORY_FOLDER}/")


def _prepared_of(folder: model.Folder, job_id: str) -> dict | None:
    """The Workbench's prepared record that the job `job_id` was submitted
    from, read through the folder's request record of the job (unit G2's
    `matsya_work.submit`); None where no request record of the folder names
    the job."""
    requests = _checked_path(folder.root, matsya_work.REQUESTS_FOLDER, ".bellman-matsya")
    for path in sorted(requests.glob("*.json")) if requests.is_dir() else []:
        request_path = _checked_path(
            folder.root, path.relative_to(folder.root).as_posix(), ".bellman-matsya"
        )
        request = json.loads(_text(request_path))
        if request.get("kind") == "job" and request.get("accepted") == job_id:
            prepared = _checked_path(folder.root, request["prepared"], ".bellman-matsya")
            if prepared.parent != folder.root / matsya_work.PREPARED_FOLDER:
                raise ValueError("the prepared record lies outside the project's prepared folder")
            return json.loads(_text(prepared))
    return None


class _Originals(NamedTuple):
    """The original paths of a copy's files, as the prepared record of its
    job gives them: `job`, the job's identifier; `paths`, each file's
    original path by the name the service read it under; and `rewritten`,
    by an original path, the entries the preparation rewrote in that file,
    pairs `(entry, written)` with the value the original writes."""

    job: str
    paths: dict
    rewritten: dict


def _originals(
    folder: model.Folder, copied: model.Folder, copy: str
) -> tuple[_Originals | None, str | None]:
    """The `_Originals` of the saved copy at `copy`, and None; or None and
    the sentence that refuses its adoption, where no prepared record of its
    job stands in the folder (decision SG3-19)."""
    job = _service(copied) or {}
    prepared = _prepared_of(folder, job["id"]) if job.get("id") else None
    if prepared is None:
        who = job.get("id") or f"the job of {copy}"
        return None, (
            f"no prepared record of {who} stands in this folder, so the files of {copy} have no "
            "original paths; review the copy on its own"
        )
    rewritten = {}
    for item in prepared.get("rewritten", []):
        rewritten.setdefault(item["path"], []).append((item["entry"], item["written"]))
    paths = {entry["name"]: entry["path"] for entry in prepared["files"]}
    return _Originals(job["id"], paths, rewritten), None


def _unnamed(originals: _Originals, copy: str, path: str) -> str:
    """The sentence that refuses the returned file at `path` in the copy,
    which the prepared record of its job does not name."""
    return (
        f"the prepared record of {originals.job} names no file sent as {_sent_name(path)}, so "
        f"{copy}/{path} has no original path; review the copy on its own"
    )


def _adopted_text(text: str, rewrites) -> str:
    """`text`, a returned file's, with each entry of `rewrites`, pairs
    `(entry, written)`, written back to the value its original writes, by
    the package's `replace_entry`: the recipe's `trellis:` entry, which the
    preparation sent as `trellis.yml`."""
    for entry, written in rewrites:
        text = replace_entry(text, entry, written)
    return text


def _unsaved_sentence(destination: str) -> str:
    return (
        f"{destination} holds unsaved changes in the editor; save or discard them before the "
        "adoption"
    )


def _checked_path(root: Path, relative: str, first: str) -> Path:
    """A relative path with no symlink or non-directory parent."""
    if not isinstance(relative, str):
        raise ValueError(f"the path under {first}/ is invalid")
    path = Path(relative)
    if (
        path.is_absolute()
        or path.as_posix() != relative
        or not path.parts
        or path.parts[0] != first
        or ".." in path.parts
        or '\\' in relative
    ):
        raise ValueError(f"{relative} lies outside {first}/")
    checked = root
    for part in path.parts:
        if checked.exists() and not checked.is_dir():
            raise ValueError(f"{relative} has a parent that is not a directory")
        checked /= part
        if checked.is_symlink():
            raise ValueError(f"{relative} passes through a symbolic link")
    return checked


def _empty_declaration(folder: model.Folder) -> bool:
    declaration = _checked_path(folder.root, model.FACTORY_FOLDER, model.FACTORY_FOLDER)
    return not declaration.exists() or (
        declaration.is_dir()
        and all(path.is_dir() and not path.is_symlink() for path in declaration.rglob("*"))
    )


def _mapped_closure(source: recipe.Source, texts: dict[str, str]) -> str | None:
    """The refusal of the proposed destinations and references, checked
    with the native reader on a staged copy of `texts`: the Workbench's own
    sentence where two returned files name one destination or the staged
    declaration reads a file outside its reviewed destinations; `the
    proposed declaration does not read: <sentence>` where the package
    refuses the staged copy, its sentence that of the one conversion,
    which logs an exception of no class of the package's refusals
    (`model.diagnostic_of`), or where the disk fails, its sentence the
    error as Python states it; None where the declaration reads within its
    destinations."""
    try:
        with tempfile.TemporaryDirectory(prefix="bellman-adoption-") as directory:
            staged = model.Folder(Path(directory).resolve(), None)
            for destination, text in texts.items():
                path = staged.root / destination
                if path.exists():
                    return f"more than one returned file names {destination}"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="")
            try:
                _, dependencies = matsya_work.required_files(staged, source, {})
            except recipe._REFUSALS as error:
                sentence = model.sentence(model.diagnostic_of(error, "read", source.path))
                return f"the proposed declaration does not read: {sentence}"
            declaration = staged.root / model.FACTORY_FOLDER
            if any(not path.is_relative_to(declaration) or not path.is_file()
                   for path in dependencies):
                return "the proposed declaration reads a file outside its reviewed destinations"
    except OSError as error:
        return f"the proposed declaration does not read: {error}"
    return None


def plan(
    folder: model.Folder,
    copy: str,
    selection=None,
    buffers: dict | None = None,
    retained=(),
    *,
    changed_only: bool = False,
) -> Planned:
    """Review the copy's declaration at its original or proposed new paths.

    A first declaration uses the copy's paths. A replacement can add a file
    its model reads where the prepared record names no original for it.
    Originals retain their mapped paths and rewritten references.
    """
    refusal = model.read_only(folder)
    if refusal:
        return Planned(copy, (), (), (refusal,))
    try:
        copy_root = _checked_path(folder.root, copy, model.OUTPUT_FOLDER)
        if len(Path(copy).parts) != 2:
            raise ValueError(f"{copy} does not name a saved returned copy")
        copied = model.open_folder(copy_root)
        first = _empty_declaration(folder)
        base = _checked_path(copied.root, model.FACTORY_FOLDER, model.FACTORY_FOLDER)
        if any(path.is_symlink() for path in base.rglob("*")):
            raise ValueError(f"the declaration of {copy} contains a symbolic link")
        _checked_path(folder.root, f"{copy}/record.json", model.OUTPUT_FOLDER)
        originals, refusal = _originals(folder, copied, copy)
    except (OSError, ValueError) as error:
        return Planned(copy, (), (), (str(error),))
    first = first and (originals is None or not originals.paths)
    if originals is None and not first:
        return Planned(copy, (), (), (refusal,))
    if not first and not originals.paths:
        return Planned(copy, (), (), (f"{copy} has no original paths; review the copy on its own",))
    paths = originals.paths if originals else {}
    rewritten = originals.rewritten if originals else {}

    sources = recipe.model_sources(copied)
    if not sources:
        return Planned(
            copy, (), (), (f"{copy} holds no recipe and no trellis file, so its model reads nothing",)
        )
    source = sources[0]
    # what the package raises while it reads the copy's model goes through
    # the one conversion; the disk's error and the Workbench's own checks of
    # the files the model reads print their own sentences
    try:
        _, reads = matsya_work.required_files(copied, source, {})
    except OSError as error:
        return Planned(copy, (), (), (f"the model of {copy} does not read: {error}",))
    except recipe._REFUSALS as error:
        subject = str((copied.root / source.path).resolve())
        sentence = model.sentence(model.diagnostic_of(error, "read", subject))
        return Planned(copy, (), (), (f"the model of {copy} does not read: {sentence}",))
    dependencies = [recipe.relative(copied, read) for read in reads]
    try:
        for dependency in dependencies:
            read = _checked_path(copied.root, dependency, model.FACTORY_FOLDER)
            if not read.is_file():
                raise ValueError(f"the model of {copy} requires {dependency}, which it does not hold")
    except (OSError, ValueError) as error:
        return Planned(copy, (), (), (str(error),))

    listed = _copy_files(copied)
    chosen = listed if selection is None else list(dict.fromkeys(selection))
    if selection is None and (first or changed_only):
        chosen = [path for path in chosen if path in dependencies or _sent_name(path) in paths]
    refusals = [f"{copy} holds no {path}" for path in chosen if path not in listed]
    destinations, occupied = {}, set()
    for path in dict.fromkeys([*dependencies, *chosen]):
        original = paths.get(_sent_name(path))
        if original is None and path not in dependencies:
            if path in listed:
                refusals.append(_unnamed(originals, copy, path) if originals else
                                f"{copy}/{path} is not read by its declaration")
            continue
        destination = original or path
        try:
            target = _checked_path(folder.root, destination, model.FACTORY_FOLDER)
            if target.exists() and (original is None or not target.is_file()):
                raise ValueError(f"{destination} already exists at the proposed destination")
            if destination in occupied:
                raise ValueError(f"more than one returned file names {destination}")
        except (OSError, ValueError) as error:
            refusals.append(str(error))
            continue
        occupied.add(destination)
        destinations[path] = destination

    files, selected, planned_texts = [], set(), {}
    for path in chosen:
        if path not in listed or path not in destinations:
            continue
        destination = destinations[path]
        returned_text = _text(copied.root / path)
        rewrites = rewritten.get(destination, [])
        text = _adopted_text(returned_text, rewrites)
        standing = folder.root / destination
        before = _text(standing) if standing.is_file() else None
        held = (buffers or {}).get(destination)
        if changed_only and text == before and (held is None or held.text == before):
            continue
        unsaved = None
        if held is not None and held.text != (before or ""):
            unsaved = _difference(
                before or "", held.text, f"{destination} (disk)", f"{destination} (editor)"
            )
            refusals.append(_unsaved_sentence(destination))
        selected.add(path)
        planned_texts[destination] = text
        files.append(
            {
                "source": f"{copy}/{path}",
                "destination": destination,
                "source_sha256": _sha256(returned_text),
                "before_sha256": None if before is None else _sha256(before),
                "rewritten": [
                    {"entry": entry, "returned": entry_value(returned_text, entry),
                     "written": written}
                    for entry, written in rewrites
                ],
                "difference": _difference(
                    before or "", text, f"{destination} (model)", f"{copy}/{path} (returned)"
                ),
                "unsaved": unsaved,
            }
        )
    kept = []
    for dependency in dependencies:
        if dependency in selected or dependency not in destinations:
            continue
        destination = destinations[dependency]
        standing = folder.root / destination
        if not standing.is_file():
            refusals.append(
                f"the selection omits {copy}/{dependency}, which the copy's model reads, and "
                f"{destination} does not stand; select it"
            )
            continue
        current = _text(standing)
        digest = _sha256(current)
        returned_text = _adopted_text(
            _text(copied.root / dependency), rewritten.get(destination, [])
        )
        identical = digest == _sha256(returned_text)
        if identical or destination in retained:
            planned_texts[destination] = current
            kept.append({"destination": destination, "sha256": digest, "identical": identical})
            continue
        refusals.append(
            f"the selection omits {copy}/{dependency}, which the copy's model reads, and "
            f"{destination} differs from it; select it or retain {destination}"
        )
    if not refusals and (first or any(_sent_name(path) not in paths for path in selected)):
        refused = _mapped_closure(recipe.Source(source.kind, destinations[source.path]),
                                  planned_texts)
        if refused is not None:
            refusals.append(refused)
    return Planned(copy, tuple(files), tuple(kept), tuple(refusals), first)


# --- the adoption and its record ---


def _reviewed_source(folder: model.Folder, entry: dict) -> str:
    source = _checked_path(folder.root, entry["source"], model.OUTPUT_FOLDER)
    if source.is_file():
        text = _text(source)
        if _sha256(text) == entry["source_sha256"]:
            return text
    raise ValueError(f"{entry['source']} no longer holds the reviewed text; review the adoption again")


def _checks(folder: model.Folder, entries, buffers: dict | None) -> list[str]:
    """Compare the reviewed source, destination and editor before writing."""
    refusals = []
    for entry in entries:
        destination = entry["destination"]
        try:
            _reviewed_source(folder, entry)
            standing = _checked_path(folder.root, destination, model.FACTORY_FOLDER)
            current = _text(standing) if standing.exists() else None
        except (OSError, ValueError) as error:
            refusals.append(str(error))
            continue
        if (None if current is None else _sha256(current)) != entry["before_sha256"]:
            refusals.append(
                f"{destination} changed on disk since the review; review the adoption again"
            )
            continue
        held = (buffers or {}).get(destination)
        if held is not None and held.text != (current or ""):
            refusals.append(_unsaved_sentence(destination))
    return refusals


def _retained_checks(folder: model.Folder, entries, buffers: dict | None) -> list[str]:
    """Ensure a retained dependency still supplies the reviewed text."""
    refusals = []
    for entry in entries:
        destination = entry["destination"]
        try:
            standing = _checked_path(folder.root, destination, model.FACTORY_FOLDER)
            current = _text(standing)
        except (OSError, ValueError) as error:
            refusals.append(str(error))
            continue
        if _sha256(current) != entry["sha256"]:
            refusals.append(
                f"{destination} changed on disk since the review; review the adoption again"
            )
            continue
        held = (buffers or {}).get(destination)
        if held is not None and held.text != current:
            refusals.append(_unsaved_sentence(destination))
    return refusals


def _adoption_lock(folder: model.Folder) -> FileLock:
    refusal = model.read_only(folder)
    if refusal:
        raise ValueError(refusal)
    path = _checked_path(folder.root, f"{ADOPTIONS_FOLDER}/.lock", ".bellman-matsya")
    return FileLock(path, timeout=0)


def _writable(path: Path) -> bool:
    """Whether the file at `path` can be written: the file where it stands,
    else the nearest folder above it that stands."""
    if path.exists():
        return os.access(path, os.W_OK)
    for above in path.parents:
        if above.exists():
            return os.access(above, os.W_OK)
    return False


def _write_record(folder: model.Folder, record: dict, expected: str | None) -> str:
    """Writes the adoption's record by the guarded save, `expected` the
    digest of the record it replaces, None for a new one, and answers the
    digest written; a refused write raises OSError, since the adoption must
    not write a model file without its record."""
    record["updated_at"] = _now()
    path = f"{ADOPTIONS_FOLDER}/{record['id']}/{RECORD}"
    _checked_path(folder.root, path, ".bellman-matsya")
    saved = model.save_file(folder, path, json.dumps(record, ensure_ascii=False, indent=1) + "\n",
                            expected)
    if not saved.saved:
        raise OSError(f"{path} was not written: {saved.reason}")
    return saved.digest


def _job_fields(folder: model.Folder, copy: str) -> dict:
    """The job, its iteration, its revision and its configuration, as the
    copy's `record.json` gives them, each None where it gives none."""
    job = _service(model.open_folder(folder.root / copy)) or {}
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    return {
        "job": job.get("id"),
        "iteration": result.get("cycles_run"),
        "revision": job.get("revision"),
        "configuration": job.get("configuration_id"),
    }


def _listed(names) -> str:
    names = list(names)
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def _writes(folder: model.Folder, record: dict, digest: str, entries, write) -> Adoption:
    """Writes each pending file of `entries`, entries of `record["files"]`,
    by `write`, the guarded save's signature, given the digest the review
    recorded; the record is replaced after each write, completed or
    failed. The first failure stops the adoption, which names the files
    changed and offers restoring the originals or completing the plan."""
    changed = []
    for entry in entries:
        rewrites = [(item["entry"], item["written"]) for item in entry["rewritten"]]
        try:
            _checked_path(folder.root, entry["destination"], model.FACTORY_FOLDER)
            text = _adopted_text(_reviewed_source(folder, entry), rewrites)
            saved = write(folder, entry["destination"], text, entry["before_sha256"])
            failure = None if saved.saved else saved.reason
        except (OSError, ValueError) as error:
            failure = str(error)
        if failure is None:
            entry.update(outcome="written", after_sha256=saved.digest, sentence=None)
            changed.append(entry["destination"])
            digest = _write_record(folder, record, digest)
            continue
        entry.update(outcome="failed", sentence=failure)
        record["conflicts"].append(f"{entry['destination']}: {failure}")
        record["state"] = "stopped"
        _write_record(folder, record, digest)
        written = [item["destination"] for item in record["files"] if item["outcome"] == "written"]
        done = f"{_listed(written)} changed" if written else "no file changed"
        sentence = (
            f"the adoption stopped at {entry['destination']}: {failure}; {done}; restore the "
            "originals or complete the reviewed plan"
        )
        return Adoption(record["id"], record, tuple(changed), (sentence,))
    record["state"] = "adopted"
    record["conflicts"] = []
    _write_record(folder, record, digest)
    return Adoption(record["id"], record, tuple(changed), ())


def adopt(
    folder: model.Folder, planned: Planned, buffers: dict | None = None, write=model.save_file
) -> Adoption:
    """Adopts the reviewed plan `planned` (amendment 06 §2 items 22 and 23):
    the checks of `_checks` and of write permission first, each refusal
    leaving every file as it stands; then the record, written before the
    first model file; then the original of each destination that stands,
    kept in the adoption's recovery area; then each file of the plan,
    written from the saved copy the plan names, never from a later job or
    iteration, through `write`, the guarded save by default, with the
    record replaced after each write. `buffers` holds the editor's buffers
    as `plan` reads them. Nothing is committed."""
    if planned.refusals or not planned.files:
        return Adoption(None, None, (), planned.refusals)
    try:
        refusals = _adoption_checks(folder, planned, buffers)
        if refusals:
            return Adoption(None, None, (), tuple(refusals))
        with _adoption_lock(folder):
            return _adopt(folder, planned, buffers, write)
    except Timeout:
        return Adoption(None, None, (), ("another adoption is writing this declaration",))
    except (OSError, ValueError) as error:
        return Adoption(None, None, (), (str(error),))


def _adoption_checks(folder: model.Folder, planned: Planned, buffers) -> list[str]:
    _checked_path(folder.root, f"{planned.copy}/record.json", model.OUTPUT_FOLDER)
    if planned.first and not _empty_declaration(folder):
        return ["the declaration is no longer empty; review it again"]
    refusals = _checks(folder, planned.files, buffers)
    refusals += _retained_checks(folder, planned.retained, buffers)
    refusals += [
        f"{entry['destination']} cannot be written: no write permission"
        for entry in planned.files
        if not _writable(folder.root / entry["destination"])
    ]
    return refusals


def _adopt(folder: model.Folder, planned: Planned, buffers, write) -> Adoption:
    refusals = _adoption_checks(folder, planned, buffers)
    if refusals:
        return Adoption(None, None, (), tuple(refusals))
    identifier = uuid.uuid4().hex
    area = f"{ADOPTIONS_FOLDER}/{identifier}"
    files = []
    for entry in planned.files:
        held = (buffers or {}).get(entry["destination"])
        files.append(
            {
                "source": entry["source"],
                "destination": entry["destination"],
                "source_sha256": entry["source_sha256"],
                "before_sha256": entry["before_sha256"],
                "rewritten": entry["rewritten"],
                "editor_sha256": None if held is None else _sha256(held.text),
                "after_sha256": None,
                "outcome": "pending",
                "sentence": None,
                "recovery": None
                if entry["before_sha256"] is None
                else f"{RECOVERY}/{entry['destination']}",
                "restored": None,
            }
        )
    record = {
        "format": FORMAT,
        "id": identifier,
        "copy": planned.copy,
        "first": planned.first,
        **_job_fields(folder, planned.copy),
        "files": files,
        "retained": list(planned.retained),
        "conflicts": [],
        "state": "writing",
        "created_at": _now(),
        "updated_at": None,
    }
    digest = _write_record(folder, record, None)
    for entry in files:
        if entry["recovery"] is None:
            continue
        original = _text(folder.root / entry["destination"])
        kept = model.save_file(folder, f"{area}/{entry['recovery']}", original, None)
        if not kept.saved:
            record["state"] = "stopped"
            record["conflicts"].append(f"{entry['recovery']}: {kept.reason}")
            _write_record(folder, record, digest)
            sentence = f"the original of {entry['destination']} was not kept: {kept.reason}"
            return Adoption(identifier, record, (), (f"{sentence}; no file changed",))
    return _writes(folder, record, digest, files, write)


def _read_record(folder: model.Folder, identifier: str) -> tuple[dict, str]:
    """The adoption's record and its digest."""
    if re.fullmatch(r"[0-9a-f]{32}", identifier) is None:
        raise ValueError("the adoption identifier is invalid")
    path = f"{ADOPTIONS_FOLDER}/{identifier}/{RECORD}"
    _checked_path(folder.root, path, ".bellman-matsya")
    held = model.read_file(folder, path)
    record = json.loads(held.text)
    if record.get("id") != identifier:
        raise ValueError("the adoption record names a different adoption")
    return record, held.digest


def restore(folder: model.Folder, identifier: str, write=model.save_file) -> Adoption:
    """Restores the originals of the files the adoption `identifier` wrote,
    the last written first: each original from the adoption's recovery area
    through `write`, the guarded save by default, given the digest of the
    text the adoption wrote, so that an edit made since is not overwritten;
    a file the adoption created is removed where it holds the text written.
    The record is replaced after each file, its outcome `restored` or
    `failed`, and a failed restore is recorded as such."""
    try:
        with _adoption_lock(folder):
            return _restore(folder, identifier, write)
    except Timeout:
        return Adoption(identifier, None, (), ("another adoption is writing this declaration",))
    except (OSError, ValueError) as error:
        return Adoption(identifier, None, (), (str(error),))


def _restore(folder: model.Folder, identifier: str, write) -> Adoption:
    record, digest = _read_record(folder, identifier)
    area = folder.root / ADOPTIONS_FOLDER / identifier
    changed, refusals = [], []
    for entry in reversed(record["files"]):
        if entry["outcome"] != "written" or entry["restored"] == "restored":
            continue
        try:
            destination = _checked_path(folder.root, entry["destination"], model.FACTORY_FOLDER)
            failure = None
            if entry["recovery"] is None:
                if destination.is_file() and _sha256(_text(destination)) == entry["after_sha256"]:
                    destination.unlink()
                else:
                    failure = "the file changed after the adoption"
            else:
                backup = _checked_path(area, entry["recovery"], RECOVERY)
                saved = write(folder, entry["destination"], _text(backup), entry["after_sha256"])
                failure = None if saved.saved else saved.reason
        except (OSError, ValueError) as error:
            failure = str(error)
        if failure is None:
            entry["restored"] = "restored"
            changed.append(entry["destination"])
        else:
            entry["restored"] = "failed"
            refusals.append(f"{entry['destination']} was not restored: {failure}")
        digest = _write_record(folder, record, digest)
    record["state"] = "restore failed" if refusals else "restored"
    record["conflicts"] = refusals
    _write_record(folder, record, digest)
    return Adoption(identifier, record, tuple(changed), tuple(refusals))


def complete(
    folder: model.Folder, identifier: str, buffers: dict | None = None, write=model.save_file
) -> Adoption:
    """Completes the reviewed plan of the stopped adoption `identifier`: the
    checks of `_checks` for each file not yet written, each refusal leaving
    every file as it stands, then each of those files written as `adopt`
    writes them, with the record replaced after each write."""
    try:
        with _adoption_lock(folder):
            return _complete(folder, identifier, buffers, write)
    except Timeout:
        return Adoption(identifier, None, (), ("another adoption is writing this declaration",))
    except (OSError, ValueError) as error:
        return Adoption(identifier, None, (), (str(error),))


def _complete(folder: model.Folder, identifier: str, buffers, write) -> Adoption:
    record, digest = _read_record(folder, identifier)
    if record["state"] != "stopped":
        return Adoption(identifier, record, (), (f"adoption {identifier} is {record['state']}",))
    pending = [entry for entry in record["files"] if entry["outcome"] != "written"]
    written = [
        {"destination": entry["destination"], "sha256": entry["after_sha256"]}
        for entry in record["files"]
        if entry["outcome"] == "written"
    ]
    refusals = _checks(folder, pending, buffers)
    refusals += _retained_checks(folder, [*record["retained"], *written], buffers)
    if record.get("first"):
        declaration = folder.root / model.FACTORY_FOLDER
        allowed = {folder.root / entry["destination"] for entry in written}
        if any(
            path.is_symlink() or (not path.is_dir() and path not in allowed)
            for path in declaration.rglob("*")
        ):
            refusals.append("the declaration gained other files since the first adoption")
    if refusals:
        return Adoption(identifier, record, (), tuple(refusals))
    for entry in pending:
        if entry["recovery"] is None:
            continue
        path = f"{ADOPTIONS_FOLDER}/{identifier}/{entry['recovery']}"
        backup = _checked_path(folder.root, path, ".bellman-matsya")
        if entry["recovery"] != f"{RECOVERY}/{entry['destination']}":
            raise ValueError("the recovery file does not match the reviewed destination")
        if not backup.is_file():
            original = _text(folder.root / entry["destination"])
            kept = model.save_file(folder, path, original, None)
            if not kept.saved:
                refusal = f"{path} was not written: {kept.reason}"
                return Adoption(identifier, record, (), (refusal,))
    record["state"] = "writing"
    return _writes(folder, record, digest, pending, write)


def commit_offer(folder: model.Folder, record: dict) -> tuple[str, tuple[str, ...]] | None:
    """The commit offered after a recorded adoption, never made here
    (amendment 06 §2 item 23): its message and the destinations the
    adoption wrote that git reports changed, nothing else; None for an
    adoption that is not recorded as adopted, or where git reports none."""
    if record["state"] != "adopted":
        return None
    marks = model.git_marks(folder)
    paths = tuple(
        entry["destination"]
        for entry in record["files"]
        if entry["outcome"] == "written" and entry["destination"] in marks
    )
    if not paths:
        return None
    name = record["copy"].rsplit("/", 1)[-1]
    return f"Adopt the returned files of {name}", paths


# --- the variant import ---


def _addresses(document, names: set, path=()) -> list[tuple]:
    """The addresses, as tuples of keys and indices, of the strings of the
    document `document`, read by the package's `entry_value`, that are one
    of `names`."""
    found = []
    if isinstance(document, dict):
        for key, value in document.items():
            if key != "__yaml_tag__":
                found += _addresses(value, names, (*path, key))
    elif isinstance(document, list):
        for index, value in enumerate(document):
            found += _addresses(value, names, (*path, index))
    elif isinstance(document, str) and document in names:
        found.append(path)
    return found


def _written_address(path: tuple) -> str:
    """`stages.tenure.calibration.all[0]` for the address of those keys and
    that index."""
    written = ""
    for step in path:
        written += f"[{step}]" if isinstance(step, int) else ("." if written else "") + str(step)
    return written


def _variant_name(base: str, name: str) -> str:
    """The name, for the variant `name`, of the binding file `base`, a path
    or a source as a recipe writes it, with or without its extension:
    `calibration/durables.yml` as `calibration/durables_<name>.yml`, and
    `calibration/durables` as `calibration/durables_<name>`, names the
    service reads (decision SG3-9)."""
    path = Path(base)
    if path.suffix in (".yml", ".yaml"):
        return path.with_name(f"{path.stem}_{name}{path.suffix}").as_posix()
    return path.with_name(f"{path.name}_{name}").as_posix()


def import_variant(folder: model.Folder, copy: str, name: str, base_recipe: str = model.RECIPE
                   ) -> Imported:
    """Imports the saved copy at `copy` as the variant `name` of the recipe
    `base_recipe`, a recipe's name in `declaration/` (amendment 06 §2 item
    24; D-6). Each file of the copy is compared with the file at the same
    path in the folder: one that stands identical is shared; a changed
    calibration, settings or methods file that the baseline's recipe reads
    is copied under the variant's name (`_variant_name`); any other changed
    or new file refuses the import, with nothing written. The variant's
    recipe, trellis file and period files are written by
    `creation.create_variant`, the recipe retained where the copy holds
    none, and each entry of the variant's recipe that names a copied file is
    rewritten by the package's `replace_entry` to name its copy. The files
    the baseline's recipe reads are digested before and after, and an
    import after which one differs is refused with its name."""
    copied = model.open_folder(folder.root / copy)
    base_path = model.factory_path(base_recipe)
    base = recipe.Source("recipe", base_path)
    try:
        syntactic, paths = matsya_work.required_files(folder, base, {})
    except recipe._REFUSALS as error:
        refused = model.diagnostic_of(error, "read", str((folder.root / base_path).resolve()))
        return Imported((), (), (), (), False, {}, (model.sentence(refused),))
    baseline = {recipe.relative(folder, path): _sha256(_text(path)) for path in paths}
    written_as = {}
    entries = [
        entry
        for period in syntactic["periods"]
        for record in period["stages"].values()
        for kind in _BINDING_KINDS
        for entry in record["provenance"]["source_lists"].get(kind, [])
        if entry.get("path")
    ]
    registry = syntactic["provenance"].get("registry", {})
    entries += [entry for listed in registry.values() for entry in listed if entry.get("path")]
    for entry in entries:
        written_as.setdefault(recipe.relative(folder, entry["path"]), set()).add(entry["source"])
    structure = creation.variant_sources(folder.root, base_recipe)
    retained_recipe = model.factory_path(model.RECIPE) not in _copy_files(copied)
    copies, refusals = [], []
    for path in _copy_files(copied):
        text = _text(copied.root / path)
        standing = folder.root / path
        if standing.is_file() and _text(standing) == text:
            continue
        if path in written_as and path not in structure:
            copies.append((path, text))
            continue
        refusals.append(
            f"{copy}/{path} differs from {path}, and a variant import copies changed "
            "calibration, settings and methods files alone; review the copy on its own"
            if standing.is_file()
            else f"{copy}/{path} is no file of the model, and a variant import copies changed "
            "calibration, settings and methods files alone; review the copy on its own"
        )
    if refusals:
        return Imported((), (), (), (), retained_recipe, baseline, tuple(refusals))
    files = list(creation.create_variant(folder.root, name, base_recipe))
    variant = files[0]
    copied_files, rewritten = [], []
    text = model.read_file(folder, variant)
    updated = text.text
    for path, returned_text in copies:
        target = _variant_name(path, name)
        saved = model.save_file(folder, target, returned_text, None)
        if not saved.saved:
            return Imported(tuple(files), (), (), (), retained_recipe, baseline,
                            (f"{target} was not written: {saved.reason}",))
        files.append(target)
        copied_files.append({"source": f"{copy}/{path}", "base": path, "written": target})
        for old in sorted(written_as[path]):
            new = _variant_name(old, name)
            for address in _addresses(entry_value(updated), {old}):
                updated = replace_entry(updated, address, new)
                rewritten.append(
                    {"file": variant, "address": _written_address(address), "written": old,
                     "now": new}
                )
    saved = model.save_file(folder, variant, updated, text.digest)
    if not saved.saved:
        return Imported(tuple(files), tuple(copied_files), (), tuple(rewritten), retained_recipe,
                        baseline, (f"{variant} was not written: {saved.reason}",))
    after = {path: _sha256(_text(folder.root / path)) for path in baseline}
    changed = [path for path in baseline if after[path] != baseline[path]]
    if changed:
        return Imported(tuple(files), tuple(copied_files), (), tuple(rewritten), retained_recipe,
                        after, (f"the baseline changed: {_listed(changed)}",))
    shared = tuple(
        path for path in baseline if path not in structure and path not in dict(copies)
    )
    return Imported(tuple(files), tuple(copied_files), shared, tuple(rewritten), retained_recipe,
                    after, ())
