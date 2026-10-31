"""The tests of unit P of Bellman Workbench, design pass 12 of 16 October
2026 (AAS: "why are there three wires coming out of period 0 in the
backward graph for durables?"), the development repository's record of
design pass 12, one cable per route and the count at the plug:
the backward trellis graph draws one cable for each route, from a plug of
its own on the writer's card into the reader's one socket, and one
`outside` marker for each occurrence its routes reach outside the drawn
periods (§2); a cable is one stroke at a wire's weight (§1), and a cable
that carries more than one wire shows their count at its plug by a bus
mark (§3). The durables model's copy is read at periods 0 to 2, the
restriction its trellis of 51 periods opens with."""

from __future__ import annotations

import math
from collections import Counter

from workbench_support import (
    DETAILS_ROWS_JS,
    HELD_COLLECTION_JS,
    JOIN_POINT_JS,
    RECIPE_FILE,
    VIEW_STATE_JS,
    choose_view,
    click_join,
    flow_handle,
    graph_named,
    join_wires_drawn,
    lay_out_left_to_right,
    new_tab,
    open_trellis,
    property_color,
    record_layouts,
    restriction_shown,
    view_still,
    viewport,
    wait_until,
)

from bellman.stage import LAYER_ID_ENDING

# the occurrences of periods[3] that the routes leaving periods 0 to 2 reach
PERIOD_3 = ["periods[3]/adjuster_cons", "periods[3]/keeper_cons"]
# the functions `tenure` writes at its arrival, which each reader of the
# next period reads at its continuation: the value and two marginal values
TENURE_VALUES = {"𝑉", "𝑑𝑉_a", "𝑑𝑉_h"}
# the readers in periods[1] of `tenure` of periods[0], each by its own route
TENURE_READERS = ["periods[1]/keeper_cons", "periods[1]/adjuster_cons"]
# the height of a card whose fields are all joined, its axis, on which its
# socket and a single plug stand, and the space between the centers of two
# plugs of one edge, at scale 1 (design pass 13 §2; the layout's G.cardH,
# G.cardAxis and G.cablePitch)
CARD_HIGH, CARD_AXIS, PLUG_PITCH = 32, 14, 12

# The cables' ports the region shows on the card whose node is `box`, a
# reading port hidden behind the first left out: each with its side,
# whether a cable joins it to another card, and its center on the screen;
# and the card's box on the screen.
CARD_PORTS_JS = r"""
(box) => {
  const node = document.querySelector(`.bl-view-host .react-flow__node[data-id="${CSS.escape(box)}"]`);
  if (!node) return null;
  const card = node.getBoundingClientRect();
  return {
    card: {top: card.top, bottom: card.bottom, left: card.left, right: card.right},
    ports: Array.from(
      node.querySelectorAll('.bf-card > .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)'), (port) => {
        const at = port.getBoundingClientRect();
        return {side: port.dataset.side, joined: port.classList.contains('bf-cable-joined'),
                x: (at.left + at.right) / 2, y: (at.top + at.bottom) / 2};
      }),
  };
}
"""
# The cable whose record runs from the stage occurrence `from` to `to`: its
# label's text and opacity as the browser computes it, null where it draws
# none, the count its bus mark prints, null where it draws none, its stroke
# as the browser computes it, and the text of its title, its hover; null
# where the cable is not drawn (design pass 13 §1, rules 5 and 7).
CABLE_LABEL_JS = r"""
([from, to]) => {
  const edge = document.querySelector(
    `.bl-view-host .react-flow__edge.bf-join-wire[data-from="${from}"][data-to="${to}"]`);
  if (!edge) return null;
  const label = edge.querySelector('.bf-join.bf-cable-label'), count = edge.querySelector('.bf-cable-count');
  return {text: label ? label.textContent : null, opacity: label ? getComputedStyle(label).opacity : null,
          count: count ? count.textContent : null,
          stroke: getComputedStyle(edge.querySelector('.bf-cable-outer')).stroke,
          title: (edge.querySelector('title') || {}).textContent || ''};
}
"""
# The `outside` markers the region draws, each with its target, and the
# dashed stubs, each by the id of its edge.
OUTSIDE_JS = r"""
() => ({
  markers: Array.from(document.querySelectorAll('.bl-view-host .bf-marker[data-kind="outside"]'),
                      (marker) => marker.dataset.target),
  stubs: Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge.bf-cable-edge'))
    .filter((edge) => edge.querySelector('.bf-cable-dashed')).map((edge) => edge.dataset.id),
})
"""


