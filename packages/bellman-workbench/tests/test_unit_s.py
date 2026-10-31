"""The tests of unit S, design pass 14 (AAS, 21 October 2026: "in the backward builder, there are still multiple
wires across a single branch?"; "yes this needs to be updated at the stage level too, lets get everything
consistent!"; "make the vertical view default; moreover once a view is selected it should stay that way even if we
switch stages or views"; "also some text overlaps boxes"), the development repository's record of design pass 14, one line per
bundle, §6, the graph's items: the stage graph's lines
(§1, whose bundling AMD-MB-001 §5.4 retired with the marginal wires: a value is one wire, and the test of the ten
bundles is deleted), the vertical layout by default and the direction kept (§2) and the markers laid out
downward (§3); and, from the controller's sections, no `:result` on the page (§4), Matsya's composer a
centered text field (§5), the trellis's Initial view (§7) and the Recipe's add glyph (§8). Every test reads the page's elements, never a screenshot's pixels, on a copy of the durables model,
its stage file `tenure.bl` and its trellis at periods 0 to 2, the restriction the trellis of 51 periods opens
with."""

from __future__ import annotations

from workbench_support import (
    LAYOUT_KEY,
    MATSYA_TOGGLE,
    RECIPE_FILE,
    TWO_FRAMES_JS,
    VIEW_STATE_JS,
    bound_as_the_recipe_binds,
    choose_view,
    flow_handle,
    graph_named,
    layout_button,
    new_tab,
    open_file,
    open_trellis,
    property_color,
    record_layouts,
    restriction_shown,
    select_node,
    status_text,
    view_still,
    viewport,
    wait_until,
)

from bellman_workbench import model

# the stage file whose graphs the tests read
TENURE_FILE = "declaration/stages/tenure/tenure.bl"
# the hover of the foot's layout button in each direction of the page (design pass 14 §2, rule 1)
TO_THE_RIGHT, DOWNWARD = "Lay out from left to right", "Lay out from top to bottom"
# the labels of the two `outside` markers of the trellis at periods 0 to 2, the occurrences of periods[3] that
# tenure of periods[2] writes
OUTSIDE_LABELS = {"periods[3]/keeper_cons", "periods[3]/adjuster_cons"}

