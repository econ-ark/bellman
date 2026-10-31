"""The acceptance tests of unit K of model interface specification 0.4, the
polish of the page (the plan `2026-10-07-unit-k.md` in the plans folder
of the model-interface build area): one test for each
task's acceptance check, each reading the page's elements and the layout's
records, never a screenshot's pixels (ruling K-P3). Deleted when the next
amendment is accepted (lean implementation rule, layer 2).
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

from bellman.period import period_joins
from bellman.stage import LAYER_ID_ENDING, admitted_methods, elaborate_text
from bellman.trellis import entry_value
from bellman_workbench import creation, model, recipe, trellis

from workbench_support import (
    ADJUSTER_CONS_DETAILS,
    ADJUSTER_CONS_FILE,
    ADJUSTER_CONS_JOIN_DETAILS,
    BEQUEST_JOIN_DETAILS,
    BOX_DETAILS_JS,
    BOX_OVERFLOW_JS,
    BOX_PORT_WORD_LINES_JS,
    CONS,
    CONS_ID,
    DETAILS_HOLDING_JS,
    DETAILS_OVERFLOW_JS,
    DETAILS_ROWS_JS,
    DISC_ID,
    DOCUMENT_JS,
    DRAWN_JOINS_JS,
    DRAWN_PLACES_JS,
    DURABLES_SLOT_KEYWORDS,
    DURABLES_STATUS_BOUND,
    DURABLES_STATUS_REST,
    FOCUSED_JS,
    FRAME_TRACKS,
    HELD_COLLECTION_JS,
    LAYER_IN_REGION_JS,
    MATSYA_FOLD,
    MATSYA_TOGGLE,
    PAIR_JOIN_DETAILS,
    PORT_CONS,
    PORT_CONS_RECORDS,
    PORT_CONS_RECIPE,
    PORT_ID,
    PULLBACK_DETAILS,
    READING_SCALE,
    RECIPE_FILE,
    RESTRICTION,
    RESTRICTION_TEXT,
    REGION_READING_JS,
    ROOT,
    TERMINAL_ID,
    TRELLIS_STATUS_FIT_JS,
    TRELLIS_TRACKS,
    TWO_FRAMES_JS,
    TWO_STAGES,
    TYPE_FACES_JS,
    VIEW_STATE_JS,
    WHOLE_GRAPH_SHOWN_JS,
    add_period_controls,
    as_json,
    attribute_of,
    bound_as_the_recipe_binds,
    boxes,
    breadcrumb,
    checklist_count,
    choose_restriction,
    choose_view,
    click_join,
    click_line,
    click_toggle,
    click_until,
    connected_event,
    control_targets,
    cut_within_a_word,
    details_until,
    drag_handle,
    cable_list,
    cable_port,
    cable_ports,
    drag_ports,
    drawn_extent,
    dropped_event,
    emptied_portfolio,
    error_lines,
    expected_layout,
    field_port,
    file_bytes,
    file_tabs,
    flow_handle,
    gesture_note,
    graph_named,
    held_events,
    held_joins,
    history_buttons,
    hold_events,
    join_wires_drawn,
    keyboard_place,
    layout_record,
    layout_records,
    layouts_recorded,
    move_join_end,
    lay_out_left_to_right,
    lay_out_top_to_bottom,
    new_tab,
    occurrence_head,
    occurrences_of,
    open_checklist,
    open_file,
    open_path_shown,
    open_recipe_row,
    open_restriction,
    open_trellis,
    open_tree_file,
    open_workbench,
    opened_namespaces,
    opens_on,
    panel_head,
    periods_held,
    press_outside_fields,
    printed_details,
    property_color,
    recipe_head,
    record_layouts,
    records_without,
    release_events,
    replace_in_editor,
    restrict,
    restriction_menu_shown,
    restriction_shown,
    reveal_in_tree,
    save_unsaved_files,
    select_until,
    slot_keywords,
    status_settled_on,
    status_text,
    tracks,
    tracks_near,
    tree_names,
    trellis_settled,
    unjoined_field_ids,
    unjoined_port_ids,
    unsaved_in_tree,
    unsaved_of,
    used_at,
    view_laid_out,
    view_shown,
    view_still,
    viewport,
    wait_until,
    with_each_recipe_row_open,
)

# the most characters a label printed on a wire takes (spec 0.4 §2.1)
LABEL_MOST = 22
# the widest gap between two adjacent period layers at scale 1 (design pass
# §5, item 1)
GAP_MOST = 200
# the labels the join wires of the durables model's forward trellis graph,
# periods 0–2, print (K-D4): between two periods, and from the trellis's
# `Inputs` into periods[2], the arrival fields of `tenure` its mapping
# reaches; inside periods[0], the arrival fields of `bequest`; inside each
# period, the two joins by equal names from `tenure`, printed as they stand
# the labels of the cables (design pass 10 §6; unit N, Task 7): the piece the
# six wires from a period into the next share, the three wires from each
# consumption stage into `bequest`, the one wire of a stub to a boundary
# marker, and the two branches of `tenure`
BETWEEN_PERIODS = "6 wires"
DURABLES_LABELS = {BETWEEN_PERIODS, "3 wires", "1 wire", "keep", "adjust"}
# the join wires of the durables model's forward trellis graph, periods
# 0–2, whose writer and reader stand in one period: from `tenure` to each
# consumption stage in each period, and from each consumption stage to
# `bequest` in periods[0]
WITHIN_PERIODS = 8
# the other join wires of the same graph, between two drawn periods: from
# `keeper_cons` and from `adjuster_cons` of periods[2] and of periods[1]
# into the next period's `tenure`; the count was 5 with the wire from the
# trellis's `Inputs` into periods[2], a container design pass 10 §6 took
# out of the graph
BETWEEN_WIRES = 4
# the stubs to the boundary markers of the same graph (design pass 10 §6),
# counted apart, since each joins a drawn period to no other drawn period:
# from the `outside` markers of `keeper_cons` and `adjuster_cons` in
# periods[3] into periods[2]'s `tenure`, and from `bequest` in periods[0]
# to the `end` marker of its measure
MARKER_STUBS = 3
# periods printed as ranges, `0–50` or `0–4, 7–50`, at the end of a text
RANGES = re.compile(r"\d+(–\d+)?(, \d+(–\d+)?)*$")
# Details' width at the window of 1600 × 1000 the tests open, and the
# tallest content of Details for a selected box at that width (design pass
# §5, item 5). The width was 314 px; unit N's Task 1 took the window's left
# padding of 60 px away with unit L's rail (design pass 10 §2), and design
# pass 13 §4 its right margin of 60 px (Q-D6), and the text and the graph
# share that room in the proportion of their columns, so that the graph's
# column, and Details in it, is the graph's width of FRAME_TRACKS, 357 px
DETAILS_WIDTH = FRAME_TRACKS[1600, False][2]
BOX_HEIGHT_MOST = 1000
# the box of the durables model's adjuster_cons.bl whose Details the design
# pass measured, and a line of that file outside every block whose
# parameter, τ, the box's kernel reads
PULLBACK = "cntn_to_dcsn:Pullback"
TAU_LINE = 8
# the fold that holds the block under the editor's cursor, its record and
# its two lists of boxes
CURSOR = ".bl-panel-body details.bl-cursor-details"
# the start and the end of the trellis's visible status line for the
# durables model's recipe, periods 0–2: the file and `trellis`; the
# restriction with its counts and the loop's seconds
STATUS_START = rf"{re.escape(RECIPE_FILE)} · trellis"
STATUS_END = r" · shown periods 0–2 of 51 \(10 occurrences\) · loop \d+\.\d\d s"
# the visible line with the verbs applied between the two (spec 0.4 §5.7;
# design pass §5, item 6)
DURABLES_STATUS_LINE = re.compile(STATUS_START + re.escape(DURABLES_STATUS_BOUND) + STATUS_END)
# the arrangements of the same status line, each the visible line and the
# trellis's parts in the details' line, None where none stands there: the
# whole line; and the line with the verbs applied, its rest in the details'
# line
WHOLE_LINE = (re.compile(DURABLES_STATUS_LINE.pattern + re.escape(DURABLES_STATUS_REST)), None)
BOUND_LINE = (DURABLES_STATUS_LINE, DURABLES_STATUS_REST)
# the windows of Task 6's test, each with the arrangements it accepts with
# Matsya open. The line is set in Small with its parts 16 px apart (design
# pass 8 §6; unit M, Task 4, M-I29): the whole line, about 853 px wide,
# fits from a window of about 1365 px while the loop takes less than ten
# seconds, and the line with the verbs applied, about 601 px wide, fits the
# least room the visible line leaves it, about 664 px, which a window of
# 1176 px gives and a narrower window keeps, since the window then scrolls
# sideways. The line without the verbs applied therefore stands at no
# window; 1100 × 800 measures the line in its least room.
STATUS_WINDOWS = (
    ((2200, 1000), (WHOLE_LINE,)),
    ((1600, 1000), (WHOLE_LINE,)),
    ((1280, 800), (BOUND_LINE,)),
    ((1200, 800), (BOUND_LINE,)),
    ((1100, 800), (BOUND_LINE,)),
)
# the two files of the durables model whose names the tree printed alike
ADJUSTER_CONS_FILES = (ADJUSTER_CONS_FILE, ADJUSTER_CONS_FILE.replace(".bl", ".md"))
# the widest the restricted forward trellis graph of the durables model may
# be at scale 1 (design pass §5, item 7)
WIDTH_MOST = 4500
# a port of a period's layer at its border, `periods[1]___group___::hout::…`
PERIOD_PORT = re.compile(r"(periods\[\d+\])" + re.escape(LAYER_ID_ENDING) + r"::h(?:in|out)::")
# the layer of the terminal period, on which a trellis graph opens (K-D6,
# K-D22 as AAS's M-D15 amends them)
TERMINAL = f"periods[0]{LAYER_ID_ENDING}"


def durables_forward(tab, url: str) -> tuple[dict, dict]:
    """The durables model's forward trellis graph, shown as the folder at
    `url` opens it, periods 0 to 2, and the layout's records of it with the
    periods and their occurrences open, as the page opens them."""
    open_trellis(tab, url, RECIPE_FILE)
    lay_out_left_to_right(tab)
    assert restriction_shown(tab) == "periods 0–2"
    record_layouts(tab)
    choose_view(tab, None, "forward")
    wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph laid out")
    held = tab.evaluate(HELD_COLLECTION_JS)
    forward = graph_named(held, "forward")
    records = layout_records(tab, forward, opened_namespaces(occurrences_of(held, "forward")))
    assert records["problems"] == []
    return forward, records


def crossing_points(first: list[dict], second: list[dict]) -> list[tuple[float, float]]:
    """The points at which a horizontal segment of one route and a vertical
    segment of the other meet strictly inside both, each route a list of
    points `{x, y}`; a shared end point and a collinear overlap are no
    crossing (row K-I7)."""

    def between(value: float, one: float, other: float) -> bool:
        return min(one, other) + 0.01 < value < max(one, other) - 0.01

    points = []
    for a, b in zip(first, first[1:]):
        for c, d in zip(second, second[1:]):
            first_level, second_level = abs(a["y"] - b["y"]) < 0.01, abs(c["y"] - d["y"]) < 0.01
            if first_level == second_level:
                continue
            (h1, h2), (v1, v2) = ((a, b), (c, d)) if first_level else ((c, d), (a, b))
            if between(v1["x"], h1["x"], h2["x"]) and between(h1["y"], v1["y"], v2["y"]):
                points.append((v1["x"], h1["y"]))
    return points


def occurrence_of(box: str, namespaces: dict[str, str]) -> str | None:
    """The occurrence `periods[h]/<key>` in which the box `box` of the
    layout's records stands, a layer known by its id and a node by its
    namespace in `namespaces`; None for a box outside every period."""
    if box.endswith(LAYER_ID_ENDING):
        namespace = box[: -len(LAYER_ID_ENDING)]
    else:
        namespace = namespaces[box]
    parts = namespace.split("/")
    if len(parts) < 2 or not parts[0].startswith("periods["):
        return None
    return "/".join(parts[:2])


def strictly_inside(point: tuple[float, float], place: dict) -> bool:
    """Whether `point` lies strictly inside the box placed at `place`."""
    x, y = point
    return (
        place["ax"] < x < place["ax"] + place["width"]
        and place["ay"] < y < place["ay"] + place["height"]
    )


def opened_on_the_terminal_period(tab, what: str) -> dict:
    """Waits until the region shows the trellis graph as it opens (K-D6 and
    K-D22 as AAS's M-D15 amends them; design pass 13 §2, rule 10): the view
    on the terminal period's layer at the largest scale, at most 1 and at
    least 0.6, at which the layer fills the region less 10 px at each side,
    moved from its center toward the graph's nearer end as far as the layer
    stays within it, the layer's top 24 px under the region's top, the
    bar's foot, its body cut where it is taller than the region
    (`opens_on`, the layer's place and the
    graph's extent read from the elements); the layer within the region,
    its right cut only where it is wider than the region at the floor 0.6;
    the header, the layer's top G.periodHeader at that scale, within the
    region and its name, `periods[0]`, drawn there; answers the viewport
    (`viewport`) with `seen`, the boxes LAYER_IN_REGION_JS reads."""
    G = tab.evaluate("() => window.BellmanFlowLayout.G")
    found = {}

    def opened() -> bool:
        view = viewport(tab)
        nodes = tab.evaluate(DRAWN_PLACES_JS)["nodes"]
        place = nodes.get(TERMINAL)
        seen = tab.evaluate(LAYER_IN_REGION_JS, TERMINAL)
        found.update(view=view, place=place, seen=seen)
        if place is None or seen is None:
            return False
        at = {"ax": place["x"], "ay": place["y"]}
        at.update(width=place["width"], height=place["height"])
        host, layer = seen["host"], seen["layer"]
        header = layer["top"] + G["periodHeader"] * view["zoom"]
        # cut at its right where it is wider than the region at the floor (M-D15)
        cut = at["width"] * READING_SCALE > view["width"] - 20
        return (
            opens_on(view, at, drawn_extent(nodes))
            and all(layer[side] >= host[side] - 1 for side in ("left", "top"))
            and (cut or layer["right"] <= host["right"] + 1)
            and header <= host["bottom"] + 1
            and seen["text"] == "periods[0]"
            and seen["drawn"]
        )

    try:
        wait_until(opened, 30.0, what)
    except AssertionError:
        raise AssertionError((what, found)) from None
    return {**found["view"], "seen": found["seen"]}


def test_task_1_a_wire_between_periods_prints_its_arrival_fields_and_the_periods_stand_close(
    browser, server_on, durables_folder
):
    """Task 1 (design pass §1 item 1 and §3 (c); K-D4): on the durables
    model's forward trellis graph, shown as the folder opens it, periods 0
    to 2, the layout's records with the periods and their occurrences open,
    as the page opens them, put adjacent period layers at most 200 px apart
    at scale 1, and every join label handed to ELK has at most 22
    characters, the wires between periods printing `a, h, z`. Drawn on the
    page with `fit`, every wire that prints `a, h, z` keeps the six entries
    of its mapping, as the exporter writes them, in its title."""
    context, tab = new_tab(browser)
    try:
        forward, records = durables_forward(tab, server_on(durables_folder))

        places = records["places"]
        period = [places[f"periods[{h}]{LAYER_ID_ENDING}"] for h in range(3)]
        # periods[0], the terminal period, stands at the right
        gaps = [period[h]["ax"] - period[h + 1]["ax"] - period[h + 1]["width"] for h in range(2)]
        print(f"task 1: periods[1] to periods[0] and periods[2] to periods[1]: {gaps} px apart")
        assert all(0 < gap <= GAP_MOST for gap in gaps), gaps
        labels = {join["text"] for join in records["joins"].values()}
        assert labels == DURABLES_LABELS
        assert max(len(label) for label in labels) <= LABEL_MOST

        # the mapping's entries, as the exporter writes them on the reading
        # port of `tenure` in each period, from periods[3] outside the view
        # into periods[2] and between the periods drawn
        entries = {
            attribute_of(port, "join")
            for node in forward["nodes"]
            if (node.get("namespace") or "").endswith("/tenure/arvl_to_dcsn")
            for port in node.get("inputsMetadata") or []
            if attribute_of(port, "join")
        }
        assert len(entries) == 3 and all(len(text) > LABEL_MOST for text in entries)
        tab.click('.bl-zoom-button[data-zoom="fit"]')
        drawn, _ = wait_until(
            lambda: (found := tab.evaluate(DRAWN_JOINS_JS))
            and {wire["label"] for wire in found} == labels
            and found,
            30.0,
            "the join labels drawn at fit",
        )
        # the pieces between the periods drawn and the stubs from the `outside`
        # markers into periods[2], each one wire (unit N, Task 7)
        between = [wire["title"] for wire in drawn if wire["label"] in (BETWEEN_PERIODS, "1 wire")]
        # a title is the wire's label and, on its second line, the join's text
        assert {title.split("\n", 1)[1] for title in between if "\n" in title} == entries
    finally:
        context.close()


def test_task_2_keeper_cons_stands_above_adjuster_cons_and_no_crossing_outside_the_writer(
    browser, server_on, durables_folder
):
    """Task 2 (design pass §1 item 7 and §3 (d); K-D12, rows K-I6, K-I7
    and K-I14, as the fix wave Q3a of unit Q, item 2, amends K-D12): on the
    durables model's forward trellis graph, periods 0 to 2, in the layout's
    records with the periods and their occurrences open, laid out with the
    recipe's order of the stages that the page gives the region,
    `keeper_cons`, which the recipe's `stages:` list names before
    `adjuster_cons` and `tenure` writes from its port `keep`, stands above
    `adjuster_cons`, which it writes from its port `adjust`, in each
    period; and among all the drawing's wires, the join
    wires within a period and between periods among them, no two cross
    outside the box of the occurrence that writes both. The crossing K-D12
    leaves lies inside `tenure`'s box, between its two wires, at most once a
    period. The join wires are counted within a period, between two drawn
    periods, and apart for the stubs to the boundary markers that design
    pass 10 §6 draws in place of the trellis's `Inputs` and `Outputs`."""
    context, tab = new_tab(browser)
    try:
        forward, records = durables_forward(tab, server_on(durables_folder))
        places, routes = records["places"], records["routes"]
        for h in range(3):
            keeper = places[f"periods[{h}]/keeper_cons{LAYER_ID_ENDING}"]
            adjuster = places[f"periods[{h}]/adjuster_cons{LAYER_ID_ENDING}"]
            assert keeper["ay"] + keeper["height"] <= adjuster["ay"], (h, keeper, adjuster)

        # each wire of the drawing, by its id: the writing occurrence and the
        # reading occurrence, None for a box outside every period
        namespaces = {node["id"]: node.get("namespace") or "" for node in forward["nodes"]}
        ends = {
            wire: (occurrence_of(writer, namespaces), occurrence_of(reader, namespaces))
            for wire, (writer, _, reader, _) in zip(records["wireIds"], records["wires"])
        }
        # the join wires whose writer and reader stand in one period; the
        # stubs to the boundary markers, counted apart, since each joins a
        # drawn period to no other drawn period (design pass 10 §6, which
        # took the trellis's `Inputs` and `Outputs` out of the graph); and the
        # other join wires, between two drawn periods; every join wire is a
        # cable, for which the layout places no label (design pass 13 §2,
        # rule 9), so the wires are read from the records of all the wires
        markers = {
            node["id"]
            for node in forward["nodes"]
            if not node.get("namespace")
            and attribute_of(node, "kind") in ("start", "end", "outside")
        }
        within = [
            wire
            for wire, (source, target) in ends.items()
            if source and target and source.split("/")[0] == target.split("/")[0]
        ]
        stubs = [
            wire
            for wire, (writer, _, reader, _) in zip(records["wireIds"], records["wires"])
            if markers & {writer, reader}
        ]
        between = [wire for wire in records["wireIds"] if wire not in within and wire not in stubs]
        assert records["joins"] == {}, records["joins"]
        assert len(within) == WITHIN_PERIODS, within
        assert len(stubs) == MARKER_STUBS, stubs
        assert len(between) == BETWEEN_WIRES, between

        # each crossing of two wires, inside the box of the occurrence that
        # writes both, as (writer, the two readers), or outside it
        inside, outside = [], []
        wires = sorted(routes)
        for i, first in enumerate(wires):
            for second in wires[i + 1 :]:
                (writer, reader), (other_writer, other_reader) = ends[first], ends[second]
                for point in crossing_points(routes[first], routes[second]):
                    own = writer is not None and writer == other_writer
                    if own and strictly_inside(point, places[writer + LAYER_ID_ENDING]):
                        inside.append((writer, tuple(sorted((str(reader), str(other_reader))))))
                    else:
                        outside.append((point, ends[first], ends[second]))
        print(f"task 2: crossings outside the writer's box {outside}, inside it {sorted(inside)}")
        assert outside == []
        for writer, readers in inside:
            period = writer.split("/")[0]
            assert writer == f"{period}/tenure", inside
            assert readers == (f"{period}/adjuster_cons", f"{period}/keeper_cons"), inside
        for h in range(3):
            assert sum(writer == f"periods[{h}]/tenure" for writer, _ in inside) <= 1, inside
    finally:
        context.close()


def test_task_3_details_of_an_occurrence_are_labeled_rows_and_its_stage_s_uses_are_ranges(
    browser, server_on, durables_folder
):
    """Task 3 (design pass §1 items 2 and 3 and §2 "A stage occurrence";
    K-D2): on the durables model's forward trellis graph, periods 0 to 2,
    Details of the selected stage occurrence periods[1]/adjuster_cons
    prints the fixture's head and rows, each row from a record of the
    package, its legend folded before the removal row, which stands last in
    Details (the fix wave Q3b of unit Q, item 17; D24); no element of
    Details is wider inside than its box. Opened from there,
    `adjuster_cons.bl` with nothing
    selected prints `No selection` first, the five sheet buttons in their
    order, text buttons in Label that take two rows of the graph column at
    its frame width with Matsya's column open (design pass 8 §§5.3 and 6;
    unit M, Task 7), and where the file is used as two items, `periods`
    for the tab's recipe and `also` for `spec.two-stages.yml`, each a
    range whose link shows that recipe's trellis at
    periods[1]/adjuster_cons; again no
    element of Details is wider inside than its box, and the legend, which
    the collection's label titles, stands folded at Details' end."""
    address = "periods[1]/adjuster_cons"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph")
        select_until(
            tab,
            address + LAYER_ID_ENDING,
            "forward",
            lambda: panel_head(tab).startswith(occurrence_head(address))
            and tab.locator(".bl-details-row").count() > 0,
            f"Details of {address}",
        )
        head, rows = tab.evaluate(DETAILS_ROWS_JS)
        assert (head, [tuple(row) for row in rows]) == printed_details(ADJUSTER_CONS_DETAILS)
        assert tab.evaluate(DETAILS_OVERFLOW_JS) == []
        # the legend folded before the removal row, a destructive act last in
        # its panel (the fix wave Q3b of unit Q, item 17; D24)
        before = ".bl-panel-body > details.bl-legend-details:nth-last-child(2)"
        assert tab.locator(before).count() == 1
        assert tab.locator(".bl-panel-body > .bl-removal-buttons:last-child").count() == 1
        assert tab.locator(before).get_attribute("open") is None
        legend = ".bl-panel-body > details.bl-legend-details:last-child"

        click_until(
            tab,
            ".bl-occurrence-open",
            lambda: tab.locator(".bl-restriction").count() == 0,
            "the stage view",
            30.0,
        )
        found, _ = wait_until(
            lambda: (found := used_at(tab)) and len(found) == 2 and found,
            60.0,
            "where adjuster_cons.bl is used",
        )
        print(f"task 3: periods and also {found}")
        assert found == [
            (RECIPE_FILE, "0–50", address),
            (TWO_STAGES, f"{TWO_STAGES} · periods 0–50", address),
        ]
        assert all(RANGES.search(text) for _, text, _ in found)
        # the keys in sentence case (design pass 13 §3; C12)
        keys = tab.locator(".bl-used-at .bl-details-key").all_text_contents()
        assert keys == ["Periods", "Also"]
        # the body's text begins with the words of the empty state, not
        # with the collection's label, which titles the folded legend
        assert tab.locator(".bl-panel-body").text_content().startswith("No selection")
        tops = tab.locator(".bl-sheet-button").evaluate_all(
            "(all) => all.map((button) => button.getBoundingClientRect().top)"
        )
        assert len(tops) == 5 and tops == sorted(tops) and len(set(tops)) <= 2, tops
        assert tab.evaluate(DETAILS_OVERFLOW_JS) == []
        assert tab.locator(legend).count() == 1
        assert tab.locator(legend).get_attribute("open") is None
    finally:
        context.close()


def test_task_4_details_of_a_join_wire_are_labeled_rows_and_its_fields_a_table(
    browser, server_on, durables_folder
):
    """Task 4 (design pass §1 item 6 and §2 "A join wire"; K-D2, J-D33,
    J-D42): on the durables model's forward trellis graph, periods 0 to 2,
    Details of the join wire selected from periods[1]/adjuster_cons to
    periods[0]/tenure prints the fixture's head and rows, its `fields` a
    table of three lines, one for each join of that writer, and the button
    `remove` under them; the six entries of the mapping, the text the
    exporter writes on the reading port, stand in no element of Details,
    as text or as a hover; no element of Details is wider inside than its
    box, and the legend stands folded at its end. The wire within
    periods[0] from adjuster_cons to bequest prints its connector, the one
    period it reaches and a table of three lines."""
    between = ("periods[1]/adjuster_cons", "periods[0]/tenure")
    within = ("periods[0]/adjuster_cons", "periods[0]/bequest")
    fields = '.bl-join-details .bl-details-row[data-key="fields"] tr.bl-details-line'
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph")
        forward = graph_named(tab.evaluate(HELD_COLLECTION_JS), "forward")
        # the six entries of the mapping, as the exporter writes them on the
        # arrival measure's port of periods[0]/tenure
        (text,) = {
            attribute_of(port, "join")
            for node in forward["nodes"]
            for port in node.get("inputsMetadata") or []
            if port["id"] == "periods[0]/tenure/tenure:measure:arvl"
        }
        assert text.count("→") == 6, text

        click_join(tab, *between)
        details_until(tab, ADJUSTER_CONS_JOIN_DETAILS, "Details of the join wire between periods")
        assert tab.locator(fields).count() == 3
        assert tab.evaluate(DETAILS_HOLDING_JS, text) == []
        remove = tab.locator(".bl-join-details .bl-join-remove")
        assert remove.get_attribute("title") == "Remove the join from trellis.yml"
        under = tab.locator(".bl-join-details .bl-details-rows").bounding_box()
        assert remove.bounding_box()["y"] >= under["y"] + under["height"]
        assert tab.evaluate(DETAILS_OVERFLOW_JS) == []
        legend = ".bl-panel-body > details.bl-legend-details:last-child"
        assert tab.locator(legend).count() == 1
        assert tab.locator(legend).get_attribute("open") is None

        click_join(tab, *within)
        details_until(tab, BEQUEST_JOIN_DETAILS, "Details of the join wire within periods[0]")
        assert tab.locator(fields).count() == 3
        assert tab.evaluate(DETAILS_OVERFLOW_JS) == []
    finally:
        context.close()


def test_task_5_details_of_a_box_are_rows_and_whole_blocks_and_the_cursor_folds(
    browser, server_on, durables_folder
):
    """Task 5 (design pass §1 item 5 and §2 "An operator box"; K-D2): on
    the durables model's adjuster_cons.bl, bound as the folder's recipe
    binds it, Details of the selected box cntn_to_dcsn:Pullback, 314 px
    wide, prints the fixture: its symbol, kind and graph, then its
    identifier and the perches its builder joins; the rows `at`, `lines`,
    `reads`, `writes`, `source`, the file's lines without their
    annotations, and `uses`; the rule and the kernel each once, whole, as
    the package's texts, broken only at `=` and `;`. No row is a numbered
    kernel, no ports table stands, every perch and role stands on one line,
    no row's value and no element outside the fold `cursor` is wider inside
    than its box, and the content is at most 1,000 px tall. The fold
    `cursor`, holding the block under the cursor, whose printed record
    scrolls within its own box, is closed while the box is selected; with
    nothing selected and the cursor on line 8, which declares τ, it is open
    and lists the boxes whose kernels read that line."""
    text = (durables_folder / ADJUSTER_CONS_FILE).read_text(encoding="utf-8")
    stage = bound_as_the_recipe_binds(durables_folder, text, ADJUSTER_CONS_FILE)
    piece = model.piece(stage, "backward", PULLBACK)
    rules = [value for key, value in piece.attributes.items() if key.split(" ")[0] == "rule"]
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(durables_folder), ADJUSTER_CONS_FILE, minimum=4)
        select_until(
            tab,
            PULLBACK,
            "backward",
            lambda: tab.locator(".bl-kernel").count() == 1 and tab.locator(CURSOR).count() == 1,
            f"Details of {PULLBACK}",
        )
        found = []

        def drawn() -> bool:
            found[:] = [tab.evaluate(BOX_DETAILS_JS)]
            return found[0] == list(PULLBACK_DETAILS)

        try:
            wait_until(drawn, 10.0, f"the card of {PULLBACK}")
        except AssertionError:
            assert found[0] == list(PULLBACK_DETAILS)
        # the rule and the kernel are the package's texts, each printed once
        assert tab.locator(".bl-kernel").text_content() == piece.kernel
        assert tab.locator(".bl-rule").text_content() == "\n".join(rules)
        panel = tab.locator(".bl-panel").text_content()
        assert "kernel 1" not in panel and tab.locator(".bl-ports").count() == 0
        lines = tab.evaluate(BOX_PORT_WORD_LINES_JS)
        assert lines and all(count == 1 for _, count in lines), lines
        assert tab.evaluate(BOX_OVERFLOW_JS) == []
        width = tab.locator(".bl-panel").bounding_box()["width"]
        height = tab.evaluate("() => document.querySelector('.bl-panel-body').scrollHeight")
        print(f"task 5: Details {width} px wide, its content {height} px tall")
        assert abs(width - DETAILS_WIDTH) < 1 and height <= BOX_HEIGHT_MOST
        assert tab.locator(CURSOR).get_attribute("open") is None
        legend = ".bl-panel-body > details.bl-legend-details:last-child"
        assert tab.locator(legend).get_attribute("open") is None

        tab.focus(f'.bl-view-host .react-flow__node[data-id="{PULLBACK}"] > .bf-box')
        tab.keyboard.press("Escape")
        wait_until(lambda: tab.locator(".bl-panel-head").count() == 0, 10.0, "nothing selected")
        click_line(tab, TAU_LINE)
        wait_until(
            lambda: tab.locator(f"{CURSOR} .bl-reading-nodes li").count() > 0,
            10.0,
            f"the boxes whose kernels read line {TAU_LINE}",
        )
        assert tab.locator(CURSOR).get_attribute("open") is not None
        assert tab.locator(".bl-panel-body").text_content().startswith("No selection")
        assert tab.evaluate(DETAILS_OVERFLOW_JS) == []
    finally:
        context.close()


def test_task_6_the_labels_the_checklist_and_the_status_line_fit_their_boxes(
    browser, server_on, durables_folder
):
    """Task 6 (design pass §1 items 8, 9 and 10 and §5 item 6; spec 0.4
    §5.7; K-D2, spec 0.4 decision 46): on the durables model's recipe in
    the trellis view, periods 0 to 2, Problems shows the binding refusal's
    native sentence once, with its supplied calibration and recipe source
    controls; no slot is an error (Task 26, K-D29). With Matsya folded, as the
    trellis view shows it (Task 8, K-D6), the whole line stands in the
    visible line at 1600 × 1000. With Matsya opened by its button, at each
    window of `STATUS_WINDOWS` neither the trellis's status line nor any
    Problem sentence or source control is wider inside than its box, and no part of the
    line is lost: at 2200 × 1000 and at 1600 × 1000 the whole line stands
    in the visible line; at 1280 × 800, at 1200 × 800 and at 1100 × 800,
    where the line has its least room, the visible line prints the file,
    `trellis`, the verbs applied, the restriction with its counts and the
    loop's seconds, and the counts of the whole trellis and the unjoined
    fields stand in the details' line (design pass 8 §6; unit M, Task 4,
    M-I29). The summary `Legend`, a fold of
    Details, is set in Label and the graph column's head in Head, both in
    Archivo at 13 px, with no letter-spacing and no change of case (design
    pass 8 §5.1; unit M, Task 7). The tree cuts adjuster_cons.bl and
    adjuster_cons.md at their end after the whole word `adjuster`, with
    room for the ellipsis, as unit L's Task 22 replaced the cut in the
    middle."""
    folder = model.open_folder(durables_folder)
    outcome = trellis.show_trellis(folder, recipe.Source("recipe", RECIPE_FILE))
    (refused,) = trellis.refused_bindings(folder, outcome.shown)
    assert (refused["key"], refused["kind"]) == ("tenure", "calibration")
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        tab.wait_for_selector(".bl-error-mark", timeout=30_000)
        # The native sentence and all source controls remain in the one list.
        open_checklist(tab)
        row = tab.locator('.bl-error-line[data-severity="error"]')
        assert row.count() == 1
        assert row.locator('.bl-error-sentence').text_content() == trellis.relative_sentence(folder, refused["sentence"])
        places = row.locator('.bl-error-place').evaluate_all(
            "elements => elements.map(element => [element.dataset.path, Number(element.dataset.line)])"
        )
        assert [tuple(place) for place in places] == list(refused["places"])
        assert (RECIPE_FILE, 12) in refused["places"]
        assert tab.locator('.bl-folder .bl-checklist').count() == 0

        found = []

        def fitted(arrangement: tuple) -> bool:
            # whether the visible line, the trellis's parts in the details'
            # line, whether the visible line holds the rest, and the elements
            # wider inside than their boxes, read at one moment, are those of
            # the arrangement
            pattern, details = arrangement
            found[:] = tab.evaluate(TRELLIS_STATUS_FIT_JS)
            line, rest, rest_in_line, overflowing = found
            overflowing += tab.locator(
                '.bl-error-list, .bl-error-line, .bl-error-sentence, .bl-error-place'
            ).evaluate_all("""elements => elements.filter(element =>
                element.scrollWidth > element.clientWidth).map(element =>
                [element.tagName.toLowerCase() + '.' + element.className,
                 element.textContent, element.scrollWidth, element.clientWidth])""")
            return (
                line is not None
                and pattern.fullmatch(line) is not None
                and rest == details
                and rest_in_line is (details is None)
                and overflowing == []
            )

        # Matsya folded, the graph holding its width: the whole line fits
        wait_until(lambda: fitted(WHOLE_LINE), 10.0, "the whole status line with Matsya folded")
        # Matsya opened by the main bar's toggle (unit N, Task 1), the columns
        # those at which Task 6 measured the line
        tab.click(MATSYA_TOGGLE)
        wait_until(lambda: tracks_near(tab, FRAME_TRACKS[1600, False]), 5.0, "Matsya opened")
        open_checklist(tab)
        for (width, height), arrangements in STATUS_WINDOWS:
            tab.set_viewport_size({"width": width, "height": height})
            try:
                wait_until(
                    lambda arrangements=arrangements: any(map(fitted, arrangements)),
                    10.0,
                    f"the status line at {width} px",
                )
            except AssertionError:
                raise AssertionError((width, found)) from None
            line, rest, _, _ = found
            print(f"task 6: at {width} px the visible line {line!r}, the details' {rest!r}")

        tab.set_viewport_size({"width": 1600, "height": 1000})
        # a fold's summary a row in Label, the graph column's head in Head,
        # with no spacing and no change of case (design pass 8 §5.1; unit
        # M, Task 7)
        label, head = tab.evaluate(
            TYPE_FACES_JS, ["summary.bl-fold-summary", ".bl-graph-bar .bl-graph-name"]
        )
        assert label[1:] == ["13px", "400", "normal", "none"], label
        assert head[1:] == ["13px", "600", "normal", "none"], head
        assert label[0].split(",")[0].strip('"') == head[0].split(",")[0].strip('"') == "Archivo"
        for path in ADJUSTER_CONS_FILES:
            reveal_in_tree(tab, path)
        names = {name["path"]: name for name in tree_names(tab)}
        found = [names[path] for path in ADJUSTER_CONS_FILES]
        print(f"task 6: the tree's names {[(name['shown'], name['cut']) for name in found]}")
        # cut at their end after a whole word, as unit L's Task 22 replaced
        # the cut in the middle (L-D13; defect 23 of the UX simulation)
        assert all(name["cut"] and not cut_within_a_word(name) for name in found), found
        assert [name["shown"] for name in found] == ["adjuster"] * 2, found
    finally:
        context.close()


def test_task_7_one_wire_per_adjacent_pair_and_the_control_in_the_gap_under_it(
    browser, server_on, durables_folder
):
    """Task 7 (design pass §3 (a) and §5 item 7; K-D5, K-D13; design pass
    13 §1, rule 4): on the durables model's forward trellis graph, periods
    0 to 2, the layout's records with the periods and their occurrences
    open hold one piece of the graph's root for each wire from a period to
    the next, two from each, the pieces of both consumption stages' wires
    into the next period's `tenure`, which meet in the gap and share the
    run into its socket, and the graph is at most 4,500 px wide at scale
    1. Drawn on the page, with its `+ period` controls, adjacent period
    layers stand at most 200 px apart, each control between two of them
    standing in the gap under the shared run, and the drawing is at most
    4,500 px wide. A click on the shared
    piece from periods[1] selects the pair, and Details print both writers'
    measures and the six joins of the mapping, with `remove`; a click on a
    writer's own piece selects that writer's join again."""
    context, tab = new_tab(browser)
    try:
        _, records = durables_forward(tab, server_on(durables_folder))
        pairs = sorted(
            (PERIOD_PORT.match(source)[1], PERIOD_PORT.match(target)[1])
            for source, target in records["rootEdges"]
            if PERIOD_PORT.match(source) and PERIOD_PORT.match(target)
        )
        print(f"task 7: the root's pieces between periods {pairs}, {records['width']} px wide")
        assert pairs == [("periods[1]", "periods[0]")] * 2 + [("periods[2]", "periods[1]")] * 2
        assert records["width"] <= WIDTH_MOST

        # the page's drawing, the shared pieces taking their records
        drawn, _ = wait_until(
            lambda: (found := tab.evaluate(DRAWN_PLACES_JS))
            and sorted(piece["from"] or "" for piece in found["pairs"])
            == ["periods[1]", "periods[2]"]
            and found,
            30.0,
            "the shared pieces drawn as join wires",
        )
        nodes = drawn["nodes"]
        period = [nodes[f"periods[{h}]{LAYER_ID_ENDING}"] for h in range(3)]
        gaps = [period[h]["x"] - period[h + 1]["x"] - period[h + 1]["width"] for h in range(2)]
        width = max(n["x"] + n["width"] for n in nodes.values()) - min(
            n["x"] for n in nodes.values()
        )
        print(f"task 7: on the page the periods stand {gaps} px apart, {width} px wide")
        assert all(0 < gap <= GAP_MOST for gap in gaps), gaps
        assert width <= WIDTH_MOST
        for h in (2, 1):
            control = nodes[f"add-period::between periods[{h}] and periods[{h - 1}]"]
            earlier, later = period[h], period[h - 1]
            (piece,) = [piece for piece in drawn["pairs"] if piece["from"] == f"periods[{h}]"]
            assert earlier["x"] + earlier["width"] < control["x"], (control, earlier)
            assert control["x"] + control["width"] < later["x"], (control, later)
            assert control["y"] >= piece["y"] + piece["height"], (control, piece)

        click_join(tab, "periods[1]", "periods[0]/tenure")
        details_until(tab, PAIR_JOIN_DETAILS, "Details of the pair of periods")
        assert [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]] == [
            ("periods[1]", "periods[0]/tenure")
        ]
        remove = tab.locator(".bl-join-details .bl-join-remove")
        assert remove.get_attribute("title") == "Remove the join from trellis.yml"
        assert tab.evaluate(DETAILS_OVERFLOW_JS) == []

        click_join(tab, "periods[1]/adjuster_cons", "periods[0]/tenure")
        details_until(tab, ADJUSTER_CONS_JOIN_DETAILS, "Details of one writer's join again")
    finally:
        context.close()


