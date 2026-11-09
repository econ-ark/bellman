"""The acceptance file of unit D3 of the implementation plan of Model
Interface 0.9, the Workbench's one diagnostic record and the places that
read it: one test for each of the six acceptance items of the plan's §2 D3,
named `test_item_<n>_<claim>`. Unit D5 adds the test of its item 4, the Rule
link with the catalogue's entry of the imported Bellman,
`test_d5_item_4_<claim>`.

The record is `model.Diagnostic`, made by the one conversion
`model.diagnostic_of` from what the package raises or records. The editor's
underline (`app.editor_record`), the list under the error mark
(`app.standing_refusals`, drawn by `app.ErrorMark`), Details
(`app.RefusalBox` in the stage view and `app.TrellisRefusal` in the trellis
view, one head for both), the refusing node of a refused graph
(`model.piece`) and the rows of a refused binding
(`trellis.refused_bindings`) read it. Each
test asserts on the record's parts and never on the wording of a sentence,
so that the rewriting of the sentences in unit D4 changes none of them.
"""

from __future__ import annotations

import importlib.metadata
import logging
import socket
import sys
import time
import types
from pathlib import Path

import ipyvuetify as v
import solara
from workbench_support import (
    CONS,
    PENSIONS_RECIPE,
    PENSIONS_WORKING_YEARS,
    RECIPE_FILE,
    TERMINAL_CALIBRATION,
    active_line,
    applied,
    clear_trellis_state,
    composition_folder,
    drawn_text,
    error_lines,
    init_repository,
    new_tab,
    open_cons,
    pensions_copy,
    replace_in_editor,
    toggle_errors,
    wait_until,
)

from bellman import refusal_catalogue
from bellman.refusals import Location
from bellman_workbench import app, model, recipe, trellis

RECIPE = recipe.Source("recipe", RECIPE_FILE)
ENTREPRENEUR = "declaration/stages/entrepreneur_death/entrepreneur_death.bl"
# the value line of the consumption stage, and the line that reads the
# savings `a`, a state of the block's input perch, directly
VALUE_LINE = "    V        = 𝑢(c) + V[>]          :: [id=value]"
STATE_READ = "    V        = 𝑢(c) + V[>] + a      :: [id=value]"
# the policy line of the consumption stage, and the line that names a field
# the stage does not declare
POLICY_LINE = "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality]"
NAME_READ = "    c      = q[>]                    :: [id=cons_choice]"
# the lifecycle registry's settings of the consumption stage and its addition
CONS_SETTINGS = "declaration/settings/cons.yml"
CONS_ADDITION = "declaration/stages/cons/methods.bl"
# those settings with the lower bound of the savings grid outside the set
# `ℝ₊` the addition declares for it
NEGATIVE_BOUND = (
    "settings:\n  n_a: 30\n  a_min: -1.0\n  a_max: 20.0\n  n_m: 30\n  m_min: 0.01\n"
    "  m_max: 20.0\n"
)
# the pension model's contribution stage, which periods 4 to 6 hold, and the
# three lines the UX simulation's post-doc first typed in place of its lines
# `w_c` and `adc_c`, for which the package raises a KeyError where a refusal
# was due (defect 18 of the UX simulation)
CONTRIBUTION = "declaration/stages/contribution/contribution.bl"
V_RATE_LINES = (
    "    v_rate = (0, v_1, v_2, v_3, v_4, v_5)[v] :: [id=contribution_rate]\n"
    "    w_c = a_d + (1 - v_S - v_rate)*y_d :: [id=take_home]\n"
    "    adc_c = adc_d + (((1 - o)*v_E + v_rate)*y_d, (v_E + v_S + v_rate)*y_d)[plan_d]"
    " :: [id=contributions]\n"
)


def written(path, old: str, new: str) -> str:
    """The text of the file `path` with its one occurrence of `old`
    replaced by `new`, written back; answers the text before."""
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    path.write_text(text.replace(old, new), encoding="utf-8")
    return text


def line_of(path, start: str) -> int:
    """The number, counted from one, of the first line of the file `path`
    that begins with `start`, its indentation left out."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return 1 + next(n for n, line in enumerate(lines) if line.strip().startswith(start))


def details_head(element) -> str:
    """The text of the head of a refusal's box in Details."""
    _, rendered = solara.render(element, handle_error=False)
    try:
        return drawn_text(rendered.find(v.Html, class_="bl-refusal-rule").widget)
    finally:
        rendered.close()


def rendered_lines() -> list[dict]:
    """The lines of the list under the error mark as `ErrorMark` draws
    them, each `{"sentence", "buttons", "facts"}`: its sentence; each
    source button as `(class, path, line, text)`; and the text of each fact
    by its class."""
    app.errors_open.value = True
    _, rendered = solara.render(app.ErrorMark(), handle_error=False)
    try:
        found = []
        for line in rendered.find(v.Html, class_="bl-error-line").widgets:
            buttons, facts = [], {}
            for child in line.children[1:]:
                if child.tag == "button":
                    attributes = child.attributes or {}
                    buttons.append((child.class_, attributes.get("data-path"),
                                    attributes.get("data-line"), drawn_text(child)))
                elif child.class_ == "bl-error-facts":
                    for fact in child.children:
                        if isinstance(fact, v.Html):
                            facts[fact.class_] = drawn_text(fact)
            found.append({"sentence": drawn_text(line.children[0]), "buttons": buttons,
                          "facts": facts})
        return found
    finally:
        rendered.close()
        app.errors_open.value = False