# The lines the region draws, in the flow's units at the view's scale: each edge's writer and reader, the nodes
# its two handles stand on, and their ports; its count's text and whether the count is drawn; its slash's stroke
# and the distance of the slash's middle from the plug's center; its title; whether its path is lit and whether
# it ends in an arrowhead; and whether a click selects it.
LINES_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host');
  const flow = host.querySelector('.react-flow');
  const pane = flow.getBoundingClientRect();
  const view = new DOMMatrixReadOnly(getComputedStyle(flow.querySelector('.react-flow__viewport')).transform);
  const zoom = view.a;
  const toFlow = (x, y) => ({x: (x - pane.left - view.e) / zoom, y: (y - pane.top - view.f) / zoom});
  const center = (element) => { const r = element.getBoundingClientRect(); return toFlow((r.left + r.right) / 2, (r.top + r.bottom) / 2); };
  const handles = {};
  for (const h of host.querySelectorAll('.react-flow__handle')) handles[h.dataset.handleid] = h;
  return Array.from(host.querySelectorAll('.react-flow__edge'), (edge) => {
    const [sp, tp] = (edge.dataset.id || '').split('>>');
    const s = handles[sp], t = handles[tp];
    const path = edge.querySelector('.react-flow__edge-path'), count = edge.querySelector('.bf-cable-count');
    const bus = edge.querySelector('.bf-cable-bus'), title = edge.querySelector('title');
    let slash = null;
    if (bus && s) {
      const [a, b] = (bus.getAttribute('d') || '').slice(1).split('L').map((p) => p.split(',').map(Number));
      const middle = {x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2}, plug = center(s);
      slash = {stroke: getComputedStyle(bus).stroke, fromPlug: Math.hypot(middle.x - plug.x, middle.y - plug.y)};
    }
    return {
      id: edge.dataset.id,
      source: s ? s.closest('.react-flow__node').dataset.id : null, out: sp.split('::out::')[1],
      target: t ? t.closest('.react-flow__node').dataset.id : null, into: tp.split('::in::')[1],
      count: count ? count.textContent : null, countShown: count ? getComputedStyle(count).display !== 'none' : false,
      countFill: count ? getComputedStyle(count).fill : null, slash, title: title ? title.textContent : null,
      lit: !!path && path.classList.contains('bf-lit'), arrow: !!edge.querySelector('.bf-arrow'),
      selectable: edge.classList.contains('selectable') || edge.classList.contains('bf-pair-bundle'),
    };
  });
}
"""

# The ports of a box of the stage graph, by its node id: each handle's side, its port, its hover, whether it is lit
# and its fill as the browser draws it.
PORTS_JS = r"""
(nodeId) => {
  const node = document.querySelector(`.bl-view-host .react-flow__node[data-id="${CSS.escape(nodeId)}"]`);
  if (!node) return null;
  return Array.from(node.querySelectorAll('.react-flow__handle'), (h) => ({
    side: h.classList.contains('source') ? 'writing' : 'reading', handle: h.dataset.handleid,
    port: (h.dataset.handleid || '').split(/::(?:out|in)::/)[1], title: h.getAttribute('title'),
    lit: h.classList.contains('bf-lit'), fill: getComputedStyle(h).backgroundColor}));
}
"""

# The period frames the region draws, each with its place in the flow's units; the box of every boundary marker's
# label and of every card on the screen; the pairs of labels that meet and the labels that meet a card; and, for
# the two `outside` markers where both are drawn, their marks' centers on the screen.
TRELLIS_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host');
  const place = (n) => { const f = /translate\(\s*(-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform); return f ? {x: Number(f[1]), y: Number(f[2])} : null; };
  const frames = Array.from(host.querySelectorAll('.react-flow__node'))
    .filter((n) => n.querySelector(':scope > .bf-layer.bf-period')).map((n) => ({id: n.dataset.id, at: place(n)}));
  const box = (e) => { const r = e.getBoundingClientRect(); return {left: r.left, right: r.right, top: r.top, bottom: r.bottom}; };
  const labels = Array.from(host.querySelectorAll('.bf-marker > .bf-boundary-label'), (l) => ({text: l.textContent, box: box(l)}));
  const cards = Array.from(host.querySelectorAll('.react-flow__node > .bf-card'), (c) => ({id: c.parentElement.dataset.id, box: box(c)}));
  const meets = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  const labelsMeeting = [], cardsMet = [];
  labels.forEach((l, i) => {
    labels.slice(i + 1).forEach((o) => { if (meets(l.box, o.box)) labelsMeeting.push([l.text, o.text]); });
    cards.forEach((c) => { if (meets(l.box, c.box)) cardsMet.push([l.text, c.id]); });
  });
  const outside = Array.from(host.querySelectorAll('.bf-marker[data-kind="outside"]'), (m) => {
    const r = m.getBoundingClientRect(), label = m.querySelector('.bf-boundary-label');
    return {target: m.dataset.target, x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2, labelWidth: label ? label.getBoundingClientRect().width : 0};
  });
  return {frames, labels: labels.map((l) => l.text), labelsMeeting, cardsMet, outside};
}
"""
# the page's layout direction as the browser's storage keeps it, null where it keeps none (design pass 14 §2)
STORED_JS = "() => { try { return window.localStorage.getItem(%s); } catch (error) { return 'refused'; } }" % repr(LAYOUT_KEY)
# the place of each box of the stage graph, by its node id
PLACES_JS = r"""
() => Object.fromEntries(Array.from(document.querySelectorAll('.bl-view-host .react-flow__node'), (n) => {
  const f = /translate\(\s*(-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform);
  return [n.dataset.id, f ? [Number(f[1]), Number(f[2])] : null];
}))
"""


