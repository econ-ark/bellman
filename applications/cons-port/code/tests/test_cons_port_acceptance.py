"""The acceptance of step D of the spec 0.3 order of work: the portfolio-consumption application on the .bl
stages (task file 50, A09 and A10). One test per item, then the tests of the review focus. The fixed reference is
read, never regenerated.
Item 6 is retired: the model's lessons are in tutorials/models/cons-port/, checked by tutorials/tests/test_lessons.py."""
from __future__ import annotations

import hashlib
import json
import os
import warnings
from operator import attrgetter

import cloudpickle
import numpy as np
import pytest
import yaml

from bellman.period import backward_order, forward_order, period_joins
from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import (
    accrete,
    changed_positions,
    configure_trellis,
    inter_period_joins,
    load_trellis,
    methodize_trellis,
)
from .conftest import (ARCHIVE_SHA256, BACKWARD, CONFIGURATIONS, DECLARATION, EVIDENCE, LEGACY_SOURCES, REFERENCE, STAGES,
                       CONSUMPTION, consumption_stage, stage_file,
                       TERMINAL, specified, tool)


def test_item_1_port_continues_to_w_and_each_period_is_ordered_by_its_fields():
    stage = {name: elaborate_stage(load_stage(str(stage_file(name))))
             for name in ("cons", "port", "noport", "disc")}
    assert "port:cntn:w" in str(stage["port"].fields())
    # (stages, connectors, forward order, the continuation fields that leave the period); in cons then port the
    # connector names disc.a, as trellis.cons-port.yml writes it, since the consumption and the discount stage
    # both continue to a field a (SD-38)
    periods = {"port then cons": ({"port", "cons", "disc"}, [{"w": "m"}], ["port", "cons", "disc"], [("disc", "a")]),
               "cons then port": ({"cons", "disc", "port"}, [{"disc.a": "k"}], ["cons", "disc", "port"], [("port", "w")]),
               "noport then cons": ({"noport", "cons", "disc"}, [], ["noport", "cons", "disc"], [("disc", "a")]),
               "port alone": ({"port", "disc"}, [{"w": "a"}], ["port", "disc"], [("disc", "a")])}
    for keys, connectors, order, outputs in periods.values():
        for listed in (sorted(keys), sorted(keys, reverse=True)):
            period = {"stages": {key: stage[key] for key in listed}, "connectors": connectors}
            assert forward_order(period) == order and period_joins(period)["outputs"] == outputs
    # both mappings inside cons then port, and noport, which keeps its continuation m, after cons, would close a loop
    # only through a pair inferred from equal names, cons.a to disc.a and noport.m to cons.m; since AMD-COMP-001 run 3
    # (10 October 2026) the selection offers no inferred pair against the authored order and withdraws every inferred
    # pair on a cycle under `inference-cycle`, which no operation refuses, so each period is ordered by its authored
    # pairs alone and cons's a leaves it; the export of 39849d46e answers the same with either consumption stage (SD-57)
    for keys, connectors, order, joins, outputs in (
            ({"cons", "disc", "port"}, [{"disc.a": "k"}, {"w": "m"}], ["disc", "port", "cons"],
             [{"from": ("disc", "a"), "to": ("port", "k")}, {"from": ("port", "w"), "to": ("cons", "m")}], [("cons", "a")]),
            ({"cons", "disc", "noport"}, [{"disc.a": "k"}], ["cons", "disc", "noport"],
             [{"from": ("disc", "a"), "to": ("noport", "k")}], [("cons", "a"), ("noport", "m")])):
        period = {"stages": {key: stage[key] for key in sorted(keys)}, "connectors": connectors}
        assert forward_order(period, "periods[0]") == order
        assert period_joins(period, "periods[0]") == {"joins": joins, "outputs": outputs}
    # the inter-period mapping joins the field that leaves port then cons, disc's a, and not cons's a, which disc reads;
    # it is written {disc.a: k}, as trellis.port-cons.yml writes it, since a bare name resolves only where one field of
    # that name stands at the perch in the period, and cons and disc both continue to a (SD-57)
    period = {"stages": {"port": stage["port"], "cons": stage["cons"], "disc": stage["disc"]}, "connectors": [{"w": "m"}]}
    assert inter_period_joins({"disc.a": "k"}, period, period) == [{"from": ("disc", "a"), "to": ("port", "k")}]


