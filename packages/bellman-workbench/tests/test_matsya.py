"""The Matsya window of Bellman Workbench without a browser (model
interface specification 0.3, unit M): `matsya_client.ask`, the one
function by which the page reaches Matsya's service, run against the
stand-in of the client, `tests/matsya_stub.py`, which the fixture
`matsya_stub` names for every test of this folder; and the window's state
and component, rendered by Solara's test renderer. No test reaches the
service or reads the client's configuration.

The tests named `test_m_item_<n>_*` close the claims of the unit's
acceptance items (`spec_0.3-matsya-window.md` §5) that need no browser;
the page's tests in `test_page.py` close the rest. The tests named
`test_r_*` close unit R's two claims on Matsya that need no browser (spec
0.4 §6; review 10): the setting `off` names no client and is read once, and
the conversation is named by a digest of the folder's path. The other
tests cover a question that begins with a dash, the Bellman client command,
a malformed answer, a blank or malformed command variable, and a question
the operating system cannot pass to the client. They also check that
Workbench reuses the service's session identifier for a folder.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import shlex
import stat
import sys

import ipyvue
import solara
from workbench_support import MATSYA_STUB, STUB_PASSAGES, wait_until

from bellman_workbench import app, command, matsya_client, matsya_window

# a question, and the stand-in's answer to it in the conversation
# `portfolio-choice` with no model named
QUESTION = "What does a stage file denote?"
ANSWER = (
    "Υ reads the stage file into the operators 𝑉 ∘ g.\n"
    f"question: {QUESTION}\n"
    "session: portfolio-choice\n"
    "model: the client's default"
)


# --- the client function ---


def test_m_item_1_ask_answers_with_the_passages_the_service_names(monkeypatch):
    """A question asked in the conversation `portfolio-choice` is answered
    with the stand-in's text, character for character, its Greek and
    mathematical letters included: the text names the question, the
    session and the client's default model, since the Workbench names no
    model (D-M3); the two passages are the cited paths in the client's JSON
    answer. The answer unpacks as the pair `answer, passages`. The test's
    environment asks for Latin-1 (`PYTHONIOENCODING=latin-1`), so that
    the answer arrives whole only because `ask` asks the client for
    UTF-8."""
    monkeypatch.setenv("PYTHONIOENCODING", "latin-1")
    answer, passages = matsya_client.ask(QUESTION, "portfolio-choice")
    assert answer == ANSWER
    assert passages == STUB_PASSAGES


def test_m_item_2_a_silent_service_is_one_sentence_without_the_clients_words():
    """The client exits with status 1 and its own sentence on standard
    error, which names the service's address: the answer is the sentence
    NO_ANSWER with no passage, and nothing of the client's sentence is in
    it."""
    found = matsya_client.ask("Is the service silent?", "portfolio-choice")
    assert found == (matsya_client.NO_ANSWER, ())
    assert "Bellman service" not in found.answer


def test_m_item_2_an_absent_client_is_one_sentence(monkeypatch, tmp_path):
    """With the variable unset and a search path without `bellman-matsya`,
    `command()` finds no client and the answer is the sentence NO_CLIENT.
    A variable naming a program that
    does not exist is answered by the sentence naming the variable and
    not its text, which may hold a token; where the variable's first word
    assigns a token, `TOKEN=msy-secret`, that word is taken as the
    program, which is not found, and the token is not in the answer."""
    monkeypatch.delenv(matsya_client.COMMAND_VARIABLE)
    monkeypatch.setenv("PATH", str(tmp_path))
    _no_client_beside_the_interpreter(monkeypatch, tmp_path)
    assert matsya_client.command() is None
    assert matsya_client.ask(QUESTION, "portfolio-choice") == (
        matsya_client.NO_CLIENT.format(name="bellman-matsya"),
        (),
    )
    missing = shlex.quote(str(tmp_path / "no-such-client"))
    in_variable = (matsya_client.NO_CLIENT.format(name="in BELLMAN_WORKBENCH_MATSYA"), ())
    monkeypatch.setenv(matsya_client.COMMAND_VARIABLE, missing)
    assert matsya_client.ask(QUESTION, "portfolio-choice") == in_variable
    monkeypatch.setenv(matsya_client.COMMAND_VARIABLE, f"TOKEN=msy-secret {missing}")
    found = matsya_client.ask(QUESTION, "portfolio-choice")
    assert found == in_variable
    assert "msy-secret" not in found.answer


def _no_client_beside_the_interpreter(monkeypatch, tmp_path):
    """Points `sys.executable` into an empty folder of `tmp_path`, so that
    the client installed beside the interpreter running the tests, which
    `command()` looks for first, is not found."""
    interpreter = tmp_path / "interpreter"
    interpreter.mkdir(exist_ok=True)
    monkeypatch.setattr(sys, "executable", str(interpreter / "python"))


def test_command_prefers_the_client_beside_the_interpreter(monkeypatch, tmp_path):
    """With the variable unset, `command()` is the Bellman client beside
    the interpreter that runs the Workbench, its own Python environment,
    before the one on the search path, so that a desktop launch, whose
    search path lacks that environment, and a search path holding an older
    client both run the client installed with the Workbench; without one
    beside the interpreter, the one on the search path; without either,
    None."""
    monkeypatch.delenv(matsya_client.COMMAND_VARIABLE)
    on_path = tmp_path / "path"
    beside = tmp_path / "venv" / "bin"
    for folder in (on_path, beside):
        folder.mkdir(parents=True)
        client = folder / "bellman-matsya"
        client.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        client.chmod(client.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(on_path))
    monkeypatch.setattr(sys, "executable", str(beside / "python"))
    assert matsya_client.command() == [str(beside / "bellman-matsya")]
    (beside / "bellman-matsya").unlink()
    assert matsya_client.command() == [str(on_path / "bellman-matsya")]
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    assert matsya_client.command() is None


def test_command_uses_only_the_bellman_client_on_the_path(monkeypatch, tmp_path):
    """The default search ignores the commands of the earlier HARK client."""
    monkeypatch.setenv(matsya_client.COMMAND_VARIABLE, "'a client/run' --group DP")
    assert matsya_client.command() == ["a client/run", "--group", "DP"]
    monkeypatch.delenv(matsya_client.COMMAND_VARIABLE)
    monkeypatch.setenv("PATH", str(tmp_path))
    _no_client_beside_the_interpreter(monkeypatch, tmp_path)
    for name in ("matsya", "econ-ark-matsya"):
        client = tmp_path / name
        client.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        client.chmod(client.stat().st_mode | stat.S_IXUSR)
    assert matsya_client.command() is None
    client = tmp_path / "bellman-matsya"
    client.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    client.chmod(client.stat().st_mode | stat.S_IXUSR)
    assert matsya_client.command() == [str(client)]


def test_ask_sends_a_question_that_begins_with_a_dash_as_the_question():
    """A question that begins with a dash is read by the client as the
    question and not as an option, since the Workbench writes `--` before
    it. Without `--`, the client's parser would read the one-word question
    `--help` as its own help option and print its usage, so the answer
    would be UNREAD, and it would refuse an unknown option such as `-x`,
    so the answer would be NO_ANSWER. The parser reads an argument that
    begins with a dash and holds a space as the question even without
    `--`; the first question here is such an argument, and the second,
    `--help`, is the one that needs `--`."""
    answer, passages = matsya_client.ask("--help, or -1 times 𝑉?", "portfolio-choice")
    assert "question: --help, or -1 times 𝑉?" in answer
    assert passages == STUB_PASSAGES
    answer, passages = matsya_client.ask("--help", "portfolio-choice")
    assert "question: --help" in answer.splitlines()
    assert passages == STUB_PASSAGES


def test_ask_answers_one_sentence_for_a_text_not_in_the_clients_form():
    """The client exits with status 0 and a text in no form it prints: the
    answer is the sentence UNREAD with no passage."""
    found = matsya_client.ask("A garbled answer, please", "portfolio-choice")
    assert found == (matsya_client.UNREAD, ())


def test_ask_raises_nothing_for_a_malformed_command_line_or_question(monkeypatch, tmp_path):
    """Three inputs on which no client can be run are each answered by one
    sentence and no passage, and nothing is raised: a question holding a
    NUL character, which the operating system cannot pass as an argument,
    by NO_ANSWER; a variable whose quotation does not close by NO_CLIENT
    naming the variable and not its text, which may hold a token; and a
    variable of blanks alone, which counts as unset, by NO_CLIENT naming
    `bellman-matsya`. The search path is an empty folder from
    the test's first line, so that no client installed on this machine
    runs."""
    monkeypatch.setenv("PATH", str(tmp_path))
    _no_client_beside_the_interpreter(monkeypatch, tmp_path)
    found = matsya_client.ask("a\x00question", "portfolio-choice")
    assert found == (matsya_client.NO_ANSWER, ())
    unclosed = " 'a client/run --group DP "
    monkeypatch.setenv(matsya_client.COMMAND_VARIABLE, unclosed)
    found = matsya_client.ask(QUESTION, "portfolio-choice")
    assert found == (matsya_client.NO_CLIENT.format(name="in BELLMAN_WORKBENCH_MATSYA"), ())
    assert unclosed.strip() not in found.answer
    monkeypatch.setenv(matsya_client.COMMAND_VARIABLE, "   ")
    assert matsya_client.command() is None
    assert matsya_client.ask(QUESTION, "portfolio-choice") == (
        matsya_client.NO_CLIENT.format(name="bellman-matsya"),
        (),
    )


def test_a_folder_reuses_its_bellman_session_after_restart(monkeypatch, tmp_path):
    """Later questions use the service's session ID, including after a restart."""
    calls = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(calls))
    first = matsya_client.ask("First question?", "folder-digest")
    importlib.reload(matsya_client)
    second = matsya_client.ask("Second question?", "folder-digest")
    assert "session: folder-digest" in first.answer
    assert "session: folder-digest" in second.answer
    arguments = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]
    assert arguments == [
        ["session", "new", "folder-digest", "--json"],
        ["ask", "id-folder-digest", "--json", "--", "First question?"],
        ["ask", "id-folder-digest", "--json", "--", "Second question?"],
    ]
    saved = matsya_client._state_file("folder-digest")
    assert saved.is_file()
    assert stat.S_IMODE(saved.stat().st_mode) == 0o600


