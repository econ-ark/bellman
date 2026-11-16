"""The numerical tool of the portfolio-consumption model, the four stage files of applications/cons-port/.

This module belongs to that application and not to the package: it realizes the stage occurrences of a
specified trellis and solves the trellis period by period. Every equation it evaluates is a kernel the package
compiles from a stage file and the methods file added to it, taken from the record a builder's `kernels()`
answers and called with the parameter values the record holds; the endogenous-grid operator is one call of
asva's `egm` on two such records, the decision builder's without the piece of the stated derivative, which the
tool evaluates itself, and no operator reads the stage once it is made. `stage_operator` checks the complete
supplied input mapping before constructing kernels, grids or numerical operators. Grids, feasible factors
and calibrated probability laws come from the detached kernel records. Node counts come from the bound
quadrature selection at construction. Unresolved input conditions remain on the operator and its results.
Among realizations it chooses only by the handler a methods file names, and it refuses a handler
it does not realize. It replaces ffp_utils.py for the notebooks, which stays as a recorded source of the fixed
reference.

`hermite_nodes` and `normal_nodes` follow `hermgauss` and `gauss_hermite_nodes` of dolo 0.4.9
(dolo/numeric/discretization/quadrature.py, ported there from the CompEcon toolbox of Miranda and Fackler),
which the fixed reference used through `Normal.discretize`; `reference_normal_nodes` adds the mean of the
logarithms once more, as that library did in two or more dimensions. The explicitly named historical share
handler retains its finite floor. Ordinary share maximization accepts every finite objective value.
Consumption search uses a 1e-6 inset, capped at 1e-6 of the feasible interval's width.
"""
from __future__ import annotations

import itertools
from collections.abc import Mapping
from functools import reduce
from types import SimpleNamespace

import asva
import matplotlib.pyplot as plt
import numpy as np

from bellman.period import backward_order, period_joins
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.trellis import inter_period_joins
from bellman.distributions.families import numeric_value
from bellman.stage.grids import (RealizedGrid, SpacedGridFactor, FeasibleGridFactor,
                                 check_grid_factor_points, feasible_interval)

# the value where consumption is not positive, and the marginal value there (ffp_utils.py lines 753 and 760)
LOW, HIGH = -1e10, 1e10


class ValueFn:
    """A value function on a one-dimensional grid, with its marginal values and the policy arrays of the stage
    that produced it. Called at points it interpolates linearly and holds the end values beyond the grid."""

    def __init__(self, grid, values, dvalues=None, policy=None, input_conditions=()):
        self.grid, self.values = np.asarray(grid), np.asarray(values)
        self.dvalues = None if dvalues is None else np.asarray(dvalues)
        self.policy = dict(policy or {})
        self.input_conditions = tuple(input_conditions)

    def __call__(self, x):
        return np.interp(x, self.grid, self.values)

    def dV(self, x):
        """The marginal value at `x`: the held marginal values interpolated, or the difference quotient of the
        values where none are held."""
        return np.interp(x, self.grid, np.gradient(self.values, self.grid) if self.dvalues is None else self.dvalues)

    def __repr__(self):
        return f"ValueFn(n={len(self.grid)}, range=[{self.values.min():.4g}, {self.values.max():.4g}])"


def expmult_grid(maximum, size, nestings=20):
    """`size` points on (0, maximum] whose growth rate from one point to the next is constant after `nestings`
    applications of log(· + 1): the multi-exponential grid of SolvingMicroDSOPs. The body is that of
    `_expmult_grid` in ffp_utils.py lines 67 to 85, unchanged but for the parameter names."""
    g = float(maximum)
    for _ in range(int(nestings)):
        g = np.log(g + 1.0)
    index = g / float(size)
    points = np.empty(int(size))
    point = g
    for j in range(1, int(size) + 1):
        points[size - j] = np.exp(point) - 1.0
        point = point - index
        for _ in range(2, int(nestings) + 1):
            points[size - j] = np.exp(points[size - j]) - 1.0
    return points


# the place of the representation of the decision value, the Evaluation of the backward decision builder
EVALUATION = "cntn_to_dcsn.evaluate"
# the places of a method that solves a stage's policy: a solution method on the policy builder, `!egm` or
# `!time_iteration`, and `!vfi` on the backward decision builder
POLICY_PLACES = ("policy", "cntn_to_dcsn")
# the ids of the line that states the derivative of the decision value: `envelope` in the methods files of
# applications/cons-port, `marginal` in the stage files of applications/portfolio-choice
MARGINAL_LINES = ("envelope", "marginal")


