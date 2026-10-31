"""The acceptance file of unit G1 of the specification 0.6 build, the client
side: the submission of a prepared-inputs file with the number of the last
session entry its user reviewed, the refusal to claim that capture against a
service whose index answer does not name it, the report of the effective
configuration without any secret, a turn started without waiting and read
again by its identifier from a later process, and the delivery identifier of
a turn and of a reply (the brief of unit G1 and the proposal of 21 October
2026 on the Matsya chat integration, §§4, 5 and 7). Items 1 and 3 run
against the Matsya service of the test configuration, items 4 to 6 against
the stand-in of `conftest.py`, which names no capability, as a service built
before unit G1 does. No test reaches another address or calls a model
provider."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ANSWER, DEFAULT_CONFIGURATION, PREPARER, STAGE, TOKEN

CLIENT_SOURCE = Path(__file__).resolve().parents[1] / "src"
KEY = "sk-ant-unit-g1-fixture-key-0123456789"
# the service's libraries warn of their own deprecations under Python 3.14;
# a warning of the client is still shown
pytestmark = [
    pytest.mark.filterwarnings(f"ignore::{category}:{module}")
    for category in ("DeprecationWarning", "PendingDeprecationWarning")
    for module in ("fastapi", "starlette", "uvicorn", "uvloop", "websockets")
]


def _session(run, tmp_path: Path, *texts: str) -> str:
    """A new session holding `texts` as its entries, made with the client's
    commands."""
    _, out, _ = run("session", "new", "a household")
    session_id = re.search(r"^Session ([0-9a-f]{32}): a household$", out, re.MULTILINE).group(1)
    for number, text in enumerate(texts, 1):
        entry = tmp_path / f"entry-{number}.md"
        entry.write_text(text + "\n", encoding="utf-8")
        assert run("session", "add", session_id, str(entry))[0] == 0
    return session_id


def _prepared(tmp_path: Path, session_id: str, reviewed_through: int) -> Path:
    path = tmp_path / f"prepared-{reviewed_through}.json"
    path.write_text(
        json.dumps(
            {
                "session": session_id,
                "reviewed_through": reviewed_through,
                "target": "stage",
                "starting_declaration": {"example.bl": STAGE},
                "paths": {"example.bl": "declaration/stages/example/example.bl"},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_item_1_a_prepared_submission_is_captured_and_a_stale_one_refused(
    service, run, tmp_path: Path
) -> None:
    session_id = _session(run, tmp_path, "A household saves.", "Income is risky.")

    status, out, err = run("job", "submit-prepared", str(_prepared(tmp_path, session_id, 1)))
    assert status == 1 and out == ""
    assert (
        "Error: The service refused the request (409): The session holds an entry after entry 1, "
        "the last entry the request reviewed: entry 2 (user); review it and submit again."
    ) in err

    status, out, err = run("job", "submit-prepared", str(_prepared(tmp_path, session_id, 2)), "--json")
    assert status == 0, err
    answer = json.loads(out)
    job = answer["job"]
    assert (job["reviewed_through"], job["revision"], job["entry_numbers"]) == (2, 2, [1, 2])
    assert answer["capabilities"] == ["capture_at_acceptance", "job_delivery_id"]
    assert answer["files"] == [
        {
            "name": "example.bl",
            "path": "declaration/stages/example/example.bl",
            "sha256": hashlib.sha256(STAGE.encode("utf-8")).hexdigest(),
        }
    ]
    request, held_session = service.application.state.jobs.pending(job["id"])
    assert held_session == session_id
    assert (request["reviewed_through"], request["starting_declaration"]) == (2, {"example.bl": STAGE})

    # the plain lines name the history the service fixed
    status, out, err = run("job", "submit-prepared", str(_prepared(tmp_path, session_id, 2)))
    assert status == 0, err
    assert re.search(
        rf"^The service fixed session {session_id} through entry 2 at acceptance: version 2 of "
        r"its text, entries 1, 2\.$",
        out,
        re.MULTILINE,
    )


def test_item_3_a_turn_and_a_reply_carry_their_delivery_identifiers(
    service, run, tmp_path: Path
) -> None:
    from scripted import prepared

    session_id = _session(run, tmp_path, "A household saves.")
    asked = ("ask", session_id, "What is a perch?", "--no-wait", "--delivery-id", "turn-1", "--json")
    status, out, err = run(*asked)
    assert status == 0, err
    first = json.loads(out)
    status, out, err = run(*asked)
    assert status == 0, err
    again = json.loads(out)
    assert (again["id"], again["question"], again["repeated"]) == (first["id"], first["question"], True)

    # the turn has no scripted answer and ends failed before the script is
    # replaced; then a job that ends with a question, and a reply to it
    # delivered twice
    assert run("turn", "wait", session_id, first["id"], "--interval", "0.05")[0] == 0
    service.caller.replies.clear()
    service.caller.replies.append((PREPARER, prepared(questions=["Which income process?"])))
    status, out, err = run("job", "submit", "--session", session_id, "--target", "stage", "--json")
    assert status == 0, err
    job_id = json.loads(out)["id"]
    assert json.loads(run("job", "wait", job_id, "--interval", "0.05", "--json")[1])["state"] == "needs_input"
    listing = json.loads(run("session", "show", session_id, "--json")[1])
    question = listing["entries"][-1]["number"]
    reply = tmp_path / "reply.md"
    reply.write_text("An AR(1) process.\n", encoding="utf-8")
    added = ("session", "add", session_id, str(reply), "--replies-to", str(question), "--delivery-id", "reply-1")
    status, out, err = run(*added)
    assert status == 0, err
    assert "The reply started the next preparation attempt of the job awaiting an answer" in out
    status, out, err = run(*added)
    assert status == 0, err
    assert out.splitlines()[0].endswith("already holds this delivery as entry " f"{question + 1}; nothing was appended.")
    assert "preparation attempt" not in out
    listing = json.loads(run("session", "show", session_id, "--json")[1])
    assert len(listing["jobs"]) == 2 and len(listing["turns"]) == 1


def test_item_4_a_service_without_the_capability_is_refused_the_claim_with_the_reason(
    stand_in, run, tmp_path: Path
) -> None:
    session_id = stand_in._new_session({"name": "a household"})[1]["id"]
    status, out, err = run("job", "submit-prepared", str(_prepared(tmp_path, session_id, 1)))
    assert status == 1 and out == ""
    assert (
        f"Error: The service at {stand_in.url} does not name the capability capture_at_acceptance "
        "in its index answer, so it would build the job from the session's text as it stands when "
        "the job starts, not from the history reviewed through entry 1; the prepared inputs were "
        f"not submitted. bellman-matsya job submit --session {session_id} --target stage submits "
        "a job that reads the session as it stands."
    ) in err
    # the session was made in the stand-in directly, so that the client sent
    # one request, for the index, and no job request
    assert [(seen["method"], seen["path"]) for seen in stand_in.requests] == [("GET", "/v1/index")]


def test_item_5_the_effective_configuration_report_holds_no_secret(
    stand_in, run, monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("BELLMAN_MATSYA_ANTHROPIC_KEY", KEY)
    session_id = "0" * 32
    status, out, err = run("configuration", "effective", "--session", session_id)
    assert status == 0, err
    assert TOKEN not in out + err and KEY not in out + err
    assert out.splitlines() == [
        f"Service: {stand_in.url} (from BELLMAN_MATSYA_SERVER)",
        "Matsya token: set (from BELLMAN_MATSYA_TOKEN)",
        f"Configuration: {DEFAULT_CONFIGURATION}, version 0.3.5, the service's default",
        f"Session: {session_id} (from --session)",
        "Anthropic key: your personal key (from BELLMAN_MATSYA_ANTHROPIC_KEY)",
        "Capabilities: none named by the service",
    ]
    status, out, err = run("configuration", "effective", "--session", session_id, "--json")
    assert status == 0, err
    assert TOKEN not in out + err and KEY not in out + err
    assert json.loads(out) == {
        "server": stand_in.url,
        "server_source": "BELLMAN_MATSYA_SERVER",
        "token_source": "BELLMAN_MATSYA_TOKEN",
        "configuration_id": DEFAULT_CONFIGURATION,
        "configuration_version": "0.3.5",
        "configuration_source": "the service's default",
        "session": session_id,
        "session_source": "--session",
        "key_source": "BELLMAN_MATSYA_ANTHROPIC_KEY",
        "credential": "client",
        "service_version": None,
        "capabilities": [],
    }


def _command(stand_in, tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess:
    """The command `bellman-matsya` run as a process of its own, with the
    worktree's client first on the path, a home folder of the test's own and
    the stand-in's address and Matsya token."""
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("BELLMAN_MATSYA_") and name.lower() not in ("http_proxy", "https_proxy", "all_proxy")
    }
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    environment.update(
        HOME=str(home),
        PYTHONPATH=os.pathsep.join([str(CLIENT_SOURCE), environment.get("PYTHONPATH", "")]),
        BELLMAN_MATSYA_TOKEN=TOKEN,
        BELLMAN_MATSYA_SERVER=stand_in.url,
        NO_PROXY="127.0.0.1,localhost",
        no_proxy="127.0.0.1,localhost",
    )
    return subprocess.run(
        [sys.executable, "-m", "bellman_matsya.cli", *arguments],
        capture_output=True,
        text=True,
        env=environment,
        timeout=60,
        check=False,
    )


