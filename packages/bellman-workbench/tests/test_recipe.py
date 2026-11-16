"""The recipe and the bindings of a model folder (`bellman_workbench.recipe`;
model interface specification 0.3, §2.2 rule 1, §3.2 and §3.3), on the
temporary copies of the corpus folders and the lifecycle registry of
`workbench_support`."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from workbench_support import (
    CONS,
    DEMO_STAGES,
    DISC,
    PENSIONS_RECIPE,
    PENSIONS_WORKING_YEARS,
    RECIPE_FILE,
    ROOT,
    TENURE,
    WORKER_SAVING,
    filled,
    pensions_copy,
    repository_copy,
    tree_entries,
    unsaved_of,
)

from bellman.stage import admitted_methods, elaborate_text
from bellman.trellis import load_recipe
from bellman_workbench import creation, model, recipe, trellis

# the recipe of a folder in the one layout, as the source of its trellis
RECIPE = recipe.Source("recipe", RECIPE_FILE)


def test_the_sources_of_a_folders_trellis(
    model_folder, pension_folder, consport_folder, cagetti_folder, lifecycle_folder, tmp_path
):
    """A folder with a recipe offers its recipe alone, and a click on the
    trellis file it reads shows the recipe's trellis; a folder with none
    offers its YAML files tagged `!trellis`, nearest the top first, as the
    eight trellis files of cons-port's `declaration/`; a folder with neither
    offers nothing (decision B-D5), as cagetti's does. In each folder the recipes offered are
    the files of its `declaration/` to which the tree gives the role
    `recipe`, where the one layout of a model folder places them. The
    portfolio model's folder holds its recipe since 4 October 2026, and
    `buffer-stock` holds neither."""
    open_folder = model.open_folder
    assert recipe.model_sources(open_folder(model_folder)) == [RECIPE]
    neither = repository_copy(ROOT / "applications/buffer-stock", tmp_path / "buffer-stock")
    assert recipe.model_sources(open_folder(neither)) == []
    pension = open_folder(pension_folder)
    assert recipe.model_sources(pension) == [RECIPE]
    assert recipe.model_sources(open_folder(lifecycle_folder)) == [RECIPE]
    # cons-port holds the two recipes of its two orders since 28 October 2026,
    # so its trellis files of records are not offered
    assert recipe.model_sources(open_folder(consport_folder)) == [
        recipe.Source("recipe", f"declaration/spec.{name}.yml")
        for name in ("cons-port", "port-cons")
    ]
    assert recipe.model_sources(open_folder(cagetti_folder)) == [
        recipe.Source("trellis", "declaration/trellis.yml")
    ]
    assert recipe.trellis_file(pension, RECIPE) == "declaration/trellis.yml"
    assert recipe.source_of(pension, "declaration/trellis.yml") == RECIPE
    assert recipe.source_of(pension, WORKER_SAVING) is None
    for root in (model_folder, pension_folder, consport_folder, cagetti_folder, lifecycle_folder):
        folder = open_folder(root)
        declared = [
            path
            for path, entry in tree_entries(model.folder_tree(folder)).items()
            if entry["kind"] == "file"
            and entry["role"] == "recipe"
            and Path(path).parent.as_posix() == "declaration"
        ]
        offered = recipe.model_sources(folder)
        assert [source.path for source in offered if source.kind == "recipe"] == declared


def test_spec_yml_is_offered_before_its_variants_in_name_order(scratch_lifecycle, tmp_path):
    """A folder that holds variants of its recipe, `spec.<name>.yml`, beside
    `spec.yml` in its `declaration/` offers `declaration/spec.yml` first and
    the variants after it in name order, so that the window opens on
    `declaration/spec.yml`, and the package reads each recipe as its own
    file, in its own folder; a recipe written at the folder's top beside
    them is not offered, the Workbench reading a folder's recipes in
    `declaration/` alone (the page Model directory layout), and nothing is
    noted of it when a stage file is read with the recipe shown or with no
    source, since `declaration/spec.yml` stands; a copy of the durables
    model offers `declaration/spec.yml` before
    `declaration/spec.two-stages.yml` (AAS, 2 October 2026: a folder may
    hold several recipes)."""
    text = (scratch_lifecycle / "declaration/spec.yml").read_text(encoding="utf-8")
    for name in ("spec.short.yml", "spec.a.yml"):
        (scratch_lifecycle / "declaration" / name).write_text(text, encoding="utf-8")
    folder = model.open_folder(scratch_lifecycle)
    offered = recipe.model_sources(folder)
    assert offered == [
        RECIPE,
        recipe.Source("recipe", "declaration/spec.a.yml"),
        recipe.Source("recipe", "declaration/spec.short.yml"),
    ]
    for source in offered:
        read = recipe.read_source(folder, source)
        assert recipe.relative(folder, read["provenance"]["recipe"]["path"]) == source.path
    (scratch_lifecycle / "spec.yml").write_text(text, encoding="utf-8")
    assert recipe.model_sources(folder) == offered
    assert recipe.find_occurrence(folder, RECIPE, CONS).notes == []
    assert recipe.find_occurrence(folder, None, CONS) == recipe.Found(None, None, None, CONS, [])
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    assert recipe.model_sources(model.open_folder(durables)) == [
        recipe.Source("recipe", "declaration/spec.yml"),
        recipe.Source("recipe", "declaration/spec.two-stages.yml"),
    ]


def test_a_buffer_is_bound_as_the_occurrence_wanted_with_the_origin_its_record_writes(
    lifecycle_folder,
):
    """`declaration/stages/disc/disc.bl` of the lifecycle registry is bound
    as the occurrence the head names, `periods[1] / disc` at β = 0.96 and
    `periods[0] / disc` at the terminal period's β = 0.9, elaborated with the
    origin `load_recipe` writes; an occurrence of another file is not taken,
    the file's first being bound; the discount stage's settings slot, which
    no keyword binds, is skipped with no note, a verb skipped being no
    refusal (unit L, Task 21; K-D29); the consumption stage is bound by its
    calibration, its settings and its addition with no note, and the files
    watched with the recipe and its trellis file are those three."""
    folder = model.open_folder(lifecycle_folder)
    found = recipe.find_occurrence(folder, RECIPE, DISC, (1, "disc"))
    assert found.position == (1, "disc") and found.origin == str(folder.root / DISC)
    stage = elaborate_text(Path(found.origin).read_text(encoding="utf-8"), found.origin)
    late = recipe.bind_occurrence(stage, found)
    assert late.occurrence == "periods[1] / disc" and late.stage.par["β"].value == 0.96
    terminal = recipe.find_occurrence(folder, RECIPE, DISC, (0, "disc"))
    assert recipe.bind_occurrence(stage, terminal).stage.par["β"].value == 0.9
    assert recipe.find_occurrence(folder, RECIPE, DISC, (1, "cons")).position == (0, "disc")
    cons = recipe.find_occurrence(folder, RECIPE, CONS)
    text = Path(cons.origin).read_text(encoding="utf-8")
    bound = recipe.bind_occurrence(elaborate_text(text, cons.origin), cons)
    assert bound.notes == []
    assert [recipe.relative(folder, path) for path in recipe.watched_files(folder, cons)] == [
        "declaration/spec.yml",
        "declaration/trellis.yml",
        "declaration/calibration/portfolio.yml",
        "declaration/settings/cons.yml",
        "declaration/stages/cons/methods.bl",
    ]


def test_a_file_no_source_holds_and_a_folder_without_a_source(model_folder, pension_folder, cons):
    """A stage file the recipe holds no occurrence of is answered as it is
    with one note and its path as its origin; without a source, no note, no
    occurrence and no watched file."""
    pension = model.open_folder(pension_folder)
    absent = "declaration/stages/none/none.bl"
    none = recipe.find_occurrence(pension, RECIPE, absent)
    assert none.origin == absent
    assert none.notes == [f"declaration/spec.yml holds no occurrence of {absent}"]
    assert recipe.bind_occurrence(cons, none) == (
        cons,
        None,
        None,
        [f"declaration/spec.yml holds no occurrence of {absent}"],
        None,
        (),
    )
    alone = recipe.find_occurrence(model.open_folder(model_folder), None, CONS)
    assert alone == recipe.Found(None, None, None, CONS, [])
    assert recipe.watched_files(model.open_folder(model_folder), alone) == []


def test_a_folder_whose_recipe_stands_at_its_top_offers_no_source_and_says_why(
    pension_folder, tmp_path
):
    """A folder in the earlier flat layout holds its recipe spec.yml at its
    top, beside the trellis and period files, and its stage files at
    stages/<key>.bl, as "new trellis" wrote a folder before the layout of 2
    October 2026; it holds no declaration/spec.yml. The pension model written
    back into that layout reads through `load_recipe` at its top, yet the
    folder offers no source of a trellis: not its recipe, since the
    Workbench reads a folder's recipe at declaration/spec.yml alone, and not
    its trellis file either. A buffer of its stage file is bound as no
    occurrence, the stage unchanged and bound by no file, nothing watched,
    with one note, which says where the recipe stands and where the
    Workbench reads a recipe; the folder, which is no model's
    `declaration/`, has no model folder above it to open (ruling R63 of the
    model folder's layout; the claims of the layout's test of
    `apply_bindings`, a function unit B deleted; unit L, Task 28, L-D23)."""
    copy = tmp_path / "pension-retirement"
    shutil.copytree(pension_folder / "declaration", copy)
    written = (copy / "spec.yml").read_text(encoding="utf-8")
    for held in sorted((copy / "stages").iterdir()):
        (held / f"{held.name}.bl").rename(copy / "stages" / f"{held.name}.bl")
        # each stage's addition stands beside its stage file, as
        # `stages/<key>_methods.bl` (decision MB-V38; specification 0.7)
        (held / "methods.bl").rename(copy / "stages" / f"{held.name}_methods.bl")
        shutil.rmtree(held)
        written = written.replace(f"stages/{held.name}/{held.name}.bl", f"stages/{held.name}.bl")
        written = written.replace(
            f"stages/{held.name}/methods.bl", f"stages/{held.name}_methods.bl"
        )
    (copy / "spec.yml").write_text(written, encoding="utf-8")
    assert len(load_recipe(copy, "spec.yml")["periods"]) == 15
    folder = model.open_folder(copy)
    assert recipe.model_sources(folder) == []
    assert recipe.model_of_declaration(folder) is None
    path = "stages/worker_saving.bl"
    found = recipe.find_occurrence(folder, None, path)
    assert found == recipe.Found(
        None,
        None,
        None,
        path,
        [
            "spec.yml stands at the folder's top, not at declaration/spec.yml; "
            "the Workbench reads a recipe at declaration/spec.yml"
        ],
    )
    text = (copy / path).read_text(encoding="utf-8")
    stage = elaborate_text(text, path)
    bound = recipe.bind_occurrence(stage, found)
    assert bound.stage is stage and bound.occurrence is None and bound.notes == found.notes
    assert set(model.input_digests(bound.stage, text)) == {"text"}
    assert recipe.watched_files(folder, found) == []


def test_a_models_declaration_opened_by_itself_names_the_model_folder_to_open(
    model_folder, tmp_path
):
    """A model's `declaration/` opened by itself, as AAS opened
    `applications/portfolio-choice/declaration` in the desktop application,
    holds the recipe spec.yml at its top and offers no source of a trellis.
    A buffer of its stage file is bound as no occurrence with one note,
    which names the model folder above and says to open it, `this folder is
    the declaration/ of portfolio-choice; open portfolio-choice`; that
    folder, which `model_of_declaration` answers, offers the recipe at
    `declaration/spec.yml` (unit L, Task 28; AAS, L-D23). The model folder
    itself, and a folder named `declaration` that holds no recipe at its
    top, have no model folder above them to open."""
    declaration = model.open_folder(model_folder / "declaration")
    assert recipe.model_sources(declaration) == []
    path = "stages/cons/cons.bl"
    assert recipe.find_occurrence(declaration, None, path) == recipe.Found(
        None,
        None,
        None,
        path,
        ["this folder is the declaration/ of portfolio-choice; open portfolio-choice"],
    )
    above = recipe.model_of_declaration(declaration)
    assert above == model_folder.resolve()
    assert recipe.model_sources(model.open_folder(above)) == [RECIPE]
    assert recipe.model_of_declaration(model.open_folder(model_folder)) is None
    (tmp_path / "declaration").mkdir()
    empty = model.open_folder(tmp_path / "declaration")
    assert recipe.model_of_declaration(empty) is None
    assert recipe.find_occurrence(empty, None, path).notes == []


def test_the_workbench_binds_a_stage_of_a_new_folder_as_its_recipes_occurrence(repository):
    """Opened on a folder "new trellis" wrote, with the slots of the
    consumption stage filled, the Workbench offers the recipe the folder
    holds in `declaration/` and binds `declaration/stages/cons/cons.bl` as
    the occurrence `periods[0] / cons`: calibrated, methodized and
    configured by the files the recipe names, which are its binding sources
    and are watched with the recipe and its trellis file, with no note; its
    origin is the one `load_recipe` writes (spec 0.3 §2.2 rule 1; merge note
    M8 of unit C; the claims of the layout's test of `apply_bindings`, a
    function unit B deleted)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    recipe_file = created.folder / creation.factory_path(creation.RECIPE)
    recipe_file.write_text(filled(recipe_file.read_text(encoding="utf-8")), encoding="utf-8")
    folder = model.open_folder(created.folder)
    sources = recipe.model_sources(folder)
    assert sources == [recipe.Source("recipe", "declaration/spec.yml")]
    found = recipe.find_occurrence(folder, sources[0], CONS)
    assert found.origin == str(created.folder / CONS)
    text = (created.folder / CONS).read_text(encoding="utf-8")
    stage = elaborate_text(text, found.origin)
    bound = recipe.bind_occurrence(stage, found)
    assert (bound.occurrence, bound.notes) == ("periods[0] / cons", [])
    assert bound.stage is not stage
    assert set(model.input_digests(bound.stage, text)) == {
        "text",
        "calibration",
        "methods",
        "settings",
    }
    declaration = created.folder / "declaration"
    assert recipe.record_files(found.record) == [
        declaration / "calibration/portfolio.yml",
        declaration / "settings/cons_wide.yml",
        declaration / "stages/cons/methods.bl",
    ]
    assert [recipe.relative(folder, path) for path in recipe.watched_files(folder, found)] == [
        "declaration/spec.yml",
        "declaration/trellis.yml",
        "declaration/calibration/portfolio.yml",
        "declaration/settings/cons_wide.yml",
        "declaration/stages/cons/methods.bl",
    ]


