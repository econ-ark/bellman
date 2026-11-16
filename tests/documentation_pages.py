"""The anchors that MkDocs gives headings, and the patterns and functions that
read the links, the generated part and the entries of a page."""

import posixpath
import re
import sys

from documentation_paths import HOOKS
from skips import require_package

# the anchors that MkDocs gives headings, from the package markdown of the
# extra `docs`, which the generator of the pages imports too; every test of a
# file that imports this module is skipped where it is not installed
slugify = require_package("markdown.extensions.toc", extra="docs").slugify


# The folder of the hooks, which holds the generator of the pages,
# reference_pages.py, stands first on the module path once this module is
# imported, so that this module and the files that import it import the
# generator.
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))


# the markers of a generated part and the reader of a table row, from the
# generator that writes the pages
from reference_pages import MARKERS, table_cells  # noqa: E402

# a markdown link that is not an image, with its text and its target
MARKDOWN_LINK = re.compile(
    r"(?<!!)\[(?P<text>[^\]\n]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)"
)


# the line that opens or closes a fenced block
FENCE_LINE = re.compile(r"^\s*(```|~~~)")


# the line that opens an entry of the methods page: its anchor, then, after
# one empty line, its numbered heading with the word
ENTRY_HEADING = re.compile(r'^<a id="([^"]+)"></a>\n\n### \d+\.\d+ `(![^`]+)`$', re.MULTILINE)


# the label in bold that opens a part of an entry, such as `**Declaration.**`
PART_LABEL = re.compile(r"^\*\*([A-Z][a-z]+(?: [a-z]+)*)\.\*\*", re.MULTILINE)


def links(text):
    """(line number, the line, the text, the target) of every markdown link of
    a page outside a fenced block and outside a code span; the text of a link
    may hold a code span."""
    found, fenced = [], False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE_LINE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        spans = [match.span() for match in re.finditer(r"`[^`]*`", line)]
        found += [
            (number, line, m.group("text"), m.group("target"))
            for m in MARKDOWN_LINK.finditer(line)
            if not any(start < m.start() < end for start, end in spans)
        ]
    return found


def link_target_path(page, target):
    """The path under docs/ a relative link of a page reaches, its anchor
    apart; None for a link that leaves the site, an anchor on the same page,
    or a link outside docs/."""
    if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
        return None
    path = target.split("#")[0].replace("%20", " ")
    reached = posixpath.normpath(posixpath.join(posixpath.dirname(page), path))
    return None if reached.startswith("..") else reached


def generated_part(text):
    """What stands between the two markers of a page, or None."""
    if text.count(MARKERS[0]) != 1 or text.count(MARKERS[1]) != 1:
        return None
    start, end = text.index(MARKERS[0]) + len(MARKERS[0]), text.index(MARKERS[1])
    return text[start:end] if start <= end else None


def reference_entries(text):
    """The entries of the generated part of the methods page, in order, each
    as (its anchor, its word with the `!`, its parts by label, each part's
    text from its label to the next label, and the rows of its argument
    table)."""
    held = generated_part(text) if MARKERS[0] in text else text
    found = list(ENTRY_HEADING.finditer(held))
    entries = []
    for number, match in enumerate(found):
        end = found[number + 1].start() if number + 1 < len(found) else len(held)
        body = held[match.end() : end]
        body = re.split(r"^## ", body, flags=re.MULTILINE)[0]
        labels = list(PART_LABEL.finditer(body))
        parts = {
            label.group(1): body[
                label.end() : (labels[index + 1].start() if index + 1 < len(labels) else len(body))
            ].strip()
            for index, label in enumerate(labels)
        }
        # the rows of the argument table, its head apart
        arguments = [
            cells for cells in map(table_cells, parts.get("Arguments", "").splitlines()) if cells
        ][1:]
        entries.append((match.group(1), match.group(2), parts, arguments))
    return entries
