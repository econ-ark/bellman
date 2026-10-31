"""The page in headless Chromium through Playwright (model interface
specification 0.3: stage A's acceptance items 1 to 4 of §12 and unit A1's
items 1 to 4).

The fixtures and the helpers are those of `conftest.py`: one Solara server
runs for the session over `model_folder`, the copy of
`applications/portfolio-choice/` made as a fresh git repository, on a free
port, with the delay marker in its environment; `server_on` starts one over
another folder for the tests that need the pension or the Cagetti–De Nardi
copy; one Chromium runs for the session; each test opens the page in a new
browser context and clicks a file in the tree. The labels item 1 expects are
computed from the stage object of the same text bound as the page binds it,
as the occurrence that the copy's recipe, `declaration/spec.yml`, names
(`recipe.find_occurrence`, `recipe.bind_occurrence`), so that a method the
recipe binds ends its box's label. The labels, cards, kernels and counts the
other tests expect are computed from the stage object of the same text
elaborated with the relative path of `cons.bl` in the copy, `CONS`, as its
origin (`stage_of`), so that the card's `Source` line prints the file's name
as the page does; the digests are those of the text (`digest7`).

The tests named `test_item_<n>_*` close the items of stage A:

1. the twelve node labels of the backward graph are drawn in the view as
   SVG text, character for character, each line of a label a line of its
   text;
2. an edit of one line redraws the view within two seconds of the pause,
   the view holds the new graph and the status line's counts equal
   `model.counts(stage)`; a save during the pause writes the current
   document; the result of an older revision does not replace a newer one;
3. a refusal is placed at its line and column with the package's
   sentence, the graph stays dimmed and the file on disk is unchanged; a
   second tab's save and a save after an outside change with the time kept
   meet the choice and write nothing on their own;
4. a click on a box shows `kernel()` of the piece in the panel and moves
   the editor to the block's header line; the cursor entering a block
   selects its boxes in the view.

The tests named `test_a1_item_<n>_*` close the items of unit A1 (§12, "A1,
stage A corrected"):

1. opening another file keeps unsaved text, and a refusal on line 8 of
   `cons.bl`, which begins with 𝑢, is underlined at the refused text;
2. `entrepreneur_death.bl` of the Cagetti–De Nardi copy, whose forward
   graph the construction refuses, shows its backward graph, the state
   `constructed, forward refused`, the one refusing node and the refusal's
   position in the panel; `cons.bl` prints the counts of the object;
3. `declaration/stages/worker_saving/worker_saving.bl` of the pension copy
   is bound as `periods[0] / worker_saving`, the head says so, and the perch
   cell of a pulled-back wire's port carries the perch's definition in its
   title;
4. the panel of a layer shows the builder's signature, parameters and
   settings and its `card` button, the panel of `Inputs` the graph's
   signature, the `block` button and a `Source` line each move the editor
   to their lines, and no word of the viewer's and no banner is on the
   page.

The tests named `test_b_item_<n>_*` close the items of unit B (§12, "B,
binding and the trellis"): 1, a methods file chosen for an occurrence
binds it and keeps the recipe; 2, the trellis of `port-cons.yml` drawn,
read again once after a save and restricted; 3, the entries answers.yml
marks apart from the refusals, no slot among them, and a connector that
names no field opened at the factory's address; 4, the name under the
cursor; 5, the pension trellis's forward graph and its refusing node's
links. The tests named `test_b_*` without an item number pin the trellis
view's other behaviors.

The tests named `test_m_item_<n>_*` close the claims of unit M's items
(`spec_0.3-matsya-window.md` §5) that need the page, in the column unit R
gives Matsya (spec 0.4 §§5.1 and 5.6): the column open at the right and
folded by its button (3), a question answered with its passages while the
page stays live, in a conversation named by a digest of the folder's path
(1), a silent service told in one sentence (2), and Υ in periwinkle with no
orange on the page (5). Every server of these tests runs the stand-in of
Matsya's client, `tests/matsya_stub.py`, and no test reaches the service.

The test named `test_amd_mi_001_item_5_*` closes item 5 of AMD-MI-001 (the
legend of the graph drawn and the selection ring): on `cons.bl` with its
methods, the legend lists the levels, the bound methods and the marks the
graph holds, the perches while the overlays are on and the roles of a
field diagram, and the selected box has the ultramarine-light ring.

The test named `test_trellis_load_item_6_*` records item 6 of the brief on
the trellis view's load time: the seconds from the page's opening to the
drawn trellis of a copy of the durables folder, opened by two servers in
turn with a cache folder of the test's own, empty for the first. The
bounds of item 6 are AAS's own reading, so the times are recorded and not
asserted.

The tests after item 4 of stage A close AAS's instructions of 1 October
2026: the types hidden behind the button `hide types` (§2.2 rule 5), with
a refusal's line drawn in full; the lines wrapped at column 78; the viewer
without its own title bar; the card copied by the button `card` in place
of the card drawn in the panel; the brand's mark, the tab's title and the
favicon.

The boxes are drawn on a WebGL canvas, so a test selects one through the
element's own method `selectNode`, which the page treats as a click. The
times of item 2 are measured in the page, from the last `keydown` to the
element's `modelGraphProcessed` event.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import urllib.request
from pathlib import Path

import pytest

from workbench_support import (
    choose_option,
    choose_restriction,
    choose_view,
    periods_held,
    restrict,
    restriction_shown,
    attribute_of,
    PORT_DESCRIPTIONS_JS,
    ATTRIBUTE_ROWS_JS,
    BOX_DRAWN_JS,
    ORANGE,
    bound_as_the_recipe_binds,
    property_color,
    BUDGET_MS,
    CLIPBOARD_RECORDS_JS,
    CLIPBOARD_REFUSES_JS,
    COLOR_OF_JS,
    CONS,
    CONS_PORT_TRELLIS,
    DELAY_MARKER,
    DISC,
    DOCUMENT_JS,
    DRAWN_TEXT_JS,
    FRAME_TRACKS,
    GUIDE_JS,
    GUTTER_MARKER_LINE_JS,
    HELD_COLLECTION_JS,
    KEEPER_CONS,
    LINT_RANGE_JS,
    MATSYA_FOLD,
    MATSYA_TOGGLE,
    ORANGE_ELEMENTS_JS,
    PAUSE_MS,
    PORT,
    PORT_CONS,
    PORT_CONS_RECIPE,
    PORT_ROWS_JS,
    RECIPE_FILE,
    RECORD_OPENED_JS,
    REFUSING_ELK_JS,
    REPLACE_SPANS_JS,
    RETIRE_CHOICE,
    ROOT,
    SHARED_CONS,
    SIZES,
    STATUS,
    STATUS_TEXT_JS,
    STORE_JS,
    STUB_PASSAGES,
    TABLE_ROWS_JS,
    TEXT_WIDTH_JS,
    TOOLTIP_TEXTS_JS,
    TREE_FILE,
    VIEW_OPACITY_JS,
    VISUAL_LINES_JS,
    WORKER_SAVING,
    active_line,
    annotated_line,
    applied,
    as_json,
    boxes,
    changed_lines,
    checklist_count,
    click_before,
    click_line,
    click_toggle,
    click_until,
    digest7,
    edited,
    error_count,
    error_lines,
    expected_layout,
    fonts_drawn,
    free_port,
    graph_named,
    line_text,
    minimap_marks,
    new_tab,
    occurrence_head,
    occurrences_of,
    open_cons,
    open_file,
    open_path_shown,
    open_recipe_row,
    open_trellis,
    orange_marks,
    panel_head,
    ports_on_box,
    recipe_head,
    record,
    record_layouts,
    repository_copy,
    reveal_in_tree,
    select_node,
    select_until,
    server_error,
    settled_status,
    slot_keywords,
    stage_of,
    start_server,
    status_place,
    status_settled_on,
    status_text,
    stop_server,
    svg_texts,
    tracks,
    tracks_near,
    trellis_settled,
    two_cons_one_joined,
    type_of,
    unjoined_port_ids,
    view_laid_out,
    wait_for_view,
    wait_until,
    viewport,
    WHOLE_GRAPH_SHOWN_JS,
    record_view_state,
    view_state,
    EDITOR_HEIGHT_JS,
    SCROLL_EDITOR_JS,
    FOCUSED_JS,
    LINE_BELOW_EDITOR_JS,
    PREVIEW_LINES_JS,
    SELECTED_BOXES_JS,
    editor_handle,
    flow_handle,
    lines_holding,
    goto_results,
    open_goto,
    replace_in_editor,
)

from bellman.stage import elaborate_text, layers_to_open, source_spans
from bellman.trellis import load_recipe
from bellman_workbench import matsya_client, model, recipe, trellis

# the brand's files the page serves, copied from the site's
BRAND = ROOT / "packages/bellman-workbench/bellman_workbench/public/brand"
SITE_BRAND = ROOT / "docs/_assets/brand"

# the stage of the Cagetti–De Nardi copy whose forward builders graph the
# construction refuses at line 17, relative to the copy
ENTREPRENEUR_DEATH = "declaration/stages/entrepreneur_death/entrepreneur_death.bl"

# the stage of the retirement copy, which branches into `work` and `retire`
RET_CHOICE = "declaration/stages/ret_choice/ret_choice.bl"

# the trellis file and the period file of a folder in the one layout of a
# model folder, by their paths from the folder
TRELLIS_FILE = "declaration/trellis.yml"
PERIOD_FILE = "declaration/period.yml"
# the portfolio model's calibration in the copy of cons-port and in the
# lifecycle registry, by its path from the folder
PORTFOLIO_CALIBRATION = "declaration/calibration/portfolio.yml"

# Interface words and the server's banner that the page does not print
# (specification §§2.3 and 2.5).
FOREIGN_WORDS = ("op name", "layer", "namespace", "node data", "This website runs on Solara")

# the keys of `model.counts` the status line prints
COUNTED = ("blocks", "blocks_backward", "blocks_forward", "builders", "wires")


# --- item 1 ---


def test_item_1_labels_drawn(page, server, original, model_folder):
    """The twelve node labels of the backward graph of cons.bl, bound as the
    page binds it, as the occurrence the folder's recipe names where one
    does (`recipe.find_occurrence`, `recipe.bind_occurrence`), so that a
    method the recipe binds ends its box's label (AMD-MI-001, rule 4), and
    read from `model.collection`, are drawn in the view as SVG text
    character for character, each line of a label one `tspan` of its text
    (AMD-MI-001, rule 1), and each as many times as it labels a node; the
    only other texts drawn are the names of the three layers the view
    opens. After the `forward` button is clicked, the four labels of the
    forward graph are drawn, and the names of its two layers, which the
    view keeps and opens though each holds one child (the configuration
    keepLayersWithASingleChild, since a perch of a field diagram may hold
    one field), and nothing else."""
    stage = bound_as_the_recipe_binds(model_folder, original, CONS)
    collection = model.collection(stage)
    labels = [node["label"] for node in graph_named(collection, "backward")["nodes"]]
    layers = layers_to_open(collection, "backward", 1)
    assert "𝑉≻ ∘ 𝑔≻" in labels and len(labels) == 12

    seconds = open_cons(page, server)
    drawn = svg_texts(page)
    print(f"the view drew {len(drawn)} texts {seconds:.2f} s after the click: {drawn}")
    # the server's banner is off (specification §2.5, `server_environment`)
    assert page.get_by_text("This website runs on Solara").count() == 0
    remaining = list(drawn)
    for label in labels:
        assert label in remaining, f"{label!r} is not drawn; drawn: {drawn}"
        remaining.remove(label)
    assert sorted(remaining) == sorted(layers)

    forward_labels = [node["label"] for node in graph_named(collection, "forward")["nodes"]]
    choose_view(page, "operator", "forward")

    def forward_drawn():
        texts = svg_texts(page)
        return texts if all(label in texts for label in forward_labels) else None

    drawn, seconds = wait_until(forward_drawn, 10.0, "the forward graph's labels drawn")
    print(f"the forward graph drawn {seconds:.2f} s after the click: {drawn}")
    remaining = list(drawn)
    for label in forward_labels:
        remaining.remove(label)
    assert sorted(remaining) == sorted(layers_to_open(collection, "forward", 1))


# --- item 2 ---


def test_item_2_edit_redraws_within_two_seconds(page, server, original, model_folder):
    """Typing `*1` at the end of line 18 (`a = m_d - c*1`) redraws the view
    within two seconds of the pause, measured in the page from the last
    keydown to the element's modelGraphProcessed event; the element then
    holds the graphs of the edited text, bound as the folder's recipe binds
    the file, as the page binds it (`bound_as_the_recipe_binds`; R-D44),
    and the status line prints the edited text's digest and the counts
    `model.counts` answers for that stage."""
    edited_text = edited(original, 18, "    a = m_d - c*1")
    stage = bound_as_the_recipe_binds(model_folder, edited_text, CONS)
    expected_collection = model.collection(stage)
    expected_counts = model.counts(stage)

    open_cons(page, server)
    click_line(page, 18)
    page.keyboard.press("End")
    started = time.perf_counter()
    page.keyboard.type("*1")
    assert line_text(page, 18) == "    a = m_d - c*1"
    page.wait_for_function("() => window.record.processed.length > 0", timeout=10_000)
    redraw_seconds = time.perf_counter() - started
    keys, processed = record(page, "keys"), record(page, "processed")
    elapsed_ms = processed[-1] - keys[-1]
    print(
        f"redrawn {elapsed_ms:.0f} ms after the last keydown in the page "
        f"({redraw_seconds:.2f} s from the typing call)"
    )
    assert elapsed_ms <= PAUSE_MS + BUDGET_MS

    held = page.evaluate(HELD_COLLECTION_JS)
    expected = {"label": expected_collection["label"], "graphs": expected_collection["graphs"]}
    assert as_json(held) == as_json(expected)

    status = settled_status(page, digest7(edited_text))
    print(f"status line: {status.string!r}")
    assert status["path"] == CONS
    assert status["state"] == "constructed" and status["refusals"] is None
    assert {
        "blocks": int(status["blocks"]),
        "blocks_backward": int(status["backward"]),
        "blocks_forward": int(status["forward"]),
        "builders": int(status["builders"]),
        "wires": int(status["wires"]),
    } == {key: expected_counts[key] for key in COUNTED}


def test_item_2_save_during_the_pause_sends_the_current_document(
    page, server, cons_file, original
):
    """A save clicked within the pause after a keystroke writes the
    document as it stands, keystroke included: the click follows the last
    keydown by less than the pause, and the file on disk equals the
    original plus the typed line; the loop then prints that text's
    digest."""
    open_cons(page, server)
    page.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+End")
    page.keyboard.press("Enter")
    page.click(".bl-save")
    saved_text = original + "\n"
    _, seconds = wait_until(
        lambda: cons_file.read_text(encoding="utf-8") == saved_text,
        5.0,
        "the file on disk equal to the editor's document",
    )
    keys, clicks = record(page, "keys"), record(page, "clicks")
    gap_ms = clicks[-1] - keys[-1]
    print(f"save clicked {gap_ms:.0f} ms after the last keydown; written {seconds:.2f} s later")
    assert gap_ms < PAUSE_MS
    assert cons_file.read_text(encoding="utf-8") == saved_text
    settled_status(page, digest7(saved_text))


def test_item_2_older_revisions_result_is_discarded(page, server, cons_file, original):
    """A valid edit that holds the delay marker (`c*1  # a1-delay`) is
    typed, so that the server holds its result back 1.5 s; once the status
    line shows its loop running, the marker is deleted and a keystroke
    (`*`) that the parser refuses is typed, followed at once by a save: the
    loop takes the saved text, without the marker, as a new buffer
    revision without waiting for the pause, and its result is written
    before the first revision's finishes. The first revision's result,
    which finishes after a newer one's, is discarded: its digest stands in
    no text the status line held. The final status is the second
    revision's, the refusal's marks stand, and the file on disk holds the
    saved second text."""
    first = edited(original, 18, f"    a = m_d - c*1  {DELAY_MARKER}")
    second = edited(original, 18, "    a = m_d - c*1*")
    assert model.elaborate_buffer(second, CONS).stage is None
    first_digest, second_digest = digest7(first), digest7(second)

    open_cons(page, server)
    click_line(page, 18)
    page.keyboard.press("End")
    page.keyboard.type(f"*1  {DELAY_MARKER}")
    assert line_text(page, 18) == f"    a = m_d - c*1  {DELAY_MARKER}"
    page.wait_for_function(f"() => ({STATUS_TEXT_JS})().includes('elaborating')", timeout=5_000)
    for _ in f"  {DELAY_MARKER}":
        page.keyboard.press("Backspace")
    page.keyboard.type("*")
    assert line_text(page, 18) == "    a = m_d - c*1*"
    page.click(".bl-save")
    page.wait_for_function(
        f"() => ({STATUS_TEXT_JS})().includes('{second_digest}')", timeout=10_000
    )
    # the first revision's loop ends within its held-back second and a half
    page.wait_for_timeout(3_000)

    texts = [text for _, text in record(page, "status")]
    first_shown = [n for n, text in enumerate(texts) if first_digest in text]
    print(f"the first digest {first_digest} was shown: {bool(first_shown)}; final {texts[-1]!r}")
    assert not first_shown, texts
    final = STATUS.match(texts[-1])
    assert final is not None and final["digest"] == second_digest
    assert final["refusals"] == "1" and final["state"] == "not parsed"
    assert page.evaluate(GUTTER_MARKER_LINE_JS) == 18
    assert page.locator(".bl-view-host.bl-stale").count() == 1
    assert cons_file.read_text(encoding="utf-8") == second


# --- item 3 ---


def test_item_3_refusal_placed_and_file_unchanged(page, server, cons_file, original):
    """Typing `- ` before `c` on line 18 (`a = m_d - - c`) underlines the
    refusal at line 18, column 15, marks the gutter on line 18 and shows the
    package's sentence in the tooltip and in the list under the error mark,
    with the file and line 18 as its link, the panel's refusal naming its
    place and its rule alone (AMD-MI-002 §6a rule 1); the view keeps its
    graph, dimmed, while the refusal stands; the file on disk is unchanged."""
    refused_text = edited(original, 18, "    a = m_d - - c")
    (diagnostic,) = model.elaborate_buffer(refused_text, CONS).diagnostics
    assert (diagnostic.line, diagnostic.column, diagnostic.rule) == (18, 15, "syntax")

    open_cons(page, server)
    click_line(page, 18)
    page.keyboard.press("End")
    page.keyboard.press("ArrowLeft")
    started = time.perf_counter()
    page.keyboard.type("- ")
    assert line_text(page, 18) == "    a = m_d - - c"
    page.wait_for_selector(".cm-content .cm-lintRange-error", timeout=8_000)
    print(f"the refusal is underlined {time.perf_counter() - started:.2f} s after the keystroke")

    underlined = page.evaluate(LINT_RANGE_JS)
    assert (underlined["line"], underlined["column"]) == (18, 15), underlined
    assert page.evaluate(GUTTER_MARKER_LINE_JS) == 18
    page.hover(".cm-lint-marker-error")
    page.wait_for_selector(".cm-tooltip-lint .cm-diagnosticText", timeout=3_000)
    assert page.evaluate(TOOLTIP_TEXTS_JS) == [diagnostic.message]

    panel, _ = wait_until(
        lambda: page.locator(".bl-refusal").text_content()
        if page.locator(".bl-refusal").count()
        else None,
        5.0,
        "the panel's refusal",
    )
    assert panel == f"refused at {CONS}:18:15 · rule syntax"
    wait_until(
        lambda: error_lines(page) == [(diagnostic.message, CONS, 18)],
        5.0,
        "the package's sentence in the list under the error mark",
    )
    status = settled_status(page, digest7(refused_text))
    assert status["refusals"] == "1" and status["state"] == "not parsed"

    assert page.locator(".bl-view-host.bl-stale").count() == 1
    assert page.evaluate(VIEW_OPACITY_JS) < 1
    assert len(svg_texts(page)) >= 12
    page.wait_for_timeout(1_000)
    assert cons_file.read_text(encoding="utf-8") == original


def test_item_3_second_tabs_save_meets_the_choice(page, browser, server, cons_file, original):
    """Two tabs hold cons.bl; B types on line 1; A adds a line and saves;
    B's save meets the compare, overwrite or reload choice, whose sentence
    stands in the list under the error mark with the file (AMD-MI-002 §6a
    rule 1); the disk keeps A's text and B's editor keeps its typing;
    compare prints the unified diff of the two texts; reload puts A's text
    into B's editor and closes the choice, which leaves the list, the disk
    still A's."""
    context_b, page_b = new_tab(browser)
    try:
        open_cons(page, server)
        open_cons(page_b, server)
        click_line(page_b, 1)
        page_b.keyboard.press("End")
        page_b.keyboard.type("  # B")
        settled_status(page_b, digest7(edited(original, 1, "@stage: cons  # B")))

        page.locator(".cm-content").click()
        page.keyboard.press("ControlOrMeta+End")
        page.keyboard.press("Enter")
        page.click(".bl-save")
        a_text = original + "\n"
        wait_until(
            lambda: cons_file.read_text(encoding="utf-8") == a_text, 5.0, "A's save on disk"
        )

        page_b.click(".bl-save")
        page_b.wait_for_selector(".bl-choice", timeout=5_000)
        wait_until(
            lambda: error_lines(page_b) == [("the file changed on disk", CONS, None)],
            5.0,
            "the choice's sentence in the list under the error mark",
        )
        assert cons_file.read_text(encoding="utf-8") == a_text
        assert line_text(page_b, 1) == "@stage: cons  # B"

        page_b.click(".bl-choice-compare")
        page_b.wait_for_selector(".bl-diff", timeout=3_000)
        diff = page_b.locator(".bl-diff").text_content()
        assert "--- on disk" in diff and "+++ in the editor" in diff
        assert "-@stage: cons\n+@stage: cons  # B" in diff

        page_b.click(".bl-choice-reload")
        wait_until(
            lambda: page_b.locator(".bl-choice").count() == 0
            and line_text(page_b, 1) == "@stage: cons",
            5.0,
            "B's editor reloaded and the choice closed",
        )
        wait_until(lambda: error_lines(page_b) == [], 5.0, "the choice's sentence left the list")
        assert cons_file.read_text(encoding="utf-8") == a_text
    finally:
        context_b.close()


