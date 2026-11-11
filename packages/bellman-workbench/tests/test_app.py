"""The page's components rendered without a browser, by Solara's test
renderer `solara.render`.

`GraphChoice` offers two selects, the kind of graph, `operator` or
`initial`, and the direction, `backward` or `forward`, and the switch
`stage │ trellis` (spec 0.4 §2.1; R-D56; unit K, K-D20). Each pair of words
shows one graph. The switch's `trellis` is disabled without a composition,
and its `stage` while the editor holds no stage file.

`legend_entries` answers the legend of the graph drawn (AMD-MI-001,
decisions A1-D2 and A1-D4), read from the collection the page holds: on
`cons` with its methods, on the trellis of `port-cons.yml` and on the
backward initial diagram.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import shutil
import threading
import time
from types import SimpleNamespace

import ipyvue
import ipyvuetify as v
import pytest
import reacton.ipyvuetify as rv
import solara
from workbench_support import (
    CAGETTI_DENARDI,
    CONS,
    CONS_PATH,
    CONS_PORT_RECIPE,
    DEMO_STAGES,
    ENTREPRENEUR_DEATH_PATH,
    KEEPER_CONS,
    NOPORT_ID,
    PENSION_RETIREMENT,
    PENSIONS_RECIPE,
    PENSIONS_WORKING_YEARS,
    PORT,
    PORT_CONS,
    PORT_CONS_RECIPE,
    RECIPE_FILE,
    RETIRE_CHOICE,
    ROOT,
    SHARED_CONS,
    TENURE,
    WORKER_SAVING,
    applications_copy,
    applied,
    changed_lines,
    clear_gesture_state,
    clear_trellis_state,
    collection_unjoined_ports,
    connected_event,
    drawn_text,
    dropped_event,
    edited,
    emptied_port_cons,
    emptied_portfolio_with_entry_connectors,
    file_bytes,
    filled,
    gesture_trellis,
    join_labels,
    open_rendered_recipe_row,
    pensions_copy,
    remove_chosen_join,
    rendered_recipe_rows,
    shown_of,
    shown_panel,
    wait_until,
    with_required_connectors,
    written_from_the_forms,
)

from bellman.refusals import TARGET_RULES, TargetError
from bellman.stage import LAYER_ID_ENDING, elaborate_text, source_spans
from bellman.trellis import load_recipe
from bellman_workbench import app, creation, icons, model, navigation, recipe, trellis

# the recipe of a folder in the one layout, as the source of its trellis
RECIPE = recipe.Source("recipe", RECIPE_FILE)

# the methods file of the consumption stage, the addition beside its stage file
CONS_METHODS = ROOT / "applications/portfolio-choice/declaration/stages/cons/methods.bl"


def view_selects(rendered) -> dict:
    """The selects of the graph's bar that `rendered` draws, each a field of
    VSCode Elements (field.vue; design pass 8 §§4 and 6), by its class,
    `bl-view-kind` or `bl-view-direction`."""
    return {
        name: widget
        for widget in rendered.find(ipyvue.VueTemplate).widgets
        for name in ("bl-view-kind", "bl-view-direction")
        if name in (getattr(widget, "classes", "") or "").split()
    }


def view_tabs(rendered) -> list:
    """The view tabs `Stage` and `Trellis` that `rendered` draws, VSCode
    Elements' tab headers (design pass 8 §§4 and 6), in their order."""
    return rendered.find(v.Html, tag="vscode-tab-header").widgets


def press_tab(tab) -> None:
    """A click on the view tab `tab`, stopped at the tab (`app.ViewTab`)."""
    tab.fire_event("click.stop", {})


def test_the_header_offers_the_two_selects_and_the_trellis_button():
    """Spec 0.4 §2.1; R-D56; amendment 02 rulings 4 and 5; design pass 8
    §§4 and 6: in a stage's view the select `graph`, `Operator` or
    `Initial`, and the select `direction`, `Backward` or `Forward`, each a
    select of VSCode Elements with its hover and no label, show the graph
    shown; each pair of words shows its graph, the four graphs of a stage,
    and no choice is a place of the history. The view tabs `Stage` and
    `Trellis` stand after them (unit K, K-D20), `Stage` marked and
    `Trellis` not acting without a composition. In the trellis view the
    select `graph` stands as well (design pass 14 §7; S-D12), `Initial`
    showing the trellis's initial diagram of the direction, the direction
    shows the trellis's graph and `Trellis` is marked."""
    app.view_mode.value = "stage"
    app.graph.value = "backward"
    history = app.history.value
    header = app.GraphChoice("backward", "stage", True, False, True)
    _, rendered = solara.render(header, handle_error=False)
    try:
        selects = view_selects(rendered)
        kind, direction = selects["bl-view-kind"], selects["bl-view-direction"]
        assert (kind.options, direction.options) == (
            ["Operator", "Initial"],
            ["Backward", "Forward"],
        )
        assert (kind.value, direction.value) == ("Operator", "Backward")
        assert (kind.hover, direction.hover) == (
            app.HEADER_SELECT_HOVERS["graph"],
            app.HEADER_SELECT_HOVERS["direction"],
        )
        assert kind.label == "" and direction.label == ""
        stage, button = view_tabs(rendered)
        assert stage.children == ["Stage"] and "bl-active" in stage.class_.split()
        assert button.children == ["Trellis"] and button.attributes["aria-disabled"] == "true"
        shown = {}
        for chosen_kind in ("operator", "initial"):
            for chosen_direction in ("backward", "forward"):
                kind.vue_entered(chosen_kind.capitalize())
                direction.vue_entered(chosen_direction.capitalize())
                shown[chosen_kind, chosen_direction] = app.graph.value
        assert shown == {
            ("operator", "backward"): "backward",
            ("operator", "forward"): "forward",
            ("initial", "backward"): "backward initial diagram",
            ("initial", "forward"): "forward initial diagram",
        }
        assert app.history.value is history
    finally:
        rendered.close()
        app.graph.value = "backward"
    app.view_mode.value = "trellis"
    header = app.GraphChoice("backward", "trellis", True, True, True)
    _, rendered = solara.render(header, handle_error=False)
    try:
        selects = view_selects(rendered)
        assert list(selects) == ["bl-view-kind", "bl-view-direction"]
        selects["bl-view-direction"].vue_entered("Forward")
        assert app.graph.value == "forward"
        selects["bl-view-kind"].vue_entered("Initial")
        assert app.graph.value == "forward initial diagram"
        selects["bl-view-kind"].vue_entered("Operator")
        assert app.graph.value == "forward"
        stage, button = view_tabs(rendered)
        assert "bl-active" not in stage.class_.split()
        assert "bl-active" in button.class_.split()
        assert button.attributes["aria-disabled"] == "false"
    finally:
        rendered.close()
        app.view_mode.value, app.graph.value = "stage", "backward"
        app.graph.value = "backward"


def test_the_legend_of_cons_with_its_methods_lists_its_levels_methods_and_marks(cons_text):
    """On `cons` with its methods, the legend of `backward` is titled by the
    collection's label, `cons methodized`, and lists the three levels the
    graph draws, each with its swatch, the two bound methods by tag and
    place, and the three marks its labels hold, each with its sentence; the
    perches only while the overlays are on, each with its overlay name
    (`model.edge_overlays`) as its swatch key, `arrival`,
    `decision` and `continuation`. The legend of `forward` lists the method
    bound at the builder `arvl_to_dcsn` and no mark `· !tag`, since no
    label of the forward graph holds one."""
    # a stage of its own, since `methodize` binds the stage it is given in
    # place and the fixture `cons` is the session's
    methodized = elaborate_text(cons_text, CONS_PATH).methodize(str(CONS_METHODS))
    collection = model.collection(methodized)
    title, groups = app.legend_entries(collection, "backward", None)
    assert title == "cons methodized"
    assert [(entry.text, entry.swatch) for entry in groups["levels"]] == [
        ("builder", "builder"),
        ("primitive operator", "operator"),
        ("builder's output", "output"),
    ]
    # each word at the place its addition types it (specification 0.7)
    assert [entry.text for entry in groups["methods"]] == [
        "!Linear  cntn_to_dcsn:Evaluation",
        "!egm  policy",
    ]
    assert [entry.text for entry in groups["marks"]] == ["· !tag", "at 𝑐", "𝑔≺, 𝑔≻"]
    assert all(entry.sentence for entry in groups["marks"])
    assert groups["perches"] == groups["roles"] == []
    overlays = model.edge_overlays(methodized)
    _, with_overlays = app.legend_entries(collection, "backward", overlays)
    assert [(entry.text, entry.swatch) for entry in with_overlays["perches"]] == [
        ("arrival", "arrival"),
        ("decision", "decision"),
        ("continuation", "continuation"),
    ]
    _, forward = app.legend_entries(collection, "forward", None)
    assert [entry.text for entry in forward["levels"]] == ["builder", "builder's output"]
    assert [entry.text for entry in forward["methods"]] == ["!deterministic  arvl_to_dcsn"]
    assert [entry.text for entry in forward["marks"]] == ["at 𝑐", "𝑔≺, 𝑔≻"]


def test_the_legend_of_a_trellis_lists_each_place_of_a_bound_method_once(consport_folder):
    """On the trellis of `port-cons.yml`, whose six periods each hold the
    stages `port`, `cons` and `disc`, the legend of `backward` lists the
    levels from the period to the builder's output, and each bound method's
    tag and place once, though six occurrences hold it: the place is named
    with its stage's key and without its period, so that the evaluations of
    `port` and of `cons`, each `cntn_to_dcsn:Evaluation` within its stage,
    read apart."""
    folder = model.open_folder(consport_folder)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PORT_CONS_RECIPE)).shown
    title, groups = app.legend_entries(shown.collection, "backward", None)
    assert title == shown.collection["label"]
    assert [(entry.text, entry.swatch) for entry in groups["levels"]] == [
        ("period", "period"),
        ("stage occurrence", "stage"),
        ("builder", "builder"),
        ("primitive operator", "operator"),
        ("builder's output", "output"),
    ]
    # each word at the place the stage's addition types it (specification
    # 0.7), the portfolio stage solved by time iteration on its policy
    places = [entry.text for entry in groups["methods"]]
    assert sorted(places) == [
        "!Linear  cons/cntn_to_dcsn:Evaluation",
        "!Linear  port/cntn_to_dcsn:Evaluation",
        "!egm  cons/policy",
        "!gauss_hermite  port/cntn_to_dcsn.value:Expectation:1",
        "!gauss_hermite  port/policy.euler:Expectation:1",
        "!time_iteration  port/policy",
    ]
    # the graph's `method` rows, of its nodes and of its layers, are six
    # times as many: each period holds every place once
    (backward,) = [graph for graph in shown.collection["graphs"] if graph["id"] == "backward"]
    rows = [
        item for node in backward["nodes"] for item in node["attrs"] if item["key"] == "method"
    ]
    rows += [attrs for attrs in backward["groupNodeAttributes"].values() if "method" in attrs]
    assert len(rows) == 6 * len(places)


def test_the_legend_of_an_initial_diagram_lists_each_role_with_its_fields(cons_text):
    """The legend of `backward initial diagram` of `cons` lists its levels,
    the perches, the fields and the blocks, and each role of its fields with
    the fields' labels, `value  V≻, V, V≺`, a value's derivative being a
    term of its wire and no field (AMD-MB-001); no method and no mark, since
    the diagram carries none."""
    # a stage of its own, as in the legend of cons with its methods
    stage = elaborate_text(cons_text, CONS_PATH).methodize(str(CONS_METHODS))
    collection = model.collection(stage)
    _, groups = app.legend_entries(collection, "backward initial diagram", None)
    assert [(entry.text, entry.swatch) for entry in groups["levels"]] == [
        ("perch", "perch"),
        ("field", "field"),
        ("block", "block"),
    ]
    assert [entry.text for entry in groups["roles"]] == ["value  V≻, V, V≺", "control  c"]
    assert groups["methods"] == groups["marks"] == []


def test_k_the_switch_shows_the_trellis_and_the_stage_again():
    """Where the folder holds a source of a trellis the view's bar shows the
    view tabs `Stage` and `Trellis` (design pass 8 §§4 and 6): a click on
    `Trellis` shows the trellis view of the folder's first source, and a
    second click on it changes nothing; with a stage file open, a click on
    `Stage` shows the stage again, the file open unchanged (spec 0.4 §2.1;
    R-D56; unit K, K-D20)."""
    first = recipe.Source("recipe", PORT_CONS_RECIPE)
    app.sources.value = [first]
    try:
        _, rendered = solara.render(app.ViewSwitch(True, True, False), handle_error=False)
        try:
            stage, button = view_tabs(rendered)
            assert (stage.children, button.children) == (["Stage"], ["Trellis"])
            press_tab(button)
            assert (app.view_mode.value, app.source.value, app.graph.value) == (
                "trellis",
                first,
                "backward",
            )
            press_tab(button)
            assert app.view_mode.value == "trellis"
            app.open_path.value = CONS
            press_tab(stage)
            assert (app.view_mode.value, app.open_path.value) == ("stage", CONS)
        finally:
            rendered.close()
    finally:
        app.sources.value, app.source.value, app.head.value = [], None, None
        app.view_mode.value, app.open_path.value = "stage", None


def test_b_the_status_line_of_a_trellis_names_its_file_its_bindings_and_its_counts(
    consport_folder,
):
    """The status line of the trellis view (specification §2.5 and §3.1;
    spec 0.4 §5.7; design pass §1 item 10, unit K, Task 6): the line, the
    file, `trellis`, the verbs applied and the loop's seconds, and then the
    rest, the periods and the occurrences and the unjoined fields of the
    forward graph (amendment 02, recommendation 17), none in lesson 05's
    trellis, whose two ends the checklist's rule does not count (unit L,
    Task 21), every term defined; where the line with the verbs
    does not fit, the verbs head the rest (`narrow_status_parts`); before a
    reading stands, the file and the word `refused` of a refused reading,
    and no rest, which the narrow form leaves as it is."""
    outcome = trellis.show_trellis(
        model.open_folder(consport_folder), recipe.Source("recipe", PORT_CONS_RECIPE)
    )
    line, rest = app.trellis_status_parts(outcome, outcome.shown)
    seconds = f"{outcome.shown.seconds:.2f} s"
    assert "".join(text for text, _ in line) == (
        f"{PORT_CONS_RECIPE} · trellis · calibrated, methodized, configured · loop {seconds}"
    )
    assert "".join(text for text, _ in rest) == (
        " · 6 periods, 18 occurrences · 0 unjoined internal entry fields"
    )
    assert all(term in app.TERMS for _, term in line + rest if term)
    narrow_line, narrow_rest = app.narrow_status_parts(line, rest)
    assert "".join(text for text, _ in narrow_line) == f"{PORT_CONS_RECIPE} · trellis · loop {seconds}"
    assert "".join(text for text, _ in narrow_rest) == (
        " · calibrated, methodized, configured · 6 periods, 18 occurrences · 0 unjoined internal entry fields"
    )
    refused = trellis.TrellisOutcome(None, model.diagnostic_of(ValueError("no")), None, 0.1, {})
    app.source.value = recipe.Source("trellis", "declaration/trellis.yml")
    try:
        line, rest = app.trellis_status_parts(refused, None)
        assert "".join(text for text, _ in line) == "declaration/trellis.yml · refused"
        assert rest == []
        assert app.narrow_status_parts(line, rest) == (line, [])
    finally:
        app.source.value = None


def test_b_a_stage_elaborated_in_the_trellis_view_does_not_mark_the_view_as_drawing(
    app_state, pension_folder
):
    """With the pension recipe's trellis shown, a stage file opened in the
    editor is elaborated by the loop and its result recorded, and the view
    is not marked as drawing: the browser holds the trellis's collection, so
    no processed event would clear the mark, and the trellis's status line
    would never settle (specification §2.5)."""
    stage_file = WORKER_SAVING
    app_state(pension_folder)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"
    try:
        app.open_file(stage_file)
        app.drawing.value = False
        app.run_loop()
        assert app.shown.value is not None and app.shown.value.path == stage_file
        assert app.drawing.value is False
    finally:
        app.source.value, app.view_mode.value, app.open_path.value = None, "stage", None
        app.buffers.value, app.results.value, app.shown.value = {}, {}, None
        app.drawing.value = False


def test_b_a_new_trellis_reaches_the_view_already_marked_as_drawing(app_state, lifecycle_folder):
    """A reading that records a new trellis in the trellis view marks the
    view as drawing before the view is given the trellis's collection, so
    that the view's processed event, which can only follow the collection,
    clears the mark; a mark set after the collection stood on the status
    line for good whenever the view processed the collection first, as it
    did for the pension trellis restricted to `periods 1–1` with its
    refusing node selected (specification §2.5)."""
    app_state(lifecycle_folder)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"
    marks = []
    unsubscribe = app.trellis_shown.subscribe(lambda shown: marks.append(app.drawing.value))
    try:
        app.drawing.value = False
        assert app.run_trellis().shown is app.trellis_shown.value
        assert marks == [True]
        app.on_processed({"graphId": "backward"})
        assert app.drawing.value is False
    finally:
        unsubscribe()
        app.source.value, app.view_mode.value = None, "stage"
        app.trellis_shown.value, app.trellis_outcome.value = None, None
        app.trellis_seen.value, app.drawing.value = {}, False


def test_b_a_draft_trellis_is_read_again_once_a_file_it_read_is_corrected_and_saved(
    monkeypatch, refused_pension, app_state
):
    """The pension copy whose terminal connector names no field is shown
    with a diagnostic; the watcher compares the files that reading read,
    the recipe, the trellis file, the period file, the four stage files,
    their four additions and the two saving stages' settings files,
    so the corrected `declaration/trellis.yml`, saved as the editor saves it,
    raises the count once, and the next reading removes that diagnostic.
    The trellis re-elaborates when a file the model reads is saved
    (specification §3.1)."""
    folder = model.open_folder(refused_pension)
    app_state(refused_pension)
    monkeypatch.setattr(app, "WATCH_SECONDS", 0.05)
    app.source.value = RECIPE
    cancel = threading.Event()
    watcher = threading.Thread(target=app.watch, args=(cancel,))
    try:
        draft = app.run_trellis()
        assert draft.refusal is None and app.trellis_shown.value is draft.shown
        assert ("endpoint-unresolved", "periods[0].connectors[0]") in {
            (diagnostic.rule, diagnostic.address)
            for diagnostic in draft.shown.selection.diagnostics
        }
        root = refused_pension.resolve() / "declaration"
        assert set(app.trellis_seen.value) == {
            str(root / name)
            for name in (
                "spec.yml",
                "trellis.yml",
                "period.yml",
                "stages/worker_saving/worker_saving.bl",
                "stages/retire_choice/retire_choice.bl",
                "stages/retiree_saving/retiree_saving.bl",
                "stages/terminal/terminal.bl",
                # the four stages' additions and the two saving stages'
                # settings files, which the recipe names (decision S7-W2)
                "stages/worker_saving/methods.bl",
                "stages/retire_choice/methods.bl",
                "stages/retiree_saving/methods.bl",
                "stages/terminal/methods.bl",
                "settings/worker_saving.yml",
                "settings/retiree_saving.yml",
            )
        }
        count = app.trellis_rebuild.value
        watcher.start()
        corrected = (PENSION_RETIREMENT / "declaration/trellis.yml").read_text(encoding="utf-8")
        found = model.read_file(folder, "declaration/trellis.yml")
        assert model.save_file(folder, "declaration/trellis.yml", corrected, found.digest).saved
        wait_until(lambda: app.trellis_rebuild.value == count + 1, 10.0, "the count raised")
        time.sleep(10 * app.WATCH_SECONDS)
        assert app.trellis_rebuild.value == count + 1
        cancel.set()
        watcher.join()
        read = app.run_trellis()
        assert read.refusal is None and app.trellis_shown.value is read.shown
        assert ("endpoint-unresolved", "periods[0].connectors[0]") not in {
            (diagnostic.rule, diagnostic.address)
            for diagnostic in read.shown.selection.diagnostics
        }
        assert app.trellis_seen.value == read.shown.files
    finally:
        cancel.set()
        if watcher.is_alive():
            watcher.join()
        app.source.value, app.trellis_shown.value, app.trellis_outcome.value = None, None, None
        app.trellis_seen.value, app.trellis_rebuild.value, app.drawing.value = {}, 0, False


def test_b_a_new_source_shows_no_trellis_of_the_source_before(app_state, consport_folder):
    """With the trellis of `declaration/trellis.cons-port.yml` held, showing
    the source `declaration/trellis.port-cons.yml` forgets that trellis, its
    outcome and the digests of its files, so that the status line names the
    new source with `reading` and no trellis of another source stands for it
    until the new reading stands (specification §3.1)."""
    app_state(consport_folder)
    try:
        app.show_source(recipe.Source("recipe", CONS_PORT_RECIPE))
        app.run_trellis()
        assert app.trellis_shown.value is not None and app.trellis_seen.value
        app.show_source(recipe.Source("recipe", PORT_CONS_RECIPE))
        assert app.trellis_shown.value is None and app.trellis_outcome.value is None
        assert app.trellis_seen.value == {}
        line, rest = app.trellis_status_parts(app.trellis_outcome.value, app.trellis_shown.value)
        assert ("".join(text for text, _ in line), rest) == (f"{PORT_CONS_RECIPE} · reading", [])
    finally:
        app.source.value, app.head.value, app.view_mode.value = None, None, "stage"
        app.trellis_shown.value, app.trellis_outcome.value, app.trellis_seen.value = None, None, {}
        app.selected.value, app.drawing.value = None, False


# the package's sentence refusing `periods 7` on the six periods of lesson 05
PERIODS_7 = "the trellis holds 6 periods, and periods[7] is none of them"


def test_b_a_file_saved_while_its_trellis_is_read_is_read_again(
    monkeypatch, scratch_consport, app_state
):
    """The final review's probe: the calibration of lesson 05's trellis is
    saved while the trellis is bound, after the reading has read it, its
    discount factor changed from 0.96 to 0.5. The reading records the digest
    the file had when it was read, so the watcher finds the file changed and
    raises the count once, and the next reading binds 0.5 at
    `periods[0]/disc`; a digest taken after the binding would hold the saved
    file, and the trellis would keep 0.96 until another save (specification
    §3.1: the trellis re-elaborates when any file the model reads is
    saved)."""
    app_state(scratch_consport)
    monkeypatch.setattr(app, "WATCH_SECONDS", 0.05)
    calibration = scratch_consport / "declaration/calibration/portfolio.yml"
    bind = trellis.bind_trellis

    def saved_while_bound(elaborated, syntactic):
        # the save lands after the reading has read the calibration
        text = calibration.read_text(encoding="utf-8")
        calibration.write_text(text.replace("β: 0.96", "β: 0.5"), encoding="utf-8")
        return bind(elaborated, syntactic)

    app.source.value = recipe.Source("recipe", PORT_CONS_RECIPE)
    cancel = threading.Event()
    watcher = threading.Thread(target=app.watch, args=(cancel,))
    try:
        monkeypatch.setattr(trellis, "bind_trellis", saved_while_bound)
        first = app.run_trellis()
        monkeypatch.setattr(trellis, "bind_trellis", bind)
        assert first.shown.trellis["periods"][0]["stages"]["disc"].par["β"].value == 0.96
        assert "β: 0.5" in calibration.read_text(encoding="utf-8")
        count = app.trellis_rebuild.value
        watcher.start()
        wait_until(lambda: app.trellis_rebuild.value == count + 1, 10.0, "the count raised")
        cancel.set()
        watcher.join()
        second = app.run_trellis()
        assert second.shown.trellis["periods"][0]["stages"]["disc"].par["β"].value == 0.5
    finally:
        cancel.set()
        if watcher.is_alive():
            watcher.join()
        clear_trellis_state()


def test_b_a_refused_restriction_leaves_each_later_reading_under_the_one_accepted_last(
    monkeypatch, scratch_consport, app_state
):
    """Lesson 05's trellis restricted to `periods 0–1`, then to `periods 7`,
    which the package refuses: the view is drawn under `periods 0–1`, the
    restriction the package accepted last, with the package's sentence under
    the input. The calibration then saved, the watcher reads the trellis
    again, and that reading too reaches the view under `periods 0–1`, its
    new discount factor bound and the sentence kept (specification §3.1;
    Review Focus 2)."""
    folder = model.open_folder(scratch_consport)
    app_state(scratch_consport)
    monkeypatch.setattr(app, "WATCH_SECONDS", 0.05)
    accepted = trellis.parse_restriction("periods 0–1")
    app.source.value = recipe.Source("recipe", PORT_CONS_RECIPE)
    app.view_mode.value = "trellis"
    cancel = threading.Event()
    watcher = threading.Thread(target=app.watch, args=(cancel,))
    try:
        app.apply_restriction("periods 0–1")
        assert app.run_trellis().shown.restriction == accepted
        app.apply_restriction("periods 7")
        refused = app.run_trellis()
        assert refused.restricted == PERIODS_7
        assert app.trellis_shown.value is refused.shown and refused.shown.restriction == accepted
        calibration = "declaration/calibration/portfolio.yml"
        found = model.read_file(folder, calibration)
        changed = found.text.replace("β: 0.96", "β: 0.95")
        assert model.save_file(folder, calibration, changed, found.digest).saved
        count = app.trellis_rebuild.value
        watcher.start()
        wait_until(lambda: app.trellis_rebuild.value == count + 1, 10.0, "the count raised")
        cancel.set()
        watcher.join()
        again = app.run_trellis()
        assert app.trellis_shown.value is again.shown and again.shown.restriction == accepted
        assert again.shown.trellis["periods"][0]["stages"]["disc"].par["β"].value == 0.95
        assert app.trellis_outcome.value.restricted == PERIODS_7
        line, _ = app.trellis_status_parts(app.trellis_outcome.value, app.trellis_shown.value)
        assert " · shown periods 0–1 of 6 (6 occurrences)" in "".join(text for text, _ in line)
    finally:
        cancel.set()
        if watcher.is_alive():
            watcher.join()
        clear_trellis_state()


def test_b_a_restriction_that_names_stages_is_written_without_the_trellis_s_periods(
    consport_folder,
):
    """The status line of lesson 05's trellis restricted to `stages cons`,
    and to `periods 0–1, stages cons`, names the restriction and the
    occurrences it shows but not the trellis's six periods after it, since
    a number written after stage keys would read as a count of stages; the
    line's rest names the six periods (specification §3.1; unit K, Task
    6)."""
    folder = model.open_folder(consport_folder)
    lesson = recipe.Source("recipe", PORT_CONS_RECIPE)
    held = trellis.show_trellis(folder, lesson).shown
    lines = []
    for typed in ("stages cons", "periods 0–1, stages cons"):
        outcome = trellis.show_trellis(folder, lesson, trellis.parse_restriction(typed), held)
        line, rest = app.trellis_status_parts(outcome, outcome.shown)
        lines.append("".join(text for text, _ in line + rest))
    assert " · shown stages cons (6 occurrences) · " in lines[0]
    assert " · shown periods 0–1, stages cons (2 occurrences) · " in lines[1]
    assert all(" of " not in line and " · 6 periods, 18 occurrences" in line for line in lines)


def test_b_a_first_reading_under_a_refused_restriction_draws_the_whole_trellis_with_the_sentence(
    app_state, consport_folder
):
    """A restriction kept from another source, `periods 7`, which the six
    periods of lesson 05 do not hold: the first reading of that trellis draws
    the whole trellis with the package's sentence under the input, the
    status line names the trellis and no restriction, never `reading` over an
    empty view, and the files the reading read are watched (specification
    §3.1)."""
    app_state(consport_folder)
    try:
        app.apply_restriction("periods 7")
        app.show_source(recipe.Source("recipe", PORT_CONS_RECIPE))
        outcome = app.run_trellis()
        assert outcome.restricted == PERIODS_7
        assert app.trellis_shown.value is outcome.shown and outcome.shown.restriction is None
        assert outcome.shown.counts == {"periods": 6, "occurrences": 18, "shown": 18}
        line, rest = app.trellis_status_parts(app.trellis_outcome.value, app.trellis_shown.value)
        assert "".join(text for text, _ in line + rest) == (
            f"{PORT_CONS_RECIPE} · trellis · calibrated, methodized, configured · loop "
            f"{outcome.shown.seconds:.2f} s · 6 periods, 18 occurrences · 0 unjoined internal entry fields"
        )
        assert app.trellis_seen.value and app.trellis_seen.value == outcome.shown.files
    finally:
        clear_trellis_state()


def test_b_a_lookup_error_while_a_recipe_is_read_is_recorded_as_a_refused_reading(
    monkeypatch, app_state, lifecycle_folder
):
    """A lookup error while the recipe is read is an internal failure with
    no rule. The trellis reading and the stage bound through that recipe
    name the same error, and the Problems list holds one line in the
    recipe's file. Both source files remain watched for changes."""
    app_state(lifecycle_folder)
    root = lifecycle_folder.resolve() / "declaration"

    def lookup_error(folder, source, texts=None):
        raise KeyError("a key the package looked up")

    monkeypatch.setattr(recipe, "read_source", lookup_error)
    app.source.value = RECIPE
    sentence = "KeyError: 'a key the package looked up'"
    try:
        outcome = app.run_trellis()
        assert app.trellis_outcome.value is outcome and outcome.shown is None
        assert model.sentence(outcome.refusal) == sentence
        assert (outcome.refusal.kind, outcome.refusal.rule) == ("internal", None)
        assert outcome.refusal.entry
        assert outcome.refusal.file == str(root / "spec.yml")
        assert set(app.trellis_seen.value) == {str(root / "spec.yml"), str(root / "trellis.yml")}
        app.open_file(CONS)
        app.run_loop()
        assert app.shown.value.notes == [sentence]
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        # the policy header of cons.bl lists `V[>]` alone, which its line reads,
        # so no diagnostic of an unread input stands before the refusal (the
        # header lost the marginal field `dV[>]` that no line read, AMD-MB-001)
        assert listed == [(sentence, "declaration/spec.yml", None)]
    finally:
        clear_trellis_state()


def test_a_trellis_file_the_factory_refuses_is_listed_whole_with_its_place_once(
    app_state, cagetti_folder
):
    """The Cagetti–De Nardi trellis file names its stages by key, which the
    factory refuses under `trellis-file-shape`: with that file the tab's
    source, the trellis's refused reading and the one note of `worker.bl`,
    bound through it, are the package's whole sentence, its message and, on
    a line of its own, the words it says to write; the list under the
    error mark holds that one refusal once, with the file and line 12, the
    entry refused (AMD-MI-002 §6a; ruling R51; unit L, Task 21)."""
    app_state(cagetti_folder)
    app.source.value = recipe.Source("trellis", "declaration/trellis.yml")
    sentence = (
        "periods[0].stages is no mapping of keys to records\n"
        "stages: {<key>: {stage: <file>.bl, calibration: ..., settings: ..., methods: ...}}"
    )
    try:
        outcome = app.run_trellis()
        assert outcome.shown is None and model.sentence(outcome.refusal) == sentence
        app.open_file("declaration/stages/worker/worker.bl")
        app.run_loop()
        assert app.shown.value.notes == [sentence]
        assert app.shown.value.refusal._replace(revision=None) == outcome.refusal
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert listed == [(sentence, "declaration/trellis.yml", 12)]
    finally:
        clear_trellis_state()


def test_b_the_trellis_panel_with_nothing_selected_reads_no_selection():
    """With nothing selected, the panel of the trellis view reads `No
    selection` in the backward and in the forward graph (specification §2.3
    and §3.1; AMD-MI-002 §6a rule 2; design pass 8 §§6 and 8, item 8)."""
    app.view_mode.value = "trellis"
    texts = {}
    try:
        for name in ("backward", "forward"):
            app.graph.value = name
            _, rendered = solara.render(app.TrellisPanel(), handle_error=False)
            try:
                texts[name] = rendered.find(v.Html, class_="bl-empty").widget.children
            finally:
                rendered.close()
    finally:
        app.view_mode.value, app.graph.value = "stage", "backward"
    assert texts == {"backward": ["No selection"], "forward": ["No selection"]}