def routes_of(graph: dict) -> Counter:
    """Each route of the trellis graph `graph` whose two occurrences the
    view draws, as the pair of the route's source and destination its
    edges' records name, counted once."""
    found = set()
    for node in graph["nodes"]:
        for edge in node.get("incomingEdges") or []:
            for pair in edge.get("attrs") or []:
                if pair["key"] == "route":
                    route = pair["value"]
                    found.add((route["source"], route["destination"], route["branch"]))
    return Counter((source, destination) for source, destination, _ in found)


def test_the_backward_graph_draws_one_cable_for_each_route_from_a_plug_of_its_own_into_one_socket(
    browser, server_on, durables_folder
):
    """Design pass 12 §2. On a copy of the durables model at periods 0 to
    2, the backward trellis graph draws each route of the view as one
    cable, a join wire whose record names the route: `tenure` of periods[0]
    carries one plug for each of its two routes, into `keeper_cons` and
    `adjuster_cons` of periods[1], joined and G.cablePitch, 12 px, apart at
    scale 1 about the middle of its card's edge, and each reader one
    socket, the plugs about the card's axis; the cable into `keeper_cons`
    counts its three wires at its plug and, hovered, stands in ice-3 and
    prints no label, its route having no branch, its hover naming the
    value and the two marginal values it carries (design pass 13 §1, rules
    5 and 7); selected, it is named in Details by its route, its
    status and its three wires, the pairs of its route as a forward cable
    lists them, and it stays one cable; the routes into periods[3] end at
    two `outside` markers, one for each occurrence they reach, each after
    one dashed stub from its own plug on `tenure` of periods[2], drawn
    filled, `bf-cable-joined`, since a cable leaves it (the fix wave Q3a of
    unit Q, item 1; A9)."""
    tenure = f"periods[0]/tenure{LAYER_ID_ENDING}"
    reader = TENURE_READERS[0]
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        # each graph chosen, so that its layout is recorded; the backward one last
        for direction in ("forward", "backward"):
            record_layouts(tab)
            choose_view(tab, None, direction)
            wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the {direction} graph")
        wait_until(lambda: view_still(tab), 30.0, "the backward graph at rest")
        backward = graph_named(tab.evaluate(HELD_COLLECTION_JS), "backward")
        routes = routes_of(backward)
        assert len(routes) == 12, routes

        # one cable for each route, a join wire whose record names it, the
        # records found once Python's records of the cables reach the region
        drawn, _ = wait_until(
            lambda: (found := Counter((w["from"], w["to"]) for w in join_wires_drawn(tab)))
            == routes
            and found,
            10.0,
            "one cable for each route, with its record",
        )

        # one plug for each route on tenure of periods[0], G.cablePitch apart
        # about the card's axis at scale 1, the card G.cardH high, and one
        # socket on each reader
        view = viewport(tab)
        flow_handle(
            tab,
            "setView",
            {"viewport": {"x": view["x"], "y": view["y"], "zoom": 1.0}, "selection": None},
        )
        wait_until(lambda: viewport(tab)["zoom"] == 1.0, 5.0, "the view at scale 1")
        found = tab.evaluate(CARD_PORTS_JS, tenure)
        plugs = sorted(
            (port for port in found["ports"] if port["side"] == "writing"), key=lambda p: p["y"]
        )
        assert [port["joined"] for port in plugs] == [True, True], found
        assert abs(plugs[1]["y"] - plugs[0]["y"] - PLUG_PITCH) <= 0.5, plugs
        middle = (plugs[0]["y"] + plugs[1]["y"]) / 2 - found["card"]["top"]
        assert abs(middle - CARD_AXIS) <= 0.5, (middle, found)
        assert abs(found["card"]["bottom"] - found["card"]["top"] - CARD_HIGH) <= 0.5, found["card"]
        assert all(abs(port["x"] - found["card"]["right"]) <= 0.5 for port in plugs), found
        for occurrence in TENURE_READERS:
            card = tab.evaluate(CARD_PORTS_JS, occurrence + LAYER_ID_ENDING)
            sockets = [port for port in card["ports"] if port["side"] == "reading"]
            assert len(sockets) == 1 and abs(sockets[0]["x"] - card["card"]["left"]) <= 0.5, card

        # the cable into keeper_cons counts its wires at its plug and, hovered,
        # stands in ice-3 and prints no label, its route having no branch; its
        # hover names the three functions it carries
        tab.click(".bl-zoom-button[data-zoom='fit']")
        wait_until(lambda: view_still(tab), 30.0, "the backward graph fitted")
        point = tab.evaluate(JOIN_POINT_JS, [reader, "periods[0]/tenure"])
        assert point is not None
        ice = property_color(tab, "--bl-ice-3")
        tab.mouse.move(point["x"], point["y"])
        label, _ = wait_until(
            lambda: (found := tab.evaluate(CABLE_LABEL_JS, [reader, "periods[0]/tenure"]))
            and found["stroke"] == ice
            and found,
            5.0,
            "the hovered cable in ice-3",
        )
        assert label["text"] is None and label["count"] == str(len(TENURE_VALUES)), label
        named = {line.split("≺")[0] for line in label["title"].split("\n") if "≺" in line}
        assert named == TENURE_VALUES, label["title"]

        # selected, the cable is named in Details by its route, its status and
        # its wires, and stays one cable
        click_join(tab, reader, "periods[0]/tenure")
        wait_until(
            lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]]
            == [(reader, "periods[0]/tenure")],
            10.0,
            "the cable selected",
        )
        (head, rows), _ = wait_until(
            lambda: (found := tab.evaluate(DETAILS_ROWS_JS))[0].startswith("Join") and found,
            10.0,
            "Details of the selected cable",
        )
        # a join's head in sentence case (the fix wave Q3b, item 19; C12)
        assert head.startswith(f"Join {reader} → periods[0]/tenure"), head
        assert [key for key, _ in rows][:3] == ["route", "status", "wires"], rows
        found = dict(rows)
        assert found["route"] == [f"{reader} ≻ → periods[0]/tenure ≺"], found["route"]
        assert found["status"] == ["certified"], found["status"]
        assert found["wires"] == [
            "a_nxt_kp → a ℝ₊ · authored, trellis.yml 20",
            "h_nxt_kp → h ℝ₊₊ · authored, trellis.yml 20",
            "z_nxt_kp → z ℝ₊₊ · authored, trellis.yml 20",
        ], found["wires"]
        assert Counter((w["from"], w["to"]) for w in join_wires_drawn(tab)) == routes

        # one `outside` marker for each occurrence of periods[3] reached, each
        # after one dashed stub from its own plug on tenure of periods[2],
        # drawn filled since a cable leaves it (the fix wave Q3a, item 1)
        outside = tab.evaluate(OUTSIDE_JS)
        assert sorted(outside["markers"]) == PERIOD_3, outside
        writer = f"periods[2]/tenure{LAYER_ID_ENDING}"
        assert len(outside["stubs"]) == len(PERIOD_3), outside
        assert all(stub.startswith(f"{writer}::out::") for stub in outside["stubs"]), outside
        assert len({stub.split(">>")[0] for stub in outside["stubs"]}) == len(PERIOD_3), outside
        stubs = tab.evaluate(CARD_PORTS_JS, writer)
        assert [port["joined"] for port in stubs["ports"] if port["side"] == "writing"] == [
            True,
            True,
        ], stubs
        print(
            f"unit P: {len(routes)} routes drawn as {sum(drawn.values())} cables, tenure's plugs "
            f"{plugs[1]['y'] - plugs[0]['y']:.2f} px apart, {len(outside['markers'])} outside markers"
        )
    finally:
        context.close()


