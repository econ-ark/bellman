"""Verification of the life-cycle application against an indexed-by-age reference."""

import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

from bellman.refusals import ConstructionError
from bellman.trellis import connection_report

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import household
from household import DIRECTORY, build, calibration, compare, savings_grid, solve
from reference import solve as solve_by_age


@pytest.fixture(scope="module")
def configured():
    return build()[-1]


def zero(z, a):
    return 0.0


def test_age_connections(configured):
    report = connection_report(configured)
    assert not report.diagnostics
    assert all(route.status == "certified" for route in report.routes)
    mortality = [route for route in report.routes if route.source[1] == "mortality"]
    assert len(mortality) == 8
    assert {route.branch for route in mortality} == {"survive"}
    assert all(
        component.rule == "equal name"
        for route in mortality for component in route.components
        if component.required.endswith(":age")
    )
    consumption = [route for route in report.routes if route.source[1] == "consumption"]
    assert len(consumption) == 8
    assert {route.destination[1] for route in consumption} == {"entry", "terminal"}
    for route in consumption:
        (pair,) = (c for c in route.components if c.required.endswith(":age_next"))
        assert pair.rule == "explicit connector"
        assert pair.supplied.endswith(":age")
    (initial,) = report.obligations
    assert initial.condition == "initial-law-supported"
    assert tuple(field.field for field in initial.entries) == ("z_0", "a_0")


def test_terminal_inputs_are_checked_before_compiling(configured, monkeypatch):
    consumption = configured["periods"][0]["stages"]["consumption"]

    def unexpected_kernels(*args, **kwargs):
        pytest.fail("A kernel was requested before validating terminal inputs.")

    monkeypatch.setattr(type(consumption.builder.policy), "kernels", unexpected_kernels)
    monkeypatch.setattr(household, "grid_points", unexpected_kernels)
    for inputs, absent_or_invalid in (
        ({"age": 8}, r"V\[>\]"),
        ({"V[>]": zero}, "age"),
        ({"V[>]": 0.0, "age": 8}, r"V\[>\]"),
        ({"V[>]": zero, "age": 9}, "age"),
    ):
        with pytest.raises(ConstructionError, match=absent_or_invalid) as error:
            solve(configured, inputs, terminal_marginal=zero)
        assert error.value.rule == "continuation-input"
    with pytest.raises(TypeError, match="terminal asset derivative"):
        solve(configured, {"V[>]": zero, "age": 8}, terminal_marginal=0.0)
    with pytest.raises(ValueError, match="negative household age"):
        solve(configured, {"V[>]": zero, "age": 7}, terminal_marginal=zero)


def test_supplied_terminal_age_value_and_marginal(configured, monkeypatch):
    short_trellis = {
        **configured,
        "periods": configured["periods"][:2],
        "inter_connectors": configured["inter_connectors"][:1],
    }
    supplied_age = 3
    inputs = {"V[>]": lambda z, a: 4.0 + 2.0*a, "age": supplied_age}
    actual, _, _ = solve(short_trellis, inputs, terminal_marginal=lambda z, a: 2.0)
    baseline, _, _ = solve(
        short_trellis, {"V[>]": zero, "age": supplied_age}, terminal_marginal=zero
    )
    assert [period["ages"] for period in actual] == [(2,) * 4, (1,) * 4]
    assert actual[0]["policy_method"].method.name == "egm"
    assert ("egm-eligibility", "required") in {
        (requirement.condition, requirement.status) for requirement in actual[0]["policy_requirements"]
    }
    assert np.all(actual[0]["values"][3] > baseline[0]["values"][3])
    assert np.any(actual[0]["savings"] > baseline[0]["savings"])

    def sqrt_marginal(z, a):
        return np.inf if a == 0 else 0.5 / np.sqrt(a)

    endpoint_consumption = []
    evaluate = household.evaluate

    def capture_endpoint(record, key, inputs):
        outputs = evaluate(record, key, inputs)
        if key == "inverse_euler:Aggregation" and np.any(np.isposinf(inputs["D_{a_4}(V≻)"])):
            endpoint_consumption.append(outputs["c≻"][:, 0])
        return outputs

    monkeypatch.setattr(household, "evaluate", capture_endpoint)
    with_infinite_bound, _, _ = solve(
        short_trellis, {"V[>]": lambda z, a: np.sqrt(a), "age": 3},
        terminal_marginal=sqrt_marginal,
    )
    (limit,) = endpoint_consumption
    np.testing.assert_array_equal(limit, 0)
    assert with_infinite_bound[0]["policy_method"].method.name == "egm"
    assert np.all(np.isfinite(with_infinite_bound[0]["consumption"]))


