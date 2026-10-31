"""The acceptance tests of unit N of model interface specification 0.4, the
recipe, the cables and stage editing (the plan "Unit N of model interface
spec 0.4, the recipe, the cables and stage editing: implementation plan"):
one test for each task's acceptance check, each reading the page's
elements, never a screenshot's pixels. Deleted when the next amendment is
accepted (lean implementation rule, layer 2).
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from workbench_support import (
    DETAILS_ROWS_JS,
    DOCUMENT_JS,
    HELD_COLLECTION_JS,
    KEEPER_CONS,
    RECIPE_FILE,
    REGION_READING_JS,
    RETIREMENT_CHOICE,
    TENURE,
    VIEW_STATE_JS,
    WORKER_SAVING,
    attribute_of,
    boxes,
    breadcrumb,
    cable_list,
    cable_port,
    cable_ports,
    choose_option,
    choose_view,
    click_join,
    click_line,
    double_click_node,
    error_lines,
    file_bytes,
    flow_handle,
    gesture_note,
    graph_named,
    held_events,
    history_buttons,
    hold_events,
    init_repository,
    join_wires_drawn,
    layout_records,
    line_text,
    move_join_end,
    lay_out_left_to_right,
    new_tab,
    occurrences_of,
    open_file,
    open_path_shown,
    open_recipe_row,
    open_tree_file,
    open_trellis,
    opened_namespaces,
    property_color,
    recipe_head,
    recipe_rows_at_rest,
    record_layouts,
    release_events,
    restrict,
    restriction_shown,
    reveal_in_tree,
    select_until,
    unsaved_in_tree,
    view_still,
    viewport,
    wait_until,
)

from bellman.stage import LAYER_ID_ENDING

# The rows of the page's chrome (design pass 10 §2), each by its element:
# the main bar, the Files head, the tabs' row over the editor and the graph
# bar, each as its top and its height.
CHROME_ROWS = {
    "main bar": ".bl-main-bar",
    "Files head": ".bl-folder-rail",
    "tabs' row": ".bl-tab-row",
    "graph bar": ".bl-graph-bar",
}

# The main bar as the page draws it (design pass 10 §3): its three groups by
# their classes; the mark's source and height; for each icon button of
# VSCode Elements its class, its accessible name and whether it is
# disabled; and each toggle's fold.
MAIN_BAR_JS = r"""
() => {
  const bar = document.querySelector('.bl-main-bar');
  const mark = bar.querySelector('.bl-mark img');
  return {
    groups: Array.from(bar.children, (group) => group.className),
    mark: [mark.getAttribute('src'), mark.getBoundingClientRect().height],
    buttons: Array.from(bar.querySelectorAll('vscode-toolbar-button'), (button) =>
      [button.className, button.getAttribute('label'),
       button.getAttribute('aria-disabled') === 'true']),
    toggles: Array.from(bar.querySelectorAll('.bl-toggle'), (toggle) => toggle.dataset.fold),
    // the toggles of each end of the bar, at the end on which their panels open (design pass 14 §10)
    startToggles: Array.from(bar.querySelector('.bl-main-start').querySelectorAll('.bl-toggle'), (toggle) => toggle.dataset.fold),
    endToggles: Array.from(bar.querySelector('.bl-main-end').querySelectorAll('.bl-toggle'), (toggle) => toggle.dataset.fold),
  };
}
"""

# The elements of the window, outside the editor's text and the status line,
# one of whose own texts holds the word `BellmanSym`, each as the start of its
# markup. The status line names the open stage file's language by that word
# (spec 0.4 §5.7; N-I8), and the editor shows the file's own words.
BELLMANSYM_JS = r"""
() => Array.from(document.querySelectorAll('.bl-window *'))
  .filter((element) => !element.closest('.cm-editor, .bl-status'))
  .filter((element) => Array.from(element.childNodes).some(
    (node) => node.nodeType === Node.TEXT_NODE && node.textContent.includes('BellmanSym')))
  .map((element) => element.outerHTML.slice(0, 80))
