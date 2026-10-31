"""Generic EGM backward builders (cntn_to_dcsn_builder).

Provides factory functions that accept sub-equation callables
(the "EGM recipe") and return compiled EGM operators:

*  ``make_egm_1d`` — scalar (1-D) continuation grid.
*  ``make_egm``    — K-dimensional continuation grid (pure EGM).
*  ``egm``         — the step of ``make_egm_1d`` for a one-dimensional
   consumption stage, built from the records of the kernels of its
   policy builder and backward decision builder that the package
   ``bellman`` answers; the parameter values are passed at each call.

The callables follow a standardized signature::

    fn(pointwise_input..., fixed_state) → result

- ``fixed_state``: non-optimized state variables held constant
  during inversion (e.g. housing stock for a durables keeper;
  0.0 for a 1D consumption-savings model).
- Model parameters are fixed in the callables at construction time;
  ``egm`` passes the parameter values in ``fixed_state`` instead, so
  that one compilation serves every calibration.

The returned operators are ``@njit``-compiled and grid-agnostic:
the continuation grid is passed as an argument so the same
operator works with any grid size without JIT recompilation.

Theory reference
----------------
The K-dimensional factory (``make_egm``) implements *pure EGM*
(Dobrescu & Shanker, Theorem 4.1): the exogenous grid dimension
K equals the active-state dimension, and the Jacobian
non-degeneracy condition ensures local invertibility.  When
dim(active states) < dim(post-states), root-finding is needed
to construct the exogenous grid on a lower-dimensional
submanifold (Claim 3.2); that grid construction is outside this
module's scope — once the K-dim exogenous grid is formed, the
operator returned by ``make_egm`` can process it.
"""

from __future__ import annotations

import types
from collections import namedtuple

import numpy as np
from numba import njit


# ── 1-D scalar EGM ────────────────────────────────────────────

def make_egm_1d(fn_inv_euler, fn_bellman_rhs, fn_cntn_to_dcsn,
                fn_concavity):
    """Build a 1D EGM backward operator from sub-equation callables.

    Parameters
    ----------
    fn_inv_euler : callable
        ``(dv_cntn_i, fixed_state) → c_i``
        Recover optimal control from marginal continuation value.
    fn_bellman_rhs : callable
        ``(c_i, v_cntn_i, fixed_state) → v_i``
        Reconstruct value at decision perch.
    fn_cntn_to_dcsn : callable
        ``(c_i, x_cntn_i, fixed_state) → x_dcsn_i``
        Build endogenous grid (the transition).
    fn_concavity : callable
        ``(c_i, ddv_cntn_i, fixed_state) → del_a_i``
        Concavity diagnostic for DCEGM upper envelope.

    Returns
    -------
    callable
        ``egm_step(dv_cntn, ddv_cntn, v_cntn, x_cntn, fixed_state)``
        → ``(c_hat, v_hat, x_dcsn_hat, del_a)``
    """

    @njit
    def egm_step(dv_cntn, ddv_cntn, v_cntn, x_cntn, fixed_state):
        """EGM backward step over the continuation grid.

        Returns unrefined (pre-upper-envelope) decision-perch
        quantities on the endogenous grid.
        """
        n = len(x_cntn)
        c_hat = np.zeros(n)
        v_hat = np.zeros(n)
        x_dcsn_hat = np.zeros(n)
        del_a = np.zeros(n)

        for i in range(n):
            c = fn_inv_euler(dv_cntn[i], fixed_state)
            v_hat[i] = fn_bellman_rhs(c, v_cntn[i],
                                      fixed_state)
            c_hat[i] = c
            x_dcsn_hat[i] = fn_cntn_to_dcsn(c, x_cntn[i],
                                             fixed_state)
            del_a[i] = fn_concavity(c, ddv_cntn[i],
                                    fixed_state)

        return c_hat, v_hat, x_dcsn_hat, del_a

    return egm_step


# ── K-dimensional EGM (pure EGM) ──────────────────────────────