def test_task_8_a_trellis_opens_on_its_terminal_period_with_matsya_folded(
    browser, server_on, durables_folder
):
    """Task 8 (design pass §1 items 4 and 11 and §5 item 8; K-D6; spec 0.4
    §§2.3 and 5.1): the durables model's recipe opened from the tree shows
    its backward trellis graph with Matsya folded and the graph taking the
    width Matsya gives up, the folder and the text keeping theirs
    (TRELLIS_TRACKS; K-D19), and nothing of the fold kept in the browser's
    storage. The graph opens on `periods[0]`'s layer at the largest scale,
    at most 1 and at least 0.6, at which the layer fills the region, its
    name drawn there and its body cut where it is taller than the region
    (K-D22 as AAS's M-D15 amends it); the forward graph opens alike. The
    main bar's toggle `Matsya` (unit N, Task 1; design pass 10 §3), in
    place of the bar's Υ, opens Matsya in the trellis view, the columns
    returning to frame 7b's widths and the graph opened again on
    `periods[0]` at the region's new size. A stage file opened from the
    tree shows Matsya open and its graph opened as spec 0.4 §2.3 states, as
    M-D15 amends it: at the largest scale, at most 1 and at least 0.6, at
    which its width fits, centered where it fits whole and else from its
    beginning; at 1280 × 800 Matsya's column measures 300 px, and the
    trellis shown by the button `trellis` folds Matsya while the text keeps
    its width."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        fold, unfold = tab.locator(MATSYA_FOLD), tab.locator(MATSYA_TOGGLE)
        wait_until(
            lambda: tracks_near(tab, TRELLIS_TRACKS[1600, False]),
            10.0,
            "Matsya folded in the trellis view",
        )
        assert fold.get_attribute("aria-expanded") == "false"
        assert unfold.get_attribute("aria-expanded") == "false"
        assert tab.locator(".bl-window[data-folded-matsya]").count() == 1
        assert layout_record(tab, durables_folder) is None

        backward = opened_on_the_terminal_period(tab, "the backward graph open on periods[0]")
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph")
        forward = opened_on_the_terminal_period(tab, "the forward graph open on periods[0]")
        scales = (backward["zoom"], forward["zoom"])
        print(f"task 8: opened at {scales[0]:.3f} backward and {scales[1]:.3f} forward")
        assert READING_SCALE <= min(scales) and max(scales) <= 1

        # the main bar's `Matsya` opens Matsya in the trellis view; the view,
        # still at its opening, opens again at the region's new size (spec
        # 0.4 §2.3)
        unfold.click()
        wait_until(
            lambda: tracks_near(tab, FRAME_TRACKS[1600, False]),
            5.0,
            "Matsya opened in the trellis view",
        )
        assert fold.get_attribute("aria-expanded") == "true"
        opened_on_the_terminal_period(tab, "the forward graph open again on periods[0]")

        # a stage's graph opens as spec 0.4 §2.3 states, as M-D15 amends it:
        # at the largest scale, at most 1 and at least 0.6, at which its
        # width fits, from its left or its top where it is not read whole;
        # laid out downward, as the stage graph opened before design pass 14
        lay_out_top_to_bottom(tab)
        reveal_in_tree(tab, ADJUSTER_CONS_FILE)
        tab.click(f'.bl-tree-file[data-path="{ADJUSTER_CONS_FILE}"]')
        wait_until(lambda: status_settled_on(tab, ADJUSTER_CONS_FILE), 60.0, "the stage's loop")
        seen = []

        def as_a_graph_opens() -> bool:
            seen[:] = [viewport(tab), tracks(tab), tab.evaluate(WHOLE_GRAPH_SHOWN_JS)]
            view, _, whole = seen
            if view is None or not tracks_near(tab, FRAME_TRACKS[1600, False]):
                return False
            if whole:
                return READING_SCALE - 1e-6 <= view["zoom"] <= 1
            extent = drawn_extent(tab.evaluate(DRAWN_PLACES_JS)["nodes"])
            expected = max(READING_SCALE, min(1.0, (view["width"] - 20) / extent))
            return abs(view["zoom"] - expected) * extent <= 2 and (
                abs(view["x"] - 10) <= 1 or abs(view["y"] - 10) <= 1
            )

        try:
            wait_until(as_a_graph_opens, 30.0, "the stage's graph opened as spec 0.4 §2.3 states")
        except AssertionError:
            raise AssertionError(seen) from None
        stage = seen[0]
        print(f"task 8: the stage's graph opened at {stage}")

        # at 1220 Matsya's column has given up width to its least, 300 px,
        # the step that stood at 1280 before the window's right margin of 60
        # px left (design pass 13 §4; Q-D6); the trellis view folds it, the
        # graph taking its width and the text keeping its own
        tab.set_viewport_size({"width": 1220, "height": 800})
        wait_until(lambda: tracks_near(tab, FRAME_TRACKS[1220, False]), 5.0, "the columns at 1220")
        text = tracks(tab)[1]
        tab.click(".bl-trellis-button")
        wait_until(
            lambda: tracks_near(tab, TRELLIS_TRACKS[1220, False]),
            30.0,
            "Matsya folded in the trellis view at 1220",
        )
        assert tracks(tab)[1] == text
        print(f"task 8: at 1220 the columns {FRAME_TRACKS[1220, False]} and {tracks(tab)}")
    finally:
        context.close()


# the stage file `new stage` writes for the key buyer, the methods file `new
# file` writes for it, the address of its methods slot in the recipe, and
# the button `New file` beside that slot in the Recipe tab (K-D7; unit M,
# Task 10)
BUYER_FILE = "declaration/stages/buyer/buyer.bl"
BUYER_METHODS = "declaration/stages/buyer/methods.yml"
BUYER_METHODS_SLOT = "stages.buyer.methods.all[0]"
BUYER_NEW_FILE = (
    f'.bl-recipe-row[data-stage="buyer"] .bl-new-file[data-address="{BUYER_METHODS_SLOT}"]'
)
# the four block headers of the empty stage file, as the page Stages writes
# each block's header, with no field on either side
EMPTY_HEADERS = [
    "[id=arvl_to_dcsn, () : !arvl -> () : !dcsn] {",
    "[id=dcsn_to_cntn, () : !dcsn -> () : !cntn] {",
    "[id=cntn_to_dcsn, () : !cntn -> () : !dcsn] {",
    "[id=dcsn_to_arvl, () : !dcsn -> () : !arvl] {",
]


def test_task_9_new_stage_and_new_file_write_the_author_s_own_files(
    browser, server_on, scratch_folder
):
    """Task 9 (the usability walkthrough §4 item 1 and §5; K-D7). On a copy
    of the portfolio model with its trellis shown, the folder bar's `new
    stage` with the key buyer writes declaration/stages/buyer/buyer.bl,
    holding `@stage: buyer` and the four block headers with no field, writes
    the stage's row into the recipe on disk with it, no file then unsaved
    (unit L, Task 17; defect 22 of the UX simulation), and opens the stage
    file in the editor. The recipe's document tab then opens the recipe, the
    panel under the editor on its Recipe tab (unit M, Task 10; design pass 9
    §2; the rail's `Recipe` having left with the rail, unit N, Task 1),
    which holds the row buyer, and, the row opened by a click (design pass
    11 §2), `New file` beside its methods slot writes
    declaration/stages/buyer/methods.yml and opens it in the editor, its
    name written in the slot's place in the recipe's text, one edit of its
    buffer (design pass 9 §4). The trellis's reading stands refused, since
    no period holds buyer, so the tab keeps the rows of the last reading
    that answered (AAS, M-D7; unit M, Task 5) and the recipe's text is
    read in the editor."""
    recipe_file = scratch_folder / RECIPE_FILE
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_folder), RECIPE_FILE)
        tab.click(".bl-new-stage")
        tab.wait_for_selector('.bl-form[data-form="new stage"]', timeout=10_000)
        tab.fill(".bl-new-stage-key input", "buyer")
        tab.click(".bl-new-stage-submit")
        wait_until(lambda: open_path_shown(tab) == BUYER_FILE, 30.0, "the stage file open")
        text = (scratch_folder / BUYER_FILE).read_text(encoding="utf-8")
        assert text.splitlines()[0] == "@stage: buyer"
        assert [line for line in text.splitlines() if line.startswith("[id=")] == EMPTY_HEADERS
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 10.0, "the stage file's text")
        row = f"  buyer: {creation.recipe_row('buyer')}\n"
        assert recipe_file.read_text(encoding="utf-8").endswith(row)
        wait_until(lambda: unsaved_in_tree(tab) == [], 10.0, "no file unsaved")
        tab.click(f'.bl-tab[data-path="{RECIPE_FILE}"]')
        wait_until(lambda: open_path_shown(tab) == RECIPE_FILE, 30.0, "the recipe open")
        tab.wait_for_selector('.bl-recipe-row[data-stage="buyer"]', timeout=60_000)
        open_recipe_row(tab, "buyer")
        tab.wait_for_selector(BUYER_NEW_FILE, timeout=60_000)
        print(f"task 9: the refusals once the recipe names buyer: {error_lines(tab)}")
        tab.click(BUYER_NEW_FILE)
        wait_until(lambda: open_path_shown(tab) == BUYER_METHODS, 30.0, "the methods file open")
        methods = (scratch_folder / BUYER_METHODS).read_text(encoding="utf-8")
        assert methods == "stage: buyer\nmethods: []\n"
        tab.click(f'.bl-tab[data-path="{RECIPE_FILE}"]')
        wait_until(lambda: open_path_shown(tab) == RECIPE_FILE, 30.0, "the recipe open again")
        wait_until(
            lambda: entry_value(tab.evaluate(DOCUMENT_JS), BUYER_METHODS_SLOT)
            == "stages/buyer/methods",
            30.0,
            "the slot's file written in the recipe's text",
        )
    finally:
        context.close()


# the methods file that the portfolio model's recipe names for `cons`, and
# its line 5, the method of the entry `on: policy`
CONS_METHODS = "declaration/stages/cons/methods.yml"
POLICY_METHOD = "    method: !egm"
# the select of the row of a target in the Methods tab
METHOD_SELECT = '.bl-values-row[data-name="{}"] select.bl-values-method'


def test_task_10_the_methods_tab_offers_at_policy_the_tags_the_package_admits_there(
    browser, server_on, scratch_folder
):
    """Task 10 (the usability walkthrough §4 item 10 and §5; AMD-MI-002 §5
    rule 5), with the offer of unit L's Task 18 (K-I150). On a copy of the
    portfolio model with `cons.bl` open, the BellmanType panel's Methods tab
    names the methods file that the recipe names for `cons`. The select of
    the row `policy` offers the tags the package admits at that target,
    `admitted_methods` of `bellman.stage`, in the method table's order, and
    no other: `!egm`, since the policy block writes the grid line, and not
    `!vfi`, which stands on the backward decision builder alone; the select
    of the row `cntn_to_dcsn.value`, a statement, offers the three
    representations. `!time-iteration` chosen at `policy` replaces `!egm` at
    line 5 of the methods file on disk, no other line changing, and the row
    then shows the tag chosen."""
    methods = scratch_folder / CONS_METHODS
    lines = methods.read_text(encoding="utf-8").split("\n")
    assert lines[4] == POLICY_METHOD
    cons = elaborate_text((scratch_folder / CONS).read_text(encoding="utf-8"), CONS)
    admitted = admitted_methods(cons, "policy")
    assert "!egm" in admitted and "!vfi" not in admitted
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(scratch_folder), CONS)
        tab.click('.bl-class-tab[data-tab="Methods"]')
        tab.wait_for_selector('.bl-values[data-tab="Methods"]', timeout=10_000)
        assert tab.locator(".bl-values-file").text_content() == f"writes {CONS_METHODS}"
        policy = tab.locator(METHOD_SELECT.format("policy"))
        policy.wait_for(timeout=30_000)
        assert policy.locator("option").all_text_contents() == list(admitted)
        value = tab.locator(METHOD_SELECT.format("cntn_to_dcsn.value"))
        representations = ["!Cartesian", "!Linear", "!pchip"]
        assert value.locator("option").all_text_contents() == representations
        policy.select_option("!time-iteration")
        lines[4] = "    method: !time-iteration"
        wait_until(
            lambda: methods.read_text(encoding="utf-8") == "\n".join(lines),
            30.0,
            "!time-iteration written at line 5 of the methods file",
        )
        wait_until(
            lambda: policy.input_value() == "!time-iteration",
            30.0,
            "the row policy showing the tag chosen",
        )
    finally:
        context.close()


# the period file of the portfolio model, which writes the period's connector
PERIOD_FILE = "declaration/period.yml"
# The ports of the copy `emptied_portfolio` that the joins of Task 11 name
# are those Task 15's test names on its copy of cons-port, whose periods hold
# the same stage keys: `M_NEXT` and `CONS_M`, `port`'s `m_next` and `cons`'s
# `m` in periods[2]; `DISC_A` and `PORT_K`, `disc`'s `a` in periods[3] and
# `port`'s `k` in periods[2].
# the status line of the join of `disc` to the next period's `port`
DISC_TO_PORT = "trellis.yml, inter_connectors[0]: a: k written, entry, periods 0–5"
# the least scale of the region (flow-canvas.js, MIN_ZOOM)
LEAST_SCALE = 0.05
# a port on a card (design pass 13 §1, rules 1 and 3): its press target, held
# at no less than TARGET px on the screen at every scale, and its mark, a
# square of MARK_AT_ONE px at scale 1, drawn at the view's scale and held at
# no less than MARK_LEAST px on the screen
TARGET, MARK_AT_ONE, MARK_LEAST = 10, 6, 3
# The tolerance of a port's size measured on the screen: the browser lays
# out the element's width in units of 1/64 px before the region's transform
# scales it, so a target the page keeps at 10 px measures up to 1/64 px
# times the scale less than 10 px.
SUBPIXEL = 0.01
# The size on the screen of each port the region draws for a drag, {port,
# box, width, height, mark}: the cables' ports of the cards that are not
# hidden (design pass 10 §6; unit N, Task 7) and the unjoined ports of a
# closed period's box (J-D47), box the id of the box that carries it (unit
# K's decision K-D9), width and height its press target's on the screen and
# mark the size of its mark in its box's own pixels, which the region's
# transform scales (design pass 13 §1, rule 3).
PORT_SIZES_JS = """
() => Array.from(document.querySelectorAll(
    '.bl-view-host .react-flow__handle.bf-unjoined, '
    + '.bl-view-host .react-flow__handle.bf-cable-port:not(.bf-cable-hidden)'),
  (port) => {
    const at = port.getBoundingClientRect();
    return {port: port.dataset.port, box: port.closest('.react-flow__node').dataset.id,
            plug: port.classList.contains('bf-cable-branch'), width: at.width, height: at.height,
            mark: parseFloat(getComputedStyle(port, '::before').width)};
  })
"""


def assert_port_sizes(sizes: list[dict], zoom: float) -> None:
    """Asserts that every port of `sizes` (PORT_SIZES_JS), drawn at the scale
    `zoom`, measures its press target at least TARGET px across on the
    screen and its mark MARK_AT_ONE px at that scale, or MARK_LEAST px where
    that is less (design pass 13 §1, rule 3; K-D9)."""
    for size in sizes:
        assert min(size["width"], size["height"]) >= TARGET - SUBPIXEL, size
        assert abs(size["mark"] * zoom - max(MARK_AT_ONE * zoom, MARK_LEAST)) <= 0.05, (size, zoom)


def close_to_card(tab, box: str) -> None:
    """Closes the stage occurrence whose layer id is `box` to its closed card
    (design pass 13 §2, rule 4): the compact card's chevron opens the
    occurrence with every builder open, and the open layer's toggle then
    closes it; the card stands once FRAME_TEXTS_JS reads it."""
    click_toggle(tab, box)
    wait_until(
        lambda: tab.locator(
            f'.bl-view-host .react-flow__node[data-id="{box}"] > .bf-layer:not(.bf-compact)'
        ).count()
        == 1,
        30.0,
        f"{box} drawn in full",
    )
    click_toggle(tab, box)
    wait_until(lambda: tab.evaluate(FRAME_TEXTS_JS, box), 10.0, f"{box} closed")


def unjoined_on_card(page, box: str) -> list[str]:
    """The ids, sorted, of the field ports that no join reaches which the
    cable ports of the card whose node has the id `box` name in
    `data-unjoined` (design pass 10 §6; unit N, Task 7)."""
    return sorted(
        field
        for port in cable_ports(page)
        if port["box"] == box and not port["hidden"]
        for field in port["unjoined"]
    )
# The center on the screen of the name of the open layer whose id is the
# argument, null where it is not drawn.
LAYER_NAME_JS = """
(id) => {
  const name = document.querySelector(
    `.bl-view-host .react-flow__node[data-id="${CSS.escape(id)}"] > .bf-layer > .bf-layer-name`);
  if (!name) return null;
  const at = name.getBoundingClientRect();
  return {x: (at.left + at.right) / 2, y: (at.top + at.bottom) / 2};
}
"""
# What the region shows while the button of a drag between two frames is
# held (unit K's decision K-D8): the ids of the boxes whose frame is marked
# as the frame the drag would reach, whether the region is marked as
# dragging, and the color of the drag's line, null where none is drawn.
FRAME_DRAG_JS = """
() => {
  const line = document.querySelector('.bl-view-host .bf-frame-line');
  return {
    targets: Array.from(document.querySelectorAll('.bl-view-host .react-flow__node'))
      .filter((node) => node.querySelector(':scope > .bf-frame-target'))
      .map((node) => node.dataset.id),
    connecting: !!document.querySelector('.bl-view-host .bf-region.bf-connecting'),
    line: line ? getComputedStyle(line).stroke : null,
  };
}
"""
# The list that a drag between two frames opens, null where none is open:
# its head, each row's field, whether it is ticked, the arrival field its
# select shows and the texts of the select's options, and whether the
# button `join` acts (unit K's decision K-D8).
PAIR_LIST_JS = """
() => {
  const list = document.querySelector('.bl-view-host .bf-pair-list');
  if (!list) return null;
  return {
    head: list.querySelector('.bf-pair-head').textContent,
    rows: Array.from(list.querySelectorAll('.bf-pair-row'), (row) => {
      const select = row.querySelector('.bf-pair-to');
      return [row.querySelector('.bf-pair-from').textContent,
              row.querySelector('.bf-pair-tick').checked,
              select.options[select.selectedIndex].textContent,
              Array.from(select.options, (option) => option.textContent)];
    }),
    join: !list.querySelector('.bf-pair-join').disabled,
  };
}
"""


def drag_frames(page, writer: str, reader: str) -> dict:
    """A drag by the pointer from the frame of the open stage occurrence
    `writer`, `periods[2]/port`, to the frame of `reader` (unit K's decision
    K-D8), made at the scale at which both stand in the region: the graph
    fitted with its button `fit`, the button pressed on the writer's name,
    the pointer moved in steps to the reader's name and released there.
    Answers what the region showed while the button was held over the
    reader (FRAME_DRAG_JS): `targets`, `connecting` and `line`."""
    page.click(".bl-zoom-button[data-zoom='fit']")
    page.evaluate(TWO_FRAMES_JS)
    start = page.evaluate(LAYER_NAME_JS, writer + LAYER_ID_ENDING)
    end = page.evaluate(LAYER_NAME_JS, reader + LAYER_ID_ENDING)
    page.mouse.move(start["x"], start["y"])
    page.mouse.down()
    page.mouse.move(end["x"], end["y"], steps=12)
    page.evaluate(TWO_FRAMES_JS)
    state = page.evaluate(FRAME_DRAG_JS)
    page.mouse.up()
    page.evaluate(TWO_FRAMES_JS)
    return state


def test_task_11a_every_cable_port_keeps_its_size_on_the_screen_at_fit_and_at_the_least_scale(
    browser, server_on, tmp_path
):
    """Task 11 (a) (the usability walkthrough §4 item 5 and §5, "Join two
    stages"; K-D9), its ports the cables' since unit N's Task 7 (design
    pass 10 §6). On the trial copy of the portfolio model,
    `emptied_portfolio`, whose period connector and inter-period mapping
    are emptied, its forward trellis graph shown: the fields the cards'
    ports name as unjoined are those `trellis.unjoined_ports` answers, and
    at the scale the button `fit` sets, below 1, where a mark of 6 px at
    scale 1 would measure less than 6 px, every cable port the region
    draws, one per continuation branch and one per arrival tuple on each
    card, measures its press target at least 10 px across on the screen
    and its mark 6 px at the view's scale, 3 px at the least (design pass
    13 §1, rules 1 and 3), and so at the least scale of the region, 0.05.
    With `port` in periods[2] closed to its card (K-D15), the card keeps
    its two ports, which name that occurrence's two unjoined fields, each
    of those sizes at the scale `fit` then sets."""
    copy = emptied_portfolio(tmp_path / "portfolio")
    shown = trellis.show_trellis(
        model.open_folder(copy), recipe.Source("recipe", RECIPE_FILE)
    ).shown
    ports = sorted(port["id"] for port in trellis.unjoined_ports(shown, {}))
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        choose_view(tab, None, "forward")
        wait_until(lambda: unjoined_field_ids(tab) == ports, 30.0, "the forward graph's ports")
        drawn = sorted(p["port"] for p in cable_ports(tab) if not p["hidden"])
        assert drawn
        tab.click(".bl-zoom-button[data-zoom='fit']")
        tab.evaluate(TWO_FRAMES_JS)
        fit = viewport(tab)
        assert MARK_AT_ONE * fit["zoom"] < MARK_AT_ONE, fit
        for zoom in (fit["zoom"], LEAST_SCALE):
            view = {"x": fit["x"], "y": fit["y"], "zoom": zoom}
            flow_handle(tab, "setView", {"viewport": view, "selection": None})
            wait_until(lambda zoom=zoom: viewport(tab)["zoom"] == zoom, 5.0, f"the scale {zoom}")
            tab.evaluate(TWO_FRAMES_JS)
            sizes = tab.evaluate(PORT_SIZES_JS)
            assert sorted(size["port"] for size in sizes) == drawn
            # every port's press target keeps 10 px on the screen and its mark 6 px at the view's scale, 3 px at the
            # least (design pass 13 §1, rules 1 and 3; under design pass 11 §1a a socket measured 8 px and a plug 6 px)
            least = min(min(size["width"], size["height"]) for size in sizes)
            print(f"task 11: at the scale {zoom:.3f} the least cable port's target is {least:.2f} px")
            assert_port_sizes(sizes, zoom)

        # the card of `port` in periods[2], closed, at the scale `fit` sets
        frame = f"periods[2]/port{LAYER_ID_ENDING}"
        close_to_card(tab, frame)
        own = sorted(port for port in ports if port.startswith("periods[2]/port/"))
        wait_until(lambda: unjoined_on_card(tab, frame) == own, 10.0, "the card's ports")
        tab.click(".bl-zoom-button[data-zoom='fit']")
        tab.evaluate(TWO_FRAMES_JS)
        zoom = viewport(tab)["zoom"]
        sizes = tab.evaluate(PORT_SIZES_JS)
        assert unjoined_field_ids(tab) == ports
        on_frame = [size for size in sizes if size["box"] == frame]
        assert len(on_frame) == 2, on_frame
        least = min(min(size["width"], size["height"]) for size in on_frame)
        print(f"task 11: at the scale {zoom:.3f} the least port's target of the card is {least:.2f} px")
        # the card's ports keep their targets of 10 px and their marks on the screen (design pass 13 §1, rule 3; K-D9)
        assert MARK_AT_ONE * zoom < MARK_AT_ONE, zoom
        assert_port_sizes(on_frame, zoom)
    finally:
        context.close()


# The occurrence `tenure` of periods[1] in the durables model, whose two
# branches, `keep` and `adjust`, give its card two writing ports on one
# edge, G.cablePitch apart at scale 1, while it is open and while it is
# closed (design pass 10 §6; unit N, Task 7).
TENURE = "periods[1]/tenure"
TENURE_BRANCHES = ["keep", "adjust"]
# the distance in pixels on the screen between the centers of two ports of
# one edge at which the test also reads them: less than the 10 px each
# target measures across, so that the targets overlap, and more than half
# of it, so that each center stands clear of the other's target, which the
# pointer at a center would otherwise take (design pass 13 §1, rule 3)
CROWDED = 6
# The viewport, {x, y, zoom}, that centers in the region at the scale given
# the middle of the ports whose ids in the graph JSON are given, and the
# distance between the first two ports' centers at scale 1, `apart`.
PORTS_CENTERED_JS = """
([ids, zoom]) => {
  const flow = document.querySelector('.bl-view-host .react-flow');
  const pane = flow.getBoundingClientRect();
  const view = new DOMMatrixReadOnly(
    getComputedStyle(flow.querySelector('.react-flow__viewport')).transform);
  const centers = ids.map((id) => {
    const at = document.querySelector(
      `.bl-view-host .react-flow__handle[data-port="${id}"]`).getBoundingClientRect();
    return [((at.left + at.right) / 2 - pane.left - view.e) / view.a,
            ((at.top + at.bottom) / 2 - pane.top - view.f) / view.a];
  });
  const x = centers.reduce((sum, c) => sum + c[0], 0) / centers.length;
  const y = centers.reduce((sum, c) => sum + c[1], 0) / centers.length;
  return {view: {x: pane.width / 2 - x * zoom, y: pane.height / 2 - y * zoom, zoom: zoom},
          apart: Math.hypot(centers[0][0] - centers[1][0], centers[0][1] - centers[1][1])};
}
"""
# The center on the screen and the size of the element of each port whose
# id in the graph JSON is given.
PORT_PLACES_JS = """
(ids) => ids.map((id) => {
  const at = document.querySelector(
    `.bl-view-host .react-flow__handle[data-port="${id}"]`).getBoundingClientRect();
  return {port: id, x: (at.left + at.right) / 2, y: (at.top + at.bottom) / 2,
          width: at.width, height: at.height};
})
"""
# The id in the graph JSON of the port whose element is under the point of
# the screen given, null where no port's element is.
PORT_UNDER_JS = """
([x, y]) => {
  const found = document.elementFromPoint(x, y);
  const port = found && found.closest('.react-flow__handle');
  return port ? port.dataset.port || null : null;
}
"""


def ports_where_the_pointer_stops(page, ports: list[str]) -> list[dict]:
    """For each port of `ports`, ids in the graph JSON: its center and size
    on the screen (PORT_PLACES_JS) and `under`, the port whose element is
    under its center once the pointer has moved there (PORT_UNDER_JS), the
    port a press there would take."""
    places = page.evaluate(PORT_PLACES_JS, ports)
    for place in places:
        page.mouse.move(place["x"], place["y"])
        place["under"] = page.evaluate(PORT_UNDER_JS, [place["x"], place["y"]])
    return places


def test_task_11a_two_ports_of_one_edge_keep_their_size_and_each_is_taken_at_its_center(
    browser, server_on, durables_folder
):
    """Task 11 (a) where two ports a drag can take stand on one edge (K-D9;
    row K-I165), the ports the cables' since unit N's Task 7 (design pass
    10 §6). On the durables model's forward graph, periods 0 to 2, the two
    branch ports of `tenure` in periods[1], `keep` and `adjust`, stand on
    one edge of its card, G.cablePitch apart at scale 1, while it is open
    and, the occurrence closed, while it is a closed card. At the scale the
    button `fit` sets, at which their centers stand less than 10 px apart
    on the screen, the targets overlapping, and at the scale at which they
    stand 6 px apart, each port's press target measures at least 10 px
    across (design pass 13 §1, rule 3), and, each center standing clear of
    the other's target, the pointer stopped at each port's center has that
    port under it, so that a press there takes it and not its
    neighbor."""
    closed = TENURE + LAYER_ID_ENDING
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: [
                port["branch"]
                for port in cable_ports(tab)
                if port["box"] == closed and port["side"] == "writing"
            ]
            == TENURE_BRANCHES,
            60.0,
            "the two branch ports of tenure",
        )
        G = tab.evaluate("() => window.BellmanFlowLayout.G")
        for state in ("open", "closed"):
            if state == "closed":
                close_to_card(tab, closed)
            branches = [cable_port(tab, TENURE, "writing", branch) for branch in TENURE_BRANCHES]
            tab.click(".bl-zoom-button[data-zoom='fit']")
            tab.evaluate(TWO_FRAMES_JS)
            fit = viewport(tab)["zoom"]
            apart = tab.evaluate(PORTS_CENTERED_JS, [branches, fit])["apart"]
            assert abs(apart - G["cablePitch"]) <= 0.5, (state, apart)
            # the two targets overlap at the fit, each center clear of the other's target
            assert TARGET / 2 < apart * fit < TARGET, (state, apart, fit)
            # the scale at which the two centers stand CROWDED px apart, to
            # four places, the transform of the region's view printing six
            # figures
            for zoom in (fit, round(CROWDED / apart, 4)):
                if zoom != fit:
                    centered = tab.evaluate(PORTS_CENTERED_JS, [branches, zoom])
                    flow_handle(tab, "setView", {"viewport": centered["view"], "selection": None})
                    wait_until(
                        lambda zoom=zoom: abs(viewport(tab)["zoom"] - zoom) < 1e-6,
                        5.0,
                        f"the scale {zoom}",
                    )
                    tab.evaluate(TWO_FRAMES_JS)
                places = ports_where_the_pointer_stops(tab, branches)
                between = math.dist(*((place["x"], place["y"]) for place in places))
                least = min(min(place["width"], place["height"]) for place in places)
                print(
                    f"task 11: {state}, at the scale {zoom:.3f} the two ports stand "
                    f"{between:.2f} px apart and the least is {least:.2f} px"
                )
                # two writing ports' targets are 10 px on the screen (design pass 13 §1, rule 3; 6-px plugs under
                # design pass 11 §1a); they stand closer than 10 px at this scale, their targets overlapping, and
                # the pointer at each center takes that port
                assert between < TARGET and least >= TARGET - SUBPIXEL, places
                assert [place["under"] for place in places] == branches, places
    finally:
        context.close()


def test_task_11b_a_drag_between_two_frames_offers_the_pairs_ticked_and_join_writes_them(
    browser, server_on, tmp_path
):
    """Task 11 (b) (the usability walkthrough §4 item 5 and §5; K-D8,
    J-D41). On the trial copy `emptied_portfolio`, its forward trellis
    graph fitted to the region: a drag from the frame of `port` in
    periods[2] to the frame of `cons` in periods[2] draws its line in
    ultramarine-light and marks `cons`'s frame while the button is held,
    and its release opens the list headed `periods[2]/port →
    periods[2]/cons` whose one row, `port`'s unjoined continuation field
    `m_next`, has `m` chosen among `cons`'s arrival fields and is ticked,
    each field printed with its declared set (K-D25).
    The button `join` sends one event `connected` that names the reading
    drawn, the two frames and the pair's two ports, and the line written is
    the drag's of unit J: the note `trellis.connector_edit` gives for the
    drag from `m_next` to `m`, `{m_next: m}` in the buffer of the period
    file, which opens at it, the join on its wire in every period, the file
    on disk unchanged. A drag from the frame of `disc` in periods[3] to that
    of `port` in periods[2] proposes nothing, since `a` and `k` pair by no
    name: its row stands unticked with `—` chosen and `join` does not act,
    and Escape closes the list with nothing sent. Opened again, `k` chosen
    by the author ticks the row, and `join` writes `a: k` into the
    inter-period mapping."""
    copy = emptied_portfolio(tmp_path / "portfolio")
    before = (copy / PERIOD_FILE).read_text(encoding="utf-8")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", RECIPE_FILE)).shown
    drag = trellis.connector_edit(
        shown, connected_event(shown, folder, (2, "port", "m_next"), (2, "cons", "m")), {}
    )
    assert drag.note == "period.yml, connectors[0]: {m_next: m} written, flat, periods 0–5"
    (typed,) = drag.edits.values()
    # each field as the list prints it, with its declared set (K-D25)
    sets = {record["id"]: record["set"] for record in trellis.connectable_ports(shown, {})}
    m_next, m = field_text("m_next", sets[M_NEXT]), field_text("m", sets[CONS_M])
    a, k = field_text("a", sets[DISC_A]), field_text("k", sets[PORT_K])
    assert m_next == "m_next : ℝ₊₊"
    joined = {f"periods[{h}]/cons/cons:measure:arvl": "m_next → m" for h in range(6)}
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        choose_view(tab, None, "forward")
        wait_until(lambda: M_NEXT in unjoined_field_ids(tab), 30.0, "the forward graph's ports")
        reading = tab.evaluate(REGION_READING_JS)
        light = property_color(tab, "--bl-ultramarine-light")

        hold_events(tab, "connected")
        state = drag_frames(tab, "periods[2]/port", "periods[2]/cons")
        target = f"periods[2]/cons{LAYER_ID_ENDING}"
        assert state == {"targets": [target], "connecting": True, "line": light}
        listed, _ = wait_until(lambda: tab.evaluate(PAIR_LIST_JS), 10.0, "the list of pairs")
        assert listed == {
            "head": "periods[2]/port → periods[2]/cons",
            "rows": [[m_next, True, m, ["—", m]]],
            "join": True,
        }
        tab.click(".bl-view-host .bf-pair-join")
        assert tab.evaluate(PAIR_LIST_JS) is None
        assert held_events(tab, "connected") == [
            {
                "reading": reading,
                "source": f"periods[2]/port{LAYER_ID_ENDING}",
                "target": target,
                "pairs": [{"sourceHandle": M_NEXT, "targetHandle": CONS_M}],
            }
        ]
        release_events(tab, "connected")
        wait_until(lambda: gesture_note(tab) == drag.note, 10.0, "the note of the join")
        wait_until(
            lambda: joined.items() <= held_joins(tab).items(), 60.0, "the join in every period"
        )
        wait_until(lambda: open_path_shown(tab) == PERIOD_FILE, 30.0, "the period file open")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == typed, 10.0, "the line typed")
        assert unsaved_in_tree(tab) == [PERIOD_FILE]
        assert (copy / PERIOD_FILE).read_text(encoding="utf-8") == before

        # a drag that pairs no name proposes nothing, and nothing is sent
        # until the author chooses
        wait_until(
            lambda: {DISC_A, PORT_K} <= set(unjoined_field_ids(tab)), 60.0, "the ports again"
        )
        hold_events(tab, "connected")
        drag_frames(tab, "periods[3]/disc", "periods[2]/port")
        listed, _ = wait_until(lambda: tab.evaluate(PAIR_LIST_JS), 10.0, "the second list")
        assert listed == {
            "head": "periods[3]/disc → periods[2]/port",
            "rows": [[a, False, "—", ["—", k]]],
            "join": False,
        }
        tab.keyboard.press("Escape")
        assert tab.evaluate(PAIR_LIST_JS) is None
        assert held_events(tab, "connected") == []
        release_events(tab, "connected")
        drag_frames(tab, "periods[3]/disc", "periods[2]/port")
        wait_until(lambda: tab.evaluate(PAIR_LIST_JS), 10.0, "the second list again")
        tab.select_option(".bl-view-host .bf-pair-to", value=PORT_K)
        assert tab.evaluate(PAIR_LIST_JS)["rows"] == [[a, True, k, ["—", k]]]
        tab.click(".bl-view-host .bf-pair-join")
        wait_until(lambda: gesture_note(tab) == DISC_TO_PORT, 10.0, "the note of the entry")
    finally:
        context.close()


# The stages Task 12's form chooses, by template id, each with the key typed
# for it: the portfolio model's three, `disc` as `discount`, and the pension
# model's terminal stage as `bequest`, which the form marks `terminal
# period`; and the stage keys of the terminal period the trellis file then
# writes out, in the order chosen.
BEQUEST_FORM = (
    (PORT_ID, "port"),
    (CONS_ID, "cons"),
    (DISC_ID, "discount"),
    (TERMINAL_ID, "bequest"),
)
BEQUEST_TERMINAL = ["port", "cons", "discount", "bequest"]