# A cable's stroke at a wire's weight, 1.3 px at scale 1 and at least 1 px
# on the screen (design pass 13 §1, rules 3 and 4), and the bus mark of a
# cable that carries more than one wire (rule 5): a slash BUS_LENGTH px
# long at 45 degrees across the cable's first run, its middle BUS_ALONG px
# along the run from the plug's center, 8 px from the plug's face, BUS_WIDTH
# thick at scale 1 in the port ink, and the count of the wires in Mark,
# COUNT_SIZE, ink-3, its left edge BUS_GAP px past the slash's right end,
# its baseline BUS_GAP px above the slash's upper end, or, for a cable
# from the lower half of a card's plugs, COUNT_BELOW px below the cable's
# line; a cable's first run is at least 24 px, so the slash always has
# its room
CABLE_WIDTH, BUS_LENGTH, BUS_ALONG, BUS_WIDTH, BUS_GAP, COUNT_BELOW, COUNT_SIZE = (
    1.3, 6, 11, 1.3, 1, 9.7, "9.5px",
)


def assert_stroke(width: str, weight: float, floor: float, zoom: float) -> None:
    """Asserts that the stroke width `width`, as the browser computes it at
    the scale `zoom`, is `weight` px at scale 1 and at least `floor` px on
    the screen, `max(weight, floor / zoom)` (design pass 13 §1, rule 3)."""
    assert width.endswith("px"), width
    assert abs(float(width[:-2]) - max(weight, floor / zoom)) <= 0.01, (width, weight, floor, zoom)