def make_egm(fn_inv_euler, fn_bellman_rhs, fn_cntn_to_dcsn,
             fn_concavity, params, n_dims, n_controls):
    r"""Build a K-dimensional EGM backward operator (pure EGM).

    Generalises ``make_egm_1d`` to an arbitrary-dimensional
    continuation grid.  Given N points on a K-dimensional
    exogenous grid, the operator inverts the Euler equation at
    each point to recover the optimal control vector, then maps
    continuation-perch coordinates to decision-perch (endogenous)
    coordinates.

    Invertibility (Dobrescu & Shanker)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    *  Pure EGM requires ``dim(active states) = dim(post-states)
       = K`` (Claim 3.1).  The Jacobian condition

       .. math::

           \det\,\partial_{x_{\mathrm{act}}}
               \operatorname{proj}\,E(x_{\mathrm{act}},\,\tilde e)
           \neq 0

       guarantees local invertibility (Theorem 4.1).
       ``fn_inv_euler`` encodes this: it must return a well-defined
       control for every gradient in the exogenous grid's image.

    *  Some grid dimensions may be **pass-through** (identity
       map from cntn to dcsn, e.g. housing stock H for a
       non-adjuster).  These dimensions are formally part of the
       K-dimensional grid but contribute trivially to the
       Jacobian (diagonal entry = 1).  The callable still
       receives their gradient and coordinate so it can use them
       in the inversion (e.g. ``inv_mu(dV/da', H)``).

    *  When ``dim(active) < dim(post-states)``, the exogenous grid
       lives on a lower-dimensional submanifold and root-finding
       is needed to construct it (Claim 3.2).  Once the grid is
       constructed, this operator can process it.

    *  For models with occasionally binding constraints, the
       exogenous grid is partitioned across constrained regions;
       each region is inverted separately.

    Parameters
    ----------
    fn_inv_euler : callable
        ``(dv_cntn_i: float[K], x_cntn_i: float[K], fixed_state,
        params) → c_i: float[n_c]``

        Recover optimal control vector from the K-dimensional
        gradient of the continuation value **and** the grid
        coordinate at one exogenous grid point.  The coordinate
        is needed when some grid dimensions enter the utility
        directly (e.g. housing stock H in ``inv_mu(dV/da', H)``).
    fn_bellman_rhs : callable
        ``(c_i: float[n_c], v_cntn_i: float, x_cntn_i: float[K],
        fixed_state, params) → v_i: float``

        Reconstruct the scalar value at the decision perch.
        Receives the grid coordinate because the period reward
        may depend on it (e.g. ``u(c, H)``).
    fn_cntn_to_dcsn : callable
        ``(c_i: float[n_c], x_cntn_i: float[K], fixed_state, params)
        → x_dcsn_i: float[K]``

        Map (control, continuation coordinate) to the K-dimensional
        endogenous grid coordinate.  Dimensions that are not
        inverted (pass-through states like H) return the input
        value unchanged: ``x_dcsn_i[k] = x_cntn_i[k]``.
    fn_concavity : callable
        ``(c_i: float[n_c], ddv_cntn_i: float[K], x_cntn_i: float[K],
        fixed_state, params) → del_a_i: float[K]``

        Concavity diagnostic per dimension for the upper-envelope
        step (e.g. FUES / RFC).  Pass-through dimensions can
        return 0.0.
    params : ndarray
        Model-specific scalar parameter array.
    n_dims : int
        Dimension K of the exogenous and endogenous grids.
    n_controls : int
        Number of control variables recovered by the inverse Euler.

    Returns
    -------
    callable
        ``egm_step(dv_cntn, ddv_cntn, v_cntn, x_cntn, fixed_state)``
        → ``(c_hat, v_hat, x_dcsn_hat, del_a)``

        Array shapes::

            dv_cntn     (N, K)      gradient of continuation value
            ddv_cntn    (N, K)      second-derivative diagonal
            v_cntn      (N,)        continuation values
            x_cntn      (N, K)      exogenous grid coordinates
            ─────────────────────────────────────────────────────
            c_hat       (N, n_c)    optimal controls
            v_hat       (N,)        decision-perch values
            x_dcsn_hat  (N, K)      endogenous grid coordinates
            del_a       (N, K)      concavity diagnostics

    Examples
    --------
    Housing non-adjuster with pass-through H (K = 2, n_c = 1):
        Grid is ``(a', H)``.  The inverse Euler uses both
        ``dv_cntn_i[0]`` (= ``dV/da'``) and ``x_cntn_i[1]``
        (= ``H``) to compute ``c = inv_mu(dV/da', H)``.
        The transition returns ``[c + a',  H]`` — the H
        dimension is identity.  This eliminates the explicit
        ``for i_h`` loop over housing levels.

    Retirement with two savings instruments (K = 2, n_c = 1):
        Two Euler equations; consumption recovered from one,
        no-arbitrage checked by the other.  Endogenous grid is
        2-D ``(w_fin, w_pen)``.

    Housing adjuster (K = 1, after root-finding):
        Active-state dimension is 1 (total resources) even though
        post-states are 2-D.  Root-finding first constructs the
        1-D exogenous grid on a submanifold of ``(a', h')``; then
        ``make_egm`` processes it with K = 1.
    """

    @njit
    def egm_step(dv_cntn, ddv_cntn, v_cntn, x_cntn, fixed_state):
        """EGM backward step over a K-dimensional continuation grid.

        Returns unrefined (pre-upper-envelope) decision-perch
        quantities on the endogenous grid.
        """
        n = x_cntn.shape[0]
        c_hat = np.zeros((n, n_controls))
        v_hat = np.zeros(n)
        x_dcsn_hat = np.zeros((n, n_dims))
        del_a = np.zeros((n, n_dims))

        for i in range(n):
            c = fn_inv_euler(dv_cntn[i], x_cntn[i],
                             fixed_state, params)
            v_hat[i] = fn_bellman_rhs(c, v_cntn[i], x_cntn[i],
                                      fixed_state, params)
            c_hat[i] = c
            x_dcsn_hat[i] = fn_cntn_to_dcsn(c, x_cntn[i],
                                             fixed_state, params)
            del_a[i] = fn_concavity(c, ddv_cntn[i], x_cntn[i],
                                    fixed_state, params)

        return c_hat, v_hat, x_dcsn_hat, del_a

    return egm_step