def test_the_pension_stage_file_is_bound_as_its_first_occurrence_with_the_calibration_skipped(
    pension_folder, tmp_path
):
    """On the pension registry, whose recipe binds the worker's calibration
    through a slot that no keyword binds, its methods through its addition
    and its settings through `settings/worker_saving.yml`,
    `declaration/stages/worker_saving/worker_saving.bl` is bound as
    `periods[0] / worker_saving`, elaborated with the origin `load_recipe`
    writes: the stage is answered methodized by its addition and configured
    by its settings file and not calibrated, with no note, since a verb
    skipped is no refusal (unit L, Task 21; K-D29), and the files watched
    are the recipe, its trellis file, the settings file and the addition,
    the binding source files the recipe names for the stage (decision
    S7-W2). On a copy whose trellis
    file is `declaration/pension.yml`, which the recipe names under its key
    `trellis:`, the file is bound as the same occurrence and `pension.yml` is
    watched in place of `trellis.yml`."""
    stage_file = WORKER_SAVING
    copy = shutil.copytree(pension_folder, tmp_path / "pension-retirement")
    (copy / "declaration/trellis.yml").rename(copy / "declaration/pension.yml")
    text = (copy / "declaration/spec.yml").read_text(encoding="utf-8")
    assert text.count("\ntrellis: trellis.yml\n") == 1
    (copy / "declaration/spec.yml").write_text(
        text.replace("\ntrellis: trellis.yml\n", "\ntrellis: pension.yml\n"), encoding="utf-8"
    )
    for root, trellis_name in ((pension_folder, "trellis.yml"), (copy, "pension.yml")):
        folder = model.open_folder(root)
        found = recipe.find_occurrence(folder, RECIPE, stage_file)
        assert found.position == (0, "worker_saving") and found.notes == []
        assert found.origin == str(root.resolve() / stage_file)
        stage = elaborate_text(Path(found.origin).read_text(encoding="utf-8"), found.origin)
        bound = recipe.bind_occurrence(stage, found)
        assert bound.occurrence == "periods[0] / worker_saving"
        assert bound.stage is not stage and bound.stage.bindings.calibration is None
        assert bound.stage.bindings.settings is not None and bound.stage.methods
        assert bound.notes == []
        assert recipe.watched_files(folder, found) == [
            root.resolve() / "declaration/spec.yml",
            root.resolve() / "declaration" / trellis_name,
            root.resolve() / "declaration/settings/worker_saving.yml",
            root.resolve() / "declaration/stages/worker_saving/methods.bl",
        ]