def test_r_details_holds_the_legend_folded_at_its_end_with_or_without_a_selection(cons, cons_text):
    """Details (spec 0.4 §§2.1 and 5.5; unit R, brief rule 6; G-R23;
    R-D36; unit K, Task 3, design pass §2: `legend` folded): the panel of a
    stage's view and the panel of the trellis view each stand under the
    panels' one head named `Details` (AAS, L-D12; its capital, unit L,
    Task 29, L-D28), and the legend passed to
    either, the element `Legend` makes,
    stands under a `details` element whose summary reads `Legend` after
    its two twisties (design pass 8 §6), the
    body's last element, whether nothing is selected or a node is selected
    in the stage's view; the legend is never the body's first element. The
    head's context is the selected node's name and position
    (`app.details_context`): `𝑐(m_d) · policy` for the box
    `policy:Evaluation`, the layer's name alone for the builder's layer
    `cntn_to_dcsn`, and nothing with no selection or a node the view does
    not hold."""
    collection = model.collection(cons)
    current = dataclasses.replace(shown_of(cons, cons_text, CONS), collection=collection)

    def drawn(element) -> tuple:
        # the heading, the classes of the body's first and last children,
        # and the summary and the classes of the legend under a details
        # element
        _, rendered = solara.render(element, handle_error=False)
        try:
            heading = rendered.find(v.Html, tag="h2").widget.children
            children = rendered.find(v.Html, class_="bl-panel-body").widget.children
            held = rendered.find(v.Html, tag="details").widgets
            under = None
            if held:
                summary, legend = held[0].children
                words = [child for child in summary.children if isinstance(child, str)]
                under = (words, legend.class_)
            return heading, children[0].class_, children[-1].class_, under
        finally:
            rendered.close()

    folded = (["Legend"], "bl-legend")
    stage_legend = app.Legend(collection, "backward", None)
    trellis_legend = app.Legend(None, "backward", None)
    for element in (app.Panel(None, current, stage_legend), app.TrellisPanel(trellis_legend)):
        heading, first, last, under = drawn(element)
        assert (heading, last, under) == (["Details"], "bl-legend-details", folded)
        assert first != "bl-legend"
    try:
        app.selected.value = {"nodeId": "policy:Evaluation", "graphId": "backward"}
        heading, first, last, under = drawn(
            app.Panel(None, current, app.Legend(collection, "backward", None))
        )
        assert (heading, last, under) == (["Details"], "bl-legend-details", folded)
        assert first != "bl-legend"
        _, rendered = solara.render(app.Panel(None, current, None), handle_error=False)
        try:
            context = rendered.find(v.Html, class_="bl-details-context").widget
            assert (context.children, context.attributes) == (
                ["𝑐(m_d) · policy"],
                {"title": "𝑐(m_d) · policy"},
            )
        finally:
            rendered.close()
    finally:
        app.selected.value = None
    layer = {"nodeId": f"cntn_to_dcsn{app.LAYER_ID_ENDING}", "graphId": "backward"}
    assert app.details_context(collection, layer) == "cntn_to_dcsn"
    unheld = {"nodeId": "nothing", "graphId": "backward"}
    assert (app.details_context(collection, unheld), app.details_context(collection, None)) == (
        "",
        "",
    )


def test_b_a_new_stage_reaches_the_view_already_marked_as_drawing(app_state, model_folder):
    """A stage's result recorded while the stage's view is shown marks the
    view as drawing before the view is given the stage's collection, so that
    the view's processed event, which can only follow the collection, clears
    the mark; set after it, the mark stood on the status line for good
    whenever the view processed the collection first, as it did for the
    trellis before `7dc44a670` (specification §2.5)."""
    app_state(model_folder)
    marks = []
    unsubscribe = app.shown.subscribe(lambda shown: marks.append(app.drawing.value))
    try:
        app.drawing.value = False
        app.open_file(CONS)
        app.run_loop()
        assert app.shown.value is not None and app.shown.value.path == CONS
        assert marks == [True]
        app.on_processed({"graphId": "backward"})
        assert app.drawing.value is False
    finally:
        unsubscribe()
        app.drawing.value = False


def test_b_a_stage_file_opened_from_the_trellis_view_leaves_the_trellis_s_drawing_mark(
    app_state, lifecycle_folder
):
    """With the lifecycle recipe's trellis just read in the trellis view, its
    drawing mark standing until the view processes the trellis's
    collection, a stage file with no result opened in the editor leaves the
    mark, which belongs to the collection the view holds, and the view's
    processed event clears it; cleared by the opening, the mark would leave
    the status line before the view had drawn the trellis (specification
    §2.5)."""
    app_state(lifecycle_folder)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"
    try:
        app.drawing.value = False
        assert app.run_trellis().shown is not None and app.drawing.value is True
        app.open_file(CONS)
        assert app.open_path.value == CONS and app.drawing.value is True
        app.on_processed({"graphId": "backward"})
        assert app.drawing.value is False
    finally:
        clear_trellis_state()


def test_b_a_new_source_clears_the_trellis_view_s_selection(app_state, consport_folder):
    """With the trellis view of `declaration/trellis.cons-port.yml` shown
    and a period selected, showing the source
    `declaration/trellis.port-cons.yml` clears the selection, so that the
    panel describes no node of the new trellis by the id of the node
    selected in the old one, while the view starts with nothing selected
    (specification §3.1)."""
    app_state(consport_folder)
    try:
        app.show_source(recipe.Source("recipe", CONS_PORT_RECIPE))
        app.selected.value = {"nodeId": "periods[1]___group___", "graphId": "backward"}
        app.show_source(recipe.Source("recipe", PORT_CONS_RECIPE))
        assert app.selected.value is None
    finally:
        clear_trellis_state()


def test_b_the_head_names_the_source_that_holds_no_occurrence_of_the_open_stage_file(
    app_state, scratch_consport
):
    """In a stage's view the head names the occurrence the open stage file is
    bound as, `periods[0] / cons` for the consumption file lesson 05's
    trellis file reads; for a stage file no occurrence of that trellis file
    uses, in a stage folder of the copy's `declaration/`, that
    `declaration/trellis.port-cons.yml` holds no occurrence of it; and,
    where no source binds the file, that no recipe holds it where no source
    of the folder holds it, and nothing where one does, since the line then
    prints `held by` and that source (specification §2.1 and §3.2; unit L's
    final judgment, §6 item 3)."""
    # the demonstration's consumption stage file since decision SD-39
    shared = scratch_consport / "declaration/stages/cons/cons.bl"
    text = shared.read_text(encoding="utf-8")
    extra = "declaration/stages/extra/extra.bl"
    (scratch_consport / extra).parent.mkdir(parents=True)
    (scratch_consport / extra).write_text(text, encoding="utf-8")
    app_state(scratch_consport)
    app.source.value = recipe.Source("recipe", PORT_CONS_RECIPE)
    try:
        _, unheld = app.elaborate(extra, text, 1)
        assert app.recipe_head(unheld, extra) == (
            "declaration/spec.port-cons.yml holds no occurrence of this file"
        )
        _, held = app.elaborate(SHARED_CONS, text, 1)
        assert app.recipe_head(held, SHARED_CONS) == "periods[0] / cons"
        app.source.value = None
        _, alone = app.elaborate(extra, text, 1)
        assert app.recipe_head(alone, extra) == "no recipe holds this file"
        _, unbound = app.elaborate(SHARED_CONS, text, 1)
        assert PORT_CONS_RECIPE in [found.path for found, positions in unbound.uses if positions]
        assert app.recipe_head(unbound, SHARED_CONS) == ""
    finally:
        clear_trellis_state()


def test_k_the_switch_marks_the_graph_shown_and_disables_what_it_cannot_show(
    app_state, consport_folder, cons, cons_text
):
    """Spec 0.4 §2.1; R-D56; amendment 02 ruling 5; unit K, K-D20; design
    pass 2 §4; design pass 8 §§4 and 6: while the trellis is shown, the
    view tab `Trellis` is marked and the select `graph` omitted; while the
    editor holds the trellis file, `Stage` carries `aria-disabled` with the
    hover `No stage file open`, and a click on it changes neither the view
    nor the history. With a stage file open, `Stage` acts and a click on it
    shows the stage's view, `Stage` marked, `Trellis` no longer marked and
    the select `graph` standing; the place left, the trellis, is recorded
    as the history records every place (AMD-MI-002 §3 rule 4). Without a
    composition `Trellis` carries `aria-disabled`."""
    app_state(consport_folder)
    try:
        app.open_from_tree(PORT_CONS)
        assert (app.view_mode.value, app.open_path.value) == ("trellis", PORT_CONS)
        current = shown_of(cons, cons_text, SHARED_CONS)
        _, rendered = solara.render(app.ViewRegion(None, current), handle_error=False)
        try:

            def segment(word):
                (button,) = [
                    widget
                    for widget in view_tabs(rendered)
                    if f"bl-{word}-button" in widget.class_.split()
                ]
                return button

            def kinds():
                return [name for name in view_selects(rendered) if name == "bl-view-kind"]

            assert "bl-active" in segment("trellis").class_.split()
            # the select `graph` stands in the trellis view too (design pass 14 §7)
            assert kinds() == ["bl-view-kind"]
            assert segment("stage").attributes == {
                "slot": "header",
                "title": "No stage file open",
                "aria-pressed": "false",
                "aria-disabled": "true",
            }
            history = app.history.value
            press_tab(segment("stage"))
            assert app.view_mode.value == "trellis" and app.history.value is history
            app.open_path.value = SHARED_CONS
            assert segment("stage").attributes == {
                "slot": "header",
                "title": "The graph of the stage file open in the editor",
                "aria-pressed": "false",
                "aria-disabled": "false",
            }
            left = app._place()
            press_tab(segment("stage"))
            assert (app.view_mode.value, app.open_path.value) == ("stage", SHARED_CONS)
            assert app.history.value.behind[-1] == left and left.view == "trellis"
            assert "bl-active" not in segment("trellis").class_.split()
            assert "bl-active" in segment("stage").class_.split()
            assert segment("stage").attributes["aria-pressed"] == "true"
            assert len(kinds()) == 1
        finally:
            rendered.close()
        _, rendered = solara.render(app.ViewSwitch(False, False, False), handle_error=False)
        try:
            _, button = view_tabs(rendered)
            assert button.children == ["Trellis"] and button.attributes["aria-disabled"] == "true"
            press_tab(button)
            assert app.view_mode.value == "stage"
        finally:
            rendered.close()
    finally:
        clear_trellis_state()
        app.history.value, app.place_request.value = navigation.History(), None


def test_b_apply_restriction_parses_the_text_and_keeps_a_refused_one_apart():
    """A restriction chosen or typed in the view's bar is parsed into the
    trellis's loop; a text the parser refuses leaves the restriction as it
    stands and holds its sentence; an empty text, which `all` of the
    restriction's menu writes with every stage key ticked, shows the whole
    trellis, the text emptied (specification §3.1; amendment 02 ruling 6;
    unit K, K-D17)."""
    try:
        app.apply_restriction("periods 0–1, stages cons")
        assert app.restriction.value == trellis.Restriction(
            (0, 1), ("cons",), "periods 0–1, stages cons"
        )
        assert app.restriction_refusal.value is None
        app.apply_restriction("periods two")
        assert app.restriction.value.text == "periods 0–1, stages cons"
        assert app.restriction_refusal.value["sentence"] == (
            "`periods two` is no period range; write `periods 0–2` or `periods 3`"
        )
        app.apply_restriction("")
        assert app.restriction.value is None and app.restriction_refusal.value is None
        assert app.restriction_text.value == ""
    finally:
        app.restriction.value, app.restriction_text.value, app.restriction_refusal.value = (
            None,
            "",
            None,
        )


def test_b_the_package_s_sentence_leaves_once_another_restriction_is_applied():
    """The sentence of a restriction the package refused, which the last
    outcome holds, stands while the same text is applied again, and leaves
    as soon as another restriction is applied, the empty text that `all`
    of the restriction's menu writes among them, before the trellis's loop
    reads the trellis again (specification §3.1; Review Focus 2)."""
    sentence = "the trellis holds 6 periods, and periods[7] is none of them"
    refused = trellis.TrellisOutcome(None, None, sentence, 0.0, {})
    try:
        app.restriction_text.value = "periods 7"
        app.restriction.value = trellis.parse_restriction("periods 7")
        app.trellis_outcome.value = refused
        app.apply_restriction("periods 7")
        assert app.trellis_outcome.value == refused
        app.apply_restriction("periods 0–2")
        assert app.restriction.value == trellis.parse_restriction("periods 0–2")
        assert app.trellis_outcome.value == trellis.TrellisOutcome(None, None, None, 0.0, {})
        app.restriction.value = trellis.parse_restriction("periods 7")
        app.trellis_outcome.value = refused
        app.apply_restriction("")
        assert app.restriction.value is None
        assert app.trellis_outcome.value == trellis.TrellisOutcome(None, None, None, 0.0, {})
    finally:
        app.restriction.value, app.restriction_text.value, app.restriction_refusal.value = (
            None,
            "",
            None,
        )
        app.trellis_outcome.value = None


def test_b_all_shows_no_sentence_of_the_restriction_it_removes(monkeypatch):
    """With `periods 7` refused by the package and `periods two` then refused
    by the parser, the select of the view's bar prints `periods two`, marked
    as refused, and its menu, with no trellis read, lists `all` alone; the
    choice of `all`, the event the menu sends, takes the list under the
    error mark from the parser's sentence to none, with no render between
    that shows the package's sentence of `periods 7`, and the select to
    `all`, unmarked (specification §3.1; Review Focus 2; AMD-MI-002 §6a
    rule 1; unit K, K-D17)."""
    sentence = "the trellis holds 6 periods, and periods[7] is none of them"
    rendered_sentences = []
    original_line = app.ErrorLine

    def record_line(refusal):
        rendered_sentences.append(refusal.sentence)
        return original_line(refusal)

    monkeypatch.setattr(app, "ErrorLine", record_line)
    try:
        app.restriction.value = trellis.parse_restriction("periods 7")
        app.trellis_outcome.value = trellis.TrellisOutcome(None, None, sentence, 0.0, {})
        app.apply_restriction("periods two")
        parser = app.restriction_refusal.value["sentence"]
        app.toggle_errors()
        _, rendered = solara.render(app.ViewRestriction(), handle_error=False)
        _, marked = solara.render(app.ErrorMark(), handle_error=False)
        try:
            select = rendered.find(ipyvue.VueTemplate).widget
            written = "periods two"
            assert (select.text, select.refused, select.typed) == (written, True, written)
            assert (select.ranges, select.stages) == (
                [{"label": "all", "text": "", "chosen": False}],
                [],
            )
            listed = marked.find(v.Html, class_="bl-error-list").widget
            assert any(parser in drawn_text(line) for line in listed.children)
            assert parser in rendered_sentences
            select.vue_chosen(select.ranges[0]["text"])
            assert sentence not in rendered_sentences
            current_list = marked.find(v.Html, class_="bl-error-list").widget
            assert not any(parser in drawn_text(line) for line in current_list.children)
            assert (select.text, select.refused) == ("all", False)
        finally:
            rendered.close()
            marked.close()
    finally:
        app.restriction.value, app.restriction_text.value, app.restriction_refusal.value = (
            None,
            "",
            None,
        )
        app.trellis_outcome.value = None
        app.errors_open.value = False


def test_the_error_mark_names_its_count_to_a_screen_reader():
    """The error mark's aria-label, which a screen reader reads, names the
    count the mark shows: `nothing refused` while nothing stands, the words
    its list reads then, `1 refusal` and `2 refusals`; its title, the hover
    text, reads `Refusals` (AMD-MI-002 §6a rule 1), with a capital (design
    pass 8 §8, item 1)."""
    labels = []
    for count in (0, 1, 2):
        _, rendered = solara.render(app.ErrorButton(count, False), handle_error=False)
        try:
            button = rendered.find(v.Html, tag="button").widget
            labels.append((button.attributes["aria-label"], button.attributes["title"]))
        finally:
            rendered.close()
    assert labels == [
        ("Problems: none reported", "Problems: none reported"),
        ("Problems: 1 error, 0 to review", "Problems: 1 error, 0 to review"),
        ("Problems: 2 errors, 0 to review", "Problems: 2 errors, 0 to review"),
    ]


def test_the_list_keeps_the_refusal_of_the_stage_shown_while_a_text_file_is_open(
    app_state, cagetti_folder
):
    """With `entrepreneur_death.bl` of the Cagetti–De Nardi copy open and
    elaborated, its forward builders graph refused at line 17, the list
    under the error mark holds that refusal once, with the stage file and
    line 17. With the stage's addition `methods.bl` then opened as text, the
    view and the panel keep the stage, and the list keeps the refusal, once,
    with the stage file and line 17 (AMD-MI-002 §6a rule 1: the sentence
    the refusing node's panel no longer prints stands in the list)."""
    stage_file = (ROOT / ENTREPRENEUR_DEATH_PATH).relative_to(CAGETTI_DENARDI).as_posix()
    methods_file = stage_file.rpartition("/")[0] + "/methods.bl"
    app_state(cagetti_folder)
    try:
        app.open_file(stage_file)
        app.run_loop()
        refusal = model.refused_directions(app.shown.value.stage)["forward"]
        line = (model.sentence(refusal), stage_file, 17)

        def listed():
            # the lines of the list under the error mark as triples
            return [(each.sentence, each.file, each.line) for each in app.standing_refusals()]

        assert refusal.line == 17 and listed().count(line) == 1
        # the editor answers the flush request with the stage's document,
        # which completes the switch to the methods file
        held = app.buffers.value[stage_file]
        app.open_file(methods_file)
        app.on_change(
            {"path": stage_file, "text": held["text"], "revision": held["document_revision"]}
        )
        assert app.open_path.value == methods_file
        app.run_loop()
        assert app.shown.value.path == stage_file
        assert listed().count(line) == 1
    finally:
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


@pytest.mark.parametrize("opened", ["the stage file", "its methods file"])
def test_the_list_keeps_the_refused_graph_of_the_stage_drawn_after_its_text_is_refused(
    app_state, cagetti_folder, opened
):
    """With `entrepreneur_death.bl` of the Cagetti–De Nardi copy elaborated,
    its forward builders graph refused at line 17, and an edit of line 24
    to `a = a_ed - - θ_n` then refused by the loop, the view still draws
    the stage made before the edit, whose refusing node's panel prints its
    rows alone. The list under the error mark holds the text's refusal at
    line 24 and the drawn stage's forward refusal at line 17, each once,
    newest first, with the stage file: while the stage file stays open,
    and while its addition `methods.bl` is open as text (AMD-MI-002 §6a rule 1:
    the sentence a place no longer shows stands in the list)."""
    stage_file = (ROOT / ENTREPRENEUR_DEATH_PATH).relative_to(CAGETTI_DENARDI).as_posix()
    methods_file = stage_file.rpartition("/")[0] + "/methods.bl"
    app_state(cagetti_folder)
    try:
        app.open_file(stage_file)
        app.run_loop()
        drawn = app.shown.value
        forward = model.refused_directions(drawn.stage)["forward"]
        held = app.buffers.value[stage_file]
        refused_text = held["text"].replace("    a = a_ed\n", "    a = a_ed - - θ_n\n", 1)
        (text,) = model.elaborate_buffer(refused_text, stage_file).diagnostics
        expected = [(model.sentence(text), stage_file, 24), (model.sentence(forward), stage_file, 17)]

        def listed():
            # the lines of the list under the error mark as triples
            return [(each.sentence, each.file, each.line) for each in app.standing_refusals()]

        # the editor's document after a pause, which the loop refuses
        app.on_change(
            {"path": stage_file, "text": refused_text, "revision": held["document_revision"]}
        )
        app.run_loop()
        if opened == "its methods file":
            # the editor answers the flush request with the stage's
            # document, which completes the switch to the methods file
            held = app.buffers.value[stage_file]
            app.open_file(methods_file)
            app.on_change(
                {"path": stage_file, "text": held["text"], "revision": held["document_revision"]}
            )
            assert app.open_path.value == methods_file
            app.run_loop()
        assert app.shown.value is drawn
        found = listed()
        assert [found.count(line) for line in expected] == [1, 1]
        assert found.index(expected[0]) < found.index(expected[1])
    finally:
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_b_a_restriction_typed_while_a_loop_writes_its_result_is_kept_and_applied(
    app_state, pension_folder
):
    """With the pension trellis shown, a text typed at the foot of the
    restriction's menu is kept when the loop of a stage file opened
    meanwhile writes its result, which renders the page, and Enter then
    applies it (specification §3.1; unit K, K-D17). The browser holds the
    text typed until Enter, and writes its field again only where the
    property `typed` changes: the render leaves `typed` as it was, so the
    field keeps the text, as item 5's page test needs after the refusing
    node's link opened `declaration/stages/retire_choice/retire_choice.bl`;
    Enter sends the text by the event `chosen`, which applies it."""
    stage_file = RETIRE_CHOICE
    app_state(pension_folder)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"

    @solara.component
    def SelectBesideTheResults():
        # the view's bar and the loop's results, which the page reads, so that
        # a result written renders the tree as it renders the page
        app.ViewRestriction()
        solara.Text(" ".join(sorted(app.results.value)))

    _, rendered = solara.render(SelectBesideTheResults(), handle_error=False)
    try:
        select = rendered.find(ipyvue.VueTemplate).widget
        typed = select.typed
        app.open_file(stage_file)
        app.run_loop()
        assert stage_file in app.results.value
        assert select.typed == typed
        # Enter at the menu's foot, as the browser sends it
        select.vue_chosen("periods 1–1")
        assert app.restriction.value == trellis.parse_restriction("periods 1–1")
        assert (select.text, select.typed) == ("periods 1–1", "periods 1–1")
    finally:
        rendered.close()
        app.source.value, app.view_mode.value = None, "stage"
        app.restriction.value, app.restriction_text.value, app.restriction_refusal.value = (
            None,
            "",
            None,
        )


def test_b_a_periods_occurrences_are_printed_by_address_and_select_their_layers():
    """The panel of a period in the trellis view prints each occurrence by
    its address, `periods[1]/cons`, without the viewer's ending of a layer's
    id (specification §2.3: the viewer's words are mapped to the project's),
    and a click on one selects the occurrence's layer in the view."""
    subject = trellis.Subject(
        "period",
        "periods[1]___group___",
        "backward",
        "periods[1]",
        None,
        {},
        {},
        None,
        (("periods[1]/port", (1, "port")), ("periods[1]/cons", (1, "cons"))),
    )
    _, rendered = solara.render(app.TrellisSubject(subject, []), handle_error=False)
    try:
        items = rendered.find(v.Html, tag="li").widgets
        assert [item.children for item in items] == [["periods[1]/port"], ["periods[1]/cons"]]
        assert [item.attributes["data-node"] for item in items] == [
            "periods[1]/port___group___",
            "periods[1]/cons___group___",
        ]
        items[1].fire_event("click", {})
        assert (app.select_request.value["nodeId"], app.select_request.value["graphId"]) == (
            "periods[1]/cons___group___",
            "backward",
        )
    finally:
        rendered.close()
        app.select_request.value = None
        app.graph.value = "backward"


def test_b_the_refusing_node_lists_its_sixty_joins_though_several_link_to_one_line(
    pension_folder,
):
    """The panel of the pension trellis's refusing backward node draws its
    sixty joins, each with its links, although the joins that leave the
    retirement choice at several periods link to one line of
    `declaration/stages/retire_choice/retire_choice.bl` with one text
    (specification §3.1: a refusing trellis node links to the header and to
    the connector); reacton allows each key once per component, so a link's
    key names its join."""
    folder = model.open_folder(pension_folder)
    shown = trellis.show_trellis(folder, RECIPE).shown
    joins = trellis.refusal_links(folder, shown)
    links = [(link.text, link.line) for join in joins for link in join.links]
    assert len(set(links)) < len(links)
    subject = trellis.describe_node(shown, "backward", "backward:refused", {})
    _, rendered = solara.render(app.TrellisSubject(subject, joins), handle_error=False)
    try:
        assert len(rendered.find(v.Html, class_="bl-unpaired bl-code-small").widgets) == 60
        items = rendered.find(v.Html, tag="li", class_="bl-link").widgets
        assert [(item.children[0], int(item.attributes["data-line"])) for item in items] == links
    finally:
        rendered.close()


def recipe_tab_fields(rendered) -> dict:
    """The selects of the Recipe tab rendered, each the widget of its field
    (field.vue), by the address of its entry in the recipe (design pass 9
    §3): the trellis row's and the open row's (design pass 11 §2)."""
    return {
        entry.attributes["data-address"]: entry.children[0]
        for entry in rendered.find(v.Html, class_="bl-recipe-entry").widgets
    }


def recipe_tab_values(rendered) -> dict:
    """The selects of the Recipe tab rendered (`recipe_tab_fields`), each
    as its kind, value, options, hover and accessible name read at the
    call, by the address of its entry, so that a select of a row that
    closes later is still read as it was drawn (design pass 11 §2)."""
    return {
        address: SimpleNamespace(
            kind=field.kind,
            value=field.value,
            options=list(field.options),
            hover=field.hover,
            named=field.named,
        )
        for address, field in recipe_tab_fields(rendered).items()
    }


def clear_recipe_tab_state() -> None:
    """The state the tests of the Recipe tab set, emptied."""
    clear_gesture_state()
    clear_trellis_state()
    app.buffers.value, app.open_path.value, app.choice_refusal.value = {}, None, None
    app.form_open.value, app.form_fill.value, app.region_wide.value = None, None, None
    app.history.value = navigation.History()
    app.sources.value, app.tree.value, app.git_line.value = [], [], ""
    app.folder_read.value = False


def test_m_10_the_recipe_tab_draws_each_binding_of_the_recipe_as_a_control(
    app_state, scratch_lifecycle
):
    """Unit M, Task 10 (AAS, M-D17; design pass 9 §3), with the strip and
    the cells of unit N, Task 2 (design pass 10 §4; N-D4, N-D5), and the
    rows at rest of design pass 11 §2. The Recipe tab of the lifecycle
    registry's recipe is the panel under the editor with data-panel
    `recipe`, no head and no `h2`, its strip `.bl-inspector-strip` holding
    the one view tab `Recipe` and the recipe's name `spec.yml`, its path
    the name's hover; the five column heads, each with its hover; the
    trellis row's select; one row per stage in the file's order, each at
    rest, focusable, with no select, its key line the key alone in Code
    name, its hover the stage file's path, the file's name `<key>.bl`
    printed on no line (design pass 13 §§3 and 4; C1, C10), and the trash
    the row's last child, in the table's last column (D2). Each row opened
    in turn by a click, the others standing at rest: the key line the key
    and the stage file's select; each entry a select whose value prints it
    without its kind's folder or the stage's own, whose options are the files
    of its kind and then the recipe's slots of that kind; the range list `0-0`
    with its periods `0–0` on the line of its select, and of its text at
    rest; `—` for a kind the recipe writes none of, the portfolio stage's
    settings; each row's trash
    button, its hover naming the key; no element reading `Replace`, the
    select's hover alone naming the replacement; the icon button `new-file`
    beside the slot whose own file is missing, the discount stage's
    settings, its hover the file it writes, and no other; the periods
    fields empty with the placeholder
    `All` and the periods the trellis lists the stage in as their hover;
    and the add row's `Stage`, which opens the stage list beside it and no
    form, a second click closing the list (unit N, Task 5; design pass 10
    §7)."""
    app_state(scratch_lifecycle)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"
    try:
        app.run_trellis()
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)
        try:
            (section,) = rendered.find(v.Html, class_="bl-classification").widgets
            assert section.attributes == {"aria-label": "recipe", "data-panel": "recipe"}
            assert rendered.find(v.Html, tag="h2").widgets == []
            assert rendered.find(v.Html, class_="bl-head bl-region-head").widgets == []
            strip = rendered.find(v.Html, class_="bl-inspector-strip").widget
            (tab,) = rendered.find(v.Html, class_="bl-class-tab bl-active").widgets
            assert (drawn_text(tab), tab.attributes["data-tab"]) == ("Recipe", "Recipe")
            assert len(rendered.find(v.Html, tag="vscode-tab-header").widgets) == 1
            file_name = rendered.find(v.Html, class_="bl-inspector-file bl-code-small").widget
            assert (drawn_text(file_name), file_name.attributes["title"]) == (
                "spec.yml",
                RECIPE_FILE,
            )
            assert file_name in strip.children
            heads = rendered.find(v.Html, class_="bl-recipe-heads").widget
            assert [drawn_text(head) for head in heads.children] == list(app.RECIPE_HEADS)
            assert [head.attributes["title"] for head in heads.children] == [
                "The stage's file",
                "Parameter values",
                "Numerical choices",
                "Numerical routines for the stage's operations",
                "The periods the stage stands in",
            ]
            rows = rendered_recipe_rows(rendered)
            assert list(rows) == ["port", "cons", "disc"]
            # every row at rest, focusable, with no select (design pass 11
            # §2); its key line the key alone, its hover the stage file's
            # path, and the trash the row's last child (design pass 13 §§3
            # and 4; C10, D2)
            assert [
                (row.class_, row.attributes["aria-expanded"], row.attributes["tabindex"])
                for row in rows.values()
            ] == [("bl-recipe-row", "false", "0")] * 3
            assert set(recipe_tab_fields(rendered)) == {"trellis"}
            assert rendered.find(v.Html, class_="bl-new-file").widgets == []
            rest_lines = rendered.find(v.Html, class_="bl-recipe-line bl-recipe-key-line").widgets
            for line, key in zip(rest_lines, ("port", "cons", "disc"), strict=True):
                (name,) = line.children
                assert (drawn_text(name), name.class_) == (key, "bl-recipe-key bl-code-name")
                assert name.attributes["title"] == f"stages/{key}/{key}.bl"
            for key, row in rows.items():
                (stage_cell,) = [
                    cell for cell in row.children if cell.attributes.get("data-kind") == "stage"
                ]
                # the file's name is `<key>.bl`, so the cell has no second line
                assert len(stage_cell.children) == 1
                assert row.children[-1].attributes["data-stage"] == key

            # each row opened in turn, the others at rest: its selects, its
            # key line, its range line, its `New file` and its periods field
            def texts(widget) -> list:
                # every string the element and its descendants draw
                found = []
                for child in getattr(widget, "children", None) or []:
                    found += [child] if isinstance(child, str) else texts(child)
                return found

            (section,) = rendered.find(v.Html, class_="bl-classification").widgets
            fields, addresses, periods, new_files = {}, set(), [], {}
            for key in ("port", "cons", "disc"):
                open_rendered_recipe_row(rendered, key)
                fields.update(recipe_tab_values(rendered))
                entries = rendered.find(v.Html, class_="bl-recipe-entry").widgets
                addresses |= {entry.attributes["data-address"] for entry in entries}
                # the Stage cell's line: the key and the stage file's select;
                # the trash is the row's last child (design pass 13 §4; D2)
                key_lines = rendered.find(
                    v.Html, class_="bl-recipe-line bl-recipe-key-line"
                ).widgets
                assert len(key_lines) == 3
                (line,) = [line for line in key_lines if drawn_text(line.children[0]) == key]
                name, select = line.children
                assert select.attributes["data-address"] == f"stages.{key}.stage"
                opened = rendered_recipe_rows(rendered)[key]
                assert opened.children[-1].attributes["data-stage"] == key
                new_files[key] = rendered.find(v.Html, class_="bl-new-file").widgets
                if key == "disc":
                    # `New file` an icon button beside its select
                    (new,) = new_files[key]
                    assert (new.tag, new.attributes["icon"], new.attributes["label"]) == (
                        "vscode-toolbar-button",
                        "new-file",
                        "New file",
                    )
                    assert (new.attributes["data-address"], new.attributes["title"]) == (
                        "stages.disc.settings.all[0]",
                        "Write declaration/settings/disc.yml",
                    )
                    (slot_entry,) = [
                        entry
                        for entry in entries
                        if entry.attributes["data-address"] == "stages.disc.settings.all[0]"
                    ]
                    assert slot_entry.children[1] is new
                    # the range list's periods on the line of its select, at
                    # its left
                    (ranged,) = [
                        line
                        for line in rendered.find(v.Html, class_="bl-recipe-line").widgets
                        if any(
                            getattr(child, "class_", "") == "bl-recipe-range bl-code-small"
                            for child in line.children
                        )
                    ]
                    label, entry = ranged.children
                    assert drawn_text(label) == "0–0"
                    assert entry.attributes["data-address"] == "stages.disc.calibration.0-0[0]"
                # no word `Replace` stands on the tab
                assert [text for text in texts(section) if "Replace" in text] == []
                periods += [
                    (widget.value, widget.placeholder, widget.hover)
                    for widget in rendered.find(ipyvue.VueTemplate).widgets
                    if "bl-recipe-periods" in widget.classes
                ]
            assert {address: field.value for address, field in fields.items()} == {
                "trellis": "trellis.yml",
                "stages.port.stage": "port.bl",
                "stages.port.calibration.all[0]": "portfolio",
                "stages.port.methods.all[0]": "methods.bl",
                "stages.cons.stage": "cons.bl",
                "stages.cons.calibration.all[0]": "portfolio",
                "stages.cons.settings.all[0]": "cons",
                "stages.cons.methods.all[0]": "methods.bl",
                "stages.disc.stage": "disc.bl",
                "stages.disc.calibration.all[0]": "portfolio",
                "stages.disc.calibration.0-0[0]": "terminal",
                "stages.disc.settings.all[0]": "$disc_settings",
                "stages.disc.methods.all[0]": "methods.bl",
            }
            slot = fields["stages.disc.settings.all[0]"]
            assert (slot.kind, slot.hover, slot.named) == (
                "select",
                "Replace $disc_settings",
                "Replace $disc_settings",
            )
            assert slot.options == ["cons", "$disc_settings"]
            # the additions of a methods cell: the stage's own by their names,
            # another stage's by its path (decision S7-W2)
            assert fields["stages.cons.methods.all[0]"].options == [
                "methods.bl",
                "methods.vfi.bl",
                "stages/disc/methods.bl",
                "stages/port/methods.bl",
            ]
            assert fields["stages.port.calibration.all[0]"].options == ["portfolio", "terminal"]
            assert fields["trellis"].options == ["trellis.yml"]
            assert fields["stages.port.stage"].options == [
                "stages/cons/cons.bl",
                "stages/disc/disc.bl",
                "port.bl",
            ]
            assert addresses == set(fields)
            assert {key: len(found) for key, found in new_files.items()} == {
                "port": 0,
                "cons": 0,
                "disc": 1,
            }
            # the range list's periods at rest on the line of its text
            app.recipe_open_stage.value = None
            (ranged,) = [
                line
                for line in rendered.find(v.Html, class_="bl-recipe-line").widgets
                if any(
                    getattr(child, "class_", "") == "bl-recipe-range bl-code-small"
                    for child in line.children
                )
            ]
            assert [drawn_text(child) for child in ranged.children] == ["0–0", "terminal"]
            (none,) = rendered.find(v.Html, class_="bl-recipe-none bl-code-small").widgets
            assert (drawn_text(none), none.attributes["title"]) == ("—", app.NONE_WRITTEN_HOVER)
            removes = rendered.find(v.Html, class_="bl-remove-stage").widgets
            assert [(b.attributes["data-stage"], b.attributes["title"]) for b in removes] == [
                (key, f"Remove {key} from this recipe") for key in ("port", "cons", "disc")
            ]
            assert [b.attributes["icon"] for b in removes] == ["trash"] * 3
            # no word `Replace` stands on the tab
            assert rendered.find(v.Html, class_="bl-recipe-acts").widgets == []
            drawn = texts(section)
            assert {"spec.yml", "Recipe", "port", "—"} <= set(drawn)
            assert [text for text in drawn if "Replace" in text] == []
            assert periods == [("", "All", "Listed in periods 0–2")] * 3
            add = rendered.find(v.Html, class_="bl-text-button bl-recipe-add-stage").widget
            assert (drawn_text(add), add.attributes["aria-label"]) == ("Stage", "Add stage")
            # the button opens the stage list beside it, no form (unit N,
            # Task 5; design pass 10 §7), and a second click closes it
            add.fire_event("click", {})
            assert (app.recipe_chooser.value, app.form_open.value) == (True, None)
            add.fire_event("click", {})
            assert app.recipe_chooser.value is False
        finally:
            rendered.close()
    finally:
        clear_recipe_tab_state()