def test_item_3_save_after_utime_meets_the_choice(page, server, cons_file, original):
    """The editor holds unsaved typing; another tool rewrites the file and
    puts its modification time back with os.utime; the save meets the
    choice and writes nothing, the disk keeping the outside text; the
    overwrite choice then writes the editor's text and the choice
    closes."""
    open_cons(page, server)
    page.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+End")
    page.keyboard.type("# A")
    settled_status(page, digest7(original + "# A"))

    before = cons_file.stat()
    outside = original + "# written outside the editor\n"
    cons_file.write_text(outside, encoding="utf-8")
    os.utime(cons_file, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert cons_file.stat().st_mtime_ns == before.st_mtime_ns

    page.click(".bl-save")
    page.wait_for_selector(".bl-choice", timeout=5_000)
    assert cons_file.read_text(encoding="utf-8") == outside

    page.click(".bl-choice-overwrite")
    wait_until(
        lambda: cons_file.read_text(encoding="utf-8") == original + "# A",
        5.0,
        "the overwrite on disk",
    )
    wait_until(lambda: page.locator(".bl-choice").count() == 0, 5.0, "the choice closed")


# --- item 4 ---


def test_item_4_box_shows_kernel_and_moves_editor(page, server, original):
    """A click on the box `cntn_to_dcsn:Pullback` shows `str(kernel())` of
    the piece in the panel character for character (its card is copied by
    the button `card`, `test_card_button_copies_the_card`) and moves the
    editor's cursor to the header line of the block `cntn_to_dcsn`; the
    cursor put on the line of `policy.InvEuler` selects the policy block's
    first box in the view, the panel lists the block's boxes, and the cursor
    stays on its line."""
    stage = stage_of(original)
    piece = model.piece(stage, "backward", "cntn_to_dcsn:Pullback")
    spans = source_spans(original, CONS)
    header_line = spans["cntn_to_dcsn"].line
    policy_line = spans["policy.InvEuler"].line
    policy_nodes = model.nodes_of_block(model.collection(stage), "backward", "policy")
    assert header_line == 21 and policy_line == 33 and len(policy_nodes) == 4

    open_cons(page, server)
    select_node(page, "cntn_to_dcsn:Pullback", "backward")
    page.wait_for_selector(".bl-kernel", timeout=10_000)
    wait_until(
        lambda: page.locator(".bl-kernel").text_content() == piece.kernel,
        5.0,
        "the piece's kernel",
    )
    wait_until(lambda: active_line(page) == header_line, 5.0, "the cursor on the block's header")

    click_line(page, policy_line)
    wait_until(
        lambda: record(page, "selections")[-1:] == [policy_nodes[0]],
        5.0,
        "the selection of the policy block's first box",
    )
    wait_until(
        lambda: page.locator(".bl-block-nodes li").all_text_contents() == policy_nodes,
        5.0,
        "the panel's list of the block's boxes",
    )
    wait_until(
        lambda: policy_nodes[0] in panel_head(page),
        5.0,
        "the panel's head naming the policy block's first box",
    )
    assert active_line(page) == policy_line


# --- unit A1, item 1 ---


def test_a1_item_1_opening_another_file_keeps_unsaved_text(page, server, model_folder, original):
    """`  # kept` typed at the end of line 1 of cons.bl, with no wait for the
    pause, then a click on `port.bl` in the tree: the editor shows port.bl's
    own text and the tree marks cons.bl `unsaved`; a click on cons.bl shows
    line 1 with the typed text, the status line reads the buffer as
    unsaved with the typed text's digest, and the file on disk is
    unchanged (specification §2.2 rule 3)."""
    kept_text = edited(original, 1, "@stage: cons  # kept")
    port_text = (model_folder / PORT).read_text(encoding="utf-8")

    open_cons(page, server)
    click_line(page, 1)
    page.keyboard.press("End")
    page.keyboard.type("  # kept")
    assert line_text(page, 1) == "@stage: cons  # kept"
    reveal_in_tree(page, PORT)
    page.click(f'.bl-tree-file[data-path="{PORT}"]')
    _, seconds = wait_until(
        lambda: open_path_shown(page) == PORT, 10.0, "port.bl open"
    )
    wait_until(lambda: line_text(page, 1) == port_text.split("\n")[0], 5.0, "port.bl's text")
    print(f"port.bl open {seconds:.2f} s after the click; line 1 {line_text(page, 1)!r}")
    mark = page.locator(f'.bl-tree-file[data-path="{CONS}"] .bl-tree-mark').text_content()
    assert mark.strip() == "unsaved"

    page.click(TREE_FILE)
    wait_until(
        lambda: open_path_shown(page) == CONS, 10.0, "cons.bl open again"
    )
    wait_until(lambda: line_text(page, 1) == "@stage: cons  # kept", 5.0, "the kept text")
    assert page.evaluate(DOCUMENT_JS) == kept_text
    status = settled_status(page, digest7(kept_text), 15.0)
    print(f"status line: {status.string!r}")
    assert status["file"] == "buffer, unsaved" and status["state"] == "constructed"
    assert (model_folder / CONS).read_text(encoding="utf-8") == original


def test_a1_item_1_the_refusal_after_an_astral_character_is_underlined_at_the_refused_text(
    page, server, original
):
    """Line 8 of cons.bl begins with 𝑢, a character outside the Basic
    Multilingual Plane, which the editor's document counts as two code
    units and the package as one code point. `  - - 1` typed after
    `c^(1-ρ)/(1-ρ)` is refused at line 8, column 32 in code points; the
    editor underlines `- 1` on line 8 at that column, the panel's refusal
    names `cons.bl:8:32` and the status line reads one refusal and the
    state `not parsed` (implementation review of stage A, correction 2)."""
    lines = original.split("\n")
    refused_line = lines[7].replace("c^(1-ρ)/(1-ρ)", "c^(1-ρ)/(1-ρ)  - - 1", 1)
    refused_text = edited(original, 8, refused_line)
    (diagnostic,) = model.elaborate_buffer(refused_text, CONS).diagnostics
    assert (diagnostic.line, diagnostic.column, diagnostic.rule) == (8, 32, "syntax")
    tail = "         :: [id=util]"
    assert lines[7].endswith(tail)

    open_cons(page, server)
    click_line(page, 8)
    page.keyboard.press("End")
    for _ in tail:
        page.keyboard.press("ArrowLeft")
    page.keyboard.type("  - - 1")
    assert line_text(page, 8) == refused_line
    page.wait_for_selector(".cm-content .cm-lintRange-error", timeout=8_000)
    underlined = page.evaluate(LINT_RANGE_JS)
    print(f"underlined: {underlined}")
    assert (underlined["line"], underlined["column"], underlined["text"]) == (8, 32, "- 1")
    assert page.evaluate(GUTTER_MARKER_LINE_JS) == 8
    panel, _ = wait_until(
        lambda: page.locator(".bl-refusal").text_content()
        if page.locator(".bl-refusal").count()
        else None,
        5.0,
        "the panel's refusal",
    )
    assert panel.startswith(f"refused at {CONS}:8:32 · rule syntax")
    status = settled_status(page, digest7(refused_text))
    assert status["refusals"] == "1" and status["state"] == "not parsed"


# --- unit A1, item 2 ---


def test_a1_item_2_refused_direction_shows_the_other_graph_and_the_counts(
    page, browser, server, server_on, cagetti_folder, original
):
    """On the Cagetti–De Nardi copy, `entrepreneur_death.bl`, whose forward
    builders graph the construction refuses at line 17, shows its backward
    graph with every label of that graph drawn, the status line's state
    `constructed, forward refused` with the counts `model.counts` answers,
    and the panel's refusal at `entrepreneur_death.bl:17:1` under the rule
    word `not constructed by this version`, its sentence standing in the
    list under the error mark with the file and line 17 (AMD-MI-002 §6a
    rule 1); the `forward` button shows the one refusing node, whose panel
    names line 17 and whose `item` button moves the editor to line 17. On
    cons.bl the status line prints
    `5 blocks (3 backward, 2 forward), 5 builders, 20 wires`, the counts of
    the object: the specification's `3 builders` are the backward graph's,
    and the line prints the builders of both graphs, as
    `test_a1_item_2_counts_of_cons_are_the_objects` asserts."""
    text = (cagetti_folder / ENTREPRENEUR_DEATH).read_text(encoding="utf-8")
    elaboration = model.elaborate_buffer(text, ENTREPRENEUR_DEATH)
    stage = elaboration.stage
    assert model.loop_state(elaboration) == "constructed, forward refused"
    collection = model.collection(stage)
    backward_labels = [node["label"] for node in graph_named(collection, "backward")["nodes"]]
    (refusing,) = graph_named(collection, "forward")["nodes"]
    counts = model.counts(stage, collection)
    refusal = model.refused_directions(stage)["forward"]
    assert (refusal["line"], refusal["column"], refusal["rule"]) == (17, 1, "not-constructed")

    context, tab = new_tab(browser)
    try:
        seconds = open_file(tab, server_on(cagetti_folder), ENTREPRENEUR_DEATH, minimum=4)
        drawn = svg_texts(tab)
        print(f"the backward graph drawn {seconds:.2f} s after the click: {drawn}")
        assert all(label in drawn for label in backward_labels)
        status = settled_status(tab, digest7(text), 20.0)
        print(f"status line: {status.string!r}")
        assert status["state"] == "constructed, forward refused"
        assert status["path"] == ENTREPRENEUR_DEATH
        assert {
            "blocks": int(status["blocks"]),
            "blocks_backward": int(status["backward"]),
            "blocks_forward": int(status["forward"]),
            "builders": int(status["builders"]),
            "wires": int(status["wires"]),
        } == {key: counts[key] for key in COUNTED}
        panel = tab.locator(".bl-refusal").text_content()
        print(f"the panel's refusal: {panel[:120]!r}")
        assert panel.startswith(f"refused at {ENTREPRENEUR_DEATH}:17:1")
        assert "rule not constructed by this version" in panel
        assert "forward builders graph" in panel and refusal["message"] not in panel
        wait_until(
            lambda: (refusal["message"], ENTREPRENEUR_DEATH, 17) in error_lines(tab),
            10.0,
            "the refusal's sentence in the list under the error mark",
        )

        choose_view(tab, "operator", "forward")
        wait_until(lambda: svg_texts(tab) == [refusing["label"]], 15.0, "the one refusing node")
        select_node(tab, refusing["id"], "forward")
        tab.wait_for_selector(".bl-item-button", timeout=10_000)
        assert panel_head(tab).startswith("forward builders graph refused")
        rows = dict(tab.evaluate(ATTRIBUTE_ROWS_JS))
        print(f"the refusing node's rows: {rows}")
        assert rows["line"] == "17" and rows["column"] == "1"
        assert rows["rule"] == "not constructed by this version"
        # the panel names the file by its name alone
        assert rows["file"] == ENTREPRENEUR_DEATH.rsplit("/", 1)[-1]
        tab.click(".bl-item-button")
        wait_until(lambda: active_line(tab) == 17, 5.0, "the editor on line 17")
    finally:
        context.close()

    cons_counts = model.counts(stage_of(original))
    open_cons(page, server)
    status = settled_status(page, digest7(original))
    print(f"status line: {status.string!r}")
    assert "5 blocks (3 backward, 2 forward), 5 builders, 20 wires" in status.string
    assert (int(status["blocks"]), int(status["builders"]), int(status["wires"])) == (
        cons_counts["blocks"],
        cons_counts["builders"],
        cons_counts["wires"],
    )
    assert (int(status["backward"]), int(status["forward"])) == (
        cons_counts["blocks_backward"],
        cons_counts["blocks_forward"],
    )


# --- unit A1, item 3 ---


def test_a1_item_3_the_occurrence_is_named_and_the_perch_is_defined(
    browser, server_on, pension_folder
):
    """On the pension copy, `worker_saving.bl` opened from the tree is
    bound as the occurrence `periods[0] / worker_saving`, which the head
    under the tree prints; the box `cntn_to_dcsn:Pullback` selected, the
    ports of the panel's rows `reads` and `writes` equal the piece's ports,
    each type in its label's hover (unit K, Task 5), each perch carrying in
    its title the definition the specification gives
    (§2.4): the perch of the field whose function the wire carries, the
    function's domain being in `type`, so that the pulled-back value
    function, a function on the decision state, printing `cntn` is read
    correctly."""
    text = (pension_folder / WORKER_SAVING).read_text(encoding="utf-8")
    stage = elaborate_text(text, WORKER_SAVING)
    piece = model.piece(stage, "backward", "cntn_to_dcsn:Pullback")
    rows = piece.ports["inputs"] + piece.ports["outputs"]
    assert {row["perch"] for row in rows} == {"cntn"}
    assert any(row["type"].startswith("ℝ₊₊ × Xp") for row in piece.ports["outputs"])

    context, tab = new_tab(browser)
    try:
        seconds = open_file(tab, server_on(pension_folder), WORKER_SAVING, minimum=4)
        print(f"the view drawn {seconds:.2f} s after the click")
        head, seconds = wait_until(
            lambda: recipe_head(tab) if recipe_head(tab).startswith("periods") else None,
            30.0,
            "the head naming the occurrence",
        )
        print(f"the head reads {head!r} {seconds:.2f} s after the view")
        assert head == "periods[0] / worker_saving"
        select_node(tab, "cntn_to_dcsn:Pullback", "backward")
        tab.wait_for_selector(".bl-port", timeout=10_000)
        found = tab.evaluate(PORT_ROWS_JS)
        print(f"the ports rows: {found}")
        assert [row["cells"] for row in found] == [
            [row["label"], row["perch"], row["type"], row["role"]] for row in rows
        ]
        for row in found:
            assert row["perch_title"].startswith(
                "the perch of the field whose function the wire carries"
            )
            assert "domain" in row["perch_title"] and "type" in row["perch_title"]
    finally:
        context.close()


# --- unit A1, item 4 ---


def test_a1_item_4_the_panel_of_a_layer_the_inputs_node_and_the_links(
    page, server, original, model_folder
):
    """The layer `policy` selected, the panel's head reads `builder policy`,
    its rows are the layer's attributes from the exporter for cons.bl bound
    as the folder's recipe binds it, as the page binds it
    (`bound_as_the_recipe_binds`; R-D44): `inputs`, `outputs`, `feasible
    set`, `parameter` and `setting 1` to `setting 6`, the six settings the
    recipe binds; its signature block is the builder's signature and its
    `card` button copies the builder's card;
    the node `Inputs`
    selected, the panel's head reads `Inputs` and its signature block is
    `str(stage.builder.bwd.signature())`, the word "boundary" written
    nowhere; the box `cntn_to_dcsn:Aggregation` selected and the cursor on
    line 1, the `block` button moves the editor to the block's header line
    21 and the `Source` line 23 moves it to line 23; no word of the
    viewer's (op name, layer, namespace, node data) and no banner is on
    the page."""
    stage = bound_as_the_recipe_binds(model_folder, original, CONS)
    collection = model.collection(stage)
    layer = model.piece(stage, "backward", "policy___group___", collection)
    inputs = model.piece(stage, "backward", "GraphInputs", collection)
    box = model.piece(stage, "backward", "cntn_to_dcsn:Aggregation", collection)
    header_line = source_spans(original, CONS)["cntn_to_dcsn"].line
    settings = {f"setting {number}" for number in range(1, 7)}
    assert set(layer.attributes) == {"inputs", "outputs", "feasible set", "parameter"} | settings
    assert inputs.signature == str(stage.builder.bwd.signature())
    assert header_line == 21 and [line for line, _ in box.source_lines] == [22, 23]

    open_cons(page, server)
    select_node(page, "policy___group___", "backward")
    page.wait_for_selector(".bl-signature", timeout=10_000)
    # the builder's identifier in Code name, then its kind (the fix wave Q3b
    # of unit Q, item 19; C1)
    wait_until(lambda: panel_head(page).startswith("policy Builder"), 5.0, "the layer's head")
    rows = dict(page.evaluate(ATTRIBUTE_ROWS_JS))
    print(f"the layer's rows: {rows}")
    assert rows == {key: str(value) for key, value in layer.attributes.items()}
    assert page.locator(".bl-signature").text_content() == layer.signature
    # the copy component's button is mounted after the plain elements
    wait_until(
        lambda: page.locator(".bl-card-button").count() == 1, 5.0, "the layer's card button"
    )
    page.evaluate(CLIPBOARD_RECORDS_JS)
    page.click(".bl-card-button")
    copied, _ = wait_until(
        lambda: page.evaluate("() => window.copiedText"), 5.0, "the builder's card copied"
    )
    assert copied == layer.card

    select_node(page, "GraphInputs", "backward")
    wait_until(lambda: panel_head(page).startswith("Inputs"), 5.0, "the Inputs head")
    wait_until(
        lambda: page.locator(".bl-signature").text_content() == inputs.signature,
        5.0,
        "the graph's signature",
    )
    assert "boundary" not in page.locator(".bl-panel").text_content()

    select_node(page, "cntn_to_dcsn:Aggregation", "backward")
    wait_until(
        lambda: page.locator(".bl-kernel").count()
        and page.locator(".bl-kernel").text_content() == box.kernel,
        5.0,
        "the box's kernel",
    )
    click_line(page, 1)
    wait_until(lambda: active_line(page) == 1, 5.0, "the cursor on line 1")
    click_until(
        page,
        ".bl-block-button",
        lambda: active_line(page) == header_line,
        "the editor on the header line",
    )
    click_until(
        page,
        '.bl-source-line[data-line="23"]',
        lambda: active_line(page) == 23,
        "the editor on source line 23",
    )

    for word in FOREIGN_WORDS:
        assert page.get_by_text(word).count() == 0, word
    drawn = page.evaluate(DRAWN_TEXT_JS, ".bl-window")
    assert all(word not in drawn for word in FOREIGN_WORDS)


# --- the page after AAS's instructions of 1 October 2026 ---


def types_button(page) -> str:
    # whether the toggle `Types` stands pressed, the types shown (unit N,
    # Task 1; design pass 10 §4)
    return page.get_attribute(".bl-types-button", "aria-pressed")


def test_hide_types_draws_names_alone(page, server, original):
    """The toggle `Types` (unit N, Task 1; design pass 10 §4), pressed while
    the types are shown, draws every block header and annotation of cons.bl
    as its name alone, line 13 as `[arvl_to_dcsn] {` and line 8 ending `::
    [util]`, and then stands unpressed; the cursor put on line 13 draws that
    line in full while line 21 stays a name; a second click draws every
    line in full. The editor's document is the file's text throughout."""
    lines = original.split("\n")
    open_cons(page, server)
    assert types_button(page) == "true"
    assert line_text(page, 13) == lines[12]

    page.click(".bl-types-button")
    wait_until(lambda: line_text(page, 13) == "[arvl_to_dcsn] {", 5.0, "line 13 as its name")
    assert line_text(page, 21) == "[cntn_to_dcsn] {"
    assert line_text(page, 8) == lines[7].replace("[id=util]", "[util]")
    assert types_button(page) == "false"
    assert page.evaluate(DOCUMENT_JS) == original

    click_line(page, 13)
    wait_until(lambda: line_text(page, 13) == lines[12], 5.0, "the cursor's line in full")
    assert line_text(page, 21) == "[cntn_to_dcsn] {"

    page.click(".bl-types-button")
    wait_until(lambda: line_text(page, 21) == lines[20], 5.0, "line 21 in full")
    assert types_button(page) == "true"
    assert page.evaluate(DOCUMENT_JS) == original


def layout_button(page) -> str:
    """The layout the graph's layout button turns to, its `data-layout`,
    `horizontal` or `vertical` (unit M, Task 7)."""
    return page.get_attribute(".bl-layout-button", "data-layout")


def test_horizontal_lays_the_view_out_left_to_right(page, server, original):
    """The icon button `Lay out from left to right` at the canvas's foot
    lays the view out left to right and then turns to `vertical`; the view
    laid out again still answers a selection with the piece's kernel in the
    panel, and the editor's document is the file's text; a second click
    turns it to `horizontal` again."""
    stage = stage_of(original)
    piece = model.piece(stage, "backward", "cntn_to_dcsn:Pullback")
    open_cons(page, server)
    assert layout_button(page) == "horizontal"

    laid_out = len(record(page, "processed"))
    page.click(".bl-layout-button")
    wait_until(lambda: layout_button(page) == "vertical", 5.0, "the button reads vertical")
    page.wait_for_function(f"() => window.record.processed.length > {laid_out}", timeout=15_000)
    select_node(page, "cntn_to_dcsn:Pullback", "backward")
    page.wait_for_selector(".bl-kernel", timeout=10_000)
    wait_until(
        lambda: page.locator(".bl-kernel").text_content() == piece.kernel,
        10.0,
        "the piece's kernel after the layout",
    )
    assert page.evaluate(DOCUMENT_JS) == original

    page.click(".bl-layout-button")
    wait_until(lambda: layout_button(page) == "horizontal", 5.0, "the button reads horizontal")


def test_zoom_buttons_scale_the_view_within_scale_one_and_fit_shows_the_whole_graph(page, server, original):
    """Spec 0.4 §2.2: zoom is at most one; fit shows every box and keeps the text."""
    open_cons(page, server)
    wait_until(lambda: viewport(page) is not None, 10.0, "the view's zoom state")
    opened = viewport(page)["zoom"]
    page.click(".bl-zoom-button[data-zoom='zoom out']")
    wait_until(lambda: viewport(page)["zoom"] < opened, 5.0, "the view zoomed out")
    smaller = viewport(page)["zoom"]
    page.click(".bl-zoom-button[data-zoom='zoom in']")
    wait_until(lambda: viewport(page)["zoom"] > smaller, 5.0, "the view zoomed in")
    for _ in range(6):
        page.click(".bl-zoom-button[data-zoom='zoom in']")
    assert viewport(page)["zoom"] <= 1
    page.click(".bl-zoom-button[data-zoom='fit']")
    wait_until(lambda: page.evaluate(WHOLE_GRAPH_SHOWN_JS), 5.0, "the graph fitted again")
    assert viewport(page)["zoom"] <= 1
    assert page.evaluate(DOCUMENT_JS) == original


def test_the_status_line_is_visible_and_more_shows_its_details(page, server, original):
    """The status line is visible (spec 0.4 §5.7; Design brief 7 §13; unit
    R, brief rule 8; R-D9, R-D39): a line 24 px high whose words are set in
    Small, Archivo at 11 px, in ink-3 (design pass 8 §6; unit M, Task 4).
    With the cursor put before `:=` on line 8 it prints the place `8:12`,
    `cons.bl`, the occurrence the occurrence line names, the square, the
    Codicon `pass-filled`, in mint, `constructed` with the first seven
    characters of the file's digest, `0 refused` in ink-2, `indent 4` and
    `BellmanSym`; the word `constructed` takes the keyboard's focus and
    carries its sentence as its title and its accessible description. The
    details, the line of the inputs' digests, counts and seconds and git's
    line, are hidden behind the icon button `More` and keep their text
    while hidden; `More` shows them, its `aria-expanded` then true and its
    name `Less`, which hides them."""
    open_cons(page, server)
    line = page.locator(".bl-status-summary")
    toggle = page.locator(".bl-status-toggle")
    # the toggle's accessible name, which VSCode Elements' toolbar button
    # gives its own button from its property `label`
    named = toggle.locator("button")
    details = page.locator(".bl-status-lines")
    assert line.is_visible()
    assert [box["height"] for box in boxes(page, ".bl-status-summary")] == [24]
    assert type_of(page, ".bl-status-summary") == [SIZES["small"]]
    assert page.evaluate(COLOR_OF_JS, ".bl-status-summary") == property_color(page, "--bl-ice-3")
    # the column of `:=` on line 8, counted in code points from one
    column = original.split("\n")[7].index(":=") + 1
    place = f"8:{column}"
    click_before(page, 8, ":=")
    wait_until(lambda: status_place(page) == place, 5.0, f"the place {place}")
    parts = {
        name: page.locator(f".bl-status-summary .bl-status-{name}").text_content()
        for name in ("file", "stage", "state", "digest", "refused", "indent", "language")
    }
    assert parts == {
        "file": "cons.bl",
        "stage": recipe_head(page),
        "state": "constructed",
        "digest": digest7(original),
        "refused": "0 refused",
        "indent": "indent 4",
        "language": "BellmanSym",
    }
    square = ".bl-status-summary .bl-status-square"
    assert page.get_attribute(square, "data-state") == "constructed"
    assert page.evaluate(COLOR_OF_JS, square) == property_color(page, "--bl-mint")
    refused = ".bl-status-summary .bl-status-refused"
    assert page.evaluate(COLOR_OF_JS, refused) == property_color(page, "--bl-ice-2")
    state = page.locator(".bl-status-summary .bl-status-state")
    sentence = "The language's check, not a verification of the economics."
    assert [state.get_attribute(name) for name in ("title", "aria-description")] == [sentence] * 2
    state.focus()
    assert page.locator(".bl-status-summary .bl-status-state:focus").count() == 1

    assert toggle.get_attribute("aria-expanded") == "false"
    assert named.get_attribute("aria-label") == "More"
    assert toggle.get_attribute("icon") == "chevron-up"
    assert not details.is_visible()
    assert " · constructed · " in status_text(page)
    toggle.click()
    wait_until(lambda: details.is_visible(), 5.0, "the details shown")
    assert toggle.get_attribute("aria-expanded") == "true"
    assert named.get_attribute("aria-label") == "Less"
    assert toggle.get_attribute("icon") == "chevron-down"
    assert page.locator(".bl-git-line").is_visible()
    toggle.click()
    wait_until(lambda: not details.is_visible(), 5.0, "the details hidden")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert named.get_attribute("aria-label") == "More"
    assert line.is_visible()


def test_hide_types_draws_a_refused_line_in_full(page, server, original):
    """With the types hidden, `!arvl` typed as `!arvx` on line 13, inside the
    header's hidden tail, is refused at line 13, column 30; with the cursor
    moved to line 1, line 13 is still drawn in full, the refused word
    underlined at its position, while line 17 is drawn as its name: a line
    holding a refusal is drawn in full, as the cursor's line is."""
    refused_line = "[id=arvl_to_dcsn, (m : Xm) : !arvx -> (m_d : Xm) : !dcsn] {"
    (diagnostic,) = model.elaborate_buffer(edited(original, 13, refused_line), CONS).diagnostics
    assert (diagnostic.line, diagnostic.column) == (13, 30)

    open_cons(page, server)
    page.click(".bl-types-button")
    wait_until(lambda: line_text(page, 13) == "[arvl_to_dcsn] {", 5.0, "line 13 as its name")
    click_line(page, 13)
    page.keyboard.press("End")
    for _ in " -> (m_d : Xm) : !dcsn] {":
        page.keyboard.press("ArrowLeft")
    page.keyboard.press("Backspace")
    page.keyboard.type("x")
    assert line_text(page, 13) == refused_line
    page.wait_for_selector(".cm-content .cm-lintRange-error", timeout=8_000)

    click_line(page, 1)
    wait_until(lambda: active_line(page) == 1, 5.0, "the cursor on line 1")
    wait_until(lambda: line_text(page, 17) == "[dcsn_to_cntn] {", 5.0, "line 17 as its name")
    assert line_text(page, 13) == refused_line
    underlined = page.evaluate(LINT_RANGE_JS)
    assert (underlined["line"], underlined["column"], underlined["text"]) == (13, 30, "!arvx")


def test_lines_wrap_at_column_78(browser, server, original):
    """In a window wide enough for 78 columns, line 21 of cons.bl, of 120
    characters, is drawn on two visual lines of at most 78 characters each,
    and line 13, of 59, on one. A wrapped line hangs by four characters
    (spec 0.4 §5.4): the text's box is 74 characters of the monospaced face
    wide, so that the first visual line, which the text indent widens by
    the four, holds at most 78 (R-D5), and the second visual line of line
    21 starts four characters to the right of its first. No guide is drawn
    after the column (§5.4). The editor's document is the file's text, so
    the wrap inserted no newline."""
    context = browser.new_context(viewport={"width": 2200, "height": 1000})
    try:
        page = context.new_page()
        open_cons(page, server)
        visual_lines = page.evaluate(VISUAL_LINES_JS, 21)
        counts = [row["count"] for row in visual_lines]
        print(f"line 21 is drawn as visual lines of {counts} characters")
        assert len(counts) == 2 and max(counts) <= 78
        assert sum(counts) == len(original.split("\n")[20]) == 120
        assert [row["count"] for row in page.evaluate(VISUAL_LINES_JS, 13)] == [59]
        width, column = page.evaluate(TEXT_WIDTH_JS)
        assert abs(width + 4 * column - 78 * column) < 1, (width, column)
        lefts = [row["left"] for row in visual_lines]
        assert abs(lefts[1] - lefts[0] - 4 * column) < 1, (lefts, column)
        assert page.evaluate(GUIDE_JS) == "none"
        assert page.evaluate(DOCUMENT_JS) == original
    finally:
        context.close()


def test_card_button_copies_the_card(page, server, original):
    """A click on the box `cntn_to_dcsn:Pullback` shows its kernel in the
    panel and not its card; the button `card` writes the card,
    `str(denote())`, to the clipboard, and where the browser refuses the
    clipboard, shows it in the panel in a collapsed block. The clipboard is
    a stand-in installed in the page, which records the text or refuses it,
    so that the machine's clipboard is not touched."""
    piece = model.piece(stage_of(original), "backward", "cntn_to_dcsn:Pullback")
    open_cons(page, server)
    select_node(page, "cntn_to_dcsn:Pullback", "backward")
    wait_until(
        lambda: page.locator(".bl-kernel").count()
        and page.locator(".bl-kernel").text_content() == piece.kernel,
        10.0,
        "the piece's kernel",
    )
    assert piece.card not in page.locator(".bl-panel").text_content()
    assert page.locator(".bl-copy-fallback").count() == 0

    page.evaluate(CLIPBOARD_RECORDS_JS)
    page.click(".bl-card-button")
    copied, _ = wait_until(lambda: page.evaluate("() => window.copiedText"), 5.0, "the copy")
    assert copied == piece.card
    assert page.locator(".bl-copy-fallback").count() == 0

    page.evaluate(CLIPBOARD_REFUSES_JS)
    page.click(".bl-card-button")
    page.wait_for_selector(".bl-copy-fallback", state="attached", timeout=5_000)
    assert page.locator(".bl-copy-fallback .bl-copy-text").text_content() == piece.card
    assert page.evaluate("() => document.querySelector('.bl-copy-fallback').open") is False
    assert piece.card in page.locator(".bl-panel").text_content()


def test_brand_mark_title_and_favicon(page, server, model_folder):
    """The brand's mark, the silhouette
    `bellman_workbench/public/brand/favicon.svg`, stands at the left of the
    main bar, 20 pixels high, and no wordmark is drawn (design pass 10 §3;
    unit N, Task 1); the folder's column is headed `Files`, and the folder's
    name stands in the tree's root row (design pass 8 §6; unit M, Task 6).
    The Files head, the tabs' row and the graph bar begin on one line, under
    the main bar; the tab's title is `<folder> · Bellman Workbench`; the
    favicon Solara's page links is the brand's; the brand's two files equal
    the site's."""
    for name in ("logo.svg", "favicon.svg"):
        assert (BRAND / name).read_bytes() == (SITE_BRAND / name).read_bytes()
    page.goto(server)
    page.wait_for_selector(".bl-tree-file.bl-open", timeout=60_000)
    assert page.title() == f"{model_folder.name} · Bellman Workbench"
    mark = page.locator(".bl-main-bar .bl-mark img")
    assert mark.get_attribute("src").endswith("/static/assets/brand/favicon.svg")
    page.wait_for_function("() => document.querySelector('.bl-mark img').naturalWidth > 0")
    assert mark.bounding_box()["height"] == 20
    assert page.locator(".bl-wordmark").count() == 0
    assert page.locator(".bl-folder-rail > h2").text_content() == "Files"
    assert page.locator(".bl-tree-root").text_content() == model_folder.name
    rows = boxes(page, ".bl-folder-rail, .bl-tab-row, .bl-graph-bar")
    assert len(rows) == 3 and {box["top"] for box in rows} == {36}
    with urllib.request.urlopen(f"{server}static/assets/favicon.svg", timeout=5) as response:
        assert response.read() == (BRAND / "favicon.svg").read_bytes()


# --- unit B ---


def test_b_the_folder_opens_on_its_trellis_and_a_trellis_file_shows_its_own(
    browser, server_on, consport_folder
):
    """The copy of cons-port, which holds no recipe and eight trellis files
    in its `declaration/`, opens on the trellis of the first in name order,
    `declaration/trellis.cons-port.yml`, the file open as text, the
    restriction's select standing, the button `trellis` marked and the select
    `graph` omitted (specification 0.4 §2.1; R-D56); a click on
    `declaration/trellis.port-cons.yml` shows its trellis, the collection
    the element holds equal, character for character, to the view
    `show_trellis` answers, and the status line names the file, the verbs
    and the counts (specification §3.1)."""
    expected = trellis.show_trellis(
        model.open_folder(consport_folder), recipe.Source("recipe", PORT_CONS_RECIPE)
    ).shown
    context, tab = new_tab(browser)
    try:
        url = server_on(consport_folder)
        tab.goto(url)
        first, seconds = wait_until(
            lambda: trellis_settled(tab, CONS_PORT_TRELLIS), 120.0, "the first trellis"
        )
        print(f"the folder opened on {first!r} after {seconds:.1f} s")
        assert open_path_shown(tab) == CONS_PORT_TRELLIS
        assert tab.locator(".bl-restriction").count() == 1
        assert tab.locator(".bl-trellis-button.bl-active").count() == 1
        # the select `graph` stands in the trellis view as well (design pass 14 §7)
        assert tab.locator(".bl-view-kind").count() == 1
        tab.click(f'.bl-tree-file[data-path="{PORT_CONS}"]')
        line, _ = wait_until(
            lambda: trellis_settled(tab, PORT_CONS), 120.0, "the trellis of port-cons.yml"
        )
        wait_for_view(tab, 20, 120_000)
        # the line with the verbs applied, or without them where they head
        # the rest, then the rest, where it stands in the visible line or in
        # the details' line (spec 0.4 §5.7; unit K, Task 6)
        bound = " · calibrated, methodized, configured"
        assert line.startswith(f"{PORT_CONS} · trellis{bound} · loop ") or (
            line.startswith(f"{PORT_CONS} · trellis · loop ") and f" s{bound} · " in line
        ), line
        # no field unjoined outside the earliest period, the two ends not
        # counted (unit L, Task 21)
        assert " · 6 periods, 18 occurrences · 0 unjoined fields" in line
        held = tab.evaluate(HELD_COLLECTION_JS)
        assert as_json(held["graphs"]) == as_json(expected.collection["graphs"])
    finally:
        context.close()


def test_b_a_folder_whose_trellis_the_factory_refuses_opens_on_the_refusal(
    browser, server_on, cagetti_folder
):
    """The Cagetti–De Nardi copy's trellis file, `declaration/trellis.yml`,
    names its stages by key and the folder holds no recipe: the window opens
    on the trellis view with the mark of the factory's refusal in the
    panel, its rule and its address, the sentence standing in the list
    under the error mark with the file and line 12 (AMD-MI-002 §6a rule 1),
    the status line `declaration/trellis.yml · refused`, and the button
    `open at the address` moves the editor to line 12 of that file; the
    stage files still open from the tree with their views (Review Focus
    1)."""
    context, tab = new_tab(browser)
    try:
        tab.goto(server_on(cagetti_folder))
        wait_until(lambda: trellis_settled(tab, TRELLIS_FILE), 120.0, "the refused trellis")
        assert status_text(tab).startswith(f"{TRELLIS_FILE} · refused")
        refusal = tab.locator(".bl-trellis-refusal").text_content()
        sentence = (
            "periods[0].stages is no mapping of keys to records\n"
            "stages: {<key>: {stage: <file>.bl, calibration: ..., settings: ..., methods: ...}}"
        )
        assert "no mapping" not in refusal and "rule trellis-file-shape" in refusal
        wait_until(
            lambda: error_lines(tab) == [(sentence, TRELLIS_FILE, 12)],
            10.0,
            "the factory's sentence in the list under the error mark",
        )
        tab.click(".bl-address-button")
        wait_until(lambda: active_line(tab) == 12, 10.0, "the editor on line 12")
        reveal_in_tree(tab, ENTREPRENEUR_DEATH)
        tab.click(f'.bl-tree-file[data-path="{ENTREPRENEUR_DEATH}"]')
        wait_until(
            lambda: status_text(tab).startswith(f"{ENTREPRENEUR_DEATH} (")
            and " · loop " in status_text(tab),
            60.0,
            "the stage's status line",
        )
        assert "bl-active" not in tab.locator(".bl-trellis-button").get_attribute("class")
    finally:
        context.close()


def test_b_the_restriction_input_restricts_the_view_and_shows_a_refusal_in_one_sentence(
    browser, server_on, consport_folder
):
    """`periods 0–1, stages cons` typed at the foot of the menu of the
    view's bar's restriction shows the two consumption occurrences, the
    element holding the restricted view `show_trellis` answers, and the
    status line names the restriction; `periods 7` marks the select as
    refused, the package's sentence standing in the list under the error
    mark (AMD-MI-002 §6a rule 1), and keeps the view; `periods two` puts the
    parser's sentence in its place, the select printing the text as
    written; `all` in the menu shows every occurrence again and clears the
    mark and the sentence (specification §3.1; Review Focus 2; amendment 02
    ruling 6; unit K, K-D17)."""
    folder = model.open_folder(consport_folder)
    lesson = recipe.Source("recipe", PORT_CONS_RECIPE)
    restricted = trellis.show_trellis(
        folder, lesson, trellis.parse_restriction("periods 0–1, stages cons")
    ).shown
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(consport_folder), PORT_CONS)

        def settled_with(words):
            line = trellis_settled(tab, PORT_CONS)
            return line if line is not None and words in line else None

        restrict(tab, "periods 0–1, stages cons")
        line, _ = wait_until(
            lambda: settled_with("shown periods 0–1, stages cons (2 occurrences)"),
            60.0,
            "the restriction",
        )
        print(f"status line: {line!r}")
        wait_until(
            lambda: as_json(tab.evaluate(HELD_COLLECTION_JS)["graphs"])
            == as_json(restricted.collection["graphs"]),
            30.0,
            "the restricted view",
        )

        def refused():
            # the lines of the list under the error mark, and whether the
            # select is marked as refused, its text the restriction as
            # written
            marked = tab.locator(".bl-restriction.bl-refusal-mark").count() == 1
            return error_lines(tab), marked

        package = "the trellis holds 6 periods, and periods[7] is none of them"
        restrict(tab, "periods 7")
        wait_until(
            lambda: refused() == ([(package, None, None)], True),
            60.0,
            "the package's sentence",
        )
        assert as_json(tab.evaluate(HELD_COLLECTION_JS)["graphs"]) == as_json(
            restricted.collection["graphs"]
        )
        assert "shown periods 0–1, stages cons (2 occurrences)" in status_text(tab)
        parser = "`periods two` is no period range; write `periods 0–2` or `periods 3`"
        restrict(tab, "periods two")
        wait_until(
            lambda: refused() == ([(parser, None, None)], True),
            10.0,
            "the parser's sentence",
        )
        assert restriction_shown(tab) == "periods two"
        choose_restriction(tab, "all")
        wait_until(
            lambda: (lambda line: line if line and " · shown " not in line else None)(
                trellis_settled(tab, PORT_CONS)
            ),
            60.0,
            "the whole trellis",
        )
        wait_until(
            lambda: refused() == ([], False),
            10.0,
            "the mark and the sentence cleared by a valid restriction",
        )
        assert restriction_shown(tab) == "all"
    finally:
        context.close()


