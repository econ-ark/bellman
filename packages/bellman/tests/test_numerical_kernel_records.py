"""Numerical records for conditional pieces and grids that read a constant."""

from fractions import Fraction

import numpy as np
import pytest
from test_modular_fields import (
    CONSUMPTION,
    EGM,
    FUNCTION_VALUE,
    KEPT_BOUND,
    SECOND_FIELD,
    kernel_outputs,
)

from bellman.native.identity import Identity
from bellman.refusals import ConstructionError
from bellman.stage import elaborate_text


def test_guard_uses_pre_transition_coordinates_and_evaluates_nested_tests_lazily():
    text = SECOND_FIELD.replace("@stage: consumption", "@stage: consumption\nthreshold : ℝ")
    text = text.replace(
        "W = c + W[>]/2",
        "W = if m > 0 then if 1/m > threshold then W[>] else 0 else 0\n    B = 1/c",
    ).replace("argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "0")
    stage = elaborate_text(text, "consumption.bl").calibrate({"threshold": 0.5})
    kernels = stage.builder["cntn", "dcsn"].kernels()
    (guard,) = kernels.guards["Pullback"]
    assert isinstance(guard.subject, Identity)
    assert guard.subject.field == "W"
    assert guard.arguments == ("m",)
    assert guard.parameters == ("threshold",)
    assert guard.parameter_values == (0.5,)
    with np.errstate(divide="raise", invalid="raise"):
        selected = guard.function(np.array([0.0, 1.0, 2.0, 4.0]), *guard.parameter_values)
    np.testing.assert_array_equal(selected, [False, True, False, False])
    assert selected.dtype == np.bool_

    by_output = kernels.output_kernels["Aggregation"]
    value = next(piece for identity, piece in by_output.items() if identity.field == "W")
    assert value.arguments == ("W≻", "m")
    with np.errstate(divide="raise", invalid="raise"):
        result = value.function(
            np.array([7.0, 8.0]), np.array([0.0, 1.0]), *value.parameter_values
        )
    np.testing.assert_array_equal(result, [0.0, 8.0])
    with pytest.raises(TypeError):
        by_output[guard.subject] = value


@pytest.mark.parametrize("feasibility_reads_bound", [False, True])
@pytest.mark.parametrize("grid_bound", ["L", "L[>]"])
def test_grid_reads_the_supplied_value_and_exposes_only_the_setting(
    feasibility_reads_bound, grid_bound
):
    text = (
        KEPT_BOUND.replace("c : ℝ₊ @ !ctrl", "c : ℝ₊₊ @ !ctrl")
        .replace("Γ_c(x : ℝ) := [0, x]", "Γ_c(x : ℝ) := {c : ℝ₊₊ | c < x - L}\n𝑢(c : ℝ₊₊) := -1/c")
        .replace("c + W[>]/2", "𝑢(c) + W[>]/2")
        .replace("cp + W[>]/2", "𝑢(cp) + W[>]/2")
        .replace("[id=policy, (W[>])", "[id=policy, (W[>], L)")
    )
    if not feasibility_reads_bound:
        text = text.replace("c < x - L", "c < x")
    text = text.replace("[id=policy, (W[>], L)", "[id=policy, (W[>], " + grid_bound + ")")
    methods = EGM.replace("a_min : ℝ\n", "").replace("a=(a_min,", "a=(extra_grid + L,")
    methods = methods.replace("extra_grid + L", "extra_grid + " + grid_bound)
    stage = elaborate_text(text, "consumption.bl").methodize(
        {"text": methods, "origin": "methods.bl"}
    )
    stage.calibrate({}).configure({"extra_grid": 0.125, "a_max": 2, "n_a": 3})
    policy = stage.dcsn.builder.policy
    open_grid = policy.kernels().grids["policy"]
    assert open_grid.diagnostic["rule"] == "grid-requirement"
    assert "L" in open_grid.reason and "policy" in open_grid.reason
    supplied = {"L": np.int64(-2), "W[>]": lambda _a: 0.0}
    grid = policy.kernels(inputs=supplied).grids["policy"]
    assert grid.points == ((Fraction(-15, 8),), (Fraction(1, 16),), (Fraction(2),))
    assert "L" not in stage.settings and "policy" in str(stage.settings["extra_grid"])
    assert any("constant" in line for line in str(stage.fields()).splitlines() if ":L " in line)
    assert policy.kernels().grids["policy"].reason == open_grid.reason
    for invalid in ({"L": -2}, {**supplied, "other": 3}, {**supplied, "L": 2}):
        with pytest.raises(ConstructionError):
            policy.kernels(inputs=invalid)

    for invalid in ("a_max + extra_grid", "W[>] + extra_grid", "L + L"):
        with pytest.raises(ConstructionError) as caught:
            elaborate_text(text, "consumption.bl").methodize(
                {
                    "text": methods.replace("extra_grid + " + grid_bound, invalid),
                    "origin": "methods.bl",
                }
            )
        assert caught.value.rule == "grid-setting-declared"


def test_authored_derivative_guards_its_own_continuation_read():
    text = CONSUMPTION.replace(
        "W = c + W[>]/2",
        "W = c + W[>]/2\n    D_{m}W = if m > 2 then D_{a}W[>] else 0 :: [id=marginal]",
    )
    stage = elaborate_text(text, "consumption.bl")
    kernels = stage.builder["cntn", "dcsn"].kernels()
    (derivative,) = (piece for piece in kernels.pieces if piece.kind == "Derivative")
    (guard,) = kernels.guards[derivative.key]
    assert "Pullback" not in kernels.guards
    assert guard.subject.field in derivative.arguments
    assert guard.arguments == ("m",)
    np.testing.assert_array_equal(guard.function(np.array([2.0, 3.0])), [False, True])


@pytest.mark.parametrize(
    "declared, first, second",
    [
        ("F := {yes, no}", "yes", "no"),
        ("F := {true, false}", True, False),
        ("Age := {old, young}\nF := Age → ℤ", [2**53 + 1, 4], [5, 6]),
    ],
)
def test_conditional_results_preserve_labels_booleans_and_integer_tables(declared, first, second):
    text = (
        FUNCTION_VALUE.replace("F := ℝ → ℝ", declared)
        .replace(
            "f : F @ !vlu @ !cnst, c",
            "f : F @ !vlu @ !cnst, g : F @ !vlu @ !cnst, L : ℝ @ !vlu @ !cnst, c",
        )
        .replace("B : ℝ @ !vlu", "B : F @ !vlu @ !cnst")
        .replace("B[<] : ℝ @ !vlu", "B[<] : F @ !vlu @ !cnst")
        .replace("B = f(c)", "B = if L > 0 then f else g")
    )
    stage = elaborate_text(text, "consumption.bl")
    kernels = stage.builder["cntn", "dcsn"].kernels()
    for bound, expected in ((1, first), (0, second), (-1, second)):
        result = kernel_outputs(
            kernels,
            "Aggregation",
            **{"W≻": 4, "m": 2, "c": 2, "f≻": first, "g≻": second, "L≻": bound},
        )["B"]
        if isinstance(expected, list):
            np.testing.assert_array_equal(result, expected)
            assert result.dtype == np.int64
            assert int(result[0]) == expected[0]
        elif isinstance(expected, bool):
            assert isinstance(result, (bool, np.bool_)) and result == expected
        else:
            assert isinstance(result, str) and result == expected


def test_conditional_derivative_integrates_only_on_its_active_branch():
    text = (
        CONSUMPTION.replace("@stage: consumption", "@stage: consumption\ny : ℝ\ny ~ N(0, 1)")
        .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y)")
        .replace("a = m - c", "a = m - c + y")
        .replace("argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "0")
        .replace(
            "W = c + W[>]/2",
            "W = c + E_{y}(W[>])/2\n"
            "    D_{m}W = if m > 0 then E_{y}(D_{a}W[>]) else 3 :: [id=marginal]",
        )
    )
    stage = elaborate_text(text, "consumption.bl")
    kernels = stage.builder["cntn", "dcsn"].kernels()
    (derivative,) = (piece for piece in kernels.pieces if piece.kind == "Derivative")
    assert derivative.function is not None
    assert derivative.integrated == ()
    expected = "marginal:Expectation:1"
    (integrand,) = (piece for piece in kernels.pieces if piece.key == expected)
    assert integrand.integrated == ("y",)
    assert kernels.laws[expected].integrated == ("y",)
    assert kernels.laws[expected].edge.block == "dcsn_to_cntn"
    (quadrature,) = (
        guard for guard in kernels.guards[expected] if guard.subject.kind == "Expectation"
    )
    assert quadrature.arguments == ("m",)
    np.testing.assert_array_equal(quadrature.function(np.array([0.0, 2.0])), [False, True])
    (sample,) = (
        guard for guard in kernels.guards[expected] if guard.subject.field in integrand.arguments
    )
    np.testing.assert_array_equal(sample.function(np.array([0.0, 2.0])), [False, True])
    assert derivative.fallback.arguments == ()
    assert derivative.fallback.function() == 3
    assert derivative.arguments == ("m", *integrand.writes)

    # The symmetric Gaussian quadrature integrates this affine derivative
    # exactly, so the active result is its value at the mean.
    active = integrand.function(np.array([-1.0, 1.0]), np.array([2.0, 4.0]))
    np.testing.assert_array_equal(active, [2.0, 4.0])
    assert derivative.function(2.0, np.dot(active, [0.5, 0.5])) == 3


@pytest.mark.parametrize(
    "formula, relation",
    [
        ("if m > 0 then E_{y}(y + 1) else E_{z}(z + 2)", "siblings"),
        ("E_{y}(E_{z}(y + z))", "nested"),
        ("if E_{y}(y + 1) > 0 then E_{z}(z + 2) else 3", "test"),
    ],
)
def test_derivative_preserves_distinct_expectation_scopes(formula, relation):
    text = (
        CONSUMPTION.replace(
            "@stage: consumption",
            "@stage: consumption\ny : ℝ\nz : ℝ\ny ~ N(0, 1)\nz ~ N(0, 1)",
        )
        .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y, z)")
        .replace("a = m - c", "a = m - c + y + z")
        .replace("argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "0")
        .replace(
            "W = c + W[>]/2",
            f"W = c + E_{{y,z}}(W[>])/2\n    D_{{m}}W = {formula} :: [id=marginal]",
        )
    )
    stage = elaborate_text(text, "consumption.bl")
    kernels = stage.builder["cntn", "dcsn"].kernels()
    parts = [piece for piece in kernels.pieces if piece.key.startswith("marginal:Expectation:")]
    assert len(parts) == 2
    by_shock = {piece.integrated[0]: piece for piece in parts}
    y, z = by_shock["y"], by_shock["z"]
    assert y.writes != z.writes
    for piece in parts:
        assert piece.function is not None
        assert kernels.laws[piece.key].integrated == piece.integrated
    (derivative,) = (piece for piece in kernels.pieces if piece.kind == "Derivative")
    assert derivative.fallback is None
    if relation == "nested":
        assert parts == [z, y]
        assert kernels.laws[y.key].given == ()
        assert kernels.laws[z.key].given == ("y",)
        assert set(z.writes) <= set(y.reads)
        assert derivative.reads == y.writes
    else:
        assert parts == [y, z]
        assert set(y.writes + z.writes) <= set(derivative.reads)
        assert kernels.laws[y.key].given == ()
        assert kernels.laws[z.key].given == ()
        if relation == "test":
            (guard,) = kernels.guards[z.key]
            assert guard.arguments == y.writes
            assert bool(guard.function(-1.0)) is False
            assert bool(guard.function(1.0)) is True
        else:
            selected = (bool(kernels.guards[piece.key][0].function(1.0)) for piece in (y, z))
            assert tuple(selected) == (True, False)


def test_nested_derivative_fallback_is_local_to_the_integrand():
    text = (
        CONSUMPTION.replace(
            "@stage: consumption", "@stage: consumption\ny : ℝ\nz : ℝ\ny ~ N(0, 1)\nz ~ N(0, 1)"
        )
        .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y, z)")
        .replace("(W[>] : ℝ @ !vlu, c)", "(W[>] : ℝ @ !vlu, c, y)")
        .replace("a = m - c", "a = m - c + y + z")
        .replace("argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "0")
        .replace(
            "W = c + W[>]/2",
            "W = c + E_{y,z}(W[>])/2\n"
            "    local = if y > 0 then E_{z}(z + 1) else 2 :: [id=selected]\n"
            "    D_{m}W = E_{y}(local) :: [id=marginal]",
        )
    )
    stage = elaborate_text(text, "consumption.bl")
    kernels = stage.builder["cntn", "dcsn"].kernels()
    by_key = {piece.key: piece for piece in kernels.pieces}
    inner = by_key["marginal:Derivative:1", "selected:Expectation:1"]
    outer = by_key["marginal:Expectation:1"]
    derivative = by_key["marginal:Derivative:1"]
    assert inner.integrated == ("z",) and outer.integrated == ("y",)
    assert kernels.laws[inner.key].given == ("y",)
    assert kernels.laws[outer.key].given == ()
    assert outer.key not in kernels.guards
    (inner_guard,) = kernels.guards[inner.key]
    assert inner_guard.arguments == ("y",)
    np.testing.assert_array_equal(inner_guard.function(np.array([-1.0, 1.0])), [False, True])
    assert outer.fallback.arguments == ()
    assert outer.fallback.function() == 2
    assert derivative.fallback is None
    assert set(inner.writes) <= set(outer.reads)
    assert derivative.reads == outer.writes


def test_derivatives_keep_separate_guards_when_they_share_an_alias():
    text = (
        SECOND_FIELD.replace("@stage: consumption", "@stage: consumption\ny : ℝ\ny ~ N(0, 1)")
        .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y)")
        .replace("a = m - c", "a = m - c + y")
        .replace("argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "0")
        .replace(
            "W = c + W[>]/2",
            "W = c + E_{y}(W[>])/2\n"
            "    B = c\n"
            "    local = E_{y}(y + 1) :: [id=shared]\n"
            "    D_{m}W = if m > 0 then local else 3 :: [id=marginal_w]\n"
            "    D_{m}B = if m < 0 then local else 4 :: [id=marginal_b]",
        )
    )
    stage = elaborate_text(text, "consumption.bl")
    kernels = stage.builder["cntn", "dcsn"].kernels()
    first = ("marginal_w:Derivative:1", "shared:Expectation:1")
    second = ("marginal_b:Derivative:1", "shared:Expectation:1")
    first_guard, second_guard = kernels.guards[first][0], kernels.guards[second][0]
    assert first_guard.subject == second_guard.subject
    assert first_guard.function(1.0) and not second_guard.function(1.0)
    assert not first_guard.function(-1.0) and second_guard.function(-1.0)
    assert kernels.laws[first].integrated == kernels.laws[second].integrated == ("y",)