"""

# The path of the main bar as the browser draws it (design pass 10 §3):
# whether its parts are wider than its box, the left edge of its first part
# and the right edge of its last relative to the box, the vertical centers
# of its parts, its direction, its cut and its wrapping, and its hover and
# its text.
PATH_CUT_JS = r"""
() => {
  const path = document.querySelector('.bl-crumbs');
  const box = path.getBoundingClientRect();
  const parts = Array.from(path.querySelectorAll('.bl-crumb'), (part) =>
    part.getBoundingClientRect());
  const style = getComputedStyle(path);
  return {
    wider: path.scrollWidth > path.clientWidth,
    first: parts[0].left - box.left,
    last: box.right - parts[parts.length - 1].right,
    centers: parts.map((part) => part.top + part.height / 2),
    style: [style.direction, style.textOverflow, style.whiteSpace],
    title: path.getAttribute('title'),
    text: path.textContent,
  };
}
"""


def chrome_rows(tab) -> dict:
    """The top and the height of each row of CHROME_ROWS, by its name."""
    found = {}
    for name, selector in CHROME_ROWS.items():
        (box,) = boxes(tab, selector)
        found[name] = (box["top"], box["height"])
    return found


# The panel under the editor as the page draws it (design pass 10 §4): its
# strip's height, its tabs' words, the active tab's word and underline, the
# file's name with its hover; the number of text nodes of the page outside the rail
# that read `Recipe`, the rail being the left strip of icons that Task 1 of
# this unit deletes; and each row of the Recipe tab's height by its stage.
INSPECTOR_JS = r"""
() => {
  const panel = document.querySelector('.bl-file .bl-classification');
  if (!panel) return null;
  const strip = panel.querySelector('.bl-inspector-strip');
  const file = strip && strip.querySelector('.bl-inspector-file');
  const active = panel.querySelector('.bl-class-tab.bl-active');
  let recipes = 0;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.textContent.trim() !== 'Recipe') continue;
    if (node.parentElement.closest('.bl-rail')) continue;
    recipes += 1;
  }
  return {
    panel: panel.dataset.panel,
    height: strip ? strip.getBoundingClientRect().height : null,
    heads: panel.querySelectorAll('.bl-region-head, h2').length,
    tabs: Array.from(panel.querySelectorAll('.bl-class-tab'), (tab) => tab.textContent.trim()),
    active: active ? active.textContent.trim() : null,
    underline: active ? getComputedStyle(active).boxShadow : null,
    file: file ? [file.textContent.trim(), file.getAttribute('title')] : null,
    recipes,
    rows: Object.fromEntries(Array.from(panel.querySelectorAll('.bl-recipe-row'),
      (row) => [row.dataset.stage, row.getBoundingClientRect().height])),
  };
}
"""
# The color of the glyph of the Recipe tab's first icon button `New file`,
# at rest and with the refusal's mark, which the page gives the button while
# its change stands refused (test_creation.py checks when the page gives
# it); the mark is removed again before the function returns. The glyph is
# read on the button, which no page test opens to its inner elements (unit
# G, item 4): VSCode Elements draws the icon in the custom property
# `--vscode-icon-foreground`, `#cccccc` where none is set, which the button
# gives its icon, so a probe in the body takes that property's value as the
# button computes it.
NEW_FILE_GLYPH_JS = r"""
() => {
  const button = document.querySelector('.bl-recipe-table vscode-toolbar-button.bl-new-file');
  if (!button) return null;
  const glyph = () => {
    const value = getComputedStyle(button).getPropertyValue('--vscode-icon-foreground').trim();
    const probe = document.createElement('span');
    probe.style.color = value || '#cccccc';
    document.body.append(probe);
    const color = getComputedStyle(probe).color;
    probe.remove();
    return color;
  };
  const rest = glyph();
  button.classList.add('bl-refusal-mark');
  const marked = glyph();
  button.classList.remove('bl-refusal-mark');
  return [rest, marked];
}
"""
# the address of tenure's first calibration entry in the durables recipe
TENURE_CALIBRATION = "stages.tenure.calibration.all[0]"


# the generic families a font stack may end in (CSS Fonts 4 §2.1.3)
GENERIC_FAMILIES = {
    "serif",
    "sans-serif",
    "monospace",
    "cursive",
    "fantasy",
    "system-ui",
    "math",
    "ui-serif",
    "ui-sans-serif",
    "ui-monospace",
    "ui-rounded",
}

# The type of the trellis's labels as the browser computes it (design pass
# 10 §5): for the head of the period `period` and the name of the card
# `card`, each a box id, the text, the family, size, weight, style and
# color, the box on the screen, and whether the text is cut (its content
# wider than its box); the same of each wire's label; the frame of the
# period on the screen; and the last family of every font stack of the
# graph's drawing, each with the element that computes it, the icons'
# Codicon font left out.
TRELLIS_TYPE_JS = r"""
([period, card]) => {
  const host = document.querySelector('.bl-view-host');
  const node = (id) => host.querySelector(`.react-flow__node[data-id="${CSS.escape(id)}"]`);
  const at = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, right: found.right, top: found.top, bottom: found.bottom};
  };
  const typed = (element) => {
    if (!element) return null;
    const style = getComputedStyle(element);
    return {text: element.textContent,
            family: style.fontFamily.split(',')[0].replace(/"/g, '').trim(),
            size: parseFloat(style.fontSize), weight: style.fontWeight, style: style.fontStyle,
            color: element.tagName.toLowerCase() === 'text' ? style.fill : style.color,
            at: at(element), cut: element.scrollWidth > element.clientWidth + 0.5};
  };
  const frame = node(period), stage = node(card);
  const stacks = [];
  for (const element of host.querySelectorAll('.react-flow, .react-flow *')) {
    if (element.closest('.codicon')) continue;
    const family = getComputedStyle(element).fontFamily;
    stacks.push([element.className.baseVal != null ? element.className.baseVal : element.className,
                 family.split(',').pop().replace(/"/g, '').trim()]);
  }
  return {
    frame: frame ? at(frame) : null,
    head: typed(frame && frame.querySelector(':scope > .bf-layer.bf-period > .bf-layer-name')),
    name: typed(stage && stage.querySelector(
      ':scope > .bf-card > .bf-layer-name, :scope > .bf-card > .bf-name')),
    labels: Array.from(host.querySelectorAll('.react-flow__edge .bf-join'), typed),
    counts: Array.from(host.querySelectorAll('.react-flow__edge .bf-cable-count'), typed),
    stacks,
  };
}
"""


# --- Task 4: the note marker and its preview ---

# the retiree's consumption stage of the retirement model, relative to the
# copy, whose line 5 is `β : (0,1)        :: ["discount factor"]`
RETIREE_CONS = "declaration/stages/retiree_cons/retiree_cons.bl"

# the note glyphs the editor draws on its line `n`, counted from one: each
# glyph's accessible name and its place in the Tab order
LINE_GLYPHS_JS = """
(n) => Array.from(
  document.querySelectorAll('.cm-content .cm-line')[n - 1].querySelectorAll('.bl-note-marker'),
  (glyph) => ({name: glyph.getAttribute('aria-label'), tabIndex: glyph.tabIndex}))
"""

# the previews of notes the page shows: each one's text and the number of
# KaTeX formulas it typesets
NOTE_PREVIEWS_JS = """
() => Array.from(document.querySelectorAll('.cm-tooltip.bl-note'), (preview) => ({
  text: preview.textContent.trim(),
  formulas: preview.querySelectorAll('.katex').length,
}))
"""

# true where the focus stands on the note glyph of the editor's line `n`
GLYPH_FOCUSED_JS = """
(n) => {
  const focused = document.activeElement;
  return focused !== null && focused.classList.contains('bl-note-marker')
    && focused.closest('.cm-line') === document.querySelectorAll('.cm-content .cm-line')[n - 1];
}
"""

# the editor's notes drawn as written (true) or as their glyphs (false), as
# the property `show_notes` of editor.vue sets them
SHOW_NOTES_JS = "(on) => document.querySelector('.bl-editor').bellmanEditor.setShowNotes(on)"

# what hiding and previewing a note must leave as it is: the editor's
# document, the marks `unsaved` of the tabs and the desktop's reading of
# unsaved text
UNCHANGED_JS = """
() => ({
  document: window.bellmanEditor.documentOf(document.querySelector('.bl-editor')),
  unsaved: document.querySelectorAll('.bl-modified').length,
  dirty: window.__bellmanDirty,
})
"""


# --- Task 5: removal with its scope, and the chooser beside its button ---

# the durables model's trellis file, relative to the folder
TRELLIS_FILE = "declaration/trellis.yml"
# the sentence under the error mark where Backspace cannot act (N-D12)
BACKSPACE_FORWARD = "Backspace acts in the forward trellis view"

# whether the element that holds the focus is the selected join wire's
# (N-I274)
SELECTED_WIRE_FOCUSED_JS = (
    "() => !!document.activeElement && "
    "document.activeElement.matches('.bl-view-host .react-flow__edge.bf-join-wire.selected')"
)
# the two controls of Details of a selected stage occurrence, its last row,
# after its rows and its other buttons, under a hairline (design pass 10
# §7; design pass 13 §5, Q-D15): each one's tag, classes, Codicon, words and
# hover, and whether its box stands wholly within the visible part of
# Details' body; whether the row is the occurrence's last block and stands
# below its rows, and the color of the rule above it; null where Details
# draws no such row
REMOVAL_BUTTONS_JS = """
() => {
  const details = document.querySelector('section[aria-label="details"]');
  const row = details && details.querySelector('.bl-removal-buttons');
  if (!row) return null;
  const body = details.querySelector('.bl-panel-body').getBoundingClientRect();
  const block = row.parentElement;
  const rows = block.querySelector('.bl-details-rows').getBoundingClientRect();
  return {
    last: block.lastElementChild === row,
    after: row.getBoundingClientRect().top >= rows.bottom,
    rule: getComputedStyle(row).borderTopColor,
    buttons: Array.from(row.children, (button) => {
      const box = button.getBoundingClientRect();
      return {
        tag: button.tagName.toLowerCase(),
        classes: button.getAttribute('class'),
        icon: (button.querySelector('.codicon') || {className: ''}).className,
        text: button.textContent.trim(),
        title: button.getAttribute('title'),
        seen: box.height > 0 && box.top >= body.top && box.bottom <= body.bottom
          && box.left >= body.left && box.right <= body.right,
      };
    }),
  };
}
"""
# The place of an open stage list and of the button that opened it, each
# box {top, bottom, left, right} on the page, and the box of the region the
# list stands in: the graph's region `.bf-region` for the graph's list and
# the panel under the editor for the Recipe tab's; the button's
# aria-expanded; null where no list is open.
LIST_PLACE_JS = """
([listSelector, buttonSelector, regionSelector]) => {
  const list = document.querySelector(listSelector);
  const button = document.querySelector(buttonSelector);
  if (!list || !button) return null;
  const region = list.closest(regionSelector);
  const box = (element) => {
    const r = element.getBoundingClientRect();
    return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width };
  };
  return {
    list: box(list), button: box(button), region: box(region),
    expanded: button.getAttribute('aria-expanded'),
  };
}
"""
# the background of the element the selector names, and the color the
# page's hover wash `--bl-hover` resolves to there
WASH_JS = """
(selector) => {
  const element = document.querySelector(selector);
  const probe = document.createElement('div');
  probe.style.background = 'var(--bl-hover)';
  element.parentElement.appendChild(probe);
  const wash = getComputedStyle(probe).backgroundColor;
  probe.remove();
  return { background: getComputedStyle(element).backgroundColor, wash: wash };
}
"""
# The graph's stage list and the `+ stage` of periods[1]; the Recipe tab's
# button `Stage` and its list
GRAPH_LIST = ".bl-view-host .bf-stage-list"
PERIOD_ONE_ADD = (
    f'.bl-view-host .react-flow__node[data-id="periods[1]{LAYER_ID_ENDING}"] '
    "> .bf-layer > .bf-add-stage"
)
RECIPE_ADD = ".bl-recipe-add-stage"
RECIPE_LIST = ".bl-stage-chooser"
# the template of the corpus whose fields match no field of the durables
# model, the portfolio model's `port` of cons-port's lesson
PORT_TEMPLATE = "cons-port/declaration/trellis.port-cons.yml#port"


def within(inner: dict, outer: dict, slack: float = 0.5) -> bool:
    """Whether the box `inner` stands wholly within the box `outer`."""
    return (
        inner["top"] >= outer["top"] - slack
        and inner["bottom"] <= outer["bottom"] + slack
        and inner["left"] >= outer["left"] - slack
        and inner["right"] <= outer["right"] + slack
    )


def beside(place: dict) -> bool:
    """Whether a list stands beside the button that opened it (design pass
    10 §7): its top edge within 4 px of the button's bottom edge, or, flipped
    above the button, its bottom edge within 4 px of the button's top edge."""
    below = abs(place["list"]["top"] - place["button"]["bottom"]) <= 4
    above = abs(place["list"]["bottom"] - place["button"]["top"]) <= 4
    return below or above


# the cable's list over the graph (design pass 10 §7)
PAIR_LIST = ".bl-view-host .bf-pair-list"


def cable_port_selector(port: str) -> str:
    """The selector of the drawn element of the cable port whose `data-port`
    is `port` (`cable_port`)."""
    return (
        ".bl-view-host .bf-card > .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)"
        f"[data-port={json.dumps(port, ensure_ascii=False)}]"
    )


def beside_port(place: dict) -> bool:
    """Whether the cable's list stands beside the port it was dropped on, by
    the stage list's rule from its button (design pass 10 §7; `beside`): its
    top edge within 4 px of the port's bottom edge, or, flipped above the
    port, its bottom edge within 4 px of the port's top edge; and its left
    edge within 4 px of the port's left edge or, shifted left to stay inside
    the region, its right edge within 4 px of the region's right edge."""
    left = abs(place["list"]["left"] - place["button"]["left"]) <= 4
    shifted = abs(place["list"]["right"] - place["region"]["right"]) <= 4
    return beside(place) and (left or shifted)


def edges_of(collection: dict, namespace: str) -> list:
    """The edges of the forward graph of `collection`, each node's
    `incomingEdges`, that join a node of the stage occurrence `namespace`,
    `periods[1]/port`, to a node of another stage occurrence; an edge to
    the graph's own inputs or outputs, which an unjoined field's measure
    reaches, joins no two occurrences."""
    def inside(node_id):
        return node_id == namespace + LAYER_ID_ENDING or node_id.startswith(namespace + "/")

    return [
        edge
        for node in graph_named(collection, "forward")["nodes"]
        for edge in node.get("incomingEdges") or []
        if inside(node["id"]) != inside(edge["sourceNodeId"])
        and all(end.startswith("periods[") for end in (node["id"], edge["sourceNodeId"]))
    ]


# the root containers the trellis graphs held before unit N, Task 6
ROOT_CONTAINERS = ("GraphInputs", "GraphOutputs")
# the occurrences of periods[3] of the durables model that the joins leaving
# periods 0 to 2 reach
PERIOD_3 = {"periods[3]/keeper_cons", "periods[3]/adjuster_cons"}


def edge_route(edge: dict) -> dict | None:
    """The route record an edge of the graph JSON carries under its
    attribute `route`, None for an edge that carries none."""
    held = edge.get("attrs") or []
    return next((pair["value"] for pair in held if pair["key"] == "route"), None)


def occurrence_of(node: dict) -> str:
    """The address of the stage occurrence that holds a node of a trellis
    graph, `periods[2]/tenure`, read from its namespace; the empty text for
    a node at the graph's root."""
    return "/".join((node.get("namespace") or "").split("/")[:2])


def test_task_1_the_main_bar_holds_the_mark_the_history_the_path_and_the_four_toggles(
    browser, server_on, durables_folder, pension_folder
):
    """Task 1 (the brief's top bar; design pass 10 §§2 to 4; N-D4, N-D10):
    on the durables model at 1600 × 1000, with its recipe's trellis shown,
    the page's chrome is the main bar, 36 px at the window's top, and under
    it, all at 36 px, the Files head, the tabs' row and the graph bar. The
    bar holds, in three groups, the brand's mark, the silhouette at 20 px,
    the two history buttons `Back` and `Forward`, both drawn and both
    disabled while the tab has no history; the path; and `Go to` with the
    four toggles, `folder`, `inspector`, `details` and `matsya`. A double
    click on the card `periods[1]/keeper_cons` makes the path end in that
    occurrence, its last two parts `periods[1]` and `keeper_cons`, and
    enables `Back`. A click on the toggle Inspector folds the panel under
    the editor and a second click unfolds it, its aria-expanded following.
    No element of the window outside the editor's text and the status line
    reads `BellmanSym`. With `tenure.bl` opened from the tree the path names
    its occurrence once, `durables › spec.yml › tenure › periods[0]` (the
    fix wave Q3b of unit Q, item 19; C19), a path that stands whole beside
    its select of positions at the main bar's least width; with the pension
    model's `worker_saving.bl` open, whose folder's and stage's names are
    longer, at 1024 × 800 the path is wider than its box and is cut at its
    left: its last part ends within the box, its first starts before it,
    its parts stand on one line and its hover is the whole path; the toggles
    and `Go to` stand in one row in the main bar."""
    card = f"periods[1]/keeper_cons{LAYER_ID_ENDING}"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        rows = chrome_rows(tab)
        drawn = tab.evaluate(MAIN_BAR_JS)
        trellis_words = tab.evaluate(BELLMANSYM_JS)

        double_click_node(tab, card, "backward")

        def stage_of_the_occurrence() -> bool:
            # the stage's view, the switch's `Stage` active, with the path
            # ending in the occurrence the stage is bound as; the select
            # `graph` stands in both views since design pass 14 §7 and so
            # marks the stage's view no longer (S-D29)
            return (
                tab.locator(".bl-stage-button.bl-active").count() == 1
                and breadcrumb(tab) == "durables › spec.yml › periods[1] › keeper_cons"
                and recipe_head(tab) == "periods[1] / keeper_cons"
            )

        wait_until(stage_of_the_occurrence, 60.0, "the path ending in the occurrence")
        named = tab.locator(".bl-crumbs .bl-occurrence-crumb").all_text_contents()
        wait_until(lambda: history_buttons(tab) == (1, 0), 10.0, "Back enabled")
        head = recipe_head(tab)

        toggle = tab.locator('.bl-main-bar .bl-fold[data-fold="inspector"]')
        panel = tab.locator(".bl-classification")
        wait_until(lambda: panel.is_visible(), 30.0, "the panel under the editor")
        assert toggle.get_attribute("aria-expanded") == "true"
        toggle.click()
        wait_until(lambda: not panel.is_visible(), 5.0, "the panel folded")
        folded = toggle.get_attribute("aria-expanded")
        toggle.click()
        wait_until(lambda: panel.is_visible(), 5.0, "the panel unfolded")
        unfolded = toggle.get_attribute("aria-expanded")
        stage_words = tab.evaluate(BELLMANSYM_JS)

        reveal_in_tree(tab, TENURE)
        tab.click(f'.bl-tree-file[data-path="{TENURE}"]')
        # the path names the occurrence once, its key and its period (the fix
        # wave Q3b of unit Q, item 19; C19)
        wait_until(
            lambda: breadcrumb(tab) == "durables › spec.yml › tenure › periods[0]",
            60.0,
            "the path of tenure.bl",
        )
        wait_until(lambda: recipe_head(tab) == "periods[0] / tenure", 60.0, "the occurrence")
        # a path wider than the main bar's middle at its least width: the
        # pension model's worker, beside its select of positions
        open_file(tab, server_on(pension_folder), WORKER_SAVING, minimum=4)
        wait_until(
            lambda: recipe_head(tab) == "periods[0] / worker_saving",
            60.0,
            "the worker's occurrence",
        )
        tab.set_viewport_size({"width": 1024, "height": 800})
        wait_until(lambda: tab.evaluate(PATH_CUT_JS)["wider"], 10.0, "the path cut at 1024 px")
        cut = tab.evaluate(PATH_CUT_JS)
        end = boxes(tab, ".bl-main-bar .bl-main-end > *")
    finally:
        context.close()

    print(f"task 1: the rows {rows}; the bar {drawn}; the path at 1024 px {cut}")
    # the three rows of chrome (design pass 10 §2)
    assert rows["main bar"] == (0, 36), rows
    assert {top for top, _ in list(rows.values())[1:]} == {36}, rows
    # the main bar's three groups and what they hold (§3)
    assert drawn["groups"] == ["bl-main-start", "bl-main-path", "bl-main-end"]
    assert drawn["mark"][0].endswith("/static/assets/brand/favicon.svg")
    assert abs(drawn["mark"][1] - 20) <= 0.5, drawn["mark"]
    assert drawn["buttons"] == [
        ["bl-back", "Back", True],
        ["bl-forward", "Forward", True],
        ["bl-goto-button", "Go to", False],
    ]
    assert drawn["toggles"] == ["folder", "inspector", "details", "matsya"]
    # each panel's toggle at the end of the bar on which its panel opens (design pass 14 §10; S-D16)
    assert drawn["startToggles"] == ["folder", "inspector"], drawn
    assert drawn["endToggles"] == ["details", "matsya"], drawn
    # the path ending in the selected occurrence
    assert named == ["periods[1]", "keeper_cons"]
    assert head == "periods[1] / keeper_cons"
    # the Inspector folded and unfolded
    assert (folded, unfolded) == ("false", "true")
    # no element reads `BellmanSym`
    assert trellis_words == [] and stage_words == [], (trellis_words, stage_words)
    # at 1024 px the path cut at its left, on one line, and the right group
    # in one row
    assert cut["wider"], cut
    assert cut["first"] < 0 and cut["last"] >= -0.5, cut
    assert max(cut["centers"]) - min(cut["centers"]) <= 2, cut
    assert cut["style"] == ["rtl", "ellipsis", "nowrap"], cut
    assert cut["title"] == cut["text"], cut
    assert len({round(box["top"]) for box in end}) == 1, end
    assert all(box["bottom"] <= 36 for box in end), end


def test_task_2_the_inspector_has_one_strip_and_a_stage_s_bindings_stand_on_one_line(
    browser, server_on, scratch_durables, lifecycle_folder
):
    """Task 2 (the brief, § Recipe and the shared panel; design pass 10 §4;
    N-D4, N-D5), at 1600 × 1000. With the durables recipe open, the panel
    under the editor has no head: its strip is 28 px and reads the one tab
    `Recipe`, underlined 2 px in the accent, and the file's name
    `spec.yml`, its path the name's hover, and the text `Recipe` stands
    once in the page. A choice of `wage_schedule`
    in tenure's first calibration select, tenure's row opened by a click
    (design pass 11 §2), writes that one replacement into
    the recipe's text, the file on disk unchanged, and one Command+Z
    restores the text (unit M, Task 10). On the lifecycle registry, whose
    stage `port` binds one entry of each kind, port's row is at most 40 px
    high at rest and open, the other rows then at rest, and the glyph of
    `New file` in cons's row opened is a row's act, ink-3 while the pointer
    is off the row and ink-2 while it is over it (design pass 13 §5; E13),
    and drawn in the refusal's color while refused in both. With
    `keeper_cons.bl` open the strip reads the four tabs and the
    file's name; a click on `Methods` shows that tab, and the choice stands
    with `tenure.bl` open and again with `keeper_cons.bl` open."""
    recipe_file = scratch_durables / RECIPE_FILE
    recipe_text = recipe_file.read_text(encoding="utf-8")
    chosen_text = recipe_text.replace(
        "tenure:        {stage: stages/tenure/tenure.bl,               "
        "calibration: {all: [calibration/durables,",
        "tenure:        {stage: stages/tenure/tenure.bl,               "
        "calibration: {all: [calibration/wage_schedule,",
    )
    assert chosen_text != recipe_text
    context, tab = new_tab(browser)
    try:
        url = server_on(scratch_durables)
        open_trellis(tab, url, RECIPE_FILE)
        tab.wait_for_selector(".bl-recipe-table .bl-recipe-row", timeout=60_000)
        tab.mouse.move(1200, 500)
        drawn = tab.evaluate(INSPECTOR_JS)
        print(f"task 2: the Recipe tab's strip and rows: {drawn}")
        assert (drawn["panel"], drawn["heads"]) == ("recipe", 0), drawn
        assert abs(drawn["height"] - 28) <= 0.5, drawn
        assert (drawn["tabs"], drawn["active"]) == (["Recipe"], "Recipe"), drawn
        assert drawn["file"] == ["spec.yml", RECIPE_FILE], drawn
        assert drawn["recipes"] == 1, drawn
        accent = property_color(tab, "--bl-accent")
        assert drawn["underline"] == f"{accent} 0px -2px 0px 0px inset", drawn

        # one replacement of the recipe's text, which one undo restores
        open_recipe_row(tab, "tenure")
        entry = f'.bl-recipe-entry[data-address="{TENURE_CALIBRATION}"]'
        choose_option(tab, entry, "wage_schedule")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == chosen_text, 30.0, "wage_schedule written")
        assert recipe_file.read_text(encoding="utf-8") == recipe_text
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == recipe_text, 10.0, "the choice undone")
        assert recipe_file.read_text(encoding="utf-8") == recipe_text

        # a row of one entry per kind
        open_trellis(tab, server_on(lifecycle_folder), RECIPE_FILE, minimum=10)
        tab.wait_for_selector('.bl-recipe-row[data-stage="port"]', timeout=60_000)
        rows = tab.evaluate(INSPECTOR_JS)["rows"]
        print(f"task 2: the lifecycle registry's rows: {rows}")
        assert rows["port"] <= 40, rows
        # port's row open, the others at rest (design pass 11 §2)
        open_recipe_row(tab, "port")
        tab.mouse.move(1200, 500)
        rows = tab.evaluate(INSPECTOR_JS)["rows"]
        print(f"task 2: the lifecycle registry's rows, port open: {rows}")
        assert rows["port"] <= 40, rows
        expanded = {key: row["expanded"] for key, row in recipe_rows_at_rest(tab).items()}
        assert expanded == {"port": True, "cons": False, "disc": False}, expanded
        # cons's row open, which holds the one `New file`, a row's act: ink-3
        # with the pointer off the row and ink-2 with it over the row, in the
        # refusal's color while refused (design pass 13 §5; E13)
        open_recipe_row(tab, "cons")
        alarm = property_color(tab, "--bl-alarm")
        tab.mouse.move(1, 999)
        glyph = tab.evaluate(NEW_FILE_GLYPH_JS)
        print(f"task 2: the glyph of New file off its row and refused: {glyph}")
        assert glyph == [property_color(tab, "--bl-ink-3"), alarm], glyph
        tab.hover('.bl-recipe-row[data-stage="cons"] .bl-recipe-key')
        glyph = tab.evaluate(NEW_FILE_GLYPH_JS)
        print(f"task 2: the glyph of New file under the row's pointer and refused: {glyph}")
        assert glyph == [property_color(tab, "--bl-ink-2"), alarm], glyph

        # the strip of a stage file, and the tab chosen over a file switch
        open_file(tab, url, KEEPER_CONS)
        types = '.bl-classification[data-panel="types"] .bl-class-row'
        tab.wait_for_selector(types, timeout=60_000)
        drawn = tab.evaluate(INSPECTOR_JS)
        assert abs(drawn["height"] - 28) <= 0.5, drawn
        assert drawn["tabs"] == ["Fields", "Parameters", "Settings", "Methods"], drawn
        assert drawn["file"] == ["keeper_cons.bl", KEEPER_CONS], drawn
        assert drawn["heads"] == 0, drawn
        tab.click('.bl-class-tab[data-tab="Methods"]')
        tab.wait_for_selector('.bl-values[data-tab="Methods"]', timeout=10_000)
        reveal_in_tree(tab, TENURE)
        tab.click(f'.bl-tree-file[data-path="{TENURE}"]')
        wait_until(
            lambda: (tab.evaluate(INSPECTOR_JS) or {}).get("file") == ["tenure.bl", TENURE],
            30.0,
            "tenure.bl in the strip",
        )
        assert tab.evaluate(INSPECTOR_JS)["active"] == "Methods"
        tab.click(f'.bl-tree-file[data-path="{KEEPER_CONS}"]')
        wait_until(
            lambda: (tab.evaluate(INSPECTOR_JS) or {}).get("file")
            == ["keeper_cons.bl", KEEPER_CONS],
            30.0,
            "keeper_cons.bl in the strip again",
        )
        assert tab.evaluate(INSPECTOR_JS)["active"] == "Methods"
        tab.wait_for_selector('.bl-values[data-tab="Methods"]', timeout=10_000)
    finally:
        context.close()