def test_item_6_a_turn_started_without_waiting_is_read_by_its_identifier_from_a_later_process(
    stand_in, tmp_path: Path
) -> None:
    session_id = stand_in._new_session({"name": "a household"})[1]["id"]
    started = _command(stand_in, tmp_path, "ask", session_id, "What is a perch?", "--no-wait")
    assert started.returncode == 0, started.stderr
    turn_id = re.search(r"^Turn ([0-9a-f]{32}): queued", started.stdout, re.MULTILINE).group(1)
    assert f"bellman-matsya turn status {session_id} {turn_id}" in started.stdout
    # the process that started the turn has ended; later processes read it
    read = _command(stand_in, tmp_path, "turn", "status", session_id, turn_id, "--json")
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout)["state"] in ("queued", "running")
    waited = _command(stand_in, tmp_path, "turn", "wait", session_id, turn_id, "--interval", "0.01")
    assert waited.returncode == 0, waited.stderr
    assert ANSWER in waited.stdout.splitlines()


def test_item_3_a_prepared_submission_repeated_under_its_delivery_identifier_creates_one_job(
    service, run, tmp_path: Path
) -> None:
    session_id = _session(run, tmp_path, "A household saves.")
    prepared = str(_prepared(tmp_path, session_id, 1))
    status, out, err = run("job", "submit-prepared", prepared, "--delivery-id", "job-1", "--json")
    assert status == 0, err
    first = json.loads(out)["job"]
    assert first["repeated"] is False
    # the acknowledgement is taken as lost, and the same request is sent again
    status, out, err = run("job", "submit-prepared", prepared, "--delivery-id", "job-1")
    assert status == 0, err
    assert f"Job {first['id']}: " in out
    assert "The service already holds delivery job-1 as this job; nothing was submitted again." in out
    listing = json.loads(run("session", "show", session_id, "--json")[1])
    assert [job["id"] for job in listing["jobs"]] == [first["id"]]