# ── The step from the records of a stage's kernels ────────────

EndogenousGridStep = namedtuple(
    "EndogenousGridStep",
    "control continuation_state value continuation_value "
    "endogenous_grid endogenous_control endogenous_value")
EndogenousGridStep.__doc__ = """The arrays of one endogenous grid step.

On the evaluation grid of the decision state: ``control``, the chosen
control; ``continuation_state``, the continuation state the law of motion
gives from each decision state and its control, held to the range of the
savings grid; ``continuation_value``, the continuation value at that state;
``value``, the output of the aggregation. No marginal value is returned:
a stage states the derivative of its value by a piece of its own, which
egm does not read. On
the savings grid: ``endogenous_grid``, the decision state from which the
control chosen there leads to each point; ``endogenous_control``, that
control, given by the inverse Euler equation; ``endogenous_value``, the
value at that decision state. The last three are the arrays ``x_dcsn_hat``,
``c_hat`` and ``v_hat`` of ``make_egm_1d``, before any upper envelope.
"""

# The pieces with a function that egm reads in each record, in order of
# application: the numbers of their arguments and of their outputs, and
# what each piece is.
_POLICY_FORM = (
    ((3, 1), "the inverse Euler equation, (continuation value, "
             "continuation state, marginal continuation value) → control"),
    ((2, 1), "the endogenous grid, (control, continuation state) → "
             "decision state"),
)
_DECISION_FORM = (
    ((2, 1), "the law of motion, (decision state, control) → "
             "continuation state"),
    ((3, 1), "the aggregation, (continuation value, decision state, "
             "control) → value"),
)

# The compiled steps, under the code of the three functions they apply.
_COMPILED_STEPS = {}


