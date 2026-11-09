"""The backend of Bellman Workbench, without Solara (model interface
specification 0.3, §2.1, §2.2 rules 1 to 4, §2.4, §2.5 and §11).

Every function here reads the model folder, the stage object or git and
answers a plain record; the Solara page `app.py` and the console command
`command.py` call these functions and hold the session's state themselves.
Nothing in this module imports Solara, so the tests of `tests/test_model.py`
and a later language server read it alone.

Every function is pure over the files and the stage object, except
`save_file`, which writes one file under the module's lock, never within a
saved copy of a job's returned files (`read_only`); `export_view`
and `export_trellis`, which write a view's files and its record under
`model-explorer/`, with a `.gitignore` there where none stands;
`write_paper`, which writes a stage's two files under `paper/` once; and
the git commands, which run `git` as a subprocess in the folder. Every
query of a stage is total on a stage with a refused direction: a refused
builders graph contributes nothing to a count and raises nothing
(specification §2.2 rule 4).
"""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import importlib.metadata
import itertools
import json
import logging
import os
import posixpath
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlsplit

from model_explorer.graph_builder import EdgeOverlaysData

from bellman.refusals import (
    ConstructionError,
    Diagnostic as PackageDiagnostic,
    FactoryError,
    NotConstructed,
    TargetError,
)
from bellman.stage import (
    BOUNDARY_IDS,
    INITIAL_IDS,
    LAYER_ID_ENDING,
    PERCH_MARK,
    PRIMITIVE_SETS,
    ROLE_WORD,
    arvl,
    box_attributes,
    branches,
    card_sections,
    cntn,
    dcsn,
    elaborate_text,
    graph_refusal,
    header_line,
    header_of,
    node_place,
    perch_overlays,
    source_lines,
    source_spans,
    to_model_explorer,
    to_source,
    wire_counts,
    write_model_explorer,
)

__all__ = [
    "HIDDEN_NAMES",
    "OUTPUT_FOLDER",
    "read_only",
    "FACTORY_FOLDER",
    "RECIPE_STEM",
    "RECIPE",
    "LOOP_STATES",
    "Folder",
    "open_folder",
    "factory_path",
    "ADDITION_LINE",
    "is_addition",
    "is_addition_file",
    "folder_tree",
    "git_marks",
    "git_summary",
    "git_commit",
    "git_push",
    "GitResult",
    "GitChange",
    "git_changes",
    "GitPlace",
    "git_place",
    "holds_password",
    "destination_refusal",
    "init_repository",
    "EXPORT_FOLDER",
    "export_view",
    "export_trellis",
    "PAPER_FOLDER",
    "write_paper",
    "FileText",
    "read_file",
    "SaveResult",
    "save_file",
    "Diagnostic",
    "Elaboration",
    "elaborate_buffer",
    "loop_state",
    "counts",
    "refused_directions",
    "input_digests",
    "collection",
    "two_levels",
    "at_level",
    "builder_sections",
    "requirements",
    "edge_overlays",
    "block_at",
    "nodes_of_block",
    "node_attributes",
    "header_line_of",
    "Piece",
    "piece",
    "block_record",
    "boxes_reading",
    "stage_sheets",
    "occurrences",
    "sentence",
    "diagnostic_of",
    "package_versions",
    "RuleEntry",
    "rule_entry",
    "LOG",
    "EXCEPTION_LOGGED",
    "is_refusal",
    "name_at",
    "NameReport",
    "name_report",
    "TABLE_PERCHES",
    "ROLE_CLASS",
    "ROLE_CHOICES",
    "ADD_TARGETS",
    "ALL_BRANCHES",
    "Listing",
    "Row",
    "Target",
    "Group",
    "role_word",
    "classification",
    "named_rows",
    "add_roles",
    "set_completions",
    "Replacement",
    "classification_edits",
    "SNIPPETS",
    "unicode_shortcuts",
]

# The names the folder tree leaves out, beside every name that begins with
# ".": `model-explorer`, the generated folder of the views (specification
# §2.6); `.bellman`, the editor's own per-user folder; and, at AAS's ruling
# of 1 October 2026, `__pycache__`, Python's cache of compiled modules.
HIDDEN_NAMES = ("model-explorer", ".bellman", "__pycache__")

# The folder at the top of a model folder that holds the saved copies of the
# files a Matsya job returned, one folder per download (specification 0.6,
# unit G2; amendment 06 of spec 0.4, §4 and D-2). The tree shows it; no
# source of the model folder is read from it (`recipe.model_sources`), and
# the guarded save writes nothing within it (`read_only`), so that a copy
# stays as the download wrote it (amendment 06 §2 item 21).
OUTPUT_FOLDER = "bellman-matsya-output"

# The folder, relative to the model folder, that holds the files the
# factory reads: the recipe, the trellis and period files, `calibration/`,
# `settings/` and one folder per stage under `stages/` (the one layout of a
# model folder); and the recipe's name in it. `recipe.model_sources` offers
# the recipes of that folder, `factory_path(RECIPE)` first, where
# `creation.py` writes a new folder's recipe. Since `creation.py` imports
# this module, this module cannot import it without a cycle, so the names
# and `factory_path` stand here and `creation.py` imports them: one
# constant places the factory's files (merge note M8 of unit C). The
# recipe's name is written once, by its stem `RECIPE_STEM`, `spec`: a model
# folder's recipe is `spec.yml`, and a variant beside it `spec.<name>.yml`
# (AAS, 2 October 2026). `_role` and the order of a folder's recipes
# (`recipe.model_sources`) read the stem.
FACTORY_FOLDER = "declaration"
RECIPE_STEM = "spec"
RECIPE = f"{RECIPE_STEM}.yml"

# The four states of the loop as the status line names them (specification
# §2.2 rule 4): `not parsed`, the parser refused the text and no term
# exists; `parsed, refused`, the term exists and the construction refused
# it; `constructed, forward refused` and `constructed, backward refused`,
# the stage exists and the construction refused one builders graph; and
# `constructed`, both builders graphs exist.
LOOP_STATES = (
    "not parsed",
    "parsed, refused",
    "constructed, forward refused",
    "constructed, backward refused",
    "constructed",
)

# The environment of every git command (specification §5). With
# GIT_TERMINAL_PROMPT=0, git asks no question on the terminal. With
# GIT_SSH_COMMAND, which §5 requires, ssh runs in batch mode, in which it
# asks no question; this variable replaces an ssh command the user sets in
# core.sshCommand. With GCM_INTERACTIVE=never, Git Credential Manager opens
# no window. With GIT_ASKPASS empty, git runs no askpass program. Git reads
# core.askPass and SSH_ASKPASS only when GIT_ASKPASS is unset. A command
# that would ask for a credential therefore fails at once with git's own
# sentence. With GIT_LITERAL_PATHSPECS=0, git's default, an inherited 1
# does not make git read `:(literal)<path>` as the name of a file.
_GIT_ENVIRONMENT = {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_SSH_COMMAND": "ssh -o BatchMode=yes",
    "GCM_INTERACTIVE": "never",
    "GIT_ASKPASS": "",
    "GIT_LITERAL_PATHSPECS": "0",
}

# The one lock under which `save_file` compares the digest of a file with
# the digest expected and writes the file (specification §2.2 rule 3).
_SAVE_LOCK = threading.Lock()

# The directions of the two builders graphs, by the name the page uses and
# the attribute of `stage.builder` that holds each.
_GRAPH_OF_DIRECTION = {"backward": "bwd", "forward": "fwd"}

# The three binding verbs in the order a stage is bound, each with the key
# of the recipe record that holds its source (`factory/recipe.py`,
# `_syntactic_periods`), which is also the key of the stage's provenance
# under `sources` and the attribute of `stage.bindings`.
_BINDING_VERBS = (
    ("calibration", "calibrate"),
    ("methods", "methodize"),
    ("settings", "configure"),
)

# The rule under which the parser refuses a text; every other rule is a
# construction rule, applied to a term that parsed (`bellman.refusals.RULES`).
_SYNTAX_RULE = "syntax"

# The keys of one row of `ports` in a `Piece`, read from the port's
# attributes as the exporter writes them (`_port_item`).
_PORT_KEYS = ("label", "perch", "type", "role")


# --- the folder ---


class Folder(NamedTuple):
    """A model folder: `root`, the folder opened, and `git_root`, the root
    of the repository that holds it, None when no repository holds it."""

    root: Path
    git_root: Path | None


def open_folder(path) -> Folder:
    """The `Folder` of `path`, whose `git_root` is what `git rev-parse
    --show-toplevel` answers in it. A path that is no folder is refused
    with a ValueError."""
    root = Path(path).resolve()
    if not root.is_dir():
        raise ValueError(f"{path} is no folder, and the editor opens a model folder")
    result = _git(root, "rev-parse", "--show-toplevel")
    git_root = Path(result.sentence.strip()).resolve() if result.ok else None
    return Folder(root=root, git_root=git_root)


def factory_path(name: str) -> str:
    """The posix path, relative to the model folder, of the file or folder
    `name` of the factory's folder `FACTORY_FOLDER`: the recipe is at
    `factory_path(RECIPE)`, `declaration/spec.yml`."""
    return posixpath.join(FACTORY_FOLDER, name)


# The metadata line that opens an addition, a methods file that the
# semantics unions with its stage file (specification 0.7 §4), where a stage
# file opens with `@stage:`. The Workbench never elaborates an addition as a
# stage: it opens as text, and the package reads it with its stage
# (decisions S7-W1 and S7-W2).
ADDITION_LINE = "@methods:"


def is_addition(text: str) -> bool:
    """Whether the text of a `.bl` file is an addition: its first line that
    is not blank begins with `ADDITION_LINE`."""
    for line in text.splitlines():
        if line.strip():
            return line.lstrip().startswith(ADDITION_LINE)
    return False