# Each cable the region draws: its edge's id, its record's two occurrences
# where it is a join wire, whether it is the piece the wires of a pair of
# periods share and whether it is dashed, the points of the first part of
# its route from its writing end as its path writes them, its stroke and
# stroke width as the browser computes them; its bus mark's slash, the two
# points its path writes, its stroke and its width, and its count's text,
# place, size, face and fill, each null where it draws none; and the colors
# the page gives the graph's wire, ice-3 and the accent as a stroke and ink-3
# as a fill, resolved in a probe of the region.
BUS_MARKS_JS = r"""
() => {
  const host = document.querySelector('.bl-view-host');
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  host.appendChild(svg);
  const resolved = (property, value) => {
    const probe = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    probe.style[property] = value;
    svg.appendChild(probe);
    const found = getComputedStyle(probe)[property];
    probe.remove();
    return found;
  };
  const colors = {wire: resolved('stroke', 'var(--bl-graph-wire)'), ice: resolved('stroke', 'var(--bl-ice-3)'),
                  accent: resolved('stroke', 'var(--bl-accent)'), ink: resolved('fill', 'var(--bl-ink-3)'),
                  port: resolved('stroke', 'var(--bl-graph-port)')};
  // whether the cable leaves a plug in the lower half of its card's plugs, where its count stands below it
  const lowerHalf = (edge) => {
    const writer = edge.dataset.id.split('::out::')[0], handle = edge.dataset.id.split('>>')[0];
    const node = host.querySelector(`.react-flow__node[data-id="${CSS.escape(writer)}"]`);
    const plugs = node ? Array.from(node.querySelectorAll('.bf-card > .react-flow__handle.source'))
      .sort((one, other) => one.getBoundingClientRect().top - other.getBoundingClientRect().top) : [];
    const index = plugs.findIndex((plug) => plug.dataset.handleid === handle);
    return plugs.length >= 2 && index >= plugs.length / 2;
  };
  svg.remove();
  const points = (path) => {
    const found = [];
    for (const step of (path.getAttribute('d') || '').match(/[ML][^ML]*/g) || []) {
      if (step[0] === 'M' && found.length) break;
      const [x, y] = step.slice(1).split(',').map(Number);
      found.push({x, y});
    }
    return found;
  };
  const cables = Array.from(host.querySelectorAll('.react-flow__edge.bf-cable-edge'), (edge) => {
    const outer = edge.querySelector('.bf-cable-outer'), bus = edge.querySelector('.bf-cable-bus');
    const count = edge.querySelector('.bf-cable-count');
    const style = (element) => getComputedStyle(element);
    return {
      id: edge.dataset.id, from: edge.dataset.from || null, to: edge.dataset.to || null, below: lowerHalf(edge),
      pair: edge.classList.contains('bf-join-pair'), dashed: !!edge.querySelector('.bf-cable-dashed'),
      route: points(outer), stroke: style(outer).stroke, width: style(outer).strokeWidth,
      slash: bus ? {points: points(bus), stroke: style(bus).stroke, width: style(bus).strokeWidth} : null,
      count: count ? {text: count.textContent, x: Number(count.getAttribute('x')), y: Number(count.getAttribute('y')),
                      size: style(count).fontSize, family: style(count).fontFamily, fill: style(count).fill} : null,
    };
  });
  return {colors, cables};
}
"""


