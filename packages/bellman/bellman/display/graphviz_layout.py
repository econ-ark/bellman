"""The layout of a drawing: `layout_svg` answers the SVG of a DOT source, laid
out by Graphviz's `dot` when that program is on the PATH and otherwise by the
WebAssembly build of Graphviz, the Node package `@viz-js/viz`, which Node runs
through the script `graphviz_layout.mjs` beside this module. Both programs
read the same DOT text on standard input and write SVG. `Drawing.svg()` and
`Drawing._repr_svg_` (`drawing.py`) lay a drawing out through `layout_svg`,
so a drawing of a graph, of a period or of a trellis answers its picture
wherever one of the two programs is installed, and refuses with the sentence
of `layout_refusal` where neither is.

The Node package is installed by `npm install` in the package's folder
`packages/bellman/`, whose `package.json` pins its version, into `node_modules/`
there, which
git ignores; no other folder is read. The Node executable is the one on the
PATH, else the newest one nvm installed, else Homebrew's: a kernel started by
an application rather than by a shell has no nvm path.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# the folder packages/bellman/, which holds package.json and, once `npm install`
# has run there, node_modules/
PACKAGE_FOLDER = Path(__file__).resolve().parents[2]
# the folder of the Node package under it
NODE_PACKAGE = Path("node_modules") / "@viz-js" / "viz"
LAYOUT_SCRIPT = Path(__file__).with_name("graphviz_layout.mjs")
# the Node executables read after the PATH: nvm's installations,
# then Homebrew's
NVM_NODES = Path.home() / ".nvm/versions/node"
HOMEBREW_NODES = (Path("/opt/homebrew/bin/node"), Path("/usr/local/bin/node"))


def dot_program() -> str | None:
    """The path of Graphviz's `dot`, or None when it is not on the PATH."""
    return shutil.which("dot")


def node_program() -> str | None:
    """The path of the Node executable: the one on the PATH, else the newest
    one nvm installed, else Homebrew's; None when there is none."""
    found = shutil.which("node")
    if found is not None:
        return found
    installed = sorted(
        NVM_NODES.glob("*/bin/node"), key=lambda path: _release(path.parents[1].name)
    )
    for candidate in installed[-1:] + list(HOMEBREW_NODES):
        if candidate.is_file():
            return str(candidate)
    return None


def _release(folder_name: str) -> list[int]:
    """The release numbers of an nvm folder name, `v22.17.1` as [22, 17, 1],
    which order the installations."""
    return [int(part) for part in folder_name.lstrip("v").split(".") if part.isdigit()]


def node_package_root() -> Path | None:
    """The folder packages/bellman/ when its `node_modules` holds the WebAssembly build
    of Graphviz; None when it does not."""
    if (PACKAGE_FOLDER / NODE_PACKAGE).is_dir():
        return PACKAGE_FOLDER
    return None


def layout_command() -> list[str] | None:
    """The command that lays the DOT text on its standard input out as SVG:
    `dot -Tsvg` when `dot` is on the PATH, else Node running the layout script
    on the installed Node package; None when no layout program is available."""
    dot = dot_program()
    if dot is not None:
        return [dot, "-Tsvg"]
    node, root = node_program(), node_package_root()
    if node is None or root is None:
        return None
    return [node, str(LAYOUT_SCRIPT), str(root)]


def layout_refusal() -> str:
    """The sentence a refusal states when no layout program is available: what
    is missing, and what to install or run."""
    missing = []
    if node_program() is None:
        missing.append("Node.js on the PATH, or installed by nvm or Homebrew")
    if node_package_root() is None:
        missing.append(
            f"the Node package @viz-js/viz, installed by `npm install` in packages/bellman/, "
            f"{PACKAGE_FOLDER}"
        )
    return (
        "No Graphviz layout program is available: install Graphviz's dot, or supply "
        + " and ".join(missing)
        + "."
    )


def layout_svg(source: str) -> str:
    """The SVG text of a DOT source, laid out by `layout_command`. Refuses
    with `layout_refusal` when no layout program is available, and with the
    program's own message when it exits with an error."""
    command = layout_command()
    if command is None:
        raise RuntimeError(layout_refusal())
    result = subprocess.run(command, input=source, capture_output=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(
            f"{command[0]} exited with status {result.returncode}:\n{result.stderr}"
        )
    return result.stdout
