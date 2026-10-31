"""Unit G5 of specification 0.6: the acceptance of the Matsya chat
integration, the six cases of amendment 06 §5 of the model-interface
specification, one test each, `test_case_<n>_<claim>`.

Each case runs the Workbench's own operations, `matsya_work.py`,
`returned.py` and the functions of the column in `matsya_window.py`, on
scratch copies of the application models, with real local file operations.
The service is either the stand-in of the client, `tests/matsya_stub.py`,
whose answers the test writes into its service file, or, where a case needs
the client's real command line, the client `bellman-matsya` of this checkout
run against the Matsya service of the service package's test configuration,
started on the loopback address with a processor that calls no model
provider (`local_service`). No test reaches the installed service.

Each case keeps what it observed in a folder of its own, `case-<n>`, under
the folder that BELLMAN_WORKBENCH_G5_OBSERVED names, else under the test's
temporary folder: the model folder's records under `.bellman-matsya/`, each
saved copy's `record.json` with the digests of its files, the stand-in's
service and its log of the client's runs, and `observed.json`, the values
and the sentences the case read, refusals included.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import importlib
import json
import os
import shlex
import shutil
import socket
import sqlite3
import sys
import threading
import urllib.request
from pathlib import Path

import ipyvue
import pytest
import solara
from workbench_support import (
    MATSYA_STUB,
    pensions_two_templates,
    returned_job,
    stub_calls,
    stub_job,
    stub_turn,
    wait_until,
)

from bellman_workbench import (
    matsya_client,
    matsya_window,
    matsya_work,
    model,
    recipe,
    returned,
    trellis,
)

# the service package's own tests, whose fixture configuration and helper
# modules `local_service` reads
SERVICE_TESTS = Path(__file__).resolve().parents[2] / "matsya" / "tests"
sys.path.insert(0, str(SERVICE_TESTS))
# the client's command, installed beside the interpreter; the package it
# imports is the one the import path names first, this checkout's
REAL_CLIENT = Path(sys.executable).with_name("bellman-matsya")
OBSERVED_VARIABLE = "BELLMAN_WORKBENCH_G5_OBSERVED"

# the service's libraries warn of their own deprecations under Python 3.14
pytestmark = [
    pytest.mark.filterwarnings(f"ignore::{category}:{module}")
    for category in ("DeprecationWarning", "PendingDeprecationWarning")
    for module in ("fastapi", "starlette", "uvicorn", "uvloop", "websockets")
]

DURABLES = recipe.Source("recipe", "declaration/spec.yml")
PENSIONS = recipe.Source("recipe", "declaration/spec.pensions.yml")
SHOCKS = "declaration/stages/shocks/shocks.bl"
TENURE = "declaration/stages/tenure/tenure.bl"
CALIBRATION = "declaration/calibration/durables.yml"
SETTINGS = "declaration/settings/durables.yml"
HIGH, LOW, LOWER = "τ: 0.12", "τ: 0.08", "τ: 0.05"
# the stand-in's service address, which its `project init` records
STAND_IN_SERVER = "http://127.0.0.1:8710"

# the Matsya tokens of the two principals of `local_service`, the author
# of a model and a colleague who receives the folder
AUTHOR_TOKEN = "msy_" + "a" * 32
COLLEAGUE_TOKEN = "msy_" + "b" * 32
# a job of `local_service` whose source holds HOLD waits until the test
# releases it; every job ends `needs_input` with QUESTION
HOLD = "Hold this job until the test releases it."
QUESTION = "Which income process does the household face?"
ENDED = ("converged", "not_converged", "needs_input", "cancelled", "failed", "interrupted")
PROXIES = ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY")
PERSONAL_KEYS = ("BELLMAN_MATSYA_ANTHROPIC_KEY", "BELLMAN_MATSYA_ANTHROPIC_KEY_OVER_HTTP")
FIXTURE_KEY = "sk-ant-unit-g5-fixture-key-0123456789"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def every_file(folder: Path) -> dict:
    """The bytes of each file of `folder` by its path, git's files left out."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(folder).parts
    }


def session_of(folder: model.Folder) -> matsya_work.Session:
    """A session of the stand-in's service for `folder`, an identifier of 32
    hexadecimal characters, on the service the client's settings name now."""
    return matsya_work.Session(sha256(folder.root.name)[:32], matsya_client.service_identity())


def connected(folder: model.Folder) -> matsya_work.Session:
    """The folder connected to the stand-in's service as the client's
    `project init` records a connection, and the folder's session."""
    project = folder.root / matsya_work.PROJECT_FILE
    project.parent.mkdir(parents=True, exist_ok=True)
    held = {"session": sha256(folder.root.name)[:32], "server": STAND_IN_SERVER}
    project.write_text(json.dumps(held), encoding="utf-8")
    return matsya_work.connected_session(folder)


def calls_of(log: Path) -> list:
    """The command lines of the client's runs the stand-in logged."""
    return [entry for entry in stub_calls(log) if isinstance(entry, list)]


@pytest.fixture(autouse=True)
def client_settings(monkeypatch):
    """The client's address and token for every case, the stand-in's, and
    no personal Anthropic key, so that no case reads the address, the token
    or the key of the environment it runs in."""
    monkeypatch.setenv("BELLMAN_MATSYA_SERVER", STAND_IN_SERVER)
    monkeypatch.setenv("BELLMAN_MATSYA_TOKEN", "msy_" + "0" * 32)
    for name in PERSONAL_KEYS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def real_client(monkeypatch, tmp_path):
    """A function `use(address, token)` that makes the Workbench run the
    client `bellman-matsya` itself against the service at `address` with the
    Matsya token `token`: the client's command, a home folder of the test's
    own with no configuration file, the address and the token in the
    client's two variables, and no proxy; `use(None, None)` returns the
    Workbench to the stand-in."""
    home = tmp_path / "home"
    home.mkdir()

    def use(address: str | None, token: str | None) -> None:
        if address is None:
            monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA", MATSYA_STUB)
            monkeypatch.setenv("BELLMAN_MATSYA_SERVER", STAND_IN_SERVER)
            return
        monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA", shlex.join([str(REAL_CLIENT)]))
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("BELLMAN_MATSYA_SERVER", address)
        monkeypatch.setenv("BELLMAN_MATSYA_TOKEN", token)
        for name in PROXIES:
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
        monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")

    return use


@pytest.fixture
def kept(tmp_path):
    """A function `keep(case, folders, observed, log=None)` that writes what
    a case observed into `case-<n>` under the folder of OBSERVED_VARIABLE,
    else under the test's temporary folder, replacing what stood there:
    each model folder's `.bellman-matsya/` as it stands, each saved copy's
    `record.json` and the digests of its files (`files.json`), the
    stand-in's service file, the log `log`, and `observed.json`."""
    root = Path(os.environ.get(OBSERVED_VARIABLE) or tmp_path / "observed")

    def keep(case: str, folders: dict, observed: dict, log: Path | None = None) -> Path:
        target = root / case
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        for name, folder in folders.items():
            records = folder / ".bellman-matsya"
            if records.is_dir():
                shutil.copytree(records, target / name / ".bellman-matsya")
            output = folder / model.OUTPUT_FOLDER
            for copy in sorted(output.iterdir()) if output.is_dir() else ():
                if copy.name.startswith("."):
                    continue
                kept_copy = target / name / model.OUTPUT_FOLDER / copy.name
                kept_copy.mkdir(parents=True)
                if (copy / "record.json").is_file():
                    shutil.copy2(copy / "record.json", kept_copy / "record.json")
                digests = {
                    path.relative_to(copy).as_posix(): hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
                    for path in sorted(copy.rglob("*"))
                    if path.is_file()
                }
                (kept_copy / "files.json").write_text(
                    json.dumps(digests, indent=1) + "\n", encoding="utf-8"
                )
        service = Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"])
        if service.is_file():
            shutil.copy2(service, target / "stand-in-service.json")
        if log is not None and log.is_file():
            shutil.copy2(log, target / "client-calls.jsonl")
        (target / "observed.json").write_text(
            json.dumps(observed, ensure_ascii=False, indent=1, default=str) + "\n",
            encoding="utf-8",
        )
        return target

    return keep


