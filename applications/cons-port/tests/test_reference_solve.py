"""The solve of the two orders of applications/cons-port against its fixed reference.

The folder's stage files, which write the maximization alone, and its block files are bound in the two
reference configurations of the order of the period, `beginning_egm` (the share chosen first) and `end_returns`
(consumption chosen first), on the reference's own settings and handlers (`declaration/trellis.reference-<name>.yml`), and solved by the
application's tool, `applications/cons-port/code/cons_port_tool.py`, with the handler `cons-port:egm` beside the
consumption stage's block and `cons-port:share_search_reference` beside the portfolio stage's (decision SD-28).

The tolerance and the region are those of item 3 of
`applications/cons-port/code/tests/test_cons_port_acceptance.py`, with its reason: every element of every array
the reference stores for the configuration, at every horizon, agrees to 1e-12, relative and absolute, and every
grid is equal; the one exception is the portfolio share, which may lie one step of its grid from the reference's
share at a state where the share objective, evaluated at both shares with the same continuation value, differs by
no more than TIE_TOLERANCE times the larger of its two values in absolute value. The reference was recorded under
Python 3.12, where numpy computes a dot product with OpenBLAS; under Python 3.14 on macOS numpy computes it with
Accelerate, which can round the dot product of the same numbers differently in the last binary digit, and where
the objective is the same at several adjacent shares the search chooses the first share at which it is largest,
so the rounding decides which. No other tolerance is used."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from bellman.period import period_joins
from bellman.trellis import calibrate_trellis, configure_trellis, elaborate_trellis, load_trellis, methodize_trellis

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "applications" / "cons-port" / "reference" / "legacy"
CONFIGURATIONS_FOLDER = ROOT / "applications" / "cons-port" / "declaration"
sys.path.insert(0, str(ROOT / "applications" / "cons-port" / "code"))
import cons_port_tool as tool  # noqa: E402

# each configuration of the reference this test reproduces: its trellis file under declaration/ and the grid
# its terminal value stands on, as applications/cons-port/code/tests/conftest.py names them
CONFIGURATIONS = {"beginning_egm": ("trellis.reference-port-cons.yml", "a"),
                  "end_returns": ("trellis.reference-cons-port.yml", "m")}
# the grids the reference placed its terminal values on, as that conftest writes them: savings
# multi-exponential, resources linear
TERMINAL = {"a": tool.expmult_grid(100.0, 800), "m": np.linspace(0.01, 2000.0, 8000)}
# the tolerance of every array, relative and absolute (item 3 of the application's acceptance)
TOLERANCE = 1e-12
# the relative tolerance within which the share objective must take the same value at two adjacent shares for
# either to be accepted as the choice (the same item, PQ1 of the decisions record of the internal release 0.01)
TIE_TOLERANCE = 1e-14


def specified(file):
    """The specified trellis of a reference trellis file under declaration/: read, elaborated and bound by the three
    verbs, as the application's conftest specifies its own."""
    syntactic = load_trellis(str(CONFIGURATIONS_FOLDER / file))
    return configure_trellis(methodize_trellis(calibrate_trellis(
        elaborate_trellis(syntactic), syntactic), syntactic), syntactic)


def port_continuation(model, solutions, h, terminal):
    """The continuation value the portfolio stage of periods[h] read: the arrival value of the stage its field
    joins, or, where the field leaves the period, the value the inter-period connector names, the terminal value
    at h = 0 (the function of the same name in the application's acceptance)."""
    joined = {join["to"][0] for join in period_joins(model["periods"][h])["joins"] if join["from"][0] == "port"}
    if joined:
        (stage,) = joined
        return solutions[h][stage]
    return tool.continuation_across(model, h, solutions) if h else terminal


def share_ties(port, continuation, computed, reference):
    """The states at which the computed share and the reference's share lie one step of the share grid apart and
    the share objective, evaluated at both shares with the same continuation value, differs by no more than
    TIE_TOLERANCE times the larger of its two values in absolute value (the function of the same name in the
    application's acceptance)."""
    step = 1.0 / (int(port.bindings.settings["n_ς"]) - 1)
    apart = np.flatnonzero(np.isclose(np.abs(computed - reference), step, rtol=0, atol=1e-12))
    if len(apart) == 0:
        return apart
    objective, capital = tool.share_objective(port), tool.evaluation_grid(port)
    tied = []
    for i in apart:
        at_reference, at_computed = objective(continuation, capital[i], np.array([reference[i], computed[i]]))
        if abs(at_reference - at_computed) <= TIE_TOLERANCE * max(abs(at_reference), abs(at_computed)):
            tied.append(i)
    return np.array(tied, dtype=int)


@pytest.fixture(scope="module")
def archive():
    with np.load(REFERENCE / "port_cons_h5.npz", allow_pickle=False) as held:
        return {key: held[key] for key in held.files}


@pytest.mark.parametrize("configuration", sorted(CONFIGURATIONS))
def test_the_demonstration_reproduces_the_reference_to_1e_12(configuration, archive):
    """Both orders of the demonstration, solved on the reference's settings, reproduce every array of the
    reference: each grid equal, each other array to 1e-12, the portfolio share one step from the reference's
    only where the share objective ties to within 1e-14."""
    file, grid = CONFIGURATIONS[configuration]
    model = specified(file)
    cons = model["periods"][0]["stages"]["cons"]
    assert "block cons_egm.bl" in str(cons.methods)
    terminal = tool.terminal_value(cons, TERMINAL[grid])
    solutions = tool.solve_trellis(model, terminal)
    actual = tool.reference_arrays(configuration, solutions)
    expected = {key: value for key, value in archive.items() if key.startswith(configuration + "/")}
    assert sorted(actual) == sorted(expected)
    largest, ties = 0.0, {}
    for key, reference in sorted(expected.items()):
        assert actual[key].shape == reference.shape, key
        if key.endswith("/grid"):
            np.testing.assert_array_equal(actual[key], reference, err_msg=key)
            continue
        compared = np.ones(reference.shape, dtype=bool)
        if key.endswith("/policy/varsigma"):
            h = int(key.split("/")[1][1:])
            tied = share_ties(model["periods"][h]["stages"]["port"], port_continuation(model, solutions, h, terminal),
                              actual[key], reference)
            compared[tied] = False
            if len(tied):
                ties[key] = len(tied)
        np.testing.assert_allclose(actual[key][compared], reference[compared], rtol=TOLERANCE, atol=TOLERANCE,
                                   err_msg=key)
        largest = max(largest, float(np.max(np.abs(actual[key][compared] - reference[compared]), initial=0.0)))
    print(f"{configuration}: {len(expected)} arrays, largest difference {largest:.2e}, "
          f"shares accepted as ties: {ties or 'none'}")
