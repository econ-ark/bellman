"""The one layout of a model folder, checked on every folder under
`applications/`, and the trellises the recipes load, compared with digests
of their answers as they were when this module was last run as a script.

The layout is that of §2 of the project's issue on the layout of the
application folders, which AAS adopted on 2 October 2026. A folder under
`applications/` that holds a stage file or a file the language reads holds
`README.md` and a folder `declaration/`. Under `declaration/` stand the
recipe, the trellis and period files, the calibration and settings
files and one folder per stage, `declaration/stages/<key>/`, which holds the
stage file `<key>.bl`, its note `<key>.md`, its addition `methods.bl` and a
replacing selection `methods.<variant>.bl`, and nothing else (decision S7-W2
of specification 0.7); a `.bl` file stands nowhere else under `declaration/`,
and the folder `declaration/methods/` of the YAML methods files and the
block files of specification 0.6 is retired (S7-W6). The top of the folder
holds `README.md`, `economics.md`
and the folders `declaration/`, `code/`, `notebooks/`, `paper/`,
`reference/`, `results/` and `tests/`; the contents of the last six are not
examined here. No path has a component `derived` or `__pycache__`.

The recipes of `RECIPES` are compared with the fixture
`tests/fixtures/layout_base_trellises.json`, which holds digests of their
answers, and not the answers themselves, as they were when this module was
last run as a script. Running it as a script, from `packages/bellman`,

    PYTHONPATH=. python tests/test_layout.py

writes the fixture again from the current answers, so that a deliberate
change of a recipe or of a file a recipe reads is recorded once.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

import pytest
from conftest import ROOT

from bellman.refusals import FactoryError
from bellman.stage import load_stage
from bellman.trellis import load_recipe

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "layout_base_trellises.json"

# the recipes whose answers the fixture holds, each by its path in the
# repository
RECIPES = (
    "applications/durables/declaration/spec.yml",
    "applications/durables/declaration/spec.two-stages.yml",
    "applications/pension-retirement/declaration/spec.yml",
    "applications/retirement-choice/declaration/spec.yml",
    "applications/housing-frictions/declaration/spec.yml",
    "applications/benhabib-2019/declaration/spec.yml",
    "packages/bellman/tests/corpus/de-la-croix-pommeret-2021/spec.yml",
    "packages/bellman/tests/corpus/branching/examples/cagetti-denardi-2006/registry/spec.yml",
)

# the suffixes of the files the language reads: a stage file or an addition,
# and a recipe, trellis, period, calibration or settings file
READ = (".bl", ".yml", ".yaml")
# the files a model folder holds at its top, beside its folders
TOP_FILES = ("README.md", "economics.md")
# the folders beside `declaration/` whose contents are not examined; `paper`
# holds the files Bellman Workbench's button `paper` writes (spec 0.4 §5.5,
# decision 38)
UNEXAMINED = ("code", "notebooks", "paper", "reference", "results", "tests")
# how a file at a model folder's top is known as one the language reads
# (`_read_at_the_top`): a recipe, trellis or period file by the beginning of
# its name, and a calibration or settings file by a stem that is its kind or
# ends in `_<kind>`, as the earlier layout named these files and as Bellman
# Workbench's tree gives them their roles
READ_NAMES = ("spec", "trellis", "period")
KINDS = ("calibration", "settings")
# the name of an addition in a stage folder: `methods.bl`, or a replacing
# selection `methods.<variant>.bl` (decision S7-W2)
ADDITION = re.compile(r"methods(?:\.[^.]+)?\.bl")
# the three sentences of the rules under `declaration/`
STAGE_FOLDER = ("declaration/stages/ holds one folder per stage, declaration/stages/<key>/, "
                "holding <key>.bl, <key>.md, methods.bl and methods.<variant>.bl and nothing else")
STAGE_FILE = ("a stage file stands at declaration/stages/<key>/<key>.bl, and an addition beside "
              "it as methods.bl or methods.<variant>.bl")
RETIRED_METHODS = ("declaration/methods/ is retired: an addition stands in its stage's folder as "
                   "methods.bl or methods.<variant>.bl")


# --- the layout ---


def files_under_applications():
    """Every file under `applications/` that git tracks and that stands on
    disk, by its path from the repository's root; an untracked file is not
    listed, so that a checkout's scratch files do not enter the check."""
    listed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "-z", "--", "applications"],
        capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    return sorted({name for name in listed if name and (ROOT / name).is_file()})