# --- the Matsya service of the service package's test configuration ---


class HeldProcessor:
    """The service's processor in these cases, which calls no model
    provider: it keeps the source material of each job it runs and ends
    every job `needs_input` with QUESTION. A job whose source text holds
    HOLD first waits until `release` is set, so that two such jobs keep
    both of the service's workers busy and a job submitted after them stays
    queued; its source is not kept."""

    def __init__(self) -> None:
        self.sources: list[dict] = []
        self.holding = threading.Semaphore(0)
        self.release = threading.Event()

    def process(self, payload: dict, progress=None, identity=None, **options) -> dict:
        source = payload.get("source") or {}
        if HOLD in str(source.get("text", "")):
            self.holding.release()
            self.release.wait(60)
        else:
            self.sources.append(source)
        return {
            "schema": "matsya-model-iteration/6",
            "status": "needs_input",
            "questions": [QUESTION],
            "reading": {
                "guides": {},
                "index_digest": None,
                "allowed_sources": [],
                "invocations": [],
            },
        }


class _Embeddings:
    """A sentence encoder for the service's small index: every text is one
    fixed vector, as in the service's own tests."""

    model_id = "stand-in-embedding-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.1] for _ in texts]


@contextlib.contextmanager
def local_service(folder: Path):
    """The Matsya service under the service package's test configuration,
    with the conversation role and an index of one published page, served
    by uvicorn on the loopback address: two principals, 11 the author and 12
    a colleague, with AUTHOR_TOKEN and COLLEAGUE_TOKEN; jobs run by
    `HeldProcessor`, turns by a caller that holds no answer. Yields the
    service's address and the processor."""
    import uvicorn
    from conversation_parts import add_conversation_role, remove_conversation_role
    from matsya_service.api import create_app
    from matsya_service.configuration import write_manifest
    from matsya_service.retrieval import activate_candidate, build_candidate, load_active
    from scripted import ScriptedCaller

    configuration = folder / "configuration"
    shutil.copytree(
        SERVICE_TESTS / "fixtures" / "configuration",
        configuration,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    remove_conversation_role(configuration)
    add_conversation_role(configuration)
    write_manifest(configuration, "fixture")
    repository = folder / "repository"
    page = repository / "docs" / "Bellman-Sym" / "01-stage.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        "# The stage\n\nA stage file names its arrival, decision and continuation fields.\n",
        encoding="utf-8",
    )
    sources = folder / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "corpus_revisions": {},
                "sources": [
                    {
                        "corpus": "repository",
                        "source_id": "repository:docs/Bellman-Sym/01-stage",
                        "path": "docs/Bellman-Sym/01-stage.md",
                        "sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
                        "kind": "markdown",
                        "authority": "primary",
                        "access": "public",
                        "model_prompt": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    roots = {"repository": repository}
    activate_candidate(
        build_candidate(sources, roots, folder / "index", _Embeddings()),
        folder / "index",
        roots,
        _Embeddings(),
    )
    tokens = folder / "tokens.db"
    with contextlib.closing(sqlite3.connect(tokens)) as db, db:
        db.execute("CREATE TABLE principals (id INTEGER PRIMARY KEY, label TEXT)")
        db.execute("INSERT INTO principals VALUES (11, 'author'), (12, 'colleague')")
        db.execute(
            "CREATE TABLE bellman_matsya_auth (service TEXT PRIMARY KEY, schema_version INTEGER)"
        )
        db.execute("INSERT INTO bellman_matsya_auth VALUES ('bellman-ddsl-matsya', 1)")
        db.execute(
            "CREATE TABLE tokens (id INTEGER PRIMARY KEY, principal_id INTEGER, "
            "token_hash TEXT, revoked_at TEXT)"
        )
        for number, (principal, token) in enumerate(
            ((11, AUTHOR_TOKEN), (12, COLLEAGUE_TOKEN)), 1
        ):
            db.execute(
                "INSERT INTO tokens VALUES (?, ?, ?, NULL)",
                (number, principal, hashlib.sha256(token.encode()).hexdigest()),
            )
    processor = HeldProcessor()
    application = create_app(
        processor=processor,
        retrieval_index=load_active(folder / "index", _Embeddings(), None),
        token_db_path=tokens,
        job_db_path=folder / "jobs.db",
        configuration=configuration,
        turn_caller_factory=lambda roles, ledger, **options: ScriptedCaller([]),
    )
    listening = socket.socket()
    listening.bind(("127.0.0.1", 0))
    server = uvicorn.Server(
        uvicorn.Config(application, log_level="warning", log_config=None, lifespan="on")
    )
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listening]}, daemon=True)
    thread.start()
    wait_until(lambda: server.started or not thread.is_alive(), 20.0, "the service's start")
    assert server.started, "the Matsya service of the test configuration did not start"
    try:
        yield f"http://127.0.0.1:{listening.getsockname()[1]}", processor
    finally:
        processor.release.set()
        server.should_exit = True
        thread.join(10)
        listening.close()


def post(address: str, token: str, path: str, body: dict) -> dict:
    """The local service's answer to one request the test sends itself,
    past any proxy."""
    request = urllib.request.Request(
        address + path,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
        request, timeout=10
    ) as answer:
        return json.loads(answer.read())


def ended_job(record: dict) -> dict:
    """The service's answer for the job of the request `record` once the
    job has ended, read by the Workbench's `follow`."""
    found, _ = wait_until(
        lambda: (lambda job: job if job and job.get("state") in ENDED else None)(
            matsya_work.follow(record)
        ),
        20.0,
        "the job's end",
    )
    return found


def ended_by_identifier(job_id: str) -> dict:
    """The service's answer for the job `job_id` once it has ended, read by
    the client's `job status`."""
    found, _ = wait_until(
        lambda: (
            lambda ran: ran.answer if ran.answer and ran.answer.get("state") in ENDED else None
        )(matsya_client.run(["job", "status", job_id, "--json"])),
        20.0,
        f"the end of job {job_id}",
    )
    return found


def session_shown(session_id: str) -> dict:
    """The session as the client's `session show --json` prints it."""
    ran = matsya_client.run(["session", "show", session_id, "--json"])
    assert ran.code == 0, ran.warning
    return ran.answer


# --- case 1 ---