def test_a_recipes_trellis_file_is_the_file_the_package_reads(scratch_lifecycle):
    """A recipe that names its trellis file without the extension,
    `trellis: lifecycle`, reads `lifecycle.yml`, as the package's reader
    finds a registry name: that file is the recipe's trellis file, a click on
    it shows the recipe, and the files the trellis reads hold it and the
    period file it names."""
    declaration = scratch_lifecycle / "declaration"
    (declaration / "trellis.yml").rename(declaration / "lifecycle.yml")
    recipe_file = declaration / "spec.yml"
    recipe_file.write_text(
        recipe_file.read_text(encoding="utf-8").replace(
            "trellis: trellis.yml", "trellis: lifecycle"
        ),
        encoding="utf-8",
    )
    folder = model.open_folder(scratch_lifecycle)
    assert recipe.trellis_file(folder, RECIPE) == "declaration/lifecycle.yml"
    assert recipe.source_of(folder, "declaration/lifecycle.yml") == RECIPE
    files = trellis.files_read(folder, RECIPE, recipe.read_source(folder, RECIPE))
    read = {recipe.relative(folder, path) for path in files}
    assert {"declaration/spec.yml", "declaration/lifecycle.yml", "declaration/period.yml"} <= read


def test_a_recipe_that_names_no_trellis_file_is_refused_and_none_is_assumed(
    scratch_lifecycle,
):
    """A recipe whose line `trellis: trellis.yml` is removed names no trellis
    file, which the package refuses under `recipe-shape` (AAS, 2 October
    2026: a recipe names every file it reads), and the Workbench assumes no
    `trellis.yml` in its place: the reading answers the refusal and raises
    nothing; the recipe has no trellis file; the files whose change reads the
    recipe again, refused or bound to an open stage file, are the recipe
    alone; the stage file's one note is the package's whole sentence, its
    message and, on a line of its own, the words it says to write, the
    refusal the trellis's reading holds (ruling R51); a click on
    `trellis.yml` shows no source; and the table shows no trellis file."""
    recipe_file = scratch_lifecycle / "declaration/spec.yml"
    text = recipe_file.read_text(encoding="utf-8")
    assert text.count("\ntrellis: trellis.yml\n") == 1
    recipe_file.write_text(text.replace("\ntrellis: trellis.yml\n", "\n"), encoding="utf-8")
    folder = model.open_folder(scratch_lifecycle)
    outcome = trellis.show_trellis(folder, RECIPE)
    assert outcome.shown is None
    assert (outcome.refusal.rule, outcome.refusal.address) == ("recipe-shape", "trellis")
    assert recipe.trellis_file(folder, RECIPE) is None
    files = trellis.files_of_refusal(folder, RECIPE, outcome.refusal)
    assert [recipe.relative(folder, path) for path in files] == ["declaration/spec.yml"]
    found = recipe.find_occurrence(folder, RECIPE, CONS)
    assert found.position is None and found.refusal == outcome.refusal
    assert found.notes == [
        "the recipe names no trellis file\n`trellis: trellis.yml`, the path from this folder"
    ]
    assert found.notes == [model.sentence(outcome.refusal)]
    watched = recipe.watched_files(folder, found)
    assert [recipe.relative(folder, path) for path in watched] == ["declaration/spec.yml"]
    assert recipe.source_of(folder, "declaration/trellis.yml") is None
    assert recipe.trellis_entry(folder, RECIPE) is None


def test_the_recipe_as_a_table_at_the_heads_period(lifecycle_folder):
    """The lifecycle recipe as a table (specification §3.2): one row per stage
    in the file's order; the consumption stage's methods cell holds its
    addition, `stages/cons/methods.bl`, and the discount stage's settings
    cell the slot `$disc_settings`; the discount stage's calibration holds, at the
    terminal period, the `all` source and the range `0-0`'s, and at
    `periods[1]` the `all` source alone, its opened lists both, each entry at
    its address in the recipe."""
    folder = model.open_folder(lifecycle_folder)
    syntactic = recipe.read_source(folder, RECIPE)
    rows = recipe.table(folder, RECIPE, syntactic, 0)
    assert [(row.key, row.active) for row in rows] == [
        ("port", True),
        ("cons", True),
        ("disc", True),
    ]
    (addition,) = rows[1].cells["methods"].entries
    assert addition == recipe.Entry(
        "stages/cons/methods.bl", False, "declaration/spec.yml", "stages.cons.methods.all[0]", None
    )
    (slot,) = rows[2].cells["settings"].entries
    assert slot == recipe.Entry(
        "$disc_settings", True, "declaration/spec.yml", "stages.disc.settings.all[0]", None
    )
    disc = rows[2].cells["calibration"]
    assert [entry.text for entry in disc.entries] == [
        "calibration/portfolio",
        "calibration/terminal",
    ]
    assert {
        name: [entry.address for entry in entries] for name, entries in disc.lists.items()
    } == {
        "all": ["stages.disc.calibration.all[0]"],
        "0-0": ["stages.disc.calibration.0-0[0]"],
    }
    later = recipe.table(folder, RECIPE, syntactic, 1)
    assert [entry.text for entry in later[2].cells["calibration"].entries] == [
        "calibration/portfolio"
    ]


