"""The acceptance tests of unit L of model interface specification 0.4, the
Workbench after unit K and the UX simulation (the plan "Unit L of model
interface spec 0.4, the Workbench after unit K and the UX simulation:
implementation plan"): one test for each task's acceptance check, each
reading the page's elements, never a screenshot's pixels. Deleted when
the next amendment is accepted (lean implementation rule, layer 2).
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import time
from collections import Counter
from pathlib import Path

from workbench_support import (
    CONTRIBUTION_JOIN_ROWS,
    ACTIVE_LINE_JS,
    CONS,
    CONTRAST_EXCEPTIONS,
    DETAILS_ROWS_JS,
    DOCUMENT_JS,
    DRAWN_PLACES_JS,
    DURABLES,
    FRAME_TRACKS,
    GROUND_JS,
    HELD_COLLECTION_JS,
    KEEPER_CONS,
    LAYER_IN_REGION_JS,
    PAGE_FORMS,
    PENSIONS_RECIPE,
    PENSIONS_TRELLIS,
    PENSIONS_WORKING_YEARS,
    PORT,
    PORT_ID,
    PORTFOLIO_CHOICE,
    READING_SCALE,
    RECIPE_FILE,
    REGION_READING_JS,
    ROOT,
    SELECTED_TEXT_JS,
    TABLE_ROWS_JS,
    TENURE,
    TWO_FRAMES_JS,
    TWO_STAGES,
    add_field,
    add_period_controls,
    as_json,
    bound_as_the_recipe_binds,
    boxes,
    carried_functions,
    changed_lines,
    choose_option,
    choose_view,
    click_before,
    click_join,
    click_line,
    click_toggle,
    connected_event,
    contrast_faults,
    corpus_startup,
    cut_within_a_word,
    details_until,
    digest7,
    double_click_node,
    cable_list,
    cable_port,
    drag_cable,
    drawn_extent,
    drop_by_keyboard,
    drop_item,
    dropped_event,
    edited,
    emptied_portfolio,
    error_group_lines,
    error_lines,
    field_port,
    field_tables,
    file_bytes,
    file_tabs,
    flow_handle,
    free_port,
    gesture_note,
    git,
    graph_named,
    held_events,
    held_joins,
    hold_events,
    in_function_italic,
    init_repository,
    join_wires_drawn,
    joined_states,
    keyboard_place,
    layout_record,
    layout_records,
    layouts_recorded,
    line_text,
    move_join_end,
    lay_out_left_to_right,
    new_tab,
    occurrences_of,
    open_cons,
    open_every_folder,
    open_file,
    open_page_form,
    open_path_shown,
    open_recipe_row,
    open_stage_list,
    open_tree_file,
    open_trellis,
    open_workbench,
    opens_on,
    pensions_copy,
    pensions_life_cycle,
    pensions_with_bequest_dur,
    period_opening,
    property_color,
    recipe_head,
    record_layouts,
    refused_corpus,
    release_events,
    repository_copy,
    restrict,
    restriction_shown,
    reveal_in_tree,
    save_unsaved_files,
    select_node,
    select_until,
    server_error,
    settled_status,
    stage_line,
    stage_name,
    start_server,
    status_settled_on,
    status_text,
    stop_server,
    tracks,
    tracks_near,
    tree_names,
    trellis_settled,
    unjoined_field_ids,
    unsaved_in_tree,
    view_still,
    viewport,
    wait_until,
    with_each_recipe_row_open,
)

from bellman.stage import LAYER_ID_ENDING, admitted_methods, elaborate_text, source_spans
from bellman.trellis import entry_value
from bellman_workbench import app, creation, icons, model, recipe, trellis


def test_task_1_a_decision_field_is_listed_in_both_blocks_that_carry_the_decision_perch(
    page, server, cons_file, original
):
    """Task 1 (AAS, L-D1; AMD-MI-002 §5 rule 2): on the portfolio model's
    cons.bl, `q`, `ℝ₊`, `state` in the box `add field` of the decision
    group writes both block headers in one edit: the outputs of
    arvl_to_dcsn, line 13, gain `q : ℝ₊`, and the inputs of dcsn_to_cntn,
    line 17, gain `q` alone, the side's `!dcsn` standing for it. The editor
    holds those two lines changed and no other, and the group's note names
    the declaration's line and the listing's block (Task 5). The loop
    refuses the text until an equation of arvl_to_dcsn defines q
    (`output-defined`); with `q = m` typed there, the stage constructs
    again, and the decision table lists q among its fields, its name
    linked to its box. The file on disk is unchanged, since the tab
    changes it by `save` alone."""
    line_13 = "[id=arvl_to_dcsn, (m : Xm) : !arvl -> (m_d : Xm, q : ℝ₊) : !dcsn] {"
    line_17 = "[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊, q) : !dcsn -> (a : Xa) : !cntn] {"
    written = edited(edited(original, 13, line_13), 17, line_17)
    open_cons(page, server)
    add_field(page, "dcsn/", "q", "ℝ₊", "state")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == written, 5.0, "q on lines 13 and 17")
    assert changed_lines(original, page.evaluate(DOCUMENT_JS)) == [13, 17]
    assert (line_text(page, 13), line_text(page, 17)) == (line_13, line_17)
    note = page.locator('.bl-class-group[data-group="dcsn/"] .bl-class-note')
    note.wait_for(timeout=5_000)
    assert note.text_content() == "q : ℝ₊ written to line 13 and listed on dcsn_to_cntn"
    assert settled_status(page, digest7(written))["state"] == "parsed, refused"

    # the equation that defines q, typed before the `}` of arvl_to_dcsn
    defined = edited(written, 14, "    m_d = m\n    q = m")
    click_before(page, 15, "}")
    page.keyboard.insert_text("    q = m\n")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == defined, 5.0, "the equation of q typed")
    assert settled_status(page, digest7(defined))["state"] == "constructed"

    def decision() -> list[str]:
        # the fields of the decision table, in its order
        return [row["field"] for row in page.evaluate(TABLE_ROWS_JS) if row["perch"] == "dcsn"]

    wait_until(
        lambda: decision() == ["m_d", "q", "c", "V", "dV"], 5.0, "q among the decision fields"
    )
    q = page.locator('.bl-class-row[data-identity="cons:dcsn:q"]')
    wait_until(lambda: q.locator("button.bl-class-field").count() == 1, 5.0, "q linked")
    assert cons_file.read_text(encoding="utf-8") == original


def test_task_2_matsyas_column_prints_no_sentence_about_its_index(page, server):
    """Task 2 (AAS, L-D2; the texts' rule): with cons.bl open, no element
    of Matsya's column holds the words "older than the repository", in its
    text or in an attribute, and its body holds the list of questions and
    the composer alone, with no empty element in the sentence's place. The
    head's heading `Matsya` and its symbol Υ, the question field and the
    button `ask` stand."""
    open_cons(page, server)
    column = page.locator(".bl-matsya")
    assert "older than the repository" not in column.inner_html()
    body = page.locator(".bl-matsya-body > *").evaluate_all("(all) => all.map((e) => e.className)")
    assert body == ["bl-matsya-exchanges", "bl-matsya-row"]
    assert page.locator(".bl-matsya-head h2").text_content() == "Matsya"
    assert page.locator(".bl-matsya-head .bl-matsya-upsilon").text_content() == "Υ"
    assert page.locator(".bl-matsya-field textarea").is_visible()
    assert page.locator(".bl-matsya-ask").is_visible()


def test_task_3_the_stage_name_stands_on_the_first_line_at_the_pages_size(
    page, server_on, durables_folder
):
    """Task 3 (AAS, L-D3; spec 0.4 §5.2): with the durables model's
    keeper_cons.bl open, the stage name `keeper_cons` is drawn at 18 px on
    a line height of 24 px, in Archivo at weight 400, in ice and at the
    width --bl-stage-name-stretch gives, and its line is 24 px high; the
    rest of the line, `@stage:`, stays in IBM Plex Mono at 12.5 px. The
    line after it is 17.9 px high, and every later line drawn is a whole
    number of 17.9-px lines. The gutter's line number beside the stage
    name reads 1, and its baseline stands within 2 px of the name's."""
    open_file(page, server_on(durables_folder), KEEPER_CONS)
    name = stage_name(page)
    assert name is not None and name["text"] == "keeper_cons"
    drawn = {"face": "Archivo", "size": 18.0, "lineHeight": 24.0}
    drawn.update(color=property_color(page, "--bl-ice"), stretch=name["stretch"])
    assert name["styles"] == [drawn]

    line = stage_line(page)
    assert line["number"] == "1"
    assert round(line["height"], 1) == 24
    assert line["weight"] == "400"
    assert line["source"] == [{"face": "IBM Plex Mono", "size": 12.5}]
    assert round(line["following"][0], 1) == 17.9
    for height in line["following"]:
        assert round(height / round(height / 17.9), 1) == 17.9, line["following"]
    assert abs(line["numberBaseline"] - line["nameBaseline"]) <= 2, line


def test_task_4_the_fields_tabs_set_column_takes_its_contents_width(
    page, server_on, durables_folder
):
    """Task 4 (AAS, L-D4; spec 0.4 §5.5), with the bounds of Task 27 (AAS,
    L-D21) and the widths of design pass 6 §3.5 (Task 29; AAS, L-D24):
    with the durables model's keeper_cons.bl open at 1600 × 1000, the
    Fields tab's three tables stand side by side, 12 px apart, under the
    titles `≺ Arrival`, `∼ Decision` and `≻ Continuation`, each headed
    `Field`, `Set`, `Role`. Each table ends with `+`'s column, 24 px, the
    cell of the button of its box `add field`. In each table the set column
    is as wide as its widest set with the cell's padding, at least four
    characters of the set's face with that padding and at most a third of
    the table, and each set's box fills it and reaches 3 px beyond it on
    each side; the role column is as wide as its widest role with the
    cell's padding, at least seven characters with that padding, and each
    role's box reaches 3 px before it and over `+`'s column; the field
    column takes the rest, and no field's name wraps, each name's element
    one line high. Each set and each name stands whole, `dV_w_kp[<]`
    included, and each hover is the name or the set whole. At 1220 × 1000
    the continuation table stands under the arrival table, its widths by
    the same rule. With tenure.bl open at 1460, where the text's column is
    568 px, as it was at 1600 before the window's left padding left (design
    pass 10 §2) and its right margin (design pass 13 §4; Q-D6), the
    decision table's set column is a third of the table,
    since `{keep, adjust}` is wider: that set is cut with an ellipsis, its
    hover the set whole; in the branch `adjust`, the name `dV_w_adj[>]`,
    wider than its column, is cut with an ellipsis, its hover the name
    whole."""

    def set_column(table: dict) -> float:
        # L-D4 and design pass 6 §3.5: the widest set with the cell's
        # padding, at most a third of the table, and at least four
        # characters with that padding
        widest = max((row["setText"] for row in table["rows"]), default=0)
        four = table["six"] * 4 / 6
        return max(four + table["gap"], min(widest + table["gap"], table["width"] / 3))

    def role_column(table: dict) -> float:
        # design pass 6 §3.5: the widest role with the cell's padding, at
        # least seven characters with that padding
        widest = max((row["roleText"] for row in table["rows"]), default=0)
        return max(table["six"] * 7 / 6, widest) + table["gap"]

    def assert_widths(tables: list[dict]) -> None:
        adds = {row["group"]: row["end"]["width"] for row in page.evaluate(ADD_ROWS_JS)}
        for table in tables:
            add = adds[table["group"]]
            field_width, set_width, role_width = table["columns"]
            assert abs(add - 24) < 0.5, (table, add)
            assert abs(set_width - set_column(table)) < 0.5, table
            assert abs(role_width - role_column(table)) < 0.5, table
            assert abs(field_width + set_width + role_width + add - table["width"]) < 0.5, table
            for row in table["rows"]:
                assert abs(row["height"] - row["lineHeight"]) < 0.5, row
                assert abs(row["setBox"] - (set_width - table["gap"] + 6)) < 0.5, row
                assert abs(row["role"] - (role_width - table["gap"] + 3 + add)) < 0.5, row

    url = server_on(durables_folder)
    open_file(page, url, KEEPER_CONS)
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)
    sections = boxes(page, ".bl-class-perch")
    assert len(sections) == 3 and {section["top"] for section in sections} == {sections[0]["top"]}
    for before, after in zip(sections, sections[1:]):
        assert abs(after["left"] - before["right"] - 12) < 0.5, (before, after)
    titles = page.locator(".bl-class-perch-name").all_text_contents()
    assert titles == ["≺ Arrival", "∼ Decision", "≻ Continuation"]
    assert page.locator(".bl-class-table th").all_text_contents() == ["Field", "Set", "Role"] * 3
    tables = field_tables(page)
    assert [table["perch"] for table in tables] == ["arvl", "dcsn", "cntn"]
    assert_widths(tables)
    rows = [row for table in tables for row in table["rows"]]
    assert [row["field"] for row in rows if row["fieldCut"]] == []
    for row in rows:
        assert row["fieldHover"] == row["field"], row
        assert not row["setCut"] and row["setHover"] == row["set"], row

    # a panel narrower than three tables: the third stands under the first,
    # at 1220 px, where the frame stood at 1280 before design pass 13 §4 took
    # the window's right margin of 60 px away (Q-D6)
    page.set_viewport_size({"width": 1220, "height": 1000})
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1220, False]), 5.0, "the frame at 1220")
    first, second, third = boxes(page, ".bl-class-perch")
    assert abs(first["top"] - second["top"]) < 0.5 and abs(third["left"] - first["left"]) < 0.5
    assert third["top"] > max(first["bottom"], second["bottom"])
    assert_widths(field_tables(page))

    # a set and a name wider than their columns: cut, whole in the hover; at
    # 1460 × 1000, since unit N's Task 1 took the window's left padding of 60
    # px away with the rail (design pass 10 §2) and design pass 13 §4 its
    # right margin of 60 px (Q-D6), which widened the text's column at 1600
    # from 568 to 645 px, and `dV_w_adj[>]` then stands whole; at 1460 the
    # column is 568 px again (FRAME_TRACKS)
    page.set_viewport_size({"width": 1460, "height": 1000})
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1460, False]), 5.0, "the frame at 1460")
    open_file(page, url, TENURE)
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)
    tables = field_tables(page)
    assert_widths(tables)
    (decision,) = [table for table in tables if table["perch"] == "dcsn"]
    assert abs(decision["columns"][1] - decision["width"] / 3) < 0.5, decision
    (d,) = [row for row in decision["rows"] if row["field"] == "d"]
    assert (d["set"], d["setCut"], d["setOverflow"], d["setHover"]) == (
        "{keep, adjust}", True, "ellipsis", "{keep, adjust}"
    )
    (adjust,) = [table for table in tables if table["group"] == "cntn/adjust"]
    cut = [(row["field"], row["fieldOverflow"], row["fieldHover"]) for row in adjust["rows"]
           if row["fieldCut"]]
    assert cut == [("dV_w_adj[>]", "ellipsis", "dV_w_adj[>]")]


def test_task_5_the_note_and_the_selection_after_add_follow_the_declaration(
    page, server, cons_file, original
):
    """Task 5 (Task 1's review, Minor 1; AAS, L-D1; amendment 02 ruling 9):
    on a copy of the portfolio model's cons.bl whose two forward blocks
    stand in the reverse order, dcsn_to_cntn on line 13 and arvl_to_dcsn on
    line 17, `q`, `ℝ₊`, `state` in the box `add field` of the decision
    group writes `q` alone on line 13 and `q : ℝ₊` on line 17. The editor
    selects line 17, the declaration's, though the listing comes first in
    the text, and the group's note is one sentence that names `q : ℝ₊`
    with its line and the block that lists it."""
    lines = original.split("\n")
    # the three lines of arvl_to_dcsn (13 to 15) and of dcsn_to_cntn (17 to
    # 19), written in the reverse order
    swapped = "\n".join(lines[:12] + lines[16:19] + lines[15:16] + lines[12:15] + lines[19:])
    cons_file.write_text(swapped, encoding="utf-8")
    line_13 = "[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊, q) : !dcsn -> (a : Xa) : !cntn] {"
    line_17 = "[id=arvl_to_dcsn, (m : Xm) : !arvl -> (m_d : Xm, q : ℝ₊) : !dcsn] {"
    written = edited(edited(swapped, 13, line_13), 17, line_17)
    open_cons(page, server)
    assert settled_status(page, digest7(swapped))["state"] == "constructed"
    add_field(page, "dcsn/", "q", "ℝ₊", "state")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == written, 5.0, "q on lines 13 and 17")
    assert changed_lines(swapped, page.evaluate(DOCUMENT_JS)) == [13, 17]
    wait_until(lambda: page.evaluate(SELECTED_TEXT_JS) == line_17, 5.0, "line 17 selected")
    note = page.locator('.bl-class-group[data-group="dcsn/"] .bl-class-note')
    note.wait_for(timeout=5_000)
    assert note.text_content() == "q : ℝ₊ written to line 17 and listed on dcsn_to_cntn"
    assert cons_file.read_text(encoding="utf-8") == swapped


# the portfolio model's stage folder of `port`, which the form from a folder
# copies (Task 6), and the path an author writes for it: from `~` where the
# home folder holds the checkout, else whole
PORT_FOLDER = ROOT / "applications/portfolio-choice/declaration/stages/port"
PORT_TYPED = (
    f"~/{PORT_FOLDER.relative_to(Path.home())}"
    if PORT_FOLDER.is_relative_to(Path.home())
    else str(PORT_FOLDER)
)
# The control `+ stage` of the layer the selector names, as the screen shows
# it, null where the layer draws none: its height, the size of its words on
# the screen (the computed size times the control's scale), its face and the
# face of the layer's name, its box against the layer's: its top, its middle
# and its bottom below the layer's top, its left beyond the name's right,
# its right short of the toggle's left, each in pixels on the screen; and
# whether the point at its middle is the control's, so that a click there
# takes it.
ADD_STAGE_SCREEN_JS = """
(selector) => {
  const layer = document.querySelector(`${selector} > .bf-layer`);
  const control = layer && layer.querySelector(':scope > .bf-add-stage');
  if (!control) return null;
  const name = layer.querySelector(':scope > .bf-layer-name');
  const at = control.getBoundingClientRect(), frame = layer.getBoundingClientRect();
  const style = getComputedStyle(control);
  return {
    height: at.height,
    words: parseFloat(style.fontSize) * at.height / control.offsetHeight,
    face: style.fontFamily,
    nameFace: getComputedStyle(name).fontFamily,
    top: at.top - frame.top,
    middle: (at.top + at.bottom) / 2 - frame.top,
    bottom: at.bottom - frame.top,
    afterName: at.left - name.getBoundingClientRect().right,
    beforeToggle:
      layer.querySelector(':scope > .bf-toggle').getBoundingClientRect().left - at.right,
    taken: control.contains(
      document.elementFromPoint((at.left + at.right) / 2, (at.top + at.bottom) / 2)),
  };
}
"""
# The form "add stage" from a folder as the page draws it, null where none
# is open: its heading, the label of its select of the period and the
# period chosen, null where it draws none, the stage's row's key, null where
# no row stands, whether `add the stage` acts, the refusal standing in the
# form, and whether the key field holds the focus. The fields and the
# select are VSCode Elements', whose value the element holds and which
# holds the focus while its own input does (design pass 8 §4; unit M, Task
# 6).
FOLDER_PERIOD_FORM_JS = """
() => {
  const form = document.querySelector('.bl-form[data-form="add stage"]');
  if (!form) return null;
  const select = form.querySelector('.bl-folder-period');
  const key = form.querySelector('.bl-create-key vscode-textfield');
  return {
    heading: form.querySelector('h2').innerText,
    label: select && select.querySelector('.bl-field-label').textContent.trim(),
    period: select && select.querySelector('vscode-single-select').value,
    key: key ? key.value : null,
    acts: !form.querySelector('.bl-add-submit').disabled,
    refusal: (form.querySelector('.bl-form-error') || {}).textContent || null,
    focused: key !== null && key === document.activeElement,
  };
}
"""


def test_task_6_from_a_folder_opens_from_the_head_s_list_with_a_period_and_the_control_keeps_24_px(
    browser, server_on, scratch_durables
):
    """Task 6 (AAS, L-D5; K-D26, K-D27). On a copy of the durables model,
    `periods 0–2`, its forward trellis graph shown. The item `From a
    folder…` chosen in the list the button `stages` opens names no period:
    the region sends the event `dropped` with no target, which the
    Workbench answers with the form "add stage" from a folder and, for
    each period drawn, the terminal period first, the period's list as a
    drop on its layer names it, the drop on a period's layer answering as
    before; `folder_entries` reads a path from `~` and a path with spaces
    around it. On the page, `+ stage` has a press target at least 24 px high
    on the screen and words in Archivo at 11 px times the graph's scale
    (design pass 13 and Q3a), between the name and the toggle, its bottom
    at the foot of its period's header row, G.periodHeader high, and
    taking a click, at the opening scale, 1 here (AAS, M-D15), where it
    stands inside the header row, at the scale of `fit` and at the reading
    scale of 0.6. Enter on the item in the head's
    list, and a click on it, each open the form, headed `Add stage from a
    folder`, with the select `Period` on `periods[0]` (unit M, Task 6).
    The path of the corpus's `port` folder written from `~` with spaces
    around it prints port's row; with the key `keeper_cons`,
    `add the stage` is refused in the form, which stays open with the key
    field holding the focus; `port` typed there in its place, `add the
    stage` copies `port` into the terminal period's list, drawn in
    periods[0], and writes `declaration/stages/port/`."""
    copy = scratch_durables
    # The current corpus includes an unused port folder; this test imports it anew.
    assert "port" not in creation.recipe_keys(copy)
    shutil.rmtree(copy / "declaration/stages/port")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(
        folder, recipe.Source("recipe", RECIPE_FILE), trellis.parse_restriction("periods 0–2")
    ).shown
    above = str(copy.resolve().parent)
    head = dropped_event(shown, folder, "folder", "folder", None)
    lists = [("trellis.yml", "periods[0]"), ("period.yml", ""), ("period.yml", "")]
    assert trellis.drop_edits(shown, head, {}) == {
        "form": "add stage",
        "fill": {
            "folder": above,
            "periods": [
                {"name": f"periods[{h}]", "period": period, "entry": entry}
                for h, (period, entry) in enumerate(lists)
            ],
        },
    }
    terminal_layer = f"periods[0]{LAYER_ID_ENDING}"
    on_terminal = dropped_event(shown, folder, "folder", "folder", terminal_layer)
    assert trellis.drop_edits(shown, on_terminal, {}) == {
        "form": "add stage",
        "fill": {"folder": above, "period": "trellis.yml", "entry": "periods[0]"},
    }
    port_entries = app.folder_entries(str(PORT_FOLDER))
    assert port_entries[1] == ("port.bl", str(PORT_FOLDER / "port.bl"))
    assert app.folder_entries(f"  {PORT_TYPED}  ") == port_entries
    assert app.folder_entries("~") == app.folder_entries(str(Path.home()))
    corpus_before = file_bytes(PORT_FOLDER)

    terminal = f'.bl-view-host .react-flow__node[data-id="{terminal_layer}"]'
    item = '.bl-view-host .bf-stage-item[data-kind="folder"]'
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")

        def at_opening() -> bool:
            nodes = tab.evaluate(DRAWN_PLACES_JS)["nodes"]
            place = nodes.get(terminal_layer)
            if not tab.evaluate(ADD_STAGE_SCREEN_JS, terminal) or place is None:
                return False
            at = {"ax": place["x"], "ay": place["y"], "width": place["width"]}
            at["height"] = place["height"]
            return opens_on(viewport(tab), at, drawn_extent(nodes))

        wait_until(at_opening, 60.0, "the graph at the opening scale")
        layer_header = tab.evaluate("() => window.BellmanFlowLayout.G.periodHeader")
        opened = flow_handle(tab, "view")
        scales = []
        for step in ("opening", "fit", "reading"):
            if step == "fit":
                tab.click(".bl-zoom-button[data-zoom='fit']")
            elif step == "reading":
                # the terminal layer's top right corner 20 px inside the region
                place = tab.evaluate(DRAWN_PLACES_JS)["nodes"][terminal_layer]
                right = viewport(tab)["width"] - 20 - (place["x"] + place["width"]) * READING_SCALE
                at_reading = {"x": right, "y": 20 - place["y"] * READING_SCALE, "zoom": READING_SCALE}
                flow_handle(tab, "setView", {**opened, "viewport": at_reading})
            tab.evaluate(TWO_FRAMES_JS)
            zoom = viewport(tab)["zoom"]
            scales.append(zoom)
            control = tab.evaluate(ADD_STAGE_SCREEN_JS, terminal)
            assert abs(control["height"] - max(24, 24 * zoom)) < 0.5, (step, zoom, control)
            assert abs(control["words"] - 11 * zoom) < 0.1, (step, zoom, control)
            assert control["face"].split(",")[0].strip('"') == "Archivo", control
            assert control["nameFace"].split(",")[0].strip('"') == "IBM Plex Mono", control
            assert control["afterName"] > 0 and control["beforeToggle"] >= 0, (step, zoom, control)
            assert abs(control["bottom"] - layer_header * zoom) < 0.5, (step, zoom, control)
            assert control["taken"], (step, zoom, control)
            if step == "opening":
                assert control["top"] >= 0, (zoom, control)
                assert control["bottom"] <= layer_header * zoom + 0.5, (zoom, control)
        print(f"task 6: + stage measured at the scales {[round(s, 3) for s in scales]}")
        rounded = {round(s, 3) for s in scales}
        assert len(rounded) == 3 and max(scales) == 1 and READING_SCALE in rounded, scales
        flow_handle(tab, "setView", opened)

        # Enter on the item in the head's list: the event with no target
        hold_events(tab, "dropped")
        open_stage_list(tab)
        tab.focus(item)
        tab.keyboard.press("Enter")
        wait_until(lambda: held_events(tab, "dropped"), 10.0, "the event dropped")
        reading = tab.evaluate(REGION_READING_JS)
        assert held_events(tab, "dropped") == [
            {"item": "folder", "kind": "folder", "target": None, "reading": reading}
        ]
        assert tab.locator(".bl-view-host .bf-stage-list").count() == 0
        release_events(tab, "dropped")
        # since unit M's Task 6 each field of a form is its own component,
        # field.vue, which the browser can draw after the form's head, so the
        # form is read once its select shows a period
        form, _ = wait_until(
            lambda: (drawn := tab.evaluate(FOLDER_PERIOD_FORM_JS)) and drawn["period"] and drawn,
            30.0,
            "the form with its select of the period",
        )
        assert (form["heading"], form["label"], form["period"]) == (
            "Add stage from a folder", "Period", "periods[0]"
        )
        tab.click(".bl-form .bl-form-cancel")
        wait_until(lambda: tab.evaluate(FOLDER_PERIOD_FORM_JS) is None, 10.0, "the form closed")

        # a click on the item, the path from `~` with spaces around it, and
        # the terminal period chosen
        open_stage_list(tab)
        tab.click(item)
        wait_until(lambda: tab.evaluate(FOLDER_PERIOD_FORM_JS), 30.0, "the form by a click")
        field = ".bl-form .bl-folder-path input"
        assert tab.locator(field).input_value() == above
        tab.fill(field, f"  {PORT_TYPED}  ")
        tab.press(field, "Enter")
        row = f'.bl-form .bl-template[data-template="{PORT_TYPED}"]'
        tab.wait_for_selector(row, timeout=30_000)
        # the row is printed before the page proposes its key
        wait_until(lambda: tab.evaluate(FOLDER_PERIOD_FORM_JS)["acts"], 30.0, "port's row chosen")
        period = tab.locator(".bl-form .bl-folder-period vscode-single-select")
        period.click()
        options = period.get_by_role("option")
        options.first.wait_for(timeout=5_000)
        assert [text.strip() for text in options.all_text_contents()] == [
            "periods[0]", "periods[1]", "periods[2]"
        ]
        period.get_by_role("option", name="periods[0]", exact=True).click()
        form = tab.evaluate(FOLDER_PERIOD_FORM_JS)
        assert (form["period"], form["key"], form["acts"]) == ("periods[0]", "port", True)

        # a held key refused, the key field keeping the focus, another typed
        tab.fill(".bl-form .bl-create-key input", "keeper_cons")
        tab.click(".bl-form .bl-add-submit")
        form, _ = wait_until(
            lambda: (drawn := tab.evaluate(FOLDER_PERIOD_FORM_JS))["refusal"] and drawn,
            10.0,
            "the refusal",
        )
        assert form["refusal"] == "declaration/stages/keeper_cons/ exists"
        wait_until(lambda: tab.evaluate(FOLDER_PERIOD_FORM_JS)["focused"], 5.0, "the key focused")
        tab.keyboard.press("ControlOrMeta+a")
        tab.keyboard.type("port")
        wait_until(lambda: tab.evaluate(FOLDER_PERIOD_FORM_JS)["key"] == "port", 5.0, "port typed")
        tab.click(".bl-form .bl-add-submit")
        # port is joined to nothing in the terminal period, which the note
        # names (unit N, Task 5; design pass 10 §7)
        note = (
            "trellis.yml, periods[0].stages: port written, periods 0; "
            "new: stages/port/port.bl, stages/port/methods.bl; port unconnected"
        )
        wait_until(
            lambda: gesture_note(tab) == note and tab.evaluate(FOLDER_PERIOD_FORM_JS) is None,
            30.0,
            "the copy's note and the form closed",
        )
        assert (copy / "declaration/stages/port/port.bl").is_file()
        assert (copy / "declaration/stages/port/methods.bl").is_file()
        wait_until(
            lambda: "periods[0]/port"
            in occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "forward"),
            60.0,
            "port drawn in periods[0]",
        )
        edited_files = [RECIPE_FILE, "declaration/trellis.yml"]
        wait_until(lambda: unsaved_in_tree(tab) == edited_files, 10.0, "the two files unsaved")
        assert save_unsaved_files(tab) == edited_files
        written = (copy / "declaration/trellis.yml").read_text(encoding="utf-8")
        assert entry_value(written, "periods[0].stages") == [
            "tenure", "keeper_cons", "adjuster_cons", "bequest", "port"
        ]
        assert file_bytes(PORT_FOLDER) == corpus_before
    finally:
        context.close()


# The answers.yml Task 7's test gives its copy of the durables model, which
# the corpus's folder does not hold, so that the copy of a stage of the
# library records its origin there, as unit K's Task 25 test gives one
DURABLES_ANSWERS = (
    "# the answers of the test's copy of the durables model\n"
    "stages: {}\n"
    "required:\n"
    "  slots: []\n"
    "  connectors: []\n"
)
# The stage list as the page draws it, null where none is open: its section
# heading lines and its items in their order, a heading line as `section`
# and its text, an item as its kind and its id.
STAGE_LIST_LINES_JS = """
() => {
  const list = document.querySelector('.bl-view-host .bf-stage-list');
  if (!list) return null;
  return Array.from(list.querySelectorAll('.bf-stage-section, .bf-stage-item'), (line) =>
    line.classList.contains('bf-stage-section')
      ? ['section', line.textContent] : [line.dataset.kind, line.dataset.item]);
}
"""


def test_task_7_a_stage_of_the_library_is_listed_under_library_and_copied_with_its_origin(
    browser, server_on, scratch_durables, tmp_path, monkeypatch
):
    """Task 7 (AAS, L-D6; K-D26). With `BELLMAN_STAGE_LIBRARY` naming a
    temporary folder that holds a copy of the corpus's `port` stage folder,
    on a copy of the durables model given an answers.yml, `periods 0–2`, its
    forward trellis graph shown: the list the button `stages` opens prints
    the heading line `This folder's stages` and the model's stages (Task
    10), then the heading line `Templates` and the corpus's templates, then
    the heading line `Library` and `port`, the stage of the library, by its
    folder's path, and last `From a folder…`, the words in sentence case
    (design pass 13 §3). `port`
    dragged onto periods[1] copies `port.bl` and its addition under
    `declaration/stages/port/` with the texts and the note the Workbench's
    drop answers for that event, and `port` is drawn in periods[1] and
    periods[2]; once the three files the tree marks unsaved are saved,
    answers.yml records the stage's origin, its folder in the library, and
    the SHA-256 of `port.bl` and `methods.bl`, and the recipe names the
    copy and never the library. Nothing in the library is written."""
    library = tmp_path / "library"
    shutil.copytree(PORT_FOLDER, library / "port")
    monkeypatch.setenv(creation.LIBRARY_VARIABLE, str(library))
    origin = str(library / "port")
    copy = scratch_durables
    # The current corpus includes an unused port folder; this test imports it anew.
    assert "port" not in creation.recipe_keys(copy)
    shutil.rmtree(copy / "declaration/stages/port")
    (copy / creation.ANSWERS).write_text(DURABLES_ANSWERS, encoding="utf-8")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(
        folder, recipe.Source("recipe", RECIPE_FILE), trellis.parse_restriction("periods 0–2")
    ).shown
    period = f"periods[1]{LAYER_ID_ENDING}"
    event = dropped_event(shown, folder, origin, "library", period)
    expected = trellis.drop_edits(shown, event, {})
    assert [path for path, _ in expected.new_files] == [
        "declaration/stages/port/port.bl",
        "declaration/stages/port/methods.bl",
    ]
    lines = (
        [["section", "This folder's stages"]]
        + [["stage", key] for key in creation.recipe_keys(copy)]
        + [["section", "Templates"]]
        + [["template", template.id] for template in creation.stage_templates()]
        + [["section", "Library"], ["library", origin], ["folder", "folder"]]
    )
    library_before = file_bytes(library)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        layer = f'.bl-view-host .react-flow__node[data-id="{period}"] > .bf-layer'
        wait_until(
            lambda: tab.locator(f"{layer} > .bf-add-stage").count() == 1,
            60.0,
            "+ stage of periods[1]",
        )
        open_stage_list(tab)
        assert tab.evaluate(STAGE_LIST_LINES_JS) == lines

        # the drop of the stage of the library, its note, its drawing, and
        # answers.yml once saved
        drop_item(tab, origin, period)
        wait_until(lambda: gesture_note(tab) == expected.note, 30.0, "the note of the copy")
        for relative, text in expected.new_files:
            assert (copy / relative).read_text(encoding="utf-8") == text
        wait_until(
            lambda: {"periods[1]/port", "periods[2]/port"}
            <= occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "forward"),
            60.0,
            "port drawn in periods[1] and periods[2]",
        )
        edited_files = [creation.ANSWERS, "declaration/period.yml", RECIPE_FILE]
        wait_until(lambda: unsaved_in_tree(tab) == edited_files, 10.0, "the three files unsaved")
        assert save_unsaved_files(tab) == edited_files
        answers = (copy / creation.ANSWERS).read_text(encoding="utf-8")
        assert entry_value(answers, "stages.port") == {
            "origin": origin,
            "sha256": {
                name: hashlib.sha256((library / "port" / name).read_bytes()).hexdigest()
                for name in ("port.bl", "methods.bl")
            },
        }
        spec = (copy / RECIPE_FILE).read_text(encoding="utf-8")
        row = creation.recipe_row("port", ("stages/port/methods.bl",))
        assert f"  port: {row}" in spec and origin not in spec
        assert file_bytes(library) == library_before
    finally:
        context.close()


