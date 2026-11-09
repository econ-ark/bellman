"""The Workbench's work with Matsya in one model folder (specification 0.6,
unit G2; the Matsya chat integration proposal of 21 October 2026, §§3 to 5
and 7): the prepared inputs of a job, the record of each request written
before its answer is awaited, the recovery of those records when the page
opens again, the check that a job belongs to the selected session on the
effective service, and the download of a job's products. Every request is
one run of the client by `matsya_client.run`, the Workbench's one route to
the service; every file is written by the guarded save `model.save_file`,
and following a job writes none. The module imports no Solara.

The files, by their paths in the model folder; the first three stand
beside the client's `.bellman-matsya/project.json`, and the tree hides them:

`.bellman-matsya/workbench/prepared/<id>.inputs.json`, the client's
prepared-inputs file of one job, written once by `prepare` in the format
`read_prepared_inputs` of the client's `bellman_matsya.client` defines:
`session`, `reviewed_through`, `target`, `starting_declaration`, the text
sent under each name the service reads, and `paths`, each name's file in
the model folder. `bellman-matsya job submit-prepared` sends it as it
stands and reads no file of the model.

`.bellman-matsya/workbench/prepared/<id>.json`, the Workbench's record of
the same preparation, written once by `prepare` after the inputs file: a
JSON object with
  `format`, 1;
  `id`, the record's identifier, 32 hexadecimal characters;
  `session` and `service`, the selected session's identifier and the digest
    that names its service (`matsya_client.service_identity`);
  `reviewed_through`, the number of the session's last entry the user
    reviewed;
  `target`, the job's target, `stage`, `period`, `trellis` or `recipe`;
  `source`, the selected recipe or trellis file, `{"kind", "path"}`;
  `description`, `{"path": "economics.md", "sha256"}` of the folder's
    description as it stood, recorded and not sent, else null;
  `choice`, the choice made for the unsaved buffers of the files read,
    `save`, `saved version` or `displayed text`, null where none differed;
  `files`, one object per file the source reads, in the order the package
    reads them: `path`, from the folder; `name`, the name the service reads
    it under; `sha256`, of the text taken; and `text`, `disk` or `buffer`,
    where that text was taken from;
  `rewritten`, each entry whose path was rewritten to a name the service
    reads, `{"path", "entry", "written", "sent"}`;
  `missing`, for each stage key, the parameters the stage declares that
    some period leaves unvalued by the rule the service applies, `{"stage",
    "names", "function", "file", "line", "sentence"}`, with the function of
    the folder's `code/` that writes them into a record's calibration,
    its file and the line of its definition, each null where no function
    does; a missing parameter is reported and refuses nothing;
  `inputs`, the path of the prepared-inputs file; and
  `inputs_sha256`, the SHA-256 of that file's bytes.

`.bellman-matsya/workbench/requests/<delivery>.json`, one request, written
before the client runs and replaced once it answers, before any wait: a
JSON object with `format`, 1; `kind`, `job`, `turn`, `entry` (a build's
first step, `add_entry`) or `reply` (`reply`, which adds `replies_to`, the
question's entry number, and `scheduled`, the continuation job the reply
started); `delivery`, the request's delivery identifier, 32 hexadecimal
characters, which a retry sends again; `session` and `service`, as above; `prepared`, the path of
the Workbench's prepared record a job was submitted from, else null;
`question`, a turn's question, else null; `accepted`, the identifier of the
job or the turn the service accepted, null until the client printed one;
`exit_code`, the client's exit status, null before it answered or where
none ran;
`warning`, the client's standard error as it printed it, the client
masking the Matsya token and the key; and `sent_at` and `answered_at`, UTC
times in ISO 8601, the second null before the client answered.

`bellman-matsya-output/job-<n>-iteration-<k>-revision-<r>-configuration-<c>/`,
one downloaded copy of a job's model folder, as the client's `job files`
writes it: `<n>` the job's number in its session, `<k>` the cycles it ran,
`<r>` the session's revision it read and `<c>` the first twelve characters
of its configuration ID, `none` for a value the service does not give. A
copy is written once and never into; the folder's `economics.md` is never
written.

The client's commands are those of `bellman-matsya` 0.13.0, as unit G1
extends it (decision SG2-3): `job submit-prepared <file> --delivery-id
<id>` (decision SG5-16), `ask <session> --no-wait --delivery-id <id> --
<question>`, `turn status <session> <turn>`, `job status <job>`, `job files
<job> <folder>`, `session select <session> <job>`, `session show <session>`
and `session add <session> <file> --replies-to <n> --delivery-id <id>`
(decision SG5-19), each with `--json`.
"""

from __future__ import annotations

import ast
import datetime
import difflib
import hashlib
import json
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import NamedTuple

from bellman.factory.recipe import declared_parameters
from bellman.trellis import entry_value, replace_entry
from bellman_workbench import matsya_client, model, recipe, trellis

# the folders of the files this module writes, by their paths in the
# model folder
WORK_FOLDER = ".bellman-matsya/workbench"
PREPARED_FOLDER = f"{WORK_FOLDER}/prepared"
REQUESTS_FOLDER = f"{WORK_FOLDER}/requests"
OUTPUT_FOLDER = model.OUTPUT_FOLDER
FORMAT = 1

# the three choices for an unsaved buffer of a file the source reads (the
# proposal's §4): write it to disk and send it, send the text on disk, or
# send the buffer and leave the disk
SAVE = "save"
SAVED_VERSION = "saved version"
DISPLAYED_TEXT = "displayed text"
CHOICES = (SAVE, SAVED_VERSION, DISPLAYED_TEXT)

