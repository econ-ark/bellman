"""Creating a model folder from templates of the application corpus, for
Bellman Workbench (model interface specification 0.3, §4 and §3.3); the
module imports no Solara.

The templates of a stage are stage files of the corpus, each with the
companion files its application binds it with, read from that
application's own trellis file or recipe by the package's readers,
`load_trellis` and `load_recipe` (D6: the corpus is the only source of
templates, every application offers "open as template", and no separate
gallery is kept). `template_entries` reads each of the eight stage files
that `TEMPLATE_SOURCES` lists, chosen once by ruling C-R4 of unit C's plan,
apart from the others, as its template or, where the package refuses a
file, as a `RefusedTemplate` with the package's sentence and rule, each
read again only when its files change; `stage_templates` offers those the
package reads (unit L, Task 13; defect 1 of the UX simulation). The
recipe, the period file and the trellis file of a new folder are written
in the form of the three files of applications/pension-retirement/
declaration/, with the new model's names, each stage's file named in its
row by its path from the recipe's folder, `stages/<stage>/<stage>.bl`,
every binding the slot `$<stage>_<kind>` and every connector mapping
empty; answers.yml records the form's answers and the entries it holds
required.

`checklist` lists the connectors answers.yml holds required that the
folder's files leave empty, and the entries answers.yml records for the
author to check, each at its file, its structural address, its line and
its column, apart from the factory's refusals (§4); an unsaved text given
for a file is read in its place (spec 0.4 §3.3). A slot of the recipe is
no entry of it: a slot is a parameter of the load, bound by the keyword of
`load_recipe` that spells its name (unit K's decision K-D29).

`create_trellis` writes a new model folder in the one layout of a model
folder under a parent folder, which is neither a model folder nor inside
one, and with no stage where none is chosen (unit L, Task 13): the files
the factory reads in the
factory's folder `declaration/` (`model.FACTORY_FOLDER`), each stage in a
folder of its own, `stages/<key>/`, with its stage file and its methods
file; answers.yml, the .gitignore and README.md at the folder's top. A
template is copied under its key, its stage file's `@stage:` line and its
methods file's `stage:` naming that key, and a stage the form marks for
the terminal period stands in that period alone, which the trellis file
then writes out (unit K, Task 12). `brought_files` names the files a
template brings by their paths from its folder, as the forms list them.
Where no repository holds the parent, it makes the folder a repository
with its push destination; it commits nothing (§4: the first commit is
offered and not made).

`create_variant` writes a second trellis of a folder's model beside the
first (§4, new variant; rule 4 of the layout): in the factory's folder, a
copy of a recipe, `spec.<name>.yml`, of the trellis file it names,
`trellis.<name>.yml`, and of each period file that trellis file names,
`period.<name>.yml`, each line that names the next file written anew as
text (`replace_entry` of `bellman.trellis`, a quoted value keeping its
quotes) and every other character kept; `variant_sources` answers the
files it copies, and `registry_sources` the sources of the recipe's
`registry` block, which the copy keeps and the form names (unit L, Task
13).

`add_stage` and `add_period` copy one more stage, or write one more
period, into a folder that holds a recipe in the factory's folder with the
trellis file it names, the recipe the Workbench shows (spec 0.4 §3.5,
§3.6): each edits the recipe, a period file or the trellis file, and
answers.yml where the folder holds it, as text (`append_to_mapping` and
`append_to_sequence` of `bellman.trellis`), so that their comments and
layout are kept (§3.2), each existing file read from the mapping of
unsaved texts where it holds the file and from disk otherwise. Neither
writes a file: each answers an `Added`, the new files with their texts and
the edited texts of the existing files, which the Workbench writes to disk
and types into their buffers once every edit has been checked (ruling
J-P5). `can_add`, `recipe_keys` and `period_files` read the recipe shown
and the texts in the same way.

`folder_template` reads a stage folder of the disk, a folder that holds one
stage file, another project's `declaration/stages/<key>/` included, or that
file itself, as a template of the corpus is read (unit K's decision K-D26):
the stage file with the calibration, settings and methods files of the same
folder, which `add_stage` copies as it copies a template's, answers.yml then
recording the folder's path as the author gave it and the SHA-256 of each
file the stage brings in place of a template's id.

`library_folders` and `library_templates` read the library of stages, a
folder outside every project that the environment variable
`BELLMAN_STAGE_LIBRARY` names, or several joined by the path separator,
else `~/.bellman/library/` where that folder exists (AAS, L-D6; the issue
stage-library-and-import-from-other-folders.md, its form 2): each folder of
a library that holds one stage file is a stage of the library, read by
`folder_template` as a stage folder of the disk is read, keyed by the
folder's name and titled by its README.md where one stands. A stage of the
library is copied as such a folder is, and nothing in the library is
written.

`add_period` adds a period between two periods as well as at the earliest
end (spec 0.4 §3.6): it splits the entry with `repeat: n` that writes both
neighbors (`split_entry`), places the new entry (`insert_in_sequence`),
gives the two new pairs their inter-period mappings or expands one
standing mapping to one for each pair, raises by one the recipe's ranges
and range keys at or above the new index, widens the range of a stage
chosen for the new period (`range_widened`), splits answers.yml's entry
and renumbers its required connectors, records there an expansion and the
ranges and range keys it changed, and answers the text for the
restriction's input. While answers.yml records an expansion, `checklist`
lists each mapping of the list that differs from the others (decision 39;
J-D23), and while it records a range or a range key changed, `checklist`
names it (spec 0.4 §3.6).

`new_stage` and `new_source_file` answer the files of the author's own
(unit K's decision K-D7): a stage key's empty stage file,
`stages/<key>/<key>.bl` holding the stage's line and the four block headers
of the page Stages with no field, each block's body the equation `0 = 0`,
the smallest the grammar admits (unit L, Task 17), with the stage's row
added to the recipe as `add_stage` adds one; and the empty calibration,
settings or methods file of a stage at the folder's conventional place
(`source_path`), which
`New file` of the Recipe tab writes and names in a slot's place (design
pass 9 §3).

`remove_stage` and `remove_period` are the inverses of `add_stage` and
`add_period` (unit L, Task 25; AAS, L-D18): a stage's row, its key in
every period's list and answers.yml's records of it taken out, or a
period's entry taken out with the recipe's ranges lowered, each answered as
an `Added` whose `deleted` lists the stage's folder, the files only its row
named and the period file only its entry named, which the Workbench deletes
from disk when the files that named them are saved. `named_files` reads
every file the folder's recipes, trellis files and period files name, the
variants' among them, so that `deletable` and `removable_files` never
offer a file another row or entry names.

`record_stages`, `add_record_stage` and `add_record_period` grow a trellis
file that writes its stages as records and is read with no recipe, as
applications/cons-port/declaration/trellis.port-cons-vfi.yml is (spec 0.4
§3.5): the keys any period writes as records; a folder stage added to a
period as a copy of the record another period writes for it, as the file
writes it; and a period added as an inline entry whose `stages` are the
text of a neighbor's and whose `connectors` is one empty mapping, at the
earliest end or between two periods as `add_period` adds one. Each edits
the text of the trellis file alone and answers an `Added`; no recipe and
no answers.yml is read or written.

`write_notebook` writes, where none exists, the notebook of a model folder
beside its `declaration/`, `notebooks/<folder>.ipynb` (`notebook_file`),
from the template `NOTEBOOK_TEMPLATE`: its first cell reads the folder's
source of a trellis, a recipe or a trellis file, by its path from
`notebooks/`, and the others print what that trellis holds when the
notebook is run (model interface specification 0.4, §5.9).
"""

from __future__ import annotations

import copy
import functools
import hashlib
import json
import os
import posixpath
import re
import shutil
import tempfile
from pathlib import Path
from typing import NamedTuple

import yaml

from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import (
    append_to_mapping,
    append_to_sequence,
    entry_span,
    entry_value,
    insert_in_sequence,
    load_recipe,
    load_trellis,
    period_entries,
    remove_from_mapping,
    remove_from_sequence,
    replace_entry,
    split_entry,
    written_at,
)
from bellman_workbench import model
from bellman_workbench.model import FACTORY_FOLDER, RECIPE, factory_path

__all__ = [
    "CORPUS",
    "TEMPLATE_SOURCES",
    "KINDS",
    "FACTORY_FOLDER",
    "RECIPE",
    "PERIOD",
    "TRELLIS",
    "ANSWERS",
    "STAGE_METHODS",
    "GITIGNORE",
    "factory_path",
    "stage_folder",
    "stage_file",
    "companion_path",
    "StageTemplate",
    "RefusedTemplate",
    "template_entries",
    "stage_templates",
    "template_of",
    "folder_template",
    "LIBRARY_VARIABLE",
    "library_folders",
    "library_templates",
    "brought_files",
    "slot_name",
    "recipe_row",
    "recipe_text",
    "period_text",
    "trellis_text",
    "answers_text",
    "readme_text",
    "STAGE_BLOCKS",
    "empty_stage_text",
    "source_path",
    "empty_source_text",
    "ChecklistEntry",
    "checklist",
    "Created",
    "create_trellis",
    "variant_sources",
    "create_variant",
    "registry_sources",
    "can_add",
    "period_files",
    "recipe_keys",
    "Added",
    "add_stage",
    "new_stage",
    "new_source_file",
    "add_period",
    "range_widened",
    "DELETED_ON_SAVE",
    "named_files",
    "deletable",
    "removable_files",
    "deletion_names",
    "without_stage",
    "remove_stage",
    "remove_period",
    "record_stages",
    "add_record_stage",
    "add_record_period",
    "NOTEBOOK_TEMPLATE",
    "notebook_file",
    "write_notebook",
]

# The application corpus, the one source of templates (D6), in the checkout
# the Workbench is installed from editable (D15); this module stands at
# packages/bellman-workbench/bellman_workbench/creation.py.
CORPUS = Path(__file__).resolve().parents[3] / "applications"

# The corpus files the templates of a stage are read from, each with the
# stage keys it binds, chosen once (1 October 2026) and brought to the one
# cons-port folder on 28 October 2026: the three stage files of the
# portfolio-consumption model that its recipe spec.port-cons.yml binds, and
# the stage without a portfolio choice that its reference trellis file
# binds, each with the calibration, settings and methods files of
# applications/cons-port/declaration/; and the four stage files of the
# pension model, applications/pension-retirement/, whose recipe binds each
# stage's own methods file, followed by a methods slot for each stage but
# the terminal one, and the calibration of the two saving stages by the
# slot `$fill` alone.
TEMPLATE_SOURCES = (
    ("cons-port/declaration/spec.port-cons.yml", ("port", "cons", "disc")),
    ("cons-port/declaration/trellis.reference-cons-only.yml", ("noport",)),
    (
        "pension-retirement/declaration/spec.yml",
        ("worker_saving", "retire_choice", "retiree_saving", "terminal"),
    ),
)

# the three binding kinds, in the order a row of the recipe writes them
KINDS = ("calibration", "settings", "methods")

# The factory's folder of a model folder, `FACTORY_FOLDER`, `declaration/`,
# the recipe's name in it, `RECIPE`, and `factory_path` are `model`'s,
# imported above, so that the Workbench's binding reads the recipe where
# this module writes it (merge note M8 of unit C). Beside the recipe, that
# folder of a new folder holds the period file and the trellis file of the
# factory's layout (§3.3); the new folder's top holds the form's own record
# of its answers (§4).
PERIOD = "period.yml"
TRELLIS = "trellis.yml"
ANSWERS = "answers.yml"
# the name of a stage's methods file in the stage's folder, `stages/<key>/`
STAGE_METHODS = "methods.yml"

# The four blocks of an empty stage file (K-D7), each as its id and the
# perch words of its two sides, in the order in which the page Stages
# (docs/Bellman-Sym/01-stage.md §4) writes them: the two forward blocks,
# then the two backward blocks. The policy block, which a stage without a
# choice does not write, is left to the author.
STAGE_BLOCKS = (
    ("arvl_to_dcsn", "arvl", "dcsn"),
    ("dcsn_to_cntn", "dcsn", "cntn"),
    ("cntn_to_dcsn", "cntn", "dcsn"),
    ("dcsn_to_arvl", "dcsn", "arvl"),
)

# the .gitignore of a new folder: the generated views and the per-user
# state of the Workbench, which git ignores (§4, §10)
GITIGNORE = (
    "# the generated views and the per-user state of Bellman Workbench\n"
    "model-explorer/\n"
    ".bellman/\n"
)


def stage_folder(key: str) -> str:
    """The folder of the stage `key`, `stages/<key>`, by its posix path from
    the factory's folder; it holds the stage's file and the methods file
    its template brings (the one layout of a model folder)."""
    return posixpath.join("stages", key)


def stage_file(key: str) -> str:
    """The file of the stage `key` by its posix path from the factory's
    folder, `stages/<key>/<key>.bl`, in the stage's folder; the recipe's row
    names it so under `stage:`."""
    return posixpath.join(stage_folder(key), f"{key}.bl")


def companion_path(key: str, kind: str, source: Path) -> str:
    """The path, relative to the model folder, that the companion file
    `source` of the binding `kind` of a template is copied to for the stage
    `key`: a methods file into the stage's folder as `methods.yml`,
    `declaration/stages/<key>/methods.yml`, and a calibration or a settings
    file under its own name into the folder of its kind,
    `declaration/<kind>/<file name>`."""
    if kind == "methods":
        return factory_path(posixpath.join(stage_folder(key), STAGE_METHODS))
    return factory_path(posixpath.join(kind, source.name))


class StageTemplate(NamedTuple):
    """One template of a stage: `id`, `<corpus file>#<key>`, the file it
    is read from and the stage key it binds there; `key`, the key it
    proposes; `stage`, the stage file; `model`, the title of its model's
    page, `economics.md` or `README.md` of the application the corpus file
    stands in; `calibration`, the names of the parameters the stage
    declares, which its calibration must give; `companions`, for each
    kind of `KINDS`, the files its application binds it with, in the order
    bound, none for a binding the application leaves to a slot; and
    `origin`, for the template of a stage folder of the disk
    (`folder_template`), the path the author gave, which is also its `id`,
    and None for a template of the corpus."""

    id: str
    key: str
    stage: Path
    model: str
    calibration: tuple[str, ...]
    companions: dict
    origin: str | None = None


class RefusedTemplate(NamedTuple):
    """An entry of `TEMPLATE_SOURCES` whose template the package refuses
    (unit L, Task 13; defect 1 of the UX simulation): `id`, `<corpus
    file>#<key>`, as a template's id; `key`, the stage key the entry binds;
    `file`, the file refused, the entry's stage file, or the corpus file
    itself where the package refuses that file; `sentence`, the package's
    sentence; and `rule`, the rule the refusal names, None where it names
    none."""

    id: str
    key: str
    file: Path
    sentence: str
    rule: str | None


def template_entries() -> tuple[StageTemplate | RefusedTemplate, ...]:
    """Each entry of `TEMPLATE_SOURCES`, in its order, as the template of the
    stage it binds or as the refusal of that template (unit L, Task 13;
    defect 1 of the UX simulation): each corpus file read by the package's
    reader, a recipe by `load_recipe` and a trellis file by `load_trellis`,
    each key's record taken from the first period that holds it, and the
    stage file the record names elaborated. A file the package refuses
    refuses its own entries alone, each with the package's sentence and its
    rule, and the other entries are offered; so does a file whose reading
    raises an exception of no class of the package's refusals, as the
    KeyError of an unresolved semantic input (`_refused`; unit L's final
    judgment, §6 item 7). A corpus file is read once for
    each state of the files of its folder (`_corpus_records`), and an
    entry's stage file once for each state of the files of the stage's
    folder (`_corpus_entry`), so that a file written correct is read again
    at the next reading with no restart, and an entry whose files are
    unchanged is answered as the same object. A checkout that holds no
    corpus is refused with a ValueError that names where the corpus was
    looked for."""
    if not CORPUS.is_dir():
        raise ValueError(f"the application corpus is not at {CORPUS}")
    found = []
    for source, keys in TEMPLATE_SOURCES:
        path = CORPUS / source
        title = _model_title(CORPUS / source.split("/")[0])
        try:
            records = _corpus_records(str(path), _folder_state(path.parent))
        except Exception as error:  # a refusal, a disk error or another exception
            found += [_refused(f"{source}#{key}", key, path, error) for key in keys]
            continue
        for key in keys:
            if key not in records:
                missing = ValueError(f"{source} binds no stage {key}")
                found.append(_refused(f"{source}#{key}", key, path, missing))
                continue
            stage, companions = records[key]
            state = _folder_state(Path(stage).parent)
            found.append(_corpus_entry(source, key, stage, companions, title, state))
    return tuple(found)


def stage_templates() -> tuple[StageTemplate, ...]:
    """The templates of a stage the corpus offers: the entries of
    `template_entries` whose stage the package reads, in the order of
    `TEMPLATE_SOURCES`, an entry it refuses left out (unit L, Task 13). A
    checkout that holds no corpus is refused as `template_entries` refuses
    it."""
    return tuple(entry for entry in template_entries() if isinstance(entry, StageTemplate))


# The most readings that each cache of the corpus's and the library's files
# keeps (`_corpus_records`, `_corpus_entry`, `_library_template`): a reading
# is kept under the state of its files, so that each edit of a file adds one,
# and the readings least recently used beyond this number are dropped (unit
# L's final judgment, §6 item 12).
READINGS_KEPT = 128


@functools.lru_cache(maxsize=READINGS_KEPT)
def _corpus_records(path: str, state: tuple) -> dict:
    """The stage file and the companions of each stage key of the corpus
    file `path`, a recipe or a trellis file, read by the package's reader:
    for each key, from the first period that holds it, the stage file's
    resolved path as a string and, for each kind of `KINDS`, the files the
    file binds the stage with, in the order bound, a pair (kind, paths).
    Read once for each `state` of the files of the corpus file's folder
    (`_folder_state`); a file the reader refuses raises the reader's error,
    which is not kept, so that it is read again at the next reading."""
    file = Path(path)
    # a recipe is the folder's `spec.yml` or a variant `spec.<name>.yml`, as `model._role` reads a name
    read = load_recipe(file.parent, file.name) if model._role(Path(file.name)) == "recipe" else load_trellis(file)
    records = {}
    for period in read["periods"]:
        for key, record in period["stages"].items():
            if key in records:
                continue
            lists = record["provenance"]["source_lists"]
            companions = tuple(
                (
                    kind,
                    tuple(Path(each["path"]).resolve() for each in lists[kind] if "path" in each),
                )
                for kind in KINDS
            )
            records[key] = (str(Path(record["stage"]["origin"]).resolve()), companions)
    return records


@functools.lru_cache(maxsize=READINGS_KEPT)
def _corpus_entry(
    source: str, key: str, stage: str, companions: tuple, title: str, state: tuple
) -> StageTemplate | RefusedTemplate:
    """The template of the stage `key` that the corpus file `source` binds,
    its stage file `stage`, its companions `companions`, pairs (kind,
    paths), and its model's title `title`, with the parameters its stage
    file declares, which the package's elaboration of the file answers; or
    its refusal where the package refuses the stage file. Read once for each
    `state` of the files of the stage file's folder (`_folder_state`), which
    the cache's key holds."""
    template_id = f"{source}#{key}"
    try:
        declared = tuple(elaborate_stage(load_stage(stage)).par.keys())
    except Exception as error:  # a refusal, a disk error or another exception
        return _refused(template_id, key, Path(stage), error)
    return StageTemplate(template_id, key, Path(stage), title, declared, dict(companions))


def _refused(template_id: str, key: str, file: Path, error: Exception) -> RefusedTemplate:
    """The refusal of the template `template_id` of the stage `key` by the
    error `error` of the package or of the disk at the file `file`: the
    error's sentence and the rule a refusal of the package names
    (`ConstructionError.rule`, `FactoryError.rule`), None for another
    refusal or an error of the disk; an exception of no class of the
    package's refusals (`model.is_refusal`), as a KeyError, as Python
    prints it under the rule `package-exception`, as the loop lists it
    (`model.exception_diagnostic`; unit L's final judgment, §6 item 7)."""
    if not isinstance(error, OSError) and not model.is_refusal(error):
        sentence = model.exception_diagnostic(error, None).message
        return RefusedTemplate(template_id, key, file.resolve(), sentence, model.EXCEPTION_RULE)
    rule = getattr(error, "rule", None)
    return RefusedTemplate(template_id, key, file.resolve(), str(error), rule)


def _model_title(application: Path) -> str:
    """The `title` of the front matter of an application's page,
    economics.md, else README.md; the folder's name where neither has
    one. A page that cannot be read, or whose front matter does not read
    as a YAML mapping, as another project's README may hold, has no title
    (unit K's final judgment, §6 item 1)."""
    for page in (application / "economics.md", application / "README.md"):
        if not page.is_file():
            continue
        try:
            text = page.read_text(encoding="utf-8")
            end = text.find("\n---", 4)
            front = yaml.safe_load(text[4:end]) if text.startswith("---\n") and end != -1 else None
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        title = front.get("title") if isinstance(front, dict) else None
        if title:
            return str(title)
    return application.name


def template_of(template_id: str) -> StageTemplate:
    """The template of a stage whose id is `template_id`; another id is
    refused with a ValueError that names it."""
    for template in stage_templates():
        if template.id == template_id:
            return template
    raise ValueError(f"no template of a stage is named {template_id!r}")


