"""Print a stage's view, encoding, dossier or the catalogue of refusals.

See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5 for the public queries.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from bellman.dossier import dossier_lines, origin_of
from bellman.factory.elaboration import elaborate_text
from bellman.refusal_catalogue import catalogue
from bellman.refusals import ConstructionError


def main(argv=None):
    """Print the requested answer, or the structured refusal of a stage file.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""
    parser = argparse.ArgumentParser(prog="python -m bellman", description=__doc__.splitlines()[0])
    parser.add_argument("stage", type=Path, nargs="?", help="the stage file, a .bl file")
    outputs = parser.add_mutually_exclusive_group()
    outputs.add_argument("--encoding", action="store_true", help="print the stage's JSON encoding")
    outputs.add_argument(
        "--dossier", action="store_true", help="print the dossier with its source"
    )
    outputs.add_argument("--refusals", action="store_true", help="print the catalogue of refusals")
    arguments = parser.parse_args(argv)
    if arguments.refusals:
        print(catalogue())
        return 0
    if arguments.stage is None:
        parser.error("the stage file is required unless --refusals is selected")
    try:
        stage = elaborate_text(
            arguments.stage.read_text(encoding="utf-8"), origin_of(arguments.stage)
        )
        if arguments.dossier:
            answer = "\n".join(dossier_lines(stage, arguments.stage, with_source=True))
        elif arguments.encoding:
            answer = stage.encoding()
        else:
            answer = stage.view()
    except ConstructionError as refusal:
        print(refusal)
        return 1
    except OSError as refusal:
        print(
            f"where   {arguments.stage}\n"
            "what    the stage source could not be read\n"
            f"why     {refusal.strerror or refusal}\n"
            "write   supply the path of a readable .bl file"
        )
        return 1
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
