"""External file requests and the configured editor, with Matsya disabled."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from workbench_support import (
    CONS,
    DOCUMENT_JS,
    PORT,
    RECIPE_FILE,
    editor_selection,
    new_tab,
    replace_in_editor,
    status_settled_on,
    wait_until,
)

from bellman_workbench import desktop


def test_item_1_requests_stay_inside_the_model_folder(tmp_path):
    root = tmp_path / "model"
    root.mkdir()
    (root / "my file.bl").write_text("@stage: a\n")
    outside = tmp_path / "outside.bl"
    outside.write_text("@stage: outside\n")
    (root / "linked.bl").symlink_to(outside)
    expected = {"file": "my file.bl", "line": 12, "box": "policy"}
    assert desktop.navigation_request(root, {**expected, "line": "12"}) == expected
    for name in ("../outside.bl", str(outside), "linked.bl", "missing.bl", "..\\outside.bl"):
        with pytest.raises(ValueError):
            desktop.navigation_request(root, {"file": name, "line": 1})
    for line in (0, -1, True, 1.5, "1.5", "1; touch bad", "", None, 2**31):
        with pytest.raises(ValueError, match="positive integer"):
            desktop.navigation_request(root, {"file": "my file.bl", "line": line})


def test_item_2_editor_receives_a_literal_path_and_line(tmp_path, monkeypatch):
    target = tmp_path / "a file; $(echo bad).bl"
    target.write_text("@stage: a\n")
    received = tmp_path / "received.json"
    command = json.dumps(
        [
            sys.executable,
            "-c",
            "import json,pathlib,sys; "
            "pathlib.Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]))",
            str(received),
            "--goto",
        ]
    )
    desktop.open_in_editor(tmp_path, target.name, 7, command)
    wait_until(received.exists, 5, "the editor argument record")
    assert json.loads(received.read_text()) == ["--goto", f"{target}:7"]
    model_folder = tmp_path / "model"
    model_folder.mkdir()
    received.unlink()
    desktop.open_in_editor(model_folder, f"../{target.name}", 9, command)
    wait_until(received.exists, 5, "the external recipe source argument record")
    assert json.loads(received.read_text()) == ["--goto", f"{target}:9"]
    with pytest.raises(ValueError, match="inside the model folder"):
        desktop.navigation_request(model_folder, {"file": f"../{target.name}", "line": 9})
    for command in ('"code --goto"', "[]", '["code", null]', "code --goto"):
        with pytest.raises(ValueError, match="JSON list"):
            desktop.open_in_editor(tmp_path, target.name, 7, command)

    monkeypatch.setattr(desktop, "os", SimpleNamespace(name="nt"))
    for command in ('["code.cmd", "--goto"]', '["editor.BAT"]'):
        with pytest.raises(ValueError, match="executable program"):
            desktop.open_in_editor(tmp_path, target.name, 7, command)


def test_item_3_latest_request_selects_after_elaboration_and_keeps_edits(
    app_state, scratch_folder, monkeypatch
):
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA", "off")
    app = app_state(scratch_folder)
    app.on_desktop_open({"file": PORT, "line": 25})
    app.apply_desktop_request()
    assert app.desktop_pending.value["line"] == 25
    app.on_desktop_open({"file": PORT, "line": 30})
    app.run_loop()
    app.on_processed({})
    app.apply_desktop_request()
    assert app.desktop_pending.value is None
    assert app.cursor_block.value == "dcsn_to_arvl"
    assert app.select_request.value["graphId"] == "backward"
    chosen = app.select_request.value["nodeId"]
    app.on_desktop_open({"file": PORT, "line": 25, "box": chosen})
    app.apply_desktop_request()
    assert app.select_request.value["nodeId"] == chosen
    held = app.buffers.value[PORT]
    changed = held["text"] + "\n"
    app.on_desktop_open({"file": CONS, "line": 1})
    assert app.open_path.value == PORT
    app.on_change({"path": PORT, "revision": held["document_revision"], "text": changed})
    assert app.open_path.value == CONS
    assert app.buffers.value[PORT]["text"] == changed
    app.on_desktop_open({"file": "../outside.bl", "line": 1})
    assert app.open_path.value == CONS
    assert any("inside the model folder" in item.sentence for item in app.standing_refusals())

    # Save the temporary edit before changing the folder, as creation requires.
    app.on_desktop_open({"file": PORT, "line": 1})
    held = app.buffers.value[CONS]
    app.on_change({"path": CONS, "revision": held["document_revision"], "text": held["text"]})
    held = app.buffers.value[PORT]
    app.on_save({"path": PORT, "revision": held["document_revision"], "text": held["text"]})
    second_folder = scratch_folder.parent / "second-model"
    second_file = second_folder / PORT
    second_file.parent.mkdir(parents=True)
    second_file.write_text((scratch_folder / PORT).read_text())
    app.open_model(second_folder)
    app.on_desktop_open({"folder": str(second_folder), "file": PORT, "line": 30})
    assert app.tab_folder.value.root == second_folder.resolve()
    assert app.open_path.value == PORT
    app.run_loop()
    app.on_processed({})
    app.apply_desktop_request()
    assert app.cursor_block.value == "dcsn_to_arvl"
    assert app.goto_request.value["line"] == 30
    app.on_desktop_open({"folder": str(scratch_folder), "file": PORT, "line": 25})
    assert app.tab_folder.value.root == second_folder.resolve()
    assert app.open_path.value == PORT
    assert app.goto_request.value["line"] == 30
    assert any("changed model folders" in item.sentence for item in app.standing_refusals())


def test_item_4_initial_and_running_page_links_keep_unsaved_text(
    browser, server_on, model_folder, monkeypatch, tmp_path
):
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA", "off")
    received = tmp_path / "editor.json"
    command = json.dumps(
        [
            sys.executable,
            "-c",
            "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(sys.argv[2])",
            str(received),
        ]
    )
    monkeypatch.setenv(desktop.EDITOR_VARIABLE, command)
    url = server_on(model_folder, matsya_command="off")
    context, page = new_tab(browser)
    disk_text = (model_folder / PORT).read_text()
    try:
        page.goto(url + "?" + urlencode({"file": PORT, "line": 30}))
        wait_until(lambda: status_settled_on(page, PORT), 60, "the requested stage")
        wait_until(lambda: editor_selection(page)["line"] == "30", 20, "the requested line")
        wait_until(
            lambda: "dcsn_to_arvl" in page.locator(".bl-cursor-block").inner_text(),
            20,
            "the selected block",
        )
        assert page.locator(".bl-matsya").count() == 0
        source_line = page.locator(".bl-lines-link").get_attribute("data-line")
        page.locator(".bl-open-in-editor").click()
        wait_until(received.exists, 5, "the editor opened from Details")
        assert received.read_text() == f"{model_folder / PORT}:{source_line}"
        original = page.evaluate(DOCUMENT_JS)
        page.wait_for_function("window.__bellmanDirty === false")
        immediate = page.evaluate("""() => {
          const host = document.querySelector('.bl-editor');
          const editor = host.bellmanEditor;
          const content = host.querySelector('.cm-content');
          const before = editor.getDoc();
          const clean = window.__bellmanDirty;
          editor.gotoLine(1, 1);
          content.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Tab', code: 'Tab', keyCode: 9, bubbles: true, cancelable: true,
          }));
          const indented = editor.getDoc();
          const dirty = window.__bellmanDirty;
          const mac = navigator.platform.includes('Mac');
          content.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'z', code: 'KeyZ', keyCode: 90, metaKey: mac, ctrlKey: !mac,
            bubbles: true, cancelable: true,
          }));
          return {clean, dirty, changed: indented !== before,
            restored: editor.getDoc() === before, afterUndo: window.__bellmanDirty};
        }""")
        assert immediate == {
            "clean": False,
            "dirty": True,
            "changed": True,
            "restored": True,
            "afterUndo": False,
        }
        replace_in_editor(page, "ρ_ζ : [-1,1]", "ρ_ζ : [-1,1]  ")
        page.evaluate(
            "request => window.dispatchEvent(new CustomEvent('bellman-open', {detail: request}))",
            {"file": CONS, "line": 1},
        )
        wait_until(lambda: status_settled_on(page, CONS), 60, "the second requested stage")
        page.evaluate(
            "request => window.dispatchEvent(new CustomEvent('bellman-open', {detail: request}))",
            {"file": PORT, "line": 25},
        )
        wait_until(lambda: status_settled_on(page, PORT), 60, "the unsaved stage")
        wait_until(lambda: editor_selection(page)["line"] == "25", 20, "the second line")
        assert page.evaluate(DOCUMENT_JS) == original.replace("ρ_ζ : [-1,1]", "ρ_ζ : [-1,1]  ")
        assert page.evaluate("window.__bellmanDirty") is True
        page.wait_for_selector('.bl-tab[data-path="' + PORT + '"] .bl-modified')
        saved_text = page.evaluate(DOCUMENT_JS)
        race = page.evaluate(
            """path => {
          const host = document.querySelector('.bl-editor');
          const editor = host.bellmanEditor;
          const tab = document.querySelector(`.bl-tab[data-path="${path}"]`);
          const file = document.querySelector('.bl-file');
          window.__dirtyAtSaveAck = null;
          const observer = new MutationObserver(() => {
            if (!tab.querySelector('.bl-modified')) {
              window.__dirtyAtSaveAck = {dirty: window.__bellmanDirty, text: editor.getDoc()};
              observer.disconnect();
            }
          });
          observer.observe(file, {attributes: true, childList: true, subtree: true});
          const mac = navigator.platform.includes('Mac');
          host.querySelector('.cm-content').dispatchEvent(new KeyboardEvent('keydown', {
            key: 's', code: 'KeyS', keyCode: 83, metaKey: mac, ctrlKey: !mac,
            bubbles: true, cancelable: true,
          }));
          const before = editor.getDoc();
          editor.replaceSpans([{
            line: 1, column: 1, end_line: 1, end_column: 1, text: '  ',
          }], before);
          return {dirty: window.__bellmanDirty, text: editor.getDoc()};
        }""",
            PORT,
        )
        assert race["dirty"] is True
        page.wait_for_function("window.__dirtyAtSaveAck !== null", timeout=20_000)
        assert page.evaluate("window.__dirtyAtSaveAck") == race
        assert (model_folder / PORT).read_text() == saved_text
    finally:
        context.close()
        (model_folder / PORT).write_text(disk_text)


def test_item_5_running_request_replaces_a_queued_request_during_elaboration(
    browser, server_on, model_folder, monkeypatch
):
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA", "off")
    url = server_on(model_folder, delay_marker="ρ_ζ", matsya_command="off")
    context, page = new_tab(browser)
    try:
        context.add_init_script(
            "window.__bellmanOpenQueue = " + json.dumps([{"file": PORT, "line": 25}])
        )
        page.goto(url + "?" + urlencode({"file": CONS, "line": 1}))
        page.wait_for_function("window.__bellmanOpenReady === true")
        page.evaluate(
            "request => window.dispatchEvent(new CustomEvent('bellman-open', {detail: request}))",
            {"file": PORT, "line": 30},
        )
        wait_until(lambda: status_settled_on(page, PORT), 60, "the latest requested stage")
        wait_until(lambda: editor_selection(page)["line"] == "30", 20, "the latest requested line")
        wait_until(
            lambda: "dcsn_to_arvl" in page.locator(".bl-cursor-block").inner_text(),
            20,
            "the selected block",
        )
        assert page.locator(f'.bl-tab[data-path="{CONS}"]').count() == 0
    finally:
        context.close()


def test_item_6_invalid_initial_request_opens_the_folder_and_reports_the_error(
    browser, server_on, model_folder, monkeypatch
):
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA", "off")
    url = server_on(model_folder, matsya_command="off")
    context, page = new_tab(browser)
    try:
        page.goto(url + "?" + urlencode({"file": "../outside.bl", "line": 1}))
        page.wait_for_selector(f'.bl-tab[data-path="{RECIPE_FILE}"]', timeout=30_000)
        wait_until(
            lambda: "inside the model folder" in page.locator(".bl-error-list").inner_text(),
            20,
            "the refused file request",
        )
        assert page.locator('.bl-tab[data-path="../outside.bl"]').count() == 0
    finally:
        context.close()
