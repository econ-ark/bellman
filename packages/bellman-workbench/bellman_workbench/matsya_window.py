"""The Matsya window of Bellman Workbench (model interface specification
0.3, unit M), drawn as Matsya's column at the right of the window (spec 0.4
§§5.1 and 5.6; unit R, brief rules 2, 3 and 8; design pass 8 §6), to the
standard of Cursor's agent column since design pass 16 (unit G4 of
specification 0.6; amendment 06 of spec 0.4, §2 items 1, 3, 6, 25 and 28;
row S0-9): the page's ground, one hairline at its left edge, which
brand.css draws, and no rule under its head.

The head, 36 px from the window's top, level with the title bar, holds the
heading `Matsya`, Υ as text in periwinkle and the icon button `Fold
Matsya`, the Codicon `close`, which window.vue reads as the column's fold.
The conversation lists each exchange: a question in a faintly bounded box,
then Matsya's answer as plain text, with the speaker `Matsya` kept as the
turn's spoken label and not drawn (SG4-4), and the citations the answer
rests on, one row each, each resolved to its destination (`resolve`): a
file of the model folder opens at its line, a returned file opens in its
saved copy, a retrieved passage opens its quotation, and a destination
that cannot be resolved is named, with `unavailable` or `not downloaded`.
A job of the folder's requests, in a folder connected to Matsya, stands as
a message of its own: its number and state, then its result in five parts
apart (`parts`): semantic convergence, comments on the prose, unresolved
assumptions, the copy's construction and binding, and numerical checks,
which the Workbench never runs; then the actions on its returned files,
`Download returned files`, `Open returned files` and `Replace model
files…`, the last showing the plan of the adoption before the files are
written.

The composer at the foot is one bordered box (design pass 16 §3 rule 7):
the context chips (`Context`): the selected recipe or source with `saved`
or `unsaved`, the session, the job discussed and the service with its
configuration; the text area, one line when empty, Enter sending its text
and Shift+Enter beginning a line, sized by its text or by the handle
`composer` on the box's top edge (amendment 07 of spec 0.4), Escape in it
moving the focus to the conversation; and the foot row: the kind of
request, `Ask`, `Search sources` or `Build declaration`, then a search's
collection or a build's output level, and last the send control, named by
the kind, the Codicon `send` in a circle.
A search lists the passages of the client's index search, each opened with
`Discuss`; a build shows its prepared material before appending its request to the
project session and starting Architect through `Build declaration`; a folder not connected offers
`Connect this folder to Matsya`. The questions and answers are held per tab
for the page's life and written to no file. Each question is answered in
a task run off the page's thread (`answer_last`), so that the page stays
live while the service answers: in a folder connected to Matsya as a turn
of its project session (decision SG4-25), otherwise by
`matsya_client.ask_cited` in unit M's conversation.
`app.py` renders the window only where `matsya_client.switched_off()`
answered False at the server's start (spec 0.4 §6; R-D8). The window
draws its controls with the page's own components, `app.Field`,
`app.ToolbarButton`, `app.TextButton` and `app.Handle`, and calls the
page's functions through `Actions`, which `app.Page` passes, since the page
imports this module.

CSS class names the tests rely on:
  bl-matsya            the column, a child of .bl-window
  bl-matsya-head       its head, also .bl-head, 36 px: the heading
                       `Matsya`, the column's symbol .bl-matsya-upsilon
                       (Υ) and, in .bl-head-actions, .bl-fold with
                       data-fold `matsya` (the icon button `Fold Matsya`,
                       its aria-expanded whether the column is open);
                       while the column is folded it is not displayed, and
                       the button `Matsya` of the rail of icons opens it
                       (`app.Rail`; AAS, L-D12)
  bl-matsya-body       the body: .bl-matsya-exchanges (tabindex 0), one
                       .bl-matsya-exchange per exchange, holding
                       .bl-matsya-question and either .bl-matsya-pending,
                       while Matsya answers, or .bl-matsya-speaker
                       (`Matsya`, not drawn), .bl-matsya-answer and
                       .bl-matsya-citations, one .bl-matsya-citation per
                       citation, its data-kind `file`, `copy`, `passage` or
                       `unavailable`, holding .bl-matsya-passage, the
                       passage as the service names it; or .bl-matsya-job,
                       with data-job, its parts .bl-matsya-part with
                       data-part; and the composer .bl-matsya-row, holding
                       the handle .bl-handle with data-handle `composer`,
                       .bl-matsya-context, one .bl-matsya-chip per chip
                       with data-kind `source`, `session`, `job` or
                       `service`, .bl-matsya-field (the text area of
                       field.vue) and .bl-matsya-foot, which ends in
                       .bl-matsya-ask (the send control)
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path, PurePosixPath
from typing import Callable, NamedTuple

import reacton.ipyvuetify as rv
import solara
import solara.lab

from bellman_workbench import icons, matsya_client, matsya_work, model, returned


@dataclasses.dataclass(frozen=True)
class Exchange:
    """One exchange of the conversation. Of the kind `question`, a
    question of the window and Matsya's answer to it: `answer` is None
    while Matsya answers, `passages` holds the passages the answer rests on,
    as the service names them, and `citations` their records as the service
    gives them, which `resolve` reads; the records stand outside the
    exchange's comparison, since `passages` names them. Of the kind
    `search`, a search of the sources in the collection `scope`, its
    passages under `passages` and `citations` and, where the client
    answered none, its sentence as `answer`. Of the kind `build`, a build
    requested, which the column draws from `builds`. Of the kind `job`,
    the message of the job `job` of the folder's requests, which the column
    draws from `jobs`."""

    question: str
    answer: str | None = None
    passages: tuple[str, ...] = ()
    citations: tuple = dataclasses.field(default=(), compare=False)
    kind: str = "question"
    job: str | None = None
    scope: str | None = None
    turn: str | None = None


class Context(NamedTuple):
    """The context beside the composer (amendment 06 §2 item 1): `source`,
    the file name of the selected recipe or source, None where the folder
    has none; `unsaved`, whether a file it reads holds unsaved text in the
    editor; `session`, the name of the folder's project session, None where
    the folder is not connected to Matsya; `job`, the job discussed, None
    where none is; `service`, the service's address, None where it is not
    known; and `configuration`, the configuration's identifier, None for
    the service's default."""

    source: str | None = None
    unsaved: bool = False
    session: str | None = None
    job: str | None = None
    service: str | None = None
    configuration: str | None = None


class Actions(NamedTuple):
    """The page's functions the column calls, which `app.Page` passes:
    `folder()`, the tab's model folder; `open_file(path, line)`, which
    opens a file of the folder, at the line `line` where it is not None;
    `open_copy(path)`, which opens a saved copy as the tab's model
    (`app.open_returned`); `buffers()`, the editor's unsaved buffers as
    `matsya_work.Buffer` by the file's path from the folder; and
    `open_commit(record)`, which opens the commit form after an adoption
    (`app.open_adoption_commit`); and `source()`, the recipe or trellis
    file the tab shows, a `recipe.Source`, None where the folder has
    none, which a build prepares."""

    folder: Callable
    open_file: Callable
    open_copy: Callable
    buffers: Callable
    open_commit: Callable
    source: Callable = lambda: None


class Citation(NamedTuple):
    """A citation's destination (`resolve`): `kind`, `file`, a file of the
    model folder, `copy`, a returned file in its saved copy, `passage`, a
    retrieved passage, or `unavailable`; `path`, the file opened, from the
    folder; `line`, its line, None for its first; `quote`, a passage's
    quotation; `source`, a passage's place in one line; and `state`, the
    word after a destination that cannot be resolved."""

    kind: str
    path: str | None = None
    line: int | None = None
    quote: str | None = None
    source: str | None = None
    state: str | None = None


class Part(NamedTuple):
    """One of the five parts of a job's result (`parts`): its `name`, its
    `value` in a word or a count, and the sentences of its `details`."""

    name: str
    value: str
    details: tuple[str, ...] = ()


class JobView(NamedTuple):
    """What the column holds of one job: `job`, the service's answer read
    last, None where the service did not answer; `copy`, the path of its
    saved copy from the folder, None before the download; `inspected`, the
    copy constructed as a model of its own (`returned.inspect`), None before
    the download; `plan`, the plan of `Replace model files…` while it is
    shown (`returned.plan`); `adoption`, what the adoption answered; and
    `refusal`, the sentence of the last action refused."""

    job: dict | None = None
    copy: str | None = None
    inspected: object = None
    plan: object = None
    adoption: object = None
    refusal: str | None = None


class BuildView(NamedTuple):
    """A build review and the identity of its accepted job."""

    prepared: object = None
    choice: str | None = None
    job: str | None = None
    refusal: str | None = None
    listed: bool = False
    history: list[dict] | None = None
    source: object = None
    session: matsya_work.Session | None = None
    root: Path | None = None
    busy: bool = False
    restored: bool = False
    review_again: bool = False


# --- the words of the column ---