def is_addition_file(path: Path) -> bool:
    """Whether the file at `path` is a `.bl` file whose text is an addition
    (`is_addition`); a file that cannot be read is none."""
    if Path(path).suffix != ".bl":
        return False
    try:
        return is_addition(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return False


def _role(relative: Path, root: Path) -> str:
    """The role of a file of the model folder `root` by the factory's
    convention: a `.bl` file is a stage, or `methods` where it is an
    addition (`is_addition_file`); `trellis*.yml` a trellis, `period*.yml` a
    period; a recipe is `<stem>.yml` or a name that begins `<stem>.` and
    ends `.yml` or `.yaml` (`spec.yml`, `spec.yaml`, `spec.<name>.yml`),
    where the stem is `RECIPE_STEM`; a `.yml` file under a folder
    named `calibration` or `settings`, named after the kind, or named
    `*_calibration.yml` or `*_settings.yml`, is of that kind; a methods
    file is an addition alone (decision S7-W6); any other file is
    `other`."""
    name = relative.name
    if relative.suffix == ".bl":
        return "methods" if is_addition_file(Path(root) / relative) else "stage"
    if relative.suffix not in (".yml", ".yaml"):
        return "other"
    if name == f"{RECIPE_STEM}.yml" or (
        name.startswith(f"{RECIPE_STEM}.") and name.endswith((".yml", ".yaml"))
    ):
        return "recipe"
    for prefix, role in (("trellis", "trellis"), ("period", "period")):
        if name.startswith(prefix):
            return role
    for kind in ("calibration", "settings"):
        if (kind in relative.parent.parts or relative.stem == kind
                or relative.stem.endswith("_" + kind)):
            return kind
    return "other"


def _hidden(name: str) -> bool:
    """Whether the tree leaves the entry `name` out: a name that begins
    with "." or stands in `HIDDEN_NAMES`."""
    return name.startswith(".") or name in HIDDEN_NAMES


def folder_tree(folder: Folder) -> list[dict]:
    """The nested entries of the model folder, folders first and each level
    in name order: `name`; `path`, relative to `folder.root` in posix form;
    `kind`, `file` or `folder`; `role`, by `_role` for a file and `folder`
    for a folder; `git`, the mark `git_marks` answers for a file and the
    empty string for a folder; and `children`, the entries of a folder.
    Names that begin with "." and the names of `HIDDEN_NAMES` are left
    out."""
    marks = git_marks(folder)

    def entries(directory: Path) -> list[dict]:
        children = [child for child in directory.iterdir() if not _hidden(child.name)]
        folders = sorted((c for c in children if c.is_dir()), key=lambda c: c.name)
        files = sorted((c for c in children if not c.is_dir()), key=lambda c: c.name)
        listed = []
        for child in folders:
            relative = child.relative_to(folder.root)
            listed.append(
                {
                    "name": child.name,
                    "path": relative.as_posix(),
                    "kind": "folder",
                    "role": "folder",
                    "git": "",
                    "children": entries(child),
                }
            )
        for child in files:
            relative = child.relative_to(folder.root)
            listed.append(
                {
                    "name": child.name,
                    "path": relative.as_posix(),
                    "kind": "file",
                    "role": _role(relative, folder.root),
                    "git": marks.get(relative.as_posix(), ""),
                    "children": [],
                }
            )
        return listed

    return entries(folder.root)


# --- git ---


class GitResult(NamedTuple):
    """What one git command answered: `ok`, whether it exited with 0, and
    `sentence`: on success, the stream the command writes its report to,
    standard output, or standard error for a push; on failure, its standard
    error, or its standard output when that is empty."""

    ok: bool
    sentence: str


def _git(root: Path, *arguments: str, report: str = "stdout") -> GitResult:
    """The result of `git <arguments>` run in `root` with no terminal
    prompt, ssh in batch mode and no standard input. A command that
    succeeds answers the stream `report` names, its standard output, or its
    standard error for a command that writes its report there, as `git
    push` does; one that fails answers its standard error, or its standard
    output when that is empty. A git that cannot be run answers the
    operating system's sentence, so no git failure raises through the
    page."""
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            env={**os.environ, **_GIT_ENVIRONMENT},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return GitResult(ok=False, sentence=f"git could not be run: {error}")
    if completed.returncode == 0:
        if report == "stderr":
            return GitResult(ok=True, sentence=completed.stderr.strip())
        return GitResult(ok=True, sentence=completed.stdout)
    return GitResult(ok=False, sentence=(completed.stderr or completed.stdout).strip())


def git_marks(folder: Folder) -> dict[str, str]:
    """The two-letter mark XY of `git status --porcelain -z
    --untracked-files=all` for each changed or untracked file under
    `folder.root`, keyed by the path relative to `folder.root` in posix
    form. A renamed or copied file is keyed by its new path. Outside a
    repository, or when git fails, the mapping is empty."""
    return {change.path: change.mark for change in git_changes(folder)}


def git_summary(folder: Folder) -> str:
    """One line on git's state of the folder, counting tracked files only,
    hidden or not (specification §2.1): `git: <n> modified`, where a
    modified file carries any mark but `??`, the mark of an untracked
    file, which the line does not count; `git: not a repository` outside
    one."""
    if folder.git_root is None:
        return "git: not a repository"
    marks = git_marks(folder)
    modified = sum(1 for mark in marks.values() if mark != "??")
    return f"git: {modified} modified"


def git_commit(folder: Folder, message: str, paths: list[str]) -> GitResult:
    """The result of `git commit --only -m <message> -- <paths>` in the
    folder, which records the named paths as they stand in the working
    tree and leaves the rest of the index as it is (specification §5); a
    deleted path records its deletion, and a rename is named by both its
    paths. Paths are relative to `folder.root`. Each path is passed to git
    as `:(literal)<path>`, so that git reads it as that file and not as a
    pattern (`[ab].yml` would also match `a.yml`), while hooks and every
    other command keep git's default reading. A named path git reports
    untracked is added to the index first, `git add -- <paths>`, since
    `git commit --only` records only paths git knows and answers `pathspec
    ... did not match any file(s) known to git` for another; a commit that
    then fails leaves those paths added. A commit with no path or no
    message is refused with a sentence, not run."""
    if not paths:
        return GitResult(ok=False, sentence="no file is named")
    if not message.strip():
        return GitResult(ok=False, sentence="the commit message is empty")
    marks = git_marks(folder)
    untracked = [path for path in paths if marks.get(path) == "??"]
    if untracked:
        added = _git(folder.root, "add", "--", *[f":(literal){path}" for path in untracked])
        if not added.ok:
            return added
    literal_paths = [f":(literal){path}" for path in paths]
    return _git(folder.root, "commit", "--only", "-m", message, "--", *literal_paths)


def git_push(folder: Folder) -> GitResult:
    """The result of `git push` for the current branch in the folder, with
    git's own sentence: on success the report git writes to its standard
    error, `To <destination>` and the line of each branch sent; a branch
    without a destination, or a push that would ask for a credential git
    does not hold, fails with git's sentence and asks nothing."""
    return _git(folder.root, "push", report="stderr")


class GitChange(NamedTuple):
    """One file git reports changed or untracked under the folder: `mark`,
    the two letters XY of `git status --porcelain`; `path`, relative to the
    folder in posix form, the new path of a rename or a copy; and
    `original`, the old path of a rename or a copy relative to the folder,
    None otherwise or where it lies outside the folder."""

    mark: str
    path: str
    original: str | None


def _relative(folder: Folder, path: str) -> str | None:
    """`path`, which git writes relative to the repository's root, as a
    path relative to `folder.root` in posix form; None where it lies
    outside the folder."""
    try:
        return (folder.git_root / path).relative_to(folder.root).as_posix()
    except ValueError:
        return None


def git_changes(folder: Folder) -> tuple[GitChange, ...]:
    """Each file `git status --porcelain -z --untracked-files=all` reports
    under `folder.root`, in git's order: what the tree's letters show and
    what the commit form lists (specification §2.1 and §5). Empty outside a
    repository or when git fails."""
    if folder.git_root is None:
        return ()
    result = _git(folder.root, "status", "--porcelain", "-z", "--untracked-files=all")
    if not result.ok:
        return ()
    fields = result.sentence.split("\0")
    changes, index = [], 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        if len(entry) < 4:
            continue
        mark, path, original = entry[:2], entry[3:], None
        # a rename or a copy writes the original path as the next field
        if mark[0] in "RC" or mark[1] in "RC":
            original = _relative(folder, fields[index])
            index += 1
        relative = _relative(folder, path)
        if relative is not None:
            changes.append(GitChange(mark, relative, original))
    return tuple(changes)


class GitPlace(NamedTuple):
    """Where a folder stands in git (specification §4): `root`, the root of
    the repository that holds it; `branch`, its current branch, named
    before the first commit too; and `destination`, the push URL of the
    remote the branch's configuration names. Each is None where there is
    none: outside a repository, on a detached head, or for a branch with no
    destination."""

    root: Path | None
    branch: str | None
    destination: str | None


def git_place(folder: Folder) -> GitPlace:
    """The `GitPlace` of the folder: its repository's root, `git symbolic-
    ref --short HEAD`, and the push URL of the remote
    `branch.<branch>.remote` names (`git remote get-url --push`)."""
    if folder.git_root is None:
        return GitPlace(None, None, None)
    found = _git(folder.root, "symbolic-ref", "--short", "HEAD")
    branch = found.sentence.strip() if found.ok else None
    destination = None
    if branch:
        remote = _git(folder.root, "config", "--get", f"branch.{branch}.remote")
        if remote.ok:
            url = _git(folder.root, "remote", "get-url", "--push", remote.sentence.strip())
            destination = url.sentence.strip() if url.ok else None
    return GitPlace(folder.git_root, branch, destination)


def holds_password(destination: str) -> bool:
    """Whether the URL `destination` carries a password,
    `https://user:password@host/…`, which the Workbench does not hold
    (specification §5)."""
    return "://" in destination and urlsplit(destination).password is not None


# git's form that names a remote helper, `<transport>::<address>`, as git
# reads it: "::" at the start of the destination or after a transport name
# there, of letters, digits, "+", "-" and ".", beginning with a letter or a
# digit; the "::" of an IPv6 host in brackets is not this form
_REMOTE_HELPER = re.compile(r"(?:[A-Za-z0-9][A-Za-z0-9+.-]*)?::")


def destination_refusal(destination: str) -> str | None:
    """The sentence that refuses the push destination `destination`, or
    None where it is accepted (specification §5 and §10: the Workbench
    holds no credential). Refused: a URL that carries a password
    (`holds_password`); an http or https URL that carries user information,
    `https://<token>@host/…`, the form in which a token is often written; a
    destination that begins with "-", which git would read as an option; a
    destination in git's remote-helper form, `<transport>::<address>` such
    as `https::https://…` or `ext::…`, whose address git passes, unchecked,
    to a helper program; and a URL that `urlsplit` cannot read. The user of
    `ssh://git@host/…` and of `git@host:owner/model.git` is a login name,
    not a credential, and is accepted, and so is an IPv6 host in brackets,
    `git@[::1]:owner/model.git`, whose "::" is not the remote-helper form."""
    if destination.startswith("-"):
        return "the push destination begins with '-'"
    if _REMOTE_HELPER.match(destination):
        return "the push destination is in git's remote-helper form, <transport>::<address>"
    try:
        if holds_password(destination):
            return "the push destination carries a password"
        parts = urlsplit(destination)
    except ValueError:
        return "the push destination does not read as a URL"
    if parts.scheme in ("http", "https") and parts.username is not None:
        return "the push destination carries user information before '@'"
    return None


def init_repository(path, destination: str | None = None) -> GitResult:
    """Makes the folder `path` a git repository of its own, `git init`,
    and, where `destination` is given, the push destination of its current
    branch: the remote `origin` at that URL and the branch's configuration
    `branch.<branch>.remote` and `branch.<branch>.merge`, so that `git
    push` sends the branch there before any push has set an upstream
    (specification §4, D10). A destination that `destination_refusal`
    refuses is refused with its sentence before git runs. Answers the first
    failing command's result, or the last one's."""
    refusal = destination_refusal(destination) if destination else None
    if refusal is not None:
        return GitResult(ok=False, sentence=refusal)
    result = _git(Path(path), "init", "-q")
    if not result.ok or not destination:
        return result
    found = _git(Path(path), "symbolic-ref", "--short", "HEAD")
    if not found.ok:
        return found
    branch = found.sentence.strip()
    for arguments in (
        ("remote", "add", "origin", destination),
        ("config", f"branch.{branch}.remote", "origin"),
        ("config", f"branch.{branch}.merge", f"refs/heads/{branch}"),
    ):
        result = _git(Path(path), *arguments)
        if not result.ok:
            return result
    return result


# --- the export record ---

# the folder of the generated views under a model folder (specification
# §2.6), which the tree hides and git ignores
EXPORT_FOLDER = "model-explorer"


def _write_export_files(folder: Folder, shown):
    """Reads package versions and HEAD before writing the view's two files
    and its folder's missing .gitignore (specification §5; G-D10). Answers
    the folder, the written paths, the versions and the commit. In a saved
    copy of a job's returned files nothing is written, and the sentence of
    `read_only` is raised as a PermissionError (amendment 06 §2 item 21)."""
    refusal = read_only(folder)
    if refusal is not None:
        raise PermissionError(refusal)
    package = package_versions()
    head = _git(folder.root, "rev-parse", "--verify", "-q", "HEAD")
    commit = head.sentence.strip() if folder.git_root is not None and head.ok else None
    views = folder.root / EXPORT_FOLDER
    written = [Path(path) for path in write_model_explorer(shown, views)]
    ignore = views / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    return views, written, package, commit


def _export_source_files(folder: Folder, source_digests: dict, commit: str | None):
    """The source paths, held digests and uncommitted marks, with git's
    marks for the folder (specification §5; G-D10). Paths within the folder
    are relative to it; other paths are absolute."""
    marks = git_marks(folder)
    files = []
    for name, digest in source_digests.items():
        resolved = Path(name).resolve()
        try:
            relative = resolved.relative_to(folder.root).as_posix()
        except ValueError:
            relative = str(resolved)
        uncommitted = commit is None or relative in marks
        files.append({"path": relative, "sha256": digest, "uncommitted": uncommitted})
    return files, marks


def export_view(
    folder: Folder,
    stage,
    text: str,
    relpath: str,
    *,
    unsaved: bool,
    occurrence: str | None,
    direction: str,
    source_digests: dict,
) -> Path:
    """Writes the view of `stage` under `model-explorer/` of the folder, the
    two files of the package's `write_model_explorer`, and beside them
    its export record, `<stem>.export.json` (specification §5); answers the
    record's path. The record names `file`, the stage file whose buffer
    `text` is; `occurrence` and `direction`, the recipe's occurrence the
    stage is bound as and the graph shown; `inputs`, the digest of the
    text, the status line's (`input_digests`), with the marks `unsaved` and
    `uncommitted`, and for each binding source the stage is bound by its
    digest beside the package's description of it
    (`stage.provenance["sources"]`); `source_files`, each file of
    `source_digests`, the files the shown object was bound from by path
    with their digests when it was made (the page's `Shown.source_digests`),
    each with whether git marks it; `generated`, the digest of each file
    written; `package`, the versions of bellman and bellman-workbench;
    `commit`, the folder's HEAD, None before a first commit or outside a
    repository; and `uncommitted`, whether the buffer is unsaved or git
    marks the stage file or a source file. Where `commit` is None, the
    text, every source file and the record are marked uncommitted, since no
    commit holds them. The versions and HEAD are read before any file is
    written. A `.gitignore` holding `*` is written into the folder of the
    views where it holds none, so that every view and record is ignored in
    any repository."""
    views, written, package, commit = _write_export_files(folder, stage)
    files, marks = _export_source_files(folder, source_digests, commit)
    digests = input_digests(stage, text)
    sources = dict(stage.provenance).get("sources", {})
    inputs = {
        "text": {
            "sha256": digests["text"],
            "unsaved": unsaved,
            "uncommitted": commit is None or relpath in marks,
        }
    }
    for kind, digest in digests.items():
        if kind != "text":
            inputs[kind] = {**dict(sources.get(kind, {})), "sha256": digest}
    record = {
        "file": relpath,
        "occurrence": occurrence,
        "direction": direction,
        "inputs": inputs,
        "source_files": files,
        "generated": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in written
        },
        "package": package,
        "commit": commit,
        "uncommitted": unsaved
        or inputs["text"]["uncommitted"]
        or any(entry["uncommitted"] for entry in files),
    }
    path = views / (written[0].name.removesuffix(".graph.json") + ".export.json")
    _replace_contents(path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return path


def export_trellis(
    folder: Folder,
    trellis: dict,
    *,
    source: str,
    restriction: str | None,
    direction: str,
    files: dict,
    buffered: dict | None = None,
) -> Path:
    """Writes the whole held trellis with `write_model_explorer` and its
    record, `model-explorer/trellis.export.json` (spec 0.4 §4; G-D10), and
    answers the record's path. The record names `source`, the recipe or
    trellis file; `restriction`, the drawing's restriction or None; and
    `direction`, the graph shown. `source_files` lists every held file's
    path, SHA-256 digest and uncommitted mark, and `"buffer": true` for
    each file whose path `buffered` holds, a file the reading took from an
    unsaved buffer (`TrellisShown.buffered`; spec 0.4 §3.3, brief rule 5).
    `write_model_explorer` writes the view with the keyword `unjoined` off,
    so that it compares with the lessons' recorded files. `generated` names
    the two written files and their digests; `package` names the versions of
    bellman and bellman-workbench; `commit` is the folder's HEAD or None;
    `uncommitted` is true where any source is uncommitted or HEAD is absent.
    Versions and HEAD are read before any write; the drawing's restriction
    does not restrict the exported trellis. Source marks refer to the
    recorded repository, including files outside the opened subfolder; a
    source outside that repository is uncommitted (G-R56). A held digest
    that differs from the recorded commit's exact bytes is uncommitted,
    even where the current source file is clean (spec 0.4 §4)."""
    views, written, package, commit = _write_export_files(folder, trellis)
    source_files, _ = _export_source_files(folder, files, commit)
    # `_export_source_files` answers one entry for each file, in the order
    # of `files`
    for entry, name in zip(source_files, files):
        if name in (buffered or {}):
            entry["buffer"] = True
    if commit is not None:
        marks = git_marks(Folder(folder.git_root, folder.git_root))
        for entry in source_files:
            resolved = (folder.root / entry["path"]).resolve()
            try:
                relative = resolved.relative_to(folder.git_root).as_posix()
            except ValueError:
                entry["uncommitted"] = True
            else:
                try:
                    blob = subprocess.run(
                        ["git", "cat-file", "blob", f"{commit}:{relative}"],
                        cwd=folder.git_root,
                        env={**os.environ, **_GIT_ENVIRONMENT},
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        check=False,
                    )
                except OSError:
                    entry["uncommitted"] = True
                else:
                    entry["uncommitted"] = (
                        relative in marks
                        or blob.returncode != 0
                        or hashlib.sha256(blob.stdout).hexdigest() != entry["sha256"]
                    )
    record = {
        "source": source,
        "restriction": restriction,
        "direction": direction,
        "source_files": source_files,
        "generated": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in written
        },
        "package": package,
        "commit": commit,
        "uncommitted": commit is None or any(entry["uncommitted"] for entry in source_files),
    }
    path = views / "trellis.export.json"
    _replace_contents(path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return path


# --- the paper files ---

# the folder beside `declaration/` into which `write_paper` writes a stage's
# Markdown and drawing (spec 0.4 §5.5; decision 38)
PAPER_FOLDER = "paper"


def _folder_path(folder: Folder, name: str) -> str:
    """The path `name` relative to the folder where it lies within it, in
    posix form, and absolute otherwise."""
    resolved = Path(name).resolve()
    try:
        return resolved.relative_to(folder.root).as_posix()
    except ValueError:
        return str(resolved)


def write_paper(
    folder: Folder, stage, relpath: str, text: str, source_digests: dict
) -> tuple[str, ...]:
    """Writes `paper/<stage>.md` and `paper/<stage>.svg` under the folder
    (spec 0.4 §5.5; brief rule 7; review 2; R-D17, R-D37) and answers their
    paths, relative to the folder; answers the empty tuple and writes
    nothing where `paper/<stage>.md` exists, so that each file is written
    once. The drawing is the stage's backward builders graph,
    `stage.builder.bwd.diagram().svg()`. It is made before any file is
    written, so that where the package refuses it, the refusal is raised
    and nothing is written. The Markdown holds a heading with the stage's
    name, the printed card of each builder (`piece`), backward then forward,
    each in a fenced block, the image link to the drawing, and one footnote.
    The footnote gives the path and the SHA-256 digest of the stage file
    `relpath`, whose text is `text`, and of each file of `source_digests`,
    the files the stage was bound from, by path with their digests (the
    page's `Shown.source_digests`). No PDF is written (R-D6). In a saved
    copy of a job's returned files nothing is written, and the sentence of
    `read_only` is raised as a PermissionError (amendment 06 §2 item 21)."""
    refusal = read_only(folder)
    if refusal is not None:
        raise PermissionError(refusal)
    name = stage.name
    papers = folder.root / PAPER_FOLDER
    markdown, drawing = papers / f"{name}.md", papers / f"{name}.svg"
    if markdown.exists():
        return ()
    svg = stage.builder.bwd.diagram().svg()
    graphs = _collection_of(stage)
    cards = [
        piece(stage, direction, builder + LAYER_ID_ENDING, graphs).card
        for direction in _GRAPH_OF_DIRECTION
        for builder in _builder_names(stage, direction)
    ]
    digests = [(relpath, input_digests(stage, text)["text"])]
    digests += [(_folder_path(folder, path), digest) for path, digest in source_digests.items()]
    listed = "; ".join(f"`{path}` `{digest}`" for path, digest in digests)
    blocks = [f"# {name}[^digests]", *(f"```\n{card}\n```" for card in cards)]
    blocks.append(f"![{name}]({name}.svg)")
    blocks.append(
        f"[^digests]: SHA-256 digests of the stage file and the files it is bound from: {listed}."
    )
    papers.mkdir(exist_ok=True)
    # the drawing first, so that a Markdown file on disk has its drawing
    _replace_contents(drawing, svg)
    _replace_contents(markdown, "\n\n".join(blocks) + "\n")
    return (f"{PAPER_FOLDER}/{name}.md", f"{PAPER_FOLDER}/{name}.svg")


# --- the file on disk ---


class FileText(NamedTuple):
    """The text of a file and `digest`, the SHA-256 of its UTF-8 bytes in
    hexadecimal."""

    text: str
    digest: str


def _digest(text: str) -> str:
    """The SHA-256 digest of the UTF-8 bytes of `text`, in hexadecimal."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_file(folder: Folder, relpath: str) -> FileText:
    """The text of the file at `relpath` under `folder.root`, read as UTF-8
    with its newlines as written, and its digest."""
    with open(folder.root / relpath, encoding="utf-8", newline="") as stream:
        text = stream.read()
    return FileText(text=text, digest=_digest(text))


def read_only(folder: Folder, relpath: str | None = None) -> str | None:
    """The sentence that refuses a change within a saved copy of a job's
    returned files, None where the change is admitted (amendment 06 §2 item
    21): with `relpath`, for the file at that path under the folder, whose
    resolved path has a folder named `OUTPUT_FOLDER` above it; without it,
    for the folder itself, where a folder of that name is the folder or
    holds it, as a copy opened as a model folder of its own is held."""
    if relpath is None:
        if OUTPUT_FOLDER in folder.root.parts:
            return (
                f"{folder.root.name} is a saved copy of a job's returned files, which is "
                "read-only; adopt its files to change the model"
            )
        return None
    if OUTPUT_FOLDER in (folder.root / relpath).resolve().parts[:-1]:
        return (
            f"{relpath} lies in a saved copy of a job's returned files under "
            f"{OUTPUT_FOLDER}/, which is read-only; adopt its files to change the model"
        )
    return None


class SaveResult(NamedTuple):
    """What `save_file` answered: `saved`; `digest`, the digest of the
    file after the call, of the text written or of the text on disk; and,
    when nothing was written, `reason`, one sentence, and `text`, the text
    on disk, None when the file no longer exists."""

    saved: bool
    digest: str
    reason: str | None
    text: str | None


def save_file(folder: Folder, relpath: str, text: str, expected_digest: str | None) -> SaveResult:
    """The result of writing `text` to the file at `relpath` under
    `folder.root`, under the module's lock: the file is read again and the
    digest of its contents compared with `expected_digest`, None for a file
    that does not exist yet; on a mismatch nothing is written and the
    answer carries the reason "the file changed on disk", the text on disk
    and its digest; otherwise the text is written as UTF-8 with its
    newlines as given to a temporary file in the same folder, which is
    then renamed over the file (`os.replace`), so that a reader of the file
    sees the old text or the new and never a part of either, and the
    answer carries the new digest. A write that fails leaves no temporary
    file behind. Modification times decide nothing (specification §2.2
    rule 3). A file within a saved copy of a job's returned files is not
    written, and the answer carries the sentence of `read_only` as its
    reason, the text on disk and its digest (amendment 06 §2 item 21)."""
    path = folder.root / relpath
    refusal = read_only(folder, relpath)
    with _SAVE_LOCK:
        if path.exists():
            with open(path, encoding="utf-8", newline="") as stream:
                on_disk = stream.read()
            found = _digest(on_disk)
        else:
            on_disk, found = None, None
        if refusal is not None:
            return SaveResult(saved=False, digest=found or "", reason=refusal, text=on_disk)
        if found != expected_digest:
            return SaveResult(
                saved=False,
                digest=found or "",
                reason="the file changed on disk",
                text=on_disk,
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        _replace_contents(path, text)
        return SaveResult(saved=True, digest=_digest(text), reason=None, text=None)


def _replace_contents(path: Path, text: str) -> None:
    """Writes `text` to a temporary file beside `path`, as UTF-8 with its
    newlines as given, and renames it over `path`; the temporary file is
    removed when the write or the rename fails."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


# --- the diagnostic record ---


class Diagnostic(NamedTuple):
    """One reported failure or check, the Workbench's one record of it,
    which the editor's underline, the Problems list, Details, the refusing
    node of a refused graph and the binding rows all read (Model Interface
    0.9 §4). Every record is made by `diagnostic_of` from what the package
    raised or recorded; nothing of it is a second description.

    The position and the sentence: `file`; `line`, `column`, `end_line` and
    `end_column`, the package's positions, counted from one in code points
    with an exclusive end, None where the package records none; `message`,
    the explanation, the package's own sentence; `rule`, the identifier the
    responsible check emits, None for an internal failure; `address`, the
    authored item, a block, a line or a key; and `write`, the action, the
    edit the check establishes, None where it establishes none.

    The kind and the operation: `kind` is `refusal` where the operation
    stopped, `held` for a refusal the construction keeps for one builders
    graph while it constructs the stage, `check` for a finding the operation
    records and continues past, and `internal` for an exception of no class
    of the package's refusals; `operation` names what produced the record,
    `parse`, `elaborate`, `calibrate`, `methodize`, `configure`, `connect`,
    `draw` or `read`, and `bind` for a binding of an occurrence that an
    exception stopped before the record could name the verb.

    The further facts of the record: `related`, the package's `Location`
    records of the second places the sentence names, each with its role;
    `direction`, `backward` or `forward` for a held refusal; `depends_on`,
    the address of the finding this one rests on, None where it rests on
    none; and `entry`, the identifier of the log entry that holds the
    traceback of an internal failure.

    The context, filled by the reader that knows it and absent from the
    conversion: `stage`, the key or name of the stage; `source`, the recipe
    or trellis file read; `view`, `stage` or `trellis`; `occurrences`, each
    `(h, key)` the problem affects, and `(h, None)` for a period a finding
    of the connections concerns; and `revision`, the SHA-256 digest of the
    text of `file` the check read.

    The category and the severity the Problems list shows are not stored
    on the record: the list derives the category from the record's
    operation and rule (`app._category`), and gives the severity where it
    reads a check, `warning` for a connection to review and for an input
    no line reads, `error` otherwise."""

    file: str | None
    line: int | None
    column: int | None
    end_line: int | None
    end_column: int | None
    message: str
    rule: str | None
    address: str | None
    write: str | None
    kind: str = "refusal"
    operation: str = "elaborate"
    related: tuple = ()
    direction: str | None = None
    depends_on: str | None = None
    entry: str | None = None
    stage: str | None = None
    source: str | None = None
    view: str | None = None
    occurrences: tuple = ()
    revision: str | None = None


def sentence(diagnostic: Diagnostic) -> str:
    """The sentence of a diagnostic as the Problems list prints it: the
    message, then the action on a line of its own where the check
    establishes one and the message does not already end with it, as a
    syntax refusal's does."""
    write = diagnostic.write
    if not write or diagnostic.message.endswith(write):
        return diagnostic.message
    return f"{diagnostic.message}\n{write}"


# The page's log, the server's standard error where nothing else configures
# it: an exception of no class of the package's refusals is written there
# with its traceback, under an identifier of its own, so that it can be
# reported by that identifier; `diagnostic_of` names the identifier on the
# record.
LOG = logging.getLogger(__name__)
# The identifiers of the entries, `exception 1`, `exception 2` and so on,
# counted from one in this process.
_ENTRIES = itertools.count(1)
# The words of such an entry: the identifier, the operation that stopped
# and the file or source read; the entry attributes the exception to
# nothing, since a function of the Workbench may have raised it.
EXCEPTION_LOGGED = "%s: an exception of no refusal class stopped %s of %s"


def is_refusal(error: BaseException) -> bool:
    """Whether `error` is of a class of the package's refusals,
    `ConstructionError`, `FactoryError` or `TargetError`. The classes alone
    decide: a `ValueError` of another class is an exception of no refusal
    class, an internal failure (Model Interface 0.9 §4)."""
    return isinstance(error, (ConstructionError, FactoryError, TargetError))


def diagnostic_of(error, operation: str = "elaborate", file: str | None = None) -> Diagnostic:
    """The one conversion into a `Diagnostic` of what the package raised or
    recorded during `operation`: a `ConstructionError` with its position, its
    related locations and its action, under the operation `parse` where its
    rule is `syntax`, the rule of the parser, whichever operation read the
    text; a `FactoryError` with the position of its key where the reader
    knows it; a `TargetError` with its rule and no position; a diagnostic
    the package recorded without raising, a connection finding or an unread
    input, as a `check`; the sentence of a refusal the package kept as
    text, as `bind_stage` does by default without `on_refusal`, as a
    refusal with that sentence and no rule or position; and an exception of
    any other class as an `internal` failure, written to the page's log
    with its traceback under an identifier the record names (`LOG`,
    `EXCEPTION_LOGGED`), the entry naming the identifier, the operation and
    `file` and attributing the exception to nothing. `file`, the file or
    source the operation read, is the record's file where the package
    names none. A refusal's `write` of the empty string is None."""
    if isinstance(error, ConstructionError):
        return Diagnostic(
            error.file or file,
            error.line,
            error.column,
            error.end_line,
            error.end_column,
            error.message,
            error.rule,
            error.address,
            error.write or None,
            "refusal",
            "parse" if error.rule == _SYNTAX_RULE else operation,
            tuple(error.related),
        )
    if isinstance(error, FactoryError):
        return Diagnostic(
            error.file or file,
            error.line,
            error.column,
            None,
            None,
            error.message,
            error.rule,
            error.address,
            error.write or None,
            "refusal",
            operation,
            tuple(error.related),
        )
    if isinstance(error, TargetError):
        return Diagnostic(file, None, None, None, None, error.message, error.rule, None,
                          error.write or None, "refusal", operation)
    if isinstance(error, PackageDiagnostic):
        return Diagnostic(file, None, None, None, None, error.message, error.rule, error.address,
                          None, "check", operation, depends_on=error.depends_on)
    if isinstance(error, str):
        return Diagnostic(file, None, None, None, None, error, None, None, None, "refusal",
                          operation)
    entry = f"exception {next(_ENTRIES)}"
    LOG.error(EXCEPTION_LOGGED, entry, operation, file, exc_info=error)
    return Diagnostic(file, None, None, None, None, f"{type(error).__name__}: {error}", None, None,
                      None, "internal", operation, entry=entry)


def _token_end(text: str, diagnostic: Diagnostic) -> Diagnostic:
    """The syntax refusal `diagnostic` of `text` with its end at the end of
    the refused token. The package's end is that of the parser's token,
    and where the parser's lexer reads the rest of a line as one token,
    `- 1         :: [id=util]` after an operator, the end runs over the
    spaces and the annotation `:: […]` that follow the refused text; the
    record ends where the refused text ends, so that the editor's
    underline, the source link and Details all read one range. Any other
    diagnostic, and a syntax refusal whose range is not within one line, is
    answered as it is."""
    if diagnostic.rule != _SYNTAX_RULE or diagnostic.line is None:
        return diagnostic
    if diagnostic.end_line != diagnostic.line or diagnostic.end_column is None:
        return diagnostic
    lines = text.split("\n")
    if not 1 <= diagnostic.line <= len(lines):
        return diagnostic
    covered = lines[diagnostic.line - 1][diagnostic.column - 1 : diagnostic.end_column - 1]
    token = covered.split("::", 1)[0].rstrip()
    if not token:
        return diagnostic
    return diagnostic._replace(end_column=diagnostic.column + len(token))


@functools.lru_cache(maxsize=None)
def package_versions() -> dict[str, str]:
    """The installed versions of `bellman` and `bellman-workbench`, by
    name, as the export records them and the copy of a problem names
    them; read once per process."""
    return {name: importlib.metadata.version(name) for name in ("bellman", "bellman-workbench")}


class RuleEntry(NamedTuple):
    """The entry of one rule that the Rule link of a line shows (Model
    Interface 0.9 §6 item 4): `text`, the entry as the catalogue of the
    imported Bellman prints it, and `address`, the rule's entry on the
    published Refusals page of that version, whose fragment is the rule's
    name."""

    text: str
    address: str


@functools.lru_cache(maxsize=None)
def rule_entry(rule: str) -> RuleEntry | None:
    """The entry of the rule `rule` in the catalogue of the imported
    Bellman (`bellman.refusal_catalogue.entry`), with the address of the
    rule's entry on its published page (`REFERENCE_PAGE` of the same
    module); None wherever no entry can be answered, so that the line shows
    the identifier alone: where the imported Bellman has no `entry`, as a
    release before Model Interface 0.9 has none, answers none for `rule`, a
    name no vocabulary of its rules holds, or fails, the failure then
    written to the page's log (`LOG`) with its traceback. The module is
    imported on demand and each rule's entry read once per process, from
    the installed package and with no connection."""
    try:
        catalogue = importlib.import_module("bellman.refusal_catalogue")
        entry = getattr(catalogue, "entry", None)
        found = None if entry is None else entry(rule)
        if found is None:
            return None
        return RuleEntry(str(found), f"{catalogue.REFERENCE_PAGE}#{rule}")
    except Exception:  # any failure of the catalogue of the imported Bellman
        LOG.warning("the catalogue of the imported Bellman answered no entry of the rule %s",
                    rule, exc_info=True)
        return None


# --- the buffer elaborated ---


class Elaboration(NamedTuple):
    """The result of elaborating one buffer: `stage`, the `ElaboratedStage`,
    None when the text is refused; `diagnostics`, the refusals; `origin`,
    the file's path given as the source; `revision`, the number the caller
    gave the buffer; `digest`, the SHA-256 of the text; `seconds`, the time
    the elaboration took; and `counts`, what `counts` answers for a stage,
    `{"blocks": n}` for a text whose term parsed and whose construction
    was refused, with `n` the top-level blocks of the term, and `{}` for a
    text that did not parse. `loop_state` names the state of the loop
    from this record."""

    stage: object
    diagnostics: tuple[Diagnostic, ...]
    origin: str
    revision: int
    digest: str
    seconds: float
    counts: dict


def _term_counts(text: str, origin: str, diagnostic: Diagnostic) -> dict:
    """The counts of a refused text: `{"blocks": n}`, the top-level blocks
    of the term in the package's span table (`source_spans`), where the
    refusal is of the construction and the term therefore parsed; `{}`
    where the parser refused the text or `source_spans` refuses it."""
    if diagnostic.rule == _SYNTAX_RULE:
        return {}
    try:
        spans = source_spans(text, origin)
    except ValueError:
        return {}
    return {"blocks": sum(1 for address in spans if "." not in address and not address.isdigit())}


def elaborate_buffer(text: str, origin: str, revision: int = 0) -> Elaboration:
    """The `Elaboration` of `text` with `origin` recorded as its source, by
    `elaborate_text` of `bellman.stage`. A refusal of the package's classes
    (`is_refusal`) becomes one `Diagnostic` (`diagnostic_of`), a syntax
    refusal's range ending where the refused text ends (`_token_end`);
    nothing else is caught, so that an exception of another class reaches
    the caller as the internal failure it is. A stage whose construction
    refused one builders graph is answered as the stage, with no
    diagnostic: `refused_directions` names the refusal."""
    started = time.perf_counter()
    try:
        stage = elaborate_text(text, origin)
    except (ConstructionError, FactoryError, TargetError) as error:
        seconds = time.perf_counter() - started
        diagnostic = _token_end(text, diagnostic_of(error, "elaborate", origin))
        return Elaboration(
            stage=None,
            diagnostics=(diagnostic,),
            origin=origin,
            revision=revision,
            digest=_digest(text),
            seconds=seconds,
            counts=_term_counts(text, origin, diagnostic),
        )
    seconds = time.perf_counter() - started
    return Elaboration(
        stage=stage,
        diagnostics=(),
        origin=origin,
        revision=revision,
        digest=_digest(text),
        seconds=seconds,
        counts=counts(stage),
    )


def loop_state(elaboration: Elaboration) -> str:
    """The state of the loop after `elaboration`, one of `LOOP_STATES`: `not
    parsed` where a diagnostic carries the rule `syntax`; `parsed, refused`
    where the stage is None under any other rule, or where both builders
    graphs of a stage are refused, since no graph is then drawn;
    `constructed, forward refused` or `constructed, backward refused` where
    `refused_directions` names that one direction; `constructed`
    otherwise."""
    if elaboration.stage is None:
        if any(diagnostic.rule == _SYNTAX_RULE for diagnostic in elaboration.diagnostics):
            return "not parsed"
        return "parsed, refused"
    refused = refused_directions(elaboration.stage)
    if len(refused) == 1:
        (direction,) = refused
        return f"constructed, {direction} refused"
    if refused:
        return "parsed, refused"
    return "constructed"


def _block_names(stage, direction: str) -> tuple:
    """The names of the blocks of the initial diagram of `direction`, the
    names of `stage.initial.<direction>.list()`; none where the construction
    refused that diagram."""
    try:
        return tuple(getattr(stage.initial, direction).list().names)
    except NotConstructed:
        return ()


def _builder_names(stage, direction: str) -> tuple:
    """The names of the builders of the builders graph of `direction`, the
    names of `stage.builder.bwd.list()` or `.fwd.list()`; none where the
    construction refused that graph."""
    try:
        return tuple(getattr(stage.builder, _GRAPH_OF_DIRECTION[direction]).list().names)
    except NotConstructed:
        return ()


def counts(stage, collection: dict | None = None) -> dict:
    """The counts of the object for the status line (specification §2.5),
    total on a stage with a refused direction: `blocks_backward` and
    `blocks_forward`, the blocks of each initial diagram
    (`stage.initial.backward.list()` and `.forward.list()`), and `blocks`,
    their sum; `builders`, the builders of the two builders graphs
    (`stage.builder.bwd.list()` and `.fwd.list()`); `wires_backward` and
    `wires_forward`, the wires of each builders graph of the collection as
    distinct wire identities, the package's `wire_counts`, so that a wire
    two boxes read counts once, and `wires`, their sum, 20 for `cons.bl`.
    A refused direction contributes 0 to each count and raises nothing,
    and so does a graph the collection does not hold; `refused` is a state
    (`loop_state`), not a count. The collection is `collection(stage)`
    where none is given."""
    found = wire_counts(collection or _collection_of(stage))
    blocks = {direction: len(_block_names(stage, direction)) for direction in _GRAPH_OF_DIRECTION}
    wires = {direction: found.get(direction, 0) for direction in _GRAPH_OF_DIRECTION}
    return {
        "blocks": sum(blocks.values()),
        "blocks_backward": blocks["backward"],
        "blocks_forward": blocks["forward"],
        "builders": sum(len(_builder_names(stage, d)) for d in _GRAPH_OF_DIRECTION),
        "wires": sum(wires.values()),
        "wires_backward": wires["backward"],
        "wires_forward": wires["forward"],
    }


def refused_directions(stage) -> dict[str, Diagnostic]:
    """The refusal of each builders graph the construction refused, by its
    direction, from the `Refusal` record the stage holds in the graph's
    place (the package's `graph_refusal`): the `Diagnostic` of the
    `NotConstructed` the package raises from that record where the graph is
    read (`graph_of`), of the kind `held`, with its `direction`. Empty where
    both graphs were constructed."""
    found = {}
    for direction in _GRAPH_OF_DIRECTION:
        refusal = graph_refusal(stage, "builders", direction)
        if refusal is None:
            continue
        held = NotConstructed(refusal.reason, **refusal.diagnostic)
        found[direction] = diagnostic_of(held)._replace(kind="held", direction=direction)
    return found


def _bound_digests(stage) -> dict[str, str]:
    """The digest of each binding source the stage's provenance names and
    the stage is bound by: `stage.provenance["sources"][kind]["sha256"]`
    for each kind of `_BINDING_VERBS` the stage is bound by, a calibration or
    settings binding that is not None, and for the methods the additions the
    provenance records (specification 0.7 §6; the methods of a version are
    the components of its signatures and no binding record). A source the
    provenance names for an unbound kind is the digest of an empty mapping
    and is left out."""
    sources = stage.provenance.get("sources", {})

    def bound(kind):
        if kind == "methods":
            return bool(stage.provenance.get("additions"))
        return getattr(stage.bindings, kind) is not None

    return {
        kind: sources[kind]["sha256"]
        for kind, _ in _BINDING_VERBS
        if bound(kind) and kind in sources
    }


def input_digests(stage, text: str) -> dict[str, str]:
    """The digest of every input of the shown object (specification §2.5):
    `text`, the SHA-256 of `text`, the buffer's text, then each binding
    source the stage's provenance names and the stage is bound by, keyed
    `calibration`, `methods` or `settings` (`_bound_digests`)."""
    return {"text": _digest(text), **_bound_digests(stage)}


# --- the view ---


def collection(stage, operative: bool = True) -> dict:
    """The graph collection of the stage as a plain dictionary,
    `dataclasses.asdict(to_model_explorer(stage))`: the one object the
    component's property `graphCollections` takes inside a list, and what
    `write_model_explorer` writes to `<stem>.graph.json`. A refused
    direction is its graph of one node, `<direction>:refused`. Where
    `operative` is false, the collection of the declared builders,
    `to_model_explorer(stage, declared=True)` (specification 0.6 §9)."""
    return dataclasses.asdict(to_model_explorer(stage, declared=not operative))


_CONNECTOR_FIELD_ID = re.compile(r"(?:un)?joined:[^:]+:(arvl|dcsn|cntn):([^:]+)")


def operator_boundary_ports(node: dict, side: str) -> list:
    """The native ports on one side of a forward operator boundary."""
    native = []
    for port in node.get(side) or []:
        occurrence, _, name = port["id"].rpartition("/")
        field = _CONNECTOR_FIELD_ID.fullmatch(name)
        if occurrence and occurrence == node.get("namespace") and field:
            attrs = {item["key"]: item["value"] for item in port.get("attrs") or []}
            if attrs.get("role") == "state" and field.groups() == (attrs.get("perch"), attrs.get("field")):
                continue
        native.append(port)
    return native


def forward_boundary_display(node: dict) -> tuple[str, str] | None:
    """The title and explanation of a forward measure boundary in Workbench."""
    boundary = node["id"].rsplit("/", 1)[-1]
    if boundary not in BOUNDARY_IDS:
        return None
    ports = operator_boundary_ports(node, "inputsMetadata") + operator_boundary_ports(
        node, "outputsMetadata"
    )
    measures = sum(
        any(item["key"] == "role" and item["value"] == "measure" for item in port.get("attrs") or [])
        for port in ports
    )
    if not measures:
        return None
    side = "Input" if boundary == BOUNDARY_IDS[0] else "Output"
    measure = "measure" if measures == 1 else "measures"
    title = f"{side} {measure}" if measures == len(ports) else f"Forward {side.lower()}s"
    return (
        title,
        "Forward operators propagate finite measures over the state spaces. "
        "When the transition takes an action, the policy supplies it.",
    )


def forward_display_collection(collection: dict | None) -> dict | None:
    """The collection the canvas draws: in the forward graph, each node
    that is a measure boundary (`forward_boundary_display`) carries the
    title as its label and the explanation as its description, and every
    other node and graph is as exported. None, and a collection that holds
    no graphs, are answered as they are."""
    if collection is None or "graphs" not in collection:
        return collection
    graphs = []
    for graph in collection["graphs"]:
        if graph["id"] != "forward":
            graphs.append(graph)
            continue
        nodes = []
        for node in graph["nodes"]:
            display = forward_boundary_display(node)
            nodes.append(
                {**node, "label": display[0], "description": display[1]} if display else node
            )
        graphs.append({**graph, "nodes": nodes})
    return {**collection, "graphs": graphs}


def two_levels(stage) -> bool:
    """Whether the declared builders of the stage, `stage.declared`, differ
    from its operative builders, `stage.builder`: whether a solution
    method's lines open a builder, the rows the stage's bindings record
    under `blocks` (specification 0.6 §7; specification 0.7 D8), since the
    two handles of a stage into which an addition has been read compare
    unequal where no line opens a builder (SE-37). Where they are one
    object, the layers button does not act (decision SE-5)."""
    return bool(stage.bindings.blocks)


def at_level(stage, operative: bool = True):
    """The stage version whose builders the view shows: `stage` itself at
    the operative level, and at the declared level the version
    `stage.declared` reads, whose builders are the declared builders and
    whose initial diagrams are the stage's (specification 0.6 §7), so that a
    piece of the declared builders graph is read as a piece of the
    operative one is (`piece`, `boxes_reading`)."""
    return stage if operative else stage.declared.version


# the function `collection` under a second name, for the functions whose
# parameter `collection` is the dictionary it answers
_collection_of = collection


def edge_overlays(stage) -> dict:
    """The three perch overlays of the stage as one `EdgeOverlaysData`
    named `perches`, as a plain dictionary: the form of the second file
    `write_model_explorer` writes, `<stem>.edge-overlays.json`, and what
    the component's configuration `edgeOverlaysDataListLeftPane` takes as
    one entry (specification §2.3). The overlays are the package's
    `perch_overlays(stage)`."""
    return dataclasses.asdict(EdgeOverlaysData(name="perches", overlays=perch_overlays(stage)))


# --- the blocks of the text and the boxes of the view ---


def block_at(spans, line: int) -> str | None:
    """The address of the top-level block whose span covers `line`: an
    address without "." that is no number, whose lines run from `span.line`
    to `span.end_line` inclusive; None when no block covers the line.
    `spans` is the table the package's `source_spans` answers."""
    for address, span in spans.items():
        if "." in address or address.isdigit():
            continue
        if span.line <= line <= span.end_line:
            return address
    return None


def nodes_of_block(collection: dict, graph: str, block: str) -> list[str]:
    """The ids of the nodes of the graph named `graph` in `collection` whose
    block, the package's `node_place`, is `block`, in node order."""
    graphs = {entry["id"]: entry["nodes"] for entry in collection["graphs"]}
    if graph not in graphs:
        raise ValueError(
            f"The view holds the graphs {' and '.join(graphs)}, and none named {graph!r}."
        )
    return [
        node["id"]
        for node in graphs[graph]
        if node_place(collection, graph, node["id"]).block == block
    ]


# --- the piece of a node ---


class Piece(NamedTuple):
    """What the panel shows for one node of the view (specification §2.4):
    `node_id` and `direction`, the graph's id; `kind`, `box` for a
    primitive operator, `layer` for a builder or a sub-builder, `boundary`
    for the graph's own `Inputs` or `Outputs` node (a word of this record
    alone, printed nowhere), `refusal` for the one node of a refused
    graph, `block` and `field` for the nodes of an initial diagram; `card`,
    the printed `denote()` of the piece, or the refusal's sentence;
    `kernel`, the printed `kernel()` of a box, or for a box of one branch
    the printed kernel of the branch's section, `kernel().section`;
    `attributes`, the rows the exporter writes on the node, or the
    refusal's position and rule;
    `address`, the block or line address the piece is born at, or the
    refusal's address; `block`, the block; `source_lines`, the lines the
    card's `Source` section quotes, each `(line, text)`; `definitions`,
    the definitions the piece's record names, each `(name, identity,
    line)` with the line of the definition's declaration, None for a name
    the definitions table does not hold; `ports`, `{"inputs": [row…],
    "outputs": [row…]}`, each row `{"label", "perch", "type", "role"}` of
    a box's port; `signature`, the printed `signature()` of a layer's
    builder or of the graph for its boundary nodes; and `sections`, for a
    builder's layer, the sections `Declared`, `Conditions` and `Method` its
    card holds (`builder_sections`), each `(heading, text)`; and `requires`,
    for a builder's layer at the declared level, the derivatives a bound
    method of the builder reads that no route supplies
    (`requirements`), which the page adds to the piece. `boundary_display`
    holds the title and explanation for a forward boundary."""

    node_id: str
    direction: str
    kind: str
    card: str
    kernel: str
    attributes: dict
    address: str
    block: str
    source_lines: list
    definitions: list
    ports: dict
    signature: str
    sections: tuple = ()
    requires: tuple = ()
    boundary_display: tuple[str, str] | None = None


# The sections of a builder's card that Details prints after its signature
# (specification 0.6 §9; the controller's third ruling on design pass 15),
# by the keys of their headings in the package's card.
BUILDER_SECTIONS = ("declared", "conditions", "method")


def builder_sections(record) -> tuple:
    """The sections `Declared`, `Conditions` and `Method` of the card of a
    builder's record, in the card's order, each `(heading, text)`: its
    heading as the card prints it, and its rows as `card_sections` gives
    them, the section's indentation removed and the rows one per line; none
    of a section the card does not hold."""
    found = []
    for section in card_sections(record):
        if section.label not in BUILDER_SECTIONS:
            continue
        lines = [line for row in section.rows for line in row]
        margin = min(len(line) - len(line.lstrip(" ")) for line in lines)
        found.append((section.heading, "\n".join(line[margin:] for line in lines)))
    return tuple(found)


def requirements(stage, builder: str) -> tuple:
    """The unmet requirements of the builder `builder` of the stage: each
    derivative a line of the builder reads of a value the stage writes that
    the value carries neither by a stated line nor by a representation whose
    row evaluates it, spelled as the amendment spells the term, `D_{a}V[>]`,
    in the order of the package's answer
    `stage.diagnostics()["derivative_missing"]`, whose address is the
    reading builder and whose candidates are the value's identity and the
    coordinates (AMD-MB-001 §5.3, D6); none for a builder that reads no such
    derivative."""
    found = []
    for diagnostic in stage.diagnostics().get("derivative_missing", ()):
        if diagnostic.address != builder:
            continue
        value, *coordinates = diagnostic.candidates
        _, _, perch, field = str(value).split(":", 3)
        heads = "".join(f"D_{{{coordinate}}}" for coordinate in coordinates)
        found.append(f"{heads}{field}{PERCH_MARK.get(perch, '')}")
    return tuple(found)


def _piece(node_id, direction, kind, **fields) -> Piece:
    """A `Piece` with the empty value in every field `fields` leaves out."""
    given = {
        "card": "",
        "kernel": "",
        "attributes": {},
        "address": "",
        "block": "",
        "source_lines": [],
        "definitions": [],
        "ports": {"inputs": [], "outputs": []},
        "signature": "",
        **fields,
    }
    return Piece(node_id=node_id, direction=direction, kind=kind, **given)


def node_attributes(collection: dict, graph: str, node_id: str) -> dict:
    """The attributes of the node `node_id` of the graph named `graph` in
    `collection`, as the exporter wrote them, `{key: value}`; a KeyError
    names a graph or a node the collection does not hold."""
    node = _node(collection, graph, node_id)
    return {item["key"]: item["value"] for item in node.get("attrs") or []}


def _node(collection: dict, graph: str, node_id: str) -> dict:
    """The node `node_id` of the graph named `graph` in `collection`; a
    KeyError names a graph or a node the collection does not hold."""
    graphs = {entry["id"]: entry["nodes"] for entry in collection["graphs"]}
    if graph not in graphs:
        raise KeyError(f"the view holds no graph named {graph!r}")
    for node in graphs[graph]:
        if node["id"] == node_id:
            return node
    raise KeyError(f"the graph {graph!r} holds no node {node_id!r}")


def _port_rows(items: list, keys: tuple = _PORT_KEYS) -> list[dict]:
    """The rows of the ports `items`, the metadata items of a node's inputs
    or outputs: for each item its attributes `keys`, by default `label`,
    `perch`, `type` and `role`, the empty string where the exporter wrote
    none."""
    rows = []
    for item in items:
        attributes = {pair["key"]: pair["value"] for pair in item.get("attrs") or []}
        rows.append({key: attributes.get(key, "") for key in keys})
    return rows


def header_line_of(attributes: dict) -> int | None:
    """The first line number of the `lines` row of a node's attributes,
    `cons.bl 21–23` giving 21, or None where the row is absent."""
    lines = attributes.get("lines")
    if not lines:
        return None
    numbers = re.findall(r"\d+", lines.split(" ", 1)[1] if " " in lines else lines)
    return int(numbers[0]) if numbers else None


def _position_line(position: str) -> int | None:
    """The line number of a position `applications/…/cons.bl:22`, the
    number after its last ":"; None where the position holds none."""
    _, separator, number = (position or "").rpartition(":")
    return int(number) if separator and number.isdigit() else None


def _quoted_lines(record) -> list[tuple[int, str]]:
    """The lines the `Source` section of a titled record's card quotes
    (the package's `source_lines`), each with its text as the
    file writes it, read from the positioned statements the record holds
    (an operator card's `kernel.statements`, an authored card's
    `statements`); a line at no position is left out."""
    held = getattr(getattr(record, "kernel", None), "statements", None)
    if held is None:
        held = getattr(record, "statements", ())
    texts = {_position_line(statement.position): statement.text for statement in held or ()}
    return [
        (line.number, texts.get(line.number, ""))
        for line in source_lines(record)
        if line.number is not None
    ]


def _declaration_line(stage, identity) -> int | None:
    """The line of the declaration of the definition `identity`: the first
    line the card of the definition quotes, `stage.definitions.denote(
    identity)`, which for a declaration is the declaration's own line;
    None where the definitions table does not hold the identity, as for a
    field function a block header supplies."""
    if identity not in stage.definitions:
        return None
    quoted = source_lines(stage.definitions.denote(identity))
    return next((line.number for line in quoted if line.number is not None), None)


def _definitions_named(stage, record) -> list[tuple[str, str, int | None]]:
    """The definitions a record names (its field `definitions`, the records
    the card's `Definitions referenced` section is written from), each as
    `(name, identity, line)` with the line of its declaration
    (`_declaration_line`), once for each identity: a set marked
    `!categories` denotes two objects, the set and its category map. The
    record names every definition the piece reads; the printed section lists
    those whose names the card writes."""
    rows = [
        (denoted.symbol, str(denoted.identity), _declaration_line(stage, denoted.identity))
        for denoted in getattr(record, "definitions", ())
    ]
    return list(dict.fromkeys(rows))


def _initial_direction(stage, block: str) -> str | None:
    """The direction of the initial diagram that holds the block `block`,
    `backward` or `forward`; None where neither does."""
    for direction in ("backward", "forward"):
        if block in _block_names(stage, direction):
            return direction
    return None


def _refusal_piece(stage, direction: str, node_id: str, collection: dict) -> Piece:
    """The `Piece` of the one node of a refused builders graph: its card
    the refusal's sentence, its attributes the refusal's position and rule,
    read from the one record (`refused_directions`) under their names and,
    under `refusal`, the whole text with the position and the rule as the
    exporter writes it on the node, its address the refusal's address."""
    refusal = refused_directions(stage).get(direction)
    if refusal is None:
        raise KeyError(f"the {direction} graph was constructed and holds no node {node_id!r}")
    attributes = dict(node_attributes(collection, direction, node_id))
    attributes.update(
        {
            key: getattr(refusal, key)
            for key in ("rule", "file", "line", "column", "end_line", "end_column", "address")
            if getattr(refusal, key) is not None
        }
    )
    return _piece(
        node_id,
        direction,
        "refusal",
        card=refusal.message,
        attributes=attributes,
        address=refusal.address or "",
    )


def _layer_piece(stage, direction: str, node_id: str, collection: dict) -> Piece:
    """The `Piece` of a layer, a builder or a sub-builder: its handle is
    reached from the builders graph of `direction` by the segments of its
    namespace, `stage.builder.bwd["cntn_to_dcsn"]["risk_ce"]`; its card
    `str(handle.denote())`, its signature `str(handle.signature())`, its
    attributes the layer's rows of the collection
    (`groupNodeAttributes[namespace]`: `inputs`, `outputs`, `where`,
    `feasible set`, `parameter` and `setting`, numbered where several),
    its address the handle's identity address and its block the package's
    `node_place` of the layer's id in the collection."""
    namespace = node_id[: -len(LAYER_ID_ENDING)]
    handle = getattr(stage.builder, _GRAPH_OF_DIRECTION[direction])
    for segment in namespace.split("/"):
        handle = handle[segment]
    graph = next((entry for entry in collection["graphs"] if entry["id"] == direction), {})
    attributes = dict(graph.get("groupNodeAttributes", {}).get(namespace, {}))
    record = handle.denote()
    return _piece(
        node_id,
        direction,
        "layer",
        card=str(record),
        attributes=attributes,
        address=handle.box.identity.address,
        block=node_place(collection, direction, node_id).block,
        signature=str(handle.signature()),
        sections=builder_sections(record),
    )


def piece(stage, direction: str, node_id: str, collection: dict | None = None) -> Piece:
    """The `Piece` of the node `node_id` of the graph `direction`
    (specification §2.4). For a builders graph, `backward` or `forward`:
    a box's handle is `stage.builder.bwd.primitives[node_id]` or `.fwd.`,
    its card `str(handle.denote())`, its kernel `str(handle.kernel())`, or
    for a box of one branch of a branching block the kernel the package
    gives for that branch's section, `str(handle.kernel().section)`
    (usability walkthrough §4 item 14; unit K, Task 14; decision K-I203),
    its attributes the package's `box_attributes(stage, direction,
    handle.box)`, its address and block those of the box's identity,
    `handle.box.identity`, its source lines those the card quotes
    (`_quoted_lines`), its definitions those its record names with their
    declaration lines (`_definitions_named`), and its ports the rows of
    its node's `inputsMetadata` and `outputsMetadata` in the collection
    (`_port_rows`); a layer, whose id ends with `LAYER_ID_ENDING`, is
    `_layer_piece`; `GraphInputs` and `GraphOutputs` carry the graph's
    printed `signature()` and the node's attributes; the one node of a
    refused graph, `<direction>:refused`, is `_refusal_piece`. For a node
    of an initial diagram, `direction` one of `INITIAL_IDS`' values: a
    block's piece has the block's printed record as its card, no kernel,
    the attributes the exporter wrote on its node and the block as its
    address and block; a field's piece has no card and no kernel, the
    field's rows as its attributes and no block. The collection is
    `collection(stage)` where none is given. A KeyError names an id the
    graph does not hold."""
    if collection is None:
        collection = _collection_of(stage)
    if direction in INITIAL_IDS.values():
        if node_id.endswith(LAYER_ID_ENDING):
            # a perch's layer of the diagram: its rows are the layer's own,
            # and it has no card and no signature, since no builder is its
            # handle (design pass 14 §7, rule 6)
            namespace = node_id[: -len(LAYER_ID_ENDING)]
            graph = next((entry for entry in collection["graphs"] if entry["id"] == direction), {})
            rows = graph.get("groupNodeAttributes") or {}
            if namespace not in rows:
                raise KeyError(f"the graph {direction!r} holds no layer {namespace!r}")
            return _piece(node_id, direction, "layer", attributes=dict(rows[namespace]))
        attributes = node_attributes(collection, direction, node_id)
        word = next(key for key, value in INITIAL_IDS.items() if value == direction)
        if attributes.get("kind") == "block":
            record = getattr(stage.initial, word)[node_id].denote()
            return _piece(
                node_id,
                direction,
                "block",
                card=str(record),
                attributes=attributes,
                address=node_id,
                block=node_id,
            )
        return _piece(node_id, direction, "field", attributes=attributes)
    if direction not in _GRAPH_OF_DIRECTION:
        raise KeyError(f"the view holds no graph named {direction!r}")
    if node_id == f"{direction}:refused":
        return _refusal_piece(stage, direction, node_id, collection)
    if direction in refused_directions(stage):
        raise KeyError(f"the {direction} graph is refused and holds no node {node_id!r}")
    if node_id.endswith(LAYER_ID_ENDING):
        return _layer_piece(stage, direction, node_id, collection)
    graph = getattr(stage.builder, _GRAPH_OF_DIRECTION[direction])
    if node_id in BOUNDARY_IDS:
        return _piece(
            node_id,
            direction,
            "boundary",
            attributes=node_attributes(collection, direction, node_id),
            signature=str(graph.signature()),
            boundary_display=(
                forward_boundary_display(_node(collection, direction, node_id))
                if direction == "forward"
                else None
            ),
        )
    handle = graph.primitives[node_id]
    identity = handle.box.identity
    record = handle.denote()
    kernel = handle.kernel()
    node = _node(collection, direction, node_id)
    return Piece(
        node_id=node_id,
        direction=direction,
        kind="box",
        card=str(record),
        kernel=str(kernel if kernel.section is None else kernel.section),
        attributes=box_attributes(stage, direction, handle.box),
        address=identity.address,
        block=identity.block,
        source_lines=_quoted_lines(record),
        definitions=_definitions_named(stage, record),
        ports={
            "inputs": _port_rows(node.get("inputsMetadata") or []),
            "outputs": _port_rows(node.get("outputsMetadata") or []),
        },
        signature=str(handle.signature()),
    )


def block_record(stage, block: str) -> str:
    """The printed record of the block `block` from the initial diagram it
    belongs to, `str(stage.initial.backward[block].denote())` or
    `.forward`; a KeyError names a block neither diagram holds."""
    direction = _initial_direction(stage, block)
    if direction is None:
        raise KeyError(f"no initial diagram of the stage holds a block {block!r}")
    return str(getattr(stage.initial, direction)[block].denote())


def _definition_lines(stage, identity) -> set[int]:
    """The lines at which the definition `identity` is written: the lines
    its card quotes, which for a declaration is its own line and for a law
    of motion `g` or a value aggregator `G` the lines of its block, and
    for a `g` or a `G` the header line of that block as well (the
    package's `header_line` of the block's record); none where the
    definitions table does not hold the identity."""
    if identity not in stage.definitions:
        return set()
    definition = stage.definitions[identity]
    lines = {
        line.number
        for line in source_lines(stage.definitions.denote(identity))
        if line.number is not None
    }
    if definition.kind in ("g", "G"):
        direction = _initial_direction(stage, definition.address)
        if direction is not None:
            header = header_line(getattr(stage.initial, direction)[definition.address].denote())
            if header is not None and header.number is not None:
                lines.add(header.number)
    return lines


def boxes_reading(stage, line: int) -> list[str]:
    """The ids of the boxes of both builders graphs whose meaning reads the
    line `line`: the boxes whose `kernel().origins` name a law of motion or
    a value aggregator whose block is headed at the line or holds a
    statement at it, or whose record names (`definitions`, the records
    the card's `Definitions referenced` is written from) a definition
    declared at the line, each box once, in the order of the backward
    graph's primitives and then the forward graph's. Both are queries of
    the object; a refused direction contributes nothing. The declaration
    of 𝑢 at line 8 of `cons.bl` reaches the boxes whose rules call 𝑢
    through their records' definitions, since `kernel().origins` names
    the aggregator and not the functions it calls."""
    found = []
    for direction, word in _GRAPH_OF_DIRECTION.items():
        if graph_refusal(stage, "builders", direction) is not None:
            continue
        primitives = getattr(stage.builder, word).primitives
        for node_id in primitives.list().names:
            handle = primitives[node_id]
            named = [origin.identity for origin in handle.kernel().origins]
            named.extend(denoted.identity for denoted in handle.denote().definitions)
            if any(line in _definition_lines(stage, identity) for identity in named):
                found.append(node_id)
    return found


def stage_sheets(stage) -> dict[str, str]:
    """The printed sheets of the stage the panel reaches when nothing is
    selected (specification §2.4): `view`, `str(stage.view())`;
    `definitions`, `str(stage.definitions.list())`; `fields`,
    `str(stage.fields())`; `obligations`, `str(stage.obligations())`; and
    `diagnostics`, `str(stage.diagnostics())`. Each prints on a stage with
    a refused direction."""
    return {
        "view": str(stage.view()),
        "definitions": str(stage.definitions.list()),
        "fields": str(stage.fields()),
        "obligations": str(stage.obligations()),
        "diagnostics": str(stage.diagnostics()),
    }


# --- the occurrences of a name ---


def occurrences(text: str, name: str) -> list[tuple[int, int]]:
    """The `(line, column)` of each whole-word occurrence of `name` in
    `text`, counted from one, in order; a word character is a letter, a
    digit or the underscore, so `c` matches in `c[>]` and not in `cp` or
    `m_d`."""
    pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)")
    found = []
    for number, line in enumerate(text.split("\n"), start=1):
        for match in pattern.finditer(line):
            found.append((number, match.start() + 1))
    return found


