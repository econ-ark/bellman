"""The two routes to the perfect foresight consumption function and the
numerical procedures they use, for the notebook `closed-form-and-grid.ipynb`
beside this file and for the package's acceptance tests, which load this
file by its path.

The stage file `declaration/stages/perfect_foresight/perfect_foresight.bl`
states the model. It defines the return patience factor q and sends human
wealth backward as a constant field. The closed-form methods define h_lim
and L_lim; the grid method reads supplied human wealth. The closed-form
route binds the addition `methods.bl` beside the stage file, which types
`!explicit` on the policy builder and on the two value builders and defines
the marginal propensity to consume κ = 1 - q: the consumption function, the
decision value and its marginal, and the arrival value and its marginal are
the compiled kernels of the lines of those three blocks, and this module
writes no formula of them. The closed
form is checked against the stage file's own blocks, the Bellman equation,
the law of motion and the arrival value's normalization, through their
compiled kernels (`value_kernels`).

The gridded route binds the replacing selection `methods.egm.bl`: the
endogenous grid method on the policy builder, iterated here on the compiled
kernels of its block and of the two marginal lines, with the consumption
function the linear interpolant of the pairs the method computes. The fixed
point's `evaluate(m)` refuses a point outside its pairs unless extrapolation
is asked for, and then applies the checked endpoint-secant extension and
reports it.

`piece` and `interpolate` keep the signatures of the module's first version,
which other programs import: `piece` gives a kernel as a function of its
positional arguments, and `interpolate` is the piecewise linear interpolant
with its end segments extended, a helper that no route of this module reads.

The module also supplies the numerical preparation of AMD-MT-003 build
contract §4, which the package leaves to applications: the scalar evaluators
`Linear` and `Pchip`, the endpoint-secant extension that only the policy
comparison and an explicit request of the fixed point's `evaluate` select,
the scalar linear reconstruction of the selected pairs of the endogenous
grid method on a family's own grid, and the preparation of a
representation from each of its four data sources. The package supplies the
exact comparison of two finite supports, `representations.supports_equal`,
and the realized grids of `kernels()`.

The functions whose names begin with `reference_` are test references: the
closed form derived independently in `economics.md` and written in Python,
so that the compiled kernels can be compared with them. No route reads them.
"""

from __future__ import annotations

import itertools
import math
import numbers
import warnings
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple

import numpy as np

from bellman.stage import elaborate_stage
from bellman.stage.representations import supports_equal

FOLDER = Path(__file__).resolve().parents[1]
ROOT = FOLDER.parents[1]
DECLARATION = FOLDER / "declaration"
STAGE_FOLDER = DECLARATION / "stages" / "perfect_foresight"
STAGE = STAGE_FOLDER / "perfect_foresight.bl"
METHODS = STAGE_FOLDER / "methods.bl"
GRIDDED_METHODS = STAGE_FOLDER / "methods.egm.bl"
CALIBRATION = DECLARATION / "calibration" / "perfect_foresight.yml"

# the four declared parameters, in the order the stage file declares them
DECLARED = ("β", "ρ", "R", "Γ")
# the key in `stage.builder` of each builder of the stage, by its block id
BUILDERS = {"policy": "policy", "cntn_to_dcsn": ("cntn", "dcsn"), "dcsn_to_arvl": ("dcsn", "arvl")}


# --- the stages ---


def source(path):
    """The source record of the file at `path` as a verb reads it, its text
    and its origin, the file's path from the repository's root, so that a
    stage and a refusal name the file as the repository holds it in every
    checkout."""
    return {"text": path.read_text(encoding="utf-8"), "origin": path.relative_to(ROOT).as_posix()}


def elaborated():
    """The symbolic stage of the stage file, the first step of each route:
    `elaborate`, with no methods, calibration or settings bound."""
    return elaborate_stage(
        {"stage": source(STAGE), "calibration": {}, "settings": {}, "methods": {}}
    )


def closed_form_stage(calibration=CALIBRATION):
    """The stage bound from the folder's files by `elaborate → methodize →
    calibrate → configure`: the addition `methods.bl`, which types
    `!explicit` on the policy builder and on the two value builders, the
    calibration, and an empty settings source, since the closed form reads
    no setting. `calibration` is the folder's calibration file unless another
    source is given, a path or a mapping as `calibrate` reads them."""
    stage = elaborated()
    stage.methodize(source(METHODS))
    stage.calibrate(calibration)
    stage.configure({"settings": {}})
    return stage


def gridded_stage(n_a, a_min, a_max, calibration=CALIBRATION):
    """The stage bound from the replacing selection `methods.egm.bl` by
    `elaborate → methodize → calibrate → configure`, with the calibration of
    `closed_form_stage` unless another source is given, and the three
    settings of the grid of savings, which the folder holds in no settings
    file and which are supplied here."""
    stage = elaborated()
    stage.methodize(source(GRIDDED_METHODS))
    stage.calibrate(calibration)
    stage.configure({"settings": {"n_a": n_a, "a_min": a_min, "a_max": a_max}})
    return stage


def parameters(stage):
    """The values of the four declared parameters at the stage's
    calibration, by name."""
    return {name: stage.par[name].value for name in DECLARED}


# --- the compiled kernels ---


def _piece(record, key):
    """The piece `key` of a builder's `kernels()` record."""
    (found,) = [held for held in record.pieces if held.key == key]
    return found


def _call(found, values, named):
    """The function of the piece `found` called with the arguments `named`,
    a mapping from each argument's printed name to its value, followed by the
    parameter values `values` in the piece's order. An argument the mapping
    does not give is passed as NaN, so that a kernel that read it would give
    a value that is not finite, which `_finite` refuses."""
    arguments = [named.get(name, math.nan) for name in found.arguments]
    return found.function(*arguments, *values)


def _output_piece(record, key, name):
    """The compiled expression for one named output of a primitive."""
    found, = [part for identity, part in record.output_kernels[key].items()
              if identity.field == name]
    return found


def output_function(record, key, name, parameters=None):
    """One output, with the record’s calibration or explicitly supplied parameters."""
    found = _output_piece(record, key, name)
    values = (found.parameter_values if parameters is None else
              tuple(parameters[key] for key in found.parameters))
    return lambda **named: _call(found, values, named)


def kernel_function(record, key):
    """One piece of a builder's `kernels()` record as a function of its
    named arguments alone, `function(m=..., c=...)`, the values of the
    parameters it reads bound from the record; an argument left out is one
    the kernel does not read."""
    found = _piece(record, key)
    values = tuple(found.parameter_values)
    return lambda **named: _call(found, values, named)


def _declared_function(stage, record, key):
    """One piece of a kernels record of `stage.declared`, which binds no
    calibration, as a function of its named arguments alone, the values of
    the parameters it reads taken from the calibration of `stage`."""
    found = _piece(record, key)
    values = tuple(stage.par[name].value for name in found.parameters)
    return lambda **named: _call(found, values, named)


def piece(record, key, values=None):
    """One piece of a builder's `kernels()` record as a function of its
    positional arguments alone, in the order of the piece's `arguments`, the
    values of the parameters it reads bound from the record, or, for the
    record of a declared builder, which holds no calibration, from `values`
    by name."""
    found = _piece(record, key)
    bound = (
        tuple(found.parameter_values)
        if values is None
        else tuple(values[name] for name in found.parameters)
    )
    return lambda *arguments: found.function(*arguments, *bound)