def test_task_3_a_period_s_head_and_a_stage_s_name_have_their_own_type(
    browser, server_on, durables_folder
):
    """Task 3 (design pass 10 §5; the brief's "Period and stage label
    typography"). On the durables model's backward trellis graph of
    `declaration/spec.yml`, periods 0 to 2, at the opening: the head of
    periods[0] is `periods[0]` in IBM Plex Mono at 11 px, weight 400, in
    ink-3, upright, within the period's head, G.periodHeader high; the name
    of the card `keeper_cons` of periods[0] is exactly `keeper_cons`, with
    its underscore, in IBM Plex Mono at 12.5 px, weight 500, in ink-1,
    upright and not cut; no cable draws a label, its branch standing first
    in its title (the fix wave Q3a of unit Q, item 4, which amends Q-D17
    and design pass 13 §1, rule 7), and every count at a plug is in IBM
    Plex Mono at 9.5 px in ink-3 (design pass 13 §1, rule 5); and every
    font stack of the graph's
    drawing ends in a generic family, so that a face that does not load
    falls to a face of its kind."""
    period = f"periods[0]{LAYER_ID_ENDING}"
    card = f"periods[0]/keeper_cons{LAYER_ID_ENDING}"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)

        def drawn():
            found = tab.evaluate(TRELLIS_TYPE_JS, [period, card])
            return found if found["head"] and found["name"] and found["counts"] else None

        found, _ = wait_until(drawn, 60.0, "the head of periods[0] and the card keeper_cons")
        zoom = viewport(tab)["zoom"]
        header = tab.evaluate("() => window.BellmanFlowLayout.G.periodHeader")
        ink = {name: property_color(tab, f"--bl-ink-{name}") for name in (1, 2, 3)}

        head = found["head"]
        assert (head["text"], head["family"], head["size"], head["weight"], head["style"]) == (
            "periods[0]",
            "IBM Plex Mono",
            11.0,
            "400",
            "normal",
        ), head
        assert head["color"] == ink[3] and not head["cut"], head
        frame = found["frame"]
        assert frame["top"] - 0.5 <= head["at"]["top"], (frame, head)
        assert head["at"]["bottom"] <= frame["top"] + header * zoom + 0.5, (frame, head, header)

        name = found["name"]
        assert (name["text"], name["family"], name["size"], name["weight"], name["style"]) == (
            "keeper_cons",
            "IBM Plex Mono",
            12.5,
            "500",
            "normal",
        ), name
        assert name["color"] == ink[1] and not name["cut"], name

        # no cable draws a label (the fix wave Q3a, item 4)
        assert found["labels"] == [], found["labels"]
        assert found["counts"], "no count drawn at a plug"
        for count in found["counts"]:
            assert (count["family"], count["size"]) == ("IBM Plex Mono", 9.5), count
            assert count["color"] == ink[3], count

        stacks = found["stacks"]
        assert stacks and [s for s in stacks if s[1] not in GENERIC_FAMILIES] == [], stacks
        print(
            f"task 3: head {head['size']} px {head['weight']}, keeper_cons {name['size']} px "
            f"{name['weight']}, {len(found['labels'])} cable labels, {len(found['counts'])} counts, "
            f"{len(stacks)} stacks read"
        )
    finally:
        context.close()