# the names under which the service reads a file of `declaration/`, as the
# client's `declaration_name` and the service's `allowed_declaration_name`
# admit them: a stage file `stages/<key>/<key>.bl` as `<key>.bl`; a period
# file, a stage's methods file and a calibration or settings file under its
# path; the selected recipe as `spec.yml` and its trellis file as
# `trellis.yml`
_KEY = r"[a-zA-Z0-9][a-zA-Z0-9_-]*"
_NAME = r"[a-z0-9][a-z0-9_-]*"
_STAGE = re.compile(rf"stages/({_KEY})/\1\.bl")
_KEPT = re.compile(
    rf"period(?:\.{_NAME})?\.yml|stages/{_KEY}/methods\.yml|(?:calibration|settings)/{_NAME}\.yml"
)
RECIPE_NAME = "spec.yml"
TRELLIS_NAME = "trellis.yml"

# the one sentence that makes the job unavailable where the source selects
# an addition, which the service does not read yet (decision S7-W5 of
# specification 0.7); the service's change is the issue
# `matsya-build-declaration-takes-a-bl-addition`
ADDITION_UNSENT = (
    "the service does not read a methods addition yet, so Build declaration cannot send {}"
)

# the folder of a model's programs, among them the code that writes values
# into the syntactic trellis (the page Model directory layout)
CODE_FOLDER = "code"


class Buffer(NamedTuple):
    """An unsaved buffer of a file: `text`, and `digest`, the SHA-256 of
    the file's text as the buffer last read or wrote it, which the guarded
    save compares."""

    text: str
    digest: str


class Session(NamedTuple):
    """The selected session: `id`, its identifier on the service, and
    `service`, the digest that names the service holding it."""

    id: str
    service: str | None


class Prepared(NamedTuple):
    """What `prepare` answered: `path`, the prepared record's path from the
    folder, None where nothing was written; `record`, its contents;
    `refusals`, one sentence per reason nothing was written; and
    `differences`, the unified difference of each unsaved buffer of a file
    the source reads from the text on disk, by the file's path."""

    path: str | None
    record: dict | None
    refusals: tuple = ()
    differences: dict = {}
    texts: dict | None = None


class Work(NamedTuple):
    """One request as its record stands: `path`, the record's path from the
    folder, and `record`, its contents."""

    path: str
    record: dict


class Recovered(NamedTuple):
    """One request recovered by `recover`: `record`; `answer`, the
    service's answer for its job or turn read now, None where none was
    accepted or the service did not answer; `state`, that answer's state;
    and `retry`, whether a retry is offered, which `retry` carries out."""

    record: dict
    answer: dict | None
    state: str | None
    retry: bool


class Membership(NamedTuple):
    """What `membership` found: `job`, the service's answer for the job,
    None where it was not asked or did not answer; and `refusal`, the
    sentence that says why the job is not acted on, None where it belongs
    to the selected session on the effective service."""

    job: dict | None
    refusal: str | None


class Downloaded(NamedTuple):
    """What `download` answered: `path`, the copy's path from the folder,
    None where none stands; `written`, whether this call wrote it; and
    `refusal`, the sentence that says why nothing was written, None where
    the copy stands."""

    path: str | None
    written: bool
    refusal: str | None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="microseconds")


def _json(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, indent=1) + "\n"


def _joined(names: list[str]) -> str:
    """`Y`, `Y and y_R`, `a, b and c`."""
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


# --- the prepared inputs ---


def required_files(folder: model.Folder, source: recipe.Source, texts: dict):
    """The syntactic trellis of `source`, read through the unsaved texts
    `texts`, and the files it reads, each once and resolved: those the
    page's watcher compares (`trellis.files_read`) and the files the
    recipe's `registry` block names, which the service reads too."""
    syntactic = recipe.read_source(folder, source, texts)
    paths = trellis.files_read(folder, source, syntactic, texts)
    for entries in syntactic["provenance"].get("registry", {}).values():
        paths += [Path(entry["path"]).resolve() for entry in entries if entry.get("path")]
    return syntactic, list(dict.fromkeys(paths))


def _within(relpath: str) -> str | None:
    """The path within `declaration/` of the file at `relpath`, its path
    from the folder; None for a file outside that folder."""
    parts = Path(relpath).parts
    if len(parts) < 2 or parts[0] != model.FACTORY_FOLDER:
        return None
    return Path(*parts[1:]).as_posix()


def _service_name(within: str, recipe_path: str | None, trellis_path: str | None) -> str | None:
    """The name under which the service reads the file at `within`, its
    path within `declaration/`, where the selected recipe stands at
    `recipe_path` and its trellis file at `trellis_path`; None for a file
    the service reads under no name."""
    if within == recipe_path:
        return RECIPE_NAME
    if within == trellis_path:
        return TRELLIS_NAME
    stage = _STAGE.fullmatch(within)
    if stage:
        return f"{stage.group(1)}.bl"
    return within if _KEPT.fullmatch(within) else None


def _ambiguous(syntactic: dict) -> list[str]:
    """One sentence for each source the trellis's records or the recipe's
    `registry` block name without the extension where both `<name>.yml`
    and `<name>.yaml` stand, of which the package reads the first
    (`_registry_file` of `bellman.factory.recipe`)."""
    entries = [
        entry
        for period in syntactic["periods"]
        for record in period["stages"].values()
        for kind in recipe.KINDS
        for entry in record["provenance"]["source_lists"].get(kind, [])
    ]
    registry = syntactic["provenance"].get("registry", {})
    entries += [entry for listed in registry.values() for entry in listed]
    sentences = []
    for entry in entries:
        written, read = entry.get("source"), entry.get("path")
        if not written or not read or Path(written).suffix in (".yml", ".yaml"):
            continue
        if Path(read).suffix == ".yml" and Path(read).with_suffix(".yaml").is_file():
            sentence = (
                f"{written} names both {written}.yml and {written}.yaml; write the name with "
                "its extension"
            )
            if sentence not in sentences:
                sentences.append(sentence)
    return sentences


def _names_stages(node) -> bool:
    """Whether `node` is `<expression>["stages"]`."""
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "stages"
    )