# The layer of the occurrence `keeper_cons` of the durables model's terminal
# period, and its height at scale 1 in the forward trellis graph's opening
# before Task 8, its builders and its own `Inputs` and `Outputs` laid out
# by ELK inside it, measured at 74dd94817 (AAS, L-D7)
KEEPER_CONS_LAYER = f"periods[0]/keeper_cons{LAYER_ID_ENDING}"
KEEPER_CONS_EARLIER = 354
# the height at scale 1 of a builder's segment in the strip of a compact
# occurrence's card, and in the band of the selected card (design pass 13
# §2, rules 5 and 7; AAS, L-D25); the strip's room from the card's left and
# right edges, the band's room from them, and the gap between two segments
STRIP_HIGH = 3
BAND_HIGH = 20
STRIP_LEFT, STRIP_RIGHT = 9, 29
BAND_LEFT, BAND_RIGHT = 1, 8
SEGMENT_GAP = 2
# the step of a band segment's width, each as wide as its id and its signs
# with their padding, rounded up to it (design pass 13 §2, rule 7)
SEGMENT_STEP = 8
# the share of ice in the ground of the policy builder's segment, the third
# tint (design pass 13 §2, rule 5; Q-D18)
POLICY_SHARE = 0.34
# The builders' segments of each stage of the durables model in its forward
# and its backward graph, each (pair, id, signs, hover), in the order the
# occurrence's card draws them from left to right: the stages' forward
# builders join the pairs `arvl,dcsn` and `dcsn,cntn`, bequest's the first
# alone, and the backward builders `cntn,dcsn` and `dcsn,arvl`, then the
# policy builder where the stage has one; a segment's hover names the pair
# in words and the id, the id alone where the words are the id (unit L's
# final judgment, §6 item 9), and the selected card's band prints the signs
# and the id (AAS, L-D16 and L-D25; design pass 7 §3)
ARRIVING = ("arvl,dcsn", "arvl_to_dcsn", "≺∼", "arrival to decision · arvl_to_dcsn")
LEAVING = ("dcsn,cntn", "dcsn_to_cntn", "∼≻", "decision to continuation · dcsn_to_cntn")
DURABLES_FORWARD = {
    "tenure": [ARRIVING, LEAVING],
    "keeper_cons": [ARRIVING, LEAVING],
    "adjuster_cons": [ARRIVING, LEAVING],
    "bequest": [ARRIVING],
}
KEEPER_CONS_BACKWARD = [
    ("cntn,dcsn", "cntn_to_dcsn", "≻∼", "continuation to decision · cntn_to_dcsn"),
    ("dcsn,arvl", "dcsn_to_arvl", "∼≺", "decision to arrival · dcsn_to_arvl"),
    ("policy", "policy", "", "policy"),
]
# An open stage occurrence of the graph shown, whose layer id is given, null
# where the region draws no open layer of it: its frame and its size at
# scale 1, its name and the labels beside its reading and its writing
# ports, each its box on the screen; each segment of a builder drawn inside
# it, from left to right, with its node's id, its `data-pair`, its hover,
# its size at scale 1, the three channels of its ground as the browser draws
# it, the signs and the id printed in it and all its text; and the ice and
# the lit navy as the browser draws them.
BUILDER_BOXES_JS = """
(occurrence) => {
  const drawn = (color) => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const context = canvas.getContext('2d');
    context.fillStyle = color.trim();
    context.fillRect(0, 0, 1, 1);
    return Array.from(context.getImageData(0, 0, 1, 1).data.slice(0, 3));
  };
  const at = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, right: found.right, top: found.top, bottom: found.bottom};
  };
  const host = document.querySelector('.bl-view-host');
  const frame = host && host.querySelector(
    `.react-flow__node[data-id="${CSS.escape(occurrence)}"] > .bf-layer`);
  if (!frame) return null;
  const inside = occurrence.slice(0, -'___group___'.length) + '/';
  const text = (box, selector) => (box.querySelector(selector) || {}).textContent ?? null;
  const builders = Array.from(host.querySelectorAll('.react-flow__node'))
    .filter((node) => node.dataset.id.startsWith(inside)
      && node.querySelector(':scope > .bf-builder'))
    .map((node) => {
      const box = node.querySelector(':scope > .bf-builder'), style = getComputedStyle(box);
      return {id: node.dataset.id, pair: box.dataset.pair || null,
              hover: box.getAttribute('title'), width: node.offsetWidth,
              height: node.offsetHeight, ground: drawn(style.backgroundColor),
              signs: text(box, '.bf-builder-signs'), name: text(box, '.bf-builder-id'),
              text: box.textContent, at: at(box),
              textRight: Math.max(-Infinity, ...Array.from(
                box.querySelectorAll('.bf-builder-signs, .bf-builder-id'), (part) => part.getBoundingClientRect().right))};
    })
    .sort((one, other) => one.at.left - other.at.left);
  const root = getComputedStyle(document.documentElement);
  return {
    frame: at(frame), size: [frame.parentElement.offsetWidth, frame.parentElement.offsetHeight],
    name: at(frame.querySelector(':scope > .bf-layer-name')),
    reading: Array.from(frame.querySelectorAll(':scope > .bf-in'), at),
    writing: Array.from(frame.querySelectorAll(':scope > .bf-out'), at),
    builders, ice: drawn(root.getPropertyValue('--bl-ice')),
    navy: drawn(root.getPropertyValue('--bl-navy')),
    orange: drawn(root.getPropertyValue('--bl-orange')), mint: drawn(root.getPropertyValue('--bl-mint')),
  };
}
"""


def perch_grounds(found: dict) -> tuple:
    """The ground of each builder's segment of an occurrence
    (BUILDER_BOXES_JS), from left to right (design pass 14 §9; S-D14):
    `orange` for a segment drawn in the brand's orange, the builder that
    joins the continuation perch, `mint` for one drawn in its mint, the
    builder that joins the arrival perch, and otherwise the share of ice in
    its mixture of ice and the lit navy, to two places, the policy
    builder's (`tints`)."""
    grounds = []
    for box in found["builders"]:
        if box["ground"] == found["orange"]:
            grounds.append("orange")
        elif box["ground"] == found["mint"]:
            grounds.append("mint")
        else:
            grounds.append(tints({**found, "builders": [box]})[0])
    return tuple(grounds)


def tints(found: dict) -> tuple:
    """The share of ice in the ground of each builder's box of an
    occurrence (BUILDER_BOXES_JS), from left to right, each to two places;
    each ground is a mixture of ice and the lit navy, the same share in each
    of its three channels to within 0.02, and so no fifth color in the
    graph region (spec 0.4 §5.3)."""
    ice, navy = found["ice"], found["navy"]
    shares = []
    for box in found["builders"]:
        channels = [(c - n) / (i - n) for c, i, n in zip(box["ground"], ice, navy)]
        assert max(channels) - min(channels) <= 0.02, box
        shares.append(round(sum(channels) / 3, 2))
    return tuple(shares)


def compact_builders(tab, occurrence: str, expected: list[tuple], band: bool = False) -> dict:
    """Waits until the open occurrence whose layer id is `occurrence` draws
    one segment for each builder `expected` names, (pair, id, signs,
    hover), in that order from left to right, with those `data-pair`, node
    ids and hovers: in the strip, `band` false, printing no text, and in
    the band of the selected card, `band` true, printing the signs and the
    builder's id; asserts that the segments are STRIP_HIGH, or BAND_HIGH,
    px high at scale 1 and SEGMENT_GAP apart, the strip's running at equal
    widths within 1 px from STRIP_LEFT inside the card's left edge to
    STRIP_RIGHT inside its right edge, the band's from BAND_LEFT inside the
    left edge and ending by BAND_RIGHT inside the right edge, each as wide
    as its printed signs and id on the step SEGMENT_STEP (design pass 13 §2,
    rules 5 and 7; AAS, L-D25), and that each stands under the occurrence's
    name, inside its card and clear of every label of its reading and its
    writing ports; answers the segments (BUILDER_BOXES_JS) with the ice and
    the lit navy."""
    inside = occurrence[: -len(LAYER_ID_ENDING)]

    def drawn():
        found = tab.evaluate(BUILDER_BOXES_JS, occurrence)
        seen = found and [
            (
                box["pair"],
                box["id"][len(inside) + 1 : -len(LAYER_ID_ENDING)],
                (box["signs"] or "") if band else "",
                box["hover"],
                box["name"] if band else box["text"],
            )
            for box in found["builders"]
        ]
        wanted = [
            (pair, name, signs if band else "", hover, name if band else "")
            for pair, name, signs, hover in expected
        ]
        return seen == wanted and found

    try:
        found, _ = wait_until(drawn, 60.0, f"the builders of {occurrence}")
    except AssertionError:
        raise AssertionError((occurrence, tab.evaluate(BUILDER_BOXES_JS, occurrence))) from None
    frame = found["frame"]
    widths = [box["width"] for box in found["builders"]]
    left, right = (BAND_LEFT, BAND_RIGHT) if band else (STRIP_LEFT, STRIP_RIGHT)
    span = sum(widths) + SEGMENT_GAP * (len(widths) - 1)
    if band:
        # the band's segments on the step of their texts, ending by BAND_RIGHT inside the card's right edge
        assert span <= found["size"][0] - left - right + 1, (widths, found["size"])
        assert all(width % SEGMENT_STEP == 0 for width in widths), widths
    else:
        assert abs(span - (found["size"][0] - left - right)) <= 1, (widths, found["size"])
        assert max(widths) - min(widths) <= 1, widths
    zoom = (frame["right"] - frame["left"]) / found["size"][0]
    assert abs(found["builders"][0]["at"]["left"] - (frame["left"] + left * zoom)) <= 0.5, (found["builders"][0], frame)
    for one, other in zip(found["builders"], found["builders"][1:]):
        assert abs(other["at"]["left"] - one["at"]["right"] - SEGMENT_GAP * zoom) <= 0.5, (one, other)
    for box, (_, name, _, _) in zip(found["builders"], expected):
        assert box["id"] == f"{inside}/{name}{LAYER_ID_ENDING}", box
        assert box["height"] == (BAND_HIGH if band else STRIP_HIGH), box
        at = box["at"]
        assert at["top"] >= found["name"]["bottom"] - 0.5, (box, found["name"])
        assert frame["left"] < at["left"] and at["right"] < frame["right"], (box, frame)
        assert at["bottom"] < frame["bottom"], (box, frame)
        # the printed signs and id stand within their segment
        assert box["textRight"] <= at["right"] + 0.5, box
        for label in found["reading"] + found["writing"]:
            clear = (
                at["right"] <= label["left"]
                or label["right"] <= at["left"]
                or at["bottom"] <= label["top"]
                or label["bottom"] <= at["top"]
            )
            assert clear, (box, label)
    return found


def test_task_8_an_open_occurrence_is_drawn_compact_its_builders_coded_by_their_pairs(
    browser, server_on, durables_folder, tmp_path
):
    """Task 8 (AAS, L-D7; spec 0.4 §5.3's four colors), its boxes the
    segments of Tasks 24 and 30 (AAS, L-D16 and L-D25; design pass 7 §3).
    On the durables model's trellis at its opening, periods 0 to 2, every
    open occurrence of the forward graph draws, under its name, inside its
    card and clear of the labels of its reading and its writing ports, one
    segment 3 px high at scale 1 for each forward builder of its stage, the
    segments at equal widths, 2 px apart, from 9 px inside the card's left
    edge to 29 px inside its right edge (design pass 13 §2, rule 5),
    from left to right `arvl,dcsn` and
    `dcsn,cntn` (bequest, whose forward graph holds one builder, the first
    alone), each segment's `data-pair` that pair, no text printed in it and
    its hover the pair in words and the id; the ground of `arvl,dcsn`, the
    builder that joins the arrival perch, is the brand's mint and that of
    `dcsn,cntn`, the builder that joins the continuation perch, its orange
    (design pass 14 §9; S-D14). The occurrence `keeper_cons` is at most
    half its earlier height, and a click on its segment `dcsn_to_cntn` opens
    that builder in place, the occurrence then drawn in full until the
    builder is closed again. In the backward graph `keeper_cons` draws
    `cntn,dcsn` in orange and `dcsn,arvl` in mint, then the policy builder
    in a tint of ice, 34 percent over the lit navy. On a copy of
    the portfolio model whose builder `dcsn_to_cntn` of cons.bl is named
    `solve`, the segment `solve` reads `dcsn,cntn` and takes that pair's
    orange, and a double click on it opens cons.bl at the block's header, line
    17, as a double click on a builder opened it before."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        arriving = f"periods[0]/keeper_cons/arvl_to_dcsn{LAYER_ID_ENDING}"
        wait_until(
            lambda: tab.locator('.bl-graph-bar[data-graph="forward"]').count() == 1
            and arriving in tab.evaluate(DRAWN_PLACES_JS)["nodes"],
            60.0,
            "the forward graph drawn",
        )
        height = tab.evaluate(DRAWN_PLACES_JS)["nodes"][KEEPER_CONS_LAYER]["height"]
        print(f"task 8: {KEEPER_CONS_LAYER} is {height} px high at scale 1")
        opened = sorted(
            namespace
            for namespace in flow_handle(tab, "openLayers")
            if namespace.count("/") == 1 and namespace.startswith("periods[")
        )
        assert len(opened) == 10, opened
        forward = {}
        for namespace in opened:
            expected = DURABLES_FORWARD[namespace.split("/")[1]]
            forward[namespace] = perch_grounds(
                compact_builders(tab, namespace + LAYER_ID_ENDING, expected)
            )
        print(f"task 8: the forward grounds, by perch, {forward}")
        pairs = {grounds for grounds in forward.values() if len(grounds) == 2}
        assert pairs == {("mint", "orange")}, pairs
        assert {grounds[0] for grounds in forward.values()} == {"mint"}
        assert height <= KEEPER_CONS_EARLIER / 2, (height, KEEPER_CONS_EARLIER)

        # a click on a segment opens its builder in place, the occurrence
        # then drawn in full, and the builder's own toggle closes it again
        leaving = f"periods[0]/keeper_cons/dcsn_to_cntn{LAYER_ID_ENDING}"
        node = '.bl-view-host .react-flow__node[data-id="{}"]'
        tab.click(f"{node.format(leaving)} .bf-builder-toggle")
        wait_until(
            lambda: tab.locator(f"{node.format(leaving)} > .bf-layer").count() == 1
            and tab.locator(f"{node.format(KEEPER_CONS_LAYER)} > .bf-compact").count() == 0,
            30.0,
            "dcsn_to_cntn open in place",
        )
        assert "periods[0]/keeper_cons/dcsn_to_cntn" in flow_handle(tab, "openLayers")
        click_toggle(tab, leaving)
        compact_builders(tab, KEEPER_CONS_LAYER, DURABLES_FORWARD["keeper_cons"])

        choose_view(tab, None, "backward")
        found = compact_builders(tab, KEEPER_CONS_LAYER, KEEPER_CONS_BACKWARD)
        grounds = perch_grounds(found)
        assert grounds[:2] == ("orange", "mint"), found["builders"]
        assert abs(grounds[2] - POLICY_SHARE) <= 0.01, found["builders"]
    finally:
        context.close()

    # the portfolio model, its builder `dcsn_to_cntn` of cons.bl named
    # `solve` in the block's header and in the addition that types it
    copy = tmp_path / "portfolio-choice"
    shutil.copytree(PORTFOLIO_CHOICE, copy, ignore=shutil.ignore_patterns("__pycache__"))
    for relative in (CONS, "declaration/stages/cons/methods.bl"):
        path = copy / relative
        text = path.read_text(encoding="utf-8")
        named = text.replace("[id=dcsn_to_cntn,", "[id=solve,").replace(
            "dcsn_to_cntn.handler", "solve.handler"
        )
        assert named != text, relative
        path.write_text(named, encoding="utf-8")
    init_repository(copy)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        lay_out_left_to_right(tab)
        choose_view(tab, None, "forward")
        renamed = ("dcsn,cntn", "solve", "∼≻", "decision to continuation · solve")
        found = compact_builders(tab, f"periods[0]/cons{LAYER_ID_ENDING}", [ARRIVING, renamed])
        assert perch_grounds(found) == ("mint", "orange"), found["builders"]
        double_click_node(tab, f"periods[0]/cons/solve{LAYER_ID_ENDING}", "forward")
        wait_until(
            lambda: open_path_shown(tab) == CONS and tab.evaluate(ACTIVE_LINE_JS) == "17",
            60.0,
            "cons.bl open at the header of solve",
        )
    finally:
        context.close()


# The text an element draws, a select or the input or the text area within a
# text field: the face and the size of its text and its width in characters
# of that face.
TEXT_TYPE_JS = r"""
(entry) => {
  const drawn = getComputedStyle(entry);
  const measure = document.createElement('canvas').getContext('2d');
  measure.font = `${drawn.fontSize} ${drawn.fontFamily}`;
  const width = entry.getBoundingClientRect().width - parseFloat(drawn.paddingLeft)
    - parseFloat(drawn.paddingRight);
  return {
    face: drawn.fontFamily.split(',')[0].replace(/"/g, '').trim(),
    size: drawn.fontSize,
    characters: width / measure.measureText('0').width,
  };
}
"""
# The panel the selector names, a form or a list over the graph, null where
# none is drawn (AAS, L-D8, L-D14): its border's width and its radius; its
# width on the screen and whether it is a wide form, `.bl-form-wide`; the
# number of lines the texts of its heading and of the note under its head
# stand on, null where it has no heading h2 or no note; the distance from
# the right edge of its last foot button to its content's right edge, null
# where it has no foot; each field, a field of VSCode Elements (unit M,
# Task 6), as its label, whether
# that label stands above the field's box on the box's left edge, the box's
# left beyond the panel's content edge, whether it stands in a list of the
# form or after another field on its row, the face and the size of the
# text of a select, its width in characters of that face (TEXT_TYPE_JS),
# null for a text field or a text area, whose text the element draws in its
# own tree, which Task 9's test reads through Playwright's selectors,
# whether it holds a path or a message and whether it is a select; and each
# icon as its name and its size on the screen.
PANEL_JS = r"""
(selector) => {
  const panel = document.querySelector(selector);
  if (!panel) return null;
  const style = getComputedStyle(panel), box = panel.getBoundingClientRect();
  const inner = box.left + parseFloat(style.borderLeftWidth) + parseFloat(style.paddingLeft);
  const innerRight =
    box.right - parseFloat(style.borderRightWidth) - parseFloat(style.paddingRight);
  // the number of lines the texts of an element stand on: its texts' boxes
  // in the order of their tops, a box that begins below the lowest bottom of
  // the line before beginning a new line, so that texts of two sizes on one
  // baseline count as one line
  const lines = (element) => {
    const rects = [];
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const range = document.createRange();
      range.selectNodeContents(node);
      for (const rect of range.getClientRects()) {
        if (rect.width > 0) rects.push(rect);
      }
    }
    rects.sort((a, b) => a.top - b.top);
    let count = 0, bottom = -Infinity;
    for (const rect of rects) {
      if (rect.top >= bottom - 0.5) count += 1;
      bottom = rect.top >= bottom - 0.5 ? rect.bottom : Math.max(bottom, rect.bottom);
    }
    return count;
  };
  const heading = panel.querySelector('h2');
  const note = panel.querySelector('.bl-form-top > .bl-form-note');
  const foot = panel.querySelector('.bl-form-buttons');
  const textType = (TEXT_TYPE_JS);
  const fields = Array.from(panel.querySelectorAll('.bl-field'), (wrapper) => {
    const control = wrapper.querySelector(
      'vscode-textfield, vscode-single-select, vscode-textarea');
    const field = control.getBoundingClientRect();
    const label = wrapper.querySelector('.bl-field-label');
    const at = label.getBoundingClientRect();
    const select = control.tagName === 'VSCODE-SINGLE-SELECT';
    return {
      label: label.textContent.trim(),
      above: at.height > 0 && at.bottom <= field.top && Math.abs(at.left - field.left) < 0.5,
      edge: Math.round((field.left - inner) * 10) / 10,
      inset: wrapper.closest('.bl-form-list') !== null
        || (wrapper.parentElement.matches('.bl-form-row')
          && wrapper.previousElementSibling !== null),
      ...(select ? textType(control) : {face: null, size: null, characters: null}),
      path: wrapper.matches(
        '.bl-folder-path, .bl-create-parent, .bl-create-destination, .bl-commit-message'),
      select,
    };
  });
  // the icons drawn, the Codicons of the forms and of the lists over the
  // graph (design pass 8 §3; unit M, Tasks 6 and 7), each as its name and
  // its box
  const icons = [
    ...Array.from(panel.querySelectorAll('.codicon'), (icon) => [
      Array.from(icon.classList).find((name) => name.startsWith('codicon-'))
        .slice('codicon-'.length), icon]),
  ].map(([name, icon]) => {
    const at = icon.getBoundingClientRect();
    return [name, at.width, at.height];
  });
  return {
    border: style.borderTopWidth,
    radius: style.borderTopLeftRadius,
    width: box.width,
    wide: panel.matches('.bl-form-wide'),
    heading: heading ? lines(heading) : null,
    note: note ? lines(note) : null,
    foot: foot
      ? Math.round((innerRight - foot.lastElementChild.getBoundingClientRect().right) * 10) / 10
      : null,
    fields,
    icons,
  };
}
""".replace("(TEXT_TYPE_JS)", TEXT_TYPE_JS.strip())
# The entry of the form's chooser that the field names, as its path and its
# computed shadow, which draws the selection's bar, null where no entry is
# marked
CURRENT_ENTRY_JS = """
() => {
  const entry = document.querySelector('.bl-form .bl-folder-entry.bl-current');
  if (!entry) return null;
  return [entry.dataset.path, getComputedStyle(entry).boxShadow];
}
"""
# The icons of the six kinds of thing a form or a list over the graph names
# (AAS, L-D8): a folder, a stage file, a template, a stage of the library, a
# period and a close, by their Codicons in the forms and the lists over the
# graph (design pass 8 §3; unit M, Tasks 6 and 7), the stage file and the
# period being the forms' alone
SIX_ICONS = {"folder", "file", "layers", "library", "split-horizontal", "close"}


def test_task_9_the_forms_and_the_lists_over_the_graph_are_one_panel_with_16_px_icons(
    browser, server_on, scratch_durables, tmp_path, monkeypatch
):
    """Task 9 (AAS, L-D8; spec 0.4 §5.8's contrast). On a copy of the
    durables model, `periods 0–2`, its forward trellis graph shown, with a
    library of stages that holds `port`: each of the seven forms, `new
    trellis`, `new variant`, `new stage`, `add stage`, `add stage` from a
    folder, `add period` and `commit`, opened from its control, and the
    stage list, opened by `stages` and by a period's `+ stage`, and the
    cable's list, opened by the move of a join wire's reading end onto
    `bequest`'s arrival port (design pass 10 §7), each measure a
    1-px border, a 4-px radius and a width of at most 440 px, 560 px for a
    wide form (Task 23; L-D14). Each form's heading and the note under its
    head stand on one line, its last button ends on its right edge, and
    each field's label, a chosen template's key field's among them, stands
    above its box on the box's left edge, every box but one in a list of
    the form or after another on its row on the form's one left edge, its
    text in Label, Archivo at 13 px (design pass 8 §5.3; unit M, Task 6),
    and no wider than 32 characters but for a path, the message or a
    select, which the library sizes to hold its options and its chevron. In
    the form from a folder, the entry `port.bl` that the field names
    carries the selection's bar in ultramarine-light (Task 23). Every icon
    drawn measures 16 × 16 px, and the six kinds, folder, stage file,
    template, library stage, period and close, are each drawn, by their
    Codicons in the forms and the lists over the graph (design pass 8 §3;
    unit M, Tasks 6 and 7). With each panel open, no text
    under the window
    falls below its contrast bound (`contrast_faults`, the rows of
    `screenshots.py --frames`)."""
    library = tmp_path / "library"
    shutil.copytree(PORT_FOLDER, library / "port")
    monkeypatch.setenv(creation.LIBRARY_VARIABLE, str(library))
    copy = scratch_durables
    writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
    add_stage = (
        f'.bl-view-host .react-flow__node[data-id="periods[0]{LAYER_ID_ENDING}"]'
        " > .bf-layer > .bf-add-stage"
    )
    port_file = str(PORT_FOLDER / "port.bl")
    drawn = []

    def panel(selector: str, what: str) -> dict:
        # the panel's measures, its icons kept, and the window's contrast
        found = tab.evaluate(PANEL_JS, selector)
        # the text of each text field and text area, the input or the text
        # area the element draws in its own tree, which Playwright's
        # selectors reach
        wrappers = tab.locator(f"{selector} .bl-field")
        for number, field in enumerate(found["fields"]):
            if not field["select"]:
                entry = wrappers.nth(number).locator("input, textarea")
                field.update(entry.evaluate(TEXT_TYPE_JS))
        assert (found["border"], found["radius"]) == ("1px", "4px"), (what, found)
        assert found["width"] <= (560 if found["wide"] else 440), (what, found["width"])
        drawn.extend(found["icons"])
        assert contrast_faults(tab, CONTRAST_EXCEPTIONS) == [], what
        return found

    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.locator(add_stage).count() == 1, 60.0, "+ stage of periods[0]")
        for form in PAGE_FORMS:
            selector = open_page_form(tab, form)
            if form in ("new trellis", "add stage"):
                # the first template chosen, which draws its key field
                tab.locator(f"{selector} .bl-template-button").first.click()
                tab.wait_for_selector(f"{selector} .bl-create-key")
            elif form == "from a folder":
                field = f"{selector} .bl-folder-path input"
                tab.fill(field, port_file)
                tab.press(field, "Enter")
                tab.wait_for_selector(f'{selector} .bl-template[data-template="{port_file}"]')
                wait_until(lambda: tab.evaluate(CURRENT_ENTRY_JS), 10.0, "the current entry")
                bar = f"{property_color(tab, '--bl-ultramarine-light')} 3px 0px 0px 0px inset"
                assert tab.evaluate(CURRENT_ENTRY_JS) == [port_file, bar]
            found = panel(selector, form)
            assert (found["heading"], found["note"], found["foot"]) == (1, 1, 0), (form, found)
            assert found["fields"], form
            for field in found["fields"]:
                assert field["above"] and (field["inset"] or field["edge"] == 0), (form, field)
                assert (field["face"], field["size"]) == ("Archivo", "13px"), (form, field)
                bound = field["path"] or field["select"] or field["characters"] <= 32.01
                assert bound, (form, field)
            tab.click(f"{selector} .bl-form-cancel")
            tab.wait_for_selector(".bl-form", state="detached")

        # the stage list opened by `stages` and by `+ stage` of periods[0]
        stage_list = ".bl-view-host .bf-stage-list"
        for opener in (".bl-stages-button", add_stage):
            tab.click(opener)
            tab.wait_for_selector(f"{stage_list} .bf-stage-item", timeout=10_000)
            panel(stage_list, opener)
            tab.click(f"{stage_list} .bf-list-close")
            tab.wait_for_selector(stage_list, state="detached")

        # the cable's list of the move of a join wire's reading end, closed by
        # its ×: the end is dropped on `bequest`'s arrival port, since design
        # pass 10 §6 took the per-field port `a_bq` off the cards (§7)
        hold_events(tab, "moved")
        click_join(tab, writer, reader)
        arrival = cable_port(tab, "periods[0]/bequest", "reading")
        move_join_end(tab, writer, reader, "target", arrival)
        pair_list = ".bl-view-host .bf-pair-list"
        tab.wait_for_selector(pair_list, timeout=10_000)
        panel(pair_list, "pairing list")
        tab.click(f"{pair_list} .bf-list-close")
        tab.wait_for_selector(pair_list, state="detached")
        assert release_events(tab, "moved") == []
    finally:
        context.close()
    assert SIX_ICONS <= {name for name, _, _ in drawn}
    assert {(width, height) for _, width, height in drawn} == {(16, 16)}


# The template of the stage `cons` that lesson 05's trellis file of the
# cons-port application binds, its stage file in the portfolio model's folder
CONS_ID = "cons-port/declaration/trellis.port-cons.yml#cons"
# The stage list as the page draws it, null where none is open (Task 10):
# its height, the height of the graph region that holds it, its computed
# maximum height and whether it scrolls; and its heading lines and items in
# their order, a heading line as its text, its height and its face, an item
# as its kind, its id, its height, whether each of its texts stands on one
# line within the item's box, its key and the key's face, the folder name it
# prints and that name's face, the word `listed` where it prints one, and
# its hover. A face is the first family, the weight, the size and the color,
# the weight telling Code name from Code (design pass 13 §3).
STAGE_LIST_ROWS_JS = r"""
() => {
  const list = document.querySelector('.bl-view-host .bf-stage-list');
  if (!list) return null;
  const face = (element) => {
    if (!element) return null;
    const style = getComputedStyle(element);
    return [style.fontFamily.split(',')[0].replace(/"/g, ''), style.fontWeight, style.fontSize,
            style.color];
  };
  const text = (element) => (element ? element.textContent : null);
  const oneLine = (row) => {
    const box = row.getBoundingClientRect();
    const walker = document.createTreeWalker(row, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const range = document.createRange();
      range.selectNodeContents(node);
      const rects = Array.from(range.getClientRects()).filter((rect) => rect.width > 0);
      if (rects.length !== 1) return false;
      if (rects[0].top < box.top - 0.5 || rects[0].bottom > box.bottom + 0.5) return false;
    }
    return true;
  };
  const rows = Array.from(list.querySelectorAll('.bf-stage-section, .bf-stage-item'), (row) => {
    const height = row.getBoundingClientRect().height;
    if (row.classList.contains('bf-stage-section')) {
      return {section: row.textContent, height, face: face(row)};
    }
    const key = row.querySelector('.bf-stage-key'), model = row.querySelector('.bf-stage-model');
    return {
      kind: row.dataset.kind, item: row.dataset.item, height, oneLine: oneLine(row),
      key: text(key), keyFace: face(key), model: text(model), modelFace: face(model),
      listed: text(row.querySelector('.bf-stage-listed')), hover: row.getAttribute('title'),
    };
  });
  return {
    height: list.getBoundingClientRect().height,
    region: list.closest('.bf-region').getBoundingClientRect().height,
    maxHeight: getComputedStyle(list).maxHeight,
    scrolls: list.scrollHeight > list.clientHeight,
    rows,
  };
}
"""


def test_task_10_each_item_of_the_stage_list_is_one_line_its_title_and_parameters_in_its_hover(
    browser, server_on, scratch_durables, tmp_path, monkeypatch
):
    """Task 10 (AAS, L-D9; design pass 3 §2's row; spec 0.4 §3.5). With a
    library of stages that holds a copy of the corpus's `port`, on a copy of
    the durables model, `periods 0–2`, its forward trellis graph shown: the
    list the button `stages` opens prints the heading lines `This folder's
    stages`, `Templates` and `Library` in that order, in sentence case, each
    20 px high in Small, Archivo 500 at 11 px in ink-3 (design pass 13 §3;
    C14), the model's stages, the corpus's templates and the stage of the
    library under them, and last `From a folder…`. Each item is one line
    26 px high (unit N, Task 5; design pass 10 §7): the icon of its kind and
    its key in Code name, IBM Plex Mono 500 at 12.5 px in ink-1, then the
    name of its model's folder in Code small, IBM Plex Mono 400 at 11 px in
    ink-3, `durables` for the model's stages, `portfolio-choice` for the
    template `cons`, `library` for the stage of the library; its hover is
    the model's title and the parameters, `<title> · <parameters>`, as
    `stage_items` gives them, nothing lost; `From a folder…` prints its
    words alone, in Label, Archivo 400 at 13 px in ink-2, the words of a
    control at rest (§5), with no hover. The list measures at most 60 percent
    of the graph region's height and scrolls within it. In the list of
    periods[1]'s `+ stage`, `cons`, reached by ArrowDown past the heading
    lines, is sent by Enter to periods[1]; and `cons` dragged onto periods[1]
    writes as unit J's test of a template's drop has it: its stage file and
    companions as new files with the texts the Workbench's drop answers, the
    period file and the recipe edited in their buffers, which the tree marks
    unsaved and the disk does not hold, the status line's note, and `cons`
    drawn in periods[1] and periods[2]."""
    library = tmp_path / "library"
    shutil.copytree(PORT_FOLDER, library / "port")
    monkeypatch.setenv(creation.LIBRARY_VARIABLE, str(library))
    origin = str(library / "port")
    copy = scratch_durables
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(
        folder, recipe.Source("recipe", RECIPE_FILE), trellis.parse_restriction("periods 0–2")
    ).shown
    period = f"periods[1]{LAYER_ID_ENDING}"
    keys = creation.recipe_keys(copy)
    templates = creation.stage_templates()
    assert CONS_ID in [template.id for template in templates]
    lines = (
        [["section", "This folder's stages"]]
        + [["stage", key] for key in keys]
        + [["section", "Templates"]]
        + [["template", template.id] for template in templates]
        + [["section", "Library"], ["library", origin], ["folder", "folder"]]
    )
    items = {item["id"]: item for item in trellis.stage_items(folder, shown, {})["items"]}
    assert {items[key]["model_folder"] for key in keys} == {"durables"}
    # the template `cons` reads the demonstration's consumption stage file
    # since decision SD-39, so its model folder is the demonstration's (SE-36)
    assert (items[CONS_ID]["model_folder"], items[origin]["model_folder"]) == (
        "cons-port",
        "library",
    )
    expected = trellis.drop_edits(
        shown, dropped_event(shown, folder, CONS_ID, "template", period), {}
    )
    assert expected.edits and expected.new_files
    on_disk = {path: Path(path).read_text(encoding="utf-8") for path in expected.edits}
    edited_files = sorted(str(Path(path).relative_to(folder.root)) for path in expected.edits)
    add_stage = f'.bl-view-host .react-flow__node[data-id="{period}"] > .bf-layer > .bf-add-stage'
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.locator(add_stage).count() == 1, 60.0, "+ stage of periods[1]")
        ink_1, ink_2, ink_3 = (
            property_color(tab, name) for name in ("--bl-ink-1", "--bl-ink-2", "--bl-ink-3")
        )

        # the list the button `stages` opens, one line per item
        open_stage_list(tab)
        drawn = tab.evaluate(STAGE_LIST_ROWS_JS)
        rows = drawn["rows"]
        assert [
            ["section", row["section"]] if "section" in row else [row["kind"], row["item"]]
            for row in rows
        ] == lines
        # Small, Code name, Code small and Label (design pass 13 §3; C14)
        head_face = ["Archivo", "500", "11px", ink_3]
        key_face = ["IBM Plex Mono", "500", "12.5px", ink_1]
        model_face = ["IBM Plex Mono", "400", "11px", ink_3]
        folder_face = ["Archivo", "400", "13px", ink_2]
        for row in rows:
            if "section" in row:
                assert (row["height"], row["face"]) == (20, head_face), row
                continue
            item = items[row["item"]]
            hover = " · ".join(filter(None, (item["title"], ", ".join(item["calibration"]))))
            assert (row["height"], row["oneLine"]) == (26, True), row
            assert (row["key"], row["listed"], row["hover"]) == (item["key"], None, hover or None)
            if row["kind"] == "folder":
                assert (row["model"], row["modelFace"]) == (None, None), row
                assert row["keyFace"] == folder_face, row
            else:
                assert row["keyFace"] == key_face, row
                assert (row["model"], row["modelFace"]) == (item["model_folder"], model_face), row
        print(f"task 10: the list {drawn['height']} px in a region of {drawn['region']} px")
        # the region's script writes the list's greatest height in px, at
        # most 60 percent of the region's, beside the button that opened it
        # (unit N, Task 5; design pass 10 §7)
        limit = float(drawn["maxHeight"].removesuffix("px"))
        assert limit <= 0.6 * drawn["region"] + 0.5 and drawn["height"] <= limit + 0.5
        assert drawn["scrolls"]
        tab.keyboard.press("Escape")
        wait_until(lambda: tab.evaluate(STAGE_LIST_ROWS_JS) is None, 5.0, "the list closed")

        # Enter on `cons` in the list of periods[1] sends it to that period
        tab.click(".bl-zoom-button[data-zoom='fit']")
        hold_events(tab, "dropped")
        tab.click(add_stage)
        wait_until(lambda: keyboard_place(tab)["item"] is not None, 10.0, "the focus on an item")
        for _ in range(len(lines)):
            if keyboard_place(tab)["item"] == CONS_ID:
                break
            tab.keyboard.press("ArrowDown")
        assert keyboard_place(tab)["item"] == CONS_ID
        tab.keyboard.press("Enter")
        wait_until(lambda: held_events(tab, "dropped"), 10.0, "the event dropped")
        reading = tab.evaluate(REGION_READING_JS)
        assert held_events(tab, "dropped") == [
            {"item": CONS_ID, "kind": "template", "target": period, "reading": reading}
        ]
        # the event held is set aside, and the holding ended
        hold_events(tab, "dropped")
        assert release_events(tab, "dropped") == []

        # `cons` dragged onto periods[1]
        drop_item(tab, CONS_ID, period)
        wait_until(lambda: gesture_note(tab) == expected.note, 30.0, "the note of the drop")
        for relative, text in expected.new_files:
            assert (copy / relative).read_text(encoding="utf-8") == text
        wait_until(lambda: unsaved_in_tree(tab) == edited_files, 10.0, "the edited files unsaved")
        wait_until(
            lambda: {"periods[1]/cons", "periods[2]/cons"}
            <= occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "forward"),
            60.0,
            "cons drawn in periods[1] and periods[2]",
        )
        assert {path: Path(path).read_text(encoding="utf-8") for path in on_disk} == on_disk
    finally:
        context.close()


# The Recipe tab under the element `root`, the panel under the editor on
# the recipe (Task 11, as unit M's Task 10 draws the recipe; design pass 9
# §3), null where it is not drawn: its width; each element of its table
# wider inside than its box, the controls' own trees left out; and each row
# as its stage, the hover of its periods field, and for each binding kind
# its lines, each the value of an entry's select or `—`, the line of a
# range list's first entry prefixed by the list's periods as `range 0–1`
# (unit N, Task 2; design pass 10 §4).
RECIPE_LINES_JS = r"""
(root) => {
  const region = document.querySelector(root);
  if (!region) return null;
  const chosen = (select) => {
    const option = select.querySelector('vscode-option[selected]');
    return option ? option.textContent.trim() : null;
  };
  const part = (element) => {
    const text = element.textContent.trim();
    const select = element.querySelector('vscode-single-select');
    const shown = element.querySelector('.bl-recipe-text, .bl-recipe-none');
    const value = select ? chosen(select) : shown ? shown.textContent.trim() : text;
    const range = element.querySelector('.bl-recipe-range');
    return range ? `range ${range.textContent.trim()} ${value}` : value;
  };
  const kinds = '.bl-recipe-cell:not([data-kind="stage"]):not([data-kind="periods"])';
  return {
    width: region.getBoundingClientRect().width,
    wider: Array.from(region.querySelectorAll('.bl-recipe-table *'))
      .filter((element) => !element.closest('vscode-single-select, vscode-textfield')
        && element.scrollWidth > element.clientWidth + 0.5)
      .map((element) => {
        const cell = element.closest('[data-kind]');
        return [String(element.className), element.textContent, element.getAttribute('title'),
                cell ? cell.dataset.kind : null];
      }),
    rows: Array.from(region.querySelectorAll('.bl-recipe-row'), (row) => ({
      stage: row.dataset.stage,
      periods: (row.querySelector('.bl-recipe-periods')
        || row.querySelector('[data-kind="periods"] .bl-recipe-text')).getAttribute('title'),
      kinds: Object.fromEntries(Array.from(row.querySelectorAll(kinds),
        (cell) => [cell.dataset.kind, Array.from(cell.children, part)])),
    })),
  };
}
"""
# the panel under the editor on the recipe
RECIPE_TAB = '.bl-classification[data-panel="recipe"]'
# The durables recipe's stages, each with the hover of its periods field, the
# periods the trellis lists it in, and the lines of its bindings (AAS, L-D10)
DURABLES_RECIPE_LINES = {
    **{
        key: (
            "Listed in periods 0–50",
            {
                "calibration": ["durables", "$fill"],
                "settings": ["durables", "$fill"],
                "methods": ["methods.bl"],
            },
        )
        for key in ("tenure", "keeper_cons", "adjuster_cons")
    },
    "bequest": (
        "Listed in periods 0",
        {"calibration": ["durables", "$fill"], "settings": ["—"], "methods": ["methods.bl"]},
    ),
}
# keeper_cons's calibration in the variant spec.two-stages.yml, written with
# two range lists beside `all` for Task 11's test, and the lines it prints
KEEPER_CALIBRATION = "calibration: {all: [calibration/durables, $fill]}, settings"
KEEPER_RANGES = (
    'calibration: {all: [calibration/durables, $fill], "0-1": [calibration/durables], '
    '"2-50": [calibration/durables]}, settings'
)
KEEPER_LINES = ["durables", "$fill", "range 0–1 durables", "range 2–50 durables"]


def recipe_shown(found: dict) -> dict:
    """The rows RECIPE_LINES_JS reads, by stage: the hover of its periods
    field, or of its periods text at rest, and its bindings' lines, each
    its select's value, or its text at rest (design pass 11 §2)."""
    return {row["stage"]: (row["periods"], row["kinds"]) for row in found["rows"]}


def cut(found: dict) -> list:
    """The elements RECIPE_LINES_JS reads as wider inside than their box but
    the stage file's name of a row at rest, which design pass 11 §2 cuts
    with an ellipsis where the key leaves it too little room, and whose
    hover holds it whole."""
    return [
        element
        for element in found["wider"]
        if element[:2] != ["bl-recipe-text bl-code-small", element[2]] or element[3] != "stage"
    ]


def opened_in_turn(tab) -> tuple[dict, list]:
    """The rows of the Recipe tab as RECIPE_LINES_JS reads them, each row
    opened in turn and read while the others stand at rest
    (`with_each_recipe_row_open`), by stage; and the elements of each
    reading that are wider inside than their box (`cut`)."""
    found = with_each_recipe_row_open(tab, lambda tab: tab.evaluate(RECIPE_LINES_JS, RECIPE_TAB))
    rows = {key: recipe_shown(reading)[key] for key, reading in found.items()}
    return rows, [element for reading in found.values() for element in cut(reading)]


def test_task_11_the_recipe_region_says_which_periods_each_binding_holds_for(
    browser, server_on, scratch_durables
):
    """Task 11 (AAS, L-D10 and L-D11; spec 0.4 §3.2 extended to the
    ranges), on the Recipe tab of unit M's Task 10 (AAS, M-D17; design pass
    9 §§3 and 5). On a copy of the durables model whose variant
    `spec.two-stages.yml` gives keeper_cons's calibration two range lists,
    `0-1` and `2-50`, beside `all`, its recipe `spec.yml` shown at 1600 ×
    1000: each row's periods field names in its hover the periods the
    trellis lists the stage in, `0` for `bequest` and `0–50` for `tenure`,
    and each binding its entries in the file's order, `—` where the recipe
    writes none, each row read at rest and opened in turn, the others then
    at rest (design pass 11 §2); nothing in the table is wider inside than
    its box but a stage file's name at rest, cut with an ellipsis and whole
    in its hover. The icon `Open wide` in the panel's strip shows the panel
    in its wide panel, 760 px wide, with the same rows, where nothing is
    cut, the strip naming `spec.yml`; a second click returns it to its
    column, and so does Escape (unit N, Task 2). On the variant, opened
    from the tree, keeper_cons's calibration prints each range list's
    periods at the left of its first entry, in the file's order, at rest
    and with its row open. The period
    select and the mark of the head's period left with the recipe region
    (design pass 9 §5)."""
    variant = scratch_durables / TWO_STAGES
    text = variant.read_text(encoding="utf-8")
    assert text.count(KEEPER_CALIBRATION) == 2
    # keeper_cons's row is the first that writes the calibration
    variant.write_text(text.replace(KEEPER_CALIBRATION, KEEPER_RANGES, 1), encoding="utf-8")
    context, tab = new_tab(browser)
    try:
        url = server_on(scratch_durables)
        open_trellis(tab, url, RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        tab.wait_for_selector(f"{RECIPE_TAB} .bl-recipe-row", timeout=60_000)

        # the rows: each stage's periods, each binding's entries, at rest and
        # each row opened in turn (design pass 11 §2)
        column = tab.evaluate(RECIPE_LINES_JS, RECIPE_TAB)
        print(f"task 11: the tab at {column['width']} px, wider {column['wider']}")
        assert cut(column) == []
        assert recipe_shown(column) == DURABLES_RECIPE_LINES
        rows, wider = opened_in_turn(tab)
        assert (rows, wider) == (DURABLES_RECIPE_LINES, [])

        # the wide panel: the same rows, 760 px wide, nothing cut
        opener = tab.locator(f"{RECIPE_TAB} .bl-region-wide")
        assert opener.evaluate("(button) => button.label") == "Open wide"
        opener.click()
        wait_until(
            lambda: abs(tab.evaluate(RECIPE_LINES_JS, RECIPE_TAB)["width"] - 760) <= 0.5,
            10.0,
            "the wide panel",
        )
        panel = tab.evaluate(RECIPE_LINES_JS, RECIPE_TAB)
        assert recipe_shown(panel) == DURABLES_RECIPE_LINES
        assert panel["wider"] == []
        rows, wider = opened_in_turn(tab)
        assert (rows, wider) == (DURABLES_RECIPE_LINES, [])
        assert tab.locator(f"{RECIPE_TAB} .bl-inspector-file").text_content() == "spec.yml"
        opener.click()
        wait_until(
            lambda: tab.locator(f"{RECIPE_TAB}.bl-wide").count() == 0,
            10.0,
            "a second click closing it",
        )
        opener.click()
        tab.wait_for_selector(f"{RECIPE_TAB}.bl-wide", timeout=10_000)
        tab.keyboard.press("Escape")
        wait_until(
            lambda: tab.locator(f"{RECIPE_TAB}.bl-wide").count() == 0, 10.0, "Escape closing it"
        )

        # the variant: each range list's periods at the left of its first
        # entry
        open_trellis(tab, url, TWO_STAGES)

        def keeper_lines():
            found = tab.evaluate(RECIPE_LINES_JS, RECIPE_TAB) or {"rows": [], "wider": []}
            rows = [row for row in found["rows"] if row["stage"] == "keeper_cons"]
            return (rows[0]["kinds"]["calibration"] if rows else None), cut(found)

        wait_until(lambda: keeper_lines()[0] == KEEPER_LINES, 60.0, "keeper_cons's lists")
        lines, wider = keeper_lines()
        print(f"task 11: keeper_cons's calibration on the variant: {lines}")
        assert wider == []
        open_recipe_row(tab, "keeper_cons")
        assert keeper_lines() == (KEEPER_LINES, [])
    finally:
        context.close()


# The main bar's toggles (design pass 10 §3; unit N, Task 1), which took
# the rail's buttons of Task 12 (AAS, L-D12): each toggle's region, its
# hover and its accessible name, the panel's name with its capital (Task 29;
# AAS, L-D28), and its icon's Codicon and glyph, None where it has none
# (unit M, Task 11; AAS, M-D18; N-D10), in the bar's order.
TOGGLES = [
    ["folder", "Files", "Files", ["files", None]],
    ["inspector", "Inspector", "Inspector", ["layout-panel", None]],
    ["details", "Details", "Details", [None, "⟦·⟧"]],
    ["matsya", "Matsya", "Matsya", ["comment", "Υ"]],
]
# The name each panel's head prints, by its data-panel: the name of its
# fold's toggle (Task 29; AAS, L-D28; N-D4).
HEAD_NAMES = {"recipe": "Inspector", "types": "Inspector", "details": "Details"}
# The fold each panel's head closes, by its data-panel (N-D4).
HEAD_FOLDS = {"recipe": "inspector", "types": "inspector", "details": "details"}
# The main bar's toggles and each panel's head as the page draws them: the
# bar's box, whether it is the window's first `nav`, and for each toggle
# its region, hover, accessible name, its icon's Codicon and glyph, its box,
# the icon's box, aria-expanded, its ground and the ground of its line under
# it while it is pressed; for each head its panel, box, ground, lower
# border, the number of its icons outside its buttons, its name, and the
# accessible name of its close button with the region's fold it names
# (design pass 8 §5.5; unit M, Tasks 6 and 7).
BAR_AND_HEADS_JS = r"""
() => {
  const box = (element) => {
    const rect = element.getBoundingClientRect();
    return {left: rect.left, top: rect.top, width: rect.width, height: rect.height};
  };
  const bar = document.querySelector('.bl-main-bar');
  const window_ = document.querySelector('.bl-window');
  return {
    bar: box(bar),
    first: window_.querySelector(':scope > nav') === bar,
    toggles: Array.from(bar.querySelectorAll('.bl-toggle'), (button) => {
      const icon = button.querySelector('.bl-toggle-icon');
      const codicon = icon.querySelector(':scope > .codicon');
      const glyph = icon.querySelector(':scope > .bl-toggle-glyph');
      return {
        fold: button.dataset.fold, title: button.title, label: button.getAttribute('aria-label'),
        icon: [codicon ? Array.from(codicon.classList).find((name) => name.startsWith('codicon-'))
                         .slice('codicon-'.length) : null,
               glyph ? glyph.dataset.glyph : null],
        box: box(button), iconBox: box(icon),
        expanded: button.getAttribute('aria-expanded'),
        ground: getComputedStyle(button).backgroundColor,
        line: getComputedStyle(button, '::after').backgroundColor,
      };
    }),
    heads: Array.from(document.querySelectorAll('.bl-window .bl-region-head'), (head) => {
      const style = getComputedStyle(head);
      const close = head.querySelector('.bl-region-close');
      return {
        panel: head.dataset.panel, box: box(head), ground: style.backgroundColor,
        border: [style.borderBottomWidth, style.borderBottomStyle],
        icons: head.querySelectorAll(':scope > svg, :scope > .codicon').length,
        name: head.querySelector('.bl-region-name').textContent,
        close: [close.label, close.dataset.fold || null],
      };
    }),
  };
}
"""
# The drawn buttons of the page outside the main bar whose text, accessible
# name or hover is `files`, and the drawn buttons of the graph's bar that
# print Υ, each as the start of its markup (AAS, L-D12: these controls of
# the bars are replaced by the main bar's toggles, design pass 10 §3). The
# tab row's `Types` is not among them, since it hides the types in the text
# and folds no panel (spec 0.4 §§5.1 and 5.4).
OLD_CONTROLS_JS = r"""
() => Array.from(document.querySelectorAll('button, [role="button"]'))
  .filter((button) => button.getClientRects().length > 0 && !button.closest('.bl-main-bar'))
  .filter((button) => {
    const names = [button.textContent.trim(), button.getAttribute('aria-label') || '',
                   button.title || ''];
    return names.includes('files')
      || (button.closest('.bl-graph-bar') && button.textContent.includes('Υ'));
  })
  .map((button) => button.outerHTML.slice(0, 120))
"""
# Whether the element that holds the keyboard's focus stands in the window.
IN_WINDOW_JS = "() => document.activeElement.closest('.bl-window') !== null"
# The ground of a toggle, which takes no wash while its region is open
# (design pass 10 §3; design pass 13 §5, E1), and the content of its
# ::after, the accent line of its on mark, `none` while its region is
# folded.
REGION_FILL_JS = "(button) => getComputedStyle(button).backgroundColor"
REGION_LINE_JS = "(button) => getComputedStyle(button, '::after').content"
# The region each toggle shows and hides, by its fold, with a stage file
# open (design pass 10 §3).
FOLDED_REGION = {
    "folder": ".bl-tree",
    "inspector": ".bl-classification",
    "details": ".bl-panel",
    "matsya": ".bl-matsya",
}
# The least widths of the columns of spec 0.4 §5.1 and R-D14, by column:
# the open folder's, or the folded folder's rail, the text's, the graph's
# and Matsya's.
LEAST_WIDTHS = (170, 300, 300, 300)
FOLDED_FOLDER = 48


def test_task_12_the_two_panels_take_one_head_and_the_main_bar_s_toggles_open_and_close_them(
    page, server, model_folder
):
    """Task 12 (AAS, L-D12; design pass 3 §§2 and 3), its rail replaced by
    the main bar's toggles of unit N's Task 1 (design pass 10 §§2 and 3).
    On the portfolio model at 1600 × 1000, the main bar stands at the
    window's top, 36 px high, the window's first `nav`, so that Tab from the
    page's start reaches the brand's mark at its left, then `Back`, before
    any other element of the window; its right group holds four toggles of
    26 × 26 px, `Files`, `Inspector`, `Details` and `Matsya` (N-D4), each
    named and hovered by its panel's name, its icon, of 16 × 16 px, its
    Codicon and glyph (N-D10), and each marked open by aria-expanded and
    the on mark of design pass 13 §5 (E1, Q-D9), no wash and a 2 px line in
    the accent as its foot. Each toggle, pressed by the keyboard (Enter),
    folds its region, which is then not drawn, its line gone, and pressed
    again opens it, its mark back. The head of Details measures 28 px on its
    region's own ground over a 1 px hairline, as design pass 8 §5.5 draws the
    one head (unit M, Tasks 6 and 7), holding no icon of its panel, the name of
    its fold's toggle, `Details`, and last the icon button `close`, named
    `Close details`, a fold button of the fold `details`; the BellmanType panel
    has no head, its strip in its place (unit N, Task 2; design pass 10
    §4), and the toggle `Inspector` folds it and opens it again. Details
    folded stays folded while another file, port.bl, is opened, and the
    record window.vue keeps holds the fold of each region under the new
    keys. No button outside the main bar is named `files`, and the graph's
    bar holds no Υ. The toggle `Types` stands in the tabs' row before
    `Save`, pressed while the types are shown; its press hides the types in
    the text (spec 0.4 §5.4), the toggle then unpressed, and leaves the
    BellmanType panel open, its toggle still marked. The icon `open` of
    Details stands it in its 760 px wide panel, which Escape closes, and of
    the BellmanType panel, whose second click then returns it to its
    column. At 1220 and at 1140 px, 60 px below the widths of before the
    window's right margin left (design pass 13 §4; Q-D6), the columns keep
    the widths of spec 0.4 §5.1, none under its least width, the folder's
    column at the window's left edge and the toggles on one row; at 1220
    the folder opened by `Files` is 170 px, the text and
    the graph at least 300 px. Every text meets its contrast bound."""
    page.goto(server)
    page.wait_for_selector(".bl-main-bar .bl-fold", timeout=60_000)
    page.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{RECIPE_FILE}"]', timeout=60_000)
    # `Back`, an icon button of VSCode Elements, takes the focus once the
    # library has defined its element
    page.wait_for_function("() => customElements.get('vscode-toolbar-button') !== undefined")
    # Tab from the page's start, past the links of Solara's own frame, which
    # stands outside the window, reaches the main bar's mark first
    for _ in range(5):
        page.keyboard.press("Tab")
        if page.evaluate(IN_WINDOW_JS):
            break
    assert page.evaluate(
        "() => document.activeElement === document.querySelector('.bl-main-bar .bl-mark')"
    )
    page.keyboard.press("Tab")
    assert page.evaluate("() => document.activeElement === document.querySelector('.bl-back')")
    open_cons(page, server)
    ground = property_color(page, "--bl-ground")
    wash = property_color(page, "--bl-selected")
    accent = property_color(page, "--bl-accent")

    # the main bar, its toggles and the one head, that of Details, the
    # Inspector having its strip in place of a head (unit N, Task 2)
    drawn = page.evaluate(BAR_AND_HEADS_JS)
    print(f"task 12: the bar {drawn['bar']}, the heads {[h['box'] for h in drawn['heads']]}")
    assert drawn["first"]
    assert (drawn["bar"]["top"], drawn["bar"]["height"]) == (0, 36)
    assert page.evaluate(GROUND_JS, ".bl-main-bar") == ground
    toggles = drawn["toggles"]
    assert [[b["fold"], b["title"], b["label"], b["icon"]] for b in toggles] == TOGGLES
    assert {(b["box"]["width"], b["box"]["height"]) for b in toggles} == {(26, 26)}
    assert {(b["iconBox"]["width"], b["iconBox"]["height"]) for b in toggles} == {(16, 16)}
    marked = [(b["fold"], b["expanded"], b["ground"], b["line"]) for b in toggles]
    assert marked == [(fold, "true", "rgba(0, 0, 0, 0)", accent) for fold, *_ in TOGGLES]
    heads = drawn["heads"]
    assert [head["panel"] for head in heads] == ["details"]
    for head in heads:
        assert abs(head["box"]["height"] - 28) <= 0.5, head
        assert (head["ground"], head["border"]) == ("rgba(0, 0, 0, 0)", ["1px", "solid"]), head
        assert (head["icons"], head["name"]) == (0, HEAD_NAMES[head["panel"]]), head
        assert head["close"] == [f"Close {head['panel']}", HEAD_FOLDS[head["panel"]]], head
    assert page.evaluate(OLD_CONTROLS_JS) == []
    assert contrast_faults(page, CONTRAST_EXCEPTIONS) == []

    # the tab row's `Types` before `Save`, which hides the types in the text
    # and folds no panel (spec 0.4 §§5.1 and 5.4; design pass 10 §4)
    hide = page.locator(".bl-tab-row .bl-types-button")
    hide_box = boxes(page, ".bl-tab-row .bl-types-button")[0]
    save_box = boxes(page, ".bl-tab-row .bl-save")[0]
    assert hide.get_attribute("aria-pressed") == "true"
    assert hide_box["right"] <= save_box["left"], (hide_box, save_box)
    hide.click()
    wait_until(lambda: line_text(page, 13) == "[arvl_to_dcsn] {", 5.0, "line 13 as its name")
    assert hide.get_attribute("aria-pressed") == "false"
    assert page.locator(".bl-classification").is_visible()
    inspector = page.locator('.bl-main-bar .bl-fold[data-fold="inspector"]')
    assert inspector.get_attribute("aria-expanded") == "true"
    hide.click()
    wait_until(lambda: hide.get_attribute("aria-pressed") == "true", 5.0, "the types shown")

    # each toggle, pressed by the keyboard, folds its region and opens it
    # again
    for fold, region in FOLDED_REGION.items():
        button = page.locator(f'.bl-main-bar .bl-fold[data-fold="{fold}"]')
        button.focus()
        page.keyboard.press("Enter")
        wait_until(lambda: not page.locator(region).first.is_visible(), 5.0, f"{fold} folded")
        assert button.get_attribute("aria-expanded") == "false"
        assert button.evaluate(REGION_FILL_JS) != wash
        assert button.evaluate(REGION_LINE_JS) == "none"
        assert page.locator(".bl-window").get_attribute(f"data-folded-{fold}") is not None
        page.keyboard.press("Enter")
        wait_until(lambda: page.locator(region).first.is_visible(), 5.0, f"{fold} opened")
        assert button.get_attribute("aria-expanded") == "true"
        assert button.evaluate(REGION_LINE_JS) == '""'
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "the frame's widths")

    # the toggle `Inspector` folds the BellmanType panel and opens it again,
    # the panel having no close button (unit N, Tasks 1 and 2)
    inspector.click()
    wait_until(lambda: not page.locator(".bl-classification").is_visible(), 5.0, "types folded")
    assert inspector.get_attribute("aria-expanded") == "false"
    inspector.click()
    wait_until(lambda: page.locator(".bl-classification").is_visible(), 5.0, "types opened")

    # Details folded stays folded while another file is opened
    page.click('.bl-region-head[data-panel="details"] .bl-region-close')
    wait_until(lambda: not page.locator(".bl-panel").is_visible(), 5.0, "details folded")
    reveal_in_tree(page, PORT)
    page.click(f'.bl-tree-file[data-path="{PORT}"]')
    wait_until(lambda: status_settled_on(page, PORT), 30.0, "port.bl open")
    page.wait_for_selector(".bl-class-row", timeout=30_000)
    assert not page.locator(".bl-panel").is_visible()
    assert layout_record(page, model_folder)["folds"] == {
        "folder": False,
        "inspector": False,
        "details": True,
        "matsya": False,
    }
    page.click('.bl-main-bar .bl-fold[data-fold="details"]')
    wait_until(lambda: page.locator(".bl-panel").is_visible(), 5.0, "details opened")

    # the icon `open` of Details and of the BellmanType panel
    page.click('.bl-region-head[data-panel="details"] .bl-region-wide')
    page.wait_for_selector(".bl-panel.bl-wide", timeout=10_000)
    assert abs(boxes(page, ".bl-panel")[0]["width"] - 760) <= 0.5
    page.keyboard.press("Escape")
    wait_until(lambda: page.locator(".bl-panel.bl-wide").count() == 0, 10.0, "Escape closing it")
    page.click('.bl-classification[data-panel="types"] .bl-region-wide')
    page.wait_for_selector(".bl-classification.bl-wide", timeout=10_000)
    assert abs(boxes(page, ".bl-classification")[0]["width"] - 760) <= 0.5
    page.click(".bl-classification.bl-wide .bl-region-wide")
    wait_until(
        lambda: page.locator(".bl-classification.bl-wide").count() == 0,
        10.0,
        "the second click returning it",
    )
    assert page.locator(".bl-classification").is_visible()

    # the columns at 1220 and 1140 px, the folder's column at the window's
    # left edge and the toggles on one row, the steps that stood at 1280 and
    # 1200 px before design pass 13 §4 took the window's right margin of 60
    # px away (Q-D6)
    for width in (1220, 1140):
        page.set_viewport_size({"width": width, "height": 1000})
        wait_until(
            lambda width=width: tracks_near(page, FRAME_TRACKS[width, False]),
            5.0,
            f"the columns at {width} px",
        )
        found = tracks(page)
        assert found[0] == FOLDED_FOLDER and all(
            column >= least for column, least in zip(found[1:], LEAST_WIDTHS[1:])
        ), (width, found)
        assert boxes(page, ".bl-folder")[0]["left"] == 0
        assert len({box["top"] for box in boxes(page, ".bl-main-bar .bl-toggle")}) == 1
    page.set_viewport_size({"width": 1220, "height": 1000})
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1220, False]), 5.0, "the columns at 1220")
    page.click('.bl-main-bar .bl-fold[data-fold="folder"]')
    wait_until(lambda: abs(tracks(page)[0] - 170) <= 1, 5.0, "the folder opened at 1220 px")
    found = tracks(page)
    print(f"task 12: the columns at 1220 px with the folder opened: {found}")
    assert all(column >= least - 0.5 for column, least in zip(found, LEAST_WIDTHS)), found