def test_each_list_of_a_binding_is_a_line_with_the_periods_it_holds_for(lifecycle_folder):
    """The lifecycle recipe as a table (unit L, Task 11; AAS, L-D10): each
    kind's cell holds one line per list the recipe writes for the stage, in
    the file's order, each with its entries and the periods it holds for as
    the block prints them, `all` for the list `all` and `periods 0–0` for
    the range `0-0`; the range line is marked at the head's period, which
    it holds at `periods[0]` and not at `periods[1]`, and the line `all` is
    never marked."""
    folder = model.open_folder(lifecycle_folder)
    syntactic = recipe.read_source(folder, RECIPE)
    rows = recipe.table(folder, RECIPE, syntactic, 0)
    disc = rows[2].cells["calibration"]
    portfolio, terminal = disc.lists["all"] + disc.lists["0-0"]
    assert disc.lines == (
        recipe.BindingLine("all", "all", (portfolio,), False),
        recipe.BindingLine("0-0", "periods 0–0", (terminal,), True),
    )
    later = recipe.table(folder, RECIPE, syntactic, 1)[2].cells["calibration"]
    assert [(line.holds_for, line.at_head) for line in later.lines] == [
        ("all", False),
        ("periods 0–0", False),
    ]
    (addition,) = rows[1].cells["methods"].lines
    assert addition == recipe.BindingLine("all", "all", rows[1].cells["methods"].entries, False)
    (slot,) = rows[2].cells["settings"].lines
    assert slot == recipe.BindingLine("all", "all", rows[2].cells["settings"].entries, False)


def test_the_table_of_a_trellis_file_holds_each_records_one_value(consport_folder):
    """A trellis file whose records name their sources (decision B-D5): one
    row per stage of the head's period, each cell the one value the record
    writes, at its address in the trellis file, the entry repeated for every
    period; a mapping written in place reads `{}`."""
    folder = model.open_folder(consport_folder)
    source = recipe.Source("trellis", "declaration/trellis.port-cons-vfi.yml")
    rows = recipe.table(folder, source, recipe.read_source(folder, source), 2)
    assert [row.key for row in rows] == ["port", "cons", "disc"]
    assert rows[1].cells["methods"].entries == (
        recipe.Entry(
            "stages/cons/methods.vfi.bl",
            False,
            "declaration/trellis.port-cons-vfi.yml",
            "periods[0].stages.cons.methods",
            None,
        ),
    )
    assert rows[2].cells["settings"].entries[0].text == "{}"
    # the record's one value is one line, which holds for no range the
    # recipe writes (unit L, Task 11)
    assert rows[1].cells["methods"].lines == (
        recipe.BindingLine(None, "", rows[1].cells["methods"].entries, False),
    )


def test_the_files_a_cell_may_take(lifecycle_folder):
    """The additions of the folder's `declaration/`, each beside its stage
    file, `methods.bl` and the replacing selection `methods.vfi.bl` of the
    consumption stage (decision S7-W2), each with its first comment line and
    nothing else, since the Workbench reads nothing of an addition beyond
    its first line (decision S7-W1); a kind that is none is an empty
    listing."""
    folder = model.open_folder(lifecycle_folder)
    found = recipe.choices(folder, "methods")
    assert [choice.path for choice in found] == [
        "declaration/stages/cons/methods.bl",
        "declaration/stages/cons/methods.vfi.bl",
        "declaration/stages/disc/methods.bl",
        "declaration/stages/port/methods.bl",
    ]
    assert found[0] == recipe.Choice(
        "declaration/stages/cons/methods.bl",
        "The methods of the consumption stage as an addition to",
        None,
    )
    assert found[1].comment.startswith("Value function iteration on the decision value builder")
    assert recipe.choices(folder, "nothing") == []

def test_a_choice_replaces_one_entry_keeping_the_comments_and_the_other_entries(
    scratch_lifecycle, scratch_consport
):
    """Choosing `declaration/stages/cons/methods.vfi.bl` for the entry of
    the consumption stage's methods answers the recipe's text with
    `stages/cons/methods.vfi.bl` in its place, the file's path from the
    recipe's folder with its extension, as an addition is named, and no
    other character changed, its comments kept, and writes nothing to disk,
    the Workbench applying the text to the recipe's buffer (AAS, M-D17;
    design pass 9 §4); a stage file and the trellis file are written with
    their extension, and a slot as it is; in a trellis file, the record's
    value takes the file's path relative to the trellis file (specification
    §3.2)."""
    folder = model.open_folder(scratch_lifecycle)
    recipe_file = scratch_lifecycle / "declaration/spec.yml"
    before = recipe_file.read_text(encoding="utf-8")
    rows = recipe.table(folder, RECIPE, recipe.read_source(folder, RECIPE), 1)
    (addition,) = rows[1].cells["methods"].entries
    assert (
        recipe.written_name(folder, RECIPE, addition, "declaration/stages/disc/methods.bl")
        == "stages/disc/methods.bl"
    )
    assert (
        recipe.written_name(folder, RECIPE, rows[0].stage, "declaration/stages/disc/disc.bl")
        == "stages/disc/disc.bl"
    )
    trellis_entry = recipe.trellis_entry(folder, RECIPE)
    assert recipe.written_name(folder, RECIPE, trellis_entry, "declaration/trellis.yml") == (
        "trellis.yml"
    )
    written = recipe.choose(folder, RECIPE, addition, "declaration/stages/cons/methods.vfi.bl", before)
    assert written == before.replace("stages/cons/methods.bl", "stages/cons/methods.vfi.bl")
    assert recipe_file.read_text(encoding="utf-8") == before
    (portfolio,) = rows[0].cells["calibration"].entries
    assert recipe.choose(folder, RECIPE, portfolio, "$fill", before) == before.replace(
        "calibration: {all: [calibration/portfolio]}, methods: {all: [stages/port/methods.bl]}",
        "calibration: {all: [$fill]}, methods: {all: [stages/port/methods.bl]}",
    )
    consport = model.open_folder(scratch_consport)
    source = recipe.Source("trellis", "declaration/trellis.port-cons-vfi.yml")
    entry = (
        recipe.table(consport, source, recipe.read_source(consport, source), 0)[1]
        .cells["methods"]
        .entries[0]
    )
    assert (
        recipe.written_name(consport, source, entry, "declaration/stages/cons/methods.bl")
        == "stages/cons/methods.bl"
    )
    text = (scratch_consport / source.path).read_text(encoding="utf-8")
    assert recipe.choose(consport, source, entry, "declaration/stages/cons/methods.bl", text) == (
        text.replace("methods: stages/cons/methods.vfi.bl", "methods: stages/cons/methods.bl")
    )


