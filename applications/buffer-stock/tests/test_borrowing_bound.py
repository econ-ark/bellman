"""The authored borrowing bound and the endpoint of the endogenous grid."""

from pathlib import Path

import numpy as np
import pytest

from bellman.stage import elaborate_text

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = {
    "R": 1.03,
    "β": 0.96,
    "Γ": 1.03,
    "ρ": 2.0,
    "σ_ψ": 0.1,
    "σ_ξ": 0.1,
    "p_zero": 0.005,
}


def model(*, deviation=0.1, extra_grid=0.001, growth=1.03):
    path = ROOT / "declaration/stages/buffer_stock/buffer_stock.bl"
    stage = elaborate_text(path.read_text(), str(path))
    stage = stage.methodize(path.with_name("methods.bl"))
    stage = stage.calibrate({**CALIBRATION, "σ_ψ": deviation, "Γ": growth})
    stage = stage.configure(ROOT / "declaration/settings/buffer_stock.yml")
    return stage.configure({"extra_grid": extra_grid})


def evaluate(piece, values):
    return piece.function(
        *(values[name] for name in piece.arguments), *piece.parameter_values
    )


def test_default_grid_is_unchanged_at_zero_bound():
    stage = model()
    inputs = {"V[>]": lambda a: -1 / (1 + a), "L": 0.0}
    stage.check_inputs(inputs)
    grid = stage.dcsn.builder.policy.kernels(inputs=inputs).grids["policy"]
    np.testing.assert_allclose(
        np.array(grid.points, dtype=float)[:, 0], np.linspace(0.001, 20, 960)
    )
    assert "a_min" not in stage.settings


@pytest.mark.parametrize(
    "deviation, bound, expected", [(0.1, 0, 0), (0.1, -2, 0), (0, -2, -2 * 1.02 / 1.03)]
)
def test_bound_transition_uses_the_declared_shock_support(deviation, bound, expected):
    stage = model(deviation=deviation, growth=1.02)
    records = stage.builder["dcsn", "arvl"].kernels(
        inputs={"V[>]": lambda a: 0.0, "L": bound}
    )
    piece = next(
        piece
        for identity, piece in records.output_kernels["Aggregation"].items()
        if identity.field == "L"
    )
    assert evaluate(piece, {"L": bound}) == pytest.approx(expected)


def test_zero_offset_computes_the_endpoint_from_infinite_marginal_value():
    stage = model(extra_grid=0)
    records = stage.dcsn.builder.policy.kernels(
        inputs={"V[>]": lambda a: 2 * np.sqrt(np.maximum(a, 0.0)), "L": 0.0}
    )
    assert records.grids["policy"].points[0] == (0,)
    outputs = {
        identity.field: piece
        for pieces in records.output_kernels.values()
        for identity, piece in pieces.items()
    }
    inverse = outputs["c"]
    values = {"D_{a}(V≻)": np.inf}
    consumption = evaluate(inverse, values)
    assert consumption == 0
    assert evaluate(outputs["m"], {"a": 0, **values}) == 0