def drawn_line(sentence: str) -> dict:
    """The one drawn line of the list whose sentence is `sentence`."""
    (line,) = [line for line in rendered_lines() if line["sentence"] == sentence]
    return line


def settled_lines(tab, seconds: float = 2.0) -> list:
    """The lines of the list under the error mark in the browser once they
    have stood unchanged for `seconds`, since the trellis's reading of an
    edited text answers after the loop's."""
    held = {"lines": None, "since": time.monotonic()}

    def unchanged():
        lines = error_lines(tab)
        if lines != held["lines"]:
            held.update(lines=lines, since=time.monotonic())
            return None
        return lines if time.monotonic() - held["since"] >= seconds else None

    lines, _ = wait_until(unchanged, 60.0, "the list unchanged")
    return lines


def focused(locator) -> bool:
    """Whether the element `locator` finds takes the focus and holds it."""
    return locator.evaluate("element => { element.focus(); return element === document.activeElement; }")


def test_item_1_one_refusal_reads_the_same_in_the_editor_the_list_details_and_the_binding(
    app_state, scratch_lifecycle, cagetti_folder
):
    """A backward-state error of the lifecycle registry's consumption stage,
    its value line reading the savings `a` directly: the loop's one record
    carries the rule, the range, the action and the three occurrences of
    the file; the editor's record, the line of the list and the box in
    Details read that record; the trellis's reading of the same text, which
    binds the three occurrences, gives a record of the same rule and range
    listing them, and the list holds one line for both. The forward graph
    the construction holds refused on `entrepreneur_death.bl`: the loop's
    one record is of the kind `held` with its direction; the editor's
    record, the line of the list, the box in Details and the refusing
    node's piece name the same rule, range and direction."""
    written(scratch_lifecycle / CONS, VALUE_LINE, STATE_READ)
    app_state(scratch_lifecycle)
    app.source.value = RECIPE
    try:
        app.open_file(CONS)
        outcome = app.run_loop()
        (refusal,) = outcome.refusals
        assert (refusal.kind, refusal.operation, refusal.rule) == (
            "refusal", "elaborate", "input-perch-state")
        range_ = (refusal.line, refusal.column, refusal.end_line, refusal.end_column)
        assert range_ == (21, 5, 21, 50)
        assert refusal.address == "cntn_to_dcsn.value" and refusal.write
        assert refusal.occurrences == ((0, "cons"), (1, "cons"), (2, "cons"))
        underline = app.editor_record(refusal)
        assert (underline["line"], underline["column"], underline["end_line"],
                underline["end_column"]) == range_
        assert (underline["rule"], underline["severity"]) == ("input-perch-state", "error")
        read = app.run_trellis()
        assert read.shown is None
        assert (read.refusal.rule, read.refusal.line, read.refusal.column,
                read.refusal.end_line, read.refusal.end_column) == ("input-perch-state", *range_)
        assert read.refusal.occurrences == refusal.occurrences
        (row,) = [row for row in app.standing_refusals() if row.rule == "input-perch-state"]
        assert (row.file, row.line, row.severity, row.category) == (
            CONS, 21, "error", "declaration")
        assert row.occurrences == refusal.occurrences
        assert (row.diagnostic.message, row.diagnostic.write) == (refusal.message, refusal.write)
        head = details_head(app.RefusalBox(CONS, refusal))
        assert head.startswith(f"refused at {CONS}:21:5") and "rule input-perch-state" in head
    finally:
        clear_trellis_state()

    # the second model, the tab's state cleared as at a test's end
    app.open_path.value, app.buffers.value, app.results.value = None, {}, {}
    app.shown.value = None
    app_state(cagetti_folder)
    app.source.value = None
    app.open_file(ENTREPRENEUR)
    outcome = app.run_loop()
    (held,) = outcome.refusals
    assert (held.kind, held.direction, held.rule) == ("held", "forward", "not-constructed")
    assert (held.line, held.column, held.end_line, held.end_column) == (17, 1, 17, 165)
    underline = app.editor_record(held)
    assert (underline["line"], underline["column"], underline["end_column"], underline["rule"],
            underline["severity"]) == (17, 1, 165, "not-constructed", "warning")
    (row,) = [row for row in app.standing_refusals() if row.rule == "not-constructed"]
    assert (row.file, row.line, row.diagnostic.direction) == (ENTREPRENEUR, 17, "forward")
    head = details_head(app.RefusalBox(ENTREPRENEUR, held))
    assert head.startswith(f"refused at {ENTREPRENEUR}:17:1")
    assert head.endswith("forward builders graph") and "not constructed" in head
    piece = model.piece(app.shown.value.stage, "forward", "forward:refused")
    assert (piece.attributes["line"], piece.attributes["column"], piece.attributes["end_column"],
            piece.attributes["rule"]) == (17, 1, 165, "not-constructed")