def test_b_the_panel_of_the_trellis_lists_the_joins_and_opens_an_occurrences_stage_at_its_block(
    browser, server_on, scratch_consport
):
    """In the trellis of lesson 05 restricted to `periods 0–1, stages cons`,
    the `outside` node at which the continuation value and marginal value of
    `periods[1]/cons` enter the backward graph from `periods[1]/disc`, which
    replaces the trellis's `Inputs` (design pass 10 §6; unit N, Task 6) and
    is one node for that pair of occurrences (design pass 12 §2), lists
    first the value's port with the join `a` and the occurrence outside the
    view; the builder `cntn_to_dcsn` of
    `periods[1]/cons` selected, the button `open at the block` opens the
    occurrence's stage file,
    `../portfolio-choice/declaration/stages/cons/cons.bl`, outside the
    folder, at the block's header, line 21, bound as `periods[1] / cons`,
    which the head names (specification §3.1; Review Focus 4)."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_consport), PORT_CONS)
        restrict(tab, "periods 0–1, stages cons")
        wait_until(
            lambda: (trellis_settled(tab, PORT_CONS) or "").find("(2 occurrences)") > 0,
            60.0,
            "the restriction",
        )
        select_node(tab, "outside:periods[1]/cons:periods[1]/disc", "backward")
        tab.wait_for_selector(".bl-port", timeout=15_000)
        rows = tab.evaluate(PORT_ROWS_JS)
        print(f"the port of the outside node: {rows}")
        assert rows[0]["cells"] == [
            "𝑉≻(a)",
            "cntn",
            "Xa → [−∞, ∞)",
            "value",
            "a",
            "periods[1]/disc",
        ]
        select_node(tab, "periods[1]/cons/cntn_to_dcsn___group___", "backward")
        tab.wait_for_selector(".bl-occurrence-block", timeout=15_000)
        tab.click(".bl-occurrence-block")
        wait_until(
            lambda: open_path_shown(tab) == SHARED_CONS,
            30.0,
            "the stage file",
        )
        wait_until(lambda: active_line(tab) == 21, 30.0, "the editor at the block's header")
        wait_until(lambda: recipe_head(tab) == "periods[1] / cons", 60.0, "the head")
    finally:
        context.close()


# --- unit B, the acceptance items (§12, "B, binding and the trellis") ---


def test_b_item_1_a_methods_file_chosen_for_an_occurrence_binds_it_and_keeps_the_recipe(
    browser, server_on, scratch_lifecycle
):
    """B item 1 (§3.2): in the lifecycle registry,
    `declaration/stages/cons/cons.bl` opened as the occurrence
    `periods[1] / cons` from the trellis; the recipe's document tab opens
    the recipe with the stage's view kept, the panel under the editor on
    its Recipe tab (unit M, Task 10; design pass 9 §§2 to 4; the rail's
    `Recipe` having left with the rail, unit N, Task 1), where the
    methods select of `cons`, its row opened by a click (design pass 11
    §2), holds the slot `$cons_method`; choosing `cons`,
    the file `declaration/methods/cons.yml`, rewrites that entry of the
    recipe's text alone, as `methods/cons`, its path from the recipe's
    folder, its comments and the other entries kept, the stage files
    untouched, and the recipe saved writes it; with `cons.bl` open again,
    the stage's view
    then shows `!egm` on the policy's Evaluation and `!Cartesian` on the
    continuation's, and the trellis holds the same `method` rows at every
    consumption occurrence; `declaration/stages/disc/disc.bl` opened as
    `periods[1] / disc` and as `periods[0] / disc` shows the discount
    factor of each, 0.96 and 0.9."""
    stage_files = {key: f"declaration/stages/{key}/{key}.bl" for key in ("port", "cons", "disc")}
    recipe_text = (scratch_lifecycle / RECIPE_FILE).read_text(encoding="utf-8")
    stage_texts = {
        key: (scratch_lifecycle / path).read_text(encoding="utf-8")
        for key, path in stage_files.items()
    }
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_lifecycle), RECIPE_FILE, minimum=10)

        def in_trellis():
            # the restriction's select stands in the trellis view alone; the
            # button `trellis` is not shown there while no stage file is open
            return tab.locator(".bl-restriction").count() > 0

        def open_occurrence(address, stage_file):
            if not in_trellis():
                # the button shows the trellis with the open stage's
                # occurrence selected (amendment 02 ruling 3), which the
                # view selects in a layout of its own after it has drawn the
                # trellis; the next selection waits for that layout
                layer = recipe_head(tab).replace(" / ", "/") + "___group___"
                record_view_state(tab)
                tab.click(".bl-trellis-button")
                wait_until(
                    lambda: in_trellis() and (view_state(tab) or {}).get("selected") == layer,
                    60.0,
                    "the open stage's occurrence selected in the trellis",
                )
            select_until(
                tab,
                f"{address}___group___",
                "backward",
                lambda: panel_head(tab).startswith(occurrence_head(address)),
                f"the panel of {address}",
            )
            # the button `open the stage` stands in the trellis's panel alone,
            # so a click that landed leaves the trellis view
            click_until(tab, ".bl-occurrence-open", lambda: not in_trellis(), "the stage view")
            wait_until(
                lambda: recipe_head(tab) == address.replace("/", " / "),
                60.0,
                f"the stage of {address}",
            )
            wait_until(
                lambda: status_text(tab).startswith(f"{stage_file} (")
                and " · loop " in status_text(tab),
                60.0,
                f"the loop of {stage_file}",
            )
            # the view's element is created again once the stage of the file
            # opened stands, a moment after the head names the occurrence
            wait_for_view(tab, 4, 60_000)

        def row(node_id, key):
            select_node(tab, node_id, "backward")
            return dict(tab.evaluate(ATTRIBUTE_ROWS_JS)).get(key)

        open_occurrence("periods[1]/cons", CONS)
        tab.click(f'.bl-tab[data-path="{RECIPE_FILE}"]')
        wait_until(lambda: open_path_shown(tab) == RECIPE_FILE, 30.0, "the recipe open")
        open_recipe_row(tab, "cons")
        entry = '.bl-recipe-entry[data-address="stages.cons.methods.all[0]"]'
        chosen = f"{entry} vscode-option[selected]"
        tab.wait_for_selector(chosen, state="attached", timeout=30_000)
        assert tab.locator(chosen).text_content().strip() == "$cons_method"
        choose_option(tab, entry, "cons")
        rewritten = recipe_text.replace("$cons_method", "methods/cons")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == rewritten, 15.0, "the text rewritten")
        tab.click(".bl-save")
        wait_until(
            lambda: (scratch_lifecycle / RECIPE_FILE).read_text(encoding="utf-8") == rewritten,
            15.0,
            "the recipe rewritten",
        )
        tab.click(f'.bl-tab[data-path="{CONS}"]')
        wait_until(lambda: open_path_shown(tab) == CONS, 30.0, "cons.bl open again")
        assert {
            key: (scratch_lifecycle / path).read_text(encoding="utf-8")
            for key, path in stage_files.items()
        } == stage_texts
        wait_until(
            lambda: " · methods " in status_text(tab), 90.0, "the stage bound with its methods"
        )
        wait_until(
            lambda: row("policy:Evaluation", "method") == "!egm",
            30.0,
            "!egm on the policy's Evaluation",
        )
        wait_until(
            lambda: row("cntn_to_dcsn:Evaluation", "method") == "!Cartesian", 30.0, "!Cartesian"
        )
        folder = model.open_folder(scratch_lifecycle)
        whole = trellis.show_trellis(folder, recipe.Source("recipe", RECIPE_FILE)).shown
        own = model.collection(
            model.elaborate_buffer(stage_texts["cons"], "cons.bl").stage.methodize(
                str(scratch_lifecycle / "declaration/methods/cons.yml")
            )
        )
        for h in range(3):
            for node_id in ("policy:Evaluation", "cntn_to_dcsn:Evaluation"):
                held = model.node_attributes(
                    whole.collection, "backward", f"periods[{h}]/cons/{node_id}"
                )
                assert held["method"] == model.node_attributes(own, "backward", node_id)["method"]
        for address, value in (("periods[1]/disc", "0.96"), ("periods[0]/disc", "0.9")):
            open_occurrence(address, DISC)
            wait_until(
                lambda: row("cntn_to_dcsn___group___", "parameter") == f"β = {value} : (0, 1)",
                30.0,
                f"β of {address}",
            )
    finally:
        context.close()


def test_b_item_2_the_trellis_of_port_cons_is_drawn_read_again_once_and_restricted(
    browser, server_on, scratch_consport
):
    """B item 2 (§3.1): the trellis of `declaration/trellis.port-cons.yml` is
    drawn as `show_trellis` draws it, each period open to its stages; the
    shared consumption file, outside the folder, opened from an occurrence
    and saved, is read again once, its six occurrences constructed again and
    the twelve others copied; the calibration, opened from the tree and
    saved, binds its new discount factor at the discount occurrences; the
    restriction `periods 0–1, stages cons` shows the two consumption
    occurrences with the joins that leave them at the view's inputs and
    outputs. The equality of the stage view of the head's occurrence and the
    trellis's occurrence is
    `test_b_item_2_the_stage_view_of_the_heads_occurrence_equals_the_trellis_view_up_to_the_joins`."""
    folder = model.open_folder(scratch_consport)
    lesson = recipe.Source("recipe", PORT_CONS_RECIPE)
    expected = trellis.show_trellis(folder, lesson).shown
    assert expected.layers["backward"][:3] == [
        "periods[5]/port",
        "periods[5]/cons",
        "periods[5]/disc",
    ]
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_consport), PORT_CONS)
        assert as_json(tab.evaluate(HELD_COLLECTION_JS)["graphs"]) == as_json(
            expected.collection["graphs"]
        )
        select_until(
            tab,
            "periods[1]/cons___group___",
            "backward",
            lambda: tab.locator(".bl-occurrence-open").count() > 0,
            "the panel of periods[1]/cons",
        )
        click_until(
            tab,
            ".bl-occurrence-open",
            lambda: open_path_shown(tab) == SHARED_CONS,
            "the shared consumption file",
        )
        wait_until(lambda: " · loop " in status_text(tab), 60.0, "the stage's loop")
        # each of the two clicks is repeated until its effect is seen, since a
        # click that lands while the page renders again is lost (`click_until`)
        click_until(
            tab,
            ".cm-content .cm-line >> nth=0",
            lambda: active_line(tab) == 1
            and tab.locator(".bl-editor .cm-editor.cm-focused").count() == 1,
            "the cursor on line 1 of the focused editor",
        )
        tab.keyboard.press("ControlOrMeta+End")
        tab.keyboard.type("\n# a note on the consumption stage")
        # the shared consumption file is the demonstration's since decision
        # SD-39, as SHARED_CONS names it (SE-33)
        shared = (
            scratch_consport / "declaration/stages/cons/cons.bl"
        )
        click_until(
            tab,
            ".bl-save",
            lambda: "# a note" in shared.read_text(encoding="utf-8"),
            "the file saved",
            15.0,
        )
        tab.click(".bl-trellis-button")

        def trellis_line_with(words):
            line = trellis_settled(tab, PORT_CONS)
            return line if line is not None and words in line else None

        wait_until(
            lambda: trellis_line_with("6 occurrences elaborated or bound again"),
            120.0,
            "the trellis read again",
        )
        reveal_in_tree(tab, PORTFOLIO_CALIBRATION)
        tab.click(f'.bl-tree-file[data-path="{PORTFOLIO_CALIBRATION}"]')
        wait_until(
            lambda: open_path_shown(tab) == PORTFOLIO_CALIBRATION,
            30.0,
            "the calibration",
        )
        click_line(tab, 4)
        tab.keyboard.press("End")
        tab.keyboard.press("Backspace")
        tab.keyboard.type("5")
        tab.click(".bl-save")
        calibration = scratch_consport / PORTFOLIO_CALIBRATION
        wait_until(
            lambda: "β: 0.95" in calibration.read_text(encoding="utf-8"),
            15.0,
            "the calibration saved",
        )
        select_until(
            tab,
            "periods[1]/disc/cntn_to_dcsn___group___",
            "backward",
            lambda: dict(tab.evaluate(ATTRIBUTE_ROWS_JS)).get("parameter") == "β = 0.95 : (0, 1)",
            "the new discount factor bound",
            seconds=120.0,
        )
        restrict(tab, "periods 0–1, stages cons")
        wait_until(
            lambda: trellis_line_with("shown periods 0–1, stages cons (2 occurrences)"),
            60.0,
            "the restriction",
        )
        restricted = trellis.show_trellis(
            folder, lesson, trellis.parse_restriction("periods 0–1, stages cons")
        ).shown
        wait_until(
            lambda: as_json(tab.evaluate(HELD_COLLECTION_JS)["graphs"])
            == as_json(restricted.collection["graphs"]),
            30.0,
            "the restricted view",
        )
    finally:
        context.close()


def test_b_item_3_the_marked_entries_no_slot_and_a_connector_that_names_no_field(
    browser, server_on, lifecycle_folder, refused_pension
):
    """B item 3 (§4; §2.2 rule 2), with unit K's decisions K-D28 and K-D29:
    the lifecycle registry's empty connector, which its answers mark
    required, is the one entry to check of the checklist, apart from the
    refusals; its slot `$cons_method`, which its answers also list, is no
    entry: the status line and the tree count nothing, the slot stands in
    its select in the Recipe tab (unit M, Task 10), cons's row opened by a
    click (design pass 11 §2), with no refusal's mark, and the slots'
    keywords are `cons_method`. A copy of the pension model
    whose terminal period's connector names a field no stage declares opens on
    the factory's refusal, and `open at the address` opens
    `declaration/trellis.yml` at line 17, that connector."""
    context, tab = new_tab(browser)
    try:
        line = open_trellis(tab, server_on(lifecycle_folder), RECIPE_FILE, minimum=10)
        assert " · loop " in line and "to fill" not in line and "refused" not in line
        wait_until(lambda: checklist_count(tab) == 1, 30.0, "the one entry to check")
        entry = tab.locator(".bl-checklist-entry")
        assert (entry.get_attribute("data-file"), entry.text_content().strip()) == (
            PERIOD_FILE,
            "period.yml · connectors[0]",
        )
        assert "to fill" not in tab.locator(".bl-status-line").text_content()
        assert "to fill" not in tab.locator(".bl-tree").text_content()
        open_recipe_row(tab, "cons")
        slot = '.bl-recipe-entry[data-address="stages.cons.methods.all[0]"]'
        assert tab.locator(f"{slot} vscode-option[selected]").text_content() == "$cons_method"
        assert tab.locator(f"{slot} .bl-refusal-mark").count() == 0
        assert not [
            entry for entry in tab.evaluate(ORANGE_ELEMENTS_JS) if "bl-recipe-entry" in entry
        ]
        assert slot_keywords(tab) == ["cons_method"]
    finally:
        context.close()
    context, tab = new_tab(browser)
    try:
        tab.goto(server_on(refused_pension))
        wait_until(lambda: trellis_settled(tab, RECIPE_FILE), 120.0, "the refused trellis")
        refusal = tab.locator(".bl-trellis-refusal").text_content()
        assert "rule connector-names-no-field" in refusal and "periods[0].connectors[0]" in refusal
        tab.click(".bl-address-button")
        wait_until(
            lambda: open_path_shown(tab) == TRELLIS_FILE,
            30.0,
            "the trellis file open",
        )
        wait_until(lambda: active_line(tab) == 17, 15.0, "the editor on the connector's line")
    finally:
        context.close()


def test_b_item_4_the_name_under_the_cursor_lists_its_occurrences_calibration_line_and_boxes(
    browser, server_on, lifecycle_folder
):
    """B item 4 (§3.2): `declaration/stages/cons/cons.bl` of the lifecycle
    registry, bound as `periods[0] / cons`; the cursor on `ρ` at line 6
    lists its five occurrences, `6:1  declaration` first, the line of the
    calibration that sets it, line 5 of
    `declaration/calibration/portfolio.yml`, which opens that file there,
    and the six boxes that depend on it: the two whose kernels'
    `parameters` hold it and the four whose records reach it through the
    definitions of the values their wires carry."""
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(lifecycle_folder), CONS, minimum=4)
        click_line(tab, 6)
        tab.keyboard.press("Home")
        wait_until(
            lambda: tab.locator(".bl-name").count()
            and "ρ" in tab.locator(".bl-name").text_content(),
            15.0,
            "the name",
        )
        occurrences = tab.locator(".bl-name-occurrences li").all_text_contents()
        assert occurrences[0] == "6:1  declaration" and len(occurrences) == 5
        assert tab.locator(".bl-name-boxes li").all_text_contents() == [
            "cntn_to_dcsn:Aggregation",
            "cntn_to_dcsn:Evaluation",
            "dcsn_to_arvl:Pullback",
            "policy.InvEuler:Aggregation",
            "policy.endoggrid:Aggregation",
            "policy.cons_choice:Pullback",
        ]
        tab.click(".bl-name-calibration .bl-link")
        wait_until(
            lambda: open_path_shown(tab) == PORTFOLIO_CALIBRATION,
            30.0,
            "the calibration",
        )
        wait_until(lambda: active_line(tab) == 5, 15.0, "the line that sets ρ")
    finally:
        context.close()


def test_b_item_5_the_pension_trellis_draws_its_forward_graph_and_links_its_refusing_node(
    browser, server_on, pension_folder
):
    """B item 5 (§3.1): the pension trellis, of fifteen periods, opens on
    `periods 0–2`, and `all` in the restriction's menu shows it whole; its
    forward graph is drawn; its backward graph is the one refusing node,
    whose panel lists sixty joins,
    the first linked to line 22 of
    `declaration/stages/retire_choice/retire_choice.bl`, the header that
    declares its two unpaired marginal values, and to line 27 of
    `declaration/trellis.yml`, the connector; restricted to `periods 1–1`,
    the backward graph is drawn as the package draws it, every drawn join's
    port naming its pairing rule
    (`test_b_item_5_every_drawn_backward_join_names_the_rule_that_paired_it`)."""
    folder = model.open_folder(pension_folder)
    restricted = trellis.show_trellis(
        folder, recipe.Source("recipe", RECIPE_FILE), trellis.parse_restriction("periods 1–1")
    ).shown
    context, tab = new_tab(browser)
    try:
        tab.goto(server_on(pension_folder))
        wait_until(lambda: trellis_settled(tab, RECIPE_FILE), 120.0, "the pension trellis")
        choose_restriction(tab, "all")
        wait_until(
            lambda: (lambda line: line if line and " · shown " not in line else None)(
                trellis_settled(tab, RECIPE_FILE)
            ),
            120.0,
            "the whole pension trellis",
        )
        choose_view(tab, None, "forward")
        wait_for_view(tab, 20, 60_000)
        choose_view(tab, None, "backward")
        select_until(
            tab,
            "backward:refused",
            "backward",
            lambda: tab.locator(".bl-unpaired").count() > 0,
            "the refusing node's panel",
        )
        assert tab.locator(".bl-unpaired").count() == 60
        links = tab.locator(".bl-unpaired").first.locator(".bl-link")
        assert [links.nth(n).get_attribute("data-line") for n in range(links.count())] == [
            "22",
            "22",
            "27",
        ]
        links.first.click()
        wait_until(
            lambda: open_path_shown(tab) == RETIRE_CHOICE,
            30.0,
            "the stage file",
        )
        wait_until(lambda: active_line(tab) == 22, 15.0, "the header's line")
        links.nth(2).click()
        wait_until(
            lambda: open_path_shown(tab) == TRELLIS_FILE,
            30.0,
            "the trellis file",
        )
        wait_until(lambda: active_line(tab) == 27, 15.0, "the connector's line")
        restrict(tab, "periods 1–1")
        wait_until(
            lambda: "shown periods 1" in (trellis_settled(tab, RECIPE_FILE) or ""),
            60.0,
            "the restriction",
        )
        wait_until(
            lambda: as_json(tab.evaluate(HELD_COLLECTION_JS)["graphs"])
            == as_json(restricted.collection["graphs"]),
            30.0,
            "the restricted backward graph",
        )
    finally:
        context.close()


# --- unit M, the Matsya window ---


def test_m_item_3_the_column_stands_open_at_the_right_and_folds_by_its_button(
    page, server, original
):
    """The window is Matsya's column (spec 0.4 §§5.1 and 5.6; unit R, brief
    rules 2, 3 and 8): it stands right of the graph's column, from the
    window's first row to its foot, open when the page opens. Its head
    holds the heading `Matsya`, Υ and the icon button `Fold Matsya`, its
    `aria-expanded` true (design pass 8 §6); its body holds the text area
    and the icon button `Ask`.
    The fold button folds the column, which is then not drawn and takes no
    width, and the main bar's toggle `Matsya` opens it again (unit K's
    decision K-D19; unit N, Task 1; design pass 10 §3). No word of the
    viewer's and
    no banner stands on the page with the column in it."""
    open_cons(page, server)
    view = page.locator(".bl-view").bounding_box()
    column = page.locator(".bl-matsya").bounding_box()
    main_bar = page.locator(".bl-main-bar").bounding_box()
    status = page.locator(".bl-status").bounding_box()
    assert column["x"] >= view["x"] + view["width"]
    assert abs(column["y"] - main_bar["y"]) < 1
    assert abs(column["y"] + column["height"] - status["y"] - status["height"]) < 1
    heading = page.locator(".bl-matsya-head h2")
    assert heading.text_content() == "Matsya"
    assert page.locator(".bl-matsya-head .bl-matsya-upsilon").text_content() == "Υ"
    fold = page.locator(MATSYA_FOLD)
    assert [fold.get_attribute(name) for name in ("label", "title", "aria-expanded")] == [
        "Fold Matsya",
        "Fold Matsya",
        "true",
    ]
    exchanges = page.locator(".bl-matsya-exchanges")
    assert exchanges.is_visible()
    assert page.locator(".bl-matsya-field textarea").is_visible()
    assert page.locator(".bl-matsya-ask").is_visible()
    drawn = page.evaluate(DRAWN_TEXT_JS, ".bl-window")
    assert all(word not in drawn for word in FOREIGN_WORDS)
    fold.click()
    wait_until(lambda: not exchanges.is_visible(), 5.0, "the column folded")
    assert fold.get_attribute("aria-expanded") == "false"
    assert not heading.is_visible()
    assert boxes(page, ".bl-matsya")[0]["width"] == 0
    toggle = page.locator(MATSYA_TOGGLE)
    assert toggle.is_visible() and toggle.get_attribute("aria-expanded") == "false"
    toggle.click()
    wait_until(lambda: exchanges.is_visible(), 5.0, "the column open")
    assert fold.get_attribute("aria-expanded") == "true"


def test_m_item_1_a_question_is_answered_with_its_passages_and_the_page_stays_live(
    page, server, model_folder, original
):
    """A question typed in the column and sent with the Enter key is listed
    with the line `Answering`, the field emptied and the button
    `Ask` waiting, `aria-disabled`. While the stand-in waits five seconds,
    a click on `port.bl` opens that file, and the column is folded by its
    button; the answer is written under its question while the column is
    folded, and
    the column opened again by the main bar's toggle `Matsya` (unit K's
    decision K-D19; unit N, Task 1) shows it: the stand-in's text, which
    names the
    question, the conversation and the client's default model, and its two
    passages, one line each; `Ask` acts again. The conversation is
    named by the first twelve characters of the SHA-256 digest of the
    folder's path, and the folder's name stands nowhere in what the client
    read (spec 0.4 §6, decision 32; R-D21)."""
    question = "What does a stage file denote? wait"
    session = hashlib.sha256(str(model_folder.resolve()).encode("utf-8")).hexdigest()[:12]
    open_cons(page, server)
    # port.bl's folder opened before the question, so that the click on
    # the file falls within the stand-in's wait
    reveal_in_tree(page, PORT)
    fold = page.locator(MATSYA_FOLD)
    field = page.locator(".bl-matsya-field textarea")
    field.fill(question)
    field.press("Enter")
    wait_until(lambda: page.locator(".bl-matsya-question").count() == 1, 5.0, "the question")
    assert page.locator(".bl-matsya-question").text_content() == question
    assert page.locator(".bl-matsya-pending").count() == 1
    assert page.get_attribute(".bl-matsya-ask", "aria-disabled") == "true"
    wait_until(lambda: field.input_value() == "", 5.0, "the field emptied")
    page.click(f'.bl-tree-file[data-path="{PORT}"]')
    wait_until(
        lambda: open_path_shown(page) == PORT,
        4.0,
        "port.bl open while Matsya answers",
    )
    assert page.locator(".bl-matsya-pending").count() == 1
    fold.click()
    wait_until(
        lambda: page.locator(".bl-matsya-answer").count() == 1,
        20.0,
        "the answer, the column folded",
    )
    page.click(MATSYA_TOGGLE)
    answer = page.locator(".bl-matsya-answer")
    wait_until(lambda: answer.is_visible(), 5.0, "the answer shown")
    text = answer.text_content()
    assert text.startswith("Υ reads the stage file into the operators 𝑉 ∘ g.")
    assert f"question: {question}" in text
    assert f"session: {session}" in text
    assert model_folder.name not in text
    assert "model: the client's default" in text
    assert page.locator(".bl-matsya-passage").all_text_contents() == list(STUB_PASSAGES)
    assert page.get_attribute(".bl-matsya-ask", "aria-disabled") is None


def test_m_item_2_a_silent_service_is_told_in_one_sentence(page, server, original):
    """The stand-in answers as the client answers for a service that does
    not answer, the exit status 1 and its own sentence on standard error,
    which names the service's address. The column shows under the question
    the one sentence NO_ANSWER and no passage, and no word of the client's
    sentence stands on the page; the Workbench works as before: a click on
    `port.bl` opens it and its reading ends `constructed`."""
    open_cons(page, server)
    page.locator(".bl-matsya-field textarea").fill("Is the service silent?")
    page.click(".bl-matsya-ask")
    wait_until(lambda: page.locator(".bl-matsya-answer").count() == 1, 10.0, "the sentence")
    assert page.locator(".bl-matsya-answer").text_content() == matsya_client.NO_ANSWER
    assert page.locator(".bl-matsya-passage").count() == 0
    drawn = page.evaluate(DRAWN_TEXT_JS, ".bl-window")
    assert "matsya.invalid" not in drawn and "Could not connect" not in drawn
    reveal_in_tree(page, PORT)
    page.click(f'.bl-tree-file[data-path="{PORT}"]')
    wait_until(lambda: status_settled_on(page, PORT), 60.0, "the loop of port.bl")
    assert " · constructed · " in status_text(page)


def test_m_item_5_upsilon_is_periwinkle_and_nothing_is_orange_without_a_refusal(
    page, server, original
):
    """With the column open and no refusal standing, Matsya's Υ is text
    drawn in periwinkle, and the column draws no image (spec 0.4 §§5.1 and
    5.7; unit R, brief rule 8); no element of the page is drawn in the
    brand's orange, #ED762D, in its color, its ground, a border or an
    outline (spec 0.4 §5.7: orange is the color of a refusal alone), but
    the problems count, orange while errors or checks stand (design pass
    13 §5; Q-D8), the legend's swatches among them, one for each of the
    three levels the backward graph draws, in sentence case (§3; C12)."""
    open_cons(page, server)
    assert page.locator(".bl-matsya-upsilon").text_content() == "Υ"
    upsilon = page.evaluate(COLOR_OF_JS, ".bl-matsya-upsilon")
    assert upsilon == property_color(page, "--bl-periwinkle")
    assert page.locator(".bl-matsya img").count() == 0
    levels = page.locator('.bl-legend-group[data-group="levels"] .bl-legend-text')
    drawn = ["Builder", "Primitive operator", "Builder's output"]
    wait_until(lambda: levels.all_text_contents() == drawn, 10.0, "the legend's three levels")
    assert page.locator(".bl-legend-swatch").count() == 3
    assert orange_marks(page) == ({"error mark"} if error_count(page) else set())


# --- AMD-MI-001, the legend and the colors ---

# The legend's groups as the page draws them: each group's key with its
# entries, each entry's text with the computed fill and border of its
# swatch, both None for an entry drawn with none.
LEGEND_GROUPS_JS = """
() => Array.from(document.querySelectorAll('.bl-legend-group'), (group) => [
  group.dataset.group,
  Array.from(group.querySelectorAll('.bl-legend-item'), (item) => {
    const swatch = item.querySelector('.bl-legend-swatch');
    const style = swatch ? getComputedStyle(swatch) : null;
    return [
      item.querySelector('.bl-legend-text').textContent,
      style ? style.backgroundColor : null,
      style ? style.borderTopColor : null,
    ];
  }),
])
"""

# --- unit G, the graph drawn in the page: the plan's Review Focus ---


def test_g_the_mathematical_font_is_requested_while_elk_is_loading(
    browser, server_on, scratch_durables
):
    """STIX is requested before ELK is available, then the durables stage
    draws mathematical labels with the bundled font."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    url = server_on(scratch_durables)
    print("STIX phase: request before ELK", flush=True)
    context, page = new_tab(browser)
    try:
        elk_pattern = "**/flow/elk.bundled.js"
        font_pattern = "**/flow/stix-two-math-latin-400-normal.woff2"
        held = []
        font_requests = []

        def hold_elk(route):
            held.append(route)

        def record_font(request):
            if request.url.endswith("/flow/stix-two-math-latin-400-normal.woff2"):
                font_requests.append(request)

        page.on("request", record_font)
        page.route(elk_pattern, hold_elk)
        missing_font = None
        phase = "font wait registration"
        primary_error = None
        released = 0
        try:
            with page.expect_request(font_pattern, timeout=15_000):
                phase = "navigation"
                page.goto(url, wait_until="domcontentloaded")
                phase = "ELK prerequisite"
                wait_until(
                    lambda: page.evaluate(
                        "() => document.querySelector('#bellman-elk-script') !== null"
                    ) and bool(held),
                    15.0,
                    "the withheld ELK request",
                )
                phase = "font request"
        except Exception as error:
            primary_error = {"type": type(error).__name__, "message": str(error)}
            if phase != "font request" or not isinstance(error, PlaywrightTimeoutError):
                raise
            missing_font = str(error)
        finally:
            print("STIX observation before release:", json.dumps({
                "phase": phase,
                "primary_error": primary_error,
                "held_elk_requests": len(held),
                "font_requests": [request.url for request in font_requests],
                "font_wait_error": missing_font,
            }, sort_keys=True), flush=True)
            try:
                for route in held:
                    route.continue_()
                    released += 1
            finally:
                page.unroute(elk_pattern, hold_elk)
        print("STIX request before ELK:", json.dumps({
            "held_elk_requests": len(held),
            "released_elk_requests": released,
            "font_requests": [request.url for request in font_requests],
            "font_wait_error": missing_font,
        }, sort_keys=True))
        assert len(held) == released == 1
        assert missing_font is None, "STIX was not requested while ELK was withheld: " + missing_font

    finally:
        context.close()

    # Routing disables the HTTP cache; use a separate context for ordinary loading.
    print("STIX phase: ordinary loading", flush=True)
    font_requests = []
    context, page = new_tab(browser)
    try:
        page.on("request", record_font)
        page.goto(url, wait_until="domcontentloaded")
        selector = f'.bl-tree-file[data-path="{KEEPER_CONS}"]'
        reveal_in_tree(page, KEEPER_CONS, timeout=60_000)
        page.click(selector)
        wait_until(
            lambda: status_settled_on(page, KEEPER_CONS),
            60.0,
            f"the loop of {KEEPER_CONS}",
        )
        wait_for_view(page, timeout=60_000)
        assert page.evaluate("""() => [...document.fonts].some(face =>
          face.family.replaceAll('"', '') === 'STIX Two Math' && face.status === 'loaded')""")
        drawn = fonts_drawn(page)
        assert drawn
        assert any("STIX Two Math (custom)" in faces for faces in drawn.values())
        bundled = {"IBM Plex Mono (custom)", "STIX Two Math (custom)"}
        # Wire titles and accessibility descriptions can have no drawn glyphs.
        assert all(faces <= bundled for faces in drawn.values()), drawn

        resources = page.evaluate("""() => performance.getEntriesByType('resource')
          .filter(entry => entry.name.endsWith('/flow/stix-two-math-latin-400-normal.woff2'))
          .map(entry => entry.toJSON())""")
        request_records = [
            {"url": request.url, "method": request.method, "resource_type": request.resource_type}
            for request in font_requests
        ]
        expected_url = url + "static/assets/flow/stix-two-math-latin-400-normal.woff2"
        print("STIX requests, resources and drawing:", json.dumps({
            "phase": "ordinary loading",
            "expected_url": expected_url,
            "requests": request_records,
            "resources": resources,
            "drawn": {text: sorted(faces) for text, faces in drawn.items()},
        }, sort_keys=True), flush=True)
        transfers = [entry for entry in resources if entry["transferSize"] > 0]
        assert len(transfers) == 1, resources
        transfer = transfers[0]
        assert transfer is resources[0] and transfer["initiatorType"] == "link"
        assert transfer["responseStatus"] == 200 and transfer["encodedBodySize"] > 0
        assert all(entry["name"] == expected_url for entry in resources)
        assert all(
            entry["transferSize"] == 0 and entry["deliveryType"] == "cache"
            for entry in resources if entry is not transfer
        ), resources
        assert font_requests
        assert all(request.url == expected_url for request in font_requests), request_records
        initial_request = font_requests[0]
        assert initial_request.url == transfer["name"] == expected_url
        assert initial_request.method == "GET" and initial_request.resource_type == "font"
        headers = initial_request.all_headers()
        print("STIX ordinary network font:", json.dumps({
            "url": initial_request.url,
            "method": initial_request.method,
            "resource_type": initial_request.resource_type,
            "sec-fetch-dest": headers.get("sec-fetch-dest"),
            "sec-fetch-mode": headers.get("sec-fetch-mode"),
            "resource": transfer,
        }, sort_keys=True), flush=True)
        assert headers["sec-fetch-dest"] == "font"
        assert headers["sec-fetch-mode"] == "cors"
    finally:
        context.close()