def test_task_12_a_stage_marked_terminal_period_stands_in_the_terminal_period_alone(
    browser, server_on, repository
):
    """Task 12 (the usability walkthrough §4 items 7 and 17). Through the
    form `new trellis` with six periods, the pension model's terminal stage
    chosen under the key bequest and marked `terminal period`, and `disc`
    chosen as discount: the trellis file writes the terminal period out,
    its `stages` the four keys and its connectors one empty mapping, then
    period.yml, which lists the three other keys, repeated five times; each
    copied stage file's `@stage:` line reads its key, and each copied
    methods file's `stage:`; the trellis the page reads holds six periods
    and nineteen stage occurrences, four in the terminal period and three
    in each of the five before it."""
    work, _ = repository
    folder = work / "bequest-demo"
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, server_on(work))
        tab.click(".bl-new-trellis")
        tab.wait_for_selector('.bl-form[data-form="new trellis"]', timeout=30_000)
        # the test repository's folder as the parent folder (unit L, Task 13)
        tab.fill(".bl-create-parent input", str(work))
        tab.press(".bl-create-parent input", "Enter")
        tab.wait_for_selector('.bl-form .bl-form-note:text-is("writes work/<name>/")')
        tab.fill(".bl-create-name input", folder.name)
        tab.fill(".bl-create-repeat input", "6")
        for template_id, key in BEQUEST_FORM:
            row = f'.bl-template[data-template="{template_id}"]'
            tab.click(f'.bl-template-button[data-template="{template_id}"]')
            tab.wait_for_selector(f"{row}.bl-active .bl-create-key input")
            tab.fill(f"{row} .bl-create-key input", key)
        terminal = f'.bl-template[data-template="{TERMINAL_ID}"] .bl-create-period'
        tab.click(f'{terminal} [data-period="terminal"]')
        tab.wait_for_selector(f'{terminal} [data-period="terminal"][aria-pressed="true"]')
        tab.click(".bl-create-submit")
        tab.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{RECIPE_FILE}"]', timeout=30_000)
        line, _ = wait_until(
            lambda: trellis_settled(tab, RECIPE_FILE), 120.0, "the trellis's status line"
        )
        print(f"task 12: the status line: {line!r}")
        assert " · 6 periods, 19 occurrences · " in line
    finally:
        context.close()
    declaration = folder / "declaration"
    trellis_text = (declaration / "trellis.yml").read_text(encoding="utf-8")
    assert entry_value(trellis_text, "periods") == [
        {"stages": BEQUEST_TERMINAL, "connectors": [{}]},
        {"template": "period.yml", "repeat": 5},
    ]
    period = (declaration / "period.yml").read_text(encoding="utf-8")
    assert entry_value(period, "stages") == BEQUEST_TERMINAL[:3]
    for key in BEQUEST_TERMINAL:
        stage = (declaration / f"stages/{key}/{key}.bl").read_text(encoding="utf-8")
        assert stage.splitlines()[0] == f"@stage: {key}"
        methods = declaration / f"stages/{key}/methods.yml"
        if key == "bequest":
            assert not methods.exists()
        else:
            assert entry_value(methods.read_text(encoding="utf-8"), "stage") == key


