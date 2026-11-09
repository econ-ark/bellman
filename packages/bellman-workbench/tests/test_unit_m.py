"""The acceptance tests of unit M of model interface specification 0.4, the
Workbench after unit L (the plan "Unit M of model interface spec 0.4, the
Workbench after unit L: implementation plan"): one test for each task's
acceptance check, each reading the page's elements, never a screenshot's
pixels. Deleted when the next amendment is accepted (lean implementation
rule, layer 2).
"""

from __future__ import annotations

import re

from workbench_support import (
    CONTRAST_EXCEPTIONS,
    DOCUMENT_JS,
    DRAWN_PLACES_JS,
    DURABLES_STATUS_REST,
    HELD_COLLECTION_JS,
    KEEPER_CONS,
    MATSYA_TOGGLE,
    RECIPE_FILE,
    ROOT,
    VIEW_STATE_JS,
    VIEWPORT,
    attribute_of,
    choose_option,
    choose_view,
    click_line,
    contrast_faults,
    gesture_note,
    graph_named,
    lay_out_left_to_right,
    new_tab,
    open_file,
    open_recipe_row,
    open_trellis,
    recipe_head,
    recipe_rows_at_rest,
    record_layouts,
    select_until,
    show_status,
    status_text,
    viewport,
    wait_until,
    with_each_recipe_row_open,
)

from bellman.stage import LAYER_ID_ENDING

# a measure's label followed by its coordinates, `μ≺(`, `μ_keep≻(`, `μ(`:
# the letter, the field as a subscript where one stands, the perch mark
# where one stands, and an opening parenthesis (AAS, M-D1)
MEASURE_AT_COORDINATES = re.compile(r"μ(?:_[^\s(]+)?[≺∼≻]?\(")

# Every text the region draws, one text node at a time, and every hover and
# accessible name of its elements, `title`, `aria-label` and
# `aria-description`, so that no two texts are read as one.
REGION_TEXTS_JS = """
() => {
  const host = document.querySelector('.bl-view-host');
  const texts = [];
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) texts.push(walker.currentNode.textContent);
  for (const element of host.querySelectorAll('[title], [aria-label], [aria-description]')) {
    for (const name of ['title', 'aria-label', 'aria-description']) {
      if (element.hasAttribute(name)) texts.push(element.getAttribute(name));
    }
  }
  return texts.filter((text) => text.trim() !== '');
}
"""


def graph_labels(graph: dict) -> list[str]:
    """Every label of the graph `graph` of the graph JSON: each node's label,
    and the attributes `label` and `__tensor_tag` of each of its ports
    (spec 0.4 §4)."""
    labels = []
    for node in graph["nodes"]:
        labels.append(node.get("label", ""))
        for port in (node.get("inputsMetadata") or []) + (node.get("outputsMetadata") or []):
            labels += [attribute_of(port, "label"), attribute_of(port, "__tensor_tag")]
    return [label for label in labels if label]


def measure_ports(graph: dict, namespace: str = "") -> set[str]:
    """The labels of the ports of the graph `graph` whose id names a
    measure, `keeper_cons:measure:arvl`, on the nodes whose namespace starts
    with `namespace`."""
    return {
        attribute_of(port, "label")
        for node in graph["nodes"]
        if (node.get("namespace") or "").startswith(namespace)
        for port in (node.get("inputsMetadata") or []) + (node.get("outputsMetadata") or [])
        if ":measure:" in port["id"]
    }


def test_task_1_a_measure_is_labeled_by_its_perch_alone_on_the_two_forward_graphs(
    browser, server_on, durables_folder
):
    """Task 1 (AAS, M-D1): with the durables model's `keeper_cons.bl` open,
    the stage's forward graph, drawn in the region, labels the measures of
    its three perches `μ≺`, `μ` and `μ≻`, with no coordinates, and no label
    of the graph JSON, no text the region draws and no hover holds `μ`
    followed by an opening parenthesis; the backward graph's functions keep
    their coordinates, `𝑉≻(a_nxt_kp, h_nxt_kp, z_nxt_kp)`. The recipe
    `declaration/spec.yml` open, the forward trellis graph labels the arrival
    and the continuation measure of `periods[0]/keeper_cons` `μ≺` and `μ≻`,
    and again no label, drawn text or hover holds `μ` followed by an opening
    parenthesis."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_file(tab, url, KEEPER_CONS)
        record_layouts(tab)
        choose_view(tab, "operator", "forward")
        wait_until(
            lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "keeper_cons's forward graph"
        )
        held = tab.evaluate(HELD_COLLECTION_JS)
        forward = graph_named(held, "forward")
        assert measure_ports(forward) == {"μ≺", "μ", "μ≻"}
        stage_texts = graph_labels(forward) + tab.evaluate(REGION_TEXTS_JS)
        assert [text for text in stage_texts if MEASURE_AT_COORDINATES.search(text)] == []
        backward = graph_labels(graph_named(held, "backward"))
        assert "𝑉≻(a_nxt_kp, h_nxt_kp, z_nxt_kp)" in backward

        open_trellis(tab, url, RECIPE_FILE)
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward trellis")
        trellis_forward = graph_named(tab.evaluate(HELD_COLLECTION_JS), "forward")
        keeper = measure_ports(trellis_forward, "periods[0]/keeper_cons")
        assert {"μ≺", "μ≻"} <= keeper, keeper
        trellis_texts = graph_labels(trellis_forward) + tab.evaluate(REGION_TEXTS_JS)
        assert [text for text in trellis_texts if MEASURE_AT_COORDINATES.search(text)] == []
        print(
            f"task 1: {len(stage_texts)} texts of the stage's forward graph and "
            f"{len(trellis_texts)} of the forward trellis read; keeper_cons's measures "
            f"{sorted(keeper)}"
        )
    finally:
        context.close()


# the measures of the button `remove stage` the page draws, read from its
# computed style and its box: its element, each side's border, each
# corner's radius, its height, the size of its words and its hover; and,
# for an icon button of VSCode Elements, its Codicon, its accessible name
# and its width
REMOVE_STAGE_JS = """
(selector) => {
  const button = document.querySelector(selector);
  if (!button) return null;
  const style = getComputedStyle(button);
  const sides = ['Top', 'Right', 'Bottom', 'Left'];
  const corners = ['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'];
  return {
    tag: button.tagName,
    borders: sides.map((side) => [style[`border${side}Width`], style[`border${side}Style`]]),
    color: style.borderTopColor,
    radii: corners.map((corner) => style[`border${corner}Radius`]),
    height: button.getBoundingClientRect().height,
    width: button.getBoundingClientRect().width,
    size: style.fontSize,
    title: button.getAttribute('title'),
    text: button.textContent.trim(),
    icon: button.getAttribute('icon'),
    label: button.label === undefined ? null : button.label,
  };
}
"""


def test_task_2_remove_stage_is_drawn_as_a_control_and_a_click_removes_the_stage_s_row(
    browser, server_on, scratch_durables
):
    """Task 2 (AAS, M-D2; design pass 4 §2), as Tasks 6, 7 and 10 of unit M
    draw the recipe and Details in the system of design pass 8 (§§3, 5.3
    and 6; design pass 9 §3): on a copy of the durables model with its
    recipe `declaration/spec.yml` open, the row of `bequest` in the Recipe
    tab draws `Remove stage` as the icon button of VSCode Elements, the Codicon
    `trash` in a target of 24 × 24 px, named `Remove stage`, whose hover
    names the stage and this recipe (unit N, Task 2; design pass 10 §4);
    Details of `periods[0]/bequest`, selected in the forward trellis graph,
    draws it, since unit N's Task 5 (design pass 10 §7), as a destructive
    act, a text button of 26 px with the Codicon `trash` before its words,
    after Details' rows (design pass 13 §5; Q-D15), whose hover names the
    scope of the removal. A click on the row's button takes
    `bequest`'s row out of the recipe's text in the editor, and the status
    line's note names the row removed (unit L, Task 25)."""
    block_button = '.bl-recipe-row[data-stage="bequest"] .bl-remove-stage'
    details_button = ".bl-removal-buttons .bl-remove-stage"
    recipe_text = (scratch_durables / RECIPE_FILE).read_text(encoding="utf-8")
    rows = [line for line in recipe_text.splitlines(True) if line.startswith("  bequest:")]
    assert len(rows) == 1
    no_bequest = recipe_text.replace(rows[0], "")
    icon_button = {
        "tag": "VSCODE-TOOLBAR-BUTTON",
        "height": 24,
        "width": 24,
        "title": "Remove bequest from this recipe",
        "icon": "trash",
        "label": "Remove stage",
    }
    control = {
        "tag": "BUTTON",
        "height": 26,
        "title": (
            "Removes bequest from spec.yml and every period; its files are deleted on save "
            "unless another recipe names them"
        ),
        "text": "Remove stage",
    }
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_durables), RECIPE_FILE)
        drawn = tab.evaluate(REMOVE_STAGE_JS, block_button)
        assert drawn is not None, "the block's button"
        assert {key: drawn[key] for key in icon_button} == icon_button, drawn

        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward trellis")
        select_until(
            tab,
            f"periods[0]/bequest{LAYER_ID_ENDING}",
            "forward",
            lambda: tab.locator(details_button).count() == 1,
            "Details of periods[0]/bequest",
            60.0,
        )
        in_details = tab.evaluate(REMOVE_STAGE_JS, details_button)
        # a text button, with no fill, the Codicon `trash` before its words
        classes = tab.get_attribute(details_button, "class").split()
        assert "bl-text-button" in classes
        assert tab.get_attribute(details_button, "secondary") is None
        assert tab.locator(f"{details_button} > .codicon.codicon-trash").count() == 1
        assert {key: in_details[key] for key in control} == control, in_details

        tab.click(block_button)
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == no_bequest, 30.0, "bequest's row out")
        wait_until(
            lambda: (gesture_note(tab) or "").startswith("spec.yml, stages: bequest removed;"),
            30.0,
            "the note of the removal",
        )
        print(f"task 2: the block's button {drawn}; Details' button {in_details}")
    finally:
        context.close()


# The class of the folder column's head `Files`, a bar of 36 px level with
# the tabs' row and the graph bar since design pass 13 §4 (D1), where the
# other heads are 28 px
FILES_BAR = "bl-folder-rail"
# The regions Task 4 builds (design pass 8 §6), its rail and title bar
# joined in the main bar by unit N's Task 1 (design pass 10 §§2 and 3): the
# main bar and the status line.
TASK_4_REGIONS = ".bl-main-bar, .bl-status"
# The regions the other tasks build, whose texts measure 8 leaves to them.
OTHER_REGIONS = (".bl-folder", ".bl-file", ".bl-view", ".bl-matsya", ".bl-goto", ".bl-forms")
# The text styles of design pass 8 §5.1, each as its face, its size in
# pixels and its weight (§7, measure 1), with Code name, which design pass
# 13 §3 adds to the Code step for an identifier that heads its row, card or
# selection (C1): the styles of the type steps outside the editor's source,
# whose stage name is Title, and the graph's drawing, whose smallest text
# is Mark.
FIVE_STYLES = {
    ("Archivo", 13.0, 600),
    ("Archivo", 13.0, 400),
    ("Archivo", 11.0, 500),
    ("IBM Plex Mono", 12.5, 400),
    ("IBM Plex Mono", 12.5, 500),
    ("IBM Plex Mono", 11.0, 400),
}
# The color roles of design pass 8 §5.4, each a custom property of
# brand.css, the mint of the constructed mark and the red Problems error mark;
# the selection's wash among them, the ground of a pressed toggle of the
# main bar (design pass 10 §3).
COLOR_ROLES = (
    "--bl-ground",
    "--bl-raised",
    "--bl-sunken",
    "--bl-raised-2",
    "--bl-ink-1",
    "--bl-ink-2",
    "--bl-ink-3",
    "--bl-hairline",
    "--bl-control-border",
    "--bl-hover",
    "--bl-press",
    "--bl-selected",
    "--bl-accent",
    "--bl-accent-fill",
    "--bl-alarm",
    "--bl-error",
    "--bl-mint",
)
# The texts no visible text node of the page may be, since a Codicon draws
# each (design pass 8 §7, measure 4).
GLYPH_TEXTS = {"▸", "▾", "×", "+", "!"}
PUBLIC = ROOT / "packages/bellman-workbench/bellman_workbench/public"
# The icon of each toggle of the main bar by its fold (AAS, M-D18; Task 11;
# design pass 10 §3; N-D10): the Codicon drawn at 16 px, None where the icon
# has none, and the glyph the browser typesets in the page's fonts, None
# where it has none. Files is the Codicon `files`; Inspector the Codicon
# `layout-panel`; Details the denotation brackets ⟦·⟧ alone; Matsya Υ in the
# speech bubble `comment`.
TOGGLE_ICONS = {
    "folder": ["files", None],
    "inspector": ["layout-panel", None],
    "details": [None, "⟦·⟧"],
    "matsya": ["comment", "Υ"],
}

# The libraries the page loads (design pass 8 §§3 and 4): the elements that
# load the Codicons stylesheet and VSCode Elements' module, each by its URL,
# with the origin of the page, whether the module's toolbar button is
# defined within ten seconds and the font faces of Codicons that load.
LIBRARIES_JS = """
async () => {
  const sheets = Array.from(document.querySelectorAll('link#vscode-codicon-stylesheet'),
    (link) => link.href);
  const modules = Array.from(document.querySelectorAll('script[src*="vscode-elements"]'),
    (script) => [script.src, script.type]);
  const defined = await Promise.race([
    customElements.whenDefined('vscode-toolbar-button').then(() => true),
    new Promise((resolve) => setTimeout(() => resolve(false), 10000)),
  ]);
  const faces = await document.fonts.load('16px codicon', '\\uea87');
  return {origin: location.origin, sheets, modules, defined, faces: faces.length};
}
"""