def test_g_a_label_in_mathematical_italic_is_drawn_whole_in_its_box(page, server, original):
    """Review Focus 2 of unit G's plan: every box of cons.bl's backward
    graph draws its label whole inside the box, `𝑉≻ ∘ 𝑔≻` among them, whose
    mathematical italic letters IBM Plex Mono lacks and STIX Two Math holds,
    the face loaded before the layout measured the label."""
    open_cons(page, server)
    drawn = page.evaluate(BOX_DRAWN_JS)
    assert drawn["cntn_to_dcsn:Pullback"]["text"] == "𝑉≻ ∘ 𝑔≻"
    assert all(box["whole"] for box in drawn.values() if box["text"] is not None)
    assert page.evaluate("""() => document.fonts.check('12.5px "STIX Two Math"', '𝑉≻')""")
    assert page.evaluate("""() => [...document.fonts].some(face =>
      face.family.replaceAll('"', '') === 'STIX Two Math' && face.status === 'loaded')""")


def test_g_a_refused_graph_draws_its_one_node_in_the_refusal_orange(
    browser, server_on, cagetti_folder
):
    """Review Focus 3 of unit G's plan: the forward graph of
    entrepreneur_death.bl, which the construction refuses, is drawn as its
    one node `forward:refused`, lined in the refusal orange
    (`--bl-graph-refusal`) with its label whole; no other element of the
    region is orange; and the refusal's sentence stands in the list under
    the error mark."""
    text = (cagetti_folder / ENTREPRENEUR_DEATH).read_text(encoding="utf-8")
    refusal = model.refused_directions(
        model.elaborate_buffer(text, ENTREPRENEUR_DEATH).stage
    )["forward"]
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(cagetti_folder), ENTREPRENEUR_DEATH, minimum=4)
        choose_view(tab, "operator", "forward")
        wait_until(
            lambda: list(tab.evaluate(BOX_DRAWN_JS)) == ["forward:refused"],
            15.0,
            "the one refusing node",
        )
        box = tab.evaluate(BOX_DRAWN_JS)["forward:refused"]
        assert box["border"] == property_color(tab, "--bl-graph-refusal") == ORANGE
        assert box["whole"]
        drawn = [entry for entry in tab.evaluate(ORANGE_ELEMENTS_JS) if "bf-" in entry]
        assert drawn and all(entry.startswith("div.bf-box") for entry in drawn), drawn
        wait_until(
            lambda: (refusal["message"], ENTREPRENEUR_DEATH, 17) in error_lines(tab),
            10.0,
            "the forward refusal's sentence, file and line in the error list",
        )
    finally:
        context.close()


