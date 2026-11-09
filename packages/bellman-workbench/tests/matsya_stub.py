"""Stand-in for the Bellman Matsya command used by Workbench tests.

It implements the two JSON commands the Workbench's question calls, and,
for unit G2 of specification 0.6, the commands `matsya_work.py` calls. The
session identifier differs from its name, so tests detect an adapter that
sends the folder digest in place of the identifier allocated by the
service.

The service of the unit G2 commands is the JSON file that
BELLMAN_WORKBENCH_MATSYA_STUB_STATE names, `{"jobs", "turns",
"deliveries", "selected"}`: the jobs and the turns by their identifiers,
the turn each delivery identifier names, and the selected job of each
session. A test writes a job into it to give the service a job of its own.
BELLMAN_WORKBENCH_MATSYA_STUB_FILES_FAIL makes `job files` stop with
status 1 after its first file. Three variables choose how a command that
starts work ends:
BELLMAN_WORKBENCH_MATSYA_STUB_WARN, the answer printed and then the
client's warning that the service used its own key, with status 1;
BELLMAN_WORKBENCH_MATSYA_STUB_LOST, the work recorded and nothing printed,
with status 1, as when the answer is lost; and neither, the answer with
status 0. The commands of unit G1 are written as its client defines them
on the branch spec06/matsya-service: `job submit-prepared <file>`, which
reads a prepared-inputs file with the fields PREPARED_FIELDS alone, `ask
--no-wait --delivery-id` and `turn status` (decision SG2-3).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

WAIT_SECONDS = 5.0
PASSAGES = (
    "docs/overview/03-language.md",
    "docs/bellman-calculus/04-fields, functions and types.md",
)
# the fields of a prepared-inputs file, as `read_prepared_inputs` of the
# client of unit G1 admits them, and the form of a session's identifier
PREPARED_FIELDS = (
    "session", "reviewed_through", "target", "starting_declaration", "paths",
    "configuration_id", "max_cycles", "force", "formulation", "model_key", "source_cluster",
)
SESSION_ID = re.compile(r"[0-9a-f]{32}")
# the configuration ID the stand-in's service pins to new work
CONFIGURATION = "c0ffee" + "0" * 58
WARNING = (
    "Error: the service at http://127.0.0.1:8710 accepted {kind} {id} under its own Anthropic "
    "key, not yours."
)


def _log(entry) -> None:
    """Appends one JSON line to the log a test names."""
    if log := os.environ.get("BELLMAN_WORKBENCH_MATSYA_STUB_LOG"):
        with Path(log).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _service() -> dict:
    """The stand-in service's state, empty where its file does not exist."""
    path = Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"])
    if not path.is_file():
        return {"jobs": {}, "turns": {}, "deliveries": {}, "selected": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _keep(state: dict) -> None:
    """Writes the stand-in service's state."""
    path = Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"])
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def _started(answer: dict, kind: str, work: dict) -> int:
    """Prints the answer of a command that started the work `work` and its
    status, as the variables of the module's docstring choose."""
    if os.environ.get("BELLMAN_WORKBENCH_MATSYA_STUB_LOST"):
        print("Error: the connection closed before the service answered", file=sys.stderr)
        return 1
    print(json.dumps(answer, ensure_ascii=False))
    if os.environ.get("BELLMAN_WORKBENCH_MATSYA_STUB_WARN"):
        print(WARNING.format(kind=kind, id=work["id"]), file=sys.stderr)
        return 1
    return 0


def _submit_prepared(path: str, delivery: str | None = None) -> int:
    """`job submit-prepared <file> [--delivery-id <id>] --json`: a new job of
    the file's session, logged with the digest of each file of its starting
    declaration and the request records that stood beside the file when the
    command began, or, for a delivery identifier the service already holds,
    the job it names, with `repeated` true (unit G5); a file with a field
    the client does not admit, or without a session, a reviewed entry or a
    target, is refused with status 1."""
    prepared = json.loads(Path(path).read_text(encoding="utf-8"))
    unknown = sorted(set(prepared) - set(PREPARED_FIELDS))
    if unknown:
        print(f"Error: {path} holds the field {unknown[0]}, which a prepared-inputs file does "
              "not hold.", file=sys.stderr)
        return 1
    if not SESSION_ID.fullmatch(str(prepared.get("session"))) or not isinstance(
        prepared.get("reviewed_through"), int
    ) or "target" not in prepared:
        print(f"Error: {path} names no session, reviewed entry or target.", file=sys.stderr)
        return 1
    requests = Path(os.environ.get("BELLMAN_WORKBENCH_MATSYA_STUB_REQUESTS",
                                   str(Path(path).parent.parent / "requests")))
    _log(
        {
            "submitted": {
                name: hashlib.sha256(text.encode("utf-8")).hexdigest()
                for name, text in prepared.get("starting_declaration", {}).items()
            },
            "requests_before": sorted(p.name for p in requests.glob("*.json")),
        }
    )
    state = _service()
    held = state.setdefault("job_deliveries", {}).get(delivery) if delivery else None
    if held is not None:
        answer = {"session": prepared["session"], "job": {**state["jobs"][held], "repeated": True}}
        return _started(answer, "job", state["jobs"][held])
    number = len(state["jobs"]) + 1
    job = {
        "id": f"job-{number}",
        "state": "queued",
        "session": prepared["session"],
        "reviewed_through": prepared["reviewed_through"],
        "label": {"number": number, "state": "queued"},
        "configuration_id": CONFIGURATION,
        "credential_source": "service",
    }
    state["jobs"][job["id"]] = job
    if delivery:
        state["job_deliveries"][delivery] = job["id"]
    _keep(state)
    files = prepared.get("starting_declaration", {})
    answer = {
        "session": prepared["session"],
        "reviewed_through": prepared["reviewed_through"],
        "target": prepared["target"],
        "files": [
            {"name": name, "path": prepared.get("paths", {}).get(name),
             "sha256": hashlib.sha256(files[name].encode("utf-8")).hexdigest()}
            for name in sorted(files)
        ],
        "capabilities": ["capture_at_acceptance"],
        "job": job,
    }
    return _started(answer, "job", job)


def _ask_without_waiting(session_id: str, delivery: str, question: str) -> int:
    """`ask <session> --no-wait --delivery-id <id> --json -- <question>`:
    a new queued turn, or the turn the delivery identifier already names.
    Where BELLMAN_WORKBENCH_MATSYA_STUB_REQUESTS names a folder of request
    records, the names of the records that stood there when the command
    began are logged (unit G4)."""
    if requests := os.environ.get("BELLMAN_WORKBENCH_MATSYA_STUB_REQUESTS"):
        _log({"turn_requests_before": sorted(p.name for p in Path(requests).glob("*.json"))})
    state = _service()
    held = state["deliveries"].get(delivery)
    if held is None:
        held = f"turn-{len(state['turns']) + 1}"
        entries = state.setdefault("entries", {}).setdefault(session_id, [])
        number = len(entries) + 1
        entries.append({"number": number, "kind": "user", "text": question})
        state["turns"][held] = {
            "id": held,
            "session": session_id,
            "state": "queued",
            "question": number,
            "configuration_id": CONFIGURATION,
        }
        state["deliveries"][delivery] = held
        _keep(state)
    return _started(state["turns"][held], "turn", state["turns"][held])


def _turn_status(session_id: str, turn_id: str) -> int:
    """`turn status <session> <turn> --json`: the turn, refused where the
    session holds no such turn."""
    turn = _service()["turns"].get(turn_id)
    if turn is None or turn["session"] != session_id:
        print(f"Error: session {session_id} holds no turn {turn_id}", file=sys.stderr)
        return 1
    print(json.dumps(turn, ensure_ascii=False))
    return 0


def _job_status(job_id: str) -> int:
    """`job status <job> --json`: the job, refused where the service holds
    none of that identifier."""
    job = _service()["jobs"].get(job_id)
    if job is None:
        print(f"Error: the service holds no job {job_id}", file=sys.stderr)
        return 1
    print(json.dumps(job, ensure_ascii=False))
    return 0


def _job_files(job_id: str, folder: str) -> int:
    """`job files <job> <folder> --json`: the job's model folder written
    into a new or empty folder, `economics.md`, `report.md`, its
    declaration and `record.json`, the job as the service holds it, as the
    client's `job files` writes it; the job's `files`, a mapping from a
    path in the model folder to its text, where the job holds one (unit
    G3), in place of the first three."""
    job = _service()["jobs"].get(job_id)
    target = Path(folder)
    if job is None or "result" not in job:
        print(f"Error: job {job_id} holds no record", file=sys.stderr)
        return 1
    if target.exists() and any(target.iterdir()):
        print(f"Error: {folder} is not empty", file=sys.stderr)
        return 1
    files = {
        **(job.get("files") or {
            "economics.md": f"# The model prose of {job_id}\n",
            "report.md": f"# The report of {job_id}\n",
            "declaration/spec.yml": "trellis: trellis.yml\n",
        }),
        "record.json": json.dumps({key: value for key, value in job.items() if key != "files"})
        + "\n",
    }
    for name, text in files.items():
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        (target / name).write_text(text, encoding="utf-8")
        if os.environ.get("BELLMAN_WORKBENCH_MATSYA_STUB_FILES_FAIL"):
            print(f"Error: the connection closed after {name} was written", file=sys.stderr)
            return 1
    print(json.dumps(job, ensure_ascii=False))
    return 0


def _session_show(session_id: str) -> int:
    state = _service()
    print(json.dumps({
        "id": session_id,
        "entries": state.get("entries", {}).get(session_id, []),
        "jobs": [job for job in state["jobs"].values() if job["session"] == session_id],
        "turns": [turn["id"] for turn in state["turns"].values() if turn["session"] == session_id],
    }))
    return 0


def _add_entry(session_id: str, file: str, delivery: str) -> int:
    """`session add <session> <file> --kind user --delivery-id <id>
    --json`: the user's entry read from `file`, appended to the session's
    entries, or the entry the delivery identifier already names (unit G4)."""
    state = _service()
    entries = state.setdefault("entries", {}).setdefault(session_id, [])
    held = state.setdefault("entry_deliveries", {}).get(delivery)
    repeated = held is not None
    if held is None:
        held = len(entries) + 1
        entry_text = Path(file).read_text(encoding="utf-8")
        entries.append({"number": held, "kind": "user", "text": entry_text})
        state["entry_deliveries"][delivery] = held
        _keep(state)
    print(json.dumps({"id": session_id, "entry": {"number": held, "kind": "user"},
                      "revision": len(entries), "repeated": repeated, "scheduled": None}))
    return 0


# the passages the stand-in's index answers a search with (unit G4)
SEARCHED = (
    {"passage_id": "p-1", "corpus": "literature", "path": "literature/deaton-1991.txt",
     "heading": "2 The model", "location": {"page": 1225},
     "text": "When the constraint binds, the marginal utility of consumption exceeds "
             "the discounted expected marginal utility of next period's consumption."},
    {"passage_id": "p-2", "corpus": "repository", "path": "docs/overview/03-language.md",
     "heading": "Stages", "location": {"page": None}, "text": "A stage has three perches."},
)


def _search(query: str, collection: str | None) -> int:
    """`search --json [--collections <c>] -- <query>`: the stand-in's
    passages of the collection named, or all, with no turn and no job."""
    found = [dict(passage) for passage in SEARCHED if collection in (None, passage["corpus"])]
    print(json.dumps({"index_digest": "stand-in", "query": query, "passages": found},
                     ensure_ascii=False))
    return 0


def _project_init(folder: str) -> int:
    """`project init <folder> --json`: the folder's session, named after
    the folder, and the client's files of a project folder (unit G4)."""
    root = Path(folder)
    session = hashlib.sha256(root.name.encode("utf-8")).hexdigest()[:32]
    held = {"session": session, "server": "http://127.0.0.1:8710"}
    (root / ".bellman-matsya").mkdir(parents=True, exist_ok=True)
    (root / ".bellman-matsya/project.json").write_text(json.dumps(held) + "\n", encoding="utf-8")
    (root / ".bellman-matsya/README.md").write_text("# The project's records\n", encoding="utf-8")
    written = [".bellman-matsya/project.json", ".bellman-matsya/README.md"]
    if not (root / "AGENTS.md").exists():
        (root / "AGENTS.md").write_text("# For an agent\n", encoding="utf-8")
        written.append("AGENTS.md")
    print(json.dumps({"folder": str(root), "project": held, "session": {"id": session,
                      "name": root.name}, "entry": None, "written": written}))
    return 0


def _select(session_id: str, job_id: str) -> int:
    """`session select <session> <job> --json`: the job selected for the
    session's conversation."""
    state = _service()
    state["selected"][session_id] = job_id
    _keep(state)
    print(json.dumps({"id": session_id, "selected_job": job_id}))
    return 0


def main() -> int:
    arguments = sys.argv[1:]
    _log(arguments)
    if len(arguments) >= 4 and arguments[:2] == ["session", "new"]:
        name = arguments[2]
        if arguments[3:] != ["--json"]:
            return 2
        print(json.dumps({"id": f"id-{name}", "name": name}))
        return 0
    if len(arguments) == 4 and arguments[:2] == ["job", "submit-prepared"]:
        return _submit_prepared(arguments[2]) if arguments[3] == "--json" else 2
    if (
        len(arguments) == 6
        and arguments[:2] == ["job", "submit-prepared"]
        and arguments[3] == "--delivery-id"
        and arguments[5] == "--json"
    ):
        return _submit_prepared(arguments[2], arguments[4])
    if len(arguments) == 8 and arguments[0] == "ask" and arguments[2:4] == [
        "--no-wait",
        "--delivery-id",
    ]:
        if arguments[5:7] != ["--json", "--"]:
            return 2
        return _ask_without_waiting(arguments[1], arguments[4], arguments[7])
    if len(arguments) == 5 and arguments[:2] == ["turn", "status"] and arguments[4] == "--json":
        return _turn_status(arguments[2], arguments[3])
    if len(arguments) == 4 and arguments[:2] == ["job", "status"] and arguments[3] == "--json":
        return _job_status(arguments[2])
    if len(arguments) == 5 and arguments[:2] == ["job", "files"] and arguments[4] == "--json":
        return _job_files(arguments[2], arguments[3])
    if len(arguments) == 4 and arguments[:2] == ["session", "show"] and arguments[3] == "--json":
        return _session_show(arguments[2])
    if len(arguments) == 5 and arguments[:2] == ["session", "select"] and arguments[4] == "--json":
        return _select(arguments[2], arguments[3])
    if len(arguments) == 4 and arguments[:2] == ["project", "init"] and arguments[3] == "--json":
        return _project_init(arguments[2])
    searching = arguments[:2] == ["search", "--json"] and len(arguments) in (4, 6)
    if searching and arguments[-2] == "--":
        named = len(arguments) == 6 and arguments[2] == "--collections"
        collection = arguments[3] if named else None
        return _search(arguments[-1], collection)
    if (
        len(arguments) == 9
        and arguments[:2] == ["session", "add"]
        and arguments[4:7] == ["--kind", "user", "--delivery-id"]
        and arguments[8] == "--json"
    ):
        return _add_entry(arguments[2], arguments[3], arguments[7])
    if len(arguments) != 5 or arguments[0] != "ask" or arguments[2:4] != ["--json", "--"]:
        return 2
    session_id, question = arguments[1], arguments[4]
    if not session_id.startswith("id-"):
        return 2
    if "silent" in question:
        print("The Bellman service did not answer", file=sys.stderr)
        return 1
    if "garbled" in question:
        print("an answer that is not JSON")
        return 0
    if "wait" in question:
        time.sleep(WAIT_SECONDS)
    name = session_id.removeprefix("id-")
    answer = (
        "Υ reads the stage file into the operators 𝑉 ∘ g.\n"
        f"question: {question}\n"
        f"session: {name}\n"
        "model: the client's default"
    )
    print(
        json.dumps(
            {
                "id": "turn-1",
                "state": "finished",
                "record": {
                    "result": {
                        "status": "answered",
                        "answer": answer,
                        "citations": [{"path": path} for path in PASSAGES],
                    }
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
