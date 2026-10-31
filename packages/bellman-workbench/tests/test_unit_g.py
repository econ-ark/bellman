"""The acceptance tests of unit G of model interface specification 0.4,
brief §3: one test for each of items 1 to 5; item 6 is AAS's reading.
Deleted when the next amendment is accepted (lean implementation rule, layer 2).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

from bellman.stage import LAYER_ID_ENDING, layers_to_open, source_spans, write_model_explorer
from bellman_workbench import app, model, recipe, trellis

from workbench_support import (
    ATTRIBUTE_ROWS_JS,
    BOX_DRAWN_JS,
    CONS,
    DURABLES,
    active_line,
    attribute_of,
    click_line,
    record,
    bound_as_the_recipe_binds,
    property_color,
    select_node,
    wait_until,
    ELK_SHA256,
    FLOW_FILES,
    FLOW_README,
    PORTFOLIO_CHOICE,
    SOLARA_CDN,
    SOLARA_CDN_README,
    fonts_drawn,
    free_port,
    installed_environment,
    installed_startup_records,
    installed_workbench,
    server_error,
    start_installed_server,
    stop_installed_server,
    unmet_requirements,
    writable,
    HELD_COLLECTION_JS,
    PORT_CONS,
    PORT_CONS_RECIPE,
    RECIPE_FILE,
    WORKBENCH,
    kept_binding_entry,
    build_record,
    every_namespace,
    expected_layout,
    graph_named,
    git_line_sentence,
    git,
    init_repository,
    new_tab,
    occurrences_of,
    show_status,
    layout_differences,
    layout_records,
    open_cons,
    open_path_shown,
    open_trellis,
    opened_namespaces,
    DOCUMENT_JS,
    NODE_POSITIONS_JS,
    OVERLAY_LINES_JS,
    RECORD_OPENED_JS,
    SHARED_CONS,
    WHOLE_GRAPH_SHOWN_JS,
    expected_overlay_lines,
    press_outside_fields,
    recipe_head,
    record_view_state,
    restrict,
    repository_copy,
    seconds_to_the_drawn_trellis,
    svg_texts,
    view_state,
    viewport,
    held_graph_ids,
    boxes_in_region,
    drawn_boxes,
    focus_region,
    region_focus,
    change_panel_height,
    fitted_viewport,
    open_every_layer,
    periods_held,
    press_in_region,
    SELECTABLE_WIRES_JS,
    join_wires_drawn,
    choose_view,
    view_options,
    view_shown,
    READING_SCALE,
    flow_handle,
    opens_on,
)

# The boundary markers of the backward graph of trellis.port-cons.yml with
# every period shown: `start` where the terminal condition's 𝑉≻ and 𝑑𝑉≻
# enter periods[0] and `end` where the result's 𝑉≺ and 𝑑𝑉≺ leave
# periods[5]. Unit N's Task 6 (design pass 10 §6) put these four nodes in
# place of the root's two containers `Inputs` and `Outputs`.
PORT_CONS_BOUNDARY_MARKERS = [
    "end:periods[5]/port/port:function:arvl:V",
    "end:periods[5]/port/port:function:arvl:dV",
    "start:periods[0]/disc/disc:function:cntn:V",
    "start:periods[0]/disc/disc:function:cntn:dV",
]
# The boxes and layers the layout lays out in that graph with every layer
# open: the 258 of the periods and their occurrences and the four boundary
# markers. Before Task 6 the root's `Inputs` and `Outputs` took the markers'
# place, and the count was 260.
ALL_OPEN_BOXES = 258 + len(PORT_CONS_BOUNDARY_MARKERS)


def boundary_markers(records: dict) -> list[str]:
    """The ids, in sorted order, of the boundary markers among the boxes the
    layout's records `records` lay out, the nodes of kind `start` or `end`
    at the graph's root, whose ids begin with their kind."""
    return sorted(box for box in records["boxes"] if box.startswith(("start:", "end:")))


def test_item_5_the_bundle_rebuilds_and_the_installed_page_draws_offline_in_bundled_fonts(
    browser, tmp_path, monkeypatch
):
    """Item 5: every file js/flow/build.sh writes is the file the record of
    js/flow/README.md names, by its size and its SHA-256, so that the files
    served are those the recorded sources rebuild (G-D15); elk.bundled.js is
    elkjs 0.12.0's file unchanged; LICENSES.txt holds the notice of every
    package of the lockfile, and ELK's license and the mathematics font's
    license stand beside the files they cover. The installed page serves its
    assets offline and draws every label in the bundled faces (G-D12)."""
    record = build_record(FLOW_README)
    assert set(record) == set(FLOW_FILES.values())
    for relpath, (size, digest) in record.items():
        data = (WORKBENCH / relpath).read_bytes()
        assert (len(data), hashlib.sha256(data).hexdigest()) == (size, digest), relpath
    assert record[FLOW_FILES["elk"]][1] == ELK_SHA256
    lock = json.loads((WORKBENCH / "js/flow/package-lock.json").read_text(encoding="utf-8"))
    notices = (WORKBENCH / FLOW_FILES["notices"]).read_text(encoding="utf-8")
    for key, entry in lock["packages"].items():
        if key.startswith("node_modules/"):
            name = key[len("node_modules/") :]
            assert f"\n{name} {entry['version']}\nlicense: " in notices, key
    elk_license = (WORKBENCH / FLOW_FILES["elk license"]).read_text(encoding="utf-8")
    assert elk_license.startswith("# Eclipse Public License - v 2.0")
    stix_license = (WORKBENCH / FLOW_FILES["stix license"]).read_text(encoding="utf-8")
    assert "SIL Open Font License, Version 1.1" in stix_license

    # Solara's own interface files are those the record names, with their
    # notices, and the server is pointed at them
    from bellman_workbench import command

    record = build_record(SOLARA_CDN_README)
    held = {p.relative_to(WORKBENCH).as_posix() for p in SOLARA_CDN.rglob("*") if p.is_file()}
    assert set(record) == held
    for relpath, (size, digest) in record.items():
        data = (WORKBENCH / relpath).read_bytes()
        assert (len(data), hashlib.sha256(data).hexdigest()) == (size, digest), relpath
    licenses = (SOLARA_CDN / "LICENSES.txt").read_text(encoding="utf-8")
    for folder in ("requirejs@2.3.6", "font-awesome@4.5.0", "@widgetti/solara-vuetify3-app@5.2.0"):
        assert f"\n\n{folder}\nlicense: " in licenses, folder
    monkeypatch.setenv("SOLARA_ASSETS_PROXY_CACHE_DIR", str(tmp_path / "inherited-cache"))
    served = command.server_environment(tmp_path)["SOLARA_ASSETS_PROXY_CACHE_DIR"]
    assert served == str(SOLARA_CDN.resolve())
    # the server sends its responses uncompressed (G-R77)
    assert command.server_environment(tmp_path)["SOLARA_SERVER_HTTP_GZIP"] == "False"

    # the two packages built as wheels and installed, read-only, outside the
    # checkout, the requirements met by the environment with bellman[explore]
    site = installed_workbench(tmp_path / "site", tmp_path / "build")
    restore_permissions = True
    try:
        assert unmet_requirements(site, {"bellman": {"explore"}}) == []
        for name in ("public", "solara-cdn"):
            installed, source = (
                {p.relative_to(base).as_posix() for p in (base / name).rglob("*") if p.is_file()}
                for base in (site / "bellman_workbench", WORKBENCH / "bellman_workbench")
            )
            assert installed == source, name
        probe_cache = tmp_path / "probe-cache"
        probe_cache.mkdir()
        print(f"item 5 probe startup records: {probe_cache / 'installed-startup'}")
        probe = (
            "import json, os, bellman, bellman_workbench as w; "
            "print(json.dumps({'pid': os.getpid(), 'files': [bellman.__file__, w.__file__]}))"
        )
        imported = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=site.parent,
            env=installed_environment(site, probe_cache),
            capture_output=True,
            text=True,
            check=True,
        )
        imported = json.loads(imported.stdout)
        assert all(Path(path).is_relative_to(site) for path in imported["files"]), imported
        probe_records = installed_startup_records(site, probe_cache)
        assert set(probe_records) == {imported["pid"]}, probe_records

        # the page of the installed package, the network closed to the server
        # and to the browser
        folder = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
        cache = tmp_path / "cache"
        cache.mkdir()
        port = free_port()
        url = f"http://localhost:{port}/"
        log_path = tmp_path / "installed.log"
        process = start_installed_server(site, folder, port, log_path, cache)
        restore_permissions = False
        context = None
        outside, failed = [], []

        def offline(route):
            # a request to another machine is refused and listed
            if urllib.parse.urlsplit(route.request.url).hostname in ("localhost", "127.0.0.1"):
                route.continue_()
            else:
                outside.append(route.request.url)
                route.abort()

        def answered(response):
            if response.status >= 400:
                failed.append(f"{response.status} {response.url}")

        try:
            error = server_error(url, process, log_path)
            assert error is None, error
            records = installed_startup_records(site, cache)
            assert process.pid in records, records
            outer = records[process.pid]
            assert outer["argv"][1:3] == ["-m", "bellman_workbench.command"], outer
            children = [record for record in records.values() if record["ppid"] == process.pid]
            assert len(children) == 1, records
            child = children[0]
            assert child["pid"] not in (process.pid, imported["pid"]), records
            assert child["argv"][1:3] == ["-m", "solara"], child
            assert child["cache"] is not None, child
            assert child["cache_resolved"] == str(site / "bellman_workbench/solara-cdn"), child
            context, tab = new_tab(browser)
            context.route("**/*", offline)
            tab.on("requestfailed", lambda request: failed.append(f"failed {request.url}"))
            tab.on("response", answered)
            open_cons(tab, url)
            drawn = fonts_drawn(tab)
        finally:
            try:
                if context is not None:
                    context.close()
            finally:
                stop_installed_server(process, cache)
                restore_permissions = True
        assert outside == [] and failed == [], (outside, failed)
        bundled = {"IBM Plex Mono (custom)", "STIX Two Math (custom)"}
        elsewhere = {text: faces for text, faces in drawn.items() if not faces <= bundled}
        assert drawn and elsewhere == {}, elsewhere
        print(
            f"item 5: the installed page drew {len(drawn)} texts in "
            f"{sorted(set().union(*drawn.values()))} on {platform.system()} "
            f"{platform.release()} ({platform.machine()}); other platforms, a machine without "
            "a checkout, and offline installation of dependencies were not verified"
        )
    finally:
        if restore_permissions:
            writable(site)


