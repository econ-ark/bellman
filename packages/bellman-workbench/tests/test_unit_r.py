"""The acceptance tests of unit R of model interface specification 0.4,
Design brief 7 (brief §3): one test for each of items 1 to 5; item 6 is
AAS's reading. Deleted when the next amendment is accepted (lean
implementation rule, layer 2).
"""

from __future__ import annotations

import hashlib
import math
import shutil
import urllib.request

from workbench_support import (
    ANNOTATED_LINES_JS,
    BLUR_JS,
    BOX_MEASURES_JS,
    CAGETTI_DENARDI,
    CLASSIFICATION_PANEL_JS,
    COLOR_OF_JS,
    COLUMN_ACTIONS_JS,
    CONS,
    CONTRAST_EXCEPTIONS,
    DOCUMENT_JS,
    ENTREPRENEUR_DEATH_PATH,
    FLOW_FILES,
    FLOW_README,
    FONT_FILES,
    FONTS_README,
    FRAME_TRACKS,
    GROUND_JS,
    GROUNDS_OF_JS,
    GROUP_HEAD,
    HANDLE_NAMES_JS,
    HELD_COLLECTION_JS,
    ICON_BUTTONS,
    KEEP_FOCUS_JS,
    KEPT_FOCUS_JS,
    KEY_PREVENTED_RECORDER_JS,
    LINT_RANGE_JS,
    MATSYA_FOLD,
    MATSYA_FOLDED_TRACKS,
    MATSYA_TOGGLE,
    MINIMAP_COLORS,
    MOTION_JS,
    NAMELESS_JS,
    OFF_TRACKS,
    OPACITY_OF_JS,
    OTHER_ICONS_JS,
    PASSIVE_LINE_NUMBER,
    PORT,
    PREVIEW_LINES_JS,
    RECIPE_FILE,
    RESTRICTION,
    ROOT,
    ROW_HEIGHTS,
    SCROLL_EDITOR_JS,
    SELECTED_TEXT_JS,
    SIZES,
    STATES,
    STUB_PASSAGES,
    SURFACES,
    TABLE_ROWS_JS,
    TEXT_WIDTH_JS,
    TOKEN_COLORS,
    TRELLIS_TRACKS,
    VIEW_OPACITY_JS,
    VIEW_STATE_JS,
    WORKBENCH,
    active_line,
    add_field,
    animations_during,
    annotated_line,
    attribute_of,
    boxes,
    breadcrumb,
    build_record,
    choose_restriction,
    choose_view,
    click_before,
    click_line,
    contrast_faults,
    digest7,
    drag_handle,
    edited,
    editor_handle,
    error_count,
    file_tabs,
    flow_handle,
    focus_faults,
    focus_region,
    folder_rows,
    fonts_drawn,
    git_line_sentence,
    goto_command,
    goto_results,
    graph_named,
    history_buttons,
    layout_record,
    line_text,
    lines_holding,
    measure_faults,
    measures,
    minimap_marks,
    occurrence_head,
    open_cons,
    open_file,
    open_goto,
    open_path_shown,
    orange_marks,
    origin_alone,
    outline_faults,
    panel_head,
    press_in_region,
    press_outside_fields,
    property_color,
    recipe_head,
    record_layouts,
    replace_in_editor,
    restrict,
    restriction_shown,
    reveal_in_tree,
    select_node,
    settled_status,
    show_state,
    stage_name,
    status_place,
    symbol_faces,
    tab_closes,
    token_style,
    tracks,
    tracks_near,
    type_of,
    view_options,
    view_shown,
    view_still,
    viewport,
    visible_in_viewport,
    wait_until,
    wash_color,
    write_refused_cons,
)

from bellman_workbench import matsya_client, model

# the running heads of spec 0.4 §5.1: the graph's name in its bar and the
# h2 of Matsya's head, the text's head having left with unit N's Task 1
# (design pass 10 §2)
RUNNING_HEADS = ".bl-graph-bar .bl-graph-name, .bl-matsya-head > h2"
# the folds window.vue keeps for a folder, every region of the main bar's
# toggles open (unit L, Task 12; AAS, L-D12; unit N, Task 1)
OPEN_FOLDS = {region: False for region in ("folder", "inspector", "details", "matsya")}


