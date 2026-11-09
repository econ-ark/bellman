"""The acceptance of the first part of unit U5 of specification 0.7, the
Workbench before the package reads a `.bl` addition (decisions S7-W1 to
S7-W7): one test for each of the four changes, brought to the state after
units U2 to U4, in which the package reads a recipe that names an addition
(the second part's file is test_spec07_u5b.py). An addition is a methods
file that the semantics unions with its stage file; its first line that is
not blank is `@methods: <key>`."""

from __future__ import annotations

from pathlib import Path

from workbench_support import (
    CONS,
    PENSIONS,
    PENSIONS_RECIPE,
    PENSIONS_WORKING_YEARS,
    RECIPE_FILE,
    pensions_copy,
    tree_entries,
)

from bellman.stage import elaborate_text
from bellman_workbench import app, matsya_work, model, recipe

RECIPE = recipe.Source("recipe", RECIPE_FILE)
# an addition beside the stage file of `cons`, and a replacing selection,
# where decision S7-W2 places them
ADDITION = "declaration/stages/cons/methods.bl"
VARIANT = "declaration/stages/cons/methods.vfi.bl"
ADDITION_TEXT = (
    "@methods: cons\n"
    "# The endogenous grid method on the policy builder of cons.bl.\n"
    "policy.method : !egm\n"
)
# the renter's stage file of the pension fixture and its addition
RENTER_CONS = "declaration/stages/renter_cons/renter_cons.bl"
RENTER_ADDITION = "declaration/stages/renter_cons/methods.bl"


def bound_renter(folder: model.Folder, copy: Path):
    """The renter's stage of the pension fixture bound as `periods[1] /
    renter_cons` of its recipe."""
    source = recipe.Source("recipe", PENSIONS_RECIPE)
    found = recipe.find_occurrence(folder, source, RENTER_CONS, (1, "renter_cons"))
    text = (copy / RENTER_CONS).read_text(encoding="utf-8")
    return recipe.bind_occurrence(elaborate_text(text, found.origin), found)


def test_item_1_an_addition_is_listed_beside_its_stage_and_opens_as_text(
    app_state, scratch_folder
):
    """A `.bl` file whose first line is `@methods:` is an addition and never
    a stage (decisions S7-W1 and S7-W2): the tree gives it the role
    `methods`; the Recipe cell of a stage lists no addition, and that of
    the methods lists the addition and the replacing selection beside the
    stage file, with the first comment line; a choice of the addition
    writes its name with its extension, since the package refuses a
    methods name without it under `recipe-source` (decision S7-F3).
    Opened, the addition is text: the loop elaborates nothing, and the
    view keeps the stage shown."""
    for path in (ADDITION, VARIANT):
        (scratch_folder / path).write_text(ADDITION_TEXT, encoding="utf-8")
    folder = model.open_folder(scratch_folder)
    entries = tree_entries(model.folder_tree(folder))
    roles = {path: entry["role"] for path, entry in entries.items()}
    assert [roles[path] for path in (ADDITION, VARIANT, CONS)] == ["methods", "methods", "stage"]
    stages = [choice.path for choice in recipe.choices(folder, "stage")]
    assert CONS in stages and not {ADDITION, VARIANT} & set(stages)
    methods = {choice.path: choice for choice in recipe.choices(folder, "methods")}
    comment = "The endogenous grid method on the policy builder of cons.bl."
    assert methods[ADDITION] == recipe.Choice(ADDITION, comment, None)
    assert VARIANT in methods
    entry = recipe.Entry("stages/cons/methods", False, RECIPE_FILE, "stages.cons.methods", None)
    assert recipe.written_name(folder, RECIPE, entry, ADDITION) == "stages/cons/methods.bl"

    app_state(scratch_folder)
    app.open_file(CONS)
    app.run_loop()
    shown = app.shown.value
    assert shown is not None and shown.path == CONS
    app.open_file(ADDITION)
    # the editor answers the flush request with the open file's text
    held = app.buffers.value[CONS]
    app.on_change({"path": CONS, "revision": held["document_revision"], "text": held["text"]})
    assert app.open_path.value == ADDITION
    outcome = app.run_loop()
    assert (outcome.state, outcome.version, outcome.note) == (
        None,
        None,
        f"{ADDITION} opened as text",
    )
    assert app.shown.value is shown