# the head of the checklist on the portfolio model with the cons methods
# emptied to a slot and the period's connector emptied (K-D16; design pass 2
# §6), its words, which its twistie, a Codicon, adds nothing to (design
# pass 8 §6; unit M, Task 6), and its items, each its class, its text, its
# file and its line (K-D10): the arrival field m of cons, which no join
# reaches, at the period file's connectors; the slot is no item (Task 26,
# K-D29)
EMPTIED_HEAD = "Problems: 0 errors, 1 to review"
EMPTIED_ITEMS = [
    ["bl-checklist-unjoined", "cons · m unjoined", "declaration/period.yml", "14"],
]
# the checklist's head and its items as the page draws them: the head's
# text, whether it is unfolded, whether its list is shown, the face, the
# size and the color of the head and of the tree's first file row, the
# color of the first item, and each item's first class, text, file and
# line; the items are rows of the tree's form, whose rows carry the tree's
# face and size (design pass 8 §6; unit M, Task 6)
CHECKLIST_JS = """
() => {
  const head = document.querySelector('.bl-error-mark');
  if (!head) return null;
  const list = document.querySelector('.bl-error-list');
  const face = (e) => { const s = getComputedStyle(e); return [s.fontFamily, s.fontSize]; };
  const items = list ? Array.from(list.querySelectorAll('.bl-row')) : [];
  return {
    head: head.getAttribute('aria-label'),
    expanded: head.getAttribute('aria-expanded'),
    shown: list !== null && list.offsetParent !== null,
    faces: [face(head), face(document.querySelector('.bl-tree .bl-tree-file'))],
    colors: [getComputedStyle(head).color,
             items.length ? getComputedStyle(items[0]).color : null],
    items: items.map((e) => [e.className.split(' ').find((c) => c.startsWith('bl-checklist')),
                             e.textContent.trim(), e.dataset.file, e.dataset.line]),
  };
}
"""
# the files named by the elements of Details that carry a file and a line,
# the legend's title and the head of the refusal's row
DETAILS_FILES_JS = """
() => ({
  files: Array.from(document.querySelectorAll('.bl-panel-body [data-path][data-line]'),
                    (e) => e.dataset.path),
  legend: (document.querySelector('.bl-panel-body .bl-legend-name') || {}).textContent || null,
  refusal: (document.querySelector('.bl-panel-body .bl-refusal') || {}).textContent || null,
  calibration: document.querySelectorAll('.bl-panel-body .bl-name-calibration').length,
})
"""


def test_task_13_the_checklist_lists_what_the_model_lacks_and_details_of_a_refused_text(
    browser, server_on, scratch_folder
):
    """Task 13 (the usability walkthrough §4 items 9, 11, 15 and 16 and §5;
    K-D10, K-D16; design pass 2 §6), with Task 26 (K-D28, K-D29). On a copy
    of the portfolio model with the cons methods emptied to a slot and the
    period's connector removed, the checklist under the tree stands folded
    under its head, `1 field unjoined`, in the tree's face and size and
    without orange, as its item, which is no refusal (spec 0.4 §5.7);
    unfolded by a click on the head, it holds one item with its file and
    line, the arrival field m of cons, which no join reaches, at the period
    file's connectors, line 14; the slot is no item. With cons.bl then open,
    the cursor on ρ at
    line 6, Details prints the line of the calibration file that values ρ;
    after an edit the construction refuses, Details holds the refusal's row
    for cons.bl, its legend names cons, and it prints no line of another
    file."""
    recipe_file = scratch_folder / RECIPE_FILE
    text = recipe_file.read_text(encoding="utf-8")
    assert text.count("methods: {all: [stages/cons/methods]}") == 1
    recipe_file.write_text(
        text.replace("methods: {all: [stages/cons/methods]}", "methods: {all: [$cons_methods]}"),
        encoding="utf-8",
    )
    period_file = scratch_folder / "declaration/period.yml"
    text = period_file.read_text(encoding="utf-8")
    assert text.count("- {m_next: m}") == 1
    period_file.write_text(text.replace("- {m_next: m}", "- {}"), encoding="utf-8")
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_folder), RECIPE_FILE)

        def checklist_of_the_reading():
            # the checklist once its head counts the trellis's reading
            drawn = tab.evaluate(CHECKLIST_JS)
            return drawn if drawn and drawn["head"] == EMPTIED_HEAD else None

        found, _ = wait_until(checklist_of_the_reading, 60.0, "the checklist's head")
        assert (found["expanded"], found["shown"]) == ("false", False)
        assert found["faces"][0][0] == found["faces"][1][0]
        assert found["colors"][0] == property_color(tab, "--bl-alarm")
        assert found["colors"][1] != found["colors"][0]
        assert found["items"] == EMPTIED_ITEMS
        open_checklist(tab)
        unfolded = tab.evaluate(CHECKLIST_JS)
        assert (unfolded["expanded"], unfolded["shown"]) == ("true", True)
        assert unfolded["head"] == EMPTIED_HEAD
        assert unfolded["items"] == EMPTIED_ITEMS
        open_tree_file(tab, CONS)
        wait_until(lambda: status_settled_on(tab, CONS), 60.0, f"the loop of {CONS}")
        click_line(tab, 6)
        tab.keyboard.press("Home")
        wait_until(
            lambda: tab.evaluate(DETAILS_FILES_JS)["calibration"] == 1, 15.0, "the calibration"
        )
        assert tab.evaluate(DETAILS_FILES_JS)["files"] == ["declaration/calibration/portfolio.yml"]
        replace_in_editor(tab, "m_d = m", "m_d = q")
        click_line(tab, 6)
        tab.keyboard.press("Home")

        def details_of_the_refusal():
            # Details once it holds the refusal's row
            drawn = tab.evaluate(DETAILS_FILES_JS)
            return drawn if drawn["refusal"] else None

        details, _ = wait_until(details_of_the_refusal, 30.0, "the refusal's row in Details")
        assert CONS in details["refusal"]
        assert details["legend"].split()[0] == "cons"
        assert details["files"] == [] and details["calibration"] == 0
    finally:
        context.close()


# The line of the portfolio model's period file that lists disc, which the
# recipe still names once the line is removed; and the package's refusal
# of the trellis that follows, as the list under the error mark prints it,
# each path from the folder (K-D11), the package writing the trellis file's
# absolute path twice (usability walkthrough §4 item 6).
DISC_LISTED = "  - disc\n"
NO_PERIOD_HOLDS_DISC = (
    "the recipe names the stage 'disc', which no period of declaration/trellis.yml holds\n"
    "'disc' in a period template of declaration/trellis.yml, or no entry for it in the recipe"
)
# the line of cons.bl whose first name after the indentation is m_d
M_D_LINE = 14
# the retirement model's branching stage, the pullback of its branch `work`
# and the kernel Details prints for it, the package's kernel of that
# branch's section, which names no output of a section of one output
# (usability walkthrough §4 item 14; decision K-I203)
RET_CHOICE = "declaration/stages/ret_choice/ret_choice.bl"
WORK_PULLBACK = "cntn_to_dcsn:Pullback:work"
WORK_KERNEL = "𝑔 of dcsn_to_cntn: 𝑔_work≻(a_d) = a_d"
# the label of the name under the cursor as the browser renders it, and
# whether it stands before the fold `cursor`, None where either is absent
NAME_ORDER_JS = """
() => {
  const name = document.querySelector('.bl-panel-body .bl-name');
  const fold = document.querySelector('.bl-panel-body details.bl-cursor-details');
  return {
    name: name ? name.innerText : null,
    before: name && fold
      ? Boolean(name.compareDocumentPosition(fold) & Node.DOCUMENT_POSITION_FOLLOWING) : null,
  };
}
"""
# each element of Details that prints the package's dependence record, the
# block's record and the builder's signature: whether it stands in the fold
# `cursor`, and whether that fold is open
DEPENDENCE_RECORDS_JS = """
() => Array.from(
  document.querySelectorAll(
    '.bl-panel-body .bl-block-record, .bl-panel-body .bl-builder-signature'),
  (element) => {
    const fold = element.closest('details.bl-cursor-details');
    return [fold !== null, fold !== null && fold.open];
  })
"""


def test_task_14_paths_from_the_folder_the_name_as_written_and_the_kernel_of_one_branch(
    browser, server_on, scratch_folder, retirement_folder
):
    """Task 14 (the usability walkthrough §4 items 6, 14 and 19 and §5,
    "Find where a field is used" and "Check a kernel"; K-D11). On a copy of
    the portfolio model whose period file no longer lists disc, the package
    refuses the trellis in a sentence that writes the trellis file's
    absolute path twice: with cons.bl open, the list under the error mark
    holds that sentence once, the trellis's refusal and the note of cons.bl
    giving it alike (unit L, Task 21; defect 17 of the UX simulation), each
    path printed from the folder and every other character the package's,
    and no sentence under the error mark holds the folder's absolute
    path. With the cursor on m_d at line 14, Details prints `name
    m_d`, the name as written, above the fold `cursor`. On the retirement
    model's ret_choice.bl, the pullback of the branch `work` selected,
    `kernel` prints that branch's kernel, `𝑔_work≻(a_d) = a_d`, and no
    `unused d`, and the package's dependence record, the block's record
    and the builder's signature, stands in the fold `cursor`, closed."""
    period_file = scratch_folder / "declaration/period.yml"
    text = period_file.read_text(encoding="utf-8")
    assert text.count(DISC_LISTED) == 1
    period_file.write_text(text.replace(DISC_LISTED, ""), encoding="utf-8")
    roots = {str(scratch_folder), str(scratch_folder.resolve())}
    ret_text = (retirement_folder / RET_CHOICE).read_text(encoding="utf-8")
    stage = bound_as_the_recipe_binds(retirement_folder, ret_text, RET_CHOICE)
    piece = model.piece(stage, "backward", WORK_PULLBACK)
    assert piece.kernel == WORK_KERNEL
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(scratch_folder), CONS)
        wait_until(
            lambda: [line[0] for line in error_lines(tab)].count(NO_PERIOD_HOLDS_DISC) == 1,
            60.0,
            "the trellis's refusal with its paths from the folder",
        )
        listed = tab.locator(".bl-error-list").text_content()
        print(f"task 14: the list under the error mark: {error_lines(tab)}")
        assert not [root for root in roots if root in listed]
        click_line(tab, M_D_LINE)
        tab.keyboard.press("Home")
        found, _ = wait_until(
            lambda: (lambda drawn: drawn if drawn["name"] == "name m_d" else None)(
                tab.evaluate(NAME_ORDER_JS)
            ),
            15.0,
            "the name m_d under the cursor",
        )
        assert found["before"] is True
    finally:
        context.close()
    context, tab = new_tab(browser)
    try:
        open_file(tab, server_on(retirement_folder), RET_CHOICE)
        select_until(
            tab,
            WORK_PULLBACK,
            "backward",
            lambda: tab.locator(".bl-kernel").count() == 1
            and tab.locator(CURSOR).count() == 1
            and tab.locator(".bl-kernel").text_content() == piece.kernel,
            f"the kernel of {WORK_PULLBACK}",
        )
        assert "unused d" not in tab.locator(".bl-panel").text_content()
        records = tab.evaluate(DEPENDENCE_RECORDS_JS)
        assert records and all(record == [True, False] for record in records), records
    finally:
        context.close()


# The words and the hover of each `+ period` control and of each period's
# `+ stage` control the region draws, each `+ stage` with the id of its
# period's layer; and the face, the family and the size the browser
# computes, of each `+ period` control and of each period's name (unit K's
# decision K-D14; design pass 10 §5), and apart of each `+ stage`, whose
# words keep 11 px on the screen (unit L's decision L-D5).
CONTROL_WORDS_JS = """
() => {
  const all = (selector) => Array.from(document.querySelectorAll(`.bl-view-host ${selector}`));
  const face = (element) => {
    const style = getComputedStyle(element);
    return [style.fontFamily, style.fontSize];
  };
  return {
    period: all('.bf-add-period').map((control) => [control.textContent, control.title]),
    stage: all('.bf-add-stage').map((control) => [
      control.closest('.react-flow__node').dataset.id, control.textContent, control.title]),
    faces: all('.bf-add-period, .bf-layer.bf-period > .bf-layer-name').map(face),
    stageFaces: all('.bf-add-stage').map(face),
  };
}
"""
# The stage list the region draws over the graph, null where none is open:
# the period its head names as its context (unit L, Task 23; design pass 4
# §4), null where it names none, and each item's id, whether it is dimmed
# as listed and the word it prints for that, null where it prints none.
STAGE_LIST_JS = """
() => {
  const list = document.querySelector('.bl-view-host .bf-stage-list');
  if (!list) return null;
  const period = list.querySelector('.bf-list-head .bf-stage-period');
  return {
    period: period && period.textContent,
    items: Array.from(list.querySelectorAll('.bf-stage-item'), (item) => [
      item.dataset.item, item.classList.contains('bf-listed'),
      (item.querySelector('.bf-stage-listed') || {}).textContent || null]),
  };
}
"""
# the hover of a `+ period` control (spec 0.4 §3.6) and of a period's
# `+ stage` control (design pass 2, §2)
ADD_PERIOD_HOVER = "add a period"
ADD_STAGE_HOVER = "add a stage to this period"
# the cons-port model's trellis file in which consumption comes first
CONS_PORT = "declaration/trellis.cons-port.yml"
# the four gestures of the page, each with the status line it prints, by
# which `port` comes before `cons` in every period of that file (design pass
# 2, §2, "Reordering"): the connector {a: k}, which joins `disc` to `port`
# within a period, removed; the inter-period entry m_next: m, which joins
# `port` to the next period's `cons`, removed; a drag from `port`'s m_next
# to `cons`'s m within periods[2]; and a drag from `disc`'s a in periods[3]
# to `port`'s k in periods[2]
WITHIN_REMOVED = "trellis.cons-port.yml, periods[0].connectors[0]: {a: k} removed, periods 0–5"
BETWEEN_REMOVED = "trellis.cons-port.yml, inter_connectors[0]: m_next: m removed, periods 0–5"
WITHIN_WRITTEN = (
    "trellis.cons-port.yml, periods[0].connectors[0]: {m_next: m} written, flat, periods 0–5"
)
BETWEEN_WRITTEN = "trellis.cons-port.yml, inter_connectors[0]: a: k written, entry, periods 0–5"
# the ports of the two drags, each unjoined once the removals are made
M_NEXT = "periods[2]/port/unjoined:port:cntn:m_next"
CONS_M = "periods[2]/cons/unjoined:cons:arvl:m"
DISC_A = "periods[3]/disc/unjoined:disc:cntn:a"
PORT_K = "periods[2]/port/unjoined:port:arvl:k"
# the joins of a period of that file after the four gestures, as the
# package's `period_joins` answers them: `port` to `cons` by the connector,
# `cons` to `disc` by the equal name a
PORT_BEFORE_CONS = [
    {"from": ("cons", "a"), "to": ("disc", "a")},
    {"from": ("port", "m_next"), "to": ("cons", "m")},
]
# the record of `port`, the first key of the stages of that file's one
# entry, written over two lines, and the status line of its removal
PORT_RECORD = (
    "      port: {stage: ../../portfolio-choice/declaration/stages/port/port.bl, "
    "calibration: calibration/portfolio.yml,\n"
    "             settings: settings/port_wide.yml, methods: methods/port.yml}\n"
)
# and, since unit L's Task 14, the connector and the inter-period entry of
# its two joins, whose fields no other stage of the period declares
PORT_REMOVED = (
    "trellis.cons-port.yml, periods[0].stages: port removed, periods 0–5; "
    "trellis.cons-port.yml, periods[0].connectors[0]: {m_next: m} removed, periods 0–5; "
    "trellis.cons-port.yml, inter_connectors[0]: a: k removed, periods 0–5"
)


def period_node(h: int) -> str:
    """The selector of the node of the layer of period `h` in the region."""
    return f'.bl-view-host .react-flow__node[data-id="periods[{h}]{LAYER_ID_ENDING}"]'


def test_task_15_the_trellis_s_controls_show_and_a_stage_occurrence_is_removed(
    browser, server_on, tmp_path
):
    """Task 15 (design pass 2 §2 and §10; K-D12, K-D13, K-D14). On a copy of
    cons-port whose lesson 05 trellis file writes periods[2] without `disc`
    (`records_without`), its forward graph shown: each `+ period` control
    prints `+ period` with the hover `add a period` and each period's open
    layer `+ stage` with the hover `add a stage to this period`, `+ period`
    in the face of a period's name (design pass 10 §5, unit N's Task 3, by
    which a stage card's name has a face of its own), `+ stage` in the
    face of a layer's name at 11 px (unit L's decision L-D5), each control
    24 px high. `+ stage` of
    periods[2] opens the stage list headed `periods[2]`, `cons` and `port`
    dimmed as listed, whose click sends nothing; a click on `disc` sends the
    event `dropped` that a drop on the period's layer sends, and the status
    line then prints the note the package's drop answers. On the copy's
    `trellis.cons-port.yml`, where `cons` comes before `port`, adjacent
    period layers stand at most 200 px apart on the page, each `+ period`
    control in the gap between them (K-I78 corrected). The page's events
    alone, the connector {a: k} and the inter-period entry m_next: m
    removed, a drag from `port`'s m_next to `cons`'s m and one from
    `disc`'s a to the next period's `port`'s k, each printing its note,
    give a text whose trellis the package reads with `port` joined to
    `cons` in every period, `period_joins` ordering `port` before `cons`.
    Backspace on the closed frame of `port` in periods[2], selected, takes
    `port`'s record out of the entry's stages and, since unit L's Task 14
    (K-D14 amended), the connector {m_next: m} and the inter-period entry
    a: k of its two joins with it, the status line naming the entry, the
    two joins and the six periods, and the package reads the trellis with
    no refusal of the trellis file."""
    copy = records_without(tmp_path / "records", 2, "disc")
    folder = model.open_folder(copy)
    lesson = trellis.show_trellis(folder, recipe.Source("trellis", PORT_CONS_RECORDS)).shown
    target = f"periods[2]{LAYER_ID_ENDING}"
    drop = trellis.drop_edits(lesson, dropped_event(lesson, folder, "disc", "stage", target), {})
    assert drop.edits is not None and drop.note
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PORT_CONS_RECORDS)
        choose_view(tab, None, "forward")
        wait_until(lambda: add_period_controls(tab) == control_targets(6), 30.0, "the controls")
        words = tab.evaluate(CONTROL_WORDS_JS)
        assert words["period"] == [["+ period", ADD_PERIOD_HOVER]] * 6
        layers = [f"periods[{h}]{LAYER_ID_ENDING}" for h in range(6)]
        assert sorted(words["stage"]) == [[layer, "+ stage", ADD_STAGE_HOVER] for layer in layers]
        assert len({tuple(face) for face in words["faces"]}) == 1, words["faces"]
        family = words["faces"][0][0]
        assert {tuple(face) for face in words["stageFaces"]} == {(family, "11px")}, words
        nodes = tab.evaluate(DRAWN_PLACES_JS)["nodes"]
        sizes = {(n["width"], n["height"]) for i, n in nodes.items() if i.startswith("add-period")}
        assert len(sizes) == 1 and sizes.pop()[1] == 24

        # `+ stage` of periods[2] opens the list for that period
        tab.click(".bl-zoom-button[data-zoom='fit']")
        hold_events(tab, "dropped")
        tab.click(f"{period_node(2)} > .bf-layer > .bf-add-stage")
        listed, _ = wait_until(
            lambda: tab.evaluate(STAGE_LIST_JS), 10.0, "the stage list of periods[2]"
        )
        assert listed["period"] == "periods[2]"
        assert sorted(listed["items"]) == [
            ["cons", True, "listed"],
            ["disc", False, None],
            ["port", True, "listed"],
        ]
        # the browser's checks take the item for disabled; the click is forced
        tab.click('.bl-view-host .bf-stage-item[data-item="port"]', force=True)
        tab.wait_for_timeout(300)
        assert held_events(tab, "dropped") == [] and tab.evaluate(STAGE_LIST_JS) is not None
        tab.click('.bl-view-host .bf-stage-item[data-item="disc"]')
        wait_until(lambda: held_events(tab, "dropped"), 10.0, "the event dropped")
        reading = tab.evaluate(REGION_READING_JS)
        assert held_events(tab, "dropped") == [
            {"item": "disc", "kind": "stage", "target": target, "reading": reading}
        ]
        assert tab.evaluate(STAGE_LIST_JS) is None
        release_events(tab, "dropped")
        wait_until(lambda: gesture_note(tab) == drop.note, 10.0, "the drop's note")
    finally:
        context.close()

    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), CONS_PORT)
        before = tab.evaluate(DOCUMENT_JS)
        choose_view(tab, None, "forward")
        wait_until(lambda: add_period_controls(tab) == control_targets(6), 30.0, "the controls")
        nodes = tab.evaluate(DRAWN_PLACES_JS)["nodes"]
        period = [nodes[f"periods[{h}]{LAYER_ID_ENDING}"] for h in range(6)]
        gaps = [period[h]["x"] - period[h + 1]["x"] - period[h + 1]["width"] for h in range(5)]
        print(f"task 15: on the page cons-port's periods stand {gaps} px apart")
        assert all(0 < gap <= GAP_MOST for gap in gaps), gaps
        for h in range(5, 0, -1):
            control = nodes[f"add-period::between periods[{h}] and periods[{h - 1}]"]
            earlier, later = period[h], period[h - 1]
            assert earlier["x"] + earlier["width"] < control["x"], (control, earlier)
            assert control["x"] + control["width"] < later["x"], (control, later)

        # the order changed by the page's events alone
        for writing, reading, note, freed in (
            ("periods[2]/disc", "periods[2]/port", WITHIN_REMOVED, PORT_K),
            ("periods[3]/port", "periods[2]/cons", BETWEEN_REMOVED, M_NEXT),
        ):
            click_join(tab, writing, reading)
            wait_until(
                lambda writing=writing: [w["from"] for w in join_wires_drawn(tab) if w["selected"]]
                == [writing],
                10.0,
                f"the join from {writing} selected",
            )
            tab.keyboard.press("Backspace")
            wait_until(lambda note=note: gesture_note(tab) == note, 10.0, note)
            wait_until(
                lambda freed=freed: freed in unjoined_port_ids(tab), 60.0, f"{freed} unjoined"
            )
        for writing, reading, note in (
            (M_NEXT, CONS_M, WITHIN_WRITTEN),
            (DISC_A, PORT_K, BETWEEN_WRITTEN),
        ):
            assert {writing, reading} <= set(unjoined_port_ids(tab))
            drag_ports(tab, writing, reading)
            wait_until(lambda note=note: gesture_note(tab) == note, 10.0, note)
            # the ports a drag can take are drawn again once the text is read
            wait_until(
                lambda reading=reading: (ids := unjoined_port_ids(tab)) and reading not in ids,
                60.0,
                f"{reading} joined",
            )
        reordered = tab.evaluate(DOCUMENT_JS)
        outcome = trellis.show_trellis(
            folder,
            recipe.Source("trellis", CONS_PORT),
            unsaved=unsaved_of(copy, {CONS_PORT: reordered}),
        )
        assert outcome.refusal is None
        for h, each in enumerate(outcome.shown.trellis["periods"]):
            assert period_joins(each, f"periods[{h}]")["joins"] == PORT_BEFORE_CONS, h
        assert reordered.count(PORT_RECORD) == 1 and reordered != before

        # Backspace on the closed frame of `port` in periods[2], selected
        occurrence = f"periods[2]/port{LAYER_ID_ENDING}"
        click_toggle(tab, occurrence)
        frame = f'.bl-view-host .react-flow__node[data-id="{occurrence}"] > .bf-box'
        wait_until(lambda: tab.locator(frame).count() == 1, 10.0, "port's frame closed")
        tab.click(f"{frame} .bf-symbol")
        wait_until(
            lambda: flow_handle(tab, "selection") == occurrence, 10.0, "port's frame selected"
        )
        tab.keyboard.press("Backspace")
        wait_until(lambda: gesture_note(tab) == PORT_REMOVED, 10.0, "the removal's note")
        without = (
            reordered.replace(PORT_RECORD, "")
            .replace("      - {m_next: m}\n", "      - {}\n")
            .replace("  - {disc.a: k}\n", "  - {}\n")
        )
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == without,
            10.0,
            "port's record and its two joins taken out",
        )
        occurrence_node = f'.bl-view-host .react-flow__node[data-id="{occurrence}"]'
        wait_until(
            lambda: tab.locator(occurrence_node).count() == 0
            and (status := trellis_settled(tab, CONS_PORT))
            and "refused" not in status.split(" · "),
            60.0,
            "the trellis read without port",
        )
        assert not any(file == CONS_PORT for _, file, _ in error_lines(tab))
    finally:
        context.close()


