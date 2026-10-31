"""The desktop server reports when its listener has bound successfully."""

from bellman_workbench import command


def test_desktop_start_reports_uvicorn_listener(monkeypatch):
    monkeypatch.setenv("BELLMAN_WORKBENCH_DESKTOP", "1")
    arguments = command.server_command(8123, "127.0.0.1", False)
    assert arguments[-2:] == ["--log-level-uvicorn", "info"]
    assert "--no-open" in arguments


def test_browser_start_keeps_default_logging(monkeypatch):
    monkeypatch.delenv("BELLMAN_WORKBENCH_DESKTOP", raising=False)
    arguments = command.server_command(8123, "localhost", False)
    assert "--log-level-uvicorn" not in arguments
