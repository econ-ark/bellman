"""The notes of a stage file under Node (design pass 10 §9; AAS's brief of
12 October 2026, § Rendered annotation comments; unit N, Task 4).

The editor bundle, `bellman_workbench/public/codemirror/bellman-workbench.js`,
is run under Node in a context of its own, as `test_flow_layout.py` runs the
layout script. Its function `noteMarkersOf` answers the spans the editor's
decoration set draws as note glyphs in a text, with the cursor at the
text's start, whose line is drawn in full; on `retiree_cons.bl` the glyph
replaces exactly the quoted explanation of lines 5 and 11 and keeps the
entry `id=feasible`, and on lines written for the cases the rule must
decide, a quoted entry or a bare
quoted annotation is a note, while a `#` comment, an unquoted entry, a
marked tag and a quoted string outside an annotation are drawn as written;
a note holding `!` that begins no tag, `"x != y"`, is tokenized. Its
function `notePreview` answers the preview's HTML: Markdown with the
mathematics between `\\(` and `\\)` or `\\[` and `\\]` typeset by KaTeX, and
no image or link; a formula KaTeX cannot typeset is drawn as written, with
no hover and no color of its own. The tests are skipped when `node` is not
on the PATH.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from workbench_support import node_output

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = (
    ROOT / "packages/bellman-workbench/bellman_workbench/public/codemirror/bellman-workbench.js"
)
RETIREE_CONS = (
    ROOT / "applications/retirement-choice/declaration/stages/retiree_cons/retiree_cons.bl"
)
# the retiree's methods file, the addition beside its stage file, which holds
# the inverse Euler line with its note since the endogenous grid method moved
# out of the stage file (decision MB-S24), and the three declarations of its
# settings with their notes
RETIREE_METHODS = (
    ROOT / "applications/retirement-choice/declaration/stages/retiree_cons/methods.bl"
)
# the lines of the methods file that hold a note: the three declarations and
# the inverse Euler line
RETIREE_METHODS_NOTES = (19, 20, 21, 24)

# lines written for the cases the rule decides, each with the texts the
# glyphs replace on it: a `!` that begins no tag inside a note, a comma
# inside a note beside a marked tag, a bare quoted annotation, an unquoted
# annotation, an entry with no quote, a `#` comment holding an annotation, a
# quoted string in a block header, two notes in one annotation, an
# unterminated quote and an annotation with no entry
EDGE_LINES = {
    'x = 1   :: [id=a, "x != y"]': ['"x != y"'],
    'v = 5   :: [id=c, "a, b", !doc]': ['"a, b"'],
    'w = 4   :: "a bare note"': ['"a bare note"'],
    "z = 3   :: plain words": [],
    "y = 2   :: [id=b, !doc]": [],
    '# a comment :: ["not a note"]': [],
    '[id=p, (a : X) : !cntn -> (c : X) : !dcsn, "method = egm! here"] {': [],
    'u = 6   :: ["first", id=d, "second"]': ['"first"', '"second"'],
    't = 7   :: [id=e, "unterminated]': [],
    "s = 8   ::": [],
}

# the Node module: runs the bundle, reads {texts, notes} on standard input
# and prints, for every text, the spans of the glyphs and its lines drawn
# with each span removed, and for every note the preview's HTML
NODE_SCRIPT = """
import { readFileSync } from "node:fs";
import vm from "node:vm";

const context = {};
vm.runInNewContext(readFileSync(%(bundle)s, "utf8"), context);
const editor = context.bellmanEditor;
const input = JSON.parse(readFileSync(0, "utf8"));

