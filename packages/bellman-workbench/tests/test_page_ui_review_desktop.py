"""The desktop welcome page restores its control after a native chooser."""

from playwright.sync_api import expect

from workbench_support import ROOT


def test_welcome_restores_focus_after_cancelling_or_failing(page):
    assets = ROOT / "packages/bellman-desktop/assets"
    page.goto((assets / "index.html").as_uri())
    action = page.get_by_role("button", name="Open Project…")
    status = page.get_by_role("status")
    action.focus()
    page.evaluate("window.bellmanWelcome.setOpenStatus('Choose a project folder.', true)")
    expect(status).to_have_text("Choose a project folder.")
    expect(action).to_be_disabled()
    page.evaluate("window.bellmanWelcome.setOpenStatus('Opening cancelled.', false)")
    expect(status).to_have_text("Opening cancelled.")
    expect(action).to_be_focused()

    page.evaluate("window.bellmanWelcome.setOpenStatus('Opening project…', true)")
    page.evaluate("window.bellmanWelcome.setOpenStatus('Cannot open the project folder.', false)")
    expect(status).to_have_text("Cannot open the project folder.")
    expect(action).to_be_enabled()
    expect(action).to_be_focused()