def test_item_2_one_problem_at_three_occurrences_is_one_row_and_two_problems_are_two(
    app_state, scratch_lifecycle, tmp_path, caplog
):
    """The lifecycle registry's consumption stage stands at three periods: a
    refusal of its text, read by the trellis, is one line of the list with
    the three occurrences and the file's line. The terminal discount factor
    outside its set and a bound of the savings grid outside its declared
    set are two refusals of two bindings: two lines, each under its own
    verb, at its own occurrence, with source links of its own; every entry
    the page's log receives while the trellis binds names the verb and the
    recipe read, and no entry names no file. A trellis
    file writing `periods` twice is one refusal of the source's reading,
    which the trellis's reading and the consumption stage bound through the
    source both meet while that stage is open: one line, each record with
    the revision of the file as its reading read it. In the pension model,
    an exception of no refusal class, which the loop and the trellis's
    construction both meet in the contribution stage's text, is one line in
    that stage file, with the three occurrences the factory's note names,
    and the Details box of the trellis view names the operation that
    stopped and the log entry, as the stage view's box does."""
    stage = scratch_lifecycle / CONS
    before = written(stage, VALUE_LINE, STATE_READ)
    app_state(scratch_lifecycle)
    app.source.value = RECIPE
    try:
        read = app.run_trellis()
        assert read.shown is None and read.refusal.rule == "input-perch-state"
        (row,) = [row for row in app.standing_refusals() if row.rule == "input-perch-state"]
        assert row.occurrences == ((0, "cons"), (1, "cons"), (2, "cons"))
        assert (row.file, row.line) == (CONS, 21)

        stage.write_text(before, encoding="utf-8")
        terminal = scratch_lifecycle / "declaration/calibration/terminal.yml"
        terminal.write_text(TERMINAL_CALIBRATION.replace("0.9", "1.5"), encoding="utf-8")
        (scratch_lifecycle / CONS_SETTINGS).write_text(NEGATIVE_BOUND, encoding="utf-8")
        with caplog.at_level(logging.ERROR, logger="bellman_workbench.model"):
            read = app.run_trellis()
        assert read.shown is not None and set(read.shown.binding.failed) == {"calibrate", "configure"}
        # an entry the binding wrote, for an exception of no refusal class the
        # package raised, names the verb and the recipe read, never no file
        recipe_path = (app.tab_folder.value.root / RECIPE_FILE).resolve()
        entries = [record for record in caplog.records if record.name == "bellman_workbench.model"]
        assert all((record.args[1], Path(record.args[2]).resolve()) == ("calibrate", recipe_path)
                   for record in entries)
        rows = {row.diagnostic.operation: row
                for row in app.standing_refusals() if row.category == "binding"}
        assert set(rows) == {"calibrate", "configure"}
        calibrate, configure = rows["calibrate"], rows["configure"]
        assert calibrate.occurrences == ((0, "disc"),) and configure.occurrences == ((0, "cons"),)
        assert ("declaration/calibration/terminal.yml", 3) in calibrate.places
        assert (configure.file, configure.line) == (
            CONS_ADDITION, line_of(scratch_lifecycle / CONS_ADDITION, "a_min"))
        assert not set(calibrate.places) & set(configure.places)

        trellis_file = scratch_lifecycle / "declaration/trellis.yml"
        text = trellis_file.read_text(encoding="utf-8")
        trellis_file.write_text(text + "periods: []\n", encoding="utf-8")
        read = app.run_trellis()
        assert read.shown is None and read.refusal.operation == "read"
        app.open_file(CONS)
        app.run_loop()
        observed = app.shown.value.refusal
        assert (observed.rule, observed.line) == (read.refusal.rule, read.refusal.line)
        assert observed.revision == read.files[str(trellis_file.resolve())]
        (row,) = [row for row in app.standing_refusals() if row.rule == read.refusal.rule]
        assert (row.file, row.line) == ("declaration/trellis.yml", len(text.splitlines()) + 1)
    finally:
        clear_trellis_state()

    # the second model, the tab's state cleared as at a test's end
    app.open_path.value, app.buffers.value, app.results.value = None, {}, {}
    app.shown.value = None
    copy = pensions_copy(tmp_path / "models" / "durables", PENSIONS_WORKING_YEARS)
    stage = copy / CONTRIBUTION
    lines = stage.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(n for n, line in enumerate(lines) if line.startswith("    w_c "))
    assert lines[at + 1].startswith("    adc_c ")
    stage.write_text("".join(lines[:at]) + V_RATE_LINES + "".join(lines[at + 2:]),
                     encoding="utf-8")
    app_state(copy)
    app.source.value = recipe.Source("recipe", PENSIONS_RECIPE)
    try:
        app.open_file(CONTRIBUTION)
        (loop,) = app.run_loop().refusals
        read = app.run_trellis()
        occurrences = ((4, "contribution"), (5, "contribution"), (6, "contribution"))
        assert (loop.kind, loop.file, loop.occurrences) == ("internal", CONTRIBUTION, occurrences)
        found = read.refusal
        assert (found.kind, found.operation, found.occurrences) == (
            "internal", "elaborate", occurrences)
        assert recipe.relative(app.tab_folder.value, found.file) == CONTRIBUTION
        (row,) = [row for row in app.standing_refusals()
                  if row.diagnostic is not None and row.diagnostic.kind == "internal"]
        assert (row.file, row.line, row.occurrences) == (CONTRIBUTION, None, occurrences)
        head = details_head(app.TrellisRefusal(found))
        assert head == f"elaborate stopped in {CONTRIBUTION} · logged as {found.entry}"
    finally:
        clear_trellis_state()