def _writers(folder: model.Folder) -> list[tuple]:
    """The functions of the Python files under the folder's `code/` that
    write a value into a record's calibration mapping,
    `<record>["calibration"]["<name>"] =`, each as `(file, function, line,
    names, keys)`: the file from the folder, the function's name and the
    line of its definition, the names it writes, and the stage keys it
    reads from a period's `stages` mapping, by `.get("<key>")` or
    `["<key>"]`, empty where it names none.
    The files are read, never run; a file that does not read as Python is
    passed over, and no function of it is named."""
    found = []
    for path in sorted((folder.root / CODE_FOLDER).rglob("*.py")):
        if any(part.startswith(".") for part in path.relative_to(folder.root).parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
            continue
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef):
                continue
            names, keys = [], []
            for node in ast.walk(function):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Subscript)
                            and isinstance(target.slice, ast.Constant)
                            and isinstance(target.slice.value, str)
                            and isinstance(target.value, ast.Subscript)
                            and isinstance(target.value.slice, ast.Constant)
                            and target.value.slice.value == "calibration"
                        ):
                            names.append(target.slice.value)
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get"
                    and _names_stages(node.func.value)
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                ):
                    keys.append(node.args[0].value)
                if (
                    isinstance(node, ast.Subscript)
                    and _names_stages(node.value)
                    and isinstance(node.slice, ast.Constant)
                ):
                    keys.append(node.slice.value)
            if names:
                file = path.relative_to(folder.root).as_posix()
                found.append((file, function.name, function.lineno, names, keys))
    return found


def _missing(folder: model.Folder, syntactic: dict) -> list[dict]:
    """For each stage key of the trellis, in the order of its first
    occurrence, the parameters its stage declares that some period leaves
    unvalued, by the rule the service applies (`_unvalued_by_period` of its
    `meaning.py`): a parameter of a period is valued where a stage of that
    period that declares it (`declared_parameters`) holds it in its
    calibration. Each comes with the function of the folder's code that
    writes them all for that key, where one does (`_writers`). A stage text
    the parser refuses raises that refusal."""
    declared, unvalued = {}, {}
    for period in syntactic["periods"]:
        by_stage = {}
        for key, record in period["stages"].items():
            text = record["stage"]["text"]
            if text not in declared:
                declared[text] = declared_parameters(text, record["stage"]["origin"])
            by_stage[key] = declared[text]
        supplied = {
            name
            for key, record in period["stages"].items()
            for name in by_stage[key]
            if name in record["calibration"]
        }
        for key, names in by_stage.items():
            held = unvalued.setdefault(key, [])
            held += [name for name in names if name not in supplied and name not in held]
    writers = _writers(folder)
    missing = []
    for key, names in unvalued.items():
        if not names:
            continue
        writer = next(
            (
                (file, function, line)
                for file, function, line, written, keys in writers
                if set(names) <= set(written) and (not keys or key in keys)
            ),
            None,
        )
        if writer is None:
            file = function = line = None
            sentence = (
                f"{_joined(names)} of {key} are valued by no file the recipe lists; supply "
                "their values"
            )
        else:
            file, function, line = writer
            sentence = (
                f"{_joined(names)} of {key} are written by {function} ({file}, line {line}), "
                "which a submission of the declaration omits; supply their values"
            )
        missing.append(
            {"stage": key, "names": names, "function": function, "file": file, "line": line,
             "sentence": sentence}
        )
    return missing


def _history_key(entries: list[dict]) -> list[list]:
    return [
        [entry["number"], entry["kind"], entry.get("replies_to"), _sha256(entry["text"])]
        for entry in entries
    ]


def reviewed_entries(folder: model.Folder, session: Session) -> list[dict]:
    held = read_session(session, folder)
    entries = held.get("entries") if held is not None else None
    if not isinstance(entries, list) or any(
        not isinstance(entry, dict)
        or type(entry.get("number")) is not int
        or not isinstance(entry.get("kind"), str)
        or not isinstance(entry.get("text"), str)
        for entry in entries
    ):
        raise ValueError("Matsya's session history is unavailable. Check the connection and try again.")
    if [entry["number"] for entry in entries] != sorted({entry["number"] for entry in entries}):
        raise ValueError("Matsya's session entries are out of order. Review the session again.")
    return entries