def test_item_5_a_key_the_client_does_not_send_to_the_address_is_reported_refused(
    stand_in, run, monkeypatch
) -> None:
    """A personal key selected for a plain-HTTP address that is not a
    loopback host is reported `refused`: the client sends no new work there.
    The address is reached through the stand-in as a proxy, as the request
    for the index carries no key."""
    remote = "http://matsya.example.test"
    monkeypatch.setenv("BELLMAN_MATSYA_ANTHROPIC_KEY", KEY)
    monkeypatch.setenv("BELLMAN_MATSYA_SERVER", remote)
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    for name in ("http_proxy", "HTTP_PROXY"):
        monkeypatch.setenv(name, stand_in.url)
    status, out, err = run("configuration", "effective", "--json")
    assert status == 0, err
    report = json.loads(out)
    assert (report["server"], report["key_source"], report["credential"]) == (
        remote, "BELLMAN_MATSYA_ANTHROPIC_KEY", "refused",
    )
    status, out, err = run("configuration", "effective")
    assert status == 0, err
    assert (
        "Anthropic key: your personal key (from BELLMAN_MATSYA_ANTHROPIC_KEY), which the client "
        f"does not send to {remote}, so new work is refused before any request"
    ) in out.splitlines()
    assert KEY not in out + err and TOKEN not in out + err
    assert [seen["path"] for seen in stand_in.requests] == [remote + "/v1/index"] * 2
    assert all(KEY not in json.dumps(seen["headers"]) for seen in stand_in.requests)


def test_item_5_a_project_folder_of_another_service_is_refused_before_its_session_is_reported(
    stand_in, run, monkeypatch, tmp_path: Path
) -> None:
    folder = tmp_path / "project"
    (folder / ".bellman-matsya").mkdir(parents=True)
    held = {"session": "1" * 32, "server": stand_in.url, "economics_sha256": None}
    (folder / ".bellman-matsya" / "project.json").write_text(json.dumps(held), encoding="utf-8")
    monkeypatch.chdir(folder)
    status, out, err = run("configuration", "effective")
    assert status == 0, err
    assert f"Session: {'1' * 32} (from .bellman-matsya/project.json)" in out.splitlines()

    held["server"] = "http://elsewhere.example.test"
    (folder / ".bellman-matsya" / "project.json").write_text(json.dumps(held), encoding="utf-8")
    status, out, err = run("configuration", "effective")
    assert (status, out) == (2, "")
    assert (
        "Error: This folder's session is kept by the service at http://elsewhere.example.test, "
        f"and the client is configured for the service at {stand_in.url}"
    ) in err
