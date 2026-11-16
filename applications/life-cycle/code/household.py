"""Backward values and forward cohort transitions from the life-cycle stages."""

from pathlib import Path

import numpy as np
import yaml

from bellman.distributions.families import label_weights, number_matrix, numeric_value
from bellman.factory.recipe import load_recipe
from bellman.native.records import Refusal
from bellman.stage import elaborate_text
from bellman.trellis import (
    calibrate_trellis,
    configure_trellis,
    connection_report,
    elaborate_trellis,
    methodize_trellis,
)


DIRECTORY = Path(__file__).resolve().parents[1] / "declaration"


def build(directory=DIRECTORY):
    """Construct each version of the trellis from its file recipe."""
    source = load_recipe(directory, "spec.yml")
    elaborated = elaborate_trellis(source)
    methodized = methodize_trellis(elaborated, source)
    calibrated = calibrate_trellis(methodized, source)
    configured = configure_trellis(calibrated, source)
    return elaborated, methodized, calibrated, configured


def calibration(directory=DIRECTORY):
    """Read the calibration shared with the indexed-by-age reference."""
    return yaml.safe_load((directory / "calibration" / "life_cycle.yml").read_text(encoding="utf-8"))["calibration"]


def savings_grid(directory=DIRECTORY):
    """Read the asset points for the indexed-by-age reference."""
    settings = yaml.safe_load((directory / "settings" / "life_cycle.yml").read_text(encoding="utf-8"))
    return np.asarray(settings["settings"]["savings_grid"])


def evaluate(record, key, inputs):
    """Evaluate one compiled piece at its named arguments."""
    (piece,) = (piece for piece in record.pieces if piece.key == key)
    result = piece.function(
        *(inputs[name] for name in piece.arguments), *(piece.parameter_values or ())
    )
    if len(piece.outputs) == 1:
        result = (result,)
    return dict(zip(piece.outputs, result, strict=True))


def value_function(grid, values):
    """Interpolate linearly in assets for each realized productivity state."""
    def at(z, a):
        z, a = np.broadcast_arrays(z, a)
        values_at = np.full(z.shape, np.nan)
        for i, row in enumerate(values):
            selected = z == i + 1
            values_at[selected] = np.interp(a[selected], grid, row)
        return values_at

    return at


def grid_points(record):
    """Read the Cartesian points of the realized terminal representation."""
    grid = record.grids["dcsn_to_arvl.evaluate[V[<]]"]
    if isinstance(grid, Refusal):
        raise ValueError(grid.reason)
    if grid.word != "Cartesian" or grid.coordinates != ("z_4", "a_4") or not grid.points:
        raise ValueError("The terminal value representation needs a Cartesian grid in (z_4, a_4).")
    points = np.asarray(grid.points, dtype=float)
    if np.unique(points, axis=0).shape[0] != len(grid.points):
        raise ValueError("Distinct terminal grid points coincide in floating-point coordinates.")
    productivity = np.unique(points[:, 0]).astype(int)
    assets = np.unique(points[:, 1])
    if assets[0] != 0 or not np.all(np.diff(assets) > 0):
        raise ValueError("The savings points must increase from the borrowing bound of zero.")
    return productivity, assets


def consumption_method(stage, values, marginal):
    """Select a policy for the linear asset interpolation, which holds endpoints fixed."""
    if not np.all(np.isfinite(values)):
        raise ValueError("Represented continuation values must be finite.")
    if np.all(marginal == 0) and np.all(values == values[:, :1]):
        method, filename = "explicit", "methods.consume-all.bl"
    elif np.all(stage.par["β"].value * marginal > 0) and np.all(
        np.isfinite(marginal[:, 1:])
    ):
        method, filename = "egm", "methods.bl"
    else:
        raise ValueError(
            "The continuation must be constant in assets with zero marginal values, "
            "or have positive discounted marginal values with infinity allowed only at the borrowing bound."
        )

    if "policy" in stage.methods and stage.methods["policy"].method.name == method:
        return stage
    path = Path(stage.provenance["origin"])
    elaborated = elaborate_text(stage.provenance["text"], str(path))
    methodized = elaborated.methodize(
        [path.with_name("methods.envelope.bl"), path.with_name(filename)]
    )
    calibration = {name: parameter.value for name, parameter in stage.par.items() if not parameter.derived}
    settings = {name: setting.value for name, setting in stage.settings.items()}
    calibrated = methodized.calibrate({"calibration": calibration})
    return calibrated.configure({"settings": settings})