def prepare(
    folder: model.Folder,
    source: recipe.Source | None,
    target: str,
    session: Session,
    reviewed_through: int,
    buffers: dict | None = None,
    choice: str | None = None,
    *,
    history: list[dict] | None = None,
    prompt: str | None = None,
) -> Prepared:
    """The prepared inputs of a job from `source` at `target` in `session`,
    whose entries the user reviewed through entry `reviewed_through`,
    written once as the client's prepared-inputs file and the Workbench's
    record beside it (the module's docstring gives both formats), which
    `submit` sends without reading a file of the model again. `buffers`
    holds the editor's unsaved buffers, a `Buffer` by each file's path from
    the folder; for those that differ from the file and are read by the
    source, `choice` is one of CHOICES:
    `save` writes each through the guarded save and sends it, `saved
    version` sends the text on disk and `displayed text` sends the buffer
    and leaves the disk. Nothing is written, and the answer says why, for
    such a buffer without a choice (with its difference from disk), a
    buffer the guarded save refuses, a source the package refuses to read,
    a source named without its extension where both its `.yml` and its
    `.yaml` files stand, a file the source reads outside the folder's
    `declaration/`, and a file the service reads under no name. A source
    whose files hold an addition (`model.is_addition_file`) prepares
    nothing and answers one sentence that names them (`ADDITION_UNSENT`),
    whatever the buffers hold, since the service reads no addition yet."""
    files, texts, rewritten, missing = [], {}, [], []
    differences = {}
    if source is not None:
        rule = model.FACTORY_FOLDER
        displayed, differences = {}, {}
        for path, held in (buffers or {}).items():
            on_disk = model.read_file(folder, path).text
            if held.text != on_disk:
                displayed[str((folder.root / path).resolve())] = held.text
                differences[path] = "".join(
                    difflib.unified_diff(
                        on_disk.splitlines(keepends=True),
                        held.text.splitlines(keepends=True),
                        fromfile=f"{path} (disk)",
                        tofile=f"{path} (editor)",
                    )
                )
        try:
            syntactic, paths = required_files(folder, source, displayed)
            missing = _missing(folder, syntactic)
        except recipe._REFUSALS as error:
            subject = str((folder.root / source.path).resolve())
            return Prepared(None, None, (model.sentence(model.diagnostic_of(error, "read", subject)),))
        additions = [recipe.relative(folder, path) for path in paths if model.is_addition_file(path)]
        if additions:
            return Prepared(None, None, (ADDITION_UNSENT.format(", ".join(additions)),))
        named = {recipe.relative(folder, path) for path in paths}
        differences = {path: text for path, text in differences.items() if path in named}
        if differences and choice not in CHOICES:
            sentences = tuple(
                f"{path} has unsaved changes; save it, send the saved version or send the "
                "displayed text"
                for path in differences
            )
            return Prepared(None, None, sentences, differences)
        taken = displayed if differences and choice in (SAVE, DISPLAYED_TEXT) else {}
        if differences and choice == SAVED_VERSION:
            try:
                syntactic, paths = required_files(folder, source, {})
                missing = _missing(folder, syntactic)
            except recipe._REFUSALS as error:
                subject = str((folder.root / source.path).resolve())
                refused = model.diagnostic_of(error, "read", subject)
                return Prepared(None, None, (model.sentence(refused),))
        recipe_path = _within(source.path) if source.kind == "recipe" else None
        trellis_path = _within(recipe.relative(folder, syntactic["provenance"]["trellis"]["path"]))
        captured = {}
        refusals = _ambiguous(syntactic)
        for path in paths:
            relpath = recipe.relative(folder, path)
            within = _within(relpath)
            if within is None:
                refusals.append(
                    f"{relpath} lies outside the folder's {rule}/, and the service reads every file "
                    "from that folder"
                )
                continue
            name = _service_name(within, recipe_path, trellis_path)
            if name is None:
                refusals.append(
                    f"the service reads no file named {within}, so {relpath} cannot be sent"
                )
                continue
            held = taken.get(str(path))
            text = held if held is not None else model.read_file(folder, relpath).text
            captured[str(path)] = text
            files.append({"path": relpath, "name": name, "sha256": _sha256(text),
                          "text": "disk" if held is None else "buffer"})
            if name == RECIPE_NAME:
                written = entry_value(text, "trellis")
                if written != TRELLIS_NAME:
                    text = replace_entry(text, "trellis", TRELLIS_NAME)
                    rewritten.append({"path": relpath, "entry": "trellis", "written": written,
                                      "sent": TRELLIS_NAME})
            texts[name] = text
            files[-1]["sent_sha256"] = _sha256(text)
        if refusals:
            return Prepared(None, None, tuple(refusals), differences)
        try:
            _, verified = required_files(folder, source, captured)
        except recipe._REFUSALS as error:
            return Prepared(None, None, (str(error),), differences)
        if set(verified) != set(paths):
            return Prepared(None, None, ("The declaration changed during preparation. Review it again.",))
        if choice == SAVE:
            for path in differences:
                saved = model.save_file(folder, path, buffers[path].text, buffers[path].digest)
                if not saved.saved:
                    refusal = f"{path} was not saved: {saved.reason}"
                    return Prepared(None, None, (refusal,), differences)
    if history is not None:
        prompt = (prompt or "").strip()
        if not prompt:
            return Prepared(None, None, ("Write a description or build request first.",))
    economics = folder.root / "economics.md"
    description = None
    if economics.is_file() and not economics.is_symlink():
        contents = economics.read_bytes()
        description = {"path": "economics.md", "sha256": hashlib.sha256(contents).hexdigest()}
        if history is not None:
            local_text = contents.decode("utf-8").strip()
            description_text = f"Current model description (economics.md):\n{local_text}"
            separator = "\n\nBuild request:\n"
            prior = next(
                (entry["text"].partition(separator)[0] for entry in reversed(history)
                 if entry["kind"] == "user"
                 and entry["text"].startswith("Current model description (economics.md):\n")),
                None,
            )
            if local_text and prior != description_text and (
                prior is not None or not any(
                    entry["kind"] in ("user", "paper") and entry["text"].strip() == local_text
                    for entry in history
                )
            ):
                prompt = f"{description_text}{separator}{prompt}"
    if history is not None:
        reviewed_through = (history[-1]["number"] if history else 0) + 1
    identifier = uuid.uuid4().hex
    inputs = f"{PREPARED_FOLDER}/{identifier}.inputs.json"
    client_inputs = {
        "session": session.id,
        "reviewed_through": reviewed_through,
        "target": target,
    }
    if texts:
        client_inputs["starting_declaration"] = texts
        client_inputs["paths"] = {entry["name"]: entry["path"] for entry in files}
    saved = model.save_file(folder, inputs, _json(client_inputs), None)
    if not saved.saved:
        return Prepared(None, None, (f"{inputs} was not written: {saved.reason}",), differences)
    record = {
        "format": FORMAT,
        "id": identifier,
        "session": session.id,
        "service": session.service,
        "reviewed_through": reviewed_through,
        "target": target,
        "source": {"kind": source.kind, "path": source.path} if source else None,
        "description": description,
        "choice": choice if differences else None,
        "files": files,
        "rewritten": rewritten,
        "missing": missing,
        "inputs": inputs,
        "inputs_sha256": saved.digest,
    }
    if history is not None:
        association = project(folder)
        if association is None or association["session"] != session.id:
            return Prepared(None, None, ("The Matsya session changed during preparation.",))
        record.update(
            history=_history_key(history), prompt=prompt, entry_delivery=uuid.uuid4().hex,
            job_delivery=uuid.uuid4().hex, server=association["server"],
        )
    path = f"{PREPARED_FOLDER}/{identifier}.json"
    saved = model.save_file(folder, path, _json(record), None)
    if not saved.saved:
        return Prepared(None, None, (f"{path} was not written: {saved.reason}",), differences)
    return Prepared(path, record, (), differences, texts)


# --- the requests and their recovery ---


class ReviewRequired(ValueError):
    """The reviewed inputs or session have changed."""


