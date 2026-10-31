"""Creating a model and git through the page, in headless Chromium through
Playwright (model interface specification 0.3, §4 and §5; unit C's
acceptance items 1 to 4, and "new variant", Task 6 of the model folder's
layout; the form's terminal period and its notes, unit K's Task 12; a stage
copied from a folder of the disk, unit K's Task 25).

Each test starts the page over a test repository with a push destination,
`repository`, a bare repository and its clone, over a folder written in
it, or over a copy of the pension model, `scratch_pension`, through the
fixtures and the helpers of `workbench_support.py`; the skip rule of the
page's tests applies to this file, whose name begins with `test_page`. The
expected files, slots and commits are read from the folder and from git,
not from the page.
"""

from __future__ import annotations

import hashlib

from workbench_support import (
    ATTRIBUTE_ROWS_JS,
    CONS,
    CONS_ID,
    DEMO_FILES,
    DEMO_FILLS,
    DEMO_STAGES,
    DISC_ID,
    NOPORT_ID,
    PORT_ID,
    RECIPE_FILE,
    ROOT,
    TERMINAL_ID,
    VARIANT_FILES,
    add_period_controls,
    checklist_count,
    choose_view,
    commit_form_paths,
    control_targets,
    drop_by_keyboard,
    drop_item,
    error_lines,
    file_bytes,
    fill_new_trellis,
    git,
    git_line_sentence,
    new_tab,
    open_every_folder,
    open_tree_file,
    open_trellis,
    open_workbench,
    refusing_server,
    replace_in_editor,
    reveal_in_tree,
    save_unsaved_files,
    select_node,
    show_status,
    slot_keywords,
    status_settled_on,
    status_text,
    tree_entries,
    unsaved_in_tree,
    wait_until,
)

from bellman.stage import LAYER_ID_ENDING
from bellman.trellis import entry_value, load_recipe
from bellman_workbench import creation, model


def test_item_1_new_trellis_writes_the_folder_and_offers_the_first_commit(
    browser, server_on, repository
):
    """Through the page over the test repository: the form's note names
    where the folder is written, by default beside the open folder, in the
    folder that holds it, which no repository holds, and no absolute path,
    the repository's root and push destination no longer among them (unit
    L, Tasks 13 and 23; design pass 4 §§2 and 3; K-D11); with the test
    repository's folder typed as the parent folder, the note names it and
    no new repository, and `write the folder`
    writes the files of §4, opens the new folder with its recipe in the
    editor, holds the keywords of its nine slots in its Recipe tab (unit
    M, Task 10) and counts none of them in the checklist, on the
    status line or in the tree, since a slot is a parameter of the load
    and no lack (unit K, K-D28 and K-D29), and opens the commit form with
    the folder's files listed and nothing committed; `commit` makes the
    first commit with those files alone (spec 0.3 §4 and §5; C item 1)."""
    work, bare = repository
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, server_on(work))
        tab.click(".bl-new-trellis")
        place = tab.locator(".bl-form .bl-form-note").text_content()
        beside = f"writes {work.resolve().parent.name}/<name>/ beside work, with a new repository"
        assert place == beside
        assert str(work.resolve()) not in place and str(bare) not in place
        tab.fill(".bl-create-parent input", str(work))
        tab.press(".bl-create-parent input", "Enter")
        wait_until(
            lambda: tab.locator(".bl-form .bl-form-note").text_content() == "writes work/<name>/",
            10.0,
            "the note naming the test repository's folder",
        )
        tab.click(".bl-form-cancel")
        fill_new_trellis(tab, "lifecycle-demo", [PORT_ID, CONS_ID, DISC_ID], 6, work)
        tab.wait_for_selector(
            '.bl-tree-file.bl-open[data-path="declaration/spec.yml"]', timeout=30_000
        )
        # the commit form opens after the recipe, in the same submission
        tab.wait_for_selector('.bl-form[data-form="commit"]', timeout=30_000)
        folder = work / "lifecycle-demo"
        written = sorted(
            p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()
        )
        assert tuple(written) == DEMO_FILES
        wait_until(lambda: len(slot_keywords(tab)) == 9, 10.0, "the nine slots' keywords")
        assert slot_keywords(tab) == [
            creation.slot_name(key, kind) for key, _ in DEMO_STAGES for kind in creation.KINDS
        ]
        assert checklist_count(tab) == 0 and tab.locator(".bl-checklist-entry").count() == 0
        assert "to fill" not in status_text(tab)
        assert "to fill" not in tab.locator(".bl-tree").text_content()
        assert tab.locator('.bl-form[data-form="commit"]').is_visible()
        assert commit_form_paths(tab) == set(DEMO_FILES)
        assert git(work, "rev-list", "--count", "HEAD").strip() == "1"
        tab.click(".bl-form-cancel")
        show_status(tab)
        tab.click(".bl-git-commit")
        tab.fill(".bl-commit-message textarea", "New trellis lifecycle-demo from templates")
        tab.click(".bl-commit-submit")
        wait_until(
            lambda: git(work, "rev-list", "--count", "HEAD").strip() == "2", 30.0, "the commit"
        )
        committed = sorted(git(work, "show", "--name-only", "--format=", "HEAD").split())
        assert committed == sorted(f"lifecycle-demo/{name}" for name in DEMO_FILES)
    finally:
        context.close()


