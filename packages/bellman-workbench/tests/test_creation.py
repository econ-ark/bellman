"""Creating a model folder from templates, without a browser (model
interface specification 0.3, §4 and §3.3; unit C): the templates read from
the corpus, the forms of the recipe, the period file and the trellis file,
the checklist, "new trellis", "add stage" and "add period", their writers
for a trellis written as records, the edits of a stage dropped on the
forward trellis graph (`drop_edits`, unit J of model interface
specification 0.4, item 5), "new variant"
(Task 6 of the model folder's layout), "new stage" and the recipe cell's
"new file" (unit K's decision K-D7), the terminal period of "new trellis"
and a template copied under another key (unit K, Task 12), the reading of
the library of stages (unit L, Task 7), the templates read per entry, a
folder with no template, the parent folder asked and a variant's own
labels (unit L, Task 13), and the forms of the page that call them,
rendered by Solara's test renderer.

The tests named `test_item_<n>_*` close the claims of C's acceptance items
1 and 2 that hold without a browser; `test_page_creation.py` closes them
through the page. The fixtures and the helpers are those of
`workbench_support.py`.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from pathlib import Path

import ipyvuetify as v
import nbformat
import pytest
import solara
import yaml
from workbench_support import (
    CONS,
    CONS_ID,
    DEMO_FILES,
    DEMO_STAGES,
    DISC_ID,
    DURABLES,
    NOPORT_ID,
    PENSION_RETIREMENT,
    PENSIONS_WORKING_YEARS,
    PORT_CONS_RECORDS,
    PORT_CONS_RECIPE,
    PORT_ID,
    PORTFOLIO_CHOICE,
    RECIPE_FILE,
    ROOT,
    SHARED_CONS,
    TERMINAL_ID,
    VARIANT_FILES,
    WORKER_ID,
    applications_copy,
    applied,
    clear_gesture_state,
    clear_trellis_state,
    code_cell_outputs,
    drawn_text,
    dropped_event,
    enter_text,
    file_bytes,
    filled,
    form_field,
    git,
    layout_faults_of,
    old_graph_gesture,
    open_rendered_recipe_row,
    pensions_copy,
    press_words,
    records_without,
    refused_corpus,
    repository_copy,
    save_added,
    tree_entries,
    without_file_provenance,
    written_from_the_forms,
)

from bellman.refusals import FactoryError
from bellman.stage import source_spans
from bellman.trellis import (
    entry_span,
    entry_value,
    load_recipe,
    load_trellis,
    period_entries,
    specify_trellis,
    split_entry,
)
from bellman_workbench import app, creation, model
from bellman_workbench.recipe import Source, read_source
from bellman_workbench.trellis import (
    Gesture,
    drop_edits,
    parse_restriction,
    show_trellis,
    stage_items,
)

CORPUS = ROOT / "applications"
# the declaration of the portfolio model, which holds the stage files of
# the four portfolio templates, and that of the portfolio-consumption
# application, which holds the files their trellis files bind them with
PORTFOLIO = CORPUS / "portfolio-choice/declaration"
CONS_PORT = CORPUS / "cons-port/declaration"
# the consumption stage file the template `cons` reads, the folder's own
# since 28 October 2026 (decision SD-39 before it)
DEMONSTRATION_CONS_FILE = CORPUS / "cons-port/declaration/stages/cons/cons.bl"


def test_the_eight_templates_of_a_stage_are_read_from_the_corpus():
    """The templates of a stage are the eight stage files the three corpus
    files of TEMPLATE_SOURCES bind, in that order, each with its stage
    file, its model's title, the parameters its calibration must give and
    the files its application binds it with, the additions beside its stage
    file among them (spec 0.3 §4, D6; decision S7-W2)."""
    templates = creation.stage_templates()
    assert [template.id for template in templates] == [
        "cons-port/declaration/spec.port-cons.yml#port",
        "cons-port/declaration/spec.port-cons.yml#cons",
        "cons-port/declaration/spec.port-cons.yml#disc",
        "cons-port/declaration/trellis.reference-cons-only.yml#noport",
        "pension-retirement/declaration/spec.yml#worker_saving",
        "pension-retirement/declaration/spec.yml#retire_choice",
        "pension-retirement/declaration/spec.yml#retiree_saving",
        "pension-retirement/declaration/spec.yml#terminal",
    ]
    by_key = {template.key: template for template in templates}
    cons = by_key["cons"]
    # the folder's own consumption stage file (decision SD-39 before the two
    # cons-port folders became one)
    assert cons.stage == DEMONSTRATION_CONS_FILE
    assert cons.model == "The portfolio-consumption application"
    assert cons.calibration == ("ρ",)
    assert cons.companions == {
        "calibration": (CONS_PORT / "calibration/portfolio.yml",),
        "settings": (CONS_PORT / "settings/cons_wide.yml",),
        "methods": (CONS_PORT / "stages/cons/methods.bl",),
    }
    assert by_key["disc"].companions["settings"] == ()
    assert by_key["disc"].companions["methods"] == (CONS_PORT / "stages/disc/methods.bl",)
    assert by_key["noport"].companions["settings"] == (CONS_PORT / "settings/noport.yml",)
    worker = by_key["worker_saving"]
    assert worker.stage == (
        CORPUS / "pension-retirement/declaration/stages/worker_saving/worker_saving.bl"
    )
    assert worker.model == "Savings and retirement choice with pension assets"
    assert worker.calibration == ("β", "ρ", "r_f", "r_p", "χ_s", "μ_w", "σ_w")
    # each pension stage brings its addition, and the two saving stages
    # their settings files (decision S7-W2); the recipe binds the
    # calibration by a slot alone
    pension = CORPUS / "pension-retirement/declaration"
    for template in templates[4:]:
        settings = pension / f"settings/{template.key}.yml"
        assert template.companions == {
            "calibration": (),
            "settings": (settings,) if template.key.endswith("_saving") else (),
            "methods": (pension / f"stages/{template.key}/methods.bl",),
        }, template.key
    assert creation.template_of("cons-port/declaration/spec.port-cons.yml#cons") is cons
    with pytest.raises(ValueError, match="no template of a stage is named"):
        creation.template_of("nowhere#cons")


def test_the_forms_read_back_through_the_factory(tmp_path):
    """The recipe, the period file and the trellis file, written in the
    form of the three files of applications/pension-retirement/declaration/
    with one slot per stage and kind and empty connector mappings,
    read back through `load_recipe` in the folder's `declaration/`: six
    periods of port, cons and disc, every slot unbound, each stage's methods
    list naming no addition, and every connector mapping empty; answers.yml
    lists the six slots as required and no connector (decision C-D1). A row
    names its stage's file in the stage's own folder, and the recipe's five
    comment lines, which name where the files of each kind stand, an
    addition in its stage's folder, are within 79 characters for a folder
    name of 32 characters (C-K36)."""
    folder = written_from_the_forms(tmp_path / "demo")
    read = load_recipe(folder / "declaration", "spec.yml")
    assert len(read["periods"]) == 6
    assert list(read["periods"][0]["stages"]) == ["port", "cons", "disc"]
    assert read["periods"][0]["connectors"] == [{}]
    assert read["inter_connectors"][0] == {}
    lists = read["periods"][3]["stages"]["cons"]["provenance"]["source_lists"]
    assert lists == {
        **{
            kind: [{"slot": f"cons_{kind}", "bound": False, "names": []}]
            for kind in creation.SLOT_KINDS
        },
        "methods": [],
    }
    answers = (folder / creation.ANSWERS).read_text(encoding="utf-8")
    assert yaml.safe_load(answers)["required"] == {
        "slots": [
            f"{key}_{kind}" for key in ("port", "cons", "disc") for kind in creation.SLOT_KINDS
        ],
        "connectors": [],
    }
    assert creation.recipe_row("cons") == (
        "{stage: stages/cons/cons.bl, calibration: {all: [$cons_calibration]}, "
        "settings: {all: [$cons_settings]}, methods: {all: []}}"
    )
    comments = creation.recipe_text("m" * 32, [("cons", ())]).split("\n")[:5]
    assert [line[0] for line in comments] == ["#"] * 5
    assert max(len(line) for line in comments) <= 79
    assert "stages/<stage>/methods.bl" in "".join(comments)


def test_item_1_a_slot_is_no_checklist_entry(tmp_path):
    """Unit K's decision K-D29, which amends C item 1 (spec 0.3 §4): the
    six slots the recipe of a new folder writes, the calibration and the
    settings of each stage (decision S7-F3), each a place for values
    supplied by the keyword of `load_recipe` that spells its name, are no
    entry of the checklist, whether answers.yml lists them under
    `required.slots`, as the form writes it, or is absent; filling them
    changes no entry."""
    folder = written_from_the_forms(tmp_path / "demo")
    recipe = folder / creation.factory_path(creation.RECIPE)
    text = recipe.read_text(encoding="utf-8")
    assert all(
        f"${key}_{kind}]" in text for key, _ in DEMO_STAGES for kind in creation.SLOT_KINDS
    )
    assert creation.checklist(folder) == ()
    (folder / creation.ANSWERS).unlink()
    assert creation.checklist(folder) == ()
    recipe.write_text(filled(text), encoding="utf-8")
    assert creation.checklist(folder) == ()


def test_the_checklist_reads_every_list_and_survives_a_broken_file(tmp_path):
    """A slot in a period-range list is no entry (K-D29); a required
    connector is an entry while its mapping is empty and none once one is
    typed; a recipe that does not read as YAML gives no entry and raises
    nothing, its refusal being the factory's, and the empty connector of
    the period file, once answers.yml holds it required, is an entry beside
    that refusal; a folder without answers.yml, as the portfolio and the
    pension models are, has no entry, the pension recipe's slots included
    (spec 0.3 §4, C-R12; K-D29). A required connector's file is read from
    the model folder, where answers.yml stands, by the rule `answers_text`
    states."""
    folder = written_from_the_forms(tmp_path / "demo")
    recipe = folder / creation.factory_path(creation.RECIPE)
    text = filled(recipe.read_text(encoding="utf-8")).replace(
        "cons: {stage: stages/cons/cons.bl, calibration: {all: [calibration/portfolio]}",
        "cons: {stage: stages/cons/cons.bl, calibration: {all: [calibration/portfolio], "
        '"0-0": [$cons_calibration]}',
    )
    recipe.write_text(text, encoding="utf-8")
    assert creation.checklist(folder) == ()
    answers = folder / creation.ANSWERS
    answers.write_text(
        answers.read_text(encoding="utf-8").replace(
            "  connectors: []",
            '  connectors:\n    - {file: declaration/trellis.yml, address: "inter_connectors[0]"}',
        ),
        encoding="utf-8",
    )
    (last,) = creation.checklist(folder)
    assert (last.file, last.address, last.line, last.column) == (
        "declaration/trellis.yml",
        "inter_connectors[0]",
        10,
        5,
    )
    trellis = folder / creation.factory_path(creation.TRELLIS)
    trellis.write_text(
        trellis.read_text(encoding="utf-8").replace("  - {}", "  - {a: k}"), encoding="utf-8"
    )
    assert creation.checklist(folder) == ()
    recipe.write_text("stages: [\n", encoding="utf-8")
    assert creation.checklist(folder) == ()
    answers.write_text(
        answers.read_text(encoding="utf-8").replace(
            '{file: declaration/trellis.yml, address: "inter_connectors[0]"}',
            '{file: declaration/period.yml, address: "connectors[0]"}',
        ),
        encoding="utf-8",
    )
    assert [(entry.file, entry.address, entry.line) for entry in creation.checklist(folder)] == [
        ("declaration/period.yml", "connectors[0]", 12)
    ]
    assert creation.checklist(ROOT / "applications/portfolio-choice") == ()
    assert creation.checklist(ROOT / "applications/pension-retirement") == ()


def test_the_checklist_survives_answers_of_the_wrong_type_and_lists_each_place_once(
    tmp_path, app_state
):
    """A `required.slots` that is not a list, 5 or null, gives no entry,
    since no slot is an entry (K-D29), and a `required.connectors` of 5
    gives no connector; a connector whose file or address is not a string
    is passed over, and so is one whose file lies outside the folder,
    `../outside.yml`; a connector listed twice is one entry, and the
    checklist block renders the entries; a file whose bytes are not UTF-8
    raises nothing: the connector's file gives no entry, and so does
    answers.yml read as absent, and the recipe (spec 0.3 §4)."""
    from workbench_support import composition_folder

    folder = composition_folder(tmp_path / "demo", repeat=2)
    trellis_path = folder / "trellis.yml"
    trellis_path.write_text(trellis_path.read_text().replace("inter_connectors: []", "inter_connectors: [{}]"))
    (folder / creation.ANSWERS).write_text("required:\n  slots: [S_calibration]\n  connectors: []\n")
    answers = folder / creation.ANSWERS
    answers.write_text("required: {slots: 5, connectors: 5}\n", encoding="utf-8")
    assert creation.checklist(folder) == ()
    (tmp_path / "outside.yml").write_text("conn: {}\n", encoding="utf-8")
    answers.write_text(
        "required:\n"
        "  slots: null\n"
        "  connectors:\n"
        "    - {file: 5, address: x}\n"
        "    - {file: trellis.yml, address: 5}\n"
        '    - {file: trellis.yml, address: "inter_connectors[0]"}\n'
        '    - {file: trellis.yml, address: "inter_connectors[0]"}\n'
        "    - {file: ../outside.yml, address: conn}\n",
        encoding="utf-8",
    )
    app_state(folder)
    entries = app.checklist.value
    assert [(entry.file, entry.address) for entry in entries] == [
        ("trellis.yml", "inter_connectors[0]"),
    ]
    _, rendered = solara.render(app.ErrorMark(), handle_error=False)
    try:
        buttons = rendered.find(v.Html, class_="bl-row bl-checklist-entry").widgets
        assert [button.attributes["data-file"] for button in buttons] == [
            entry.file for entry in entries
        ]
    finally:
        rendered.close()
    for name in ("trellis.yml", creation.ANSWERS):
        path = folder / name
        path.write_bytes(path.read_bytes() + b"# \xff\n")
        assert creation.checklist(folder) == ()
    recipe = folder / creation.factory_path(creation.RECIPE)
    recipe.parent.mkdir(exist_ok=True)
    recipe.write_bytes(b"trellis: ../trellis.yml\n# \xff\n")
    assert creation.checklist(folder) == ()


def test_the_checklist_counts_from_the_buffers(tmp_path):
    """Spec 0.4 §3.3 and §8 J (1): the checklist reads each of answers.yml,
    the recipe and a required connector's file from the mapping of unsaved
    texts where it holds that file, by its resolved path, and from disk
    otherwise. In a folder of the forms whose answers.yml requires the
    trellis file's inter-period mapping, the mapping typed in an unsaved
    text is no longer listed, the slots filled in an unsaved recipe change
    no entry, since no slot is one (K-D29), and an unsaved answers.yml that
    requires nothing lists nothing; the files on disk still give every
    entry."""
    folder = written_from_the_forms(tmp_path / "demo")
    answers = folder / creation.ANSWERS
    answers.write_text(
        answers.read_text(encoding="utf-8").replace(
            "  connectors: []",
            '  connectors:\n    - {file: declaration/trellis.yml, address: "inter_connectors[0]"}',
        ),
        encoding="utf-8",
    )
    entries = creation.checklist(folder)
    assert [(entry.file, entry.address) for entry in entries] == [
        ("declaration/trellis.yml", "inter_connectors[0]")
    ]
    trellis = folder / creation.factory_path(creation.TRELLIS)
    recipe = folder / creation.factory_path(creation.RECIPE)
    typed = trellis.read_text(encoding="utf-8").replace("  - {}", "  - {a: k}")
    assert creation.checklist(folder, {str(trellis.resolve()): typed}) == ()
    slots_filled = filled(recipe.read_text(encoding="utf-8"))
    assert creation.checklist(folder, {str(recipe.resolve()): slots_filled}) == entries
    nothing = "required: {slots: [], connectors: []}\n"
    assert creation.checklist(folder, {str(answers.resolve()): nothing}) == ()
    assert creation.checklist(folder) == entries


def test_the_checklist_block_lists_the_entries_and_opens_the_file_at_one(tmp_path, app_state):
    """The page reads the checklist with the tree; in a new folder whose
    answers.yml requires the period file's connector and the trellis file's
    inter-period mapping, its block lists one button per entry, by file and
    line, and none for the six slots (K-D29); a click opens the file with
    the editor at the entry's line and column (spec 0.3 §4)."""
    from workbench_support import composition_folder

    folder = composition_folder(tmp_path / "demo", repeat=2)
    trellis_path = folder / "trellis.yml"
    trellis_path.write_text(trellis_path.read_text().replace("inter_connectors: []", "inter_connectors: [{}]"))
    (folder / creation.ANSWERS).write_text("required:\n  slots: [S_calibration]\n  connectors: []\n")
    answers = folder / creation.ANSWERS
    answers.write_text(
        answers.read_text(encoding="utf-8").replace(
            "  connectors: []",
            '  connectors:\n    - {file: period.yml, address: "connectors[0]"}'
            '\n    - {file: trellis.yml, address: "inter_connectors[0]"}',
        ),
        encoding="utf-8",
    )
    app_state(folder)
    assert [(entry.file, entry.address) for entry in app.checklist.value] == [
        ("period.yml", "connectors[0]"),
        ("trellis.yml", "inter_connectors[0]"),
    ]
    _, rendered = solara.render(app.ErrorMark(), handle_error=False)
    try:
        buttons = rendered.find(v.Html, class_="bl-row bl-checklist-entry").widgets
        assert [
            (drawn_text(button), button.attributes["data-file"], button.attributes["data-line"])
            for button in buttons
        ] == [
            ("period.yml · connectors[0]", "period.yml", "5"),
            ("trellis.yml · inter_connectors[0]", "trellis.yml", "4"),
        ]
        buttons[1].fire_event("click", {})
    finally:
        rendered.close()
    entry = app.checklist.value[1]
    assert app.open_path.value == "trellis.yml"
    assert (app.goto_request.value["line"], app.goto_request.value["column"]) == (
        entry.line,
        entry.column,
    )


def test_item_1_new_trellis_writes_the_folder_of_section_4_inside_a_repository(repository):
    """`create_trellis` writes, inside the test repository whose push
    destination the place names, the folder of §4 from three templates: the
    stage files copied, their companions, the recipe, the period and the
    trellis files, answers.yml, the .gitignore and the README (C-R3); the
    factory reads every file written but those three once the slots are
    filled; the recipe holds the line `trellis: trellis.yml`, and
    `load_recipe` reads the recipe back with the trellis file beside it in
    `declaration/` as its trellis file; no slot is a checklist entry
    (K-D29); nothing is committed (C-R1)."""
    work, bare = repository
    assert model.git_place(model.open_folder(work)).destination == str(bare)
    created = creation.create_trellis(
        work,
        "lifecycle-demo",
        [("port", PORT_ID), ("cons", CONS_ID), ("disc", DISC_ID)],
        "lifecycle_demo_period",
        6,
    )
    assert created == creation.Created((work / "lifecycle-demo").resolve(), DEMO_FILES, False)
    # the three templates read the stage files of cons-port, one folder
    # since 28 October 2026 (decisions SD-39 and SE-32 before it)
    sources = {
        "port": CONS_PORT / "stages/port/port.bl",
        "cons": DEMONSTRATION_CONS_FILE,
        "disc": CONS_PORT / "stages/disc/disc.bl",
    }
    for key, source in sources.items():
        copied = (created.folder / f"declaration/stages/{key}/{key}.bl").read_bytes()
        assert copied == source.read_bytes()
    assert creation.checklist(created.folder) == ()
    assert git(work, "rev-list", "--count", "HEAD").strip() == "1"
    recipe = created.folder / "declaration/spec.yml"
    assert yaml.safe_load(recipe.read_text(encoding="utf-8"))["trellis"] == "trellis.yml"
    recipe.write_text(filled(recipe.read_text(encoding="utf-8")), encoding="utf-8")
    read = load_recipe(created.folder / "declaration", "spec.yml")
    trellis = Path(read["provenance"]["trellis"]["path"])
    assert trellis == created.folder / "declaration/trellis.yml"
    named = {
        Path(entry["path"]).resolve().relative_to(created.folder).as_posix()
        for period in read["periods"]
        for record in period["stages"].values()
        for entries in record["provenance"]["source_lists"].values()
        for entry in entries
    }
    named |= {f"declaration/stages/{key}/{key}.bl" for key in ("port", "cons", "disc")}
    named |= {"declaration/spec.yml", "declaration/period.yml", "declaration/trellis.yml"}
    assert set(created.files) - named == {"answers.yml", ".gitignore", "README.md"}
    assert creation.checklist(created.folder) == ()


def test_new_trellis_add_stage_and_add_period_write_the_one_layout(repository):
    """A folder "new trellis" writes, with a stage copied under a key of
    its own, and to which "add stage" and "add period" add a stage and a
    period, has the one layout of a model folder by the layout's own check
    (`layout_faults` of packages/bellman/tests/test_layout.py), answers.yml
    and the .gitignore excepted at its top: `declaration/` holds the recipe,
    the trellis and period files, `calibration/`, `settings/` and one
    folder per stage, `stages/<key>/`, with the stage file `<key>.bl` and
    the addition its template brings, copied as `methods.bl` and naming
    the stage by its key (unit K, Task 12);
    README.md stands at the top (merge note M8). Neither writer writes a
    file: "add period" reads the recipe "add stage" edited from the texts
    it answered, and the layout is that of the folder once the new files
    and the edited texts are written (spec 0.4 §3.5, §3.6)."""
    work, _ = repository
    created = creation.create_trellis(
        work,
        "layout-demo",
        [("port", PORT_ID), ("consumption", CONS_ID), ("disc", DISC_ID), ("worker", WORKER_ID)],
        "demo_period",
        2,
    )
    before = file_bytes(created.folder)
    stage = creation.add_stage(created.folder, "noport", NOPORT_ID)
    period = creation.add_period(
        created.folder, "young", ["consumption", "noport"], texts=stage.edits
    )
    assert file_bytes(created.folder) == before
    save_added(created.folder, stage)
    save_added(created.folder, period)
    declaration = created.folder / "declaration"
    assert sorted(path.name for path in (declaration / "stages").iterdir()) == [
        "consumption",
        "disc",
        "noport",
        "port",
        "worker",
    ]
    for key, source in (
        ("port", CONS_PORT / "stages/port/methods.bl"),
        ("consumption", CONS_PORT / "stages/cons/methods.bl"),
        ("disc", CONS_PORT / "stages/disc/methods.bl"),
        ("noport", CONS_PORT / "stages/noport/methods.bl"),
        ("worker", PENSION_RETIREMENT / "declaration/stages/worker_saving/methods.bl"),
    ):
        assert sorted(path.name for path in (declaration / "stages" / key).iterdir()) == sorted(
            [f"{key}.bl", "methods.bl"]
        )
        # the source's text with its `@methods:` line naming the key (unit K,
        # Task 12; specification 0.7 §4 rule 1)
        named = re.sub(
            r"^@methods: .*$",
            f"@methods: {key}",
            source.read_text(encoding="utf-8"),
            count=1,
            flags=re.M,
        )
        assert (declaration / "stages" / key / "methods.bl").read_text(encoding="utf-8") == named
    # no folder of block files is written (decision S7-W2)
    assert not (declaration / "methods").exists()
    assert sorted(path.name for path in created.folder.iterdir()) == [
        ".gitignore",
        "README.md",
        "answers.yml",
        "declaration",
    ]
    faults = layout_faults_of(created.folder)
    assert faults == [
        f"applications/layout-demo/{name}: the top of a model folder holds README.md, "
        "economics.md and folders alone"
        for name in (".gitignore", "answers.yml")
    ], "\n".join(faults)


def test_new_trellis_outside_a_repository_makes_one_with_its_destination(tmp_path, git_identity):
    """Under a folder no repository holds, the new folder is made a
    repository of its own whose branch pushes to the destination typed; its
    git folder is not among the files written (spec 0.3 §4, D10)."""
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    plain = tmp_path / "plain"
    plain.mkdir()
    created = creation.create_trellis(
        plain, "pension-copy", [("worker_saving", WORKER_ID)], "pension_period", 3, str(bare)
    )
    assert created.repository and (created.folder / ".git").is_dir()
    assert not [name for name in created.files if name.startswith(".git/")]
    place = model.git_place(model.open_folder(created.folder))
    assert (place.root, place.destination) == (created.folder, str(bare))
    assert len(load_recipe(created.folder / "declaration", "spec.yml")["periods"]) == 3