# The form `new trellis` as the page draws it (Task 13), null where it is
# not open: each row of its template list, as whether it is the row of a
# refused entry, its template's id, its height, the texts of its key, its
# model's folder and its refusal, null where it has none, and its hover;
# the value of the field `parent folder`, a text field of VSCode Elements,
# whose value the element holds (design pass 8 §4; unit M, Task 6); the
# note; and whether `write the folder` acts, with its hover.
NEW_TRELLIS_JS = r"""
() => {
  const form = document.querySelector('.bl-form[data-form="new trellis"]');
  if (!form) return null;
  const text = (row, selector) => {
    const found = row.querySelector(selector);
    return found ? found.textContent : null;
  };
  const rows = Array.from(form.querySelectorAll('.bl-templates > li'), (row) => {
    const refused = row.classList.contains('bl-template-refused');
    const button = row.querySelector('.bl-template-button');
    return {
      refused, id: row.dataset.template, height: row.getBoundingClientRect().height,
      key: text(row, '.bl-template-name'), model: text(row, '.bl-template-model'),
      refusal: text(row, '.bl-template-refusal'),
      hover: refused ? row.getAttribute('title') : button.getAttribute('title'),
    };
  });
  const submit = form.querySelector('.bl-create-submit');
  return {
    rows,
    parent: form.querySelector('.bl-create-parent vscode-textfield').value,
    note: form.querySelector('.bl-form-top > .bl-form-note').textContent,
    acts: !submit.disabled,
    waits: submit.getAttribute('title'),
  };
}
"""


def test_task_13_new_trellis_writes_beside_the_open_model_with_one_corpus_template_refused(
    browser, tmp_path, monkeypatch
):
    """Task 13 (defects 1, 15, 19 and 26 of the UX simulation; design pass 4
    §3). A server over a copy of the durables model, `models/durables`,
    reads its templates from a copy of the corpus whose cons.bl the package
    refuses under `output-defined`. The form `new trellis` lists the eight
    entries in their order: the seven templates read, each a row of 24 px,
    and in the place of `cons` its row with its key, `portfolio-choice` and
    `refused · output-defined`, the package's sentence in its hover with no
    absolute path. Its field `parent folder` holds the folder that holds
    the open model, and the note reads `writes models/<name>/ beside
    durables, with a new repository`. `write the folder` does not act, its
    hover `type a name`, until the name is typed, and then acts with no
    template chosen. With `port` chosen it writes `models/pensions/`, beside
    the durables model, whose files are as they were, and opens the new
    folder, whose stage list's hovers carry no title of the durables model,
    the folder's own stage `port` carrying the new folder's name."""
    corpus = refused_corpus(tmp_path / "corpus")
    monkeypatch.setattr(creation, "CORPUS", corpus)
    site = corpus_startup(tmp_path / "site", corpus)
    paths = [str(site), os.environ.get("PYTHONPATH", "")]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(path for path in paths if path))
    models = tmp_path / "models"
    durables = repository_copy(DURABLES, models / "durables")
    before = file_bytes(durables)
    title = creation._model_title(durables)
    offered = [template.id for template in creation.stage_templates()]
    entries = [entry.id for entry in creation.template_entries()]
    assert CONS_ID in entries and CONS_ID not in offered and len(offered) == 7
    port = free_port()
    url = f"http://localhost:{port}/"
    log_path = tmp_path / "solara.log"
    process = start_server(durables, port, log_path)
    context = None
    try:
        error = server_error(url, process, log_path)
        assert error is None, error
        context, tab = new_tab(browser)
        open_workbench(tab, url)
        selector = open_page_form(tab, "new trellis")
        # the form's element is drawn with its templates before its fields,
        # each a component of field.vue, which mount some 70 ms later; the
        # form is read once the field `parent folder` stands in it
        tab.wait_for_selector(f"{selector} .bl-create-parent vscode-textfield", timeout=10_000)
        drawn = tab.evaluate(NEW_TRELLIS_JS)
        rows = drawn["rows"]
        assert [row["id"] for row in rows] == entries
        assert [row["id"] for row in rows if not row["refused"]] == offered
        assert {row["height"] for row in rows} == {24}, rows
        (refused,) = [row for row in rows if row["refused"]]
        assert (refused["id"], refused["key"], refused["model"], refused["refusal"]) == (
            CONS_ID,
            "cons",
            "portfolio-choice",
            "refused · output-defined",
        )
        assert "declares output 'cons:dcsn:c'" in refused["hover"]
        assert not ABSOLUTE_PATH.search(refused["hover"]), refused["hover"]
        assert drawn["parent"] == str(models.resolve())
        assert drawn["note"] == "writes models/<name>/ beside durables, with a new repository"
        assert (drawn["acts"], drawn["waits"]) == (False, "type a name")
        tab.fill(f"{selector} .bl-create-name input", "pensions")
        wait_until(lambda: tab.evaluate(NEW_TRELLIS_JS)["acts"], 10.0, "write the folder acting")
        assert tab.evaluate(NEW_TRELLIS_JS)["waits"] is None
        tab.click(f'{selector} .bl-template-button[data-template="{PORT_ID}"]')
        tab.wait_for_selector(f'{selector} .bl-template.bl-active[data-template="{PORT_ID}"]')
        tab.click(f"{selector} .bl-create-submit")
        tab.wait_for_selector('.bl-form[data-form="commit"]', timeout=30_000)
        tab.click(".bl-form-cancel")
        created = models / "pensions"
        assert (created / "declaration/stages/port/port.bl").is_file()
        assert (created / ".git").is_dir()
        assert file_bytes(durables) == before
        assert sorted(path.name for path in models.iterdir()) == ["durables", "pensions"]

        # the new folder's stage list
        wait_until(lambda: trellis_settled(tab, RECIPE_FILE), 120.0, "the new folder's trellis")
        choose_view(tab, None, "forward")
        open_stage_list(tab)
        listed = tab.evaluate(STAGE_LIST_ROWS_JS)["rows"]
        hovers = [row["hover"] or "" for row in listed if "section" not in row]
        assert not [hover for hover in hovers if title in hover], hovers
        (own,) = [row for row in listed if row.get("kind") == "stage"]
        assert (own["key"], own["model"]) == ("port", "pensions")
        assert own["hover"].startswith("pensions · ")
        assert [row["item"] for row in listed if row.get("kind") == "template"] == offered
    finally:
        if context is not None:
            context.close()
        stop_server(process)


# The stage list over the graph, null where none is drawn: the period it is
# opened for, null for the list the button `stages` opens, and each item as
# its id and whether it is dimmed as listed in that period (Task 14)
PERIOD_LIST_JS = r"""
() => {
  const list = document.querySelector('.bl-view-host .bf-stage-list');
  if (!list) return null;
  const period = list.querySelector('.bf-stage-period');
  return {
    period: period ? period.textContent : null,
    items: Array.from(list.querySelectorAll('.bf-stage-item'),
      (item) => [item.dataset.item, item.classList.contains('bf-listed')]),
  };
}
"""
# the connector of the pension model's periods[0], which joins `shocks` to
# `bequest_pa` in five pairs, its pairs, its line in the trellis file and the
# list of stages that holds both (Task 14)
BEQUEST_PAIRS = "a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq"
BEQUEST_CONNECTOR_LINE = f"      - {{{BEQUEST_PAIRS}}}\n"
BEQUEST_LISTED = "stages: [shocks, bequest_pa]"


def period_layer(h: int) -> str:
    """The selector of the open layer of period `h` in the graph region."""
    return f'.bl-view-host .react-flow__node[data-id="periods[{h}]{LAYER_ID_ENDING}"] > .bf-layer'


def refused(tab) -> bool | None:
    """Whether the status line names the pension model's trellis after a
    reading that the package refused, its part `refused`; None before the
    status line names a reading."""
    text = trellis_settled(tab, PENSIONS_RECIPE)
    return "refused" in text.split(" · ") if text else None


def test_task_14_a_stage_moved_between_periods_takes_its_joins_and_a_copied_stage_s_are_named(
    browser, server_on, tmp_path
):
    """Removing a stage removes its authored connectors. Re-entering those connectors leaves a visible draft with unresolved endpoint diagnostics; dropping the missing stage back activates the retained entries and restores the source."""
    copy = pensions_copy(tmp_path / "models" / "durables")
    text = (copy / PENSIONS_TRELLIS).read_text(encoding="utf-8")
    assert text.count(BEQUEST_LISTED) == 1 and text.count(BEQUEST_CONNECTOR_LINE) == 1
    removed = text.replace(BEQUEST_LISTED, "stages: [shocks]").replace(
        BEQUEST_CONNECTOR_LINE, "      - {}\n"
    )
    typed = removed.replace("      - {}\n", BEQUEST_CONNECTOR_LINE)
    occurrence = f"periods[0]/bequest_pa{LAYER_ID_ENDING}"
    node = f'.bl-view-host .react-flow__node[data-id="{occurrence}"]'
    context, tab = new_tab(browser)
    try:
        # the backward graph of this model is refused (the language's gap §5 of
        # the simulation's record), so the view opens on no box
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.locator(node).count() == 1, 60.0, "bequest_pa in periods[0]")

        # Backspace on the closed frame of `bequest_pa` in periods[0]
        click_toggle(tab, occurrence)
        frame = f"{node} > .bf-box"
        wait_until(lambda: tab.locator(frame).count() == 1, 10.0, "bequest_pa's frame closed")
        tab.click(f"{frame} .bf-symbol")
        wait_until(
            lambda: flow_handle(tab, "selection") == occurrence, 10.0, "bequest_pa selected"
        )
        tab.keyboard.press("Backspace")
        note = (
            "trellis.pensions.yml, periods[0].stages: bequest_pa removed, periods 0; "
            "trellis.pensions.yml, periods[0].connectors[0]: "
            f"{{{BEQUEST_PAIRS}}} removed, periods 0"
        )
        wait_until(lambda: gesture_note(tab) == note, 10.0, "the removal's note")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == removed, 10.0, "the key and its joins out")
        wait_until(
            lambda: tab.locator(node).count() == 0 and refused(tab) is False,
            60.0,
            "the trellis constructed without bequest_pa in periods[0]",
        )

        # the five pairs typed again by hand: the reading stands refused
        line = removed.split("\n").index("      - {}") + 1
        click_before(tab, line, "}")
        tab.keyboard.type(BEQUEST_PAIRS)
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == typed, 10.0, "the pairs typed")
        wait_until(
            lambda: not refused(tab)
            and any("a_bq" in sentence for sentence, _, _ in error_lines(tab)),
            60.0,
            "the package's refusal of the connector",
        )

        # `+ stage` of periods[1] opens the list on the last graph constructed
        tab.click(".bl-zoom-button[data-zoom='fit']")
        control = f"{period_layer(1)} > .bf-add-stage"
        wait_until(
            lambda: tab.locator(control).get_attribute("aria-disabled") is None,
            10.0,
            "the control + stage of periods[1] acting",
        )
        tab.click(control)
        listed, _ = wait_until(
            lambda: tab.evaluate(PERIOD_LIST_JS), 10.0, "the stage list of periods[1]"
        )
        assert listed["period"] == "periods[1]"
        assert ["bequest_pa", True] in listed["items"], listed
        tab.keyboard.press("Escape")
        wait_until(lambda: tab.evaluate(PERIOD_LIST_JS) is None, 10.0, "the list closed")

        # the drop lists `bequest_pa` in periods[0] again
        drop_item(tab, "bequest_pa", f"periods[0]{LAYER_ID_ENDING}")
        note = (
            "trellis.pensions.yml, periods[0].stages: bequest_pa written, periods 0; "
            f"trellis.pensions.yml, periods[0].connectors[0]: {BEQUEST_PAIRS} now join bequest_pa"
        )
        wait_until(lambda: gesture_note(tab) == note, 10.0, "the drop's note")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 10.0, "the text as it was")
        wait_until(
            lambda: tab.locator(node).count() == 1 and refused(tab) is False,
            60.0,
            "the trellis constructed with bequest_pa in periods[0]",
        )
        assert not [line for line in error_lines(tab) if "'a_bq'" in line[0]]
    finally:
        context.close()