def after_decision(record, state, value, marginal, derivative, pullback="Pullback"):
    """Pull back and aggregate value and its stated marginal value."""
    points = evaluate(record, pullback, state)
    args = {
        **state,
        "V≻": value(*points.values()),
        derivative: marginal(*points.values()),
    }
    fields = evaluate(record, "Aggregation", args)
    fields.update(evaluate(record, "marginal_decision:Derivative:1", args))
    return fields


def before_decision(record, state, fields, coordinate):
    """Apply the arrival formulas to fields already evaluated at decision."""
    args = {**state, **fields, f"D_{{{coordinate}}}(V)": fields[f"D_{{{coordinate}}}V"]}
    values = evaluate(record, "Aggregation", args)
    (values["marginal"],) = evaluate(record, "marginal_arrival:Derivative:1", args).values()
    return values


def terminal(stage, arrival, inputs, marginal, z, a):
    """Evaluate the two terminal functions one grid point at a time."""
    initial = {"z_4": z, "a_4": a}
    decision = evaluate(arrival, "Pullback", initial)
    record = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    value_on_grid = np.vectorize(inputs["V[>]"], otypes=[float])
    marginal_on_grid = np.vectorize(marginal, otypes=[float])
    fields = after_decision(
        record, {**decision, "age": inputs["age"]}, value_on_grid, marginal_on_grid, "D_{a_end}V[>]"
    )
    return before_decision(arrival, initial, fields, "a_T")


def endogenous_policy(policy, savings, z, a, cash, continuation, marginal):
    """Interpolate the inverse Euler equation, using cash when the bound binds."""
    grid = policy.grids["policy"]
    points = np.column_stack((z.ravel(), a.ravel()))
    if grid.coordinates != ("z_4", "a_4") or not np.array_equal(points, grid.points):
        raise ValueError("The EGM grid must use the represented productivity and asset points.")
    args = {
        "V≻": continuation(z, a), "z_4": z, "a_4": a,
        "D_{a_4}(V≻)": marginal(z, a),
    }
    with np.errstate(over="raise", divide="raise", invalid="raise"):
        inverse = evaluate(policy, "inverse_euler:Aggregation", args)
    endogenous_cash = evaluate(policy, "endogenous_grid:Aggregation", {**args, **inverse})
    if not np.all(np.isfinite(endogenous_cash["m≻"])) or not np.all(
        np.diff(endogenous_cash["m≻"], axis=1) > 0
    ):
        raise ValueError("The endogenous cash points must be finite and strictly increasing in savings.")
    c = np.array(cash, copy=True)
    for i, (m, c_node) in enumerate(zip(endogenous_cash["m≻"], inverse["c≻"])):
        interior = cash[i] > m[0]
        x = cash[i, interior]
        lo = np.clip(np.searchsorted(m, x) - 1, 0, m.size - 2)
        fraction = (x - m[lo]) / (m[lo + 1] - m[lo])
        c[i, interior] = (1 - fraction) * c_node[lo] + fraction * c_node[lo + 1]
    trial = evaluate(savings, "Pushforward", {"z_c": z, "m": cash, "c": c})
    return cash - np.clip(trial["a_4≻"], a.min(), a.max())