@pytest.mark.parametrize(
    ("answers", "words"),
    [
        ({"name": "../escape"}, "is no folder name"),
        ({"stages": [("cons", CONS_ID), ("cons", DISC_ID)]}, "is given twice"),
        ({"stages": [("2cons", CONS_ID)]}, "is no stage key"),
        ({"stages": [("cons", "nowhere#cons")]}, "no template of a stage is named"),
        ({"label": "a period"}, "is no period label"),
        ({"repeat": 0}, "whole number of one or more"),
        ({"destination": "https://user:password@example.org/model.git"}, "password"),
        (
            {"destination": "https://ghp_abcdef0123456789@github.com/me/model.git"},
            "user information before '@'",
        ),
        ({"destination": "-x"}, "begins with '-'"),
        ({"name": "2026"}, "YAML reads"),
        ({"stages": [("yes", CONS_ID)]}, "YAML reads"),
        ({"label": "null"}, "YAML reads"),
        ({"terminal": ["bequest"]}, "is marked for the terminal period and is not chosen"),
        ({"terminal": ["cons"]}, "the periods before it would hold no stage"),
    ],
)
def test_new_trellis_refuses_before_writing(repository, answers, words):
    """Each answer the form cannot write is refused in one line that names
    what is wrong, and nothing is written."""
    work, _ = repository
    given = {
        "name": "refused",
        "stages": [("cons", CONS_ID)],
        "label": "refused_period",
        "repeat": 6,
        "destination": None,
    }
    with pytest.raises(ValueError, match=words):
        creation.create_trellis(work, **(given | answers))
    assert sorted(path.name for path in work.iterdir()) == [".git", "README.md"]


def test_new_trellis_refuses_a_folder_that_exists(repository):
    """A name that names an existing entry is refused, and the existing
    folder is left as it was."""
    work, _ = repository
    creation.create_trellis(work, "lifecycle-demo", [("cons", CONS_ID)], "p", 1)
    before = sorted(path.name for path in (work / "lifecycle-demo").iterdir())
    with pytest.raises(ValueError, match="exists"):
        creation.create_trellis(work, "lifecycle-demo", [("disc", DISC_ID)], "p", 1)
    assert sorted(path.name for path in (work / "lifecycle-demo").iterdir()) == before


# the stages of a folder whose last stage, the pension model's terminal
# stage copied as `bequest`, stands in the terminal period alone (unit K,
# Task 12), and the stage keys of its terminal period
BEQUEST_STAGES = (*DEMO_STAGES, ("bequest", TERMINAL_ID))
TERMINAL_KEYS = ["port", "cons", "disc", "bequest"]
# the two text buttons of a chosen template's row in the form "new trellis",
# with their capitals (design pass 8 §8, item 1; unit M, Task 6)
PERIOD_WORDS = ("Every period", "Terminal period")


def test_a_template_copied_under_another_key_names_that_key_in_its_files(repository):
    """Unit K, Task 12 (the usability walkthrough §4 item 17): a template
    copied under another key, by "new trellis" or by "add stage", names the
    key on its stage file's `@stage:` line and, where it brings an
    addition, on that file's `@methods:` line, every other character of the
    template kept, so that the stage and its addition name the key the tree
    and the recipe show, and the addition is unioned with the stage once
    the recipe's row names it (decision S7-W2); a template copied under its
    own key is copied byte for byte."""
    work, _ = repository
    created = creation.create_trellis(
        work,
        "renamed-demo",
        [("port", PORT_ID), ("discount", DISC_ID), ("bequest", TERMINAL_ID)],
        "demo_period",
        2,
    )
    declaration = created.folder / "declaration"
    for key, template_id in (("discount", DISC_ID), ("bequest", TERMINAL_ID)):
        source = creation.template_of(template_id).stage.read_text(encoding="utf-8")
        copied = (declaration / f"stages/{key}/{key}.bl").read_text(encoding="utf-8")
        assert copied.splitlines()[0] == f"@stage: {key}"
        assert copied.split("\n", 1)[1] == source.split("\n", 1)[1]
    port = (declaration / "stages/port/port.bl").read_bytes()
    assert port == (CONS_PORT / "stages/port/port.bl").read_bytes()
    methods = (declaration / "stages/discount/methods.bl").read_text(encoding="utf-8")
    source = (CONS_PORT / "stages/disc/methods.bl").read_text(encoding="utf-8")
    assert methods == source.replace("@methods: disc\n", "@methods: discount\n", 1) != source
    recipe = declaration / "spec.yml"
    text = filled(recipe.read_text(encoding="utf-8"))
    for slot, written in (
        ("discount_calibration", "[calibration/portfolio]"),
        ("discount_settings", "[]"),
        *((creation.slot_name("bequest", kind), "[]") for kind in creation.SLOT_KINDS),
    ):
        text = text.replace(f"[${slot}]", written)
    recipe.write_text(text, encoding="utf-8")
    specified = specify_trellis(load_recipe(declaration, "spec.yml"))
    stages = specified["periods"][0]["stages"]
    assert [(key, stage.name) for key, stage in stages.items()] == [
        ("port", "port"),
        ("discount", "discount"),
        ("bequest", "bequest"),
    ]
    assert stages["discount"].methods
    added = dict(creation.add_stage(created.folder, "renter", NOPORT_ID).new_files)
    stage = added["declaration/stages/renter/renter.bl"]
    assert stage == (CONS_PORT / "stages/noport/noport.bl").read_text(encoding="utf-8").replace(
        "@stage: noport\n", "@stage: renter\n", 1
    )
    # the addition's copy names the key on its `@methods:` line
    assert added["declaration/stages/renter/methods.bl"] == (
        (CONS_PORT / "stages/noport/methods.bl")
        .read_text(encoding="utf-8")
        .replace("@methods: noport\n", "@methods: renter\n", 1)
    )


def test_new_trellis_writes_the_terminal_period_out_with_the_stages_marked_for_it(repository):
    """Unit K, Task 12 (walkthrough §4 item 7): a stage marked for the
    terminal period stands in periods[0] alone. trellis.yml writes the
    terminal period out, as applications/durables/declaration/trellis.yml
    does, its `stages` every key chosen and its connectors one empty
    mapping, then period.yml, which lists the other keys, repeated for the
    periods before it; answers.yml records the two entries as the trellis
    file writes them. Once the slots are filled the trellis is specified,
    the bequest an occurrence of periods[0] alone, named by its key; and a
    period added between two periods splits answers.yml's entry as it
    splits the trellis file's."""
    work, _ = repository
    created = creation.create_trellis(
        work, "terminal-demo", list(BEQUEST_STAGES), "demo_period", 6, terminal=["bequest"]
    )
    declaration = created.folder / "declaration"
    trellis = (declaration / "trellis.yml").read_text(encoding="utf-8")
    assert entry_value(trellis, "periods") == [
        {"stages": TERMINAL_KEYS, "connectors": [{}]},
        {"template": "period.yml", "repeat": 5},
    ]
    assert entry_value(trellis, "inter_connectors") == [{}]
    period = (declaration / "period.yml").read_text(encoding="utf-8")
    assert entry_value(period, "stages") == ["port", "cons", "disc"]
    answers = (created.folder / creation.ANSWERS).read_text(encoding="utf-8")
    assert entry_value(answers, "periods") == [
        {"stages": TERMINAL_KEYS, "repeat": 1},
        {"label": "demo_period", "file": "period.yml", "repeat": 5},
    ]
    assert creation.checklist(created.folder) == ()
    recipe = declaration / "spec.yml"
    text = filled(recipe.read_text(encoding="utf-8"))
    for kind in creation.SLOT_KINDS:
        text = text.replace(f"[${creation.slot_name('bequest', kind)}]", "[]")
    recipe.write_text(text, encoding="utf-8")
    read = load_recipe(declaration, "spec.yml")
    assert [list(period["stages"]) for period in read["periods"]] == [TERMINAL_KEYS] + [
        TERMINAL_KEYS[:3]
    ] * 5
    specified = specify_trellis(read)
    assert [list(period["stages"]) for period in specified["periods"]] == [TERMINAL_KEYS] + [
        TERMINAL_KEYS[:3]
    ] * 5
    bequest = specified["periods"][0]["stages"]["bequest"]
    assert bequest.name == "bequest"
    added = creation.add_period(created.folder, "middle", ["port", "cons", "disc"], at=3)
    edited = added.edits[str((created.folder / creation.ANSWERS).resolve())]
    assert entry_value(edited, "periods") == [
        {"stages": TERMINAL_KEYS, "repeat": 1},
        {"label": "demo_period", "file": "period.yml", "repeat": 2},
        {"label": "middle", "file": "period.middle.yml", "repeat": 1},
        {"label": "demo_period", "file": "period.yml", "repeat": 3},
    ]


def test_new_trellis_without_a_terminal_period_writes_the_period_repeated(repository):
    """Unit K, Task 12, the review's focus: a form with no stage marked for
    the terminal period writes trellis.yml as it did before the choice
    existed, period.yml repeated for every period with one empty
    inter-period mapping, and answers.yml one entry; so does a form whose
    trellis has one period, that period being the terminal one, which holds
    every stage chosen."""
    work, _ = repository
    created = creation.create_trellis(work, "plain-demo", list(DEMO_STAGES), "demo_period", 6)
    assert (created.folder / "declaration/trellis.yml").read_text(encoding="utf-8") == (
        "!trellis\n"
        "name: plain_demo\n"
        "# periods[0] is the terminal period and periods[h] lies h periods before it.\n"
        "periods:\n"
        "  - {template: period.yml, repeat: 6}\n"
        "# One mapping stands for every adjacent pair, {continuation field of a\n"
        "# period: arrival field of the period after it}: type it in place of the\n"
        "# empty mapping below.\n"
        "inter_connectors:\n"
        "  - {}\n"
    )
    answers = (created.folder / creation.ANSWERS).read_text(encoding="utf-8")
    assert entry_value(answers, "periods") == [
        {"label": "demo_period", "file": "period.yml", "repeat": 6}
    ]
    one = creation.create_trellis(
        work, "one-period", list(BEQUEST_STAGES), "demo_period", 1, terminal=["bequest"]
    )
    declaration = one.folder / "declaration"
    trellis = (declaration / "trellis.yml").read_text(encoding="utf-8")
    assert entry_value(trellis, "periods") == [{"template": "period.yml", "repeat": 1}]
    period = (declaration / "period.yml").read_text(encoding="utf-8")
    assert entry_value(period, "stages") == TERMINAL_KEYS


def test_new_trellis_from_the_form_opens_the_recipe_and_offers_the_commit(
    repository, app_state, matsya_state
):
    """The form "new trellis" filled and submitted, the test repository's
    folder typed as the parent folder (unit L, Task 13), writes the folder
    under it, opens it in the tab with the recipe in the
    editor and its checklist read, and opens the commit form with the new
    folder's files and a message, nothing committed (spec 0.3 §4); the
    Matsya window's exchanges, asked in the conversation named by the
    folder left, are emptied (D-M2, C-K47). Each template's row names in its
    hover the files it brings by their paths from the template's folder,
    the folder of the corpus file that binds it, whatever key it is chosen
    under, and `brings no file` where it brings none (unit K, Task 12; the
    usability walkthrough §4 items 20 and 21; unit L, Task 23, design pass 4
    §3)."""
    work, _ = repository
    app_state(work)
    matsya_state.exchanges.value = (
        matsya_state.Exchange("What is a perch?", "An information set of a stage."),
    )
    app.open_form("new trellis")

    def button(template_id):
        # the button of the template's row, which carries its hover
        (found,) = [
            widget
            for widget in rendered.find(v.Html, tag="button").widgets
            if widget.attributes.get("data-template") == template_id
        ]
        return found

    _, rendered = solara.render(app.NewTrellisForm(), handle_error=False)
    try:
        # the parent folder, which the field reads when it is left
        enter_text(rendered, "Parent folder", str(work))
        enter_text(rendered, "Name", "lifecycle-demo")
        enter_text(rendered, "Periods", "6")
        for template_id in (PORT_ID, CONS_ID, DISC_ID):
            button(template_id).fire_event("click", {})
        brought = {
            CONS_ID: "brings calibration/portfolio.yml, settings/cons_wide.yml, stages/cons/methods.bl",
            NOPORT_ID: "brings calibration/portfolio.yml, settings/noport.yml, stages/noport/methods.bl",
        }
        for template_id, text in brought.items():
            assert button(template_id).attributes["title"].endswith(f" · {text}")
        # the pension worker brings its settings file and its addition
        # (decision S7-W2)
        assert button(WORKER_ID).attributes["title"].endswith(
            " · brings settings/worker_saving.yml, stages/worker_saving/methods.bl"
        )
        disc_files = "brings calibration/portfolio.yml, stages/disc/methods.bl"
        assert button(DISC_ID).attributes["title"].endswith(f" · {disc_files}")
        disc = rendered.find(v.Html, attributes={"data-template": DISC_ID})
        enter_text(disc, "Stage key", "discount")
        assert button(DISC_ID).attributes["title"].endswith(f" · {disc_files}")
        disc = rendered.find(v.Html, attributes={"data-template": DISC_ID})
        enter_text(disc, "Stage key", "disc")
        press_words(rendered, "Write the folder")
    finally:
        rendered.close()
    assert app.form_error.value == ""
    assert app.tab_folder.value.root == (work / "lifecycle-demo").resolve()
    assert app.open_path.value == "declaration/spec.yml"
    assert app.checklist.value == ()
    assert app.form_open.value == "commit"
    assert app.commit_message.value.startswith("New trellis lifecycle-demo")
    assert {change.path for change in app.commit_changes.value} == set(DEMO_FILES)
    assert git(work, "rev-list", "--count", "HEAD").strip() == "1"
    assert matsya_state.exchanges.value == ()


def test_new_trellis_form_asks_each_chosen_stage_for_the_periods_that_hold_it(
    repository, app_state
):
    """Unit K, Task 12 (the usability walkthrough §4 items 7 and 21; unit L,
    Task 23, design pass 4 §3): in the form "new trellis" a template's row
    prints its parameters on its own line, none where it declares none, and
    names in its hover the files it brings, `brings no file` where it
    brings none; once chosen, a row offers `every period`
    and `terminal period`, `every period` marked until `terminal period` is
    pressed, each mark also the button's `aria-pressed`; the form, the test
    repository's folder typed as the parent folder (unit L, Task 13), writes
    a stage marked `terminal period` into the terminal period alone, and the
    form "add stage" offers no such choice."""
    work, _ = repository
    app_state(work)
    app.open_form("new trellis")

    def button(rendered, template_id):
        # the button of the template's row, which carries its hover
        (found,) = [
            widget
            for widget in rendered.find(v.Html, tag="button").widgets
            if widget.attributes.get("data-template") == template_id
        ]
        return found

    def marks(rendered, template_id):
        row = rendered.find(v.Html, attributes={"data-template": template_id})
        buttons = [row.find(v.Html, tag="button", children=[word]).widget for word in PERIOD_WORDS]
        return [
            ("bl-active" in button.class_.split(), button.attributes["aria-pressed"])
            for button in buttons
        ]

    _, rendered = solara.render(app.NewTrellisForm(), handle_error=False)
    try:
        port = rendered.find(v.Html, attributes={"data-template": PORT_ID})
        calibration = "bl-template-calibration bl-code-small"
        assert port.find(v.Html, class_=calibration).widget.children == [
            "R, μ_Ψ, σ_Ψ, μ_θ, σ_θ, ρ_ζ"
        ]
        terminal = rendered.find(v.Html, attributes={"data-template": TERMINAL_ID})
        assert terminal.find(v.Html, class_=calibration).widget.children == [""]
        # the terminal stage brings its methods file (decision MB-V38)
        assert button(rendered, TERMINAL_ID).attributes["title"].endswith(
            " · brings stages/terminal/methods.bl"
        )
        assert not terminal.find(v.Html, tag="button", children=[PERIOD_WORDS[1]]).widgets
        enter_text(rendered, "Parent folder", str(work))
        enter_text(rendered, "Name", "bequest-demo")
        enter_text(rendered, "Periods", "3")
        for _, template_id in BEQUEST_STAGES:
            button(rendered, template_id).fire_event("click", {})
        terminal = rendered.find(v.Html, attributes={"data-template": TERMINAL_ID})
        enter_text(terminal, "Stage key", "bequest")
        assert marks(rendered, TERMINAL_ID) == [(True, "true"), (False, "false")]
        terminal = rendered.find(v.Html, attributes={"data-template": TERMINAL_ID})
        terminal.find(v.Html, tag="button", children=[PERIOD_WORDS[1]]).widget.fire_event(
            "click", {}
        )
        assert marks(rendered, TERMINAL_ID) == [(False, "false"), (True, "true")]
        assert marks(rendered, PORT_ID) == [(True, "true"), (False, "false")]
        press_words(rendered, "Write the folder")
    finally:
        rendered.close()
    assert app.form_error.value == ""
    folder = work / "bequest-demo"
    trellis = (folder / "declaration/trellis.yml").read_text(encoding="utf-8")
    assert entry_value(trellis, "periods") == [
        {"stages": TERMINAL_KEYS, "connectors": [{}]},
        {"template": "period.yml", "repeat": 2},
    ]
    app.open_form("add stage")
    _, rendered = solara.render(app.AddStageForm(), handle_error=False)
    try:
        button(rendered, NOPORT_ID).fire_event("click", {})
        row = rendered.find(v.Html, attributes={"data-template": NOPORT_ID})
        # the key field of the form "add stage" stands under the list
        form_field(rendered, "Stage key").assert_single()
        for word in PERIOD_WORDS:
            assert not row.find(v.Html, tag="button", children=[word]).widgets
    finally:
        rendered.close()


def test_new_trellis_with_unsaved_text_writes_nothing(repository, app_state):
    """While a buffer of the tab holds unsaved text, "new trellis" is
    refused with a sentence naming the file, nothing is written, and the
    tab keeps its folder and its buffer (spec 0.3 §2.2 rule 3)."""
    work, _ = repository
    app_state(work)
    app.open_file("README.md")
    held = app.buffers.value["README.md"]
    app.buffers.value = {"README.md": {**held, "text": held["text"] + "typed\n"}}
    app.submit_new_trellis(
        str(work), "lifecycle-demo", "", "lifecycle_demo_period", 6, [("cons", CONS_ID)]
    )
    assert "README.md" in app.form_error.value
    assert not (work / "lifecycle-demo").exists()
    assert app.tab_folder.value.root == work.resolve()
    assert app.buffers.value["README.md"]["text"].endswith("typed\n")


def test_add_stage_refuses_a_recipe_the_writer_cannot_extend_and_writes_nothing(tmp_path):
    """ "Add stage" on a recipe whose last row is an alias of a mapping
    written elsewhere in the file, a layout `append_to_mapping` cannot
    extend, is refused with a sentence naming the recipe, and every file of
    the folder is unchanged on disk (spec 0.3 §3.2)."""
    folder = written_from_the_forms(tmp_path / "demo")
    recipe = folder / creation.factory_path(creation.RECIPE)
    row = (
        "  stage: stages/disc/disc.bl\n"
        + "".join(
            f"  {kind}: {{all: [${creation.slot_name('disc', kind)}]}}\n"
            for kind in creation.SLOT_KINDS
        )
        + "  methods: {all: []}\n"
    )
    recipe.write_text(
        recipe.read_text(encoding="utf-8")
        .replace("stages:\n", f"disc_row: &disc\n{row}stages:\n")
        .replace(f"  disc: {creation.recipe_row('disc')}\n", "  disc: *disc\n"),
        encoding="utf-8",
    )
    before = {path: path.read_bytes() for path in folder.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="declaration/spec.yml: the layout of the file at stages"):
        creation.add_stage(folder, "noport", NOPORT_ID)
    assert {path: path.read_bytes() for path in folder.rglob("*") if path.is_file()} == before
    assert not (folder / "declaration/stages/noport").exists()


def test_item_2_add_stage_copies_a_stage_and_its_companions(repository):
    """ "Add stage" answers, writing nothing (spec 0.4 §3.5; ruling J-P5),
    the template's stage file as a new file in the stage's own folder under
    the key, with the methods file the template brings, and the calibration
    and settings files the folder does not hold yet, each with its source's
    text; the recipe with the stage's row added, the period file with its
    key and answers.yml with its slots, each by its resolved path with the
    text it was made from, keeping its other lines; and the status line's
    parts, the periods the period file writes and the new files. No slot
    of the edited texts is a checklist entry (K-D29); once the files
    are written the factory reads four stages per period; a key whose stage
    folder exists is refused (spec 0.3 §4; C item 2)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    recipe = created.folder / "declaration/spec.yml"
    period = created.folder / "declaration/period.yml"
    answers = created.folder / creation.ANSWERS
    before = file_bytes(created.folder)
    added = creation.add_stage(created.folder, "noport", NOPORT_ID)
    assert [path for path, _ in added.new_files] == [
        "declaration/stages/noport/noport.bl",
        "declaration/settings/noport.yml",
        "declaration/stages/noport/methods.bl",
    ]
    new = dict(added.new_files)
    for path, source in (
        ("declaration/stages/noport/noport.bl", CONS_PORT / "stages/noport/noport.bl"),
        ("declaration/stages/noport/methods.bl", CONS_PORT / "stages/noport/methods.bl"),
    ):
        # copied under its own key, each file keeps every byte
        assert new[path].encode("utf-8") == source.read_bytes()
    edited = [str(path.resolve()) for path in (recipe, period, answers)]
    assert list(added.edits) == list(added.read) == edited
    assert added.read == {path: Path(path).read_text(encoding="utf-8") for path in edited}
    assert added.edits[edited[0]] == (
        added.read[edited[0]] + NOPORT_ROW
    )
    assert added.edits[edited[1]] == added.read[edited[1]].replace(
        "  - disc\n", "  - disc\n  - noport\n"
    )
    assert added.notes == (
        "period.yml, stages: noport written, periods 0–5",
        "new: stages/noport/noport.bl, settings/noport.yml, stages/noport/methods.bl",
    )
    assert file_bytes(created.folder) == before
    assert creation.checklist(created.folder, added.edits) == ()
    assert creation.checklist(created.folder) == ()
    save_added(created.folder, added)
    read = load_recipe(created.folder / "declaration", "spec.yml")
    assert list(read["periods"][0]["stages"]) == ["port", "cons", "disc", "noport"]
    with pytest.raises(ValueError, match="declaration/stages/noport/ exists"):
        creation.add_stage(created.folder, "noport", NOPORT_ID)
    (created.folder / "declaration/stages/other").mkdir()
    with pytest.raises(ValueError, match="declaration/stages/other/ exists"):
        creation.add_stage(created.folder, "other", NOPORT_ID)
    # a folder that new trellis did not write and that holds no recipe; the
    # portfolio model's folder holds its recipe since 4 October 2026
    with pytest.raises(ValueError, match="holds no declaration/spec.yml"):
        creation.add_stage(CORPUS / "buffer-stock", "noport", NOPORT_ID)
    with pytest.raises(ValueError, match="YAML reads"):
        creation.add_stage(created.folder, "yes", NOPORT_ID)
    assert not (created.folder / "declaration/stages/yes").exists()


# the stage folder of the portfolio model's `port`, which holds its stage
# file, its methods file and its page
PORT_FOLDER = PORTFOLIO / "stages/port"


def sha256_of(path: Path) -> str:
    """The SHA-256 of the bytes of the file `path`, in hexadecimal."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def other_project(parent: Path) -> Path:
    """A stage folder of another project under `parent`, in the one layout
    of a model folder, `other-project/declaration/stages/port/`, whose
    README.md titles the project `The other project`: the portfolio stage
    file `port.bl` and its page `port.md`; the four files a recipe binds,
    the calibration `calibration.yml` and the settings `wide.yml` of
    cons-port's port, and the addition `methods.bl` of the portfolio
    model's port; and `notes.yml`, whose one top key names no kind."""
    project = parent / "other-project"
    folder = project / "declaration/stages/port"
    folder.mkdir(parents=True)
    (project / "README.md").write_text("---\ntitle: The other project\n---\n", encoding="utf-8")
    for name, source in (
        ("port.bl", PORT_FOLDER / "port.bl"),
        ("port.md", PORT_FOLDER / "port.md"),
        ("calibration.yml", CONS_PORT / "calibration/portfolio.yml"),
        ("wide.yml", CONS_PORT / "settings/port_wide.yml"),
        ("methods.bl", PORT_FOLDER / "methods.bl"),
    ):
        (folder / name).write_bytes(source.read_bytes())
    (folder / "notes.yml").write_text("notes: [the grid is wide]\n", encoding="utf-8")
    return folder


