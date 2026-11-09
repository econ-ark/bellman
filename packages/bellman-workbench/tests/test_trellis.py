"""The trellis of a model folder (`bellman_workbench.trellis`; model
interface specification 0.3, §3.1), on the temporary copies of cons-port,
the pension model, the Cagetti–De Nardi model and the lifecycle registry of
`workbench_support`: the restriction typed in the view's bar, the binding
with its report, one reading of the trellis, its reading again after a save,
and the place a refusal's address names. On a copy of the durables model,
items 2 and 4 of the brief on the trellis view's load time: the first
reading in a fresh process, and a reading in which only the restriction
changed; its item 3, the text the view's bar opens with for a trellis of
more than six periods; and its change 4, the stage views kept in the cache
folder from one process to the next. On the portfolio model, and once on
the durables model, the binding of a trellis kept on disk between starts of
the Workbench, one test for each claim of ruling G-R81. On copies of
lesson 05, of the portfolio model and of the pension model, the reading of
the tab's unsaved buffers (unit J of model interface specification 0.4,
brief rules 2, 5 and 10); the one replacement that takes a gesture's
line out of the text it made (brief rule 8); and, on copies of lesson 05
and of the portfolio model, the text a drag between two unjoined ports
types, or the Workbench's sentence where it types nothing (brief rules 1,
6 and 8, and §5); and the `+ period` controls, what Details lists for the
terminal period, and a drop of another reading (brief rules 6 and 9, and
§5). On copies of lesson 05 and of the durables model, the removal and
the move of a join wire of the forward trellis graph (unit J, Task 19;
decisions J-D33 and J-D34). On a copy of the durables model, Details of
a selected stage occurrence, and the ranges of a stage file's uses (unit
K, Task 3); on copies of the durables model and of lesson 05, Details of a
selected join wire (unit K, Task 4); on copies of the portfolio model, of
lesson 05, of the pension model and of the durables model, the pairing of
two stage occurrences' fields and the mapping their join types (unit K,
Task 11). On a folder of the forms, the sections of the stage list and a
stage of the library of stages dropped on a period (unit L, Task 7). On
the durables model and on lesson 05, the periods each stage key is listed
in and the periods the view draws (unit L, Task 11). On copies of the
pension model of the UX simulation and of lesson 05, a stage occurrence
removed with the entries of its joins, a drop on the last graph
constructed while a reading stands refused, and the joins entries already
written give a stage added (unit L, Task 14). On a copy of the durables
model, the labels the layout script gives the wires of the two trellis
graphs as the page opens them: the value and marginal-value fields in the
backward graph, the joins' fields in the forward graph (unit L, Task 31). Every
test has a cache folder of its own, so that none reads a binding another
test or a server kept."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import pickle
import re
import shutil
import stat
import subprocess
import sys
import time
import types
from pathlib import Path

import ipyvuetify as v
import pytest
import solara
from workbench_support import COMPOSITION_STAGE, composition_folder
from workbench_support import (
    ADJUSTER_CONS_DETAILS,
    CONTRIBUTION_JOIN_ROWS,
    ADJUSTER_CONS_JOIN_DETAILS,
    BEQUEST_JOIN_DETAILS,
    DURABLES,
    LIFECYCLE_RECIPE,
    NOPORT_ID,
    PAIR_JOIN_DETAILS,
    PENSION_RETIREMENT,
    PENSIONS_RECIPE,
    PENSIONS_TRELLIS,
    PENSIONS_WORKING_YEARS,
    PORT_CONS,
    PORT_CONS_RECIPE,
    PORT_CONS_RECORDS,
    PORT_ID,
    PORTFOLIO_CHOICE,
    RECIPE_FILE,
    ROOT,
    SHARED_CONS,
    TERMINAL_CALIBRATION,
    applications_copy,
    applied,
    as_json,
    carried_functions,
    changed_lines,
    clear_trellis_state,
    connected_event,
    dropped_event,
    durables_without_a,
    emptied_pension,
    emptied_port_cons,
    emptied_portfolio,
    emptied_portfolio_with_entry_connectors,
    field_port,
    file_bytes,
    five_mappings_port_cons,
    graph_named,
    join_event,
    join_labels,
    joined_states,
    kept_bindings,
    lifecycle_registry,
    node_output,
    occurrence_nodes,
    old_graph_gesture,
    pensions_copy,
    pensions_with_bequest_dur,
    records_folder,
    records_without,
    repository_copy,
    stage_nodes,
    two_cons_one_joined,
    two_cons_period,
    unsaved_of,
    written_from_the_forms,
)

import bellman.factory.trellis as factory_trellis
from bellman.native.labels import function_name
from bellman.native.provenance import package_version
from bellman.stage import LAYER_ID_ENDING, elaborate_text, source_spans
from bellman.trellis import elaborate_trellis, entry_value, load_recipe
from bellman_workbench import app, creation, model, recipe, trellis

pytestmark = pytest.mark.usefixtures("own_cache_folder")

LESSON = recipe.Source("recipe", PORT_CONS_RECIPE)
# the trellis of records a folder of records opens on (`records_folder`)
RECORDS = recipe.Source("trellis", PORT_CONS_RECORDS)


def without_drafts(gesture):
    """The gesture `gesture` with the drafts its note names after `; draft:`
    left out, the part of the note that unit N's Task 7 adds for an
    incomplete route the package reports (design pass 10 §7)."""
    if gesture.note is None or "; draft: " not in gesture.note:
        return gesture
    return gesture._replace(note=gesture.note.split("; draft: ")[0])
# the recipe of a folder in the one layout, as the source of its trellis
RECIPE = recipe.Source("recipe", RECIPE_FILE)


def test_parse_restriction_reads_the_two_clauses_and_refuses_in_one_sentence():
    """`periods 0–2`, `stages cons, port` and both, in either order and with a
    hyphen or an en dash, are read; an empty text is the whole trellis; a
    clause that is neither, a range that runs down, a word in place of a
    number and a clause written twice are refused, each in one sentence that
    says what to write."""
    parse = trellis.parse_restriction
    assert parse("") is None and parse("   ") is None
    assert parse("periods 0–2") == trellis.Restriction((0, 1, 2), None, "periods 0–2")
    assert parse("stages cons, port") == trellis.Restriction(
        None, ("cons", "port"), "stages cons, port"
    )
    assert parse("periods 0-1, stages cons") == trellis.Restriction(
        (0, 1), ("cons",), "periods 0–1, stages cons"
    )
    assert parse("stages cons; periods 3") == trellis.Restriction(
        (3,), ("cons",), "periods 3, stages cons"
    )
    for text, words in (
        ("periods two", "is no period range; write `periods 0–2` or `periods 3`"),
        ("periods 3–1", "^the range `3–1` runs from 3 down to 1$"),
        ("stages", "names no stage keys; write `stages cons, port`"),
        ("sideways 1", "is neither `periods 0–2` nor `stages cons, port`"),
        ("periods 1, periods 2", "is neither"),
    ):
        with pytest.raises(ValueError, match=words):
            parse(text)


def test_parse_restriction_reads_a_space_before_a_comma_and_a_comma_after_the_last_key():
    """A space before the comma that joins the clauses, `periods 0-1 , stages
    cons`, and a comma after the last stage key, `stages cons,`, are read as
    written without them; `stages ,`, which names no key, is refused
    (the ledger's line 114)."""
    parse = trellis.parse_restriction
    assert parse("periods 0-1 , stages cons") == trellis.Restriction(
        (0, 1), ("cons",), "periods 0–1, stages cons"
    )
    assert parse("stages cons,") == trellis.Restriction(None, ("cons",), "stages cons")
    assert parse("stages cons , port ;periods 2") == trellis.Restriction(
        (2,), ("cons", "port"), "periods 2, stages cons, port"
    )
    with pytest.raises(ValueError, match="names no stage keys"):
        parse("stages ,")


def test_k_the_restriction_s_menu_lists_the_ranges_the_trellis_admits_and_its_keys():
    """The menu of the restriction (unit K, K-D17; design pass 2 §3), for a
    trellis of 51 periods whose terminal period lists `tenure`,
    `keeper_cons`, `adjuster_cons` and `bequest` and whose other periods the
    first three: under `periods 0–2` the four ranges, `0–2` chosen, and `all
    51`, then the four keys ticked, `bequest` last; a range keeps the stage
    clause and a check the period clause, every key ticked writing none; the
    one key ticked cannot be unticked. A trellis of six periods lists `0–2`
    and `0–5`; with no trellis read the menu is `all` alone. Every text the
    menu writes is read back by `parse_restriction` as itself."""
    first = {"tenure": {}, "keeper_cons": {}, "adjuster_cons": {}}
    syntactic = {"periods": [{"stages": {**first, "bequest": {}}}] + [{"stages": first}] * 50}
    keys = ["tenure", "keeper_cons", "adjuster_cons", "bequest"]
    parse = trellis.parse_restriction
    Choice = trellis.RestrictionChoice

    ranges, checks = trellis.restriction_menu(parse("periods 0–2"), syntactic)
    assert ranges == [
        Choice("0–2", "periods 0–2", True),
        Choice("0–5", "periods 0–5", False),
        Choice("0–10", "periods 0–10", False),
        Choice("0–20", "periods 0–20", False),
        Choice("all 51", "", False),
    ]
    assert [(check.label, check.chosen) for check in checks] == [(key, True) for key in keys]
    assert checks[0].text == "periods 0–2, stages keeper_cons, adjuster_cons, bequest"

    restricted = parse("periods 0–5, stages tenure, bequest")
    ranges, checks = trellis.restriction_menu(restricted, syntactic)
    assert [range_.text for range_ in ranges] == [
        "periods 0–2, stages tenure, bequest",
        "periods 0–5, stages tenure, bequest",
        "periods 0–10, stages tenure, bequest",
        "periods 0–20, stages tenure, bequest",
        "stages tenure, bequest",
    ]
    assert [range_.chosen for range_ in ranges] == [False, True, False, False, False]
    assert checks == [
        Choice("tenure", "periods 0–5, stages bequest", True),
        Choice("keeper_cons", "periods 0–5, stages tenure, keeper_cons, bequest", False),
        Choice("adjuster_cons", "periods 0–5, stages tenure, adjuster_cons, bequest", False),
        Choice("bequest", "periods 0–5, stages tenure", True),
    ]
    _, checks = trellis.restriction_menu(parse("stages tenure, keeper_cons, bequest"), syntactic)
    assert checks[2] == Choice("adjuster_cons", "", False)
    _, checks = trellis.restriction_menu(parse("periods 3, stages bequest"), syntactic)
    assert checks[3] == Choice("bequest", None, True)

    ranges, checks = trellis.restriction_menu(None, syntactic)
    assert ranges[-1] == Choice("all 51", "", True) and not any(r.chosen for r in ranges[:-1])
    assert all(check.chosen for check in checks)

    six = {"periods": [{"stages": {"port": {}, "disc": {}, "cons": {}}}] * 6}
    ranges, checks = trellis.restriction_menu(None, six)
    assert [range_.label for range_ in ranges] == ["0–2", "0–5", "all 6"]
    assert [check.label for check in checks] == ["port", "disc", "cons"]
    assert trellis.restriction_menu(parse("stages cons"), None) == (
        [Choice("all", "stages cons", True)],
        [],
    )

    for restriction in (None, parse("periods 0–5, stages tenure, bequest"), parse("periods 7")):
        ranges, checks = trellis.restriction_menu(restriction, syntactic)
        for choice in ranges + checks:
            if choice.text:
                assert parse(choice.text).text == choice.text, choice


def test_bind_trellis_reports_the_verbs_applied_skipped_and_refused(pension_folder, tmp_path):
    """The pension trellis, whose slots no keyword binds and whose stages'
    methods files the recipe names, binds the methods and names the two other
    verbs skipped, which give no note, since a verb skipped is no refusal
    (unit L, Task 21; K-D29; decision MB-V38); the lifecycle registry binds
    all three; a terminal
    discount factor of 1.5, outside `(0, 1)`, refuses `calibrate_trellis`
    with the occurrence it names, its note the package's sentence and
    nothing added, the message on its first line and the occurrence on a
    line of its own, as `model.refusal_of` prints a sentence of the
    package, and the two other verbs still bind (decision B-D3; AMD-MI-002
    §6a rule 2; ruling R51)."""
    syntactic = load_recipe(pension_folder / "declaration", "spec.yml")
    pension = trellis.bind_trellis(elaborate_trellis(syntactic), syntactic)
    assert (pension.bound, pension.skipped, pension.failed) == (
        ("methodize",),
        ("calibrate", "configure"),
        {},
    )
    assert trellis.binding_notes(pension) == []
    registry = lifecycle_registry(tmp_path / "lifecycle") / "declaration"
    syntactic = load_recipe(registry, "spec.yml")
    assert trellis.bind_trellis(elaborate_trellis(syntactic), syntactic).bound == (
        "calibrate",
        "methodize",
        "configure",
    )
    (registry / "calibration/terminal.yml").write_text(
        TERMINAL_CALIBRATION.replace("0.9", "1.5"), encoding="utf-8"
    )
    syntactic = load_recipe(registry, "spec.yml")
    broken = trellis.bind_trellis(elaborate_trellis(syntactic), syntactic)
    assert broken.bound == ("methodize", "configure") and list(broken.failed) == ["calibrate"]
    message, *notes = broken.failed["calibrate"].split("\n")
    assert message.startswith("stage 'disc', parameter 'β' (address '")
    assert message.endswith(
        "the value 1.5 lies outside the declared set (0, 1); a parameter's value lies in the"
        " set its declaration names (AMD-SG-006 §2, the parameter record); write a value in"
        " (0, 1)"
    )
    assert notes == ["Stage occurrence: periods[0].stages['disc']"]
    assert trellis.binding_notes(broken) == [broken.failed["calibrate"]]


def test_show_trellis_reads_elaborates_binds_and_draws_port_cons(consport_folder):
    """The trellis of lesson 05: bound by the three verbs, two graphs, the
    eighteen occurrences opened period by period, the last period first, in
    each period's forward order, the files it reads among them the stage
    files outside the folder; restricted to `periods 0–1, stages cons`, the
    two consumption occurrences; a period it does not hold is the package's
    sentence, the view drawn under the restriction the package accepted last
    for the source, the whole trellis after the first reading and `periods
    0–1, stages cons` after the second."""
    folder = model.open_folder(consport_folder)
    outcome = trellis.show_trellis(folder, LESSON)
    shown = outcome.shown
    assert outcome.refusal is None and shown.binding.bound == (
        "calibrate",
        "methodize",
        "configure",
    )
    # the two builders graphs; the two initial diagrams follow once the Initial view asks for
    # them, drawn under the same restriction (design pass 14 §7; S-D30)
    assert [graph["id"] for graph in shown.collection["graphs"]] == ["backward", "forward"]
    assert shown.layers["backward"] == [
        f"periods[{h}]/{key}" for h in range(5, -1, -1) for key in ("port", "cons", "disc")
    ]
    assert not trellis.holds_initial_diagrams(shown)
    shown = trellis.with_initial_diagrams(shown)
    assert trellis.holds_initial_diagrams(shown) and trellis.with_initial_diagrams(shown) is shown
    assert [graph["id"] for graph in shown.collection["graphs"]] == [
        "backward",
        "forward",
        "backward initial diagram",
        "forward initial diagram",
    ]
    # the initial diagram opens the perch layers of those occurrences as well (design pass 14 §7)
    initial = shown.layers["backward initial diagram"]
    assert [layer for layer in initial if layer.count("/") == 1] == shown.layers["backward"]
    assert {layer.split("/")[2] for layer in initial if layer.count("/") == 2} <= {"arvl", "dcsn", "cntn"}
    assert any(layer.count("/") == 2 for layer in initial)
    assert shown.counts == {"periods": 6, "occurrences": 18, "shown": 18} and shown.changed == []
    read = {recipe.relative(folder, path) for path in shown.files}
    # the demonstration's consumption stage file since decision SD-39
    assert {
        PORT_CONS,
        SHARED_CONS,
        "declaration/calibration/portfolio.yml",
    } <= read
    restricted = trellis.show_trellis(
        folder, LESSON, trellis.parse_restriction("periods 0–1, stages cons"), shown
    ).shown
    assert restricted.counts["shown"] == 2
    assert restricted.layers["backward"] == ["periods[1]/cons", "periods[0]/cons"]
    sentence = "the trellis holds 6 periods, and periods[7] is none of them"
    seven = trellis.parse_restriction("periods 7")
    for held in (shown, restricted):
        refused = trellis.show_trellis(folder, LESSON, seven, held)
        assert refused.restricted == sentence and refused.refusal is None
        assert refused.shown.restriction == held.restriction
        assert refused.shown.collection == held.collection
        assert refused.files == refused.shown.files == held.files


def test_saving_a_stage_file_and_a_calibration_reads_the_trellis_again_once(scratch_consport):
    """The shared consumption file changed on disk: the files' digests differ,
    and the next reading, with the trellis shown as its `previous`,
    constructs the six consumption occurrences again and keeps the twelve
    others, as the trellis shown before holds them; the calibration's
    discount factor changed: the calibration file is a source of the three
    stages, whose records all change, so that every occurrence is bound
    again, the six discount occurrences at the new value (specification
    §3.1; unit L, Task 20)."""
    folder = model.open_folder(scratch_consport)
    first = trellis.show_trellis(folder, LESSON).shown
    # the demonstration's consumption stage file since decision SD-39
    stage_file = (
        scratch_consport / "declaration/stages/cons/cons.bl"
    )
    stage_file.write_text(
        stage_file.read_text(encoding="utf-8") + "\n# a comment\n", encoding="utf-8"
    )
    assert trellis.file_digests(first.files) != first.files
    second = trellis.show_trellis(folder, LESSON, previous=first).shown
    assert sorted(second.changed) == [(h, "cons") for h in range(6)]
    assert second.alone == ("cons",)
    calibration = scratch_consport / "declaration/calibration/portfolio.yml"
    calibration.write_text(
        calibration.read_text(encoding="utf-8").replace("β: 0.96", "β: 0.95"), encoding="utf-8"
    )
    third = trellis.show_trellis(folder, LESSON, previous=second).shown
    assert len(third.changed) == 18 and third.alone == ("port", "cons", "disc")
    assert {third.trellis["periods"][h]["stages"]["disc"].par["β"].value for h in range(6)} == {
        0.95
    }


def test_show_trellis_answers_the_refusal_of_a_trellis_file_that_names_its_stages_by_key(
    cagetti_folder,
):
    """The Cagetti–De Nardi trellis file names its stages by key and the
    folder holds no recipe: the reading is refused under
    `trellis-file-shape` with the file and the address, its sentence the
    package's message and, on a line of its own, the words it says to
    write, no trellis, nothing raised; the address opens the file at line
    12."""
    folder = model.open_folder(cagetti_folder)
    outcome = trellis.show_trellis(folder, recipe.Source("trellis", "declaration/trellis.yml"))
    assert outcome.shown is None
    refusal = outcome.refusal
    assert (refusal.rule, refusal.address) == ("trellis-file-shape", "periods[0].stages")
    assert refusal.message == (
        "periods[0].stages is no mapping of keys to records\n"
        "stages: {<key>: {stage: <file>.bl, calibration: ..., settings: ..., methods: ...}}"
    )
    assert trellis.address_place(folder, refusal.file, refusal.address, expanded=False) == (
        "declaration/trellis.yml",
        12,
    )


def test_address_place_moves_an_address_of_the_trellis_to_the_line_of_the_file_that_writes_it(
    pension_folder,
):
    """A connector of the terminal period stands in the trellis file at line
    20, one of a period the template repeats in `period.yml` at line 11, and a
    recipe's entry at its own line; an address no file writes has no place."""
    folder = model.open_folder(pension_folder)
    trellis_file = folder.root / "declaration/trellis.yml"
    assert trellis.address_place(folder, trellis_file, "periods[0].connectors[0]") == (
        "declaration/trellis.yml",
        20,
    )
    assert trellis.address_place(folder, trellis_file, "periods[5].connectors[0]") == (
        "declaration/period.yml",
        11,
    )
    # the line of the worker's entry is read from the recipe's text
    recipe_file = folder.root / "declaration/spec.yml"
    lines = recipe_file.read_text(encoding="utf-8").split("\n")
    numbers = [n for n, line in enumerate(lines, start=1) if line.startswith("  worker_saving:")]
    assert len(numbers) == 1
    assert trellis.address_place(folder, recipe_file, "stages.worker_saving.calibration") == (
        "declaration/spec.yml",
        numbers[0],
    )
    assert trellis.address_place(folder, trellis_file, "periods[0].nothing") is None


def test_address_place_answers_no_place_in_a_trellis_file_of_a_shape_the_factory_refuses(
    tmp_path,
):
    """A trellis file whose `periods` is a number, and one whose
    `inter_connectors` is a number, shapes the factory refuses, on which
    `written_at` raises a TypeError: `address_place` answers no place and
    raises nothing, as the recipe under the tree reads such a file (the
    ledger's line 283)."""
    folder = model.open_folder(tmp_path)
    trellis_file = tmp_path / "trellis.yml"
    for text, address in (
        ("!trellis\nperiods: 5\n", "periods[0].connectors[0]"),
        (
            "!trellis\nperiods:\n  - stages: [a]\n  - stages: [a]\ninter_connectors: 5\n",
            "inter_connectors[0]",
        ),
    ):
        trellis_file.write_text(text, encoding="utf-8")
        assert trellis.address_place(folder, trellis_file, address) is None


def test_bind_trellis_reports_a_methods_target_the_stage_lacks_as_a_failed_verb(
    scratch_lifecycle,
):
    """A methods file that names a builder the discount stage lacks is refused
    by `methodize_trellis` with a `TargetError`, a LookupError, as
    `bind_stage` refuses it: the binding names `methodize` failed, with the
    target and the occurrence, and raises nothing."""
    methods = scratch_lifecycle / "declaration/stages/disc/methods.yml"
    methods.write_text(
        methods.read_text(encoding="utf-8").replace("on: dcsn_to_cntn", "on: no_such_builder"),
        encoding="utf-8",
    )
    syntactic = load_recipe(scratch_lifecycle / "declaration", "spec.yml")
    broken = trellis.bind_trellis(elaborate_trellis(syntactic), syntactic)
    assert "methodize" in broken.failed and "methodize" not in broken.bound
    assert "'no_such_builder' in stage 'disc' names no builder" in broken.failed["methodize"]
    assert "Stage occurrence: periods[0].stages['disc']" in broken.failed["methodize"]


def test_a_reading_with_the_trellis_shown_before_answers_what_a_reading_without_it_answers(
    tmp_path,
):
    """The lifecycle registry read once, then read again with that reading
    as `previous` and without it. After a settings file writes a key that is
    a number, which the elaboration refuses, the two readings answer the
    same refusal and no trellis. After a terminal discount factor of 1.5,
    which `calibrate_trellis` refuses, and after the recipe's calibration
    sources are removed, which skips `calibrate`, they answer the same view
    and the same verbs bound, skipped and refused, so that no binding of the
    first reading outlives its source (decision B-D3)."""
    registry = lifecycle_registry(tmp_path / "lifecycle")
    folder = model.open_folder(registry)
    first = trellis.show_trellis(folder, RECIPE).shown
    settings = registry / "declaration/settings/cons.yml"
    written = settings.read_text(encoding="utf-8")
    settings.write_text(written + "  extra: {1: 10}\n", encoding="utf-8")
    integer_key = [trellis.show_trellis(folder, RECIPE, previous=held) for held in (first, None)]
    settings.write_text(written, encoding="utf-8")
    (registry / "declaration/calibration/terminal.yml").write_text(
        TERMINAL_CALIBRATION.replace("0.9", "1.5"), encoding="utf-8"
    )
    refused = [trellis.show_trellis(folder, RECIPE, previous=held).shown for held in (first, None)]
    (registry / "declaration/spec.yml").write_text(
        LIFECYCLE_RECIPE.replace("calibration: {all: [calibration/portfolio]}, ", "").replace(
            "calibration: {all: [calibration/portfolio], 0-0: [calibration/terminal]}, ", ""
        ),
        encoding="utf-8",
    )
    skipped = [trellis.show_trellis(folder, RECIPE, previous=held).shown for held in (first, None)]
    assert integer_key[0].shown is None and integer_key[1].shown is None
    assert integer_key[0].refusal == integer_key[1].refusal
    assert "Stage occurrence: periods[0].stages['cons']" in integer_key[1].refusal.message
    assert list(refused[1].binding.failed) == ["calibrate"]
    assert skipped[1].binding.skipped == ("calibrate",)
    for again, alone in (refused, skipped):
        assert (again.binding.bound, again.binding.skipped, list(again.binding.failed)) == (
            alone.binding.bound,
            alone.binding.skipped,
            list(alone.binding.failed),
        )
        assert again.collection == alone.collection


def test_files_of_refusal_are_the_source_the_trellis_file_the_refusals_file_and_the_held_files(
    refused_pension,
):
    """The files whose change reads a refused trellis again: the pension copy
    whose terminal connector has an invalid keyed shape is refused at
    `declaration/trellis.yml`, and the files are the recipe and that file,
    once each; with the trellis of the same recipe held from before, they
    are every file that trellis read; a trellis of another source adds none
    (specification §3.1)."""
    file = refused_pension / "declaration/trellis.yml"
    source = file.read_text(encoding="utf-8")
    file.write_text(source.replace("y_f_wk: y_f_X", "fields: y_f_X", 1), encoding="utf-8")
    folder = model.open_folder(refused_pension)
    refusal = trellis.show_trellis(folder, RECIPE).refusal
    assert (refusal.rule, refusal.address) == (
        "connector-names-no-field",
        "periods[0].connectors[0]",
    )
    root = refused_pension.resolve() / "declaration"
    assert trellis.files_of_refusal(folder, RECIPE, refusal) == [
        root / "spec.yml",
        root / "trellis.yml",
    ]
    corrected = (PENSION_RETIREMENT / "declaration/trellis.yml").read_text(encoding="utf-8")
    (refused_pension / "declaration/trellis.yml").write_text(corrected, encoding="utf-8")
    held = trellis.show_trellis(folder, RECIPE).shown
    files = trellis.files_of_refusal(folder, RECIPE, refusal, held)
    assert files[:2] == [root / "spec.yml", root / "trellis.yml"]
    assert set(files) == {Path(name) for name in held.files}
    other = recipe.Source("trellis", "declaration/trellis.yml")
    assert trellis.files_of_refusal(folder, other, refusal, held) == [root / "trellis.yml"]


def test_describe_node_reads_the_occurrences_own_stage_view_and_the_trellis_ports(consport_folder):
    """In the trellis of lesson 05 (specification §2.4 and §3.1): a box of
    `periods[1]/cons` is the piece of that occurrence's own stage view, its
    input carrying the join `a` and the rule that paired it; the
    occurrence's layer holds its stage's name and bindings; the layer of
    `periods[1]` lists its occurrences in their forward order; an
    occurrence's own `Outputs` lists its ports; a boundary node of the
    trellis, at which the terminal value enters the backward graph or the
    first stage's value leaves it, lists its attributes and its one port as
    the trellis's `Inputs` or `Outputs` listed them (design pass 10 §6;
    unit N, Task 6), and the root `Inputs` is no longer a node of the view;
    a block's header stands at line 21 of the occurrence's stage file, which
    lies outside the folder (Review Focus 4); a node the view does not hold
    is refused."""
    folder = model.open_folder(consport_folder)
    shown = trellis.show_trellis(folder, LESSON).shown
    views = {}
    box = trellis.describe_node(shown, "backward", "periods[1]/cons/cntn_to_dcsn:Pullback", views)
    assert (box.kind, box.occurrence, box.position) == ("piece", "periods[1]/cons", (1, "cons"))
    assert (box.piece.node_id, box.piece.kind, box.piece.block) == (
        "cntn_to_dcsn:Pullback",
        "box",
        "cntn_to_dcsn",
    )
    assert [
        (row["label"], row["join"], row["paired by"]) for row in box.piece.ports["inputs"]
    ] == [("𝑉≻(a)", "a", "one wire per role")]
    occurrence = trellis.describe_node(shown, "backward", "periods[1]/cons___group___", views)
    assert (occurrence.kind, occurrence.position) == ("occurrence", (1, "cons"))
    assert occurrence.rows == {"stage": "cons calibrated methodized configured"}
    period = trellis.describe_node(shown, "backward", "periods[1]___group___", views)
    assert period.kind == "period"
    assert [address for address, _ in period.occurrences] == [
        "periods[1]/port",
        "periods[1]/cons",
        "periods[1]/disc",
    ]
    own = trellis.describe_node(shown, "backward", "periods[5]/port/GraphOutputs", views)
    assert (own.kind, own.position) == ("outputs", (5, "port"))
    terminal = "periods[0]/disc/disc:function:cntn:V"
    inputs = trellis.describe_node(shown, "backward", f"start:{terminal}", views)
    assert (inputs.kind, inputs.occurrence, inputs.position) == ("inputs", "", None)
    assert inputs.rows == {"kind": "start", "label": "terminal condition 𝑉≻(a)"}
    assert [row["label"] for row in inputs.ports["outputs"]] == ["𝑉≻(a)"]
    assert inputs.ports["inputs"] == []
    result = "periods[5]/port/port:function:arvl:V"
    outputs = trellis.describe_node(shown, "backward", f"end:{result}", views)
    assert (outputs.kind, outputs.rows["kind"]) == ("outputs", "end")
    (row,) = outputs.ports["inputs"]
    assert outputs.rows["label"] == f"result {row['label']}"
    with pytest.raises(KeyError):
        trellis.describe_node(shown, "backward", "GraphInputs", views)
    # the demonstration's consumption stage file since decision SD-39, whose
    # block cntn_to_dcsn begins at its line 14
    assert trellis.block_line(views["periods[1]/cons"], "cntn_to_dcsn") == 14
    assert trellis.occurrence_file(folder, shown, (1, "cons")) == SHARED_CONS
    with pytest.raises(KeyError):
        trellis.describe_node(shown, "backward", "no such node", views)


def test_refusal_links_go_to_each_unpaired_wires_header_and_to_the_connector(pension_folder):
    """The pension trellis's refusing backward node (specification §3.1: it
    links to the marginal value's header declaration and to the connector):
    sixty joins; the first links twice to line 22 of
    `declaration/stages/retire_choice/retire_choice.bl`, where the header
    lists its two wires, and to line 27 of `declaration/trellis.yml`, the
    one inter-period mapping; a join into the terminal stage links to
    line 17, its period's connector; the node's rows are the package's."""
    folder = model.open_folder(pension_folder)
    shown = trellis.show_trellis(folder, RECIPE).shown
    links = trellis.refusal_links(folder, shown)
    assert len(links) == 60
    first = links[0]
    assert (first.label, first.source, first.target) == (
        "inter_connectors[13] y_f_wk → y_f_w",
        "periods[14]/retire_choice",
        "periods[13]/worker_saving",
    )
    assert [(link.path, link.line) for link in first.links] == [
        ("declaration/stages/retire_choice/retire_choice.bl", 22),
        ("declaration/stages/retire_choice/retire_choice.bl", 22),
        ("declaration/trellis.yml", 27),
    ]
    terminal = next(join for join in links if join.target == "periods[0]/terminal")
    assert terminal.links[-1] == trellis.Link(
        "trellis.yml periods[0].connectors[0]", "declaration/trellis.yml", 17
    )
    subject = trellis.describe_node(shown, "backward", "backward:refused", {})
    assert subject.kind == "refusal" and list(subject.rows)[:2] == ["refusal", "join 1"]


def test_a_periods_occurrences_follow_the_views_order_and_a_refused_graph_holds_no_layer(
    pension_folder,
):
    """The pension trellis (specification §3.1): in its forward graph the
    occurrences of `periods[3]` are listed in the order the view's layers
    list them, the forward order the exporter computes from the joins, which
    is not the order the trellis file writes; its backward graph is refused
    and holds no layer, so a period's or an occurrence's layer selected
    there is refused with a KeyError naming the node."""
    folder = model.open_folder(pension_folder)
    shown = trellis.show_trellis(folder, RECIPE).shown
    layers = graph_named(shown.collection, "forward")["groupNodeAttributes"]
    viewed = [key for key in layers if key.startswith("periods[3]/") and key.count("/") == 1]
    written = [f"periods[3]/{key}" for key in shown.trellis["periods"][3]["stages"]]
    assert viewed != written
    period = trellis.describe_node(shown, "forward", "periods[3]___group___", {})
    assert [address for address, _ in period.occurrences] == viewed
    assert period.occurrences[0][1] == (3, viewed[0].split("/")[1])
    for node_id in ("periods[3]___group___", "periods[3]/worker_saving___group___"):
        with pytest.raises(KeyError) as refused:
            trellis.describe_node(shown, "backward", node_id, {})
        assert node_id in refused.value.args[0]


def test_a_period_of_a_restricted_view_lists_the_occurrences_the_view_holds(consport_folder):
    """The trellis of lesson 05 restricted to `periods 0–1, stages cons`
    (specification §3.1): the layer of `periods[1]` lists `periods[1]/cons`
    alone, and a layer the view does not hold, the period `periods[3]` or
    the occurrence `periods[1]/port`, is refused with a KeyError naming the
    node."""
    folder = model.open_folder(consport_folder)
    restricted = trellis.show_trellis(
        folder, LESSON, trellis.parse_restriction("periods 0–1, stages cons")
    ).shown
    period = trellis.describe_node(restricted, "backward", "periods[1]___group___", {})
    assert period.occurrences == (("periods[1]/cons", (1, "cons")),)
    for node_id in ("periods[3]___group___", "periods[1]/port___group___"):
        with pytest.raises(KeyError) as refused:
            trellis.describe_node(restricted, "backward", node_id, {})
        assert node_id in refused.value.args[0]


def rows_text(rows) -> list:
    """Rows of Details as the page prints them: each label with the text of
    each of its lines (`trellis.line_text`)."""
    return [(label, [trellis.line_text(line) for line in lines]) for label, lines in rows]


def test_occurrence_rows_of_adjuster_cons_are_the_package_s_records(durables_folder):
    """Details of the durables model's stage occurrence
    periods[1]/adjuster_cons in the forward graph of `declaration/spec.yml`
    under `periods 0–2` (design pass §2, "A stage occurrence"; unit K, Task
    3), by direct call: the head and the rows of the fixture, the page's;
    `file` a link to the stage file's first line, `periods` and `also` each
    one link to its recipe's trellis at the occurrence. While a refusal of
    the trellis's reading names the stage file, the row `refused` follows
    `file`, a link to the refused line; a refusal of another file adds no
    row."""
    folder = model.open_folder(durables_folder)
    shown = trellis.show_trellis(folder, RECIPE, trellis.parse_restriction("periods 0–2")).shown
    sources = recipe.model_sources(folder)
    position = (1, "adjuster_cons")
    found = trellis.occurrence_rows(folder, shown, "forward", position, sources)
    head, rows = ADJUSTER_CONS_DETAILS
    assert f"{found.key} {found.place} forward" == head
    assert rows_text(found.rows) == rows
    by_label = dict(found.rows)
    path = "declaration/stages/adjuster_cons/adjuster_cons.bl"
    assert by_label["file"][0].parts == (trellis.Link(path, path, 1),)
    two_stages = recipe.Source("recipe", "declaration/spec.two-stages.yml")
    assert [part for label in ("periods", "also") for part in by_label[label][0].parts] == [
        trellis.Use("0–50", RECIPE, position),
        trellis.Use("declaration/spec.two-stages.yml · periods 0–50", two_stages, position),
    ]

    def refused(file):
        return model.Diagnostic(
            file, 17, 62, 17, 70, "the refusal's sentence", "output-defined", None, None
        )

    origin = shown.syntactic["periods"][1]["stages"]["adjuster_cons"]["stage"]["origin"]
    marked = trellis.occurrence_rows(folder, shown, "forward", position, sources, refused(origin))
    text = f"{path} 17:62 · output-defined"
    assert [label for label, _ in marked.rows][:3] == ["file", "refused", "bound"]
    assert dict(marked.rows)["refused"][0].parts == (trellis.Link(text, path, 17),)
    other = refused(shown.syntactic["periods"][1]["stages"]["tenure"]["stage"]["origin"])
    unmarked = trellis.occurrence_rows(folder, shown, "forward", position, sources, other)
    assert unmarked.rows == found.rows


def test_use_rows_print_one_range_per_recipe_and_a_recipe_with_gaps_as_runs():
    """The rows `periods` and `also` (design pass §2; unit K, Task 3): one
    range per recipe, the tab's under `periods`, a recipe with gaps as its
    runs, `0–4, 7–50`, every other recipe under `also` after its path, each
    link at the occurrence given where the recipe holds it and at its first
    position otherwise; a recipe that holds none has no line, and without
    the tab's recipe among the holders the row `periods` is left out."""
    own = recipe.Source("recipe", "declaration/spec.yml")
    short = recipe.Source("recipe", "declaration/spec.short.yml")
    empty = recipe.Source("recipe", "declaration/spec.empty.yml")
    held = tuple((h, "cons") for h in [*range(5), *range(7, 51)])
    rows = trellis.use_rows(
        [(own, held), (empty, ()), (short, ((2, "cons"), (3, "cons")))], own, (8, "cons")
    )
    assert rows_text(rows) == [
        ("periods", ["0–4, 7–50"]),
        ("also", ["declaration/spec.short.yml · periods 2–3"]),
    ]
    assert [line.parts[0].position for _, lines in rows for line in lines] == [
        (8, "cons"),
        (2, "cons"),
    ]
    alone = trellis.use_rows([(own, ()), (short, ((2, "cons"),))], own, None)
    assert rows_text(alone) == [("also", ["declaration/spec.short.yml · periods 2"])]


def test_join_rows_of_a_wire_between_periods_and_within_one_are_the_package_s_joins(
    durables_folder, tmp_path
):
    """Details of a selected join wire (design pass §2, "A join wire"; unit
    K, Task 4), by direct call. On the durables model under `periods 0–2`,
    the wire from periods[1]/adjuster_cons to periods[0]/tenure prints the
    fixture: the entry that writes it, a link to its line; the adjacent
    pairs it reaches; the two measures; the table of the three joins the
    package answers for that writer, not the six entries of the reading
    port's text, each arrival field counting its second source, which `also`
    names (J-D42). The wire within periods[0] from adjuster_cons to bequest
    prints its connector, the one period it reaches and the same form. On
    lesson 05, the wire within a period from port to cons, of one source,
    prints the join and the two sets its fields are declared in, with no
    count of sources, and the six periods; the wire from
    periods[3]/disc to periods[2]/port reaches every adjacent pair, and,
    where the file writes one mapping for each pair, its own pair alone."""
    folder = model.open_folder(durables_folder)
    shown = trellis.show_trellis(folder, RECIPE, trellis.parse_restriction("periods 0–2")).shown
    wires = {(wire["from"], wire["to"]): wire for wire in trellis.join_wires(shown)}
    between = trellis.join_rows(
        folder, shown, wires["periods[1]/adjuster_cons", "periods[0]/tenure"]
    )
    head, rows = ADJUSTER_CONS_JOIN_DETAILS
    assert f"join {between.place} forward" == head
    assert rows_text(between.rows) == rows
    by_label = dict(between.rows)
    link = trellis.Link(
        "declaration/trellis.yml · inter_connectors[0]", "declaration/trellis.yml", 19
    )
    assert by_label["written"][0].parts == (link,)
    assert [line.cells for line in by_label["fields"]] == [
        ("a_nxt_adj → a", "ℝ₊", "2 sources"),
        ("h_nxt_adj → h", "ℝ₊₊", "2 sources"),
        ("z_nxt_adj → z", "ℝ₊₊", "2 sources"),
    ]
    within = trellis.join_rows(
        folder, shown, wires["periods[0]/adjuster_cons", "periods[0]/bequest"]
    )
    head, rows = BEQUEST_JOIN_DETAILS
    assert f"join {within.place} forward" == head
    assert rows_text(within.rows) == rows

    copy = applications_copy(tmp_path / "lesson")
    lesson = model.open_folder(copy)
    shown = trellis.show_trellis(lesson, LESSON).shown
    wires = {(wire["from"], wire["to"]): wire for wire in trellis.join_wires(shown)}
    inside = trellis.join_rows(lesson, shown, wires["periods[2]/port", "periods[2]/cons"])
    assert inside.place == "periods[2]/port → periods[2]/cons"
    by_label = dict(inside.rows)
    assert [label for label, _ in inside.rows] == ["written", "periods", "measure", "fields"]
    assert rows_text([("periods", by_label["periods"])]) == [("periods", ["0–5"])]
    assert [line.cells for line in by_label["fields"]] == [("w → m", "ℝ₊₊ → Xm")]
    across = trellis.join_rows(lesson, shown, wires["periods[3]/disc", "periods[2]/port"])
    assert dict(across.rows)["pairs"][0].parts == ("every adjacent pair (5)",)
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    five = text.replace(FILLED_MAPPING, "inter_connectors:\n" + "  - {disc.a: k}\n" * 5)
    unsaved = unsaved_of(copy, {PORT_CONS: five})
    texts = trellis.texts_of(unsaved)
    held = trellis.show_trellis(lesson, LESSON, previous=shown, unsaved=unsaved).shown
    wire = {(w["from"], w["to"]): w for w in trellis.join_wires(held, texts)}[
        "periods[3]/disc", "periods[2]/port"
    ]
    own = trellis.join_rows(lesson, held, wire, texts)
    assert rows_text(own.rows)[:2] == [
        ("written", ["declaration/trellis.port-cons.yml · inter_connectors[2]"]),
        ("pairs", ["1 of 5 · periods 2–3"]),
    ]


def test_k_a_pair_of_periods_is_one_record_whose_removal_takes_its_entry(durables_folder):
    """The piece that the two join wires of an adjacent pair of periods
    share between the two periods (unit K's decision K-D5, Task 7), by
    direct call. On the durables model under `periods 0–2`, `join_wires`
    answers, after the twelve join wires that entries write, six of them
    from `tenure` to the decision states of the two consumption stages of
    each period, which the period's connector writes since those stages
    begin at their decision perch (decision MB-U30), one record for each
    pair, from
    periods[2] and from periods[1] into the next period's `tenure`, named by
    its writers' period and no port, its reading end alone movable (unit
    K's decision K-D23, Task 22); the wires keep their records. Details of
    the pair print both writers' measures and the six joins of the one
    inter-period mapping, with no `also`. Its removal takes that entry's six
    keys out, the mapping left `{}` so that the list keeps one mapping, and
    the note names the entry with its text as written and the periods it
    reached; a move of the pair that names one port, as a move of one entry
    does, is the sentence of an old graph, since a pair moves through its
    list."""
    folder = model.open_folder(durables_folder)
    shown = trellis.show_trellis(folder, RECIPE, trellis.parse_restriction("periods 0–2")).shown
    wires = trellis.join_wires(shown)
    pairs = [wire for wire in wires if wire["writing"]["key"] is None]
    assert [(pair["from"], pair["to"]) for pair in pairs] == [
        ("periods[2]", "periods[1]/tenure"),
        ("periods[1]", "periods[0]/tenure"),
    ]
    assert wires[-2:] == pairs and len(wires) == 14
    assert [(w["from"], w["to"]) for w in wires if not w["removable"]] == []
    assert sorted((w["from"], w["to"]) for w in wires if w["file"] == "period.yml") == [
        (f"periods[{h}]/tenure", f"periods[{h}]/{key}")
        for h in (1, 2)
        for key in ("adjuster_cons", "keeper_cons")
    ]
    pair = pairs[1]
    assert (pair["source"], pair["sourceHandle"], pair["between"], pair["movable"]) == (
        "periods[1]",
        None,
        True,
        READING_END,
    )
    assert pair["targetHandle"] == "periods[0]/tenure/tenure:measure:arvl"
    rows = trellis.join_rows(folder, shown, pair)
    head, expected = PAIR_JOIN_DETAILS
    assert (f"join {rows.place} forward", rows_text(rows.rows)) == (head, expected)

    file = durables_folder / "declaration/trellis.yml"
    path, text = str(file.resolve()), file.read_text(encoding="utf-8")
    mapping = "{a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}"
    ids = ("source", "sourceHandle", "target", "targetHandle")
    event = {"reading": trellis.reading_record(folder, shown), "join": {k: pair[k] for k in ids}}
    gesture = trellis.removal_edit(shown, event, {})
    assert gesture == trellis.Gesture(
        {path: text.replace(f"  - {mapping}\n", "  - {}\n")},
        {path: text},
        (),
        f"trellis.yml, inter_connectors[0]: {mapping} removed, periods 0–50",
        None,
        path,
        "inter_connectors[0]",
    )
    assert entry_value(gesture.edits[path], "inter_connectors") == [{}]
    moved = {**event, "end": "reading", "handle": "periods[0]/tenure/unjoined:a"}
    assert trellis.removal_edit(shown, moved, {}) == old_graph_gesture(file)
    assert file.read_text(encoding="utf-8") == text


# the record of `disc` in the stages of lesson 05's one entry, the last key
# of that mapping, written over two lines
DISC_RECORD = (
    "      disc: {stage: ../../portfolio-choice/declaration/stages/disc/disc.bl, "
    "calibration: calibration/portfolio.yml,\n"
    "             settings: {}, "
    "methods: ../../portfolio-choice/declaration/stages/disc/methods.yml}\n"
)


def test_k_a_stage_occurrence_removed_takes_its_key_out_of_the_list_that_writes_its_period(
    tmp_path,
):
    """A stage occurrence removed from its period (unit K's decision K-D14,
    Task 15), by direct call. On lesson 05, whose one entry of the trellis
    file writes its stages as records for six periods, the event `removed`
    that names `disc`'s layer in periods[2] takes the key `disc` with its
    record out of that entry's `stages` and nothing else, the note naming
    the file, the list and the six periods it writes; nothing is written to
    disk, and the trellis read from the text the removal made holds no
    `disc` in any period. On the portfolio model, whose periods' list is
    the period file's list of keys, `cons` removed from periods[4] takes
    that item out of the list. An event of another reading; a layer of a
    period the trellis does not hold, of a key the period does not hold, of
    a period itself, or no layer's id; a record that is no event; and an
    event read against a file that now holds another text each answer the
    sentence "An old graph", whose last sentence asks for the stage to be
    removed again, and write nothing."""
    copy = applications_copy(tmp_path / "lesson")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    assert text.count(DISC_RECORD) == 1
    reading = trellis.reading_record(folder, shown)
    event = {"reading": reading, "occurrence": "periods[2]/disc___group___"}
    gesture = trellis.occurrence_removal_edit(shown, event, {})
    assert gesture == trellis.Gesture(
        {path: text.replace(DISC_RECORD, "")},
        {path: text},
        (),
        "trellis.port-cons.yml, periods[0].stages: disc removed, periods 0–5",
        None,
        path,
        "periods[0].stages",
    )
    assert (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8") == text
    unsaved = unsaved_of(copy, {PORT_CONS: gesture.edits[path]})
    outcome = trellis.show_trellis(folder, LESSON, previous=shown, unsaved=unsaved)
    assert outcome.refusal is None
    assert [sorted(period["stages"]) for period in outcome.shown.trellis["periods"]] == [
        ["cons", "port"]
    ] * 6

    old = trellis.Gesture(
        None,
        None,
        (),
        None,
        "trellis.port-cons.yml: nothing was written. The graph was drawn from an earlier "
        "text. Remove the stage again in the graph now drawn.",
        path,
        None,
    )
    for other in (
        {**event, "reading": {**reading, "number": reading["number"] + 1}},
        {**event, "reading": {**reading, "source": "declaration/trellis.port-cons-vfi.yml"}},
        {**event, "reading": {**reading, "graph": "backward"}},
        {**event, "reading": None},
        {**event, "occurrence": "periods[6]/disc___group___"},
        {**event, "occurrence": "periods[2]/bequest___group___"},
        {**event, "occurrence": "periods[2]___group___"},
        {**event, "occurrence": "periods[2]/disc"},
        {**event, "occurrence": None},
        {"reading": reading},
        None,
        "removed",
    ):
        assert trellis.occurrence_removal_edit(shown, other, {}) == old
    changed = {path: text.replace("repeat: 6", "repeat: 5")}
    assert trellis.occurrence_removal_edit(shown, event, changed) == old
    assert (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8") == text

    # period.yml's list is the only one that holds cons, so its recipe row
    # leaves with the key (unit N, Task 5; N-D8)
    portfolio = emptied_portfolio(tmp_path / "portfolio")
    folder = model.open_folder(portfolio)
    shown = trellis.show_trellis(folder, RECIPE).shown
    period, spec = portfolio / "declaration/period.yml", portfolio / RECIPE_FILE
    path, text = str(period.resolve()), period.read_text(encoding="utf-8")
    spec_path, spec_text = str(spec.resolve()), spec.read_text(encoding="utf-8")
    (row,) = [line for line in spec_text.splitlines(True) if line.startswith("  cons:")]
    event = {
        "reading": trellis.reading_record(folder, shown),
        "occurrence": "periods[4]/cons___group___",
    }
    assert trellis.occurrence_removal_edit(shown, event, {}) == trellis.Gesture(
        {path: text.replace("  - cons\n", "", 1), spec_path: spec_text.replace(row, "")},
        {path: text, spec_path: spec_text},
        (),
        "period.yml, stages: cons removed, periods 0–5; spec.yml, stages: cons removed",
        None,
        path,
        "stages",
    )
    assert period.read_text(encoding="utf-8") == text


# The durables model's terminal period as trellis.yml writes it, before and
# after `bequest` is taken out, with the connector that joins bequest alone,
# and bequest's row of the recipe (unit N, Task 5)
DURABLES_TERMINAL = (
    "  - stages: [tenure, keeper_cons, adjuster_cons, bequest]\n",
    "  - stages: [tenure, keeper_cons, adjuster_cons]\n",
)
BEQUEST_ENTRY = (
    "{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, h_nxt_adj: h_bq, "
    "z_nxt_adj: z_bq}"
)
BEQUEST_ROW = (
    "  bequest:       {stage: stages/bequest/bequest.bl,             calibration: {all: "
    "[calibration/durables, $fill]}, methods: {all: [stages/bequest/methods]}, periods: [0, 0]}\n"
)


def test_n_5_an_occurrence_removed_from_its_stage_s_only_list_takes_the_recipe_row_too(tmp_path):
    """Unit N, Task 5 (N-D8; design pass 10 §7; `spec-factory.md` §2.6), by
    direct call. On a copy of the durables model, `bequest` removed from
    periods[0], whose list in trellis.yml is the only list that holds it,
    answers in one gesture trellis.yml without the key and without the
    entry of the connector that joins bequest alone, the period's other
    connector kept (decision MB-U30), and the recipe without
    bequest's row, which the factory would otherwise refuse under
    `recipe-template-agreement`; the note names the list, the row and the
    connector, in that order, and the gesture names the list. The trellis
    read from those texts is constructed and holds no bequest. `keeper_cons`
    removed from periods[1], whose list in period.yml is one of two that
    hold it, leaves the recipe as it stands. Nothing is written to disk."""
    copy = repository_copy(DURABLES, tmp_path / "durables")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, RECIPE).shown
    names = ("declaration/trellis.yml", RECIPE_FILE)
    texts = {name: (copy / name).read_text(encoding="utf-8") for name in names}
    paths = {name: str((copy / name).resolve()) for name in names}
    assert texts["declaration/trellis.yml"].count(DURABLES_TERMINAL[0]) == 1
    assert texts[RECIPE_FILE].count(BEQUEST_ROW) == 1
    made = {
        "declaration/trellis.yml": texts["declaration/trellis.yml"]
        .replace(*DURABLES_TERMINAL)
        .replace(f"      - {BEQUEST_ENTRY}\n", ""),
        RECIPE_FILE: texts[RECIPE_FILE].replace(BEQUEST_ROW, ""),
    }
    reading = trellis.reading_record(folder, shown)
    event = {"reading": reading, "occurrence": f"periods[0]/bequest{LAYER_ID_ENDING}"}
    assert trellis.occurrence_removal_edit(shown, event, {}) == trellis.Gesture(
        {paths[name]: made[name] for name in names},
        {paths[name]: texts[name] for name in names},
        (),
        "trellis.yml, periods[0].stages: bequest removed, periods 0; "
        "spec.yml, stages: bequest removed; "
        f"trellis.yml, periods[0].connectors[0]: {BEQUEST_ENTRY} removed, periods 0",
        None,
        paths["declaration/trellis.yml"],
        "periods[0].stages",
    )
    assert {name: (copy / name).read_text(encoding="utf-8") for name in names} == texts
    outcome = trellis.show_trellis(folder, RECIPE, previous=shown, unsaved=unsaved_of(copy, made))
    assert outcome.refusal is None
    assert all("bequest" not in period["stages"] for period in outcome.shown.trellis["periods"])

    event = {"reading": reading, "occurrence": f"periods[1]/keeper_cons{LAYER_ID_ENDING}"}
    gesture = trellis.occurrence_removal_edit(shown, event, {})
    assert gesture.sentence is None and paths[RECIPE_FILE] not in gesture.edits
    assert gesture.note.startswith("period.yml, stages: keeper_cons removed, periods 1–50;")
    assert "spec.yml" not in gesture.note
    assert trellis.occurrence_list(shown, (1, "keeper_cons")) == ("period.yml", "1–50")
    assert trellis.occurrence_list(shown, (0, "bequest")) == ("trellis.yml", "0")


# the package's sentence of a removal that the layout of a list does not
# admit as text, as its writers of `bellman.trellis` write it for `stages`
NOT_REMOVABLE = (
    "the layout of the file at stages does not admit the removal as text; remove the entry "
    "there by hand"
)


def test_k_a_writer_s_refusal_of_a_stage_removal_answers_its_own_sentence(tmp_path, monkeypatch):
    """Unit K's final judgment, §6 item 9, by direct call: where the
    package's writers refuse with a ValueError to take a stage occurrence's
    key out of the list that writes its period, the removal answers the
    writer's own sentence after the file's path from the model folder, as
    a drop's refusal does, and writes nothing, whether the trellis is read
    from a recipe, the portfolio model's, or from a trellis file, lesson
    05's; the writer is made to refuse with the sentence the package gives
    a layout that does not admit the removal."""

    def refusing(text: str, address: str, key: str):
        raise ValueError(NOT_REMOVABLE)

    monkeypatch.setattr(creation, "without_stage", refusing)
    portfolio = emptied_portfolio(tmp_path / "portfolio")
    lesson = applications_copy(tmp_path / "lesson")
    for copy, source, written, occurrence in (
        (portfolio, RECIPE, "declaration/period.yml", "periods[4]/cons___group___"),
        (lesson, LESSON, PORT_CONS, "periods[2]/disc___group___"),
    ):
        folder = model.open_folder(copy)
        shown = trellis.show_trellis(folder, source).shown
        before = (copy / written).read_text(encoding="utf-8")
        event = {"reading": trellis.reading_record(folder, shown), "occurrence": occurrence}
        assert trellis.occurrence_removal_edit(shown, event, {}) == trellis.Gesture(
            None,
            None,
            (),
            None,
            f"{written}: {NOT_REMOVABLE}",
            str((copy / written).resolve()),
            None,
        )
        assert (copy / written).read_text(encoding="utf-8") == before


# The connector of the pension model's periods[0], by which `shocks` joins
# `bequest_pa` in five pairs, its line in the trellis file, and the list of
# stages that holds both (unit L, Task 14)
BEQUEST_CONNECTOR = "{a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq}"
BEQUEST_CONNECTOR_LINE = f"      - {BEQUEST_CONNECTOR}\n"
BEQUEST_LISTED = "stages: [shocks, bequest_pa]"
# the note of the removal of `bequest_pa` from periods[0] with its joins
BEQUEST_REMOVED = (
    "trellis.pensions.yml, periods[0].stages: bequest_pa removed, periods 0; "
    f"trellis.pensions.yml, periods[0].connectors[0]: {BEQUEST_CONNECTOR} removed, periods 0"
)
PENSIONS_SOURCE = recipe.Source("recipe", PENSIONS_RECIPE)


def test_l_14_a_removed_stage_occurrence_takes_out_the_entries_its_joins_alone_need(tmp_path):
    """Unit L, Task 14 (defect 2 of the UX simulation; K-D14 amended), by
    direct call. On the pension model of the UX simulation at its first
    construction, `bequest_pa` removed from periods[0] takes its key out of
    the entry's `stages` and, in the same text of the trellis file, the
    connector that writes its five joins out of the entry's `connectors`,
    the list left `- {}`; the note names the key and the connector as a
    join's removal names it; the trellis read from that text is
    constructed, periods[0] holding `shocks` alone. On lesson 05 with two
    occurrences of the consumption stage, `cons_one` removed leaves the flat
    connector {w: m}, which `cons_two` still takes, and takes out the
    keyed connector that names `cons_one`; both trellises are constructed.
    Nothing is written to disk."""
    copy = pensions_copy(tmp_path / "pensions")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, PENSIONS_SOURCE).shown
    file = copy / PENSIONS_TRELLIS
    path, text = str(file.resolve()), file.read_text(encoding="utf-8")
    assert text.count(BEQUEST_LISTED) == 1 and text.count(BEQUEST_CONNECTOR_LINE) == 1
    event = {
        "reading": trellis.reading_record(folder, shown),
        "occurrence": f"periods[0]/bequest_pa{LAYER_ID_ENDING}",
    }
    removed = text.replace(BEQUEST_LISTED, "stages: [shocks]").replace(
        BEQUEST_CONNECTOR_LINE, "      - {}\n"
    )
    assert trellis.occurrence_removal_edit(shown, event, {}) == trellis.Gesture(
        {path: removed}, {path: text}, (), BEQUEST_REMOVED, None, path, "periods[0].stages"
    )
    assert file.read_text(encoding="utf-8") == text
    unsaved = unsaved_of(copy, {PENSIONS_TRELLIS: removed})
    outcome = trellis.show_trellis(folder, PENSIONS_SOURCE, previous=shown, unsaved=unsaved)
    assert outcome.refusal is None
    assert [list(period["stages"]) for period in outcome.shown.trellis["periods"]][0] == ["shocks"]

    flat = two_cons_period(tmp_path / "flat")
    (flat / PORT_CONS_RECORDS).write_text(
        (flat / PORT_CONS_RECORDS)
        .read_text(encoding="utf-8")
        .replace("      - {}\n", "      - {w: m}\n", 1),
        encoding="utf-8",
    )
    keyed = two_cons_one_joined(tmp_path / "keyed")
    connector = "{from: port, to: cons_one, fields: {w: m}}"
    for copy, kept in ((flat, True), (keyed, False)):
        folder = model.open_folder(copy)
        shown = trellis.show_trellis(folder, RECORDS).shown
        path = str((copy / PORT_CONS_RECORDS).resolve())
        text = (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8")
        (record,) = [line for line in text.splitlines(keepends=True) if "cons_one: {" in line]
        follows = text.splitlines(keepends=True)[text.splitlines(keepends=True).index(record) + 1]
        event = {
            "reading": trellis.reading_record(folder, shown),
            "occurrence": f"periods[2]/cons_one{LAYER_ID_ENDING}",
        }
        gesture = trellis.occurrence_removal_edit(shown, event, {})
        expected = text.replace(record + follows, "")
        note = "trellis.port-cons-vfi.yml, periods[0].stages: cons_one removed, periods 0–5"
        if not kept:
            expected = expected.replace(f"      - {connector}\n", "      - {}\n")
            note += (
                "; trellis.port-cons-vfi.yml, periods[0].connectors[0]: "
                f"{connector} removed, periods 0–5"
            )
        assert gesture == trellis.Gesture(
            {path: expected}, {path: text}, (), note, None, path, "periods[0].stages"
        ), copy
        unsaved = unsaved_of(copy, {PORT_CONS_RECORDS: expected})
        outcome = trellis.show_trellis(folder, RECORDS, previous=shown, unsaved=unsaved)
        assert outcome.refusal is None, copy


def test_l_14_a_drop_on_the_last_constructed_graph_lists_the_stage_and_names_its_joins(tmp_path):
    """An unresolved authored connector remains in an inspectable draft. Adding its missing stage activates the existing entries; adding a stage with duplicate local names does not give it another stage’s selected connections."""
    copy = pensions_copy(tmp_path / "pensions")
    folder = model.open_folder(copy)
    first = trellis.show_trellis(folder, PENSIONS_SOURCE).shown
    file = copy / PENSIONS_TRELLIS
    path, text = str(file.resolve()), file.read_text(encoding="utf-8")
    event = {
        "reading": trellis.reading_record(folder, first),
        "occurrence": f"periods[0]/bequest_pa{LAYER_ID_ENDING}",
    }
    removed = trellis.occurrence_removal_edit(first, event, {}).edits[path]
    shown = trellis.show_trellis(
        folder,
        PENSIONS_SOURCE,
        previous=first,
        unsaved=unsaved_of(copy, {PENSIONS_TRELLIS: removed}),
    ).shown
    typed = removed.replace("      - {}\n", BEQUEST_CONNECTOR_LINE)
    unsaved = unsaved_of(copy, {PENSIONS_TRELLIS: typed})
    draft = trellis.show_trellis(
        folder, PENSIONS_SOURCE, previous=shown, unsaved=unsaved
    )
    assert draft.refusal is None and draft.shown is not None
    assert any(d.rule == "endpoint-unresolved" and "a_bq" in d.message
               for d in draft.shown.selection.diagnostics)
    texts = trellis.texts_of(unsaved)
    target = f"periods[0]{LAYER_ID_ENDING}"
    drop = dropped_event(shown, folder, "bequest_pa", "stage", target)
    assert trellis.drop_edits(shown, drop, texts) == old_graph_gesture(file)
    pairs = "a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq"
    shown = draft.shown
    drop = dropped_event(shown, folder, "bequest_pa", "stage", target)
    assert trellis.drop_edits(shown, drop, texts) == trellis.Gesture(
        {path: text},
        {path: typed},
        (),
        "trellis.pensions.yml, periods[0].stages: bequest_pa written, periods 0; "
        f"trellis.pensions.yml, periods[0].connectors[0]: {pairs} now join bequest_pa",
        None,
        path,
        "periods[0].stages",
    )
    control = dropped_event(
        shown, folder, "bequest_pa", "stage", "between periods[1] and periods[0]"
    )
    assert trellis.drop_edits(shown, control, texts)["form"] == "add period"
    outcome = trellis.show_trellis(
        folder, PENSIONS_SOURCE, previous=shown, unsaved=unsaved_of(copy, {PENSIONS_TRELLIS: text})
    )
    assert outcome.refusal is None

    durables_bequest = creation.folder_template(str(copy / "declaration/stages/bequest"))
    entry = ("trellis.pensions.yml", "periods[0]")
    # neither stage receives a connection, and the note says so (unit N,
    # Task 5; design pass 10 §7)
    assert (
        trellis.added_stage_joins(first, copy, *entry, "bequest_dur", durables_bequest, {})
        == "bequest_dur unconnected"
    )
    assert trellis.added_stage_joins(first, copy, *entry, "port", PORT_ID, {}) == (
        "port unconnected"
    )


# The pension model at its first build of the working years (unit L, Task
# 15): the stage file of `allocation`; the period file whose `connectors` the
# working years and the year of enrollment take; the ten arrival fields that
# `contribution` joins to `allocation` by equal names, in the package's
# order, with their sets; and the two places at which the
# stage file writes the arrival field `w_c`, its listing in the header of
# `arvl_to_dcsn` and the line that reads it, each as written and as the
# rename to `w_in` writes it.
ALLOCATION = "declaration/stages/allocation/allocation.bl"
PENSIONS_PERIOD = "declaration/period.pensions.yml"
ALLOCATION_NAMES = (
    ("P_c", "ℝ₊₊"),
    ("adc_c", "ℝ₊"),
    ("adc_pre_c", "ℝ₊"),
    ("h_c", "ℝ₊"),
    ("m_c", "ℝ₊"),
    ("plan_c", "Plan"),
    ("w_c", "ℝ₊"),
    ("α_c", "(0, 1)"),
    ("β_c", "(0, 1)"),
    ("ξ_c", "ℝ"),
)
W_C_WRITTEN = (
    ("(w_c : ℝ₊, adc_c", "(w_in : ℝ₊, adc_c"),
    ("w_d       = w_c\n", "w_d       = w_in\n"),
)


def test_l_15_a_join_by_equal_names_is_a_join_wire_whose_reading_field_is_renamed(tmp_path):
    """An inferred arrow exposes both movable ends and its selected local field pairs. Details retains rename; renaming the reading field edits its stage source, leaves the other inferred pairs selected, and permits an explicit connector for the renamed field."""
    copy = pensions_copy(tmp_path / "pensions", PENSIONS_WORKING_YEARS)
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, PENSIONS_SOURCE).shown
    writer, reader = "periods[4]/contribution", "periods[4]/allocation"
    wire = {(w["from"], w["to"]): w for w in trellis.join_wires(shown)}[writer, reader]
    names = tuple(name for name, _ in ALLOCATION_NAMES)
    shown_keys = ("join", "between", "movable", "file", "removable")
    assert {key: wire[key] for key in shown_keys} == {
        "join": "; ".join(names),
        "between": False,
        "movable": ["writing", "reading"],
        "file": None,
        "removable": False,
    }
    assert {(f["field"], f["arrival"]) for f in wire["fields"]} == {(name, name) for name in names}
    rows = trellis.join_rows(folder, shown, wire)
    header_names = tuple(f["field"] for f in wire["fields"])
    assert (rows.place, rows.names, rows.removable) == (f"{writer} → {reader}", header_names, False)
    assert rows_text(rows.rows) == CONTRIBUTION_JOIN_ROWS
    event = join_event(shown, folder, writer, reader)
    nothing = trellis.Gesture(None, None, (), None, None, None, None)
    assert trellis.removal_edit(shown, event, {}) == nothing

    file = copy / ALLOCATION
    path, text = str(file.resolve()), file.read_text(encoding="utf-8")
    renamed = text
    for old, new in W_C_WRITTEN:
        assert renamed.count(old) == 1
        renamed = renamed.replace(old, new)
    assert changed_lines(text, renamed) == [22, 23] and "dV_w_c[<]" in renamed

    def rename(name: str, field: str = "w_c"):
        return trellis.rename_edit(shown, {**event, "field": field, "name": name}, {})

    assert rename(" w_in ") == trellis.Gesture(
        {path: renamed},
        {path: text},
        (),
        "allocation.bl, lines 22–23: w_c renamed to w_in",
        None,
        path,
        None,
    )
    assert file.read_text(encoding="utf-8") == text
    for name, why in (
        ("w_d", "The stage file already writes w_d. Type another name."),
        ("2w", "2w is no name of the language. Type a name that begins with a letter."),
        ("_w", "_w is no name of the language. Type a name that begins with a letter."),
        ("", "No name was typed. Type a name that begins with a letter."),
    ):
        sentence = f"allocation.bl: nothing was written. {why}"
        assert rename(name) == trellis.Gesture(None, None, (), None, sentence, path, None)
    assert rename("w_c") == nothing
    old = rename("w_in", field="dV_w_c")
    assert (old.edits, old.sentence) == (
        None,
        "trellis.pensions.yml: nothing was written. The graph was drawn from an earlier text. "
        "Rename the field again in the graph now drawn.",
    )

    # the renamed text saved: the two fields unjoined, nine other joins kept
    file.write_text(renamed, encoding="utf-8")
    saved = trellis.show_trellis(folder, PENSIONS_SOURCE, previous=shown)
    assert saved.refusal is None
    unjoined = {
        (port["side"], port["h"], port["key"], port["field"])
        for port in trellis.unjoined_ports(saved.shown, {})
    }
    freed = {("writing", h, "contribution", "w_c") for h in (4, 5, 6)}
    freed |= {("reading", h, "allocation", "w_in") for h in (4, 5, 6)}
    assert freed <= unjoined
    kept = {(w["from"], w["to"]): w for w in trellis.join_wires(saved.shown)}[writer, reader]
    assert trellis.join_rows(folder, saved.shown, kept).names == tuple(
        name for name in header_names if name != "w_c"
    )

    # a drag from the one to the other joins them through the period file
    ports = (4, "contribution", "w_c"), (4, "allocation", "w_in")
    drag = trellis.connector_edit(saved.shown, connected_event(saved.shown, folder, *ports), {})
    period = str((copy / PENSIONS_PERIOD).resolve())
    assert drag.note == "period.pensions.yml, connectors: {w_c: w_in} written, flat, periods 4–6"
    assert list(drag.edits) == [period]
    assert entry_value(drag.edits[period], "connectors") == [{"w_c": "w_in"}]
    unsaved = unsaved_of(copy, {PENSIONS_PERIOD: drag.edits[period]})
    joined = trellis.show_trellis(folder, PENSIONS_SOURCE, previous=saved.shown, unsaved=unsaved)
    assert joined.refusal is None
    unjoined = {
        (port["side"], port["h"], port["key"], port["field"])
        for port in trellis.unjoined_ports(joined.shown, trellis.texts_of(unsaved))
    }
    assert not freed & unjoined


# --- the acceptance items of unit B (§12, "B, binding and the trellis") ---


def test_b_item_2_the_stage_view_of_the_heads_occurrence_equals_the_trellis_view_up_to_the_joins(
    consport_folder,
):
    """B item 2 (§3.1: "two surfaces present one position"): for three
    occurrences of the trellis of lesson 05, the stage file elaborated with
    the origin its record writes and bound as that occurrence, the page's
    own route (`recipe.find_occurrence`, `recipe.bind_occurrence`), has the
    view the trellis draws for the occurrence, node for node, port for port
    and builder for builder, but for the edges and the port attributes of
    the joins."""
    folder = model.open_folder(consport_folder)
    shown = trellis.show_trellis(folder, LESSON).shown
    for position in ((1, "cons"), (0, "port"), (5, "disc")):
        relpath = trellis.occurrence_file(folder, shown, position)
        found = recipe.find_occurrence(folder, LESSON, relpath, position)
        assert found.position == position
        stage = elaborate_text(Path(found.origin).read_text(encoding="utf-8"), found.origin)
        view = model.collection(recipe.bind_occurrence(stage, found).stage)
        occurrence = f"periods[{position[0]}]/{position[1]}"
        for graph in ("backward", "forward"):
            assert as_json(stage_nodes(view, graph)) == as_json(
                occurrence_nodes(shown.collection, graph, occurrence)
            ), (position, graph)
            layers = graph_named(shown.collection, graph)["groupNodeAttributes"]
            for namespace, rows in graph_named(view, graph)["groupNodeAttributes"].items():
                assert layers[f"{occurrence}/{namespace}"] == rows, (position, namespace)


def test_b_item_5_every_drawn_backward_join_names_the_rule_that_paired_it(
    pension_folder, consport_folder
):
    """B item 5 (§3.1): the pension trellis's backward graph is the one
    refusing node, its rows the sixty unpaired joins, and its forward graph
    is drawn; restricted to `periods 1–1`, its backward graph is drawn; there,
    as in the whole trellis of lesson 05, every reading port a drawn join
    supplies names the join and the rule that paired its wire, one of the
    package's three, and a port of a join that leaves the view names the
    occurrence outside and no rule."""
    rules = {"declared coordinate", "one wire per role", "equal name"}
    pension = model.open_folder(pension_folder)
    whole = trellis.show_trellis(pension, RECIPE).shown
    (refusing,) = graph_named(whole.collection, "backward")["nodes"]
    assert refusing["id"] == "backward:refused"
    assert len([pair for pair in refusing["attrs"] if pair["key"].startswith("join")]) == 60
    assert len(graph_named(whole.collection, "forward")["nodes"]) > 1
    for folder, source, typed in (
        (pension, RECIPE, "periods 1–1"),
        (model.open_folder(consport_folder), LESSON, ""),
    ):
        shown = trellis.show_trellis(folder, source, trellis.parse_restriction(typed)).shown
        ports = [
            {pair["key"]: pair["value"] for pair in item["attrs"]}
            for node in graph_named(shown.collection, "backward")["nodes"]
            for item in node.get("inputsMetadata") or []
        ]
        drawn = [port for port in ports if "join" in port and "outside" not in port]
        assert drawn, source
        assert all(
            port.get("paired by") and set(port["paired by"].split("; ")) <= rules for port in drawn
        )
        assert all("paired by" not in port for port in ports if "outside" in port)


# --- the acceptance items of the brief on the trellis view's load time,
# `trellis-load-time.md` §3 ---

# The script of item 2, run in a fresh process: one reading of the durables
# trellis in the folder its first argument names, under `periods 0–2`; its
# verbs bound and refused, the occurrences shown and the reading's seconds
# are printed as one line of JSON.
FIRST_READING = """\
import json
import sys

from bellman_workbench import model, recipe, trellis

shown = trellis.show_trellis(
    model.open_folder(sys.argv[1]),
    recipe.Source("recipe", "declaration/spec.yml"),
    trellis.parse_restriction("periods 0–2"),
).shown
print(
    json.dumps(
        {
            "bound": list(shown.binding.bound),
            "failed": list(shown.binding.failed),
            "shown": shown.counts["shown"],
            "seconds": shown.seconds,
        }
    )
)
"""


def test_trellis_load_item_2_the_first_reading_of_durables_binds_two_verbs_and_prints_its_seconds(
    tmp_path,
):
    """Item 2: a copy of the durables folder read in a fresh process, whose
    cache folder `XDG_CACHE_HOME` is empty, under `periods 0–2`, binds
    `methodize` and `configure` and reports `calibrate` refused, since the
    calibration supplies no value for the tenure stage's `Y`; it shows the
    ten occurrences of periods 0 to 2. A second fresh process with the same
    cache folder, which then holds the stage views the first process wrote,
    reports the same binding and shows the same ten occurrences. The
    `TrellisShown.seconds` of each reading, which depend on the machine's
    load, are printed and not asserted, and the brief's bounds, 5 s with the
    cache folder empty and 3 s with it holding the stage views, are checked
    by the measurement script of the run folder
    `2026-10-03-trellis-load-time/` of the internal verification records and
    recorded in its report."""
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    command = [sys.executable, "-c", FIRST_READING, str(durables)]
    environment = {**os.environ, "XDG_CACHE_HOME": str(cache)}

    def read_in_a_fresh_process() -> dict:
        """The answer the script prints, the last line of its output."""
        run = subprocess.run(command, env=environment, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        return json.loads(run.stdout.splitlines()[-1])

    first = read_in_a_fresh_process()
    print(f"item 2 first reading: {first['seconds']:.3f} s")
    assert (first["bound"], first["failed"], first["shown"]) == (
        ["methodize", "configure"],
        ["calibrate"],
        10,
    )
    # the first process wrote the stage views into the cache folder
    assert any((cache / "bellman-workbench/views").rglob("*.json"))
    second = read_in_a_fresh_process()
    print(f"item 2 second reading: {second['seconds']:.3f} s")
    assert (second["bound"], second["failed"], second["shown"]) == (
        ["methodize", "configure"],
        ["calibrate"],
        10,
    )


def test_trellis_load_item_3_a_trellis_of_more_than_six_periods_opens_on_periods_0_2(
    pension_folder, consport_folder
):
    """Item 3: the text the view's bar opens with for a syntactic trellis,
    `opening_restriction`. The trellises of the durables recipe `spec.yml`,
    of 51 periods, and of the pension recipe, of 15, open on `periods 0–2`,
    which the parser reads as periods 0 to 2, the terminal period and the
    two before it; the trellis of lesson 05, of six periods,
    `OPEN_PERIODS_WHOLE` itself, opens with no restriction, whole."""
    durables = load_recipe(ROOT / "applications/durables/declaration", "spec.yml")
    pension = load_recipe(pension_folder / "declaration", "spec.yml")
    lesson = recipe.read_source(model.open_folder(consport_folder), LESSON)
    found = [
        (len(syntactic["periods"]), trellis.opening_restriction(syntactic))
        for syntactic in (durables, pension, lesson)
    ]
    assert found == [(51, "periods 0–2"), (15, "periods 0–2"), (6, None)]
    assert trellis.parse_restriction(found[0][1]).periods == (0, 1, 2)


def test_trellis_load_item_4_a_new_restriction_copies_nothing_and_a_save_constructs_one_text(
    tmp_path, monkeypatch
):
    """Item 4, on a copy of the durables folder: a reading under `periods
    0–2`, then one under `periods 0–10` with no file written and the first
    as its `previous`. The second reading's syntactic trellis and bound
    trellis are the first reading's objects; no position changed, no stage
    text is constructed, no occurrence is copied, and it answers in under
    half a second. The same restriction once more answers the second
    reading itself. A comment appended to `keeper_cons.bl` then reads the
    trellis again: that file's text alone is constructed, once, and the
    keeper's 51 occurrences alone are bound and copied, the others kept
    (`respecify_trellis`; unit L, Task 20), so that the positions changed
    are the keeper's 51. The constructions and the copies are counted by
    patching `construct_stage` and `copy_native` in the factory's module,
    as `test_item_2` of `packages/bellman/tests/test_amd_fac_002.py` counts
    the constructions."""
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    folder = model.open_folder(durables)
    first = trellis.show_trellis(folder, RECIPE, trellis.parse_restriction("periods 0–2")).shown
    constructions, construct = [], factory_trellis.construct_stage
    copies, copy = [], factory_trellis.copy_native
    monkeypatch.setattr(
        factory_trellis,
        "construct_stage",
        lambda text, origin, additions=(): constructions.append(origin)
        or construct(text, origin, additions),
    )
    monkeypatch.setattr(
        factory_trellis, "copy_native", lambda stage: copies.append(stage.name) or copy(stage)
    )
    wider = trellis.parse_restriction("periods 0–10")
    outcome = trellis.show_trellis(folder, RECIPE, wider, first)
    second = outcome.shown
    assert second.syntactic is first.syntactic and second.trellis is first.trellis
    assert second.changed == [] and (constructions, copies) == ([], [])
    assert outcome.seconds < 0.5, outcome.seconds
    assert second.restriction == wider and second.counts["shown"] == 34
    assert trellis.show_trellis(folder, RECIPE, wider, second).shown is second
    keeper = durables / "declaration/stages/keeper_cons/keeper_cons.bl"
    keeper.write_text(keeper.read_text(encoding="utf-8") + "\n# a comment\n", encoding="utf-8")
    third = trellis.show_trellis(folder, RECIPE, wider, second).shown
    assert [Path(origin).name for origin in constructions] == ["keeper_cons.bl"]
    assert copies == ["keeper_cons"] * 51 and third.alone == ("keeper_cons",)
    assert sorted(third.changed) == [(h, "keeper_cons") for h in range(51)]


# The script of the test of the cache folder, run in a fresh process: one
# reading of the durables trellis in the folder its first argument names,
# under `periods 0–2`, each stage view the exporter computes counted at the
# function that computes it, `_graph`. Printed as one line of JSON: that
# count; the number of distinct versions in periods 0 to 2
# (`_version_key`); for each view the process holds (`_VIEW_CACHE`),
# whether its entry in the cache folder rebuilds an object equal to it; and
# the collection drawn.
COUNTED_READING = """\
import json
import sys

from bellman.factory import model_explorer
from bellman_workbench import model, recipe, trellis

computed = []
compute = model_explorer._graph
compute_initial = model_explorer._initial_graph


def counted(graph_builder, stage, direction):
    computed.append(direction)
    return compute(graph_builder, stage, direction)


def counted_initial(graph_builder, stage, direction):
    computed.append(direction + " initial diagram")
    return compute_initial(graph_builder, stage, direction)


model_explorer._graph = counted
model_explorer._initial_graph = counted_initial
shown = trellis.show_trellis(
    model.open_folder(sys.argv[1]),
    recipe.Source("recipe", "declaration/spec.yml"),
    trellis.parse_restriction("periods 0–2"),
).shown
# the initial diagrams, which the page asks for once its Initial view is chosen (S-D30)
shown = trellis.with_initial_diagrams(shown)
graph_builder = model_explorer._viewer()
print(
    json.dumps(
        {
            "computed": len(computed),
            "versions": len(
                {
                    model_explorer._version_key(stage)
                    for period in shown.trellis["periods"][:3]
                    for stage in period["stages"].values()
                }
            ),
            "rebuilt": [
                model_explorer._read_entry(graph_builder, model_explorer._view_entry(key)) == view
                for key, view in model_explorer._VIEW_CACHE.items()
            ],
            "collection": shown.collection,
        }
    )
)
"""


def test_trellis_load_the_stage_views_are_kept_in_the_cache_folder_between_processes(tmp_path):
    """Change 4: a version's stage view, in each direction, is kept as one
    JSON file, its entry, in `bellman-workbench/views/<package version>/`
    under the cache folder `XDG_CACHE_HOME`, the package version being the
    version `package_version` answers, a hyphen and twelve hexadecimal
    digits of the digest of the package's source; since design pass 14 §7
    the trellis's initial diagram of each direction is kept the same way
    once the Initial view asks for it (S-D30), four views for each
    version. Three fresh processes
    read a copy of the durables folder under `periods 0–2`, the cache
    folder at an empty folder of the test's own. The first computes the four
    views of each of the four versions once and writes one entry
    for each, and each entry rebuilds an object equal to the view it was
    written from. The second computes no stage view, writes no entry and
    draws a collection equal to the first's. The third, after one entry was
    overwritten with text that is no JSON and another moved into the folder
    of another package version, computes those two views alone, writes
    their two entries again as they were and draws the same collection. No
    reading writes a file into the model folder."""
    durables = shutil.copytree(
        ROOT / "applications/durables",
        tmp_path / "durables",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    model_files = file_bytes(durables)
    cache = tmp_path / "cache"
    cache.mkdir()
    command = [sys.executable, "-c", COUNTED_READING, str(durables)]
    environment = {**os.environ, "XDG_CACHE_HOME": str(cache)}

    def read_in_a_fresh_process() -> dict:
        """The answer the script prints, the last line of its output."""
        run = subprocess.run(command, env=environment, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        return json.loads(run.stdout.splitlines()[-1])

    first = read_in_a_fresh_process()
    views = cache / "bellman-workbench/views"
    (folder,) = views.iterdir()
    assert re.fullmatch(re.escape(package_version()) + "-[0-9a-f]{12}", folder.name)
    entries = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in folder.iterdir()
    }
    # every file of the folder is an entry named by a SHA-256 digest
    assert all(re.fullmatch(r"[0-9a-f]{64}\.json", name) for name in entries)
    # one entry for each distinct version and each of its four views, the
    # builders graph and the initial diagram of each direction
    assert first["versions"] == 4
    assert first["computed"] == len(entries) == 4 * first["versions"]
    assert first["rebuilt"] == [True] * len(entries)
    second = read_in_a_fresh_process()
    assert second["computed"] == 0
    assert second["collection"] == first["collection"]
    # no entry was written again
    assert {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in folder.iterdir()
    } == entries
    damaged, moved = sorted(entries)[:2]
    (folder / damaged).write_text("no view", encoding="utf-8")
    other = views / "0.0.0-000000000000"
    other.mkdir()
    (folder / moved).rename(other / moved)
    third = read_in_a_fresh_process()
    # the two views computed are those of the damaged and the moved entries
    assert third["computed"] == 2
    assert third["collection"] == first["collection"]
    assert {path.name: path.read_bytes() for path in folder.iterdir()} == {
        name: written for name, (written, _) in entries.items()
    }
    assert file_bytes(durables) == model_files


# --- the binding kept on disk (ruling G-R81) ---

# the line the tests of the binding kept on disk append to a stage file
COMMENT = "\n# a comment\n"


def test_a_reading_from_a_kept_binding_answers_what_a_reading_that_binds_answers(
    model_folder, durables_folder, specify_calls
):
    """Claim (a): the portfolio trellis whole, and the durables trellis under
    `periods 0–2`, each read once with no trellis before it, which binds,
    and its binding kept (`keep_binding`); read again with no trellis
    before it, each reads the entry, calls `specify_trellis` not once, and
    answers the first reading's collection, layers and counts and its
    binding's verbs bound, skipped and failed."""
    for path, typed in ((model_folder, ""), (durables_folder, "periods 0–2")):
        folder = model.open_folder(path)
        restriction = trellis.parse_restriction(typed)
        called = len(specify_calls)
        bound = trellis.show_trellis(folder, RECIPE, restriction).shown
        assert len(specify_calls) > called
        trellis.keep_binding(bound, None)
        assert trellis.binding_entry(bound.syntactic).is_file()
        called = len(specify_calls)
        read = trellis.show_trellis(folder, RECIPE, restriction).shown
        assert len(specify_calls) == called, path.name
        assert (read.collection, read.layers, read.counts) == (
            bound.collection,
            bound.layers,
            bound.counts,
        )
        assert (read.binding.bound, read.binding.skipped, read.binding.failed) == (
            bound.binding.bound,
            bound.binding.skipped,
            bound.binding.failed,
        )


def test_a_change_of_any_file_the_trellis_reads_binds_the_trellis_again(
    scratch_folder, specify_calls
):
    """Claim (b): the portfolio trellis read and its binding kept; then one
    file of each kind the trellis reads changed, a stage file, the
    calibration, a methods and a settings source, the recipe, the period
    file and the trellis file, each written back before the next: every
    reading of a changed file, with no trellis before it, binds the trellis
    and names another entry, and the reading after the last file is
    written back reads the first reading's entry."""
    folder = model.open_folder(scratch_folder)
    first = trellis.show_trellis(folder, RECIPE).shown
    trellis.keep_binding(first, None)
    declaration = scratch_folder / "declaration"
    # each file by its path from `declaration/`, with the text replaced and
    # its replacement, None for the comment appended
    for name, written, replaced in (
        ("stages/disc/disc.bl", None, COMMENT),
        ("calibration/portfolio.yml", "β: 0.96", "β: 0.95"),
        ("stages/port/methods.yml", "cons-port:transition", "cons-port:another_transition"),
        ("settings/cons.yml", "n_a: 800", "n_a: 400"),
        (
            "spec.yml",
            "disc: {stage: stages/disc/disc.bl, calibration: {all: [calibration/portfolio]}",
            "disc: {stage: stages/disc/disc.bl, calibration: {all: [calibration/portfolio], "
            "0-0: [calibration/portfolio]}",
        ),
        ("period.yml", "  - port\n  - cons\n", "  - cons\n  - port\n"),
        ("trellis.yml", "repeat: 6", "repeat: 5"),
    ):
        path = declaration / name
        text = path.read_text(encoding="utf-8")
        changed = text + replaced if written is None else text.replace(written, replaced)
        assert changed != text, name
        path.write_text(changed, encoding="utf-8")
        called = len(specify_calls)
        again = trellis.show_trellis(folder, RECIPE).shown
        assert len(specify_calls) > called, name
        assert trellis.binding_entry(again.syntactic) != trellis.binding_entry(first.syntactic)
        path.write_text(text, encoding="utf-8")
    called = len(specify_calls)
    assert trellis.show_trellis(folder, RECIPE).shown.collection == first.collection
    assert len(specify_calls) == called


def test_a_reading_after_one_from_a_kept_binding_answers_what_a_reading_without_it_answers(
    scratch_folder, specify_calls
):
    """Claim (c): the portfolio trellis read, its binding kept and read
    again from the entry, with no call of `specify_trellis`; a comment then
    appended to `disc.bl`, the reading with the reading from the entry as
    `previous` answers the collection, the layers, the counts and the
    verbs of a reading with no trellis before it, and names as changed the
    six positions of `disc` alone."""
    folder = model.open_folder(scratch_folder)
    trellis.keep_binding(trellis.show_trellis(folder, RECIPE).shown, None)
    called = len(specify_calls)
    read = trellis.show_trellis(folder, RECIPE).shown
    assert len(specify_calls) == called
    stage_file = scratch_folder / "declaration/stages/disc/disc.bl"
    stage_file.write_text(stage_file.read_text(encoding="utf-8") + COMMENT, encoding="utf-8")
    again = trellis.show_trellis(folder, RECIPE, previous=read).shown
    alone = trellis.show_trellis(folder, RECIPE).shown
    assert sorted(again.changed) == [(h, "disc") for h in range(6)]
    assert (again.collection, again.layers, again.counts) == (
        alone.collection,
        alone.layers,
        alone.counts,
    )
    assert (again.binding.bound, again.binding.skipped, again.binding.failed) == (
        alone.binding.bound,
        alone.binding.skipped,
        alone.binding.failed,
    )


def records_of(binding: trellis.TrellisBinding) -> tuple:
    """The records of a binding as the standard pickle writes them: the
    trellis's entries but its stage occurrences, then each occurrence's
    bindings and provenance by its position; and the verbs bound, skipped
    and failed. A drawn view leaves answers inside an occurrence's graphs,
    which the pickle writes, so the graphs are compared by equality."""
    shape = {
        **binding.trellis,
        "periods": [
            {**period, "stages": list(period["stages"])} for period in binding.trellis["periods"]
        ],
    }
    occurrences = {
        (h, key): pickle.dumps((stage.bindings, stage.provenance))
        for h, period in enumerate(binding.trellis["periods"])
        for key, stage in period["stages"].items()
    }
    return pickle.dumps(shape), occurrences, binding.bound, binding.skipped, binding.failed


def test_l_20_a_change_of_one_stage_s_sources_binds_that_stage_alone(tmp_path):
    """Unit L, Task 20 (defect 14 of the UX simulation). On the pension
    model at its first build of the working years, whose calibration the
    package refuses at `periods[0] / shocks`: a comment appended to the
    renter's methods file, a change of one stage's sources alone, binds the
    renter's occurrences alone, `alone` naming `renter_cons` and the status
    line's loop `for renter_cons`; every other occurrence is the object the
    trellis shown before holds, and the refusal of the calibration stands.
    The binding equals the whole binding of the same files, its records byte
    for byte and its trellis by equality, and the view equals the view of a
    reading with no trellis before it. A comment appended to the shocks
    calibration, the file of the refused position, and one appended to the
    trellis file each bind the whole trellis, `alone` empty, the refusal
    standing."""
    folder_path = pensions_copy(tmp_path / "durables", PENSIONS_WORKING_YEARS)
    folder, source = model.open_folder(folder_path), recipe.Source("recipe", PENSIONS_RECIPE)
    first = trellis.show_trellis(folder, source).shown
    assert first.alone == () and first.binding.bound == ("methodize",)
    refused_at = "Stage occurrence: periods[0].stages['shocks']"
    assert first.binding.failed["calibrate"].endswith(refused_at)
    declaration = folder_path / "declaration"
    methods = declaration / "stages/renter_cons/methods.yml"
    methods.write_text(methods.read_text(encoding="utf-8") + COMMENT, encoding="utf-8")
    again = trellis.show_trellis(folder, source, previous=first).shown
    renter = [
        (h, "renter_cons")
        for h, period in enumerate(first.trellis["periods"])
        if "renter_cons" in period["stages"]
    ]
    assert again.alone == ("renter_cons",) and again.changed == renter and len(renter) == 6
    for h, period in enumerate(again.trellis["periods"]):
        for key, stage in period["stages"].items():
            held = first.trellis["periods"][h]["stages"][key]
            assert (stage is held) == (key != "renter_cons"), (h, key)
    whole = trellis.bind_trellis(None, again.syntactic)
    assert records_of(again.binding) == records_of(whole) and again.trellis == whole.trellis
    fresh = trellis.show_trellis(folder, source).shown
    assert as_json(again.collection) == as_json(fresh.collection) and fresh.alone == ()
    outcome = trellis.TrellisOutcome(again, None, None, again.seconds, again.files)
    line, _ = app.trellis_status_parts(outcome, again)
    loop = f" · loop {again.seconds:.2f} s for renter_cons"
    assert "".join(text for text, _ in line).endswith(loop)
    line, _ = app.trellis_status_parts(outcome, first)
    assert "".join(text for text, _ in line).endswith(f" · loop {first.seconds:.2f} s")

    # the file of the refused position, and the trellis file: the whole trellis
    calibration = declaration / "calibration/shocks.yml"
    calibration.write_text(calibration.read_text(encoding="utf-8") + COMMENT, encoding="utf-8")
    third = trellis.show_trellis(folder, source, previous=again).shown
    assert third.alone == () and third.binding.failed == first.binding.failed
    trellis_file = declaration / "trellis.pensions.yml"
    trellis_file.write_text(trellis_file.read_text(encoding="utf-8") + COMMENT, encoding="utf-8")
    fourth = trellis.show_trellis(folder, source, previous=third).shown
    assert fourth.alone == () and fourth.binding.failed == first.binding.failed


def test_an_entry_that_is_no_binding_is_deleted_and_replaced_by_the_new_binding(
    model_folder, specify_calls
):
    """Claim (d): the entry of the portfolio trellis overwritten with bytes
    that `pickle` cannot read, and then with a list pickled: each reading
    with no trellis before it deletes the file and binds the trellis, and
    the binding then kept stands in the entry, a `TrellisBinding` with the
    reading's verbs."""
    folder = model.open_folder(model_folder)
    first = trellis.show_trellis(folder, RECIPE).shown
    trellis.keep_binding(first, None)
    entry = trellis.binding_entry(first.syntactic)
    for written in (b"no binding", pickle.dumps(["another type"])):
        entry.write_bytes(written)
        called = len(specify_calls)
        again = trellis.show_trellis(folder, RECIPE).shown
        assert len(specify_calls) > called and not entry.exists()
        trellis.keep_binding(again, None)
        kept = pickle.loads(entry.read_bytes())
        assert isinstance(kept, trellis.TrellisBinding)
        assert (kept.bound, kept.skipped, kept.failed) == (
            again.binding.bound,
            again.binding.skipped,
            again.binding.failed,
        )


def test_a_write_removes_other_code_versions_and_keeps_the_eight_entries_used_last(
    scratch_folder, own_cache_folder
):
    """Claim (e): the entry of the portfolio trellis, its modification time
    set back a day, beside nine other entries written in the last quarter
    hour, and a folder of another code version; the entry then read, and
    the trellis of the folder with a comment appended to `disc.bl` bound and
    kept. The write removes the other code version's folder and leaves
    eight entries, the most recently used: the one written, the one read
    and the six latest of the nine."""
    folder = model.open_folder(scratch_folder)
    first = trellis.show_trellis(folder, RECIPE).shown
    trellis.keep_binding(first, None)
    entry = trellis.binding_entry(first.syntactic)
    now = time.time_ns()
    os.utime(entry, ns=(now - 86_400 * 10**9,) * 2)
    others = [entry.with_name(f"{number:064x}.pickle") for number in range(9)]
    for number, other in enumerate(others):
        other.write_bytes(b"")
        os.utime(other, ns=(now - (900 - number) * 10**9,) * 2)
    version = entry.parent.parent / ("0" * 64)
    version.mkdir()
    (version / f"{'1' * 64}.pickle").write_bytes(b"")
    trellis.show_trellis(folder, RECIPE)
    stage_file = scratch_folder / "declaration/stages/disc/disc.bl"
    stage_file.write_text(stage_file.read_text(encoding="utf-8") + COMMENT, encoding="utf-8")
    second = trellis.show_trellis(folder, RECIPE).shown
    trellis.keep_binding(second, None)
    written = trellis.binding_entry(second.syntactic)
    assert set(kept_bindings(own_cache_folder)) == {
        f"{trellis.code_version()}/{path.name}" for path in (written, entry, *others[3:])
    }


def test_a_refused_reading_and_a_reading_given_its_own_source_keep_nothing(
    cagetti_folder, scratch_folder, own_cache_folder
):
    """Claim (f): the Cagetti–De Nardi trellis file, which the factory
    refuses, read with no trellis before it: its outcome given to
    `keep_binding` keeps nothing. The portfolio trellis read, a comment
    appended to `disc.bl`, and the trellis read again with the first
    reading as `previous`, and then once more with that reading as
    `previous`: neither reading, given with its `previous`, keeps
    anything."""
    refused = trellis.show_trellis(
        model.open_folder(cagetti_folder), recipe.Source("trellis", "declaration/trellis.yml")
    )
    assert refused.shown is None
    trellis.keep_binding(refused.shown, None)
    assert kept_bindings(own_cache_folder) == {}
    folder = model.open_folder(scratch_folder)
    first = trellis.show_trellis(folder, RECIPE).shown
    stage_file = scratch_folder / "declaration/stages/disc/disc.bl"
    stage_file.write_text(stage_file.read_text(encoding="utf-8") + COMMENT, encoding="utf-8")
    second = trellis.show_trellis(folder, RECIPE, previous=first).shown
    trellis.keep_binding(second, first)
    third = trellis.show_trellis(folder, RECIPE, previous=second).shown
    trellis.keep_binding(third, second)
    assert kept_bindings(own_cache_folder) == {}


@pytest.mark.skipif(os.name != "posix", reason="a folder's mode is POSIX's")
def test_the_folders_of_the_bindings_are_the_users_alone(model_folder):
    """Claim (g): the binding of the portfolio trellis kept, the folders
    `bindings/` and `bindings/<code version>/` it creates have the mode
    0o700, read, written and searched by their owner alone."""
    shown = trellis.show_trellis(model.open_folder(model_folder), RECIPE).shown
    trellis.keep_binding(shown, None)
    entry = trellis.binding_entry(shown.syntactic)
    modes = [stat.S_IMODE(path.stat().st_mode) for path in (entry.parent.parent, entry.parent)]
    assert modes == [0o700, 0o700]


def test_with_no_code_version_no_binding_is_read_or_written(
    model_folder, own_cache_folder, specify_calls, monkeypatch
):
    """Claim (h): the binding of the portfolio trellis kept; then, with no
    code version (`code_version` answering None), no entry is named, a
    reading with no trellis before it binds the trellis and leaves the
    entry's modification time as it was, and, the entry deleted, the
    binding given to `keep_binding` writes nothing."""
    folder = model.open_folder(model_folder)
    first = trellis.show_trellis(folder, RECIPE).shown
    trellis.keep_binding(first, None)
    entry = trellis.binding_entry(first.syntactic)
    kept = kept_bindings(own_cache_folder)
    assert len(kept) == 1
    monkeypatch.setattr(trellis, "code_version", lambda: None)
    assert trellis.binding_entry(first.syntactic) is None
    called = len(specify_calls)
    again = trellis.show_trellis(folder, RECIPE).shown
    assert len(specify_calls) > called
    assert kept_bindings(own_cache_folder) == kept
    entry.unlink()
    trellis.keep_binding(again, None)
    assert kept_bindings(own_cache_folder) == {}


@pytest.mark.skipif(
    os.name != "posix" or os.geteuid() == 0,
    reason="a folder's mode is POSIX's, and the superuser searches any folder",
)
def test_a_binding_under_a_folder_that_cannot_be_searched_is_kept_nowhere_and_raises_nothing(
    pension_folder, own_cache_folder
):
    """Claim (3) of G-R81: the binding of the pension trellis given to
    `keep_binding` while the cache folder cannot be searched (mode 0o000)
    and `Path.exists` raises `PermissionError`, as it does there on Python
    3.12 and 3.13: `keep_binding` answers None, raises nothing and writes
    nothing into the cache folder."""
    shown = trellis.show_trellis(model.open_folder(pension_folder), RECIPE).shown
    assert shown is not None
    before = sorted(own_cache_folder.rglob("*"))
    mode = stat.S_IMODE(own_cache_folder.stat().st_mode)

    def refused(path, *args, **kwargs):
        """Raises the error `Path.exists` raises on Python 3.12 and 3.13
        for a path under a folder that cannot be searched."""
        raise PermissionError(13, "Permission denied", str(path))

    own_cache_folder.chmod(0o000)
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(Path, "exists", refused)
            assert trellis.keep_binding(shown, None) is None
    finally:
        own_cache_folder.chmod(mode)
    assert sorted(own_cache_folder.rglob("*")) == before


@pytest.mark.skipif(os.name != "posix", reason="a folder's mode is POSIX's")
def test_an_entry_whose_folder_its_group_can_write_is_not_read(pension_folder):
    """The binding of the pension trellis kept, and its entry's folder made
    writable by its group (mode 0o770): `read_binding` answers None and the
    entry stands; the folder's mode set back to 0o700, `read_binding` reads
    the entry again."""
    shown = trellis.show_trellis(model.open_folder(pension_folder), RECIPE).shown
    assert shown is not None
    trellis.keep_binding(shown, None)
    entry = trellis.binding_entry(shown.syntactic)
    entry.parent.chmod(0o770)
    assert trellis.read_binding(shown.syntactic) is None
    assert entry.is_file()
    entry.parent.chmod(0o700)
    assert isinstance(trellis.read_binding(shown.syntactic), trellis.TrellisBinding)


def test_the_code_version_digests_the_sources_of_both_packages_and_the_versions(tmp_path):
    """`code_version` is `code_digest` of the two installed folders and the
    installed versions. `code_digest` of two folders written for the test,
    `bellman` with a `pyproject.toml` beside it and `bellman_workbench`:
    the same inputs give the same digest; a changed byte of a `.py` file, a
    renamed `.py` file, a changed `.lark` file of the package and a changed
    version each give a digest none before gave; a file of another suffix
    added to either folder leaves the digest as it was."""
    installed = Path(importlib.util.find_spec("bellman").origin).resolve().parent
    assert trellis.code_version() == trellis.code_digest(
        installed, Path(trellis.__file__).resolve().parent, trellis._installed_versions()
    )
    package, workbench = tmp_path / "bellman", tmp_path / "bellman_workbench"
    (package / "syntax").mkdir(parents=True)
    workbench.mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'bellman'\n", encoding="utf-8")
    (package / "stage.py").write_text("x = 1\n", encoding="utf-8")
    (package / "syntax/stage.lark").write_text("start: NAME\n", encoding="utf-8")
    (workbench / "app.py").write_text("y = 2\n", encoding="utf-8")
    versions = {"python": "3.14", "bellman": "0.1.0"}
    first = trellis.code_digest(package, workbench, versions)
    assert trellis.code_digest(package, workbench, versions) == first
    (workbench / "app.py").write_text("y = 3\n", encoding="utf-8")
    changed_byte = trellis.code_digest(package, workbench, versions)
    (package / "stage.py").rename(package / "stages.py")
    renamed = trellis.code_digest(package, workbench, versions)
    (package / "syntax/stage.lark").write_text("start: WORD\n", encoding="utf-8")
    grammar = trellis.code_digest(package, workbench, versions)
    versions["bellman"] = "0.1.1"
    version = trellis.code_digest(package, workbench, versions)
    assert len({first, changed_byte, renamed, grammar, version}) == 5
    (package / "notes.txt").write_text("a note\n", encoding="utf-8")
    (workbench / "page.vue").write_text("<template></template>\n", encoding="utf-8")
    assert trellis.code_digest(package, workbench, versions) == version


# --- unit J: the trellis loop reads the tab's unsaved buffers ---

# the connector of the trellis file of `emptied_port_cons`, emptied and
# filled
EMPTIED_ENTRY = "    connectors:\n      - {}\n"
FILLED_ENTRY = "    connectors:\n      - {w: m}\n"
# the connector of the period file of `emptied_portfolio`, emptied and filled
EMPTIED_PERIOD = "connectors:\n  - {}\n"
FILLED_PERIOD = "connectors:\n  - {m_next: m}\n"
# the period file of the portfolio model, by its path from the folder
PERIOD_FILE = "declaration/period.yml"
# the join a filled connector draws in the forward graph, on the copy of
# cons-port and on the portfolio model's registry, whose explicit portfolio
# stage continues to m_next
JOIN = "w → m"
JOIN_PORTFOLIO = "m_next → m"


def test_a_reading_takes_an_unsaved_trellis_file_and_records_it(tmp_path):
    """Lesson 05's trellis file with its connector and its inter-period
    mapping emptied (`emptied_port_cons`), read from disk, draws no join
    `w → m`. Read again with an unsaved text of the trellis file that
    fills the connector (spec 0.4 §3.1, §3.3; brief rule 5), it draws the
    join; `files` holds the digest of that text; `buffered` maps the file's
    path to the revision given; `number` is greater than the first
    reading's; the inputs are current for that text; and the file on disk
    is unchanged."""
    copy = emptied_port_cons(tmp_path)
    folder = model.open_folder(copy)
    on_disk = (copy / PORT_CONS).read_bytes()
    first = trellis.show_trellis(folder, LESSON).shown
    assert JOIN not in join_labels(first.collection, "forward") and first.buffered == {}
    text = on_disk.decode("utf-8").replace(EMPTIED_ENTRY, FILLED_ENTRY)
    unsaved = unsaved_of(copy, {PORT_CONS: text}, revision=4)
    second = trellis.show_trellis(folder, LESSON, previous=first, unsaved=unsaved).shown
    path = str((copy / PORT_CONS).resolve())
    assert JOIN in join_labels(second.collection, "forward")
    assert second.files[path] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert second.buffered == {path: 4}
    assert second.number > first.number
    assert trellis.inputs_current(second, trellis.texts_of(unsaved))
    assert not trellis.inputs_current(first, trellis.texts_of(unsaved))
    assert (copy / PORT_CONS).read_bytes() == on_disk


def test_an_unsaved_period_file_is_read_and_a_reading_is_not_skipped(tmp_path):
    """The portfolio model with its connectors emptied (`emptied_portfolio`),
    read with an unsaved text of `period.yml` that fills the connector: the
    join is drawn, and the same reading again, given that reading as
    `previous` and the same text, answers `previous` itself, since the
    digest of the text read is unchanged (spec 0.4 §3.3). A changed text of
    `period.yml`, the connector emptied again under a typed comment, is read
    by the next reading, which draws no join and records the new text's
    digest and revision."""
    copy = emptied_portfolio(tmp_path)
    folder = model.open_folder(copy)
    written = (copy / PERIOD_FILE).read_text(encoding="utf-8")
    text = written.replace(EMPTIED_PERIOD, FILLED_PERIOD)
    first = trellis.show_trellis(
        folder, RECIPE, unsaved=unsaved_of(copy, {PERIOD_FILE: text})
    ).shown
    assert JOIN_PORTFOLIO in join_labels(first.collection, "forward")
    again = trellis.show_trellis(
        folder, RECIPE, previous=first, unsaved=unsaved_of(copy, {PERIOD_FILE: text})
    )
    assert again.shown is first
    changed = "# a comment typed after the reading\n" + written
    second = trellis.show_trellis(
        folder, RECIPE, previous=first, unsaved=unsaved_of(copy, {PERIOD_FILE: changed}, 2)
    ).shown
    path = str((copy / PERIOD_FILE).resolve())
    assert JOIN_PORTFOLIO not in join_labels(second.collection, "forward")
    digest = hashlib.sha256(changed.encode("utf-8")).hexdigest()
    assert (second.files[path], second.buffered) == (digest, {path: 2})


def test_j_saving_a_buffer_the_reading_took_reads_nothing_again(tmp_path, specify_calls):
    """Review Focus 4: lesson 05's emptied trellis file read with an unsaved
    text that fills the connector; that text then saved as `Save` writes it
    (`model.save_file`), and the trellis read again with no unsaved text and
    that reading as `previous`. The reading answers `previous` itself and
    calls `specify_trellis` not once, so the graph and its ports stay, since
    the text read is unchanged; and the digests on disk equal those the
    reading recorded, so the watcher reads nothing again."""
    copy = emptied_port_cons(tmp_path)
    folder = model.open_folder(copy)
    found = model.read_file(folder, PORT_CONS)
    text = found.text.replace(EMPTIED_ENTRY, FILLED_ENTRY)
    shown = trellis.show_trellis(folder, LESSON, unsaved=unsaved_of(copy, {PORT_CONS: text})).shown
    assert JOIN in join_labels(shown.collection, "forward") and shown.buffered
    assert model.save_file(folder, PORT_CONS, text, found.digest).saved
    called = len(specify_calls)
    assert trellis.show_trellis(folder, LESSON, previous=shown).shown is shown
    assert len(specify_calls) == called
    assert trellis.file_digests(shown.files) == shown.files


def test_a_reading_with_buffers_touches_no_entry_of_the_kept_bindings(
    tmp_path, own_cache_folder, specify_calls, monkeypatch
):
    """Rule 10 of the brief (G-R81): the emptied portfolio model read with no
    trellis before it and its binding kept on disk; then read with that
    reading as `previous` and an unsaved text of `period.yml` that fills the
    connector, and the outcome given to `keep_binding` with that
    `previous`. The folder of the bindings is as it was, each entry with its
    modification time, so no entry was read or written; and
    `specify_trellis` was called once, with the previous trellis."""
    copy = emptied_portfolio(tmp_path)
    folder = model.open_folder(copy)
    first = trellis.show_trellis(folder, RECIPE).shown
    trellis.keep_binding(first, None)
    kept = kept_bindings(own_cache_folder)
    assert len(kept) == 1
    given = []
    recorded = trellis.specify_trellis
    monkeypatch.setattr(
        trellis,
        "specify_trellis",
        lambda syntactic, previous, kinds: given.append(previous)
        or recorded(syntactic, previous, kinds),
    )
    text = (copy / PERIOD_FILE).read_text(encoding="utf-8").replace(EMPTIED_PERIOD, FILLED_PERIOD)
    called = len(specify_calls)
    second = trellis.show_trellis(
        folder, RECIPE, previous=first, unsaved=unsaved_of(copy, {PERIOD_FILE: text})
    ).shown
    trellis.keep_binding(second, first)
    assert JOIN_PORTFOLIO in join_labels(second.collection, "forward")
    assert kept_bindings(own_cache_folder) == kept
    assert len(specify_calls) == called + 1
    assert len(given) == 1 and given[0] is first.trellis


def test_address_place_counts_the_line_in_the_buffers_text(pension_folder):
    """The pension model's terminal connector stands in the trellis file at
    line 20 and a connector of a period the template repeats in `period.yml`
    at line 11 on disk; with unsaved texts that add two lines at the top of
    the trellis file and four at the top of the period file, the lines are
    22 and 15, counted in the buffers' texts (brief rule 2), and the files
    on disk are unchanged."""
    folder = model.open_folder(pension_folder)
    trellis_file = folder.root / "declaration/trellis.yml"
    head = "# a line typed\n# and another\n"
    texts = trellis.texts_of(
        unsaved_of(
            pension_folder,
            {
                "declaration/trellis.yml": head + trellis_file.read_text(encoding="utf-8"),
                PERIOD_FILE: head + head + (folder.root / PERIOD_FILE).read_text(encoding="utf-8"),
            },
        )
    )
    places = [
        trellis.address_place(folder, trellis_file, address, texts=given)
        for given in (texts, None)
        for address in ("periods[0].connectors[0]", "periods[5].connectors[0]")
    ]
    assert places == [
        ("declaration/trellis.yml", 22),
        (PERIOD_FILE, 15),
        ("declaration/trellis.yml", 20),
        (PERIOD_FILE, 11),
    ]


# --- unit J: the line a gesture typed, taken out ---


def test_restoring_edit_turns_the_text_after_into_the_text_before():
    """`restoring_edit(before, after)` is the one replacement, counted from
    one in code points, that turns the text a gesture made, `after`, into
    the text before it (spec 0.4 §3.3; brief rule 8): the span of `after`
    between the longest common prefix and suffix of the two texts, with the
    text of `before` between them. The four cases are an inserted line, a
    filled `{}`, an entry added to a flow mapping after a character above
    U+FFFF, which is one column, and two equal texts. The arguments
    exchanged give the edit that types the line again."""
    head = "!trellis\nname: port_cons\nperiods:\n  - stages: {cons: {stage: cons.bl}}\n"
    emptied = head + "    connectors:\n      - {}\n"
    filled = head + "    connectors:\n      - {m_next: m}\n"
    inserted = emptied + "      - {a: k}\n"
    mapping = "inter_connectors:\n  - {𝑢: k}\n"
    added = "inter_connectors:\n  - {𝑢: k, a: m}\n"
    cases = [
        (emptied, inserted, {"line": 7, "column": 1, "end_line": 8, "end_column": 1, "text": ""}),
        (emptied, filled, {"line": 6, "column": 10, "end_line": 6, "end_column": 19, "text": ""}),
        (mapping, added, {"line": 2, "column": 10, "end_line": 2, "end_column": 16, "text": ""}),
        (head, head, {"line": 5, "column": 1, "end_line": 5, "end_column": 1, "text": ""}),
    ]
    for before, after, expected in cases:
        edit = trellis.restoring_edit(before, after)
        assert edit == expected, (before, after)
        assert applied(after, [model.Replacement(**edit)]) == before
    again = trellis.restoring_edit(filled, emptied)
    assert again == {"line": 6, "column": 10, "end_line": 6, "end_column": 10, "text": "m_next: m"}
    assert applied(emptied, [model.Replacement(**again)]) == filled


def test_typed_line_is_the_first_line_the_gesture_changed():
    """`typed_line(before, after)` is the line, counted from one, that a
    gesture typed (spec 0.4 §3.1, the typed line): the first line of
    `after` that differs from the line of `before` at the same position.
    The cases are a filled `{}`, an inserted line, an entry added to a flow
    mapping, a line typed into a trellis entry written as a flow mapping,
    and a line typed after the last line of a text that ends without a line
    end, where the replacement `restoring_edit` answers begins at the end
    of the line before the typed line."""
    head = "!trellis\nname: port_cons\nperiods:\n  - stages: {cons: {stage: cons.bl}}\n"
    emptied = head + "    connectors:\n      - {}\n"
    filled = head + "    connectors:\n      - {m_next: m}\n"
    inserted = emptied + "      - {a: k}\n"
    mapping = "inter_connectors:\n  - {𝑢: k}\n"
    added = "inter_connectors:\n  - {𝑢: k, a: m}\n"
    entry = "periods:\n  - {template: period.yml, repeat: 6, connectors: [{}]}\n"
    joined = entry.replace("[{}]", "[{a: m}]")
    unended = emptied.rstrip("\n")
    appended = unended + "\n      - {a: k}"
    cases = [
        (emptied, filled, 6),
        (emptied, inserted, 7),
        (mapping, added, 2),
        (entry, joined, 2),
        (unended, appended, 7),
    ]
    assert [trellis.typed_line(before, after) for before, after, _ in cases] == [
        line for _, _, line in cases
    ]
    assert trellis.restoring_edit(unended, appended)["line"] == 6


# --- unit J: the line a drag between two unjoined ports types ---

# the inter-period mapping of the trellis file of `emptied_port_cons`,
# emptied
EMPTIED_MAPPING = "inter_connectors:\n  - {}\n"
# the trellis file of the portfolio model, by its path from the folder
TRELLIS_FILE = "declaration/trellis.yml"
# the one entry of that trellis file's `periods` list
PERIODS_ENTRY = "- {template: period.yml, repeat: 6}"
# the drag within `periods[2]` of item 1, and the drag of item 2 from
# `periods[3]` to `periods[2]`, the period after it in time
# the portfolio stage of cons-port continues to `w`; the portfolio model's, in
# its own registry, to `m_next`
WITHIN = ((2, "port", "w"), (2, "cons", "m"))
WITHIN_PORTFOLIO = ((2, "port", "m_next"), (2, "cons", "m"))
BETWEEN = ((3, "disc", "a"), (2, "port", "k"))
# the record of the portfolio stage in the trellis file of lesson 05, on its
# two lines
PORT_RECORD = (
    "      port: {stage: ../../portfolio-choice/declaration/stages/port/port.bl, "
    "calibration: calibration/portfolio.yml,\n"
    "             settings: settings/port_wide.yml, methods: methods/port.yml}\n"
)
# the sentence "An old graph" of brief §5, at lesson 05's trellis file
OLD_GRAPH = (
    "trellis.port-cons.yml: nothing was written. The graph was drawn from an earlier text. "
    "Drag again in the graph now drawn."
)
# the same sentence for a removal of a join, which is no drag (unit J's
# plan, Task 17)
OLD_GRAPH_REMOVAL = (
    "trellis.port-cons.yml: nothing was written. The graph was drawn from an earlier text. "
    "Remove the join again in the graph now drawn."
)


def test_item_1_cases_the_flat_connector_is_written_in_each_of_the_three_copies(tmp_path):
    """Item 1 (spec 0.4 §3.1; brief rule 1, its first row, and §5): a drag
    within `periods[2]` from `port`'s continuation resources to `cons`'s
    `m`, each name held by one stage occurrence, types the flat connector
    into the first empty mapping of the `connectors` list the package
    names, on each of item 1's three copies: the entry of lesson 05's
    `trellis.port-cons.yml`; the portfolio model's `period.yml`, whose entry
    in `trellis.yml` writes no `connectors`; and that model's `trellis.yml`,
    whose entry writes `connectors: [{}]` over the period file's. The edit
    is the text read with `{}` filled and no other character changed; the
    note is the status line of §5; nothing is written to disk. The record of
    the reading names its source, the forward graph, its number and its
    inputs, each relative to the folder or, outside it, absolute; and the
    writing port's record names the six periods the line reaches."""
    # each case with the field the portfolio stage of its copy continues to,
    # `w` in cons-port and `m_next` in the portfolio model's registry
    cases = [
        (
            emptied_port_cons(tmp_path / "port-cons"),
            LESSON,
            PORT_CONS,
            "periods[0].connectors[0]",
            EMPTIED_ENTRY,
            FILLED_ENTRY,
            "w",
        ),
        (
            emptied_portfolio(tmp_path / "portfolio"),
            RECIPE,
            PERIOD_FILE,
            "connectors[0]",
            EMPTIED_PERIOD,
            FILLED_PERIOD,
            "m_next",
        ),
        (
            emptied_portfolio_with_entry_connectors(tmp_path / "entry"),
            RECIPE,
            TRELLIS_FILE,
            "periods[0].connectors[0]",
            "connectors: [{}]",
            "connectors: [{m_next: m}]",
            "m_next",
        ),
    ]
    for copy, source, written, address, emptied, filled, field in cases:
        folder = model.open_folder(copy)
        shown = trellis.show_trellis(folder, source).shown
        text = (copy / written).read_text(encoding="utf-8")
        assert text.count(emptied) == 1
        within = ((2, "port", field), (2, "cons", "m"))
        gesture = trellis.connector_edit(shown, connected_event(shown, folder, *within), {})
        path = str((copy / written).resolve())
        note = f"{Path(written).name}, {address}: {{{field}: m}} written, flat, periods 0–5"
        assert gesture == trellis.Gesture(
            {path: text.replace(emptied, filled)}, {path: text}, (), note, None, path, address
        )
        assert (copy / written).read_text(encoding="utf-8") == text
        record = trellis.reading_record(folder, shown)
        assert {key: record[key] for key in ("source", "graph", "number")} == {
            "source": source.path,
            "graph": "forward",
            "number": shown.number,
        }
        # each input names a file the reading read, in the order it read them
        assert [str((copy / name).resolve()) for name in record["inputs"]] == list(shown.files)
        assert not any(Path(name).is_absolute() for name in record["inputs"])
        # lesson 05 reads its stage files from the portfolio model's folder,
        # named as the editor names them
        assert (SHARED_CONS in record["inputs"]) == (source == LESSON)
        (port,) = [
            port
            for port in trellis.unjoined_ports(shown)
            if (port["side"], port["h"], port["key"], port["field"]) == ("writing", *WITHIN[0])
        ]
        assert port["periods"] == [0, 1, 2, 3, 4, 5]


@pytest.mark.parametrize("between", [False, True])
@pytest.mark.parametrize("duplicate_writer, duplicate_reader, source_name, target_name", [
    (False, False, "c", "x"),
    (True, False, "U.c", "x"),
    (False, True, "c", "S.x"),
    (True, True, "U.c", "S.x"),
])
def test_item_2_cases_the_entry_is_added_to_the_mapping_the_file_writes(
    tmp_path, between, duplicate_writer, duplicate_reader, source_name, target_name,
):
    """Unique fields keep bare names; repeated local names are qualified
    in compact source, within and between periods of a shared template."""
    path = composition_folder(tmp_path / "composition", repeat=4)
    period = path / "period.yml"
    text = period.read_text(encoding="utf-8")
    additions = ("  U_two: {stage: U.bl}\n" if duplicate_writer else "")
    additions += "  S_two: {stage: S.bl}\n" if duplicate_reader else ""
    period.write_text(text.replace("connectors:", additions + "connectors:"), encoding="utf-8")
    file = path / "trellis.yml"
    file.write_text(file.read_text(encoding="utf-8").replace(
        "inter_connectors: []", "inter_connectors: [{}]",
    ), encoding="utf-8")
    folder = model.open_folder(path)
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    writing, reading = (2, "U", "c"), (1 if between else 2, "S", "x")
    edit = trellis.connector_edit(shown, connected_event(shown, folder, writing, reading), {})
    assert edit.sentence is None, edit.sentence
    written = str(file if between else period)
    assert set(edit.edits) == {written}
    address = "inter_connectors[0]" if between else "connectors[0]"
    assert entry_value(edit.edits[written], address) == {source_name: target_name}
    assert "periods 0–3" in edit.note
    assert "from:" not in edit.edits[written] and "fields:" not in edit.edits[written]
    reopened = trellis.show_trellis(folder, source, previous=shown, unsaved={
        p: trellis.Unsaved(t, 1) for p, t in edit.edits.items()
    }).shown
    selected = [pair for pair in reopened.selection.pairs if pair.origin == "authored"]
    assert len(selected) == (3 if between else 4)
    assert all(pair.writing.key == "U" and pair.reading.key == "S" for pair in selected)
    assert not reopened.selection.diagnostics


def test_item_2_indexed_mapping_keeps_its_other_pairs_and_adds_a_second_entry(tmp_path):
    path = composition_folder(tmp_path / "composition", repeat=4)
    file = path / "trellis.yml"
    file.write_text(file.read_text(encoding="utf-8").replace(
        "inter_connectors: []", "inter_connectors: [{}, {}, {}]",
    ), encoding="utf-8")
    folder = model.open_folder(path)
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    first = trellis.connector_edit(shown, connected_event(shown, folder, (2, "U", "c"), (1, "S", "x")), {})
    written = str(file)
    assert first.sentence is None, first.sentence
    assert entry_value(first.edits[written], "inter_connectors") == [{}, {"c": "x"}, {}]
    assert "periods 1–2" in first.note
    unsaved = {p: trellis.Unsaved(t, 1) for p, t in first.edits.items()}
    again = trellis.show_trellis(folder, source, previous=shown, unsaved=unsaved).shown
    second = trellis.connector_edit(
        again, connected_event(again, folder, (2, "T", "y"), (1, "U", "z")), first.edits,
    )
    assert second.sentence is None, second.sentence
    assert entry_value(second.edits[written], "inter_connectors") == [{}, {"c": "x", "y": "z"}, {}]
    file.write_text(file.read_text(encoding="utf-8").replace("inter_connectors: [{}, {}, {}]", "inter_connectors: []"), encoding="utf-8")
    absent = trellis.show_trellis(folder, source).shown
    refused = trellis.connector_edit(absent, connected_event(absent, folder, (2, "U", "c"), (1, "S", "x")), {})
    assert refused.edits is None and "no inter-period mapping" in refused.sentence


def test_item_3_cases_an_event_of_another_reading_writes_nothing(tmp_path, monkeypatch):
    """Item 3 (spec 0.4 §3.3, its third paragraph; brief §5): the event of a
    drag is checked against the reading drawn, and an old event types
    nothing and answers the sentence "An old graph" of §5 at the trellis
    file, raising nothing: an event of another elaboration number; one of
    another source whose ports have the same ids, `trellis.port-cons-vfi.yml`;
    one whose reading's trellis file now holds an unsaved text with another
    `repeat`; one whose reading's unrelated input, a stage file, now holds
    an unsaved text; handles that name the two ports on the sides
    exchanged, or a port no join leaves unjoined; a drag to a period neither
    the same nor the next, which no current graph admits; and records that
    are no event. The same event with the reading unchanged is admitted;
    where the package's text writer refuses the line, nothing is typed and
    the sentence "An edit not applied" of §5 is answered at the line's
    address. Nothing is written to disk. Where the trellis file's unsaved
    text reads as no mapping, the record of each unjoined port names the
    port's own period and no pair, and nothing is raised."""
    copy = emptied_port_cons(tmp_path)
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    event = connected_event(shown, folder, *WITHIN)
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    assert text.count("repeat: 6") == 1
    (stage,) = [name for name in shown.files if name.endswith("/port.bl")]
    reading = event["reading"]
    # `cons`'s `a` is read by `disc`'s `a`, a join by name
    joined = event["sourceHandle"].replace(
        "port/unjoined:port:cntn:w", "cons/unjoined:cons:cntn:a"
    )
    assert joined != event["sourceHandle"]
    old = trellis.Gesture(None, None, (), None, OLD_GRAPH, path, None)
    for given, texts in (
        ({**event, "reading": {**reading, "number": shown.number + 1}}, {}),
        ({**event, "reading": {**reading, "source": "declaration/trellis.port-cons-vfi.yml"}}, {}),
        (event, {path: text.replace("repeat: 6", "repeat: 5")}),
        (event, {stage: Path(stage).read_text(encoding="utf-8") + "\n"}),
        (
            {
                **event,
                "sourceHandle": event["targetHandle"],
                "targetHandle": event["sourceHandle"],
            },
            {},
        ),
        ({**event, "sourceHandle": joined}, {}),
        (connected_event(shown, folder, (2, "port", "w"), (4, "cons", "m")), {}),
        ({**event, "reading": None}, {}),
        ({}, {}),
        (None, {}),
    ):
        assert trellis.connector_edit(shown, given, texts) == old, given
    # a trellis text that reads as a list, which names no place
    for port in trellis.unjoined_ports(shown, {path: "- a list\n"}):
        assert (port["periods"], port["periods_between"]) == ([port["h"]], []), port
    admitted = trellis.connector_edit(shown, event, {})
    assert admitted.edits == {path: text.replace(EMPTIED_ENTRY, FILLED_ENTRY)}
    assert admitted.sentence is None

    def refused(*arguments):
        raise ValueError("the layout of the file cannot be extended as text")

    monkeypatch.setattr(trellis, "append_to_mapping", refused)
    not_applied = (
        "trellis.port-cons.yml, periods[0].connectors[0]: nothing was written. The text changed "
        "after the drag read it. Drag again."
    )
    assert trellis.connector_edit(shown, event, {}) == trellis.Gesture(
        None, None, (), None, not_applied, path, "periods[0].connectors[0]"
    )
    assert (copy / PORT_CONS).read_text(encoding="utf-8") == text


def test_j_a_typed_line_keeps_every_other_character_of_the_file(tmp_path):
    """Review Focus 2 (spec 0.4 §3.1: the text writers keep comments and
    layout): lesson 05's emptied trellis file read from unsaved texts that
    write comments around its `connectors` list; the list in flow style
    with its one empty mapping; the list in flow style and empty; every line
    ended by a carriage return and a line feed; and so ended, with the
    inter-period mapping in block style holding `a: k`. A drag within a
    period fills the empty mapping or appends to the empty list, and a drag
    between periods adds `w: m` on a line of its own; in each case the
    new text is the text read with the one line typed and every other
    character kept, the line ends included."""
    copy = emptied_port_cons(tmp_path)
    folder = model.open_folder(copy)
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    crlf = text.replace("\n", "\r\n")
    commented = (
        "    connectors:  # the period's connectors\n"
        "      # the mapping a drag fills\n"
        "      - {}  # to fill\n"
    )
    block = crlf.replace("inter_connectors:\r\n  - {}\r\n", "inter_connectors:\r\n  - a: k\r\n")
    cases = [
        (
            text.replace(EMPTIED_ENTRY, commented),
            WITHIN,
            "- {}  # to fill",
            "- {w: m}  # to fill",
        ),
        (text.replace(EMPTIED_ENTRY, "    connectors: [{}]\n"), WITHIN, "[{}]", "[{w: m}]"),
        (text.replace(EMPTIED_ENTRY, "    connectors: []\n"), WITHIN, "[]", "[{w: m}]"),
        (crlf, WITHIN, "      - {}\r\n    repeat", "      - {w: m}\r\n    repeat"),
        (
            block,
            ((3, "port", "w"), (2, "cons", "m")),
            "  - a: k\r\n",
            "  - a: k\r\n    w: m\r\n",
        ),
    ]
    shown = None
    for typed, (writing, reading), old, new in cases:
        assert typed.count(old) == 1
        unsaved = unsaved_of(copy, {PORT_CONS: typed})
        shown = trellis.show_trellis(folder, LESSON, previous=shown, unsaved=unsaved).shown
        event = connected_event(shown, folder, writing, reading)
        gesture = trellis.connector_edit(shown, event, trellis.texts_of(unsaved))
        assert (gesture.edits, gesture.read) == ({path: typed.replace(old, new)}, {path: typed}), (
            typed
        )
    assert (copy / PORT_CONS).read_text(encoding="utf-8") == text


def test_j_a_period_that_writes_no_connectors_list_takes_no_drag(tmp_path):
    """Review Focus 3 (the plan's decision J-D25): where neither a period's
    entry nor its period file writes a `connectors` list, a drag within the
    period types nothing, raises nothing and answers the Workbench's
    sentence at the entry: the entry `periods[0]` of lesson 05's trellis
    file, read from an unsaved text with no `connectors`; and the portfolio
    model's `period.yml`, the entry being the whole file, which the sentence
    names by the file alone, read from an unsaved text with none."""
    def told(connector):
        return (
            f"the connector {connector} was not written. The period writes no connectors list. "
            "Type connectors: [{}] in it."
        )

    for copy, source, written, emptied, address, place, within, connector in (
        (
            emptied_port_cons(tmp_path / "port-cons"),
            LESSON,
            PORT_CONS,
            EMPTIED_ENTRY,
            "periods[0]",
            "trellis.port-cons.yml, periods[0]",
            WITHIN,
            "{w: m}",
        ),
        (
            emptied_portfolio(tmp_path / "portfolio"),
            RECIPE,
            PERIOD_FILE,
            EMPTIED_PERIOD,
            "",
            "period.yml",
            WITHIN_PORTFOLIO,
            "{m_next: m}",
        ),
    ):
        folder = model.open_folder(copy)
        text = (copy / written).read_text(encoding="utf-8")
        assert text.count(emptied) == 1
        unsaved = unsaved_of(copy, {written: text.replace(emptied, "")})
        shown = trellis.show_trellis(folder, source, unsaved=unsaved).shown
        gesture = trellis.connector_edit(
            shown, connected_event(shown, folder, *within), trellis.texts_of(unsaved)
        )
        path = str((copy / written).resolve())
        assert gesture == trellis.Gesture(
            None, None, (), None, f"{place}: {told(connector)}", path, address
        )


def test_a_typed_connector_constructs_no_stage_and_binds_no_occurrence_again(
    tmp_path, specify_calls, monkeypatch
):
    """Spec 0.4 §8 J (1) and §3.1: a connector line constructs no stage and
    binds no occurrence again, since the trellis is read through
    `specify_trellis` with the previous trellis. On the copy
    `durables_without_a` of the corpus's largest trellis, read under the
    restriction it opens with, `periods 0–2`, the drag from `keeper_cons`'s
    `a_nxt_kp` in `periods[2]` to `tenure`'s `a` in `periods[1]` (decision
    J-D8) adds `a_nxt_kp: a` to the standing inter-period mapping. The
    trellis read again with that text unsaved and the first reading as
    `previous` calls `specify_trellis` with the kinds the first reading
    gave it, each call given the first reading's trellis; it constructs no
    stage text, the factory's `construct_stage` counted as
    `test_trellis_load_item_4_a_new_restriction_copies_nothing_and_a_save_constructs_one_text`
    counts it; and it changes no position, `changed == []`. The two fields
    dragged are no longer unjoined, and `adjuster_cons`'s `a_nxt_adj`, the
    second branch, stays unjoined. The second branch is then dragged to
    `tenure`'s `a`, which the first drag's entry now reaches: a further
    source, added as the key `a_nxt_adj: a` of the same mapping, the note
    naming no form (unit J's decisions J-D41 and J-D42)."""
    copy = durables_without_a(tmp_path)
    folder = model.open_folder(copy)
    opening = trellis.opening_restriction(recipe.read_source(folder, RECIPE))
    assert opening == "periods 0–2"
    restriction = trellis.parse_restriction(opening)
    first = trellis.show_trellis(folder, RECIPE, restriction).shown
    # the kinds of each call of `specify_trellis` the first reading made
    first_calls = list(specify_calls)
    assert first_calls
    drag = ((2, "keeper_cons", "a_nxt_kp"), (1, "tenure", "a"))
    gesture = trellis.connector_edit(first, connected_event(first, folder, *drag), {})
    assert gesture.note.startswith(
        "trellis.yml, inter_connectors[0]: a_nxt_kp: a written, entry, periods 0–50"
    )
    (typed,) = gesture.edits.values()
    constructions, construct = [], factory_trellis.construct_stage
    monkeypatch.setattr(
        factory_trellis,
        "construct_stage",
        lambda text, origin, additions=(): constructions.append(origin)
        or construct(text, origin, additions),
    )
    given, recorded = [], trellis.specify_trellis
    monkeypatch.setattr(
        trellis,
        "specify_trellis",
        lambda syntactic, previous, kinds: given.append(previous)
        or recorded(syntactic, previous, kinds),
    )
    called = len(specify_calls)
    unsaved = unsaved_of(copy, {TRELLIS_FILE: typed})
    second = trellis.show_trellis(folder, RECIPE, restriction, first, unsaved=unsaved).shown
    assert specify_calls[called:] == first_calls
    assert [previous is first.trellis for previous in given] == [True] * len(first_calls)
    assert constructions == [] and second.changed == []
    unjoined = {
        (port["side"], port["h"], port["key"], port["field"])
        for port in trellis.unjoined_ports(second, trellis.texts_of(unsaved))
    }
    assert not {("writing", *drag[0]), ("reading", *drag[1])} & unjoined
    assert ("writing", 2, "adjuster_cons", "a_nxt_adj") in unjoined
    # the second branch, a further source of `tenure`'s `a`
    branch = ((2, "adjuster_cons", "a_nxt_adj"), drag[1])
    texts = trellis.texts_of(unsaved)
    further = trellis.connector_edit(second, connected_event(second, folder, *branch), texts)
    assert further.note == "trellis.yml, inter_connectors[0]: a_nxt_adj: a written, periods 0–50"
    (both,) = further.edits.values()
    assert both == typed.replace(
        "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z, a_nxt_kp: a}\n",
        "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z, a_nxt_kp: a, a_nxt_adj: a}\n",
    )


def test_j_a_further_source_is_a_key_of_the_mapping_that_joins_the_arrival():
    """Branching in and branching out (unit J's decisions J-D41 to J-D43;
    spec 0.4 §3.1 as J-D41 amends it), by direct calls on
    `applications/durables`, read under the restriction it opens with,
    `periods 0–2`. With `a_nxt_adj: a_bq` taken out of the terminal
    period's connector in an unsaved text, `bequest`'s `a_bq` is still
    reached by `keeper_cons`'s `a_nxt_kp`, and its port, hovered as `a_bq≺ ·
    1 source`, takes the drag from `adjuster_cons`'s `a_nxt_adj`: the key
    `a_nxt_adj: a_bq` is typed back into that connector, so that the list
    keeps its one mapping, the text read as the file's own, the key at the
    mapping's end, and the note names no form; read again, the port counts
    two sources. The same holds of `a_nxt_adj: a` of the standing
    inter-period mapping, the drag from `periods[2]` to `tenure`'s `a` in
    `periods[1]`. A writing port that a join reads starts no second line:
    the drag from `keeper_cons`'s `a_nxt_kp`, which the connector joins,
    types nothing and answers the one sentence that the port is joined, at
    the connector's address, the port named by its field as the file writes
    it, `a_nxt_kp` (spec 0.4 §3.1). The writing ports of `tenure`, a branching
    stage, carry the labels `keep` and `adjust` of their branches, grouped,
    while those of `keeper_cons` are unchanged."""
    folder = model.open_folder(DURABLES)
    path = str((DURABLES / TRELLIS_FILE).resolve())
    text = (DURABLES / TRELLIS_FILE).read_text(encoding="utf-8")
    restriction = trellis.parse_restriction("periods 0–2")
    connector = (
        "{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, "
        "a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}"
    )
    mapping = "{a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}"
    for old, key, back, drag, note, port in (
        (
            connector,
            " a_nxt_adj: a_bq,",
            "{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, "
            "h_nxt_adj: h_bq, z_nxt_adj: z_bq, a_nxt_adj: a_bq}",
            ((0, "adjuster_cons", "a_nxt_adj"), (0, "bequest", "a_bq")),
            "trellis.yml, periods[0].connectors[0]: {a_nxt_adj: a_bq} written, periods 0",
            ("periods[0]/bequest/joined:bequest:arvl:a_bq", "a_bq≺"),
        ),
        (
            mapping,
            " a_nxt_adj: a,",
            "{a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z, a_nxt_adj: a}",
            ((2, "adjuster_cons", "a_nxt_adj"), (1, "tenure", "a")),
            "trellis.yml, inter_connectors[0]: a_nxt_adj: a written, periods 0–50",
            ("periods[1]/tenure/joined:tenure:arvl:a", "a≺"),
        ),
    ):
        taken = text.replace(old, old.replace(key, ""))
        unsaved = unsaved_of(DURABLES, {TRELLIS_FILE: taken})
        texts = trellis.texts_of(unsaved)
        shown = trellis.show_trellis(folder, RECIPE, restriction, unsaved=unsaved).shown
        reached = {item["id"]: item for item in trellis.connectable_ports(shown, texts)}
        assert (reached[port[0]]["sources"], reached[port[0]]["title"]) == (
            1,
            f"{port[1]} · 1 source",
        )
        gesture = trellis.connector_edit(shown, connected_event(shown, folder, *drag), texts)
        assert (gesture.note, gesture.sentence, gesture.read) == (note, None, {path: taken})
        (typed,) = gesture.edits.values()
        # the key stands at the mapping's end, and the text reads as the file's
        assert typed == text.replace(old, back)
        assert entry_value(typed) == entry_value(text)
        again = unsaved_of(DURABLES, {TRELLIS_FILE: typed})
        drawn = trellis.show_trellis(folder, RECIPE, restriction, shown, again).shown
        ports = trellis.connectable_ports(drawn, trellis.texts_of(again))
        reached = {item["id"]: item for item in ports}
        assert (reached[port[0]]["sources"], reached[port[0]]["title"]) == (
            2,
            f"{port[1]} · 2 sources",
        )
    assert (DURABLES / TRELLIS_FILE).read_text(encoding="utf-8") == text

    shown = trellis.show_trellis(folder, RECIPE, restriction).shown
    joined = ((0, "keeper_cons", "a_nxt_kp"), (0, "bequest", "a_bq"))
    # a drag from a joined continuation port is the move of its cable's
    # reading end (design pass 10 §7; unit N, Task 7): to the port its pair
    # already joins, it writes nothing and answers no sentence
    assert trellis.connector_edit(shown, connected_event(shown, folder, *joined), {}) == (
        trellis.Gesture(None, None, (), None, None, None, None)
    )
    outputs = {
        node["id"]: [
            next(pair["value"] for pair in item["attrs"] if pair["key"] == "label")
            for item in node.get("outputsMetadata") or []
            if any(pair["key"] == "field" for pair in item["attrs"])
        ]
        for node in graph_named(shown.collection, "forward")["nodes"]
    }
    assert outputs["periods[1]/tenure/GraphOutputs"] == [
        "keep: w_kp≻",
        "keep: h_kp≻",
        "keep: z_kp≻",
        "adjust: w_adj≻",
        "adjust: z_adj≻",
    ]
    assert outputs["periods[1]/keeper_cons/GraphOutputs"] == [
        "a_nxt_kp≻",
        "h_nxt_kp≻",
        "z_nxt_kp≻",
    ]


# --- unit J: the drops, the stage list and the + period controls ---

# the `+ period` controls of a trellis of six periods, all shown, by their
# targets: the control at the earliest end, then one between each two
# adjacent periods, in the order of the periods from the earliest
SIX_CONTROLS = ["earliest end"] + [
    f"between periods[{h}] and periods[{h - 1}]" for h in range(5, 0, -1)
]


def test_no_control_stands_at_the_terminal_end_and_details_lists_what_a_typed_period_moves(
    tmp_path, app_state
):
    """Spec 0.4 §3.6 and brief §5: in the forward trellis graph of a folder
    of the forms, six periods all shown, a `+ period` control stands at the
    earliest end, beside periods[5], and between each two adjacent periods,
    beside the earlier of the two, each named `add a period`, and none
    stands at the terminal end. Its recipe restricts `port` to periods 0 to
    5 and binds `cons`'s calibration under the range keys `0-2` and `3-5`:
    a period typed at the head of `periods` would move each, which
    `moved_ranges` lists as the recipe writes them, in the recipe's order,
    read from the recipe's unsaved text where one is given; a trellis
    written as records has no recipe and lists none. Details, with the
    terminal period's layer selected, lists them under the label `moved by
    a period typed first`, and with another period's layer selected lists
    nothing of the kind."""
    folder_path = written_from_the_forms(tmp_path / "demo")
    recipe_file = folder_path / RECIPE_FILE
    recipe_file.write_text(
        recipe_file.read_text(encoding="utf-8")
        .replace(
            "{all: [$cons_calibration]}",
            '{all: [$cons_calibration], "0-2": [$cons_late], "3-5": [$cons_early]}',
        )
        .replace("{all: [$port_methods]}}", "{all: [$port_methods]}, periods: [0, 5]}"),
        encoding="utf-8",
    )
    folder = model.open_folder(folder_path)
    shown = trellis.show_trellis(folder, RECIPE).shown
    controls = trellis.period_controls(shown)
    assert [control["target"] for control in controls] == SIX_CONTROLS
    assert [control["after"] for control in controls] == [
        f"periods[{h}]___group___" for h in (5, 5, 4, 3, 2, 1)
    ]
    assert {control["name"] for control in controls} == {"add a period"}
    moved = [
        "stages.port.periods: [0, 5]",
        "stages.cons.calibration: 0-2",
        "stages.cons.calibration: 3-5",
    ]
    assert trellis.moved_ranges(folder, shown, {}) == moved
    unsaved = {
        str(recipe_file.resolve()): recipe_file.read_text(encoding="utf-8").replace(
            "periods: [0, 5]", "periods: [1, 5]"
        )
    }
    assert trellis.moved_ranges(folder, shown, unsaved)[0] == "stages.port.periods: [1, 5]"
    records = applications_copy(tmp_path / "records")
    lesson = model.open_folder(records)
    assert trellis.moved_ranges(lesson, trellis.show_trellis(lesson, LESSON).shown, {}) == []
    app_state(folder_path)
    app.trellis_shown.value = shown
    try:
        for h, listed in ((0, moved), (1, [])):
            subject = trellis.describe_node(shown, "forward", f"periods[{h}]___group___", {})
            _, rendered = solara.render(app.TrellisSubject(subject, []), handle_error=False)
            try:
                labels = [
                    widget.children
                    for widget in rendered.find(v.Html, class_="bl-block-label").widgets
                ]
                items = [
                    widget.children
                    for widget in rendered.find(v.Html, class_="bl-moved-range").widgets
                ]
                # the label in sentence case (the fix wave Q3b, item 19; C12)
                assert (["Moved by a period typed first"] in labels) == bool(listed)
                assert items == [[line] for line in listed]
            finally:
                rendered.close()
    finally:
        clear_trellis_state()


def test_a_restricted_view_shows_controls_only_between_periods_adjacent_in_the_whole_trellis(
    tmp_path,
):
    """Spec 0.4 §3.6: in a restricted view a `+ period` control stands only
    between two periods adjacent in the whole trellis that the view shows,
    and at the earliest end where the earliest period is shown. On lesson
    05's trellis file, whose periods[1] alone writes no `disc`, the
    restriction `stages disc` shows every period but periods[1]: controls
    stand at the earliest end and between periods 5 and 4, 4 and 3, and 3
    and 2, and none between periods[2] and periods[0], which are not
    adjacent. The restriction `periods 2–4` shows neither end, and controls
    stand between periods 4 and 3 and 3 and 2 alone."""
    copy = records_without(tmp_path, 1, "disc")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, RECORDS).shown
    assert [control["target"] for control in trellis.period_controls(shown)] == SIX_CONTROLS

    def targets(text):
        restriction = trellis.parse_restriction(text)
        drawn = trellis.show_trellis(folder, RECORDS, restriction, previous=shown).shown
        assert drawn.restriction == restriction
        return [control["target"] for control in trellis.period_controls(drawn)]

    assert targets("stages disc") == SIX_CONTROLS[:4]
    assert targets("periods 2–4") == SIX_CONTROLS[2:4]


def test_a_drop_of_another_reading_writes_nothing(tmp_path):
    """Spec 0.4 §3.3, last paragraph: `drop_edits` checks the event as
    `connector_edit` does. On lesson 05's trellis, `disc` dropped on
    periods[0], whose entry writes it, is admitted and writes nothing. An
    event whose reading names another elaboration number, another source or
    another graph; a target that is no period of the graph and no `+
    period` control; a kind that is neither `stage` nor `template`; an item
    the stage list does not offer, a key no period writes, a template, a
    stage of the library (unit L, Task 7), or none on a period; a record
    that is no event; and an event read against
    a file that now holds another text, each answer the sentence "An old
    graph" of brief §5 and write nothing."""
    copy = records_folder(tmp_path)
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, RECORDS).shown
    path = str((copy / PORT_CONS_RECORDS).resolve())
    text = (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8")
    good = dropped_event(shown, folder, "disc", "stage", "periods[0]___group___")
    assert trellis.drop_edits(shown, good, {}) == trellis.Gesture(
        None, None, (), None, None, path, "periods[0].stages"
    )
    reading = good["reading"]
    # the sentence names the trellis of records the folder of records opens on
    old_graph = OLD_GRAPH.replace("trellis.port-cons.yml", "trellis.port-cons-vfi.yml")
    old = trellis.Gesture(None, None, (), None, old_graph, path, None)
    for event in (
        {**good, "reading": {**reading, "number": reading["number"] + 1}},
        {**good, "reading": {**reading, "source": "declaration/trellis.reference-port-cons.yml"}},
        {**good, "reading": {**reading, "graph": "backward"}},
        {**good, "reading": None},
        {**good, "target": "periods[6]___group___"},
        {**good, "target": "periods[0]/disc___group___"},
        {**good, "target": "between periods[2] and periods[0]"},
        {**good, "target": None},
        {**good, "kind": "field"},
        {**good, "item": "bequest"},
        {**good, "item": None},
        {**good, "kind": "template", "item": NOPORT_ID},
        {**good, "kind": "library", "item": str(copy / "library/port")},
        None,
        [],
        "dropped",
        {},
    ):
        assert trellis.drop_edits(shown, event, {}) == old
    assert trellis.drop_edits(shown, good, {path: text.replace("repeat: 6", "repeat: 5")}) == old
    assert (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8") == text


# the portfolio model's stage folder of `port`, of which a library of stages
# holds copies (unit L, Task 7)
PORT_STAGE_FOLDER = ROOT / "applications/portfolio-choice/declaration/stages/port"


def test_l_the_stage_list_lists_the_library_after_the_templates_and_a_drop_copies_its_stage(
    tmp_path, monkeypatch
):
    """Unit L, Task 7 (AAS, L-D6; K-D26). On a folder of the forms, whose
    recipe holds `port`, `cons` and `disc` in the six periods `period.yml`
    writes: with `BELLMAN_STAGE_LIBRARY` naming a folder that does not
    exist, the stage list offers the folder's stages in the section `This
    folder's stages` (AAS, L-D9), the templates in the section `Templates`,
    no stage of the library and nothing refused, and last `From a folder…`,
    which, dropped on a period, opens the form on the folder that holds the
    model folder. Once that folder holds two copies of the corpus's `port`
    stage folder, `port` and `renter`, the list is the same with the two
    stages of the library before `From a folder…`, in the section `Library`,
    each with its full path as its id, the kind `library`, its key as its
    title, the library's folder's name, its parameters and no period; and
    `From a folder…` opens the form on the library. The sections' words and
    the item's are in sentence case (design pass 13 §3). `renter` dropped on
    periods[2] answers, writing nothing, the edits "add stage" makes for a
    stage folder of the disk: `renter.bl` and its methods file as new files,
    the recipe, the period file and answers.yml edited, answers.yml
    recording the origin, the path and the SHA-256 of `port.bl` and
    `methods.yml`. `port`, whose key the recipe
    holds, opens the form from a folder on its folder in the library, the
    period's list named and the key left to type; an id that is the path of
    no stage of the library answers "An old graph". Nothing in the library
    is written."""
    folder_path = written_from_the_forms(tmp_path / "demo")
    folder = model.open_folder(folder_path)
    shown = trellis.show_trellis(folder, RECIPE).shown
    on_period = f"periods[2]{LAYER_ID_ENDING}"
    library = tmp_path / "library"
    monkeypatch.setenv("BELLMAN_STAGE_LIBRARY", str(library))
    without = trellis.stage_items(folder, shown, {})["items"]
    assert [(item["kind"], item["section"]) for item in without] == (
        [("stage", "This folder's stages")] * 3
        + [("template", "Templates")] * 8
        + [("folder", None)]
    )
    from_folder = dropped_event(shown, folder, "folder", "folder", on_period)
    above = str(folder_path.resolve().parent)
    assert trellis.drop_edits(shown, from_folder, {})["fill"]["folder"] == above

    for key in ("port", "renter"):
        shutil.copytree(PORT_STAGE_FOLDER, library / key)
    before = file_bytes(library)
    calibration = list(creation.folder_template(str(library / "port")).calibration)
    listed = trellis.stage_items(folder, shown, {})
    in_library = [
        {
            "id": str(library / key),
            "kind": "library",
            "key": key,
            "title": key,
            "model_folder": "library",
            "calibration": calibration,
            "periods_listed": [],
            "section": "Library",
        }
        for key in ("port", "renter")
    ]
    assert listed["heading"] is None
    assert listed["items"] == without[:-1] + in_library + without[-1:]
    assert trellis.drop_edits(shown, from_folder, {})["fill"] == {
        "folder": str(library),
        "period": "period.yml",
        "entry": "",
    }

    renter = dropped_event(shown, folder, str(library / "renter"), "library", on_period)
    gesture = trellis.drop_edits(shown, renter, {})
    recipe_path, period, answers = (
        str((folder_path / name).resolve())
        for name in (RECIPE_FILE, "declaration/period.yml", "answers.yml")
    )
    assert [path for path, _ in gesture.new_files] == [
        "declaration/stages/renter/renter.bl",
        "declaration/stages/renter/methods.yml",
    ]
    assert list(gesture.edits) == [recipe_path, period, answers]
    assert entry_value(gesture.edits[answers], "stages.renter") == {
        "origin": str(library / "renter"),
        "sha256": {
            name: hashlib.sha256((library / "renter" / name).read_bytes()).hexdigest()
            for name in ("port.bl", "methods.yml")
        },
    }
    assert str(library) not in gesture.edits[recipe_path] + gesture.edits[period]
    # renter, a second copy of port in the period, is joined to nothing, and
    # the note says so (unit N, Task 5; design pass 10 §7)
    assert gesture.note == (
        "period.yml, stages: renter written, periods 0–5; "
        "new: stages/renter/renter.bl, stages/renter/methods.yml; renter unconnected"
    )
    held = dropped_event(shown, folder, str(library / "port"), "library", on_period)
    assert trellis.drop_edits(shown, held, {}) == {
        "form": "add stage",
        "fill": {"folder": str(library / "port"), "period": "period.yml", "entry": ""},
    }
    nowhere = dropped_event(shown, folder, str(library / "nowhere"), "library", on_period)
    trellis_file = folder_path / "declaration/trellis.yml"
    assert trellis.drop_edits(shown, nowhere, {}) == old_graph_gesture(trellis_file)
    assert file_bytes(library) == before


def test_l_each_item_of_the_stage_list_names_its_model_s_folder(tmp_path, monkeypatch):
    """Unit L, Task 10 (AAS, L-D9). The stage list prints each item on one
    line with the name of its model's folder. On a folder of the forms,
    `demo`, read from its recipe, with a library of stages, `shelf`, that
    holds a copy of the corpus's `port`: the folder's stages name `demo`
    and stand in the section `This folder's stages`; each template names
    the model folder its stage file stands in, `portfolio-choice` for the
    four that the cons-port application binds from the portfolio model's
    folder and `pension-retirement` for the pension model's four; the stage
    of the library names the library's folder, `shelf`; and `From a
    folder…` names none. On a copy of `applications/cons-port`, whose
    trellis file writes its stages as records, the list's heading is `This
    folder's stages` and its items, `cons-port`'s stages, stand in no
    section. The sections' words and the item's are in sentence case
    (design pass 13 §3)."""
    library = tmp_path / "shelf"
    shutil.copytree(PORT_STAGE_FOLDER, library / "port")
    monkeypatch.setenv("BELLMAN_STAGE_LIBRARY", str(library))
    folder = model.open_folder(written_from_the_forms(tmp_path / "demo"))
    listed = trellis.stage_items(folder, trellis.show_trellis(folder, RECIPE).shown, {})
    assert listed["heading"] is None
    assert [(item["key"], item["model_folder"], item["section"]) for item in listed["items"]] == (
        [(key, "demo", "This folder's stages") for key in ("port", "cons", "disc")]
        # the template cons reads the demonstration's stage file since
        # decision SD-39
        + [
            (key, "cons-port", "Templates")
            for key in ("port", "cons", "disc", "noport")
        ]
        + [
            (key, "pension-retirement", "Templates")
            for key in ("worker_saving", "retire_choice", "retiree_saving", "terminal")
        ]
        + [("port", "shelf", "Library"), ("From a folder…", "", None)]
    )

    records = model.open_folder(records_folder(tmp_path / "records"))
    listed = trellis.stage_items(records, trellis.show_trellis(records, RECORDS).shown, {})
    assert listed["heading"] == "This folder's stages"
    assert [(item["key"], item["model_folder"], item["section"]) for item in listed["items"]] == [
        (key, "cons-port", None) for key in ("port", "cons", "disc")
    ]


def test_l_each_stage_s_periods_are_ranges_and_the_view_s_periods_its_restriction_s(
    durables_folder, consport_folder
):
    """Unit L, Task 11 (AAS, L-D10 and L-D11). The periods each stage key is
    listed in, read from the positions of its occurrences, are ranges as
    the page prints them: on the durables model's trellis under `periods
    0–2`, `0–50` for the three stages of every period and `0` for the
    bequest of the terminal period alone, the whole trellis read whatever
    the view draws; on a trellis whose stage stands in periods apart, each
    run of consecutive periods a range and a period alone by its number,
    `0, 2`. The periods the view draws are those its restriction holds,
    from the terminal one: `0, 1, 2` under `periods 0–2`; on lesson 05,
    `0, 1` under `periods 0–1, stages cons` and all six under none."""
    folder = model.open_folder(durables_folder)
    shown = trellis.show_trellis(folder, RECIPE, trellis.parse_restriction("periods 0–2")).shown
    assert trellis.listed_periods(shown) == {
        "tenure": "0–50",
        "keeper_cons": "0–50",
        "adjuster_cons": "0–50",
        "bequest": "0",
    }
    assert trellis.view_periods(shown) == [0, 1, 2]
    # a stand-in holding the one key `listed_periods` reads, a trellis of
    # three periods whose stage `b` stands in the first and the last
    periods = [{"stages": {"a": 0, "b": 0}}, {"stages": {"a": 0}}, {"stages": {"b": 0}}]
    apart = types.SimpleNamespace(trellis={"periods": periods})
    assert trellis.listed_periods(apart) == {"a": "0–1", "b": "0, 2"}
    lesson = model.open_folder(consport_folder)
    restricted = trellis.show_trellis(
        lesson, LESSON, trellis.parse_restriction("periods 0–1, stages cons")
    ).shown
    assert trellis.view_periods(restricted) == [0, 1]
    assert trellis.view_periods(trellis.show_trellis(lesson, LESSON).shown) == list(range(6))


# --- unit J, Task 19: the removal and the move of a join (J-D33, J-D34) ---

# the inter-period mapping of lesson 05's trellis file, and that mapping
# emptied
FILLED_MAPPING = "inter_connectors:\n  - {disc.a: k}\n"
# the keyed connector of `two_cons_one_joined`, from `port` to `cons_one`
KEYED_TO_CONS_ONE = "{from: port, to: cons_one, fields: {m_next: m}}"
# the join wire's port of `periods[2]/disc` in lesson 05's forward graph,
# which the join `a` by equal names reaches, and its label
DISC_ARRIVAL = "periods[2]/disc/disc:measure:arvl"
# the port of `disc`'s continuation field `a` in `periods[2]` of that graph,
# which the inter-period mapping `{a: k}` reads
DISC_LEAVING = "periods[2]/disc/joined:disc:cntn:a"


def test_j_a_join_within_a_period_is_removed_and_the_list_keeps_an_empty_mapping(tmp_path):
    """A join wire within a period (unit J's decisions J-D33 and J-D34;
    amendment 02, rulings 11 and 13): in lesson 05, the wire from `port`'s
    `m_next` to `cons`'s `m` in `periods[2]` is a join wire whose Details
    name the join, its two stage occurrences and the entry that writes it,
    a link to line 15 of the trellis file; the wire of the join `a` by equal
    names, which no entry writes, is a join wire too (unit L, Task 15),
    with no end to move, no field pairs, no file and not removable, and
    its removal writes and prints nothing. The first wire's removal takes the
    connector's only item out of the list and leaves `- {}` in its place,
    the note naming the file, the address, the item as written and the six
    periods it reached; nothing is written to disk. The trellis read from
    the text the removal made is drawn, not refused, with the two fields
    unjoined in every period. On the durables model, a wire that three keys
    of one flat connector write loses those keys alone, and the wire of
    three keys of the standing inter-period mapping leaves the other three,
    each note listing the pairs taken out."""
    copy = applications_copy(tmp_path / "lesson")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    wires = {(wire["from"], wire["to"]): wire for wire in trellis.join_wires(shown)}
    shown_keys = ("join", "between", "movable", "fields", "file", "removable")
    by_names = wires["periods[2]/cons", "periods[2]/disc"]
    assert {key: by_names[key] for key in shown_keys} == {
        "join": "a",
        "between": False,
        "movable": [],
        "fields": [],
        "file": None,
        "removable": False,
    }
    event = join_event(shown, folder, "periods[2]/cons", "periods[2]/disc")
    nothing = trellis.Gesture(None, None, (), None, None, None, None)
    assert trellis.removal_edit(shown, event, {}) == nothing
    wire = wires["periods[2]/port", "periods[2]/cons"]
    assert {key: wire[key] for key in shown_keys if key != "fields"} == {
        "join": JOIN,
        "between": False,
        "movable": BOTH_ENDS,
        "file": "trellis.port-cons.yml",
        "removable": True,
    }
    link = trellis.Link(
        "declaration/trellis.port-cons.yml · periods[0].connectors[0]", PORT_CONS, 15
    )
    assert dict(trellis.join_rows(folder, shown, wire).rows)["written"][0].parts == (link,)
    assert (wire["writing"], wire["reading"]) == ({"h": 2, "key": "port"}, {"h": 2, "key": "cons"})
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    event = join_event(shown, folder, "periods[2]/port", "periods[2]/cons")
    gesture = trellis.removal_edit(shown, event, {})
    assert gesture == trellis.Gesture(
        {path: text.replace(FILLED_ENTRY, EMPTIED_ENTRY)},
        {path: text},
        (),
        "trellis.port-cons.yml, periods[0].connectors[0]: {m_next: m} removed, periods 0–5",
        None,
        path,
        "periods[0].connectors[0]",
    )
    assert (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8") == text
    unsaved = unsaved_of(copy, {PORT_CONS: gesture.edits[path]})
    outcome = trellis.show_trellis(folder, LESSON, previous=shown, unsaved=unsaved)
    assert outcome.refusal is None and JOIN not in join_labels(outcome.shown.collection, "forward")
    ports = {
        (port["side"], port["h"], port["key"], port["field"])
        for port in trellis.unjoined_ports(outcome.shown, trellis.texts_of(unsaved))
    }
    assert {("writing", h, "port", "m_next") for h in range(6)} <= ports
    assert {("reading", h, "cons", "m") for h in range(6)} <= ports
    # the fourteen ports unjoined, the two ends among them, are one field
    # the checklist lists, the arrival field m of cons outside the earliest
    # period (unit L, Task 21)
    assert len(trellis.unjoined_ports(outcome.shown, {})) == 14
    assert trellis.unjoined_count(outcome.shown) == 1 and trellis.unjoined_count(shown) == 0

    durables = model.open_folder(ROOT / "applications/durables")
    held = trellis.show_trellis(durables, recipe.Source("recipe", "declaration/spec.yml")).shown
    written = (ROOT / "applications/durables/declaration/trellis.yml").read_text(encoding="utf-8")
    file = str((ROOT / "applications/durables/declaration/trellis.yml").resolve())
    within = trellis.removal_edit(
        held, join_event(held, durables, "periods[0]/keeper_cons", "periods[0]/bequest"), {}
    )
    assert within.note == (
        "trellis.yml, periods[0].connectors[0]: a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq "
        "removed, periods 0"
    )
    assert within.edits == {
        file: written.replace(
            "{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq,",
            "{a_nxt_adj: a_bq,",
        )
    }
    between = trellis.removal_edit(
        held, join_event(held, durables, "periods[3]/adjuster_cons", "periods[2]/tenure"), {}
    )
    assert between.note == (
        "trellis.yml, inter_connectors[0]: a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z removed, "
        "periods 0–50"
    )
    assert entry_value(between.edits[file], "inter_connectors") == [
        {"a_nxt_kp": "a", "h_nxt_kp": "h", "z_nxt_kp": "z"}
    ]


def test_j_a_join_between_periods_is_removed_and_the_count_of_mappings_never_changes(tmp_path):
    """A join wire between two periods (unit J's decisions J-D33 and J-D34;
    amendment 02, ruling 13): in lesson 05, the wire from `disc`'s `a` in
    `periods[3]` to `port`'s `k` in `periods[2]` is written by the key `a`
    of the one inter-period mapping, which stands for every pair; its
    removal leaves that mapping `{}`, so that the list still holds one
    mapping, and the note names the six periods. Where the file writes one
    mapping for each of the five pairs, read from an unsaved text, the
    removal empties the mapping of the pair of the wire alone and names its
    two periods; the list keeps its five mappings."""
    copy = applications_copy(tmp_path / "lesson")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    wire = {(w["from"], w["to"]): w for w in trellis.join_wires(shown)}[
        "periods[3]/disc", "periods[2]/port"
    ]
    assert (wire["join"], wire["between"], wire["movable"]) == (
        "inter_connectors[2] a → k",
        True,
        BOTH_ENDS,
    )
    link = trellis.Link("declaration/trellis.port-cons.yml · inter_connectors[0]", PORT_CONS, 13)
    assert dict(trellis.join_rows(folder, shown, wire).rows)["written"][0].parts == (link,)
    event = join_event(shown, folder, "periods[3]/disc", "periods[2]/port")
    assert trellis.removal_edit(shown, event, {}) == trellis.Gesture(
        {path: text.replace(FILLED_MAPPING, EMPTIED_MAPPING)},
        {path: text},
        (),
        "trellis.port-cons.yml, inter_connectors[0]: disc.a: k removed, periods 0–5",
        None,
        path,
        "inter_connectors[0]",
    )
    five = text.replace(FILLED_MAPPING, "inter_connectors:\n" + "  - {disc.a: k}\n" * 5)
    unsaved = unsaved_of(copy, {PORT_CONS: five})
    texts = trellis.texts_of(unsaved)
    held = trellis.show_trellis(folder, LESSON, previous=shown, unsaved=unsaved).shown
    event = join_event(held, folder, "periods[3]/disc", "periods[2]/port", texts=texts)
    gesture = trellis.removal_edit(held, event, texts)
    assert gesture.note == "trellis.port-cons.yml, inter_connectors[2]: disc.a: k removed, periods 2–3"
    assert (
        entry_value(gesture.edits[path], "inter_connectors")
        == [{"disc.a": "k"}] * 2 + [{}] + [{"disc.a": "k"}] * 2
    )
    assert gesture.read == {path: five}
    assert (copy / PORT_CONS).read_text(encoding="utf-8") == text


def test_j_a_moved_end_types_the_new_line_in_place_of_the_old_in_one_edit(tmp_path):
    """A move of one end of a join wire (unit J's decision J-D33; amendment
    02, ruling 14): the old entry is taken out and the line the package's
    `connector_entry` answers for the new pair of ports typed in its place,
    one edit of the file's text, which differs from the text read in that
    line alone. Within a period, on `two_cons_one_joined`, the reading end
    of the keyed connector from `port` to `cons_one` moved to `cons_two`'s
    unjoined `m` types the keyed connector to `cons_two` into the `{}` the
    removal left. Between two periods, on lesson 05 with its connector
    emptied, the reading end of the join `a: k` moved to `cons`'s unjoined
    `m` in `periods[2]` makes the mapping `{a: m}`, and its writing end
    moved to `port`'s unjoined `m_next` in `periods[3]` makes it `{m_next:
    k}`. Each note names the old entry and the new line, `… a: k changed to
    a: m, periods 0–5`."""
    copy = two_cons_one_joined(tmp_path / "two")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    event = join_event(
        shown, folder, "periods[2]/port", "periods[2]/cons_one", "reading", (2, "cons_two", "m")
    )
    keyed_to_cons_two = KEYED_TO_CONS_ONE.replace("cons_one", "cons_two")
    assert trellis.removal_edit(shown, event, {}) == trellis.Gesture(
        {path: text.replace(KEYED_TO_CONS_ONE, keyed_to_cons_two)},
        {path: text},
        (),
        f"trellis.port-cons.yml, periods[0].connectors[0]: {KEYED_TO_CONS_ONE} changed to "
        f"{keyed_to_cons_two}, periods 0–5",
        None,
        path,
        "periods[0].connectors[0]",
    )

    copy = applications_copy(tmp_path / "lesson")
    folder = model.open_folder(copy)
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8").replace(FILLED_ENTRY, EMPTIED_ENTRY)
    (copy / PORT_CONS).write_text(text, encoding="utf-8")
    shown = trellis.show_trellis(folder, LESSON).shown
    event = join_event(
        shown, folder, "periods[3]/disc", "periods[2]/port", "reading", (2, "cons", "m")
    )
    assert trellis.removal_edit(shown, event, {}) == trellis.Gesture(
        {path: text.replace(FILLED_MAPPING, "inter_connectors:\n  - {a: m}\n")},
        {path: text},
        (),
        "trellis.port-cons.yml, inter_connectors[0]: a: k changed to a: m, periods 0–5",
        None,
        path,
        "inter_connectors[0]",
    )
    event = join_event(
        shown, folder, "periods[3]/disc", "periods[2]/port", "writing", (3, "port", "m_next")
    )
    assert trellis.removal_edit(shown, event, {}) == trellis.Gesture(
        {path: text.replace(FILLED_MAPPING, "inter_connectors:\n  - {m_next: k}\n")},
        {path: text},
        (),
        "trellis.port-cons.yml, inter_connectors[0]: a: k changed to m_next: k, periods 0–5",
        None,
        path,
        "inter_connectors[0]",
    )


def test_j_a_move_to_a_joined_port_and_an_event_of_another_graph_type_nothing(tmp_path):
    """What a removal or a move types nothing for (unit J's plan, Task 19,
    its rulings; amendment 02, ruling 14), each sentence giving what to do
    for the gesture made (spec 0.4 §3.1; unit J's plan, Task 17). A move of
    the reading end of the join `m_next → m` of lesson 05 to the port of
    `disc`'s arrival measure in `periods[2]`, which the join `a` by equal
    names reaches, answers the sentence that the port is joined, at the
    connector's file and address, the end to be moved to a field's port,
    since a reading end may land on a joined field (J-D42); a move of its
    writing end to `disc`'s continuation field `a`, which the inter-period
    mapping reads, answers it with the field as the file writes it, `a`,
    the end to be moved to a port marked unjoined. A move to a port of the
    other side, an event of another source, graph or elaboration number, a
    wire the view does not draw, a record that is no event, and an input
    that changed since the reading answer "An old graph", whose last
    sentence names the gesture: a move is dragged again, and a removal,
    which is no drag, is made again. On the durables model a move that
    names one port for a wire that several entries write answers "An old
    graph", since such a wire moves through its list (unit K's decision
    K-D23, Task 22). Nothing is written to disk."""
    copy = applications_copy(tmp_path / "lesson")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    event = join_event(shown, folder, "periods[2]/port", "periods[2]/cons")
    label = next(
        pair["value"]
        for node in graph_named(shown.collection, "forward")["nodes"]
        for item in node.get("inputsMetadata") or []
        if item["id"] == DISC_ARRIVAL
        for pair in item["attrs"]
        if pair["key"] == "label"
    )
    assert trellis.removal_edit(
        shown, {**event, "end": "reading", "handle": DISC_ARRIVAL}, {}
    ) == (
        trellis.Gesture(
            None,
            None,
            (),
            None,
            f"trellis.port-cons.yml, periods[0].connectors[0]: nothing was written. The port "
            f"{label} is joined. Move the end to a field's port.",
            path,
            "periods[0].connectors[0]",
        )
    )
    assert trellis.removal_edit(
        shown, {**event, "end": "writing", "handle": DISC_LEAVING}, {}
    ) == (
        trellis.Gesture(
            None,
            None,
            (),
            None,
            "trellis.port-cons.yml, periods[0].connectors[0]: nothing was written. The port a "
            "is joined. Move the end to a port marked unjoined.",
            path,
            "periods[0].connectors[0]",
        )
    )
    ends = {(port["side"], port["h"]): port["id"] for port in trellis.unjoined_ports(shown)}
    reading = event["reading"]
    old = trellis.Gesture(None, None, (), None, OLD_GRAPH, path, None)
    for wrong in (
        {**event, "end": "reading", "handle": ends["writing", 0]},
        {**event, "end": "writing", "handle": ends["reading", 5]},
        {**event, "end": "sideways", "handle": ends["reading", 5]},
        {**event, "end": "reading", "reading": {**reading, "graph": "backward"}},
    ):
        assert trellis.removal_edit(shown, wrong, {}) == old
    old = old._replace(sentence=OLD_GRAPH_REMOVAL)
    for wrong in (
        {**event, "reading": {**reading, "graph": "backward"}},
        {**event, "reading": {**reading, "number": reading["number"] + 1}},
        {**event, "reading": {**reading, "source": "declaration/trellis.port-cons-vfi.yml"}},
        {**event, "join": {**event["join"], "targetHandle": DISC_ARRIVAL}},
        {**event, "join": None},
        None,
        "removed",
    ):
        assert trellis.removal_edit(shown, wrong, {}) == old
    assert (
        trellis.removal_edit(shown, event, {path: text.replace("repeat: 6", "repeat: 5")}) == old
    )
    assert (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8") == text

    durables = model.open_folder(ROOT / "applications/durables")
    held = trellis.show_trellis(durables, recipe.Source("recipe", "declaration/spec.yml")).shown
    several = join_event(held, durables, "periods[0]/keeper_cons", "periods[0]/bequest")
    end = next(port["id"] for port in trellis.unjoined_ports(held) if port["side"] == "reading")
    gesture = trellis.removal_edit(held, {**several, "end": "reading", "handle": end}, {})
    assert gesture.sentence is not None and gesture.sentence.startswith("trellis.yml: nothing")
    assert gesture.edits is None


def test_j_a_moved_reading_end_whose_continuation_field_keeps_a_join_types_nothing(
    monkeypatch, tmp_path
):
    """Unit J's decision J-D41 and plan, Task 17: where the package answers
    `port-joined` for the new line of a moved reading end, since the kept
    continuation field `m_next` is still read by another join once the
    old entry is taken out, no move of the reading end can succeed, and the
    answer is the sentence of a joined continuation port at the connector's
    file and address, not a request to move the end elsewhere. The package
    refuses a second connector for one continuation field
    (`connector-names-no-field`), so the case is made by the package's
    answer given in place of `connector_entry`'s; nothing is written."""
    copy = applications_copy(tmp_path / "lesson")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, LESSON).shown
    path = str((copy / PORT_CONS).resolve())
    text = (copy / PORT_CONS).read_text(encoding="utf-8")
    # the package's answer for `disc`'s `a`, which the inter-period mapping
    # reads
    joined = trellis.connector_entry(shown.trellis, (2, "disc", "a"), (1, "port", "k"))
    assert joined.reason == "port-joined"
    monkeypatch.setattr(trellis, "connector_entry", lambda *_: joined)
    event = join_event(shown, folder, "periods[2]/port", "periods[2]/cons")
    reading = {**event, "end": "reading", "handle": "periods[2]/disc/joined:disc:arvl:a"}
    assert trellis.removal_edit(shown, reading, {}) == trellis.Gesture(
        None,
        None,
        (),
        None,
        "trellis.port-cons.yml, periods[0].connectors[0]: nothing was written. The port m_next "
        "is joined. A continuation field joins one arrival field.",
        path,
        "periods[0].connectors[0]",
    )
    assert (copy / PORT_CONS_RECORDS).read_text(encoding="utf-8") == text


# --- unit K, Task 11: two stage occurrences joined in one gesture ---

# the ports of the forward trellis graph of the copy `emptied_portfolio` that
# a join of the frames of `port` and `cons` in `periods[2]` names, and
# `cons`'s `m` in `periods[1]`, the period after it in time
PORT_M_NEXT = "periods[2]/port/unjoined:port:cntn:m_next"
CONS_M = "periods[2]/cons/unjoined:cons:arvl:m"
NEXT_CONS_M = "periods[1]/cons/unjoined:cons:arvl:m"


def frame_event(shown, folder, writer: tuple, reader: tuple, fields) -> dict:
    """The record of the event `connected` that the graph region sends for
    the button `join` of the list a drag from the frame of the stage
    occurrence `writer` to the frame of `reader` opens, each `(h, key)`,
    with the pairs `fields` ticked, each `(continuation field, arrival
    field)` (unit K's decision K-D8): `reading`, the record
    `trellis.reading_record` gives for the model folder `folder`; `source`
    and `target`, the layer ids of the two frames; and `pairs`, the ids of
    the two ports of each pair (`field_port`)."""
    (h, key), (h2, key2) = writer, reader
    return {
        "reading": trellis.reading_record(folder, shown),
        "source": f"periods[{h}]/{key}{LAYER_ID_ENDING}",
        "target": f"periods[{h2}]/{key2}{LAYER_ID_ENDING}",
        "pairs": [
            {
                "sourceHandle": field_port(shown, "writing", (h, key, field))["id"],
                "targetHandle": field_port(shown, "reading", (h2, key2, arrival))["id"],
            }
            for field, arrival in fields
        ],
    }


def test_k_a_continuation_field_pairs_with_the_arrival_field_of_its_name_less_a_suffix(
    tmp_path,
):
    """Unit K's decision K-D8 (plan, Task 11): a continuation field pairs
    with an arrival field of the same name, or of the same name after a
    suffix `_next`, `_nxt`, `_kp`, `_adj` or `_<label>`, for a branch label
    of its stage, is dropped from its end, one suffix after another
    (`pairing_names`). In the records the graph region is given
    (`connectable_ports`), each writing port names, for each stage
    occurrence a drag from it can reach that holds an unjoined arrival field
    whose name pairs with its own, that field's port. On the copy
    `emptied_portfolio`, `port`'s `m_next` in `periods[2]` names `cons`'s `m`
    in `periods[2]` and in `periods[1]`; `disc`'s `a` in `periods[3]` names
    none, since no unjoined arrival field it can reach is named `a`, and
    `disc`'s own `a`, which a join by equal names reaches, is offered as a
    further source and never proposed (J-D41); no reading port names a pair.
    On the copy `durables_without_a`, read as it opens, `periods 0–2`,
    `keeper_cons`'s `a_nxt_kp` in `periods[2]` names `tenure`'s `a` in
    `periods[1]`."""
    assert trellis.pairing_names("m_next") == ("m_next", "m")
    assert trellis.pairing_names("a_nxt_kp") == ("a_nxt_kp", "a_nxt", "a")
    assert trellis.pairing_names("z_adj_next") == ("z_adj_next", "z_adj", "z")
    assert trellis.pairing_names("w_keep", ("keep", "adjust")) == ("w_keep", "w")
    assert trellis.pairing_names("w_keep") == ("w_keep",)
    assert trellis.pairing_names("a") == ("a",)
    assert trellis.pairing_names("_kp") == ("_kp",)

    copy = emptied_portfolio(tmp_path / "portfolio")
    shown = trellis.show_trellis(model.open_folder(copy), RECIPE).shown
    records = {record["id"]: record for record in trellis.connectable_ports(shown, {})}
    assert records[PORT_M_NEXT]["pairs"] == {
        "periods[2]/cons": CONS_M,
        "periods[1]/cons": NEXT_CONS_M,
    }
    assert records["periods[3]/disc/unjoined:disc:cntn:a"]["pairs"] == {}
    assert "periods[2]/disc/joined:disc:arvl:a" in records
    for record in records.values():
        assert ("pairs" in record) == (record["side"] == "writing"), record

    durables = durables_without_a(tmp_path / "durables")
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(model.open_folder(durables), RECIPE, restriction).shown
    records = {record["id"]: record for record in trellis.connectable_ports(shown, {})}
    keeper = records["periods[2]/keeper_cons/unjoined:keeper_cons:cntn:a_nxt_kp"]
    assert keeper["pairs"]["periods[1]/tenure"] == "periods[1]/tenure/unjoined:tenure:arvl:a"


def test_k_the_join_of_two_frames_types_the_pairs_ticked_as_one_mapping(tmp_path):
    """Unit K's decision K-D8 (plan, Task 11; spec 0.4 §3.1's form of the
    line): the event `connected` of the join of two frames, whose `pairs`
    name the ports of the pairs the author ticked, is answered by
    `connector_edit` with the pairs typed as one mapping. One pair within a
    period answers what the drag between its two ports answers: on the copy
    `emptied_portfolio` the flat connector `{m_next: m}` in the period
    file, and on the copy `two_cons_period`, where `cons_one` and `cons_two`
    both arrive at `m`, the keyed connector from `port` to `cons_two`. Two
    pairs between two periods are two entries of one mapping: on the copy
    `emptied_pension`, `retiree_saving`'s `y_f_ret` and `y_p_ret` in
    `periods[2]` joined to its `y_f_r` and `y_p_r` in `periods[1]` fill the
    emptied standing mapping with the line that unit J's item 4 types by
    two drags, the note naming both entries. An event whose pairs are none,
    name one writing port twice or name two reading occurrences answers
    "An old graph", and nothing is written."""
    copy = emptied_portfolio(tmp_path / "portfolio")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, RECIPE).shown
    drag = trellis.connector_edit(shown, connected_event(shown, folder, *WITHIN), {})
    event = frame_event(shown, folder, (2, "port"), (2, "cons"), [("m_next", "m")])
    assert drag.note == "period.yml, connectors[0]: {m_next: m} written, flat, periods 0–5"
    assert trellis.connector_edit(shown, event, {}) == drag

    lesson = two_cons_period(tmp_path / "two")
    folder = model.open_folder(lesson)
    shown = trellis.show_trellis(folder, LESSON).shown
    within = ((2, "port", "m_next"), (2, "cons_two", "m"))
    drag = trellis.connector_edit(shown, connected_event(shown, folder, *within), {})
    event = frame_event(shown, folder, (2, "port"), (2, "cons_two"), [("m_next", "m")])
    assert "{from: port, to: cons_two, fields: {m_next: m}} written, keyed," in drag.note
    assert trellis.connector_edit(shown, event, {}) == drag

    pension = emptied_pension(tmp_path / "pension")
    folder = model.open_folder(pension)
    shown = trellis.show_trellis(folder, RECIPE).shown
    path = str((pension / TRELLIS_FILE).resolve())
    text = (pension / TRELLIS_FILE).read_text(encoding="utf-8")
    assert text.count("  - {}\n") == 1
    first = trellis.connector_edit(
        shown,
        connected_event(
            shown, folder, (2, "retiree_saving", "y_f_ret"), (1, "retiree_saving", "y_f_r")
        ),
        {},
    )
    assert first.note.startswith(
        "trellis.yml, inter_connectors[0]: y_f_ret: y_f_r written, entry, periods 0–"
    )
    pairs = [("y_f_ret", "y_f_r"), ("y_p_ret", "y_p_r")]
    event = frame_event(shown, folder, (2, "retiree_saving"), (1, "retiree_saving"), pairs)
    assert trellis.connector_edit(shown, event, {}) == trellis.Gesture(
        {path: text.replace("  - {}\n", "  - {y_f_ret: y_f_r, y_p_ret: y_p_r}\n")},
        {path: text},
        (),
        first.note.replace(
            "y_f_ret: y_f_r written, entry,", "y_f_ret: y_f_r, y_p_ret: y_p_r written, entries,"
        ),
        None,
        path,
        "inter_connectors[0]",
    )

    elsewhere = field_port(shown, "reading", (2, "retiree_saving", "y_p_r"))["id"]
    for pairs in (
        [],
        [event["pairs"][0]] * 2,
        [event["pairs"][0], {**event["pairs"][1], "targetHandle": elsewhere}],
    ):
        answer = trellis.connector_edit(shown, {**event, "pairs": pairs}, {})
        assert answer == old_graph_gesture(pension / TRELLIS_FILE), pairs
    assert (pension / TRELLIS_FILE).read_text(encoding="utf-8") == text


# --- unit K, Task 22: every join wire can be moved (K-D23) ---

# the standing inter-period mapping of the durables model's trellis file
DURABLES_MAPPING = (
    "  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}\n"
)
# the three continuation fields of `keeper_cons` that the mapping joins to
# `tenure` of the next period, each with the arrival field it joins there
# and the arrival field of `bequest` that holds the same state
KEEPER_FIELDS = (("a_nxt_kp", "a", "a_bq"), ("h_nxt_kp", "h", "h_bq"), ("z_nxt_kp", "z", "z_bq"))
# the declared set of each of those arrival fields, which keeper_cons.bl also
# writes for the continuation field joined to it (unit K's decision K-D25)
KEEPER_SETS = {"a": "ℝ₊", "h": "ℝ₊₊", "z": "ℝ₊₊"}
# the ends a drag can move of a join wire, and of the piece that the wires of
# an adjacent pair of periods share, whose writing end is a period
BOTH_ENDS = ["writing", "reading"]
READING_END = ["reading"]


def moved_event(shown, folder, writing: str, reading: str, end: str, moves, texts=None) -> dict:
    """The record of the event `moved` that the button `join` of the list
    sends for a move of the end `end`, `reading` or `writing`, of the join
    wire from the stage occurrence `writing` to `reading`, each by its
    address, `periods[1]/keeper_cons` or, for the piece of a pair of
    periods, `periods[1]` (unit K's decision K-D23): `reading` and `join`
    as `join_event` gives them, `end`, and `pairs`, one record for each
    move of `moves`, `(kept, new, replaced)`, each a port `(h, key,
    field)`, the port the pair keeps, the new port and the port of the
    moved end that the pair leaves, as the ids of the new pair's writing
    and reading ports and of the port it leaves (`field_port`)."""
    event = join_event(shown, folder, writing, reading, texts=texts)
    other = "writing" if end == "reading" else "reading"
    pairs = []
    for kept, new, replaced in moves:
        ends = field_port(shown, other, kept)["id"], field_port(shown, end, new)["id"]
        source, target = ends if end == "reading" else ends[::-1]
        left = field_port(shown, end, replaced)["id"]
        pairs.append({"sourceHandle": source, "targetHandle": target, "replaced": left})
    return {**event, "end": end, "pairs": pairs}


def replaced_lines(before: str, after: str) -> list[tuple[str, str]]:
    """The pairs of a line of `before` and the line of `after` that stands
    at the same place and differs from it, of two texts of one number of
    lines; `workbench_support.changed_lines` answers the numbers of those
    lines."""
    old, new = before.split("\n"), after.split("\n")
    assert len(old) == len(new)
    return [(one, other) for one, other in zip(old, new) if one != other]


def test_k_a_wire_of_several_entries_moves_the_pairs_ticked_in_one_edit(tmp_path):
    """A complete two-coordinate fixture checks partial and grouped moves
    from two source stages without relying on an incomplete application."""
    copy = composition_folder(tmp_path / "composition", repeat=3, two_fields=True)
    file = copy / "trellis.yml"
    text = file.read_text(encoding="utf-8").replace(
        "inter_connectors: []", "inter_connectors: [{a: x, b: q, c: x, f: q}]")
    file.write_text(text, encoding="utf-8")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
    assert not shown.selection.diagnostics
    writer, reader = "periods[1]/S", "periods[0]/S"
    moves = [((1, "S", field), (0, "T", other), (0, "S", arrival))
             for field, arrival, other in (("a", "x", "a"), ("b", "q", "b"))]
    event = moved_event(shown, folder, writer, reader, "reading", moves)
    changed = trellis.removal_edit(shown, event, {})
    assert changed.sentence is None and changed.edits
    assert entry_value(changed.edits[str(file)], "inter_connectors") == [
        {"c": "x", "f": "q", "a": "a", "b": "b"}]
    assert "no longer selected" in changed.note and "now selected" in changed.note
    reopened = trellis.show_trellis(folder, shown.source, previous=shown, unsaved={
        path: trellis.Unsaved(text, 1) for path, text in changed.edits.items()
    }).shown
    assert not reopened.selection.diagnostics
    partial = trellis.removal_edit(shown, {**event, "pairs": event["pairs"][:1]}, {})
    assert entry_value(partial.edits[str(file)], "inter_connectors") == [
        {"b": "q", "c": "x", "f": "q", "a": "a"}]
    both = moves + [((1, "U", f), (0, "T", t), (0, "S", a))
                    for f, a, t in (("c", "x", "a"), ("f", "q", "b"))]
    grouped = trellis.removal_edit(shown, moved_event(
        shown, folder, "periods[1]", reader, "reading", both), {})
    assert grouped.sentence is None and grouped.edits
    assert entry_value(grouped.edits[str(file)], "inter_connectors") == [
        {"a": "a", "b": "b", "c": "a", "f": "b"}]
    old = old_graph_gesture(file)
    for wrong in ({**event, "pairs": []},
                  {**event, "pairs": event["pairs"][:1] * 2},
                  {**event, "pairs": [{**event["pairs"][0], "replaced": None}]}):
        assert trellis.removal_edit(shown, wrong, {}) == old
    assert file.read_text(encoding="utf-8") == text


def test_k_a_move_proposes_the_fields_whose_names_pair_and_moves_a_writing_end(durables_folder):
    """Unit K's decision K-D23 (plan, Task 22) with K-D8's pairing. A field
    pair of a join wire proposes, for each stage occurrence the moved end
    can reach, the port whose name pairs (`pairing_names`): on the durables
    model read with both entries of the state `a` taken out of the standing
    mapping, the reading end of the wire from `keeper_cons` to `bequest` in
    periods[0] proposes for `a_nxt_kp` the unjoined `a` of `tenure`, and
    for `h_nxt_kp` and `z_nxt_kp` the `h` and `z` of `tenure`, which joins
    reach, since a move proposes such a port (unit L, Task 19; row K-I216
    amended); read with `a_nxt_adj: a` alone taken out, the writing end
    of the wire from `keeper_cons` in periods[1] to `tenure` proposes for
    `a` the unjoined `a_nxt_adj` of `adjuster_cons`. The move of that
    writing end with that pair alone ticked replaces `a_nxt_kp: a` by
    `a_nxt_adj: a` and keeps the other two entries; a move to a writing
    port that a join reads answers that the port is joined, with nothing
    typed."""
    folder = model.open_folder(durables_folder)
    restriction = trellis.parse_restriction("periods 0–2")
    shown = trellis.show_trellis(folder, RECIPE, restriction).shown
    file = durables_folder / TRELLIS_FILE
    path, text = str(file.resolve()), file.read_text(encoding="utf-8")

    without_a = text.replace(
        DURABLES_MAPPING, "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z}\n"
    )
    unsaved = unsaved_of(durables_folder, {TRELLIS_FILE: without_a})
    texts = trellis.texts_of(unsaved)
    held = trellis.show_trellis(folder, RECIPE, restriction, previous=shown, unsaved=unsaved).shown
    wires = {(w["from"], w["to"]): w for w in trellis.join_wires(held, texts)}
    fields = wires["periods[0]/keeper_cons", "periods[0]/bequest"]["fields"]
    tenure_a, tenure_h, tenure_z = (
        field_port(held, "reading", (0, "tenure", field))["id"] for field in ("a", "h", "z")
    )
    assert tenure_a.startswith("periods[0]/tenure/unjoined:")
    assert tenure_h.startswith("periods[0]/tenure/joined:")
    assert [field["readers"] for field in fields] == [
        {"periods[0]/tenure": port} for port in (tenure_a, tenure_h, tenure_z)
    ]

    without_adjuster_a = text.replace(
        DURABLES_MAPPING,
        "  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z}\n",
    )
    unsaved = unsaved_of(durables_folder, {TRELLIS_FILE: without_adjuster_a})
    texts = trellis.texts_of(unsaved)
    held = trellis.show_trellis(folder, RECIPE, restriction, previous=shown, unsaved=unsaved).shown
    writer, reader = "periods[1]/keeper_cons", "periods[0]/tenure"
    wire = {(w["from"], w["to"]): w for w in trellis.join_wires(held, texts)}[writer, reader]
    adjuster_a = field_port(held, "writing", (1, "adjuster_cons", "a_nxt_adj"))["id"]
    assert [field["writers"] for field in wire["fields"]] == [
        {"periods[1]/adjuster_cons": adjuster_a},
        {},
        {},
    ]
    move = [
        ((0, "tenure", "a"), (1, "adjuster_cons", "a_nxt_adj"), (1, "keeper_cons", "a_nxt_kp"))
    ]
    event = moved_event(held, folder, writer, reader, "writing", move, texts=texts)
    assert without_drafts(trellis.removal_edit(held, event, texts)) == trellis.Gesture(
        {
            path: text.replace(
                DURABLES_MAPPING,
                "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z, a_nxt_adj: a}\n",
            )
        },
        {path: without_adjuster_a},
        (),
        "trellis.yml, inter_connectors[0]: a_nxt_adj: a written, periods 0–50; "
        "no longer selected: " + ", ".join(
            f"periods[{h}].keeper_cons.a_nxt_kp → periods[{h-1}].tenure.a" for h in range(1, 51)
        ) + "; now selected: " + ", ".join(
            f"periods[{h}].adjuster_cons.a_nxt_adj → periods[{h-1}].tenure.a" for h in range(1, 51)
        ),
        None,
        path,
        "inter_connectors[0]",
    )
    joined = [
        ((0, "tenure", "a"), (1, "adjuster_cons", "h_nxt_adj"), (1, "keeper_cons", "a_nxt_kp"))
    ]
    event = moved_event(held, folder, writer, reader, "writing", joined, texts=texts)
    # a writing end may land on a joined writing port: the write releases the
    # pair that read it, `h_nxt_adj: h`, and types the new one (design pass 10
    # §7; unit N, Task 7), where before it refused that the port is joined
    landed = without_drafts(trellis.removal_edit(held, event, texts))
    assert landed.sentence is None, landed.sentence
    assert landed.note.startswith("trellis.yml, inter_connectors[0]: h_nxt_adj: a written, periods 0–50"), landed.note
    assert entry_value(landed.edits[path], "inter_connectors") == [
        {"h_nxt_kp": "h", "z_nxt_kp": "z", "z_nxt_adj": "z", "h_nxt_adj": "a"}
    ]
    assert file.read_text(encoding="utf-8") == text


# --- unit K, Task 24: the pairing list prints each field's set (K-D25) ---

# the perch of the fields of each side of a port of the forward trellis graph
SIDE_PERCH = {"writing": "cntn", "reading": "arvl"}


def fields_tab_sets(path: Path) -> dict[tuple[str, str], str]:
    """The set the Fields tab prints for each field of the stage file
    `path`, by the field's perch and name: the rows of `model.classification`
    of the file's elaboration and of the package's span table of its text,
    as the tab reads them (AMD-MI-002 §5)."""
    text = path.read_text(encoding="utf-8")
    stage = model.elaborate_buffer(text, str(path)).stage
    groups = model.classification(stage, source_spans(text, str(path)))
    return {(group.perch, row.stem): row.set for group in groups for row in group.rows}


def test_k_a_pairing_record_holds_its_field_s_set_as_the_fields_tab_prints_it(
    tmp_path, durables_folder
):
    """Unit K's decision K-D25 (plan, Task 24): the records from which the
    graph region builds its pairing lists hold each field's declared set as
    the Fields tab of its stage file prints it. On the copy
    `emptied_portfolio`, every record `connectable_ports` answers holds
    `set`, that of its field, `ℝ₊₊` for `port`'s continuation field
    `m_next`. On the durables model, `periods 0–2`, every field pair of every
    join wire `join_wires` answers holds `field_set` and `arrival_set`, the
    sets of its continuation field and of the field of the reading stage's
    entry perch, which the port's id names, the decision perch of the two
    consumption stages (decision MB-U31), `ℝ₊` for both fields of the pair
    `a_nxt_kp → a` of the wire from `keeper_cons` in periods[1] to `tenure`
    in periods[0]. The records compare no sets."""
    copy = emptied_portfolio(tmp_path / "portfolio")
    shown = trellis.show_trellis(model.open_folder(copy), RECIPE).shown
    records = trellis.connectable_ports(shown, {})
    tabs = {}
    for record in records:
        key = record["key"]
        if key not in tabs:
            tabs[key] = fields_tab_sets(copy / f"declaration/stages/{key}/{key}.bl")
        assert record["set"] == tabs[key][SIDE_PERCH[record["side"]], record["field"]], record
    assert {record["id"]: record["set"] for record in records}[PORT_M_NEXT] == "ℝ₊₊"

    folder = model.open_folder(durables_folder)
    shown = trellis.show_trellis(folder, RECIPE, trellis.parse_restriction("periods 0–2")).shown
    tabs = {}
    checked = 0
    for wire in trellis.join_wires(shown):
        for pair in wire["fields"]:
            sets = []
            for side, name in (("writing", pair["field"]), ("reading", pair["arrival"])):
                # the stage key is the second segment of the port's id and
                # the perch the one before the field's name,
                # `periods[1]/keeper_cons/joined:keeper_cons:cntn:a_nxt_kp`
                key, perch = pair[side].split("/")[1], pair[side].split(":")[-2]
                if key not in tabs:
                    path = durables_folder / f"declaration/stages/{key}/{key}.bl"
                    tabs[key] = fields_tab_sets(path)
                sets.append(tabs[key][perch, name])
            assert [pair["field_set"], pair["arrival_set"]] == sets, pair
            checked += 1
    assert checked > 0
    keeper = {(w["from"], w["to"]): w for w in trellis.join_wires(shown)}[
        "periods[1]/keeper_cons", "periods[0]/tenure"
    ]
    assert [
        (f["field"], f["field_set"], f["arrival"], f["arrival_set"]) for f in keeper["fields"]
    ] == [
        (field, KEEPER_SETS[arrival], arrival, KEEPER_SETS[arrival])
        for field, arrival, _ in KEEPER_FIELDS
    ]


# --- unit L, Task 19: a drag adds to the pair's mapping, the list of a move
# ticks by name and offers the writer's fields (defects 10 and 13) ---

# the connector of the pension model's periods[0], as the post-doc wrote it
PENSIONS_CONNECTOR = "      - {a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq}\n"
# the unjoined continuation fields of `shocks` in periods[0] of that model
SHOCKS_OTHERS = ["plan_s", "y_s", "α_s", "β_s", "ξ_s", "π_s"]


def pensions_connectors(folder: Path, lines: str) -> tuple[str, str]:
    """The resolved path and the text of the trellis file of the pension
    copy `folder` once its connector of periods[0] is replaced by the
    connector lines `lines`, the text written to disk."""
    file = folder / PENSIONS_TRELLIS
    text = file.read_text(encoding="utf-8")
    qualified = PENSIONS_CONNECTOR.replace("a_s: a_bq", "a_s: bequest_pa.a_bq").replace(
        "h_s: h_bq", "h_s: bequest_pa.h_bq")
    existing = qualified if qualified in text else PENSIONS_CONNECTOR
    assert text.count(existing) == 1
    file.write_text(text.replace(existing, lines), encoding="utf-8")
    return str(file.resolve()), file.read_text(encoding="utf-8")


def test_l_a_second_drag_between_two_stages_adds_its_key_to_their_mapping(tmp_path):
    """Further field connections extend the existing mapping between the same stages. Authored keyed form remains keyed; an ambiguous compact endpoint receives its stage prefix."""
    folder_path = pensions_copy(tmp_path / "one" / "durables")
    path, text = pensions_connectors(folder_path, "      - {a_s: a_bq}\n")
    folder = model.open_folder(folder_path)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    event = connected_event(shown, folder, (0, "shocks", "adc_s"), (0, "bequest_pa", "adc_bq"))
    drag = trellis.connector_edit(shown, event, {})
    typed = text.replace("      - {a_s: a_bq}\n", "      - {a_s: a_bq, adc_s: adc_bq}\n")
    assert without_drafts(drag) == trellis.Gesture(
        {path: typed},
        {path: text},
        (),
        "trellis.pensions.yml, periods[0].connectors[0]: {adc_s: adc_bq} written, flat, periods 0",
        None,
        path,
        "periods[0].connectors[0]",
    )
    assert entry_value(typed, "periods[0].connectors") == [{"a_s": "a_bq", "adc_s": "adc_bq"}]
    pairs = [
        {
            "sourceHandle": field_port(shown, "writing", (0, "shocks", field))["id"],
            "targetHandle": field_port(shown, "reading", (0, "bequest_pa", arrival))["id"],
        }
        for field, arrival in (("h_s", "h_bq"), ("m_s", "m_bq"))
    ]
    frames = trellis.connector_edit(shown, {"reading": event["reading"], "pairs": pairs}, {})
    assert frames.edits == {
        path: text.replace("      - {a_s: a_bq}\n", "      - {a_s: a_bq, h_s: h_bq, m_s: m_bq}\n")
    }
    assert frames.note.startswith(
        "trellis.pensions.yml, periods[0].connectors[0]: {h_s: h_bq, m_s: m_bq} written, flat, "
        "periods 0"
    )

    # the keyed form where both bequests arrive at a name
    folder_path = pensions_with_bequest_dur(tmp_path / "two" / "durables")
    keyed = "      - {from: shocks, to: bequest_dur, fields: {a_s: a_bq}}\n"
    path, text = pensions_connectors(folder_path, keyed)
    folder = model.open_folder(folder_path)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    event = connected_event(shown, folder, (0, "shocks", "h_s"), (0, "bequest_dur", "h_bq"))
    drag = trellis.connector_edit(shown, event, {})
    assert drag.edits == {path: text.replace("{a_s: a_bq}}", "{a_s: a_bq, h_s: h_bq}}")}
    assert drag.note.startswith(
        "trellis.pensions.yml, periods[0].connectors[0].fields: {h_s: h_bq} written, keyed, "
        "periods 0"
    )
    path, text = pensions_connectors(
        pensions_with_bequest_dur(tmp_path / "three" / "durables"), "      - {adc_s: adc_bq}\n"
    )
    folder = model.open_folder(Path(path).parents[1])
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    event = connected_event(shown, folder, (0, "shocks", "a_s"), (0, "bequest_pa", "a_bq"))
    drag = trellis.connector_edit(shown, event, {})
    assert drag.edits == {
        path: text.replace("{adc_s: adc_bq}", "{adc_s: adc_bq, a_s: bequest_pa.a_bq}")
    }


def test_l_a_moved_end_ticks_its_own_names_and_offers_the_writer_s_other_fields(tmp_path):
    """A qualified connector selects the intended bequest among repeated local field names. Moving selected fields preserves the others, offers compatible additional fields, and refuses forged or duplicate endpoint records."""
    folder_path = pensions_with_bequest_dur(tmp_path / "durables")
    qualified = PENSIONS_CONNECTOR.replace("a_s: a_bq", "a_s: bequest_pa.a_bq").replace(
        "h_s: h_bq", "h_s: bequest_pa.h_bq")
    folder = model.open_folder(folder_path)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    file = folder_path / PENSIONS_TRELLIS
    path, text = str(file.resolve()), file.read_text(encoding="utf-8")
    writer, reader = "periods[0]/shocks", "periods[0]/bequest_pa"
    wire = {(w["from"], w["to"]): w for w in trellis.join_wires(shown)}[writer, reader]
    dur = "periods[0]/bequest_dur"
    ports = {
        field: field_port(shown, "reading", (0, "bequest_dur", field))["id"]
        for field in ("a_bq", "h_bq", "z_bq")
    }
    assert [(f["field"], f["readers"]) for f in wire["fields"]] == [
        ("a_s", {dur: ports["a_bq"]}),
        ("adc_s", {}),
        ("h_s", {dur: ports["h_bq"]}),
        ("m_s", {}),
        ("P_s", {}),
    ]
    assert [(o["field"], o["readers"]) for o in wire["others"]] == [
        (field, {}) for field in SHOCKS_OTHERS
    ]
    beta = field_port(shown, "writing", (0, "shocks", "β_s"))["id"]
    assert {o["field"]: o["writing"] for o in wire["others"]}["β_s"] == beta

    moves = [
        ((0, "shocks", field), (0, "bequest_dur", arrival), (0, "bequest_pa", arrival))
        for field, arrival in (("a_s", "a_bq"), ("h_s", "h_bq"))
    ]
    event = moved_event(shown, folder, writer, reader, "reading", moves)
    other = {"sourceHandle": beta, "targetHandle": ports["z_bq"]}
    moved = trellis.removal_edit(shown, {**event, "pairs": event["pairs"] + [other]}, {})
    keyed = "{a_s: bequest_dur.a_bq, h_s: bequest_dur.h_bq, β_s: z_bq}"
    assert without_drafts(moved) == trellis.Gesture(
        {
            path: text.replace(
                qualified,
                f"      - {{adc_s: adc_bq, m_s: m_bq, P_s: P_bq}}\n      - {keyed}\n",
            )
        },
        {path: text},
        (),
        f"trellis.pensions.yml, periods[0].connectors: {keyed} written, periods 0; "
        "no longer selected: shocks.a_s → bequest_pa.a_bq in periods 0, "
        "shocks.h_s → bequest_pa.h_bq in periods 0; now selected: "
        "shocks.a_s → bequest_dur.a_bq in periods 0, "
        "shocks.h_s → bequest_dur.h_bq in periods 0, shocks.β_s → bequest_dur.z_bq in periods 0",
        None,
        path,
        "periods[0].connectors",
    )
    alone = trellis.removal_edit(shown, {**event, "pairs": [other]}, {})
    assert alone == trellis.connector_edit(
        shown, {"reading": event["reading"], "pairs": [other]}, {}
    )
    # The additional pair has its own target stage and its own source entry.
    assert alone.edits == {
        path: text.replace(qualified, qualified + "      - {β_s: z_bq}\n")
    }
    old = old_graph_gesture(file)
    a_s = field_port(shown, "writing", (0, "shocks", "a_s"))["id"]
    for wrong in (
        {**event, "pairs": [{"sourceHandle": a_s, "targetHandle": ports["z_bq"]}]},
        {**event, "pairs": [other, other]},
        {**event, "end": "writing", "pairs": [other]},
    ):
        assert trellis.removal_edit(shown, wrong, {}) == old, wrong["pairs"]
    assert file.read_text(encoding="utf-8") == text


def test_l_a_standing_mapping_joins_a_period_whose_stages_carry_its_fields(tmp_path):
    """The historical pension draft lacks a declared backward derivative correspondence at the inter-period interface, so adding a period must not preserve its standing mapping as certified. Complete, absent and incompatible interfaces are checked on the composition fixture below."""
    folder_path = pensions_copy(tmp_path / "durables", PENSIONS_WORKING_YEARS)
    folder = model.open_folder(folder_path)
    shown = trellis.show_trellis(folder, recipe.Source("recipe", PENSIONS_RECIPE)).shown
    year = ["shocks", "survival", "tenure_pa", "renter_cons", "keeper_cons_pa", "adjuster_cons_pa"]
    assert any(d.rule == "route-not-established" and d.address == "inter_connectors[0]"
               for d in shown.selection.diagnostics)
    assert trellis.standing_mapping_joins(shown, 1, year, {}) is False
    assert trellis.standing_mapping_joins(shown, 1, ["renter_cons", "shocks"], {}) is False
    assert trellis.standing_mapping_joins(None, 1, year, {}) is False
    for at in (0, 7, True):
        assert trellis.standing_mapping_joins(shown, at, year, {}) is False
    assert trellis.standing_mapping_joins(shown, 1, ["shocks", "buyer"], {}) is False


# The portfolio model's files that `remove stage` of `port` edits, relative
# to the folder, and the texts each holds after it (unit L, Task 25): the
# recipe without port's row; period.yml without its key and with its
# connector {m_next: m} emptied; trellis.yml with its inter-period mapping
# {a: k} emptied, since no other stage takes those fields.
PORT_REMOVED = {
    RECIPE_FILE: (
        "  port: {stage: stages/port/port.bl, calibration: {all: [calibration/portfolio]}, "
        "settings: {all: [settings/port]}, methods: {all: [stages/port/methods]}}\n",
        "",
    ),
    "declaration/period.yml": (
        "  - port\n  - cons\n  - disc\nconnectors:\n  - {m_next: m}\n",
        "  - cons\n  - disc\nconnectors:\n  - {}\n",
    ),
    "declaration/trellis.yml": ("  - {disc.a: k}\n", "  - {}\n"),
}
PORT_REMOVED_NOTE = (
    "spec.yml, stages: port removed; period.yml, stages: port removed, periods 0–5; "
    "period.yml, connectors[0]: {m_next: m} removed, periods 0–5; "
    "trellis.yml, inter_connectors[0]: disc.a: k removed, periods 0–5; "
    "deleted on save: stages/port/, settings/port.yml"
)


def test_l_25_a_stage_removed_takes_its_row_keys_and_joins_in_one_change(tmp_path):
    """Unit L, Task 25 (AAS, L-D18; J-D33 and J-D39), by direct call. On the
    portfolio model, `remove stage` of `port` answers one text of each of
    the recipe, period.yml and trellis.yml: the row, the key, and the
    connector and inter-period mapping that join port and that no other
    stage takes, the lists left `- {}`; the note names each file and
    address and last the folder and the file deleted on save, which the
    gesture's `deleted` lists; the gesture names the recipe at `stages`.
    Nothing is written to disk, and the trellis read from those texts is
    constructed with no `port`. An event of another reading, and a reading
    whose inputs changed, answer "An old graph"."""
    copy = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, RECIPE).shown
    texts = {name: (copy / name).read_text(encoding="utf-8") for name in PORT_REMOVED}
    made = {name: texts[name].replace(*PORT_REMOVED[name]) for name in PORT_REMOVED}
    assert all(made[name] != texts[name] for name in made)
    paths = {name: str((copy / name).resolve()) for name in PORT_REMOVED}
    event = {"reading": trellis.reading_record(folder, shown), "stage": "port"}
    assert trellis.stage_removal_edit(shown, event, {}) == trellis.Gesture(
        {paths[name]: made[name] for name in made},
        {paths[name]: texts[name] for name in texts},
        (),
        PORT_REMOVED_NOTE,
        None,
        paths[RECIPE_FILE],
        "stages",
        None,
        ("declaration/stages/port", "declaration/settings/port.yml"),
    )
    assert {name: (copy / name).read_text(encoding="utf-8") for name in texts} == texts
    outcome = trellis.show_trellis(folder, RECIPE, previous=shown, unsaved=unsaved_of(copy, made))
    assert outcome.refusal is None
    assert all("port" not in period["stages"] for period in outcome.shown.trellis["periods"])

    sentence = (
        "trellis.yml: nothing was written. The graph was drawn from an earlier text. "
        "Remove the stage again in the graph now drawn."
    )
    stale = {**event, "reading": {**event["reading"], "number": shown.number + 1}}
    changed = {paths[RECIPE_FILE]: made[RECIPE_FILE]}
    for gesture in (
        trellis.stage_removal_edit(shown, stale, {}),
        trellis.stage_removal_edit(shown, event, changed),
    ):
        assert (gesture.edits, gesture.sentence) == (None, sentence)


def test_l_25_a_period_removed_lowers_its_entry_s_repeat_and_names_the_restriction(tmp_path):
    """Unit L, Task 25 (AAS, L-D18), by direct call: on the portfolio model,
    `remove period` of periods[2] answers trellis.yml with its entry's
    repeat lowered from 6 to 5, the note naming it and the restriction
    emptied, nothing deleted, the gesture naming the trellis file at
    `periods`; an index that is no period answers "An old graph"."""
    copy = repository_copy(PORTFOLIO_CHOICE, tmp_path / "portfolio-choice")
    folder = model.open_folder(copy)
    shown = trellis.show_trellis(folder, RECIPE).shown
    file = copy / "declaration/trellis.yml"
    path, text = str(file.resolve()), file.read_text(encoding="utf-8")
    event = {"reading": trellis.reading_record(folder, shown), "period": 2}
    assert trellis.period_removal_edit(shown, event, {}) == trellis.Gesture(
        {path: text.replace("repeat: 6}", "repeat: 5}")},
        {path: text},
        (),
        "trellis.yml, periods[0].repeat: 6 now 5; restriction emptied",
        None,
        path,
        "periods",
        "",
        (),
    )
    gesture = trellis.period_removal_edit(shown, {**event, "period": 6}, {})
    assert gesture.sentence == (
        "trellis.yml: nothing was written. The graph was drawn from an earlier text. "
        "Remove the period again in the graph now drawn."
    )


# --- unit L, Task 31: the backward trellis carries the values and the
# marginal values (AAS, L-D26; design pass 7 §3, measure 5) ---

# the layout script, whose `build` gives each wire the label it prints
FLOW_LAYOUT = ROOT / "packages/bellman-workbench/js/flow/src/flow-layout.js"
# The Node module: runs the layout script, builds the trellis graph read on
# standard input with its periods and stage occurrences open, so that every
# occurrence is drawn compact, as the page opens a trellis graph, and prints
# for each wire its two boxes, the label it prints and whether it is the
# bundle of an ordered pair of stage occurrences within a period.
WIRE_LABELS_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
context.self = context;
vm.runInNewContext(readFileSync(%(script)s, "utf8"), context);
const L = context.BellmanFlowLayout;
const m = L.model(JSON.parse(readFileSync(0, "utf8")));
const open = new Set(Object.keys(m.layers).filter((ns) => ns.split("/").length < 3));
const built = L.build(m, open, {}, (text) => Array.from(text || "").length * 7);
console.log(JSON.stringify(built.wires.map((w) => (
  { source: w.source, target: w.target, label: w.join, bundle: !!w.pairBundle }))));
"""


def wire_labels(node: str, graph: dict) -> list[dict]:
    """The wires of the trellis graph `graph` as the layout script draws
    them at the page's opening, each with its two boxes, the label it
    prints and whether it is a pair's bundle (WIRE_LABELS_SCRIPT)."""
    script = WIRE_LABELS_SCRIPT % {"script": json.dumps(str(FLOW_LAYOUT))}
    return node_output(node, script, graph)


def test_l_31_the_backward_trellis_labels_its_wires_with_the_values_and_no_state_field(
    durables_folder, node
):
    """Unit L, Task 31 (AAS, L-D26; design pass 7 §3, measure 5): on the
    durables model under `periods 0–2`, as the page opens it, the layout
    script labels the bundle from `bequest` to `keeper_cons` in periods[0]
    with the value and the two marginal values `keeper_cons` reads at its
    continuation, `𝑉, 𝑑𝑉_h, 𝑑𝑉_a`, the package's names of those functions
    in mathematical italic, in the order the graph lists the wires that
    reach `keeper_cons`. Every label of the backward graph is a list of
    such names, each the name of a function a join carries and none a state
    field a join names, and every such function is named. The forward
    graph's labels are unchanged, the joins' fields of unit K's decision
    K-D4."""
    folder = model.open_folder(durables_folder)
    shown = trellis.show_trellis(folder, RECIPE, trellis.parse_restriction("periods 0–2")).shown
    backward = graph_named(shown.collection, "backward")
    drawn = wire_labels(node, backward)
    labels = {(w["source"], w["target"]): w for w in drawn}
    bequest, keeper = (f"periods[0]/{key}{LAYER_ID_ENDING}" for key in ("bequest", "keeper_cons"))
    assert labels[bequest, keeper]["bundle"]
    # a cable's label is the count of its wires where its route has no branch
    # (design pass 10 §6; unit N, Task 7); the functions' names stand in
    # its hover, in Details, and no longer on the canvas
    assert labels[bequest, keeper]["label"] == "3 wires"
    states = joined_states(backward)
    assert not any(name in states for w in drawn if w["label"] for name in w["label"].split(", "))
    assert function_name("V") in carried_functions(backward)
    forward = graph_named(shown.collection, "forward")
    assert {w["label"] for w in wire_labels(node, forward) if w["label"]} == {
        "3 wires",
        "1 wire",
        "adjust",
        "keep",
    }


def test_comp_each_join_wire_reads_the_pairs_its_edge_s_route_record_names(consport_folder):
    """Unit N, Task 6 (design pass 10 §6): the pairs of a join wire are
    those the record of the route that the wire's edge carries names, each
    the selection's native pair with its two uses, in the selection's
    order. In the trellis of lesson 05, each forward edge of a join carries
    the record of a route of the selection, the pairs read for the edge
    are that route's, and the join wires answered to the canvas name them;
    with the records taken off the edges, no pair and no join wire is
    read, so that none is derived again from the selection's routes."""
    folder = model.open_folder(consport_folder)
    shown = trellis.show_trellis(folder, LESSON).shown
    carried = trellis._pairs_by_wire(shown)
    routes = {
        (f"periods[{r.source[0]}]/{r.source[1]}/{r.law}", r.destination): r
        for r in shown.selection.routes
        if r.law is not None
    }
    assert carried and set(carried) == set(routes)
    for key, pairs in carried.items():
        assert pairs == tuple(p for p in shown.selection.pairs if p in routes[key].pairs), key
    wires = [w for w in trellis.join_wires(shown) if w["writing"]["key"] is not None]
    assert wires
    assert {(w["sourceHandle"], (w["reading"]["h"], w["reading"]["key"])) for w in wires} <= set(
        carried
    )
    stripped = json.loads(json.dumps(shown.collection, ensure_ascii=False))
    for graph in stripped["graphs"]:
        for node in graph["nodes"]:
            for edge in node.get("incomingEdges") or []:
                edge.pop("attrs", None)
    bare = dataclasses.replace(shown, collection=stripped)
    assert trellis._pairs_by_wire(bare) == {} and trellis.join_wires(bare) == []


@pytest.mark.parametrize("end, target, expected", [
    ("reading", (2, "U", "z"), ("S", "a", "U", "z")),
    ("writing", (2, "U", "c"), ("U", "c", "T", "a")),
])
def test_comp_an_inferred_end_moves_through_one_shared_source_and_reopens(
    tmp_path, end, target, expected, monkeypatch,
):
    folder = model.open_folder(composition_folder(tmp_path / "composition", repeat=3))
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    assert shown is not None
    wire = next(w for w in trellis.join_wires(shown) if w["from"] == "periods[2]/S")
    assert wire["movable"] == ["writing", "reading"] and not wire["removable"]
    event = join_event(shown, folder, "periods[2]/S", "periods[2]/T", end, target)
    original = tuple(stage for period in shown.trellis["periods"] for stage in period["stages"].values())
    move = trellis.removal_edit(shown, event, {})
    assert move.sentence is None, move.sentence
    assert set(move.edits) == {str(folder.root / "period.yml")}
    assert "periods 0–2" in move.note
    proposed = trellis._with_connectors(shown, move.edits, around=0)
    assert all(stage is held for stage, held in zip(
        (s for p in proposed["periods"] for s in p["stages"].values()), original,
    ))
    reopened = trellis.show_trellis(folder, source, previous=shown, unsaved={
        path: trellis.Unsaved(text, 1) for path, text in move.edits.items()
    }).shown
    assert reopened is not None
    assert [(p.writing.key, p.writing.field, p.reading.key, p.reading.field)
            for p in reopened.selection.pairs] == [expected] * 3
    assert all(p.origin == "authored" for p in reopened.selection.pairs)
    undone = trellis.show_trellis(folder, source, previous=reopened).shown
    assert all(p.origin == "inferred" for p in undone.selection.pairs)
    assert len(undone.selection.pairs) == 3
    assert all(Path(path).read_text(encoding="utf-8") == text for path, text in move.read.items())
    monkeypatch.setattr(trellis, "trellis_selection", lambda *_: pytest.fail("restriction selected again"))
    restricted = trellis.show_trellis(folder, source, trellis.parse_restriction("periods 0"), previous=undone).shown
    assert restricted.selection is undone.selection


def test_comp_noop_and_stale_moves_write_nothing_and_incompatible_move_uses_package_reason(tmp_path):
    folder = model.open_folder(composition_folder(tmp_path / "composition", alternative_domain="ℝ₊₊"))
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    event = join_event(shown, folder, "periods[0]/S", "periods[0]/T")
    event.update(end="reading", handle=field_port(shown, "reading", (0, "T", "a"))["id"])
    assert trellis.removal_edit(shown, event, {}) == trellis.Gesture(None, None, (), None, None, None, None)
    event["handle"] = field_port(shown, "reading", (0, "U", "z"))["id"]
    refused = trellis.removal_edit(shown, event, {})
    assert refused.edits is None and "does not lie in" in refused.sentence
    period = folder.root / "period.yml"
    proposed = trellis.show_trellis(folder, source, unsaved={
        str(period): trellis.Unsaved(period.read_text(encoding="utf-8").replace(
            "[{}]", "[{a: z}]",
        ), 1),
    }).shown
    diagnostic = next(d for d in proposed.selection.diagnostics if d.rule == "pair-incompatible")
    assert refused.sentence == diagnostic.message
    stale = trellis.removal_edit(shown, event, {str(folder.root / "period.yml"): "stages: {}\n"})
    assert stale.edits is None and "earlier text" in stale.sentence


@pytest.mark.parametrize("connector", ["{S.a: T.a}", "{from: S, to: T, fields: {a: a}}"])
def test_comp_qualified_and_keyed_source_entries_move_by_their_written_key(tmp_path, connector):
    path = composition_folder(tmp_path / "composition")
    period = path / "period.yml"
    period.write_text(period.read_text(encoding="utf-8").replace("[{}]", f"[{connector}]"), encoding="utf-8")
    folder = model.open_folder(path)
    shown = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
    event = join_event(shown, folder, "periods[0]/S", "periods[0]/T", "reading", (0, "U", "z"))
    moved = trellis.removal_edit(shown, event, {})
    assert moved.sentence is None, moved.sentence
    proposed = trellis.trellis_selection(trellis._with_connectors(shown, moved.edits))
    assert [(p.writing.key, p.writing.field, p.reading.key, p.reading.field) for p in proposed.pairs] == [
        ("S", "a", "U", "z"),
    ]


@pytest.mark.parametrize("authored", [False, True])
def test_comp_crossed_pairs_are_checked_as_one_complete_proposal(tmp_path, authored):
    path = composition_folder(tmp_path / "composition", two_fields=True)
    if authored:
        period = path / "period.yml"
        period.write_text(period.read_text(encoding="utf-8").replace(
            "[{}]", "[{S.a: T.b, S.b: T.a}]",
        ), encoding="utf-8")
    folder = model.open_folder(path)
    shown = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
    wire = next(w for w in trellis.join_wires(shown) if w["from"] == "periods[0]/S")
    event = join_event(shown, folder, "periods[0]/S", "periods[0]/T")
    event.update(end="reading", pairs=[{
        "sourceHandle": row["writing"], "replaced": row["reading"],
        "targetHandle": field_port(shown, "reading", (0, "T", row["field"] if authored else
                                                       "b" if row["field"] == "a" else "a"))["id"],
    } for row in wire["fields"]])
    move = trellis.removal_edit(shown, event, {})
    assert move.sentence is None, move.sentence
    proposed = trellis.trellis_selection(trellis._with_connectors(shown, move.edits))
    expected = {("a", "a"), ("b", "b")} if authored else {("a", "b"), ("b", "a")}
    assert {(p.writing.field, p.reading.field) for p in proposed.pairs} == expected
    assert proposed.routes[0].status == "certified"


def test_comp_shared_source_is_checked_against_every_periods_effective_values(tmp_path):
    path = composition_folder(tmp_path / "composition", repeat=3)
    stage = path / "U.bl"
    stage.write_text(stage.read_text(encoding="utf-8").replace(
        "@stage: relay", "@stage: relay\na_min : ℝ",
    ).replace("ℝ₊", "[a_min, inf)"), encoding="utf-8")
    period = (path / "period.yml").read_text(encoding="utf-8")
    (path / "period.yml").write_text(period.replace("stage: U.bl", "stage: U.bl, calibration: {a_min: 0}"), encoding="utf-8")
    trellis_file = path / "trellis.yml"
    trellis_file.write_text(
        "!trellis\nperiods:\n  - {template: period.yml, repeat: 2}\n"
        "  - template: period.yml\n    stages:\n      S: {stage: S.bl}\n      T: {stage: T.bl}\n"
        "      U: {stage: U.bl, calibration: {a_min: 1}}\n",
        encoding="utf-8",
    )
    folder = model.open_folder(path)
    shown = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
    event = join_event(shown, folder, "periods[0]/S", "periods[0]/T", "reading", (0, "U", "z"))
    move = trellis.removal_edit(shown, event, {})
    assert move.edits is None and "periods[2].U.z" in move.sentence
    assert "does not lie in" in move.sentence

    absent = composition_folder(tmp_path / "absent", repeat=3)
    (absent / "trellis.yml").write_text(
        "!trellis\nperiods:\n  - {template: period.yml}\n"
        "  - template: period.yml\n    repeat: 2\n"
        "    stages: {S: {stage: S.bl}, T: {stage: T.bl}}\n"
        "inter_connectors: [{a: x}]\n", encoding="utf-8")
    folder = model.open_folder(absent)
    shown = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
    event = join_event(shown, folder, "periods[1]/S", "periods[0]/S", "reading", (0, "U", "z"))
    move = trellis.removal_edit(shown, event, {})
    assert move.edits is None and "every period reached" in move.sentence
    assert "Write separate period mappings" in move.sentence


def test_comp_a_move_reports_another_inferred_arrow_displaced_by_its_new_endpoint(tmp_path):
    path = composition_folder(tmp_path / "composition")
    (path / "V.bl").write_text(COMPOSITION_STAGE.replace("INPUT", "z").replace("OUTPUT", "v").replace("DOMAIN", "ℝ₊"), encoding="utf-8")
    period = path / "period.yml"
    period.write_text(period.read_text(encoding="utf-8").replace(
        "  U: {stage: U.bl}", "  U: {stage: U.bl}\n  V: {stage: V.bl}",
    ), encoding="utf-8")
    (path / "U.bl").write_text(COMPOSITION_STAGE.replace("INPUT", "k").replace("OUTPUT", "z").replace("DOMAIN", "ℝ₊"), encoding="utf-8")
    folder = model.open_folder(path)
    shown = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
    assert shown is not None
    event = join_event(shown, folder, "periods[0]/S", "periods[0]/T")
    event.update(end="reading", handle=field_port(shown, "reading", (0, "V", "z"))["id"])
    move = trellis.removal_edit(shown, event, {})
    assert move.sentence is None, move.sentence
    assert "no longer selected" in move.note and "U.z → V.z" in move.note
    assert "now selected: S.a → V.z" in move.note


@pytest.mark.parametrize("connector", ["{}", "{S.a: U.z}"])
def test_comp_added_stage_keeps_unconnected_fields_and_reports_qualified_authored_pairs(tmp_path, connector):
    path = composition_folder(tmp_path / "composition")
    (path / "trellis.yml").write_text(
        "!trellis\nperiods:\n  - stages:\n      S: {stage: S.bl}\n      T: {stage: T.bl}\n"
        f"    connectors: [{connector}]\n  - stages:\n      U: {{stage: U.bl}}\n"
        "    connectors: []\ninter_connectors: []\n", encoding="utf-8",
    )
    folder = model.open_folder(path)
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    event = {"reading": trellis.reading_record(folder, shown),
             "target": "periods[0]___group___", "item": "U", "kind": "stage"}
    added = trellis.drop_edits(shown, event, {})
    assert added.edits is not None, added.sentence
    reopened = trellis.show_trellis(folder, source, previous=shown, unsaved={
        p: trellis.Unsaved(text, 1) for p, text in added.edits.items()
    }).shown
    assert "U" in reopened.trellis["periods"][0]["stages"]
    expected = "T" if connector == "{}" else "U"
    assert [(p.writing.key, p.reading.key) for p in reopened.selection.pairs] == [("S", expected)]
    assert ("S.a: U.z now join U" in added.note) == (connector != "{}")
    # a stage the package joins to nothing is named unconnected (unit N,
    # Task 5; design pass 10 §7)
    assert added.note.endswith("; U unconnected") == (connector == "{}")


def test_comp_a_standing_mapping_must_resolve_at_both_inserted_interfaces(tmp_path):
    path = composition_folder(tmp_path / "composition", repeat=2)
    file = path / "trellis.yml"
    file.write_text(file.read_text(encoding="utf-8").replace(
        "inter_connectors: []", "inter_connectors: [{a: x}]",
    ), encoding="utf-8")
    shown = trellis.show_trellis(model.open_folder(path), recipe.Source("trellis", "trellis.yml")).shown
    assert not shown.selection.diagnostics
    assert trellis.standing_mapping_joins(shown, 1, ["S"], {})
    assert not trellis.standing_mapping_joins(shown, 1, ["U"], {})
    # The current interface is compatible, but copying the first S makes
    # its broad output meet its own strict-positive arrival.
    first = COMPOSITION_STAGE.replace("INPUT", "x").replace("OUTPUT", "a").replace("DOMAIN", "ℝ₊₊")
    second = COMPOSITION_STAGE.replace("INPUT", "x").replace("OUTPUT", "a").replace("DOMAIN", "ℝ₊")
    (path / "S.bl").write_text(first.replace("(a : ℝ₊₊)", "(a : ℝ₊)"), encoding="utf-8")
    (path / "second.bl").write_text(second.replace("(a : ℝ₊)", "(a : ℝ₊₊)"), encoding="utf-8")
    file.write_text(
        "!trellis\nperiods:\n  - stages: {S: {stage: S.bl}}\n  - stages: {S: {stage: second.bl}}\n"
        "inter_connectors: [{a: x}]\n", encoding="utf-8",
    )
    shown = trellis.show_trellis(model.open_folder(path), recipe.Source("trellis", "trellis.yml")).shown
    assert not shown.selection.diagnostics
    assert not trellis.standing_mapping_joins(shown, 1, ["S"], {})



def test_comp_refused_calibration_cannot_authorize_a_move_and_a_later_valid_value_can(tmp_path):
    path = composition_folder(tmp_path / "composition")
    stage = path / "U.bl"
    stage.write_text(stage.read_text(encoding="utf-8").replace(
        "@stage: relay", "@stage: relay\na_min : ℝ₊",
    ).replace("ℝ₊) : !arvl", "[a_min, inf)) : !arvl"), encoding="utf-8")
    period = path / "period.yml"
    period.write_text(period.read_text(encoding="utf-8").replace(
        "stage: U.bl", "stage: U.bl, calibration: {a_min: 0}",
    ), encoding="utf-8")
    folder = model.open_folder(path)
    source = recipe.Source("trellis", "trellis.yml")
    good = trellis.show_trellis(folder, source).shown
    assert good is not None and not good.binding.failed
    event = join_event(good, folder, "periods[0]/S", "periods[0]/T", "reading", (0, "U", "z"))
    assert trellis.removal_edit(good, event, {}).edits is not None
    invalid = {str(period): period.read_text(encoding="utf-8").replace("a_min: 0", "a_min: -1")}
    refused = trellis.show_trellis(folder, source, previous=good, unsaved={
        p: trellis.Unsaved(t, 1) for p, t in invalid.items()
    }).shown
    assert "calibrate" in refused.binding.failed
    event = join_event(refused, folder, "periods[0]/S", "periods[0]/T", "reading", (0, "U", "z"))
    move = trellis.removal_edit(refused, event, invalid)
    assert move.edits is None and "a_min" in move.sentence and "no finite value" in move.sentence
    assert refused.selection.bindings[0, "U"] is None
    symbolic = join_event(refused, folder, "periods[0]/S", "periods[0]/T", "writing", (0, "U", "c"))
    independent = trellis.removal_edit(refused, symbolic, invalid)
    assert independent.edits is not None and independent.sentence is None
    assert "calibrate" in refused.binding.failed
    restored = trellis.show_trellis(folder, source, previous=refused).shown
    assert not restored.binding.failed
    event = join_event(restored, folder, "periods[0]/S", "periods[0]/T", "reading", (0, "U", "z"))
    assert trellis.removal_edit(restored, event, {}).edits is not None


@pytest.mark.parametrize("connector, between, free_spelling", [
    ("{S.a: T.b, S.b: missing}", False, False),
    ("{from: S, to: T, fields: {a: b, b: missing}}", False, False),
    ("{S.a: T.b, S.b: missing}", True, False),
    ("{S.a: T.b, S.b: missing}", False, True),
])
def test_comp_an_unresolved_authored_source_is_not_overwritten(tmp_path, connector, between, free_spelling):
    path = composition_folder(tmp_path / "composition", repeat=2 if between else 1, two_fields=True)
    # Both writers use b, so only the already-authored qualified key can name S.b.
    if not free_spelling:
        alternative = path / "U.bl"
        alternative.write_text(alternative.read_text(encoding="utf-8").replace(
            "f : ℝ₊", "b : ℝ₊").replace("f = e", "b = e"), encoding="utf-8")
    file = path / ("trellis.yml" if between else "period.yml")
    text = file.read_text(encoding="utf-8")
    old = "inter_connectors: []" if between else "connectors: [{}]"
    new = f"inter_connectors: [{connector}]" if between else f"connectors: [{connector}]"
    text = text.replace(old, new)
    file.write_text(text, encoding="utf-8")
    folder = model.open_folder(path)
    shown = trellis.show_trellis(folder, recipe.Source("trellis", "trellis.yml")).shown
    assert any(d.rule == "endpoint-unresolved" for d in shown.selection.diagnostics)
    event = connected_event(shown, folder, (1 if between else 0, "S", "b"), (0, "T", "a"))
    result = trellis.connector_edit(shown, event, {})
    if free_spelling:
        assert result.edits is not None and result.sentence is None
        entry = "inter_connectors[0]" if between else "connectors[0]"
        assert entry_value(result.edits[str(file)], entry) == {"S.a": "T.b", "S.b": "missing", "b": "a"}
        reopened = trellis.show_trellis(folder, shown.source, previous=shown, unsaved={
            name: trellis.Unsaved(source, 1) for name, source in result.edits.items()
        }).shown
        assert any(d.rule == "endpoint-unresolved" for d in reopened.selection.diagnostics)
    else:
        assert result.edits is None and "already has an entry with a source name needed" in result.sentence
        assert "Edit or remove that entry first" in result.sentence
    assert file.read_text(encoding="utf-8") == text


@pytest.mark.parametrize("branch, fields, other", [
    ("up", ("x_up", "y_up"), ("x_dn", "y_dn")),
    ("down", ("x_dn", "y_dn"), ("x_up", "y_up")),
])
@pytest.mark.parametrize("end", [None, "reading", "writing"])
def test_comp_each_branch_arrow_edits_only_the_pairs_its_law_carries(tmp_path, branch, fields, other, end):
    path = composition_folder(tmp_path / "branches", branching=True)
    period = path / "period.yml"
    before = period.read_text(encoding="utf-8")
    folder = model.open_folder(path)
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    assert shown.selection.diagnostics == ()
    assert len(shown.selection.routes) == 2
    assert all(route.status == "certified" for route in shown.selection.routes)
    (route,) = [route for route in shown.selection.routes if route.branch == branch]
    wires = trellis.join_wires(shown)
    assert len(wires) == 2
    (wire,) = [wire for wire in wires if wire["sourceHandle"] == f"periods[0]/S/{route.law}"]
    assert [row["field"] for row in wire["fields"]] == list(fields)
    assert wire["join"] == "; ".join(f"{field} → {arrival}" for field, arrival in zip(fields, ("x", "y")))
    details = dict(trellis.join_rows(folder, shown, wire).rows)
    assert [row.cells[0] for row in details["fields"]] == [f"{field} → {arrival}" for field, arrival in zip(fields, ("x", "y"))]
    event = {
        "reading": trellis.reading_record(folder, shown),
        "join": {key: wire[key] for key in ("source", "sourceHandle", "target", "targetHandle")},
    }
    if end is not None:
        event.update(end=end, pairs=[{
            "sourceHandle": row["writing"] if end == "reading" else field_port(shown, "writing", (0, "U", row["field"]))["id"],
            "targetHandle": row["reading"] if end == "writing" else field_port(shown, "reading", (0, "U", row["arrival"]))["id"],
            "replaced": row[end],
        } for row in wire["fields"]])
    edited = trellis.removal_edit(shown, event, {})
    assert edited.sentence is None, edited.sentence
    assert set(edited.edits) == {str(period)}
    written = entry_value(edited.edits[str(period)], "connectors")
    assert {f"S.{field}": f"T.{arrival}" for field, arrival in zip(other, ("x", "y"))}.items() <= written[0].items()
    reopened = trellis.show_trellis(folder, source, previous=shown, unsaved={
        name: trellis.Unsaved(text, 1) for name, text in edited.edits.items()
    }).shown
    assert reopened.selection.diagnostics == ()
    expected = {("S", field, "T", arrival) for field, arrival in zip(other, ("x", "y"))}
    if end is not None:
        expected |= {("S" if end == "reading" else "U", field, "U" if end == "reading" else "T", arrival)
                     for field, arrival in zip(fields, ("x", "y"))}
    assert {(pair.writing.key, pair.writing.field, pair.reading.key, pair.reading.field)
            for pair in reopened.selection.pairs} == expected
    assert all(route.status == "certified" for route in reopened.selection.routes)
    assert period.read_text(encoding="utf-8") == before


# --- unit N, Task 7: the cable and the whole-cable gesture (design pass 10 §§6–8) ---


def _durables_shown(folder_path):
    """The durables model read under its recipe at periods 0 to 2, and its
    folder."""
    folder = model.open_folder(folder_path)
    source = recipe.Source("recipe", RECIPE_FILE)
    shown = trellis.show_trellis(folder, source, trellis.parse_restriction("periods 0–2")).shown
    assert shown is not None
    return folder, source, shown


def _tenure_keep(shown, h: int) -> dict:
    """The join wire of the inferred cable from `tenure`'s branch `keep` to
    `keeper_cons` in periods[h]."""
    (wire,) = [
        w for w in trellis.join_wires(shown)
        if (w["from"], w["to"]) == (f"periods[{h}]/tenure", f"periods[{h}]/keeper_cons")
    ]
    return wire


def test_n_7_a_cable_s_move_writes_one_entry_for_every_pair_and_releases_the_inferred_pairs(
    tmp_path,
):
    """Unit N, Task 7 (design pass 10 §7; AMD-COMP-001 §§3.2–3.3). In the
    composition model with two fields, the cable from `S` to `T` is
    inferred, its two wires `a` and `b`. The move of its reading end to `U`,
    the whole cable, every arrival field of `U` paired, `a → z` and `b → w`,
    writes one compact entry for every pair of the route in one file, and
    the next reading selects the two authored pairs and none of the inferred
    pairs the move replaced; the old pairs do not return, since the authored
    endpoints reserve the continuation fields, and the new route is
    certified."""
    folder = model.open_folder(composition_folder(tmp_path / "composition", two_fields=True))
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    assert shown is not None
    (wire,) = [w for w in trellis.join_wires(shown) if (w["from"], w["to"]) == ("periods[0]/S", "periods[0]/T")]
    assert (wire["branch"], wire["status"]) == (None, "certified")
    assert [f["field"] for f in wire["fields"]] == ["a", "b"] and not wire["removable"]
    arrivals = {name: field_port(shown, "reading", (0, "U", name))["id"] for name in ("z", "w")}
    event = {
        "reading": trellis.reading_record(folder, shown),
        "join": {name: wire[name] for name in ("source", "sourceHandle", "target", "targetHandle")},
        "end": "reading",
        "cable": True,
        "pairs": [
            {"sourceHandle": f["writing"], "targetHandle": arrivals[name], "replaced": f["reading"]}
            for f, name in zip(wire["fields"], ("z", "w"))
        ],
    }
    move = trellis.removal_edit(shown, event, {})
    assert move.sentence is None, move.sentence
    assert set(move.edits) == {str(folder.root / "period.yml")}
    assert move.note.startswith("period.yml, connectors[0]: {a: z, b: w} written, periods 0"), move.note
    assert "no longer selected: S.a → T.a in periods 0, S.b → T.b in periods 0" in move.note, move.note
    reopened = trellis.show_trellis(folder, source, previous=shown, unsaved={
        path: trellis.Unsaved(text, 1) for path, text in move.edits.items()
    }).shown
    assert reopened is not None
    assert {(p.writing.key, p.writing.field, p.reading.key, p.reading.field, p.origin)
            for p in reopened.selection.pairs} == {("S", "a", "U", "z", "authored"), ("S", "b", "U", "w", "authored")}
    assert all(route.status == "certified" for route in reopened.selection.routes)
    # the move chosen as the canvas sends it, through the join wire record
    # the next reading answers: the cable now runs from S to U and none to T
    assert {(w["from"], w["to"]) for w in trellis.join_wires(reopened)} == {("periods[0]/S", "periods[0]/U")}


def test_n_7_a_drag_from_a_joined_continuation_port_is_the_move_of_its_cable(tmp_path):
    """Unit N, Task 7 (design pass 10 §7). In the composition model with two
    fields, the event `connected` of a drag from `S`'s joined writing port to
    `U`'s arrival port, the two pairs its list ticks, `a → z` and `b → w`,
    is answered as the move of the whole inferred cable from `S` to `T`: the
    gesture types the one entry as the move does, where before it wrote
    nothing and answered that the port is joined, and the next reading
    selects no pair from `S` into `T`. A drag of the one field `a` alone,
    which leaves `b` to the package, is refused, since the package would pair
    `b` with `T` again and the branch would stand on two destinations
    (AMD-COMP-001 §3.2)."""
    folder = model.open_folder(composition_folder(tmp_path / "composition", two_fields=True))
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    assert shown is not None
    (wire,) = [w for w in trellis.join_wires(shown) if (w["from"], w["to"]) == ("periods[0]/S", "periods[0]/T")]
    arrivals = {name: field_port(shown, "reading", (0, "U", name))["id"] for name in ("z", "w")}
    event = {
        "reading": trellis.reading_record(folder, shown),
        "source": wire["source"],
        "target": f"periods[0]/U{LAYER_ID_ENDING}",
        "cable": True,
        "pairs": [
            {"sourceHandle": f["writing"], "targetHandle": arrivals[name]}
            for f, name in zip(wire["fields"], ("z", "w"))
        ],
    }
    gesture = trellis.connector_edit(shown, event, {})
    assert gesture.sentence is None, gesture.sentence
    assert gesture.edits is not None and set(gesture.edits) == {str(folder.root / "period.yml")}
    assert gesture.note.startswith("period.yml, connectors[0]: {a: z, b: w} written, periods 0"), gesture.note
    assert "no longer selected: S.a → T.a in periods 0, S.b → T.b in periods 0" in gesture.note, gesture.note
    reopened = trellis.show_trellis(folder, source, previous=shown, unsaved={
        path: trellis.Unsaved(text, 1) for path, text in gesture.edits.items()
    }).shown
    assert {(p.writing.key, p.reading.key) for p in reopened.selection.pairs} == {("S", "U")}
    alone = connected_event(shown, folder, (0, "S", "a"), (0, "U", "z"))
    refused = trellis.connector_edit(shown, alone, {})
    assert refused.edits is None and refused.sentence == (
        "Nothing was written. The proposed source still selects S.b → T.b, "
        "so the branch would stand on two destinations."
    ), refused.sentence


def test_n_7_a_list_with_a_field_unpaired_writes_the_ticked_pairs_and_names_the_draft(scratch_durables):
    """Unit N, Task 7 (design pass 10 §7; AMD-COMP-001 §3.2). The cable of
    `tenure`'s branch `adjust` moved to `keeper_cons` in periods[1], its two
    fields paired with the keeper's decision states, the fields of its entry
    perch, `w_adj → w_d` and `z_adj → z_d`, and `keeper_cons`'s `h_d` left
    unpaired, writes the ticked pairs as one entry, releases every pair of
    the route, and the gesture's report names the draft the package then
    reports, the incomplete route, in the package's sentence; nothing is
    certified. The cable of the branch `keep` moved to `tenure` in
    periods[0] with `z_kp` left unpaired is written: the period's connector
    authors the branch's three pairs, so the move takes them out with the
    cable and no pair of `z_kp` is selected again (decision MB-U31; the
    refusal of a move the package would pair again stands in
    `test_n_7_a_drag_from_a_joined_continuation_port_is_the_move_of_its_cable`)."""
    folder, source, shown = _durables_shown(scratch_durables)
    (adjust,) = [
        w for w in trellis.join_wires(shown)
        if (w["from"], w["to"]) == ("periods[1]/tenure", "periods[1]/adjuster_cons")
    ]
    assert (adjust["branch"], adjust["status"]) == ("adjust", "certified")
    assert [f["field"] for f in adjust["fields"]] == ["w_adj", "z_adj"]
    arrivals = {name: field_port(shown, "reading", (1, "keeper_cons", name))["id"] for name in ("w_d", "z_d")}
    event = {
        "reading": trellis.reading_record(folder, shown),
        "join": {name: adjust[name] for name in ("source", "sourceHandle", "target", "targetHandle")},
        "end": "reading",
        "cable": True,
        "pairs": [
            {"sourceHandle": f["writing"], "targetHandle": arrivals[name], "replaced": f["reading"]}
            for f, name in zip(adjust["fields"], ("w_d", "z_d"))
        ],
    }
    move = trellis.removal_edit(shown, event, {})
    assert move.sentence is None, move.sentence
    assert "{w_adj: w_d, z_adj: keeper_cons.z_d} written" in move.note, move.note
    assert "draft: " in move.note and "route-incomplete" not in move.note, move.note
    reopened = trellis.show_trellis(folder, source, trellis.parse_restriction("periods 0–2"), previous=shown, unsaved={
        path: trellis.Unsaved(text, 1) for path, text in move.edits.items()
    }).shown
    routes = [r for r in reopened.selection.routes if r.source == (1, "tenure") and r.branch == "adjust"]
    assert [r.destination for r in routes] == [(1, "keeper_cons")], routes
    assert all(route.status != "certified" for route in routes), routes
    assert any(d.rule == "route-incomplete" for d in reopened.selection.diagnostics)
    # the branch `keep` with `z_kp` unpaired: written, the authored pairs of
    # the branch taken out with the cable
    keep = _tenure_keep(shown, 1)
    arrivals = {name: field_port(shown, "reading", (0, "tenure", name))["id"] for name in ("a", "h")}
    event = {
        "reading": trellis.reading_record(folder, shown),
        "join": {name: keep[name] for name in ("source", "sourceHandle", "target", "targetHandle")},
        "end": "reading",
        "cable": True,
        "pairs": [
            {"sourceHandle": f["writing"], "targetHandle": arrivals[name], "replaced": f["reading"]}
            for f, name in zip(keep["fields"][:2], ("a", "h"))
        ],
    }
    moved = trellis.removal_edit(shown, event, {})
    assert moved.sentence is None and moved.edits is not None, moved.sentence
    assert moved.note.startswith("trellis.yml, inter_connectors[0]: w_kp: a, h_kp: h written, periods 0–50"), moved.note
    assert (
        "no longer selected: tenure.h_kp → keeper_cons.h_d in periods 1–50, tenure.w_kp → keeper_cons.w_d "
        "in periods 1–50, tenure.z_kp → keeper_cons.z_d in periods 1–50"
    ) in moved.note, moved.note


def test_n_7_a_cable_dropped_on_its_own_destination_is_no_split_and_a_writing_end_names_the_sources(
    tmp_path,
):
    """Unit N, Task 7 (design pass 10 §7; AMD-COMP-001 §3.2; the re-review
    of 12 October 2026, New 1). In the composition model with two fields,
    the whole inferred cable from `S` to `T` dropped on `T` itself with its
    pairing changed, `a → b` and `b → a`, is no split: the pairs of the
    route stand on the one destination the moved end now stands on, so the
    write is admitted, one entry naming both pairs, and the next reading
    selects the two authored pairs on `T`. The writing end of that cable
    moved to `U`'s branch with `T`'s `b` left unpaired is refused, since the
    package would select `S.b → T.b` again and `T`'s arrival tuple would
    read two sources; the sentence names that outcome and not a branch."""
    folder = model.open_folder(composition_folder(tmp_path / "composition", two_fields=True))
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    assert shown is not None
    (wire,) = [w for w in trellis.join_wires(shown) if (w["from"], w["to"]) == ("periods[0]/S", "periods[0]/T")]
    by_field = {f["field"]: f for f in wire["fields"]}
    arrivals = {name: field_port(shown, "reading", (0, "T", name))["id"] for name in ("a", "b")}
    join = {name: wire[name] for name in ("source", "sourceHandle", "target", "targetHandle")}
    swapped = {
        "reading": trellis.reading_record(folder, shown),
        "join": join,
        "end": "reading",
        "cable": True,
        "pairs": [
            {"sourceHandle": by_field["a"]["writing"], "targetHandle": arrivals["b"], "replaced": by_field["a"]["reading"]},
            {"sourceHandle": by_field["b"]["writing"], "targetHandle": arrivals["a"], "replaced": by_field["b"]["reading"]},
        ],
    }
    move = trellis.removal_edit(shown, swapped, {})
    assert move.sentence is None, move.sentence
    assert move.edits is not None and set(move.edits) == {str(folder.root / "period.yml")}
    assert move.note.startswith("period.yml, connectors[0]: {a: b, b: a} written, periods 0"), move.note
    reopened = trellis.show_trellis(folder, source, previous=shown, unsaved={
        path: trellis.Unsaved(text, 1) for path, text in move.edits.items()
    }).shown
    assert reopened is not None
    assert {(p.writing.key, p.writing.field, p.reading.key, p.reading.field, p.origin)
            for p in reopened.selection.pairs} == {("S", "a", "T", "b", "authored"), ("S", "b", "T", "a", "authored")}
    assert {(w["from"], w["to"]) for w in trellis.join_wires(reopened)} == {("periods[0]/S", "periods[0]/T")}
    # the writing end moved to U with T's b left unpaired
    c = field_port(shown, "writing", (0, "U", "c"))["id"]
    writing_end = {
        "reading": trellis.reading_record(folder, shown),
        "join": join,
        "end": "writing",
        "cable": True,
        "pairs": [{"sourceHandle": c, "targetHandle": arrivals["a"], "replaced": by_field["a"]["writing"]}],
    }
    refused = trellis.removal_edit(shown, writing_end, {})
    assert refused.edits is None and refused.sentence == (
        "Nothing was written. The proposed source still selects S.b → T.b, "
        "so the arrival tuple would read two sources."
    ), refused.sentence


def test_n_7_the_pre_fill_is_the_package_s_one_candidate_and_not_an_equal_name(tmp_path):
    """Unit N, Task 7 (design pass 10 §7; AMD-COMP-001 §§3.2–3.3). In the
    composition model `S.a → T.a` is the package's one candidate for `T`'s
    arrival field `a`, and `S`'s writing record names `T` under `equal`; it
    names no occurrence of the next period, since the package infers no pair
    between periods. Where `U` writes a field `a` as well, the two sources
    dispute `T.a`, the package selects neither, and neither record names
    `T`: the pre-fill is the package's candidate, not an equal name."""
    path = composition_folder(tmp_path / "composition", repeat=2)
    folder = model.open_folder(path)
    source = recipe.Source("trellis", "trellis.yml")
    shown = trellis.show_trellis(folder, source).shown
    assert shown is not None
    records = {(r["h"], r["key"], r["field"]): r for r in trellis.connectable_ports(shown) if r["side"] == "writing"}
    reading = field_port(shown, "reading", (1, "T", "a"))["id"]
    assert records[(1, "S", "a")]["equal"] == {"periods[1]/T": reading}
    (path / "U.bl").write_text(
        (path / "U.bl").read_text(encoding="utf-8").replace("(c : ℝ₊) : !cntn", "(a : ℝ₊) : !cntn").replace("c = d", "a = d"),
        encoding="utf-8",
    )
    disputed = trellis.show_trellis(model.open_folder(path), source).shown
    assert disputed is not None
    assert any(r.rule == "inference-disputed" for r in disputed.selection.rejected)
    records = {(r["h"], r["key"], r["field"]): r for r in trellis.connectable_ports(disputed) if r["side"] == "writing"}
    assert records[(1, "S", "a")]["equal"] == {} and records[(1, "U", "a")]["equal"] == {}


def test_n_7_a_cable_of_the_backward_graph_reveals_its_route_in_details(scratch_durables):
    """Unit N, Task 7 (design pass 10 §8; the brief, § Wires, cables and
    connections). `join_wires` with the backward graph answers one record
    per cable of that graph, the route's source and destination as `from`
    and `to`, no movable end and nothing removable; `join_rows` of the
    record from `tenure`'s branch `keep` to `keeper_cons` in periods[1]
    begins with the route, its status and its three wires in the route's
    order, as the forward cable's Details does, and offers no rename and
    no removal."""
    folder, source, shown = _durables_shown(scratch_durables)
    wires = trellis.join_wires(shown, graph="backward")
    assert wires and all(w["movable"] == [] and not w["removable"] and w["graph"] == "backward" for w in wires)
    # one record per function wire of the route, each selecting the same route
    keep = [w for w in wires if (w["from"], w["to"], w["branch"]) == ("periods[1]/tenure", "periods[1]/keeper_cons", "keep")]
    assert len(keep) > 1 and all(w["status"] == "certified" for w in keep), keep
    assert len({(w["source"], w["sourceHandle"], w["target"], w["targetHandle"]) for w in keep}) == len(keep)
    wire = keep[0]
    assert wire["source"].startswith("periods[1]/keeper_cons") and wire["target"].startswith("periods[1]/tenure")
    rows = trellis.join_rows(folder, shown, wire)
    assert rows.place == "periods[1]/tenure → periods[1]/keeper_cons" and rows.names == () and not rows.removable
    keys = [key for key, _ in rows.rows]
    assert keys[:3] == ["route", "status", "wires"], keys
    found = dict(rows.rows)
    assert found["route"][0].head == "branch keep"
    assert found["status"][0].parts == ("certified",)
    assert [line.head for line in found["wires"]] == ["w_kp → w_d", "h_kp → h_d", "z_kp → z_d"]
    forward = {(w["from"], w["to"]): w for w in trellis.join_wires(shown)}[("periods[1]/tenure", "periods[1]/keeper_cons")]
    assert dict(trellis.join_rows(folder, shown, forward).rows)["wires"] == found["wires"]


def test_describe_node_lists_a_field_a_block_and_a_perch_of_the_trellis_s_initial_diagram(durables_folder):
    """Design pass 14 §7, rule 6 (S-D21). In the trellis's initial diagram of
    the durables model at periods 0 to 2, a field box, a block and a perch
    layer of `periods[0]/bequest` are the pieces of that occurrence's own
    stage view, under the occurrence: the field `bequest:cntn:V` with its
    rows, the block `cntn_to_dcsn` as its own block, and the perch layer
    `cntn` as a layer; the occurrence's and the period's layers answer as
    the builders graph's do; and with nothing selected the panel prints
    `No selection`, which the page gates on the graph shown."""
    folder = model.open_folder(durables_folder)
    shown = trellis.with_initial_diagrams(
        trellis.show_trellis(
            folder, recipe.Source("recipe", RECIPE_FILE), trellis.parse_restriction("periods 0–2")
        ).shown
    )
    views = {}
    graph = "backward initial diagram"
    field = trellis.describe_node(shown, graph, "periods[0]/bequest/bequest:cntn:V", views)
    assert (field.kind, field.occurrence, field.position) == ("piece", "periods[0]/bequest", (0, "bequest"))
    assert (field.piece.kind, field.piece.node_id, field.piece.block) == ("field", "bequest:cntn:V", "")
    assert field.piece.attributes["kind"] == "field" and field.piece.attributes["perch"] == "cntn"
    block = trellis.describe_node(shown, graph, "periods[0]/bequest/cntn_to_dcsn", views)
    assert (block.kind, block.occurrence) == ("piece", "periods[0]/bequest")
    assert (block.piece.kind, block.piece.node_id, block.piece.block) == ("block", "cntn_to_dcsn", "cntn_to_dcsn")
    perch = trellis.describe_node(shown, graph, "periods[0]/bequest/cntn" + LAYER_ID_ENDING, views)
    assert (perch.kind, perch.occurrence, perch.piece.kind) == ("piece", "periods[0]/bequest", "layer")
    occurrence = trellis.describe_node(shown, graph, "periods[0]/bequest" + LAYER_ID_ENDING, views)
    assert (occurrence.kind, occurrence.position) == ("occurrence", (0, "bequest"))
    period = trellis.describe_node(shown, graph, "periods[0]" + LAYER_ID_ENDING, views)
    assert period.kind == "period" and [a for a, _ in period.occurrences] == [
        "periods[0]/tenure",
        "periods[0]/adjuster_cons",
        "periods[0]/keeper_cons",
        "periods[0]/bequest",
    ]
    assert set(views) == {"periods[0]/bequest"}