def test_item_1_the_window_stands_in_the_frames_measures_and_folds_and_narrows_in_order(
    page, server, model_folder, server_on, cagetti_folder, scratch_consport, scratch_folder
):
    """Item 1, first part (spec 0.4 §5.1; brief rules 2 and 3; R-D14,
    R-D15, R-D30, R-D31): the folder opens on its recipe with every folder
    of the tree closed but `declaration/`, the one folder on the recipe's
    path (R-D52). With cons.bl open at 1600 × 1000, the four
    columns have the widths FRAME_TRACKS gives, with the folder open and
    with the folder folded by the main bar's toggle `Files` (unit N, Task
    1; design pass 10 §3), its hover `Files`, whose `aria-expanded` follows
    the fold and whose folder hides its tree while folded; the
    main bar and the status line end at the graph column's right
    edge, and Matsya's column spans the window's rows (Task 12). A drag of
    the handle `folder` stops at 170 px; a drag of the handle `file` stops
    at 300 px for the text to the left and at 300 px for the graph to the
    right; a drag of the handle `matsya` to the right stops at 300 px; a
    double click on a handle returns the frame's widths. Matsya folded by
    the button of its head takes no width, its column 0 px wide and the
    text and the graph sharing the rest (MATSYA_FOLDED_TRACKS; unit K's
    decision K-D19), and opened again by the main bar's toggle `Matsya`
    has the frame's width. At 1800, 1460, 1446 and 1380 px the columns
    narrow in the order of §5.1, the width function folding the folder at
    1380 px, each step 120 px lower than before the window's left padding
    left with the rail (unit N, Task 1) and its right margin of 60 px with
    design pass 13 §4 (Q-D6). At 1140 px the width function
    folds the folder and stores no fold; `Save`, `Types` and the main bar
    stand whole
    in the viewport; a click on `Files` opens the folder, the text giving
    up width to its least, where the BellmanType panel's head scrolls its
    context sideways and no part of its controls is drawn beyond the text's
    column (R-D32), and the tree's root row is visible, the recipe having
    left the folder column for the panel under the editor (unit M, Task 10;
    design pass 9 §5).

    The boxes (spec 0.4 §5.3; R-D49): each box of cons.bl's backward graph
    prints its label, its symbol with its method mark, and nothing else, no
    label of an output port among it; each output port keeps its label as
    its title and at the head of its accessible description; an operator's
    box is as wide as its label as drawn with its two 1 px borders and its
    9 px paddings, or 140 px, the least width of a box, so that
    `dcsn_to_arvl:Aggregation`, whose label is `𝐺`, is 140 px wide.

    The head (spec 0.4 §§5.1 and 5.2; brief rule 4; Design brief 7 §§2, 6
    and 7): the mark, the silhouette, is 20 px high at the main bar's left
    (design pass 10 §3), and no wordmark is drawn (design pass 8 §8, item
    5; unit M, Task 4), whether the folder is open or folded; no running
    head `BellmanSym` stands; the Files head, the tabs' row and the graph
    bar, which holds `Semantic graph`, begin on one line under the main bar
    (design pass 10 §2), and Matsya's head stands at the window's top, 36
    px high, level with the main bar (design pass 8 §6; unit M, Tasks 6 and
    7); the running heads, the tabs, the buttons, the path, in Code small
    since design pass 10 §3, and the tree's files have the faces and the
    sizes of SIZES, the tabs, `Save` and the tree's files in the system of
    design pass 8 (unit M, Task 6); the Files head, the tabs' row, the
    graph bar, 36 px or, where its items take further rows, a whole number
    of rows of 36 px (amendment 02 ruling 5), and the tree's rows have the
    heights of
    ROW_HEIGHTS. With `entrepreneur_death.bl` of cagetti-denardi-2006 open
    at 1600 × 1000, the tree's rows, whose names are longer than the folder
    is wide, are still one row high, and `Types` and `Save` stand left of
    the handle between the text and the graph and clear of the graph's
    name (ruling R-P15).

    The legend in Details (spec 0.4 §§2.1 and 5.5; brief rule 6; G-R23,
    G-R76; R-D36; unit K, Task 3): with nothing selected and with a box
    selected, it stands under a `details` element whose summary reads
    `legend`, the last element of Details' body, and the graph's viewport,
    its place, its scale and the host's size, is unchanged by the
    selection.

    The five states (spec 0.4 §8, R item 1; brief §4; R-D12): at 1600 ×
    1000, with cons.bl constructed, with its backward initial diagram, with
    the trellis PORT_CONS of cons-port, six periods, with a refusal of
    cons.bl made by an edit after a construction, and with a refusal before
    any construction, cons.bl holding the refused text on disk before the
    page opens, the window's measures equal the tables within 1 px: the
    columns FRAME_TRACKS, the rows ROW_HEIGHTS, the status line's among
    them, and the space above it, the grounds SURFACES and the faces and
    sizes SIZES, a size exactly. Every region of SURFACES is drawn but the
    palette, which is closed, the user messages, of which there are none,
    and, in the trellis's state, the BellmanType panel, which a trellis
    file has not. The trellis's state folds Matsya, the graph taking its
    width (TRELLIS_TRACKS; unit K's decision K-D6), and is measured with
    Matsya opened by the main bar's toggle `Matsya` (K-D19; unit N, Task
    1)."""
    # the tree as the folder opens on its recipe: the rows drawn are the
    # folders of the folder's top and of `declaration/`, all closed but
    # `declaration/`
    page.goto(server)
    page.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{RECIPE_FILE}"]', timeout=60_000)
    entries = model.folder_tree(model.open_folder(model_folder))
    folders = [entry for entry in entries if entry["kind"] == "folder"]
    declaration = next(entry for entry in folders if entry["path"] == "declaration")
    folders += [entry for entry in declaration["children"] if entry["kind"] == "folder"]
    assert folder_rows(page) == {entry["path"]: entry is not declaration for entry in folders}

    open_cons(page, server)
    # a box prints its label and nothing else, each port's label in its
    # title and its accessible description, an operator's box as wide as
    # its label as drawn, which the bundle does not measure here
    measured = page.evaluate(BOX_MEASURES_JS)
    for node in graph_named(page.evaluate(HELD_COLLECTION_JS), "backward")["nodes"]:
        box = measured[node["id"]]
        assert box["text"] == node["label"], node["id"]
        labels = [attribute_of(port, "label") for port in node.get("outputsMetadata") or []]
        # a bundle of value wires leaves by its first wire's port, whose title lists the label of every wire drawn
        # at it, one per line (design pass 14 §1, rule 5; S-I3), so the lines of the drawn ports' titles are the
        # labels of the node's ports, and a port's description opens with its own label, the title's first line
        assert [line for title, _ in box["outputs"] for line in title.split("\n")] == labels, node["id"]
        assert all(about.startswith(title.split("\n")[0]) for title, about in box["outputs"]), node["id"]
        if box["role"] == "label":
            assert box["width"] == max(140, math.ceil(box["measure"] + 2 + 2 * 9)), node["id"]
    assert measured["dcsn_to_arvl:Aggregation"]["width"] == 140
    fold = page.locator('.bl-fold[data-fold="folder"]')
    assert tracks_near(page, FRAME_TRACKS[1600, False]), tracks(page)
    assert [fold.get_attribute(name) for name in ("aria-label", "title", "aria-expanded")] == [
        "Files",
        "Files",
        "true",
    ]
    # the main bar and the status line end at the graph's column; Matsya's
    # column spans the window's rows, from the main bar's top to the status
    # line's foot
    regions = (".bl-view", ".bl-matsya", ".bl-main-bar", ".bl-status")
    view, matsya, main_bar, status = (boxes(page, selector)[0] for selector in regions)
    assert abs(main_bar["right"] - view["right"]) <= 1, (main_bar, view)
    assert abs(status["right"] - view["right"]) <= 1, (status, view)
    assert abs(matsya["top"] - main_bar["top"]) <= 1, (matsya, main_bar)
    assert abs(matsya["bottom"] - status["bottom"]) <= 1, (matsya, status)

    # the mark, the running heads, the sizes and the rows of the head
    assert boxes(page, ".bl-main-bar .bl-mark img")[0]["height"] == 20
    assert page.locator(".bl-wordmark").count() == 0
    assert page.locator(RUNNING_HEADS).all_text_contents() == ["Semantic graph", "Matsya"]
    # the graph's name and Matsya's head in Head (design pass 8 §5.5; unit
    # M, Tasks 6 and 7), the columns' first rows on one line under the main
    # bar, Matsya's head from the window's top, level with the main bar
    # (design pass 8 §6; design pass 10 §2)
    assert type_of(page, RUNNING_HEADS) == [SIZES["head"], SIZES["head"]]
    tops = {box["top"] for box in boxes(page, ".bl-folder-rail, .bl-tab-row, .bl-graph-bar")}
    assert tops == {36}, tops
    matsya_head = boxes(page, ".bl-matsya-head")[0]
    assert (matsya_head["top"], matsya_head["height"]) == (0, 36), matsya_head
    assert type_of(page, ".bl-tab") == [SIZES["tab"]] * len(file_tabs(page))
    # `Save`, a button of VSCode Elements in Label (design pass 8 §5.3; unit
    # M, Task 6); the graph's view tabs in Label (unit M, Task 7); the
    # folder's `New trellis` and the graph's `Perch overlays` are icon
    # buttons and draw no words (design pass 8 §4)
    assert type_of(page, ".bl-save") == [SIZES["control"]]
    buttons = ".bl-stage-button, .bl-trellis-button"
    assert set(type_of(page, buttons)) == {SIZES["button"]}
    # the path in Label (design pass 13 §3; C4)
    assert type_of(page, ".bl-crumbs") == [SIZES["label"]]
    assert set(type_of(page, ".bl-tree-file")) == {SIZES["tree"]}
    heads = [box["height"] for box in boxes(page, ".bl-folder-rail")]
    assert heads == [ROW_HEIGHTS["column head"]]
    rows = [box["height"] for box in boxes(page, ".bl-tab-row, .bl-tab")]
    assert rows == [ROW_HEIGHTS["bar"]] * len(rows)
    rows = boxes(page, ".bl-graph-bar")[0]["height"] / ROW_HEIGHTS["graph bar"]
    assert rows >= 1 and abs(rows - round(rows)) < 0.02, rows
    tree = {box["height"] for box in boxes(page, ".bl-folder-row, .bl-tree-file")}
    assert tree == {ROW_HEIGHTS["tree"]}

    # the legend under `legend` at the end of Details, before and after a
    # box is selected (unit K, Task 3), the graph's host keeping its size
    # and the view its place
    folded = ".bl-panel > .bl-panel-body > details.bl-legend-details:last-child > .bl-legend"
    assert page.locator(folded).count() == 1
    opened = viewport(page)
    select_node(page, "policy:Evaluation", "backward")
    wait_until(lambda: panel_head(page) != "", 10.0, "the box selected")
    assert page.locator(folded).count() == 1
    assert page.locator(".bl-legend").count() == 1
    assert page.locator(".bl-legend-details > summary").text_content() == "Legend"
    assert viewport(page) == opened

    # the reader folds the folder and opens it again
    fold.click()
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, True]), 5.0, "the folder folded")
    assert fold.get_attribute("aria-expanded") == "false"
    assert page.locator(".bl-window").get_attribute("data-folded-folder") is not None
    assert not page.locator(".bl-tree").is_visible()
    assert boxes(page, ".bl-main-bar .bl-mark img")[0]["height"] == 20
    fold.click()
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "the folder opened")
    assert fold.get_attribute("aria-expanded") == "true"
    assert page.locator(".bl-tree").is_visible()

    # the drags stop at the least widths of §5.1 and R-D14; at 1600 px the
    # graph and Matsya hold 34 px above theirs, which a drag of the folder
    # may take
    drag_handle(page, "folder", 30)
    wait_until(lambda: abs(tracks(page)[0] - 200) <= 1, 5.0, "the folder at 200 px")
    drag_handle(page, "folder", -200)
    wait_until(lambda: abs(tracks(page)[0] - 170) <= 1, 5.0, "the folder stopped at 170 px")
    drag_handle(page, "file", -900)
    wait_until(lambda: abs(tracks(page)[1] - 300) <= 1, 5.0, "the text stopped at 300 px")
    drag_handle(page, "file", 900)
    wait_until(lambda: abs(tracks(page)[2] - 300) <= 1, 5.0, "the graph stopped at 300 px")
    page.locator('.bl-handle[data-handle="file"]').dblclick()
    page.locator('.bl-handle[data-handle="folder"]').dblclick()
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "the frame's widths")
    drag_handle(page, "matsya", 200)
    wait_until(lambda: abs(tracks(page)[3] - 300) <= 1, 5.0, "Matsya stopped at 300 px")
    page.locator('.bl-handle[data-handle="matsya"]').dblclick()
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "Matsya's frame width")

    # the reader folds Matsya by the button of its head, its column then
    # taking no width, and opens it again by the main bar's toggle (K-D19;
    # unit L, Task 12)
    matsya_fold, matsya_toggle = page.locator(MATSYA_FOLD), page.locator(MATSYA_TOGGLE)
    assert matsya_fold.get_attribute("aria-expanded") == "true"
    assert matsya_toggle.get_attribute("aria-expanded") == "true"
    matsya_fold.click()
    wait_until(lambda: tracks_near(page, MATSYA_FOLDED_TRACKS), 5.0, "Matsya folded")
    assert matsya_fold.get_attribute("aria-expanded") == "false"
    assert matsya_toggle.get_attribute("aria-expanded") == "false"
    assert page.locator(".bl-window").get_attribute("data-folded-matsya") is not None
    assert boxes(page, ".bl-matsya")[0]["width"] == 0
    assert not page.locator(".bl-matsya-exchanges").is_visible()
    matsya_toggle.click()
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "Matsya opened")

    # the narrowing order: Matsya to 300 px, the graph to 300 px, then the
    # folder folded
    for width in (1800, 1460, 1446, 1380):
        page.set_viewport_size({"width": width, "height": 1000})
        wait_until(
            lambda width=width: tracks_near(page, FRAME_TRACKS[width, False]),
            5.0,
            f"the columns at {width} px",
        )
    assert fold.get_attribute("aria-expanded") == "false"
    page.set_viewport_size({"width": 1140, "height": 1000})
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1140, False]), 5.0, "the narrowed columns")
    assert fold.get_attribute("aria-expanded") == "false"
    assert layout_record(page, model_folder) is None
    assert visible_in_viewport(page, ".bl-save")
    assert visible_in_viewport(page, ".bl-types-button")
    assert visible_in_viewport(page, ".bl-main-bar .bl-fold[data-fold=\"matsya\"]")
    fold.click()
    wait_until(lambda: abs(tracks(page)[0] - 170) <= 1, 5.0, "the folder opened at 1200 px")
    assert tracks(page)[1] >= 299 and abs(tracks(page)[2] - 300) <= 1
    # the BellmanType panel's strip, wider than the text at its least
    # width, scrolls its tabs sideways as the tabs' row does (R-D32; unit N,
    # Task 2): the part of each control of the strip that the browser
    # draws, its intersection rectangle, ends within the text's column; the
    # strip's control is VSCode Elements' icon button `open wide` (design
    # pass 8 §4; unit M, Task 6)
    drawn = page.evaluate(
        """() => new Promise((resolve) => {
          const controls = document.querySelectorAll(
            '.bl-classification[data-panel="types"] .bl-inspector-strip vscode-toolbar-button');
          const rights = new Map();
          const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => rights.set(entry.target, entry.intersectionRect.right));
            if (rights.size === controls.length) {
              observer.disconnect();
              resolve(Math.max(...rights.values()));
            }
          });
          controls.forEach((control) => observer.observe(control));
          if (!controls.length) resolve(Infinity);
        })"""
    )
    assert drawn <= boxes(page, ".bl-file")[0]["right"] + 1, drawn
    assert fold.get_attribute("aria-expanded") == "true"
    assert visible_in_viewport(page, ".bl-tree .bl-tree-root")
    assert layout_record(page, model_folder) is None

    # a stage file with a long path keeps its buttons in the text's column
    page.set_viewport_size({"width": 1600, "height": 1000})
    stage_file = (ROOT / ENTREPRENEUR_DEATH_PATH).relative_to(CAGETTI_DENARDI).as_posix()
    open_file(page, server_on(cagetti_folder), stage_file, minimum=4)
    tree = {box["height"] for box in boxes(page, ".bl-folder-row, .bl-tree-file")}
    assert tree == {ROW_HEIGHTS["tree"]}
    handle = boxes(page, '.bl-handle[data-handle="file"]')[0]
    heading = boxes(page, ".bl-graph-bar .bl-graph-name")[0]
    for selector in (".bl-types-button", ".bl-save"):
        button = boxes(page, selector)[0]
        assert button["right"] <= handle["left"], (selector, button, handle)
        assert (
            button["right"] <= heading["left"]
            or heading["right"] <= button["left"]
            or button["bottom"] <= heading["top"]
            or heading["bottom"] <= button["top"]
        ), (selector, button, heading)

    # the five states: the columns, the rows, the grounds and the type of
    # the tables
    write_refused_cons(scratch_folder)
    urls = {
        "trellis": server_on(scratch_consport),
        "refused before a construction": server_on(scratch_folder),
    }
    for state in STATES:
        show_state(page, state, urls.get(state, server))
        if state == "trellis":
            wait_until(
                lambda: tracks_near(page, TRELLIS_TRACKS[1600, False]), 10.0, "Matsya folded"
            )
            page.click(MATSYA_TOGGLE)
            wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "Matsya opened")
        found = measures(page)
        assert measure_faults(found, FRAME_TRACKS[1600, False]) == [], state
        regions = set(SURFACES) - {"Goto Anything", "user messages"}
        if state == "trellis":
            regions -= {"BellmanType panel"}
        assert set(found["grounds"]) == regions, state