def test_case_1_the_bytes_reviewed_are_the_bytes_sent_and_each_missing_input_is_named(
    tmp_path, scratch_durables, monkeypatch, real_client, kept
):
    """Amendment 06 §5 case 1 (§2 items 11 and 12). The named pensions
    recipe `spec.pensions.yml`, whose trellis file names two period
    templates, with an unsaved edit of the shocks stage in the editor:
    without a choice nothing is prepared and the difference from disk is
    shown; sent as the displayed text, the texts the stand-in receives are,
    byte for byte, those of the prepared-inputs file the record names, under
    the names and fingerprints the record lists, the recipe's one rewritten
    entry included, and the disk keeps its text. The durables recipe's
    record names Y and y_R of tenure as missing from the declaration, with
    the function of the folder's code that writes them. A PDF given to the
    client as a paper is refused before any request, with the client's
    sentence asking for its text."""
    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    pensions = model.open_folder(pensions_two_templates(tmp_path / "pensions"))
    session = session_of(pensions)
    disk = (pensions.root / SHOCKS).read_text(encoding="utf-8")
    edited = disk + "# the edit under review, not yet saved\n"
    buffers = {SHOCKS: matsya_work.Buffer(edited, sha256(disk))}

    unchosen = matsya_work.prepare(pensions, PENSIONS, "recipe", session, 1, buffers=buffers)
    assert unchosen.path is None and unchosen.refusals == (
        f"{SHOCKS} has unsaved changes; save it, send the saved version or send the "
        "displayed text",
    )
    assert "+# the edit under review, not yet saved" in unchosen.differences[SHOCKS]

    prepared = matsya_work.prepare(
        pensions,
        PENSIONS,
        "recipe",
        session,
        1,
        buffers=buffers,
        choice=matsya_work.DISPLAYED_TEXT,
    )
    assert prepared.refusals == ()
    record = prepared.record
    inputs_bytes = (pensions.root / record["inputs"]).read_bytes()
    assert record["inputs_sha256"] == hashlib.sha256(inputs_bytes).hexdigest()
    reviewed = json.loads(inputs_bytes)["starting_declaration"]
    assert sorted(entry["name"] for entry in record["files"]) == sorted(reviewed)
    templates = sorted(
        entry["path"]
        for entry in record["files"]
        if Path(entry["path"]).name.startswith("period.")
    )
    assert templates == ["declaration/period.pensions.yml", "declaration/period.working.yml"]
    assert record["rewritten"] == [
        {
            "path": PENSIONS.path,
            "entry": "trellis",
            "written": "trellis.pensions.yml",
            "sent": "trellis.yml",
        }
    ]
    for entry in record["files"]:
        if entry["name"] != "spec.yml":
            assert entry["sha256"] == sha256(reviewed[entry["name"]]), entry
    recipe_text = (pensions.root / PENSIONS.path).read_text(encoding="utf-8")
    assert reviewed["spec.yml"] == recipe_text.replace(
        "trellis: trellis.pensions.yml", "trellis: trellis.yml"
    )
    assert reviewed["shocks.bl"] == edited
    shocks = next(entry for entry in record["files"] if entry["path"] == SHOCKS)
    assert (shocks["text"], record["choice"]) == ("buffer", matsya_work.DISPLAYED_TEXT)

    work = matsya_work.submit(pensions, prepared.path, session)
    (received,) = [entry["submitted"] for entry in stub_calls(log) if "submitted" in entry]
    assert received == {name: sha256(text) for name, text in reviewed.items()}
    assert (pensions.root / SHOCKS).read_text(encoding="utf-8") == disk
    assert work.record["accepted"] == "job-1"

    durables = model.open_folder(scratch_durables)
    declared = matsya_work.prepare(durables, DURABLES, "recipe", session_of(durables), 1)
    assert declared.refusals == ()
    [missing] = declared.record["missing"]
    assert (missing["stage"], missing["names"], missing["function"], missing["file"]) == (
        "tenure",
        ["Y", "y_R"],
        "write_wage_schedule",
        "code/wage_schedule.py",
    )
    assert missing["sentence"].endswith(
        "which a submission of the declaration omits; supply their values"
    )

    real_client("http://127.0.0.1:9", "msy_" + "0" * 32)
    paper = tmp_path / "paper.pdf"
    paper.write_bytes(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n")
    refused = matsya_client.run(["session", "add", session.id, str(paper), "--kind", "paper"])
    assert refused.code == 2 and refused.answer is None
    assert refused.warning.endswith(
        "error: A paper is sent as Markdown or LaTeX text; convert the PDF first."
    )
    kept(
        "case-1",
        {"pensions": pensions.root, "durables": durables.root},
        {
            "unchosen_refusals": unchosen.refusals,
            "pensions_files": len(record["files"]),
            "period_templates": templates,
            "rewritten": record["rewritten"],
            "sent_equals_reviewed": received == {n: sha256(t) for n, t in reviewed.items()},
            "disk_unchanged": True,
            "durables_missing": missing,
            "pdf_refusal": {"exit_status": refused.code, "standard_error": refused.warning},
        },
        log,
    )


# --- case 2 ---


def test_case_2_the_reviewed_history_is_read_one_reply_continues_once_and_results_stand_apart(
    tmp_path, scratch_durables, monkeypatch, real_client, kept, matsya_state
):
    """Amendment 06 §5 case 2 (§2 items 13, 16 and 25), end to end through
    the Workbench's adapter, the client's command line and the local
    service. A submission that reviewed entry 1 while entry 2 stands is
    refused with the service's sentence asking for a refreshed review, and
    the request's record keeps it; a submission that reviewed entry 2 is
    accepted, and entry 3, appended while the job waits in the queue, is not
    read: the job reads entries 1 and 2 and its label marks it overtaken.
    An overtaken job's question is not entered in the session, so nothing
    awaits an answer to it. A current job's question is answered by a reply
    with its delivery identifier, which starts one continuation; the same
    delivery again, as after a lost acknowledgement, is recognized and
    starts nothing; a reply to that question once a later job awaits an
    answer starts nothing either. Then, on the stand-in, a job that did not
    converge keeps its provisional files in the saved copy, and its result
    stands in five parts apart."""
    folder = model.open_folder(scratch_durables)
    with local_service(tmp_path / "service") as (address, processor):
        real_client(address, AUTHOR_TOKEN)
        project, refusal = matsya_work.connect(folder)
        assert refusal is None
        session = matsya_work.connected_session(folder)
        request = matsya_work.add_entry(folder, session, "Lower the housing cost τ to 0.08.")
        assert request.record["accepted"] == "2"

        stale = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
        refused = matsya_work.submit(folder, stale.path, session)
        stale_sentence = (
            "Error: The service refused the request (409): The session holds an entry after "
            "entry 1, the last entry the request reviewed: entry 2 (user); review it and submit "
            "again."
        )
        assert (refused.record["accepted"], refused.record["exit_code"]) == (None, 1)
        assert refused.record["warning"] == stale_sentence

        for _ in range(2):
            post(
                address,
                AUTHOR_TOKEN,
                "/v1/model-iterations",
                {"source": {"kind": "description", "text": HOLD}, "target": "stage"},
            )
        assert processor.holding.acquire(timeout=10) and processor.holding.acquire(timeout=10)
        current = matsya_work.prepare(folder, DURABLES, "recipe", session, 2)
        accepted = matsya_work.submit(folder, current.path, session)
        first_job = accepted.record["accepted"]
        assert first_job is not None and accepted.record["exit_code"] == 0
        later = matsya_work.add_entry(folder, session, "Let the wage grow with age.")
        assert later.record["accepted"] == "3"
        waiting = matsya_work.follow(accepted.record)
        assert (waiting["state"], waiting["reviewed_through"], waiting["entry_numbers"]) == (
            "queued",
            2,
            [1, 2],
        )
        processor.release.set()
        first = ended_job(accepted.record)
        assert first["state"] == "needs_input"
        assert first["result"]["captured_source"] == {
            "reviewed_through": 2,
            "revision": 2,
            "entries": [1, 2],
        }
        [read] = processor.sources
        assert read["text"].startswith("Entry 1 (user):")
        assert "Entry 2 (user):\nLower the housing cost τ to 0.08." in read["text"]
        assert "Let the wage grow with age." not in read["text"]
        assert first["label"]["overtaken"] is True and first["current"] is False
        assert first["label"]["text"].endswith("built from an earlier version")
        shown = session_shown(session.id)
        assert shown["awaiting_answer"] is None
        assert [entry["kind"] for entry in shown["entries"]] == ["user", "user", "user"]

        second = matsya_work.submit(
            folder, matsya_work.prepare(folder, DURABLES, "recipe", session, 3).path, session
        )
        asked = ended_job(second.record)
        assert (asked["state"], asked["current"]) == ("needs_input", True)
        shown = session_shown(session.id)
        assert shown["awaiting_answer"] == second.record["accepted"]
        [question] = [entry for entry in shown["entries"] if entry["kind"] == "question"]
        assert question["text"] == QUESTION

        reply = tmp_path / "reply.md"
        reply.write_text("An AR(1) process with persistence 0.9.\n", encoding="utf-8")
        replied = [
            "session",
            "add",
            session.id,
            str(reply),
            "--replies-to",
            str(question["number"]),
            "--delivery-id",
            "reply-1",
            "--json",
        ]
        once = matsya_client.run(replied)
        assert once.code == 0 and once.answer["repeated"] is False
        continuation = once.answer["scheduled"]["id"]
        again = matsya_client.run(replied)
        assert again.code == 0 and again.answer["repeated"] is True
        assert again.answer["scheduled"] is None
        assert again.answer["entry"]["number"] == once.answer["entry"]["number"]
        ended_by_identifier(continuation)
        assert session_shown(session.id)["awaiting_answer"] == continuation
        overtaken = matsya_client.run([*replied[:-3], "--delivery-id", "reply-2", "--json"])
        assert overtaken.code == 0 and overtaken.answer["scheduled"] is None
        jobs = [job["id"] for job in session_shown(session.id)["jobs"]]
        assert jobs == [first_job, second.record["accepted"], continuation]

    real_client(None, None)
    session = connected(folder)
    job = returned_job(folder.root, session.id, 7, 3, {CALIBRATION: (HIGH, LOW)})
    difference = "tenure: the law of motion of H differs from the earlier attempt's"
    comment = "The prose reads τ as a share of the house's value; the source names no unit."
    assumption = "Is τ paid every period or only when the house is sold?"
    stub_job(
        {
            **job,
            "state": "not_converged",
            "result": {
                "cycles_run": 3,
                "comparison": {"converged": False, "differences": [difference]},
                "comments": [comment],
                "questions": [assumption],
            },
        }
    )
    copy = matsya_work.download(folder, session, "job-7")
    assert copy.written and copy.refusal is None
    provisional = (folder.root / copy.path / CALIBRATION).read_text(encoding="utf-8")
    assert LOW in provisional and HIGH in (folder.root / CALIBRATION).read_text(encoding="utf-8")
    inspected = returned.inspect(folder, copy.path)
    answer = matsya_work.membership(session, "job-7", "discussed").job
    found = matsya_window.parts(matsya_window.JobView(answer, copy.path, inspected))
    assert [part.name for part in found] == list(matsya_window.PART_NAMES)
    assert [part.value for part in found] == ["not converged", "1", "1", "constructed", "not run"]
    assert (found[0].details, found[1].details, found[2].details) == (
        (difference,),
        (comment,),
        (assumption,),
    )
    assert found[3].details == inspected.construction and inspected.missing == ()
    kept(
        "case-2",
        {"durables": folder.root},
        {
            "stale_refusal": refused.record["warning"],
            "waiting": waiting,
            "captured_source": first["result"]["captured_source"],
            "source_read_by_the_job": read,
            "first_label": first["label"],
            "awaiting_after_the_overtaken_job": None,
            "question_entry": question,
            "reply": {"repeated": once.answer["repeated"], "scheduled": continuation},
            "reply_again": {
                "repeated": again.answer["repeated"],
                "scheduled": again.answer["scheduled"],
            },
            "reply_to_the_overtaken_question": {"scheduled": overtaken.answer["scheduled"]},
            "jobs_of_the_session": jobs,
            "parts": [part._asdict() for part in found],
        },
    )


# --- case 3 ---


def test_case_3_accepted_work_is_recovered_after_the_page_closes_and_following_changes_nothing(
    tmp_path, scratch_durables, monkeypatch, real_client, kept, matsya_state
):
    """Amendment 06 §5 case 3 (§2 items 17 and 18). On the stand-in: a job
    whose client exits with the warning that the service used its own key
    keeps its accepted identifier; a turn whose wait ends, as at the
    adapter's limit, keeps its record; a turn whose answer is lost in
    transport keeps a record with no identifier. After the module is loaded
    again, as when the page is opened again, recovery reads the job and the
    turn by their identifiers before it offers anything, writes nothing,
    and offers a retry for the lost turn alone, which the service answers
    with the turn it already holds. Following and the column's recovery of
    jobs neither cancel nor download. Then, on the local service through
    the client, a cancellation of a job that had ended is refused with the
    service's sentence and the job's actual outcome stands, and a queued
    job's cancellation takes effect."""
    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    folder = model.open_folder(scratch_durables)
    session = connected(folder)
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_WARN", "1")
    job = matsya_work.submit(folder, prepared.path, session)
    monkeypatch.delenv("BELLMAN_WORKBENCH_MATSYA_STUB_WARN")
    assert (job.record["accepted"], job.record["exit_code"]) == ("job-1", 1)
    credential_warning = job.record["warning"]
    assert credential_warning == (
        "Error: the service at http://127.0.0.1:8710 accepted job job-1 under its own "
        "Anthropic key, not yours."
    )
    waited = matsya_work.start_turn(folder, session, "What does tenure choose?")
    assert waited.record["accepted"] == "turn-1"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOST", "1")
    lost = matsya_work.start_turn(folder, session, "And what does the keeper choose?")
    monkeypatch.delenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOST")
    assert (lost.record["accepted"], lost.record["exit_code"]) == (None, 1)
    transport_warning = lost.record["warning"]

    held = json.loads(Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"]).read_text("utf-8"))
    stub_job({**held["jobs"]["job-1"], "state": "running"})
    stub_turn(
        {
            **held["turns"]["turn-1"],
            "state": "finished",
            "record": {
                "result": {
                    "status": "answered",
                    "answer": "Whether to keep the house or to adjust it.",
                    "citations": [{"path": TENURE, "location": {"line": 1}}],
                }
            },
        }
    )
    before = every_file(folder.root)
    log.unlink()

    reopened = importlib.reload(matsya_work)
    recovered = reopened.recover(folder, session)
    assert [
        (item.record["kind"], item.record["accepted"], item.state, item.retry)
        for item in recovered
    ] == [
        ("job", "job-1", "running", False),
        ("turn", "turn-1", "finished", False),
        ("turn", None, None, True),
    ]
    assert matsya_client.read_turn(recovered[1].answer).answer == (
        "Whether to keep the house or to adjust it."
    )
    assert sorted(calls_of(log)) == sorted(
        [
            ["job", "status", "job-1", "--json"],
            ["turn", "status", session.id, "turn-1", "--json"],
        ]
    )
    assert every_file(folder.root) == before
    retried = reopened.retry(folder, recovered[2].record)
    assert (retried.record["delivery"], retried.record["accepted"]) == (
        lost.record["delivery"],
        "turn-2",
    )
    turns = json.loads(Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"]).read_text("utf-8"))
    assert sorted(turns["turns"]) == ["turn-1", "turn-2"]

    log.unlink()
    following = every_file(folder.root)
    assert reopened.follow(job.record)["state"] == "running"
    matsya_window.recover_jobs(folder)
    assert "job-1" in matsya_window.jobs.value
    assert [exchange.job for exchange in matsya_window.exchanges.value] == ["job-1"]
    assert every_file(folder.root) == following
    assert not (folder.root / model.OUTPUT_FOLDER).exists()
    followed = calls_of(log)
    assert followed and all(call[:2] == ["job", "status"] for call in followed), followed

    with local_service(tmp_path / "service") as (address, processor):
        real_client(address, AUTHOR_TOKEN)
        finished = post(
            address,
            AUTHOR_TOKEN,
            "/v1/model-iterations",
            {"source": {"kind": "description", "text": "A household saves."}, "target": "stage"},
        )["id"]
        assert ended_by_identifier(finished)["state"] == "needs_input"
        too_late = matsya_client.run(["job", "cancel", finished, "--json"])
        assert (too_late.code, too_late.warning) == (
            1,
            "Error: The service refused the request (409): The job has ended.",
        )
        outcome = matsya_client.run(["job", "status", finished, "--json"]).answer
        assert outcome["state"] == "needs_input"

        for _ in range(2):
            post(
                address,
                AUTHOR_TOKEN,
                "/v1/model-iterations",
                {"source": {"kind": "description", "text": HOLD}, "target": "stage"},
            )
        assert processor.holding.acquire(timeout=10) and processor.holding.acquire(timeout=10)
        queued = post(
            address,
            AUTHOR_TOKEN,
            "/v1/model-iterations",
            {"source": {"kind": "description", "text": "A household borrows."}, "target": "stage"},
        )["id"]
        cancelled = matsya_client.run(["job", "cancel", queued, "--json"])
        assert cancelled.code == 0 and cancelled.answer["state"] == "cancelled"
        processor.release.set()
        assert ended_by_identifier(queued)["state"] == "cancelled"
        assert len(processor.sources) == 1
    kept(
        "case-3",
        {"durables": folder.root},
        {
            "credential_warning": credential_warning,
            "transport_warning": transport_warning,
            "recovered": [
                (item.record["kind"], item.record["accepted"], item.state, item.retry)
                for item in recovered
            ],
            "retried": retried.record,
            "following_calls": followed,
            "cancellation_of_an_ended_job": {
                "exit_status": too_late.code,
                "standard_error": too_late.warning,
                "outcome": outcome["state"],
            },
            "cancellation_of_a_queued_job": cancelled.answer["state"],
        },
        log,
    )


# --- case 4 ---


def test_case_4_a_second_account_is_refused_the_author_s_session_and_keeps_local_inspection(
    tmp_path, scratch_durables, real_client, kept
):
    """Amendment 06 §5 case 4 (§2 item 19), on the local service through the
    client. The author connects the folder, submits a job and asks a
    question; a colleague receives a copy of the folder with its
    `.bellman-matsya/` records and opens it under another Matsya token. The
    folder's project file names the author's session, but the colleague's
    question is refused with the service's sentence, and the discussion and
    the download of the author's job with the adapter's sentence, which says
    that the job belongs to another account's session and names `session
    new` (decision SG5-18); the author's records
    are not listed for the colleague's service and stay byte-identical; the
    folder's model is constructed and its records read without the service;
    the client refuses to connect the folder again, since it is already a
    project, and the colleague's own session is made by the client."""
    author = model.open_folder(scratch_durables)
    with local_service(tmp_path / "service") as (address, processor):
        real_client(address, AUTHOR_TOKEN)
        project, refusal = matsya_work.connect(author)
        assert refusal is None
        session = matsya_work.connected_session(author)
        job = matsya_work.submit(
            author, matsya_work.prepare(author, DURABLES, "recipe", session, 1).path, session
        )
        assert ended_job(job.record)["state"] == "needs_input"
        author_job = job.record["accepted"]

        colleague_root = tmp_path / "colleague" / author.root.name
        shutil.copytree(author.root, colleague_root)
        colleague = model.open_folder(colleague_root)
        records_before = every_file(colleague_root / ".bellman-matsya")
        real_client(address, COLLEAGUE_TOKEN)
        theirs = matsya_work.connected_session(colleague)
        assert theirs.id == session.id and theirs.service != session.service
        assert matsya_work.records(colleague, theirs) == []

        asked = matsya_work.start_turn(colleague, theirs, "What does tenure choose?")
        assert (asked.record["accepted"], asked.record["exit_code"]) == (None, 1)
        assert asked.record["warning"] == (
            "Error: The service refused the request (404): Session not found."
        )
        discussed = matsya_work.discuss(theirs, author_job)
        another = f"job {author_job} belongs to a session of another account, or to none"
        session_new = "start a session of your own with bellman-matsya session new"
        assert discussed.refusal == f"{another}, so it is not discussed; {session_new}"
        downloaded = matsya_work.download(colleague, theirs, author_job)
        assert downloaded.refusal == f"{another}, so it is not downloaded; {session_new}"
        assert downloaded.path is None and not (colleague_root / model.OUTPUT_FOLDER).exists()
        status = matsya_client.run(["job", "status", author_job, "--json"])
        assert (status.code, status.warning) == (
            1,
            "Error: The service refused the request (404): Model iteration not found.",
        )
        after = every_file(colleague_root / ".bellman-matsya")
        assert {path: after[path] for path in records_before} == records_before

        shown = trellis.show_trellis(colleague, DURABLES)
        assert shown.refusal is None
        prepared_records = sorted((colleague_root / matsya_work.PREPARED_FOLDER).glob("*.json"))
        assert prepared_records and all(
            json.loads(path.read_text(encoding="utf-8")) for path in prepared_records
        )

        reconnected, sentence = matsya_work.connect(colleague)
        assert reconnected is None
        assert sentence == (
            f"Error: The folder {colleague_root.resolve()} is already a Matsya project, of "
            f"session {session.id}; bellman-matsya project status shows it."
        )
        own = matsya_client.run(["session", "new", "durables", "--json"])
        assert own.code == 0 and own.answer["id"] != session.id
    kept(
        "case-4",
        {"author": author.root, "colleague": colleague_root},
        {
            "colleague_question": asked.record,
            "colleague_discussion": discussed.refusal,
            "colleague_download": downloaded.refusal,
            "colleague_job_status": status.warning,
            "author_records_unchanged": True,
            "local_construction_refusal": shown.refusal,
            "colleague_connection": sentence,
            "colleague_own_session": own.answer["id"],
        },
    )


# --- case 5 ---


def test_case_5_a_saved_copy_is_its_own_model_and_only_the_reviewed_files_are_adopted(
    tmp_path, scratch_durables, kept, matsya_state
):
    """Amendment 06 §5 case 5 (§2 items 20 to 24; §2 item 6, the citations).
    On the stand-in: a saved copy whose calibration lowers τ to 0.08 is
    constructed under its own root, with its own files, and the service's
    comparison stands apart; a citation of an equation of the folder's
    tenure stage opens that file at its line, a citation of a returned file
    opens the saved copy and an invented path is unavailable; a replacement
    over unsaved editor text is refused and writes nothing; the variant
    import leaves every file of the baseline byte-identical; a deliberate
    full-disk failure of the second of two writes stops the adoption with
    its record, and the restore returns the originals; and an adoption of
    the reviewed iteration writes its text, not that of a newer iteration
    downloaded during the review."""
    folder = model.open_folder(scratch_durables)
    session = session_of(folder)
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    number = int(matsya_work.submit(folder, prepared.path, session).record["accepted"][4:])

    def downloaded(cycles: int, edits: dict) -> str:
        job = returned_job(folder.root, session.id, number, cycles, edits)
        copy = matsya_work.download(folder, session, job["id"])
        assert copy.written, copy.refusal
        return copy.path

    copy = downloaded(2, {CALIBRATION: (HIGH, LOW)})
    inspected = returned.inspect(folder, copy)
    assert inspected.folder.root == folder.root / copy and inspected.source == DURABLES
    assert all(path.startswith(str(folder.root / copy) + os.sep) for path in inspected.shown.files)
    adjuster = inspected.shown.syntactic["periods"][1]["stages"]["adjuster_cons"]
    assert adjuster["calibration"]["τ"] == 0.08 and inspected.missing == ()
    assert inspected.service["result"]["comparison"] == {"converged": True, "differences": []}

    lines = (folder.root / TENURE).read_text(encoding="utf-8").splitlines()
    equation = next(n for n, line in enumerate(lines, 1) if " = " in line and "~" not in line)
    cited = matsya_window.resolve(folder.root, {"path": TENURE, "location": {"line": equation}})
    assert cited == matsya_window.Citation(matsya_window.FILE, path=TENURE, line=equation)
    returned_file = matsya_window.resolve(
        folder.root,
        {
            "identity": {"source": "job"},
            "location": {"job": f"job-{number}", "output": "calibration/durables.yml"},
        },
    )
    assert returned_file == matsya_window.Citation(
        matsya_window.COPY, path=f"{copy}/{CALIBRATION}"
    )
    invented = matsya_window.resolve(folder.root, {"path": "docs/overview/03-language.md"})
    assert invented.kind == matsya_window.UNAVAILABLE

    disk = (folder.root / CALIBRATION).read_text(encoding="utf-8")
    buffers = {CALIBRATION: matsya_work.Buffer(disk + "# typed, not saved\n", sha256(disk))}
    unsaved = (
        f"{CALIBRATION} holds unsaved changes in the editor; save or discard them before the "
        "adoption"
    )
    shown = returned.plan(folder, copy, [CALIBRATION], buffers=buffers)
    assert shown.refusals == (unsaved,)
    before = every_file(folder.root)
    refused = returned.adopt(folder, returned.plan(folder, copy, [CALIBRATION]), buffers=buffers)
    assert (refused.id, refused.changed, refused.refusals) == (None, (), (unsaved,))
    assert every_file(folder.root) == before

    imported = returned.import_variant(folder, copy, "low-cost", "spec.yml")
    assert imported.refusals == ()
    after = every_file(folder.root)
    assert all(after[path] == before[path] for path in before)
    assert set(after) - set(before) == set(imported.files)
    variant = trellis.show_trellis(
        folder, recipe.Source("recipe", "declaration/spec.low-cost.yml")
    )
    assert (
        variant.shown.syntactic["periods"][1]["stages"]["adjuster_cons"]["calibration"]["τ"]
        == 0.08
    )

    two = downloaded(3, {CALIBRATION: (HIGH, LOW), SETTINGS: ("n_a:", "n_a: 301 #")})
    planned = returned.plan(folder, two, [CALIBRATION, SETTINGS])
    assert planned.refusals == ()
    originals = {path: (folder.root / path).read_bytes() for path in (CALIBRATION, SETTINGS)}

    def full_disk(at, relpath, text, expected):
        if relpath == SETTINGS:
            raise OSError(errno.ENOSPC, "No space left on device", relpath)
        return model.save_file(at, relpath, text, expected)

    stopped = returned.adopt(folder, planned, write=full_disk)
    assert stopped.changed == (CALIBRATION,) and stopped.record["state"] == "stopped"
    assert [entry["outcome"] for entry in stopped.record["files"]] == ["written", "failed"]
    restored = returned.restore(folder, stopped.id)
    assert (restored.changed, restored.refusals, restored.record["state"]) == (
        (CALIBRATION,),
        (),
        "restored",
    )
    assert {path: (folder.root / path).read_bytes() for path in originals} == originals

    reviewed = returned.plan(folder, copy, [CALIBRATION])
    newer = downloaded(4, {CALIBRATION: (HIGH, LOWER)})
    adopted = returned.adopt(folder, reviewed)
    assert adopted.changed == (CALIBRATION,) and adopted.record["copy"] == copy
    written = (folder.root / CALIBRATION).read_text(encoding="utf-8")
    assert LOW in written and LOWER not in written
    kept(
        "case-5",
        {"durables": folder.root},
        {
            "copy": copy,
            "copy_root": str(inspected.folder.root.relative_to(folder.root)),
            "copy_tau": 0.08,
            "service_comparison": inspected.service["result"]["comparison"],
            "citations": {
                "equation": cited._asdict(),
                "returned_file": returned_file._asdict(),
                "invented": invented._asdict(),
            },
            "unsaved_refusal": unsaved,
            "variant_files": imported.files,
            "baseline_unchanged": True,
            "late_failure": stopped.refusals,
            "restored": restored.record["state"],
            "reviewed_copy": copy,
            "newer_copy": newer,
            "adopted_from": adopted.record["copy"],
        },
    )


# --- case 6 ---


def _texts_of(rendered, class_: str) -> list:
    """The texts of the rendered elements of the class `class_`, in order."""
    found = rendered.find(ipyvue.Html, class_=class_)
    return ["".join(str(child) for child in widget.children) for widget in found.widgets]


def _click(rendered, class_: str) -> None:
    """Clicks the one rendered button of the class `class_`."""
    found = rendered.find(ipyvue.Html, tag="button", class_=class_)
    found.assert_single()
    found.widget.fire_event("click", {})


def _chips(rendered) -> dict:
    """The composer's chips, each kind's value and state words."""
    found = rendered.find(ipyvue.Html, tag="li", class_="bl-matsya-chip bl-code-small")
    return {
        widget.attributes["data-kind"]: [
            "".join(map(str, child.children))
            for child in widget.children
            if hasattr(child, "children")
            and child.children
            and all(isinstance(part, str) for part in child.children)
        ]
        for widget in found.widgets
    }


def test_case_6_each_request_shows_what_it_sends_and_where_before_it_is_sent(
    tmp_path, scratch_durables, monkeypatch, real_client, kept, matsya_state
):
    """Amendment 06 §5 case 6 (§2 items 6, 9 and 10). The column drawn in
    this process with the stand-in. The connection shows the folder's name,
    its `economics.md` and the service before the click, and `project init`
    then sends them. A search shows its collection and the service, and the
    client receives the field's text and that collection alone. A question
    shows the source, the session and the service with its configuration,
    and the client receives that session and the question's text alone. A
    build shows its level, its source with the number of files and the
    service, `Files` lists each file with the start of its
    fingerprint, and the submission sends exactly those texts. The chips
    name the configuration `default` and no key source; the client's
    `configuration effective`, run against the local service, reports the
    address, the configuration and the key's source, `service` without a
    personal key and `client` with one, and prints neither the token nor
    the key."""
    from bellman_workbench import app

    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    folder = model.open_folder(scratch_durables)
    requests = folder.root / matsya_work.REQUESTS_FOLDER
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_REQUESTS", str(requests))
    opened: list = []
    actions = matsya_window.Actions(
        folder=lambda: folder,
        open_file=lambda path, line: opened.append((path, line)),
        open_copy=lambda path: opened.append((path, None)),
        buffers=lambda: {},
        open_commit=lambda record: None,
        source=lambda: DURABLES,
    )
    held = (app.tab_folder.value, app.source.value)
    app.tab_folder.value = folder
    app.source.value = DURABLES

    @solara.component
    def Column():
        return matsya_window.MatsyaWindow(
            app._session(),
            app.Field,
            app.ToolbarButton,
            app.TextButton,
            app.matsya_context(),
            actions,
        )

    _, rendered = solara.render(Column(), handle_error=False)
    observed: dict = {}
    try:
        connection = _texts_of(rendered, "bl-matsya-connect-sent bl-code-small")
        assert connection == ["durables · economics.md · 127.0.0.1:8710"]
        assert _chips(rendered)["session"] == ["not connected"]
        _click(rendered, "bl-text-button bl-matsya-connect-button")
        assert calls_of(log) == [["project", "init", str(folder.root), "--json"]]
        session = matsya_work.connected_session(folder)
        wait_until(lambda: "durables" in _chips(rendered)["session"], 10.0, "the session's chip")
        chips = _chips(rendered)
        assert chips["source"] == ["spec.yml", "saved"]
        assert chips["service"] == ["127.0.0.1:8710", "default"]
        observed["connection"] = {"shown": connection, "sent": calls_of(log)[0], "chips": chips}

        log.unlink()
        matsya_state.set_kind(matsya_window.SEARCH)
        matsya_state.set_collection("literature")
        matsya_state.send("Euler equation with a borrowing constraint")
        wait_until(lambda: matsya_state.exchanges.value[-1].answer is not None, 20.0, "the search")
        assert calls_of(log) == [
            [
                "search",
                "--json",
                "--collections",
                "literature",
                "--",
                "Euler equation with a borrowing constraint",
            ]
        ]
        observed["search"] = {
            "collection": "literature",
            "service": chips["service"],
            "sent": calls_of(log)[0],
        }

        log.unlink()
        matsya_state.set_kind(matsya_window.ASK)
        matsya_state.send("What does the tenure stage choose?")
        wait_until(lambda: requests.is_dir() and any(requests.glob("*.json")), 20.0, "the record")
        (path,) = [
            found
            for found in requests.glob("*.json")
            if json.loads(found.read_text(encoding="utf-8"))["kind"] == "turn"
        ]
        wait_until(
            lambda: json.loads(path.read_text(encoding="utf-8"))["accepted"],
            20.0,
            "the turn accepted",
        )
        turn_record = json.loads(path.read_text(encoding="utf-8"))
        stub_turn(
            {
                "id": turn_record["accepted"],
                "session": session.id,
                "state": "finished",
                "record": {
                    "result": {
                        "status": "answered",
                        "answer": "Whether to keep or to adjust the house.",
                        "citations": [{"path": TENURE, "location": {"line": 1}}],
                    }
                },
            }
        )
        wait_until(lambda: matsya_state.exchanges.value[-1].answer is not None, 20.0, "the answer")
        asked = calls_of(log)[0]
        assert asked == [
            "ask",
            session.id,
            "--no-wait",
            "--delivery-id",
            path.stem,
            "--json",
            "--",
            "What does the tenure stage choose?",
        ]
        assert (turn_record["session"], turn_record["question"]) == (
            session.id,
            "What does the tenure stage choose?",
        )
        observed["question"] = {"chips": _chips(rendered), "sent": asked, "record": turn_record}

        log.unlink()
        matsya_state.set_kind(matsya_window.BUILD)
        matsya_state.set_target("Recipe")
        matsya_state.send("Lower the housing cost τ to 0.08")
        wait_until(
            lambda: (
                matsya_state.builds.value.get(1, matsya_window.BuildView()).prepared
                or matsya_state.builds.value.get(2, matsya_window.BuildView()).prepared
            ),
            20.0,
            "the build prepared",
        )
        number = max(matsya_state.builds.value)
        record = matsya_state.builds.value[number].prepared.record
        rendered.find(
            ipyvue.Html, tag="button", class_="bl-text-button bl-matsya-files-sent"
        ).wait_for(timeout=10)
        assert f"{matsya_window.BUILD} · Recipe" in _texts_of(rendered, "bl-small")
        what = _texts_of(rendered, "bl-matsya-build-what bl-code-small")
        assert what == [f"spec.yml · {len(record['files'])} files", "127.0.0.1:8710 · default"]
        assert [call[:2] for call in calls_of(log)] == [["session", "add"]]
        _click(rendered, "bl-text-button bl-matsya-files-sent")
        listed = rendered.find(ipyvue.Html, tag="li", class_="bl-code-small").wait_for(timeout=10)
        files_shown = [
            "".join(map(str, widget.children))
            for widget in listed.widgets
            if " · " in "".join(map(str, widget.children))
            and "".join(map(str, widget.children)).startswith("declaration/")
        ]
        assert files_shown == [
            f"{entry['path']} · {entry['sha256'][:12]}" for entry in record["files"]
        ]
        _click(rendered, "bl-text-button bl-matsya-submit")
        (sent,) = [entry["submitted"] for entry in stub_calls(log) if "submitted" in entry]
        inputs = json.loads((folder.root / record["inputs"]).read_text(encoding="utf-8"))
        assert sent == {
            name: sha256(text) for name, text in inputs["starting_declaration"].items()
        }
        assert {entry["name"]: entry["sha256"] for entry in record["files"]} == sent
        observed["build"] = {"shown": what, "files_sent": files_shown, "submitted": sent}
    finally:
        rendered.close()
        app.tab_folder.value, app.source.value = held

    with local_service(tmp_path / "service") as (address, processor):
        real_client(address, AUTHOR_TOKEN)
        plain = matsya_client.run(["configuration", "effective", "--json"])
        assert plain.code == 0
        assert (plain.answer["server"], plain.answer["configuration_source"]) == (
            address,
            "the service's default",
        )
        assert (plain.answer["key_source"], plain.answer["credential"]) == (None, "service")
        monkeypatch.setenv("BELLMAN_MATSYA_ANTHROPIC_KEY", FIXTURE_KEY)
        keyed = matsya_client.run(["configuration", "effective", "--json"])
        assert (keyed.answer["key_source"], keyed.answer["credential"]) == (
            "BELLMAN_MATSYA_ANTHROPIC_KEY",
            "client",
        )
        printed = json.dumps([plain.answer, keyed.answer]) + plain.warning + keyed.warning
        assert AUTHOR_TOKEN not in printed and FIXTURE_KEY not in printed
    observed["configuration_effective"] = {
        "without_a_key": plain.answer,
        "with_a_key": keyed.answer,
    }
    kept("case-6", {"durables": folder.root}, observed, log)


# --- the words the no-slop review changed ---


def test_the_words_the_no_slop_review_changed_stand_on_the_page(
    scratch_durables, monkeypatch, matsya_state
):
    """The page texts that the no-slop review of unit G5 changed. A client's
    sentence is shown as its first line without the word `Error:` the
    client prints before a refusal, at the line's start and after the colon
    of an adapter's sentence that quotes it, so that a turn whose answer the
    transport lost answers the client's sentence alone. The list of a
    build's files is `Files`, before the submission as after it. The job
    discussed is named `job <n>`, as its message names it, and by its
    identifier where no number is known. A job that holds no result yet is
    not downloaded, with that sentence."""
    assert (
        matsya_window.client_sentence(
            "Error: The service refused the request (404): Session not found.\nCancel it with: x"
        )
        == "The service refused the request (404): Session not found."
    )
    assert matsya_window.client_sentence(
        "the client did not write the files of job job-3: Error: the connection closed after "
        "economics.md was written"
    ) == (
        "the client did not write the files of job job-3: the connection closed after "
        "economics.md was written"
    )
    assert matsya_window.FILES_SENT == "Files"
    matsya_window.jobs.value = {"0123abcd": matsya_window.JobView(job={"label": {"number": 3}})}
    assert (matsya_window.job_name("0123abcd"), matsya_window.job_name("4567ef")) == (
        "job 3",
        "4567ef",
    )

    folder = model.open_folder(scratch_durables)
    session = connected(folder)
    actions = matsya_window.Actions(
        folder=lambda: folder,
        open_file=lambda path, line: None,
        open_copy=lambda path: None,
        buffers=lambda: {},
        open_commit=lambda record: None,
        source=lambda: DURABLES,
    )
    matsya_window.exchanges.value = (matsya_window.Exchange("What does tenure choose?"),)
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOST", "1")
    matsya_window.answer_last("a conversation of unit M", actions)
    assert matsya_window.exchanges.value[0].answer == (
        "the connection closed before the service answered"
    )
    stub_job({"id": "job-9", "state": "running", "session": session.id, "label": {"number": 9}})
    assert matsya_work.download(folder, session, "job-9").refusal == (
        "job job-9 holds no result yet, so it is not downloaded"
    )


# --- the resolutions of SG5-11 and SG5-15 ---


def test_a_job_whose_answer_was_lost_is_recovered_by_its_delivery_identifier(
    tmp_path, scratch_durables, monkeypatch
):
    """Decision SG5-16. A prepared submission carries its request's
    delivery identifier, the record standing before the client runs. When
    the client's answer is lost, recovery offers a retry for the job, and
    the retry sends the same identifier, which the service answers with the
    job it already holds: the service holds one job, and the record names
    it."""
    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    folder = model.open_folder(scratch_durables)
    session = connected(folder)
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOST", "1")
    lost = matsya_work.submit(folder, prepared.path, session)
    monkeypatch.delenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOST")
    assert lost.record["accepted"] is None
    (sent,) = [call for call in calls_of(log) if call[:2] == ["job", "submit-prepared"]]
    assert sent[3:5] == ["--delivery-id", lost.record["delivery"]]
    (submitted,) = [entry for entry in stub_calls(log) if "submitted" in entry]
    assert submitted["requests_before"] == [f"{lost.record['delivery']}.json"]
    [recovered] = matsya_work.recover(folder, session)
    assert (recovered.record["kind"], recovered.retry) == ("job", True)
    again = matsya_work.retry(folder, recovered.record)
    assert (again.record["delivery"], again.record["accepted"]) == (
        lost.record["delivery"],
        "job-1",
    )
    held = json.loads(Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"]).read_text("utf-8"))
    assert sorted(held["jobs"]) == ["job-1"]


def test_the_client_refuses_a_delivery_identifier_over_64_characters_before_any_request(
    tmp_path, real_client
):
    """Decision SG5-17. The client's `job submit-prepared --delivery-id`
    with 65 characters is refused before any request, with one sentence and
    exit status 2 and no traceback; the client's address is one at which no
    service listens."""
    real_client("http://127.0.0.1:9", "msy_" + "0" * 32)
    prepared = tmp_path / "prepared.json"
    prepared.write_text(
        json.dumps({"session": "0" * 32, "reviewed_through": 1, "target": "stage",
                    "starting_declaration": {"example.bl": "@stage: example\n"},
                    "paths": {"example.bl": "declaration/stages/example/example.bl"}}),
        encoding="utf-8",
    )
    refused = matsya_client.run(
        ["job", "submit-prepared", str(prepared), "--delivery-id", "d" * 65, "--json"]
    )
    assert refused.code == 2
    assert refused.warning.splitlines()[-1] == (
        "bellman-matsya: error: --delivery-id is a string of 1 to 64 characters"
    )
    assert "Traceback" not in refused.warning


def test_a_reply_to_a_question_a_later_entry_overtook_is_historical_and_is_not_sent(
    tmp_path, scratch_durables, real_client
):
    """Decision SG5-19 (SG5-15; amendment 06 §2 item 16), on the local
    service through the client. A job reviewed through the session's last
    entry ends current with its question. Once a later plain entry follows
    the question, the adapter's reply compares the session's revision with
    the revision the job read, marks the question historical and sends
    nothing, and the service starts no continuation. A reply to the
    question of a job that is current is sent with its delivery identifier,
    its record written first, and starts one continuation."""
    folder = model.open_folder(scratch_durables)
    with local_service(tmp_path / "service") as (address, processor):
        real_client(address, AUTHOR_TOKEN)
        matsya_work.connect(folder)
        session = matsya_work.connected_session(folder)
        first = matsya_work.submit(
            folder, matsya_work.prepare(folder, DURABLES, "recipe", session, 1).path, session
        )
        first_job = first.record["accepted"]
        assert ended_job(first.record)["current"] is True
        [question] = [e for e in session_shown(session.id)["entries"] if e["kind"] == "question"]
        assert matsya_work.add_entry(folder, session, "Let the wage grow with age.").record[
            "accepted"
        ] == "3"
        historical = matsya_work.reply(
            folder, session, first_job, question["number"], "An AR(1) process."
        )
        assert (historical.work, historical.historical) == (None, True)
        assert historical.refusal == (
            f"the question of entry {question['number']} is historical: the session's text has "
            f"moved from version 1 to version 3 since job {first_job} read it; submit the build "
            "again to act on it"
        )
        assert [job["id"] for job in session_shown(session.id)["jobs"]] == [first_job]

        second = matsya_work.submit(
            folder, matsya_work.prepare(folder, DURABLES, "recipe", session, 3).path, session
        )
        assert ended_job(second.record)["current"] is True
        current = [e for e in session_shown(session.id)["entries"] if e["kind"] == "question"][-1]
        sent = matsya_work.reply(
            folder, session, second.record["accepted"], current["number"], "An AR(1) process."
        )
        assert (sent.historical, sent.refusal) == (False, None)
        record = json.loads((folder.root / sent.work.path).read_text(encoding="utf-8"))
        assert record == sent.work.record
        assert (record["kind"], record["replies_to"], record["exit_code"]) == (
            "reply",
            current["number"],
            0,
        )
        continuation = record["scheduled"]
        assert continuation is not None
        assert [job["id"] for job in session_shown(session.id)["jobs"]] == [
            first_job,
            second.record["accepted"],
            continuation,
        ]