# the suffixes of the YAML files of a stage folder of the disk among which
# `folder_template` finds its calibration, settings and methods files
_YAML_SUFFIXES = (".yml", ".yaml")


def folder_template(path: str) -> StageTemplate:
    """The template of a stage copied from a folder of the disk (unit K's
    decision K-D26; the plan of unit K, Task 25), read as `stage_templates`
    reads a template of the corpus. `path`, as the author gives it, a full
    path or one from `~`, names a stage folder, a folder that holds one
    stage file `<name>.bl`, another project's `declaration/stages/<key>/`
    included, or that stage file itself. The template's `id` and `origin`
    are `path` as given; `key`, the name of the folder that holds the stage
    file; `stage`, that file; `model`, the title of the model folder
    (`_model_title`) where the stage's folder stands at
    `<model folder>/declaration/stages/<key>/`, else the title
    `_model_title` reads from the stage's folder itself, its README.md where
    one stands, as a stage of the library is titled (AAS, L-D6), and the
    folder's name where none gives one; `calibration`, the names of the
    parameters the stage declares; and `companions`, for each kind of
    `KINDS`, the YAML files of the same folder whose one top key among
    `KINDS` names that kind, as the factory tells a source file's kind
    (`_source_kind`), in name order. Refused with
    a ValueError: a path that is not full; a path that names nothing, or a
    file that is no `.bl` file; a folder that holds no `.bl` file, or
    several; a folder that holds more than one methods file, since a stage's
    folder holds one; and a stage file the package refuses, in the
    package's sentence."""
    given = Path(path).expanduser()
    if not given.is_absolute():
        raise ValueError(f"{path} is no full path: write it from / or from ~")
    if given.is_file():
        if given.suffix != ".bl":
            raise ValueError(f"{path} is no .bl file")
        stage = given.resolve()
    elif given.is_dir():
        found = sorted(
            entry
            for entry in given.iterdir()
            if entry.is_file() and entry.suffix == ".bl" and not entry.name.startswith(".")
        )
        if not found:
            raise ValueError(f"{path} holds no .bl file")
        if len(found) > 1:
            names = _listed([entry.name for entry in found])
            raise ValueError(
                f"{path} holds {len(found)} .bl files, {names}: give the path of the one to copy"
            )
        stage = found[0].resolve()
    else:
        raise ValueError(f"{path} does not exist")
    folder = stage.parent
    sources = sorted(
        entry
        for entry in folder.iterdir()
        if entry.is_file() and entry.suffix in _YAML_SUFFIXES and not entry.name.startswith(".")
    )
    kinds = {entry: _source_kind(entry) for entry in sources}
    companions = {kind: tuple(e for e in sources if kinds[e] == kind) for kind in KINDS}
    if len(companions["methods"]) > 1:
        names = _listed([entry.name for entry in companions["methods"]])
        raise ValueError(
            f"{path} holds {len(companions['methods'])} methods files, {names}, and a stage "
            "brings one"
        )
    in_layout = folder.parent.name == "stages" and folder.parents[1].name == FACTORY_FOLDER
    model = _model_title(folder.parents[2] if in_layout else folder)
    declared = tuple(elaborate_stage(load_stage(str(stage))).par.keys())
    return StageTemplate(path, folder.name, stage, model, declared, companions, path)


# The environment variable that names the library of stages, one folder or
# several joined by the path separator (AAS, L-D6), and the library's folder
# under the home folder where that variable is unset or empty.
LIBRARY_VARIABLE = "BELLMAN_STAGE_LIBRARY"
_LIBRARY_AT_HOME = (".bellman", "library")


def library_folders() -> tuple[Path, ...]:
    """The folders of the library of stages (AAS, L-D6; the issue
    stage-library-and-import-from-other-folders.md, its form 2), in the
    order named: the paths `LIBRARY_VARIABLE` names, joined by the path
    separator `os.pathsep`, each read without the spaces around it and from
    `~`, the home folder; where the variable is unset or empty,
    `~/.bellman/library/`. A path that is not full, that names no folder, or
    that names a folder named before, is left out, so that a library that
    does not exist gives no folder and no refusal. Nothing is written."""
    named = os.environ.get(LIBRARY_VARIABLE, "")
    if named.strip():
        given = [Path(part.strip()).expanduser() for part in named.split(os.pathsep)]
    else:
        given = [Path.home().joinpath(*_LIBRARY_AT_HOME)]
    found = []
    for folder in given:
        if folder.is_absolute() and folder.is_dir() and folder not in found:
            found.append(folder)
    return tuple(found)


def library_templates() -> tuple[StageTemplate, ...]:
    """The stages of the library (AAS, L-D6), in the order of
    `library_folders` and, within a folder of the library, of the names of
    its folders: each folder of the library that holds one stage file
    `<name>.bl`, read by `folder_template` from its full path, which is the
    template's `id` and its `origin`, so that `add_stage` copies it and
    answers.yml records its origin as for any stage folder of the disk; its
    key is the folder's name and its title the `title` of its README.md
    where one stands. A folder whose name begins with ".", a folder that
    holds no stage file or several, and a stage folder that `folder_template`
    refuses, are left out, so that one such folder hides no other stage. A
    folder is read again when a file in it changes (`_library_template`).
    Nothing in the library is written."""
    found = []
    for library in library_folders():
        try:
            folders = sorted(
                entry
                for entry in library.iterdir()
                if entry.is_dir() and not entry.name.startswith(".")
            )
        except OSError:
            continue
        for folder in folders:
            state = _folder_state(folder)
            stages = [name for name, _, _ in state if name.endswith(".bl")]
            if len(stages) == 1:
                template = _library_template(str(folder), state)
                if template is not None:
                    found.append(template)
    return tuple(found)


def _folder_state(folder: Path) -> tuple:
    """The name, the time of the last change in nanoseconds and the size in
    bytes of each file of `folder` whose name does not begin with ".", in
    the order of the names; none for a folder that cannot be read."""
    try:
        files = sorted(
            entry
            for entry in folder.iterdir()
            if entry.is_file() and not entry.name.startswith(".")
        )
        return tuple(
            (entry.name, entry.stat().st_mtime_ns, entry.stat().st_size) for entry in files
        )
    except OSError:
        return ()


@functools.lru_cache(maxsize=READINGS_KEPT)
def _library_template(path: str, state: tuple) -> StageTemplate | None:
    """The template `folder_template` reads from the stage folder of the
    library at `path`, None where it refuses the folder; read once for each
    `state` of the folder's files (`_folder_state`), so that the library's
    stages are elaborated again only after a file of theirs changes."""
    try:
        return folder_template(path)
    except (OSError, ValueError):
        return None


def _source_kind(path: Path) -> str | None:
    """The kind of the YAML file `path` among `KINDS`, the one top key of
    `KINDS` it writes, as the factory tells a source file's kind by its top
    key: `methods` for a methods file, which also writes `stage:`; None for
    a file that cannot be read as a YAML mapping, by the package's reader of
    YAML text (`entry_value`), or whose top keys name no kind or two."""
    try:
        document = entry_value(_source_text(path))
    except (OSError, UnicodeDecodeError, ValueError, KeyError):
        return None
    named = [kind for kind in KINDS if isinstance(document, dict) and kind in document]
    return named[0] if len(named) == 1 else None


def brought_files(template: StageTemplate) -> tuple[str, ...]:
    """The files the template `template` brings, its companions in the
    order of `KINDS`, each by its posix path from the template's folder,
    the folder of the corpus file it is read from, as that file names it:
    `calibration/portfolio.yml`, or for a file of another application
    `../../portfolio-choice/declaration/stages/disc/methods.yml` (unit K,
    Task 12; the usability walkthrough §4 item 20); for a stage folder of
    the disk, the folder that holds the stage file, `methods.yml` (unit K's
    decision K-D26). The forms that list the templates print them under
    each one."""
    if template.origin is not None:
        folder = template.stage.parent
    else:
        folder = (CORPUS / template.id.partition("#")[0]).parent
    return tuple(
        Path(os.path.relpath(path, folder)).as_posix()
        for kind in KINDS
        for path in template.companions[kind]
    )


def slot_name(key: str, kind: str) -> str:
    """The name of the slot of the binding `kind` of the stage `key`,
    `cons_calibration`, written `$cons_calibration` in the recipe."""
    return f"{key}_{kind}"


def recipe_row(key: str) -> str:
    """The row of the stage `key` in the recipe, in flow style as
    applications/pension-retirement/declaration/spec.yml writes its rows:
    first the stage's file under `stage:`, `stages/<key>/<key>.bl`
    (`stage_file`), its path from the recipe's folder, then each binding of
    `KINDS` the list of its one slot."""
    bindings = ", ".join(f"{kind}: {{all: [${slot_name(key, kind)}]}}" for kind in KINDS)
    # the recipe stands in the factory's folder, so the stage's file is
    # written by its path from that folder, not built by factory_path
    return f"{{stage: {stage_file(key)}, {bindings}}}"


def recipe_text(name: str, keys) -> str:
    """The recipe of the new folder `name`: three comment lines, each
    within 79 characters for a folder name of up to 32 characters, which
    say that the recipe names the trellis file and each stage's file by
    their paths from its folder and that each binding is a slot until the
    name of a file replaces it, a file of calibration/ or settings/ or the
    stage's methods file in the stage's folder, stages/<stage>/methods; the
    trellis file it is read against, `trellis: trellis.yml`, by its path
    from the recipe's folder; and one row per stage key (`recipe_row`),
    which names the stage's file by its path from the same folder, or, with
    no key, the empty mapping `stages: {}` in flow style, to which "new
    stage" adds a row as text (unit L, Task 13)."""
    rows = "".join(f"  {key}: {recipe_row(key)}\n" for key in keys)
    return (
        f"# The recipe of {name}: the trellis and stage files,\n"
        "# by their paths from this folder. A binding is the slot $<stage>_<kind> until\n"
        "# a file of calibration/ or settings/, or stages/<stage>/methods, replaces it.\n"
        f"trellis: {TRELLIS}\n" + (f"stages:\n{rows}" if rows else "stages: {}\n")
    )


def period_text(label: str, keys) -> str:
    """A period file in the form of applications/pension-retirement/
    declaration/period.yml: the period `label`, its stage keys, or with no
    key the empty list `stages: []` in flow style (unit L, Task 13), and
    one empty connector mapping."""
    stages = "".join(f"  - {key}\n" for key in keys)
    return (
        "!period\n"
        f"name: {label}\n"
        "# The stages of one period; the order in which they are computed is read\n"
        "# from their fields, not from this list. A connector, {continuation field:\n"
        "# arrival field}, joins two fields of different names: type it in place of\n"
        "# the empty mapping below.\n"
        + (f"stages:\n{stages}" if stages else "stages: []\n")
        + "connectors:\n"
        "  - {}\n"
    )


def trellis_text(name: str, repeat: int, terminal=()) -> str:
    """A trellis file in the form of applications/pension-retirement/
    declaration/trellis.yml: the trellis `name`, the period of period.yml
    repeated `repeat` times, and one empty inter-period mapping, which
    stands for every adjacent pair.

    Where `terminal` names stage keys, two or more periods being written
    (unit K, Task 12; the usability walkthrough §4 item 7), the terminal
    period is written out in the form of applications/durables/
    declaration/trellis.yml, its `stages` the keys `terminal` and its
    connectors one empty mapping, and period.yml is repeated `repeat - 1`
    times before it, so that `repeat` counts the periods either way."""
    if terminal:
        periods = (
            f"  - stages: [{', '.join(terminal)}]\n"
            "    connectors:\n"
            "      - {}\n"
            f"  - {{template: {PERIOD}, repeat: {repeat - 1}}}\n"
        )
        written_out = (
            "# The terminal period is written out with a list of stages of its own,\n"
            "# which a stage added to period.yml does not reach. The periods before it\n"
            "# repeat period.yml.\n"
        )
    else:
        periods = f"  - {{template: {PERIOD}, repeat: {repeat}}}\n"
        written_out = ""
    return (
        "!trellis\n"
        f"name: {name}\n"
        "# periods[0] is the terminal period and periods[h] lies h periods before it.\n"
        f"{written_out}"
        "periods:\n"
        f"{periods}"
        "# One mapping stands for every adjacent pair, {continuation field of a\n"
        "# period: arrival field of the period after it}: type it in place of the\n"
        "# empty mapping below.\n"
        "inter_connectors:\n"
        "  - {}\n"
    )


def answers_text(
    name: str, destination: str | None, label: str, repeat: int, stages, terminal=()
) -> str:
    """answers.yml of a new folder: the form's answers, so that a template
    updated later can be applied again, and under `required`, in the form
    of decision B-D2 of unit B's plan (C-R12), the name of each slot the
    form wrote for each stage of `stages`, pairs (key, template id), which
    the checklist does not read (unit K's decision K-D29), and the
    connectors the checklist reads, none (decision C-D1).

    answers.yml stands at the model folder's top and holds paths of two
    readings, by one rule (merge note M8 of unit C): `periods[].file` is a
    period file's name in the factory's folder, as the trellis file's
    `template:` writes it, and is read from that folder (`factory_path`);
    `required.connectors[].file` is a path from the model folder, where
    answers.yml stands, and is read from there. This function writes
    `periods[].file` by that rule, `add_period` adds its period's file by
    it, and `checklist` reads `required.connectors[].file` by it.

    `periods` records the entries of the trellis file one for one, as
    `add_period` reads them: where `terminal` names the stage keys of a
    terminal period written out (`trellis_text`; unit K, Task 12), that
    period first, `{stages: [<keys>], repeat: 1}`, which names no file, and
    then period.yml with `repeat - 1` periods. With no stage, `stages` and
    `required.slots` are written empty in flow style, `{}` and `[]`, to
    which "new stage" adds as text (unit L, Task 13)."""
    rows = "".join(
        f"  {key}: {{template: {_quoted(template_id)}}}\n" for key, template_id in stages
    )
    slots = "".join(f"    - {slot_name(key, kind)}\n" for key, _ in stages for kind in KINDS)
    if terminal:
        periods = (
            f"  - {{stages: [{', '.join(terminal)}], repeat: 1}}\n"
            f"  - {{label: {label}, file: {PERIOD}, repeat: {repeat - 1}}}\n"
        )
    else:
        periods = f"  - {{label: {label}, file: {PERIOD}, repeat: {repeat}}}\n"
    return (
        '# The answers of the form "new trellis" of Bellman Workbench, kept so that\n'
        "# a template updated later can be applied again; `required` lists the\n"
        "# slots the form wrote and the connectors the Workbench's checklist reads.\n"
        f"name: {_quoted(name)}\n"
        f"destination: {_quoted(destination)}\n"
        "periods:\n"
        f"{periods}"
        + (f"stages:\n{rows}" if rows else "stages: {}\n")
        + "required:\n"
        + (f"  slots:\n{slots}" if slots else "  slots: []\n")
        + "  connectors: []\n"
    )


def readme_text(name: str, keys) -> str:
    """The three-line README.md of the new folder `name` (§4), which
    stands at the folder's top and names the recipe by its path from
    there; it says that the folder was written from templates of the
    application corpus where `keys`, the stages copied, holds any, and that
    it holds no stage otherwise (unit L, Task 13)."""
    written = "from templates of the application corpus" if keys else "with no stage"
    return (
        f"# {name}\n"
        f"A model folder of Bellman-SYM, written by Bellman Workbench {written}.\n"
        f"The recipe is {factory_path(RECIPE)}; answers.yml records the answers of the "
        "form that wrote the folder.\n"
    )


# The body of each block of an empty stage file (K-D7, amended by unit L,
# Task 17; defect 7 of the UX simulation): the smallest body the grammar
# admits. A block's body holds one block item or more (the rule `_body` of
# packages/bellman/bellman/syntax/grammars/stage.lark), and the smallest
# item is a statement, an equality of two formulas, each a number at its
# smallest (the rules `statement`, `equality` and `atom`); it names no field
# and no parameter.
EMPTY_BODY = "0 = 0"


def empty_stage_text(key: str) -> str:
    """The empty stage file of the stage `key` that "new stage" writes
    (unit K's decision K-D7): the stage's line, `@stage: <key>`, and the
    four block headers of `STAGE_BLOCKS`, each with no field on either side,
    `[id=arvl_to_dcsn, () : !arvl -> () : !dcsn]`, and a body that holds
    the one statement `EMPTY_BODY`, the smallest body the grammar admits,
    since it admits no empty body (unit L, Task 17; defect 7 of the UX
    simulation). The file parses, and the package constructs it as a stage
    with no field, so that the Fields tab writes its first fields; its
    builders graphs are refused until a block declares an output."""
    blocks = "".join(
        f"[id={name}, () : !{start} -> () : !{end}] {{\n    {EMPTY_BODY}\n}}\n"
        for name, start, end in STAGE_BLOCKS
    )
    return f"@stage: {key}\n\n{blocks}"


def source_path(key: str, kind: str) -> str:
    """The path, relative to the model folder, at which the folder's layout
    places the file of the binding `kind` of the stage `key` that "new
    file" writes (K-D7): `declaration/calibration/<key>.yml`,
    `declaration/settings/<key>.yml`, or the stage's methods file in its
    folder, `declaration/stages/<key>/methods.yml`, the places to which a
    template's companions are copied (`companion_path`)."""
    return companion_path(key, kind, Path(f"{key}.yml"))


def empty_source_text(key: str, kind: str) -> str:
    """The empty file of the binding `kind` that "new file" writes for the
    stage `key` (K-D7): the one top key by which the factory tells a
    source's kind, with nothing under it, `calibration: {}` or `settings:
    {}`; a methods file also names its stage, as every methods file of the
    corpus does, since a methods file binds the stage it names (spec 0.3c
    §4.3): `stage: <key>`, then `methods: []`."""
    if kind == "methods":
        return f"stage: {key}\nmethods: []\n"
    return f"{kind}: {{}}\n"


def _quoted(value) -> str:
    """`value` as a YAML scalar written in JSON's form, a double-quoted
    string or `null`, which YAML reads as written."""
    return json.dumps(value, ensure_ascii=False)


class ChecklistEntry(NamedTuple):
    """One entry of the checklist: a connector answers.yml holds required
    that a file of the folder leaves empty (§4), or an entry answers.yml
    records for the author to check after a period is added (spec 0.4 §3.6):
    `file`, its path relative to the folder; `address`, its structural
    address in that file, `inter_connectors[0]` or `stages.port.periods`;
    `line` and `column`, where it stands, counted from one; and `sentence`,
    what is to be written or checked there."""

    file: str
    address: str
    line: int
    column: int
    sentence: str


def checklist(folder, texts=None) -> tuple[ChecklistEntry, ...]:
    """The entries of the folder `folder` that answers.yml at its top
    marks, apart from the factory's refusals (§4), read as decision B-D2 of
    unit B's plan reads them (C-R12): each connector answers.yml lists under
    `required.connectors`, `{file, address}`, that its file, read from the
    folder by the rule `answers_text` states, writes as an empty mapping. A
    slot of the recipe, `$<name>`, is no entry, required or not: it is a
    place for values supplied by the keyword of `load_recipe` that spells
    its name, and nothing is lacking where a recipe writes one (unit K's
    decision K-D29; the factory page, §3.3). A file that is not UTF-8 or
    does not read as YAML gives no entry, its refusal being the factory's to
    state. A `required.connectors` that is not a list lists no connector.
    An entry of `required.connectors` that is not
    a mapping whose `file` and `address` are strings is passed over, and so
    is one whose file lies outside the folder once resolved, symbolic links
    followed. An entry at the file, line and column of an earlier entry is
    passed over, so that each place is listed once.

    Each of answers.yml, the recipe and a required connector's file is read
    from `texts`, the mapping of unsaved texts by a file's resolved path as a
    string (spec 0.4 §3.1), where it holds that file, and from disk
    otherwise, so that a connector typed into a buffer and not saved is no
    longer counted (spec 0.4 §3.3).

    While answers.yml records that the inter-period list of the trellis
    file the recipe names was expanded from one standing mapping,
    `expanded: {inter_connectors: true}` (decision 39; J-D23), each mapping
    of that list that differs from the others is listed after them
    (`_differing_mappings`), so that a copy edited alone is seen; the
    author removes the record when the pairs are meant to differ.

    Each range and range key of a recipe that answers.yml records under
    `moved`, `{file, address}`, as changed by a period added between two
    periods (spec 0.4 §3.6, "names every range and key changed in the status
    line and the checklist"), is listed last, at the place of its value,
    with the sentence `the range <address> was changed by an added period:
    check any schedule keyed by period index`, so that the author checks
    the schedules a renumbering of periods cannot see; the author removes
    the record once they are checked. An entry of `moved` is read as one of
    `required.connectors` is, and one whose address its file no longer
    writes is passed over."""
    folder = Path(folder)
    texts = texts or {}
    connectors = []
    try:
        answers = yaml.safe_load(_unsaved_or_disk(folder / ANSWERS, texts))
    except (OSError, ValueError, yaml.YAMLError):
        answers = None
    required = answers.get("required") if isinstance(answers, dict) else None
    if isinstance(required, dict):
        listed = required.get("connectors")
        connectors = [
            item for item in (listed if isinstance(listed, list) else []) if _is_mark(item)
        ]
    try:
        text = _unsaved_or_disk(folder / factory_path(RECIPE), texts)
    except (OSError, ValueError):
        text = None
    found = []
    root = folder.resolve()
    for mark in connectors:
        try:
            path = (folder / mark["file"]).resolve()
            # a file outside the folder gives no entry, so that no path read
            # from answers.yml opens a file outside the folder
            if not path.is_relative_to(root):
                continue
            # the connector's file, read under its own name, so that `text`
            # remains the recipe's text, which `_differing_mappings` reads
            marked = _unsaved_or_disk(path, texts)
            value = entry_value(marked, mark["address"])
            span = entry_span(marked, mark["address"])
        except (OSError, RuntimeError, ValueError, KeyError):
            continue
        if isinstance(value, dict) and not value:
            found.append(
                ChecklistEntry(
                    mark["file"],
                    mark["address"],
                    span.line,
                    span.column,
                    f"the connector {mark['address']} is empty: write "
                    "{continuation field: arrival field} in it",
                )
            )
    expanded = answers.get("expanded") if isinstance(answers, dict) else None
    if (
        text is not None
        and isinstance(expanded, dict)
        and expanded.get("inter_connectors") is True
    ):
        found += _differing_mappings(folder, text, texts)
    moved = answers.get("moved") if isinstance(answers, dict) else None
    for mark in (item for item in (moved if isinstance(moved, list) else []) if _is_mark(item)):
        try:
            path = (folder / mark["file"]).resolve()
            # a file outside the folder gives no entry, as for a connector
            if not path.is_relative_to(root):
                continue
            span = entry_span(_unsaved_or_disk(path, texts), mark["address"])
        except (OSError, RuntimeError, ValueError, KeyError):
            continue
        sentence = (
            f"the range {mark['address']} was changed by an added period: check any "
            "schedule keyed by period index"
        )
        found.append(
            ChecklistEntry(mark["file"], mark["address"], span.line, span.column, sentence)
        )
    # the first entry at each place, so that the checklist block's keys,
    # file, line and column, are unique
    places = {}
    for entry in found:
        places.setdefault((entry.file, entry.line, entry.column), entry)
    return tuple(places.values())