def test_k_a_stage_folder_of_the_disk_is_copied_as_a_template_with_its_origin(
    repository, tmp_path
):
    """Unit K, Task 25 (K-D26): a stage folder of another project, given by
    its full path, is read as a template of the corpus is read: its key the
    folder's name, its stage file, its project's title, the parameters the
    stage declares, and the calibration and settings files of the folder,
    each told by its one top key, and its addition, told by its first line,
    a page and a YAML file of another key brought by none. "Add stage"
    copies it under another key through the template's writers, writing
    nothing: the stage file and the addition in the stage's folder, naming
    the key, the calibration and the
    settings under `calibration/` and `settings/`; the recipe and the period
    file edited as for a template, neither naming the origin; and
    answers.yml records, in place of a template's id, the path as given and
    the SHA-256 of each file the stage brings. No path of the copy leaves
    the model folder, and nothing is written in the origin's folder."""
    disk = tmp_path / "disk"
    folder = other_project(disk)
    given = str(folder)
    record = creation.folder_template(given)
    assert (record.id, record.origin, record.key) == (given, given, "port")
    assert record.stage == (folder / "port.bl").resolve()
    assert record.model == "The other project"
    assert record.calibration == creation.template_of(PORT_ID).calibration
    assert record.companions == {
        "calibration": ((folder / "calibration.yml").resolve(),),
        "settings": ((folder / "wide.yml").resolve(),),
        "methods": ((folder / "methods.bl").resolve(),),
    }
    assert creation.brought_files(record) == ("calibration.yml", "wide.yml", "methods.bl")
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    before, origin_before = file_bytes(created.folder), file_bytes(disk)
    added = creation.add_stage(created.folder, "renter", record)
    new = dict(added.new_files)
    assert list(new) == [
        "declaration/stages/renter/renter.bl",
        "declaration/calibration/calibration.yml",
        "declaration/settings/wide.yml",
        "declaration/stages/renter/methods.bl",
    ]
    assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in new)
    source = (folder / "port.bl").read_text(encoding="utf-8")
    assert new["declaration/stages/renter/renter.bl"] == source.replace(
        "@stage: port\n", "@stage: renter\n", 1
    )
    methods = (folder / "methods.bl").read_text(encoding="utf-8")
    assert new["declaration/stages/renter/methods.bl"] == methods.replace(
        "@methods: port\n", "@methods: renter\n", 1
    )
    for path, name in (
        ("declaration/calibration/calibration.yml", "calibration.yml"),
        ("declaration/settings/wide.yml", "wide.yml"),
    ):
        assert new[path].encode("utf-8") == (folder / name).read_bytes()
    recipe, period, answers = (
        str((created.folder / name).resolve())
        for name in (RECIPE_FILE, "declaration/period.yml", creation.ANSWERS)
    )
    assert list(added.edits) == [recipe, period, answers]
    assert added.edits[recipe] == (
        added.read[recipe]
        + f"  renter: {creation.recipe_row('renter', ('stages/renter/methods.bl',))}\n"
    )
    assert all(given not in added.edits[path] for path in (recipe, period))
    assert entry_value(added.edits[answers], "stages.renter") == {
        "origin": given,
        "sha256": {
            name: sha256_of(folder / name)
            for name in ("port.bl", "calibration.yml", "wide.yml", "methods.bl")
        },
    }
    slots = entry_value(added.edits[answers], "required.slots")
    assert slots[-2:] == [creation.slot_name("renter", kind) for kind in creation.SLOT_KINDS]
    assert added.notes == (
        "period.yml, stages: renter written, periods 0–5",
        "new: stages/renter/renter.bl, calibration/calibration.yml, settings/wide.yml, "
        "stages/renter/methods.bl",
    )
    assert file_bytes(created.folder) == before
    assert file_bytes(disk) == origin_before
    save_added(created.folder, added)
    read = load_recipe(created.folder / "declaration", "spec.yml")
    assert list(read["periods"][0]["stages"]) == ["port", "cons", "disc", "renter"]
    assert file_bytes(disk) == origin_before


def test_k_a_stage_file_given_itself_brings_no_companion_from_a_folder_of_its_own(
    repository, tmp_path
):
    """Unit K, Task 25 (K-D26): the stage file itself may be given, here
    the pension model's `terminal.bl` alone in a folder `bequest_stage` that
    stands in no model folder: the key proposed is the folder's name, the
    model the folder's name, and no file is brought. "Add stage" copies the
    stage file alone, its `@stage:` line naming the key, and answers.yml
    records the file's path as given and its one SHA-256."""
    folder = tmp_path / "loose/bequest_stage"
    folder.mkdir(parents=True)
    terminal = CORPUS / "pension-retirement/declaration/stages/terminal/terminal.bl"
    (folder / "terminal.bl").write_bytes(terminal.read_bytes())
    given = str(folder / "terminal.bl")
    record = creation.folder_template(given)
    assert (record.id, record.origin, record.key, record.model) == (
        given,
        given,
        "bequest_stage",
        "bequest_stage",
    )
    assert record.companions == {"calibration": (), "settings": (), "methods": ()}
    assert creation.brought_files(record) == ()
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    added = creation.add_stage(created.folder, record.key, record)
    assert [(path, text.splitlines()[0]) for path, text in added.new_files] == [
        ("declaration/stages/bequest_stage/bequest_stage.bl", "@stage: bequest_stage")
    ]
    answers = str((created.folder / creation.ANSWERS).resolve())
    assert entry_value(added.edits[answers], "stages.bequest_stage") == {
        "origin": given,
        "sha256": {"terminal.bl": sha256_of(terminal)},
    }


def test_a_template_offers_no_derived_parameter_as_a_calibration_input(tmp_path):
    """The parameters a template's calibration must give are the declared
    parameters of its stage file and no derived parameter, whose value its
    definition computes and for which `calibrate` refuses a value: the
    perfect-foresight stage of the refusal examples declares β, ρ, R and Γ
    and derives h and R_n (AMD-MT-003 build contract §5)."""
    from bellman.refusal_examples import PERFECT_FORESIGHT

    folder = tmp_path / "perfect_foresight"
    folder.mkdir()
    (folder / "perfect_foresight.bl").write_text(PERFECT_FORESIGHT, encoding="utf-8")
    record = creation.folder_template(str(folder))
    assert record.calibration == ("β", "ρ", "R", "Γ")


def test_k_a_folder_that_holds_no_single_stage_file_is_refused(tmp_path):
    """Unit K, Task 25 (K-D26): `folder_template` refuses, each in one
    sentence that names the path as given, a folder that holds no `.bl`
    file, one that holds two stage files, a file that is no `.bl` file, a
    path that names nothing, a path that is not full, a folder that holds
    an addition and no stage file, and the path of an addition, which is
    no stage file (decision S7-W11)."""
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "notes.yml").write_text("notes: []\n", encoding="utf-8")
    two = tmp_path / "two"
    two.mkdir()
    for name in ("a.bl", "b.bl"):
        (two / name).write_bytes((PORT_FOLDER / "port.bl").read_bytes())
    addition = tmp_path / "addition"
    addition.mkdir()
    (addition / "methods.bl").write_text("@methods: port\n", encoding="utf-8")
    for path, sentence in (
        (str(empty), f"{empty} holds no stage file"),
        (
            str(two),
            f"{two} holds 2 stage files, a.bl and b.bl: give the path of the one to copy",
        ),
        (str(empty / "notes.yml"), f"{empty / 'notes.yml'} is no .bl file"),
        (str(tmp_path / "nowhere"), f"{tmp_path / 'nowhere'} does not exist"),
        ("stages/port", "stages/port is no full path: write it from / or from ~"),
        (str(addition), f"{addition} holds no stage file"),
        (
            str(addition / "methods.bl"),
            f"{addition / 'methods.bl'} is an addition, not a stage file",
        ),
    ):
        with pytest.raises(ValueError) as refused:
            creation.folder_template(path)
        assert str(refused.value) == sentence


@pytest.mark.parametrize(
    "front_matter",
    ["The other project\n", "title: [The other project\n"],
    ids=["no-mapping", "no-yaml"],
)
def test_k_a_project_page_whose_front_matter_is_no_mapping_titles_it_by_its_folder(
    tmp_path, front_matter
):
    """Unit K's final judgment, §6 item 1: the README.md of another
    project, whose front matter reads as a string and no mapping, or does
    not read as YAML, gives no title, so that the project is titled by its
    folder's name, `other-project`, both by `_model_title` and in the
    template that `folder_template` reads from the project's stage folder,
    where an error raised there would stop the form "add stage"."""
    folder = other_project(tmp_path / "disk")
    project = folder.parents[2]
    (project / "README.md").write_text(f"---\n{front_matter}---\n", encoding="utf-8")
    assert creation._model_title(project) == "other-project"
    assert creation.folder_template(str(folder)).model == "other-project"


# --- the library of stages (AAS, L-D6; unit L, Task 7) ---

# the pension model's terminal stage file, which a stage folder of the
# library holds alone
TERMINAL_FILE = CORPUS / "pension-retirement/declaration/stages/terminal/terminal.bl"


def library_with_two_stages(library: Path) -> Path:
    """`library`, a folder of the library of stages, made with its parents,
    holding two stage folders and four folders that are none: `port`, a copy
    of the portfolio model's stage folder of `port` with a README.md that
    titles it `Portfolio share`; `bequest`, the pension model's
    `terminal.bl` alone; `notes`, which holds no stage file; `two`, which
    holds two; `broken`, whose one stage file the package refuses; and
    `.hidden`, a copy of `port` whose name begins with "."; and the stage
    file `loose.bl` in the library itself. Answers the library."""
    shutil.copytree(PORT_FOLDER, library / "port")
    (library / "port/README.md").write_text("---\ntitle: Portfolio share\n---\n", encoding="utf-8")
    shutil.copytree(library / "port", library / ".hidden")
    for name in ("bequest", "notes", "two", "broken"):
        (library / name).mkdir()
    (library / "bequest/terminal.bl").write_bytes(TERMINAL_FILE.read_bytes())
    (library / "notes/README.md").write_text("notes on the stages\n", encoding="utf-8")
    for name in ("a.bl", "b.bl"):
        (library / "two" / name).write_bytes(TERMINAL_FILE.read_bytes())
    (library / "broken/broken.bl").write_text("@stage: broken\nno stage\n", encoding="utf-8")
    (library / "loose.bl").write_bytes(TERMINAL_FILE.read_bytes())
    return library


def test_l_each_folder_of_the_library_that_holds_one_stage_file_is_a_stage_of_it(
    tmp_path, monkeypatch
):
    """Unit L, Task 7 (AAS, L-D6): with `BELLMAN_STAGE_LIBRARY` naming a
    folder that holds two stage folders, `bequest` and `port`, and four
    folders that are none, the library is that folder alone, and its stages
    are the two, in the order of their names, each the template that
    `folder_template` reads from its full path, which is its id and its
    origin, keyed by its folder's name: `port` titled by its README.md, with
    the parameters the corpus's `port` declares and its methods file
    brought; `bequest`, which has no README.md, titled by its folder's name
    and bringing no file. A folder whose stage file the package refuses is
    left out, and nothing is refused. A file of a stage folder changed is
    read again: a new title in port's README.md is the stage's title at the
    next reading. Nothing in the library is written."""
    library = library_with_two_stages(tmp_path / "library")
    before = file_bytes(library)
    monkeypatch.setenv(creation.LIBRARY_VARIABLE, str(library))
    assert creation.library_folders() == (library,)
    stages = creation.library_templates()
    assert stages == tuple(
        creation.folder_template(str(library / name)) for name in ("bequest", "port")
    )
    assert [(stage.id, stage.origin, stage.key, stage.model) for stage in stages] == [
        (str(library / "bequest"), str(library / "bequest"), "bequest", "bequest"),
        (str(library / "port"), str(library / "port"), "port", "Portfolio share"),
    ]
    assert stages[1].calibration == creation.template_of(PORT_ID).calibration
    assert [creation.brought_files(stage) for stage in stages] == [(), ("methods.bl",)]
    assert file_bytes(library) == before
    (library / "port/README.md").write_text(
        "---\ntitle: The share of risky assets\n---\n", encoding="utf-8"
    )
    assert creation.library_templates()[1].model == "The share of risky assets"


def test_l_an_unset_variable_reads_the_library_under_the_home_folder_where_it_exists(
    tmp_path, monkeypatch
):
    """Unit L, Task 7 (AAS, L-D6): with `BELLMAN_STAGE_LIBRARY` unset, or
    holding spaces alone, and no `~/.bellman/library/` under the home
    folder, there is no folder and no stage of the library, and nothing is
    refused; once `~/.bellman/library/` exists, it is the library. A
    variable that names only a folder that does not exist gives no library,
    the folder under the home folder then not being read."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv(creation.LIBRARY_VARIABLE, raising=False)
    assert (creation.library_folders(), creation.library_templates()) == ((), ())
    monkeypatch.setenv(creation.LIBRARY_VARIABLE, "  ")
    assert (creation.library_folders(), creation.library_templates()) == ((), ())
    library = library_with_two_stages(home / ".bellman/library")
    assert creation.library_folders() == (library,)
    assert [stage.key for stage in creation.library_templates()] == ["bequest", "port"]
    monkeypatch.setenv(creation.LIBRARY_VARIABLE, str(tmp_path / "nowhere"))
    assert (creation.library_folders(), creation.library_templates()) == ((), ())


def test_l_library_folders_joined_by_the_path_separator_are_read_in_their_order(
    tmp_path, monkeypatch
):
    """Unit L, Task 7 (AAS, L-D6): `BELLMAN_STAGE_LIBRARY` naming, joined by
    the path separator, a second library, a folder that does not exist, a
    path that is not full, the first library from `~` with spaces around
    it, and the second library again gives the two libraries in that order,
    each once, and their stages in that order: the second's `bequest` and
    `port`, then the first's `renter`."""
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    first = home / "first"
    shutil.copytree(PORT_FOLDER, first / "renter")
    second = library_with_two_stages(tmp_path / "second")
    named = [str(second), str(tmp_path / "nowhere"), "relative/library", "  ~/first ", str(second)]
    monkeypatch.setenv(creation.LIBRARY_VARIABLE, os.pathsep.join(named))
    assert creation.library_folders() == (second, first)
    assert [(stage.key, stage.id) for stage in creation.library_templates()] == [
        ("bequest", str(second / "bequest")),
        ("port", str(second / "port")),
        ("renter", str(first / "renter")),
    ]


def test_add_period_writes_the_earliest_period(repository):
    """ "Add period" answers, writing nothing (spec 0.4 §3.6; ruling J-P5),
    `period.<label>.yml` in `declaration/` with the stages chosen as a new
    file, the trellis file's text with its entry appended at the end of the
    list, the earliest period of the model, and answers.yml's text with the
    period; and the status line's parts, the entry, the period it reaches
    and the new file. Once the files are written the factory reads seven
    periods, the last of the two stages chosen; answers.yml names each
    period's file as the trellis file's `template:` does, by its name in
    `declaration/`, the rule `answers_text` states; a stage the recipe does
    not hold is refused, and nothing is written (spec 0.3 §4; merge note
    M8)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    before = file_bytes(created.folder)
    added = creation.add_period(created.folder, "young", ["cons", "disc"])
    assert added.new_files == (
        ("declaration/period.young.yml", creation.period_text("young", ["cons", "disc"])),
    )
    edited = [
        str((created.folder / path).resolve())
        for path in ("declaration/trellis.yml", "answers.yml")
    ]
    assert list(added.edits) == list(added.read) == edited
    assert (
        "  - {template: period.yml, repeat: 6}\n  - {template: period.young.yml, repeat: 1}\n"
    ) in added.edits[edited[0]]
    assert added.notes == (
        "trellis.yml, periods: {template: period.young.yml, repeat: 1} written, periods 6",
        "new: period.young.yml",
    )
    assert file_bytes(created.folder) == before
    save_added(created.folder, added)
    read = load_recipe(created.folder / "declaration", "spec.yml")
    assert len(read["periods"]) == 7
    assert list(read["periods"][6]["stages"]) == ["cons", "disc"]
    # the files answers.yml names are the trellis file's templates above
    answers = yaml.safe_load((created.folder / "answers.yml").read_text(encoding="utf-8"))
    assert answers["periods"] == [
        {"label": "demo_period", "file": "period.yml", "repeat": 6},
        {"label": "young", "file": "period.young.yml", "repeat": 1},
    ]
    assert all(
        (created.folder / creation.factory_path(entry["file"])).is_file()
        for entry in answers["periods"]
    )
    with pytest.raises(ValueError, match="holds no stage 'noport'"):
        creation.add_period(created.folder, "old", ["noport"])
    assert not (created.folder / "declaration/period.old.yml").exists()
    with pytest.raises(ValueError, match="declaration/period.young.yml exists"):
        creation.add_period(created.folder, "young", ["cons"])
    with pytest.raises(ValueError, match="YAML reads"):
        creation.add_period(created.folder, "2026", ["cons"])
    assert not (created.folder / "declaration/period.2026.yml").exists()


def test_add_period_keeps_one_inter_period_mapping_for_each_pair(tmp_path):
    """Where trellis.yml writes one inter-period mapping for each adjacent
    pair of periods, "add period" adds an empty mapping for the new pair to
    the text it answers, the file on disk unchanged, so that the factory,
    under its rule trellis-file-shape, reads one more period without a
    refusal once the files are written (spec 0.3 §4; spec 0.4 §3.6)."""
    folder = written_from_the_forms(tmp_path / "demo", repeat=3)
    trellis = folder / "declaration/trellis.yml"
    two = "inter_connectors:\n  - {}\n  - {}\n"
    trellis.write_text(
        trellis.read_text(encoding="utf-8").replace("inter_connectors:\n  - {}\n", two),
        encoding="utf-8",
    )
    assert len(load_recipe(folder / "declaration", "spec.yml")["periods"]) == 3
    added = creation.add_period(folder, "young", ["cons", "disc"])
    assert added.edits[str(trellis.resolve())].endswith(two + "  - {}\n")
    assert trellis.read_text(encoding="utf-8").endswith(two)
    save_added(folder, added)
    read = load_recipe(folder / "declaration", "spec.yml")
    assert (len(read["periods"]), len(read["inter_connectors"])) == (4, 3)


def test_add_stage_edits_the_unsaved_recipe_in_its_buffer(repository, app_state):
    """Spec 0.4 §3.5 and brief rule 9 (unit J's plan, Task 11; ruling J-P5;
    J-D36): with the recipe open and its buffer holding unsaved text, the
    button of "add stage" first asks the editor for its text, and the
    writer edits the recipe in that text. Since the gesture edits closed
    files as well, the editor is first asked to confirm the open document,
    with no replacement. The first time the editor refuses: the form holds
    the sentence that nothing was written, and no file is written, the
    template's stage file included. The second time the editor confirms the
    document: the buffers of the period file and of answers.yml take their
    edits, unsaved, and the template's stage file and companions are
    written to disk; the recipe's own edit is asked last, and once the
    editor applies it the form closes and the status line names the period
    file, the periods it writes and the new files. No file the folder held
    changes on disk, and once the editor's change event brings the recipe's
    new text, the checklist, read from the buffers, lists none of its eight
    slots (K-D29)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    recipe, period = "declaration/spec.yml", "declaration/period.yml"
    app_state(created.folder)
    # the recipe shown is then the folder's first source, its recipe
    app.source.value = None
    try:
        app.open_file(recipe)
        held = app.buffers.value[recipe]
        typed = held["text"] + "# typed\n"
        app.buffers.value = {recipe: {**held, "text": typed}}
        editor = {"path": recipe, "text": typed, "revision": held["document_revision"]}
        before = file_bytes(created.folder)
        app.open_form("add stage")
        asked = app.edit_request.value
        app.submit_add_stage(NOPORT_ID, "noport", creation.PERIOD)
        assert app.edit_request.value is asked
        app.on_change(editor)
        request = app.edit_request.value
        assert request == {"edits": [], "expected": typed, "n": request["n"]}
        answer = {"path": recipe, "revision": held["document_revision"]}
        app.on_applied({**answer, "n": request["n"], "applied": False})
        assert app.form_error.value == (
            f"{recipe}: nothing was written. The text changed after the form read it. "
            "Press the button again."
        )
        assert (app.form_open.value, app.gesturing.value) == ("add stage", None)
        assert file_bytes(created.folder) == before and period not in app.buffers.value
        app.submit_add_stage(NOPORT_ID, "noport", creation.PERIOD)
        assert app.form_error.value == ""
        app.on_change(editor)
        confirm = app.edit_request.value
        assert confirm == {"edits": [], "expected": typed, "n": confirm["n"]}
        app.on_applied({**answer, "n": confirm["n"], "applied": True})
        request = app.edit_request.value
        assert request["n"] != confirm["n"] and app.form_open.value == "add stage"
        new = applied(typed, [model.Replacement(**edit) for edit in request["edits"]])
        assert request["expected"] == typed and new.endswith("# typed\n")
        assert NOPORT_ROW in new
        app.on_applied({**answer, "n": request["n"], "applied": True})
        assert (app.form_open.value, app.form_error.value, app.gesturing.value) == (None, "", None)
        on_disk = (created.folder / period).read_text(encoding="utf-8")
        assert app.buffers.value[period]["text"] == on_disk.replace(
            "  - disc\n", "  - disc\n  - noport\n"
        )
        assert "    - noport_calibration\n" in app.buffers.value[creation.ANSWERS]["text"]
        assert app.gesture_note.value["sentence"] == (
            "period.yml, stages: noport written, periods 0–5; new: stages/noport/noport.bl, "
            "settings/noport.yml, stages/noport/methods.bl"
        )
        after = file_bytes(created.folder)
        assert {path: after[path] for path in before} == before
        assert sorted(set(after) - set(before)) == [
            "declaration/settings/noport.yml",
            "declaration/stages/noport/methods.bl",
            "declaration/stages/noport/noport.bl",
        ]
        app.on_change({**editor, "text": new})
        assert app.checklist.value == ()
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_add_period_with_no_file_open_edits_the_buffers_at_once(repository, app_state):
    """Spec 0.4 §3.6 and brief rule 9, the first step of a gesture skipped
    where no file is open: the button of "add period" edits the buffers of
    the trellis file and of answers.yml at once, each unsaved, writes the
    new period file to disk and closes the form; the two files are
    unchanged on disk, and the status line names the entry, the period it
    reaches and the new file."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    app_state(created.folder)
    app.source.value = None
    try:
        assert app.open_path.value is None
        before = file_bytes(created.folder)
        app.open_form("add period")
        app.submit_add_period("young", ["cons", "disc"])
        assert (app.form_open.value, app.form_error.value, app.gesturing.value) == (None, "", None)
        unsaved = app.unsaved_texts()
        trellis_file = str((created.folder / "declaration/trellis.yml").resolve())
        assert set(unsaved) == {trellis_file, str((created.folder / creation.ANSWERS).resolve())}
        assert "  - {template: period.young.yml, repeat: 1}\n" in unsaved[trellis_file].text
        after = file_bytes(created.folder)
        assert {path: after[path] for path in before} == before
        assert after["declaration/period.young.yml"].decode("utf-8") == creation.period_text(
            "young", ["cons", "disc"]
        )
        assert sorted(set(after) - set(before)) == ["declaration/period.young.yml"]
        assert app.gesture_note.value["sentence"] == (
            "trellis.yml, periods: {template: period.young.yml, repeat: 1} written, periods 6; "
            "new: period.young.yml"
        )
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_the_writers_edit_answers_only_where_it_exists(tmp_path):
    """Spec 0.4 §3.5: on a copy of applications/portfolio-choice, a recipe
    folder of the corpus that holds no answers.yml, "add stage" and "add
    period" are offered (`can_add`): "add stage" edits the recipe and the
    period file, and "add period", reading the recipe "add stage" edited
    from its text, the trellis file; neither edits nor writes answers.yml,
    and no file is written to disk. The recipe's keys are read from the
    texts given (`recipe_keys`)."""
    folder = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
    declaration = folder / creation.FACTORY_FOLDER
    before = file_bytes(folder)
    assert creation.can_add(folder) and creation.period_files(folder) == ("period.yml",)
    stage = creation.add_stage(folder, "worker", WORKER_ID)
    # the pension worker brings its settings file and its addition (decision
    # S7-W2)
    brought = [
        "declaration/stages/worker/worker.bl",
        "declaration/settings/worker_saving.yml",
        "declaration/stages/worker/methods.bl",
    ]
    assert [path for path, _ in stage.new_files] == brought
    edited = [str((declaration / name).resolve()) for name in ("spec.yml", "period.yml")]
    assert list(stage.edits) == edited
    assert stage.notes == (
        "period.yml, stages: worker written, periods 0–5",
        "new: stages/worker/worker.bl, settings/worker_saving.yml, stages/worker/methods.bl",
    )
    keys = ("port", "cons", "disc")
    assert creation.recipe_keys(folder) == keys
    assert creation.recipe_keys(folder, texts=stage.edits) == (*keys, "worker")
    period = creation.add_period(folder, "young", ["worker"], texts=stage.edits)
    assert [path for path, _ in period.new_files] == ["declaration/period.young.yml"]
    assert list(period.edits) == [str((declaration / "trellis.yml").resolve())]
    assert file_bytes(folder) == before and not (folder / creation.ANSWERS).exists()


def test_add_stage_and_add_period_name_every_file_they_write(repository, app_state):
    """With a variant's recipe open in the editor and the folder's recipe
    shown, each form's note names, in one line, every file the form writes,
    by its path from the model folder (ruling R64 of the model folder's
    layout; AMD-MI-002 §6a rule 2): "add stage" names declaration/, where
    it writes the stage, the recipe declaration/spec.yml, the period file
    chosen, the note following the choice, and answers.yml; "add period"
    names the period file it writes, declaration/trellis.yml and
    answers.yml. Neither names a file of the variant (spec 0.3 §4). In a
    folder without answers.yml neither names it (spec 0.4 §3.5)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    save_added(created.folder, creation.add_period(created.folder, "young", ["cons", "disc"]))
    creation.create_variant(created.folder, "two-stages", "spec.yml")
    app_state(created.folder)
    app.source.value = None
    app.open_file("declaration/spec.two-stages.yml")
    # the forms' notes with answers.yml and, after it is removed, without it
    # (unit L, Task 23: each a line under the form's head, as design pass 4
    # §3 writes it, `writes …` with no full stop)
    notes = (
        (
            "writes the stage into declaration/ and adds it to declaration/spec.yml, "
            "declaration/{} and answers.yml",
            "writes declaration/period.<label>.yml and adds the period, the earliest, to "
            "declaration/trellis.yml and answers.yml",
        ),
        (
            "writes the stage into declaration/ and adds it to declaration/spec.yml and "
            "declaration/{}",
            "writes declaration/period.<label>.yml and adds the period, the earliest, to "
            "declaration/trellis.yml",
        ),
    )
    for number, (stage_note, period_note) in enumerate(notes):
        if number == 1:
            (created.folder / creation.ANSWERS).unlink()
        _, rendered = solara.render(app.AddStageForm(), handle_error=False)
        try:
            note = rendered.find(v.Html, class_="bl-form-note")
            assert note.widget.children == [stage_note.format("period.yml")]
            enter_text(rendered, "Period file", "period.young.yml")
            note = rendered.find(v.Html, class_="bl-form-note")
            assert note.widget.children == [stage_note.format("period.young.yml")]
        finally:
            rendered.close()
        _, rendered = solara.render(app.AddPeriodForm(), handle_error=False)
        try:
            assert rendered.find(v.Html, class_="bl-form-note").widget.children == [period_note]
        finally:
            rendered.close()
    assert app.open_path.value == "declaration/spec.two-stages.yml"


