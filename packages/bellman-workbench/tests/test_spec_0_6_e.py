"""The acceptance file of units E2 to E4 of the build of specification 0.6: the
layers button, which switches the builders the graph and Details show between
the declared builders, `stage.declared`, and the operative builders,
`stage.builder` (specification 0.6 §9; design pass 15, the development
repository's record of 21 October 2026, the build of unit E2 and the
controller's judgment). One test for each test of the record's build section,
on the consumption stage of the demonstration's folder,
`applications/cons-port/`, whose addition `stages/cons/methods.bl` opens the
policy builder with the lines of the endogenous grid method and adds the
derivative line of its decision value builder, and one test of its portfolio
stage, whose addition opens its policy builder with the share's first-order
condition. The rulings the build took are the rows SE of the development
repository's decisions file `SE-E2-to-E4.md`. When the environment variable
`BELLMAN_WORKBENCH_FRAMES` names a folder, the page tests write their frames
there."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

from workbench_support import (
    DEMONSTRATION,
    DURABLES,
    DEMONSTRATION_CONS,
    DEMONSTRATION_PORT,
    FRAME_TRACKS,
    bound_as_the_recipe_binds,
    boxes,
    choose_view,
    flow_handle,
    graph_named,
    new_tab,
    open_workbench,
    panel_head,
    property_color,
    select_node,
    status_settled_on,
    tracks_near,
    wait_until,
)

from bellman.stage import LAYER_ID_ENDING, elaborate_text, to_model_explorer
from bellman_workbench import app, model

# the policy builder's layer, and the operations its layer holds at the two levels, by their node ids
POLICY_LAYER = "policy" + LAYER_ID_ENDING
DECLARED_POLICY = ["policy:Pullback", "policy.optimality:Aggregation", "policy.optimality:Argmax", "policy:Evaluation"]
OPERATIVE_POLICY = [
    "policy.InvEuler:Aggregation",
    "policy.grid:Aggregation",
    "policy.identification:Pullback",
    "policy:Evaluation",
]
ARGMAX = "policy.optimality:Argmax"
# the portfolio stage's policy builder at the two levels: the argmax's operations, and the rows of the block of the
# share's first-order condition its addition writes
PORT_DECLARED_POLICY = ["policy:Pullback", "policy.objective:Expectation:1", "policy.objective:Argmax", "policy:Evaluation"]
PORT_OPERATIVE_POLICY = [
    "policy:Pullback",
    "policy.euler:Aggregation:1",
    "policy.euler:Expectation:1",
    "policy.euler:Aggregation",
    "policy:Evaluation",
]
# the stage file of the buffer-stock application, whose two levels are one object
BUFFER_STOCK_FILE = "declaration/stages/buffer_stock/buffer_stock.bl"
# the declared line the opened builder's Details prints under `Declared`
DECLARED_LINE = "𝑐(m) ∈ argmax_{cp ∈ Γ(m)} [𝑢(cp) + 𝑉≻(𝑔≻(m, cp))]"

# The layers button as the browser holds it: the toolbar button's place among the bar's items and the foot's
# controls, its icon, hover and disabled mark, its inner button's role and state, the computed height and color of
# its on mark, and whether the focus stands on it.
BUTTON_JS = r"""
() => {
  const host = document.querySelector('.bl-layers-button');
  if (!host) return null;
  const inner = host.shadowRoot ? host.shadowRoot.querySelector('button') : null;
  const mark = getComputedStyle(host, '::after');
  const before = host.previousElementSibling;
  return {
    icon: host.getAttribute('icon'), label: inner ? inner.getAttribute('aria-label') : null,
    title: host.getAttribute('title'),
    disabled: host.getAttribute('aria-disabled'), role: inner ? inner.getAttribute('role') : null,
    checked: inner ? inner.getAttribute('aria-checked') : null,
    after: before ? before.className : null, inBar: !!host.closest('.bl-graph-bar'),
    inFoot: !!host.closest('.bl-graph-controls'),
    markHeight: mark.content === 'none' ? null : mark.height, markColor: mark.backgroundColor,
    focused: document.activeElement === host || (host.shadowRoot && host.shadowRoot.activeElement !== null),
  };
}
"""
# the Details blocks of the selected piece, each label with the text of the block after it, the blocks of the
# editor's cursor left out
BLOCKS_JS = r"""
() => Array.from(document.querySelectorAll('.bl-panel .bl-block-label'))
  .filter((label) => !label.closest('.bl-cursor-details'))
  .map((label) => {
    const block = label.nextElementSibling;
    return [label.textContent, block ? block.textContent : null];
  })