# The card of the closed stage occurrence whose layer's id is the argument,
# null where it is not drawn closed: its box on the screen; its name and the
# text of each row it prints for its reading fields (.bf-in) and its
# writing fields (.bf-out), each with its text, the family and the size of
# its face as the browser computes them, and its box on the screen; and
# each port, the cables' since unit N's Task 7 (design pass 10 §6), in the
# order the card holds them, whether it writes, its hover, its `data-port`
# and its center on the screen (unit K's decision K-D15; AAS, L-D16 and
# L-D25).
FRAME_TEXTS_JS = """
(id) => {
  const box = document.querySelector(
    `.bl-view-host .react-flow__node[data-id="${CSS.escape(id)}"] > .bf-box`);
  if (!box) return null;
  const read = (element) => {
    const at = element.getBoundingClientRect(), style = getComputedStyle(element);
    return {text: element.textContent, family: style.fontFamily, size: style.fontSize,
            left: at.left, right: at.right, top: at.top, bottom: at.bottom, height: at.height};
  };
  return {
    frame: read(box),
    name: read(box.querySelector(':scope > .bf-name')),
    reading: Array.from(box.querySelectorAll(':scope > .bf-in'), read),
    writing: Array.from(box.querySelectorAll(':scope > .bf-out'), read),
    ports: Array.from(box.querySelectorAll(':scope > .react-flow__handle'), (port) => {
      const at = port.getBoundingClientRect();
      return {writes: port.classList.contains('source'), title: port.getAttribute('title'),
              port: port.dataset.port || null, y: (at.top + at.bottom) / 2};
    }),
  };
}
"""
# the id of a field port the exporter adds to a stage occurrence of the
# forward trellis graph (spec 0.4 §3.4; J-D16)
FIELD_PORT = re.compile(r"/(?:un)?joined:[^/]+$")
# the occurrence of the durables model whose frame the design pass draws
# beside `adjuster_cons` (design pass 2, §2), in the terminal period, and
# the names a card prints for its arrival and its continuation fields
KEEPER_CONS = "periods[0]/keeper_cons"
KEEPER_CONS_FIELDS = ({"h_kp", "w_kp", "z_kp"}, {"a_nxt_kp", "h_nxt_kp", "z_nxt_kp"})
# the least height on the screen of a text of a card's rows (unit K's plan,
# Task 16; row K-I101), read on the selected card, which prints every name
# (AAS, L-D25), at the scale LEGIBLE_SCALE
FRAME_TEXT_LEAST = 9
LEGIBLE_SCALE = 0.9
# the family and the size of the port face, in which a card prints its rows
# (design pass 5 §2)
PORT_FACE = ('"IBM Plex Mono", "STIX Two Math", monospace', "9.5px")


def printed_name(label: str, field: bool) -> str:
    """The text a card prints for a port whose label the graph JSON writes
    `label` (AAS, L-D25; design pass 7 §3): for a field, its branch word
    with a colon, the text before `: `, and its name with no perch's sign,
    `keep: w_kp≻` printing `keep: w_kp`; for every other port, the label as
    it stands."""
    if not field:
        return label
    branch, _, name = label.partition(": ") if ": " in label else ("", "", label)
    name = name.rstrip("≺≻")
    return f"{branch}: {name}" if branch else name


def frame_names(graph: dict, occurrence: str) -> tuple[list, list]:
    """The texts the card of the stage occurrence `occurrence` of the trellis
    graph `graph` prints while it is selected, reading and writing, each
    list sorted: every field port of its own `Inputs` and `Outputs`
    (K-D15), printed as `printed_name` prints it; a wire that crosses its
    border prints no row, its label standing in its port's hover (design
    pass 13 §2, rule 7; design pass 7 §3)."""
    reading: list[str] = []
    writing: list[str] = []
    for node in graph["nodes"]:
        if node.get("namespace") == occurrence:
            for ports, side in (
                (node.get("inputsMetadata"), reading),
                (node.get("outputsMetadata"), writing),
            ):
                side += [
                    printed_name(attribute_of(p, "label"), True)
                    for p in ports or []
                    if FIELD_PORT.search(p["id"])
                ]
    return sorted(reading), sorted(writing)


def centered_on(
    tab, box: str, zoom: float, texts_js: str | None = None, selected: bool = False
) -> dict:
    """Sets the region's view, as the graph's handle sets one (R-D29), to
    the scale `zoom` with the box `box` at the region's center and the box
    selected where `selected` holds, else nothing; answers the card of
    `box` (FRAME_TEXTS_JS, or `texts_js`) read once the view stands, the
    layout that the selection runs again has drawn, every name printed
    while the card is selected and none of a joined field otherwise, at
    every scale (AAS, L-D25), and two frames are drawn."""
    texts_js = texts_js or FRAME_TEXTS_JS
    place = tab.evaluate(DRAWN_PLACES_JS)["nodes"][box]
    view = viewport(tab)
    middle = (place["x"] + place["width"] / 2, place["y"] + place["height"] / 2)
    flow_handle(
        tab,
        "setView",
        {
            "viewport": {
                "x": view["width"] / 2 - middle[0] * zoom,
                "y": view["height"] / 2 - middle[1] * zoom,
                "zoom": zoom,
            },
            "selection": box if selected else None,
        },
    )
    wait_until(lambda: abs(viewport(tab)["zoom"] - zoom) <= 1e-6, 5.0, f"the view at {zoom}")

    def drawn():
        frame = tab.evaluate(texts_js, box)
        printed = frame and (frame["reading"] or frame["writing"])
        return frame if frame and bool(printed) == selected else None

    wait_until(drawn, 10.0, f"{box} drawn at {zoom}")
    tab.evaluate(TWO_FRAMES_JS)
    frame, _ = wait_until(drawn, 10.0, f"{box} drawn at {zoom}")
    return frame


def centered_on_band(tab, box: str, zoom: float, G: dict) -> dict:
    """Sets the region's view as `centered_on` does, the box `box` selected,
    and answers its card (FRAME_TEXTS_JS) read once it stands at the scale
    `zoom` as its band alone: no row printed and the card G.cardStripY,
    G.cardBandH and G.framePad high, the selected card of an occurrence
    that has no field port of its own (design pass 13 §2, rule 7)."""
    high = G["cardStripY"] + G["cardBandH"] + G["framePad"]
    place = tab.evaluate(DRAWN_PLACES_JS)["nodes"][box]
    view = viewport(tab)
    middle = (place["x"] + place["width"] / 2, place["y"] + place["height"] / 2)
    flow_handle(
        tab,
        "setView",
        {
            "viewport": {
                "x": view["width"] / 2 - middle[0] * zoom,
                "y": view["height"] / 2 - middle[1] * zoom,
                "zoom": zoom,
            },
            "selection": box,
        },
    )
    wait_until(lambda: abs(viewport(tab)["zoom"] - zoom) <= 1e-6, 5.0, f"the view at {zoom}")

    def drawn():
        frame = tab.evaluate(FRAME_TEXTS_JS, box)
        if not frame or frame["reading"] or frame["writing"]:
            return None
        edge = frame["frame"]
        return frame if abs((edge["bottom"] - edge["top"]) / zoom - high) <= 0.5 else None

    wait_until(drawn, 10.0, f"{box} drawn as its band at {zoom}")
    tab.evaluate(TWO_FRAMES_JS)
    frame, _ = wait_until(drawn, 10.0, f"{box} drawn as its band at {zoom}")
    return frame


def in_rows_under_its_name(frame: dict, zoom: float, G: dict) -> None:
    """Asserts that the texts of the card `frame` (FRAME_TEXTS_JS), drawn at
    the scale `zoom` while it is selected and prints every name, stand in
    rows of G.frameRow under its name within the card, in the port face,
    the reading texts at one left edge and the writing texts at one right
    edge, no two overlapping; and that the card's ports are the cables'
    (design pass 10 §6; unit N, Task 7), which stand on the card's axis,
    G.cardAxis from its top, since the per-field ports left the cards: a
    side that prints a text has a port, one for the arrival tuple or one
    per continuation branch. The rows start under the band of the card's
    builders, which a selected card draws from G.cardStripY, G.cardBandH
    high, and the card is as high as that and a row for each text of its
    fuller side with G.framePad, G being the layout's geometry (design pass
    13 §2, rule 7; AAS, L-D16 and L-D25)."""
    box, name = frame["frame"], frame["name"]
    rows_top = G["cardStripY"] + G["cardBandH"]
    axis = box["top"] + G["cardAxis"] * zoom
    for writes, labels in ((False, frame["reading"]), (True, frame["writing"])):
        for label in labels:
            assert (label["family"], label["size"]) == PORT_FACE, label
            assert box["left"] <= label["left"] and label["right"] <= box["right"], label
            assert name["bottom"] - 0.5 <= label["top"] and label["bottom"] <= box["bottom"]
        edges = [label["right" if writes else "left"] for label in labels]
        assert not edges or max(edges) - min(edges) <= 0.5, (writes, edges)
        tops = sorted(label["top"] for label in labels)
        assert all(
            abs((below - above) / zoom - G["frameRow"]) <= 0.5
            for above, below in zip(tops, tops[1:])
        ), (writes, tops)
        side = [port for port in frame["ports"] if port["writes"] is writes]
        assert not labels or side, (writes, labels)
        # the ports of a side stand on the axis, or about it where the side has several
        if side:
            assert abs(sum(port["y"] for port in side) / len(side) - axis) <= 0.5, (side, axis)
        for label in labels:
            assert label["top"] >= box["top"] + rows_top * zoom - 0.5, (label, rows_top)
    for left in frame["reading"]:
        for right in frame["writing"]:
            if left["top"] < right["bottom"] and right["top"] < left["bottom"]:
                assert left["right"] < right["left"], (left, right)
    rows = max(len(frame["reading"]), len(frame["writing"]))
    high = rows_top + rows * G["frameRow"] + G["framePad"]
    assert abs((box["bottom"] - box["top"]) / zoom - high) <= 0.5, (box, zoom, high)


def test_task_16_a_closed_occurrence_s_card_prints_its_fields_names_in_rows_under_its_name(
    browser, server_on, durables_folder
):
    """Task 16 (design pass 2 §2, the frame, and §10; K-D15, J-D47
    extended to the reading ports, K-D9 unchanged), its frame the card of
    unit L's Tasks 24 and 30 (AAS, L-D16 and L-D25; design pass 7 §3), its
    ports the cables' since unit N's Task 7 (design pass 10 §6). On the
    durables model's forward trellis graph, periods 0 to 2, the card of
    `keeper_cons` in periods[0], closed by its chevron and the open layer's
    toggle (design pass 13 §2, rule 4) and centered at the scales 1 and
    0.6, prints no name, no field of the durables model being unjoined,
    and is G.cardH high, 32 px, its name and its strip. Selected and
    centered at the scale 1, it prints each name in a row of its own under
    the band of its builders: every field of its `Inputs` and `Outputs`,
    with no perch's sign, each text in the port face, the rows G.frameRow
    apart, the reading names at one left edge and the writing names at one
    right edge, the card as high as its band's foot and its fuller side's
    rows; its ports, one for the arrival tuple and one per continuation
    branch, stand on the card's axis. Selected at 0.9, each text is at least 9 px high on the
    screen. The backward trellis graph's card of the same occurrence, which
    has no field port of its own, prints no row while it is selected, its
    band alone, each cable of its routes' values standing whole and naming
    the functions it carries in its port's hover (design pass 13 §2, rule
    7; design pass 12 §2)."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        record_layouts(tab)
        G = tab.evaluate("() => window.BellmanFlowLayout.G")
        held = tab.evaluate(HELD_COLLECTION_JS)
        box = KEEPER_CONS + LAYER_ID_ENDING
        seen = []
        for direction in ("forward", "backward"):
            choose_view(tab, None, direction)
            wait_until(
                lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, f"the {direction} graph"
            )
            opened_on_the_terminal_period(tab, f"the {direction} graph on periods[0]")
            close_to_card(tab, box)
            opened = set(flow_handle(tab, "openLayers"))
            assert KEEPER_CONS not in opened and "periods[0]" in opened
            reading, writing = frame_names(graph_named(held, direction), KEEPER_CONS)
            # not selected, at the scales 1 and 0.6, no field unjoined: no name
            for zoom in (1.0, READING_SCALE):
                folded = centered_on(tab, box, zoom)
                assert folded["reading"] == folded["writing"] == [], zoom
                high = G["cardH"]
                edge = folded["frame"]
                assert abs((edge["bottom"] - edge["top"]) / zoom - high) <= 0.5, (edge, high)
            # selected: the forward card prints its fields' names in rows under its band; the backward card,
            # which has no field port of its own, is its band alone (design pass 13 §2, rule 7)
            printed = bool(reading or writing)
            frame = centered_on(tab, box, 1.0, selected=True) if printed else centered_on_band(tab, box, 1.0, G)
            print(f"task 16: {direction}, {KEEPER_CONS} reads {reading} and writes {writing}")
            if direction == "forward":
                assert KEEPER_CONS_FIELDS[0] <= set(reading)
                assert KEEPER_CONS_FIELDS[1] <= set(writing)
            assert sorted(label["text"] for label in frame["reading"]) == reading
            assert sorted(label["text"] for label in frame["writing"]) == writing
            in_rows_under_its_name(frame, 1.0, G)
            names = (
                centered_on(tab, box, LEGIBLE_SCALE, selected=True)
                if printed
                else centered_on_band(tab, box, LEGIBLE_SCALE, G)
            )
            in_rows_under_its_name(names, LEGIBLE_SCALE, G)
            texts = names["reading"] + names["writing"]
            if texts:
                least = min(label["height"] for label in texts)
                assert least >= FRAME_TEXT_LEAST, least
                seen.append((direction, least))
            else:
                # the backward card, no field port of its own: its band alone, the functions its cables carry
                # named in its reading ports' hovers (design pass 13 §2, rule 7; design pass 12 §2)
                assert direction == "backward" and reading == writing == [], (direction, reading, writing)
                hovers = [port["title"] or "" for port in frame["ports"] if not port["writes"]]
                assert hovers and all("𝑉" in hover for hover in hovers), hovers
        for direction, at_names in seen:
            print(f"task 16: {direction}, the texts {at_names:.2f} px high at {LEGIBLE_SCALE}")
    finally:
        context.close()


# the durables model's ranges and stage keys as the restriction's menu lists
# them, and the occurrences of periods 0 to 5, the terminal period's four
# and three in each other period (unit K, Task 17)
DURABLES_RANGES = ["0–2", "0–5", "0–10", "0–20", "all 51"]
DURABLES_KEYS = ["tenure", "keeper_cons", "adjuster_cons", "bequest"]
SIX_PERIODS_OCCURRENCES = 19
# the bar's items whose words the restriction's text matches in face, size
# and weight, Label (design pass 8 §5.1; unit M, Task 7): the direction
# select, VSCode Elements' select, which sets its word in the face it
# computes, `Trellis` and `Stages`
BAR_WORDS = (
    ".bl-view-direction vscode-single-select",
    ".bl-trellis-button",
    ".bl-stages-button",
)


def test_task_17_the_restriction_is_chosen_from_a_list_in_the_bar_s_face(
    browser, server_on, durables_folder
):
    """Task 17 (design pass 2 §3 and §10; K-D17, K-D18). On opening the
    durables model the select of the view's bar reads `periods 0–2`, with no
    label of its own, its text in the family, the size and the weight of
    the word the direction select shows, of `trellis` and of `stages`. Its
    menu lists the ranges `0–2`, `0–5`, `0–10`, `0–20` and `all 51`, `0–2`
    chosen, then the four stage keys ticked, and at its foot the field
    holding `periods 0–2`. Choosing `0–5` draws six periods, the select and
    the status line's restriction reading `periods 0–5`; choosing `all`
    draws fifty-one, the select reading `all` and the status line naming no
    restriction. A text of the grammar typed at the foot, `periods 1–3,
    stages tenure`, is applied as written; `tenure`, the one key then
    ticked, cannot be unticked, and ticking `keeper_cons` keeps the menu
    open and adds the key to the text."""

    def settled_with(words: str) -> str | None:
        line = trellis_settled(tab, RECIPE_FILE)
        return line if line is not None and words in line else None

    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        choose_view(tab, None, "forward")
        tab.wait_for_selector(".bl-stages-button", timeout=30_000)
        assert restriction_shown(tab) == "periods 0–2"
        assert tab.locator(".bl-graph-bar label").count() == 0
        faces = tab.evaluate(TYPE_FACES_JS, [RESTRICTION_TEXT, *BAR_WORDS])
        print(f"task 17: the faces of the restriction's text and the bar's words: {faces}")
        assert {tuple(face[:3]) for face in faces} == {tuple(faces[0][:3])}

        open_restriction(tab)
        ranges = [("radio", label, label == "0–2", False) for label in DURABLES_RANGES]
        checks = [("checkbox", key, True, False) for key in DURABLES_KEYS]
        assert restriction_menu_shown(tab) == (ranges + checks, "periods 0–2")

        choose_restriction(tab, "0–5")
        wait_until(lambda: restriction_menu_shown(tab) is None, 5.0, "the menu closed")
        line, _ = wait_until(
            lambda: settled_with(f" · shown periods 0–5 of 51 ({SIX_PERIODS_OCCURRENCES} "),
            60.0,
            "the status line's restriction periods 0–5",
        )
        print(f"task 17: {line!r}")
        assert restriction_shown(tab) == "periods 0–5"
        six = {f"periods[{h}]" for h in range(6)}
        wait_until(lambda: periods_held(tab) == six, 60.0, "six periods drawn")

        choose_restriction(tab, "all")
        everything = {f"periods[{h}]" for h in range(51)}
        wait_until(lambda: periods_held(tab) == everything, 180.0, "fifty-one periods drawn")
        line, _ = wait_until(lambda: settled_with(" · loop "), 60.0, "the whole trellis's line")
        assert " · shown " not in line, line
        assert restriction_shown(tab) == "all"

        restrict(tab, "periods 1–3, stages tenure")
        wait_until(
            lambda: settled_with(" · shown periods 1–3, stages tenure (3 occurrences)"),
            60.0,
            "the restriction typed at the foot",
        )
        assert restriction_shown(tab) == "periods 1–3, stages tenure"
        open_restriction(tab)
        items, field = restriction_menu_shown(tab)
        assert field == "periods 1–3, stages tenure"
        assert [item for item in items if item[0] == "checkbox"] == [
            ("checkbox", "tenure", True, True),
            *[("checkbox", key, False, False) for key in DURABLES_KEYS[1:]],
        ]
        assert not any(checked for role, _, checked, _ in items if role == "radio")
        choose_restriction(tab, "keeper_cons")
        wait_until(
            lambda: settled_with(" · shown periods 1–3, stages tenure, keeper_cons (6 "),
            60.0,
            "keeper_cons ticked",
        )
        assert restriction_shown(tab) == "periods 1–3, stages tenure, keeper_cons"
        assert restriction_menu_shown(tab) is not None
        tab.keyboard.press("Escape")
        wait_until(lambda: restriction_menu_shown(tab) is None, 5.0, "the menu closed by Escape")
    finally:
        context.close()


# the view tabs `Stage` and `Trellis` of the graph's bar (design pass 2 §4;
# K-D20; design pass 8 §§4 and 6), each tab as its word, whether it is
# marked, whether it is pressed for a screen reader, whether it does not
# act, by `aria-disabled`, and its hover
SWITCH_JS = """
() => Array.from(document.querySelectorAll('.bl-view-switch vscode-tab-header'), (button) => [
  button.textContent.trim(), button.classList.contains('bl-active'),
  button.getAttribute('aria-pressed') === 'true',
  button.disabled || button.getAttribute('aria-disabled') === 'true', button.title])
"""
STAGE_SEGMENT = ".bl-view-switch .bl-stage-button"
TRELLIS_SEGMENT = ".bl-view-switch .bl-trellis-button"
# the hovers of `Stage` with a stage file open and with none, and the hover
# of `Trellis`, the gloss of its term, each with its capital (design pass 8
# §8, item 1)
STAGE_HOVER = "The graph of the stage file open in the editor"
NO_STAGE_HOVER = "No stage file open"
TRELLIS_HOVER = "The model over its periods, each a frame of its stage occurrences"
# the view tabs while the stage's view is shown and while the trellis is
# shown with a stage file open, and while the trellis is shown with none
STAGE_SHOWN = [
    ["Stage", True, True, False, STAGE_HOVER],
    ["Trellis", False, False, False, TRELLIS_HOVER],
]
TRELLIS_SHOWN = [
    ["Stage", False, False, False, STAGE_HOVER],
    ["Trellis", True, True, False, TRELLIS_HOVER],
]
NO_STAGE_FILE = [["Stage", False, False, True, NO_STAGE_HOVER], TRELLIS_SHOWN[1]]


def test_task_18_the_switch_shows_the_stage_or_the_trellis_and_each_choice_is_a_place(
    browser, server_on, model_folder
):
    """Task 18 (design pass 2 §4 and §10; K-D20; AMD-MI-002 §3 rule 4). The
    portfolio model's recipe opened from the tree shows its trellis with
    `declaration/spec.yml` in the editor: the graph's header holds the
    switch `stage │ trellis`, `trellis` marked and `stage` disabled with
    the hover `no stage file open`, and a click on `stage` leaves the
    trellis, the breadcrumb and the history's buttons as they stood. With
    `cons.bl` opened from the tree, `stage` is marked, its word and that of
    `trellis` in the face of the word the direction select shows.
    `trellis` then shows the trellis with the occurrence cons.bl is bound
    as selected, and `stage` shows cons's backward graph again, the
    collection the view held before, with the open file, the editor's
    document and the tabs unchanged. A step back shows the trellis with
    that occurrence selected, and a step forward the stage."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(model_folder), RECIPE_FILE, minimum=10)
        assert open_path_shown(tab) == RECIPE_FILE
        assert tab.evaluate(SWITCH_JS) == NO_STAGE_FILE
        crumbs, buttons = breadcrumb(tab), history_buttons(tab)
        # Playwright clicks a control marked disabled only when forced
        tab.click(STAGE_SEGMENT, force=True)
        # the click changes nothing the page draws, so the page is read again
        # after a second, which holds the server's answer to the click
        tab.wait_for_timeout(1_000)
        assert tab.locator(RESTRICTION).count() == 1
        assert (breadcrumb(tab), history_buttons(tab)) == (crumbs, buttons)
        assert tab.evaluate(SWITCH_JS) == NO_STAGE_FILE

        record_layouts(tab)
        reveal_in_tree(tab, CONS)
        tab.click(f'.bl-tree-file[data-path="{CONS}"]')
        wait_until(lambda: view_laid_out(tab, "cons"), 60.0, "cons.bl's graph laid out")
        wait_until(lambda: status_settled_on(tab, CONS), 60.0, "cons.bl's loop")
        assert tab.evaluate(SWITCH_JS) == STAGE_SHOWN
        faces = tab.evaluate(
            TYPE_FACES_JS,
            [STAGE_SEGMENT, TRELLIS_SEGMENT, ".bl-view-direction vscode-single-select"],
        )
        print(f"task 18: the faces of the switch's words and the direction's word: {faces}")
        assert {tuple(face[:3]) for face in faces} == {tuple(faces[0][:3])}
        assert view_shown(tab) == {"graph": "operator", "direction": "backward"}
        stage = tab.evaluate(HELD_COLLECTION_JS)
        stage_crumbs, occurrence = breadcrumb(tab), recipe_head(tab).replace(" / ", "/")
        # the trellis's breadcrumb ends at the recipe's crumb (R-I157), the
        # stage's path naming the occurrence it is bound as after the recipe
        # by two parts, its key and its period (the fix wave Q3b of unit Q,
        # item 19; C19)
        trellis_crumbs = stage_crumbs.rsplit(" › ", 2)[0]
        document, tabs = tab.evaluate(DOCUMENT_JS), file_tabs(tab)

        def unchanged_editor() -> bool:
            return (open_path_shown(tab), tab.evaluate(DOCUMENT_JS), file_tabs(tab)) == (
                CONS,
                document,
                tabs,
            )

        def the_trellis(since: int) -> bool:
            return (
                view_laid_out(tab, "trellis", since)
                and breadcrumb(tab) == trellis_crumbs
                and panel_head(tab).startswith(occurrence_head(occurrence))
            )

        def the_stage(since: int) -> bool:
            return view_laid_out(tab, "cons", since) and breadcrumb(tab) == stage_crumbs

        since = layouts_recorded(tab)
        tab.click(TRELLIS_SEGMENT)
        wait_until(lambda: the_trellis(since), 60.0, f"the trellis with {occurrence} selected")
        assert tab.evaluate(SWITCH_JS) == TRELLIS_SHOWN
        assert unchanged_editor()

        since = layouts_recorded(tab)
        tab.click(STAGE_SEGMENT)
        wait_until(lambda: the_stage(since), 60.0, "cons.bl's graph shown again")
        assert tab.evaluate(SWITCH_JS) == STAGE_SHOWN
        assert tab.get_attribute(".bl-graph-bar", "data-graph") == "backward"
        assert view_shown(tab) == {"graph": "operator", "direction": "backward"}
        assert as_json(tab.evaluate(HELD_COLLECTION_JS)) == as_json(stage)
        assert unchanged_editor()

        # the history's two places: a step back shows the trellis left, a
        # step forward the stage
        since = layouts_recorded(tab)
        press_outside_fields(tab, "Alt+ArrowLeft")
        wait_until(lambda: the_trellis(since), 60.0, "the trellis by a step back")
        assert tab.evaluate(SWITCH_JS) == TRELLIS_SHOWN
        assert unchanged_editor()
        since = layouts_recorded(tab)
        press_outside_fields(tab, "Alt+ArrowRight")
        wait_until(lambda: the_stage(since), 60.0, "the stage by a step forward")
        assert tab.evaluate(SWITCH_JS) == STAGE_SHOWN
        assert unchanged_editor()
    finally:
        context.close()


# the columns at 1800 × 1000 with Matsya's handle dragged 60 px to the left,
# Matsya then 380 px wide, and with Matsya folded by the button of its head,
# the text and the graph sharing the width of its column and of the column
# gap before it in the proportion of their frame widths, in whole pixels
# (K-D19); the window has a right padding alone since the rail of icons
# left (unit N, Task 1)
DRAGGED_TRACKS = (170, 697, 385, 380)
DRAGGED_FOLDED_TRACKS = (170, 965, 533)
# the window's right padding, at which the graph's column ends while Matsya
# is folded
SIDE_PADDING = 60