def test_amd_mi_001_item_5_the_legend_lists_what_the_graph_holds_and_the_selection_ring_is_ultramarine_light(
    browser, server
):
    """AMD-MI-001 item 5: in the Workbench on `cons.bl` with its methods,
    bound as `periods[0] / cons` by the model folder's recipe,
    `declaration/spec.yml`, with its calibration, settings and methods, the
    legend of `backward` is titled `cons calibrated methodized configured`
    and holds the three levels the graph draws, each with its swatch,
    `!egm  policy:Evaluation`, `!Cartesian  cntn_to_dcsn:Evaluation` and the
    three marks, and no other tag; the perches appear with `perch
    overlays`, each by its name and colored by its custom property; the
    levels and the perches in sentence case (design pass 13 §3; C12);
    the legend of `backward initial diagram` lists `value  V≻, V, V≺`;
    and a selected box has the ring of `--bl-graph-ring`, as specification
    §§2.1 and 5.3 prescribe. A transparent period swatch in the trellis
    shows its navy background at the center."""
    context, tab = new_tab(browser)
    try:
        open_file(tab, server, CONS)
        wait_until(
            # the version's states after the name, joined by commas (the fix
            # wave Q3b of unit Q, item 19; C8)
            lambda: tab.locator(".bl-legend-name").all_text_contents()
            == ["cons calibrated, methodized, configured"],
            30.0,
            "the legend of cons with its methods",
        )
        groups = dict(tab.evaluate(LEGEND_GROUPS_JS))
        assert list(groups) == ["levels", "methods", "marks"]
        assert groups["levels"] == [
            [
                "Builder",
                property_color(tab, "--bl-graph-builder"),
                property_color(tab, "--bl-graph-layer-border"),
            ],
            [
                "Primitive operator",
                property_color(tab, "--bl-navy"),
                # the edge of every graph box since design pass 13 §5, which
                # retired `--bl-graph-box-border` into it (B6, Q-D24)
                property_color(tab, "--bl-control-border"),
            ],
            [
                "Builder's output",
                property_color(tab, "--bl-navy"),
                property_color(tab, "--bl-graph-output"),
            ],
        ]
        assert tab.locator(".bl-legend-swatch[data-level]").evaluate_all(
            "(all) => all.map((swatch) => swatch.dataset.level)"
        ) == ["builder", "operator", "output"]
        assert tab.locator(".bl-legend-swatch[style]").count() == 0
        assert sorted(text for text, _, _ in groups["methods"]) == [
            "!Cartesian  cntn_to_dcsn:Evaluation",
            "!egm  policy:Evaluation",
        ]
        assert [text for text, _, _ in groups["marks"]] == ["· !tag", "at 𝑐", "𝑔≺, 𝑔≻"]
        # the tags the legend's whole text holds: the two methods' and the
        # mark's own
        legend = tab.locator(".bl-legend").text_content()
        assert set(re.findall(r"!\w[\w-]*", legend)) == {"!egm", "!Cartesian", "!tag"}

        tab.click(".bl-overlays-button")
        wait_until(
            lambda: "perches" in dict(tab.evaluate(LEGEND_GROUPS_JS)),
            10.0,
            "the perches in the legend",
        )
        perches = dict(tab.evaluate(LEGEND_GROUPS_JS))["perches"]
        assert [(text, fill) for text, fill, _ in perches] == [
            ("Arrival", property_color(tab, "--bl-graph-arrival")),
            ("Decision", property_color(tab, "--bl-graph-decision")),
            ("Continuation", property_color(tab, "--bl-graph-continuation")),
        ]

        assert tab.locator(".bl-legend-swatch[data-perch]").evaluate_all(
            "(all) => all.map((swatch) => swatch.dataset.perch)"
        ) == ["arrival", "decision", "continuation"]
        assert tab.locator(".bl-legend-swatch[style]").count() == 0

        choose_view(tab, "initial", "backward")
        wait_until(
            lambda: "value  V≻, V, V≺"
            in [text for text, _, _ in dict(tab.evaluate(LEGEND_GROUPS_JS)).get("roles", [])],
            10.0,
            "the fields of the role value in the legend",
        )

        choose_view(tab, "operator", "backward")
        wait_until(lambda: "𝑉≻ ∘ 𝑔≻" in svg_texts(tab), 15.0, "the backward graph")
        select_node(tab, "policy:Evaluation", "backward")
        ring = property_color(tab, "--bl-graph-ring")
        wait_until(
            lambda: tab.evaluate(BOX_DRAWN_JS)["policy:Evaluation"]["outline"][0] == ring,
            10.0,
            "the selected box's ultramarine-light ring",
        )

        # A transparent period swatch shows the navy ground at its center.
        tab.click(".bl-trellis-button")
        period = tab.locator('.bl-legend-swatch[data-level="period"]')
        wait_until(lambda: period.count() == 1, 30.0, "the period swatch")
        # the button selects the stage's occurrence (amendment 02 ruling 3),
        # so the legend stands under its details element, opened here
        tab.click(".bl-legend-details > summary")
        assert period.evaluate("(swatch) => getComputedStyle(swatch).backgroundColor") == (
            property_color(tab, "--bl-graph-period")
        )
        png = base64.b64encode(period.screenshot(type="png")).decode("ascii")
        pixel = tab.evaluate(
            """async (png) => {
              const image = new Image();
              image.src = `data:image/png;base64,${png}`;
              await image.decode();
              const canvas = document.createElement('canvas');
              canvas.width = image.width;
              canvas.height = image.height;
              const context = canvas.getContext('2d');
              context.drawImage(image, 0, 0);
              return Array.from(context.getImageData(
                Math.floor(image.width / 2), Math.floor(image.height / 2), 1, 1
              ).data);
            }""",
            png,
        )
        assert pixel[3] == 255
        assert f"rgb({pixel[0]}, {pixel[1]}, {pixel[2]})" == property_color(tab, "--bl-navy")
    finally:
        context.close()