def method_at(stage, place):
    """The components bound at `place` of the stage occurrence, a place as its methods table prints it: the
    method word with its keyword arguments, the grid and the handler."""
    held = {str(key): method for key, method in stage.methods.items()}
    if place not in held:
        raise ValueError(f"stage {stage.name!r} binds no method at {place!r}; its methods stand at {', '.join(sorted(held))}")
    return held[place]


def expectation_place(stage):
    """The place of the expectation of the backward decision builder, `cntn_to_dcsn.E_<shocks>`, the one
    operator of that block whose head begins with `E_`; None where the stage binds none."""
    found = [str(key) for key in stage.methods
             if str(key).startswith("cntn_to_dcsn.") and str(key).rpartition(".")[2].startswith("E_")]
    if len(found) > 1:
        raise ValueError(f"stage {stage.name!r} binds a method at {len(found)} expectations of cntn_to_dcsn, "
                         f"{', '.join(sorted(found))}; this tool reads one")
    return found[0] if found else None


def setting(stage, argument):
    """The number an argument of a grid factor or of a method word stands for: a literal is its own value, and
    a name is read in the stage occurrence's settings. Any other argument, a quoted string, a tuple or a nested
    word, is refused by name."""
    if isinstance(argument, T.Literal):
        return argument.value
    if isinstance(argument, T.Name):
        return stage.bindings.settings[argument.name]
    written = to_source(argument) if isinstance(argument, T.argument) else repr(argument)
    raise ValueError(f"stage {stage.name!r}: the argument {written} is no number and no setting's name; this tool "
                     "reads a literal or the name of a setting")


def keyword_arguments(method):
    """The keyword arguments of a place's method word, `{key: argument}`, as `!gauss_hermite(n_Ψ=n_Ψ_nodes)`
    writes them."""
    return {keyword.key: keyword.value for keyword in method.method.arguments}


def cartesian_points(record, address):
    """Numerical points from a detached realized grid or spacing factor."""
    grid = (record.grids or {}).get(address)
    if isinstance(grid, RealizedGrid):
        if len(grid.coordinates) != 1:
            raise ValueError(f"The grid at {address} must have one coordinate.")
        exact = tuple(row[0] for row in grid.points)
        # The saved reference uses NumPy's floating-point construction of a
        # uniform grid. Its endpoints and count come from this detached record.
        uniform = len(exact) > 1 and all(right - left == exact[1] - exact[0]
                                        for left, right in zip(exact, exact[1:]))
        points = (np.linspace(float(exact[0]), float(exact[-1]), len(exact)) if uniform
                  else np.array([float(point) for point in exact]))
        if np.any(np.diff(points) <= 0):
            raise ValueError(f"Floating-point conversion merges grid points at {address}.")
        return points
    factor = (record.grid_factors or {}).get(address)
    if not isinstance(factor, SpacedGridFactor):
        raise ValueError(f"No supported detached spacing factor at {address}: {grid}")
    if factor.spacing != "expmult" or factor.options:
        raise ValueError(f"Unsupported spacing !{factor.spacing} with options {factor.options}; this tool realizes !expmult without options.")
    points = float(factor.lower) + expmult_grid(float(factor.upper - factor.lower), factor.count)
    # Repeated logarithms and exponentials can overshoot the declared bound.
    # The upper endpoint is authored data and is represented exactly here.
    points[-1] = float(factor.upper)
    check_grid_factor_points(factor, points)
    return points


def feasible_points(factor, at, *, inset=0.0, cache=None):
    """Checked candidate points inside a detached feasible interval."""
    if not isinstance(factor, FeasibleGridFactor):
        raise ValueError("The search requires a detached feasible grid factor.")
    bounds = feasible_interval(factor, at)
    # This cache belongs to one factor. Every state is checked above; equal
    # exact bounds give the same candidates and point-domain requirements.
    key = (*bounds, inset)
    if cache is not None and key in cache:
        return cache[key]
    low, left_closed, high, right_closed = bounds
    low, high = float(low), float(high)
    # Preserve the reference's 1e-6 inset on intervals of width at least one.
    # Narrow intervals use the same relative inset, so their endpoints stay ordered.
    margin = min(inset, (high - low) * inset)
    lower = low + margin if margin else (low if left_closed else np.nextafter(low, high))
    upper = high - margin if margin else (high if right_closed else np.nextafter(high, low))
    points = np.linspace(lower, upper, factor.count)
    check_grid_factor_points(factor, points, at=at)
    if cache is not None:
        points.setflags(write=False)
        cache[key] = points
    return points