def test_m_10_a_choice_edits_the_recipe_s_buffer_and_a_refused_one_marks_its_select(
    app_state, scratch_lifecycle
):
    """Unit M, Task 10 (AAS, M-D17; design pass 9 §4). With no file open,
    and disc's row of the Recipe tab opened by a click (design pass 11 §2),
    a choice of `cons` in the select of the slot `$disc_settings` writes
    `settings/cons` in the slot's place in the recipe's buffer, one change of
    it, the file on disk unchanged, the status line's note naming the entry
    written; a choice asked of the same entry, which the buffer no longer
    writes, is refused in one sentence, nothing written, the sentence under
    the error mark at the recipe's line, and its select marked, the same
    element, answered at the refusal, and another select of the open row
    the same element, answered at the reading alone."""
    app_state(scratch_lifecycle)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"
    on_disk = (scratch_lifecycle / RECIPE.path).read_text(encoding="utf-8")
    try:
        app.run_trellis()
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)
        try:
            open_rendered_recipe_row(rendered, "disc")
            field = recipe_tab_fields(rendered)["stages.disc.settings.all[0]"]
            field.vue_entered("cons")
            written = app.buffers.value[RECIPE.path]
            assert "settings: {all: [settings/cons]}" in written["text"]
            assert written["text"] == on_disk.replace("[$disc_settings]", "[settings/cons]")
            assert (scratch_lifecycle / RECIPE.path).read_text(encoding="utf-8") == on_disk
            assert app.choice_refusal.value is None
            assert app.gesture_note.value["sentence"] == (
                "spec.yml, stages.disc.settings.all[0]: settings/cons written"
            )
            # the entry the table showed, which the buffer no longer writes
            held = app.trellis_shown.value
            (entry,) = recipe.table(app.tab_folder.value, RECIPE, held.syntactic, 0)[2].cells[
                "settings"
            ].entries
            drawn = recipe_tab_fields(rendered)
            app.choose_file(entry, "declaration/settings/cons.yml")
            assert app.buffers.value[RECIPE.path]["text"] == written["text"]
            refused = app.choice_refusal.value
            sentence = "the file no longer writes $disc_settings at stages.disc.settings.all[0]"
            assert (refused["sentence"], refused["control"]) == (sentence, app.SELECT)
            (listed,) = [item for item in app.standing_refusals() if item.sentence == sentence]
            assert (listed.file, listed.line) == (RECIPE.path, 8)
            field = recipe_tab_fields(rendered)["stages.disc.settings.all[0]"]
            assert field.classes == "bl-code-small bl-refusal-mark"
            # the refused select, the same element, is answered at the
            # refusal, and the others at the reading alone (fix round 1),
            # another select of the open row among them, port's row standing
            # at rest with none (design pass 11 §2)
            made = app.trellis_outcome.value.made
            assert field is drawn["stages.disc.settings.all[0]"]
            assert field.answered == f"{made} {refused['made']}"
            other = recipe_tab_fields(rendered)["stages.disc.calibration.all[0]"]
            assert (other is drawn["stages.disc.calibration.all[0]"], other.answered) == (
                True,
                f"{made} 0.0",
            )
            assert "stages.port.calibration.all[0]" not in recipe_tab_fields(rendered)
        finally:
            rendered.close()
    finally:
        clear_recipe_tab_state()


def test_m_10_the_periods_field_and_new_file_write_the_recipe_s_buffer(
    app_state, scratch_lifecycle
):
    """Unit M, Task 10 (design pass 9 §4). The periods `0-1` typed for
    `disc` add `periods: [0, 1]` at the end of its block in the recipe's
    buffer, which disc's row prints at rest (design pass 11 §2); a text that
    is no range is refused in the page's sentence, the field marked, in
    cons's row opened, and no other; `New file` beside `$disc_settings`
    writes the empty settings file of `disc` to disk and `settings/disc` in
    the slot's place in the buffer, and opens the new file; asked again, it
    is refused in the creation unit's sentence, since the file exists, its
    button marked."""
    app_state(scratch_lifecycle)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"
    root = scratch_lifecycle
    try:
        app.run_trellis()
        app.choose_periods("disc", "0-1", None)
        text = app.buffers.value[RECIPE.path]["text"]
        (row,) = [line for line in text.splitlines() if line.startswith("  disc:")]
        assert row.endswith("methods: {all: [stages/disc/methods.bl]}, periods: [0, 1]}")
        assert app.gesture_note.value["sentence"] == "spec.yml, stages.disc.periods: 0-1 written"
        app.choose_periods("cons", "late", None)
        refused = app.choice_refusal.value
        assert (refused["sentence"], refused["control"], refused["address"]) == (
            "late is no range of periods; write lo–hi",
            app.PERIODS,
            "stages.cons.periods",
        )
        assert app.buffers.value[RECIPE.path]["text"] == text
        app.run_trellis()
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)
        try:
            # at rest, each row's periods as text (design pass 11 §2), in the
            # cell before the trash (design pass 13 §4; D2)
            rest = {
                key: drawn_text(
                    next(
                        cell
                        for cell in row.children
                        if cell.attributes.get("data-kind") == "periods"
                    )
                )
                for key, row in rendered_recipe_rows(rendered).items()
            }
            assert rest == {"port": "All", "cons": "All", "disc": "0–1"}
            # each row opened in turn, the others at rest: its periods field
            periods, marked = [], {}
            for key in ("port", "cons", "disc"):
                open_rendered_recipe_row(rendered, key)
                (field,) = [
                    widget
                    for widget in rendered.find(ipyvue.VueTemplate).widgets
                    if "bl-recipe-periods" in widget.classes
                ]
                assert field.named == f"Periods of {key}"
                periods.append(field.value)
                marked[key] = "bl-refusal-mark" in field.classes.split()
            assert periods == ["", "", "0–1"]
            assert marked == {"port": False, "cons": True, "disc": False}
        finally:
            rendered.close()
        held = app.trellis_shown.value
        (slot,) = recipe.table(app.tab_folder.value, RECIPE, held.syntactic, 0)[2].cells[
            "settings"
        ].entries
        app.new_file_for(slot, "disc", "settings")
        made = root / "declaration/settings/disc.yml"
        assert made.read_text(encoding="utf-8") == "settings: {}\n"
        assert "settings: {all: [settings/disc]}" in app.buffers.value[RECIPE.path]["text"]
        assert app.open_path.value == "declaration/settings/disc.yml"
        assert app.choice_refusal.value is None
        # no editor answers in this test, so the new file's tab is closed
        app.open_path.value = None
        app.new_file_for(slot, "disc", "settings")
        refused = app.choice_refusal.value
        assert (refused["sentence"], refused["control"]) == (
            "declaration/settings/disc.yml exists",
            app.NEW_FILE,
        )
    finally:
        clear_recipe_tab_state()


def test_m_10_the_panel_under_the_editor_shows_the_recipe_for_the_trellis_s_recipe_alone(
    app_state, lifecycle_folder
):
    """Unit M, Task 10 (AAS, M-D3; design pass 9 §2), as unit N, Task 1
    names the panel (design pass 10 §§3 and 4; N-D4). The panel under the
    editor, the Inspector, shows the Recipe tab for the recipe the trellis
    is read under and the four tabs of Types for a stage file, `lower_panel`
    answering `inspector` for both, and nothing for the trellis file, for a
    period file, for no file, or for a recipe the trellis is not read
    under, `lower_panel` answering None. The main bar's Inspector toggle is
    disabled while the panel shows nothing, its hover `Nothing to inspect
    in <file>`, and enabled, its hover `Inspector`, while it shows the open
    file."""
    app_state(lifecycle_folder)
    app.source.value = RECIPE
    try:
        assert app.inspector_content(RECIPE.path) == "recipe"
        assert app.inspector_content("declaration/stages/cons/cons.bl") == "types"
        assert app.lower_panel(RECIPE.path) == "inspector"
        assert app.lower_panel("declaration/stages/cons/cons.bl") == "inspector"
        for path in ("declaration/trellis.yml", "declaration/period.yml", None):
            assert (app.inspector_content(path), app.lower_panel(path)) == (None, None)
        app.source.value = recipe.Source("recipe", "declaration/spec.a.yml")
        assert app.lower_panel(RECIPE.path) is None
        app.source.value = RECIPE
        app.open_path.value = "declaration/trellis.yml"
        _, rendered = solara.render(app.MainBar(None), handle_error=False)
        try:

            def inspector_toggle():
                (button,) = [
                    item
                    for item in rendered.find(v.Html, class_="bl-fold bl-toggle").widgets
                    if item.attributes["data-fold"] == "inspector"
                ]
                return button

            assert inspector_toggle().attributes == {
                "type": "button",
                "data-fold": "inspector",
                "title": "Nothing to inspect in trellis.yml",
                "aria-label": "Inspector",
                "aria-disabled": "true",
            }
            app.open_path.value = RECIPE.path
            assert inspector_toggle().attributes == {
                "type": "button",
                "data-fold": "inspector",
                "title": "Inspector",
                "aria-label": "Inspector",
            }
        finally:
            rendered.close()
    finally:
        clear_recipe_tab_state()


def test_m_10_a_change_of_source_clears_the_refusal_of_a_change_of_the_tab():
    """With the refusal of a change of the Recipe tab standing, showing
    another source clears it (specification §3.2), so that no mark stands
    on a control of another recipe."""
    entry = recipe.Entry("$disc_settings", True, RECIPE.path, "stages.disc.settings.all[0]", None)
    try:
        app.source.value = RECIPE
        app.choice_refusal.value = {
            "sentence": "the file no longer writes $disc_settings at stages.disc.settings.all[0]",
            "address": entry.address,
            "control": app.SELECT,
            "file": entry.file,
            "line": None,
            "made": 0.0,
        }
        app.show_source(recipe.Source("recipe", "declaration/spec.short.yml"))
        assert app.choice_refusal.value is None
    finally:
        app.source.value, app.view_mode.value, app.head.value = None, "stage", None
        app.choice_refusal.value, app.selected.value = None, None


def test_k_a_block_prints_an_entry_without_its_kind_s_folder_or_the_stage_s_own():
    """An entry of a stage's row of the Recipe tab prints without the kind's
    folder or the stage's own folder at its start, which the column's head and
    the row's key name (unit K, K-D30; design pass 9 §3):
    `calibration/durables` prints `durables`, `stages/tenure/methods.bl`
    `methods.bl` and the stage file `stages/tenure/tenure.bl` `tenure.bl`;
    another stage's folder, a path that holds the stage's folder further in, a
    slot and an entry that would print nothing stand as written."""
    assert app.block_text("calibration/durables", "tenure", "calibration") == "durables"
    assert app.block_text("stages/tenure/methods.bl", "tenure", "methods") == "methods.bl"
    assert app.block_text("stages/tenure/tenure.bl", "tenure") == "tenure.bl"
    for text, key, kind in (
        ("stages/disc/methods.bl", "cons", "methods"),
        ("../../portfolio-choice/declaration/stages/port/port.bl", "port", None),
        ("$fill", "tenure", "calibration"),
        ("calibration/", "tenure", "calibration"),
        ("settings/cons", "cons", "calibration"),
    ):
        assert app.block_text(text, key, kind) == text


def test_a_place_in_the_open_file_withdraws_a_switch_to_another_file(app_state, pension_folder):
    """A place asked in the file already open withdraws a switch to another
    file that still waits for the editor's answer, as a click on the open
    file does (`open_file`; AMD-MI-002 §3 rule 4). On the pension trellis,
    with the recipe open and a switch to the stage file of
    `periods[1]/worker_saving` waiting, the recipe's line 3 asked
    (`open_at`) keeps the recipe open once the editor answers, the cursor
    asked at line 3; the stage file then opens in its view."""
    app_state(pension_folder)
    app.source.value = RECIPE
    try:
        app.run_trellis()
        stage = trellis.occurrence_file(
            app.tab_folder.value, app.trellis_shown.value, (1, "worker_saving")
        )
        app.open_file(RECIPE.path)
        app.open_file(stage)
        app.open_at(RECIPE.path, 3)
        # the editor answers the flush request with the recipe's document
        held = app.buffers.value[RECIPE.path]
        app.on_change(
            {"path": RECIPE.path, "text": held["text"], "revision": held["document_revision"]}
        )
        assert app.open_path.value == RECIPE.path
        assert app.goto_request.value["line"] == 3
        app.open_file(stage)
        held = app.buffers.value[RECIPE.path]
        app.on_change(
            {"path": RECIPE.path, "text": held["text"], "revision": held["document_revision"]}
        )
        app.show_stage()
        assert (app.open_path.value, app.view_mode.value) == (stage, "stage")
    finally:
        clear_trellis_state()
        app.history.value, app.place_request.value = navigation.History(), None
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.switching.value, app.folder_read.value = None, False


def test_b_a_folder_opened_in_the_tab_forgets_the_trellis_left_and_new_trellis_shows_its_own(
    repository, app_state, consport_folder, pension_folder
):
    """With the trellis of `declaration/trellis.port-cons.yml` shown in the
    copy of cons-port, `periods 0–1` applied and `periods[1] / cons` the head,
    opening the pension copy in the tab (`open_model`) leaves nothing of the
    folder left: no source, no trellis or reading of it, no restriction, no
    head, the stage's view, and the pension's own sources. With the
    pension's trellis shown, new trellis from the form opens the new folder
    on its own trellis: its recipe `declaration/spec.yml` the source, the
    trellis view, nothing of the pension's trellis standing, the recipe open
    as text, and the next reading the new folder's; once its slots are
    filled, `declaration/stages/cons/cons.bl` opened from the tree is bound
    by the recipe as `periods[0] / cons`, the recipe among the files its
    watcher compares (specification §3.1, §4)."""
    work, _ = repository
    app_state(work)
    try:
        app.open_model(consport_folder)
        app.open_from_tree(PORT_CONS)
        assert app.run_trellis().shown is not None
        app.apply_restriction("periods 0–1")
        app.set_head((1, "cons"))
        assert app.view_mode.value == "trellis" and app.restriction.value is not None
        app.open_model(pension_folder)
        assert (app.source.value, app.trellis_shown.value, app.trellis_outcome.value) == (
            None,
            None,
            None,
        )
        assert (app.restriction.value, app.restriction_text.value, app.head.value) == (
            None,
            "",
            None,
        )
        assert (app.trellis_seen.value, app.view_mode.value) == ({}, "stage")
        assert app.sources.value == [RECIPE]
        app.open_from_tree(RECIPE.path)
        assert app.run_trellis().shown is not None
        app.submit_new_trellis(str(work), "lifecycle-demo", "", "demo_period", 6, DEMO_STAGES)
        created = (work / "lifecycle-demo").resolve()
        assert app.form_error.value == ""
        assert app.tab_folder.value.root == created
        assert (app.source.value, app.view_mode.value) == (RECIPE, "trellis")
        assert (app.trellis_shown.value, app.trellis_seen.value) == (None, {})
        assert app.open_path.value == RECIPE.path
        app.run_trellis()
        assert str(created / RECIPE.path) in app.trellis_seen.value
        recipe_file = created / RECIPE.path
        recipe_file.write_text(filled(recipe_file.read_text(encoding="utf-8")), encoding="utf-8")
        app.open_from_tree(CONS)
        # the editor answers the flush request with the recipe's document,
        # which completes the switch to the stage file
        held = app.buffers.value[RECIPE.path]
        app.on_change(
            {"path": RECIPE.path, "text": held["text"], "revision": held["document_revision"]}
        )
        assert app.open_path.value == CONS
        app.run_loop()
        shown = app.shown.value
        assert (shown.version, shown.occurrence) == ("bound", "periods[0] / cons")
        assert str(recipe_file) in shown.source_digests
    finally:
        app.source.value, app.view_mode.value, app.head.value = None, "stage", None
        app.trellis_shown.value, app.trellis_outcome.value, app.trellis_seen.value = None, None, {}
        app.restriction.value, app.restriction_text.value, app.restriction_refusal.value = (
            None,
            "",
            None,
        )
        app.restriction_opening.value = ""
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.commit_changes.value, app.commit_message.value = (), ""
        app.trellis_rebuild.value, app.rebind.value, app.rebind_sources.value = 0, 0, {}
        app.selected.value, app.drawing.value, app.folder_read.value = None, False, False


def test_b_the_name_under_the_cursor_is_read_against_the_shown_text(cons, cons_text):
    """The panel reads the name under the cursor from the shown object's own
    text at the line and the column the last cursor event recorded
    (specification §3.2, the reference view): the cursor on `ρ` at line 6,
    column 1, of cons.bl gives `ρ`, under the label `name` (unit K, Task 6);
    once the shown object is replaced by the elaboration of a text that
    writes `γ` there, the panel gives `γ`, with no new cursor event."""
    held = {
        "text": cons_text,
        "revision": 1,
        "digest": "",
        "document": cons_text,
        "document_revision": 1,
    }
    renamed = cons_text.replace("ρ", "γ")
    stage = model.elaborate_buffer(renamed, CONS).stage
    first = dataclasses.replace(shown_of(cons, cons_text, CONS), collection=model.collection(cons))
    second = dataclasses.replace(
        shown_of(stage, renamed, CONS), collection=model.collection(stage)
    )
    rendered = None
    try:
        app.open_path.value = CONS
        app.buffers.value = {CONS: held}
        app.shown.value = first
        app.on_cursor({"path": CONS, "revision": 1, "line": 6, "column": 1})
        _, rendered = solara.render(shown_panel(), handle_error=False)
        name = rendered.find(v.Html, class_="bl-block-label bl-name")
        assert [getattr(part, "children", part) for part in name.widget.children] == [
            ["name"],
            " ρ",
        ]
        app.shown.value = second
        name = rendered.find(v.Html, class_="bl-block-label bl-name")
        assert name.widget.children[1:] == [" γ"]
    finally:
        if rendered is not None:
            rendered.close()
        app.shown.value = None
        app.buffers.value = {}
        app.open_path.value = None
        app.cursor_line.value = None
        app.cursor_place.value = None


def test_b_the_name_view_marks_one_declaration_and_names_the_file_that_sets_the_name():
    """The panel's view of the name under the cursor (specification §3.2):
    `μ_ξ` of buffer_stock.bl, a derived parameter, is defined at line 13,
    column 1, and read again at line 18 by the law of ξ; the first
    occurrence, on the line of its definition, alone carries the word
    `declaration`, which carries its definition. The calibration location
    the test passes, line 7 of `declaration/calibration/portfolio.yml`, is
    written by hand and sets no `μ_ξ`; it shows how the view names such a
    location, by its file and line, `given at <file>, line <n>`: the link's
    own words hold no `calibration`, which names the digest of the status
    line, though its path may. The boxes `μ_ξ` lists stand under the label
    `boxes depending on μ_ξ` (unit K, Task 6), each of its two terms
    carrying its definition."""
    path = "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
    text = (ROOT / path).read_text(encoding="utf-8")
    stage = model.elaborate_buffer(text, path).stage
    report = model.name_report(stage, model.collection(stage), text, "μ_ξ")
    assert report.declaration == 13
    assert [line for line, _ in report.occurrences[:2]] == [13, 18]
    _, rendered = solara.render(
        app.NameView(report, ("declaration/calibration/portfolio.yml", 7)), handle_error=False
    )
    try:
        (listed,) = rendered.find(v.Html, class_="bl-name-occurrences bl-code-small").widgets
        first, *others = listed.children
        assert first.children[:2] == ["13:1", "  "]
        term = first.children[2]
        assert term.children == ["declaration"]
        assert term.attributes["title"] == app.TERMS["declaration"]
        assert [item.children for item in others] == [
            [f"{line}:{column}"] for line, column in report.occurrences[1:]
        ]
        (link,) = rendered.find(v.Html, class_="bl-link").widgets
        assert link.children == ["given at declaration/calibration/portfolio.yml, line 7"]
        assert report.boxes
        (label,) = rendered.find(v.Html, class_="bl-block-label").widgets
        assert [getattr(part, "children", part) for part in label.children] == [
            ["boxes"],
            " ",
            ["depending on"],
            " μ_ξ",
        ]
        terms = [part for part in label.children if not isinstance(part, str)]
        assert [term.attributes["title"] for term in terms] == [
            app.TERMS["box"],
            app.TERMS["depends on"],
        ]
    finally:
        rendered.close()


def test_t_a_table_change_asks_the_editor_for_its_replacements(cons, cons_text):
    """A set changed in a cell (unit T, rule 3) asks the editor for the
    replacements of both declarations of V[>] and names the text they were
    read from; a refused change leaves its sentence for its group and asks
    nothing. A change that arrives after the buffer changed is written into
    the buffer's text through the spans of that text's own parse, a line
    lower where a line was added above (Review Focus 1; unit R, R-D57); a
    change while the buffer's text does not parse asks nothing and is
    refused with the parse's sentence."""
    held = {
        "text": cons_text,
        "revision": 1,
        "digest": "",
        "document": cons_text,
        "document_revision": 1,
    }
    change = {"kind": "set", "group": "cntn/", "identity": "cons:cntn:V", "value": "ℝ"}
    try:
        app.open_path.value = CONS
        app.buffers.value = {CONS: held}
        app.shown.value = shown_of(cons, cons_text, CONS)
        app.on_table_change(change)
        request = app.edit_request.value
        assert request["edits"] == [
            {"line": 21, "column": 27, "end_line": 21, "end_column": 38, "text": "ℝ"},
            {"line": 31, "column": 21, "end_line": 31, "end_column": 32, "text": "ℝ"},
        ]
        assert (request["expected"], request["n"]) == (cons_text, 1)
        app.on_table_change({**change, "value": " "})
        assert app.table_note.value["group"] == "cntn/"
        assert app.table_note.value["path"] == CONS
        assert app.table_note.value["sentence"] == "the set of V[>] is empty"
        assert app.table_note.value["refused"]
        assert app.edit_request.value is request
        later = "# typed\n" + cons_text
        app.buffers.value = {CONS: {**held, "text": later}}
        app.on_table_change(change)
        written = app.edit_request.value
        assert written["edits"] == [
            {"line": 22, "column": 27, "end_line": 22, "end_column": 38, "text": "ℝ"},
            {"line": 32, "column": 21, "end_line": 32, "end_column": 32, "text": "ℝ"},
        ]
        assert (written["expected"], written["n"]) == (later, 2)
        broken = cons_text.replace("a = m_d - c", "a = m_d - - c")
        with pytest.raises(ValueError) as refused:
            source_spans(broken, CONS)
        app.buffers.value = {CONS: {**held, "text": broken}}
        app.on_table_change(change)
        assert app.edit_request.value is written
        assert app.table_note.value["sentence"] == model.refusal_of(refused.value, CONS).message
        assert app.table_note.value["refused"]
    finally:
        app.shown.value = None
        app.buffers.value = {}
        app.open_path.value = None
        app.edit_request.value = None
        app.table_note.value = None


def test_t_the_region_holds_the_head_and_the_three_tables(cons, cons_text):
    """The BellmanType panel under the editor (unit T, §4; AMD-MI-002 §5),
    with no state of the loop (unit R, R-D50) and no head (unit N, Task 2;
    design pass 10 §4): its strip `.bl-inspector-strip` holds the view tabs
    of the four tabs, Fields shown (unit M, Task 6), the open file's name
    `cons.bl` with its path as its hover, and the icon button `open wide`
    (N-I31); no `h2` and no close button stand in the panel. Then the
    component of the three tables with the rows of cons.bl, the role words,
    the completions and the shortcuts. `open wide` stands the panel in its
    wide panel, `.bl-wide`, and a second click returns it to its column.
    The tab Parameters, chosen, shows the parameter cons.bl declares with no
    value, since the stage is shown without a recipe: the tab names no file
    and says `no recipe values them`."""
    current = shown_of(cons, cons_text, CONS)
    _, rendered = solara.render(app.BellmanTypeRegion(current, CONS, True), handle_error=False)

    def tabs() -> list:
        # the view tabs of the four tabs, in the bar's order
        return [
            b
            for b in rendered.find(v.Html, tag="vscode-tab-header").widgets
            if "bl-class-tab" in b.class_.split()
        ]

    def section():
        return rendered.find(v.Html, tag="section").widget

    try:
        assert rendered.find(v.Html, tag="h2").widgets == []
        assert rendered.find(v.Html, class_="bl-head bl-region-head").widgets == []
        strip = rendered.find(v.Html, class_="bl-inspector-strip").widget
        tab_list, name, wide = strip.children
        assert tab_list.tag == "vscode-tabs"
        assert (drawn_text(name), name.attributes["title"]) == ("cons.bl", CONS)
        assert rendered.find(v.Html, class_="bl-region-close").widgets == []
        assert rendered.find(v.Html, class_="bl-class-state").widgets == []
        assert [(b.attributes["data-tab"], "bl-active" in b.class_.split()) for b in tabs()] == [
            ("Fields", True),
            ("Parameters", False),
            ("Settings", False),
            ("Methods", False),
        ]
        assert (wide.class_, wide.attributes["icon"]) == ("bl-region-wide", "window")
        tables = rendered.find(ipyvue.VueTemplate).widget
        assert [
            (group["key"], [row["field"] for row in group["rows"]]) for group in tables.groups
        ] == [
            ("arvl/", ["m", "l", "V[<]"]),
            ("dcsn/", ["m_d", "c", "V"]),
            ("cntn/", ["a", "V[>]"]),
        ]
        assert tables.groups[1]["rows"][1] == {
            "identity": "cons:dcsn:c",
            "field": "c",
            "set": "ℝ₊₊",
            "role": "!ctrl",
            "line": 16,
            "editable": True,
            "linked": True,
        }
        assert tables.role_choices == ["state", "!ctrl", "!vlu"]
        # the titles' texts and the roles' hovers (unit L, Task 29; design
        # pass 6 §§3.1 and 3.7)
        assert tables.perch_texts["arvl"] == {
            "sign": "≺",
            "word": "Arrival",
            "hover": "The information set at which the stage begins.",
            "add": "Add field at arrival",
        }
        assert tables.role_hovers["!vlu"] == "Value"
        assert tables.completions[:3] == ["Xm", "Xa", "ℝ"]
        assert tables.shortcuts["\\StrictlyPositiveReals"] == "ℝ₊₊"
        assert tables.disabled is False
        assert section().class_ == "bl-classification"
        wide.fire_event("click", {})
        assert app.region_wide.value == "types"
        assert section().class_ == "bl-classification bl-wide"
        assert rendered.find(v.Html, class_="bl-region-close").widgets == []
        rendered.find(v.Html, class_="bl-region-wide").widget.fire_event("click", {})
        assert app.region_wide.value is None
        assert section().class_ == "bl-classification"
        tabs()[1].fire_event("click", {})
        values = rendered.find(ipyvue.VueTemplate).widget
        assert (values.tab, values.file, values.sentence) == (
            "Parameters",
            None,
            "no recipe values them",
        )
        assert [(row["name"], row["detail"], row["value"]) for row in values.rows] == [
            ("ρ", "[1, inf)", "")
        ]
    finally:
        rendered.close()
        app.region_wide.value = None
        app.class_tab.value = "Fields"


def test_l_12_a_wide_panel_that_is_not_drawn_leaves_no_ground(app_state, scratch_folder):
    """Task 12 (AAS, L-D12; unit L's final judgment, §6 item 11): the
    BellmanType panel stands for a stage file alone, so its wide panel
    closes where a file that is no stage file is opened, or where the last
    file closes, while Details, which stands for every file, keeps its
    wide panel; and a panel folded while it stands wide leaves its wide
    panel (`on_region_folded`, which window.vue's fold calls), the fold of
    another region leaving the wide panel standing. So `WideGround` is
    drawn under no panel."""
    app_state(scratch_folder)

    def answer(path):
        # the editor's answer to the flush request of a switch or a close
        held = app.buffers.value[path]
        app.on_change({"path": path, "text": held["text"], "revision": held["document_revision"]})

    try:
        app.open_file(CONS)
        app.show_wide("types")
        app.open_file(RECIPE_FILE)
        answer(CONS)
        assert (app.open_path.value, app.region_wide.value) == (RECIPE_FILE, None)
        app.open_file(CONS)
        answer(RECIPE_FILE)
        app.show_wide("details")
        app.open_file(RECIPE_FILE)
        answer(CONS)
        assert (app.open_path.value, app.region_wide.value) == (RECIPE_FILE, "details")
        app.open_file(CONS)
        answer(RECIPE_FILE)
        app.show_wide("types")
        app.close_file(RECIPE_FILE)
        app.close_file(CONS)
        answer(CONS)
        assert (app.open_path.value, app.region_wide.value) == (None, None)
        app.show_wide("details")
        app.on_region_folded("types")
        assert app.region_wide.value == "details"
        app.on_region_folded("details")
        assert app.region_wide.value is None
    finally:
        app.region_wide.value = None
        app.open_path.value, app.buffers.value, app.results.value = None, {}, {}
        app.shown.value = None
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_t_a_refusal_is_shown_under_the_table_of_its_own_file(cons, cons_text):
    """A refused change (unit T, rule 3) belongs to the file and the
    revision on which it was made: the region of cons.bl at revision 1
    gives its tables the mark of the refused cell of cons.bl at revision 1,
    and no sentence, which stands in the list under the error mark
    (AMD-MI-002 §6a rule 1), and the region of a copy of cons.bl under
    another name, also at revision 1, gives its tables none."""
    note = {
        "group": "cntn/",
        "kind": "set",
        "identity": "cons:cntn:V",
        "sentence": "the set of V[>] is empty",
        "refused": True,
        "revision": 1,
        "path": CONS,
        "made": 0.0,
    }
    _, rendered = solara.render(
        app.BellmanTypeRegion(shown_of(cons, cons_text, CONS), CONS, True),
        handle_error=False,
    )
    try:
        app.table_note.value = note
        tables = rendered.find(ipyvue.VueTemplate).widget
        assert tables.refused == {"group": "cntn/", "kind": "set", "identity": "cons:cntn:V"}
        assert tables.note is None
        copy = shown_of(cons, cons_text, "cons_copy.bl")
        rendered.render(app.BellmanTypeRegion(copy, copy.path, True))
        assert rendered.find(ipyvue.VueTemplate).widget.refused is None
    finally:
        rendered.close()
        app.table_note.value = None


