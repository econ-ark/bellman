"""The behaviour file of asva (the lean implementation rule, layer 3): one test
for each module of the package, named `test_<module>_...` with the runner's
modules as `test_run_<module>_...`, so that the acceptance file can find each
module's test by name.

The factories are run on arrays against values computed by hand; the runner's
moments and sweep on a small panel whose moments are written out below. No
test reads a stage: asva imports nothing of `bellman`.
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from numba import njit

# the records of a run are read through their module, so that pytest does not
# take the class TestSpec for a class of tests
import asva.run.types as run_types
from asva.compose_interp import make_compose_interp
from asva.egm_1d import make_egm, make_egm_1d
from asva.numerics import clamp_policy, clamp_scalar, clamp_value
from asva.run.estimate import diagnostics, estimate, load_estimation_spec, make_criterion
from asva.run.io import load_solution, save_solution
from asva.run.make_test import make_test
from asva.run.metrics import format_table, write_results_table
from asva.run.moments import (compute_moments_from_dataframe, compute_moments_from_panels, load_data_moments,
                              make_moment_fn, moment_names)
from asva.run.mpi import bcast_item, gather_results, is_root, mpi_map, rank_size, scatter_items
from asva.run.sweep import SweepResult, param_grid, sweep
from asva.simulate import StageForward, apply_rename, draw_shocks, forward_stage, simulate, simulate_period

ASVA = Path(__file__).resolve().parents[1]

# The small panel: ten agents over two dates. Assets are 0, ..., 9 at the first
# date and 2a + 1 at the second; consumption is assets plus one.
ASSETS = np.array([np.arange(10.0), 2.0 * np.arange(10.0) + 1.0])
PANEL = {"a": ASSETS, "c": ASSETS + 1.0}
SPEC = {"identification": {"mean": ["c"], "sd": ["c"], "corrs": [["c", "a"]], "autocorrs": ["a"]}}
# pooled over both dates: the twenty assets have mean (45 + 100) / 20 = 7.25
MEAN_C = 8.25
SD_C = math.sqrt(float(np.mean((ASSETS.ravel() - 7.25) ** 2)))


# ── the modules of asva ─────────────────────────────────────

RHO = 2.0


@njit
def _inverse_euler(dv, fixed_state):
    return dv ** (-1.0 / RHO)


@njit
def _value(c, v_cntn, fixed_state):
    return c ** (1.0 - RHO) / (1.0 - RHO) + v_cntn


@njit
def _grid(c, a, fixed_state):
    return a + c


@njit
def _concavity(c, ddv, fixed_state):
    return ddv * c


@njit
def _inverse_euler_k(dv, x, fixed_state, params):
    return np.array([dv[0] ** (-1.0 / params[0])])


@njit
def _value_k(c, v_cntn, x, fixed_state, params):
    return c[0] ** (1.0 - params[0]) / (1.0 - params[0]) + v_cntn


@njit
def _grid_k(c, x, fixed_state, params):
    return np.array([x[0] + c[0]])


@njit
def _concavity_k(c, ddv, x, fixed_state, params):
    return np.array([ddv[0] * c[0]])


def test_egm_1d_the_one_dimensional_step_and_the_k_dimensional_step_at_k_equal_one_give_the_values_computed_by_hand():
    """With u(c) = c^(1-ρ)/(1-ρ) at ρ = 2, the marginal values 4, 1 and 1/4 give
    the consumptions 1/2, 1 and 2; the savings 0, 1, 2 give the cash on hand
    1/2, 2 and 4; the values are -1/c plus the continuation value."""
    dv = np.array([4.0, 1.0, 0.25])
    ddv = np.array([1.0, 2.0, 3.0])
    v = np.array([-1.0, -0.5, -0.25])
    a = np.array([0.0, 1.0, 2.0])
    step = make_egm_1d(_inverse_euler, _value, _grid, _concavity)
    c, value, cash, del_a = step(dv, ddv, v, a, 0.0)
    assert np.allclose(c, [0.5, 1.0, 2.0])
    assert np.allclose(cash, [0.5, 2.0, 4.0])
    assert np.allclose(value, [-3.0, -1.5, -0.75])
    assert np.allclose(del_a, [0.5, 2.0, 6.0])

    step_k = make_egm(_inverse_euler_k, _value_k, _grid_k, _concavity_k, np.array([RHO]), 1, 1)
    c_k, value_k, cash_k, del_a_k = step_k(dv.reshape(-1, 1), ddv.reshape(-1, 1), v, a.reshape(-1, 1), 0.0)
    assert c_k.shape == (3, 1) and cash_k.shape == (3, 1) and del_a_k.shape == (3, 1)
    assert np.allclose(c_k[:, 0], c) and np.allclose(value_k, value)
    assert np.allclose(cash_k[:, 0], cash) and np.allclose(del_a_k[:, 0], del_a)


def test_compose_interp_interpolates_the_arrays_at_the_transition_of_the_arrival_points():
    """The transition doubles the arrival points 0.5 and 1, so the arrays are read
    at 1 and 2 of the source grid 0, 1, 2."""

    def double(x, params):
        return x * params[0]

    def interp_two(xp, y1, y2, x):
        return np.interp(x, xp, y1), np.interp(x, xp, y2)

    compose = make_compose_interp(double, interp_two)
    first, second = compose(np.array([0.0, 1.0, 2.0]), np.array([0.0, 10.0, 20.0]), np.array([5.0, 6.0, 7.0]),
                            np.array([0.5, 1.0]), np.array([2.0]))
    assert np.allclose(first, [10.0, 20.0]) and np.allclose(second, [6.0, 7.0])


def test_numerics_clamps_values_policies_and_scalars():
    assert np.array_equal(clamp_value(np.array([np.nan, np.inf, -np.inf, 1.5])), [-1e10, -1e10, -1e10, 1.5])
    assert np.array_equal(clamp_value(np.array([np.nan, 2.0]), -7.0), [-7.0, 2.0])
    assert np.array_equal(clamp_policy(np.array([np.nan, -1.0, 0.5, 2.0, np.inf]), 0.0, 1.0),
                          [0.0, 0.0, 0.5, 1.0, 1.0])
    assert [clamp_scalar(x, 0.0, 1.0, 0.3) for x in (np.nan, -np.inf, np.inf, -2.0, 2.0, 0.5)] == \
        [0.3, 0.0, 1.0, 0.0, 1.0, 0.5]


def test_simulate_takes_one_stage_step_renames_and_draws_by_hand_and_the_walk_over_periods_raises():
    """A stage with cash m = R a + y, consumption c = m / 2 and savings m - c, for
    two agents with assets 1 and 3, R = 2 and income 1: m = 3 and 7, c = 1.5 and
    3.5, savings 1.5 and 3.5. The walk over the periods of a trellis raises at
    the call, with the message that it waits for the trellis's forward record."""
    stage = StageForward(
        arvl_to_dcsn=lambda p, s: {"m": 2.0 * p["a"] + s["y"]},
        policy=lambda p: {"c": 0.5 * p["m"]},
        dcsn_to_cntn=lambda p, controls, s: {"b": p["m"] - controls["c"]},
        shock_draw_arvl="income", shock_draw_cntn=None)
    poststates, records = forward_stage(stage, {"a": np.array([1.0, 3.0])}, {"income": {"y": np.array([1.0, 1.0])}})
    assert np.allclose(records["states"]["m"], [3.0, 7.0])
    assert np.allclose(records["controls"]["c"], [1.5, 3.5])
    assert np.allclose(poststates["b"], [1.5, 3.5])

    renamed = apply_rename({"b": "a"}, poststates)
    assert list(renamed) == ["a"] and renamed["a"] is poststates["b"]
    assert apply_rename({}, poststates) is poststates

    spec = {"income": lambda n, rng: rng.standard_normal(n)}
    draws = draw_shocks(4, 0, 2, spec, rng_seed=7)
    again = draw_shocks(4, 0, 2, spec, rng_seed=7)
    assert sorted(draws) == [0, 1, 2] and all(draws[t]["income"].shape == (4,) for t in draws)
    assert all(np.array_equal(draws[t]["income"], again[t]["income"]) for t in draws)
    assert not np.array_equal(draws[0]["income"], draws[1]["income"])

    for walk in (simulate, simulate_period):
        with pytest.raises(NotImplementedError, match="forward record of a trellis"):
            walk()


