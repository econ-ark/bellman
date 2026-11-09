"""The acceptance tests of unit J of model interface specification 0.4, the
gestures of the trellis graph, brief §4: one test for each of items 1 to 5;
item 6 is AAS's reading. Each test makes its gestures once in the browser,
on a copy of a model folder served by its own server. Deleted when the
next amendment is accepted (lean implementation rule, layer 2).
"""

from __future__ import annotations

import dataclasses
import json
import os
import platform
from pathlib import Path

from workbench_support import (
    BOX_DRAWN_JS,
    DEMO_STAGES,
    DOCUMENT_JS,
    GUTTER_MARKER_LINE_JS,
    HELD_COLLECTION_JS,
    LINT_RANGE_JS,
    NOPORT_ID,
    PORT_CONS,
    PORT_CONS_RECIPE,
    RECIPE_FILE,
    REGION_READING_JS,
    ROOT,
    SELECTABLE_WIRES_JS,
    SHARED_CONS,
    STARTING_PORTS_JS,
    TOOLTIP_TEXTS_JS,
    TWO_PORTS_JS,
    add_period_controls,
    applications_copy,
    cable_list,
    cable_port,
    cable_ports,
    checklist_count,
    choose_restriction,
    choose_view,
    click_join,
    click_line,
    click_toggle,
    connected_event,
    control_targets,
    controls_left_of,
    details_until,
    drag_cable,
    drag_ports,
    drop_by_keyboard,
    drop_item,
    durables_without_a,
    editor_selection,
    emptied_pension,
    emptied_port_cons,
    emptied_portfolio,
    emptied_portfolio_with_entry_connectors,
    error_lines,
    five_mappings_port_cons,
    gesture_note,
    held_events,
    held_graph_ids,
    held_joins,
    hold_events,
    join_wires_drawn,
    keyboard_place,
    line_text,
    move_join_end,
    lay_out_left_to_right,
    new_tab,
    occurrences_of,
    open_path_shown,
    open_stage_list,
    open_trellis,
    period_layers,
    property_color,
    release_events,
    restriction_shown,
    reveal_in_tree,
    trellis_settled,
    two_cons_one_joined,
    unjoined_field_ids,
    unsaved_in_tree,
    unsaved_of,
    wait_until,
    with_required_connectors,
)

from bellman.stage import LAYER_ID_ENDING, elaborate_stage, load_stage
from bellman.trellis import accrete, to_model_explorer, write_model_explorer
from bellman_workbench import creation, model, recipe, trellis

# the trellis of lesson 05 as the tab's source
LESSON = recipe.Source("recipe", PORT_CONS_RECIPE)
# the line of the connector of the trellis file of `emptied_port_cons`, which
# that copy empties to `- {}`, and of its inter-period mapping, also emptied
CONNECTOR_LINE = 15
MAPPING_LINE = 18
# three unjoined ports of the forward graph of `emptied_port_cons`: `port`'s
# continuation field `m_next` and `cons`'s arrival field `m` in `periods[2]`,
# and `cons`'s `m` in `periods[4]`
WRITING = "periods[2]/port/unjoined:port:cntn:m_next"
READING = "periods[2]/cons/unjoined:cons:arvl:m"
TWO_PERIODS_ON = "periods[4]/cons/unjoined:cons:arvl:m"
# two more: `disc`'s continuation field `a` in `periods[3]` and in
# `periods[2]`, and `port`'s arrival field `k` in `periods[2]`
LEAVING = "periods[3]/disc/unjoined:disc:cntn:a"
DISC_A = "periods[2]/disc/unjoined:disc:cntn:a"
ARRIVING = "periods[2]/port/unjoined:port:arvl:k"
# the status line of the drag from `WRITING` to `READING` on lesson 05's
# emptied trellis file (brief §5)
WITHIN_NOTE = (
    "trellis.port-cons.yml, periods[0].connectors[0]: {m_next: m} written, flat, periods 0–5"
)
# the status line of the removal of that connector (amendment 02, ruling 13)
REMOVED_NOTE = "trellis.port-cons.yml, periods[0].connectors[0]: {m_next: m} removed, periods 0–5"
# the keyed connector of `two_cons_one_joined`, from `port` to `cons_one`,
# and the one the move of its reading end to `cons_two`'s `m` types
TO_CONS_ONE = "{from: port, to: cons_one, fields: {m_next: m}}"
TO_CONS_TWO = "{from: port, to: cons_two, fields: {m_next: m}}"
# `cons_two`'s unjoined arrival port `m` in `periods[2]` of that copy
CONS_TWO_M = "periods[2]/cons_two/unjoined:cons:arvl:m"
# the sentence "An old graph" of brief §5 at a trellis file of lesson 05
OLD_GRAPH = (
    "{}: nothing was written. The graph was drawn from an earlier text. "
    "Drag again in the graph now drawn."
)
# the other trellis file of lesson 05 whose periods hold the same stage keys
VFI = "declaration/trellis.port-cons-vfi.yml"
# the portfolio model's trellis file and the period file its entry names
TRELLIS_FILE = "declaration/trellis.yml"
PERIOD_FILE = "declaration/period.yml"
# the arrival port of `cons` that a flat connector joins, in each period
CONS_ARRIVAL = "periods[{}]/cons/cons:measure:arvl"
# the arrival port of `port` that an inter-period entry joins, in each period
PORT_ARRIVAL = "periods[{}]/port/port:measure:arvl"
# the number of ports the region draws that a drag can start or end at
CONNECTABLE_JS = (
    "() => document.querySelectorAll('.bl-view-host .react-flow__handle.connectable').length"
)
# the number of ports the region draws
PORTS_JS = "() => document.querySelectorAll('.bl-view-host .react-flow__handle').length"
# the files of a folder `new trellis` wrote that item 5's gestures edit in
# their buffers and never on disk
NEW_TRELLIS_EDITED = (
    "answers.yml",
    "declaration/period.yml",
    "declaration/spec.yml",
    "declaration/trellis.yml",
)
# the files the template of `noport` brings, written to disk at its drop
NOPORT_FILES = (
    "declaration/stages/noport/noport.bl",
    "declaration/settings/noport.yml",
    "declaration/stages/noport/methods.bl",
)
# the status lines of item 5's three gestures that write (brief §5; ruling
# J-P21)
NOPORT_NOTE = (
    "period.yml, stages: noport written, periods 0–5; "
    "new: stages/noport/noport.bl, settings/noport.yml, stages/noport/methods.bl"
)
YOUNG_NOTE = (
    "trellis.yml, periods: {template: period.young.yml, repeat: 1} written, periods 6; "
    "new: period.young.yml"
)
MID_NOTE = (
    "trellis.yml, periods: repeat 6 split 3, period.mid.yml, 3; new: period.mid.yml; "
    "restriction periods 2–4"
)
# the heading of the stage list of a trellis written as records (brief §5),
# in sentence case since design pass 13 §3
RECORDS_HEADING = "This folder's stages"
# the drag on the corpus's largest trellis, `durables_without_a` (decision
# J-D8): from `keeper_cons`'s unjoined `a_nxt_kp` in periods[2] to
# `tenure`'s unjoined `a` in periods[1], the next period in time
KEEPER_A = "periods[2]/keeper_cons/unjoined:keeper_cons:cntn:a_nxt_kp"
TENURE_A = "periods[1]/tenure/unjoined:tenure:arvl:a"
# `adjuster_cons`'s `a_nxt_adj` in periods[2], the second branch, which the
# drag leaves unjoined
ADJUSTER_A = "periods[2]/adjuster_cons/unjoined:adjuster_cons:cntn:a_nxt_adj"
# the standing inter-period mapping of that copy before and after the drag
WITHOUT_A = "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z}"
WITH_A = "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z, a_nxt_kp: a}"
# the status line of that drag (brief §5): the cable from `keeper_cons`'s
# branch to `tenure`, which `h` and `z` join already, is moved whole onto
# its own destination, its list keeping those two pairs and adding
# `a_nxt_kp → a`, and the note of a cable's write names no form (unit N,
# Task 7; design pass 10 §7); after it the note names the draft the package
# reports while the second branch's `a_nxt_adj` is paired to no arrival
# field, the route from `adjuster_cons` to `tenure` not certified (N-I184)
DURABLES_NOTE = "trellis.yml, inter_connectors[0]: a_nxt_kp: a written, periods 0–50"
DURABLES_DRAFT = "; draft: the route periods[1].adjuster_cons → periods[0].tenure is not certified"
# `tenure`'s arrival port `a` in periods[1] once the drag's entry reaches it,
# which then takes the second branch's `a_nxt_adj` as a further source
# (decisions J-D41 and J-D42), the mapping after that drag and its note
TENURE_A_JOINED = "periods[1]/tenure/joined:tenure:arvl:a"
WITH_BOTH = "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z, a_nxt_kp: a, a_nxt_adj: a}"
BRANCH_NOTE = "trellis.yml, inter_connectors[0]: a_nxt_adj: a written, periods 0–50"
# Records three times on the page's clock for a drag: `connected`, when the
# event `event`, `connected` or `moved`, leaves the region; `drawn`, when
# the region first reports a layout after it whose collection no longer
# holds the port `joined` and still holds the port `kept`, the trellis drawn
# again from the typed line; and `opened`, when the editor first shows the
# file `file` with a selected text and the cursor on line `line` (decision
# J-D40).
DRAG_TIMES_JS = """
([joined, kept, file, line, event]) => {
  const times = {connected: null, drawn: null, opened: null};
  window.dragTimes = times;
  document.addEventListener(event, () => {
    if (times.connected === null) times.connected = performance.now();
  }, true);
  document.addEventListener('processed', (event) => {
    const host = event.target;
    if (!host.classList || !host.classList.contains('bl-view-host')) return;
    if (times.connected === null || times.drawn !== null || !host.bellmanFlow) return;
    const held = JSON.stringify(host.bellmanFlow.collection());
    if (!held.includes(joined) && held.includes(kept)) times.drawn = performance.now();
  }, true);
  const observer = new MutationObserver(() => {
    if (times.connected === null || times.opened !== null) return;
    const name = document.querySelector('.bl-file-name');
    const gutter = document.querySelector('.bl-editor .cm-activeLineGutter');
    const selected = document.querySelector('.bl-editor .cm-selectionBackground');
    if (name && name.dataset.path === file && selected && gutter &&
        gutter.textContent === String(line)) {
      times.opened = performance.now();
      observer.disconnect();
    }
  });
  observer.observe(document.body,
    {subtree: true, childList: true, characterData: true, attributes: true});
}
"""
# the three times `DRAG_TIMES_JS` records, once all three stand; null before
DRAG_TIMES_HELD_JS = """
() => {
  const times = window.dragTimes;
  return times && times.connected !== null && times.drawn !== null && times.opened !== null
    ? times : null;
}
"""
# item 4's copy `emptied_pension`: the occurrence `retiree_saving` in
# periods[2], whose two continuation states no join reads, and its two
# unjoined continuation ports, each named by its field
RETIREE = "periods[2]/retiree_saving"
Y_F_RET = "periods[2]/retiree_saving/unjoined:retiree_saving:cntn:y_f_ret"
Y_P_RET = "periods[2]/retiree_saving/unjoined:retiree_saving:cntn:y_p_ret"
# `retiree_saving`'s unjoined arrival ports in periods[1], the next period in
# time, at which the two entries arrive
Y_F_R = "periods[1]/retiree_saving/unjoined:retiree_saving:arvl:y_f_r"
Y_P_R = "periods[1]/retiree_saving/unjoined:retiree_saving:arvl:y_p_r"
# The unjoined ports of the forward graph of the whole trellis of
# `emptied_pension`, the two ends counted, computed once from the package's
# `joins.unjoined_fields`: in each of the 15 periods the arrival fields
# `y_f_w` and `y_p_w` of `worker_saving` and `y_f_r` and `y_p_r` of
# `retiree_saving`, 60, those of periods[14] being the earliest end; and in
# each of periods 1 to 14 the continuation fields `y_f_wk`, `y_p_wk`, `y_f_rt`
# and `y_p_rt` of `retire_choice` and `y_f_ret` and `y_p_ret` of
# `retiree_saving`, 84. At the terminal end the terminal period's connector
# joins those six fields to the terminal stage, which declares no
# continuation state.
PENSION_UNJOINED = 144
# The unjoined fields the status line counts, by the checklist's rule (unit
# L, Task 21): the four arrival fields `y_f_w`, `y_p_w`, `y_f_r` and `y_p_r`,
# each unjoined at periods 0 to 13, counted once for its stage and field;
# each of the two entries joins one of them, `retiree_saving`'s `y_f_r` and
# then its `y_p_r`.
PENSION_FIELDS_UNJOINED = 4
# the two drags of item 4, each as its writing port, its reading port, the
# line of the inter-period mapping after it and the entry it adds
PENSION_DRAGS = (
    (Y_F_RET, Y_F_R, "  - {y_f_ret: y_f_r}", "y_f_ret: y_f_r"),
    (Y_P_RET, Y_P_R, "  - {y_f_ret: y_f_r, y_p_ret: y_p_r}", "y_p_ret: y_p_r"),
)
# the stage files lesson 05 constructs for its trellis `two`, by key
LESSON_STAGES = {
    key: f"applications/portfolio-choice/declaration/stages/{key}/{key}.bl"
    for key in ("port", "cons", "disc")
}