def test_item_2_the_reference_structure_is_reproduced(reference_runs, manifest, archive):
    runs, opened = reference_runs
    digest = hashlib.sha256((REFERENCE / "port_cons_h5.npz").read_bytes()).hexdigest()
    assert digest == ARCHIVE_SHA256 == manifest["archive"]["sha256"]
    assert not [path for path in opened if path.startswith(LEGACY_SOURCES)]
    calibration = yaml.safe_load((DECLARATION / "calibration" / "portfolio.yml").read_text(encoding="utf-8"))["calibration"]
    assert calibration == manifest["calibration_as_loaded"]
    for configuration, (model, solutions) in runs.items():
        assert len(model["periods"]) == len(solutions) == manifest["horizon"] + 1 and len(model["inter_connectors"]) == manifest["horizon"]
        for h, period in enumerate(model["periods"]):
            assert backward_order(period) == BACKWARD[configuration], (configuration, h)
            for key, stage in period["stages"].items():
                assert stage.name == key and repr(stage) == f"ElaboratedStage({key!r}, specified)"
                # the consumption stage is the demonstration's since AAS's instruction of 21 October 2026 (SD-33)
                assert os.path.normpath(stage.provenance["origin"]) == os.path.normpath(stage_file(key))
                assert h == 0 or stage is not model["periods"][0]["stages"][key]
        actual = tool.reference_arrays(configuration, solutions)
        expected = {key: value for key, value in archive.items() if key.startswith(configuration + "/")}
        assert sorted(actual) == sorted(expected), configuration
        for key, legacy in expected.items():
            assert actual[key].shape == legacy.shape, key
            if key.endswith("/grid"):
                np.testing.assert_array_equal(actual[key], legacy, err_msg=key)
            for sentinel in (tool.LOW, tool.HIGH):
                np.testing.assert_array_equal(actual[key] == sentinel, legacy == sentinel, err_msg=key)
            np.testing.assert_array_equal(np.isfinite(actual[key]), np.isfinite(legacy), err_msg=key)
    # the six expressions of the reference are kernels of cons.bl, equal at a hundred points: each the function of
    # a piece of the builders' kernels, called with its arguments and then the parameter values the record holds
    cons = runs["beginning_egm"][0]["periods"][0]["stages"]["cons"]
    c, a = np.linspace(0.05, 5.0, 100), np.linspace(0.01, 20.0, 100)
    m_d, dv = np.linspace(0.1, 30.0, 100), np.linspace(0.02, 3.0, 100)
    continuation = tool.ValueFn(a, -1.0 / a)
    names = {"rho": manifest["calibration_as_loaded"]["ρ"], "c": c, "a": a, "m_d": m_d, "V_cont": continuation,
             "dV_cont": lambda x: np.interp(x, a, dv)}
    legacy = {role: eval(text, {"__builtins__": {}}, names) for role, text in manifest["expressions"].items()}
    pieces = {(record.builder, piece.key): piece
              for record in (cons.dcsn.builder.bwd.kernels(), cons.builder.policy.kernels()) for piece in record.pieces}

    def kernel(builder, key, *arguments):
        piece = pieces[builder, key]
        return piece.function(*arguments, *piece.parameter_values)

    value, marginal = kernel("cntn_to_dcsn", "Aggregation", continuation(kernel("cntn_to_dcsn", "Pullback", m_d, c)), m_d, c)
    kernels = {"vfi_maximand": value, "marginal_bellman": marginal,
               "dcsn_to_cntn_transition": kernel("cntn_to_dcsn", "Pullback", m_d, c),
               "utility": kernel("cntn_to_dcsn", "Aggregation", np.zeros_like(c), m_d, c)[0],
               "inv_euler": kernel("policy", "InvEuler:Aggregation", dv, a),
               # the grid line is `grid` in the demonstration's block file, `endoggrid` in the earlier stage file (SD-33)
               "cntn_to_dcsn_transition": kernel("policy", "grid:Aggregation", c, a)}
    for role, computed in kernels.items():
        np.testing.assert_array_equal(computed, legacy[role], err_msg=role)


