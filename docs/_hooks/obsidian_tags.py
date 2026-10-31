#!/usr/bin/env python3
"""MkDocs hook — render standalone Obsidian tag lines as subtle chips.

Cards and notes in this repo carry Obsidian inline tags on their own line, e.g.

    #rosetta-stone #handler/hark #egm #model_locked

python-markdown treats a leading ``#`` as an ATX heading even without a space, so
such a line otherwise renders as a large ``<h1>``. This hook rewrites a *tag-only*
line (outside fenced code) into a small chip row, so the published page shows the
tags quietly under the title instead of as a giant heading.

The hook only touches the in-memory Markdown handed to the renderer — the source
``.md`` files keep their ``#tags`` verbatim, so they stay Obsidian-friendly
(per the project's "never strip #tags" rule). Styling lives in
``docs/_stylesheets/rosetta.css`` (``.obsidian-tags`` / ``.obsidian-tag``).

Registered in ``mkdocs.yml`` under ``hooks:``.
"""
import re

# An Obsidian tag: '#', then a letter/underscore, then word / '/' / '-' chars
# (covers nested tags like #handler/hark and hyphenated tags like #pre-dcnsn-shock).
_TAG = r"#[A-Za-z_][\w/-]*"
_TAGLINE = re.compile(rf"^(?:{_TAG})(?:[ \t]+{_TAG})*[ \t]*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_TAG_FIND = re.compile(_TAG)


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
            chips = "".join(
                f'<span class="obsidian-tag">{t}</span>'
                for t in _TAG_FIND.findall(stripped)
            )
            out.append(f'<nav class="obsidian-tags" aria-label="tags">{chips}</nav>')
        else:
            out.append(line)
    return "\n".join(out)