# The measures of design pass 8 §7 read on the regions: every drawn text
# node with its face, size, weight, letter-spacing and case and whether an
# element of the file's words (`.bl-code`, `.bl-code-name`, `.bl-code-small`)
# holds it; the boxes of the main bar and of the status line; the main bar's
# mark, its toggles and their icons, each as its box, its Codicon's name and
# its glyph (Task 11; design pass 10 §3); every SVG; every Codicon, drawn in
# the page or in a VSCode Elements toolbar button, with its size and face,
# and whether the button stands in the main bar; the colors of every drawn
# element against the color roles; the contrast of the state marks that are
# no text; and the box of every target.
TASK_4_JS = r"""
([regionsSelector, roles]) => {
  const regions = Array.from(document.querySelectorAll(regionsSelector));
  const box = (element) => {
    const rect = element.getBoundingClientRect();
    return {left: rect.left, top: rect.top, width: rect.width, height: rect.height};
  };
  const drawn = (element) => element.getClientRects().length > 0
    && getComputedStyle(element).visibility === 'visible';
  const inRegions = (selector) => regions.flatMap((region) =>
    Array.from(region.querySelectorAll(selector))).filter(drawn);
  const texts = [];
  for (const region of regions) {
    const walker = document.createTreeWalker(region, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      if (!Array.from(range.getClientRects()).some((r) => r.width > 0 && r.height > 0)) continue;
      const style = getComputedStyle(node.parentElement);
      texts.push({
        text: node.textContent.trim().slice(0, 40),
        region: region.classList[0],
        style: [style.fontFamily.split(',')[0].replace(/"/g, '').trim(),
                parseFloat(style.fontSize), Number(style.fontWeight)],
        spacing: style.letterSpacing,
        transform: style.textTransform,
        code: node.parentElement.closest('.bl-code, .bl-code-name, .bl-code-small') !== null,
      });
    }
  }
  const bar = document.querySelector('.bl-main-bar');
  const mark = bar.querySelector('.bl-mark img');
  const buttons = Array.from(bar.querySelectorAll('.bl-toggle'), (button) => {
    const icon = button.querySelector('.bl-toggle-icon');
    const codicon = icon.querySelector(':scope > .codicon');
    const glyph = icon.querySelector(':scope > .bl-toggle-glyph');
    return {
      fold: button.dataset.fold, box: box(button), icon: box(icon),
      parts: [codicon ? Array.from(codicon.classList).find((name) => name.startsWith('codicon-'))
                        .slice('codicon-'.length) : null,
              glyph ? glyph.dataset.glyph : null],
    };
  });
  const otherSvgs = inRegions('svg').map((svg) => svg.outerHTML.slice(0, 80));
  const toolbar = inRegions('vscode-toolbar-button').map((host) => {
    return {icon: host.getAttribute('icon'), box: box(host),
            inBar: host.closest('.bl-main-bar') !== null};
  });
  const probe = document.createElement('span');
  document.body.append(probe);
  const allowed = new Set(['rgba(0, 0, 0, 0)']);
  for (const role of roles) {
    probe.style.color = `var(${role})`;
    allowed.add(getComputedStyle(probe).color);
  }
  probe.remove();
  const colors = [];
  const record = (element, property, value) => {
    if (!allowed.has(value)) {
      const name = `${element.tagName.toLowerCase()}.${element.getAttribute('class')}`;
      colors.push(`${name} ${property} ${value}`);
    }
  };
  for (const element of inRegions('*')) {
    const style = getComputedStyle(element);
    record(element, 'background', style.backgroundColor);
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) {
      if (parseFloat(style[`border${side}Width`]) > 0 && style[`border${side}Style`] !== 'none') {
        record(element, `border-${side.toLowerCase()}`, style[`border${side}Color`]);
      }
    }
    const lettered = Array.from(element.childNodes).some(
      (node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
    if (lettered || element.matches('svg, .codicon, .bl-toggle-glyph')) {
      record(element, 'color', style.color);
    }
    const before = getComputedStyle(element, '::before');
    if (before.content !== 'none' && before.content !== 'normal') {
      record(element, '::before background', before.backgroundColor);
    }
  }
  const parse = (text) => {
    let match = /^rgba?\((.*)\)$/.exec(text);
    if (match) {
      const parts = match[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
      return [parts[0], parts[1], parts[2], parts.length > 3 ? parts[3] : 1];
    }
    match = /^color\(srgb (.*)\)$/.exec(text);
    const parts = match[1].split(/[\s\/]+/).filter(Boolean).map(Number);
    return [parts[0] * 255, parts[1] * 255, parts[2] * 255, parts.length > 3 ? parts[3] : 1];
  };
  const luminance = (color) => color.slice(0, 3).reduce((sum, value, i) => {
    const channel = value / 255;
    const linear = channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    return sum + linear * [0.2126, 0.7152, 0.0722][i];
  }, 0);
  const ratio = (a, b) => {
    const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (high + 0.05) / (low + 0.05);
  };
  const ground = parse(getComputedStyle(bar).backgroundColor);
  const marks = [];
  for (const button of bar.querySelectorAll('.bl-toggle')) {
    marks.push([`${button.dataset.fold} icon`,
                ratio(parse(getComputedStyle(button.querySelector('.bl-toggle-icon')).color),
                      ground)]);
    const line = getComputedStyle(button, '::after');
    if (line.content !== 'none' && parse(line.backgroundColor)[3] > 0) {
      marks.push([`${button.dataset.fold} line`, ratio(parse(line.backgroundColor), ground)]);
    }
  }
  const targets = inRegions('button, a[href], [role="button"], [tabindex]:not([tabindex="-1"]),'
                            + ' [data-link], vscode-toolbar-button')
    .filter((element) => !element.parentElement.closest('vscode-toolbar-button, button, a[href]'))
    .map((element) => [`${element.tagName.toLowerCase()}.${element.getAttribute('class')}`,
                       box(element)]);
  return {
    texts, colors, marks, targets, toolbar, otherSvgs, buttons,
    mark: {box: box(mark), src: mark.getAttribute('src')},
    title: box(bar),
    status: box(document.querySelector('.bl-status')),
    window: window.innerHeight,
  };
}
"""


# The trellis's rest where the details' line holds it (design pass 8 §6):
# its text, and each part it draws, in the line's order, as its text and the
# left and right edges of its box; null while the details' line draws no
# rest.
DETAILS_REST_JS = """
() => {
  const rest = document.querySelector('.bl-status-line .bl-trellis-rest');
  if (rest === null || rest.getClientRects().length === 0) return null;
  const parts = Array.from(rest.children)
    .filter((part) => part.getClientRects().length > 0)
    .map((part) => {
      const box = part.getBoundingClientRect();
      return {text: part.textContent, left: box.left, right: box.right};
    });
  return {text: rest.textContent, parts};
}
"""


# Every drawn Codicon among the elements given, each as its name, its size
# and face, whether its glyph is drawn and whether a VSCode Elements control
# draws it in its own tree, which Playwright's selectors reach (design pass
# 8 §§3 and 4; §7, measure 4).
CODICONS_JS = """
(elements) => elements.filter((element) => element.getClientRects().length > 0).map((element) => {
  const before = getComputedStyle(element, '::before');
  return {name: Array.from(element.classList).find((name) => name.startsWith('codicon-')),
          size: parseFloat(getComputedStyle(element).fontSize),
          face: getComputedStyle(element).fontFamily,
          drawn: before.content !== 'none' && before.content !== '""',
          library: element.getRootNode() !== document};
})
"""


def drawn_codicons(tab, regions: str) -> tuple[list[dict], list[dict]]:
    """The Codicons of the regions `regions`, a list of selectors parted by
    commas (CODICONS_JS), the main bar's toggles' among them, which stand at
    16 px as every other (design pass 10 §3; N-D10): those the page draws
    in its own elements, and those VSCode Elements' controls draw in their
    own trees."""
    named = ", ".join(f"{region.strip()} .codicon" for region in regions.split(","))
    found = tab.locator(named).evaluate_all(CODICONS_JS)
    return (
        [glyph for glyph in found if not glyph["library"]],
        [glyph for glyph in found if glyph["library"]],
    )


def task_4_measures(tab) -> tuple[dict, dict, list[str]]:
    """The libraries the page loaded, the measures of the regions
    (TASK_4_JS) with their Codicons (`drawn_codicons`) and the texts of the
    regions under their contrast bound (spec 0.4 §5.8), read with the
    pointer over the graph's canvas, so that no hover stands in the
    regions."""
    tab.mouse.move(1200, 500)
    libraries = tab.evaluate(LIBRARIES_JS)
    measured = tab.evaluate(TASK_4_JS, [TASK_4_REGIONS, list(COLOR_ROLES)])
    measured["codicons"], measured["glyphs"] = drawn_codicons(tab, TASK_4_REGIONS)
    faults = contrast_faults(tab, [*CONTRAST_EXCEPTIONS, *OTHER_REGIONS])
    return libraries, measured, faults


