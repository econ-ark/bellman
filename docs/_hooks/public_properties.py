"""MkDocs hook: a published page shows neither a status icon nor tag chips.

The front-matter keys ``status`` and ``tags`` are the repository's own
properties, read by Obsidian and by the script ``document_properties.py``;
Material for MkDocs would draw a status icon beside the page's navigation
entry and the tags plugin would print the tags as chips above the page.
The hook removes both keys from the page's metadata before any plugin reads
them. The source files keep their front matter unchanged (AAS, 10 November
2026, the website review's §3).
"""

from mkdocs.plugins import event_priority


@event_priority(100)
def on_page_markdown(markdown, *, page, config, files):
    """Removes ``status`` and ``tags`` from the page's metadata; the text is unchanged."""
    page.meta.pop("status", None)
    page.meta.pop("tags", None)
    return markdown