# ── the modules of asva.run ─────────────────────────────────

def test_run_types_holds_frozen_records_with_no_deprecated_attribute():
    """The records are frozen, and the two deprecated names of `base_spec`,
    `model_dir` and `syntax_dir`, are deleted."""
    test = run_types.TestSpec(slots={"beta": 0.96}, label="patient")
    assert run_types.TestSpec().slots == {} and run_types.TestSpec().label == ""
    simulation = run_types.SimSpec(n_sim=100, seed=1, plots=False)
    spec = run_types.RunSpec(
        name="cons", base_spec=Path("applications/cons-port"), output_dir=Path("out"), run_tag=None,
        test_set=(test,), sweep_runs=1, warmup=False, sim=simulation, mode="solve", extra_args={},
        verbose=False, trace=False, mpi=False, gpu=False, skip_egm_plots=True, csv_export=False)
    assert spec.test_set == (test,) and spec.sim.n_sim == 100
    with pytest.raises(AttributeError):
        spec.name = "other"
    for retired in ("model_dir", "syntax_dir"):
        with pytest.raises(AttributeError):
            getattr(spec, retired)


def test_run_make_test_wraps_each_slot_bundle_and_an_empty_list_in_one_test():
    assert make_test([]) == (run_types.TestSpec(),)
    tests = make_test([{"beta": 0.9}, {"beta": 0.95}])
    assert tests == (run_types.TestSpec(slots={"beta": 0.9}), run_types.TestSpec(slots={"beta": 0.95}))


