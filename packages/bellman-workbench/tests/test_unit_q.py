"""The tests of unit Q, design pass 13 (AAS, 16 October 2026: "the
alignment, fonts and formatting really need to be made clean"; "the plug
also looks off"), the development repository's record of design pass 13,
the page made clean, §6. Work
package Q1, the graph: the port's center on its wire's end in both graphs
within 0.25 px; a first run of 24 px from every plug, no count's box
crossing a route, and the marks between 3 and 6 px on the screen at the
fitted view; the card's 32 px with its ports on the axis and the chevron's
click changing the drawing; the column's one width; and the selected
cable's accent at its plug. Work package Q2, the chrome: the five type
steps and no other size among the texts of the main bar, the tree, the
tabs' row, the graph bar, the Recipe, Details and the status line, Codicons
and the editor's source excepted; the row heights and the text edges; and
the three line values and the one mark per state. The fix wave Q3a, the
graph after the second review round of design pass 13 (items 1 to 11 of
its brief, 17 October 2026): a plug a cable leaves filled; one row order per
stage, from the recipe's `stages:` list, and no two cables sharing a run or
crossing at periods 0 to 2 and 0 to 9; the edges drawn as inset shadows
that take no layout width and hold a pixel on the screen at every zoom; no
cable label, and the count clear in every state; no end square on a
selected cable, its movable ports ringed; the stubs bent outside the frame;
a card selected in the opening view inside the region; the opening view on
the text edge; every period frame of periods 0 to 9 on one top; and the add
controls at the view's scale. The fix wave Q3b, the chrome after the second
review round (items 15 to 20 of its brief, 18 October 2026): the Recipe's
rows of 48 px, four standing whole at the panel's default height; the graph
bar of one row, its name not drawn where its items do not fit with it;
Details' blocks 8 px apart, the removal row last after the legend; the
chrome on whole pixels and its right text edges; Details' heads and the
page's words in their faces and in sentence case, the path naming its
occurrence once, the lists' and the tables' rows on their baselines; and the
inks and states of contexts, chevrons, lists, links and overlays. Every test
reads the page's elements, never a screenshot's pixels, on a copy of the
durables model at periods 0 to 2, the restriction its trellis of 51 periods
opens with, or 0 to 9 where it says so. Since design pass 14 the page opens
laid out from top to bottom and keeps the direction turned (unit S); the
tests of the trellis's geometry turn the page to the right first, the
layout they were written for, and the tests of the stage graph turn it
back, under unit N's fix-wave rule that a test of a rule which holds in
the horizontal layout turns the page horizontal first."""

from __future__ import annotations

from workbench_support import (
    FRAME_TRACKS,
    JOIN_POINT_JS,
    MATSYA_TOGGLE,
    OPENING_TOP,
    RECIPE_FILE,
    TEXT_EDGE,
    TWO_FRAMES_JS,
    VIEW_STATE_JS,
    cable_port,
    choose_view,
    click_join,
    click_toggle,
    flow_handle,
    hold_events,
    join_wires_drawn,
    lay_out_left_to_right,
    lay_out_top_to_bottom,
    move_join_end,
    new_tab,
    open_file,
    open_page_form,
    open_recipe_row,
    open_stage_list,
    open_trellis,
    property_color,
    record_layouts,
    release_events,
    restrict,
    restriction_shown,
    select_node,
    view_still,
    viewport,
    wait_until,
)

from bellman.stage import LAYER_ID_ENDING

# the stage file whose graph is the stage view read, and the two occurrences whose cable the tests hover and
# select, the route from `tenure` of periods[0] into `keeper_cons` of periods[1], whose record names the reader
# first (design pass 12 §2; N-I192)
TENURE_FILE = "declaration/stages/tenure/tenure.bl"
# the lines the backward graph of tenure.bl draws for its 35 wires: one for each bundle of the value wires from
# one box to another and one for each other wire, ten bundles and the policy builder's seven lines (design pass 14
# §1; unit S)
STAGE_LINES = 17
TENURE, READER = "periods[0]/tenure", "periods[1]/keeper_cons"
# the card at rest (design pass 13 §2): its height, its axis, the pitch of two plugs, the top and the left of
# its name's line box, its chevron's target, its strip (the top, the height, the left inset and the right
# inset), and the width of each card of the durables model, one width for the consumers' column
CARD_HIGH, AXIS, PITCH = 32, 14, 12
NAME_AT = (9, 3)
CHEVRON_TARGET = 24
STRIP = (24, 3, 9, 29)
CARD_WIDTHS = {"tenure": 80, "bequest": 88, "keeper_cons": 136, "adjuster_cons": 136}
# the builders of each stage of the durables model, one segment each in the card's strip: the two pairs of
# perches and, where the stage decides, the policy builder
BUILDERS = {"tenure": 3, "bequest": 2, "keeper_cons": 3, "adjuster_cons": 3}
# the first run from a plug, a port's mark, the mark's least size on the screen, the scale below which no count
# is drawn, and the cap height of a digit of the count at the Mark step (design pass 13 §1, rules 3 and 5)
FIRST_RUN, MARK, MARK_LEAST, SMALL, CAP = 24, 6, 3, 0.75, 6.6