def test_task_4_the_main_bar_and_the_status_line_stand_in_the_system_of_design_pass_8(
    browser, server_on, durables_folder
):
    """Task 4 (AAS, M-D4, M-D6, M-D11, M-D12; design pass 8 §§3 to 7), its
    rail and title bar joined in the main bar by unit N's Task 1 (design
    pass 10 §§2 and 3): on the durables model at 1600 × 1000, in the
    trellis view of `declaration/spec.yml` and in `keeper_cons.bl`'s view,
    the page loads Codicons' stylesheet and VSCode Elements' module once
    each, from its own files; and the main bar and the status line meet the
    measures of §7. Measure 1: every drawn text computes one of the five
    styles, with no letter-spacing and no change of case, the mono face only
    within the elements of the file's words, the path's among them. Measure
    2: the main bar is 36 px high at the window's top, the status line 24 px
    at its foot. Measure 4: the main bar draws the brand's mark, the
    silhouette, 20 px high and its four toggles, each its Codicon and glyph
    of Task 11 (AAS, M-D18; N-D10) at 16 px in a button of 26 × 26, and its
    icon buttons Back, Forward and Go to 26 × 26; every icon of the two
    regions is a Codicon at 16 px and none is an SVG; the status line's icon
    button is 24 × 24; no drawn text is `▸`, `▾`, `×`, `+` or `!`. Measure
    7: every color drawn is a role of §5.4. Measure 8: every text meets its
    contrast bound, the toggles' icons and their lines meet 3:1, and every
    target is at least 24 × 24. Where the trellis's rest
    stands in the details' line, with Matsya opened at 1200 × 800 (unit K,
    Task 6), its parts stand 16 px apart, as in the visible line, each
    separator kept in the rest's text and not drawn (§6)."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        views = {}
        open_trellis(tab, url, RECIPE_FILE)
        views["trellis"] = task_4_measures(tab)
        # the trellis's rest in the details' line: Matsya opened by the
        # main bar's toggle in a window of 1200 × 800, where the whole line
        # does not fit the visible line (unit K, Task 6), and the details
        # shown
        tab.click(MATSYA_TOGGLE)
        tab.set_viewport_size({"width": 1200, "height": 800})
        show_status(tab)
        rest, _ = wait_until(
            lambda: tab.evaluate(DETAILS_REST_JS), 10.0, "the trellis's rest in the details' line"
        )
        tab.set_viewport_size(VIEWPORT)
        open_file(tab, url, KEEPER_CONS)
        views["keeper_cons"] = task_4_measures(tab)
    finally:
        context.close()

    # the trellis's rest in the details' line, its parts 16 px apart
    parts = rest["parts"]
    assert rest["text"].endswith(DURABLES_STATUS_REST), rest
    assert len(parts) >= 2 and all(" · " not in part["text"] for part in parts), rest
    gaps = [after["left"] - before["right"] for before, after in zip(parts, parts[1:])]
    assert all(abs(gap - 16) <= 0.5 for gap in gaps), (gaps, rest)

    for view, (libraries, measured, faults) in views.items():
        # the libraries, loaded once from the page's own files
        origin = libraries["origin"]
        assert libraries["sheets"] == [f"{origin}/static/assets/codicons/codicon.css"], view
        assert libraries["modules"] == [
            [f"{origin}/static/assets/vscode-elements/bundled.js", "module"]
        ], view
        assert libraries["defined"] and libraries["faces"] >= 1, (view, libraries)

        # measure 1: the five styles
        texts = measured["texts"]
        assert {text["region"] for text in texts} == {"bl-main-bar", "bl-status"}
        for text in texts:
            assert tuple(text["style"]) in FIVE_STYLES, (view, text)
            assert (text["spacing"], text["transform"]) == ("normal", "none"), (view, text)
            if text["style"][0] == "IBM Plex Mono":
                assert text["code"], (view, text)
            assert text["text"] not in GLYPH_TEXTS, (view, text)

        # measure 2: the main bar and the status line
        title, status = measured["title"], measured["status"]
        assert abs(title["top"]) <= 0.5 and abs(title["height"] - 36) <= 0.5, (view, title)
        assert abs(status["height"] - 24) <= 0.5, (view, status)
        assert abs(status["top"] + status["height"] - measured["window"]) <= 0.5, (view, status)

        # measure 4: the mark, the main bar's four toggles, and Codicons
        mark = measured["mark"]
        assert mark["src"].endswith("/static/assets/brand/favicon.svg")
        assert abs(mark["box"]["height"] - 20) <= 0.5, (view, mark)
        buttons = measured["buttons"]
        assert [button["fold"] for button in buttons] == list(TOGGLE_ICONS)
        for button in buttons:
            assert (button["box"]["width"], button["box"]["height"]) == (26, 26), (view, button)
            assert (button["icon"]["width"], button["icon"]["height"]) == (16, 16), (view, button)
            assert button["parts"] == TOGGLE_ICONS[button["fold"]], (view, button)
        assert measured["otherSvgs"] == [], view
        assert len(measured["glyphs"]) == len(measured["toolbar"]), view
        codicons = measured["codicons"] + measured["glyphs"]
        assert codicons, view
        for glyph in codicons:
            assert glyph["drawn"], (view, glyph)
            # the `add` glyph beside a word, `Stage` or `Period`, drawn as a bare Codicon, is 12 px on the word's
            # cap height since design pass 14 §8 (S-D15); every other Codicon keeps 16, the library's icon
            # button `add` of the Fields tab among them
            expected = 12 if glyph["name"] == "codicon-add" and not glyph["library"] else 16
            assert glyph["size"] == expected and glyph["face"] == "codicon", (view, glyph)
        for host in measured["toolbar"]:
            side = 26 if host["inBar"] else 24
            assert (host["box"]["width"], host["box"]["height"]) == (side, side), (view, host)

        # measure 7: the colors
        assert measured["colors"] == [], view

        # measure 8: contrast and targets
        assert faults == [], view
        assert [mark for mark in measured["marks"] if mark[1] < 3] == [], view
        small = [
            target
            for target in measured["targets"]
            if target[1]["width"] < 23.5 or target[1]["height"] < 23.5
        ]
        assert small == [], view
    print(
        "task 4: "
        + "; ".join(
            f"{view}: {len(measured['texts'])} texts, {len(measured['codicons'])} Codicons, "
            f"{len(measured['toolbar'])} toolbar buttons, {len(measured['targets'])} targets, "
            f"the main bar {measured['title']['height']} px, the status line "
            f"{measured['status']['height']} px"
            for view, (_, measured, _) in views.items()
        )
        + f"; the details' rest {[part['text'] for part in parts]}, gaps {gaps}"
    )


def test_task_5_a_removed_stage_s_row_leaves_the_recipe_tab_before_the_save(
    browser, server_on, scratch_durables
):
    """Task 5 (M-D7; spec 0.4 §3.1), on the Recipe tab of Task 10 (design
    pass 9 §4): on a copy of the durables model with its recipe
    `declaration/spec.yml` open, a click on `Remove stage` in `bequest`'s
    row of the Recipe tab takes the row out of the tab once the trellis is
    read from the unsaved buffers, the recipe on disk still writing it; one
    Command+Z in the recipe brings the row back; made again and the recipe
    saved, the file on disk holds no row of `bequest` and the tab none."""
    block = '.bl-recipe-row[data-stage="bequest"]'
    button = f"{block} .bl-remove-stage"
    recipe_file = scratch_durables / RECIPE_FILE
    recipe_text = recipe_file.read_text(encoding="utf-8")
    rows = [line for line in recipe_text.splitlines(True) if line.startswith("  bequest:")]
    assert len(rows) == 1
    no_bequest = recipe_text.replace(rows[0], "")
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_durables), RECIPE_FILE)
        assert tab.locator(block).count() == 1
        tab.click(button)
        _, removed = wait_until(lambda: tab.locator(block).count() == 0, 60.0, "the block out")
        status = status_text(tab)
        assert tab.evaluate(DOCUMENT_JS) == no_bequest
        assert recipe_file.read_text(encoding="utf-8") == recipe_text

        # one Command+Z in the recipe takes the removal back
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == recipe_text, 10.0, "the removal undone")
        _, restored = wait_until(lambda: tab.locator(block).count() == 1, 60.0, "the block back")

        # made again, and the recipe saved
        tab.click(button)
        wait_until(lambda: tab.locator(block).count() == 0, 60.0, "the block out again")
        assert tab.evaluate(DOCUMENT_JS) == no_bequest
        tab.click(".bl-save")
        wait_until(
            lambda: recipe_file.read_text(encoding="utf-8") == no_bequest, 30.0, "the recipe saved"
        )
        tab.wait_for_timeout(1_000)
        assert tab.locator(block).count() == 0
        print(
            f"task 5: the row left {removed:.1f} s after the click, the status line then "
            f"{status!r}, and came back {restored:.1f} s after the undo"
        )
    finally:
        context.close()


# The regions Task 6 builds (design pass 8 §6): the folder column, the text
# column with the editor and the panel under it, and the forms.
TASK_6_REGIONS = ".bl-folder, .bl-file, .bl-forms"
# The tab of the Types panel that holds the focus, by its `data-tab`, null
# where none does (the delegated acceptance of unit M, D3).
FOCUSED_TAB_JS = """
() => {
  const focused = document.activeElement;
  return focused && focused.matches('.bl-class-tab') ? focused.dataset.tab : null;
}
"""
# The tabs of the Types panel as the library and the page mark them: the
# index the library's tabs hold selected, the tabs the page draws
# `.bl-active` and the tabs the library marks `active`, each by its
# `data-tab` (D3).
CLASS_TABS_SELECTED_JS = """
() => {
  const tabs = document.querySelector('.bl-class-tabs');
  const headers = Array.from(tabs.querySelectorAll('.bl-class-tab'));
  return {
    index: tabs.selectedIndex,
    active: headers.filter((header) => header.classList.contains('bl-active'))
      .map((header) => header.dataset.tab),
    marked: headers.filter((header) => header.hasAttribute('active'))
      .map((header) => header.dataset.tab),
  };
}
"""
# The elements of the system's own classes that a control may be (§7,
# measure 3): VSCode Elements' elements, by their tags, the text button, the
# document tab and a row of the tree, a list or a check (§4: rows are the
# page's own), or a cell of the Types tables (§5.3).
OWN_CONTROLS = ".bl-text-button, .bl-tab, .bl-row, .bl-class-table *"

# The measures of design pass 8 §7 read on the regions of Task 6: every
# drawn text node outside the editor's text, with its face, size, weight,
# letter-spacing and case and whether an element of the file's words holds
# it (measure 1); the heights of the heads, the bars, the rows and the
# controls (measure 2); every element that is a button, a field, a select
# or a check and is no VSCode Elements element and none of the system's own
# controls, every Vuetify button or field, each text button's radius and
# each icon target's box (measures 3 and 8); every SVG drawn and every
# text node that is a glyph a Codicon draws (measure 4); for each column,
# its left edge and the left edges of its head's name, its first control,
# its first row's text and its first table's first cell (measure 5); and
# the tops of the columns' heads and of the lower panels' heads (measure
# 6).
TASK_6_JS = r"""
([regionsSelector, own]) => {
  const regions = Array.from(document.querySelectorAll(regionsSelector));
  const drawn = (element) => element.getClientRects().length > 0
    && getComputedStyle(element).visibility === 'visible';
  const inRegions = (selector) => regions.flatMap((region) =>
    Array.from(region.querySelectorAll(selector))).filter(drawn);
  const name = (element) => `${element.tagName.toLowerCase()}.${element.getAttribute('class')}`;
  const textLeft = (element) => {
    if (!element) return null;
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      const rect = Array.from(range.getClientRects()).find((r) => r.width > 0);
      if (rect) return rect.left;
    }
    return null;
  };
  const texts = [];
  for (const region of regions) {
    const walker = document.createTreeWalker(region, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim() || node.parentElement.closest('.cm-editor')) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      if (!Array.from(range.getClientRects()).some((r) => r.width > 0 && r.height > 0)) continue;
      const style = getComputedStyle(node.parentElement);
      texts.push({
        text: node.textContent.trim().slice(0, 40),
        at: name(node.parentElement),
        style: [style.fontFamily.split(',')[0].replace(/"/g, '').trim(),
                parseFloat(style.fontSize), Number(style.fontWeight)],
        spacing: style.letterSpacing,
        transform: style.textTransform,
        code: node.parentElement.closest('.bl-code, .bl-code-name, .bl-code-small') !== null,
      });
    }
  }
  const height = (element) => [name(element), element.getBoundingClientRect().height];
  const heights = {
    heads: inRegions('.bl-head').map(height),
    bars: inRegions('.bl-bar, .bl-tab-row').map(height),
    rows: inRegions('.bl-row').map(height),
    controls: inRegions('vscode-button, vscode-textfield, vscode-textarea, vscode-single-select,'
                        + ' .bl-text-button')
      .map(height),
  };
  const controls = inRegions('button, input, select, textarea, [role="checkbox"], [role="radio"]')
    .filter((element) => !element.matches(own))
    .map(name);
  const vuetify = inRegions('.v-btn, .v-field, .v-input, .v-select').map(name);
  const radii = inRegions('.bl-text-button').map((element) =>
    [name(element), getComputedStyle(element).borderTopLeftRadius]);
  const targets = inRegions('vscode-toolbar-button').map((element) => {
    const box = element.getBoundingClientRect();
    return [name(element), box.width, box.height];
  });
  const svgs = inRegions('svg').filter((svg) => !svg.closest('.cm-editor'))
    .map((svg) => svg.outerHTML.slice(0, 80));
  const columns = {};
  for (const [key, selector] of [['folder', '.bl-folder'], ['file', '.bl-file']]) {
    const column = document.querySelector(selector);
    const head = column.querySelector(':scope > .bl-head > h2');
    const first = column.querySelector(':scope > .bl-head, :scope > .bl-tab-row');
    columns[key] = {
      left: column.getBoundingClientRect().left,
      head: head ? textLeft(head) : null,
      headTop: first ? first.getBoundingClientRect().top : null,
    };
  }
  const folder = document.querySelector('.bl-folder');
  columns.folder.row = textLeft(folder.querySelector('.bl-tree .bl-row'));
  columns.folder.panel = null;
  const file = document.querySelector('.bl-file');
  columns.file.tab = textLeft(file.querySelector('.bl-tab'));
  const types = file.querySelector('.bl-classification .bl-inspector-strip');
  columns.file.panel = types && drawn(types) ? {
    top: types.getBoundingClientRect().top,
    tab: textLeft(file.querySelector('.bl-class-tab')),
    cell: textLeft(file.querySelector('.bl-class-table th, .bl-recipe-heads > span')),
  } : null;
  return {texts, heights, controls, vuetify, radii, targets, svgs, columns,
          window: window.innerHeight};
}
"""


def task_6_measures(tab) -> dict:
    """The measures of Task 6's regions (TASK_6_JS), read with the pointer
    over the graph's canvas, so that no hover stands in them."""
    tab.mouse.move(1200, 500)
    tab.wait_for_timeout(300)
    return tab.evaluate(TASK_6_JS, [TASK_6_REGIONS, OWN_CONTROLS])


def test_task_6_the_folder_column_the_editor_the_types_panel_and_the_forms_stand_in_the_system(
    browser, server_on, scratch_durables
):
    """Task 6 (AAS, M-D4, M-D6, M-D11; design pass 8 §§5 to 7): on a copy of
    the durables model at 1600 × 1000, in the trellis view of
    `declaration/spec.yml`, in `keeper_cons.bl`'s view and with the form
    `new trellis` open over it, its first template chosen, the folder
    column, the text column with the editor and the panel under it, and the
    form meet the measures of §7. Measure 1: every drawn text outside the
    editor's text computes one of the five styles, with no letter-spacing
    and no change of case, the mono face only within the elements of the
    file's words. Measure 2: every head is 28 px but `Files`, a bar of 36 px
    level with the tabs' row and the graph bar since design pass 13 §4
    (D1), every bar 36, every row of the tree, the lists and the checks 24,
    and every button, field and select 26. Measure 3: every button, field,
    select and check is a VSCode Elements element, a text button, a document
    tab, a row or a cell of the Types tables, no Vuetify control stands in the
    regions, every text button has a radius of 4 px and every icon target is 24
    × 24. Measure 4: the regions draw no SVG and no text that a Codicon draws.
    Measure 5: in each column the head's name, the first control's box, the
    first row's text, the tab's text, the view tabs' first text and the first
    table's first cell start 12 px in from the column's left edge. Measure
    6: the folder's head and the text's tabs' row, its first row since
    unit N's Task 1 (design pass 10 §2), start at 36 px, and the
    head of the panel under the editor, on its Recipe tab with the recipe
    open and on its Types tabs with the stage open (Task 10; design pass 9
    §2), at 656 px, 320 px above the status line. The Types panel's tabs
    answer the keyboard: from
    `Fields`, ArrowRight and Enter show `Parameters`, which the library then
    marks selected, and ArrowLeft and Enter show `Fields` again (the
    delegated acceptance of unit M, D3)."""
    context, tab = new_tab(browser)
    views = {}
    try:
        url = server_on(scratch_durables)
        open_trellis(tab, url, RECIPE_FILE)
        tab.wait_for_selector(".bl-recipe-table vscode-single-select", timeout=30_000)
        views["trellis"] = task_6_measures(tab)
        open_file(tab, url, KEEPER_CONS)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        views["keeper_cons"] = task_6_measures(tab)
        # the Types panel's tabs by the keyboard: the arrow keys move the
        # focus and Enter shows the tab focused, which the library then marks
        # selected, there and back (the delegated acceptance of unit M, D3)
        tab.focus('.bl-class-tab[data-tab="Fields"]')
        for key, name, index in (("ArrowRight", "Parameters", 1), ("ArrowLeft", "Fields", 0)):
            tab.keyboard.press(key)
            wait_until(
                lambda name=name: tab.evaluate(FOCUSED_TAB_JS) == name, 5.0, f"the focus on {name}"
            )
            tab.keyboard.press("Enter")
            shown = ".bl-class-tables" if name == "Fields" else f'.bl-values[data-tab="{name}"]'
            tab.wait_for_selector(f".bl-classification {shown}", state="visible", timeout=10_000)
            selected = {"index": index, "active": [name], "marked": [name]}
            wait_until(
                lambda selected=selected: tab.evaluate(CLASS_TABS_SELECTED_JS) == selected,
                5.0,
                f"the tab {name} selected",
            )
        tab.click(".bl-new-trellis")
        form = '.bl-form[data-form="new trellis"]'
        tab.wait_for_selector(form, timeout=30_000)
        tab.locator(f"{form} .bl-template-button").first.click()
        tab.wait_for_selector(f"{form} .bl-create-key vscode-textfield", timeout=10_000)
        views["new trellis"] = task_6_measures(tab)
    finally:
        context.close()

    for view, measured in views.items():
        # measure 1: the five styles
        texts = measured["texts"]
        assert texts, view
        for text in texts:
            assert tuple(text["style"]) in FIVE_STYLES, (view, text)
            assert (text["spacing"], text["transform"]) == ("normal", "none"), (view, text)
            if text["style"][0] == "IBM Plex Mono":
                assert text["code"], (view, text)
            assert text["text"] not in GLYPH_TEXTS, (view, text)

        # measure 2: heads 28 but the Files bar's 36 (design pass 13 §4;
        # D1), bars 36, rows 24, controls 26
        heights = measured["heights"]
        for kind, expected in (("heads", 28), ("bars", 36), ("rows", 24), ("controls", 26)):
            assert heights[kind], (view, kind)
            wrong = [
                found
                for found in heights[kind]
                if abs(found[1] - (36 if FILES_BAR in found[0] else expected)) > 0.5
            ]
            assert wrong == [], (view, kind, wrong)

        # measures 3 and 4: the controls, their radii and targets, the icons
        assert measured["controls"] == [], view
        assert measured["vuetify"] == [], view
        assert {radius for _, radius in measured["radii"]} <= {"4px"}, view
        assert [found for found in measured["targets"] if found[1:] != [24, 24]] == [], view
        assert measured["svgs"] == [], view

        # measure 5: the text edges; measure 6: the heads' lines
        if view == "new trellis":
            continue
        columns = measured["columns"]
        for key, column in columns.items():
            edge = column["left"] + 12
            assert abs(column["headTop"] - 36) <= 0.5, (view, key, column)
            # the folder holds no control, the recipe's selects having left
            # the column for the panel under the editor (design pass 9 §5)
            # and the occurrence's choice for the main bar (unit N, Task 1);
            # the text column has no head, its tabs' row its first row
            places = ["head", "row"] if key == "folder" else ["tab"]
            assert key != "file" or column["head"] is None, column
            for place in places:
                assert abs(column[place] - edge) <= 1, (view, key, place, column)
            panel = column["panel"]
            if panel is None:
                assert key == "folder", (view, key)
                continue
            assert abs(panel["top"] - 656) <= 0.5, (view, key, panel)
            for place in [part for part in ("name", "tab", "cell") if part in panel]:
                assert abs(panel[place] - edge) <= 1, (view, key, place, panel)
    print(
        "task 6: "
        + "; ".join(
            f"{view}: {len(measured['texts'])} texts, "
            + ", ".join(f"{len(found)} {kind}" for kind, found in measured["heights"].items())
            + f", {len(measured['targets'])} targets"
            for view, measured in views.items()
        )
        + f"; the columns {views['keeper_cons']['columns']}"
    )