def test_item_2_decorations_keep_bytes_and_addresses_and_the_panes_keep_their_links_and_each_file_is_written_once(  # noqa: E501  (the name the plan gives the test)
    page, server, model_folder, original
):
    """Item 2, first part (spec 0.4 §5.1; brief rule 4; R-D4, R-D32): text
    typed in cons.bl, then port.bl opened from the tree and typed in. The
    tabs stand in the order the files were opened, the recipe's first, since
    the folder opens on its trellis with the recipe as text, then cons.bl
    and port.bl, each of these two reading `unsaved`, port.bl's active. A
    click on the tab of cons.bl gives the editor cons.bl's typed text, and
    the name on the active tab reads `cons.bl` with cons.bl's path. Neither
    file on disk has changed.

    The token colors (spec 0.4 §5.2; brief rule 5; R-D18): each token of
    TOKEN_COLORS, a perch tag and a role tag among them, has the color of
    its custom property of brand.css, its weight and its style.

    The decorations (spec 0.4 §§5.2 and 5.4; brief rule 5; R-D26, R-D34):
    the stage name `cons` on line 1 is drawn at 18/24 px in Archivo, in ice
    and at the width --bl-stage-name-stretch gives, on a line 24 px high
    (L-D3);
    every line of cons.bl that holds `::` is drawn as a statement and its
    annotation. The editor's document is the file's bytes with the
    decorations drawn, with the types hidden, line 8's annotation then
    reading `:: [util]`, and with the types shown again. A click before a
    token, of the statement and of the annotation of an annotated line and
    of the stage name, then the key X, puts X at that token's offset in the
    file's text, and one undo restores the bytes; before the key, the
    status line's place reads the token's line and column, counted in code
    points as the file's text counts them (spec 0.4 §5.7; R-D20). A refusal
    of line 22, an annotated line, written through the search panel, is
    underlined from the package's line and column; one undo restores the
    bytes.

    The text minimap (spec 0.4 §5.4; brief rule 5; review 4; R-D35): a
    strip 60 px wide at the editor's right edge, beside the text, which
    still holds 78 characters on its first visual line in a window of
    2200 px, wide enough for them, on a ground of 4 percent ice and hidden
    from assistive technology. It holds one mark per
    line of the file, 2 px high and 1 px apart, 0.6 px wide per character
    up to 56 px. The header marks are the lines whose first character that
    is no white space opens a group GROUP_HEAD matches; the stage name's
    line is `stage`; the mark of an annotated statement is an ordinary
    line's, of the same kind and color; each kind has its color of §5.4. A
    click on the mark of a header line and on that of line 24 makes each
    the active line, the document unchanged; the key X then stands at the
    start of line 24, and one undo restores the bytes.

    The lower panes (spec 0.4 §5.5; brief rule 6; review 13; R-D23,
    R-D36; ruling R-P9): at 1600 × 1000 the three perch tables of Fields
    stand on one top, each 12 px right of the one before, under the titles
    `≺ Arrival`, `∼ Decision` and `≻ Continuation` in Archivo at 13 px,
    headed `Field`, `Set` and `Role` (unit L, Task 29; design pass 6 §§3.1
    and 3.3, AAS, L-D24), with no line column; the button of the field c,
    whose accessible description
    is `line 17`, focused and given Enter, makes line 17 the active line.
    The bar of the BellmanType panel holds no state of the loop, which the
    status line prints, `constructed` (R-D50). The panel has one height on
    its four tabs, at its default and at 120 px dragged on its handle, each
    tab's content standing inside it and scrolling, Methods' content taller
    than the dragged panel; a double click on the handle returns the
    default (R-D51). Details is headed `Details` (unit L, Task 29; L-D28),
    and a key of its rows is
    64 px wide in IBM Plex Mono at 10.5 px. In each of Parameters, Settings
    and Methods, the button of a row's name, whose accessible description is
    the row's file and line, focused and given Enter, opens that file with
    that line active, and the tree opens the folders on its path, so that
    its row is seen (R-D52).

    The panel under a refusal (R-D57; amendment 02 rulings 7 to 10): `h`,
    `ℝ₊`, `state` added in the continuation table is written on line 17,
    which the editor then selects whole, and the package refuses the text,
    since no line defines h. The tables stay editable, read from the text:
    the row of h stands, its field text with no link to a box, in orange,
    the package's sentence its hover, and no other row is marked. `k` added
    next is written after h. A later text that does not parse leaves the
    tables of the last parse, h and k among them, dimmed and locked; one
    undo makes them editable again. The two equations `h = a` and `k = a`
    typed in the editor construct the stage again: the mark goes and the
    field h links to its box. Three undos return the file's text.

    The button `paper` (spec 0.4 §5.5; brief rule 7; R-D17, R-D41): with
    the builder `policy` selected, a click writes `paper/cons.md` and
    `paper/cons.svg`, which then stand, the button is omitted, and git's
    line and the status line's note print `paper/cons.md written with
    paper/cons.svg` (ruling R-P6); the two files are removed again, so that
    the session's folder stays as copied.
    With a key typed in the editor and the loop's answer to that text
    shown, the builder still selected, no button stands.

    The button `notebook` (spec 0.4 §5.9; brief rule 7; R-D41, R-D42), the
    last of the folder's buttons: a click writes
    `notebooks/<folder>.ipynb`, which then stands alone in `notebooks/`, the
    button is omitted, and the status line's note prints
    `notebooks/<folder>.ipynb written`; the open file, its text and the tabs
    are unchanged. The folder is removed again.

    The tabs' close controls (R-D53; amendment 02 rulings 1 and 2; design
    pass 8 §§3 and 5.5): each tab holds the icon button `close`, named
    `Close` and the file's name, its hover `Close`; the controls of cons.bl
    and port.bl, unsaved, are disabled, their hover `Save the file first.`,
    the control under the pointer at its center, so that the hover is
    shown, and a click on one closes nothing. The open file's close control
    closes its tab and opens the tab to its left; the recipe's, its tab not
    open, closes its tab alone. Neither unsaved file on disk has
    changed."""
    port_text = (model_folder / PORT).read_text(encoding="utf-8")
    kept = edited(original, 1, "@stage: cons  # kept")
    open_cons(page, server)
    tokens = {
        text: {"color": property_color(page, name), "weight": weight, "style": style}
        for text, (name, weight, style) in TOKEN_COLORS.items()
    }
    assert {text: token_style(page, text) for text in TOKEN_COLORS} == tokens

    # the stage name and the annotated lines, the bytes unchanged
    lines = original.split("\n")
    name = stage_name(page)
    assert name is not None and name["text"] == "cons"
    drawn = {"face": "Archivo", "size": 18.0, "lineHeight": 24.0}
    drawn.update(color=property_color(page, "--bl-ice"), stretch=name["stretch"])
    assert name["styles"] == [drawn]
    assert [round(box["height"], 1) for box in boxes(page, ".cm-content .bl-stage-line")] == [24]
    annotated = [number for number, text in enumerate(lines, 1) if "::" in text]
    assert page.evaluate(ANNOTATED_LINES_JS) == annotated
    assert page.evaluate(DOCUMENT_JS) == original
    page.click(".bl-types-button")
    wait_until(lambda: line_text(page, 13) == "[arvl_to_dcsn] {", 5.0, "line 13 as its name")
    assert annotated_line(page, 8)["annotation"]["text"] == ":: [util]"
    assert page.evaluate(ANNOTATED_LINES_JS) == annotated
    assert page.evaluate(DOCUMENT_JS) == original
    page.click(".bl-types-button")
    wait_until(lambda: line_text(page, 13) == lines[12], 5.0, "line 13 in full")
    assert page.evaluate(DOCUMENT_JS) == original

    # the text minimap: one mark per line, its kind and its measures
    colors = {kind: wash_color(page, *wash) for kind, wash in MINIMAP_COLORS.items()}
    assert page.locator(".bl-editor .bl-minimap").count() == 1
    strip, editor, scroller = (
        boxes(page, f".bl-editor {selector}")[0]
        for selector in (".bl-minimap", ".cm-editor", ".cm-scroller")
    )
    assert strip["width"] == 60 and abs(strip["right"] - editor["right"]) < 0.5, strip
    assert scroller["right"] <= strip["left"] + 0.5, (scroller, strip)
    assert page.evaluate(GROUND_JS, ".bl-editor .bl-minimap") == colors["ground"]
    assert page.get_attribute(".bl-editor .bl-minimap", "aria-hidden") == "true"
    # the text beside the strip holds 78 characters on its first visual line
    # in a window wide enough for them, 2200 px as test_lines_wrap_at_column_78
    # opens it, since at 1600 px the text's column is frame 7b's 568 px,
    # which holds fewer (spec 0.4 §5.1; Task 12)
    page.set_viewport_size({"width": 2200, "height": 1000})
    wait_until(lambda: tracks(page)[1] > 900, 5.0, "the text's column at 2200 px")
    width, column = page.evaluate(TEXT_WIDTH_JS)
    assert abs(width + 4 * column - 78 * column) < 1, (width, column)
    page.set_viewport_size({"width": 1600, "height": 1000})
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "the frame's widths")
    marks = minimap_marks(page)
    assert [mark["line"] for mark in marks] == list(range(1, len(lines) + 1))
    headers = [number for number, text in enumerate(lines, 1) if GROUP_HEAD.match(text.lstrip())]
    assert headers and [mark["line"] for mark in marks if mark["kind"] == "header"] == headers
    assert [mark["line"] for mark in marks if mark["kind"] == "stage"] == [1]
    assert {(marks[number - 1]["kind"], marks[number - 1]["color"]) for number in annotated} == {
        ("line", colors["line"])
    }
    for mark, text in zip(marks, lines):
        assert mark["color"] == colors[mark["kind"]], mark
        # at most 44 px, the strip's 60 px less 4 px inside its left edge
        # and 12 px inside its right (the fix wave Q3b of unit Q, item 18; D17)
        assert abs(mark["width"] - min(0.6 * len(text), 44)) < 0.02 and mark["height"] == 2, mark
    assert {after["top"] - before["top"] for before, after in zip(marks, marks[1:])} == {3}

    # a click on a mark puts the cursor at its line's start and writes nothing
    for number in (31, 24):
        page.mouse.click(strip["left"] + 30, marks[number - 1]["top"] + 1)
        wait_until(lambda number=number: active_line(page) == number, 5.0, f"line {number}")
    assert page.evaluate(DOCUMENT_JS) == original
    page.keyboard.type("X")
    typed = edited(original, 24, "X" + lines[23])
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == typed, 5.0, "X at the start of line 24")
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of X")

    # a click before a token puts the cursor at the token's offset
    for number, token in ((8, ":="), (8, "[id=util]"), (32, "!doc"), (1, "cons")):
        text = lines[number - 1]
        at = text.index(token)
        typed = edited(original, number, text[:at] + "X" + text[at:])
        click_before(page, number, token)
        # the status line's place is the token's line and column in code
        # points, as the file's text gives them
        wait_until(
            lambda number=number, at=at: status_place(page) == f"{number}:{at + 1}",
            5.0,
            f"the place {number}:{at + 1}",
        )
        page.keyboard.type("X")
        wait_until(
            lambda typed=typed: page.evaluate(DOCUMENT_JS) == typed,
            5.0,
            f"X before {token!r} on line {number}",
        )
        page.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of X")

    # a refusal of an annotated line is underlined at the package's column
    find, refusing = "𝑢(c) + V[>]", "𝑢(c) + - V[>]"
    (diagnostic,) = model.elaborate_buffer(original.replace(find, refusing), CONS).diagnostics
    assert (diagnostic.line, diagnostic.column) == (22, 17)
    replace_in_editor(page, find, refusing)
    page.wait_for_selector(".cm-content .cm-lintRange-error", timeout=8_000)
    underlined = page.evaluate(LINT_RANGE_JS)
    assert (underlined["line"], underlined["column"]) == (22, 17), underlined
    click_line(page, 1)
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of the refusal")
    wait_until(lambda: page.evaluate(LINT_RANGE_JS) is None, 8.0, "the refusal withdrawn")

    # the Fields tab: three tables side by side, 12 px apart (unit L, Task
    # 29; design pass 6 §3.3), no line column, a field's name a button that
    # moves the editor by the keyboard alone
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)
    sections = boxes(page, ".bl-class-perch")
    assert len(sections) == 3 and {section["top"] for section in sections} == {sections[0]["top"]}
    for before, after in zip(sections, sections[1:]):
        assert abs(after["left"] - before["right"] - 12) < 0.5, (before, after)
    titles = page.locator(".bl-class-perch-name")
    assert titles.all_text_contents() == ["≺ Arrival", "∼ Decision", "≻ Continuation"]
    assert type_of(page, ".bl-class-perch-name") == [SIZES["prose"]] * 3
    assert page.locator(".bl-class-table th").all_text_contents() == ["Field", "Set", "Role"] * 3
    field = page.locator('.bl-class-row[data-identity="cons:dcsn:c"] button.bl-class-field')
    assert field.get_attribute("aria-description") == "line 17"
    assert field.get_attribute("data-line") == "17"
    click_line(page, 1)
    wait_until(lambda: active_line(page) == 1, 5.0, "the cursor on line 1")
    field.focus()
    page.keyboard.press("Enter")
    wait_until(lambda: active_line(page) == 17, 5.0, "the editor on line 17")
    assert page.evaluate(DOCUMENT_JS) == original

    # a field added in the panel refuses the construction, and the tables
    # stay editable, read from the text: the row the refusal names is orange
    # with the package's sentence as its hover, and the new field links to no
    # box; a second field is added after it (R-D57; amendment 02 rulings 7
    # to 9)
    header = lines[16]
    one = edited(original, 17, header.replace("(a : Xa)", "(a : Xa, h : ℝ₊)"))
    two = edited(original, 17, header.replace("(a : Xa)", "(a : Xa, h : ℝ₊, k : ℝ₊)"))
    (refusal,) = model.elaborate_buffer(one, CONS).diagnostics
    assert "'cons:cntn:h'" in refusal.message
    row_h = page.locator('.bl-class-row[data-identity="cons:cntn:h"]')
    marked = page.locator(".bl-class-row.bl-refusal-mark")
    add_field(page, "cntn/", "h", "ℝ₊", "state")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == one, 5.0, "h written on line 17")
    wait_until(
        lambda: page.evaluate(SELECTED_TEXT_JS) == one.split("\n")[16], 5.0, "line 17 selected"
    )
    assert settled_status(page, digest7(one))["state"] == "parsed, refused"
    row_h.wait_for(timeout=5_000)
    wait_until(lambda: marked.count() == 1, 5.0, "the row the refusal names marked")
    assert page.locator(".bl-class-tables.bl-stale").count() == 0
    assert marked.get_attribute("data-identity") == "cons:cntn:h"
    assert row_h.get_attribute("title") == refusal.message
    orange = property_color(page, "--bl-orange")
    assert page.evaluate(COLOR_OF_JS, '[data-identity="cons:cntn:h"] .bl-class-field') == orange
    assert row_h.locator("button.bl-class-field").count() == 0
    assert page.locator('[data-identity="cons:dcsn:c"] button.bl-class-field').is_enabled()
    assert page.locator('[data-identity="cons:dcsn:c"] .bl-class-set').is_enabled()

    def continuation() -> list[str]:
        # the fields of the continuation table, in its order
        return [row["field"] for row in page.evaluate(TABLE_ROWS_JS) if row["perch"] == "cntn"]

    add_field(page, "cntn/", "k", "ℝ₊", "state")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == two, 5.0, "k written after h")
    assert settled_status(page, digest7(two))["state"] == "parsed, refused"
    rows = ["a", "h", "k", "V[>]", "dV[>]"]
    wait_until(lambda: continuation() == rows, 5.0, "the rows of h and k")
    assert marked.get_attribute("data-identity") == "cons:cntn:h"

    # a later text that does not parse: the last parse's tables, locked
    # (ruling 10); one undo makes them editable again
    broken = two.replace("a = m_d - c", "a = m_d - - c")
    replace_in_editor(page, "a = m_d - c", "a = m_d - - c")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == broken, 5.0, "a text that does not parse")
    assert settled_status(page, digest7(broken))["state"] == "not parsed"
    page.wait_for_selector(".bl-class-tables.bl-stale", timeout=8_000)
    assert continuation() == rows
    assert page.locator('[data-identity="cons:dcsn:c"] .bl-class-set').is_disabled()
    click_line(page, 1)
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == two, 5.0, "one undo of the text")
    page.wait_for_selector(".bl-class-tables:not(.bl-stale)", timeout=8_000)

    # the two equations typed construct the stage again: the mark goes, and
    # h links to its box; undo then returns the file's text
    three = edited(two, 19, "    h = a\n    k = a\n}")
    click_before(page, 19, "}")
    page.keyboard.insert_text("    h = a\n    k = a\n")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == three, 5.0, "the two equations typed")
    assert settled_status(page, digest7(three))["state"] == "constructed"
    wait_until(lambda: marked.count() == 0, 5.0, "the mark withdrawn")
    assert row_h.locator("button.bl-class-field").count() == 1
    click_line(page, 1)
    for _ in range(3):
        page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "three undos")
    assert settled_status(page, digest7(original))["state"] == "constructed"

    # the panel's strip: its tabs, the file's name and `open wide` (unit N,
    # Task 2), the loop's state in the status line alone
    types_head = '.bl-classification[data-panel="types"] .bl-inspector-strip'
    assert page.locator(f"{types_head} .bl-class-state").count() == 0
    assert "constructed" not in page.locator(types_head).text_content()
    assert page.locator(".bl-status-summary .bl-status-state").text_content() == "constructed"

    # the panel's one height on its four tabs, at its default and dragged;
    # a tab's content taller than the panel scrolls inside it
    def panel_on_each_tab() -> dict:
        shown = {}
        for tab in ("Fields", "Parameters", "Settings", "Methods"):
            page.click(f'.bl-class-tab[data-tab="{tab}"]')
            content = ".bl-class-tables" if tab == "Fields" else f'.bl-values[data-tab="{tab}"]'
            page.wait_for_selector(content, timeout=10_000)
            shown[tab] = page.evaluate(CLASSIFICATION_PANEL_JS)
        return shown

    shown = panel_on_each_tab()
    assert len({panel["height"] for panel in shown.values()}) == 1, shown
    assert all(panel["inside"] and panel["scrolls"] for panel in shown.values()), shown
    default = shown["Fields"]["height"]
    drag_handle(page, "classification", 0, default - 120)
    wait_until(
        lambda: abs(page.evaluate(CLASSIFICATION_PANEL_JS)["height"] - 120) <= 1,
        5.0,
        "the panel dragged to 120 px",
    )
    shown = panel_on_each_tab()
    assert {round(panel["height"]) for panel in shown.values()} == {120}, shown
    assert all(panel["inside"] and panel["scrolls"] for panel in shown.values()), shown
    assert shown["Methods"]["taller"], shown
    page.locator('.bl-handle[data-handle="classification"]').dblclick()
    wait_until(
        lambda: abs(page.evaluate(CLASSIFICATION_PANEL_JS)["height"] - default) <= 0.5,
        5.0,
        "the panel at its default height",
    )
    page.click('.bl-class-tab[data-tab="Fields"]')

    # Details: its heading and the rows of a selected box, each key 64 px;
    # the check reads the box's own rows, since the rows of its builder
    # stand in the fold `cursor`, closed while the box is selected (unit K,
    # Task 5)
    assert page.locator(".bl-panel .bl-region-name").text_content() == "Details"
    select_node(page, "policy:Evaluation", "backward")
    keys = ".bl-box-details .bl-attribute-key"
    page.wait_for_selector(keys, timeout=10_000)
    assert {box["width"] for box in boxes(page, keys)} == {64}
    assert set(type_of(page, keys)) == {SIZES["small"]}

    # paper: written once from the saved text, then omitted
    papers = model_folder / model.PAPER_FOLDER
    select_node(page, "policy___group___", "backward")
    # the builder's identifier in Code name, then its kind (the fix wave Q3b
    # of unit Q, item 19; C1)
    wait_until(lambda: panel_head(page).startswith("policy Builder"), 5.0, "the builder")
    try:
        page.click(".bl-paper-button", timeout=10_000)
        wait_until(
            lambda: page.locator(".bl-paper-button").count() == 0, 10.0, "paper omitted"
        )
        assert sorted(path.name for path in papers.iterdir()) == ["cons.md", "cons.svg"]
        assert (papers / "cons.md").read_text(encoding="utf-8").startswith("# cons")
        wait_until(
            lambda: "paper/cons.md written with paper/cons.svg" in git_line_sentence(page),
            5.0,
            "the sentence of paper",
        )
        note = page.locator(".bl-status-summary .bl-status-note")
        assert note.is_visible()
        assert note.text_content() == "paper/cons.md written with paper/cons.svg"
    finally:
        shutil.rmtree(papers, ignore_errors=True)

    # notebook: written once for the source shown, the open file and the tabs
    # unchanged
    notebooks = model_folder / "notebooks"
    sentence = f"notebooks/{model_folder.name}.ipynb written"
    tabs = file_tabs(page)
    assert page.locator(".bl-folder-bar > :last-child.bl-notebook").count() == 1
    try:
        page.click(".bl-folder-bar .bl-notebook", timeout=10_000)
        wait_until(lambda: page.locator(".bl-notebook").count() == 0, 10.0, "notebook omitted")
        assert [path.name for path in notebooks.iterdir()] == [f"{model_folder.name}.ipynb"]
        note = page.locator(".bl-status-summary .bl-status-note")
        wait_until(lambda: note.text_content() == sentence, 5.0, "the sentence of notebook")
        assert note.is_visible()
        assert open_path_shown(page) == CONS and file_tabs(page) == tabs
        assert page.evaluate(DOCUMENT_JS) == original
    finally:
        shutil.rmtree(notebooks, ignore_errors=True)

    # the builder's selection scrolled the text to its block, line 31, so
    # line 1 is brought into view before the click (CHARACTER_BOX_JS)
    click_before(page, 1, "cons")
    page.keyboard.press("End")
    page.keyboard.type("  # kept")
    # the typed text answered by the loop, unsaved: no paper button stands
    settled_status(page, digest7(kept))
    assert panel_head(page).startswith("policy Builder")
    assert page.locator(".bl-paper-button").count() == 0
    reveal_in_tree(page, PORT)
    page.click(f'.bl-tree-file[data-path="{PORT}"]')
    wait_until(lambda: open_path_shown(page) == PORT, 10.0, "port.bl open")
    wait_until(lambda: line_text(page, 1) == port_text.split("\n")[0], 5.0, "port.bl's text")
    click_line(page, 1)
    page.keyboard.press("End")
    page.keyboard.type("  # typed")
    opened = [
        {"path": RECIPE_FILE, "active": False, "unsaved": False},
        {"path": CONS, "active": False, "unsaved": True},
        {"path": PORT, "active": True, "unsaved": True},
    ]
    wait_until(lambda: file_tabs(page) == opened, 10.0, "two unsaved tabs in the order opened")

    page.click(f'.bl-tab[data-path="{CONS}"]')
    wait_until(lambda: open_path_shown(page) == CONS, 10.0, "cons.bl open again")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == kept, 5.0, "cons.bl's typed text")
    assert [(tab["path"], tab["unsaved"]) for tab in file_tabs(page)] == [
        (RECIPE_FILE, False),
        (CONS, True),
        (PORT, True),
    ]
    assert page.locator(".bl-file-name").text_content() == "cons.bl"
    assert (model_folder / CONS).read_text(encoding="utf-8") == original
    assert (model_folder / PORT).read_text(encoding="utf-8") == port_text

    # each value tab's row names its file and line in the name's button, which
    # opens that file at that line by the keyboard alone
    for tab in ("Parameters", "Settings", "Methods"):
        page.click(f'.bl-tab[data-path="{CONS}"]')
        wait_until(lambda: open_path_shown(page) == CONS, 10.0, "cons.bl open")
        page.click(f'.bl-class-tab[data-tab="{tab}"]')
        page.wait_for_selector(f'.bl-values[data-tab="{tab}"]', timeout=10_000)
        assert "line" not in page.locator(".bl-values-table th").all_text_contents()
        name = page.locator(".bl-values-name button").first
        path, line = name.get_attribute("data-path"), int(name.get_attribute("data-line"))
        assert name.get_attribute("aria-description") == f"{path}:{line}"
        name.focus()
        page.keyboard.press("Enter")
        wait_until(
            lambda path=path, line=line: (open_path_shown(page), active_line(page)) == (path, line),
            10.0,
            f"{path} at line {line}",
        )
        # the folders on the opened file's path open, so that its row is seen
        page.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{path}"]', timeout=5_000)

    # the tabs' close controls: an unsaved buffer's is disabled and closes
    # nothing; a saved tab closes, the open one opening the tab to its left
    def close_of(path: str) -> str:
        return f'.bl-tab-item:has(> .bl-tab[data-path="{path}"]) > .bl-tab-close'

    tabs = file_tabs(page)
    paths = [tab["path"] for tab in tabs]
    assert [tab["path"] for tab in tabs if tab["unsaved"]] == [CONS, PORT]
    assert tab_closes(page) == [
        {
            "path": tab["path"],
            "label": f"Close {tab['path'].rsplit('/', 1)[-1]}",
            "title": "Save the file first." if tab["unsaved"] else "Close",
            "disabled": tab["unsaved"],
        }
        for tab in tabs
    ]
    # the disabled close takes the pointer, so that its hover is shown
    # (design pass 8 §5.5; unit M, Task 6)
    assert visible_in_viewport(page, close_of(CONS))
    page.click(close_of(CONS), force=True)
    page.wait_for_timeout(1_000)
    assert [tab["path"] for tab in file_tabs(page)] == paths
    active = next(tab["path"] for tab in tabs if tab["active"])
    left = paths[paths.index(active) - 1]
    page.click(close_of(active))
    paths.remove(active)
    wait_until(
        lambda: open_path_shown(page) == left
        and [tab["path"] for tab in file_tabs(page)] == paths,
        10.0,
        "the open tab closed and the tab to its left open",
    )
    page.click(close_of(RECIPE_FILE))
    paths.remove(RECIPE_FILE)
    wait_until(
        lambda: [tab["path"] for tab in file_tabs(page)] == paths, 10.0, "the recipe's tab closed"
    )
    assert open_path_shown(page) == left
    assert (model_folder / CONS).read_text(encoding="utf-8") == original
    assert (model_folder / PORT).read_text(encoding="utf-8") == port_text