def test_task_4_a_note_is_a_glyph_whose_preview_hover_and_focus_open_and_enter_reveals(
    browser, server_on, retirement_folder
):
    """Task 4 (AAS's brief, § Rendered annotation comments; design pass 10
    §9): with the retirement model's `retiree_cons.bl` open, line 5 draws
    its note as one glyph named `note`, in the Tab order, and not the words
    `discount factor`. The pointer resting on the glyph opens a
    `.cm-tooltip.bl-note` holding `discount factor`, which stays while the
    pointer is over it and closes when the pointer leaves both; the
    editor's `setShowNotes` draws the note as written and then as its glyph
    again; Escape and then Tab from the text bring the focus to the
    glyph, which opens the preview too, and Escape closes it; Enter on the
    glyph draws line 5 as written, with the focus in the text, until the
    cursor leaves the line. The editor's document, the tabs' marks `unsaved`
    and `window.__bellmanDirty` are unchanged throughout. `\\(β\\)` typed
    into the note of line 5, and the cursor moved off the line, the glyph's
    preview typesets one KaTeX formula; one undo restores the file's
    text."""
    text = (retirement_folder / RETIREE_CONS).read_text(encoding="utf-8")
    lines = text.split("\n")
    assert lines[4] == 'β : (0,1)        :: ["discount factor"]'
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(retirement_folder), RETIREE_CONS)
        wait_until(
            lambda: tab.evaluate(LINE_GLYPHS_JS, 5) == [{"name": "note", "tabIndex": 0}],
            10.0,
            "the glyph of line 5",
        )
        assert line_text(tab, 5) == "β : (0,1)        :: []"
        before = tab.evaluate(UNCHANGED_JS)
        assert before == {"document": text, "unsaved": 0, "dirty": False}, before

        # the pointer on the glyph, then on the preview, then away from both
        glyph = tab.locator(".cm-content .cm-line").nth(4).locator(".bl-note-marker")
        glyph.hover()
        wait_until(
            lambda: tab.evaluate(NOTE_PREVIEWS_JS) == [{"text": "discount factor", "formulas": 0}],
            5.0,
            "the preview under the pointer",
        )
        tab.locator(".cm-tooltip.bl-note").hover()
        tab.wait_for_timeout(600)
        assert tab.evaluate(NOTE_PREVIEWS_JS) == [{"text": "discount factor", "formulas": 0}]
        tab.mouse.move(2, 2)
        wait_until(lambda: tab.evaluate(NOTE_PREVIEWS_JS) == [], 5.0, "the preview closed")

        # the toggle `Notes` draws every note as written, and again as its
        # glyph (setShowNotes, the property `show_notes` of the editor)
        tab.evaluate(SHOW_NOTES_JS, True)
        wait_until(lambda: line_text(tab, 5) == lines[4], 5.0, "the notes as written")
        tab.evaluate(SHOW_NOTES_JS, False)
        wait_until(lambda: line_text(tab, 5) == "β : (0,1)        :: []", 5.0, "the glyphs again")
        assert tab.evaluate(UNCHANGED_JS) == before

        # the keyboard: Escape and then Tab from the text, then Escape
        click_line(tab, 1)
        tab.keyboard.press("Escape")
        tab.keyboard.press("Tab")
        wait_until(lambda: tab.evaluate(GLYPH_FOCUSED_JS, 5), 5.0, "the focus on the glyph")
        wait_until(
            lambda: tab.evaluate(NOTE_PREVIEWS_JS) == [{"text": "discount factor", "formulas": 0}],
            5.0,
            "the preview of the focused glyph",
        )
        tab.keyboard.press("Escape")
        wait_until(lambda: tab.evaluate(NOTE_PREVIEWS_JS) == [], 5.0, "the preview closed")
        assert tab.evaluate(GLYPH_FOCUSED_JS, 5)
        assert tab.evaluate(UNCHANGED_JS) == before

        # Enter draws the line as written until the cursor leaves it
        tab.keyboard.press("Enter")
        wait_until(lambda: line_text(tab, 5) == lines[4], 5.0, "line 5 as written")
        assert tab.evaluate("() => document.activeElement.classList.contains('cm-content')")
        assert tab.evaluate(UNCHANGED_JS) == before
        tab.keyboard.press("ArrowUp")
        wait_until(lambda: line_text(tab, 5) == "β : (0,1)        :: []", 5.0, "the glyph again")
        assert tab.evaluate(UNCHANGED_JS) == before

        # a formula typed into the note, previewed once the cursor leaves
        glyph.click()
        wait_until(lambda: line_text(tab, 5) == lines[4], 5.0, "line 5 as written")
        tab.keyboard.type("\\(β\\) ")
        typed = text.replace('["discount factor"]', '["\\(β\\) discount factor"]')
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == typed, 5.0, "the formula typed")
        tab.keyboard.press("ArrowUp")
        wait_until(lambda: tab.evaluate(LINE_GLYPHS_JS, 5) != [], 5.0, "the glyph of the new note")
        glyph.hover()

        def typeset() -> bool:
            shown = tab.evaluate(NOTE_PREVIEWS_JS)
            return (
                len(shown) == 1
                and shown[0]["formulas"] == 1
                and shown[0]["text"].endswith("discount factor")
            )

        wait_until(typeset, 5.0, "the typeset formula")
        tab.mouse.move(2, 2)
        tab.locator(".cm-content").focus()
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 5.0, "one undo of the typing")
    finally:
        context.close()