def consumption(stage, continuation, marginal, age_next, z, a):
    """Compute consumption, savings, and the value sent back with current age."""
    inputs = {"V[>]": continuation, "age_next": age_next}
    initial = {"z_3": z, "a_3": a, "age_next": age_next}
    arrival = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
    decision = evaluate(arrival, "Pullback", initial)
    savings = stage.builder["dcsn", "cntn"].kernels(inputs=inputs)
    policy = stage.builder.policy.kernels(inputs=inputs)
    if stage.methods["policy"].method.name == "explicit":
        c = evaluate(policy, "consume_all:Aggregation", decision)["c"]
    else:
        handler = {"life-cycle:egm": endogenous_policy}[stage.methods["policy"].handler]
        c = handler(policy, savings, decision["z_c"], a, decision["m"], continuation, marginal)
    state = {**decision, "c": c}
    record = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    fields = after_decision(
        record, {**state, "age_next≻": age_next},
        continuation, marginal, "D_{a_4}V[>]",
    )
    return {
        **before_decision(arrival, initial, fields, "m"),
        "consumption": c,
        "savings": evaluate(savings, "Pushforward", state)["a_4≻"],
    }


def entry(stage, value, marginal, age, z, a):
    """Carry value, marginal value, and age back through the entry stage."""
    inputs = {"V[>]": value, "age": age}
    state = {"z_0": z, "a_0": a}
    arrival = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
    decision = evaluate(arrival, "Pullback", state)
    backward = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    fields = after_decision(
        backward, {**decision, "age": age}, value, marginal, "D_{a_1}V[>]"
    )
    return before_decision(arrival, state, fields, "a_e")


def laws(record, key):
    """Read the one distribution declaration that a finite draw integrates."""
    (owner,) = record.laws[key].declarations
    return owner.term


def transition_matrix(law):
    """Read the native matrix of an age-selected Markov chain."""
    rows = (row.items for row in law.args[0].items)
    return np.asarray(number_matrix(rows, {}), dtype=float)


def draw(stage, value, marginal, age, z, a, productivity):
    """Integrate the productivity draw at the supplied age."""
    inputs = {"V[>]": value, "age": age}
    record = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
    dcsn = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    matrix = transition_matrix(laws(record, "value:Expectation:1"))
    derivative = "marginal_arrival:Derivative:1"
    marginal_matrix = transition_matrix(laws(record, derivative))
    initial = {"z_2": z, "a_2": a}
    expected = np.zeros_like(a)
    expected_marginal = np.zeros_like(a)
    for i, realization in enumerate(productivity):
        state = evaluate(record, "Pullback", {**initial, "z": realization})
        fields = after_decision(
            dcsn, {**state, "age": age}, value, marginal, "D_{a_3}V[>]"
        )
        expected += matrix[z - 1, i] * fields["V"]
        integrand = evaluate(record, derivative, {"z": realization, "D_{a_d}(V)": fields["D_{a_d}V"]})
        expected_marginal += marginal_matrix[z - 1, i] * integrand["D_{a_2}V[<]"]
    fields = evaluate(record, "Aggregation", {**initial, "w": expected, "age": age})
    return {**fields, "marginal": expected_marginal}


def mortality(stage, value, marginal, age, z, a):
    """Average the survival and bequest values under the mortality law."""
    inputs = {"V[>]": value, "age": age}
    initial = {"z_1": z, "a_1": a}
    arrival = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
    state = evaluate(arrival, "Pullback", initial)
    record = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    alive = evaluate(record, "Pullback:survive", {**state, "s": "survive"})
    points = alive["z_2≻"], alive["a_2≻"]
    fields = evaluate(record, "Aggregation", {**state, "age": age, "V≻": value(*points)})
    derivative = "marginal_decision:Derivative:1"
    weights = label_weights(laws(record, derivative))
    expected_marginal = np.zeros_like(a)
    for label, weight in zip(("survive", "die"), weights, strict=True):
        integrand = evaluate(
            record, derivative, {**state, "s": label, "D_{a_2}V[>]": marginal(*points)}
        )
        expected_marginal += numeric_value(weight, {}) * integrand["D_{a_m}V"]
    fields["D_{a_m}V"] = expected_marginal
    return before_decision(arrival, initial, fields, "a_m")


