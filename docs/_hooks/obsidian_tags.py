#!/usr/bin/env python3
"""MkDocs hook — render standalone Obsidian tag lines as subtle chips.

Cards and notes in this repo carry Obsidian inline tags on their own line, e.g.

    #rosetta-stone #handler/hark #egm #model_locked

python-markdown treats a leading ``#`` as an ATX heading even without a space, so
such a line otherwise renders as a large ``<h1>``. This hook leaves a *tag-only*
line (outside fenced code) out of the rendered page: since 10 November 2026 the
published pages show no tag chips at all (the website review of that day, §3).

The hook only touches the in-memory Markdown handed to the renderer — the source
``.md`` files keep their ``#tags`` verbatim, so they stay Obsidian-friendly
(per the project's "never strip #tags" rule).

Registered in ``mkdocs.yml`` under ``hooks:``.
"""
import re

# An Obsidian tag: '#', then a letter/underscore, then word / '/' / '-' chars
# (covers nested tags like #handler/hark and hyphenated tags like #pre-dcnsn-shock).
_TAG = r"#[A-Za-z_][\w/-]*"
_TAGLINE = re.compile(rf"^(?:{_TAG})(?:[ \t]+{_TAG})*[ \t]*$")
_FENCE = re.compile(r"^\s*(```|~~~)")


def on_page_markdown(markdown, **kwargs):  # noqa: D401 (MkDocs hook signature)
    if "#" not in markdown:
        return markdown
    out, in_fence = [], False
    for line in markdown.split("\n"):
        if _FENCE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        stripped = line.strip()
        if not in_fence and stripped and _TAGLINE.match(stripped):
            # The published page shows no tag chips (AAS, 10 November 2026); the
            # source file keeps the line, and the renderer never sees it as a heading.
            continue
        else:
            out.append(line)
    return "\n".join(out)