def occurrence_at(box: str) -> tuple[int, str]:
    """The position `(h, key)` of the stage occurrence whose card's node has
    the id `box`, `periods[2]/cons` followed by the layer ending."""
    address = box[: -len(LAYER_ID_ENDING)] if box.endswith(LAYER_ID_ENDING) else box
    period, key = address.split("/", 1)
    return int(period[len("periods[") : -1]), key


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


def test_item_1_a_drag_within_a_period_types_the_flat_connector_into_the_entry_the_package_names(
    browser, server_on, tmp_path
):
    """Item 1 (spec 0.4 §8 J (1)): the region's part (spec 0.4 §§3.2 to
    3.4; brief §5; unit J's plan, Task 9), then the line typed and drawn
    (spec 0.4 §§3.1, 3.3; brief rules 6 and 7; Task 10), the drag made
    through the cables' ports and the cable's list since unit N's Task 7
    (design pass 10 §§6 and 7). In the copy `emptied_port_cons`, its
    trellis file opened. In the backward graph no port starts a drag and
    the region holds no record of a reading. In the forward graph the
    fields the cards' ports name as unjoined are those
    `trellis.unjoined_ports` answers; a drag starts at a branch port whose
    branch holds an unjoined field or which a cable leaves, and at an
    arrival port one cable reaches, not at a port of the card's own for an
    arrival tuple no cable reaches (design pass 10 §7); and the region holds
    the record `trellis.reading_record` gives, with the number of the
    elaboration drawn. With the event `connected` held back, a drag from
    `port`'s branch port to `cons`'s arrival port in `periods[2]` draws its
    line in ultramarine-light, marks the region, the arrival ports that
    would take it, among those drawn, and the arrival port as a valid end
    while the button is held, and opens the cable's list, whose one row,
    `m`, takes `m_next`; `join` sends one event whose detail holds the
    region's record, the two occurrences and the pair of the two ports'
    ids in the graph JSON, marked as the whole cable's; a drag to `cons`'s
    arrival port in `periods[4]` draws its line, marks no valid end, opens
    no list and sends nothing. With the occurrence `periods[2]/port`
    closed, its card keeps the two cable ports, which name its two unjoined
    fields, and the same drag sends the same event. One character typed
    into the open trellis file takes every port a drag starts at away
    before the editor's change event, and the reading of the typed text
    restores them under a new elaboration's number. The two events held,
    sent then, name the earlier elaboration: the list under the error mark
    holds the sentence "An old graph" and nothing is typed. The same drag,
    not held, types the flat connector into the trellis file's connector;
    the tree and the title mark the file `unsaved`, the status line reads
    the note of §5, the trellis is drawn again from the buffer with the join
    on its wire in every period, and the file on disk is unchanged. In a
    stage's graph and in an initial diagram no port is connectable and the
    region holds no record. In the portfolio model, whose trellis entry
    names the period file, the drag made with the recipe open types the
    connector into the closed period file's buffer, which the tree marks
    `unsaved` and whose title does so once it is opened; where the entry
    writes its own `connectors`, the drag made with the trellis file open
    types it there. In each, the join stands on its wire in every period and
    the note names the file and the address; in the period file the drag
    opened, one undo leaves the text the drag made, since the opening
    begins the file's own undo history (R-D45). Each portfolio copy's
    answers.yml requires the connector and the inter-period mapping: the
    checklist's count falls from two to one, the mapping's entry standing.
    Then the removal and the move of a join (unit J, Task 19; decisions
    J-D33, J-D34, J-D39 and J-D40): a click on the join wire within
    `periods[2]` selects it, drawn in ultramarine-light, and Details names
    the join, its two stage occurrences and the line that writes it, the
    rows `trellis.join_rows` answers, the route, its status and its wires
    first (design pass 10 §8), with the button `remove`; Backspace, the
    focus in the region, takes the connector out, `- {}` left, the status
    line names the removal, the trellis is drawn with the two fields
    unjoined again in every period and is not refused, the status line
    counts the unjoined fields by the checklist's rule, `2 unjoined internal entry fields`,
    the arrival fields m of cons and k of port outside the earliest period,
    the inter-period mapping standing emptied (unit L, Task 21), and the
    open file shows the line selected; the editor's undo types the
    connector again, and the button `remove` takes it out once more. The
    join `a` by equal names from `cons` to `disc`, which no entry writes, is
    a join wire too (unit L, Task 15): a click selects it, Details prints
    `joined by the names` under `written` and offers `rename` and no
    `remove`, and Backspace removes nothing. In the copy
    `two_cons_one_joined`, the reading end of the keyed connector's wire
    within `periods[2]`, dragged from `cons_one` to `cons_two`'s arrival
    port, whose one field `m` is unjoined, replaces the connector by the one
    to `cons_two` in one edit, which the editor's undo takes back whole.
    Last, the time on the corpus's largest trellis (unit J's plan, Task 16;
    decision J-D8): in the copy `durables_without_a`, its recipe opened and
    its forward graph restricted as the folder opens, `periods 0–2`, the
    drag from `keeper_cons`'s branch port in `periods[2]`, which `h` and `z`
    join to `tenure` in `periods[1]` already, to `tenure`'s arrival port is
    the move of that cable onto its own destination: its list keeps the two
    pairs and takes `a_nxt_kp` for `a`, and `join` adds `a_nxt_kp: a` to the
    standing inter-period mapping of the closed trellis file, whose line
    the editor then shows selected (J-D40), and `adjuster_cons`'s
    `a_nxt_adj`, the second branch, stays unjoined, the note naming the
    draft the package reports for that branch's route; the same drag from
    `adjuster_cons`'s branch port adds `a_nxt_adj: a` to the same mapping,
    `tenure`'s `a`, which the entry reaches, taking a further source
    (decisions J-D41 and J-D42). The seconds on the page's clock from the
    event `moved` to the first layout of the trellis drawn again, and to
    the trellis file open at the typed line, are printed with the machine;
    no bound is asserted, since the specification states none."""
    copy = emptied_port_cons(tmp_path / "port-cons")
    on_disk = (copy / PORT_CONS).read_text(encoding="utf-8")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    ports = {port["id"]: port for port in trellis.unjoined_ports(shown, {})}
    assert {WRITING, READING, TWO_PERIODS_ON} <= set(ports)
    # the ports a drag can take: the unjoined ports, the reading ports that
    # joins reach, `disc`'s `a` in every period (J-D41), and the joined
    # continuation fields, `cons`'s `a`, which a cable's list offers (unit
    # N, Task 7)
    connectable = {port["id"]: port for port in trellis.connectable_ports(shown, {})}
    assert connectable.keys() - ports.keys() == {
        f"periods[{h}]/disc/joined:disc:arvl:a" for h in range(6)
    } | {f"periods[{h}]/cons/joined:cons:cntn:a" for h in range(6)}
    record = trellis.reading_record(folder, shown)
    # the join of the flat connector, on `cons`'s arrival port in every period
    joined = {CONS_ARRIVAL.format(h): "m_next → m" for h in range(6)}
    # the rows Details prints for the join the drag writes, read from the
    # text the drag types (design pass 10 §8; unit N, Task 7)
    lines = on_disk.split("\n")
    assert lines[CONNECTOR_LINE - 1] == "      - {}"
    lines[CONNECTOR_LINE - 1] = "      - {m_next: m}"
    with_join = trellis.show_trellis(
        folder, LESSON, previous=shown, unsaved=unsaved_of(copy, {PORT_CONS: "\n".join(lines)})
    ).shown
    within = ("periods[2]/port", "periods[2]/cons")
    wire = {(w["from"], w["to"]): w for w in trellis.join_wires(with_join)}[within]
    rows = trellis.join_rows(folder, with_join, wire).rows
    card = [(label, [trellis.line_text(line) for line in items]) for label, items in rows]
    assert [label for label, _ in card][:3] == ["route", "status", "wires"], card
    assert ("written", ["declaration/trellis.port-cons.yml · periods[0].connectors[0]"]) in card
    assert ("periods", ["0–5"]) in card and ("measure", ["μ≻", "→ μ≺"]) in card
    assert ("fields", ["m_next → m ℝ₊₊ → Xm"]) in card
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PORT_CONS)
        assert tab.evaluate(PORTS_JS) > 0
        assert tab.evaluate(STARTING_PORTS_JS) == 0
        assert tab.evaluate(REGION_READING_JS) is None

        choose_view(tab, None, "forward")
        wait_until(
            lambda: unjoined_field_ids(tab) == sorted(ports), 30.0, "the forward graph's ports"
        )
        # the ports a drag starts at (design pass 10 §7): a branch port that
        # holds an unjoined field or that a cable leaves, and an arrival
        # port one cable reaches, `disc`'s from `cons` in every period; a
        # port of the card's own for an arrival tuple no cable reaches, and
        # no port of the stage-view graphs, starts none
        drawn = [port for port in cable_ports(tab) if not port["hidden"]]
        assert drawn and tab.evaluate(STARTING_PORTS_JS) == sum(port["starts"] for port in drawn)
        for port in drawn:
            starts = port["joined"] or bool(port["unjoined"]) if port["side"] == "writing" else port["joined"]
            assert port["starts"] == starts, port
        light = property_color(tab, "--bl-ultramarine-light")
        reading = tab.evaluate(REGION_READING_JS)
        assert {key: reading[key] for key in ("source", "graph", "inputs")} == {
            key: record[key] for key in ("source", "graph", "inputs")
        }
        assert isinstance(reading["number"], int)

        # the arrival ports a drag from `port`'s branch port in periods[2]
        # can end at: another stage occurrence's in `periods[2]` and every
        # one in `periods[1]` (design pass 10 §7)
        takes = {
            port["port"]
            for port in drawn
            if port["side"] == "reading"
            and occurrence_at(port["box"]) != (2, "port")
            and occurrence_at(port["box"])[0] in (1, 2)
        }
        port_out = cable_port(tab, "periods[2]/port", "writing")
        cons_in = cable_port(tab, "periods[2]/cons", "reading")
        hold_events(tab, "connected")
        state = drag_cable(tab, "periods[2]/port", "", "periods[2]/cons", {READING: WRITING})
        admitted = state.pop("admitted")
        # a cable drag marks the ports that would take it and the valid end,
        # and no period layer, which the field drag of unit J marked
        assert (state["connecting"], state["line"], state["valid"]) == (True, light, [cons_in]), state
        assert cons_in in admitted and set(admitted) <= takes, (admitted, takes)
        event = {
            "reading": reading,
            "source": f"periods[2]/port{LAYER_ID_ENDING}",
            "target": f"periods[2]/cons{LAYER_ID_ENDING}",
            "pairs": [{"sourceHandle": WRITING, "targetHandle": READING}],
            "cable": True,
        }
        assert held_events(tab, "connected") == [event]
        two_on = cable_port(tab, "periods[4]/cons", "reading")
        state = drag_ports(tab, port_out, two_on)
        admitted = state.pop("admitted")
        assert (state["connecting"], state["line"], state["valid"]) == (True, light, []), state
        assert two_on not in admitted and set(admitted) <= takes, (admitted, takes)
        assert cable_list(tab) is None
        assert held_events(tab, "connected") == [event]

        # the closed occurrence's card keeps the cable ports, which name
        # its unjoined fields (design pass 10 §6)
        closed = f"periods[2]/port{LAYER_ID_ENDING}"
        # the toggle reached as a reader reaches it, the view enlarged over
        # it, since the card's branch port, which the pointer near it gives
        # the pointer, stands over the toggle at the scale the drag left
        click_toggle(tab, closed)
        own = sorted(port for port in ports if port.startswith("periods[2]/port/"))
        wait_until(lambda: unjoined_on_card(tab, closed) == own, 10.0, "the closed occurrence's ports")
        assert unjoined_field_ids(tab) == sorted(ports)
        drag_cable(tab, "periods[2]/port", "", "periods[2]/cons", {READING: WRITING})
        assert held_events(tab, "connected") == [event, event]

        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+End")
        tab.keyboard.type("#")
        wait_until(lambda: tab.evaluate(STARTING_PORTS_JS) == 0, 0.6, "the ports taken away")
        assert tab.locator(".bl-file .bl-modified").count() == 0
        wait_until(
            lambda: tab.locator(".bl-file .bl-modified").count() == 1, 10.0, "the change event"
        )
        wait_until(
            lambda: unjoined_field_ids(tab) == sorted(ports) and tab.evaluate(STARTING_PORTS_JS) > 0,
            60.0,
            "the ports of the typed text",
        )
        assert tab.evaluate(REGION_READING_JS)["number"] > reading["number"]

        # the two events held, sent after the reading of the typed text: each
        # names an earlier elaboration, so nothing is written
        assert release_events(tab, "connected") == [event, event]
        assert held_events(tab, "connected") == []
        old = (OLD_GRAPH.format("trellis.port-cons.yml"), PORT_CONS, None)
        wait_until(lambda: old in error_lines(tab), 10.0, "the sentence of an old graph")
        assert line_text(tab, CONNECTOR_LINE) == "      - {}"

        # the drag types the flat connector into the open trellis file
        drag_cable(tab, "periods[2]/port", "", "periods[2]/cons", {READING: WRITING})
        wait_until(
            lambda: line_text(tab, CONNECTOR_LINE) == "      - {m_next: m}", 10.0, "the line typed"
        )
        wait_until(lambda: gesture_note(tab) == WITHIN_NOTE, 10.0, "the status line's note")
        wait_until(
            lambda: joined.items() <= held_joins(tab).items(), 60.0, "the join in every period"
        )
        assert old not in error_lines(tab)
        assert unsaved_in_tree(tab) == [PORT_CONS]
        assert tab.locator(".bl-file .bl-modified").count() == 1
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == on_disk

        # the join wire selected by a click, drawn in ultramarine-light and
        # named in Details; no other wire is selectable than the six the
        # connector writes and the six of the join `a` by equal names from
        # `cons` to `disc`, a join wire too (unit L, Task 15)
        by_names = {(f"periods[{h}]/cons", f"periods[{h}]/disc") for h in range(6)}
        wires = {(wire["from"], wire["to"]) for wire in join_wires_drawn(tab)}
        assert within in wires and by_names <= wires and len(wires) == 12
        assert tab.evaluate(SELECTABLE_WIRES_JS) == len(wires)
        click_join(tab, *within)
        wait_until(
            lambda: [w for w in join_wires_drawn(tab) if w["selected"]]
            == [{"from": within[0], "to": within[1], "selected": True, "stroke": light}],
            10.0,
            "the join wire selected",
        )
        details = tab.locator(".bl-join-details")
        wait_until(lambda: details.count() == 1, 10.0, "the join in Details")
        # the card of unit K's Task 4 (design pass §2, "A join wire") after
        # the route, its status and its wires (design pass 10 §8): the two
        # occurrences in the head, the entry typed, the periods its list
        # reaches, the two measures and the table of the one join, whose two
        # fields the files declare in two sets
        head = "join periods[2]/port → periods[2]/cons forward"
        details_until(tab, (head, card), "the join's rows in Details")
        link = details.locator(".bl-link", has_text="periods[0].connectors[0]").first
        assert (link.inner_text(), link.get_attribute("data-line")) == (
            "declaration/trellis.port-cons.yml · periods[0].connectors[0]",
            str(CONNECTOR_LINE),
        )
        button = details.locator(".bl-join-remove")
        assert button.get_attribute("title") == "Remove the join from trellis.port-cons.yml"

        # Backspace, the focus in the region, removes it; the trellis left
        # with the fields unjoined is drawn and not refused
        tab.keyboard.press("Backspace")
        wait_until(
            lambda: line_text(tab, CONNECTOR_LINE) == "      - {}", 10.0, "the line removed"
        )
        wait_until(lambda: gesture_note(tab) == REMOVED_NOTE, 10.0, "the removal's note")
        wait_until(
            lambda: unjoined_field_ids(tab) == sorted(ports), 60.0, "the fields unjoined again"
        )
        assert not joined.items() <= held_joins(tab).items()
        assert error_lines(tab) == [] and tab.locator(".bl-view-host.bl-stale").count() == 0
        assert trellis.unjoined_count(shown) == 2
        wait_until(
            lambda: " · 2 unjoined internal entry fields" in (trellis_settled(tab, PORT_CONS) or ""),
            10.0,
            "the status line's count of unjoined fields",
        )
        assert editor_selection(tab) == {"selected": True, "line": str(CONNECTOR_LINE)}
        assert details.count() == 0

        # the editor's undo types the connector again; the button `remove`
        # takes it out once more
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(
            lambda: line_text(tab, CONNECTOR_LINE) == "      - {m_next: m}", 10.0, "the undo"
        )
        wait_until(lambda: joined.items() <= held_joins(tab).items(), 60.0, "the join drawn again")
        click_join(tab, *within)
        wait_until(lambda: details.count() == 1, 10.0, "the join in Details again")
        details.locator(".bl-join-remove").click()
        wait_until(lambda: line_text(tab, CONNECTOR_LINE) == "      - {}", 10.0, "removed again")
        wait_until(lambda: gesture_note(tab) == REMOVED_NOTE, 10.0, "the note again")
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == on_disk

        # the join `a` by equal names within `periods[2]`, selected by a click,
        # is drawn and named in Details as any join wire; Details prints
        # `joined by the names` under `written` and offers `rename` and no
        # `remove`, and Backspace removes nothing (unit L, Task 15; J-D33 and
        # J-D39 extended to joins by equal names)
        names = ("periods[2]/cons", "periods[2]/disc")
        wire = {(w["from"], w["to"]): w for w in trellis.join_wires(shown)}[names]
        rows = trellis.join_rows(folder, shown, wire).rows
        card = [(label, [trellis.line_text(line) for line in lines]) for label, lines in rows]
        assert ("written", ["joined by the names"]) in card, card
        # the join wires return once the removal's text is read
        wait_until(
            lambda: names in {(w["from"], w["to"]) for w in join_wires_drawn(tab)},
            60.0,
            "the join wires of the text read",
        )
        click_join(tab, *names)
        wait_until(
            lambda: [w for w in join_wires_drawn(tab) if w["selected"]]
            == [{"from": names[0], "to": names[1], "selected": True, "stroke": light}],
            10.0,
            "the join by equal names selected",
        )
        details_until(tab, (f"join {names[0]} → {names[1]} forward", card), "its rows")
        assert details.locator(".bl-join-remove").count() == 0
        assert details.locator(".bl-join-rename").count() == 1
        document = tab.evaluate(DOCUMENT_JS)
        tab.keyboard.press("Backspace")
        tab.wait_for_timeout(300)
        assert tab.evaluate(DOCUMENT_JS) == document and gesture_note(tab) == REMOVED_NOTE

        occurrence = f'.bl-view-host .react-flow__node[data-id="periods[1]/cons{LAYER_ID_ENDING}"]'
        # the drag left the view enlarged about its last port
        tab.click(".bl-zoom-button[data-zoom='fit']")
        tab.dblclick(f"{occurrence} .bf-layer-name")
        wait_until(
            lambda: open_path_shown(tab) == SHARED_CONS
            and "forward initial diagram" in held_graph_ids(tab),
            60.0,
            "the occurrence's stage",
        )
        for kind, graph in (
            ("operator", "forward"),
            ("initial", "forward initial diagram"),
        ):
            choose_view(tab, kind, "forward")
            wait_until(
                lambda graph=graph: tab.locator(f'.bl-graph-bar[data-graph="{graph}"]').count()
                == 1
                and tab.evaluate(PORTS_JS) > 0,
                30.0,
                f"the stage's {graph} graph",
            )
            assert tab.evaluate(CONNECTABLE_JS) == 0
            assert tab.evaluate(REGION_READING_JS) is None
    finally:
        context.close()

    # the portfolio model: the drag with the recipe open fills the closed
    # period file's connector; where the trellis entry writes its own
    # connectors, the drag with the trellis file open fills them; each
    # copy's answers.yml requires that connector and the inter-period
    # mapping, which stands at line 10 of the trellis file
    for made, opened, written, address, line, typed in (
        (emptied_portfolio, RECIPE_FILE, PERIOD_FILE, "connectors[0]", 14, "  - {m_next: m}"),
        (
            emptied_portfolio_with_entry_connectors,
            TRELLIS_FILE,
            TRELLIS_FILE,
            "periods[0].connectors[0]",
            8,
            "  - {template: period.yml, repeat: 6, connectors: [{m_next: m}]}",
        ),
    ):
        required = [(written, address), (TRELLIS_FILE, "inter_connectors[0]")]
        model_copy = with_required_connectors(made(tmp_path / made.__name__), required)
        before = (model_copy / written).read_text(encoding="utf-8")
        context, tab = new_tab(browser)
        try:
            open_trellis(tab, server_on(model_copy), RECIPE_FILE)
            wait_until(lambda: checklist_count(tab) == 2, 10.0, "the two required connectors")
            if opened != RECIPE_FILE:
                reveal_in_tree(tab, opened)
                tab.click(f'.bl-tree-file[data-path="{opened}"]')
                wait_until(
                    lambda opened=opened: open_path_shown(tab) == opened,
                    30.0,
                    f"{opened} open",
                )
            choose_view(tab, None, "forward")
            wait_until(
                lambda: WRITING in unjoined_field_ids(tab), 30.0, "the forward graph's ports"
            )
            drag_cable(tab, "periods[2]/port", "", "periods[2]/cons", {READING: WRITING})
            note = f"{Path(written).name}, {address}: {{m_next: m}} written, flat, periods 0–5"
            wait_until(lambda note=note: gesture_note(tab) == note, 10.0, "the status line's note")
            wait_until(
                lambda: joined.items() <= held_joins(tab).items(), 60.0, "the join in every period"
            )
            wait_until(lambda: checklist_count(tab) == 1, 10.0, "the checklist's count fallen")
            entry = tab.locator(".bl-checklist-entry")
            assert (entry.get_attribute("data-file"), entry.get_attribute("data-line")) == (
                TRELLIS_FILE,
                "10",
            )
            assert unsaved_in_tree(tab) == [written]
            # the file the drag wrote opens at the line it typed, selected
            # (J-D40), whether the recipe or that file was open
            wait_until(
                lambda written=written: open_path_shown(tab) == written,
                30.0,
                f"{written} open",
            )
            assert tab.locator(".bl-file .bl-modified").count() == 1
            assert line_text(tab, line) == typed
            assert editor_selection(tab) == {"selected": True, "line": str(line)}
            assert (model_copy / written).read_text(encoding="utf-8") == before
            if opened != written:
                # one undo in the file the drag opened leaves the text the drag
                # made, at once and after the editor's pause: the opening
                # begins the file's own undo history (R-D45; unit J's plan,
                # Task 21)
                made = tab.evaluate(DOCUMENT_JS)
                click_line(tab, 1)
                tab.keyboard.press("ControlOrMeta+z")
                assert tab.evaluate(DOCUMENT_JS) == made
                tab.wait_for_timeout(1_000)
                assert tab.evaluate(DOCUMENT_JS) == made and line_text(tab, line) == typed
                assert open_path_shown(tab) == written
        finally:
            context.close()

    # the move of the reading end of the keyed connector's wire within
    # `periods[2]`, from `cons_one` to `cons_two`'s unjoined `m`: one edit
    two = two_cons_one_joined(tmp_path / "two")
    text = (two / PORT_CONS).read_text(encoding="utf-8")
    line = text.split("\n").index(f"      - {TO_CONS_ONE}") + 1
    moved_note = (
        f"trellis.port-cons.yml, periods[0].connectors[0]: {TO_CONS_ONE} changed to "
        f"{TO_CONS_TWO}, periods 0–5"
    )
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(two), PORT_CONS)
        choose_view(tab, None, "forward")
        wait_until(lambda: CONS_TWO_M in unjoined_field_ids(tab), 30.0, "the forward graph's ports")
        # the cable carries one wire and `cons_two` holds one arrival field,
        # so the end dropped on its arrival port moves with no list (J-D33)
        move_join_end(
            tab, "periods[2]/port", "periods[2]/cons_one", "target", cable_port(tab, "periods[2]/cons_two", "reading")
        )
        wait_until(
            lambda: line_text(tab, line) == f"      - {TO_CONS_TWO}", 10.0, "the line changed"
        )
        wait_until(lambda: gesture_note(tab) == moved_note, 10.0, "the move's note")
        moved = {f"periods[{h}]/cons_two/cons:measure:arvl": "m_next → m" for h in range(6)}
        wait_until(
            lambda: moved.items() <= held_joins(tab).items(),
            60.0,
            "the join moved in every period",
        )
        assert CONS_TWO_M not in unjoined_field_ids(tab)
        assert "periods[2]/cons_one/unjoined:cons:arvl:m" in unjoined_field_ids(tab)
        assert tab.evaluate(DOCUMENT_JS) == text.replace(TO_CONS_ONE, TO_CONS_TWO)
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+z")
        wait_until(lambda: tab.evaluate(DOCUMENT_JS) == text, 10.0, "the move undone in one step")
        assert (two / PORT_CONS).read_text(encoding="utf-8") == text
    finally:
        context.close()

    # the time on the corpus's largest trellis (unit J's plan, Task 16;
    # decision J-D8): the drag between periods in `durables_without_a`, its
    # forward graph restricted as the folder opens, timed on the page's clock
    durables = durables_without_a(tmp_path / "durables")
    standing = (durables / TRELLIS_FILE).read_text(encoding="utf-8")
    mapping_line = standing.split("\n").index(WITHOUT_A) + 1
    context, tab = new_tab(browser)
    try:
        # the backward graph, which the page opens with, is one node, the
        # package drawing no backward graph where a marginal value one
        # occurrence reads is paired with no wire the other writes
        open_trellis(tab, server_on(durables), RECIPE_FILE, minimum=1)
        assert restriction_shown(tab) == "periods 0–2"
        choose_view(tab, None, "forward")
        wait_until(
            lambda: {KEEPER_A, TENURE_A} <= set(unjoined_field_ids(tab)),
            60.0,
            "the forward graph's ports",
        )
        assert ADJUSTER_A in unjoined_field_ids(tab)
        tab.evaluate(DRAG_TIMES_JS, [TENURE_A, ADJUSTER_A, TRELLIS_FILE, mapping_line, "moved"])
        # the drag from the joined branch port is the move of the cable to
        # `tenure` onto its own destination: the list keeps `h` and `z`,
        # pre-filled, and takes `a_nxt_kp` for `a` (design pass 10 §7)
        drag_cable(tab, "periods[2]/keeper_cons", "", "periods[1]/tenure", {TENURE_A: KEEPER_A})
        times, _ = wait_until(
            lambda: tab.evaluate(DRAG_TIMES_HELD_JS), 120.0, "the trellis drawn again"
        )
        wait_until(
            lambda: (gesture_note(tab) or "").startswith(DURABLES_NOTE + DURABLES_DRAFT),
            10.0,
            "the status line's note",
        )
        assert line_text(tab, mapping_line) == WITH_A
        # the second branch's `a_nxt_adj` stays unjoined, for the author to
        # type
        wait_until(
            lambda: TENURE_A not in unjoined_field_ids(tab)
            and ADJUSTER_A in unjoined_field_ids(tab),
            30.0,
            "the ports of the trellis drawn again",
        )
        assert (durables / TRELLIS_FILE).read_text(encoding="utf-8") == standing
        # the second branch dragged to `tenure`'s arrival port, whose `a` the
        # entry now reaches: a further source, added to the same mapping
        # (J-D41, J-D42)
        tenure_in = cable_port(tab, "periods[1]/tenure", "reading")
        state = drag_cable(tab, "periods[2]/adjuster_cons", "", "periods[1]/tenure", {TENURE_A_JOINED: ADJUSTER_A})
        assert state["valid"] == [tenure_in] and tenure_in in state["admitted"], state
        wait_until(lambda: gesture_note(tab) == BRANCH_NOTE, 10.0, "the further source's note")
        wait_until(lambda: line_text(tab, mapping_line) == WITH_BOTH, 10.0, "the key typed")
        wait_until(
            lambda: ADJUSTER_A not in unjoined_field_ids(tab),
            60.0,
            "the second branch's field joined",
        )
        assert (durables / TRELLIS_FILE).read_text(encoding="utf-8") == standing
        drawn = (times["drawn"] - times["connected"]) / 1000
        opened = (times["opened"] - times["connected"]) / 1000
        print(
            f"item 1: on the durables trellis of 51 periods, shown periods 0–2, the trellis "
            f"drawn again {drawn:.3f} s after the event moved and {TRELLIS_FILE} open at "
            f"the typed line after {opened:.3f} s, on {platform.system()} {platform.release()} "
            f"({platform.machine()}) with {os.cpu_count()} processors"
        )
    finally:
        context.close()


