"""The layout of a model folder under applications/."""

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

import pytest
from application_files import ROOT

from bellman.refusals import FactoryError
from bellman.stage import load_stage
from bellman.trellis import load_recipe

# the file that holds, for each recipe of RECIPES, the digests of the syntactic
# trellis that the recipe loads to; this module, run as a script, writes it
TRELLIS_DIGESTS_FILE = Path(__file__).resolve().parent / "fixtures" / "layout_base_trellises.json"


# the command, run from the repository's root, that writes TRELLIS_DIGESTS_FILE
TRELLIS_DIGESTS_COMMAND = (
    "PYTHONPATH=packages/bellman:packages/bellman/tests python tests/test_application_layout.py"
)


# the recipes whose syntactic trellises TRELLIS_DIGESTS_FILE holds, each by its
# path in the repository
RECIPES = (
    "applications/durables/declaration/spec.yml",
    "applications/durables/declaration/spec.two-stages.yml",
    "applications/pension-retirement/declaration/spec.yml",
    "applications/retirement-choice/declaration/spec.yml",
    "applications/housing-frictions/declaration/spec.yml",
    "applications/benhabib-2019/declaration/spec.yml",
    "packages/bellman/tests/copied_files/de-la-croix-pommeret-2021/spec.yml",
    "packages/bellman/tests/copied_files/branching/examples/cagetti-denardi-2006/registry/spec.yml",
)


# the suffixes of the files the language reads: a stage file or an addition,
# and a recipe, trellis, period, calibration or settings file
READ_SUFFIXES = (".bl", ".yml", ".yaml")


# the files a model folder holds at its top, beside its folders
TOP_FILES = ("README.md", "economics.md")


# the folders beside `declaration/` whose contents are not examined; `paper`
# holds the files that the button `paper` of Bellman Workbench writes
UNEXAMINED = ("code", "notebooks", "paper", "reference", "results", "tests")


# how a file at a model folder's top is known as one the language reads
# (`_read_at_the_top`): every `.bl` file; and a `.yml` or `.yaml` file that is
# a recipe, trellis or period file by the beginning of its name, or a
# calibration or settings file by a stem that is its kind or ends in
# `_<kind>`, the names by which Bellman Workbench's tree gives these files
# their roles
READ_NAMES = ("spec", "trellis", "period")


KINDS = ("calibration", "settings")


# the name of an addition in a stage folder: `methods.bl`, or a replacing
# selection `methods.<variant>.bl`
ADDITION = re.compile(r"methods(?:\.[^.]+)?\.bl")


# the three sentences of the rules under `declaration/`
STAGE_FOLDER = (
    "declaration/stages/ holds one folder per stage, declaration/stages/<key>/, "
    "holding <key>.bl, <key>.md, methods.bl and methods.<variant>.bl and nothing else"
)


STAGE_FILE = (
    "a stage file stands at declaration/stages/<key>/<key>.bl, and an addition beside "
    "it as methods.bl or methods.<variant>.bl"
)


RETIRED_METHODS = (
    "declaration/methods/ is retired: an addition stands in its stage's folder as "
    "methods.bl or methods.<variant>.bl"
)


def files_under_applications():
    """Every file under `applications/` that git tracks and that stands on
    disk, by its path from the repository's root, or a skip of the test
    outside a git checkout; an untracked file is not listed, so that a
    checkout's scratch files do not enter the check."""
    # imported here: the Workbench's tests load this file by its path to read
    # `layout_faults` alone, with a stand-in for `application_files` and
    # without the folder of the package's tests, where `skips` stands, on the
    # path
    from skips import environment_without_git_variables, require_git_checkout

    require_git_checkout()
    listed = (
        subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--cached", "-z", "--", "applications"],
            capture_output=True,
            check=True,
            env=environment_without_git_variables(),
        )
        .stdout.decode("utf-8")
        .split("\0")
    )
    return sorted({name for name in listed if name and (ROOT / name).is_file()})


def layout_faults(paths):
    """The faults against the one layout of the files `paths`, each a path
    from the repository's root under `applications/`, one sentence each."""
    faults = [
        f"{path}: a generated path, with a component derived or __pycache__"
        for path in paths
        if {"derived", "__pycache__"} & set(PurePosixPath(path).parts)
    ]
    folders = {}
    for path in paths:
        parts = PurePosixPath(path).parts
        if len(parts) > 2:
            folders.setdefault(parts[1], []).append(PurePosixPath(*parts[2:]))
    for folder, files in sorted(folders.items()):
        if not any(file.suffix in READ_SUFFIXES for file in files):
            continue
        where = f"applications/{folder}"
        if not any(file.parts[0] == "declaration" for file in files):
            faults.append(f"{where}: no declaration/ folder")
        if PurePosixPath("README.md") not in files:
            faults.append(f"{where}: no README.md")
        for file in files:
            faults.extend(f"{where}/{file}: {fault}" for fault in _faults_of(file))
        keys = {
            file.parts[2]
            for file in files
            if file.parts[:2] == ("declaration", "stages") and len(file.parts) > 3
        }
        faults.extend(
            f"{where}/declaration/stages/{key}/: no stage file {key}.bl"
            for key in sorted(keys)
            if PurePosixPath("declaration", "stages", key, f"{key}.bl") not in files
        )
    return faults