def _is_mark(item) -> bool:
    """Whether `item`, an entry of a list of answers.yml, `required.connectors`
    or `moved`, is a mapping whose `file` and `address` are strings, the
    form in which answers.yml names an entry of a file of the folder."""
    return (
        isinstance(item, dict)
        and isinstance(item.get("file"), str)
        and isinstance(item.get("address"), str)
    )


def _differing_mappings(folder: Path, recipe: str, texts: dict) -> list[ChecklistEntry]:
    """The checklist's entries of an inter-period list expanded from one
    standing mapping (decision 39; J-D23): in the trellis file the recipe's
    text `recipe` names, read from `texts` where it holds it, each mapping
    of `inter_connectors` that differs from the most frequent one, the first
    of the most frequent in the list where two are as frequent, at its line
    and column, with the sentence `the mapping <address> differs from the
    others`. None where the trellis file is no file of the factory's folder
    within the model folder, cannot be read, or writes fewer than two
    mappings."""
    try:
        name = entry_value(recipe, "trellis")
        if not isinstance(name, str) or not _beside(name):
            return []
        relative = factory_path(name)
        if not (folder / relative).resolve().is_relative_to(folder.resolve()):
            return []
        text = _unsaved_or_disk(folder / relative, texts)
        mappings = entry_value(text, "inter_connectors")
        if not isinstance(mappings, list) or len(mappings) < 2:
            return []
        counts = [sum(other == mapping for other in mappings) for mapping in mappings]
        usual = mappings[counts.index(max(counts))]
        found = []
        for index, mapping in enumerate(mappings):
            if mapping != usual:
                address = f"inter_connectors[{index}]"
                span = entry_span(text, ("inter_connectors", index))
                sentence = f"the mapping {address} differs from the others"
                found.append(ChecklistEntry(relative, address, span.line, span.column, sentence))
        return found
    except (OSError, ValueError, KeyError):
        return []


def _unsaved_or_disk(path: Path, texts: dict) -> str:
    """The text of the file `path`: the text `texts` holds under the file's
    resolved path, as a string, where it holds one (spec 0.4 §3.1); the
    file's text on disk otherwise, read as UTF-8 with its line ends as
    written, as `model.read_file` reads a buffer's file."""
    resolved = str(path.resolve())
    if resolved in texts:
        return texts[resolved]
    with open(path, encoding="utf-8", newline="") as stream:
        return stream.read()


def _child(node, key: str):
    """The value at `key` of the mapping node `node`, None where `node` is
    no mapping or holds no such key."""
    if isinstance(node, yaml.MappingNode):
        return next((value for name, value in node.value if name.value == key), None)
    return None


# a folder name: letters, digits, "-" and "_", beginning with a letter or a
# digit; a stage key: letters, digits and "_", beginning with a letter or
# "_"; a period label: letters, digits and "_"
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_LABEL = re.compile(r"[A-Za-z0-9_]+")
# a variant's name, which stands in the names of its files: a plain word of
# letters, digits and "-" (§4, new variant); and the name of a period file a
# variant copies, `period.yml` or `period.<x>.yml` (ruling R25)
_VARIANT = re.compile(r"[A-Za-z0-9-]+")
_PERIOD_FILE = re.compile(r"period(\.[^/\\]+)?\.yml")


class Created(NamedTuple):
    """What `create_trellis` wrote: `folder`, the new model folder;
    `files`, the files written under it, relative and in posix form, sorted,
    git's own folder left out; and `repository`, whether a repository was
    made for it."""

    folder: Path
    files: tuple[str, ...]
    repository: bool


def create_trellis(
    parent,
    name: str,
    stages,
    label: str,
    repeat: int,
    destination: str | None = None,
    *,
    terminal=(),
) -> Created:
    """The folder `name` written under `parent`, the folder the form "new
    trellis" asks for, by default the folder that holds the open model, so
    that the new model stands beside it (unit L, Task 13; defect 15 of the
    UX simulation), in the one layout of a
    model folder (§3.3, §4): in the factory's folder `declaration/`
    (`factory_path`), each stage `(key, template id)` of `stages` copied
    from its template into its own folder, `stages/<key>/<key>.bl`, never
    linked back, with the methods file the template brings copied beside
    it as `methods.yml`, and the template's calibration and settings files
    copied into `calibration/` and `settings/` under their own names
    (`companion_path`), the stage file's `@stage:` line and the methods
    file's `stage:` naming the key (`_stage_copy`, `_companion_copy`);
    `period.yml`, the period `label` listing the keys with an empty
    connector mapping; `trellis.yml`, that period repeated `repeat` times
    with an empty inter-period mapping; `spec.yml`, one row per stage whose
    three bindings are slots; and at the folder's top answers.yml,
    the .gitignore and a three-line README.md. With no stage, the folder
    holds those files with their lists of stages empty, for "new stage" to
    fill (unit L, Task 13; defect 1 of the UX simulation).

    `terminal` holds the keys of `stages` that stand in the terminal period
    alone, as a bequest does (unit K, Task 12; the usability walkthrough §4
    item 7). Where it holds any and `repeat` is two or more, period.yml
    lists the other keys and `trellis.yml` writes the terminal period out
    with every key before period.yml repeated `repeat - 1` times
    (`trellis_text`); with one period, that period is the terminal one and
    holds every key, and the files are those written without `terminal`.

    The files are written into a hidden folder beside the target and
    renamed to it when complete, so that a refusal or a failure leaves
    nothing. Where no repository holds `parent`, the folder is made a
    repository of its own, with `destination`, where given, as the push
    destination of its branch (`model.init_repository`); nothing is
    committed (§4). Refused with an `AnswerRefusal`, a ValueError that
    names the answer it concerns, before anything is written: a parent that
    is no folder, or that is a model folder or lies in one
    (`_check_parent`); a name that is no plain folder name or names an
    existing entry; a key that is no identifier or is given twice, a
    template id `stage_templates` does not list; a label that is not
    letters, digits and "_"; a key, the label or the trellis name, the name
    with each "-" written "_", that YAML reads as an integer, a boolean or
    null, such as `2026`, `yes` or `null`; a repeat below one; a key of
    `terminal` that `stages` does not hold, or every key of `stages` in
    `terminal` with two or more periods, which would leave the periods
    before the terminal one with no stage; two companions of one name and
    different contents; a destination that `model.destination_refusal`
    refuses, such as one that carries a password or a token."""
    parent = Path(parent).resolve()
    terminal = tuple(terminal)
    _check_answers(parent, name, stages, label, repeat, destination, terminal)
    keys = [key for key, _ in stages]
    templates = [template_of(template_id) for _, template_id in stages]
    try:
        companions = _companions(zip(keys, templates, strict=True))
    except ValueError as error:
        raise AnswerRefusal("templates", str(error)) from None
    in_repository = model.open_folder(parent).git_root is not None
    # the keys of the terminal period written out, none where every period
    # is period.yml's
    apart = set(terminal) if repeat > 1 else set()
    written_out = keys if apart else ()
    texts = {
        factory_path(RECIPE): recipe_text(name, keys),
        factory_path(PERIOD): period_text(label, [key for key in keys if key not in apart]),
        factory_path(TRELLIS): trellis_text(name.replace("-", "_"), repeat, written_out),
        ANSWERS: answers_text(name, destination, label, repeat, stages, written_out),
        ".gitignore": GITIGNORE,
        "README.md": readme_text(name, keys),
    }
    # the copies of the templates' stage files and companions
    copies = {
        factory_path(stage_file(key)): _stage_copy(template, key)
        for key, template in zip(keys, templates, strict=True)
    }
    copies.update((target, text) for target, (_, text) in companions.items())
    target = parent / name
    building = Path(tempfile.mkdtemp(prefix=f".{name}.", dir=parent))
    try:
        # the factory's folder first, then each stage's folder with stages/,
        # so that the folders exist before their files are written, a
        # folder with no stage included
        (building / FACTORY_FOLDER).mkdir()
        for key in keys:
            (building / factory_path(stage_folder(key))).mkdir(parents=True)
        for relative, text in texts.items():
            (building / relative).write_text(text, encoding="utf-8")
        # each copy with the line ends its source writes
        for relative, text in copies.items():
            (building / relative).parent.mkdir(exist_ok=True)
            (building / relative).write_text(text, encoding="utf-8", newline="")
        if not in_repository:
            made = model.init_repository(building, destination)
            if not made.ok:
                raise ValueError(f"git made no repository for {name}: {made.sentence}")
        os.rename(building, target)
    except BaseException:
        shutil.rmtree(building, ignore_errors=True)
        raise
    files = sorted(
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file() and path.relative_to(target).parts[0] != ".git"
    )
    return Created(target, tuple(files), not in_repository)


class AnswerRefusal(ValueError):
    """The refusal of one answer of the form "new trellis", a ValueError
    whose sentence names what is wrong, with `field`, the answer it
    concerns: `name`, `periods`, `parent`, `destination`, `label` or
    `templates`, so that the form draws the sentence under that field
    (design pass 4 §2; unit L's final judgment, §6 item 10)."""

    def __init__(self, field: str, sentence: str):
        super().__init__(sentence)
        self.field = field


def _check_answers(parent: Path, name, stages, label, repeat, destination, terminal) -> None:
    """Refuses the answers of the form "new trellis" that cannot be
    written, before anything is, with an `AnswerRefusal` that names what is
    wrong and, where that alone does not say it, what to write, and the
    answer it concerns. No stage chosen is no refusal: the folder is then
    written with none (unit L, Task 13)."""
    try:
        _check_parent(parent)
    except ValueError as error:
        raise AnswerRefusal("parent", str(error)) from None
    if not _NAME.fullmatch(name or ""):
        raise AnswerRefusal(
            "name",
            f"{name!r} is no folder name: write letters, digits, '-' and '_', beginning "
            "with a letter or a digit",
        )
    trellis_name = name.replace("-", "_")
    if not _reads_as_itself(trellis_name):
        raise AnswerRefusal(
            "name",
            f"YAML reads the trellis name {trellis_name!r}, the folder name with '_' for "
            "'-', as an integer, a boolean or null",
        )
    if (parent / name).exists():
        raise AnswerRefusal("name", f"{parent / name} exists")
    keys = [key for key, _ in stages]
    try:
        for key in keys:
            _check_key(key)
    except ValueError as error:
        raise AnswerRefusal("templates", str(error)) from None
    twice = next((key for number, key in enumerate(keys) if key in keys[:number]), None)
    if twice is not None:
        raise AnswerRefusal("templates", f"the stage key {twice!r} is given twice")
    try:
        for _, template_id in stages:
            template_of(template_id)
    except ValueError as error:
        raise AnswerRefusal("templates", str(error)) from None
    try:
        _check_label(label)
    except ValueError as error:
        raise AnswerRefusal("label", str(error)) from None
    if isinstance(repeat, bool) or not isinstance(repeat, int) or repeat < 1:
        raise AnswerRefusal(
            "periods", f"the number of periods is {repeat!r}, not a whole number of one or more"
        )
    # the stages marked for the terminal period alone (unit K, Task 12)
    unknown = next((key for key in terminal if key not in keys), None)
    if unknown is not None:
        raise AnswerRefusal(
            "templates",
            f"the stage key {unknown!r} is marked for the terminal period and is not chosen",
        )
    if keys and repeat > 1 and set(keys) <= set(terminal):
        raise AnswerRefusal(
            "templates",
            "every stage chosen is marked for the terminal period, so the periods before it "
            "would hold no stage: mark one for every period",
        )
    refusal = model.destination_refusal(destination) if destination else None
    if refusal is not None:
        raise AnswerRefusal("destination", refusal)


def _check_parent(parent: Path) -> None:
    """Refuses, with a ValueError, a parent folder of a new model folder
    that is no folder, or that is a model folder, one that holds the
    factory's folder `declaration/`, or lies in one, so that "new trellis"
    writes no model inside another model's folder (unit L, Task 13; defect
    15 of the UX simulation)."""
    if not parent.is_dir():
        raise ValueError(f"{parent} is no folder")
    holder = next(
        (folder for folder in (parent, *parent.parents) if (folder / FACTORY_FOLDER).is_dir()),
        None,
    )
    if holder == parent:
        raise ValueError(f"{parent} is a model folder: write the new folder beside it")
    if holder is not None:
        raise ValueError(
            f"{parent} lies in the model folder {holder}: write the new folder beside it"
        )


def _reads_as_itself(text: str) -> bool:
    """Whether `yaml.safe_load(text)` is the string `text` itself; False
    also where YAML cannot read `text`. YAML reads `yes`, `off` and `null`
    as a boolean or null and `2026`, `017` and `0x1F` as integers, and it
    raises a ValueError on `0x_`, a hexadecimal integer with no digit; the
    factory would read such a key, label or name in a file of the folder
    as that value, or refuse the file."""
    try:
        return yaml.safe_load(text) == text
    except (yaml.YAMLError, ValueError):
        return False


def _check_key(key: str) -> None:
    """Refuses a stage key that is no identifier, or that YAML reads as a
    boolean or null and not as the key itself (`_reads_as_itself`), with a
    ValueError that names what is wrong."""
    if not _KEY.fullmatch(key or ""):
        raise ValueError(
            f"{key!r} is no stage key: write letters, digits and '_', beginning with a "
            "letter or '_'"
        )
    if not _reads_as_itself(key):
        raise ValueError(f"YAML reads the stage key {key!r} as a boolean or null")


def _check_label(label: str) -> None:
    """Refuses a period label that is not letters, digits and "_", or that
    YAML reads as an integer, a boolean or null and not as the label itself
    (`_reads_as_itself`), with a ValueError that names what is wrong."""
    if not _LABEL.fullmatch(label or ""):
        raise ValueError(f"{label!r} is no period label: write letters, digits and '_'")
    if not _reads_as_itself(label):
        raise ValueError(f"YAML reads the period label {label!r} as an integer, a boolean or null")


def _check_chosen(keys) -> None:
    """Refuses, with a ValueError, a period for which `keys`, the stages
    chosen, is empty."""
    if not keys:
        raise ValueError("no stage is chosen")


def _companions(chosen) -> dict[str, tuple[Path, str]]:
    """Each companion file of the templates `chosen`, pairs (stage key,
    template), with the text of its copy (`_companion_copy`), by the path
    it is copied to, relative to the model folder (`companion_path`): a
    template's methods file into its stage's folder,
    `declaration/stages/<key>/methods.yml`, and its calibration and
    settings files into `declaration/<kind>/`, each once. A template brings
    one methods file at most, as each of `TEMPLATE_SOURCES` does; two
    files of one name and different contents are refused with a ValueError
    that names both. A methods file whose lines name a block file under
    `block:` brings that block file as well, copied as its source writes it
    into `declaration/methods/`, where the layout places block files
    (decision SD-14), and the methods file's copy names it there
    (`_block_copies`; SE-29)."""
    planned, copies = {}, {}

    def copied(target, source, text):
        earlier = planned.setdefault(target, source)
        if earlier != source and earlier.read_bytes() != source.read_bytes():
            raise ValueError(
                f"two templates bring {target} with different contents, {earlier} "
                f"and {source}"
            )
        copies.setdefault(target, (source, text))

    for key, template in chosen:
        for kind in KINDS:
            for source in template.companions[kind]:
                target = companion_path(key, kind, source)
                text = _companion_copy(source, kind, key)
                if kind == "methods":
                    text, blocks = _block_copies(source, target, text)
                    for block_target, block in blocks:
                        copied(block_target, block, _source_text(block))
                copied(target, source, text)
    return copies


def _block_copies(source: Path, target: str, text: str) -> tuple[str, tuple]:
    """The text `text` of the copy `target` of the methods file `source`,
    with each `block:` entry of its `methods` list rewritten as the path,
    from the copy's folder, of the block file's copy in the factory's
    `methods/` folder, `../../methods/cons_egm.bl`; and the pairs (that
    copy's path relative to the model folder, the block file the entry
    names from the source's folder), in the order of the list. A block
    path is read from the folder of the methods file that writes it, as the
    package reads it (SE-29)."""
    document = entry_value(text)
    lines = document.get("methods") if isinstance(document, dict) else None
    blocks = []
    for index, line in enumerate(lines if isinstance(lines, list) else ()):
        if not isinstance(line, dict) or not isinstance(line.get("block"), str):
            continue
        block = (source.parent / line["block"]).resolve()
        block_target = factory_path(posixpath.join("methods", block.name))
        written = posixpath.relpath(block_target, posixpath.dirname(target))
        text = replace_entry(text, ("methods", index, "block"), written)
        blocks.append((block_target, block))
    return text, tuple(blocks)


# the line of a stage file that names the stage, `@stage: <name>`: `@stage:`
# and the spaces after it as the first group, the name as the second
_STAGE_LINE = re.compile(r"^(@stage:[ \t]*)(\S+)", re.MULTILINE)


def _stage_copy(template: StageTemplate, key: str) -> str:
    """The text of the copy of the stage file of `template` under the stage
    key `key` (unit K, Task 12; the usability walkthrough §4 item 17): the
    file's text with the name its `@stage:` line writes replaced by `key`,
    every other character kept, line ends included, so that the stage is
    named by the key the tree and the recipe show; the file's text itself
    where the key is the template's own."""
    return _STAGE_LINE.sub(lambda found: found[1] + key, _source_text(template.stage), count=1)


def _companion_copy(source: Path, kind: str, key: str) -> str:
    """The text of the copy of the companion file `source`, of the binding
    `kind`, for the stage key `key`: a methods file that names a stage under
    `stage:`, which binds the stage it names (spec 0.3c §4.3), with that
    name written `key` by the package's writer `replace_entry`, every other
    character kept (unit K, Task 12); any other file, and a methods file
    that names no stage or names `key`, as its source writes it."""
    text = _source_text(source)
    if kind != "methods":
        return text
    try:
        named = entry_value(text, "stage")
    except KeyError:
        return text
    return text if named == key else replace_entry(text, "stage", key)


def variant_sources(folder, from_recipe: str, texts=None) -> tuple[str, ...]:
    """The files a variant of the recipe `from_recipe`, a recipe's name in
    the factory's folder, copies (`create_variant`), by their paths from
    the model folder `folder`: the recipe, the trellis file it names, then
    each period file that trellis file names, once, in the order it names
    them. The recipe and the trellis file are read from `texts`, the mapping
    of unsaved texts by a file's resolved path as a string, where it holds
    them (spec 0.4 §3.1), and from disk otherwise. Refused as
    `create_variant` refuses its recipe, trellis file and period files."""
    root = Path(folder).resolve()
    _, trellis, _, templates = _variant_sources(root, from_recipe, texts)
    periods = dict.fromkeys(template for _, template in templates)
    return (factory_path(from_recipe), factory_path(trellis), *map(factory_path, periods))


