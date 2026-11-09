"""The demonstration of model interface specification 0.3, §13, with
unit C: the ten-minute sequence of spec 0.2 §11, unchanged in its steps,
run in headless Chromium as one test with a screenshot at each step (C's
acceptance item 5).

It needs units B and C merged: the trellis view of the steps at 6:00 and
9:00 is B's (§3.1). At 6:00 it is asserted through the collection the
view's element holds, its occurrences and the labels of its joins; at 9:00
through B's panel, which names the selected box and holds the button
`open at the block`, §2.4's button "block", and through the file, the line
and the occurrence the page shows after the button. The page readers the
screenshots wait on stand in `workbench_support.py`. The nine slots are
filled in the editor through CodeMirror's own search panel, which an
economist may use as well as choose the files in B's table. The
screenshots are written to the folder BELLMAN_WORKBENCH_SCREENSHOTS names,
else to the test's temporary folder; each is taken once the view has laid
out the graph the step shows and has come to rest.
"""

from __future__ import annotations

import os
from pathlib import Path

from workbench_support import (
    ATTRIBUTE_ROWS_JS,
    CONS,
    CONS_ID,
    DEMO_FILES,
    DEMO_FILLS,
    DISC_ID,
    DOCUMENT_JS,
    HELD_COLLECTION_JS,
    LINT_RANGE_JS,
    PORT_ID,
    RECIPE_FILE,
    VIEW_OPACITY_JS,
    VIEW_STATE_JS,
    active_line,
    click_until,
    commit_form_paths,
    fill_new_trellis,
    git,
    git_line_sentence,
    join_labels,
    layouts_recorded,
    new_tab,
    occurrences_of,
    open_every_folder,
    open_path_shown,
    open_tree_file,
    open_workbench,
    panel_heads,
    recipe_head,
    record_layouts,
    replace_in_editor,
    select_until,
    show_status,
    slot_keywords,
    status_settled_on,
    status_text,
    trellis_settled,
    view_laid_out,
    view_still,
    wait_until,
)

from bellman_workbench import creation

# the steps of the sequence by their minute (spec 0.2 §11), each the name
# of its screenshot
SHOTS = (
    "00-00-new-trellis",
    "01-30-cons",
    "02-30-evaluation",
    "03-30-refusal",
    "04-30-slots-filled",
    "06-00-trellis",
    "08-00-commit-and-push",
    "09-00-box-to-line",
)

# the period file and the trellis file of the new folder, by their paths
# from the folder
PERIOD_FILE = creation.factory_path(creation.PERIOD)
TRELLIS_FILE = creation.factory_path(creation.TRELLIS)

# the stage occurrences of the trellis of six periods, each a period's
# namespace and a stage key, and the labels of the joins its connectors
# make: one per adjacent pair of periods, and the within-period connector
OCCURRENCES = {f"periods[{h}]/{key}" for h in range(6) for key in ("port", "cons", "disc")}
CONNECTOR_JOINS = {f"inter_connectors[{h}] a → k" for h in range(5)} | {"m_next → m"}