# The relative tolerance within which the share objective must take the same value at two adjacent shares for
# item 3 to accept either as the choice (PQ1 of the decisions record of the internal release 0.01): where the
# continuation values at two adjacent shares are bit-identical, Accelerate's values of the objective differ by
# at most 2.8e-16 of its size; where they differ, the smallest nonzero gap between the objective at the chosen
# share and at an adjacent share is 7.0e-14 of its size.
TIE_TOLERANCE = 1e-14


def port_continuation(model, solutions, h, terminal):
    """The continuation value the portfolio stage of periods[h] read, found from the period's joins as
    `tool.solve_period` finds it: the arrival value of the stage its field joins, or, where the field leaves the
    period, the value the inter-period connector names, which at h = 0 is the terminal value."""
    joined = {join["to"][0] for join in period_joins(model["periods"][h])["joins"] if join["from"][0] == "port"}
    if joined:
        (stage,) = joined
        return solutions[h][stage]
    return tool.continuation_across(model, h, solutions) if h else terminal


def share_ties(port, continuation, computed, reference):
    """The states at which the computed share and the reference's share lie one step of the share grid apart and
    the share objective, evaluated at both shares with the same continuation value, differs by no more than
    TIE_TOLERANCE times the larger of its two values in absolute value."""
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


def test_item_3_the_reference_values_are_reproduced_to_1e_12(reference_runs, manifest, archive, ending):
    """Every array of the fixed reference is reproduced to 1e-12, except that the portfolio share may lie one step
    of its grid from the reference's share at a state where the share objective takes the same value at both.

    The reference was recorded under Python 3.12, where numpy computes a dot product with the OpenBLAS library.
    Under Python 3.14 on macOS numpy computes it with Apple's Accelerate library, which can round the dot product
    of the same numbers differently in the last binary digit according to where in memory the numbers begin. At
    many levels of capital the share objective, the expected continuation value, is exactly the same at several
    adjacent shares, because every outcome of the shocks gives resources at which the continuation value is
    constant, beyond the end of its grid or near the top of the capital grid. The search chooses the first share
    at which the objective is largest, so the rounding decides which of those shares it chooses, and under
    Accelerate it chooses the share one step above the reference's at some of these states. Such a share is
    accepted where the objective, evaluated at both shares with the same continuation value, differs by no more
    than TIE_TOLERANCE times the larger of its two values in absolute value; every other element of the share,
    and every element of every other array, must agree with the reference to 1e-12. The number of shares accepted
    in this way depends on the library, so it is reported in a warning and in the evidence, not asserted."""
    runs, _ = reference_runs
    rows, ties = [], {}
    for configuration, (model, solutions) in runs.items():
        actual = tool.reference_arrays(configuration, solutions)
        terminal = tool.terminal_value(ending, TERMINAL[CONFIGURATIONS[configuration][1]])
        for h in range(manifest["horizon"] + 1):
            keys = sorted(key for key in actual if key.startswith(f"{configuration}/h{h}/") and not key.endswith("/grid"))
            if configuration == "beginning_vfi":
                rows.append({"configuration": configuration, "h": h, "arrays": len(keys), "largest difference": None,
                             "share ties": None, "result": "structural only: " + manifest["vfi_structural_only_reason"]})
                continue
            largest, tied_here = 0.0, 0
            for key in keys:
                compared = np.ones(actual[key].shape, dtype=bool)
                if key.endswith("/policy/varsigma"):
                    tied = share_ties(model["periods"][h]["stages"]["port"], port_continuation(model, solutions, h, terminal),
                                      actual[key], archive[key])
                    compared[tied] = False
                    if len(tied):
                        ties[key], tied_here = len(tied), tied_here + len(tied)
                np.testing.assert_allclose(actual[key][compared], archive[key][compared], rtol=1e-12, atol=1e-12, err_msg=key)
                largest = max(largest, float(np.max(np.abs(actual[key][compared] - archive[key][compared]), initial=0.0)))
            rows.append({"configuration": configuration, "h": h, "arrays": len(keys), "result": "equal to 1e-12",
                         "largest difference": largest, "share ties": tied_here})
    if ties:
        warnings.warn(f"item 3 accepted {sum(ties.values())} elements of the portfolio share, each one step of the share "
                      f"grid from the reference's share, as ties of the share objective to within {TIE_TOLERANCE:g} of "
                      "its size: " + "; ".join(f"{key} {count} of {archive[key].size}" for key, count in sorted(ties.items())),
                      stacklevel=1)
    if os.environ.get("CONS_PORT_WRITE_EVIDENCE") == "1":
        EVIDENCE.mkdir(exist_ok=True)
        (EVIDENCE / "reference-comparison.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        lines = [f"{'configuration':15s} {'h':>2s} {'arrays':>6s} {'largest difference':>19s} {'share ties':>10s}  result"]
        lines += [f"{row['configuration']:15s} {row['h']:2d} {row['arrays']:6d} "
                  f"{'' if row['largest difference'] is None else format(row['largest difference'], '.2e'):>19s} "
                  f"{'' if row['share ties'] is None else row['share ties']:>10}  "
                  f"{row['result'][:22]}" for row in rows]
        (EVIDENCE / "reference-comparison.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    recorded = json.loads((EVIDENCE / "reference-comparison.json").read_text(encoding="utf-8"))
    assert [(row["configuration"], row["h"], row["arrays"]) for row in recorded] == \
           [(row["configuration"], row["h"], row["arrays"]) for row in rows]


def test_item_4_the_reference_quadrature_adds_the_mean_of_the_logarithms_twice(reference_runs):
    runs, _ = reference_runs
    port = runs["beginning_egm"][0]["periods"][0]["stages"]["port"]
    noport = runs["cons_only"][0]["periods"][0]["stages"]["noport"]
    assert tool.method_at(port, "cntn_to_dcsn.value:Expectation:1").handler == "cons-port:gauss_hermite_reference"
    shocks, mean, covariance = tool.lognormal_law(port)
    assert shocks == ("Ψ", "θ")
    declared, weights = tool.normal_nodes(mean, covariance, [7, 7])
    doubled, same_weights = tool.reference_normal_nodes(mean, covariance, [7, 7])
    np.testing.assert_array_equal(weights, same_weights)
    np.testing.assert_allclose(doubled - declared, np.broadcast_to(mean, declared.shape), rtol=0, atol=1e-15)
    np.testing.assert_allclose(weights @ np.exp(declared), [1.040000, 1.000000], atol=5e-7)
    np.testing.assert_allclose(weights @ np.exp(doubled), [1.070524, 0.988813], atol=5e-7)
    # in one dimension the earlier library added the mean once, so the two rules agree
    _, mean_1, covariance_1 = tool.lognormal_law(noport)
    np.testing.assert_array_equal(tool.normal_nodes(mean_1, covariance_1, [7])[0],
                                  tool.reference_normal_nodes(mean_1, covariance_1, [7])[0])


def test_item_5_a_trellis_accreted_by_hand_equals_the_trellis_its_recipe_writes():
    stage = {name: elaborate_stage(load_stage(str(stage_file(name))))
             .calibrate(str(DECLARATION / "calibration" / "portfolio.yml")) for name in ("port", "cons", "disc")}
    stage["port"] = stage["port"].methodize(str(DECLARATION / "methods" / "port.yml")).configure(str(DECLARATION / "settings" / "port_wide.yml"))
    stage["cons"] = stage["cons"].methodize(str(DECLARATION / "methods" / "cons.yml")).configure(str(DECLARATION / "settings" / "cons_wide.yml"))
    stage["disc"] = stage["disc"].methodize(str(DECLARATION / "methods" / "disc.yml")).configure({})
    period = {"stages": stage, "connectors": [{"w": "m"}]}
    by_hand = accrete({"periods": [], "inter_connectors": []}, period)
    for _ in range(5):
        # the inter-period mapping as trellis.port-cons.yml writes it, {disc.a: k} (SD-38)
        by_hand = accrete(by_hand, period, {"disc.a": "k"})
    from_file = specified("spec.port-cons.yml")
    assert by_hand["inter_connectors"] == from_file["inter_connectors"] == [{"disc.a": "k"}] * 5
    for h, held in enumerate(from_file["periods"]):
        assert held["connectors"] == [{"w": "m"}]
        for key, occurrence in held["stages"].items():
            twin = by_hand["periods"][h]["stages"][key]
            assert occurrence.bindings == twin.bindings, (h, key)
            for view in map(attrgetter, ("initial.backward", "initial.forward", "builder.bwd", "builder.fwd")):
                assert view(occurrence).graph == view(twin).graph, (h, key)


# the review focus

def test_an_unknown_handler_is_refused_with_the_handlers_the_tool_realizes(ending):
    # the method opens the policy builder with the block file beside the methods file, which the stage file needs
    # since AAS's instruction of 21 October 2026 (SD-33); `ending` holds the representation and the marginal block
    block = str(DECLARATION / "methods" / "cons_egm.bl")
    cons = consumption_stage().methodize({"methods": [{"on": "policy", "method": "!egm", "block": block, "handler": "cons-port:unknown"}]}
                            ).configure(str(DECLARATION / "settings" / "cons.yml"))
    with pytest.raises(ValueError) as refused:
        tool.stage_operator(cons)
    assert "'cons-port:unknown'" in str(refused.value) and "cons-port:egm" in str(refused.value)


def test_in_cons_then_port_the_discount_stage_scales_the_portfolio_value_by_beta(reference_runs, manifest):
    runs, _ = reference_runs
    for period in runs["end_returns"][1]:
        np.testing.assert_array_equal(period["disc"].values, manifest["calibration_as_loaded"]["β"] * period["port"].values)


def test_a_method_choice_on_consumption_rebinds_the_six_consumption_occurrences(orders):
    choice = load_trellis(str(DECLARATION / "trellis.port-cons-vfi.yml"))
    switched = configure_trellis(methodize_trellis(orders["port-cons"], choice), choice)
    assert sorted(changed_positions(orders["port-cons"], switched)) == [(h, "cons") for h in range(6)]
    assert "!vfi" in str(switched["periods"][0]["stages"]["cons"].methods)
    assert "!egm" in str(orders["port-cons"]["periods"][0]["stages"]["cons"].methods)


def test_the_terminal_value_is_the_utility_of_consuming_the_resources(ending, manifest):
    grid = TERMINAL["a"]
    ρ = manifest["calibration_as_loaded"]["ρ"]
    terminal = tool.terminal_value(ending, grid)
    np.testing.assert_array_equal(terminal.values, np.where(grid > 0, grid ** (1 - ρ) / (1 - ρ), tool.LOW))
    np.testing.assert_array_equal(terminal.dvalues, np.where(grid > 0, grid ** (-ρ), tool.HIGH))


def test_the_endogenous_grid_operator_is_built_from_the_records_under_a_new_calibration_and_new_grids(ending, manifest):
    """The operator of `!egm` is one call of asva's egm on the kernels of the policy builder and the backward decision
    builder, and it holds no stage. Under ρ = 3 and grids other than the application's settings it gives what the
    reference's own expressions give at ρ = 3 on those grids: the consumption the inverse Euler equation gives at each
    saving, interpolated onto the grid of resources at the resources the endogenous grid gives and held in
    (1e-10, m_d − 1e-10); the saving the law of motion gives, held to the savings grid; the value and the marginal
    value of the aggregation."""
    ρ = 3.0
    settings = {"n_m": 150, "m_min": 0.05, "m_max": 20.0, "n_a": 300, "a_min": 1.0e-6, "a_max": 40.0,
                "grid_spacing": "expmult"}
    # a stage of its own, since a binding binds the stage it is called on (SB-10)
    stage = consumption_stage().calibrate({"ρ": ρ}).methodize(str(DECLARATION / "methods" / "cons.yml")).configure(settings)
    operator = tool.egm(stage)
    # the operator's saved form names neither the class of the stage nor the module that defines it
    saved = cloudpickle.dumps(operator)
    assert type(stage).__qualname__.encode() not in saved and type(stage).__module__.encode() not in saved
    grid = tool.expmult_grid(50.0, 400)
    continuation = tool.ValueFn(grid, -1.0 / (grid + 0.5), 1.0 / (grid + 0.5) ** 2)
    solved = operator(continuation)
    savings, resources = tool.savings_grid(stage), tool.evaluation_grid(stage)
    assert (len(savings), len(resources)) == (300, 150)

    def expression(role, **names):
        return eval(manifest["expressions"][role], {"__builtins__": {}}, {"rho": ρ, **names})

    chosen = expression("inv_euler", a=savings, dV_cont=continuation.dV)
    at = expression("cntn_to_dcsn_transition", a=savings, c=chosen)
    order = np.argsort(at)
    c = np.clip(np.interp(resources, at[order], chosen[order]), 1e-10, resources - 1e-10)
    a = np.clip(expression("dcsn_to_cntn_transition", m_d=resources, c=c), savings[0], savings[-1])
    np.testing.assert_array_equal(solved.grid, resources)
    np.testing.assert_allclose(solved.policy["c"], c, rtol=1e-12, atol=0)
    np.testing.assert_allclose(solved.policy["a"], a, rtol=1e-12, atol=0)
    np.testing.assert_allclose(solved.values, expression("utility", c=c) + continuation(a), rtol=1e-12, atol=0)
    np.testing.assert_allclose(solved.dvalues, expression("marginal_bellman", c=c), rtol=1e-12, atol=0)


def test_the_setting_grid_spacing_gives_the_even_and_the_multi_exponential_grid(ending):
    # the setting absent or `even`: numpy.linspace from the lower bound to the upper, bit for bit
    # a stage of its own, since a binding binds the stage it is called on (SB-10)
    methodized = consumption_stage().methodize(str(DECLARATION / "methods" / "cons.yml"))
    settings = {"n_m": 500, "m_min": 0.01, "m_max": 2000.0, "n_a": 400, "a_min": 1.0e-6, "a_max": 100.0}
    for source in (settings, {**settings, "grid_spacing": "even"}):
        stage = methodized.configure(source)
        np.testing.assert_array_equal(tool.evaluation_grid(stage), np.linspace(0.01, 2000.0, 500))
        np.testing.assert_array_equal(tool.savings_grid(stage), np.linspace(1.0e-6, 100.0, 400))
    # `expmult`: the count asked, strictly increasing from just above the lower bound to the upper bound, the
    # multi-exponential grid of the tool shifted by the lower bound, and dense near it: the first spacing is
    # less than a thousandth of the last, and more than half of the points lie in the lowest tenth of the range
    stage = methodized.configure({**settings, "grid_spacing": "expmult"})
    for grid, (low, high, count) in ((tool.evaluation_grid(stage), (0.01, 2000.0, 500)),
                                     (tool.savings_grid(stage), (1.0e-6, 100.0, 400))):
        assert len(grid) == count and low < grid[0] and np.isclose(grid[-1], high, rtol=1e-12, atol=0)
        assert np.all(np.diff(grid) > 0) and np.diff(grid)[0] < np.diff(grid)[-1] / 1000
        assert (grid <= low + (high - low) / 10).sum() > count / 2
        np.testing.assert_array_equal(grid, low + tool.expmult_grid(high - low, count))
    with pytest.raises(ValueError) as refused:
        tool.evaluation_grid(methodized.configure({**settings, "grid_spacing": "log"}))
    assert "'log'" in str(refused.value) and "'even'" in str(refused.value) and "'expmult'" in str(refused.value)


def test_solve_period_gives_the_same_values_whatever_the_list_order(reference_runs):
    runs, _ = reference_runs
    model, solutions = runs["end_returns"]
    period = model["periods"][1]
    listed = {"stages": dict(reversed(list(period["stages"].items()))), "connectors": period["connectors"]}
    again = tool.solve_period(listed, solutions[0]["cons"])
    for key, held in solutions[1].items():
        np.testing.assert_array_equal(again[key].values, held.values)
