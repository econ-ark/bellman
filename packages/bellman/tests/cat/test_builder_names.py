"""Retired public stage names are absent from queries and reader-facing text."""
from __future__ import annotations

import re

import bellman.period
import bellman.trellis
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


def test_item_6_no_old_form_is_left_in_scope_and_no_old_name_answers(cons):
    """Readers use the current names on pages and on the stage object."""
    found = []
    for relative in IN_FULL:
        for path, name in _files(relative, EXCLUDED):
            data = path.read_bytes()
            if b"\0" not in data:               # a picture or another binary file holds no text
                found.extend(f"{name}:{number}" for number, line in
                             enumerate(data.decode("utf-8", errors="replace").splitlines(), 1)
                             if OLD_FORMS.search(line))
    assert not found, f"{len(found)} lines hold an old form:\n" + "\n".join(found)

    graphs = (cons.builder.bwd, cons.builder.fwd)
    pieces = (cons.builder, *graphs, cons.dcsn.builder.bwd, cons.dcsn.builder.bwd["Pullback"],
              cons.initial, cons.initial.backward, cons.initial.backward["cntn_to_dcsn"], cons.definitions)
    held = [(cons, name) for name in ("builders", "initial_diagrams", "parameters", "denotation", "build")]
    held += [(piece, name) for piece in pieces for name in ("denotation", "draw")]
    held += [(graph, name) for graph in graphs for name in ("arvl", "dcsn", "policy")]
    held += [(bellman.period, name) for name in ("draw_trellis", "draw_period")]
    held += [(bellman.trellis, name) for name in ("draw_trellis", "draw_period")]
    assert [(holder, name) for holder, name in held if hasattr(holder, name)] == []