def test_task_5_removal_names_its_scope_and_undoes_once_and_the_chooser_opens_beside_its_button(
    browser, server_on, scratch_durables
):
    """Task 5 (the brief's § Removing and adding stages; design pass 10 §7;
    N-D8, N-D12). On a copy of the durables model with its recipe open and
    the forward trellis graph shown: `periods[0]/bequest` selected, Details
    draws as its last row, after its rows under a hairline, `Remove from
    periods 0` and `Remove stage`, text buttons with the Codicon `trash`
    (design pass 13 §5; Q-D15), in view once the row is scrolled to, each
    with the pass's hover naming its scope.
    Backspace on the selected card removes the occurrence; since trellis.yml's
    list was bequest's only one, the recipe's row leaves in the same gesture:
    trellis.yml, opened at the line, holds the list without bequest and the
    connector emptied, the graph draws no bequest, the recipe's text holds
    no row of bequest and the Recipe tab no row, and the status line names
    the list and the row; one Mod-z restores the recipe, trellis.yml, the
    Recipe tab and the graph, no file left unsaved. In the backward graph,
    Backspace on the selected card removes nothing and the list under the
    error mark says `Backspace acts in the forward trellis view`. A click on
    periods[1]'s `+ stage` opens the stage list with its top edge within 4
    px of the button's bottom edge, within the region, the button pressed;
    the item
    under the pointer takes the hover wash, and Escape closes the list. The
    Recipe tab's `Stage` opens the same list beside the button, within the
    panel, and Escape closes it. The portfolio model's `port`, whose fields
    match nothing in durables, added to periods[1] from the list, is drawn
    with no wire, and the note says `port unconnected`."""
    root = scratch_durables
    names = (RECIPE_FILE, TRELLIS_FILE)
    texts = {name: (root / name).read_text(encoding="utf-8") for name in names}
    rows = [line for line in texts[RECIPE_FILE].splitlines(True) if line.startswith("  bequest:")]
    assert len(rows) == 1
    occurrence = f"periods[0]/bequest{LAYER_ID_ENDING}"
    card = f'.bl-view-host .react-flow__node[data-id="{occurrence}"]'
    recipe_row = '.bl-recipe-row[data-stage="bequest"]'
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(root), RECIPE_FILE)
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward trellis")

        # Details of the selected occurrence: two controls with their scopes
        select_until(
            tab,
            occurrence,
            "forward",
            lambda: tab.evaluate(REMOVAL_BUTTONS_JS) is not None,
            "Details of periods[0]/bequest",
            60.0,
        )
        removal_row = tab.locator("section[aria-label='details'] .bl-removal-buttons")
        removal_row.scroll_into_view_if_needed()
        removal = tab.evaluate(REMOVAL_BUTTONS_JS)
        controls = removal["buttons"]
        assert [(c["text"], c["title"]) for c in controls] == [
            ("Remove from periods 0", "Takes bequest out of trellis.yml, which writes periods 0"),
            (
                "Remove stage",
                "Removes bequest from spec.yml and every period; its files are deleted on save "
                "unless another recipe names them",
            ),
        ]
        assert all(c["seen"] for c in controls), controls
        assert all(
            c["tag"] == "button"
            and "bl-text-button" in c["classes"]
            and "codicon-trash" in c["icon"]
            for c in controls
        ), controls
        hairline = property_color(tab, "--bl-hairline")
        placed = (removal["last"], removal["after"], removal["rule"])
        assert placed == (True, True, hairline), removal

        # Backspace on the selected card
        tab.click(f"{card} .bf-layer-name")
        wait_until(lambda: flow_handle(tab, "selection") == occurrence, 10.0, "bequest selected")
        tab.keyboard.press("Backspace")
        note, _ = wait_until(lambda: gesture_note(tab), 30.0, "the removal's note")
        assert note.startswith(
            "trellis.yml, periods[0].stages: bequest removed, periods 0; "
            "spec.yml, stages: bequest removed; "
        ), note
        without = (
            texts[TRELLIS_FILE]
            .replace(
                "  - stages: [tenure, keeper_cons, adjuster_cons, bequest]\n",
                "  - stages: [tenure, keeper_cons, adjuster_cons]\n",
            )
            .replace(
                "{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, "
                "h_nxt_adj: h_bq, z_nxt_adj: z_bq}",
                "{}",
            )
        )
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == without, 30.0, "trellis.yml opened")
        wait_until(lambda: tab.locator(card).count() == 0, 120.0, "bequest's card gone")
        assert unsaved_in_tree(tab) == sorted([RECIPE_FILE, TRELLIS_FILE])
        tab.click(f'.bl-tab[data-path="{RECIPE_FILE}"]')
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == texts[RECIPE_FILE].replace(rows[0], ""),
            30.0,
            "the recipe without bequest's row",
        )
        wait_until(lambda: tab.locator(".bl-recipe-row").count() > 0, 30.0, "the Recipe tab")
        assert tab.locator(recipe_row).count() == 0

        # one Mod-z restores the recipe, trellis.yml, the Recipe tab and the
        # graph
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == texts[RECIPE_FILE], 30.0, "the recipe restored"
        )
        wait_until(lambda: unsaved_in_tree(tab) == [], 30.0, "no file left unsaved")
        wait_until(lambda: tab.locator(recipe_row).count() == 1, 120.0, "bequest's row back")
        wait_until(lambda: tab.locator(card).count() == 1, 120.0, "bequest's card back")

        # Backspace in the backward graph removes nothing and says why (N-D12)
        choose_view(tab, None, "backward")
        wait_until(lambda: tab.locator(card).count() == 1, 60.0, "bequest's backward card")
        tab.click(f"{card} .bf-layer-name")
        wait_until(lambda: flow_handle(tab, "selection") == occurrence, 10.0, "bequest selected")
        tab.keyboard.press("Backspace")
        wait_until(
            lambda: BACKSPACE_FORWARD in [sentence for sentence, _, _ in error_lines(tab)],
            10.0,
            "the sentence of Backspace under the error mark",
        )
        assert tab.evaluate(DOCUMENT_JS) == texts[RECIPE_FILE] and unsaved_in_tree(tab) == []
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward trellis")

        # the graph's `+ stage` opens the list beside it
        tab.click(".bl-zoom-button[data-zoom='fit']")
        tab.click(PERIOD_ONE_ADD)
        place, _ = wait_until(
            lambda: tab.evaluate(LIST_PLACE_JS, [GRAPH_LIST, PERIOD_ONE_ADD, ".bf-region"]),
            10.0,
            "the stage list of periods[1]",
        )
        assert abs(place["list"]["top"] - place["button"]["bottom"]) <= 4, place
        assert within(place["list"], place["region"]) and place["expanded"] == "true", place
        assert place["list"]["width"] == 280, place
        item = f'{GRAPH_LIST} .bf-stage-item[data-item="{PORT_TEMPLATE}"]'
        tab.hover(item)
        wash = tab.evaluate(WASH_JS, item)
        assert wash["background"] == wash["wash"], wash
        tab.keyboard.press("Escape")
        wait_until(lambda: tab.locator(GRAPH_LIST).count() == 0, 10.0, "the list closed")
        graph_place = place

        # the Recipe tab's `Stage` opens the same list beside it
        tab.locator(RECIPE_ADD).scroll_into_view_if_needed()
        tab.click(RECIPE_ADD)
        place, _ = wait_until(
            lambda: tab.evaluate(LIST_PLACE_JS, [RECIPE_LIST, RECIPE_ADD, ".bl-classification"]),
            10.0,
            "the Recipe tab's stage list",
        )
        assert beside(place) and within(place["list"], place["region"]), place
        assert place["expanded"] == "true", place
        assert tab.locator(f'{RECIPE_LIST} .bf-stage-item[data-item="{PORT_TEMPLATE}"]').count()
        tab.focus(f'{RECIPE_LIST} .bf-stage-item[data-item="{PORT_TEMPLATE}"]')
        tab.keyboard.press("Escape")
        wait_until(lambda: tab.locator(RECIPE_LIST).count() == 0, 10.0, "the list closed")

        # a stage whose fields match nothing stands unconnected
        tab.click(PERIOD_ONE_ADD)
        wait_until(lambda: tab.locator(GRAPH_LIST).count() == 1, 10.0, "the list again")
        tab.click(f'{GRAPH_LIST} .bf-stage-item[data-item="{PORT_TEMPLATE}"]')
        added, _ = wait_until(
            lambda: (note := gesture_note(tab)) and "port written" in note and note,
            30.0,
            "the addition's note",
        )
        assert added.startswith("period.yml, stages: port written, periods 1–50;"), added
        assert added.endswith("; port unconnected"), added
        port_card = f'.bl-view-host .react-flow__node[data-id="periods[1]/port{LAYER_ID_ENDING}"]'
        wait_until(lambda: tab.locator(port_card).count() == 1, 120.0, "port's card drawn")
        assert edges_of(tab.evaluate(HELD_COLLECTION_JS), "periods[1]/port") == []
        print(
            f"task 5: Details' controls {controls}; the graph's list at {graph_place}; "
            f"the Recipe tab's list at {place}; the addition's note {added!r}"
        )
    finally:
        context.close()


# Each boundary marker's label as the browser draws it (design pass 10 §6;
# N-I277): the region's box on the screen, and each marker's kind, its
# label's text and its label's box.
MARKER_LABELS_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host').getBoundingClientRect();
  return {
    region: {left: host.left, right: host.right, top: host.top, bottom: host.bottom},
    labels: Array.from(document.querySelectorAll('.bl-view-host .bf-marker'), (marker) => {
      const label = marker.querySelector('.bf-boundary-label');
      const box = label.getBoundingClientRect();
      return {kind: marker.dataset.kind, text: label.textContent,
              left: box.left, right: box.right, top: box.top, bottom: box.bottom};
    }),
  };
}
"""


def test_task_6_the_trellis_graph_marks_the_joins_to_periods_3_and_holds_no_root_container(
    browser, server_on, durables_folder
):
    """Task 6 (design pass 10 §6; N-D7, N-D13): the durables model's
    `declaration/spec.yml` open at periods 0 to 2, the graph JSON the region
    holds, read through its component's `collection()`, has no `Inputs` or
    `Outputs` of the trellis at its root in either direction; the wires the
    joins to `periods[3]` carry enter or leave at one `outside` node for
    each occurrence they reach, two in each graph, labeled with that
    occurrence, `periods[3]/keeper_cons` or `periods[3]/adjuster_cons`, the
    backward graph's each holding the value and the two marginal values of
    `tenure` (design pass 12 §2, where the backward graph held six); every
    node at the root is a boundary node, and every edge between two
    occurrences carries its route's record. The trellis still draws: the
    layout of each graph reports no problem, and places every boundary node
    as a box of its own, the region drawing two `outside` markers. At the
    opening, at 1600 × 1000, the label of the `start` or `end` marker
    beside the terminal period stands whole within the region, and no
    marker's label is cut by the region's edge (N-I277)."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        counts = {}
        # the trellis opens on the backward graph, so the forward graph is
        # chosen first, and each choice is laid out anew
        for direction in ("forward", "backward"):
            record_layouts(tab)
            choose_view(tab, None, direction)
            wait_until(
                lambda: tab.evaluate(VIEW_STATE_JS)["current"],
                60.0,
                f"the {direction} trellis graph laid out",
            )
            held = tab.evaluate(HELD_COLLECTION_JS)
            graph = graph_named(held, direction)
            roots = [node for node in graph["nodes"] if not node.get("namespace")]
            assert not [node["id"] for node in roots if node["id"].endswith(ROOT_CONTAINERS)]
            kinds = {attribute_of(node, "kind") for node in roots}
            assert kinds <= {"start", "end", "outside"} and "outside" in kinds, kinds
            outside = [node for node in roots if attribute_of(node, "kind") == "outside"]
            assert {attribute_of(node, "target") for node in outside} == PERIOD_3
            assert all(node["label"] == attribute_of(node, "target") for node in outside)
            # one node for each occurrence reached (design pass 12 §2), the
            # backward one holding tenure's value and two marginal values
            assert len(outside) == len(PERIOD_3), [node["id"] for node in outside]
            if direction == "backward":
                assert all(len(node["inputsMetadata"]) == 3 for node in outside), outside
            nodes = {node["id"]: node for node in graph["nodes"]}
            joins = [
                (occurrence_of(nodes[edge["sourceNodeId"]]), occurrence_of(node), edge_route(edge))
                for node in graph["nodes"]
                for edge in node.get("incomingEdges") or []
            ]
            between = [
                route for source, target, route in joins if source and target and source != target
            ]
            assert between
            assert all(
                (route is not None) == bool(source and target and source != target)
                for source, target, route in joins
            )
            opened = opened_namespaces(occurrences_of(held, direction))
            records = layout_records(tab, graph, opened)
            assert records["problems"] == []
            for node in roots:
                place = records["places"][node["id"]]
                assert all(math.isfinite(place[key]) for key in ("ax", "ay", "width", "height"))
            # the markers' labels at the opening (N-I277)
            wait_until(lambda: view_still(tab), 30.0, f"the {direction} graph at its opening")
            drawn = tab.evaluate(MARKER_LABELS_JS)
            region = drawn["region"]

            def within(box, region=region) -> bool:
                return (
                    region["left"] - 0.5 <= box["left"]
                    and box["right"] <= region["right"] + 0.5
                    and region["top"] - 0.5 <= box["top"]
                    and box["bottom"] <= region["bottom"] + 0.5
                )

            def beyond(box, region=region) -> bool:
                return box["right"] <= region["left"] + 0.5 or box["left"] >= region["right"] - 0.5

            ends = [box for box in drawn["labels"] if box["kind"] in ("start", "end")]
            assert ends and all(within(box) for box in ends), (direction, region, ends)
            assert all(within(box) or beyond(box) for box in drawn["labels"]), (
                direction,
                region,
                drawn["labels"],
            )
            # the region draws one `outside` marker for each occurrence reached
            drawn_outside = sorted(box["text"] for box in drawn["labels"] if box["kind"] == "outside")
            assert drawn_outside == sorted(PERIOD_3), (direction, drawn_outside)
            counts[direction] = (len(outside), len(roots), len(between))
        print(
            "task 6: on the durables trellis at periods 0–2, outside nodes, root nodes and "
            f"edges carrying a route by graph: {counts}"
        )
    finally:
        context.close()


