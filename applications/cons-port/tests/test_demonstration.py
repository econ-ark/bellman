"""The cons-port folder: its stage files elaborate with
the package as it stands, and its two recipes, consumption first and portfolio
first, load with the package's recipe reader and name the folder's own stage,
calibration, settings and methods files, the methods file of a stage the
addition beside its stage file. What the additions bind is tested in code/tests/."""

from pathlib import Path

import pytest

from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import load_recipe

DECLARATION = Path(__file__).resolve().parents[1] / "declaration"

# the stage keys of the folder, each the name of its folder under stages/
STAGES = ("cons", "disc", "port")

# the policy builder's card of the consumption stage with nothing bound, the
# argmax-only card of specification 0.6 §8, recorded from the printed card on
# 28 October 2026 (its states m and a, unindexed by perch since AMD-MB-001)
POLICY_CARD = """\
STAGE cons / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → ℝ
       ──────────────────────────────────────────────────────────────────
  out  𝑐   : Xm → ℝ₊₊,  𝑐(m) ∈ Γ(m)

Operations
  1  Pullback
     in: 𝑉≻                             out: 𝑉≻ ∘ 𝑔≻
     ────────────────────────────────────────────────────────────────────
     rule: (𝑉≻ ∘ 𝑔≻)(m, c) = 𝑉≻(𝑔≻(m, c))

  2  optimality:Aggregation
     in: (1)                            out: (m, c) ↦ 𝑢(c) + 𝑉≻(𝑔≻(m, c))
     ────────────────────────────────────────────────────────────────────
     rule: (m, c) ↦ 𝑢(c) + 𝑉≻(𝑔≻(m, c))

  3  optimality:Argmax
     in: (2)                            out: 𝑐
     ────────────────────────────────────────────────────────────────────
     rule: 𝑐(m) ∈ argmax_{cp ∈ Γ(m)} [𝑢(cp) + 𝑉≻(𝑔≻(m, cp))]

  4  Evaluation
     in: 𝑐                              out: 𝑐
     ────────────────────────────────────────────────────────────────────
     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m) ∈ Γ(m)
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  17  c = argmax_{cp : Γ(m)}(𝑢(cp) + V[>])  :: [id=optimality]

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  𝑢     cons:function:𝑢
  Γ     cons:correspondence:Γ
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# for each stage key, the sources its recipe entry lists by kind, each by its
# path from the folder declaration/
SOURCES = {
    "cons": {"calibration": ["calibration/portfolio.yml"], "settings": ["settings/cons_wide.yml"],
             "methods": ["stages/cons/methods.bl"]},
    "disc": {"calibration": ["calibration/portfolio.yml"], "settings": [],
             "methods": ["stages/disc/methods.bl"]},
    "port": {"calibration": ["calibration/portfolio.yml"], "settings": ["settings/port_wide.yml"],
             "methods": ["stages/port/methods.bl"]},
}

# the two recipes, each with the connectors its period writes and the
# inter-period connector of every adjacent pair
# each recipe's connectors within a period, its connectors between periods,
# and the number of periods its trellis file writes: the cons-port order
# repeats its period three times since AAS's edit of 29 October 2026, the
# port-cons order six times
RECIPES = {
    "spec.cons-port.yml": ([{"disc.a": "k"}], [{"w": "m"}], 3),
    "spec.port-cons.yml": ([{"w": "m"}], [{"disc.a": "k"}], 6),
}


def stage_file(key):
    """The path of the stage file of the stage key `key`."""
    return DECLARATION / "stages" / key / f"{key}.bl"


def test_item_1_the_three_stage_files_elaborate_and_cons_prints_the_argmax_policy_card():
    elaborated = {key: elaborate_stage(load_stage(str(stage_file(key)))) for key in STAGES}
    assert {key: stage.name for key, stage in elaborated.items()} == {key: key for key in STAGES}
    assert str(elaborated["cons"].dcsn.builder.policy.denote()) + "\n" == POLICY_CARD


@pytest.mark.parametrize("recipe", sorted(RECIPES))
def test_item_3_each_recipe_loads_and_names_the_folders_own_files(recipe):
    syntactic = load_recipe(DECLARATION, recipe)
    connectors, inter_connectors, periods = RECIPES[recipe]
    assert len(syntactic["periods"]) == periods
    assert syntactic["inter_connectors"] == inter_connectors * (periods - 1)
    for period in syntactic["periods"]:
        assert period["connectors"] == connectors
        assert sorted(period["stages"]) == list(STAGES)
        for key, record in period["stages"].items():
            assert Path(record["stage"]["origin"]) == stage_file(key)
            named = {kind: [Path(source["path"]).relative_to(DECLARATION).as_posix()
                            for source in record["provenance"]["source_lists"][kind]]
                     for kind in ("calibration", "settings", "methods")}
            assert named == SOURCES[key]