def at_scale_one(tab) -> None:
    """Sets the view's scale to 1 where it stands, as the graph's handle sets a view (R-D29), and waits for two
    frames at that scale."""
    view = viewport(tab)
    flow_handle(tab, "setView", {"viewport": {"x": view["x"], "y": view["y"], "zoom": 1.0}, "selection": None})
    wait_until(lambda: abs(viewport(tab)["zoom"] - 1.0) <= 1e-6, 5.0, "the view at scale 1")
    tab.evaluate(TWO_FRAMES_JS)


def lines_drawn(tab) -> int:
    """The number of edges the region draws."""
    return tab.evaluate("() => document.querySelectorAll('.bl-view-host .react-flow__edge').length")


def open_tenure(tab, url: str) -> None:
    """Opens tenure.bl from the tree and waits for its backward graph's lines at scale 1."""
    open_file(tab, url, TENURE_FILE)
    wait_until(lambda: lines_drawn(tab) > 0, 60.0, "the backward graph's lines")
    tab.wait_for_timeout(500)
    at_scale_one(tab)


def stored_layout(tab):
    """The direction the browser's storage keeps under LAYOUT_KEY, None where it keeps none."""
    return tab.evaluate(STORED_JS)


def one_edge(frames: list, axis: str) -> bool:
    """Whether every period frame of `frames` (TRELLIS_JS) shares one place on `axis`, `x` for one left edge, laid
    out downward, and `y` for one top edge, laid out to the right, within 0.01 px."""
    places = [f["at"][axis] for f in frames]
    return len(frames) == 3 and max(places) - min(places) <= 0.01


def trellis_at_rest(tab, direction: str) -> None:
    """Chooses the trellis graph `direction`, waits until it is laid out and at rest, and sets the scale to 1."""
    choose_view(tab, None, direction)
    wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the {direction} graph")
    wait_until(lambda: view_still(tab), 30.0, f"the {direction} graph at rest")
    at_scale_one(tab)