def create_variant(folder, name: str, from_recipe: str) -> tuple[str, ...]:
    """A second trellis of the model of `folder` written beside the first
    (§4, new variant; rule 4 of the layout), in the factory's folder: the
    recipe `spec.<name>.yml`, a copy of the recipe `from_recipe` of that
    folder whose `trellis:` names `trellis.<name>.yml`; the trellis file
    `trellis.<name>.yml`, a copy of the trellis file the recipe names whose
    `template:` entries name the copies of their period files; and a copy
    of each period file the trellis file names, `period.yml` as
    `period.<name>.yml` and `period.<x>.yml` as `period.<name>.<x>.yml`
    (rulings R23 and R25), so that the variant and its source share no file
    that "add stage" or "add period" edits. Each copy is its source's text
    with those entries alone written anew by the package's writer
    `replace_entry`, a quoted value within its quotes, every other
    character kept, comments included; nothing else in the folder is
    written. Answers the files written, by their paths from the
    folder: the recipe, the trellis file, then the period files in the
    order the trellis file names them. Refused with a ValueError before
    anything is written: a name that is no plain word of letters, digits
    and "-"; a recipe the factory's folder does not hold; a trellis file or
    a period file named at an entry that is no file of that folder, or a
    period file named otherwise than `period.yml` or `period.<x>.yml`; a
    file that does not read as UTF-8 text, or that the package's reader of
    YAML files refuses (`entry_value`), or an entry `replace_entry` cannot
    write anew; a file of the variant that exists, every one named. A file
    of the variant that appears on disk while the variant is written is
    refused with a ValueError naming it, and the files written before it
    are removed."""
    folder = Path(folder).resolve()
    if not _VARIANT.fullmatch(name or ""):
        raise ValueError(f"{name!r} is no variant name: write letters, digits and '-'")
    handle = model.open_folder(folder)
    recipe, trellis_name, trellis, templates = _variant_sources(handle.root, from_recipe)
    copies = {template: _period_copy(template, name) for _, template in templates}
    texts = {
        f"spec.{name}.yml": _replaced(recipe, from_recipe, [("trellis", f"trellis.{name}.yml")]),
        f"trellis.{name}.yml": _replaced(
            trellis, trellis_name, [(address, copies[template]) for address, template in templates]
        ),
        **{
            copy: _text_of(handle.root, factory_path(template))
            for template, copy in copies.items()
        },
    }
    existing = [factory_path(copy) for copy in texts if (folder / factory_path(copy)).exists()]
    if existing:
        verb = "exists" if len(existing) == 1 else "exist"
        raise ValueError(f"{_listed(existing)} {verb}")
    # the period files first and the recipe last, so that no written file of
    # the variant names one not yet written
    written = []
    try:
        for copy in reversed(texts):
            relative = factory_path(copy)
            if not model.save_file(handle, relative, texts[copy], None).saved:
                raise ValueError(f"{relative} appeared on disk while the variant was written")
            written.append(relative)
    except BaseException:
        for relative in written:
            (folder / relative).unlink(missing_ok=True)
        raise
    return tuple(factory_path(copy) for copy in texts)


def registry_sources(folder, recipe: str = RECIPE, texts=None) -> tuple[str, ...]:
    """The source names the `registry` block of the recipe `recipe` of the
    folder lists, each kind's in the order the block writes them,
    `calibration/wage_schedule`, read from `texts` where it holds the
    recipe and from disk otherwise: a variant copies that block with the
    recipe, and the periods' ages the trellis graph prints are read from
    the registry of the recipe shown, so the form "new variant" names the
    copy (unit L, Task 13; defect 19 of the UX simulation). No name where
    the recipe holds no such block, or cannot be read as YAML."""
    try:
        registry = entry_value(_text_of(Path(folder), factory_path(recipe), texts), "registry")
    except (OSError, ValueError, KeyError):
        return ()
    if not isinstance(registry, dict):
        return ()
    return tuple(
        str(name) for names in registry.values() if isinstance(names, list) for name in names
    )


def _variant_sources(root: Path, from_recipe: str, texts=None):
    """What a variant of the recipe `from_recipe` is made from, read from
    the factory's folder of the model folder `root`, each file from `texts`
    where it holds one (`_text_of`): the recipe's text; the name of the
    trellis file it names under `trellis:`, and that file's text; and the
    trellis file's `template:` entries, each as its address in the file,
    `periods[1].template`, and the name of the period file it names, in the
    order of `periods`. Refused with a ValueError naming the file: a recipe
    that is no file of the factory's folder; a trellis file or a period file
    named at an entry that is no file of that folder; a period file named
    otherwise than `period.yml` or `period.<x>.yml`; a file that does not
    read as UTF-8 text, or that the package's reader of YAML files refuses
    (`entry_value`)."""
    recipe_path = factory_path(from_recipe)
    if not _beside(from_recipe) or not (root / recipe_path).is_file():
        raise ValueError(f"the folder holds no {recipe_path}")
    recipe = _text_of(root, recipe_path, texts)
    trellis_name = _named_file(root, recipe, recipe_path, "trellis")
    trellis_path = factory_path(trellis_name)
    trellis = _text_of(root, trellis_path, texts)
    try:
        periods = entry_value(trellis, "periods")
    except KeyError:
        periods = None
    except ValueError as error:
        raise ValueError(f"{trellis_path}: {error}") from None
    templates = []
    for number, entry in enumerate(periods if isinstance(periods, list) else []):
        if not isinstance(entry, dict) or "template" not in entry:
            continue
        address = f"periods[{number}].template"
        template = _named_file(root, trellis, trellis_path, address)
        if not _PERIOD_FILE.fullmatch(template):
            raise ValueError(
                f"{trellis_path} names the period file {template} at {address}, not "
                "period.yml or period.<x>.yml"
            )
        templates.append((address, template))
    return recipe, trellis_name, trellis, templates


def _beside(name: str) -> bool:
    """Whether `name` is the name of an entry of a folder, one that names
    no other folder."""
    return posixpath.basename(name) == name and "\\" not in name and name not in ("", ".", "..")


def _text_of(root: Path, relative: str, texts=None) -> str:
    """The text of the file `relative` of the model folder `root`: the text
    `texts`, the mapping of unsaved texts by a file's resolved path as a
    string, holds for it (spec 0.4 §3.1), else the file's text, read as
    `model.read_file` reads it (`_unsaved_or_disk`); a file that is not
    UTF-8 text is refused with a ValueError naming it."""
    try:
        return _unsaved_or_disk(root / relative, texts or {})
    except UnicodeDecodeError:
        raise ValueError(f"{relative} is not UTF-8 text") from None


def _named_file(root: Path, text: str, relative: str, address: str) -> str:
    """The name of the file of the factory's folder of the model folder
    `root` that the file `relative`, whose text is `text`, names at the
    entry `address`, read by the package's reader of YAML files
    (`entry_value`); refused with a ValueError naming both where the entry
    is absent or is no string naming a file that stands in that folder, and
    with one naming the file where the reader refuses its text."""
    try:
        value = entry_value(text, address)
    except KeyError:
        value = None
    except ValueError as error:
        raise ValueError(f"{relative}: {error}") from None
    name = value if isinstance(value, str) else None
    if name is None or not _beside(name) or not (root / factory_path(name)).is_file():
        raise ValueError(f"{relative} names no file of {FACTORY_FOLDER}/ at {address}")
    return name


def _period_copy(template: str, name: str) -> str:
    """The name of the copy, for the variant `name`, of the period file
    `template`, `period.yml` or `period.<x>.yml`: `period.<name>.yml` or
    `period.<name>.<x>.yml` (ruling R25)."""
    return f"period.{name}{template.removeprefix('period')}"


def _replaced(text: str, source: str, replacements) -> str:
    """`text`, of the file `source` of the factory's folder, with the
    value at each address of `replacements`, pairs (address, value),
    written `value` by the package's writer `replace_entry`, within the
    value's quotes where it is quoted; an entry `replace_entry` cannot write
    anew, or an address the text does not hold, is refused with a
    ValueError naming the file."""
    try:
        for address, value in replacements:
            text = replace_entry(text, address, value)
    except (KeyError, ValueError) as error:
        reason = error.args[0] if isinstance(error, KeyError) else str(error)
        raise ValueError(f"{factory_path(source)}: {reason}") from None
    return text


def _listed(names: list[str]) -> str:
    """`names` written as a list in a sentence: `a`, `a and b`, `a, b and
    c`."""
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def can_add(folder, recipe: str = RECIPE, texts=None) -> bool:
    """Whether "add stage" and "add period" can edit the files of the recipe
    `recipe`, a recipe's name in the factory's folder of `folder`, the
    recipe the Workbench shows (spec 0.4 §3.5): the recipe stands in that
    folder and names under `trellis:` a file of it, the recipe read from
    `texts`, the mapping of unsaved texts by a file's resolved path as a
    string, where it holds it. answers.yml is not asked for, since the
    writers edit it only where it exists."""
    root = Path(folder).resolve()
    relative = factory_path(recipe)
    if not _beside(recipe) or not (root / relative).is_file():
        return False
    try:
        _named_file(root, _text_of(root, relative, texts), relative, "trellis")
    except (OSError, ValueError):
        return False
    return True


def period_files(folder, recipe: str = RECIPE, texts=None) -> tuple[str, ...]:
    """The period files of the recipe `recipe` of the folder, by their names
    in the factory's folder: those the trellis file it names writes under
    `template:` (`variant_sources`), the recipe and the trellis file read
    from `texts` where it holds them, period.yml first and the others in
    name order, so that "add stage" offers no period file of another recipe
    (`create_variant`); none where the recipe or its trellis file cannot be
    read so."""
    try:
        sources = variant_sources(folder, recipe, texts)
    except (OSError, ValueError):
        return ()
    names = [posixpath.basename(path) for path in sources[2:]]
    return tuple(sorted(names, key=lambda name: (name != PERIOD, name)))


def recipe_keys(folder, recipe: str = RECIPE, texts=None) -> tuple[str, ...]:
    """The stage keys of the recipe `recipe` of the folder, in its order,
    the recipe read from `texts` where it holds it; none where the recipe
    cannot be read, does not read as YAML or holds no `stages` mapping."""
    try:
        read = yaml.safe_load(_text_of(Path(folder), factory_path(recipe), texts))
    except (OSError, ValueError, yaml.YAMLError):
        return ()
    stages = read.get("stages") if isinstance(read, dict) else None
    return tuple(stages) if isinstance(stages, dict) else ()


class Added(NamedTuple):
    """What `add_stage`, `add_period`, `add_record_stage` or
    `add_record_period` answers, having written nothing (spec 0.4 §3.5,
    §3.6; brief rule 9; rulings J-P5 and J-P6):
    `new_files`, each file new to the folder, a template's stage file and
    its companions or a period file, as a pair (its path relative to the
    folder, its text), in the order the status line names them; `edits`,
    the new text of each existing file edited, by the file's resolved path
    as a string, the key of the mapping of unsaved texts; `read`, the text
    each edit was made from, by the same paths; `notes`, the parts of the
    status line in the forms of brief §5, which joined by "; " name the
    file and the entry written, the periods reached, the entry split, the
    inter-period mapping replaced or the list expanded, each range and
    range key of the recipe changed, the new files and, after an insertion,
    the restriction written; `restriction`, the text for the
    restriction's input after a period is added between two periods,
    `periods 2–4` or the empty text, and None where no index moved (spec
    0.4 §3.6; plan, Task 12; ruling J-P21); and `deleted`, for
    `remove_stage` and `remove_period`, the files and folders the removal
    deletes from disk once the files that named them are saved, by their
    paths from the model folder, none for an addition (unit L, Task 25;
    AAS, L-D18)."""

    new_files: tuple
    edits: dict
    read: dict
    notes: tuple
    restriction: str | None = None
    deleted: tuple = ()


def add_stage(
    folder,
    key: str,
    template: str | StageTemplate,
    period_file: str = PERIOD,
    *,
    entry: str = "",
    recipe: str = RECIPE,
    texts=None,
) -> Added:
    """One more stage in the folder `folder` (spec 0.3 §4; spec 0.4 §3.5),
    answered and not written, from `template`, the id of a template that
    `stage_templates` lists or the template of a stage folder of the disk
    that `folder_template` answers (unit K's decision K-D26): as new files,
    the template's stage file in
    the stage's own folder, `stages/<key>/<key>.bl` in the factory's folder,
    with the methods file the template brings beside it as `methods.yml`,
    and its calibration and settings files in `calibration/` and
    `settings/` (`companion_path`), a companion the folder holds with the
    same contents being kept, the stage file's `@stage:` line and the
    methods file's `stage:` naming the key as "new trellis" writes them
    (`_stage_copy`, `_companion_copy`; unit K, Task 12); as edits, the row
    of `key` with its three slots added at the end of the `stages`
    of the recipe `recipe`, the key added at the end of the `stages` list
    of the entry `entry` of `period_file`, and, where the folder holds
    answers.yml, the stage with its template's record (`_answers_record`)
    and its slots added to it, each file edited as
    text, its comments and layout kept (spec 0.3 §3.2), and read from
    `texts`, the mapping of unsaved texts by a file's resolved path as a
    string, where it holds it, and from disk otherwise; and as notes,
    `period.yml, stages: <key> written, periods 0–5`, the periods whose
    entry is that entry of `period_file` (`period_entries` of the trellis
    file the recipe names), then `new: ` and the new files by their paths
    from the factory's folder. Nothing outside the model folder is written,
    and the recipe names the copy, never its origin. Refused with a
    ValueError: a folder without
    the recipe or `period_file`, or whose recipe names no trellis file of
    the factory's folder; a key that is no identifier, that the recipe
    holds, or whose folder `stages/<key>/` exists; a key that YAML reads as
    a boolean or null, such as `yes`; a template id `stage_templates` does
    not list; a companion the folder holds with other contents; an entry
    that `append_to_mapping` or `append_to_sequence` cannot extend.
    `period_file` is the name in the factory's folder of the file that
    writes the period's list, a period file as `period_files` answers it or
    the trellis file, and `entry` the address of the period's entry in it,
    as `period_entries` answers it: the empty address for a period file,
    and `periods[0]` for an entry of the trellis file that writes its own
    stages, whose list is then `periods[0].stages` (spec 0.4 §3.5: a
    period's list is a period file's `stages` or the `stages` of an inline
    entry of the trellis file)."""
    folder = Path(folder).resolve()
    _require(folder, (factory_path(recipe), factory_path(period_file)))
    trellis = _trellis_named(folder, recipe, texts)
    _check_key(key)
    held = factory_path(stage_folder(key))
    if (folder / held).exists():
        raise ValueError(f"{held}/ exists")
    if not isinstance(template, StageTemplate):
        template = template_of(template)
    new_files = [(factory_path(stage_file(key)), _stage_copy(template, key))]
    for target, (source, text) in _companions([(key, template)]).items():
        if not (folder / target).is_file():
            new_files.append((target, text))
        elif (folder / target).read_bytes() != text.encode("utf-8"):
            raise ValueError(f"{target} exists with other contents than {source}")
    # the address of the period's list in `period_file`
    stages = f"{entry}.stages" if entry else "stages"
    edits = {
        factory_path(recipe): lambda text: append_to_mapping(text, "stages", key, recipe_row(key)),
        factory_path(period_file): lambda text: append_to_sequence(text, stages, key),
    }
    if (folder / ANSWERS).is_file():
        edits[ANSWERS] = lambda text: _answers_with_stage(text, key, _answers_record(template))
    made, read = _edits(folder, edits, texts)
    listed = (folder / factory_path(period_file)).resolve()
    reached = next(
        (
            periods
            for path, address, periods in _entries(trellis, texts)
            if address == entry and Path(path).resolve() == listed
        ),
        (),
    )
    notes = (_written_note(period_file, stages, key, reached), _new_note(new_files))
    return Added(tuple(new_files), made, read, notes)


def new_stage(folder, key: str, *, recipe: str = RECIPE, texts=None) -> Added:
    """A stage of the author's own in the folder `folder` (unit K's decision
    K-D7; the plan of unit K, Task 9), answered and not written, as
    `add_stage` answers a template's stage: as the new file, the stage file
    `stages/<key>/<key>.bl` in the factory's folder, the empty stage
    (`empty_stage_text`); as edits, the row of `key` with its three slots
    (`recipe_row`) added at the end of the `stages` of the recipe `recipe`
    and, where the folder holds answers.yml, the names of those slots added
    to its `required.slots`, the record of the slots written,
    each file edited as text, its comments and layout kept, and read from
    `texts`, the mapping of unsaved texts by a file's resolved path as a
    string, where it holds it, and from disk otherwise; and as notes,
    `spec.yml, stages: <key> written` and `new: stages/<key>/<key>.bl`. No
    period's list is edited, so that the factory refuses the recipe, which
    then names a stage that no period holds, until the author writes the
    key in a period's list. Refused with a ValueError: a folder without the
    recipe; a key that is no identifier, that YAML reads as a boolean or
    null, whose folder `stages/<key>/` exists, or that the recipe holds; an
    entry that `append_to_mapping` or `append_to_sequence` cannot extend."""
    folder = Path(folder).resolve()
    _require(folder, (factory_path(recipe),))
    _check_key(key)
    held = factory_path(stage_folder(key))
    if (folder / held).exists():
        raise ValueError(f"{held}/ exists")
    new_files = ((factory_path(stage_file(key)), empty_stage_text(key)),)
    edits = {
        factory_path(recipe): lambda text: append_to_mapping(text, "stages", key, recipe_row(key)),
    }
    if (folder / ANSWERS).is_file():
        edits[ANSWERS] = lambda text: _answers_with_slots(text, key)
    made, read = _edits(folder, edits, texts)
    notes = (_written_note(recipe, "stages", key, ()), _new_note(new_files))
    return Added(new_files, made, read, notes)


def new_source_file(folder, key: str, kind: str) -> tuple[str, str]:
    """The file of the binding `kind` of the stage `key` that `New file` of
    the Recipe tab writes in place of a slot (unit K's decision
    K-D7), answered and not written: its path relative to the model folder
    `folder`, at the folder's conventional place (`source_path`), and its
    text, the empty file of its kind (`empty_source_text`). Refused with a
    ValueError: a kind that is none of `KINDS`; a key that is no identifier
    or that YAML reads as a boolean or null; a file that exists at that
    path."""
    if kind not in KINDS:
        raise ValueError(f"{kind!r} is no binding kind: write calibration, settings or methods")
    _check_key(key)
    path = source_path(key, kind)
    if (Path(folder) / path).exists():
        raise ValueError(f"{path} exists")
    return path, empty_source_text(key, kind)


def add_period(
    folder,
    label: str,
    keys,
    *,
    at: int | None = None,
    recipe: str = RECIPE,
    texts=None,
    standing=None,
) -> Added:
    """One more period (spec 0.3 §4; spec 0.4 §3.6), answered and not
    written: as the new file, the period file `period.<label>.yml` in the
    factory's folder in the form of period.yml with the stage keys `keys`
    and an empty connector mapping; as edits, of the trellis file the
    recipe `recipe` names, of the recipe and, where the folder holds it, of
    answers.yml, each file read from `texts`, the mapping of unsaved texts
    by a file's resolved path as a string, where it holds it, and from disk
    otherwise, and a file left as it was not answered.

    With `at` None the period is the earliest of the model: the entry
    `{template: period.<label>.yml, repeat: 1}` is added at the end of the
    trellis file's `periods`, since that list counts the periods back from
    the terminal one, `periods[h]` lying h periods before it, with an empty
    mapping added at the end of its `inter_connectors` where that list holds
    one mapping for each adjacent pair (`_trellis_with_period`), and the
    period is added to answers.yml's `periods`, its file named as the
    trellis file names it, by the rule `answers_text` states.

    With `at` the index h the new period takes, from 1 to the number of
    periods less one, the period is added between periods[h] and
    periods[h−1], raising by one the index of every period on its earlier
    side (`_trellis_with_insertion`): the entry that writes both neighbors
    with `repeat: n` is split around the new entry, its repeat first
    written into it where it stands in its period file (ruling J-P11); the
    new entry stands above the comments over the entry after it
    (`_entry_inserted`); the mapping of the pair split is replaced by the
    mappings of the two new pairs, or the one standing mapping kept where
    the new period's stages equal both neighbors' or `standing(at, keys)`,
    given, answers that the package admits it at both new pairs, and
    expanded to one for each pair otherwise (`_insertion`,
    `_pairs_inserted`; unit L, Task 19); in the recipe every bound of a
    range `periods: [lo, hi]` and every range key `lo-hi` of a binding
    list at or above h is raised by one (`_ranges_raised`); answers.yml's
    entry is split in the
    same way where its `periods` record those of this trellis file entry for
    entry, the addresses of its `required.connectors` in this trellis file
    are renumbered with it, and, where this trellis file is the one the
    folder's recipe names, which the checklist reads, an expansion is
    recorded as `expanded: {inter_connectors: true}` (J-D23) and each range
    and range key the recipe's edit changed is recorded under `moved`, so
    that the checklist names them as the status line does
    (`_with_moved_record`); and `restriction` holds the text for the
    restriction's input (`_restriction_after`).

    At either place, the range of a stage of `keys` that the recipe
    restricts to periods that exclude the new index is widened to include
    it (`range_widened`; ruling J-P8). The notes are the status line's
    parts in the forms of brief §5: `trellis.yml, periods: {template:
    period.<label>.yml, repeat: 1} written, periods 6`, or for a split
    `trellis.yml, periods: repeat 6 split 3, period.mid.yml, 3`; then
    `inter_connectors[2] replaced` or `inter_connectors: one mapping
    expanded to 6`; each range and key changed, `spec.yml,
    stages.housing.periods: [1, 3] now [1, 4]`, the recipe's file named
    before the first; `new: ` and the period file; and after an insertion
    `restriction periods 2–4` or `restriction emptied` (ruling J-P21).
    Refused with a ValueError before any text is answered: a folder without
    the recipe, or whose recipe names no trellis file of the factory's
    folder; a label that is not letters, digits and "_", or whose period
    file exists; a label that YAML reads as an integer, a boolean or null,
    such as `2026`; no stage, or a key the recipe does not hold; an `at`
    that is no place between two periods; an answers.yml whose text reads
    as no mapping; an entry that a writer cannot extend or write over as
    text."""
    folder = Path(folder).resolve()
    _require(folder, (factory_path(recipe),))
    trellis = _trellis_named(folder, recipe, texts)
    _check_label(label)
    # the period file's name in the factory's folder, as the trellis file's
    # `template:` and answers.yml's `periods[].file` write it
    # (`answers_text`), and its path from the model folder
    name = f"period.{label}.yml"
    period_file = factory_path(name)
    if (folder / period_file).exists():
        raise ValueError(f"{period_file} exists")
    keys = list(keys)
    _check_chosen(keys)
    known = recipe_keys(folder, recipe, texts)
    unknown = [key for key in keys if key not in known]
    if unknown:
        raise ValueError(f"the recipe holds no stage {unknown[0]!r}")
    entry = f"{{template: {name}, repeat: 1}}"
    recorded = f"{{label: {label}, file: {name}, repeat: 1}}"
    recipe_path = factory_path(recipe)
    if at is None:
        # the new period is the earliest, whose index is the number of
        # periods the trellis file writes before it
        earlier = _entries(trellis, texts)
        h = len(earlier) if earlier else None
        insertion = None
        trellis_edit = functools.partial(_trellis_with_period, name=name)
        answers_edit = functools.partial(append_to_sequence, address="periods", item=recorded)
    else:
        insertion = _insertion(
            folder, trellis, at, keys, texts, _text_of(folder, recipe_path, texts), standing
        )
        h = at
        trellis_edit = functools.partial(_trellis_with_insertion, insertion=insertion, item=entry)
    # the trellis file first and the recipe second, as the notes name them
    edits = {
        factory_path(trellis.name): trellis_edit,
        recipe_path: functools.partial(_recipe_for_period, h=h, keys=keys, raised=at is not None),
    }
    made, read = _edits(folder, edits, texts)
    resolved = str((folder / recipe_path).resolve())
    moved = _moved(read[resolved], made[resolved]) if resolved in made else []
    if insertion is not None:
        # answers.yml's periods and its records of an expansion and of the
        # ranges changed describe the trellis file the folder's recipe
        # names, which the checklist reads
        answers_edit = functools.partial(
            _answers_with_insertion,
            insertion=insertion,
            item=recorded,
            folder=folder,
            trellis=trellis,
            records=_trellis_of_the_folder(folder, texts) == trellis.resolve(),
            recipe=recipe_path,
            moved=[(old, new) for old, new, _ in moved],
        )
    if (folder / ANSWERS).is_file():
        # answers.yml last, since it records what the recipe's edit changed
        answered, answered_from = _edits(folder, {ANSWERS: answers_edit}, texts)
        made.update(answered)
        read.update(answered_from)
    new_files = ((period_file, period_text(label, keys)),)
    if insertion is None:
        notes = [_written_note(trellis.name, "periods", entry, () if h is None else (h,))]
        restriction = None
    else:
        notes = [_split_note(trellis.name, insertion, name)]
        notes += [part for part in (_pairs_note(insertion),) if part is not None]
        restriction = _restriction_after(insertion)
    notes += [
        f"{recipe}, {part}" if number == 0 else part for number, (*_, part) in enumerate(moved)
    ]
    notes.append(_new_note(new_files))
    if restriction is not None:
        notes.append(f"restriction {restriction}" if restriction else "restriction emptied")
    return Added(new_files, made, read, tuple(notes), restriction)