def transition(stages, values, continuation, age_next, z, a, productivity, assets):
    """Compose the forward stage maps and allocate savings to neighboring nodes."""
    age = values["age"]
    inputs = {"V[>]": continuation, "age": age}
    entry, mortality_stage, draw_stage, consumption_stage = (
        stages[name] for name in ("entry", "mortality", "draw", "consumption")
    )
    entry_dcsn = entry.builder["arvl", "dcsn"].kernels(inputs=inputs)
    entry_cntn = entry.builder["dcsn", "cntn"].kernels(inputs=inputs)
    start = evaluate(entry_dcsn, "Pushforward", {"z_0": z, "a_0": a})
    entered = evaluate(entry_cntn, "Pushforward", start)

    mortality_dcsn = mortality_stage.builder["arvl", "dcsn"].kernels(inputs=inputs)
    mortality_cntn = mortality_stage.builder["dcsn", "cntn"].kernels(inputs=inputs)
    exposed = evaluate(
        mortality_dcsn, "Pushforward", {"z_1": entered["z_1≻"], "a_1": entered["a_1≻"]}
    )
    survived = evaluate(mortality_cntn, "Pushforward", {**exposed, "s": "survive"})
    died = evaluate(mortality_cntn, "Pushforward", {**exposed, "s": "die"})
    assert died["death≻"] == "die"
    np.testing.assert_array_equal(died["a_b≻"], exposed["a_m"])
    weights = label_weights(laws(mortality_cntn, "DistributionExtension:s"))
    survival = numeric_value(weights[0], {})

    draw_dcsn = draw_stage.builder["arvl", "dcsn"].kernels(inputs=inputs)
    draw_cntn = draw_stage.builder["dcsn", "cntn"].kernels(inputs=inputs)
    pi = transition_matrix(laws(draw_dcsn, "DistributionExtension:z"))
    c_inputs = {"V[>]": continuation, "age_next": age_next}
    consumption_dcsn = consumption_stage.builder["arvl", "dcsn"].kernels(inputs=c_inputs)
    consumption_cntn = consumption_stage.builder["dcsn", "cntn"].kernels(inputs=c_inputs)
    rows = np.arange(z.size)
    lottery = np.zeros((z.size, z.size))
    for i, realization in enumerate(productivity):
        drawn = evaluate(
            draw_dcsn, "Pushforward",
            {"z_2": survived["z_2≻"], "a_2": survived["a_2≻"], "z": realization},
        )
        moved = evaluate(draw_cntn, "Pushforward", drawn)
        z_3 = np.broadcast_to(moved["z_3≻"], a.shape)
        a_3 = moved["a_3≻"]
        cash = evaluate(
            consumption_dcsn, "Pushforward",
            {"z_3": z_3, "a_3": a_3, "age_next": age_next},
        )
        a_index = np.searchsorted(assets, a_3)
        c = values["consumption"][z_3 - 1, a_index]
        saved = evaluate(consumption_cntn, "Pushforward", {**cash, "c": c})
        savings = saved["a_4≻"]
        lo = np.clip(np.searchsorted(assets, savings) - 1, 0, assets.size - 2)
        upper_share = (savings - assets[lo]) / (assets[lo + 1] - assets[lo])
        probability = survival * pi[survived["z_2≻"] - 1, i]
        cols = ((saved["z_4≻"] - 1) * assets.size + lo).ravel()
        lottery[rows, cols] += (probability * (1 - upper_share)).ravel()
        lottery[rows, cols + 1] += (probability * upper_share).ravel()
    return lottery