def test_the_forward_graph_of_tenure_keeps_two_measure_lines_into_outputs(browser, server_on, durables_folder):
    """Design pass 14 §1, rule 1 (S-D2). The forward graph of `tenure.bl` draws its five measure wires as five
    lines with no count: the two measures `μ_keep≻` and `μ_adjust≻` from the pushforward into `Outputs` stay two
    lines at two ports, as the forward trellis draws one cable per route."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_tenure(tab, url)
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph")
        wait_until(lambda: view_still(tab), 30.0, "the forward graph at rest")
        lines = tab.evaluate(LINES_JS)
        assert len(lines) == 5 and not any(line["count"] or line["slash"] for line in lines), lines
        into = sorted((line["source"], line["out"], line["into"]) for line in lines if line["target"] == "GraphOutputs")
        assert into == [
            ("dcsn_to_cntn:Pushforward", "tenure:measure:cntn:adjust", "tenure:measure:cntn:adjust"),
            ("dcsn_to_cntn:Pushforward", "tenure:measure:cntn:keep", "tenure:measure:cntn:keep"),
        ], into
        assert [(p["side"], p["port"]) for p in tab.evaluate(PORTS_JS, "GraphOutputs")] == [
            ("reading", "tenure:measure:cntn:keep"), ("reading", "tenure:measure:cntn:adjust")
        ]
    finally:
        context.close()


def test_the_page_opens_laid_out_downward_and_keeps_a_turn_across_graphs_and_tabs(
    browser, server_on, durables_folder
):
    """Design pass 14 §2 (S-D5, S-D6). The page opens its trellis laid out from top to bottom, the three period
    frames on one left edge, the foot's button offering `Lay out from left to right` and the browser's storage
    holding nothing under `bellman-workbench layout`. A click turns every graph to the right: the frames stand on
    one top edge, the button offers `Lay out from top to bottom`, the storage holds `horizontal`, and the direction
    is kept while `tenure.bl` is opened, whose graph then runs from left to right, and when the trellis is opened
    again, and in a new tab of the same browser context. Turning back lays the frames on one left edge again and
    removes the stored value."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        record_layouts(tab)
        tab.wait_for_timeout(500)
        found = tab.evaluate(TRELLIS_JS)
        assert one_edge(found["frames"], "x") and not one_edge(found["frames"], "y"), found["frames"]
        assert layout_button(tab) == "horizontal" and tab.get_attribute(".bl-layout-button", "title") == TO_THE_RIGHT
        assert stored_layout(tab) is None
        # the turn
        tab.click(".bl-layout-button")
        wait_until(lambda: layout_button(tab) == "vertical", 10.0, "the button reads vertical")
        wait_until(lambda: view_still(tab), 60.0, "the trellis laid out to the right")
        found = tab.evaluate(TRELLIS_JS)
        assert one_edge(found["frames"], "y") and not one_edge(found["frames"], "x"), found["frames"]
        assert tab.get_attribute(".bl-layout-button", "title") == DOWNWARD
        assert stored_layout(tab) == "horizontal"
        # the stage opened after the turn is laid out to the right too
        open_tenure(tab, url)
        assert layout_button(tab) == "vertical"
        places = tab.evaluate(PLACES_JS)
        assert places["GraphInputs"][0] < places["GraphOutputs"][0], places
        assert abs(places["GraphInputs"][1] - places["GraphOutputs"][1]) < abs(places["GraphInputs"][0] - places["GraphOutputs"][0]), places
        # the trellis opened again, a reload of the page, keeps the direction
        open_trellis(tab, url, RECIPE_FILE)
        record_layouts(tab)
        tab.wait_for_timeout(500)
        found = tab.evaluate(TRELLIS_JS)
        assert one_edge(found["frames"], "y"), found["frames"]
        assert layout_button(tab) == "vertical" and stored_layout(tab) == "horizontal"
        # a new tab of the same browser context opens in the kept direction
        other = context.new_page()
        other.on("pageerror", lambda error: print(f"page error: {error}"))
        open_trellis(other, url, RECIPE_FILE)
        record_layouts(other)
        other.wait_for_timeout(500)
        found = other.evaluate(TRELLIS_JS)
        assert one_edge(found["frames"], "y"), found["frames"]
        assert layout_button(other) == "vertical" and stored_layout(other) == "horizontal"
        # turning back removes the stored value
        other.click(".bl-layout-button")
        wait_until(lambda: layout_button(other) == "horizontal", 10.0, "the button reads horizontal")
        wait_until(lambda: view_still(other), 60.0, "the trellis laid out downward again")
        found = other.evaluate(TRELLIS_JS)
        assert one_edge(found["frames"], "x"), found["frames"]
        assert other.get_attribute(".bl-layout-button", "title") == TO_THE_RIGHT
        assert stored_layout(other) is None
        print("unit S: the trellis opens downward; the turn is kept across the stage, the trellis and a new tab, and turning back stores nothing")
    finally:
        context.close()