def test_item_3_goto_anything_previews_and_cancels_and_the_keyboard_reaches_every_region_and_the_folds_persist(  # noqa: E501  (the name the plan gives the test)
    page, server, model_folder
):
    """Item 3, first part (spec 0.4 §5.1; R-D3, R-D16): with the handle
    `file` dragged and the folder folded by the main bar's toggle `Files`,
    the record in the browser's storage under the folder's path holds the
    keys `sizes` and `folds` and no other, each key of `sizes` the name of a
    handle and `folds` the fold of each region of the main bar's toggles,
    the folder's, the two panels' and Matsya's (unit L, Task 12; AAS,
    L-D12; unit N, Task 1, N-D4);
    Matsya folded by its button then stands in the record's folds too (Task
    12); the page loaded again keeps the folder and Matsya folded and the
    columns' widths.

    The graph's header (R-D55, R-D56; amendment 02 rulings 3 to 6), the
    graph bar since unit N's Task 1 (design pass 10 §2): with cons.bl open
    at 1600 × 1000, the bar is a whole number of rows of the frame's height,
    Problems in the first, holding `Semantic graph`, the select `graph`,
    whose options are `Operator` and `Initial`,
    the select `direction`, whose options are `Backward` and `Forward`, each
    a combobox of that name with its capital, and the view tabs `Stage` and
    `Trellis` (unit K, K-D20; design pass 8 §§4 and 6); each pair of words
    shows its graph, which the view lays out. A keyboard reader opens a
    select with ↓, VSCode Elements' list then marking the option chosen
    active, moves with the arrow keys and chooses with Enter. The choices
    make no place of the history: one ← shows the recipe's trellis the tab
    left for cons.bl, and → shows cons.bl
    again in the graph last chosen. `trellis` shows the trellis where the
    breadcrumb's `spec.yml` goes, marked, the select `graph` omitted, the
    occurrence cons.bl is bound as selected; ← shows the stage and its graph
    again. In the trellis view the restriction's select, with no label of
    its own, stands with the graph's name and the view tabs on the bar's
    one row (unit K, K-D17 and K-D18); a text with a stage clause typed at
    the foot of its menu keeps the row at 1600 px; at 1200 px, the graph at
    its least width (R-D59), the bar in the system's controls takes two
    rows of 36 px, each item centered on one of them, Problems on the first
    and the restriction's select on the second (amendment 02 ruling 5; unit
    M, Task 7); and `all` in its menu shows the whole trellis.

    Goto Anything (spec 0.4 §5.8; brief rule 9; reviews 1 and 17; R-D35),
    with the box `cntn_to_dcsn:Pullback` selected and the cursor on line 8:
    P with the primary modifier opens the palette, the browser's printing
    prevented, and its input holds the focus; `:2` marks line 2, a further
    key grows the input's value to `:20`, which marks line 20, and the
    editor's document is unchanged; `@Aggregation` previews its first box,
    which Details then shows. Escape closes the palette and leaves the
    document, the editor's `view()`, the graph's `view()`, the focused
    element, Details' heading and the buttons of the history as they were
    before the key, with no line marked. `@` with a block's name lists the
    block first at its header's line and its boxes after it, and Enter makes
    the header the active line. `#argmax` lists the lines that hold it, each
    at its line and column; Tab leaves the input for the first result, and
    Escape there closes the palette. `>hide types` with Enter hides the
    types and `>show types` shows them; `>fold folder` folds the folder and
    opens it again; `>high contrast` makes the passive line numbers opaque
    ice-3, and the page loaded again keeps them so (R-D24). Each result
    prints its kind and its address, a command's address empty.

    The keyboard's reach (spec 0.4 §§2.4 and 5.8; brief §4; R-D13): in the
    recipe's trellis, the selection cleared by Escape, Tab from the
    region's first box reaches boxes that lie outside the view, the view
    moving to each, and from the last of them leaves the graph's region
    within twenty presses. In cons.bl's view, Tab reaches the last icon of
    the graph's controls, the last field's button in Fields, the last
    name's button in each of Parameters, Settings and Methods, and Matsya's
    list of exchanges, each reached again by Tab after Shift+Tab, and from
    each moves the focus out of its region within twenty presses
    (`focus_faults`)."""
    open_cons(page, server)
    record_layouts(page)

    # Goto Anything: the state before the key, a box selected and the
    # cursor on line 8 with the focus in the editor
    select_node(page, "cntn_to_dcsn:Pullback", "backward")
    wait_until(
        lambda: flow_handle(page, "selection") == "cntn_to_dcsn:Pullback",
        5.0,
        "the Pullback selected",
    )
    document = page.evaluate(DOCUMENT_JS)

    def header_of(block: str) -> int:
        return next(
            number
            for number, line in enumerate(document.split("\n"), 1)
            if line.startswith(f"[id={block},")
        )

    # the editor moved to the box's block, then scrolled to its top
    wait_until(
        lambda: status_place(page).startswith(f"{header_of('cntn_to_dcsn')}:"),
        5.0,
        "the cursor on the box's block",
    )
    page.evaluate(SCROLL_EDITOR_JS, 0)
    click_before(page, 8, ":=")
    wait_until(lambda: status_place(page).startswith("8:"), 5.0, "the cursor on line 8")
    # longer than the editor's pause of 120 ms before it reports the cursor
    page.wait_for_timeout(300)

    def state() -> dict:
        return {
            "editor": editor_handle(page, "view"),
            "graph": flow_handle(page, "view"),
            "details": panel_head(page),
            "history": history_buttons(page),
        }

    page.evaluate(KEEP_FOCUS_JS)
    kept = state()
    assert kept["graph"]["selection"] == "cntn_to_dcsn:Pullback" and kept["details"]
    page.evaluate(KEY_PREVENTED_RECORDER_JS)
    open_goto(page)
    assert page.evaluate("() => window.keyPrevented") is True
    page.keyboard.type(":2")
    wait_until(lambda: page.evaluate(PREVIEW_LINES_JS) == [2], 5.0, "line 2 previewed")
    page.keyboard.press("0")
    assert page.input_value(".bl-goto-input") == ":20"
    wait_until(lambda: page.evaluate(PREVIEW_LINES_JS) == [20], 5.0, "line 20 previewed")
    line_20 = {"text": "20", "kind": "line", "address": "20:1", "current": True}
    assert goto_results(page) == [line_20]
    assert page.evaluate(DOCUMENT_JS) == document
    assert editor_handle(page, "view")["anchor"] == kept["editor"]["anchor"]
    page.fill(".bl-goto-input", "@Aggregation")
    wait_until(
        lambda: flow_handle(page, "selection") == "cntn_to_dcsn:Aggregation"
        and panel_head(page) != kept["details"],
        10.0,
        "the first box of the name previewed",
    )
    first = goto_results(page)[0]
    assert (first["kind"], first["current"]) == ("box", True)
    assert page.evaluate(DOCUMENT_JS) == document
    page.keyboard.press("Escape")
    wait_until(lambda: not page.locator(".bl-goto").is_visible(), 5.0, "the palette closed")
    wait_until(lambda: state() == kept, 10.0, "the state before the key")
    page.wait_for_timeout(500)
    assert state() == kept
    assert page.evaluate(KEPT_FOCUS_JS)
    assert page.evaluate(PREVIEW_LINES_JS) == []
    assert page.evaluate(DOCUMENT_JS) == document

    # `@` with a block's name, then Enter
    header = header_of("dcsn_to_arvl")
    open_goto(page)
    page.keyboard.type("@dcsn_to_arvl")
    wait_until(lambda: page.evaluate(PREVIEW_LINES_JS) == [header], 5.0, "the header previewed")
    results = goto_results(page)
    assert results[0] == {
        "text": "dcsn_to_arvl",
        "kind": "block",
        "address": f"{header}:1",
        "current": True,
    }
    assert results[1:] and {result["kind"] for result in results[1:]} == {"box"}
    assert {result["address"] for result in results} == {f"{header}:1"}
    page.keyboard.press("Enter")
    wait_until(lambda: active_line(page) == header, 5.0, "the block's header the active line")
    assert page.evaluate(PREVIEW_LINES_JS) == []

    # `#argmax`, then Tab to the first result and Escape there
    holding = lines_holding("argmax", document)
    assert holding
    open_goto(page)
    page.keyboard.type("#argmax")
    expected = [
        {"text": row["text"], "kind": "text", "address": f"{row['line']}:{row['column']}"}
        for row in holding
    ]
    wait_until(
        lambda: [
            {key: result[key] for key in ("text", "kind", "address")}
            for result in goto_results(page)
        ]
        == expected,
        5.0,
        "the lines that hold argmax",
    )
    page.keyboard.press("Tab")
    assert page.evaluate(
        "() => document.activeElement.matches('.bl-goto-result')"
        " && document.activeElement === document.querySelector('.bl-goto-result')"
    )
    page.keyboard.press("Escape")
    wait_until(lambda: not page.locator(".bl-goto").is_visible(), 5.0, "the palette closed")
    assert page.evaluate(DOCUMENT_JS) == document

    # the commands
    types = page.locator(".bl-types-button")
    goto_command(page, "hide types")
    wait_until(lambda: types.get_attribute("aria-pressed") == "false", 5.0, "the types hidden")
    goto_command(page, "show types")
    wait_until(lambda: types.get_attribute("aria-pressed") == "true", 5.0, "the types shown")
    folded = page.locator(".bl-window[data-folded-folder]")
    goto_command(page, "fold folder")
    wait_until(lambda: folded.count() == 1, 5.0, "the folder folded")
    goto_command(page, "fold folder")
    wait_until(lambda: folded.count() == 0, 5.0, "the folder opened")
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "the frame's widths")
    ice_3 = property_color(page, "--bl-ice-3")
    assert page.evaluate(COLOR_OF_JS, PASSIVE_LINE_NUMBER) != ice_3
    goto_command(page, "high contrast")
    wait_until(
        lambda: page.evaluate(COLOR_OF_JS, PASSIVE_LINE_NUMBER) == ice_3,
        5.0,
        "the line numbers in opaque ice-3",
    )
    assert page.evaluate(DOCUMENT_JS) == document

    assert view_shown(page) == {"graph": "operator", "direction": "backward"}
    assert view_options(page, "graph") == ["operator", "initial"]
    assert view_options(page, "direction") == ["backward", "forward"]
    for name in ("Graph", "Direction"):
        assert page.get_by_role("combobox", name=name, exact=True).count() == 1
    switch = page.locator(".bl-graph-bar .bl-view-switch vscode-tab-header").all_text_contents()
    assert [word.strip() for word in switch] == ["Stage", "Trellis"]
    rows = boxes(page, ".bl-graph-bar")[0]["height"] / ROW_HEIGHTS["graph bar"]
    assert rows >= 1 and abs(rows - round(rows)) < 0.02, rows
    # the four pairs, in an order in which each changes the graph shown
    pairs = (("operator", "forward"), ("operator", "backward"))
    pairs += (("initial", "backward"), ("initial", "forward"))
    for kind, direction in pairs:
        choose_view(page, kind, direction)
        chosen = f"{direction} initial diagram" if kind == "initial" else direction
        wait_until(
            lambda chosen=chosen: page.evaluate(VIEW_STATE_JS)["current"]
            and page.evaluate("() => window.laidOut.graphId") == chosen,
            15.0,
            f"the graph {chosen} laid out",
        )

    # the keyboard: ↓ opens VSCode Elements' list with the option chosen
    # active, the arrows move the active option, Enter chooses (design pass
    # 8 §4; unit M, Task 7)
    def active_option() -> str | None:
        active = page.locator(".bl-view-direction li.option.active")
        return active.text_content().strip().lower() if active.count() else None

    page.get_by_role("combobox", name="Direction", exact=True).focus()
    page.keyboard.press("ArrowDown")
    wait_until(lambda: active_option() is not None, 5.0, "the list open on an option")
    for _ in range(3):
        if active_option() == "backward":
            break
        page.keyboard.press("ArrowUp")
    assert active_option() == "backward"
    page.keyboard.press("Enter")
    wait_until(
        lambda: page.get_attribute(".bl-graph-bar", "data-graph") == "backward initial diagram",
        10.0,
        "the backward initial diagram chosen by the keyboard",
    )

    # the choices are no places: one ← to the recipe's trellis, → back to
    # cons.bl in the graph last chosen
    stage_crumbs = breadcrumb(page)
    # the stage's path names the occurrence it is bound as after the recipe
    # by two parts, its key and its period (the fix wave Q3b of unit Q, item
    # 19; C19)
    trellis_crumbs = stage_crumbs.rsplit(" › ", 2)[0]
    occurrence = recipe_head(page).replace(" / ", "/")
    assert history_buttons(page) == (1, 0)
    press_outside_fields(page, "Alt+ArrowLeft")
    wait_until(lambda: breadcrumb(page) == trellis_crumbs, 30.0, "the recipe's trellis")
    press_outside_fields(page, "Alt+ArrowRight")
    wait_until(lambda: breadcrumb(page) == stage_crumbs, 30.0, "cons.bl again")
    wait_until(
        lambda: page.get_attribute(".bl-graph-bar", "data-graph") == "backward initial diagram",
        10.0,
        "the graph last chosen",
    )
    assert view_shown(page) == {"graph": "initial", "direction": "backward"}

    # `trellis`: the place of the breadcrumb's recipe, the occurrence
    # selected, a place of the history
    page.click(".bl-trellis-button")
    wait_until(lambda: breadcrumb(page) == trellis_crumbs, 30.0, "the trellis's breadcrumb")
    wait_until(
        lambda: panel_head(page).startswith(occurrence_head(occurrence)),
        30.0,
        f"the occurrence {occurrence} selected",
    )
    assert page.locator(".bl-trellis-button.bl-active").count() == 1
    # the trellis view offers the kind select too since design pass 14 §7 (S-D12)
    assert view_shown(page) == {"direction": "backward", "graph": "operator"}
    press_outside_fields(page, "Alt+ArrowLeft")
    wait_until(lambda: breadcrumb(page) == stage_crumbs, 30.0, "the stage again")
    wait_until(
        lambda: page.get_attribute(".bl-graph-bar", "data-graph") == "backward initial diagram",
        10.0,
        "the stage's graph again",
    )

    # the restriction's select on the header's one row, in the bar's face
    # with no label of its own (unit K, K-D17 and K-D18): a text with a
    # stage clause typed at the foot of its menu keeps the row at 1600 px;
    # at 1200 px, where the graph has its least width (R-D59), the bar's
    # items in the system's controls take two rows of 36 px, the direction
    # and the view tabs the first and the restriction's select the second
    # (amendment 02 ruling 5; design pass 8 §§4 and 6; unit M, Task 7); and
    # `all` shows the whole trellis
    page.click(".bl-trellis-button")
    page.wait_for_selector(RESTRICTION, timeout=30_000)
    assert page.locator(".bl-graph-bar label").count() == 0
    # the graph's name, its selects, the view tabs and the restriction's
    # select, the items of the bar but Problems, the name where the bar draws
    # it, since a bar whose items do not fit one row with it draws no name
    # (the fix wave Q3b of unit Q, item 16; D22)
    items = (
        ".bl-graph-bar:not([data-crowded]) .bl-graph-tools > .bl-graph-name,"
        f" .bl-graph-tools > .bl-graph-choice > *, {RESTRICTION}"
    )

    def one_row() -> bool:
        centers = [box["top"] + box["height"] / 2 for box in boxes(page, items)]
        return max(centers) - min(centers) <= 1

    assert one_row()
    restrict(page, "periods 0–1, stages cons")
    wait_until(
        lambda: restriction_shown(page) == "periods 0–1, stages cons", 30.0, "the text typed"
    )
    assert one_row()
    restrict(page, "periods 0–1")
    wait_until(lambda: restriction_shown(page) == "periods 0–1", 30.0, "the range typed")
    # two rows at 1200 px, where the graph has its least width (R-D59), with
    # Matsya opened by the main bar's toggle, the trellis view folding it
    # (unit K's decisions K-D6 and K-D19; unit N, Task 1): each item
    # centered on a row, Problems on the first and the restriction's select
    # on the second
    page.click(MATSYA_TOGGLE)
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "Matsya opened")
    page.set_viewport_size({"width": 1200, "height": 1000})
    wait_until(lambda: boxes(page, ".bl-view")[0]["width"] == 300, 5.0, "the graph at 300 px")
    bar, restriction = boxes(page, ".bl-graph-bar")[0], boxes(page, RESTRICTION)[0]
    assert bar["height"] == 72, bar
    rows = (bar["top"] + 18, bar["top"] + 54)
    for found in boxes(page, items):
        center = found["top"] + found["height"] / 2
        assert min(abs(center - row) for row in rows) <= 1, (found, bar)
    problems = boxes(page, ".bl-graph-bar > .bl-errors")[0]
    assert abs(problems["top"] + problems["height"] / 2 - rows[0]) <= 1, (problems, bar)
    assert abs(restriction["top"] + restriction["height"] / 2 - rows[1]) <= 1
    page.set_viewport_size({"width": 1600, "height": 1000})
    wait_until(lambda: tracks_near(page, FRAME_TRACKS[1600, False]), 5.0, "the frame's widths")
    choose_restriction(page, "all")
    wait_until(lambda: restriction_shown(page) == "all", 30.0, "the whole trellis")

    # the keyboard in the trellis: from the region's first box, Tab reaches
    # boxes outside the view, the view moving to each, and leaves the
    # region within twenty presses of the last of them; the trellis is
    # waited for at rest, since its second layout selects the occurrence
    # cons.bl is bound as (Task 19's report, concern 1)
    wait_until(lambda: view_still(page), 30.0, "the whole trellis at rest")
    focus_region(page)
    page.keyboard.press("Escape")
    wait_until(lambda: flow_handle(page, "selection") is None, 5.0, "the selection cleared")
    page.evaluate(BLUR_JS)
    # the first box is the graph's first node, the `start` node of a wire
    # that enters it, which replaces the trellis's own `Inputs` (design pass
    # 10 §6; unit N, Task 6), in the graph shown, which the graph bar names
    # (`.bl-graph-bar`, where the view's bar was before unit N's Task 1)
    shown = page.get_attribute(".bl-graph-bar", "data-graph")
    first = graph_named(page.evaluate(HELD_COLLECTION_JS), shown)["nodes"][0]
    assert attribute_of(first, "kind") == "start" and not first.get("namespace"), first["id"]
    assert focus_region(page)["box"] == first["id"]
    presses, panned = 0, []
    while presses < 400:
        before = viewport(page)
        presses += 1
        if press_in_region(page, "Tab") is None:
            break
        if viewport(page) != before:
            panned.append(presses)
    assert panned and presses - panned[-1] <= 20, (presses, panned)

    # the keyboard in the stage's view: Tab reaches an icon of the graph's
    # controls, a field's button in Fields, a name's button in each value
    # tab and Matsya's list of exchanges, and leaves the region of each
    # (R-D13); the switch's `stage` shows cons.bl's view (unit K, K-D20)
    page.click(".bl-stage-button")
    page.wait_for_selector(".bl-view-kind", timeout=30_000)
    page.wait_for_selector(".bl-class-field", timeout=30_000)
    assert focus_faults(page, [".bl-graph-icon", ".bl-class-field"]) == []
    for tab in ("Parameters", "Settings", "Methods"):
        page.click(f'.bl-class-tab[data-tab="{tab}"]')
        page.wait_for_selector(f'.bl-values[data-tab="{tab}"]', timeout=10_000)
        assert focus_faults(page, [".bl-values-name button"]) == [], tab
    page.click('.bl-class-tab[data-tab="Fields"]')
    assert focus_faults(page, [".bl-matsya-exchanges"]) == []
    text = FRAME_TRACKS[1600, False][1]
    drag_handle(page, "file", -100)
    wait_until(lambda: abs(tracks(page)[1] - (text - 100)) <= 1, 5.0, "the text dragged")
    page.click('.bl-fold[data-fold="folder"]')
    wait_until(lambda: abs(tracks(page)[0] - 48) <= 1, 5.0, "the folder folded")
    assert layout_record(page, model_folder)["folds"] == {**OPEN_FOLDS, "folder": True}
    page.click(MATSYA_FOLD)
    # folded, Matsya's column takes no width (K-D19)
    wait_until(lambda: len(tracks(page)) == 3, 5.0, "Matsya folded")
    kept = tracks(page)
    record = layout_record(page, model_folder)
    assert set(record) == {"sizes", "folds"}
    assert record["sizes"] and set(record["sizes"]) <= set(page.evaluate(HANDLE_NAMES_JS))
    assert record["folds"] == {**OPEN_FOLDS, "folder": True, "matsya": True}

    page.reload()
    page.wait_for_selector(
        ".bl-window[data-folded-folder][data-folded-matsya]", state="attached", timeout=60_000
    )
    wait_until(lambda: tracks_near(page, kept), 30.0, "the kept widths after the reload")
    for selector in ('.bl-fold[data-fold="folder"]', MATSYA_FOLD, MATSYA_TOGGLE):
        assert page.get_attribute(selector, "aria-expanded") == "false", selector
    assert layout_record(page, model_folder) == record
    # the high-contrast setting kept for the browser (R-D24)
    assert page.get_attribute(".bl-window", "data-contrast") == "high"
    page.wait_for_selector(PASSIVE_LINE_NUMBER, state="attached", timeout=30_000)
    assert page.evaluate(COLOR_OF_JS, PASSIVE_LINE_NUMBER) == ice_3


