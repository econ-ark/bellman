"""The icons of Bellman Workbench (design pass 8 §§3 and 3a; AAS, M-D4,
M-D18).

Codicons, VS Code's icon set (`@vscode/codicons` 0.0.45, copied unmodified
under `public/codicons/` with its licenses), draws every icon of the page:
`codicon` draws one glyph by its Codicons name, and
`CODICONS` names the glyph of each control that draws one. VSCode
Elements' toolbar buttons draw the same glyphs from the same stylesheet,
by the name in their attribute `icon`, and the graph's bundle draws its
own, the foot's controls, the lists' heads and items and a card's chevron,
by the same names (flow-canvas.js).

The icons of the main bar's four toggles are taken from the same set at
16 px, with the brand's glyphs typeset by the browser in the page's fonts,
and no path drawn by hand (design pass 8 §3a as AAS's M-D18 amends it;
design pass 10 §3; N-D10): `TOGGLE_ICONS` names each panel's Codicon and
glyph, and `toggle_icon` draws them in the color of the button's text.

Lucide's glyphs, which the graph region and Matsya's column drew until
Task 7 of unit M, are deleted with their last reader (design pass 8 §8,
item 2).
"""

from __future__ import annotations

import reacton.ipyvuetify as rv

# The icon of each toggle of the main bar, by the fold the toggle toggles
# (design pass 10 §3; N-D10, keeping AAS's M-D18): the Codicon that carries
# the panel's meaning, or the set's container for the panel's glyph, None
# where the icon takes none; and the glyph the browser typesets in the
# page's fonts, None where the icon takes none. The meanings are AAS's
# (M-D5, M-D8 to M-D10), the Inspector's design pass 10's: the folder's
# files; a panel under a layout, the panel under the editor; the
# denotation brackets ⟦·⟧, what the selected piece denotes; and Υ, the
# brand's letter for Matsya, in a speech bubble.
TOGGLE_ICONS = {
    "folder": ("files", None),
    "inspector": ("layout-panel", None),
    "details": (None, "⟦·⟧"),
    "matsya": ("comment", "Υ"),
}

# The Codicon of each control that draws one (design pass 8 §3): on the
# main bar and the status line, the history's steps, Goto Anything, the
# error mark, the construction's mark while the state is `constructed` and
# while it is not, and the status line's button that shows its details and
# hides them again; then those of the regions of Tasks 6 and 7.
CODICONS = {
    "back": "arrow-left",
    "forward": "arrow-right",
    "go to": "search",
    # the separator between two parts of the main bar's path (design pass
    # 13 §3; C4)
    "path separator": "chevron-right",
    # the problems count: `error` while an error stands, `warning` while
    # only checks to review stand, both in the alarm's orange (design pass
    # 13 §5; Q-D8)
    "error mark": "error",
    "checks mark": "warning",
    "constructed": "pass-filled",
    "not constructed": "circle-large-outline",
    "more": "chevron-up",
    "less": "chevron-down",
    # the folder column, the editor, the panel under the editor and the
    # forms (Task 6 of unit M): the folder's head, a folder of the tree
    # folded and unfolded, the checklist's head folded and unfolded, a
    # control that deletes a file or removes a stage, a panel's head, the
    # editor's tab row, the add row of the Fields tab, and each form's head
    # and the entries of its lists
    "new trellis": "new-folder",
    "new variant": "versions",
    "new stage": "new-file",
    # the Recipe tab's button that writes a slot's own file (design pass 10
    # §4)
    "new file": "new-file",
    "notebook": "notebook",
    "folded": "chevron-right",
    "unfolded": "chevron-down",
    "remove": "trash",
    "open wide": "window",
    "close": "close",
    "unsaved": "circle-filled",
    "add": "add",
    "add stage": "symbol-structure",
    "add period": "split-horizontal",
    "commit": "git-commit",
    "folder": "folder",
    "file": "file",
    "above": "arrow-up",
    "checked": "check",
    "refused template": "warning",
    # the graph column, Details and Matsya's column (Task 7 of unit M):
    # the perch overlays at the canvas's foot, the fold of Matsya's column
    # and the question sent to Matsya
    "perch overlays": "layers",
    # the layers button of the graph bar, while the declared builders are
    # shown and while the operative builders are (specification 0.6 §9;
    # design pass 15; SE-2)
    "declared builders": "layers-dot",
    "operative builders": "layers-active",
    "fold matsya": "close",
    "ask matsya": "send",
    # Matsya's column after design pass 16 (unit G4 of specification 0.6):
    # the context chips of the composer, the source, the session, the job
    # discussed and the service; a citation of a file, of a retrieved
    # passage and of a destination that cannot be resolved; and the actions
    # on a job's returned files
    "matsya source": "file",
    "matsya session": "comment-discussion",
    "matsya job": "tasklist",
    "matsya service": "server",
    "cited file": "file",
    "cited passage": "book",
    "cited unavailable": "circle-slash",
    "download returned files": "cloud-download",
    "open returned files": "folder-opened",
    "replace model files": "diff",
    "connect folder": "plug",
}


def codicon(name: str, classes: str = "", attributes: dict | None = None, children=()):
    """The Codicon `name` as the element Codicons' stylesheet draws, `<i
    class="codicon codicon-<name>">` (design pass 8 §3), with the classes
    `classes`, the attributes `attributes` and the children `children`, 16
    px in the color of its text and hidden from assistive technology, since
    the control that holds it carries the name and the hover."""
    return rv.Html(
        tag="i",
        class_=f"codicon codicon-{name} {classes}".strip(),
        attributes={**(attributes or {}), "aria-hidden": "true"},
        children=list(children),
    )


def toggle_icon(fold: str):
    """The icon of the main bar's toggle for the fold `fold`
    (`TOGGLE_ICONS`; design pass 10 §3; N-D10): a span `.bl-toggle-icon` of
    16 × 16 px, hidden from assistive technology, since the toggle carries
    the panel's name, holding the panel's Codicon at 16 px and its glyph,
    `.bl-toggle-glyph`, whose data-glyph brand.css sets as the content of
    its ::before, as Codicons set theirs, in STIX Two Math; both in the
    color of the button's text."""
    name, glyph = TOGGLE_ICONS[fold]
    children = []
    if name is not None:
        children.append(codicon(name))
    if glyph is not None:
        children.append(
            rv.Html(tag="span", class_="bl-toggle-glyph", attributes={"data-glyph": glyph})
        )
    return rv.Html(
        tag="span",
        class_="bl-toggle-icon",
        attributes={"aria-hidden": "true"},
        children=children,
    )