# The pension model at its first build of the working years (Task 15): the
# stage file of `allocation`, the join wire from `contribution` to it in
# periods[4], whose ten joins equal names make, as Details prints it; the
# two places at which the stage file writes the arrival field `w_c`, as
# written and as the rename to `w_in` writes them; and the ports of
# contribution's `w_c` and allocation's `w_in` in periods[4] once the rename
# is read, and the port of allocation's measure, which carries the joins
ALLOCATION = "declaration/stages/allocation/allocation.bl"
CONTRIBUTION_ALLOCATION = ("periods[4]/contribution", "periods[4]/allocation")
NAME_JOIN_CARD = CONTRIBUTION_JOIN_ROWS
W_C_WRITTEN = (
    ("(w_c : ℝ₊, adc_c", "(w_in : ℝ₊, adc_c"),
    ("w_d       = w_c\n", "w_d       = w_in\n"),
)
CONTRIBUTION_W_C = "periods[4]/contribution/unjoined:contribution:cntn:w_c"
ALLOCATION_W_IN = "periods[4]/allocation/unjoined:allocation:arvl:w_in"
ALLOCATION_ARRIVAL = "periods[4]/allocation/allocation:measure:arvl"


def test_task_15_a_join_by_equal_names_is_selected_and_its_reading_field_renamed(
    browser, server_on, tmp_path
):
    """Task 15 (defect 3 of the UX simulation; L-D13; J-D33 and J-D39
    extended to joins by equal names). On a copy of the pension model the
    UX simulation's post-doc built, at its first build of the working
    years, its forward graph restricted to periods[4]: a click on the wire
    from `contribution` to `allocation`, whose ten joins equal names make,
    selects that join, drawn in ultramarine-light, and Details prints its
    head, `joined by the names` under `written`, the two measures and the
    ten fields, and offers `rename` and no `remove`; Backspace in the region
    removes nothing. `rename` of the reading field `w_c` to `w_in` writes
    allocation's stage file at its header's listing and at the line that
    reads it, as the file's unsaved text, which the editor opens, the
    status line naming the file and the two lines; no other file changes,
    and nothing is written to disk until the file is saved. Saved, the
    trellis is read with contribution's `w_c` and allocation's `w_in` drawn
    unjoined, each named among the unjoined fields of its card's cable port;
    the drag from contribution's branch port to allocation's arrival port,
    the move of the cable onto its own destination, opens the cable's list,
    in which `w_c` chosen for `w_in` types `{w_c: w_in}` into the
    connectors of the period file the working years take (design pass 10
    §7; unit N, Task 7), the trellis read again constructed, not refused,
    with the two fields joined by that connector."""
    copy = pensions_copy(tmp_path / "models" / "durables", PENSIONS_WORKING_YEARS)
    file = copy / ALLOCATION
    text = file.read_text(encoding="utf-8")
    renamed = text
    for old, new in W_C_WRITTEN:
        renamed = renamed.replace(old, new)
    untouched = {
        name: (copy / name).read_text(encoding="utf-8")
        for name in (
            PENSIONS_TRELLIS,
            PENSIONS_RECIPE,
            "declaration/period.pensions.yml",
            "declaration/stages/contribution/contribution.bl",
        )
    }
    context, tab = new_tab(browser)
    try:
        # the trellis opens restricted to periods 0–2, whose backward graph
        # is refused (the language's gap §5 of the simulation's record), so
        # the view opens on no box
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)
        choose_view(tab, None, "forward")
        restrict(tab, "periods 4")
        wait_until(
            lambda: " · shown periods 4 of 7 " in (trellis_settled(tab, PENSIONS_RECIPE) or ""),
            60.0,
            "the view restricted to periods[4]",
        )
        # the period shown alone opens with its stage occurrences open, so
        # that no toggle is pressed (Task 22, which corrected this step)
        wait_until(
            lambda: CONTRIBUTION_ALLOCATION
            in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the join wire by equal names drawn",
        )

        # the click selects the join, for which Details offers `rename` alone
        click_join(tab, *CONTRIBUTION_ALLOCATION)
        light = property_color(tab, "--bl-ultramarine-light")
        selected = {"from": CONTRIBUTION_ALLOCATION[0], "to": CONTRIBUTION_ALLOCATION[1]}
        wait_until(
            lambda: [w for w in join_wires_drawn(tab) if w["selected"]]
            == [{**selected, "selected": True, "stroke": light}],
            10.0,
            "the join by equal names selected",
        )
        head = "join periods[4]/contribution → periods[4]/allocation forward"
        details_until(tab, (head, NAME_JOIN_CARD), "the join's rows in Details")
        details = tab.locator(".bl-join-details")
        assert details.locator(".bl-join-remove").count() == 0
        assert details.locator(".bl-join-rename").count() == 1
        document = tab.evaluate(DOCUMENT_JS)
        tab.keyboard.press("Backspace")
        tab.wait_for_timeout(300)
        assert tab.evaluate(DOCUMENT_JS) == document and gesture_note(tab) is None
        assert unsaved_in_tree(tab) == []

        # `rename` of `w_c` to `w_in` writes the stage file's unsaved text
        choose_option(tab, ".bl-join-rename-field", "w_c")
        button = details.locator(".bl-join-rename-button")
        assert button.is_disabled()
        tab.fill(".bl-join-rename-name input", "w_in")
        wait_until(lambda: button.is_enabled(), 10.0, "the button rename enabled")
        assert button.get_attribute("title") == "Rename w_c in allocation.bl"
        button.click()
        note = "allocation.bl, lines 22–23: w_c renamed to w_in"
        wait_until(lambda: gesture_note(tab) == note, 10.0, "the rename's note")
        wait_until(lambda: open_path_shown(tab) == ALLOCATION, 30.0, "the stage file open")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == renamed, 10.0, "the field renamed")
        assert unsaved_in_tree(tab) == [ALLOCATION]
        assert file.read_text(encoding="utf-8") == text
        for name, written in untouched.items():
            assert (copy / name).read_text(encoding="utf-8") == written, name

        # saved, the two fields are read unjoined, and a drag joins them
        tab.click(".bl-save")
        wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "the stage file saved")
        assert file.read_text(encoding="utf-8") == renamed
        wait_until(
            lambda: {CONTRIBUTION_W_C, ALLOCATION_W_IN} <= set(unjoined_field_ids(tab)),
            60.0,
            "the two fields unjoined",
        )
        # the drag from contribution's branch port to allocation's arrival port
        # opens the cable's list, in which `w_c` is chosen for `w_in` (design
        # pass 10 §7)
        drag_cable(tab, "periods[4]/contribution", "", "periods[4]/allocation", {ALLOCATION_W_IN: CONTRIBUTION_W_C})
        # the drag from the joined branch port is the move of the cable onto
        # its own destination, whose list keeps the nine pairs equal names
        # make and adds `w_c → w_in`; the note of a cable's write names no
        # form (unit N, Task 7)
        note = "period.pensions.yml, connectors: {w_c: w_in} written, periods 4–6"
        wait_until(lambda: gesture_note(tab) == note, 10.0, "the drag's note")
        wait_until(
            lambda: "w_c → w_in" in held_joins(tab).get(ALLOCATION_ARRIVAL, "")
            and not {CONTRIBUTION_W_C, ALLOCATION_W_IN} & set(unjoined_field_ids(tab)),
            60.0,
            "the two fields joined by the connector",
        )
        # the held collection changes before the region has drawn it, while
        # the status line still ends in `drawing`, so the line is read once
        # it names the reading settled (unit N, Task 7)
        wait_until(lambda: refused(tab) is not None, 10.0, "the reading's status line settled")
        assert refused(tab) is False
        assert unsaved_in_tree(tab) == ["declaration/period.pensions.yml"]
    finally:
        context.close()


# The pension model at step 29 of the UX simulation's record (Task 16): the
# stage file of `shocks` and the calibration file `new file` wrote for it,
# `calibration: {}`, which the recipe names in place of its slot; the
# fourteen values the post-doc typed in the Parameters tab, in his order,
# and the matrix he typed for `Π_α` at step 30; and each row's value input,
# by the row's name
SHOCKS = "declaration/stages/shocks/shocks.bl"
SHOCKS_CALIBRATION = "declaration/calibration/shocks.yml"
SHOCKS_VALUES = (
    ("R", "1.0223"),
    ("δ", "0.011"),
    ("Y", "0.0"),
    ("φ", "0.9044"),
    ("σ_u", "0.0922"),
    ("r_r", "0.0476"),
    ("r_s", "0.0193"),
    ("scale_r", "1.68"),
    ("scale_s", "0.54"),
    ("σ_d", "0.064"),
    ("β_m", "3.36"),
    ("κ_m", "0.33"),
    ("r_h", "0.032"),
    ("σ_h", "0.042"),
)
TASTE_MATRIX = "[[0.6, 0.1, 0.3], [0.05, 0.9, 0.05], [0.03, 0.02, 0.95]]"
VALUE_INPUTS_JS = r"""
() => Object.fromEntries(Array.from(document.querySelectorAll('.bl-values-row'),
  (row) => [row.dataset.name, row.querySelector('.bl-values-value').value]))
"""


def test_task_16_values_typed_a_second_apart_all_stand_and_a_matrix_gets_the_package_s_sentence(
    browser, server_on, tmp_path
):
    """Task 16 (defects 4 and 5 of the UX simulation; L-D13; K-D11). On a
    copy of the pension model the UX simulation's post-doc built, at step
    29 of its record, `shocks.bl` bound as `periods[0] / shocks` with its
    Parameters tab writing the calibration file `new file` wrote,
    `calibration: {}`: the fourteen values the post-doc typed are typed one
    second apart, each with Enter. After each Enter every value typed so
    far stands in its input through the next second, none reading
    `unvalued` again, and after the first the status line prints the loop
    running. After the reading the fourteen values stand in their inputs,
    and the file holds each once. The matrix of step 30 typed for `Π_α` is
    written, the tab composing no sentence about its form, and the
    package's sentence refusing it, which names `Π_α`, stands in the list
    under the error mark and on the row: its input shows the matrix,
    marked, with the sentence as its hover."""
    copy = pensions_copy(tmp_path / "models" / "durables")
    (copy / SHOCKS_CALIBRATION).parent.mkdir(parents=True, exist_ok=True)
    (copy / SHOCKS_CALIBRATION).write_text("calibration: {}\n", encoding="utf-8")
    recipe_file = copy / PENSIONS_RECIPE
    recipe_text = recipe_file.read_text(encoding="utf-8")
    assert recipe_text.count("$shocks_calibration") == 1
    recipe_file.write_text(
        recipe_text.replace("$shocks_calibration", "calibration/shocks"), encoding="utf-8"
    )
    expected = {name: float(value) for name, value in SHOCKS_VALUES}
    taste = '.bl-values-row[data-name="Π_α"] .bl-values-value'
    context, tab = new_tab(browser)
    try:
        # the backward graph of this model is refused (the language's gap §5 of
        # the simulation's record), so the view opens on no box
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)
        reveal_in_tree(tab, SHOCKS)
        tab.click(f'.bl-tree-file[data-path="{SHOCKS}"]')
        wait_until(lambda: recipe_head(tab) == "periods[0] / shocks", 120.0, "shocks bound")
        wait_until(lambda: status_settled_on(tab, SHOCKS), 120.0, "the loop of shocks.bl")
        tab.click('.bl-class-tab[data-tab="Parameters"]')
        named = ".bl-values-file"
        wait_until(
            lambda: tab.locator(named).count()
            and tab.locator(named).text_content() == f"writes {SHOCKS_CALIBRATION}",
            30.0,
            "the tab naming the calibration file",
        )
        inputs = tab.evaluate(VALUE_INPUTS_JS)
        assert {inputs[name] for name, _ in SHOCKS_VALUES} == {"unvalued"}

        # fourteen values, one second apart
        started = time.perf_counter()
        for n, (name, value) in enumerate(SHOCKS_VALUES):
            cell = tab.locator(f'.bl-values-row[data-name="{name}"] .bl-values-value')
            cell.fill(value)
            cell.press("Enter")
            if n == 0:
                wait_until(lambda: "elaborating" in status_text(tab), 5.0, "the loop running")
            typed = dict(SHOCKS_VALUES[: n + 1])
            while time.perf_counter() < started + n + 1:
                inputs = tab.evaluate(VALUE_INPUTS_JS)
                assert {key: inputs[key] for key in typed} == typed, (name, inputs)
                tab.wait_for_timeout(100)

        def written() -> dict | None:
            # the file's calibration where it reads, None otherwise
            try:
                held = (copy / SHOCKS_CALIBRATION).read_text(encoding="utf-8")
                return entry_value(held, "calibration")
            except (OSError, KeyError, ValueError):
                return None

        wait_until(
            lambda: written() == expected and status_settled_on(tab, SHOCKS),
            180.0,
            "the fourteen values written and the reading settled",
        )
        # the file reads, and the package's reader refuses a key written
        # twice, so that each value stands once
        inputs = tab.evaluate(VALUE_INPUTS_JS)
        assert {name: inputs[name] for name, _ in SHOCKS_VALUES} == dict(SHOCKS_VALUES)

        # the matrix of step 30 is passed to the package, whose sentence
        # stands under the error mark and on the row
        tab.locator(taste).fill(TASTE_MATRIX)
        tab.locator(taste).press("Enter")
        wait_until(
            lambda: all(name in (tab.locator(taste).get_attribute("title") or "")
                        for name in ("Π_α", TASTE_MATRIX)),
            180.0,
            "the package's sentence on the row of Π_α",
        )
        assert tab.locator(taste).input_value() == TASTE_MATRIX
        assert "bl-refusal-mark" in tab.locator(taste).get_attribute("class").split()
        lines = error_lines(tab)
        # The sentence and affected occurrence are separate facts of one line.
        refused = trellis.show_trellis(
            model.open_folder(copy), recipe.Source("recipe", PENSIONS_RECIPE)
        ).shown.binding.failed["calibrate"]
        assert refused.occurrences == ((0, "shocks"),)
        sentence = model.sentence(refused).replace(str(copy.resolve()) + "/", "")
        assert tab.locator(taste).get_attribute("title") == sentence
        assert [line[0] for line in lines].count(sentence) == 1, lines
        assert "shocks at period 0" in tab.locator(".bl-error-occurrences").all_text_contents()
        assert not [line for line in lines if " reads as " in line[0]], lines
        assert written() == {**expected, "Π_α": entry_value(TASTE_MATRIX)}
    finally:
        context.close()


# The portfolio model's trellis file; the end of the recipe's row of `port`,
# and the same row with the periods 0 to 5, which Task 17's copy gives it so
# that a period added with `port` at the earliest end also widens its range
# in the recipe (spec 0.4 §3.6); and the stage file `new stage` writes for
# the key buyer (K-D7)
PORTFOLIO_TRELLIS = "declaration/trellis.yml"
PORT_ROW_END = "methods: {all: [stages/port/methods.bl]}}"
PORT_RANGE = "methods: {all: [stages/port/methods.bl]}, periods: [0, %d]}"
BUYER_STAGE_FILE = "declaration/stages/buyer/buyer.bl"


def test_task_17_one_undo_per_gesture_in_every_file_and_new_stage_saved_and_parsing(
    browser, server_on, tmp_path
):
    """Task 17 (defects 6, 7 and 22 of the UX simulation; L-D13; K-D7 and
    K-I139 amended). On a copy of the portfolio model whose recipe gives
    `port` the periods 0 to 5, its recipe open: `add period` with the label
    `young` and the stages port, cons and disc adds the period at the
    earliest end of the trellis file and widens port's range in the recipe
    to 0 to 6, both files unsaved; `add period` with `older` does so again,
    to 0 to 7. One Cmd+Z in the recipe takes the second gesture back in both
    files and the first in neither: the recipe holds the text the first
    wrote, and the trellis file, its tab opened, holds it too. Back in the
    recipe's tab, whose editor history the change of tab began again
    (R-D45), one Cmd+Z takes the first gesture back in both files, which
    then hold their texts on disk, no file unsaved. Then `new stage` with
    the key buyer writes declaration/stages/buyer/buyer.bl and the recipe's
    row to disk, no tab reading `unsaved`; the stage file, which the editor
    opens, is not refused by the parser, the BellmanType panel shows its
    Fields tab, and the box `add field` of the continuation table writes the
    stage's first field, `a : ℝ₊`, into the output side of dcsn_to_cntn."""
    copy = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
    recipe_file, trellis_file = copy / RECIPE_FILE, copy / PORTFOLIO_TRELLIS
    original = recipe_file.read_text(encoding="utf-8").replace(PORT_ROW_END, PORT_RANGE % 5)
    recipe_file.write_text(original, encoding="utf-8")
    standing = trellis_file.read_text(encoding="utf-8")
    six = "  - {template: period.yml, repeat: 6}\n"
    assert standing.count(six) == 1
    # each text the two gestures make: the range widened, the period added
    recipes = [original.replace(PORT_RANGE % 5, PORT_RANGE % n) for n in (5, 6, 7)]
    young = six + "  - {template: period.young.yml, repeat: 1}\n"
    trellises = [
        standing,
        standing.replace(six, young),
        standing.replace(six, young + "  - {template: period.older.yml, repeat: 1}\n"),
    ]
    edited = [RECIPE_FILE, PORTFOLIO_TRELLIS]
    context, tab = new_tab(browser)

    def shown_in(path: str) -> str:
        # the text of `path` once its tab is opened, read a second after the
        # file shows, since the editor may take its properties in two steps
        tab.click(f'.bl-tab[data-path="{path}"]')
        wait_until(lambda: open_path_shown(tab) == path, 30.0, f"{path} open")
        tab.wait_for_timeout(1_000)
        return tab.evaluate(DOCUMENT_JS)

    def undone_to(text: str, what: str) -> None:
        # one Cmd+Z in the editor, after which the editor holds `text`, and
        # still holds it a second later
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 10.0, what)
        tab.wait_for_timeout(1_000)
        assert tab.evaluate(DOCUMENT_JS) == text, what

    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        for n, label in ((1, "young"), (2, "older")):
            form = open_page_form(tab, "add period")
            tab.fill(".bl-period-label input", label)
            for key in ("port", "cons", "disc"):
                tab.click(f'{form} .bl-period-stage[data-key="{key}"]')
            tab.click(".bl-period-submit")
            wait_until(lambda: tab.locator(form).count() == 0, 30.0, f"the period {label} added")
            wait_until(
                lambda n=n: tab.evaluate(DOCUMENT_JS) == recipes[n],
                10.0,
                f"the range widened by {label}",
            )
            wait_until(lambda: unsaved_in_tree(tab) == edited, 10.0, "both files unsaved")

        # one undo in the recipe takes the second gesture back in both files
        undone_to(recipes[1], "the second gesture undone")
        assert unsaved_in_tree(tab) == edited
        assert shown_in(PORTFOLIO_TRELLIS) == trellises[1]

        # back in the recipe, one undo takes the first gesture back in both
        assert shown_in(RECIPE_FILE) == recipes[1]
        undone_to(original, "the first gesture undone")
        wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "no file unsaved")
        assert shown_in(PORTFOLIO_TRELLIS) == standing

        # `new stage` writes the stage file and the recipe's row together
        open_page_form(tab, "new stage")
        tab.fill(".bl-new-stage-key input", "buyer")
        tab.click(".bl-new-stage-submit")
        wait_until(lambda: open_path_shown(tab) == BUYER_STAGE_FILE, 30.0, "buyer.bl open")
        row = f"  buyer: {creation.recipe_row('buyer')}\n"
        assert recipe_file.read_text(encoding="utf-8") == original + row
        wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "no file unsaved")
        assert not [held for held in file_tabs(tab) if held["unsaved"]], file_tabs(tab)
        status = wait_until(
            lambda: status_settled_on(tab, BUYER_STAGE_FILE), 60.0, "the loop of buyer.bl"
        )[0]
        assert "not parsed" not in status, status
        wait_until(
            lambda: tab.locator('.bl-class-tab[data-tab="Fields"].bl-active').count() == 1
            and tab.locator(".bl-class-empty").count() == 0,
            30.0,
            "the Fields tab of buyer.bl",
        )
        # the box `add field` of the continuation table writes the stage's
        # first field into the output side of dcsn_to_cntn
        stage_text = (copy / BUYER_STAGE_FILE).read_text(encoding="utf-8")
        assert tab.evaluate(DOCUMENT_JS) == stage_text
        add_field(tab, "cntn/", "a", "ℝ₊", "state")
        header = "[id=dcsn_to_cntn, () : !dcsn -> () : !cntn] {"
        first = stage_text.replace(header, header.replace("() : !cntn", "(a : ℝ₊) : !cntn"))
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == first, 10.0, "the first field written")
    finally:
        context.close()


# The stage files of the pension model whose Methods tabs defects 8 and 9
# of the UX simulation name, with their additions; the names the package's
# refusal of `!monte_carlo` chosen at `arvl_to_dcsn` of `renter_cons` gives,
# whose entry then writes no `n_paths`, by which the refusal is read and
# not by its wording; and the rows of the Methods tab shown, each as
# its target, the words its select offers, the word it shows and the
# method bound as the row prints it (unit L, Task 18).
RENTER_CONS = "declaration/stages/renter_cons/renter_cons.bl"
RENTER_CONS_METHODS = "declaration/stages/renter_cons/methods.bl"
TENURE_PA = "declaration/stages/tenure_pa/tenure_pa.bl"
TENURE_PA_METHODS = "declaration/stages/tenure_pa/methods.bl"
MONTE_CARLO_NAMES = ("renter_cons", "arvl_to_dcsn.method : !monte_carlo", "n_paths")
METHOD_ROWS_JS = r"""
() => Array.from(document.querySelectorAll('.bl-values[data-tab="Methods"] .bl-values-row'),
  (row) => {
    const choice = row.querySelector('select.bl-values-method');
    const shown = choice || row.querySelector('.bl-values-tag');
    return {
      target: row.dataset.name,
      offers: choice ? Array.from(choice.options, (option) => option.textContent) : [],
      tag: choice ? choice.value : shown.textContent.trim(),
      bound: row.querySelector('.bl-values-detail').textContent.trim(),
    };
  })
"""


def test_task_18_the_methods_tab_offers_what_the_block_admits_and_empties_when_refused(
    browser, server_on, tmp_path
):
    """Task 18 (defects 8 and 9 of the UX simulation; L-D13; AMD-MI-002 §5
    rule 5; K-I150), with the tab read from the methods the stage binds
    (decision S7-W1 of specification 0.7). On a copy of the pension model
    the UX simulation's post-doc built, at its first build of the working
    years, `renter_cons.bl` bound as `periods[1] / renter_cons` shows in its
    Methods tab the four places its addition types, in the package's order,
    each with the word bound there. The row `arvl_to_dcsn`, a forward
    identity block, offers the words the package admits there,
    `admitted_methods` of `bellman.stage`, `!monte_carlo` among them.
    `!monte_carlo` chosen there is written into the addition in place of
    `!deterministic`, and the package refuses it, since the entry writes no
    `n_paths`: the stage then binds no method, so that the tab has no row,
    and the sentence stands in the list under the error mark. `tenure_pa.bl`,
    a branching stage, bound as `periods[1] / tenure_pa` shows the four
    places of its addition, each with a choice among the words the package
    admits at its target, and no sentence in the tab."""
    copy = pensions_copy(tmp_path / "models" / "durables", PENSIONS_WORKING_YEARS)
    renter = elaborate_text((copy / RENTER_CONS).read_text(encoding="utf-8"), RENTER_CONS)
    tenure = elaborate_text((copy / TENURE_PA).read_text(encoding="utf-8"), TENURE_PA)
    forward = admitted_methods(renter, "arvl_to_dcsn")
    assert "!monte_carlo" in forward
    bound = {
        "arvl_to_dcsn": "!deterministic",
        "dcsn_to_cntn": "!deterministic",
        "cntn_to_dcsn.evaluate": "!Linear",
        "policy.optimality.argmax": "!root_find",
    }
    methods = (copy / RENTER_CONS_METHODS).read_text(encoding="utf-8")
    entry = "arvl_to_dcsn.method : !deterministic\n"
    assert methods.count(entry) == 1
    context, tab = new_tab(browser)
    try:
        # the backward graph of this model is refused (the language's gap §5
        # of the simulation's record), so the view opens on no box
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)

        def shown(path: str, key: str, written: str) -> None:
            # the stage file `path` opened from the tree, bound as
            # `periods[1] / <key>`, and its Methods tab naming `written`
            reveal_in_tree(tab, path)
            tab.click(f'.bl-tree-file[data-path="{path}"]')
            wait_until(lambda: recipe_head(tab) == f"periods[1] / {key}", 120.0, f"{key} bound")
            wait_until(lambda: status_settled_on(tab, path), 120.0, f"the loop of {key}")
            tab.click('.bl-class-tab[data-tab="Methods"]')
            named = ".bl-values-file"
            wait_until(
                lambda: tab.locator(named).count()
                and tab.locator(named).text_content() == f"writes {written}",
                30.0,
                f"the Methods tab of {key}",
            )

        shown(RENTER_CONS, "renter_cons", RENTER_CONS_METHODS)
        rows = {row["target"]: row for row in tab.evaluate(METHOD_ROWS_JS)}
        assert list(rows) == list(bound)
        assert {target: (row["tag"], row["bound"]) for target, row in rows.items()} == {
            target: (tag, tag) for target, tag in bound.items()
        }
        assert rows["arvl_to_dcsn"]["offers"] == list(forward)

        # a choice the block admits and the package refuses binds no method
        choice = '.bl-values-row[data-name="arvl_to_dcsn"] select.bl-values-method'
        tab.locator(choice).select_option("!monte_carlo")
        wait_until(
            lambda: (copy / RENTER_CONS_METHODS).read_text(encoding="utf-8")
            == methods.replace(entry, entry.replace("!deterministic", "!monte_carlo")),
            30.0,
            "!monte_carlo written for arvl_to_dcsn",
        )

        wait_until(
            lambda: not tab.evaluate(METHOD_ROWS_JS), 120.0, "the tab of renter_cons emptied"
        )
        lines = error_lines(tab)
        refused = trellis.show_trellis(
            model.open_folder(copy), recipe.Source("recipe", PENSIONS_RECIPE)
        ).refusal
        assert refused is not None and any(key == "renter_cons" for _, key in refused.occurrences)
        sentence = model.sentence(refused).replace(str(copy.resolve()) + "/", "")
        assert all(name in sentence for name in MONTE_CARLO_NAMES)
        assert [line[0] for line in lines].count(sentence) == 1, lines

        # the branching stage's rows, each with its choices, and no sentence
        # in the tab
        shown(TENURE_PA, "tenure_pa", TENURE_PA_METHODS)
        wait_until(
            lambda: [row["target"] for row in tab.evaluate(METHOD_ROWS_JS)]
            == ["arvl_to_dcsn", "dcsn_to_cntn", "cntn_to_dcsn.evaluate", "policy"],
            30.0,
            "the four rows of tenure_pa",
        )
        assert tab.locator(".bl-values-sentence").count() == 0
        for row in tab.evaluate(METHOD_ROWS_JS):
            assert row["offers"] and row["offers"] == list(
                admitted_methods(tenure, row["target"])
            ), row
            assert row["bound"] == row["tag"], row
    finally:
        context.close()


# the four ids by which an event names a join wire
JOIN_IDS = ("source", "sourceHandle", "target", "targetHandle")
# whether the element that holds the focus is the select of the row of the
# list of a move whose index the argument gives
ROW_SELECT_FOCUSED_JS = """
(index) => document.activeElement ===
  document.querySelectorAll('.bl-view-host .bf-pair-row select')[index]
"""
# the connector of the pension model's periods[0] as the post-doc wrote it,
# and the one connector of its first drag (steps 21 and 22 of the record)
BEQUEST_CONNECTOR = "      - {a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq}\n"
FIRST_DRAG_CONNECTOR = "      - {a_s: a_bq}\n"
# the fields of `shocks` in periods[0] as the list of the move of the wire
# to `bequest_pa` names its rows: the wire's five field pairs, then the six
# unjoined continuation fields of `shocks`
SHOCKS_ROWS = ["a_s", "adc_s", "h_s", "m_s", "P_s", "plan_s", "y_s", "α_s", "β_s", "ξ_s", "π_s"]
# the comment over the retirement years' entry of the trellis file at the
# first build of the working years, the entry of the period `+ period`
# adds, and the stages of a retirement year, which carry every field of the
# file's one inter-period mapping
RETIREMENT_COMMENT = (
    "  # retirement years: the survive branch goes straight to the tenure choice\n"
)
EXTRA_YEAR = "  - {template: period.extra_year.yml, repeat: 1}\n"
RETIREMENT_YEAR = [
    "shocks",
    "survival",
    "tenure_pa",
    "renter_cons",
    "keeper_cons_pa",
    "adjuster_cons_pa",
]


def option_text(record: dict) -> str:
    """The text a pairing list's select prints for the port record `record`
    of `trellis.connectable_ports`: the field, its set after ` : `, and the
    count of its sources where joins reach it, as `portText` writes it."""
    title = record.get("title") or ""
    sources = title[title.index(" · ") :] if " · " in title else ""
    return record["field"] + (f" : {record['set']}" if record["set"] else "") + sources


