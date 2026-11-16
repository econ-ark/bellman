"""Unit G3 of specification 0.6: a saved copy of a job's returned files,
opened as a model of its own and read-only, adopted into the model folder
with its record and recovery area, and imported as a variant (`returned.py`;
amendment 06 §2 items 21 to 24). Each copy is written by unit G2's download
through the stand-in of the client, `tests/matsya_stub.py`; no test reaches
the service. One test per acceptance item of the unit's brief,
`test_item_<n>_<claim>`, and one for the adoption of a job prepared from a
named recipe (decision SG3-19).
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat

import pytest
from workbench_support import (
    applications_copy,
    clear_gesture_state,
    client_path,
    git,
    returned_job,
)

from bellman.trellis import entry_value
from bellman_workbench import matsya_client, matsya_work, model, recipe, returned, trellis

CALIBRATION = "declaration/calibration/durables.yml"
SETTINGS = "declaration/settings/durables.yml"
HIGH, LOW, LOWER = "τ: 0.12", "τ: 0.08", "τ: 0.05"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def every_file(folder) -> dict:
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(folder).parts
    }


def session_of(folder) -> matsya_work.Session:
    return matsya_work.Session(sha256(folder.root.name)[:32], matsya_client.service_identity())


def submitted(folder, path: str = "declaration/spec.yml") -> int:
    """The number of a job of the recipe at `path` that unit G2's adapter
    prepared and submitted, so that the folder holds its prepared record."""
    prepared = matsya_work.prepare(folder, recipe.Source("recipe", path), "recipe",
                                   session_of(folder), 1)
    work = matsya_work.submit(folder, prepared.path, session_of(folder))
    return int(work.record["accepted"].removeprefix("job-"))


def downloaded(folder, number: int, cycles: int, edits=None, removed=(), files=None) -> str:
    """The saved copy of a job of the folder's session that ended with the
    folder's declaration, or `files`, changed by `edits`, as unit G2's
    download writes it."""
    session = session_of(folder)
    job = returned_job(folder.root, session.id, number, cycles, edits, removed, files)
    copy = matsya_work.download(folder, session, job["id"])
    assert copy.written, copy.refusal
    return copy.path


def test_item_1_a_returned_model_opens_under_its_own_root_and_no_discovery_lists_its_files(
    tmp_path, scratch_durables, app_state
):
    """cons-port, whose declaration/ holds two recipes, opens on them: a
    saved copy of its declaration under bellman-matsya-output/ adds no
    source, and a
    folder of stage files alone opens on its own stage, not the copy's. A
    durables copy whose calibration lowers τ to 0.08 opens under its own
    root: its recipe, its files and the τ its calibration binds are its own,
    and the service's comparison stands apart; a copy without its
    calibration file reports a missing dependency, and one whose stage does
    not parse a construction error, each apart from that comparison."""
    consport = model.open_folder(applications_copy(tmp_path / "corpus"))
    before = recipe.model_sources(consport)
    assert before and all(source.kind == "recipe" for source in before)
    copied = downloaded(consport, 1, 1)
    assert (consport.root / copied / "declaration/trellis.port-cons.yml").is_file()
    assert recipe.model_sources(consport) == before

    stages = tmp_path / "stages"
    (stages / "declaration/stages/cons").mkdir(parents=True)
    (stages / "declaration/stages/cons/cons.bl").write_text("", encoding="utf-8")
    saved = stages / model.OUTPUT_FOLDER / "job-1-iteration-1-revision-1-configuration-none"
    (saved / "declaration/stages/aaa").mkdir(parents=True)
    (saved / "declaration/stages/aaa/aaa.bl").write_text("", encoding="utf-8")
    app = app_state(stages)
    assert app.first_stage(app.tree.value) == "declaration/stages/cons/cons.bl"

    folder = model.open_folder(scratch_durables)
    copy = downloaded(folder, 3, 2, {CALIBRATION: (HIGH, LOW)})
    inspected = returned.inspect(folder, copy)
    assert inspected.folder.root == folder.root / copy
    assert inspected.source == recipe.Source("recipe", "declaration/spec.yml")
    assert all(path.startswith(str(folder.root / copy) + os.sep) for path in inspected.shown.files)
    adjuster = inspected.shown.syntactic["periods"][1]["stages"]["adjuster_cons"]
    assert adjuster["calibration"]["τ"] == 0.08
    assert inspected.service["result"]["comparison"] == {"converged": True, "differences": []}
    own = trellis.show_trellis(folder, recipe.Source("recipe", "declaration/spec.yml"))
    assert own.shown.syntactic["periods"][1]["stages"]["adjuster_cons"]["calibration"]["τ"] == 0.12
    # the copy holds every file its model reads, and its binding meets no
    # note, as the folder's own meets none: the declaration values the income
    # functions Y and y_R of tenure in calibration/wage_schedule.yml
    notes = trellis.binding_notes(own.shown.binding)
    own_notes = tuple(trellis.relative_sentence(folder, note) for note in notes)
    assert own_notes == ()
    assert inspected.missing == () and inspected.construction == ()

    lacking = returned.inspect(folder, downloaded(folder, 4, 1, removed=(CALIBRATION,)))
    assert lacking.construction == () and len(lacking.missing) == 1
    assert "calibration/durables" in lacking.missing[0]
    assert lacking.service["result"]["comparison"] == inspected.service["result"]["comparison"]
    keeper = "declaration/stages/keeper_cons/keeper_cons.bl"
    unparsed = returned.inspect(folder, downloaded(folder, 5, 1, {keeper: ("@stage", "@@stage")}))
    assert unparsed.missing == () and len(unparsed.construction) == 1
    assert unparsed.service["result"]["comparison"] == inspected.service["result"]["comparison"]


def test_item_2_a_save_or_an_edit_gesture_on_a_returned_model_is_refused_with_the_reason(
    scratch_durables, app_state
):
    """The copy opened from the model folder as the tab's model folder, on
    its own recipe: Mod-s on an edited buffer writes nothing and the list
    under the error mark gives the reason, with no choice to overwrite; a
    drop on the trellis graph begins no gesture and gives the reason; the
    guarded save itself refuses a file of the copy; and neither a view's
    export nor a paper draft is written into it."""
    folder = model.open_folder(scratch_durables)
    copy = downloaded(folder, 3, 2, {CALIBRATION: (HIGH, LOW)})
    root = folder.root / copy
    on_disk = (root / CALIBRATION).read_bytes()
    reason = (
        f"{CALIBRATION} lies in a saved copy of a job's returned files under "
        "bellman-matsya-output/, which is read-only; adopt its files to change the model"
    )
    app = app_state(folder.root)
    try:
        app.open_returned(copy)
        assert app.tab_folder.value.root == root
        assert app.open_path.value == "declaration/spec.yml"
        spec = app.buffers.value["declaration/spec.yml"]
        app.open_file(CALIBRATION)
        app.on_change({"path": "declaration/spec.yml", "text": spec["text"],
                       "revision": spec["document_revision"]})
        held = app.buffers.value[CALIBRATION]
        event = {"path": CALIBRATION, "text": held["text"].replace(LOW, "τ: 0.01"),
                 "revision": held["document_revision"]}
        app.on_change(event)
        app.on_save(event)
        assert (root / CALIBRATION).read_bytes() == on_disk
        assert app.conflict.value is None
        assert app.gesture_refusal.value["sentence"] == reason
        app.on_dropped({"item": {"key": "bequest"}, "kind": "stage", "target": {}, "reading": 1})
        assert app.gesturing.value is None
        whole = (
            f"{root.name} is a saved copy of a job's returned files, which is read-only; adopt "
            "its files to change the model"
        )
        assert app.gesture_refusal.value["sentence"] == whole
        app.submit_new_variant("lower")
        assert app.form_error.value == whole
        assert not (root / "declaration/spec.lower.yml").exists()
    finally:
        clear_gesture_state()
    copied = model.open_folder(root)
    saved = model.save_file(copied, CALIBRATION, "τ: 0.01\n", sha256(on_disk.decode("utf-8")))
    assert (saved.saved, saved.reason) == (False, reason)
    assert (root / CALIBRATION).read_bytes() == on_disk
    bequest = "declaration/stages/bequest/bequest.bl"
    text = (root / bequest).read_text(encoding="utf-8")
    stage = model.elaborate_buffer(text, str(root / bequest)).stage
    writes = (
        lambda: model.export_view(copied, stage, text, bequest, unsaved=False, occurrence=None,
                                  direction="backward", source_digests={}),
        lambda: model.write_paper(copied, stage, bequest, text, {}),
    )
    for write in writes:
        with pytest.raises(PermissionError, match="is a saved copy of a job's returned files"):
            write()
    assert not (root / model.EXPORT_FOLDER).exists() and not (root / model.PAPER_FOLDER).exists()


def test_item_3_an_adoption_shows_versions_destinations_and_differences_and_refuses_unsaved_text(
    matsya_durables,
):
    """The plan of the copy's calibration names the copy's version, its
    destination and the line differences, and retains each dependency the
    copy reads that stands identical in the folder. A buffer of the
    destination with unsaved text is shown and refused, at the plan and
    again immediately before writing, with nothing written. A selection that
    omits a dependency that differs is refused until the dependency is
    explicitly retained."""
    folder = model.open_folder(matsya_durables)
    changed = {CALIBRATION: (HIGH, LOW), SETTINGS: ("n_a:", "n_a: 301 #")}
    copy = downloaded(folder, submitted(folder), 2, changed)
    source = (folder.root / copy / CALIBRATION).read_text(encoding="utf-8")
    disk = (folder.root / CALIBRATION).read_text(encoding="utf-8")
    planned = returned.plan(folder, copy, [CALIBRATION], retained=[SETTINGS])
    assert planned.refusals == ()
    [entry] = planned.files
    assert (entry["source"], entry["destination"]) == (f"{copy}/{CALIBRATION}", CALIBRATION)
    assert (entry["source_sha256"], entry["before_sha256"]) == (sha256(source), sha256(disk))
    assert f"-  {HIGH}" in entry["difference"] and f"+  {LOW}" in entry["difference"]
    assert entry["unsaved"] is None
    retained = {item["destination"]: item["identical"] for item in planned.retained}
    assert retained[SETTINGS] is False and retained["declaration/spec.yml"] is True
    assert "declaration/stages/tenure/tenure.bl" in retained

    omitted = returned.plan(folder, copy, [CALIBRATION])
    assert omitted.refusals == (
        f"the selection omits {copy}/{SETTINGS}, which the copy's model reads, and {SETTINGS} "
        f"differs from it; select it or retain {SETTINGS}",
    )

    before = every_file(folder.root)
    buffers = {CALIBRATION: matsya_work.Buffer(disk + "# typed, not saved\n", sha256(disk))}
    shown = returned.plan(folder, copy, [CALIBRATION], buffers=buffers, retained=[SETTINGS])
    assert "+# typed, not saved" in shown.files[0]["unsaved"]
    unsaved = (
        f"{CALIBRATION} holds unsaved changes in the editor; save or discard them before the "
        "adoption"
    )
    assert shown.refusals == (unsaved,)
    adoption = returned.adopt(folder, planned, buffers=buffers)
    assert (adoption.id, adoption.changed, adoption.refusals) == (None, (), (unsaved,))
    assert every_file(folder.root) == before


def test_item_4_a_late_write_failure_is_recorded_and_the_originals_are_restored(
    matsya_durables,
):
    """A destination without write permission is refused before any file
    changes. A plan of two files whose second write fails, deliberately,
    with the error of a full disk: the adoption stops, its record names the
    file changed and the one that failed, the original of the first stands
    in the adoption's recovery area, and the restore writes it back and is
    recorded. The same failure followed by a hand edit of the file written
    leaves that edit, and the restore is recorded as failed. The same
    failure once more, then the completion of the reviewed plan, writes
    both files."""
    folder = model.open_folder(matsya_durables)
    number = submitted(folder)
    changed = {CALIBRATION: (HIGH, LOW), SETTINGS: ("n_a:", "n_a: 301 #")}
    copy = downloaded(folder, number, 2, changed)
    planned = returned.plan(folder, copy, [CALIBRATION, SETTINGS])
    assert planned.refusals == ()
    originals = {path: (folder.root / path).read_bytes() for path in (CALIBRATION, SETTINGS)}
    mode = stat.S_IMODE((folder.root / SETTINGS).stat().st_mode)
    (folder.root / SETTINGS).chmod(stat.S_IRUSR)
    try:
        refused = returned.adopt(folder, planned)
    finally:
        (folder.root / SETTINGS).chmod(mode)
    assert (refused.id, refused.changed) == (None, ())
    assert refused.refusals == (f"{SETTINGS} cannot be written: no write permission",)
    assert not (folder.root / returned.ADOPTIONS_FOLDER).exists()

    def full_disk(at, relpath, text, expected):
        if relpath == SETTINGS:
            raise OSError(errno.ENOSPC, "No space left on device", relpath)
        return model.save_file(at, relpath, text, expected)

    stopped = returned.adopt(folder, planned, write=full_disk)
    assert stopped.changed == (CALIBRATION,)
    assert stopped.refusals == (
        f"the adoption stopped at {SETTINGS}: [Errno 28] No space left on device: "
        f"'{SETTINGS}'; {CALIBRATION} changed; restore the originals or complete the reviewed "
        "plan",
    )
    area = folder.root / returned.ADOPTIONS_FOLDER / stopped.id
    record = json.loads((area / "record.json").read_text(encoding="utf-8"))
    assert record == stopped.record
    assert (record["copy"], record["job"], record["iteration"]) == (copy, f"job-{number}", 2)
    assert record["state"] == "stopped"
    first, second = record["files"]
    assert (first["outcome"], second["outcome"]) == ("written", "failed")
    assert first["after_sha256"] == sha256((folder.root / CALIBRATION).read_text("utf-8"))
    assert second["sentence"].startswith("[Errno 28]")
    assert (area / first["recovery"]).read_bytes() == originals[CALIBRATION]
    assert (folder.root / SETTINGS).read_bytes() == originals[SETTINGS]

    restored = returned.restore(folder, stopped.id)
    assert (restored.changed, restored.refusals) == ((CALIBRATION,), ())
    assert {path: (folder.root / path).read_bytes() for path in originals} == originals
    record = json.loads((area / "record.json").read_text(encoding="utf-8"))
    assert record["state"] == "restored"
    assert [entry["restored"] for entry in record["files"]] == ["restored", None]

    edited = returned.adopt(folder, planned, write=full_disk)
    (folder.root / CALIBRATION).write_text("τ: 0.3\n", encoding="utf-8")
    failed = returned.restore(folder, edited.id)
    assert failed.refusals == (f"{CALIBRATION} was not restored: the file changed on disk",)
    assert (failed.record["state"], failed.record["files"][0]["restored"]) == (
        "restore failed", "failed"
    )
    assert (folder.root / CALIBRATION).read_text(encoding="utf-8") == "τ: 0.3\n"
    (folder.root / CALIBRATION).write_bytes(originals[CALIBRATION])

    again = returned.adopt(folder, planned, write=full_disk)
    completed = returned.complete(folder, again.id)
    assert (completed.changed, completed.refusals) == ((SETTINGS,), ())
    assert completed.record["state"] == "adopted"
    for path in (CALIBRATION, SETTINGS):
        assert (folder.root / path).read_bytes() == (folder.root / copy / path).read_bytes()


def test_item_5_a_newer_job_finishing_during_the_review_does_not_replace_the_reviewed_files(
    matsya_durables, app_state
):
    """The review of iteration 2 of job 3; iteration 3 ends and is
    downloaded beside it while the review stands; the adoption writes
    iteration 2's text and its record names that copy. The commit offered
    after the recorded result opens the commit form with the adopted file
    alone, and nothing is committed. A copy whose file no longer holds the
    reviewed text is refused."""
    folder = model.open_folder(matsya_durables)
    number = submitted(folder)
    reviewed = downloaded(folder, number, 2, {CALIBRATION: (HIGH, LOW)})
    planned = returned.plan(folder, reviewed, [CALIBRATION])
    newer = downloaded(folder, number, 3, {CALIBRATION: (HIGH, LOWER)})
    assert newer != reviewed
    (folder.root / "economics.md").write_text("# an unrelated edit\n", encoding="utf-8")
    head = git(folder.root, "rev-parse", "HEAD")
    adopted = returned.adopt(folder, planned)
    assert (adopted.changed, adopted.refusals) == ((CALIBRATION,), ())
    written = (folder.root / CALIBRATION).read_text(encoding="utf-8")
    assert LOW in written and LOWER not in written
    assert adopted.record["copy"] == reviewed and adopted.record["state"] == "adopted"
    message, paths = returned.commit_offer(folder, adopted.record)
    assert paths == (CALIBRATION,) and reviewed.split("/")[-1] in message
    app = app_state(folder.root)
    app.open_adoption_commit(adopted.record)
    assert (app.form_open.value, app.commit_message.value) == ("commit", message)
    assert app.commit_paths() == [CALIBRATION]
    app.form_open.value = None
    assert git(folder.root, "rev-parse", "HEAD") == head

    stale = returned.plan(folder, newer, [CALIBRATION])
    (folder.root / newer / CALIBRATION).write_text("τ: 0.5\n", encoding="utf-8")
    refused = returned.adopt(folder, stale)
    assert refused.refusals == (
        f"{newer}/{CALIBRATION} no longer holds the reviewed text; review the adoption again",
    )
    assert (folder.root / CALIBRATION).read_text(encoding="utf-8") == written


def test_item_6_the_variant_import_of_the_lower_housing_cost_leaves_the_baseline_byte_identical(
    scratch_durables,
):
    """The 0.12 to 0.08 housing-cost case, the job's note on the tenure
    stage beside it: the import copies the changed calibration under the
    variant's name and no note, shares every other file, rewrites
    the variant recipe's entries that named the baseline's calibration, and
    leaves every file of the baseline byte-identical; the variant constructs
    with τ 0.08 and the baseline with τ 0.12. A copy that changes a stage
    file is refused, with nothing written."""
    folder = model.open_folder(scratch_durables)
    note = "declaration/stages/tenure/tenure.md"
    title = 'title: "The tenure stage (tenure.bl)"'
    copy = downloaded(folder, 3, 2, {CALIBRATION: (HIGH, LOW), note: (title, "title: a note")})
    before = every_file(folder.root)
    imported = returned.import_variant(folder, copy, "low-cost", "spec.yml")
    assert imported.refusals == ()
    variant = "declaration/calibration/durables_low-cost.yml"
    assert imported.copied == (
        {"source": f"{copy}/{CALIBRATION}", "base": CALIBRATION, "written": variant},
    )
    assert "declaration/stages/tenure/tenure.bl" in imported.shared
    assert SETTINGS in imported.shared and CALIBRATION not in imported.shared
    assert {entry["now"] for entry in imported.rewritten} == {"calibration/durables_low-cost"}
    assert len(imported.rewritten) == 4
    assert imported.retained_recipe is False
    after = every_file(folder.root)
    assert all(after[path] == before[path] for path in before)
    assert set(after) - set(before) == set(imported.files) == {
        "declaration/spec.low-cost.yml", "declaration/trellis.low-cost.yml",
        "declaration/period.low-cost.yml", variant,
    }
    assert imported.baseline == {path: sha256(before[path].decode("utf-8"))
                                 for path in imported.baseline}
    shown = trellis.show_trellis(folder, recipe.Source("recipe", "declaration/spec.low-cost.yml"))
    assert shown.refusal is None
    held = shown.shown.syntactic["periods"][1]["stages"]["adjuster_cons"]
    assert held["calibration"]["τ"] == 0.08

    keeper = "declaration/stages/keeper_cons/keeper_cons.bl"
    staged = downloaded(folder, 4, 1, {keeper: ("@stage", "# a returned comment\n@stage")})
    after = every_file(folder.root)
    refused = returned.import_variant(folder, staged, "with-comment", "spec.yml")
    assert refused.files == () and refused.refusals == (
        f"{staged}/{keeper} differs from {keeper}, and a variant import copies changed "
        "calibration, settings and methods files alone; review the copy on its own",
    )
    assert every_file(folder.root) == after


def test_a_job_prepared_from_a_named_recipe_is_adopted_at_that_recipe_s_own_files(
    matsya_durables,
):
    """A job prepared from `declaration/spec.two-stages.yml` returns its
    recipe as `spec.yml` and its trellis file as `trellis.yml`, each changed:
    the plan maps them through the job's prepared record to the recipe's own
    files, the adoption writes `declaration/spec.two-stages.yml` with its
    `trellis:` entry written back to `trellis.two-stages.yml`, and
    `declaration/trellis.two-stages.yml`, and the main recipe and its trellis
    file stand byte-identical. The copy of a job no prepared record of the
    folder names, and a returned file the record does not name, are each
    refused with the reason (decision SG3-19)."""
    folder = model.open_folder(matsya_durables)
    number = submitted(folder, "declaration/spec.two-stages.yml")
    [held] = (folder.root / matsya_work.PREPARED_FOLDER).glob("*.inputs.json")
    sent = json.loads(held.read_text(encoding="utf-8"))["starting_declaration"]
    files = {client_path(name): text for name, text in sent.items()}
    assert entry_value(files["declaration/spec.yml"], "trellis") == "trellis.yml"
    files["declaration/spec.yml"] += "# a line the job added\n"
    files["declaration/trellis.yml"] += "# a line the job added\n"
    files["declaration/calibration/extra.yml"] = "calibration: {}\n"
    copy = downloaded(folder, number, 1, files=files)
    main = {path: (folder.root / path).read_bytes()
            for path in ("declaration/spec.yml", "declaration/trellis.yml")}

    chosen = ["declaration/spec.yml", "declaration/trellis.yml"]
    planned = returned.plan(folder, copy, chosen)
    assert planned.refusals == ()
    assert [(entry["source"], entry["destination"]) for entry in planned.files] == [
        (f"{copy}/declaration/spec.yml", "declaration/spec.two-stages.yml"),
        (f"{copy}/declaration/trellis.yml", "declaration/trellis.two-stages.yml"),
    ]
    assert planned.files[0]["rewritten"] == [
        {"entry": "trellis", "returned": "trellis.yml", "written": "trellis.two-stages.yml"}
    ]
    assert "+# a line the job added" in planned.files[0]["difference"]
    shown_difference = planned.files[0]["difference"]
    assert "trellis.yml" not in shown_difference.replace("trellis.two-stages.yml", "")
    adopted = returned.adopt(folder, planned)
    named = ("declaration/spec.two-stages.yml", "declaration/trellis.two-stages.yml")
    assert adopted.changed == named
    written = (folder.root / "declaration/spec.two-stages.yml").read_text(encoding="utf-8")
    assert entry_value(written, "trellis") == "trellis.two-stages.yml"
    assert written.endswith("# a line the job added\n")
    trellis_text = (folder.root / "declaration/trellis.two-stages.yml").read_text(encoding="utf-8")
    assert trellis_text == files["declaration/trellis.yml"]
    assert {path: (folder.root / path).read_bytes() for path in main} == main
    shown = trellis.show_trellis(folder, recipe.Source("recipe", named[0]))
    assert shown.refusal is None

    unnamed = returned.plan(folder, copy, ["declaration/calibration/extra.yml"])
    assert unnamed.refusals == (
        f"the prepared record of job-{number} names no file sent as calibration/extra.yml, so "
        f"{copy}/declaration/calibration/extra.yml has no original path; review the copy on its "
        "own",
    )
    stranger = downloaded(folder, 9, 1, {CALIBRATION: (HIGH, LOW)})
    before = every_file(folder.root)
    refused = returned.plan(folder, stranger, [CALIBRATION])
    assert refused.refusals == (
        f"no prepared record of job-9 stands in this folder, so the files of {stranger} have no "
        "original paths; review the copy on its own",
    )
    assert returned.adopt(folder, refused).changed == ()
    assert every_file(folder.root) == before


def test_first_adoption_uses_returned_paths_and_serializes_competing_plans(
    tmp_path, scratch_durables,
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    root = tmp_path / "first-model"
    root.mkdir()
    economics = root / "economics.md"
    economics.write_text("The original model description.\n", encoding="utf-8")
    folder = model.open_folder(root)
    sample = model.open_folder(scratch_durables)
    _, dependencies = matsya_work.required_files(
        sample, recipe.Source("recipe", "declaration/spec.yml"), {}
    )
    declaration = {
        path.relative_to(scratch_durables).as_posix(): path.read_text(encoding="utf-8")
        for path in dependencies
    }
    first = downloaded(folder, 1, 1, files=declaration)
    second = downloaded(folder, 2, 1, {CALIBRATION: (HIGH, LOW)}, files=declaration)
    archived = root / first / "declaration"
    spec = archived / "spec.yml"
    original_spec = spec.read_text(encoding="utf-8")
    spec.write_text(
        original_spec.replace("trellis: trellis.yml", f"trellis: {archived / 'trellis.yml'}"),
        encoding="utf-8",
    )
    assert returned.plan(folder, first).refusals
    spec.write_text(original_spec, encoding="utf-8")
    reviewed = returned.plan(folder, first)
    competing = returned.plan(folder, second)
    assert reviewed.refusals == competing.refusals == ()
    assert {entry["destination"] for entry in reviewed.files} == declaration.keys()
    assert all(entry["before_sha256"] is None for entry in reviewed.files)
    assert not (root / "declaration").exists()

    entered, finish = Event(), Event()

    def paused_write(folder, destination, text, digest):
        entered.set()
        assert finish.wait(timeout=5)
        return model.save_file(folder, destination, text, digest)

    with ThreadPoolExecutor(max_workers=2) as workers:
        building = workers.submit(returned.adopt, folder, reviewed, None, paused_write)
        try:
            assert entered.wait(timeout=5)
            blocked = workers.submit(returned.adopt, folder, competing).result(timeout=5)
            assert blocked.refusals and not blocked.changed
        finally:
            finish.set()
        adopted = building.result(timeout=5)

    assert not adopted.refusals and set(adopted.changed) == declaration.keys()
    assert returned.adopt(folder, competing).refusals
    assert (root / CALIBRATION).read_text(encoding="utf-8") == declaration[CALIBRATION]
    assert economics.read_text(encoding="utf-8") == "The original model description.\n"
    assert trellis.show_trellis(folder, recipe.Source("recipe", "declaration/spec.yml")).refusal is None


def test_replacement_previews_new_dependency_and_refuses_late_collision(matsya_durables):
    folder = model.open_folder(matsya_durables)
    number = submitted(folder)
    [held] = (folder.root / matsya_work.PREPARED_FOLDER).glob("*.inputs.json")
    sent = json.loads(held.read_text(encoding="utf-8"))["starting_declaration"]
    files = {client_path(name): text for name, text in sent.items()}
    generated = "declaration/calibration/generated.yml"
    files[generated] = files[CALIBRATION].replace(HIGH, LOW)
    files["declaration/spec.yml"] = files["declaration/spec.yml"].replace(
        "calibration/durables,", "calibration/generated,", 1
    )
    copy = downloaded(folder, number, 1, files=files)
    planned = returned.plan(folder, copy, ["declaration/spec.yml", generated])
    assert planned.refusals == ()
    new = next(entry for entry in planned.files if entry["destination"] == generated)
    assert new["before_sha256"] is None and f"+  {LOW}" in new["difference"]

    local = folder.root / generated
    local.write_text("# local file arrived after review\n", encoding="utf-8")
    refused = returned.adopt(folder, planned)
    assert refused.refusals and not refused.changed
    assert local.read_text(encoding="utf-8") == "# local file arrived after review\n"
    local.unlink()

    outside = folder.root / "outside.yml"
    outside.write_text("# outside the declaration\n", encoding="utf-8")
    local.symlink_to(outside)
    unsafe = returned.plan(folder, copy, ["declaration/spec.yml", generated])
    assert any("symbolic link" in refusal for refusal in unsafe.refusals)
    assert returned.adopt(folder, planned).refusals
    assert outside.read_text(encoding="utf-8") == "# outside the declaration\n"
    local.unlink()

    adopted = returned.adopt(folder, planned)
    assert adopted.refusals == ()
    assert adopted.changed == ("declaration/spec.yml", generated)
    assert local.read_text(encoding="utf-8") == files[generated]
    assert (folder.root / CALIBRATION).read_text(encoding="utf-8") == files[CALIBRATION]
    assert trellis.show_trellis(folder, recipe.Source("recipe", "declaration/spec.yml")).refusal is None