def evaluation_grid(record):
    """The detached grid of the decision value's representation."""
    return cartesian_points(record, EVALUATION)


def savings_grid(record):
    """The detached savings grid of the endogenous-grid policy builder."""
    return cartesian_points(record, "policy")


def lognormal_law(record):
    """The selected joint lognormal law, with its already bound parameters."""
    expected = [piece.key for piece in record.pieces if piece.kind == "Expectation"]
    if len(expected) != 1:
        raise ValueError("The numerical rule requires one expectation of a joint law.")
    law = (record.laws or {}).get(expected[0])
    if law is None or not hasattr(law, "edge") or law.given or len(law.edge.declarations) != 1:
        raise ValueError(f"The numerical rule requires one unconditional law: {law}")
    owner, = law.edge.declarations
    if owner.term.fun != "LogNormal" or tuple(law.integrated) != tuple(owner.subjects):
        raise ValueError("The numerical rule integrates the whole declared lognormal vector.")
    location, scale = owner.term.args
    if len(owner.subjects) == 1:
        return owner.subjects, np.array([numeric_value(location, {})]), np.array([[numeric_value(scale, {}) ** 2]])
    return (owner.subjects, np.array([numeric_value(item, {}) for item in location.items]),
            np.array([[numeric_value(entry, {}) for entry in row.items] for row in scale.items]))


def hermite_nodes(n):
    """Nodes and weights of n-point Gauss-Hermite quadrature for the standard normal distribution: the CompEcon
    routine's roots by Newton's iteration, the nodes scaled by √2 and the weights by 1/√π."""
    pim4, m = 1 / np.pi ** 0.25, int(np.fix((n + 1) / 2))
    x, w = np.zeros(n), np.zeros(n)
    for i in range(m):
        if i == 0:
            z = np.sqrt(2 * n + 1) - 1.85575 * ((2 * n + 1) ** (-1 / 6))
        elif i == 1:
            z = z - 1.14 * (n ** 0.426) / z
        elif i == 2:
            z = 1.86 * z + 0.86 * x[0]
        elif i == 3:
            z = 1.91 * z + 0.91 * x[1]
        else:
            z = 2 * z + x[i - 2]
        for _ in range(100):
            p1, p2 = pim4, 0
            for j in range(n):
                p3, p2 = p2, p1
                p1 = z * np.sqrt(2 / (j + 1)) * p2 - np.sqrt(j / (j + 1)) * p3
            pp = np.sqrt(2 * n) * p2
            z1, z = z, z - p1 / pp
            if abs(z - z1) < 1e-14:
                break
        else:
            raise ArithmeticError(f"the Gauss-Hermite root {i} of order {n} did not converge in 100 iterations")
        x[n - i - 1], x[i] = z, -z
        w[i] = w[n - i - 1] = 2 / pp ** 2
    return x * np.sqrt(2), w / np.sqrt(np.pi)


def normal_nodes(mean, covariance, orders):
    """Nodes of the logarithms and weights for the normal distribution N(mean, covariance): in one dimension the rule
    scaled by the standard deviation; in several, the tensor product of the rules, the first coordinate varying
    slowest, mapped by the Cholesky factor of the covariance; the mean added once."""
    rules = [hermite_nodes(n) for n in orders]
    if len(orders) == 1:
        nodes, weights = rules[0]
        return (nodes * np.sqrt(covariance[0, 0]))[:, None] + mean, weights
    standard = np.array(list(itertools.product(*(nodes for nodes, _ in rules)))).T
    weights = reduce(np.kron, [weights for _, weights in rules])
    return np.ascontiguousarray((np.dot(np.linalg.cholesky(covariance), standard) + mean[:, None]).T), weights


def reference_normal_nodes(mean, covariance, orders):
    """The nodes the fixed reference integrated with: those of `normal_nodes` with the mean added once more in
    two or more dimensions, as the earlier library's `Normal.discretize` added it after `gauss_hermite_nodes`
    had; in one dimension the two rules agree (item 4 of the acceptance)."""
    nodes, weights = normal_nodes(mean, covariance, orders)
    return (nodes + mean if len(orders) > 1 else nodes), weights