def egm(policy, decision, savings, evaluation, *, margin=1e-10):
    """The endogenous grid step of a one-dimensional consumption stage,
    built on ``make_egm_1d`` from the records of the kernels of the
    stage's policy builder and backward decision builder.

    ``policy`` and ``decision`` are the records that the package
    ``bellman`` answers as ``stage.builder.policy.kernels()`` and
    ``stage.dcsn.builder.bwd.kernels()``; asva imports nothing of that
    package. From each record egm reads ``pieces``, in order of
    application, ``parameters`` and ``parameter_values``, and from each
    piece its ``name``, its ``function``, which is ``None`` for a row that
    states a relation, and the names of its ``arguments``, its ``outputs``
    and its ``parameters``. A function takes its arguments and then the
    values of its parameters, in the order the piece names them. In
    ``policy`` the pieces with a function must be the inverse Euler
    equation, (continuation value, continuation state, marginal
    continuation value) → control, the marginal value being the
    derivative term the policy line reads,
    and the endogenous grid, (control, continuation state) → decision
    state; in ``decision``, the law of motion, (decision state, control) →
    continuation state, and the aggregation, (continuation value, decision
    state, control) → value. Any other record, and a
    record that binds no value to a parameter its functions take, is
    refused with ``ValueError``.

    ``savings`` is the grid of the continuation state at which the inverse
    Euler equation is solved, and ``evaluation`` the grid of the decision
    state on which the step gives its result; the caller reads both from
    the stage's settings.

    Returns ``operator(value, marginal)``, which takes the continuation
    value and the marginal continuation value as functions of the
    continuation state and returns an ``EndogenousGridStep``. At each point
    of the savings grid the inverse Euler equation gives the control and
    the endogenous grid gives the decision state it is chosen at. The
    controls, ordered by those decision states, are interpolated linearly
    at the evaluation grid, beyond which the end values are held, and are
    held in [``margin``, x − ``margin``] at each decision state x: the
    interval (0, x] of feasible consumption less the margin at each end,
    so that where the borrowing constraint binds the control is
    x − ``margin``. The law of motion gives the continuation state, held to
    the range of the savings grid, and the aggregation gives the value. The
    step gives no marginal value: the derivative of the value is a piece of
    its own in the stage's record, which the caller evaluates.

    The three functions the step applies at each point of the savings grid
    are compiled by Numba once for their code, and the parameter values are
    passed at each call, so that a record made again from the same kernel
    text, or of another calibration, reuses the compiled step. The operator
    holds functions, arrays and numbers, and reads no stage.
    """
    (inverse, inverse_values), (endogenous, endogenous_values) = \
        _explicit_functions(policy, "policy builder", _POLICY_FORM)
    (law, law_values), (aggregate, aggregate_values) = \
        _explicit_functions(decision, "backward decision builder",
                            _DECISION_FORM)
    savings = np.asarray(savings, dtype=float)
    evaluation = np.asarray(evaluation, dtype=float)
    if savings.ndim != 1 or evaluation.ndim != 1:
        raise ValueError("egm takes a one-dimensional savings grid and a "
                         "one-dimensional evaluation grid")
    step = _compiled_step(inverse, endogenous, aggregate)
    parameter_values = (inverse_values, endogenous_values, aggregate_values)
    # no second derivative of the continuation value is given, so the
    # concavity diagnostic of make_egm_1d reads zeros and is not returned
    zeros = np.zeros(len(savings))

    def operator(value, marginal):
        # make_egm_1d gives each function one entry of each array; each
        # entry of the first array is the triple (value, state, marginal
        # value) in the order of the inverse Euler kernel's arguments, and
        # each entry of the third the pair (value, state)
        c_hat, v_hat, x_dcsn_hat, _ = step(
            np.column_stack((value(savings), savings, marginal(savings))), zeros,
            np.column_stack((value(savings), savings)), savings,
            parameter_values)
        order = np.argsort(x_dcsn_hat)
        control = np.clip(
            np.interp(evaluation, x_dcsn_hat[order], c_hat[order]),
            margin, evaluation - margin)
        continuation_state = np.clip(law(evaluation, control, *law_values),
                                     savings[0], savings[-1])
        continuation_value = value(continuation_state)
        decision_value = aggregate(
            continuation_value, evaluation, control, *aggregate_values)
        return EndogenousGridStep(
            control, continuation_state, decision_value,
            continuation_value, x_dcsn_hat, c_hat, v_hat)

    return operator


