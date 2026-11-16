"""Unit G2 of specification 0.6: the Workbench's Matsya adapter,
`matsya_work.py`, run against the stand-in of the client,
`tests/matsya_stub.py`, whose service is the JSON file the fixture
`matsya_stub` names; no test reaches the service. One test per acceptance
item of the unit's brief, `test_item_<n>_<claim>`.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re

import pytest
from workbench_support import (
    PORT_CONS_RECORDS,
    applications_copy,
    pensions_two_templates,
    stub_calls,
    stub_job,
)

from bellman_workbench import matsya_client, matsya_work, model, recipe

PENSIONS = recipe.Source("recipe", "declaration/spec.pensions.yml")
DURABLES = recipe.Source("recipe", "declaration/spec.yml")
SHOCKS = "declaration/stages/shocks/shocks.bl"
# The files the named pensions recipe reads, as a reviewer lists them from
# the recipe, its trellis file, the two period templates, the stage files
# and the source lists; each with
# the name under which the service reads it.
PENSIONS_FILES = {
    "declaration/spec.pensions.yml": "spec.yml",
    "declaration/trellis.pensions.yml": "trellis.yml",
    "declaration/period.pensions.yml": "period.pensions.yml",
    "declaration/period.working.yml": "period.working.yml",
    "declaration/calibration/bequest_pa.yml": "calibration/bequest_pa.yml",
    "declaration/calibration/renter_cons.yml": "calibration/renter_cons.yml",
    "declaration/calibration/shocks.yml": "calibration/shocks.yml",
    "declaration/calibration/pension_age_profiles.yml": "calibration/pension_age_profiles.yml",
    **{
        f"declaration/stages/{key}/{key}.bl": f"{key}.bl"
        for key in (
            "shocks", "survival", "plan_choice", "contribution", "allocation", "payout",
            "tenure_pa", "renter_cons", "keeper_cons_pa", "adjuster_cons_pa", "bequest_pa",
        )
    },
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def session_of(folder) -> matsya_work.Session:
    """The selected session, an identifier of 32 hexadecimal characters as
    the service gives one, on the service the client's settings name now."""
    return matsya_work.Session(sha256(folder.name)[:32], matsya_client.service_identity())


def every_file(folder) -> dict:
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(folder).parts
    }


def test_item_1_the_pensions_record_lists_the_reviewed_files_and_each_choice_sends_its_text(
    tmp_path, monkeypatch
):
    """The named recipe `spec.pensions.yml`, whose trellis file names two
    period templates, with an unsaved edit of the shocks stage in the
    editor. Without a choice nothing is prepared and the difference is
    shown. Each of the three choices gives a record whose files and
    fingerprints are the reviewed ones under the service's names, the
    recipe's `trellis:` entry rewritten to `trellis.yml`; the saved version
    sends the disk's text, the displayed text sends the buffer and leaves
    the disk, and save writes the buffer through the guarded save and sends
    it. The submission sends the record's texts, not the file as it later
    stands."""
    folder = model.open_folder(pensions_two_templates(tmp_path / "durables"))
    session = session_of(folder.root)
    disk = (folder.root / SHOCKS).read_text(encoding="utf-8")
    edited = disk + "# an edit not yet saved\n"
    buffers = {SHOCKS: matsya_work.Buffer(edited, sha256(disk))}

    refused = matsya_work.prepare(folder, PENSIONS, "recipe", session, 3, buffers=buffers)
    assert refused.path is None
    assert refused.refusals == (
        f"{SHOCKS} has unsaved changes; save it, send the saved version or send the "
        "displayed text",
    )
    assert "+# an edit not yet saved" in refused.differences[SHOCKS]
    assert not (folder.root / ".bellman-matsya").exists()

    sent = {}
    for choice in (matsya_work.SAVED_VERSION, matsya_work.DISPLAYED_TEXT, matsya_work.SAVE):
        prepared = matsya_work.prepare(
            folder, PENSIONS, "recipe", session, 3, buffers=buffers, choice=choice
        )
        assert prepared.refusals == ()
        record = json.loads((folder.root / prepared.path).read_text(encoding="utf-8"))
        assert record == prepared.record
        assert {entry["path"]: entry["name"] for entry in record["files"]} == PENSIONS_FILES
        inputs_file = (folder.root / record["inputs"]).read_bytes()
        assert record["inputs_sha256"] == hashlib.sha256(inputs_file).hexdigest()
        inputs = json.loads(inputs_file)
        texts = inputs["starting_declaration"]
        assert inputs == {
            "session": session.id,
            "reviewed_through": 3,
            "target": "recipe",
            "starting_declaration": texts,
            "paths": {name: path for path, name in PENSIONS_FILES.items()},
        }
        assert sorted(texts) == sorted(PENSIONS_FILES.values())
        for entry in record["files"]:
            if entry["path"] != SHOCKS:
                assert entry["sha256"] == sha256((folder.root / entry["path"]).read_text("utf-8"))
        recipe_text = (folder.root / PENSIONS.path).read_text(encoding="utf-8")
        assert texts["spec.yml"] == recipe_text.replace(
            "trellis: trellis.pensions.yml", "trellis: trellis.yml"
        )
        assert record["rewritten"] == [
            {"path": PENSIONS.path, "entry": "trellis", "written": "trellis.pensions.yml",
             "sent": "trellis.yml"}
        ]
        shocks = next(entry for entry in record["files"] if entry["path"] == SHOCKS)
        assert shocks["sha256"] == sha256(texts["shocks.bl"])
        sent[choice] = (texts["shocks.bl"], (folder.root / SHOCKS).read_text(encoding="utf-8"))
    assert sent[matsya_work.SAVED_VERSION] == (disk, disk)
    assert sent[matsya_work.DISPLAYED_TEXT] == (edited, disk)
    assert sent[matsya_work.SAVE] == (edited, edited)

    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    (folder.root / SHOCKS).write_text("# the file changed after the review\n", encoding="utf-8")
    matsya_work.submit(folder, prepared.path, session)
    (received,) = [entry["submitted"] for entry in stub_calls(log) if "submitted" in entry]
    assert received == {name: sha256(text) for name, text in texts.items()}