# the quadrature rule each handler names
QUADRATURE = {"cons-port:gauss_hermite": normal_nodes, "cons-port:gauss_hermite_reference": reference_normal_nodes}


def _realized(table, handler, stage, place):
    """The entry of `table` for `handler`, or the refusal naming the handlers the tool realizes."""
    if handler not in table:
        raise ValueError(f"stage {stage.name!r}: the handler {handler!r} at {place!r} is not one this tool realizes; "
                         f"it realizes {', '.join(sorted(table))}")
    return table[handler]


def expectation_rule(record, handler, counts):
    """Quadrature from a detached law, handler name, and bound node counts."""
    if handler not in QUADRATURE:
        raise ValueError(f"Unsupported quadrature handler {handler!r}.")
    shocks, mean, covariance = lognormal_law(record)
    log_nodes, weights = QUADRATURE[handler](mean, covariance, [counts[f"n_{shock}"] for shock in shocks])
    return {shock: np.exp(log_nodes[:, j]) for j, shock in enumerate(shocks)}, weights


def piece_function(record, key):
    """The function of one piece of a builder's `kernels()` record, the piece `key` reaches from its builder,
    called with the values the record's calibration binds to its parameters after its own arguments."""
    found = [held for held in record.pieces if held.key == key]
    if len(found) != 1:
        raise ValueError(f"the builder {record.builder!r} holds no one piece {key!r}; its pieces are "
                         f"{', '.join(str(held.key) for held in record.pieces)}")
    (piece,) = found
    if piece.function is None:
        raise ValueError(f"the builder {record.builder!r}: the piece {key!r} has no function, since its line is not "
                         "in closed form, an expectation among such lines (kernel-form); this tool evaluates "
                         "compiled pieces alone")
    if piece.parameter_values is None:
        raise ValueError(f"the builder {record.builder!r} is of a version no calibration binds; this tool reads "
                         "calibrated stages")
    function, values = piece.function, tuple(piece.parameter_values)
    return lambda *arguments: function(*arguments, *values)


def piece_arguments(record, key):
    """The names of the arguments of one piece of a builder's `kernels()` record, in the order its function
    takes them."""
    found = [held for held in record.pieces if held.key == key]
    if len(found) != 1:
        raise ValueError(f"the builder {record.builder!r} holds no one piece {key!r}; its pieces are "
                         f"{', '.join(str(held.key) for held in record.pieces)}")
    return tuple(str(name) for name in found[0].arguments)


def by_name(record, key, supplied):
    """The function of the piece `key` called with the arguments it names, each taken from the mapping
    `supplied`; a name the mapping does not hold is refused with the names it holds."""
    names = piece_arguments(record, key)
    missing = [name for name in names if name not in supplied]
    if missing:
        raise ValueError(f"the builder {record.builder!r}: the piece {key!r} takes {', '.join(missing)}, which this "
                         f"tool does not supply; it supplies {', '.join(supplied)}")
    return piece_function(record, key)(*(supplied[name] for name in names))


def derivative_input(record, key):
    """The name under which the piece `key` takes the derivative of the continuation value its line reads, the
    term's printed form, such as `D_{m_next}V[>]`."""
    (name,) = [name for name in piece_arguments(record, key) if name.startswith("D_")]
    return name


def integrand_inputs(record, key, shocks, law_names, integrated):
    """The inputs the integrand piece `key` may take beyond the law of motion's and the derivative term: each
    input of the builder's Aggregation that the law does not give, the value's expectation `w` among them, bound
    to `integrated`. The piece must name under `integrated` the shocks `shocks` whose nodes the tool holds: a
    derivative line whose right side is one expectation compiles as its integrand over those shocks, and the
    quadrature of the value's expectation applies to it; any other piece is refused."""
    piece_arguments(record, key)
    (piece,) = [held for held in record.pieces if held.key == key]
    named = tuple(str(shock) for shock in piece.integrated)
    if sorted(named) != sorted(shocks):
        raise ValueError(f"the builder {record.builder!r}: the piece {key!r} is integrated over "
                         f"({', '.join(named)}), and the tool holds the nodes of ({', '.join(shocks)}); this tool "
                         "integrates a stated derivative whose right side is one expectation over those shocks")
    return {name: integrated for name in piece_arguments(record, "Aggregation") if name not in law_names}


