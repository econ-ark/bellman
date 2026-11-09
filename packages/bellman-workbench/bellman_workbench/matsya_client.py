"""Ask the Bellman Matsya service through its separate command-line client.

The Workbench uses the Bellman-only command and keeps the service's session
identifier for each model folder. The name passed by the page is a digest of
the folder's path, so neither a local path nor a token is sent as a session
name. The client itself reads its token and service address.

`run` runs any other command of the client for `matsya_work.py` (unit G2
of specification 0.6) and keeps what the client printed whatever its exit
status, since the client prints the answer of a request the service
accepted before a warning that ends it with status 1.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple

COMMAND_VARIABLE = "BELLMAN_WORKBENCH_MATSYA"
STATE_DIR_VARIABLE = "BELLMAN_WORKBENCH_MATSYA_STATE_DIR"
OFF = "off"
COMMANDS = ("bellman-matsya",)
ANSWER_SECONDS = 930

NO_CLIENT = "Bellman Matsya's client {name} was not found"
NO_ANSWER = "Bellman Matsya did not answer"
UNREAD = "Bellman Matsya's client returned an answer the Workbench cannot read"


class Answer(NamedTuple):
    """One answer and the paths of its cited passages."""

    answer: str
    passages: tuple[str, ...]


class Cited(NamedTuple):
    """One answer, the paths of its cited passages, as `Answer` holds them,
    and `citations`, each citation as the service's answer gives it, a
    mapping with its `identity`, `path`, `heading`, `location`, `quote`
    and `authority` where the service gives them, which the column reads to
    resolve its destination (amendment 06 §2 item 6)."""

    answer: str
    passages: tuple[str, ...]
    citations: tuple[dict, ...]


def _named() -> str:
    """The configured command after surrounding white space is removed."""
    return os.environ.get(COMMAND_VARIABLE, "").strip()


@functools.cache
def switched_off() -> bool:
    """Whether the Workbench was started with its Matsya column disabled."""
    return _named() == OFF


def command() -> list[str] | None:
    """The explicitly configured command; else the Bellman-only command
    beside the interpreter that runs the Workbench, its own Python
    environment, where the README installs the client; else that command on
    PATH. The environment comes first so that a desktop launch, whose PATH
    lacks it, and a PATH holding an older client both run the client
    installed with the Workbench."""
    named = _named()
    if named == OFF:
        return None
    if named:
        return shlex.split(named)
    beside = shutil.which(COMMANDS[0], path=str(Path(sys.executable).parent))
    found = beside or shutil.which(COMMANDS[0])
    return [found] if found is not None else None


def _state_file(name: str) -> Path:
    """The local file that remembers the service session for one folder."""
    directory = os.environ.get(STATE_DIR_VARIABLE)
    root = Path(directory) if directory else Path.home() / ".config" / "bellman-matsya" / "workbench-sessions"
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return root / f"{digest}.json"


def service_identity() -> str | None:
    """Identify the Bellman client settings without saving the token: the
    SHA-256 of the configuration file's bytes, the two variables that
    override its address and its token, and the configured command, so
    that a change of any of them names another service."""
    config_path = Path.home() / ".config" / "bellman-matsya" / "config.toml"
    try:
        saved = config_path.read_bytes() if config_path.exists() else b""
    except OSError:
        return None
    values = (
        saved,
        os.environ.get("BELLMAN_MATSYA_SERVER", "").encode("utf-8"),
        os.environ.get("BELLMAN_MATSYA_TOKEN", "").encode("utf-8"),
        _named().encode("utf-8"),
    )
    digest = hashlib.sha256()
    for value in values:
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def service_url() -> str | None:
    """The configured service URL, or None for the built-in address."""
    named = os.environ.get("BELLMAN_MATSYA_SERVER", "").strip()
    if not named:
        config_path = Path.home() / ".config" / "bellman-matsya" / "config.toml"
        if not config_path.is_file():
            return None
        try:
            saved = tomllib.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            return None
        server = saved.get("server")
        named = server.strip() if isinstance(server, str) else ""
    if not named:
        return None
    return named.rstrip("/")


def service_address() -> str | None:
    """The configured service address without the scheme."""
    url = service_url()
    return url.split("://", 1)[-1] if url else None


def _saved_session(path: Path, name: str, identity: str) -> str | None:
    """Read a session identifier created for this folder and service."""
    if not path.is_file() or path.is_symlink():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(value, dict) or value.get("name") != name or value.get("service") != identity:
        return None
    session_id = value.get("id")
    return session_id if isinstance(session_id, str) and session_id else None


def _remember_session(path: Path, name: str, identity: str, session_id: str) -> None:
    """Write the mapping as a private file, replacing it atomically."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"name": name, "service": identity, "id": session_id}, stream)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _completed(
    words: list[str], arguments: list[str], cwd: Path | None = None
) -> subprocess.CompletedProcess:
    """Runs the client command `words` with `arguments`, in UTF-8, with no
    standard input and within ANSWER_SECONDS, its two outputs captured."""
    return subprocess.run(
        [*words, *arguments],
        stdin=subprocess.DEVNULL,
        cwd=cwd,
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=ANSWER_SECONDS,
        check=False,
    )