# The graph as the region draws it, in the flow's units at the view's scale `zoom`: each cable, a cable's edge,
# with whether it is the piece a pair of periods shares, whether it leaves a plug, whether its two ends stand
# in one period, the distance of its route's first point from its source handle's center and of its last point
# from its target handle's center, the length of its first run, whether any run is neither horizontal nor
# vertical, its stroke on the screen, its slash's stroke and ink, and its count's text, its digits' box (the
# cap height above the baseline, the text's advance), its ink and whether it is drawn; every segment of every
# route; each card port's mark, its size and its border on the screen, its fill, its border's ink and whether
# it is lit; each card's size, place and ports, with the places of its name, its chevron and its strip's
# segments; the period frames' tops; the region's box; and the drawing's top left corner on the screen, a
# marker's label counted.
GRAPH_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host');
  const flow = host.querySelector('.react-flow');
  const pane = flow.getBoundingClientRect();
  const view = new DOMMatrixReadOnly(getComputedStyle(flow.querySelector('.react-flow__viewport')).transform);
  const zoom = view.a;
  const toFlow = (x, y) => ({x: (x - pane.left - view.e) / zoom, y: (y - pane.top - view.f) / zoom});
  const center = (element) => {
    const r = element.getBoundingClientRect();
    return toFlow((r.left + r.right) / 2, (r.top + r.bottom) / 2);
  };
  const periodOf = (id) => (/^periods\[\d+\]/.exec(id || '') || [null])[0];
  // a mark's edge, the inset shadow of no offset and no blur, {color, width}, which takes no layout width (Q3a item 3)
  const edgeOf = (style) => {
    const found = /(rgba?\([^)]*\)|color\([^)]*\))\s+0px\s+0px\s+0px\s+(-?[\d.]+)px\s+inset/.exec(style.boxShadow || '');
    return found ? {color: found[1], width: Number(found[2])} : null;
  };
  const handles = {};
  for (const h of host.querySelectorAll('.react-flow__handle')) handles[h.dataset.handleid] = h;
  const edges = [];
  for (const edge of host.querySelectorAll('.react-flow__edge')) {
    const path = edge.querySelector('.react-flow__edge-path');
    if (!path) continue;
    const parts = [];
    for (const step of (path.getAttribute('d') || '').match(/[ML][^ML]*/g) || []) {
      const [x, y] = step.slice(1).split(',').map(Number);
      if (step[0] === 'M' || !parts.length) parts.push([]);
      parts[parts.length - 1].push({x, y});
    }
    const [sp, tp] = (edge.dataset.id || '').split('>>');
    const s = handles[sp], t = handles[tp], first = parts[0] || [], last = parts[parts.length - 1] || [];
    // the piece a pair of periods shares runs from where its wires meet into the socket, and each of its wires
    // from its plug to that meeting, so that the piece has the reading end and a wire the writing end (K-D5)
    const pair = edge.classList.contains('bf-join-pair'), shared = edge.classList.contains('bf-cable-shared');
    const ends = {};
    if (s && first.length && !pair) { const c = center(s); ends.source = [first[0].x - c.x, first[0].y - c.y]; }
    if (t && last.length && !shared) { const c = center(t); ends.target = [last[last.length - 1].x - c.x, last[last.length - 1].y - c.y]; }
    const segments = parts.flatMap((part) => part.slice(1).map((p, i) => [part[i], p]));
    const count = edge.querySelector('.bf-cable-count'), bus = edge.querySelector('.bf-cable-bus');
    const sourceNode = s ? s.closest('.react-flow__node').dataset.id : null;
    const targetNode = t ? t.closest('.react-flow__node').dataset.id : null;
    edges.push({
      id: edge.dataset.id, cable: edge.classList.contains('bf-cable-edge'), pair, shared,
      plug: !!s && s.classList.contains('bf-cable-branch'),
      within: !!periodOf(sourceNode) && periodOf(sourceNode) === periodOf(targetNode),
      ends, firstRun: first.length > 1 ? Math.hypot(first[1].x - first[0].x, first[1].y - first[0].y) : null,
      diagonal: segments.some(([a, b]) => Math.abs(a.x - b.x) > 0.01 && Math.abs(a.y - b.y) > 0.01),
      strokeScreen: parseFloat(getComputedStyle(path).strokeWidth) * zoom, stroke: getComputedStyle(path).stroke,
      bus: bus ? {stroke: getComputedStyle(bus).stroke, width: parseFloat(getComputedStyle(bus).strokeWidth)} : null,
      count: count ? {text: count.textContent, x: Number(count.getAttribute('x')), baseline: Number(count.getAttribute('y')),
                      advance: count.getComputedTextLength(), fill: getComputedStyle(count).fill,
                      shown: getComputedStyle(count).display !== 'none'} : null,
      label: (() => { const l = edge.querySelector('.bf-cable-label'); return l ? {text: l.textContent, opacity: getComputedStyle(l).opacity, family: getComputedStyle(l).fontFamily, size: getComputedStyle(l).fontSize, fill: getComputedStyle(l).fill} : null; })(),
      title: (() => { const t = edge.querySelector('title'); return t ? t.textContent : null; })(),
      segments,
    });
  }
  const marks = Array.from(host.querySelectorAll('.bf-card > .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)'), (h) => {
    const before = getComputedStyle(h, '::before'), r = h.getBoundingClientRect(), edge = edgeOf(before);
    return {handle: h.dataset.handleid, side: h.dataset.side, markScreen: parseFloat(before.width) * zoom,
            borderScreen: edge ? edge.width * zoom : 0, fill: before.backgroundColor, border: edge ? edge.color : null,
            target: Math.min(r.width, r.height), lit: h.classList.contains('bf-lit')};
  });
  const cards = [];
  for (const node of host.querySelectorAll('.react-flow__node')) {
    const card = node.querySelector(':scope > .bf-card');
    if (!card) continue;
    const box = node.getBoundingClientRect();
    const rel = (element) => { const r = element.getBoundingClientRect(); return {left: (r.left - box.left) / zoom, top: (r.top - box.top) / zoom, width: r.width / zoom, height: r.height / zoom}; };
    const place = (n) => { const f = /translate\(\s*(-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform); return f ? [Number(f[1]), Number(f[2])] : [null, null]; };
    const [cardX, cardY] = place(node);
    cards.push({
      id: node.dataset.id, x: cardX, width: node.offsetWidth, height: node.offsetHeight,
      full: !!node.querySelector(':scope > .bf-layer:not(.bf-compact)'),
      ports: Array.from(card.querySelectorAll(':scope > .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)'), (h) => {
        const r = h.getBoundingClientRect();
        return {side: h.dataset.side, x: ((r.left + r.right) / 2 - box.left) / zoom, y: ((r.top + r.bottom) / 2 - box.top) / zoom};
      }),
      name: rel(card.querySelector(':scope > .bf-layer-name, :scope > .bf-name')),
      chevron: rel(card.querySelector(':scope > .bf-chevron')),
      strip: Array.from(host.querySelectorAll(`.react-flow__node[data-id^="${CSS.escape(node.dataset.id.slice(0, -'___group___'.length) + '/')}"]`))
        .filter((n) => n.querySelector(':scope > .bf-builder'))
        .map((n) => { const [x, y] = place(n); return {x: x - cardX, y: y - cardY, width: n.offsetWidth, height: n.offsetHeight}; })
        .sort((a, b) => a.x - b.x),
    });
  }
  const frames = Array.from(host.querySelectorAll('.react-flow__node'), (node) => {
    if (!node.querySelector(':scope > .bf-layer.bf-period')) return null;
    const found = /translate\(\s*(-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(node.style.transform);
    return {id: node.dataset.id, y: Number(found[2])};
  }).filter(Boolean);
  let left = Infinity, top = Infinity;
  for (const node of host.querySelectorAll('.react-flow__node')) {
    const r = node.getBoundingClientRect();
    left = Math.min(left, r.left); top = Math.min(top, r.top);
    const label = node.querySelector('.bf-marker > .bf-boundary-label');
    if (label) { const l = label.getBoundingClientRect(); left = Math.min(left, l.left); top = Math.min(top, l.top); }
  }
  return {zoom, edges, marks, cards, frames, region: {left: pane.left, top: pane.top, width: pane.width, height: pane.height}, drawn: {left, top}};
}
"""

# The stage graph as the region draws it, at the view's scale: each wire's ends against its handles' centers,
# in the flow's units, and each port's size, border and fill.
STAGE_JS = r"""
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
  const edges = [];
  for (const edge of host.querySelectorAll('.react-flow__edge')) {
    const path = edge.querySelector('.react-flow__edge-path');
    const pts = ((path.getAttribute('d') || '').match(/[ML][^ML]*/g) || []).map((s) => { const [x, y] = s.slice(1).split(',').map(Number); return {x, y}; });
    const [sp, tp] = (edge.dataset.id || '').split('>>');
    const s = handles[sp], t = handles[tp], ends = {};
    if (s && pts.length) { const c = center(s); ends.source = [pts[0].x - c.x, pts[0].y - c.y]; }
    if (t && pts.length) { const c = center(t); ends.target = [pts[pts.length - 1].x - c.x, pts[pts.length - 1].y - c.y]; }
    edges.push({id: edge.dataset.id, ends});
  }
  const ports = Array.from(host.querySelectorAll('.react-flow__handle'), (h) => {
    const r = h.getBoundingClientRect(), style = getComputedStyle(h);
    const found = /(rgba?\([^)]*\)|color\([^)]*\))\s+0px\s+0px\s+0px\s+(-?[\d.]+)px\s+inset/.exec(style.boxShadow || '');
    return {size: r.width / zoom, border: parseFloat(style.borderTopWidth) || 0, edge: found ? {color: found[1], width: Number(found[2])} : null,
            fill: style.backgroundColor, writes: h.classList.contains('source')};
  });
  return {zoom, edges, ports};
}
"""


def at_scale_one(tab) -> None:
    """Sets the view's scale to 1 where it stands, as the graph's handle sets a view (R-D29), and waits for the
    drawing to stand still there."""
    view = viewport(tab)
    flow_handle(tab, "setView", {"viewport": {"x": view["x"], "y": view["y"], "zoom": 1.0}, "selection": None})
    wait_until(lambda: abs(viewport(tab)["zoom"] - 1.0) <= 1e-6, 5.0, "the view at scale 1")
    tab.evaluate(TWO_FRAMES_JS)


def both_graphs(tab, url, folder):
    """Opens the durables trellis at periods 0 to 2, turns the page to the right, the layout these tests were
    written for (design pass 14 §2; unit N's fix-wave rule), and yields each trellis graph, the forward one first,
    laid out and at rest, with the view at scale 1."""
    open_trellis(tab, url, RECIPE_FILE)
    assert restriction_shown(tab) == "periods 0–2"
    record_layouts(tab)
    lay_out_left_to_right(tab)
    for direction in ("forward", "backward"):
        choose_view(tab, None, direction)
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the {direction} graph")
        wait_until(lambda: view_still(tab), 30.0, f"the {direction} graph at rest")
        at_scale_one(tab)
        yield direction


def cables_of(drawn: dict) -> list[dict]:
    """The cables of the drawing `drawn` (GRAPH_JS) that leave a plug or a marker, the piece a pair of periods
    shares left out."""
    return [e for e in drawn["edges"] if e["cable"] and not e["pair"]]


def ends_of(drawn: dict) -> list[tuple]:
    """Every end a cable of the drawing `drawn` (GRAPH_JS) is to meet a port at, (the cable's id, the end, dx,
    dy): a cable's writing end, the reading end of a cable that shares no piece, and the reading end of a
    piece a pair of periods shares (K-D5)."""
    return [
        (e["id"], end, dx, dy)
        for e in drawn["edges"]
        if e["cable"]
        for end, (dx, dy) in e["ends"].items()
    ]


def test_a_port_s_center_stands_on_its_wire_s_end_in_both_graphs(browser, server_on, durables_folder):
    """Design pass 13 §1, rule 1 (A11, O-D7). In each trellis graph of the durables model at periods 0 to 2, at
    scale 1, every cable's route begins at the center of its plug, or of the marker's mark it leaves, and ends at
    the center of its socket, within 0.25 px, every run of every route horizontal or vertical; and in the stage
    graph of `tenure.bl`, at scale 1, every one of its 17 lines, one for each bundle of value wires between two
    boxes and one for each other wire (design pass 14 §1), begins and ends at the centers of its two ports, which
    are 6-px squares with no CSS border, a writing port filled and a reading port hollow, its edge a 1-px inset
    shadow in the port ink (Q3a item 3)."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            drawn = tab.evaluate(GRAPH_JS)
            cables = cables_of(drawn)
            assert len(cables) >= 15, (direction, len(cables))
            for cable in cables:
                expected = {"source"} if cable["shared"] else {"source", "target"}
                assert set(cable["ends"]) == expected, (direction, cable["id"], cable["ends"])
                assert not cable["diagonal"], (direction, cable["id"])
            ends = ends_of(drawn)
            assert len(ends) >= 2 * len(cables) - 4, (direction, len(ends))
            for id, end, dx, dy in ends:
                assert abs(dx) <= 0.25 and abs(dy) <= 0.25, (direction, id, end, dx, dy)
            print(f"unit Q: the {direction} graph's {len(cables)} cables, {len(ends)} ends on their ports")
        # the stage graph of tenure.bl at scale 1, laid out downward as it opened before design pass 14
        lay_out_top_to_bottom(tab)
        open_file(tab, url, TENURE_FILE)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        wait_until(lambda: tab.evaluate("() => document.querySelectorAll('.bl-view-host .react-flow__edge').length") == STAGE_LINES, 60.0, "the stage graph's lines")
        at_scale_one(tab)
        stage = tab.evaluate(STAGE_JS)
        assert len(stage["edges"]) == STAGE_LINES, len(stage["edges"])
        for wire in stage["edges"]:
            for end, (dx, dy) in wire["ends"].items():
                assert abs(dx) <= 0.25 and abs(dy) <= 0.25, (wire["id"], end, dx, dy)
        navy, port_ink = property_color(tab, "--bl-navy"), property_color(tab, "--bl-graph-port")
        assert stage["ports"], stage
        for port in stage["ports"]:
            assert abs(port["size"] - MARK) <= 0.01 and port["border"] == 0, port
            assert port["fill"] == (port_ink if port["writes"] else navy), port
            if not port["writes"]:
                assert port["edge"] == {"color": port_ink, "width": 1}, port
        print(f"unit Q: the stage graph's {len(stage['edges'])} wires end on their {len(stage['ports'])} ports")
    finally:
        context.close()


def test_a_first_run_of_24_px_no_count_on_a_route_and_marks_of_3_px_at_the_fitted_view(
    browser, server_on, durables_folder
):
    """Design pass 13 §1, rules 3 to 6 (A1, A2, A6, E8, check 21, check 24). In each trellis graph at scale 1,
    every cable leaves its plug on a straight run of 24 px within a period and of at least 24 px between
    periods; no count's digits stand on any route; every count is drawn, at the Mark step in ink-3, its slash in
    the port ink; and every period frame shares one top edge. Fitted, at a scale below 0.75, no count is drawn,
    every port's mark stands between 3 and 6 px on the screen with its border no thinner than a pixel, every
    cable no thinner than a pixel, and the drawing's top stands 24 px below the bar and its left edge, a
    marker's label counted, on the text edge."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            ink_3, port_ink = property_color(tab, "--bl-ink-3"), property_color(tab, "--bl-graph-port")
            drawn = tab.evaluate(GRAPH_JS)
            cables = cables_of(drawn)
            plugs = [c for c in cables if c["plug"]]
            assert plugs, direction
            for cable in plugs:
                if cable["within"]:
                    assert abs(cable["firstRun"] - FIRST_RUN) <= 0.01, (direction, cable["id"], cable["firstRun"])
                else:
                    assert cable["firstRun"] >= FIRST_RUN - 0.01, (direction, cable["id"], cable["firstRun"])
            counted = [c for c in cables if c["count"]]
            assert counted, direction
            segments = [segment for c in drawn["edges"] for segment in c["segments"]]
            for cable in counted:
                count = cable["count"]
                assert count["shown"] and count["fill"] == ink_3, (direction, count)
                assert cable["bus"] and cable["bus"]["stroke"] == port_ink and abs(cable["bus"]["width"] - 1.3) <= 0.01, (direction, cable["bus"])
                box = (count["x"], count["baseline"] - CAP, count["x"] + count["advance"], count["baseline"])
                for a, b in segments:
                    crosses = (
                        max(a["x"], b["x"]) >= box[0] and min(a["x"], b["x"]) <= box[2]
                        and max(a["y"], b["y"]) >= box[1] and min(a["y"], b["y"]) <= box[3]
                    )
                    assert not crosses, (direction, cable["id"], box, a, b)
            tops = {frame["y"] for frame in drawn["frames"]}
            assert len(drawn["frames"]) == 3 and len(tops) == 1, (direction, drawn["frames"])
            print(f"unit Q: the {direction} graph's {len(plugs)} plugs and {len(counted)} counts; first runs {sorted({round(c['firstRun']) for c in plugs})}")

            # fitted
            tab.click(".bl-zoom-button[data-zoom='fit']")
            wait_until(lambda: view_still(tab), 30.0, f"the {direction} graph fitted")
            fitted = tab.evaluate(GRAPH_JS)
            assert fitted["zoom"] < SMALL, (direction, fitted["zoom"])
            for cable in cables_of(fitted):
                if cable["count"]:
                    assert not cable["count"]["shown"], (direction, cable["id"])
                assert cable["strokeScreen"] >= 1 - 0.01, (direction, cable["id"], cable["strokeScreen"])
            assert fitted["marks"], direction
            for mark in fitted["marks"]:
                assert MARK_LEAST - 0.01 <= mark["markScreen"] <= MARK + 0.01, (direction, mark)
                if mark["side"] == "reading":
                    assert mark["borderScreen"] >= 1 - 0.01, (direction, mark)
            region, place = fitted["region"], fitted["drawn"]
            assert abs(place["top"] - (region["top"] + OPENING_TOP)) <= 1, (direction, region, place)
            assert abs(place["left"] - (region["left"] + TEXT_EDGE)) <= 1, (direction, region, place)
            print(f"unit Q: the {direction} graph fitted at {fitted['zoom']:.3f}, marks {min(m['markScreen'] for m in fitted['marks']):.2f} px on the screen")
    finally:
        context.close()


def test_the_card_is_32_px_with_its_ports_on_the_axis_and_the_chevron_s_click_changes_the_drawing(
    browser, server_on, durables_folder
):
    """Design pass 13 §2, rules 1 to 5 (B1, B3, B10, check 30). In the backward graph at scale 1, every card of
    the durables model, its fields all joined, is 32 px high, its name's line box from (9, 3), its chevron's
    target 24 px square from w − 28 to w − 4 and y 2 to 26, its socket's center at (0, 14), a single plug's at
    (w, 14) and two plugs' at y 8 and 20, its strip 3 px high at y 24 from x = 9 to w − 29 in segments of
    equal width 2 px apart, one per builder. A click on the chevron of `tenure` of periods[0] opens the
    occurrence with every builder open, which changes the drawing; the open layer's chevron closes it back to
    the card, drawn as before with its strip."""
    tenure = TENURE + LAYER_ID_ENDING
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            if direction != "backward":
                continue
            drawn = tab.evaluate(GRAPH_JS)
            cards = {c["id"]: c for c in drawn["cards"]}
            assert len(cards) == 10, sorted(cards)
            for id, card in cards.items():
                key = id.split("/")[1][: -len(LAYER_ID_ENDING)]
                w = card["width"]
                assert card["height"] == CARD_HIGH and w == CARD_WIDTHS[key], (id, card["height"], w)
                assert (round(card["name"]["left"], 1), round(card["name"]["top"], 1)) == NAME_AT, (id, card["name"])
                chevron = card["chevron"]
                assert (round(chevron["left"]), round(chevron["top"]), round(chevron["width"]), round(chevron["height"])) == (w - 28, 2, CHEVRON_TARGET, CHEVRON_TARGET), (id, chevron)
                sockets = [p for p in card["ports"] if p["side"] == "reading"]
                plugs = sorted((p for p in card["ports"] if p["side"] == "writing"), key=lambda p: p["y"])
                assert len(sockets) == 1 and abs(sockets[0]["x"]) <= 0.5 and abs(sockets[0]["y"] - AXIS) <= 0.5, (id, sockets)
                assert all(abs(p["x"] - w) <= 0.5 for p in plugs), (id, plugs)
                expected = [AXIS] if len(plugs) == 1 else [AXIS - PITCH / 2, AXIS + PITCH / 2]
                assert [round(p["y"], 1) for p in plugs] == expected, (id, plugs)
                strip = card["strip"]
                assert len(strip) == BUILDERS[key], (id, strip)
                top, high, left, right = STRIP
                assert all((s["y"], s["height"]) == (top, high) for s in strip), (id, strip)
                assert strip[0]["x"] == left and strip[-1]["x"] + strip[-1]["width"] == w - right, (id, strip)
                assert all(strip[i + 1]["x"] - (strip[i]["x"] + strip[i]["width"]) == 2 for i in range(len(strip) - 1)), (id, strip)
                assert max(s["width"] for s in strip) - min(s["width"] for s in strip) <= 1, (id, strip)
            # the chevron's click opens the occurrence with every builder open
            node = f'.bl-view-host .react-flow__node[data-id="{tenure}"]'
            tab.click(f"{node} .bf-chevron")
            wait_until(
                lambda: (found := tab.evaluate(GRAPH_JS)) and tenure not in {c["id"] for c in found["cards"]}
                and tab.locator(f"{node} > .bf-layer:not(.bf-compact)").count() == 1,
                30.0,
                "tenure drawn in full",
            )
            opened = set(flow_handle(tab, "openLayers"))
            inside = {ns for ns in opened if ns.startswith(TENURE + "/")}
            assert TENURE in opened and inside == {TENURE + "/cntn_to_dcsn", TENURE + "/dcsn_to_arvl", TENURE + "/policy"}, opened
            # the open layer's chevron closes it back to the card, one drawing with its strip; the view is
            # fitted and enlarged over the toggle first, since the open layer reaches above the region
            click_toggle(tab, tenure)
            card, _ = wait_until(
                lambda: next((c for c in tab.evaluate(GRAPH_JS)["cards"] if c["id"] == tenure), None),
                30.0,
                "tenure drawn as its card again",
            )
            assert card["height"] == CARD_HIGH and card["width"] == CARD_WIDTHS["tenure"] and len(card["strip"]) == 3, card
            assert TENURE not in set(flow_handle(tab, "openLayers"))
            print(f"unit Q: {len(cards)} cards of 32 px; tenure opened with {sorted(inside)} and closed again")
    finally:
        context.close()


def test_the_cards_of_one_column_take_one_width(browser, server_on, durables_folder):
    """Design pass 13 §2, rule 6 (D14, B5; Q-D25). In each trellis graph at scale 1, `keeper_cons` and
    `adjuster_cons` of each period, one column, take one width, the widest of the two at rest, 136 px, and
    stand on one left edge; `tenure` is 80 px and `bequest` 88."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            cards = {c["id"]: c for c in tab.evaluate(GRAPH_JS)["cards"]}
            for h in range(3):
                keeper = cards[f"periods[{h}]/keeper_cons{LAYER_ID_ENDING}"]
                adjuster = cards[f"periods[{h}]/adjuster_cons{LAYER_ID_ENDING}"]
                assert keeper["width"] == adjuster["width"] == CARD_WIDTHS["keeper_cons"], (direction, h, keeper["width"], adjuster["width"])
                assert abs(keeper["x"] - adjuster["x"]) <= 0.01, (direction, h, keeper["x"], adjuster["x"])
                assert cards[f"periods[{h}]/tenure{LAYER_ID_ENDING}"]["width"] == CARD_WIDTHS["tenure"]
            assert cards[f"periods[0]/bequest{LAYER_ID_ENDING}"]["width"] == CARD_WIDTHS["bequest"]
            print(f"unit Q: the {direction} graph's columns, {[(c['id'].split('/')[1].split('_')[0], c['width']) for c in cards.values()][:4]}")
    finally:
        context.close()


def test_the_selected_cable_s_plug_takes_the_accent_and_its_socket_keeps_the_port_ink(
    browser, server_on, durables_folder
):
    """Design pass 13 §1, rule 7 (A10, A12, E7, check 36; Q-D17). In the backward graph, the cable from `tenure`
    of periods[0] into `keeper_cons` of periods[1], hovered, draws its stroke in ice-3 and no label, its count
    standing at its plug; selected, its stroke and its slash are 2 px in the accent, its plug is filled in the
    accent, its socket keeps its 1-px border in the port ink around a navy hole, and its count keeps ink-3. In
    the forward graph the hovered cable of the branch `keep` draws no label, its title beginning with `keep` (Q3a
    item 4, amending Q-D17)."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            accent, port_ink, navy = (property_color(tab, name) for name in ("--bl-accent", "--bl-graph-port", "--bl-navy"))
            ice_3, ink_2, ink_3 = (property_color(tab, name) for name in ("--bl-ice-3", "--bl-ink-2", "--bl-ink-3"))
            if direction == "forward":
                writer, reader = "periods[0]/tenure", "periods[0]/keeper_cons"
                wait_until(lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)}, 30.0, "the forward cable's record")
                point = tab.evaluate(JOIN_POINT_JS, [writer, reader])
                tab.mouse.move(point["x"], point["y"])

                def lit_by_hover():
                    cable = next((c for c in tab.evaluate(GRAPH_JS)["edges"] if c["cable"] and c["stroke"] == ice_3), None)
                    return cable or None

                cable, _ = wait_until(lit_by_hover, 10.0, "the hovered cable in ice-3")
                assert cable["label"] is None, cable["label"]
                assert (cable["title"] or "").split("\n")[0] == "keep", cable["title"]
                print(f"unit Q: the forward cable hovered draws no label; its title begins {cable['title'].splitlines()[0]!r}")
                continue
            wait_until(lambda: (READER, TENURE) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)}, 30.0, "the backward cable's record")
            point = tab.evaluate(JOIN_POINT_JS, [READER, TENURE])
            tab.mouse.move(point["x"], point["y"])

            def hovered():
                found = tab.evaluate(GRAPH_JS)
                cable = next((c for c in found["edges"] if c["stroke"] == ice_3 and c["cable"]), None)
                return cable or None

            cable, _ = wait_until(hovered, 10.0, "the hovered cable in ice-3")
            assert cable["label"] is None or cable["label"]["text"] == "", cable["label"]
            assert cable["count"] and cable["count"]["text"] == "3", cable["count"]
            # selected, read at scale 1, where the stroke is 2 px and the count is drawn
            click_join(tab, READER, TENURE)
            tab.mouse.move(4, 4)
            at_scale_one(tab)

            def selected():
                found = tab.evaluate(GRAPH_JS)
                cable = next((c for c in found["edges"] if c["stroke"] == accent and c["cable"] and not c["pair"]), None)
                return (cable, found) if cable else None

            (cable, found), _ = wait_until(selected, 10.0, "the selected cable in the accent")
            assert abs(cable["strokeScreen"] - 2) <= 0.01 and cable["bus"]["stroke"] == accent and abs(cable["bus"]["width"] - 2) <= 0.01, cable
            assert cable["count"]["shown"] and cable["count"]["fill"] == ink_3, cable["count"]
            source, target = cable["id"].split(">>")
            marks = {m["handle"]: m for m in found["marks"]}
            plug = marks[source]
            assert plug["lit"] and plug["fill"] == accent, plug
            socket = next((m for m in found["marks"] if m["side"] == "reading" and m["lit"]), None)
            assert socket and socket["border"] == port_ink and socket["fill"] == navy, socket
            print(f"unit Q: the selected cable {cable['id'][:48]}… lit at its plug; its socket in the port ink")
    finally:
        context.close()


# --- work package Q2: the chrome of design pass 13 §§3 to 5 ---

# The styles of the five type steps of design pass 13 §3, each its face, the
# first family of the computed stack, its size and its weight: Title; Body's
# Head and Label; Code and Code name; Small and Code small; and Mark.
TYPE_STYLES = {
    "Title": ("Archivo", "18px", "400"),
    "Head": ("Archivo", "13px", "600"),
    "Label": ("Archivo", "13px", "400"),
    "Code": ("IBM Plex Mono", "12.5px", "400"),
    "Code name": ("IBM Plex Mono", "12.5px", "500"),
    "Small": ("Archivo", "11px", "500"),
    "Code small": ("IBM Plex Mono", "11px", "400"),
    "Mark": ("IBM Plex Mono", "9.5px", "400"),
}
# The regions of the chrome whose texts the type test reads (design pass 13 §6;
# check 40), by name; a Codicon draws its glyph as generated content and holds
# no text, and the editor's source and the graph's drawing stand outside these
# regions.
CHROME_REGIONS = {
    "main bar": ".bl-main-bar",
    "tree": ".bl-folder",
    "tabs' row": ".bl-tab-row",
    "graph bar": ".bl-graph-bar",
    "Recipe": '.bl-file .bl-classification[data-panel="recipe"]',
    "Details": ".bl-panel",
    "status line": ".bl-status",
}

# Every text the page draws among the elements given, the elements of one
# region and the library's components' own elements within it, which
# Playwright's selectors reach, as unit M reads the Codicons: each text that
# is an element's own child, with the element's face, size, weight, letter
# spacing, text transform and style; a text is drawn where its range has a
# box, its element is not hidden and no element that holds it, the
# components' hosts among them, is displayed as none or at opacity 0.
CHROME_TEXTS_JS = r"""
(elements) => {
  const shown = (node) => {
    const range = document.createRange();
    range.selectNodeContents(node);
    if (!Array.from(range.getClientRects()).some((r) => r.width > 0 && r.height > 0)) return false;
    let element = node.parentElement;
    if (getComputedStyle(element).visibility === 'hidden') return false;
    while (element) {
      const style = getComputedStyle(element);
      if (style.display === 'none' || parseFloat(style.opacity) === 0) return false;
      element = element.parentElement
        || (element.getRootNode && element.getRootNode().host) || null;
    }
    return true;
  };
  const found = [];
  for (const element of elements) {
    for (const node of element.childNodes) {
      if (node.nodeType !== 3 || !node.textContent.trim() || !shown(node)) continue;
      const style = getComputedStyle(element);
      found.push({
        text: node.textContent.trim().slice(0, 40),
        face: style.fontFamily.split(',')[0].replace(/"/g, '').trim(),
        size: style.fontSize, weight: style.fontWeight, spacing: style.letterSpacing,
        transform: style.textTransform, style: style.fontStyle,
      });
    }
  }
  return found;
}
"""
# The font synthesis of the window and of the editor's text
SYNTHESIS_JS = """
() => [getComputedStyle(document.querySelector('.bl-window')).fontSynthesis,
       getComputedStyle(document.querySelector('.cm-content')).fontSynthesis]
"""

# The rows and the edges of the chrome (design pass 13 §4): the columns' boxes
# and the window's width; the heights and tops of the main bar, the three first
# rows, the two lower heads, the status line and the tree's rows, each tree
# row's left and width and its twistie's left with the row's level; the
# baselines of the three first rows' words; the boxes of the controls of the
# bars; each Recipe row at rest with its height, its cells' first baselines and
# every line's height; the first glyph of the rows that stand on a left text
# edge, and the last glyph, filled box or icon glyph of the rows that end on a
# right text edge.
CHROME_GRID_JS = r"""
() => {
  const box = (element) => {
    if (!element) return null;
    const r = element.getBoundingClientRect();
    return {left: r.left, top: r.top, right: r.right, bottom: r.bottom,
            width: r.width, height: r.height};
  };
  const text = (element) => {
    if (!element) return null;
    const range = document.createRange();
    range.selectNodeContents(element);
    const r = range.getBoundingClientRect();
    return {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
  };
  const baseline = (element) => {
    if (!element) return null;
    const probe = document.createElement('span');
    probe.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
    element.insertBefore(probe, element.firstChild);
    const y = probe.getBoundingClientRect().bottom;
    probe.remove();
    return y;
  };
  // the box of a 16-px icon glyph centered in its target
  const glyph = (element) => {
    const r = box(element);
    if (!r) return null;
    const x = (r.left + r.right) / 2;
    return {left: x - 8, right: x + 8};
  };
  const q = (selector) => document.querySelector(selector);
  const levelOf = (row) => {
    let level = 0;
    for (let at = row.parentElement; at && !at.classList.contains('bl-tree');
         at = at.parentElement) {
      if (at.classList.contains('bl-tree-children')) level += 1;
    }
    return level;
  };
  const table = q('.bl-recipe-table');
  return {
    window: innerWidth,
    columns: {folder: box(q('.bl-folder')), file: box(q('.bl-file')), view: box(q('.bl-view'))},
    heights: {
      main: box(q('.bl-main-bar')), files: box(q('.bl-folder-rail')), tabs: box(q('.bl-tab-row')),
      graph: box(q('.bl-graph-bar')), strip: box(q('.bl-file .bl-inspector-strip')),
      details: box(q('.bl-panel .bl-region-head')), status: box(q('.bl-status')),
    },
    baselines: [baseline(q('.bl-folder-rail > h2')),
                baseline(q('.bl-tab.bl-active .bl-file-name')),
                baseline(q('.bl-graph-name'))],
    tree: Array.from(document.querySelectorAll('.bl-tree .bl-tree-level .bl-row'), (row) => ({
      box: box(row), level: levelOf(row), twistie: box(row.querySelector('.bl-twistie')),
    })),
    root: box(q('.bl-tree-root')),
    controls: Array.from(document.querySelectorAll(
      '.bl-graph-bar vscode-single-select, .bl-graph-bar .bl-restriction, '
      + '.bl-tab-actions > *'), box),
    recipe: Array.from(table.querySelectorAll('.bl-recipe-row[aria-expanded="false"]'), (row) => ({
      key: row.dataset.stage, box: box(row),
      firsts: Array.from(row.querySelectorAll('.bl-recipe-cell'),
        (cell) => baseline(cell.querySelector(
          '.bl-recipe-key, .bl-recipe-text, .bl-recipe-none, .bl-recipe-range'))),
      cells: Array.from(row.querySelectorAll('.bl-recipe-cell'),
        (cell) => Array.from(cell.querySelectorAll('.bl-recipe-line'),
          (line) => box(line).height)),
      trash: glyph(row.querySelector(':scope > .bl-remove-stage')),
    })),
    heads: box(table.querySelector('.bl-recipe-heads')),
    left: {
      files: text(q('.bl-folder-rail > h2')), tab: text(q('.bl-tab .bl-file-name')),
      graph: text(q('.bl-graph-name')),
      recipe: text(table.querySelector('.bl-recipe-heads > span')),
      details: text(q('.bl-panel .bl-region-name')),
      status: box(q('.bl-status-summary > :first-child')),
    },
    right: {
      toggle: glyph(Array.from(document.querySelectorAll('.bl-main-bar .bl-toggle')).pop()),
      save: box(q('.bl-save')), count: text(q('.bl-error-count')),
      close: glyph(q('.bl-panel .bl-region-close')),
      wide: glyph(q('.bl-file .bl-inspector-strip .bl-region-wide')),
      more: glyph(q('.bl-status-toggle')),
      files: glyph(Array.from(document.querySelectorAll('.bl-folder-bar > *')).pop()),
    },
  };
}
"""

# The boxes that draw the borders of the graph bar's select and of the
# restriction's button in the library's own trees, which Playwright's
# selectors reach
LIBRARY_EDGES = {
    "select": ".bl-graph-bar vscode-single-select .select-face",
    "restriction": ".bl-graph-bar vscode-button.bl-restriction .base",
}
# The lines and the marks of the chrome (design pass 13 §5), each a computed
# style: the color of the hairline under the main bar, an inset shadow since
# the fix wave Q3b (item 18; D29), of the folder's bar, the
# strip, Details' head and the Recipe's heads, above the add row and above the
# status line; the border of the canvas's control strip, the graph bar's two
# selects' being read in their own trees by Playwright's selectors
# (LIBRARY_EDGES); the main bar's open toggles and `Types`, each with its
# ground, its ink and its ::after; the active view tab's ::after and the
# disabled one's opacity; the Inspector's active tab's shadow; the tree's open
# file with its ground and its ::before; the problems count's color and
# Codicon; and the main bar's mark, its image's opacity and its ::before's
# ground.
CHROME_MARKS_JS = r"""
() => {
  const q = (selector) => document.querySelector(selector);
  const css = (element, pseudo) => element ? getComputedStyle(element, pseudo || null) : null;
  const after = (element) => {
    const style = css(element, '::after');
    return style ? {content: style.content, height: style.height, bottom: style.bottom,
                    ground: style.backgroundColor, left: style.left, right: style.right}
      : null;
  };
  const shadowLine = (element) => (
    css(element).boxShadow.match(/^(rgba?\([^)]*\)|color\([^)]*\))/) || [null])[0];
  const toggles = Array.from(
    document.querySelectorAll('.bl-main-bar .bl-toggle[aria-expanded="true"]'));
  const types = q('.bl-types-button[aria-pressed="true"]');
  const trellis = q('.bl-view-switch > vscode-tab-header.bl-active');
  const stage = q('.bl-view-switch > vscode-tab-header[aria-disabled="true"]');
  const open = q('.bl-tree-file.bl-open');
  const mark = q('.bl-error-mark');
  return {
    rules: {
      main: shadowLine(q('.bl-main-bar')), files: shadowLine(q('.bl-folder-rail')),
      strip: css(q('.bl-file .bl-inspector-strip')).borderBottomColor,
      details: css(q('.bl-panel .bl-region-head')).borderBottomColor,
      heads: css(q('.bl-recipe-heads')).borderBottomColor,
      add: css(q('.bl-recipe-add')).borderTopColor,
      status: shadowLine(q('.bl-status')),
    },
    edges: {
      controls: css(q('.bl-graph-controls')).borderTopColor,
    },
    toggles: toggles.map((toggle) => ({
      fold: toggle.dataset.fold, ground: css(toggle).backgroundColor,
      ink: css(toggle).color, line: after(toggle),
    })),
    types: types
      ? {ground: css(types).backgroundColor, ink: css(types).color, line: after(types)}
      : null,
    trellis: trellis ? {line: after(trellis)} : null,
    stage: stage ? css(stage).opacity : null,
    inspector: css(q('.bl-inspector-strip vscode-tab-header.bl-active')).boxShadow,
    open: open ? {ground: css(open).backgroundColor, left: open.getBoundingClientRect().left,
                  bar: {left: css(open, '::before').left, width: css(open, '::before').width,
                        ground: css(open, '::before').backgroundColor}} : null,
    count: {ink: css(mark).color, icon: mark.querySelector('.bl-error-icon').className},
    brand: {image: css(q('.bl-main-bar .bl-mark img')).opacity,
            paint: css(q('.bl-main-bar .bl-mark'), '::before').backgroundColor},
  };
}
"""

# The state of the element `selector` names under a forced pseudo-class: its
# ground, its ink and its outline.
STATE_JS = r"""
(selector) => {
  const element = document.querySelector(selector);
  const style = getComputedStyle(element);
  return {ground: style.backgroundColor, ink: style.color,
          outline: [style.outlineStyle, style.outlineWidth, style.outlineColor]};
}
"""

# Details of a selected stage occurrence as the page lays it out (design pass
# 13 §§3 to 5): each row's key as printed and as written, its value's ink and
# the inks of its names and its heads; the word row `bound`'s face and text;
# the head's name's face; and the removal row: whether it is the last element
# of Details' body and stands after the occurrence's rows and after the fold
# `Legend` (the fix wave Q3b, item 17; D24), its top rule's color, and each
# button's tag, classes, Codicon and words.
DETAILS_MARKS_JS = r"""
() => {
  const details = document.querySelector('.bl-occurrence-details');
  if (!details) return null;
  const css = (element) => element ? getComputedStyle(element) : null;
  const rows = Array.from(details.querySelectorAll('.bl-details-row'), (row) => ({
    key: row.dataset.key, printed: row.querySelector('.bl-details-key').textContent,
    value: css(row.querySelector('.bl-details-value')).color,
    names: Array.from(row.querySelectorAll('.bl-details-name'), (name) => css(name).color),
    heads: Array.from(row.querySelectorAll('.bl-details-head'), (head) => css(head).color),
  }));
  const words = details.querySelector('.bl-details-words');
  const body = details.closest('.bl-panel-body');
  const removal = body.querySelector(':scope > .bl-removal-buttons');
  const legend = body.querySelector(':scope > .bl-legend-details');
  const name = details.querySelector('.bl-panel-head > .bl-panel-name');
  return {
    rows,
    words: words ? {text: words.textContent,
                    face: css(words).fontFamily.split(',')[0].replace(/"/g, ''),
                    size: css(words).fontSize, weight: css(words).fontWeight} : null,
    name: name ? [css(name).fontFamily.split(',')[0].replace(/"/g, ''),
                  css(name).fontSize, css(name).fontWeight] : null,
    removal: removal ? {
      last: body.lastElementChild === removal,
      after: removal.getBoundingClientRect().top
        >= details.querySelector('.bl-details-rows').getBoundingClientRect().bottom
        && legend !== null
        && removal.getBoundingClientRect().top >= legend.getBoundingClientRect().bottom,
      rule: css(removal).borderTopColor, ruleWidth: css(removal).borderTopWidth,
      buttons: Array.from(removal.children, (button) => ({
        tag: button.tagName.toLowerCase(), classes: button.className,
        icon: (button.querySelector('.codicon') || {className: ''}).className,
        words: button.textContent.trim(),
      })),
    } : null,
  };
}
"""


def opened_backward(tab, url) -> None:
    """Opens the durables model's recipe with its trellis at periods 0 to 2,
    the backward graph drawn and at rest, and the pointer at the window's lower
    left corner."""
    open_trellis(tab, url, RECIPE_FILE)
    record_layouts(tab)
    for direction in ("forward", "backward"):
        choose_view(tab, None, direction)
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the {direction} graph")
        wait_until(lambda: view_still(tab), 30.0, f"the {direction} graph at rest")
    tab.mouse.move(1, 999)


def forced(tab, selector: str, states: list[str]):
    """Forces the pseudo-classes `states`, `hover` or `focus-visible`, on the
    element `selector` names through Chromium's developer protocol, as the
    pointer over it or the keyboard's focus sets them, and answers the
    protocol's session, whose detachment ends the forcing."""
    session = tab.context.new_cdp_session(tab)
    session.send("DOM.enable")
    session.send("CSS.enable")
    root = session.send("DOM.getDocument")["root"]["nodeId"]
    node = session.send("DOM.querySelector", {"nodeId": root, "selector": selector})["nodeId"]
    session.send("CSS.forcePseudoState", {"nodeId": node, "forcedPseudoClasses": states})
    return session


def test_the_chrome_s_texts_take_the_five_type_steps_and_no_other_size(
    browser, server_on, durables_folder
):
    """Design pass 13 §3 (C1 to C16; check 40). With the durables model's
    recipe open, its trellis drawn and the card `tenure` of a period selected,
    every text the page draws in the main bar, the folder column, the tabs'
    row, the graph bar, the Recipe tab, Details and the status line, the
    library's controls' own texts among them, is set in one of the styles of
    the five type steps, Title, Head, Label, Code, Code name, Small, Code small
    and Mark, with no letter spacing, no text transform and no slant; Codicons,
    which hold no text, and the editor's source stand outside the regions. The
    window and the editor draw no weight or slant a face does not hold
    (`font-synthesis: none`). The path is Label, the Recipe's keys and Details'
    selected name Code name, the Recipe's heads Small, Details' keys sentence
    case and `Bound` Small."""
    styles = {style: name for name, style in TYPE_STYLES.items()}
    context, tab = new_tab(browser)
    try:
        opened_backward(tab, server_on(durables_folder))
        tab.locator('.bf-card[aria-label="layer tenure"]').first.click()
        wait_until(lambda: tab.evaluate(DETAILS_MARKS_JS), 30.0, "Details of tenure")
        tab.mouse.move(1, 999)
        # each region's texts, those of the library's components' own trees
        # among them, through Playwright's selectors, which reach those trees
        texts, missing = [], []
        for region, selector in CHROME_REGIONS.items():
            if tab.locator(selector).count() == 0:
                missing.append(region)
                continue
            elements = tab.locator(f"{selector}, {selector} *")
            texts += [
                {"region": region, **text} for text in elements.evaluate_all(CHROME_TEXTS_JS)
            ]
        synthesis = tab.evaluate(SYNTHESIS_JS)
        assert missing == [] and synthesis == ["none", "none"], (missing, synthesis)
        assert {text["region"] for text in texts} == set(CHROME_REGIONS), {
            text["region"] for text in texts
        }
        outside = [
            text for text in texts if (text["face"], text["size"], text["weight"]) not in styles
        ]
        assert outside == [], outside
        plain = [
            text
            for text in texts
            if (text["spacing"], text["transform"], text["style"]) != ("normal", "none", "normal")
        ]
        assert plain == [], plain
        used = {
            (text["region"], styles[(text["face"], text["size"], text["weight"])])
            for text in texts
        }
        expected = {
            ("main bar", "Label"),
            ("tree", "Head"),
            ("tree", "Label"),
            ("tabs' row", "Label"),
            ("graph bar", "Head"),
            ("graph bar", "Label"),
            ("Recipe", "Code name"),
            ("Recipe", "Small"),
            ("Recipe", "Code small"),
            ("Details", "Head"),
            ("Details", "Code name"),
            ("Details", "Small"),
            ("Details", "Code small"),
            ("status line", "Small"),
            ("status line", "Code small"),
        }
        assert expected <= used, sorted(used)
        details = tab.evaluate(DETAILS_MARKS_JS)
        assert details["name"] == ["IBM Plex Mono", "12.5px", "500"], details["name"]
        assert all(
            row["printed"] == row["key"][:1].upper() + row["key"][1:] for row in details["rows"]
        ), details["rows"]
        assert details["words"] == {
            "text": "methodized, configured",
            "face": "Archivo",
            "size": "11px",
            "weight": "500",
        }, details["words"]
        styles_used = len({name for _, name in used})
        print(f"unit Q: {len(texts)} texts of the chrome in {styles_used} styles of the steps")
    finally:
        context.close()


def test_the_chrome_s_rows_stand_at_their_heights_and_on_its_text_edges(
    browser, server_on, durables_folder
):
    """Design pass 13 §4 (D1, D2, D4, D7, D9, D11, D12; Q-D6, Q-D21). At 1600 ×
    1000 with the durables model's recipe and its trellis drawn, the chrome
    runs to the window's edges: the folder, text and graph columns are 170, 645
    and 713 px and the graph's ends on the window's right edge. The main bar is
    36 px; `Files`, the tabs' row and the graph bar are 36-px bars from y = 36,
    their words on one baseline within 0.5 px; the strip and Details' head are
    28 px on one top; the status line is 24 px at the window's foot; every tree
    row is 24 px and spans its column, its twistie at 12 + 8 × its level. The
    bars' controls are 26 px. Each Recipe row at rest has its cells' first
    baselines on one line, its key's line 14 px and every other line 16 px, 8
    px of padding above and below, 48 px for two entries a cell (the fix wave
    Q3b, item 15; D21). The first
    glyph of `Files`, of the first tab, of `Semantic graph`, of the Recipe's
    heads, of `Details` and of the status line stands on its column's left edge
    plus 12, and the last toggle's glyph, `Save`'s box, the problems count,
    Details' close glyph, the strip's open-wide glyph, the status line's last
    glyph, the Files bar's last glyph and each Recipe trash's glyph end on its
    column's right edge minus 12, within 0.5 px."""
    context, tab = new_tab(browser)
    try:
        opened_backward(tab, server_on(durables_folder))
        grid = tab.evaluate(CHROME_GRID_JS)
        columns = grid["columns"]
        widths = {name: round(box["width"]) for name, box in columns.items()}
        assert widths == {"folder": 170, "file": 645, "view": 713}, widths
        assert columns["view"]["right"] == grid["window"], (columns, grid["window"])
        heights = grid["heights"]
        assert heights["main"]["height"] == 36 and heights["main"]["right"] == grid["window"], (
            heights["main"]
        )
        for name in ("files", "tabs", "graph"):
            assert (heights[name]["top"], heights[name]["height"]) == (36, 36), (
                name,
                heights[name],
            )
        assert max(grid["baselines"]) - min(grid["baselines"]) <= 0.5, grid["baselines"]
        assert heights["strip"]["height"] == heights["details"]["height"] == 28, (
            heights["strip"],
            heights["details"],
        )
        assert heights["strip"]["top"] == heights["details"]["top"], (
            heights["strip"],
            heights["details"],
        )
        assert (
            heights["status"]["height"],
            heights["status"]["bottom"],
            heights["status"]["right"],
        ) == (24, 1000, grid["window"]), heights["status"]
        assert grid["tree"], grid
        folder = columns["folder"]
        for row in grid["tree"]:
            assert row["box"]["height"] == 24 and row["box"]["left"] == folder["left"], row
            assert abs(row["box"]["width"] - folder["width"]) <= 32, row
            if row["twistie"]:
                assert row["twistie"]["left"] - folder["left"] == 12 + 8 * row["level"], row
        assert all(abs(control["height"] - 26) <= 0.01 for control in grid["controls"]), grid[
            "controls"
        ]
        assert len(grid["recipe"]) == 4 and grid["heads"]["height"] == 24, (
            grid["recipe"],
            grid["heads"],
        )
        for row in grid["recipe"]:
            # the key's line 14 px and every other line 16 px; the key's
            # baseline stands 12 px below its line's top as a value's does,
            # so that every cell starts at the row's padding, and the row
            # adds 8 px above and below (the fix wave Q3b, item 15; D21)
            stage, *kinds = row["cells"]
            assert max(row["firsts"]) - min(row["firsts"]) <= 0.5, row
            assert stage[0] == 14 and all(
                line == 16 for cell in [stage[1:], *kinds] for line in cell
            ), row
            content = max(sum(cell) for cell in [stage, *kinds])
            assert row["box"]["height"] == 8 + content + 8, (row, content)
        file, view = columns["file"], columns["view"]
        left = grid["left"]
        edges = {
            "files": folder,
            "tab": file,
            "graph": view,
            "recipe": file,
            "details": view,
            "status": folder,
        }
        for name, column in edges.items():
            assert abs(left[name]["left"] - (column["left"] + 12)) <= 1.0, (
                name,
                left[name],
                column,
            )
        right = grid["right"]
        ends = {
            "toggle": view,
            "save": file,
            "count": view,
            "close": view,
            "wide": file,
            "more": view,
            "files": folder,
        }
        for name, column in ends.items():
            assert abs(right[name]["right"] - (column["right"] - 12)) <= 0.5, (
                name,
                right[name],
                column,
            )
        for row in grid["recipe"]:
            assert abs(row["trash"]["right"] - (file["right"] - 12)) <= 0.5, row
        row_heights = [row["box"]["height"] for row in grid["recipe"]]
        print(f"unit Q: columns {widths}; baselines {grid['baselines']}; Recipe {row_heights}")
    finally:
        context.close()


def test_the_chrome_takes_three_line_values_and_one_mark_per_state(
    browser, server_on, durables_folder
):
    """Design pass 13 §5 (E1, E3, E4, E5, E9, E10, E12, E13, E16, E17; Q-D8,
    Q-D9, Q-D15). With the durables model's recipe and its trellis drawn: the
    rules under the main bar, the Files bar, the strip, Details' head and the
    Recipe's heads, above the add row and above the status line are the
    hairline; the graph bar's two selects and the canvas's control strip take
    the control border. The open toggles of the main bar and the pressed
    `Types` stand in ink-1 with no ground and a 2-px accent line as their foot;
    the active view tab has the 2-px accent line at its foot and the disabled
    one stands at 40 percent; the Inspector's active tab has the 2-px accent
    edge; the tree's open file is on the selection's wash from the column's
    edge with the 3-px accent bar at x = 0. A tree row under the pointer takes
    the hover wash in ink-1 and a toggle with the keyboard's focus the 1-px
    accent outline. The problems count is the alarm's orange with the Codicon
    `error`, an error standing in the model, and the main bar's mark paints
    ink-1. The open Recipe row takes the selected mark, the selection's wash
    and a 3-px accent bar. With `tenure` selected, Details prints its values in
    ink-2 and its names in ink-1, and its two destructive acts are text buttons
    with the Codicon `trash` after the rows and the fold `Legend`, under a
    hairline, last in Details (the fix wave Q3b, item 17; D24)."""
    context, tab = new_tab(browser)
    try:
        opened_backward(tab, server_on(durables_folder))
        hairline, edge = (
            property_color(tab, "--bl-hairline"),
            property_color(tab, "--bl-control-border"),
        )
        accent, selected, hover = (
            property_color(tab, name) for name in ("--bl-accent", "--bl-selected", "--bl-hover")
        )
        ink_1, ink_2, alarm = (
            property_color(tab, name) for name in ("--bl-ink-1", "--bl-ink-2", "--bl-alarm")
        )
        drawn = tab.evaluate(CHROME_MARKS_JS)
        for name, selector in LIBRARY_EDGES.items():
            drawn["edges"][name] = tab.locator(selector).first.evaluate(
                "(element) => getComputedStyle(element).borderTopColor"
            )
        assert set(drawn["rules"].values()) == {hairline}, (hairline, drawn["rules"])
        assert set(drawn["edges"].values()) == {edge}, (edge, drawn["edges"])
        line = {
            "content": '""',
            "height": "2px",
            "bottom": "0px",
            "ground": accent,
            "left": "0px",
            "right": "0px",
        }
        assert {toggle["fold"] for toggle in drawn["toggles"]} >= {
            "folder",
            "inspector",
            "details",
        }, drawn["toggles"]
        for toggle in [*drawn["toggles"], drawn["types"]]:
            assert (toggle["ground"], toggle["ink"], toggle["line"]) == (
                "rgba(0, 0, 0, 0)",
                ink_1,
                line,
            ), toggle
        assert drawn["trellis"] == {"line": line} and drawn["stage"] == "0.4", (
            drawn["trellis"],
            drawn["stage"],
        )
        assert drawn["inspector"].startswith(accent) and drawn["inspector"].endswith(
            "0px -2px 0px 0px inset"
        ), drawn["inspector"]
        open_file = drawn["open"]
        assert open_file["ground"] == selected and open_file["left"] == 0, open_file
        assert open_file["bar"] == {"left": "0px", "width": "3px", "ground": accent}, open_file
        assert drawn["count"]["ink"] == alarm and "codicon-error" in drawn["count"]["icon"], drawn[
            "count"
        ]
        assert drawn["brand"] == {"image": "0", "paint": ink_1}, drawn["brand"]

        # hover and focus, forced as the pointer and the keyboard set them
        row = '.bl-tree-file[data-path="declaration/trellis.yml"]'
        session = forced(tab, row, ["hover"])
        try:
            state = tab.evaluate(STATE_JS, row)
            assert (state["ground"], state["ink"]) == (hover, ink_1), state
        finally:
            session.detach()
        toggle = '.bl-main-bar .bl-toggle[data-fold="details"]'
        session = forced(tab, toggle, ["focus", "focus-visible"])
        try:
            assert tab.evaluate(STATE_JS, toggle)["outline"] == ["solid", "1px", accent], (
                tab.evaluate(STATE_JS, toggle)
            )
        finally:
            session.detach()

        # the open Recipe row takes the selected mark
        open_recipe_row(tab, "keeper_cons")
        mark = tab.evaluate(
            "() => { const s = getComputedStyle("
            "document.querySelector('.bl-recipe-row.bl-recipe-open'));"
            " return [s.backgroundColor, s.boxShadow]; }"
        )
        assert mark == [selected, f"{accent} 3px 0px 0px 0px inset"], mark

        # Details of tenure: values in ink-2, names in ink-1, the destructive
        # acts last
        tab.keyboard.press("Escape")
        tab.locator('.bf-card[aria-label="layer tenure"]').first.click()
        details, _ = wait_until(lambda: tab.evaluate(DETAILS_MARKS_JS), 30.0, "Details of tenure")
        rows = {row["key"]: row for row in details["rows"]}
        assert all(row["value"] == ink_2 for row in rows.values()), rows
        assert rows["fields"]["names"] and set(rows["fields"]["names"]) == {ink_1}, rows["fields"]
        assert (
            rows["from"]["names"]
            and set(rows["from"]["names"]) == {ink_1}
            and set(rows["from"]["heads"]) == {ink_2}
        ), rows["from"]
        removal = details["removal"]
        assert (
            removal["last"]
            and removal["after"]
            and (removal["rule"], removal["ruleWidth"]) == (hairline, "1px")
        ), removal
        words = [button["words"] for button in removal["buttons"]]
        assert (
            len(words) == 2
            and words[0].startswith("Remove from periods ")
            and words[1] == "Remove stage"
        ), removal
        for button in removal["buttons"]:
            assert (
                button["tag"] == "button"
                and "bl-text-button" in button["classes"]
                and "codicon-trash" in button["icon"]
            ), button
        acts = [button["words"] for button in removal["buttons"]]
        print(
            f"unit Q: {len(drawn['rules'])} rules, {len(drawn['edges'])} edges, "
            f"{len(drawn['toggles'])} open toggles; Details' acts {acts}"
        )
    finally:
        context.close()


# --- the fix wave Q3a: the graph after the second review round ---

# the recipe's order of the durables model's stages, by which every period stands its occurrences in rows
# (Q3a item 2; amends K-D12)
STAGE_ORDER = ("tenure", "keeper_cons", "adjuster_cons", "bequest")
# the zooms at which the edges and the names are measured (Q3a item 3; A19)
ZOOMS = (1.0, 0.75, 0.6, 0.5, 0.46)
# a selected card's ring, 5 px out and 2 px wide (spec 0.4 §5.3), the room it keeps from the region's sides once the
# view pans to it (item 8), and the room a frame's border keeps inside the region's sides at the opening (item 9)
RING_OUT, REGION_ROOM, FRAME_CLEAR = 7, 12, 24
# a frame's left padding and the room a stub keeps from a frame's border (item 6)
FRAME_LEFT, BORDER_ROOM = 8, 2

# The drawing as the region draws it, for the fix wave Q3a: the view's scale, its translation and the region's box
# on the screen; each edge with its two handles, the socket it enters (a hidden reading port of a card stands for
# its arrival tuple's first), its classes, whether it ends at a marker, the place of its target handle, its
# segments, the end of its first run, its count's text and digits, its slash's box, its title, its labels, its
# end squares and the boxes of what it paints over its line, and the centers of its press circles on the screen;
# each card port's handle, side, card, whether a cable leaves or enters it, its mark's fill, its inset edge, its
# ring, its CSS border and its center; each card's place, size, title, name (its scroll and client widths and its
# box), its inset edge, its CSS border and its box on the screen; each period's frame, open or closed, with the
# same and its name's size, ink and box, its chevron's glyph box and its ports; each boundary marker's kind,
# label box, mark box, inset edge and CSS border; each `add` control's target box and glyph box; the stage view's
# boxes and open layers with their edges; and the number of arrowheads. An edge is the inset shadow of no offset
# and no blur, `{color, width}` in the element's own pixels, and a ring the outer shadow of no offset and no blur.
DRAWING_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host');
  const flow = host.querySelector('.react-flow');
  const pane = flow.getBoundingClientRect();
  const view = new DOMMatrixReadOnly(getComputedStyle(flow.querySelector('.react-flow__viewport')).transform);
  const zoom = view.a;
  const toFlow = (x, y) => ({x: (x - pane.left - view.e) / zoom, y: (y - pane.top - view.f) / zoom});
  const box = (element) => { const r = element.getBoundingClientRect(); return {left: r.left, top: r.top, right: r.right, bottom: r.bottom}; };
  const flowBox = (element) => {
    const r = element.getBoundingClientRect(), a = toFlow(r.left, r.top), b = toFlow(r.right, r.bottom);
    return {left: a.x, top: a.y, right: b.x, bottom: b.y};
  };
  const center = (element) => { const r = element.getBoundingClientRect(); return toFlow((r.left + r.right) / 2, (r.top + r.bottom) / 2); };
  const shadows = (text) => Array.from((text || '').matchAll(
    /(rgba?\([^)]*\)|color\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px\s+(-?[\d.]+)px(?:\s+(-?[\d.]+)px)?(\s+inset)?/g),
    (f) => ({color: f[1], x: +f[2], y: +f[3], blur: +f[4], spread: +(f[5] || 0), inset: !!f[6]}));
  const edgeOf = (style) => {
    const s = shadows(style.boxShadow).find((s) => s.inset && !s.x && !s.y && !s.blur && s.spread > 0);
    return s ? {color: s.color, width: s.spread} : null;
  };
  const ringOf = (style) => {
    const s = shadows(style.boxShadow).find((s) => !s.inset && !s.x && !s.y && !s.blur && s.spread > 0);
    return s ? {color: s.color, width: s.spread} : null;
  };
  const border = (style) => parseFloat(style.borderTopWidth) || 0;
  const handles = {};
  for (const h of host.querySelectorAll('.react-flow__handle')) handles[h.dataset.handleid] = h;
  const socketOf = (handle) => {
    const element = handles[handle];
    if (!element || !element.classList.contains('bf-cable-hidden')) return handle;
    const first = element.parentElement.querySelector(':scope > .bf-cable-arrival:not(.bf-cable-hidden)');
    return first ? first.dataset.handleid : handle;
  };
  const edges = [], sources = new Set(), sockets = new Set();
  for (const edge of host.querySelectorAll('.react-flow__edge')) {
    const path = edge.querySelector('.react-flow__edge-path');
    if (!path) continue;
    const parts = [];
    for (const step of (path.getAttribute('d') || '').match(/[ML][^ML]*/g) || []) {
      const [x, y] = step.slice(1).split(',').map(Number);
      if (step[0] === 'M' || !parts.length) parts.push([]);
      parts[parts.length - 1].push({x, y});
    }
    const [sp, tp] = (edge.dataset.id || '').split('>>');
    const pair = edge.classList.contains('bf-join-pair'), shared = edge.classList.contains('bf-cable-shared');
    if (!pair) sources.add(sp);
    sockets.add(socketOf(tp));
    const count = edge.querySelector('.bf-cable-count'), bus = edge.querySelector('.bf-cable-bus');
    const target = handles[tp] ? handles[tp].closest('.react-flow__node') : null, title = edge.querySelector('title');
    edges.push({
      id: edge.dataset.id, source: sp, target: tp, socket: socketOf(tp),
      cable: edge.classList.contains('bf-cable-edge'), pair, shared, selected: edge.classList.contains('selected'),
      toMarker: !!(target && target.querySelector(':scope > .bf-marker')),
      targetAt: handles[tp] ? center(handles[tp]) : null,
      segments: parts.flatMap((part) => part.slice(1).map((p, i) => [part[i], p])),
      firstRunEnd: !pair && parts[0] && parts[0].length > 1 ? parts[0][1] : null,
      count: count ? {text: count.textContent, x: +count.getAttribute('x'), baseline: +count.getAttribute('y'),
                      advance: count.getComputedTextLength(), fill: getComputedStyle(count).fill,
                      shown: getComputedStyle(count).display !== 'none'} : null,
      slash: bus ? {box: flowBox(bus), stroke: getComputedStyle(bus).stroke, width: parseFloat(getComputedStyle(bus).strokeWidth)} : null,
      title: title ? title.textContent : null,
      labels: edge.querySelectorAll('.bf-cable-label').length,
      ends: edge.querySelectorAll('.bf-wire-end').length,
      painted: Array.from(edge.querySelectorAll('.bf-wire-end, .bf-cable-label, text.bf-join'), (e) => flowBox(e)),
      circles: Array.from(edge.querySelectorAll('.react-flow__edgeupdater'), (c) => {
        const r = c.getBoundingClientRect();
        return {end: c.classList.contains('react-flow__edgeupdater-source') ? 'writing' : 'reading',
                x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2, radius: r.width / 2};
      }),
      // the place on the screen of each movable end's port as the region writes it for the end's anchor or square,
      // the origin about which brand.css scales it (K-D23, K-D27)
      anchors: Array.from(edge.querySelectorAll('.bf-wire-end, .bf-wire-anchor'), (a) => {
        const [x, y] = a.style.transformOrigin.split(' ').map(parseFloat), m = a.ownerSVGElement.getScreenCTM();
        return {end: a.dataset.end, anchor: a.classList.contains('bf-wire-anchor'), x: m.a * x + m.c * y + m.e, y: m.b * x + m.d * y + m.f};
      }),
    });
  }
  const ports = Array.from(host.querySelectorAll('.bf-card > .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)'), (h) => {
    const before = getComputedStyle(h, '::before'), r = h.getBoundingClientRect();
    return {handle: h.dataset.handleid, side: h.dataset.side, card: h.closest('.react-flow__node').dataset.id,
            wire: h.dataset.side === 'writing' ? sources.has(h.dataset.handleid) : sockets.has(h.dataset.handleid),
            fill: before.backgroundColor, edge: edgeOf(before), ring: ringOf(before), border: border(before),
            mark: parseFloat(before.width), lit: h.classList.contains('bf-lit'), at: center(h),
            screen: {x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2}};
  });
  const place = (n) => { const f = /translate\(\s*(-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform); return f ? [+f[1], +f[2]] : [null, null]; };
  const cards = [], frames = [], boxes = [];
  for (const node of host.querySelectorAll('.react-flow__node')) {
    const [x, y] = place(node), id = node.dataset.id;
    const card = node.querySelector(':scope > .bf-card');
    if (card) {
      const name = card.querySelector(':scope > .bf-name, :scope > .bf-layer-name'), style = getComputedStyle(card);
      cards.push({id, x, y, width: node.offsetWidth, height: node.offsetHeight, title: card.getAttribute('title'),
                  label: name.textContent, name: {scroll: name.scrollWidth, client: name.clientWidth, box: box(name)},
                  edge: edgeOf(style), border: border(style), selected: card.classList.contains('selected'),
                  ring: parseFloat(style.outlineWidth) || 0, screen: box(node)});
      continue;
    }
    const element = node.querySelector(':scope > .bf-layer, :scope > .bf-box');
    if (!element) continue;
    const style = getComputedStyle(element);
    if (/^periods\[\d+\]___group___$/.test(id)) {
      const name = element.querySelector(':scope > .bf-layer-name, :scope > .bf-name');
      const chevron = element.querySelector(':scope > .bf-toggle > .codicon');
      frames.push({id, open: !element.classList.contains('bf-closed'), x, y, width: node.offsetWidth, height: node.offsetHeight,
                   edge: edgeOf(style), border: border(style),
                   name: name ? {size: getComputedStyle(name).fontSize, color: getComputedStyle(name).color, box: flowBox(name)} : null,
                   chevron: chevron ? flowBox(chevron) : null, screen: box(node),
                   ports: Array.from(element.querySelectorAll(':scope > .react-flow__handle'), (h) => (
                     {side: h.classList.contains('source') ? 'writing' : 'reading', at: center(h)}))});
    } else boxes.push({id, open: !element.classList.contains('bf-closed') && element.classList.contains('bf-layer'), x, y, width: node.offsetWidth, height: node.offsetHeight,
                       edge: edgeOf(style), border: border(style), screen: box(node)});
  }
  const markers = Array.from(host.querySelectorAll('.bf-marker'), (m) => {
    const label = m.querySelector(':scope > .bf-boundary-label'), paint = m.querySelector(':scope > .bf-marker-paint');
    const style = getComputedStyle(paint);
    return {kind: m.dataset.kind, target: m.dataset.target || null, label: label ? box(label) : null, mark: box(paint),
            edge: edgeOf(style), border: border(style), at: center(paint),
            reader: paint.classList.contains('bf-outside-mark') && !paint.classList.contains('bf-outside-writer')};
  });
  const adds = Array.from(host.querySelectorAll('.bf-add-stage, .bf-add-period'), (b) => (
    {kind: b.classList.contains('bf-add-stage') ? 'stage' : 'period', target: box(b), glyph: box(b.querySelector('.codicon'))}));
  return {zoom, view: {x: view.e, y: view.f}, region: box(flow), edges, ports, cards, frames, boxes, markers, adds,
          arrows: host.querySelectorAll('.bf-arrow').length};
}
"""

# the records of the join wires the region holds, those Python gives it (J-D33)
REGION_JOINS_JS = "() => document.querySelector('.bl-view-host').bellmanFlow.joins()"


def drawing(tab) -> dict:
    """The drawing as the region draws it (DRAWING_JS)."""
    return tab.evaluate(DRAWING_JS)


def on_screen(drawn: dict, point: dict) -> tuple[float, float]:
    """The place on the screen of the point `point` of the flow in the drawing `drawn`."""
    zoom, view, region = drawn["zoom"], drawn["view"], drawn["region"]
    return region["left"] + view["x"] + point["x"] * zoom, region["top"] + view["y"] + point["y"] * zoom


def meets(a: dict, b: dict, room: float = 0.0) -> bool:
    """Whether the boxes `a` and `b`, each `{left, top, right, bottom}`, overlap by more than `room`."""
    return (
        min(a["right"], b["right"]) - max(a["left"], b["left"]) > room
        and min(a["bottom"], b["bottom"]) - max(a["top"], b["top"]) > room
    )


def count_box(cable: dict) -> dict:
    """The box of a cable's count's digits in the flow: its left edge, the cap height CAP above its baseline, its
    advance and its baseline."""
    count = cable["count"]
    return {"left": count["x"], "top": count["baseline"] - CAP, "right": count["x"] + count["advance"], "bottom": count["baseline"]}


def touches(box: dict, segment) -> bool:
    """Whether the segment `segment`, two points, meets the box `box`."""
    a, b = segment
    return (
        max(a["x"], b["x"]) >= box["left"] and min(a["x"], b["x"]) <= box["right"]
        and max(a["y"], b["y"]) >= box["top"] and min(a["y"], b["y"]) <= box["bottom"]
    )


def crossings(edges: list[dict], room: float = 0.5) -> list[tuple]:
    """Each place where two edges of `edges` that do not enter one socket share a run or cross: two horizontal runs
    on one line or two vertical runs on one line overlapping by more than `room`, or a horizontal and a vertical run
    crossing more than `room` inside both (Q3a item 2; A17, B15)."""
    found = []
    for i, a in enumerate(edges):
        for b in edges[i + 1:]:
            if a["socket"] == b["socket"]:
                continue
            for p, q in a["segments"]:
                for r, s in b["segments"]:
                    ah, bh = abs(p["y"] - q["y"]) < 0.01, abs(r["y"] - s["y"]) < 0.01
                    ax = sorted((p["x"], q["x"])); ay = sorted((p["y"], q["y"]))
                    bx = sorted((r["x"], s["x"])); by = sorted((r["y"], s["y"]))
                    if ah and bh and abs(p["y"] - r["y"]) < room and min(ax[1], bx[1]) - max(ax[0], bx[0]) > room:
                        found.append(("shared horizontal run", a["id"], b["id"], p["y"]))
                    elif not ah and not bh and abs(p["x"] - r["x"]) < room and min(ay[1], by[1]) - max(ay[0], by[0]) > room:
                        found.append(("shared vertical run", a["id"], b["id"], p["x"]))
                    elif ah != bh:
                        hx, hy, vx, vy = (ax, p["y"], r["x"], by) if ah else (bx, r["y"], p["x"], ay)
                        if hx[0] + room < vx < hx[1] - room and vy[0] + room < hy < vy[1] - room:
                            found.append(("crossing", a["id"], b["id"], vx, hy))
    return found


def key_of(node_id: str) -> str:
    """The stage key of the node of a stage occurrence's card, `periods[1]/keeper_cons___group___`."""
    return node_id.split("/")[1][: -len(LAYER_ID_ENDING)]


def period_of(node_id: str) -> str:
    """The period of the node of a stage occurrence's card."""
    return node_id.split("/")[0]


def restricted(tab, restriction: str) -> None:
    """Restricts the trellis view to `restriction`, `periods 0–9`, where it shows another, and waits until the
    view shows it, laid out again, and stands at rest; a view that shows it already is left as it stands."""
    if restriction_shown(tab) == restriction:
        return
    restrict(tab, restriction)
    wait_until(lambda: restriction_shown(tab) == restriction, 60.0, restriction)
    wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the view of {restriction}")
    wait_until(lambda: view_still(tab), 30.0, f"the view of {restriction} at rest")


def settled(tab, pause_ms: int = 400) -> bool:
    """Whether the region's viewport and its drawing stand unchanged across `pause_ms`, for a stage file's view,
    whose page holds no recorder of layouts."""
    first = (viewport(tab), tab.evaluate(DRAWING_JS))
    tab.wait_for_timeout(pause_ms)
    return first == (viewport(tab), tab.evaluate(DRAWING_JS))


def graph_opened(tab, direction: str) -> None:
    """Chooses the trellis graph `direction` and waits until it stands at rest at its opening."""
    choose_view(tab, None, direction)
    wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the {direction} graph")
    wait_until(lambda: view_still(tab), 30.0, f"the {direction} graph at rest")


def test_a_plug_a_cable_leaves_is_filled_in_both_graphs(browser, server_on, durables_folder):
    """Q3a item 1 (A9, B18, E6; design pass 13 §1, rule 1). In each trellis graph of the durables model at periods 0
    to 2, at scale 1 and at rest, every plug a cable leaves, to a card or to a marker, draws its mark filled in the
    port ink with no edge, the plugs whose cables reach a marker among them: the two of `tenure` of periods[2] in the
    backward graph and the one of `bequest` of periods[0] in the forward graph; no plug a cable leaves is hollow."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            port_ink = property_color(tab, "--bl-graph-port")
            drawn = drawing(tab)
            plugs = [p for p in drawn["ports"] if p["side"] == "writing"]
            leaving = [p for p in plugs if p["wire"]]
            assert len(leaving) >= 8, (direction, plugs)
            for plug in leaving:
                assert plug["fill"] == port_ink and plug["edge"] is None and plug["border"] == 0, (direction, plug)
            to_markers = {e["source"] for e in drawn["edges"] if e["toMarker"]}
            reaching = [p for p in leaving if p["handle"] in to_markers]
            assert len(reaching) == (2 if direction == "backward" else 1), (direction, sorted(to_markers))
            print(f"unit Q3a: the {direction} graph's {len(leaving)} plugs filled, {len(reaching)} of them reaching a marker")
    finally:
        context.close()


def test_one_row_order_per_stage_and_no_two_cables_share_a_run_or_cross(browser, server_on, durables_folder):
    """Q3a item 2 (A17, B15; amends K-D12). In each trellis graph of the durables model at periods 0 to 2 and at
    periods 0 to 9, at scale 1: every open period stands its occurrences in the order of the recipe's `stages:`
    list, `keeper_cons` above `adjuster_cons` in one column; a card's plugs stand in the order of the cards and the
    markers their cables reach, the higher plug reaching the higher end; the two `outside` markers of periods[3]
    stand in the same order; and no two edges that do not enter one socket share a run or cross."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        record_layouts(tab)
        lay_out_left_to_right(tab)
        for restriction in ("periods 0–2", "periods 0–9"):
            restricted(tab, restriction)
            for direction in ("forward", "backward"):
                graph_opened(tab, direction)
                at_scale_one(tab)
                drawn = drawing(tab)
                cards = {c["id"]: c for c in drawn["cards"]}
                periods = sorted({period_of(id) for id in cards})
                assert len(periods) == 3, (restriction, direction, periods)
                for period in periods:
                    keeper = cards[f"{period}/keeper_cons{LAYER_ID_ENDING}"]
                    adjuster = cards[f"{period}/adjuster_cons{LAYER_ID_ENDING}"]
                    assert keeper["x"] == adjuster["x"] and keeper["y"] < adjuster["y"], (restriction, direction, period, keeper, adjuster)
                # each card's plugs in the order of the ends their cables reach
                for card in cards:
                    plugs = sorted((p for p in drawn["ports"] if p["card"] == card and p["side"] == "writing"), key=lambda p: p["at"]["y"])
                    ends = [next(e["targetAt"]["y"] for e in drawn["edges"] if e["source"] == p["handle"] and not e["pair"]) for p in plugs if p["wire"]]
                    assert ends == sorted(ends), (restriction, direction, card, ends)
                outside = sorted((m for m in drawn["markers"] if m["kind"] == "outside"), key=lambda m: m["at"]["y"])
                if outside:
                    assert [m["target"].split("/")[1] for m in outside] == ["keeper_cons", "adjuster_cons"], (restriction, direction, outside)
                found = crossings(drawn["edges"])
                assert not found, (restriction, direction, found[:6])
                print(f"unit Q3a: {restriction}, the {direction} graph's {len(drawn['edges'])} edges, none sharing a run or crossing")
    finally:
        context.close()


def test_the_edges_take_no_layout_width_and_hold_a_pixel_on_the_screen_at_every_zoom(
    browser, server_on, durables_folder
):
    """Q3a item 3 (A19, B16, C18, E8, N4; design pass 13 §1, rules 1 and 3, §2, rule 3). In each trellis graph of
    the durables model at periods 0 to 2, at the zooms 1, 0.75, 0.6, 0.5 and 0.46: no card, frame or hollow mark
    has a CSS border, and each draws its edge as an inset shadow at least 1 px on the screen; every name that fits
    its card at zoom 1 fits it at every zoom, its scroll width its client width; every cable's ends stand within
    0.25 px of their ports' centers; and a card's hover holds its whole name wherever the name overflows."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            fits = {c["id"]: c["name"]["scroll"] <= c["name"]["client"] for c in drawing(tab)["cards"]}
            assert fits and all(fits.values()), (direction, fits)
            view = viewport(tab)
            for zoom in ZOOMS:
                flow_handle(tab, "setView", {"viewport": {"x": view["x"], "y": view["y"], "zoom": zoom}, "selection": None})
                wait_until(lambda: abs(viewport(tab)["zoom"] - zoom) <= 1e-6, 5.0, f"the view at {zoom}")
                tab.evaluate(TWO_FRAMES_JS)
                drawn = drawing(tab)
                for card in drawn["cards"]:
                    if fits[card["id"]]:
                        assert card["name"]["scroll"] == card["name"]["client"], (direction, zoom, card)
                    if card["name"]["scroll"] > card["name"]["client"]:
                        assert card["title"] == card["label"], (direction, zoom, card)
                    assert card["border"] == 0 and card["edge"] and card["edge"]["width"] * zoom >= 1 - 0.01, (direction, zoom, card)
                for frame in drawn["frames"]:
                    assert frame["border"] == 0 and frame["edge"] and frame["edge"]["width"] * zoom >= 1 - 0.01, (direction, zoom, frame)
                hollow = [p for p in drawn["ports"] if p["side"] == "reading"] + [m for m in drawn["markers"] if m["reader"]]
                assert hollow, (direction, zoom)
                for mark in hollow:
                    assert mark["border"] == 0 and mark["edge"] and mark["edge"]["width"] * zoom >= 1 - 0.01, (direction, zoom, mark)
                for id, end, dx, dy in ends_of(tab.evaluate(GRAPH_JS)):
                    assert abs(dx) <= 0.25 and abs(dy) <= 0.25, (direction, zoom, id, end, dx, dy)
            print(f"unit Q3a: the {direction} graph's {len(fits)} names whole and its edges at least 1 px at {ZOOMS}")
    finally:
        context.close()


def test_a_cable_draws_no_label_and_its_count_stands_clear_in_every_state(browser, server_on, durables_folder):
    """Q3a item 4 (A20, C21, E N1; amends Q-D17 and design pass 13 §1, rule 7). In each trellis graph of the
    durables model at periods 0 to 2, at scale 1, at rest, with a cable of a branch hovered and with it selected: no
    `.bf-cable-label` is drawn; every count is drawn in ink-3 and no route, label or end square meets its digits'
    box; and the hovered cable's title begins with its branch, `keep`."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            ink_3 = property_color(tab, "--bl-ink-3")
            # the cable of the branch `keep` within periods[0], whose record names the forward route in both graphs
            writer, reader = "periods[0]/tenure", "periods[0]/keeper_cons"
            wait_until(lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)}, 30.0, f"the {direction} cable's record")

            def clear(state: str) -> dict:
                drawn = drawing(tab)
                assert all(e["labels"] == 0 for e in drawn["edges"]), (direction, state)
                segments = [s for e in drawn["edges"] for s in e["segments"]]
                painted = [b for e in drawn["edges"] for b in e["painted"]]
                counted = [e for e in drawn["edges"] if e["count"]]
                assert counted, (direction, state)
                for cable in counted:
                    assert cable["count"]["shown"] and cable["count"]["fill"] == ink_3, (direction, state, cable["count"])
                    digits = count_box(cable)
                    assert not any(touches(digits, s) for s in segments), (direction, state, cable["id"], digits)
                    assert not any(meets(digits, b) for b in painted), (direction, state, cable["id"], digits, painted)
                return drawn

            clear("at rest")
            point = tab.evaluate(JOIN_POINT_JS, [writer, reader])
            tab.mouse.move(point["x"], point["y"])
            tab.evaluate(TWO_FRAMES_JS)
            hovered = clear("hovered")
            branch = "keep"
            titled = [e for e in hovered["edges"] if e["cable"] and (e["title"] or "").split("\n")[0] == branch]
            assert titled, (direction, [e["title"] for e in hovered["edges"] if e["cable"]][:6])
            click_join(tab, writer, reader)
            tab.mouse.move(4, 4)
            at_scale_one(tab)
            wait_until(lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]] == [(writer, reader)], 10.0, "the cable selected")
            clear("selected")
            print(f"unit Q3a: the {direction} graph draws no cable label; {len(titled)} titles begin with {branch!r}")
    finally:
        context.close()