# --- a stage and the files of the author's own (unit K, Task 9; K-D7) ---

# the empty stage `buyer` that "new stage" writes (K-D7, amended by unit L,
# Task 17): the stage's line and the four block headers of the page Stages,
# each with no field on either side and the body `0 = 0`, the smallest body
# the grammar admits
BUYER_STAGE = """\
@stage: buyer

[id=arvl_to_dcsn, () : !arvl -> () : !dcsn] {
    0 = 0
}
[id=dcsn_to_cntn, () : !dcsn -> () : !cntn] {
    0 = 0
}
[id=cntn_to_dcsn, () : !cntn -> () : !dcsn] {
    0 = 0
}
[id=dcsn_to_arvl, () : !dcsn -> () : !arvl] {
    0 = 0
}
"""
# the page that names the blocks of a stage file, and a block header it
# writes in a stage file: the block's id and the perch word of each side
STAGE_PAGE = ROOT / "docs/Bellman-Sym/01-stage.md"
PAGE_HEADER = re.compile(r"^\[id=(\w+), .*\) : !(\w+) -> .*\) : !(\w+)\] \{$", re.M)
# the files "new file" writes for the stage buyer, each with its text
BUYER_SOURCES = {
    "calibration": ("declaration/calibration/buyer.yml", "calibration: {}\n"),
    "settings": ("declaration/settings/buyer.yml", "settings: {}\n"),
    "methods": ("declaration/stages/buyer/methods.bl", "@methods: buyer\n"),
}


def test_new_stage_answers_the_empty_stage_and_the_recipe_s_row(tmp_path):
    """Unit K's decision K-D7 (plan, Task 9): on a copy of the portfolio
    model, a recipe folder with no answers.yml, "new stage" answers, writing
    nothing, the stage file declaration/stages/buyer/buyer.bl, the stage's
    line and the four block headers as the page Stages writes them, each
    with no field; the recipe with the stage's row and its two slots
    added, by its resolved path with the text it was made from; and
    the status line's parts. No slot of the edited text is a checklist
    entry (K-D29). The file parses, each block holding the equation `0 = 0`,
    the smallest body the grammar admits, and the package constructs it as a
    stage with no field, its builders graphs refused while no block declares
    an output; the box `add field` of the continuation table, the sides
    placed by the pairs the headers write (`model.header_pairs`), writes the
    first field `a : ℝ₊` into the output side of dcsn_to_cntn (unit L, Task
    17; defect 7 of the UX simulation). A key whose folder exists, a key the
    recipe holds, a key YAML reads as a boolean, a key that is no identifier
    and a folder with no recipe are refused, and no file is written."""
    folder = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
    recipe = folder / "declaration/spec.yml"
    before = file_bytes(folder)
    added = creation.new_stage(folder, "buyer")
    assert added.new_files == (("declaration/stages/buyer/buyer.bl", BUYER_STAGE),)
    page = set(PAGE_HEADER.findall(STAGE_PAGE.read_text(encoding="utf-8")))
    written = PAGE_HEADER.findall(BUYER_STAGE)
    assert [name for name, *_ in written] == [
        "arvl_to_dcsn",
        "dcsn_to_cntn",
        "cntn_to_dcsn",
        "dcsn_to_arvl",
    ]
    assert set(written) <= page
    stage_path = "declaration/stages/buyer/buyer.bl"
    elaborated = model.elaborate_buffer(BUYER_STAGE, stage_path)
    assert model.loop_state(elaborated) == "parsed, refused"
    assert list(elaborated.stage.fields()) == []
    spans = source_spans(BUYER_STAGE, stage_path)
    headers = model.header_pairs(spans, BUYER_STAGE)
    groups = model.classification(elaborated.stage, spans, headers=headers)
    change = {"kind": "add", "perch": "cntn", "branch": None, "field": "a", "set": "ℝ₊"}
    first = applied(BUYER_STAGE, model.classification_edits(groups, {**change, "role": "state"}))
    assert first == BUYER_STAGE.replace("() : !cntn]", "(a : ℝ₊) : !cntn]")
    edited = str(recipe.resolve())
    assert list(added.edits) == list(added.read) == [edited]
    assert added.read[edited] == recipe.read_text(encoding="utf-8")
    assert added.edits[edited] == added.read[edited] + f"  buyer: {creation.recipe_row('buyer')}\n"
    assert added.notes == ("spec.yml, stages: buyer written", "new: stages/buyer/buyer.bl")
    assert creation.checklist(folder, added.edits) == ()
    assert file_bytes(folder) == before
    held = {edited: added.edits[edited]}
    for key, texts, words in (
        ("cons", None, "declaration/stages/cons/ exists"),
        ("buyer", held, "the mapping stages holds the key 'buyer' already"),
        ("yes", None, "YAML reads the stage key 'yes'"),
        ("2buyer", None, "'2buyer' is no stage key"),
    ):
        with pytest.raises(ValueError, match=re.escape(words)):
            creation.new_stage(folder, key, texts=texts)
    with pytest.raises(ValueError, match="holds no declaration/spec.yml"):
        creation.new_stage(CORPUS / "buffer-stock", "buyer")
    assert file_bytes(folder) == before