def kernel_text(record, key):
    """The Python text of one piece of a builder's `kernels()` record, as
    the package writes it."""
    return _piece(record, key).python


def _shown(number):
    """A number as a sentence writes it: a NumPy scalar as the Python number
    it equals, any other number as it is."""
    if isinstance(number, np.floating):
        return repr(float(number))
    if isinstance(number, np.integer):
        return repr(int(number))
    return repr(number)


def _finite(name, value):
    """`value` as an array, refused where any of its entries is not finite."""
    value = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(value)):
        bad = value[~np.isfinite(value)]
        raise ValueError(
            f"{name} is not finite at {bad.size} of its {value.size} points, the first value "
            f"being {_shown(bad[0])}"
        )
    return value


def _above(points, limit, coordinate, function):
    """The points of the coordinate `coordinate` as an array, refused where
    any lies at or below `limit`: the closed form holds where total wealth is
    positive."""
    points = np.asarray(points, dtype=float)
    low = points[~(points > limit)]
    if low.size:
        raise ValueError(
            f"the {function} is evaluated at {coordinate} = {_shown(low.flat[0])}, at or below "
            f"the natural borrowing limit L = {_shown(limit)}, where total wealth "
            f"{coordinate} - L = {_shown(low.flat[0] - limit)} is not positive; the closed form "
            f"holds on {coordinate} > L"
        )
    return points


def _continuation(p, taken):
    """An initial CRRA continuation value at the human wealth `taken`:
    utility of total wealth on a > -`taken`, a measurable initial value
    function, which no route evaluates as a solved continuation value."""
    def continuation(a):
        wealth = _above(a, -taken, "a", "initial continuation value") + taken
        return _finite("initial continuation value", wealth ** (1 - p["ρ"]) / (1 - p["ρ"]))
    return continuation


def stationary_inputs(stage):
    """Finite stationary human wealth and an initial CRRA continuation value.

    The value is utility of total wealth on a > -h[>], a measurable initial
    value function. The human wealth is the limit 1/(1 - Γ/R) - 1, which the
    closed form, its value kernels and the grid's checks read; the gridded
    route reads it only to refuse a grid of savings that starts at or below
    the natural borrowing limit, and computes human wealth step by step.
    """
    p = parameters(stage)
    ratio = p["Γ"] / p["R"]
    if not ratio < 1:
        raise ValueError("Stationary finite human wealth requires Γ < R; use gridded_step with supplied finite inputs.")
    taken = 1 / (1 - ratio) - 1
    return {"V[>]": _continuation(p, taken), "h[>]": taken}


def gridded_step(stage, inputs, continuation_marginal):
    """One endogenous-grid step for supplied finite continuation data.

    The value and its derivative are supplied independently. Their agreement
    and the callable's measurability remain mathematical obligations. This
    step admits Γ >= R and makes no stationary-solution claim.
    """
    conditions = stage.check_inputs(inputs)
    grid, savings = _realized(stage, "policy", inputs=inputs)
    limit = -float(inputs["h[>]"])
    _above(savings, limit, "a", "continuation value")
    marginal = _finite("continuation marginal value", continuation_marginal(savings))
    if np.any(marginal <= 0):
        raise ValueError("The continuation marginal value must be positive for the inverse Euler equation.")
    policy_record = stage.builder.policy.kernels(inputs=inputs)
    candidate = kernel_function(policy_record, "g_cntn_to_dcsn:Aggregation")
    consumption, resources = candidate(a=savings, **{"D_{a}(V≻)": marginal})
    _finite("candidate consumption", consumption)
    _finite("endogenous resources", resources)
    if not np.all((consumption > 0) & (consumption < resources - limit)):
        raise ValueError("The endogenous-grid pairs violate the authored strict feasible set.")
    policy = Linear(resources, consumption, "m")
    decision = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    arrival = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
    value = output_function(decision, "Aggregation", "V")
    h = output_function(decision, "Aggregation", "h")(**{"h≻": inputs["h[>]"]})
    sent = output_function(arrival, "Aggregation", "h")(h=h)
    return SimpleNamespace(
        inputs=inputs, input_conditions=conditions, grid=grid,
        knots=resources, consumption=consumption, policy=policy,
        value=_finite("decision value", value(m=resources, c=consumption,
                    **{"V≻": inputs["V[>]"](savings)})),
        h=float(h), sent_h=float(sent), limit=limit,
    )


def closed_form(stage):
    """The closed form as the stage holds it under `!explicit`: the derived
    parameters read from `stage.par` at the calibration, the return patience
    factor `return_patience` (q), κ, limiting human wealth `h` (h_lim) and
    borrowing bound `limit` (L_lim); and five functions, each the compiled kernel
    of a line of one explicit block: `consumption(m) = κ(m - L)`, the
    decision value `value(m) = κ^(-ρ)(m - L)^(1-ρ)/(1-ρ)` and its marginal
    `marginal(m) = κ^(-ρ)(m - L)^(-ρ)`, all three on m > L, and the arrival
    value `arrival_value(k) = Γ^(1-ρ) κ^(-ρ)(Rk/Γ + 1 - L)^(1-ρ)/(1-ρ)` and
    its marginal `arrival_marginal(k) = RΓ^(-ρ) κ^(-ρ)(Rk/Γ + 1 - L)^(-ρ)`,
    both on k > L. Each function refuses a point at or below the limit,
    where total wealth is not positive, and a result that is not finite."""
    q, κ, h, L = (stage.par[name].value for name in ("q", "κ", "h_lim", "L_lim"))
    # The checker does not evaluate the callable. Its evaluator is constructed below.
    inputs = {"V[>]": lambda a: form.arrival_value(a), "h[>]": h - 1}
    conditions = stage.check_inputs(inputs)
    consumption = kernel_function(stage.builder.policy.kernels(inputs=inputs), "consumption:Aggregation")
    decision_record = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    arrival_record = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
    decision = output_function(decision_record, "Aggregation", "V")
    decision_marginal = kernel_function(decision_record, "marginal:Derivative:1")
    arrival = output_function(arrival_record, "Aggregation", "V")
    arrival_marginal = kernel_function(arrival_record, "arrival_marginal:Derivative:1")
    form = SimpleNamespace(
        inputs=inputs,
        input_conditions=conditions,
        return_patience=q,
        κ=κ,
        h=h,
        limit=L,
        consumption=lambda m: _finite(
            "the consumption", consumption(m=_above(m, L, "m", "consumption function"))
        ),
        value=lambda m: _finite(
            "the decision value", decision(m=_above(m, L, "m", "decision value"))
        ),
        marginal=lambda m: _finite(
            "the decision marginal value",
            decision_marginal(m=_above(m, L, "m", "decision marginal value")),
        ),
        arrival_value=lambda k: _finite(
            "the arrival value", arrival(k=_above(k, L, "k", "arrival value"))
        ),
        arrival_marginal=lambda k: _finite(
            "the arrival marginal value",
            arrival_marginal(k=_above(k, L, "k", "arrival marginal value")),
        ),
    )

    return form


