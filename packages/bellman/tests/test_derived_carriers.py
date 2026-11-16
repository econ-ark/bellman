"""Carrier sets of shocks, expected values, and policy objectives."""

from pathlib import Path

import pytest

from bellman.stage import elaborate_text
from bellman.syntax import terms as T
from bellman.syntax.source import to_source


APPLICATION = Path(__file__).resolve().parents[3] / "applications/life-cycle/declaration/stages"


def stage_text(name):
    path = APPLICATION / name / f"{name}.bl"
    return path.read_text(encoding="utf-8"), str(path)


@pytest.mark.parametrize(
    ("name", "block", "label", "declared_set"),
    [
        ("draw", "arvl_to_dcsn", "z", T.Named("Z")),
        ("mortality", "dcsn_to_cntn", "s", T.FiniteSet(("survive", "die"))),
    ],
)
def test_initial_shock_has_its_role_and_declared_set(name, block, label, declared_set):
    stage = elaborate_text(*stage_text(name))
    (wire,) = (entry for entry in stage.initial.forward[block].signature().inputs if entry.name == label)
    kind, classification, _, _, result = wire.mathematical_type.sort
    assert kind == "field"
    assert classification[:2] == (None, "shock")
    assert result == declared_set
    assert wire.mathematical_type.carrier == T.FiniteSet((wire.identity,))


def test_expectation_result_types_the_aggregation_argument():
    stage = elaborate_text(*stage_text("draw"))
    (aggregate,) = stage.definitions.denote("draw:G:dcsn_to_arvl").denoted
    assert aggregate.mathematical_type.carrier.domain == T.Product(
        tuple(T.Named(name) for name in ("Ages", "ℝ", "Z", "Xa"))
    )


def test_policy_objective_takes_the_matched_value_fields_result_set():
    text, path = stage_text("consumption")
    text = (
        text.replace("V : ℝ @ !vlu, age :", "B : ℝ @ !vlu, V : (-inf, 0] @ !vlu, age :")
        .replace("    V   = 𝑢(c) + β*V[>]", "    B = c\n    candidate = 𝑢(c) + β*V[>]\n    V   = candidate")
        .replace("(V, age) : !dcsn", "(V, B, age) : !dcsn")
        .replace("V[<] = V ", "V[<] = V + B ")
        .replace("    c = argmax_{", "    continued = β*V[>]\n    c = argmax_{")
        .replace("𝑢(cp) + β*V[>]", "𝑢(cp) + continued")
    )
    stage = elaborate_text(text, path)
    (aggregate,) = stage.definitions.denote("consumption:G:policy").denoted
    assert to_source(aggregate.mathematical_type.carrier.codomain) == "(-inf, 0]"