def test_new_stage_adds_its_slots_to_answers_where_it_exists(repository):
    """K-D7: in a folder "new trellis" wrote, whose answers.yml lists the
    slots the form wrote, "new stage" adds the new stage's two slots, its
    calibration and its settings (decision S7-F3), to answers.yml's
    `required.slots` and no entry to its `stages`, which records the
    templates copied; the checklist lists none of the eight slots (K-D29).
    Once the
    files are written, the factory refuses the recipe, which names a stage
    that no period holds, in its own sentence, until a period's list names
    the key."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    added = creation.new_stage(created.folder, "buyer")
    paths = (created.folder / "declaration/spec.yml", created.folder / creation.ANSWERS)
    edited = [str(path.resolve()) for path in paths]
    assert list(added.edits) == list(added.read) == edited
    slots = "".join(f"    - {creation.slot_name('buyer', kind)}\n" for kind in creation.SLOT_KINDS)
    assert added.edits[edited[1]] == added.read[edited[1]].replace(
        "  connectors: []\n", f"{slots}  connectors: []\n"
    )
    assert creation.checklist(created.folder, added.edits) == ()
    save_added(created.folder, added)
    with pytest.raises(FactoryError, match="the recipe names the stage 'buyer', which no period"):
        load_recipe(created.folder / "declaration", "spec.yml")


def test_new_source_file_answers_the_empty_file_of_each_kind_at_its_place(tmp_path):
    """K-D7 (plan, Task 9): for the stage buyer, the file "new file" writes
    for each binding kind, answered and not written, at the folder's
    conventional place, declaration/calibration/buyer.yml,
    declaration/settings/buyer.yml, each the one top key of its kind with
    nothing under it, and the stage's addition
    declaration/stages/buyer/methods.bl, its first line alone, which names
    the stage it is unioned with. Written and bound after the portfolio
    stage's own files, the calibration and the settings add no value, and
    the addition is one the Workbench lists for a methods cell. A file that
    exists, a kind that is none of the three and a key that is no stage key
    are refused."""
    folder = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
    before = file_bytes(folder)
    answered = {kind: creation.new_source_file(folder, "buyer", kind) for kind in creation.KINDS}
    assert answered == BUYER_SOURCES
    assert file_bytes(folder) == before
    for path, text in answered.values():
        (folder / path).parent.mkdir(parents=True, exist_ok=True)
        (folder / path).write_text(text, encoding="utf-8")
    declaration = folder / "declaration"
    port = load_recipe(declaration, "spec.yml")["periods"][0]["stages"]["port"]
    recipe = declaration / "spec.yml"
    recipe.write_text(
        recipe.read_text(encoding="utf-8")
        .replace("[calibration/portfolio]", "[calibration/portfolio, calibration/buyer]")
        .replace("[settings/port]", "[settings/port, settings/buyer]"),
        encoding="utf-8",
    )
    bound = load_recipe(declaration, "spec.yml")["periods"][0]["stages"]["port"]
    assert (bound["calibration"], bound["settings"]) == (port["calibration"], port["settings"])
    assert model.is_addition_file(folder / BUYER_SOURCES["methods"][0])
    with pytest.raises(ValueError, match="declaration/stages/buyer/methods.bl exists"):
        creation.new_source_file(folder, "buyer", "methods")
    with pytest.raises(ValueError, match="'grid' is no binding kind"):
        creation.new_source_file(folder, "buyer", "grid")
    with pytest.raises(ValueError, match="'2buyer' is no stage key"):
        creation.new_source_file(folder, "2buyer", "settings")


def test_new_stage_from_the_folder_bar_writes_the_stage_and_opens_it(
    scratch_folder, tmp_path, app_state
):
    """K-D7 (plan, Task 9): the folder's bar holds `new stage`, after `new
    trellis` and the `+` of `new variant`, where the folder holds the
    recipe the forms edit, and not in a folder with no recipe. Its form,
    whose note says in one line what it writes and where, given the key
    buyer with no file open, writes the stage file to disk and the recipe's
    row with it, no buffer unsaved (unit L, Task 17; defect 22 of the UX
    simulation), closes, names both on the status line and opens the stage
    file in the editor (spec 0.4 §3.5, as "add stage" writes). Given the key
    buyer again, it is refused in the form, and nothing is written; given
    the key seller while the recipe holds unsaved text, which the save would
    write with the row, it is refused in the form naming the recipe, and
    nothing is written."""
    plain = tmp_path / "plain"
    plain.mkdir()
    app_state(plain)
    _, rendered = solara.render(app.FolderActions(), handle_error=False)
    try:
        assert not rendered.find(v.Html, class_="bl-new-stage").widgets
    finally:
        rendered.close()
    app_state(scratch_folder)
    app.source.value = None
    stage = "declaration/stages/buyer/buyer.bl"
    try:
        _, rendered = solara.render(app.FolderActions(), handle_error=False)
        try:
            labels = [
                button.attributes["label"]
                for button in rendered.find(v.Html, tag="vscode-toolbar-button").widgets
            ]
            assert labels == ["New trellis", "New variant", "New stage"]
            rendered.find(v.Html, class_="bl-new-stage").widget.fire_event("click", {})
        finally:
            rendered.close()
        assert app.form_open.value == "new stage"
        before = file_bytes(scratch_folder)
        _, rendered = solara.render(app.NewStageForm(), handle_error=False)
        try:
            note = rendered.find(v.Html, class_="bl-form-note").widget
            assert note.children == [
                "writes declaration/stages/<key>/<key>.bl and adds the stage to "
                "declaration/spec.yml"
            ]
            enter_text(rendered, "Stage key", "buyer")
            press_words(rendered, "Write the stage")
        finally:
            rendered.close()
        assert (app.form_error.value, app.form_open.value, app.gesturing.value) == ("", None, None)
        after = file_bytes(scratch_folder)
        row = f"  buyer: {creation.recipe_row('buyer')}\n"
        assert {path: after[path] for path in before if path != RECIPE_FILE} == {
            path: text for path, text in before.items() if path != RECIPE_FILE
        }
        assert after[RECIPE_FILE].decode("utf-8") == before[RECIPE_FILE].decode("utf-8") + row
        assert sorted(set(after) - set(before)) == [stage]
        assert after[stage].decode("utf-8") == BUYER_STAGE
        assert app.unsaved_texts() == {}
        assert app.buffers.value[RECIPE_FILE]["text"].endswith(row)
        assert app.gesture_note.value["sentence"] == (
            "spec.yml, stages: buyer written; new: stages/buyer/buyer.bl"
        )
        assert app.open_path.value == stage
        app.open_form("new stage")
        app.submit_new_stage("buyer")
        held = app.buffers.value[stage]
        editor = {"path": stage, "text": held["text"], "revision": held["document_revision"]}
        app.on_change(editor)
        assert (app.form_error.value, app.form_open.value) == (
            "declaration/stages/buyer/ exists",
            "new stage",
        )
        assert file_bytes(scratch_folder) == after
        # the recipe's buffer holding unsaved text, which the save would write
        held = app.buffers.value[RECIPE_FILE]
        app.buffers.value = {
            **app.buffers.value,
            RECIPE_FILE: {**held, "text": held["text"] + "# typed\n"},
        }
        app.submit_new_stage("seller")
        app.on_change(editor)
        assert (app.form_error.value, app.form_open.value) == (
            f"{RECIPE_FILE} holds unsaved text",
            "new stage",
        )
        assert file_bytes(scratch_folder) == after
    finally:
        clear_gesture_state()
        clear_trellis_state()
        app.sources.value, app.tree.value = [], []


def test_new_stage_refuses_a_changed_period_before_writing(tmp_path, app_state, monkeypatch):
    folder = creation.create_trellis(tmp_path, "inventory", [], "year", 2).folder
    app_state(folder)
    path = "declaration/period.yml"
    period = folder / path
    recipe = folder / RECIPE_FILE
    original = recipe.read_bytes()
    other = period.read_text(encoding="utf-8") + "# written by another program\n"
    app.open_file(path)
    editor = app.buffers.value[path]
    new_stage = creation.new_stage

    def changed_after(*args, **kwargs):
        added = new_stage(*args, **kwargs)
        period.write_text(other, encoding="utf-8")
        return added

    monkeypatch.setattr(creation, "new_stage", changed_after)
    try:
        app.open_form("new stage")
        app.submit_new_stage("inventory", "period.yml")
        answer = {"path": path, "revision": editor["document_revision"]}
        app.on_change({**answer, "text": editor["text"]})
        app.on_applied({**answer, "n": app.edit_request.value["n"], "applied": True})
        if app.gesturing.value is not None:
            app.on_applied({**answer, "n": app.edit_request.value["n"], "applied": True})
        assert app.form_open.value == "new stage"
        assert path in app.form_error.value
        assert recipe.read_bytes() == original
        assert period.read_text(encoding="utf-8") == other
        assert not (folder / "declaration/stages/inventory").exists()
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_l_17_new_stage_opens_the_unsaved_file_if_it_changes_during_the_write(
    scratch_folder, app_state, monkeypatch
):
    """Unit L, Task 17 (unit L's final judgment, §6 item 6): where the
    recipe changes on disk after `new stage` applied its row to the
    recipe's buffer and before the save, as a write by another program
    changes it, the recipe on disk keeps the other program's text. The
    editor opens the unsaved recipe and the status says the stage exists."""
    app_state(scratch_folder)
    app.source.value = None
    written = scratch_folder / RECIPE_FILE
    other = written.read_text(encoding="utf-8") + "# written by another program\n"
    apply_edits = app.apply_edits

    def changed_after(edits, read, new_files=()):
        failed = apply_edits(edits, read, new_files)
        written.write_text(other, encoding="utf-8")
        return failed

    monkeypatch.setattr(app, "apply_edits", changed_after)
    try:
        app.open_form("new stage")
        app.submit_new_stage("buyer")
        assert app.form_open.value is None
        assert app.gesturing.value is None
        assert app.open_path.value == RECIPE_FILE
        stage = "declaration/stages/buyer/buyer.bl"
        assert (scratch_folder / stage).is_file()
        assert stage in app.gesture_note.value["sentence"]
        assert f"{RECIPE_FILE}: the file changed on disk" in app.gesture_note.value["sentence"]
        assert written.read_text(encoding="utf-8") == other
        held = app.buffers.value[RECIPE_FILE]
        assert held["text"].endswith(f"  buyer: {creation.recipe_row('buyer')}\n")
        assert RECIPE_FILE in app._dirty_paths()
    finally:
        app.close_form()
        clear_gesture_state()
        clear_trellis_state()
        app.sources.value, app.tree.value = [], []


def test_new_file_in_a_slot_s_cell_writes_the_empty_file_and_fills_the_slot(
    scratch_lifecycle, app_state
):
    """K-D7 (plan, Task 9), on the Recipe tab of unit M's Task 10 (AAS,
    M-D17; design pass 9 §§3 and 4): in the lifecycle registry's recipe,
    the slot `$disc_settings` of the settings of `disc`, whose settings
    file the folder does not hold, has in disc's row opened by a click
    (design pass 11 §2) the icon button `New file` at the right of its
    select (unit N, Task 2; design pass 10 §4), its hover naming the file it
    writes. Where the recipe's text no longer writes the slot, it is refused
    in the writer's sentence, its button marked, and nothing is written.
    Otherwise it writes declaration/settings/disc.yml, the empty settings
    file of disc, writes its name in the slot's place in the recipe's
    buffer, one edit of it, the recipe on disk unchanged, and opens the new
    file in the editor. A slot whose file the folder holds, and an entry
    that is no slot, have no `New file`, disc's row and cons's opened in
    turn; a methods list names additions and no slot (decision S7-F3), so
    no row offers `New file` for the methods."""
    folder = model.open_folder(scratch_lifecycle)
    shown = Source("recipe", RECIPE_FILE)
    settings = "declaration/settings/disc.yml"
    address = "stages.disc.settings.all[0]"
    recipe = scratch_lifecycle / RECIPE_FILE
    original = recipe.read_text(encoding="utf-8")
    app_state(scratch_lifecycle)
    app.source.value = shown
    app.view_mode.value = "trellis"
    try:
        app.run_trellis()
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)
        try:
            assert rendered.find(v.Html, class_="bl-new-file").widgets == []
            open_rendered_recipe_row(rendered, "disc")
            (button,) = rendered.find(v.Html, class_="bl-new-file").widgets
            assert (
                button.tag,
                button.attributes["label"],
                button.attributes["title"],
                button.attributes["data-address"],
            ) == ("vscode-toolbar-button", "New file", f"Write {settings}", address)
            # the recipe's buffer no longer writes the slot
            on_disk = model.read_file(folder, RECIPE_FILE)
            changed = original.replace("[$disc_settings]", "[settings/disc]")
            app.buffers.value = {
                RECIPE_FILE: {
                    "text": changed,
                    "revision": 1,
                    "digest": on_disk.digest,
                    "document": changed,
                    "document_revision": 1,
                }
            }
            before = file_bytes(scratch_lifecycle)
            button.fire_event("click", {})
            refused = app.choice_refusal.value
            assert (refused["sentence"], refused["address"], refused["control"]) == (
                f"the file no longer writes $disc_settings at {address}",
                address,
                "new file",
            )
            marked = "bl-new-file bl-refusal-mark"
            assert rendered.find(v.Html, class_=marked).widget
            assert file_bytes(scratch_lifecycle) == before
            assert app.buffers.value[RECIPE_FILE]["text"] == changed
            app.buffers.value, app.choice_refusal.value = {}, None
            new_file = rendered.find(v.Html, class_="bl-new-file").widget
            new_file.fire_event("click", {})
        finally:
            rendered.close()
        assert app.choice_refusal.value is None
        assert (scratch_lifecycle / settings).read_text(encoding="utf-8") == "settings: {}\n"
        written = app.buffers.value[RECIPE_FILE]["text"]
        assert entry_value(written, address) == "settings/disc"
        assert written == original.replace("[$disc_settings]", "[settings/disc]")
        assert recipe.read_text(encoding="utf-8") == original
        assert app.open_path.value == settings
        # the slot's file now stands, and the entries of cons and port are
        # no slots
        app.open_path.value, app.buffers.value = None, {}
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)
        try:
            for key in ("disc", "cons", "port"):
                open_rendered_recipe_row(rendered, key)
                assert rendered.find(v.Html, class_="bl-new-file").widgets == [], key
        finally:
            rendered.close()
    finally:
        clear_gesture_state()
        clear_trellis_state()
        app.source.value, app.buffers.value, app.open_path.value = None, {}, None
        app.choice_refusal.value, app.view_mode.value = None, "stage"
        app.sources.value, app.tree.value, app.rebind.value = [], [], 0


# --- a period added between two periods (spec 0.4 §3.6; unit J, Task 12) ---


def test_a_period_between_two_periods_splits_the_repeated_entry(repository):
    """Spec 0.4 §3.6: between periods[3] and periods[2] of the six periods
    that one entry with `repeat: 6` writes, "add period" answers, writing
    nothing, the trellis file's text with that entry split around the new
    entry, `repeat: 3`, `{template: period.mid.yml, repeat: 1}`, `repeat:
    3`, and answers.yml's text with its entry split in the same way; the
    standing mapping is kept, since the new period's stages equal both
    neighbors'. Read from the texts, the trellis has seven periods, the
    new period being periods[3], and the status line names the split, the
    new file and the restriction. Where the entry takes its repeat from the
    period file it names, the repeat is first written into the entry, and
    the entry is then split in the same way (ruling J-P11). An answers.yml
    whose text reads as no mapping, an empty text, a comment alone or a
    list, refuses the insertion with a ValueError naming the file, as the
    earliest end's writer refuses it, so that the form shows the refusal."""
    work, _ = repository
    keys = ["port", "cons", "disc"]
    for name, repeat_in_file in (("lifecycle-demo", False), ("file-repeat", True)):
        created = creation.create_trellis(work, name, list(DEMO_STAGES), "demo_period", 6)
        declaration = created.folder / "declaration"
        trellis, answers = declaration / "trellis.yml", created.folder / creation.ANSWERS
        if repeat_in_file:
            trellis.write_text(
                trellis.read_text(encoding="utf-8").replace(
                    "{template: period.yml, repeat: 6}", "{template: period.yml}"
                ),
                encoding="utf-8",
            )
            period = declaration / "period.yml"
            period.write_text(period.read_text(encoding="utf-8") + "repeat: 6\n", encoding="utf-8")
            assert len(load_recipe(declaration, "spec.yml")["periods"]) == 6
        before = file_bytes(created.folder)
        added = creation.add_period(created.folder, "mid", keys, at=3)
        assert added.new_files == (
            ("declaration/period.mid.yml", creation.period_text("mid", keys)),
        )
        edited = [str(trellis.resolve()), str(answers.resolve())]
        assert list(added.edits) == list(added.read) == edited
        assert (
            "periods:\n"
            "  - {template: period.yml, repeat: 3}\n"
            "  - {template: period.mid.yml, repeat: 1}\n"
            "  - {template: period.yml, repeat: 3}\n"
        ) in added.edits[edited[0]]
        assert added.edits[edited[0]].endswith("inter_connectors:\n  - {}\n")
        assert (
            "periods:\n"
            "  - {label: demo_period, file: period.yml, repeat: 3}\n"
            "  - {label: mid, file: period.mid.yml, repeat: 1}\n"
            "  - {label: demo_period, file: period.yml, repeat: 3}\n"
        ) in added.edits[edited[1]]
        assert added.notes == (
            "trellis.yml, periods: repeat 6 split 3, period.mid.yml, 3",
            "new: period.mid.yml",
            "restriction periods 2–4",
        )
        assert file_bytes(created.folder) == before
        texts = {
            **added.edits,
            **{str((created.folder / path).resolve()): text for path, text in added.new_files},
        }
        read = load_recipe(declaration, "spec.yml", texts)
        assert (len(read["periods"]), len(read["inter_connectors"])) == (7, 6)
        assert period_entries(trellis, texts)[3] == (str(declaration / "period.mid.yml"), "", (3,))
    for unread in ("", "# a comment alone\n", "- a list\n"):
        with pytest.raises(ValueError, match=r"^answers\.yml: the file holds no mapping$"):
            creation.add_period(
                created.folder, "mid", keys, at=3, texts={str(answers.resolve()): unread}
            )


def test_the_new_pairs_copy_the_old_pairs_mapping_where_the_list_holds_one_per_pair(repository):
    """Spec 0.4 §3.6: where `inter_connectors` holds one mapping for each
    adjacent pair, an insertion between periods[3] and periods[2] replaces
    the mapping of that pair, inter_connectors[2], by the mappings of the two
    new pairs, the status line naming it replaced: a copy of the old pair's
    mapping for both where the new period's stages equal both neighbors',
    and an empty mapping for both otherwise (ruling J-P3). Every other pair
    keeps its mapping, the list holding one mapping for each of the six
    pairs of the seven periods, which the factory reads without a refusal
    of their number; the addresses of answers.yml's `required.connectors`
    that name a later pair of the trellis file are renumbered with it.
    Where the old pair's mapping is anchored and read again by the next
    pair's alias, the text written over no longer reads as intended, and
    the whole gesture is refused, naming the address, before any text is
    answered."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    declaration = created.folder / "declaration"
    trellis, answers = declaration / "trellis.yml", created.folder / creation.ANSWERS
    trellis.write_text(
        trellis.read_text(encoding="utf-8").replace(
            "inter_connectors:\n  - {}\n",
            "inter_connectors:\n  - {}\n  - {}\n  - {a: k}\n  - {}\n  - {}\n",
        ),
        encoding="utf-8",
    )
    answers.write_text(
        answers.read_text(encoding="utf-8").replace(
            "  connectors: []\n",
            "  connectors:\n"
            '    - {file: declaration/trellis.yml, address: "inter_connectors[2]"}\n'
            '    - {file: declaration/trellis.yml, address: "inter_connectors[3]"}\n',
        ),
        encoding="utf-8",
    )
    before = file_bytes(created.folder)
    for keys, mappings in (
        (["port", "cons", "disc"], [{}, {}, {"a": "k"}, {"a": "k"}, {}, {}]),
        (["cons", "disc"], [{}, {}, {}, {}, {}, {}]),
    ):
        added = creation.add_period(created.folder, "mid", keys, at=3)
        made = added.edits[str(trellis.resolve())]
        assert entry_value(made, "inter_connectors") == mappings
        assert added.notes == (
            "trellis.yml, periods: repeat 6 split 3, period.mid.yml, 3",
            "inter_connectors[2] replaced",
            "new: period.mid.yml",
            "restriction periods 2–4",
        )
        required = entry_value(added.edits[str(answers.resolve())], "required.connectors")
        assert [mark["address"] for mark in required] == [
            "inter_connectors[2]",
            "inter_connectors[4]",
        ]
        assert "expanded" not in entry_value(added.edits[str(answers.resolve())])
        texts = {
            **added.edits,
            **{str((created.folder / path).resolve()): text for path, text in added.new_files},
        }
        read = load_recipe(declaration, "spec.yml", texts)
        assert read["inter_connectors"] == mappings
        assert list(read["periods"][3]["stages"]) == keys
    assert file_bytes(created.folder) == before
    trellis.write_text(
        trellis.read_text(encoding="utf-8").replace(
            "  - {a: k}\n  - {}\n", "  - &old {a: k}\n  - *old\n"
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match=r"^declaration/trellis\.yml: the layout of the file at inter_connectors\[2\] "
        "cannot be written over as text",
    ):
        creation.add_period(created.folder, "mid", ["cons", "disc"], at=3)


def test_a_standing_mapping_is_expanded_where_the_new_periods_stages_differ(repository):
    """Spec 0.4 §3.6 and decision 39 (J-D23): where `inter_connectors` holds
    the one mapping that stands for every pair, an insertion whose stages
    equal both neighbors' keeps it; one whose stages differ expands the
    list to one mapping for each pair, each existing pair a copy of the
    standing mapping and each of the two new pairs an empty mapping, the
    status line naming the list expanded, and answers.yml records the
    expansion as `expanded: {inter_connectors: true}`. While the record
    stands, the checklist lists each mapping that differs from the most
    frequent one, the two new pairs and then a copy edited alone, with the
    sentence `the mapping <address> differs from the others`, answers.yml
    also requiring a connector of period.yml, which the checklist reads
    first; once the author removes the record, it lists none of them. The
    stages compared are those the recipe makes active at each period, as
    the factory checks the standing mapping: where period.yml lists `disc`
    and the recipe restricts it to period 0, as applications/benhabib-2019
    lists its bequest, a new period of `port` and `cons` keeps the standing
    mapping."""
    work, _ = repository
    restricted = creation.create_trellis(work, "restricted", list(DEMO_STAGES), "demo_period", 6)
    recipe = restricted.folder / "declaration/spec.yml"
    recipe.write_text(
        recipe.read_text(encoding="utf-8").replace(
            "disc/methods.bl]}}", "disc/methods.bl]}, periods: [0, 0]}"
        ),
        encoding="utf-8",
    )
    kept = creation.add_period(restricted.folder, "mid", ["port", "cons"], at=3)
    assert kept.notes == (
        "trellis.yml, periods: repeat 6 split 3, period.mid.yml, 3",
        "new: period.mid.yml",
        "restriction periods 2–4",
    )
    kept_trellis = str((restricted.folder / "declaration/trellis.yml").resolve())
    assert entry_value(kept.edits[kept_trellis], "inter_connectors") == [{}]
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    declaration = created.folder / "declaration"
    trellis, answers = declaration / "trellis.yml", created.folder / creation.ANSWERS
    trellis.write_text(
        trellis.read_text(encoding="utf-8").replace(
            "inter_connectors:\n  - {}\n", "inter_connectors:\n  - {a: k}\n"
        ),
        encoding="utf-8",
    )
    answers.write_text(
        answers.read_text(encoding="utf-8").replace(
            "  connectors: []\n",
            '  connectors:\n    - {file: declaration/period.yml, address: "connectors[0]"}\n',
        ),
        encoding="utf-8",
    )
    same = creation.add_period(created.folder, "mid", ["port", "cons", "disc"], at=3)
    assert entry_value(same.edits[str(trellis.resolve())], "inter_connectors") == [{"a": "k"}]
    assert "expanded" not in entry_value(same.edits[str(answers.resolve())])
    added = creation.add_period(created.folder, "young", ["cons", "disc"], at=3)
    made = added.edits[str(trellis.resolve())]
    assert made.endswith(
        "inter_connectors:\n  - {a: k}\n  - {a: k}\n  - {}\n  - {}\n  - {a: k}\n  - {a: k}\n"
    )
    assert added.notes == (
        "trellis.yml, periods: repeat 6 split 3, period.young.yml, 3",
        "inter_connectors: one mapping expanded to 6",
        "new: period.young.yml",
        "restriction periods 2–4",
    )
    recorded = added.edits[str(answers.resolve())]
    assert recorded.endswith("expanded: {inter_connectors: true}\n")
    texts = {
        **added.edits,
        **{str((created.folder / path).resolve()): text for path, text in added.new_files},
    }
    read = load_recipe(declaration, "spec.yml", texts)
    assert (len(read["periods"]), len(read["inter_connectors"])) == (7, 6)

    def differing(texts):
        return [
            (entry.file, entry.address, entry.line, entry.column, entry.sentence)
            for entry in creation.checklist(created.folder, texts)
            if entry.address.startswith("inter_connectors")
        ]

    assert differing(None) == []
    assert differing(added.edits) == [
        (
            "declaration/trellis.yml",
            f"inter_connectors[{h}]",
            line,
            5,
            f"the mapping inter_connectors[{h}] differs from the others",
        )
        for h, line in ((2, 14), (3, 15))
    ]
    edited = made.replace(
        "  - {}\n  - {a: k}\n  - {a: k}\n", "  - {}\n  - {a: k, b: m}\n  - {a: k}\n"
    )
    assert [
        address for _, address, *_ in differing({**added.edits, str(trellis.resolve()): edited})
    ] == [
        "inter_connectors[2]",
        "inter_connectors[3]",
        "inter_connectors[4]",
    ]
    removed = recorded.replace("expanded: {inter_connectors: true}\n", "")
    assert differing({**added.edits, str(answers.resolve()): removed}) == []


def test_ranges_and_range_keys_at_or_above_the_new_index_rise_by_one(repository):
    """Spec 0.4 §3.6: an insertion as periods[3] raises by one, in the
    recipe's text, every bound of a `periods: [lo, hi]` range and every
    range key of a binding list (`"3-5"`, as `load_recipe` reads one) that
    lies at or above 3, a key through the writer of ruling J-P3, so that
    each binding keeps the periods it bound: the stage restricted to periods
    1 to 3 is active at periods 1 to 4, the old periods 1 to 3 and the new
    one, and the calibration slot bound at periods 3 to 5 is bound at the
    old periods 3 to 5, now 4 to 6, and not at the new period. A bound or
    a key below 3 is kept. The status line names each range and key
    changed, the recipe's file once, and so does the checklist: answers.yml
    records each under its new address in `moved`, and while the record
    stands the checklist lists each at its place in the recipe. A second
    insertion renumbers the record of a key it raises again and adds no
    record twice; once the author removes the record, the checklist lists
    none of them."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    declaration = created.folder / "declaration"
    recipe = declaration / "spec.yml"
    recipe.write_text(
        recipe.read_text(encoding="utf-8")
        .replace(
            "{all: [$cons_calibration]}",
            '{all: [$cons_calibration], "0-2": [$cons_late], "3-5": [$cons_early]}',
        )
        .replace("port/methods.bl]}}", "port/methods.bl]}, periods: [2, 5]}")
        .replace("disc/methods.bl]}}", "disc/methods.bl]}, periods: [1, 3]}"),
        encoding="utf-8",
    )

    def bound(read):
        """For each period, whether each stage is active there, and the
        range keys under which the calibration of `cons` is bound."""
        return [
            (
                tuple(period["stages"]),
                tuple(
                    entry.get("range")
                    for entry in period["stages"]["cons"]["provenance"]["source_lists"][
                        "calibration"
                    ]
                ),
            )
            for period in read["periods"]
        ]

    old = bound(load_recipe(declaration, "spec.yml"))
    added = creation.add_period(created.folder, "mid", ["port", "cons", "disc"], at=3)
    made = added.edits[str(recipe.resolve())]
    assert entry_value(made, "stages.port.periods") == [2, 6]
    assert entry_value(made, "stages.disc.periods") == [1, 4]
    assert list(entry_value(made, "stages.cons.calibration")) == ["all", "0-2", "4-6"]
    assert '"0-2": [$cons_late], "4-6": [$cons_early]' in made
    assert added.notes == (
        "trellis.yml, periods: repeat 6 split 3, period.mid.yml, 3",
        "spec.yml, stages.port.periods: [2, 5] now [2, 6]",
        "stages.cons.calibration: 3-5 now 4-6",
        "stages.disc.periods: [1, 3] now [1, 4]",
        "new: period.mid.yml",
        "restriction periods 2–4",
    )
    texts = {
        **added.edits,
        **{str((created.folder / path).resolve()): text for path, text in added.new_files},
    }
    new = bound(load_recipe(declaration, "spec.yml", texts))
    assert new[:3] == old[:3] and new[4:] == [
        (stages, tuple("4-6" if key == "3-5" else key for key in keys)) for stages, keys in old[3:]
    ]
    assert new[3] == (("port", "cons", "disc"), (None,))
    answers = str((created.folder / creation.ANSWERS).resolve())
    recorded = added.edits[answers]
    addresses = ["stages.port.periods", "stages.cons.calibration.4-6", "stages.disc.periods"]
    assert entry_value(recorded, "moved") == [
        {"file": "declaration/spec.yml", "address": address} for address in addresses
    ]
    sentence = (
        "the range {} was changed by an added period: check any schedule keyed by period index"
    )
    assert [
        (entry.file, entry.address, entry.line, entry.column, entry.sentence)
        for entry in creation.checklist(created.folder, added.edits)
        if entry.sentence.startswith("the range")
    ] == [
        ("declaration/spec.yml", address, *entry_span(made, address)[:2], sentence.format(address))
        for address in addresses
    ]
    removed = {**added.edits, answers: recorded[: recorded.index("moved:")]}
    assert not any(
        entry.sentence.startswith("the range")
        for entry in creation.checklist(created.folder, removed)
    )
    save_added(created.folder, added)
    again = creation.add_period(created.folder, "late", ["port", "cons", "disc"], at=3)
    assert again.notes[1:4] == (
        "spec.yml, stages.port.periods: [2, 6] now [2, 7]",
        "stages.cons.calibration: 4-6 now 5-7",
        "stages.disc.periods: [1, 4] now [1, 5]",
    )
    assert entry_value(again.edits[answers], "moved") == [
        {"file": "declaration/spec.yml", "address": address.replace("4-6", "5-7")}
        for address in addresses
    ]


# The comment that stands over the retirement years' entry of the pension
# model's trellis file at its first build of the working years, and the
# entry of a period `extra_year` (unit L, Task 19)
RETIREMENT_COMMENT = (
    "  # retirement years: the survive branch goes straight to the tenure choice\n"
)
EXTRA_YEAR = "  - {template: period.extra_year.yml, repeat: 1}\n"
# a retirement year's stages, which carry every field of the one mapping
RETIREMENT_YEAR = [
    "shocks",
    "survival",
    "tenure_pa",
    "renter_cons",
    "keeper_cons_pa",
    "adjuster_cons_pa",
]


def test_a_standing_mapping_is_kept_where_the_package_admits_it_and_comments_stay(tmp_path):
    """Unit L, Task 19 (defect 11 of the UX simulation; spec 0.4 §3.6). On
    the pension model at its first build of the working years, whose
    trellis file writes one inter-period mapping and a comment over each
    entry: `add period` between periods[1] and periods[0] with `standing`
    answering that the package admits the mapping at both new pairs keeps
    the one mapping as it is written, though the new period's stages differ
    from the terminal period's, the status line naming no expansion; the
    new entry stands above the comment over the retirement years' entry,
    which stays over that entry, and every other line of the file is kept.
    With `standing` answering that it does not, or none given, the list is
    expanded as before, the comment again over its entry. Between
    periods[2] and periods[1], which one entry writes with `repeat: 2`, the
    entry is split around the new one and the comment stays over the first
    part."""
    copy = pensions_copy(tmp_path / "durables", PENSIONS_WORKING_YEARS)
    trellis_file = copy / "declaration/trellis.pensions.yml"
    path, text = str(trellis_file.resolve()), trellis_file.read_text(encoding="utf-8")
    assert text.count(RETIREMENT_COMMENT) == 1
    asked = []

    def admits(at, keys):
        asked.append((at, list(keys)))
        return True

    kept = creation.add_period(
        copy, "extra_year", RETIREMENT_YEAR, at=1, recipe="spec.pensions.yml", standing=admits
    )
    assert asked == [(1, RETIREMENT_YEAR)]
    assert kept.edits[path] == text.replace(RETIREMENT_COMMENT, EXTRA_YEAR + RETIREMENT_COMMENT)
    assert not any("inter_connectors" in note for note in kept.notes), kept.notes
    for refused in ({"standing": lambda at, keys: False}, {}):
        expanded = creation.add_period(
            copy, "extra_year", RETIREMENT_YEAR, at=1, recipe="spec.pensions.yml", **refused
        )
        made = expanded.edits[path]
        assert len(entry_value(made, "inter_connectors")) == 7
        assert "inter_connectors: one mapping expanded to 7" in expanded.notes
        assert EXTRA_YEAR + RETIREMENT_COMMENT in made
    split = creation.add_period(
        copy, "extra_year", RETIREMENT_YEAR, at=2, recipe="spec.pensions.yml", standing=admits
    )
    first = split.edits[path].split("\n").index(RETIREMENT_COMMENT.rstrip("\n"))
    lines = split.edits[path].split("\n")[first : first + 4]
    assert [line.split(",")[0] for line in lines] == [
        RETIREMENT_COMMENT.rstrip("\n"),
        "  - {template: period.pensions.yml",
        "  - {template: period.extra_year.yml",
        "  - {template: period.pensions.yml",
    ]
    assert entry_value(split.edits[path], "inter_connectors") == entry_value(
        text, "inter_connectors"
    )


def test_a_range_that_excludes_the_target_period_is_widened(repository):
    """Spec 0.4 §§3.5 and 3.6 (ruling J-P8): where the recipe restricts a
    stage chosen for the new period to a range that excludes the new index,
    the range is widened to include it, after the renumbering: `disc`,
    restricted to periods 0 to 2, is widened to 0 to 4 for a period inserted
    as periods[4], and `port`, restricted to period 5, raised to 6 and then
    widened to 4 to 6, the status line naming each range written once, from
    the range read to the range written. At the earliest end, the seventh
    period, `disc` is widened to 0 to 6. A stage the recipe does not restrict,
    and a range that holds the period, are kept (`range_widened`)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    declaration = created.folder / "declaration"
    recipe = declaration / "spec.yml"
    recipe.write_text(
        recipe.read_text(encoding="utf-8")
        .replace("port/methods.bl]}}", "port/methods.bl]}, periods: [5, 5]}")
        .replace("disc/methods.bl]}}", "disc/methods.bl]}, periods: [0, 2]}"),
        encoding="utf-8",
    )
    text = recipe.read_text(encoding="utf-8")
    assert creation.range_widened(text, "cons", 3) == (text, None)
    assert creation.range_widened(text, "disc", 1) == (text, None)
    assert creation.range_widened(text, "disc", 4)[1] == "stages.disc.periods: [0, 2] now [0, 4]"
    between = creation.add_period(created.folder, "mid", ["port", "disc"], at=4)
    made = between.edits[str(recipe.resolve())]
    assert entry_value(made, "stages.port.periods") == [4, 6]
    assert entry_value(made, "stages.disc.periods") == [0, 4]
    assert between.notes == (
        "trellis.yml, periods: repeat 6 split 4, period.mid.yml, 2",
        "inter_connectors: one mapping expanded to 6",
        "spec.yml, stages.port.periods: [5, 5] now [4, 6]",
        "stages.disc.periods: [0, 2] now [0, 4]",
        "new: period.mid.yml",
        "restriction periods 3–5",
    )
    texts = {
        **between.edits,
        **{str((created.folder / path).resolve()): text for path, text in between.new_files},
    }
    assert list(load_recipe(declaration, "spec.yml", texts)["periods"][4]["stages"]) == [
        "port",
        "disc",
    ]
    earliest = creation.add_period(created.folder, "young", ["disc"])
    assert entry_value(earliest.edits[str(recipe.resolve())], "stages.disc.periods") == [0, 6]
    assert earliest.notes == (
        "trellis.yml, periods: {template: period.young.yml, repeat: 1} written, periods 6",
        "spec.yml, stages.disc.periods: [0, 2] now [0, 6]",
        "new: period.young.yml",
    )
    texts = {
        **earliest.edits,
        **{str((created.folder / path).resolve()): text for path, text in earliest.new_files},
    }
    assert list(load_recipe(declaration, "spec.yml", texts)["periods"][6]["stages"]) == ["disc"]


def test_the_restriction_after_an_insertion_names_the_new_period_and_its_neighbors(repository):
    """Spec 0.4 §3.6 and ruling J-P21: after an insertion the indices a
    restriction names have moved, so "add period" answers the text for the
    restriction's input, the new period and the periods beside it in the
    new numbering where the trellis then holds more than six periods, as
    the trellis load opens a long trellis on part of it, `periods 2–4` for a
    period inserted as periods[3] and `periods 4–6` as periods[5], which the
    Workbench's parser reads as those periods; the empty text otherwise, the
    status line ending `restriction emptied`. A period added at the earliest
    end moves no index and answers no restriction."""
    work, _ = repository
    long = creation.create_trellis(work, "long-demo", list(DEMO_STAGES), "demo_period", 6)
    for at, written, periods in ((3, "periods 2–4", (2, 3, 4)), (5, "periods 4–6", (4, 5, 6))):
        added = creation.add_period(long.folder, "mid", ["port", "cons", "disc"], at=at)
        assert (added.restriction, added.notes[-1]) == (written, f"restriction {written}")
        assert parse_restriction(added.restriction).periods == periods
    short = creation.create_trellis(work, "short-demo", list(DEMO_STAGES), "demo_period", 3)
    for at in (1, 2):
        added = creation.add_period(short.folder, "mid", ["port", "cons", "disc"], at=at)
        assert (added.restriction, added.notes[-1]) == ("", "restriction emptied")
    earliest = creation.add_period(long.folder, "young", ["port", "cons", "disc"])
    assert earliest.restriction is None
    assert not any(note.startswith("restriction") for note in earliest.notes)
    for at in (0, 6, True):
        with pytest.raises(ValueError, match="between two of them or at the earliest end"):
            creation.add_period(long.folder, "mid", ["cons"], at=at)


def test_a_variant_changes_its_own_three_files_and_nothing_of_the_first_recipe(repository):
    """Spec 0.4 §3.5 and §3.6: "add period" between two periods of a
    variant's trellis, `recipe="spec.v.yml"`, edits the variant's trellis
    file, whose entry is split and whose standing mapping is expanded for a
    period of other stages, and the variant's recipe, whose range is
    raised, and answers the new period file: the variant's three files.
    Nothing of the first recipe is edited: spec.yml, trellis.yml and
    period.yml stay as they were, and so does answers.yml, whose periods
    record the first trellis file and whose record of an expansion the
    checklist reads against that file. Once written, the variant reads
    seven periods and the first recipe six."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    declaration = created.folder / "declaration"
    recipe = declaration / "spec.yml"
    recipe.write_text(
        recipe.read_text(encoding="utf-8").replace(
            "disc/methods.bl]}}", "disc/methods.bl]}, periods: [0, 3]}"
        ),
        encoding="utf-8",
    )
    creation.create_variant(created.folder, "v", "spec.yml")
    before = file_bytes(created.folder)
    added = creation.add_period(created.folder, "mid", ["cons", "disc"], at=3, recipe="spec.v.yml")
    assert added.new_files == (
        ("declaration/period.mid.yml", creation.period_text("mid", ["cons", "disc"])),
    )
    assert list(added.edits) == [
        str((declaration / name).resolve()) for name in ("trellis.v.yml", "spec.v.yml")
    ]
    assert added.notes == (
        "trellis.v.yml, periods: repeat 6 split 3, period.mid.yml, 3",
        "inter_connectors: one mapping expanded to 6",
        "spec.v.yml, stages.disc.periods: [0, 3] now [0, 4]",
        "new: period.mid.yml",
        "restriction periods 2–4",
    )
    assert file_bytes(created.folder) == before
    first = {
        path: before[path]
        for path in (
            "declaration/spec.yml",
            "declaration/trellis.yml",
            "declaration/period.yml",
            "answers.yml",
        )
    }
    save_added(created.folder, added)
    assert {path: (created.folder / path).read_bytes() for path in first} == first
    assert len(load_recipe(declaration, "spec.v.yml")["periods"]) == 7
    assert len(load_recipe(declaration, "spec.yml")["periods"]) == 6


# --- a trellis written as records (spec 0.4 §3.5; unit J, Task 13) ---


def test_a_folder_stage_is_copied_as_its_record_into_the_target_period(tmp_path):
    """Spec 0.4 §3.5: on a copy of applications/cons-port, whose
    trellis.port-cons-vfi.yml writes its stages as records with no recipe, the
    entry with `repeat: 6` is first split by text into an entry of one
    period, periods[0], that writes no `disc`, and one of five periods that
    writes it. `record_stages` answers the keys any period writes as
    records. `disc` dropped on periods[0] is answered, writing nothing, as
    the trellis file's text with the record that periods[1] writes copied
    as the file writes it, its two lines kept, to the end of periods[0]'s
    `stages` mapping (`append_to_mapping`), and with the status line's part
    that names the file, the address, the key and the period reached; the
    trellis read from that text holds `disc` in periods[0] with the record
    of periods[1]. A key that no period writes as a record, and a period
    the file does not write, are refused with a ValueError."""
    folder = applications_copy(tmp_path)
    trellis = folder / PORT_CONS_RECORDS
    path = str(trellis.resolve())
    text = trellis.read_text(encoding="utf-8")
    # the two lines of the record of `disc`, the last record of the entry
    disc = text[text.index("      disc: {") : text.index("    connectors:")]
    whole = split_entry(text, "periods[0]", 1)
    trellis.write_text(whole.replace(disc, "", 1), encoding="utf-8")
    split = trellis.read_text(encoding="utf-8")
    listed = [list(period["stages"]) for period in load_trellis(trellis)["periods"]]
    assert listed == [["port", "cons"]] + [["port", "cons", "disc"]] * 5
    assert creation.record_stages(trellis) == ("port", "cons", "disc")
    before = file_bytes(folder)
    added = creation.add_record_stage(trellis, "disc", 0)
    assert added.new_files == () and list(added.edits) == list(added.read) == [path]
    assert added.read[path] == split and added.edits[path] == whole
    assert added.notes == ("trellis.port-cons-vfi.yml, periods[0].stages: disc written, periods 0",)
    assert added.restriction is None and file_bytes(folder) == before
    read = load_trellis(trellis, texts=added.edits)
    assert [list(period["stages"]) for period in read["periods"]] == [["port", "cons", "disc"]] * 6
    assert read["periods"][0]["stages"]["disc"] == read["periods"][1]["stages"]["disc"]
    refused = (
        ("bequest", 0, "no period of trellis.port-cons-vfi.yml writes a record for 'bequest'"),
        ("disc", 6, "trellis.port-cons-vfi.yml writes no period 6"),
    )
    for key, h, words in refused:
        with pytest.raises(ValueError, match=f"^{re.escape(words)}$"):
            creation.add_record_stage(trellis, key, h)


def test_a_stage_the_period_holds_writes_nothing(tmp_path):
    """Spec 0.4 §3.5, "writes nothing where the list already holds it":
    each of the three stages of trellis.port-cons-vfi.yml dropped on each of
    its six periods, whose one entry writes all three for every period,
    answers an `Added` with no new file, no edit and no note. Where the
    file on disk writes `disc` in no period, and an unsaved buffer, read in
    the file's place, holds the corpus's text, the drop of `disc` on
    periods[0] writes nothing as well."""
    folder = applications_copy(tmp_path)
    trellis = folder / PORT_CONS_RECORDS
    nothing = creation.Added((), {}, {}, ())
    for key in ("port", "cons", "disc"):
        assert all(creation.add_record_stage(trellis, key, h) == nothing for h in range(6))
    text = trellis.read_text(encoding="utf-8")
    disc = text[text.index("      disc: {") : text.index("    connectors:")]
    trellis.write_text(text.replace(disc, "", 1), encoding="utf-8")
    assert creation.record_stages(trellis) == ("port", "cons")
    unsaved = {str(trellis.resolve()): text}
    assert creation.record_stages(trellis, unsaved) == ("port", "cons", "disc")
    assert creation.add_record_stage(trellis, "disc", 0, texts=unsaved) == nothing


def test_a_period_is_inserted_as_an_inline_entry_with_one_empty_connector(tmp_path):
    """Spec 0.4 §§3.5, 3.6: on trellis.port-cons-vfi.yml, "+ period" answers,
    writing nothing, the trellis file's text with an inline entry whose
    `stages` are the text of the neighbor's, every line kept, and whose
    `connectors` is one empty mapping, `connectors: [{}]`. At the earliest
    end the entry follows the last entry and copies the stages of the
    earliest period, periods[5]; the one standing mapping stands for the new
    pair as well. Between periods[3] and periods[2], which the entry with
    `repeat: 6` writes, that entry is split around the new entry, `repeat:
    3` on both sides, which copies the stages of the neighbor on its
    terminal side, periods[2]; the standing mapping is kept, the stages
    being equal, and the restriction's input names the new period and its
    neighbors. Where the neighbors' stages differ, as between periods[1] and
    periods[0] of a file whose periods[0] writes no `disc`, no entry is
    split and the standing mapping is expanded to one mapping for each pair
    (spec 0.4 §3.6). Read from each text, the trellis holds the new period;
    an `at` that is no place between two periods is refused."""
    folder = applications_copy(tmp_path)
    trellis = folder / PORT_CONS_RECORDS
    path = str(trellis.resolve())
    text = trellis.read_text(encoding="utf-8")
    before = file_bytes(folder)
    # the lines of the one entry, from its dash to its repeat, and the lines
    # of its three records
    entry = text[text.index("  - stages:\n") : text.index("inter_connectors:")]
    records = entry[len("  - stages:\n") : entry.index("    connectors:")]
    inline = "  - stages:\n" + records + "    connectors: [{}]\n"
    added = creation.add_record_period(trellis)
    assert added.new_files == () and list(added.edits) == list(added.read) == [path]
    assert added.edits[path] == text.replace(entry, entry + inline, 1)
    assert added.notes == (
        "trellis.port-cons-vfi.yml, periods: an entry with the stages of periods[5] written, "
        "periods 6",
    )
    assert added.restriction is None
    read = load_trellis(trellis, texts=added.edits)
    assert (len(read["periods"]), len(read["inter_connectors"])) == (7, 6)
    assert read["periods"][6] == {**read["periods"][5], "connectors": [{}]}
    added = creation.add_record_period(trellis, at=3)
    halves = entry.replace("repeat: 6", "repeat: 3")
    assert added.edits[path] == text.replace(entry, halves + inline + halves, 1)
    assert added.notes == (
        "trellis.port-cons-vfi.yml, periods: repeat 6 split 3, an entry with the stages of "
        "periods[2], 3",
        "restriction periods 2–4",
    )
    assert added.restriction == "periods 2–4"
    read = load_trellis(trellis, texts=added.edits)
    assert len(read["periods"]) == 7 and read["inter_connectors"] == [{"disc.a": "k"}] * 6
    assert read["periods"][3] == {**read["periods"][2], "connectors": [{}]}
    assert period_entries(trellis, added.edits)[3] == (str(trellis), "periods[1]", (3,))
    assert file_bytes(folder) == before
    disc = text[text.index("      disc: {") : text.index("    connectors:")]
    split = split_entry(text, "periods[0]", 1).replace(disc, "", 1)
    added = creation.add_record_period(trellis, at=1, texts={path: split})
    assert added.read[path] == split
    assert entry_value(added.edits[path], "periods[1]") == {
        "stages": entry_value(split, "periods[0].stages"),
        "connectors": [{}],
    }
    assert entry_value(added.edits[path], "inter_connectors") == [{}, {}] + [{"disc.a": "k"}] * 4
    assert added.notes == (
        "trellis.port-cons-vfi.yml, periods: an entry with the stages of periods[0] written, "
        "periods 1",
        "inter_connectors: one mapping expanded to 6",
        "restriction periods 0–2",
    )
    listed = [list(period["stages"]) for period in load_trellis(trellis, added.edits)["periods"]]
    assert listed == [["port", "cons"]] * 2 + [["port", "cons", "disc"]] * 5
    with pytest.raises(ValueError, match=r"^no period is added at 6: trellis\.port-cons-vfi\.yml "):
        creation.add_record_period(trellis, at=6)


# --- the drops of the trellis graph (spec 0.4 §§3.5, 3.6; unit J) ---

# the recipe of a folder in the one layout, as the source of its trellis
RECIPE_SOURCE = Source("recipe", RECIPE_FILE)
# lesson 05's trellis file, written as records, as the source of its trellis
# the trellis of records a folder of records (`records_without`) opens on
RECORDS_SOURCE = Source("trellis", PORT_CONS_RECORDS)
# the files "add stage" writes for the template `noport` in a folder that
# holds the calibration it brings, by their paths from the model folder
NOPORT_FILES = (
    "declaration/stages/noport/noport.bl",
    "declaration/settings/noport.yml",
    "declaration/stages/noport/methods.bl",
)
# the status line's part that names those files (brief §5)
NOPORT_NEW = "new: stages/noport/noport.bl, settings/noport.yml, stages/noport/methods.bl"
# the recipe's row of the no-portfolio stage, which names the addition its
# template brings (decision S7-W17)
NOPORT_ROW = f"  noport: {creation.recipe_row('noport', ('stages/noport/methods.bl',))}\n"
# the item that ends the stage list of a recipe's trellis, which opens the
# form "add stage" on a folder of the disk (unit K, Task 25; K-D26), its
# words in sentence case since design pass 13 §3
FOLDER_ITEM = {
    "id": "folder",
    "kind": "folder",
    "key": "From a folder…",
    "title": "",
    "model_folder": "",
    "calibration": [],
    "periods_listed": [],
    "section": None,
}


def test_item_5_cases_a_template_dropped_on_a_period(repository, own_cache_folder):
    """Item 5 (spec 0.4 §3.5; brief rule 1, its fifth row, and §5): on a
    folder `new trellis` wrote, whose six periods `period.yml` writes, the
    template `noport` dropped on periods[2] answers, writing nothing, the
    edits "add stage" makes with the template's own key: the template's
    stage file and companions as new files in the stage's folder; the recipe
    with the stage's row, `period.yml` with the key and answers.yml with the
    slots, each by its resolved path with the text it was made from. The
    gesture names `period.yml` and its `stages`, and the status line names
    the key, every period the list writes and the new files. No slot of
    the edited texts is a checklist entry (K-D29). The stage list,
    under no heading, offers the recipe's three keys, each with the folder's
    title and name, the calibration its stage file declares and every
    period, since each period lists each, in the section `This folder's
    stages` (AAS, L-D9), then every template in the section `Templates`
    (AAS, L-D6), each with the name of the model folder its stage file
    stands in; and it names the periods the one list of stages writes
    together; last, the item `From a folder…` (unit K, Task 25), in no
    section. The sections' words and the item's are in sentence case
    (design pass 13 §3)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    folder = model.open_folder(created.folder)
    shown = show_trellis(folder, RECIPE_SOURCE).shown
    before = file_bytes(created.folder)
    event = dropped_event(shown, folder, NOPORT_ID, "template", "periods[2]___group___")
    gesture = drop_edits(shown, event, {})
    recipe, period, answers = (
        str((created.folder / name).resolve())
        for name in (RECIPE_FILE, "declaration/period.yml", creation.ANSWERS)
    )
    assert [path for path, _ in gesture.new_files] == list(NOPORT_FILES)
    assert list(gesture.edits) == list(gesture.read) == [recipe, period, answers]
    assert gesture.read == {path: Path(path).read_text(encoding="utf-8") for path in gesture.read}
    row = NOPORT_ROW
    assert gesture.edits[recipe] == gesture.read[recipe] + row
    assert gesture.edits[period] == gesture.read[period].replace(
        "  - disc\n", "  - disc\n  - noport\n"
    )
    assert (gesture.note, gesture.sentence, gesture.file, gesture.address) == (
        f"period.yml, stages: noport written, periods 0–5; {NOPORT_NEW}",
        None,
        period,
        "stages",
    )
    assert file_bytes(created.folder) == before
    assert creation.checklist(created.folder, gesture.edits) == ()
    listed = stage_items(folder, shown, {})
    assert listed["heading"] is None and listed["entries"] == [[0, 1, 2, 3, 4, 5]]
    assert listed["items"][:3] == [
        {
            "id": key,
            "kind": "stage",
            "key": key,
            "title": "lifecycle-demo",
            "model_folder": "lifecycle-demo",
            "calibration": list(creation.template_of(template_id).calibration),
            "periods_listed": [0, 1, 2, 3, 4, 5],
            "section": "This folder's stages",
        }
        for key, template_id in DEMO_STAGES
    ]
    assert listed["items"][3:-1] == [
        {
            "id": template.id,
            "kind": "template",
            "key": template.key,
            "title": template.model,
            # the cons-port application binds the portfolio model's stage
            # files, and the demonstration's consumption stage file since
            # decision SD-39
            "model_folder": (
                "cons-port" if template.id.startswith("cons-port/") else "pension-retirement"
            ),
            "calibration": list(template.calibration),
            "periods_listed": [],
            "section": "Templates",
        }
        for template in creation.stage_templates()
    ]
    assert listed["items"][-1] == FOLDER_ITEM


def test_item_5_cases_a_folder_stage_dropped_on_a_period_that_lists_it_and_one_that_does_not(
    repository, own_cache_folder
):
    """Item 5 (spec 0.4 §3.5; brief rule 1, its fourth row, and §5; ruling
    J-P8): on a folder `new trellis` wrote, given a seventh period,
    `period.young.yml`, that lists `cons` and `disc`, and a recipe that
    restricts `port` to periods 0 to 5. `cons` dropped on periods[2], whose
    list holds it, answers a gesture with no edit and no sentence. `port`
    dropped on periods[6] answers, writing nothing, its key appended to the
    `stages` list of `period.young.yml` and, since the recipe's range
    excludes period 6, that range widened to include it, the status line
    naming the list, the key and the period it reaches, then the range
    written; the trellis read from the edited texts holds `port` in
    periods[6]. The stage list names, for each key, the periods whose list
    holds it, and the two lists of stages."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    declaration = created.folder / "declaration"
    spec = declaration / "spec.yml"
    spec.write_text(
        spec.read_text(encoding="utf-8").replace(
            "port/methods.bl]}}", "port/methods.bl]}, periods: [0, 5]}"
        ),
        encoding="utf-8",
    )
    save_added(created.folder, creation.add_period(created.folder, "young", ["cons", "disc"]))
    folder = model.open_folder(created.folder)
    shown = show_trellis(folder, RECIPE_SOURCE).shown
    period, young, recipe = (
        str((declaration / name).resolve())
        for name in ("period.yml", "period.young.yml", "spec.yml")
    )
    before = file_bytes(created.folder)
    event = dropped_event(shown, folder, "cons", "stage", "periods[2]___group___")
    assert drop_edits(shown, event, {}) == Gesture(None, None, (), None, None, period, "stages")
    event = dropped_event(shown, folder, "port", "stage", "periods[6]___group___")
    gesture = drop_edits(shown, event, {})
    young_text, recipe_text = (Path(path).read_text(encoding="utf-8") for path in (young, recipe))
    assert gesture == Gesture(
        {
            young: young_text.replace("  - disc\n", "  - disc\n  - port\n"),
            recipe: recipe_text.replace("periods: [0, 5]", "periods: [0, 6]"),
        },
        {young: young_text, recipe: recipe_text},
        (),
        "period.young.yml, stages: port written, periods 6; "
        "spec.yml, stages.port.periods: [0, 5] now [0, 6]; port unconnected",
        None,
        young,
        "stages",
    )
    assert file_bytes(created.folder) == before
    read = load_recipe(declaration, "spec.yml", gesture.edits)
    assert list(read["periods"][6]["stages"]) == ["cons", "disc", "port"]
    listed = stage_items(folder, shown, {})
    assert {item["key"]: item["periods_listed"] for item in listed["items"][:3]} == {
        "port": [0, 1, 2, 3, 4, 5],
        "cons": [0, 1, 2, 3, 4, 5, 6],
        "disc": [0, 1, 2, 3, 4, 5, 6],
    }
    assert listed["entries"] == [[0, 1, 2, 3, 4, 5], [6]]


def test_item_5_cases_a_template_whose_key_the_recipe_holds_opens_the_form(
    repository, own_cache_folder
):
    """Spec 0.4 §3.5: where the recipe holds the template's key, as it
    holds `cons`, or the stage folder `stages/<key>/` exists, as it then
    does for `noport`, a template dropped on a period writes nothing and
    answers the form "add stage" filled with the template and the place of
    the period's list, the period file `period.yml` and its entry, the key
    alone left to type."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    folder = model.open_folder(created.folder)
    shown = show_trellis(folder, RECIPE_SOURCE).shown
    (created.folder / "declaration/stages/noport").mkdir()
    before = file_bytes(created.folder)
    for template_id, target in (
        (CONS_ID, "periods[2]___group___"),
        (NOPORT_ID, "periods[0]___group___"),
    ):
        event = dropped_event(shown, folder, template_id, "template", target)
        assert drop_edits(shown, event, {}) == {
            "form": "add stage",
            "fill": {"template": template_id, "period": "period.yml", "entry": ""},
        }
    assert file_bytes(created.folder) == before


def test_k_the_item_from_a_folder_opens_the_form_on_the_folder_above_the_model(
    repository, own_cache_folder
):
    """Unit K, Task 25 (K-D26): the item `From a folder…` dropped on
    periods[2], or sent to it, writes nothing and answers the form "add
    stage" filled with the folder of the disk its chooser opens on, the one
    that holds the model folder, and the place of the period's list, as a
    template's form names it. Dropped on a `+ period` control, it opens "add
    period" with no stage chosen, as a template does; an event of the kind
    `folder` with another id is no item the list offers and answers the
    sentence "An old graph"."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    folder = model.open_folder(created.folder)
    shown = show_trellis(folder, RECIPE_SOURCE).shown
    before = file_bytes(created.folder)

    def dropped(item, kind, target):
        return drop_edits(shown, dropped_event(shown, folder, item, kind, target), {})

    assert dropped("folder", "folder", "periods[2]___group___") == {
        "form": "add stage",
        "fill": {
            "folder": str(created.folder.resolve().parent),
            "period": "period.yml",
            "entry": "",
        },
    }
    assert dropped("folder", "folder", "earliest end") == {
        "form": "add period",
        "fill": {"head": "before periods[5]", "at": None, "keys": []},
    }
    old = old_graph_gesture(created.folder / "declaration/trellis.yml")
    assert dropped("port", "folder", "periods[2]___group___") == old
    assert file_bytes(created.folder) == before


def test_item_5_cases_a_stage_dropped_on_the_earliest_end_opens_the_form_headed_for_that_end(
    repository, own_cache_folder
):
    """Spec 0.4 §§3.2 and 3.6; brief §5, the form's heads: a stage of the
    recipe dropped on the `+ period` control at the earliest end of six
    periods writes nothing and answers the form "add period" headed `before
    periods[5]`, with the place `at` None and the dropped stage chosen; on
    the control between periods[3] and periods[2], the form headed `between
    periods[3] and periods[2]` with `at` 3, the index the new period takes.
    Enter on a control, an event with no item, and a template dropped on
    one choose no stage. No control stands at the terminal end or between
    two periods that are not adjacent, so an event that names one answers
    the sentence "An old graph" of brief §5."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    folder = model.open_folder(created.folder)
    shown = show_trellis(folder, RECIPE_SOURCE).shown
    before = file_bytes(created.folder)

    def dropped(item, kind, target):
        return drop_edits(shown, dropped_event(shown, folder, item, kind, target), {})

    assert dropped("cons", "stage", "earliest end") == {
        "form": "add period",
        "fill": {"head": "before periods[5]", "at": None, "keys": ["cons"]},
    }
    between = "between periods[3] and periods[2]"
    assert dropped("cons", "stage", between) == {
        "form": "add period",
        "fill": {"head": between, "at": 3, "keys": ["cons"]},
    }
    assert dropped(None, None, "earliest end")["fill"]["keys"] == []
    assert dropped(NOPORT_ID, "template", "between periods[1] and periods[0]") == {
        "form": "add period",
        "fill": {"head": "between periods[1] and periods[0]", "at": 1, "keys": []},
    }
    old = old_graph_gesture(created.folder / "declaration/trellis.yml")
    for target in (
        "between periods[0] and periods[-1]",
        "between periods[6] and periods[5]",
        "between periods[3] and periods[1]",
        "after periods[0]",
    ):
        assert dropped("cons", "stage", target) == old
    assert file_bytes(created.folder) == before


def test_item_5_cases_a_drop_on_a_folder_of_records(tmp_path, own_cache_folder):
    """Spec 0.4 §3.5 and J-D24: on a copy of applications/cons-port whose
    lesson 05 trellis file writes periods[0] without `disc`, the stage list
    is headed `This folder's stages` (brief §5; in sentence case since design
    pass 13 §3) and offers the keys the
    periods write as records and no template. `disc` dropped on periods[0]
    answers, writing nothing, the record another period writes copied into
    the entry of periods[0] (`creation.add_record_stage`); dropped on
    periods[3], whose entry holds it, a gesture with no edit and no
    sentence. A stage dropped on the `+ period` control at the earliest end,
    and Enter on the control between periods[3] and periods[2], open no
    form: each answers the inline entry `creation.add_record_period` writes,
    the second with the text for the restriction's input. A template, or
    the item `From a folder…` (unit K, Task 25), which the list does not
    offer, answers the sentence "An old graph"."""
    copy = records_without(tmp_path, 0, "disc")
    folder = model.open_folder(copy)
    file = copy / PORT_CONS_RECORDS
    path = str(file.resolve())
    shown = show_trellis(folder, RECORDS_SOURCE).shown
    listed = stage_items(folder, shown, {})
    assert listed["heading"] == "This folder's stages"
    assert listed["entries"] == [[0], [1, 2, 3, 4, 5]]
    assert [(item["kind"], item["key"], item["periods_listed"]) for item in listed["items"]] == [
        ("stage", "port", [0, 1, 2, 3, 4, 5]),
        ("stage", "cons", [0, 1, 2, 3, 4, 5]),
        ("stage", "disc", [1, 2, 3, 4, 5]),
    ]
    before = file_bytes(copy)

    def dropped(item, kind, target):
        return drop_edits(shown, dropped_event(shown, folder, item, kind, target), {})

    added = creation.add_record_stage(file, "disc", 0)
    assert dropped("disc", "stage", "periods[0]___group___") == Gesture(
        added.edits,
        added.read,
        (),
        "trellis.port-cons-vfi.yml, periods[0].stages: disc written, periods 0",
        None,
        path,
        "periods[0].stages",
    )
    assert dropped("disc", "stage", "periods[3]___group___") == Gesture(
        None, None, (), None, None, path, "periods[1].stages"
    )
    earliest = creation.add_record_period(file)
    assert dropped("port", "stage", "earliest end") == Gesture(
        earliest.edits, earliest.read, (), "; ".join(earliest.notes), None, path, "periods"
    )
    between = creation.add_record_period(file, at=3)
    gesture = dropped(None, None, "between periods[3] and periods[2]")
    assert gesture == Gesture(
        between.edits,
        between.read,
        (),
        "; ".join(between.notes),
        None,
        path,
        "periods",
        "periods 2–4",
    )
    assert dropped(NOPORT_ID, "template", "periods[0]___group___") == old_graph_gesture(file)
    assert dropped("folder", "folder", "periods[0]___group___") == old_graph_gesture(file)
    assert file_bytes(copy) == before


def test_item_5_cases_a_recipe_folder_without_answers(tmp_path, own_cache_folder):
    """Spec 0.4 §3.5: on a copy of applications/pension-retirement, a
    recipe folder of the corpus with no answers.yml, whose trellis file
    writes periods[0] in an entry of its own and the fourteen earlier
    periods from `period.yml`. The template `noport` dropped on periods[0]
    edits the recipe and the `stages` of that entry, the list the package
    resolves the period to, and writes no answers.yml; the status line names
    the entry's list and its one period. A template whose key the recipe
    holds opens the form with that entry. `terminal`, which the recipe
    restricts to periods 0 to 0, dropped on periods[3] is appended to
    `period.yml`'s list, which writes periods 1 to 14, and its range is
    widened to include period 3 (ruling J-P8), the comment at the recipe's
    head that writes the same range kept. Nothing is written to disk."""
    copy = repository_copy(PENSION_RETIREMENT, tmp_path / "pension-retirement")
    folder = model.open_folder(copy)
    shown = show_trellis(folder, RECIPE_SOURCE).shown
    recipe, trellis_file, period = (
        str((copy / "declaration" / name).resolve())
        for name in ("spec.yml", "trellis.yml", "period.yml")
    )
    before = file_bytes(copy)

    def dropped(item, kind, target):
        return drop_edits(shown, dropped_event(shown, folder, item, kind, target), {})

    gesture = dropped(NOPORT_ID, "template", "periods[0]___group___")
    assert list(gesture.edits) == [recipe, trellis_file]
    listed = "[worker_saving, retire_choice, retiree_saving, terminal"
    assert gesture.edits[trellis_file] == gesture.read[trellis_file].replace(
        listed + "]", listed + ", noport]"
    )
    assert gesture.edits[recipe].endswith(NOPORT_ROW)
    assert [path for path, _ in gesture.new_files] == [
        "declaration/stages/noport/noport.bl",
        "declaration/calibration/portfolio.yml",
        "declaration/settings/noport.yml",
        "declaration/stages/noport/methods.bl",
    ]
    assert (gesture.note, gesture.file, gesture.address) == (
        "trellis.yml, periods[0].stages: noport written, periods 0; new: stages/noport/noport.bl, "
        "calibration/portfolio.yml, settings/noport.yml, stages/noport/methods.bl; "
        "noport unconnected",
        trellis_file,
        "periods[0].stages",
    )
    assert dropped(WORKER_ID, "template", "periods[0]___group___") == {
        "form": "add stage",
        "fill": {"template": WORKER_ID, "period": "trellis.yml", "entry": "periods[0]"},
    }
    gesture = dropped("terminal", "stage", "periods[3]___group___")
    period_text, recipe_text = (
        Path(path).read_text(encoding="utf-8") for path in (period, recipe)
    )
    assert gesture.edits == {
        period: period_text.replace("  - retiree_saving\n", "  - retiree_saving\n  - terminal\n"),
        recipe: recipe_text.replace("periods: [0, 0]}", "periods: [0, 3]}"),
    }
    assert gesture.note == (
        "period.yml, stages: terminal written, periods 1–14; "
        "spec.yml, stages.terminal.periods: [0, 0] now [0, 3]; terminal unconnected"
    )
    assert file_bytes(copy) == before and not (copy / creation.ANSWERS).exists()


# --- new variant: a second trellis of the same model beside the first ---


def test_new_variant_writes_the_recipe_trellis_and_period_beside_the_first(scratch_pension):
    """`create_variant(folder, "two-stages", "spec.yml")` on a copy of the
    pension folder writes in `declaration/` spec.two-stages.yml, a copy of
    spec.yml whose `trellis:` line reads `trellis.two-stages.yml`;
    trellis.two-stages.yml, a copy of the trellis file spec.yml names whose
    `template:` line reads `period.two-stages.yml`; and
    period.two-stages.yml, a copy of that template. Every other line of each
    copy is byte-identical to its source, comments included, and no other
    file of the folder changes. `load_recipe` reads the variant's recipe to
    what it reads spec.yml to, record for record, with the path and the
    digest of the recipe and of the trellis file left out (ruling R24)
    (spec 0.3 §4, new variant)."""
    declaration = scratch_pension / "declaration"
    before = file_bytes(scratch_pension)
    assert creation.create_variant(scratch_pension, "two-stages", "spec.yml") == VARIANT_FILES
    after = file_bytes(scratch_pension)
    assert sorted(set(after) - set(before)) == sorted(VARIANT_FILES)
    assert {path: after[path] for path in before} == before
    # each source, with the one line its copy writes anew, or None for a
    # copy that is byte-identical to its source
    replaced = (
        ("declaration/spec.yml", b"trellis: trellis.yml\n", b"trellis: trellis.two-stages.yml\n"),
        (
            "declaration/trellis.yml",
            b"  - {template: period.yml, repeat: 14}\n",
            b"  - {template: period.two-stages.yml, repeat: 14}\n",
        ),
        ("declaration/period.yml", None, None),
    )
    for (source, line, written), copied in zip(replaced, VARIANT_FILES, strict=True):
        if line is None:
            assert after[copied] == before[source]
        else:
            assert before[source].count(line) == 1
            assert after[copied] == before[source].replace(line, written)
    source = load_recipe(declaration, "spec.yml")
    variant = load_recipe(declaration, "spec.two-stages.yml")
    assert variant["provenance"]["recipe"]["path"] == str(declaration / "spec.two-stages.yml")
    assert variant["provenance"]["trellis"]["path"] == str(declaration / "trellis.two-stages.yml")
    assert len(variant["periods"]) == 15
    assert without_file_provenance(variant) == without_file_provenance(source)


@pytest.mark.parametrize(
    "name", ["two stages", "two_stages", "two-stages.yml", "../two-stages", "", "zwei-stüfe"]
)
def test_new_variant_refuses_a_name_that_is_no_plain_word(scratch_pension, name):
    """A variant's name is a plain word, `[A-Za-z0-9-]+`, since it stands in
    the names of the variant's files; another name is refused in one line
    that names it and what to write, and nothing is written (spec 0.3 §4,
    new variant)."""
    before = file_bytes(scratch_pension)
    with pytest.raises(ValueError) as refused:
        creation.create_variant(scratch_pension, name, "spec.yml")
    assert str(refused.value) == f"{name!r} is no variant name: write letters, digits and '-'"
    assert file_bytes(scratch_pension) == before


def test_new_variant_refuses_a_name_whose_files_exist_before_writing_any(scratch_pension):
    """A name whose files exist is refused, before anything is written, with
    the sentence that names each existing file: the variant two-stages
    written a second time, and the name young, whose period file
    period.young.yml alone exists, so that its recipe and its trellis file
    are not written either (ruling R25). A recipe the folder does not hold,
    and a trellis file whose `template:` names a period file other than
    `period.yml` or `period.<x>.yml`, are refused with a sentence naming
    the file, and nothing is written (spec 0.3 §4, new variant)."""
    declaration = scratch_pension / "declaration"
    creation.create_variant(scratch_pension, "two-stages", "spec.yml")
    (declaration / "period.young.yml").write_bytes((declaration / "period.yml").read_bytes())
    before = file_bytes(scratch_pension)
    for name, recipe, sentence in (
        (
            "two-stages",
            "spec.yml",
            "declaration/spec.two-stages.yml, declaration/trellis.two-stages.yml and "
            "declaration/period.two-stages.yml exist",
        ),
        ("young", "spec.yml", "declaration/period.young.yml exists"),
        ("old", "spec.old.yml", "the folder holds no declaration/spec.old.yml"),
    ):
        with pytest.raises(ValueError) as refused:
            creation.create_variant(scratch_pension, name, recipe)
        assert str(refused.value) == sentence
        assert file_bytes(scratch_pension) == before
    trellis = declaration / "trellis.yml"
    trellis.write_bytes(
        trellis.read_bytes().replace(b"{template: period.yml,", b"{template: young.yml,")
    )
    (declaration / "young.yml").write_bytes((declaration / "period.yml").read_bytes())
    before = file_bytes(scratch_pension)
    with pytest.raises(ValueError, match=r"^declaration/trellis\.yml names the period file young"):
        creation.create_variant(scratch_pension, "old", "spec.yml")
    assert file_bytes(scratch_pension) == before


def test_new_variant_copies_each_period_file_and_stays_apart_from_its_source(repository):
    """On a folder "new trellis" wrote, to which "add period" added
    period.young.yml, `create_variant` copies both period files the trellis
    file names, period.yml as period.two-stages.yml and period.young.yml as
    period.two-stages.young.yml, and writes each `template:` line anew to
    name its copy (ruling R25); the variant's recipe reads to what spec.yml
    reads to. "Add stage" then offers the period files of spec.yml alone
    (`period_files`), and "add stage" and "add period" change the source's
    files and none of the variant's, whose recipe reads as before (spec
    0.3 §4, new variant: an edit of one recipe's files stays with that
    recipe)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    save_added(created.folder, creation.add_period(created.folder, "young", ["cons", "disc"]))
    written = creation.create_variant(created.folder, "two-stages", "spec.yml")
    assert written == (
        "declaration/spec.two-stages.yml",
        "declaration/trellis.two-stages.yml",
        "declaration/period.two-stages.yml",
        "declaration/period.two-stages.young.yml",
    )
    declaration = created.folder / "declaration"
    trellis = (declaration / "trellis.yml").read_text(encoding="utf-8")
    assert (declaration / "trellis.two-stages.yml").read_text(encoding="utf-8") == (
        trellis.replace("{template: period.yml,", "{template: period.two-stages.yml,").replace(
            "{template: period.young.yml,", "{template: period.two-stages.young.yml,"
        )
    )
    for source, copied in (
        ("period.yml", "period.two-stages.yml"),
        ("period.young.yml", "period.two-stages.young.yml"),
    ):
        assert (declaration / copied).read_bytes() == (declaration / source).read_bytes()
    variant = without_file_provenance(load_recipe(declaration, "spec.two-stages.yml"))
    assert variant == without_file_provenance(load_recipe(declaration, "spec.yml"))
    held = {path: (created.folder / path).read_bytes() for path in written}
    assert creation.period_files(created.folder) == ("period.yml", "period.young.yml")
    save_added(created.folder, creation.add_stage(created.folder, "noport", NOPORT_ID))
    save_added(created.folder, creation.add_period(created.folder, "old", ["noport"]))
    assert creation.period_files(created.folder) == (
        "period.yml",
        "period.old.yml",
        "period.young.yml",
    )
    assert {path: (created.folder / path).read_bytes() for path in written} == held
    assert len(load_recipe(declaration, "spec.yml")["periods"]) == 8
    assert without_file_provenance(load_recipe(declaration, "spec.two-stages.yml")) == variant