# The cables the region draws (design pass 10 §6): each edge of the class
# `.bf-cable-edge`, with the widths of its outer and inner strokes as the
# browser computes them, whether its stub is dashed and whether it ends in
# an arrowhead; the cards' marks of the kind the pass removes; each boundary
# marker with the kind of its painted element, which has a name of its own,
# `.bf-marker-paint` (N-I276); and the count of markers whose child still
# takes the name `bf-mark` of a card's port mark and a cut name's mark.
CABLES_JS = r"""
() => ({
  cables: Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge.bf-cable-edge'), (edge) => {
    const outer = edge.querySelector('.bf-cable-outer'), inner = edge.querySelector('.bf-cable-inner');
    return {from: edge.dataset.from || null, to: edge.dataset.to || null,
            outer: outer ? getComputedStyle(outer).strokeWidth : null,
            inner: inner ? getComputedStyle(inner).strokeWidth : null,
            bundle: !!(outer && outer.classList.contains('bf-cable-bundle')),
            dashed: !!edge.querySelector('.bf-cable-dashed'),
            pair: edge.classList.contains('bf-join-pair'),
            arrow: !!edge.querySelector('.bf-cable-arrow')};
  }),
  marks: document.querySelectorAll('.bl-view-host .bf-card > .react-flow__handle.bf-mark').length,
  markers: Array.from(document.querySelectorAll('.bl-view-host .bf-marker'), (mark) => {
    const paint = mark.querySelector(':scope > .bf-marker-paint');
    return {
      kind: mark.dataset.kind, target: mark.dataset.target || null, label: mark.querySelector('.bf-boundary-label').textContent,
      hover: mark.getAttribute('title'), width: mark.getBoundingClientRect().width,
      paint: !paint ? null : paint.classList.contains('bf-outside-mark') ? 'outside'
        : paint.classList.contains('bf-boundary-mark') ? 'boundary' : 'unclassed'};
  }),
  shared: document.querySelectorAll('.bl-view-host .bf-marker > .bf-mark').length,
})
"""