def test_the_trellis_file_and_the_stage_files_are_answered_as_written(
    lifecycle_folder, pension_folder, consport_folder
):
    """A recipe names every file it reads by a path relative to its own
    folder (AAS, 2 October 2026), and the table answers each as the file
    writes it: the `trellis: trellis.yml` of the lifecycle recipe and of
    the pension recipe at the address `trellis`; nothing for a trellis
    file, which is its own trellis file; for each stage of the lifecycle
    recipe, the stage file its entry writes, `stage:
    stages/<key>/<key>.bl`, at the address `stages.<key>.stage`; and for
    each record of a trellis file, its `stage` as the file writes it."""
    folder = model.open_folder(lifecycle_folder)
    assert recipe.trellis_entry(folder, RECIPE) == recipe.Entry(
        "trellis.yml", False, "declaration/spec.yml", "trellis", None
    )
    assert recipe.trellis_entry(model.open_folder(pension_folder), RECIPE) == recipe.Entry(
        "trellis.yml", False, "declaration/spec.yml", "trellis", None
    )
    consport = model.open_folder(consport_folder)
    source = recipe.Source("trellis", "declaration/trellis.port-cons-vfi.yml")
    assert recipe.trellis_entry(consport, source) is None
    rows = recipe.table(folder, RECIPE, recipe.read_source(folder, RECIPE), 0)
    assert [row.stage for row in rows] == [
        recipe.Entry(
            f"stages/{key}/{key}.bl", False, "declaration/spec.yml", f"stages.{key}.stage", None
        )
        for key in ("port", "cons", "disc")
    ]
    rows = recipe.table(consport, source, recipe.read_source(consport, source), 2)
    # the trellis file names the demonstration's consumption stage file
    # since decision SD-39
    assert [row.stage for row in rows] == [
        recipe.Entry(
            f"stages/{key}/{key}.bl",
            False,
            "declaration/trellis.port-cons-vfi.yml",
            f"periods[0].stages.{key}.stage",
            None,
        )
        for key in ("port", "cons", "disc")
    ]


def test_a_choice_is_refused_where_the_text_no_longer_writes_the_entry(scratch_lifecycle):
    """An entry of a table read before its text changed takes no file: where
    the text writes another entry at the entry's address, or none, the
    choice is refused in one sentence and no text is answered, so that no
    entry the table did not show is replaced (specification §3.2; design
    pass 9 §4)."""
    folder = model.open_folder(scratch_lifecycle)
    (addition,) = (
        recipe.table(folder, RECIPE, recipe.read_source(folder, RECIPE), 0)[1]
        .cells["methods"]
        .entries
    )
    original = (scratch_lifecycle / "declaration/spec.yml").read_text(encoding="utf-8")
    sentence = "the file no longer writes stages/cons/methods.bl at stages.cons.methods.all[0]"
    for written in ("stages/cons/methods.vfi.bl", ""):
        changed = original.replace("stages/cons/methods.bl", written)
        with pytest.raises(ValueError) as refused:
            recipe.choose(
                folder, RECIPE, addition, "declaration/stages/cons/methods.vfi.bl", changed
            )
        assert str(refused.value) == sentence


def test_the_table_of_a_recipe_that_no_longer_reads_is_total(scratch_lifecycle):
    """The table and the trellis file are total (specification §2.2 rule 4): a
    recipe that no longer reads as YAML gives no rows and no trellis file; a
    stage written as a list, `cons: [stages/cons/methods.bl]`, a shape the
    factory refuses, reads as a stage that writes nothing, its row kept with
    every cell empty."""
    folder = model.open_folder(scratch_lifecycle)
    syntactic = recipe.read_source(folder, RECIPE)
    recipe_file = scratch_lifecycle / "declaration/spec.yml"
    original = recipe_file.read_text(encoding="utf-8")
    recipe_file.write_text(original + "  broken: [\n", encoding="utf-8")
    assert recipe.table(folder, RECIPE, syntactic, 1) == []
    assert recipe.trellis_entry(folder, RECIPE) is None
    start = original.index("  cons: {")
    end = original.index("\n", start)
    recipe_file.write_text(
        original[:start] + "  cons: [stages/cons/methods.bl]" + original[end:], encoding="utf-8"
    )
    rows = recipe.table(folder, RECIPE, syntactic, 1)
    assert [row.key for row in rows] == ["port", "cons", "disc"]
    assert rows[1].cells == {kind: recipe.Cell(kind, (), {}) for kind in recipe.KINDS}
    assert rows[1].stage is None
    assert recipe.trellis_entry(folder, RECIPE).text == "trellis.yml"


def test_the_table_reads_the_unsaved_texts_as_the_reading_of_the_source_does(
    lifecycle_folder, consport_folder
):
    """The table and the trellis file a recipe names read the recipe through
    the mapping of unsaved texts, as `read_source` reads it (spec 0.4 §3.1;
    AAS, M-D7): the lifecycle recipe's buffer that writes the replacing
    selection `stages/cons/methods.vfi.bl` in place of the addition
    `stages/cons/methods.bl` gives that entry, the file on disk still giving
    the addition; a buffer that no longer reads as YAML gives no rows and
    no trellis file. A trellis file's buffer gives the value its record
    writes there, `stages/cons/methods.bl` in place of
    `stages/cons/methods.vfi.bl`."""
    folder = model.open_folder(lifecycle_folder)
    text = (lifecycle_folder / RECIPE_FILE).read_text(encoding="utf-8")
    chosen = text.replace("stages/cons/methods.bl", "stages/cons/methods.vfi.bl")
    texts = trellis.texts_of(unsaved_of(lifecycle_folder, {RECIPE_FILE: chosen}))
    syntactic = recipe.read_source(folder, RECIPE, texts)
    (entry,) = recipe.table(folder, RECIPE, syntactic, 0, texts)[1].cells["methods"].entries
    assert (entry.text, entry.slot) == ("stages/cons/methods.vfi.bl", False)
    (on_disk,) = recipe.table(folder, RECIPE, syntactic, 0)[1].cells["methods"].entries
    assert (on_disk.text, on_disk.slot) == ("stages/cons/methods.bl", False)
    assert recipe.trellis_entry(folder, RECIPE, texts).text == "trellis.yml"
    broken = trellis.texts_of(unsaved_of(lifecycle_folder, {RECIPE_FILE: text + "  broken: [\n"}))
    assert recipe.table(folder, RECIPE, syntactic, 0, broken) == []
    assert recipe.trellis_entry(folder, RECIPE, broken) is None

    consport = model.open_folder(consport_folder)
    source = recipe.Source("trellis", "declaration/trellis.port-cons-vfi.yml")
    written = (consport_folder / source.path).read_text(encoding="utf-8")
    buffer = written.replace(
        "methods: stages/cons/methods.vfi.bl", "methods: stages/cons/methods.bl"
    )
    texts = trellis.texts_of(unsaved_of(consport_folder, {source.path: buffer}))
    rows = recipe.table(consport, source, recipe.read_source(consport, source, texts), 2, texts)
    assert rows[1].cells["methods"].entries[0].text == "stages/cons/methods.bl"
    rows = recipe.table(consport, source, recipe.read_source(consport, source), 2)
    assert rows[1].cells["methods"].entries[0].text == "stages/cons/methods.vfi.bl"