# The regions Task 7 builds (design pass 8 §6): the graph column with
# Details under the canvas, and Matsya's column; and the whole page, every
# region of the window, on which §7's eight measures are read at the end.
GRAPH_COLUMN = ".bl-view"
MATSYA_COLUMN = ".bl-matsya"
# The controls of the whole page that are the page's own beyond those of
# Task 6 (OWN_CONTROLS): the main bar's four toggles, each its icon of Task
# 11, the path's links and the recipes after it (unit N, Task 1; design
# pass 10 §3), and the graph bar's error mark, the Codicon `error` with its
# count, which §6 draws as the page's own and no VSCode Elements control
# draws (Task 4; M-I57).
PAGE_CONTROLS = f"{OWN_CONTROLS}, .bl-toggle, .bl-crumb, .bl-recipe-holder, .bl-error-mark"
WHOLE_PAGE = ".bl-main-bar, .bl-folder, .bl-file, .bl-view, .bl-matsya, .bl-status"
# The parts of the page that §7 leaves out of its measures of text and color
# and of its controls: the editor's source text, the graph's drawing, which
# spec 0.4 §5.3 sets, with the legend's swatches, which draw samples of it,
# and React Flow's attribution (§5.1).
OUTSIDE_THE_SYSTEM = (
    ".cm-editor, .react-flow__viewport, .react-flow__attribution, .bl-legend-ground"
)
# The color roles of §5.4 a region's chrome may draw, beyond COLOR_ROLES:
# the selection's wash (§5.5); and the colors §5.4 keeps for one element
# each, periwinkle for Matsya's `Υ`.
SELECTION_ROLES = ("--bl-selected",)
KEPT_COLORS = {"--bl-periwinkle": ".bl-matsya-upsilon"}

# The measures of design pass 8 §7 read on the regions given, outside the
# editor's text, the graph's drawing and React Flow's attribution: every
# drawn text node with its face, size, weight, letter-spacing and case and
# whether an element of the file's words holds it (measure 1); the heights
# of the heads, the bars, the rows, Details' rows with their values, and the
# controls (measure 2); every button, field, select or check that is no
# VSCode Elements element and none of the system's own controls, every
# Vuetify control or icon, each text button's radius and each icon target
# (measure 3); every SVG, and every Lucide icon left under the window, the
# graph's drawing included (measure 4); each
# column's left edge with the left edges of its head's name, its first
# control and its first row's text, and the top of its head, and the head
# of Details (measures 5 and 6); every color drawn that is no role of §5.4
# (measure 7); and the box of every target (measure 8).
TASK_7_JS = r"""
([regionsSelector, own, roles, kept, outside]) => {
  const drawn = (element) => element.getClientRects().length > 0
    && element.checkVisibility({visibilityProperty: true});
  const regions = Array.from(document.querySelectorAll(regionsSelector)).filter(drawn);
  const shown = (element) => drawn(element) && element.closest(outside) === null;
  const inRegions = (selector) => regions.flatMap((region) =>
    Array.from(region.querySelectorAll(selector))).filter(shown);
  const name = (element) => `${element.tagName.toLowerCase()}.${element.getAttribute('class')}`;
  const box = (element) => {
    const rect = element.getBoundingClientRect();
    return {left: rect.left, top: rect.top, width: rect.width, height: rect.height};
  };
  const textLeft = (element) => {
    if (!element) return null;
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim() || !shown(node.parentElement)) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      const rect = Array.from(range.getClientRects()).find((r) => r.width > 0);
      if (rect) return rect.left;
    }
    return null;
  };
  const texts = [];
  for (const region of regions) {
    const walker = document.createTreeWalker(region, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim() || node.parentElement.closest(outside)) continue;
      if (!drawn(node.parentElement)) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      if (!Array.from(range.getClientRects()).some((r) => r.width > 0 && r.height > 0)) continue;
      const style = getComputedStyle(node.parentElement);
      texts.push({
        text: node.textContent.trim().slice(0, 40),
        at: name(node.parentElement),
        style: [style.fontFamily.split(',')[0].replace(/"/g, '').trim(),
                parseFloat(style.fontSize), Number(style.fontWeight)],
        spacing: style.letterSpacing,
        transform: style.textTransform,
        code: node.parentElement.closest('.bl-code, .bl-code-name, .bl-code-small') !== null,
      });
    }
  }
  const height = (element) => [name(element), element.getBoundingClientRect().height];
  const heights = {
    heads: inRegions('.bl-head').map(height),
    bars: inRegions('.bl-bar, .bl-tab-row').map(height),
    rows: inRegions('.bl-row').map(height),
    details: inRegions('.bl-details-row, .bl-attribute').map((row) => {
      const value = row.querySelector(':scope > .bl-details-value, :scope > .bl-attribute-value');
      return [name(row), row.getBoundingClientRect().height,
              value ? value.getBoundingClientRect().height : null];
    }),
    controls: inRegions('vscode-button, vscode-textfield, vscode-textarea, vscode-single-select,'
                        + ' .bl-text-button')
      .map(height),
  };
  const controls = inRegions('button, input, select, textarea, [role="checkbox"], [role="radio"]')
    .filter((element) => !element.matches(own))
    .map(name);
  const vuetify = inRegions('.v-btn, .v-field, .v-input, .v-select, .v-icon').map(name);
  const radii = inRegions('.bl-text-button').map((element) =>
    [name(element), getComputedStyle(element).borderTopLeftRadius]);
  const icons = inRegions('vscode-toolbar-button').map((element) => {
    const found = element.getBoundingClientRect();
    return [name(element), found.width, found.height,
            element.closest('.bl-main-bar') !== null];
  });
  const svgs = inRegions('svg').map((svg) => svg.outerHTML.slice(0, 80));
  const lucide = Array.from(document.querySelectorAll('.bl-window svg.bl-icon'))
    .map((svg) => svg.outerHTML.slice(0, 80));
  const columns = {};
  for (const [key, selector] of [['folder', '.bl-folder'], ['file', '.bl-file'],
                                 ['view', '.bl-view'], ['matsya', '.bl-matsya']]) {
    const column = document.querySelector(selector);
    if (!column || !regions.includes(column)) continue;
    // a column's first row: its head, the text's tabs' row or the graph bar
    // (design pass 10 §2), and the first text it holds
    const head = column.querySelector(':scope > .bl-head, :scope > .bl-tab-row,'
                                      + ' :scope > .bl-graph-bar');
    columns[key] = {
      left: column.getBoundingClientRect().left,
      head: head ? textLeft(head.querySelector('h2, .bl-tab')) : null,
      headTop: head ? head.getBoundingClientRect().top : null,
      headHeight: head ? head.getBoundingClientRect().height : null,
    };
  }
  if (columns.view) {
    const view = document.querySelector('.bl-view');
    const control = view.querySelector('.bl-graph-bar vscode-single-select');
    columns.view.control = control ? control.getBoundingClientRect().left : null;
    columns.view.bar = box(view.querySelector('.bl-graph-bar'));
    const host = view.querySelector('.bl-view-host');
    columns.view.canvas = host ? box(host) : null;
    const foot = view.querySelector('.bl-graph-controls');
    columns.view.foot = foot && drawn(foot) ? box(foot) : null;
    const details = view.querySelector('.bl-panel > .bl-region-head');
    columns.view.details = details && drawn(details) ? {
      top: details.getBoundingClientRect().top,
      name: textLeft(details.querySelector('h2')),
      row: textLeft(view.querySelector('.bl-panel-body')),
    } : null;
  }
  if (columns.matsya) {
    const composer = document.querySelector('.bl-matsya vscode-textarea');
    columns.matsya.control = composer ? composer.getBoundingClientRect().left : null;
    columns.matsya.top = document.querySelector('.bl-matsya').getBoundingClientRect().top;
  }
  const probe = document.createElement('span');
  document.body.append(probe);
  const color = (role) => {
    probe.style.color = `var(${role})`;
    return getComputedStyle(probe).color;
  };
  const allowed = new Set(['rgba(0, 0, 0, 0)', ...roles.map(color)]);
  const keptColors = Object.entries(kept).map(([role, selector]) => [color(role), selector]);
  probe.remove();
  const colors = [];
  const record = (element, property, value) => {
    if (allowed.has(value)) return;
    const keptHere = ([found, selector]) => found === value && element.matches(selector);
    if (keptColors.some(keptHere)) return;
    colors.push(`${name(element)} ${property} ${value}`);
  };
  for (const element of inRegions('*')) {
    const style = getComputedStyle(element);
    record(element, 'background', style.backgroundColor);
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) {
      if (parseFloat(style[`border${side}Width`]) > 0 && style[`border${side}Style`] !== 'none') {
        record(element, `border-${side.toLowerCase()}`, style[`border${side}Color`]);
      }
    }
    const lettered = Array.from(element.childNodes).some(
      (node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
    if (lettered || element.matches('svg, .codicon, .bl-toggle-glyph')) {
      record(element, 'color', style.color);
    }
  }
  const targets = inRegions('button, a[href], [role="button"], [tabindex]:not([tabindex="-1"]),'
                            + ' [data-link], vscode-toolbar-button')
    .filter((element) => !element.parentElement.closest('vscode-toolbar-button, button, a[href]'))
    .map((element) => [name(element), box(element)]);
  return {texts, heights, controls, vuetify, radii, icons, svgs, lucide, columns, colors,
          targets, title: box(document.querySelector('.bl-main-bar')),
          status: box(document.querySelector('.bl-status')), window: window.innerHeight};
}
"""


# The toggles of the graph's drawing that open or close a layer (design pass
# 8 §3; the delegated acceptance of unit M, D2): a closed layer's box, an
# open layer's head and a card's chevron, each as its accessible name, its
# text, the name of the Codicon it holds, null where it holds none, and
# whether it is a card's; a builder's segment of a compact card, a toggle
# whose text is the pair's signs and the builder's id, is left out.
GRAPH_TOGGLES_JS = r"""
() => Array.from(
  document.querySelectorAll(
    '.bl-view-host .react-flow__viewport .bf-toggle:not(.bf-builder-toggle)'),
  (toggle) => {
    const icon = toggle.querySelector(':scope > .codicon');
    const name = icon && Array.from(icon.classList).find(
      (each) => each.startsWith('codicon-') && each !== 'codicon');
    return {label: toggle.getAttribute('aria-label'), text: toggle.textContent.trim(),
            icon: name ? name.slice('codicon-'.length) : null,
            card: toggle.classList.contains('bf-chevron')};
  })
"""


def task_7_measures(tab, regions: str) -> dict:
    """The measures of design pass 8 §7 on the regions `regions` (TASK_7_JS)
    with their Codicons (`drawn_codicons`) and the texts of the whole window
    under their contrast bound (spec 0.4 §5.8) outside the graph's drawing,
    which spec 0.4 §5.3 sets and the system leaves as it is (§5.1; M-I62),
    read with the pointer over the graph's canvas, so that no hover stands
    in a measured region; and the toggles of the graph's drawing
    (GRAPH_TOGGLES_JS), which measure 4 reads."""
    tab.mouse.move(1200, 400)
    tab.wait_for_timeout(300)
    measured = tab.evaluate(
        TASK_7_JS,
        [
            regions,
            PAGE_CONTROLS,
            [*COLOR_ROLES, *SELECTION_ROLES],
            KEPT_COLORS,
            OUTSIDE_THE_SYSTEM,
        ],
    )
    measured["codicons"], measured["glyphs"] = drawn_codicons(tab, regions)
    measured["contrast"] = contrast_faults(tab, [*CONTRAST_EXCEPTIONS, ".react-flow__viewport"])
    measured["toggles"] = tab.evaluate(GRAPH_TOGGLES_JS)
    return measured