def test_task_19_a_drag_adds_to_the_pair_s_mapping_the_list_ticks_by_name_and_period_keeps_one(
    browser, server_on, tmp_path
):
    """Task 19 (defects 10, 11 and 13 of the UX simulation; L-D13; spec 0.4
    §§3.1, 3.6; K-D8, K-D23; rows K-I215 and K-I216 amended), its gestures
    the cable's since unit N's Task 7 (design pass 10 §7). On the pension
    model at its first construction whose periods[0] writes the one
    connector `{a_s: a_bq}`, the drag from `shocks`'s branch port, which
    the cable to `bequest_pa` leaves, to `bequest_pa`'s arrival port is the
    move of that cable onto its own destination: its list has one row per
    arrival field of `bequest_pa`, keeps `a_s` for `a_bq`, and `adc_s`
    chosen for `adc_bq` adds the key to that connector, the text the one
    `connector_edit` answers for the drag between the two fields and the
    note the one `removal_edit` answers for the move. With the durables
    bequest copied into periods[0] beside the pension bequest, the wire
    from `shocks` to `bequest_pa` selected and its reading end dropped on
    `bequest_dur`'s arrival port, the list has one row for each of
    `bequest_dur`'s three arrival fields, `a_bq`, `h_bq` and `z_bq`, each
    with a select over the eleven continuation fields of `shocks`, `β_s`
    among them, counts the rows paired, and names before `join` that
    `bequest_pa` loses every pair of the cable; a tick on a row with no
    field chosen puts the focus on its select and holds `join` until a
    field is chosen. `a_s`, `h_s` and `β_s` chosen by hand, `join` sends the
    whole cable's move, which releases the five pairs of the connector to
    `bequest_pa` in the same write, no equal name selecting one again, and
    writes the three chosen in its place as one entry, `{a_s:
    bequest_dur.a_bq, h_s: bequest_dur.h_bq, β_s: z_bq}`; the text and the
    note, which names the pairs released and selected and the draft the
    package reports for the route to `bequest_dur`, are those the one
    `removal_edit` answers (design pass 10 §7). On the pension model at its
    first build of the working years, `+ period` between periods[1] and
    periods[0] with a retirement year's stages writes the new entry above
    the comment over the retirement years' entry. Its uncertified standing
    mapping is left empty at the two new interfaces; the other interfaces
    keep the original mapping, with comments unchanged."""
    # a second drag between shocks and bequest_pa
    copy = pensions_copy(tmp_path / "first" / "durables")
    trellis_file = copy / PENSIONS_TRELLIS
    text = trellis_file.read_text(encoding="utf-8")
    assert text.count(BEQUEST_CONNECTOR) == 1
    one = text.replace(BEQUEST_CONNECTOR, FIRST_DRAG_CONNECTOR)
    trellis_file.write_text(one, encoding="utf-8")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    ends = (0, "shocks", "adc_s"), (0, "bequest_pa", "adc_bq")
    drag = trellis.connector_edit(shown, connected_event(shown, folder, *ends), {})
    # the note names the draft the edit leaves after the entry written (unit N, Task 7)
    assert drag.note.startswith(
        "trellis.pensions.yml, periods[0].connectors[0]: {adc_s: adc_bq} written, flat, periods 0"
    )
    (typed,) = drag.edits.values()
    assert typed == one.replace(FIRST_DRAG_CONNECTOR, "      - {a_s: a_bq, adc_s: adc_bq}\n")
    source, target = field_port(shown, "writing", ends[0]), field_port(shown, "reading", ends[1])
    writer, reader = "periods[0]/shocks", "periods[0]/bequest_pa"
    (first,) = [w for w in trellis.join_wires(shown) if (w["from"], w["to"]) == (writer, reader)]
    assert [f["field"] for f in first["fields"]] == ["a_s"], first["fields"]
    context, tab = new_tab(browser)
    try:
        # the backward graph of this model is refused (the language's gap §5 of
        # the simulation's record), so the view opens on no box
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)
        open_tree_file(tab, PENSIONS_TRELLIS)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: {source["id"], target["id"]} <= set(unjoined_field_ids(tab)),
            60.0,
            "adc_s and adc_bq unjoined",
        )
        # the drag from the joined branch port is the move of the cable onto
        # its own destination: the list keeps the pair `a_s → a_bq`
        hold_events(tab, "moved")
        drag_cable(tab, writer, "", reader)
        listed, _ = wait_until(lambda: cable_list(tab), 10.0, "the cable's list")
        rows = {row[0].split(" : ")[0]: row for row in listed["rows"]}
        assert set(rows) == {"a_bq", "adc_bq", "h_bq", "m_bq", "P_bq"}, listed
        assert rows["a_bq"][1] and rows["a_bq"][2].startswith("a_s"), listed
        assert not rows["adc_bq"][1], listed
        tab.locator(f'.bl-view-host .bf-pair-row[data-port="{target["id"]}"] select.bf-pair-from').select_option(
            value=source["id"]
        )
        ticked = [row for row in cable_list(tab)["rows"] if row[1]]
        assert cable_list(tab)["count"] == f"{len(ticked)} of 5 fields paired"
        tab.click(".bl-view-host .bf-pair-join")
        (event,) = held_events(tab, "moved")
        assert event["cable"] is True and event["end"] == "reading", event
        assert {(p["sourceHandle"], p["targetHandle"]) for p in event["pairs"]} >= {
            (first["fields"][0]["writing"], first["fields"][0]["reading"]),
            (source["id"], target["id"]),
        }, event
        move = trellis.removal_edit(shown, {**event, "reading": trellis.reading_record(folder, shown)}, {})
        assert move.sentence is None, move.sentence
        (added,) = move.edits.values()
        connector = entry_value(added, "periods[0].connectors")[0]
        assert connector.items() >= {"a_s": "a_bq", "adc_s": "adc_bq"}.items(), connector
        if len(ticked) == 2:
            assert added == typed
        release_events(tab, "moved")
        wait_until(lambda: gesture_note(tab) == move.note, 10.0, "the note of the second drag")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == added, 10.0, "the key added")
    finally:
        context.close()

    # the reading end of the wire to bequest_pa moved to the copied bequest
    copy = pensions_with_bequest_dur(tmp_path / "moved" / "durables")
    trellis_file = copy / PENSIONS_TRELLIS
    before = trellis_file.read_text(encoding="utf-8")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    dur = {
        field: field_port(shown, "reading", (0, "bequest_dur", field))["id"]
        for field in ("a_bq", "h_bq", "z_bq")
    }
    # the continuation fields of `shocks` as the list's selects offer them,
    # in the order of the region's records
    shocks_fields = [
        record for record in trellis.connectable_ports(shown, {})
        if record["side"] == "writing" and (record["h"], record["key"]) == (0, "shocks")
    ]
    options = ["—"] + [option_text(record) for record in shocks_fields]
    assert sorted(record["field"] for record in shocks_fields) == sorted(SHOCKS_ROWS)
    by_field = {record["field"]: record["id"] for record in shocks_fields}
    (wire,) = [w for w in trellis.join_wires(shown) if (w["from"], w["to"]) == (writer, reader)]
    replaced = {f["field"]: f["reading"] for f in wire["fields"]}
    pairs = [
        {"sourceHandle": by_field["a_s"], "targetHandle": dur["a_bq"], "replaced": replaced["a_s"]},
        {"sourceHandle": by_field["h_s"], "targetHandle": dur["h_bq"], "replaced": replaced["h_s"]},
        {"sourceHandle": by_field["β_s"], "targetHandle": dur["z_bq"]},
    ]
    event = {
        "reading": trellis.reading_record(folder, shown),
        "join": {name: wire[name] for name in JOIN_IDS},
        "end": "reading",
        "pairs": pairs,
        "cable": True,
    }
    move = trellis.removal_edit(shown, event, {})
    # the whole cable moves (design pass 10 §7): the five pairs of the
    # connector to bequest_pa are released in the same write, no equal name
    # selecting one again, and the three pairs chosen are written in its
    # place as one entry; the note names the pairs released and selected and
    # the draft the package reports for the route to bequest_dur
    assert move.sentence is None, move.sentence
    (moved,) = move.edits.values()
    keyed = "{a_s: bequest_dur.a_bq, h_s: bequest_dur.h_bq, β_s: z_bq}"
    assert entry_value(moved, "periods[0].connectors") == [entry_value(keyed)]
    assert move.note.startswith(
        f"trellis.pensions.yml, periods[0].connectors[0]: {keyed} written, periods 0; "
        "no longer selected: "
    ), move.note
    draft = "; draft: the route periods[0].shocks → periods[0].bequest_dur is not certified"
    assert draft in move.note, move.note
    loses = f"{reader} loses " + ", ".join(f"{f['field']}: {f['arrival']}" for f in wire["fields"])
    assert loses == "periods[0]/bequest_pa loses a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)
        open_tree_file(tab, PENSIONS_TRELLIS)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the join wire from shocks to bequest_pa",
        )
        reading = tab.evaluate(REGION_READING_JS)
        click_join(tab, writer, reader)
        hold_events(tab, "moved")
        move_join_end(tab, writer, reader, "target", cable_port(tab, "periods[0]/bequest_dur", "reading"))
        listed, _ = wait_until(lambda: cable_list(tab), 10.0, "the cable's list")
        assert listed["head"] == f"{writer} → periods[0]/bequest_dur", listed
        assert sorted(row[0].split(" : ")[0] for row in listed["rows"]) == ["a_bq", "h_bq", "z_bq"], listed
        assert all(row[3] == options for row in listed["rows"]), listed
        paired = sum(row[1] for row in listed["rows"])
        assert listed["count"] == f"{paired} of 3 fields paired" and listed["join"] == (paired > 0), listed
        assert tab.locator(".bl-view-host .bf-pair-loses").text_content() == loses
        # a tick on a row with no field chosen puts the focus on its select
        # and holds `join`
        rows = tab.locator(".bl-view-host .bf-pair-row")
        z_row = [i for i, row in enumerate(listed["rows"]) if row[0].startswith("z_bq")][0]
        assert not listed["rows"][z_row][1]
        rows.nth(z_row).locator(".bf-pair-tick").click()
        assert tab.evaluate(ROW_SELECT_FOCUSED_JS, z_row)
        assert cable_list(tab)["join"] is False
        rows.nth(z_row).locator(".bf-pair-tick").click()
        # a_s, h_s and β_s chosen by hand
        for arrival, field in (("a_bq", "a_s"), ("h_bq", "h_s"), ("z_bq", "β_s")):
            tab.locator(f'.bl-view-host .bf-pair-row[data-port="{dur[arrival]}"] select.bf-pair-from').select_option(
                value=by_field[field]
            )
        drawn = cable_list(tab)
        assert drawn["count"] == "3 of 3 fields paired" and drawn["join"], drawn
        tab.click(".bl-view-host .bf-pair-join")
        assert cable_list(tab) is None
        (held,) = held_events(tab, "moved")
        by_target = lambda pair: pair["targetHandle"]  # noqa: E731
        assert {**held, "pairs": sorted(held["pairs"], key=by_target)} == {
            **event, "reading": reading, "pairs": sorted(pairs, key=by_target)
        }, held
        release_events(tab, "moved")
        wait_until(lambda: gesture_note(tab) == move.note, 10.0, "the note of the move")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == moved, 10.0, "the move typed")
        assert trellis_file.read_text(encoding="utf-8") == before
    finally:
        context.close()

    # The uncertified mapping is not extended to either new interface.
    copy = pensions_copy(tmp_path / "added" / "durables", PENSIONS_WORKING_YEARS)
    trellis_file = copy / PENSIONS_TRELLIS
    text = trellis_file.read_text(encoding="utf-8")
    assert text.count(RETIREMENT_COMMENT) == 1
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    added = creation.add_period(
        copy,
        "extra_year",
        RETIREMENT_YEAR,
        at=1,
        recipe="spec.pensions.yml",
        standing=lambda at, keys: trellis.standing_mapping_joins(shown, at, keys, {}),
    )
    old_mapping = entry_value(text, "inter_connectors")[0]
    expected = text.replace(RETIREMENT_COMMENT, EXTRA_YEAR + RETIREMENT_COMMENT)
    mapping_line = text.split("inter_connectors:\n", 1)[1]
    expected = expected.replace(mapping_line, "  - {}\n  - {}\n" + mapping_line * 5)
    assert added.edits[str(trellis_file.resolve())] == expected
    assert entry_value(expected, "inter_connectors") == [{}, {}] + [old_mapping] * 5
    form = '.bl-form[data-form="add period"]'
    between = "between periods[1] and periods[0]"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)
        choose_view(tab, None, "forward")
        wait_until(lambda: between in add_period_controls(tab), 60.0, "the + period controls")
        drop_by_keyboard(tab, None, between)
        tab.wait_for_selector(form, timeout=30_000)
        # the form's name with its capital (design pass 8 §8 item 1; unit
        # M, Task 6)
        assert tab.locator(f"{form} h2").inner_text() == f"Add period {between}"
        tab.fill(".bl-period-label input", "extra_year")
        for key in RETIREMENT_YEAR:
            tab.click(f'{form} .bl-period-stage[data-key="{key}"]')
        tab.click(".bl-period-submit")
        wait_until(
            lambda: gesture_note(tab) == "; ".join(added.notes), 30.0, "the note of the period"
        )
        tab.wait_for_selector(form, state="detached", timeout=30_000)
        # The note precedes the new reading; wait for the inserted period.
        _, seconds = wait_until(
            lambda: (line := trellis_settled(tab, PENSIONS_RECIPE))
            and f" of {len(shown.trellis['periods']) + 1} (" in line,
            120.0,
            "the inserted period read",
        )
        print(f"task 19: the inserted period's reading settled after {seconds:.2f} s")
        tab.click(f'.bl-tab[data-path="{PENSIONS_TRELLIS}"]')
        wait_until(lambda: open_path_shown(tab) == PENSIONS_TRELLIS, 30.0, "the trellis file")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == expected, 10.0, "the period mappings written")
        assert trellis_file.read_text(encoding="utf-8") == text
    finally:
        context.close()


# The renter's stage file and settings file in the pension model of
# eighty-five periods, whose grid of cash on hand the post-doc changed at
# step 58 of the record; and, in the trellis's visible status line, the
# loop's seconds and the stages its loop bound alone (Task 20)
RENTER = "declaration/stages/renter_cons/renter_cons.bl"
RENTER_SETTINGS = "declaration/settings/renter_cons.yml"
LOOP_PART = re.compile(r" · loop (?P<seconds>\d+\.\d\d) s(?: for (?P<alone>[^·]+?))?(?: · |$)")


def test_task_20_a_setting_typed_on_85_periods_rebinds_its_stage_alone_in_under_10_s(
    browser, server_on, tmp_path
):
    """Task 20 (defect 14 of the UX simulation; L-D13; G-R81). On a copy of
    the pension model of eighty-five periods and 686 stage occurrences as
    the post-doc left it, its trellis read once, `renter_cons.bl` open as
    `periods[1] / renter_cons` and the trellis view shown: the value 35
    typed for `n_w` in the Settings tab, with Enter, reaches the page at
    rest in under 10 s, where the record measured 25 to 110 s for such an
    edit: the file holds it, and the trellis's status line, settled, names
    `renter_cons` as the stage its loop bound alone, which the first
    reading's line names nowhere. The stage's own loop has settled by then,
    as the stage view shows within five seconds. The view the page holds
    equals the view of the same files read and bound whole in this process,
    under the same restriction."""
    copy = pensions_life_cycle(tmp_path / "models" / "durables")
    context, tab = new_tab(browser)
    try:
        first = open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0, timeout=300_000)
        assert LOOP_PART.search(first)["alone"] is None, first
        open_tree_file(tab, RENTER, timeout=60_000)
        wait_until(lambda: recipe_head(tab) == "periods[1] / renter_cons", 120.0, "the renter")
        wait_until(lambda: status_settled_on(tab, RENTER), 120.0, "the loop of renter_cons.bl")
        tab.click(".bl-trellis-button")
        wait_until(lambda: trellis_settled(tab, PENSIONS_RECIPE), 120.0, "the trellis view")
        restriction = restriction_shown(tab)
        assert restriction == "periods 0–2"
        tab.click('.bl-class-tab[data-tab="Settings"]')
        named = ".bl-values-file"
        wait_until(
            lambda: tab.locator(named).count()
            and tab.locator(named).text_content() == f"writes {RENTER_SETTINGS}",
            30.0,
            "the tab naming the settings file",
        )
        cell = tab.locator('.bl-values-row[data-name="n_w"] .bl-values-value')
        assert cell.input_value() == "50"
        cell.fill("35")
        started = time.perf_counter()
        cell.press("Enter")

        def at_rest() -> re.Match | None:
            # the trellis's line settled on a reading that bound the renter
            # alone, the file holding the value typed
            line = trellis_settled(tab, PENSIONS_RECIPE)
            found = LOOP_PART.search(line) if line else None
            written = (copy / RENTER_SETTINGS).read_text(encoding="utf-8")
            if found is None or found["alone"] != "renter_cons":
                return None
            return found if entry_value(written, "settings")["n_w"] == 35 else None

        found, _ = wait_until(at_rest, 120.0, "the trellis read again for renter_cons")
        seconds = time.perf_counter() - started
        held = tab.evaluate(HELD_COLLECTION_JS)
        tab.click(".bl-stage-button")
        wait_until(lambda: status_settled_on(tab, RENTER), 5.0, "the loop of renter_cons.bl")
        print(f"task 20: at rest {seconds:.2f} s after Enter, the loop {found['seconds']} s")
        assert seconds < 10.0, (seconds, found.group())
        assert cell.input_value() == "35"

        # the view of the same files read and bound whole
        expected = trellis.show_trellis(
            model.open_folder(copy),
            recipe.Source("recipe", PENSIONS_RECIPE),
            trellis.parse_restriction(restriction),
        )
        assert expected.shown.alone == ()
        assert as_json(held["graphs"]) == as_json(expected.shown.collection["graphs"])
    finally:
        context.close()


# The pension model at step 19 of the UX simulation's record, its first
# reading (Task 21): the entries that join the stages, the connector of
# periods[0], that of the period file and the one inter-period mapping,
# each written `{}` as the post-doc first wrote them (the record's
# `texts/19-period.pensions-v1.yml` and `texts/20-trellis.pensions-v1.yml`),
# the recipe's sources all slots; the forward graph then marks 148 ports
# unjoined, of which the checklist lists 25 fields (defect 20). The address
# of the recipe's slot for the calibration of `shocks`, its button `New
# file` in the Recipe tab (unit M, Task 10).
STEP_19_JOINS = re.compile(r"^(\s*- )\{(?:a_s|a_sv|a_nxt_rt): .+\}$", re.MULTILINE)
STEP_19_FIELDS = 25
SHOCKS_CALIBRATION_SLOT = "stages.shocks.calibration.all[0]"
SHOCKS_NEW_FILE = (
    f'.bl-recipe-row[data-stage="shocks"] .bl-new-file[data-address="{SHOCKS_CALIBRATION_SLOT}"]'
)
# the count of the status line's part and that of the checklist's head
STATUS_FIELDS = re.compile(r" · (\d+) unjoined internal entry fields?\b")
HEAD_FIELDS = re.compile(r"(\d+) fields? unjoined\b")
# each row of a value tab whose input is marked, by its name, with the
# input's hover
MARKED_ROWS_JS = r"""
() => Object.fromEntries(Array.from(
  document.querySelectorAll('.bl-values-row .bl-values-value.bl-refusal-mark'),
  (input) => [input.closest('.bl-values-row').dataset.name, input.getAttribute('title')]))
"""


def unjoined_counts(tab) -> tuple[int, int] | None:
    """The number of unjoined fields that the trellis's status line counts
    and that the checklist's head counts, read at one moment once both
    print one; None before."""
    line = status_text(tab)
    group = tab.locator(".bl-problem-unjoined")
    found = STATUS_FIELDS.search(line)
    return (int(found[1]), int(group.get_attribute("data-count"))) if found and group.count() else None


def test_task_21_a_refusal_stands_once_no_slot_is_one_and_the_counts_of_unjoined_fields_agree(
    browser, server_on, tmp_path
):
    """Task 21 (defects 17, 18 and 20 of the UX simulation; L-D13; K-D10,
    K-D29; A2-D13). On a copy of the pension model at its first reading,
    step 19 of the record, every source of the recipe a slot and every join
    written `{}`, the trellis's status line and the checklist's head count
    the same 25 unjoined fields, where the record read 148 and 25, and the
    list under the error mark holds no error, where the record listed three
    lines about the sources no occurrence names, since a slot is no refusal
    (the open continuation fields of the branches stand in the list as
    items to review, under `Connections to check`, since the Workbench
    interface review of 4 November 2026, item 3).
    `New file` beside the slot of the calibration of `shocks` in the Recipe
    tab (unit M, Task 10), shocks' row opened by a click (design pass 11
    §2), writes `calibration: {}` and names it in the recipe's text, which
    is saved; with `shocks.bl` then
    bound as `periods[0] / shocks` and its Parameters tab writing that
    file, no line about the calibration source stands. The first value the
    post-doc typed, `R`, written by the tab (step 30), leaves the next
    parameter with no value, which the package refuses in the stage's
    binding and in the trellis's alike: the list under the error mark holds
    that refusal alone, once, with its affected occurrence, `shocks` at
    period 0; the sentence is also the marked row's hover. Back in the trellis view the status line and the checklist's
    head still count the same 25 fields, the head counting the binding
    refused."""
    copy = pensions_copy(tmp_path / "models" / "durables")
    for name in ("declaration/period.pensions.yml", PENSIONS_TRELLIS):
        text = (copy / name).read_text(encoding="utf-8")
        assert len(STEP_19_JOINS.findall(text)) == (1 if "period." in name else 2)
        (copy / name).write_text(STEP_19_JOINS.sub(r"\1{}", text), encoding="utf-8")

    def about_a_source() -> list:
        # the lines under the error mark that are about a binding source
        return [line for line in error_lines(tab) if " source" in line[0]]

    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PENSIONS_RECIPE, minimum=0)
        counts, _ = wait_until(lambda: unjoined_counts(tab), 60.0, "the two counts")
        print(f"task 21: the first reading counts {counts}, the list holds {error_lines(tab)}")
        assert counts == (STEP_19_FIELDS, STEP_19_FIELDS)
        assert error_group_lines(tab, "Errors") == []

        # `New file` in the slot's place, shocks' row opened by a click
        # (design pass 11 §2), the file opened in the editor, its name
        # written in the recipe's text, which is then saved
        open_recipe_row(tab, "shocks")
        tab.click(SHOCKS_NEW_FILE)
        wait_until(lambda: open_path_shown(tab) == SHOCKS_CALIBRATION, 30.0, "the new file open")
        assert (copy / SHOCKS_CALIBRATION).read_text(encoding="utf-8") == "calibration: {}\n"
        tab.click(f'.bl-tab[data-path="{PENSIONS_RECIPE}"]')
        wait_until(lambda: open_path_shown(tab) == PENSIONS_RECIPE, 30.0, "the recipe open")
        wait_until(
            lambda: entry_value(tab.evaluate(DOCUMENT_JS), SHOCKS_CALIBRATION_SLOT)
            == "calibration/shocks",
            30.0,
            "the slot's file in the recipe's text",
        )
        tab.click(".bl-save")
        wait_until(
            lambda: entry_value(
                (copy / PENSIONS_RECIPE).read_text(encoding="utf-8"), SHOCKS_CALIBRATION_SLOT
            )
            == "calibration/shocks",
            30.0,
            "the recipe saved",
        )

        # shocks.bl bound through the filled slot
        reveal_in_tree(tab, SHOCKS)
        tab.click(f'.bl-tree-file[data-path="{SHOCKS}"]')
        wait_until(lambda: recipe_head(tab) == "periods[0] / shocks", 120.0, "shocks bound")
        wait_until(lambda: status_settled_on(tab, SHOCKS), 120.0, "the loop of shocks.bl")
        tab.click('.bl-class-tab[data-tab="Parameters"]')
        named = ".bl-values-file"
        wait_until(
            lambda: tab.locator(named).count()
            and tab.locator(named).text_content() == f"writes {SHOCKS_CALIBRATION}",
            30.0,
            "the tab naming the calibration file",
        )
        assert about_a_source() == [], error_lines(tab)

        # the first value typed: the package refuses the next parameter with
        # no value, in the stage's binding and in the trellis's
        cell = tab.locator('.bl-values-row[data-name="R"] .bl-values-value')
        cell.fill(SHOCKS_VALUES[0][1])
        cell.press("Enter")

        def refused_once() -> tuple | None:
            # The refusal and its occurrence stand separately on one line.
            lines = error_lines(tab)
            marked = tab.evaluate(MARKED_ROWS_JS)
            named = [line for line in lines if line[0] in marked.values()]
            occurrences = tab.locator(".bl-error-occurrences").all_text_contents()
            if len(named) != 1 or "shocks at period 0" not in occurrences:
                return None
            return lines, named[0][0], marked

        (lines, sentence, marked), _ = wait_until(refused_once, 180.0, "the binding refused")
        print(f"task 21: the list after R is typed: {lines}; the rows marked: {marked}")
        refusal = trellis.show_trellis(
            model.open_folder(copy), recipe.Source("recipe", PENSIONS_RECIPE)
        ).shown.binding.failed["calibrate"]
        assert refusal.occurrences == ((0, "shocks"),)
        assert model.sentence(refusal).replace(str(copy.resolve()) + "/", "") == sentence
        assert "stage 'shocks', parameter " in sentence
        assert [line[0] for line in lines].count(sentence) == 1
        assert error_group_lines(tab, "Errors") == [(sentence, SHOCKS_CALIBRATION, 1)]

        # the trellis view: the counts agree, the head counting the refusal
        tab.click(".bl-trellis-button")
        wait_until(lambda: trellis_settled(tab, PENSIONS_RECIPE), 120.0, "the trellis view")
        counts, _ = wait_until(lambda: unjoined_counts(tab), 60.0, "the two counts again")
        assert counts == (STEP_19_FIELDS, STEP_19_FIELDS)
        assert len(tab.locator('.bl-error-line[data-severity="error"]').all()) == 1
        assert tab.locator(".bl-folder .bl-checklist").count() == 0
    finally:
        context.close()


# The working year the post-doc of the UX simulation restricted the trellis
# to, a period of nine stage occurrences (Task 22; defect 21), and its layer.
PERIOD_ALONE = "periods[40]"
PERIOD_ALONE_LAYER = f"{PERIOD_ALONE}{LAYER_ID_ENDING}"
SHOCKS_STAGE = "declaration/stages/shocks/shocks.bl"
# the sets of shocks.bl that the record printed `[0…` and `(0…` in the
# Fields tab with Matsya's column open at 1600 px (defect 25)
UNIT_INTERVALS = {"[0, 1]", "(0, 1)"}
# each set box of the Fields tab: its set, the widths of its text area and
# of its text, its hover and its text-overflow
SET_BOXES_JS = r"""
() => Array.from(document.querySelectorAll('.bl-class-tables .bl-class-set'), (box) => ({
  set: box.value, box: box.clientWidth, text: box.scrollWidth, hover: box.title,
  overflow: getComputedStyle(box).textOverflow}))
"""
# the editor beside its minimap: the minimap's left edge, the right edges of
# the scroller, of the content and of each annotation drawn, the width by
# which the content runs past the scroller, and the scroller's place and
# its end, in pixels
EDITOR_BESIDE_MINIMAP_JS = r"""
() => {
  const editor = document.querySelector('.bl-editor .cm-editor');
  const scroller = editor.querySelector('.cm-scroller');
  return {strip: editor.querySelector('.bl-minimap').getBoundingClientRect().left,
          scroller: scroller.getBoundingClientRect().right,
          content: editor.querySelector('.cm-content').getBoundingClientRect().right,
          beyond: scroller.scrollWidth - scroller.clientWidth,
          annotations: Array.from(editor.querySelectorAll('.bl-annotation'),
                                  (annotation) => annotation.getBoundingClientRect().right),
          top: scroller.scrollTop, end: scroller.scrollHeight - scroller.clientHeight};
}
"""
SCROLL_EDITOR_JS = (
    "(top) => { document.querySelector('.bl-editor .cm-scroller').scrollTop = top; }"
)
OPEN_LAYERS_JS = "() => document.querySelector('.bl-view-host').bellmanFlow.openLayers()"
FOLDER_TOGGLE = '.bl-main-bar .bl-fold[data-fold="folder"]'


def opened_alone(tab, occurrences: set[str], what: str) -> dict:
    """Waits until the region shows the period PERIOD_ALONE alone as it
    opens: its layer and the layers of `occurrences` open, the viewport
    the opening of its layer, the graph's terminal period
    (`period_opening`, as AAS's M-D15 amends Task 22), to one screen pixel,
    and the period's name drawn within the region; answers the viewport
    with the layer's place."""
    found = {}

    def opened() -> bool:
        view = viewport(tab)
        nodes = tab.evaluate(DRAWN_PLACES_JS)["nodes"]
        place = nodes.get(PERIOD_ALONE_LAYER)
        seen = tab.evaluate(LAYER_IN_REGION_JS, PERIOD_ALONE_LAYER)
        open_layers = set(tab.evaluate(OPEN_LAYERS_JS))
        found.update(view=view, place=place, open=sorted(open_layers))
        if view is None or place is None or seen is None:
            return False
        at = {"ax": place["x"], "ay": place["y"], "width": place["width"]}
        at["height"] = place["height"]
        expected = period_opening(view, at, drawn_extent(nodes))
        name, host = seen["name"], seen["host"]
        return (
            {PERIOD_ALONE, *occurrences} <= open_layers
            and abs(view["x"] - expected["x"]) <= 1
            and abs(view["y"] - expected["y"]) <= 1
            and abs(view["zoom"] - expected["zoom"]) < 1e-6
            and seen["text"] == PERIOD_ALONE
            and seen["drawn"]
            and all(name[side] >= host[side] - 1 for side in ("left", "top"))
        )

    try:
        wait_until(opened, 30.0, what)
    except AssertionError:
        raise AssertionError((what, found)) from None
    return found


def editor_text_within_the_scroller(tab) -> int:
    """Scrolls the editor from its first line to its last, one screen at a
    time, asserting at each place that the content runs no wider than the
    scroller, which ends at the minimap's left edge, and that no annotation
    drawn stands under the minimap; answers the number of annotations
    read."""
    read = 0
    top = 0
    while True:
        tab.evaluate(SCROLL_EDITOR_JS, top)
        tab.evaluate(TWO_FRAMES_JS)
        found = tab.evaluate(EDITOR_BESIDE_MINIMAP_JS)
        assert found["scroller"] <= found["strip"] + 0.5, found
        assert found["beyond"] <= 0 and found["content"] <= found["scroller"] + 0.5, found
        assert all(right <= found["strip"] + 0.5 for right in found["annotations"]), found
        read += len(found["annotations"])
        if found["top"] >= found["end"]:
            return read
        top = found["top"] + 300


def test_task_22_a_period_alone_opens_on_its_layer_and_a_tree_name_is_cut_after_a_whole_word(
    browser, server_on, tmp_path
):
    """Task 22 (defects 21, 23, 24 and 25 of the UX simulation; L-D13; K-D22;
    L-D4; as AAS's M-D15 amends the opening). On a copy of the pension model
    of eighty-five periods as the post-doc left it, its trellis read:
    restricted to `periods 40`, the forward graph shows that working year
    alone with the layers of its nine stage occurrences open, at the largest
    scale, at most 1 and at least the reading scale 0.6, at which the
    period's layer fills the region less 10 px at each side, the layer
    moved toward the graph's nearer end as far as it stays within the
    region, and otherwise with its top left corner, which holds its name,
    10 px inside the region's (`period_opening`): at 1600, where the layer
    fills the region at a scale between 0.6 and 1, and, the window
    narrowed, at 1280 × 1000, the backward graph instead states the native refusal because this historical model lacks derivative correspondence. Then, on shocks.bl with Matsya's column open
    at 1600: the Fields tab prints the sets [0, 1] and (0, 1) whole, and a
    set its column cannot hold, [-inf, inf), is cut with an ellipsis and
    whole in its hover; the editor's content is never wider than its
    scroller, which ends at the minimap's left edge, so that no annotation
    stands under the minimap, at 1600 and 1280; and with every folder of
    the tree open and shocks.bl unsaved, no name of the tree is cut within
    a word, `declaration` whole, without the slash (design pass 8 §8 item
    9; unit M, Task 6), and the open file printing `shocks`, at
    the folder's default width of 170 px, its least width (R-D14), and with
    the folder opened by the main bar's toggle `Files` at 1280 (unit N,
    Task 1)."""
    copy = pensions_life_cycle(tmp_path / "models" / "durables")
    url = server_on(copy)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, url, PENSIONS_RECIPE, minimum=0, timeout=300_000)
        choose_view(tab, None, "forward")
        restrict(tab, "periods 40")
        wait_until(
            lambda: "shown periods 40 of 85 (9 occurrences)"
            in (trellis_settled(tab, PENSIONS_RECIPE) or ""),
            120.0,
            "the trellis restricted to periods 40",
        )
        forward = graph_named(tab.evaluate(HELD_COLLECTION_JS), "forward")
        occurrences = {
            "/".join(node["namespace"].split("/")[:2])
            for node in forward["nodes"]
            if node.get("namespace", "").startswith(f"{PERIOD_ALONE}/")
        }
        assert len(occurrences) == 9, occurrences
        found = opened_alone(tab, occurrences, "periods 40 alone, forward, at 1600")
        print(f"task 22: periods 40 alone at 1600 {found['view']}, its layer {found['place']}")
        zoom = found["view"]["zoom"]
        assert READING_SCALE < zoom < 1, found
        assert abs(found["place"]["width"] * zoom - (found["view"]["width"] - 20)) <= 1, found
        wide = found["view"]["width"]
        tab.set_viewport_size({"width": 1280, "height": 1000})
        wait_until(lambda: viewport(tab)["width"] < wide, 5.0, "the region narrowed at 1280")
        found = opened_alone(tab, occurrences, "periods 40 alone, forward, at 1280")
        print(f"task 22: periods 40 alone at 1280 {found['view']}")
        choose_view(tab, None, "backward")
        backward = graph_named(tab.evaluate(HELD_COLLECTION_JS), "backward")
        (refusal,) = backward["nodes"]
        assert refusal["id"] == "backward:refused"
        message = next(item["value"] for item in refusal["attrs"] if item["key"] == "refusal")
        assert "pairs the marginal values" in message and "coordinate map" in message
        wait_until(lambda: tab.locator('.react-flow__node[data-id="backward:refused"]').count() == 1,
                   15.0, "the native refusal of the incomplete pension backward graph")
    finally:
        context.close()

    context, tab = new_tab(browser)
    try:
        open_file(tab, url, SHOCKS_STAGE, timeout=120_000)
        assert tracks_near(tab, FRAME_TRACKS[1600, False]), tracks(tab)
        boxes_of = {}
        for found in tab.evaluate(SET_BOXES_JS):
            boxes_of.setdefault(found["set"], []).append(found)
        assert UNIT_INTERVALS <= set(boxes_of), sorted(boxes_of)
        for name in UNIT_INTERVALS:
            assert all(found["text"] <= found["box"] for found in boxes_of[name]), boxes_of[name]
        assert all(found["text"] > found["box"] for found in boxes_of["[-inf, inf)"])
        for found in boxes_of["[-inf, inf)"]:
            assert (found["overflow"], found["hover"]) == ("ellipsis", "[-inf, inf)"), found
        widths = [(found["text"], found["box"]) for found in boxes_of["[0, 1]"]]
        print(f"task 22: [0, 1] in its boxes {widths}")

        assert editor_text_within_the_scroller(tab) > 0
        open_every_folder(tab)
        click_line(tab, 2)
        tab.keyboard.type(" ")
        wait_until(lambda: SHOCKS_STAGE in unsaved_in_tree(tab), 10.0, "shocks.bl unsaved")
        for width in (1600, 1280):
            tab.set_viewport_size({"width": width, "height": 1000})
            if width == 1280:
                wait_until(lambda: abs(tracks(tab)[0] - 48) <= 1, 5.0, "the folder folded at 1280")
                tab.click(FOLDER_TOGGLE)
                assert editor_text_within_the_scroller(tab) > 0
            wait_until(lambda: abs(tracks(tab)[0] - 170) <= 1, 5.0, f"the folder at {width}")
            names = tree_names(tab)
            faults = [name for name in names if cut_within_a_word(name)]
            assert names and faults == [], faults
            named = {name["path"]: name for name in names}
            assert named["declaration"]["shown"] == "declaration", named["declaration"]
            assert named[SHOCKS_STAGE]["shown"].startswith("shocks"), named[SHOCKS_STAGE]
            cut = [name["name"] for name in names if name["cut"]]
            shocks = named[SHOCKS_STAGE]
            print(f"task 22: at {width} the open file {shocks}, {len(cut)} names cut: {cut}")
    finally:
        context.close()


# The form open over the window as design pass 4 measures it (Task 23; AAS,
# L-D14, L-D15), null where none is open: its data-form, whether it is
# wide, `.bl-form-wide`, its width and its opening animation's name and
# duration; its head, as its height, its icon, the number of lines its
# heading stands on, the faces of its name and of its context, `null`
# where it has none, the context's text, and its last element, `×`, as its
# accessible name, its icon and its size; its note, as its lines, its face,
# its text and its hover; every text of the form, each text node's words
# and each hover; each box a reader sees as one thing, a line, a field's
# box, a button or a row, that measures more than 30 px high outside a
# list or a text area; the height of each field's box but a text area's;
# the height of each row of a list; its refusal, as its lines, its face,
# its text, its hover and the classes of the element before it; its foot,
# as whether `cancel` stands first and the primary last, the distance from
# the primary's right edge to the content's right edge and the buttons'
# heights; and each icon as its name, its grid, its size and its stroke.
# A face is the first family, the size and the color.
FORM_MEASURES_JS = r"""
() => {
  const form = document.querySelector('.bl-forms .bl-form');
  if (!form) return null;
  const box = (element) => element.getBoundingClientRect();
  const style = getComputedStyle(form);
  const right = box(form).right - parseFloat(style.borderRightWidth)
    - parseFloat(style.paddingRight);
  const face = (element) => {
    const drawn = getComputedStyle(element);
    return [drawn.fontFamily.split(',')[0].replace(/"/g, ''), drawn.fontSize, drawn.color];
  };
  // the number of lines the texts of an element stand on: its texts' boxes
  // in the order of their tops, a box that begins below the lowest bottom of
  // the line before beginning a new line, so that texts of two sizes on one
  // baseline count as one line
  const lines = (element) => {
    const rects = [];
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const range = document.createRange();
      range.selectNodeContents(node);
      for (const rect of range.getClientRects()) {
        if (rect.width > 0) rects.push(rect);
      }
    }
    rects.sort((a, b) => a.top - b.top);
    let count = 0, bottom = -Infinity;
    for (const rect of rects) {
      if (rect.top >= bottom - 0.5) count += 1;
      bottom = rect.top >= bottom - 0.5 ? rect.bottom : Math.max(bottom, rect.bottom);
    }
    return count;
  };
  const head = form.querySelector('.bl-form-head');
  const close = head.lastElementChild;
  const context = head.querySelector('.bl-form-context');
  const note = form.querySelector('.bl-form-top > .bl-form-note');
  const texts = [];
  const walker = document.createTreeWalker(form, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) texts.push(node.data);
  form.querySelectorAll('[title]').forEach((element) => texts.push(element.getAttribute('title')));
  const seen = '.bl-form-head, .bl-form-note, .bl-form-label, .bl-form-error, vscode-textfield, '
    + 'vscode-single-select, vscode-button, button, .bl-form-list-head, .bl-template-refused, '
    + 'li.bl-list-item';
  const tall = Array.from(form.querySelectorAll(seen))
    .filter((element) => element.getClientRects().length > 0)
    .filter((element) => box(element).height > 30.5)
    .map((element) => [String(element.className), box(element).height]);
  const refusal = form.querySelector('.bl-form-error');
  const before = refusal && refusal.previousElementSibling;
  const foot = form.querySelector('.bl-form-buttons');
  const primary = foot.lastElementChild;
  return {
    form: form.dataset.form,
    wide: form.matches('.bl-form-wide'),
    width: box(form).width,
    animation: [style.animationName, style.animationDuration],
    head: {
      height: box(head).height,
      icon: Array.from(head.firstElementChild.classList)
        .find((name) => name.startsWith('codicon-')).slice('codicon-'.length),
      heading: lines(head.querySelector('h2')),
      name: face(head.querySelector('h2')),
      context: context && face(context),
      contextText: context && context.textContent,
      close: [close.label, close.getAttribute('icon'), box(close).width, box(close).height],
    },
    note: note && {lines: lines(note), face: face(note), text: note.textContent,
                   title: note.getAttribute('title')},
    texts,
    tall,
    fields: Array.from(form.querySelectorAll('vscode-textfield, vscode-single-select'),
      (field) => box(field).height),
    rows: Array.from(form.querySelectorAll('.bl-form-list .bl-list-item'),
      (row) => box(row).height),
    refusal: refusal && {lines: lines(refusal), face: face(refusal), text: refusal.textContent,
      title: refusal.getAttribute('title'), after: before && String(before.className)},
    foot: {
      cancelFirst: foot.firstElementChild.matches('.bl-form-cancel'),
      primaryLast: primary.matches('.bl-primary'),
      right: Math.round((right - box(primary).right) * 10) / 10,
      heights: Array.from(foot.children, (button) => box(button).height),
    },
    svgs: form.querySelectorAll('svg').length,
    icons: Array.from(form.querySelectorAll('.codicon'), (icon) => [
      Array.from(icon.classList).find((name) => name.startsWith('codicon-'))
        .slice('codicon-'.length),
      getComputedStyle(icon).fontFamily, parseFloat(getComputedStyle(icon).fontSize)]),
  };
}
"""
# The head of the list over the graph the selector names, null where none is
# drawn (Task 23; design pass 4 §4): its height, its icon, its name, its
# context, null where it has none, and its last element's accessible name;
# the heights of its items or rows; and, for a list with a foot, whether
# `cancel` stands first and `join` last.
LIST_MEASURES_JS = r"""
(selector) => {
  const list = document.querySelector(selector);
  if (!list) return null;
  const head = list.querySelector(':scope > .bf-list-head');
  const context = head.querySelector('.bf-stage-period, .bf-pair-head');
  const foot = list.querySelector(':scope > .bf-list-foot');
  return {
    height: head.getBoundingClientRect().height,
    icon: Array.from(head.firstElementChild.classList)
      .find((name) => name.startsWith('codicon-')).slice('codicon-'.length),
    name: head.querySelector('.bf-list-name').textContent,
    context: context && context.textContent,
    close: head.lastElementChild.getAttribute('aria-label'),
    rows: Array.from(list.querySelectorAll('.bf-stage-item, .bf-pair-row'),
      (row) => row.getBoundingClientRect().height),
    foot: foot && [foot.firstElementChild.className, foot.lastElementChild.className],
  };
}
"""
# An absolute path a text of a form might print (K-D11): a slash at the
# text's start or after a space, a quotation mark, a bracket or `=`, and two
# names or more, each after a slash
ABSOLUTE_PATH = re.compile(r"(?<![^\s'\"`(\[{=])(?:/[^\s'\"`,;()\[\]{}<>/]+){2,}")
# Each form's head as design pass 4 §3 draws it, in the Codicons of design
# pass 8 §3 (unit M, Task 6): its icon and its context
FORM_HEADS = {
    "new trellis": ("new-folder", None),
    "new variant": ("versions", "of spec.yml"),
    "new stage": ("new-file", None),
    "add stage": ("symbol-structure", "from a template"),
    "from a folder": ("symbol-structure", "from a folder"),
    "add period": ("split-horizontal", None),
    "commit": ("git-commit", "on {branch}"),
}
# the forms 560 px wide, which hold a chooser or the templates with their keys
WIDE_FORMS = {"new trellis", "from a folder"}


