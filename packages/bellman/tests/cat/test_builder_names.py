"""The sweep of §3 of the internal developer release 0.01's implementation
plan for every retired form of the way into a stage: the forms lane N of the
release retired, the builders graphs as `stage.builders`, the initial
diagrams as `stage.initial_diagrams`, the parameters as `stage.parameters`,
the verbs `denotation()` and `draw()`, `draw_trellis`, `draw_period` and
`bindings.calibration`; and the forms the plan of 29 September 2026, "The
builders reached by the pair of perches they join", retired, `stage.build` with
its two builders graphs `sol` and `sim`, the table `BUILD_MEMBERS` and the
resolution `builder_named`, where a builder is now read by the pair of perches
it joins, `stage.builder["cntn", "dcsn"]` (`test_builder_pairs.py`).
"""
from __future__ import annotations

import ast
import re

import bellman.period
import bellman.trellis
from bellman.stage import pieces as pieces_module
from conftest import ROOT

# the pattern of every retired form: lane N's (the release plan's §3), then
# the builders graphs under `stage.build` and the two names that resolved them
OLD_FORMS = re.compile(r"\bstage\.(builders|parameters)\b|\.initial_diagrams\b|\.denotation\(|\.draw\("
                       r"|\bdraw_(trellis|period)\b|bindings\.calibration"
                       r"|\bstage\.build\b|\.build\.(sol|sim)\b|\bBUILD_MEMBERS\b|\bbuilder_named\b")


# the places the sweep reads every line of: the pages, the lessons with their
# outputs, the applications and the project memory; the rule files are not
# read (PL13), and the lane's acceptance sweeps them once by hand (BN62)
IN_FULL = ("docs", "tutorials", "applications", "AGENTS.md")
# the places whose Python files it reads the string constants of alone: the
# package, and the kept scripts outside the internal folder (RH8, RH10), in
# scripts/ and tools/ until lane R moves them and in the site's hooks and the
# tests' tools after
STRINGS = ("packages/bellman/bellman", "scripts", "tools", "docs/_hooks",
           "packages/bellman/tests/tools")
# left out: the changelog, a record of what was; the wiki, which lane W
# brought to the new names after every other lane, is read
EXCLUDED = ("docs/changelog.md",)
# the folders no reader opens
SKIPPED = {".git", ".ipynb_checkpoints", "__pycache__", "node_modules", "site", "venv", "legacy"}


def _files(relative, left_out):
    """`(path, name)` of each file at the repository path `relative`, but for
    the paths `left_out` and the folders of `SKIPPED`."""
    path = ROOT / relative
    found = [path] if path.is_file() else sorted(item for item in path.rglob("*") if item.is_file())
    for item in found:
        name = item.relative_to(ROOT).as_posix()
        if SKIPPED.isdisjoint(item.relative_to(ROOT).parts) and not any(
                name == other or name.startswith(other + "/") for other in left_out):
            yield item, name


def _strings(path):
    """`(line, text)` of every string constant of a Python file, its
    docstrings included."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def test_item_6_no_old_form_is_left_in_scope_and_no_old_name_answers(cons):
    """The sweep with the pattern of every retired form finds nothing in the
    pages, the lessons with their outputs, the applications and `AGENTS.md`,
    nor in a string constant of the package or of a kept script; and no old
    name answers at any level: `builders`, `initial_diagrams`, `parameters`,
    `denotation` and `build` of the stage, `denotation` and `draw` of the
    pair mapping, a graph, a builder, a primitive, a block and the
    definitions table, the names `arvl`, `dcsn` and `policy` by which a
    builders graph named its builders, `draw_trellis` and `draw_period` of
    `bellman.period` and `bellman.trellis`, where `diagram_period` and
    `diagram_trellis` stand, and `BUILD_MEMBERS`, `Build`, `BuildersGraph`
    and `builder_named` of the module that defined them."""
    found = []
    for relative in IN_FULL:
        for path, name in _files(relative, EXCLUDED + STRINGS):
            data = path.read_bytes()
            if b"\0" not in data:               # a picture or another binary file holds no text
                found.extend(f"{name}:{number}" for number, line in
                             enumerate(data.decode("utf-8", errors="replace").splitlines(), 1)
                             if OLD_FORMS.search(line))
    for relative in STRINGS:
        for path, name in _files(relative, EXCLUDED):
            if name.endswith(".py"):
                found.extend(f"{name}:{number}" for number, text in _strings(path) if OLD_FORMS.search(text))
    assert not found, f"{len(found)} lines hold an old form:\n" + "\n".join(found)

    graphs = (cons.builder.bwd, cons.builder.fwd)
    pieces = (cons.builder, *graphs, cons.dcsn.builder.bwd, cons.dcsn.builder.bwd["Pullback"],
              cons.initial, cons.initial.backward, cons.initial.backward["cntn_to_dcsn"], cons.definitions)
    held = [(cons, name) for name in ("builders", "initial_diagrams", "parameters", "denotation", "build")]
    held += [(piece, name) for piece in pieces for name in ("denotation", "draw")]
    held += [(graph, name) for graph in graphs for name in ("arvl", "dcsn", "policy")]
    held += [(bellman.period, name) for name in ("draw_trellis", "draw_period")]
    held += [(bellman.trellis, name) for name in ("draw_trellis", "draw_period")]
    held += [(pieces_module, name) for name in ("BUILD_MEMBERS", "Build", "BuildersGraph", "builder_named")]
    assert [(holder, name) for holder, name in held if hasattr(holder, name)] == []