def test_a_selected_forward_cable_draws_no_end_square_and_rings_its_movable_ports(browser, server_on, durables_folder):
    """Q3a item 5 (A21; amends K-D23's squares for cables). In the forward trellis graph of the durables model at
    periods 0 to 2, the cable from `tenure` of periods[0] into `keeper_cons`, selected and read at scale 1, draws no
    `.bf-wire-end`; the mark of each end its record names movable, its plug for the writing end and its socket for
    the reading end, takes the 2-px accent ring; nothing its edge paints meets its slash or its count; and React
    Flow's press circle of each such end stands 16 px on the screen from the place the region writes for the end,
    its radius 16 px, where K-D23 drew it, beside the end's unpainted anchor."""
    writer, reader = "periods[0]/tenure", "periods[0]/keeper_cons"
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            if direction != "forward":
                continue
            accent = property_color(tab, "--bl-accent")
            wait_until(lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)}, 30.0, "the forward cable's record")
            (record,) = [j for j in tab.evaluate(REGION_JOINS_JS) if (j["from"], j["to"]) == (writer, reader)]
            assert record["movable"], record
            click_join(tab, writer, reader)
            tab.mouse.move(4, 4)
            at_scale_one(tab)
            drawn, _ = wait_until(
                lambda: (found := drawing(tab)) and any(e["selected"] and e["cable"] for e in found["edges"]) and found,
                10.0, "the selected cable")
            (cable,) = [e for e in drawn["edges"] if e["selected"] and e["cable"]]
            assert all(e["ends"] == 0 for e in drawn["edges"]), [e["id"] for e in drawn["edges"] if e["ends"]]
            ports = {p["handle"]: p for p in drawn["ports"]}
            ends = {"writing": ports[cable["source"]], "reading": ports[cable["socket"]]}
            for end in ("writing", "reading"):
                ring = ends[end]["ring"]
                if end in record["movable"]:
                    assert ring == {"color": accent, "width": 2}, (end, ends[end])
                else:
                    assert ring is None, (end, ends[end])
            for edge in drawn["edges"]:
                for painted in edge["painted"]:
                    assert not meets(painted, cable["slash"]["box"]), (edge["id"], painted, cable["slash"])
                    assert not meets(painted, count_box(cable)), (edge["id"], painted, cable["count"])
            anchors = {a["end"]: a for a in cable["anchors"]}
            assert set(anchors) == set(record["movable"]) and all(a["anchor"] for a in anchors.values()), cable["anchors"]
            for circle in cable["circles"]:
                if circle["end"] not in record["movable"]:
                    continue
                at = anchors[circle["end"]]
                assert abs(circle["radius"] - 16) <= 0.5, circle
                assert abs(abs(circle["x"] - at["x"]) - 16) <= 0.5 and abs(circle["y"] - at["y"]) <= 0.5, (circle, at)
            print(f"unit Q3a: the selected forward cable draws no end square; its movable ends {record['movable']} ringed")
    finally:
        context.close()


