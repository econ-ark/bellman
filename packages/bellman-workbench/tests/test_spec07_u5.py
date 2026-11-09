"""The acceptance of the first part of unit U5 of specification 0.7, the
Workbench before the package reads a `.bl` addition (decisions S7-W1 to
S7-W7): one test for each of the four changes. An addition is a methods
file that the semantics unions with its stage file; its first line that is
not blank is `@methods: <key>`."""

from __future__ import annotations

from pathlib import Path

from workbench_support import CONS, RECIPE_FILE, tree_entries

from bellman.stage import elaborate_text
from bellman_workbench import app, matsya_work, model, recipe

RECIPE = recipe.Source("recipe", RECIPE_FILE)
CONS_METHODS = "declaration/stages/cons/methods.yml"
# an addition beside the stage file of `cons`, and a replacing selection,
# where decision S7-W2 places them
ADDITION = "declaration/stages/cons/methods.bl"
VARIANT = "declaration/stages/cons/methods.vfi.bl"
ADDITION_TEXT = (
    "@methods: cons\n"
    "# The endogenous grid method on the policy builder of cons.bl.\n"
    "policy.method : !egm\n"
)
# a block file of the methods folder the decisions retire, which opens as
# an addition does
BLOCK_FILE = "declaration/methods/cons_egm.bl"


def bound_cons(folder: model.Folder):
    """`cons.bl` of the portfolio model bound as the recipe binds it."""
    found = recipe.find_occurrence(folder, RECIPE, CONS)
    text = Path(found.origin).read_text(encoding="utf-8")
    return recipe.bind_occurrence(elaborate_text(text, found.origin), found)


def test_item_1_an_addition_is_listed_beside_its_stage_and_opens_as_text(
    app_state, scratch_folder
):
    """A `.bl` file whose first line is `@methods:` is an addition and never
    a stage (decisions S7-W1 and S7-W2): the tree gives it the role
    `methods`, as it gives the block file of the methods folder; the Recipe
    cell of a stage lists no addition, and that of the methods lists the
    addition and the replacing selection beside the stage file, with the
    first comment line and no stage or targets, and none of the block files;
    a choice of the addition writes its name with its extension, since the
    package reads a name without one as a YAML file. Opened, the addition is
    text: the loop elaborates nothing, and the view keeps the stage shown."""
    for path in (ADDITION, VARIANT):
        (scratch_folder / path).write_text(ADDITION_TEXT, encoding="utf-8")
    folder = model.open_folder(scratch_folder)
    entries = tree_entries(model.folder_tree(folder))
    roles = {path: entry["role"] for path, entry in entries.items()}
    assert [roles[path] for path in (ADDITION, VARIANT, BLOCK_FILE, CONS)] == [
        "methods",
        "methods",
        "methods",
        "stage",
    ]
    stages = [choice.path for choice in recipe.choices(folder, "stage")]
    assert CONS in stages and not {ADDITION, VARIANT} & set(stages)
    methods = {choice.path: choice for choice in recipe.choices(folder, "methods")}
    comment = "The endogenous grid method on the policy builder of cons.bl."
    assert methods[ADDITION] == recipe.Choice(ADDITION, comment, "", (), None)
    assert VARIANT in methods and BLOCK_FILE not in methods
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