# a name of the text: a run of letters, digits and underscores
_NAME = re.compile(r"\w+")

# the marks a kernel writes after the name of a field at the arrival or the
# continuation perch, `≺` and `≻`, read from the package's table
_PERCH_MARKS = tuple(mark for mark in PERCH_MARK.values() if mark)


def _unmarked(written: str) -> str:
    """A name a kernel writes, without the perch mark it ends in: `a≻`
    gives `a`, and a name that ends in no mark is answered as written."""
    for mark in _PERCH_MARKS:
        if written.endswith(mark):
            return written[: -len(mark)]
    return written


def name_at(text: str, line: int, column: int) -> str | None:
    """The name under the cursor at `line` and `column`, counted from one,
    the column in code points as the editor sends it: the run of letters,
    digits and underscores that holds the character at the column or ends
    just before it; None on any other character, on a number and on a line
    the text does not hold."""
    lines = text.split("\n")
    if not 1 <= line <= len(lines):
        return None
    for match in _NAME.finditer(lines[line - 1]):
        if match.start() <= column - 1 <= match.end():
            return None if match.group().isdigit() else match.group()
    return None


class NameReport(NamedTuple):
    """What the panel lists for the name under the cursor (specification
    §3.2, the reference view): `name`; `declaration`, the line
    `name_report` reads as its declaration, None where it reads none;
    `occurrences`, each whole-word `(line, column)` of the name in the
    text, those on the declaration's line first (`occurrences`); and
    `boxes`, the boxes of both builders graphs that depend on it
    (`name_report`), each `(node id, graph)`."""

    name: str
    declaration: int | None
    occurrences: list
    boxes: list