def test_a_stub_bends_outside_the_frame_and_every_frame_keeps_its_left_padding(browser, server_on, durables_folder):
    """Q3a item 6 (A22, B20; amends design pass 13 §1, rule 6's runs of 24 and 16). In each trellis graph of the
    durables model at periods 0 to 2, at scale 1: no segment of any route runs within 2 px of a frame's border along
    more than 2 px of it; every open frame's cards stand 8 px inside its left border; and each stub that bends
    takes its vertical run 8 px outside its frame's border, a writing stub's first run 32 px from its plug and its
    last 16 px into its mark, a reading stub's first run 16 px from its mark and its last 16 px into its socket."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            drawn = drawing(tab)
            frames = [f for f in drawn["frames"] if f["open"]]
            assert len(frames) == 3, (direction, frames)
            for frame in frames:
                left, right, top, bottom = frame["x"], frame["x"] + frame["width"], frame["y"], frame["y"] + frame["height"]
                for edge in drawn["edges"]:
                    for a, b in edge["segments"]:
                        if abs(a["x"] - b["x"]) < 0.01:
                            along = min(max(a["y"], b["y"]), bottom) - max(min(a["y"], b["y"]), top)
                            assert not (along > BORDER_ROOM and min(abs(a["x"] - left), abs(a["x"] - right)) < BORDER_ROOM), (direction, frame["id"], edge["id"], a, b)
                        else:
                            along = min(max(a["x"], b["x"]), right) - max(min(a["x"], b["x"]), left)
                            assert not (along > BORDER_ROOM and min(abs(a["y"] - top), abs(a["y"] - bottom)) < BORDER_ROOM), (direction, frame["id"], edge["id"], a, b)
                inside = [c for c in drawn["cards"] if period_of(c["id"]) + LAYER_ID_ENDING == frame["id"]]
                assert min(c["x"] for c in inside) - left == FRAME_LEFT, (direction, frame["id"], [c["x"] for c in inside], left)
            stubs = [e for e in drawn["edges"] if e["cable"] and (e["toMarker"] or e["source"].startswith(("outside:", "start:")))]
            bent = 0
            for stub in stubs:
                points = [stub["segments"][0][0]] + [b for _, b in stub["segments"]]
                runs = [abs(b["x"] - a["x"]) for a, b in stub["segments"] if abs(a["y"] - b["y"]) < 0.01]
                if len(points) < 4:
                    continue
                bent += 1
                if stub["toMarker"]:
                    assert (round(runs[0]), round(runs[-1])) == (32, 16), (direction, stub["id"], points)
                else:
                    assert (round(runs[0]), round(runs[-1])) == (16, 16), (direction, stub["id"], points)
            assert bent == 2, (direction, bent, [s["id"] for s in stubs])
            print(f"unit Q3a: the {direction} graph's routes clear of every border; {bent} stubs bent outside their frame")
    finally:
        context.close()


def grown(drawn: dict, card: dict) -> dict:
    """The box on the screen of the card `card` of the drawing `drawn` with its ring and the first runs of its
    cables, which hold their counts (Q3a item 8; A18, B19, D23)."""
    zoom, at = drawn["zoom"], card["screen"]
    box = {"left": at["left"] - RING_OUT * zoom, "top": at["top"] - RING_OUT * zoom,
           "right": at["right"] + RING_OUT * zoom, "bottom": at["bottom"] + RING_OUT * zoom}
    plugs = {p["handle"] for p in drawn["ports"] if p["card"] == card["id"] and p["side"] == "writing"}
    for edge in drawn["edges"]:
        if edge["source"] in plugs and edge["firstRunEnd"]:
            x, y = on_screen(drawn, edge["firstRunEnd"])
            box = {"left": min(box["left"], x), "top": min(box["top"], y), "right": max(box["right"], x), "bottom": max(box["bottom"], y)}
    return box


def test_a_card_selected_in_the_opening_view_stands_inside_the_region(browser, server_on, durables_folder):
    """Q3a item 8 (A18, B19, D23) and item 7 (A23). In each trellis graph of the durables model at periods 0 to 2,
    each card the opening view shows, clicked there, unfolds, and the view pans at the same scale so that the card
    with its ring and the first runs of its cables, which hold their counts, stands inside the region less 12 px at
    each side; the slashes of the selected card's lit cables keep the port ink."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        record_layouts(tab)
        lay_out_left_to_right(tab)
        for direction in ("forward", "backward"):
            graph_opened(tab, direction)
            port_ink = property_color(tab, "--bl-graph-port")
            opening = viewport(tab)
            region = drawing(tab)["region"]
            shown = [c for c in drawing(tab)["cards"] if meets(c["screen"], region, 8)]
            assert len(shown) >= 3, (direction, [c["id"] for c in shown])
            for card in shown:
                flow_handle(tab, "setView", {"viewport": {"x": opening["x"], "y": opening["y"], "zoom": opening["zoom"]}, "selection": None})
                wait_until(lambda: view_still(tab), 30.0, "the opening view again")
                at = next(c for c in drawing(tab)["cards"] if c["id"] == card["id"])
                name = at["name"]["box"]
                x = (max(name["left"], region["left"]) + min(name["right"], region["right"])) / 2
                tab.mouse.click(x, (name["top"] + name["bottom"]) / 2)
                wait_until(lambda: flow_handle(tab, "selection") == card["id"], 10.0, f"{card['id']} selected")
                wait_until(lambda: view_still(tab), 30.0, f"{card['id']} unfolded")
                drawn = drawing(tab)
                assert abs(drawn["zoom"] - opening["zoom"]) <= 1e-6, (card["id"], drawn["zoom"])
                selected = next(c for c in drawn["cards"] if c["id"] == card["id"])
                assert selected["selected"] and selected["height"] > CARD_HIGH, selected
                box = grown(drawn, selected)
                inner = {"left": region["left"] + REGION_ROOM - 1, "top": region["top"] + REGION_ROOM - 1,
                         "right": region["right"] - REGION_ROOM + 1, "bottom": region["bottom"] - REGION_ROOM + 1}
                assert inner["left"] <= box["left"] and box["right"] <= inner["right"], (direction, card["id"], box, inner)
                assert inner["top"] <= box["top"] and box["bottom"] <= inner["bottom"], (direction, card["id"], box, inner)
                for edge in drawn["edges"]:
                    if edge["slash"] and edge["slash"]["stroke"] != port_ink:
                        assert edge["selected"], (direction, card["id"], edge["id"], edge["slash"])
            print(f"unit Q3a: the {direction} graph's {len(shown)} cards of the opening view each stand inside the region once selected")
    finally:
        context.close()