def test_item_2_the_methods_tab_reads_the_methods_the_stage_binds(scratch_folder):
    """The Methods tab has one row for each method the stage binds, read from
    `stage.methods` (decision S7-W1): on `cons.bl` bound by its YAML file,
    the four methods with the words the package answers. Where the
    occurrence's methods source is an addition, each row shows its method as
    text, with no choice and no place (decision S7-W3), and a stage that
    binds no method says `addition, not read yet`. Until the package reads a
    recipe that names an addition (unit U2), the record is the YAML one with
    its methods source replaced by the addition, as the package will list
    it."""
    folder = model.open_folder(scratch_folder)
    cons = bound_cons(folder)
    tab = recipe.methods_tab(folder, cons.stage, cons.record, "cons")
    assert (tab.file, tab.sentence) == (CONS_METHODS, None)
    assert len(tab.rows) == len(cons.stage.methods)
    assert [row.bound for row in tab.rows] == ["!egm", "!Linear", "!deterministic", "handler only"]

    (scratch_folder / ADDITION).write_text(ADDITION_TEXT, encoding="utf-8")
    provenance = cons.record["provenance"]
    named = [{"source": "stages/cons/methods.bl", "path": str(scratch_folder / ADDITION)}]
    lists = {**provenance["source_lists"], "methods": named}
    record = {**cons.record, "provenance": {**provenance, "source_lists": lists}}
    read = recipe.methods_tab(folder, cons.stage, record, "cons")
    assert (read.file, read.sentence) == (ADDITION, None)
    assert [(row.tag, row.choices, row.place) for row in read.rows] == [
        (row.bound, (), None) for row in tab.rows
    ]
    unbound = elaborate_text((scratch_folder / CONS).read_text(encoding="utf-8"), CONS)
    unread = recipe.methods_tab(folder, unbound, record, "cons")
    assert (unread.rows, unread.file, unread.sentence) == ((), ADDITION, recipe.ADDITION_UNREAD)
    assert recipe.ADDITION_UNREAD == "addition, not read yet"


def test_item_3_methodized_reads_whether_an_operator_carries_a_method(model_folder):
    """The label of a stage's collection, which the legend's title prints
    and the occurrence row `bound` reads from the trellis's layers, holds
    `methodized` where any operator of the stage carries a bound method,
    read from `stage.methods` (decision S7-W7): `cons.bl` bound by its
    methods file is methodized, and bound by an entry that names a handler
    alone, it is not, although its binding of methods is no longer empty."""

    def fresh():
        return elaborate_text((model_folder / CONS).read_text(encoding="utf-8"), CONS)

    assert model.collection(fresh())["label"] == "cons"
    methodized = fresh().methodize(str(model_folder / CONS_METHODS))
    assert model.collection(methodized)["label"] == "cons methodized"
    entry = {"on": "dcsn_to_cntn", "handler": "cons-port:transition_fwd"}
    handler = fresh().methodize({"stage": "cons", "methods": [entry]})
    assert [method.tag for method in handler.methods.values()] == [None]
    assert model.collection(handler)["label"] == "cons"


def test_item_4_build_declaration_is_unavailable_for_an_addition(scratch_folder, monkeypatch):
    """The Matsya job `Build declaration` is unavailable, with one sentence,
    where the files of the selected recipe hold an addition, which the
    service does not read yet (decision S7-W5): `prepare` writes nothing and
    answers that sentence, naming the addition. An addition that stands
    beside its stage file and that the recipe does not select changes
    nothing. Until the package reads a recipe that names an addition (unit
    U2), the files the recipe reads are the package's answer with the
    addition added, as the package will list it."""
    (scratch_folder / ADDITION).write_text(ADDITION_TEXT, encoding="utf-8")
    folder = model.open_folder(scratch_folder)
    session = matsya_work.Session("0" * 32, None)
    beside = matsya_work.prepare(folder, RECIPE, "recipe", session, 1)
    assert beside.path is not None and beside.refusals == ()

    read = matsya_work.required_files

    def selecting(folder, source, texts):
        syntactic, paths = read(folder, source, texts)
        return syntactic, [*paths, (scratch_folder / ADDITION).resolve()]

    monkeypatch.setattr(matsya_work, "required_files", selecting)
    prepared = matsya_work.prepare(folder, RECIPE, "recipe", session, 1)
    assert (prepared.path, prepared.record) == (None, None)
    assert prepared.refusals == (matsya_work.ADDITION_UNSENT.format(ADDITION),)
    assert prepared.refusals[0] == (
        "the service does not read a methods addition yet, so Build declaration cannot send "
        "declaration/stages/cons/methods.bl"
    )