def test_new_trellis_lists_each_template_on_one_line_and_asks_each_stage_s_periods(
    browser, server_on, repository
):
    """Through the page (unit K, Task 12; the usability walkthrough §4
    items 7, 20 and 21; unit L, Task 23, design pass 4 §3): in the form
    `new trellis`, each template's row prints on one line its key, the name
    of its model's folder and the parameters its calibration must give,
    none where it gives none, and its hover holds its model's title, the
    parameters and the files it brings, named by their paths from the
    template's folder, `brings no file` where it brings none; a chosen
    template's row offers the text buttons `Every period` and `Terminal
    period` (unit M, Task 6), `Every period` pressed, and a press on
    `Terminal period` moves the mark to it."""
    work, _ = repository
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, server_on(work))
        tab.click(".bl-new-trellis")
        tab.wait_for_selector('.bl-form[data-form="new trellis"]', timeout=30_000)
        terminal = f'.bl-template[data-template="{TERMINAL_ID}"]'
        port = f'.bl-template[data-template="{PORT_ID}"]'
        templates = {template.id: template for template in creation.stage_templates()}
        for row, template_id in ((port, PORT_ID), (terminal, TERMINAL_ID)):
            template = templates[template_id]
            parameters = ", ".join(template.calibration)
            assert tab.locator(f"{row} .bl-template-name").text_content() == template.key
            assert tab.locator(f"{row} .bl-template-calibration").text_content() == parameters
        assert tab.locator(f"{port} .bl-template-model").text_content() == "portfolio-choice"
        hover = tab.locator(f"{port} .bl-template-button").get_attribute("title")
        assert hover.endswith(
            "brings calibration/portfolio.yml, settings/port_wide.yml, methods/port.yml"
        )
        assert hover.startswith(templates[PORT_ID].model)
        terminal_hover = tab.locator(f"{terminal} .bl-template-button").get_attribute("title")
        assert terminal_hover == f"{templates[TERMINAL_ID].model} · brings no file"
        assert tab.locator(f"{terminal} .bl-create-period").count() == 0
        tab.click(f'.bl-template-button[data-template="{TERMINAL_ID}"]')
        choice = f"{terminal} .bl-create-period"
        tab.wait_for_selector(choice)

        def pressed():
            buttons = tab.locator(f"{choice} .bl-text-button")
            return [
                (
                    buttons.nth(n).text_content().strip(),
                    buttons.nth(n).get_attribute("aria-pressed"),
                )
                for n in range(buttons.count())
            ]

        assert pressed() == [("Every period", "true"), ("Terminal period", "false")]
        tab.click(f'{choice} [data-period="terminal"]')
        wait_until(
            lambda: pressed() == [("Every period", "false"), ("Terminal period", "true")],
            10.0,
            "the mark on terminal period",
        )
    finally:
        context.close()