def test_the_opening_view_stands_on_the_text_edge_and_cuts_no_frame_near_the_region_s_sides(
    browser, server_on, durables_folder
):
    """Q3a item 9 (D20, D3, D26). At the opening of each trellis graph of the durables model at periods 0 to 2, the
    backward graph's terminal-condition label begins at the region's left plus 12 and the forward graph's
    terminal-marker label ends at the region's right minus 12, the drawing's top 24 px below the bar; no period
    frame's border stands within 24 px inside the region's sides. At the opening of the stage graph of `tenure.bl`,
    no layer the region's side cuts has its border within 24 px inside that side, a layer standing whole being free
    to end on the text edge (D20), and the highest box or wire within the region's width stands 24 px below the
    bar."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        record_layouts(tab)
        lay_out_left_to_right(tab)
        for direction in ("forward", "backward"):
            graph_opened(tab, direction)
            drawn = drawing(tab)
            region = drawn["region"]
            kind = "start" if direction == "backward" else "end"
            (marker,) = [m for m in drawn["markers"] if m["kind"] == kind]
            if direction == "backward":
                assert abs(marker["label"]["left"] - (region["left"] + TEXT_EDGE)) <= 1, (direction, marker, region)
            else:
                assert abs(marker["label"]["right"] - (region["right"] - TEXT_EDGE)) <= 1, (direction, marker, region)
            top = min(f["screen"]["top"] for f in drawn["frames"])
            assert abs(top - (region["top"] + OPENING_TOP)) <= 1, (direction, top, region)
            for frame in drawn["frames"]:
                for side in (frame["screen"]["left"], frame["screen"]["right"]):
                    assert not (region["left"] < side < region["left"] + FRAME_CLEAR), (direction, frame["id"], side, region)
                    assert not (region["right"] - FRAME_CLEAR < side < region["right"]), (direction, frame["id"], side, region)
            print(f"unit Q3a: the {direction} graph opens on the text edge, no frame within {FRAME_CLEAR} px inside its sides")
        # the stage graph, laid out downward as it opened before design pass 14
        lay_out_top_to_bottom(tab)
        open_file(tab, url, TENURE_FILE)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        wait_until(lambda: tab.evaluate("() => document.querySelectorAll('.bl-view-host .react-flow__edge').length") == STAGE_LINES, 60.0, "the stage graph's lines")
        wait_until(lambda: settled(tab), 30.0, "the stage graph at rest")
        drawn = drawing(tab)
        region = drawn["region"]
        layers = [b for b in drawn["boxes"] if b["open"]]
        assert layers, drawn["boxes"][:4]
        for layer in layers:
            left, right = layer["screen"]["left"], layer["screen"]["right"]
            if left < region["right"] < right:
                assert left <= region["right"] - FRAME_CLEAR, (layer["id"], left, right, region)
            if left < region["left"] < right:
                assert right >= region["left"] + FRAME_CLEAR, (layer["id"], left, right, region)
        within = [b["screen"]["top"] for b in drawn["boxes"] if b["screen"]["right"] > region["left"] and b["screen"]["left"] < region["right"]]
        for edge in drawn["edges"]:
            for a, b in edge["segments"]:
                for point in (a, b):
                    x, y = on_screen(drawn, point)
                    if region["left"] <= x <= region["right"]:
                        within.append(y)
        assert abs(min(within) - (region["top"] + OPENING_TOP)) <= 1, (min(within), region)
        print(f"unit Q3a: the stage graph opens at {drawn['zoom']:.3f}, its top {min(within) - region['top']:.1f} px below the bar")
    finally:
        context.close()


def test_every_period_frame_of_periods_0_to_9_shares_one_top(browser, server_on, durables_folder):
    """Q3a item 10 (B22, D13; design pass 13 §2, rule 8, and §1, rule 4). In each trellis graph of the durables
    model at periods 0 to 9, at scale 1, every period's frame, open or closed, shares one top; a closed period's
    box draws its name in the period style, Code small in ink-3 at (9, 5), its chevron's glyph centered at (W − 14,
    14), and its reading and writing ports on its axis at y 14, two of them 12 px apart; and no arrowhead is drawn."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        record_layouts(tab)
        lay_out_left_to_right(tab)
        restricted(tab, "periods 0–9")
        for direction in ("forward", "backward"):
            graph_opened(tab, direction)
            at_scale_one(tab)
            ink_3 = property_color(tab, "--bl-ink-3")
            drawn = drawing(tab)
            frames = drawn["frames"]
            assert len(frames) == 10 and len([f for f in frames if not f["open"]]) == 7, (direction, [f["id"] for f in frames])
            assert len({f["y"] for f in frames}) == 1, (direction, sorted((f["id"], f["y"]) for f in frames))
            for frame in (f for f in frames if not f["open"]):
                name, chevron = frame["name"], frame["chevron"]
                assert (name["size"], name["color"]) == ("11px", ink_3), (direction, frame["id"], name)
                assert (round(name["box"]["left"] - frame["x"]), round(name["box"]["top"] - frame["y"])) == (9, 5), (direction, frame["id"], name)
                middle = ((chevron["left"] + chevron["right"]) / 2 - frame["x"], (chevron["top"] + chevron["bottom"]) / 2 - frame["y"])
                assert abs(middle[0] - (frame["width"] - 14)) <= 0.5 and abs(middle[1] - AXIS) <= 0.5, (direction, frame["id"], middle)
                for side in ("reading", "writing"):
                    ys = sorted(p["at"]["y"] - frame["y"] for p in frame["ports"] if p["side"] == side)
                    assert ys and abs(sum(ys) / len(ys) - AXIS) <= 0.5, (direction, frame["id"], side, ys)
                    assert all(abs(b - a - PITCH) <= 0.5 for a, b in zip(ys, ys[1:])), (direction, frame["id"], side, ys)
            assert drawn["arrows"] == 0, (direction, drawn["arrows"])
            print(f"unit Q3a: the {direction} graph's 10 frames on one top, 7 closed in the period style, no arrowhead")
    finally:
        context.close()