def test_task_19_a_folded_matsya_takes_no_width_and_the_main_bar_s_toggle_opens_it(
    browser, server_on, durables_folder
):
    """Task 19 (design pass 2 §5 and §10; K-D19), its control moved to the
    rail of icons by unit L's Task 12 (AAS, L-D12) and from the rail to the
    main bar by unit N's Task 1 (design pass 10 §3). The durables model's
    recipe opened from the tree shows the trellis with Matsya folded (K-D6):
    `.bl-matsya` measures 0 px wide, the window has the three columns of
    TRELLIS_TRACKS and the graph's column ends at the window's side padding.
    The main bar's toggle `Matsya`, hover `Matsya`, stands in the main bar
    at the window's top, its aria-expanded false, and the graph's bar holds
    no fold button and no Υ. Tab from the toggle `Details` reaches the
    toggle, and Enter there opens Matsya at its frame width, the toggle then
    expanded. With `adjuster_cons.bl` opened from the tree at 1800 × 1000,
    Matsya dragged to 380 px and then folded by the button of its head
    measures 0 px, the text and the graph sharing its width and the column
    gap before it; a click on the toggle `Matsya` gives every column the
    width it had before the fold."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        toggle = tab.locator(MATSYA_TOGGLE)

        def folded_to(expected: tuple, width: int) -> bool:
            # the columns `expected`, Matsya 0 px wide and the graph's column
            # ending at the window's side padding
            matsya, view = boxes(tab, ".bl-matsya")[0], boxes(tab, ".bl-view")[0]
            return (
                tracks_near(tab, expected)
                and matsya["width"] == 0
                and abs(view["right"] - (width - SIDE_PADDING)) <= 1
            )

        wait_until(
            lambda: folded_to(TRELLIS_TRACKS[1600, False], 1600),
            10.0,
            "Matsya folded in the trellis view",
        )
        choose_view(tab, None, "forward")
        tab.locator(".bl-stages-button:enabled").wait_for(timeout=60_000)
        assert toggle.is_visible()
        named = [toggle.get_attribute(name) for name in ("title", "aria-label", "aria-expanded")]
        assert named == ["Matsya", "Matsya", "false"]
        button = boxes(tab, MATSYA_TOGGLE)[0]
        print(f"task 19: the main bar's toggle Matsya {button}")
        assert button["bottom"] <= 36, button
        assert tab.locator(".bl-graph-bar .bl-fold").count() == 0
        assert "Υ" not in tab.locator(".bl-graph-bar").text_content()

        # Tab from the toggle `Details` reaches the toggle `Matsya`, and
        # Enter opens Matsya
        tab.locator('.bl-main-bar .bl-fold[data-fold="details"]').focus()
        tab.keyboard.press("Tab")
        assert toggle.evaluate(FOCUSED_JS)
        tab.keyboard.press("Enter")
        wait_until(
            lambda: tracks_near(tab, FRAME_TRACKS[1600, False]), 5.0, "Matsya opened by Enter"
        )
        assert abs(boxes(tab, ".bl-matsya")[0]["width"] - FRAME_TRACKS[1600, False][3]) <= 1
        assert toggle.get_attribute("aria-expanded") == "true"
        assert tab.locator(MATSYA_FOLD).get_attribute("aria-expanded") == "true"

        # a stage's view: Matsya dragged wider, folded by its head's button
        # and opened again by the main bar's toggle
        reveal_in_tree(tab, ADJUSTER_CONS_FILE)
        tab.click(f'.bl-tree-file[data-path="{ADJUSTER_CONS_FILE}"]')
        wait_until(lambda: status_settled_on(tab, ADJUSTER_CONS_FILE), 60.0, "the stage's loop")
        tab.set_viewport_size({"width": 1800, "height": 1000})
        wait_until(lambda: tracks_near(tab, FRAME_TRACKS[1800, False]), 5.0, "the columns at 1800")
        drag_handle(tab, "matsya", -60)
        wait_until(lambda: tracks_near(tab, DRAGGED_TRACKS), 5.0, "Matsya dragged to 380 px")
        tab.click(MATSYA_FOLD)
        wait_until(
            lambda: folded_to(DRAGGED_FOLDED_TRACKS, 1800), 5.0, "Matsya folded by its head"
        )
        print(f"task 19: at 1800 the columns {DRAGGED_TRACKS} and {tracks(tab)}")
        assert toggle.get_attribute("aria-expanded") == "false"
        toggle.click()
        wait_until(lambda: tracks_near(tab, DRAGGED_TRACKS), 5.0, "Matsya opened at 380 px")
        assert abs(boxes(tab, ".bl-matsya")[0]["width"] - DRAGGED_TRACKS[3]) <= 1
    finally:
        context.close()


# the Recipe tab's words, each element as its text and its hover (design
# pass 2 §7; K-D21), as Task 10 of unit M draws the recipe (AAS, M-D17;
# design pass 9 §3) and Task 2 of unit N its strip and cells (design pass 10
# §4): the strip's tab and the file's name with its hover, each column
# head and its hover, each select's value and its field's hover, each `—`
# and its hover, each icon button of a row, `Remove stage` and `New file`,
# by its name and hover, each text of a row outside its controls, each
# periods field's hover, and the hover of each periods text of a row at rest
# (design pass 11 §2)
RECIPE_HOVERS_JS = """
() => {
  const panel = document.querySelector('.bl-classification[data-panel="recipe"]');
  if (!panel) return null;
  const strip = panel.querySelector('.bl-inspector-strip');
  const file = strip.querySelector('.bl-inspector-file');
  const chosen = (field) => {
    const option = field.querySelector('vscode-option[selected]');
    return option ? option.textContent.trim() : null;
  };
  return {
    strip: [strip.querySelector('.bl-class-tab').textContent.trim(), file.textContent.trim(),
      file.getAttribute('title')],
    heads: Array.from(panel.querySelectorAll('.bl-recipe-heads > span'),
      (head) => [head.textContent.trim(), head.getAttribute('title')]),
    selects: Array.from(panel.querySelectorAll('.bl-recipe-entry .bl-field'),
      (field) => [chosen(field), field.getAttribute('title')]),
    none: Array.from(panel.querySelectorAll('.bl-recipe-none'),
      (mark) => [mark.textContent.trim(), mark.getAttribute('title')]),
    buttons: Array.from(panel.querySelectorAll('.bl-recipe-row vscode-toolbar-button'),
      (button) => [button.label, button.getAttribute('title')]),
    words: Array.from(panel.querySelectorAll('.bl-recipe-row button'),
      (button) => button.textContent.trim()),
    periods: Array.from(panel.querySelectorAll('.bl-recipe-periods'),
      (field) => field.getAttribute('title')),
    restPeriods: Array.from(
      panel.querySelectorAll('.bl-recipe-row [data-kind="periods"] .bl-recipe-text'),
      (text) => text.getAttribute('title')),
  };
}
"""
# the hover of each column head of the Recipe tab (design pass 10 §4)
RECIPE_HEAD_HOVERS = [
    ["Stage", "The stage's file"],
    ["Calibration", "Parameter values"],
    ["Settings", "Numerical choices"],
    ["Methods", "Numerical routines for the stage's operations"],
    ["Periods", "The periods the stage stands in"],
]
# the hover of a column the recipe writes nothing for (design pass 9 §3)
NOTHING_WRITTEN = "The recipe writes none"
DURABLES_SLOTS_WRITTEN = {"$fill", "$tenure_method", "$keeper_method", "$adjuster_method"}
# the documentation's paragraph on the recipe in the panel under the editor,
# by the words it opens with (unit M, Task 10)
RECIPE_PARAGRAPH = "**The recipe in the panel under the editor.** "


def one_sentence(text: str) -> bool:
    """Whether `text` is one sentence, holding no second clause after a
    semicolon and no second sentence, the test `test_app.py` applies to
    every term's hover (the texts' rule)."""
    return bool(text) and ";" not in text and ". " not in text.rstrip(".")


def test_task_20_the_recipe_s_words_slots_and_select_say_what_they_are(
    browser, server_on, durables_folder
):
    """Task 20 (design pass 2 §7 and §10; K-D21), on the Recipe tab of unit
    M's Task 10 (AAS, M-D17; design pass 9 §3), with the strip and the
    cells of unit N's Task 2 (design pass 10 §4; N-D5) and the rows at
    rest of design pass 11 §2. The durables
    model's recipe opened from the tree shows its tab `Recipe` in the
    panel's strip beside the file's name, `spec.yml`, its path its hover;
    each column head carries its hover; with each row opened in turn, the
    others at rest, each entry's select carries the
    hover `Replace <the entry as written>`, every slot of the recipe,
    `$fill` and the three methods slots, among them; each column written
    `—` `The recipe writes none`; each row's trash `Remove stage` names the
    stage it takes out of this recipe, and each icon button `New file` the
    file it writes; no row holds a word on a button; and each periods field
    names the periods the trellis lists the stage in, as each periods text
    of a row at rest does. Each hover is one sentence. The
    paragraph "The recipe in the panel under the editor" of
    `docs/overview/07-workbench.md` holds four sentences and names the
    select, `New file` and the slot."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        tab.wait_for_selector(".bl-recipe-table .bl-recipe-row", timeout=60_000)
        shown, _ = wait_until(
            lambda: (lambda drawn: drawn if drawn and drawn["selects"] else None)(
                tab.evaluate(RECIPE_HOVERS_JS)
            ),
            30.0,
            "the Recipe tab's words",
        )
        print(f"task 20: the recipe's words and hovers at rest: {shown}")
        assert shown["strip"] == ["Recipe", "spec.yml", RECIPE_FILE]
        assert shown["heads"] == RECIPE_HEAD_HOVERS
        # each row opened in turn, the others at rest (design pass 11 §2)
        opened = with_each_recipe_row_open(tab, lambda tab: tab.evaluate(RECIPE_HOVERS_JS))
        print(f"task 20: the rows opened in turn: {opened}")
        selects = [select for found in opened.values() for select in found["selects"]]
        assert {value for value, _ in selects} >= DURABLES_SLOTS_WRITTEN
        for value, hover in selects:
            assert hover.startswith("Replace ") and hover.endswith(value.split("/")[-1]), (
                value,
                hover,
            )
        assert shown["none"] and all(mark == ["—", NOTHING_WRITTEN] for mark in shown["none"])
        buttons = shown["buttons"] + [
            button for found in opened.values() for button in found["buttons"]
        ]
        removes = [hover for name, hover in shown["buttons"] if name == "Remove stage"]
        assert removes == [f"Remove {key} from this recipe" for key in DURABLES_KEYS]
        writes = [hover for name, hover in buttons if name == "New file"]
        assert writes and all(hover.startswith("Write declaration/") for hover in writes)
        assert {name for name, _ in buttons} == {"Remove stage", "New file"}
        assert shown["words"] == [] and [found["words"] for found in opened.values()] == [[]] * 4
        periods = [hover for found in opened.values() for hover in found["periods"]]
        assert periods == ["Listed in periods 0–50"] * 3 + ["Listed in periods 0"]
        assert shown["restPeriods"] == periods
        hovers = [
            shown["strip"][2],
            *(hover for _, hover in shown["heads"]),
            *(hover for _, hover in selects + shown["none"] + buttons),
            *periods,
        ]
        assert [hover for hover in hovers if not one_sentence(hover)] == []
    finally:
        context.close()

    page = (ROOT / "docs/overview/07-workbench.md").read_text(encoding="utf-8")
    (paragraph,) = [line for line in page.splitlines() if line.startswith(RECIPE_PARAGRAPH)]
    sentences = re.split(r"(?<=\.)\s+", paragraph[len(RECIPE_PARAGRAPH) :].strip())
    print(f"task 20: the paragraph's sentences: {sentences}")
    assert len(sentences) == 4
    assert all(sentence.endswith(".") for sentence in sentences)
    assert "Each entry is a select" in paragraph and "`New file`" in paragraph
    assert "slot" in paragraph


# the occurrence of the durables model in the terminal period whose fields
# design pass 2 §2 draws, and the ids of its own `Inputs` and `Outputs`
ADJUSTER_CONS = "periods[0]/adjuster_cons"
ADJUSTER_CONS_OWN = (f"{ADJUSTER_CONS}/GraphInputs", f"{ADJUSTER_CONS}/GraphOutputs")
# The card of a stage occurrence drawn compact (AAS, L-D7 and L-D16), read
# as FRAME_TEXTS_JS reads a closed occurrence's card: its open layer,
# `.bf-layer.bf-compact`, and its name, `.bf-layer-name`.
COMPACT_TEXTS_JS = FRAME_TEXTS_JS.replace("> .bf-box`", "> .bf-layer.bf-compact`").replace(
    "':scope > .bf-name'", "':scope > .bf-layer-name'"
)
# the least size on the screen of a control's target (spec 0.4 §5.8)
TARGET_LEAST = 24


def field_labels(graph: dict, node: str) -> tuple[list, list]:
    """The labels the graph JSON gives the field ports of the node `node`
    of the trellis graph `graph`, reading and writing, each list in the
    order of the node's ports (spec 0.4 §3.4)."""
    (found,) = [item for item in graph["nodes"] if item["id"] == node]
    return tuple(
        [
            attribute_of(port, "label")
            for port in found.get(key) or []
            if FIELD_PORT.search(port["id"])
        ]
        for key in ("inputsMetadata", "outputsMetadata")
    )


def test_task_21_the_trellis_opens_on_its_terminal_period_with_its_header_in_view_and_inputs_print_the_fields(
    browser, server_on, durables_folder
):
    """Task 21 (K-D22, which builds K-D6's words; K-D15 as AAS asked it of
    the trellis view; rows K-I91, K-I101 and K-I105; design pass 2 §2 for
    the face), its frame the card of unit L's Task 30 (AAS, L-D25; design
    pass 7 §3). The durables model's recipe
    `declaration/spec.yml`, opened at 1600 × 1000, shows its backward and
    then its forward trellis graph, each opened on `periods[0]` by K-D22's
    rule as AAS's M-D15 amends it: at the largest scale, at most 1 and at
    least 0.6, at which the layer fills the region, the body cut where it
    is taller than the region (`opened_on_the_terminal_period`). The
    forward graph opens at a scale from the reading scale 0.6 to 1, the
    layer's toggle at least 24 px across (spec 0.4 §5.8). There the open occurrence
    `adjuster_cons`, drawn compact since unit L's Task 8 (AAS, L-D7), no
    field of which is unjoined, prints no field's name, its card as high as
    its name's row, its strip of builders and its padding (AAS, L-D25).
    Selected, it prints every arrival
    field of its `Inputs` and every continuation field of its `Outputs` as
    the graph JSON labels them with no perch's sign, in the order of the
    graph JSON's ports, and no other label, each in a row of its own under
    its name at the card's left or right edge, in the port face, the card
    as high as its name's row, its band and its fuller side's rows, its
    ports the cables' on the head's part of the card (design pass 10 §6;
    unit N, Task 7); selected at 0.9, each such text is at least 9 px high
    on the screen. The scale and the
    toggle's size at which the backward graph opens are printed for the
    record (row K-I209)."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        record_layouts(tab)
        held = tab.evaluate(HELD_COLLECTION_JS)
        G = tab.evaluate("() => window.BellmanFlowLayout.G")
        openings = {}
        for direction in ("backward", "forward"):
            if direction == "forward":
                choose_view(tab, None, "forward")
                wait_until(
                    lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph"
                )
            opening = opened_on_the_terminal_period(tab, f"the {direction} graph on periods[0]")
            seen = opening["seen"]
            toggle = seen["toggle"]
            cut = seen["layer"]["bottom"] > seen["host"]["bottom"] + 1
            print(
                f"task 21: the {direction} graph opens at {opening['zoom']:.3f}, the toggle "
                f"{toggle['right'] - toggle['left']:.2f} px across, the layer's body "
                f"{'cut by' if cut else 'within'} the region"
            )
            openings[direction] = opening
        forward = openings["forward"]
        zoom = forward["zoom"]
        assert READING_SCALE <= zoom <= 1, forward
        toggle = forward["seen"]["toggle"]
        across = min(toggle["right"] - toggle["left"], toggle["bottom"] - toggle["top"])
        assert round(across, 2) >= TARGET_LEAST, toggle

        graph = graph_named(held, "forward")
        box = ADJUSTER_CONS + LAYER_ID_ENDING
        frame = tab.evaluate(COMPACT_TEXTS_JS, box)
        assert frame is not None, f"{box} is not drawn compact"
        assert frame["reading"] == frame["writing"] == []
        edge = frame["frame"]
        high = G["cardH"]
        assert abs((edge["bottom"] - edge["top"]) / zoom - high) <= 0.5, (edge, high)

        # selected, the card prints every field of its `Inputs` and `Outputs`
        tab.click(f'.react-flow__node[data-id="{box}"] .bf-layer-name')
        frame, _ = wait_until(
            lambda: (lambda found: found if found and found["reading"] else None)(
                tab.evaluate(COMPACT_TEXTS_JS, box)
            ),
            30.0,
            f"{box} selected",
        )
        for own, writes in zip(ADJUSTER_CONS_OWN, (False, True)):
            labels = [printed_name(label, True) for label in field_labels(graph, own)[writes]]
            printed = frame["writing" if writes else "reading"]
            print(f"task 21: {box} prints {[label['text'] for label in printed]}")
            assert labels and [label["text"] for label in printed] == labels, (own, printed)
        in_rows_under_its_name(frame, zoom, G)
        names = centered_on(tab, box, LEGIBLE_SCALE, COMPACT_TEXTS_JS, selected=True)
        in_rows_under_its_name(names, LEGIBLE_SCALE, G)
        heights = [label["height"] for label in names["reading"] + names["writing"]]
        assert min(heights) >= FRAME_TEXT_LEAST, heights
    finally:
        context.close()


# The trellis file of a model folder in the one layout, which writes the
# inter-period mapping.
TRELLIS_FILE = "declaration/trellis.yml"
# the four ids by which an event names a join wire (J-D33)
JOIN_IDS = ("source", "sourceHandle", "target", "targetHandle")
# the side in px on the screen of the square drawn at each end of a selected
# join wire that a drag can move, and the radius in px on the screen of the
# circle beside each such end that takes the press, at every scale (unit K's
# decisions K-D23 and K-D27)
WIRE_END = 10
RECONNECT = 16
# The join wires the region holds, the records Python gives it.
REGION_JOINS_JS = "() => document.querySelector('.bl-view-host').bellmanFlow.joins()"
# The selected join wire, null where none is selected: its two stage
# occurrences; at each end it can move, the square a wire draws, or the
# anchor of the square's place and size that a cable keeps unpainted, its
# end, whether it is a square, its fill as the browser computes it and its
# size on the screen; the radius on the screen of the circle beside each end
# that takes the press, by the end, each size to a tenth of a pixel (unit
# K's decisions K-D23 and K-D27); and the ends whose ports take the accent
# ring, a cable's plug for a writing end and its drawn socket for a reading
# end (the fix wave Q3a of unit Q, item 5, which amends K-D23's squares for
# cables).
WIRE_ENDS_JS = """
() => {
  const edge = document.querySelector('.bl-view-host .react-flow__edge.bf-join-wire.selected');
  if (!edge) return null;
  const tenth = (size) => Math.round(size * 10) / 10;
  const host = document.querySelector('.bl-view-host');
  const handle = (id) => Array.from(host.querySelectorAll('.react-flow__handle'))
    .find((element) => element.dataset.handleid === id) || null;
  const drawn = (element) => element && element.classList.contains('bf-cable-hidden')
    ? element.parentElement.querySelector(':scope > .bf-cable-arrival:not(.bf-cable-hidden)') : element;
  const [source, target] = (edge.dataset.id || '').split('>>');
  const rung = (element) => !!element && element.classList.contains('bf-moving');
  return {
    from: edge.dataset.from,
    to: edge.dataset.to,
    ends: Array.from(edge.querySelectorAll('.bf-wire-end, .bf-wire-anchor'), (end) => {
      const at = end.getBoundingClientRect();
      return {end: end.dataset.end, square: end.classList.contains('bf-wire-end'), fill: getComputedStyle(end).fill,
              width: tenth(at.width), height: tenth(at.height)};
    }),
    radii: Object.fromEntries(Array.from(
      edge.querySelectorAll('.react-flow__edgeupdater'), (circle) => [
        circle.classList.contains('react-flow__edgeupdater-source') ? 'writing' : 'reading',
        tenth(circle.getBoundingClientRect().width / 2)])),
    rings: [['writing', handle(source)], ['reading', drawn(handle(target))]]
      .filter(([, element]) => rung(element)).map(([end]) => end),
  };
}
"""


def region_join(page, writing: str, reading: str) -> dict:
    """The record of the join wire from the stage occurrence `writing` to
    `reading`, each by its address, that the region holds
    (REGION_JOINS_JS)."""
    (found,) = [
        join
        for join in page.evaluate(REGION_JOINS_JS) or []
        if (join["from"], join["to"]) == (writing, reading)
    ]
    return found


def test_task_22_every_join_wire_moves_and_one_of_several_entries_through_the_list(
    browser, server_on, scratch_durables, tmp_path
):
    """Task 22 (K-D23; design pass 2 §2; J-D33, J-D39, K-D8). On a copy of
    the durables model, `periods 0–2`, its trellis file open in the editor:
    the piece that the wires from periods[1] share, a cable, selected,
    draws no square: its socket takes the accent ring, and an unpainted
    anchor of 10 px keeps the square's place at its reading end alone; and
    the wire from `keeper_cons` in periods[1] to `tenure` in periods[0], a
    cable, selected, rings its plug and its socket, with an anchor at both
    ends, each end taken in a circle of radius 16 px beside its port (the
    fix wave Q3a of unit Q, item 5, which amends K-D23's squares for
    cables).
    The reading end of that wire, which three entries of the standing
    inter-period mapping write, dragged to `bequest`'s arrival port in
    periods[0] opens the list headed
    `periods[1]/keeper_cons → periods[0]/bequest`, one row for each of the
    three field pairs, each ticked where Python's pairing names a port of
    `bequest`, each field printed with its declared set (K-D25): none
    ticked, since `bequest`'s arrival fields `a_bq`, `h_bq` and `z_bq` bear
    none of the pairs' arrival names and pair with no continuation name
    (unit L, Task 19), and no other row, since `keeper_cons` has no other
    unjoined continuation field, so that `join` does not act. The author's
    choice of the three fields ticks the rows;
    `join` sends one event `moved` naming the wire, the end and the three
    pairs with the ports they leave, and the trellis file's text takes the
    removal of the three entries and the three new entries in one change,
    which the status line names in unit J's words and one undo of the editor
    takes back; the file on disk is unchanged. On the trial copy of the
    portfolio model the one-entry move writes as unit J's test has it: the
    join `a: k` dragged from `disc` to `port`, its reading end moved to
    `cons`'s `m` opens no list, sends `moved` with the new port, and types
    `a: m` in its place in one change."""
    folder = model.open_folder(scratch_durables)
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, recipe.Source("recipe", RECIPE_FILE), restriction).shown
    writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
    keeper = {(w["from"], w["to"]): w for w in trellis.join_wires(shown)}[writer, reader]
    bequest = {
        field: field_port(shown, "reading", (0, "bequest", field))["id"]
        for field in ("a_bq", "h_bq", "z_bq")
    }
    pairs = [
        {"sourceHandle": f["writing"], "targetHandle": port, "replaced": f["reading"]}
        for f, port in zip(keeper["fields"], bequest.values())
    ]
    event = {
        "reading": trellis.reading_record(folder, shown),
        "join": {name: keeper[name] for name in JOIN_IDS},
        "end": "reading",
        "pairs": pairs,
    }
    move = trellis.removal_edit(shown, event, {})
    assert move.note == (
        "trellis.yml, inter_connectors[0]: a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z changed to "
        "a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, periods 0–50"
    )
    (typed,) = move.edits.values()
    before = (scratch_durables / TRELLIS_FILE).read_text(encoding="utf-8")
    # each arrival field of `bequest` as the list prints it, with its
    # declared set and its sources (K-D25)
    sets = {record["id"]: record["set"] for record in trellis.connectable_ports(shown, {})}
    options = ["—"] + [
        f"{field_text(field, sets[port])} · 2 sources" for field, port in bequest.items()
    ]
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_durables), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        # the trellis file open, so that the editor's undo reaches the move
        open_tree_file(tab, TRELLIS_FILE)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the join wires of the forward graph",
        )
        anchor = {"square": False, "fill": "none", "width": WIRE_END, "height": WIRE_END}
        click_join(tab, "periods[1]", reader)
        assert tab.evaluate(WIRE_ENDS_JS) == {
            "from": "periods[1]",
            "to": reader,
            "ends": [{"end": "reading", **anchor}],
            "radii": {"reading": RECONNECT},
            "rings": ["reading"],
        }
        click_join(tab, writer, reader)
        assert tab.evaluate(WIRE_ENDS_JS) == {
            "from": writer,
            "to": reader,
            "ends": [{"end": "writing", **anchor}, {"end": "reading", **anchor}],
            "radii": {"writing": RECONNECT, "reading": RECONNECT},
            "rings": ["writing", "reading"],
        }
        assert region_join(tab, writer, reader)["fields"] == keeper["fields"]
        reading = tab.evaluate(REGION_READING_JS)

        hold_events(tab, "moved")
        move_join_end(tab, writer, reader, "target", bequest["a_bq"])
        listed, _ = wait_until(lambda: tab.evaluate(PAIR_LIST_JS), 10.0, "the list of the move")
        assert listed == {
            "head": f"{writer} → periods[0]/bequest",
            "rows": [
                [field_text(f["field"], f["field_set"]), False, "—", options]
                for f in keeper["fields"]
            ],
            "join": False,
        }
        rows = tab.locator(".bl-view-host .bf-pair-row")
        for i, port in enumerate(bequest.values()):
            rows.nth(i).locator(".bf-pair-to").select_option(value=port)
        assert tab.evaluate(PAIR_LIST_JS)["rows"] == [
            [field_text(f["field"], f["field_set"]), True, chosen, options]
            for f, chosen in zip(keeper["fields"], options[1:])
        ]
        tab.click(".bl-view-host .bf-pair-join")
        assert tab.evaluate(PAIR_LIST_JS) is None
        assert held_events(tab, "moved") == [{**event, "reading": reading}]
        release_events(tab, "moved")
        wait_until(lambda: gesture_note(tab) == move.note, 10.0, "the note of the move")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == typed, 10.0, "the move typed")
        assert open_path_shown(tab) == TRELLIS_FILE
        wait_until(lambda: unsaved_in_tree(tab) == [TRELLIS_FILE], 10.0, "the file unsaved")
        assert (scratch_durables / TRELLIS_FILE).read_text(encoding="utf-8") == before
        # one undo takes back the removal and the writing together
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == before, 10.0, "the move undone in one step"
        )
    finally:
        context.close()

    copy = emptied_portfolio(tmp_path / "portfolio")
    text = (copy / TRELLIS_FILE).read_text(encoding="utf-8")
    joined, moved = (text.replace("  - {}\n", f"  - {{{pair}}}\n") for pair in ("a: k", "a: m"))
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        open_tree_file(tab, TRELLIS_FILE)
        choose_view(tab, None, "forward")
        wait_until(lambda: DISC_A in unjoined_port_ids(tab), 30.0, "the forward graph's ports")
        drag_ports(tab, DISC_A, PORT_K)
        wait_until(lambda: gesture_note(tab) == DISC_TO_PORT, 10.0, "the note of the join")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == joined, 10.0, "the join typed")
        between = ("periods[3]/disc", "periods[2]/port")
        wait_until(
            lambda: between in {(w["from"], w["to"]) for w in join_wires_drawn(tab)}
            and CONS_M in unjoined_port_ids(tab),
            60.0,
            "the join's wire",
        )
        wire = region_join(tab, *between)
        assert (wire["movable"], len(wire["fields"])) == (["writing", "reading"], 1)
        reading = tab.evaluate(REGION_READING_JS)
        hold_events(tab, "moved")
        move_join_end(tab, *between, "target", CONS_M)
        tab.evaluate(TWO_FRAMES_JS)
        assert tab.evaluate(PAIR_LIST_JS) is None
        assert held_events(tab, "moved") == [
            {
                "reading": reading,
                "join": {name: wire[name] for name in JOIN_IDS},
                "end": "reading",
                "handle": CONS_M,
            }
        ]
        release_events(tab, "moved")
        note = "trellis.yml, inter_connectors[0]: a: k changed to a: m, periods 0–5"
        wait_until(lambda: gesture_note(tab) == note, 10.0, "the note of the move")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == moved, 10.0, "the move typed")
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(
            lambda: tab.evaluate(DOCUMENT_JS) == joined, 10.0, "the move undone in one step"
        )
        assert (copy / TRELLIS_FILE).read_text(encoding="utf-8") == text
    finally:
        context.close()


# The stage list the region draws over the graph, and the control at the
# right of a list's first line that closes it, the stage list's and the
# pairing list's (unit K's decision K-D24).
STAGE_LIST = ".bl-view-host .bf-stage-list"
LIST_CLOSE = ".bf-list-close"
# the icon of that control, the Codicon `close` (AAS, L-D8; design pass 8
# §3; unit M, Task 7), and its hover text and spoken name (the texts' rule)
CLOSE_ICON = "close"
CLOSE_HOVER = "close"
# the name in the head of the list that the button `Stages` opens (unit L,
# Task 23; design pass 4 §4): the button's word
STAGES_HEADING = "Stages"
# A point of the graph region on the screen at which the browser finds the
# graph's ground, `.react-flow__pane`, and the center of a box of the graph
# at which the browser finds that box, each outside the stage list and null
# where none is found: {pane: {x, y}, box: {x, y, id}} (K-D24). A box is a
# closed box or, since the list stands beside the button that opened it
# and may cover every closed box, a card's name (unit N, Task 5; design
# pass 10 §7).
OUTSIDE_THE_LIST_JS = """
() => {
  const region = document.querySelector('.bl-view-host .bf-region').getBoundingClientRect();
  const list = document.querySelector('.bl-view-host .bf-stage-list');
  const away = list ? list.getBoundingClientRect() : null;
  const outside = (x, y) =>
    !away || x < away.left || x > away.right || y < away.top || y > away.bottom;
  const inside = (x, y) =>
    x > region.left + 4 && x < region.right - 4 && y > region.top + 4 && y < region.bottom - 4;
  let pane = null;
  for (let y = region.top + 12; !pane && y < region.bottom - 12; y += 12) {
    for (let x = region.left + 12; !pane && x < region.right - 12; x += 12) {
      const hit = document.elementFromPoint(x, y);
      if (outside(x, y) && hit && hit.classList.contains('react-flow__pane')) pane = {x, y};
    }
  }
  let box = null;
  const boxes = document.querySelectorAll(
    '.bl-view-host .react-flow__node > .bf-box, .bl-view-host .react-flow__node > .bf-compact > .bf-layer-name');
  for (const element of boxes) {
    const at = element.getBoundingClientRect();
    const x = (at.left + at.right) / 2, y = (at.top + at.bottom) / 2;
    const hit = document.elementFromPoint(x, y);
    if (inside(x, y) && outside(x, y) && hit && element.contains(hit)) {
      box = {x, y, id: element.closest('.react-flow__node').dataset.id};
      break;
    }
  }
  return {pane, box};
}
"""
# The control that closes the list `.bf-stage-list` or `.bf-pair-list`
# named by the argument, null where that list is not drawn and {} where it
# carries no such control: its element's name, its text, the name of the
# icon it holds, null where it holds none, its hover, its spoken name, its
# size on the screen, and whether it stands at the right of
# the list's first line, its head (unit L, Task 23), its middle within that
# line's height and its box in the list's right half (K-D24).
CLOSE_CONTROL_JS = """
(name) => {
  const list = document.querySelector(`.bl-view-host ${name}`);
  if (!list) return null;
  const close = list.querySelector(':scope > .bf-list-head > .bf-list-close');
  if (!close) return {};
  const line = list.firstElementChild.getBoundingClientRect();
  const at = close.getBoundingClientRect(), whole = list.getBoundingClientRect();
  const middle = (at.top + at.bottom) / 2;
  const icon = close.querySelector('.codicon');
  const glyph = icon
    ? Array.from(icon.classList).find((name) => name.startsWith('codicon-')).slice(8) : null;
  return {
    tag: close.tagName, text: close.textContent, icon: glyph,
    title: close.getAttribute('title'),
    label: close.getAttribute('aria-label'), width: at.width, height: at.height,
    right: at.left >= whole.left + whole.width / 2 && middle > line.top && middle < line.bottom,
  };
}
"""
# For each end of the selected join wire that a drag can move, null where
# none is selected: the end, and the distances on the screen, to a tenth of
# a pixel, from its port to the center of its square, or of a cable's
# unpainted anchor of the square's place (the fix wave Q3a of unit Q, item
# 5), and to the center of the circle in which a press takes it, the port's
# place being the origin the region writes for the square (K-D23, K-D27).
WIRE_END_PLACES_JS = """
() => {
  const edge = document.querySelector('.bl-view-host .react-flow__edge.bf-join-wire.selected');
  if (!edge) return null;
  const center = (element) => {
    const at = element.getBoundingClientRect();
    return [(at.left + at.right) / 2, (at.top + at.bottom) / 2];
  };
  return Array.from(edge.querySelectorAll('.bf-wire-end, .bf-wire-anchor'), (square) => {
    const [x, y] = square.style.transformOrigin.split(' ').map(parseFloat);
    const m = square.ownerSVGElement.getScreenCTM();
    const port = [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f];
    const side = square.dataset.end === 'writing' ? 'source' : 'target';
    const circle = edge.querySelector('.react-flow__edgeupdater-' + side);
    const away = (point) =>
      Math.round(Math.hypot(point[0] - port[0], point[1] - port[1]) * 10) / 10;
    return [square.dataset.end, away(center(square)), away(center(circle))];
  });
}
"""
# the hover of the control that closes a list where that control holds the
# focus, null otherwise
FOCUSED_CONTROL_JS = """
() => {
  const active = document.activeElement;
  const close = active && active.classList.contains('bf-list-close');
  return close ? active.getAttribute('title') : null;
}
"""


def open_stage_list_by(page, opener: str, view: dict) -> None:
    """Opens the stage list with the control `opener`, the button `stages`
    or a period's `+ stage`, the region's view first set to `view`, the
    handle's record of a view (`flow_handle`, `view`), and waits until the
    list's first item holds the focus."""
    flow_handle(page, "setView", view)
    page.evaluate(TWO_FRAMES_JS)
    page.click(opener)
    page.wait_for_selector(f"{STAGE_LIST} .bf-stage-item", timeout=10_000)
    wait_until(
        lambda: keyboard_place(page)["item"] is not None, 5.0, "the list's first item focused"
    )