"""
# the rows of Details, by key
ROWS_JS = r"""
() => Array.from(document.querySelectorAll('.bl-panel .bl-attribute'))
  .filter((row) => !row.closest('.bl-cursor-details'))
  .map((row) => [row.dataset.key, row.querySelector('.bl-attribute-value').textContent])
"""
# the lines from `Inputs` into the opened policy builder's first operation, each with the count its plug prints and
# its title
INTO_POLICY_JS = r"""
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge'))
  .filter((edge) => (edge.dataset.id || '').startsWith('GraphInputs::') && (edge.dataset.id || '').includes('>>policy.InvEuler'))
  .map((edge) => {
    const count = edge.querySelector('.bf-cable-count'), title = edge.querySelector('title');
    return {id: edge.dataset.id, count: count ? count.textContent : null, title: title ? title.textContent : null};
  })
"""
# The items of the graph bar but Problems, each with its box, the name where the bar draws it.
BAR_ITEMS = (
    ".bl-graph-bar:not([data-crowded]) .bl-graph-tools > .bl-graph-name,"
    " .bl-graph-tools > .bl-graph-choice > *"
)


def node_named(graph: dict, node_id: str) -> dict:
    """The node `node_id` of `graph`, a graph of a collection."""
    return next(node for node in graph["nodes"] if node["id"] == node_id)


def frame(tab, name: str) -> None:
    """Writes the frame `name` of the page where BELLMAN_WORKBENCH_FRAMES names a folder."""
    folder = os.environ.get("BELLMAN_WORKBENCH_FRAMES")
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        tab.screenshot(path=str(Path(folder) / f"{name}.png"))


def button(tab) -> dict:
    """The layers button as the browser holds it (BUTTON_JS)."""
    return tab.evaluate(BUTTON_JS)


def layer_nodes(tab, namespace: str = "policy") -> list[str]:
    """The ids of the nodes of the backward graph the region holds whose layer is `namespace`."""
    held = graph_named(flow_handle(tab, "collection"), "backward")
    return [node["id"] for node in held["nodes"] if node.get("namespace") == namespace]


def open_demonstration(tab, url: str, relpath: str = DEMONSTRATION_CONS) -> None:
    """Opens the page over the demonstration's folder at the address that names the stage file `relpath`, the
    consumption stage's by default, as the desktop shell's link `bellman://open?folder=…&file=…&line=1` opens it
    (E4; SE-24), and waits for the stage's graph."""
    open_workbench(tab, f"{url}?file={relpath}")
    wait_until(lambda: status_settled_on(tab, relpath), 90.0, f"{relpath} shown")
    wait_until(lambda: len(layer_nodes(tab)) == 4, 30.0, "the policy builder's layer drawn")


def select_layer(tab) -> None:
    """Selects the policy builder's layer and waits for its Details."""
    select_node(tab, POLICY_LAYER, "backward")
    wait_until(lambda: flow_handle(tab, "selection") == POLICY_LAYER, 10.0, "the policy layer selected")
    wait_until(lambda: panel_head(tab).startswith("policy"), 10.0, "the policy layer's Details")


def test_item_1_the_page_opens_on_the_consumption_stage_with_the_button_off(browser, server_on, demonstration_folder):
    """E2 item 1 and E4 (R7, R10; SE-2, SE-3, SE-6, SE-15). The page over the
    demonstration's folder opens on the consumption stage with the button
    `Operative builders` off, at the canvas's foot after `Perch overlays`: the
    Codicon `layers-dot`, the hover `Show operative builders`, its inner button
    a switch that is not checked. The graph holds the declared policy builder,
    the argmax's four operations, and Details of its layer prints no row
    `method`, since the declared level is the stage file elaborated alone
    (specification 0.7, the implementation specification §U2)."""
    context, tab = new_tab(browser)
    try:
        open_demonstration(tab, server_on(demonstration_folder))
        found = button(tab)
        assert found is not None
        assert (found["icon"], found["label"], found["title"]) == (
            "layers-dot",
            "Operative builders",
            "Show operative builders",
        ), found
        assert (found["role"], found["checked"], found["disabled"]) == ("switch", "false", None), found
        assert found["inFoot"] and "bl-overlays-button" in found["after"], found
        assert layer_nodes(tab) == DECLARED_POLICY
        select_layer(tab)
        rows = dict(tab.evaluate(ROWS_JS))
        assert "method" not in rows, rows
        labels = [label for label, _ in tab.evaluate(BLOCKS_JS)]
        assert labels == ["Signature"], labels
        frame(tab, "1600-consumption-button-off")
    finally:
        context.close()