def value_kernels(stage):
    """The compiled kernels of the stage file's own blocks that the Bellman
    equation reads, as `stage.declared` builds them, each called at the
    values the calibration of `stage` binds to the parameters it reads: the
    law of motion of savings `savings(m, c) = m - c`, the decision value's
    aggregation `decision_value(V≻, m, c) = 𝑢(c) + βV≻`, the law of motion of
    resources `resources(k) = Rk/Γ + 1` and the arrival value's aggregation
    `arrival_value(V, k) = Γ^(1-ρ)V`. Under `!explicit` the operative value
    builders hold the closed form, so the stage file's equations are read
    from the declared builders, which methods do not change."""
    inputs = stationary_inputs(stage)
    conditions = stage.check_inputs(inputs)
    decision = stage.declared["cntn", "dcsn"].kernels(inputs=inputs)
    arrival = stage.declared["dcsn", "arvl"].kernels(inputs=inputs)
    savings = _declared_function(stage, decision, "Pullback")
    aggregation = output_function(decision, "Aggregation", "V", parameters(stage))
    resources = _declared_function(stage, arrival, "Pullback")
    normalization = output_function(arrival, "Aggregation", "V", parameters(stage))
    return SimpleNamespace(
        input_conditions=conditions,
        savings=lambda m, c: savings(m=m, c=c),
        decision_value=lambda continuation, m, c: aggregation(
            **{"V≻": continuation, "m": m, "c": c}
        ),
        resources=lambda k: resources(k=k),
        arrival_value=lambda value, k: normalization(V=value, k=k),
    )


# --- the identities of the closed form ---


def bellman_residual(stage, m, policy=None):
    """The residual of the Bellman equation the stage file writes, at the
    closed form, through the compiled kernels: v(m) - G(V≺(a), m, c), where
    v and V≺ are the closed form's decision and arrival values
    (`closed_form`), G is the decision value's aggregation 𝑢(c) + βV≻ and a
    the saving m - c, both from the stage file's blocks (`value_kernels`),
    and c is the closed form's consumption or, where `policy` is given, that
    function of m, such as the converged policy of the gridded route."""
    form, kernels = closed_form(stage), value_kernels(stage)
    m = np.asarray(m, dtype=float)
    c = form.consumption(m) if policy is None else np.asarray(policy(m), dtype=float)
    a = kernels.savings(m, c)
    return form.value(m) - kernels.decision_value(form.arrival_value(a), m, c)


def arrival_residual(stage, k):
    """The residual of the arrival value block the stage file writes, at the
    closed form, through the compiled kernels: V≺(k) - Γ^(1-ρ) v(Rk/Γ + 1),
    the closed form's arrival value less the stage file's normalization of
    the closed form's decision value at the resources its law of motion
    gives."""
    form, kernels = closed_form(stage), value_kernels(stage)
    k = np.asarray(k, dtype=float)
    return form.arrival_value(k) - kernels.arrival_value(form.value(kernels.resources(k)), k)


def euler_residual(stage, m, policy=None):
    """The relative residual of the Euler equation at the resources `m`,
    |1 - βR(Γc′/c)^(-ρ)|, with c the consumption at m and c′ the consumption
    at the next decision state m′ = R(m - c)/Γ + 1, which the laws of motion
    of the stage file give (`value_kernels`). The consumption is the closed
    form's, or `policy` where given. The formula is the normalized Euler
    equation of `economics.md`, a test reference."""
    form, kernels = closed_form(stage), value_kernels(stage)
    p = parameters(stage)
    consume = form.consumption if policy is None else policy
    m = np.asarray(m, dtype=float)
    c = np.asarray(consume(m), dtype=float)
    following = np.asarray(consume(kernels.resources(kernels.savings(m, c))), dtype=float)
    return np.abs(1 - p["β"] * p["R"] * (p["Γ"] * following / c) ** (-p["ρ"]))


def feasibility(stage, m, policy=None):
    """Whether consumption at the resources `m` lies in the feasible set of
    the stage file, 0 < c < m - L, for the closed form's consumption or for
    `policy` where given; one boolean per point."""
    form = closed_form(stage)
    m = np.asarray(m, dtype=float)
    c = np.asarray((form.consumption if policy is None else policy)(m), dtype=float)
    return (c > 0) & (c < m - form.limit)


def present_value_budget(stage, m, periods):
    """The present-value budget of the closed form from the resources `m`
    over `periods` periods, through the compiled kernels: the consumption
    path the closed form chooses along the stage file's laws of motion,
    discounted to the first period in units of its permanent income,
    `present_value` = Σ (Γ/R)^n c_n, the total wealth `total_wealth` = m - L,
    and `remainder` = (Γ/R)^N (m_N - L), the present value of the total
    wealth left after the last period. The budget holds where the present
    value and the remainder sum to total wealth, and the closed form
    consumes all of it in the limit where the remainder tends to zero; its
    ratio to total wealth is q^N, the patience factor to the power N."""
    form, kernels = closed_form(stage), value_kernels(stage)
    p = parameters(stage)
    discount = p["Γ"] / p["R"]
    m = np.asarray(m, dtype=float)
    total = m - form.limit
    present = np.zeros_like(m)
    resources = m
    for n in range(periods):
        c = form.consumption(resources)
        present = present + discount**n * c
        resources = kernels.resources(kernels.savings(resources, c))
    return SimpleNamespace(
        present_value=present,
        total_wealth=total,
        remainder=discount**periods * (resources - form.limit),
        periods=periods,
    )


# --- the test references ---


def reference_coefficients(p):
    """The coefficients of the closed form from the four parameters `p`,
    derived in `economics.md`: the return patience factor q = (βR)^(1/ρ)/R,
    the marginal propensity to consume κ = 1 - q, human wealth
    h = 1/(1 - Γ/R) and the natural borrowing limit L = 1 - h. A test
    reference."""
    q = (p["β"] * p["R"]) ** (1 / p["ρ"]) / p["R"]
    h = 1 / (1 - p["Γ"] / p["R"])
    return SimpleNamespace(q=q, κ=1 - q, h=h, L=1 - h)


def reference_consumption(p, m):
    """The consumption function κ(m - L), a test reference."""
    held = reference_coefficients(p)
    return held.κ * (np.asarray(m, dtype=float) - held.L)


def reference_value(p, m):
    """The decision value κ^(-ρ) w^(1-ρ)/(1-ρ), w = m - L, a test
    reference."""
    held, ρ = reference_coefficients(p), p["ρ"]
    return held.κ ** (-ρ) * (np.asarray(m, dtype=float) - held.L) ** (1 - ρ) / (1 - ρ)


def reference_arrival_value(p, k):
    """The arrival value Γ^(1-ρ) v(Rk/Γ + 1), the decision value at the
    resources the law of motion gives, normalized by Γ^(1-ρ); a test
    reference."""
    k = np.asarray(k, dtype=float)
    return p["Γ"] ** (1 - p["ρ"]) * reference_value(p, p["R"] * k / p["Γ"] + 1)


def reference_arrival_marginal(p, k):
    """The derivative of the arrival value, RΓ^(-ρ) v′(Rk/Γ + 1), with
    v′(m) = c(m)^(-ρ) by the envelope condition; a test reference."""
    k = np.asarray(k, dtype=float)
    following = reference_consumption(p, p["R"] * k / p["Γ"] + 1)
    return p["R"] * p["Γ"] ** (-p["ρ"]) * following ** (-p["ρ"])


def reference_curvature(p, x, arrival=False):
    """The absolute second derivative of the decision value,
    ρκ^(-ρ)(m - L)^(-ρ-1), or with `arrival` of the arrival value,
    ρR^(1-ρ)κ^(-ρ)(k - L)^(-ρ-1); a test reference."""
    held, ρ = reference_coefficients(p), p["ρ"]
    x = np.asarray(x, dtype=float)
    scale = p["R"] ** (1 - ρ) if arrival else 1.0
    return ρ * scale * held.κ ** (-ρ) * (x - held.L) ** (-ρ - 1)


