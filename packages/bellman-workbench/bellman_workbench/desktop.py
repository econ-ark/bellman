"""File requests shared by the desktop application and the browser page."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

EDITOR_VARIABLE = "BELLMAN_WORKBENCH_EDITOR"


def navigation_request(root: Path, data: dict) -> dict:
    """Validate a file and line received from outside the page.

    Files must exist within the model folder, including after resolving
    symbolic links. The returned path is relative to that folder.
    """
    if not isinstance(data, dict):
        raise ValueError("The file request must name a file and a line.")
    name = data.get("file")
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("The file request must name a relative file path.")
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("The requested file must be inside the model folder.")
    folder = root.resolve()
    target = (folder / relative).resolve()
    if not target.is_relative_to(folder):
        raise ValueError("The requested file must be inside the model folder.")
    if not target.is_file():
        raise ValueError(f"The requested file does not exist: {name}")
    line = data.get("line", 1)
    if isinstance(line, str) and re.fullmatch(r"[0-9]{1,10}", line):
        line = int(line)
    if type(line) is not int or not 1 <= line <= 2_147_483_647:
        raise ValueError("The requested line must be a positive integer.")
    box = data.get("box")
    if box is not None and (not isinstance(box, str) or not box or len(box) > 4096):
        raise ValueError("The requested box must be a nonempty name.")
    return {"file": relative.as_posix(), "line": line, "box": box}


def open_in_editor(root: Path, file: str, line: int, command: str) -> None:
    """Start the configured editor with one absolute file-and-line argument.

    The configuration is a JSON argument list, such as ["code", "--goto"].
    The file is a source path supplied by Details. A recipe can refer to
    a file outside the model folder; external navigation requests use
    navigation_request instead. No argument is interpreted by a shell.
    """
    if not isinstance(file, str) or not file or "\x00" in file:
        raise ValueError("The source must name a file.")
    if type(line) is not int or not 1 <= line <= 2_147_483_647:
        raise ValueError("The source line must be a positive integer.")
    target = (root / file).resolve()
    if not target.is_file():
        raise ValueError(f"The source file does not exist: {file}")
    try:
        arguments = json.loads(command)
    except (TypeError, ValueError) as error:
        raise ValueError("The editor command must be a JSON list of arguments.") from error
    if (
        not isinstance(arguments, list)
        or not arguments
        or any(not isinstance(part, str) or not part or "\x00" in part for part in arguments)
    ):
        raise ValueError("The editor command must be a nonempty JSON list of arguments.")
    if os.name == "nt" and arguments[0].lower().endswith((".cmd", ".bat")):
        raise ValueError("The editor command must name an executable program, such as Code.exe.")
    process_options = (
        {
            "creationflags": subprocess.CREATE_BREAKAWAY_FROM_JOB
            | subprocess.CREATE_NEW_PROCESS_GROUP
        }
        if os.name == "nt"
        else {"start_new_session": True}
    )
    subprocess.Popen(
        [*arguments, f"{target}:{line}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **process_options,
    )