def test_task_23_the_forms_and_the_lists_measure_as_design_pass_4_draws_them(
    browser, server_on, scratch_durables
):
    """Task 23 (AAS, L-D14, L-D15; design pass 4 §§2 to 5; K-D11; spec 0.4
    §5.8's contrast). On a copy of the durables model, `periods 0–2`, its
    forward trellis graph shown, each form of the page opened in turn from
    its control and closed, by `×`, by `cancel` or by Escape: each `.bl-form`
    opens in a fade of 120 ms and is at least 360 and at most 440 px wide,
    560 for `new trellis` and the form from a folder; its head is one line
    of 28 px, its icon the Codicon of its kind (design pass 8 §3; unit M,
    Task 6) and its context as §3 names it, the name in Head, Archivo at
    13 px, and the context in Code small, IBM Plex Mono at 11 px in ice-2,
    and the icon button `close` last, a 24 px target named `Close`; its
    note one line at 11 px in the prose face in ice-3, whole in its hover;
    no box a reader sees as one thing stands higher than 30 px but a list
    or the commit's text area, each field VSCode Elements' at 26 px; no
    text and no hover of the form prints an absolute path; `Cancel` stands
    first in the foot and the primary last at its right edge, each 26 px;
    the templates and the chooser are lists of 24-px rows; every icon is a
    Codicon at 16 px, and the form draws no SVG. In `new trellis` the name and
    the
    number of periods share one row and `write the folder` names in its
    hover what it waits for; the templates of `add stage` are a choice of
    one and the stages of `add period` checkboxes, and ArrowDown moves the
    focus to the next row; in `new stage` the primary modifier with Enter
    presses `write the stage`, whose refusal for a held key stands in one
    line in orange under the key's field, whole in its hover, and nothing
    is written. The stage list's head and the pairing list's are 28 px with
    their icon, name, context and `×`, each item of the stage list 26 px
    (unit N, Task 5; design pass 10 §7) and each row of the pairing list 24
    px, and the pairing list's foot holds `cancel` then `join`; the pairing
    list is the cable's list that the move of a join wire's reading end onto
    `bequest`'s arrival port opens (design pass 10 §7). With each panel open,
    no text under the window falls below its contrast bound."""
    copy = scratch_durables
    writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
    add_stage = (
        f'.bl-view-host .react-flow__node[data-id="periods[0]{LAYER_ID_ENDING}"]'
        " > .bf-layer > .bf-add-stage"
    )
    branch = git(copy, "symbolic-ref", "--short", "HEAD").strip()
    before = file_bytes(copy)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.locator(add_stage).count() == 1, 60.0, "+ stage of periods[0]")
        ice, ice_2, ice_3 = (
            property_color(tab, name) for name in ("--bl-ice", "--bl-ice-2", "--bl-ice-3")
        )
        orange = property_color(tab, "--bl-orange")
        for number, form in enumerate(PAGE_FORMS):
            selector = open_page_form(tab, form)
            if form in ("new trellis", "add stage"):
                tab.locator(f"{selector} .bl-template-button").first.click()
                tab.wait_for_selector(f"{selector} .bl-create-key")
            elif form == "new stage":
                # the key's field drawn before the form is measured, as the
                # key field of a chosen template is above; the form's element
                # can stand a moment before its field
                tab.wait_for_selector(f"{selector} .bl-new-stage-key vscode-textfield")
            elif form == "from a folder":
                field = f"{selector} .bl-folder-path input"
                tab.fill(field, str(PORT_FOLDER))
                tab.press(field, "Enter")
                tab.wait_for_selector(f'{selector} .bl-template[data-template="{PORT_FOLDER}"]')
                tab.wait_for_selector(f"{selector} .bl-create-key")
            found = tab.evaluate(FORM_MEASURES_JS)
            icon, expected_context = FORM_HEADS[form]
            assert found["wide"] == (form in WIDE_FORMS), form
            assert 360 <= found["width"] <= (560 if found["wide"] else 440), (form, found["width"])
            assert found["animation"] == ["bl-panel-in", "0.12s"], form
            drawn_head = found["head"]
            assert (drawn_head["height"], drawn_head["icon"], drawn_head["heading"]) == (
                28,
                icon,
                1,
            ), (form, drawn_head)
            assert drawn_head["name"] == ["Archivo", "13px", ice], (form, drawn_head)
            if expected_context is None:
                assert drawn_head["context"] is None, (form, drawn_head)
            else:
                assert drawn_head["contextText"] == expected_context.format(branch=branch), form
                assert drawn_head["context"] == ["IBM Plex Mono", "11px", ice_2], form
            assert drawn_head["close"] == ["Close", "close", 24, 24], (form, drawn_head)
            note = found["note"]
            assert (note["lines"], note["face"]) == (1, ["Archivo", "11px", ice_3]), (form, note)
            assert note["title"] == note["text"], (form, note)
            assert found["tall"] == [], (form, found["tall"])
            # every form holds a field, the commit's its text area alone
            assert (form == "commit") != bool(found["fields"]), form
            assert set(found["fields"]) <= {26}, (form, found["fields"])
            printed = [text for text in found["texts"] if ABSOLUTE_PATH.search(text)]
            assert printed == [], (form, printed)
            assert found["foot"]["cancelFirst"] and found["foot"]["primaryLast"], form
            assert found["foot"]["right"] == 0 and set(found["foot"]["heights"]) == {26}, form
            assert set(found["rows"]) <= {24}, (form, found["rows"])
            assert found["svgs"] == 0, form
            for name, face, size in found["icons"]:
                assert name in icons.CODICONS.values(), (form, name)
                assert (face, size) == ("codicon", 16), (form, name)
            assert contrast_faults(tab, CONTRAST_EXCEPTIONS) == [], form

            # what each form holds beside the measures
            if form == "new trellis":
                name_box = boxes(tab, f"{selector} .bl-field.bl-create-name")[0]
                periods_box = boxes(tab, f"{selector} .bl-field.bl-create-repeat")[0]
                assert name_box["top"] == periods_box["top"], (name_box, periods_box)
                assert periods_box["width"] < name_box["width"] / 3, periods_box
                tab.locator(f"{selector} .bl-template-button").first.click()
                submit = tab.locator(f"{selector} .bl-create-submit")
                wait_until(lambda: submit.get_attribute("title") == "type a name", 5.0, "hover")
                assert submit.is_disabled()
            elif form == "add stage":
                rows = tab.locator(f"{selector} .bl-template-button")
                assert {rows.nth(n).get_attribute("role") for n in range(rows.count())} == {
                    "radio"
                }
                rows.first.focus()
                tab.keyboard.press("ArrowDown")
                assert tab.evaluate(
                    "() => document.activeElement === document.querySelectorAll("
                    "'.bl-form .bl-template-button')[1]"
                )
            elif form == "add period":
                checks = tab.locator(f"{selector} .bl-period-stage")
                assert checks.count() == len(creation.recipe_keys(copy))
                assert {checks.nth(n).get_attribute("role") for n in range(checks.count())} == {
                    "checkbox"
                }
            elif form == "new stage":
                tab.fill(f"{selector} .bl-new-stage-key input", "tenure")
                # the key typed, the primary acts, and the keys press it
                submit = tab.locator(f"{selector} .bl-new-stage-submit")
                wait_until(lambda: submit.is_enabled(), 10.0, "write the stage acting")
                tab.keyboard.press("ControlOrMeta+Enter")
                tab.wait_for_selector(f"{selector} .bl-form-error", timeout=10_000)
                refusal = tab.evaluate(FORM_MEASURES_JS)["refusal"]
                assert refusal["text"] == refusal["title"] == "declaration/stages/tenure/ exists"
                assert (refusal["lines"], refusal["face"]) == (1, ["Archivo", "11px", orange])
                assert "bl-new-stage-key" in refusal["after"].split()
                assert file_bytes(copy) == before
            elif form == "commit":
                message = boxes(tab, f"{selector} .bl-commit-message vscode-textarea")[0]
                assert message["height"] >= 2 * 17.9, message

            # closed by `×`, by `cancel` or by Escape in turn
            if number % 3 == 0:
                tab.click(f"{selector} .bl-form-close")
            elif number % 3 == 1:
                tab.click(f"{selector} .bl-form-cancel")
            else:
                tab.keyboard.press("Escape")
            tab.wait_for_selector(".bl-form", state="detached")

        # the stage list opened by `stages` and by `+ stage` of periods[0]
        stage_list = ".bl-view-host .bf-stage-list"
        for opener, period in ((".bl-stages-button", None), (add_stage, "periods[0]")):
            tab.click(opener)
            tab.wait_for_selector(f"{stage_list} .bf-stage-item", timeout=10_000)
            listed = tab.evaluate(LIST_MEASURES_JS, stage_list)
            assert (listed["height"], listed["icon"], listed["name"]) == (
                28,
                "symbol-structure",
                "Stages",
            )
            assert (listed["context"], listed["close"]) == (period, "close"), listed
            assert listed["rows"] and set(listed["rows"]) == {26}, listed["rows"]
            assert contrast_faults(tab, CONTRAST_EXCEPTIONS) == [], opener
            tab.keyboard.press("Escape")
            tab.wait_for_selector(stage_list, state="detached")

        # the cable's list of the move of a join wire's reading end, closed by
        # cancel: the end is dropped on `bequest`'s arrival port, since design
        # pass 10 §6 took the per-field port `a_bq` off the cards (§7)
        hold_events(tab, "moved")
        click_join(tab, writer, reader)
        arrival = cable_port(tab, "periods[0]/bequest", "reading")
        move_join_end(tab, writer, reader, "target", arrival)
        pair_list = ".bl-view-host .bf-pair-list"
        tab.wait_for_selector(pair_list, timeout=10_000)
        listed = tab.evaluate(LIST_MEASURES_JS, pair_list)
        # the list's name in sentence case, as `Stages` (the fix wave Q3b of
        # unit Q, item 19; C12)
        assert (listed["height"], listed["icon"], listed["name"]) == (28, "link", "Join")
        assert listed["context"] == "periods[1]/keeper_cons → periods[0]/bequest", listed
        assert set(listed["rows"]) == {24} and listed["foot"] == ["bf-pair-cancel", "bf-pair-join"]
        assert contrast_faults(tab, CONTRAST_EXCEPTIONS) == []
        tab.click(f"{pair_list} .bf-pair-cancel")
        tab.wait_for_selector(pair_list, state="detached")
        assert release_events(tab, "moved") == []
    finally:
        context.close()


# A stage occurrence's card whose layer id is given, null where none is
# drawn (AAS, L-D16 and L-D25; design pass 7 §3): its size at scale 1 and
# its box on the screen; the box of its name; the glyph its chevron draws;
# each printed text, its classes, its text and its box; every non-empty text
# node in the card's element; each port's mark, its center on the screen,
# its computed radius and whether it is drawn as a hollow mark; and each
# builder's segment, from left to right, its id, its box on the screen, its
# size at scale 1, its text and the three channels of its ground.
CARD_JS = r"""
(id) => {
  const host = document.querySelector('.bl-view-host');
  const node = host && host.querySelector(`.react-flow__node[data-id="${CSS.escape(id)}"]`);
  const card = node && node.querySelector(':scope > .bf-card');
  if (!card) return null;
  const at = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, right: found.right, top: found.top, bottom: found.bottom};
  };
  const drawn = (color) => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const context = canvas.getContext('2d');
    context.fillStyle = color.trim();
    context.fillRect(0, 0, 1, 1);
    return Array.from(context.getImageData(0, 0, 1, 1).data.slice(0, 3));
  };
  const inside = id.slice(0, -'___group___'.length) + '/';
  const chevron = card.querySelector(':scope > .bf-chevron > .codicon');
  const walker = document.createTreeWalker(card, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    if (walker.currentNode.textContent.trim()) nodes.push(walker.currentNode.textContent);
  }
  return {
    size: [node.offsetWidth, node.offsetHeight], card: at(card),
    name: at(card.querySelector(':scope > .bf-layer-name, :scope > .bf-name')),
    chevron: chevron
      ? Array.from(chevron.classList).find((name) => name.startsWith('codicon-')).slice(8)
      : null,
    texts: Array.from(
      card.querySelectorAll(':scope > .bf-in, :scope > .bf-out'),
      (text) => ({classes: text.className, text: text.textContent, at: at(text)})),
    nodes,
    marks: Array.from(card.querySelectorAll(':scope > .react-flow__handle'), (mark) => {
      const found = mark.getBoundingClientRect();
      return {x: (found.left + found.right) / 2, y: (found.top + found.bottom) / 2,
              radius: getComputedStyle(mark).borderTopLeftRadius,
              open: mark.classList.contains('bf-open'), port: mark.dataset.port || null};
    }),
    segments: Array.from(host.querySelectorAll('.react-flow__node'))
      .filter((other) => other.dataset.id.startsWith(inside)
        && other.querySelector(':scope > .bf-builder'))
      .map((other) => {
        const segment = other.querySelector(':scope > .bf-builder');
        return {id: other.dataset.id, at: at(other), size: [other.offsetWidth, other.offsetHeight],
                text: segment.textContent,
                ground: drawn(getComputedStyle(segment).backgroundColor)};
      })
      .sort((one, two) => one.at.left - two.at.left),
  };
}
"""
# The main bar as the page draws it (design pass 10 §3; unit N, Task 1),
# which took the rail's buttons of Task 24: the bar's box and its mark's;
# for each toggle its region, accessible name, hover, aria-expanded and
# box, the box of its icon and the icon's Codicon and glyph, the color of
# the icon, and the color and height of the line under it, each color as
# the browser draws it, null where no line is drawn; and the accent, ink-1
# and ink-2 as the browser draws them.
TOGGLE_ICONS_JS = r"""
() => {
  const drawn = (color) => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const context = canvas.getContext('2d');
    context.fillStyle = color.trim();
    context.fillRect(0, 0, 1, 1);
    return Array.from(context.getImageData(0, 0, 1, 1).data.slice(0, 3));
  };
  const at = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, right: found.right, top: found.top, bottom: found.bottom,
            width: found.width, height: found.height};
  };
  const bar = document.querySelector('.bl-main-bar');
  const root = getComputedStyle(document.documentElement);
  return {
    bar: at(bar),
    mark: at(bar.querySelector('.bl-mark img')),
    accent: drawn(root.getPropertyValue('--bl-accent')),
    ink1: drawn(root.getPropertyValue('--bl-ink-1')),
    ink2: drawn(root.getPropertyValue('--bl-ink-2')),
    buttons: Array.from(bar.querySelectorAll('.bl-toggle'), (button) => {
      const icon = button.querySelector('.bl-toggle-icon');
      const codicon = icon.querySelector(':scope > .codicon');
      const glyph = icon.querySelector(':scope > .bl-toggle-glyph');
      const line = getComputedStyle(button, '::after');
      return {
        fold: button.dataset.fold, label: button.getAttribute('aria-label'), title: button.title,
        expanded: button.getAttribute('aria-expanded'), box: at(button),
        icon: at(icon), iconColor: drawn(getComputedStyle(icon).color),
        parts: [codicon ? Array.from(codicon.classList).find((name) => name.startsWith('codicon-'))
                          .slice('codicon-'.length) : null,
                glyph ? glyph.dataset.glyph : null],
        line: line.content === 'none' ? null : [drawn(line.backgroundColor), line.height],
      };
    }),
  };
}
"""
# the height at scale 1 of a card whose fields are all joined, within one
# pixel, and its least width (design pass 13 §2, rules 1 and 6), and the
# most height at scale 1 of `keeper_cons`'s card with its six fields
# printed, while it is selected (design pass 13 §2, rule 7: the band's
# foot at 44, three rows of 12 and 4 px of fill)
CARD_JOINED = 32
CARD_LEAST = 80
KEEPER_PRINTED = 84


def card_bands(found: dict, zoom: float, G: dict, band: bool = False) -> None:
    """Asserts the bands of the card `found` (CARD_JS) drawn at the scale
    `zoom` (design pass 13 §2; design pass 7 §§3 and 4): its name's line
    box from G.cardNameTop under the card's top, above the strip; its
    builders' segments, where it has any, at G.cardStripY, G.cardStripH
    high at scale 1 and printing no text, side by side G.cardSegmentGap
    apart from G.cardInset inside the card's left edge to G.cardStripRight
    inside its right edge, or, where the card is selected, `band`,
    G.cardBandH high from G.cardBandLeft inside the left edge and ending by
    G.cardBandRight inside the right edge; each printed text G.frameRow
    high at scale 1, the first of them directly under the band, or under
    the strip and the pixel beneath it; and each port's mark a square
    centered on the card's left or right edge, the marks of a side about
    the card's axis, G.cardAxis."""
    card, name = found["card"], found["name"]
    strip_top = card["top"] + G["cardStripY"] * zoom
    assert card["top"] + (G["cardNameTop"] - 0.5) * zoom <= name["top"], (card, name)
    assert name["bottom"] <= strip_top + 0.5, (name, strip_top)
    above = strip_top + (G["cardStripH"] + 1) * zoom
    if found["segments"]:
        left, right = (G["cardBandLeft"], G["cardBandRight"]) if band else (G["cardInset"], G["cardStripRight"])
        for segment in found["segments"]:
            assert segment["size"][1] == G["cardBandH" if band else "cardStripH"], segment
            assert band or segment["text"] == "", segment
            assert abs(segment["at"]["top"] - strip_top) <= 0.5, (segment, strip_top)
        lefts = [segment["at"]["left"] for segment in found["segments"]]
        assert lefts == sorted(lefts)
        assert abs(lefts[0] - (card["left"] + left * zoom)) <= 0.5, (lefts, card)
        for one, other in zip(found["segments"], found["segments"][1:]):
            assert abs(other["at"]["left"] - one["at"]["right"] - G["cardSegmentGap"] * zoom) <= 0.5, (one, other)
        end = found["segments"][-1]["at"]["right"]
        if band:
            assert end <= card["right"] - right * zoom + 0.5, (end, card)
        else:
            assert abs(end - (card["right"] - right * zoom)) <= 0.5, (end, card)
        above = max(segment["at"]["bottom"] for segment in found["segments"]) + (0 if band else zoom)
    if found["texts"]:
        # the rows start directly under the band, or under the strip and the pixel beneath it
        first = min(text["at"]["top"] for text in found["texts"])
        assert abs(first - above) <= 0.5, (first, above)
        for text in found["texts"]:
            high = text["at"]["bottom"] - text["at"]["top"]
            assert abs(high - G["frameRow"] * zoom) <= 0.5, text
    axis = card["top"] + G["cardAxis"] * zoom
    for side in ("left", "right"):
        marks = [mark for mark in found["marks"] if abs(mark["x"] - card[side]) <= 1.5]
        if marks:
            assert abs(sum(mark["y"] for mark in marks) / len(marks) - axis) <= 0.5, (marks, axis)
    for mark in found["marks"]:
        # a port is a square plug or socket since design pass 11 §1a (a circle under design pass 10 §6)
        assert mark["radius"] == "0px", mark
        edge = min(abs(mark["x"] - card["left"]), abs(mark["x"] - card["right"]))
        assert edge <= 1.5, (mark, card)


def own_fields(graph: dict, occurrence: str) -> list[str]:
    """The fields of the own `Inputs` and `Outputs` of the stage occurrence
    `occurrence` of the trellis graph `graph`, the reading fields first, each
    side in the order of its ports (spec 0.4 §3.4)."""
    return [
        next(attribute["value"] for attribute in port["attrs"] if attribute["key"] == "field")
        for key in ("inputsMetadata", "outputsMetadata")
        for node in graph["nodes"]
        if node.get("namespace") == occurrence
        for port in node.get(key) or []
        if re.search(r"/(?:un)?joined:[^/]+$", port["id"])
    ]


def terminal_opening(tab, layer: str) -> bool:
    """Whether the region shows its graph at the opening on the drawn
    layer `layer`, the terminal period's (`opens_on`, the layer's place and
    the graph's extent read from the drawn boxes; AAS, M-D15)."""
    nodes = tab.evaluate(DRAWN_PLACES_JS)["nodes"]
    terminal = nodes.get(layer)
    if terminal is None:
        return False
    place = {"ax": terminal["x"], "ay": terminal["y"]}
    place.update(width=terminal["width"], height=terminal["height"])
    return opens_on(viewport(tab), place, drawn_extent(nodes))


def printed_fields(found: dict) -> list[str]:
    """The fields a card prints in its rows (CARD_JS), each its name with no
    branch word, in the card's order."""
    return [text["text"].split(" ")[-1] for text in found["texts"]]