def range_widened(text: str, key: str, h: int) -> tuple[str, str | None]:
    """The recipe's text `text` with the range `periods: [lo, hi]` of the
    stage `key` widened to include period `h` where it excludes it, so that
    the stage is active at the period it is added to rather than listed and
    inactive there (spec 0.4 §§3.5, 3.6; ruling J-P8): `lo` lowered to `h`,
    or `hi` raised to it, through the package's writer `replace_entry`,
    every other character kept; and the status line's part
    `stages.<key>.periods: [lo, hi] now [lo', hi']`. A stage the recipe
    does not restrict, a range the factory would refuse, and a range that
    holds `h` answer the text as given and None. Refused with a ValueError
    where the text does not read as YAML or `replace_entry` cannot write a
    bound."""
    path = ("stages", key, "periods")
    try:
        bounds = _bounds(entry_value(text, path))
    except KeyError:
        return text, None
    if bounds is None or bounds[0] <= h <= bounds[1]:
        return text, None
    widened = (min(bounds[0], h), max(bounds[1], h))
    for index, (old, new) in enumerate(zip(bounds, widened)):
        if new != old:
            text = replace_entry(text, (*path, index), new)
    return text, _range_note(path, bounds, widened)


def _require(folder: Path, names) -> None:
    """Refuses, with a ValueError naming them, a folder that lacks one of
    the files `names`."""
    missing = [name for name in names if not (folder / name).is_file()]
    if missing:
        raise ValueError(f"the folder holds no {', '.join(missing)}")


def _trellis_named(folder: Path, recipe: str, texts) -> Path:
    """The trellis file the recipe `recipe` of the model folder `folder`
    names under `trellis:`, the recipe read from `texts` where it holds it;
    refused with a ValueError naming the recipe where it names no file of
    the factory's folder (`_named_file`)."""
    relative = factory_path(recipe)
    name = _named_file(folder, _text_of(folder, relative, texts), relative, "trellis")
    return folder / factory_path(name)


def _entries(trellis: Path, texts) -> list:
    """The package's `period_entries` of the trellis file `trellis`, read
    with the mapping of unsaved texts `texts`: for each period, the file and
    the address of its entry and the periods that entry writes; empty where
    the file cannot be read so, the factory then stating its refusal."""
    try:
        return period_entries(trellis, texts or None)
    except (OSError, ValueError, KeyError):
        return []


def _source_text(path: Path) -> str:
    """The text of a template's file `path`, read as UTF-8 with its line
    ends as written, so that the copy written from it holds the same
    bytes."""
    with open(path, encoding="utf-8", newline="") as stream:
        return stream.read()


def _edits(folder: Path, edits: dict, texts) -> tuple[dict, dict]:
    """The new text of each file of `edits`, `{path relative to the folder:
    function of its text}`, and the text it was made from, each by the
    file's resolved path as a string (ruling J-P6); each file read from
    `texts` where it holds it and from disk otherwise (`_text_of`). Every
    edit is made before any is answered, so that a refused edit answers
    none; a file whose text its edit leaves as it was is not answered, so
    that no buffer is marked unsaved for it. An entry that a writer cannot
    extend or write over is refused with a ValueError naming the file."""
    made, read = {}, {}
    for relative, edit in edits.items():
        text = _text_of(folder, relative, texts)
        try:
            new = edit(text)
        except (KeyError, ValueError) as error:
            reason = error.args[0] if isinstance(error, KeyError) else str(error)
            raise ValueError(f"{relative}: {reason}") from None
        if new != text:
            path = str((folder / relative).resolve())
            made[path], read[path] = new, text
    return made, read


def _written_note(file: str, address: str, text: str, periods) -> str:
    """One part of the status line in the form of brief §5: the file by its
    name in the factory's folder, the address and the text written, and
    the periods reached, each run of consecutive periods as a range, as the
    connector's note writes them, `period.yml, stages: housing written,
    periods 1–5`; the periods left out where none is known."""
    note = f"{file}, {address}: {text} written"
    return f"{note}, periods {_runs(periods)}" if periods else note


def _new_note(new_files) -> str:
    """The part of the status line that names the new files, by their paths
    from the factory's folder, in the form of brief §5: `new:
    stages/housing/housing.bl`."""
    return "new: " + ", ".join(posixpath.relpath(path, FACTORY_FOLDER) for path, _ in new_files)


def _runs(periods) -> str:
    """The periods `periods`, in order, each run of consecutive periods
    written as a range, `0–5`, and a period alone by its number, `0–2, 4`,
    as the trellis module of the Workbench writes a connector's note."""
    runs = []
    for h in periods:
        if runs and h == runs[-1][1] + 1:
            runs[-1][1] = h
        else:
            runs.append([h, h])
    return ", ".join(f"{first}–{last}" if last > first else f"{first}" for first, last in runs)


def _trellis_with_period(text: str, name: str) -> str:
    """trellis.yml's text with the entry `{template: <name>, repeat: 1}`
    added at the end of `periods`, and the mapping of the new pair of
    periods (`_pair_appended`)."""
    return _pair_appended(append_to_sequence(text, "periods", f"{{template: {name}, repeat: 1}}"))


def _pair_appended(text: str) -> str:
    """The trellis file's text, an entry having been added at the end of
    `periods`, with an empty mapping added at the end of `inter_connectors`
    for the new pair of periods where that list holds more than one
    mapping. The factory reads a list of more than one mapping as one
    mapping for each adjacent pair, and refuses it where its length differs
    from the number of pairs (rule trellis-file-shape); one mapping, which
    stands for every pair, and an empty or absent list are left as they
    are."""
    try:
        mappings = entry_value(text, "inter_connectors")
    except KeyError:
        return text
    if isinstance(mappings, list) and len(mappings) > 1:
        text = append_to_sequence(text, "inter_connectors", "{}")
    return text


# --- a period added between two periods (spec 0.4 §3.6; unit J, Task 12) ---

# a line break as the YAML reader counts lines, "\r\n" counted once, as
# `entry_span` counts them
_LINE_BREAK = re.compile(r"\r\n|[\r\n\x85\u2028\u2029]")

# a range key of a binding list, `lo-hi`, as `load_recipe` reads one
_RANGE_KEY = re.compile(r"(\d+)-(\d+)")

# the address of an entry of the trellis file's `periods` list, as
# `written_at` answers it, and an address answers.yml's `required.connectors`
# writes in a trellis file, a list's name, an index and the rest
_ENTRY_ADDRESS = re.compile(r"periods\[(\d+)\]")
_LISTED_ADDRESS = re.compile(r"(periods|inter_connectors)\[(\d+)\](.*)")


class _Insertion(NamedTuple):
    """What a period added between two periods changes in the trellis file,
    read before any text is written (spec 0.4 §3.6): `at`, the index the new
    period takes; `count`, the number of periods before the insertion;
    `entry`, the index in the file's `periods` list of the entry that writes
    periods[at]; `split`, the number of that entry's periods on the terminal
    side of the new one where the entry also writes periods[at−1], None
    otherwise; `repeat`, the number of periods that entry writes, and
    `written`, whether it writes `repeat` itself; `place`, the index in the
    list of the new entry; `templates` and `repeats`, each entry's
    `template` and number of periods; `mappings`, the `inter_connectors`
    the file writes; and `change`, what becomes of them: `kept`,
    `expanded` from one standing mapping, `copied` or `emptied` for the two
    new pairs of a list of one mapping for each pair."""

    at: int
    count: int
    entry: int
    split: int | None
    repeat: int
    written: bool
    place: int
    templates: tuple
    repeats: tuple
    mappings: list | None
    change: str


def _insertion(
    folder: Path, trellis: Path, at, keys, texts, recipe: str | None, standing=None
) -> _Insertion:
    """The `_Insertion` of a period with the stage keys `keys` added as
    periods[at] of the trellis file `trellis` of the model folder `folder`,
    read with the mapping of unsaved texts `texts` through the package's
    own reversal of the expansion (`period_entries`, `written_at`), so that
    the Workbench keeps no second reading of repeats and templates. The new
    period's stages are compared with those of both neighbors as the
    factory checks a standing mapping, by the stage occurrences of each
    period: the keys it lists that the recipe, whose text is `recipe`, makes
    active there once its ranges are raised and widened for the insertion
    (`_recipe_for_period`), every key it lists where `recipe` is None, a
    trellis file read with no recipe (`add_record_period`), as sets, since
    the order of a period's stages carries no meaning. Where they differ,
    one standing mapping is still kept where `standing(at, keys)`, given,
    answers that the package's check of a standing mapping admits it at
    both new pairs (`trellis.standing_mapping_joins`; unit L, Task 19;
    defect 11 of the UX simulation), and expanded otherwise. Refused with a
    ValueError: an `at` that is no whole number from 1 to the number of
    periods less one, the places between two periods; a trellis file the
    factory refuses, in its own sentence."""
    relative = trellis.relative_to(folder).as_posix()
    try:
        count = len(period_entries(trellis, texts or None))
        if isinstance(at, bool) or not isinstance(at, int) or not 1 <= at < count:
            raise ValueError(
                f"no period is added at {at!r}: {trellis.name} writes periods 0 to "
                f"{count - 1}, and a period is added between two of them or at the earliest end"
            )
        numbers = [_entry_number(trellis, h, texts) for h in range(count)]
        document = entry_value(_text_of(folder, relative, texts))
    except KeyError as error:
        raise ValueError(f"{relative}: {error.args[0]}") from None
    listed = document["periods"]
    entry = numbers[at]
    repeats = tuple(numbers.count(number) for number in range(len(listed)))
    split = at - numbers.index(entry) if numbers[at - 1] == entry else None
    try:
        ranges = (
            {} if recipe is None else _ranges_of(_recipe_for_period(recipe, at, keys, raised=True))
        )
    except (KeyError, ValueError):
        # the recipe's own edit then refuses the gesture, naming the recipe
        ranges = {}
    # the stage occurrences of the old periods[at], now periods[at + 1], of
    # the new period and of periods[at − 1]
    same = (
        _active(_period_keys(trellis, at, texts), ranges, at + 1)
        == _active(set(keys), ranges, at)
        == _active(_period_keys(trellis, at - 1, texts), ranges, at - 1)
    )
    mappings = document.get("inter_connectors")
    if not isinstance(mappings, list) or not mappings or len(mappings) not in (1, count - 1):
        change = "kept"
    elif len(mappings) == 1:
        joined = same or (standing is not None and standing(at, keys))
        change = "kept" if joined else "expanded"
    else:
        change = "copied" if same else "emptied"
    return _Insertion(
        at,
        count,
        entry,
        split,
        repeats[entry],
        isinstance(listed[entry], dict) and "repeat" in listed[entry],
        entry + 1 if split is not None else entry,
        tuple(item.get("template") if isinstance(item, dict) else None for item in listed),
        repeats,
        mappings,
        change,
    )


def _entry_number(trellis: Path, h: int, texts) -> int:
    """The index in the trellis file's `periods` list of the entry that
    writes period `h`, as the package's `written_at` answers it for the key
    `template`, which it places in the trellis file's entry for an entry
    that names a period file and for one written out alike."""
    _, address = written_at(trellis, f"periods[{h}].template", texts or None)
    return int(_ENTRY_ADDRESS.match(address)[1])


def _period_keys(trellis: Path, h: int, texts) -> set | None:
    """The stage keys period `h` of the trellis file `trellis` lists, read
    where the package's `written_at` places its `stages`, the entry's own or
    its period file's, as a list of keys or of one-key mappings, or as a
    mapping of records; None where they cannot be read so."""
    try:
        path, address = written_at(trellis, f"periods[{h}].stages", texts or None)
        listed = entry_value(_unsaved_or_disk(Path(path), texts or {}), address)
    except (OSError, ValueError, KeyError):
        return None
    if isinstance(listed, dict):
        return set(listed)
    if isinstance(listed, list):
        return {
            key for item in listed for key in (item if isinstance(item, dict) else [str(item)])
        }
    return None


def _ranges_of(recipe: str) -> dict:
    """The range `(lo, hi)` of each stage of the recipe's text `recipe`, or
    None for a stage the recipe does not restrict (`_bounds`)."""
    stages = entry_value(recipe, "stages")
    if not isinstance(stages, dict):
        return {}
    return {
        str(stage): _bounds(block.get("periods"))
        for stage, block in stages.items()
        if isinstance(block, dict)
    }


def _active(keys, ranges: dict, h: int) -> set | None:
    """The keys of `keys` that the recipe makes active at period `h`, a key
    whose range `ranges` holds being active within it, as the factory's
    reading of a recipe makes it, and every other key at every period; None
    where `keys` is None, the keys not having been read."""
    if keys is None:
        return None
    return {
        key for key in keys if ranges.get(key) is None or ranges[key][0] <= h <= ranges[key][1]
    }


def _trellis_of_the_folder(folder: Path, texts) -> Path | None:
    """The resolved path of the trellis file the folder's recipe, `spec.yml`
    in the factory's folder, names, the one whose periods answers.yml
    records and whose inter-period list the checklist reads; None where the
    folder holds no such recipe or it names no file so."""
    try:
        return _trellis_named(folder, RECIPE, texts).resolve()
    except (OSError, ValueError):
        return None


def _trellis_with_insertion(text: str, insertion: _Insertion, item: str) -> str:
    """The trellis file's text with the period `item`, its entry, added as
    periods[at] (spec 0.4 §3.6): the entry that writes both neighbors
    first given `repeat: n` where it takes its repeat from its period file
    (`append_to_mapping`; ruling J-P11) and split around the new period
    (`split_entry`), the periods on either side unchanged; the new entry
    placed in the list above the comments over the entry after it
    (`_entry_inserted`); and the inter-period mappings of the two new pairs
    (`_pairs_inserted`)."""
    address = f"periods[{insertion.entry}]"
    if insertion.split is not None:
        if not insertion.written:
            text = append_to_mapping(text, address, "repeat", str(insertion.repeat))
        text = split_entry(text, address, insertion.split)
    text = _entry_inserted(text, insertion.place, item)
    return _pairs_inserted(text, insertion)


def _text_lines(text: str) -> list[str]:
    """The lines of `text`, each with the line break that ends it, the last
    without one where the text does not end with a break; a break as the
    package's reader of YAML files counts one (`_LINE_BREAK`)."""
    lines, start = [], 0
    for found in _LINE_BREAK.finditer(text):
        lines.append(text[start : found.end()])
        start = found.end()
    if start < len(text):
        lines.append(text[start:])
    return lines


def _entry_inserted(text: str, index: int, item: str) -> str:
    """The trellis file's text with the entry `item` placed in its
    `periods` list before the entry at `index` (`insert_in_sequence`), and
    above the comment lines that stand directly over that entry, each a line
    of its own at the column of the entry's dash, so that each comment
    stays over the entry it describes and does not come to stand over the
    new one (unit L, Task 19; defect 11 of the UX simulation). Where the
    list is written in the flow style, or the document read from the moved
    text differs from the one the writer's text reads, the text stands as
    the package's writer wrote it."""
    inserted = insert_in_sequence(text, "periods", index, item)
    before, after = _text_lines(text), _text_lines(inserted)
    count = len(after) - len(before)
    # the index of the line of the new entry's dash, where its value begins
    first = entry_span(inserted, ("periods", index)).line - 1
    if count < 1 or after[:first] != before[:first] or after[first + count :] != before[first:]:
        return inserted
    dash = after[first][: len(after[first]) - len(after[first].lstrip(" "))]
    top = first
    while top > 0 and before[top - 1].startswith(dash + "#"):
        top -= 1
    if top == first:
        return inserted
    moved = "".join(after[:top] + after[first : first + count] + after[top:first] + before[first:])
    return moved if entry_value(moved) == entry_value(inserted) else inserted


def _pairs_inserted(text: str, insertion: _Insertion) -> str:
    """The trellis file's text with the inter-period mappings of an
    insertion as periods[at] (spec 0.4 §3.6): the old pair (at, at−1) becomes
    two pairs, inter_connectors[at−1] and [at]. For a list of one mapping for
    each pair, both new pairs take a copy of the old pair's mapping where
    the new period's stages equal both neighbors' (`copied`), and an empty
    mapping otherwise (`emptied`), the old mapping written over by `{}`
    (`_written_over`; ruling J-P3); every other pair keeps its mapping. For
    one standing mapping and stages that differ from a neighbor's
    (`expanded`), the list becomes one mapping for each pair: each existing
    pair a copy of the standing mapping and each new pair an empty mapping,
    so that the factory, which checks a standing mapping at every pair,
    does not refuse a field the new period lacks. A copy is written as the
    file writes the mapping where it stands on one line (`_item_text`). The
    list written is read back and must equal the list intended; otherwise
    a ValueError names the address."""
    old, mappings = insertion.at - 1, insertion.mappings
    if insertion.change == "kept":
        return text
    if insertion.change == "copied":
        intended = [*mappings[: old + 1], *mappings[old:]]
        text = insert_in_sequence(text, "inter_connectors", old, _item_text(text, old))
    else:
        if insertion.change == "emptied":
            intended = [*mappings[:old], {}, {}, *mappings[old + 1 :]]
            text = _written_over(text, ("inter_connectors", old), "{}")
        else:
            standing, pairs = mappings[0], insertion.count - 1
            intended = [standing] * old + [{}, {}] + [standing] * (pairs - 1 - old)
            if pairs == 1:
                text = _written_over(text, ("inter_connectors", 0), "{}")
            else:
                copied = _item_text(text, 0)
                for _ in range(pairs - 2):
                    text = insert_in_sequence(text, "inter_connectors", 0, copied)
                text = insert_in_sequence(text, "inter_connectors", old, "{}")
        text = insert_in_sequence(text, "inter_connectors", old, "{}")
    if entry_value(text, "inter_connectors") != intended:
        raise _not_written_over(("inter_connectors",))
    return text


def _item_text(text: str, index: int) -> str:
    """The text of the mapping inter_connectors[index] of the trellis file's
    text, as the file writes it where it stands on one line, and otherwise
    in YAML's flow style, so that it is written as one item of the list."""
    path = ("inter_connectors", index)
    start, end = _span_indices(text, entry_span(text, path))
    if _LINE_BREAK.search(text, start, end) is None:
        return text[start:end]
    return yaml.safe_dump(
        entry_value(text, path), default_flow_style=True, sort_keys=False, width=float("inf")
    ).strip()