def without_piece(record, key):
    """The record as asva reads it, its pieces, parameters and parameter values, with the piece `key` left out."""
    return SimpleNamespace(builder=record.builder, pieces=tuple(held for held in record.pieces if held.key != key),
                           parameters=record.parameters, parameter_values=record.parameter_values)


def egm(decision, policy, *, input_conditions=()):
    """The endogenous-grid operator of the consumption stage: one call of asva's `egm` on the kernels of the
    policy builder and of the backward decision builder, `stage.builder.policy.kernels()` and
    `stage.dcsn.builder.bwd.kernels()`, with the savings grid of `!egm` and the evaluation grid of the
    representation. On the savings grid the inverse marginal utility of the continuation's marginal value (the
    line InvEuler) gives consumption and the line grid the resources it was chosen at; consumption is
    interpolated onto the evaluation grid and held in (1e-10, m_d − 1e-10); savings follow from the law of
    motion, held to the savings grid; the value from the aggregation and the marginal value from the piece of
    the stated derivative. The operator reads no stage."""
    resources = evaluation_grid(decision)
    # D4 of AMD-MB-001: the stated derivative of the value stands at the decision builder's Evaluation, and its
    # kernel is the piece `<line id>:Derivative:1`; asva reads the law of motion and the aggregation, so the
    # record it is given leaves that piece out, and the tool evaluates the piece itself.
    key = marginal_key(decision)
    step = asva.egm(policy, without_piece(decision, key), savings_grid(policy), resources)
    names = piece_arguments(decision, "Aggregation")

    def operator(continuation):
        held = step(continuation, continuation.dV)
        c, continued = held.control, held.continuation_value
        marginal = by_name(decision, key, dict(zip(names, (continued, resources, c))))
        return ValueFn(resources, np.where(c > 0, held.value, LOW + continued), np.where(c > 0, marginal, HIGH),
                       {"c": c, "a": held.continuation_state}, input_conditions=input_conditions)
    return operator


def consumption_search(decision, *, input_conditions=()):
    """A grid search on the consumption stage: at each point of the evaluation grid the aggregation at the law
    of motion over the candidates the feasible factor of `!vfi` counts, `!Cartesian(c=(Γ, n_c))`. The endpoint
    inset is min(1e-6, 1e-6 times the interval width). The first maximum is chosen; the marginal value is the
    difference quotient of the values. The
    aggregation's value is its first output where it also writes the marginal value, and its one output where
    no derivative line is stated."""
    resources = evaluation_grid(decision)
    factor = decision.grid_factors["cntn_to_dcsn"]
    law, aggregate = piece_function(decision, "Pullback"), piece_function(decision, "Aggregation")
    # whether the aggregation writes the marginal value beside the value, as its piece's outputs name them
    pair = len(next(held for held in decision.pieces if held.key == "Aggregation").outputs) > 1

    def operator(continuation):
        values, chosen = np.full(len(resources), LOW), np.zeros(len(resources))
        for i, m_d in enumerate(resources):
            c = feasible_points(factor, {"m": m_d}, inset=1e-6)
            outputs = aggregate(continuation(law(m_d, c)), m_d, c)
            objective = outputs[0] if pair else outputs
            if not np.all(np.isfinite(objective)):
                raise ValueError("The consumption objective must be finite at every candidate.")
            best = int(np.argmax(objective))
            values[i], chosen[i] = objective[best], c[best]
        return ValueFn(resources, values, np.gradient(values, resources), {"c": chosen}, input_conditions=input_conditions)
    return operator


def share_objective(decision, nodes, weights, *, historical=False):
    """The objective of the share choice, the line `objective` of the portfolio stage's policy block (port.bl
    line 25), as a function of a continuation value, a point k_d of the evaluation grid and an array of shares:
    at each share, the supplied continuation value at the law of motion, integrated by the rule at the
    expectation of `cntn_to_dcsn`. Only the historical handler clips resources to the decision grid.
    `share_search` chooses the first share at which the objective is largest."""
    capital = evaluation_grid(decision) if historical else None
    Ψ, θ = nodes["Ψ"], nodes["θ"]
    law = piece_function(decision, "Pullback")

    def objective(continuation, k_d, shares):
        resources = law(k_d, shares[:, None], Ψ, θ)
        if historical:
            resources = np.clip(resources, capital[0], capital[-1])
        reached = continuation(resources)
        return np.array([np.dot(weights, row) for row in reached])
    return objective