def test_run_moments_computes_the_moments_of_a_small_panel_and_loads_pandas_only_where_a_data_file_is_read(tmp_path):
    moments = compute_moments_from_panels(PANEL, SPEC)
    assert moments["mean_c__ageall"] == pytest.approx(MEAN_C)
    assert moments["sd_c__ageall"] == pytest.approx(SD_C)
    # consumption is assets plus one, and the second date's assets are affine in the first's
    assert moments["corr_c_a__ageall"] == pytest.approx(1.0)
    assert moments["autocorr_a__ageall"] == pytest.approx(1.0)
    assert make_moment_fn(SPEC)(PANEL) == moments
    assert moment_names(SPEC) == list(moments)

    frame = pd.DataFrame(
        [{"t": t, "_idx": n, "a": ASSETS[t, n], "c": ASSETS[t, n] + 1.0} for t in range(2) for n in range(10)])
    assert compute_moments_from_dataframe(frame, SPEC) == pytest.approx(moments)
    data = tmp_path / "moments.csv"
    data.write_text("age,mean_c\n1,2.5\n")
    assert load_data_moments(data, {}) == {"mean_c__age1": 2.5}

    path = os.pathsep.join(p for p in (str(ASVA), os.environ.get("PYTHONPATH", "")) if p)
    loaded = subprocess.run([sys.executable, "-c", "import sys, asva, asva.run; print('pandas' in sys.modules)"],
                            env={**os.environ, "PYTHONPATH": path}, capture_output=True, text=True, check=True)
    assert loaded.stdout.strip() == "False"


def test_run_sweep_maps_a_solve_function_over_the_tests_and_keeps_the_best_of_its_repetitions():
    """The solve function shifts the small panel's consumption by the test's
    slot `shift`; the metric is the mean consumption, 8.25 plus the shift."""
    moment_fn = make_moment_fn(SPEC)
    calls = []

    def solve(test):
        calls.append(test.slots["shift"])
        return {"a": PANEL["a"], "c": PANEL["c"] + test.slots["shift"]}

    tests = make_test(param_grid(shift=[0.0, 1.0]))
    results = sweep(solve, tests, {"mean_c": lambda panel: moment_fn(panel)["mean_c__ageall"]},
                    n_reps=2, warmup=True, verbose=False)
    assert [r.point for r in results] == list(tests)
    assert [r.metrics["mean_c"] for r in results] == pytest.approx([MEAN_C, MEAN_C + 1.0])
    assert all(isinstance(r, SweepResult) and np.allclose(r.result["c"], PANEL["c"] + r.point.slots["shift"])
               for r in results)
    assert calls == [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]  # the warm-up call and two repetitions of each test