def solve(trellis, terminal_inputs, *, terminal_marginal):
    """Solve backward from the supplied age, value, and asset derivative."""
    periods = trellis["periods"]
    terminal_stage = periods[0]["stages"]["terminal"]
    terminal_conditions = terminal_stage.check_inputs(terminal_inputs)
    if not callable(terminal_marginal):
        raise TypeError("The terminal asset derivative must be a function of productivity and assets.")
    age = terminal_inputs["age"]
    if age < len(periods):
        raise ValueError(
            f"Terminal age {age} would require a negative household age over {len(periods)} periods."
        )
    arrival = terminal_stage.builder["dcsn", "arvl"].kernels(inputs=terminal_inputs)
    productivity, assets = grid_points(arrival)
    z, a = np.meshgrid(productivity, assets, indexing="ij")
    end = terminal(terminal_stage, arrival, terminal_inputs, terminal_marginal, z, a)

    results = []
    incoming = end
    for period in periods:
        stages = period["stages"]
        chosen = consumption_method(stages["consumption"], incoming["V"], incoming["marginal"])
        stages = {**stages, "consumption": chosen}
        continuation = value_function(assets, incoming["V"])
        marginal = value_function(assets, incoming["marginal"])
        age_next = int(incoming["age"])
        v4 = consumption(stages["consumption"], continuation, marginal, age_next, z, a)
        age = int(v4["age"])
        v4_fn = value_function(assets, v4["V"])
        v4_marginal = value_function(assets, v4["marginal"])
        v3 = draw(stages["draw"], v4_fn, v4_marginal, age, z, a, productivity)
        v2 = mortality(
            stages["mortality"], value_function(assets, v3["V"]),
            value_function(assets, v3["marginal"]), v3["age"], z, a,
        )
        v1 = entry(
            stages["entry"], value_function(assets, v2["V"]),
            value_function(assets, v2["marginal"]), v2["age"], z, a,
        )
        result = {
            "age": int(v1["age"]),
            "ages": tuple(int(fields["age"]) for fields in (v1, v2, v3, v4)),
            "policy_method": chosen.methods["policy"],
            "policy_requirements": chosen.builder.policy.obligations(),
            "consumption": v4["consumption"].ravel(),
            "savings": v4["savings"].ravel(),
            "values": tuple(fields["V"].ravel() for fields in (v1, v2, v3, v4)),
            "marginals": tuple(fields["marginal"].ravel() for fields in (v1, v2, v3, v4)),
            "transition": transition(stages, v4, continuation, age_next, z, a, productivity, assets),
        }
        results.append(result)
        incoming = v1
    return results, assets, terminal_conditions


def compare(actual, expected):
    """Check every stage's value and every period's policies and transition."""
    maxima = dict.fromkeys(("consumption", "savings", "values", "marginals", "transition"), 0.0)
    for observed, reference in zip(actual, expected, strict=True):
        assert observed["ages"] == (reference["age"],) * 4
        for name in maxima:
            diff = np.max(np.abs(np.asarray(observed[name]) - np.asarray(reference[name])))
            maxima[name] = max(maxima[name], float(diff))
            np.testing.assert_allclose(observed[name], reference[name], atol=2e-12, rtol=2e-12)
    return maxima


if __name__ == "__main__":
    from argparse import ArgumentParser

    from reference import compare_original, solve as indexed_by_age

    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--terminal-age", type=int, required=True, help="Terminal age of the fixture")
    parser.add_argument("--research-reference", type=Path, help="Original check_age_as_a_field.py")
    args = parser.parse_args()
    *_, configured = build()
    report = connection_report(configured)
    print(f"{report.counts['certified']} certified routes and {len(report.diagnostics)} diagnostics")
    def zero(z, a):
        return 0.0

    inputs = {"age": args.terminal_age, "V[>]": zero}
    results, assets, terminal_conditions = solve(configured, inputs, terminal_marginal=zero)
    for condition in terminal_conditions:
        print(condition.explanation)
    expected_grid = savings_grid()
    np.testing.assert_array_equal(assets, expected_grid)
    print(compare(results, indexed_by_age(calibration(), expected_grid)))
    if args.research_reference:
        compare_original(results, assets, args.research_reference)
        print("All eight ages agree with the original indexed reference.")