def share_search(decision, policy, nodes, weights, by_the_line, *, input_conditions=()):
    """A grid search over the risky share: at each point k_d of the evaluation grid, the objective of
    `share_objective` at the shares the feasible factor of the policy builder's grid counts,
    `!Cartesian(ς=(Γ_ς, n_ς))`, evenly spaced on Γ_ς(k_d) = [0, 1] (port.bl line 10); the first share with the
    largest expectation is chosen. The marginal value follows the handler of the method that solves the
    policy: `cons-port:share_search` integrates the envelope line at the chosen share,
    `cons-port:share_search_reference` takes the difference quotient of the values and retains the reference's
    −1e10 floor. That historical handler does not solve a problem whose maximum lies below the floor."""
    capital = evaluation_grid(decision)
    factor = policy.grid_factors["policy"]
    points_by_interval = {}
    objective = share_objective(decision, nodes, weights, historical=not by_the_line)
    Ψ, θ = nodes["Ψ"], nodes["θ"]
    law, law_names = piece_function(decision, "Pullback"), piece_arguments(decision, "Pullback")
    # D4 of AMD-MB-001: the stated derivative's kernel is the piece `<line id>:Derivative:1` of the decision
    # builder, which reads the derivative of the continuation value under the term's printed form
    key = marginal_key(decision) if by_the_line else None

    def operator(continuation):
        values, chosen = np.full(len(capital), LOW), np.zeros(len(capital))
        for i, k_d in enumerate(capital):
            shares = feasible_points(factor, {"k": k_d}, cache=points_by_interval)
            expected = objective(continuation, k_d, shares)
            if by_the_line:
                if not np.all(np.isfinite(expected)):
                    raise ValueError("The portfolio objective must be finite at every candidate share.")
                best = int(np.argmax(expected))
                values[i], chosen[i] = expected[best], shares[best]
            else:
                # Only the explicitly selected historical handler retains its
                # finite floor. It is not the maximum when every value is lower.
                best = int(np.argmax(np.where(np.isnan(expected), -np.inf, expected)))
                if expected[best] > LOW:
                    values[i], chosen[i] = expected[best], shares[best]
        if by_the_line:
            resources = law(capital[:, None], chosen[:, None], Ψ, θ)
            # the integrand of the derivative line at the nodes of the value's expectation, summed with its weights
            supplied = integrand_inputs(decision, key, tuple(nodes), law_names, values[:, None])
            supplied.update(zip(law_names, (capital[:, None], chosen[:, None], Ψ, θ)))
            supplied[derivative_input(decision, key)] = continuation.dV(resources)
            marginal = by_name(decision, key, supplied) @ weights
        else:
            marginal = np.gradient(values, capital)
        return ValueFn(capital, values, marginal, {"varsigma": chosen}, input_conditions=input_conditions)
    return operator


def expectation(decision, nodes, weights, *, input_conditions=()):
    """A stage with an expectation and no choice (noport): at each point k_d of the evaluation grid the
    continuation value and the envelope line are integrated at the law of motion, the resources held to the
    continuation's grid, by the rule at the expectation of `cntn_to_dcsn`."""
    capital = evaluation_grid(decision)
    θ = nodes["θ"]
    law, law_names = piece_function(decision, "Pullback"), piece_arguments(decision, "Pullback")
    # D4 of AMD-MB-001: the stated derivative's kernel is the piece `<line id>:Derivative:1` of the decision
    # builder, which reads the derivative of the continuation value under the term's printed form
    key = marginal_key(decision)

    def operator(continuation):
        resources = np.clip(law(capital[:, None], θ), continuation.grid[0], continuation.grid[-1])
        values = np.array([np.dot(weights, row) for row in continuation(resources)])
        # the integrand of the derivative line at the nodes of the value's expectation, summed with its weights
        supplied = integrand_inputs(decision, key, tuple(nodes), law_names, values[:, None])
        supplied.update(zip(law_names, (capital[:, None], θ)))
        supplied[derivative_input(decision, key)] = continuation.dV(resources)
        lines = by_name(decision, key, supplied)
        return ValueFn(capital, values, np.array([np.dot(weights, row) for row in lines]), {}, input_conditions=input_conditions)
    return operator


