"""Supplied continuation data and detached numerical construction."""
from pathlib import Path
import sys

import numpy as np
import pytest

from bellman.stage import elaborate_stage, load_stage
from bellman.stage.grids import check_grid_factor_points

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "code"))
import cons_port_tool as tool


def consumption(methods="methods.bl", lower=0.01):
    folder = APP / "declaration/stages/cons"
    stage = elaborate_stage(load_stage(folder / "cons.bl"))
    stage.methodize(folder / methods)
    stage.calibrate({"ρ": 2.0})
    stage.configure({"n_a": 20, "a_min": 0.0, "a_max": 100.0,
                     "n_m": 20, "m_min": lower, "m_max": 100.0, "n_c": 1001})
    return stage


def continuation():
    x = np.linspace(0.0, 100.0, 200)
    return tool.ValueFn(x, -1 / (1 + x), 1 / (1 + x) ** 2)


def test_stage_operator_checks_all_inputs_and_keeps_detached_data():
    stage, value = consumption(), continuation()
    with pytest.raises(ValueError, match="missing"):
        tool.stage_operator(stage, {})
    operator = tool.stage_operator(stage, {"V[>]": value})
    before = operator(value)
    assert operator.input_conditions
    assert all(condition.status == "required" for condition in operator.input_conditions)
    stage.calibrate({"ρ": 3.0})
    stage.configure({"a_max": 200.0, "m_max": 200.0})
    after = operator(value)
    np.testing.assert_array_equal(after.values, before.values)
    np.testing.assert_array_equal(after.policy["c"], before.policy["c"])


def test_exponential_spacing_has_the_declared_upper_endpoint():
    stage = consumption()
    record = stage.builder.policy.kernels(inputs={"V[>]": continuation()})
    points = tool.cartesian_points(record, "policy")
    assert points[-1] == 100.0
    check_grid_factor_points(record.grid_factors["policy"], points)


def test_corrected_search_matches_an_independent_objective():
    stage = consumption("methods.vfi_reference.bl", 1e-10)
    # Smooth, strictly concave objective: -1/c - 1/(1 + m - c).
    value = continuation()
    record = stage.dcsn.builder.bwd.kernels(inputs={"V[>]": value})
    factor = record.grid_factors["cntn_to_dcsn"]
    for resources in (1e-10, 0.25, 2.0, 10.0):
        candidates = tool.feasible_points(factor, {"m": resources}, inset=1e-6)
        assert np.all((candidates > 0) & (candidates <= resources))
        objective = lambda c: -1 / c - 1 / (1 + resources - c)
        chosen = candidates[np.argmax(objective(candidates))]
        # Independent dense maximization uses 100,001 resource shares. Its
        # consumption error is bounded by one step, including tiny intervals.
        shares = np.linspace(1e-12, 1.0, 100001)
        optimum = resources * shares[np.argmax(objective(resources * shares))]
        analytic = min(resources, (resources + 1) / 2)
        assert abs(optimum - analytic) <= 1e-5 * resources
        gap = objective(analytic) - objective(chosen)
        # Concavity bounds the value loss by the maximum absolute slope on
        # the segment joining the grid choice to the continuous optimum.
        slopes = [abs(1 / c**2 - 1 / (1 + resources - c)**2) for c in (chosen, analytic)]
        bound = max(slopes) * abs(chosen - analytic)
        assert gap >= -1e-14 * abs(objective(analytic))
        assert gap <= bound + 1e-14 * abs(objective(analytic))
    result = tool.stage_operator(stage, {"V[>]": value})(value)
    assert np.all(np.isfinite(result.values))
    assert np.all((result.policy["c"] > 0) & (result.policy["c"] <= result.grid))


def portfolio():
    folder = APP / "declaration/stages/port"
    stage = elaborate_stage(load_stage(folder / "port.bl"))
    stage.methodize(folder / "methods.bl")
    stage.calibrate(APP / "declaration/calibration/portfolio.yml")
    stage.configure({"n_k": 10, "k_min": 1e-10, "k_max": 10.0, "n_ς": 7,
                     "n_Ψ_nodes": 3, "n_θ_nodes": 3, "n_sim": 10, "sim_seed": 0})
    return stage


def test_detached_lognormal_law_keeps_its_calibrated_parameters():
    stage, value = portfolio(), continuation()
    inputs = {"V[>]": value}
    stage.check_inputs(inputs)
    record = stage.dcsn.builder.bwd.kernels(inputs=inputs)
    shocks, means, covariance = tool.lognormal_law(record)
    assert shocks == ("Ψ", "θ")
    before = means.copy(), covariance.copy()
    stage.calibrate({**{name: record.value for name, record in stage.par.items()}, "μ_Ψ": 0.5})
    after = tool.lognormal_law(record)
    np.testing.assert_array_equal(after[1], before[0])
    np.testing.assert_array_equal(after[2], before[1])


def test_ordinary_portfolio_maximum_has_no_finite_floor():
    stage = portfolio()
    value = tool.ValueFn([0.0, 10.0], [-1e20, -1e20], [0.0, 0.0])
    result = tool.stage_operator(stage, {"V[>]": value})(value)
    # A constant continuation has that expectation at every share. Only
    # double-precision accumulation of the quadrature weights can differ.
    np.testing.assert_allclose(result.values, -1e20, rtol=2e-15, atol=0)
    assert np.all(result.values < tool.LOW)


def test_repeated_share_interval_still_checks_each_state():
    stage = portfolio()
    inputs = {"V[>]": continuation()}
    stage.check_inputs(inputs)
    factor = stage.builder.policy.kernels(inputs=inputs).grid_factors["policy"]
    cache = {}
    first = tool.feasible_points(factor, {"k": 1.0}, cache=cache)
    second = tool.feasible_points(factor, {"k": 2.0}, cache=cache)
    assert first is second
    assert len(cache) == 1
    with pytest.raises(ValueError, match="outside"):
        tool.feasible_points(factor, {"k": -1.0}, cache=cache)


@pytest.mark.parametrize("power", [1, 2])
def test_ordinary_portfolio_uses_the_continuation_domain(power):
    stage = portfolio()
    grid = np.linspace(0.0, 100.0, 10001)
    value = tool.ValueFn(grid, grid**power, power * grid**(power - 1))
    inputs = {"V[>]": value}
    stage.check_inputs(inputs)
    record = stage.dcsn.builder.bwd.kernels(inputs=inputs)
    method = tool.method_at(stage, tool.expectation_place(stage))
    counts = {name: int(tool.setting(stage, argument))
              for name, argument in tool.keyword_arguments(method).items()}
    nodes, weights = tool.expectation_rule(record, method.handler, counts)
    shares = np.linspace(0.0, 1.0, 7)
    # Independent law and derivative at capital 10. The continuation grid
    # contains every outcome although the capital grid stops at 10.
    returns = shares[:, None] * nodes["Ψ"] + (1 - shares[:, None]) * float(stage.par["R"].value)
    resources = 10.0 * returns + nodes["θ"]
    direct = value(resources) @ weights
    best = int(np.argmax(direct))
    result = tool.stage_operator(stage, inputs)(value)
    assert shares[best] == 1.0
    assert result.policy["varsigma"][-1] == shares[best]
    np.testing.assert_allclose(result.values[-1], direct[best], rtol=1e-14)
    np.testing.assert_allclose(result.dvalues[-1],
                               np.dot(weights, value.dV(resources[best]) * returns[best]), rtol=1e-14)