def test_item_5_the_demonstration_runs_in_headless_chrome(
    browser, server_on, repository, tmp_path
):
    """The demonstration's eight steps in one page, a screenshot at each:
    the folder written from three templates inside a test repository, its
    nine slots counted and its first commit offered, not made; cons.bl's
    backward graph and the counts of the object; the Evaluation box's
    kernel with the editor at the policy block's header; the refusal at
    line 18, column 15, the line then restored; the nine slots filled in
    spec 0.2 §11's order, cons, port and disc, the count falling from nine
    to six, three and zero, and cons.bl bound with `!egm` on the policy's
    Evaluation and `!Linear` on the continuation's; the connectors typed
    and the trellis of six periods drawn with the joins they make, the
    period periods[0] listing its three stages; the view exported, the
    folder's files committed alone and pushed, with git's sentence and the
    tree's letters cleared; a box of the trellis view followed back to the
    block of its stage (spec 0.3 §13; C item 5)."""
    work, bare = repository
    folder = work / "lifecycle-demo"
    shots = Path(os.environ.get("BELLMAN_WORKBENCH_SCREENSHOTS") or tmp_path)
    shots.mkdir(parents=True, exist_ok=True)
    context, tab = new_tab(browser)

    def shot(name: str) -> None:
        wait_until(lambda: view_still(tab), 30.0, f"the view at rest for {name}")
        tab.screenshot(path=str(shots / f"{name}.png"))

    def open_text(relpath: str) -> None:
        """Opens the file `relpath` of the new folder from the tree and waits
        until the editor holds its text as the disk holds it, which the page
        draws a moment after the tree marks the file open: a click on the
        recipe or on its trellis file draws the trellis view first, the
        editor holding no file meanwhile, so that a search typed at once
        replaces nothing (the fix wave of unit N)."""
        open_tree_file(tab, relpath)
        text = (folder / relpath).read_text(encoding="utf-8")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 30.0, f"{relpath} in the editor")

    def trellis_joined():
        """The collection the view's element holds once it is the trellis
        whose backward graph holds the eighteen occurrences and the joins
        the typed connectors make; None before."""
        # HELD_COLLECTION_JS answers null where the region holds no collection.
        # The guard restricts the reading to the trellis view.
        if tab.evaluate(VIEW_STATE_JS)["label"] != "trellis":
            return None
        held = tab.evaluate(HELD_COLLECTION_JS)
        whole = OCCURRENCES <= occurrences_of(held, "backward")
        return held if whole and CONNECTOR_JOINS <= join_labels(held, "backward") else None

    try:
        # 0:00 new trellis inside the test repository, typed as the parent
        # folder (unit L, Task 13): six periods of port,
        # cons and disc; the recipe open, the nine slots' keywords read from
        # its Recipe tab (unit M, Task 10) and none counted as a lack (unit
        # K, K-D29),
        # the first commit offered and not made. The commit form stands over
        # the window, so the screenshot is taken once it is closed.
        open_workbench(tab, server_on(work))
        record_layouts(tab)
        fill_new_trellis(tab, "lifecycle-demo", [PORT_ID, CONS_ID, DISC_ID], 6, work)
        tab.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{RECIPE_FILE}"]', timeout=30_000)
        tab.wait_for_selector('.bl-form[data-form="commit"]', timeout=30_000)
        assert commit_form_paths(tab) == set(DEMO_FILES)
        assert git(work, "rev-list", "--count", "HEAD").strip() == "1"
        tab.click(".bl-form-cancel")
        show_status(tab)
        wait_until(lambda: len(slot_keywords(tab)) == 9, 30.0, "the nine slots' keywords")
        assert "to fill" not in status_text(tab)
        wait_until(lambda: view_laid_out(tab, "trellis", 0), 90.0, "the trellis laid out")
        shot(SHOTS[0])

        # 1:30 cons.bl: its backward graph with its three builders, and the
        # counts of the object
        since = layouts_recorded(tab)
        open_tree_file(tab, CONS)
        wait_until(lambda: status_settled_on(tab, CONS), 60.0, f"the loop of {CONS}")
        wait_until(lambda: view_laid_out(tab, "cons", since), 60.0, "cons.bl laid out")
        assert "5 blocks (3 backward, 2 forward), 5 builders, 20 wires" in status_text(tab)
        shot(SHOTS[1])

        # 2:30 the Evaluation box of the policy builder: its rows and its
        # kernel in the panel, and the editor at the policy block's header
        select_until(
            tab,
            "policy:Evaluation",
            "backward",
            lambda: "policy:Evaluation" in panel_heads(tab)
            and tab.locator(".bl-kernel").count() > 0
            and active_line(tab) == 31,
            "the Evaluation's kernel in the panel and the editor at the policy block",
        )
        shot(SHOTS[2])

        # 3:30 the deliberate refusal at line 18, column 15: one refusal
        # counted and the graph dimmed; the refused line is scrolled into
        # the editor's view for the screenshot; then the line restored
        replace_in_editor(tab, "a = m_d - c", "a = m_d - - c")
        wait_until(lambda: " · not parsed · " in status_text(tab), 30.0, "the refusal")
        found, _ = wait_until(lambda: tab.evaluate(LINT_RANGE_JS), 30.0, "the underline")
        assert (found["line"], found["column"]) == (18, 15)
        assert " · 1 refused · not parsed · " in status_text(tab)
        assert tab.evaluate(VIEW_OPACITY_JS) < 1
        tab.locator(".cm-content .cm-lintRange-error").first.scroll_into_view_if_needed()
        shot(SHOTS[3])
        replace_in_editor(tab, "a = m_d - - c", "a = m_d - c")
        wait_until(lambda: " · constructed · " in status_text(tab), 30.0, "the line restored")

        # 4:30 the nine slots filled stage by stage in spec 0.2 §11's order,
        # the recipe saved after each stage; the slots' keywords of its Recipe
        # tab fall from nine to six, three and zero; cons.bl
        # bound, `!Linear` on the continuation's Evaluation and `!egm` on
        # the policy's, which stays selected for the screenshot
        open_text(RECIPE_FILE)
        for key, left in (("cons", 6), ("port", 3), ("disc", 0)):
            for kind in creation.KINDS:
                slot = creation.slot_name(key, kind)
                source = DEMO_FILLS[slot]
                replace_in_editor(tab, f"[${slot}]", f"[{source}]" if source else "[]")
            tab.click(".bl-save")
            wait_until(lambda left=left: len(slot_keywords(tab)) == left, 30.0, f"{left} left")
        since = layouts_recorded(tab)
        open_tree_file(tab, CONS)
        wait_until(
            lambda: " · bound · " in (status_settled_on(tab, CONS) or ""),
            60.0,
            "cons.bl bound",
        )
        wait_until(lambda: view_laid_out(tab, "cons", since), 60.0, "the bound graph laid out")
        for node_id, method in (
            ("cntn_to_dcsn:Evaluation", "!Linear"),
            ("policy:Evaluation", "!egm"),
        ):
            select_until(
                tab,
                node_id,
                "backward",
                lambda: node_id in panel_heads(tab)
                and ["method", method] in tab.evaluate(ATTRIBUTE_ROWS_JS),
                f"{method} on {node_id}",
            )
        shot(SHOTS[4])

        # 6:00 the connectors typed in the period file and the trellis file
        # and saved; on a click of the trellis file the trellis of the
        # recipe that reads it, six periods with the joins the connectors
        # make (B, §3.1); the period periods[0] selected, the panel lists
        # its three stages
        for relpath, mapping in ((PERIOD_FILE, "{m_next: m}"), (TRELLIS_FILE, "{a: k}")):
            open_text(relpath)
            replace_in_editor(tab, "  - {}", f"  - {mapping}")
            tab.click(".bl-save")
            wait_until(
                lambda: f"  - {mapping}\n" in (folder / relpath).read_text(encoding="utf-8"),
                30.0,
                f"{relpath} saved",
            )
        open_tree_file(tab, TRELLIS_FILE)
        line, _ = wait_until(
            lambda: trellis_settled(tab, RECIPE_FILE), 120.0, "the trellis's status line"
        )
        assert " · 6 periods, 18 occurrences · " in line
        wait_until(trellis_joined, 90.0, "the trellis view with the joins of the connectors")
        wait_until(
            lambda: view_laid_out(tab, "trellis"), 90.0, "the trellis with its joins laid out"
        )
        select_until(
            tab,
            "periods[0]___group___",
            "backward",
            lambda: tab.locator(".bl-occurrences li").all_text_contents()
            == ["periods[0]/port", "periods[0]/cons", "periods[0]/disc"],
            "the panel of periods[0]",
        )
        wait_until(lambda: view_laid_out(tab, "trellis"), 30.0, "the trellis after the selection")
        # `fit` shows the six periods side by side, which the selection's
        # enlargement around periods[0] leaves partly outside the view
        tab.click('.bl-zoom-button[data-zoom="fit"]')
        # the view starts to move a moment after the click
        tab.wait_for_timeout(500)
        shot(SHOTS[5])

        # 8:00 the view of cons.bl exported; the folder's files committed
        # alone, the view and its record not among them; pushed, git's
        # sentence shown and the tree's letters cleared
        since = layouts_recorded(tab)
        open_tree_file(tab, CONS)
        wait_until(
            lambda: " · bound · " in (status_settled_on(tab, CONS) or ""), 60.0, "cons.bl shown"
        )
        wait_until(lambda: view_laid_out(tab, "cons", since), 60.0, "cons.bl laid out")
        show_status(tab)
        tab.click(".bl-git-export")
        wait_until(lambda: "exported" in git_line_sentence(tab), 30.0, "the export")
        tab.click(".bl-git-commit")
        tab.wait_for_selector('.bl-form[data-form="commit"]')
        assert commit_form_paths(tab) == set(DEMO_FILES)
        tab.fill(".bl-commit-message textarea", "The lifecycle model: slots filled, joins typed")
        tab.click(".bl-commit-submit")
        wait_until(
            lambda: git(work, "rev-list", "--count", "HEAD").strip() == "2", 30.0, "the commit"
        )
        committed = sorted(git(work, "show", "--name-only", "--format=", "HEAD").split())
        assert committed == sorted(f"lifecycle-demo/{name}" for name in DEMO_FILES)
        tab.click(".bl-git-push")
        wait_until(lambda: "->" in git_line_sentence(tab), 30.0, "git's sentence of the push")
        branch = git(work, "symbolic-ref", "--short", "HEAD").strip()
        assert git(bare, "rev-parse", branch) == git(work, "rev-parse", "HEAD")
        open_every_folder(tab)
        wait_until(
            lambda: not "".join(tab.locator(".bl-tree-mark").all_text_contents()).strip(),
            30.0,
            "the tree's letters cleared",
        )
        # git's buttons and `new trellis` are disabled while git runs
        wait_until(
            lambda: tab.locator(".bl-git-push").is_enabled()
            and tab.locator(".bl-new-trellis").is_enabled(),
            30.0,
            "git's line ready again",
        )
        # `fit` places the graph in the middle of the view's region
        tab.click('.bl-zoom-button[data-zoom="fit"]')
        # the view starts to move a moment after the click
        tab.wait_for_timeout(500)
        shot(SHOTS[6])

        # 9:00 a box of the trellis view followed back to its block: the
        # Evaluation of periods[0] / cons selected, its name in the panel,
        # and the button `open at the block` (§2.4's "block") opens cons.bl
        # at the policy block's header, bound as that occurrence
        open_tree_file(tab, TRELLIS_FILE)
        wait_until(
            lambda: trellis_settled(tab, RECIPE_FILE), 120.0, "the trellis's status line again"
        )
        wait_until(trellis_joined, 90.0, "the trellis view again")
        wait_until(lambda: view_laid_out(tab, "trellis"), 90.0, "the trellis laid out again")
        since = layouts_recorded(tab)
        policy = '.bl-view-host .react-flow__node[data-id="periods[0]/cons/policy___group___"]'
        evaluation = '.bl-view-host .react-flow__node[data-id="periods[0]/cons/policy:Evaluation"]'
        tab.click(f'{policy} .bf-toggle[aria-label="open policy"]')
        wait_until(
            lambda: view_laid_out(tab, "trellis", since)
            and tab.locator(
                f'{policy} > .bf-layer:not(.bf-box) > .bf-toggle[aria-label="close policy"]'
            ).count() == 1
            and tab.locator(evaluation).count() == 1,
            30.0,
            "the open policy layer and its Evaluation drawn",
        )
        select_until(
            tab,
            "periods[0]/cons/policy:Evaluation",
            "backward",
            lambda: "policy:Evaluation" in panel_heads(tab)
            and tab.locator(".bl-occurrence-block").count() > 0,
            "the panel of periods[0]/cons/policy:Evaluation",
        )
        since = layouts_recorded(tab)
        click_until(
            tab,
            ".bl-occurrence-block",
            lambda: open_path_shown(tab) == CONS,
            "the occurrence's stage file",
            seconds=30.0,
        )
        wait_until(lambda: active_line(tab) == 31, 30.0, "the editor at the block's header")
        wait_until(lambda: recipe_head(tab) == "periods[0] / cons", 60.0, "the head")
        wait_until(lambda: view_laid_out(tab, "cons", since), 60.0, "cons.bl laid out")
        # `fit` places the graph in the middle of the view's region
        tab.click('.bl-zoom-button[data-zoom="fit"]')
        # the view starts to move a moment after the click
        tab.wait_for_timeout(500)
        shot(SHOTS[7])
    finally:
        context.close()