def test_item_2_a_click_turns_the_button_on_and_space_turns_it_off_with_the_focus_kept(
    browser, server_on, demonstration_folder
):
    """E2 item 2 (SE-4, SE-9; the judgment's first and third rulings). A click
    turns the button on: the Codicon `layers-active`, the hover `Show declared
    builders`, the switch checked and the 2-px accent line at its foot. The
    policy layer then holds the block's rows and Inputs carries 𝑉≻ alone, the
    one value the header lists, whose derivative the block reads as the term
    `D_{a}V[>]` (AMD-MB-001 §4.2). Details of the layer prints the signature
    and, after it, `Declared` with the stage file's line, `Conditions` with
    `egm-eligibility` and `Method` with the method word, the grid and the
    handler the addition types, and no row `method`; the accessibility tree
    reads `switch "Operative builders" [checked]`. Tab from `Perch overlays`
    reaches the button, and Space turns it off, the focus kept on it. The line
    into the opened builder is the one wire its header lists, 𝑉≻, its title
    naming it (AMD-MB-001 §5.4, which retired the bundle of the judgment's
    first ruling with the marginal wires)."""
    context, tab = new_tab(browser)
    try:
        open_demonstration(tab, server_on(demonstration_folder))
        select_layer(tab)
        tab.click(".bl-layers-button")
        wait_until(lambda: button(tab)["icon"] == "layers-active", 10.0, "the button on")
        found = button(tab)
        assert (found["title"], found["checked"]) == ("Show declared builders", "true"), found
        assert found["markHeight"] == "2px" and found["markColor"] == property_color(tab, "--bl-accent"), found
        wait_until(lambda: layer_nodes(tab) == OPERATIVE_POLICY, 30.0, "the opened policy builder")
        held = graph_named(flow_handle(tab, "collection"), "backward")
        inputs = next(node for node in held["nodes"] if node["id"] == "GraphInputs")
        labels = [
            next(item["value"] for item in port["attrs"] if item["key"] == "label")
            for port in inputs["outputsMetadata"]
        ]
        assert labels == ["𝑉≻(a)"], labels
        # the line into the opened builder, the one wire its header lists (AMD-MB-001 §5.4)
        lines = tab.evaluate(INTO_POLICY_JS)
        assert [(line["count"], line["title"]) for line in lines] == [(None, "𝑉≻(a)")], lines
        wait_until(lambda: "Declared" in [label for label, _ in tab.evaluate(BLOCKS_JS)], 10.0, "Declared")
        blocks = dict(tab.evaluate(BLOCKS_JS))
        assert list(blocks) == ["Signature", "Declared", "Conditions", "Method"], list(blocks)
        assert "𝑉≻" in blocks["Signature"] and "𝑑𝑉≻" not in blocks["Signature"], blocks
        assert blocks["Declared"].strip() == DECLARED_LINE, blocks
        assert "egm-eligibility" in blocks["Conditions"], blocks
        method = blocks["Method"]
        assert method.startswith("!egm") and '"cons-port:egm"' in method, blocks
        assert "method" not in dict(tab.evaluate(ROWS_JS))
        tab.locator(".bl-panel .bl-block-label", has_text="Declared").scroll_into_view_if_needed()
        # the frame after Details has drawn the opened builder's blocks
        tab.wait_for_timeout(500)
        frame(tab, "1600-consumption-button-on")
        snapshot = tab.locator(".bl-graph-controls").aria_snapshot()
        assert '- switch "Operative builders" [checked]' in snapshot, snapshot
        # the keyboard reaches the button from `Perch overlays`, the control before it
        # the focus on the switch of `Perch overlays`, inside its toolbar button, and Tab from it
        tab.locator(".bl-overlays-button").evaluate("(host) => host.shadowRoot.querySelector('button').focus()")
        tab.keyboard.press("Tab")
        wait_until(lambda: button(tab)["focused"], 5.0, "the focus on the layers button")
        tab.keyboard.press("Space")
        wait_until(lambda: button(tab)["icon"] == "layers-dot", 10.0, "the button off by Space")
        assert button(tab)["checked"] == "false"
        assert button(tab)["focused"], button(tab)
        wait_until(lambda: layer_nodes(tab) == DECLARED_POLICY, 30.0, "the declared policy builder again")
    finally:
        context.close()


