"""The expansion of the Unicode shortcuts under Node (model interface
specification 0.3, unit T, rule 6).

The editor's function `expandShortcut` in `js/codemirror/src/shortcuts.js`,
which the code editor runs on Tab and the set cells of the classification
table run through the bundle, is run on the table `model.unicode_shortcuts`
reads from the VS Code extension's snippets file, on the text before a
cursor in the cases the rule decides: a prefix that begins a token, a prefix
inside a name, a prefix that begins another prefix, and no prefix. The test
is skipped when `node` is not on the PATH.
"""

from __future__ import annotations

import json
from pathlib import Path

from workbench_support import node_output

from bellman_workbench import model

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "packages/bellman-workbench/js/codemirror/src/shortcuts.js"

# the Node module: reads {cases, shortcuts} on standard input and prints the
# expansion of each case
NODE_SCRIPT = """
import { readFileSync } from "node:fs";
import { expandShortcut } from %(module)s;

const input = JSON.parse(readFileSync(0, "utf8"));
console.log(JSON.stringify(input.cases.map((before) => expandShortcut(before, input.shortcuts))));
"""

# the text before the cursor, and the expansion the rule gives it: the code
# units of the prefix and the text that replaces it, or None
CASES = {
    "Xm := \\StrictlyPositiveReals": {"length": 22, "insert": "ℝ₊₊"},
    "x : \\Reals": {"length": 6, "insert": "ℝ"},
    "\\infty": {"length": 6, "insert": "∞"},
    "a ∈ \\in": {"length": 3, "insert": "∈"},
    "_c": {"length": 2, "insert": "𝑐"},
    "(_h": {"length": 2, "insert": "ℎ"},
    "m_c": None,
    "μ_y": None,
    "x\\in": None,
    "\\Real": None,
    "ℝ₊₊": None,
    "": None,
}


def test_t_item_5_the_rule_of_the_shortcuts_on_the_extensions_table(node):
    """Each case gives the expansion above on the sixty-six snippets of the
    extension (Review Focus 4)."""
    script = NODE_SCRIPT % {"module": json.dumps(MODULE.as_uri())}
    expansions = node_output(
        node, script, {"cases": list(CASES), "shortcuts": model.unicode_shortcuts()}
    )
    assert expansions == list(CASES.values())