def test_item_2_a_drag_between_periods_adds_its_entry_to_the_inter_period_mapping(
    browser, server_on, tmp_path
):
    """Item 2 (spec 0.4 §8 J (2); spec 0.4 §3.1; brief rule 1, its third
    row, and §5): in the copy `emptied_port_cons`, its trellis file opened.
    In the backward graph a drag between two ports starts no line, sends no
    event and types nothing. In the forward graph a drag from `disc`'s
    branch port in `periods[3]` to `port`'s arrival port in `periods[2]`,
    the period after it in time, opens the cable's list, whose row `k` takes
    `a` (design pass 10 §7; unit N, Task 7), and `join` adds the entry
    `disc.a: k`, its key naming the writer since `cons` writes an `a` too,
    to the one inter-period mapping the file writes; the note of §5
    names every period, and the trellis is drawn
    again from the buffer with the join on `port`'s arrival port in every
    period but the earliest, whose arrival no join reaches. In the copy
    `five_mappings_port_cons`, whose trellis file writes one mapping for
    each of its five pairs, the same drag fills `inter_connectors[2]` alone,
    the list keeps its five mappings, the note names periods 2 and 3, and
    the join stands between those two periods alone."""
    standing = emptied_port_cons(tmp_path / "standing")
    five = five_mappings_port_cons(tmp_path / "five")
    notes = {}
    for copy in (standing, five):
        folder = model.open_folder(copy)
        shown = trellis.show_trellis(folder, LESSON).shown
        ids = {port["id"] for port in trellis.unjoined_ports(shown, {})}
        assert {LEAVING, ARRIVING} <= ids
        # the note of the drag, which names after the entry the draft the
        # package reports where the route into `port` is incomplete (unit N,
        # Task 7)
        drag = trellis.connector_edit(
            shown, connected_event(shown, folder, (3, "disc", "a"), (2, "port", "k")), {}
        )
        assert drag.sentence is None, drag.sentence
        notes[copy] = drag.note
    # the entry names the writer, `disc.a`, since `cons` and `disc` both
    # write a continuation field `a` and the package asks for the stage key
    # before an ambiguous field (`endpoint-ambiguous`), as lesson 05's
    # trellis file writes it
    cases = (
        (
            standing,
            ["  - {disc.a: k}"],
            "inter_connectors[0]: disc.a: k written, entry, periods 0–5",
            {PORT_ARRIVAL.format(h): f"inter_connectors[{h}] a → k" for h in range(5)},
        ),
        (
            five,
            ["  - {}", "  - {}", "  - {disc.a: k}", "  - {}", "  - {}"],
            "inter_connectors[2]: disc.a: k written, entry, periods 2–3",
            {PORT_ARRIVAL.format(2): "inter_connectors[2] a → k"},
        ),
    )
    for copy, mappings, written, joins in cases:
        on_disk = (copy / PORT_CONS).read_text(encoding="utf-8")
        lines = range(MAPPING_LINE, MAPPING_LINE + len(mappings))
        assert [on_disk.split("\n")[n - 1] for n in lines] == ["  - {}"] * len(mappings)
        context, tab = new_tab(browser)
        try:
            open_trellis(tab, server_on(copy), PORT_CONS)
            if copy == standing:
                hold_events(tab, "connected")
                state = drag_ports(tab, *tab.evaluate(TWO_PORTS_JS))
                assert (state["connecting"], state["line"]) == (False, None)
                assert release_events(tab, "connected") == []
            choose_view(tab, None, "forward")
            wait_until(
                lambda: {LEAVING, ARRIVING} <= set(unjoined_field_ids(tab)),
                30.0,
                "the forward graph's ports",
            )
            drag_cable(tab, "periods[3]/disc", "", "periods[2]/port", {ARRIVING: LEAVING})
            note = notes[copy]
            assert note.startswith(f"trellis.port-cons.yml, {written}"), note
            wait_until(lambda note=note: gesture_note(tab) == note, 10.0, "the status line's note")
            assert [line_text(tab, n) for n in lines] == mappings
            wait_until(
                lambda joins=joins: {
                    port: join for port, join in held_joins(tab).items() if join.endswith("a → k")
                }
                == joins,
                60.0,
                "the joins of the entry",
            )
            assert unsaved_in_tree(tab) == [PORT_CONS]
            assert (copy / PORT_CONS).read_text(encoding="utf-8") == on_disk
        finally:
            context.close()