# --- the scalar evaluators ---


class Derivative(NamedTuple):
    """One derivative a scalar evaluator offers: `coordinate`, the name of
    its one input; `order`; `shape`, the shape of one value, `()` for a
    scalar; and `region`, the sentence that says where the derivative is
    evaluated and where it may jump."""

    coordinate: str
    order: int
    shape: tuple
    region: str


class Evaluated(NamedTuple):
    """The values of a Linear evaluator with the endpoint-secant extension:
    `values`, one per point; `interpolated`, the number of points inside the
    closed node interval; and `extrapolated`, the number outside it, each
    read by the extension, which this record reports at each use."""

    values: np.ndarray
    interpolated: int
    extrapolated: int


class EndpointSecant(NamedTuple):
    """The endpoint-secant extension of a Linear evaluator of the
    consumption function, which only the policy comparison and an explicit
    request of the fixed point's `evaluate` select (AMD-MT-003 build
    contract §4): beyond the first or the last node the
    evaluator continues the secant of the first or the last interval. It is
    restricted to the economic domain m > `limit`, the natural borrowing
    limit L, and each extended value is checked finite and feasible,
    0 < c < m - L; a point outside the domain and a value that is not finite
    or not feasible are refused. It supplies no claim of accuracy."""

    limit: float


def _array(name, data):
    """`data` as a one-dimensional array: a NumPy array as it is, and any
    other sequence as an array of its entries as given, so that no entry is
    converted before it is checked; refused where it is not one-dimensional."""
    if isinstance(data, (str, bytes)):
        raise ValueError(f"the {name} are a one-dimensional sequence of numbers, not {data!r}")
    held = data if isinstance(data, np.ndarray) else np.asarray(list(data), dtype=object)
    if held.ndim != 1:
        raise ValueError(
            f"the {name} are a one-dimensional sequence of numbers, one per node; their shape "
            f"is {held.shape}"
        )
    return held


def _real_and_finite(name, held):
    """Refuse an entry of `held` that is not a finite real number."""
    if held.dtype == object:
        for position, entry in enumerate(held):
            if isinstance(entry, bool) or not isinstance(
                entry, (int, float, np.integer, np.floating)
            ):
                raise ValueError(
                    f"the {name} {entry!r} at position {position} is not a real number"
                )
            if not math.isfinite(entry):
                raise ValueError(f"the {name} {entry!r} at position {position} is not finite")
        return
    if held.dtype == bool or not (
        np.issubdtype(held.dtype, np.integer) or np.issubdtype(held.dtype, np.floating)
    ):
        raise ValueError(f"the {name} are {held.dtype} numbers, not real numbers")
    bad = np.flatnonzero(~np.isfinite(held))
    if bad.size:
        raise ValueError(f"the {name} {_shown(held[bad[0]])} at position {bad[0]} is not finite")


def _checked(word, nodes, values):
    """The nodes and values of a scalar evaluator as two arrays of floating
    point numbers, refused unless there are at least two nodes, each a
    finite real number, in strictly increasing order, with one finite real
    value aligned with each node; nothing is sorted, merged or broadcast. A
    conversion of the nodes to floating point is checked against the nodes
    as given, by `supports_equal`, and refused where it merges two distinct
    nodes."""
    nodes, values = _array("nodes", nodes), _array("values", values)
    if nodes.size < 2:
        raise ValueError(f"!{word} needs at least two nodes; it is given {nodes.size}")
    if values.size != nodes.size:
        raise ValueError(
            f"!{word} reads one value aligned with each node, and it is given {values.size} "
            f"values for {nodes.size} nodes; nothing is broadcast"
        )
    _real_and_finite("node", nodes)
    _real_and_finite("value", values)
    if nodes.dtype == object:
        failing = [n for n in range(nodes.size - 1) if not nodes[n] < nodes[n + 1]]
    else:
        failing = np.flatnonzero(~(nodes[1:] > nodes[:-1])).tolist()
    if failing:
        position = failing[0] + 1
        raise ValueError(
            f"!{word} reads strictly increasing nodes, and the node {_shown(nodes[position])} at "
            f"position {position} does not exceed the node {_shown(nodes[position - 1])} before "
            "it; nodes are neither sorted nor merged"
        )
    converted = nodes.astype(float)
    if (
        nodes.dtype != np.float64
        and not supports_equal(list(nodes), converted)
        and not np.all(np.diff(converted) > 0)
    ):
        raise ValueError(
            f"the conversion of the nodes of !{word} to floating point merges distinct nodes, "
            f"{nodes.size} nodes becoming {np.unique(converted).size}; preparation refuses a "
            "conversion that merges nodes"
        )
    return converted, values.astype(float)


class _Scalar:
    """The data and the checks a scalar evaluator shares."""

    word = None
    derivative_orders = ()

    def __init__(self, nodes, values, coordinate="x"):
        self.nodes, self.values = _checked(self.word, nodes, values)
        self.coordinate = coordinate

    def __repr__(self):
        return (
            f"!{self.word} on {self.coordinate} with {self.nodes.size} nodes from "
            f"{_shown(self.nodes[0])} to {_shown(self.nodes[-1])}"
        )

    def _inside(self, points, what):
        """`points` as an array of floating point numbers, refused where any
        is not finite or lies outside the closed node interval."""
        points = np.asarray(points, dtype=float)
        lower, upper = self.nodes[0], self.nodes[-1]
        outside = points[~((points >= lower) & (points <= upper))]
        if outside.size:
            raise ValueError(
                f"!{self.word} {what} at {self.coordinate} = {_shown(outside.flat[0])}, which "
                f"lies outside the closed node interval [{_shown(lower)}, {_shown(upper)}]; "
                f"{self._outside}"
            )
        return points

    def _interval(self, points):
        """The index of the interval that holds each point, the intervals
        closed on the left and open on the right and the last closed on both
        sides."""
        return np.clip(
            np.searchsorted(self.nodes, points, side="right") - 1, 0, self.nodes.size - 2
        )

    def __call__(self, points):
        """The evaluator at `points`, which lie in the closed node
        interval."""
        return self._evaluate(self._inside(points, "is evaluated"))

    def derivative(self, points, order=1):
        """The derivative of order `order` at `points`, which lie in the
        closed node interval, as the record of `derivatives` states it; an
        order the evaluator does not offer is refused. This is the
        derivative of the representation, distinct from a marginal value the
        author states in a stage file."""
        if order not in self.derivative_orders:
            raise ValueError(
                f"!{self.word} offers the derivatives of orders "
                f"{', '.join(str(n) for n in self.derivative_orders)}, and order {order} is asked"
            )
        return self._derivative(self._inside(points, "is differentiated"), order)

    @property
    def derivatives(self):
        """The `Derivative` record of each order the evaluator offers."""
        return tuple(
            Derivative(self.coordinate, order, (), self._regions[order])
            for order in self.derivative_orders
        )