def test_t_a_refusal_is_not_shown_after_another_folder_opens(cons, cons_text, tmp_path, app_state):
    """A refused change (unit T, rule 3) belongs to the file of the tab's
    folder on which it was made: once another folder opens in the tab, as
    `new trellis` opens the folder it wrote, the region of that folder's
    file at the same path and revision gives its tables no note and no
    mark."""
    (tmp_path / "first").mkdir()
    (tmp_path / "second").mkdir()
    app_state(tmp_path / "first")
    app.table_note.value = {
        "group": "cntn/",
        "kind": "set",
        "identity": "cons:cntn:V",
        "sentence": "the set of V[>] is empty",
        "refused": True,
        "revision": 1,
        "path": CONS,
        "made": 0.0,
    }
    app.open_model(tmp_path / "second")
    _, rendered = solara.render(
        app.BellmanTypeRegion(shown_of(cons, cons_text, CONS), CONS, True),
        handle_error=False,
    )
    try:
        tables = rendered.find(ipyvue.VueTemplate).widget
        assert (tables.note, tables.refused) == (None, None)
    finally:
        rendered.close()
        app.table_note.value = None


def test_r_the_fields_tables_read_the_parse_of_a_refused_text_and_mark_the_row_it_names(
    cons, cons_text
):
    """The Fields tab under a refusal of the construction (unit R, R-D57;
    amendment 02 rulings 7, 8 and 10): the region given the construction
    of cons.bl and the parse of a later text that lists h and k among the
    outputs of dcsn_to_cntn, which the package refuses since no line
    defines h, shows the rows of that parse, editable. The continuation
    table lists a, h, k and V[>], h and k on line 16 with their sets
    and roles and no link to a box, since the construction holds neither
    field, the other rows linked. The row of h, whose listing the
    refusal's record names as a related location, is marked with the
    refusal's sentence, and no other row is (Model Interface 0.9 §4).
    Given the same parse with `editable` false, as while a later text does
    not parse, the tables keep those rows, locked."""
    later = cons_text.replace("(a : Xa) : !cntn", "(a : Xa, h : ℝ₊, k : ℝ₊) : !cntn")
    assert changed_lines(cons_text, later) == [16]
    (refusal,) = model.elaborate_buffer(later, CONS).diagnostics
    (listed,) = refusal.related
    assert (refusal.rule, listed.role, listed.file, listed.line) == (
        "output-defined", "listed output", CONS, 16
    )
    parsed = app.parse_text(CONS, later)
    current = shown_of(cons, cons_text, CONS)
    _, rendered = solara.render(
        app.BellmanTypeRegion(current, CONS, True, parsed, (refusal,)),
        handle_error=False,
    )

    def continuation() -> list:
        # each row of the continuation table as the component takes it
        tables = rendered.find(ipyvue.VueTemplate).widget
        (group,) = [group for group in tables.groups if group["key"] == "cntn/"]
        return [
            (row["field"], row["set"], row["role"], row["line"], row["editable"], row["linked"])
            for row in group["rows"]
        ]

    rows = [
        ("a", "Xa", "state", 16, True, True),
        ("h", "ℝ₊", "state", 16, True, False),
        ("k", "ℝ₊", "state", 16, True, False),
        ("V[>]", "[-inf, inf)", "!vlu", 20, True, True),
    ]
    try:
        tables = rendered.find(ipyvue.VueTemplate).widget
        assert tables.disabled is False
        assert continuation() == rows
        assert tables.named == {"cons:cntn:h": model.sentence(refusal)}
        rendered.render(app.BellmanTypeRegion(current, CONS, False, parsed, (refusal,)))
        tables = rendered.find(ipyvue.VueTemplate).widget
        assert tables.disabled is True
        assert continuation() == rows
    finally:
        rendered.close()


# --- item 3 of the brief on the trellis view's load time,
# `trellis-load-time.md` §3 ---


def test_trellis_load_item_3_the_window_writes_periods_0_2_into_the_bar_of_a_long_trellis(
    app_state, tmp_path, consport_folder
):
    """Item 3 (specification §3.1: the full trellis is one click away): a
    copy of the durables folder shown with the bar empty writes `periods
    0–2` into the bar and applies it before the source is set, so that the
    source's first reading, which the trellis's task begins when the source
    changes, is under it; that reading draws the ten occurrences of periods
    0 to 2, the status line naming the restriction and the trellis's 51
    periods, `periods 0–2 of 51 (10 occurrences)`; the button `whole
    trellis` then draws the 154 occurrences under no restriction. The
    trellis of lesson 05, of six periods, shown with the bar empty, leaves
    the bar empty and is drawn whole."""
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    app_state(durables)
    # the restriction that stands each time the source is set
    standing = []
    unsubscribe = app.source.subscribe(lambda found: standing.append(app.restriction.value))
    try:
        app.show_source(RECIPE)
        assert standing == [trellis.parse_restriction("periods 0–2")]
        assert app.restriction_text.value == "periods 0–2"
        assert app.restriction.value == trellis.parse_restriction("periods 0–2")
        outcome = app.run_trellis()
        assert outcome.shown.restriction == app.restriction.value
        assert outcome.shown.counts == {"periods": 51, "occurrences": 154, "shown": 10}
        line, _ = app.trellis_status_parts(app.trellis_outcome.value, app.trellis_shown.value)
        assert ("periods 0–2", "restriction") in line
        assert " · shown periods 0–2 of 51 (10 occurrences)" in "".join(text for text, _ in line)
        app.apply_restriction("")
        whole = app.run_trellis()
        assert whole.shown.restriction is None and whole.shown.counts["shown"] == 154
        line, rest = app.trellis_status_parts(app.trellis_outcome.value, app.trellis_shown.value)
        assert " · shown " not in "".join(text for text, _ in line + rest)
        app_state(consport_folder)
        app.show_source(recipe.Source("recipe", PORT_CONS_RECIPE))
        assert (app.restriction_text.value, app.restriction.value) == ("", None)
        assert app.run_trellis().shown.counts == {"periods": 6, "occurrences": 18, "shown": 18}
    finally:
        unsubscribe()
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_trellis_load_item_3_a_short_source_after_a_long_one_opens_whole_with_the_bar_empty(
    app_state, pension_folder, consport_folder, cagetti_folder
):
    """The opening restriction belongs to the source the window wrote it
    for (item 3: a trellis of six periods or fewer opens whole): the
    pension trellis, of fifteen periods, writes `periods 0–2` into the
    empty bar; lesson 05, of six periods, shown next, empties the bar, and
    its reading draws the whole trellis, the status line naming no
    restriction. The pension trellis shown again writes `periods 0–2`
    again, and the Cagetti–De Nardi trellis file shown next, which the
    package refuses to read, empties the bar, its reading answering the
    refusal as before."""
    app_state(pension_folder)
    try:
        app.show_source(RECIPE)
        assert app.restriction_text.value == "periods 0–2"
        app_state(consport_folder)
        app.show_source(recipe.Source("recipe", PORT_CONS_RECIPE))
        assert (app.restriction_text.value, app.restriction.value) == ("", None)
        outcome = app.run_trellis()
        assert outcome.shown.counts == {"periods": 6, "occurrences": 18, "shown": 18}
        line, rest = app.trellis_status_parts(app.trellis_outcome.value, app.trellis_shown.value)
        assert " · shown " not in "".join(text for text, _ in line + rest)
        app_state(pension_folder)
        app.show_source(RECIPE)
        assert app.restriction_text.value == "periods 0–2"
        app_state(cagetti_folder)
        app.show_source(recipe.Source("trellis", "declaration/trellis.yml"))
        assert (app.restriction_text.value, app.restriction.value) == ("", None)
        assert app.run_trellis().refusal.rule == "trellis-file-shape"
    finally:
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_trellis_load_item_3_a_restriction_the_reader_wrote_stays_for_a_short_source(
    app_state, pension_folder, consport_folder
):
    """A text the reader wrote stays in the bar for the next source: the
    pension trellis writes `periods 0–2` into the empty bar, the reader
    applies `periods 0–1`, and lesson 05, of six periods, shown next, keeps
    `periods 0–1` in the bar and as the restriction held."""
    app_state(pension_folder)
    try:
        app.show_source(RECIPE)
        assert app.restriction_text.value == "periods 0–2"
        app.apply_restriction("periods 0–1")
        app_state(consport_folder)
        app.show_source(recipe.Source("recipe", PORT_CONS_RECIPE))
        assert app.restriction_text.value == "periods 0–1"
        assert app.restriction.value == trellis.parse_restriction("periods 0–1")
    finally:
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_a_link_s_restriction_is_replaced_by_the_next_recipe_s_opening_text(
    app_state, scratch_durables
):
    """A restriction that a link into a position writes is the window's
    text, not the reader's (ruling R39): on a copy of the durables folder,
    with the recipe `declaration/spec.yml` shown under its opening text
    `periods 0–2`, the link of the row `periods` of Details to
    `periods[40]/keeper_cons` writes `periods 40` into the bar, and the
    recipe `declaration/spec.two-stages.yml` shown next writes its own
    opening text, `periods 0–2`; the breadcrumb's period at
    `periods[40]/keeper_cons` of that recipe writes `periods 40` again, and
    `declaration/spec.yml` shown next writes `periods 0–2`.

    The copy holds a recipe of three periods, which opens whole:
    `declaration/spec.short.yml`, the text of `spec.two-stages.yml` naming
    the trellis file `declaration/trellis.short.yml`, the text of
    `trellis.two-stages.yml` with its period template repeated twice, not
    fifty times. A step back after the link restores the restriction that
    stood before it, and a step forward restores the link's (AMD-MI-002 §3
    rule 4), with `spec.yml` open in the editor, so that the link records
    the place it leaves. A restriction restored is the window's text where
    it is the recipe's opening text (ruling R57) or `periods h` of the
    place's position (ruling R59), and otherwise the reader's. The text
    `periods 1–2`, which the reader applied before the link, is restored by
    the step back and stays in the bar when the short recipe is shown next.
    The opening text `periods 0–2`, restored by the step back, and
    `periods 40`, restored by the step forward, are each the window's
    again, so that the short recipe shown next opens by its own rule,
    whole, under the empty text."""
    declaration = scratch_durables / "declaration"
    trellis_text = (declaration / "trellis.two-stages.yml").read_text(encoding="utf-8")
    (declaration / "trellis.short.yml").write_text(
        trellis_text.replace("repeat: 50", "repeat: 2"), encoding="utf-8"
    )
    recipe_text = (declaration / "spec.two-stages.yml").read_text(encoding="utf-8")
    (declaration / "spec.short.yml").write_text(
        recipe_text.replace("trellis: trellis.two-stages.yml", "trellis: trellis.short.yml"),
        encoding="utf-8",
    )
    two_stages = recipe.Source("recipe", "declaration/spec.two-stages.yml")
    short = recipe.Source("recipe", "declaration/spec.short.yml")
    app_state(scratch_durables)
    try:
        assert len(recipe.read_source(app.tab_folder.value, short)["periods"]) == 3
        app.show_recipe(RECIPE)
        assert app.restriction_text.value == "periods 0–2"
        app.show_occurrence(RECIPE, (40, "keeper_cons"))
        assert app.restriction_text.value == "periods 40"
        app.show_recipe(two_stages)
        assert app.restriction_text.value == "periods 0–2"
        assert app.restriction.value == trellis.parse_restriction("periods 0–2")
        app.show_period(two_stages, (40, "keeper_cons"))
        assert app.restriction_text.value == "periods 40"
        app.show_recipe(RECIPE)
        assert app.restriction_text.value == "periods 0–2"
        assert app.restriction.value == trellis.parse_restriction("periods 0–2")
        app.open_file(RECIPE.path)
        # the reader's text, which the select's menu applies, a choice or
        # Enter at its foot alike (unit K, K-D17)
        app.apply_restriction("periods 1–2")
        app.show_occurrence(RECIPE, (40, "keeper_cons"))
        assert app.restriction_text.value == "periods 40"
        app.go_back()
        assert app.restriction_text.value == "periods 1–2"
        app.show_recipe(short)
        assert app.restriction_text.value == "periods 1–2"
        assert app.restriction.value == trellis.parse_restriction("periods 1–2")
        # the opening text, restored by a step back, after the empty text
        # that `all` of the select's menu writes with every key ticked
        app.apply_restriction("")
        app.show_recipe(RECIPE)
        assert app.restriction_text.value == "periods 0–2"
        app.show_occurrence(RECIPE, (40, "keeper_cons"))
        assert app.restriction_text.value == "periods 40"
        app.go_back()
        assert app.restriction_text.value == "periods 0–2"
        app.show_recipe(short)
        assert (app.restriction_text.value, app.restriction.value) == ("", None)
        # the link's text, restored by a step forward
        app.show_recipe(RECIPE)
        assert app.restriction_text.value == "periods 0–2"
        app.show_occurrence(RECIPE, (40, "keeper_cons"))
        app.go_back()
        app.go_forward()
        assert app.restriction_text.value == "periods 40"
        app.show_recipe(short)
        assert (app.restriction_text.value, app.restriction.value) == ("", None)
    finally:
        clear_trellis_state()
        app.history.value, app.place_request.value = navigation.History(), None
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_a_click_in_the_tree_on_the_open_stage_file_keeps_its_position(
    app_state, durables_folder
):
    """A click in the tree on the stage file already open changes nothing
    (ruling R55; AMD-MI-002 §3 rule 4): `keeper_cons.bl` of the durables
    recipe opened from the tree is bound as its first occurrence, the head
    `periods[0] / keeper_cons`; `periods[3]` chosen on the occurrence line
    becomes the head, and a second click on the file in the tree keeps that
    head and the stage's view and records no place."""
    app_state(durables_folder)
    try:
        app.show_recipe(RECIPE)
        app.open_from_tree(KEEPER_CONS)
        assert (app.open_path.value, app.view_mode.value) == (KEEPER_CONS, "stage")
        app.choose_position((3, "keeper_cons"))
        recorded = app.history.value
        app.open_from_tree(KEEPER_CONS)
        assert (app.head.value, app.view_mode.value) == ((3, "keeper_cons"), "stage")
        assert app.history.value == recorded
    finally:
        clear_trellis_state()
        app.history.value, app.place_request.value = navigation.History(), None
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


# --- change 2 of the same brief, §1: a reading that changes nothing is not
# repeated, at the page's opening as well ---


def test_trellis_load_the_page_opens_the_durables_folder_with_one_reading_of_its_trellis(
    app_state, monkeypatch, tmp_path
):
    """The page rendered over a copy of the durables folder opens on the
    folder's recipe under `periods 0–2` and reads its trellis once:
    `trellis.show_trellis`, the function the trellis's task calls, is called
    once, for the source `declaration/spec.yml` and that restriction, and
    the trellis it answers shows the ten occurrences of periods 0 to 2. Each
    call of the task carries the values of the render that made it: the
    first render names no source, so its run reads nothing, and the render
    after the opening starts the only reading."""
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    app_state(durables)
    show = trellis.show_trellis
    # each call of the reading, as its source and its restriction
    calls = []
    # the sources of the calls that have not returned
    running = []

    # the stand-in takes every keyword `show_trellis` takes, `initial`
    # among them since unit S, so that the page's call reaches the reading
    # (SE-41)
    def counted(folder, source, restriction=None, previous=None, unsaved=None, initial=False):
        calls.append((source, restriction))
        running.append(source)
        try:
            return show(folder, source, restriction, previous, unsaved, initial=initial)
        finally:
            running.remove(source)

    monkeypatch.setattr(trellis, "show_trellis", counted)
    threads = set(threading.enumerate())
    _, rendered = solara.render(app.Page(), handle_error=False)
    try:
        # the trellis shown, which the task records after the outcome
        wait_until(
            lambda: app.trellis_shown.value is not None and not running,
            120.0,
            "the trellis shown",
        )
        assert calls == [(RECIPE, trellis.parse_restriction("periods 0–2"))]
        assert app.trellis_shown.value.counts == {"periods": 51, "occurrences": 154, "shown": 10}
    finally:
        rendered.close()
        try:
            # the threads of the page's tasks and of its watcher write the
            # values cleared below
            wait_until(
                lambda: set(threading.enumerate()) <= threads,
                30.0,
                "the end of the page's threads",
            )
        finally:
            clear_trellis_state()
            app.sources.value, app.tree.value, app.git_line.value = [], [], ""
            app.folder_read.value = False


def test_trellis_load_a_short_source_shown_after_durables_is_read_once_and_durables_not_again(
    app_state, monkeypatch, tmp_path
):
    """The page rendered over a copy of the durables folder, once the trellis
    of `declaration/spec.yml` stands under `periods 0–2`, is shown a recipe
    of two periods that the test writes into the copy,
    `declaration/spec.short.yml`: `trellis.show_trellis`, the function the
    trellis's task calls, is called once more, for that recipe and the whole
    trellis, and not again for `declaration/spec.yml`. The window empties the
    bar for the short recipe before it sets the source, and the trellis's
    effect makes no call while the window writes that text, so that the
    change of restriction starts no reading of `declaration/spec.yml`."""
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    declaration = durables / "declaration"
    # the trellis file of two periods: the terminal period and one period of
    # the template before it; and the recipe that reads it
    written = (declaration / "trellis.yml").read_text(encoding="utf-8")
    (declaration / "trellis.short.yml").write_text(
        written.replace("repeat: 50", "repeat: 1"), encoding="utf-8"
    )
    written = (declaration / "spec.yml").read_text(encoding="utf-8")
    (declaration / "spec.short.yml").write_text(
        written.replace("trellis: trellis.yml", "trellis: trellis.short.yml"), encoding="utf-8"
    )
    short = recipe.Source("recipe", "declaration/spec.short.yml")
    app_state(durables)
    show = trellis.show_trellis
    # each call of the reading, as its source and its restriction
    calls = []
    # the sources of the calls that have not returned
    running = []

    # the stand-in takes every keyword `show_trellis` takes, `initial`
    # among them since unit S, so that the page's call reaches the reading
    # (SE-41)
    def counted(folder, source, restriction=None, previous=None, unsaved=None, initial=False):
        calls.append((source, restriction))
        running.append(source)
        try:
            return show(folder, source, restriction, previous, unsaved, initial=initial)
        finally:
            running.remove(source)

    monkeypatch.setattr(trellis, "show_trellis", counted)
    threads = set(threading.enumerate())
    _, rendered = solara.render(app.Page(), handle_error=False)
    try:
        wait_until(
            lambda: app.trellis_shown.value is not None and not running,
            120.0,
            "the trellis of declaration/spec.yml shown",
        )
        assert calls == [(RECIPE, trellis.parse_restriction("periods 0–2"))]
        app.show_source(short)
        # the short recipe's trellis shown, which the task records after its
        # call returns, and no call of the reading still running
        wait_until(
            lambda: getattr(app.trellis_shown.value, "source", None) == short and not running,
            120.0,
            "the trellis of the recipe of two periods shown",
        )
        assert calls[1:] == [(short, None)]
        assert app.trellis_shown.value.counts == {"periods": 2, "occurrences": 7, "shown": 7}
    finally:
        rendered.close()
        try:
            # the threads of the page's tasks and of its watcher write the
            # values cleared below
            wait_until(
                lambda: set(threading.enumerate()) <= threads,
                30.0,
                "the end of the page's threads",
            )
        finally:
            clear_trellis_state()
            app.sources.value, app.tree.value, app.git_line.value = [], [], ""
            app.folder_read.value = False


# --- unit J: the trellis loop reads the tab's unsaved buffers ---

# the trellis of lesson 05 as the tab's source
LESSON = recipe.Source("recipe", PORT_CONS_RECIPE)
# the connector of the trellis file of `emptied_port_cons`, emptied and
# filled
EMPTIED_ENTRY = "    connectors:\n      - {}\n"
FILLED_ENTRY = "    connectors:\n      - {w: m}\n"


def test_the_trellis_task_starts_again_when_an_unsaved_input_changes(app_state, tmp_path):
    """Lesson 05's emptied trellis read by the trellis's task; its trellis
    file then opened and typed into, the connector filled. The task's fourth
    value, the unsaved inputs, now names the buffer and its revision, so the
    page's effect starts the task again (brief rule 5). A run with the
    values of the render before the typing records nothing; a run with the
    current values records a trellis that draws the join, marks the buffer
    in `buffered`, and whose status line reads `unsaved` after `trellis`
    until the buffer is saved."""
    copy = emptied_port_cons(tmp_path)
    app_state(copy)
    app.source.value = LESSON
    app.view_mode.value = "trellis"
    try:
        first = app.run_trellis()
        assert app.trellis_outcome.value is first and app.unsaved_inputs() == ()
        before = (app.source.value, app.restriction.value, app.trellis_rebuild.value, ())
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"].replace(EMPTIED_ENTRY, FILLED_ENTRY)
        app.on_change(
            {"path": PORT_CONS, "text": text, "revision": held["document_revision"]}
        )
        path = str((copy / PORT_CONS).resolve())
        revision = app.buffers.value[PORT_CONS]["revision"]
        assert app.unsaved_inputs() == ((path, revision),)
        stale = app.run_trellis(before)
        assert stale.shown is not None and app.trellis_outcome.value is first
        current = app.run_trellis()
        assert app.trellis_outcome.value is current and app.trellis_shown.value is current.shown
        assert "w → m" in join_labels(current.shown.collection, "forward")
        assert current.shown.buffered == {path: revision}
        line, _ = app.trellis_status_parts(current, current.shown)
        assert line[2:5] == [("trellis", "trellis"), (" · ", None), ("unsaved", "unsaved")]
        app.on_save({"path": PORT_CONS, "text": text, "revision": held["document_revision"]})
        assert app.unsaved_texts() == {}
        line, rest = app.trellis_status_parts(current, current.shown)
        assert ("unsaved", "unsaved") not in line + rest
    finally:
        clear_trellis_state()


def test_the_watcher_leaves_a_buffered_input_alone(monkeypatch, app_state, tmp_path):
    """Lesson 05's emptied trellis read with its trellis file's buffer, the
    connector filled, unsaved: the watcher compares the text the reading
    took, the buffer's, and raises the trellis's count at no tick, where a
    comparison with the file on disk would raise it at every tick; a
    calibration the reading read from disk, then saved with another
    discount factor, raises the count once (spec 0.4 §3.1)."""
    copy = emptied_port_cons(tmp_path)
    app_state(copy)
    monkeypatch.setattr(app, "WATCH_SECONDS", 0.05)
    app.source.value = LESSON
    cancel = threading.Event()
    watcher = threading.Thread(target=app.watch, args=(cancel,))
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"].replace(EMPTIED_ENTRY, FILLED_ENTRY)
        app.on_change(
            {"path": PORT_CONS, "text": text, "revision": held["document_revision"]}
        )
        assert app.run_trellis().shown.buffered
        count = app.trellis_rebuild.value
        watcher.start()
        time.sleep(20 * app.WATCH_SECONDS)
        assert app.trellis_rebuild.value == count
        folder = model.open_folder(copy)
        calibration = "declaration/calibration/portfolio.yml"
        found = model.read_file(folder, calibration)
        changed = found.text.replace("β: 0.96", "β: 0.95")
        assert model.save_file(folder, calibration, changed, found.digest).saved
        wait_until(lambda: app.trellis_rebuild.value == count + 1, 10.0, "the count raised")
        time.sleep(10 * app.WATCH_SECONDS)
        assert app.trellis_rebuild.value == count + 1
    finally:
        cancel.set()
        if watcher.is_alive():
            watcher.join()
        clear_trellis_state()


def test_an_unsaved_stage_file_raises_the_trellis_count_at_no_tick(
    monkeypatch, app_state, scratch_consport
):
    """Ruling J-P2: lesson 05's trellis read, then the consumption stage's
    file it reads opened and typed into, unsaved. The trellis loop takes no
    stage file's buffer, so the unsaved inputs name none, a reading with
    the buffer answers the trellis held, and the watcher, which compares the
    stage file on disk, raises the trellis's count at no tick; the inputs
    are no longer current, so the gestures are disabled (spec 0.4 §3.3)."""
    app_state(scratch_consport)
    monkeypatch.setattr(app, "WATCH_SECONDS", 0.05)
    app.source.value = LESSON
    cancel = threading.Event()
    watcher = threading.Thread(target=app.watch, args=(cancel,))
    try:
        held = app.run_trellis().shown
        app.open_file(SHARED_CONS)
        buffer = app.buffers.value[SHARED_CONS]
        app.on_change(
            {
                "path": SHARED_CONS,
                "text": buffer["text"] + "\n# a comment typed\n",
                "revision": buffer["document_revision"],
            }
        )
        assert app.unsaved_inputs() == ()
        unsaved = app.unsaved_texts()
        assert list(unsaved) == [str((scratch_consport / SHARED_CONS).resolve())]
        assert not trellis.inputs_current(held, trellis.texts_of(unsaved))
        folder = model.open_folder(scratch_consport)
        assert trellis.show_trellis(folder, LESSON, previous=held, unsaved=unsaved).shown is held
        count = app.trellis_rebuild.value
        watcher.start()
        time.sleep(20 * app.WATCH_SECONDS)
        assert app.trellis_rebuild.value == count
    finally:
        cancel.set()
        if watcher.is_alive():
            watcher.join()
        clear_trellis_state()