def test_item_1_the_layout_lays_out_every_box_and_wire_of_the_graph_json(
    page, server, server_on, consport_folder, cons, tmp_path
):
    """Item 1: for every graph of cons.bl, bound as the page binds it, and of
    trellis.port-cons.yml, the layout's records hold what the graph JSON
    makes of them (spec 0.4 §4): with every layer open, at the opening state
    the page opens, and after the first layer of that state is closed; a
    wire read by two boxes is among the cases; a dropped wire and two
    exchanged destinations are each found; and the two files lesson 01's
    `checkout.explore` writes, `write_model_explorer`'s, read back from disk,
    lay out to the records their graph JSON makes."""

    def compare(collection: dict, depth: int) -> set[str]:
        # the first two comparisons on every graph of `collection`, the
        # opening state being the layers `layers_to_open` names at `depth`;
        # answers the boxes laid out with every layer open
        laid_out = set()
        for graph in collection["graphs"]:
            every = every_namespace(graph)
            records = layout_records(page, graph, every)
            assert layout_differences(records, expected_layout(graph, every)) == [], graph["id"]
            laid_out |= set(records["boxes"])
            opening = layers_to_open(collection, graph["id"], depth)
            for named in (opening, opening[1:]):
                opened = opened_namespaces(named)
                records = layout_records(page, graph, opened)
                assert layout_differences(records, expected_layout(graph, opened)) == [], named
        return laid_out

    open_cons(page, server)
    held = page.evaluate(HELD_COLLECTION_JS)
    compare(held, 1)

    backward = graph_named(held, "backward")
    every = every_namespace(backward)
    expected = expected_layout(backward, every)
    records = layout_records(page, backward, every)
    assert max(Counter(tuple(wire[:2]) for wire in records["wires"]).values()) > 1
    for fault in ("drop", "exchange", "duplicate", "extra", "incomplete", "missing box", "exchange routes"):
        damaged = layout_records(page, backward, every, fault=fault)
        differences = layout_differences(damaged, expected)
        assert differences, fault
        if fault == "exchange routes":
            assert sum("does not end at its ELK endpoints" in line for line in differences) == 2
    assert layout_differences({**records, "places": {}, "routes": {}}, expected)

    graph_file, overlays_file = write_model_explorer(cons, tmp_path / "model-explorer")
    lesson = json.loads(graph_file.read_text(encoding="ascii"))
    overlays = json.loads(overlays_file.read_text(encoding="ascii"))
    laid_out = compare(lesson, 1)
    ends = {
        edge[end]
        for overlay in overlays["overlays"]
        for edge in overlay["edges"]
        for end in ("sourceNodeId", "targetNodeId")
    }
    assert ends and ends <= laid_out

    open_trellis(page, server_on(consport_folder), PORT_CONS)
    compare(page.evaluate(HELD_COLLECTION_JS), 2)

    # the third comparison: the boxes kept in the page, all of them at 150
    # boxes or fewer, those within the region above 150; the boxes of the
    # builders of a compact occurrence among them (AAS, L-D7)
    held = page.evaluate(HELD_COLLECTION_JS)
    backward = graph_named(held, "backward")
    opening = opened_namespaces(layers_to_open(held, "backward", 2))
    records = layout_records(page, backward, opening)
    assert records["builderPlaces"] and len(drawn_boxes(records)) <= 150
    assert set(page.evaluate(NODE_POSITIONS_JS)) == drawn_boxes(records)
    open_every_layer(page)
    every = every_namespace(backward)
    opened = page.evaluate("() => document.querySelector('.bl-view-host').bellmanFlow.openLayers()")
    assert set(opened) == every
    records = layout_records(page, backward, every)
    assert len(records["boxes"]) == ALL_OPEN_BOXES
    assert boundary_markers(records) == PORT_CONS_BOUNDARY_MARKERS
    page.wait_for_timeout(200)
    assert set(page.evaluate(NODE_POSITIONS_JS)) == boxes_in_region(records, viewport(page))

    # a trellis restricted by unit B's input
    restrict(page, "periods 0–1")
    wait_until(lambda: periods_held(page) == {"periods[0]", "periods[1]"}, 60.0, "periods 0–1")
    compare(page.evaluate(HELD_COLLECTION_JS), 2)
    held = page.evaluate(HELD_COLLECTION_JS)
    backward = graph_named(held, "backward")
    opened = page.evaluate("() => document.querySelector('.bl-view-host').bellmanFlow.openLayers()")
    records = layout_records(page, backward, set(opened))
    expected_boxes = (
        drawn_boxes(records) if len(drawn_boxes(records)) <= 150
        else boxes_in_region(records, viewport(page))
    )
    assert set(page.evaluate(NODE_POSITIONS_JS)) == expected_boxes


