"""Authored partial derivatives are read at the law's image."""

from pathlib import Path

import pytest

from bellman.trellis import assemble_trellis

_RECIPE = Path(__file__).resolve().parents[3] / "applications" / "life-cycle" / "declaration"


def test_derivative_rules_apply_the_partial_at_the_forward_coordinates():
    stages = assemble_trellis(_RECIPE, "spec.yml")["periods"][1]["stages"]
    for version in (stages["consumption"].declared, stages["consumption"].builder):
        arrival = version["dcsn", "arvl"]
        for piece in (arrival, arrival.primitives["Evaluation"]):
            card = str(piece.denote())
            assert "(z_c, m) = 𝑔≺(z_3, a_3, 𝑎𝑔𝑒_next≻())" in card
            assert "D_{a_3}𝑉≺(z_3, a_3) = R · D_{m}𝑉(z_c, m)" in card

    draw = str(stages["draw"].builder["dcsn", "arvl"].denote())
    assert "D_{a_2}𝑉≺(z_2, a_2) = E_{z}[D_{a_d}𝑉(𝑔≺(z_2, a_2, z))]" in draw
    mortality = str(stages["mortality"].builder["cntn", "dcsn"].denote())
    assert "E_{s}[(D_{a_2}𝑉≻(𝑔_survive≻(z_m, a_m)), b · (a_m + ξ)^(−ρ))[s]]" in mortality


def test_arrival_derivative_accepts_the_marginal_value_at_each_law_image():
    stage = assemble_trellis(_RECIPE, "spec.yml")["periods"][1]["stages"]["consumption"]
    pieces = stage.builder["dcsn", "arvl"].kernels().pieces
    law = next(piece for piece in pieces if piece.key == "Pullback")
    marginal = next(piece for piece in pieces if piece.key == "marginal_arrival:Derivative:1")
    (gross_return,) = marginal.parameter_values
    results = []
    for age in (2, 5):
        values = {"z_3": 2, "a_3": 1.5, "age_next": age}
        z_c, m = law.function(*(values[name] for name in law.arguments), *law.parameter_values)
        # The decision value z_c · m² supplies the partial derivative in m.
        values.update({"V": z_c * m**2, "age": age, "D_{m}(V)": 2 * z_c * m})
        result = marginal.function(
            *(values[name] for name in marginal.arguments), *marginal.parameter_values
        )
        assert result == pytest.approx(gross_return * 2 * z_c * m)
        results.append(result)
    assert results[0] != results[1]