# the kinds of request (amendment 06 §2 item 28), those whose operations
# stand in the order of the menu
ASK = "Ask"
SEARCH = "Search sources"
BUILD = "Build declaration"
KINDS = (ASK, SEARCH, BUILD)
# the collections of a search, every collection the first
ALL_COLLECTIONS = "All collections"
COLLECTIONS = (ALL_COLLECTIONS, *matsya_work.COLLECTIONS)
# the output levels of a build, each with the target the adapter takes and
# the files that name it (amendment 06 §2 item 4)
TARGETS = {"Stage": "stage", "Period": "period", "Trellis": "trellis", "Recipe": "recipe"}
TARGET_FILES = {
    "Stage": "one .bl file",
    "Period": "stages, period.yml",
    "Trellis": "periods, trellis.yml",
    "Recipe": "calibration, settings, methods",
}
# the spoken names of the foot row's choices
KIND_NAME, TARGET_NAME, COLLECTION_NAME = "Kind of request", "Output level", "Collections"
# the action on an opened passage of a search, and the connection
DISCUSS = "Discuss"
CONNECT = "Connect this folder to Matsya"
# the line of a build being prepared, the list of its files, and the
# three choices for an unsaved buffer of unit G2 (`matsya_work.CHOICES`)
PREPARING = "Preparing"
FILES_SENT = "Files"
CHOICE_WORDS = {
    matsya_work.SAVE: "Save",
    matsya_work.SAVED_VERSION: "Saved version",
    matsya_work.DISPLAYED_TEXT: "Displayed text",
}

# the hover of the send control, the words the empty composer shows (design
# pass 8 §6, the mock's composer; the words of design pass 14 §5, AAS's, 21
# October 2026) and the composer's spoken name, where it has no label
ASK_HOVER = "Send the question to Matsya (Enter)"
COMPOSER_PLACEHOLDER = "Matsya query?"
COMPOSER_NAME = "Matsya query"
# the line of a question Matsya answers (SG4-9)
ANSWERING = "Answering"
# the words of the chips
SAVED, UNSAVED = "saved", "unsaved"
NOT_CONNECTED = "not connected"
UNKNOWN = "unknown"
DEFAULT = "default"
# the hover and the spoken kind of each chip
CHIP_KINDS = {
    "source": "Source",
    "session": "Session",
    "job": "Job discussed",
    "service": "Service and configuration",
}
# the kinds of a citation, and the words after one that cannot be resolved
FILE, COPY, PASSAGE, UNAVAILABLE = "file", "copy", "passage", "unavailable"
NOT_DOWNLOADED = "not downloaded"
# the five parts of a job's result (amendment 06 §2 item 25)
PART_NAMES = (
    "Semantic convergence",
    "Comments on the prose",
    "Unresolved assumptions",
    "Construction and binding",
    "Numerical checks",
)
# the actions on a job's returned files (amendment 06 §2 item 3)
DOWNLOAD = "Download returned files"
OPEN_COPY = "Open returned files"
REPLACE = "Replace model files…"
REPLACE_NOW = "Replace model files"
ADOPT_FIRST = "Adopt first declaration"
RESTORE = "Restore originals"
COMPLETE = "Complete replacement"
CANCEL = "Cancel"
COMMIT = "Commit…"
# a plan whose copy holds no file that differs from the model's
NO_CHANGE = "no file differs"
# the refusals of a build's first step
NOT_CONNECTED_SENTENCE = "this folder is not connected to Matsya"


def client_sentence(text: str) -> str:
    """A sentence of the client as the column shows it (the no-slop review
    of unit G5): the first line of what the client printed, without the
    word `Error:` that the client prints before a refusal, at the line's
    start and after the colon of an adapter's sentence that quotes the
    client. The request's record keeps the client's text as it printed it."""
    lines = text.strip().splitlines()
    first = lines[0] if lines else ""
    return first.removeprefix("Error: ").replace(": Error: ", ": ")


# --- the state of one tab, held for the page's life ---

# the text of the field, the question not yet sent
draft = solara.reactive("")
# the exchanges, in the order they were sent or the jobs were found
exchanges = solara.reactive(())
# the number of questions sent, on which the task that answers depends
asked = solara.reactive(0)
# the passages opened, by the exchange's number and the citation's
opened = solara.reactive(frozenset())
# the jobs the column shows, `JobView` by the job's identifier
jobs = solara.reactive({})
# the kind of request the composer sends, the output level of a build and
# the collection of a search
kind = solara.reactive(ASK)
target = solara.reactive("Recipe")
collection = solara.reactive(ALL_COLLECTIONS)
# the count of searches sent, on which the task that searches depends, and
# the count of connections made, which the page reads with the context
searched = solara.reactive(0)
connections = solara.reactive(0)
# the sentence of a connection refused
connect_refusal = solara.reactive(None)
# the job the conversation discusses, selected by its message's `Discuss`
# alone, so that a job that ends never changes it (amendment 06 §2 item 2)
discussed = solara.reactive(None)
# the builds, `BuildView` by the number of their exchange, and the count of
# builds requested, on which the task that prepares the last depends
builds = solara.reactive({})
requested = solara.reactive(0)
submission = solara.reactive(None)


conversation_generation = solara.reactive(0)
remote_history_unavailable = solara.reactive(False)


def clear_conversation() -> None:
    """Empties the conversation, the passages opened and the jobs, as a
    change of the tab's folder does; the field keeps its text."""
    conversation_generation.value += 1
    remote_history_unavailable.value = False
    exchanges.value = ()
    opened.value = frozenset()
    jobs.value = {}
    builds.value = {}
    submission.value = None
    discussed.value = None


def set_draft(text: str | None) -> None:
    """Keeps the field's text as the modeler types it."""
    draft.value = text or ""


def answering() -> bool:
    """Whether Matsya is answering the last question sent, or the last
    build requested is being prepared."""
    held = [exchange for exchange in exchanges.value if exchange.kind in ("question", "search")]
    if held and held[-1].answer is None:
        return True
    numbers = [n for n, exchange in enumerate(exchanges.value) if exchange.kind == "build"]
    return bool(numbers) and builds.value.get(numbers[-1], BuildView()) == BuildView()


def set_kind(text: str | None) -> None:
    """Keeps the kind of request chosen in the foot row."""
    kind.value = text if text in KINDS else ASK


def set_target(text: str | None) -> None:
    """Keeps the output level chosen in the foot row."""
    target.value = text if text in TARGETS else "Recipe"


def set_collection(text: str | None) -> None:
    """Keeps the collection chosen in the foot row."""
    collection.value = text if text in COLLECTIONS else ALL_COLLECTIONS


def send(text: str | None) -> None:
    """Sends `text` as the next question: the window lists it, the field
    is emptied and the count of questions sent rises by one. Text of white
    space alone sends nothing, and while Matsya answers the last question
    nothing is sent and the field keeps the text."""
    question = (text or "").strip()
    if not question or answering():
        return
    if kind.value == BUILD:
        exchanges.value = (*exchanges.value, Exchange(question, kind="build", scope=target.value))
        draft.value = ""
        requested.value = requested.value + 1
        return
    if kind.value == SEARCH:
        exchanges.value = (
            *exchanges.value,
            Exchange(question, kind="search", scope=collection.value),
        )
        draft.value = ""
        searched.value = searched.value + 1
        return
    exchanges.value = (*exchanges.value, Exchange(question))
    draft.value = ""
    asked.value = asked.value + 1


# the seconds between two readings of a turn the service has not finished,
# and the states in which a turn holds no answer to wait for
TURN_SECONDS = 1.0
TURN_ENDS = ("failed", "refused", "cancelled")


def _job_started(turn: dict) -> str | None:
    """The job this turn started, distinct from the job it discussed."""
    record = turn.get("record")
    result = record.get("result") if isinstance(record, dict) else None
    started = result.get("job_started") if isinstance(result, dict) else None
    job_id = started.get("id") if isinstance(started, dict) else None
    return job_id if isinstance(job_id, str) and job_id else None


def _turn_answer(
    folder: model.Folder,
    session: matsya_work.Session,
    question: str,
    standing: Callable[[], bool],
    on_accepted: Callable[[str], None],
) -> tuple[matsya_client.Cited | None, str | None, str | None]:
    """Read the accepted turn's answer and the job it started."""
    if not matsya_work.session_current(folder, session) or (
        matsya_client.service_url() is None and matsya_work.read_session(session, folder) is None
    ):
        refusal = "The connected Matsya session could not be verified."
        return matsya_client.Cited(refusal, (), ()), None, None
    work = matsya_work.start_turn(folder, session, question)
    turn_id = work.record["accepted"]
    if turn_id is None:
        refusal = client_sentence(work.record["warning"]) or matsya_client.NO_ANSWER
        return matsya_client.Cited(refusal, (), ()), None, None
    if standing() and matsya_work.session_current(folder, session):
        on_accepted(turn_id)
    for _ in range(int(matsya_client.ANSWER_SECONDS / TURN_SECONDS)):
        if not standing() or not matsya_work.session_current(folder, session):
            return None, turn_id, None
        turn = matsya_work.read_turn(session, turn_id)
        state = turn.get("state") if turn is not None else None
        if state == "finished":
            found = matsya_client.read_turn(turn)
            if found is None:
                found = matsya_client.Cited(matsya_client.UNREAD, (), ())
            job_id = _job_started(turn)
            if job_id is not None and matsya_work.session_current(folder, session):
                matsya_work.record_started_job(folder, work, job_id)
            return found, turn_id, job_id
        if state in TURN_ENDS:
            return matsya_client.Cited(matsya_client.NO_ANSWER, (), ()), turn_id, None
        time.sleep(TURN_SECONDS)
    return matsya_client.Cited(matsya_client.NO_ANSWER, (), ()), turn_id, None