def test_changed_bellman_service_settings_create_a_new_session(monkeypatch, tmp_path):
    """Changing the service address prevents reuse of its session ID."""
    calls = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(calls))
    monkeypatch.setenv("BELLMAN_MATSYA_SERVER", "http://127.0.0.1:8710")
    matsya_client.ask(QUESTION, "portfolio-choice")
    monkeypatch.setenv("BELLMAN_MATSYA_SERVER", "http://127.0.0.1:18710")
    matsya_client.ask(QUESTION, "portfolio-choice")
    arguments = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]
    assert [call for call in arguments if call[:2] == ["session", "new"]] == [
        ["session", "new", "portfolio-choice", "--json"],
        ["session", "new", "portfolio-choice", "--json"],
    ]


# --- the window ---


def test_the_window_renders_its_head_and_sends_a_question_by_enter_or_ask(matsya_state):
    """The window renders open, as Matsya's column (spec 0.4 §§5.1 and 5.6;
    brief rules 3 and 8; design pass 8 §6): its head, the system's head,
    holds the heading `Matsya`, Υ as text and the icon button `Fold
    Matsya`, the Codicon `close`, a fold button `.bl-fold` for `matsya`,
    which window.vue reads; it draws no image, and the list of exchanges
    takes the keyboard's focus (R-D13). The body holds that list and the
    composer, and no sentence about Matsya's index (L-D2). The composer is
    a text area that grows with its text, one line when empty (amendment 07
    of spec 0.4, §2 items 1 and 2), its placeholder `Matsya query?` and its
    spoken name `Matsya query` (S-D10), which sends its text on Enter: text
    of white space sends nothing; a question sent is listed, the field
    emptied, and the task answers it in a thread off the renderer's, the
    answer under the speaker `Matsya`; a second question sent by the icon
    button `Ask`, the Codicon `send`, is listed and answered in turn."""
    _, rendered = solara.render(
        matsya_window.MatsyaWindow("portfolio-choice", app.Field, app.ToolbarButton),
        handle_error=False,
    )
    try:
        head = rendered.find(ipyvue.Html, class_="bl-head bl-matsya-head")
        head.assert_single()
        head.find(ipyvue.Html, tag="h2", children=["Matsya"]).assert_single()
        head.find(ipyvue.Html, class_="bl-matsya-upsilon", children=["Υ"]).assert_single()
        fold = head.find(ipyvue.Html, tag="vscode-toolbar-button").widget
        assert fold.class_ == "bl-fold"
        names = ("data-fold", "icon", "label", "title")
        assert {name: fold.attributes[name] for name in names} == {
            "data-fold": "matsya",
            "icon": "close",
            "label": "Fold Matsya",
            "title": "Fold Matsya",
        }
        assert not rendered.find(ipyvue.Html, tag="img")
        exchanges = rendered.find(ipyvue.Html, class_="bl-matsya-exchanges").widget
        assert exchanges.attributes["tabindex"] == "0"
        body = rendered.find(ipyvue.Html, class_="bl-matsya-body").widget
        assert [child.class_ for child in body.children] == [
            "bl-matsya-exchanges",
            "bl-matsya-row",
        ]
        field = rendered.find(ipyvue.VueTemplate, classes="bl-matsya-field").widget
        assert (field.kind, field.submits, field.grows, field.placeholder, field.named) == (
            "area",
            True,
            True,
            "Matsya query?",
            "Matsya query",
        )
        assert matsya_window.COMPOSER_PLACEHOLDER == "Matsya query?"
        field.vue_submitted("   ")
        assert matsya_state.exchanges.value == ()
        field.vue_entered("What is a perch?")
        field.vue_submitted("What is a perch?")
        assert matsya_state.exchanges.value[0].question == "What is a perch?"
        assert matsya_state.draft.value == ""
        wait_until(lambda: not matsya_state.answering(), 10.0, "the first answer")
        (first,) = matsya_state.exchanges.value
        assert "question: What is a perch?" in first.answer
        assert first.passages == STUB_PASSAGES
        speaker = rendered.find(ipyvue.Html, class_="bl-matsya-speaker").wait_for(timeout=5)
        assert speaker.widget.children == ["Matsya"]
        field.vue_entered("And a stage?")
        ask = rendered.find(ipyvue.Html, tag="vscode-toolbar-button", class_="bl-matsya-ask")
        assert ask.widget.attributes["icon"] == "send"
        ask.widget.fire_event("click", {})
        questions = [exchange.question for exchange in matsya_state.exchanges.value]
        assert questions == ["What is a perch?", "And a stage?"]
        wait_until(lambda: not matsya_state.answering(), 10.0, "the second answer")
    finally:
        rendered.close()


