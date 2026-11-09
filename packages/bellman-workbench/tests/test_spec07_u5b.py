"""The acceptance of the second part of unit U5 of specification 0.7, the
Workbench after the semantics reads a `.bl` addition (decisions S7-W3,
S7-W4, S7-W6 and S7-F3): one test for each of the six items of its brief.
The folders are the Workbench's own fixtures, the lifecycle registry and
the pension model, whose additions stand beside their stage files."""

from __future__ import annotations

from pathlib import Path

from workbench_support import PENSIONS_RECIPE, RECIPE_FILE, lifecycle_registry, pensions_life_cycle

from bellman.stage import admitted_methods, elaborate_text
from bellman.trellis import entry_value, load_recipe
from bellman_workbench import creation, model, recipe

RECIPE = recipe.Source("recipe", RECIPE_FILE)
CONS = "declaration/stages/cons/cons.bl"
CONS_ADDITION = "declaration/stages/cons/methods.bl"
CONS_VFI = "declaration/stages/cons/methods.vfi.bl"
RENTER_CONS = "declaration/stages/renter_cons/renter_cons.bl"
RENTER_SETTINGS = "declaration/settings/renter_cons.yml"
# words of the catalogue a forward builder admits, as a `.bl` entry writes
# them
FORWARD_WORDS = {"!deterministic", "!histogram", "!identity", "!monte_carlo"}


def bound(folder: model.Folder, root: Path, source: recipe.Source, path: str, position=None):
    """The stage file `path` of the folder bound as the occurrence `position`
    of `source`, or as its first occurrence."""
    found = recipe.find_occurrence(folder, source, path, position)
    text = (root / path).read_text(encoding="utf-8")
    return recipe.bind_occurrence(elaborate_text(text, found.origin), found)


def test_item_1_the_settings_tab_prints_the_declared_set_beside_each_value(tmp_path):
    """The Settings tab reads `stage.settings` and prints the set each
    setting is declared in beside its value, as the Parameters tab prints a
    parameter's set (decision S7-W4): on the renter's stage of the pension
    model, whose addition declares `n_w : ℕ` and the bounds `w_min` and
    `w_max` in `ℝ₊`, the three rows with the values of
    `settings/renter_cons.yml` and their places; where the recipe lists no
    settings source, the rows stand with `unvalued`; without a recipe, with
    no value. A value typed in a row is written as typed, and the package
    judges it against the declared set when the stage is bound again, the
    refusal standing among the binding's notes under its rule."""
    copy = pensions_life_cycle(tmp_path / "durables")
    folder = model.open_folder(copy)
    source = recipe.Source("recipe", PENSIONS_RECIPE)
    renter = bound(folder, copy, source, RENTER_CONS, (1, "renter_cons"))
    tab = recipe.settings_tab(folder, renter.stage, renter.record, "renter_cons")
    assert (tab.file, tab.sentence) == (RENTER_SETTINGS, None)
    assert [(row.name, row.domain, row.value) for row in tab.rows] == [
        ("n_w", "ℕ", "50"),
        ("w_min", "ℝ₊", "0.001"),
        ("w_max", "ℝ₊", "30.0"),
    ]
    assert tab.rows[0].place == recipe.Place(RENTER_SETTINGS, "settings.n_w", 5)
    without = recipe.settings_tab(folder, renter.stage, None, None)
    assert [(row.domain, row.value) for row in without.rows] == [("ℕ", None), ("ℝ₊", None), ("ℝ₊", None)]
    assert without.sentence == recipe.NO_RECIPE
    tenure = bound(folder, copy, source, "declaration/stages/tenure_pa/tenure_pa.bl", (1, "tenure_pa"))
    unvalued = recipe.settings_tab(folder, tenure.stage, tenure.record, "tenure_pa")
    assert unvalued.sentence == "the recipe lists no settings source for tenure_pa"
    assert {row.value for row in unvalued.rows} == {recipe.UNVALUED}
    written = recipe.write_value(folder, renter.record, "renter_cons", "settings", "w_min", "0.001", "-1")
    assert written.saved and "w_min: -1" in written.text
    again = bound(folder, copy, source, RENTER_CONS, (1, "renter_cons"))
    (refusal,) = again.failures
    assert refusal.rule == "setting-outside-set" and "setting 'w_min'" in refusal.message
    assert model.sentence(refusal) in again.notes