def test_item_3_an_internal_failure_a_dependent_finding_and_the_entries_of_a_cycle(
    app_state, scratch_folder, tmp_path, monkeypatch, caplog
):
    """An exception of no class of the package's refusals, raised by the
    elaboration of an edited buffer: the loop's one record is an internal
    failure under the operation `elaborate`, with no rule, no position and
    the identifier of the entry of the page's log that holds its
    traceback; the list and Details name the operation and the entry, and
    the list gives no Rule link; the view keeps the drawing of the earlier
    text. Raised after the elaboration, by the binding, the exception is
    the loop's one record under the operation `bind`, and the view keeps
    the drawing. A period template repeated over two periods whose
    authored connectors form a cycle: the findings of the routes that rest
    on the cycle are left out of the list, the cycle, which the package
    records once per period, is one line listing both periods and linking
    both connectors, and the connectors' entries are marked in the editor
    of the period file. Where a gesture
    of the Workbench typed the cycle, the mark at the typed line carries
    the action that restores the text before it, after which the trellis
    is drawn again."""
    app_state(scratch_folder)
    app.source.value = None
    app.open_file(CONS)
    app.run_loop()
    drawn = app.shown.value
    assert drawn is not None

    saved = (scratch_folder / CONS).read_text()
    held = app.buffers.value[CONS]
    edited = held["text"] + "\n# keep this edit after a failed save\n"
    event = {"path": CONS, "text": edited, "revision": held["document_revision"]}
    with monkeypatch.context() as patch:
        def denied(*args, **kwargs):
            raise PermissionError(13, "Permission denied")

        patch.setattr(model, "save_file", denied)
        app.on_save(event)
    (save_row,) = [row for row in app.standing_refusals()
                   if row.diagnostic is not None and row.diagnostic.operation == "save"]
    assert save_row.diagnostic.kind == "application" and save_row.rule is None
    assert save_row.line is None and "Save again" in save_row.diagnostic.write
    assert app.buffers.value[CONS]["text"] == edited
    assert (scratch_folder / CONS).read_text() == saved
    app.on_save(event)
    assert app.gesture_refusal.value is None
    assert (scratch_folder / CONS).read_text() == edited
    app.on_refused({"sentence": "the graph backward was not laid out: test failure"})
    (layout_row,) = [row for row in app.standing_refusals()
                     if row.diagnostic is not None and row.diagnostic.operation == "layout"]
    assert layout_row.rule is None and layout_row.diagnostic.write
    app.on_processed({})
    assert app.layout_refusal.value is None
    app.on_desktop_open({"file": "../outside.bl", "line": 1})
    (desktop_row,) = [row for row in app.standing_refusals()
                      if row.diagnostic is not None
                      and row.diagnostic.operation == "open desktop link"]
    assert desktop_row.diagnostic.kind == "application" and desktop_row.rule is None
    assert desktop_row.line is None and "open the link again" in desktop_row.diagnostic.write
    app.on_desktop_open({"file": CONS, "line": 1})
    assert app.desktop_refusal.value is None
    with monkeypatch.context() as patch:
        patch.setattr(app.desktop, "open_in_editor", denied)
        app.open_external_editor(CONS, 1)
        assert app.desktop_refusal.value["diagnostic"].operation == "open external editor"
        patch.setattr(app.desktop, "open_in_editor", lambda *args: None)
        app.open_external_editor(CONS, 1)
        assert app.desktop_refusal.value is None
        patch.setattr(model, "git_push", lambda folder: model.GitResult(False, "remote refused"))
        app.git_task(kind="push")
        wait_until(lambda: not app.git_task.pending, 10.0, "the refused Git command")
        assert app.git_task.finished, app.git_task.exception
        (git_row,) = [row for row in app.standing_refusals()
                     if row.diagnostic is not None and row.diagnostic.operation == "git push"]
        assert git_row.diagnostic.kind == "application" and git_row.rule is None
        assert git_row.line is None and "remote refused" in git_row.diagnostic.message
        assert git_row.diagnostic.write
        patch.setattr(model, "git_push", lambda folder: model.GitResult(True, "pushed"))
        app.git_task(kind="push")
        wait_until(lambda: not app.git_task.pending, 10.0, "the successful Git command")
        assert app.git_answer.value["diagnostic"] is None
    assert app.shown.value is drawn

    def raising(text, origin):
        raise KeyError("unresolved semantic input 'm' at policy")

    monkeypatch.setattr(model, "elaborate_text", raising)
    held = app.buffers.value[CONS]
    with caplog.at_level(logging.ERROR, logger="bellman_workbench.model"):
        app.on_change({"path": CONS, "text": held["text"] + "\n",
                       "revision": held["document_revision"]})
        outcome = app.run_loop()
    (failure,) = outcome.refusals
    assert (failure.kind, failure.operation, failure.rule, failure.line) == (
        "internal", "elaborate", None, None)
    assert failure.entry and failure.entry.startswith("exception ")
    (logged,) = [record for record in caplog.records if record.name == "bellman_workbench.model"]
    assert failure.entry in logged.getMessage() and isinstance(logged.exc_info[1], KeyError)
    assert app.shown.value is drawn
    (row,) = [row for row in app.standing_refusals() if row.diagnostic is failure]
    assert row.rule is None
    facts = drawn_line(row.sentence)["facts"]
    assert "bl-error-rule" not in facts
    assert facts["bl-error-operation"] == "elaborate stopped"
    assert facts["bl-error-entry"] == f"logged as {failure.entry}"
    assert facts["bl-error-severity"] == "error"
    head = details_head(app.RefusalBox(CONS, failure))
    assert head == f"elaborate stopped in {CONS} · logged as {failure.entry}"
    monkeypatch.undo()

    def unbound(stage, found):
        raise AttributeError("an attribute the binding reads")

    monkeypatch.setattr(recipe, "bind_occurrence", unbound)
    held = app.buffers.value[CONS]
    app.on_change({"path": CONS, "text": held["text"] + "\n",
                   "revision": held["document_revision"]})
    (failure,) = app.run_loop().refusals
    assert (failure.kind, failure.operation, failure.rule, failure.line) == (
        "internal", "bind", None, None)
    assert failure.entry and app.shown.value is drawn
    monkeypatch.undo()

    path = composition_folder(tmp_path / "cyclic", repeat=2)
    period = path / "period.yml"
    original = period.read_text(encoding="utf-8")
    cyclic = original.replace("connectors: [{}]", "connectors:\n  - {S.a: T.a}\n  - {T.y: S.x}")
    period.write_text(cyclic, encoding="utf-8")
    app.open_path.value, app.buffers.value, app.results.value = None, {}, {}
    app.shown.value = None
    app_state(path)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    app.view_mode.value = "trellis"
    try:
        shown = app.run_trellis().shown
        assert shown is not None and shown.view_refusal.rule == "period-join-cycle"
        report = trellis.connection_report(shown.trellis, selection=shown.selection)
        cycles = [found for found in report.diagnostics if found.rule == "authored-cycle"]
        assert len(cycles) == 2
        dependent = [found for found in report.diagnostics
                     if found.depends_on in {cycle.address for cycle in cycles}]
        assert dependent
        rows = app.standing_refusals()
        (cycle_row,) = [row for row in rows if row.rule == "authored-cycle"]
        assert set(cycle_row.places) == {("period.yml", 6), ("period.yml", 7)}
        assert cycle_row.occurrences == ((0, None), (1, None))
        assert drawn_line(cycle_row.sentence)["facts"]["bl-error-occurrences"] == "periods 0–1"
        assert not {found.rule for found in dependent} & {row.rule for row in rows}
        app.open_file("period.yml")
        marks = app.trellis_diagnostics("period.yml")
        assert sorted(mark["line"] for mark in marks if mark["rule"] == "authored-cycle") == [6, 7]
        # the cycle typed by a gesture of the Workbench
        app.gesture_made.value = {"path": "period.yml", "before": original, "after": cyclic}
        (record,) = [mark for mark in app.trellis_diagnostics("period.yml") if "action" in mark]
        assert (record["action"]["name"], record["rule"]) == (app.TAKE_THE_LINE_OUT,
                                                              "period-join-cycle")
        edits = [model.Replacement(**edit) for edit in record["action"]["edits"]]
        assert applied(cyclic, edits) == original
        (typed,) = [row for row in app.standing_refusals() if row.rule == "period-join-cycle"]
        assert (typed.file, typed.line) == ("period.yml", record["line"])
        period.write_text(original, encoding="utf-8")
        held = app.buffers.value["period.yml"]
        app.on_change({"path": "period.yml", "text": original,
                       "revision": held["document_revision"]})
        app.gesture_made.value = None
        repaired = app.run_trellis()
        assert repaired.shown.view_refusal is None and repaired.shown.collection["graphs"]
        assert not {"authored-cycle", "period-join-cycle"} & {
            row.rule for row in app.standing_refusals()}
    finally:
        app.gesture_made.value = None
        clear_trellis_state()


