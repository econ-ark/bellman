"""The compact dossier of a stage, `bellman.dossier.compact_dossier_lines`:
each fact once, no rule line, the numbering kept, the full dossier unchanged
beside it (the brief of 16 October 2026 on token use, item 3.2)."""

from __future__ import annotations

import re
from collections import Counter

import pytest
from conftest import ROOT, STAGE_FILES

from bellman.dossier import (
    RULE_CHARACTERS,
    compact_dossier_lines,
    condition_key,
    condition_rows,
    dossier_lines,
)
from bellman.factory.elaboration import elaborate_text
from bellman.refusals import ConstructionError

# a numbered line: four digits, then two spaces and the text, or nothing
NUMBERED = re.compile(r"^(\d{4})(?:  (.*))?$")


def _bodies(lines):
    """The text of each numbered line, and a check that the numbers run
    from one without a gap."""
    bodies = []
    for number, line in enumerate(lines, 1):
        matched = NUMBERED.match(line)
        assert matched and int(matched.group(1)) == number, line
        bodies.append(matched.group(2) or "")
    return bodies


def _elaborated(path, application_stage):
    try:
        return application_stage(path)
    except ConstructionError:
        return None


@pytest.mark.parametrize("path", STAGE_FILES, ids=lambda path: path.name)
def test_the_compact_dossier_states_each_fact_once_and_no_rule_line(path, application_stage):
    """For each stage file of the applications the elaborator constructs: the
    compact dossier is numbered like the full one and is less than half its
    size; it holds no line drawn with rule characters alone; it holds the
    view, the fields, the definitions, each block's card and the
    obligations, and none of the builders' primitives' cards; every
    condition the full dossier prints is a condition of the compact one, and
    a condition printed under a builders graph is printed under no
    definition; and the stage's name is hidden as in the full dossier."""
    stage = _elaborated(path, application_stage)
    if stage is None:
        pytest.skip(f"{path.name} is refused by the elaborator")
    full = dossier_lines(stage, path)
    compact = compact_dossier_lines(stage, path)
    bodies = _bodies(compact)
    full_bodies = _bodies(full)

    assert len(compact) < len(full)
    assert len("\n".join(compact)) < len("\n".join(full)) / 2
    assert not any(body.strip() and set(body.strip()) <= RULE_CHARACTERS for body in bodies)
    for heading in ("## stage", "## fields", "## definitions", "## obligations"):
        assert heading in bodies
    for direction in ("backward", "forward"):
        assert f"## builders, {direction}" in bodies
        assert f"## initial diagram, {direction}" in bodies
        for name in getattr(stage.initial, direction).list():
            assert bodies.count(f"### the block {name}") == 1
    assert not any(body.startswith("### the primitives of") for body in bodies)
    assert not any(body.startswith("STAGE stage / BACKWARD BUILDER") for body in bodies)

    full_keys = {condition_key(row) for row in condition_rows(full_bodies)}
    compact_keys = {condition_key(row) for row in condition_rows(bodies)}
    assert full_keys <= compact_keys
    definitions = bodies[bodies.index("## definitions") : bodies.index("## builders, backward")]
    builders = bodies[bodies.index("## builders, backward") : bodies.index("## initial diagram, backward")]
    under_definitions = {condition_key(row) for row in condition_rows(definitions)}
    under_builders = Counter(condition_key(row) for row in condition_rows(builders))
    assert not (set(under_builders) & under_definitions)
    assert all(count == 1 for count in under_builders.values())

    hidden = re.compile(rf"(?<![0-9A-Za-z_.]){re.escape(stage.name)}(?=:)")
    assert not any(hidden.search(body) for body in bodies)
    assert bodies[0] == "stage"


def test_the_full_dossier_keeps_its_cards_beside_the_compact_one(application_stage):
    """The full dossier of a stage still prints the definitions table, the
    builders' primitives and the two diagrams' cards, which the compact one
    leaves out, and its rule lines; the two forms hide the same name."""
    path = ROOT / "applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"
    stage = _elaborated(path, application_stage)
    assert stage is not None
    full = _bodies(dossier_lines(stage, path))
    compact = _bodies(compact_dossier_lines(stage, path))

    assert any(body.startswith("### the primitives of") for body in full)
    assert any(body.endswith("/ BACKWARD INITIAL DIAGRAM") for body in full)
    assert not any(body.endswith("/ BACKWARD INITIAL DIAGRAM") for body in compact)
    assert any(body.strip() and set(body.strip()) <= RULE_CHARACTERS for body in full)
    assert "## fields" not in full and "## fields" in compact
    source = [body for body in compact if body.startswith("  cntn_to_dcsn.value")]
    assert source and all("𝑢(c) + β*V[>]" in body for body in source)
    # the name is hidden as an identity prefix in both forms; the whole word
    # is hidden by the Matsya service, which prints the dossier a reader reads
    assert not any("buffer_stock:" in body for body in full + compact)