def answer_last(session: str, actions=None) -> None:
    """Answer a question in the project session or anonymous conversation."""
    held = exchanges.value
    numbers = [n for n, exchange in enumerate(held) if exchange.kind == "question"]
    if not numbers or held[numbers[-1]].answer is not None:
        return
    number = numbers[-1]
    pending = held[number]
    generation = conversation_generation.value
    folder = actions.folder() if actions is not None else None

    def standing() -> bool:
        current = exchanges.value
        return (
            generation == conversation_generation.value
            and (actions is None or actions.folder().root == folder.root)
            and number < len(current)
            and current[number] is pending
        )

    def accepted(turn_id: str) -> None:
        nonlocal pending
        current = exchanges.value
        pending = dataclasses.replace(pending, turn=turn_id)
        exchanges.value = (*current[:number], pending, *current[number + 1 :])

    project = matsya_work.connected_session(folder) if folder is not None else None
    turn_id = job_id = None
    if project is not None:
        found, turn_id, job_id = _turn_answer(
            folder, project, pending.question, standing, accepted
        )
    else:
        found = matsya_client.ask_cited(pending.question, session)
    if not standing():
        return
    status = matsya_work.read_job(project, job_id) if job_id is not None else None
    if not standing():
        return
    if turn_id is not None and not matsya_work.session_current(folder, project):
        message = "The connected Matsya session changed while this question was being read."
        found, turn_id, job_id = matsya_client.Cited(message, (), ()), None, None
    if found is None:
        return
    current = exchanges.value
    answered = Exchange(
        pending.question, found.answer, found.passages, found.citations, turn=turn_id
    )
    exchanges.value = (*current[:number], answered, *current[number + 1 :])
    if job_id is not None:
        register_job(job_id, status)


# --- a search, a connection and a passage discussed ---


def search_last() -> None:
    """The task of a search, run off the page's thread: the last search
    sent, in its collection, by `matsya_work.search`, its passages written
    into its exchange as citations of retrieved passages; a search the
    client answered with no passage keeps the client's sentence."""
    held = exchanges.value
    numbers = [n for n, exchange in enumerate(held) if exchange.kind == "search"]
    if not numbers or held[numbers[-1]].answer is not None:
        return
    number = numbers[-1]
    asked_for = held[number]
    scope = None if asked_for.scope in (None, ALL_COLLECTIONS) else asked_for.scope
    passages, refusal = matsya_work.search(asked_for.question, scope)
    names = tuple(
        f"{passage.get('path')} — {passage['heading']}"
        if passage.get("heading")
        else str(passage.get("path"))
        for passage in passages
    )
    done = dataclasses.replace(
        asked_for,
        answer=client_sentence(refusal) if refusal else "",
        passages=names,
        citations=tuple(passages),
    )
    current = exchanges.value
    if number < len(current) and current[number] == asked_for:
        exchanges.value = (*current[:number], done, *current[number + 1 :])


def searched_citation(passage: dict) -> Citation:
    """A retrieved passage of a search as a citation: its text the
    quotation, and its collection, path and page its place."""
    location = passage.get("location") if isinstance(passage.get("location"), dict) else {}
    page = location.get("page")
    place = [str(passage[key]) for key in ("corpus", "path") if passage.get(key)]
    if page is not None:
        place.append(f"p. {page}")
    text_found = passage.get("text") if isinstance(passage.get("text"), str) else ""
    return Citation(PASSAGE, quote=text_found, source=" · ".join(place) or None)


def discuss(name: str, quote: str | None) -> None:
    """`Discuss`: the passage's quotation and name put in the composer's
    field as the start of a question, the kind of request `Ask`."""
    kind.value = ASK
    draft.value = f"“{quote}” ({name}) " if quote else f"{name} "


def connect(actions) -> None:
    """`Connect this folder to Matsya` (amendment 06 §2 items 3 and 14; D-1):
    unit G4's `matsya_work.connect`; the page reads the context again, so
    that the chips name the new session, and a refusal is the client's
    sentence."""
    held, refusal = matsya_work.connect(actions.folder())
    connect_refusal.value = client_sentence(refusal) if refusal else refusal
    if held is not None:
        connections.value = connections.value + 1


# --- the two steps of a build ---


def _set_build(number: int, **changes) -> None:
    """Replaces fields of the build's `BuildView`."""
    held = builds.value.get(number, BuildView())
    builds.value = {**builds.value, number: held._replace(**changes)}


def build_last(actions, number: int | None = None) -> None:
    """Read the session and capture the declaration before any new text is sent."""
    numbers = [n for n, exchange in enumerate(exchanges.value) if exchange.kind == "build"]
    if actions is None or not numbers:
        return
    if number is None:
        number = numbers[-1]
        if number in builds.value:
            return
    folder = actions.folder()
    session = matsya_work.connected_session(folder)
    if session is None:
        _set_build(number, refusal=NOT_CONNECTED_SENTENCE)
        return
    exchange = exchanges.value[number]
    source = actions.source()
    try:
        history = matsya_work.reviewed_entries(folder, session)
    except (OSError, ValueError) as error:
        if actions.folder().root == folder.root and exchanges.value[number:number + 1] == (exchange,):
            _set_build(number, refusal=str(error))
        return
    if actions.folder().root != folder.root or exchanges.value[number:number + 1] != (exchange,):
        return
    previous = builds.value.get(number, BuildView())
    if previous.restored:
        question = previous.prepared.record["prompt"]
        exchange = dataclasses.replace(exchange, question=question)
        current = exchanges.value
        exchanges.value = (*current[:number], exchange, *current[number + 1:])
    builds.value = {**builds.value, number: BuildView(
        history=history, source=source, session=session, root=folder.root
    )}
    prepare_build(actions, number, None)


def prepare_build(actions, number: int, choice: str | None) -> None:
    """Capture the reviewed file versions and the new entry."""
    folder = actions.folder()
    view = builds.value.get(number, BuildView())
    if view.session is None or view.history is None or folder.root != view.root:
        return
    exchange = exchanges.value[number]
    try:
        prepared = matsya_work.prepare(
            folder, view.source, TARGETS[exchange.scope], view.session, 0,
            actions.buffers(), choice, history=view.history, prompt=exchange.question,
        )
    except (OSError, ValueError) as error:
        _set_build(number, refusal=str(error))
        return
    if actions.folder().root == folder.root and exchanges.value[number:number + 1] == (exchange,):
        _set_build(number, prepared=prepared, choice=choice, refusal=None)


def submit_build(actions, number: int) -> None:
    """Send the reviewed text and inputs, and show the accepted job."""
    folder = actions.folder()
    view = builds.value.get(number, BuildView())
    if (view.session is None or folder.root != view.root or view.prepared is None
        or view.prepared.path is None or view.job or view.busy):
        return
    exchange = exchanges.value[number]
    _set_build(number, busy=True, refusal=None)
    review_again = False
    try:
        work = matsya_work.submit(folder, view.prepared.path, view.session, view.prepared.record)
        accepted = work.record["accepted"]
        if accepted is None:
            refusal = client_sentence(work.record["warning"]) or matsya_client.NO_ANSWER
            review_again = "the last entry the request reviewed:" in work.record["warning"]
            answer = None
        else:
            refusal = None
            answer = matsya_work.follow(work.record)
    except (OSError, ValueError) as error:
        accepted, answer, refusal = None, None, str(error)
        review_again = isinstance(error, matsya_work.ReviewRequired)
    if actions.folder().root != folder.root or exchanges.value[number:number + 1] != (exchange,):
        return
    if matsya_work.connected_session(folder) != view.session:
        _set_build(number, busy=False, review_again=True,
                   refusal="The Matsya connection changed. Prepare the build again.")
        return
    _set_build(number, job=accepted, refusal=refusal, busy=False, review_again=review_again)
    if accepted:
        register_job(accepted, answer)


def queue_submission(number: int) -> None:
    """Start submission on the background task for this conversation."""
    if submission.value is None:
        submission.value = (conversation_generation.value, number)


def submit_requested(actions, request) -> None:
    if actions is None or request is None:
        return
    generation, number = request
    try:
        if generation == conversation_generation.value:
            submit_build(actions, number)
    finally:
        if submission.value == request:
            submission.value = None