def _read_at_the_top(file):
    """Whether the file `file`, standing at a model folder's top, is one the
    language reads: a `.bl` file, a stage file or an addition, or a `.yml` or
    `.yaml` file whose name begins with one of `READ_NAMES`, or whose stem is
    one of `KINDS` or ends in `_` and one of them. The check reads names
    alone; another file is read only where a recipe names it."""
    if file.suffix == ".bl":
        return True
    return file.suffix in READ_SUFFIXES and (
        file.name.startswith(READ_NAMES)
        or any(file.stem == kind or file.stem.endswith(f"_{kind}") for kind in KINDS)
    )


def _faults_of(file):
    """The faults of one file of a model folder, `file` its path from the
    folder. At the folder's top, `README.md` and `economics.md` are accepted;
    a file that the language reads (`_read_at_the_top`) is sent under
    `declaration/`; another markdown file breaks the rule of markdown files;
    and any other file, such as the record `answers.yml` that Bellman
    Workbench's "new trellis" writes there, breaks the rule of the top."""
    first = file.parts[0]
    if first == "declaration":
        if len(file.parts) > 2 and file.parts[1] == "stages":
            key = file.parts[2]
            if len(file.parts) == 4 and (
                file.name in (f"{key}.bl", f"{key}.md") or ADDITION.fullmatch(file.name)
            ):
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
    if file.suffix in READ_SUFFIXES and (len(file.parts) > 1 or _read_at_the_top(file)):
        return ["a file the language reads stands under declaration/"]
    if file.suffix == ".md":
        return [
            "a markdown file outside declaration/ is README.md or economics.md at the "
            "folder's top, and a stage's note stands in its stage folder"
        ]
    if len(file.parts) == 1:
        return ["the top of a model folder holds README.md, economics.md and folders alone"]
    return [
        f"the folder {first}/ is none of declaration/, "
        f"{', '.join(name + '/' for name in UNEXAMINED)}"
    ]


def trellis_of(recipe):
    """The syntactic trellis that `load_recipe` gives for the recipe at the
    path `recipe` in the repository, its folder given as an absolute path."""
    path = ROOT / recipe
    return load_recipe(path.parent, path.name)


def normalized(trellis, root=ROOT):
    """`trellis` with every absolute path under the repository's root `root`
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

    written = relative(trellis)
    del written["provenance"]["recipe"]["sha256"]
    return written


def json_digest(value):
    """The SHA-256 of the canonical JSON of `value`: keys sorted, characters
    outside ASCII written as they are, no space between items."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stage_key_digests(trellis):
    """The digests that TRELLIS_DIGESTS_FILE holds of a normalized syntactic
    trellis: for each stage key, the digest of that key's record in every
    period, in the order of the periods, `None` in a period without the key;
    under `"*"`, the digest of the trellis with every period's `stages`
    removed."""
    periods = trellis["periods"]
    keys = sorted({key for period in periods for key in period["stages"]})
    found = {key: json_digest([period["stages"].get(key) for period in periods]) for key in keys}
    rest = {name: value for name, value in trellis.items() if name != "periods"}
    rest["periods"] = [
        {name: value for name, value in period.items() if name != "stages"} for period in periods
    ]
    found["*"] = json_digest(rest)
    return found