def test_item_2_the_durables_declaration_submission_contains_the_income_sources(
    matsya_durables,
):
    """The declaration includes the fixed income functions Y and y_R;
    the submission needs no external writer and contains no code files."""
    folder = model.open_folder(matsya_durables)
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session_of(folder.root), 1)
    assert prepared.refusals == ()
    assert prepared.record["missing"] == []
    assert "declaration/calibration/wage_schedule.yml" in {
        entry["path"] for entry in prepared.record["files"]
    }
    assert all(entry["path"].startswith("declaration/") for entry in prepared.record["files"])


def test_item_3_an_accepted_job_survives_a_client_exit_with_a_warning_and_a_nonzero_code(
    matsya_durables, tmp_path, monkeypatch
):
    """The client prints the accepted job and then its warning that the
    service used its own key, with status 1: the request's record keeps the
    job's identifier, the status and the warning; the record with the
    request's delivery identifier stood before the client ran."""
    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    folder = model.open_folder(matsya_durables)
    session = session_of(folder.root)
    monkeypatch.setenv(
        "BELLMAN_WORKBENCH_MATSYA_STUB_REQUESTS", str(folder.root / matsya_work.REQUESTS_FOLDER)
    )
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_WARN", "1")
    work = matsya_work.submit(folder, prepared.path, session)
    kept = json.loads((folder.root / work.path).read_text(encoding="utf-8"))
    assert kept == work.record
    assert (kept["kind"], kept["accepted"], kept["exit_code"]) == ("job", "job-1", 1)
    assert "accepted job job-1 under its own Anthropic key" in kept["warning"]
    assert (kept["session"], kept["service"]) == session
    (submitted,) = [entry for entry in stub_calls(log) if "submitted" in entry]
    assert submitted["requests_before"] == [f"{kept['delivery']}.json"]


def test_item_4_on_reopening_the_saved_identifiers_are_polled_before_a_retry_is_offered(
    matsya_durables, tmp_path, monkeypatch
):
    """An accepted job, an accepted turn and a turn whose answer was lost.
    After the module is loaded again, as on reopening the page, recovery
    reads the three records and polls the job and the turn by their
    identifiers before it offers anything: a retry is offered for the lost
    turn alone, and sends its delivery identifier again, which the service
    answers with the turn it already holds."""
    folder = model.open_folder(matsya_durables)
    session = session_of(folder.root)
    job = matsya_work.submit(
        folder, matsya_work.prepare(folder, DURABLES, "recipe", session, 1).path, session
    )
    turn = matsya_work.start_turn(folder, session, "What does tenure choose?")
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOST", "1")
    lost = matsya_work.start_turn(folder, session, "And the keeper?")
    monkeypatch.delenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOST")
    assert (job.record["accepted"], turn.record["accepted"], lost.record["accepted"]) == (
        "job-1", "turn-1", None,
    )
    stub_job({"id": "job-1", "state": "running", "session": session.id, "label": {"number": 1}})

    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    reopened = importlib.reload(matsya_work)
    recovered = reopened.recover(folder, session)
    assert [(item.record["delivery"], item.state, item.retry) for item in recovered] == [
        (job.record["delivery"], "running", False),
        (turn.record["delivery"], "queued", False),
        (lost.record["delivery"], None, True),
    ]
    assert sorted(stub_calls(log)) == sorted(
        [["job", "status", "job-1", "--json"], ["turn", "status", session.id, "turn-1", "--json"]]
    )
    again = reopened.retry(folder, next(item for item in recovered if item.retry).record)
    assert again.record["accepted"] == "turn-2"
    assert again.record["delivery"] == lost.record["delivery"]
    assert stub_calls(log)[-1][:4] == ["ask", session.id, "--no-wait", "--delivery-id"]