def restore_build_reviews(
    folder: model.Folder, session: matsya_work.Session, entries: list[dict]
) -> None:
    """Offer to resume an earlier reviewed submission using its original delivery."""
    generation = conversation_generation.value
    levels = {value: name for name, value in TARGETS.items()}
    for prepared, history in matsya_work.pending_builds(folder, session, entries):
        if generation != conversation_generation.value or not matsya_work.session_current(
            folder, session
        ):
            return
        if any(view.prepared is not None and view.prepared.path == prepared.path
               for view in builds.value.values()):
            continue
        level = levels.get(prepared.record["target"])
        if level is None:
            continue
        number = len(exchanges.value)
        _set_build(number, prepared=prepared, history=history, session=session,
                   root=folder.root, restored=True)
        exchanges.value = (*exchanges.value, Exchange(
            "Previously reviewed build", kind="build", scope=level
        ))


# --- the citations ---


def _copies(root: Path) -> dict:
    """The saved copies under the folder's `model.OUTPUT_FOLDER`, each
    copy's path from the folder by the identifier of the job its
    `record.json` names, the last by name where several hold one job."""
    output = root / model.OUTPUT_FOLDER
    found = {}
    for copy in sorted(output.iterdir()) if output.is_dir() else ():
        record = copy / "record.json"
        if copy.name.startswith(".") or not record.is_file():
            continue
        held = json.loads(record.read_text(encoding="utf-8"))
        if isinstance(held, dict) and isinstance(held.get("id"), str):
            found[held["id"]] = f"{model.OUTPUT_FOLDER}/{copy.name}"
    return found


def _placed(name: str) -> str:
    """The path in a saved copy of the returned file the service names
    `name`, as the client's `job files` places it: a stage file `<key>.bl`
    at `declaration/stages/<key>/<key>.bl`, any other file at its name under
    `declaration/`."""
    held = PurePosixPath(name)
    if held.suffix == ".bl" and len(held.parts) == 1:
        return f"{model.FACTORY_FOLDER}/stages/{held.stem}/{name}"
    return f"{model.FACTORY_FOLDER}/{name}"


def _line(location: dict) -> int | None:
    """The line, counted from one, a citation's location names, None where
    it names none."""
    for key in ("line", "start_line"):
        if isinstance(location.get(key), int):
            return location[key]
    return None


def resolve(root: Path, citation: dict) -> Citation:
    """The destination of the citation record `citation` in the model
    folder at `root` (amendment 06 §2 item 6): a retrieved passage of the
    service's index or of a guide opens its quotation, with its path and
    its place; a job's returned file opens in the folder's saved copy of
    that job, `not downloaded` where the folder holds none; a path that
    names a file of the folder opens that file at the line the location
    names; any other destination is `unavailable`, and no path is invented
    for it."""
    identity = citation.get("identity") if isinstance(citation.get("identity"), dict) else {}
    location = citation.get("location") if isinstance(citation.get("location"), dict) else {}
    path = citation.get("path") if isinstance(citation.get("path"), str) else None
    quote = citation.get("quote") if isinstance(citation.get("quote"), str) else None
    source = identity.get("source")
    if source in ("index", "guide") and quote:
        page = location.get("page")
        place = [part for part in (path, f"p. {page}" if page is not None else None) if part]
        return Citation(PASSAGE, quote=quote, source=" · ".join(place) or None)
    if source == "job":
        job, output = location.get("job"), location.get("output")
        copy = _copies(root).get(job) if isinstance(job, str) else None
        if copy is None or not isinstance(output, str):
            return Citation(UNAVAILABLE, state=NOT_DOWNLOADED)
        placed = f"{copy}/{_placed(output)}"
        if (root / placed).is_file():
            return Citation(COPY, path=placed, line=_line(location))
        return Citation(UNAVAILABLE, state=UNAVAILABLE)
    if path is not None:
        target = (root / path).resolve()
        if target.is_file() and target.is_relative_to(root.resolve()):
            return Citation(FILE, path=path, line=_line(location))
    return Citation(UNAVAILABLE, state=UNAVAILABLE)


# --- the five parts of a job's result ---


def _texts(value) -> tuple[str, ...]:
    """The sentences of a value the service gives: a text; a mapping's
    first text among its usual keys; or a list's texts, in order."""
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, dict):
        for key in ("text", "sentence", "comment", "question", "message", "summary", "reason"):
            if isinstance(value.get(key), str) and value[key].strip():
                return (value[key],)
        return ()
    if isinstance(value, list):
        return tuple(text for item in value for text in _texts(item))
    return ()


def _count(found: tuple) -> str:
    """A count in a word: `none`, or the number."""
    return str(len(found)) if found else "none"


def _prose_disagreements(name: str, check) -> tuple[str, ...]:
    if not isinstance(check, dict):
        return ()
    unavailable = check.get("unavailable")
    if isinstance(unavailable, dict):
        reason = _texts(unavailable.get("reason"))
        return (f"{name} unavailable" + (f" ({reason[0]})" if reason else ""),)
    if check.get("agrees") is not False:
        return ()
    headings = {}
    for report in check.get("reports") or ():
        items = report.get("items") if isinstance(report, dict) else None
        if isinstance(items, dict):
            for heading, finding in items.items():
                if isinstance(finding, dict) and finding.get("agrees") is False:
                    quotes = headings.setdefault(heading, {})
                    quotes.update(dict.fromkeys(_texts(finding.get("quotes"))))
    if not headings:
        return (f"{name} reports a disagreement.",)
    return tuple(
        f"{name} disagrees on {heading}." + (" " + " ".join(quotes) if quotes else "")
        for heading, quotes in headings.items()
    )


def _written_files(product: dict) -> dict:
    """The service's latest available writing, with its older fallback."""
    writing = product.get("available_writing", product.get("last_cycle"))
    files = writing.get("files") if isinstance(writing, dict) else None
    return files if isinstance(files, dict) else {}


def _can_download(job: dict) -> bool:
    """A job can return a report and record even without a declaration."""
    return isinstance(job.get("result"), dict) or isinstance(job.get("record"), dict)


def _declaration_absent(job: dict) -> bool:
    product = job.get("result")
    if not isinstance(product, dict):
        return False
    if "available_writing" not in product and "last_cycle" not in product:
        return False
    return all(name == "note.md" for name in _written_files(product))


def parts(view: JobView) -> tuple[Part, ...]:
    """The service's results, native construction, and numerical checks."""
    job = view.job or {}
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    record = job.get("record") if isinstance(job.get("record"), dict) else {}
    native_keys = (
        "last_completed_comparison", "last_cycle", "paper_source_check",
        "paper_form_check", "available_writing",
    )
    native = any(key in result for key in native_keys)
    product = result if native else record
    last = product.get("last_cycle")
    last = last if isinstance(last, dict) else {}

    # Older responses supplied `result.comparison` or a separate record.
    comparison = result.get("comparison") if not native else None
    if isinstance(comparison, dict):
        converged = comparison.get("converged")
        differences = _texts(comparison.get("differences"))
    else:
        comparison = product.get("last_completed_comparison") or last.get("comparison")
        converged = comparison.get("equal") if isinstance(comparison, dict) else None
        first = comparison.get("first_difference") if isinstance(comparison, dict) else None
        differences = _texts(first) or ((json.dumps(first, ensure_ascii=False),) if first else ())
    if not isinstance(converged, bool):
        converged = None
    words = {True: "converged", False: "not converged", None: "unavailable"}

    source_check = product.get("paper_source_check")
    form_check = product.get("paper_form_check")
    judging = last.get("judging")
    comments = _prose_disagreements("Source comparison", source_check)
    comments += _prose_disagreements("Prose comparison", judging)
    if isinstance(form_check, dict) and form_check.get("passed") is False:
        comments += _texts(form_check.get("findings")) or ("Model prose failed the form check.",)
    if last.get("citations_supported") is False:
        comments += ("One or more quotations are missing or unsupported by the model prose.",)
    if not native:
        comments += _texts(result.get("comments")) + _texts(source_check) + _texts(form_check)
        comments += _texts(judging)
    has_prose = bool(comments) or any(
        check.get(key) is True
        for check, key in ((source_check, "agrees"), (judging, "agrees"), (form_check, "passed"))
        if isinstance(check, dict)
    )
    if not native:
        has_prose |= "comments" in result

    questions = _texts(product.get("questions")) or _texts(result.get("questions"))
    unresolved = last.get("unresolved_note")
    if unresolved is True:
        note = _texts(_written_files(product).get("note.md"))
        detail = note[0] if note else "The service did not provide the note text."
        questions += (f"The writer's note marks unresolved assumptions. {detail}",)
    has_assumptions = (
        bool(questions) or unresolved is False or "questions" in result or "questions" in product
    )
    inspected = view.inspected
    if inspected is None:
        construction = Part(PART_NAMES[3], NOT_DOWNLOADED)
    else:
        notes = tuple(inspected.missing) + tuple(inspected.construction)
        notes += tuple(f"External terminal input {entry}" for entry in inspected.terminal_inputs)
        built = inspected.shown is not None and not inspected.missing
        construction = Part(PART_NAMES[3], "constructed" if built else "refused", notes)
    return (
        Part(PART_NAMES[0], words[converged], differences if converged is False else ()),
        Part(PART_NAMES[1], _count(comments) if has_prose else UNAVAILABLE, comments),
        Part(PART_NAMES[2], _count(questions) if has_assumptions else UNAVAILABLE, questions),
        construction,
        Part(PART_NAMES[4], "not run"),
    )