def test_the_export_of_a_trellis_records_which_inputs_were_buffers(app_state, tmp_path):
    """Lesson 05's emptied trellis read with its trellis file's buffer, the
    connector filled, unsaved, and exported from the trellis view: the
    export's record marks the trellis file `buffer`, with the digest of the
    buffer's text, and no other file; and the graph JSON exported is made
    with the keyword `unjoined` off, so it marks no port unjoined, where
    the view held marks the ports of the emptied mapping (brief rule 5)."""
    copy = emptied_port_cons(tmp_path)
    app_state(copy)
    app.source.value = LESSON
    app.view_mode.value = "trellis"
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"].replace(EMPTIED_ENTRY, FILLED_ENTRY)
        app.on_change(
            {"path": PORT_CONS, "text": text, "revision": held["document_revision"]}
        )
        shown = app.run_trellis().shown
        assert collection_unjoined_ports(shown.collection)
        app.run_export()
        assert app.git_answer.value["refused"] is False
        views = copy / model.EXPORT_FOLDER
        record = json.loads((views / "trellis.export.json").read_text(encoding="utf-8"))
        marked = {entry["path"]: entry for entry in record["source_files"] if "buffer" in entry}
        assert list(marked) == [PORT_CONS] and marked[PORT_CONS]["buffer"] is True
        assert marked[PORT_CONS]["sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
        (graph_name,) = [name for name in record["generated"] if name.endswith(".graph.json")]
        exported = json.loads((views / graph_name).read_text(encoding="utf-8"))
        assert collection_unjoined_ports(exported) == set()
    finally:
        clear_trellis_state()


# the connector of the trellis file of `emptied_port_cons` filled with a line
# that closes a cycle: `disc` continues to `a`, which `cons` takes as `m`
CYCLE_ENTRY = "    connectors:\n      - {a: m}\n"


def test_a_refused_line_of_the_open_trellis_file_is_a_diagnostic_with_its_action(
    app_state, tmp_path
):
    """Brief rule 8 and spec 0.4 §3.1, §3.3: lesson 05's emptied trellis read
    and its file opened; a comment typed above `periods:`, then the
    connector filled with `{a: m}`, which closes a cycle. The reading of that
    buffer is refused, and `trellis_diagnostics` answers one record, in the
    form the editor's `setDiagnostics` takes, with the package's sentence.
    With no gesture recorded, the record stands at the place the package
    names, counted in the buffer's text: the package names the period,
    `periods[0]`, whose entry stands at line 8 of the buffer and at line 7
    on disk, and the record underlines that line's text; the list under the
    error mark links the sentence to that line. With `gesture_made` naming
    the file and holding the buffer's text as the text the gesture made,
    the record stands at the typed line, the connector's line 16, and
    carries the action `take the line out`, whose one replacement, applied
    while the document is that text, restores the text before the gesture;
    the list links the sentence to line 16. After a change event with
    another text the record and the list's link return to line 8 and the
    record carries no action. Another file of the folder has no record."""
    copy = emptied_port_cons(tmp_path)
    app_state(copy)
    app.source.value = LESSON
    app.view_mode.value = "trellis"
    try:
        assert app.run_trellis().refusal is None
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        before = "# a line typed above the trellis\n" + held["text"]
        after = before.replace(EMPTIED_ENTRY, CYCLE_ENTRY)
        app.on_change({"path": PORT_CONS, "text": after, "revision": held["document_revision"]})
        refusal = app.run_trellis().refusal
        assert (refusal.rule, refusal.address) == ("period-join-cycle", "periods[0]")
        assert after.split("\n")[7] == "  - stages:"
        record = {
            "line": 8,
            "column": 3,
            "end_line": 8,
            "end_column": 12,
            "message": refusal.message,
            "severity": "error",
        }
        assert app.trellis_diagnostics(PORT_CONS) == [record]

        def linked():
            # the lines of the list under the error mark that hold the sentence
            listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
            return [entry for entry in listed if entry[0] == refusal.message]

        assert linked() == [(refusal.message, PORT_CONS, 8)]
        app.gesture_made.value = {"path": PORT_CONS, "before": before, "after": after}
        assert after.split("\n")[15] == "      - {a: m}"
        (taken,) = app.trellis_diagnostics(PORT_CONS)
        edit = trellis.restoring_edit(before, after)
        assert taken == {
            **record,
            "line": 16,
            "column": 7,
            "end_line": 16,
            "end_column": 15,
            "action": {"name": "take the line out", "edits": [edit], "expected": after},
        }
        assert applied(after, [model.Replacement(**edit)]) == before
        assert linked() == [(refusal.message, PORT_CONS, 16)]
        typed = after + "# a comment typed after the gesture\n"
        app.on_change({"path": PORT_CONS, "text": typed, "revision": held["document_revision"]})
        assert app.trellis_diagnostics(PORT_CONS) == [record]
        assert linked() == [(refusal.message, PORT_CONS, 8)]
        assert app.trellis_diagnostics("declaration/calibration/portfolio.yml") == []
        assert app.trellis_diagnostics(None) == []
    finally:
        app.gesture_made.value = None
        clear_trellis_state()


def test_a_refused_gesture_is_marked_at_its_line_where_the_package_names_another_file(
    app_state, tmp_path
):
    """Spec 0.4 §3.1, the typed line: the portfolio model whose trellis entry
    writes its own connectors (`emptied_portfolio_with_entry_connectors`),
    read, and `{a: m}`, which closes a cycle, typed into the entry's
    connectors in the buffer of `trellis.yml`. The package addresses the
    cycle to `periods[0]`, whose place is the period file the entry names,
    `period.yml` at line 1, so with no gesture recorded `trellis.yml` has no
    record. With `gesture_made` naming `trellis.yml` and holding the
    buffer's text, the record stands at the typed line, the entry's line 8
    of `trellis.yml`, with the action `take the line out`; `period.yml` has
    none; and the list under the error mark links the sentence to that
    line."""
    copy = emptied_portfolio_with_entry_connectors(tmp_path)
    app_state(copy)
    app.source.value = RECIPE
    app.view_mode.value = "trellis"
    trellis_file, period_file = "declaration/trellis.yml", "declaration/period.yml"
    try:
        assert app.run_trellis().refusal is None
        app.open_file(trellis_file)
        held = app.buffers.value[trellis_file]
        before = held["text"]
        after = before.replace("connectors: [{}]", "connectors: [{a: m}]")
        entry = "  - {template: period.yml, repeat: 6, connectors: [{a: m}]}"
        assert after.split("\n")[7] == entry
        app.on_change({"path": trellis_file, "text": after, "revision": held["document_revision"]})
        refusal = app.run_trellis().refusal
        assert (refusal.rule, refusal.address) == ("period-join-cycle", "periods[0]")
        assert app.trellis_diagnostics(trellis_file) == []
        assert [record["line"] for record in app.trellis_diagnostics(period_file)] == [1]
        app.gesture_made.value = {"path": trellis_file, "before": before, "after": after}
        (taken,) = app.trellis_diagnostics(trellis_file)
        edit = trellis.restoring_edit(before, after)
        assert taken == {
            "line": 8,
            "column": 3,
            "end_line": 8,
            "end_column": len(entry) + 1,
            "message": refusal.message,
            "severity": "error",
            "action": {"name": "take the line out", "edits": [edit], "expected": after},
        }
        assert app.trellis_diagnostics(period_file) == []
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert [item for item in listed if item[0] == refusal.message] == [
            (refusal.message, trellis_file, 8)
        ]
    finally:
        app.gesture_made.value = None
        clear_trellis_state()


# --- unit J: the editor's answer to an edit ---


def test_on_applied_records_the_editors_answer(cons, cons_text):
    """Brief rule 7 and J-D12, J-D30: a role entered in a cell of the
    classification table asks the editor for its replacement. The editor's
    event `applied`, which carries the path and the revision of the document
    it held, the request's counter and whether the edit applied, is
    recorded in `edit_answer` as the path, the counter and the answer. It
    changes nothing else: the buffer, the request and the table's note stand
    as they were, since nothing reads the answer to a request of the table
    (J-D13). A later answer, a false one, replaces the first."""
    held = {
        "text": cons_text,
        "revision": 1,
        "digest": "",
        "document": cons_text,
        "document_revision": 1,
    }
    change = {"kind": "role", "group": "dcsn/", "identity": "cons:dcsn:m_d", "value": "!ctrl"}
    try:
        app.open_path.value = CONS
        app.buffers.value = {CONS: held}
        app.shown.value = shown_of(cons, cons_text, CONS)
        app.on_table_change(change)
        request, note, buffers = app.edit_request.value, app.table_note.value, app.buffers.value
        assert request["n"] == 1 and len(request["edits"]) == 1
        assert note["sentence"] == "@ !ctrl written to line 13" and not note["refused"]
        app.on_applied({"path": CONS, "revision": 1, "n": 1, "applied": True})
        assert app.edit_answer.value == {"path": CONS, "n": 1, "applied": True}
        assert app.edit_request.value is request
        assert app.table_note.value is note
        assert app.buffers.value is buffers
        app.on_applied({"path": CONS, "revision": 1, "n": 2, "applied": False})
        assert app.edit_answer.value == {"path": CONS, "n": 2, "applied": False}
    finally:
        app.shown.value = None
        app.buffers.value = {}
        app.open_path.value = None
        app.edit_request.value = None
        app.table_note.value = None
        app.edit_answer.value = None


# --- unit J: the seven steps of a gesture ---

# the drag within `periods[2]` from `port`'s `m_next` to `cons`'s `m`, and
# the drag from `disc`'s `a` in `periods[3]` to `port`'s `k` in `periods[2]`,
# the period after it in time, each port `(h, key, field)`
WITHIN = ((2, "port", "w"), (2, "cons", "m"))
BETWEEN = ((3, "disc", "a"), (2, "port", "k"))
# the status line of each drag on lesson 05's emptied trellis file (brief §5)
WITHIN_NOTE = (
    "trellis.port-cons.yml, periods[0].connectors[0]: {w: m} written, flat, periods 0–5"
)
BETWEEN_NOTE = "trellis.port-cons.yml, inter_connectors[0]: a: k written, entry, periods 0–5"
# the inter-period mapping of that trellis file, emptied and filled by the
# drag between periods
EMPTIED_MAPPING = "inter_connectors:\n  - {}\n"
FILLED_MAPPING = "inter_connectors:\n  - {a: k}\n"
# the sentences "An old graph" and "An edit not applied" of brief §5 at that
# file, and the line of its connector `- {}`
OLD_GRAPH = (
    "trellis.port-cons.yml: nothing was written. The graph was drawn from an earlier text. "
    "Drag again in the graph now drawn."
)
NOT_APPLIED = (
    "trellis.port-cons.yml, periods[0].connectors[0]: nothing was written. The text changed "
    "after the drag read it. Drag again."
)
CONNECTOR_LINE = 10
# another input of lesson 05's trellis, read from disk: the calibration file
CALIBRATION = "declaration/calibration/portfolio.yml"


def test_a_gesture_waits_for_the_editors_text_and_for_its_answer(app_state, tmp_path):
    """Brief rules 6 and 7, J-D6 (spec 0.4 §3.3): lesson 05's emptied
    trellis read, its trellis file open. The event of a drag within
    `periods[2]` asks the editor for its text and for nothing else. At the
    editor's change event the one replacement that types the line is asked
    of the editor, with the text read as the document the editor must hold;
    no buffer changes and no note stands before the editor answers. After a
    true answer the status line's note is the line of §5, and the gesture's
    file with its text before and after is recorded; the buffer takes the
    line at the editor's next change event, and the file on disk is
    unchanged."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"]
        typed = text.replace(EMPTIED_ENTRY, FILLED_ENTRY)
        flushes, before = app.flush_request.value, app.edit_request.value
        app.on_connected(connected_event(shown, app.tab_folder.value, *WITHIN))
        assert app.flush_request.value == flushes + 1
        assert app.edit_request.value is before
        editor = {"path": PORT_CONS, "text": text, "revision": held["document_revision"]}
        app.on_change(editor)
        request = app.edit_request.value
        edit = trellis.restoring_edit(typed, text)
        assert request == {"edits": [edit], "expected": text, "n": request["n"]}
        assert applied(text, [model.Replacement(**edit)]) == typed
        assert app.gesture_note.value is None and app.gesture_made.value is None
        assert app.buffers.value[PORT_CONS]["text"] == text
        answer = {"path": PORT_CONS, "revision": held["document_revision"], "n": request["n"]}
        app.on_applied({**answer, "applied": True})
        assert app.gesture_note.value["sentence"] == WITHIN_NOTE
        assert app.gesture_made.value == {"path": PORT_CONS, "before": text, "after": typed}
        assert app.gesturing.value is None and app.unsaved_texts() == {}
        app.on_change({**editor, "text": typed})
        path = str((copy / PORT_CONS).resolve())
        assert trellis.texts_of(app.unsaved_texts()) == {path: typed}
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == text
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_a_gesture_with_no_file_open_edits_the_buffer_at_once(app_state, tmp_path):
    """Brief rule 6, its first step skipped where no file is open (spec 0.4
    §3.3): lesson 05's emptied trellis read and no file open. The event of a
    drag within `periods[2]` asks the editor nothing: the trellis file is
    read from disk, compared with the text the edit was made from, and
    given a buffer that holds the line and the disk's digest, so that it is
    unsaved; the note of §5 stands, and the file on disk is unchanged."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        assert app.open_path.value is None
        text = (copy / PORT_CONS).read_text(encoding="utf-8")
        typed = text.replace(EMPTIED_ENTRY, FILLED_ENTRY)
        flushes, before = app.flush_request.value, app.edit_request.value
        app.on_connected(connected_event(shown, app.tab_folder.value, *WITHIN))
        assert app.flush_request.value == flushes and app.edit_request.value is before
        held = app.buffers.value[PORT_CONS]
        on_disk = model.read_file(app.tab_folder.value, PORT_CONS)
        assert (held["text"], held["digest"]) == (typed, on_disk.digest)
        path = str((copy / PORT_CONS).resolve())
        assert trellis.texts_of(app.unsaved_texts()) == {path: typed}
        assert app.gesture_note.value["sentence"] == WITHIN_NOTE
        assert app.gesture_made.value == {"path": PORT_CONS, "before": text, "after": typed}
        assert app.gesturing.value is None
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == text
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_a_closed_destination_is_edited_only_after_the_open_document_is_confirmed(
    app_state, tmp_path
):
    """J-D6 (spec 0.4 §3.3: a closed buffer receives the revision-checked
    edit in Python): lesson 05's emptied trellis read, and the consumption
    stage's file open, which the trellis reads. At the editor's change
    event the editor is asked an edit with no replacement and the open
    document as the text it must hold; nothing is written before its
    answer. After a true answer the trellis file's buffer holds the line
    and is unsaved, the note of §5 stands, and the file on disk is
    unchanged."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        app.open_file(SHARED_CONS)
        stage = app.buffers.value[SHARED_CONS]
        text = (copy / PORT_CONS).read_text(encoding="utf-8")
        typed = text.replace(EMPTIED_ENTRY, FILLED_ENTRY)
        app.on_connected(connected_event(shown, app.tab_folder.value, *WITHIN))
        app.on_change(
            {"path": SHARED_CONS, "text": stage["text"], "revision": stage["document_revision"]}
        )
        request = app.edit_request.value
        assert request == {"edits": [], "expected": stage["text"], "n": request["n"]}
        assert PORT_CONS not in app.buffers.value and app.gesture_note.value is None
        answer = {"path": SHARED_CONS, "revision": stage["document_revision"], "n": request["n"]}
        app.on_applied({**answer, "applied": True})
        path = str((copy / PORT_CONS).resolve())
        assert app.buffers.value[PORT_CONS]["text"] == typed
        assert trellis.texts_of(app.unsaved_texts()) == {path: typed}
        assert app.gesture_note.value["sentence"] == WITHIN_NOTE
        assert app.gesture_made.value == {"path": PORT_CONS, "before": text, "after": typed}
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == text
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_typing_seen_only_at_the_flush_prevents_the_insertion(app_state, tmp_path):
    """Spec 0.4 §3.3 (typing made during the pause before the ordinary
    change event): lesson 05's emptied trellis read, its trellis file open.
    The editor's text, read at the drag's flush request, holds another
    `repeat`, typed after the trellis was drawn: no edit is asked of the
    editor, nothing is written, and the list under the error mark holds the
    sentence "An old graph" of §5 at the trellis file."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        before = app.edit_request.value
        app.on_connected(connected_event(shown, app.tab_folder.value, *WITHIN))
        typed = held["text"].replace("repeat: 6", "repeat: 5")
        app.on_change({"path": PORT_CONS, "text": typed, "revision": held["document_revision"]})
        assert app.edit_request.value is before
        assert app.gesturing.value is None and app.gesture_note.value is None
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert (OLD_GRAPH, PORT_CONS, None) in listed
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_an_input_changed_while_the_query_runs_prevents_the_insertion(
    monkeypatch, app_state, tmp_path
):
    """Spec 0.4 §3.3 (if an input changes while the query is running, no
    insertion occurs, even when the destination text did not change):
    lesson 05's emptied trellis read, its trellis file open. The query, here
    replaced by one that answers the real query's edit and then gives the
    calibration file, another input of the trellis, an unsaved buffer with
    another discount factor, admits the line; the comparison under
    LOOP_LOCK then finds the inputs changed, so no edit is asked of the
    editor and the list holds the sentence "An old graph" of §5."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    query, answers = trellis.connector_edit, []

    def changing(held, event, texts):
        # the real query's answer, then another input's buffer changed
        answers.append(query(held, event, texts))
        found = model.read_file(app.tab_folder.value, CALIBRATION)
        assert "β: 0.96" in found.text
        changed = {
            "text": found.text.replace("β: 0.96", "β: 0.95"),
            "revision": 1,
            "digest": found.digest,
            "document": found.text,
            "document_revision": 0,
        }
        app.buffers.value = {**app.buffers.value, CALIBRATION: changed}
        return answers[-1]

    monkeypatch.setattr(trellis, "connector_edit", changing)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        before = app.edit_request.value
        app.on_connected(connected_event(shown, app.tab_folder.value, *WITHIN))
        editor = {"path": PORT_CONS, "text": held["text"], "revision": held["document_revision"]}
        app.on_change(editor)
        (answer,) = answers
        assert answer.edits and answer.sentence is None
        assert app.edit_request.value is before
        assert app.gesturing.value is None and app.gesture_note.value is None
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert (OLD_GRAPH, PORT_CONS, None) in listed
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_an_edit_the_editor_refuses_is_reported_as_not_written(app_state, tmp_path):
    """Brief rule 7 (the status line names the line written only on a true
    answer; otherwise the list holds the sentence that nothing was written):
    lesson 05's emptied trellis read, its trellis file open, and the line
    of a drag within `periods[2]` asked of the editor. The editor answers
    that the edit did not apply: no note stands, no gesture is recorded,
    the buffer is unchanged, and the list under the error mark holds the
    sentence "An edit not applied" of §5, linked to the line of the address
    it names, the connector's."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"]
        app.on_connected(connected_event(shown, app.tab_folder.value, *WITHIN))
        app.on_change({"path": PORT_CONS, "text": text, "revision": held["document_revision"]})
        request = app.edit_request.value
        assert len(request["edits"]) == 1
        answer = {"path": PORT_CONS, "revision": held["document_revision"], "n": request["n"]}
        app.on_applied({**answer, "applied": False})
        assert app.gesture_note.value is None and app.gesture_made.value is None
        assert app.gesturing.value is None
        assert app.buffers.value[PORT_CONS]["text"] == text
        assert text.split("\n")[CONNECTOR_LINE - 1] == "      - {}"
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert (NOT_APPLIED, PORT_CONS, CONNECTOR_LINE) in listed
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_j_a_second_gesture_withdraws_the_one_waiting(app_state, tmp_path):
    """Unit J's plan, review focus 5: lesson 05's emptied trellis read, its
    trellis file open. A drag within `periods[2]`, then, while it waits for
    the editor's text, a drag between `periods[3]` and `periods[2]`: each
    asks the editor for its text, the second withdraws the first, and at the
    editor's change event one edit is asked, the second's, which adds `a:
    k` to the inter-period mapping and leaves the connector empty. After a
    true answer the note is the second drag's."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"]
        folder, flushes = app.tab_folder.value, app.flush_request.value
        app.on_connected(connected_event(shown, folder, *WITHIN))
        app.on_connected(connected_event(shown, folder, *BETWEEN))
        assert app.flush_request.value == flushes + 2
        app.on_change({"path": PORT_CONS, "text": text, "revision": held["document_revision"]})
        request = app.edit_request.value
        typed = text.replace(EMPTIED_MAPPING, FILLED_MAPPING)
        assert request["edits"] == [trellis.restoring_edit(typed, text)]
        assert EMPTIED_ENTRY in typed
        answer = {"path": PORT_CONS, "revision": held["document_revision"], "n": request["n"]}
        app.on_applied({**answer, "applied": True})
        assert app.gesture_note.value["sentence"] == BETWEEN_NOTE
        assert app.gesture_made.value == {"path": PORT_CONS, "before": text, "after": typed}
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_a_change_of_source_graph_or_restriction_withdraws_a_gesture(app_state, tmp_path):
    """Brief rule 6 (a change of source, graph, restriction or elaboration
    number withdraws the gesture that waits): lesson 05's emptied trellis
    read, its trellis file open. A drag within `periods[2]` waits for the
    editor's text while the graph `backward` is shown, while a restriction
    is applied, while the trellis is read again from a changed buffer under
    another elaboration number, while the consumption stage's file is
    opened from the tree, and, with that file open, while the header's
    switch shows the stage's view by `stage`: each withdraws it, and the
    editor's change event then asks no edit and writes no note or sentence.
    The last two leave the forward trellis graph for the stage's forward
    graph, whose id is the same, `forward`. A drag that waits while another
    source is shown is withdrawn too, and the change of source clears the
    note, the sentence and the text of the last gesture."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"]
        event = connected_event(shown, app.tab_folder.value, *WITHIN)
        editor = {"path": PORT_CONS, "text": text, "revision": held["document_revision"]}

        def read_again():
            # the trellis file's buffer changed and read by the trellis's task
            buffer = app.buffers.value[PORT_CONS]
            changed = {**buffer, "text": text + "# a comment\n"}
            changed["revision"] = buffer["revision"] + 1
            app.buffers.value = {**app.buffers.value, PORT_CONS: changed}
            assert app.run_trellis().shown.number != shown.number

        def stage_from_the_tree():
            # the stage's view of the file opened from the tree, the forward
            # graph kept; the editor's change event completes the switch
            app.open_from_tree(SHARED_CONS)
            assert (app.view_mode.value, app.graph.value) == ("stage", "forward")

        def stage_from_the_header():
            # the stage's view of the open stage file by the switch's
            # `stage` (unit K, K-D20), the forward graph kept
            assert app.open_path.value == SHARED_CONS
            app.choose_stage()
            assert (app.view_mode.value, app.graph.value) == ("stage", "forward")

        def trellis_again():
            # the forward trellis graph shown again by the switch's `trellis`
            app.choose_trellis()
            assert (app.view_mode.value, app.graph.value) == ("trellis", "forward")

        for change, undo in (
            (lambda: app.switch_graph("backward"), lambda: app.switch_graph("forward")),
            (lambda: app.apply_restriction("periods 0–2"), lambda: app.apply_restriction("")),
            (read_again, lambda: None),
            (stage_from_the_tree, trellis_again),
            (stage_from_the_header, trellis_again),
        ):
            before = app.edit_request.value
            app.on_connected(event)
            assert app.gesturing.value is not None
            change()
            assert app.gesturing.value is None
            app.on_change(editor)
            assert app.edit_request.value is before
            assert app.gesture_note.value is None and app.gesture_refusal.value is None
            undo()
        app.on_connected(event)
        app.gesture_note.value = {"sentence": WITHIN_NOTE, "made": 0.0}
        refused = {"sentence": OLD_GRAPH, "file": PORT_CONS, "line": None, "made": 0.0}
        app.gesture_refusal.value = refused
        app.gesture_made.value = {"path": PORT_CONS, "before": text, "after": text}
        app.show_source(recipe.Source("trellis", "declaration/trellis.port-cons-vfi.yml"))
        assert app.gesturing.value is None
        assert app.gesture_note.value is None and app.gesture_refusal.value is None
        assert app.gesture_made.value is None
    finally:
        clear_gesture_state()
        clear_trellis_state()
        app.history.value, app.place_request.value = navigation.History(), None
        app.switching.value = None


# the two connectors the answers.yml of the gestures' copy requires: the
# trellis file's connector and its inter-period mapping, each emptied
REQUIRED = [(PORT_CONS, "periods[0].connectors[0]"), (PORT_CONS, "inter_connectors[0]")]


@pytest.mark.parametrize("opened", [PORT_CONS, SHARED_CONS, None])
def test_the_checklist_no_longer_counts_a_connector_a_gesture_typed(app_state, tmp_path, opened):
    """Spec 0.4 §3.3 and §8 J (1) (where answers.yml marks the connector
    required, the checklist's count falls by one): lesson 05's emptied
    trellis read, its answers.yml requiring the trellis file's connector and
    inter-period mapping, so that the checklist counts both. A drag within
    `periods[2]` types the connector into the trellis file's buffer, and the
    checklist, read from the buffers, then counts the mapping alone. With a
    file open the count is unchanged before the editor answers; with the
    trellis file open it falls at the editor's change event that brings the
    line, with a stage file open at the editor's true answer, and with no
    file open at once. The file on disk is unchanged."""
    copy, shown = gesture_trellis(app_state, tmp_path)
    try:
        with_required_connectors(copy, REQUIRED)
        app.refresh_folder()
        assert [(entry.file, entry.address) for entry in app.checklist.value] == REQUIRED
        text = (copy / PORT_CONS).read_text(encoding="utf-8")
        if opened is not None:
            app.open_file(opened)
            held = app.buffers.value[opened]
            editor = {"path": opened, "text": held["text"], "revision": held["document_revision"]}
        app.on_connected(connected_event(shown, app.tab_folder.value, *WITHIN))
        if opened is not None:
            app.on_change(editor)
            n = app.edit_request.value["n"]
            assert len(app.checklist.value) == 2
            app.on_applied(
                {"path": opened, "revision": editor["revision"], "n": n, "applied": True}
            )
        if opened == PORT_CONS:
            assert len(app.checklist.value) == 2
            app.on_change({**editor, "text": text.replace(EMPTIED_ENTRY, FILLED_ENTRY)})
        assert app.gesture_note.value["sentence"] == WITHIN_NOTE
        assert [(entry.file, entry.address) for entry in app.checklist.value] == REQUIRED[1:]
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == text
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_j_a_gesture_of_several_files_edits_the_open_document_last(repository, app_state):
    """J-D36 (spec 0.4 §3.3: of a refusal, nothing is written): with the
    recipe of a folder `new trellis` wrote open, "add stage" edits the
    recipe, the closed `period.yml` and answers.yml, and writes the
    template's files. At the editor's change event the editor is asked to
    confirm the open document, with no replacement, and nothing is written
    before its answer. On a true answer the closed files' buffers take their
    edits and the new files are written, and only then is the recipe's own
    edit asked of the editor. While that edit waits for the editor's
    answer, a second press of the button, and then a change of source, each
    take back what the gesture wrote: the two closed files hold no buffer,
    and the new files and the stage's folder are gone from disk; the
    editor's answer to the request of the gesture pressed first is taken by
    no gesture. An editor that refuses that last edit leaves nothing written
    in the same way, and the form holds the sentence that nothing was
    written. Pressed again and answered true twice, the form closes and the
    status line names what was written."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    recipe_file, period = RECIPE_FILE, "declaration/period.yml"
    app_state(created.folder)
    app.source.value = None
    try:
        app.open_file(recipe_file)
        held = app.buffers.value[recipe_file]
        text = held["text"]
        editor = {"path": recipe_file, "text": text, "revision": held["document_revision"]}
        answer = {"path": recipe_file, "revision": held["document_revision"]}
        before = file_bytes(created.folder)
        app.open_form("add stage")
        app.submit_add_stage(NOPORT_ID, "noport", creation.PERIOD)
        for case in ("pressed again", "source changed", "refused", "written"):
            app.on_change(editor)
            confirm = app.edit_request.value
            assert confirm == {"edits": [], "expected": text, "n": confirm["n"]}
            assert period not in app.buffers.value and file_bytes(created.folder) == before
            app.on_applied({**answer, "n": confirm["n"], "applied": True})
            own = app.edit_request.value
            assert own["n"] != confirm["n"] and own["expected"] == text
            new = applied(text, [model.Replacement(**edit) for edit in own["edits"]])
            row = creation.recipe_row("noport", ("stages/noport/methods.bl",))
            assert new == text + f"  noport: {row}\n"
            assert "  - noport\n" in app.buffers.value[period]["text"]
            assert sorted(set(file_bytes(created.folder)) - set(before)) == [
                "declaration/settings/noport.yml",
                "declaration/stages/noport/methods.bl",
                "declaration/stages/noport/noport.bl",
            ]
            assert app.gesture_note.value is None and app.form_open.value == "add stage"
            if case == "pressed again":
                # the button pressed again before the editor answers
                app.submit_add_stage(NOPORT_ID, "noport", creation.PERIOD)
                assert app.gesturing.value["step"] == "flushed"
            elif case == "source changed":
                # the recipe's trellis shown before the editor answers
                app.show_source(RECIPE)
                assert app.gesturing.value is None
            else:
                app.on_applied({**answer, "n": own["n"], "applied": case == "written"})
            if case == "written":
                break
            # nothing stands written
            assert not {period, creation.ANSWERS} & set(app.buffers.value)
            assert file_bytes(created.folder) == before
            assert not (created.folder / "declaration/stages/noport").exists()
            if case == "pressed again":
                # the editor's answer to the last request of the press replaced
                app.on_applied({**answer, "n": own["n"], "applied": False})
                assert app.gesturing.value["step"] == "flushed" and app.form_error.value == ""
            elif case == "source changed":
                clear_trellis_state()
                app.submit_add_stage(NOPORT_ID, "noport", creation.PERIOD)
            else:
                # the recipe's edit refused
                assert app.form_error.value == (
                    f"{recipe_file}: nothing was written. The text changed after the form read "
                    "it. Press the button again."
                )
                assert (app.form_open.value, app.gesturing.value) == ("add stage", None)
                app.submit_add_stage(NOPORT_ID, "noport", creation.PERIOD)
        # the last time: the recipe's edit applied, and the form closed
        assert (app.form_open.value, app.form_error.value, app.gesturing.value) == (None, "", None)
        assert app.gesture_note.value["sentence"] == (
            "period.yml, stages: noport written, periods 0–5; new: stages/noport/noport.bl, "
            "settings/noport.yml, stages/noport/methods.bl"
        )
        assert {period, creation.ANSWERS} <= set(app.buffers.value)
    finally:
        clear_gesture_state()
        clear_trellis_state()


# the status line of the removal of the join within `periods[2]` of lesson
# 05 (amendment 02, ruling 13)
REMOVED_NOTE = "trellis.port-cons.yml, periods[0].connectors[0]: {w: m} removed, periods 0–5"


def test_j_a_join_removed_from_details_goes_through_the_editor_and_opens_at_its_line(
    app_state, tmp_path
):
    """Unit J's decisions J-D33, J-D39 and J-D40 (amendment 02, rulings 11
    and 13, recommendation 16): lesson 05 read whole, its trellis file open.
    The region's event `join-chosen` of the join wire within `periods[2]`
    makes it the subject of Details, the box selected before no longer
    selected. The button `remove` begins a gesture of the kind `removed`,
    which asks the editor for its text and then for the one replacement
    that takes the connector's item out, `- {}` left; nothing is written
    before the editor answers. After a true answer the status line's note
    names the removal, and the trellis file, the destination, stands open
    with its line 15, `- {}`, selected. An event that ends the selection,
    and a change of graph, leave Details with no join; the file on disk is
    unchanged."""
    copy, shown = gesture_trellis(app_state, tmp_path, applications_copy)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"]
        removed = text.replace(FILLED_ENTRY, EMPTIED_ENTRY)
        folder = app.tab_folder.value
        (wire,) = [
            wire
            for wire in trellis.join_wires(shown)
            if (wire["from"], wire["to"]) == ("periods[2]/port", "periods[2]/cons")
        ]
        reading = trellis.reading_record(folder, shown)
        app.selected.value = {"nodeId": "periods[2]/cons___group___", "graphId": "forward"}
        app.on_join_chosen({"reading": reading, "join": wire})
        assert app.chosen_join.value == {"reading": reading, "join": wire}
        assert app.selected.value is None
        flushes, before = app.flush_request.value, app.edit_request.value
        app.remove_join()
        assert app.gesturing.value["kind"] == "removed"
        assert app.gesturing.value["event"] == {
            "reading": reading,
            "join": {name: wire[name] for name in app.JOIN_IDS},
        }
        assert app.flush_request.value == flushes + 1 and app.edit_request.value is before
        editor = {"path": PORT_CONS, "text": text, "revision": held["document_revision"]}
        app.on_change(editor)
        request = app.edit_request.value
        assert request == {
            "edits": [trellis.restoring_edit(removed, text)],
            "expected": text,
            "n": request["n"],
        }
        assert app.gesture_note.value is None and app.buffers.value[PORT_CONS]["text"] == text
        answer = {"path": PORT_CONS, "revision": held["document_revision"], "n": request["n"]}
        app.on_applied({**answer, "applied": True})
        assert app.gesture_note.value["sentence"] == REMOVED_NOTE
        assert app.gesture_made.value == {"path": PORT_CONS, "before": text, "after": removed}
        assert app.open_path.value == PORT_CONS
        goto = app.goto_request.value
        line = {
            "line": CONNECTOR_LINE,
            "column": 7,
            "end_line": CONNECTOR_LINE,
            "end_column": 11,
            "focus": False,
        }
        assert goto == {**line, "n": goto["n"]}
        app.on_join_chosen({"reading": reading, "join": None})
        assert app.chosen_join.value is None
        app.on_join_chosen({"reading": reading, "join": wire})
        app.switch_graph("backward")
        assert app.chosen_join.value is None
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == text
    finally:
        clear_gesture_state()
        clear_trellis_state()


# the sentences "An old graph" and "An edit not applied" of brief §5 for the
# removal of the join within `periods[2]` of lesson 05, which is no drag:
# the reader removes the join again (unit J's plan, Task 17)
OLD_GRAPH_REMOVAL = (
    "trellis.port-cons.yml: nothing was written. The graph was drawn from an earlier text. "
    "Remove the join again in the graph now drawn."
)
NOT_APPLIED_REMOVAL = (
    "trellis.port-cons.yml, periods[0].connectors[0]: nothing was written. The text changed "
    "after the removal read it. Remove the join again."
)
# the join wire within `periods[2]` of lesson 05, by its two stage
# occurrences
WITHIN_JOIN = ("periods[2]/port", "periods[2]/cons")


def test_j_a_removal_that_writes_nothing_asks_for_the_join_to_be_removed_again(
    app_state, tmp_path
):
    """Spec 0.4 §3.1, the Workbench's sentences give what to do (unit J's
    plan, Task 17): lesson 05 read whole, its trellis file open, and the
    join within `periods[2]` removed by `remove` (J-D33), which is no drag.
    Where the editor answers that the removal's edit did not apply, the
    list under the error mark holds "An edit not applied", linked to the
    connector's line, its last sentence asking for the join to be removed
    again; where the editor's text, read at the next removal's flush
    request, holds another `repeat`, the list holds "An old graph", asking
    for the join to be removed again in the graph now drawn. Nothing is
    written."""
    copy, shown = gesture_trellis(app_state, tmp_path, applications_copy)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        text = held["text"]
        remove_chosen_join(shown, *WITHIN_JOIN)
        app.on_change({"path": PORT_CONS, "text": text, "revision": held["document_revision"]})
        request = app.edit_request.value
        assert len(request["edits"]) == 1
        answer = {"path": PORT_CONS, "revision": held["document_revision"], "n": request["n"]}
        app.on_applied({**answer, "applied": False})
        assert app.gesture_note.value is None and app.gesturing.value is None
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert (NOT_APPLIED_REMOVAL, PORT_CONS, CONNECTOR_LINE) in listed

        before = app.edit_request.value
        remove_chosen_join(shown, *WITHIN_JOIN)
        typed = text.replace("repeat: 6", "repeat: 5")
        app.on_change({"path": PORT_CONS, "text": typed, "revision": held["document_revision"]})
        assert app.edit_request.value is before
        assert app.gesturing.value is None and app.gesture_note.value is None
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert (OLD_GRAPH_REMOVAL, PORT_CONS, None) in listed
        assert (copy / PORT_CONS).read_text(encoding="utf-8") == text
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_j_an_input_changed_while_a_removal_is_queried_asks_for_it_again(
    monkeypatch, app_state, tmp_path
):
    """Spec 0.4 §3.3 and §3.1 (unit J's plan, Task 17): lesson 05 read
    whole, its trellis file open, and the join within `periods[2]` removed
    by `remove`. The query, here replaced by one that answers the real
    query's edit and then gives the calibration file, another input of the
    trellis, an unsaved buffer with another discount factor, admits the
    removal; the comparison under LOOP_LOCK then finds the inputs changed,
    so no edit is asked of the editor and the list holds "An old graph",
    its last sentence asking for the join to be removed again."""
    copy, shown = gesture_trellis(app_state, tmp_path, applications_copy)
    query, answers = trellis.removal_edit, []

    def changing(held, event, texts):
        # the real query's answer, then another input's buffer changed
        answers.append(query(held, event, texts))
        found = model.read_file(app.tab_folder.value, CALIBRATION)
        assert "β: 0.96" in found.text
        changed = {
            "text": found.text.replace("β: 0.96", "β: 0.95"),
            "revision": 1,
            "digest": found.digest,
            "document": found.text,
            "document_revision": 0,
        }
        app.buffers.value = {**app.buffers.value, CALIBRATION: changed}
        return answers[-1]

    monkeypatch.setattr(trellis, "removal_edit", changing)
    try:
        app.open_file(PORT_CONS)
        held = app.buffers.value[PORT_CONS]
        before = app.edit_request.value
        remove_chosen_join(shown, *WITHIN_JOIN)
        editor = {"path": PORT_CONS, "text": held["text"], "revision": held["document_revision"]}
        app.on_change(editor)
        (answer,) = answers
        assert answer.edits and answer.sentence is None
        assert app.edit_request.value is before
        assert app.gesturing.value is None and app.gesture_note.value is None
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert (OLD_GRAPH_REMOVAL, PORT_CONS, None) in listed
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_r_one_tab_stands_per_buffer_in_the_order_opened():
    """Spec 0.4 §5.1; brief rule 4; R-D4, R-D32: `Tabs` renders one button
    `.bl-tab` for each buffer the tab holds, in the order the buffers were
    opened, whatever the order of their paths. Each tab carries its path as
    `data-path` and as its hover and reads the file's last name; the open
    file's tab is `.bl-active`, marked as the current one for a screen
    reader, and its name is `.bl-file-name`, carrying the path; a tab whose
    path is among the dirty paths reads `unsaved` after its name, the
    Codicon `circle-filled` that keeps the word in its text (design pass 8
    §3; unit M, Task 6); no tab holds a close control. A click on another tab
    asks the editor for its
    document before the switch (`open_file`)."""
    opened = (PORT_CONS, RECIPE_FILE, CONS)
    buffer = {"text": "", "revision": 1, "digest": None, "document": "", "document_revision": 1}
    app.buffers.value = {path: dict(buffer) for path in opened}
    app.open_path.value = RECIPE_FILE
    flushes = app.flush_request.value
    _, rendered = solara.render(app.Tabs({PORT_CONS, CONS}), handle_error=False)
    try:
        found = [
            widget
            for widget in rendered.find(v.Html, tag="button").widgets
            if "bl-tab" in widget.class_.split()
        ]
        assert [tab.attributes["data-path"] for tab in found] == list(opened)
        assert [tab.attributes["title"] for tab in found] == list(opened)
        assert ["bl-active" in tab.class_.split() for tab in found] == [False, True, False]
        assert [tab.attributes.get("aria-current") for tab in found] == [None, "true", None]
        texts = [[drawn_text(part) for part in tab.children] for tab in found]
        assert texts == [
            ["trellis.port-cons.yml", "unsaved"],
            ["spec.yml"],
            ["cons.bl", "unsaved"],
        ]
        name = rendered.find(v.Html, class_="bl-file-name").widget
        assert (name.children, name.attributes["data-path"]) == (["spec.yml"], RECIPE_FILE)
        marks = rendered.find(v.Html, class_="codicon codicon-circle-filled bl-modified").widgets
        assert marks == [found[0].children[1], found[2].children[1]]
        found[2].fire_event("click", {})
        assert (app.switching.value, app.flush_request.value) == (CONS, flushes + 1)
    finally:
        rendered.close()
        app.switching.value = None
        app.open_path.value = None
        app.buffers.value = {}


def test_r_the_status_line_prints_place_file_stage_state_and_digest(cons, cons_text):
    """The visible status line (spec 0.4 §5.7; unit R, brief rule 8, §5;
    R-D19, R-D20, R-D33, R-D39): for cons.bl constructed, with the cursor
    at line 8, column 12, `status_summary` answers the place, the file and
    the stage, `8:12 · cons.bl · stage cons`, then the square, the Codicon
    `pass-filled`, whose `data-state` is `constructed`, and `constructed
    <digest> · 0 refused · indent 4 · BellmanSym`, the digest the first
    seven characters of the digest of the text the state was computed from,
    each separator kept in the line's text and not drawn (design pass 8
    §6). The word `constructed` is focusable and carries `The language's
    check, not a verification of the economics.` as its title and its
    accessible description. A stage bound as an occurrence is named by the
    occurrence. Under a refusal of a later text, the state and the digest
    are those of the refused text, the count reads `1 refused`, the
    square's state is `not parsed` and its Codicon `circle-large-outline`,
    the stage named is the construction shown, and no sentence of the
    refusal stands in the line. No method is printed. A file opened as text
    prints its name and `indent 4`, and no state and no language; before
    the loop answers, nothing."""
    digest = hashlib.sha256(cons_text.encode("utf-8")).hexdigest()
    current = dataclasses.replace(shown_of(cons, cons_text, CONS), digest=digest)
    constructed = app.Outcome(
        path=CONS,
        revision=1,
        state="constructed",
        counts={},
        seconds=0.1,
        digests={"text": digest, "methods": "f" * 64},
        version="bound",
        refusals=[],
        stale=False,
        note=None,
    )

    def drawn(result, shown, place) -> tuple[str, str, dict]:
        # the text of each of the two groups of the line, and the square
        # and the state's term, each by its class
        _, rendered = solara.render(
            rv.Html(tag="div", children=app.status_summary(result, shown, place)),
            handle_error=False,
        )
        try:
            texts = [
                "".join(drawn_text(group) for group in rendered.find(v.Html, class_=name).widgets)
                for name in ("bl-status-where", "bl-status-loop")
            ]
            # the square is the Codicon of the state (design pass 8 §6)
            squares = [
                f"codicon codicon-{glyph} bl-status-square"
                for glyph in ("pass-filled", "circle-large-outline")
            ]
            parts = {
                name: [
                    widget
                    for classes in alternatives
                    for widget in rendered.find(v.Html, class_=classes).widgets
                ]
                for name, alternatives in (
                    ("square", squares),
                    ("state", ["bl-term bl-status-state"]),
                )
            }
            return texts[0], texts[1], parts
        finally:
            rendered.close()

    where, loop, parts = drawn(constructed, current, (8, 12))
    assert where == "8:12 · cons.bl · stage cons"
    assert loop == f"constructed {digest[:7]} · 0 refused · indent 4 · BellmanSym"
    assert [square.attributes["data-state"] for square in parts["square"]] == ["constructed"]
    # the Codicon `pass-filled`, drawn in mint (design pass 8 §6)
    assert "codicon-pass-filled" in parts["square"][0].class_.split()
    sentence = "The language's check, not a verification of the economics."
    assert app.TERMS["constructed"] == sentence
    (state,) = parts["state"]
    assert state.children == ["constructed"]
    described = ("title", "tabindex", "aria-description")
    assert {key: state.attributes.get(key) for key in described} == {
        "title": sentence,
        "tabindex": "0",
        "aria-description": sentence,
    }
    assert "!" not in where + loop

    bound = dataclasses.replace(current, occurrence="periods[0] / cons")
    assert drawn(constructed, bound, (8, 12))[0] == "8:12 · cons.bl · periods[0] / cons"

    refused_text = edited(cons_text, 18, "    a = m_d - - c")
    elaboration = model.elaborate_buffer(refused_text, CONS)
    (diagnostic,) = elaboration.diagnostics
    refused = app.Outcome(
        path=CONS,
        revision=2,
        state=model.loop_state(elaboration),
        counts={},
        seconds=0.1,
        digests={"text": elaboration.digest},
        version=None,
        refusals=[diagnostic],
        stale=True,
        note=None,
    )
    where, loop, parts = drawn(refused, current, (18, 17))
    assert where == "18:17 · cons.bl · stage cons"
    assert loop == f"not parsed {elaboration.digest[:7]} · 1 refused · indent 4 · BellmanSym"
    assert elaboration.digest[:7] != digest[:7]
    assert [square.attributes["data-state"] for square in parts["square"]] == ["not parsed"]
    assert "codicon-circle-large-outline" in parts["square"][0].class_.split()
    assert diagnostic.message not in where + loop

    text = dataclasses.replace(
        constructed, path=RECIPE_FILE, state=None, digests={}, version=None, note="a text file"
    )
    assert drawn(text, None, None)[:2] == ("spec.yml", "indent 4")
    assert drawn(None, current, (8, 12))[:2] == ("", "")


def test_r_a_tab_closes_its_saved_buffer_and_never_an_unsaved_one(app_state, scratch_consport):
    """R-D53; amendment 02 rulings 1 and 2. Three files of a copy of
    cons-port opened from the tree, the third open: each tab's close
    control, the icon button `close` (design pass 8 §3; unit M, Task 6), is
    named `Close` and the file's name, its hover `Close`; the control of an
    unsaved buffer is disabled, its hover `Save the file first.`, and a
    click on it closes nothing. The second tab, not open,
    closes at once, its buffer and its result leaving the tab's state. A
    step back shows the second file's place again, its text read from the
    disk, which changed while the file was closed. Closing the open file
    waits for the editor's document: text typed within the pause keeps the
    tab, which reads unsaved; with the text as saved, the tab closes and
    the tab to its left opens. The first tab closed while open opens the
    tab to its right, and the last tab closed leaves no file open."""
    app_state(scratch_consport)
    first, second, third = (
        "declaration/calibration/portfolio.yml",
        "declaration/stages/cons/methods.bl",
        "declaration/stages/cons/methods.vfi.bl",
    )

    def answer(path, text=None):
        # the editor's answer to a flush request, with the document it holds
        held = app.buffers.value[path]
        app.on_change(
            {
                "path": path,
                "text": held["text"] if text is None else text,
                "revision": held["document_revision"],
            }
        )

    try:
        app.open_from_tree(first)
        app.open_from_tree(second)
        answer(first)
        app.open_from_tree(third)
        answer(second)
        assert (list(app.buffers.value), app.open_path.value) == ([first, second, third], third)
        app.results.value = {
            path: {"outcome": None, "shown": None, "revision": 1, "rebind": None}
            for path in (first, second, third)
        }
        saved = app.buffers.value[first]
        app.buffers.value = {**app.buffers.value, first: {**saved, "text": saved["text"] + "#\n"}}
        _, rendered = solara.render(app.Tabs(app._dirty_paths()), handle_error=False)
        try:
            closes = [
                widget
                for widget in rendered.find(v.Html, tag="vscode-toolbar-button").widgets
                if "bl-tab-close" in widget.class_.split()
            ]
            assert [widget.attributes["icon"] for widget in closes] == ["close"] * 3
            assert [
                (
                    widget.attributes["label"],
                    widget.attributes["title"],
                    widget.attributes.get("aria-disabled"),
                )
                for widget in closes
            ] == [
                ("Close portfolio.yml", "Save the file first.", "true"),
                ("Close methods.bl", "Close", None),
                ("Close methods.vfi.bl", "Close", None),
            ]
            closes[0].fire_event("click", {})
            assert list(app.buffers.value) == [first, second, third]
            closes[1].fire_event("click", {})
        finally:
            rendered.close()
        assert (list(app.buffers.value), list(app.results.value)) == ([first, third], [first, third])
        assert app.open_path.value == third
        app.buffers.value = {**app.buffers.value, first: saved}

        # a step back reads the closed file from the disk
        (scratch_consport / second).write_text("changed: 1\n", encoding="utf-8")
        app.go_back()
        answer(third)
        assert app.open_path.value == second
        assert app.buffers.value[second]["text"] == "changed: 1\n"

        # the open file: typing within the pause keeps it, the saved text
        # closes it and opens the tab to its left
        flushes = app.flush_request.value
        app.close_file(second)
        assert (app.closing.value, app.flush_request.value) == (second, flushes + 1)
        answer(second, "changed: 2\n")
        assert (app.open_path.value, app.closing.value) == (second, None)
        assert app._dirty_paths() == {second}
        answer(second, "changed: 1\n")
        app.close_file(second)
        answer(second)
        assert (list(app.buffers.value), app.open_path.value) == ([first, third], third)

        # the first tab opens the tab to its right; the last leaves none open
        app.open_file(first)
        answer(third)
        app.close_file(first)
        answer(first)
        assert (list(app.buffers.value), app.open_path.value) == ([third], third)
        app.close_file(third)
        answer(third)
        assert (app.buffers.value, app.open_path.value) == ({}, None)
    finally:
        clear_trellis_state()
        app.history.value, app.place_request.value = navigation.History(), None
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.switching.value, app.closing.value, app.folder_read.value = None, None, False


def test_r_the_commands_of_goto_anything_follow_the_folder(app_state, scratch_folder, monkeypatch):
    """Spec 0.4 §5.8; unit R, brief rule 9: the commands of Goto Anything,
    `>`, each offered where its control is, in one order: `save` while a
    file is open; `hide types`, or `show types` while the types are hidden;
    `fold folder`; `fold Matsya`, absent with the setting off; `high
    contrast`; `notebook` while the tab has a source and the folder holds
    no notebook; `new trellis`; `new variant` where the folder holds the
    recipe `declaration/spec.yml`; and `add stage` and `add period` where
    `creation.can_add` holds, which each reading of the commands calls once,
    with its defaults, and which asks for the recipe and the trellis file it
    names and for no answers.yml (unit J, J-D7). Each command is a result of
    kind `command` whose address is empty. `run_command` runs a command
    offered as its control does, and a command not offered, `add stage`
    where `can_add` does not hold, does nothing."""
    app_state(scratch_folder)
    calls = []
    can_add = creation.can_add

    def counted(folder) -> bool:
        calls.append(folder)
        return can_add(folder)

    monkeypatch.setattr(creation, "can_add", counted)
    monkeypatch.setattr(app, "MATSYA_OFF", False)
    notebook = scratch_folder / creation.notebook_file(scratch_folder)
    assert not notebook.exists()

    def words() -> list[str]:
        before = len(calls)
        commands = app.goto_commands()
        assert len(calls) == before + 1
        for command in commands:
            assert command == {
                "prefix": ">",
                "kind": "command",
                "text": command["text"],
                "address": "",
                "command": command["text"],
            }
        return [command["text"] for command in commands]

    try:
        app.open_path.value, app.source.value, app.hide_types.value = None, None, False
        assert words() == [
            "hide types",
            "fold folder",
            "fold Matsya",
            "high contrast",
            "new trellis",
            "new variant",
            "add stage",
            "add period",
        ]
        app.open_path.value = CONS
        app.hide_types.value = True
        monkeypatch.setattr(app, "MATSYA_OFF", True)
        app.source.value = RECIPE
        assert words() == [
            "save",
            "show types",
            "fold folder",
            "high contrast",
            "notebook",
            "new trellis",
            "new variant",
            "add stage",
            "add period",
        ]

        # a command offered runs as its control does
        saves, contrasts = app.save_request.value, app.contrast_request.value
        app.run_command("save")
        app.run_command("show types")
        app.run_command("fold folder")
        app.run_command("high contrast")
        assert app.save_request.value == saves + 1
        assert app.hide_types.value is False
        assert app.fold_request.value["region"] == "folder"
        assert app.contrast_request.value == contrasts + 1
        for word in ("new trellis", "new variant", "add stage", "add period"):
            app.run_command(word)
            assert app.form_open.value == word
            app.close_form()
        app.run_command("notebook")
        assert notebook.is_file()
        assert "notebook" not in words()

        # a command not offered does nothing
        folds = app.fold_request.value
        app.run_command("fold Matsya")
        app.run_command("show types")
        assert (app.fold_request.value, app.hide_types.value) == (folds, False)
        monkeypatch.setattr(creation, "can_add", lambda folder: False)
        app.run_command("add stage")
        assert app.form_open.value is None
    finally:
        app.close_form()
        app.hide_types.value, app.source.value = False, None
        app.fold_request.value = None


def test_r_each_term_carries_one_sentence_on_hover():
    """The interface-text review of unit R (the project's lean-implementation
    rule,
    last section; Task 16): a hover carries at most one short sentence, so
    the definition each term carries on hover holds one sentence, with no
    second clause after a semicolon and no second sentence. The definitions
    of `kind` and `period`, which each held a second clause after a
    semicolon, now read as one clause."""
    assert app.TERMS["kind"] == (
        "the kind of the box's operator, or block or field in an initial diagram"
    )
    assert app.TERMS["period"] == (
        "one date of the model, numbered from the terminal period, periods[0]"
    )
    assert [
        word
        for word, definition in app.TERMS.items()
        if ";" in definition or ". " in definition.rstrip(".")
    ] == []


# --- unit K, Task 13: what the page says while a text is refused, and the
# one list of what the model lacks ---

# An edit of cons.bl that the construction refuses, the name `q` standing in
# no scope, and the line of cons.bl that declares the parameter ρ, which the
# calibration file of the portfolio model values.
REFUSED_EDIT = ("    m_d = m\n", "    m_d = q\n")
RHO_LINE = 6
# the period file of the portfolio model, relative to its folder
PERIOD_FILE = "declaration/period.yml"


def _rewrite(path, old: str, new: str) -> None:
    """Writes the file `path` with its one occurrence of `old` replaced by
    `new`."""
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (path, old)
    path.write_text(text.replace(old, new), encoding="utf-8")


def _within(widget) -> list:
    """The widget `widget` and every widget among its children, at every
    depth, in the order drawn."""
    found = [widget]
    for child in getattr(widget, "children", None) or []:
        if not isinstance(child, str):
            found += _within(child)
    return found


def _details(result, current) -> tuple:
    """Details as `app.Panel` draws it for the loop's outcome `result` and
    the stage shown `current`, with the legend of `current`'s backward
    graph: the classes of the children of its body; every class of an
    element within it; the files named by each element of the body that
    carries a file and a line; and the texts of the legend's title."""
    collection = current.collection if current is not None else None
    legend = app.Legend(collection, "backward", None)
    _, rendered = solara.render(app.Panel(result, current, legend), handle_error=False)
    try:
        body = rendered.find(v.Html, class_="bl-panel-body").widget
        classes = [child.class_ for child in body.children]
        drawn = _within(body)
        within = {name for widget in drawn for name in (widget.class_ or "").split()}
        files = {
            widget.attributes["data-path"]
            for widget in drawn
            if {"data-path", "data-line"} <= set(getattr(widget, "attributes", None) or {})
        }
        names = [
            drawn_text(w)
            # the legend's name line holds the name in Code small and the
            # version's states after it (the fix wave Q3b of unit Q, item 19)
            for w in rendered.find(v.Html, class_="bl-legend-name").widgets
        ]
        return classes, within, files, names
    finally:
        rendered.close()