def test_item_2_add_stage_and_add_period_from_the_page(browser, server_on, repository):
    """Through the page over a folder new trellis wrote, its recipe open
    and its forward trellis graph shown, the forms open from the graph
    (spec 0.4 §§3.5, 3.6; brief rule 9, J-D7): the template of cons, whose
    key the recipe holds, dropped on a period opens `add stage` with that
    template chosen. With the template of noport chosen in its place, the
    form copies the stage and its two companions to disk, which the tree
    shows, and types its edits into the buffers of the recipe, the period
    file and answers.yml, which the tree marks `unsaved` and the disk does
    not yet hold; once they are saved, the line `slots` under the recipe's
    blocks lists twelve keywords (K-D29). Enter on the
    `+ period` control at the earliest end opens `add period`, which with
    noport, cons and disc writes period.young.yml, which the tree shows, and
    types its edits into the buffers of the trellis file and answers.yml;
    once the reader opens and saves each file the tree marks `unsaved`, the
    factory reads seven periods (spec 0.3 §4; C item 2; J-D14)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    recipe = created.folder / "declaration/spec.yml"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(created.folder), RECIPE_FILE)
        choose_view(tab, None, "forward")
        wait_until(lambda: add_period_controls(tab) == control_targets(6), 30.0, "the controls")
        drop_item(tab, CONS_ID, f"periods[0]{LAYER_ID_ENDING}")
        tab.wait_for_selector('.bl-form[data-form="add stage"]', timeout=30_000)
        assert tab.locator(f'.bl-template.bl-active[data-template="{CONS_ID}"]').count() == 1
        tab.click(f'.bl-template-button[data-template="{NOPORT_ID}"]')
        tab.click(".bl-add-submit")
        for path in (
            "declaration/stages/noport/noport.bl",
            "declaration/settings/noport.yml",
            "declaration/stages/noport/methods.yml",
        ):
            reveal_in_tree(tab, path, timeout=15_000)
        edited = ["answers.yml", "declaration/period.yml", "declaration/spec.yml"]
        wait_until(lambda: unsaved_in_tree(tab) == edited, 10.0, "the three files unsaved")
        assert "  noport: " not in recipe.read_text(encoding="utf-8")
        assert save_unsaved_files(tab) == edited
        assert "  noport: " in recipe.read_text(encoding="utf-8")
        wait_until(lambda: len(slot_keywords(tab)) == 12, 10.0, "the twelve slots' keywords")
        wait_until(lambda: add_period_controls(tab) == control_targets(6), 60.0, "the controls")
        drop_by_keyboard(tab, None, "earliest end")
        tab.wait_for_selector('.bl-form[data-form="add period"]', timeout=30_000)
        tab.fill(".bl-period-label input", "young")
        for key in ("noport", "cons", "disc"):
            tab.click(f'.bl-period-stage[data-key="{key}"]')
        tab.click(".bl-period-submit")
        tab.wait_for_selector(
            '.bl-tree-file[data-path="declaration/period.young.yml"]', timeout=15_000
        )
        edited = ["answers.yml", "declaration/trellis.yml"]
        wait_until(lambda: unsaved_in_tree(tab) == edited, 10.0, "the two files unsaved")
        assert len(load_recipe(created.folder / "declaration", "spec.yml")["periods"]) == 6
        assert save_unsaved_files(tab) == edited
        assert len(load_recipe(created.folder / "declaration", "spec.yml")["periods"]) == 7
    finally:
        context.close()


# the portfolio model's stage folder of `disc`, which the form "add stage"
# from a folder copies (unit K, Task 25)
DISC_FOLDER = ROOT / "applications/portfolio-choice/declaration/stages/disc"


def test_add_stage_from_a_folder_refuses_a_held_key_and_copies_under_another(
    browser, server_on, repository
):
    """Through the page over a folder new trellis wrote, its forward trellis
    graph shown (unit K, Task 25; K-D26): the item `From a folder…` dragged
    from the list of `stages` onto periods[0] opens the form "add stage"
    from a folder, its field on the folder that holds the model folder. The
    portfolio model's `disc/` written in the field, then its entry
    `disc.bl` clicked in the chooser, prints disc's row, whose hover says it
    brings `methods.yml`, under the key `disc`, which the folder holds: `add
    the stage` is refused in the form with the creation unit's sentence and
    writes nothing. With the key `discount` typed in its place, the stage
    file and its methods file are written under
    `declaration/stages/discount/`, each naming the key, the recipe, the
    period file and answers.yml are left unsaved, and answers.yml, once
    saved, records the path of `disc.bl` as given and the SHA-256 of the
    two files."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    before = file_bytes(created.folder)
    stage_file = DISC_FOLDER / "disc.bl"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(created.folder), RECIPE_FILE)
        choose_view(tab, None, "forward")
        wait_until(lambda: add_period_controls(tab) == control_targets(6), 30.0, "the controls")
        drop_item(tab, "folder", f"periods[0]{LAYER_ID_ENDING}")
        field = '.bl-form[data-form="add stage"] .bl-folder-path input'
        tab.wait_for_selector(field, timeout=30_000)
        assert tab.locator(field).input_value() == str(work.resolve())
        tab.fill(field, str(DISC_FOLDER))
        tab.press(field, "Enter")
        # the folder `disc/` holds one stage file, and the form prints its row
        tab.wait_for_selector(f'.bl-form .bl-template[data-template="{DISC_FOLDER}"]')
        tab.click(f'.bl-form .bl-folder-entry[data-path="{stage_file}"]')
        row = f'.bl-form .bl-template[data-template="{stage_file}"]'
        tab.wait_for_selector(row, timeout=30_000)
        hover = tab.locator(f"{row} .bl-template-button").get_attribute("title")
        assert hover.endswith(" · brings methods.yml")
        key = ".bl-form .bl-create-key input"
        assert tab.locator(key).input_value() == "disc"
        tab.click(".bl-form .bl-add-submit")
        refusal = tab.locator(".bl-form .bl-form-error")
        refusal.wait_for(timeout=10_000)
        assert refusal.text_content() == "declaration/stages/disc/ exists"
        assert file_bytes(created.folder) == before
        tab.fill(key, "discount")
        tab.click(".bl-form .bl-add-submit")
        stage = "declaration/stages/discount/discount.bl"
        methods = "declaration/stages/discount/methods.yml"
        reveal_in_tree(tab, stage, timeout=30_000)
        assert tab.locator(".bl-form").count() == 0
        assert (created.folder / stage).read_text(encoding="utf-8") == stage_file.read_text(
            encoding="utf-8"
        ).replace("@stage: disc\n", "@stage: discount\n", 1)
        assert (created.folder / methods).read_text(encoding="utf-8") == (
            (DISC_FOLDER / "methods.yml")
            .read_text(encoding="utf-8")
            .replace("stage: disc\n", "stage: discount\n", 1)
        )
        edited = ["answers.yml", "declaration/period.yml", "declaration/spec.yml"]
        wait_until(lambda: unsaved_in_tree(tab) == edited, 10.0, "the three files unsaved")
        assert save_unsaved_files(tab) == edited
        answers = (created.folder / creation.ANSWERS).read_text(encoding="utf-8")
        assert entry_value(answers, "stages.discount") == {
            "origin": str(stage_file),
            "sha256": {
                name: hashlib.sha256((DISC_FOLDER / name).read_bytes()).hexdigest()
                for name in ("disc.bl", "methods.yml")
            },
        }
    finally:
        context.close()