def assert_task_7_measures(view: str, measured: dict, whole: bool) -> None:
    """The measures of design pass 8 §7 that `task_7_measures` read in the
    view `view`, on the whole page where `whole` holds and otherwise on the
    graph column with Details, or on Matsya's column."""
    # measure 1: the five styles, outside the editor's text and the graph's
    # drawing; the mono face only on the file's words; no glyph as text
    texts = measured["texts"]
    assert texts, view
    for text in texts:
        assert tuple(text["style"]) in FIVE_STYLES, (view, text)
        assert (text["spacing"], text["transform"]) == ("normal", "none"), (view, text)
        if text["style"][0] == "IBM Plex Mono":
            assert text["code"], (view, text)
        assert text["text"] not in GLYPH_TEXTS, (view, text)

    # measure 2: the main bar 36, every head 28 but Matsya's, level with the
    # main bar at 36, and the Files bar's, a bar of 36 since design pass 13
    # §4 (D1), every bar 36, the graph bar 36 or, in a column too
    # narrow for its items, a whole number of rows of 36 (amendment 02
    # ruling 5; unit N, Task 1), every row 24, every control 26, the status
    # line 24; a row of Details 24 where its value holds one line
    heights = measured["heights"]
    for found in heights["heads"]:
        expected = 36 if "bl-matsya-head" in found[0] or FILES_BAR in found[0] else 28
        assert abs(found[1] - expected) <= 0.5, (view, "head", found)
    for kind, expected in (("bars", 36), ("rows", 24), ("controls", 26)):
        wrong = [
            found
            for found in heights[kind]
            if abs(found[1] - expected) > 0.5
            and not (
                "bl-graph-bar" in found[0]
                and abs(found[1] - expected * round(found[1] / expected)) <= 0.5
            )
        ]
        assert wrong == [], (view, kind, wrong)
    for row, height, value in heights["details"]:
        assert height >= 23.5, (view, row, height)
        if value is not None and value <= 16.5:
            assert abs(height - 24) <= 0.5, (view, row, height, value)
    if whole:
        title, status = measured["title"], measured["status"]
        assert abs(title["top"]) <= 0.5 and abs(title["height"] - 36) <= 0.5, (view, title)
        assert abs(status["height"] - 24) <= 0.5, (view, status)
        assert abs(status["top"] + status["height"] - measured["window"]) <= 0.5, (view, status)

    # measure 3: the controls, their radii and their targets
    assert measured["controls"] == [], (view, measured["controls"])
    assert measured["vuetify"] == [], (view, measured["vuetify"])
    assert {radius for _, radius in measured["radii"]} <= {"4px"}, view
    # an icon target 24 × 24, the main bar's 26 × 26 (design pass 10 §3)
    wrong = [
        found
        for found in measured["icons"]
        if found[1:3] != ([26, 26] if found[3] else [24, 24])
    ]
    assert wrong == [], (view, wrong)

    # measure 4: Codicons at 16 px, the main bar's toggles' among them; no
    # SVG and no Lucide icon left under the window
    assert measured["svgs"] == [], (view, measured["svgs"])
    assert measured["lucide"] == [], (view, measured["lucide"])
    for glyph in measured["codicons"] + measured["glyphs"]:
        # the `add` glyph beside a word, drawn as a bare Codicon, is 12 px since design pass 14 §8 (S-D15); every
        # other Codicon keeps 16, the library's icon button `add` of the Fields tab among them
        expected = 12 if glyph["name"] == "codicon-add" and not glyph["library"] else 16
        assert glyph["drawn"] and glyph["size"] == expected and glyph["face"] == "codicon", (view, glyph)
    # the drawing's toggles, which the text measure leaves out with the
    # drawing: each the Codicon `chevron-right` or `chevron-down`, a closed
    # layer's opening and an open layer's closing, and no glyph as text
    # (the delegated acceptance of unit M, D2)
    for toggle in measured["toggles"]:
        assert toggle["text"] not in GLYPH_TEXTS and toggle["text"] == "", (view, toggle)
        expected = "chevron-right" if toggle["label"].startswith("open ") else "chevron-down"
        assert toggle["icon"] == expected, (view, toggle)

    # measures 5 and 6: the text edges at the column's x + 12, the columns'
    # first rows at 36, under the main bar, and Details' head at 656, 320 px
    # above the status line; Matsya's head from the window's top, level
    # with the main bar; the graph bar's selects after its name
    columns = measured["columns"]
    for key, column in columns.items():
        edge = column["left"] + 12
        assert abs(column["head"] - edge) <= 1, (view, key, column)
        if key == "matsya":
            assert abs(column["headTop"]) <= 0.5 and abs(column["top"]) <= 0.5, (view, column)
            assert abs(column["control"] - edge) <= 1, (view, key, column)
            continue
        assert abs(column["headTop"] - 36) <= 0.5, (view, key, column)
        if key != "view":
            continue
        assert column["control"] > column["head"], (view, key, column)
        canvas, foot, details = column["canvas"], column["foot"], column["details"]
        bar = column["bar"]
        assert abs(canvas["top"] - (36 + bar["height"])) <= 0.5, (view, canvas, bar)
        assert abs(canvas["top"] + canvas["height"] - 656) <= 0.5, (view, canvas)
        # the foot's controls float 12 px inside the canvas's lower left
        assert abs(foot["left"] - (canvas["left"] + 12)) <= 0.5, (view, foot)
        bottom = canvas["top"] + canvas["height"] - 12
        assert abs(foot["top"] + foot["height"] - bottom) <= 0.5, (view, foot)
        assert abs(details["top"] - 656) <= 0.5, (view, details)
        assert abs(details["name"] - edge) <= 1 and abs(details["row"] - edge) <= 1, (
            view,
            details,
        )
    assert set(columns) >= ({"matsya"} if "Matsya" in view else {"view"}), (view, columns)

    # measure 7: every chrome color a role of §5.4
    assert measured["colors"] == [], (view, measured["colors"])

    # measure 8: contrast and targets
    assert measured["contrast"] == [], (view, measured["contrast"])
    small = [
        target
        for target in measured["targets"]
        if target[1]["width"] < 23.5 or target[1]["height"] < 23.5
    ]
    assert small == [], (view, small)


def test_task_7_the_graph_column_details_and_matsya_stand_in_the_system_and_the_page_meets_7(
    browser, server_on, durables_folder
):
    """Task 7 (AAS, M-D4, M-D6, M-D11; design pass 8 §§5 to 7): on the
    durables model at 1600 × 1000, the graph column, Details and Matsya's
    column meet the measures of §7 in the trellis view of
    `declaration/spec.yml` with Matsya folded, with the occurrence
    `periods[0]/keeper_cons` selected, and in `keeper_cons.bl`'s view with
    nothing selected and with the box `cntn_to_dcsn:Pullback` selected,
    Matsya folded as §6 reads the page; Matsya's column, opened by the
    main bar's toggle in the trellis view; and the whole page meets the eight
    measures in the trellis view and in `keeper_cons.bl`'s view.
    Measure 1: every drawn text outside the editor's text, the graph's
    drawing and React Flow's attribution computes one of the five styles,
    with no letter-spacing and no change of case, the mono face only within
    the elements of the file's words, and none is `▸`, `▾`, `×`, `+` or
    `!`. Measure 2: the main bar is 36 px, every head 28 but Matsya's, 36
    from the window's top, and `Files`, a bar of 36 since design pass 13 §4
    (D1), every bar 36, the graph bar 36 or, in a column
    too narrow for its items, a whole number of rows of 36 (amendment 02
    ruling 5; unit N, Task 1),
    every row 24, a row of Details 24 where its value holds one line, every
    control 26 and the status line 24.
    Measure 3: every button, field, select and check is a VSCode Elements
    element or one of the system's own controls, no Vuetify control or icon
    stands, every text button has a radius of 4 px and every icon target is
    24 × 24, the main bar's 26 × 26 (design pass 10 §3). Measure 4: every
    icon is a Codicon at 16 px, no SVG and no Lucide icon stands under
    the window, the graph's drawing included; in the drawing, every toggle
    of a layer's box, of a layer's head and of a card is the Codicon
    `chevron-right` where it opens the
    layer and `chevron-down` where it closes it, and holds no text, `▸` and
    `▾` among them, the periods' frames of the trellis view included (the
    delegated acceptance of unit M, D2). Measure 5: in each column the
    head's name, and in the graph column the first control and Details'
    first row, start 12 px in from
    the column's left edge, as Matsya's head and composer do, the graph
    bar's selects after its name `Semantic graph`. Measure 6: the columns'
    first rows start at 36 px, Details' head at 656 px, 320 px above the
    status line, the canvas runs from the graph bar's foot to 656 px with
    the foot's controls floating 12 px inside its lower left. Measure 7:
    every chrome color is a role of §5.4, periwinkle on Matsya's `Υ` alone.
    Measure 8: every text
    meets its contrast bound and every target is at least 24 × 24."""
    occurrence = "periods[0]/keeper_cons" + LAYER_ID_ENDING
    pullback = "cntn_to_dcsn:Pullback"
    views = {}
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        tab.wait_for_selector(".bl-graph-bar vscode-single-select", timeout=30_000)
        views["trellis", True] = task_7_measures(tab, WHOLE_PAGE)
        select_until(
            tab,
            occurrence,
            "backward",
            lambda: tab.locator(".bl-occurrence-details .bl-details-row").count() > 0,
            "Details of periods[0]/keeper_cons",
        )
        views["trellis, an occurrence selected", False] = task_7_measures(tab, GRAPH_COLUMN)
        tab.click(MATSYA_TOGGLE)
        tab.wait_for_selector(".bl-matsya vscode-textarea", timeout=10_000)
        views["trellis, Matsya open", False] = task_7_measures(tab, MATSYA_COLUMN)
        tab.click(f"{MATSYA_COLUMN} .bl-fold")
        open_file(tab, url, KEEPER_CONS)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        if tab.locator(MATSYA_COLUMN).is_visible():
            tab.click(f"{MATSYA_COLUMN} .bl-fold")
        wait_until(
            lambda: not tab.locator(MATSYA_COLUMN).is_visible(), 10.0, "Matsya's column folded"
        )
        views["keeper_cons", True] = task_7_measures(tab, WHOLE_PAGE)
        select_until(
            tab,
            pullback,
            "backward",
            lambda: tab.locator(".bl-box-details .bl-kernel").count() == 1,
            f"Details of {pullback}",
        )
        views["keeper_cons, a box selected", False] = task_7_measures(tab, GRAPH_COLUMN)
    finally:
        context.close()

    for (view, whole), measured in views.items():
        assert_task_7_measures(view, measured, whole)
    # the periods' frames of the trellis are open layers whose heads carry
    # the toggle (D2)
    heads = [found for found in views["trellis", True]["toggles"] if not found["card"]]
    assert heads and {found["icon"] for found in heads} == {"chevron-down"}, heads
    print(
        "task 7: "
        + "; ".join(
            f"{view}: {len(measured['texts'])} texts, "
            + ", ".join(f"{len(found)} {kind}" for kind, found in measured["heights"].items())
            + f", {len(measured['codicons']) + len(measured['glyphs'])} Codicons, "
            f"{len(measured['targets'])} targets"
            for (view, _), measured in views.items()
        )
        + f"; the columns {views['keeper_cons', True]['columns']}"
    )


