"""Put the notebook's process in this checkout and make the objects of the
six cases of the Matsya chat integration's acceptance.

Importing this module does five things and prints nothing.

1. It finds the checkout, the nearest folder above this file that holds
   `packages/bellman-workbench`, and refuses a package of the Workbench, the
   language, the client or the service already imported from another
   checkout; a kernel that holds one is restarted.
2. It puts the checkout's four packages first on `sys.path` and names them
   in `PYTHONPATH`, so that the client the Workbench runs as a program of
   its own reads this checkout's client as well.
3. It puts the Workbench's test folder on `sys.path`, whose stand-in client
   `matsya_stub.py`, helpers `workbench_support.py` and acceptance file
   `test_spec_0_6_unit_g5.py` the cases use, so that a notebook runs the
   same steps as the tests.
4. It makes a scratch folder of its own, in which every copy of a model,
   the stand-in's service file and its log, the local service's files and a
   home folder with no client configuration stand.
5. It makes the stand-in the client the Workbench runs, with the stand-in's
   address, a token of the tests and no personal Anthropic key, so that no
   step reaches the installed service and none reads the user's own
   configuration; the client's messages are printed without terminal
   colors.

The functions below make each case's objects; each is one step a test of
the acceptance file also takes.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import json
import os
import shlex
import shutil
import sys
import tempfile
from pathlib import Path


def _checkout() -> Path:
    """The nearest folder above this file that holds the Workbench."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "packages" / "bellman-workbench").is_dir():
            return candidate
    raise ImportError(f"no checkout holding packages/bellman-workbench stands above {__file__}")


ROOT = _checkout()
PACKAGES = (
    ROOT / "packages" / "bellman",
    ROOT / "packages" / "bellman-workbench",
    ROOT / "packages" / "matsya",
    ROOT / "packages" / "bellman-matsya-client" / "src",
)
TESTS = ROOT / "packages" / "bellman-workbench" / "tests"
for _name in ("bellman", "bellman_workbench", "bellman_matsya", "matsya_service"):
    _held = sys.modules.get(_name)
    if _held is not None and not Path(_held.__file__).resolve().is_relative_to(ROOT):
        raise ImportError(
            f"{_name} was imported from {_held.__file__}, not from {ROOT}; restart the kernel"
        )
sys.path[:0] = [str(path) for path in (*PACKAGES, TESTS)]
os.environ["PYTHONPATH"] = os.pathsep.join(str(path) for path in PACKAGES)

# the plotting library's cache stays where it is, outside the scratch home
os.environ.setdefault("MPLCONFIGDIR", str(Path.home() / ".matplotlib"))
SCRATCH = Path(tempfile.mkdtemp(prefix="matsya-cases-"))
(SCRATCH / "home").mkdir()
STAND_IN_SERVER = "http://127.0.0.1:8710"
LOG = SCRATCH / "client-calls.jsonl"
os.environ.update(
    {
        "HOME": str(SCRATCH / "home"),
        "XDG_CACHE_HOME": str(SCRATCH / "cache"),
        "BELLMAN_WORKBENCH_MATSYA_STATE_DIR": str(SCRATCH / "matsya-sessions"),
        "BELLMAN_WORKBENCH_MATSYA_STUB_STATE": str(SCRATCH / "stand-in-service.json"),
        "BELLMAN_WORKBENCH_MATSYA_STUB_LOG": str(LOG),
        "BELLMAN_MATSYA_SERVER": STAND_IN_SERVER,
        "BELLMAN_MATSYA_TOKEN": "msy_" + "0" * 32,
        "NO_PROXY": "127.0.0.1,localhost",
        "no_proxy": "127.0.0.1,localhost",
        "NO_COLOR": "1",
    }
)
for _name in (
    "http_proxy",
    "HTTP_PROXY",
    "https_proxy",
    "HTTPS_PROXY",
    "all_proxy",
    "ALL_PROXY",
    "BELLMAN_MATSYA_ANTHROPIC_KEY",
    "BELLMAN_MATSYA_ANTHROPIC_KEY_OVER_HTTP",
):
    os.environ.pop(_name, None)

import test_spec_0_6_unit_g5 as cases  # noqa: E402
import workbench_support as support  # noqa: E402

from bellman_workbench import matsya_client, matsya_window, matsya_work, model  # noqa: E402

os.environ["BELLMAN_WORKBENCH_MATSYA"] = support.MATSYA_STUB