def _answers_with_insertion(
    text: str,
    insertion: _Insertion,
    item: str,
    folder: Path,
    trellis: Path,
    records: bool,
    recipe: str,
    moved: list,
) -> str:
    """answers.yml's text after a period, recorded as `item`, is added as
    periods[at] of the trellis file `trellis` (spec 0.4 §3.6; J-D23). Where
    `records` holds, that trellis file being the one the folder's recipe
    names, and answers.yml's `periods` record its entries one for one, the
    same file and the same number of periods each, the entry is split and
    the new entry placed as in the trellis file; where `records` holds, an
    expansion of one standing mapping is recorded
    (`_with_expansion_record`), and so is each range and range key of the
    recipe `recipe`, its path from the model folder, that the insertion
    changed, `moved` holding for each its address before and after
    (`_with_moved_record`). The addresses of `required.connectors` whose
    file is `trellis` are renumbered with it (`_renumbered`), through
    `replace_entry`. Where answers.yml's periods record other entries, a
    variant's trellis file among them, they are left as they stand. A text
    that reads as no mapping, an empty file, a comment alone or a list, is
    refused with a ValueError, as the earliest end's writer refuses it."""
    document = entry_value(text)
    if not isinstance(document, dict):
        raise ValueError("the file holds no mapping")
    listed = document.get("periods")
    mirrors = (
        isinstance(listed, list)
        and len(listed) == len(insertion.templates)
        and all(
            isinstance(entry, dict) and entry.get("file") == template and entry.get("repeat") == n
            for entry, template, n in zip(listed, insertion.templates, insertion.repeats)
        )
    )
    if records and mirrors:
        if insertion.split is not None:
            text = split_entry(text, f"periods[{insertion.entry}]", insertion.split)
        text = insert_in_sequence(text, "periods", insertion.place, item)
    required = document.get("required")
    marks = required.get("connectors") if isinstance(required, dict) else None
    for number, mark in enumerate(marks if isinstance(marks, list) else []):
        if not (_is_mark(mark) and (folder / mark["file"]).resolve() == trellis.resolve()):
            continue
        renumbered = _renumbered(mark["address"], insertion)
        if renumbered != mark["address"]:
            text = replace_entry(text, ("required", "connectors", number, "address"), renumbered)
    if records and insertion.change == "expanded":
        text = _with_expansion_record(text, document)
    if records and moved:
        text = _with_moved_record(text, document, folder, recipe, moved)
    return text


def _renumbered(address: str, insertion: _Insertion) -> str:
    """An address of the trellis file renumbered with an insertion, so that
    it names the entry it named: an entry of `periods` at or after the new
    entry's place moves by one, or by two where an entry was split, the
    split entry's address naming its first part; a mapping of a list of one
    mapping for each pair at or above the new index moves by one, the
    old pair's address naming the new pair (at, at−1). Any other address,
    one standing mapping's among them, is kept."""
    found = _LISTED_ADDRESS.fullmatch(address)
    if found is None:
        return address
    name, index, rest = found[1], int(found[2]), found[3]
    if name == "periods" and index >= insertion.place:
        index += 1 if insertion.split is None else 2
    elif name == "inter_connectors" and insertion.change in ("copied", "emptied"):
        index += index >= insertion.at
    return f"{name}[{index}]{rest}"


def _with_expansion_record(text: str, document: dict) -> str:
    """answers.yml's text, whose document is `document`, recording that the
    inter-period list was expanded from one standing mapping, as the
    top-level entry `expanded: {inter_connectors: true}` (decision 39;
    J-D23): appended where the file writes no `expanded`, the key added
    or its value written `true` where `expanded` is a mapping without it;
    a record that stands is kept."""
    held = document.get("expanded")
    if "expanded" not in document:
        return append_to_mapping(text, (), "expanded", "{inter_connectors: true}")
    if isinstance(held, dict) and "inter_connectors" in held:
        if held["inter_connectors"] is True:
            return text
        return replace_entry(text, ("expanded", "inter_connectors"), True)
    return append_to_mapping(text, "expanded", "inter_connectors", "true")


def _with_moved_record(text: str, document: dict, folder: Path, recipe: str, moved: list) -> str:
    """answers.yml's text, whose document is `document`, recording the
    ranges and range keys of the recipe `recipe`, its path from the model
    folder `folder`, that a period added between two periods changed, so
    that the checklist names them as the status line does (spec 0.4 §3.6):
    the top-level list `moved` of `{file, address}`, each address the one
    the recipe writes after the insertion, `moved` holding for each change
    its address before and after. An entry that names a range key the
    insertion raised again is renumbered with it, through `replace_entry`,
    as `required.connectors` is; a change not yet recorded is added, the
    list appended where the file writes no `moved` (`append_to_mapping`)
    and extended otherwise (`append_to_sequence`), which refuses a `moved`
    that is no list. The checklist lists each entry while it stands, and
    the author removes the record once the schedules keyed by period index
    are checked."""
    held = document.get("moved")
    target = (folder / recipe).resolve()
    after = dict(moved)
    recorded = set()
    for number, mark in enumerate(held if isinstance(held, list) else []):
        if not (_is_mark(mark) and (folder / mark["file"]).resolve() == target):
            continue
        address = after.get(mark["address"], mark["address"])
        if address != mark["address"]:
            text = replace_entry(text, ("moved", number, "address"), address)
        recorded.add(address)
    items = [
        f"{{file: {_quoted(recipe)}, address: {_quoted(new)}}}"
        for new in dict.fromkeys(new for _, new in moved)
        if new not in recorded
    ]
    if not items:
        return text
    if "moved" not in document:
        return append_to_mapping(text, (), "moved", f"[{', '.join(items)}]")
    for item in items:
        text = append_to_sequence(text, "moved", item)
    return text


def _recipe_for_period(text: str, h: int | None, keys, *, raised: bool) -> str:
    """The recipe's text for a new period at index `h` with the stage keys
    `keys` (spec 0.4 §3.6): where `raised`, the period being added between
    two periods, every range and range key at or above `h` raised by one
    (`_ranges_raised`); then the range of each of `keys` widened to include
    `h` (`range_widened`). The text as given where `h` is None, the trellis
    file not being read."""
    if h is None:
        return text
    if raised:
        text = _ranges_raised(text, h)
    for key in keys:
        text, _ = range_widened(text, key, h)
    return text


def _ranges_raised(text: str, h: int) -> str:
    """The recipe's text with every bound of a stage's `periods: [lo, hi]`
    and every range key `lo-hi` of its binding lists, `calibration`,
    `settings` and `methods`, that lies at or above `h` raised by one, so
    that each binding keeps the periods it bound after a period is added as
    periods[h] (spec 0.4 §3.6): a bound through `replace_entry`, a key through
    `_written_over` (ruling J-P3), the keys of one list from the highest
    down, so that no key is written while another holds it. Only the recipe
    is read; no calibration file is."""
    stages = entry_value(text, "stages")
    for stage, block in stages.items() if isinstance(stages, dict) else ():
        if not isinstance(block, dict):
            continue
        bounds = _bounds(block.get("periods"))
        for index, bound in enumerate(bounds or ()):
            if bound >= h:
                text = replace_entry(text, ("stages", stage, "periods", index), bound + 1)
        for kind in KINDS:
            lists = block.get(kind)
            ranges = [
                (int(found[1]), int(found[2]), name)
                for name in (lists if isinstance(lists, dict) else ())
                if isinstance(name, str) and (found := _RANGE_KEY.fullmatch(name))
            ]
            for lo, hi, name in sorted(ranges, reverse=True):
                if hi >= h:
                    moved = f"{lo + (lo >= h)}-{hi + 1}"
                    text = _written_over(text, ("stages", stage, kind, name), moved, key=True)
    return text


def _bounds(value) -> tuple[int, int] | None:
    """`(lo, hi)` of a range `periods: [lo, hi]` as the factory reads one,
    two integers with lo ≤ hi; None for any other value, which the factory
    refuses in its own sentence."""
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(bound, int) and not isinstance(bound, bool) for bound in value)
        and value[0] <= value[1]
    ):
        return value[0], value[1]
    return None


def _range_note(path: tuple, old, new) -> str:
    """The status line's part of a range changed, in the form of brief §5:
    `stages.housing.periods: [1, 3] now [1, 4]`."""
    return f"{_dotted(path)}: [{old[0]}, {old[1]}] now [{new[0]}, {new[1]}]"


def _moved(before: str, after: str) -> list[tuple[str, str, str]]:
    """The ranges and the range keys of the recipe that its new text
    `after` changed from its text `before`, in the recipe's order (spec 0.4
    §3.6, "names every range and key changed in the status line and the
    checklist"): for each, its address in `before` and its address in
    `after`, which differ for a range key raised,
    `stages.cons.calibration.3-5` and `stages.cons.calibration.4-6`, and the
    status line's part, each range written once from the range read to the
    range written: `stages.housing.periods: [1, 3] now [1, 4]` for a range
    and `stages.cons.calibration: 3-5 now 4-6` for a range key."""
    old, new = entry_value(before, "stages"), entry_value(after, "stages")
    if not isinstance(old, dict) or not isinstance(new, dict):
        return []
    found = []
    for stage, block in old.items():
        changed = new.get(stage)
        if not isinstance(block, dict) or not isinstance(changed, dict):
            continue
        if block.get("periods") != changed.get("periods"):
            path = ("stages", stage, "periods")
            note = _range_note(path, block["periods"], changed["periods"])
            found.append((_dotted(path), _dotted(path), note))
        for kind in KINDS:
            names, renamed = block.get(kind), changed.get(kind)
            if isinstance(names, dict) and isinstance(renamed, dict):
                found += [
                    (
                        _dotted(("stages", stage, kind, name)),
                        _dotted(("stages", stage, kind, other)),
                        f"{_dotted(('stages', stage, kind))}: {name} now {other}",
                    )
                    for name, other in zip(names, renamed)
                    if name != other
                ]
    return found


def _split_note(file: str, insertion: _Insertion, name: str) -> str:
    """The status line's part of the trellis file after an insertion, in
    the form of brief §5: `trellis.yml, periods: repeat 6 split 3,
    period.mid.yml, 3` where an entry was split around the new period
    `name`, and `trellis.yml, periods: {template: period.mid.yml, repeat: 1}
    written, periods 3` where the new entry stands between two entries."""
    if insertion.split is None:
        return _written_note(file, "periods", f"{{template: {name}, repeat: 1}}", (insertion.at,))
    rest = insertion.repeat - insertion.split
    return f"{file}, periods: repeat {insertion.repeat} split {insertion.split}, {name}, {rest}"


def _pairs_note(insertion: _Insertion) -> str | None:
    """The status line's part of the inter-period mappings after an
    insertion, in the form of brief §5: `inter_connectors[2] replaced`
    where the mapping of the pair split was replaced by those of the two new
    pairs, `inter_connectors: one mapping expanded to 6` where one standing
    mapping was expanded; None where the list was kept."""
    if insertion.change == "expanded":
        return f"inter_connectors: one mapping expanded to {insertion.count}"
    if insertion.change in ("copied", "emptied"):
        return f"inter_connectors[{insertion.at - 1}] replaced"
    return None


def _restriction_after(insertion: _Insertion) -> str:
    """The text for the restriction's input after an insertion, since the
    indices a restriction names have moved (spec 0.4 §3.6): the new period
    and the periods beside it in the new numbering, `periods 2–4` for
    periods[3], where the trellis then holds more than the periods the
    trellis load opens whole (`trellis.OPEN_PERIODS_WHOLE`, six), as it
    opens a longer trellis on part of it; the empty text otherwise."""
    # imported here, not at the module's top, so that the module trellis.py
    # may import this one without a cycle (unit J's plan, Task 14)
    from bellman_workbench.trellis import OPEN_PERIODS_WHOLE

    if insertion.count + 1 > OPEN_PERIODS_WHOLE:
        return f"periods {insertion.at - 1}–{insertion.at + 1}"
    return ""


def _written_over(text: str, path: tuple, written: str, *, key: bool = False) -> str:
    """`text` with the characters of the value at `path`, a tuple of keys
    and indices, where `entry_span` places them, written over by `written`,
    the text of a value such as `{}`; with `key`, the characters of the key
    that holds that value written over by the key `written`, within the
    key's quotes where it is quoted. It writes the two edits of an insertion
    that no writer of the package writes, a mapping replaced by another and
    a range key raised (ruling J-P3; J-D27). The result is accepted only
    where the package's reader (`entry_value`) reads it as the document read
    before with that one value, or that one key, changed and every other
    entry as it was; otherwise, and where the text does not read, a
    ValueError names the address, the file's layout there being one that
    cannot be written over as text."""
    intended = copy.deepcopy(entry_value(text))
    holder = intended
    for step in path[:-1]:
        holder = holder[step]
    if key:
        node = _key_node(text, path)
        quote = node.style if node.style in ("'", '"') else ""
        start, end = node.start_mark.index, node.end_mark.index
        new = text[:start] + quote + written + quote + text[end:]
        entries = list(holder.items())
        holder.clear()
        holder.update((written if name == path[-1] else name, value) for name, value in entries)
    else:
        start, end = _span_indices(text, entry_span(text, path))
        new = text[:start] + written + text[end:]
        holder[path[-1]] = entry_value(written)
    try:
        accepted = entry_value(new) == intended
    except ValueError:
        accepted = False
    if not accepted:
        raise _not_written_over(path)
    return new


def _not_written_over(path: tuple) -> ValueError:
    """The ValueError of `_written_over`, or of an inter-period list not
    written as intended, naming the address `path`."""
    return ValueError(
        f"the layout of the file at {_dotted(path)} cannot be written over as text; change "
        "the entry there by hand"
    )


def _key_node(text: str, path: tuple):
    """The node of the key that holds the value at `path`, a tuple of keys,
    as the YAML composer reads the text, with its position and its style;
    a KeyError where the text writes no such key."""
    node = yaml.compose(text, Loader=yaml.SafeLoader)
    for step in path[:-1]:
        node = _child(node, step)
    names = [
        name
        for name, _ in (node.value if isinstance(node, yaml.MappingNode) else ())
        if isinstance(name, yaml.ScalarNode) and name.value == path[-1]
    ]
    if not names:
        raise KeyError(f"the file writes no key {path[-1]!r} at {_dotted(path[:-1])!r}")
    return names[0]


def _span_indices(text: str, span) -> tuple[int, int]:
    """The indices in `text` of the first character of the `EntrySpan`
    `span` and of the character just after its last, its lines counted as
    the YAML reader counts them and its columns in code points, a byte
    order mark not counted, as `entry_span` counts them."""
    starts = [0, *(found.end() for found in _LINE_BREAK.finditer(text))]
    indices = []
    for line, column in ((span.line, span.column), (span.end_line, span.end_column)):
        index, counted = starts[line - 1], 1
        while counted < column:
            counted += text[index] != "\ufeff"
            index += 1
        indices.append(index)
    return indices[0], indices[1]


def _dotted(path) -> str:
    """An address written from its keys and indices, as the factory's
    refusals write one: keys joined by "." and indices in brackets."""
    return "".join(
        f"[{step}]" if isinstance(step, int) else ("." if number else "") + str(step)
        for number, step in enumerate(path)
    )


def _answers_with_stage(text: str, key: str, record: str) -> str:
    """answers.yml's text with the stage `key` added to `stages`, its value
    the text `record` (`_answers_record`), and the names of its three slots
    to `required.slots` (`_answers_with_slots`)."""
    text = append_to_mapping(text, "stages", key, record)
    return _answers_with_slots(text, key)


def _answers_record(template: StageTemplate) -> str:
    """The record of the template a stage is copied from, which answers.yml
    holds under the stage's key, in flow style: for a template of the
    corpus, its id, `{template: "<id>"}`; for a stage folder of the disk
    (unit K's decision K-D26), the path the author gave and the SHA-256 of
    each file the stage brings, its stage file and then its companions in
    the order of `KINDS`, each by its name in that folder and read as it
    stands now, `{origin: "<path>", sha256: {"port.bl": "<digest>",
    "methods.yml": "<digest>"}}`, so that the folder can later be compared
    with the files the copy was made from."""
    if template.origin is None:
        return f"{{template: {_quoted(template.id)}}}"
    brought = (template.stage, *(path for kind in KINDS for path in template.companions[kind]))
    digests = ", ".join(
        f"{_quoted(path.name)}: {_quoted(hashlib.sha256(path.read_bytes()).hexdigest())}"
        for path in brought
    )
    return f"{{origin: {_quoted(template.origin)}, sha256: {{{digests}}}}}"


def _answers_with_slots(text: str, key: str) -> str:
    """answers.yml's text with the names of the three slots of the stage
    `key` added to `required.slots`, the record of the slots written, which
    the checklist does not read (unit K's decision K-D29)."""
    for kind in KINDS:
        text = append_to_sequence(text, "required.slots", slot_name(key, kind))
    return text


# --- a stage, a period or a file removed (unit L, Task 25; AAS, L-D18) ---

# the words of the status line's part that names the files and folders a
# removal deletes from disk once the files that named them are saved
DELETED_ON_SAVE = "deleted on save"


def _document_of(path: Path, texts: dict):
    """The document of the YAML file `path`, read from `texts`, the mapping
    of unsaved texts by a file's resolved path as a string, where it holds
    the file and from disk otherwise, by the package's reader of YAML files
    (`entry_value`), which keeps a document's tag under `__yaml_tag__`; None
    where the file cannot be read so."""
    try:
        return entry_value(_unsaved_or_disk(path, texts))
    except (OSError, UnicodeDecodeError, ValueError, KeyError):
        return None


def _source_files(base: Path, name) -> list[Path]:
    """The files a source name of a binding list or of a recipe's
    `registry` may stand for, resolved, as the package's reader tries them
    under its registry folder `base` (`_registry_file` of
    `bellman.factory.recipe`): `<name>.yml`, `<name>.yaml` and the name as
    written, or the name as written alone where it ends in `.yml` or
    `.yaml`; none for a slot, a name written `$<slot>`, and for a value that
    is no text."""
    if not isinstance(name, str) or not name.strip() or name.startswith("$"):
        return []
    written = base / name
    if written.suffix in _YAML_SUFFIXES:
        return [written.resolve()]
    return [Path(f"{written}{suffix}").resolve() for suffix in _YAML_SUFFIXES] + [
        written.resolve()
    ]


def _binding_names(record) -> list:
    """The source names a stage's row of a recipe, or its record in a
    trellis file written as records, writes in its binding lists, in the
    order of `KINDS`: each entry of a kind's list, written alone, as a list,
    or as lists under `all` and range keys."""
    names = []
    for kind in KINDS:
        lists = record.get(kind) if isinstance(record, dict) else None
        for listed in lists.values() if isinstance(lists, dict) else (lists,):
            names += listed if isinstance(listed, list) else [listed]
    return names


def _record_files(base: Path, record) -> list[Path]:
    """The files a stage's row of a recipe, or its record in a trellis
    file, names, resolved from the folder `base` that its paths are read
    from, each once: the stage file under `stage`, then each source of its
    binding lists in their order (`_source_files`)."""
    if not isinstance(record, dict):
        return []
    found = [(base / record["stage"]).resolve()] if isinstance(record.get("stage"), str) else []
    for name in _binding_names(record):
        found += _source_files(base, name)
    return list(dict.fromkeys(found))


def named_files(folder, texts=None) -> frozenset:
    """Every file the model folder `folder` names in the files its trellis
    is read from (unit L, Task 25; AAS, L-D18), each a resolved path, read
    from `texts`, the mapping of unsaved texts by a file's resolved path as
    a string, where it holds a file and from disk otherwise: in each recipe
    of the factory's folder (`model._role`), the trellis file under
    `trellis`, each row's stage file and binding sources, and the sources of
    its `registry`; in each trellis file a recipe names or the factory's
    folder holds under the tag `!trellis`, the period file of each entry's
    `template` and the stage file and sources of each record its periods
    write, a period file's included; and the parents of each source named
    (`parent:`), as the package's reader follows them. A source name stands
    for each file the package's reader may read for it (`_source_files`),
    and a file that cannot be read names nothing. The variants of the folder
    are recipes of it, so that a file one variant names is named."""
    root = Path(folder).resolve()
    factory = root / FACTORY_FOLDER
    texts = texts or {}
    try:
        listed = sorted(path for path in factory.iterdir() if path.is_file())
    except OSError:
        listed = []
    named, trellises = set(), {}
    for path in listed:
        role = model._role(path.relative_to(root))
        document = _document_of(path, texts) if role in ("recipe", "trellis") else None
        if not isinstance(document, dict):
            continue
        if role == "trellis" and document.get("__yaml_tag__") == "trellis":
            trellises[path.resolve()] = document
        if role != "recipe":
            continue
        rows = document.get("stages")
        for row in rows.values() if isinstance(rows, dict) else ():
            named.update(_record_files(factory, row))
        registry = document.get("registry")
        for names in registry.values() if isinstance(registry, dict) else ():
            for name in names if isinstance(names, list) else [names]:
                named.update(_source_files(factory, name))
        if isinstance(document.get("trellis"), str):
            trellis = (factory / document["trellis"]).resolve()
            named.add(trellis)
            if trellis not in trellises:
                trellises[trellis] = _document_of(trellis, texts)
    for trellis, document in trellises.items():
        entries = document.get("periods") if isinstance(document, dict) else None
        for entry in entries if isinstance(entries, list) else ():
            if not isinstance(entry, dict):
                continue
            places = [(trellis.parent, entry)]
            if isinstance(entry.get("template"), str):
                period = (trellis.parent / entry["template"]).resolve()
                named.add(period)
                places.append((period.parent, _document_of(period, texts)))
            for base, written in places:
                records = written.get("stages") if isinstance(written, dict) else None
                for record in records.values() if isinstance(records, dict) else ():
                    named.update(_record_files(base, record))
    return frozenset(named | _parents(factory, named, texts))