def test_an_empty_list_written_all_colon_is_a_cell_with_no_entry(scratch_lifecycle):
    """The lifecycle recipe with the discount stage's methods written
    `{all: }`, an empty list, which the factory reads as `{'methods': []}`:
    the cell of that kind holds no entry, its list `all` none and its one
    line, `all`, none, where an entry `None` with a button `replace` would
    be a mark no file writes (specification §1; unit L, Task 11)."""
    recipe_file = scratch_lifecycle / "declaration/spec.yml"
    text = recipe_file.read_text(encoding="utf-8")
    assert text.count("methods: {all: [stages/disc/methods.bl]}") == 1
    recipe_file.write_text(
        text.replace("methods: {all: [stages/disc/methods.bl]}", "methods: {all: }"),
        encoding="utf-8",
    )
    folder = model.open_folder(scratch_lifecycle)
    rows = recipe.table(folder, RECIPE, recipe.read_source(folder, RECIPE), 0)
    (disc,) = [row for row in rows if row.key == "disc"]
    assert disc.cells["methods"] == recipe.Cell(
        "methods", (), {"all": ()}, (recipe.BindingLine("all", "all", (), False),)
    )


def test_a_choice_whose_entry_cannot_be_replaced_is_refused_in_the_package_s_sentence(
    scratch_lifecycle,
):
    """`choose` is total (specification §2.2 rule 4): where the entry cannot
    be replaced as text, an anchored value that an alias reads, no text is
    answered and the choice is refused in the package's sentence; no other
    exception reaches the page's handler."""
    folder = model.open_folder(scratch_lifecycle)
    (addition,) = (
        recipe.table(folder, RECIPE, recipe.read_source(folder, RECIPE), 0)[1]
        .cells["methods"]
        .entries
    )
    anchored = (
        (scratch_lifecycle / "declaration/spec.yml")
        .read_text(encoding="utf-8")
        .replace(
            "methods: {all: [stages/cons/methods.bl]}", "methods: {all: [&m stages/cons/methods.bl]}"
        )
        .replace("methods: {all: [stages/disc/methods.bl]}", "methods: {all: [*m]}")
    )
    with pytest.raises(ValueError) as refused:
        recipe.choose(folder, RECIPE, addition, "declaration/stages/cons/methods.vfi.bl", anchored)
    assert str(refused.value) == (
        "'stages/cons/methods.vfi.bl' cannot be written as a string at "
        "'stages.cons.methods.all[0]'"
    )


def test_a_stage_s_periods_are_written_in_the_recipe_s_text(scratch_durables):
    """The periods typed in the Recipe tab's field (design pass 9 §§3 and
    4): the durables recipe's `bequest` writes `periods: [0, 0]`, read as
    `0–0`, and the other stages none; `0-1` replaces its two numbers, `2–5`
    adds the key at the end of `tenure`'s block, `[3, 4]` and `7` are read
    as ranges, the empty text takes the key out and writes nothing where
    none stands; a text that is no range, and a block that no longer
    writes what the field showed, are refused in one sentence."""
    folder = model.open_folder(scratch_durables)
    text = (scratch_durables / "declaration/spec.yml").read_text(encoding="utf-8")
    rows = recipe.table(folder, RECIPE, recipe.read_source(folder, RECIPE), 0)
    assert [(row.key, row.periods and row.periods.text) for row in rows] == [
        ("tenure", None),
        ("keeper_cons", None),
        ("adjuster_cons", None),
        ("bequest", "0–0"),
    ]
    assert rows[3].periods.address == "stages.bequest.periods"

    def row_of(written, key):
        (line,) = [line for line in written.splitlines() if line.startswith(f"  {key}:")]
        return line

    replaced = recipe.write_periods(text, "bequest", "0-1", "0–0")
    assert row_of(replaced, "bequest").endswith(
        "methods: {all: [stages/bequest/methods.bl]}, periods: [0, 1]}"
    )
    added = recipe.write_periods(text, "tenure", "2–5", None)
    assert row_of(added, "tenure").endswith("stages/tenure/methods.bl]}, periods: [2, 5]}")
    assert row_of(recipe.write_periods(text, "tenure", "[3, 4]", None), "tenure").endswith(
        "periods: [3, 4]}"
    )
    assert row_of(recipe.write_periods(text, "tenure", "7", None), "tenure").endswith(
        "periods: [7, 7]}"
    )
    assert row_of(recipe.write_periods(text, "bequest", " ", "0–0"), "bequest").endswith(
        "methods: {all: [stages/bequest/methods.bl]}}"
    )
    assert recipe.write_periods(text, "tenure", "", None) == text
    for typed, shown, sentence in (
        ("late", "0–0", "late is no range of periods; write lo–hi"),
        ("1-", "0–0", "1- is no range of periods; write lo–hi"),
        ("1", None, "the file no longer writes no periods at stages.bequest.periods"),
        ("1", "0–5", "the file no longer writes 0–5 at stages.bequest.periods"),
    ):
        with pytest.raises(ValueError) as refused:
            recipe.write_periods(text, "bequest", typed, shown)
        assert str(refused.value) == sentence


def test_the_files_a_cell_may_take_include_one_that_cannot_be_read(scratch_lifecycle):
    """`choices` is total (specification §2.2 rule 4): a file named as an
    addition beside a stage file that is no UTF-8 text is listed with the
    sentence that it cannot be read, and one whose first line is a stage's
    is no addition and is left out; neither raises in the chooser's
    render."""
    stages = scratch_lifecycle / "declaration/stages"
    (stages / "cons/methods.binary.bl").write_bytes(b"\xff\xfe policy.method : !egm\n")
    (stages / "disc/methods.stage.bl").write_text("@stage: disc\n", encoding="utf-8")
    folder = model.open_folder(scratch_lifecycle)
    found = {choice.path: choice for choice in recipe.choices(folder, "methods")}
    binary = found["declaration/stages/cons/methods.binary.bl"]
    assert binary.comment == ""
    assert binary.unread.startswith("the file cannot be read: ")
    assert "declaration/stages/disc/methods.stage.bl" not in found
    assert found["declaration/stages/cons/methods.bl"].unread is None


def test_value_place_is_the_place_of_the_last_source_that_sets_the_parameter(lifecycle_folder):
    """`ρ` of the consumption stage is set at `calibration.ρ`, line 5 of the
    portfolio calibration; the discount stage's `β` at line 3 of the
    terminal period's own calibration for `periods[0]` and at line 4 of the
    portfolio calibration for `periods[1]`; a name no calibration sets has
    no place, and neither has a name of a stage that no record binds
    (`recipe.value_place`; AMD-MI-002 §5 rule 3)."""
    folder = model.open_folder(lifecycle_folder)
    cons = recipe.find_occurrence(folder, RECIPE, CONS)
    assert recipe.value_place(folder, cons.record, "calibration", "ρ") == recipe.Place(
        "declaration/calibration/portfolio.yml", "calibration.ρ", 5
    )
    terminal = recipe.find_occurrence(folder, RECIPE, DISC, (0, "disc"))
    later = recipe.find_occurrence(folder, RECIPE, DISC, (1, "disc"))
    assert recipe.value_place(folder, terminal.record, "calibration", "β") == recipe.Place(
        "declaration/calibration/terminal.yml", "calibration.β", 3
    )
    assert recipe.value_place(folder, later.record, "calibration", "β") == recipe.Place(
        "declaration/calibration/portfolio.yml", "calibration.β", 4
    )
    assert recipe.value_place(folder, cons.record, "calibration", "m_d") is None
    assert recipe.value_place(folder, None, "calibration", "ρ") is None