def test_new_variant_from_the_page_writes_the_variant_and_opens_its_recipe(
    scratch_pension, tmp_path, app_state
):
    """The folder's bar holds `new variant` where the folder holds
    declaration/spec.yml and not elsewhere. Its one-line form, given the
    name two-stages, writes the variant's three files, closes, reads the
    tree again, which lists them as a recipe, a trellis file and a period
    file, and opens the variant's recipe in the editor as a click on it in
    the tree does: the recipe list shows the variant beside the first, and
    the view the variant's trellis (spec 0.3 §4, new variant: "The recipe
    list of §3 shows the variant beside the first")."""
    plain = tmp_path / "plain"
    plain.mkdir()
    app_state(plain)
    _, rendered = solara.render(app.FolderActions(), handle_error=False)
    try:
        assert not rendered.find(v.Html, class_="bl-new-variant").widgets
    finally:
        rendered.close()
    app_state(scratch_pension)
    _, rendered = solara.render(app.FolderActions(), handle_error=False)
    try:
        rendered.find(v.Html, class_="bl-new-variant").widget.fire_event("click", {})
    finally:
        rendered.close()
    assert app.form_open.value == "new variant"
    _, rendered = solara.render(app.NewVariantForm(), handle_error=False)
    try:
        enter_text(rendered, "Name", "two-stages")
        enter_text(rendered, "Binding files", "Share binding files")
        press_words(rendered, "Write the variant")
    finally:
        rendered.close()
    try:
        assert (app.form_error.value, app.form_open.value) == ("", None)
        roles = {path: entry["role"] for path, entry in tree_entries(app.tree.value).items()}
        assert [roles.get(path) for path in VARIANT_FILES] == ["recipe", "trellis", "period"]
        assert app.open_path.value == "declaration/spec.two-stages.yml"
        variant = Source("recipe", "declaration/spec.two-stages.yml")
        assert app.sources.value == [Source("recipe", "declaration/spec.yml"), variant]
        assert (app.source.value, app.view_mode.value) == (variant, "trellis")
    finally:
        # the bar's text, the restriction and the window's own text of the
        # bar, which the variant's trellis of fifteen periods opens with
        app.restriction.value, app.restriction_text.value = None, ""
        app.restriction_opening.value = ""


