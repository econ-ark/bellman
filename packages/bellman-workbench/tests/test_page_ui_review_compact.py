"""The narrow Workbench keeps the model and its source in one window."""

from playwright.sync_api import expect

from workbench_support import CONS, focus_region, open_file, replace_in_editor


def test_compact_panels_keep_the_buffer_and_problem_source(
    page, server_on, scratch_folder
):
    url = server_on(scratch_folder, matsya_command="off")
    open_file(page, url, CONS, minimum=4)
    editor = page.locator(".bl-editor")
    graph = page.locator(".bl-view")
    layout = page.locator(".bl-compact-switch")
    page.set_viewport_size({"width": 390, "height": 780})
    expect(layout.get_by_role("button", name="Source")).to_have_attribute(
        "aria-pressed", "true", timeout=3000
    )
    assert editor.bounding_box()["width"] == 390
    expect(graph).to_have_css("opacity", "0")
    assert page.evaluate("document.documentElement.scrollWidth") == 390

    stage_path = scratch_folder / CONS
    original = stage_path.read_text()
    replace_in_editor(page, "a = m_d - c", "a = unknown_symbol - c")
    layout.get_by_role("button", name="Show problems").click()
    expect(layout.get_by_role("button", name="Graph")).to_have_attribute("aria-pressed", "true")
    assert graph.bounding_box()["width"] == 390
    assert not editor.is_visible()
    source = graph.locator(f'.bl-error-place[data-path="{CONS}"]').first
    expect(source).to_be_visible(timeout=30_000)
    source.click()
    expect(editor).to_be_visible()
    assert "unknown_symbol" in editor.locator(".cm-content").inner_text()
    assert stage_path.read_text() == original

    layout.get_by_role("button", name="Files").click()
    expect(page.locator(".bl-folder")).to_be_visible()
    assert not editor.is_visible()
    page.locator(f'.bl-tree-file[data-path="{CONS}"]').click()
    expect(editor).to_be_visible()
    expect(page.locator(".bl-save")).to_be_visible()

    page.set_viewport_size({"width": 1600, "height": 900})
    expect(layout).to_be_hidden()
    expect(editor).to_be_visible()
    expect(graph).to_be_visible()
    assert "unknown_symbol" in editor.locator(".cm-content").inner_text()


def test_compact_matsya_and_wide_folds_keep_their_state(
    page, server_on, scratch_folder
):
    open_file(page, server_on(scratch_folder), CONS, minimum=4)
    window = page.locator(".bl-window")
    details = window.locator('.bl-main-bar [data-fold="details"]')
    details.click()
    expect(details).to_have_attribute("aria-expanded", "false")
    page.set_viewport_size({"width": 1100, "height": 760})
    files = window.locator('.bl-main-bar [data-fold="folder"]')
    expect(files).to_have_attribute("aria-expanded", "false")
    files.click()
    expect(window).to_have_attribute("data-compact-pane", "folder")
    assert page.evaluate("document.documentElement.scrollWidth") == 1100
    page.set_viewport_size({"width": 390, "height": 760})
    layout = page.get_by_role("navigation", name="Workbench panels")
    layout.get_by_role("button", name="Matsya").click()
    expect(layout.get_by_role("button", name="Matsya")).to_have_attribute("aria-pressed", "true")
    expect(page.locator(".bl-matsya")).to_be_visible()
    assert page.locator(".bl-matsya").bounding_box()["width"] == 390
    assert page.evaluate("document.documentElement.scrollWidth") == 390
    layout.get_by_role("button", name="Graph").click()
    expect(page.locator(".bl-view")).to_be_visible()
    expect(page.locator(".bl-matsya")).to_be_hidden()
    focused = focus_region(page)["box"]
    page.keyboard.press("Enter")
    selected = page.locator(f'.bl-view .react-flow__node[data-id="{focused}"].selected')
    expect(selected).to_be_visible()
    layout.get_by_role("button", name="Source").click()
    layout.get_by_role("button", name="Graph").click()
    expect(selected).to_be_visible()
    page.set_viewport_size({"width": 1600, "height": 900})
    expect(layout).to_be_hidden()
    expect(details).to_have_attribute("aria-expanded", "false")
    expect(page.locator(".bl-matsya")).to_be_visible()