def test_item_4_a_malformed_trellis_file_a_duplicate_key_and_a_setting_outside_its_set(
    app_state, scratch_lifecycle, tmp_path
):
    """A standalone file tagged `!trellis` whose contents do not read is a
    source of the folder, and its refusal stands in the list with the file;
    a YAML file beside it without the tag is none. A trellis file writing
    `periods` twice is refused at the second key, with the first as a
    related location. A setting's value outside the set its declaration in
    the addition names is refused at that declaration: the list's line
    links the declaration as its place and the settings file's key as a
    related location, each button opening its own line."""
    standalone = tmp_path / "standalone"
    standalone.mkdir()
    (standalone / "model.yml").write_text("!trellis\nperiods: [\n", encoding="utf-8")
    (standalone / "notes.yml").write_text("periods: []\n", encoding="utf-8")
    init_repository(standalone)
    app_state(standalone)
    assert [source.path for source in recipe.model_sources(app.tab_folder.value)] == ["model.yml"]
    app.source.value = recipe.Source("trellis", "model.yml")
    try:
        outcome = app.run_trellis()
        assert outcome.shown is None
        assert (outcome.refusal.kind, outcome.refusal.operation) == ("refusal", "read")
        (row,) = [row for row in app.standing_refusals() if row.diagnostic is not None]
        assert row.file == "model.yml" and row.rule == outcome.refusal.rule
    finally:
        clear_trellis_state()

    twice = composition_folder(tmp_path / "twice")
    (twice / "trellis.yml").write_text(
        "!trellis\nperiods:\n  - {template: period.yml, repeat: 1}\nperiods: []\n"
        "inter_connectors: []\n",
        encoding="utf-8",
    )
    app_state(twice)
    app.source.value = recipe.Source("trellis", "trellis.yml")
    try:
        outcome = app.run_trellis()
        assert (outcome.refusal.line, outcome.refusal.column) == (4, 1)
        (row,) = [row for row in app.standing_refusals() if row.rule == outcome.refusal.rule]
        assert (row.file, row.line) == ("trellis.yml", 4)
        ((role, file, line),) = [(held.role, held.file, held.line) for held in row.related]
        assert (role, file, line) == ("original declaration", "trellis.yml", 2)
    finally:
        clear_trellis_state()

    settings = scratch_lifecycle / CONS_SETTINGS
    settings.write_text(NEGATIVE_BOUND, encoding="utf-8")
    app_state(scratch_lifecycle)
    app.source.value = RECIPE
    try:
        outcome = app.run_trellis()
        assert outcome.shown.binding.failed["configure"].rule == "setting-outside-set"
        (row,) = [row for row in app.standing_refusals() if row.rule == "setting-outside-set"]
        declared = line_of(scratch_lifecycle / CONS_ADDITION, "a_min")
        key = line_of(settings, "a_min:")
        assert (row.file, row.line) == (CONS_ADDITION, declared)
        ((role, file, line),) = [(held.role, held.file, held.line) for held in row.related]
        assert (role, file, line) == ("rejected setting", CONS_SETTINGS, key)
        buttons = drawn_line(row.sentence)["buttons"]
        assert buttons[0][1:3] == (CONS_ADDITION, str(declared))
        assert ("bl-error-place bl-error-related", CONS_SETTINGS, str(key),
                f"rejected setting: {CONS_SETTINGS}:{key}") in buttons
    finally:
        clear_trellis_state()