def test_k_details_of_a_refused_text_describe_its_file_s_last_construction_alone(
    app_state, scratch_folder
):
    """Unit K, Task 13 (usability walkthrough §4 item 11; spec 0.4 §5.7):
    on a copy of the portfolio model, with cons.bl constructed and the
    cursor on ρ at line 6, Details prints the name under the cursor with the
    line of the calibration file that values it, and the legend names cons.
    After an edit the construction refuses, Details holds the refusal's row
    and describes the last construction of cons.bl, the legend naming cons,
    and prints nothing the cursor reads, no line of another file among
    them; the cursor then enters no block and selects no box. With no
    construction of the refused file, the stage shown of another file or
    none, Details holds the refusal's row alone."""
    app_state(scratch_folder)
    app.source.value = RECIPE
    try:
        app.open_file(CONS)
        app.run_loop()
        drawn = app.shown.value
        held = app.buffers.value[CONS]
        cursor = {
            "path": CONS,
            "revision": held["document_revision"],
            "line": RHO_LINE,
            "column": 1,
        }
        app.on_cursor(cursor)
        _, within, files, names = _details(app._result_of(CONS), drawn)
        assert {"bl-name-calibration", "bl-cursor-details"} <= within
        assert files == {"declaration/calibration/portfolio.yml"}
        assert names[0].split()[0] == "cons"
        assert held["text"].count(REFUSED_EDIT[0]) == 1
        refused_text = held["text"].replace(*REFUSED_EDIT)
        app.on_change({"path": CONS, "text": refused_text, "revision": held["document_revision"]})
        app.run_loop()
        result = app._result_of(CONS)
        assert result.stale and app.shown.value is drawn
        app.on_cursor(cursor)
        assert app.cursor_block.value is None and app.block_nodes.value == []
        classes, within, files, names = _details(result, drawn)
        assert classes[0] == "bl-refusal bl-code-small" and classes[-1] == "bl-legend-details"
        assert not {"bl-name", "bl-name-calibration", "bl-cursor-details"} & within
        assert files == set() and names[0].split()[0] == "cons"
        port_text = (scratch_folder / PORT).read_text(encoding="utf-8")
        port = elaborate_text(port_text, PORT)
        other = dataclasses.replace(
            shown_of(port, port_text, PORT), collection=model.collection(port)
        )
        for current in (other, None):
            classes, _, files, names = _details(result, current)
            assert (classes, files, names) == (["bl-refusal bl-code-small"], set(), [])
    finally:
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False
        app.cursor_line.value = app.cursor_place.value = None


def test_k_the_list_under_the_error_mark_holds_the_notes_of_the_last_reading_alone(
    app_state, scratch_folder
):
    """Unit K, Task 13 (usability walkthrough §4 item 15): on a copy of the
    portfolio model whose cons addition names the stage port, the notes of
    cons.bl's binding stand in the list under the error mark. The trellis's
    reading, which constructs the same stage with its addition, is refused
    under the package's rule `metadata-mismatch`, since an addition's first
    line names the stage it adds to; the refusal stands while that reading is
    the last and leaves the list once a later reading is refused, the later
    refusal standing in its place (unit L, Task 21). Once the addition is
    written back on disk, before any reading binds cons.bl again, the list
    holds none of the stage's notes. Each sentence is compared as the list
    prints it, its paths relative to the folder (K-D11), since the package's
    refusal names the files by their absolute paths."""
    methods = scratch_folder / "declaration/stages/cons/methods.bl"
    written = methods.read_text(encoding="utf-8")
    _rewrite(methods, "@methods: cons\n", "@methods: port\n")
    app_state(scratch_folder)
    app.source.value = RECIPE

    def listed() -> list[str]:
        # the sentences of the list under the error mark
        return [each.sentence for each in app.standing_refusals()]

    try:
        app.open_file(CONS)
        app.run_loop()
        notes = [app.folder_relative(note) for note in app.shown.value.notes]
        assert any("'port'" in note for note in notes)
        assert set(notes) <= set(listed())
        outcome = app.run_trellis()
        assert outcome.shown is None and outcome.refusal.rule == "metadata-mismatch"
        refused = app.folder_relative(outcome.refusal.message)
        assert refused in listed()
        sentence = "declaration/spec.yml does not read: a refusal of a later reading"
        refusal = model.Diagnostic(None, None, None, None, None, sentence, None, None, None)
        app.trellis_outcome.value = trellis.TrellisOutcome(
            None, refusal, None, 0.0, {}, made=time.monotonic()
        )
        assert sentence in listed() and refused not in listed()
        methods.write_text(written, encoding="utf-8")
        assert not set(notes) & set(listed())
    finally:
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_k_a_save_clears_the_note_of_the_last_gesture(app_state, scratch_folder):
    """Unit K, Task 13 (usability walkthrough §4 item 15; J-D20 amended):
    the status line's note of the last gesture of the trellis graph stands
    while the file is edited and while a save meets a file changed on disk,
    which writes nothing, and leaves once a save writes the file."""
    app_state(scratch_folder)
    note = "period.yml, connectors[0]: {m_next: m} written, flat, periods 0–5"
    try:
        app.open_file(PERIOD_FILE)
        held = app.buffers.value[PERIOD_FILE]
        app.gesture_note.value = {"sentence": note, "made": time.monotonic()}
        text = held["text"] + "# a comment typed after the drag\n"
        event = {"path": PERIOD_FILE, "text": text, "revision": held["document_revision"]}
        app.on_change(event)
        assert app.gesture_note.value["sentence"] == note
        on_disk = scratch_folder / PERIOD_FILE
        on_disk.write_text(held["text"] + "# written by another program\n", encoding="utf-8")
        app.on_save(event)
        assert app.conflict.value is not None and app.gesture_note.value["sentence"] == note
        app.choose_overwrite()
        app.on_save(event)
        assert app.conflict.value is None and app.gesture_note.value is None
        assert on_disk.read_text(encoding="utf-8") == text
    finally:
        clear_gesture_state()
        app.conflict.value = None
        app.overwrite_pending.value = False


def test_k_problems_keep_unjoined_fields_and_entries_to_check_and_no_slot(app_state, tmp_path):
    from workbench_support import composition_folder

    path = composition_folder(tmp_path / "open-model", repeat=2)
    (path / creation.ANSWERS).write_text("required:\n  connectors:\n    - {file: period.yml, address: 'connectors[0]'}\n")
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    try:
        outcome = app.run_trellis()
        items = app.lacking_items(app.checklist.value, outcome, outcome.shown, app.tab_folder.value)
        assert any(item.kind == "unjoined" for item in items)
        assert [(item.file, item.line) for item in items if item.kind == "check"] == [("period.yml", 5)]
        app.errors_open.value = False
        _, rendered = solara.render(app.ErrorMark(), handle_error=False)
        try:
            assert rendered.find(v.Html, class_="bl-problem-group bl-problem-check").widget.attributes["data-count"] == "1"
            button = rendered.find(v.Html, tag="button", class_="bl-error-mark").widget
            assert button.attributes["aria-expanded"] == "false"
            button.fire_event("click", {})
            assert rendered.find(v.Html, tag="button", class_="bl-error-mark bl-active").widget.attributes["aria-expanded"] == "true"
        finally:
            rendered.close()
    finally:
        clear_trellis_state()
        app.errors_open.value = False


def test_k_a_problem_source_follows_an_unsaved_edit(app_state, tmp_path):
    from workbench_support import composition_folder

    path = composition_folder(tmp_path / "unsaved-model", repeat=2)
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    try:
        outcome = app.run_trellis()
        app.errors_open.value = True
        _, rendered = solara.render(app.ErrorMark(), handle_error=False)
        try:
            def lines():
                return {item.attributes["data-line"] for item in rendered.find(
                    v.Html, class_="bl-row bl-checklist-unjoined").widgets}
            assert lines() == {"5"}
            app.open_file("period.yml")
            held = app.buffers.value["period.yml"]
            app.on_change({"path": "period.yml", "text": "# source comment\n"+held["text"],
                           "revision": held["document_revision"]})
            assert app.trellis_outcome.value is outcome
            assert lines() == {"6"}
        finally:
            rendered.close()
    finally:
        clear_trellis_state()
        app.errors_open.value = False


def test_k_the_slots_line_reads_each_slot_once_with_the_lists_it_stands_in(tmp_path):
    """Unit K, Task 26 (K-D29; design pass 2 §11): `recipe.slots` reads
    from the rows `recipe.table` answers for a folder of the forms, whose
    recipe also writes `$cons_calibration` and `$late` in a period-range
    list of cons, each slot once, in the order the recipe first writes it,
    with every list that writes it, a range list named by its range; the
    keywords are those `load_recipe` takes, and a trellis file's rows hold
    no slot."""
    folder = written_from_the_forms(tmp_path / "demo")
    path = folder / RECIPE_FILE
    _rewrite(
        path,
        "calibration: {all: [$cons_calibration]}",
        'calibration: {all: [$cons_calibration], "0-2": [$cons_calibration, $late]}',
    )
    opened = model.open_folder(folder)
    rows = recipe.table(opened, RECIPE, recipe.read_source(opened, RECIPE), 0)
    found = recipe.slots(rows)
    # the calibration and the settings of each row are slots, a methods list
    # naming additions and no slot (decision S7-F3)
    assert [slot.keyword for slot in found] == [
        "port_calibration",
        "port_settings",
        "cons_calibration",
        "late",
        "cons_settings",
        "disc_calibration",
        "disc_settings",
    ]
    assert found[2] == recipe.Slot(
        "cons_calibration", ("cons · calibration", "cons · calibration · 0-2")
    )
    assert found[3] == recipe.Slot("late", ("cons · calibration · 0-2",))
    keywords = {slot.keyword: {} for slot in found}
    assert load_recipe(folder / "declaration", "spec.yml", **keywords)["periods"]
    source = recipe.Source("recipe", PORT_CONS_RECIPE)
    cons_port = model.open_folder(ROOT / "applications/cons-port")
    syntactic = recipe.read_source(cons_port, source)
    assert recipe.slots(recipe.table(cons_port, source, syntactic, 0)) == []


# --- unit K, Task 14: the texts the page composes ---

# The period file's line that lists the discount stage, which the recipe
# still names once it is removed; and the package's refusal of the trellis
# that follows, with each path printed from the folder (K-D11): the trellis
# file's absolute path stands twice in the package's sentence.
DISC_LISTED = "  - disc\n"
NO_PERIOD_HOLDS_DISC = (
    "the recipe names the stage 'disc', which no period of declaration/trellis.yml holds\n"
    "'disc' in a period template of declaration/trellis.yml, or no entry for it in the recipe"
)
# the line of cons.bl whose first name, at column 5 after the indentation,
# is the decision state m_d
M_D_PLACE = (14, 5)


def test_k_a_sentence_prints_each_absolute_path_from_the_folder_and_nothing_else(model_folder):
    """Unit K, Task 14 (usability walkthrough §4 item 6; K-D11): a sentence
    the page prints keeps every character but its absolute paths, each
    printed relative to the model folder: a file of the folder from the
    folder, the line after a file's name kept; the folder itself by its
    name, with a full stop or a colon after it kept; a file outside it by
    `..` steps. A slash after a character, as in `1/ρ`, a link's address
    and a path whose folder this machine does not hold are left as
    written."""
    folder = model.open_folder(model_folder)
    root = folder.root
    cases = {
        f"stage 'disc', parameter 'β' (address '{root}/declaration/stages/disc/disc.bl:7'): the"
        " calibration source supplies no value for it": (
            "stage 'disc', parameter 'β' (address 'declaration/stages/disc/disc.bl:7'): the"
            " calibration source supplies no value for it"
        ),
        f"which no period of {root}/declaration/trellis.yml holds": (
            "which no period of declaration/trellis.yml holds"
        ),
        f"the folder {root} holds no recipe": f"the folder {root.name} holds no recipe",
        # a full stop or a colon after the folder's path ends the sentence or
        # the clause
        f"no recipe stands in {root}.": f"no recipe stands in {root.name}.",
        f"in {root}: no recipe": f"in {root.name}: no recipe",
        f"read {root.parent}/notes.md first.": "read ../notes.md first.",
        "𝑑𝑢𝑖𝑛𝑣(x) := x^(-1/ρ) and c^(1-ρ)/(1-ρ)": "𝑑𝑢𝑖𝑛𝑣(x) := x^(-1/ρ) and c^(1-ρ)/(1-ρ)",
        "served at http://localhost:8765/static/assets": (
            "served at http://localhost:8765/static/assets"
        ),
        "no file /no/such/folder/spec.yml": "no file /no/such/folder/spec.yml",
    }
    assert {sentence: trellis.relative_sentence(folder, sentence) for sentence in cases} == cases


def test_k_the_list_under_the_error_mark_prints_the_package_s_sentence_with_paths_from_the_folder(
    app_state, scratch_folder
):
    """Unit K, Task 14 (usability walkthrough §4 item 6; K-D11; the texts'
    rule that a refusal is the package's sentence): on a copy of the
    portfolio model whose period file no longer lists disc, the package
    refuses the trellis's reading in a sentence that writes the trellis
    file's absolute path twice. The trellis's refusal and the one note of
    cons.bl bound through the recipe give it alike, and the list under the
    error mark holds it once (unit L, Task 21; defect 17 of the UX
    simulation), each path printed from the folder and every other
    character the package's, and no line of the list holds the folder's
    absolute path; the record of the refusal's underline in the editor,
    whose message is its hover, prints the same sentence."""
    _rewrite(scratch_folder / PERIOD_FILE, DISC_LISTED, "")
    app_state(scratch_folder)
    app.source.value = RECIPE
    root = str(app.tab_folder.value.root)
    try:
        outcome = app.run_trellis()
        message = model.sentence(outcome.refusal)
        assert message.count(f"{root}/") == 2
        assert message.replace(f"{root}/", "") == NO_PERIOD_HOLDS_DISC
        app.open_file(CONS)
        app.run_loop()
        assert app.shown.value.notes == [message]
        listed = [each.sentence for each in app.standing_refusals()]
        # the policy header of cons.bl lists `V[>]` alone, which its line reads, so the
        # recipe's sentence stands alone (the header lost the marginal field `dV[>]`
        # that no line read, AMD-MB-001)
        assert listed == [NO_PERIOD_HOLDS_DISC]
        hover = app.editor_record(outcome.refusal)["message"]
        assert hover == NO_PERIOD_HOLDS_DISC
        assert not [sentence for sentence in [*listed, hover] if root in sentence]
    finally:
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_k_the_name_under_the_cursor_stands_as_written_above_the_block_s_record(
    app_state, scratch_folder
):
    """Unit K, Task 14 (usability walkthrough §4 item 19 and §5, "Find where
    a field is used"): with the cursor on m_d at line 14 of cons.bl,
    Details prints the label `name m_d`, the name as the file writes it,
    with its occurrences and the boxes that depend on it, above the fold
    `cursor`, which holds the block's record."""
    app_state(scratch_folder)
    app.source.value = RECIPE
    try:
        app.open_file(CONS)
        app.run_loop()
        drawn = app.shown.value
        held = app.buffers.value[CONS]
        line, column = M_D_PLACE
        revision = held["document_revision"]
        app.on_cursor({"path": CONS, "revision": revision, "line": line, "column": column})
        legend = app.Legend(drawn.collection, "backward", None)
        _, rendered = solara.render(
            app.Panel(app._result_of(CONS), drawn, legend), handle_error=False
        )
        try:
            name = rendered.find(v.Html, class_="bl-block-label bl-name").widget
            assert [getattr(part, "children", part) for part in name.children] == [
                ["name"],
                " m_d",
            ]
            body = rendered.find(v.Html, class_="bl-panel-body").widget
            holding = [
                {cls for widget in _within(child) for cls in (widget.class_ or "").split()}
                for child in body.children
            ]
            named = next(index for index, found in enumerate(holding) if "bl-name" in found)
            folded = next(
                index for index, found in enumerate(holding) if "bl-cursor-details" in found
            )
            assert named < folded and "bl-block-record" in holding[folded]
        finally:
            rendered.close()
    finally:
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False
        app.cursor_line.value = app.cursor_place.value = None


# --- unit L, Task 5: the note and the selection after `+` ---