def test_task_7_the_cable_is_one_connection_per_branch_and_moves_whole_through_its_list(
    browser, server_on, scratch_durables
):
    """Task 7 (design pass 10 §§6–8; the brief, § Wires, cables and
    connections; AMD-COMP-001 §3). On a copy of the durables model at
    periods 0 to 2, the forward trellis graph: (a) each card shows one port
    per continuation branch, two for `tenure` and one for every other
    stage, and one arrival port, each a press target of 10 px with a 6-px
    mark, and no per-field mark (design pass 13 §1, rules 1 and 3); (b) a cable's path
    is one stroke of 1.3 px, a wire's weight (design pass 12 §1), with no
    arrowhead, and a stub to an `outside` marker is dashed; (c) selecting the cable from `tenure` to
    `keeper_cons` in periods[1] lists in Details, first, the route with its
    branch, its status and its three wires in order with their sets and
    their origin; (d) dragging that cable's reading end onto
    `adjuster_cons`'s arrival port opens the cable's list beside that port,
    within the region, with one row per
    arrival field of `adjuster_cons` and the count line `0 of 2 fields
    paired`; the author's two choices make it `2 of 2 fields paired`, and
    `join` sends one event `moved` marked as the whole cable's, which is
    refused in one sentence under Problems, since the package would pair
    the unpaired `h_kp` with `keeper_cons` again and the branch would stand
    on two destinations, nothing written; the cable of the branch `adjust`
    dragged onto `keeper_cons` opens the list of its three arrival fields,
    `2 of 3 fields paired` after two choices, and `join` writes the one
    entry naming both pairs, the note names the draft, the editor shows the
    entry, the graph draws the cable from `tenure`'s branch `adjust` on
    `keeper_cons` and none on `adjuster_cons`, its route uncertified and
    reported under Problems, and one Mod-z restores both the text and the
    drawing; (e) at periods 0 to 2 an `outside` marker
    names `periods[3]/keeper_cons` with the hover `Outside periods 0–2`, and
    at periods 49 to 50 a boundary marker reads `starting data μ≺` at the
    first occurrence."""
    writer, reader, other = "periods[1]/tenure", "periods[1]/keeper_cons", "periods[1]/adjuster_cons"
    period_file = "declaration/period.yml"
    context, tab = new_tab(browser)
    try:
        url = server_on(scratch_durables)
        open_trellis(tab, url, RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        open_tree_file(tab, period_file)
        before = (scratch_durables / period_file).read_text(encoding="utf-8")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == before, 30.0, "the period file in the editor")
        choose_view(tab, None, "forward")
        # the forward graph drawn: tenure's two plugs carry its branches, which the backward graph's record of
        # the same pair of occurrences does not (design pass 12 §2), so the records alone would not tell the two
        # graphs apart while the forward layout runs
        wait_until(
            lambda: [
                p["branch"]
                for p in cable_ports(tab)
                if p["box"] == writer + LAYER_ID_ENDING and p["side"] == "writing" and not p["hidden"]
            ]
            == ["keep", "adjust"]
            and (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the join wires of the forward graph",
        )
        # (a) one port per branch and one arrival port on each card, no mark
        ports = [p for p in cable_ports(tab) if not p["hidden"]]
        by_card = {}
        for p in ports:
            by_card.setdefault(p["box"], {"writing": [], "reading": []})[p["side"]].append(p)
        for box, sides in by_card.items():
            key = box.split("/")[1].split("___")[0]
            assert len(sides["reading"]) == 1, (box, sides)
            assert [p["branch"] for p in sides["writing"]] == (["keep", "adjust"] if key == "tenure" else [""]), (box, sides)
        # every port is a press target of 10 px on the screen, the graph standing at a scale of 0.5 or more here,
        # and its mark a 6-px square at the view's scale (design pass 13 §1, rules 1 and 3)
        assert viewport(tab)["zoom"] >= 0.5, viewport(tab)
        assert all(abs(p["width"] - 10) <= 0.5 and abs(p["height"] - 10) <= 0.5 and abs(p["mark"] - 6) <= 0.01 for p in ports), ports
        drawn = tab.evaluate(CABLES_JS)
        assert drawn["marks"] == 0
        # (b) the cable's two strokes and its arrowhead; the outside stub dashed
        cables = [c for c in drawn["cables"] if c["from"] and c["to"]]
        # design pass 12 §1: one stroke at a wire's weight, 1.3 px, whatever the cable carries, and no inner stroke
        assert cables and all(c["outer"] == "1.3px" and c["inner"] is None for c in cables), cables
        # a cable runs from its plug into its socket and draws no arrowhead (design pass 11 §1a)
        assert all(not c["arrow"] for c in cables), cables
        stubs = [c for c in drawn["cables"] if c["dashed"]]
        assert stubs and all(not c["arrow"] for c in stubs), drawn["cables"]
        # (e) the outside markers of periods[3]
        outside = [m for m in drawn["markers"] if m["kind"] == "outside"]
        assert {m["target"] for m in outside} == {"periods[3]/keeper_cons", "periods[3]/adjuster_cons"}, outside
        assert all(m["label"] == m["target"] and m["hover"] == "Outside periods 0–2" for m in outside), outside
        # an outside marker draws the far card's port, a mark of 6 px (design pass 13 §1, rule 6)
        assert all(abs(m["width"] - 6 * viewport(tab)["zoom"]) <= 1 for m in outside), outside
        # each marker's painted element by its own name, the hollow square's
        # for an `outside` marker, and none named as a card's port mark (N-I276)
        assert all(m["paint"] == "outside" for m in outside), outside
        assert drawn["shared"] == 0
        # (c) Details of the selected cable
        click_join(tab, writer, reader)
        (head, rows), _ = wait_until(
            # a join's head in sentence case (Q3b, item 19; C12)
            lambda: tab.evaluate(DETAILS_ROWS_JS) if tab.evaluate(DETAILS_ROWS_JS)[0].startswith("Join") else None,
            10.0,
            "Details of the selected cable",
        )
        keys = [key for key, _ in rows]
        assert keys[:3] == ["route", "status", "wires"], keys
        found = dict(rows)
        assert found["route"] == [f"branch keep {writer} ≻ → {reader} ≺"], found["route"]
        assert found["status"] == ["certified"], found["status"]
        assert found["wires"] == [
            "w_kp → w_kp ℝ₊₊ · inferred",
            "h_kp → h_kp ℝ₊₊ · inferred",
            "z_kp → z_kp ℝ₊₊ · inferred",
        ], found["wires"]
        # (d) the cable's reading end dragged onto adjuster_cons opens the list
        reading = tab.evaluate(REGION_READING_JS)
        arrival = cable_port(tab, other, "reading")
        hold_events(tab, "moved")
        move_join_end(tab, writer, reader, "target", arrival)
        listed, _ = wait_until(lambda: cable_list(tab), 10.0, "the cable's list")
        options = ["—", "w_kp : ℝ₊₊", "h_kp : ℝ₊₊", "z_kp : ℝ₊₊"]
        assert listed == {
            "head": f"{writer} → {other}",
            "rows": [["w_adj : ℝ₊₊", False, "—", options], ["z_adj : ℝ₊₊", False, "—", options]],
            "count": "0 of 2 fields paired",
            "join": False,
        }, listed
        # the list stands beside the arrival port it was dropped on, within the region (design pass 10 §7)
        place = tab.evaluate(LIST_PLACE_JS, [PAIR_LIST, cable_port_selector(arrival), ".bf-region"])
        assert beside_port(place) and within(place["list"], place["region"]), place
        print(f"task 7: the cable's list at {place['list']} beside the port at {place['button']}")
        rows_drawn = tab.locator(".bl-view-host .bf-pair-row")
        selects = rows_drawn.locator("select.bf-pair-from")
        w_kp = selects.nth(0).locator("option", has_text="w_kp").get_attribute("value")
        selects.nth(0).select_option(value=w_kp)
        z_kp = selects.nth(1).locator("option", has_text="z_kp").get_attribute("value")
        selects.nth(1).select_option(value=z_kp)
        after = cable_list(tab)
        assert after["count"] == "2 of 2 fields paired" and after["join"], after
        # a continuation field chosen in one row is offered in no other
        assert after["rows"][0][3] == ["—", "w_kp : ℝ₊₊", "h_kp : ℝ₊₊"] and after["rows"][1][3] == ["—", "h_kp : ℝ₊₊", "z_kp : ℝ₊₊"], after
        tab.click(".bl-view-host .bf-pair-join")
        assert cable_list(tab) is None
        (event,) = held_events(tab, "moved")
        assert event["reading"] == reading and event["end"] == "reading" and event["cable"] is True
        assert [(p["sourceHandle"].rsplit(":", 1)[1], p["targetHandle"].rsplit(":", 1)[1], "replaced" in p) for p in event["pairs"]] == [
            ("w_kp", "w_adj", True), ("z_kp", "z_adj", True)
        ], event
        release_events(tab, "moved")
        # `h_kp`, which the list left unpaired, the package would pair with
        # `keeper_cons` again, so the branch would stand on two destinations:
        # the move is refused in one sentence under Problems and nothing is
        # written (AMD-COMP-001 §3.2)
        split = (
            "Nothing was written. The proposed source still selects tenure.h_kp → keeper_cons.h_kp, "
            "so the branch would stand on two destinations."
        )
        wait_until(lambda: any(line[0] == split for line in error_lines(tab)), 20.0, "the refusal of the split")
        assert tab.evaluate(DOCUMENT_JS) == before and unsaved_in_tree(tab) == []
        def routes_of(branch: str) -> dict:
            # the cables from `tenure`'s branch `branch` the region holds, by their ends, with their status
            return {
                (w["from"], w["to"]): w["status"]
                for w in flow_handle(tab, "joins") or []
                if w["from"] == writer and w["branch"] == branch
            }
        assert routes_of("keep") == {(writer, reader): "certified"}, routes_of("keep")
        # the cable of the branch `adjust`, two fields, moved whole onto
        # `keeper_cons`, three arrival fields: the list pairs two of the three
        # and `join` writes the one entry; `h_kp` left unpaired leaves the draft
        # the package reports under Problems, and the branch stands on one
        # destination (design pass 10 §7)
        arrival = cable_port(tab, reader, "reading")
        # the selection of the branch `keep`'s cable ends first, by Escape with the focus on it, as unit L's Task 30
        # ends a cable's selection: a selected cable's end circles, 16 px on the screen (K-I226), cover the
        # neighbouring cable's line at the pitch of 12 px (design pass 13 §1, rule 2)
        click_join(tab, writer, reader)
        wait_until(lambda: tab.evaluate(SELECTED_WIRE_FOCUSED_JS), 10.0, "the focus on the keep cable")
        tab.keyboard.press("Escape")
        wait_until(
            lambda: not [w for w in join_wires_drawn(tab) if w["selected"]], 10.0, "the selection of the keep cable ended"
        )
        click_join(tab, writer, other)
        wait_until(
            lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]] == [(writer, other)],
            10.0,
            "the cable of the branch adjust selected",
        )
        hold_events(tab, "moved")
        move_join_end(tab, writer, other, "target", arrival)
        listed, _ = wait_until(lambda: cable_list(tab), 10.0, "the cable's list")
        options = ["—", "w_adj : ℝ₊₊", "z_adj : ℝ₊₊"]
        assert listed == {
            "head": f"{writer} → {reader}",
            # the rows in the order of the region's records of the arrival ports
            "rows": [["h_kp : ℝ₊₊", False, "—", options], ["w_kp : ℝ₊₊", False, "—", options], ["z_kp : ℝ₊₊", False, "—", options]],
            "count": "0 of 3 fields paired",
            "join": False,
        }, listed
        selects = tab.locator(".bl-view-host .bf-pair-row").locator("select.bf-pair-from")
        selects.nth(1).select_option(value=selects.nth(1).locator("option", has_text="w_adj").get_attribute("value"))
        selects.nth(2).select_option(value=selects.nth(2).locator("option", has_text="z_adj").get_attribute("value"))
        after = cable_list(tab)
        assert after["count"] == "2 of 3 fields paired" and after["join"], after
        tab.click(".bl-view-host .bf-pair-join")
        assert cable_list(tab) is None
        (event,) = held_events(tab, "moved")
        assert event["reading"] == reading and event["end"] == "reading" and event["cable"] is True
        assert [(p["sourceHandle"].rsplit(":", 1)[1], p["targetHandle"].rsplit(":", 1)[1], "replaced" in p) for p in event["pairs"]] == [
            ("w_adj", "w_kp", True), ("z_adj", "z_kp", True)
        ], event
        release_events(tab, "moved")
        entry = "{w_adj: w_kp, z_adj: z_kp}"
        note, _ = wait_until(
            lambda: (gesture_note(tab) or "").startswith(f"period.yml, connectors: {entry} written, periods 1–50") and gesture_note(tab),
            20.0,
            "the note of the move",
        )
        assert "; draft: the route periods[1].tenure (branch adjust) → periods[1].keeper_cons is not certified" in note, note
        wait_until(lambda: entry in tab.evaluate(DOCUMENT_JS), 10.0, "the entry typed in the editor")
        assert open_path_shown(tab) == period_file
        # the graph redraws with the cable of the branch `adjust` on
        # `keeper_cons` and none on `adjuster_cons`, the route uncertified
        wait_until(
            lambda: (writer, reader) in routes_of("adjust") and (writer, other) not in routes_of("adjust"),
            60.0,
            "the cable drawn on keeper_cons and none on adjuster_cons",
        )
        assert routes_of("adjust") == {(writer, reader): "uncertified"}, routes_of("adjust")
        wait_until(
            lambda: any(
                line[0].startswith("the route periods[1].tenure (branch adjust) → periods[1].keeper_cons is not certified")
                for line in error_lines(tab)
            ),
            20.0,
            "the draft under Problems",
        )
        wait_until(lambda: unsaved_in_tree(tab) == [period_file], 10.0, "the period file unsaved")
        assert (scratch_durables / period_file).read_text(encoding="utf-8") == before
        # one undo restores the text and the drawing
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == before, 10.0, "the move undone in one step")
        wait_until(
            lambda: routes_of("adjust") == {(writer, other): "certified"},
            60.0,
            "the cable drawn on adjuster_cons again, certified, and none on keeper_cons",
        )
        # (e) the boundary marker where the starting data enter, at the first occurrence
        restrict(tab, "periods 49–50")
        wait_until(lambda: restriction_shown(tab) == "periods 49–50", 30.0, "the restriction to periods 49–50")
        wait_until(
            lambda: any(m["kind"] == "start" for m in tab.evaluate(CABLES_JS)["markers"]),
            60.0,
            "the start marker drawn",
        )
        starts = [m for m in tab.evaluate(CABLES_JS)["markers"] if m["kind"] == "start"]
        assert [m["label"] for m in starts] == ["starting data μ≺"], starts
        assert [m["paint"] for m in starts] == ["boundary"], starts
        print(
            f"task 7: {len(by_card)} cards with cable ports, {len(cables)} cables of two strokes, "
            f"{len(outside)} outside markers, the list's count line read, the whole cable moved and undone"
        )
    finally:
        context.close()


def test_task_7_backspace_on_a_cable_of_the_backward_graph_says_it_acts_in_the_forward_view(
    browser, server_on, scratch_durables
):
    """Task 7, fix round 3 (the re-review of round 1, Minor 5; N-D12,
    N-I192). On a copy of the durables model at periods 0 to 2, the
    backward trellis graph: with `keeper_cons`'s card in periods[0]
    selected, beside which the cable of the route from `tenure`'s branch
    `keep` stands whole (design pass 12 §2, where the selection drew it as
    its three wires), that cable, selected by a click, is named in Details
    by its route, and the focus the click gave it stands on it once its
    element is drawn after the others (N-I274);
    Backspace then removes nothing, and the list under the error mark says
    `Backspace acts in the forward trellis view`, as it says for an
    occurrence selected there (Task 5); no file changes on disk and none is
    left unsaved."""
    writer, reader = "periods[0]/tenure", "periods[0]/keeper_cons"
    card = f'.bl-view-host .react-flow__node[data-id="{reader}{LAYER_ID_ENDING}"]'
    before = file_bytes(scratch_durables)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_durables), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "backward")
        wait_until(lambda: tab.locator(card).count() == 1, 60.0, "keeper_cons's backward card")
        tab.click(f"{card} .bf-layer-name")
        wait_until(
            lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            30.0,
            "the cables from tenure to keeper_cons",
        )
        click_join(tab, writer, reader)
        wait_until(
            lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]]
            == [(writer, reader)],
            10.0,
            "the cable selected",
        )
        (head, rows), _ = wait_until(
            lambda: (found := tab.evaluate(DETAILS_ROWS_JS))[0].startswith("Join") and found,
            10.0,
            "Details of the selected cable",
        )
        assert dict(rows)["route"] == [f"branch keep {writer} ≻ → {reader} ≺"], (head, rows)
        # the focus the click gave the cable stands on it once its element is
        # drawn after the other wires, which moves it among them (N-I274), so
        # that Backspace reaches the region's handler
        wait_until(
            lambda: tab.evaluate(SELECTED_WIRE_FOCUSED_JS),
            10.0,
            "the focus on the selected cable",
        )
        tab.keyboard.press("Backspace")
        wait_until(
            lambda: BACKSPACE_FORWARD in [sentence for sentence, _, _ in error_lines(tab)],
            10.0,
            "the sentence of Backspace under the error mark",
        )
        assert gesture_note(tab) is None
        assert unsaved_in_tree(tab) == []
        assert file_bytes(scratch_durables) == before
        print(f"task 7: Backspace on the backward cable {writer} → {reader}: {BACKSPACE_FORWARD}")
    finally:
        context.close()


# --- Task 8: the two forms of a note in the page, with their formulas ---