def _box_contains(handle, name: str, named: list, field: bool) -> bool:
    """Whether the box `handle` depends on `name` (`name_report`, the page's
    term `depends on`): the definitions the package's record of the box
    rests on, `denote().definitions`, which follows the record's references
    through the definitions they use, hold one of the definitions `named` by
    its identity; or the kernel's `parameters` hold a parameter of that
    name; or, where `field`, a name of the kernel's `arguments` or
    `outputs`, read without the perch mark it ends in (`_unmarked`), or a
    wire the box reads or writes carries it. The record reaches beyond the
    kernel, to a parameter a function reads, the parameters of a
    distribution and the definitions of the values the box's wires carry.
    The kernel is built only where a parameter or a field is to be read in
    it."""
    if named:
        record = {denoted.identity for denoted in handle.denote().definitions}
        if any(identity in record for identity in named):
            return True
    parameter = any(identity.kind == "parameter" for identity in named)
    if not parameter and not field:
        return False
    if field:
        wires = (*handle.box.dom.inside, *handle.box.cod.inside)
        if any(sort.identity.field == name for sort in wires):
            return True
    kernel = handle.kernel()
    if parameter and name in kernel.parameters:
        return True
    written = [argument for argument, _ in kernel.arguments] + list(kernel.outputs)
    return field and any(_unmarked(str(each)) == name for each in written)