def test_item_5_severity_in_text_and_the_keyboard_reach_the_rows_the_links_and_the_rule(
    browser, server_on, scratch_folder
):
    """In the browser, the policy line of `cons.bl` edited to name a field
    the stage does not declare: every line of the list under the error mark
    prints its severity in text; the refused line takes the focus from the
    keyboard, and Enter on it opens the file at the refused line; Tab moves
    the focus to the line's source button, and Enter on the button opens
    the same line; the Rule link, a link to the rule's entry on the
    Refusals page, takes the focus too. The refusal after a character
    outside the basic Unicode plane is underlined at the refused text by
    the existing test of `test_page.py`,
    `test_a1_item_1_the_refusal_after_an_astral_character_is_underlined_at_the_refused_text`."""
    context, tab = new_tab(browser)
    try:
        open_cons(tab, server_on(scratch_folder))
        component = Path(app.__file__).with_name("editor.vue").read_text().split("<script>")[1].split("</script>")[0]
        tab.evaluate("""source => {
            const module = {exports: {}};
            new Function("module", source)(module);
            const component = module.exports;
            let text = "old text", marks = [];
            const context = {appliedPath: "stage.bl", appliedRevision: 1,
                handle: {getDoc: () => text, setDiagnostics: value => {marks = value;}},
                change: () => {}, ...component.methods};
            const record = {line: 2, column: 1, end_line: 2, end_column: 2,
                            message: "unknown name", revision: "old digest"};
            const previous = {path: "stage.bl", document_revision: 1, text, items: [record]};
            const receive = value => component.watch.diagnostics.call(context, value);
            const check = condition => {if (!condition) throw Error("diagnostics name another document");};
            receive(previous); check(marks.length === 1);
            text = "new text";
            context.sendChange({path: "stage.bl", revision: 1, text});
            receive(previous); check(marks.length === 0);
            const fresh = {...previous, text, items: [{...record, revision: "new digest"}]};
            receive(fresh); check(marks.length === 1);
            text = "saved before the typing pause";
            receive({...fresh, text}); check(marks.length === 1);
            receive({...fresh, path: "other.bl", text}); check(marks.length === 0);
            receive({...fresh, document_revision: 0, text}); check(marks.length === 0);
        }""", component)
        replace_in_editor(tab, POLICY_LINE.strip(), NAME_READ.strip())
        wait_until(lambda: any(line == 30 for _, _, line in error_lines(tab)), 30.0,
                   "the refusal at line 30 in the list")
        settled_lines(tab)
        # the editor's cursor moved away from the refused line
        tab.locator(".cm-content").click()
        tab.keyboard.press("ControlOrMeta+Home")
        wait_until(lambda: active_line(tab) == 1, 10.0, "the editor at its first line")
        if not tab.locator(".bl-error-list").is_visible():
            toggle_errors(tab)
        lines = tab.locator(".bl-error-list .bl-error-line")
        severities = tab.locator(".bl-error-list .bl-error-line .bl-error-severity")
        assert lines.count() >= 1 and severities.count() == lines.count()
        assert set(severities.all_text_contents()) <= {"error", "warning"}
        refused = '.bl-error-list .bl-error-line:has(.bl-error-place[data-line="30"])'
        line = tab.locator(refused).first
        wait_until(lambda: focused(line), 10.0, "the refused line holding the focus")
        tab.keyboard.press("Enter")
        wait_until(lambda: active_line(tab) == 30, 10.0, "the editor at the refused line")
        if not tab.locator(".bl-error-list").is_visible():
            toggle_errors(tab)
        wait_until(lambda: focused(line), 10.0, "the refused line holding the focus again")
        tab.keyboard.press("Tab")
        assert tab.evaluate("() => document.activeElement.className") == "bl-error-place"
        assert tab.evaluate("() => document.activeElement.dataset.line") == "30"
        tab.keyboard.press("Enter")
        wait_until(lambda: active_line(tab) == 30, 10.0, "the editor at the refused line")
        if not tab.locator(".bl-error-list").is_visible():
            toggle_errors(tab)
        link = tab.locator(refused).first.locator("a.bl-error-rule")
        assert link.get_attribute("href").endswith("/reference/refusals/#name-in-scope")
        assert link.text_content() == "name-in-scope"
        wait_until(lambda: focused(link), 10.0, "the Rule link holding the focus")
        marks = tab.locator(".cm-lintRange-error, .cm-lintPoint-error")
        wait_until(lambda: marks.count() > 0, 10.0, "the current refusal underlined")
        tab.locator(".cm-content").click()
        tab.keyboard.press("ControlOrMeta+Home")
        tab.keyboard.insert_text("# a new first line\n")
        assert marks.count() == 0
        tab.keyboard.press("ControlOrMeta+s")
        wait_until(lambda: marks.count() > 0, 10.0, "the newly saved text underlined")
        wait_until(lambda: any(line == 31 for _, _, line in error_lines(tab)), 10.0,
                   "the refusal at its new line")
    finally:
        context.close()