def test_item_2_a_method_chosen_in_the_tab_is_written_into_the_addition(tmp_path):
    """The Methods tab offers at each place the words the package admits
    there, and a choice is written back as the typing entry of the addition
    at the place, in the writer's sheet's form, so that the choice returns
    for additions (decision S7-W3): on the lifecycle registry's consumption
    stage, the row of `arvl_to_dcsn` offers the forward words and links the
    entry's line; `!histogram` chosen there replaces the word in
    `stages/cons/methods.bl`, every other character kept, and the stage
    bound again carries it. At the discount stage a word chosen for a place
    no entry types is appended at file level, and a word of no row of the
    method table is refused in one sentence. A place whose method word the
    stage file itself types, which no addition of the list writes, offers
    no choice, as a place the parser records no place for offers none, and
    a write asked there is refused."""
    root = lifecycle_registry(tmp_path / "lifecycle")
    folder = model.open_folder(root)
    cons = bound(folder, root, RECIPE, CONS)
    tab = recipe.methods_tab(folder, cons.stage, cons.record, "cons")
    assert tab.file == CONS_ADDITION
    rows = {row.target: row for row in tab.rows}
    assert rows["arvl_to_dcsn"].choices == admitted_methods(cons.stage, "arvl_to_dcsn")
    assert FORWARD_WORDS <= set(rows["arvl_to_dcsn"].choices)
    assert rows["arvl_to_dcsn"].place == recipe.Place(CONS_ADDITION, "arvl_to_dcsn.method", 45)
    assert (rows["policy"].tag, rows["policy"].bound, "!egm" in rows["policy"].choices) == ("!egm", "!egm", True)
    before = (root / CONS_ADDITION).read_text(encoding="utf-8")
    written = recipe.write_method(folder, cons.record, "cons", "arvl_to_dcsn", "!deterministic", "!histogram")
    assert written.saved
    after = (root / CONS_ADDITION).read_text(encoding="utf-8")
    assert after == before.replace("arvl_to_dcsn.method : !deterministic", "arvl_to_dcsn.method : !histogram")
    assert bound(folder, root, RECIPE, CONS).stage.methods["arvl_to_dcsn"].word == "!histogram"

    disc = bound(folder, root, RECIPE, "declaration/stages/disc/disc.bl")
    assert recipe.write_method(folder, disc.record, "disc", "cntn_to_dcsn", "", "!vfi").saved
    text = (root / "declaration/stages/disc/methods.bl").read_text(encoding="utf-8")
    assert text.endswith("cntn_to_dcsn.method : !vfi\n")
    refused = recipe.write_method(folder, disc.record, "disc", "arvl_to_dcsn", "!deterministic", "!nothing")
    assert (refused.saved, refused.reason) == (False, "!nothing is no word of the method table")

    typed = lifecycle_registry(tmp_path / "typed")
    entry = "arvl_to_dcsn.method : !deterministic\n"
    addition = typed / CONS_ADDITION
    without = addition.read_text(encoding="utf-8").replace(entry, "")
    addition.write_text(without, encoding="utf-8")
    with (typed / CONS).open("a", encoding="utf-8") as stage_file:
        stage_file.write("\n" + entry)
    folder = model.open_folder(typed)
    cons = bound(folder, typed, RECIPE, CONS)
    tab = recipe.methods_tab(folder, cons.stage, cons.record, "cons")
    rows = {row.target: row for row in tab.rows}
    assert (rows["arvl_to_dcsn"].tag, rows["arvl_to_dcsn"].choices, rows["arvl_to_dcsn"].place) == (
        "!deterministic",
        (),
        None,
    )
    refused = recipe.write_method(
        folder, cons.record, "cons", "arvl_to_dcsn", "!deterministic", "!histogram"
    )
    assert (refused.saved, refused.reason) == (
        False,
        "no addition of cons writes !deterministic at arvl_to_dcsn.method",
    )


def test_item_3_an_addition_that_types_nothing_leaves_the_tab_without_a_sentence(tmp_path):
    """The label `addition, not read yet` is gone, since the package reads
    additions: on the lifecycle registry, the discount stage's addition
    rewritten to its first line alone leaves the Methods tab with no row and
    no sentence, the tab naming the addition."""
    root = lifecycle_registry(tmp_path / "lifecycle")
    (root / "declaration/stages/disc/methods.bl").write_text("@methods: disc\n", encoding="utf-8")
    folder = model.open_folder(root)
    disc = bound(folder, root, RECIPE, "declaration/stages/disc/disc.bl")
    tab = recipe.methods_tab(folder, disc.stage, disc.record, "disc")
    assert (tab.rows, tab.file, tab.sentence) == ((), "declaration/stages/disc/methods.bl", None)
    assert disc.notes == []


def test_item_4_the_workbench_reads_the_methods_off_the_signatures(tmp_path):
    """The readers of the retired binding record are replaced by the
    package's answers off the signatures: the two levels are told apart by
    the rows a solution method's lines open (`stage.bindings.blocks`), the
    lifecycle registry's consumption stage having two and its discount
    stage one; and the digests of a bound stage's inputs name the additions
    under `methods`."""
    root = lifecycle_registry(tmp_path / "lifecycle")
    folder = model.open_folder(root)
    cons = bound(folder, root, RECIPE, CONS)
    disc = bound(folder, root, RECIPE, "declaration/stages/disc/disc.bl")
    assert model.two_levels(cons.stage) and not model.two_levels(disc.stage)
    text = (root / CONS).read_text(encoding="utf-8")
    assert set(model.input_digests(cons.stage, text)) == {"text", "calibration", "methods", "settings"}