def test_the_portfolio_stage_opens_its_policy_builder_with_the_block_of_the_first_order_condition(
    browser, server_on, demonstration_folder
):
    """E3, the portfolio stage on (SE-25). The page opens the portfolio stage
    of the demonstration with the button off, the policy layer holding the
    argmax's operations; the button acts there, and on, the layer holds the
    rows of the share's first-order condition its addition writes, and Details
    of the layer prints `Declared` with the stage file's argmax and a section
    `Method` with the method word and the handler the addition types."""
    context, tab = new_tab(browser)
    try:
        open_demonstration(tab, server_on(demonstration_folder), DEMONSTRATION_PORT)
        assert layer_nodes(tab) == PORT_DECLARED_POLICY
        found = button(tab)
        assert (found["icon"], found["disabled"], found["title"]) == (
            "layers-dot",
            None,
            "Show operative builders",
        ), found
        select_layer(tab)
        tab.click(".bl-layers-button")
        wait_until(lambda: button(tab)["icon"] == "layers-active", 10.0, "the button on")
        wait_until(lambda: layer_nodes(tab) == PORT_OPERATIVE_POLICY, 30.0, "the opened policy builder")
        wait_until(lambda: "Declared" in [label for label, _ in tab.evaluate(BLOCKS_JS)], 10.0, "Declared")
        blocks = tab.evaluate(BLOCKS_JS)
        assert [label for label, _ in blocks][:2] == ["Signature", "Declared"], blocks
        assert any(
            label == "Method"
            and text.startswith("!time_iteration")
            and '"cons-port:share_search"' in text
            for label, text in blocks
        ), blocks
        tab.locator(".bl-panel .bl-block-label", has_text="Declared").scroll_into_view_if_needed()
        # the frame after Details has drawn the opened builder's blocks
        tab.wait_for_timeout(500)
        frame(tab, "1600-portfolio-button-on")
    finally:
        context.close()


def test_item_3_a_selection_the_other_level_holds_stays_and_one_it_does_not_becomes_its_builder(
    browser, server_on, demonstration_folder
):
    """E2 item 3 (SE-7). The selected policy layer stays selected across the switch on and back; the selected
    argmax, which the operative level does not hold, becomes the policy builder's layer when the button is
    turned on."""
    context, tab = new_tab(browser)
    try:
        open_demonstration(tab, server_on(demonstration_folder))
        select_layer(tab)
        tab.click(".bl-layers-button")
        wait_until(lambda: layer_nodes(tab) == OPERATIVE_POLICY, 30.0, "the opened policy builder")
        assert flow_handle(tab, "selection") == POLICY_LAYER
        tab.click(".bl-layers-button")
        wait_until(lambda: layer_nodes(tab) == DECLARED_POLICY, 30.0, "the declared policy builder")
        assert flow_handle(tab, "selection") == POLICY_LAYER
        select_node(tab, ARGMAX, "backward")
        wait_until(lambda: flow_handle(tab, "selection") == ARGMAX, 10.0, "the argmax selected")
        tab.click(".bl-layers-button")
        wait_until(lambda: layer_nodes(tab) == OPERATIVE_POLICY, 30.0, "the opened policy builder")
        wait_until(lambda: flow_handle(tab, "selection") == POLICY_LAYER, 10.0, "the policy layer selected")
        wait_until(lambda: panel_head(tab).startswith("policy"), 10.0, "the policy layer's Details")
    finally:
        context.close()