def test_item_3_a_refused_drag_is_taken_out_and_an_old_event_writes_nothing(
    browser, server_on, tmp_path
):
    """Item 3 (spec 0.4 §8 J (3); brief rules 6 to 8). Its first part, a
    refused line typed: in the copy `emptied_port_cons`, its trellis file
    opened, the connector `- {}` is filled with `a: m`, which closes a
    cycle, and no gesture made the text. The trellis's reading of the
    buffer is refused, and the editor of the open file marks the place the
    package's refusal names, counted in the buffer's text, the entry of
    `periods[0]`: the line's text underlined in orange and the gutter's
    mark on it, its tooltip the package's sentence with no button `take the
    line out`. The list under the error mark holds that sentence alone,
    linked to the file and that line; the last graph stays drawn, dimmed;
    and the file on disk is unchanged. A line typed by hand is marked at the
    package's place, since no record names the line typed (J-I55).

    Its second part, in a new tab (unit J's plan, Task 10): a drag whose
    event is held while the reader opens `trellis.port-cons-vfi.yml`, and
    sent there, names the other source's reading: the list holds the
    sentence "An old graph" at that file, and neither file is edited. Back
    on lesson 05's trellis, the drag from `disc`'s branch port to `cons`'s
    arrival port in `periods[2]`, `a` chosen for `m` in the cable's list
    (design pass 10 §7), types the keyed connector, which the package
    refuses: the
    package's sentence stands in the list linked to the typed line, the
    editor marks that line with the button `take the line out`, and the
    graph is dimmed (J-D32). The button restores the text before the drag,
    which the trellis then reads. The drag made again marks the typed line
    with the button again; one character typed in the file withdraws the
    button, and the sentence returns to the package's place. Nothing is
    written to disk."""
    copy = emptied_port_cons(tmp_path)
    on_disk = (copy / PORT_CONS).read_text(encoding="utf-8")
    emptied = "      - {}"
    assert on_disk.split("\n")[CONNECTOR_LINE - 1] == emptied
    typed = on_disk.replace(f"{emptied}\n", "      - {a: m}\n")
    folder = model.open_folder(copy)
    unsaved = unsaved_of(copy, {PORT_CONS: typed})
    refusal = trellis.show_trellis(folder, LESSON, unsaved=unsaved).refusal
    assert refusal is not None and refusal.rule == "period-join-cycle"
    place = trellis.address_place(
        folder, refusal.file, refusal.address, texts=trellis.texts_of(unsaved)
    )
    assert place == (PORT_CONS, 7)
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PORT_CONS)
        assert open_path_shown(tab) == PORT_CONS
        assert tab.locator(".bl-view-host.bl-stale").count() == 0
        click_line(tab, CONNECTOR_LINE)
        tab.keyboard.press("End")
        tab.keyboard.press("ArrowLeft")
        tab.keyboard.type("a: m")
        assert line_text(tab, CONNECTOR_LINE) == "      - {a: m}"
        tab.wait_for_selector(".cm-content .cm-lintRange-error", timeout=30_000)
        underlined = tab.evaluate(LINT_RANGE_JS)
        assert (underlined["line"], underlined["column"], underlined["text"]) == (
            7,
            3,
            "- stages:",
        )
        assert tab.evaluate(GUTTER_MARKER_LINE_JS) == 7
        tab.hover(".cm-lint-marker-error")
        tab.wait_for_selector(".cm-tooltip-lint .cm-diagnosticText", timeout=5_000)
        assert tab.evaluate(TOOLTIP_TEXTS_JS) == [refusal.message]
        assert tab.locator(".cm-tooltip-lint .cm-diagnosticAction").count() == 0
        wait_until(
            lambda: error_lines(tab) == [(refusal.message, PORT_CONS, 7)],
            10.0,
            "the package's sentence in the list under the error mark",
        )
        assert tab.locator(".bl-view-host.bl-stale").count() == 1
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == on_disk
    finally:
        context.close()

    # the keyed connector the drag from `disc`'s `a` to `cons`'s `m` types,
    # and the package's refusal of the text it makes
    shown = trellis.show_trellis(folder, LESSON).shown
    cycle = connected_event(shown, folder, (2, "disc", "a"), (2, "cons", "m"))
    (keyed,) = trellis.connector_edit(shown, cycle, {}).edits.values()
    keyed_line = keyed.split("\n")[CONNECTOR_LINE - 1]
    assert keyed_line == "      - {from: disc, to: cons, fields: {a: m}}"
    refused = trellis.show_trellis(
        folder, LESSON, previous=shown, unsaved=unsaved_of(copy, {PORT_CONS: keyed})
    ).refusal
    assert refused is not None and refused.rule == "period-join-cycle"
    vfi_on_disk = (copy / VFI).read_text(encoding="utf-8")
    action = ".cm-tooltip-lint .cm-diagnosticAction"
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PORT_CONS)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: {WRITING, READING, DISC_A} <= set(unjoined_field_ids(tab)),
            30.0,
            "the forward graph's ports",
        )
        hold_events(tab, "connected")
        drag_cable(tab, "periods[2]/port", "", "periods[2]/cons", {READING: WRITING})
        assert len(held_events(tab, "connected")) == 1
        reveal_in_tree(tab, VFI)
        tab.click(f'.bl-tree-file[data-path="{VFI}"]')
        wait_until(lambda: trellis_settled(tab, VFI), 60.0, f"the trellis of {VFI}")
        assert open_path_shown(tab) == VFI
        assert len(release_events(tab, "connected")) == 1
        old = (OLD_GRAPH.format("trellis.port-cons-vfi.yml"), VFI, None)
        wait_until(lambda: old in error_lines(tab), 10.0, "the sentence of an old graph")
        assert unsaved_in_tree(tab) == []
        assert tab.locator(".bl-file .bl-modified").count() == 0

        reveal_in_tree(tab, PORT_CONS)
        tab.click(f'.bl-tree-file[data-path="{PORT_CONS}"]')
        wait_until(
            lambda: trellis_settled(tab, PORT_CONS) and open_path_shown(tab) == PORT_CONS,
            60.0,
            f"the trellis of {PORT_CONS}",
        )
        typed_place = (refused.message, PORT_CONS, CONNECTOR_LINE)
        for again in (False, True):
            wait_until(
                lambda: {DISC_A, READING} <= set(unjoined_field_ids(tab)),
                30.0,
                "the forward graph's ports",
            )
            drag_cable(tab, "periods[2]/disc", "", "periods[2]/cons", {READING: DISC_A})
            wait_until(
                lambda: typed_place in error_lines(tab), 30.0, "the sentence at the typed line"
            )
            assert line_text(tab, CONNECTOR_LINE) == keyed_line
            assert tab.locator(".bl-view-host.bl-stale").count() == 1
            assert tab.evaluate(GUTTER_MARKER_LINE_JS) == CONNECTOR_LINE
            tab.hover(".cm-lint-marker-error")
            tab.wait_for_selector(action, timeout=5_000)
            assert tab.locator(action).text_content() == "take the line out"
            if again:
                break
            tab.click(action)
            assert line_text(tab, CONNECTOR_LINE) == emptied
            wait_until(
                lambda: tab.locator(".bl-view-host.bl-stale").count() == 0
                and unsaved_in_tree(tab) == [],
                30.0,
                "the text before the drag read again",
            )
        click_line(tab, 1)
        tab.keyboard.press("ControlOrMeta+End")
        tab.keyboard.type("#")
        package_place = (refused.message, PORT_CONS, 7)
        wait_until(
            lambda: package_place in error_lines(tab), 10.0, "the sentence at the package's place"
        )
        tab.hover(".cm-lint-marker-error")
        tab.wait_for_selector(".cm-tooltip-lint .cm-diagnosticText", timeout=5_000)
        assert tab.locator(action).count() == 0
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == on_disk
        assert (copy / VFI).read_text(encoding="utf-8") == vfi_on_disk
    finally:
        context.close()