def test_a_question_while_matsya_answers_sends_nothing_and_keeps_the_text(matsya_state):
    """While the last question waits for its answer, a second question is
    not sent: the window lists the first alone, the field keeps the
    second, and the count of questions sent, on which the task depends,
    stays at one."""
    matsya_state.send("What is a perch?")
    matsya_state.set_draft("And a stage?")
    matsya_state.send(matsya_state.draft.value)
    assert matsya_state.exchanges.value == (matsya_window.Exchange("What is a perch?"),)
    assert matsya_state.draft.value == "And a stage?"
    assert matsya_state.asked.value == 1


# --- the task and the tests' own client ---


def test_answer_last_writes_the_answer_into_its_question(matsya_state):
    """The task's body asks the last question sent and writes the answer
    and its passages into that question's exchange; run again, it asks
    nothing, since the question is answered."""
    matsya_state.send(QUESTION)
    assert matsya_state.answering()
    matsya_state.answer_last("portfolio-choice")
    answered = matsya_window.Exchange(QUESTION, ANSWER, STUB_PASSAGES)
    assert matsya_state.exchanges.value == (answered,)
    assert not matsya_state.answering()
    matsya_state.answer_last("portfolio-choice")
    assert matsya_state.exchanges.value == (answered,)


def test_m_item_4_the_tests_run_the_stand_in_and_need_no_token(
    monkeypatch, tmp_path, model_folder
):
    """With the home folder empty, so that no configuration of the client
    exists, a question is answered by the stand-in, which the fixture
    `matsya_stub` names for every test of this folder; the environment of
    the tests' page servers names the same stand-in."""
    monkeypatch.setenv("HOME", str(tmp_path))
    assert matsya_client.ask(QUESTION, "portfolio-choice") == (ANSWER, STUB_PASSAGES)
    environment = command.server_environment(model_folder, None, MATSYA_STUB)
    assert environment[matsya_client.COMMAND_VARIABLE] == MATSYA_STUB