# The drawing of the region as Task 8 reads it (AAS, M-D15), in pixels on
# the screen: the region's box; the boxes of the frames of `periods[0]` and
# `periods[1]` and of the `start` node at which the terminal condition enters
# the graph, which replaces the graph's own `Inputs` (design pass 10 §6;
# unit N, Task 6); the union of the boxes the
# region draws; each wire's label, its text, face, style, size, opacity and
# box; the count of the grounds drawn behind labels; each cable's port on a
# card, its card's id, its side, the width on the screen of its press
# target and the size, in the card's own pixels, of its mark (design pass
# 13 §1, rules 1 and 3); and each wire, its id, the box of its arrowhead,
# null where it draws none, whether it is the bundle of a pair of cards,
# that pair's namespaces, the count its bus mark prints and its hover.
GRAPH_AS_MOCK_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host');
  const box = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, right: found.right, top: found.top, bottom: found.bottom,
            width: found.width, height: found.height};
  };
  const frame = (id) => {
    const node = host.querySelector(`.react-flow__node[data-id="${CSS.escape(id)}"]`);
    return node ? box(node) : null;
  };
  // the label of the boundary marker whose node is `id`, beside its mark
  const label = (id) => {
    const node = host.querySelector(`.react-flow__node[data-id="${CSS.escape(id)}"]`);
    const text = node && node.querySelector('.bf-boundary-label');
    return text ? box(text) : null;
  };
  const nodes = Array.from(host.querySelectorAll('.react-flow__node'), box);
  return {
    region: box(host.querySelector('.react-flow')),
    frames: {early: frame('periods[0]___group___'), later: frame('periods[1]___group___'),
             start: frame('start:periods[0]/bequest/bequest:function:cntn:V'),
             startLabel: label('start:periods[0]/bequest/bequest:function:cntn:V')},
    drawn: {left: Math.min(...nodes.map((found) => found.left)),
            right: Math.max(...nodes.map((found) => found.right))},
    labels: Array.from(host.querySelectorAll('.react-flow__edge .bf-join'), (text) => {
      const style = getComputedStyle(text);
      const title = text.closest('.react-flow__edge').querySelector('title');
      return {text: text.textContent, family: style.fontFamily, style: style.fontStyle,
              size: style.fontSize, opacity: style.opacity, at: box(text), title: title ? title.textContent : ''};
    }),
    grounds: host.querySelectorAll('.bf-join-ground').length,
    marks: Array.from(host.querySelectorAll('.bf-card > .react-flow__handle.bf-mark'), (mark) => ({
      card: mark.closest('.react-flow__node').dataset.id})),
    ports: Array.from(host.querySelectorAll('.bf-card > .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)'), (port) => ({
      card: port.closest('.react-flow__node').dataset.id, side: port.dataset.side, width: port.getBoundingClientRect().width,
      mark: parseFloat(getComputedStyle(port, '::before').width)})),
    wires: Array.from(host.querySelectorAll('.react-flow__edge'), (edge) => {
      const arrow = edge.querySelector('.bf-arrow'), count = edge.querySelector('.bf-cable-count');
      const title = edge.querySelector('title');
      return {id: edge.dataset.id, arrow: arrow ? box(arrow) : null,
              bundle: edge.classList.contains('bf-pair-bundle'), pair: edge.classList.contains('bf-join-pair'),
              dashed: !!edge.querySelector('.bf-cable-dashed'), count: count ? count.textContent : null,
              title: title ? title.textContent : '',
              from: edge.getAttribute('data-from'), to: edge.getAttribute('data-to')};
    }),
  };
}
"""
# the least scale at which a trellis graph opens (spec 0.4 §2.3; K-D22, as
# M-D15 keeps it as the floor), the least scale at which a stage view
# opens (Q-D7), and the room the opening keeps at each side of the region
READING_FLOOR = 0.6
STAGE_READING_FLOOR = 0.8
OPENING_ROOM = 10
# a cable's port at scale 1: its press target, held at no less than 10 px
# on the screen, and its mark, a 6-px square held at no less than 3 px on
# the screen; and a terminal marker, an 8-px circle (design pass 13 §1,
# rules 1, 3 and 6); a cable draws no arrowhead since design pass 11 §1a
PORT_TARGET, PORT_MARK, MARK_LEAST = 10, 6, 3
MARKER = 8
# the functions the wires from `tenure` of periods[0] carry into periods[1]
# of the durables model's backward trellis graph: its arrival's value and
# marginal values
TENURE_VALUES = {"𝑉", "𝑑𝑉_a", "𝑑𝑉_h"}


def opening_scale(view: dict, width: float, floor: float = READING_FLOOR) -> float:
    """The scale at which a graph opens with a frame, or a graph, `width`
    wide at scale 1 in a region of the width `view` gives (`viewport`): the
    largest, at most 1 and at least `floor`, READING_FLOOR for a trellis
    graph and STAGE_READING_FLOOR for a stage view, at which the frame
    fills the region less OPENING_ROOM at each side (AAS, M-D15; Q-D7)."""
    return max(floor, min(1.0, (view["width"] - 2 * OPENING_ROOM) / width))


def test_task_8_the_graph_is_drawn_as_design_pass_8_s_mock_draws_it(
    browser, server_on, durables_folder
):
    """Task 8 (AAS, M-D15; design pass 8's mock, as design pass 13 amends
    it). On the durables model at 1600 × 1000, the backward trellis graph
    of `declaration/spec.yml`, periods 0 to 2: (a) opens at the largest
    scale, at most 1 and at least 0.6, at which the frame of its terminal
    period, periods[0], with the marker of its terminal condition and that
    marker's label, which stand between the frame and the graph's left end,
    fills the region less 10 px at each side (N-I277), where it opened at
    0.6, the frame within the region less 10 px and the marker, the 8-px
    circle that replaces the graph's `Inputs` (design pass 13 §1, rule 6;
    unit N, Tasks 6 and 7), and its label `terminal condition 𝑉≻()` wholly
    within the region beside it; (b) draws no cable's label and no ground
    behind one, a cable of a branch standing its branch first in its title
    (the fix wave Q3a of unit Q, item 4, which amends Q-D17 and design pass
    13 §1, rule 7, which had retired the `3 wires` label and the STIX
    setting of unit N's Task 3); (c) draws on each card the cables' ports
    alone, each a press target of 10 px on the screen with a 6-px mark at
    the view's scale, and no per-field mark, and ends no cable in an
    arrowhead (design pass 13 §1, rules 1 and 3; design pass 11 §1a); (d)
    draws the wires from `tenure` of periods[0] into periods[1] as one
    cable for each route, two, each from a plug of its own on `tenure` to
    one reader of periods[1], each a cable whose route Details names and
    each counting at its plug the wires it carries, `3`, the names of the
    three functions in its hover (design pass 13 §1, rule 5; design pass
    12 §2), where M-D15 drew one piece for both from one port of `tenure`,
    labeled `6 wires`. `keeper_cons.bl`'s stage view opens at the largest
    scale, at most 1 and at least 0.8, at which its width fits the region
    less 10 px at each side (Q-D7)."""
    tenure = f"periods[0]/tenure{LAYER_ID_ENDING}"
    bequest = f"periods[0]/bequest{LAYER_ID_ENDING}"
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        lay_out_left_to_right(tab)
        tab.mouse.move(1300, 600)

        def opened() -> bool:
            view = viewport(tab)
            early = tab.evaluate(DRAWN_PLACES_JS)["nodes"].get(f"periods[0]{LAYER_ID_ENDING}")
            if view is None or early is None:
                return False
            # the box the opening shows runs from the graph's left end, where
            # the marker of the terminal condition and its label stand, to the
            # right edge of periods[0]'s frame, whose width alone the opening
            # filled before the label was taken into it (N-I277)
            expected = opening_scale(view, early["x"] + early["width"])
            return abs(view["zoom"] - expected) <= 1e-6

        wait_until(opened, 30.0, "the backward trellis at its opening on periods[0]")
        view, drawn = viewport(tab), tab.evaluate(GRAPH_AS_MOCK_JS)

        # (a) the opening scale, the terminal frame within the region and
        # the marker of its terminal condition, the 8-px circle, wholly
        # within the region beside it (design pass 13 §1, rule 6; unit N, Task 7)
        region, early = drawn["region"], drawn["frames"]["early"]
        assert view["zoom"] > READING_FLOOR + 1e-6, view
        assert region["left"] + OPENING_ROOM - 1 <= early["left"], (region, early)
        assert early["right"] <= region["right"] - OPENING_ROOM + 1, (region, early)
        start = drawn["frames"]["start"]
        assert region["left"] <= start["left"] and start["right"] <= early["left"], (region, start, early)
        assert abs(start["width"] - MARKER * view["zoom"]) <= 0.5, start
        label = drawn["frames"]["startLabel"]
        assert region["left"] <= label["left"] and label["right"] <= start["left"], (region, label, start)

        # (b) no cable's label and no ground; a cable of a branch stands its branch first in its title (the fix
        # wave Q3a, item 4)
        assert drawn["labels"] == [], drawn["labels"]
        assert drawn["grounds"] == 0
        branched = [wire for wire in drawn["wires"] if "|keep>>" in wire["id"] or "|adjust>>" in wire["id"]]
        assert branched, drawn["wires"]
        for wire in branched:
            branch = "keep" if "|keep>>" in wire["id"] else "adjust"
            assert wire["title"].split("\n")[0] == branch, wire

        # (c) the cables' ports alone on the cards, each a press target of 10
        # px on the screen with a 6-px mark at the view's scale, held at 3 px,
        # no per-field mark, and no cable ending in an arrowhead (design pass
        # 13 §1, rules 1 and 3; design pass 11 §1a)
        assert drawn["marks"] == [], drawn["marks"]
        assert drawn["ports"] and any(port["card"] == bequest for port in drawn["ports"]), drawn["ports"]
        for port in drawn["ports"]:
            assert abs(port["width"] - max(PORT_TARGET * view["zoom"], PORT_TARGET)) <= 0.5, port
            assert abs(port["mark"] * view["zoom"] - max(PORT_MARK * view["zoom"], MARK_LEAST)) <= 0.05, port
        # the piece the wires of a pair of periods share draws no arrowhead (K-D5), and a dashed stub to an
        # `outside` marker none (design pass 10 §6)
        # a cable runs from its plug into its socket and draws no arrowhead (design pass 11 §1a)
        assert drawn["wires"] and all(not wire["arrow"] for wire in drawn["wires"]), [wire for wire in drawn["wires"] if wire["arrow"]]

        # (d) the wires from tenure into periods[1], one cable for each route,
        # each from a plug of its own on tenure to one reader of periods[1],
        # each a cable whose record names its route, from that reader into
        # tenure (design pass 12 §2), read once Python's records of the
        # cables have reached the region, the view unchanged
        def leaving_of(found: dict) -> list:
            return [
                wire
                for wire in found["wires"]
                if wire["id"].startswith(f"{tenure}::out::")
                and wire["id"].split(">>")[1].startswith("periods[1]/")
            ]

        drawn, _ = wait_until(
            lambda: (found := tab.evaluate(GRAPH_AS_MOCK_JS))
            and leaving_of(found)
            and all(wire["from"] for wire in leaving_of(found))
            and found,
            10.0,
            "the cables from tenure with their records",
        )
        leaving = leaving_of(drawn)
        readers = {f"periods[1]/{key}" for key in ("keeper_cons", "adjuster_cons")}
        assert len(leaving) == len(readers), drawn["wires"]
        for wire in leaving:
            assert not wire["bundle"] and wire["to"] == "periods[0]/tenure", wire
            assert wire["from"] in readers, wire
            assert wire["id"].split(">>")[1].startswith(f"{wire['from']}{LAYER_ID_ENDING}::in::"), wire
        assert len({wire["id"].split(">>")[0] for wire in leaving}) == len(leaving), leaving
        assert {wire["from"] for wire in leaving} == readers, leaving
        # each cable counts at its plug the wires it carries, the three
        # functions of TENURE_VALUES, and its hover names those functions,
        # each once (design pass 13 §1, rule 5; design pass 12 §2)
        for wire in leaving:
            assert wire["count"] == str(len(TENURE_VALUES)), leaving
            named = {line.split("≺")[0] for line in wire["title"].split("\n") if "≺" in line}
            assert named == TENURE_VALUES, leaving

        # (a) the stage view at the largest scale at which its width fits
        open_file(tab, url, KEEPER_CONS)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        if tab.locator(MATSYA_COLUMN).is_visible():
            tab.click(f"{MATSYA_COLUMN} .bl-fold")

        def stage_opened() -> bool:
            view, found = viewport(tab), tab.evaluate(GRAPH_AS_MOCK_JS)
            if view is None or tab.locator(MATSYA_COLUMN).is_visible():
                return False
            width = (found["drawn"]["right"] - found["drawn"]["left"]) / view["zoom"]
            return abs(view["zoom"] - opening_scale(view, width, STAGE_READING_FLOOR)) * width <= 4

        wait_until(stage_opened, 30.0, "keeper_cons's stage view at its opening")
        stage = viewport(tab)
        print(
            f"task 8: the backward trellis opened at {view['zoom']:.3f}, periods[0] "
            f"{early['width']:.0f} px wide, {len(drawn['labels'])} cable labels, {len(drawn['ports'])} cable "
            f"ports, {len(drawn['wires'])} cables without arrowheads, the counts at the plugs of the cables "
            f"from periods[0] into periods[1] {[wire['count'] for wire in leaving]}; keeper_cons's stage view "
            f"opened at {stage['zoom']:.3f}"
        )
    finally:
        context.close()


def test_task_9_a_press_on_the_graph_moves_the_view_not_at_all_after_a_pan(
    browser, server_on, durables_folder
):
    """Task 9 (AAS, M-D16). On the durables model's backward trellis at its
    opening, a drag of 570 px on the empty ground pans the view by 570 px,
    which takes periods[0] out of the region; then a press on the ground and
    a click on the name of periods[1]'s `tenure` card leave the viewport
    where the drag put it, the card selected; a second drag pans by 570 px
    more; and a focus the script gives the region then reveals the selected
    card, as the keyboard's entry does (§2.4)."""
    tenure = f"periods[1]/tenure{LAYER_ID_ENDING}"
    node = f'.bl-view-host .react-flow__node[data-id="{tenure}"]'
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        lay_out_left_to_right(tab)
        tab.mouse.move(1300, 600)
        wait_until(
            lambda: (viewport(tab) or {}).get("zoom", 0) > 0.99 and tab.locator(node).count() == 1,
            30.0,
            "the backward trellis at its opening at scale 1",
        )
        tab.wait_for_timeout(500)
        pane = tab.locator(".bl-view-host .react-flow__pane").bounding_box()
        ground = (pane["x"] + pane["width"] - 40, pane["y"] + pane["height"] - 60)

        def drag(distance: float) -> dict:
            tab.mouse.move(*ground)
            tab.mouse.down()
            tab.mouse.move(ground[0] - distance, ground[1], steps=15)
            tab.mouse.up()
            tab.wait_for_timeout(800)
            return viewport(tab)

        def same(a: dict, b: dict) -> bool:
            return abs(a["x"] - b["x"]) <= 1 and abs(a["y"] - b["y"]) <= 1 and a["zoom"] == b["zoom"]

        opened = viewport(tab)
        panned = drag(570)
        assert abs(panned["x"] - (opened["x"] - 570)) <= 3 and abs(panned["y"] - opened["y"]) <= 3, (opened, panned)

        # a press on the empty ground moves the view not at all
        tab.mouse.click(*ground)
        tab.wait_for_timeout(800)
        assert same(viewport(tab), panned), (panned, viewport(tab))

        # a click on the name of periods[1]'s tenure card selects it and
        # moves the view not at all
        card = tab.locator(node).bounding_box()
        assert pane["x"] < card["x"] < pane["x"] + pane["width"], (pane, card)
        tab.mouse.click(card["x"] + 24, card["y"] + 10)
        tab.wait_for_timeout(800)
        assert same(viewport(tab), panned), (panned, viewport(tab))
        selected = tab.evaluate(
            "() => { const n = document.querySelector('.bl-view-host .react-flow__node.selected');"
            " return n ? n.getAttribute('data-id') : null; }"
        )
        assert selected is not None and selected.startswith("periods[1]/tenure"), selected

        # a second drag pans by 570 px more, its press moving the view not at all
        further = drag(570)
        assert abs(further["x"] - (panned["x"] - 570)) <= 3 and abs(further["y"] - panned["y"]) <= 3, (panned, further)

        # a focus given by script, as the keyboard gives it, reveals the selected card
        tab.evaluate("() => { if (document.activeElement) document.activeElement.blur(); }")
        tab.focus(".bl-view-host .bf-region")
        tab.wait_for_timeout(800)
        revealed = viewport(tab)
        assert not same(revealed, further), (further, revealed)
        focused = tab.evaluate(
            "() => { const n = document.activeElement && document.activeElement.closest('.react-flow__node');"
            " return n ? n.getAttribute('data-id') : null; }"
        )
        assert focused is not None and focused.startswith("periods[1]/tenure"), focused
        print(
            f"task 9: opened at x {opened['x']:.0f}, panned to {panned['x']:.0f}, the press and the click "
            f"left it there with {selected} selected, the second drag reached {further['x']:.0f}, and the "
            f"script's focus revealed {focused} at x {revealed['x']:.0f}"
        )
    finally:
        context.close()


# The Recipe tab as the page draws it (design pass 9 §§3 and 6; design pass
# 10 §4): the panel under the editor's data-panel, its strip's top and the
# file's name it prints, its view tabs' words; the column heads; the trellis
# row's select; each row's key;
# each select's value by its entry's address; each periods field's value and
# placeholder by its stage, null for a row at rest, which draws no field
# (design pass 11 §2); every control with its height and width, its
# opacity and visibility; each row's
# buttons by their names, each with the value of the select whose entry
# holds it, and each row's selects' values; every text the tab draws outside
# a control's value; and the add row's button's words.
RECIPE_TAB_JS = r"""
() => {
  const panel = document.querySelector('.bl-file .bl-classification');
  if (!panel) return null;
  const strip = panel.querySelector('.bl-inspector-strip');
  const box = (element) => element.getBoundingClientRect();
  const valueOf = (select) => {
    const chosen = select.querySelector('vscode-option[selected]');
    return chosen ? chosen.textContent.trim() : null;
  };
  const table = panel.querySelector('.bl-recipe-table');
  const texts = [];
  const walker = document.createTreeWalker(panel, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!node.textContent.trim()) continue;
    if (node.parentElement.closest('vscode-single-select, vscode-option, vscode-textfield')) continue;
    texts.push(node.textContent.trim());
  }
  return {
    panel: panel.dataset.panel,
    headTop: box(strip).top,
    context: strip.querySelector('.bl-inspector-file').textContent.trim(),
    tabs: Array.from(panel.querySelectorAll('.bl-class-tab'), (tab) => tab.textContent.trim()),
    heads: table ? Array.from(table.querySelectorAll('.bl-recipe-heads > span'),
                              (span) => span.textContent.trim()) : [],
    keys: table ? Array.from(table.querySelectorAll('.bl-recipe-row'),
                             (row) => row.dataset.stage) : [],
    values: table ? Object.fromEntries(Array.from(table.querySelectorAll('.bl-recipe-entry'),
      (entry) => [entry.dataset.address, valueOf(entry.querySelector('vscode-single-select'))])) : {},
    periods: table ? Object.fromEntries(Array.from(table.querySelectorAll('.bl-recipe-row'),
      (row) => {
        const field = row.querySelector('.bl-recipe-periods vscode-textfield');
        return [row.dataset.stage, field ? [field.value, field.placeholder] : null];
      })) : {},
    controls: table ? Array.from(table.querySelectorAll(
      'vscode-single-select, vscode-textfield, vscode-toolbar-button, .bl-text-button'),
      (control) => {
        const style = getComputedStyle(control);
        return [control.tagName.toLowerCase(), box(control).height, box(control).width,
                style.opacity, style.visibility];
      }) : [],
    buttons: table ? Object.fromEntries(Array.from(table.querySelectorAll('.bl-recipe-row'),
      (row) => [row.dataset.stage, Array.from(
        row.querySelectorAll('vscode-toolbar-button'),
        (button) => {
          const entry = button.closest('.bl-recipe-entry');
          return [button.label || button.textContent.trim(),
                  entry ? valueOf(entry.querySelector('vscode-single-select')) : null];
        })])) : {},
    selects: table ? Object.fromEntries(Array.from(table.querySelectorAll('.bl-recipe-row'),
      (row) => [row.dataset.stage,
                Array.from(row.querySelectorAll('vscode-single-select'), valueOf)])) : {},
    texts,
    add: table ? panel.querySelector('.bl-recipe-add .bl-text-button').textContent.trim() : null,
  };
}
"""
# The main bar's toggle Inspector, which took the rail's buttons Recipe and
# Types (unit N, Task 1; design pass 10 §3; N-D4), as window.vue and the
# page mark it: whether it is announced open (aria-expanded), whether it is
# disabled (aria-disabled) and its hover.
INSPECTOR_TOGGLE_JS = """
() => {
  const button = document.querySelector('.bl-main-bar .bl-fold[data-fold="inspector"]');
  return [button.getAttribute('aria-expanded'), button.getAttribute('aria-disabled'),
          button.title];
}
"""
# the address of tenure's first calibration entry in the durables recipe
TENURE_CALIBRATION = "stages.tenure.calibration.all[0]"
# The Recipe tab's selects and fields, each marked as an element, so that a
# field the page has drawn again reads as unmarked (Task 10, fix round 1);
# and the number of them that carry no mark.
MARK_FIELDS_JS = """
() => document.querySelectorAll(
  '.bl-recipe-table vscode-single-select, .bl-recipe-table vscode-textfield')
  .forEach((field) => { field.blKept = true; })
"""
UNMARKED_FIELDS_JS = """
() => Array.from(document.querySelectorAll(
  '.bl-recipe-table vscode-single-select, .bl-recipe-table vscode-textfield'))
  .filter((field) => !field.blKept).length
"""
# whether the list of the select of the entry at an address stands open,
# None where no such select stands
LIST_OPEN_JS = """
(address) => {
  const select = document.querySelector(
    `.bl-recipe-entry[data-address="${address}"] vscode-single-select`);
  return select ? select.open : null;
}
"""
# the address of bequest's first calibration entry in the durables recipe
BEQUEST_CALIBRATION = "stages.bequest.calibration.all[0]"
# keeper_cons's periods field on the Recipe tab of the durables model
KEEPER_PERIODS = '.bl-recipe-row[data-stage="keeper_cons"] .bl-recipe-periods vscode-textfield'
# a field's value and whether it holds the focus
VALUE_AND_FOCUS_JS = """
(selector) => {
  const field = document.querySelector(selector);
  return field ? [field.value, field.matches(":focus")] : null;
}
"""


def rest_text(tab, key: str, kind: str):
    """The first text of the cell `kind` of the stage `key`'s row of the
    Recipe tab while the row stands at rest, the entry as the table prints
    it (design pass 11 §2), None where the row draws no such text."""
    return tab.evaluate(
        """([key, kind]) => {
          const text = document.querySelector(
            `.bl-recipe-row[data-stage="${key}"] [data-kind="${kind}"] .bl-recipe-text`);
          return text ? text.textContent.trim() : null;
        }""",
        [key, kind],
    )


def recipe_select_value(tab, address: str):
    """The value the Recipe tab's select of the entry at `address` shows,
    its option marked selected, None where no such select stands."""
    return tab.evaluate(
        """(address) => {
          const select = document.querySelector(
            `.bl-recipe-entry[data-address="${address}"] vscode-single-select`);
          const chosen = select && select.querySelector('vscode-option[selected]');
          return chosen ? chosen.textContent.trim() : null;
        }""",
        address,
    )


def test_task_10_the_recipe_is_a_tab_of_the_panel_under_the_editor_whose_changes_undo_once(
    browser, server_on, scratch_durables
):
    """Task 10 (AAS, M-D17; design pass 9 §6), on a copy of the durables model
    at 1600 × 1000. Measure 1: opened on `declaration/spec.yml`, the panel
    under the editor stands on its Recipe tab, its strip at 656 px reading
    `spec.yml` beside one view tab `Recipe` (unit N, Task 2; design pass 10
    §4); with `keeper_cons.bl` open
    it stands on the four Types tabs and holds no recipe; with `trellis.yml`
    open no panel stands. Measure 2: the column heads, the trellis row's
    select, the rows in the file's order, each at rest (design pass 11 §2),
    and, each row opened in turn by a click and the others standing at
    rest, tenure's calibration selects, the periods fields and the add
    row's `Stage`. Measure 3: with the pointer away, each row opened in
    turn, every select, field and text button is 26 px high, an entry's
    actions among them, and every icon button 24 × 24, each at full opacity
    and visible; each row holds `Remove stage`, and the icon button `New
    file` stands beside each `$fill` (unit N, Task 2; N-D5). Measure 4: no
    text of the tab outside a control's value holds more than three words,
    at rest or with a row open. Measure 5: `wage_schedule` chosen for
    tenure's first calibration entry, tenure's row open, changes the
    editor's text in that entry alone, the file on disk unchanged, and the
    select reads it; one Command+Z returns the text and tenure's row, at
    rest, reads `durables`; `0–3` typed in keeper_cons's periods field,
    its row opened before the undo, while the undo's reading runs stays
    there, the field holding the focus, and every select and field of the
    tab is the element it was before the change (fix round 1); `0–1`
    typed in the bequest's periods, its row open, writes `periods: [0, 1]`,
    which one Command+Z returns to `[0, 0]`. Measure 6: no recipe region
    stands under the tree, and the main bar names keeper_cons's occurrence
    (unit N, Task 1). Measure 7: with `keeper_cons.bl` open, the main bar's
    toggle Inspector is open; a click on the recipe's document tab opens
    the recipe on its Recipe tab, Inspector still open; with `trellis.yml`
    open no panel stands and Inspector is disabled, its hover `Nothing to
    inspect in trellis.yml` (unit N, Task 1; design pass 10 §3). Measure 8
    (fix round 1): a click on tenure's first calibration select, its row
    open, opens its list, `wage_schedule` chosen there writes as measure
    5's choice does and one Command+Z returns the text; the list a click
    opens on bequest's first calibration select, its row opened before the
    undo, while the undo's reading runs stays open when the reading
    answers, every select and field the element it was, and Escape closes
    the list and leaves the row open."""
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
        tab.wait_for_timeout(500)
        drawn = tab.evaluate(RECIPE_TAB_JS)

        # measure 1: the tab, under the editor, for the recipe
        named = (drawn["panel"], drawn["context"])
        assert named == ("recipe", "spec.yml"), named
        assert abs(drawn["headTop"] - 656) <= 1, drawn["headTop"]
        assert drawn["tabs"] == ["Recipe"]

        # measure 2: the table, every row at rest, then each row open in
        # turn, the others at rest (design pass 11 §2)
        assert drawn["heads"] == ["Stage", "Calibration", "Settings", "Methods", "Periods"]
        assert drawn["keys"] == ["tenure", "keeper_cons", "adjuster_cons", "bequest"]
        assert drawn["values"] == {"trellis": "trellis.yml"}
        assert set(drawn["periods"].values()) == {None}
        opened = with_each_recipe_row_open(tab, lambda tab: tab.evaluate(RECIPE_TAB_JS))
        values = {
            address: value
            for found in opened.values()
            for address, value in found["values"].items()
        }
        assert values["trellis"] == "trellis.yml"
        assert (values[TENURE_CALIBRATION], values["stages.tenure.calibration.all[1]"]) == (
            "durables",
            "$fill",
        )
        assert values["stages.tenure.stage"] == "tenure.bl"
        assert values["stages.tenure.methods.all[0]"] == "methods.bl"
        assert {key: found["periods"][key] for key, found in opened.items()} == {
            "tenure": ["", "All"],
            "keeper_cons": ["", "All"],
            "adjuster_cons": ["", "All"],
            "bequest": ["0–0", "All"],
        }
        assert drawn["add"] == "Stage"

        # measure 3: every control drawn, at rest and with each row open, an
        # entry's actions among them (fix round 1)
        controls = drawn["controls"] + [
            control for found in opened.values() for control in found["controls"]
        ]
        for tag, height, width, opacity, visibility in controls:
            if tag == "vscode-toolbar-button":
                assert (height, width) == (24, 24), (tag, height, width)
            else:
                assert abs(height - 26) <= 0.5, (tag, height)
            assert (opacity, visibility) == ("1", "visible"), (tag, opacity, visibility)
        for key, found in opened.items():
            buttons = found["buttons"][key]
            assert ["Remove stage", None] in buttons, (key, buttons)
            fills = [value for name, value in buttons if name == "New file"]
            assert fills and set(fills) == {"$fill"}, (key, buttons)
            assert [name for name, _ in buttons if name == "Replace"] == [], (key, buttons)

        # measure 4: labels of a word or a few
        texts = drawn["texts"] + [text for found in opened.values() for text in found["texts"]]
        assert [text for text in texts if len(text.split()) > 3] == [], texts

        # measure 5: one change of the buffer, one undo; a text typed in
        # keeper_cons's periods field while the undo's reading runs stays,
        # and the tab's selects and fields are the elements they were before
        # the change (fix round 1), keeper_cons's row opened before the undo
        # and the editor given the focus without a click, which would close
        # the row (design pass 11 §2); tenure's row, at rest, reads
        # `durables` again only once that reading has answered
        open_recipe_row(tab, "tenure")
        entry = f'.bl-recipe-entry[data-address="{TENURE_CALIBRATION}"]'
        choose_option(tab, entry, "wage_schedule")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == chosen_text, 30.0, "wage_schedule written")
        wait_until(
            lambda: recipe_select_value(tab, TENURE_CALIBRATION) == "wage_schedule",
            60.0,
            "the select reading wage_schedule",
        )
        assert recipe_file.read_text(encoding="utf-8") == recipe_text
        open_recipe_row(tab, "keeper_cons")
        wait_until(
            lambda: rest_text(tab, "tenure", "calibration") == "wage_schedule",
            60.0,
            "tenure's row reading wage_schedule",
        )
        tab.evaluate(MARK_FIELDS_JS)
        tab.focus(".cm-content")
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == recipe_text, 10.0, "the choice undone")
        tab.locator(KEEPER_PERIODS).click()
        tab.keyboard.type("0–3")
        wait_until(
            lambda: rest_text(tab, "tenure", "calibration") == "durables",
            60.0,
            "tenure's row reading durables again",
        )
        assert tab.evaluate(VALUE_AND_FOCUS_JS, KEEPER_PERIODS) == ["0–3", True]
        assert tab.evaluate(UNMARKED_FIELDS_JS) == 0
        tab.keyboard.press("ControlOrMeta+a")
        tab.keyboard.press("Backspace")
        open_recipe_row(tab, "bequest")
        field = '.bl-recipe-row[data-stage="bequest"] .bl-recipe-periods vscode-textfield'
        tab.locator(field).click()
        tab.keyboard.press("ControlOrMeta+a")
        tab.keyboard.type("0–1")
        tab.keyboard.press("Enter")
        widened = recipe_text.replace("periods: [0, 0]}", "periods: [0, 1]}")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == widened, 30.0, "periods: [0, 1] written")
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == recipe_text, 10.0, "the periods undone")
        assert recipe_file.read_text(encoding="utf-8") == recipe_text

        # measure 8: a click opens the select's list, a choice there
        # writes as measure 5's choice does, and a list opened while the
        # undo's reading runs stays open when that reading answers (fix
        # round 1); Escape then closes the list and leaves its row open
        open_recipe_row(tab, "tenure")
        tab.click(f"{entry} vscode-single-select")
        wait_until(
            lambda: tab.evaluate(LIST_OPEN_JS, TENURE_CALIBRATION) is True, 10.0, "the list open"
        )
        tab.get_by_role("option", name="wage_schedule", exact=True).click()
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == chosen_text, 30.0, "chosen in the list")
        wait_until(
            lambda: recipe_select_value(tab, TENURE_CALIBRATION) == "wage_schedule",
            60.0,
            "the select reading wage_schedule after the list's choice",
        )
        open_recipe_row(tab, "bequest")
        wait_until(
            lambda: rest_text(tab, "tenure", "calibration") == "wage_schedule",
            60.0,
            "tenure's row reading wage_schedule after the list's choice",
        )
        tab.evaluate(MARK_FIELDS_JS)
        tab.focus(".cm-content")
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == recipe_text, 10.0, "the list's choice undone"
        )
        tab.click(f'.bl-recipe-entry[data-address="{BEQUEST_CALIBRATION}"] vscode-single-select')
        wait_until(
            lambda: tab.evaluate(LIST_OPEN_JS, BEQUEST_CALIBRATION) is True,
            10.0,
            "bequest's list open",
        )
        wait_until(
            lambda: rest_text(tab, "tenure", "calibration") == "durables",
            60.0,
            "tenure's row reading durables after the list's undo",
        )
        assert tab.evaluate(LIST_OPEN_JS, BEQUEST_CALIBRATION) is True
        assert tab.evaluate(UNMARKED_FIELDS_JS) == 0
        tab.keyboard.press("Escape")
        wait_until(
            lambda: tab.evaluate(LIST_OPEN_JS, BEQUEST_CALIBRATION) is False,
            10.0,
            "bequest's list closed",
        )
        rows = recipe_rows_at_rest(tab)
        assert [key for key, row in rows.items() if row["expanded"]] == ["bequest"], rows
        assert recipe_file.read_text(encoding="utf-8") == recipe_text

        # measures 6 and 7: the region gone, the occurrence in the main bar
        # and the toggle Inspector
        for selector in (".bl-recipe", ".bl-recipe-block", ".bl-recipe-context"):
            assert tab.locator(selector).count() == 0, selector
        opened = ["true", None, "Inspector"]
        wait_until(lambda: tab.evaluate(INSPECTOR_TOGGLE_JS) == opened, 10.0, "Inspector open")
        open_file(tab, url, KEEPER_CONS)
        types = '.bl-classification[data-panel="types"] .bl-class-row'
        tab.wait_for_selector(types, timeout=60_000)
        assert tab.locator(".bl-recipe-table").count() == 0
        tabs = tab.evaluate(RECIPE_TAB_JS)["tabs"]
        assert tabs == ["Fields", "Parameters", "Settings", "Methods"], tabs
        wait_until(lambda: recipe_head(tab).endswith("/ keeper_cons"), 30.0, "the occurrence")
        assert tab.evaluate(INSPECTOR_TOGGLE_JS) == opened
        tab.click(f'.bl-tab[data-path="{RECIPE_FILE}"]')
        tab.wait_for_selector(
            f'.bl-tab.bl-active[data-path="{RECIPE_FILE}"]', timeout=30_000
        )
        tab.wait_for_selector(".bl-recipe-table .bl-recipe-row", timeout=30_000)
        assert tab.evaluate(INSPECTOR_TOGGLE_JS) == opened
        trellis_file = "declaration/trellis.yml"
        tab.click(f'.bl-tree-file[data-path="{trellis_file}"]')
        tab.wait_for_selector(f'.bl-tab.bl-active[data-path="{trellis_file}"]', timeout=30_000)
        wait_until(
            lambda: tab.locator(".bl-file .bl-classification").count() == 0, 30.0, "no panel"
        )
        disabled = ["false", "true", "Nothing to inspect in trellis.yml"]
        wait_until(
            lambda: tab.evaluate(INSPECTOR_TOGGLE_JS) == disabled, 10.0, "Inspector disabled"
        )
        print(f"task 10: {len(drawn['controls'])} controls, texts {sorted(set(drawn['texts']))}")
    finally:
        context.close()


