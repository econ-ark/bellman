"""Indexed-by-age reference for the eight-age household example."""

import numpy as np


def solve(calibration, assets):
    """Compute by age with matrices on the productivity and asset grid."""
    p = calibration
    j_max = p["J"]
    n_z, n_a = len(p["ζ"]), len(assets)
    size = n_z * n_a
    rho, beta = p["ρ"], p["β"]
    gross_return, tax, inheritance = p["R"], p["τ"], p["I"]
    previous_assets = np.tile(assets, n_z)
    bequest = p["b"] * (previous_assets + p["ξ"]) ** (1 - rho) / (1 - rho)
    marginal_bequest = p["b"] * (previous_assets + p["ξ"]) ** (-rho)
    next_value = np.zeros(size)
    next_marginal = np.zeros(size)
    results = []
    for age in range(j_max - 1, -1, -1):
        # Terminal continuation is zero, and utility increases with consumption.
        terminal_period = age == j_max - 1
        draw = np.kron(p["Π"][age], np.eye(n_a))
        survival = p["ψ"][age]
        c = np.empty(size)
        a = np.empty(size)
        lottery = np.zeros((size, size))
        for z, productivity in enumerate(p["ζ"]):
            indices = slice(z * n_a, (z + 1) * n_a)
            work = p["work"][age]
            income = (work * p["w"] + 1 - work) * p["F"][age] * productivity
            resources = gross_return * (assets + inheritance) + (1 - tax) * income
            if not terminal_period:
                if np.any(next_marginal[indices] <= 0):
                    raise ValueError("The indexed reference needs positive continuation marginal values before the last age.")
                endogenous_c = (beta * next_marginal[indices]) ** (-1 / rho)
                endogenous_m = assets + endogenous_c
            for i, cash in enumerate(resources):
                if terminal_period or cash <= endogenous_m[0]:
                    consumption = cash
                else:
                    lo = np.searchsorted(endogenous_m, cash) - 1
                    lo = min(max(lo, 0), n_a - 2)
                    slope = (endogenous_c[lo + 1] - endogenous_c[lo]) / (
                        endogenous_m[lo + 1] - endogenous_m[lo]
                    )
                    consumption = endogenous_c[lo] + slope * (cash - endogenous_m[lo])
                savings = min(max(cash - consumption, assets[0]), assets[-1])
                row = z * n_a + i
                c[row], a[row] = cash - savings, savings
                lo = np.searchsorted(assets, savings) - 1
                lo = min(max(lo, 0), n_a - 2)
                weight = (assets[lo + 1] - savings) / (assets[lo + 1] - assets[lo])
                lottery[row, z * n_a + lo] = weight
                lottery[row, z * n_a + lo + 1] = 1 - weight
        value4 = c ** (1 - rho) / (1 - rho) + beta * (lottery @ next_value)
        marginal4 = gross_return * c ** (-rho)
        value3, marginal3 = draw @ value4, draw @ marginal4
        value2 = (1 - survival) * bequest + survival * value3
        marginal2 = (1 - survival) * marginal_bequest + survival * marginal3
        results.append({
            "age": age,
            "consumption": c,
            "savings": a,
            "values": (value2, value2, value3, value4),
            "marginals": (marginal2, marginal2, marginal3, marginal4),
            "transition": survival * draw @ lottery,
        })
        next_value, next_marginal = value2, marginal2
    return results


def compare_original(actual, assets, path):
    """Check against the original numerical research script supplied by the reader."""
    from contextlib import redirect_stdout
    from io import StringIO
    import runpy

    with redirect_stdout(StringIO()):
        original = runpy.run_path(str(path))
    np.testing.assert_array_equal(assets, original["A_GRID"])
    for held, expected in zip(actual, reversed(original["SS_A"]), strict=True):
        pairs = (
            (held["consumption"], expected["c"]),
            (held["savings"], expected["a"]),
            (held["transition"], expected["L"]),
            (held["values"], [expected[key] for key in ("v1", "v2", "v3", "v4")]),
            (held["marginals"][0], expected["dv"]),
        )
        for observed, target in pairs:
            np.testing.assert_allclose(observed, target, atol=2e-12, rtol=2e-12)