# --- unit R: the setting `off` and the conversation's name ---


def test_r_off_names_no_client_and_is_read_once(monkeypatch):
    """Spec 0.4 §6 and review 10 (R-D8): the value `off` of
    BELLMAN_WORKBENCH_MATSYA, white space around it included, names no
    client: `command()` answers None, and `ask` runs no process.
    `switched_off()` reads the variable at its first call and keeps the
    answer: the variable set to `off` after a first call that read the
    stand-in leaves the answer False, and the stand-in set after a first
    call that read `off` leaves it True."""
    runs = []
    monkeypatch.setattr(matsya_client.subprocess, "run", lambda *args, **_: runs.append(args))
    matsya_client.switched_off.cache_clear()
    try:
        assert matsya_client.switched_off() is False
        monkeypatch.setenv(matsya_client.COMMAND_VARIABLE, " off ")
        assert matsya_client.switched_off() is False
        assert matsya_client.command() is None
        assert matsya_client.ask(QUESTION, "portfolio-choice").passages == ()
        assert runs == []
        matsya_client.switched_off.cache_clear()
        assert matsya_client.switched_off() is True
        monkeypatch.setenv(matsya_client.COMMAND_VARIABLE, MATSYA_STUB)
        assert matsya_client.switched_off() is True
        assert matsya_client.command() == shlex.split(MATSYA_STUB)
    finally:
        matsya_client.switched_off.cache_clear()


def test_r_the_session_is_a_digest_of_the_folders_path(app_state, model_folder, matsya_state):
    """Spec 0.4 §6, decision 32, and review 10 (R-D21): the conversation's
    name the page passes to the window, `app._session()`, is the first
    twelve characters of the SHA-256 digest of the tab's folder's path, and
    holds no part of the folder's name; a question asked in that
    conversation reaches the client with the digest as the session, and the
    folder's name stands nowhere in what the client read."""
    app = app_state(model_folder)
    session = app._session()
    path = str(model_folder.resolve())
    assert session == hashlib.sha256(path.encode("utf-8")).hexdigest()[:12]
    assert model_folder.name not in session
    matsya_state.send(QUESTION)
    matsya_state.answer_last(session)
    (exchange,) = matsya_state.exchanges.value
    assert f"session: {session}" in exchange.answer
    assert model_folder.name not in exchange.answer