def test_the_add_controls_draw_at_the_view_s_scale_and_keep_their_target(browser, server_on, durables_folder):
    """Q3a item 11 (B17, C11; amends L-D5's drawn size and Q-D13). In the forward trellis graph of the durables
    model at periods 0 to 2, fitted: the glyph of `+ Stage` and of `+ Period` stands no taller on the screen than a
    card's name, and `+ Stage` keeps a press target of 24 px on the screen."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        for direction in both_graphs(tab, url, durables_folder):
            if direction != "forward":
                continue
            tab.click(".bl-zoom-button[data-zoom='fit']")
            wait_until(lambda: view_still(tab), 30.0, "the forward graph fitted")
            drawn = drawing(tab)
            assert drawn["zoom"] < SMALL, drawn["zoom"]
            name = min(c["name"]["box"]["bottom"] - c["name"]["box"]["top"] for c in drawn["cards"])
            adds = drawn["adds"]
            assert {a["kind"] for a in adds} == {"stage", "period"}, adds
            for add in adds:
                assert add["glyph"]["bottom"] - add["glyph"]["top"] <= name + 0.01, (add, name)
            for add in (a for a in adds if a["kind"] == "stage"):
                assert add["target"]["bottom"] - add["target"]["top"] >= 24 - 0.5, add
            print(f"unit Q3a: the add controls' glyphs at most {name:.2f} px tall on the screen at {drawn['zoom']:.3f}")
    finally:
        context.close()


# --- the fix wave Q3b: the chrome after the second review round ---

# A text's style as the five steps name them (TYPE_STYLES), by its face, its
# size and its weight
STEP_OF = {style: name for name, style in TYPE_STYLES.items()}

# The Recipe at the panel's default height (the fix wave Q3b, item 15; D21,
# D28): the boxes of the panel, its strip, its table and its add row; the
# table's scroll height and height; each row at rest with its box, its key's
# line, its cells' first baselines and its trash's box; and the baseline of
# the trellis row's key. A baseline is the bottom of an empty inline block
# placed at the start of its element.
RECIPE_FIT_JS = r"""
() => {
  const baseline = (element) => {
    const probe = document.createElement('span');
    probe.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
    element.insertBefore(probe, element.firstChild);
    const y = probe.getBoundingClientRect().bottom;
    probe.remove();
    return y;
  };
  const box = (element) => {
    const r = element.getBoundingClientRect();
    return {left: r.left, top: r.top, right: r.right, bottom: r.bottom,
            width: r.width, height: r.height};
  };
  const panel = document.querySelector('.bl-file .bl-classification[data-panel="recipe"]');
  const table = panel.querySelector('.bl-recipe-table');
  const trellis = table.querySelector('.bl-recipe-trellis-row');
  return {
    panel: box(panel), strip: box(panel.querySelector('.bl-inspector-strip')),
    table: box(table), scroll: table.scrollHeight, client: table.clientHeight,
    add: box(panel.querySelector('.bl-recipe-add')),
    trellisKey: baseline(trellis.querySelector('.bl-recipe-key')),
    rows: Array.from(table.querySelectorAll('.bl-recipe-row[aria-expanded="false"]'), (row) => ({
      key: row.dataset.stage, box: box(row),
      line: box(row.querySelector('.bl-recipe-key-line')),
      firsts: Array.from(row.querySelectorAll('.bl-recipe-cell'), (cell) => baseline(
        cell.querySelector('.bl-recipe-key, .bl-recipe-text, .bl-recipe-none, .bl-recipe-range'))),
      trash: box(row.querySelector(':scope > .bl-remove-stage')),
    })),
  };
}
"""
# The baseline of the words of a select of VSCode Elements, read in the
# library's own tree, which Playwright's selectors reach (Q-I96): its face's
# text element, `.text`, given
FACE_BASELINE_JS = r"""
(text) => {
  const probe = document.createElement('span');
  probe.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
  text.insertBefore(probe, text.firstChild);
  const y = probe.getBoundingClientRect().bottom;
  probe.remove();
  return y;
}
"""


def test_the_recipe_s_rows_are_48_px_and_four_stand_whole_at_the_panel_s_default_height(
    browser, server_on, durables_folder
):
    """The fix wave Q3b, item 15 (D21, D28; Q-D21). At 1600 × 1000 with the
    durables model's recipe open, the panel under the editor stands at its
    default height, 320 px, its strip 28 px. Each of the four rows at rest,
    in the recipe's order, is 48 px, 8 + 32 + 8: its key's line 14 px, 8 px
    below the row's top, the trash's target of 24 px centered on that line,
    and its cells' first baselines on one line 20 px below the row's top,
    12 px below the key line's top as below a value's line of 16 px. The
    four rows stand whole in the table, which does not scroll, and the table
    ends above the add row. The trellis row's key stands on the baseline of
    its select's words within 0.5 px."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        tab.wait_for_selector(".bl-recipe-table .bl-recipe-row", timeout=60_000)
        tab.mouse.move(1, 999)
        fit = tab.evaluate(RECIPE_FIT_JS)
        assert (fit["panel"]["height"], fit["strip"]["height"]) == (320, 28), fit
        rows = fit["rows"]
        assert [row["key"] for row in rows] == list(STAGE_ORDER), rows
        for row in rows:
            top, line, trash = row["box"]["top"], row["line"], row["trash"]
            assert (row["box"]["height"], line["height"], line["top"] - top) == (48, 14, 8), row
            assert {first - top for first in row["firsts"]} == {20}, row
            middle = (trash["top"] + trash["bottom"]) / 2
            assert trash["height"] == 24 and abs(middle - (line["top"] + 7)) <= 0.5, row
        assert fit["scroll"] <= fit["client"], fit
        assert rows[-1]["box"]["bottom"] <= fit["table"]["bottom"] <= fit["add"]["top"], fit
        text = tab.locator(".bl-recipe-trellis-row vscode-single-select .select-face .text")
        words = text.first.evaluate(FACE_BASELINE_JS)
        assert abs(fit["trellisKey"] - words) <= 0.5, (fit["trellisKey"], words)
        print(
            f"unit Q3b: Recipe rows {[row['box']['height'] for row in rows]}, the table "
            f"{fit['scroll']} of {fit['client']} px; the trellis row's key on {words}"
        )
    finally:
        context.close()