def _parents(factory: Path, named: set, texts: dict) -> set[Path]:
    """The source files the files `named` name as their parents, and theirs
    in turn, each `parent:` read as the package's reader reads it, a source
    name under the factory's folder `factory` (`_source_files`)."""
    found, waiting = set(), [path for path in named if path.suffix in _YAML_SUFFIXES]
    while waiting:
        document = _document_of(waiting.pop(), texts)
        parent = document.get("parent") if isinstance(document, dict) else None
        for path in _source_files(factory, parent):
            if path not in found and path not in named:
                found.add(path)
                waiting.append(path)
    return found


def _unnamed(root: Path, candidates, named) -> tuple[str, ...]:
    """The paths of `candidates`, files and folders as resolved paths,
    relative to the resolved model folder `root` in posix form, of those
    that lie within `root`, are not `root` itself, and that none of the
    files `named` is or lies within, each once, in their order. A file
    outside the folder is never listed or deleted, since `named_files` does
    not read the files of other folders that may name it (unit L, Task 25;
    L-I360)."""
    found = [
        Path(os.path.relpath(path, root)).as_posix()
        for path in candidates
        if path != root
        and path.is_relative_to(root)
        and not any(other == path or other.is_relative_to(path) for other in named)
    ]
    return tuple(dict.fromkeys(found))


def deletable(folder, paths, texts=None) -> tuple[str, ...]:
    """The paths of `paths`, files and folders relative to the model folder
    `folder`, that stand on disk, resolve within the folder, and that no
    file of the folder names, read both from `texts`, the mapping of the
    unsaved texts, and from disk (`named_files`): those a save may delete
    (unit L, Task 25; AAS, L-D18), since neither a buffer nor the disk then
    names them, so that a file another row names is never deleted, though
    the removal that listed it stands unsaved in another file. A path that
    resolves outside the folder, through `..` or a symbolic link, is never
    answered (`_unnamed`)."""
    root = Path(folder).resolve()
    named = named_files(root, texts) | named_files(root)
    candidates = [(root / path).resolve() for path in paths if (root / path).exists()]
    return _unnamed(root, candidates, named)


def removable_files(folder, texts=None) -> tuple[str, ...]:
    """The files and folders of the factory's folder of `folder` that the
    tree offers to delete (unit L, Task 25; AAS, L-D18), by their paths from
    the model folder: each period file, `period.yml` or `period.<x>.yml`,
    that no trellis file names, and each stage folder, `stages/<name>/`,
    within which no file of the folder names a file, in name order, read
    from `texts` and from disk as `deletable` reads them; the files a
    removal or an undone addition left behind among them."""
    root = Path(folder).resolve()
    factory = root / FACTORY_FOLDER
    found = []
    for place, kept in (
        (factory, lambda path: path.is_file() and _PERIOD_FILE.fullmatch(path.name)),
        (factory / "stages", lambda path: path.is_dir()),
    ):
        try:
            found += [path for path in place.iterdir() if kept(path)]
        except OSError:
            continue
    paths = [Path(os.path.relpath(path, root)).as_posix() for path in sorted(found)]
    return deletable(root, paths, texts)


def deletion_names(folder, paths) -> list[str]:
    """The files and folders `paths`, relative to the model folder `folder`,
    as the status line names them: by their paths from the factory's
    folder where they lie within it, as a new file is named (`_new_note`),
    a folder with "/" at its end, `stages/bequest/`."""
    root = Path(folder)
    names = []
    for path in paths:
        within = path.startswith(f"{FACTORY_FOLDER}/")
        name = posixpath.relpath(path, FACTORY_FOLDER) if within else path
        names.append(f"{name}/" if (root / path).is_dir() else name)
    return names


def _deleted_note(folder: Path, deleted) -> str:
    """The status line's part that names the files and folders a removal
    deletes on save, `deleted on save: stages/bequest/` (`deletion_names`)."""
    return f"{DELETED_ON_SAVE}: {', '.join(deletion_names(folder, deleted))}"


def without_stage(text: str, address: str, key: str) -> str | None:
    """The YAML text `text` with the stage `key` taken out of the stages
    written at `address`, by the package's writers, every other character
    kept: from a mapping of records, the key with its record
    (`remove_from_mapping`); from a list, the item that is the key or a
    mapping of that key alone (`remove_from_sequence`), or the key of a
    mapping of the list that writes other keys too. None where those stages
    hold no `key`. A writer's refusal is its ValueError, and an address the
    text no longer holds a KeyError (unit K's decision K-D14; unit L, Task
    25)."""
    value = entry_value(text, address)
    if isinstance(value, dict):
        return remove_from_mapping(text, address, key) if key in value else None
    for at, item in enumerate(value if isinstance(value, list) else ()):
        if (not isinstance(item, dict) and str(item) == key) or (
            isinstance(item, dict) and list(item) == [key]
        ):
            return remove_from_sequence(text, address, at)
        if isinstance(item, dict) and key in item:
            return remove_from_mapping(text, f"{address}[{at}]", key)
    return None


def _without_stages(text: str, addresses, key: str) -> str:
    """`text` with the stage `key` taken out of the stages at each address
    of `addresses` that holds it (`without_stage`)."""
    for address in addresses:
        text = without_stage(text, address, key) or text
    return text


def _answers_without_stage(text: str, key: str) -> str:
    """answers.yml's text with its records of the stage `key` taken out by
    the package's writers, as `add_stage` and `new_stage` write them: its
    entry under `stages`, the names of its three slots in `required.slots`
    (`slot_name`), and the key in the `stages` of a period record, the
    terminal period's of a folder `new trellis` wrote."""
    document = entry_value(text)
    if not isinstance(document, dict):
        raise ValueError("the file holds no mapping")
    if isinstance(document.get("stages"), dict) and key in document["stages"]:
        text = remove_from_mapping(text, "stages", key)
    required = document.get("required")
    slots = required.get("slots") if isinstance(required, dict) else None
    names = {slot_name(key, kind) for kind in KINDS}
    for at in reversed(range(len(slots) if isinstance(slots, list) else 0)):
        if slots[at] in names:
            text = remove_from_sequence(text, "required.slots", at)
    periods = document.get("periods")
    for number, period in enumerate(periods if isinstance(periods, list) else ()):
        if isinstance(period, dict) and isinstance(period.get("stages"), list):
            text = without_stage(text, f"periods[{number}].stages", key) or text
    return text


def remove_stage(folder, key: str, *, recipe: str = RECIPE, texts=None) -> Added:
    """The stage `key` removed from the model of the folder `folder` (unit
    L, Task 25; AAS, L-D18; spec 0.4 §3.5 by its inverse), answered and not
    written: as edits, the row of `key` taken out of the `stages` of the
    recipe `recipe` (`remove_from_mapping`), the key taken out of every
    period's list that holds it, the trellis file's entries and the period
    files, at the places the package's `written_at` answers for
    `periods[h].stages` (`_stage_places`, `without_stage`), and, where the
    folder holds answers.yml, its records of the stage
    (`_answers_without_stage`); each file read from `texts`, the mapping of
    unsaved texts by a file's resolved path as a string, where it holds it,
    and from disk otherwise, and edited as text, its comments and layout
    kept. The connectors that name the stage's fields are the trellis
    module's to take out, from the joins the package answers
    (`trellis.stage_removal_edit`).

    `deleted` lists, by their paths from the model folder, the stage's
    folder `stages/<key>/` and each file the row names outside it, its
    stage file and its calibration, settings and methods files, that lie
    within the model folder and that no file of the folder names once the
    edits stand (`named_files`, `_unnamed`), the
    variants of the folder and the other rows included; the Workbench
    deletes them when the files that named them are saved. The notes are
    the status line's parts in the form of J-D39: `spec.yml, stages: port
    removed`, each list's `period.yml, stages: port removed, periods 0–5`,
    answers.yml's records, and last `deleted on save: stages/port/,
    settings/port.yml`. Refused with a ValueError: a folder without the
    recipe, or whose recipe names no trellis file of the factory's folder;
    a key the recipe's `stages` do not hold; a trellis file the factory
    refuses, in its own sentence; an entry a writer cannot take out as
    text."""
    folder = Path(folder).resolve()
    recipe_path = factory_path(recipe)
    _require(folder, (recipe_path,))
    trellis = _trellis_named(folder, recipe, texts)
    row, own = _row_removal(folder, key, recipe, texts)
    edits = {recipe_path: own[recipe_path]}
    notes = [f"{recipe}, stages: {key} removed"]
    grouped = {}
    for relative, address, periods in _stage_places(trellis, texts):
        grouped.setdefault(relative, []).append((address, periods))
    for relative, places in grouped.items():
        text = _text_of(trellis.parent, relative, texts)
        held = [(address, periods) for address, periods in places if _lists(text, address, key)]
        if not held:
            continue
        addresses = [address for address, _ in held]
        edits[factory_path(relative)] = functools.partial(
            _without_stages, addresses=addresses, key=key
        )
        notes += [
            f"{relative}, {address}: {key} removed, periods {_runs(periods)}"
            for address, periods in held
        ]
    if ANSWERS in own:
        edits[ANSWERS] = own[ANSWERS]
    made, read = _edits(folder, edits, texts)
    answers = str((folder / ANSWERS).resolve())
    if answers in made:
        notes.append(f"{ANSWERS}: the records of {key} removed")
    # the stage's folder first, then each file the row names outside it
    own = (folder / factory_path(stage_folder(key))).resolve()
    candidates = [own] if own.is_dir() else []
    candidates += [
        path
        for path in _record_files(folder / FACTORY_FOLDER, row)
        if path.is_file() and not path.is_relative_to(own)
    ]
    deleted = _unnamed(folder, candidates, named_files(folder, {**(texts or {}), **made}))
    if deleted:
        notes.append(_deleted_note(folder, deleted))
    return Added((), made, read, tuple(notes), None, deleted)


def _row_removal(folder: Path, key: str, recipe: str, texts) -> tuple[object, dict]:
    """The row of the stage `key` as the recipe `recipe` of the model folder
    `folder` writes it, read from `texts` where it holds the recipe and from
    disk otherwise, and the edits that take the row out, by the path of
    each file relative to the folder: the recipe's row
    (`remove_from_mapping`) and, where the folder holds answers.yml, its
    records of the stage (`_answers_without_stage`). Refused with a
    ValueError naming the recipe: a key the recipe's `stages` do not hold,
    or a recipe that cannot be read."""
    recipe_path = factory_path(recipe)
    try:
        row = entry_value(_text_of(folder, recipe_path, texts), ("stages", key))
    except KeyError:
        raise ValueError(f"{recipe_path}: the recipe holds no stage {key!r}") from None
    except ValueError as error:
        raise ValueError(f"{recipe_path}: {error}") from None
    edits = {recipe_path: functools.partial(remove_from_mapping, address="stages", key=key)}
    if (folder / ANSWERS).is_file():
        edits[ANSWERS] = functools.partial(_answers_without_stage, key=key)
    return row, edits


def without_row(folder, key: str, *, recipe: str = RECIPE, texts=None) -> Added:
    """The row of the stage `key` taken out of the recipe `recipe` of the
    model folder `folder`, answered and not written, for the removal of a
    stage occurrence from the last period list that holds the stage (unit
    N, Task 5; N-D8): the recipe then names no stage that no period holds,
    which the factory refuses under `recipe-template-agreement`
    (`spec-factory.md` §2.6). The edits are the recipe's row and, where the
    folder holds answers.yml, its records of the stage (`_row_removal`),
    each file read from `texts`, the mapping of unsaved texts by a file's
    resolved path as a string, where it holds it, and from disk otherwise;
    the notes, `spec.yml, stages: port removed` and answers.yml's part as
    `remove_stage` writes them. No file is listed to delete on save, since
    the gesture names one period list and not the stage's files; the tree
    offers the stage's folder for removal once no file names it
    (`removable_files`). Refused with a ValueError: a folder without the
    recipe, or a key the recipe does not hold."""
    folder = Path(folder).resolve()
    _require(folder, (factory_path(recipe),))
    _, edits = _row_removal(folder, key, recipe, texts)
    made, read = _edits(folder, edits, texts)
    notes = [f"{recipe}, stages: {key} removed"]
    if str((folder / ANSWERS).resolve()) in made:
        notes.append(f"{ANSWERS}: the records of {key} removed")
    return Added((), made, read, tuple(notes))


def _lists(text: str, address: str, key: str) -> bool:
    """Whether the stages written at `address` of the YAML text `text` hold
    the stage `key`, as `without_stage` takes it out: a key of a mapping of
    records, an item of a list, or a key of a mapping of the list; a place
    that cannot be read holds none."""
    try:
        value = entry_value(text, address)
    except (KeyError, ValueError):
        return False
    if isinstance(value, dict):
        return key in value
    return any(
        key in item if isinstance(item, dict) else str(item) == key
        for item in (value if isinstance(value, list) else ())
    )


class _Removal(NamedTuple):
    """What a period removed from the trellis file changes, read before any
    text is written (unit L, Task 25): `h`, the index of the period removed;
    `count`, the number of periods before the removal; `entry`, the index in
    the file's `periods` list of the entry that writes periods[h]; `repeat`,
    the number of periods that entry writes, so that the entry goes where it
    writes the one period and its repeat falls by one otherwise; `written`,
    whether the entry writes `repeat` itself; `templates` and `repeats`,
    each entry's `template` and number of periods; and `pair`, the index of
    the inter-period mapping that goes where the file writes one mapping for
    each adjacent pair, None otherwise."""

    h: int
    count: int
    entry: int
    repeat: int
    written: bool
    templates: tuple
    repeats: tuple
    pair: int | None


def _removal(folder: Path, trellis: Path, h, texts) -> _Removal:
    """The `_Removal` of periods[h] of the trellis file `trellis` of the
    model folder `folder`, read with the mapping of unsaved texts `texts`
    through the package's own reversal of the expansion (`period_entries`,
    `written_at`), as `_insertion` reads an insertion. The two adjacent
    pairs of an inner period become one, and of the two mappings of a list
    of one for each pair the one of the pair from the earlier period into
    the removed one goes, `inter_connectors[h]`, the mapping out of it
    standing for the new pair, whose writing period then lists the stages
    the removed one listed where those neighbors are alike; at either end
    the one pair that touches the removed period goes. Refused with a
    ValueError: an `h` that is no period of the file; a file that writes one
    period alone, since a trellis holds one period or more; a trellis file
    the factory refuses, in its own sentence."""
    relative = trellis.relative_to(folder).as_posix()
    try:
        count = len(period_entries(trellis, texts or None))
        if isinstance(h, bool) or not isinstance(h, int) or not 0 <= h < count:
            raise ValueError(f"{trellis.name} writes no period {h!r}")
        if count == 1:
            raise ValueError(
                f"{trellis.name} writes periods[0] alone, and a trellis holds one period or more"
            )
        numbers = [_entry_number(trellis, p, texts) for p in range(count)]
        document = entry_value(_text_of(folder, relative, texts))
    except KeyError as error:
        raise ValueError(f"{relative}: {error.args[0]}") from None
    listed = document["periods"]
    entry = numbers[h]
    repeats = tuple(numbers.count(number) for number in range(len(listed)))
    mappings = document.get("inter_connectors")
    pairs = count - 1
    per_pair = isinstance(mappings, list) and pairs > 1 and len(mappings) == pairs
    return _Removal(
        h,
        count,
        entry,
        repeats[entry],
        isinstance(listed[entry], dict) and "repeat" in listed[entry],
        tuple(item.get("template") if isinstance(item, dict) else None for item in listed),
        repeats,
        min(h, pairs - 1) if per_pair else None,
    )


def _trellis_without_period(text: str, removal: _Removal) -> str:
    """The trellis file's text with periods[h] removed (unit L, Task 25):
    the entry that writes it taken out of `periods` where it writes the one
    period (`remove_from_sequence`), and otherwise its `repeat` lowered by
    one, written into the entry where it takes its repeat from its period
    file (`replace_entry`, `append_to_mapping`; ruling J-P11); and the
    mapping of the pair that goes taken out of `inter_connectors`
    (`_Removal.pair`)."""
    address = ("periods", removal.entry)
    if removal.repeat == 1:
        text = remove_from_sequence(text, "periods", removal.entry)
    elif removal.written:
        text = replace_entry(text, (*address, "repeat"), removal.repeat - 1)
    else:
        text = append_to_mapping(text, address, "repeat", str(removal.repeat - 1))
    if removal.pair is not None:
        text = remove_from_sequence(text, "inter_connectors", removal.pair)
    return text


def _ranges_lowered(text: str, h: int) -> str:
    """The recipe's text after periods[h] is removed (unit L, Task 25; spec
    0.4 §3.6 in reverse, `_ranges_raised`): each bound of a stage's
    `periods: [lo, hi]` above `h`, and its upper bound at `h`, lowered by
    one, so that each range keeps the periods it held but the one removed,
    through `replace_entry`; a range that held periods[h] alone is left as
    written, the package then reading the stage as it reads any recipe. Each
    range key `lo-hi` of a binding list lowered in the same way, through
    `_written_over`, the keys of one list from the lowest up, so that no key
    is written while another holds it, and the list of a key that held
    periods[h] alone taken out (`remove_from_mapping`), since it binds no
    period that stands. Only the recipe is read; no calibration file is."""
    stages = entry_value(text, "stages")
    for stage, block in stages.items() if isinstance(stages, dict) else ():
        if not isinstance(block, dict):
            continue
        bounds = _bounds(block.get("periods"))
        if bounds is not None and bounds != (h, h):
            lowered = (bounds[0] - (bounds[0] > h), bounds[1] - (bounds[1] >= h))
            for index, (old, new) in enumerate(zip(bounds, lowered)):
                if new != old:
                    text = replace_entry(text, ("stages", stage, "periods", index), new)
        for kind in KINDS:
            lists = block.get(kind)
            ranges = [
                (int(found[1]), int(found[2]), name)
                for name in (lists if isinstance(lists, dict) else ())
                if isinstance(name, str) and (found := _RANGE_KEY.fullmatch(name))
            ]
            for lo, hi, name in sorted(ranges):
                if (lo, hi) == (h, h):
                    text = remove_from_mapping(text, ("stages", stage, kind), name)
                elif hi >= h:
                    moved = f"{lo - (lo > h)}-{hi - 1}"
                    text = _written_over(text, ("stages", stage, kind, name), moved, key=True)
    return text


def _lowered_notes(text: str, h: int) -> list[str]:
    """The status line's parts of the ranges and range keys of the recipe's
    text `text` that `_ranges_lowered` changes after periods[h] is removed,
    in the recipe's order, by the same rule: `stages.housing.periods: [1, 3]
    now [1, 2]`, `stages.cons.calibration: 3-5 now 2-4`, and
    `stages.cons.calibration: 3-3 removed` for a list taken out with its
    key."""
    stages = entry_value(text, "stages")
    notes = []
    for stage, block in stages.items() if isinstance(stages, dict) else ():
        if not isinstance(block, dict):
            continue
        bounds = _bounds(block.get("periods"))
        if bounds is not None and bounds != (h, h):
            lowered = (bounds[0] - (bounds[0] > h), bounds[1] - (bounds[1] >= h))
            if lowered != bounds:
                notes.append(_range_note(("stages", stage, "periods"), bounds, lowered))
        for kind in KINDS:
            lists = block.get(kind)
            written = _dotted(("stages", stage, kind))
            for name in lists if isinstance(lists, dict) else ():
                found = _RANGE_KEY.fullmatch(name) if isinstance(name, str) else None
                if found is None or int(found[2]) < h:
                    continue
                lo, hi = int(found[1]), int(found[2])
                if (lo, hi) == (h, h):
                    notes.append(f"{written}: {name} removed")
                else:
                    notes.append(f"{written}: {name} now {lo - (lo > h)}-{hi - 1}")
    return notes


def _answers_without_period(
    text: str, removal: _Removal, folder: Path, trellis: Path, records: bool
) -> str:
    """answers.yml's text after periods[h] is removed from the trellis file
    `trellis` (unit L, Task 25; spec 0.4 §3.6 in reverse,
    `_answers_with_insertion`): where `records` holds, that trellis file
    being the one the folder's recipe names, and answers.yml's `periods`
    record its entries one for one, the same file and the same number of
    periods each, the entry is taken out or its `repeat` lowered as in the
    trellis file; and the marks of `required.connectors` whose file is
    `trellis` are renumbered with it, a mark of the entry or the mapping
    taken out going with it (`_renumbered_after`). Where answers.yml's
    periods record other entries, they are left as they stand. A text that
    reads as no mapping is refused with a ValueError."""
    document = entry_value(text)
    if not isinstance(document, dict):
        raise ValueError("the file holds no mapping")
    listed = document.get("periods")
    mirrors = (
        isinstance(listed, list)
        and len(listed) == len(removal.templates)
        and all(
            isinstance(entry, dict) and entry.get("file") == template and entry.get("repeat") == n
            for entry, template, n in zip(listed, removal.templates, removal.repeats)
        )
    )
    if records and mirrors:
        if removal.repeat == 1:
            text = remove_from_sequence(text, "periods", removal.entry)
        else:
            text = replace_entry(text, ("periods", removal.entry, "repeat"), removal.repeat - 1)
    required = document.get("required")
    marks = required.get("connectors") if isinstance(required, dict) else None
    gone = []
    for number, mark in enumerate(marks if isinstance(marks, list) else []):
        if not (_is_mark(mark) and (folder / mark["file"]).resolve() == trellis.resolve()):
            continue
        renumbered = _renumbered_after(mark["address"], removal)
        if renumbered is None:
            gone.append(number)
        elif renumbered != mark["address"]:
            text = replace_entry(text, ("required", "connectors", number, "address"), renumbered)
    for number in reversed(gone):
        text = remove_from_sequence(text, "required.connectors", number)
    return text


