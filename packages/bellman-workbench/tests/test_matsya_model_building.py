"""Matsya job identities and products observed in model-building trials."""

import json
import os
from pathlib import Path
from types import SimpleNamespace

from workbench_support import MATSYA_TOGGLE, new_tab, stub_job, stub_turn, wait_until

from bellman_workbench import matsya_client, matsya_window, matsya_work, model


def test_connected_ask_shows_its_job_and_recovers_it_on_reopening(
    tmp_path, matsya_state, monkeypatch
):
    folder = model.open_folder(tmp_path)
    endpoint = "http://127.0.0.1:8710"
    monkeypatch.setenv("BELLMAN_MATSYA_SERVER", endpoint)
    project = folder.root / matsya_work.PROJECT_FILE
    project.parent.mkdir()
    project.write_text(json.dumps({"session": "trial", "server": endpoint}))
    question = "Build a Recipe from the pension assumptions."
    job = {"id": "new-job", "session": "trial", "state": "running"}
    turn = {
        "id": "build-turn",
        "session": "trial",
        "question": 6,
        "state": "finished",
        "record": {
            "result": {
                "answer": "Architect accepted the Recipe.",
                "job": {"id": "discussed-job"},
                "job_started": {"id": job["id"]},
            }
        },
    }
    session = {
        "id": "trial",
        "jobs": [job],
        "turns": [turn["id"]],
        "entries": [{"number": 6, "kind": "user", "text": question}],
    }
    calls = []

    def run(args):
        calls.append(tuple(args))
        if args[0] == "ask":
            return matsya_client.Run(0, {"id": turn["id"]}, "")
        if args[:2] == ["turn", "status"]:
            return matsya_client.Run(0, turn, "")
        if args[:2] == ["session", "show"]:
            return matsya_client.Run(0, session, "")
        assert args == ["job", "status", job["id"], "--json"]
        return matsya_client.Run(0, job, "")

    monkeypatch.setattr(matsya_client, "run", run)
    matsya_state.send(question)
    matsya_window.answer_last("local", SimpleNamespace(folder=lambda: folder))
    assert [exchange.job for exchange in matsya_state.exchanges.value if exchange.job] == [
        job["id"]
    ]
    assert matsya_state.exchanges.value[0].answer == "Architect accepted the Recipe."
    before = {p: p.read_bytes() for p in (folder.root / matsya_work.REQUESTS_FOLDER).glob("*")}
    (request,) = before.values()
    assert json.loads(request)["started_job"] == job["id"]
    matsya_window.clear_conversation()
    matsya_window.recover_jobs(folder)
    matsya_window.recover_jobs(folder)
    assert [exchange.job for exchange in matsya_state.exchanges.value if exchange.job] == [
        job["id"]
    ]
    assert [e.answer for e in matsya_state.exchanges.value if e.kind == "question"] == [
        "Architect accepted the Recipe."
    ]
    assert before == {p: p.read_bytes() for p in before}
    assert sum(call[0] == "ask" for call in calls) == 1


def test_job_products_show_the_native_comparison_and_unresolved_note():
    products = {
        "state": "converged",
        "result": {
            "last_completed_comparison": {
                "left_cycle": 0,
                "right_cycle": 1,
                "equal": True,
                "first_difference": None,
            },
            "last_cycle": {"unresolved_note": True},
            "paper_form_check": {"passed": False, "findings": ["An assumption is missing."]},
        },
    }

    comparison, prose, assumptions, construction, numerical = matsya_window.parts(
        matsya_window.JobView(job=products)
    )

    assert comparison.value == "converged"
    assert prose.details == ("An assumption is missing.",)
    assert assumptions.value == "1"
    assert "unresolved" in assumptions.details[0]
    assert construction.value == "not downloaded"
    assert numerical.value == "not run"


def test_missing_products_report_unavailable_without_following_a_failed_job():
    job = {"state": "failed", "error": "The writer refused the source."}
    comparison, prose, assumptions, _, _ = matsya_window.parts(matsya_window.JobView(job=job))
    assert all(part.value == "unavailable" for part in (comparison, prose, assumptions))
    assert matsya_window._ended(job)
    assert not matsya_window._can_download(job)
    report_only = {"state": "not_converged", "result": {"available_writing": None}}
    assert matsya_window._can_download(report_only)
    assert matsya_window._declaration_absent(report_only)


def test_browser_recovers_the_chat_build_and_its_unresolved_note(browser, server_on, tmp_path):
    blank = tmp_path / "pension-trial"
    blank.mkdir()
    folder = model.open_folder(blank)
    endpoint = os.environ["BELLMAN_MATSYA_SERVER"]
    project = folder.root / matsya_work.PROJECT_FILE
    project.parent.mkdir()
    project.write_text(json.dumps({"session": "a" * 32, "server": endpoint}))
    session_id = "a" * 32
    question = "Build a Recipe from the pension assumptions."
    state_path = Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"])
    context, page = new_tab(browser)

    def open_column():
        page.wait_for_function(
            "(selector) => document.querySelector(selector)?.hasAttribute('aria-expanded')",
            arg=MATSYA_TOGGLE,
        )
        toggle = page.locator(MATSYA_TOGGLE)
        if toggle.get_attribute("aria-expanded") == "false":
            toggle.click()
        field = page.locator(".bl-matsya-field textarea")
        field.wait_for()
        return field

    try:
        page.goto(server_on(folder.root))
        field = open_column()
        field.fill(question)
        field.press("Enter")
        wait_until(
            lambda: state_path.is_file() and state_path.stat().st_size > 0,
            15.0,
            "the accepted turn",
        )
        state = json.loads(state_path.read_text())
        (turn,) = state["turns"].values()
        label = {"number": 1, "target": "recipe", "state": "converged"}
        job = {
            "id": "chat-job",
            "session": session_id,
            "state": "converged",
            "label": label,
            "result": {
                "last_completed_comparison": {
                    "left_cycle": 0,
                    "right_cycle": 1,
                    "equal": True,
                    "first_difference": None,
                },
                "last_cycle": {"unresolved_note": True},
                "available_writing": {"files": {"note.md": "Supply the terminal continuation."}},
            },
        }
        stub_job(job)
        stub_turn(
            {
                **turn,
                "state": "finished",
                "record": {
                    "result": {
                        "answer": "Architect accepted the Recipe.",
                        "job": {"id": "discussed-job"},
                        "job_started": {"id": job["id"], "label": label},
                    }
                },
            }
        )
        card = page.locator('.bl-matsya-job[data-job="chat-job"]')
        card.wait_for(timeout=20_000)
        assert page.locator(".bl-matsya-job").count() == 1
        assert "Supply the terminal continuation." in card.inner_text()
        assert "Architect accepted the Recipe." in page.locator(".bl-matsya-answer").inner_text()

        requests = folder.root / matsya_work.REQUESTS_FOLDER
        before = {path: path.read_bytes() for path in requests.glob("*.json")}
        page.reload()
        open_column()
        card.wait_for(timeout=20_000)
        assert page.locator(".bl-matsya-job").count() == 1
        assert "Supply the terminal continuation." in card.inner_text()
        assert "Architect accepted the Recipe." in page.locator(".bl-matsya-answer").inner_text()
        assert before == {path: path.read_bytes() for path in requests.glob("*.json")}
        assert len(json.loads(state_path.read_text())["turns"]) == 1
    finally:
        context.close()