def _ended(job: dict | None) -> bool:
    """Whether the job stopped running, even if it returned no products."""
    if not isinstance(job, dict):
        return False
    state = job.get("state")
    if state in ("queued", "running"):
        return False
    if state in (
        "converged", "not_converged", "needs_input", "cancelled", "failed", "interrupted"
    ):
        return True
    return isinstance(job.get("result"), dict) or isinstance(job.get("record"), dict)


def job_name(job_id: str) -> str:
    """The name of a job on the page, `job <n>`, its number in its session
    as the service's label gives it, else its identifier."""
    job = jobs.value.get(job_id, JobView()).job or {}
    label = job.get("label") if isinstance(job.get("label"), dict) else {}
    number = label.get("number")
    return f"job {number}" if number else job_id


def _set_job(job_id: str, **changes) -> None:
    """Replaces fields of the job's `JobView`."""
    held = jobs.value.get(job_id, JobView())
    jobs.value = {**jobs.value, job_id: held._replace(**changes)}


def register_job(job_id: str, answer: dict | None = None) -> None:
    """Show one card for an accepted job regardless of how it was started."""
    if answer is not None or job_id not in jobs.value:
        _set_job(job_id, job=answer)
    if not any(exchange.job == job_id for exchange in exchanges.value):
        exchanges.value = (*exchanges.value, Exchange("", kind="job", job=job_id))


def recover_jobs(folder: model.Folder, generation: int | None = None) -> None:
    """Read the connected project's conversation and jobs from Matsya."""
    session = matsya_work.connected_session(folder)
    if session is None:
        return
    if generation is None:
        generation = conversation_generation.value

    def standing() -> bool:
        return (
            generation == conversation_generation.value
            and matsya_work.session_current(folder, session)
        )

    held = matsya_work.read_session(session, folder)
    if generation != conversation_generation.value:
        return
    remote_history_unavailable.value = held is None
    if held is None or not standing():
        return
    copies = _copies(folder.root)
    job_ids = {
        job["id"]: None for job in held.get("jobs") or ()
        if isinstance(job, dict) and isinstance(job.get("id"), str) and job["id"]
    }
    local_turns = {}
    for record in matsya_work.records(folder, session):
        kind = record.get("kind")
        accepted = record.get("accepted")
        job_id = accepted if kind == "job" else record.get("started_job")
        if isinstance(job_id, str) and job_id:
            job_ids.setdefault(job_id, None)
        if kind == "turn" and isinstance(accepted, str):
            local_turns[accepted] = record.get("question")
    entries = {
        entry["number"]: entry["text"] for entry in held.get("entries") or ()
        if isinstance(entry, dict)
        and type(entry.get("number")) is int
        and isinstance(entry.get("text"), str)
    }
    known = {exchange.turn for exchange in exchanges.value if exchange.turn}
    turn_ids = dict.fromkeys(
        turn_id for turn_id in (*(held.get("turns") or ()), *local_turns)
        if isinstance(turn_id, str) and turn_id not in known
    )
    for turn_id in turn_ids:
        turn = matsya_work.read_turn(session, turn_id)
        if not standing():
            return
        if turn is None or turn.get("state") != "finished":
            continue
        job_id = _job_started(turn)
        if job_id is not None:
            job_ids.setdefault(job_id, None)
        found = matsya_client.read_turn(turn) or matsya_client.Cited(matsya_client.UNREAD, (), ())
        entry = turn.get("question")
        question = entries.get(entry) if type(entry) is int else None
        question = question or local_turns.get(turn_id)
        if isinstance(question, str) and not any(e.turn == turn_id for e in exchanges.value):
            exchanges.value = (
                *exchanges.value,
                Exchange(question, found.answer, found.passages, found.citations, turn=turn_id),
            )
    for job_id in job_ids:
        answer = matsya_work.read_job(session, job_id)
        if not standing():
            return
        # A failed membership read must not attach an unknown job.
        if answer is None:
            continue
        view = jobs.value.get(job_id, JobView())
        copy = view.copy or copies.get(job_id)
        inspected = view.inspected
        if copy is not None and inspected is None:
            inspected = returned.inspect(folder, copy)
        if not standing():
            return
        _set_job(job_id, copy=copy, inspected=inspected)
        register_job(job_id, answer)
    if standing():
        restore_build_reviews(folder, session, held.get("entries") or [])


# The interval and limit for reading current jobs.
FOLLOW_SECONDS = 5.0
FOLLOW_READINGS = 720


def unfinished_jobs() -> tuple[str, ...]:
    """The displayed jobs whose observation is still active."""
    return tuple(
        exchange.job
        for exchange in exchanges.value
        if exchange.kind == "job" and not _ended(jobs.value.get(exchange.job, JobView()).job)
    )


def follow_jobs(
    folder: model.Folder, followed: tuple[str, ...], generation: int | None = None
) -> None:
    """Observe jobs of the same project session until their state changes."""
    session = matsya_work.connected_session(folder) if followed else None
    if session is None:
        return
    if generation is None:
        generation = conversation_generation.value

    def standing() -> bool:
        return (
            generation == conversation_generation.value
            and matsya_work.session_current(folder, session)
            and unfinished_jobs() == followed
        )

    for _ in range(FOLLOW_READINGS):
        time.sleep(FOLLOW_SECONDS)
        if not standing():
            return
        for job_id in followed:
            answer = matsya_work.read_job(session, job_id)
            if not standing():
                return
            if answer is not None and answer != jobs.value.get(job_id, JobView()).job:
                _set_job(job_id, job=answer)


def discuss_job(folder: model.Folder, job_id: str) -> None:
    """`Discuss` on a job's message: the job selected as the one the
    project session's conversation discusses, by unit G2's
    `matsya_work.discuss`, which checks first that the job belongs to the
    selected session on the effective service; a refusal is its sentence."""
    session = matsya_work.connected_session(folder)
    if session is None:
        _set_job(job_id, refusal=NOT_CONNECTED_SENTENCE)
        return
    found = matsya_work.discuss(session, job_id)
    if found.refusal is not None:
        _set_job(job_id, refusal=client_sentence(found.refusal))
        return
    discussed.value = job_id
    _set_job(job_id, refusal=None)


def download(folder: model.Folder, job_id: str) -> None:
    """`Download returned files`: one saved copy of the job's model folder
    by unit G2's `matsya_work.download`, then the copy constructed as a
    model of its own by unit G3's `returned.inspect`; a refusal is the
    adapter's sentence."""
    session = matsya_work.connected_session(folder)
    if session is None:
        _set_job(job_id, refusal=NOT_CONNECTED_SENTENCE)
        return
    found = matsya_work.download(folder, session, job_id)
    if found.refusal is not None:
        _set_job(job_id, refusal=client_sentence(found.refusal))
        return
    _set_job(job_id, copy=found.path, inspected=returned.inspect(folder, found.path), refusal=None)


def _adoption_refusal(folder: model.Folder, job_id: str) -> str | None:
    session = matsya_work.connected_session(folder)
    if session is None:
        return NOT_CONNECTED_SENTENCE
    if not matsya_work.session_current(folder, session):
        return "The configured Matsya service does not match this project."
    found = matsya_work.membership(session, job_id, "adopted")
    return client_sentence(found.refusal) if found.refusal else None


def review_replacement(folder: model.Folder, job_id: str, buffers: dict) -> None:
    """Review the returned files at the destinations the adoption will use."""
    view = jobs.value.get(job_id, JobView())
    if view.copy is None:
        return
    refusal = _adoption_refusal(folder, job_id)
    if refusal:
        _set_job(job_id, refusal=refusal)
        return
    planned = returned.plan(folder, view.copy, buffers=buffers, changed_only=True)
    _set_job(job_id, plan=planned, adoption=None, refusal=None)


def replace(folder: model.Folder, job_id: str, buffers: dict) -> None:
    """Recheck membership and apply the reviewed plan."""
    view = jobs.value.get(job_id, JobView())
    if view.plan is None:
        return
    refusal = _adoption_refusal(folder, job_id)
    if refusal:
        _set_job(job_id, plan=None, refusal=refusal)
        return
    _set_job(job_id, adoption=returned.adopt(folder, view.plan, buffers), plan=None, refusal=None)


def recover_replacement(
    folder: model.Folder, job_id: str, buffers: dict, *, finish: bool = False
) -> None:
    """Restore locally or finish writing the same reviewed copy."""
    adoption = jobs.value.get(job_id, JobView()).adoption
    if adoption is None or adoption.id is None or adoption.record is None:
        return
    if finish:
        refusal = _adoption_refusal(folder, job_id)
        if refusal:
            _set_job(job_id, refusal=refusal)
            return
        outcome = returned.complete(folder, adoption.id, buffers)
    else:
        for entry in adoption.record["files"]:
            destination = entry["destination"]
            if entry["outcome"] == "written" and destination in buffers:
                _set_job(job_id, refusal=f"{destination} holds unsaved changes in the editor")
                return
        outcome = returned.restore(folder, adoption.id)
    if outcome.record is None:
        outcome = outcome._replace(record=adoption.record)
    _set_job(job_id, adoption=outcome, refusal=None)


