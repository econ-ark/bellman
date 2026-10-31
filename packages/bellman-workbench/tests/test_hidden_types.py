"""The rule of the hidden types under Node (model interface specification
0.3, §2.2 rule 5).

The editor's range finder, `js/codemirror/src/hidden_types.js`, hides the
same spans as the VS Code extension's own function `hiddenRanges` in
`editor/dynspec-vscode/extension.js`, on every line of every stage file of
the applications (the folders directly under `applications/`) and on lines
written for the cases the rule must decide, once with no line in full and
once with a selection's lines in full; the extension's function is read from
its file and run with a stand-in of the module `vscode`. On `cons.bl` the
lines drawn with the spans hidden read as the names alone. The tests are
skipped when `node` is not on the PATH.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from workbench_support import node_output

ROOT = Path(__file__).resolve().parents[3]
FINDER = ROOT / "packages/bellman-workbench/js/codemirror/src/hidden_types.js"
EXTENSION = ROOT / "editor/dynspec-vscode/extension.js"
APPLICATIONS = ROOT / "applications"
# the stage file of the consumption stage, relative to the repository
CONS_PATH = "applications/portfolio-choice/declaration/stages/cons/cons.bl"

# lines written for the cases the rule decides: a header whose types hold a
# half-open interval, a label group, an annotation, spaces around the key,
# three groups on one line, a group the line does not close, a group closed
# by `)` before a later group, a name of another alphabet, a name that
# continues in another alphabet, a group in a comment, a key that is no key,
# a selection bracket before a group, an empty name, nested groups
EDGE_LINES = [
    "[id=g_ad, (m : Xm) : !arvl -> (m_d : Xm) : !dcsn] {",
    "[label=work, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (V : ℝ) : !dcsn] {",
    "x = 𝑢(c) + V[>]   :: [id=cash_on_hand]",
    "[ id = spaced , tail ]",
    "[id=a] [id=b, t] [label=c]",
    "[id=open, (a : [0, 1) ",
    "[id=bad, a) [id=after]",
    "[id=ν, tail]",
    "[id=foc_ς, tail]",
    "# a comment [id=in_comment, tail]",
    "[idx=not_a_group]",
    "V[>][id=work]",
    "[label=]",
    "[id=a, [id=b, c]] [id=d]",
    "",
    "[",
]

# the Node module: reads {texts, extension} on standard input and prints,
# for every text, the extension's spans and the finder's, with no line in
# full and with lines 2 to 5 in full, and the lines drawn with the spans
# hidden
NODE_SCRIPT = """
import { readFileSync } from "node:fs";
import { hiddenRanges } from %(finder)s;

const input = JSON.parse(readFileSync(0, "utf8"));
class Range {
  constructor(startLine, startCharacter, endLine, endCharacter) {
    this.start = { line: startLine, character: startCharacter };
    this.end = { line: endLine, character: endCharacter };
  }
}
const vscode = {
  Range,
  DecorationRangeBehavior: { ClosedClosed: 0 },
  window: { createTextEditorDecorationType: () => ({}) },
};
const source = readFileSync(input.extension, "utf8");
const extensionRanges = new Function("require", "module", "exports",
  `${source}\\nreturn hiddenRanges;`)(() => vscode, { exports: {} }, {});

const output = {};
for (const [name, text] of Object.entries(input.texts)) {
  const lines = text.split(/\\r\\n?|\\n/);
  const document = { lineCount: lines.length, lineAt: (line) => ({ text: lines[line] }) };
  const runs = [];
  for (const selections of [[], [{ start: { line: 2 }, end: { line: 5 } }]]) {
    const shown = new Set();
    for (const s of selections) for (let l = s.start.line; l <= s.end.line; l++) shown.add(l);
    const extension = extensionRanges(document, selections).map((r) =>
      ({ line: r.start.line, from: r.start.character, to: r.end.character }));
    runs.push({ extension, finder: hiddenRanges(lines, shown) });
  }
  const drawn = lines.slice();
  for (const span of runs[0].finder.slice().reverse()) {
    const text = drawn[span.line];
    drawn[span.line] = text.slice(0, span.from) + text.slice(span.to);
  }
  output[name] = { runs, drawn };
}
console.log(JSON.stringify(output));
"""


@pytest.fixture(scope="module")
def ranges(node) -> dict:
    """The output of the Node module over the stage files of the
    applications, keyed by their paths relative to the repository, and the
    edge lines, keyed `edge lines`."""
    texts = {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
        for path in sorted(APPLICATIONS.glob("*/declaration/stages/*/*.bl"))
    }
    texts["edge lines"] = "\n".join(EDGE_LINES)
    script = NODE_SCRIPT % {"finder": json.dumps(FINDER.as_uri())}
    return node_output(node, script, {"texts": texts, "extension": str(EXTENSION)})


def test_finder_hides_the_extensions_spans(ranges):
    """On every stage file and on the edge lines, with no line in full and
    with lines 2 to 5 in full, the finder's spans equal the extension's."""
    assert len(ranges) > 20 and CONS_PATH in ranges
    for name, found in ranges.items():
        for run in found["runs"]:
            assert run["finder"] == run["extension"], name
    assert sum(len(found["runs"][0]["finder"]) for found in ranges.values()) > 400


def test_cons_drawn_as_names(ranges):
    """`cons.bl` drawn with its spans hidden: a block header reads its name
    alone, an annotation its identity alone, and a line with no group is
    unchanged."""
    drawn = ranges[CONS_PATH]["drawn"]
    assert drawn[12] == "[arvl_to_dcsn] {"
    assert drawn[20] == "[cntn_to_dcsn] {"
    assert drawn[30] == "[policy] {"
    assert drawn[7] == "𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [util]"
    assert drawn[31] == "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [optimality]"
    assert drawn[17] == "    a = m_d - c"


def test_edge_lines_drawn(ranges):
    """The edge lines drawn with their spans hidden, as the extension's rule
    decides each case."""
    drawn = ranges["edge lines"]["drawn"]
    assert drawn == [
        "[g_ad] {",
        "[work] {",
        "x = 𝑢(c) + V[>]   :: [cash_on_hand]",
        "[spaced]",
        "[a] [b] [c]",
        "[id=open, (a : [0, 1) ",
        "[id=bad, a) [id=after]",
        "[id=ν, tail]",
        "[foc_]",
        "# a comment [in_comment]",
        "[idx=not_a_group]",
        "V[>][work]",
        "[label=]",
        "[a] [d]",
        "",
        "[",
    ]