def test_consume_all_requires_a_flat_continuation_without_inverse_euler(configured, monkeypatch):
    calls = []
    evaluate = household.evaluate

    def checked_evaluate(record, key, inputs):
        if key in ("consume_all:Aggregation", "inverse_euler:Aggregation"):
            calls.append(key)
        if key == "inverse_euler:Aggregation":
            assert np.all(inputs["D_{a_4}(V≻)"] > 0)
        return evaluate(record, key, inputs)

    monkeypatch.setattr(household, "evaluate", checked_evaluate)
    short_trellis = {
        **configured,
        "periods": configured["periods"][:2],
        "inter_connectors": configured["inter_connectors"][:1],
    }
    actual, _, _ = solve(
        short_trellis, {"V[>]": lambda z, a: z, "age": 3}, terminal_marginal=zero
    )
    flat, positive = actual
    assert calls == ["consume_all:Aggregation", "inverse_euler:Aggregation"]
    assert flat["policy_method"].method.name == "explicit"
    flat_requirements = {requirement.condition for requirement in flat["policy_requirements"]}
    assert "egm-eligibility" not in flat_requirements
    assert "function-argument-domain-inclusion" not in flat_requirements
    np.testing.assert_array_equal(flat["savings"], 0)
    assert positive["policy_method"].method.name == "egm"

    calls.clear()
    for value, marginal in (
        (lambda z, a: a, zero),
        (lambda z, a: a, lambda z, a: 0.0 if a == 0 else 1.0),
        (lambda z, a: -a, lambda z, a: -1.0),
        (lambda z, a: a, lambda z, a: 1.0 if a == 0 else np.inf),
    ):
        with pytest.raises(ValueError, match="constant in assets.*positive discounted marginal"):
            solve(short_trellis, {"V[>]": value, "age": 3}, terminal_marginal=marginal)
    assert calls == []


def test_household_uses_the_terminal_grid_and_matches_indexed_by_age(configured):
    actual, assets, requirements = solve(
        configured, {"V[>]": zero, "age": 8}, terminal_marginal=zero
    )
    (boundary,) = requirements
    assert boundary.condition == "continuation-input"
    assert boundary.status == "required"
    assert [period["age"] for period in actual] == list(range(7, -1, -1))
    expected_grid = savings_grid()
    np.testing.assert_array_equal(assets, expected_grid)
    compare(actual, solve_by_age(calibration(), expected_grid))

    last = configured["periods"][0]
    stages = last["stages"]
    changed_grid = 1.25 * expected_grid
    terminal = stages["terminal"].configure({"settings": {"savings_grid": changed_grid.tolist()}})
    short_trellis = {
        **configured,
        "periods": [{**last, "stages": {**stages, "terminal": terminal}}],
        "inter_connectors": [],
    }
    sampled = []

    def terminal_value(z, a):
        sampled.append((z, a))
        return 0.0

    inputs = {"V[>]": terminal_value, "age": 8}
    record = terminal.builder["dcsn", "arvl"].kernels(inputs=inputs)
    grid = record.grids["dcsn_to_arvl.evaluate[V[<]]"]
    assert sampled == []
    changed, represented_assets, _ = solve(short_trellis, inputs, terminal_marginal=zero)
    np.testing.assert_array_equal(represented_assets, changed_grid)
    np.testing.assert_array_equal(sampled, np.asarray(grid.points, dtype=float))
    assert changed[0]["policy_method"].method.name == "explicit"


def test_income_at_the_previous_age_changes_the_solution(tmp_path):
    directory = tmp_path / "life-cycle"
    shutil.copytree(DIRECTORY, directory, ignore=shutil.ignore_patterns("*.ipynb", "__pycache__"))
    consumption = directory / "stages" / "consumption" / "consumption.bl"
    text = consumption.read_text(encoding="utf-8")
    correct = "𝑦(z_3, age_next - 1)"
    assert text.count(correct) == 1
    wrong = "𝑦(z_3, max((age_next - 2, 0)))"
    consumption.write_text(text.replace(correct, wrong), encoding="utf-8")
    actual, _, _ = solve(
        build(directory)[-1], {"V[>]": zero, "age": 8}, terminal_marginal=zero
    )
    reference = solve_by_age(calibration(), savings_grid())
    difference = max(
        np.max(np.abs(held["consumption"] - expected["consumption"]))
        for held, expected in zip(actual, reference, strict=True)
    )
    assert difference > 1e-3