# The three lines of `retiree_cons.bl` that Task 8's copy of the retirement
# model writes, as the acceptance notebook writes them: line 5 a bare note
# with an inline formula, line 7 a comment holding an annotation, line 11 a
# bracketed note with an entry and a displayed formula (AAS's brief,
# § Verification and handoff)
NOTE_FORMS = (
    ('β : (0,1)        :: ["discount factor"]', r'β : (0,1)        :: "discount factor \(β\)"'),
    (
        'R : ℝ₊₊          :: ["gross return on assets"]\n\n',
        'R : ℝ₊₊          :: ["gross return on assets"]\n# a comment :: ["not a note"]\n',
    ),
    (
        '[id=feasible, "empty at zero resources"]',
        r'[id=feasible, "empty at zero resources: \[Γ(0) = ∅\]"]',
    ),
)
# the number of displayed formulas in each preview the page shows
DISPLAYED_JS = """
() => Array.from(document.querySelectorAll('.cm-tooltip.bl-note'),
  (preview) => preview.querySelectorAll('.katex-display').length)
"""
# the box of the note glyph of the editor's line `n`, counted from one
GLYPH_BOX_JS = """
(n) => {
  const line = document.querySelectorAll('.cm-content .cm-line')[n - 1];
  const glyph = line.querySelector('.bl-note-marker');
  const box = glyph.getBoundingClientRect();
  return {x: box.x, y: box.y, width: box.width, height: box.height};
}
"""


def retirement_with_note_forms(target: Path) -> tuple[Path, str]:
    """A copy of the retirement model at `target` whose `retiree_cons.bl`
    holds NOTE_FORMS, made a git repository with one commit; answers the
    copy and the file's text."""
    shutil.copytree(RETIREMENT_CHOICE, target, ignore=shutil.ignore_patterns("__pycache__"))
    text = (target / RETIREE_CONS).read_text(encoding="utf-8")
    for old, new in NOTE_FORMS:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    (target / RETIREE_CONS).write_text(text, encoding="utf-8")
    return init_repository(target), text


def test_task_8_both_note_forms_typeset_their_formulas_and_an_edited_note_is_saved_and_undone(
    browser, server_on, tmp_path
):
    """Task 8 (AAS's brief, § Verification and handoff: "inline and display
    mathematics in both annotation forms, hover/focus, and reveal/edit/hide
    with save and undo"; design pass 10 §9), which no page test covered
    before the acceptance record. In a copy of the retirement model whose
    `retiree_cons.bl` writes line 5 as the bare note `"discount factor
    \\(β\\)"`, line 7 as a comment holding an annotation and line 11 as the
    bracketed note `[id=feasible, "empty at zero resources: \\[Γ(0) =
    ∅\\]"]`: lines 5 and 11 each draw one glyph `note`, line 11 keeping its
    entry `[id=feasible, ]`, and line 7 is drawn as written. The focus on
    line 5's glyph opens a preview with one formula, not displayed; the
    pointer on line 11's glyph opens a preview with one displayed formula,
    and so does the focus; none of this changes the document or the
    unsaved marks. A click on line 11's glyph draws the line as written;
    text typed there and the cursor moved off the line, the glyph is drawn
    again and the file is unsaved; Save writes the typed note to the file;
    one undo restores the text before the typing in the editor, which the
    tree then marks unsaved."""
    folder, text = retirement_with_note_forms(tmp_path / "retirement-choice")
    lines = text.split("\n")
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(folder), RETIREE_CONS)
        wait_until(
            lambda: tab.evaluate(LINE_GLYPHS_JS, 11) == [{"name": "note", "tabIndex": 0}],
            10.0,
            "the glyph of line 11",
        )
        assert tab.evaluate(LINE_GLYPHS_JS, 5) == [{"name": "note", "tabIndex": 0}]
        assert tab.evaluate(LINE_GLYPHS_JS, 7) == []
        assert line_text(tab, 5) == "β : (0,1)        :: "
        assert line_text(tab, 7) == lines[6]
        assert line_text(tab, 11).endswith(":: [id=feasible, ]"), line_text(tab, 11)
        before = tab.evaluate(UNCHANGED_JS)
        assert before == {"document": text, "unsaved": 0, "dirty": False}, before

        # the bare form: an inline formula
        glyphs = tab.locator(".cm-content .cm-line")
        glyphs.nth(4).locator(".bl-note-marker").focus()
        inline, _ = wait_until(
            lambda: tab.evaluate(NOTE_PREVIEWS_JS), 5.0, "the preview of line 5"
        )
        assert len(inline) == 1 and inline[0]["formulas"] == 1, inline
        assert inline[0]["text"].startswith("discount factor"), inline
        assert tab.evaluate(DISPLAYED_JS) == [0]
        tab.keyboard.press("Escape")
        wait_until(lambda: tab.evaluate(NOTE_PREVIEWS_JS) == [], 5.0, "the preview closed")

        # the bracketed form: a displayed formula, by the pointer and by
        # the focus
        glyph = glyphs.nth(10).locator(".bl-note-marker")
        for reach in (glyph.hover, glyph.focus):
            reach()
            shown, _ = wait_until(
                lambda: tab.evaluate(NOTE_PREVIEWS_JS), 5.0, "the preview of line 11"
            )
            assert len(shown) == 1 and shown[0]["formulas"] == 1, shown
            assert shown[0]["text"].startswith("empty at zero resources:"), shown
            assert tab.evaluate(DISPLAYED_JS) == [1]
            tab.mouse.move(2, 2)
            tab.keyboard.press("Escape")
            wait_until(lambda: tab.evaluate(NOTE_PREVIEWS_JS) == [], 5.0, "the preview closed")
        assert tab.evaluate(UNCHANGED_JS) == before

        # reveal, edit and hide; save; one undo
        glyph.click()
        wait_until(lambda: line_text(tab, 11) == lines[10], 5.0, "line 11 as written")
        tab.keyboard.type("Note: ")
        edited = text.replace('[id=feasible, "empty', '[id=feasible, "Note: empty')
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == edited, 5.0, "the typed text")
        # line 11, drawn as written, takes two rows: the cursor goes to line 1
        click_line(tab, 1)
        wait_until(lambda: tab.evaluate(LINE_GLYPHS_JS, 11) != [], 5.0, "the glyph again")
        wait_until(lambda: unsaved_in_tree(tab) == [RETIREE_CONS], 10.0, "the file unsaved")
        tab.click(".bl-save")
        wait_until(
            lambda: (folder / RETIREE_CONS).read_text(encoding="utf-8") == edited, 15.0, "the save"
        )
        wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "nothing unsaved")
        tab.locator(".cm-content").focus()
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 5.0, "one undo of the typing")
        wait_until(lambda: unsaved_in_tree(tab) == [RETIREE_CONS], 10.0, "unsaved again")
        print(f"task 8: line 5 {inline!r}; line 11 {shown!r}; saved and undone")
    finally:
        context.close()


def test_task_8_a_bare_note_s_glyph_has_the_glyph_s_box_and_the_pointer_on_it_opens_the_preview(
    browser, server_on, tmp_path
):
    """Task 8, the defect the acceptance record found (design pass 10 §9:
    the quoted explanation of a `:: "…"` entry is drawn as a 16-px glyph,
    and the pointer resting on it opens the preview). In the copy of the
    retirement model of the test above, the glyph of line 5, the bare note
    `"discount factor \\(β\\)"` at the end of its line, has the box of the
    bracketed glyph of line 6, 16 × 16 px, and the pointer at its center
    opens the preview `discount factor` with one formula. At the record's
    revision the glyph stands outside the annotation's mark as an item of the
    line's flex row (theme.js, `.cm-line.bl-annotated`), with a box of zero
    width, and the pointer there reaches the line."""
    folder, _ = retirement_with_note_forms(tmp_path / "retirement-choice")
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(folder), RETIREE_CONS)
        wait_until(
            lambda: tab.evaluate(LINE_GLYPHS_JS, 5) == [{"name": "note", "tabIndex": 0}],
            10.0,
            "the glyph of line 5",
        )
        bare, bracketed = (tab.evaluate(GLYPH_BOX_JS, n) for n in (5, 6))
        print(f"task 8: the glyph's box of line 5 {bare}, of line 6 {bracketed}")
        assert (round(bracketed["width"]), round(bracketed["height"])) == (16, 16), bracketed
        assert (round(bare["width"]), round(bare["height"])) == (16, 16), bare
        tab.mouse.move(bare["x"] + bare["width"] / 2, bare["y"] + bare["height"] / 2)
        shown, _ = wait_until(lambda: tab.evaluate(NOTE_PREVIEWS_JS), 5.0, "the preview of line 5")
        assert len(shown) == 1 and shown[0]["formulas"] == 1, shown
        assert shown[0]["text"].startswith("discount factor"), shown
    finally:
        context.close()


def test_task_7_backspace_in_a_forward_graph_no_gesture_can_extend_sends_nothing(
    browser, server_on, scratch_durables
):
    """N-I273 (the fix wave). On a copy of the durables model whose recipe
    names its trellis file by the path `./trellis.yml`, which `add stage`
    and `add period` cannot extend (`creation.can_add`), the forward
    trellis graph lays out no `+ period` and takes no drop. Backspace on
    the selected card of `keeper_cons` in periods[0], and on the selected
    cable from `tenure`'s branch `keep` to it, a join by equal names that no
    entry writes, sends no event `removed`, as before unit N, where it sent
    each with no reading and the page answered in the forward view with a
    sentence that names the backward one or the reading; no file changes."""
    writer, reader = "periods[0]/tenure", "periods[0]/keeper_cons"
    occurrence = f"{reader}{LAYER_ID_ENDING}"
    card = f'.bl-view-host .react-flow__node[data-id="{occurrence}"]'
    recipe = scratch_durables / RECIPE_FILE
    text = recipe.read_text(encoding="utf-8")
    assert text.count("\ntrellis: trellis.yml\n") == 1
    recipe.write_text(
        text.replace("\ntrellis: trellis.yml\n", "\ntrellis: ./trellis.yml\n"), encoding="utf-8"
    )
    before = file_bytes(scratch_durables)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_durables), RECIPE_FILE)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the cables of the forward graph",
        )
        # the forward graph that no gesture can extend: no `+ period` laid out
        assert tab.locator(".bl-view-host .bf-add-period").count() == 0
        hold_events(tab, "removed")

        # Backspace on the selected card
        tab.click(f"{card} .bf-layer-name")
        wait_until(
            lambda: flow_handle(tab, "selection") == occurrence, 10.0, "keeper_cons selected"
        )
        tab.keyboard.press("Backspace")
        assert held_events(tab, "removed") == []

        # Backspace on the selected cable, the focus the click gave it
        click_join(tab, writer, reader)
        wait_until(
            lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]]
            == [(writer, reader)],
            10.0,
            "the cable selected",
        )
        wait_until(
            lambda: tab.evaluate(SELECTED_WIRE_FOCUSED_JS),
            10.0,
            "the focus on the selected cable",
        )
        tab.keyboard.press("Backspace")
        assert held_events(tab, "removed") == []
        assert gesture_note(tab) is None
        assert unsaved_in_tree(tab) == []
        assert file_bytes(scratch_durables) == before
        print(
            "task 7: Backspace in the forward graph no gesture can extend sent nothing "
            f"on {occurrence} and on its cable from {writer}"
        )
    finally:
        context.close()