def _explicit_functions(record, builder, form):
    """The function of each piece of ``record`` that has one, in order of
    application, with the values of the parameters it takes. Refused unless
    the numbers of the pieces' arguments and outputs are those of ``form``
    and the record binds a value to every parameter the functions take."""
    pieces = tuple(piece for piece in record.pieces
                   if piece.function is not None)
    shapes = tuple((len(piece.arguments), len(piece.outputs))
                   for piece in pieces)
    if shapes != tuple(shape for shape, _ in form):
        held = "; ".join(
            f"{piece.name}, ({', '.join(map(str, piece.arguments))}) → "
            f"({', '.join(map(str, piece.outputs))})"
            for piece in pieces) or "none"
        raise ValueError(
            f"egm reads the {builder}'s pieces with a function as "
            f"{' and '.join(what for _, what in form)}; the record's pieces "
            f"with a function are {held}")
    bound = ({} if record.parameter_values is None
             else dict(zip(record.parameters, record.parameter_values)))
    unbound = [f"{name} of {piece.name}" for piece in pieces
               for name in piece.parameters if name not in bound]
    if unbound:
        raise ValueError(
            f"the {builder}'s record binds no value to {', '.join(unbound)}; "
            "the record of a stage that is not calibrated holds no "
            "parameter values")
    return tuple((piece.function,
                  tuple(bound[name] for name in piece.parameters))
                 for piece in pieces)


def _compiled_step(inverse, endogenous, aggregate):
    """The step ``make_egm_1d`` builds from the inverse Euler equation, the
    endogenous grid and the aggregation, each compiled by Numba. The step is
    kept under the three functions' code, so that the functions made again
    from the same text, as at each stage occurrence of a trellis, reuse it.
    The last argument of the step, which make_egm_1d passes unchanged to
    each function, holds the three functions' parameter values."""
    key = tuple(_code_key(function)
                for function in (inverse, endogenous, aggregate))
    if None not in key and key in _COMPILED_STEPS:
        return _COMPILED_STEPS[key]
    inverse, endogenous, aggregate = \
        njit(inverse), njit(endogenous), njit(aggregate)

    @njit
    def fn_inv_euler(value_state_and_marginal, parameter_values):
        return inverse(value_state_and_marginal[0],
                       value_state_and_marginal[1],
                       value_state_and_marginal[2], *parameter_values[0])

    @njit
    def fn_bellman_rhs(c, v_and_state, parameter_values):
        x_dcsn = endogenous(c, v_and_state[1], *parameter_values[1])
        return aggregate(v_and_state[0], x_dcsn, c,
                         *parameter_values[2])

    @njit
    def fn_cntn_to_dcsn(c, x_cntn, parameter_values):
        return endogenous(c, x_cntn, *parameter_values[1])

    @njit
    def fn_concavity(c, ddv_cntn, parameter_values):
        return 0.0

    step = make_egm_1d(fn_inv_euler, fn_bellman_rhs, fn_cntn_to_dcsn,
                       fn_concavity)
    if None not in key:
        _COMPILED_STEPS[key] = step
    return step


def _code_key(function):
    """The key of ``function`` among the compiled steps: its code and the
    modules it reads by name. ``None`` for a function with a closure or
    default values, or one that reads a global object other than a module,
    whose compiled form such a key cannot identify."""
    if function.__closure__ or function.__defaults__ \
            or function.__kwdefaults__:
        return None
    read = {name: function.__globals__[name]
            for name in _names_read(function.__code__)
            if name in function.__globals__}
    if not all(isinstance(held, types.ModuleType) for held in read.values()):
        return None
    return function.__code__, tuple(sorted(
        (name, held.__name__) for name, held in read.items()))


def _names_read(code):
    """The names that ``code`` and the code objects nested in it read as
    globals or attributes."""
    names = set(code.co_names)
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            names |= _names_read(constant)
    return names