def test_item_2_a_box_shows_its_symbol_and_mark_and_the_links_hold(
    page, server, model_folder, original
):
    """Item 2: on cons.bl with its methods, bound as the folder's recipe
    binds it, every box of the backward graph prints its label as
    `node_label` writes it, whole inside the box, the symbol in ice and the
    mark from ` · !` in ice-3, `𝑐(m_d) · !egm` among them, and no box prints
    its kind; the kind `Evaluation` stands in the head of policy:Evaluation
    in the panel and its rows are those of the box's Details (unit K, Task
    5; `app.box_rows`), no kernel among them; the three backward boxes and
    the two forward boxes of
    AMD-MI-001's item 3 alone are lined in the accent, and the box selected
    carries the ring 5 px outside it; the boxes of the policy layer stand in
    one column where ELK's options give it (the plan's Task 3). Selection
    links the panel, editor and Fields rows; Escape clears the selection
    without changing the editor (spec 0.4 §2.5). The legend gives each
    mark its words and colors each swatch by its custom property (§2.1)."""
    stage = bound_as_the_recipe_binds(model_folder, original, CONS)
    collection = model.collection(stage)
    open_cons(page, server)
    ice, ice_3 = property_color(page, "--bl-ice"), property_color(page, "--bl-ice-3")
    accent = property_color(page, "--bl-graph-output")
    ring = property_color(page, "--bl-graph-ring")

    drawn = page.evaluate(BOX_DRAWN_JS)
    for node in graph_named(collection, "backward")["nodes"]:
        box = drawn[node["id"]]
        _, bound, tag = node["label"].partition(" · !")
        assert box["text"] == node["label"] and box["whole"], node["id"]
        assert box["symbolColor"] == ice, node["id"]
        assert box["mark"] == (f" · !{tag}" if bound else None), node["id"]
        if bound:
            assert box["markColor"] == ice_3, node["id"]
        kind = attribute_of(node, "kind")
        assert not kind or kind not in box["text"], node["id"]
    assert drawn["policy:Evaluation"]["text"] == "𝑐(m_d) · !egm"
    lined = {node_id for node_id, box in drawn.items() if box["border"] == accent}
    assert lined == {"cntn_to_dcsn:Evaluation", "dcsn_to_arvl:Evaluation", "policy:Evaluation"}

    select_node(page, "policy:Evaluation", "backward")
    kind = ".bl-panel-head .bl-panel-kind"
    wait_until(
        lambda: page.locator(kind).count() and page.locator(kind).text_content() == "Evaluation",
        10.0,
        "the kind Evaluation in the panel's head",
    )
    color, width, offset, line = page.evaluate(BOX_DRAWN_JS)["policy:Evaluation"]["outline"]
    assert (color, offset, line) == (ring, "5px", "solid") and 2 <= float(width[:-2]) <= 2.5

    backward = graph_named(page.evaluate(HELD_COLLECTION_JS), "backward")
    records = layout_records(page, backward, every_namespace(backward))
    centers = {
        node["id"]: (
            records["places"][node["id"]]["ax"] + records["places"][node["id"]]["width"] / 2
        )
        for node in backward["nodes"]
        if node.get("namespace") == "policy"
    }
    print(f"the centers of the boxes of the policy layer: {centers}")

    choose_view(page, "operator", "forward")
    wait_until(
        lambda: "arvl_to_dcsn:Pushforward" in page.evaluate(BOX_DRAWN_JS),
        10.0,
        "the forward graph",
    )
    drawn = page.evaluate(BOX_DRAWN_JS)
    lined = {node_id for node_id, box in drawn.items() if box["border"] == accent}
    assert lined == {"arvl_to_dcsn:Pushforward", "dcsn_to_cntn:Pushforward"}

    # The panel's rows and source lines describe the selected box.
    choose_view(page, "operator", "backward")
    wait_until(lambda: "𝑉≻ ∘ 𝑔≻" in svg_texts(page), 15.0, "the backward graph")
    select_node(page, "policy:Evaluation", "backward")
    piece = model.piece(stage, "backward", "policy:Evaluation", collection)
    rows = dict(app.box_rows(piece.attributes))
    assert rows["method"] == "!egm"

    def shown_rows() -> dict:
        return dict(page.evaluate(ATTRIBUTE_ROWS_JS))

    wait_until(lambda: rows.items() <= shown_rows().items(), 10.0, "the box's rows")
    assert not any(key.startswith("kernel") for key in shown_rows())

    def source_lines() -> list[int]:
        return page.locator(".bl-source-line").evaluate_all(
            "(lines) => lines.map((line) => Number(line.dataset.line))"
        )

    quoted = [line for line, _ in piece.source_lines]
    wait_until(lambda: source_lines() == quoted, 10.0, "the source lines of policy:Evaluation")
    spans = source_spans(original, CONS)
    wait_until(lambda: active_line(page) == spans["policy"].line, 10.0, "the editor on policy")
    # The cursor entering cntn_to_dcsn selects the block's first box.
    first = model.nodes_of_block(collection, "backward", "cntn_to_dcsn")[0]
    click_line(page, spans["cntn_to_dcsn"].line + 1)
    wait_until(lambda: record(page, "selections")[-1:] == [first], 10.0, "the block's first box")
    # The Fields row and its box select each other in an initial diagram.
    record_view_state(page)
    choose_view(page, "initial", "backward")
    wait_until(lambda: "V≻" in svg_texts(page), 15.0, "the backward initial diagram")
    page.click('.bl-class-row[data-identity="cons:dcsn:V"] .bl-class-field')
    wait_until(
        lambda: (view_state(page) or {}).get("selected") == "cons:dcsn:V", 10.0, "the field's box"
    )
    select_node(page, "cons:dcsn:dV", "backward initial diagram")
    marked = '.bl-class-row.bl-selected'
    wait_until(
        lambda: page.get_attribute(marked, "data-identity") == "cons:dcsn:dV",
        10.0,
        "the row marked",
    )
    before_text, before_line = page.evaluate(DOCUMENT_JS), active_line(page)
    page.focus('.bl-view-host .react-flow__node[data-id="cons:dcsn:dV"] > .bf-box')
    page.keyboard.press("Escape")

    def cleared() -> bool:
        panel = page.locator(".bl-panel").text_content()
        return (
            page.locator(marked).count() == 0
            and "No selection" in panel
            and page.locator(".bl-block-nodes li").count() == 0
            and page.locator(".bl-cursor-block").count() == 0
        )

    wait_until(cleared, 10.0, "nothing selected anywhere")
    assert page.evaluate(DOCUMENT_JS) == before_text
    assert active_line(page) == before_line

    # The legend gives each mark its words and each swatch its level color.
    choose_view(page, "operator", "backward")
    wait_until(lambda: "𝑉≻ ∘ 𝑔≻" in svg_texts(page), 15.0, "the backward graph")
    marks = '.bl-legend-group[data-group="marks"]'
    texts = page.locator(f"{marks} .bl-legend-text").all_text_contents()
    assert texts == ["· !tag", "at 𝑐", "𝑔≺, 𝑔≻"]
    # the words after a mark in sentence case (design pass 13 §3; C12)
    assert page.locator(f"{marks} .bl-legend-sentence").all_text_contents() == [
        "Bound method",
        "At a policy",
        "Law of motion",
    ]
    swatches = page.locator('.bl-legend-swatch[data-level]').evaluate_all(
        "(all) => all.map((s) => [s.dataset.level, getComputedStyle(s).backgroundColor])"
    )
    assert [level for level, _ in swatches] == ["builder", "operator", "output"]
    assert dict(swatches)["builder"] == property_color(page, "--bl-graph-builder")