def test_item_4_two_continuation_states_show_two_unjoined_ports_each_dragged_to_its_entry(
    browser, server_on, tmp_path
):
    """Item 4 (spec 0.4 §8 J (4); spec 0.4 §3.4; brief §4, decision J-D11).
    In the copy `emptied_pension`, whose standing inter-period mapping is
    emptied, the Workbench's `trellis.unjoined_ports` answers 144 unjoined
    ports for the forward graph of the whole trellis, the two ends
    counted. On the page, its recipe opened, the whole trellis shown and its
    forward graph chosen, the status line counts the four fields of them
    that the checklist lists, the arrival fields outside the earliest period
    once for each stage and field (unit L, Task 21). With the
    occurrence `periods[2]/retiree_saving` closed, its card carries one
    branch port and one arrival port, which name its four unjoined fields,
    the two continuation fields `y_f_ret` and `y_p_ret` on the branch port
    (design pass 10 §6; unit N, Task 7). A drag from the closed card's
    branch port to `retiree_saving`'s arrival port in `periods[1]`, the next
    period in time, opens the cable's list, in which `y_f_ret` is chosen for
    `y_f_r`, and `join` adds `y_f_ret: y_f_r` to the one inter-period
    mapping; the same drag, now the move of that cable onto its own
    destination, keeps that pair and takes `y_p_ret` for `y_p_r`, and `join`
    adds `y_p_ret: y_p_r` to the same mapping (design pass 10 §7); each
    status line names the entry and every period, the first its form, the
    trellis file opens at the line, and the trellis drawn again from the
    buffer counts one unjoined field fewer after each. The list keeps its
    one mapping, no other character of the file changes, the tree marks the
    file `unsaved`, and the file on disk is unchanged.

    With the keyword off a lesson's graph JSON is unchanged (spec 0.4 §3.4;
    the plan's ruling J-P22). A lesson records of a graph the two paths its
    cell `checkout.explore` prints, the files `write_model_explorer` writes,
    which git ignores. The trellis `two` that lesson 05 builds, written by
    `write_model_explorer` after the view of `two` was made with the keyword
    on, which then holds the two ends' ports, is byte for byte the file
    written before it, `trellis.graph.json`, holds no port marked
    `unjoined`, and reads as the view made with the keyword off."""
    copy = emptied_pension(tmp_path / "pension")
    folder = model.open_folder(copy)
    whole = trellis.show_trellis(folder, recipe.Source("recipe", RECIPE_FILE)).shown
    assert len(trellis.unjoined_ports(whole, {})) == PENSION_UNJOINED
    assert trellis.unjoined_count(whole) == PENSION_FIELDS_UNJOINED
    # the first drag writes a new cable, whose note names the form of its
    # line and the draft the package reports while `y_p_r` is unjoined; the
    # second moves that cable onto its own destination, and the note of a
    # cable's write names no form (unit N, Task 7)
    first = trellis.connector_edit(
        whole,
        connected_event(whole, folder, (2, "retiree_saving", "y_f_ret"), (1, "retiree_saving", "y_f_r")),
        {},
    )
    assert first.sentence is None and first.note.startswith(
        "trellis.yml, inter_connectors[0]: y_f_ret: y_f_r written, entry, periods 0–14"
    ), first.note
    notes = (first.note, "trellis.yml, inter_connectors[0]: y_p_ret: y_p_r written, periods 0–14")
    on_disk = (copy / TRELLIS_FILE).read_text(encoding="utf-8")
    emptied = "inter_connectors:\n  - {}\n"
    assert on_disk.count(emptied) == 1
    mapping_line = on_disk.split("\n").index("  - {}") + 1
    context, tab = new_tab(browser)
    try:
        # the backward graph, which the page opens with, is one node, the
        # package refusing to pair the retirement choice's marginal values
        open_trellis(tab, server_on(copy), RECIPE_FILE, minimum=1)
        choose_restriction(tab, "all")
        choose_view(tab, None, "forward")
        wait_until(
            lambda: f" · {PENSION_FIELDS_UNJOINED} unjoined internal entry fields"
            in (trellis_settled(tab, RECIPE_FILE) or ""),
            60.0,
            "the whole trellis's unjoined fields",
        )
        wait_until(
            lambda: {Y_F_RET, Y_P_RET, Y_F_R, Y_P_R} <= set(unjoined_field_ids(tab)),
            60.0,
            "the forward graph's ports",
        )
        own = sorted(port for port in unjoined_field_ids(tab) if port.startswith(f"{RETIREE}/"))
        assert len(own) == 4
        closed = f"{RETIREE}{LAYER_ID_ENDING}"
        # the toggle reached as a reader reaches it, since the graph opens on
        # periods[0] (unit K's decision K-D6)
        click_toggle(tab, closed)
        wait_until(lambda: unjoined_on_card(tab, closed) == own, 10.0, "the closed occurrence's ports")
        # the closed card's one branch port names the two continuation fields
        (branch,) = [p for p in cable_ports(tab) if p["box"] == closed and p["side"] == "writing" and not p["hidden"]]
        assert (branch["branch"], sorted(branch["unjoined"]), branch["joined"], branch["starts"]) == ("", [Y_F_RET, Y_P_RET], False, True), branch

        count = PENSION_FIELDS_UNJOINED
        for (source, target, mapping, entry), note in zip(PENSION_DRAGS, notes):
            drag_cable(tab, RETIREE, "", "periods[1]/retiree_saving", {target: source})
            assert f"inter_connectors[0]: {entry} written" in note
            wait_until(lambda note=note: gesture_note(tab) == note, 10.0, "the status line's note")
            wait_until(
                lambda: open_path_shown(tab) == TRELLIS_FILE,
                30.0,
                f"{TRELLIS_FILE} open",
            )
            assert line_text(tab, mapping_line) == mapping
            count -= 1
            wait_until(
                lambda count=count, ends={source, target}: f" · {count} unjoined internal entry fields"
                in (trellis_settled(tab, RECIPE_FILE) or "")
                and not ends & set(unjoined_field_ids(tab)),
                60.0,
                "the trellis drawn again",
            )
        # the mapping's line after the second drag
        last = PENSION_DRAGS[-1][2]
        typed = on_disk.replace(emptied, f"inter_connectors:\n{last}\n")
        assert tab.evaluate(DOCUMENT_JS) == typed
        assert unsaved_in_tree(tab) == [TRELLIS_FILE]
        assert (copy / TRELLIS_FILE).read_text(encoding="utf-8") == on_disk
    finally:
        context.close()

    # what lesson 05 writes of its trellis `two` (its cell
    # `checkout.explore(two)`), built by the lesson's own calls
    stages = {key: elaborate_stage(load_stage(ROOT / path)) for key, path in LESSON_STAGES.items()}
    period = {"stages": stages, "connectors": [{"m_next": "m"}]}
    two = accrete(accrete({"periods": [], "inter_connectors": []}, period), period, {"a": "k"})
    written, _ = write_model_explorer(two, tmp_path / "lesson")
    before = written.read_bytes()
    off = to_model_explorer(two, unjoined=False)
    assert to_model_explorer(two, unjoined=True) != off
    again, _ = write_model_explorer(two, tmp_path / "again")
    assert again.name == written.name == "trellis.graph.json"
    assert again.read_bytes() == before and b"unjoined" not in before
    assert json.loads(before) == json.loads(json.dumps(dataclasses.asdict(off)))