def test_new_stage_from_the_page_refuses_a_held_key_and_adds_the_stage_to_the_recipe(
    browser, server_on, repository
):
    """Through the page over a folder new trellis wrote, its trellis shown
    (unit K's decision K-D7): the form `new stage` says in one line that it
    writes declaration/stages/<key>/<key>.bl and adds the stage to the
    recipe and answers.yml; with the key cons, whose stage folder exists,
    it is refused in the form and writes nothing; with the key buyer it
    writes the empty stage file, which the tree shows and the editor opens,
    and writes the stage's row into the recipe and its three slots into
    answers.yml on disk with it, no file then unsaved (unit L, Task 17;
    defect 22 of the UX simulation)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    stage = "declaration/stages/buyer/buyer.bl"
    before = file_bytes(created.folder)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(created.folder), RECIPE_FILE)
        wait_until(lambda: len(slot_keywords(tab)) == 9, 10.0, "the nine slots' keywords")
        tab.click(".bl-new-stage")
        tab.wait_for_selector('.bl-form[data-form="new stage"]', timeout=10_000)
        assert tab.locator(".bl-form-note").text_content() == (
            "writes declaration/stages/<key>/<key>.bl and adds the stage to "
            "declaration/spec.yml and answers.yml"
        )
        tab.fill(".bl-new-stage-key input", "cons")
        tab.click(".bl-new-stage-submit")
        refusal = tab.locator(".bl-form-error")
        refusal.wait_for(timeout=10_000)
        assert refusal.text_content() == "declaration/stages/cons/ exists"
        assert file_bytes(created.folder) == before
        tab.fill(".bl-new-stage-key input", "buyer")
        tab.click(".bl-new-stage-submit")
        tab.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{stage}"]', timeout=30_000)
        wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "no file unsaved")
        after = file_bytes(created.folder)
        edited = ["answers.yml", "declaration/spec.yml"]
        assert {path: after[path] for path in before if path not in edited} == {
            path: text for path, text in before.items() if path not in edited
        }
        row = f"  buyer: {creation.recipe_row('buyer')}\n"
        assert after["declaration/spec.yml"].decode("utf-8").endswith(row)
        slots = [f"    - {creation.slot_name('buyer', kind)}\n" for kind in creation.KINDS]
        assert all(slot in after["answers.yml"].decode("utf-8") for slot in slots)
        assert sorted(set(after) - set(before)) == [stage]
        assert after[stage].decode("utf-8") == creation.empty_stage_text("buyer")
    finally:
        context.close()


def test_item_3_the_letters_the_named_commit_the_export_and_the_push(
    browser, server_on, repository
):
    """Through the page over a folder new trellis wrote, with unrelated
    work staged in the repository: the tree's letters equal `git status
    --porcelain`; `export view` writes the shown view and its record, which
    git ignores; `commit` lists the folder's files alone and commits them,
    the staged work staying; `push` reaches the destination and shows
    git's sentence (spec 0.3 §5; C items 3 and 4)."""
    work, bare = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    (work / "unrelated.md").write_text("staged and not the model's\n", encoding="utf-8")
    git(work, "add", "unrelated.md")
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, server_on(created.folder))
        open_tree_file(tab, CONS)
        wait_until(lambda: status_settled_on(tab, CONS), 60.0, f"the loop of {CONS}")
        porcelain = git(work, "status", "--porcelain", "--untracked-files=all").splitlines()
        letters = {
            line[3:].removeprefix("lifecycle-demo/"): line[:2].strip() for line in porcelain
        }
        open_every_folder(tab)
        rows = tab.locator(".bl-tree-file")
        for number in range(rows.count()):
            row = rows.nth(number)
            mark = row.locator(".bl-tree-mark").text_content().strip()
            assert mark == letters.get(row.get_attribute("data-path"), "")
        show_status(tab)
        tab.click(".bl-git-export")
        wait_until(lambda: "exported" in git_line_sentence(tab), 30.0, "the export")
        assert len(list((created.folder / "model-explorer").glob("*.export.json"))) == 1
        tab.click(".bl-git-commit")
        tab.wait_for_selector('.bl-form[data-form="commit"]')
        assert commit_form_paths(tab) == set(DEMO_FILES)
        tab.fill(".bl-commit-message textarea", "The lifecycle model from templates")
        tab.click(".bl-commit-submit")
        wait_until(
            lambda: git(work, "rev-list", "--count", "HEAD").strip() == "2", 30.0, "the commit"
        )
        committed = sorted(git(work, "show", "--name-only", "--format=", "HEAD").split())
        assert committed == sorted(f"lifecycle-demo/{name}" for name in DEMO_FILES)
        assert git(work, "diff", "--cached", "--name-only").split() == ["unrelated.md"]
        tab.click(".bl-git-push")
        wait_until(lambda: "->" in git_line_sentence(tab), 30.0, "git's sentence of the push")
        branch = git(work, "symbolic-ref", "--short", "HEAD").strip()
        assert git(bare, "rev-parse", branch) == git(work, "rev-parse", "HEAD")
    finally:
        context.close()


def test_item_3_a_push_that_would_prompt_shows_gits_sentence(browser, server_on, repository):
    """Through the page, a push to a destination that asks for a user name
    fails at once: git's own sentence stands in the list under the error
    mark, the button `push` is marked as refused and git's line prints no
    sentence (AMD-MI-002 §6a rule 1); no field of the page asks for a
    credential (spec 0.3 §5)."""
    work, _ = repository
    with refusing_server() as url:
        git(work, "remote", "set-url", "origin", url)
        context, tab = new_tab(browser)
        try:
            open_workbench(tab, server_on(work))
            show_status(tab)
            tab.click(".bl-git-push")

            def refused() -> str | None:
                # the sentence of the list that is git's of the refused push
                sentences = [line[0] for line in error_lines(tab)]
                found = [each for each in sentences if "could not read Username" in each]
                return found[0] if found else None

            sentence, _ = wait_until(refused, 30.0, "git's sentence of the refused push")
            assert "terminal prompts disabled" in sentence
            assert tab.locator(".bl-git-push.bl-refusal-mark").count() == 1
            assert git_line_sentence(tab) == ""
            assert tab.locator("input[type=password]").count() == 0
        finally:
            context.close()


def test_a_slot_filled_in_the_recipe_binds_the_stage_shown(browser, server_on, repository):
    """Through the page over a folder new trellis wrote: cons.bl is shown
    symbolic while no file is written in place of its slots; once its three
    slots are replaced by files in the recipe, by typing in the editor and
    saving, the line `slots` lists six keywords, and cons.bl, opened
    again, is bound by the recipe, `!egm` on its Evaluation, since the page
    watches the recipe with the sources it names (spec 0.3 §2.2 rule 1,
    C-R11)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, server_on(created.folder))
        open_tree_file(tab, CONS)
        wait_until(lambda: status_settled_on(tab, CONS), 60.0, f"the loop of {CONS}")
        assert " · symbolic · " in status_text(tab)
        open_tree_file(tab, "declaration/spec.yml")
        for kind in creation.KINDS:
            slot = creation.slot_name("cons", kind)
            replace_in_editor(tab, f"[${slot}]", f"[{DEMO_FILLS[slot]}]")
        tab.click(".bl-save")
        wait_until(lambda: len(slot_keywords(tab)) == 6, 10.0, "six slots' keywords left")
        open_tree_file(tab, CONS)
        wait_until(lambda: " · bound · " in status_text(tab), 30.0, "cons.bl bound by the recipe")
        # a selection made while the view lays out a new graph is lost, so
        # the node is selected once the status line has settled
        wait_until(lambda: status_settled_on(tab, CONS), 30.0, "the bound graph drawn")
        select_node(tab, "policy:Evaluation", "backward")
        wait_until(
            lambda: ["method", "!egm"] in tab.evaluate(ATTRIBUTE_ROWS_JS),
            10.0,
            "!egm on the Evaluation",
        )
    finally:
        context.close()


def test_new_variant_writes_three_files_beside_the_recipe_and_nothing_else(
    browser, server_on, scratch_pension
):
    """Through the page over a copy of the pension model, whose
    `declaration/` holds spec.yml: `new variant` with the name two-stages
    writes declaration/spec.two-stages.yml, trellis.two-stages.yml and
    period.two-stages.yml, which the page's tree shows, and opens the
    variant's recipe in the editor and its trellis in the view, the panel
    under the editor on its Recipe tab naming the variant (unit M, Task 10;
    design pass 9 §2); the folder's tree, read by
    `model.folder_tree`, holds the three files as a recipe, a trellis file
    and a period file, and no other file of the folder changed (spec 0.3
    §4, new variant; the page test of Task 6 of the model folder's
    layout)."""
    before = file_bytes(scratch_pension)
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, server_on(scratch_pension))
        tab.click(".bl-new-variant")
        tab.wait_for_selector('.bl-form[data-form="new variant"]', timeout=30_000)
        tab.fill(".bl-variant-name input", "two-stages")
        tab.click(".bl-variant-submit")
        for path in VARIANT_FILES:
            tab.wait_for_selector(f'.bl-tree-file[data-path="{path}"]', timeout=15_000)
        tab.wait_for_selector(
            f'.bl-tree-file.bl-open[data-path="{VARIANT_FILES[0]}"]', timeout=15_000
        )
        named = '.bl-classification[data-panel="recipe"] .bl-inspector-file'
        tab.wait_for_selector(named, timeout=30_000)
        wait_until(
            lambda: tab.locator(named).text_content() == "spec.two-stages.yml",
            30.0,
            "the Recipe tab naming the variant",
        )
    finally:
        context.close()
    tree = tree_entries(model.folder_tree(model.open_folder(scratch_pension)))
    assert [tree[path]["role"] for path in VARIANT_FILES] == ["recipe", "trellis", "period"]
    after = file_bytes(scratch_pension)
    assert sorted(set(after) - set(before)) == sorted(VARIANT_FILES)
    assert {path: after[path] for path in before} == before