class Linear(_Scalar):
    """Continuous piecewise linear interpolation of a function of one real
    coordinate through at least two strictly increasing finite nodes and the
    finite values aligned with them (build contract §4). It refuses a point
    outside the closed node interval; only the policy comparison and an
    explicit request of the fixed point's `evaluate` may select the
    endpoint-secant extension (`extend`). Its first derivative is the
    slope of each interval."""

    word = "Linear"
    derivative_orders = (1,)
    _regions = {
        1: (
            "the slope of the interval that holds the point, the intervals closed on the left "
            "and open on the right and the last closed on both sides; the slopes of two "
            "adjacent intervals need not agree at their common node"
        ),
    }
    _outside = (
        "Linear refuses evaluation outside it, and only the policy comparison or an "
        "explicit request may select the endpoint-secant extension"
    )

    def _evaluate(self, points):
        return np.interp(points, self.nodes, self.values)

    def _slopes(self):
        return np.diff(self.values) / np.diff(self.nodes)

    def _derivative(self, points, order):
        return self._slopes()[self._interval(points)]

    def extend(self, points, extension):
        """The evaluator at `points` with the endpoint-secant extension
        `extension`, an `EndpointSecant`, beyond the node interval: a point
        at or below its limit is refused, and so is an extended value that
        is not finite or not feasible. The answer, an `Evaluated` record,
        reports how many points were interpolated and how many extended."""
        if not isinstance(extension, EndpointSecant):
            raise TypeError("the extension of a Linear evaluator is an EndpointSecant record")
        points = np.asarray(points, dtype=float)
        low = points[~(points > extension.limit)]
        if low.size:
            raise ValueError(
                f"the endpoint-secant extension is restricted to the economic domain "
                f"{self.coordinate} > L = {_shown(extension.limit)}, and the point "
                f"{self.coordinate} = {_shown(low.flat[0])} lies outside it"
            )
        lower, upper = self.nodes[0], self.nodes[-1]
        below, above = points < lower, points > upper
        slopes = self._slopes()
        values = np.interp(points, self.nodes, self.values)
        values = np.where(below, self.values[0] + (points - lower) * slopes[0], values)
        values = np.where(above, self.values[-1] + (points - upper) * slopes[-1], values)
        extended = below | above
        if extended.any():
            reached, at = values[extended], points[extended]
            bad = ~(np.isfinite(reached) & (reached > 0) & (reached < at - extension.limit))
            if bad.any():
                raise ValueError(
                    f"the endpoint-secant extension gives c = {_shown(reached[bad][0])} at "
                    f"{self.coordinate} = {_shown(at[bad][0])}, which is not a finite consumption "
                    f"in the feasible set 0 < c < {self.coordinate} - L = "
                    f"{_shown(at[bad][0] - extension.limit)}; an extrapolation that leaves the "
                    "feasible set is refused"
                )
        return Evaluated(values, int((~extended).sum()), int(extended.sum()))


class Pchip(_Scalar):
    """Piecewise cubic Hermite interpolation of a function of one real
    coordinate with the shape-preserving slopes of PCHIP, as SciPy's
    `PchipInterpolator` defines them: at an interior node the weighted
    harmonic mean of the two adjacent secants, zero where they differ in
    sign or one is zero; at an end node the one-sided three-point estimate,
    set to zero where its sign differs from the end secant's and to three
    times that secant where the two end secants differ in sign and the
    estimate exceeds it threefold; with two nodes, the one secant. The cubic
    of each interval is written in powers of the distance from its left
    node, as SciPy's `CubicHermiteSpline` writes it. Evaluation outside the
    closed node interval is refused, extrapolation included."""

    word = "pchip"
    derivative_orders = (1, 2)
    _regions = {
        1: (
            "continuous on the closed node interval; at a node it is the slope the PCHIP rule "
            "assigns there"
        ),
        2: (
            "the second derivative of the cubic of the interval that holds the point, the "
            "intervals closed on the left and open on the right and the last closed on both "
            "sides; the second derivatives of two adjacent cubics need not agree at their "
            "common node"
        ),
    }
    _outside = "PCHIP extrapolation is refused"

    def __init__(self, nodes, values, coordinate="x"):
        super().__init__(nodes, values, coordinate)
        self.slopes = _pchip_slopes(self.nodes, self.values)
        widths = np.diff(self.nodes)
        secants = np.diff(self.values) / widths
        bend = (self.slopes[:-1] + self.slopes[1:] - 2 * secants) / widths
        self.coefficients = np.array(
            [
                bend / widths,
                (secants - self.slopes[:-1]) / widths - bend,
                self.slopes[:-1],
                self.values[:-1],
            ]
        )

    def _local(self, points):
        index = self._interval(points)
        return index, points - self.nodes[index]

    def _evaluate(self, points):
        index, s = self._local(points)
        c = self.coefficients[:, index]
        return ((c[0] * s + c[1]) * s + c[2]) * s + c[3]

    def _derivative(self, points, order):
        index, s = self._local(points)
        c = self.coefficients[:, index]
        if order == 1:
            return (3 * c[0] * s + 2 * c[1]) * s + c[2]
        return 6 * c[0] * s + 2 * c[1]


def _pchip_end_slope(h0, h1, m0, m1):
    """The slope PCHIP assigns at an end node, from the widths `h0` and `h1`
    and the secants `m0` and `m1` of the two intervals nearest it: the
    one-sided three-point estimate, zero where its sign differs from that of
    `m0`, and 3·m0 where `m0` and `m1` differ in sign and the estimate
    exceeds 3|m0|."""
    estimate = ((2 * h0 + h1) * m0 - h0 * m1) / (h0 + h1)
    if np.sign(estimate) != np.sign(m0):
        return 0.0
    if np.sign(m0) != np.sign(m1) and abs(estimate) > 3 * abs(m0):
        return 3.0 * m0
    return estimate