def test_item_5_a_stage_and_a_period_are_added_by_drops_by_pointer_and_by_keyboard(
    browser, server_on, repository, tmp_path
):
    """Item 5 (spec 0.4 §8 J (5); spec 0.4 §§3.2, 3.5, 3.6; brief rule 9 and
    §5). On a folder `new trellis` wrote, its recipe opened: the folder's
    bar holds `new trellis` and `new variant` and no longer `add stage` or
    `add period`; the backward graph draws no button `stages` and no `+
    period` control; the forward graph draws one control at the earliest
    end and one between each two periods, none at the terminal end, every
    control standing left of `periods[0]`. The template of `noport`,
    dropped by the pointer on `periods[2]`, marks the six layers its entry
    writes during the drag, writes the stage folder to disk, types its edits
    into the recipe, the period file and answers.yml, which the tree marks
    `unsaved` and the disk does not hold, names them on the status line, and
    the graph is drawn with `noport` in every period. Enter on the control
    at the earliest end opens the form `add period` headed `before
    periods[5]`, whose button writes the period file `period.young.yml`
    with `cons` and `disc`. The folder stage `port`, sent by the keyboard to
    `periods[6]`, the period that does not list it, types its key into that
    period file's buffer. `cons`, dropped by the pointer on the control
    between `periods[3]` and `periods[2]`, opens the form headed `between
    periods[3] and periods[2]` with `cons` chosen; its button splits the
    repeated entry, and the status line and the restriction's select name the
    new period and its neighbors, `periods 2–4`. On a copy of
    `applications/cons-port`, whose trellis file writes its stages as
    records, the list is headed `This folder's stages`; Backspace and
    Delete remove nothing from the forward trellis graph, and a stage's
    graph draws no button `stages`, no control and no port a drag can
    take."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    folder = created.folder
    on_disk = {name: (folder / name).read_text(encoding="utf-8") for name in NEW_TRELLIS_EDITED}
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(folder), RECIPE_FILE)
        lay_out_left_to_right(tab)
        assert tab.locator(".bl-add-stage").count() == 0
        assert tab.locator(".bl-add-period").count() == 0
        assert tab.locator(".bl-new-trellis").count() == 1
        assert tab.locator(".bl-new-variant").count() == 1
        assert tab.locator(".bl-stages-button").count() == 0
        assert add_period_controls(tab) == []

        choose_view(tab, None, "forward")
        wait_until(
            lambda: add_period_controls(tab) == control_targets(6), 30.0, "the six controls"
        )
        assert controls_left_of(tab, f"periods[0]{LAYER_ID_ENDING}")
        assert tab.locator(".bl-stages-button").text_content() == "Stages"

        # a template dropped by the pointer on periods[2], whose entry writes
        # the six periods
        state = drop_item(tab, NOPORT_ID, f"periods[2]{LAYER_ID_ENDING}")
        assert state == {"reached": period_layers(range(6)), "control": None}
        for path in NOPORT_FILES:
            reveal_in_tree(tab, path, timeout=30_000)
        edited = ["answers.yml", "declaration/period.yml", "declaration/spec.yml"]
        wait_until(lambda: unsaved_in_tree(tab) == edited, 10.0, "the three files unsaved")
        wait_until(lambda: gesture_note(tab) == NOPORT_NOTE, 10.0, "the status line's note")
        noport = {f"periods[{h}]/noport" for h in range(6)}
        wait_until(
            lambda: noport <= occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "forward"),
            60.0,
            "noport drawn in every period",
        )
        assert all(
            (folder / name).read_text(encoding="utf-8") == text for name, text in on_disk.items()
        )

        # Enter on the control at the earliest end
        wait_until(
            lambda: add_period_controls(tab) == control_targets(6), 30.0, "the controls again"
        )
        drop_by_keyboard(tab, None, "earliest end")
        form = '.bl-form[data-form="add period"]'
        tab.wait_for_selector(form, timeout=30_000)
        # the form's name with its capital (design pass 8 §8 item 1; unit
        # M, Task 6)
        assert tab.locator(f"{form} h2").inner_text() == "Add period before periods[5]"
        assert tab.locator(f"{form} .bl-period-stage.bl-active").count() == 0
        tab.fill(".bl-period-label input", "young")
        for key in ("cons", "disc"):
            tab.click(f'.bl-period-stage[data-key="{key}"]')
        tab.click(".bl-period-submit")
        reveal_in_tree(tab, "declaration/period.young.yml", timeout=30_000)
        wait_until(lambda: gesture_note(tab) == YOUNG_NOTE, 10.0, "the note of the young period")
        assert tab.locator(form).count() == 0

        # the folder stage `port` sent by the keyboard to periods[6], whose
        # period file lists cons and disc alone
        wait_until(
            lambda: add_period_controls(tab) == control_targets(7), 60.0, "the seven controls"
        )
        drop_by_keyboard(tab, "port", f"periods[6]{LAYER_ID_ENDING}")
        # port is joined to nothing in the earliest period, which the note
        # names (unit N, Task 5; design pass 10 §7)
        wait_until(
            lambda: gesture_note(tab)
            == "period.young.yml, stages: port written, periods 6; port unconnected",
            10.0,
            "the note of the keyboard's drop",
        )
        wait_until(
            lambda: "declaration/period.young.yml" in unsaved_in_tree(tab),
            10.0,
            "the young period file unsaved",
        )
        wait_until(
            lambda: "periods[6]/port"
            in occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "forward"),
            60.0,
            "port drawn in periods[6]",
        )

        # `cons` dropped by the pointer on the control between periods[3] and
        # periods[2]
        wait_until(
            lambda: add_period_controls(tab) == control_targets(7), 60.0, "the controls again"
        )
        between = "between periods[3] and periods[2]"
        state = drop_item(tab, "cons", between)
        assert state == {"reached": [], "control": between}
        tab.wait_for_selector(form, timeout=30_000)
        assert tab.locator(f"{form} h2").inner_text() == f"Add period {between}"
        chosen = tab.locator(f"{form} .bl-period-stage.bl-active")
        assert [chosen.nth(n).get_attribute("data-key") for n in range(chosen.count())] == ["cons"]
        tab.fill(".bl-period-label input", "mid")
        for key in ("port", "disc", "noport"):
            tab.click(f'.bl-period-stage[data-key="{key}"]')
        tab.click(".bl-period-submit")
        reveal_in_tree(tab, "declaration/period.mid.yml", timeout=30_000)
        wait_until(lambda: gesture_note(tab) == MID_NOTE, 10.0, "the note of the insertion")
        wait_until(
            lambda: restriction_shown(tab) == "periods 2–4",
            10.0,
            "the restriction written",
        )
        assert (folder / "declaration/trellis.yml").read_text(encoding="utf-8") == on_disk[
            "declaration/trellis.yml"
        ]
    finally:
        context.close()

    copy = applications_copy(tmp_path / "records")
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(copy), PORT_CONS)
        lay_out_left_to_right(tab)
        choose_view(tab, None, "forward")
        wait_until(
            lambda: add_period_controls(tab) == control_targets(6), 30.0, "the records' controls"
        )
        open_stage_list(tab)
        assert tab.locator(".bf-stage-list .bf-stage-heading").text_content() == RECORDS_HEADING
        items = tab.locator(".bf-stage-list .bf-stage-item")
        assert sorted(items.nth(n).get_attribute("data-item") for n in range(items.count())) == [
            "cons",
            "disc",
            "port",
        ]
        tab.keyboard.press("Escape")
        wait_until(
            lambda: tab.locator(".bf-stage-list").count() == 0
            and keyboard_place(tab)["box"] is not None,
            5.0,
            "the list closed and the focus in the graph",
        )
        held = tab.evaluate(HELD_COLLECTION_JS)
        drawn = tab.evaluate(BOX_DRAWN_JS)
        tab.keyboard.press("Backspace")
        tab.keyboard.press("Delete")
        tab.wait_for_timeout(300)
        assert tab.evaluate(BOX_DRAWN_JS) == drawn
        assert tab.evaluate(HELD_COLLECTION_JS) == held

        occurrence = f'.bl-view-host .react-flow__node[data-id="periods[1]/cons{LAYER_ID_ENDING}"]'
        tab.click(".bl-zoom-button[data-zoom='fit']")
        tab.dblclick(f"{occurrence} .bf-layer-name")
        wait_until(
            lambda: open_path_shown(tab) == SHARED_CONS,
            60.0,
            "the occurrence's stage",
        )
        choose_view(tab, "operator", "forward")
        wait_until(
            lambda: tab.locator('.bl-graph-bar[data-graph="forward"]').count() == 1
            and tab.evaluate(PORTS_JS) > 0,
            30.0,
            "the stage's forward graph",
        )
        assert tab.evaluate(CONNECTABLE_JS) == 0
        assert tab.locator(".bl-stages-button").count() == 0
        assert add_period_controls(tab) == []
    finally:
        context.close()