# The graph bar as its row lays it out (the fix wave Q3b, item 16; D22): the
# graph column's box; the bar's box and whether it carries data-crowded; the
# canvas's top; the name's box and text; and each other item of the bar's
# row, a child of .bl-graph-tools, a child displayed as contents counted by
# its own children, with its left edge and its middle.
GRAPH_BAR_JS = r"""
() => {
  const box = (element) => {
    const r = element.getBoundingClientRect();
    return {left: r.left, top: r.top, right: r.right, bottom: r.bottom,
            width: r.width, height: r.height};
  };
  const bar = document.querySelector('.bl-graph-bar');
  const tools = bar.querySelector('.bl-graph-tools');
  const name = tools.querySelector(':scope > .bl-graph-name');
  const items = [];
  const walk = (element) => {
    for (const child of element.children) {
      const display = getComputedStyle(child).display;
      if (display === 'contents') walk(child);
      else if (display !== 'none' && child !== name) items.push(child);
    }
  };
  walk(tools);
  return {
    column: box(document.querySelector('.bl-view')), bar: box(bar),
    crowded: bar.hasAttribute('data-crowded'),
    canvas: box(document.querySelector('.bl-canvas')).top,
    name: {...box(name), text: name.textContent},
    items: items.map((item) => {
      const r = item.getBoundingClientRect();
      return {left: r.left, middle: (r.top + r.bottom) / 2};
    }),
  };
}
"""


def test_the_graph_bar_keeps_one_row_with_matsya_open_and_its_name_stays_the_heading(
    browser, server_on, durables_folder
):
    """The fix wave Q3b, item 16 (D22). At 1600 × 1000 with tenure.bl open and
    Matsya's column open, as the page opens a stage file, the graph column is
    357 px and the bar's items with `Semantic graph` do not fit its row: the
    bar carries data-crowded and draws no name, the name's box no wider and
    no higher than 1 px, and keeps one row of 36 px from y = 36, every item's
    middle at 54 within 1 px, its first item on the column's text edge, and
    the canvas begins at 72; `Semantic graph` stays the region's heading for
    assistive technology. With Matsya folded the graph column widens, the
    bar carries no data-crowded and draws the name on the text edge in its
    one row. In the trellis view, with the editor column still open on
    tenure.bl, the graph column is 483 px, and since design pass 14 §7 put
    the kind select in the trellis's bar too (S-D18), the bar's items with
    the name no longer fit that row: the bar is crowded, draws no name and
    keeps its 36 px; the trellis's opening view with no file open, where the
    column is 713 px, draws the name (`test_unit_s.py`)."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_file(tab, url, TENURE_FILE)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        assert tab.locator(".bl-window[data-folded-matsya]").count() == 0
        wait_until(lambda: tab.evaluate(GRAPH_BAR_JS)["crowded"], 10.0, "the bar crowded")
        bar = tab.evaluate(GRAPH_BAR_JS)
        edge = bar["column"]["left"] + 12
        assert bar["column"]["width"] == FRAME_TRACKS[1600, False][2], bar
        assert (bar["bar"]["top"], bar["bar"]["height"], bar["canvas"]) == (36, 36, 72), bar
        assert bar["name"]["width"] <= 1 and bar["name"]["height"] <= 1, bar
        assert bar["name"]["text"] == "Semantic graph", bar
        assert bar["items"] and all(abs(item["middle"] - 54) <= 1 for item in bar["items"]), bar
        assert abs(bar["items"][0]["left"] - edge) <= 0.5, bar
        assert tab.get_by_role("heading", name="Semantic graph").count() == 1
        crowded = bar

        tab.click(MATSYA_TOGGLE)
        tab.wait_for_selector(".bl-window[data-folded-matsya]", state="attached", timeout=10_000)
        wait_until(lambda: not tab.evaluate(GRAPH_BAR_JS)["crowded"], 10.0, "the name drawn")
        bar = tab.evaluate(GRAPH_BAR_JS)
        edge = bar["column"]["left"] + 12
        assert bar["name"]["width"] > 80 and abs(bar["name"]["left"] - edge) <= 0.5, bar
        assert (bar["bar"]["height"], bar["canvas"]) == (36, 72), bar
        assert all(abs(item["middle"] - 54) <= 1 for item in bar["items"]), bar

        drawn = bar
        open_trellis(tab, url, RECIPE_FILE)
        wait_until(lambda: tab.locator(".bl-restriction").count() == 1, 60.0, "the trellis")
        # the trellis's bar beside the editor column: the kind select's 82 px and its 8-px gap (design pass 14
        # §7; S-D18) take the row past the 483-px column that drew the name without them
        wait_until(lambda: tab.evaluate(GRAPH_BAR_JS)["crowded"], 10.0, "the trellis's bar crowded")
        bar = tab.evaluate(GRAPH_BAR_JS)
        # the column keeps the width the stage's view had with Matsya folded, 483 px beside the editor
        assert bar["column"]["width"] == drawn["column"]["width"], (bar["column"], drawn["column"])
        assert bar["name"]["width"] <= 1 and bar["name"]["height"] <= 1, bar
        assert bar["bar"]["height"] == 36 and all(abs(item["middle"] - 54) <= 1 for item in bar["items"]), bar
        assert tab.get_by_role("heading", name="Semantic graph").count() == 1
        print(
            f"unit Q3b: the graph bar at {crowded['column']['width']} px "
            f"{crowded['bar']['height']} px high, its name not drawn; at "
            f"{drawn['column']['width']} px drawn; the trellis's beside the editor at "
            f"{bar['column']['width']} px not drawn"
        )
    finally:
        context.close()


# The blocks of Details' body in their order (the fix wave Q3b, item 17;
# D24, D25), each [class, top, bottom]: each child of the body, a selected
# occurrence's Details and a stage's view's empty Details each counted by
# their own children; the class of the body's last element; and the top of
# the removal row's first button, where the row stands.
DETAILS_BLOCKS_JS = r"""
() => {
  const body = document.querySelector('.bl-panel .bl-panel-body');
  const block = (element) => {
    const r = element.getBoundingClientRect();
    return [element.className, r.top, r.bottom];
  };
  const blocks = [];
  for (const child of body.children) {
    if (child.matches('.bl-occurrence-details, .bl-empty-panel')) {
      blocks.push(...Array.from(child.children, block));
    } else {
      blocks.push(block(child));
    }
  }
  const removal = body.querySelector(':scope > .bl-removal-buttons');
  return {
    blocks, last: body.lastElementChild.className,
    buttons: removal ? removal.firstElementChild.getBoundingClientRect().top : null,
  };
}
"""


def gaps(blocks: list) -> list[float]:
    """The space between each two blocks of Details that follow each other,
    `[class, top, bottom]` each (DETAILS_BLOCKS_JS)."""
    return [after[1] - before[2] for before, after in zip(blocks, blocks[1:])]


def test_details_blocks_stand_8_apart_and_the_removal_row_stands_last_after_the_legend(
    browser, server_on, durables_folder
):
    """The fix wave Q3b, item 17 (D24, D25; design pass 13 §§4 and 5). With
    the card `tenure` selected in the backward trellis graph, Details holds,
    in this order and 8 px apart, the occurrence's head, its rows, the piece
    buttons, the fold `Legend` and the removal row, whose hairline stands 8
    px below `Legend` and whose buttons stand 8 px below the hairline; the
    removal row is the body's last element, a destructive act last in its
    panel. In the stage view of tenure.bl with nothing selected, `No
    selection`, the sheet buttons, the rows `Periods` and the fold `Legend`
    stand 8 px apart."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        opened_backward(tab, url)
        tab.locator('.bf-card[aria-label="layer tenure"]').first.click()
        wait_until(lambda: tab.evaluate(DETAILS_MARKS_JS), 30.0, "Details of tenure")
        found = tab.evaluate(DETAILS_BLOCKS_JS)
        classes = [block[0] for block in found["blocks"]]
        assert classes == [
            "bl-panel-head",
            "bl-details-rows",
            "bl-piece-buttons",
            "bl-legend-details",
            "bl-removal-buttons",
        ], found
        assert gaps(found["blocks"]) == [8, 8, 8, 8], found
        removal = found["blocks"][-1]
        assert found["last"] == "bl-removal-buttons" and found["buttons"] - removal[1] == 9, found
        occurrence = found

        open_file(tab, url, TENURE_FILE)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        tab.wait_for_selector(".bl-panel .bl-used-at", timeout=30_000)
        found = tab.evaluate(DETAILS_BLOCKS_JS)
        classes = [block[0] for block in found["blocks"]]
        assert classes == ["bl-empty", "bl-sheet-buttons", "bl-used-at", "bl-legend-details"], (
            found
        )
        assert gaps(found["blocks"]) == [8, 8, 8], found
        print(
            f"unit Q3b: Details of an occurrence {gaps(occurrence['blocks'])} px apart, "
            f"the removal row last; of a stage's view {gaps(found['blocks'])}"
        )
    finally:
        context.close()


# The chrome's whole pixels and right text edges in a stage's view (the fix
# wave Q3b, item 18; D17, D27, D29): the main bar's and Matsya's head's bottom
# border width and box shadow; the main bar's toggles' boxes and an open
# toggle's line; Matsya's head's actions; the editor's number column and the
# refusals' gutter, and the left edge of the first line's text; each perch
# table's box; the minimap's strip, the right edge of its widest mark and
# `Save`'s box; the canvas, React Flow's attribution, its text and the foot's
# controls.
WHOLE_PIXELS_JS = r"""
() => {
  const box = (element) => {
    const r = element.getBoundingClientRect();
    return {left: r.left, top: r.top, right: r.right, bottom: r.bottom,
            width: r.width, height: r.height};
  };
  const text = (element) => {
    const range = document.createRange();
    range.selectNodeContents(element);
    const r = range.getBoundingClientRect();
    return {left: r.left, right: r.right};
  };
  const q = (selector) => document.querySelector(selector);
  const open = q('.bl-main-bar .bl-toggle[aria-expanded="true"]');
  return {
    heads: ['.bl-main-bar', '.bl-matsya > .bl-matsya-head'].map((selector) => {
      const style = getComputedStyle(q(selector));
      return {border: style.borderBottomWidth, shadow: style.boxShadow, box: box(q(selector))};
    }),
    toggles: Array.from(document.querySelectorAll('.bl-main-bar .bl-toggle'), box),
    line: open ? [getComputedStyle(open, '::after').height,
                  getComputedStyle(open, '::after').bottom] : null,
    actions: box(q('.bl-matsya-head .bl-head-actions')),
    numbers: box(q('.cm-gutter.cm-lineNumbers')), lint: box(q('.cm-gutter.cm-gutter-lint')),
    text: text(q('.cm-content .cm-line')).left,
    perches: Array.from(document.querySelectorAll('.bl-class-perch'), box),
    strip: box(q('.bl-minimap')), save: box(q('.bl-save')),
    widest: Math.max(...Array.from(document.querySelectorAll('.bl-minimap-mark'),
      (mark) => mark.getBoundingClientRect().right)),
    canvas: box(q('.bl-canvas')), attribution: box(q('.react-flow__attribution')),
    credit: text(q('.react-flow__attribution a')), controls: box(q('.bl-graph-controls')),
  };
}
"""


def test_the_chrome_stands_on_whole_pixels_and_on_its_right_text_edges(
    browser, server_on, durables_folder
):
    """The fix wave Q3b, item 18 (D17, D27, D29). At 1600 × 1000 with tenure.bl
    open and Matsya's column open: the main bar and Matsya's head draw their
    hairline as an inset shadow and no border, so that each one's content is
    its 36 px, the main bar's toggles stand from y = 5 to 31, an open
    toggle's line of 2 px at their foot, from 29 to 31, and the actions of
    Matsya's head on whole pixels, centered at 18; the editor's number column
    is 36 px, the refusals' gutter and the text after it begin on whole
    pixels, the text 8 px past the gutter; each perch table's edges stand on
    whole pixels; the minimap's widest mark ends on the column's right text
    edge, `Save`'s, 12 px inside the strip's right edge; and React Flow's
    attribution ends its text on the canvas's right text edge, 12 px in, its
    box's foot on the foot controls' foot."""
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(durables_folder), TENURE_FILE)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        tab.wait_for_selector(".bl-minimap .bl-minimap-mark", timeout=30_000)
        assert tab.locator(".bl-window[data-folded-matsya]").count() == 0
        hairline = property_color(tab, "--bl-hairline")
        found = tab.evaluate(WHOLE_PIXELS_JS)
        for head in found["heads"]:
            assert head["border"] == "0px" and head["box"]["height"] == 36, head
        main_bar, matsya_head = found["heads"]
        assert main_bar["shadow"] == f"{hairline} 0px -1px 0px 0px inset", main_bar
        # Matsya's head has no rule under it since amendment 06 §6.1, the
        # column's one separation its divider (SG4-2; SE-38)
        assert matsya_head["shadow"] == "none", matsya_head
        assert found["toggles"] and all(
            (toggle["top"], toggle["bottom"]) == (5, 31) for toggle in found["toggles"]
        ), found["toggles"]
        assert found["line"] == ["2px", "0px"], found["line"]
        actions = found["actions"]
        assert actions["top"] == round(actions["top"]), actions
        assert (actions["top"] + actions["bottom"]) / 2 == 18, actions
        numbers, lint = found["numbers"], found["lint"]
        assert numbers["width"] == 36 and lint["left"] == numbers["right"], (numbers, lint)
        assert lint["right"] == round(lint["right"]), lint
        assert found["text"] == lint["right"] + 8, (found["text"], lint)
        for perch in found["perches"]:
            assert (perch["left"], perch["right"]) == (
                round(perch["left"]),
                round(perch["right"]),
            ), found["perches"]
        edge = found["strip"]["right"] - 12
        assert found["save"]["right"] == edge and abs(found["widest"] - edge) <= 0.5, found
        canvas, attribution = found["canvas"], found["attribution"]
        assert abs(found["credit"]["right"] - (canvas["right"] - 12)) <= 0.5, found
        assert abs(attribution["bottom"] - found["controls"]["bottom"]) <= 0.5, found
        print(
            f"unit Q3b: toggles {found['toggles'][0]['top']}-{found['toggles'][0]['bottom']}, "
            f"gutter {numbers['width']} px, minimap to {found['widest']}, attribution's text to "
            f"{found['credit']['right']}"
        )
    finally:
        context.close()


# The texts the element `selector` names holds, each [text, face, size,
# weight, ink, baseline]: each text that is an element's own child, with the
# element's computed style, and the bottom of an empty inline block placed at
# the start of that element (the fix wave Q3b, item 19).
TEXT_FACES_JS = r"""
(selector) => {
  const root = document.querySelector(selector);
  if (!root) return null;
  const baseline = (element) => {
    const probe = document.createElement('span');
    probe.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
    element.insertBefore(probe, element.firstChild);
    const y = probe.getBoundingClientRect().bottom;
    probe.remove();
    return y;
  };
  const found = [];
  const walk = (element) => {
    for (const node of element.childNodes) {
      if (node.nodeType === 3 && node.textContent.trim()) {
        const style = getComputedStyle(element);
        found.push([node.textContent.trim(), style.fontFamily.split(',')[0].replace(/"/g, ''),
                    style.fontSize, style.fontWeight, style.color, baseline(element)]);
      } else if (node.nodeType === 1) {
        walk(node);
      }
    }
  };
  walk(root);
  return found;
}
"""


def styled(texts: list) -> list[tuple[str, str]]:
    """Each text of TEXT_FACES_JS with the name of its type step, None for a
    style outside the steps."""
    return [(text[0], STEP_OF.get((text[1], text[2], text[3]))) for text in texts]