def _renumbered_after(address: str, removal: _Removal) -> str | None:
    """An address of the trellis file renumbered after a removal, so that
    it names the entry it named: an entry of `periods` after an entry taken
    out moves back by one, and a mapping of a list of one mapping for each
    pair after the mapping taken out; None for an address within the entry
    or the mapping taken out. Any other address is kept."""
    found = _LISTED_ADDRESS.fullmatch(address)
    if found is None:
        return address
    name, index, rest = found[1], int(found[2]), found[3]
    if name == "periods" and removal.repeat == 1:
        if index == removal.entry:
            return None
        index -= index > removal.entry
    elif name == "inter_connectors" and removal.pair is not None:
        if index == removal.pair:
            return None
        index -= index > removal.pair
    return f"{name}[{index}]{rest}"


def _restriction_after_removal(removal: _Removal) -> str:
    """The text for the restriction's input after a removal, since the
    indices a restriction names have moved (spec 0.4 §3.6 in reverse,
    `_restriction_after`): the periods on either side of the place of the
    period removed, in the new numbering, `periods 2–3` for periods[3] or
    `periods 0` for the terminal one, where the trellis then holds more
    than the periods the trellis load opens whole
    (`trellis.OPEN_PERIODS_WHOLE`, six); the empty text otherwise."""
    from bellman_workbench.trellis import OPEN_PERIODS_WHOLE

    if removal.count - 1 <= OPEN_PERIODS_WHOLE:
        return ""
    lo, hi = max(removal.h - 1, 0), min(removal.h, removal.count - 2)
    return f"periods {lo}–{hi}" if lo < hi else f"periods {lo}"


def remove_period(folder, h: int, *, recipe: str = RECIPE, texts=None) -> Added:
    """Period `h` removed from the trellis file the recipe `recipe` of the
    folder `folder` names (unit L, Task 25; AAS, L-D18; spec 0.4 §3.6 by its
    inverse), answered and not written: as edits, of the trellis file, the
    entry that writes the period taken out, or its repeat lowered where it
    writes several periods, and the mapping of a pair that goes where the
    file writes one mapping for each adjacent pair (`_removal`,
    `_trellis_without_period`); of the recipe, its ranges and range keys
    lowered as `add_period` raises them, in reverse (`_ranges_lowered`); and
    of answers.yml, where the folder holds it, its record of the entry and
    the addresses of its required connectors (`_answers_without_period`);
    each file read from `texts`, the mapping of unsaved texts by a file's
    resolved path as a string, where it holds it, and from disk otherwise,
    and edited as text. `deleted` lists the period file of the entry taken
    out, by its path from the model folder, where it lies within the model
    folder and no file of the folder names it once the edits stand
    (`named_files`, `_unnamed`); `restriction` is the
    text for the restriction's input (`_restriction_after_removal`).

    The notes are the status line's parts: `trellis.yml, periods[1]
    removed, periods 6` or `trellis.yml, periods[0].repeat: 6 now 5`;
    `trellis.yml, inter_connectors[3] removed`; each range and key changed,
    the recipe's file named before the first; `deleted on save:
    period.young.yml`; and `restriction periods 2–3` or `restriction
    emptied`. Refused with a ValueError: a folder without the recipe, or
    whose recipe names no trellis file of the factory's folder; an `h` that
    is no period, or the one period of the trellis; a trellis file the
    factory refuses, in its own sentence; an entry a writer cannot take out
    or write over as text."""
    folder = Path(folder).resolve()
    recipe_path = factory_path(recipe)
    _require(folder, (recipe_path,))
    trellis = _trellis_named(folder, recipe, texts)
    removal = _removal(folder, trellis, h, texts)
    trellis_path = factory_path(trellis.name)
    edits = {
        trellis_path: functools.partial(_trellis_without_period, removal=removal),
        recipe_path: functools.partial(_ranges_lowered, h=h),
    }
    made, read = _edits(folder, edits, texts)
    if (folder / ANSWERS).is_file():
        answers_edit = functools.partial(
            _answers_without_period,
            removal=removal,
            folder=folder,
            trellis=trellis,
            records=_trellis_of_the_folder(folder, texts) == trellis.resolve(),
        )
        answered, answered_from = _edits(folder, {ANSWERS: answers_edit}, texts)
        made.update(answered)
        read.update(answered_from)
    if removal.repeat == 1:
        notes = [f"{trellis.name}, periods[{removal.entry}] removed, periods {h}"]
    else:
        notes = [
            f"{trellis.name}, periods[{removal.entry}].repeat: {removal.repeat} now "
            f"{removal.repeat - 1}"
        ]
    if removal.pair is not None:
        notes.append(f"{trellis.name}, inter_connectors[{removal.pair}] removed")
    resolved = str((folder / recipe_path).resolve())
    if resolved in made:
        lowered = _lowered_notes(read[resolved], h)
        notes += [
            f"{recipe}, {part}" if number == 0 else part for number, part in enumerate(lowered)
        ]
    template = removal.templates[removal.entry]
    candidates = []
    if removal.repeat == 1 and isinstance(template, str):
        period = (trellis.parent / template).resolve()
        candidates = [period] if period.is_file() else []
    deleted = _unnamed(folder, candidates, named_files(folder, {**(texts or {}), **made}))
    if deleted:
        notes.append(_deleted_note(folder, deleted))
    restriction = _restriction_after_removal(removal)
    notes.append(f"restriction {restriction}" if restriction else "restriction emptied")
    return Added((), made, read, tuple(notes), restriction, deleted)


# --- a trellis written as records (spec 0.4 §3.5; unit J, Task 13) ---


def record_stages(trellis_file, texts=None) -> tuple[str, ...]:
    """The keys of the stages that any period of the trellis file
    `trellis_file` writes as records, `<key>: {stage: …, calibration: …,
    settings: …, methods: …}` in a `stages` mapping, each once, in the
    order of the periods and then of the file: the folder's own stages,
    which the stage list offers for a trellis written as records with no
    recipe (spec 0.4 §3.5). Each period's `stages` are read where the
    package's `written_at` places them (`_stage_places`), from `texts`, the
    mapping of unsaved texts by a file's resolved path as a string, where it
    holds the file, and from disk otherwise; a period whose `stages` are a
    list of keys adds none. No key where the file cannot be read so."""
    trellis = Path(trellis_file).resolve()
    try:
        keys = {}
        for relative, address, _ in _stage_places(trellis, texts):
            keys.update(dict.fromkeys(_records_at(trellis, relative, address, texts)))
    except (OSError, ValueError, KeyError):
        return ()
    return tuple(key for key in keys if isinstance(key, str))


def add_record_stage(trellis_file, key: str, h: int, texts=None) -> Added:
    """The folder stage `key` added to period `h` of the trellis file
    `trellis_file`, a trellis written as records (spec 0.4 §3.5), answered
    and not written: the record that the first period writing `key` writes
    for it, the stage file and its bindings, copied as the file writes it,
    the characters `entry_span` answers, so that its paths and its layout
    are kept, and added at the end of the `stages` mapping that writes
    period `h` (`append_to_mapping`), which every period that mapping
    writes then holds. A record's paths are read relative to the trellis
    file's folder wherever the record stands (`load_trellis`), so the copy
    keeps their meaning. The mapping stands where the package's `written_at`
    places the period's `stages`, in the trellis file's entry in the
    corpus's examples, and each file is read from `texts`, the mapping of
    unsaved texts by a file's resolved path as a string, where it holds it,
    and from disk otherwise. The `Added` holds no new file, the edited text
    by the file's resolved path, the text it was made from, and the status
    line's part in the form of brief §5, `trellis.port-cons.yml,
    periods[0].stages: disc written, periods 0`; where that mapping holds
    `key` already, it holds no edit and no note. No recipe and no
    answers.yml is read or written. Refused with a ValueError: a folder
    without the trellis file; a period the file does not write; a key that
    no period writes as a record; a mapping to which the record cannot be
    added as text, or a copy that does not read as the record copied."""
    trellis = Path(trellis_file).resolve()
    _require(trellis.parent, (trellis.name,))
    places = _stage_places(trellis, texts)
    target = next((place for place in places if h in place[2]), None)
    if isinstance(h, bool) or not isinstance(h, int) or target is None:
        raise ValueError(f"{trellis.name} writes no period {h!r}")
    relative, address, reached = target
    if key in _records_at(trellis, relative, address, texts):
        return Added((), {}, {}, ())
    source = next(
        (
            (path, where)
            for path, where, _ in places
            if key in _records_at(trellis, path, where, texts)
        ),
        None,
    )
    if source is None:
        raise ValueError(f"no period of {trellis.name} writes a record for {key!r}")
    copied = _text_of(trellis.parent, source[0], texts)
    record = _keyed(source[1], key)
    start, end = _span_indices(copied, entry_span(copied, record))
    edit = functools.partial(
        _with_record,
        address=address,
        key=key,
        written=copied[start:end],
        record=entry_value(copied, record),
    )
    made, read = _edits(trellis.parent, {relative: edit}, texts)
    return Added((), made, read, (_written_note(relative, address, key, reached),))


def add_record_period(trellis_file, at: int | None = None, texts=None) -> Added:
    """One more period of the trellis file `trellis_file`, a trellis
    written as records (spec 0.4 §§3.5, 3.6), answered and not written: an
    inline entry of `periods` whose `stages` are the text of a neighbor's,
    `stages:` followed by the neighbor's own lines (`_stages_item`), and
    whose `connectors` is one empty mapping, `connectors: [{}]`, which a
    drag then fills; no label is asked, since no period file is written
    (J-D24). The file is read from `texts`, the mapping of unsaved texts by
    a file's resolved path as a string, where it holds it, and from disk
    otherwise.

    With `at` None the period is the earliest: the entry is added at the
    end of `periods` with the stages of the earliest period, and an empty
    mapping at the end of `inter_connectors` where that list holds more
    than one mapping, one for each adjacent pair (`_pair_appended`), as
    `add_period` adds one. With `at` the index h the new period takes, from
    1 to the number of periods less one, the entry is placed between
    periods[h] and periods[h−1] with the stages of periods[h−1], the
    neighbor on its later side in time, the terminal side, as `add_period`
    places one (`_insertion`, `_trellis_with_insertion`): the entry with
    `repeat: n` that writes both neighbors split around it, and the
    mappings of the two new pairs given or one standing mapping expanded,
    every stage the file lists being active at every period, since no
    recipe restricts one.

    The `Added` holds no new file, the edited text by the file's resolved
    path, the text it was made from, and the status line's parts in the
    forms of brief §5: `trellis.port-cons.yml, periods: an entry with the
    stages of periods[5] written, periods 6`, or for a split
    `trellis.port-cons.yml, periods: repeat 6 split 3, an entry with the
    stages of periods[2], 3`; then `inter_connectors[2] replaced` or
    `inter_connectors: one mapping expanded to 6`; and after an insertion
    `restriction periods 2–4` or `restriction emptied`, with `restriction`
    the text for the restriction's input (ruling J-P21). No recipe and no
    answers.yml is read or written. Refused with a ValueError: a folder
    without the trellis file; an `at` that is no place between two periods;
    a trellis file the factory refuses; an entry that a writer cannot
    extend or write over as text, or a new entry that does not read as the
    stages copied and one empty connector mapping."""
    trellis = Path(trellis_file).resolve()
    _require(trellis.parent, (trellis.name,))
    places = _stage_places(trellis, texts)
    count = sum(len(periods) for *_, periods in places)
    if at is None:
        insertion, h = None, count - 1
    else:
        # the stage keys of the terminal side's neighbor, which the new
        # period copies; none where `at` names no period, which
        # `_insertion` then refuses
        whole = isinstance(at, int) and not isinstance(at, bool)
        keys = (_period_keys(trellis, at - 1, texts) if whole else None) or set()
        insertion = _insertion(trellis.parent, trellis, at, keys, texts, None)
        h = at - 1
    relative, address, _ = next(place for place in places if h in place[2])
    copied = _text_of(trellis.parent, relative, texts)
    edit = functools.partial(
        _trellis_with_inline_entry,
        insertion=insertion,
        item=_stages_item(copied, address),
        intended={"stages": entry_value(copied, address), "connectors": [{}]},
    )
    made, read = _edits(trellis.parent, {trellis.name: edit}, texts)
    written = f"an entry with the stages of periods[{h}]"
    if insertion is None:
        return Added((), made, read, (_written_note(trellis.name, "periods", written, (count,)),))
    if insertion.split is None:
        notes = [_written_note(trellis.name, "periods", written, (at,))]
    else:
        notes = [_split_note(trellis.name, insertion, written)]
    notes += [part for part in (_pairs_note(insertion),) if part is not None]
    restriction = _restriction_after(insertion)
    notes.append(f"restriction {restriction}" if restriction else "restriction emptied")
    return Added((), made, read, tuple(notes), restriction)


def _stage_places(trellis: Path, texts) -> list[tuple[str, str, tuple[int, ...]]]:
    """Each place at which the trellis file `trellis`, a resolved path,
    writes the `stages` of its periods, in the order of their first period:
    the file, by its path from the trellis file's folder, the address in
    it, and the periods whose stages it writes. A period's place is the one
    the package's `written_at` answers for `periods[h].stages`, the entry's
    own or the period file's, read through `texts`, so that the Workbench
    keeps no second reading of repeats and templates. A trellis file the
    factory refuses is refused in its own sentence."""
    places = {}
    for h in range(len(period_entries(trellis, texts or None))):
        path, address = written_at(trellis, f"periods[{h}].stages", texts or None)
        relative = Path(os.path.relpath(path, trellis.parent)).as_posix()
        places.setdefault((relative, address), []).append(h)
    return [(relative, address, tuple(periods)) for (relative, address), periods in places.items()]


def _records_at(trellis: Path, relative: str, address: str, texts) -> dict:
    """The `stages` mapping of records at `address` of the file `relative`,
    a path from the folder of the trellis file `trellis`, read from `texts`
    where it holds the file; empty where the stages written there are no
    mapping, a list of keys."""
    listed = entry_value(_text_of(trellis.parent, relative, texts), address)
    return listed if isinstance(listed, dict) else {}


def _keyed(address: str, key: str) -> str:
    """The address of the entry `key` of the mapping at `address`, the key
    written in quotes in brackets, as the package's addresses write a key
    that holds a "." or a bracket, `periods[1].stages['disc']`."""
    quote = '"' if "'" in key else "'"
    return f"{address}[{quote}{key}{quote}]"


def _with_record(text: str, address: str, key: str, written: str, record) -> str:
    """`text` with the entry `<key>: <written>` added at the end of the
    `stages` mapping at `address` (`append_to_mapping`), `written` being
    the text of a record as another period writes it and `record` that
    record as the package's reader reads it; a copy that does not read as
    `record` is refused with the package's ValueError of a layout that
    cannot be extended as text."""
    new = append_to_mapping(text, address, key, written)
    if entry_value(new, _keyed(address, key)) != record:
        raise _not_extended(address)
    return new


def _stages_item(text: str, address: str) -> str:
    """The text of an item of `periods` that writes the `stages` at
    `address` of `text` as the file writes them: `stages:` and the line
    break that ends it, followed by every line from the stages' first line
    to their last, each with its indentation, where the stages begin on a
    line of their own, as a block mapping of records does, so that the item
    reads as `{stages: …}` alone and in its place in the list wherever its
    lines stand deeper than the new entry's keys; `stages: ` followed by
    their characters where they begin on the line of their key, as a flow
    mapping does."""
    start, end = _span_indices(text, entry_span(text, address))
    breaks = list(_LINE_BREAK.finditer(text, 0, start))
    line = breaks[-1].end() if breaks else 0
    if breaks and not text[line:start].strip(" "):
        return "stages:" + breaks[-1].group() + text[line:end]
    return "stages: " + text[start:end]


def _trellis_with_inline_entry(
    text: str, insertion: _Insertion | None, item: str, intended: dict
) -> str:
    """The trellis file's text with the inline entry whose `stages` the
    item `item` writes (`_stages_item`) added to `periods`: at the end,
    with the mapping of the new pair (`_pair_appended`), where `insertion`
    is None; otherwise at the place an insertion gives it, the entry that
    writes both neighbors split and the mappings of the new pairs written
    (`_trellis_with_insertion`). The entry is then given `connectors: [{}]`
    (`append_to_mapping`), and must read as `intended`, the stages copied
    and one empty connector mapping; otherwise the package's ValueError of
    a layout that cannot be extended as text names the entry."""
    if insertion is None:
        place = len(entry_value(text, "periods"))
        text = _pair_appended(append_to_sequence(text, "periods", item))
    else:
        place = insertion.place
        text = _trellis_with_insertion(text, insertion, item)
    text = append_to_mapping(text, ("periods", place), "connectors", "[{}]")
    if entry_value(text, ("periods", place)) != intended:
        raise _not_extended(f"periods[{place}]")
    return text


def _not_extended(address: str) -> ValueError:
    """The ValueError of a copy that the file's layout at `address` does not
    admit, in the words of the package's text writers."""
    return ValueError(
        f"the layout of the file at {address} cannot be extended as text; add the entry there "
        "by hand"
    )


# --- the notebook beside the Workbench (spec 0.4 §5.9) ---

# The template of the notebook `write_notebook` writes: a notebook of format
# 4 with five code cells, the first cell in two forms, each marked in its
# metadata under `_FORM_MARK` by the kind of source it reads, `recipe` or
# `trellis` (`recipe.Source`), then the cells that print each stage
# occurrence's sheet, the digests of its inputs and its methods.
NOTEBOOK_TEMPLATE = Path(__file__).resolve().parent / "public" / "notebook" / "template.ipynb"
# the key of a first cell's metadata that holds the kind of source it reads
_FORM_MARK = "bellman_workbench"
# the placeholder in the first cell for the source's path from `notebooks/`
_SOURCE_PLACEHOLDER = "{{source}}"


def notebook_file(folder) -> str:
    """The path, relative to the model folder `folder`, of the notebook
    `write_notebook` writes there, `notebooks/<folder's name>.ipynb`, beside
    `declaration/` (spec 0.4 §5.9)."""
    return posixpath.join("notebooks", f"{Path(folder).resolve().name}.ipynb")


def write_notebook(folder, source: str, kind: str) -> str | None:
    """Writes the notebook `notebook_file(folder)` under the model folder
    `folder` where none exists, and answers its path relative to the
    folder; answers None and writes nothing where the file exists, since
    the notebook is the economist's from then on (spec 0.4 §5.9; brief
    rule 7; review 11; R-D41). The notebook is `NOTEBOOK_TEMPLATE` with the
    form of its first cell for a source of the kind `kind`, `recipe` or
    `trellis` (`recipe.Source`), whose placeholder is replaced by the path
    of the source `source`, given relative to the folder, from
    `notebooks/`. It holds no digest and no text of a file: its cells read
    them when the notebook is run. A kind for which the template holds no
    form is refused with a ValueError naming it."""
    folder = Path(folder).resolve()
    relative = notebook_file(folder)
    if (folder / relative).exists():
        return None
    text = _notebook_text(posixpath.relpath(source, posixpath.dirname(relative)), kind)
    if not model.save_file(model.open_folder(folder), relative, text, None).saved:
        return None
    return relative


def _notebook_text(path: str, kind: str) -> str:
    """The text of the notebook for a source of the kind `kind` at `path`,
    its path from `notebooks/`: the cells of `NOTEBOOK_TEMPLATE`, of which
    the first cell's form marked `kind` is kept and the other form left
    out; the kept form's mark is removed and its placeholder replaced by
    `path`, written as the inside of a double-quoted string. The text is in
    the JSON form in which nbformat writes a notebook: one space of
    indentation and sorted keys."""
    notebook = json.loads(NOTEBOOK_TEMPLATE.read_text(encoding="utf-8"))
    cells = [
        cell
        for cell in notebook["cells"]
        if cell["metadata"].get(_FORM_MARK, {"kind": kind})["kind"] == kind
    ]
    if not any(_FORM_MARK in cell["metadata"] for cell in cells):
        raise ValueError(f"the notebook's template holds no first cell for the kind {kind!r}")
    # the inside of the path's JSON string, in which a quote or a backslash
    # is escaped as a Python string reads it
    written = json.dumps(path, ensure_ascii=False)[1:-1]
    for cell in cells:
        cell["metadata"].pop(_FORM_MARK, None)
        cell["source"] = [line.replace(_SOURCE_PLACEHOLDER, written) for line in cell["source"]]
    notebook["cells"] = cells
    return json.dumps(notebook, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