# --- unit T, the classification table ---


def test_t_the_editor_replaces_spans_given_in_code_points(page, server, cons_file, original):
    """The editor's write-back (unit T, rule 3; Review Focus 1 and 2): the
    two replacements of the set of V[>], on lines 21 and 31, and a space
    inserted at column 28 of line 8, counted in code points after 𝑢, which
    the document counts as two units, are applied as one transaction when
    the document is the text they were read from: the three lines change
    and no other, the loop reads the new text, one undo restores the
    file's text, and the file on disk is unchanged. With another expected
    text nothing is applied."""
    groups = model.classification(stage_of(original), source_spans(original, CONS))
    change = {"kind": "set", "identity": "cons:cntn:V", "value": "ℝ"}
    edits = [*model.classification_edits(groups, change), model.Replacement(8, 28, 8, 28, " ")]
    expected = applied(original, edits)
    lines = original.split("\n")
    assert expected.split("\n")[7] == lines[7][:27] + " " + lines[7][27:]
    assert changed_lines(original, expected) == [8, 21, 31]
    records = [edit._asdict() for edit in edits]

    open_cons(page, server)
    assert page.evaluate(REPLACE_SPANS_JS, [records, "another text"]) is False
    assert page.evaluate(DOCUMENT_JS) == original
    assert page.evaluate(REPLACE_SPANS_JS, [records, original]) is True
    assert page.evaluate(DOCUMENT_JS) == expected
    assert line_text(page, 8) == expected.split("\n")[7]
    assert settled_status(page, digest7(expected))["state"] == "constructed"
    click_line(page, 1)
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of the edit")
    assert cons_file.read_text(encoding="utf-8") == original


def test_t_item_5_the_code_editor_expands_the_extensions_shortcuts(page, server, original):
    """Line 3 of cons.bl, `Xm := ℝ₊₊`, with its set deleted and
    `\\StrictlyPositiveReals` typed in its place, reads `Xm := ℝ₊₊` again
    when Tab is pressed (unit T, item 5; rule 6), and the document is the
    file's text; Tab on the empty line 2, where no shortcut ends, indents
    it (Review Focus 4) by the four spaces of one indent (unit R, R-D33)."""
    assert original.split("\n")[2] == "Xm := ℝ₊₊"
    open_cons(page, server)
    click_line(page, 3)
    page.keyboard.press("End")
    for _ in range(3):
        page.keyboard.press("Backspace")
    page.keyboard.type("\\StrictlyPositiveReals")
    assert line_text(page, 3) == "Xm := \\StrictlyPositiveReals"
    page.keyboard.press("Tab")
    assert line_text(page, 3) == "Xm := ℝ₊₊"
    assert page.evaluate(DOCUMENT_JS) == original
    click_line(page, 2)
    page.keyboard.press("Tab")
    assert line_text(page, 2) == " " * 4


def test_t_item_1_the_three_tables_list_the_fields_and_follow_the_text(page, server, original):
    """The three tables of cons.bl list the fields with the sets and roles
    the fields table prints, in its order, the row of c naming line 17
    (unit T, item 1); the panel's strip names the file `cons.bl` (unit N,
    Task 2; design pass 10 §4); `hide types` leaves the tables unchanged;
    line 13 typed with m in Xa changes the row of m once the loop has read
    it; the main bar's toggle `Inspector` folds the region, which is then
    not drawn, and opens it again (unit L, Task 12; AAS, L-D12; unit N,
    Task 1, N-D4). The window
    is 2200 px wide, so that line 13 stands on one
    visual line and Home and Shift+End select the whole of it; at 1600 px
    the text's column is frame 7b's 568 px, in which line 13 wraps (spec
    0.4 §5.1; unit R, Task 12)."""
    expected = [
        {"perch": group.perch, "group": f"{group.perch}/", "field": row.field, "set": row.set,
         "role": row.role, "line": str(row.line)}
        for group in model.classification(stage_of(original), source_spans(original, CONS))
        for row in group.rows
    ]
    page.set_viewport_size({"width": 2200, "height": 1000})
    open_cons(page, server)
    page.wait_for_selector(".bl-class-row", timeout=10_000)
    rows = page.evaluate(TABLE_ROWS_JS)
    assert rows == expected
    assert [row["field"] for row in rows] == [
        "m", "V[<]", "dV[<]", "m_d", "c", "V", "dV", "a", "V[>]", "dV[>]",
    ]
    assert next(row for row in rows if row["field"] == "c")["line"] == "17"
    strip = '.bl-classification[data-panel="types"] .bl-inspector-strip'
    assert page.locator(f"{strip} .bl-inspector-file").text_content() == "cons.bl"
    assert page.locator(".bl-status-summary .bl-status-state").text_content() == "constructed"

    page.click(".bl-types-button")
    wait_until(lambda: line_text(page, 13) == "[arvl_to_dcsn] {", 5.0, "line 13 as its name")
    assert page.evaluate(TABLE_ROWS_JS) == rows
    page.click(".bl-types-button")
    wait_until(lambda: line_text(page, 13) == original.split("\n")[12], 5.0, "line 13 in full")

    line_13 = original.split("\n")[12].replace("(m : Xm)", "(m : Xa)")
    click_line(page, 13)
    page.keyboard.press("Home")
    page.keyboard.press("Shift+End")
    started = time.perf_counter()
    page.keyboard.type(line_13)
    wait_until(
        lambda: page.evaluate(TABLE_ROWS_JS)[0]["set"] == "Xa", 8.0, "the row of m read again"
    )
    print(f"the row of m changed {time.perf_counter() - started:.2f} s after the typing began")

    toggle = page.locator('.bl-main-bar .bl-fold[data-fold="inspector"]')
    toggle.click()
    wait_until(lambda: not page.locator(".bl-classification").is_visible(), 5.0, "folded")
    assert toggle.get_attribute("aria-expanded") == "false"
    toggle.click()
    page.wait_for_selector(".bl-class-row", state="visible", timeout=5_000)


def test_t_a_role_cell_shows_the_role_the_text_writes(page, server, cons_file, original):
    """The role `!ctrl` chosen in the cell of m_d (unit T, rule 3) writes
    ` @ !ctrl` into the declaration of m_d on line 13, which the
    construction refuses; while the refusal stands, the tables stay
    editable, read from the text, and the cell shows `!ctrl`, the role the
    text writes (unit R, R-D57); after one undo, once the loop has read the
    file's text again, it shows `state`. The file on disk is unchanged."""
    groups = model.classification(stage_of(original), source_spans(original, CONS))
    change = {"kind": "role", "group": "dcsn/", "identity": "cons:dcsn:m_d", "value": "!ctrl"}
    expected = applied(original, model.classification_edits(groups, change))
    assert changed_lines(original, expected) == [13]
    cell = '.bl-class-row[data-identity="cons:dcsn:m_d"] .bl-class-role'

    open_cons(page, server)
    page.wait_for_selector(cell, timeout=10_000)
    assert page.locator(cell).input_value() == "state"
    page.select_option(cell, "!ctrl")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == expected, 5.0, "the text the change writes")
    assert settled_status(page, digest7(expected))["state"] == "parsed, refused"
    wait_until(
        lambda: page.locator(".bl-status-summary .bl-status-state").text_content()
        == "parsed, refused",
        5.0,
        "the refusal in the status line",
    )
    wait_until(lambda: page.locator(cell).input_value() == "!ctrl", 5.0, "the role the text writes")
    assert page.locator(".bl-class-tables.bl-stale").count() == 0
    assert page.locator(cell).is_enabled()

    click_line(page, 1)
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of the change")
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)
    assert settled_status(page, digest7(original))["state"] == "constructed"
    wait_until(lambda: page.locator(cell).input_value() == "state", 5.0, "the role state again")
    assert cons_file.read_text(encoding="utf-8") == original


def test_t_item_2_a_set_cell_rewrites_every_declaration_in_one_transaction(
    page, server, cons_file, original
):
    """The set of V[>] entered as ℝ in its cell, with Enter, rewrites
    `[-inf, inf)` on lines 21 and 31 and nothing else (unit T, item 2); the
    loop reads the new text and the row prints ℝ; one undo restores both
    lines, the edit being one transaction; the file on disk is unchanged,
    since the file changes by `save` alone."""
    groups = model.classification(stage_of(original), source_spans(original, CONS))
    change = {"kind": "set", "identity": "cons:cntn:V", "value": "ℝ"}
    expected = applied(original, model.classification_edits(groups, change))
    assert changed_lines(original, expected) == [21, 31]

    open_cons(page, server)
    cell = page.locator('.bl-class-row[data-identity="cons:cntn:V"] .bl-class-set')
    cell.fill("ℝ")
    cell.press("Enter")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == expected, 5.0, "lines 21 and 31 rewritten")
    assert settled_status(page, digest7(expected))["state"] == "constructed"
    wait_until(lambda: cell.input_value() == "ℝ", 5.0, "the row of V[>] read again")
    click_line(page, 1)
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of both lines")
    assert cons_file.read_text(encoding="utf-8") == original


def test_t_item_3_add_field_writes_the_header_the_rule_names(page, server, cons_file, original):
    """`h`, `ℝ₊`, `state` in the box of the decision table is appended to
    the outputs of arvl_to_dcsn on line 13 (unit T, item 3; rule 4) and
    listed by its name on the inputs of dcsn_to_cntn on line 17 (AAS,
    L-D1); the loop refuses the output no equation defines, and while the
    refusal stands the tables stay editable, read from the text (unit R,
    R-D57): the row of h stands in the decision table, its field text with
    no link to a box, since the last construction holds none, and a click
    on it selects nothing; one undo returns the file's text, the status
    line reading `constructed`. `c`, declared on line 17, is written
    nowhere: the box is marked as refused and the list under the error mark
    says where `c` is declared, with the file (AMD-MI-002 §6a rule 1), a
    refusal that still stands after the loop's pause."""
    line_13 = "[id=arvl_to_dcsn, (m : Xm) : !arvl -> (m_d : Xm, h : ℝ₊) : !dcsn] {"
    line_17 = "[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊, h) : !dcsn -> (a : Xa) : !cntn] {"
    written = edited(edited(original, 13, line_13), 17, line_17)
    sentence = "c is already declared on line 17"
    open_cons(page, server)
    record_view_state(page)
    choose_view(page, "initial", "backward")
    wait_until(lambda: "V≻" in svg_texts(page), 15.0, "the backward initial diagram")
    select_node(page, "cons:dcsn:V", "backward initial diagram")
    wait_until(
        lambda: (view_state(page) or {}).get("selected") == "cons:dcsn:V"
        and page.locator('.bl-class-row.bl-selected[data-identity="cons:dcsn:V"]').count() == 1,
        10.0,
        "the field selected before the refused edit",
    )
    box = page.locator('.bl-class-group[data-group="dcsn/"] .bl-add-field')
    box.locator('[data-entry="field"]').fill("h")
    box.locator('[data-entry="set"]').fill("ℝ₊")
    box.locator('[data-entry="role"]').select_option("state")
    box.locator(".bl-add-button").click()
    wait_until(lambda: line_text(page, 13) == line_13, 5.0, "line 13 with h")
    assert page.evaluate(DOCUMENT_JS) == written
    status = settled_status(page, digest7(written))
    assert status["state"] == "parsed, refused"
    row_h = page.locator('.bl-class-row[data-identity="cons:dcsn:h"]')
    row_h.wait_for(timeout=5_000)
    assert page.locator(".bl-class-tables.bl-stale").count() == 0
    assert page.locator('.bl-class-row[data-identity="cons:dcsn:c"] .bl-class-set').is_enabled()
    assert page.locator('.bl-class-row[data-identity="cons:dcsn:c"] .bl-class-field').is_enabled()
    assert row_h.locator("button.bl-class-field").count() == 0
    selection = "() => document.querySelector('.bl-view-host').bellmanFlow.selection()"
    selected_before = page.evaluate(selection)
    marked = page.locator(".bl-class-row.bl-selected")
    marked_before = marked.evaluate_all("rows => rows.map(row => row.dataset.identity)")
    selections_before = record(page, "selections")
    row_h.locator(".bl-class-field").click()
    # Observe one second for normal asynchronous selection dispatch.
    until = time.monotonic() + 1.0
    while time.monotonic() < until:
        assert page.evaluate(selection) == selected_before
        assert marked.evaluate_all("rows => rows.map(row => row.dataset.identity)") == marked_before
        assert record(page, "selections") == selections_before
        page.wait_for_timeout(50)
    click_line(page, 1)
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "the field undone")
    assert settled_status(page, digest7(original))["state"] == "constructed"
    wait_until(lambda: row_h.count() == 0, 5.0, "the row of h withdrawn")
    assert page.locator(".bl-status-summary .bl-status-state").text_content() == "constructed"
    box.locator('[data-entry="field"]').fill("c")
    box.locator(".bl-add-button").click()
    group = page.locator('.bl-class-group[data-group="dcsn/"]')
    group.locator(".bl-add-field.bl-refusal-mark").wait_for(timeout=5_000)
    wait_until(
        lambda: error_lines(page) == [(sentence, CONS, None)],
        5.0,
        "the table's sentence in the list under the error mark",
    )
    assert group.locator(".bl-class-note").count() == 0
    page.wait_for_timeout(PAUSE_MS + 500)
    assert group.locator(".bl-add-field.bl-refusal-mark").count() == 1
    assert error_lines(page) == [(sentence, CONS, None)]
    assert page.evaluate(DOCUMENT_JS) == original
    assert cons_file.read_text(encoding="utf-8") == original


def test_t_item_5_the_set_cell_expands_the_extensions_shortcuts(page, server, original):
    """`\\StrictlyPositiveReals` typed in the set cell of V[>], whose
    printed set is `[-inf, inf)`, then Tab, reads `ℝ₊₊` (unit T, item 5;
    rule 6), as the code editor expands it; Escape restores the printed
    set and writes nothing."""
    open_cons(page, server)
    cell = page.locator('.bl-class-row[data-identity="cons:cntn:V"] .bl-class-set')
    cell.fill("")
    cell.press_sequentially("\\StrictlyPositiveReals")
    cell.press("Tab")
    assert cell.input_value() == "ℝ₊₊"
    cell.press("Escape")
    assert cell.input_value() == "[-inf, inf)"
    page.wait_for_timeout(PAUSE_MS + 500)
    assert page.evaluate(DOCUMENT_JS) == original


def test_t_item_4_the_continuation_table_of_ret_choice_has_one_group_per_branch(
    page, server_on, retirement_folder
):
    """`declaration/stages/ret_choice/ret_choice.bl` of the retirement copy
    (unit T, item 4; rule 5, T-C12; AMD-MI-002 §5 rule 2, A2-D12): the
    continuation table holds `work` with a_w and the two values the
    builder joining `cntn` and `dcsn` types on its states, `retire` with
    a_r and its two values, and the group `all branches` with no row,
    each group with its box; `h`, `ℝ₊`, `state` under `work` writes into
    line 10 alone."""
    url = server_on(retirement_folder)
    text = (retirement_folder / RET_CHOICE).read_text(encoding="utf-8")
    open_file(page, url, RET_CHOICE)
    page.wait_for_selector(".bl-class-row", timeout=10_000)
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)
    groups = {}
    for row in page.evaluate(TABLE_ROWS_JS):
        if row["perch"] == "cntn":
            groups.setdefault(row["group"], []).append(row["field"])
    assert groups == {
        "cntn/work": ["a_w", "V_w[>]", "dV_w[>]"],
        "cntn/retire": ["a_r", "V_r[>]", "dV_r[>]"],
    }
    for key in ("cntn/work", "cntn/retire", "cntn/all branches"):
        assert page.locator(f'.bl-class-group[data-group="{key}"] .bl-add-field').count() == 1
    line_10 = "    [label=work,   () -> (a_w : ℝ₊, h : ℝ₊) : !cntn] { a_w = a_d }"
    box = page.locator('.bl-class-group[data-group="cntn/work"] .bl-add-field')
    box.locator('[data-entry="field"]').fill("h")
    box.locator('[data-entry="set"]').fill("ℝ₊")
    box.locator('[data-entry="role"]').select_option("state")
    box.locator(".bl-add-button").click()
    wait_until(lambda: line_text(page, 10) == line_10, 5.0, "line 10 with h")
    assert page.evaluate(DOCUMENT_JS) == edited(text, 10, line_10)


# --- unit J, the gestures of the trellis graph: the notice of typing ---

# A recorder installed before the page's scripts run: the path of each DOM
# event `input-edited` dispatched on `document`, in order.
INPUT_EDITED_RECORDER_JS = """
window.inputEdited = [];
document.addEventListener("input-edited", (event) => window.inputEdited.push(event.detail.path));
"""
# the paths the recorder holds
INPUT_EDITED_JS = "() => window.inputEdited"


def test_j_the_editor_reports_the_first_typing_after_each_change_event(
    browser, server_on, scratch_consport
):
    """Brief rule 6, its last sentence, and J-D12: the editor dispatches the
    DOM event `input-edited`, with the open file's path, at the first change
    of its document after the last change event it sent, and at no document
    Python gives it. Over the copy of cons-port, with the recorder installed
    before the page's scripts: the page opened on the trellis file of
    lesson 05 records no event; `#a` typed at the file's end records one
    event with the file's path; once the change event has been read, the
    title marking the file `unsaved`, one more character records a second.
    The calibration file opened, a document Python gives the editor, records
    nothing, and a character typed there records that file's path."""
    trellis_text = (scratch_consport / PORT_CONS).read_text(encoding="utf-8")
    calibration_text = (scratch_consport / PORTFOLIO_CALIBRATION).read_text(encoding="utf-8")
    context, tab = new_tab(browser)
    try:
        tab.add_init_script(INPUT_EDITED_RECORDER_JS)
        open_trellis(tab, server_on(scratch_consport), PORT_CONS)
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == trellis_text, 30.0, "the trellis file's text"
        )
        assert tab.evaluate(INPUT_EDITED_JS) == []

        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+End")
        tab.keyboard.type("#a")
        assert tab.evaluate(DOCUMENT_JS) == trellis_text + "#a"
        wait_until(lambda: tab.evaluate(INPUT_EDITED_JS), 5.0, "the first notice")
        wait_until(
            lambda: tab.locator(".bl-file .bl-modified").count() == 1, 10.0, "the change event"
        )
        assert tab.evaluate(INPUT_EDITED_JS) == [PORT_CONS]
        tab.keyboard.type("b")
        wait_until(lambda: len(tab.evaluate(INPUT_EDITED_JS)) == 2, 5.0, "the second notice")
        assert tab.evaluate(INPUT_EDITED_JS) == [PORT_CONS, PORT_CONS]

        reveal_in_tree(tab, PORTFOLIO_CALIBRATION)
        tab.click(f'.bl-tree-file[data-path="{PORTFOLIO_CALIBRATION}"]')
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == calibration_text,
            30.0,
            "the calibration file's text",
        )
        assert tab.evaluate(INPUT_EDITED_JS) == [PORT_CONS, PORT_CONS]
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+End")
        tab.keyboard.type("#")
        wait_until(lambda: len(tab.evaluate(INPUT_EDITED_JS)) == 3, 5.0, "the third notice")
        assert tab.evaluate(INPUT_EDITED_JS) == [PORT_CONS, PORT_CONS, PORTFOLIO_CALIBRATION]
    finally:
        context.close()


# --- unit J, the gestures of the trellis graph: a closed layer's ports ---