def aggregation(decision, *, input_conditions=()):
    """A stage with neither a choice nor an expectation (disc): its aggregation at each point of the
    continuation's grid, applied to the values and to the derivative values the continuation holds."""
    aggregate = piece_function(decision, "Aggregation")

    def operator(continuation):
        value = aggregate(continuation.values, continuation.grid)
        # D3 of AMD-MB-001: a line that scales the value it reads, through a law that leaves the state unchanged,
        # carries the stored derivative values by the same map, here multiplication by β.
        marginal = None if continuation.dvalues is None else aggregate(continuation.dvalues, continuation.grid)
        return ValueFn(continuation.grid, value, marginal, {}, input_conditions=input_conditions)
    return operator


# the operator each handler at a policy place names
POLICY = {"cons-port:egm": egm, "cons-port:consumption_search": consumption_search,
          "cons-port:share_search": share_search, "cons-port:share_search_reference": share_search}


def policy_method(stage):
    """The place and the components of the stage occurrence's one method at a place of POLICY_PLACES, or None
    where it binds none."""
    held = [(str(key), method) for key, method in stage.methods.items() if str(key) in POLICY_PLACES]
    if not held:
        return None
    (found,) = held
    return found


def marginal_key(record):
    """The key of the piece of a backward decision builder's record that evaluates the stated derivative of the
    value, `<line>:Derivative:1` for the first line of MARGINAL_LINES the record holds."""
    # D4 of AMD-MB-001: a derivative line stands at the value builder's Evaluation as a property of the value,
    # and `kernels()` answers its kernel as the piece `<line id>:Derivative:1`
    held = {piece.key for piece in record.pieces}
    found = [f"{line}:Derivative:1" for line in MARGINAL_LINES if f"{line}:Derivative:1" in held]
    return found[0] if found else f"{MARGINAL_LINES[0]}:Derivative:1"


def stage_operator(stage, inputs):
    """An operator constructed after checking the complete continuation mapping."""
    conditions = stage.check_inputs(inputs)
    decision = stage.dcsn.builder.bwd.kernels(inputs=inputs)
    expected = expectation_place(stage)
    if expected is not None:
        method = method_at(stage, expected)
        counts = {name: int(setting(stage, value)) for name, value in keyword_arguments(method).items()}
        nodes, weights = expectation_rule(decision, method.handler, counts)
    found = policy_method(stage)
    if found:
        place, method = found
        construct = _realized(POLICY, method.handler, stage, place)
        if construct is consumption_search:
            operator = construct(decision, input_conditions=conditions)
        else:
            policy = stage.builder.policy.kernels(inputs=inputs)
            operator = (construct(decision, policy, input_conditions=conditions) if construct is egm else
                        construct(decision, policy, nodes, weights,
                                  method.handler == "cons-port:share_search", input_conditions=conditions))
    else:
        operator = (expectation(decision, nodes, weights, input_conditions=conditions) if expected
                    else aggregation(decision, input_conditions=conditions))
    operator.input_conditions = conditions
    return operator


def zero_value(points):
    """Zero value after the terminal consumption decision."""
    return np.zeros_like(points, dtype=float)


def terminal_value(consumption, grid):
    """The value of ending with the resources `grid`: all of it consumed and nothing continued, the consumption
    stage's aggregation 𝐺(V≻, m, c) at V≻ = 0 and c = m, and the stated derivative of the value at the same
    point; the values −10¹⁰ and 10¹⁰ where a point is not positive."""
    inputs = {"V[>]": zero_value}
    conditions = consumption.check_inputs(inputs)
    record = consumption.dcsn.builder.bwd.kernels(inputs=inputs)
    arguments = (np.zeros_like(grid), grid, grid)
    value = piece_function(record, "Aggregation")(*arguments)
    # D4 of AMD-MB-001: the stated derivative's kernel is the piece `<line id>:Derivative:1`, which takes the
    # inputs of the Aggregation
    marginal = by_name(record, marginal_key(record), dict(zip(piece_arguments(record, "Aggregation"), arguments)))
    return ValueFn(grid, np.where(grid > 0, value, LOW), np.where(grid > 0, marginal, HIGH),
                   input_conditions=conditions)


def solve_period(period, continuation):
    """The arrival value of each stage occurrence of a specified period, in the backward order its joins
    determine: a stage whose continuation fields leave the period reads `continuation`, and every other stage
    the arrival value of the stage its continuation field joins."""
    successors = {}
    for join in period_joins(period)["joins"]:
        successors.setdefault(join["from"][0], set()).add(join["to"][0])
    solved = {}
    for key in backward_order(period):
        after = successors.get(key, set())
        if len(after) > 1:
            raise ValueError(f"stage {key!r} continues to {sorted(after)}; a stage joined to two stages waits for branching (B02)")
        inputs = {"V[>]": solved[after.pop()]} if after else continuation
        operator = stage_operator(period["stages"][key], inputs)
        solved[key] = operator(inputs["V[>]"])
    return solved