def name_report(stage, collection: dict, text: str, name: str) -> NameReport:
    """The `NameReport` of `name` in a stage and its text, the occurrences
    read from the text and every other part a query of the object. The
    definitions of the name are those whose identity carries it as its
    `field`, a set, a parameter, a function, a correspondence or a
    multiplier, or among its `subjects`, the distribution of a shock, `Ψ ~
    LogNormal(ν, σ_Ψ)`, whose identity carries no field. The declaration is
    the first line the card of one of them quotes (`_declaration_line`): a
    declaration's own line, the line of a multiplier a block body declares,
    `μ[>] : ℝ₊ ⟂ a >= 0`, and a shock's distribution's line, never a header
    that reads it. Where no definition names the word, the declaration of a
    field is the first line the `lines` row of its node in an initial
    diagram names (`header_line_of`), for the first field of that name in
    the order of the fields table that a diagram holds: a header that lists
    the field, or, for a field that a branch declares, the header of the
    block that holds the branch, a line that need not hold the name. A word
    the stage declares nowhere has no declaration and no box, and no box is
    read for it. A box is listed where it depends on the name, the page's
    term `depends on` (`_box_contains`): where the kernel's `parameters`
    hold a parameter of that name; where, for a field, a shock among them,
    the kernel reads or writes it, any perch mark removed, or one of the
    box's wires carries it, so that `V` of cons.bl lists four boxes through
    a wire alone; or where the definitions the package's record of the box
    rests on, `denote().definitions`, followed through the definitions they
    use, include one of the name's definitions by identity, so that
    `dcsn_to_arvl:Pullback` of cons.bl, whose kernel is the law of motion
    `m_d = m`, is listed for `ρ` through the definitions of the values its
    wires carry. A refused direction contributes no box."""
    named = [
        identity
        for identity in stage.definitions.keys()
        if identity.field == name or name in identity.subjects
    ]
    fields_named = [identity for identity, _ in stage.fields().items() if identity.field == name]
    found = occurrences(text, name)
    if not named and not fields_named:
        return NameReport(name, None, found, [])
    lines = (_declaration_line(stage, identity) for identity in named)
    declaration = next((line for line in lines if line is not None), None)
    for identity in fields_named if declaration is None else []:
        for graph_id in INITIAL_IDS.values():
            try:
                declaration = header_line_of(node_attributes(collection, graph_id, str(identity)))
            except KeyError:
                continue
            if declaration is not None:
                break
        if declaration is not None:
            break
    found = [place for place in found if place[0] == declaration] + [
        place for place in found if place[0] != declaration
    ]
    boxes = []
    for direction, word in _GRAPH_OF_DIRECTION.items():
        if graph_refusal(stage, "builders", direction) is not None:
            continue
        primitives = getattr(stage.builder, word).primitives
        for node_id in primitives.list().names:
            if _box_contains(primitives[node_id], name, named, bool(fields_named)):
                boxes.append((node_id, direction))
    return NameReport(name, declaration, found, boxes)