def test_item_4_contrast_names_focus_and_no_animation_hold_and_orange_marks_a_refusal_alone(
    page, server, original, server_on, scratch_consport, scratch_folder
):
    """Item 4, first part: with cons.bl constructed at 1600 × 1000, no
    element under the window or Vuetify's menus has a transition or an
    animation but CodeMirror's caret layer (brief rule 10; review 8); every
    text meets 4.5:1 on its composited ground, or 3:1 within a button, but
    for the exceptions of spec 0.4 §5.8 and R-D38; the window stands on the
    chrome, and the editor's frame and the graph's host on the lit surface
    (§5.2); and no element under the window is drawn on the ice ground
    (brief rule 10). The menu of the occurrence line's six positions opens
    and closes with no animation, those of the Web Animations API included,
    and holds no element that moves while open (§5.8: "selection and preview
    changes are immediate").

    A refusal (spec 0.4 §5.7; brief rule 8): with `- ` typed before `c` on
    line 18, which the parser refuses, the orange marks are the error mark
    with its count, the refused span's underline and its gutter mark, and
    no element of the status line. The status line prints `not parsed`
    with the digest of the refused text, `1 refused` and no sentence of the
    refusal, its square neutral. The graph stands at 32 percent and reads
    above it `last constructed` with the digest the status line printed
    before the edit; the tables of Fields and of Parameters stand at 50
    percent.

    Names, focus and words (spec 0.4 §§5.1, 5.6 and 5.8; brief §4): with
    cons.bl constructed, no element under the window is drawn in orange
    (ORANGE_ELEMENTS_JS); every drawn button and link has an accessible
    name (NAMELESS_JS); each icon and each fold button, ICON_BUTTONS,
    which names every drawn button that holds a drawing, draws an outline
    while it holds the keyboard's focus; the two running heads read
    `Semantic graph` and `Matsya` (unit N, Task 1); and Υ is drawn in
    periwinkle. With the palette open on `@cntn`, every text meets its
    bound. In each of the five states of item 1 every text meets its
    bound, but for the exceptions."""
    open_cons(page, server)
    page.wait_for_selector(".bl-class-row", timeout=10_000)
    assert page.evaluate(MOTION_JS) == []
    assert contrast_faults(page, CONTRAST_EXCEPTIONS) == []
    assert page.evaluate(GROUND_JS, ".bl-window") == property_color(page, "--bl-chrome")
    lit = property_color(page, "--bl-navy")
    assert page.evaluate(GROUND_JS, ".bl-editor-frame") == lit
    assert page.evaluate(GROUND_JS, ".bl-view-host") == lit
    assert page.evaluate(GROUNDS_OF_JS, property_color(page, "--bl-ice")) == []

    # no orange without a refusal: the problems count alone, in the alarm's
    # orange while errors or checks stand (design pass 13 §5; Q-D8), the
    # model's whole-model problems among them; the names, the outlines, the
    # running heads and Υ
    assert orange_marks(page) == ({"error mark"} if error_count(page) else set())
    assert page.evaluate(NAMELESS_JS) == []
    assert page.evaluate(OTHER_ICONS_JS, ICON_BUTTONS) == []
    assert outline_faults(page, ICON_BUTTONS) == []
    assert page.locator(RUNNING_HEADS).all_text_contents() == ["Semantic graph", "Matsya"]
    periwinkle = property_color(page, "--bl-periwinkle")
    assert page.evaluate(COLOR_OF_JS, ".bl-matsya-upsilon") == periwinkle

    # the palette open
    open_goto(page)
    page.keyboard.type("@cntn")
    wait_until(lambda: goto_results(page), 5.0, "the results of @cntn")
    assert contrast_faults(page, CONTRAST_EXCEPTIONS) == []
    page.keyboard.press("Escape")
    wait_until(lambda: not page.locator(".bl-goto").is_visible(), 5.0, "the palette closed")
    # a click on the select opens its list, and a second closes it; the
    # select is VSCode Elements', its `open` reflected as an attribute
    # (design pass 8 §4; unit M, Task 6)
    select = page.locator(".bl-recipe-positions vscode-single-select")
    items = select.get_by_role("option")
    opened = animations_during(page, lambda: select.click())
    assert select.get_attribute("open") is not None and items.first.is_visible()
    assert page.evaluate(MOTION_JS) == []
    closed = animations_during(page, lambda: select.click())
    assert (opened, closed, select.get_attribute("open")) == ([], [], None)

    # a refusal: orange marks the error mark, the refused span and its
    # line alone; the graph and the tables dim and name what they show
    digest = page.locator(".bl-status-summary .bl-status-digest").text_content()
    assert digest == digest7(original)
    refused_text = edited(original, 18, "    a = m_d - - c")
    (diagnostic,) = model.elaborate_buffer(refused_text, CONS).diagnostics
    replace_in_editor(page, "a = m_d - c", "a = m_d - - c")
    page.wait_for_selector(".cm-content .cm-lintRange-error", timeout=8_000)
    page.wait_for_selector(".bl-view-host.bl-stale", timeout=8_000)
    wait_until(
        lambda: page.locator(".bl-status-summary .bl-status-digest").text_content()
        == digest7(refused_text),
        8.0,
        "the status line on the refused text",
    )
    assert orange_marks(page) == {"error mark", "underline", "gutter mark"}
    assert page.locator(".bl-status-summary").is_visible()
    assert page.locator(".bl-status-summary .bl-status-state").text_content() == "not parsed"
    assert page.locator(".bl-status-summary .bl-status-refused").text_content() == "1 refused"
    assert page.get_attribute(".bl-status-square", "data-state") == "not parsed"
    assert page.evaluate(COLOR_OF_JS, ".bl-status-square") != property_color(page, "--bl-mint")
    assert diagnostic.message not in page.locator(".bl-status").text_content()
    assert page.evaluate(VIEW_OPACITY_JS) == 0.32
    assert page.locator(".bl-view-shown").text_content() == f"last constructed {digest}"
    assert page.evaluate(OPACITY_OF_JS, ".bl-class-tables.bl-stale") == 0.5
    page.click('.bl-class-tab[data-tab="Parameters"]')
    page.wait_for_selector('.bl-values[data-tab="Parameters"].bl-stale', timeout=10_000)
    assert page.evaluate(OPACITY_OF_JS, ".bl-values.bl-stale") == 0.5

    # the contrast of every text in the five states of item 1
    write_refused_cons(scratch_folder)
    urls = {
        "trellis": server_on(scratch_consport),
        "refused before a construction": server_on(scratch_folder),
    }
    for state in STATES:
        show_state(page, state, urls.get(state, server))
        assert contrast_faults(page, CONTRAST_EXCEPTIONS) == [], state