# --- the drawing ---


@solara.component
def CitationItem(
    number: int, place: int, passage: str, citation: Citation, actions, text_button=None
):
    """One citation of an answer, one row: the Codicon of its kind and the
    passage as the service names it, `.bl-matsya-passage`; a destination
    that can be opened is a text button (`OpenedCitation`), one that cannot
    be resolved is text followed by its state."""
    with rv.Html(tag="li", class_="bl-matsya-citation", attributes={"data-kind": citation.kind}):
        if citation.kind == UNAVAILABLE or actions is None:
            with rv.Html(tag="span", class_="bl-matsya-cited"):
                icons.codicon(icons.CODICONS["cited unavailable"])
                rv.Html(tag="span", class_="bl-matsya-passage bl-code-small", children=[passage])
                if citation.state:
                    rv.Html(tag="span", class_="bl-matsya-cited-state", children=[citation.state])
        else:
            OpenedCitation(number, place, passage, citation, actions, text_button)


@solara.component
def OpenedCitation(
    number: int, place: int, passage: str, citation: Citation, actions, text_button=None
):
    """A citation whose destination opens: a file of the folder at its
    line, a returned file in its saved copy, or a passage, whose quotation
    and place open below its row and close again."""
    key = (number, place)
    shown = key in opened.value

    def act():
        if citation.kind == PASSAGE:
            opened.value = opened.value - {key} if shown else opened.value | {key}
        elif citation.kind == COPY:
            # a returned file opens its saved copy, the model it belongs to
            actions.open_copy(citation.path.split(f"/{model.FACTORY_FOLDER}/", 1)[0])
        else:
            actions.open_file(citation.path, citation.line)

    control = "cited passage" if citation.kind == PASSAGE else "cited file"
    hover = None
    if citation.path:
        hover = citation.path + (f", line {citation.line}" if citation.line else "")
    attributes = {"type": "button", **({"title": hover} if hover else {})}
    if citation.kind == PASSAGE:
        attributes["aria-expanded"] = "true" if shown else "false"
    with rv.Html(
        tag="button", class_="bl-text-button bl-matsya-cited", attributes=attributes
    ) as button:
        icons.codicon(icons.CODICONS[control])
        rv.Html(tag="span", class_="bl-matsya-passage bl-code-small", children=[passage])
    rv.use_event(button, "click", lambda *_: act())
    if citation.kind == PASSAGE and shown:
        with rv.Html(tag="div", class_="bl-matsya-quote"):
            rv.Html(tag="div", class_="bl-matsya-quote-text", children=[citation.quote or ""])
            if citation.source:
                rv.Html(
                    tag="div",
                    class_="bl-matsya-quote-source bl-code-small",
                    children=[citation.source],
                )
            if text_button is not None:
                with rv.Html(tag="div", class_="bl-matsya-actions"):
                    ActionButton(
                        text_button,
                        DISCUSS,
                        lambda: discuss(passage, citation.quote),
                        "bl-matsya-discuss",
                    ).key(DISCUSS)


@solara.component
def ActionButton(text_button, words: str, act, classes: str, icon: str | None = None):
    """One action of the column, the page's text button `text_button`
    (`app.TextButton`), drawn by a component of its own so that the
    action's hooks stand in the same order at every drawing."""
    text_button(words, act, classes, icon=icon)


@solara.component
def ExchangeItem(number: int, exchange: Exchange, text_button=None, actions=None):
    """One question in its faintly bounded box, with Matsya's answer as
    plain text under the speaker `Matsya`, which is spoken and not drawn,
    and its citations, one row each, or the line `Answering` while Matsya
    answers (spec 0.4 §5.6; design pass 16 §3 rules 3 and 4)."""
    with rv.Html(tag="li", class_="bl-matsya-exchange"):
        rv.Html(tag="div", class_="bl-matsya-question", children=[exchange.question])
        if exchange.answer is None:
            rv.Html(tag="div", class_="bl-matsya-pending", children=[ANSWERING])
            return
        rv.Html(tag="div", class_="bl-matsya-speaker", children=["Matsya"])
        rv.Html(tag="div", class_="bl-matsya-answer", children=[exchange.answer])
        if not exchange.passages:
            return
        root = actions.folder().root if actions is not None else None
        records = list(exchange.citations) + [{}] * (
            len(exchange.passages) - len(exchange.citations)
        )
        with rv.Html(tag="ul", class_="bl-matsya-citations"):
            for place, (passage, record) in enumerate(zip(exchange.passages, records)):
                citation = (
                    resolve(root, record)
                    if root is not None
                    else Citation(UNAVAILABLE, state=UNAVAILABLE)
                )
                CitationItem(number, place, passage, citation, actions).key(str(place))


def _meta(job: dict) -> str:
    """The line under a job's name: its iteration, the revision it read and
    its configuration, each where the service gives it."""
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    record = job.get("record") if isinstance(job.get("record"), dict) else {}
    progress = job.get("progress")
    progress = progress if isinstance(progress, dict) else {}
    cycles = result.get("cycles_run", record.get("cycles_run", progress.get("cycle")))
    revision = job.get("revision", job.get("reviewed_through"))
    configuration = job.get("configuration_id")
    label = job.get("label")
    target = label.get("target") if isinstance(label, dict) else None
    step = progress.get("step")
    found = [
        str(target).capitalize() if isinstance(target, str) else None,
        str(step).replace("_", " ") if isinstance(step, str) else None,
        f"iteration {cycles}" if cycles is not None else None,
        f"revision {revision}" if revision is not None else None,
        f"configuration {configuration[:12] if configuration else DEFAULT}",
    ]
    return " · ".join(part for part in found if part)


@solara.component
def JobItem(job_id: str, text_button, actions):
    """A job's message (design pass 16 §3 rule 5): its number in Code name
    and its state; its iteration, revision and configuration; once the job
    holds a result, its five parts apart; and the actions on its returned
    files, or the plan of an adoption with `Replace model files` and
    `Cancel`, and what an adoption wrote."""
    view = jobs.value.get(job_id, JobView())
    job = view.job or {}
    label = job.get("label") if isinstance(job.get("label"), dict) else {}
    state = job.get("state") or label.get("state") or UNKNOWN
    with rv.Html(tag="li", class_="bl-matsya-exchange"):
        with rv.Html(tag="div", class_="bl-matsya-job", attributes={"data-job": job_id}):
            with rv.Html(tag="div", class_="bl-matsya-job-line"):
                rv.Html(
                    tag="span",
                    class_="bl-code-name",
                    children=[job_name(job_id)],
                )
                rv.Html(tag="span", class_="bl-small", children=[str(state)])
            if view.job is not None:
                rv.Html(
                    tag="div", class_="bl-matsya-job-meta bl-code-small", children=[_meta(job)]
                )
            declaration_absent = _declaration_absent(job)
            if _ended(view.job):
                if declaration_absent:
                    rv.Html(
                        tag="div",
                        class_="bl-small",
                        children=["A report is available. The job returned no declaration files."],
                    )
                with rv.Html(tag="dl", class_="bl-matsya-parts"):
                    for part in parts(view):
                        with rv.Html(
                            tag="div", class_="bl-matsya-part", attributes={"data-part": part.name}
                        ):
                            rv.Html(tag="dt", class_="bl-matsya-part-name", children=[part.name])
                            rv.Html(tag="dd", class_="bl-matsya-part-value", children=[part.value])
                            for detail in part.details:
                                rv.Html(
                                    tag="dd", class_="bl-matsya-part-detail", children=[detail]
                                )
            refusal = view.refusal or job.get("error")
            if isinstance(refusal, str) and refusal:
                rv.Html(tag="div", class_="bl-matsya-refusal", children=[refusal])
            if text_button is None or actions is None or not _ended(view.job):
                return
            folder = actions.folder()
            if view.plan is not None:
                PlanItem(job_id, view.plan, text_button, actions)
                return
            with rv.Html(tag="div", class_="bl-matsya-actions"):
                if discussed.value != job_id:
                    ActionButton(
                        text_button,
                        DISCUSS,
                        lambda: discuss_job(folder, job_id),
                        "bl-matsya-discuss-job",
                    ).key(f"{DISCUSS} job")
                if view.copy is None and _can_download(job):
                    ActionButton(
                        text_button,
                        DOWNLOAD,
                        lambda: download(folder, job_id),
                        "bl-matsya-download",
                        "download returned files",
                    ).key(DOWNLOAD)
                elif view.copy is not None:
                    ActionButton(
                        text_button,
                        OPEN_COPY,
                        lambda: actions.open_copy(view.copy),
                        "bl-matsya-open-copy",
                        "open returned files",
                    ).key(OPEN_COPY)
                    if not declaration_absent:
                        ActionButton(
                            text_button,
                            REPLACE,
                            lambda: review_replacement(folder, job_id, actions.buffers()),
                            "bl-matsya-replace",
                            "replace model files",
                        ).key(REPLACE)
            if view.adoption is not None:
                AdoptionItem(job_id, view.adoption, text_button, actions)