def test_item_3_layers_controls_keys_and_gestures_act_as_specified(
    page, server, server_on, consport_folder, model_folder, original
):
    """Item 3: on cons.bl the bar offers the select `graph`, `Operator`
    or `Initial`, the select `direction`, `Backward` or `Forward`, and the
    view tab `Trellis` (R-D56; design pass 8 §6); the strip `Graph
    controls`, floating inside the canvas's lower left, holds the four icon
    buttons of VSCode Elements, each its Codicon with its hover and its
    spoken name, and `Perch overlays`, whose glyph meets 3:1 on the strip's
    ground and which, while the overlays are drawn, stands checked within
    a solid accent outline wider than 0 that meets 3:1, the strip, the
    toggle, its button and its glyph drawn at opacity 1 (design pass 8
    §§3, 5.5 and 6); no
    minimap, dot lattice or box movement; `Lay out from left to right` lays
    every layer out left to right and then offers `Lay out from top to
    bottom`; zoom keeps the scale at or under 1 and `Fit` shows
    the whole graph; a layer closes to one box with one port per wire and
    opens again; Backspace and Delete remove no box and no wire, the one
    exception being a join wire of the forward trellis graph, which alone
    takes a click (unit J's decisions J-D33 and J-D39); the perch overlays
    are drawn in the colors of §5.3 and removed; a double click on the
    ground does nothing; and on trellis.port-cons.yml a double click on the
    occurrence periods[1]/cons opens its stage and Alt+← returns to the
    trellis with the occurrence selected and open. Tab reaches every box,
    including an off-region box before and after a layer closes; Enter
    selects it and Escape clears the region selection. Open and closed
    layer controls have 24-pixel screen targets at reading scale without
    covering labels or ports (spec §5.8; G-R73). The all-open trellis
    opens on its terminal period (unit K's decision K-D6); a change of the
    height of Details, which holds the legend since unit R (G-R23), as a
    drag of its handle makes, leaves it at its opening, and once the view
    has moved fits the graph (spec §2.3; G-R76)."""
    open_cons(page, server)

    # These hidden DOM instructions describe the graph's available keys.
    assert page.locator('.bl-view-host [id^="react-flow__node-desc-"]').all_text_contents() == [
        "Press Enter to select a box or Escape to clear the selection."
    ]
    assert page.locator('.bl-view-host [id^="react-flow__edge-desc-"]').all_text_contents() == [""]

    def words(selector: str) -> list[str]:
        return [text.strip() for text in page.locator(selector).all_text_contents()]

    def control_target(selector: str) -> dict:
        # The representative button's screen area, labels and adjacent ports.
        observed = page.locator(selector).evaluate("""button => {
          const host = button.closest('.bl-view-host');
          const owner = button.closest('.react-flow__node');
          const area = button.getBoundingClientRect();
          const frame = host.getBoundingClientRect();
          const overlaps = rect => area.left < rect.right && area.right > rect.left &&
            area.top < rect.bottom && area.bottom > rect.top;
          const textBounds = element => {
            const range = document.createRange();
            range.selectNodeContents(element);
            return range.getBoundingClientRect();
          };
          const texts = host.querySelectorAll('.bf-name, .bf-layer-name');
          const coveredText = Array.from(texts)
            .filter(element => overlaps(textBounds(element))).map(element => element.textContent);
          const coveredBoxes = Array.from(host.querySelectorAll('.react-flow__node > .bf-box'))
            .filter(element => element.parentElement !== owner &&
              overlaps(element.getBoundingClientRect()))
            .map(element => element.parentElement.dataset.id);
          const ports = Array.from(host.querySelectorAll('.react-flow__handle'));
          const coveredPorts = ports.filter(port => overlaps(port.getBoundingClientRect()))
            .map(port => [port.closest('.react-flow__node').dataset.id,
              port.getAttribute('title')]);
          const ownPorts = ports.filter(port => port.closest('.react-flow__node') === owner);
          const portHits = ownPorts.map(port => {
            const rect = port.getBoundingClientRect();
            const x = rect.x + rect.width / 2, y = rect.y + rect.height / 2;
            if (x <= frame.left || x >= frame.right ||
                y <= frame.top || y >= frame.bottom) return null;
            const hit = document.elementFromPoint(x, y);
            return hit !== button && !button.contains(hit);
          }).filter(hit => hit !== null);
          const points = [[area.left + 1, area.top + 1], [area.right - 1, area.top + 1],
            [area.right - 1, area.bottom - 1], [area.left + 1, area.bottom - 1]];
          const hits = points.map(([x, y]) => {
            const element = document.elementFromPoint(x, y);
            return element === button || button.contains(element);
          });
          const style = getComputedStyle(button);
          return {width: area.width, height: area.height, coveredText, coveredBoxes, coveredPorts,
            portHits, hits, point: points[0], label: button.getAttribute('aria-label'),
            title: button.title, fontSize: parseFloat(style.fontSize),
            expectedFontSize: parseFloat(style.getPropertyValue('--bl-graph-port-size')),
            inside: area.left >= frame.left && area.right <= frame.right &&
              area.top >= frame.top && area.bottom <= frame.bottom};
        }""")
        assert observed["width"] >= 24 and observed["height"] >= 24, observed
        assert observed["inside"] and all(observed["hits"]), observed
        assert not observed["coveredText"] and not observed["coveredBoxes"], observed
        assert not observed["coveredPorts"] and all(observed["portHits"]), observed
        assert observed["label"] == observed["title"], observed
        assert observed["fontSize"] == observed["expectedFontSize"], observed
        return observed

    # the header's two selects, AAS's words, and the button `trellis` (R-D56)
    assert view_shown(page) == {"graph": "operator", "direction": "backward"}
    assert view_options(page, "graph") == ["operator", "initial"]
    assert view_options(page, "direction") == ["backward", "forward"]
    assert words(".bl-trellis-button") == ["Trellis"]
    choose_view(page, "initial", "backward")
    wait_until(lambda: "V≻" in svg_texts(page), 15.0, "the backward initial diagram drawn")
    assert page.locator('.bl-graph-bar[data-graph="backward initial diagram"]').count() == 1
    choose_view(page, "operator", "backward")
    wait_until(lambda: "𝑉≻ ∘ 𝑔≻" in svg_texts(page), 15.0, "the backward graph drawn")

    strip = page.locator('.bl-graph-controls[role="group"][aria-label="Graph controls"]')
    icons = strip.locator(".bl-graph-icon").all()
    assert [
        (icon.get_attribute("title"), icon.get_attribute("label"), icon.get_attribute("icon"))
        for icon in icons
    ] == [
        ("Lay out from left to right", "Lay out from left to right", "split-horizontal"),
        ("Zoom in", "Zoom in", "zoom-in"),
        ("Zoom out", "Zoom out", "zoom-out"),
        ("Fit", "Fit", "screen-full"),
    ]
    for icon in icons:
        size = icon.bounding_box()
        assert icon.locator(".codicon").count() == 1
        assert (size["width"], size["height"]) == (24, 24), size
    assert strip.locator(".bl-overlays-button").count() == 1
    # Spec §5.8: the glyph, and the mark of the checked toggle, contrast
    # with the strip's ground, the strip, the toggle, its button and its
    # glyph each drawn at opacity 1; each read through Playwright's
    # selectors, which reach the toolbar button's own tree. The checked
    # toggle's mark is the on mark of design pass 13 §5 (E1, Q-D9), a 2-px
    # accent line as the toggle's foot, its ::after, with no wash and no
    # outline, which marks the keyboard's focus alone.
    overlay_contrast = r"""([glyph, inner, toggle, strip]) => {
      const rgba = color => {
        const values = color.match(/[\d.]+/g).map(Number);
        return [values[0], values[1], values[2], values.length > 3 ? values[3] : 1];
      };
      const over = (ink, ground) => ink.slice(0, 3).map((value, i) =>
        value * ink[3] + ground[i] * (1 - ink[3]));
      const luminance = color => color.slice(0, 3).reduce((sum, value, i) => {
        const channel = value / 255;
        const linear = channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
        return sum + linear * [0.2126, 0.7152, 0.0722][i];
      }, 0);
      const ratio = (a, b) => (Math.max(luminance(a), luminance(b)) + 0.05) /
        (Math.min(luminance(a), luminance(b)) + 0.05);
      const ground = rgba(getComputedStyle(strip).backgroundColor);
      const style = getComputedStyle(inner);
      const background = over(rgba(style.backgroundColor), ground);
      const text = over(rgba(getComputedStyle(glyph).color), background);
      const outline = over(rgba(style.outlineColor), ground);
      const after = getComputedStyle(toggle, '::after');
      const line = after.content === 'none' ? null : {
        height: parseFloat(after.height), bottom: after.bottom,
        contrast: ratio(over(rgba(after.backgroundColor), ground), ground)};
      const opacity = [strip, toggle, inner, glyph].map(
        node => Number(getComputedStyle(node).opacity));
      return {ground, checked: inner.getAttribute('aria-checked'), opacity,
        text: ratio(text, background), outline: ratio(outline, ground),
        outlineWidth: parseFloat(style.outlineWidth), outlineStyle: style.outlineStyle,
        wash: background, line};
    }"""

    def overlay_measures() -> dict:
        button = strip.locator(".bl-overlays-button")
        handles = [
            button.locator(".codicon").element_handle(),
            button.locator("button").element_handle(),
            button.element_handle(),
            strip.element_handle(),
        ]
        return page.evaluate(overlay_contrast, handles)

    normal_contrast = overlay_measures()
    assert normal_contrast["ground"][3] == 1 and normal_contrast["checked"] == "false"
    assert normal_contrast["opacity"] == [1, 1, 1, 1], normal_contrast
    assert normal_contrast["text"] >= 3, normal_contrast
    assert normal_contrast["line"] is None, normal_contrast
    absent = ".bl-view-host .react-flow__minimap, .bl-view-host .react-flow__background"
    assert page.locator(absent).count() == 0

    chain = ["cntn_to_dcsn:Pullback", "cntn_to_dcsn:Aggregation", "cntn_to_dcsn:Evaluation"]
    places = page.evaluate(NODE_POSITIONS_JS)
    assert places[chain[0]][1] < places[chain[1]][1] < places[chain[2]][1]
    box = f'.bl-view-host .react-flow__node[data-id="{chain[0]}"]'
    start = page.locator(box).bounding_box()
    page.mouse.move(start["x"] + start["width"] / 2, start["y"] + start["height"] / 2)
    page.mouse.down()
    page.mouse.move(400, 400, steps=5)
    page.mouse.up()
    assert page.evaluate(NODE_POSITIONS_JS)[chain[0]] == places[chain[0]]
    page.click(".bl-layout-button")
    def titled(word):
        return page.get_attribute(".bl-layout-button", "data-layout") == word

    wait_until(lambda: titled("vertical"), 5.0, "vertical")

    def turned():
        places = page.evaluate(NODE_POSITIONS_JS)
        return places[chain[0]][0] < places[chain[1]][0] < places[chain[2]][0]

    wait_until(turned, 10.0, "the builder laid out left to right")
    page.click(".bl-layout-button")
    wait_until(lambda: titled("horizontal"), 5.0, "horizontal")

    opened = viewport(page)["zoom"]
    assert opened <= 1
    page.click(".bl-zoom-button[data-zoom='zoom out']")
    wait_until(lambda: viewport(page)["zoom"] < opened, 5.0, "the region zoomed out")
    for _ in range(6):
        page.click(".bl-zoom-button[data-zoom='zoom in']")
    assert viewport(page)["zoom"] <= 1
    page.click(".bl-zoom-button[data-zoom='fit']")
    wait_until(lambda: page.evaluate(WHOLE_GRAPH_SHOWN_JS), 5.0, "the whole graph shown")
    assert viewport(page)["zoom"] <= 1

    held = page.evaluate(HELD_COLLECTION_JS)
    backward = graph_named(held, "backward")
    closed = expected_layout(backward, opened_namespaces(["cntn_to_dcsn", "dcsn_to_arvl"]))
    ports = sum(1 for box_id, _, _ in closed["titles"] if box_id == "policy___group___")
    layer = '.bl-view-host .react-flow__node[data-id="policy___group___"]'
    for _ in range(6):
        page.click(".bl-zoom-button[data-zoom='zoom in']")
    assert 0.6 <= viewport(page)["zoom"] <= 1
    focus = focus_region(page)
    for _ in range(100):
        assert focus is not None, "the focus left the graph before close policy"
        if focus["toggle"] and focus["label"] == "close policy":
            break
        focus = press_in_region(page, "Tab")
    else:
        raise AssertionError("Tab did not reach close policy")
    target = control_target(f"{layer} .bf-toggle")
    page.mouse.click(*target["point"])
    wait_until(lambda: page.locator(f"{layer} > .bf-box").count() == 1, 10.0, "policy closed")
    assert page.locator(f"{layer} .react-flow__handle").count() == ports
    assert page.get_attribute(f"{layer} .bf-toggle", "aria-label") == "open policy"
    wait_until(
        lambda: region_focus(page) == {**focus, "label": "open policy"},
        5.0,
        "the focus on the closed policy control",
    )
    target = control_target(f"{layer} .bf-toggle")
    page.mouse.click(*target["point"])
    wait_until(lambda: page.locator(f"{layer} > .bf-layer:not(.bf-box)").count() == 1, 10.0, "policy open")

    count = len(page.evaluate(BOX_DRAWN_JS))
    page.focus(box)
    page.keyboard.press("Backspace")
    page.keyboard.press("Delete")
    page.wait_for_timeout(300)
    assert len(page.evaluate(BOX_DRAWN_JS)) == count
    assert page.evaluate(HELD_COLLECTION_JS) == held
    assert page.evaluate(DOCUMENT_JS) == original

    stage = bound_as_the_recipe_binds(model_folder, original, CONS)
    opening = opened_namespaces(layers_to_open(held, "backward", 1))
    lines = expected_overlay_lines(backward, opening, model.edge_overlays(stage))
    page.click(".bl-overlays-button")
    wait_until(
        lambda: len(page.evaluate(OVERLAY_LINES_JS)) == len(lines), 10.0, "the overlays drawn"
    )
    for perch, stroke in page.evaluate(OVERLAY_LINES_JS):
        assert stroke == property_color(page, f"--bl-graph-{perch}"), perch
    assert strip.locator(".bl-overlays-button.bl-active").count() == 1
    # the pointer off the toggle, whose hover wash would stand over the mark
    page.mouse.move(1, 999)
    active_contrast = overlay_measures()
    assert active_contrast["checked"] == "true", active_contrast
    assert active_contrast["opacity"] == [1, 1, 1, 1], active_contrast
    assert active_contrast["text"] >= 3, active_contrast
    # the on mark: a line of 2 px at the toggle's foot that meets a state
    # indicator's 3:1 on the strip's ground, over no wash
    line = active_contrast["line"]
    assert line is not None and (line["height"], line["bottom"]) == (2, "0px"), active_contrast
    assert line["contrast"] >= 3, active_contrast
    assert active_contrast["wash"] == active_contrast["ground"][:3], active_contrast
    page.click(".bl-overlays-button")
    wait_until(lambda: page.evaluate(OVERLAY_LINES_JS) == [], 10.0, "the overlays removed")

    # The first point of an 8-pixel grid that starts 4 pixels inside the
    # pane's corner at which elementFromPoint finds the pane itself (R-D47).
    ground_point = """() => {
      const pane = document.querySelector('.bl-view-host .react-flow__pane');
      const area = pane.getBoundingClientRect();
      for (let y = area.top + 4; y < area.bottom - 4; y += 8)
        for (let x = area.left + 4; x < area.right - 4; x += 8)
          if (document.elementFromPoint(x, y) === pane) return [x, y];
      return null;
    }"""
    page.evaluate(RECORD_OPENED_JS)
    point = page.evaluate(ground_point)
    assert point is not None, "no point of the pane is uncovered"
    # A click on the ground gives the focus to the first box, and the region
    # pans to show it; the viewport compared is read after that click (R-D47).
    page.mouse.click(*point)
    page.wait_for_timeout(300)
    before = viewport(page)
    # The pan moves the boxes, so the point is chosen again.
    point = page.evaluate(ground_point)
    assert point is not None, "no point of the pane is uncovered"
    page.mouse.dblclick(*point)
    page.wait_for_timeout(300)
    assert viewport(page) == before and page.evaluate("() => window.openedEvents") == []

    open_trellis(page, server_on(consport_folder), PORT_CONS)
    record_view_state(page)
    occurrence = '.bl-view-host .react-flow__node[data-id="periods[1]/cons___group___"]'
    page.dblclick(f"{occurrence} .bf-layer-name")
    wait_until(lambda: recipe_head(page) == "periods[1] / cons", 60.0, "the occurrence's stage")
    wait_until(
        lambda: open_path_shown(page) == SHARED_CONS
        and {"backward", "forward", "backward initial diagram", "forward initial diagram"}
        <= set(held_graph_ids(page)),
        60.0,
        "the occurrence's file and stage graphs",
    )
    assert open_path_shown(page) == SHARED_CONS
    press_outside_fields(page, "Alt+ArrowLeft")

    def returned() -> bool:
        state = view_state(page) or {}
        layer = "periods[1]/cons___group___"
        return state.get("selected") == layer and layer in state.get("open", [])

    wait_until(returned, 60.0, "the trellis with the occurrence selected and open")

    # The one exception (unit J's decisions J-D33 and J-D39; amendment 02,
    # rulings 11 and 12): in the forward trellis graph the join wires, and no
    # other wire, take a click and Backspace and Delete, which unit J's item
    # 1 removes; spec 0.4 §2.2's sentence that turns reconnection off is
    # amended for them alone, which the controller records at the merge. A
    # box focused there takes neither key.
    folder = model.open_folder(consport_folder)
    lesson = trellis.show_trellis(folder, recipe.Source("recipe", PORT_CONS_RECIPE)).shown
    joins = sorted((wire["from"], wire["to"]) for wire in trellis.join_wires(lesson))
    choose_view(page, None, "forward")
    wait_until(
        lambda: sorted((wire["from"], wire["to"]) for wire in join_wires_drawn(page)) == joins,
        30.0,
        "the join wires of the forward trellis graph",
    )
    # the eleven join wires that entries write and the six of the join `a`
    # by equal names from `cons` to `disc`, a join wire too (unit L, Task 15)
    assert page.evaluate(SELECTABLE_WIRES_JS) == len(joins) == 17
    count, held, text = (
        len(page.evaluate(BOX_DRAWN_JS)),
        page.evaluate(HELD_COLLECTION_JS),
        page.evaluate(DOCUMENT_JS),
    )
    assert focus_region(page) is not None
    page.keyboard.press("Backspace")
    page.keyboard.press("Delete")
    page.wait_for_timeout(300)
    assert len(page.evaluate(BOX_DRAWN_JS)) == count
    assert page.evaluate(HELD_COLLECTION_JS) == held and page.evaluate(DOCUMENT_JS) == text
    choose_view(page, None, "backward")

    # Tab reaches, and Enter selects, a box outside the region among the 262
    # boxes and layers (ALL_OPEN_BOXES), before and after a layer is closed,
    # with no pointer
    region = "document.querySelector('.bl-view-host').bellmanFlow"
    open_trellis(page, server_on(consport_folder), PORT_CONS)
    record_view_state(page)
    open_every_layer(page)
    held = page.evaluate(HELD_COLLECTION_JS)
    backward = graph_named(held, "backward")
    every = every_namespace(backward)
    opened = page.evaluate(f"() => {region}.openLayers()")
    assert set(opened) == every
    records = layout_records(page, backward, set(opened))
    assert len(records["boxes"]) == ALL_OPEN_BOXES
    assert boundary_markers(records) == PORT_CONS_BOUNDARY_MARKERS
    names = {node["id"]: node["label"] for node in backward["nodes"]}
    layouts = page.evaluate(f"() => {region}.layouts()")
    choose_view(page, None, "forward")
    choose_view(page, None, "backward")
    page.wait_for_function(f"() => {region}.layouts() >= {layouts + 2}", timeout=30_000)
    assert set(page.evaluate(f"() => {region}.openLayers()")) == every

    def tab_to(wanted) -> dict:
        # Tab from the region's first item until `wanted(focus)` holds, each
        # box's spoken name read on the way
        now = focus_region(page)
        for _ in range(2000):
            assert now is not None, "the focus left the region"
            if wanted(now):
                return now
            if now["box"] and not now["toggle"]:
                if now["box"].endswith(LAYER_ID_ENDING):
                    name = now["box"][: -len(LAYER_ID_ENDING)].rsplit("/", 1)[-1]
                    assert now["label"] in (f"layer {name}", f"closed layer {name}"), now
                else:
                    assert now["label"] == names[now["box"]], now
            now = press_in_region(page, "Tab")
        raise AssertionError("Tab did not reach the item")

    for close in (False, True):
        if close:
            before = tab_to(lambda now: now["toggle"] and now["label"].startswith("close "))
            after = press_in_region(page, "Enter")
            assert after == {**before, "label": before["label"].replace("close ", "open ", 1)}
        opened = page.evaluate(f"() => {region}.openLayers()")
        records = layout_records(page, backward, set(opened))
        if not close:
            # This all-open trellis, too large to read whole, opens on its
            # terminal period's layer at the largest scale, at most 1 and at
            # least 0.6, at which the layer fills the region's width, the
            # body cut where it is taller than the region, at either height
            # of Details (unit K's decisions K-D6 and K-D22, as AAS's M-D15
            # amends them; `period_opening`).
            terminal = records["places"][f"periods[0]{LAYER_ID_ENDING}"]

            def at_opening(view) -> bool:
                return opens_on(view, terminal, records["width"])

            wait_until(
                lambda: at_opening(viewport(page)),
                10.0,
                "the all-open backward trellis at its opening on periods[0]",
            )

            def fits(view) -> bool:
                # The region's fit to one screen pixel: React Flow measures
                # a drawn box in whole pixels, the layout in fractions.
                fitted = fitted_viewport(page, records["places"])
                extent = max(fitted["width"], fitted["height"])
                return (
                    abs(view["x"] - fitted["x"]) <= 1
                    and abs(view["y"] - fitted["y"]) <= 1
                    and abs(view["zoom"] - fitted["zoom"]) * extent <= 1
                )

            # G-R76: a size change, as a drag of the handle of Details makes,
            # opens the graph again while the view stands at its opening
            start = viewport(page)
            grown = change_panel_height(page, 20)
            assert grown["height"] < start["height"] and at_opening(grown), (start, grown)
            restored = change_panel_height(page, None)
            assert abs(restored["height"] - start["height"]) <= 1, (start, restored)
            assert at_opening(restored), restored

            # and fits the graph once the view has moved
            page.click(".bl-zoom-button[data-zoom='zoom out']")
            wait_until(
                lambda: viewport(page)["zoom"] < restored["zoom"], 5.0, "the region zoomed out"
            )
            grown = change_panel_height(page, 20)
            assert grown["height"] < start["height"], (start, grown)
            assert fits(grown), (grown, fitted_viewport(page, records["places"]))
            restored = change_panel_height(page, None)
            assert abs(restored["height"] - start["height"]) <= 1, (start, restored)
            assert fits(restored), (restored, fitted_viewport(page, records["places"]))

            # The rest of this item reads the opening; choosing the graph
            # again restores it.
            layouts = page.evaluate(f"() => {region}.layouts()")
            choose_view(page, None, "forward")
            page.wait_for_function(f"() => {region}.layouts() >= {layouts + 1}", timeout=30_000)
            choose_view(page, None, "backward")
            page.wait_for_function(f"() => {region}.layouts() >= {layouts + 2}", timeout=30_000)
            assert set(page.evaluate(f"() => {region}.openLayers()")) == set(opened)
            wait_until(
                lambda: at_opening(viewport(page)),
                10.0,
                "the all-open backward trellis at its opening again",
            )
            # the layer controls' targets are read at reading size (G-R73):
            # the view set to 0.6 about its center, as the handle's setView
            # sets a view (R-D29)
            shown = flow_handle(page, "view")
            view, scale = viewport(page), shown["viewport"]["zoom"]
            middle = [
                (view[side] / 2 - shown["viewport"][axis]) / scale
                for side, axis in (("width", "x"), ("height", "y"))
            ]
            shown["viewport"] = {
                "x": view["width"] / 2 - middle[0] * READING_SCALE,
                "y": view["height"] / 2 - middle[1] * READING_SCALE,
                "zoom": READING_SCALE,
            }
            flow_handle(page, "setView", shown)
            wait_until(
                lambda: abs(viewport(page)["zoom"] - READING_SCALE) <= 0.000001,
                5.0,
                "the view at reading size",
            )
            before = tab_to(lambda now: now["toggle"] and now["label"] == "close policy")
            control = (
                f'.bl-view-host .react-flow__node[data-id="{before["box"]}"] .bf-toggle'
            )
            assert abs(viewport(page)["zoom"] - 0.6) <= 0.000001
            control_target(control)
            after = press_in_region(page, "Enter")
            assert after == {**before, "label": "open policy"}
            assert abs(viewport(page)["zoom"] - 0.6) <= 0.000001
            control_target(control)
            assert press_in_region(page, "Enter") == before
            assert set(page.evaluate(f"() => {region}.openLayers()")) == every
        outside = set(records["boxes"]) - boxes_in_region(records, viewport(page))
        target = next(node["id"] for node in backward["nodes"] if node["id"] in outside)
        tab_to(lambda now, target=target: now["box"] == target and not now["toggle"])
        assert target in boxes_in_region(records, viewport(page))
        page.keyboard.press("Enter")
        wait_until(lambda: (view_state(page) or {}).get("selected") == target, 10.0, target)
        page.keyboard.press("Escape")
        wait_until(
            lambda: page.evaluate(f"() => {region}.selection()") is None, 10.0, "no selection"
        )