def stage_list_open(page) -> bool:
    """Whether the region draws the stage list."""
    return page.locator(STAGE_LIST).count() == 1


def test_task_23_the_stage_list_closes_on_a_click_outside_it_and_a_wire_s_ends_keep_their_size(
    browser, server_on, durables_folder
):
    """Task 23 (K-D24 and K-D27; spec 0.4 §3.5 and §5.8; the texts' rule). On
    the durables model's forward trellis graph, `periods 0–2`, as it opens,
    at a scale from 0.6 to 1 (AAS, M-D15): the stage list opened by
    `stages`, whose head names `stages`, and
    the list opened by `+ stage` of periods[0], whose head names
    `periods[0]` (unit L, Task 23), each close on a click on the graph's
    ground and on a click on a box, stay open on a click on that name, and
    close by the control at its head's right, the button holding the icon
    `x` (AAS, L-D8, L-D15), whose hover and spoken name are
    `close`, at least 24 px square; Shift+Tab from the first item, which
    holds the focus when the list opens, reaches that control, and Enter on
    it closes the list as Escape does, the graph taking the focus. The join
    wire from `keeper_cons` in periods[1] to `tenure` in periods[0], a
    cable, selected, draws no square: the ports of the ends it can move take
    the accent ring, and the unpainted anchor of each such end keeps the
    square's 10 px on the screen, its center 8 px from the port, each end
    taken in a circle of radius 16 px on the screen whose center stands 16
    px from the port (the fix wave Q3a of unit Q, item 5, which amends
    K-D23's squares for cables), at the scale at which `click_join` selects
    it, at the opening scale and at the scale of `fit`; its reading end dragged to `bequest`'s arrival port
    opens the cable's list (design pass 10 §7), which carries the same
    control at the right of its head and closes by it with no event sent."""
    writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
    # each control that opens the stage list, with the part of its list's
    # head, its first line, that names it, and the text that part prints
    # (unit L, Task 23)
    openers = {
        ".bl-stages-button": (".bf-list-name", STAGES_HEADING),
        f"{period_node(0)} > .bf-layer > .bf-add-stage": (".bf-stage-period", "periods[0]"),
    }
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert restriction_shown(tab) == "periods 0–2"
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(lambda: tab.evaluate(VIEW_STATE_JS)["current"], 60.0, "the forward graph")
        opening = opened_on_the_terminal_period(tab, "the forward graph on periods[0]")
        assert READING_SCALE <= opening["zoom"] <= 1, opening
        opened = flow_handle(tab, "view")
        for opener, (first, text) in openers.items():
            for place in ("pane", "box"):
                open_stage_list_by(tab, opener, opened)
                point = tab.evaluate(OUTSIDE_THE_LIST_JS)[place]
                assert point is not None, (opener, place)
                tab.mouse.click(point["x"], point["y"])
                wait_until(
                    lambda: not stage_list_open(tab),
                    5.0,
                    f"the list closed by a click on a {place}",
                )
            open_stage_list_by(tab, opener, opened)
            assert tab.locator(f"{STAGE_LIST} > .bf-list-head {first}").text_content() == text
            tab.click(f"{STAGE_LIST} > .bf-list-head {first}")
            tab.wait_for_timeout(300)
            assert stage_list_open(tab), (opener, "closed by a click on its first line")
            control = tab.evaluate(CLOSE_CONTROL_JS, ".bf-stage-list")
            assert min(control.pop("width"), control.pop("height")) >= TARGET_LEAST, control
            assert control == {
                "tag": "BUTTON",
                "text": "",
                "icon": CLOSE_ICON,
                "title": CLOSE_HOVER,
                "label": CLOSE_HOVER,
                "right": True,
            }
            tab.click(f"{STAGE_LIST} > .bf-list-head > {LIST_CLOSE}")
            wait_until(lambda: not stage_list_open(tab), 5.0, "the list closed by its ×")
            # the control reached and pressed by the keyboard
            open_stage_list_by(tab, opener, opened)
            tab.keyboard.press("Shift+Tab")
            assert tab.evaluate(FOCUSED_CONTROL_JS) == CLOSE_HOVER
            tab.keyboard.press("Enter")
            wait_until(
                lambda: not stage_list_open(tab) and keyboard_place(tab)["box"] is not None,
                5.0,
                "the list closed by Enter on its × and the focus in the graph",
            )

        # the ends of a selected join wire, a cable, at three scales (K-D27): unpainted anchors of the squares'
        # places and sizes, and its plug and its socket ringed (the fix wave Q3a, item 5)
        anchor = {"square": False, "fill": "none", "width": WIRE_END, "height": WIRE_END}
        drawn = {
            "from": writer,
            "to": reader,
            "ends": [{"end": "writing", **anchor}, {"end": "reading", **anchor}],
            "radii": {"writing": RECONNECT, "reading": RECONNECT},
            "rings": ["writing", "reading"],
        }
        click_join(tab, writer, reader)
        scales = []
        for step in ("selected", "opening", "fit"):
            if step == "opening":
                flow_handle(tab, "setView", {"viewport": opened["viewport"]})
            elif step == "fit":
                tab.click(".bl-zoom-button[data-zoom='fit']")
            tab.evaluate(TWO_FRAMES_JS)
            scales.append(viewport(tab)["zoom"])
            assert tab.evaluate(WIRE_ENDS_JS) == drawn, (step, scales[-1])
            assert tab.evaluate(WIRE_END_PLACES_JS) == [
                [end, RECONNECT / 2, RECONNECT] for end in ("writing", "reading")
            ], (step, scales[-1])
        print(f"task 23: the wire's ends measured at the scales {[round(s, 3) for s in scales]}")
        assert READING_SCALE <= scales[1] <= 1 and len({round(s, 3) for s in scales}) == 3, scales

        # the pairing list carries the same control (K-D24)
        hold_events(tab, "moved")
        # the reading end dropped on `bequest`'s arrival port opens the
        # cable's list (design pass 10 §7)
        arrival = cable_port(tab, "periods[0]/bequest", "reading")
        move_join_end(tab, writer, reader, "target", arrival)
        wait_until(lambda: cable_list(tab), 10.0, "the pairing list")
        control = tab.evaluate(CLOSE_CONTROL_JS, ".bf-pair-list")
        assert min(control.pop("width"), control.pop("height")) >= TARGET_LEAST, control
        assert control == {
            "tag": "BUTTON",
            "text": "",
            "icon": CLOSE_ICON,
            "title": CLOSE_HOVER,
            "label": CLOSE_HOVER,
            "right": True,
        }
        tab.click(f".bl-view-host .bf-pair-list > .bf-list-head > {LIST_CLOSE}")
        wait_until(lambda: cable_list(tab) is None, 5.0, "the pairing list closed")
        tab.wait_for_timeout(300)
        assert held_events(tab, "moved") == []
        release_events(tab, "moved")
    finally:
        context.close()


# The text a pairing list prints for each arrival field of `tenure` in
# periods[0] of the durables model, which the two consumption stages of
# periods[1] both join: its name, its declared set as tenure.bl writes it,
# and the number of its sources (unit K's decision K-D25; J-D42).
TENURE_OPTIONS = ["—", "a : ℝ₊ · 2 sources", "h : ℝ₊₊ · 2 sources", "z : ℝ₊₊ · 2 sources"]
# the start of the status line's note of the join of `port`'s m_next to
# `tenure`'s a, which then names the draft the package reports (unit N,
# Task 7)
M_NEXT_TO_A = "trellis.yml, inter_connectors[0]: m_next: a written, periods 0–50"
# For each select of the pairing list, its width on the screen and the width
# its widest option asks, so that a test can read that no option is cut
# (the texts' rule).
SELECT_WIDTHS_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .bf-pair-row select'), (select) => {
  const given = select.getBoundingClientRect().width;
  select.style.width = 'max-content';
  const asked = select.getBoundingClientRect().width;
  select.style.width = '';
  return [given, asked];
})
"""
# the color of the declared sets the pairing list prints, as the browser
# computes it, null where it prints none
PAIR_SET_COLOR_JS = """
() => {
  const set = document.querySelector('.bl-view-host .bf-pair-list .bf-pair-set');
  return set ? getComputedStyle(set).color : null;
}
"""


def field_text(field: str, declared: str) -> str:
    """The text a pairing list prints for a field: its name and, where it
    declares a set, the set after ` : ` (unit K's decision K-D25)."""
    return f"{field} : {declared}" if declared else field


def error_sentences(folder, outcome) -> list[str]:
    """The sentences that the list under the error mark holds for the
    reading `outcome` of a trellis, as the package answers them and the page
    prints them, their paths relative to the model folder `folder`
    (`trellis.relative_sentence`; K-D11), in sorted order: the refusal of
    the reading, where it was refused; else the sentence of each graph the
    package refused to draw, each note of the trellis's binding, and each
    native connection diagnostic."""
    if outcome.refusal is not None:
        found = [outcome.refusal.message]
    else:
        found = [
            attribute_of(graph["nodes"][0], "refusal")
            for graph in outcome.shown.collection["graphs"]
            if [node["id"] for node in graph["nodes"]] == [f"{graph['id']}:refused"]
        ]
        found += trellis.binding_notes(outcome.shown.binding)
        found += [diagnostic.message for diagnostic in outcome.shown.selection.diagnostics]
    return sorted(trellis.relative_sentence(folder, sentence) for sentence in found)


def test_task_24_the_pairing_list_prints_each_field_s_set_and_port_joins_tenure_by_hand(
    browser, server_on, scratch_durables
):
    """Task 24 (K-D25; K-D8, K-D11; A2-D13). On a copy of the durables
    model, `periods 0–2`, its forward trellis graph shown: `+ stage` of
    periods[1] and a click on the corpus's template `port` copy its files
    under the key `port`, write the key into the period file's list and
    print the note the package's drop answers, and `port` is drawn in
    periods[1] and periods[2]. A drag from `port`'s frame in periods[1] to
    `tenure`'s frame in periods[0] opens the list whose one row prints
    `m_next : ℝ₊₊`, the set in ice-3, against `tenure`'s arrival fields
    `a : ℝ₊`, `h : ℝ₊₊` and `z : ℝ₊₊`, each with the number of its
    sources, no option cut. No arrival field is proposed, since no name
    pairs with `m_next` and joins reach all three (K-I158), so the row
    stands unticked with `—` chosen and `join` does not act, though `h` and
    `z` declare `m_next`'s set; the page ticks nothing by set. `a` chosen by
    hand ticks the row; `join` sends the event `connected`
    with the one pair, and the note and the text typed into the trellis
    file are those `connector_edit` answers, `m_next: a` added to the
    inter-period mapping, the files on disk unchanged. The trellis is then
    read again, and the status line and the list under the error mark
    print what the package answers on the same texts, constructed or
    refused; the test prints which and asserts no rule of its own."""
    copy = scratch_durables
    folder = model.open_folder(copy)
    source = recipe.Source("recipe", RECIPE_FILE)
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, source, restriction).shown
    period = f"periods[1]{LAYER_ID_ENDING}"
    drop = trellis.drop_edits(shown, dropped_event(shown, folder, PORT_ID, "template", period), {})
    assert drop.note.startswith("period.yml, stages: port written, periods 1–50; new: ")
    dropped = {
        Path(path).relative_to(copy.resolve()).as_posix(): text
        for path, text in drop.edits.items()
    }
    assert sorted(dropped) == [PERIOD_FILE, RECIPE_FILE]
    on_disk = {
        name: (copy / name).read_text(encoding="utf-8")
        for name in (RECIPE_FILE, PERIOD_FILE, TRELLIS_FILE)
    }
    writer, reader = "periods[1]/port", "periods[0]/tenure"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        add_stage = f"{period_node(1)} > .bf-layer > .bf-add-stage"
        wait_until(lambda: tab.locator(add_stage).count() == 1, 60.0, "+ stage of periods[1]")

        # the template `port` added to periods[1] through `+ stage`
        tab.click(".bl-zoom-button[data-zoom='fit']")
        tab.evaluate(TWO_FRAMES_JS)
        tab.click(add_stage)
        item = f'.bl-view-host .bf-stage-item[data-item="{PORT_ID}"]'
        tab.wait_for_selector(item, timeout=10_000)
        tab.click(item)
        wait_until(lambda: gesture_note(tab) == drop.note, 10.0, "the note of the drop")
        for relative, text in drop.new_files:
            wait_until(
                lambda relative=relative, text=text: (copy / relative).is_file()
                and (copy / relative).read_text(encoding="utf-8") == text,
                10.0,
                f"{relative} copied",
            )
        wait_until(
            lambda: {writer, "periods[2]/port"}
            <= occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "forward"),
            60.0,
            "port drawn in periods[1] and periods[2]",
        )

        # the reading the page now draws, as Python reads the same texts
        unsaved = unsaved_of(copy, dropped)
        texts = trellis.texts_of(unsaved)
        held = trellis.show_trellis(folder, source, restriction, unsaved=unsaved).shown
        m_next = field_port(held, "writing", (1, "port", "m_next"))["id"]
        a = field_port(held, "reading", (0, "tenure", "a"))["id"]
        records = {record["id"]: record for record in trellis.connectable_ports(held, texts)}
        assert (records[m_next]["set"], records[m_next]["pairs"]) == ("ℝ₊₊", {})
        wait_until(lambda: m_next in unjoined_field_ids(tab), 60.0, "m_next unjoined")
        reading = tab.evaluate(REGION_READING_JS)

        hold_events(tab, "connected")
        drag_frames(tab, writer, reader)
        listed, _ = wait_until(lambda: tab.evaluate(PAIR_LIST_JS), 10.0, "the list of pairs")
        assert listed == {
            "head": f"{writer} → {reader}",
            "rows": [["m_next : ℝ₊₊", False, "—", TENURE_OPTIONS]],
            "join": False,
        }
        assert tab.evaluate(PAIR_SET_COLOR_JS) == property_color(tab, "--bl-ice-3")
        widths = tab.evaluate(SELECT_WIDTHS_JS)
        assert all(given + 0.5 >= asked for given, asked in widths), widths
        tab.select_option(".bl-view-host .bf-pair-to", value=a)
        assert tab.evaluate(PAIR_LIST_JS)["rows"] == [
            ["m_next : ℝ₊₊", True, TENURE_OPTIONS[1], TENURE_OPTIONS]
        ]
        tab.click(".bl-view-host .bf-pair-join")
        assert tab.evaluate(PAIR_LIST_JS) is None
        event = {
            "source": writer + LAYER_ID_ENDING,
            "target": reader + LAYER_ID_ENDING,
            "pairs": [{"sourceHandle": m_next, "targetHandle": a}],
        }
        assert held_events(tab, "connected") == [{"reading": reading, **event}]
        join = trellis.connector_edit(
            held, {"reading": trellis.reading_record(folder, held), **event}, texts
        )
        # the note names, after the entry, the draft the package reports: the
        # route into `tenure` lacks `h` and `z` (unit N, Task 7)
        assert join.sentence is None and join.note.startswith(M_NEXT_TO_A + "; draft: "), join.note
        (typed,) = join.edits.values()
        release_events(tab, "connected")
        wait_until(lambda: gesture_note(tab) == join.note, 10.0, "the note of the join")
        wait_until(lambda: open_path_shown(tab) == TRELLIS_FILE, 30.0, "the trellis file open")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == typed, 10.0, "the entry typed")
        assert all(
            (copy / name).read_text(encoding="utf-8") == text for name, text in on_disk.items()
        )

        # what the package answers on the page's texts, printed in the one
        # place, the status line and the list under the error mark
        again = unsaved_of(copy, {**dropped, TRELLIS_FILE: typed})
        outcome = trellis.show_trellis(folder, source, restriction, unsaved=again)
        expected = error_sentences(folder, outcome)
        if outcome.refusal is None:
            print(f"task 24: the package reads the trellis; the list holds {expected}")
            wait_until(
                lambda: (ids := unjoined_field_ids(tab)) and m_next not in ids,
                60.0,
                "the trellis drawn with m_next joined",
            )
        else:
            print(f"task 24: the package refuses the reading: {expected}")
            wait_until(
                lambda: "refused" in status_text(tab).split(" · "),
                60.0,
                "the refusal in the status line",
            )
        line = status_text(tab).split(" · ")
        assert ("refused" in line) == (outcome.refusal is not None), line
        wait_until(
            lambda: sorted(sentence for sentence, _, _ in error_lines(tab)) == expected,
            30.0,
            "the package's answer under the error mark",
        )
    finally:
        context.close()