def route_counts(graph: dict, direction: str) -> dict:
    """The count of the wires of each cable of the trellis graph `graph` of
    `direction` that a route's record names, by the route's source and
    destination: in the backward graph the value functions it carries, the
    outputs its edges come from, and in the forward graph its route's pairs,
    the fields of the one measure it carries (design pass 10 §6; design pass
    12 §§2 and 3)."""
    outputs, pairs = {}, {}
    for node in graph["nodes"]:
        for edge in node.get("incomingEdges") or []:
            for pair in edge.get("attrs") or []:
                if pair["key"] == "route":
                    ends = (pair["value"]["source"], pair["value"]["destination"])
                    outputs.setdefault(ends, set()).add((edge["sourceNodeId"], edge["sourceNodeOutputId"]))
                    pairs[ends] = len(pair["value"]["pairs"])
    return {ends: len(outputs[ends]) if direction == "backward" else pairs[ends] for ends in pairs}


def assert_bus_mark(cable: dict, count: int, colors: dict, zoom: float) -> None:
    """Asserts that the cable `cable`, as BUS_MARKS_JS reads it at the scale
    `zoom`, draws the bus mark of `count` wires (design pass 13 §1, rule 5):
    its slash BUS_LENGTH px long at 45 degrees to the first run of the
    cable's route, its middle on that run BUS_ALONG px from the plug's
    center, BUS_WIDTH thick at scale 1 and at least 1 px on the screen, in
    the port ink; the count's text `count`, in Mark, COUNT_SIZE, ink-3, its
    left edge BUS_GAP px past the slash's right end and its baseline BUS_GAP
    px above the slash's upper end, or COUNT_BELOW px below the cable's
    line where the cable leaves the lower half of its card's plugs."""
    route, slash, text = cable["route"], cable["slash"], cable["count"]
    assert slash is not None and text is not None, cable
    start = route[0]
    following = next(point for point in route[1:] if point != start)
    dx, dy = following["x"] - start["x"], following["y"] - start["y"]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    one, other = slash["points"]
    sx, sy = other["x"] - one["x"], other["y"] - one["y"]
    assert abs(math.hypot(sx, sy) - BUS_LENGTH) <= 0.01, cable
    middle = ((one["x"] + other["x"]) / 2, (one["y"] + other["y"]) / 2)
    assert math.dist(middle, (start["x"] + ux * BUS_ALONG, start["y"] + uy * BUS_ALONG)) <= 0.01, cable
    angle = math.degrees(math.acos(min(1.0, abs(sx * ux + sy * uy) / math.hypot(sx, sy))))
    assert abs(angle - 45) <= 0.5, (angle, cable)
    assert_stroke(slash["width"], BUS_WIDTH, 1.0, zoom)
    assert slash["stroke"] == colors["port"], cable
    upper = min((one, other), key=lambda point: (point["y"], -point["x"]))
    assert text["text"] == str(count), (count, cable)
    right = max(one["x"], other["x"]) + BUS_GAP
    baseline = middle[1] + COUNT_BELOW if cable["below"] else upper["y"] - BUS_GAP
    assert abs(text["x"] - right) <= 0.01 and abs(text["y"] - baseline) <= 0.01, cable
    assert text["size"] == COUNT_SIZE and text["family"].startswith('"IBM Plex Mono"'), cable
    assert text["fill"] == colors["ink"], (text, colors)