def test_j_a_closed_period_carries_the_unjoined_port_of_each_occurrence_alone(
    browser, server_on, tmp_path
):
    """Ruling J-P25 (spec 0.4 §3.4; unit J's plan, Task 9): in the copy
    `two_cons_one_joined`, whose periods each hold two occurrences of
    `cons.bl`, `cons_one`, whose `m` the keyed connector joins to `port`,
    and `cons_two`, whose `m` no join reaches, the forward graph draws as
    ports a drag can take those `trellis.unjoined_ports` answers. With
    `periods[2]` closed, its box carries, under their own ids, the unjoined
    ports of `periods[2]` alone: `cons_two`'s `m`, and not `cons_one`'s,
    since each port of the box that a drag can take stands for one port of
    the graph JSON, marked by its own attribute."""
    copy = two_cons_one_joined(tmp_path)
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PORT_CONS_RECIPE)).shown
    ports = sorted(port["id"] for port in trellis.unjoined_ports(shown, {}))
    inside = sorted(port for port in ports if port.startswith("periods[2]/"))
    assert "periods[2]/cons_two/unjoined:cons:arvl:m" in inside
    assert not any(port.startswith("periods[2]/cons_one/") for port in inside)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PORT_CONS)
        choose_view(tab, None, "forward")
        wait_until(lambda: unjoined_port_ids(tab) == ports, 30.0, "the forward graph's ports")
        closed = "periods[2]___group___"
        # the toggle reached as a reader reaches it, since the graph opens on
        # periods[0] (unit K's decision K-D6)
        click_toggle(tab, closed)
        wait_until(lambda: ports_on_box(tab, closed) == inside, 10.0, "the closed period's ports")
        assert unjoined_port_ids(tab) == ports
    finally:
        context.close()


# --- the trellis view's load time, item 6 of its brief ---


def test_trellis_load_item_6_durables_opens_on_periods_0_2_twice_and_the_seconds_are_recorded(
    browser, tmp_path
):
    """Item 6 of the brief on the trellis view's load time: a copy of the
    durables folder, of 51 periods, opened in the page by two servers in
    turn, each a new process started by `start_server` on a free port, with
    `XDG_CACHE_HOME` naming one folder of the test's own, empty for the
    first server and holding, for the second, the stage views the first
    wrote. Each time the view's element lays out the trellis, whose backward
    graph holds the ten occurrences of periods 0 to 2, the bar reads
    `periods 0–2`, and the status line settles on `shown periods 0–2 of 51
    (10 occurrences)`. The seconds of an opening are counted from the call
    that navigates the page to the server's address, made once the server
    answers that address, to the moment the view shows the trellis drawn:
    the element has reported the layout of a collection, the collection it
    holds is the trellis, and no processing panel stands (`view_laid_out`).
    They are printed with the prefix `item 6 first opening:` or `item 6
    second opening:`, beside the seconds to the settled status line, and
    are written, with the status line at both moments, to the JSON file the
    environment variable BELLMAN_TRELLIS_LOAD_TIMES names, where it is set.
    The bounds of item 6, under seven seconds the first time and under five
    the second, are AAS's own reading and are not asserted."""
    durables = repository_copy(ROOT / "applications/durables", tmp_path / "durables")
    syntactic = load_recipe(durables / "declaration", "spec.yml")
    # the occurrences of periods 0 to 2, the terminal period and the two
    # before it, each as its period's namespace and its stage key
    expected = {
        f"periods[{h}]/{key}"
        for h, period in enumerate(syntactic["periods"][:3])
        for key in period["stages"]
    }
    assert len(syntactic["periods"]) == 51 and len(expected) == 10
    shown = "shown periods 0–2 of 51 (10 occurrences)"
    cache = tmp_path / "cache"
    cache.mkdir()

    def opened(name: str) -> dict:
        """The page opened once over the copy by a new server whose cache
        folder is `cache`, the server stopped after: the seconds to the
        trellis drawn and to the settled status line, and the status line
        at each of the two moments."""
        port = free_port()
        url = f"http://localhost:{port}/"
        log_path = tmp_path / f"{name}-server.log"
        process = start_server(durables, port, log_path, cache_home=cache)
        context = None
        try:
            context, tab = new_tab(browser)
            error = server_error(url, process, log_path)
            assert error is None, error
            started = time.perf_counter()
            tab.goto(url)
            record_layouts(tab)
            # the count of layouts is read in the page at each frame, so
            # that the test reads no collection while the page lays one out
            tab.wait_for_function("() => window.laidOut.count > 0", timeout=120_000)
            wait_until(lambda: view_laid_out(tab, "trellis", 0), 60.0, "the trellis drawn")
            drawn = time.perf_counter() - started
            line_drawn = status_text(tab)
            assert occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "backward") == expected
            line, _ = wait_until(
                lambda: (lambda found: found if found and shown in found else None)(
                    trellis_settled(tab, RECIPE_FILE)
                ),
                120.0,
                "the status line of periods 0–2",
            )
            settled = time.perf_counter() - started
            assert restriction_shown(tab) == "periods 0–2"
        finally:
            if context is not None:
                context.close()
            stop_server(process)
        print(
            f"item 6 {name} opening: {drawn:.3f} s (the status line settled after {settled:.3f} s)"
        )
        return {
            "seconds to the trellis drawn": round(drawn, 3),
            "status line when the trellis is drawn": line_drawn,
            "seconds to the settled status line": round(settled, 3),
            "settled status line": line,
        }

    first = opened("first")
    # the first server wrote the stage views into the cache folder
    assert any((cache / "bellman-workbench/views").rglob("*.json"))
    second = opened("second")
    times = os.environ.get("BELLMAN_TRELLIS_LOAD_TIMES")
    if times:
        Path(times).write_text(
            json.dumps(
                {"first opening": first, "second opening": second}, ensure_ascii=False, indent=2
            )
            + "\n",
            encoding="utf-8",
        )


def test_g_an_edit_keeps_the_view_the_open_layers_and_the_selection(page, server, original):
    """Spec 0.4 §2.3: a comment leaves the graph unchanged, and a valid
    arrival-domain edit redraws it; both keep the viewport, open layers
    and selected Pullback while policy is closed (Review Focus 1)."""
    open_cons(page, server)
    record_view_state(page)
    page.click('.bl-view-host .react-flow__node[data-id="policy___group___"] .bf-toggle')
    wait_until(
        lambda: (view_state(page) or {}).get("open") is not None
        and "policy___group___" not in view_state(page)["open"],
        10.0,
        "policy closed",
    )
    select_node(page, "cntn_to_dcsn:Pullback", "backward")
    page.click(".bl-zoom-button[data-zoom='zoom out']")
    page.wait_for_timeout(300)
    before = viewport(page)
    state_before = view_state(page)
    held = page.evaluate(HELD_COLLECTION_JS)
    first = original.split("\n")[0]
    commented = edited(original, 1, first + "  # kept")
    click_line(page, 1)
    page.keyboard.press("End")
    # the comment typed through the editor's own change at the end of line
    # 1, which the loop receives as typed text, since keystrokes sent with no
    # pause can reach the editor out of order while it redraws (unit K's fix
    # wave, item 14)
    end = len(first) + 1
    comment = model.Replacement(1, end, 1, end, "  # kept")
    assert page.evaluate(REPLACE_SPANS_JS, [[comment._asdict()], original]) is True
    assert page.evaluate(DOCUMENT_JS) == commented
    status = settled_status(page, digest7(commented), 15.0)
    assert status["state"] == "constructed" and status["refusals"] is None
    assert page.evaluate(HELD_COLLECTION_JS) == held
    assert viewport(page) == before
    assert view_state(page) == state_before
    assert "policy___group___" not in state_before["open"]
    assert state_before["selected"] == "cntn_to_dcsn:Pullback"

    # The editor's replacement operation keeps its cursor on line 1.
    lines = commented.split("\n")
    matching = [(n, line) for n, line in enumerate(lines, 1) if "(m : Xm)" in line]
    assert len(matching) == 1
    line_number, line = matching[0]
    column = line.index("(m : Xm)") + len("(m : ") + 1
    replacement = model.Replacement(line_number, column, line_number, column + 2, "Xa")
    changed = applied(commented, [replacement])
    assert changed == commented.replace("(m : Xm)", "(m : Xa)", 1)

    laid_out = len(record(page, "processed"))
    assert page.evaluate(REPLACE_SPANS_JS, [[replacement._asdict()], commented]) is True
    assert page.evaluate(DOCUMENT_JS) == changed
    status = settled_status(page, digest7(changed), 15.0)
    assert status["state"] == "constructed" and status["refusals"] is None
    page.wait_for_function(f"() => window.record.processed.length > {laid_out}", timeout=15_000)
    assert page.evaluate(HELD_COLLECTION_JS) != held
    assert viewport(page) == before
    assert view_state(page) == state_before
    assert "policy___group___" not in view_state(page)["open"]
    assert view_state(page)["selected"] == "cntn_to_dcsn:Pullback"


# Each boundary marker the region draws (design pass 10 §6; unit N, Task
# 6): its node's id, its kind, `start`, `end` or `outside`, its label, which
# is its accessible name, and its hover, null where it has none.
MARKERS_DRAWN_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .bf-marker'), (marker) => ({
  id: marker.closest('.react-flow__node').dataset.id,
  kind: marker.dataset.kind,
  label: marker.getAttribute('aria-label'),
  hover: marker.getAttribute('title'),
}))
"""


def test_g_a_restricted_trellis_keeps_its_drawing_and_names_each_port_outside(
    browser, server_on, consport_folder
):
    """Review Focus 5 of unit G's plan: on trellis.port-cons.yml, with the
    occurrence periods[1]/cons selected and periods[0]/cons closed, the
    restriction `periods 0–1` draws the two periods with the selection and
    the closed layer kept (spec 0.4 §2.6), and every port that a join
    leaves the restricted view by names, in its accessible description,
    `outside` and the occurrences outside; every port's description begins
    with its title. Since unit N's Task 6 (design pass 10 §6) boundary
    markers stand in place of the root's `Inputs` and `Outputs`, whose
    ports the description rule covered: a marker's port carries its wire's
    title and is named by its marker, the label of a `start` or an `end`
    marker ending with the port's title, and a join that leaves the view
    ends at an `outside` marker labeled by the occurrence it reaches, whose
    hover names the periods drawn."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(consport_folder), PORT_CONS)
        record_view_state(tab)
        select_node(tab, "periods[1]/cons___group___", "backward")
        layer = "periods[0]/cons___group___"

        def closed() -> bool:
            state = view_state(tab) or {}
            return "open" in state and layer not in state["open"]

        tab.click(f'.bl-view-host .react-flow__node[data-id="{layer}"] .bf-layer > .bf-toggle')
        wait_until(closed, 10.0, "periods[0]/cons closed")
        restrict(tab, "periods 0–1")
        wait_until(lambda: periods_held(tab) == {"periods[0]", "periods[1]"}, 60.0, "periods 0–1")
        state = view_state(tab)
        assert state["selected"] == "periods[1]/cons___group___"
        assert "periods[0]/cons___group___" not in state["open"]
        held = graph_named(tab.evaluate(HELD_COLLECTION_JS), "backward")
        described = tab.evaluate(PORT_DESCRIPTIONS_JS)
        markers = {marker["id"]: marker for marker in tab.evaluate(MARKERS_DRAWN_JS)}
        for box, title, description in described:
            marker = markers.get(box)
            if marker is None:
                assert description.startswith(title), (box, title, description)
            elif marker["kind"] in ("start", "end"):
                # `terminal condition 𝑉≻(a)` names the port `𝑉≻(a)`
                assert marker["label"].endswith(title), (marker, title)
            else:
                assert marker["kind"] == "outside" and title, (marker, title)
        leaving = [
            (node["id"], attribute_of(port, "outside"))
            for node in held["nodes"]
            for side in ("inputsMetadata", "outputsMetadata")
            for port in node.get(side) or []
            if attribute_of(port, "outside")
        ]
        assert leaving
        drawn = {box for box, _, _ in described}
        assert any(node_id in markers for node_id, _ in leaving), "no outside marker drawn"
        for node_id, where in leaving:
            if node_id in markers:
                marker = markers[node_id]
                assert (marker["kind"], marker["label"], marker["hover"]) == (
                    "outside",
                    where,
                    "Outside periods 0–1",
                ), marker
            elif node_id in drawn:
                assert any(
                    box == node_id and f"outside {where}" in description
                    for box, _, description in described
                ), node_id
    finally:
        context.close()


def test_g_a_layout_refused_and_a_file_not_loaded_stand_in_the_error_list(page, browser, server):
    """Review Focus 4: an ELK refusal and a bundle that did not load each
    have their exact sentence with no file or line under the error mark.
    A refusal after a graph-direction or file change ends drawing
    (A2-D13, G-D9), removes the old geometry and permits no action on its
    former nodes. A later
    successful layout draws the current collection and clears the refusal
    (spec 0.4 §§2.1 and 2.5; G-R72)."""
    open_cons(page, server)
    old_drawing = page.evaluate("""() => {
      window.savedELK = window.ELK;
      const host = document.querySelector('.bl-view-host').getBoundingClientRect();
      const nodes = Array.from(document.querySelectorAll('.bl-view-host .react-flow__node'));
      const point = nodes.filter(node => node.querySelector(':scope > .bf-box')).map(node => {
        const box = node.getBoundingClientRect();
        return {id: node.dataset.id, x: box.x + box.width / 2, y: box.y + box.height / 2};
      }).find(point => point.x > host.left && point.x < host.right &&
        point.y > host.top && point.y < host.bottom);
      return {ids: nodes.map(node => node.dataset.id), point};
    }""")
    assert old_drawing["ids"] and old_drawing["point"]
    page.evaluate(REFUSING_ELK_JS)
    toggle = '.bl-view-host .react-flow__node[data-id="policy___group___"] .bf-layer > .bf-toggle'
    page.click(toggle)
    sentence = "the graph backward was not laid out: the stand-in refuses"
    wait_until(lambda: (sentence, None, None) in error_lines(page), 10.0, "the layout's refusal")

    region = "document.querySelector('.bl-view-host').bellmanFlow"

    def no_old_geometry(path: str) -> None:
        assert "drawing" not in status_text(page)
        assert page.locator(".bl-view-host .react-flow__node").count() == 0
        assert page.locator(".bl-view-host .react-flow__edge-path").count() == 0
        assert page.locator(".bl-view-host .bf-perch").count() == 0
        assert page.evaluate(f"() => {region}.openLayers()") == []
        assert page.evaluate(f"() => {region}.selection()") is None
        selections = record(page, "selections")
        page.evaluate(RECORD_OPENED_JS)
        point = old_drawing["point"]
        assert page.evaluate("""point => {
          const hit = document.elementFromPoint(point.x, point.y);
          return !!hit && !!hit.closest('.bl-view-host');
        }""", point)
        page.mouse.click(point["x"], point["y"])
        page.mouse.dblclick(point["x"], point["y"])
        page.focus(".bl-view-host .bf-region")
        page.keyboard.press("Enter")
        assert record(page, "selections") == selections
        assert page.evaluate("() => window.openedEvents") == []
        assert status_settled_on(page, path)

    # Changing direction retains the collection and updates the mounted region.
    choose_view(page, "operator", "forward")
    forward_sentence = "the graph forward was not laid out: the stand-in refuses"
    wait_until(
        lambda: (forward_sentence, None, None) in error_lines(page)
        and status_settled_on(page, CONS),
        10.0,
        "the forward graph's refusal",
    )
    assert page.get_attribute(".bl-graph-bar", "data-graph") == "forward"
    no_old_geometry(CONS)

    choose_view(page, "operator", "backward")
    wait_until(lambda: (sentence, None, None) in error_lines(page), 10.0, "the backward refusal")
    # A different stage sets drawing before its layout is refused.
    reveal_in_tree(page, DISC)
    page.click('.bl-tree-file[data-path="declaration/stages/disc/disc.bl"]')
    wait_until(
        lambda: (sentence, None, None) in error_lines(page) and status_settled_on(page, DISC),
        10.0,
        "the new collection's refusal and the drawing mark ended",
    )
    no_old_geometry(DISC)

    processed = len(record(page, "processed"))
    page.evaluate("() => { window.ELK = window.savedELK; delete window.savedELK; }")
    page.click(".bl-layout-button")
    wait_until(
        lambda: len(record(page, "processed")) > processed
        and (sentence, None, None) not in error_lines(page)
        and status_settled_on(page, DISC),
        15.0,
        "the current graph drawn after the layout refusal",
    )
    current = graph_named(page.evaluate(HELD_COLLECTION_JS), "backward")
    drawn = set(page.evaluate(BOX_DRAWN_JS))
    assert drawn
    opened = set(page.evaluate(f"() => {region}.openLayers()"))
    current_ids = set(expected_layout(current, opened)["boxes"])
    old_only = set(old_drawing["ids"]) - current_ids
    assert old_only and drawn.isdisjoint(old_only)
    assert drawn == current_ids
    assert "drawing" not in status_text(page)

    context, tab = new_tab(browser)
    try:
        tab.route("**/flow/bellman-flow.js", lambda route: route.abort())
        tab.goto(server)
        wait_until(
            lambda: ("flow/bellman-flow.js did not load", None, None) in error_lines(tab),
            60.0,
            "the bundle's refusal",
        )
        wait_until(lambda: "drawing" not in status_text(tab), 60.0, "the drawing mark ended")
        reveal_in_tree(tab, DISC)
        tab.click('.bl-tree-file[data-path="declaration/stages/disc/disc.bl"]')
        wait_until(
            lambda: status_settled_on(tab, DISC)
            and ("flow/bellman-flow.js did not load", None, None) in error_lines(tab),
            60.0,
            "the later collection's unchanged bundle refusal and the drawing mark ended",
        )
    finally:
        context.close()


# --- unit R, Design brief 7: the plan's Review Focus ---


def test_r_a_record_under_the_earlier_key_is_not_read(page, server, model_folder):
    """Review Focus 1 of unit R's plan (R-D16): the browser's storage holds,
    before the page loads, a record of the sizes under the key AMD-MI-002
    wrote, `bellman-workbench sizes <folder>`, with a folder of 400 px and
    the height of the Matsya window, 250 px; the page does not read it, and
    the folder's column is 170 px wide, frame 7b's width."""
    page.goto(server)
    earlier = f"bellman-workbench sizes {model_folder.resolve()}"
    page.evaluate(STORE_JS, [earlier, json.dumps({"folder": 400, "matsya": 250})])
    open_cons(page, server)
    assert abs(tracks(page)[0] - 170) <= 1, tracks(page)


def test_r_a_kept_width_below_its_columns_least_is_not_read(page, server, model_folder):
    """Review Focus 1 of unit R's plan under the record's own key (spec 0.4
    §5.1; R-D14, R-D16): the browser's storage holds, before the page loads,
    a record under `bellman-workbench layout <folder>` whose size `matsya`
    is 250 px, the height an earlier build kept for Matsya's window under
    the panel; the page reads no width below its column's least width,
    300 px, and the four columns have frame 7b's widths."""
    page.goto(server)
    kept = f"bellman-workbench layout {model_folder.resolve()}"
    page.evaluate(STORE_JS, [kept, json.dumps({"sizes": {"matsya": 250}, "folds": {}})])
    open_cons(page, server)
    assert tracks_near(page, FRAME_TRACKS[1600, False]), tracks(page)


def test_r_an_annotation_wraps_below_its_statement_in_a_narrow_text(page, server, original):
    """Review Focus 2 of unit R's plan (spec 0.4 §5.4; R-D26): at
    1600 × 1000 the annotation of line 8 of cons.bl, `:: [id=util]`, ends at
    the right edge of the line's content and stands at its statement's top.
    At 1416 × 1000, where the width function folds the folder since design
    pass 13 §4 took the window's right margin of 60 px away (Q-D6), with the
    folder opened so that the text gives up width, to 538 px, the statement
    of line 32 fits the text's column and its annotation, `::
    [id=optimality, !doc]`, does not: the annotation stands below its
    statement, its right edge still the content's right edge, while line 8
    keeps its annotation at its statement's top. On line 32 so drawn, a
    click before `argmax` of the statement, before the annotation's `::` and
    before its `!doc`, then the key X, puts X at that token's offset in the
    file's text, and one undo restores the bytes. The editor's document is
    the file's text. (With Matsya's column, the text at 1200 px is 300 px
    wide, too narrow for line 8; Task 12.)"""
    lines = original.split("\n")
    assert lines[7].endswith(":: [id=util]") and lines[31].endswith(":: [id=optimality, !doc]")
    open_cons(page, server)
    wide = annotated_line(page, 8)
    assert wide is not None, "line 8 is not drawn as a statement and its annotation"
    assert wide["annotation"]["text"] == ":: [id=util]"
    assert abs(wide["annotation"]["box"]["right"] - wide["content"]["right"]) <= 1, wide
    assert abs(wide["annotation"]["box"]["top"] - wide["statement"]["box"]["top"]) <= 1, wide

    page.set_viewport_size({"width": 1416, "height": 1000})
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1416, False]), 5.0, "the narrowed columns")
    page.click('.bl-fold[data-fold="folder"]')
    wait_until(lambda: abs(tracks(page)[0] - 170) <= 1, 5.0, "the folder opened at 1416 px")
    assert abs(tracks(page)[1] - 538) <= 1, tracks(page)
    narrow = annotated_line(page, 32)
    statement, annotation = narrow["statement"]["box"], narrow["annotation"]["box"]
    print(f"line 32 at 1476 px with the folder open: {narrow}")
    assert narrow["annotation"]["text"] == ":: [id=optimality, !doc]"
    assert abs(statement["top"] - narrow["content"]["top"]) <= 1, narrow
    assert annotation["top"] >= statement["bottom"] - 1, narrow
    assert abs(annotation["right"] - narrow["content"]["right"]) <= 1, narrow
    short = annotated_line(page, 8)
    assert abs(short["annotation"]["box"]["top"] - short["statement"]["box"]["top"]) <= 1, short

    # a click on the wrapped line 32 puts the cursor where it is made (R-D26)
    for token in ("argmax", "::", "!doc"):
        at = lines[31].index(token)
        typed = edited(original, 32, lines[31][:at] + "X" + lines[31][at:])
        wrapped = annotated_line(page, 32)
        top, bottom = wrapped["annotation"]["box"]["top"], wrapped["statement"]["box"]["bottom"]
        assert top >= bottom - 1, wrapped
        click_before(page, 32, token)
        page.keyboard.type("X")
        wait_until(
            lambda typed=typed: page.evaluate(DOCUMENT_JS) == typed,
            5.0,
            f"X before {token!r} on line 32 at 1476 px",
        )
        page.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of X")
    assert page.evaluate(DOCUMENT_JS) == original