def test_item_5_a_job_of_another_session_or_service_is_refused_with_the_reason(
    scratch_durables, tmp_path, monkeypatch
):
    """A job of another session is refused for discussion, download and
    adoption with the reason, and nothing is selected or written; a session
    whose service is not the effective one is refused before the client is
    asked about the job; a job of the selected session on its service is
    selected for discussion."""
    folder = model.open_folder(scratch_durables)
    session = session_of(folder.root)
    another = "0123456789abcdef" * 2
    stub_job({"id": "job-7", "state": "converged", "session": another,
              "label": {"number": 1}, "result": {"cycles_run": 1}})
    stub_job({"id": "job-8", "state": "converged", "session": session.id,
              "label": {"number": 2}, "result": {"cycles_run": 1}})
    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    reason = f"job job-7 belongs to session {another}, not to the selected session {session.id}"
    assert matsya_work.discuss(session, "job-7").refusal == f"{reason}, so it is not discussed"
    downloaded = matsya_work.download(folder, session, "job-7")
    assert downloaded.refusal == f"{reason}, so it is not downloaded"
    assert matsya_work.membership(session, "job-7", "adopted").refusal == (
        f"{reason}, so it is not adopted"
    )
    assert not (folder.root / matsya_work.OUTPUT_FOLDER).exists()
    assert not [call for call in stub_calls(log) if call[:2] == ["session", "select"]]

    elsewhere = matsya_work.Session(session.id, "a digest of another service")
    calls = len(stub_calls(log))
    assert matsya_work.discuss(elsewhere, "job-8").refusal == (
        f"the selected session {session.id} is kept by another service than the one the "
        "client's settings name now, so job job-8 is not discussed"
    )
    assert len(stub_calls(log)) == calls
    assert matsya_work.discuss(session, "job-8").refusal is None
    assert stub_calls(log)[-1] == ["session", "select", session.id, "job-8", "--json"]


def test_item_6_following_writes_nothing_and_a_download_writes_one_new_keyed_copy(
    scratch_durables,
):
    """Following a job reads its state and leaves every file of the folder
    as it was. A download writes one new copy under bellman-matsya-output/,
    named by the job, its iteration, the source revision and the
    configuration, and leaves economics.md; the same download again writes
    nothing; after a further iteration a second copy is written beside the
    first."""
    folder = model.open_folder(scratch_durables)
    session = session_of(folder.root)
    job = {"id": "job-3", "state": "converged", "session": session.id, "revision": 4,
           "configuration_id": "ab12cd34ef56" + "0" * 52, "label": {"number": 3},
           "result": {"cycles_run": 2}}
    stub_job(job)
    before = every_file(folder.root)
    followed = matsya_work.follow(
        {"kind": "job", "accepted": "job-3", "session": session.id, "service": session.service}
    )
    assert followed["state"] == "converged"
    assert every_file(folder.root) == before

    first = matsya_work.download(folder, session, "job-3")
    assert (first.refusal, first.written) == (None, True)
    assert first.path == (
        f"{matsya_work.OUTPUT_FOLDER}/job-3-iteration-2-revision-4-configuration-ab12cd34ef56"
    )
    after = every_file(folder.root)
    assert after["economics.md"] == before["economics.md"]
    assert {path for path in after if path not in before} == {
        f"{first.path}/{name}"
        for name in ("economics.md", "report.md", "declaration/spec.yml", "record.json")
    }
    assert all(after[path] == before[path] for path in before)

    repeated = matsya_work.download(folder, session, "job-3")
    assert (repeated.path, repeated.written, repeated.refusal) == (first.path, False, None)
    assert every_file(folder.root) == after

    stub_job({**job, "result": {"cycles_run": 3}})
    second = matsya_work.download(folder, session, "job-3")
    assert second.written
    assert second.path.endswith("job-3-iteration-3-revision-4-configuration-ab12cd34ef56")
    assert sorted(p.name for p in (folder.root / matsya_work.OUTPUT_FOLDER).iterdir()) == sorted(
        [first.path.split("/")[-1], second.path.split("/")[-1]]
    )