def layout_faults(paths):
    """The faults against the one layout of the files `paths`, each a path
    from the repository's root under `applications/`, one sentence each."""
    faults = [f"{path}: a generated path, with a component derived or __pycache__"
              for path in paths if {"derived", "__pycache__"} & set(PurePosixPath(path).parts)]
    folders = {}
    for path in paths:
        parts = PurePosixPath(path).parts
        if len(parts) > 2:
            folders.setdefault(parts[1], []).append(PurePosixPath(*parts[2:]))
    for folder, files in sorted(folders.items()):
        if not any(file.suffix in READ for file in files):
            continue
        where = f"applications/{folder}"
        if not any(file.parts[0] == "declaration" for file in files):
            faults.append(f"{where}: no declaration/ folder")
        if PurePosixPath("README.md") not in files:
            faults.append(f"{where}: no README.md")
        for file in files:
            faults.extend(f"{where}/{file}: {fault}" for fault in _faults_of(file))
        keys = {file.parts[2] for file in files if file.parts[:2] == ("declaration", "stages")
                and len(file.parts) > 3}
        faults.extend(f"{where}/declaration/stages/{key}/: no stage file {key}.bl"
                      for key in sorted(keys)
                      if PurePosixPath("declaration", "stages", key, f"{key}.bl") not in files)
    return faults


def _read_at_the_top(file):
    """Whether the file `file`, standing at a model folder's top, is one the
    language reads: a `.bl` file, a stage file or an addition, or a `.yml` or
    `.yaml` file whose name begins with one of `READ_NAMES`, or whose stem is
    one of `KINDS` or ends in `_` and one of them. The check reads names
    alone; another file is read only where a recipe names it."""
    if file.suffix == ".bl":
        return True
    return file.suffix in READ and (
        file.name.startswith(READ_NAMES)
        or any(file.stem == kind or file.stem.endswith(f"_{kind}") for kind in KINDS))


def _faults_of(file):
    """The faults of one file of a model folder, `file` its path from the
    folder. A file at the folder's top that the language does not read
    (`_read_at_the_top`), such as the record `answers.yml` that Bellman
    Workbench's "new trellis" writes there, breaks the rule of the top and
    is not sent under `declaration/`."""
    first = file.parts[0]
    if first == "declaration":
        if len(file.parts) > 2 and file.parts[1] == "stages":
            key = file.parts[2]
            if len(file.parts) == 4 and (file.name in (f"{key}.bl", f"{key}.md")
                                         or ADDITION.fullmatch(file.name)):
                return []
            return [STAGE_FOLDER]
        if len(file.parts) > 2 and file.parts[1] == "methods":
            return [RETIRED_METHODS]
        if file.suffix == ".bl":
            return [STAGE_FILE]
        return []
    if len(file.parts) == 1 and file.name in TOP_FILES:
        return []
    if len(file.parts) > 1 and first in UNEXAMINED:
        return []
    if file.suffix in READ and (len(file.parts) > 1 or _read_at_the_top(file)):
        return ["a file the language reads stands under declaration/"]
    if file.suffix == ".md":
        return ["a markdown file outside declaration/ is README.md or economics.md at the "
                "folder's top, and a stage's note stands in its stage folder"]
    if len(file.parts) == 1:
        return ["the top of a model folder holds README.md, economics.md and folders alone"]
    return [f"the folder {first}/ is none of declaration/, "
            f"{', '.join(name + '/' for name in UNEXAMINED)}"]


def test_every_application_has_the_one_layout():
    """Every folder under `applications/` that holds a stage file or a file
    the language reads has `declaration/` and `README.md`; a stage's file, its
    note and its additions stand in its stage folder; a recipe, a trellis,
    period, calibration or settings file stands under `declaration/`; the
    folder's top holds no other file than `README.md` and `economics.md`; and
    no path is generated."""
    faults = layout_faults(files_under_applications())
    assert faults == [], "\n".join([f"{len(faults)} faults against the one layout:"] + faults)