def test_new_variant_refuses_while_a_file_it_copies_holds_unsaved_text(scratch_pension, app_state):
    """While the buffer of the recipe the variant copies, declaration/spec.yml,
    holds unsaved text, the form "new variant" is refused in one line
    naming the file, and nothing is written, since the variant copies the
    files on disk; the buffer keeps its text (spec 0.3 §4, new variant;
    §2.2 rule 3)."""
    recipe = "declaration/spec.yml"
    app_state(scratch_pension)
    app.open_file(recipe)
    held = app.buffers.value[recipe]
    app.buffers.value = {recipe: {**held, "text": held["text"] + "# typed\n"}}
    before = file_bytes(scratch_pension)
    app.submit_new_variant("two-stages")
    assert app.form_error.value == f"{recipe} holds unsaved text"
    assert file_bytes(scratch_pension) == before
    assert app.buffers.value[recipe]["text"].endswith("# typed\n")


def test_independent_variant_keeps_order_shared_files_and_copies_methods_bl_as_methods_variant_bl(
    scratch_folder,
):
    declaration = scratch_folder / "declaration"
    calibration = declaration / "calibration/portfolio.yml"
    parent = declaration / "calibration/returns.yml"
    parent.write_text("calibration: {R: 1.02}\n", encoding="utf-8")
    calibration.write_text(
        "parent: calibration/returns\n" + calibration.read_text().replace("  R: 1.02\n", ""),
        encoding="utf-8",
    )
    registry = declaration / "calibration/age.yml"
    registry.write_text("calibration: {age: 25}\n", encoding="utf-8")
    recipe = declaration / "spec.yml"
    recipe.write_text(
        recipe.read_text().replace("calibration/portfolio]", "calibration/portfolio.yml]", 1)
        + "registry: {calibration: [calibration/age]}\n",
        encoding="utf-8",
    )
    before = file_bytes(scratch_folder)
    written = creation.create_variant(scratch_folder, "alternative", "spec.yml", copy_bindings=True)
    assert written[0] == "declaration/spec.alternative.yml"
    assert all((scratch_folder / path).read_bytes() == data for path, data in before.items())

    base = load_recipe(declaration, "spec.yml")
    variant = load_recipe(declaration, "spec.alternative.yml")
    assert variant["registry"] == base["registry"]
    old_registry = base["provenance"]["registry"]["calibration"][0]["path"]
    new_registry = variant["provenance"]["registry"]["calibration"][0]["path"]
    assert new_registry != old_registry
    stages = variant["periods"][0]["stages"]
    sources = {key: stage["provenance"]["source_lists"] for key, stage in stages.items()}
    assert len({source["calibration"][0]["path"] for source in sources.values()}) == 1
    copied = sources["cons"]["calibration"][0]
    assert copied["path"] != str(calibration)
    assert copied["parents"][0] != str(parent)
    for key, stage in stages.items():
        assert stage["calibration"] == base["periods"][0]["stages"][key]["calibration"]
        assert stage["settings"] == base["periods"][0]["stages"][key]["settings"]
    old_methods = declaration / "stages/cons/methods.bl"
    new_methods = Path(sources["cons"]["methods"][0]["path"])
    assert new_methods == declaration / "stages/cons/methods.alternative.bl"
    assert new_methods.read_bytes() == old_methods.read_bytes()
    assert "!egm" in str(specify_trellis(variant)["periods"][0]["stages"]["cons"].methods)


def test_independent_variant_refuses_an_unsupported_source_before_writing(scratch_folder):
    declaration = scratch_folder / "declaration"
    original = declaration / "calibration/portfolio.yml"
    original.rename(original.with_suffix(""))
    before = file_bytes(scratch_folder)
    with pytest.raises(ValueError, match=r"cannot copy calibration source .*/calibration/portfolio"):
        creation.create_variant(scratch_folder, "alternative", "spec.yml", copy_bindings=True)
    assert file_bytes(scratch_folder) == before


def test_independent_variant_refuses_dirty_binding_before_writing(scratch_folder, app_state):
    path = "declaration/calibration/portfolio.yml"
    app_state(scratch_folder)
    app.open_file(path)
    held = app.buffers.value[path]
    app.buffers.value = {path: {**held, "text": held["text"] + "# typed\n"}}
    before = file_bytes(scratch_folder)
    app.submit_new_variant("alternative", copy_bindings=True)
    assert app.form_error.value == f"{path} holds unsaved text"
    assert file_bytes(scratch_folder) == before


def test_handover_notebook_reads_the_named_variant_and_keeps_existing_notebooks(scratch_folder):
    base = creation.write_notebook(scratch_folder, RECIPE_FILE, "recipe")
    original = (scratch_folder / base).read_bytes()
    variant, *_ = creation.create_variant(scratch_folder, "alternative", "spec.yml")
    copied = creation.write_notebook(scratch_folder, variant, "recipe")
    assert copied is not None and copied != base
    notebook = nbformat.read(scratch_folder / copied, as_version=4)
    assert f'"../{variant}"' in notebook.cells[0].source
    assert creation.write_notebook(scratch_folder, variant, "recipe") is None
    assert (scratch_folder / base).read_bytes() == original


def test_r_write_notebook_keeps_the_first_cell_of_the_source_s_kind_and_writes_once(
    scratch_folder, scratch_consport, monkeypatch
):
    """`write_notebook` (spec 0.4 §5.9; brief rule 7; review 11; R-D40,
    R-D41) writes `notebooks/<folder>.ipynb` for the portfolio model's
    recipe and for cons-port's trellis file port-cons, whose stage files
    stand in the portfolio model's folder. The file validates under
    nbformat; its first cell is the form for the source's kind, naming
    `load_recipe` and `assemble_trellis`, or `load_trellis` and
    `specify_trellis`, with the source's path from `notebooks/`; it holds
    no digest of a file it reads. A second call answers None and leaves the
    bytes. The code cells, run in one namespace with `notebooks/` as the
    working directory, print each stage occurrence's sheet under its
    position; for the occurrence `periods[0] / cons`, the first seven
    characters of the digests `model.input_digests` gives, as the status
    line prints them; and the methods bound to each occurrence."""
    forms = {
        "recipe": ("load_recipe", "assemble_trellis"),
        "trellis": ("load_trellis", "specify_trellis"),
    }
    cases = (
        (scratch_folder, Source("recipe", RECIPE_FILE), CONS, "notebooks/portfolio-choice.ipynb"),
        (
            scratch_consport, Source("recipe", PORT_CONS_RECIPE), SHARED_CONS,
            "notebooks/cons-port.spec.port-cons.yml.ipynb",
        ),
    )
    for folder, source, cons_path, expected in cases:
        written = creation.write_notebook(folder, source.path, source.kind)
        assert written == expected
        data = (folder / written).read_bytes()
        text = data.decode("utf-8")
        notebook = nbformat.reads(text, as_version=4)
        nbformat.validate(notebook)
        code = [cell for cell in notebook.cells if cell.cell_type == "code"]
        assert len(code) == 4
        (other,) = (names for kind, names in forms.items() if kind != source.kind)
        assert all(name in code[0].source for name in forms[source.kind]), code[0].source
        assert not any(name in text for name in other)
        assert f'"../{source.path}"' in code[0].source
        assert "{{source}}" not in text
        assert creation.write_notebook(folder, source.path, source.kind) is None
        assert (folder / written).read_bytes() == data

        # the trellis the Workbench reads from the source, and the digests the
        # status line prints for the consumption stage's first occurrence
        specified = specify_trellis(read_source(model.open_folder(folder), source))
        occurrences = [
            (f"periods[{h}] / {key}", stage)
            for h, period in enumerate(specified["periods"])
            for key, stage in period["stages"].items()
        ]
        cons = specified["periods"][0]["stages"]["cons"]
        digests = model.input_digests(cons, (folder / cons_path).read_text(encoding="utf-8"))
        assert set(digests) == {"text", "calibration", "methods", "settings"}
        assert not any(digest[:7] in text for digest in digests.values())

        monkeypatch.chdir(folder / "notebooks")
        sheets, printed, methods = code_cell_outputs(folder / written)[1:]
        for position, stage in occurrences:
            assert f"{position}\n{stage.view().splitlines()[0]}\n" in sheets, position
            assert f"{position}\n{stage.methods}\n" in methods, position
        line = " · ".join(
            ["periods[0] / cons", *(f"{name} {digest[:7]}" for name, digest in digests.items())]
        )
        assert line in printed.splitlines()
        assert len(printed.splitlines()) == len(occurrences)


# --- unit L, Task 13: the templates read per entry, a folder with no
# template, the parent folder asked, and a variant's own labels ---

# the eight ids of the templates, in the order of TEMPLATE_SOURCES
TEMPLATE_IDS = [
    PORT_ID,
    CONS_ID,
    DISC_ID,
    NOPORT_ID,
    WORKER_ID,
    "pension-retirement/declaration/spec.yml#retire_choice",
    "pension-retirement/declaration/spec.yml#retiree_saving",
    TERMINAL_ID,
]
# the files a folder written with no template holds, by their posix paths
# from it, git's own folder left out
EMPTY_FOLDER_FILES = (
    ".gitignore",
    "README.md",
    "answers.yml",
    "declaration/period.yml",
    "declaration/spec.yml",
    "declaration/trellis.yml",
)


def test_l_13_a_refused_corpus_file_is_listed_with_its_rule_and_the_others_offered(
    tmp_path, monkeypatch
):
    """Unit L, Task 13 (defect 1 of the UX simulation): the templates are
    read per entry of TEMPLATE_SOURCES, so that with the portfolio model's
    cons.bl refused under `output-defined` the entries are the eight in
    their order, `cons` the one refused, with the package's sentence, its
    rule and the stage file refused, and the seven others are the templates
    offered, `template_of` refusing the id of `cons`; a second reading
    answers the same entries, each read once for the state of its files;
    once the stage file is written correct, the next reading offers `cons`
    again with no restart. A corpus file the reader refuses refuses its own
    entries alone, each with the reader's sentence."""
    corpus = refused_corpus(tmp_path / "corpus")
    monkeypatch.setattr(creation, "CORPUS", corpus)
    cons_file = corpus / "portfolio-choice/declaration/stages/cons/cons.bl"
    entries = creation.template_entries()
    assert [entry.id for entry in entries] == TEMPLATE_IDS
    (refused,) = [entry for entry in entries if isinstance(entry, creation.RefusedTemplate)]
    assert (refused.id, refused.key, refused.rule) == (CONS_ID, "cons", "output-defined")
    assert refused.file == cons_file.resolve()
    assert "declares output 'cons:dcsn:c'" in refused.sentence
    assert [template.id for template in creation.stage_templates()] == [
        template_id for template_id in TEMPLATE_IDS if template_id != CONS_ID
    ]
    with pytest.raises(ValueError, match="no template of a stage is named"):
        creation.template_of(CONS_ID)
    again = creation.template_entries()
    assert all(first is second for first, second in zip(entries, again, strict=True))

    # the stage file written correct is read again at the next reading
    cons_file.write_text(
        (PORTFOLIO / "stages/cons/cons.bl").read_text(encoding="utf-8"), encoding="utf-8"
    )
    cons = creation.template_of(CONS_ID)
    assert (cons.key, cons.calibration) == ("cons", ("ρ",))

    # a corpus file the reader refuses refuses its own four entries alone
    recipe_file = corpus / "pension-retirement/declaration/spec.yml"
    recipe_file.write_text("stages: [\n", encoding="utf-8")
    entries = creation.template_entries()
    refused = [entry for entry in entries if isinstance(entry, creation.RefusedTemplate)]
    assert [entry.id for entry in refused] == TEMPLATE_IDS[4:]
    assert {entry.file for entry in refused} == {recipe_file.resolve()}
    assert [template.id for template in creation.stage_templates()] == TEMPLATE_IDS[:4]


def test_l_13_an_exception_of_the_package_refuses_its_own_entries_and_the_others_are_offered(
    tmp_path, monkeypatch
):
    """Unit L, Task 13 (unit L's final judgment, §6 item 7): an exception of
    no class of the package's refusals, as the KeyError the elaborator
    raises for an unresolved semantic input, refuses the entries whose
    reading raised it, as Python prints the exception and under the rule
    `package-exception`, and the other entries are offered: raised by the
    reading of the pension model's recipe, its four entries; raised by the
    reading of the stage file of `noport`, that entry alone."""
    corpus = refused_corpus(tmp_path / "corpus")
    monkeypatch.setattr(creation, "CORPUS", corpus)
    pension = (corpus / "pension-retirement/declaration/spec.yml").resolve()
    noport = (corpus / "portfolio-choice/declaration/stages/noport/noport.bl").resolve()
    load_recipe, load_stage = creation.load_recipe, creation.load_stage
    raised = KeyError("unresolved semantic input at dcsn_to_cntn.contributions")

    def recipe_raising(folder, name):
        if (Path(folder) / name).resolve() == pension:
            raise raised
        return load_recipe(folder, name)

    def stage_raising(path):
        if Path(path).resolve() == noport:
            raise raised
        return load_stage(path)

    monkeypatch.setattr(creation, "load_recipe", recipe_raising)
    monkeypatch.setattr(creation, "load_stage", stage_raising)
    entries = creation.template_entries()
    assert [entry.id for entry in entries] == TEMPLATE_IDS
    sentence = "KeyError: 'unresolved semantic input at dcsn_to_cntn.contributions'"
    refused = {
        entry.id: (entry.rule, entry.sentence, entry.file)
        for entry in entries
        if isinstance(entry, creation.RefusedTemplate)
    }
    assert refused.pop(CONS_ID)[0] == "output-defined"
    assert refused == {
        NOPORT_ID: ("package-exception", sentence, noport),
        **{each: ("package-exception", sentence, pension) for each in TEMPLATE_IDS[4:]},
    }
    assert [template.id for template in creation.stage_templates()] == [PORT_ID, DISC_ID]


def test_l_13_new_trellis_writes_a_folder_with_no_stage_which_new_stage_fills(tmp_path):
    """Unit L, Task 13 (defect 1): with no template chosen, `create_trellis`
    writes the folder with no stage, its recipe's `stages` and its period's
    `stages` empty in flow style, `{}` and `[]`, answers.yml's `stages` and
    `required.slots` the same, and a README that names no template; the
    package reads its recipe as three periods with no stage, and `new
    stage` then adds its first row to the recipe and its slots to
    answers.yml as text."""
    created = creation.create_trellis(tmp_path, "empty-model", [], "empty_period", 3)
    assert created.files == EMPTY_FOLDER_FILES and created.repository
    folder = created.folder
    recipe_text = (folder / "declaration/spec.yml").read_text(encoding="utf-8")
    period_text = (folder / "declaration/period.yml").read_text(encoding="utf-8")
    answers = (folder / "answers.yml").read_text(encoding="utf-8")
    assert "stages: {}\n" in recipe_text and entry_value(recipe_text, "stages") == {}
    assert "stages: []\n" in period_text and entry_value(period_text, "stages") == []
    assert entry_value(answers, "stages") == {}
    assert entry_value(answers, "required.slots") == []
    assert "template" not in (folder / "README.md").read_text(encoding="utf-8")
    read = load_recipe(folder / "declaration", "spec.yml")
    assert [period["stages"] for period in read["periods"]] == [{}, {}, {}]
    added = creation.new_stage(folder, "shocks")
    edited = {
        Path(path).relative_to(folder).as_posix(): text for path, text in added.edits.items()
    }
    assert list(entry_value(edited["declaration/spec.yml"], "stages")) == ["shocks"]
    assert entry_value(edited["answers.yml"], "required.slots") == [
        creation.slot_name("shocks", kind) for kind in creation.SLOT_KINDS
    ]