def test_l_the_note_and_the_selection_after_add_follow_the_declaration(cons, cons_text):
    """Unit L, Task 5 (Task 1's review, Minor 1; AAS, L-D1; amendment 02
    ruling 9): `q`, `ℝ₊`, `state` added in the decision group asks the editor
    for the declaration `q : ℝ₊` on the outputs of arvl_to_dcsn and the name
    `q` alone on the inputs of dcsn_to_cntn. The group's note names the
    declaration with its set and its line and, in one clause, the block that
    lists the name, and the editor selects the declaration's whole line,
    the focus given to it. The same holds on a copy of cons.bl whose two
    forward blocks stand in the reverse order, where the listing comes
    first in the text: only the line numbers differ. A control added in the
    decision group, declared on the side that takes the listing, is noted
    with no listing."""
    lines = cons_text.split("\n")
    # the three lines of arvl_to_dcsn (13 to 15) and of dcsn_to_cntn (17 to
    # 19), written in the reverse order
    swapped = "\n".join(lines[:12] + lines[16:19] + lines[15:16] + lines[12:15] + lines[19:])
    assert swapped.split("\n")[12].startswith("[id=dcsn_to_cntn,")
    assert swapped.split("\n")[16].startswith("[id=arvl_to_dcsn,")
    add = {"kind": "add", "group": "dcsn/", "perch": "dcsn", "branch": None, "field": "q"}
    state = {**add, "set": "ℝ₊", "role": "state"}

    def asked(stage, text: str, change: dict) -> tuple:
        # the edits, the note and the editor's move one change asks for
        held = {
            "text": text,
            "revision": 1,
            "digest": "",
            "document": text,
            "document_revision": 1,
        }
        app.buffers.value = {CONS: held}
        app.shown.value = shown_of(stage, text, CONS)
        app.on_table_change(change)
        edits = [(edit["line"], edit["text"]) for edit in app.edit_request.value["edits"]]
        goto = {key: value for key, value in app.goto_request.value.items() if key != "n"}
        return edits, app.table_note.value["sentence"], goto

    try:
        app.open_path.value = CONS
        assert asked(cons, cons_text, state) == (
            [(13, ", q : ℝ₊"), (17, ", q")],
            "q : ℝ₊ written to line 13 and listed on dcsn_to_cntn",
            {"line": 13, "column": 1, "end_line": 13, "end_column": None, "focus": True},
        )
        reversed_stage = elaborate_text(swapped, CONS)
        assert asked(reversed_stage, swapped, state) == (
            [(13, ", q"), (17, ", q : ℝ₊")],
            "q : ℝ₊ written to line 17 and listed on dcsn_to_cntn",
            {"line": 17, "column": 1, "end_line": 17, "end_column": None, "focus": True},
        )
        control = {**add, "field": "k", "set": "ℝ₊", "role": "!ctrl"}
        assert asked(reversed_stage, swapped, control) == (
            [(13, ", k : ℝ₊ @ !ctrl")],
            "k : ℝ₊ @ !ctrl written to line 13",
            {"line": 13, "column": 1, "end_line": 13, "end_column": None, "focus": True},
        )
    finally:
        app.shown.value = None
        app.buffers.value = {}
        app.open_path.value = None
        app.edit_request.value = None
        app.table_note.value = None
        app.goto_request.value = None


# The Codicon of each control of the graph column and Matsya's column that
# Python draws (design pass 8 §3; unit M, Task 7), by the control's name in
# `icons.CODICONS`.
TASK_7_CODICONS = {
    "perch overlays": "layers",
    "fold matsya": "close",
    "ask matsya": "send",
}


def test_m_7_lucide_leaves_and_the_graph_column_and_matsya_draw_codicons():
    """Unit M, Task 7 (design pass 8 §§3 and 8, item 2): Lucide's glyphs,
    their drawing and their CSS image leave `icons` with their last reader,
    and the page's stylesheet holds no image of a glyph; `icons.CODICONS`
    names the Codicon of the foot's `Perch overlays`, of Matsya's fold and
    of the question sent to Matsya, each drawn by `icons.codicon` as the
    element Codicons' stylesheet draws."""
    assert not any(hasattr(icons, name) for name in ("GLYPHS", "icon", "mask", "STROKE"))
    assert "--bl-icon-" not in app.BRAND_CSS and not hasattr(app, "PANEL_ICONS")
    assert {name: icons.CODICONS[name] for name in TASK_7_CODICONS} == TASK_7_CODICONS
    for name in TASK_7_CODICONS.values():
        drawn = icons.codicon(name)
        assert drawn.kwargs["tag"] == "i"
        assert drawn.kwargs["class_"] == f"codicon codicon-{name}"
        assert drawn.kwargs["attributes"] == {"aria-hidden": "true"}


# The icon of each toggle of the main bar by its fold (design pass 10 §3;
# N-D10, keeping AAS's M-D18): its Codicon and the glyph the browser
# typesets, None where it has none.
TOGGLE_ICONS = {
    "folder": ("files", None),
    "inspector": ("layout-panel", None),
    "details": (None, "⟦·⟧"),
    "matsya": ("comment", "Υ"),
}


def test_n_1_the_main_bar_draws_the_mark_the_history_the_path_and_the_four_toggles(
    app_state, scratch_folder
):
    """Unit N, Task 1 (design pass 10 §§2 and 3; N-D4, N-D10): the rail of
    icons, its buttons and its glyphs leave the page with their names, and
    the main bar takes their toggles. `icons.toggle_icon` draws each
    toggle's icon, a span `.bl-toggle-icon` hidden from assistive
    technology holding the Codicon `icons.TOGGLE_ICONS` names and its
    glyph, a span `.bl-toggle-glyph` whose data-glyph is the glyph.
    `MainBar` draws one `nav.bl-main-bar` of three groups: at the left the
    brand's mark, the silhouette, a link to the page of the Workbench in the
    documentation, and Back and Forward, both drawn and disabled while no
    place stands behind or ahead; in the middle the path, in Label, its
    parts parted by the Codicon `chevron-right` (design pass 13 §3; C4), its
    hover the whole path; one toggle per panel, `.bl-fold` with data-fold
    `folder`, `inspector`, `details`, `matsya`, its accessible name and
    hover the panel's name, which is also the name its panel's head prints,
    at the end of the bar on which its panel opens: the Files column's and
    the Inspector's after `Forward` at the left, `Go to` and then Details'
    and Matsya's at the right (design pass 14 §10; S-D16)."""
    retired = ("Rail", "RailButton", "RAIL", "Breadcrumb", "OccurrenceLine")
    assert not any(hasattr(app, name) for name in retired)
    assert not any(hasattr(icons, name) for name in ("RAIL_ICONS", "rail_icon"))
    assert not {"hide types", "show types"} & set(icons.CODICONS)
    # the path's parts are parted by the Codicon `chevron-right` since design
    # pass 13 §3 (C4), where unit N had drawn no glyph between them
    assert icons.CODICONS["path separator"] == "chevron-right"
    assert icons.TOGGLE_ICONS == TOGGLE_ICONS
    assert app.PANEL_NAMES == {
        "folder": "Files",
        "inspector": "Inspector",
        "details": "Details",
        "matsya": "Matsya",
    }
    assert app.PANEL_FOLDS == {"recipe": "inspector", "types": "inspector", "details": "details"}
    for fold, (name, glyph) in icons.TOGGLE_ICONS.items():
        drawn = icons.toggle_icon(fold)
        assert (drawn.kwargs["tag"], drawn.kwargs["class_"]) == ("span", "bl-toggle-icon")
        assert drawn.kwargs["attributes"] == {"aria-hidden": "true"}
        parts = [
            (child.kwargs["tag"], child.kwargs["class_"], child.kwargs["attributes"])
            for child in drawn.kwargs["children"]
        ]
        assert parts == [
            *([("i", f"codicon codicon-{name}", {"aria-hidden": "true"})] if name else []),
            *([("span", "bl-toggle-glyph", {"data-glyph": glyph})] if glyph else []),
        ], fold
    app_state(scratch_folder)
    _, rendered = solara.render(app.MainBar(None), handle_error=False)
    try:
        (bar,) = rendered.find(v.Html, tag="nav", class_="bl-main-bar").widgets
        assert [child.class_ for child in bar.children] == [
            "bl-main-start",
            "bl-main-path",
            "bl-main-end",
        ]
        (mark,) = rendered.find(v.Html, class_="bl-mark").widgets
        assert mark.attributes["href"] == app.WORKBENCH_PAGE
        assert mark.children[0].attributes["src"].endswith("/static/assets/brand/favicon.svg")
        for control in ("back", "forward"):
            (button,) = rendered.find(v.Html, class_=f"bl-{control}").widgets
            assert button.attributes["title"] == control.capitalize()
            assert button.attributes["aria-disabled"] == "true"
        # the path in Label, the page's own face (design pass 13 §3; C4)
        (path,) = rendered.find(v.Html, class_="bl-crumbs").widgets
        assert path.attributes["title"] == drawn_text(path)
        buttons = rendered.find(v.Html, class_="bl-fold bl-toggle").widgets
        assert [button.attributes["data-fold"] for button in buttons] == list(TOGGLE_ICONS)
        # the toggles at the end of the bar on which their panels open (design pass 14 §10)
        assert (app.LEFT_PANELS, app.RIGHT_PANELS) == (("folder", "inspector"), ("details", "matsya"))
        start, _, end = bar.children
        assert [child.attributes.get("data-fold") for child in start.children if "bl-fold" in (child.class_ or "")] == ["folder", "inspector"]
        assert [child.attributes.get("data-fold") for child in end.children if "bl-fold" in (child.class_ or "")] == ["details", "matsya"]
        assert end.children[0].class_ == "bl-goto-button"
        for button in buttons:
            name = app.PANEL_NAMES[button.attributes["data-fold"]]
            assert button.attributes["aria-label"] == name
            if button.attributes["data-fold"] != "inspector":
                assert button.attributes["title"] == name
                assert "aria-disabled" not in button.attributes
            (icon,) = button.children
            assert icon.class_ == "bl-toggle-icon"
    finally:
        rendered.close()


def test_n_1_the_page_draws_no_rail_and_no_running_head_and_one_main_bar(
    app_state, scratch_folder
):
    """Unit N, Task 1 (design pass 10 §2; the brief's top bar): the regions
    draw no rail of icons, `.bl-rail` and its buttons, no running head
    `.bl-title`, `BellmanSym` over the editor or `Semantic graph` over the
    graph's bar, and no occurrence line under the tree; the main bar draws
    one `nav.bl-main-bar`; the graph column opens with one bar,
    `.bl-graph-bar`, holding `Semantic graph` and Problems; the tabs' row
    holds `Types`, pressed while the types are shown, `Notes`, pressed
    while the notes are shown, which a click sets in the editor's property
    `show_notes` (Task 4), and `Save`."""
    app_state(scratch_folder)
    regions = [
        app.MainBar(None),
        app.FolderRegion(set()),
        app.FileRegion(None, None, set()),
        app.ViewRegion(None, None),
    ]
    for region in regions:
        _, rendered = solara.render(region, handle_error=False)
        try:
            classes = {
                name
                for widget in rendered.find(v.Html).widgets
                for name in (widget.class_ or "").split()
            }
            gone = {"bl-rail", "bl-rail-button", "bl-title", "bl-recipe-head", "bl-breadcrumb"}
            assert not classes & gone, classes & gone
            assert "bl-view-bar" not in classes
        finally:
            rendered.close()
    _, rendered = solara.render(app.MainBar(None), handle_error=False)
    try:
        assert len(rendered.find(v.Html, tag="nav", class_="bl-main-bar").widgets) == 1
    finally:
        rendered.close()
    _, rendered = solara.render(app.ViewRegion(None, None), handle_error=False)
    try:
        bar = rendered.find(v.Html, class_="bl-bar bl-graph-bar").widget
        tools, problems = bar.children
        assert tools.class_ == "bl-graph-tools"
        assert drawn_text(tools.children[0]) == "Semantic graph"
        assert problems.class_ == "bl-errors"
    finally:
        rendered.close()
    _, rendered = solara.render(app.FileRegion(None, None, set()), handle_error=False)
    try:
        actions = rendered.find(v.Html, class_="bl-tab-actions").widget
        types, notes = actions.children[:2]
        assert (drawn_text(types), types.attributes["aria-pressed"]) == ("Types", "true")
        assert types.attributes["title"] == "Show or hide the bracketed entries"
        assert (drawn_text(notes), notes.attributes["aria-pressed"]) == ("Notes", "false")
        assert "aria-disabled" not in notes.attributes
        assert notes.attributes["title"] == "Show or hide the notes"
        types.fire_event("click", {})
        assert app.hide_types.value is True
        assert actions.children[0].attributes["aria-pressed"] == "false"
        notes.fire_event("click", {})
        assert app.show_notes.value is True
        assert actions.children[1].attributes["aria-pressed"] == "true"
    finally:
        app.hide_types.value = False
        app.show_notes.value = False
        rendered.close()


def test_l_23_a_form_draws_its_head_its_refusal_under_its_field_and_its_foot(
    app_state, scratch_folder
):
    """Unit L, Task 23 (AAS, L-D14; design pass 4 §§2 and 3; K-D11), in the
    system of design pass 8 (unit M, Task 6): the form `new stage` draws
    its head, the Codicon `new-file`, the heading `New stage` and the icon
    button `close`, which closes the form, with its note under it, its
    paths from the model folder; a refusal standing, its one line stands
    right after the key's field, its absolute paths printed from the model
    folder, whole in its hover; its foot holds the text button `Cancel` and
    last the primary of VSCode Elements `Write the stage`, which while no
    key is typed does not act and names in its hover what it waits for."""
    app_state(scratch_folder)
    root = app.tab_folder.value.root
    app.open_form("new stage")
    app.form_error.value = f"{root / 'declaration/stages/cons'}/ exists"
    _, rendered = solara.render(app.NewStageForm(), handle_error=False)
    try:
        (head,) = rendered.find(v.Html, class_="bl-head bl-form-head").widgets
        icon, heading, close = head.children
        assert (icon.class_, drawn_text(heading)) == (
            "codicon codicon-new-file bl-form-icon",
            "New stage",
        )
        assert close.attributes == {"icon": "close", "label": "Close", "title": "Close"}
        (note,) = rendered.find(v.Html, class_="bl-form-note").widgets
        assert note.children == [
            "writes declaration/stages/<key>/<key>.bl and adds the stage to declaration/spec.yml"
        ]
        (refusal,) = rendered.find(v.Html, class_="bl-form-error").widgets
        assert refusal.children == ["declaration/stages/cons/ exists"]
        assert refusal.attributes == {"title": "declaration/stages/cons/ exists", "role": "alert"}
        (form,) = [
            widget
            for widget in rendered.find().widgets
            if refusal in getattr(widget, "children", ())
        ]
        order = form.children
        field = order[order.index(refusal) - 1]
        assert field.classes == "bl-new-stage-key"
        (foot,) = rendered.find(v.Html, class_="bl-form-buttons").widgets
        cancel, primary = foot.children
        assert (cancel.children, primary.children) == (["Cancel"], ["Write the stage"])
        assert (cancel.tag, cancel.class_) == ("button", "bl-text-button bl-form-cancel")
        assert (primary.tag, primary.class_) == (
            "vscode-button",
            "bl-new-stage-submit bl-primary",
        )
        assert primary.attributes == {
            "disabled": True,
            "aria-disabled": "true",
            "title": "type a key",
        }
        close.fire_event("click", {})
        assert app.form_open.value is None
    finally:
        rendered.close()
        app.close_form()


# --- unit L, Task 16: the queue of values typed in the Parameters tab ---

# the matrix typed for a parameter of tenure in the queue's direct test
TENURE_MATRIX = "[[0.6, 0.4], [0.3, 0.7]]"


def test_l_16_three_values_typed_in_a_second_are_written_in_turn_and_a_matrix_is_passed_on(
    scratch_durables, app_state
):
    """Task 16 (defects 4 and 5 of the UX simulation; L-D13). With
    `tenure.bl` of the durables model shown at `periods[3]/tenure`, three
    values typed in the Parameters tab within a second, `1.05` for `R`,
    `1.0` for the unvalued `Y` and the matrix `[[0.6, 0.4], [0.3, 0.7]]`
    for the unvalued `y_R`, are each answered at once: each Enter adds its
    value to the queue and returns, and while no writer has written, the
    rows show the three values as typed and the calibration file is as it
    was. Once the writers run, the three values are written in turn, each
    once: the file holds `R: 1.05` at line 11 and `Y: 1.0` and the matrix
    added after `K: 1.3`, and the three ids are answered in order. The tab
    composes no sentence about the matrix; the stage bound again is refused
    by the package's check of its calibration, in a sentence that names
    `y_R`, which the row of `y_R` carries as its note."""
    app_state(scratch_durables)
    calibration = scratch_durables / "declaration/calibration/durables.yml"
    before = calibration.read_text(encoding="utf-8")
    lines = before.split("\n")
    assert (lines[10], lines[37]) == ("  R: 1.045", "  K: 1.3")
    typed = (("R", "1.045", "1.05"), ("Y", "unvalued", "1.0"), ("y_R", "unvalued", TENURE_MATRIX))
    app.source.value = RECIPE
    app.head.value = (3, "tenure")
    try:
        app.open_file(TENURE)
        app.run_loop()
        current = app.shown.value
        assert (current.path, current.position) == (TENURE, (3, "tenure"))
        # the writers wait while the test holds their lock
        with app.WRITER_LOCK:
            started = time.perf_counter()
            for n, (name, shown, value) in enumerate(typed):
                asked = {"tab": "Parameters", "name": name, "shown": shown, "typed": value}
                app.on_value_write({**asked, "id": f"t{n}"})
            assert time.perf_counter() - started < 1.0
            queued = app.value_queue.value["queue"]
            assert [(entry["name"], entry["typed"]) for entry in queued] == [
                (name, value) for name, _, value in typed
            ]
            rows = app._tab_rows(app.value_tab(current, "Parameters"), "Parameters", queued)
            shown_rows = {row["name"]: row["value"] for row in rows}
            assert {name: shown_rows[name] for name, _, _ in typed} == {
                name: value for name, _, value in typed
            }
            assert calibration.read_text(encoding="utf-8") == before
        wait_until(
            lambda: not any(thread.name == "value-writer" for thread in threading.enumerate()),
            20.0,
            "the queue written and its writers ended",
        )
        assert app.value_queue.value == {"queue": (), "answered": ("t0", "t1", "t2")}
        lines[10] = "  R: 1.05"
        lines[38:38] = ["  Y: 1.0", f"  y_R: {TENURE_MATRIX}"]
        assert calibration.read_text(encoding="utf-8") == "\n".join(lines)
        assert app.value_note.value is None

        # the stage bound again, as the watcher binds it once the file changed
        app.rebind.value = app.rebind.value + 1
        app.run_loop()
        current = app.shown.value
        (note,) = [note for note in current.notes if "parameter 'y_R'" in note]
        assert f"the value {TENURE_MATRIX} lies outside the declared set ℝ₊" in note
        rows = app._tab_rows(
            app.value_tab(current, "Parameters"), "Parameters", (), tuple(current.notes)
        )
        noted = {row["name"]: (row["value"], row["note"]) for row in rows}
        assert noted["y_R"] == (TENURE_MATRIX, app.folder_relative(note))
        assert noted["R"] == ("1.05", None)
        assert not any("reads as" in sentence for sentence in current.notes)
    finally:
        app.value_queue.value = {"queue": (), "answered": ()}
        app.value_note.value = None
        app.source.value, app.head.value, app.view_mode.value = None, None, "stage"
        app.open_path.value, app.buffers.value, app.results.value = None, {}, {}
        app.shown.value, app.drawing.value, app.rebind_sources.value = None, False, {}
        app.rebind.value = 0
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_l_16_a_value_whose_write_raises_leaves_the_steps_after_the_earlier_write_taken(
    scratch_durables, app_state, monkeypatch
):
    """Task 16 (unit L's final judgment, §6 item 6). With `tenure.bl` of
    the durables model shown at `periods[3]/tenure`, `1.05` typed for `R`
    and `1.0` for `Y` within a second, where the write of `Y` raises: the
    writer writes `R`, answers both values and raises, and the steps after
    a write (`_after_write`) are taken once, for the calibration file that
    `R` was written to, so that the stage is bound again with its value."""
    app_state(scratch_durables)
    calibration = "declaration/calibration/durables.yml"
    write_value, after_write = recipe.write_value, app._after_write
    # the files the steps after a write were taken for, and the exceptions
    # the writers' threads raised
    taken, raised = [], []

    def raising(folder, record, key, kind, name, shown, typed):
        if name == "Y":
            raise RuntimeError("the write of Y raised")
        return write_value(folder, record, key, kind, name, shown, typed)

    def recorded(path, written):
        taken.append(path)
        after_write(path, written)

    monkeypatch.setattr(recipe, "write_value", raising)
    monkeypatch.setattr(app, "_after_write", recorded)
    monkeypatch.setattr(threading, "excepthook", lambda hooked: raised.append(hooked.exc_value))
    app.source.value = RECIPE
    app.head.value = (3, "tenure")
    try:
        app.open_file(TENURE)
        app.run_loop()
        typed = (("R", "1.045", "1.05"), ("Y", "unvalued", "1.0"))
        # the writers wait while the test holds their lock
        with app.WRITER_LOCK:
            for n, (name, shown, value) in enumerate(typed):
                asked = {"tab": "Parameters", "name": name, "shown": shown, "typed": value}
                app.on_value_write({**asked, "id": f"t{n}"})
        wait_until(
            lambda: not any(thread.name == "value-writer" for thread in threading.enumerate()),
            20.0,
            "the queue written and its writers ended",
        )
        assert [str(error) for error in raised] == ["the write of Y raised"]
        assert app.value_queue.value == {"queue": (), "answered": ("t0", "t1")}
        lines = (scratch_durables / calibration).read_text(encoding="utf-8").split("\n")
        assert lines[10] == "  R: 1.05"
        assert taken == [calibration]
    finally:
        app.value_queue.value = {"queue": (), "answered": ()}
        app.value_note.value = None
        app.source.value, app.head.value, app.view_mode.value = None, None, "stage"
        app.open_path.value, app.buffers.value, app.results.value = None, {}, {}
        app.shown.value, app.drawing.value, app.rebind_sources.value = None, False, {}
        app.rebind.value = 0
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_l_17_one_undo_takes_a_drop_back_in_both_files_it_edited(repository, app_state):
    """Task 17 (defect 6 of the UX simulation: one undo per gesture, across
    all the files the gesture edited). In a folder `new trellis` wrote,
    whose trellis file writes its earliest period's stages in its own entry
    and whose recipe gives `port` the periods 0 to 5, the stage `port`
    dropped on periods[6] edits the trellis file's entry and widens port's
    range in the recipe. With the trellis file open, the request of its own
    edit carries the gesture's key, and the gesture's step holds both files'
    texts. The editor's undo of that edit, with the key, takes the recipe's
    buffer back, so that neither file is unsaved; its redo makes the edit
    again in the recipe, and a second undo takes it back again. Made again,
    and the recipe opened, whose editor history the change of file began
    again, Mod-z with no step of the history to undo asks the editor for the
    recipe's part, kept out of its history, where the editor holds the text
    the gesture left, and at the editor's true answer the trellis file
    follows; a second Mod-z asks nothing."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    folder = created.folder
    trellis_file, recipe_file = "declaration/trellis.yml", RECIPE_FILE
    six = "  - {template: period.yml, repeat: 6}\n"
    earliest = "  - {stages: [cons, disc], connectors: [{}]}\n"
    texts = {}
    for name, old, new in (
        (trellis_file, six, six + earliest),
        (recipe_file, "port/methods.bl]}}", "port/methods.bl]}, periods: [0, 5]}"),
    ):
        text = (folder / name).read_text(encoding="utf-8")
        assert text.count(old) == 1
        texts[name] = text.replace(old, new)
        (folder / name).write_text(texts[name], encoding="utf-8")
    made = {
        trellis_file: texts[trellis_file].replace(
            "[cons, disc], connectors", "[cons, disc, port], connectors"
        ),
        recipe_file: texts[recipe_file].replace("periods: [0, 5]", "periods: [0, 6]"),
    }
    app_state(folder)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    try:
        outcome = app.run_trellis()
        assert outcome is not None and outcome.refusal is None
        app.open_file(trellis_file)
        opened = app.buffers.value[trellis_file]["document_revision"]
        editor = {"path": trellis_file, "revision": opened, "text": texts[trellis_file]}
        answer = {"path": trellis_file, "revision": opened}
        event = dropped_event(
            outcome.shown, app.tab_folder.value, "port", "stage", "periods[6]___group___"
        )
        app.on_dropped(event)
        app.on_change(editor)
        app.on_applied({**answer, "n": app.edit_request.value["n"], "applied": True})
        own = app.edit_request.value
        key = own["gesture"]
        edits = [model.Replacement(**edit) for edit in own["edits"]]
        assert applied(texts[trellis_file], edits) == made[trellis_file]
        app.on_applied({**answer, "n": own["n"], "applied": True})
        (step,) = app.gesture_steps.value
        assert (step["key"], step["undone"]) == (key, False)
        assert step["files"] == {name: (texts[name], made[name]) for name in texts}
        assert app.buffers.value[recipe_file]["text"] == made[recipe_file]
        app.on_change({**editor, "text": made[trellis_file]})
        assert app.open_path.value == trellis_file

        # the editor's undo of the trellis file's edit, its redo, its undo
        for redo, text in ((False, texts), (True, made), (False, texts), (True, made)):
            undo = {**answer, "gesture": key, "redo": redo, "text": text[trellis_file]}
            app.on_gesture_undo(undo)
            app.on_change({**editor, "text": text[trellis_file]})
            assert app.buffers.value[recipe_file]["text"] == text[recipe_file]
            assert app.gesture_steps.value[0]["undone"] is not redo
            assert (app.unsaved_texts() == {}) is not redo

        # with the recipe open, Mod-z with no step of the editor's to undo
        app.open_file(recipe_file)
        app.on_change({**editor, "text": made[trellis_file]})
        assert app.open_path.value == recipe_file
        revision = app.buffers.value[recipe_file]["document_revision"]
        place = {"path": recipe_file, "revision": revision}
        asked = {**place, "gesture": None, "redo": False}
        app.on_gesture_undo({**asked, "text": made[recipe_file]})
        request = app.edit_request.value
        assert (request["expected"], request["history"]) == (made[recipe_file], False)
        edits = [model.Replacement(**edit) for edit in request["edits"]]
        assert applied(made[recipe_file], edits) == texts[recipe_file]
        assert app.buffers.value[trellis_file]["text"] == made[trellis_file]
        app.on_applied({**place, "n": request["n"], "applied": True})
        assert app.buffers.value[trellis_file]["text"] == texts[trellis_file]
        assert app.gesture_steps.value[0]["undone"] is True
        app.on_gesture_undo({**asked, "text": texts[recipe_file]})
        assert app.edit_request.value is request
    finally:
        clear_gesture_state()
        clear_trellis_state()


# The two lines of the pension model's `contribution` stage that write the
# contribution rate out inside each expression (`pensions-working-years`),
# and the three lines the UX simulation's post-doc typed first in their place
# (the record's `texts/50-contribution-v1.bl`, step 47), in which the
# intermediate line `v_rate` is read inside the tuple that the plan label
# selects: the package raises a KeyError for it in place of a refusal
# (defect 18; the package's issue of that KeyError), its message naming the
# line `contributions`, which then stands at line 40.
CONTRIBUTION = "declaration/stages/contribution/contribution.bl"
WRITTEN_OUT = ("    w_c ", "    adc_c ")
V_RATE_LINES = (
    "    v_rate = (0, v_1, v_2, v_3, v_4, v_5)[v] :: [id=contribution_rate]\n"
    "    w_c = a_d + (1 - v_S - v_rate)*y_d :: [id=take_home]\n"
    "    adc_c = adc_d + (((1 - o)*v_E + v_rate)*y_d, (v_E + v_S + v_rate)*y_d)[plan_d]"
    " :: [id=contributions]\n"
)
V_RATE_EXCEPTION = (
    "KeyError: \"unresolved semantic input MarkedName(stem='v_rate', mark=None) at "
    'dcsn_to_cntn.contributions"'
)


def test_l_21_an_exception_names_its_operation_and_log_entry_without_a_rule_or_line(
    app_state, tmp_path, monkeypatch, caplog
):
    """An unexpected exception in the contribution stage has no rule or
    source position. The loop, trellis reading and Details name the stopped
    operation and its log entry; the Problems list holds one line for the
    three occurrences, and the log holds each exception's traceback."""
    copy = pensions_copy(tmp_path / "models" / "durables", PENSIONS_WORKING_YEARS)
    stage = copy / CONTRIBUTION
    lines = stage.read_text(encoding="utf-8").splitlines(keepends=True)
    assert [line[: len(start)] for line, start in zip(lines[37:39], WRITTEN_OUT)] == list(
        WRITTEN_OUT
    )
    stage.write_text("".join(lines[:37]) + V_RATE_LINES + "".join(lines[39:]), encoding="utf-8")
    app_state(copy)
    occurrences = ((4, "contribution"), (5, "contribution"), (6, "contribution"))
    app.source.value = recipe.Source("recipe", PENSIONS_RECIPE)
    try:
        app.open_file(CONTRIBUTION)
        with caplog.at_level(logging.ERROR, logger="bellman_workbench.model"):
            outcome = app.run_loop()
        assert app.shown.value is None and outcome.stale
        (refusal,) = outcome.refusals
        assert refusal.message == V_RATE_EXCEPTION
        assert (refusal.kind, refusal.operation, refusal.rule, refusal.address, refusal.line) == (
            "internal", "elaborate", None, None, None,
        )
        assert refusal.entry and refusal.occurrences == occurrences
        editor = app.editor_record(refusal)
        assert all(editor[key] is None for key in ("line", "column", "end_line", "end_column", "rule"))
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert listed == [(V_RATE_EXCEPTION, CONTRIBUTION, None)]
        (record,) = [each for each in caplog.records if each.name == "bellman_workbench.model"]
        assert record.levelno == logging.ERROR and CONTRIBUTION in record.getMessage()
        assert isinstance(record.exc_info[1], KeyError) and record.exc_info[2] is not None
        _, rendered = solara.render(app.RefusalBox(CONTRIBUTION, refusal), handle_error=False)
        try:
            head = drawn_text(rendered.find(v.Html, class_="bl-refusal-rule").widget)
            assert head == f"elaborate stopped in {CONTRIBUTION} · logged as {refusal.entry}"
        finally:
            rendered.close()

        app.source.value = recipe.Source("recipe", PENSIONS_RECIPE)
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="bellman_workbench.model"):
            read = app.run_trellis()
        found = read.refusal
        assert read.shown is None and found.message == V_RATE_EXCEPTION
        assert (found.kind, found.operation, found.line, found.rule, found.address) == (
            "internal", "elaborate", None, None, None,
        )
        assert found.entry and found.occurrences == occurrences
        assert recipe.relative(app.tab_folder.value, found.file) == CONTRIBUTION
        listed = [(each.sentence, each.file, each.line) for each in app.standing_refusals()]
        assert listed == [(V_RATE_EXCEPTION, CONTRIBUTION, None)]
        (record,) = [each for each in caplog.records if each.name == "bellman_workbench.model"]
        assert isinstance(record.exc_info[1], KeyError) and record.exc_info[2] is not None

        def raising(*arguments, **keywords):
            raise RuntimeError("an error of the reading")

        monkeypatch.setattr(trellis, "show_trellis", raising)
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="bellman_workbench.model"):
            read = app.run_trellis()
        found = read.refusal
        assert (found.file, found.kind, found.operation, found.rule, found.line) == (
            str((copy / PENSIONS_RECIPE).resolve()), "internal", "read", None, None,
        )
        assert found.message == "RuntimeError: an error of the reading" and found.entry
        assert (found.message, PENSIONS_RECIPE, None) in [
            (each.sentence, each.file, each.line) for each in app.standing_refusals()
        ]
        (record,) = [each for each in caplog.records if each.name == "bellman_workbench.model"]
        assert isinstance(record.exc_info[1], RuntimeError)
    finally:
        clear_trellis_state()


def test_l_21_the_list_holds_each_refusal_once_and_no_line_of_a_verb_skipped(
    app_state, scratch_folder, tmp_path
):
    """Task 21 (defect 17 of the UX simulation; K-D29; A2-D13). On a copy
    of the portfolio model whose cons addition names the stage port, the
    stage shown's binding of cons.bl and the trellis's reading, which
    constructs the stage with its addition, both refuse that addition: the
    list holds that refusal once, and each other refusal once. On a folder
    of the forms,
    whose bindings are slots, every verb is skipped: neither the trellis's
    binding nor cons.bl's gives a note, and no line of the list names a
    source, since a slot is a parameter of the load and no refusal."""
    methods = scratch_folder / "declaration/stages/cons/methods.bl"
    _rewrite(methods, "@methods: cons\n", "@methods: port\n")
    app_state(scratch_folder)
    app.source.value = RECIPE

    def listed() -> list[str]:
        # the sentences of the list under the error mark
        return [each.sentence for each in app.standing_refusals()]

    try:
        app.open_file(CONS)
        app.run_loop()
        assert any("'port'" in note for note in app.shown.value.notes)
        outcome = app.run_trellis()
        assert outcome.shown is None and outcome.refusal.rule == "metadata-mismatch"
        found = listed()
        assert sum("'port'" in sentence for sentence in found) == 1, found
        assert len(found) == len(set(found))

        # the folder of the forms, in a tab that holds nothing of the first
        clear_trellis_state()
        app.open_path.value, app.buffers.value, app.results.value = None, {}, {}
        app.shown.value = None
        app_state(written_from_the_forms(tmp_path / "demo"))
        app.source.value = RECIPE
        outcome = app.run_trellis()
        assert outcome.shown.binding.skipped == ("calibrate", "methodize", "configure")
        assert trellis.binding_notes(outcome.shown.binding) == []
        app.open_file(CONS)
        app.run_loop()
        assert app.shown.value.occurrence == "periods[0] / cons" and app.shown.value.notes == []
        assert not [sentence for sentence in listed() if " source" in sentence]
    finally:
        clear_trellis_state()
        app.sources.value, app.tree.value, app.git_line.value = [], [], ""
        app.folder_read.value = False