def test_a_cable_of_several_wires_draws_their_count_at_its_plug_and_a_cable_of_one_wire_none(
    browser, server_on, durables_folder
):
    """Design pass 13 §1, rules 3 to 5 and 7 (design pass 12 §§1 and 3). On
    a copy of the durables model at periods 0 to 2, in the backward
    trellis graph and in the forward one, every cable is one stroke of 1.3
    px at scale 1, a wire's weight, and at least 1 px on the screen; every
    cable that carries more than one wire draws at its plug the bus mark,
    a slash of 6 px at 45 degrees across its first run, its center 11 px
    along the run from the plug's center, 1.3 px thick at scale 1 in the
    port ink, and the count of its wires in Mark, 9.5 px, ink-3, 1 px past
    the slash's right end, its baseline 1 px above the slash's upper end,
    or 9.7 px below the cable's line for a cable from the lower half of a
    card's plugs: a backward cable counts the value functions it carries,
    three from `tenure` of periods[0] into `keeper_cons` of periods[1] and
    into each `outside` marker, two on the branch `adjust`, and a forward
    cable its route's pairs; the stub of the terminal condition, one wire,
    draws no mark. Hovered, the cable from `tenure` of periods[0] to
    `keeper_cons` stands in ice-3 and its slash keeps the port ink, and
    selected, the cable and its slash are 2 px in the accent at scale 1,
    held at 1.5 px on the screen."""
    tenure, reader = "periods[0]/tenure", TENURE_READERS[0]
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        seen = {}
        for direction in ("forward", "backward"):
            record_layouts(tab)
            choose_view(tab, None, direction)
            wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the {direction} graph")
            wait_until(lambda: view_still(tab), 30.0, f"the {direction} graph at rest")
            counts = route_counts(graph_named(tab.evaluate(HELD_COLLECTION_JS), direction), direction)
            # every route's cable with its record, which names its route
            wait_until(
                lambda: set(counts) <= {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
                10.0,
                f"the {direction} graph's cables with their records",
            )
            zoom = viewport(tab)["zoom"]
            drawn = tab.evaluate(BUS_MARKS_JS)
            colors, cables = drawn["colors"], drawn["cables"]
            marked = []
            for cable in cables:
                # every cable one stroke at a wire's weight, at least 1 px on the screen (design pass 13 §1, rule 3)
                assert_stroke(cable["width"], CABLE_WIDTH, 1.0, zoom)
                assert cable["stroke"] == colors["wire"], cable
                if cable["pair"]:
                    # the piece the wires of a pair of periods share has no plug and draws no mark
                    assert cable["slash"] is None and cable["count"] is None, cable
                    continue
                if cable["from"] and cable["to"]:
                    count = counts[(cable["from"], cable["to"])]
                elif cable["dashed"] and direction == "backward":
                    # a stub to an `outside` marker carries tenure's three wires
                    count = len(TENURE_VALUES)
                else:
                    # a stub of the forward graph, or the terminal condition's, one wire
                    count = 1
                if count > 1:
                    assert_bus_mark(cable, count, colors, zoom)
                    marked.append(count)
                else:
                    assert cable["slash"] is None and cable["count"] is None, cable
            seen[direction] = Counter(marked)
        # the backward graph's marks: three wires on the nine routes of three
        # pairs and on the two stubs to the `outside` markers, two on the
        # branch `adjust` in each period; the stub of the terminal condition,
        # the one cable of one wire, unmarked
        assert seen["backward"] == Counter({3: 11, 2: 3}), seen
        assert counts[(reader, tenure)] == 3 and counts[(tenure, "periods[0]/adjuster_cons")] == 2

        # hovered, the cable into keeper_cons and its slash stand in ice-3
        tab.click(".bl-zoom-button[data-zoom='fit']")
        wait_until(lambda: view_still(tab), 30.0, "the backward graph fitted")

        def cable_of(found: dict) -> dict:
            (cable,) = [c for c in found["cables"] if (c["from"], c["to"]) == (reader, tenure)]
            return cable

        point = tab.evaluate(JOIN_POINT_JS, [reader, tenure])
        tab.mouse.move(point["x"], point["y"])
        hovered, _ = wait_until(
            lambda: (found := tab.evaluate(BUS_MARKS_JS))
            and cable_of(found)["stroke"] == found["colors"]["ice"]
            and found,
            5.0,
            "the hovered cable in ice-3",
        )
        # the slash keeps the port ink while the cable is hovered (design pass 13 §1, rule 7)
        assert cable_of(hovered)["slash"]["stroke"] == hovered["colors"]["port"], cable_of(hovered)
        # selected, the cable and its slash in the accent at 2 px at scale 1, held at 1.5 px on the screen,
        # measured at the scale the click's enlargement of the region leaves (design pass 13 §1, rules 3 and 7)
        click_join(tab, reader, tenure)
        tab.mouse.move(4, 4)
        selected, _ = wait_until(
            lambda: (found := tab.evaluate(BUS_MARKS_JS))
            and cable_of(found)["stroke"] == found["colors"]["accent"]
            and found,
            10.0,
            "the selected cable in the accent",
        )
        zoom = viewport(tab)["zoom"]
        cable = cable_of(selected)
        assert_stroke(cable["width"], 2.0, 1.5, zoom)
        assert_stroke(cable["slash"]["width"], 2.0, 1.5, zoom)
        assert cable["slash"]["stroke"] == selected["colors"]["accent"], cable
        print(f"unit P: bus marks by count, {dict((d, dict(c)) for d, c in seen.items())}")
    finally:
        context.close()