def test_no_marker_label_meets_another_label_or_a_card_laid_out_downward(browser, server_on, durables_folder):
    """Design pass 14 §3 (S-D7). In each trellis graph of the durables model at periods 0 to 2, laid out downward
    at scale 1, no boundary marker's label meets another marker's label or a card; in the backward graph the two
    `outside` markers of periods[3] stand with their marks' centers at least their widest label plus 8 px apart."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        record_layouts(tab)
        for direction in ("forward", "backward"):
            trellis_at_rest(tab, direction)
            found = tab.evaluate(TRELLIS_JS)
            assert one_edge(found["frames"], "x"), (direction, found["frames"])
            assert found["labels"] and not found["labelsMeeting"] and not found["cardsMet"], (direction, found)
            assert set(found["labels"]) >= OUTSIDE_LABELS, (direction, found["labels"])
            if direction == "backward":
                outside = {m["target"]: m for m in found["outside"]}
                assert set(outside) == OUTSIDE_LABELS, outside
                keeper, adjuster = outside["periods[3]/keeper_cons"], outside["periods[3]/adjuster_cons"]
                widest = max(keeper["labelWidth"], adjuster["labelWidth"])
                assert abs(keeper["x"] - adjuster["x"]) >= widest + 8 - 0.5, (keeper, adjuster)
                assert abs(keeper["y"] - adjuster["y"]) <= 0.5, (keeper, adjuster)
            print(f"unit S: the {direction} graph's {len(found['labels'])} marker labels meet no label and no card")
    finally:
        context.close()

# --- the controller's tests of design pass 14 §§4, 5, 7, 8 and 10 ---

# The hovers, titles and texts of the page that hold the mark `:result`
# (design pass 14 §4), and a sample of the expectation's port hovers.
RESULT_JS = r"""
() => {
  const found = [];
  for (const element of document.querySelectorAll('[title]')) {
    const text = element.getAttribute('title') || '';
    if (text.includes(':result')) found.push(text.slice(0, 120));
  }
  for (const element of document.querySelectorAll('title')) {
    const text = element.textContent || '';
    if (text.includes(':result')) found.push(text.slice(0, 120));
  }
  const texts = Array.from(document.querySelectorAll('.bl-window *'))
    .filter((element) => element.children.length === 0 && (element.textContent || '').includes(':result'))
    .map((element) => element.textContent.trim().slice(0, 120));
  const sample = Array.from(document.querySelectorAll('.react-flow__handle[title]'))
    .map((handle) => handle.getAttribute('title'))
    .filter((text) => text.includes('Expectation'));
  return { found, texts, sample };
}
"""

# The composer of Matsya's column (design pass 14 §5; amendment 07 of spec
# 0.4, §2 item 2): the control's tag, its placeholder and spoken name, its
# box, its inner element's box, the top of the line's band, the inner
# element's top with its border and padding, and the line's height, and
# the box of the icon button `Ask`.
COMPOSER_JS = r"""
() => {
  const R = (element) => {
    const r = element.getBoundingClientRect();
    return { left: r.left, top: r.top, width: r.width, height: r.height };
  };
  const host = document.querySelector('.bl-matsya-field vscode-textarea');
  if (!host) return null;
  const input = host.shadowRoot && host.shadowRoot.querySelector('textarea');
  const style = input ? getComputedStyle(input) : null;
  const ask = document.querySelector('.bl-matsya-ask');
  const foot = document.querySelector('.bl-matsya-foot');
  const box = document.querySelector('.bl-matsya-row');
  return {
    tag: host.tagName.toLowerCase(),
    placeholder: host.getAttribute('placeholder'),
    name: host.getAttribute('aria-label'),
    host: R(host),
    input: input ? R(input) : null,
    band: input ? R(input).top + parseFloat(style.borderTopWidth) + parseFloat(style.paddingTop) : null,
    line: style ? parseFloat(style.lineHeight) : null,
    ask: ask ? R(ask) : null,
    foot: foot ? R(foot) : null,
    box: box ? R(box) : null,
  };
}
"""

# The Recipe's add control (design pass 14 §8): the glyph's box and font
# size, and the word's box and cap height from its font metrics.
RECIPE_ADD_JS = r"""
() => {
  const button = document.querySelector('.bl-recipe-add-stage');
  const glyph = button && button.querySelector('.codicon');
  if (!button || !glyph) return null;
  const R = (element) => {
    const r = element.getBoundingClientRect();
    return { left: r.left, top: r.top, width: r.width, height: r.height };
  };
  const word = Array.from(button.childNodes).find((node) => node.nodeType === 3 && node.textContent.trim());
  const range = document.createRange();
  range.selectNodeContents(word);
  const wordBox = range.getBoundingClientRect();
  return { glyph: R(glyph), size: getComputedStyle(glyph).fontSize,
           word: { left: wordBox.left, top: wordBox.top, width: wordBox.width, height: wordBox.height },
           text: word.textContent.trim() };
}
"""

# The trellis's initial diagram as the page draws it (design pass 14 §7):
# the graph named by the bar, the field boxes by perch layer, the join
# wires that carry a route, and the kind select's presence.
TRELLIS_INITIAL_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host') || document;
  const bar = document.querySelector('.bl-graph-bar');
  const nodes = Array.from(host.querySelectorAll('.react-flow__node'));
  // a field box's node, `periods[0]/bequest/bequest:cntn:V`, the stage's own field id under the occurrence's address
  const fields = nodes.filter((node) => node.querySelector('.bf-box.bf-field')).map((node) => node.getAttribute('data-id'));
  // an open perch layer, `periods[0]/bequest/cntn___group___`, under its occurrence's layer
  const perches = nodes.filter((node) => node.querySelector(':scope > .bf-layer'))
    .map((node) => node.getAttribute('data-id'))
    .filter((id) => /\/(arvl|dcsn|cntn)___group___$/.test(id));
  const wires = Array.from(host.querySelectorAll('.react-flow__edge')).map((edge) => edge.getAttribute('data-id'));
  return {
    graph: bar && bar.getAttribute('data-graph'),
    kindSelect: !!document.querySelector('.bl-view-kind'),
    fields: fields.length,
    perches: perches.length,
    wires: wires.length,
    errors: (window.__errors || []).slice(0, 3),
  };
}
"""


