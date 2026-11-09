import json
from pathlib import Path

import pytest

from bellman_workbench import matsya_client, matsya_work, model


@pytest.fixture
def reviewed_build(tmp_path, monkeypatch):
    folder = model.open_folder(tmp_path)
    session = matsya_work.Session("a" * 32, "test-service")
    server = "https://matsya.test"
    association = tmp_path / matsya_work.PROJECT_FILE
    association.parent.mkdir()
    association.write_text(json.dumps({"session": session.id, "server": server}))
    (tmp_path / "economics.md").write_text("New pension description.\n")
    entries = [{"number": 1, "kind": "user", "text": "Old pension description."}]
    monkeypatch.setattr(matsya_client, "service_identity", lambda: session.service)
    monkeypatch.setattr(matsya_client, "service_url", lambda: server)
    monkeypatch.setattr(matsya_work, "read_session", lambda *_: {"entries": entries})
    prepared = matsya_work.prepare(
        folder, None, "recipe", session, 0,
        history=entries, prompt="  Build the model.\n",
    )
    assert prepared.record["source"] is None
    return folder, session, prepared, entries


def test_empty_project_review_retries_the_same_append_and_job(reviewed_build, monkeypatch):
    folder, session, prepared, entries = reviewed_build
    calls = []

    def run(arguments):
        if arguments[:2] == ["session", "add"]:
            text = Path(arguments[3]).read_text()
            calls.append(("entry", arguments[7]))
            assert text == (
                "Current model description (economics.md):\nNew pension description.\n\n"
                "Build request:\nBuild the model."
            )
            if len(entries) == 1:
                entries.append({"number": 2, "kind": "user", "text": text})
                return matsya_client.Run(1, None, "Lost entry acknowledgement")
            return matsya_client.Run(0, {"entry": {"number": 2}}, "")
        assert arguments[:2] == ["job", "submit-prepared"]
        assert json.loads(Path(arguments[2]).read_text()) == {
            "session": session.id, "target": "recipe", "reviewed_through": 2,
        }
        if not any(kind == "job" for kind, _ in calls):
            calls.append(("job", arguments[4]))
            return matsya_client.Run(1, None, "Lost job acknowledgement")
        calls.append(("job", arguments[4]))
        return matsya_client.Run(0, {"job": {"id": "job-one"}}, "")

    monkeypatch.setattr(matsya_client, "run", run)
    assert len(entries) == 1 and not calls
    for expected in (None, None, "job-one", "job-one"):
        result = matsya_work.submit(folder, prepared.path, session, prepared.record)
        assert result.record["accepted"] == expected
        pending = list(matsya_work.pending_builds(folder, session, entries))
        if expected is None:
            assert [review.path for review, _ in pending] == [prepared.path]
            assert pending[0][1] == entries[:1]
        else:
            assert pending == []
    assert calls[0] == calls[1] == ("entry", prepared.record["entry_delivery"])
    assert calls[2] == calls[3] == ("job", prepared.record["job_delivery"])
    assert len(calls) == 4 and len(entries) == 2


@pytest.mark.parametrize("change", ["history", "capture", "during_append"])
def test_build_refuses_an_unreviewed_change(reviewed_build, monkeypatch, change):
    folder, session, prepared, entries = reviewed_build
    changed = {"number": 2, "kind": "user", "text": "An intervening entry."}
    calls = []

    def run(arguments):
        calls.append(arguments[:2])
        assert change == "during_append" and arguments[:2] == ["session", "add"]
        entries.extend([changed, {
            "number": 3, "kind": "user", "text": Path(arguments[3]).read_text(),
        }])
        return matsya_client.Run(0, {"entry": {"number": 3}}, "")

    monkeypatch.setattr(matsya_client, "run", run)
    if change == "history":
        entries.append(changed)
    if change == "capture":
        (folder.root / prepared.record["inputs"]).write_text("{}")
    with pytest.raises(ValueError, match="changed"):
        matsya_work.submit(folder, prepared.path, session, prepared.record)
    assert calls == ([["session", "add"]] if change == "during_append" else [])


def test_empty_project_builds_after_review_in_the_browser(
    tmp_path, monkeypatch, browser, server_on
):
    from workbench_support import MATSYA_TOGGLE, choose_option, new_tab, stub_calls

    root = tmp_path / "pension"
    root.mkdir()
    (root / "economics.md").write_text("Retired households consume and save.\n")
    log = tmp_path / "client-calls.jsonl"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_LOG", str(log))
    context, tab = new_tab(browser)
    try:
        tab.goto(server_on(root))
        tab.wait_for_selector(".bl-window")
        if not tab.locator(".bl-matsya").is_visible():
            tab.click(MATSYA_TOGGLE)
        tab.click(".bl-matsya-connect-button")
        tab.wait_for_selector('.bl-matsya-chip[data-kind="session"]:has-text("pension")')
        choose_option(tab, ".bl-matsya-kind", "Build declaration")
        composer = tab.locator(".bl-matsya-field textarea")
        composer.fill("Prepare a two-period pension recipe.")
        composer.press("Enter")
        tab.wait_for_selector(".bl-matsya-build-what:has-text('Description only')")
        review = tab.locator(".bl-matsya-build")
        review.get_by_text("Text and session history", exact=True).click()
        assert review.get_by_text("Retired households consume and save.", exact=False).is_visible()
        assert not any(
            call[:2] in (["session", "add"], ["job", "submit-prepared"])
            for call in stub_calls(log) if isinstance(call, list)
        )
        review.get_by_role("button", name="Build declaration").click()
        tab.wait_for_selector('.bl-matsya-job[data-job="job-1"]', timeout=20_000)
        (sent,) = [item["submitted"] for item in stub_calls(log)
                   if isinstance(item, dict) and "submitted" in item]
        assert sent == {}
        assert not (root / "declaration").exists()
    finally:
        context.close()