# --- the classification table (unit T of the model interface specification
# 0.3) ---

# The three tables, headed by the perches as the file writes them (rule 1).
TABLE_PERCHES = (arvl, dcsn, cntn)

# The class of each role in the tables, by which `ADD_TARGETS` names the side
# that takes a new field (rule 4). A shock, at no perch, and a multiplier,
# which a block body declares, stand in no table (T-R4).
ROLE_CLASS = {
    "state": "state",
    "control": "control",
    "value": "value",
}


def role_word(role: str) -> str:
    """The word of a role as the table prints it, from the package's
    `ROLE_WORD`: `!ctrl` or `!vlu` as a header writes it, and `state` for a
    state, whose listings write `!state` or no word."""
    return ROLE_WORD[role] if ROLE_CLASS[role] == "state" else "!" + ROLE_WORD[role]


# The choices of a role cell, in the order of ROLE_CLASS, and the role of
# each choice.
ROLE_CHOICES = tuple(role_word(role) for role in ROLE_CLASS)
_ROLE_OF_WORD = {role_word(role): role for role in ROLE_CLASS}

# The sides of block headers that take a field the file does not yet
# declare (rule 4, T-R6), by the table and the class of the field's role,
# each side the builder by the pair of perches it joins and its inputs or
# outputs. The first side takes the field's declaration. A second side, that
# of a decision state, lists the field by its name alone on the inputs of
# the builder joining `dcsn` and `cntn`, which reads it (AAS, L-D1).
ADD_TARGETS = {
    (arvl, "state"): (((arvl, dcsn), "in"),),
    (dcsn, "state"): (((arvl, dcsn), "out"), ((dcsn, cntn), "in")),
    (dcsn, "control"): (((dcsn, cntn), "in"),),
    (cntn, "state"): (((dcsn, cntn), "out"),),
    (cntn, "value"): (((cntn, dcsn), "in"),),
    (dcsn, "value"): (((cntn, dcsn), "out"),),
    (arvl, "value"): (((dcsn, arvl), "out"),),
}

# The group of the continuation table of a branching stage that holds the
# fields every branch holds, a state the nested block of each branch writes,
# and the fields whose branch no query answers: a value the builder joining
# `cntn` and `dcsn` does not type on the states of one branch, as where that
# builder is refused, or a state no nested block writes (rule 5, T-C12). The
# group stands in every branching stage, holding a row or none, and its box
# writes a new field into the block of every branch (AMD-MI-002 §5 rule 2,
# A2-D12).
ALL_BRANCHES = "all branches"


class Listing(NamedTuple):
    """One listing of a field on a side of a block header (rule 2), from
    the package's span table: `name`, the field as the header writes it,
    `V[>]`; `at`, the span of the field with its typing; and `domain`,
    `role` and `perch`, the spans of the set, the role word and the perch
    word its typing writes, None for a component it does not write."""

    name: str
    at: object
    domain: object
    role: object
    perch: object


class Row(NamedTuple):
    """One row of a table (rule 1): `identity`, as the fields table prints
    it, `cons:cntn:V`; `stem`, the field's name without a perch mark;
    `field`, the field as the header that first lists it writes it,
    `V[>]`; `set`, the declared set as the fields table prints it, the
    empty text where none is declared; `role`, the role word; `line`, the
    line of the header that first lists the field, None where no listing
    is read; and `listings`, in the order of the file."""

    identity: str
    stem: str
    field: str
    set: str
    role: str
    line: int | None
    listings: tuple


class Target(NamedTuple):
    """The side of a block header that takes a new field (rule 4): `at`,
    the span of the side, from its `(` to the end of its typing; `last`,
    the span of its last listing, None for an empty side `()`; `bare`,
    whether the side is one field written without parentheses;
    `name_alone`, whether the side takes the field's name alone, its
    declaration standing on another side (AAS, L-D1); and `names`, each
    field its listings write, as the header writes it, `V[>]`, in the order
    written."""

    at: object
    last: object
    bare: bool
    name_alone: bool = False
    names: tuple = ()


class Group(NamedTuple):
    """One table, or one group of the continuation table of a branching
    stage (rules 1 and 5): `perch`; `branch`, a label of
    `branches(stage)`, whose group holds the states of that branch that
    not every branch holds and the values the stage types on them,
    `ALL_BRANCHES`, or None for a table of one group; `rows`, in the order
    of the fields table; `targets`, for each role class, `state`, `control`
    or `value`, that the stage's builders name a side for, the tuple of the
    `Target`s of the sides the box writes a new field of that class into,
    in one edit: one side, except a state of the group `ALL_BRANCHES`,
    which takes the side of each branch, and a decision state, which a
    second side lists by its name alone (L-D1); and `heading`, the heading
    of a group of a branching stage, `cntn · d = keep`, None for a table of
    one group (AMD-MI-002 §5 rule 2, A2-D12)."""

    perch: str
    branch: str | None
    rows: tuple
    targets: dict
    heading: str | None = None


def _listings_of(spans, side: str) -> list[Listing]:
    """The listings of the side `side` of a block header, `cntn_to_dcsn.in`,
    in the order written: the entries of the span table one segment below
    the side's own, each with the entries of its components."""
    prefix = side + "."
    return [
        Listing(
            name=address[len(prefix) :],
            at=span,
            domain=spans.get(f"{address}.domain"),
            role=spans.get(f"{address}.role"),
            perch=spans.get(f"{address}.perch"),
        )
        for address, span in spans.items()
        if address.startswith(prefix) and "." not in address[len(prefix) :]
    ]


def _declared_sides(stage) -> dict[str, tuple]:
    """The identities each block's header lists on each side, inputs then
    outputs, in the order written (the package's `header_of`), for the
    blocks of the two initial diagrams; a diagram the construction refused
    contributes none."""
    found = {}
    for direction in ("forward", "backward"):
        try:
            graph = getattr(stage.initial, direction)
            names = graph.list().names
        except NotConstructed:
            continue
        for name in names:
            inputs, outputs = header_of(graph[name].box)
            found[name] = (
                tuple(sort.identity for sort in inputs),
                tuple(sort.identity for sort in outputs),
            )
    return found