# The face each glyph of the main bar's toggles is typeset in, by its
# toggle's fold (AAS, M-D18; design pass 10 §3; N-D10): the brackets and Υ
# in STIX Two Math.
GLYPH_FACES = {
    "details": "STIX Two Math",
    "matsya": "STIX Two Math",
}
# The page's own declaration of STIX Two Math in brand.css, which the page
# carries whole (`solara.Style`), so that the font applies on the whole page
# and not only in the graph's drawing.
STIX_FACE = re.compile(
    r'@font-face\s*\{\s*font-family:\s*"STIX Two Math";\s*'
    r'src:\s*url\("static/assets/flow/stix-two-math-latin-400-normal\.woff2"\)'
)
# The main bar's toggles' icons as the page draws them (AAS, M-D18; design
# pass 10 §3): every SVG, path, image, object or `use` element under the
# toggles; and for each toggle its fold, its icon's tag, aria-hidden and
# box, the icon's children
# that are neither a Codicon nor a glyph, every image or mask the button or
# an element under it draws by CSS, its own or its ::before's or ::after's,
# the icon's color, each Codicon as its name, face, size, color and whether
# its glyph is drawn, and each glyph as its data-glyph, the content of its
# ::before, its own text and its color; and the states of the page's faces
# of STIX Two Math.
TOGGLE_PARTS_JS = r"""
() => {
  const bar = document.querySelector('.bl-main-bar');
  const box = (element) => {
    const rect = element.getBoundingClientRect();
    return [rect.width, rect.height];
  };
  const drawn = (style) => !['none', 'normal', '""'].includes(style.content);
  const buttons = Array.from(bar.querySelectorAll('.bl-toggle'), (button) => {
    const icon = button.querySelector(':scope > .bl-toggle-icon');
    const parts = Array.from(icon.children);
    const codicons = parts.filter((part) => part.matches('i.codicon'));
    const glyphs = parts.filter((part) => part.matches('.bl-toggle-glyph'));
    const images = [button, ...button.querySelectorAll('*')].flatMap((element) =>
      [null, '::before', '::after'].flatMap((pseudo) => {
        const style = getComputedStyle(element, pseudo);
        return [style.backgroundImage, style.maskImage, style.webkitMaskImage];
      })).filter((value) => value && value !== 'none');
    return {
      fold: button.dataset.fold,
      icon: [icon.tagName.toLowerCase(), icon.getAttribute('aria-hidden'), box(icon)],
      others: parts.filter((part) => !codicons.includes(part) && !glyphs.includes(part))
        .map((part) => part.outerHTML.slice(0, 80)),
      images,
      color: getComputedStyle(icon).color,
      codicons: codicons.map((part) => ({
        name: Array.from(part.classList).find((name) => name.startsWith('codicon-')),
        face: getComputedStyle(part).fontFamily,
        size: getComputedStyle(part).fontSize,
        color: getComputedStyle(part).color,
        drawn: drawn(getComputedStyle(part, '::before')),
      })),
      glyphs: glyphs.map((part) => ({
        glyph: part.dataset.glyph,
        content: getComputedStyle(part, '::before').content,
        text: part.textContent,
        color: getComputedStyle(part).color,
      })),
    };
  });
  return {
    drawings: Array.from(
      bar.querySelectorAll('.bl-toggle :is(svg, path, img, object, use)'),
      (element) => element.outerHTML.slice(0, 80)),
    buttons,
    stix: Array.from(document.fonts)
      .filter((face) => face.family.replace(/"/g, '') === 'STIX Two Math')
      .map((face) => face.status),
  };
}
"""