def test_a_file_at_a_folders_top_is_refused_by_the_rule_it_breaks():
    """At a model folder's top, a file the language reads is sent under
    `declaration/`: a stage file or an addition, a recipe, trellis or period
    file, and a calibration or settings file named after its kind, as the
    earlier layout named them. Any other file is refused by the rule of the
    folder's top, among them `answers.yml`, the `.gitignore` that Bellman
    Workbench's "new trellis" writes there and a YAML methods file of the
    retired form, which the language no longer reads. The paths are planted,
    not read from git."""
    top = "the top of a model folder holds README.md, economics.md and folders alone"
    read = "a file the language reads stands under declaration/"
    planted = {
        ".gitignore": top,
        "answers.yml": top,
        "calibration.yml": read,
        "cons.bl": read,
        "cons_methods.yml": top,
        "methods.bl": read,
        "notes.yaml": top,
        "period.young.yml": read,
        "settings.yml": read,
        "spec.two-stages.yml": read,
        "spec.yml": read,
        "trellis.yml": read,
    }
    paths = ["applications/demo/README.md", "applications/demo/declaration/spec.yml"]
    paths += [f"applications/demo/{name}" for name in planted]
    assert layout_faults(sorted(paths)) == [
        f"applications/demo/{name}: {sentence}" for name, sentence in sorted(planted.items())
    ]


def test_an_addition_stands_in_its_stage_folder_and_the_methods_folder_is_retired():
    """A stage folder holds the stage file, its note, its addition
    `methods.bl` and a replacing selection `methods.<variant>.bl`, and refuses
    the retired `methods.yml` and any other name; a `.bl` file in another
    folder of `declaration/` is refused by the rule of the stage file; and
    every file under `declaration/methods/`, the folder of the retired YAML
    methods files and block files, is refused by the rule that retires it
    (decisions S7-W2 and S7-W6). The paths are planted, not read from git."""
    paths = [
        "applications/demo/README.md",
        "applications/demo/declaration/blocks/cons_egm.bl",
        "applications/demo/declaration/methods/cons.yml",
        "applications/demo/declaration/methods/cons_egm.bl",
        "applications/demo/declaration/methods/egm/cons_egm.bl",
        "applications/demo/declaration/spec.yml",
        "applications/demo/declaration/stages/cons/cons.bl",
        "applications/demo/declaration/stages/cons/cons.md",
        "applications/demo/declaration/stages/cons/methods.bl",
        "applications/demo/declaration/stages/cons/methods.vfi.bl",
        "applications/demo/declaration/stages/cons/methods.yml",
        "applications/demo/declaration/stages/cons/notes.md",
    ]
    assert layout_faults(paths) == [
        f"applications/demo/declaration/blocks/cons_egm.bl: {STAGE_FILE}",
        f"applications/demo/declaration/methods/cons.yml: {RETIRED_METHODS}",
        f"applications/demo/declaration/methods/cons_egm.bl: {RETIRED_METHODS}",
        f"applications/demo/declaration/methods/egm/cons_egm.bl: {RETIRED_METHODS}",
        f"applications/demo/declaration/stages/cons/methods.yml: {STAGE_FOLDER}",
        f"applications/demo/declaration/stages/cons/notes.md: {STAGE_FOLDER}",
    ]


# --- the trellises the recipes load ---


def answer_of(recipe):
    """The syntactic trellis `load_recipe` answers for the recipe at the path
    `recipe` in the repository, its folder given as an absolute path."""
    path = ROOT / recipe
    return load_recipe(path.parent, path.name)