def _listings_by_field(stage, spans) -> dict[str, tuple[Listing, ...]]:
    """The listings of each field, by its identity as a string, in the order
    of the file: each side of a block header paired, place by place, with
    the identities the object reads that side to list, and the output side
    of each branch's nested block, `dcsn_to_cntn.work.out`, with the fields
    `branches(stage)` answers for the label (T-R3). A side whose listings
    and identities differ in number is paired with none, so that no
    listing is guessed (rule 7)."""
    found = {}

    def pair(side, identities):
        listed = _listings_of(spans, side)
        if len(listed) == len(identities):
            for identity, listing in zip(identities, listed):
                found.setdefault(str(identity), []).append(listing)

    sides = _declared_sides(stage)
    for block, declared in sides.items():
        for side, identities in zip(("in", "out"), declared):
            pair(f"{block}.{side}", identities)
    for label, identities in branches(stage).items():
        for block in sides:
            if f"{block}.{label}.out" in spans:
                pair(f"{block}.{label}.out", identities)
    return {
        identity: tuple(sorted(listed, key=lambda listing: (listing.at.line, listing.at.column)))
        for identity, listed in found.items()
    }


def _builder_blocks(stage) -> dict:
    """The block of each builder of the stage by the pair of perches it
    joins, `("cntn", "dcsn")` to `cntn_to_dcsn`, read from `stage.builder`;
    a builders graph the construction refused holds no builder, and its
    pairs are absent."""
    try:
        keys = tuple(stage.builder.keys())
    except NotConstructed:
        return {}
    return {key: stage.builder[key].box.name for key in keys if isinstance(key, tuple)}


def header_pairs(spans, text: str) -> dict:
    """The block of each pair of perches as the block headers of `text`
    write it, `("cntn", "dcsn")` to `cntn_to_dcsn`: the perch words the two
    sides of each top-level block's header write after their fields, read
    as the classification table's text reading reads them (`_side_perch`),
    from `spans`, the package's span table of `text`, which holds the sides
    as `<block>.in` and `<block>.out`. A header with a side that writes no
    such word, as a bare side, whose field's own typing writes the perch
    word, gives no pair, and a pair two headers write, as a policy block
    and the block whose value it reads, gives no block. The sides that take
    a new field read these pairs where the package refused every builder of
    the stage, as for the empty stage "new stage" writes, whose blocks
    declare no field (`_targets`; unit L, Task 17; defect 7 of the UX
    simulation)."""
    lines = text.split("\n")
    found = {}
    for address in spans:
        sides = (f"{address}.in", f"{address}.out")
        if "." in address or not all(side in spans for side in sides):
            continue
        words = tuple(_side_perch(lines, spans, side, _listings_of(spans, side)) for side in sides)
        if None not in words:
            found.setdefault(words, []).append(address)
    return {pair: held[0] for pair, held in found.items() if len(held) == 1}


def _target(spans, side: str, name_alone: bool = False) -> Target | None:
    """The `Target` of the side `side` of a block header, which takes a
    new field's name alone where `name_alone` holds; None where the span
    table holds no such side."""
    at = spans.get(side)
    if at is None:
        return None
    listed = _listings_of(spans, side)
    return Target(
        at=at,
        last=listed[-1].at if listed else None,
        bare=len(listed) == 1 and listed[0].at == at,
        name_alone=name_alone,
        names=tuple(listing.name for listing in listed),
    )


def _targets(
    stage, spans, perch: str, branch: str | None, labels: tuple, headers: dict | None = None
) -> dict:
    """The sides that take a new field of each role class at `perch`
    (`ADD_TARGETS`), where a builder of the stage joins the pair of
    perches the rule names. In a branching stage, whose branches are
    `labels`, a branch's group takes a state into the output side of its
    nested block and a value into the inputs of the builder joining `cntn`
    and `dcsn`, the side the rule names for a continuation value (rule 5,
    T-C12); the group `ALL_BRANCHES` takes a state into the output side of
    the nested block of every branch, and a value into those inputs, the
    side every branch's value is written into (AMD-MI-002 §5 rule 2,
    A2-D12). A class takes no side where the span table or the stage's
    builders lack one of the sides of its declaration. The side that lists
    a decision state by its name alone (AAS, L-D1) is placed by the same
    rule, and where the stage lacks it the declaration stands alone. Where
    the package refused every builder of the stage, the pairs the block
    headers write, `headers` (`header_pairs`), stand for the builders, so
    that the box writes the first fields of a stage whose blocks declare
    none (unit L, Task 17)."""
    blocks = _builder_blocks(stage) or dict(headers or {})
    found = {}
    for (table, kind), sides in ADD_TARGETS.items():
        if table != perch:
            continue
        targets = []
        for place, (pair, side) in enumerate(sides):
            if pair not in blocks:
                addresses = []
            elif branch is not None and kind == "state":
                held = labels if branch == ALL_BRANCHES else (branch,)
                addresses = [f"{blocks[pair]}.{label}.{side}" for label in held]
            else:
                addresses = [f"{blocks[pair]}.{side}"]
            taken = tuple(_target(spans, address, place > 0) for address in addresses)
            if taken and None not in taken:
                targets.extend(taken)
            elif place == 0:
                # the declaration has no side, and the class takes none
                break
        if targets:
            found[kind] = tuple(targets)
    return found


def _row(identity, sort, listings: tuple) -> Row:
    """The row of one field: its identity and stem, the field as its first
    listing writes it, its declared set printed as the fields table prints
    it (`to_source`), its role word, the line of its first listing, and
    its listings."""
    return Row(
        identity=str(identity),
        stem=identity.field,
        field=listings[0].name if listings else identity.field,
        set="" if sort.domain is None else to_source(sort.domain),
        role=role_word(sort.role),
        line=listings[0].at.line if listings else None,
        listings=listings,
    )


def _value_branches(stage, labels) -> dict:
    """The label of each continuation value that the builder joining `cntn`
    and `dcsn` types on the states of one branch, by the perch and the name
    of the value's field: the label whose fields `branches(stage)` answers
    are the coordinates of that builder's input function, in their order
    (rule 5, T-C12). A stage where that builder does not stand
    answers none."""
    if (cntn, dcsn) not in _builder_blocks(stage):
        return {}
    by_fields = {}
    for label, identities in labels.items():
        by_fields.setdefault(tuple(identities), []).append(label)
    found = {}
    for wire in stage.builder[cntn, dcsn].signature().inputs:
        # the ordered coordinates, the third part of the documented sort
        held = by_fields.get(tuple(wire.mathematical_type.sort[2]), [])
        if len(held) == 1:
            found[(wire.identity.perch, wire.identity.field)] = held[0]
    return found


def _selecting_control(stage, labels) -> str | None:
    """The name of the control that selects the branches `labels` of a
    branching stage, `d`: the control the header of the branching block
    names among its inputs, read by `header_of` (`_declared_sides`) from
    the block whose outputs are the branches' fields, its role from the
    stage's fields table. The language selects that block's branches by
    the one control its header names (`docs/Bellman-Sym/05-branching.md`
    §4) and reads the block's lines at it
    (`docs/Bellman-Sym/API/stage/02-initial.md` §3). None where that
    header names no control, a branch drawn by nature, which a shock over
    the labels selects, and where no initial diagram holds the block."""
    fields = stage.fields()
    written = {str(i) for identities in labels.values() for i in identities}
    for inputs, outputs in _declared_sides(stage).values():
        if written & {str(i) for i in outputs}:
            controls = (i for i in inputs if i in fields and fields[i].role == "control")
            return next((i.field for i in controls), None)
    return None


def _heading(perch: str, branch: str | None, control: str | None) -> str | None:
    """The heading of a group of a branching stage (AMD-MI-002 §5 rule 2,
    A2-D12): `cntn · d = keep` for the branch `keep` the control `d`
    selects, `cntn · survive` for a branch drawn by nature, and
    `cntn · all branches`; None for a table of one group."""
    if branch is None:
        return None
    if branch == ALL_BRANCHES or control is None:
        return f"{perch} · {branch}"
    return f"{perch} · {control} = {branch}"


class _Reading(NamedTuple):
    """What the classification table reads of a stage or of a text: `rows`,
    the rows of each group by its `(perch, branch)`, in the order of the
    fields table; `labels`, the labels of the branches, in the order of the
    file; and `control`, the name of the control that selects them, None
    where none does."""

    rows: dict
    labels: tuple
    control: str | None


def _branch_of_states(labels: dict) -> dict:
    """The label of each state the nested block of one branch writes, by
    its identity as a string, from `labels`, each label to the identities
    its nested block writes; a state every branch holds stands under
    ALL_BRANCHES, not under a label, and is left out."""
    held = [{str(i) for i in identities} for identities in labels.values()]
    every = set.intersection(*held) if held else set()
    return {
        str(i): label
        for label, identities in labels.items()
        for i in identities
        if str(i) not in every
    }


def _stage_reading(stage, spans) -> _Reading:
    """The rows of the fields `stage.fields()` holds at each perch, in its
    order, each with its set and its role as that table prints them and its
    listings in the block headers, read from `spans`, the package's span
    table of the text the stage was elaborated from (`source_spans`); the
    branches are those of `branches(stage)`. Nothing is parsed here: the
    rows are the object's and the places the lowering's."""
    listed = _listings_by_field(stage, spans)
    labels = branches(stage)
    branch_of = _branch_of_states(labels)
    placed = _value_branches(stage, labels) if labels else {}
    rows = {}
    for identity, sort in stage.fields().items():
        if sort.perch not in TABLE_PERCHES or sort.role not in ROLE_CLASS:
            continue
        branch = None
        if labels and sort.perch == cntn:
            if ROLE_CLASS[sort.role] == "value":
                branch = placed.get((identity.perch, identity.field), ALL_BRANCHES)
            else:
                branch = branch_of.get(str(identity), ALL_BRANCHES)
        row = _row(identity, sort, listed.get(str(identity), ()))
        rows.setdefault((sort.perch, branch), []).append(row)
    control = _selecting_control(stage, labels) if labels else None
    return _Reading(rows, tuple(labels), control)


def classification(stage, spans, text: str | None = None, headers: dict | None = None) -> tuple:
    """The three tables of the classification table (rule 1), in the order
    `arvl`, `dcsn`, `cntn`, each holding its rows, each row with its set and
    its role as the fields table prints them and its listings in the block
    headers. Without `text`, the rows are those of the fields
    `stage.fields()` holds, their listings read from `spans`, the package's
    span table of the text the stage was elaborated from (`source_spans`).
    With `text`, the rows are read from the parse of `text`, whose span
    table is `spans`, and `stage` is the last construction of the file, of
    that text or of an earlier one, which answers only what the text alone
    does not (`_text_reading`; unit R, R-D57). In a branching stage the
    continuation table is one group per label of the branches, holding the
    fields that label's nested block writes and the values the builder
    joining `cntn` and `dcsn` types on those fields (rule 5, T-C12), then
    the group `ALL_BRANCHES`, holding a field the nested block of every
    branch writes and a value or a state that no query places on one
    branch, each group with its heading (AMD-MI-002 §5 rule 2, A2-D12). A
    field stands in one group alone (rules 1 and 2). The sides that take a
    new field are read from `spans`, and the block that joins each pair of
    perches from `stage`, or from `headers`, the pairs the block headers of
    the text of `spans` write (`header_pairs`), where the package refused
    every builder of `stage` (`_targets`; unit L, Task 17)."""
    if text is None:
        reading = _stage_reading(stage, spans)
    else:
        reading = _text_reading(stage, spans, text)
    groups = []
    for perch in TABLE_PERCHES:
        names = (*reading.labels, ALL_BRANCHES) if reading.labels and perch == cntn else (None,)
        for branch in names:
            groups.append(
                Group(
                    perch=perch,
                    branch=branch,
                    rows=tuple(reading.rows.get((perch, branch), ())),
                    targets=_targets(stage, spans, perch, branch, reading.labels, headers),
                    heading=_heading(perch, branch, reading.control),
                )
            )
    return tuple(groups)


# The perch each written mark of a listed field names, `V[>]` at
# continuation and `V[<]` at arrival, the marks of the language's
# vocabulary (`WRITTEN_MARK` of `bellman/syntax/vocabulary.py`, which
# `bellman.stage` does not export); a field of the decision perch is written
# bare, and the span table names a field written `c[~]` bare.
_PERCH_OF_MARK = {"[<]": arvl, "[>]": cntn}

# The role each role word of a typing names, `!ctrl` to `control`.
_ROLE_OF_TEXT = {"!" + word: role for role, word in ROLE_WORD.items()}


class _Listed(NamedTuple):
    """One listing of a field as the text alone gives it (R-D57):
    `listing`; `block`, the block whose header writes it; `label`, the
    branch whose nested block writes it, None on a block's own side;
    `output`, whether it stands on an output side; `stem`, the field's
    name without its mark; `placed`, the perch its mark or its own perch
    word names, None for neither; `side`, the perch word its side writes
    after its fields, None for none; and `role`, the role its role word
    names, None for none."""

    listing: Listing
    block: str
    label: str | None
    output: bool
    stem: str
    placed: str | None
    side: str | None
    role: str | None


def _text_between(lines: list, start: tuple, end: tuple) -> str:
    """The text of `lines`, a text's lines, from `start` to `end`, each a
    place `(line, column)` counted from one in code points, the end just
    after the last character."""
    (line, column), (end_line, end_column) = start, end
    if line == end_line:
        return lines[line - 1][column - 1 : end_column - 1]
    first, last = lines[line - 1][column - 1 :], lines[end_line - 1][: end_column - 1]
    return "\n".join([first, *lines[line : end_line - 1], last])


def _written(lines: list, span) -> str | None:
    """The text the span `span` covers in `lines`, None for no span."""
    if span is None:
        return None
    return _text_between(lines, (span.line, span.column), (span.end_line, span.end_column))


def _side_perch(lines: list, spans, side: str, listed: list) -> str | None:
    """The perch the side `side` of a block header writes after its fields,
    `cntn` for `(a : Xa) : !cntn`; None where it writes none, as a bare
    side, whose field's own typing writes the perch word."""
    at = spans[side]
    last = listed[-1].at if listed else None
    start = (last.end_line, last.end_column) if last else (at.line, at.column)
    tail = _text_between(lines, start, (at.end_line, at.end_column))
    return next((word for word in re.findall(r"!(\w+)", tail) if word in TABLE_PERCHES), None)


def _sets_written(lines: list, listings) -> tuple:
    """The sets the listings `listings` write, as the text whose lines are
    `lines` writes them, in their order; a listing that writes none adds
    none."""
    return tuple(_written(lines, each.domain) for each in listings if each.domain is not None)


