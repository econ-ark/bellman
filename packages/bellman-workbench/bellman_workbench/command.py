"""The console command `bellman-workbench <folder>` (model interface
specification 0.3, §11): it starts Solara's server on the page `app.py` in
production mode and opens the browser at the local address.

The server's environment is answered by one function, `server_environment`,
which the command and the page tests both call (specification §2.5): the
process's environment plus `BELLMAN_WORKBENCH_FOLDER`, the resolved path of
the model folder, which `app.py` reads at import;
`SOLARA_TELEMETRY_MIXPANEL_ENABLE=False`, which turns Solara's usage
reporting off; `SOLARA_THEME_SHOW_BANNER=False`, which leaves the server's
own banner, "This website runs on Solara", off the page;
`SOLARA_THEME_LOADER=solara` selects the markup styled by `public/custom.css`,
and `SOLARA_THEME_TITLE` names the page before the model opens;
`SOLARA_ASSETS_PROXY_CACHE_DIR`, the package folder holding all of Solara's
interface files (G-D12), overriding an inherited cache location so that
Solara need not fetch and write a missing file;
`SOLARA_SERVER_HTTP_GZIP=False`, which makes the server send every response
uncompressed: the server answers the browser of the same machine, where
compressing the graph's scripts costs the server more time than the
transfer saves (G-R77); and, when the tests give
them, `BELLMAN_WORKBENCH_DELAY_MARKER`, the text that makes the
loop wait before writing a result (the hook `app.py` documents), and
`BELLMAN_WORKBENCH_MATSYA`, the command line of Matsya's client, which the
tests set to the stand-in `tests/matsya_stub.py` (`matsya_client.py`
reads it). The server
is Solara's own, run as `python -m solara run <app.py> --production
--no-check-version --port <port> --host <host>`;
`--production` turns off the file watching of development mode, and
`--no-check-version` leaves out Solara's request to PyPI for a newer
version.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from bellman_workbench import matsya_client, model

# the page the server runs
APP = Path(__file__).resolve().parent / "app.py"
# Solara's own interface files, read from SOLARA_ASSETS_PROXY_CACHE_DIR (G-D12).
SOLARA_CDN = Path(__file__).resolve().parent / "solara-cdn"


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """The parsed command line: the folder (default "."), `--port`
    (default 8765), `--host` (default localhost) and `--no-open`."""
    parser = argparse.ArgumentParser(
        prog="bellman-workbench",
        description="Bellman Workbench over one model folder.",
    )
    parser.add_argument("folder", nargs="?", default=".", help="the model folder (default .)")
    parser.add_argument("--port", type=int, default=8765, help="the port (default 8765)")
    parser.add_argument("--host", default="localhost", help="the host (default localhost)")
    parser.add_argument(
        "--no-open", action="store_true", help="do not open the browser at the address"
    )
    return parser.parse_args(argv)


def server_environment(
    folder: Path, delay_marker: str | None = None, matsya_command: str | None = None
) -> dict:
    """The environment of the server's process: `os.environ` with
    `BELLMAN_WORKBENCH_FOLDER` set to `folder`, Solara's usage reporting,
    its banner and its compression of responses turned off, and
    its startup loader and title selected for the Workbench. The
    `SOLARA_ASSETS_PROXY_CACHE_DIR` is set to the complete package folder of
    Solara's interface files, overriding any inherited cache. Solara fetches
    and writes a missing file, so that folder must be complete (G-D12).
    Responses go uncompressed because the server answers the browser of the
    same machine, where compressing the graph's scripts costs the server
    more time than the transfer saves (G-R77).
    `BELLMAN_WORKBENCH_DELAY_MARKER` is set to
    `delay_marker` when one is given, and BELLMAN_WORKBENCH_MATSYA set to
    `matsya_command`, the command line of Matsya's client, when one is
    given. The command and the tests' server fixture both call this
    function, so the environment is written once."""
    environment = {
        **os.environ,
        "BELLMAN_WORKBENCH_FOLDER": str(folder),
        "SOLARA_TELEMETRY_MIXPANEL_ENABLE": "False",
        "SOLARA_THEME_SHOW_BANNER": "False",
        "SOLARA_THEME_LOADER": "solara",
        "SOLARA_THEME_TITLE": "Bellman Workbench",
        "SOLARA_ASSETS_PROXY_CACHE_DIR": str(SOLARA_CDN),
        "SOLARA_SERVER_HTTP_GZIP": "False",
    }
    if delay_marker is not None:
        environment["BELLMAN_WORKBENCH_DELAY_MARKER"] = delay_marker
    if matsya_command is not None:
        environment[matsya_client.COMMAND_VARIABLE] = matsya_command
    return environment


def server_command(port: int, host: str, open_browser: bool) -> list[str]:
    """The command line of Solara's server on the page."""
    command = [
        sys.executable,
        "-m",
        "solara",
        "run",
        str(APP),
        "--production",
        "--no-check-version",
        "--port",
        str(port),
        "--host",
        host,
    ]
    if not open_browser:
        command.append("--no-open")
    if os.environ.get("BELLMAN_WORKBENCH_DESKTOP") == "1":
        # The desktop shell waits for Uvicorn's message after its socket binds.
        command.extend(["--log-level-uvicorn", "info"])
    return command


def main(argv: list[str] | None = None) -> int:
    """Runs the server on the folder and answers its exit code; a path that
    is no folder is refused with the sentence on standard error and 2."""
    arguments = parse_arguments(argv)
    try:
        folder = model.open_folder(arguments.folder)
    except ValueError as error:
        print(f"bellman-workbench: {error}", file=sys.stderr)
        return 2
    command = server_command(arguments.port, arguments.host, not arguments.no_open)
    return subprocess.call(command, env=server_environment(folder.root))


if __name__ == "__main__":
    sys.exit(main())