def test_item_4_the_page_runs_on_the_region_within_the_trellis_load_bounds(
    browser, server_on, scratch_consport, tmp_path
):
    """Item 4: in the trellis view of trellis.port-cons.yml restricted to
    periods 0–1, `export view` writes the whole trellis's two files and its
    record under model-explorer/, the record naming the source, the
    restriction, the graph shown, every file the reading read with its
    digest, the digests of the files written and the commit. The durables
    trellis meets its first and warm-cache bounds, the second start reading
    the binding the first kept in the cache folder, and no page test
    reaches a shadow root. Model Explorer's component and build files are
    absent. Source flags refer to
    the recorded repository, including sibling inputs and inputs outside
    that repository (G-R56). Held bytes that differ from a clean recorded
    commit remain uncommitted, including a CRLF-to-LF change (G-R71)."""
    folder = model.open_folder(scratch_consport)
    whole = trellis.show_trellis(folder, recipe.Source("recipe", PORT_CONS_RECIPE)).shown
    context, tab = new_tab(browser)
    try:
        open_trellis(tab, server_on(scratch_consport), PORT_CONS)
        restrict(tab, "periods 0–1")
        wait_until(
            lambda: len(occurrences_of(tab.evaluate(HELD_COLLECTION_JS), "backward")) < len(
                occurrences_of(whole.collection, "backward")
            ),
            60.0,
            "the trellis restricted",
        )
        show_status(tab)
        tab.click(".bl-git-export")
        wait_until(
            lambda: "exported with its record" in git_line_sentence(tab), 60.0, "the export"
        )
    finally:
        context.close()
    views = scratch_consport / "model-explorer"
    record = json.loads((views / "trellis.export.json").read_text(encoding="utf-8"))
    assert (record["source"], record["restriction"], record["direction"]) == (
        PORT_CONS,
        "periods 0–1",
        "backward",
    )
    digests = sorted(entry["sha256"] for entry in record["source_files"])
    assert digests == sorted(whole.files.values())
    assert set(record["generated"]) == {"trellis.graph.json", "trellis.edge-overlays.json"}
    for name, digest in record["generated"].items():
        assert hashlib.sha256((views / name).read_bytes()).hexdigest() == digest, name
    written = json.loads((views / "trellis.graph.json").read_text(encoding="ascii"))
    assert occurrences_of(written, "backward") == occurrences_of(whole.collection, "backward")
    assert record["commit"] == git(scratch_consport, "rev-parse", "HEAD").strip()
    expected_sources = {
        (
            Path(name).relative_to(scratch_consport).as_posix()
            if Path(name).is_relative_to(scratch_consport)
            else name
        ): {"sha256": digest, "uncommitted": not Path(name).is_relative_to(folder.git_root)}
        for name, digest in whole.files.items()
    }
    assert {
        entry["path"]: {key: entry[key] for key in ("sha256", "uncommitted")}
        for entry in record["source_files"]
    } == expected_sources
    assert {entry["uncommitted"] for entry in record["source_files"]} == {False, True}
    assert record["uncommitted"] is True

    repository = tmp_path / "export-record"
    opened = repository / "model"
    opened.mkdir(parents=True)
    local, sibling = opened / "source.txt", repository / "sibling.txt"
    (repository / ".gitattributes").write_text("*.txt -text\n", encoding="utf-8")
    for path in (local, sibling):
        path.write_bytes(b"held source\r\n")
    init_repository(repository)
    other = tmp_path / "other-repository"
    other.mkdir()
    other_source = other / "source.txt"
    other_source.write_text("other source\n", encoding="utf-8")
    init_repository(other)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside source\n", encoding="utf-8")
    untracked = repository / "untracked.txt"
    untracked.write_text("untracked source\n", encoding="utf-8")
    held_files = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (local, sibling, other_source, outside, untracked)
    }
    clean_files = {str(path): held_files[str(path)] for path in (local, sibling)}
    for dirty in (False, True):
        if dirty:
            sibling.write_text("changed after reading\n", encoding="utf-8")
        inputs = held_files if dirty else clean_files
        exported = model.export_trellis(
            model.open_folder(opened),
            whole.trellis,
            source=PORT_CONS,
            restriction=None,
            direction="backward",
            files=inputs,
        )
        provenance = json.loads(exported.read_text(encoding="utf-8"))
        expected = {"source.txt": False, str(sibling): dirty}
        if dirty:
            expected.update({str(path): True for path in (other_source, outside, untracked)})
        assert {
            entry["path"]: entry["uncommitted"] for entry in provenance["source_files"]
        } == expected
        assert {entry["path"]: entry["sha256"] for entry in provenance["source_files"]} == {
            "source.txt" if name == str(local) else name: digest
            for name, digest in inputs.items()
        }
        assert provenance["commit"] == git(repository, "rev-parse", "HEAD").strip()
        assert provenance["uncommitted"] is dirty

    # The held local bytes differ from the next commit only in line endings.
    commit_a = git(repository, "rev-parse", "HEAD").strip()
    local.write_bytes(b"held source\n")
    git(repository, "add", "--", "model/source.txt", "sibling.txt")
    git(repository, "commit", "-q", "-m", "Change the sources after their reading")
    commit_b = git(repository, "rev-parse", "HEAD").strip()
    assert commit_b != commit_a
    assert git(repository, "status", "--porcelain", "--", "model/source.txt", "sibling.txt") == ""
    exported = model.export_trellis(
        model.open_folder(opened),
        whole.trellis,
        source=PORT_CONS,
        restriction=None,
        direction="backward",
        files=clean_files,
    )
    provenance = json.loads(exported.read_text(encoding="utf-8"))
    assert provenance["commit"] == commit_b
    assert {entry["path"]: entry["sha256"] for entry in provenance["source_files"]} == {
        "source.txt" if name == str(local) else name: digest
        for name, digest in clean_files.items()
    }
    assert {entry["path"]: entry["uncommitted"] for entry in provenance["source_files"]} == {
        "source.txt": True,
        str(sibling): True,
    }
    assert provenance["uncommitted"] is True

    unborn = tmp_path / "unborn"
    unborn.mkdir()
    assert model.init_repository(unborn).ok
    exported = model.export_trellis(
        model.open_folder(unborn),
        whole.trellis,
        source=PORT_CONS,
        restriction=None,
        direction="backward",
        files=held_files,
    )
    provenance = json.loads(exported.read_text(encoding="utf-8"))
    assert provenance["commit"] is None and provenance["uncommitted"] is True
    assert {
        entry["path"]: (entry["sha256"], entry["uncommitted"])
        for entry in provenance["source_files"]
    } == {
        name: (digest, True) for name, digest in held_files.items()
    }

    # No page test reaches a shadow root.
    for path in sorted((WORKBENCH / "tests").glob("*.py")):
        if path.name != Path(__file__).name:
            assert "shadowRoot" not in path.read_text(encoding="utf-8"), path.name

    # The cache folder is empty for the first opening and warm for the second:
    # the first server keeps the stage views and the binding, which the
    # second reads.
    durables = repository_copy(DURABLES, tmp_path / "durables")
    cache = tmp_path / "cache"
    cache.mkdir()
    entry = kept_binding_entry(cache, durables, recipe.Source("recipe", RECIPE_FILE))
    first = seconds_to_the_drawn_trellis(browser, durables, cache, tmp_path / "first.log", entry)
    written = entry.stat().st_mtime_ns
    inode = entry.stat().st_ino
    second = seconds_to_the_drawn_trellis(browser, durables, cache, tmp_path / "second.log")
    print(
        f"item 4: the durables trellis drawn after {first:.3f} s the first time and "
        f"{second:.3f} s with the cache warm, on {platform.machine()} with "
        f"{os.cpu_count()} processors"
    )
    # the second start read the binding, which marks the entry as used
    assert entry.stat().st_mtime_ns > written
    # and did not write it again, which would put another file in its place
    assert entry.stat().st_ino == inode
    assert first < 7 and second < 5

    # Model Explorer's component and its build are gone, and nothing names them
    for gone in ("bellman_workbench/view.vue", "js/model-explorer", "public/model-explorer"):
        assert not (WORKBENCH / gone).exists(), gone
    named = re.compile(
        r"view\.vue|model-explorer-visualizer|js/model-explorer|public/model-explorer|--me-"
    )
    for path in sorted(WORKBENCH.rglob("*")):
        skipped = {"node_modules", "public", "solara-cdn", "__pycache__"} & set(path.parts)
        if path.is_file() and not skipped and path.name != Path(__file__).name and path.suffix in (
            ".py", ".vue", ".css", ".md", ".js", ".mjs", ".sh", ".toml",
        ):
            assert not named.search(path.read_text(encoding="utf-8")), path