def test_item_6_a_stale_mark_a_late_result_the_text_checked_and_the_copy(
    app_state, scratch_folder, monkeypatch
):
    """With a refused policy line saved in `cons.bl`: the loop's line of
    the list is marked stale once the buffer holds a newer revision than
    the one the loop answered; a result the loop finishes after a newer
    revision was given is dropped, the recorded revision unchanged; the
    trellis's reading of the file on disk while the buffer holds edits
    gives a line marked `checked on disk`, whose places name the file and
    no line of the changed text; and the copy of that line gives the rule,
    the two package versions, the sentence and the model-relative places,
    and no absolute path."""
    stage = scratch_folder / CONS
    written(stage, POLICY_LINE, NAME_READ)
    app_state(scratch_folder)
    app.source.value = RECIPE
    try:
        app.open_file(CONS)
        outcome = app.run_loop()
        (refusal,) = outcome.refusals
        assert refusal.rule == "name-in-scope" and refusal.revision == outcome.digests["text"]
        (row,) = [row for row in app.standing_refusals() if row.rule == "name-in-scope"]
        assert (row.line, row.stale, row.checked) == (30, False, None)
        held = app.buffers.value[CONS]
        app.on_change({"path": CONS, "text": held["text"] + "\n",
                       "revision": held["document_revision"]})
        (row,) = [row for row in app.standing_refusals() if row.rule == "name-in-scope"]
        assert row.stale and row.line is None
        assert drawn_line(row.sentence)["facts"]["bl-error-stale"] == "stale"
        assert drawn_line(row.sentence)["buttons"][0][:3] == ("bl-error-file", CONS, None)
        related = Location("original declaration", RECIPE_FILE, 8, 1, 8, 7)
        preserved = app._row(refusal._replace(related=(related,)), CONS, 30,
                             outcome.made, stale=True,
                             checked_files={app._resolved(RECIPE_FILE):
                                            app._digest((scratch_folder / RECIPE_FILE).read_text())})
        assert preserved.line is None and preserved.related == (related,)
        unknown = app._row(refusal._replace(related=(related,)), CONS, 30, outcome.made)
        assert unknown.related[0].line is None
        buffers = app.buffers.value
        checked_text = "the checked related source"
        checked_files = {app._resolved(RECIPE_FILE): app._digest(checked_text)}
        try:
            app.buffers.value = {**buffers, RECIPE_FILE: {
                "text": checked_text, "digest": app._digest("earlier disk text")}}
            current = app._row(refusal._replace(related=(related,)), CONS, 30,
                               outcome.made, checked_files=checked_files)
            assert current.related == (related,)
            changed_text = "the related source edited and saved"
            app.buffers.value = {**buffers, RECIPE_FILE: {
                "text": changed_text, "digest": app._digest(changed_text)}}
            changed = app._row(refusal._replace(related=(related,)), CONS, 30,
                               outcome.made, checked_files=checked_files)
            assert changed.related == (related._replace(
                line=None, column=None, end_line=None, end_column=None),)
        finally:
            app.buffers.value = buffers

        elaborate = app.elaborate

        def moving(path, text, revision):
            # the elaboration answers once the buffer has a newer revision
            result = elaborate(path, text, revision)
            later = app.buffers.value[path]
            app.on_change({"path": path, "text": later["text"] + "\n# later",
                           "revision": later["document_revision"]})
            return result

        monkeypatch.setattr(app, "elaborate", moving)
        recorded = app.results.value[CONS]["revision"]
        late = app.run_loop()
        assert late.revision > recorded and app.results.value[CONS]["revision"] == recorded
        monkeypatch.setattr(app, "elaborate", elaborate)

        read = app.run_trellis()
        assert read.shown is None and read.refusal.rule == "name-in-scope"
        (disk,) = [row for row in app.standing_refusals() if row.checked == "disk"]
        assert (disk.rule, disk.file, disk.line) == ("name-in-scope", CONS, None)
        assert all(line is None for _, line in disk.places)
        assert disk.occurrences and all(key == "cons" for _, key in disk.occurrences)
        drawn = drawn_line(disk.sentence)
        assert drawn["facts"]["bl-error-checked"] == "checked on disk"
        assert drawn["buttons"][0][:3] == ("bl-error-file", CONS, None)
        copied = app.problem_text(disk)
        first, versions, *rest = copied.splitlines()
        assert first == "rule: name-in-scope"
        assert versions.startswith("bellman ") and ", bellman-workbench " in versions
        assert disk.sentence in copied and f"at: {CONS}" in rest
        assert str(scratch_folder) not in copied and "/private/" not in copied
    finally:
        clear_trellis_state()