def test_task_24_the_stage_frame_is_a_card_of_three_bands_and_the_main_bar_draws_its_panels(
    browser, server_on, durables_folder
):
    """Task 24 (AAS, L-D16, L-D17 and L-D19), its card as Task 30 amends it
    (AAS, L-D25; design pass 7 §3). Chosen while the view stands at the
    scale 1, the durables model's forward trellis graph, periods 0 to 2, is
    laid out once to its opening: the view opens on its terminal period's
    drawn layer at the largest scale, at most 1 and at least the reading
    scale 0.6, at which the layer fills the region (K-D22 as AAS's M-D15
    amends it; L-I277). On that graph every open occurrence is a card of
    bands with no room between them: the name's row, the strip of its
    builders' segments, each 3 px high at scale 1 from 9 px inside the
    card's left edge to 29 px inside its right edge, 2 px apart, with no
    text, and the rows of its unjoined fields; no field of the durables
    model is unjoined, so each card prints no field's name and no count,
    and `keeper_cons` is 32 px high at scale 1 (design pass 13 §2); every
    port's mark a 6-px square centered on the card's edge and about its
    axis, 14 px from its top. Selected, `keeper_cons`'s card
    prints its three reading fields and its three writing fields in rows of
    their own under the band of 20 px and is at most 84 px high; at the
    scales 1 and 0.9 no card prints a field and the layout does not run
    again (L-D25). A click on each of `keeper_cons`'s two segments opens
    that builder in place, and its toggle closes it again. The main bar,
    which took the rail's buttons (design pass 10 §3; unit N, Task 1), is
    36 px high, the brand's mark 20 px high at its left and its four
    toggles 26 × 26 px, 4 px apart (design pass 13 §4; D5), each its panel's icon of 16 px, its
    Codicon and glyph (unit M, Task 11; AAS, M-D18; N-D10), named and
    hovered by its panel's name; while the panel is open the icon is in
    ink-1 and a line of 2 px in the accent stands under the toggle, and
    while it is closed the icon is in ink-2 with no line. Every text meets
    its contrast bound."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        # the backward graph shown at the scale 1 (L-I277), which lays out
        # nothing again (L-D25)
        record_layouts(tab)
        view = viewport(tab)
        flow_handle(
            tab,
            "setView",
            {"viewport": {"x": view["x"], "y": view["y"], "zoom": 1.0}, "selection": None},
        )
        wait_until(
            lambda: abs(viewport(tab)["zoom"] - 1.0) <= 1e-6, 30.0, "the backward graph at 1"
        )
        tab.evaluate(TWO_FRAMES_JS)
        before = layouts_recorded(tab)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: tab.locator('.bl-graph-bar[data-graph="forward"]').count() == 1
            and tab.evaluate(CARD_JS, KEEPER_CONS_LAYER) is not None,
            60.0,
            "the forward graph's cards",
        )
        wait_until(
            lambda: terminal_opening(tab, f"periods[0]{LAYER_ID_ENDING}"), 30.0, "the opening"
        )
        # the forward graph's opening is measured on the cards it draws: one
        # layout, its cards folded, and the view the opening of its terminal
        # period's drawn layer (K-D22 as M-D15 amends it)
        wait_until(lambda: view_still(tab, 1000), 30.0, "the forward graph at rest")
        assert layouts_recorded(tab) - before == 1, layouts_recorded(tab) - before
        nodes = tab.evaluate(DRAWN_PLACES_JS)["nodes"]
        terminal = nodes[f"periods[0]{LAYER_ID_ENDING}"]
        place = {"ax": terminal["x"], "ay": terminal["y"]}
        place.update(width=terminal["width"], height=terminal["height"])
        assert opens_on(viewport(tab), place, drawn_extent(nodes)), (viewport(tab), place)
        tab.evaluate(TWO_FRAMES_JS)
        G = tab.evaluate("() => window.BellmanFlowLayout.G")
        zoom = viewport(tab)["zoom"]
        held = tab.evaluate(HELD_COLLECTION_JS)
        graph = graph_named(held, "forward")
        opened = sorted(
            namespace
            for namespace in flow_handle(tab, "openLayers")
            if namespace.count("/") == 1 and namespace.startswith("periods[")
        )
        assert len(opened) == 10, opened
        fields = {namespace: own_fields(graph, namespace) for namespace in opened}
        for namespace in opened:
            found = tab.evaluate(CARD_JS, namespace + LAYER_ID_ENDING)
            card_bands(found, zoom, G)
            # the chevron that opens the occurrence with every builder open (design pass 13 §2, rule 4)
            assert found["chevron"] == "chevron-right", found
            assert found["texts"] == [], (namespace, found["texts"])
        keeper = tab.evaluate(CARD_JS, KEEPER_CONS_LAYER)
        print(f"task 24: {KEEPER_CONS_LAYER} folded at {zoom:.3f}: {keeper['size']} at scale 1")
        assert abs(keeper["size"][1] - CARD_JOINED) <= 1, keeper["size"]
        assert [segment["id"].split("/")[2] for segment in keeper["segments"]] == [
            f"arvl_to_dcsn{LAYER_ID_ENDING}",
            f"dcsn_to_cntn{LAYER_ID_ENDING}",
        ]
        assert contrast_faults(tab, CONTRAST_EXCEPTIONS) == []

        # selected, keeper_cons's card prints every field in a row of its own
        tab.click(f'.react-flow__node[data-id="{KEEPER_CONS_LAYER}"] .bf-layer-name')
        printed, _ = wait_until(
            lambda: (lambda found: found if found and len(printed_fields(found)) == 6 else None)(
                tab.evaluate(CARD_JS, KEEPER_CONS_LAYER)
            ),
            30.0,
            "keeper_cons's card unfolded while selected",
        )
        print(f"task 24: {KEEPER_CONS_LAYER} selected: {printed['size']} at scale 1")
        assert printed["size"][1] <= KEEPER_PRINTED, printed["size"]
        assert printed_fields(printed) == fields["periods[0]/keeper_cons"]
        card_bands(printed, zoom, G, band=True)

        # at the scales 1 and 0.9, nothing selected, no card prints a field;
        # the layout runs once as the selection ends, and no change of the
        # scale runs it again (L-D25); the view ends at the opening's scale,
        # on the terminal period, where the opening's translation holds it
        # (M-D15)
        settled = None
        for scale in (1.0, 0.9, READING_SCALE, zoom):
            view = viewport(tab)
            flow_handle(
                tab,
                "setView",
                {"viewport": {"x": view["x"], "y": view["y"], "zoom": scale}, "selection": None},
            )

            def drawn_at():
                cards = {ns: tab.evaluate(CARD_JS, ns + LAYER_ID_ENDING) for ns in opened}
                done = all(found is not None and found["texts"] == [] for found in cards.values())
                return cards if done else None

            cards, _ = wait_until(drawn_at, 30.0, f"the cards at the scale {scale}")
            wait_until(lambda: view_still(tab, 1000), 30.0, f"the view at the scale {scale}")
            counted = layouts_recorded(tab)
            assert settled is None or counted == settled, (scale, counted, settled)
            settled = counted
            for namespace in opened:
                card_bands(tab.evaluate(CARD_JS, namespace + LAYER_ID_ENDING), scale, G)
            keeper = cards["periods[0]/keeper_cons"]["size"]
            print(f"task 24: at the scale {scale} periods[0]/keeper_cons is {keeper} at scale 1")

        # a click on each of keeper_cons's segments opens its builder in place
        for name in ("arvl_to_dcsn", "dcsn_to_cntn"):
            builder = f"periods[0]/keeper_cons/{name}{LAYER_ID_ENDING}"
            node = f'.bl-view-host .react-flow__node[data-id="{builder}"]'
            tab.click(f"{node} .bf-builder-toggle")
            wait_until(
                lambda node=node: tab.locator(f"{node} > .bf-layer").count() == 1
                and tab.evaluate(CARD_JS, KEEPER_CONS_LAYER) is None,
                30.0,
                f"{name} open in place",
            )
            click_toggle(tab, builder)
            wait_until(
                lambda: tab.evaluate(CARD_JS, KEEPER_CONS_LAYER) is not None,
                30.0,
                f"{name} closed again",
            )
            view = viewport(tab)
            flow_handle(
                tab,
                "setView",
                {"viewport": {"x": view["x"], "y": view["y"], "zoom": zoom}},
            )

        # the main bar: the mark, then each toggle its panel's icon, the
        # open ones marked by ink-1 and the accent's line under them (design
        # pass 10 §3; unit N, Task 1)
        bar = tab.evaluate(TOGGLE_ICONS_JS)
        print(f"task 24: the main bar {bar['bar']}, its mark {bar['mark']}")
        assert bar["bar"]["height"] == 36
        assert abs(bar["mark"]["height"] - 20) <= 0.5
        buttons = bar["buttons"]
        assert [button["fold"] for button in buttons] == list(app.PANEL_NAMES)
        for button in buttons:
            name = app.PANEL_NAMES[button["fold"]]
            assert (button["label"], button["title"]) == (name, name), button
            assert (button["box"]["width"], button["box"]["height"]) == (26, 26), button
            assert (button["icon"]["width"], button["icon"]["height"]) == (16, 16), button
            assert button["parts"] == list(icons.TOGGLE_ICONS[button["fold"]]), button
            if button["expanded"] == "true":
                assert button["iconColor"] == bar["ink1"], button
                assert button["line"] == [bar["accent"], "2px"], button
            else:
                assert button["iconColor"] == bar["ink2"], button
                assert button["line"] is None, button
        lefts = [button["box"]["left"] for button in buttons[1:]]
        gaps = [left - button["box"]["right"] for left, button in zip(lefts, buttons)]
        # four pixels between the two toggles of a group, design pass 13 §4's grid (D5), where design pass 10 §3
        # left two; since design pass 14 §10 (S-D16) each toggle stands at the end of the bar on which its panel
        # opens, `folder` and `inspector` at the left and `details` and `matsya` at the right, so the gap between
        # `inspector` and `details` spans the bar's middle
        assert [gaps[0], gaps[2]] == [4, 4] and gaps[1] > bar["bar"]["width"] / 2, gaps
        # a toggle folded draws its icon in ink-2, with no line
        details = '.bl-main-bar .bl-fold[data-fold="details"]'
        tab.click(details)
        wait_until(
            lambda: tab.get_attribute(details, "aria-expanded") == "false", 5.0, "details folded"
        )
        tab.mouse.move(800, 600)
        drawn = tab.evaluate(TOGGLE_ICONS_JS)["buttons"]
        (folded,) = [button for button in drawn if button["fold"] == "details"]
        assert folded["iconColor"] == bar["ink2"], folded
        assert folded["line"] is None, folded
        assert contrast_faults(tab, CONTRAST_EXCEPTIONS) == []
        tab.click(details)
        wait_until(
            lambda: tab.get_attribute(details, "aria-expanded") == "true", 5.0, "details opened"
        )
    finally:
        context.close()


# The durables model of Task 25's test, relative to the folder: its recipe's
# row of `bequest`, which `remove stage` takes out; the terminal period's
# list and connector in the trellis file, as written and as the removal
# leaves them; the entry of period.yml and the earliest entry of a period
# file of its own, period.extra.yml, which the test writes in its place, and
# which `remove period` takes out; and the variant's period file, which no
# trellis file names once the variant's recipe and trellis file are gone.
BEQUEST_ROW = (
    "  bequest:       {stage: stages/bequest/bequest.bl,             calibration: "
    "{all: [calibration/durables, $fill]}, methods: {all: [stages/bequest/methods.bl]}, "
    "periods: [0, 0]}\n"
)
TERMINAL_LISTED = (
    "stages: [tenure, keeper_cons, adjuster_cons, bequest]",
    "stages: [tenure, keeper_cons, adjuster_cons]",
)
TERMINAL_CONNECTOR = (
    "      - {a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, "
    "h_nxt_adj: h_bq, z_nxt_adj: z_bq}\n",
    "      - {}\n",
)
FIFTY = "  - {template: period.yml, repeat: 50}\n"
EXTRA_ENTRY = "  - {template: period.extra.yml, repeat: 1}\n"
EXTRA_PERIOD = "declaration/period.extra.yml"
DURABLES_TRELLIS = "declaration/trellis.yml"
TWO_STAGES_PERIOD = "declaration/period.two-stages.yml"
BEQUEST_FOLDER = "declaration/stages/bequest"
BEQUEST_REMOVED_NOTE = (
    "spec.yml, stages: bequest removed; trellis.yml, periods[0].stages: bequest removed, "
    "periods 0; trellis.yml, periods[0].connectors[0]: {a_nxt_kp: a_bq, h_nxt_kp: h_bq, "
    "z_nxt_kp: z_bq, a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq} removed, periods 0; "
    "deleted on save: stages/bequest/"
)
EXTRA_REMOVED_NOTE = (
    "trellis.yml, periods[2] removed, periods 50; deleted on save: period.extra.yml; "
    "restriction periods 49"
)
# each row of the tree that a save would delete, as its path, its mark and
# the words of its control, the text button `Keep` (design pass 8 §§4 and
# 8 item 1; unit M, Task 6)
DELETING_ROWS_JS = r"""
() => Array.from(document.querySelectorAll('.bl-tree .bl-deleting'), (row) => {
  const control = row.parentElement.querySelector('.bl-tree-remove');
  return [row.dataset.path, row.querySelector('.bl-tree-mark').textContent,
          control ? control.textContent.trim() : null];
})
"""


def test_task_25_a_stage_a_period_and_a_file_are_removed_and_deleted_on_save(
    browser, server_on, tmp_path
):
    """Task 25 (AAS, L-D18; J-D33 and J-D39; spec 0.4 §§3.5 and 3.6 by their
    inverses). On a copy of the durables model without its variant's recipe
    and trellis file, whose earliest period is written by an entry of its
    own period file, period.extra.yml, the recipe open: `remove stage` in
    `bequest`'s row of the Recipe tab (unit M, Task 10) takes the row out
    of the recipe and, in the trellis file, the key and the connector of
    its six joins, the status line naming each file and address and `stages/bequest/` as
    deleted on save; the tree draws that folder dimmed with `deleted on
    save` and its control `Keep`; nothing is deleted. One Command+Z in the
    recipe restores both files, no file unsaved and no folder listed. Made
    again and the recipe saved, the folder is gone from disk, git staging
    nothing, the save's note naming it, and once the trellis file is saved
    the trellis is read constructed with no `bequest`. Then `remove period`
    in Details of periods[50] takes the entry of period.extra.yml out of the
    trellis file, the note naming the file deleted on save and the
    restriction written; one Command+Z restores it; made again and saved,
    period.extra.yml is gone and the trellis holds 50 periods. Last, the
    tree's `remove` on period.two-stages.yml, which no trellis file names,
    draws it dimmed with `deleted on save`, and the next save deletes it."""
    copy = tmp_path / "durables"
    shutil.copytree(DURABLES, copy, ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("spec.two-stages.yml", "trellis.two-stages.yml"):
        (copy / "declaration" / name).unlink()
    trellis_file, recipe_file = copy / DURABLES_TRELLIS, copy / RECIPE_FILE
    standing = trellis_file.read_text(encoding="utf-8").replace(
        FIFTY, "  - {template: period.yml, repeat: 49}\n" + EXTRA_ENTRY
    )
    trellis_file.write_text(standing, encoding="utf-8")
    shutil.copyfile(copy / "declaration/period.yml", copy / EXTRA_PERIOD)
    init_repository(copy)
    recipe_text = recipe_file.read_text(encoding="utf-8")
    assert recipe_text.count(BEQUEST_ROW) == 1
    assert standing.count(TERMINAL_LISTED[0]) == 1 and standing.count(TERMINAL_CONNECTOR[0]) == 1
    no_bequest = recipe_text.replace(BEQUEST_ROW, "")
    terminal = standing.replace(*TERMINAL_LISTED).replace(*TERMINAL_CONNECTOR)
    no_extra = terminal.replace(EXTRA_ENTRY, "")
    remove_bequest = '.bl-recipe-row[data-stage="bequest"] .bl-remove-stage'
    context, tab = new_tab(browser)

    def undone_to(text: str, what: str) -> None:
        # one Command+Z in the editor, which then holds `text` and still
        # holds it a second later
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 10.0, what)
        tab.wait_for_timeout(1_000)
        assert tab.evaluate(DOCUMENT_JS) == text, what

    def constructed(periods: int) -> bool:
        line = trellis_settled(tab, RECIPE_FILE)
        return bool(line) and "refused" not in line.split(" · ") and f" {periods} periods" in line

    def saved(path: str, text: str) -> None:
        # the file `path` opened in its tab and saved, then holding `text`
        if open_path_shown(tab) != path:
            tab.click(f'.bl-tab[data-path="{path}"]')
            wait_until(lambda: open_path_shown(tab) == path, 30.0, f"{path} open")
            tab.wait_for_timeout(1_000)
        tab.click(".bl-save")
        wait_until(
            lambda: (copy / path).read_text(encoding="utf-8") == text, 30.0, f"{path} saved"
        )

    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        assert tab.locator(remove_bequest).get_attribute("title") == (
            "Remove bequest from this recipe"
        )
        reveal_in_tree(tab, "declaration/stages/bequest/bequest.bl")

        # (a) `remove stage`: one change of the two files' unsaved texts
        for attempt in ("first", "again"):
            tab.click(remove_bequest)
            wait_until(lambda: gesture_note(tab) == BEQUEST_REMOVED_NOTE, 30.0, "the note")
            wait_until(lambda: tab.evaluate(DOCUMENT_JS) == no_bequest, 10.0, "the row out")
            edited_files = sorted([DURABLES_TRELLIS, RECIPE_FILE])
            wait_until(lambda: unsaved_in_tree(tab) == edited_files, 10.0, "both unsaved")
            wait_until(
                lambda: tab.evaluate(DELETING_ROWS_JS)
                == [[BEQUEST_FOLDER, "deleted on save", "Keep"]],
                10.0,
                "the folder dimmed",
            )
            assert (copy / BEQUEST_FOLDER).is_dir()
            if attempt == "first":
                undone_to(recipe_text, "the removal undone")
                wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "no file unsaved")
                wait_until(lambda: tab.evaluate(DELETING_ROWS_JS) == [], 10.0, "none dimmed")
                wait_until(lambda: constructed(51), 60.0, "the trellis read again")
                tab.wait_for_selector(remove_bequest, timeout=30_000)

        # the recipe saved: the folder is deleted, git staging nothing
        saved(RECIPE_FILE, no_bequest)
        wait_until(lambda: not (copy / BEQUEST_FOLDER).exists(), 10.0, "the folder deleted")
        wait_until(lambda: gesture_note(tab) == "deleted: stages/bequest/", 10.0, "save's note")
        assert git(copy, "diff", "--cached", "--name-only") == ""
        saved(DURABLES_TRELLIS, terminal)
        wait_until(lambda: constructed(51), 60.0, "the trellis without bequest")
        assert not tab.locator(".bl-recipe-row[data-stage='bequest']").count()

        # (b) `remove period` of periods[50], the earliest, in Details
        for attempt in ("first", "again"):
            restrict(tab, "periods 48–50")
            choose_view(tab, None, "forward")
            select_until(
                tab,
                "periods[50]___group___",
                "forward",
                lambda: tab.locator(".bl-period-remove").count() == 1,
                "Details of periods[50]",
                60.0,
            )
            tab.click(".bl-period-remove")
            wait_until(lambda: gesture_note(tab) == EXTRA_REMOVED_NOTE, 30.0, "the note")
            wait_until(lambda: tab.evaluate(DOCUMENT_JS) == no_extra, 10.0, "the entry out")
            wait_until(lambda: restriction_shown(tab) == "periods 49", 10.0, "the restriction")
            wait_until(
                lambda: tab.evaluate(DELETING_ROWS_JS)
                == [[EXTRA_PERIOD, "deleted on save", "Keep"]],
                10.0,
                "period.extra.yml dimmed",
            )
            if attempt == "first":
                undone_to(terminal, "the period's removal undone")
                wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "no file unsaved")
                wait_until(lambda: tab.evaluate(DELETING_ROWS_JS) == [], 10.0, "none dimmed")
                wait_until(lambda: constructed(51), 60.0, "the trellis read again")
        saved(DURABLES_TRELLIS, no_extra)
        wait_until(lambda: not (copy / EXTRA_PERIOD).exists(), 10.0, "period.extra.yml deleted")
        wait_until(lambda: gesture_note(tab) == "deleted: period.extra.yml", 10.0, "save's note")
        wait_until(lambda: constructed(50), 60.0, "the trellis of 50 periods")

        # (c) the tree's `remove` of a period file no trellis file names, the
        # icon button `Remove` (design pass 8 §§3 and 4; unit M, Task 6)
        control = f'.bl-tree-remove[data-path="{TWO_STAGES_PERIOD}"]'
        assert tab.locator(control).evaluate("(button) => button.label") == "Remove"
        tab.click(control)
        wait_until(
            lambda: tab.evaluate(DELETING_ROWS_JS)
            == [[TWO_STAGES_PERIOD, "deleted on save", "Keep"]],
            10.0,
            "period.two-stages.yml dimmed",
        )
        assert (copy / TWO_STAGES_PERIOD).is_file()
        tab.click(".bl-save")
        wait_until(lambda: not (copy / TWO_STAGES_PERIOD).exists(), 10.0, "the file deleted")
        wait_until(
            lambda: gesture_note(tab) == "deleted: period.two-stages.yml", 10.0, "save's note"
        )
        assert git(copy, "diff", "--cached", "--name-only") == ""
    finally:
        context.close()


# The nodes the region draws, by id (AAS, L-D20): each node's box on the
# screen; for a box, its hover and whether it is selected, and its name's
# box, classes and text, the width its symbol is drawn in and the width of
# its whole text, and its method mark's box.
STAGE_NODES_JS = r"""
() => {
  const at = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, right: found.right, top: found.top, bottom: found.bottom,
            width: found.width, height: found.height};
  };
  const nodes = {};
  for (const node of document.querySelectorAll('.bl-view-host .react-flow__node')) {
    const box = node.querySelector(':scope > .bf-box');
    const name = box && box.querySelector(':scope > .bf-name');
    const symbol = name && name.querySelector(':scope > .bf-symbol');
    const mark = name && name.querySelector(':scope > .bf-mark');
    nodes[node.dataset.id] = {
      at: at(node),
      title: box ? box.getAttribute('title') : null,
      selected: !!box && box.classList.contains('selected'),
      name: name && {at: at(name), classes: name.className, text: name.textContent,
                     drawn: symbol.clientWidth, whole: symbol.scrollWidth, mark: mark && at(mark)},
    };
  }
  return nodes;
}
"""
# the frames of `keeper_cons`'s backward builders graph that stand in one
# column, its two value builders' (AAS, L-D20)
KEEPER_COLUMN = ("cntn_to_dcsn___group___", "dcsn_to_arvl___group___")
# the frame of `keeper_cons`'s policy builder, which stands beside the column
KEEPER_POLICY = "policy___group___"
# the output box of `cntn_to_dcsn`, whose label the layout cuts
KEEPER_OUTPUT = "cntn_to_dcsn:Evaluation"


def test_task_26_the_stage_view_s_frames_and_boxes_stand_on_one_axis(
    browser, server_on, durables_folder
):
    """Task 26 (AAS, L-D20). The durables model's `keeper_cons` opened from
    the tree, its backward builders graph drawn in the stage view: each
    node's place on the page, relative to the stage's `Inputs`, is the
    place of the layout's records within 1 px, the records that the
    bundle's `arrange` aligns with the page's measure; the frames
    `cntn_to_dcsn` and `dcsn_to_arvl` share their left edge and their width
    within 1 px, the frame of the policy builder stands beside them at that
    width within 1 px, `Inputs` and `Outputs` stand on their axis and every
    box of every open frame on its frame's axis, within 2 px. The output box
    `cntn_to_dcsn:Evaluation` cuts its label: it is no wider than
    G.labelMax and its padding, its symbol is drawn narrower than its whole
    text, its method mark stands whole within the box, and its hover holds
    the label whole; selected, the box prints the label whole, centered on
    the box, and the frames stand where they stood."""
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(durables_folder), KEEPER_CONS)
        choose_view(tab, "operator", "backward")
        wait_until(
            lambda: KEEPER_OUTPUT in tab.evaluate(STAGE_NODES_JS), 30.0, "the backward graph"
        )

        def at_rest() -> bool:
            # the nodes and the viewport unchanged across 300 ms
            first = (tab.evaluate(STAGE_NODES_JS), viewport(tab))
            tab.wait_for_timeout(300)
            return first == (tab.evaluate(STAGE_NODES_JS), viewport(tab))

        wait_until(at_rest, 30.0, "the backward graph at rest")
        G = tab.evaluate("() => window.BellmanFlowLayout.G")
        zoom = viewport(tab)["zoom"]
        graph = graph_named(tab.evaluate(HELD_COLLECTION_JS), "backward")
        records = layout_records(tab, graph, set(flow_handle(tab, "openLayers")))
        drawn = tab.evaluate(STAGE_NODES_JS)
        origin = drawn["GraphInputs"]["at"]

        def place(node_id: str, nodes: dict) -> dict:
            # the node's place at scale 1 relative to the stage's `Inputs`
            found = nodes[node_id]["at"]
            return {
                "x": (found["left"] - origin["left"]) / zoom,
                "y": (found["top"] - origin["top"]) / zoom,
                "width": found["width"] / zoom,
                "height": found["height"] / zoom,
            }

        inputs = records["places"]["GraphInputs"]
        assert set(records["places"]) == set(drawn)
        for node_id, laid in records["places"].items():
            shown = place(node_id, drawn)
            for key, value in (
                ("x", laid["ax"] - inputs["ax"]),
                ("y", laid["ay"] - inputs["ay"]),
                ("width", laid["width"]),
                ("height", laid["height"]),
            ):
                assert abs(shown[key] - value) <= 1, (node_id, key, shown, laid)

        def center(found: dict) -> float:
            return found["x"] + found["width"] / 2

        frames = [place(frame, drawn) for frame in KEEPER_COLUMN]
        assert abs(frames[0]["x"] - frames[1]["x"]) <= 1, frames
        assert abs(frames[0]["width"] - frames[1]["width"]) <= 1, frames
        # the policy builder's frame beside the column, of the column's width
        policy = place(KEEPER_POLICY, drawn)
        assert abs(policy["width"] - frames[0]["width"]) <= 1, (policy, frames)
        assert policy["x"] >= frames[0]["x"] + frames[0]["width"] or (
            policy["x"] + policy["width"] <= frames[0]["x"]
        ), (policy, frames)
        axis = center(frames[0])
        for node_id in ("GraphInputs", "GraphOutputs"):
            assert abs(center(place(node_id, drawn)) - axis) <= 2, node_id
        for node in graph["nodes"]:
            if node.get("namespace"):
                frame = place(node["namespace"] + LAYER_ID_ENDING, drawn)
                assert abs(center(place(node["id"], drawn)) - center(frame)) <= 2, node["id"]

        label = next(node["label"] for node in graph["nodes"] if node["id"] == KEEPER_OUTPUT)
        whole = tab.evaluate("(text) => window.BellmanFlow.measure(text, 'label')", label)
        output = drawn[KEEPER_OUTPUT]
        name = output["name"]
        assert whole > G["labelMax"], whole
        assert output["title"] == label and name["text"] == label
        assert "bf-cut" in name["classes"].split(), name
        assert name["whole"] > name["drawn"], name
        assert output["at"]["left"] <= name["mark"]["left"], (output, name)
        assert name["mark"]["right"] <= output["at"]["right"] + 0.5, (output, name)
        assert place(KEEPER_OUTPUT, drawn)["width"] <= G["labelMax"] + 2 * G["padX"] + 2 + 0.5
        print(
            f"task 26: at {zoom:.3f} the frames {[round(f['width'], 1) for f in frames]} wide "
            f"at {[round(f['x'], 1) for f in frames]}, the policy's {policy['width']:.1f} wide "
            f"at {policy['x']:.1f}; {KEEPER_OUTPUT} "
            f"{place(KEEPER_OUTPUT, drawn)['width']:.1f} wide, its label {whole:.1f}"
        )

        select_node(tab, KEEPER_OUTPUT, "backward")
        wait_until(
            lambda: tab.evaluate(STAGE_NODES_JS)[KEEPER_OUTPUT]["selected"],
            10.0,
            "the output box selected",
        )
        chosen = tab.evaluate(STAGE_NODES_JS)
        box, name = chosen[KEEPER_OUTPUT]["at"], chosen[KEEPER_OUTPUT]["name"]
        assert name["whole"] <= name["drawn"] + 1, name
        assert name["at"]["width"] / zoom >= whole, (name, whole)
        middle = (name["at"]["left"] + name["at"]["right"]) / 2
        assert abs(middle - (box["left"] + box["right"]) / 2) <= 1, (name, box)
        for frame in KEEPER_COLUMN:
            for key in ("left", "top", "width", "height"):
                assert abs(chosen[frame]["at"][key] - drawn[frame]["at"][key]) <= 0.5, frame
        print(f"task 26: selected, the label printed {name['at']['width'] / zoom:.1f} wide")
    finally:
        context.close()


# Each group's box `add field` as drawn (Task 27; AAS, L-D21): the edges of
# its perch's section, of its table's column heads, of its three entries,
# of its button `+` and of the button's cell; the padding before a cell
# after the first; whether the box is its table's last row; its entries'
# placeholders, the button's hover and the text the group draws.
ADD_ROWS_JS = r"""
() => Array.from(document.querySelectorAll('.bl-class-group'), (group) => {
  const edges = (element) => {
    const box = element.getBoundingClientRect();
    return {left: box.left, top: box.top, right: box.right, width: box.width};
  };
  const table = group.querySelector('.bl-class-table');
  const row = group.querySelector('.bl-add-field');
  const entry = (name) => row.querySelector(`[data-entry="${name}"]`);
  const button = row.querySelector('.bl-add-button');
  return {
    group: group.dataset.group,
    section: edges(group.closest('.bl-class-perch')),
    heads: Array.from(table.querySelectorAll('th'), edges),
    gap: parseFloat(getComputedStyle(table.querySelector('th + th')).paddingLeft),
    last: table.rows[table.rows.length - 1] === row,
    entries: ['field', 'set', 'role'].map((name) => edges(entry(name))),
    button: edges(button),
    end: edges(button.closest('td') || button),
    placeholders: [entry('field').placeholder, entry('set').placeholder],
    hover: button.title,
    text: group.innerText,
  };
})
"""


def test_task_27_every_set_prints_whole_and_the_box_add_field_stands_on_one_line(
    page, server_on, durables_folder
):
    """Task 27 (AAS, L-D21; L-D4; L-D1), with the add row of design pass 6
    §3.6 (Task 29; AAS, L-D24). With the durables model's keeper_cons.bl
    open at 1600 × 1000, the page as it opens (K-D22), every set box of the
    Fields tab holds its set whole, its text no wider than its text area.
    In each group the box `add field` is its table's last row and stands on
    one line: its field entry spans the field column, its set entry the set
    column after the cell's padding, and its role select the role column
    after the cell's padding, each reaching 3 px beyond its column's text
    on each side; `+`, 24 px, stands in the cell after the role column, at
    the row's end; the three entries and `+` share one top and stand within
    the perch's section, the field entry's reach at its left excepted. The
    entries read `New field` and `Set`, `+` has the hover `Add field`, and
    the group draws no words `add field`. `q`, `ℝ₊` and `state` entered in
    the box of the decision group write `q : ℝ₊` into the outputs of
    arvl_to_dcsn, line 15, and `q` into the inputs of dcsn_to_cntn, line
    21, and no other line (Task 1)."""

    def spans(box: dict, left: float, width: float) -> bool:
        # the box's left edge and width, each within 0.5 px
        return abs(box["left"] - left) < 0.5 and abs(box["width"] - width) < 0.5

    url = server_on(durables_folder)
    original = (durables_folder / KEEPER_CONS).read_text(encoding="utf-8")
    open_file(page, url, KEEPER_CONS)
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)
    page.evaluate("() => document.fonts.ready.then(() => null)")
    sets = page.evaluate(SET_BOXES_JS)
    assert len(sets) == 19, sets
    for found in sets:
        assert found["text"] <= found["box"], found

    rows = page.evaluate(ADD_ROWS_JS)
    assert [row["group"] for row in rows] == ["arvl/", "dcsn/", "cntn/"]
    for row in rows:
        field, kind, role = row["entries"]
        button, end, section = row["button"], row["end"], row["section"]
        heads, gap = row["heads"], row["gap"]
        assert row["last"], row
        tops = [entry["top"] for entry in row["entries"]] + [button["top"]]
        assert max(tops) - min(tops) < 0.5, row
        assert spans(field, heads[0]["left"] - 3, heads[0]["width"] + 6), row
        assert spans(kind, heads[1]["left"] + gap - 3, heads[1]["width"] - gap + 6), row
        assert spans(role, heads[2]["left"] + gap - 3, heads[2]["width"] - gap + 6), row
        assert abs(end["left"] - heads[2]["right"]) < 0.5, row
        assert abs(end["width"] - 24) < 0.5 and abs(button["width"] - 24) < 0.5, row
        assert role["right"] <= button["left"] + 3.5, row
        assert abs(end["right"] - section["right"]) < 0.5, row
        assert section["left"] - 3.5 <= field["left"], row
        assert button["right"] <= section["right"] + 0.5, row
        assert row["placeholders"] == ["New field", "Set"], row
        assert row["hover"] == "Add field", row
        assert "add field" not in row["text"].lower(), row

    line_15 = original.split("\n")[14].replace(
        "z_d : ℝ₊₊) : !dcsn]", "z_d : ℝ₊₊, q : ℝ₊) : !dcsn]"
    )
    line_21 = original.split("\n")[20].replace(
        "c : ℝ₊₊ @ !ctrl) : !dcsn", "c : ℝ₊₊ @ !ctrl, q) : !dcsn"
    )
    written = edited(edited(original, 15, line_15), 21, line_21)
    assert changed_lines(original, written) == [15, 21]
    add_field(page, "dcsn/", "q", "ℝ₊", "state")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == written, 5.0, "q on lines 15 and 21")
    assert (durables_folder / KEEPER_CONS).read_text(encoding="utf-8") == original
    print(
        "task 27: the boxes `add field` at",
        [round(row["section"]["right"] - row["section"]["left"], 1) for row in rows],
        "px, `+` at",
        [round(row["button"]["width"], 1) for row in rows],
        "px",
    )


# The note of a model's declaration/ opened by itself, and the words of the
# button beside it (unit L, Task 28; AAS, L-D23)
DECLARATION_NOTE = "this folder is the declaration/ of portfolio-choice; open portfolio-choice"
ERROR_ACTION = ".bl-error-list .bl-error-line .bl-error-action"


def test_task_28_a_models_declaration_opened_by_itself_opens_the_model_folder(
    browser, server_on, tmp_path
):
    """Task 28 (AAS, L-D23), as M-D14 changes it by design: a server started
    on the `declaration/` of a copy of the portfolio model, as the desktop
    application starts the Workbench on the folder chosen in its dialog,
    opens the page on the model folder above it, where the recipe
    `declaration/spec.yml` is read, without the note and the button `open
    portfolio-choice` that unit L's page offered: the folder's name heads
    the tree, its root row (design pass 8 §6; unit M, Task 6), the tree
    shows `declaration` open with the recipe, which the editor opens, the
    recipe's trellis is read and constructs, and the list under the error
    mark holds no note of the declaration/ (AAS, M-D14: "somehow the
    trellis view does not work")."""
    copy = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
    url = server_on(copy / "declaration")
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, url)
        wait_until(lambda: open_path_shown(tab) == RECIPE_FILE, 60.0, "the recipe open")
        assert tab.locator(".bl-tree-root").text_content() == "portfolio-choice"
        assert tab.locator('.bl-folder-row[data-path="declaration"]:not(.bl-closed)').count() == 1
        assert tab.locator(f'.bl-tree-file[data-path="{RECIPE_FILE}"]').count() == 1
        status, _ = wait_until(
            lambda: trellis_settled(tab, RECIPE_FILE), 120.0, "the model folder's trellis"
        )
        assert " · loop " in status and not status.endswith(" · refused"), status
        assert DECLARATION_NOTE not in [line[0] for line in error_lines(tab)]
        assert tab.locator(ERROR_ACTION).count() == 0
    finally:
        context.close()


# The Fields tab as design pass 6 measures it (Task 29; AAS, L-D24): for
# each group, the boxes of its section, its table and its title; the
# title's text and hover, the computed type of its sign and of its word,
# and the word's left edge; each column head's text, hover, box, computed
# type and shadow; the box of the head row; for each field row its box,
# its cells' borders and shadows, its name, set and role as printed, the
# computed type of each, whether each holds its text whole, the hovers of
# the set and the role, and the border's color and the ground of each at
# rest; and the add row: whether it is the table's last row, its box, its
# cells' shadows, the boxes of its three entries, their placeholders and
# the placeholder's computed type, the box, hover, accessible name and text
# of `+`, the box of its cell, and the Codicon it names; the glyph it draws
# stands in the toolbar button's own tree, which ADD_GLYPHS_JS reads
# through Playwright's selectors (design pass 8 §4; unit M, Task 6).
FIELDS_TAB_JS = r"""
() => {
  const box = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, top: found.top, right: found.right, bottom: found.bottom,
            width: found.width, height: found.height};
  };
  const type = (element, pseudo) => {
    if (!element) return null;
    const style = getComputedStyle(element, pseudo || null);
    return {face: style.fontFamily.split(',')[0].trim().replace(/^"(.*)"$/, '$1'),
            size: style.fontSize, weight: style.fontWeight, color: style.color,
            spacing: style.letterSpacing, transform: style.textTransform};
  };
  const width = (element, text) => {
    const style = getComputedStyle(element);
    const probe = document.createElement('span');
    for (const name of ['fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'letterSpacing']) {
      probe.style[name] = style[name];
    }
    probe.style.position = 'absolute';
    probe.style.whiteSpace = 'pre';
    probe.textContent = text;
    document.body.append(probe);
    const found = probe.getBoundingClientRect().width;
    probe.remove();
    return found;
  };
  const inside = (element) => {
    const style = getComputedStyle(element);
    return element.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  };
  const rest = (element) => {
    const style = getComputedStyle(element);
    return [style.borderTopColor, style.backgroundColor];
  };
  return Array.from(document.querySelectorAll('.bl-class-group'), (group) => {
    const section = group.closest('.bl-class-perch');
    const title = section.querySelector('.bl-class-perch-name');
    const word = title.querySelector('.bl-class-perch-word');
    const table = group.querySelector('.bl-class-table');
    const add = table.querySelector('.bl-add-field');
    const entry = (name) => add.querySelector(`[data-entry="${name}"]`);
    const button = add.querySelector('.bl-add-button');
    return {
      perch: section.dataset.perch,
      group: group.dataset.group,
      section: box(section),
      table: box(table),
      title: {text: title.textContent, hover: title.title, box: box(title),
              sign: type(title.querySelector('.bl-class-sign')), word: type(word),
              wordLeft: word && box(word).left},
      heads: Array.from(table.tHead.rows[0].cells, (head) => ({
        text: head.textContent, hover: head.title, box: box(head), type: type(head),
        shadow: getComputedStyle(head).boxShadow})),
      headRow: box(table.tHead.rows[0]),
      rows: Array.from(table.tBodies[0].rows, (row) => {
        const field = row.querySelector('.bl-class-field');
        const set = row.querySelector('.bl-class-set');
        const role = row.querySelector('.bl-class-role');
        return {
          box: box(row),
          cells: Array.from(row.cells, (cell) => {
            const style = getComputedStyle(cell);
            return [style.borderTopWidth, style.borderRightWidth, style.borderBottomWidth,
                    style.borderLeftWidth, style.boxShadow];
          }),
          field: field.textContent,
          fieldType: type(field),
          fieldWidth: width(field, field.textContent),
          fieldWhole: width(field, field.textContent) <= field.clientWidth + 0.5,
          set: set.value,
          setType: type(set),
          setWhole: set.scrollWidth <= set.clientWidth,
          setHover: set.title,
          setRest: rest(set),
          role: role.value,
          roleType: type(role),
          roleWhole: width(role, role.value) <= inside(role) + 0.5,
          roleHover: role.title,
          roleRest: rest(role),
        };
      }),
      add: {
        last: table.rows[table.rows.length - 1] === add,
        box: box(add),
        shadows: Array.from(add.cells, (cell) => getComputedStyle(cell).boxShadow),
        entries: ['field', 'set', 'role'].map((name) => box(entry(name))),
        placeholders: [entry('field').placeholder, entry('set').placeholder],
        placeholderType: type(entry('field'), '::placeholder'),
        button: box(button),
        end: box(button.closest('td')),
        hover: button.title,
        label: button.label,
        text: button.textContent,
        icon: button.getAttribute('icon'),
      },
    };
  });
}
"""
# A set input or a role select of the Fields tab, the selector naming it,
# as drawn: its box, its top border's width and color, the radius of its
# top left corner, its ground, the box
# of its table cell and that cell's left padding, the left edge of its
# text, the box of its table, and whether the chevron its cell draws is
# shown.
FIELDS_CELL_JS = r"""
(selector) => {
  const cell = document.querySelector(selector);
  const style = getComputedStyle(cell);
  const holder = cell.closest('td');
  const edges = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, right: found.right, top: found.top, bottom: found.bottom};
  };
  const at = edges(cell);
  const chevron = getComputedStyle(holder, '::before');
  return {
    box: at,
    border: [style.borderTopWidth, style.borderTopColor],
    radius: style.borderTopLeftRadius,
    ground: style.backgroundColor,
    holder: edges(holder),
    padding: parseFloat(getComputedStyle(holder).paddingLeft),
    text: at.left + parseFloat(style.borderLeftWidth) + parseFloat(style.paddingLeft),
    table: edges(cell.closest('table')),
    chevron: chevron.content !== 'none' && chevron.display !== 'none'
      && chevron.opacity === '1',
  };
}
"""
# The color a custom property of the BellmanType panel holds, as the
# browser computes the color of an element in the panel whose color is
# that property.
PANEL_COLOR_JS = """
(name) => {
  const probe = document.createElement('span');
  probe.style.color = `var(${name})`;
  document.querySelector('.bl-classification').append(probe);
  const color = getComputedStyle(probe).color;
  probe.remove();
  return color;
}
"""
# the title of each perch's table and its hover (design pass 6 §§3.1 and
# 3.7), by the perch
FIELDS_TITLES = {
    "arvl": ("≺ Arrival", "The information set at which the stage begins."),
    "dcsn": ("∼ Decision", "The information set at which the control is chosen."),
    "cntn": ("≻ Continuation", "The information set after the control is chosen."),
}
# the size, the face and the color of each glyph the groups' `+` buttons
# draw, in the groups' order, given the glyphs that Playwright's selectors
# find within the buttons' own trees
ADD_GLYPHS_JS = """
(found) => found.map((glyph) => {
  const style = getComputedStyle(glyph);
  return [style.fontSize, style.fontFamily, style.color];
})
"""
# the hover of each column head of the Fields tab, in the columns' order
FIELDS_HEAD_HOVERS = [
    "The field's name, as the stage file writes it.",
    "The set in which the field takes its values.",
    "Whether the field is a state, a control or a value.",
]
# the words in which the hover of a role tag names the role (§3.7)
ROLE_HOVERS = {
    "state": "State",
    "!ctrl": "Control",
    "!vlu": "Value",
}
# the heads of the columns of the tabs Parameters, Settings and Methods
# (§3.1)
VALUE_HEADS = {
    "Parameters": ["Parameter", "Set", "Value"],
    "Settings": ["Setting", "Set", "Value"],
    "Methods": ["Target", "Method", "Bound"],
}


def test_task_29_the_fields_tab_takes_the_capitals_and_the_faces_of_design_pass_6(
    page, server_on, durables_folder
):
    """Task 29 (AAS, L-D24 and L-D28; design pass 6 §§3 to 5). With the
    durables model's keeper_cons.bl open at 1600 × 1000, as the page opens
    (K-D22), each table's title reads `≺ Arrival`, `∼ Decision` or
    `≻ Continuation`, its sign in ice-3 at weight 400 and its word in
    Archivo at 13 px, weight 600, in ice, 14 px from the table's left edge,
    its hover the sentence of §3.7; its heads read `Field`, `Set` and
    `Role`, in Archivo at 11 px, weight 500, in ice-3, neither letter-spaced
    nor transformed, each with its hover. Every name, set and role reads
    as `model.classification` gives it, in IBM Plex Mono at 11 px, weight
    400, names in ice and sets and roles in ice-2, a role's hover the role
    in words. The title line, the head row, every field row and the add
    row are each 24 px high; one hairline stands under the head row and one
    above the add row, and no field cell draws a border. The add row is the
    table's last row, its entries and `+` at one top; `+` is a 24 × 24 px
    target whose cell ends at the table's right edge, the icon button of
    VSCode Elements drawing the Codicon `add` at 16 px in ice-2 (design pass
    8 §3; unit M, Task 6), with no text, its hover `Add field` and its
    accessible name `Add field at arrival`, `at decision` or `at
    continuation`; the entries read `New field` and `Set`, in
    Archivo at 11 px in the panel's placeholder color. The three tables
    stand at one top, each 189 px wide, a third of the 39 px the text
    column gained when the window's left padding left with the rail (unit
    N, Task 1) over the 176 px before; every set and role holds its text
    whole, and every name prints whole. At rest no set or role draws a
    border or a ground. Under the pointer a set draws a 1-px border in the
    control border on ice at 7 percent, with the radius of 4 px, as every
    cell of the Types tables does (design pass 8 §5.3; the delegated
    acceptance of unit M, D5), 3 px beyond its text on each side, its text
    where it stood, and a role's box runs to the table's right edge with its
    chevron; focused, a set's border is ultramarine-light. The main bar's
    toggles are named `Files`, `Inspector`, `Details` and `Matsya` (unit N,
    Task 1; N-D4), the one panel's head `Details` with the stage file open,
    the panel under the editor having its strip in place of a head (unit
    N, Task 2; design pass 10 §4), and the tabs Parameters, Settings
    and Methods head their columns with a capital. Escape in the decision
    group's add row empties its entries and returns its role to `state`;
    Enter in its field entry adds the field as `+` does, writing lines 15
    and 21, and the file on disk is unchanged."""
    url = server_on(durables_folder)
    original = (durables_folder / KEEPER_CONS).read_text(encoding="utf-8")
    stage = bound_as_the_recipe_binds(durables_folder, original, KEEPER_CONS)
    expected = {
        f"{group.perch}/{group.branch or ''}": [
            (row.field, row.set, row.role) for row in group.rows
        ]
        for group in model.classification(stage, source_spans(original, KEEPER_CONS))
    }
    open_file(page, url, KEEPER_CONS)
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)
    page.evaluate("() => document.fonts.ready.then(() => null)")
    ice, ice_2, ice_3 = (
        property_color(page, name) for name in ("--bl-ice", "--bl-ice-2", "--bl-ice-3")
    )
    hairline = property_color(page, "--bl-hairline")
    control = property_color(page, "--bl-control-border")
    light = property_color(page, "--bl-ultramarine-light")
    placeholder = page.evaluate(PANEL_COLOR_JS, "--bl-class-placeholder")
    fill = page.evaluate(PANEL_COLOR_JS, "--bl-class-cell-fill")
    transparent = "rgba(0, 0, 0, 0)"
    unspaced = {"face": "Archivo", "spacing": "normal", "transform": "none"}

    groups = page.evaluate(FIELDS_TAB_JS)
    assert [group["group"] for group in groups] == list(expected) == ["arvl/", "dcsn/", "cntn/"]
    glyphs = page.locator(".bl-class-group .bl-add-button .codicon").evaluate_all(ADD_GLYPHS_JS)
    assert len(glyphs) == len(groups), glyphs
    for group, glyph in zip(groups, glyphs):
        group["add"]["icon"] = [group["add"]["icon"], *glyph]
    assert len({round(group["table"]["top"], 1) for group in groups}) == 1, groups
    for group in groups:
        title, heads, rows, add = group["title"], group["heads"], group["rows"], group["add"]
        widest = max(row["fieldWidth"] for row in rows)
        print(f"task 29: {group['group']} {group['table']['width']:.1f} px, names {widest:.1f}")
        # 1, the panel's words
        assert (title["text"], title["hover"]) == FIELDS_TITLES[group["perch"]], title
        assert (title["word"]["face"], title["word"]["size"]) == ("Archivo", "13px"), title
        assert (title["word"]["weight"], title["word"]["color"]) == ("600", ice), title
        assert (title["sign"]["weight"], title["sign"]["color"]) == ("400", ice_3), title
        assert abs(title["wordLeft"] - group["table"]["left"] - 14) <= 0.5, title
        assert [head["text"] for head in heads] == ["Field", "Set", "Role"], heads
        assert [head["hover"] for head in heads] == FIELDS_HEAD_HOVERS, heads
        for head in heads:
            drawn = head["type"]
            assert {key: drawn[key] for key in unspaced} == unspaced, head
            assert (drawn["size"], drawn["weight"], drawn["color"]) == ("11px", "500", ice_3)
        word = FIELDS_TITLES[group["perch"]][0].split(" ")[1].lower()
        assert add["placeholders"] == ["New field", "Set"], add
        named = ("Add field", f"Add field at {word}", "")
        assert (add["hover"], add["label"], add["text"]) == named, add
        assert add["icon"] == ["add", "16px", "codicon", ice_2], add
        drawn = add["placeholderType"]
        assert (drawn["face"], drawn["size"], drawn["color"]) == ("Archivo", "11px", placeholder)
        # 2, the file's words
        printed = [(row["field"], row["set"], row["role"]) for row in rows]
        assert printed == expected[group["group"]], rows
        for row in rows:
            for kind, color in (("field", ice), ("set", ice_2), ("role", ice_2)):
                drawn = row[f"{kind}Type"]
                mono = ("IBM Plex Mono", "11px", "400", color)
                assert (drawn["face"], drawn["size"], drawn["weight"], drawn["color"]) == mono, row
            assert row["setHover"] == row["set"], row
            assert row["roleHover"] == ROLE_HOVERS[row["role"]], row
        # 3, rows and rules
        heights = [title["box"]["height"], group["headRow"]["height"], add["box"]["height"]]
        heights += [row["box"]["height"] for row in rows]
        assert all(abs(height - 24) <= 0.5 for height in heights), heights
        for head in heads:
            assert hairline in head["shadow"] and "0px -1px 0px 0px inset" in head["shadow"]
        for shadow in add["shadows"]:
            assert hairline in shadow and "0px 1px 0px 0px inset" in shadow, add
        for row in rows:
            assert {tuple(cell) for cell in row["cells"]} == {("0px",) * 4 + ("none",)}, row
        # 4, the add row on one line
        assert add["last"], add
        tops = [entry["top"] for entry in add["entries"]] + [add["button"]["top"]]
        assert max(tops) - min(tops) <= 0.5, add
        button, end = add["button"], add["end"]
        assert abs(button["width"] - 24) <= 0.5 and abs(button["height"] - 24) <= 0.5, add
        assert end["left"] - 0.5 <= button["left"] and button["right"] <= end["right"] + 0.5
        assert abs(end["right"] - group["table"]["right"]) <= 0.5, add
        # 5, nothing cut at the opening size
        assert abs(group["table"]["width"] - 189) <= 1, group["table"]
        for row in rows:
            assert row["fieldWhole"] and row["setWhole"] and row["roleWhole"], row
        # 6, cells at rest
        for row in rows:
            assert row["setRest"] == row["roleRest"] == [transparent, transparent], row

    # 6, a set under the pointer and focused, and a role under the pointer
    first = '.bl-class-group[data-group="arvl/"] tbody tr:first-child'
    page.hover(f"{first} .bl-class-set")
    found = page.evaluate(FIELDS_CELL_JS, f"{first} .bl-class-set")
    assert (found["border"], found["ground"]) == (["1px", control], fill), found
    assert found["radius"] == "4px", found
    text = found["holder"]["left"] + found["padding"]
    assert abs(found["text"] - text) <= 0.5, found
    assert abs(found["box"]["left"] - (text - 3)) <= 0.5, found
    assert abs(found["box"]["right"] - (found["holder"]["right"] + 3)) <= 0.5, found
    page.hover(f"{first} .bl-class-role")
    found = page.evaluate(FIELDS_CELL_JS, f"{first} .bl-class-role")
    assert (found["border"], found["ground"]) == (["1px", control], fill), found
    assert found["radius"] == "4px", found
    assert abs(found["box"]["right"] - found["table"]["right"]) <= 0.5, found
    assert found["chevron"], found
    page.mouse.move(0, 0)
    page.focus(f"{first} .bl-class-set")
    found = page.evaluate(FIELDS_CELL_JS, f"{first} .bl-class-set")
    assert found["border"] == ["1px", light], found

    # L-D28: the toggles' names, the panels' heads and the other tabs' heads
    toggles = page.locator(".bl-main-bar .bl-toggle")
    named = toggles.evaluate_all("(found) => found.map((b) => b.getAttribute('aria-label'))")
    assert named == ["Files", "Inspector", "Details", "Matsya"]
    names = page.locator(".bl-window .bl-region-head .bl-region-name").all_text_contents()
    assert names == ["Details"]
    for tab, heads in VALUE_HEADS.items():
        page.click(f'.bl-class-tab[data-tab="{tab}"]')
        shown = f'.bl-values[data-tab="{tab}"] .bl-values-table th'
        page.wait_for_selector(shown, timeout=10_000)
        assert page.locator(shown).all_text_contents() == heads, tab
    page.click('.bl-class-tab[data-tab="Fields"]')
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)

    # §3.6: Escape empties the add row, and Enter adds the field as `+` does
    row = page.locator('.bl-class-group[data-group="dcsn/"] .bl-add-field')
    field, kind, role = (
        row.locator(f'[data-entry="{name}"]') for name in ("field", "set", "role")
    )
    field.fill("x")
    kind.fill("ℝ")
    role.select_option("!vlu")
    field.press("Escape")
    assert [field.input_value(), kind.input_value(), role.input_value()] == ["", "", "state"]
    line_15 = original.split("\n")[14].replace(
        "z_d : ℝ₊₊) : !dcsn]", "z_d : ℝ₊₊, q : ℝ₊) : !dcsn]"
    )
    line_21 = original.split("\n")[20].replace(
        "c : ℝ₊₊ @ !ctrl) : !dcsn", "c : ℝ₊₊ @ !ctrl, q) : !dcsn"
    )
    written = edited(edited(original, 15, line_15), 21, line_21)
    field.fill("q")
    kind.fill("ℝ₊")
    field.press("Enter")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == written, 5.0, "q on lines 15 and 21")
    assert (durables_folder / KEEPER_CONS).read_text(encoding="utf-8") == original