def test_no_hover_label_or_type_of_the_stage_page_prints_result(browser, server_on, durables_folder):
    """Design pass 14 §4 (S-D8). On the stage page of `tenure.bl`, with the
    aggregation box of `cntn_to_dcsn` selected, no hover, title or text
    holds the mark `:result`; the expectation's writing ports read their
    coordinate-lambda text with the identity spelled without the mark,
    `(a, h, z) ↦ dcsn_to_arvl.value:Expectation:1(a, h, z)`."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_file(tab, url, TENURE_FILE)
        wait_until(
            lambda: tab.evaluate("() => document.querySelectorAll('.bl-view-host .react-flow__edge').length") >= 10,
            60.0,
            "the stage graph's wires",
        )
        drawn = tab.evaluate(RESULT_JS)
        assert drawn["found"] == [] and drawn["texts"] == [], drawn
        assert drawn["sample"], drawn
        assert all("Expectation:1(" in text for text in drawn["sample"]), drawn["sample"]
        print(f"unit S: no ':result' on the stage page; {len(drawn['sample'])} expectation hovers")
    finally:
        context.close()


def test_the_composer_is_a_text_area_of_one_line_whose_text_and_button_stand_on_one_axis(
    browser, server_on, durables_folder
):
    """Design pass 14 §5 (S-D9, S-D10), as amendment 07 of spec 0.4 §2 item
    2 rewrites it. Matsya's composer is a text area, one line of 26 px
    while the draft is empty, its placeholder `Matsya query?` and its
    spoken name `Matsya query`; its one line stands centered in it within 1
    px, read on the line's band, from the inner element's top with its
    border and padding to the line's height of 18 px below, which stands as
    far from the control's top as from its foot (amendment 07 §6 case 2);
    and the icon button `Ask` is centered within 1 px on the axis of the
    composer's foot row `.bl-matsya-foot`, its right edge 8 px inside the
    composer box's right edge within 1 px (amendment 06 §6.2, which rewrites
    design pass 14 §5 and S-D9; SG4-11)."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_file(tab, url, TENURE_FILE)
        if not tab.evaluate("() => !!document.querySelector('.bl-matsya-field')"):
            tab.click(MATSYA_TOGGLE)
        wait_until(
            lambda: tab.evaluate("() => !!document.querySelector('.bl-matsya-field vscode-textarea')"),
            20.0,
            "the composer",
        )
        drawn = tab.evaluate(COMPOSER_JS)
        assert drawn["tag"] == "vscode-textarea", drawn
        assert (drawn["placeholder"], drawn["name"]) == ("Matsya query?", "Matsya query"), drawn
        host, inner, ask = drawn["host"], drawn["input"], drawn["ask"]
        assert abs(host["height"] - 26) <= 0.5, host
        assert inner is not None
        assert drawn["line"] == 18, drawn
        above = drawn["band"] - host["top"]
        below = (host["top"] + host["height"]) - (drawn["band"] + drawn["line"])
        assert abs(above - below) <= 1, (above, below)
        foot, box = drawn["foot"], drawn["box"]
        axis = foot["top"] + foot["height"] / 2
        assert abs((ask["top"] + ask["height"] / 2) - axis) <= 1, (ask, axis)
        assert abs((box["left"] + box["width"] - 8) - (ask["left"] + ask["width"])) <= 1, (ask, box)
        print(f"unit S: the composer {host['height']} px, its line {above} px from the top and {below} from the foot")
    finally:
        context.close()