def test_item_4_the_button_does_not_act_where_the_levels_are_one_or_the_initial_diagram_is_shown(
    browser, server_on, demonstration_folder, buffer_stock_folder
):
    """E2 item 4 (SE-5). On `buffer_stock.bl`, which no source binds, the two levels are one object and the button
    does not act, its hover `No method adds operations`; on the consumption stage it does not act while `Initial`
    is chosen, its hover `Applies to the builders graph`, and keeps its state. Disabled, the switch is read in the
    accessibility tree of the bar or the foot as the snapshot prints it."""
    context, tab = new_tab(browser)
    try:
        open_workbench(tab, server_on(buffer_stock_folder))
        wait_until(lambda: status_settled_on(tab, BUFFER_STOCK_FILE), 90.0, "buffer_stock.bl shown")
        found = button(tab)
        assert (found["disabled"], found["title"]) == ("true", "No method adds operations"), found
        tab.click(".bl-layers-button")
        tab.wait_for_timeout(500)
        assert button(tab)["checked"] == "false"
        place = ".bl-graph-bar" if found["inBar"] else ".bl-graph-controls"
        print(f"the accessibility tree of {place}:\n{tab.locator(place).aria_snapshot()}")
        open_demonstration(tab, server_on(demonstration_folder))
        tab.click(".bl-layers-button")
        wait_until(lambda: button(tab)["icon"] == "layers-active", 10.0, "the button on")
        choose_view(tab, "initial", "backward")
        wait_until(lambda: button(tab)["disabled"] == "true", 10.0, "the button disabled in the Initial view")
        found = button(tab)
        assert (found["title"], found["checked"]) == ("Applies to the builders graph", "true"), found
        frame(tab, "1600-initial-button-disabled")
        choose_view(tab, "operator", "backward")
        wait_until(lambda: button(tab)["disabled"] is None, 10.0, "the button acting again")
        wait_until(lambda: layer_nodes(tab) == OPERATIVE_POLICY, 30.0, "the opened policy builder kept")
    finally:
        context.close()


def test_item_5_the_button_stands_at_the_canvas_s_foot_and_the_bar_keeps_its_rows(
    browser, server_on, demonstration_folder
):
    """E2 item 5 (amendment 02 ruling 5; SE-15 and the controller's second ruling). In the graph bar the button took
    the bar to a second row at the 314-px graph column and at the 357-px one, its items 82, 87, 24 and 100 px wide
    with the view tabs on the second row; so it stands at the canvas's foot after `Perch overlays` at every width.
    With Matsya's column open, at 1600 px the graph column is 357 px wide and the bar stands in one row of 36 px; at
    1460 px it is 314 px wide, and the bar's items, their widths and the Problems control's are printed for the
    report."""
    context, tab = new_tab(browser)
    try:
        open_demonstration(tab, server_on(demonstration_folder))
        # Matsya's column stands open in a stage's view, as the page opens
        for width in (1600, 1460):
            tab.set_viewport_size({"width": width, "height": 1000})
            wait_until(lambda w=width: tracks_near(tab, FRAME_TRACKS[w, False]), 10.0, f"the frame at {width} px")
            tab.wait_for_timeout(300)
            found = boxes(tab, BAR_ITEMS)
            bar = boxes(tab, ".bl-graph-bar")[0]
            problems = boxes(tab, ".bl-graph-bar > .bl-errors")[0]
            centers = [item["top"] + item["height"] / 2 for item in found]
            print(
                f"unit E: at {width} px the graph column is {bar['width']} px and the bar {bar['height']} px high; "
                f"its items {[round(item['width']) for item in found]} px, Problems {round(problems['width'])} px"
            )
            assert button(tab)["inFoot"] and not button(tab)["inBar"], button(tab)
            if width == 1600:
                assert bar["height"] == 36 and max(centers) - min(centers) <= 1, (found, bar)
            frame(tab, f"{width}-bar")
    finally:
        context.close()