def test_l_13_new_trellis_refuses_a_parent_that_is_no_folder_or_lies_in_a_model_folder(
    tmp_path,
):
    """Unit L, Task 13 (defect 15): `create_trellis` refuses, before writing
    anything, a parent that names no folder, and a parent that is a model
    folder, a folder that holds `declaration/`, or lies in one, so that no
    new model is written inside another model's folder."""
    other = tmp_path / "durables"
    (other / "declaration/stages").mkdir(parents=True)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    for parent, words in (
        (tmp_path / "nowhere", "is no folder"),
        (other, "is a model folder"),
        (other / "declaration", "lies in the model folder"),
        (other / "declaration/stages", "lies in the model folder"),
    ):
        with pytest.raises(ValueError, match=words):
            creation.create_trellis(parent, "new-model", [], "p", 1)
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before


def test_l_13_the_form_new_trellis_writes_beside_the_open_model_with_one_template_refused(
    tmp_path, app_state, monkeypatch
):
    """Unit L, Task 13 (defects 1, 15 and 26; design pass 4 §3): over a copy
    of the durables model with the corpus's cons.bl refused, the form `new
    trellis` asks the parent folder, the folder that holds the open model by
    default, and its note says `writes models/<name>/ beside durables`; the
    template list holds the seven templates read and, in the place of
    `cons`, its row `.bl-template-refused` with its key, its model's folder
    and `refused · output-defined`, the package's sentence in its hover;
    `write the folder` does not act while no name is typed, its hover
    `type a name`, and acts once one is, no template chosen; it writes the
    new folder beside the durables model, which is left as it was, and
    opens the new folder's recipe for editing."""
    corpus = refused_corpus(tmp_path / "corpus")
    monkeypatch.setattr(creation, "CORPUS", corpus)
    models = tmp_path / "models"
    durables = repository_copy(DURABLES, models / "durables")
    before = file_bytes(durables)
    app_state(durables)
    app.open_form("new trellis")

    def submit():
        return rendered.find(v.Html, tag="vscode-button", children=["Write the folder"]).widget

    _, rendered = solara.render(app.NewTrellisForm(), handle_error=False)
    try:
        assert form_field(rendered, "Parent folder").widget.value == str(models.resolve())
        note = rendered.find(v.Html, class_="bl-form-note").widgets[0]
        assert note.children == ["writes models/<name>/ beside durables, with a new repository"]
        rows = rendered.find(v.Html, class_="bl-template-refused").widgets
        assert [row.attributes["data-template"] for row in rows] == [CONS_ID]
        texts = [part.children[0] for part in rows[0].children if part.tag == "span"]
        assert texts == ["cons", "portfolio-choice", "refused · output-defined"]
        hover = rows[0].attributes["title"]
        assert "declares output 'cons:dcsn:c'" in hover and "rule output-defined" in hover
        assert str(corpus) not in hover
        listed = [
            widget.attributes["data-template"]
            for widget in rendered.find(v.Html, tag="button").widgets
            if "data-template" in widget.attributes
        ]
        assert listed == [template_id for template_id in TEMPLATE_IDS if template_id != CONS_ID]
        assert submit().attributes["disabled"] and submit().attributes["title"] == "type a name"
        enter_text(rendered, "Name", "pension-model")
        assert "disabled" not in submit().attributes and "title" not in submit().attributes
        submit().fire_event("click", {})
    finally:
        rendered.close()
    created = (models / "pension-model").resolve()
    try:
        assert app.form_error.value == ""
        assert app.tab_folder.value.root == created
        assert app.open_path.value == "declaration/spec.yml"
        assert app.form_open.value is None
        assert sorted(
            path.relative_to(created).as_posix()
            for path in created.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(created).parts
        ) == list(EMPTY_FOLDER_FILES)
        assert file_bytes(durables) == before
    finally:
        # the new folder's source, its trellis's state and its tree, which
        # opening it set and `app_state` does not clear, cleared, so that a
        # later test of the process starts with no source (unit L's final
        # judgment, §6 item 5)
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False
        app.commit_message.value = ""


def test_l_13_the_form_new_trellis_draws_a_refusal_under_the_field_it_concerns(
    tmp_path, app_state, monkeypatch
):
    """Unit L, Task 13 (design pass 4 §2; unit L's final judgment, §6 item
    10): the form `new trellis` draws its one refusal under the field the
    refusal concerns, and nothing is written: a name that exists beside
    the open model under the row of the name and the periods, a period
    label that is not letters, digits and `_` under the period's label, a
    number of periods below one under that row, and a parent folder that
    is no full path under the parent folder, which the submission refuses,
    since the form's primary waits while the field names no folder."""
    monkeypatch.setattr(creation, "CORPUS", refused_corpus(tmp_path / "corpus"))
    models = tmp_path / "models"
    durables = repository_copy(DURABLES, models / "durables")
    before = sorted(path.relative_to(models) for path in models.rglob("*"))
    app_state(durables)
    app.open_form("new trellis")
    _, rendered = solara.render(app.NewTrellisForm(), handle_error=False)

    def field(label, text):
        enter_text(rendered, label, text)

    def refused_after():
        # the refusal's sentence and the classes of the element before it,
        # a field's wrapper (field.vue) or the row of two fields
        (refusal,) = rendered.find(v.Html, class_="bl-form-error").widgets
        (form,) = [
            widget
            for widget in rendered.find().widgets
            if refusal in getattr(widget, "children", ())
        ]
        order = list(form.children)
        before = order[order.index(refusal) - 1]
        return refusal.children[0], (getattr(before, "classes", "") or before.class_).split()

    def submit():
        press_words(rendered, "Write the folder")

    try:
        field("Name", "durables")
        submit()
        sentence, before_class = refused_after()
        assert sentence.endswith("durables exists") and "bl-form-row" in before_class
        field("Name", "pension-model")
        field("Period label (optional)", "a-b")
        submit()
        sentence, before_class = refused_after()
        assert sentence.startswith("'a-b' is no period label")
        assert "bl-create-label" in before_class
        field("Period label (optional)", "")
        field("Periods", "0")
        submit()
        sentence, before_class = refused_after()
        assert sentence.startswith("the number of periods is 0") and "bl-form-row" in before_class
        field("Periods", "2")
        field("Parent folder", "models")
        # the primary waits while the parent folder names no folder, its
        # click then calling nothing (unit M, Task 6), so the refusal is
        # asked of the submission itself with the form's values
        assert form_field(rendered, "Parent folder").widget.value == "models"
        app.submit_new_trellis("models", "pension-model", "", "pension_model_period", 2, [], [])
        sentence, before_class = refused_after()
        assert sentence == "models is no full path: write it from / or from ~"
        assert "bl-create-parent" in before_class
    finally:
        rendered.close()
        app.close_form()
    assert sorted(path.relative_to(models) for path in models.rglob("*")) == before


def test_l_13_a_variant_s_labels_come_from_its_own_recipe_and_its_form_names_the_registry(
    scratch_durables, app_state, own_cache_folder
):
    """Unit L, Task 13 (defect 19): the form `new variant` over the durables
    model, whose recipe holds a `registry` block, names under its note the
    registry it copies, `copies the registry of spec.yml:
    calibration/wage_schedule`; in the stage list of the variant's trellis
    each of the folder's stages carries the variant recipe's name,
    `spec.pensions.yml`, and not the durables model's title, which the
    folder's own recipe keeps; and the periods' ages come from the variant's
    own registry, so that with its `registry` block taken out no period
    carries an age."""
    copy = scratch_durables
    app_state(copy)
    app.open_form("new variant")
    _, rendered = solara.render(app.NewVariantForm(), handle_error=False)
    try:
        notes = [
            widget.children[0] for widget in rendered.find(v.Html, class_="bl-form-note").widgets
        ]
    finally:
        rendered.close()
    assert notes == [
        "writes spec.<name>.yml, trellis.<name>.yml and period.<name>.yml in declaration/",
        "Copies calibration, settings and method assignments.",
        "Stage declarations are shared in both modes. Slots keep their names.",
        "Copies registry sources: calibration/wage_schedule",
    ]
    creation.create_variant(copy, "pensions", "spec.yml")
    folder = model.open_folder(copy)
    restriction = parse_restriction("periods 0–2")
    title = creation._model_title(copy)
    for name, expected in (("spec.yml", title), ("spec.pensions.yml", "spec.pensions.yml")):
        shown = show_trellis(folder, Source("recipe", f"declaration/{name}"), restriction).shown
        items = stage_items(folder, shown, {})["items"]
        assert {item["title"] for item in items if item["kind"] == "stage"} == {expected}, name

    def ages(name):
        shown = show_trellis(folder, Source("recipe", f"declaration/{name}"), restriction).shown
        (forward,) = [graph for graph in shown.collection["graphs"] if graph["id"] == "forward"]
        layers = forward["groupNodeAttributes"]
        return [layers[f"periods[{h}]"].get("age") for h in range(3)]

    assert ages("spec.pensions.yml") == ["70", "69", "68"]
    variant = copy / "declaration/spec.pensions.yml"
    text = variant.read_text(encoding="utf-8")
    variant.write_text(text[: text.index("registry:")], encoding="utf-8")
    assert ages("spec.pensions.yml") == [None, None, None]
    assert ages("spec.yml") == ["70", "69", "68"]


# The portfolio model's row of the stage `port` and its line in period.yml,
# which `remove_stage` takes out (unit L, Task 25)
PORT_ROW = (
    "  port: {stage: stages/port/port.bl, calibration: {all: [calibration/portfolio]}, "
    "settings: {all: [settings/port]}, methods: {all: [stages/port/methods.bl]}}\n"
)
PORT_LISTED = "  - port\n"
# the portfolio model's period file, relative to the folder
PORTFOLIO_PERIOD = "declaration/period.yml"
# the entry of the portfolio model's trellis file, its six periods
SIX_PERIODS = "  - {template: period.yml, repeat: 6}\n"


def test_l_25_remove_stage_takes_its_row_and_keys_and_lists_the_files_only_it_names(
    scratch_folder, scratch_durables
):
    """Unit L, Task 25 (AAS, L-D18), by direct call, nothing written to
    disk. In the portfolio model, `remove_stage` of `port` answers the
    recipe without port's row and period.yml without its key, the notes
    naming each file and address, and lists as deleted on save the stage's
    folder `stages/port/` and `settings/port.yml`, which no other row names,
    and not `calibration/portfolio.yml`, which the rows of cons and disc
    name. In the durables model, `bequest`'s folder is not listed while the
    variant `spec.two-stages.yml` names its stage file, and is listed once
    the variant's recipe is gone. A key the recipe does not hold is
    refused."""
    root = scratch_folder
    files = (RECIPE_FILE, PORTFOLIO_PERIOD)
    names = {name: (root / name).read_text(encoding="utf-8") for name in files}
    assert names[RECIPE_FILE].count(PORT_ROW) == 1
    assert names[PORTFOLIO_PERIOD].count(PORT_LISTED) == 1
    removed = creation.remove_stage(root, "port")
    paths = {name: str((root / name).resolve()) for name in names}
    assert removed.edits == {
        paths[RECIPE_FILE]: names[RECIPE_FILE].replace(PORT_ROW, ""),
        paths[PORTFOLIO_PERIOD]: names[PORTFOLIO_PERIOD].replace(PORT_LISTED, ""),
    }
    assert removed.read == {paths[name]: names[name] for name in names}
    assert removed.notes == (
        "spec.yml, stages: port removed",
        "period.yml, stages: port removed, periods 0–5",
        "deleted on save: stages/port/, settings/port.yml",
    )
    assert removed.deleted == ("declaration/stages/port", "declaration/settings/port.yml")
    assert (removed.new_files, removed.restriction) == ((), None)
    assert {name: (root / name).read_text(encoding="utf-8") for name in names} == names
    assert (root / "declaration/stages/port/port.bl").is_file()
    with pytest.raises(ValueError, match="the recipe holds no stage 'buyer'"):
        creation.remove_stage(root, "buyer")

    # the durables model's bequest, whose stage file the variant names
    variant = creation.remove_stage(scratch_durables, "bequest")
    assert variant.deleted == ()
    assert variant.notes == (
        "spec.yml, stages: bequest removed",
        "trellis.yml, periods[0].stages: bequest removed, periods 0",
    )
    (scratch_durables / "declaration/spec.two-stages.yml").unlink()
    alone = creation.remove_stage(scratch_durables, "bequest")
    assert alone.deleted == ("declaration/stages/bequest",)
    assert alone.notes[-1] == "deleted on save: stages/bequest/"


def test_l_25_remove_stage_takes_answers_records_of_the_stage(repository):
    """Unit L, Task 25: in a folder `new trellis` wrote, `remove_stage` of
    `port` also takes answers.yml's records of the stage, its entry under
    `stages` and the names of its two slots in `required.slots`, the
    other stages' records kept; the stage's folder is listed as deleted on
    save, its bindings being slots that name no file."""
    work, _ = repository
    folder = creation.create_trellis(
        work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6
    ).folder
    removed = creation.remove_stage(folder, "port")
    answers = removed.edits[str((folder / creation.ANSWERS).resolve())]
    document = entry_value(answers)
    assert list(document["stages"]) == ["cons", "disc"]
    assert document["required"]["slots"] == [
        creation.slot_name(key, kind) for key in ("cons", "disc") for kind in creation.SLOT_KINDS
    ]
    assert "answers.yml: the records of port removed" in removed.notes
    assert removed.deleted == ("declaration/stages/port",)


def test_n_5_without_row_takes_what_a_removed_last_occurrence_takes_from_the_recipe(
    scratch_folder, repository
):
    """Unit N, Task 5 (N-D8), by direct call, nothing written to disk:
    `without_row` of `port` in the portfolio model answers the recipe
    without port's row and nothing else, its one note naming the row, and
    lists no file to delete on save, `stages/port/` staying on disk; read
    with an unsaved recipe, it edits that text. In a folder `new trellis`
    wrote, it also takes answers.yml's records of the stage, its note
    following the row's, as `remove_stage` takes them. A key the recipe
    does not hold is refused."""
    root = scratch_folder
    text = (root / RECIPE_FILE).read_text(encoding="utf-8")
    path = str((root / RECIPE_FILE).resolve())
    removed = creation.without_row(root, "port")
    assert removed == creation.Added(
        (), {path: text.replace(PORT_ROW, "")}, {path: text}, ("spec.yml, stages: port removed",)
    )
    assert (root / RECIPE_FILE).read_text(encoding="utf-8") == text
    assert (root / "declaration/stages/port/port.bl").is_file()
    unsaved = text.replace("# ", "#  ", 1)
    assert creation.without_row(root, "port", texts={path: unsaved}).edits == {
        path: unsaved.replace(PORT_ROW, "")
    }
    with pytest.raises(ValueError, match="the recipe holds no stage 'buyer'"):
        creation.without_row(root, "buyer")

    work, _ = repository
    folder = creation.create_trellis(
        work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6
    ).folder
    removed = creation.without_row(folder, "port")
    answers = entry_value(removed.edits[str((folder / creation.ANSWERS).resolve())])
    assert list(answers["stages"]) == ["cons", "disc"]
    assert removed.notes == (
        "spec.yml, stages: port removed",
        "answers.yml: the records of port removed",
    )
    assert removed.deleted == ()


def test_l_25_remove_period_takes_an_entry_out_or_lowers_its_repeat(scratch_folder):
    """Unit L, Task 25 (AAS, L-D18; spec 0.4 §3.6 in reverse), by direct
    call. In the portfolio model, periods[2] of the entry `{template:
    period.yml, repeat: 6}` lowers its repeat to 5, nothing deleted. With an
    earliest entry `{template: period.young.yml, repeat: 1}` of its own
    period file, a recipe that gives port the periods 0 to 6 and cons's
    calibration the range keys `0-5` and `6-6` beside `all`, and one
    inter-period mapping for each pair: periods[6] removed takes the entry
    out with the mapping of the pair into periods[5], lowers port's range
    to 0 to 5 and takes the list `6-6` out, lists period.young.yml as
    deleted on save, and the recipe and the trellis read from those texts;
    with period.yml named by the young entry too, the file is not listed. A
    trellis of one period, and an index that is no period, are refused."""
    root = scratch_folder
    trellis_file = root / "declaration" / creation.TRELLIS
    text = trellis_file.read_text(encoding="utf-8")
    lowered = creation.remove_period(root, 2)
    assert lowered.edits == {str(trellis_file.resolve()): text.replace("repeat: 6}", "repeat: 5}")}
    assert lowered.notes == ("trellis.yml, periods[0].repeat: 6 now 5", "restriction emptied")
    assert (lowered.deleted, lowered.restriction) == ((), "")

    young = SIX_PERIODS + "  - {template: period.young.yml, repeat: 1}\n"
    pairs = "inter_connectors:\n" + "".join(f"  - {{disc.a: k}}  # pair {p}\n" for p in range(6))
    seven = text.replace(SIX_PERIODS, young).replace("inter_connectors:\n  - {disc.a: k}\n", pairs)
    trellis_file.write_text(seven, encoding="utf-8")
    shutil.copyfile(root / PORTFOLIO_PERIOD, root / "declaration/period.young.yml")
    recipe_file = root / RECIPE_FILE
    recipe_text = (
        recipe_file.read_text(encoding="utf-8")
        .replace(
            "methods: {all: [stages/port/methods.bl]}}",
            "methods: {all: [stages/port/methods.bl]}, periods: [0, 6]}",
        )
        .replace(
            "cons: {stage: stages/cons/cons.bl, calibration: {all: [calibration/portfolio]}",
            "cons: {stage: stages/cons/cons.bl, calibration: {all: [calibration/portfolio], "
            '"0-5": [calibration/portfolio], '
            '"6-6": [calibration/portfolio]}',
        )
    )
    recipe_file.write_text(recipe_text, encoding="utf-8")
    removed = creation.remove_period(root, 6)
    without = text.replace("inter_connectors:\n  - {disc.a: k}\n", pairs)
    without = without.replace("  - {disc.a: k}  # pair 5\n", "")
    assert removed.edits[str(trellis_file.resolve())] == without
    made = removed.edits[str(recipe_file.resolve())]
    assert entry_value(made, "stages.port.periods") == [0, 5]
    assert list(entry_value(made, "stages.cons.calibration")) == ["all", "0-5"]
    assert removed.notes == (
        "trellis.yml, periods[1] removed, periods 6",
        "trellis.yml, inter_connectors[5] removed",
        "spec.yml, stages.port.periods: [0, 6] now [0, 5]",
        "stages.cons.calibration: 6-6 removed",
        "deleted on save: period.young.yml",
        "restriction emptied",
    )
    assert removed.deleted == ("declaration/period.young.yml",)
    load_recipe(root / "declaration", "spec.yml", removed.edits)
    assert (root / "declaration/period.young.yml").is_file()

    # period.yml, which the other entry names, is never listed
    trellis_file.write_text(seven.replace("period.young.yml", "period.yml"), encoding="utf-8")
    assert creation.remove_period(root, 6).deleted == ()

    with pytest.raises(ValueError, match="writes no period 9"):
        creation.remove_period(root, 9)
    trellis_file.write_text(text.replace("repeat: 6}", "repeat: 1}"), encoding="utf-8")
    with pytest.raises(ValueError, match="a trellis holds one period or more"):
        creation.remove_period(root, 0)


def test_l_25_the_tree_offers_the_period_files_and_stage_folders_nothing_names(
    scratch_folder, scratch_durables
):
    """Unit L, Task 25 (AAS, L-D18): `removable_files` offers the portfolio
    model's stage folders `stages/cons_obs/` and `stages/noport/`, which no
    row names, and no folder or period file a recipe or a trellis file
    names; `stages/port/` once neither the recipe's unsaved text nor its
    text on disk names it, the disk's text naming it until then
    (`deletable`). The durables model's unreferenced disc and retiree_saving
    stage folders are offered; period.two-stages.yml is offered only after
    the variant's recipe and trellis file are gone."""
    root = scratch_folder
    held = ("declaration/stages/cons_obs", "declaration/stages/noport")
    assert creation.removable_files(root) == held
    recipe_file = root / RECIPE_FILE
    without_port = recipe_file.read_text(encoding="utf-8").replace(PORT_ROW, "")
    unsaved = {str(recipe_file.resolve()): without_port}
    assert creation.removable_files(root, unsaved) == held
    assert creation.deletable(root, ["declaration/stages/port"], unsaved) == ()
    recipe_file.write_text(unsaved[str(recipe_file.resolve())], encoding="utf-8")
    assert creation.removable_files(root) == (
        "declaration/stages/cons_obs",
        "declaration/stages/noport",
        "declaration/stages/port",
    )
    named = ["declaration/stages/port", "declaration/period.yml"]
    assert creation.deletion_names(root, named) == ["stages/port/", "period.yml"]

    unnamed = ("declaration/stages/disc", "declaration/stages/retiree_saving")
    assert creation.removable_files(scratch_durables) == unnamed
    for name in ("spec.two-stages.yml", "trellis.two-stages.yml"):
        (scratch_durables / "declaration" / name).unlink()
    assert creation.removable_files(scratch_durables) == ("declaration/period.two-stages.yml", *unnamed)


def test_l_25_a_file_outside_the_model_folder_is_never_listed_or_deleted(scratch_folder):
    """Unit L, Task 25 (L-I360): where port's row names
    its addition through `../`, `other/methods.bl` beside the model folder,
    `remove_stage` of `port` lists the stage's folder and
    `settings/port.yml` and not that file, and once the edits stand on disk
    `deletable` answers the stage's folder and refuses that file; where the
    trellis file's earliest entry names a period file beside the model
    folder through `../`, `remove_period` of that period lists nothing, and
    once its edits stand on disk `deletable` refuses that file. The files
    outside the folder stand throughout."""
    root = scratch_folder
    other = root.parent / "other"
    other.mkdir()
    shutil.copyfile(root / "declaration/stages/port/methods.bl", other / "methods.bl")
    recipe_file = root / RECIPE_FILE
    recipe_file.write_text(
        recipe_file.read_text(encoding="utf-8").replace(
            "[stages/port/methods.bl]}}", "[../../other/methods.bl]}}"
        ),
        encoding="utf-8",
    )
    removed = creation.remove_stage(root, "port")
    assert removed.deleted == ("declaration/stages/port", "declaration/settings/port.yml")
    assert removed.notes[-1] == "deleted on save: stages/port/, settings/port.yml"
    for path, text in removed.edits.items():
        Path(path).write_text(text, encoding="utf-8")
    listed = ["../other/methods.bl", "declaration/stages/port"]
    assert creation.deletable(root, listed) == ("declaration/stages/port",)
    assert (other / "methods.bl").is_file()

    trellis_file = root / "declaration" / creation.TRELLIS
    shutil.copyfile(root / PORTFOLIO_PERIOD, other / "period.yml")
    trellis_file.write_text(
        trellis_file.read_text(encoding="utf-8").replace(
            SIX_PERIODS, SIX_PERIODS + "  - {template: ../../other/period.yml, repeat: 1}\n"
        ),
        encoding="utf-8",
    )
    lowered = creation.remove_period(root, 6)
    assert lowered.deleted == ()
    assert not any(note.startswith("deleted on save") for note in lowered.notes)
    for path, text in lowered.edits.items():
        Path(path).write_text(text, encoding="utf-8")
    assert creation.deletable(root, ["../other/period.yml"]) == ()
    assert (other / "period.yml").is_file()


def test_new_stage_refuses_a_period_file_whose_stage_list_is_overridden(scratch_folder):
    trellis = scratch_folder / "declaration/trellis.yml"
    before = trellis.read_text()
    trellis.write_text(
        before.replace(
            "template: period.yml, repeat: 6",
            "template: period.yml, repeat: 6, stages: [port, cons, disc]",
        )
    )
    assert len(load_recipe(scratch_folder / "declaration", "spec.yml")["periods"]) == 6
    saved = file_bytes(scratch_folder)
    with pytest.raises(ValueError, match="no period .* uses the stages list from period.yml"):
        creation.new_stage(scratch_folder, "new_choice", period_file="period.yml")
    assert file_bytes(scratch_folder) == saved

    trellis.write_text(trellis.read_text().replace(
        "inter_connectors:",
        "  - {template: period.yml}\ninter_connectors:",
    ))
    added = creation.new_stage(scratch_folder, "new_choice", period_file="period.yml")
    period = str((scratch_folder / "declaration/period.yml").resolve())
    assert "- new_choice" in added.edits[period]