def _pchip_slopes(nodes, values):
    """The slopes PCHIP assigns at the nodes."""
    widths = np.diff(nodes)
    secants = np.diff(values) / widths
    if nodes.size == 2:
        return np.array([secants[0], secants[0]])
    slopes = np.zeros_like(values)
    left, right = secants[:-1], secants[1:]
    flat = (np.sign(left) != np.sign(right)) | (left == 0) | (right == 0)
    w1 = 2 * widths[1:] + widths[:-1]
    w2 = widths[1:] + 2 * widths[:-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        harmonic = (w1 / left + w2 / right) / (w1 + w2)
    slopes[1:-1] = np.where(flat, 0.0, 1.0 / np.where(flat, 1.0, harmonic))
    slopes[0] = _pchip_end_slope(widths[0], widths[1], secants[0], secants[1])
    slopes[-1] = _pchip_end_slope(widths[-1], widths[-2], secants[-1], secants[-2])
    return slopes


# the evaluator of each base family this module supplies, by its word
EVALUATORS = {"Linear": Linear, "pchip": Pchip}


# --- the gridded route ---


def interpolate(m, knots, values):
    """The piecewise linear interpolant of the pairs (`knots`, `values`) at
    `m`, its end segments extended linearly beyond the first and the last
    pair, as HARK's linear interpolant extrapolates; `numpy.interp` holds
    the end values instead. The extension is not checked: the routes of this
    module read the Linear evaluator, which refuses a point outside its
    pairs, and the checked endpoint-secant extension (`EndpointSecant`)."""
    m = np.asarray(m, dtype=float)
    knots, values = np.asarray(knots, dtype=float), np.asarray(values, dtype=float)
    inside = np.interp(m, knots, values)
    below = values[0] + (m - knots[0]) * (values[1] - values[0]) / (knots[1] - knots[0])
    above = values[-1] + (m - knots[-1]) * (values[-1] - values[-2]) / (knots[-1] - knots[-2])
    return np.where(m < knots[0], below, np.where(m > knots[-1], above, inside))


def _exact_grid(stage, address, inputs=None):
    """The realized grid of the place `address` of `stage`, from the
    `kernels()` record of the builder that holds the place, whose points are
    exact; refused where construction could not establish it or where it has
    another number of coordinates. A comparison with the grid reads these
    exact points, before any conversion."""
    inputs = stationary_inputs(stage) if inputs is None else inputs
    stage.check_inputs(inputs)
    record = stage.builder[BUILDERS[address.split(".", 1)[0]]].kernels(inputs=inputs)
    grid = (record.grids or {}).get(address)
    if grid is None:
        raise ValueError(f"the place {address!r} has no realized grid at the bound settings")
    if not hasattr(grid, "points"):
        raise ValueError(f"the grid of {address!r} is not constructed: {grid.reason}")
    if len(grid.coordinates) != 1:
        raise ValueError(
            f"the grid of {address!r} lies on ({', '.join(grid.coordinates)}), and the scalar "
            "evaluators read one coordinate"
        )
    return grid


def _realized(stage, address, inputs=None):
    """The realized grid of the place `address` of `stage` (`_exact_grid`)
    and the array of the nearest floating-point numbers of its exact points,
    at which an evaluator is built or a family's own nodes are sampled. The
    conversion is refused where two distinct exact nodes have the same
    nearest floating-point number, since numerical preparation refuses a
    conversion that merges distinct nodes (AMD-MT-003 build contract §4), and
    where an exact node exceeds the largest finite floating-point number."""
    grid = _exact_grid(stage, address, inputs=inputs)
    (name,) = grid.coordinates
    converted = {}
    for (node,) in grid.points:
        try:
            nearest = float(node)
        except OverflowError:
            raise ValueError(
                f"the grid of {address!r} holds the exact node {name} = {node!s}, which exceeds "
                "the largest finite floating-point number; numerical preparation converts the "
                "exact nodes of a grid to floating-point numbers and refuses a node it cannot "
                "convert"
            ) from None
        first = converted.setdefault(nearest, node)
        if first != node:
            raise ValueError(
                f"the grid of {address!r} holds the distinct exact nodes {name} = {first!s} and "
                f"{name} = {node!s}, whose nearest floating-point number is the same, "
                f"{nearest!r}; numerical preparation converts the exact nodes of a grid to "
                "floating-point numbers and refuses a conversion that merges distinct nodes"
            )
    return grid, np.array(list(converted), dtype=float)


def _exact(value):
    """A finite real number as the `Fraction` it equals, read exactly."""
    if isinstance(value, numbers.Integral):
        return Fraction(int(value))
    return Fraction(*value.as_integer_ratio())


def _exactly_shown(value):
    """An exact number as a sentence writes it: its floating-point number
    where that equals it, and otherwise its ratio with its nearest
    floating-point number."""
    nearest = float(value)
    if Fraction(nearest) == value:
        return repr(nearest)
    return f"{value} (nearest floating-point number {nearest!r})"


def _first_difference(points, knots):
    """The first node, in increasing order, at which the exact support of a
    realized grid of one coordinate and the knots of a table, each read
    exactly, differ, as a sentence names the two nodes; None where the two
    supports are equal."""
    nodes = sorted({_exact(point[0]) for point in points})
    held = sorted({_exact(knot) for knot in knots})
    for node, knot in itertools.zip_longest(nodes, held):
        if node != knot:
            return (
                ("no node" if node is None else f"the node {_exactly_shown(node)}")
                + " of the grid and "
                + ("no knot" if knot is None else f"the knot {_exactly_shown(knot)}")
                + " of the table"
            )
    return None


def gridded_route(stage, tolerance=1e-12, iterations=10_000, initial=None):
    """The endogenous grid method of the gridded variant iterated to its
    fixed point on the stage's compiled kernels. The grid of savings is the
    realized grid of the policy builder (`kernels().grids`). At each saving
    the policy block's kernel gives the candidate consumption and the
    resources it is chosen at, from the marginal continuation value; that
    value is the compiled marginal of the arrival value, R Γ^(-ρ) D_{m}V,
    read at the compiled envelope condition D_{m}V = c^(-ρ) of the decision
    value, at the resources the law of motion gives and the consumption of
    the previous iterate there. The previous iterate is the Linear
    interpolant of its pairs with the endpoint-secant extension, which the
    route reports at each use.

    Human wealth is iterated with the consumption function, as a solution
    computed by backward steps requires (CDC's scope of DR-0981, 14 November
    2026): each step uses only what the step after it provides. The step
    after hands back h[<] = h*Γ/R, with h = 1 + h[>] there, through the
    compiled lines `human_wealth` of the stage's two value builders, and that
    value is the step's own h[>]; the first iterate takes in h[>] = 0, the
    value that the last period takes in. Each step's natural borrowing limit
    is L = -h[>], and it solves at the savings of the grid above its own L,
    which map into resources above the limit of the step after it; the
    lower savings join as h[>] rises. The limit of human wealth,
    1/(1 - Γ/R) - 1, is read only to refuse a grid of savings that starts at
    or below the limit of the infinite horizon.

    The first iterate consumes half of total wealth, c = (m - L)/2 with
    L = 0, feasible at every level of resources above that limit, unless
    `initial` gives its pairs (knots, consumption). The pairs of each iterate
    are feasible, 0 < c < m - L, ordered, since the endogenous grid of this
    model is strictly increasing and needs no selection among branches, and
    finite. The change of an iteration is read at its resources above the
    limit of the iterate before it. The route is refused where the return
    impatience condition q < 1 fails, where the natural borrowing limit L is
    not finite, where the exact first node of the grid of savings lies at or
    below the limit of the infinite horizon, where a step has fewer than two
    savings above its limit, where two distinct exact nodes of the grid have
    one nearest floating-point number (`_realized`), where an intermediate
    value is not finite, where the extension leaves the feasible set, and
    where `iterations` iterations end before the largest change of the
    consumption function and the change of human wealth both fall below
    `tolerance` with every saving of the grid in use.
    The stage file declares the return impatience condition as the upper
    bound of the discount factor and as the set (0, 1) of q, and `calibrate`
    refuses a calibration that breaks either; the route checks q all the
    same, since it reads q from the stage it is given, and under a
    definition of q without that set a discount factor one rounding step
    below the bound binds with q computed as one.

    Returns the pairs of the fixed point, `knots` and `consumption`, their
    Linear evaluator `policy`, the number of iterations, the last change,
    `extended`, the number of extended points at each iteration, the last
    step's inputs, its human wealth `human_wealth` (its h[>]) and its limit
    `limit`, and
    `evaluate(m, extrapolate=False)`, the consumption function at `m`: the
    linear interpolant between the pairs; a point outside them is refused
    unless `extrapolate` is true, and then the endpoint-secant extension
    gives it, restricted to m > L, each extended value checked finite and
    feasible, and each use reported by a warning that counts the
    interpolated and the extended points."""
    limiting = stationary_inputs(stage)
    q, limit = stage.par["q"].value, -limiting["h[>]"]
    if not q < 1:
        raise ValueError(
            f"the return patience factor q = (βR)^(1/ρ)/R is {q!r} at the calibration, and the "
            "endogenous grid iteration has an infinite-horizon fixed point only under the "
            "return impatience condition q < 1"
        )
    _finite("the natural borrowing limit L at the calibration", limit)
    grid, every_saving = _realized(stage, "policy", inputs=limiting)
    if grid.points[0][0] <= _exact(limit):
        raise ValueError(
            f"the grid of savings starts at a_min = {_shown(every_saving[0])}, at or below the "
            f"natural borrowing limit on savings, L = {limit!r}: from such a saving the law of "
            "motion gives resources at which no consumption is feasible, and the iteration "
            f"would stop at its tolerance on pairs that solve nothing; set a_min above {limit!r}"
        )
    # the last period takes in no human wealth; each step after the first
    # takes in what the step after it hands back
    p, taken = parameters(stage), 0.0
    inputs = {"V[>]": _continuation(p, taken), "h[>]": taken}
    conditions = stage.check_inputs(inputs)
    candidate = kernel_function(stage.builder.policy.kernels(inputs=inputs), "g_cntn_to_dcsn:Aggregation")
    decision = stage.builder["cntn", "dcsn"].kernels(inputs=inputs)
    envelope = kernel_function(decision, "marginal:Derivative:1")
    human = output_function(decision, "Aggregation", "h")
    arrival = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
    marginal = kernel_function(arrival, "marginal:Derivative:1")
    resources = kernel_function(arrival, "Pullback")
    handing = output_function(arrival, "Aggregation", "h")
    L = -taken
    first = every_saving[every_saving > L]
    knots, consumption = (2 * first - L, first - L) if initial is None else initial
    policy = Linear(knots, consumption, "m")
    extended, change, moved = [], math.inf, math.inf
    for count in range(1, iterations + 1):
        # the step after this one has h = 1 + h[>] and hands back
        # h[<] = h*Γ/R, by the stage's compiled lines; that is this step's
        # h[>], and its natural borrowing limit is L = -h[>]
        handed = float(handing(h=float(human(**{"h≻": taken}))))
        moved, taken = abs(handed - taken), handed
        before, L = L, -taken
        _finite(f"the natural borrowing limit L at iteration {count}", L)
        savings = every_saving[every_saving > L]
        if savings.size < 2:
            raise ValueError(
                f"at iteration {count} the natural borrowing limit is L = {L!r}, and "
                f"{savings.size} saving(s) of the grid lie above it; the step needs two"
            )
        m_next = resources(k=savings)
        found = policy.extend(m_next, EndpointSecant(before))
        # every intermediate value is checked below and refused where it is
        # not finite, so NumPy's warnings of overflow and of division by zero
        # are silenced here
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            decision_marginal = envelope(m=m_next, c=found.values)
            continuation = marginal(k=savings, **{"D_{m}(V)": decision_marginal})
            c_end, m_end = candidate(a=savings, **{"D_{a}(V≻)": continuation})
        _finite(f"the marginal value at iteration {count}", continuation)
        _finite(f"the candidate consumption at iteration {count}", c_end)
        _finite(f"the endogenous grid at iteration {count}", m_end)
        if not (np.all(c_end > 0) and np.all(np.diff(m_end) > 0)):
            raise ValueError(
                f"the pairs of iteration {count} are not feasible and ordered: the consumption "
                "is positive and the endogenous grid strictly increasing at a fixed point of "
                "this model"
            )
        following = Linear(m_end, c_end, "m")
        # the iterate before this one is read only above its own limit
        comparable = m_end > before
        previous = policy.extend(m_end[comparable], EndpointSecant(before))
        change = (
            float(np.max(np.abs(previous.values - c_end[comparable])))
            if comparable.any()
            else math.inf
        )
        extended.append(found.extrapolated + previous.extrapolated)
        policy = following
        if change < tolerance and moved < tolerance and savings.size == every_saving.size:
            break
    else:
        raise ValueError(
            f"the endogenous grid iteration stopped at its limit of iterations, {iterations}, "
            f"with the largest change of the consumption function {change!r} and the change "
            f"of human wealth {moved!r}, one or both above the tolerance {tolerance!r}; the "
            "pairs are not a fixed point"
        )
    extension = EndpointSecant(L)
    inputs = {"V[>]": _continuation(p, taken), "h[>]": taken}

    def evaluate(m, extrapolate=False):
        m = np.asarray(m, dtype=float)
        lower, upper = policy.nodes[0], policy.nodes[-1]
        if not extrapolate:
            outside = m[~((m >= lower) & (m <= upper))]
            if outside.size:
                raise ValueError(
                    f"the point m = {_shown(outside.flat[0])} lies outside the pairs of the fixed "
                    f"point, which span resources from {_shown(lower)} to {_shown(upper)}; the "
                    "linear interpolant is established between them, and "
                    "evaluate(m, extrapolate=True) applies the checked endpoint-secant extension "
                    "beyond them"
                )
            return policy(m)
        found = policy.extend(m, extension)
        if found.extrapolated:
            warnings.warn(
                f"the endpoint-secant extension gives {found.extrapolated} of the {m.size} points "
                f"beyond the pairs of the fixed point, which span resources from {_shown(lower)} "
                f"to {_shown(upper)}, and {found.interpolated} are interpolated; the extended "
                "values are finite and feasible, and they carry no claim of accuracy",
                stacklevel=2,
            )
        return found.values

    return SimpleNamespace(
        inputs=inputs,
        input_conditions=conditions,
        knots=policy.nodes,
        consumption=policy.values,
        policy=policy,
        evaluate=evaluate,
        iterations=count,
        change=change,
        extended=tuple(extended),
        human_wealth=taken,
        limit=L,
    )


def comparison(n_a, a_min, a_max, m, tolerance=1e-12, calibration=CALIBRATION):
    """The gridded route on a grid of `n_a` savings from `a_min` to `a_max`
    compared with the closed form at the resources `m`, on the stage bound
    from the folder's addition: the largest absolute difference between the
    two consumption functions there, the number of iterations, the route
    and the gridded stage it iterated on. The comparison alone selects the
    endpoint-secant extension of the route's policy, and reports how many of
    the points of `m` it interpolates and how many it extends. `calibration`
    is the folder's file unless another source is given, and binds both
    stages."""
    gridded = gridded_stage(n_a, a_min, a_max, calibration)
    route = gridded_route(gridded, tolerance)
    form = closed_form(closed_form_stage(calibration))
    m = np.asarray(m, dtype=float)
    found = route.policy.extend(m, EndpointSecant(route.limit))
    difference = float(np.max(np.abs(found.values - form.consumption(m))))
    return SimpleNamespace(
        n_a=n_a,
        iterations=route.iterations,
        difference=difference,
        route=route,
        gridded=gridded,
        interpolated=found.interpolated,
        extrapolated=found.extrapolated,
    )


# --- the accuracy checks ---


def evaluation_sample(lower, upper, count=1000):
    """A fixed sample of `count` points of the interval (lower, upper), the
    additive sequence of the golden ratio,
    `lower + (upper - lower) * frac(n/φ)` for n = 1, …, count: deterministic,
    spread over the interval and independent of any equally spaced nodes."""
    golden = (math.sqrt(5) - 1) / 2
    fractions = np.array([(n * golden) % 1.0 for n in range(1, count + 1)])
    return np.sort(lower + (upper - lower) * fractions)


def value_interpolation(stage, word, count, lower=-30.0, upper=50.0, sample=None):
    """The decision value and the arrival value of the closed form, each
    represented by the evaluator of the family `word`, `Linear` or `pchip`,
    on `count` equally spaced nodes from `lower` to `upper`, at which the
    compiled closed form is sampled, and compared with the compiled closed
    form on `sample`, the fixed sample of `evaluation_sample` unless another
    is given; every point of the sample interpolates, inside the node
    interval and on no node. For each value the record holds the largest
    off-node error, the node spacing Δ, the interpolation bound of Linear
    Δ² max|v″|/8 on the interval with the curvature of `reference_curvature`,
    and the rounding allowance, 64 times the machine epsilon times the
    largest absolute value at the nodes, for the rounding of the compiled
    values and of the interpolation."""
    form = closed_form(stage)
    p = parameters(stage)
    nodes = np.linspace(lower, upper, count)
    points = evaluation_sample(lower, upper) if sample is None else np.asarray(sample, dtype=float)
    if np.isin(points, nodes).any() or points.min() < lower or points.max() > upper:
        raise ValueError("the evaluation sample lies inside the node interval and on no node")
    found = {}
    for name, exact, arrival in (
        ("decision", form.value, False),
        ("arrival", form.arrival_value, True),
    ):
        values = exact(nodes)
        evaluator = EVALUATORS[word](nodes, values, "k" if arrival else "m")
        error = float(np.max(np.abs(evaluator(points) - exact(points))))
        spacing = float(np.max(np.diff(nodes)))
        curvature = float(np.max(reference_curvature(p, np.array([lower, upper]), arrival)))
        found[name] = SimpleNamespace(
            error=error,
            spacing=spacing,
            bound=spacing**2 * curvature / 8,
            allowance=64 * np.finfo(float).eps * float(np.max(np.abs(values))),
            interpolated=points.size,
            extrapolated=0,
        )
    return SimpleNamespace(word=word, count=count, **found)


def near_limit(closed, route, w):
    """The checks near the borrowing limit at the resources m = L + w, for
    the points of total wealth `w`, from the exact compiled values of the
    closed-form stage `closed` and the converged policy of `route`: the
    relative policy error |c - κw|/(κw) against the test reference; the
    relative Euler residual |1 - βR(Γc′/c)^(-ρ)|, c′ the converged policy at
    the next decision state; and the scaled Bellman residual
    |v(m) - 𝑢(c) - βV≺(m - c)|/(1 + |v(m)|), v and V≺ the compiled closed
    form. Every evaluation of the converged policy interpolates between its
    pairs; a point outside them is refused, since an extrapolation
    establishes no accuracy."""
    p = parameters(closed)
    held = reference_coefficients(p)
    form = closed_form(closed)
    w = np.asarray(w, dtype=float)
    m = form.limit + w
    c = route.policy(m)
    policy_error = np.abs(c - held.κ * w) / (held.κ * w)
    euler = euler_residual(closed, m, route.policy)
    bellman = np.abs(bellman_residual(closed, m, route.policy)) / (1 + np.abs(form.value(m)))
    return SimpleNamespace(
        policy_error=float(np.max(policy_error)),
        euler=float(np.max(euler)),
        bellman=float(np.max(bellman)),
        interpolated=w.size,
        extrapolated=0,
    )


# --- the preparation of a representation from its data source ---


class Prepared(NamedTuple):
    """A representation prepared for numerical use from its data source:
    `word`, the family's method word; `source`, its data source among the
    four of build contract §3; `nodes` and `values`, the data it stores,
    None for a closed form; and `evaluator`, the function that evaluates it,
    None for a family whose numerical procedure this module does not supply,
    which stores its values at its nodes alone."""

    word: str
    source: str
    nodes: object
    values: object
    evaluator: object


def _record(stage, address, source):
    """The method word of the representation typed at `address`, `!Linear`,
    refused where its method record selects another data source than
    `source`."""
    held = stage.methods[address]
    if held.source != source:
        raise ValueError(
            f"the representation at {address!r} reads the data source {held.source!r}, and this "
            f"preparation reads {source!r}; missing data never selects another source"
        )
    return held.word


def _evaluator(word):
    """The evaluator this module supplies for the method word `word`, or
    None for a family it supplies none for."""
    return EVALUATORS.get(word.lstrip("!"))


def prepare_expression(stage, address):
    """The closed form at the Evaluation `address` of an explicit builder,
    prepared from its authored expression: the compiled kernel of the
    builder's line (`closed_form`)."""
    word = _record(stage, address, "expression")
    form = closed_form(stage)
    functions = {
        "policy.evaluate": form.consumption,
        "cntn_to_dcsn.evaluate": form.value,
        "dcsn_to_arvl.evaluate": form.arrival_value,
    }
    return Prepared(word, "expression", None, None, functions[address])


def prepare_pairs(stage, address, route):
    """The representation at the closing Evaluation `address` of the `!egm`
    builder, prepared from the selected pairs of the endogenous grid method,
    the fixed point of `route`, by the family's evaluator."""
    word = _record(stage, address, "pairs")
    evaluator = _evaluator(word)(route.knots, route.consumption, "m")
    return Prepared(word, "pairs", evaluator.nodes, evaluator.values, evaluator)


def reconstruct(route, nodes):
    """The scalar Linear reconstruction of the consumption function from the
    feasible, branch-selected, ordered pairs of the endogenous grid method,
    the fixed point of `route`, sampled at `nodes`, the grid of the family
    that is prepared from it (build contract §3); a node outside the
    interval of the pairs is refused, since no extension is selected."""
    return route.policy(np.asarray(nodes, dtype=float))


def prepare_own_nodes(stage, address, function):
    """The representation at `address` prepared from its own nodes: the
    realized grid of the place (`kernels().grids`), at whose nodes
    `function` is sampled, such as the compiled closed form or, at the
    closing Evaluation of an `!egm` builder, the reconstruction of the
    selected pairs (`reconstruct`); then the family's evaluator, or for a
    family whose procedure this module does not supply its values at its
    nodes alone. The nodes are the nearest floating-point numbers of the
    grid's exact points, and preparation is refused where that conversion
    merges two distinct nodes (`_realized`)."""
    word = _record(stage, address, "own nodes")
    _, nodes = _realized(stage, address)
    values = _finite(f"the values sampled on the grid of {address!r}", function(nodes))
    family = _evaluator(word)
    evaluator = None if family is None else family(nodes, values)
    return Prepared(word, "own nodes", nodes, values, evaluator)


def prepare_table(stage, address, knots, values):
    """The representation of the authored table `evaluate(knots, values, x)`
    at `address`, its knots and values the parameters named `knots` and
    `values` at the calibration, or the sequences given where a table reads
    runtime inputs. Where the place types a grid, the exact points of its
    realized grid are compared with the table's knots, each read exactly, by
    `supports_equal` before any conversion and before the evaluator is
    built, with no sorting, resampling or tolerance, and a difference is
    refused with the first node at which the two supports differ; the
    evaluator is then built from the table's own knots and values, whose
    order and alignment are kept."""
    word = _record(stage, address, "table")
    knots = stage.par[knots].value if isinstance(knots, str) else knots
    values = stage.par[values].value if isinstance(values, str) else values
    if stage.methods[address].grid is not None:
        grid = _exact_grid(stage, address)
        if not supports_equal(knots, grid.points):
            raise ValueError(
                f"the grid of {address!r} and the authored table with the knots {tuple(knots)} "
                f"first differ at {_first_difference(grid.points, knots)}, both read exactly; an "
                "optional grid beside a table has exactly the table's finite support, compared "
                "with no tolerance before the evaluator is built"
            )
    evaluator = _evaluator(word)(knots, values)
    return Prepared(word, "table", evaluator.nodes, evaluator.values, evaluator)