def write_trellis_digests(held):
    """Write TRELLIS_DIGESTS_FILE: `held` maps each recipe's path to the
    digests of its normalized syntactic trellis."""
    TRELLIS_DIGESTS_FILE.write_text(
        json.dumps(held, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    write_trellis_digests(
        {recipe: stage_key_digests(normalized(trellis_of(recipe))) for recipe in RECIPES}
    )
    print(
        TRELLIS_DIGESTS_FILE.relative_to(ROOT).as_posix(),
        TRELLIS_DIGESTS_FILE.stat().st_size,
        "bytes",
    )


@pytest.fixture(scope="module")
def recorded_trellis_digests():
    """The digests that TRELLIS_DIGESTS_FILE holds, by the path of each
    recipe."""
    return json.loads(TRELLIS_DIGESTS_FILE.read_text(encoding="utf-8"))


@pytest.mark.xfail(
    strict=True,
    reason="The test expects every folder under `applications/` that holds a file which the "
    "language reads to follow the layout of a model folder. Today `applications/cons-port/` "
    "holds the file `AGENTS.md` at its top and the folder `.bellman-matsya/`, which the "
    "layout does not allow.",
)
def test_every_application_has_the_one_layout():
    """Every folder under `applications/` that holds a stage file or a file
    the language reads has `declaration/` and `README.md`; a stage's file, its
    note and its additions stand in its stage folder; a recipe, a trellis,
    period, calibration or settings file stands under `declaration/`; the
    folder's top holds no other file than `README.md` and `economics.md` and
    no other folder than `declaration/` and the folders of `UNEXAMINED`; and
    no path is generated."""
    faults = layout_faults(files_under_applications())
    assert faults == [], "\n".join(
        [f"{len(faults)} faults against the layout of a model folder:"] + faults
    )


def test_a_file_at_a_folders_top_is_refused_by_the_rule_it_breaks():
    """At the top of a model folder, `README.md` is accepted, a planted file
    whose name marks it as one that the language reads is refused by the rule
    that sends it under `declaration/`, and the other planted files, which the
    language does not read and none of which is a markdown file, by the rule
    of the top."""
    # the paths are planted, not read from git; `answers.yml` and the
    # `.gitignore` are the two files that Bellman Workbench's "new trellis"
    # writes at the top, and `cons_methods.yml` is a methods file written in
    # YAML, a form that the language does not read
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


def test_a_file_under_declaration_is_refused_by_the_rule_it_breaks():
    """Under `declaration/`, a stage folder accepts its stage file, its note
    and its additions, and the other planted files of the stage folder, a
    planted `.bl` file in another folder of `declaration/` and each planted
    file under `declaration/methods/` are refused by the rule that each
    breaks."""
    # the paths are planted, not read from git; `methods.yml` is a methods file
    # written in YAML, a form that the language does not read, and
    # `declaration/methods/` is a folder that the layout does not have, whose
    # rule sends an addition to its stage folder
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


def test_the_file_of_trellis_digests_holds_each_recipe_of_the_table_and_no_other(
    recorded_trellis_digests,
):
    """The recipes whose digests TRELLIS_DIGESTS_FILE holds are the recipes of
    RECIPES."""
    assert sorted(recorded_trellis_digests) == sorted(RECIPES)


@pytest.mark.parametrize("recipe", RECIPES, ids=str)
def test_a_recipe_loads_to_the_syntactic_trellis_whose_digests_are_recorded(
    recorded_trellis_digests, recipe
):
    """The syntactic trellis that `load_recipe` gives for a recipe, its paths
    written from the repository's root, has for each stage key and for the
    rest of the trellis the digest that TRELLIS_DIGESTS_FILE holds."""
    assert (ROOT / recipe).is_file(), f"no recipe stands at {recipe}"
    assert recipe in recorded_trellis_digests, (
        f"{TRELLIS_DIGESTS_FILE.name} holds no digests of {recipe}; write it again with "
        f"`{TRELLIS_DIGESTS_COMMAND}`, run from the repository's root"
    )
    expected, found = (
        recorded_trellis_digests[recipe],
        stage_key_digests(normalized(trellis_of(recipe))),
    )
    differing = [
        key for key in sorted(set(expected) | set(found)) if expected.get(key) != found.get(key)
    ]
    assert differing == [], (
        f"{recipe}: the records of the stage keys {', '.join(differing)} "
        f"differ from those that {TRELLIS_DIGESTS_FILE.name} holds ('*' is the "
        "trellis without the periods' stages); after a deliberate change of "
        "a recipe or of a file it reads, write that file again with "
        f"`{TRELLIS_DIGESTS_COMMAND}`, run from the repository's root"
    )


def test_a_recipe_naming_the_earlier_path_of_a_stage_file_is_refused_as_a_missing_file(tmp_path):
    """A recipe whose `stage:` names `stages/tenure.bl`, where no file
    stands, is refused under the rule `readable-file` at the address
    `stages.tenure.stage`, with the message of `load_stage` for the missing
    file."""
    # the recipe of the durables model, in a copy of its declaration folder,
    # with the line of the tenure stage written with the path that a stage
    # file had before each stage had a folder of its own
    declaration = ROOT / "applications/durables/declaration"
    assert (declaration / "spec.yml").is_file(), f"no recipe stands at {declaration / 'spec.yml'}"
    recipe, lines = re.subn(
        r"stage: stages/tenure/tenure\.bl\b",
        "stage: stages/tenure.bl",
        (declaration / "spec.yml").read_text(encoding="utf-8"),
    )
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
        "readable-file",
        str(copy / "spec.yml"),
        "stages.tenure.stage",
        "stages/tenure.bl",
    )
    assert (error.message, error.write) == (direct.value.message, direct.value.write)
    assert str(error).startswith(
        f"{copy / 'spec.yml'}: address 'stages.tenure.stage': the file {earlier} does not exist"
    )