# Each wire the region draws between two boxes, [the box it leaves, the box
# it reaches, its label or null, whether it is a bundle of a pair within a
# period, the count its bus mark prints or null], the boxes read from the
# wire's id, `<box>::out::<port>>><box>::in::<port>`; the shared pieces of
# unit K's decision K-D5, whose ids name no box, are left out (design pass
# 13 §1, rules 5 and 7).
PAIR_WIRES_JS = r"""
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge'))
  .filter((edge) => edge.dataset.id.includes('::out::'))
  .map((edge) => {
    const id = edge.dataset.id, label = edge.querySelector('.bf-join'), count = edge.querySelector('.bf-cable-count');
    return [id.split('::out::')[0], id.split('>>')[1].split('::in::')[0],
            label ? label.textContent : null, edge.classList.contains('bf-pair-bundle'),
            count ? count.textContent : null];
  })
"""
# The hovers of the wires the region draws from the box `from` to the box
# `to`, the text of each title (design pass 13 §1, rule 7; AAS, L-D25).
CABLE_TITLE_JS = r"""
([from, to]) => Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge'))
  .filter((edge) => edge.dataset.id.startsWith(from + '::out::')
    && (edge.dataset.id.split('>>')[1] || '').startsWith(to + '::in::'))
  .map((edge) => (edge.querySelector('title') || {}).textContent || '')
"""
# The hover of the join wire whose record runs from the stage occurrence
# `from` to `to`, the text of its title, null where none is drawn (J-D33;
# a cable of the backward graph since design pass 12 §2).
JOIN_TITLE_JS = r"""
([from, to]) => {
  const edge = document.querySelector(
    `.bl-view-host .react-flow__edge.bf-join-wire[data-from="${from}"][data-to="${to}"]`);
  return edge ? (edge.querySelector('title') || {}).textContent || '' : null;
}
"""
# the ground of a builder's segment by its pair (design pass 14 §9; S-D14,
# which amends design pass 13 §2, rule 5 and Q-D18): mint for the builder
# that joins the arrival perch, orange for the one that joins the
# continuation perch, and the policy builder's share of ice over the lit navy
PAIR_GROUNDS = {"arvl,dcsn": "mint", "cntn,dcsn": "orange", "dcsn,cntn": "orange", "dcsn,arvl": "mint"}
PAIR_GROUNDS["policy"] = POLICY_SHARE


def occurrence_of(namespace: str) -> str | None:
    """The stage occurrence `periods[h]/<key>` a namespace stands in, or
    None for a namespace outside every occurrence."""
    parts = namespace.split("/")
    return "/".join(parts[:2]) if len(parts) >= 2 and parts[0].startswith("periods[") else None


def pairs_within(graph: dict) -> Counter:
    """The ordered pairs of stage occurrences of one period that the trellis
    graph `graph` joins by wires, each with the number of the writers'
    outputs its wires come from, read from the graph JSON alone (AAS,
    L-D25)."""
    namespaces = {node["id"]: node.get("namespace") or "" for node in graph["nodes"]}
    outputs: dict[tuple, set] = {}
    for node in graph["nodes"]:
        reader = occurrence_of(namespaces[node["id"]])
        for edge in node.get("incomingEdges") or []:
            writer = occurrence_of(namespaces[edge["sourceNodeId"]])
            if (
                reader
                and writer
                and writer != reader
                and writer.split("/")[0] == reader.split("/")[0]
            ):
                outputs.setdefault((writer, reader), set()).add(
                    (edge["sourceNodeId"], edge["sourceNodeOutputId"])
                )
    return Counter({pair: len(found) for pair, found in outputs.items()})


def wires_within(tab) -> Counter:
    """The number of wires the region draws for each ordered pair of stage
    occurrences of one period (PAIR_WIRES_JS)."""
    found = Counter()
    for source, target, _, _, _ in tab.evaluate(PAIR_WIRES_JS):
        writer, reader = (box[: -len(LAYER_ID_ENDING)] for box in (source, target))
        if (
            occurrence_of(writer) == writer
            and occurrence_of(reader) == reader
            and writer.split("/")[0] == reader.split("/")[0]
        ):
            found[writer, reader] += 1
    return found


def unjoined_names(graph: dict, occurrence: str) -> list[str]:
    """The names a card of the stage occurrence `occurrence` of the trellis
    graph `graph` prints while it is not selected (AAS, L-D25): one for
    each field port of its own `Inputs` and `Outputs` that no join
    reaches, with no perch's sign, in the order of its ports, the reading
    side first."""
    return [
        name.split(": ")[-1].rstrip("≺≻")
        for key in ("inputsMetadata", "outputsMetadata")
        for node in graph["nodes"]
        if node.get("namespace") == occurrence
        for port in node.get(key) or []
        if re.search(r"/unjoined:[^/]+$", port["id"])
        for name in [next(a["value"] for a in port["attrs"] if a["key"] == "label")]
    ]


def test_task_30_a_card_prints_its_name_alone_and_one_bundle_joins_each_pair_within_a_period(
    browser, server_on, durables_folder, tmp_path
):
    """Task 30 (AAS, L-D25; design pass 7 §§3 to 5, measures 1 to 4 and
    6). On the durables model's backward and forward trellis graphs,
    periods 0 to 2, at the opening: every card, its fields all joined, is
    32 ± 1 px high at scale 1 and 80 px or wider (design pass 13 §2), its
    element holding one text node, its name (measure 1); its strip holds
    one segment per builder of the drawn direction, the stage's builders
    graph's, each in its pair's color, mint for the builder that joins the
    arrival perch, orange for the one that joins the continuation perch
    and ice at 34 percent over the lit navy for the policy builder (design
    pass 14 §9; S-D14), and no text (measure 2); no card prints a field's
    name, at the reading scale, at 0.9 and at 1, and no change of the scale
    lays the graph out again (measure 3); each ordered pair of stage
    occurrences of one period that the graph JSON joins has one wire, a
    cable counting its wires at its plug where they come from two or more
    outputs and printing no label but its branch's name (measure 4; design
    pass 13 §1, rules 5 and 7). The forward graph opens on its terminal
    period at the largest scale, at most 1 and at least 0.6, at which that
    period fills the region, each card 32 px high at scale 1 on the screen
    there (measure 6, as M-D15 amends it).
    Selected, `keeper_cons` of periods[0] unfolds: its band holds each
    builder's signs and id; in the forward graph its pairs' bundles stand
    split, one wire for each output, every other pair keeping one label
    (measures 2 and 4), and in the backward graph every pair keeps its one
    cable, the cable of its route's values, which nothing splits (design
    pass 12 §2). In the backward graph a click on the cable from `bequest`
    to `adjuster_cons`, whose hover lists its wires' labels and its route's
    pairs, selects it as one cable, which Details names by its route, and
    every pair keeps one label; a click on the graph's ground ends the
    selection and the drawing stands as it stood (design pass 12 §2, where
    the click split the bundle into its wires, drawn lit). In the forward
    graph, `keeper_cons` selected, a click on
    its join wire to `bequest` selects it, and its reading end dropped on
    `adjuster_cons`'s arrival port opens the cable's list, one row for each
    of the two arrival fields of `adjuster_cons`, which cancel closes,
    sending nothing (unit J's gestures on the split wires, through the
    cable's ports since unit N's Task 7; design pass 10 §§6–7). On the
    portfolio model, its connector and its inter-period mapping emptied,
    the forward graph opens on its terminal period by the same rule; each
    card prints the names of its unjoined fields alone; with `cons` of
    periods[0] selected, the drag from `port`'s branch port, whose `m_next`
    no join reads, to `cons`'s arrival port, the one port the drag admits,
    opens the cable's list, in which `m_next` chosen for `m` and `join`
    send the event `connected` with that one pair, marked as the whole
    cable's (unit J's drag)."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        G = tab.evaluate("() => window.BellmanFlowLayout.G")
        held = tab.evaluate(HELD_COLLECTION_JS)
        record_layouts(tab)
        # each graph chosen, so that its layout is recorded
        for direction in ("forward", "backward"):
            choose_view(tab, None, direction)
            wait_until(
                lambda direction=direction: tab.locator(
                    f'.bl-graph-bar[data-graph="{direction}"]'
                ).count()
                == 1
                and tab.evaluate(CARD_JS, KEEPER_CONS_LAYER) is not None,
                60.0,
                f"the {direction} graph's cards",
            )
            wait_until(lambda: view_still(tab, 1000), 30.0, f"the {direction} graph at rest")
            zoom = viewport(tab)["zoom"]
            if direction == "forward":
                # measure 6: the forward graph opens on its terminal period (M-D15)
                assert terminal_opening(tab, f"periods[0]{LAYER_ID_ENDING}"), viewport(tab)
            graph = graph_named(held, direction)
            opened = sorted(
                namespace
                for namespace in flow_handle(tab, "openLayers")
                if namespace.count("/") == 1 and namespace.startswith("periods[")
            )
            assert len(opened) == 10, opened
            layers = {node.get("namespace") or "" for node in graph["nodes"]}
            for namespace in opened:
                box = namespace + LAYER_ID_ENDING
                found = tab.evaluate(CARD_JS, box)
                # measure 1: 32 px high, 80 px or wider, its name its one text
                assert found["nodes"] == [namespace.split("/")[1]], (namespace, found["nodes"])
                assert abs(found["size"][1] - CARD_JOINED) <= 1, (namespace, found["size"])
                assert found["size"][0] >= CARD_LEAST, (namespace, found["size"])
                card_bands(found, zoom, G)
                if direction == "forward":
                    high = found["card"]["bottom"] - found["card"]["top"]
                    assert round(high) == round(CARD_JOINED * zoom), (namespace, high, zoom)
                # measure 2: a segment per builder, tinted by its pair, no text
                builders = sorted(
                    {ns.split("/")[2] for ns in layers if ns.startswith(namespace + "/")}
                )
                segments = tab.evaluate(BUILDER_BOXES_JS, box)
                assert (
                    sorted(
                        s["id"].split("/")[2][: -len(LAYER_ID_ENDING)]
                        for s in segments["builders"]
                    )
                    == builders
                ), namespace
                for segment, ground in zip(segments["builders"], perch_grounds(segments)):
                    assert segment["text"] == "", segment
                    expected_ground = PAIR_GROUNDS[segment["pair"]]
                    if isinstance(expected_ground, float):
                        assert abs(ground - expected_ground) <= 0.01, (segment, ground)
                    else:
                        assert ground == expected_ground, (segment, ground)
            # measure 4: one wire for each ordered pair within a period, its count at its plug
            pairs = pairs_within(graph)
            assert wires_within(tab) == Counter(dict.fromkeys(pairs, 1)), direction
            print(f"task 30: {direction}, wires within a period by pair {dict(pairs)}")
            # measure 3: no name at the reading scale, at 0.9 or at 1, and no
            # layout run again
            counted = layouts_recorded(tab)
            view = viewport(tab)
            for scale in (READING_SCALE, 0.9, 1.0, zoom):
                flow_handle(
                    tab,
                    "setView",
                    {
                        "viewport": {"x": view["x"], "y": view["y"], "zoom": scale},
                        "selection": None,
                    },
                )
                wait_until(lambda: view_still(tab, 1000), 30.0, f"the view at {scale}")
                for namespace in opened:
                    found = tab.evaluate(CARD_JS, namespace + LAYER_ID_ENDING)
                    assert found["texts"] == [], (scale, namespace, found["texts"])
            assert layouts_recorded(tab) == counted

            # keeper_cons selected: its band prints the signs and the ids; in
            # the forward graph its pairs' bundles split, every other pair one
            # label (L-D25); in the backward graph every pair keeps its one
            # cable, which nothing splits (design pass 12 §2)
            tab.click(f'.react-flow__node[data-id="{KEEPER_CONS_LAYER}"] .bf-layer-name')
            keeper = "periods[0]/keeper_cons"
            split = Counter(
                {
                    pair: count if keeper in pair and direction == "forward" else 1
                    for pair, count in pairs.items()
                }
            )
            wait_until(
                lambda: wires_within(tab) == split,
                30.0,
                f"the {direction} pairs with keeper_cons selected",
            )
            expected = (
                KEEPER_CONS_BACKWARD
                if direction == "backward"
                else DURABLES_FORWARD["keeper_cons"]
            )
            compact_builders(tab, KEEPER_CONS_LAYER, expected, band=True)
            card_bands(tab.evaluate(CARD_JS, KEEPER_CONS_LAYER), zoom, G, band=True)
            # the card unfolded, the layout drawn again, the pairs as they stood
            assert wires_within(tab) == split, direction

            if direction == "backward":
                # a click on the cable from `bequest` to `adjuster_cons`, whose
                # record names its route from `adjuster_cons` into `bequest`,
                # selects it as one cable, which Details names by its route,
                # every pair keeping one label; Escape ends the selection and
                # the drawing stands as it stood (design pass 12 §2)
                tab.keyboard.press("Escape")
                wait_until(
                    lambda: wires_within(tab) == Counter(dict.fromkeys(pairs, 1))
                    and view_still(tab, 500),
                    30.0,
                    "the pairs with no card selected",
                )
                ends = ("periods[0]/bequest", "periods[0]/adjuster_cons")
                route = ("periods[0]/adjuster_cons", "periods[0]/bequest")
                # the layout drawn again once the card's selection ends, the
                # cable takes its record again before its title names it
                title, _ = wait_until(
                    lambda: tab.evaluate(JOIN_TITLE_JS, list(route)),
                    10.0,
                    "the cable from bequest to adjuster_cons with its record",
                )
                lines = title.split("\n")
                assert len(lines) == 1 + pairs[ends] and "→" in lines[-1], title
                click_join(tab, *route)
                wait_until(
                    lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]]
                    == [route],
                    10.0,
                    "the cable from bequest to adjuster_cons selected",
                )
                (head, rows), _ = wait_until(
                    # a join's head in sentence case (Q3b, item 19; C12)
                    lambda: (found := tab.evaluate(DETAILS_ROWS_JS))[0].startswith("Join") and found,
                    10.0,
                    "Details of the selected cable",
                )
                assert dict(rows)["route"] == [f"{route[0]} ≻ → {route[1]} ≺"], (head, rows)
                assert wires_within(tab) == Counter(dict.fromkeys(pairs, 1))
                tab.keyboard.press("Escape")
                wait_until(
                    lambda: not [w for w in join_wires_drawn(tab) if w["selected"]],
                    10.0,
                    "the selection of the cable ended",
                )
                assert wires_within(tab) == Counter(dict.fromkeys(pairs, 1))
            else:
                # unit J's gestures on a split wire of keeper_cons's pairs, the
                # card selected: the join wire to `bequest`, which a connector
                # writes, selected, and its reading end moved through the
                # pairing list, which cancel closes
                bequest = "periods[0]/bequest"
                hold_events(tab, "moved")
                click_join(tab, keeper, bequest)
                wait_until(
                    lambda: [w["to"] for w in join_wires_drawn(tab) if w["selected"]] == [bequest],
                    10.0,
                    "the join wire selected",
                )
                # the reading end dropped on adjuster_cons's arrival port opens the
                # cable's list, one row per arrival field of adjuster_cons (design
                # pass 10 §7)
                move_join_end(tab, keeper, bequest, "target", cable_port(tab, "periods[0]/adjuster_cons", "reading"))
                pair_list = ".bl-view-host .bf-pair-list"
                tab.wait_for_selector(pair_list, timeout=10_000)
                assert tab.locator(f"{pair_list} .bf-pair-row").count() == 2
                tab.click(f"{pair_list} .bf-pair-cancel")
                tab.wait_for_selector(pair_list, state="detached")
                assert release_events(tab, "moved") == []
    finally:
        context.close()

    # the portfolio model, its connector and inter-period mapping emptied
    copy = emptied_portfolio(tmp_path / "portfolio")
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        lay_out_left_to_right(tab)
        record_layouts(tab)
        choose_view(tab, None, "forward")
        writing = "periods[0]/port/unjoined:port:cntn:m_next"
        reading = "periods[0]/cons/unjoined:cons:arvl:m"
        wait_until(
            lambda: writing in unjoined_field_ids(tab), 60.0, "the forward graph's unjoined ports"
        )
        wait_until(lambda: view_still(tab, 1000), 30.0, "the forward graph at rest")
        assert terminal_opening(tab, f"periods[0]{LAYER_ID_ENDING}"), viewport(tab)
        graph = graph_named(tab.evaluate(HELD_COLLECTION_JS), "forward")
        cards = sorted(
            namespace
            for namespace in flow_handle(tab, "openLayers")
            if namespace.count("/") == 1 and namespace.startswith("periods[")
        )
        assert cards
        for namespace in cards:
            found = tab.evaluate(CARD_JS, namespace + LAYER_ID_ENDING)
            assert printed_fields(found) == unjoined_names(graph, namespace), namespace
        # unit J's drag, cons selected and its wires split
        cons = "periods[0]/cons" + LAYER_ID_ENDING
        tab.click(f'.react-flow__node[data-id="{cons}"] .bf-layer-name')
        wait_until(
            lambda: (tab.evaluate(CARD_JS, cons) or {}).get("texts", []) != []
            and len(printed_fields(tab.evaluate(CARD_JS, cons))) > 1,
            30.0,
            "cons unfolded",
        )
        # the drag from port's branch port to cons's arrival port opens the
        # cable's list, whose one row takes `m_next` for `m`, and `join` sends
        # the event with the one pair, marked as the whole cable's (design pass
        # 10 §7)
        hold_events(tab, "connected")
        state = drag_cable(tab, "periods[0]/port", "", "periods[0]/cons", {reading: writing})
        assert state["valid"] == [cable_port(tab, "periods[0]/cons", "reading")], state
        (event,) = held_events(tab, "connected")
        assert (event["source"], event["target"], event["pairs"], event["cable"]) == (
            "periods[0]/port" + LAYER_ID_ENDING,
            cons,
            [{"sourceHandle": writing, "targetHandle": reading}],
            True,
        )
    finally:
        context.close()


# Each label a wire prints in the region (unit K's decision K-D4), [its
# text, its font style, its font family], read from the label's element.
LABEL_FACES_JS = r"""
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge .bf-join'), (text) => {
  const style = getComputedStyle(text);
  return [text.textContent, style.fontStyle, style.fontFamily];
})
"""
# The first line of the title of each cable of a branch the region draws, its
# branch's name, a cable of a branch standing in a route whose bundle's id
# ends in its branch, `…|keep` (the fix wave Q3a of unit Q, item 4)
BRANCH_TITLES_JS = r"""
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge.bf-cable-edge'))
  .filter((edge) => /\|(keep|adjust)>>/.test(edge.dataset.id || '') || /:(keep|adjust)>>/.test(edge.dataset.id || ''))
  .map((edge) => (edge.querySelector('title') || {textContent: ''}).textContent.split('\n')[0])
"""
# the label of the bundle from `bequest` to `keeper_cons` in periods[0] of
# the durables model's backward trellis graph: the value and the two
# marginal values `keeper_cons` reads at its continuation, in the order its
# file first lists them, `V[>]` and `dV_h[>]` in `cntn_to_dcsn`, `dV_a[>]`
# in `policy` (AAS, L-D26)
BEQUEST_KEEPER_VALUES = ("𝑉", "𝑑𝑉_h", "𝑑𝑉_a")
# The hovers of the cables' ports the region shows on the cards, a hidden
# port of an arrival tuple left out (design pass 10 §6; unit N, Task 7): a
# joined port's hover names the functions its cable carries, as the reading
# stage names them, `𝑉_kp, 𝑑𝑉_w_kp, 𝑑𝑉_h_kp` (AAS, L-D26), and an open
# port's hover its own label, `𝑉≺(a, h, z)`.
CABLE_PORT_HOVERS_JS = r"""
() => Array.from(document.querySelectorAll(
  '.bl-view-host .bf-card > .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)'),
  (port) => port.getAttribute('title') || '')
"""


def test_task_31_the_backward_trellis_labels_its_wires_with_the_values_in_italic(
    browser, server_on, durables_folder
):
    """Task 31 (AAS, L-D26; design pass 7 §3, measure 5), as unit N's Task
    7, design pass 13 §1, rules 5 and 7, and the fix wave Q3a of unit Q,
    item 4, amend it: a cable draws no label, its branch's name standing
    first in its title, its count stands at its plug, and the names of the
    functions the joins carry, the value and the marginal values, which
    the canvas printed before, stand in the hovers of the cable's ports. On
    the durables model's backward trellis graph, periods 0 to 2, at the
    opening, the region draws no wire's label, no state field a join names
    nor a function's name, and each cable of a branch begins its title
    with the branch's name; the hovers of the
    cables' ports the region shows name every function a join carries, as
    the reading stage names it and as the package prints a function, its
    letters in mathematical italic, and no other name in italic. The cable
    from `bequest` to `keeper_cons` counts its three wires at its plug,
    `3`, prints no label, its route having no branch, and its own hover,
    its wires' labels as the writing stage prints them (L-D25), names `𝑉,
    𝑑𝑉_h, 𝑑𝑉_a`; with `keeper_cons` selected, the cable from `bequest`
    stands whole, one cable counting the three functions it carries
    (design pass 12 §§2 and 3, where the selection split it into three wires
    that each printed that count). The forward graph draws no wire's label
    either, its cables of a branch beginning their titles with it."""
    bequest, keeper = (f"periods[0]/{key}{LAYER_ID_ENDING}" for key in ("bequest", "keeper_cons"))

    def from_bequest() -> list[tuple]:
        # the wires from `bequest` to `keeper_cons`, each (label, count)
        return [
            (label, count)
            for source, target, label, _, count in tab.evaluate(PAIR_WIRES_JS)
            if (source, target) == (bequest, keeper)
        ]

    def cable_label(text: str) -> bool:
        # a cable's label: its branch's name (design pass 13 §1, rule 7)
        return text in {"keep", "adjust"}

    def named_at_ports() -> set[str]:
        # the functions named in the hovers of the cables' ports, each
        # written as the package writes a function's name; a port's label
        # also names the state fields of its arguments, which are no
        # function's name
        return {
            name
            for hover in tab.evaluate(CABLE_PORT_HOVERS_JS)
            for name in re.findall(r"[^\s,()≺≻]+", hover)
            if in_function_italic(name)
        }

    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        held = tab.evaluate(HELD_COLLECTION_JS)
        backward, forward = (graph_named(held, direction) for direction in ("backward", "forward"))
        choose_view(tab, None, "backward")
        wait_until(
            lambda: tab.locator('.bl-graph-bar[data-graph="backward"]').count() == 1
            and from_bequest() == [(None, "3")],
            60.0,
            "the backward graph's cable from bequest to keeper_cons, counting its three wires",
        )
        drawn = tab.evaluate(LABEL_FACES_JS)
        print(f"task 31: backward labels {sorted({text for text, _, _ in drawn})}")
        states = joined_states(backward)
        # no wire's label, a cable of a branch beginning its title with the branch (the fix wave Q3a, item 4)
        assert drawn == [], drawn
        branched = tab.evaluate(BRANCH_TITLES_JS)
        assert branched and all(cable_label(first) and first not in states for first in branched), branched
        # the functions' names stand in the hovers of the cables' ports,
        # every function a join carries named as the reading stage names it,
        # and nothing else in mathematical italic
        functions = named_at_ports()
        hovers = tab.evaluate(CABLE_PORT_HOVERS_JS)
        assert functions == carried_functions(backward), (functions, hovers)
        assert not functions & states and set(BEQUEST_KEEPER_VALUES) <= functions, functions
        # the cable's own hover lists its wires' labels, as the writing stage
        # prints them, then their joins (AAS, L-D25): the cable from `bequest`
        # to `keeper_cons` names the value and its two marginal values
        titles = tab.evaluate(CABLE_TITLE_JS, [bequest, keeper])
        assert titles and all(
            set(BEQUEST_KEEPER_VALUES)
            <= {re.split(r"[≺≻(]", line)[0].strip() for line in title.split("\n")}
            for title in titles
        ), titles

        # keeper_cons selected, its card unfolded and the layout drawn again:
        # the cable from bequest stands whole, one cable counting at its plug
        # the three functions it carries (design pass 12 §§2 and 3, one cable
        # for each route, which nothing splits, counting its value functions)
        tab.click(f'.react-flow__node[data-id="{KEEPER_CONS_LAYER}"] .bf-layer-name')
        # the band of the selected card is drawn with the layout of the selection
        compact_builders(tab, KEEPER_CONS_LAYER, KEEPER_CONS_BACKWARD, band=True)
        assert from_bequest() == [(None, "3")], from_bequest()
        tab.keyboard.press("Escape")

        choose_view(tab, None, "forward")
        wait_until(
            lambda: tab.locator('.bl-graph-bar[data-graph="forward"]').count() == 1
            and tab.locator('.bl-view-host .react-flow__edge.bf-cable-edge[data-id*="Pushforward"]').count() > 0,
            60.0,
            "the forward graph's cables",
        )
        fields = joined_states(forward)
        assert tab.evaluate(LABEL_FACES_JS) == [], tab.evaluate(LABEL_FACES_JS)
        branched = tab.evaluate(BRANCH_TITLES_JS)
        assert branched and all(cable_label(first) and first not in fields for first in branched), branched
    finally:
        context.close()


# --- the fix wave of unit L (the final judgment of 10 October 2026, §6) ---


def test_fix_item_11_a_panel_folded_while_it_stands_wide_leaves_no_ground(page, server):
    """The final judgment of unit L, §6 item 11 (AAS, L-D12): with cons.bl
    open and the BellmanType panel shown in its wide panel over its ground,
    the main bar's toggle `Inspector` (unit N, Task 1; N-D4), pressed by the
    keyboard, folds the panel, and neither the wide panel nor its ground
    then stands over the window; pressed again, it opens the panel in its
    column."""
    open_cons(page, server)
    page.click('.bl-classification[data-panel="types"] .bl-region-wide')
    page.wait_for_selector(".bl-classification.bl-wide", timeout=10_000)
    page.wait_for_selector(".bl-wide-ground", timeout=10_000)
    toggle = page.locator('.bl-main-bar .bl-fold[data-fold="inspector"]')
    toggle.focus()
    page.keyboard.press("Enter")
    wait_until(lambda: page.locator(".bl-wide-ground").count() == 0, 10.0, "the ground gone")
    assert not page.locator(".bl-classification").is_visible()
    assert toggle.get_attribute("aria-expanded") == "false"
    page.keyboard.press("Enter")
    wait_until(lambda: page.locator(".bl-classification").is_visible(), 5.0, "types opened")
    assert page.locator(".bl-classification.bl-wide").count() == 0


# For each group of the Fields tab whose table holds the box `add field`,
# the right edge of its last head's box and of what that head draws before
# it, its ground and its hairline over `+`'s column, null where it draws
# nothing, and the right edge of the table.
HEAD_RULE_JS = """
() => Array.from(document.querySelectorAll('.bl-class-scroll'))
  .filter((scroll) => scroll.querySelector('tfoot'))
  .map((scroll) => {
    const table = scroll.querySelector('.bl-class-table');
    const head = table.querySelector('th:last-child');
    const drawn = getComputedStyle(head, '::before');
    const right = head.getBoundingClientRect().right;
    return {
      head: right,
      rule: drawn.content === 'none' ? null : right + parseFloat(drawn.width),
      shadow: drawn.boxShadow,
      table: table.getBoundingClientRect().right,
    };
  })
"""


def test_fix_item_12_the_head_row_s_hairline_runs_across_the_column_of_plus(page, server):
    """The final judgment of unit L, §6 item 12 (Task 27's review, Minor 2):
    in each table of the Fields tab of cons.bl that holds the box `add
    field`, the head row's ground and hairline reach the table's right
    edge across `+`'s column, which no head names."""
    open_cons(page, server)
    page.wait_for_selector(".bl-class-tables tfoot", timeout=30_000)
    heads = page.evaluate(HEAD_RULE_JS)
    assert len(heads) == 3, heads
    for head in heads:
        assert head["table"] - head["head"] > 20, head
        assert head["rule"] is not None and abs(head["rule"] - head["table"]) < 0.5, head
        assert head["shadow"] != "none", head


def test_fix_item_12_the_list_of_a_move_takes_the_page_s_primary_modifier_alone(
    browser, server_on, scratch_durables
):
    """The final judgment of unit L, §6 item 12 (Task 23's review, Minor 1;
    design pass 4 §2a): in the cable's list that the move of a cable's
    reading end opens, its end dropped on another occurrence's arrival port
    (design pass 10 §7; unit N, Task 7), on a copy of the durables model
    under `periods 0–2`, Enter with the modifier that is not the page's
    primary one, Control on macOS and Command elsewhere, presses nothing,
    as in window.vue's forms, and the list stands; Enter with the primary
    modifier presses `join`, which closes the list and sends the move."""
    copy = scratch_durables
    writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
    pair_list = ".bl-view-host .bf-pair-list"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        record_layouts(tab)
        choose_view(tab, None, "forward")
        mac = tab.evaluate("() => navigator.platform.startsWith('Mac')")
        primary, other = ("Meta", "Control") if mac else ("Control", "Meta")
        hold_events(tab, "moved")
        # the wire drawn and the view at rest before the click, so that the
        # opening's view does not move the wire from under the pointer
        wait_until(
            lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the join wire from keeper_cons to tenure drawn",
        )
        wait_until(lambda: view_still(tab, 1000), 30.0, "the forward graph at rest")
        click_join(tab, writer, reader)
        wait_until(
            lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]]
            == [(writer, reader)],
            10.0,
            "the join wire selected",
        )
        # the reading end dropped on bequest's arrival port, the per-field
        # ports having left the cards (design pass 10 §6)
        bequest = cable_port(tab, "periods[0]/bequest", "reading")
        move_join_end(tab, writer, reader, "target", bequest)
        tab.wait_for_selector(pair_list, timeout=10_000)
        # the first row ticked with the first port its select offers, so
        # that `join` acts
        row = tab.locator(f"{pair_list} .bf-pair-row").first
        row.locator(".bf-pair-tick").click()
        select = row.locator("select")
        offered = select.evaluate("(s) => Array.from(s.options, (o) => o.value).filter(Boolean)")
        select.select_option(value=offered[0])
        assert cable_list(tab)["join"] is True
        assert tab.locator(f"{pair_list} .bf-pair-join").get_attribute("title") is None
        row.locator(".bf-pair-tick").focus()
        tab.keyboard.press(f"{other}+Enter")
        tab.wait_for_timeout(500)
        assert tab.locator(pair_list).count() == 1
        assert held_events(tab, "moved") == []
        tab.keyboard.press(f"{primary}+Enter")
        tab.wait_for_selector(pair_list, state="detached", timeout=10_000)
        assert len(held_events(tab, "moved")) == 1
    finally:
        context.close()