def test_r_a_yaml_file_draws_no_stage_name_and_an_ordinary_minimap(
    page, server_on, scratch_folder
):
    """Review Focus 3 of unit R's plan (spec 0.4 §5.4; brief rule 5): with
    the recipe `declaration/spec.yml` of a scratch copy of the portfolio
    model open in the editor, a file with no `@stage` line and no block
    header, no stage name is drawn, and the text minimap holds one mark per
    line of the file, each the mark of an ordinary line."""
    text = (scratch_folder / RECIPE_FILE).read_text(encoding="utf-8")
    open_trellis(page, server_on(scratch_folder), RECIPE_FILE, minimum=1)
    wait_until(lambda: open_path_shown(page) == RECIPE_FILE, 10.0, "the recipe open")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == text, 5.0, "the recipe's text")
    assert page.locator(".bl-stage-name").count() == 0
    marks = minimap_marks(page)
    assert [mark["line"] for mark in marks] == list(range(1, len(text.split("\n")) + 1))
    assert {mark["kind"] for mark in marks} == {"line"}


def test_r_a_preview_moves_neither_the_cursor_nor_the_focus(page, server, original):
    """Unit R, brief rule 9 with review 1 (spec 0.4 §5.8; R-D29; ruling
    R-P7): the functions of the graph's handle, `bellmanFlow` of
    `.bl-view-host`, and of the editor's, `bellmanEditor` of `.bl-editor`.
    On the backward graph, the record that `view()` takes with the box
    `cntn_to_dcsn:Pullback` selected, given to `setView` after a click on
    `zoom out` and a click on another box, gives back the viewport read
    before and the Pullback selected, and a record whose selection is None
    clears the selection, with no `selected` event and no layout. With the
    cursor on line 8 and the focus in the set cell of V[>] in the Fields
    tab, `previewLine(20)` marks line 20 alone with `bl-preview-line` and
    leaves the focused element, the selection of `view()` and the status
    line's place as they were, at 1600 × 1000 and at 1600 × 700, where line
    20 lies below the visible lines of the editor scrolled 40 px from its
    top and the preview changes `view().top`; `setView` of the record taken
    before restores the scroll position of 40 px and removes the mark, the
    focus and the selection unchanged. `findText` answers, the case
    ignored, the lines of the editor's document that Python finds holding
    the text, with the column counted in code points."""
    open_cons(page, server)
    select_node(page, "cntn_to_dcsn:Pullback", "backward")
    wait_until(
        lambda: flow_handle(page, "selection") == "cntn_to_dcsn:Pullback",
        5.0,
        "the Pullback selected",
    )
    before = viewport(page)
    kept = flow_handle(page, "view")
    assert kept["selection"] == "cntn_to_dcsn:Pullback"
    assert set(kept["viewport"]) == {"x", "y", "zoom"}
    page.click(".bl-zoom-button[data-zoom='zoom out']")
    wait_until(lambda: viewport(page)["zoom"] < before["zoom"], 5.0, "the view zoomed out")
    select_node(page, "dcsn_to_arvl:Aggregation", "backward")
    wait_until(
        lambda: flow_handle(page, "selection") == "dcsn_to_arvl:Aggregation",
        5.0,
        "the Aggregation selected",
    )
    # Python's answers to the click, the editor moved to the box's block
    page.wait_for_timeout(500)
    selections, layouts = record(page, "selections"), flow_handle(page, "layouts")
    flow_handle(page, "setView", kept)
    wait_until(lambda: viewport(page) == before, 5.0, "the viewport read before")
    wait_until(
        lambda: page.evaluate(SELECTED_BOXES_JS) == ["cntn_to_dcsn:Pullback"],
        5.0,
        "the Pullback selected again",
    )
    assert flow_handle(page, "selection") == "cntn_to_dcsn:Pullback"
    flow_handle(page, "setView", {**kept, "selection": None})
    wait_until(lambda: page.evaluate(SELECTED_BOXES_JS) == [], 5.0, "no box selected")
    assert flow_handle(page, "selection") is None
    page.wait_for_timeout(500)
    assert record(page, "selections") == selections
    assert flow_handle(page, "layouts") == layouts
    assert viewport(page) == before

    place = f"8:{original.split(chr(10))[7].index(':=') + 1}"
    click_before(page, 8, ":=")
    wait_until(lambda: status_place(page) == place, 5.0, f"the place {place}")
    cell = page.locator('.bl-class-row[data-identity="cons:cntn:V"] .bl-class-set')
    cursor = ("anchor", "head", "line", "column")
    for height in (1000, 700):
        if height != 1000:
            taller = page.evaluate(EDITOR_HEIGHT_JS)
            page.set_viewport_size({"width": 1600, "height": height})
            wait_until(
                lambda: page.evaluate(EDITOR_HEIGHT_JS) < taller, 5.0, "the editor made shorter"
            )
        page.evaluate(SCROLL_EDITOR_JS, 40)
        cell.focus()
        taken = editor_handle(page, "view")
        assert taken["line"] == 8 and taken["top"] == 40
        below = page.evaluate(LINE_BELOW_EDITOR_JS, 20)
        editor_handle(page, "previewLine", 20)
        wait_until(
            lambda: page.evaluate(PREVIEW_LINES_JS) == [20], 5.0, f"line 20 marked at {height} px"
        )
        if height == 700:
            assert below
            wait_until(
                lambda: editor_handle(page, "view")["top"] != taken["top"],
                5.0,
                "the editor scrolled to line 20",
            )
            assert not page.evaluate(LINE_BELOW_EDITOR_JS, 20)
        # longer than the editor's pause of 120 ms before it reports the cursor
        page.wait_for_timeout(300)
        now = editor_handle(page, "view")
        assert {key: now[key] for key in cursor} == {key: taken[key] for key in cursor}
        assert cell.evaluate(FOCUSED_JS)
        assert status_place(page) == place
        editor_handle(page, "setView", taken)
        wait_until(
            lambda: page.evaluate(PREVIEW_LINES_JS) == [] and editor_handle(page, "view") == taken,
            5.0,
            f"the editor's view restored at {height} px",
        )
        page.wait_for_timeout(300)
        assert editor_handle(page, "view") == taken
        assert cell.evaluate(FOCUSED_JS)
        assert status_place(page) == place

    document = page.evaluate(DOCUMENT_JS)
    for text in ("argmax", "ARGMAX", "C^("):
        assert editor_handle(page, "findText", text) == lines_holding(text, document), text
    assert lines_holding("argmax", document)
    # a match after a character outside the Basic Multilingual Plane, 𝑢 or 𝑑,
    # whose column in code points is less than its column in code units
    assert any(
        len(row["text"][: row["column"] - 1].encode("utf-16-le")) // 2 > row["column"] - 1
        for row in lines_holding("C^(", document)
    )
    assert page.evaluate(DOCUMENT_JS) == original


def test_r_goto_offers_no_box_of_a_previous_construction(page, server, original):
    """Unit R, brief rule 9 with review 1 (spec 0.4 §5.8, last sentence:
    refused or unavailable graph addresses are not guessed from old line
    numbers): with cons.bl constructed, `@` lists the blocks of the text
    and the boxes of the graph shown. After an edit that renames the block
    `dcsn_to_arvl` to `back_to_arvl` and that the package refuses after it
    parses, the graph shown is the previous construction, and `@` lists the
    blocks of the text as it now stands, each at its header's line, the new
    name among them and the old one not, and no result of kind `box`. The
    palette changes no text."""
    open_cons(page, server)
    open_goto(page)
    page.keyboard.type("@")
    wait_until(
        lambda: {"block", "box"} <= {result["kind"] for result in goto_results(page)},
        5.0,
        "the blocks and the boxes of the construction",
    )
    page.keyboard.press("Escape")
    wait_until(lambda: not page.locator(".bl-goto").is_visible(), 5.0, "the palette closed")

    refused = original.replace("[id=dcsn_to_arvl, (V, dV)", "[id=back_to_arvl, (V, dW)")
    replace_in_editor(page, "[id=dcsn_to_arvl, (V, dV)", "[id=back_to_arvl, (V, dW)")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == refused, 5.0, "the edit in the editor")
    wait_until(
        lambda: page.locator(".bl-status-summary .bl-status-state").text_content()
        == "parsed, refused",
        10.0,
        "the construction refused",
    )
    page.wait_for_selector(".bl-view-host.bl-stale", timeout=10_000)
    spans = source_spans(refused, CONS)
    blocks = sorted(
        (span.line, name) for name, span in spans.items() if "." not in name and not name.isdigit()
    )
    open_goto(page)
    page.keyboard.type("@")
    expected = [{"text": name, "kind": "block", "address": f"{line}:1"} for line, name in blocks]
    wait_until(
        lambda: [
            {key: result[key] for key in ("text", "kind", "address")}
            for result in goto_results(page)
        ]
        == expected,
        5.0,
        "the blocks of the refused text and no box",
    )
    texts = [result["text"] for result in goto_results(page)]
    assert "back_to_arvl" in texts and "dcsn_to_arvl" not in texts
    page.keyboard.press("Escape")
    wait_until(lambda: not page.locator(".bl-goto").is_visible(), 5.0, "the palette closed")
    assert page.evaluate(DOCUMENT_JS) == refused


@pytest.mark.parametrize("end, side, field, written, endpoints", [
    ("target", "reading", "z", "a: z", ("S", "U")),
    ("source", "writing", "c", "c: a", ("U", "T")),
])
def test_comp_an_inferred_arrow_moves_in_the_page_and_undo_restores_its_source(
    browser, server_on, tmp_path, end, side, field, written, endpoints,
):
    from workbench_support import (
        cable_list, cable_port, composition_folder, join_wires_drawn, move_join_end,
        new_tab, open_trellis, open_tree_file, choose_view, click_join, click_line, drag_ports,
    )
    from bellman_workbench import model, recipe, trellis

    path = composition_folder(tmp_path / "composition")
    folder = model.open_folder(path)
    before = (path / "period.yml").read_text(encoding="utf-8")
    context, tab = new_tab(browser)
    try:
        url = server_on(path)
        open_trellis(tab, url, "trellis.yml", minimum=3)
        open_tree_file(tab, "period.yml")
        choose_view(tab, None, "forward")
        wait_until(lambda: any(w["from"] == "periods[0]/S" for w in join_wires_drawn(tab)),
                   30.0, "the inferred connection")
        click_join(tab, "periods[0]/S", "periods[0]/T")
        # the moved end lands on `U`'s cable port of its side, the arrival port
        # or the port of its one branch (design pass 10 §§6 and 7); the cable
        # carries one wire and the side dropped on holds one field, so that no
        # list opens and the event names the field's port
        target = cable_port(tab, "periods[0]/U", side)
        move_join_end(tab, "periods[0]/S", "periods[0]/T", end, target)
        wait_until(lambda: written in tab.evaluate(DOCUMENT_JS), 15.0, "the authored replacement")
        wait_until(lambda: any((w["from"], w["to"]) == tuple(f"periods[0]/{key}" for key in endpoints)
                               for w in join_wires_drawn(tab)), 30.0, "the replacement connection")
        assert (path / "period.yml").read_text(encoding="utf-8") == before
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == before, 15.0, "the source restored by undo")
        wait_until(lambda: any((w["from"], w["to"]) == ("periods[0]/S", "periods[0]/T")
                               for w in join_wires_drawn(tab)), 30.0, "the inferred connection restored")
        tab.keyboard.press("ControlOrMeta+Shift+z")
        wait_until(lambda: written in tab.evaluate(DOCUMENT_JS), 15.0, "the authored source restored by redo")
        wait_until(lambda: any((w["from"], w["to"]) == tuple(f"periods[0]/{key}" for key in endpoints)
                               for w in join_wires_drawn(tab)), 30.0, "the replacement restored by redo")
        # a new cable from `T`'s unjoined branch to `S`'s arrival port opens
        # the cable's list with `S`'s one arrival field and a select of `T`'s
        # one continuation field, which the author pairs (design pass 10 §7)
        drag_ports(tab, cable_port(tab, "periods[0]/T", "writing"), cable_port(tab, "periods[0]/S", "reading"))
        listed, _ = wait_until(lambda: cable_list(tab), 10.0, "the cable's list")
        assert listed["count"] == "0 of 1 field paired" and [row[0] for row in listed["rows"]] == ["x : ℝ₊"], listed
        select = tab.locator(".bl-view-host .bf-pair-row select.bf-pair-from").first
        select.select_option(value=select.locator("option", has_text="y").get_attribute("value"))
        tab.click(".bl-view-host .bf-pair-join")
        wait_until(lambda: "y: x" in tab.evaluate(DOCUMENT_JS), 15.0, "a new cable after reconnection")
        saved = tab.evaluate(DOCUMENT_JS)
        tab.click(".bl-save")
        wait_until(lambda: (path / "period.yml").read_text(encoding="utf-8") == saved,
                   15.0, "the moved connector saved")
        fresh_context, fresh = new_tab(browser)
        try:
            open_trellis(fresh, url, "trellis.yml", minimum=3)
            open_tree_file(fresh, "period.yml")
            choose_view(fresh, None, "forward")
            wait_until(lambda: any((w["from"], w["to"]) == tuple(f"periods[0]/{key}" for key in endpoints)
                                   for w in join_wires_drawn(fresh)), 30.0, "the authored connection after reopening")
            assert fresh.evaluate(DOCUMENT_JS) == saved
            reopened = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
            assert any(pair.origin == "authored" and (pair.writing.key, pair.reading.key) == endpoints
                       for pair in reopened.selection.pairs)
            backward = graph_named(reopened.collection, "backward")
            assert backward["nodes"] and not any(n["id"] == "backward:refused" for n in backward["nodes"])
            choose_view(fresh, None, "backward")
            wait_until(lambda: fresh.locator('.react-flow__node[data-id="periods[0]/S___group___"]').count() == 1,
                       15.0, "the certified backward stage after reopening")
        finally:
            fresh_context.close()
        unresolved = before.replace("[{}]", "[{Missing.a: T.a}]")
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+a")
        tab.keyboard.insert_text(unresolved)
        wait_until(lambda: any("Missing.a" in line[0] for line in error_lines(tab)),
                   15.0, "the package reason for the retained unresolved connector")
        assert tab.evaluate(DOCUMENT_JS) == unresolved
        assert not any(w["from"] == "periods[0]/S" for w in join_wires_drawn(tab))
        assert (path / "period.yml").read_text(encoding="utf-8") == saved
    finally:
        context.close()


@pytest.mark.parametrize("branch, other", [("up", "dn"), ("dn", "up")])
def test_comp_a_branch_arrow_names_and_removes_only_its_own_pairs(browser, server_on, tmp_path, branch, other):
    from workbench_support import composition_folder, new_tab, open_trellis, open_tree_file, choose_view
    from bellman.trellis import entry_value

    path = composition_folder(tmp_path / "branches", branching=True)
    before = (path / "period.yml").read_text(encoding="utf-8")
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(path), "trellis.yml", minimum=3)
        open_tree_file(tab, "period.yml")
        choose_view(tab, None, "forward")
        tab.click('.react-flow__node[data-id="periods[0]/S___group___"] .bf-layer-name')
        edges = tab.locator('.react-flow__edge.bf-join-wire[data-from="periods[0]/S"][data-to="periods[0]/T"]')
        wait_until(lambda: edges.count() == 2, 20.0, "the two branch arrows")
        expected = f"x_{branch} → x; y_{branch} → y"
        own = edges.filter(has=tab.locator("title", has_text=expected))
        assert own.count() == 1
        assert f"x_{other}" not in own.locator("title").text_content()
        # the cable's label is its branch's label, `up` or `down`; its hover names its joins (design pass 10 §6)
        assert own.locator(".bf-join").text_content() == {"up": "up", "dn": "down"}[branch]
        point = own.locator(".react-flow__edge-path").evaluate("""path => {
          const point = path.getPointAtLength(path.getTotalLength() / 2);
          const screen = new DOMPoint(point.x, point.y).matrixTransform(path.getScreenCTM());
          return {x: screen.x, y: screen.y};
        }""")
        tab.mouse.click(point["x"], point["y"])
        wait_until(lambda: own.get_attribute("class").split().count("selected") == 1,
                   5.0, "the branch arrow selected")
        own.focus()
        tab.keyboard.press("Delete")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) != before, 15.0, "the selected branch source removed")
        assert entry_value(tab.evaluate(DOCUMENT_JS), "connectors") == [{
            f"S.x_{other}": "T.x", f"S.y_{other}": "T.y",
        }]
        assert (path / "period.yml").read_text(encoding="utf-8") == before
    finally:
        context.close()


@pytest.mark.parametrize("invalid", [True, False])
def test_comp_problems_are_one_keyboard_control_with_source_navigation(browser, server_on, tmp_path, invalid):
    from workbench_support import composition_folder, new_tab, open_trellis, open_path_shown

    path = composition_folder(tmp_path / "problems", repeat=2)
    period = path / "period.yml"
    if invalid:
        period.write_text(period.read_text().replace("connectors: [{}]", "connectors: [{S.a: U.typo}]"))
    before = {file.name: file.read_bytes() for file in path.iterdir() if file.is_file()}
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(path), "trellis.yml", minimum=3)
        button = tab.locator(".bl-view > .bl-graph-bar .bl-error-mark")
        assert tab.locator(".bl-error-mark").count() == 1
        assert tab.locator(".bl-folder .bl-checklist").count() == 0
        label = button.get_attribute("aria-label")
        assert "errors" in label
        assert ("bl-has-errors" in button.get_attribute("class")) == invalid
        if not invalid:
            assert "0 errors" in label and "to review" in label
        button.focus()
        tab.keyboard.press("Enter")
        tab.wait_for_selector(".bl-error-list", state="visible", timeout=10_000)
        assert button.get_attribute("aria-expanded") == "true"
        assert tab.locator(".bl-problem-unjoined .bl-problem-scope").text_content() == "Whole model"
        source = tab.locator('.bl-error-place[data-path="period.yml"]').first if invalid else tab.locator('.bl-checklist-unjoined[data-file="period.yml"]').first
        source.focus()
        tab.keyboard.press("Escape")
        tab.wait_for_selector(".bl-error-list", state="hidden", timeout=10_000)
        assert button.evaluate("element => element === document.activeElement")
        tab.keyboard.press("Enter")
        tab.wait_for_selector(".bl-error-list", state="visible", timeout=10_000)
        tab.locator(".bl-view > .bl-graph-bar").click(position={"x": 8, "y": 8})
        tab.wait_for_selector(".bl-error-list", state="hidden", timeout=10_000)
        assert button.get_attribute("aria-expanded") == "false"
        button.click()
        tab.wait_for_selector(".bl-error-list", state="visible", timeout=10_000)
        # The heading and its open list are visible together in this image.
        tab.locator(".bl-view").screenshot(path=str(tmp_path / "problems-control.png"))
        source.focus()
        tab.keyboard.press("Enter")
        wait_until(lambda: open_path_shown(tab) == "period.yml", 30.0, "the problem source")
        assert {file.name: file.read_bytes() for file in path.iterdir() if file.is_file()} == before
    finally:
        context.close()