const markers = {};
for (const [name, text] of Object.entries(input.texts)) {
  const found = editor.noteMarkersOf(text);
  const drawn = text.split("\\n");
  for (const span of found.slice().reverse()) {
    const line = drawn[span.line - 1];
    drawn[span.line - 1] = line.slice(0, span.from) + line.slice(span.to);
  }
  markers[name] = { found: JSON.parse(JSON.stringify(found)), drawn };
}
const previews = input.notes.map((note) => editor.notePreview(note));
console.log(JSON.stringify({ markers, previews }));
"""

NOTES = [
    "\\(x^2\\)",
    "**k**",
    "\\[V = \\max_c u(c)\\]",
    "![a picture](https://example.org/a.png) and [a link](https://example.org)",
    "x != y",
    # formulas KaTeX cannot typeset: a parse error, inline and displayed,
    # and a command KaTeX does not define
    "\\(x^}\\) or \\[x^}\\] or \\(\\nosuchcommand\\)",
    # a command KaTeX does not trust, which it draws as its name
    "\\(\\href{https://example.org}{x}\\)",
]


@pytest.fixture(scope="module")
def notes(node) -> dict:
    """The output of the Node module over `retiree_cons.bl`, keyed
    `retiree_cons`, over its methods file `methods.bl`, keyed
    `retiree_methods`, and the edge lines, keyed `edge lines`, and the
    previews of NOTES."""
    texts = {
        "retiree_cons": RETIREE_CONS.read_text(encoding="utf-8"),
        "retiree_methods": RETIREE_METHODS.read_text(encoding="utf-8"),
        # the cursor's line, the first, is drawn in full
        "edge lines": "\n".join(["@stage: edge_lines", *EDGE_LINES]),
    }
    script = NODE_SCRIPT % {"bundle": json.dumps(str(BUNDLE))}
    return node_output(node, script, {"texts": texts, "notes": NOTES})


def test_the_glyph_replaces_exactly_the_quoted_explanation_of_retiree_cons(notes):
    """On `retiree_cons.bl` the decoration set replaces the quoted
    explanation of lines 5, 6 and 11, and on its methods file `methods.bl`
    those of its three declarations, lines 19 to 21, and of the inverse Euler
    line, line 24, each span from its opening to its closing quote: line 5 is
    drawn `:: []`, and line 11 keeps its entry `id=feasible`,
    `:: [id=feasible, ]`; the quoted handler names in the block headers of
    the methods file and every line holding no note are drawn as written."""
    lines = RETIREE_CONS.read_text(encoding="utf-8").split("\n")
    found = notes["markers"]["retiree_cons"]["found"]
    assert [(span["line"], span["text"]) for span in found] == [
        (5, '"discount factor"'),
        (6, '"gross return on assets"'),
        (11, '"empty at zero resources"'),
    ]
    drawn = notes["markers"]["retiree_cons"]["drawn"]
    assert drawn[4] == "β : (0,1)        :: []"
    assert drawn[10] == "Γ(x : ℝ₊) := (0, x]                 :: [id=feasible, ]"
    noted = {span["line"] for span in found}
    assert [line for number, line in enumerate(drawn, 1) if number not in noted] == [
        line for number, line in enumerate(lines, 1) if number not in noted
    ]
    lines = RETIREE_METHODS.read_text(encoding="utf-8").split("\n")
    found = notes["markers"]["retiree_methods"]["found"]
    assert [(span["line"], span["text"]) for span in found] == [
        (number, lines[number - 1][lines[number - 1].index('"') :].rstrip("]"))
        for number in RETIREE_METHODS_NOTES
    ]
    drawn = notes["markers"]["retiree_methods"]["drawn"]
    noted = set(RETIREE_METHODS_NOTES)
    assert [line for number, line in enumerate(drawn, 1) if number not in noted] == [
        line for number, line in enumerate(lines, 1) if number not in noted
    ]


def test_the_edge_lines_draw_their_notes_alone_and_tokenize(notes):
    """On the edge lines, each glyph replaces the quoted entries the
    package reads as tags and nothing else: a note holding `!` before `=`
    is tokenized, and a comment, an unquoted entry, a marked tag, a header's
    quoted string and an unterminated quote are drawn as written."""
    found = notes["markers"]["edge lines"]["found"]
    for number, (line, texts) in enumerate(EDGE_LINES.items(), 2):
        spans = [span for span in found if span["line"] == number]
        assert [span["text"] for span in spans] == texts, line
        for span in spans:
            assert line[span["from"] : span["to"]] == span["text"], line
    drawn = notes["markers"]["edge lines"]["drawn"]
    assert drawn[1] == "x = 1   :: [id=a, ]"
    assert drawn[2] == "v = 5   :: [id=c, , !doc]"


def test_the_preview_renders_markdown_and_typesets_mathematics(notes):
    """The preview's HTML: `\\(x^2\\)` holds a KaTeX span, `**k**` a
    `<strong>`, `\\[…\\]` KaTeX's display, an image or a link written in
    Markdown neither an `<img>` nor an `<a>`, so that the preview fetches
    nothing and leaves the page in place, and `x != y` the text as
    written."""
    inline, strong, display, picture, plain = notes["previews"][:5]
    assert '<span class="katex">' in inline and "x^2" in inline
    assert "<strong>k</strong>" in strong
    assert '<span class="katex-display">' in display
    assert "<img" not in picture and "<a " not in picture
    assert "x != y" in plain


def test_a_formula_that_cannot_be_typeset_has_no_hover_and_no_color_of_its_own(notes):
    """The texts' rule of the plan: the preview adds no hover and no color
    that design pass 10 §9 does not give. A formula KaTeX cannot typeset,
    a parse error or a command KaTeX does not define, is drawn as written,
    its delimiters included, in the preview's own ink, with no `title`; a
    command KaTeX does not trust, `\\href`, is drawn as its name in the
    preview's own ink and is no link."""
    unreadable, untrusted = notes["previews"][5:]
    assert "title=" not in unreadable and "katex-error" not in unreadable
    assert "color" not in unreadable
    assert "\\(x^}\\) or \\[x^}\\] or \\(\\nosuchcommand\\)" in unreadable
    assert "<a " not in untrusted and "title=" not in untrusted
    colors = re.findall(r'color(?::|=")\s*([^;"]+)', untrusted)
    assert colors and set(colors) == {"currentColor"}, colors
