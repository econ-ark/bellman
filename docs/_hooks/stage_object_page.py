"""Print the listings of a public page from the package.

A page alternates a `python` block and, where it shows a result, the `text`
block that holds what that block prints. This script runs the page's own
python blocks, in order, in one namespace with the repository root as the
working directory, and writes what each printed into the `text` block that
follows it. Nothing on such a page is described from a specification: a
listing that changes when the package changes is regenerated here.

The pages it prints are those `printed_pages` names: every page of the API,
under `docs/Bellman-Sym/API/`, the nine pages of the stage object under
`API/stage/` among them, and every reference page, under
`docs/Bellman-Sym/reference/`, that holds a listing. `--page` names one page,
of these or another written in the same way, and may be given more than
once.

Run from the repository root with the project interpreter:

    PYTHONPATH=packages/bellman python docs/_hooks/stage_object_page.py
    PYTHONPATH=packages/bellman python docs/_hooks/stage_object_page.py --check

The first rewrites the listings of every page; `--check` reports the blocks
that differ and writes nothing. `settle` writes a page or reports how it
differs from what the package prints; `reference_pages.py` beside this script
writes the tables of the reference pages through it, so that every page
printed from the package is written and checked one way.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # the repository root, above docs/_hooks/

# the folders whose pages hold listings printed here: the API pages and the
# reference pages
API = "docs/Bellman-Sym/API"
REFERENCE = "docs/Bellman-Sym/reference"

# every ```python block, with the ```text block that follows it when there
# is one
BLOCK = re.compile(
    r"```python\n(?P<code>.*?)```(?P<gap>\n\n```text\n(?P<printed>.*?)```)?", re.DOTALL
)


def listings(text):
    """(code, printed) of every python block of the page, in page order;
    `printed` is None for a block the page shows no result for."""
    return [(m.group("code"), m.group("printed")) for m in BLOCK.finditer(text)]


def holds_a_listing(text):
    """Whether the page shows what at least one python block prints."""
    return any(printed is not None for _, printed in listings(text))


def printed_pages(root=ROOT):
    """The pages this script prints, as paths relative to the repository root
    in sorted order: every page under `API` and `REFERENCE` that holds a
    listing."""
    found = [
        page
        for folder in (API, REFERENCE)
        for page in sorted((root / folder).rglob("*.md"))
        if holds_a_listing(page.read_text(encoding="utf-8"))
    ]
    return sorted(page.relative_to(root).as_posix() for page in found)


def run(code_blocks, page):
    """What each code block prints, run in order in one namespace."""
    namespace = {"__name__": "__main__"}
    printed = []
    for code in code_blocks:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(compile(code, str(page), "exec"), namespace)
        printed.append(buffer.getvalue())
    return printed


def rewrite(text, printed):
    """The page with each text block replaced by what its python block
    printed."""
    blocks = iter(printed)

    def replace(match):
        result = next(blocks)
        if match.group("gap") is None:
            return match.group(0)
        return f"```python\n{match.group('code')}```\n\n```text\n{result}```"
    return BLOCK.sub(replace, text)


def settle(page, shown, rewritten, check, what="listing", numbered="block"):
    """Write one page, or with `check` report how it differs from what the
    package prints. `shown` holds (number, held, fresh) for each generated
    part of the page: the number `numbered` names it by, what the page holds
    and what the package prints; `rewritten` is the page's text with every
    part as the package prints it, and `what` names one such part. Returns 1
    when `check` finds a part that differs, else 0."""
    where = page.relative_to(ROOT)
    counted = f"{len(shown)} {what}" + ("" if len(shown) == 1 else "s")
    if check:
        differing = [(number, held, fresh) for number, held, fresh in shown if held != fresh]
        for number, held, fresh in differing:
            print(f"{where}: {numbered} {number} differs from what the package prints")
            print("--- on the page ---")
            print(held, end="" if held.endswith("\n") else "\n")
            print("--- from the package ---")
            print(fresh, end="" if fresh.endswith("\n") else "\n")
        if differing:
            return 1
        print(f"{where}: {counted} {'agrees' if len(shown) == 1 else 'agree'} with the package")
        return 0
    page.write_text(rewritten, encoding="utf-8")
    print(f"wrote {counted} into {where}")
    return 0


def print_page(relative, check):
    """Run the python blocks of one page and write or check its listings;
    returns 1 when `check` finds a listing that differs, else 0."""
    page = ROOT / relative
    text = page.read_text(encoding="utf-8")
    pairs = listings(text)
    if not pairs:
        raise SystemExit(f"{page} holds no python block")
    printed = run([code for code, _ in pairs], page)
    shown = [
        (number, held, fresh)
        for number, ((_, held), fresh) in enumerate(zip(pairs, printed), start=1)
        if held is not None
    ]
    return settle(page, shown, rewrite(text, printed), check)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report the blocks that differ; write nothing")
    parser.add_argument("--page", action="append",
                        help="a page to run, relative to the repository root; may be given "
                             "more than once (default: every page `printed_pages` names)")
    arguments = parser.parse_args()
    os.chdir(ROOT)
    pages = arguments.page or printed_pages()
    return 1 if any([print_page(page, arguments.check) for page in pages]) else 0


if __name__ == "__main__":
    sys.exit(main())