def test_run_io_saves_and_loads_a_nested_solution_with_its_metadata(tmp_path):
    solution = {"periods": [{"c": np.array([1.0, 2.0]), "stage": "worker"}, {"c": np.array([[3.0]])}],
                "beta": 0.96}
    saved = save_solution(tmp_path / "solution", solution, metadata={"method": "egm", "n_a": 2})
    assert sorted(p.name for p in saved.iterdir()) == ["metadata.json", "solutions.npz"]
    loaded, metadata = load_solution(saved)
    assert metadata == {"method": "egm", "n_a": 2}
    assert loaded["beta"] == 0.96 and loaded["periods"][0]["stage"] == "worker"
    assert np.array_equal(loaded["periods"][0]["c"], [1.0, 2.0])
    assert np.array_equal(loaded["periods"][1]["c"], [[3.0]])
    assert json.loads((saved / "metadata.json").read_text())["array_keys"] == ["periods.0.c", "periods.1.c"]


def test_run_metrics_formats_markdown_and_latex_tables_and_writes_the_results_of_a_sweep(tmp_path):
    rows = [{"label": "shift=0.0", "mean_c": 8.25}]
    assert format_table(rows, ["label", "mean_c"]) == (
        "| label     | mean_c |\n"
        "|-----------|--------|\n"
        "| shift=0.0 | 8.2500 |")
    latex = format_table(rows, ["label", "mean_c"], fmt="latex", caption="Mean c")
    assert r"\begin{tabular}{ll}" in latex and r"label & mean\_c \\" in latex and r"\caption{Mean c}" in latex

    results = [SweepResult(point=run_types.TestSpec(slots={"shift": 0.0}), metrics={"mean_c": 8.25})]
    table = tmp_path / "tables" / "results.md"
    write_results_table(results, str(table))
    assert table.read_text() == format_table(rows, ["label", "mean_c"])


class _TwoRanks:
    """A communicator of two ranks, enough for the split of the items."""

    def __init__(self, rank):
        self.rank = rank

    def Get_rank(self):
        return self.rank

    def Get_size(self):
        return 2


def test_run_mpi_runs_on_one_process_without_a_communicator_and_splits_items_across_ranks():
    assert rank_size() == (0, 1) and is_root()
    assert scatter_items([1, 2, 3]) == [1, 2, 3] and gather_results([4, 5]) == [4, 5]
    assert bcast_item("x") == "x" and mpi_map(lambda x: x * x, [1, 2, 3]) == [1, 4, 9]
    # five items on two ranks: the first rank takes the one left over
    assert scatter_items([1, 2, 3, 4, 5], _TwoRanks(0)) == [1, 2, 3]
    assert scatter_items([1, 2, 3, 4, 5], _TwoRanks(1)) == [4, 5]


def test_run_estimate_recovers_the_scale_of_a_small_panel_from_its_moments(tmp_path):
    """The trial function scales the small panel's consumption by θ; the data
    moments are those at θ = 2, where the criterion is zero."""
    moment_fn = make_moment_fn(SPEC)
    data = {k: v for k, v in moment_fn({"a": PANEL["a"], "c": 2.0 * PANEL["c"]}).items() if k.startswith(("mean", "sd"))}

    def trial(theta):
        return {"a": PANEL["a"], "c": theta["scale"] * PANEL["c"]}

    criterion = make_criterion(trial, moment_fn, data)
    assert criterion({"scale": 2.0}) == pytest.approx(0.0)
    assert criterion({"scale": 1.5}) > criterion({"scale": 1.9}) > 0.0
    result = estimate(criterion, {"scale": {"bounds": [1.0, 3.0]}},
                      method_options={"n_samples": 40, "n_elite": 8, "max_iter": 20, "tol": 1e-10,
                                      "sampling_seed": 3}, verbose=False)
    assert result.theta["scale"] == pytest.approx(2.0, abs=0.02)
    report = diagnostics(result, data)
    assert [row["moment"] for row in report["fit_table"]] == sorted(data)

    (tmp_path / "moments.csv").write_text("age,mean_c\n1,16.5\n")
    (tmp_path / "estimation.yml").write_text(
        "estimation:\n  free:\n    scale: {bounds: [1.0, 3.0]}\n  method: cross-entropy\n"
        "moments:\n  data_file: moments.csv\n")
    loaded = load_estimation_spec(str(tmp_path / "estimation.yml"))
    assert loaded["free"] == {"scale": {"bounds": [1.0, 3.0]}} and loaded["method"] == "cross-entropy"
    assert loaded["data_moments"] == {"mean_c__age1": 16.5}