@solara.component
def PlanItem(job_id: str, planned, text_button, actions):
    """The plan of `Replace model files…` (amendment 06 §2 item 22): each
    file's destination and its line difference, the unsaved difference of
    an editor buffer where one stands, the refusals, and the two actions,
    `Replace model files`, absent while a refusal stands or no file
    differs, and `Cancel`."""
    folder = actions.folder()
    with rv.Html(tag="div", class_="bl-matsya-plan"):
        if not planned.files and not planned.refusals:
            rv.Html(tag="div", class_="bl-matsya-refusal", children=[NO_CHANGE])
        for entry in planned.files:
            with rv.Html(tag="div", class_="bl-matsya-plan-file"):
                rv.Html(
                    tag="div",
                    class_="bl-matsya-plan-destination bl-code-small",
                    children=[entry["destination"]],
                )
                if entry.get("difference"):
                    rv.Html(
                        tag="pre",
                        class_="bl-matsya-plan-difference bl-code-small",
                        children=[entry["difference"]],
                    )
                if entry.get("unsaved"):
                    rv.Html(
                        tag="pre",
                        class_="bl-matsya-plan-difference bl-code-small",
                        children=[entry["unsaved"]],
                    )
        for sentence in planned.refusals:
            rv.Html(tag="div", class_="bl-matsya-refusal", children=[sentence])
        with rv.Html(tag="div", class_="bl-matsya-actions"):
            if planned.files and not planned.refusals:
                words = ADOPT_FIRST if planned.first else REPLACE_NOW
                ActionButton(
                    text_button,
                    words,
                    lambda: replace(folder, job_id, actions.buffers()),
                    "bl-matsya-replace-now",
                    "replace model files",
                ).key(words)
            ActionButton(
                text_button, CANCEL, lambda: _set_job(job_id, plan=None), "bl-matsya-cancel"
            ).key(CANCEL)


@solara.component
def AdoptionItem(job_id: str, adoption, text_button, actions):
    """What an adoption answered: the files it wrote, its refusals, and,
    for an adoption recorded as adopted, `Commit…`, which opens the commit
    form with the adopted files alone (amendment 06 §2 item 23)."""
    with rv.Html(tag="div", class_="bl-matsya-adoption"):
        for path in adoption.changed:
            rv.Html(tag="div", class_="bl-matsya-adopted bl-code-small", children=[path])
        for sentence in adoption.refusals:
            rv.Html(tag="div", class_="bl-matsya-refusal", children=[sentence])
        state = adoption.record.get("state") if adoption.record is not None else None
        if state in ("stopped", "restore failed"):
            with rv.Html(tag="div", class_="bl-matsya-actions"):
                ActionButton(
                    text_button,
                    RESTORE,
                    lambda: recover_replacement(actions.folder(), job_id, actions.buffers()),
                    "bl-matsya-restore",
                ).key(RESTORE)
                if state == "stopped":
                    ActionButton(
                        text_button,
                        COMPLETE,
                        lambda: recover_replacement(
                            actions.folder(), job_id, actions.buffers(), finish=True
                        ),
                        "bl-matsya-complete",
                    ).key(COMPLETE)
        if state == "adopted":
            with rv.Html(tag="div", class_="bl-matsya-actions"):
                ActionButton(
                    text_button,
                    COMMIT,
                    lambda: actions.open_commit(adoption.record),
                    "bl-matsya-commit",
                ).key(COMMIT)


@solara.component
def SearchItem(number: int, exchange: Exchange, text_button, actions):
    """A search (amendment 06 §2 item 8): the query in its faintly bounded
    box, `Search sources` with its collection, then `Answering` while the
    service searches, or the client's sentence, or the passages, each a
    retrieved passage whose quotation opens below its row with `Discuss`."""
    with rv.Html(tag="li", class_="bl-matsya-exchange"):
        rv.Html(tag="div", class_="bl-matsya-question", children=[exchange.question])
        with rv.Html(tag="div", class_="bl-matsya-job-line bl-matsya-search"):
            rv.Html(
                tag="span",
                class_="bl-small",
                children=[f"{SEARCH} · {exchange.scope or ALL_COLLECTIONS}"],
            )
        if exchange.answer is None:
            rv.Html(tag="div", class_="bl-matsya-pending", children=[ANSWERING])
            return
        if exchange.answer:
            rv.Html(tag="div", class_="bl-matsya-refusal", children=[exchange.answer])
        with rv.Html(tag="ul", class_="bl-matsya-citations"):
            for place, (name, passage) in enumerate(zip(exchange.passages, exchange.citations)):
                CitationItem(
                    number, place, name, searched_citation(passage), actions, text_button
                ).key(str(place))


@solara.component
def ConnectItem(text_button, actions, context):
    """`Connect this folder to Matsya` (amendment 06 §2 items 3, 9 and 14),
    at the head of the conversation of a folder not connected, with what the
    connection sends, the folder's name and its `economics.md`, and the
    service it reaches, in one line under it, and the client's sentence
    where it refused."""
    folder = actions.folder()
    service = context.service if context is not None and context.service else UNKNOWN
    held = [folder.root.name]
    if (folder.root / "economics.md").is_file():
        held.append("economics.md")
    with rv.Html(tag="li", class_="bl-matsya-exchange bl-matsya-connect"):
        ActionButton(
            text_button,
            CONNECT,
            lambda: connect(actions),
            "bl-matsya-connect-button",
            "connect folder",
        ).key(CONNECT)
        rv.Html(
            tag="div",
            class_="bl-matsya-connect-sent bl-code-small",
            children=[" · ".join([*held, service])],
        )
        if connect_refusal.value:
            rv.Html(tag="div", class_="bl-matsya-refusal", children=[connect_refusal.value])


@solara.component
def BuildItem(number: int, exchange: Exchange, text_button, actions, context):
    """A build (design pass 16 §3 rule 6; decision SG4-7): the request in
    its faintly bounded box, then `Preparing` while the first step runs, or
    its refusal, or the material prepared: the kind and the level, the
    source with its number of files, the destination, each unsaved file
    with the three choices of unit G2, `Files`, which lists each file
    with the start of its fingerprint, and the one action `Build
    declaration`, which sends the reviewed inputs as they stand."""
    view = builds.value.get(number, BuildView())
    prepared = view.prepared
    with rv.Html(tag="li", class_="bl-matsya-exchange"):
        rv.Html(tag="div", class_="bl-matsya-question", children=[exchange.question])
        with rv.Html(tag="div", class_="bl-matsya-build", attributes={"data-build": str(number)}):
            if view.refusal:
                rv.Html(tag="div", class_="bl-matsya-refusal", children=[view.refusal])
            if prepared is None:
                if not view.refusal:
                    rv.Html(tag="div", class_="bl-matsya-pending", children=[PREPARING])
                return
            with rv.Html(tag="div", class_="bl-matsya-job-line"):
                rv.Html(tag="span", class_="bl-small", children=[f"{BUILD} · {exchange.scope}"])
            record = prepared.record
            if record is not None:
                source = record["source"]
                name = PurePosixPath(source["path"]).name if source else "Description only"
                rv.Html(
                    tag="div",
                    class_="bl-matsya-build-what bl-code-small",
                    children=[f"{name} · {len(record['files'])} files"],
                )
                service = record.get("server") or UNKNOWN
                rv.Html(
                    tag="div",
                    class_="bl-matsya-build-what bl-code-small",
                    children=[f"{service} · {DEFAULT}"],
                )
            for path in prepared.differences:
                with rv.Html(tag="div", class_="bl-matsya-build-unsaved bl-code-small"):
                    icons.codicon(icons.CODICONS["unsaved"])
                    rv.Html(tag="span", children=[path])
                    rv.Html(tag="span", class_="bl-matsya-chip-state", children=[UNSAVED])
            if prepared.differences and record is None:
                with rv.Html(tag="div", class_="bl-matsya-actions"):
                    for choice, words in CHOICE_WORDS.items():
                        ActionButton(
                            text_button,
                            words,
                            lambda choice=choice: prepare_build(actions, number, choice),
                            "bl-matsya-choice",
                        ).key(choice)
            elif not prepared.differences:
                for sentence in prepared.refusals:
                    rv.Html(tag="div", class_="bl-matsya-refusal", children=[sentence])
            if record is None:
                return
            with rv.Html(tag="details"):
                rv.Html(tag="summary", children=["Text and session history"])
                rv.Html(tag="div", class_="bl-matsya-answer", children=[record["prompt"]])
                entries = view.history or ()
                accepted = {entry.get("replies_to") for entry in entries
                            if entry["kind"] == "acceptance"}
                for entry in entries:
                    role = entry["kind"]
                    if role == "answer":
                        role += " · accepted" if entry["number"] in accepted else " · excluded from build"
                    elif role == "acceptance":
                        role += f" of answer {entry.get('replies_to')}"
                    rv.Html(tag="div", class_="bl-small",
                            children=[f"Entry {entry['number']} · {role}"])
                    rv.Html(tag="div", class_="bl-matsya-answer", children=[entry["text"]])
            if view.listed:
                with rv.Html(tag="ul", class_="bl-matsya-build-files"):
                    for entry in record["files"]:
                        with rv.Html(tag="li", class_="bl-code-small").key(entry["path"]):
                            with rv.Html(tag="details"):
                                rv.Html(tag="summary", children=[
                                    f"{entry['path']} · sent {entry['sent_sha256'][:12]}"
                                ])
                                rv.Html(tag="div", class_="bl-matsya-answer",
                                        children=[prepared.texts[entry["name"]]])
            if view.busy:
                rv.Html(tag="div", class_="bl-matsya-pending", children=["Submitting build"])
            with rv.Html(tag="div", class_="bl-matsya-actions"):
                ActionButton(
                    text_button,
                    FILES_SENT,
                    lambda: _set_build(number, listed=not view.listed),
                    "bl-matsya-files-sent",
                ).key(FILES_SENT)
                if view.review_again:
                    ActionButton(text_button, "Prepare again", lambda: build_last(actions, number),
                                 "bl-matsya-review-again").key("prepare again")
                elif view.job is None and not view.busy and submission.value is None:
                    ActionButton(
                        text_button,
                        "Resume submission" if view.restored else BUILD,
                        lambda: queue_submission(number),
                        "bl-matsya-submit",
                        "ask matsya",
                    ).key(BUILD)