def _run(words: list[str], arguments: list[str]) -> dict | None:
    """Run one Bellman client command and read its JSON answer."""
    try:
        finished = _completed(words, arguments)
    except (ValueError, subprocess.TimeoutExpired):
        return None
    if finished.returncode != 0:
        return None
    try:
        answer = json.loads(finished.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {}
    return answer if isinstance(answer, dict) else None


def _answer(turn: dict) -> Answer | None:
    """Read the completed turn's answer and cited paths."""
    if turn.get("state") != "finished":
        return None
    record = turn.get("record")
    result = record.get("result") if isinstance(record, dict) else None
    if not isinstance(result, dict):
        return None
    if result.get("status") == "needs_input":
        questions = result.get("questions")
        if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
            return None
        message = "Matsya asks:\n" + "\n".join(
            f"{number}. {question}" for number, question in enumerate(questions, 1)
        )
    else:
        message = result.get("answer")
        if not isinstance(message, str) or not message.strip():
            return None
    citations = result.get("citations") or []
    if not isinstance(citations, list):
        return None
    passages = []
    for citation in citations:
        if not isinstance(citation, dict):
            return None
        identity = citation.get("identity")
        path = citation.get("path") or (
            identity.get("target") if isinstance(identity, dict) else None
        )
        if not isinstance(path, str) or not path:
            return None
        heading = citation.get("heading")
        passages.append(f"{path} — {heading}" if isinstance(heading, str) and heading else path)
    return Answer(message, tuple(passages))


def _citations(turn: dict) -> tuple[dict, ...]:
    """The citations of a finished turn's answer, each a copy of the
    service's mapping; none where the answer holds none."""
    record = turn.get("record")
    result = record.get("result") if isinstance(record, dict) else None
    citations = result.get("citations") if isinstance(result, dict) else None
    if not isinstance(citations, list):
        return ()
    return tuple(dict(citation) for citation in citations if isinstance(citation, dict))


def read_turn(turn: dict) -> Cited | None:
    """The answer of a finished turn as the service gives it, the answer
    of `ask --json` or of `turn status --json`, with the paths of its
    passages and their citation records; None where the turn holds no
    answer the Workbench can read."""
    found = _answer(turn)
    if found is None:
        return None
    return Cited(found.answer, found.passages, _citations(turn) if found.passages else ())


def ask(question: str, session: str) -> Answer:
    """Ask in the saved session for this folder and show no client error text."""
    return _asked(question, session)[0]


def ask_cited(question: str, session: str) -> Cited:
    """Asks as `ask` does, and answers the citation records of the answer
    with it."""
    found, turn = _asked(question, session)
    citations = _citations(turn) if turn is not None and found.passages else ()
    return Cited(found.answer, found.passages, citations)


def _asked(question: str, session: str) -> tuple[Answer, dict | None]:
    """The answer of `ask` and the turn it read, None where the client gave
    no turn the Workbench can read."""
    from_variable = bool(_named())
    try:
        words = command()
    except ValueError:
        return Answer(NO_CLIENT.format(name=f"in {COMMAND_VARIABLE}"), ()), None
    if not words:
        return Answer(NO_CLIENT.format(name=" or ".join(COMMANDS)), ()), None
    identity = service_identity()
    if identity is None:
        return Answer(NO_ANSWER, ()), None
    state_file = _state_file(session)
    session_id = _saved_session(state_file, session, identity)
    if session_id is None:
        try:
            created = _run(words, ["session", "new", session, "--json"])
        except OSError:
            name = f"in {COMMAND_VARIABLE}" if from_variable else words[0]
            return Answer(NO_CLIENT.format(name=name), ()), None
        if created is None:
            return Answer(NO_ANSWER, ()), None
        session_id = created.get("id")
        if not isinstance(session_id, str) or not session_id:
            return Answer(UNREAD, ()), None
        try:
            _remember_session(state_file, session, identity, session_id)
        except OSError:
            return Answer(NO_ANSWER, ()), None
    try:
        turn = _run(words, ["ask", session_id, "--json", "--", question])
    except OSError:
        name = f"in {COMMAND_VARIABLE}" if from_variable else words[0]
        return Answer(NO_CLIENT.format(name=name), ()), None
    if turn is None:
        return Answer(NO_ANSWER, ()), None
    found = _answer(turn)
    return (found, turn) if found is not None else (Answer(UNREAD, ()), None)


class Run(NamedTuple):
    """One run of the client by `run`: `code`, its exit status, None where
    no client ran or it did not end within ANSWER_SECONDS; `answer`, the
    JSON object it printed on standard output, None where it printed none;
    and `warning`, its standard error as it printed it, which the client
    masks, or the sentence NO_CLIENT or NO_ANSWER where no client ran."""

    code: int | None
    answer: dict | None
    warning: str


def run(arguments: list[str], *, cwd: Path | None = None) -> Run:
    """Runs the configured client with `arguments`, in UTF-8 and within
    ANSWER_SECONDS, and answers what it printed whatever its exit status;
    a command that cannot be run is answered by the sentence `ask` gives."""
    from_variable = bool(_named())
    try:
        words = command()
    except ValueError:
        return Run(None, None, NO_CLIENT.format(name=f"in {COMMAND_VARIABLE}"))
    if not words:
        return Run(None, None, NO_CLIENT.format(name=" or ".join(COMMANDS)))
    try:
        if cwd is None:
            finished = _completed(words, arguments)
        else:
            finished = _completed(words, arguments, cwd)
    except OSError:
        name = f"in {COMMAND_VARIABLE}" if from_variable else words[0]
        return Run(None, None, NO_CLIENT.format(name=name))
    except (ValueError, subprocess.TimeoutExpired):
        return Run(None, None, NO_ANSWER)
    warning = finished.stderr.decode("utf-8", "replace").strip()
    try:
        answer = json.loads(finished.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return Run(finished.returncode, None, warning)
    return Run(finished.returncode, answer if isinstance(answer, dict) else None, warning)