# The answers.yml Task 25's test gives its copy of the durables model, which
# the corpus's folder does not hold, so that the copy of a stage records its
# origin there, as in a folder `new trellis` wrote (spec 0.4 §3.5: no
# gesture writes answers.yml into a folder that has none)
DURABLES_ANSWERS = (
    "# the answers of the test's copy of the durables model\n"
    "stages: {}\n"
    "required:\n"
    "  slots: []\n"
    "  connectors: []\n"
)
# the folder of the portfolio model's stage folders, which Task 25's chooser
# lists, and the stage folder of `port`, which it copies
PORTFOLIO_STAGES = ROOT / "applications/portfolio-choice/declaration/stages"
PORT_STAGE_FOLDER = PORTFOLIO_STAGES / "port"
# the line of the form from a folder where the path names a folder that holds
# no stage file (unit L, Task 23; design pass 4 §3)
NO_STAGE_IN_FOLDER = "no stage file in this folder"
# the form "add stage" from a folder as the page draws it, null where no form
# "add stage" with its folder field is drawn: its heading, the field's path, the head of the
# chooser, the name of the folder it lists (unit L, Task 23), each entry of
# the chooser as its text and its path, the line that says why the path
# names no stage, null where it names one, the stage's row, null where none
# is printed, as its template, its key, the name of its model's folder, its
# parameters and its hover, which holds its model's title and the files it
# brings (unit L, Task 23; design pass 4 §3), the key field's value, and
# whether `add the stage` acts; the fields are VSCode Elements' text fields,
# whose value the element holds (design pass 8 §4; unit M, Task 6)
FOLDER_FORM_JS = """
() => {
  const form = document.querySelector('.bl-form[data-form="add stage"]');
  // the form's element can stand a moment before its folder field
  const field = form && form.querySelector('.bl-folder-path vscode-textfield');
  if (!field) return null;
  const row = form.querySelector('.bl-template');
  const text = (selector) => (row.querySelector(selector) || {}).textContent || null;
  return {
    heading: form.querySelector('h2').innerText,
    path: field.value,
    listed: (form.querySelector('.bl-form-list-head') || {}).textContent || null,
    entries: Array.from(form.querySelectorAll('.bl-folder-entry'),
      (entry) => [entry.textContent, entry.dataset.path]),
    reason: (form.querySelector('.bl-folder-reason') || {}).textContent || null,
    row: row && {
      template: row.dataset.template,
      name: text('.bl-template-name'),
      model: text('.bl-template-model'),
      calibration: text('.bl-template-calibration'),
      hover: row.querySelector('.bl-template-button').getAttribute('title'),
    },
    key: (form.querySelector('.bl-create-key vscode-textfield') || {}).value || null,
    acts: !form.querySelector('.bl-add-submit').disabled,
  };
}
"""
# the element of the form "add stage", which stands while the form is open
ADD_STAGE_FORM = '.bl-form[data-form="add stage"]'
# the last item of the stage list open: its words, its kind, whether it is
# .bf-stage-folder, and whether its words stand in the list's own face
LAST_STAGE_ITEM_JS = """
() => {
  const list = document.querySelector('.bl-view-host .bf-stage-list');
  const items = list ? list.querySelectorAll('.bf-stage-item') : [];
  const last = items[items.length - 1];
  if (!last) return null;
  const face = (element) => getComputedStyle(element).fontFamily;
  return [last.textContent, last.dataset.kind, last.classList.contains('bf-stage-folder'),
    face(last.querySelector('.bf-stage-key')) === face(list)];
}
"""


def test_task_25_a_stage_folder_of_the_disk_is_copied_into_a_period_with_its_origin(
    browser, server_on, scratch_durables
):
    """Task 25 (K-D26; spec 0.4 §3.5). On a copy of the durables model given
    an answers.yml, `periods 0–2`, its forward trellis graph shown: `+ stage`
    of periods[1] opens the list whose last item, after the templates, is
    `From a folder…`, in the list's face and not a key's, which the
    Workbench's drop answers with the form "add
    stage" on the folder that holds the model folder, the period's list
    `period.yml`. A click on it opens that form, headed `Add stage from a
    folder` (unit L, Task 23; design pass 4 §3; unit M, Task 6), its
    field on that folder, which holds no stage file, as one line says, the
    chooser headed by that folder's name and listing its entries. The
    corpus's folder of the portfolio model's stage folders typed in the
    field holds no stage file;
    its entry `port/` clicked in the chooser writes the stage folder's path,
    and the form prints `port`'s row as `folder_template` reads it, its key,
    its model's folder and its parameters, its hover the model's title, the
    parameters and `methods.yml` brought, and the key `port` proposed. `add
    the stage` copies `port.bl` and its methods file under
    `declaration/stages/port/` with the texts `add_stage` answers for that
    record, prints its note, and `port` is
    drawn in periods[1] and periods[2]; once the three files the tree marks
    unsaved are saved, the period file lists `port`, the recipe names the
    copy and never the origin, and answers.yml records the path as given
    and the SHA-256 of `port.bl` and `methods.yml`. Nothing is written in
    the corpus's stage folder or beside the model folder."""
    copy = scratch_durables
    (copy / creation.ANSWERS).write_text(DURABLES_ANSWERS, encoding="utf-8")
    folder = model.open_folder(copy)
    source = recipe.Source("recipe", RECIPE_FILE)
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, source, restriction).shown
    period = f"periods[1]{LAYER_ID_ENDING}"
    above = str(copy.resolve().parent)
    event = dropped_event(shown, folder, "folder", "folder", period)
    assert trellis.drop_edits(shown, event, {}) == {
        "form": "add stage",
        "fill": {"folder": above, "period": "period.yml", "entry": ""},
    }
    given = str(PORT_STAGE_FOLDER)
    record = creation.folder_template(given)
    added = creation.add_stage(copy, "port", record, "period.yml")
    assert [path for path, _ in added.new_files] == [
        "declaration/stages/port/port.bl",
        "declaration/stages/port/methods.yml",
    ]
    corpus_before = file_bytes(PORT_STAGE_FOLDER)
    beside_before = sorted(path.name for path in copy.parent.iterdir())
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        add_stage = f"{period_node(1)} > .bf-layer > .bf-add-stage"
        wait_until(lambda: tab.locator(add_stage).count() == 1, 60.0, "+ stage of periods[1]")
        tab.click(".bl-zoom-button[data-zoom='fit']")
        tab.evaluate(TWO_FRAMES_JS)

        # the list's last item, and the form it opens on the folder above
        tab.click(add_stage)
        listed, _ = wait_until(lambda: tab.evaluate(STAGE_LIST_JS), 10.0, "the stage list")
        assert listed["period"] == "periods[1]" and listed["items"][-1] == ["folder", False, None]
        assert tab.evaluate(LAST_STAGE_ITEM_JS) == ["From a folder…", "folder", True, True]
        tab.click('.bl-view-host .bf-stage-item[data-kind="folder"]')
        form, _ = wait_until(lambda: tab.evaluate(FOLDER_FORM_JS), 30.0, "the form add stage")
        assert form["heading"] == "Add stage from a folder"
        assert form["path"] == above and form["reason"] == NO_STAGE_IN_FOLDER
        assert form["listed"] == Path(above).name
        assert ["durables/", str(copy.resolve())] in form["entries"]
        assert (form["row"], form["acts"]) == (None, False)

        # the folder of the stage folders typed, then `port/` chosen
        field = ".bl-form .bl-folder-path input"
        tab.fill(field, str(PORTFOLIO_STAGES))
        tab.press(field, "Enter")
        # the field's text is the browser's at once, the chooser's head
        # Python's once it has read the path
        form, _ = wait_until(
            lambda: (shown_form := tab.evaluate(FOLDER_FORM_JS))["listed"] == "stages"
            and shown_form,
            10.0,
            "the stage folders listed",
        )
        assert form["reason"] == NO_STAGE_IN_FOLDER
        assert form["path"] == str(PORTFOLIO_STAGES)
        assert form["entries"] == [["..", str(PORTFOLIO_STAGES.parent)]] + [
            [f"{name}/", str(PORTFOLIO_STAGES / name)]
            for name in ("cons", "cons_obs", "disc", "noport", "port")
        ]
        tab.click(f'.bl-form .bl-folder-entry[data-path="{given}"]')
        form, _ = wait_until(
            lambda: (shown_form := tab.evaluate(FOLDER_FORM_JS))["acts"] and shown_form,
            30.0,
            "port's row chosen",
        )
        assert (form["path"], form["reason"]) == (given, None)
        assert form["entries"] == [
            ["..", str(PORTFOLIO_STAGES)],
            ["port.bl", str(PORT_STAGE_FOLDER / "port.bl")],
        ]
        assert form["row"] == {
            "template": given,
            "name": "port",
            "model": "portfolio-choice",
            "calibration": ", ".join(record.calibration),
            "hover": f"{record.model} · {', '.join(record.calibration)} · brings methods.yml",
        }
        assert form["key"] == "port"

        # the copy, its note, its drawing, and answers.yml once saved
        tab.click(".bl-form .bl-add-submit")
        # the notes of `add_stage`, then the joins the trellis gives the
        # stage, `port unconnected`, since the package pairs no field of
        # `port` with a field of the durables model's stages (unit N, Task 5,
        # `trellis.added_stage_joins`), as test_creation.py's notes now end
        note = "; ".join((*added.notes, "port unconnected"))
        # the page sets the note before it closes the form, so that both
        # are waited for (unit K's fix wave, item 13); FOLDER_FORM_JS answers
        # null wherever the folder field is not drawn, so the form's own
        # element is read as well, which the close takes away (N-I275)
        wait_until(
            lambda: gesture_note(tab) == note
            and tab.evaluate(FOLDER_FORM_JS) is None
            and tab.locator(ADD_STAGE_FORM).count() == 0,
            30.0,
            "the note of the copy and the form closed",
        )
        for relative, text in added.new_files:
            assert (copy / relative).read_text(encoding="utf-8") == text
        wait_until(
            lambda: {"periods[1]/port", "periods[2]/port"}
            <= occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "forward"),
            60.0,
            "port drawn in periods[1] and periods[2]",
        )
        edited = [creation.ANSWERS, PERIOD_FILE, RECIPE_FILE]
        wait_until(lambda: unsaved_in_tree(tab) == edited, 10.0, "the three files unsaved")
        assert save_unsaved_files(tab) == edited
        answers = (copy / creation.ANSWERS).read_text(encoding="utf-8")
        assert entry_value(answers, "stages.port") == {
            "origin": given,
            "sha256": {
                name: hashlib.sha256((PORT_STAGE_FOLDER / name).read_bytes()).hexdigest()
                for name in ("port.bl", "methods.yml")
            },
        }
        assert "port" in entry_value((copy / PERIOD_FILE).read_text(encoding="utf-8"), "stages")
        spec = (copy / RECIPE_FILE).read_text(encoding="utf-8")
        assert f"  port: {creation.recipe_row('port')}" in spec and given not in spec
        assert file_bytes(PORT_STAGE_FOLDER) == corpus_before
        assert sorted(path.name for path in copy.parent.iterdir()) == beside_before
    finally:
        context.close()


# The folder region's elements in which a slot or a count of slots could
# stand, read at one moment: each file row of the tree with the classes of
# its children; the checklist's head and the texts of its items, each a
# row (design pass 8 §6; unit M, Task 6); the text of the status line,
# visible and in the details; and each slot of the Recipe tab (unit M, Task
# 10), its select's value and whether it carries the refusal's mark.
SLOTS_SHOWN_JS = """
() => {
  const head = document.querySelector('.bl-error-mark');
  const chosen = (field) => {
    const option = field.querySelector('vscode-option[selected]');
    return option ? option.textContent.trim() : '';
  };
  return {
    rows: Array.from(document.querySelectorAll('.bl-tree-file'),
      (row) => Array.from(row.children, (child) => child.className)),
    head: head ? head.getAttribute('aria-label') : null,
    items: Array.from(document.querySelectorAll('.bl-checklist-list .bl-row'),
      (item) => item.textContent.trim()),
    status: document.querySelector('.bl-status').textContent,
    slots: Array.from(document.querySelectorAll('.bl-recipe-table .bl-recipe-entry .bl-field'))
      .filter((field) => chosen(field).startsWith('$'))
      .map((field) => [chosen(field), field.classList.contains('bl-refusal-mark')]),
    restSlots: Array.from(document.querySelectorAll('.bl-recipe-table .bl-recipe-slot'),
      (slot) => slot.textContent.trim()),
  };
}
"""


def test_task_26_a_slot_is_a_parameter_of_the_load_and_no_lack(
    browser, server_on, durables_folder
):
    """Task 26 (K-D28, K-D29; design pass 2 §11; the factory page, §3.3).
    The durables model's recipe, whose source lists write ten slots, opened
    in the trellis view: no file row of the tree holds a count beside its
    name and its mark; the checklist's head reads `1 binding refused` and
    its one item is the refused calibration of tenure, no slot line among
    them; the status line holds no part `to fill`; and every `$` entry of
    the recipe's Recipe tab (unit M, Task 10; design pass 9 §3) is a slot
    of a row at rest and, each row opened in turn (design pass 11 §2), a
    select that carries no refusal's mark, the four keywords `load_recipe`
    takes, `fill, tenure_method, keeper_method, adjuster_method`, among
    them."""
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(durables_folder), RECIPE_FILE)
        wait_until(lambda: slot_keywords(tab) == DURABLES_SLOT_KEYWORDS, 60.0, "the slots")
        found, _ = wait_until(
            lambda: (lambda drawn: drawn if drawn["head"] else None)(tab.evaluate(SLOTS_SHOWN_JS)),
            30.0,
            "the checklist's head",
        )
        print(f"task 26: the region's slots and counts: {found}")
        # each file row its empty twistie, its name and its mark (design
        # pass 8 §6; unit M, Task 6), and no count
        assert found["rows"] and all(
            classes == ["bl-twistie", "bl-tree-name", "bl-tree-mark"]
            or classes == ["bl-twistie", "bl-tree-name", "bl-tree-mark bl-dirty"]
            for classes in found["rows"]
        ), found["rows"]
        assert found["head"].startswith("Problems: 1 error,")
        assert checklist_count(tab) == 0
        assert found["items"] == []
        assert len(error_lines(tab)) == 1 and "stage 'tenure'" in error_lines(tab)[0][0]
        assert "to fill" not in found["status"]
        assert len(found["restSlots"]) == 10
        assert set(found["restSlots"]) == DURABLES_SLOTS_WRITTEN
        opened = with_each_recipe_row_open(tab, lambda tab: tab.evaluate(SLOTS_SHOWN_JS))
        slots = [slot for shown in opened.values() for slot in shown["slots"]]
        print(f"task 26: the slots' selects, each row opened in turn: {slots}")
        assert len(slots) == 10
        assert {text for text, _ in slots} == DURABLES_SLOTS_WRITTEN
        assert not any(marked for _, marked in slots), slots
    finally:
        context.close()


# The Recipe tab read at one moment (unit M, Task 10; design pass 9 §3): the
# panel under the editor's width; each element of the tab wider inside than
# its box, by its class, its text, its hover and the kind of the cell that
# holds it; each text of an element of the tab that ends in a full stop;
# whether the tab is drawn; the rows' keys; and the value of each select by
# its entry's address.
RECIPE_TAB_JS = """
() => {
  const panel = document.querySelector('.bl-classification[data-panel="recipe"]');
  const table = panel && panel.querySelector('.bl-recipe-table');
  const elements = table ? Array.from(table.querySelectorAll('*'))
    .filter((element) => !element.closest('vscode-single-select, vscode-textfield')) : [];
  const own = (element) => Array.from(element.childNodes)
    .filter((node) => node.nodeType === Node.TEXT_NODE)
    .map((node) => node.textContent).join('').trim();
  const chosen = (entry) => {
    const option = entry.querySelector('vscode-option[selected]');
    return option ? option.textContent.trim() : null;
  };
  return {
    width: panel ? panel.getBoundingClientRect().width : null,
    wider: elements.filter((element) => element.scrollWidth > element.clientWidth + 0.5
      && !element.classList.contains('bl-recipe-table'))
      .map((element) => {
        const cell = element.closest('[data-kind]');
        return [String(element.className), element.textContent.trim(),
                element.getAttribute('title'), cell ? cell.dataset.kind : null];
      }),
    stops: elements.map(own).filter((text) => text.endsWith('.')),
    drawn: table !== null && table.getClientRects().length > 0,
    keys: table ? Array.from(table.querySelectorAll('.bl-recipe-row'), (row) => row.dataset.stage)
      : [],
    values: table ? Object.fromEntries(Array.from(table.querySelectorAll('.bl-recipe-entry'),
      (entry) => [entry.dataset.address, chosen(entry)])) : {},
  };
}
"""
# The durables recipe's values as the Recipe tab prints them (unit M, Task
# 10; design pass 9 §3), by each entry's address: the trellis file, then for
# each stage its stage file and each entry of its lists, the kind's folder
# and the stage's own folder dropped
DURABLES_METHODS = ("tenure_method", "keeper_method", "adjuster_method")
DURABLES_VALUES = {
    "trellis": "trellis.yml",
    **{
        address: value
        for key, method in zip(DURABLES_KEYS, (*DURABLES_METHODS, None))
        for address, value in (
            (f"stages.{key}.stage", f"{key}.bl"),
            (f"stages.{key}.calibration.all[0]", "durables"),
            (f"stages.{key}.calibration.all[1]", "$fill"),
            *(
                ()
                if method is None
                else (
                    (f"stages.{key}.settings.all[0]", "durables"),
                    (f"stages.{key}.settings.all[1]", "$fill"),
                    (f"stages.{key}.methods.all[0]", "methods"),
                    (f"stages.{key}.methods.all[1]", f"${method}"),
                )
            ),
        )
    },
}


def cut(found: dict) -> list:
    """The elements RECIPE_TAB_JS reads as wider inside than their box but
    the stage file's name of a row at rest, which design pass 11 §2 cuts
    with an ellipsis where the key leaves it too little room, and whose
    hover holds it whole."""
    return [
        element
        for element in found["wider"]
        if element[:2] != ["bl-recipe-text bl-code-small", element[2]] or element[3] != "stage"
    ]


def test_task_27_the_recipe_is_a_fold_of_blocks_that_stand_whole_in_the_folder_column(
    browser, server_on, durables_folder
):
    """Task 27 (design pass 2 §11; K-D30), as unit M's Task 10 moves the
    recipe from the folder column to the panel under the editor (AAS,
    M-D17; design pass 9 §§2, 3 and 5). The durables model's recipe opened
    from the tree, at 1600 × 1000: the folder column holds no recipe, and
    the main bar names no occurrence until one is selected (unit N, Task
    1); the
    Recipe tab stands open in the text column, its rows the recipe's stages
    in the file's order, each value, each row opened in turn (design pass
    11 §2), as the recipe writes it less its kind's folder or the stage's
    own. No element of the tab is wider inside than its box, at rest or
    with a row open, but a stage file's name at rest, which is cut with an
    ellipsis and whole in its hover, and no text of it ends in a full stop.
    A click on the main
    bar's toggle `Inspector` folds the panel, which is then not drawn, and
    a second click opens it again (L-D12; unit N, Tasks 1 and 2). The
    variant `spec.two-stages.yml` opened from the tree shows its own tab,
    which stands whole as well."""
    context, tab = new_tab(browser)
    try:
        url = server_on(durables_folder)
        open_trellis(tab, url, RECIPE_FILE)
        assert tracks_near(tab, TRELLIS_TRACKS[1600, False])
        tab.wait_for_selector(".bl-recipe-table .bl-recipe-row", timeout=60_000)
        wait_until(lambda: slot_keywords(tab) == DURABLES_SLOT_KEYWORDS, 30.0, "the slots")
        found = tab.evaluate(RECIPE_TAB_JS)
        print(f"task 27: the Recipe tab at 1600 px: {found}")
        assert tab.locator(".bl-folder .bl-recipe-table, .bl-folder .bl-recipe").count() == 0
        assert recipe_head(tab) == ""
        assert (cut(found), found["stops"]) == ([], [])
        assert found["drawn"]
        assert found["keys"] == DURABLES_KEYS
        assert found["values"] == {"trellis": "trellis.yml"}
        # each row opened in turn, the others at rest (design pass 11 §2)
        opened = with_each_recipe_row_open(tab, lambda tab: tab.evaluate(RECIPE_TAB_JS))
        print(f"task 27: the rows opened in turn: {opened}")
        assert [(cut(drawn), drawn["stops"]) for drawn in opened.values()] == [([], [])] * 4
        values = {
            address: value
            for drawn in opened.values()
            for address, value in drawn["values"].items()
        }
        assert values == DURABLES_VALUES

        # the main bar's toggle `Inspector` folds the panel and opens it
        # again, the panel having no close button (unit N, Tasks 1 and 2;
        # design pass 10 §§3 and 4)
        toggle = tab.locator('.bl-main-bar .bl-fold[data-fold="inspector"]')
        toggle.click()
        wait_until(lambda: not tab.evaluate(RECIPE_TAB_JS)["drawn"], 5.0, "the recipe folded")
        assert toggle.get_attribute("aria-expanded") == "false"
        toggle.click()
        wait_until(lambda: tab.evaluate(RECIPE_TAB_JS)["drawn"], 5.0, "the recipe opened")
        assert toggle.get_attribute("aria-expanded") == "true"

        # the variant opened from the tree shows its own tab, whole
        open_trellis(tab, url, TWO_STAGES)
        variant, _ = wait_until(
            lambda: (lambda drawn: drawn if drawn["keys"] == DURABLES_KEYS[1:] else None)(
                tab.evaluate(RECIPE_TAB_JS)
            ),
            60.0,
            "the variant's tab",
        )
        print(f"task 27: the Recipe tab on the variant: {variant}")
        assert variant["values"]["trellis"] == "trellis.two-stages.yml"
        assert (cut(variant), variant["stops"]) == ([], [])
    finally:
        context.close()


# --- the fix wave of unit K (the final judgment of 8 October 2026, §6) ---

# Each row of the list that the move of a join wire's writing end opens,
# whose select chooses a writing port of the stage occurrence dropped on:
# the arrival field the row keeps, the id of the port its select holds,
# empty for none, and the ids of the ports its select offers; null where no
# list is open (unit K's decision K-D23).
WRITING_PAIR_ROWS_JS = """
() => {
  const list = document.querySelector('.bl-view-host .bf-pair-list');
  if (!list) return null;
  return Array.from(list.querySelectorAll('.bf-pair-row'), (row) => {
    const select = row.querySelector('select.bf-pair-from');
    return [row.querySelector('span.bf-pair-to').firstChild.textContent, select.value,
            Array.from(select.options, (option) => option.value)];
  });
}
"""
# the standing inter-period mapping of the durables model, and the same
# mapping with the adjuster's three entries taken out
DURABLES_MAPPING_LINE = (
    "  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}\n"
)
KEEPER_MAPPING_LINE = "  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z}\n"


def offered_elsewhere(rows: list) -> list:
    """The ports that the select of one row of WRITING_PAIR_ROWS_JS offers
    while another row holds them, each with the row's field."""
    return [
        (field, port)
        for i, (field, _, options) in enumerate(rows)
        for j, (_, port, _) in enumerate(rows)
        if j != i and port and port in options
    ]


def test_fix_item_12_a_writing_port_chosen_in_one_row_is_offered_in_no_other(
    browser, server_on, scratch_durables
):
    """Unit K's final judgment, §6 item 12 (K-D23; J-D41). On a copy of the
    durables model whose standing inter-period mapping keeps the keeper's
    three entries alone, so that `adjuster_cons`'s three continuation
    fields are unjoined before the terminal period, `periods 0–2`, the
    writing end of the wire from `keeper_cons` in periods[1] to `tenure` in
    periods[0] dropped on `adjuster_cons`'s writing port, the one port of
    its branch (design pass 10 §6), opens the cable's list of the move
    (§7), one row for each of `tenure`'s three arrival fields, each with a
    select of `adjuster_cons`'s continuation fields. No select offers a
    field another row holds, so that `join` cannot send one writing field
    for two pairs, which the package refuses as an old graph: `a_nxt_adj`
    chosen in the first row leaves the other two rows' selects, and the
    first row emptied offers it to them again. Escape closes the list and
    nothing is written."""
    trellis_path = scratch_durables / TRELLIS_FILE
    text = trellis_path.read_text(encoding="utf-8")
    assert text.count(DURABLES_MAPPING_LINE) == 1
    trellis_path.write_text(
        text.replace(DURABLES_MAPPING_LINE, KEEPER_MAPPING_LINE), encoding="utf-8"
    )
    edited = trellis_path.read_text(encoding="utf-8")
    folder = model.open_folder(scratch_durables)
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, recipe.Source("recipe", RECIPE_FILE), restriction).shown
    writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
    adjuster = {
        field: field_port(shown, "writing", (1, "adjuster_cons", field))["id"]
        for field in ("a_nxt_adj", "h_nxt_adj", "z_nxt_adj")
    }
    first = adjuster["a_nxt_adj"]
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_durables), RECIPE_FILE)
        assert restriction_shown(tab) == "periods 0–2"
        record_layouts(tab)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: (writer, reader) in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the join wires of the forward graph",
        )
        # the view at rest before the click, so that the opening's view does
        # not move the wire from under the pointer (as unit L's fix item 12)
        wait_until(lambda: view_still(tab, 1000), 30.0, "the forward graph at rest")
        click_join(tab, writer, reader)
        wait_until(
            lambda: [(w["from"], w["to"]) for w in join_wires_drawn(tab) if w["selected"]]
            == [(writer, reader)],
            10.0,
            "the join wire selected",
        )
        # the writing end dropped on `adjuster_cons`'s one writing port, since
        # design pass 10 §6 took the per-field port `a_nxt_adj` off the cards
        branch = cable_port(tab, "periods[1]/adjuster_cons", "writing")
        move_join_end(tab, writer, reader, "source", branch)
        rows, _ = wait_until(
            lambda: tab.evaluate(WRITING_PAIR_ROWS_JS), 10.0, "the list of the move"
        )
        print(f"fix item 12: the rows of the list as it opens: {rows}")
        assert [field for field, _, _ in rows] == ["a", "h", "z"]
        assert set(adjuster.values()) <= {port for _, _, options in rows for port in options}
        assert offered_elsewhere(rows) == []
        selects = tab.locator(".bl-view-host .bf-pair-row select.bf-pair-from")
        selects.nth(0).select_option(value=first)
        chosen, _ = wait_until(
            lambda: (lambda drawn: drawn if drawn[0][1] == first else None)(
                tab.evaluate(WRITING_PAIR_ROWS_JS)
            ),
            5.0,
            "the first row holding a_nxt_adj",
        )
        print(f"fix item 12: the rows with a_nxt_adj in the first: {chosen}")
        assert all(first not in options for _, _, options in chosen[1:])
        assert offered_elsewhere(chosen) == []
        selects.nth(0).select_option(value="")
        emptied, _ = wait_until(
            lambda: (lambda drawn: drawn if drawn[0][1] == "" else None)(
                tab.evaluate(WRITING_PAIR_ROWS_JS)
            ),
            5.0,
            "the first row emptied",
        )
        assert all(
            first in options for _, port, options in emptied[1:] if port != first
        ), emptied
        assert offered_elsewhere(emptied) == []
        # Escape pressed in the list, which closes it as the list's `×` does
        selects.nth(0).press("Escape")
        wait_until(
            lambda: tab.evaluate(WRITING_PAIR_ROWS_JS) is None, 5.0, "the list closed"
        )
        assert trellis_path.read_text(encoding="utf-8") == edited
    finally:
        context.close()