def test_item_5_the_recipe_editor_names_additions_per_occurrence(tmp_path):
    """The recipe editor names addition files per occurrence as the package
    reads them (decision S7-F3): the methods cell offers the additions
    beside the stage files and no YAML file, a choice writes the replacing
    selection's name with its extension in place of the addition's, the
    rows the forms write name the stage's own addition in the form
    `{all: [stages/<key>/methods.bl]}` with no slot, a replacing selection
    the template brings copied beside the stage file and named by no row
    (decision S7-W17), so that the stage bound carries the one selection, a
    stage of the author's own an empty list, and `New file` writes the empty
    addition at its place."""
    root = lifecycle_registry(tmp_path / "lifecycle")
    folder = model.open_folder(root)
    assert [choice.path for choice in recipe.choices(folder, "methods")] == [
        CONS_ADDITION,
        CONS_VFI,
        "declaration/stages/disc/methods.bl",
        "declaration/stages/port/methods.bl",
    ]
    text = (root / RECIPE_FILE).read_text(encoding="utf-8")
    entry = recipe.Entry("stages/cons/methods.bl", False, RECIPE_FILE, "stages.cons.methods.all[0]", None)
    chosen = recipe.choose(folder, RECIPE, entry, CONS_VFI, text)
    assert chosen == text.replace("[stages/cons/methods.bl]", "[stages/cons/methods.vfi.bl]")
    assert creation.recipe_row("cons", ("stages/cons/methods.bl",)) == (
        "{stage: stages/cons/cons.bl, calibration: {all: [$cons_calibration]}, "
        "settings: {all: [$cons_settings]}, methods: {all: [stages/cons/methods.bl]}}"
    )
    template = creation.folder_template(str(root / "declaration/stages/cons"))
    assert creation.brought_files(template) == ("methods.bl", "methods.vfi.bl")
    assert creation.addition_names("saver", template) == ("stages/saver/methods.bl",)
    # the registry's answers.yml records no stage, so the form's record of
    # the stage added is not read here
    (root / creation.ANSWERS).unlink()
    added = creation.add_stage(root, "saver", template)
    new = dict(added.new_files)
    assert list(new) == [
        "declaration/stages/saver/saver.bl",
        "declaration/stages/saver/methods.bl",
        "declaration/stages/saver/methods.vfi.bl",
    ]
    assert new["declaration/stages/saver/methods.bl"].startswith("@methods: saver\n")
    row = creation.recipe_row("saver", ("stages/saver/methods.bl",))
    assert added.edits[str((root / RECIPE_FILE).resolve())].endswith(f"  saver: {row}\n")
    # written, the stage bound through the recipe carries the selection of
    # methods.bl alone: !egm on the policy builder, no !vfi on cntn_to_dcsn
    for path, text in added.new_files:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text, encoding="utf-8")
    for path, text in added.edits.items():
        Path(path).write_text(text, encoding="utf-8")
    saver = bound(model.open_folder(root), root, RECIPE, "declaration/stages/saver/saver.bl")
    words = {str(place): held.word for place, held in saver.stage.methods.items()}
    assert words["policy"] == "!egm" and "cntn_to_dcsn" not in words
    own = creation.new_stage(root, "payer")
    assert own.edits[str((root / RECIPE_FILE).resolve())].endswith(
        f"  payer: {creation.recipe_row('payer')}\n"
    )
    assert creation.recipe_row("payer").endswith("methods: {all: []}}")
    assert creation.new_source_file(root, "payer", "methods") == (
        "declaration/stages/payer/methods.bl",
        "@methods: payer\n",
    )


def test_item_6_a_variant_copies_an_addition_beside_the_stage_file(tmp_path):
    """The form `New variant` with `Copy binding files for this variant`
    copies an addition the recipe names as text, with nothing rewritten, as
    `methods.<variant>.bl` beside the stage file, and the variant's recipe
    names it (the plan of Model Interface 0.9, §4); a settings file is
    copied as before, `<stem>.<variant>_settings.yml`."""
    root = lifecycle_registry(tmp_path / "lifecycle")
    written = creation.create_variant(root, "wide", "spec.yml", copy_bindings=True)
    copies = {"declaration/stages/cons/methods.wide.bl", "declaration/settings/cons.wide_settings.yml"}
    assert copies <= set(written)
    assert (root / "declaration/stages/cons/methods.wide.bl").read_bytes() == (root / CONS_ADDITION).read_bytes()
    variant = entry_value((root / "declaration/spec.wide.yml").read_text(encoding="utf-8"), "stages.cons")
    assert variant["methods"] == {"all": ["stages/cons/methods.wide.bl"]}
    assert variant["settings"] == {"all": ["settings/cons.wide_settings.yml"]}
    read = load_recipe(root / "declaration", "spec.wide.yml")
    cons = read["periods"][0]["stages"]["cons"]
    assert [entry["path"] for entry in cons["provenance"]["source_lists"]["methods"]] == [
        str(root / "declaration/stages/cons/methods.wide.bl")
    ]