@solara.component
def Chip(kind: str, value: str, state: str | None = None):
    """One chip of the composer's context: the Codicon of its kind, its
    value in Code small and its state in Small; its hover and its spoken
    name say its kind."""
    spoken = " ".join(part for part in (CHIP_KINDS[kind], value, state) if part)
    with rv.Html(
        tag="li",
        class_="bl-matsya-chip bl-code-small",
        attributes={"data-kind": kind, "title": CHIP_KINDS[kind], "aria-label": spoken},
    ):
        icons.codicon(icons.CODICONS[f"matsya {kind}"])
        if value:
            rv.Html(tag="span", class_="bl-matsya-chip-value", children=[value])
        if state:
            rv.Html(tag="span", class_="bl-matsya-chip-state", children=[state])


@solara.component
def Composer(context: Context, field, button, handle=None):
    """The composer (design pass 16 §3 rule 7; amendment 07 of spec 0.4):
    one bordered box holding the handle `composer` on its top edge, which
    `handle`, the page's `app.Handle`, draws and window.vue reads, a drag
    upward enlarging the field, none where `handle` is None; the context
    chips; the text area, one line when empty and growing with its text,
    Enter sending its text (`send`) and Shift+Enter beginning a line,
    Escape in it moving the focus to the conversation, which window.vue
    reads; and the foot row, which ends in the send control `Ask`, the
    Codicon `send` in a circle, filled while there is a question to send
    and waiting while Matsya answers."""
    with rv.Html(tag="div", class_="bl-matsya-row"):
        if handle is not None:
            handle("composer")
        with rv.Html(tag="ul", class_="bl-matsya-context", attributes={"aria-label": "Context"}):
            if context.source:
                Chip("source", context.source, UNSAVED if context.unsaved else SAVED)
            if context.session:
                Chip("session", context.session)
            else:
                Chip("session", "", NOT_CONNECTED)
            if context.job:
                Chip("job", context.job)
            Chip(
                "service",
                context.service or UNKNOWN,
                context.configuration[:12] if context.configuration else DEFAULT,
            )
        field(
            kind="area",
            value=draft.value,
            classes="bl-matsya-field",
            placeholder=COMPOSER_PLACEHOLDER,
            named=COMPOSER_NAME,
            continuous=True,
            submits=True,
            grows=True,
            event_entered=set_draft,
            event_submitted=send,
        )
        with rv.Html(tag="div", class_="bl-matsya-foot"):
            if len(KINDS) > 1:
                field(
                    kind="select",
                    value=kind.value,
                    options=list(KINDS),
                    classes="bl-matsya-kind",
                    named=KIND_NAME,
                    above=True,
                    event_entered=set_kind,
                )
            if kind.value == SEARCH:
                field(
                    kind="select",
                    value=collection.value,
                    options=list(COLLECTIONS),
                    classes="bl-matsya-collection",
                    named=COLLECTION_NAME,
                    above=True,
                    event_entered=set_collection,
                )
            if kind.value == BUILD:
                field(
                    kind="select",
                    value=target.value,
                    options=list(TARGETS),
                    descriptions=TARGET_FILES,
                    classes="bl-matsya-target",
                    named=TARGET_NAME,
                    above=True,
                    event_entered=set_target,
                )
            waits = ANSWERING if answering() else None
            action = "Prepare build" if kind.value == BUILD else kind.value
            button(
                "ask matsya",
                action,
                waits or (ASK_HOVER if kind.value == ASK else f"{action} (Enter)"),
                lambda: send(draft.value),
                "bl-matsya-ask",
                {"data-ready": "true" if draft.value.strip() and waits is None else "false"},
                disabled=waits is not None,
            )


@solara.component
def MatsyaWindow(
    session: str, field, button, text_button=None, context=None, actions=None, handle=None
):
    """Matsya's column (design pass 16): its head, 36 px from the window's
    top, level with the title bar, with the heading `Matsya`, Υ and the
    icon button `Fold Matsya`, the Codicon `close`, a fold button
    `.bl-fold` with data-fold `matsya`, which window.vue reads; and its
    body, the conversation and the composer. `field`, `button`,
    `text_button` and `handle` are the page's components `app.Field`,
    `app.ToolbarButton`, `app.TextButton` and `app.Handle`, `context` the
    composer's `Context` and `actions` the page's `Actions`, which
    `app.Page` passes; without `actions` no citation opens and no job is
    listed, and without `handle` the composer has no handle. `session`
    names the conversation the questions are asked in, a digest of the
    folder's path (spec 0.4 §6, decision 32)."""
    # the task that answers the last question, run in a thread off the
    # page's thread whenever a question is sent, as `app.Page` runs the
    # loop, so that the page stays live while Matsya answers
    solara.lab.use_task(
        lambda: answer_last(session, actions), dependencies=[asked.value], raise_error=False
    )
    # the task that searches the last search sent, off the page's thread
    solara.lab.use_task(search_last, dependencies=[searched.value], raise_error=False)
    # the task that prepares the last build requested, off the page's thread
    solara.lab.use_task(
        lambda: build_last(actions), dependencies=[requested.value], raise_error=False
    )
    pending_submission = submission.value
    solara.lab.use_task(
        lambda: submit_requested(actions, pending_submission),
        dependencies=[pending_submission],
        raise_error=False,
    )
    folder = actions.folder() if actions is not None else None
    root = str(folder.root) if folder is not None else None
    generation = conversation_generation.value
    connection = connections.value
    followed = unfinished_jobs() if folder is not None else ()
    solara.lab.use_task(
        lambda: follow_jobs(folder, followed, generation) if followed else None,
        dependencies=[root, generation, connection, followed],
        raise_error=False,
    )
    solara.lab.use_task(
        lambda: recover_jobs(folder, generation) if folder is not None else None,
        dependencies=[root, generation, connection],
        raise_error=False,
    )
    with rv.Html(tag="section", class_="bl-matsya"):
        with rv.Html(tag="div", class_="bl-head bl-matsya-head"):
            rv.Html(tag="h2", children=["Matsya"])
            rv.Html(tag="span", class_="bl-matsya-upsilon", children=["Υ"])
            with rv.Html(tag="span", class_="bl-head-actions"):
                # the fold button's click is window.vue's alone
                button(
                    "fold matsya",
                    "Fold Matsya",
                    "Fold Matsya",
                    lambda: None,
                    "bl-fold",
                    {"data-fold": "matsya"},
                )
        with rv.Html(tag="div", class_="bl-matsya-body"):
            with rv.Html(
                tag="ol",
                class_="bl-matsya-exchanges",
                attributes={"tabindex": "0", "aria-label": "Conversation", "aria-live": "polite"},
            ):
                if remote_history_unavailable.value:
                    rv.Html(
                        tag="li",
                        class_="bl-matsya-refusal",
                        children=["The connected Matsya session history could not be read."],
                    )
                if (
                    actions is not None
                    and text_button is not None
                    and matsya_work.project(actions.folder()) is None
                ):
                    ConnectItem(text_button, actions, context).key("connect")
                for number, exchange in enumerate(exchanges.value):
                    if exchange.kind == "search":
                        SearchItem(number, exchange, text_button, actions).key(f"search {number}")
                    elif exchange.kind == "job":
                        JobItem(exchange.job, text_button, actions).key(f"job {exchange.job}")
                    elif exchange.kind == "build":
                        BuildItem(number, exchange, text_button, actions, context).key(
                            f"build {number}"
                        )
                    else:
                        ExchangeItem(number, exchange, text_button, actions).key(str(number))
            shown = context or Context(service=matsya_client.service_address())
            Composer(
                shown._replace(job=job_name(discussed.value) if discussed.value else None),
                field,
                button,
                handle,
            )