def test_d5_item_4_the_rule_link_shows_the_installed_entry_offline_and_the_identifier_without_it(
    app_state, scratch_folder, monkeypatch
):
    """Unit D5, item 4: with the network disabled, the line of the list for
    the policy line of `cons.bl` edited to name a field the stage does not
    declare links its rule, `name-in-scope`, to the rule's entry on the
    published Refusals page at the address the catalogue of the imported
    Bellman gives, and holds under its facts the catalogue's entry of the
    rule as the installed package prints it, its four parts labeled as the
    package's example; the copy of the line records the installed versions
    of the two packages. Under a Bellman whose catalogue has no `entry`, a
    module built for the test standing in for a release before Model
    Interface 0.9, and under one whose `entry` fails, the line shows the
    sentence and the identifier alone, with no link and no entry."""

    def disabled(*args, **kwargs):
        raise OSError("the network is disabled for this test")

    monkeypatch.setattr(socket.socket, "connect", disabled)
    monkeypatch.setattr(socket, "create_connection", disabled)
    written(scratch_folder / CONS, POLICY_LINE, NAME_READ)
    app_state(scratch_folder)
    app.source.value = RECIPE
    model.rule_entry.cache_clear()
    try:
        app.open_file(CONS)
        app.run_loop()
        (row,) = [row for row in app.standing_refusals() if row.rule == "name-in-scope"]

        def drawn() -> tuple:
            # the rule's element, its address, its text and the entries of the
            # line, and the line's sentence
            _, rendered = solara.render(app.ErrorLine(row), handle_error=False)
            try:
                (rule,) = rendered.find(v.Html, class_="bl-error-rule").widgets
                entries = rendered.find(v.Html, class_="bl-rule-entry").widgets
                sentence = rendered.find(v.Html, class_="bl-error-sentence").widget
                return (rule.tag, (rule.attributes or {}).get("href"), drawn_text(rule),
                        [drawn_text(held) for held in entries], drawn_text(sentence))
            finally:
                rendered.close()

        installed = refusal_catalogue.entry("name-in-scope")
        address = f"{refusal_catalogue.REFERENCE_PAGE}#name-in-scope"
        shown = drawn()
        assert shown == ("a", address, "name-in-scope", [f"entry{installed}"], row.sentence)
        label = "\n  example  the package's example of the rule, and the refusal it provokes:\n"
        assert label + "  where  t.bl," in shown[3][0]
        versions = app.problem_text(row).splitlines()[1]
        assert versions == ", ".join(
            f"{name} {importlib.metadata.version(name)}"
            for name in ("bellman", "bellman-workbench")
        )

        def failing(rule):
            raise FileNotFoundError(f"the stage file of the example of {rule} is not installed")

        older = types.ModuleType("bellman.refusal_catalogue")
        older.catalogue = refusal_catalogue.catalogue
        older.refusal_of = refusal_catalogue.refusal_of
        failed = types.ModuleType("bellman.refusal_catalogue")
        failed.entry, failed.REFERENCE_PAGE = failing, refusal_catalogue.REFERENCE_PAGE
        for stand_in in (older, failed):
            monkeypatch.setitem(sys.modules, "bellman.refusal_catalogue", stand_in)
            model.rule_entry.cache_clear()
            assert drawn() == ("span", None, "name-in-scope", [], row.sentence)
    finally:
        model.rule_entry.cache_clear()
        clear_trellis_state()