def _printed_sets(stage) -> dict:
    """The set the fields table of `stage` prints for each field, by its
    identity as a string, with the sets its listings write in the text the
    stage was elaborated from (its provenance's `text`), as
    `(printed, written)`; none for a stage whose provenance holds no
    text."""
    text = stage.provenance.get("text")
    if not text:
        return {}
    spans = source_spans(text, stage.provenance.get("origin"))
    lines = text.split("\n")
    return {
        row.identity: (row.set, _sets_written(lines, row.listings))
        for rows in _stage_reading(stage, spans).rows.values()
        for row in rows
    }


def _listed_in_text(spans, lines: list) -> list:
    """Every `_Listed` of the text whose lines are `lines` and whose span
    table is `spans`, in the order of the text: the listings of each side
    of a block header and of each branch's nested block, a side being an
    address `<block>.in` whose `<block>.out` the table also holds."""
    found = []
    for address in spans:
        base = address.removesuffix(".in")
        if base == address or f"{base}.out" not in spans:
            continue
        block, _, label = base.partition(".")
        for side, output in ((address, False), (f"{base}.out", True)):
            listed = _listings_of(spans, side)
            word = _side_perch(lines, spans, side, listed)
            for listing in listed:
                mark = next((m for m in _PERCH_OF_MARK if listing.name.endswith(m)), "")
                own = (_written(lines, listing.perch) or "").removeprefix("!")
                found.append(
                    _Listed(
                        listing=listing,
                        block=block,
                        label=label or None,
                        output=output,
                        stem=listing.name.removesuffix(mark) if mark else listing.name,
                        placed=_PERCH_OF_MARK[mark] if mark else (own or None),
                        side=word,
                        role=_ROLE_OF_TEXT.get(_written(lines, listing.role)),
                    )
                )
    return sorted(found, key=lambda each: (each.listing.at.line, each.listing.at.column))


def _text_reading(stage, spans, text: str) -> _Reading:
    """The rows of the fields the block headers of `text` list, read from
    its parse, whose span table is `spans` (unit R, R-D57: while the
    construction of a text is refused, its rows are read from the text, so
    that a write lands in the text as it is). A field is a name with its
    perch, its identity `<stage>:<perch>:<name>` under the name of
    `stage`, the last construction of the file. Its role is the one its
    first role word in the headers names, else the role `stage` gives a
    field of that name, as for a role a top-level declaration writes, else
    `state`; a role no table holds, a shock or a multiplier, has no row. A
    control stands at the decision perch, and any other field at the perch
    its mark or its own perch word names, else at the perch its side
    writes; a listing that none of these places has no row, so that no
    perch is guessed. A row's listings are those of its field, in the
    order of the text. Its set is the one `stage` prints for the field
    where the field's listings write the sets they write in the text
    `stage` was elaborated from (`_printed_sets`), the meet of the sets
    written being the construction's to compute; otherwise the set its
    first listing that writes one writes, as written, else none. The
    branches are the labels of the nested blocks the text writes, a state
    standing in the group of the one branch whose nested block writes it,
    as `branches` answers; a value stands in the group `stage` places it
    in (`_value_branches`), else in ALL_BRANCHES; the control that selects
    the branches is the first control the inputs of their block list."""
    lines = text.split("\n")
    listed = _listed_in_text(spans, lines)
    known_roles = {identity.field: sort.role for identity, sort in stage.fields().items()}
    printed = _printed_sets(stage)
    roles = {}
    for each in listed:
        if each.role is not None:
            roles.setdefault(each.stem, each.role)
    fields, labels = {}, {}
    for each in listed:
        role = roles.get(each.stem) or known_roles.get(each.stem, "state")
        perch = dcsn if role == "control" else each.placed or each.side
        if role not in ROLE_CLASS or perch not in TABLE_PERCHES:
            continue
        identity = f"{stage.name}:{perch}:{each.stem}"
        fields.setdefault(identity, (perch, each.stem, role, []))[3].append(each)
        if each.label is not None:
            outputs = labels.setdefault(each.label, [])
            if each.output and identity not in outputs:
                outputs.append(identity)
    branch_of = _branch_of_states(labels)
    stage_labels = branches(stage)
    placed = _value_branches(stage, stage_labels) if labels and stage_labels else {}
    rows = {}
    for identity, (perch, stem, role, items) in fields.items():
        branch = None
        if labels and perch == cntn:
            if ROLE_CLASS[role] == "value":
                branch = placed.get((perch, stem), ALL_BRANCHES)
            else:
                branch = branch_of.get(identity, ALL_BRANCHES)
        listings = tuple(each.listing for each in items)
        written = _sets_written(lines, listings)
        kept, before = printed.get(identity, (None, None))
        row = Row(
            identity=identity,
            stem=stem,
            field=items[0].listing.name,
            set=kept if written == before else (written[0] if written else ""),
            role=role_word(role),
            line=items[0].listing.at.line,
            listings=listings,
        )
        rows.setdefault((perch, branch), []).append(row)
    branching = {each.block for each in listed if each.label is not None}
    control = next(
        (
            each.stem
            for each in listed
            if each.block in branching
            and each.label is None
            and not each.output
            and (roles.get(each.stem) or known_roles.get(each.stem)) == "control"
        ),
        None,
    )
    return _Reading(rows, tuple(labels), control)


def named_rows(groups, places) -> dict:
    """The rows of the tables `groups` that a refusal names (unit R, R-D57):
    each row one of whose listings holds one of `places`, each `(line,
    column, sentence)` for a position of the file that a refusal's record
    names, its own or a related location's (Model Interface 0.9 §4), mapped
    to the sentence of the first such place."""
    found = {}
    for group in groups:
        for row in group.rows:
            sentence = next(
                (
                    sentence
                    for line, column, sentence in places
                    if any(_holds(listing.at, line, column) for listing in row.listings)
                ),
                None,
            )
            if sentence is not None:
                found[row.identity] = sentence
    return found


def _holds(span, line: int, column: int) -> bool:
    """Whether the span `span` holds the position `line`, `column`, the
    span's end being exclusive."""
    return (span.line, span.column) <= (line, column) < (span.end_line, span.end_column)


def add_roles(group: Group) -> tuple[str, ...]:
    """The role words the box `add field` of `group` offers: those of
    `ROLE_CHOICES` whose class has a side among the group's targets."""
    return tuple(word for word in ROLE_CHOICES if ROLE_CLASS[_ROLE_OF_WORD[word]] in group.targets)


def set_completions(stage) -> tuple[str, ...]:
    """The completions of a set cell (rule 6): the names of the sets the
    file defines, then the glyph of each primitive set of the language
    (`PRIMITIVE_SETS`), each once."""
    named = [d.identity.field for d in stage.definitions.values() if d.kind == "set"]
    glyphs = [name for name, primitive in PRIMITIVE_SETS.items() if name == primitive.glyph]
    return tuple(dict.fromkeys(named + glyphs))


class Replacement(NamedTuple):
    """One replacement of a text (rule 3): the span from `line` and
    `column` to `end_line` and `end_column`, counted from one in code
    points as the package counts them, the end just after the last
    character replaced, and `text`, written there; an insertion ends where
    it starts."""

    line: int
    column: int
    end_line: int
    end_column: int
    text: str


def _replaced(span, text: str) -> Replacement:
    """The replacement of the span `span` by `text`."""
    return Replacement(span.line, span.column, span.end_line, span.end_column, text)


def _inserted(line: int, column: int, text: str) -> Replacement:
    """The insertion of `text` at `line` and `column`."""
    return Replacement(line, column, line, column, text)


def _first_component(listing: Listing):
    """The span of the first component a listing's typing writes."""
    spans = [span for span in (listing.domain, listing.role, listing.perch) if span is not None]
    return min(spans, key=lambda span: (span.line, span.column))


def classification_edits(groups, change: dict) -> tuple:
    """The replacements one change of the classification table makes in
    the text the tables were read from (rules 2 to 4), in the order of
    the text. `change` is what a cell or a box sends: `{"kind": "set" |
    "role", "identity", "value"}` for a cell and `{"kind": "add", "perch",
    "branch", "field", "set", "role"}` for the box `add field`. A set or a
    role is written only where a block header declares the field (T-C22),
    in every declaration of the field (rule 3), which for a field of the
    group `ALL_BRANCHES` stands in the block of each branch (AMD-MI-002 §5
    rule 2, A2-D12).
    A change the table cannot write is refused with a ValueError whose
    sentence the page shows; the text the change makes is the
    elaborator's to judge, as after typing."""
    kind = change.get("kind")
    if kind in ("set", "role"):
        edits = _component_edits(groups, change)
    elif kind == "add":
        edits = _added_field(groups, change)
    else:
        raise ValueError(f"the table makes no change of the kind {kind!r}")
    return tuple(sorted(edits, key=lambda edit: (edit.line, edit.column)))


def _component_edits(groups, change: dict) -> list:
    """The edits of a set or a role changed in a cell (rule 3, T-C22). A
    listing declares the field where its typing writes a set, a role word
    or a perch word, and the table writes into these declarations alone,
    since the lowering keeps the components of block headers only (T-R2).
    A component is rewritten in every declaration that writes it. A field
    with no set at all, which the elaborator admits, has the set written
    before the first component of each declaration; where no declaration
    writes a role word and the field is a state, the role chosen is
    written after each declaration's typing. The role `state` replaces a
    written role word by `!state`, and for a state whose declarations
    write no role word it writes nothing (T-R5). A change is refused where
    the component the row shows is written in no declaration of the
    field: any change where no block header declares the field, a set
    change where the row shows a set no declaration writes, and a role
    change where no declaration writes the role word of a field that is
    not a state, a word that then stands at the top level or beside
    another field of the same name."""
    rows = {row.identity: row for group in groups for row in group.rows}
    row = rows.get(change.get("identity"))
    if row is None or not row.listings:
        named = row.field if row is not None else "this field"
        raise ValueError(f"no block header lists {named}")
    value = (change.get("value") or "").strip()
    declaring = [
        listing
        for listing in row.listings
        if (listing.domain, listing.role, listing.perch) != (None, None, None)
    ]
    undeclared = f"no block header declares {row.field}"
    if change["kind"] == "set":
        if not value:
            raise ValueError(f"the set of {row.field} is empty")
        written = [listing for listing in declaring if listing.domain is not None]
        if written:
            return [_replaced(listing.domain, value) for listing in written]
        if not declaring:
            raise ValueError(undeclared)
        if row.set:
            raise ValueError(f"the set of {row.field} is written outside its block headers")
        return [
            _inserted(_first_component(x).line, _first_component(x).column, f"{value} @ ")
            for x in declaring
        ]
    if value not in ROLE_CHOICES:
        raise ValueError(f"{value!r} is no role word of the language")
    written = [listing for listing in declaring if listing.role is not None]
    state = ROLE_CHOICES[0]
    if written:
        word = "!" + value if value == state else value
        return [_replaced(listing.role, word) for listing in written]
    if row.role == state and value == state:
        return []
    if not declaring:
        raise ValueError(undeclared)
    if row.role != state:
        raise ValueError(f"the role of {row.field} is written outside its block headers")
    return [_inserted(x.at.end_line, x.at.end_column, f" @ {value}") for x in declaring]


def _added_field(groups, change: dict) -> list:
    """The edits of the box `add field` (rule 4, T-R6): the declaration
    `field : set @ !role`, the set or the word left out where not given,
    written into each side the group's targets hold for the role's class,
    in one edit: the side of a table of one group or of a branch's group,
    and in the group `ALL_BRANCHES` the side of every branch (AMD-MI-002
    §5 rule 2, A2-D12); a decision state's name is also listed on the
    inputs of the block joining `dcsn` and `cntn` (AAS, L-D1). A field the
    table already lists at the group's perch is declared where the file
    holds it and is written nowhere else (rule 2)."""
    key = (change.get("perch"), change.get("branch"))
    group = next((g for g in groups if (g.perch, g.branch) == key), None)
    if group is None:
        raise ValueError("the table has no group of that perch and branch")
    field = (change.get("field") or "").strip()
    if not field:
        raise ValueError("the field's name is empty")
    rows = [row for g in groups if g.perch == group.perch for row in g.rows]
    held = next((row for row in rows if field in (row.field, row.stem)), None)
    if held is not None:
        place = f"on line {held.line}" if held.line else "in the file"
        raise ValueError(f"{field} is already declared {place}")
    role = change.get("role") or ROLE_CHOICES[0]
    targets = group.targets.get(ROLE_CLASS.get(_ROLE_OF_WORD.get(role)))
    if not targets:
        raise ValueError(f"no header of this stage takes a field of the role {role} here")
    written = (change.get("set") or "").strip()
    parts = ([written] if written else []) + ([] if role == ROLE_CHOICES[0] else [role])
    return [
        edit
        for target in targets
        for edit in _declaration_edits(target, field, parts, group.perch)
    ]


def _declaration_edits(target: Target, field: str, parts: list, perch: str) -> list:
    """The edits that write the declaration of `field` with its typing
    `parts`, its set and its role word, into the side `target` (T-R6):
    after the side's last field, inside the parentheses of an empty side,
    and around a bare side, which the same edit parenthesizes. On a bare
    side the declaration ends with the table's perch word `perch`, `!dcsn`
    on the decision table, because the parenthesized side writes no perch
    word of its own. A side that takes the name alone (AAS, L-D1) is
    written `field`, with no set and no role word, the side's perch word
    standing for it, and nothing where the side already lists `field`."""
    if target.name_alone:
        if field in target.names:
            return []
        parts = []
    declaration = field + (" : " + " @ ".join(parts) if parts else "")
    if target.last is None:
        return [_inserted(target.at.line, target.at.column + 1, declaration)]
    if target.bare:
        declaration = field + " : " + " @ ".join([*parts, "!" + perch])
        return [
            _inserted(target.at.line, target.at.column, "("),
            _inserted(target.at.end_line, target.at.end_column, f", {declaration})"),
        ]
    return [_inserted(target.last.end_line, target.last.end_column, f", {declaration}")]


# The one file of the Unicode shortcuts of the VS Code extension (rule 6),
# beside this package in the checkout the editable install reads.
SNIPPETS = (
    Path(__file__).resolve().parents[3] / "editor" / "dynspec-vscode" / "snippets" / "dynspec.json"
)


def unicode_shortcuts(path: Path = SNIPPETS) -> dict[str, str]:
    """The Unicode shortcuts of the VS Code extension, read from its
    snippets file `path`: each entry's prefix, `\\Reals`, mapped to its
    body, `ℝ`, in the file's order. A prefix written as a list maps each of
    its strings, and a body written as a list of lines is joined by
    newlines, as VS Code reads them. A file that is absent, as in an
    install that is not editable, gives no shortcut."""
    try:
        snippets = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    table = {}
    for snippet in snippets.values():
        body = snippet["body"]
        body = "\n".join(body) if isinstance(body, list) else body
        prefixes = snippet["prefix"]
        for prefix in prefixes if isinstance(prefixes, list) else [prefixes]:
            table[prefix] = body
    return table