def test_item_5_matsya_answers_in_its_column_and_the_page_draws_with_the_network_closed(
    page, server, server_on, model_folder, original
):
    """Item 5: every file js/fonts/build.sh writes is the file the record of
    js/fonts/README.md names, by its size and its SHA-256, and the server
    answers it at static/assets/fonts/<name> with the same bytes, so that
    the runtime fonts are served locally (spec 0.4 §5.2; R-D1); each font's
    license is the SIL Open Font License beside it. The graph's bundle
    writes the seven files of js/flow/README.md's record, IBM Plex Mono no
    longer among them (R-D22).

    The network closed (spec 0.4 §5.2 and §8, R item 5; brief §4): with
    every request of the page outside the server's origin refused, cons.bl
    opens and its graph draws; the page asked the server
    for every font file of FONT_FILES; every text under the window is drawn
    in a face the page loaded (`fonts_drawn`); and each of the seven
    symbols of brief rule 1 is drawn in STIX Two Math, the served file, in
    each of the four stacks (`symbol_faces`), as Task 1 measured.

    Matsya's column (spec 0.4 §§5.6 and 6; brief rule 8; review 8; R-D7,
    R-D8): with cons.bl open, a question sent by the Enter key is answered
    in the column under the speaker `Matsya`, with its two passages; no
    button, link or chip of the column reads `Apply to buffer`, `Discard`
    or `@`; a question that holds `silent` is answered by the one sentence
    NO_ANSWER, and a key typed in the editor afterwards changes the
    editor's document. On a server started with `matsya_command="off"` no
    Matsya column, handle or fold button stands, and the three columns have
    the widths OFF_TRACKS gives, with the folder open, with the folder
    folded by the reader and at 1080 px, where the width function folds the
    folder, the window having no left padding since unit N's Task 1 and no
    right margin since design pass 13 §4 (Q-D6)."""
    record = build_record(FONTS_README)
    assert set(record) == set(FONT_FILES.values())
    for relpath, (size, digest) in record.items():
        data = (WORKBENCH / relpath).read_bytes()
        assert (len(data), hashlib.sha256(data).hexdigest()) == (size, digest), relpath
        name = relpath.rsplit("/", 1)[1]
        with urllib.request.urlopen(f"{server}static/assets/fonts/{name}", timeout=5) as response:
            assert response.read() == data, name
    for name in ("archivo license", "plex license"):
        text = (WORKBENCH / FONT_FILES[name]).read_text(encoding="utf-8")
        assert "SIL Open Font License, Version 1.1" in text, name
    assert len(FLOW_FILES) == 7
    assert set(build_record(FLOW_README)) == set(FLOW_FILES.values())

    # the network closed: the page draws, its fonts asked of the server
    # alone, and every text and every symbol drawn in a face it loaded
    requested = origin_alone(page, server)
    open_cons(page, server)
    page.wait_for_selector(".bl-class-row", timeout=10_000)
    fonts = [relpath.rsplit("/", 1)[1] for relpath in FONT_FILES.values()]
    fonts = [name for name in fonts if name.endswith(".woff2")]
    assert {f"{server}static/assets/fonts/{name}" for name in fonts} <= set(requested)
    drawn = fonts_drawn(page, under=".bl-window")
    system = {face for faces in drawn.values() for face in faces if not face.endswith(" (custom)")}
    assert drawn and system == set(), system
    assert {
        (symbol, stack): faces
        for symbol, stacks in symbol_faces(page).items()
        for stack, faces in stacks.items()
        if faces != {"STIX Two Math (custom)"}
    } == {}

    # a question answered in the column, no action of unit Q, a silent
    # service told in one sentence while the editor takes keys
    field = page.locator(".bl-matsya-field textarea")
    field.fill("What does a stage file denote?")
    field.press("Enter")
    answers = page.locator(".bl-matsya-answer")
    wait_until(lambda: answers.count() == 1, 10.0, "the answer")
    assert page.locator(".bl-matsya-speaker").all_text_contents() == ["Matsya"]
    assert page.locator(".bl-matsya-passage").all_text_contents() == list(STUB_PASSAGES)
    assert page.evaluate(COLUMN_ACTIONS_JS, ["Apply to buffer", "Discard", "@"]) == []
    field.fill("Is the service silent?")
    page.click(".bl-matsya-ask")
    wait_until(lambda: answers.count() == 2, 10.0, "the sentence")
    assert answers.nth(1).text_content() == matsya_client.NO_ANSWER
    assert page.locator(".bl-matsya-passage").count() == len(STUB_PASSAGES)
    typed = edited(original, 1, original.split("\n")[0] + "X")
    click_line(page, 1)
    page.keyboard.press("End")
    page.keyboard.type("X")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == typed, 5.0, "the key typed in the editor")
    page.keyboard.press("ControlOrMeta+z")
    wait_until(lambda: page.evaluate(DOCUMENT_JS) == original, 5.0, "one undo of the key")

    # the setting `off`: no column, and the three columns of the folder,
    # the text and the graph, on a server of another origin
    page.unroute("**/*")
    open_cons(page, server_on(model_folder, None, "off"))
    for selector in (".bl-matsya", '.bl-handle[data-handle="matsya"]', '[data-fold="matsya"]'):
        assert page.locator(selector).count() == 0, selector
    assert tracks_near(page, OFF_TRACKS[1600, False]), tracks(page)
    fold = page.locator('.bl-fold[data-fold="folder"]')
    fold.click()
    wait_until(lambda: tracks_near(page, OFF_TRACKS[1600, True]), 5.0, "the folder folded")
    fold.click()
    wait_until(lambda: tracks_near(page, OFF_TRACKS[1600, False]), 5.0, "the folder opened")
    page.set_viewport_size({"width": 1080, "height": 1000})
    wait_until(lambda: tracks_near(page, OFF_TRACKS[1080, False]), 5.0, "the narrowed columns")