def test_prepare_refuses_a_file_outside_the_folder_a_missing_file_and_an_ambiguous_name(
    tmp_path, matsya_durables
):
    """Part 1's three refusals, each with nothing written: a trellis file of
    cons-port that reads the portfolio stage file of portfolio-choice,
    outside its folder's declaration/, its records naming no addition,
    which the service does not read yet (decision S7-W5); a recipe that
    names a calibration file that does not exist is refused with the
    package's sentence; and a source written without its extension where
    both its .yml and its .yaml files stand, of which the package reads the
    first."""
    consport = model.open_folder(applications_copy(tmp_path / "corpus"))
    # since the consolidation of 28 October 2026 the folder's trellis files
    # read its own stage files, so the test writes a file of records whose
    # portfolio stage is portfolio-choice's, outside the folder
    records = (consport.root / PORT_CONS_RECORDS).read_text(encoding="utf-8")
    records = re.sub(r"methods: stages/\w+/methods[.\w]*\.bl", "methods: []", records)
    assert records.count("stages/port/port.bl") == 1
    (consport.root / "declaration/trellis.outside.yml").write_text(
        records.replace("stages/port/port.bl", "../../portfolio-choice/declaration/stages/port/port.bl"),
        encoding="utf-8",
    )
    outside = matsya_work.prepare(
        consport, recipe.Source("trellis", "declaration/trellis.outside.yml"), "trellis",
        session_of(consport.root), 1,
    )
    assert outside.path is None
    assert (
        "../portfolio-choice/declaration/stages/port/port.bl lies outside the folder's "
        "declaration/, and the service reads every file from that folder"
    ) in outside.refusals

    folder = model.open_folder(matsya_durables)
    session = session_of(folder.root)
    calibration = folder.root / "declaration/calibration/durables.yml"
    (folder.root / "declaration/calibration/durables.yaml").write_text(
        calibration.read_text(encoding="utf-8"), encoding="utf-8"
    )
    ambiguous = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    assert ambiguous.refusals == (
        "calibration/durables names both calibration/durables.yml and calibration/durables.yaml; "
        "write the name with its extension",
    )
    calibration.unlink()
    (folder.root / "declaration/calibration/durables.yaml").unlink()
    missing = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    assert missing.path is None
    assert len(missing.refusals) == 1 and "calibration/durables" in missing.refusals[0]
    assert not (folder.root / matsya_work.WORK_FOLDER).exists()


def test_a_download_the_client_does_not_finish_leaves_no_copy_under_its_key(
    scratch_durables, monkeypatch
):
    """The client stops after the first file of a job's model folder: the
    download is refused with the client's sentence, no copy stands under
    the job's name and nothing is left under bellman-matsya-output/; the
    same download once the client finishes writes the copy."""
    folder = model.open_folder(scratch_durables)
    session = session_of(folder.root)
    stub_job({"id": "job-3", "state": "converged", "session": session.id, "revision": 4,
              "configuration_id": "ab12cd34ef56" + "0" * 52, "label": {"number": 3},
              "result": {"cycles_run": 2}})
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_FILES_FAIL", "1")
    failed = matsya_work.download(folder, session, "job-3")
    assert (failed.path, failed.written) == (None, False)
    assert failed.refusal == (
        "the client did not write the files of job job-3: Error: the connection closed after "
        "economics.md was written"
    )
    assert list((folder.root / matsya_work.OUTPUT_FOLDER).iterdir()) == []
    monkeypatch.delenv("BELLMAN_WORKBENCH_MATSYA_STUB_FILES_FAIL")
    written = matsya_work.download(folder, session, "job-3")
    assert written.written and (folder.root / written.path / "record.json").is_file()


def test_a_request_is_sent_again_or_submitted_only_where_that_cannot_start_work_twice(
    matsya_durables, monkeypatch
):
    """A prepared record of another session is not submitted, and an
    accepted turn or a job is not sent again: each is refused with a
    ValueError before the client runs or a record is written."""
    folder = model.open_folder(matsya_durables)
    session = session_of(folder.root)
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    other = matsya_work.Session("0123456789abcdef" * 2, session.service)
    with pytest.raises(ValueError, match="was prepared for session"):
        matsya_work.submit(folder, prepared.path, other)
    assert not (folder.root / matsya_work.REQUESTS_FOLDER).exists()
    job = matsya_work.submit(folder, prepared.path, session)
    turn = matsya_work.start_turn(folder, session, "What does tenure choose?")
    for accepted in (job.record, turn.record):
        with pytest.raises(ValueError, match="is no turn whose answer was lost"):
            matsya_work.retry(folder, accepted)
