"""Detached inputs and point checks for handler-owned grid construction."""

from fractions import Fraction

import pytest
from application_files import ROOT
from stage_texts import GRID_STAGE, GRID_VALUES
from test_modular_fields import EGM, KEPT_BOUND

from bellman.native.records import Refusal
from bellman.stage import elaborate_text
from bellman.stage.grids import check_grid_factor_points, feasible_interval


def test_cons_port_handler_grid_factors_keep_their_authored_data():
    folder = ROOT / "applications/cons-port/declaration/stages/cons"
    stage = elaborate_text((folder / "cons.bl").read_text(), "cons.bl")
    stage.methodize({"text": (folder / "methods.vfi.bl").read_text(), "origin": "methods.vfi.bl"})
    stage.calibrate({"ρ": 2})
    stage.configure({"m_min": 1, "m_max": 3, "n_m": 3, "n_c": 3})
    kernels = stage.builder["cntn", "dcsn"].kernels()

    assert all(isinstance(grid, Refusal) for grid in kernels.grids.values())
    spaced = kernels.grid_factors["cntn_to_dcsn.evaluate"]
    feasible = kernels.grid_factors["cntn_to_dcsn"]
    assert (spaced.coordinate, spaced.lower, spaced.upper, spaced.count) == ("m", 1, 3, 3)
    assert (spaced.spacing, spaced.options) == ("expmult", ())
    assert feasible.coordinate == "c" and feasible.count == 3
    assert feasible.correspondence.field == "Γ"
    assert tuple(name for name, _ in feasible.coordinates) == ("m",)

    assert feasible_interval(feasible, {"m": 2}) == (0, False, 2, True)
    points = check_grid_factor_points(feasible, [Fraction(1, 2), 1, 2], at={"m": 2})
    assert points.points == ((Fraction(1, 2),), (1,), (2,))
    with pytest.raises(ValueError, match="feasible"):
        check_grid_factor_points(feasible, [0, 1, 2], at={"m": 2})


def test_spacing_options_and_requirements_remain_explicit(grid_stage_with_one_addition):
    stage = grid_stage_with_one_addition(
        "cntn_to_dcsn.method : !vfi\n"
        "cntn_to_dcsn.grid : !Cartesian("
        "m=(m_lo, m_hi, n_m, !expmult(nest=n_c, shape=(n_m, !inner(power=n_c)))), "
        "require=!UniformCartesian)\n"
    ).configure({**GRID_VALUES, "n_m": 3})
    kernels = stage.builder["cntn", "dcsn"].kernels()
    factor = kernels.grid_factors["cntn_to_dcsn"]
    assert factor.options == (("nest", 2), ("shape", (3, ("inner", (("power", 2),)))))
    assert factor.requirements == ("UniformCartesian",)

    assert check_grid_factor_points(factor, [1, Fraction(3, 2), 2]).points == (
        (1,),
        (Fraction(3, 2),),
        (2,),
    )
    with pytest.raises(ValueError, match="UniformCartesian"):
        check_grid_factor_points(factor, [1, Fraction(4, 3), 2])
    with pytest.raises(ValueError, match="count"):
        check_grid_factor_points(factor, [1, 2])
    with pytest.raises(ValueError, match="bounds"):
        check_grid_factor_points(factor, [0, 1, 2])


def test_spaced_handler_factor_requires_a_supplied_bound_and_orders_it():
    text = (
        KEPT_BOUND.replace("c : ℝ₊ @ !ctrl", "c : ℝ₊₊ @ !ctrl")
        .replace(
            "Γ_c(x : ℝ) := [0, x]",
            "Γ_c(x : ℝ) := {c : ℝ₊₊ | c < x - L}\n𝑢(c : ℝ₊₊) := -1/c",
        )
        .replace("c + W[>]/2", "𝑢(c) + W[>]/2")
        .replace("cp + W[>]/2", "𝑢(cp) + W[>]/2")
        .replace("[id=policy, (W[>])", "[id=policy, (W[>], L)")
    )
    methods = EGM.replace("a_min : ℝ\n", "").replace(
        "a=(a_min, a_max, n_a)", "a=(L + extra_grid, a_max, n_a, !expmult)"
    )
    stage = elaborate_text(text, "consumption.bl").methodize(
        {"text": methods, "origin": "methods.bl"}
    )
    stage.configure({"extra_grid": 2, "a_max": 1, "n_a": 3})
    policy = stage.dcsn.builder.policy
    absent = policy.kernels()
    assert "policy" not in absent.grid_factors and isinstance(absent.grids["policy"], Refusal)
    assert "requires the continuation field L" in absent.grids["policy"].reason

    supplied = {"W[>]": lambda _a: 0, "L": 0}
    invalid = policy.kernels(inputs=supplied)
    assert "policy" not in invalid.grid_factors and isinstance(invalid.grids["policy"], Refusal)
    assert "not in order" in invalid.grids["policy"].reason

    valid = policy.kernels(inputs={**supplied, "L": -2})
    factor = valid.grid_factors["policy"]
    assert (factor.lower, factor.upper, factor.count) == (0, 1, 3)


def test_feasible_factor_uses_detached_calibration_and_continuation_data():
    text = (
        KEPT_BOUND.replace("@stage: consumption", "@stage: consumption\nR : ℝ₊₊")
        .replace("Γ_c(x : ℝ) := [0, x]", "Γ_c(x : ℝ) := [0, R*x - L]")
        .replace("[id=policy, (W[>])", "[id=policy, (W[>], L)")
    )
    methods = """\
@methods: consumption
n_c : ℕ
cntn_to_dcsn.method : !vfi
cntn_to_dcsn.grid : !Cartesian(c=(Γ_c, n_c))
"""
    stage = elaborate_text(text, "consumption.bl").methodize(
        {"text": methods, "origin": "methods.bl"}
    )
    stage.calibrate({"R": 2}).configure({"n_c": 3})
    builder = stage.builder["cntn", "dcsn"]
    absent = builder.kernels()
    assert "cntn_to_dcsn" not in absent.grid_factors
    assert "needs a numerical value for L" in absent.grids["cntn_to_dcsn"].reason

    supplied = {"W[>]": lambda _a: 0, "L": -1}
    old = builder.kernels(inputs=supplied).grid_factors["cntn_to_dcsn"]
    assert feasible_interval(old, {"m": 2}) == (0, True, 5, True)

    stage.calibrate({"R": 3})
    new = stage.builder["cntn", "dcsn"].kernels(inputs=supplied).grid_factors["cntn_to_dcsn"]
    assert feasible_interval(new, {"m": 2}) == (0, True, 7, True)
    assert feasible_interval(old, {"m": 2}) == (0, True, 5, True)


def test_a_handler_factor_with_no_supported_correspondence_is_refused(
    grid_stage_with_one_addition,
):
    text = GRID_STAGE.replace("Γ_c(m : Xm) := [0, m]", "Γ_c(m : Xm) := {c : ℝ₊ | c ≤ m}")
    stage = grid_stage_with_one_addition(
        "cntn_to_dcsn.method : !vfi\ncntn_to_dcsn.grid : !Cartesian(c=(Γ_c, n_c))\n",
        text=text,
    ).configure(GRID_VALUES)
    kernels = stage.builder["cntn", "dcsn"].kernels()
    assert "cntn_to_dcsn" not in kernels.grid_factors
    assert "not a scalar interval" in kernels.grids["cntn_to_dcsn"].reason