def test_item_2_the_methods_tab_reads_the_methods_the_stage_binds(tmp_path):
    """The Methods tab has one row for each place of the version at which a
    component is typed, read from `stage.methods` (decision S7-W1): on the
    renter's stage of the pension fixture bound by its addition, the four
    places with the words the package answers, in the package's order, and
    the tab names the addition. An addition that types nothing leaves the
    tab with no row and no sentence, since the package reads additions
    now."""
    copy = pensions_copy(tmp_path / "durables", PENSIONS_WORKING_YEARS)
    folder = model.open_folder(copy)
    renter = bound_renter(folder, copy)
    tab = recipe.methods_tab(folder, renter.stage, renter.record, "renter_cons")
    assert (tab.file, tab.sentence) == (RENTER_ADDITION, None)
    assert len(tab.rows) == len(renter.stage.methods)
    assert [(row.target, row.bound) for row in tab.rows] == [
        ("arvl_to_dcsn", "!deterministic"),
        ("dcsn_to_cntn", "!deterministic"),
        ("cntn_to_dcsn.evaluate", "!Linear"),
        ("policy.optimality.argmax", "!root_find"),
    ]
    (copy / RENTER_ADDITION).write_text(
        "@methods: renter_cons\n# No selection yet.\n", encoding="utf-8"
    )
    empty = bound_renter(folder, copy)
    tab = recipe.methods_tab(folder, empty.stage, empty.record, "renter_cons")
    assert (tab.rows, tab.file, tab.sentence) == ((), RENTER_ADDITION, None)


def test_item_3_methodized_reads_whether_an_operator_carries_a_method(tmp_path):
    """The label of a stage's collection, which the legend's title prints
    and the occurrence row `bound` reads from the trellis's layers, holds
    `methodized` where any operator of the stage carries a method
    component, read from the signatures (decision S7-W7): the renter's stage
    with its addition is methodized, and with an addition that types a
    handler alone it is not, although it carries a component."""
    copy = pensions_copy(tmp_path / "durables", PENSIONS_WORKING_YEARS)
    text = (copy / RENTER_CONS).read_text(encoding="utf-8")

    def fresh():
        return elaborate_text(text, str(copy / RENTER_CONS))

    assert model.collection(fresh())["label"] == "renter_cons"
    methodized = fresh().methodize(str(copy / RENTER_ADDITION))
    assert model.collection(methodized)["label"] == "renter_cons methodized"
    handler = fresh().methodize(
        {
            "text": '@methods: renter_cons\ndcsn_to_cntn.handler : "pensions:transition_fwd"\n',
            "origin": str(copy / RENTER_ADDITION),
        }
    )
    assert [held.word for held in handler.methods.values()] == [""]
    assert model.collection(handler)["label"] == "renter_cons"


def test_item_4_build_declaration_is_unavailable_for_an_addition(tmp_path):
    """The Matsya job `Build declaration` is unavailable, with one sentence,
    where the files of the selected recipe hold an addition, which the
    service does not read yet (decision S7-W5): `prepare` writes nothing and
    answers that sentence, naming the additions the recipe reads. A recipe
    whose methods lists name no addition prepares its files."""
    session = matsya_work.Session("0" * 32, None)
    source = recipe.Source("recipe", PENSIONS_RECIPE)
    without = pensions_copy(tmp_path / "without", PENSIONS)
    beside = matsya_work.prepare(model.open_folder(without), source, "recipe", session, 1)
    assert beside.path is not None and beside.refusals == ()

    with_additions = pensions_copy(tmp_path / "with", PENSIONS_WORKING_YEARS)
    prepared = matsya_work.prepare(model.open_folder(with_additions), source, "recipe", session, 1)
    assert (prepared.path, prepared.record) == (None, None)
    assert len(prepared.refusals) == 1
    assert prepared.refusals[0].startswith(
        "the service does not read a methods addition yet, so Build declaration cannot send "
    )
    assert RENTER_ADDITION in prepared.refusals[0]