def test_the_recipe_s_add_glyph_is_12_px_on_the_word_s_cap_height(browser, server_on, durables_folder):
    """Design pass 14 §8 (S-D15). The Codicon `add` before `Stage` at the
    Recipe's foot is 12 px, and its center stands within 1.5 px of the
    middle of the word's cap height."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        wait_until(lambda: tab.evaluate("() => !!document.querySelector('.bl-recipe-add-stage')"), 20.0, "the add control")
        drawn = tab.evaluate(RECIPE_ADD_JS)
        assert drawn is not None and drawn["text"] == "Stage", drawn
        assert drawn["size"] == "12px", drawn
        assert abs(drawn["glyph"]["width"] - 12) <= 0.5 and abs(drawn["glyph"]["height"] - 12) <= 0.5, drawn
        # the word's cap height, about 0.72 of its 13-px size, sits in the upper part of its 18-px line box
        word = drawn["word"]
        cap_middle = word["top"] + word["height"] / 2
        glyph_middle = drawn["glyph"]["top"] + drawn["glyph"]["height"] / 2
        assert abs(glyph_middle - cap_middle) <= 1.5, (glyph_middle, cap_middle)
        print(f"unit S: the add glyph {drawn['glyph']['height']} px, its middle {glyph_middle - cap_middle:+.2f} px from the word's")
    finally:
        context.close()


def test_the_trellis_offers_the_initial_view_whose_joins_run_between_fields(
    browser, server_on, durables_folder
):
    """Design pass 14 §7 (S-D12, S-D13). The graph bar of the trellis view
    holds the kind select; `Initial` shows the trellis's initial diagram of
    the direction shown, the bar naming it, with field boxes in open perch
    layers of the terminal period's occurrences, `periods[0]/bequest/cntn`,
    and wires between them, and no error from the region; `Operator` shows
    the builders graph again."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        assert tab.evaluate("() => !!document.querySelector('.bl-view-kind')")
        choose_view(tab, "initial", None)
        wait_until(
            lambda: tab.evaluate(TRELLIS_INITIAL_JS)["fields"] > 0,
            60.0,
            "the fields of the initial diagram",
        )
        drawn = tab.evaluate(TRELLIS_INITIAL_JS)
        assert drawn["graph"] == "backward initial diagram", drawn
        assert drawn["kindSelect"] and drawn["fields"] >= 3 and drawn["perches"] >= 1, drawn
        assert drawn["wires"] >= 1 and drawn["errors"] == [], drawn
        choose_view(tab, "operator", None)
        wait_until(lambda: tab.evaluate(TRELLIS_INITIAL_JS)["graph"] == "backward", 30.0, "the builders graph")
        print(f"unit S: the trellis's initial diagram drew {drawn['fields']} fields in {drawn['perches']} perch layers and {drawn['wires']} wires")
    finally:
        context.close()