DURABLES = cases.DURABLES
PENSIONS = cases.PENSIONS
SHOCKS = cases.SHOCKS
TENURE = cases.TENURE
CALIBRATION = cases.CALIBRATION
SETTINGS = cases.SETTINGS
AUTHOR_TOKEN = cases.AUTHOR_TOKEN
COLLEAGUE_TOKEN = cases.COLLEAGUE_TOKEN
HIGH, LOW, LOWER = cases.HIGH, cases.LOW, cases.LOWER


def _fresh(name: str) -> Path:
    """A new folder `name` in a new numbered folder of the scratch folder."""
    number = len(list(SCRATCH.glob("copy-*")))
    holder = SCRATCH / f"copy-{number}"
    holder.mkdir()
    return holder / name


# --- the models and the stand-in ---


def durables() -> model.Folder:
    """A fresh copy of the durables model, a git repository with one commit."""
    return model.open_folder(support.repository_copy(support.DURABLES, _fresh("durables")))


def pensions() -> model.Folder:
    """A fresh copy of the pension model whose trellis file names two period
    templates, `period.pensions.yml` and `period.working.yml`."""
    return model.open_folder(support.pensions_two_templates(_fresh("pensions")))


def session_of(folder: model.Folder) -> matsya_work.Session:
    """A session of the stand-in's service for `folder` on the service the
    client's settings name now."""
    return cases.session_of(folder)


def connected(folder: model.Folder) -> matsya_work.Session:
    """The folder connected to the stand-in's service, as the client's
    `project init` records a connection, and its session."""
    return cases.connected(folder)


def unsaved(folder: model.Folder, path: str, line: str) -> dict:
    """The editor's unsaved buffer of the file at `path`: its text on disk
    with `line` added, by the file's path."""
    disk = (folder.root / path).read_text(encoding="utf-8")
    return {path: matsya_work.Buffer(disk + line, cases.sha256(disk))}


def received() -> dict:
    """The digest of each text the stand-in received with the last prepared
    submission, by the name the service reads it under."""
    return [entry for entry in support.stub_calls(LOG) if "submitted" in entry][-1]["submitted"]


def prepared_texts(prepared) -> dict:
    """The digest of each text of the prepared-inputs file of `prepared`, by
    the name the service reads it under."""
    inputs = json.loads((_folder_of(prepared) / prepared.record["inputs"]).read_text("utf-8"))
    return {name: cases.sha256(text) for name, text in inputs["starting_declaration"].items()}


def _folder_of(prepared) -> Path:
    """The model folder whose prepared record `prepared` is."""
    for folder in SCRATCH.glob("copy-*/*"):
        if (folder / prepared.path).is_file():
            return folder
    raise FileNotFoundError(prepared.path)


def calls() -> list:
    """The command lines of the client's runs the stand-in logged since the
    log was last emptied."""
    return cases.calls_of(LOG)


def forget_calls() -> None:
    """Empties the stand-in's log."""
    LOG.unlink(missing_ok=True)