def test_a_parameter_s_value_is_written_as_typed_and_judged_by_the_package_s_calibration(
    retirement_folder, tmp_path
):
    """The Parameters tab composes no sentence about a value's form: a value
    typed for a parameter is written whatever it reads as, and the package's
    check of the calibration judges it against the set the declaration
    names when the stage is bound again (unit L, Task 16; defect 4 of the
    UX simulation; AMD-MI-002 §5 rule 3). On a copy of the retirement-choice
    model, whose `worker_cons.bl` declares `y : ℝ₊₊` and whose
    `calibration/retirement.yml` writes `y: 20` at line 6: with `y` declared
    in `ℕ`, `21.5` is written, and the stage bound with it is refused in the
    package's sentence naming `y` and `ℕ`, while `21` binds; with the text
    as written, `1e-5`, which reads as text, is written as typed and refused
    by the package in the same way. A list in place of the value written is
    refused in the sentence of the package's entry writer, which writes no
    list in place of a value, and the file is left as it was."""
    copy = shutil.copytree(retirement_folder, tmp_path / "retirement-choice")
    folder = model.open_folder(copy)
    path = "declaration/stages/worker_cons/worker_cons.bl"
    calibration = copy / "declaration/calibration/retirement.yml"
    found = recipe.find_occurrence(folder, RECIPE, path)
    text = (copy / path).read_text(encoding="utf-8")
    assert text.count("y : ℝ₊₊") == 1
    assert calibration.read_text(encoding="utf-8").split("\n")[5] == "  y: 20"
    natural_text = text.replace("y : ℝ₊₊", "y : ℕ")

    def notes_naming_y(stage_text: str) -> list[str]:
        # the notes of the stage bound with the calibration as the file now
        # writes it that name the parameter `y`
        again = recipe.find_occurrence(folder, RECIPE, path)
        bound = recipe.bind_occurrence(elaborate_text(stage_text, again.origin), again)
        return [note for note in bound.notes if "parameter 'y'" in note]

    written = recipe.write_value(
        folder, found.record, "worker_cons", "calibration", "y", "20", "21.5"
    )
    assert written.saved and written.text.split("\n")[5] == "  y: 21.5"
    (note,) = notes_naming_y(natural_text)
    assert "the value 21.5 lies outside the declared set ℕ" in note
    written = recipe.write_value(
        folder, found.record, "worker_cons", "calibration", "y", "21.5", "21"
    )
    assert written.saved and written.text.split("\n")[5] == "  y: 21"
    assert notes_naming_y(natural_text) == []
    written = recipe.write_value(
        folder, found.record, "worker_cons", "calibration", "y", "21", "1e-5"
    )
    assert written.saved and written.text.split("\n")[5] == "  y: 1e-5"
    (note,) = notes_naming_y(text)
    assert "the value '1e-5' lies outside the declared set ℝ₊₊" in note
    before = calibration.read_text(encoding="utf-8")
    refused = recipe.write_value(
        folder, found.record, "worker_cons", "calibration", "y", "1e-5", "[1, 2]"
    )
    assert (refused.saved, refused.reason) == (
        False,
        "a list is no string, int, float, boolean or tag, and cannot be written at "
        "'calibration.y'",
    )
    assert calibration.read_text(encoding="utf-8") == before


def test_a_value_typed_for_an_unvalued_parameter_is_added_as_the_writer_writes_it(
    scratch_durables,
):
    """A missing scalar appends to the last declared calibration source.
    A document marker or byte-order mark reads as the number 1.05; neither
    becomes part of the written scalar. The income tables remain intact."""
    folder = model.open_folder(scratch_durables)
    calibration = scratch_durables / "declaration/calibration/durables.yml"
    text = calibration.read_text(encoding="utf-8")
    assert text.count("  R_H: 1.0\n") == 1
    calibration.write_text(text.replace("  R_H: 1.0\n", ""), encoding="utf-8")
    source = scratch_durables / "declaration/calibration/wage_schedule.yml"
    before = source.read_bytes()
    found = recipe.find_occurrence(folder, RECIPE, TENURE, (3, "tenure"))
    text = (scratch_durables / TENURE).read_text(encoding="utf-8")
    tenure = recipe.bind_occurrence(elaborate_text(text, found.origin), found)
    for typed in ("--- 1.05", "\ufeff1.05"):
        rows = recipe.parameters_tab(folder, tenure.stage, tenure.record, "tenure").rows
        assert next(row.value for row in rows if row.name == "R_H") == "unvalued"
        written = recipe.write_value(
            folder, tenure.record, "tenure", "calibration", "R_H", "unvalued", typed
        )
        assert written.saved
        assert written.text == before.decode("utf-8") + "  R_H: 1.05\n"
        rows = recipe.parameters_tab(folder, tenure.stage, tenure.record, "tenure").rows
        assert next(row.value for row in rows if row.name == "R_H") == "1.05"
        source.write_bytes(before)


def test_a_value_no_file_writes_as_an_entry_of_its_own_is_refused_and_written_nowhere(
    scratch_lifecycle,
):
    """A value typed for a parameter whose row shows a value that no file of
    the occurrence's calibration list writes as an entry of its own is
    refused in one sentence naming the files of that kind, and nothing is
    written (AMD-MI-002 §5 rule 6, §6a rule 2). On a copy of the lifecycle
    registry at `periods[1]/disc`, the portfolio calibration writing `β`
    through a merge key, `<<: {β: 0.96}`, the row of `β` shows the record's
    `0.96` with no place, and `0.95` typed for it is refused, the file as
    it was; with `β: 0.96` written again and the row read, a file that
    drops the entry before the write refuses it in the same sentence."""
    folder = model.open_folder(scratch_lifecycle)
    calibration = scratch_lifecycle / "declaration/calibration/portfolio.yml"
    text = calibration.read_text(encoding="utf-8")
    assert text.count("\n  β: 0.96\n") == 1
    sentence = "no calibration file of disc writes β as an entry of its own"
    merged = text.replace("\n  β: 0.96\n", "\n  <<: {β: 0.96}\n")
    calibration.write_text(merged, encoding="utf-8")
    found = recipe.find_occurrence(folder, RECIPE, DISC, (1, "disc"))
    stage = elaborate_text(Path(found.origin).read_text(encoding="utf-8"), found.origin)
    rows = recipe.parameters_tab(folder, stage, found.record, "disc").rows
    assert next((row.value, row.place) for row in rows if row.name == "β") == ("0.96", None)
    refused = recipe.write_value(folder, found.record, "disc", "calibration", "β", "0.96", "0.95")
    assert (refused.saved, refused.reason) == (False, sentence)
    assert calibration.read_text(encoding="utf-8") == merged
    calibration.write_text(text, encoding="utf-8")
    found = recipe.find_occurrence(folder, RECIPE, DISC, (1, "disc"))
    dropped = text.replace("\n  β: 0.96\n", "\n")
    calibration.write_text(dropped, encoding="utf-8")
    refused = recipe.write_value(folder, found.record, "disc", "calibration", "β", "0.96", "0.95")
    assert (refused.saved, refused.reason) == (False, sentence)
    assert calibration.read_text(encoding="utf-8") == dropped