def normalized(answer, root=ROOT):
    """`answer` with every absolute path under the repository's root `root`
    written relative to that root, and without the recipe's own digest under
    `provenance`; every other value as it stands."""
    prefix = Path(root).as_posix() + "/"

    def relative(value):
        if isinstance(value, dict):
            return {key: relative(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [relative(item) for item in value]
        if isinstance(value, str):
            return value.replace(prefix, "")
        return value

    written = relative(answer)
    del written["provenance"]["recipe"]["sha256"]
    return written


def digest(value):
    """The SHA-256 of the canonical JSON of `value`: keys sorted, characters
    outside ASCII written as they are, no space between items."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digests(answer):
    """The digests the fixture holds of a normalized answer: for each stage
    key, the digest of that key's record in every period, in the order of the
    periods, `None` in a period without the key; under `"*"`, the digest of
    the answer with every period's `stages` removed."""
    periods = answer["periods"]
    keys = sorted({key for period in periods for key in period["stages"]})
    found = {key: digest([period["stages"].get(key) for period in periods]) for key in keys}
    rest = {name: value for name, value in answer.items() if name != "periods"}
    rest["periods"] = [{name: value for name, value in period.items() if name != "stages"}
                       for period in periods]
    found["*"] = digest(rest)
    return found


def write_fixture(held):
    """Write the fixture: `held` maps each recipe's path to the digests of its
    normalized answer."""
    FIXTURE.write_text(json.dumps(held, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                       encoding="utf-8")


@pytest.mark.parametrize("recipe", RECIPES)
def test_every_recipe_loads_to_the_base_trellis(recipe):
    """The recipe's answer, normalized, has the digests the fixture holds:
    every stage key's records and the rest of the answer equal those the
    recipe gave when the module was last run as a script."""
    held = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert sorted(held) == sorted(RECIPES)
    assert (ROOT / recipe).is_file(), f"no recipe stands at {recipe}"
    expected, found = held[recipe], digests(normalized(answer_of(recipe)))
    differing = [key for key in sorted(set(expected) | set(found))
                 if expected.get(key) != found.get(key)]
    assert differing == [], (f"{recipe}: the records of the stage keys {', '.join(differing)} "
                             f"differ from those the fixture {FIXTURE.name} holds ('*' is the "
                             "answer without the periods' stages); after a deliberate change of "
                             "a recipe or of a file it reads, write the fixture again with "
                             "`PYTHONPATH=. python tests/test_layout.py`, run from "
                             "packages/bellman")


def test_a_stage_path_of_the_old_layout_is_refused(tmp_path):
    """A recipe whose `stage:` names a stage file at its path in the earlier
    layout, `stages/tenure.bl`, is refused as `load_stage` refuses a missing
    file, at the address `stages.tenure.stage`, with the path in the
    sentence. The recipe is that of the durables model, in a copy of its
    declaration, with the tenure stage's line written back to the earlier
    path."""
    declaration = ROOT / "applications/durables/declaration"
    assert (declaration / "spec.yml").is_file(), f"no recipe stands at {declaration / 'spec.yml'}"
    recipe, lines = re.subn(r"stage: stages/tenure/tenure\.bl\b", "stage: stages/tenure.bl",
                            (declaration / "spec.yml").read_text(encoding="utf-8"))
    assert lines == 1, "the durables recipe writes `stage: stages/tenure/tenure.bl` once"
    copy = tmp_path / "declaration"
    shutil.copytree(declaration, copy)
    (copy / "spec.yml").write_text(recipe, encoding="utf-8")
    earlier = copy / "stages/tenure.bl"
    with pytest.raises(FactoryError) as refused:
        load_recipe(copy, "spec.yml")
    with pytest.raises(FactoryError) as direct:
        load_stage(earlier)
    error = refused.value
    assert (error.rule, error.file, error.address, error.written) == (
        "readable-file", str(copy / "spec.yml"), "stages.tenure.stage", "stages/tenure.bl")
    assert (error.message, error.write) == (direct.value.message, direct.value.write)
    assert str(error).startswith(f"{copy / 'spec.yml'}: address 'stages.tenure.stage': "
                                 f"the file {earlier} does not exist")


if __name__ == "__main__":
    write_fixture({recipe: digests(normalized(answer_of(recipe))) for recipe in RECIPES})
    print(FIXTURE.relative_to(ROOT).as_posix(), FIXTURE.stat().st_size, "bytes")