def test_l_21_a_target_error_of_the_elaboration_is_a_refusal_under_its_own_rule(
    app_state, scratch_folder, monkeypatch, caplog
):
    """Task 21 (unit L's final judgment, §6 item 8; Task 21's review, Minor
    3): a `TargetError` that the elaboration of the open text raises is of
    a class of the package's refusals (`model.is_refusal`), so the loop's
    one refusal is its sentence under the rule of the identity table it
    names, the state is `parsed, refused`, and
    the page's log holds no exception where a refusal was due."""
    sentence = "'no_such_builder' in stage 'cons' names no builder"

    def raising(text, origin):
        raise TargetError("no_such_builder", "cons", TARGET_RULES[0], (), sentence)

    monkeypatch.setattr(model, "elaborate_text", raising)
    app_state(scratch_folder)
    app.source.value = None
    text = (scratch_folder / CONS).read_text(encoding="utf-8")
    try:
        with caplog.at_level(logging.ERROR, logger="bellman_workbench.app"):
            outcome, current = app.elaborate(CONS, text, 1)
        assert current is None and outcome.state == "parsed, refused"
        (refusal,) = outcome.refusals
        assert (refusal.message, refusal.rule) == (sentence, TARGET_RULES[0])
        assert not [each for each in caplog.records if each.name == "bellman_workbench.app"]
    finally:
        clear_trellis_state()


def test_l_21_the_status_line_and_problems_count_the_same_unjoined_fields(app_state, tmp_path):
    """Status and Problems count native unjoined internal inputs, once per field."""
    from workbench_support import composition_folder

    path = composition_folder(tmp_path / "counts", repeat=2)
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    try:
        outcome = app.run_trellis()
        held = outcome.shown
        found = trellis.missing_joins(app.tab_folder.value, held)
        assert {(each["key"], each["field"]) for each in found} == {("S", "x"), ("U", "z")}
        assert trellis.unjoined_count(held) == len(found) == 2
        _, rest = app.trellis_status_parts(outcome, held)
        assert " · 2 unjoined internal entry fields" in "".join(text for text, _ in rest)
        items = app.lacking_items((), outcome, held, app.tab_folder.value)
        assert {item.label for item in items if item.kind == "unjoined"} == {"S · x unjoined", "U · z unjoined"}
    finally:
        clear_trellis_state()


def test_l_22_a_tree_name_is_divided_into_words_each_with_the_separators_before_it():
    """Task 22 (defect 23 of the UX simulation): the tree divides a name
    into words before each separator, `_`, `.`, `-` or a space, that follows
    another character, so that brand.css cuts the name after a whole word;
    the words make the name, and a name that begins with separators keeps
    them on its first word."""
    cases = {
        "period.pensions.yml": ["period", ".pensions", ".yml"],
        "adjuster_cons_pa/": ["adjuster", "_cons", "_pa/"],
        "spec.two-stages.yml": ["spec", ".two", "-stages", ".yml"],
        "__init__.py": ["__init", "__.py"],
        ".gitignore": [".gitignore"],
        "declaration/": ["declaration/"],
    }
    for name, words in cases.items():
        assert app.name_words(name) == words, name
        assert "".join(app.name_words(name)) == name


def test_l_25_a_removal_is_one_undo_and_deletes_its_files_when_the_recipe_is_saved(
    scratch_folder, app_state
):
    """Unit L, Task 25 (AAS, L-D18; J-D33 and J-D39). On a copy of the
    portfolio model with no file open, `remove stage` of `port` puts the
    recipe, period.yml and trellis.yml in their unsaved buffers as one
    gesture, whose step lists `stages/port/` and `settings/port.yml`, which
    join the files to delete on save under its key; nothing is deleted from
    disk. The recipe opens at the row's line, and Mod-z there, with no step
    of the editor's history to undo, takes the gesture back in all three
    files and withdraws the two files. Made again, a save of the recipe
    deletes them, the status line naming them, `deleted: stages/port/,
    settings/port.yml`, and none stays listed. The tree offers the stage
    folders no row names, `cons_obs` and `noport`; `remove` marks
    `stages/noport/`, `keep` withdraws the mark, and marked again, the next
    save of any file deletes it."""
    root = scratch_folder
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    edited_files = [RECIPE_FILE, "declaration/period.yml", "declaration/trellis.yml"]
    listed = ("declaration/stages/port", "declaration/settings/port.yml")
    texts = {name: (root / name).read_text(encoding="utf-8") for name in edited_files}
    try:
        assert app.run_trellis().refusal is None
        app.remove_stage("port")
        made = {name: app.buffers.value[name]["text"] for name in edited_files}
        assert all(made[name] != texts[name] for name in edited_files)
        assert sorted(app.unsaved_texts()) == sorted(str((root / n).resolve()) for n in made)
        (step,) = app.gesture_steps.value
        assert step["deleted"] == listed
        assert app.deleting.value == tuple((path, step["key"]) for path in listed)
        assert app.gesture_note.value["sentence"].endswith(
            "deleted on save: stages/port/, settings/port.yml"
        )
        assert all((root / path).exists() for path in listed)
        assert app.open_path.value == RECIPE_FILE

        # Mod-z in the recipe takes the gesture back in all three files
        revision = app.buffers.value[RECIPE_FILE]["document_revision"]
        place = {"path": RECIPE_FILE, "revision": revision}
        app.on_gesture_undo({**place, "gesture": None, "redo": False, "text": made[RECIPE_FILE]})
        request = app.edit_request.value
        assert request["history"] is False
        app.on_applied({**place, "n": request["n"], "applied": True})
        app.on_change({**place, "text": texts[RECIPE_FILE]})
        assert app.unsaved_texts() == {}
        assert app.deleting.value == ()
        assert app.gesture_steps.value[0]["undone"] is True

        # made again with the recipe open, its own edit asked last under the
        # gesture's key (J-D36); a save of the recipe then deletes the
        # stage's folder and file
        assert app.run_trellis().refusal is None
        app.remove_stage("port")
        app.on_change({**place, "text": texts[RECIPE_FILE]})
        app.on_applied({**place, "n": app.edit_request.value["n"], "applied": True})
        own = app.edit_request.value
        assert own["gesture"] is not None
        app.on_applied({**place, "n": own["n"], "applied": True})
        app.on_change({**place, "text": made[RECIPE_FILE]})
        assert app.gesture_steps.value[-1]["key"] == own["gesture"]
        assert app.deleting.value == tuple((path, own["gesture"]) for path in listed)
        assert all((root / path).exists() for path in listed)
        recipe_text = app.buffers.value[RECIPE_FILE]["text"]
        assert recipe_text == made[RECIPE_FILE]
        app.on_save({**place, "text": recipe_text})
        assert (root / RECIPE_FILE).read_text(encoding="utf-8") == made[RECIPE_FILE]
        assert not any((root / path).exists() for path in listed)
        assert app.gesture_note.value["sentence"] == "deleted: stages/port/, settings/port.yml"
        assert app.deleting.value == ()

        # the tree's control: remove, keep, remove, and the next save
        noport = "declaration/stages/noport"
        assert creation.removable_files(root) == (
            "declaration/stages/cons_obs",
            noport,
        )
        app.toggle_deletion(noport)
        assert app.deleting.value == ((noport, None),)
        app.toggle_deletion(noport)
        assert app.deleting.value == ()
        app.toggle_deletion(noport)
        app.on_save({**place, "text": recipe_text})
        assert not (root / noport).exists() and (root / "declaration/stages/cons_obs").is_dir()
        assert app.gesture_note.value["sentence"] == "deleted: stages/noport/"
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_m_2_a_stage_removal_that_cannot_act_lists_its_sentence_under_the_error_mark(
    scratch_folder, app_state
):
    """Unit M, Task 2 (AAS, M-D2). On a copy of the portfolio model with no
    file open and its recipe the source, `remove stage` of `port` before
    the trellis view holds a reading writes nothing and lists the page's
    sentence under the error mark, at the line of `port`'s row in the
    recipe: the trellis is still being read. Once the trellis is read and
    its next reading is refused, the earlier trellis still drawn, the same
    gesture writes nothing and its sentence says that the trellis stands
    refused, in place of the sentence of an old graph."""
    root = scratch_folder
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    recipe_text = (root / RECIPE_FILE).read_text(encoding="utf-8")
    row = next(
        number
        for number, line in enumerate(recipe_text.splitlines(), 1)
        if line.startswith("  port:")
    )
    unread = (
        "spec.yml: port was not removed, since the trellis of spec.yml is still being read; "
        "remove port again once the trellis is drawn"
    )
    refused = (
        "spec.yml: port was not removed, since the trellis of spec.yml stands refused; "
        "remove port again once the trellis is drawn"
    )
    try:
        assert app.trellis_shown.value is None
        app.remove_stage("port")
        lines = [(line.sentence, line.file, line.line) for line in app.standing_refusals()]
        assert lines == [(unread, RECIPE_FILE, row)]
        assert app.buffers.value == {} and app.gesture_steps.value == ()
        assert app.deleting.value == () and app.gesturing.value is None

        # the trellis read, then its next reading refused: a connector of
        # the period file names a field no stage declares
        assert app.run_trellis().refusal is None
        period = root / "declaration/period.yml"
        text = period.read_text(encoding="utf-8")
        period.write_text(text.replace("{m_next: m}", "{m_next: m_X}", 1), encoding="utf-8")
        assert app.run_trellis().refusal is not None
        assert app.trellis_shown.value is not None
        app.remove_stage("port")
        lines = [(line.sentence, line.file, line.line) for line in app.standing_refusals()]
        assert lines[0] == (refused, RECIPE_FILE, row)
        assert not any("earlier text" in sentence for sentence, _, _ in lines)
        assert app.buffers.value == {} and app.gesture_steps.value == ()
        assert app.deleting.value == () and app.gesturing.value is None
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_m_5_the_recipe_tab_reads_the_recipe_as_the_trellis_reading_reads_it(
    scratch_durables, app_state
):
    """Unit M, Task 5 (M-D7; spec 0.4 §3.1), on the Recipe tab of Task 10
    (design pass 9 §4). On a copy of the durables model with no file open
    and its recipe the source, `remove stage` of `bequest` takes its row out
    of the recipe's unsaved buffer; once the trellis is read from the
    buffers, the Recipe tab holds no row of `bequest`, while the recipe on
    disk still writes its row. Then the row of `keeper_cons` typed out of
    the buffer, a text the package refuses since the trellis file still
    lists that stage, leaves the rows the last reading read, `keeper_cons`
    among them, and the reading's refusal stands in the list under the
    error mark."""
    root = scratch_durables
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    on_disk = (root / RECIPE_FILE).read_text(encoding="utf-8")
    try:
        assert app.run_trellis().refusal is None
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)

        def stages():
            # every row of the tab in its order
            return [
                row.attributes["data-stage"]
                for row in rendered.find(v.Html, class_="bl-recipe-row").widgets
            ]

        try:
            assert stages() == ["tenure", "keeper_cons", "adjuster_cons", "bequest"]
            app.remove_stage("bequest")
            assert app.run_trellis().refusal is None
            assert stages() == ["tenure", "keeper_cons", "adjuster_cons"]
            assert (root / RECIPE_FILE).read_text(encoding="utf-8") == on_disk

            # the row of keeper_cons typed out of the recipe's buffer
            held = app.buffers.value[RECIPE_FILE]
            (row,) = [
                line for line in held["text"].splitlines(True) if line.startswith("  keeper_cons:")
            ]
            app.on_change(
                {
                    "path": RECIPE_FILE,
                    "text": held["text"].replace(row, ""),
                    "revision": held["document_revision"],
                }
            )
            assert app.run_trellis().refusal is not None
            assert stages() == ["tenure", "keeper_cons", "adjuster_cons"]
            (listed,) = app.standing_refusals()
            assert listed.file == RECIPE_FILE
            assert "holds the stage 'keeper_cons'" in listed.sentence
        finally:
            rendered.close()
    finally:
        clear_gesture_state()
        clear_trellis_state()


# the durables model's trellis file, relative to the folder, whose entry of
# periods[0] lists the terminal period's stages (unit N, Task 5)
DURABLES_TRELLIS = "declaration/trellis.yml"


def undo_in(path: str, made: str, before: str) -> None:
    """Mod-z in the open file `path`, whose editor history holds no step of
    the last gesture, its text `made`: the gesture's step taken back there
    by the editor's answer and the change it then sends, the text `before`
    (unit L, Task 17; `on_gesture_undo`)."""
    place = {"path": path, "revision": app.buffers.value[path]["document_revision"]}
    app.on_gesture_undo({**place, "gesture": None, "redo": False, "text": made})
    request = app.edit_request.value
    assert request["history"] is False
    app.on_applied({**place, "n": request["n"], "applied": True})
    app.on_change({**place, "text": before})


def test_n_5_a_gesture_that_edits_one_closed_file_is_one_undo_step(scratch_durables, app_state):
    """Unit N, Task 5 (the brief's "Verify graph, recipe, source and undo
    agree"). On a copy of the durables model with no file open and its
    recipe the source, `Remove from periods 0` of `periods[0]/keeper_cons`
    (`remove_occurrence`) takes the key and its connector's pairs out of
    trellis.yml alone, the stage standing in period.yml still, so the
    recipe keeps its row. The gesture is one step among the tab's gestures,
    though it edits one file, since the editor did not hold that file; the
    file opens at its line, and Mod-z there, with no step of the editor's
    history to undo, takes the gesture back."""
    root = scratch_durables
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    text = (root / DURABLES_TRELLIS).read_text(encoding="utf-8")
    try:
        assert app.run_trellis().refusal is None
        app.remove_occurrence((0, "keeper_cons"))
        assert sorted(app.unsaved_texts()) == [str((root / DURABLES_TRELLIS).resolve())]
        made = app.buffers.value[DURABLES_TRELLIS]["text"]
        assert "  - stages: [tenure, adjuster_cons, bequest]\n" in made
        assert app.gesture_note.value["sentence"].startswith(
            "trellis.yml, periods[0].stages: keeper_cons removed, periods 0"
        )
        (step,) = app.gesture_steps.value
        assert set(step["files"]) == {DURABLES_TRELLIS}
        assert app.open_path.value == DURABLES_TRELLIS
        undo_in(DURABLES_TRELLIS, made, text)
        assert app.unsaved_texts() == {}
        assert app.gesture_steps.value[0]["undone"] is True
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_n_5_a_removal_from_the_stage_s_only_list_takes_its_row_in_one_undo_step(
    scratch_durables, app_state
):
    """Unit N, Task 5 (N-D8; design pass 10 §7). On a copy of the durables
    model with no file open, `Remove from periods 0` of `periods[0]/bequest`,
    whose list in trellis.yml is the only one that holds it, takes the key,
    its connector and the recipe's row out as one gesture, one step among
    the tab's gestures that lists no file to delete; its note names the list
    and the row; the next reading is constructed and holds no bequest, and
    the Recipe tab reads it so. Mod-z in trellis.yml, which opens at the
    line, takes the gesture back in both files."""
    root = scratch_durables
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    names = (RECIPE_FILE, DURABLES_TRELLIS)
    texts = {name: (root / name).read_text(encoding="utf-8") for name in names}
    try:
        assert app.run_trellis().refusal is None
        app.remove_occurrence((0, "bequest"))
        assert sorted(app.unsaved_texts()) == sorted(str((root / n).resolve()) for n in names)
        made = {name: app.buffers.value[name]["text"] for name in names}
        assert "  bequest:" not in made[RECIPE_FILE]
        assert app.gesture_note.value["sentence"].startswith(
            "trellis.yml, periods[0].stages: bequest removed, periods 0; "
            "spec.yml, stages: bequest removed; "
        )
        (step,) = app.gesture_steps.value
        assert (set(step["files"]), step["deleted"]) == (set(names), ())
        assert app.deleting.value == ()
        assert app.run_trellis().refusal is None
        periods = app.trellis_shown.value.trellis["periods"]
        assert all("bequest" not in period["stages"] for period in periods)
        assert app.open_path.value == DURABLES_TRELLIS
        undo_in(DURABLES_TRELLIS, made[DURABLES_TRELLIS], texts[DURABLES_TRELLIS])
        assert app.unsaved_texts() == {}
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_n_5_the_recipe_tab_s_add_stage_list_adds_an_item_as_a_drop_on_its_period_file(
    scratch_durables, app_state
):
    """Unit N, Task 5 (design pass 10 §7: the Recipe tab's `+ Stage` opens
    the list a period's `+ stage` opens). On a copy of the durables model
    with no file open and its recipe the source, the button `Stage` of the
    Recipe tab, pressed, draws the stage list beside it, its head `Stages`
    and the items of the graph's list, the folder's stages dimmed with
    `listed` where period.yml's list holds them, no select of the period
    file, since the trellis names one; a click on the portfolio model's
    `port` closes the list and adds it to period.yml as a drop on periods[1]
    adds it, the note ending `port unconnected`, and the item is marked
    chosen when the list opens again."""
    root = scratch_durables
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    try:
        assert app.run_trellis().refusal is None
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)
        try:
            add = rendered.find(v.Html, class_="bl-text-button bl-recipe-add-stage").widget
            add.fire_event("click", {})
            assert add.attributes["aria-expanded"] == "true"
            (chooser,) = rendered.find(v.Html, class_="bf-stage-list bl-stage-chooser").widgets
            items = {
                item.attributes["data-item"]: item
                for item in rendered.find(v.Html, tag="button").widgets
                if "bf-stage-item" in item.class_.split()
            }
            assert list(items)[:4] == ["tenure", "keeper_cons", "adjuster_cons", "bequest"]
            listed = [key for key, item in items.items() if "bf-listed" in item.class_.split()]
            assert listed == ["tenure", "keeper_cons", "adjuster_cons"]
            assert not rendered.find(ipyvue.VueTemplate, class_="bl-chooser-period-file").widgets
            items[PORT_TEMPLATE].fire_event("click", {})
            assert app.recipe_chooser.value is False
            assert app.gesture_note.value["sentence"].startswith(
                "period.yml, stages: port written, periods 1–50;"
            )
            assert app.gesture_note.value["sentence"].endswith("; port unconnected")
            add = rendered.find(v.Html, class_="bl-text-button bl-recipe-add-stage").widget
            add.fire_event("click", {})
            chosen = [
                item.attributes["data-item"]
                for item in rendered.find(v.Html, tag="button").widgets
                if "bf-chosen" in item.class_.split()
            ]
            assert chosen == [PORT_TEMPLATE]
        finally:
            rendered.close()
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_n_5_the_recipe_tab_s_add_stage_list_asks_the_period_file_where_the_trellis_names_two(
    scratch_durables, app_state
):
    """Unit N, Task 5 (design pass 10 §7: "with a select of the period file
    at its head when the trellis names more than one template"). On a copy
    of the durables model whose trellis file writes its earliest period
    from `period.young.yml`, a copy of `period.yml`, the Recipe tab's stage
    list draws the select `Period file` with the two files, `period.yml`
    first; `period.young.yml` chosen, the stage `bequest` chosen from the
    list is written into that file's list alone, periods[50]."""
    root = scratch_durables
    declaration = root / "declaration"
    shutil.copy(declaration / "period.yml", declaration / "period.young.yml")
    trellis_file = declaration / "trellis.yml"
    text = trellis_file.read_text(encoding="utf-8")
    entry = "  - {template: period.yml, repeat: 50}\n"
    assert text.count(entry) == 1
    split = "  - {template: period.yml, repeat: 49}\n  - {template: period.young.yml, repeat: 1}\n"
    trellis_file.write_text(text.replace(entry, split), encoding="utf-8")
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "forward"
    try:
        assert app.run_trellis().refusal is None
        _, rendered = solara.render(app.RecipeRegion(), handle_error=False)
        try:
            add = rendered.find(v.Html, class_="bl-text-button bl-recipe-add-stage").widget
            add.fire_event("click", {})
            (select,) = [
                widget
                for widget in rendered.find(ipyvue.VueTemplate).widgets
                if "bl-chooser-period-file" in widget.classes
            ]
            assert (select.value, list(select.options)) == (
                "period.yml",
                ["period.yml", "period.young.yml"],
            )
            select.vue_entered("period.young.yml")
            items = {
                item.attributes["data-item"]: item
                for item in rendered.find(v.Html, tag="button").widgets
                if "bf-stage-item" in item.class_.split()
            }
            items["bequest"].fire_event("click", {})
            assert app.gesture_note.value["sentence"].startswith(
                "period.young.yml, stages: bequest written, periods 50;"
            )
            assert sorted(app.unsaved_texts()) == sorted(
                str((root / name).resolve())
                for name in (RECIPE_FILE, "declaration/period.young.yml")
            )
        finally:
            rendered.close()
    finally:
        clear_gesture_state()
        clear_trellis_state()


# the template of the corpus whose fields match no field of the durables
# model, the portfolio model's `port` of cons-port's lesson (unit N, Task 5)
PORT_TEMPLATE = "cons-port/declaration/spec.port-cons.yml#port"


def test_n_5_the_last_gesture_s_note_stands_in_a_stage_s_view_too(scratch_durables, app_state):
    """Unit N, Task 5 (the brief's "show success or the actual refusal"):
    the status line holds the note of the last gesture that wrote,
    `.bl-gesture-note`, in a stage's view as in the trellis view, so that a
    removal made from Details or the Recipe tab with a stage file open names
    what it wrote."""
    app_state(scratch_durables)
    note = "trellis.yml, periods[0].stages: bequest removed, periods 0"
    try:
        app.gesture_note.value = {"sentence": note, "made": time.monotonic()}
        for mode in ("stage", "trellis"):
            app.view_mode.value = mode
            _, rendered = solara.render(
                app.StatusRegion(None, False, None, False), handle_error=False
            )
            try:
                (found,) = rendered.find(v.Html, class_="bl-gesture-note").widgets
                assert found.children == [note], mode
            finally:
                rendered.close()
    finally:
        clear_gesture_state()
        clear_trellis_state()


def test_n_5_backspace_where_the_removal_cannot_act_lists_one_sentence(
    scratch_durables, app_state
):
    """Unit N, Task 5 (N-D12; design pass 10 §7). On a copy of the durables
    model with its recipe the source and its trellis read, Backspace on the
    selected card of `periods[0]/bequest` in the backward trellis graph,
    which the region sends with no reading, writes nothing and lists the
    one sentence `Backspace acts in the forward trellis view` under the
    error mark; in the forward view, where the region sends no reading while
    the inputs are being read again, the sentence of `remove stage` that
    cannot act. A removal that waits for the editor and is withdrawn by a
    new reading leaves the sentence that asks for it again."""
    root = scratch_durables
    app_state(root)
    app.source.value = RECIPE
    app.view_mode.value, app.graph.value = "trellis", "backward"
    event = {"reading": None, "occurrence": f"periods[0]/bequest{LAYER_ID_ENDING}"}
    try:
        assert app.run_trellis().refusal is None
        app.on_removed(event)
        assert app.gesture_refusal.value["sentence"] == app.BACKSPACE_FORWARD
        assert app.BACKSPACE_FORWARD in [line.sentence for line in app.standing_refusals()]
        assert app.BACKSPACE_FORWARD == "Backspace acts in the forward trellis view"
        assert app.buffers.value == {} and app.gesture_steps.value == ()
        assert app.gesturing.value is None

        app.graph.value = "forward"
        app.on_removed(event)
        assert app.gesture_refusal.value["sentence"] == (
            "spec.yml: bequest was not removed, since the trellis of spec.yml is still being "
            "read; remove bequest again once the trellis is drawn"
        )
        assert app.buffers.value == {} and app.gesturing.value is None

        # a removal that waits for the editor's text, withdrawn
        app.open_path.value = RECIPE_FILE
        app.remove_occurrence((0, "bequest"))
        assert app.gesturing.value["step"] == "flushed"
        app.withdraw_gesture()
        assert app.gesturing.value is None
        assert app.gesture_refusal.value["sentence"] == (
            "trellis.yml: nothing was written. The graph was drawn from an earlier text. "
            "Remove the stage again in the graph now drawn."
        )
    finally:
        app.open_path.value = None
        clear_gesture_state()
        clear_trellis_state()


def test_m_14_a_models_declaration_opened_by_itself_opens_the_model_folder(
    app_state, tmp_path
):
    """AAS, M-D14 ("somehow the trellis view does not work"): the desktop
    application had opened the `declaration/` of the durables model, chosen
    in its dialog, where the Workbench finds no recipe at
    `declaration/spec.yml` and so reads no trellis. The page's first open
    makes the model folder above the tab's folder and opens its recipe, so
    that the trellis is read; a link that still names the `declaration/`
    the window was opened on is accepted, the file named from the model folder."""
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    app = app_state(durables / "declaration")
    try:
        app.open_first()
        assert app.tab_folder.value.root == durables.resolve()
        assert app.open_path.value == "declaration/spec.yml"
        app.on_desktop_open(
            {
                "folder": str(durables / "declaration"),
                "file": "stages/bequest/bequest.bl",
                "line": 1,
            }
        )
        # the request is accepted with the file named from the model folder;
        # the switch to it waits for the editor's answer, which no browser
        # gives here (`_switch_to`), so the request and its place are read
        assert app.desktop_refusal.value is None
        assert app.desktop_pending.value["file"] == "declaration/stages/bequest/bequest.bl"
        assert app.pending_goto.value["path"] == "declaration/stages/bequest/bequest.bl"
    finally:
        clear_trellis_state()


def test_comp_problems_separate_native_errors_from_open_fields_and_keep_source_links(app_state, tmp_path):
    from workbench_support import composition_folder

    path = composition_folder(tmp_path / "problems", repeat=2)
    period = path / "period.yml"
    period.write_text(period.read_text().replace("connectors: [{}]", "connectors: [{S.a: U.typo}]"))
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    try:
        outcome = app.run_trellis()
        assert outcome.shown is not None
        held = outcome.shown
        native = next(item for item in held.selection.diagnostics if item.rule == "endpoint-unresolved")
        refused = next(item for item in app.standing_refusals() if item.sentence == native.message)
        assert refused.severity == "error" and refused.places == (("period.yml", 5),)
        count = trellis.unjoined_count(held)
        # An undrawn graph cannot hide missing inputs from the whole-model query.
        undrawn = dataclasses.replace(held, collection={"graphs": []})
        assert trellis.unjoined_count(undrawn) == count > 0
        _, rendered = solara.render(app.ErrorMark(), handle_error=False)
        try:
            button = rendered.find(v.Html, tag="button", class_="bl-error-mark bl-has-errors").widget
            assert button.attributes["aria-controls"] == "bl-problems-list"
            assert button.attributes["aria-label"] == "Problems: 1 error, 3 to review"
            links = rendered.find(v.Html, tag="button", class_="bl-error-place").widgets
            assert any(link.attributes["data-path"] == "period.yml" for link in links)
            assert rendered.find(v.Html, class_="bl-problem-group bl-problem-unjoined").widget.attributes["data-count"] == str(count)
        finally:
            rendered.close()
    finally:
        clear_trellis_state()


def test_comp_unjoined_model_is_a_warning_and_preserves_the_occurrence_control(app_state, tmp_path, monkeypatch):
    from workbench_support import composition_folder

    path = composition_folder(tmp_path / "open-model", repeat=2)
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    try:
        outcome = app.run_trellis()
        assert outcome.shown is not None
        def no_classification(*args, **kwargs):
            raise AssertionError("Problem source locations need only the current text")
        monkeypatch.setattr(model, "classification", no_classification)
        pair = outcome.shown.selection.pairs[0]
        uses = (pair.writing, pair.reading)
        places = trellis.field_places(app.tab_folder.value, outcome.shown, uses)
        assert places == {pair.writing: ("S.bl", 5), pair.reading: ("T.bl", 2)}
        texts = {str((path / "S.bl").resolve()): "# source comment\n"+(path / "S.bl").read_text()}
        places = trellis.field_places(app.tab_folder.value, outcome.shown, uses, texts)
        assert places == {pair.writing: ("S.bl", 6), pair.reading: ("T.bl", 2)}
        assert not [item for item in app.standing_refusals() if item.severity == "error"]
        _, rendered = solara.render(app.ErrorMark(), handle_error=False)
        try:
            button = rendered.find(v.Html, tag="button", class_="bl-error-mark").widget
            assert "0 errors" in button.attributes["aria-label"]
            assert "to review" in button.attributes["aria-label"]
        finally:
            rendered.close()
    finally:
        clear_trellis_state()


@pytest.mark.parametrize("connector, expected", [
    ("  - S.a: T.b\n  - S.b: T.a\n", (6, 7)),
    ("  - from: S\n    to: T\n    fields:\n      a: b\n      b: a\n", (9, 10)),
])
def test_comp_diagnostic_links_name_each_authored_key_after_unsaved_edits(app_state, tmp_path, monkeypatch, connector, expected):
    from workbench_support import composition_folder

    path = composition_folder(tmp_path / "source-lines", repeat=2, two_fields=True)
    period = path / "period.yml"
    period.write_text(period.read_text().replace("connectors: [{}]\n", "connectors:\n"+connector))
    target = path / "T.bl"
    target.write_text(target.read_text().replace("ℝ₊", "ℝ₊₊"))
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    try:
        outcome = app.run_trellis()
        native = next(d for d in outcome.shown.selection.diagnostics if d.rule == "route-incompatible")
        calls = []
        spans = trellis.written_spans
        def queried(file, addresses, texts=None):
            calls.append(tuple(addresses))
            return spans(file, addresses, texts)
        def scalar(*args, **kwargs):
            raise AssertionError("Native diagnostic origins are resolved together")
        monkeypatch.setattr(trellis, "written_spans", queried)
        monkeypatch.setattr(trellis, "address_place", scalar)
        item = next(d for d in app.standing_refusals() if d.sentence == native.message)
        assert len(calls) == 1 and len(calls[0]) >= len(expected)
        assert len(item.places) == len(expected)
        assert set(item.places) == {("period.yml", line) for line in expected}
        app.open_file("period.yml")
        held = app.buffers.value["period.yml"]
        app.on_change({"path": "period.yml", "text": "# source comment\n"+held["text"],
                       "revision": held["document_revision"]})
        item = next(d for d in app.standing_refusals() if d.sentence == native.message)
        assert len(item.places) == len(expected)
        assert set(item.places) == {("period.yml", line+1) for line in expected}
    finally:
        clear_trellis_state()


def test_comp_an_undrawable_current_trellis_keeps_its_diagnostics_and_recovers(app_state, tmp_path):
    """A refused graph does not replace the current model with an older reading."""
    from workbench_support import composition_folder

    path = composition_folder(tmp_path / "cyclic", repeat=2)
    period = path / "period.yml"
    original = period.read_text()
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    app.view_mode.value = "trellis"
    try:
        previous = app.run_trellis().shown
        assert previous.collection["graphs"] and previous.view_refusal is None
        period.write_text(original.replace("connectors: [{}]", "connectors:\n  - {S.a: T.a}\n  - {T.y: S.x}"))
        outcome = app.run_trellis()
        held = outcome.shown
        assert outcome.refusal is None and held is app.trellis_shown.value
        assert held is not previous and held.number > previous.number
        assert held.view_refusal.rule == "period-join-cycle"
        assert held.collection == {"graphs": []} and held.layers == {}
        assert not app._trellis_stale() and not app.drawing.value
        assert trellis.unjoined_count(held) > 0
        cycle = next(d for d in held.selection.diagnostics if d.rule == "authored-cycle")
        problem = next(d for d in app.standing_refusals() if d.sentence == cycle.message)
        assert set(problem.places) == {("period.yml", 6), ("period.yml", 7)}
        assert app.run_trellis().shown is held
        assert held.view_refusal.rule == "period-join-cycle"
        _, rendered = solara.render(app.ViewRegion(None, None), handle_error=False)
        try:
            assert any("Graph unavailable. See Problems." in drawn_text(node)
                       for node in rendered.find(v.Html, class_="bl-empty").widgets)
            assert rendered.find(v.Html, tag="button", class_="bl-error-mark bl-has-errors").widgets
        finally:
            rendered.close()
        period.write_text(original)
        repaired = app.run_trellis()
        assert repaired.refusal is None and repaired.shown is app.trellis_shown.value
        assert repaired.shown is not held and repaired.shown.number > held.number
        assert repaired.shown.view_refusal is None and repaired.shown.collection["graphs"]
        assert not any(d.rule in ("authored-cycle", "selected-cycle") for d in repaired.shown.selection.diagnostics)
        assert not any(d.sentence == cycle.message for d in app.standing_refusals())
    finally:
        clear_trellis_state()