def fingerprint(folder: model.Folder) -> str:
    """One SHA-256 digest of every file of the folder, its path and its
    bytes, git's files left out, so that two readings can be compared at a
    glance."""
    digest = hashlib.sha256()
    for path, data in cases.every_file(folder.root).items():
        digest.update(path.encode("utf-8") + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest()


def client(*arguments: str):
    """One run of the client the Workbench runs, with `arguments`."""
    return matsya_client.run(list(arguments))


def pdf() -> str:
    """The path of a small PDF file in the scratch folder."""
    path = SCRATCH / "paper.pdf"
    path.write_bytes(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n")
    return str(path)


def warned_submission(folder: model.Folder, session) -> matsya_work.Work:
    """A job prepared from the durables recipe and submitted while the
    stand-in's client prints the accepted job and then the warning that the
    service used its own key, exiting with status 1."""
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_WARN"] = "1"
    try:
        return matsya_work.submit(folder, prepared.path, session)
    finally:
        os.environ.pop("BELLMAN_WORKBENCH_MATSYA_STUB_WARN")


def lost_turn(folder: model.Folder, session, question: str) -> matsya_work.Work:
    """A turn whose answer the stand-in's client loses in transport: the
    service holds the turn and the client prints nothing, exiting with
    status 1."""
    os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_LOST"] = "1"
    try:
        return matsya_work.start_turn(folder, session, question)
    finally:
        os.environ.pop("BELLMAN_WORKBENCH_MATSYA_STUB_LOST")


def service_works_on(job_id: str, turn_id: str, answer: str) -> None:
    """The stand-in's service runs the job `job_id` and finishes the turn
    `turn_id` with `answer`, while the page is closed."""
    held = json.loads(Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"]).read_text("utf-8"))
    support.stub_job({**held["jobs"][job_id], "state": "running"})
    support.stub_turn(
        {
            **held["turns"][turn_id],
            "state": "finished",
            "record": {
                "result": {"status": "answered", "answer": answer, "citations": [{"path": TENURE}]}
            },
        }
    )


def stand_in_turns() -> list:
    """The identifiers of the turns the stand-in's service holds."""
    held = json.loads(Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"]).read_text("utf-8"))
    return sorted(held["turns"])


def reopened():
    """The adapter's module loaded again, as when the page is opened again."""
    return importlib.reload(matsya_work)


def not_converged(folder: model.Folder, session, number: int) -> str:
    """A job of the stand-in's service that did not converge, whose returned
    calibration lowers τ to 0.08, with one difference of its comparison, one
    comment on the prose and one unresolved assumption; answers its
    identifier."""
    job = support.returned_job(folder.root, session.id, number, 3, {CALIBRATION: (HIGH, LOW)})
    support.stub_job(
        {
            **job,
            "state": "not_converged",
            "result": {
                "cycles_run": 3,
                "comparison": {
                    "converged": False,
                    "differences": [
                        "tenure: the law of motion of H differs from the earlier attempt's"
                    ],
                },
                "comments": [
                    "The prose reads τ as a share of the house's value; the source names no unit."
                ],
                "questions": ["Is τ paid every period or only when the house is sold?"],
            },
        }
    )
    return job["id"]


def submitted(folder: model.Folder, session) -> int:
    """The number of a job prepared from the durables recipe and submitted
    to the stand-in, so that the folder holds the job's prepared record."""
    prepared = matsya_work.prepare(folder, DURABLES, "recipe", session, 1)
    return int(matsya_work.submit(folder, prepared.path, session).record["accepted"][4:])


def _returned(folder: model.Folder, session, number: int, cycles: int, edits: dict) -> str:
    """A job of the stand-in's service that converged with the folder's own
    declaration changed by `edits`, downloaded as a saved copy; answers the
    copy's path from the folder."""
    job = support.returned_job(folder.root, session.id, number, cycles, edits)
    return matsya_work.download(folder, session, job["id"]).path


def lowered(folder: model.Folder, session, number: int, cycles: int, tau: str = LOW) -> str:
    """The saved copy of iteration `cycles` of the job `number`, whose
    calibration lowers the housing cost τ from 0.12 to `tau`."""
    return _returned(folder, session, number, cycles, {CALIBRATION: (HIGH, tau)})


def lowered_with_settings(folder: model.Folder, session, number: int, cycles: int) -> str:
    """The saved copy of iteration `cycles` of the job `number`, whose
    calibration lowers τ to 0.08 and whose settings file sets n_a to 301."""
    return _returned(
        folder,
        session,
        number,
        cycles,
        {CALIBRATION: (HIGH, LOW), SETTINGS: ("n_a:", "n_a: 301 #")},
    )


def files_of(folder: model.Folder) -> dict:
    """The bytes of each file of the folder by its path, git's files left
    out."""
    return cases.every_file(folder.root)


def changed_since(folder: model.Folder, files: dict) -> list:
    """The paths of `files` whose bytes now differ in the folder, or that no
    longer stand."""
    now = cases.every_file(folder.root)
    return [path for path in files if now.get(path) != files[path]]


def view_of(folder: model.Folder, session, job_id: str, copy: str):
    """What the column holds of the job `job_id`: the service's answer, its
    saved copy and the copy constructed as a model of its own."""
    from bellman_workbench import returned as returned_module

    answer = matsya_work.membership(session, job_id, "discussed").job
    return matsya_window.JobView(answer, copy, returned_module.inspect(folder, copy))


def full_disk(at, relpath, text, expected):
    """A writer that fails on the settings file with the operating system's
    full-disk error and writes every other file by the guarded save."""
    import errno

    if relpath == SETTINGS:
        raise OSError(errno.ENOSPC, "No space left on device", relpath)
    return model.save_file(at, relpath, text, expected)


def equation_citation(folder: model.Folder) -> dict:
    """A citation of the first equation of the tenure stage, by its path
    and line, as the service names a file of the model folder."""
    lines = (folder.root / TENURE).read_text(encoding="utf-8").splitlines()
    line = next(n for n, text in enumerate(lines, 1) if " = " in text and "~" not in text)
    return {"path": TENURE, "location": {"line": line}}


def returned_citation(number: int) -> dict:
    """A citation of the calibration file the job `number` returned."""
    return {
        "identity": {"source": "job"},
        "location": {"job": f"job-{number}", "output": "calibration/durables.yml"},
    }


def invented_citation() -> dict:
    """A citation of a path of Matsya's own repository, which the model
    folder does not hold."""
    return {"path": "docs/overview/03-language.md"}


# --- the local service and the client itself ---


def real_client(address: str, token: str) -> None:
    """The Workbench runs the client `bellman-matsya` itself against the
    service at `address` with the Matsya token `token`."""
    os.environ["BELLMAN_WORKBENCH_MATSYA"] = shlex.join([str(cases.REAL_CLIENT)])
    os.environ["BELLMAN_MATSYA_SERVER"] = address
    os.environ["BELLMAN_MATSYA_TOKEN"] = token


def with_personal_key() -> None:
    """A personal Anthropic key of the tests in the client's variable."""
    os.environ["BELLMAN_MATSYA_ANTHROPIC_KEY"] = cases.FIXTURE_KEY


def without_personal_key() -> None:
    """No personal Anthropic key in the client's variable."""
    os.environ.pop("BELLMAN_MATSYA_ANTHROPIC_KEY", None)


def stand_in() -> None:
    """The Workbench runs the stand-in again, at its own address."""
    os.environ["BELLMAN_WORKBENCH_MATSYA"] = support.MATSYA_STUB
    os.environ["BELLMAN_MATSYA_SERVER"] = STAND_IN_SERVER
    os.environ["BELLMAN_MATSYA_TOKEN"] = "msy_" + "0" * 32


class Service:
    """The Matsya service of the service package's test configuration,
    started on the loopback address by the acceptance file's
    `local_service`: the author's and a colleague's tokens, jobs that end
    with one question, and no model provider. `address` is its address;
    `hold()` keeps both of its workers busy; `release()` lets them go;
    `stop()` stops it."""

    def __init__(self) -> None:
        self._stack = contextlib.ExitStack()
        self.address, self.processor = self._stack.enter_context(
            cases.local_service(_fresh("service"))
        )

    def __repr__(self) -> str:
        return f"the local Matsya service at {self.address}"

    def hold(self) -> str:
        """Two jobs that hold both workers until `release()`, which a
        `release()` before had let go."""
        self.processor.release.clear()
        for _ in range(2):
            cases.post(
                self.address,
                AUTHOR_TOKEN,
                "/v1/model-iterations",
                {"source": {"kind": "description", "text": cases.HOLD}, "target": "stage"},
            )
        held = self.processor.holding.acquire(timeout=10) and self.processor.holding.acquire(
            timeout=10
        )
        return "both workers hold a job" if held else "the workers did not take the two jobs"

    def release(self) -> None:
        self.processor.release.set()

    def stop(self) -> None:
        self._stack.close()

    def job(self, text: str) -> str:
        """A job of no session whose source is the description `text`,
        submitted by the author; answers its identifier."""
        return cases.post(
            self.address,
            AUTHOR_TOKEN,
            "/v1/model-iterations",
            {"source": {"kind": "description", "text": text}, "target": "stage"},
        )["id"]


def ended(record: dict) -> dict:
    """The service's answer for the job of the request `record` once the job
    has ended."""
    return cases.ended_job(record)


def ended_job(job_id: str) -> dict:
    """The service's answer for the job `job_id` once it has ended."""
    return cases.ended_by_identifier(job_id)


def session_shown(session_id: str) -> dict:
    """The session as the client's `session show --json` prints it."""
    return cases.session_shown(session_id)


def question_of(session_id: str) -> dict:
    """The session's last question entry, which a job asked."""
    return [
        entry for entry in session_shown(session_id)["entries"] if entry["kind"] == "question"
    ][-1]


def reply(session_id: str, number: int, delivery: str) -> dict:
    """A reply to the session's entry `number`, sent by the client's
    `session add --replies-to` with the delivery identifier `delivery`:
    the entry's number, whether the service recognized the delivery as
    repeated, and the job the reply started, None for none."""
    path = SCRATCH / "reply.md"
    path.write_text("An AR(1) process with persistence 0.9.\n", encoding="utf-8")
    ran = client(
        "session",
        "add",
        session_id,
        str(path),
        "--replies-to",
        str(number),
        "--delivery-id",
        delivery,
        "--json",
    )
    scheduled = ran.answer.get("scheduled")
    return {
        "entry": ran.answer["entry"]["number"],
        "repeated": ran.answer["repeated"],
        "started": scheduled["id"] if scheduled else None,
    }


def jobs_of(session_id: str) -> list:
    """The identifiers of the session's jobs, in the order they were made."""
    return [job["id"] for job in session_shown(session_id)["jobs"]]


def handed_over(folder: model.Folder) -> model.Folder:
    """A copy of the folder with its records, as given to a colleague."""
    target = _fresh(folder.root.name)
    shutil.copytree(folder.root, target)
    return model.open_folder(target)


# --- the column drawn in this process ---


class Column:
    """Matsya's column for one folder, drawn in this process with the page's
    own components, as the page draws it, and read by the classes of its
    elements: `texts(class_)`, `chips()`, `click(class_)`, `send(kind,
    text)`, `close()`."""

    def __init__(self, folder: model.Folder) -> None:
        import solara

        from bellman_workbench import app

        self._app = app
        self._folder = folder
        self._held = (app.tab_folder.value, app.source.value)
        app.tab_folder.value = folder
        app.source.value = DURABLES
        actions = matsya_window.Actions(
            folder=lambda: folder,
            open_file=lambda path, line: None,
            open_copy=lambda path: None,
            buffers=lambda: {},
            open_commit=lambda record: None,
            source=lambda: DURABLES,
        )

        @solara.component
        def Drawn():
            return matsya_window.MatsyaWindow(
                app._session(),
                app.Field,
                app.ToolbarButton,
                app.TextButton,
                app.matsya_context(),
                actions,
            )

        _, self._rendered = solara.render(Drawn(), handle_error=False)

    def __repr__(self) -> str:
        return "Matsya's column, drawn"

    def texts(self, class_: str) -> list:
        return cases._texts_of(self._rendered, class_)

    def chips(self) -> dict:
        return cases._chips(self._rendered)

    def click(self, class_: str) -> None:
        cases._click(self._rendered, class_)

    def send(self, kind: str, text: str, choice: str | None = None) -> None:
        """Sends `text` as the kind of request `kind`, with the collection of
        a search or the level of a build `choice`, and waits for its answer,
        its search's passages or its build's prepared material."""
        matsya_window.set_kind(kind)
        if kind == matsya_window.SEARCH:
            matsya_window.set_collection(choice)
        if kind == matsya_window.BUILD:
            matsya_window.set_target(choice)
        before = len(matsya_window.exchanges.value)
        matsya_window.send(text)
        if kind == matsya_window.BUILD:
            support.wait_until(
                lambda: any(view.prepared for view in matsya_window.builds.value.values()),
                20.0,
                "the build",
            )
            return
        support.wait_until(lambda: len(matsya_window.exchanges.value) > before, 5.0, "the request")
        if kind == matsya_window.SEARCH:
            support.wait_until(
                lambda: matsya_window.exchanges.value[-1].answer is not None, 20.0, "the search"
            )

    def connect(self) -> dict:
        """Clicks `Connect this folder to Matsya` and answers the chips once
        the session's chip names the new session."""
        self.click("bl-text-button bl-matsya-connect-button")
        support.wait_until(
            lambda: self.chips()["session"] != [matsya_window.NOT_CONNECTED],
            10.0,
            "the session's chip",
        )
        return self.chips()

    def ask(self, text: str) -> dict:
        """Sends the question `text` in the folder's project session and
        answers the request's record once the stand-in has accepted the
        turn."""
        matsya_window.set_kind(matsya_window.ASK)
        matsya_window.send(text)
        requests = self._folder.root / matsya_work.REQUESTS_FOLDER

        def accepted():
            for path in requests.glob("*.json") if requests.is_dir() else ():
                record = json.loads(path.read_text(encoding="utf-8"))
                if record["kind"] == "turn" and record["question"] == text and record["accepted"]:
                    return record
            return None

        record, _ = support.wait_until(accepted, 20.0, "the turn accepted")
        return record

    def answered(self, record: dict, answer: str) -> str:
        """The stand-in's service finishes the turn of `record` with
        `answer`; answers the column's answer once it is drawn."""
        support.stub_turn(
            {
                "id": record["accepted"],
                "session": record["session"],
                "state": "finished",
                "record": {
                    "result": {
                        "status": "answered",
                        "answer": answer,
                        "citations": [{"path": TENURE}],
                    }
                },
            }
        )
        support.wait_until(
            lambda: matsya_window.exchanges.value[-1].answer is not None, 20.0, "the answer"
        )
        return matsya_window.exchanges.value[-1].answer

    def files_listed(self) -> list:
        """The rows of `Files`, each file with the start of its
        fingerprint."""
        found = self._rendered.find(cases.ipyvue.Html, tag="ul", class_="bl-matsya-build-files")
        found.wait_for(timeout=10)
        return ["".join(map(str, item.children)) for item in found.widget.children]

    def close(self) -> None:
        self._rendered.close()
        self._app.tab_folder.value, self._app.source.value = self._held