def test_find_occurrence_and_uses_of_read_the_unsaved_recipe(scratch_folder):
    """The portfolio model with a copy of the discount stage's file,
    `disc_copy.bl`, that the recipe on disk names nowhere; an unsaved text of
    the recipe binds the key `disc` to the copy. Given the mapping of that
    text, `find_occurrence` finds the copy at the position asked, with the
    six positions of `disc`, and `uses_of` lists them; without it, the
    recipe holds no occurrence of the copy (brief rule 2)."""
    folder = model.open_folder(scratch_folder)
    stages = scratch_folder / "declaration/stages/disc"
    shutil.copy(stages / "disc.bl", stages / "disc_copy.bl")
    copied = "declaration/stages/disc/disc_copy.bl"
    written = (scratch_folder / RECIPE_FILE).read_text(encoding="utf-8")
    text = written.replace(
        "disc: {stage: stages/disc/disc.bl", "disc: {stage: stages/disc/disc_copy.bl"
    )
    assert text != written
    texts = trellis.texts_of(unsaved_of(scratch_folder, {RECIPE_FILE: text}))
    positions = tuple((h, "disc") for h in range(6))
    found = recipe.find_occurrence(folder, RECIPE, copied, (3, "disc"), texts)
    assert (found.position, found.notes, found.positions) == ((3, "disc"), [], positions)
    assert recipe.uses_of(folder, [RECIPE], copied, texts) == [(RECIPE, positions)]
    alone = recipe.find_occurrence(folder, RECIPE, copied)
    note = f"{RECIPE_FILE} holds no occurrence of {copied}"
    assert (alone.position, alone.notes) == (None, [note])
    assert recipe.uses_of(folder, [RECIPE], copied) == [(RECIPE, ())]


def test_the_methods_tab_offers_at_each_target_the_tags_the_package_admits_there(
    model_folder,
):
    """Each row of the Methods tab is a place of the version at which a
    component is typed, read from `stage.methods` (decision S7-W1 of
    specification 0.7), and offers the words that the package admits at the
    place, `admitted_methods` of `bellman.stage` (AMD-MI-002 §5 rule 5; unit
    L, Task 18; K-I150). On the portfolio model's `cons.bl`, bound as the
    recipe binds it by the addition beside it: the two forward builders, the
    decision builder's Evaluation, which one entry types for the value and
    its stated derivative (D4), and the policy builder, whose row offers
    `!egm` among the words a builder admits; the Evaluation offers the three
    base representation families of the registry, `!Linear`, `!pchip` and
    `!closed_form` (AMD-MT-003 build contract §3), and nothing else; the
    forward decision builder, which the addition gives a handler and no
    word, shows `handler only` and offers the words too, a choice there
    appending the entry."""
    folder = model.open_folder(model_folder)
    found = recipe.find_occurrence(folder, RECIPE, CONS)
    text = Path(found.origin).read_text(encoding="utf-8")
    cons = recipe.bind_occurrence(elaborate_text(text, found.origin), found)
    tab = recipe.methods_tab(folder, cons.stage, cons.record, "cons")
    assert (tab.file, tab.sentence) == ("declaration/stages/cons/methods.bl", None)
    assert [(row.target, row.tag, row.bound) for row in tab.rows] == [
        ("arvl_to_dcsn", "!deterministic", "!deterministic"),
        ("dcsn_to_cntn", "", "handler only"),
        ("cntn_to_dcsn.evaluate", "!Linear", "!Linear"),
        ("policy", "!egm", "!egm"),
    ]
    shown = {row.target: row.choices for row in tab.rows}
    for target in shown:
        assert shown[target] == admitted_methods(cons.stage, target)
    assert "!egm" in shown["policy"]
    assert shown["cntn_to_dcsn.evaluate"] == ("!Linear", "!pchip", "!closed_form")
    assert not any("!gauss_hermite" in choices for choices in shown.values())

# the stage files of the pension model of the UX simulation whose Methods
# tabs defects 8 and 9 name, and the addition of the renter's stage
RENTER_CONS = "declaration/stages/renter_cons/renter_cons.bl"
RENTER_CONS_METHODS = "declaration/stages/renter_cons/methods.bl"
TENURE_PA = "declaration/stages/tenure_pa/tenure_pa.bl"


def test_a_refused_methods_entry_binds_no_method_and_a_branching_stage_offers_its_tags(
    tmp_path,
):
    """A typing entry that the package refuses leaves the stage with no
    component, so that the Methods tab, which reads `stage.methods`
    (decision S7-W1 of specification 0.7), has no row and the package's
    sentence stands among the binding's notes, under the error mark; a
    branching stage's rows offer the words the package admits at their
    places (unit L, Task 18; defect 9 of the UX simulation). On a copy of
    the pension model the UX simulation's post-doc built, `renter_cons.bl`
    bound as `periods[1] / renter_cons` shows the four places its addition
    types, and the row `arvl_to_dcsn`, a forward builder, offers `!egm` too,
    since admission is by the kind of the place. `!monte_carlo`, which that
    builder admits, written there in place of `!deterministic`, is refused
    when the stage is bound again, since the entry writes no `n_paths`, the
    keyword its row requires. The branching `tenure_pa.bl` bound as
    `periods[1] / tenure_pa` shows a row for each place its addition types,
    each bound and offering the words the package admits there, and the tab
    says no sentence."""
    copy = pensions_copy(tmp_path / "durables", PENSIONS_WORKING_YEARS)
    folder = model.open_folder(copy)
    source = recipe.Source("recipe", PENSIONS_RECIPE)

    def bound(path: str, key: str):
        # the stage file `path` bound as `periods[1] / <key>` of the recipe
        found = recipe.find_occurrence(folder, source, path, (1, key))
        text = (copy / path).read_text(encoding="utf-8")
        return recipe.bind_occurrence(elaborate_text(text, found.origin), found)

    renter = bound(RENTER_CONS, "renter_cons")
    tab = recipe.methods_tab(folder, renter.stage, renter.record, "renter_cons")
    rows = {row.target: row for row in tab.rows}
    assert {target: row.bound for target, row in rows.items()} == {
        "policy.optimality.argmax": "!root_find",
        "cntn_to_dcsn.evaluate": "!Linear",
        "arvl_to_dcsn": "!deterministic",
        "dcsn_to_cntn": "!deterministic",
    }
    assert tab.sentence is None
    assert rows["arvl_to_dcsn"].choices == admitted_methods(renter.stage, "arvl_to_dcsn")
    assert {"!egm", "!monte_carlo"} <= set(rows["arvl_to_dcsn"].choices)

    written = recipe.write_method(
        folder, renter.record, "renter_cons", "arvl_to_dcsn", "!deterministic", "!monte_carlo"
    )
    assert written.saved
    renter = bound(RENTER_CONS, "renter_cons")
    assert any("n_paths" in note and "monte_carlo" in note for note in renter.notes)
    tab = recipe.methods_tab(folder, renter.stage, renter.record, "renter_cons")
    assert (tab.rows, tab.file, tab.sentence) == ((), RENTER_CONS_METHODS, None)

    tenure = bound(TENURE_PA, "tenure_pa")
    tab = recipe.methods_tab(folder, tenure.stage, tenure.record, "tenure_pa")
    assert tab.sentence is None
    assert [(row.target, row.tag, row.bound) for row in tab.rows] == [
        ("arvl_to_dcsn", "!deterministic", "!deterministic"),
        ("dcsn_to_cntn", "!monte_carlo", "!monte_carlo"),
        ("cntn_to_dcsn.evaluate", "!Linear", "!Linear"),
        ("policy", "!max", "!max"),
    ]
    for row in tab.rows:
        assert row.choices and row.choices == admitted_methods(tenure.stage, row.target)