def glyph_fonts(context, tab) -> dict[str, list]:
    """The fonts the browser draws each glyph of the main bar's toggles in,
    by its toggle's fold: each font as its family, whether it is a font the
    page loaded and the number of glyphs drawn in it, read from the glyph's
    ::before by the DevTools protocol's `CSS.getPlatformFontsForNode`."""
    session = context.new_cdp_session(tab)
    try:
        session.send("DOM.enable")
        session.send("CSS.enable")
        root = session.send("DOM.getDocument", {"depth": -1})["root"]
        nodes, stack = {}, [root]
        while stack:
            node = stack.pop()
            nodes[node["nodeId"]] = node
            stack.extend(node.get("children", []) + node.get("pseudoElements", []))
        fonts = {}
        for fold in TOGGLE_ICONS:
            selector = f'.bl-main-bar .bl-fold[data-fold="{fold}"] .bl-toggle-glyph'
            found = session.send(
                "DOM.querySelector", {"nodeId": root["nodeId"], "selector": selector}
            )
            if not found["nodeId"]:
                continue
            pseudos = nodes[found["nodeId"]].get("pseudoElements", [])
            (before,) = [pseudo for pseudo in pseudos if pseudo["pseudoType"] == "before"]
            answered = session.send("CSS.getPlatformFontsForNode", {"nodeId": before["nodeId"]})
            fonts[fold] = [
                [font["familyName"], font["isCustomFont"], font["glyphCount"]]
                for font in answered["fonts"]
            ]
        return fonts
    finally:
        session.detach()


def test_task_11_the_toggles_icons_are_codicons_and_glyphs_typeset_in_the_pages_fonts(
    browser, server_on, durables_folder
):
    """Task 11 (AAS, M-D18; design pass 8 §3a as M-D18 amends it), its
    icons moved from the rail to the main bar's toggles by unit N's Task 1
    (design pass 10 §3; N-D10): on the durables model at 1600 × 1000, in
    the trellis view of `declaration/spec.yml`, no toggle of the main bar
    holds an SVG, a path, an image, an object or a `use` element, and none
    draws an image or a mask by CSS; the package's public/rail/ is gone.
    Each toggle's icon is a span of 16 × 16 px hidden from assistive
    technology, holding the Codicon and the glyph of TOGGLE_ICONS and
    nothing else: each Codicon drawn by the Codicons font at 16 px; each
    glyph the content of its ::before, its data-glyph, and no text of its
    own, typeset by the browser in one of the page's own fonts, STIX Two
    Math for ⟦·⟧ and Υ. brand.css, which the page carries whole, declares
    STIX Two Math by an @font-face, and the page has loaded that face.
    Every part draws in its icon's color, so that the open panel's mark
    reaches it: Details folded turns its brackets from ink-1 to ink-2."""
    brand = (ROOT / "packages/bellman-workbench/bellman_workbench/brand.css").read_text(
        encoding="utf-8"
    )
    assert STIX_FACE.search(brand), "brand.css declares no @font-face of STIX Two Math"
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        tab.mouse.move(1200, 500)
        tab.evaluate("document.fonts.ready.then(() => true)")
        drawn = tab.evaluate(TOGGLE_PARTS_JS)
        fonts = glyph_fonts(context, tab)
        details = '.bl-main-bar .bl-fold[data-fold="details"]'
        opened = tab.evaluate(
            "(selector) => getComputedStyle(document.querySelector(selector + ' .bl-toggle-icon'))"
            ".color",
            details,
        )
        tab.click(details)
        wait_until(
            lambda: tab.get_attribute(details, "aria-expanded") == "false", 5.0, "details folded"
        )
        tab.mouse.move(1200, 500)
        folded = tab.evaluate(TOGGLE_PARTS_JS)["buttons"]
        tab.click(details)
        wait_until(
            lambda: tab.get_attribute(details, "aria-expanded") == "true", 5.0, "details opened"
        )
        ink_2 = tab.evaluate(
            "() => { const probe = document.createElement('span');"
            " probe.style.color = 'var(--bl-ink-2)'; document.body.append(probe);"
            " const color = getComputedStyle(probe).color; probe.remove(); return color; }"
        )
    finally:
        context.close()

    # no drawing of the project's own: no SVG, path or image, no CSS image
    assert drawn["drawings"] == [], drawn["drawings"]
    assert not (PUBLIC / "rail").exists()
    buttons = drawn["buttons"]
    assert [button["fold"] for button in buttons] == list(TOGGLE_ICONS)
    for button in buttons:
        fold = button["fold"]
        codicon, glyph = TOGGLE_ICONS[fold]
        assert button["images"] == [], (fold, button["images"])
        assert button["icon"] == ["span", "true", [16, 16]], (fold, button["icon"])
        assert button["others"] == [], (fold, button["others"])
        # the Codicon, drawn by its font at 16 px
        assert [part["name"] for part in button["codicons"]] == (
            [f"codicon-{codicon}"] if codicon else []
        ), fold
        for part in button["codicons"]:
            assert (part["face"], part["size"], part["drawn"]) == ("codicon", "16px", True), (
                fold,
                part,
            )
            assert part["color"] == button["color"], (fold, part)
        # the glyph, typeset by the browser in the page's own font
        assert [part["glyph"] for part in button["glyphs"]] == ([glyph] if glyph else []), fold
        for part in button["glyphs"]:
            assert part["content"] == f'"{glyph}"', (fold, part)
            assert part["text"] == "", (fold, part)
            assert part["color"] == button["color"], (fold, part)
        if glyph:
            assert len(fonts[fold]) == 1, (fold, fonts[fold])
            ((family, custom, count),) = fonts[fold]
            assert family.startswith(GLYPH_FACES[fold]) and custom, (fold, fonts[fold])
            assert count == len(glyph), (fold, fonts[fold])
    assert "loaded" in drawn["stix"], drawn["stix"]

    # the state of the panel reaches the glyph: Details in ink-1 while open,
    # in ink-2 while folded
    (details_folded,) = [button for button in folded if button["fold"] == "details"]
    (details_open,) = [button for button in buttons if button["fold"] == "details"]
    assert details_open["glyphs"][0]["color"] == opened != ink_2
    assert details_folded["glyphs"][0]["color"] == details_folded["color"] == ink_2
    print(f"task 11: the glyphs' fonts {fonts}")