def test_item_6_the_exporter_answers_the_declared_builders_under_the_keyword_declared(demonstration_folder):
    """E2 item 6 (SE-8, SE-19, SE-26). For a stage with nothing bound, `to_model_explorer(stage, declared=True)` equals
    `to_model_explorer(stage)`; for the consumption stage bound as the demonstration's recipe binds it by the
    addition beside it, the declared collection holds the argmax's operations in the policy builder's layer, the
    stage file elaborated alone, so no row `method` (specification 0.7, the implementation specification §U2), and
    keeps the stage's label; the operative collection holds the addition's lines, the layer's rows naming the method
    word, the grid and the handler the addition types, the reading port of its first operation naming no unread
    input, since the one input the header lists, `𝑉≻`, is read by the derivative term `D_{a}V[>]` (AMD-MB-001
    §4.2), and the decision builder's Evaluation names the one method typed there, `!Linear`."""
    text = (demonstration_folder / DEMONSTRATION_CONS).read_text(encoding="utf-8")
    unbound = elaborate_text(text, str(demonstration_folder / DEMONSTRATION_CONS))
    assert dataclasses.asdict(to_model_explorer(unbound, declared=True)) == dataclasses.asdict(
        to_model_explorer(unbound)
    )
    stage = bound_as_the_recipe_binds(demonstration_folder, text, DEMONSTRATION_CONS)
    declared = dataclasses.asdict(to_model_explorer(stage, declared=True))
    operative = dataclasses.asdict(to_model_explorer(stage))
    assert declared["label"] == operative["label"] and operative["label"].startswith("cons ")

    def policy(collection):
        graph = graph_named(collection, "backward")
        return (
            [node["id"] for node in graph["nodes"] if node.get("namespace") == "policy"],
            graph["groupNodeAttributes"]["policy"],
        )

    nodes, rows = policy(declared)
    assert nodes == DECLARED_POLICY
    assert "method" not in rows, rows
    nodes, rows = policy(operative)
    assert nodes == OPERATIVE_POLICY
    assert (rows["method"], rows["handler"]) == ("!egm", "cons-port:egm"), rows
    assert rows["grid"].startswith("!Cartesian(a=("), rows
    # the decision builder's Evaluation holds the one representation its entry types (D4), which its node names
    evaluation = node_named(graph_named(operative, "backward"), "cntn_to_dcsn:Evaluation")
    assert {item["key"]: item["value"] for item in evaluation["attrs"]}["method"] == "!Linear"
    assert evaluation["label"].endswith(" · !Linear"), evaluation["label"]
    # the one input the block's header lists is read by the derivative term, so no reading port of the opened
    # builder's first operation names an unread input (AMD-MB-001 §4.2)
    graph = graph_named(operative, "backward")
    first = next(node for node in graph["nodes"] if node["id"] == OPERATIVE_POLICY[0])
    ports = {port["id"]: {item["key"]: item["value"] for item in port["attrs"]} for port in first["inputsMetadata"]}
    assert not any("unread" in attributes for attributes in ports.values()), ports
    graph = graph_named(declared, "backward")
    assert not any(
        item["key"] == "unread" for node in graph["nodes"] for port in node.get("inputsMetadata") or [] for item in port["attrs"]
    )


def test_the_two_levels_are_one_where_no_bound_method_block_opens_a_builder():
    """The declared and the operative builders are two levels only where a
    solution method's lines open a builder (specification 0.6 §7; SE-5;
    specification 0.7 D8). The durables model's `disc`, with its addition
    read, carries `!deterministic` and no line, so its levels are one and
    the page shows its operative builders; the demonstration's consumption
    stage, whose addition writes the endogenous grid method's lines in the
    block `policy`, has two (SE-37)."""
    disc = DURABLES / "declaration/stages/disc/disc.bl"
    stage = elaborate_text(disc.read_text(encoding="utf-8"), str(disc))
    assert not model.two_levels(stage.methodize(str(disc.parent / "methods.bl")))
    cons = DEMONSTRATION / DEMONSTRATION_CONS
    stage = elaborate_text(cons.read_text(encoding="utf-8"), str(cons))
    assert model.two_levels(stage.methodize(str(cons.parent / "methods.bl")))


def test_the_layers_button_is_a_toggle_of_the_page_and_off_at_the_start():
    """SE-6. The page's state `builders_operative` is False at the start and `toggle_builders` turns it; the
    button's hovers are the four of LAYERS_HOVERS."""
    assert app.builders_operative.value is False
    app.toggle_builders()
    try:
        assert app.builders_operative.value is True
    finally:
        app.toggle_builders()
    assert app.builders_operative.value is False
    assert set(app.LAYERS_HOVERS.values()) == {
        "Show operative builders",
        "Show declared builders",
        "No method adds operations",
        "Applies to the builders graph",
    }