def test_details_heads_and_the_page_s_words_take_their_faces_and_sentence_case(
    browser, server_on, durables_folder
):
    """The fix wave Q3b, item 19 (C1, C8, C12; resolves Q-I72). In the
    backward trellis graph: a selected period's head prints `periods[0]` in
    Code name, then its kind `Period` in Small in ink-3, and its block labels
    read `Occurrences` and `Moved by a period typed first`; a selected card's
    head prints its place `periods[2] · age 68` in Code small but the page's
    word `age` in Small; the cable of `keep` within periods[0] heads Details
    with `Join` in Head, prints its route's `branch` in Small and `keep` in
    Code small, and the states `certified` and `inferred` in Small. In the
    stage view of tenure.bl, the builder `policy` heads Details with `policy`
    in Code name, then `Builder` in Small in ink-3, its block label
    `Signature`; the box `policy:Evaluation` labels its rule `Rule`; and the
    legend's name line prints `tenure` in Code small and `methodized,
    configured` in Small in ink-2."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        opened_backward(tab, url)
        ink_2, ink_3 = (property_color(tab, name) for name in ("--bl-ink-2", "--bl-ink-3"))
        select_node(tab, f"periods[0]{LAYER_ID_ENDING}", "backward")
        occurrences = ".bl-panel .bl-occurrences li"
        wait_until(lambda: tab.locator(occurrences).count() > 0, 30.0, "a period")
        head = tab.evaluate(TEXT_FACES_JS, ".bl-panel .bl-panel-head")
        assert styled(head)[:3] == [
            ("periods[0]", "Code name"),
            ("Period", "Small"),
            ("Backward", "Small"),
        ], head
        assert head[1][4] == ink_3, head
        labels = tab.locator(".bl-panel .bl-block-label").all_text_contents()
        assert "Occurrences" in labels and "Moved by a period typed first" in labels, labels

        tab.keyboard.press("Escape")
        tab.locator('.bf-card[aria-label="layer tenure"]').first.click()
        wait_until(lambda: tab.evaluate(DETAILS_MARKS_JS), 30.0, "Details of tenure")
        head = styled(tab.evaluate(TEXT_FACES_JS, ".bl-panel .bl-panel-head"))
        assert head[:4] == [
            ("tenure", "Code name"),
            ("periods[2] ·", "Code small"),
            ("age", "Small"),
            ("68", "Code small"),
        ], head

        tab.keyboard.press("Escape")
        writer, reader = "periods[0]/tenure", "periods[0]/keeper_cons"
        wait_until(
            lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            30.0,
            "the cable of keep",
        )
        click_join(tab, writer, reader)
        wait_until(
            lambda: tab.locator('.bl-panel .bl-details-row[data-key="wires"]').count() == 1,
            30.0,
            "Details of the cable",
        )
        cable = styled(tab.evaluate(TEXT_FACES_JS, ".bl-panel .bl-panel-body"))
        assert cable[0] == ("Join", "Head"), cable
        assert ("branch", "Small") in cable and ("keep", "Code small") in cable, cable
        assert ("certified", "Small") in cable, cable
        inferred = [text for text in cable if text[0] == "inferred"]
        assert inferred and set(inferred) == {("inferred", "Small")}, cable

        open_file(tab, url, TENURE_FILE)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        wait_until(
            lambda: tab.evaluate(
                "() => document.querySelectorAll('.bl-view-host .react-flow__edge').length"
            )
            == STAGE_LINES,
            60.0,
            "the stage graph's lines",
        )
        name = tab.evaluate(TEXT_FACES_JS, ".bl-panel .bl-legend-name")
        assert styled(name) == [("tenure", "Code small"), ("methodized, configured", "Small")], (
            name
        )
        assert name[1][4] == ink_2, name
        select_node(tab, f"policy{LAYER_ID_ENDING}", "backward")
        wait_until(lambda: tab.locator(".bl-panel .bl-panel-head").count() == 1, 30.0, "policy")
        head = tab.evaluate(TEXT_FACES_JS, ".bl-panel .bl-panel-head")
        assert styled(head)[:2] == [("policy", "Code name"), ("Builder", "Small")], head
        assert head[1][4] == ink_3, head
        labels = tab.locator(".bl-panel .bl-block-label").all_text_contents()
        assert "Signature" in labels, labels
        select_node(tab, "policy:Evaluation", "backward")
        wait_until(lambda: tab.locator(".bl-panel .bl-math-label").count() > 0, 30.0, "a box")
        labels = tab.locator(".bl-panel .bl-math-label").all_text_contents()
        assert "Rule" in labels and all(label[:1].isupper() for label in labels), labels
        print(f"unit Q3b: heads in Code name and Small, words in Small; the box's labels {labels}")
    finally:
        context.close()


# The main bar's path and the select after it, the status line's occurrence,
# in a stage's view (the fix wave Q3b, item 19; C19, C20): the path's text;
# each part's text, face, size, weight and whether it is marked as naming the
# occurrence; whether a path note stands; and the occurrence of the status
# line with its face, size and weight.
MAIN_PATH_JS = r"""
() => {
  const face = (element) => {
    const style = getComputedStyle(element);
    return [style.fontFamily.split(',')[0].replace(/"/g, ''), style.fontSize, style.fontWeight];
  };
  const stage = document.querySelector('.bl-status-stage');
  return {
    path: document.querySelector('.bl-crumbs').textContent,
    parts: Array.from(document.querySelectorAll('.bl-crumbs .bl-crumb'), (part) => [
      part.textContent, ...face(part), part.classList.contains('bl-occurrence-crumb')]),
    note: document.querySelectorAll('.bl-main-bar .bl-path-note').length,
    stage: stage ? [stage.textContent, ...face(stage)] : null,
  };
}
"""
# The baselines of each item of the stage list over the graph: its key's, its
# model folder's and its word `listed`'s, where it holds them (C22)
STAGE_LIST_BASELINES_JS = r"""
() => {
  const baseline = (element) => {
    const probe = document.createElement('span');
    probe.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
    element.appendChild(probe);
    const y = probe.getBoundingClientRect().bottom;
    probe.remove();
    return y;
  };
  return Array.from(document.querySelectorAll('.bl-view-host .bf-stage-list .bf-stage-item'),
    (item) => Array.from(item.querySelectorAll(
      ':scope > .bf-stage-key, :scope > .bf-stage-model, :scope > .bf-stage-listed'), baseline));
}
"""
# The rows of the Types panel's three perch tables, each row's top, and the
# placeholder of the add row's entry with its face, size, weight and ink (C22,
# C23), with the color the panel's placeholder ink computes to, read from an
# element of the panel that draws it
TYPES_ROWS_JS = r"""
() => {
  const input = document.querySelector('.bl-class-tables input[placeholder]');
  const style = input ? getComputedStyle(input, '::placeholder') : null;
  const probe = document.createElement('span');
  probe.style.color = 'var(--bl-class-placeholder)';
  document.querySelector('.bl-classification').appendChild(probe);
  const ink = getComputedStyle(probe).color;
  probe.remove();
  return {
    ink,
    tables: Array.from(document.querySelectorAll('.bl-class-tables .bl-class-perch'),
      (perch) => Array.from(perch.querySelectorAll('tr'),
        (row) => row.getBoundingClientRect().top)),
    placeholder: style ? [input.getAttribute('placeholder'),
      style.fontFamily.split(',')[0].replace(/"/g, ''), style.fontSize, style.fontWeight,
      style.color] : null,
  };
}
"""


def test_the_path_the_status_line_the_lists_and_the_types_tables_take_their_faces_and_rows(
    browser, server_on, scratch_durables
):
    """The fix wave Q3b, item 19 (C12, C19, C20, C22, C23). In the stage view
    of tenure.bl at 1600 × 1000: the main bar's path names the occurrence
    once, `durables › spec.yml › tenure › periods[0]`, every part in Label,
    the last two marked as naming the occurrence, no path note after it, and
    the select of the positions prints its words in ink-2 at rest and in
    ink-1 under the pointer; the status line prints `periods[0] / tenure` in
    Code small; the three perch tables of the Types panel stand their rows on
    one grid of 24 px, the continuation's branches' rows on the rows of the
    arrival's table; and the add row's placeholder `New field` is Small in
    the placeholder's ink. In the forward trellis graph each item of the
    stage list prints its key, its model folder and `listed` on one baseline
    within 0.25 px; and the cable's list that a move of a join wire's reading
    end opens is named `Join`, its foot's buttons `Cancel` and `Join`, which
    closes with no move written."""
    context, tab = new_tab(browser)
    try:
        url = server_on(scratch_durables)
        open_file(tab, url, TENURE_FILE)
        tab.wait_for_selector(".bl-classification .bl-class-row", timeout=60_000)
        tab.wait_for_selector(".bl-main-bar .bl-recipe-positions vscode-single-select")
        found = tab.evaluate(MAIN_PATH_JS)
        assert found["path"] == "durables › spec.yml › tenure › periods[0]", found
        assert [part[1:4] for part in found["parts"]] == [["Archivo", "13px", "400"]] * 4, found
        assert [part[4] for part in found["parts"]] == [False, False, True, True], found
        assert found["note"] == 0, found
        assert found["stage"] == ["periods[0] / tenure", "IBM Plex Mono", "11px", "400"], found
        ink_1, ink_2 = (property_color(tab, name) for name in ("--bl-ink-1", "--bl-ink-2"))
        positions = ".bl-main-bar .bl-recipe-positions vscode-single-select"
        face = tab.locator(f"{positions} .select-face").first
        assert face.evaluate("(face) => getComputedStyle(face).color") == ink_2
        session = forced(tab, positions, ["hover"])
        try:
            assert face.evaluate("(face) => getComputedStyle(face).color") == ink_1
        finally:
            session.detach()
        rows = tab.evaluate(TYPES_ROWS_JS)
        origin = rows["tables"][0][0]
        assert len(rows["tables"]) == 3 and all(rows["tables"]), rows
        for table in rows["tables"]:
            assert all((top - origin) % 24 == 0 for top in table), (origin, rows["tables"])
        assert rows["placeholder"][:4] == ["New field", "Archivo", "11px", "500"], rows
        assert rows["placeholder"][4] == rows["ink"], rows

        open_trellis(tab, url, RECIPE_FILE)
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph")
        wait_until(lambda: view_still(tab), 30.0, "the forward graph at rest")
        open_stage_list(tab)
        baselines = tab.evaluate(STAGE_LIST_BASELINES_JS)
        assert baselines and all(
            max(item) - min(item) <= 0.25 for item in baselines if len(item) > 1
        ), baselines
        tab.keyboard.press("Escape")
        tab.wait_for_selector(".bl-view-host .bf-stage-list", state="detached", timeout=10_000)

        writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
        hold_events(tab, "moved")
        click_join(tab, writer, reader)
        arrival = cable_port(tab, "periods[0]/bequest", "reading")
        move_join_end(tab, writer, reader, "target", arrival)
        pair_list = ".bl-view-host .bf-pair-list"
        tab.wait_for_selector(pair_list, timeout=10_000)
        words = [
            tab.locator(f"{pair_list} {part}").first.text_content()
            for part in (".bf-list-name", ".bf-pair-cancel", ".bf-pair-join")
        ]
        assert words == ["Join", "Cancel", "Join"], words
        tab.click(f"{pair_list} .bf-pair-cancel")
        tab.wait_for_selector(pair_list, state="detached", timeout=10_000)
        assert release_events(tab, "moved") == []
        print(f"unit Q3b: {found['path']!r}; the join list's words {words}")
    finally:
        context.close()


# The computed ground, ink, edge, radius, shadow and underline of the first
# element the selector given names (the fix wave Q3b, item 20)
LOOK_JS = r"""
(selector) => {
  const element = document.querySelector(selector);
  if (!element) return null;
  const style = getComputedStyle(element);
  const r = element.getBoundingClientRect();
  return {ground: style.backgroundColor, ink: style.color, shadow: style.boxShadow,
          edge: [style.borderTopWidth, style.borderTopStyle, style.borderTopColor],
          radius: style.borderTopLeftRadius, underline: style.textDecorationLine,
          left: r.left, right: r.right, inner: r.left + element.clientLeft + element.clientWidth};
}
"""
# The same of an element made for the reading and removed after it: the
# element `html` holds placed in the first element `parent` names, and the
# look of the element that `selector` names within it, so that the rules of
# a state the page draws only in a gesture or an event, the editor's lint
# tooltip, a Vuetify overlay and the active box of the block under the
# cursor, are read where they apply
PROBE_LOOK_JS = r"""
([parent, html, selector]) => {
  const holder = document.createElement('div');
  holder.innerHTML = html;
  const placed = holder.firstElementChild;
  document.querySelector(parent).appendChild(placed);
  const element = placed.matches(selector) ? placed : placed.querySelector(selector);
  const style = getComputedStyle(element);
  const found = {ground: style.backgroundColor, ink: style.color, shadow: style.boxShadow,
                 edge: [style.borderTopWidth, style.borderTopStyle, style.borderTopColor],
                 radius: style.borderTopLeftRadius};
  placed.remove();
  return found;
}
"""
# The elements made for PROBE_LOOK_JS: the active box of a block's list, the
# editor's lint tooltip, and a Vuetify overlay that holds a list
ACTIVE_BOX = '<ul class="bl-block-nodes"><li class="bl-active">x</li></ul>'
LINT_TOOLTIP = '<div class="cm-tooltip">x</div>'
VUETIFY_OVERLAY = (
    '<div class="v-overlay-container"><div class="v-overlay__content">'
    '<div class="v-list">x</div></div></div>'
)
# The overlays' shadow as the page computes it, read from an element that
# draws it
OVERLAY_SHADOW_JS = r"""
() => {
  const probe = document.createElement('div');
  probe.style.boxShadow = 'var(--bl-overlay-shadow)';
  document.body.appendChild(probe);
  const shadow = getComputedStyle(probe).boxShadow;
  probe.remove();
  return shadow;
}
"""


def test_the_chrome_s_inks_and_states_after_the_second_review(browser, server_on, durables_folder):
    """The fix wave Q3b, item 20 (E N2, N3, N6, N7, N8, N10c). With the
    durables model's trellis drawn: the Inspector's context `spec.yml` is
    ink-2; a period frame's chevron under the pointer turns ink-1 with no
    fill, and so does a closed period's at periods 0 to 9; the restriction's
    face stays
    raised under the pointer, its words turning ink-1, as the select's; with
    periods[0] selected, an item of its occurrences spans Details from edge
    to edge and under the pointer takes the hover wash in ink-1, and with a
    card selected a link of its rows turns ink-1 and underlined under the
    pointer; the active box of the block under the cursor stands on the
    selection's wash with the 3-px accent bar; a ticked stage of the form
    `add period` stands selected, on the selection's wash with the bar; and
    the editor's lint tooltip and a Vuetify overlay stand raised within the
    control border, a radius of 4 px and the overlays' shadow, a Vuetify list
    within one on its ground."""
    context, tab = new_tab(browser)
    try:
        opened_backward(tab, server_on(durables_folder))
        ink_1, ink_2 = (property_color(tab, name) for name in ("--bl-ink-1", "--bl-ink-2"))
        hover, selected, accent, raised, edge = (
            property_color(tab, name)
            for name in (
                "--bl-hover",
                "--bl-selected",
                "--bl-accent",
                "--bl-raised",
                "--bl-control-border",
            )
        )
        shadow = tab.evaluate(OVERLAY_SHADOW_JS)
        assert tab.evaluate(LOOK_JS, ".bl-file .bl-inspector-file")["ink"] == ink_2

        # a chevron of the graph under the pointer, ink-1 and no fill
        chevron = (
            f'.bl-view-host .react-flow__node[data-id="periods[0]{LAYER_ID_ENDING}"]'
            " > .bf-layer > .bf-toggle"
        )
        session = forced(tab, chevron, ["hover"])
        try:
            look = tab.evaluate(LOOK_JS, chevron)
            assert (look["ink"], look["ground"]) == (ink_1, "rgba(0, 0, 0, 0)"), look
        finally:
            session.detach()

        # the restriction's face under the pointer
        face = tab.locator(".bl-graph-bar vscode-button.bl-restriction .base").first
        ground = "(base) => [getComputedStyle(base).backgroundColor, getComputedStyle(base).color]"
        assert face.evaluate(ground)[0] == raised
        session = forced(tab, ".bl-graph-bar vscode-button.bl-restriction", ["hover"])
        try:
            assert face.evaluate(ground) == [raised, ink_1], face.evaluate(ground)
        finally:
            session.detach()

        # a list's item of Details, edge to edge, and its hover
        select_node(tab, f"periods[0]{LAYER_ID_ENDING}", "backward")
        item = ".bl-panel .bl-occurrences li"
        wait_until(lambda: tab.locator(item).count() > 0, 30.0, "periods[0]'s occurrences")
        panel = tab.evaluate(LOOK_JS, ".bl-panel .bl-panel-body")
        look = tab.evaluate(LOOK_JS, item)
        assert look["left"] == panel["left"] and look["right"] == panel["inner"], (look, panel)
        session = forced(tab, item, ["hover"])
        try:
            look = tab.evaluate(LOOK_JS, item)
            assert (look["ground"], look["ink"]) == (hover, ink_1), look
        finally:
            session.detach()

        # a link of a card's rows under the pointer
        tab.keyboard.press("Escape")
        tab.locator('.bf-card[aria-label="layer tenure"]').first.click()
        link = '.bl-panel .bl-details-row[data-key="file"] span.bl-link'
        wait_until(lambda: tab.locator(link).count() > 0, 30.0, "the card's file link")
        session = forced(tab, link, ["hover"])
        try:
            look = tab.evaluate(LOOK_JS, link)
            assert (look["ink"], look["underline"]) == (ink_1, "underline"), look
        finally:
            session.detach()

        # the active box of the block under the cursor, the lint tooltip and a
        # Vuetify overlay, read on elements made for the reading
        active = tab.evaluate(PROBE_LOOK_JS, [".bl-panel .bl-panel-body", ACTIVE_BOX, "li"])
        assert (active["ground"], active["shadow"], active["ink"]) == (
            selected,
            f"{accent} 3px 0px 0px 0px inset",
            ink_1,
        ), active
        tooltip = tab.evaluate(PROBE_LOOK_JS, [".bl-file .cm-editor", LINT_TOOLTIP, ".cm-tooltip"])
        overlay = tab.evaluate(PROBE_LOOK_JS, ["body", VUETIFY_OVERLAY, ".v-overlay__content"])
        for look in (tooltip, overlay):
            assert (look["ground"], look["edge"], look["radius"], look["shadow"]) == (
                raised,
                ["1px", "solid", edge],
                "4px",
                shadow,
            ), (look, tooltip, overlay)
        listed = tab.evaluate(PROBE_LOOK_JS, ["body", VUETIFY_OVERLAY, ".v-list"])
        assert (listed["ground"], listed["radius"], listed["shadow"]) == (
            "rgba(0, 0, 0, 0)",
            "0px",
            "none",
        ), listed

        # a ticked stage of the form `add period`
        tab.keyboard.press("Escape")
        choose_view(tab, None, "forward")
        wait_until(lambda: view_still(tab), 30.0, "the forward graph at rest")
        form = open_page_form(tab, "add period")
        stage = f"{form} .bl-period-stage"
        tab.wait_for_selector(stage, timeout=10_000)
        tab.locator(stage).first.click()
        wait_until(lambda: tab.locator(f"{stage}.bl-active").count() == 1, 10.0, "a ticked stage")
        look = tab.evaluate(LOOK_JS, f"{stage}.bl-active")
        bar = f"{accent} 3px 0px 0px 0px inset"
        assert (look["ground"], look["shadow"]) == (selected, bar), look
        tab.keyboard.press("Escape")
        tab.wait_for_selector(form, state="detached", timeout=10_000)

        # a closed period's chevron under the pointer at periods 0 to 9
        restricted(tab, "periods 0–9")
        closed = ".bl-view-host .bf-period-closed > .bf-toggle"
        wait_until(lambda: tab.locator(closed).count() > 0, 30.0, "the closed periods")
        session = forced(tab, closed, ["hover"])
        try:
            look = tab.evaluate(LOOK_JS, closed)
            assert (look["ink"], look["ground"]) == (ink_1, "rgba(0, 0, 0, 0)"), look
        finally:
            session.detach()
        print("unit Q3b: contexts in ink-2; chevrons, lists and links in ink-1 under the pointer")
    finally:
        context.close()