def continuation_across(model, h, solved):
    """The continuation value of periods[h], h ≥ 1: the arrival value, in periods[h − 1], of the stage to which
    the inter-period connector inter_connectors[h − 1] joins the fields leaving periods[h] (D15)."""
    joins = inter_period_joins(model["inter_connectors"][h - 1], model["periods"][h], model["periods"][h - 1])
    (arrival,) = {join["to"][0] for join in joins}
    return solved[h - 1][arrival]


def solve_trellis(model, terminal):
    """The solutions of a specified trellis, one mapping from stage key to arrival value per period, in the order
    of `periods`, the terminal period first. `terminal` is the complete declared input mapping, for example
    {"V[>]": terminal_value(stage, grid)}. Each earlier period reads the value its inter-period connector
    names. Results retain unresolved input conditions. The trellis is read and not changed."""
    if not isinstance(terminal, Mapping):
        raise TypeError("Terminal data must be the complete declared input mapping, such as {'V[>]': value}.")
    solved = []
    for h, period in enumerate(model["periods"]):
        solved.append(solve_period(period, terminal if h == 0 else {"V[>]": continuation_across(model, h, solved)}))
    return solved


# The entries of the fixed reference, `<configuration>/h<h>/<field>`, as the stage occurrences of this model
# holding the same arrays: field → (the stage whose value, the stage whose policy, the nested entries the earlier
# helper wrote under policy/, each (value, policy)). In cons then port the reference discounted before the
# portfolio stage; here discounting stands between consumption and the portfolio stage, so the reference's `k`
# is the discount stage's arrival value with the portfolio stage's share (plan, question 3).
REFERENCE_VIEW = {
    "cons_only": {"k": ("noport", None, {"_cons_stage": ("cons", "cons")}), "m": ("cons", "cons", {})},
    "beginning_egm": {"k": ("port", "port", {"_cons_stage": ("cons", "cons")}), "m": ("cons", "cons", {})},
    "beginning_vfi": {"k": ("port", "port", {"_cons_stage": ("cons", "cons")}), "m": ("cons", "cons", {})},
    "end_returns": {"m": ("cons", "cons", {"_port_stage": ("disc", "port")}), "k": ("disc", "port", {})},
    "port_only": {"k": ("port", "port", {}), "m": ("port", "port", {})},
}


def reference_arrays(configuration, solved):
    """The arrays of one solved configuration under the paths the fixed reference stores them at:
    `<configuration>/h<h>/<field>/{grid,values,dvalues}`, the policy arrays of the stage whose policy the
    entry held under `policy/<name>`, and the nested entries under `policy/_<stage>/`."""
    arrays = {}

    def put(prefix, value_of, policy_of, period):
        held = period[value_of]
        arrays[f"{prefix}/grid"], arrays[f"{prefix}/values"], arrays[f"{prefix}/dvalues"] = held.grid, held.values, held.dvalues
        for name, array in (period[policy_of].policy.items() if policy_of else ()):
            arrays[f"{prefix}/policy/{name}"] = array

    for h, period in enumerate(solved):
        for field, (value_of, policy_of, nested) in REFERENCE_VIEW[configuration].items():
            put(f"{configuration}/h{h}/{field}", value_of, policy_of, period)
            for name, (inner_value, inner_policy) in nested.items():
                put(f"{configuration}/h{h}/{field}/policy/{name}", inner_value, inner_policy, period)
    return arrays


def plot_functions(curves, *, xlabel, ylabel, title, diagonal=None, xlim=None):
    """One figure of the curves `{label: (x, y)}`, each labeled; `diagonal` names the line y = x and draws it
    dotted; `xlim` cuts the axis. Nothing is saved."""
    figure, axis = plt.subplots(figsize=(6.4, 4.2))
    for label, (x, y) in curves.items():
        axis.plot(x, y, linewidth=1.4, label=label)
    if xlim is not None:
        axis.set_xlim(*xlim)
    if diagonal is not None:
        low, high = axis.get_xlim()
        axis.plot([low, high], [low, high], color="0.5", linestyle=":", linewidth=1.0, label=diagonal)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend(frameon=False)
    figure.tight_layout()
    plt.close(figure)
    return figure