def _captured_inputs(folder: model.Folder, prepared: dict) -> bytes:
    data = (folder.root / prepared["inputs"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != prepared["inputs_sha256"]:
        raise ReviewRequired("The prepared inputs changed. Prepare and review the build again.")
    return data


def _write(folder: model.Folder, path: str, record: dict, expected: str | None) -> str:
    """Writes the request's record by the guarded save, `expected` the
    digest of the record it replaces, None for a new one; answers the
    digest written. A refused write raises OSError, since the request must
    not be sent, or awaited, without its record."""
    saved = model.save_file(folder, path, _json(record), expected)
    if not saved.saved:
        raise OSError(f"{path} was not written: {saved.reason}")
    return saved.digest


def _send(folder: model.Folder, record: dict, path: str, digest: str | None) -> Work:
    """Runs the client for the request, its record standing on disk with
    `digest`, and replaces the record with the identifier the client
    printed, its exit status and its warning, whatever that status."""
    if record["service"] != matsya_client.service_identity():
        raise ValueError("The Matsya connection changed before the request was sent.")
    if record["kind"] == "job":
        prepared = json.loads((folder.root / record["prepared"]).read_text(encoding="utf-8"))
        data = _captured_inputs(folder, prepared)
        if record.get("inputs_sha256", prepared["inputs_sha256"]) != prepared["inputs_sha256"]:
            raise ReviewRequired("The prepared inputs changed. Prepare and review the build again.")
        with tempfile.TemporaryDirectory() as holder:
            snapshot = Path(holder) / "prepared-inputs.json"
            snapshot.write_bytes(data)
            ran = matsya_client.run(
                ["job", "submit-prepared", str(snapshot), "--delivery-id", record["delivery"], "--json"]
            )
    else:
        ran = matsya_client.run(
            ["ask", record["session"], "--no-wait", "--delivery-id", record["delivery"],
             "--json", "--", record["question"]]
        )
    # `job submit-prepared` answers the job under `job`, `ask --no-wait`
    # the turn itself
    work = ran.answer.get("job") if record["kind"] == "job" and ran.answer else ran.answer
    accepted = work.get("id") if isinstance(work, dict) else None
    answered = {
        **record,
        "accepted": accepted if isinstance(accepted, str) and accepted else record["accepted"],
        "exit_code": ran.code,
        "warning": ran.warning,
        "answered_at": _now(),
    }
    _write(folder, path, answered, digest)
    return Work(path, answered)


def _request(
    folder: model.Folder, session: Session, kind: str, *, delivery: str | None = None, **fields
) -> Work:
    """A new request of `kind`, its record written before the client runs."""
    delivery = delivery or uuid.uuid4().hex
    record = {
        "format": FORMAT,
        "kind": kind,
        "delivery": delivery,
        "session": session.id,
        "service": session.service,
        "prepared": None,
        "question": None,
        **fields,
        "accepted": None,
        "exit_code": None,
        "warning": "",
        "sent_at": _now(),
        "answered_at": None,
    }
    path = f"{REQUESTS_FOLDER}/{delivery}.json"
    digest = _write(folder, path, record, None)
    return _send(folder, record, path, digest)


def submit(
    folder: model.Folder, prepared: str, session: Session, reviewed: dict | None = None
) -> Work:
    """Send the reviewed inputs and, for a build from the panel, append its
    reviewed text with a separate delivery identifier."""
    document = model.read_file(folder, prepared)
    held = json.loads(document.text)
    if (held["session"], held["service"]) != tuple(session):
        raise ValueError(f"{prepared} was prepared for session {held['session']}, not this connection.")
    if session.service != matsya_client.service_identity():
        raise ReviewRequired("The Matsya connection changed. Prepare the build again.")
    if reviewed is not None and held != reviewed:
        raise ReviewRequired("The build review changed on disk. Prepare the build again.")
    _captured_inputs(folder, held)
    if "history" not in held:
        return _request(folder, session, "job", prepared=prepared, inputs_sha256=held["inputs_sha256"])
    association = project(folder)
    if association != {"session": session.id, "server": held["server"]} or not session_current(
        folder, session
    ):
        raise ReviewRequired("The Matsya connection changed. Prepare the build again.")

    job_delivery = held["job_delivery"]
    job_path = f"{REQUESTS_FOLDER}/{job_delivery}.json"
    if (folder.root / job_path).is_file():
        record = json.loads(model.read_file(folder, job_path).text)
        if (record["kind"], record["session"], record["service"], record["prepared"],
            record["delivery"]) != ("job", *session, prepared, job_delivery):
            raise ReviewRequired("The job request record changed. Prepare the build again.")
        return Work(job_path, record) if record["accepted"] else retry(folder, record)

    before = held["history"]
    number = held["reviewed_through"]
    expected = [*before, [number, "user", None, _sha256(held["prompt"])]]
    entry_delivery = held["entry_delivery"]
    entry_path = folder.root / REQUESTS_FOLDER / f"{entry_delivery}.json"
    current = _history_key(reviewed_entries(folder, session))
    if current != before and not (entry_path.is_file() and current == expected):
        raise ReviewRequired("The session changed since preparation. Review a new build.")

    entry = add_entry(
        folder, session, held["prompt"], delivery=entry_delivery, prepared=prepared,
        prepared_digest=document.digest
    )
    if entry.record["accepted"] is None:
        return entry
    if entry.record["accepted"] != str(number) or _history_key(
        reviewed_entries(folder, session)
    ) != expected:
        raise ReviewRequired("The session changed before submission. Review a new build.")
    return _request(
        folder, session, "job", delivery=job_delivery, prepared=prepared,
        inputs_sha256=held["inputs_sha256"],
    )


def add_entry(
    folder: model.Folder, session: Session, text: str, *,
    delivery: str | None = None, prepared: str | None = None,
    prepared_digest: str | None = None,
) -> Work:
    """Append the user's entry. Replay a previously recorded delivery with
    the same text and destination if the acknowledgement was lost."""
    delivery = delivery or uuid.uuid4().hex
    path = f"{REQUESTS_FOLDER}/{delivery}.json"
    if not (folder.root / path).is_file():
        record = {
            "format": FORMAT,
            "kind": "entry",
            "delivery": delivery,
            "session": session.id,
            "service": session.service,
            "prepared": prepared,
            "prepared_digest": prepared_digest,
            "question": text,
            "accepted": None,
            "exit_code": None,
            "warning": "",
            "sent_at": _now(),
            "answered_at": None,
        }
        digest = _write(folder, path, record, None)
    else:
        saved = model.read_file(folder, path)
        record = json.loads(saved.text)
        if (record["kind"], record["session"], record["service"], record["question"],
            record["delivery"], record.get("prepared"), record.get("prepared_digest")) != (
                "entry", *session, text, delivery, prepared, prepared_digest
            ):
            raise ReviewRequired("The saved build request changed. Prepare the build again.")
        if record["accepted"] is not None:
            return Work(path, record)
        digest = saved.digest
    if session.service != matsya_client.service_identity():
        raise ValueError("The Matsya connection changed before the request was sent.")
    with tempfile.TemporaryDirectory() as holder:
        held = Path(holder) / "entry.txt"
        held.write_bytes(text.encode("utf-8"))
        ran = matsya_client.run(
            ["session", "add", session.id, str(held), "--kind", "user",
             "--delivery-id", delivery, "--json"]
        )
    entry = ran.answer.get("entry") if ran.answer else None
    number = entry.get("number") if isinstance(entry, dict) else None
    answered = {
        **record,
        "accepted": str(number) if isinstance(number, int) else None,
        "exit_code": ran.code,
        "warning": ran.warning,
        "answered_at": _now(),
    }
    _write(folder, path, answered, digest)
    return Work(path, answered)


def pending_builds(folder: model.Folder, session: Session, entries: list[dict]):
    """Read reviews with an unfinished delivery. Never send a request on reopen."""
    requests = {record["delivery"]: record for record in records(folder, session)}
    for entry in requests.values():
        prepared = entry.get("prepared")
        if not prepared or entry["kind"] != "entry":
            continue
        try:
            document = model.read_file(folder, prepared)
            if document.digest != entry.get("prepared_digest"):
                continue
            held = json.loads(document.text)
            if (
                held["entry_delivery"] != entry["delivery"]
                or held["prompt"] != entry["question"]
                or (held["session"], held["service"]) != tuple(session)
                or held["server"] != project(folder)["server"]
            ):
                continue
            job = requests.get(held["job_delivery"])
            if job is not None and job["accepted"] is not None:
                continue
            files = json.loads(_captured_inputs(folder, held)).get("starting_declaration", {})
            history = entries[:len(held["history"])]
            # Display earlier text only when it matches the original review.
            if _history_key(history) != held["history"]:
                history = []
        except (KeyError, OSError, TypeError, ValueError):
            continue
        yield Prepared(prepared, held, texts=files), history


def start_turn(folder: model.Folder, session: Session, question: str) -> Work:
    """Starts a turn of `question` in `session` without waiting for its
    answer, by the client's start of a turn with a delivery identifier."""
    return _request(folder, session, "turn", question=question)


def record_started_job(folder: model.Folder, turn: Work, job_id: str) -> None:
    """Record the job on its accepted turn without creating a second request."""
    try:
        saved = model.read_file(folder, turn.path)
        current = json.loads(saved.text)
    except (OSError, ValueError):
        return
    if current == turn.record:
        model.save_file(folder, turn.path, _json({**current, "started_job": job_id}), saved.digest)


def follow(record: dict) -> dict | None:
    """The service's answer for the job or the turn the request `record`
    names, read now; None where none was accepted, where the record's
    service is not the one the client's settings name now, or where the
    service did not answer. Nothing is written."""
    if record.get("accepted") is None or record["service"] != matsya_client.service_identity():
        return None
    if record["kind"] == "job":
        ran = matsya_client.run(["job", "status", record["accepted"], "--json"])
    else:
        ran = matsya_client.run(
            ["turn", "status", record["session"], record["accepted"], "--json"]
        )
    return ran.answer if ran.code == 0 else None


def records(folder: model.Folder, session: Session) -> list[dict]:
    """The request records of the folder for `session` on its service, in
    the order they were sent."""
    folder_path = folder.root / REQUESTS_FOLDER
    found = []
    for path in sorted(folder_path.glob("*.json")) if folder_path.is_dir() else []:
        record = json.loads(path.read_text(encoding="utf-8"))
        if (record.get("session"), record.get("service")) == tuple(session):
            found.append(record)
    return sorted(found, key=lambda record: (record["sent_at"], record["delivery"]))


def recover(folder: model.Folder, session: Session) -> list[Recovered]:
    """The folder's requests for `session`, each accepted one with its job
    or turn read now (`follow`), before any retry is offered: a retry is
    offered only for a turn or a job whose answer was lost, which `retry`
    sends again with its delivery identifier, so that the service answers
    the turn or the job it already holds (decision SG5-16); none is offered
    where the session's service is not the one the client's settings name
    now, whose records are listed unread."""
    current = session.service == matsya_client.service_identity()
    recovered = []
    for record in records(folder, session):
        answer = follow(record)
        state = answer.get("state") if answer is not None else None
        retry = current and record["accepted"] is None and record["kind"] in ("turn", "job")
        recovered.append(Recovered(record, answer, state, retry))
    return recovered


def retry(folder: model.Folder, record: dict) -> Work:
    """Sends the turn or the job of `record`, whose answer was lost, again
    with its delivery identifier, which the service answers with the work
    it already holds, and replaces its record with the answer. Any other
    request is refused with a ValueError, since sending it again could start
    the work twice."""
    if record["kind"] not in ("turn", "job") or record["accepted"] is not None:
        raise ValueError(f"request {record['delivery']} is no turn whose answer was lost")
    if record["service"] != matsya_client.service_identity():
        raise ValueError("The Matsya connection changed before the request was retried.")
    path = f"{REQUESTS_FOLDER}/{record['delivery']}.json"
    digest = model.read_file(folder, path).digest
    return _send(folder, record, path, digest)


# --- the folder's project session ---

# the client's project file, which `bellman-matsya project init` writes
PROJECT_FILE = ".bellman-matsya/project.json"


def project(folder: model.Folder) -> dict | None:
    """The folder's project as the client's `project.json` records it,
    `{"session", "server"}`, the session's identifier and the service's
    address; None where the folder holds no such file or the file names no
    session and no address, the folder then not connected to Matsya."""
    path = folder.root / PROJECT_FILE
    if not path.is_file() or path.is_symlink():
        return None
    try:
        held = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(held, dict):
        return None
    session, server = held.get("session"), held.get("server")
    if not (isinstance(session, str) and session and isinstance(server, str) and server):
        return None
    return {"session": session, "server": server.rstrip("/")}


def connected_session(folder: model.Folder) -> Session | None:
    """The folder's project session on the service the client's settings
    name now (`project`; `matsya_client.service_identity`), the session
    the column discusses jobs in; None where the folder is not connected."""
    held = project(folder)
    return Session(held["session"], matsya_client.service_identity()) if held else None


def session_current(folder: model.Folder, session: Session) -> bool:
    """Whether the saved project and current client still name this session."""
    held = project(folder)
    url = matsya_client.service_url()
    identity = matsya_client.service_identity()
    return (
        held is not None
        and held["session"] == session.id
        and identity is not None
        and identity == session.service
        and (url is None or held["server"] == url)
    )


def read_session(session: Session, folder: model.Folder | None = None) -> dict | None:
    """Read the current service's session without writing local history."""
    if session.service is None or session.service != matsya_client.service_identity():
        return None
    if folder is not None and not session_current(folder, session):
        return None
    if folder is not None and matsya_client.service_url() is None:
        # The client checks its built-in URL against the project's saved URL.
        found = matsya_client.run(["project", "status", "--json"], cwd=folder.root)
        held = found.answer.get("session") if found.answer else None
    else:
        found = matsya_client.run(["session", "show", session.id, "--json"])
        held = found.answer
    if found.code != 0 or not isinstance(held, dict) or held.get("id") != session.id:
        return None
    if folder is not None and not session_current(folder, session):
        return None
    return held


def read_turn(session: Session, turn_id: str) -> dict | None:
    """Read an accepted turn that belongs to this project session."""
    answer = follow({
        "kind": "turn",
        "accepted": turn_id,
        "session": session.id,
        "service": session.service,
    })
    if answer is not None and answer.get("id") == turn_id and answer.get("session") == session.id:
        return answer
    return None


def connect(folder: model.Folder) -> tuple[dict | None, str | None]:
    """`Connect this folder to Matsya` (amendment 06 §2 items 3 and 14):
    the client's `project init` on the folder, which creates the folder's
    project session, named after the folder, sends the folder's name and
    its `economics.md`, and writes `.bellman-matsya/project.json`, its
    README and, where none stands, `AGENTS.md` (§4); answers the project as
    `project` reads it then, or None with the client's sentence. The
    earlier conversation of unit M stays where `matsya_client` keeps it
    (D-1)."""
    ran = matsya_client.run(["project", "init", str(folder.root), "--json"])
    held = project(folder)
    if ran.code != 0 or held is None:
        return None, ran.warning or matsya_client.NO_ANSWER
    return held, None


# the collections of the service's index (the client's `search`)
COLLECTIONS = ("repository", "literature", "articles", "hark", "buffer_stock")


def search(query: str, collection: str | None = None) -> tuple[tuple[dict, ...], str | None]:
    """`Search sources` (amendment 06 §2 item 8): the passages of the
    service's index that match `query`, in `collection`, or in every
    collection the Matsya token may read where it is None, by the client's
    `search`, which starts no turn and no job and writes nothing; answers
    the passages as the service gives them, with None, or no passage and
    the client's sentence."""
    arguments = ["search", "--json"]
    if collection is not None:
        arguments += ["--collections", collection]
    ran = matsya_client.run([*arguments, "--", query])
    passages = ran.answer.get("passages") if ran.code == 0 and ran.answer else None
    if not isinstance(passages, list):
        return (), ran.warning or matsya_client.NO_ANSWER
    return tuple(passage for passage in passages if isinstance(passage, dict)), None


# --- membership ---

# the words of the client's refusal of a request whose object the service
# does not hold for the account
NOT_FOUND = "The service refused the request (404)"


def membership(session: Session, job_id: str, action: str) -> Membership:
    """Whether the job `job_id` may be `action`, `discussed`, `downloaded`
    or `adopted`: refused, before the client is asked, where the selected
    session's service is not the one the client's settings name now; and,
    where the service's answer names another session or none, refused with
    the session it names. The service's answer is read now."""
    if session.service != matsya_client.service_identity():
        return Membership(
            None,
            f"the selected session {session.id} is kept by another service than the one the "
            f"client's settings name now, so job {job_id} is not {action}",
        )
    ran = matsya_client.run(["job", "status", job_id, "--json"])
    if ran.code != 0 and NOT_FOUND in ran.warning:
        # the service answers a job of another account's session as one it
        # does not hold (decision SG5-18)
        return Membership(
            None,
            f"job {job_id} belongs to a session of another account, or to none, so it is not "
            f"{action}; start a session of your own with bellman-matsya session new",
        )
    if ran.code != 0 or ran.answer is None:
        return Membership(
            None, f"the service did not answer for job {job_id}, so it is not {action}"
        )
    held = ran.answer.get("session")
    if held != session.id:
        owner = f"session {held}" if held else "no session"
        return Membership(
            ran.answer,
            f"job {job_id} belongs to {owner}, not to the selected session {session.id}, so it "
            f"is not {action}",
        )
    return Membership(ran.answer, None)


def read_job(session: Session, job_id: str) -> dict | None:
    """Read the current state of a job belonging to this session."""
    answer = membership(session, job_id, "read").job
    return answer if answer is not None and answer.get("id") == job_id else None


def discuss(session: Session, job_id: str) -> Membership:
    """Selects the job `job_id` as the one the session's conversation
    discusses, after `membership` admits it."""
    found = membership(session, job_id, "discussed")
    if found.refusal is not None:
        return found
    ran = matsya_client.run(["session", "select", session.id, job_id, "--json"])
    if ran.code != 0:
        return Membership(found.job, f"the service did not select job {job_id}: {ran.warning}")
    return found


# --- a reply to a job's question ---


class Replied(NamedTuple):
    """What `reply` answered: `work`, the reply's request as its record
    stands, None where nothing was sent; `historical`, whether the question
    is historical, a later entry of the user's kinds standing above the
    version of the session's text its job read; and `refusal`, the sentence
    that says why nothing was sent, None where the reply was sent."""

    work: Work | None
    historical: bool
    refusal: str | None


def _read_revision(job: dict) -> int | None:
    """The version of the session's text the job read: that of its
    `captured_source`, which the service fixed when it accepted the job,
    else the job's own `revision`; None where the service gives neither."""
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    captured = result.get("captured_source")
    held = captured if isinstance(captured, dict) else {}
    revision = held.get("revision", job.get("revision"))
    return revision if isinstance(revision, int) else None


def reply(
    folder: model.Folder, session: Session, job_id: str, question: int, text: str
) -> Replied:
    """A reply `text` to the question entry `question` that the job
    `job_id` asked (amendment 06 §2 item 16; decision SG5-19). After
    `membership` admits the job, the session's present version is read
    (`session show`) and compared with the version the job read
    (`_read_revision`): where a later entry of the user's kinds stands above
    it, the question is historical, nothing is sent or written, and acting
    on it needs a fresh submission. Otherwise the reply is sent by the
    client's `session add --replies-to` with a delivery identifier, its
    record, of the kind `reply`, written before the client runs, as a
    build's entry is (`add_entry`), with `replies_to`, the question's
    number, and `scheduled`, the continuation job the reply started, null
    where it started none; `accepted` is the reply's entry number, as text.
    The service is unchanged."""
    found = membership(session, job_id, "replied to")
    if found.refusal is not None:
        return Replied(None, False, found.refusal)
    shown = matsya_client.run(["session", "show", session.id, "--json"])
    now = shown.answer.get("revision") if shown.code == 0 and shown.answer else None
    read = _read_revision(found.job)
    if not isinstance(now, int) or read is None:
        return Replied(
            None, False, f"the service did not give the versions of session {session.id}, so "
            "no reply is sent"
        )
    if now > read:
        return Replied(
            None,
            True,
            f"the question of entry {question} is historical: the session's text has moved "
            f"from version {read} to version {now} since job {job_id} read it; submit the build "
            "again to act on it",
        )
    delivery = uuid.uuid4().hex
    record = {
        "format": FORMAT,
        "kind": "reply",
        "delivery": delivery,
        "session": session.id,
        "service": session.service,
        "prepared": None,
        "question": text,
        "replies_to": question,
        "scheduled": None,
        "accepted": None,
        "exit_code": None,
        "warning": "",
        "sent_at": _now(),
        "answered_at": None,
    }
    path = f"{REQUESTS_FOLDER}/{delivery}.json"
    digest = _write(folder, path, record, None)
    with tempfile.TemporaryDirectory() as holder:
        held = Path(holder) / "reply.txt"
        held.write_text(text, encoding="utf-8")
        ran = matsya_client.run(
            ["session", "add", session.id, str(held), "--replies-to", str(question),
             "--delivery-id", delivery, "--json"]
        )
    entry = ran.answer.get("entry") if ran.answer else None
    number = entry.get("number") if isinstance(entry, dict) else None
    scheduled = ran.answer.get("scheduled") if ran.answer else None
    answered = {
        **record,
        "accepted": str(number) if isinstance(number, int) else None,
        "scheduled": scheduled.get("id") if isinstance(scheduled, dict) else None,
        "exit_code": ran.code,
        "warning": ran.warning,
        "answered_at": _now(),
    }
    _write(folder, path, answered, digest)
    return Replied(Work(path, answered), False, None)


# --- the download ---


def _part(value) -> str:
    return "none" if value is None else str(value)


def download(folder: model.Folder, session: Session, job_id: str) -> Downloaded:
    """Writes one new copy of the job's model folder under
    `bellman-matsya-output/`, by the client's `job files`, named by the
    job's number, its iteration, the revision it read and its
    configuration (the module's docstring), after `membership` admits the
    job. The client writes into a hidden folder beside it, renamed to that
    name once the client has finished, and removed where it has not. A copy
    of that name that stands already is answered and nothing is written; a
    job that holds no record is refused."""
    found = membership(session, job_id, "downloaded")
    if found.refusal is not None:
        return Downloaded(None, False, found.refusal)
    job = found.job
    result = job.get("result")
    if not isinstance(result, dict):
        return Downloaded(
            None, False, f"job {job_id} holds no result yet, so it is not downloaded"
        )
    label = job.get("label") if isinstance(job.get("label"), dict) else {}
    number = label.get("number", job_id)
    configuration = job.get("configuration_id")
    name = (
        f"job-{_part(number)}-iteration-{_part(result.get('cycles_run'))}"
        f"-revision-{_part(job.get('revision'))}"
        f"-configuration-{_part(configuration[:12] if configuration else None)}"
    )
    path = f"{OUTPUT_FOLDER}/{name}"
    target = folder.root / path
    if target.is_dir() and any(target.iterdir()):
        return Downloaded(path, False, None)
    # the client writes into a hidden folder, renamed to the copy's name once
    # every file stands, so that a copy the client did not finish never
    # holds the name
    partial = folder.root / OUTPUT_FOLDER / f".{name}.{uuid.uuid4().hex}.partial"
    ran = matsya_client.run(["job", "files", job_id, str(partial), "--json"])
    if ran.code != 0:
        if partial.exists():
            shutil.rmtree(partial)
        refusal = f"the client did not write the files of job {job_id}: {ran.warning}"
        return Downloaded(None, False, refusal)
    partial.rename(target)
    return Downloaded(path, True, None)
