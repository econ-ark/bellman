---
audience: user
type: user-guide
topic: [numerical-representation]
---
# Numerical steps

> [!summary]
> `make_egm_1d` builds the step of the endogenous grid method on a one-dimensional grid of the continuation state from four functions of numbers that the reader writes, and `make_egm` builds the same step on a grid of K dimensions. `make_compose_interp` builds the step that evaluates arrays known on a grid of decision states at the decision states $g(x)$ of the points $x$ of an arrival grid, with the transition $g$ and the interpolation supplied by the reader. The three functions of `asva.numerics` replace missing and infinite entries of value and policy arrays. `egm` builds the one-dimensional step from the records of a stage's kernels, the two grids supplied by the caller, and passes the parameter values at each call. `make_egm_1d`, `make_egm`, `make_compose_interp` and `egm` each return a function, and none of the functions on this page reads a stage.

> [!info]- Relationship with other documents
> **Formal account** — [Operators and builders](../bellman-calculus/05-Operators%20and%20builders.md): the backward builders whose numerical steps these functions compute.
> **Builds on** — [Perch](../wiki/perch.md): the arrival, decision and continuation perches that the names of the arguments refer to.
> **See also** — [Constraints](../Bellman-Sym/10-constraints.md) §4: the inverse Euler statement of a stage file, which the endogenous grid method reads.

## 1 The names of the arguments

The suffix of an argument's name gives the perch at which its quantity stands: `_arvl` the arrival perch, `_dcsn` the decision perch and `_cntn` the continuation perch ([perch](../wiki/perch.md)). `v` is a value, `dv` a marginal value, `ddv` the second derivative of the value, `c` a control and `x` the state coordinate of a grid; the suffix `_i` marks the entry at one grid point. The suffix `_hat` marks a result of the endogenous grid step before an upper envelope: where the continuation value is not concave, the Euler equation has several solutions at some decision states, and the upper envelope keeps, at each such state, the solution with the highest value. `fixed_state` is a state held constant during the step, such as the housing stock of a household that keeps its house, and is `0.0` when there is none.

## 2 The one-dimensional step

The endogenous grid method (Carroll 2006) computes, at each point of a grid of the continuation state, the control from the marginal continuation value there, and then the decision state from which that control leads to the point. `make_egm_1d` builds this step from four functions:

```python
make_egm_1d(fn_inv_euler, fn_bellman_rhs, fn_cntn_to_dcsn, fn_concavity)
```

The four arguments are functions of numbers compiled with `numba.njit`, the decorator of the Numba package that compiles a Python function to machine code. Each holds the model's parameters as constants: Numba reads their values when it compiles the function, at the step's first call, so a model with other parameter values needs its own four functions and its own step.

| Argument | Called at grid point i as | Returns |
|---|---|---|
| `fn_inv_euler` | `fn_inv_euler(dv_cntn_i, fixed_state)` | the control, from the marginal continuation value: the inverse Euler equation |
| `fn_bellman_rhs` | `fn_bellman_rhs(c_i, v_cntn_i, fixed_state)` | the value at the decision perch |
| `fn_cntn_to_dcsn` | `fn_cntn_to_dcsn(c_i, x_cntn_i, fixed_state)` | the decision state from which the control leads to the continuation state `x_cntn_i`: the point of the endogenous grid |
| `fn_concavity` | `fn_concavity(c_i, ddv_cntn_i, fixed_state)` | a number that an upper-envelope step reads, such as the derivative of the continuation state with respect to the decision state |

The call returns the step, a function that Numba compiles at its first call:

```python
egm_step(dv_cntn, ddv_cntn, v_cntn, x_cntn, fixed_state)
```

Its first four arguments are one-dimensional arrays of one length: the marginal continuation value, its derivative and the continuation value at the points of the continuation grid `x_cntn`, and the grid itself. At each point the step calls the four functions in the order of the table, and it returns four arrays of the same length: the controls `c_hat`, the values `v_hat`, the endogenous grid `x_dcsn_hat` and the results of `fn_concavity`, `del_a`. The grid is an argument of the step, so one step computes on grids of every length without being compiled again. A function that Numba has not compiled is refused at the step's first call, with Numba's `TypingError`.

The example is one step of a consumption–savings problem at the decision perch: cash on hand $m$, consumption $c$ and savings $a = m - c$, the utility $u(c) = c^{1-\rho}/(1-\rho)$ with $\rho = 2$, and the continuation value $V_\succ(a) = -1/(1+a)$ on a grid of savings. The first-order condition $u'(c) = V_\succ'(a)$ gives $c = V_\succ'(a)^{-1/\rho} = 1 + a$; the point of the endogenous grid is $m = a + c = 1 + 2a$; the value is $u(c) + V_\succ(a) = -2/(1 + a)$; and the derivative of savings with respect to cash on hand, $u''(c)/(u''(c) + V_\succ''(a))$, is one half at every point. The listing passes $V_\succ'$, $V_\succ''$ and $V_\succ$ at the savings grid as the step's arguments `dv_cntn`, `ddv_cntn` and `v_cntn`, and names the endogenous grid, which is in cash on hand, `m_hat`.

```python
import numpy as np
from numba import njit
from asva.egm_1d import make_egm_1d

ρ = 2.0

@njit
def inv_euler(dv_cntn, fixed_state):
    return dv_cntn ** (-1.0 / ρ)

@njit
def bellman_rhs(c, v_cntn, fixed_state):
    return c ** (1.0 - ρ) / (1.0 - ρ) + v_cntn

@njit
def cntn_to_dcsn(c, a, fixed_state):
    return a + c

@njit
def savings_slope(c, ddv_cntn, fixed_state):
    ddu = -ρ * c ** (-ρ - 1.0)
    return ddu / (ddu + ddv_cntn)

egm_step = make_egm_1d(inv_euler, bellman_rhs, cntn_to_dcsn, savings_slope)

a = np.array([0.0, 0.5, 1.0, 2.0])
c_hat, v_hat, m_hat, del_a = egm_step((1 + a) ** -2, -2 * (1 + a) ** -3, -1 / (1 + a), a, 0.0)
print(c_hat, m_hat, v_hat.round(4), del_a)
```

```text
[1.  1.5 2.  3. ] [1. 2. 3. 5.] [-2.     -1.3333 -1.     -0.6667] [0.5 0.5 0.5 0.5]
```

## 3 The step on K dimensions

```python
make_egm(fn_inv_euler, fn_bellman_rhs, fn_cntn_to_dcsn, fn_concavity, params, n_dims, n_controls)
```

`make_egm` builds the same step on a grid of K = `n_dims` dimensions with `n_controls` controls. `params` is an array of the model's parameters, held by the step and passed to each function at every point. The four functions, compiled with `numba.njit`, also receive the grid point, since a coordinate of the grid may enter the utility, and they return what the table states:

| Argument | Called at grid point i as | Returns |
|---|---|---|
| `fn_inv_euler` | `fn_inv_euler(dv_cntn_i, x_cntn_i, fixed_state, params)` | the controls, an array of length `n_controls` |
| `fn_bellman_rhs` | `fn_bellman_rhs(c_i, v_cntn_i, x_cntn_i, fixed_state, params)` | the value at the decision perch, a number |
| `fn_cntn_to_dcsn` | `fn_cntn_to_dcsn(c_i, x_cntn_i, fixed_state, params)` | the point of the endogenous grid, an array of length K |
| `fn_concavity` | `fn_concavity(c_i, ddv_cntn_i, x_cntn_i, fixed_state, params)` | the numbers an upper-envelope step reads, an array of length K |

`dv_cntn_i` is the gradient of the continuation value at the point and `ddv_cntn_i` the diagonal of its matrix of second derivatives. The step is called as the one-dimensional step is, `egm_step(dv_cntn, ddv_cntn, v_cntn, x_cntn, fixed_state)`, with arrays of these shapes for N grid points:

| Array | Shape |
|---|---|
| `dv_cntn`, `ddv_cntn`, `x_cntn` | (N, K) |
| `v_cntn` | (N,) |
| the returned controls `c_hat` | (N, `n_controls`) |
| the returned values `v_hat` | (N,) |
| the returned `x_dcsn_hat` and `del_a` | (N, K) |

A coordinate that the decision leaves unchanged, such as the housing stock of a household that keeps its house, is returned unchanged by `fn_cntn_to_dcsn`, and `fn_concavity` may return 0.0 for it. The step constructs no grid: where the decision acts on fewer states than the continuation state holds, the grid lies on a set of lower dimension within the continuation states, and the reader constructs it before the call.

## 4 Composing with the arrival transition

```python
make_compose_interp(g_transition, interp_fn)
```

`g_transition(x_arvl, params)` returns the decision states $g(x)$ of an array of arrival states $x$, `params` being an array of the model's parameters. `interp_fn(xp, y_1, …, y_k, x)` interpolates k arrays given at the points `xp` at the points `x`, both sorted in increasing order, and returns the k results as a tuple. The call returns the function

```python
compose(x_dcsn_src, y_1, ..., y_k, x_arvl, params)
```

which computes the targets `g_transition(x_arvl, params)` and returns `interp_fn(x_dcsn_src, y_1, …, y_k, targets)`: the arrays `y_1` to `y_k`, given at the decision states `x_dcsn_src`, evaluated at the decision states $g(x)$ of the points $x$ of the arrival grid. For a transition $g$ without a shock this is the pullback of each decision-perch function $f$ along the transition, the composition $f \circ g$, which is what the backward builder from the decision perch to the arrival perch computes. The step computes no expectation: with a shock in the transition, the reader integrates over it. The first argument is the grid of decision states, the last two are the arrival grid and the parameter array, and every argument between them is an array to interpolate. `compose` is a Python function, and the two functions given to `make_compose_interp`, `g_transition` and `interp_fn`, may be Python functions or functions compiled by Numba. Asva supplies no interpolation function; linear interpolation by `numpy.interp` is one the reader may pass.

The example continues §2. The arrival state is the assets $k$ held before an income $y$, so that cash on hand is $m = Rk + y$, here with $R = 1$ and $y = 1$:

```python
from asva.compose_interp import make_compose_interp

def arrival_to_decision(k, params):
    R, y = params
    return R * k + y

def interp_two(xp, y1, y2, x):
    return np.interp(x, xp, y1), np.interp(x, xp, y2)

compose = make_compose_interp(arrival_to_decision, interp_two)
k = np.array([0.0, 0.5, 1.0, 2.0])
c_arvl, v_arvl = compose(m_hat, c_hat, v_hat, k, np.array([1.0, 1.0]))
print(c_arvl, v_arvl.round(4))
```

```text
[1.   1.25 1.5  2.  ] [-2.     -1.6667 -1.3333 -1.    ]
```

Consumption, $(m + 1)/2$, is linear in cash on hand, so its interpolated values are exact. The value, $-4/(m + 1)$, is not, and linear interpolation gives −1.6667 at $m = 1.5$, where the value is −1.6.

## 5 Clamping values and policies

| Function | Returns |
|---|---|
| `clamp_value(arr, nan_val=-1e10)` | a copy of `arr` with every entry that is NaN or infinite, of either sign, replaced by `nan_val`, so that a state whose value is missing is never chosen |
| `clamp_policy(arr, min_val, max_val)` | a copy of `arr` with NaN replaced by `min_val`, the entries below `min_val` by `min_val`, and the entries above `max_val`, infinity included, by `max_val` |
| `clamp_scalar(val, min_val, max_val, nan_replacement)` | one number: `nan_replacement` for NaN, `max_val` for infinity, `min_val` for minus infinity, and otherwise `val` clipped to the interval from `min_val` to `max_val` |

The three are compiled with `numba.njit`, so compiled functions may call them; the first two take one-dimensional arrays of floating-point numbers and leave them unchanged.

```python
from asva.numerics import clamp_value, clamp_policy

print(clamp_value(np.array([1.0, np.nan, np.inf, -np.inf])))
print(clamp_policy(np.array([np.nan, -1.0, 0.5, 2.0, np.inf]), 0.0, 1.0))
```

```text
[ 1.e+00 -1.e+10 -1.e+10 -1.e+10]
[0.  0.  0.5 1.  1. ]
```

## 6 The step from the records of a stage's kernels

`egm` builds the one-dimensional step of §2 from the records that the package `bellman` answers for a consumption stage, with no stage in hand:

```python
step = egm(policy, decision, savings, evaluation)
```

`policy` and `decision` are the records `stage.dcsn.builder.policy.kernels()` and `stage.dcsn.builder.bwd.kernels()` ([A builder](../Bellman-Sym/API/stage/04-builder.md) §5): for each piece of the builder, its compiled function with the names of its arguments and outputs, and the parameters' names and bound values. `egm` reads from `policy` the inverse Euler equation and the endogenous grid, and from `decision` the law of motion and the aggregation, and refuses any other record. `savings` is the grid of the continuation state and `evaluation` the grid of the decision state, both read by the caller from the stage's methods and settings: the exogenous grid of savings that the stage's `!egm` entry names by its setting `grid` and the grid that the representation at the decision builder's Evaluation names the same way, each given by its kind, `!Cartesian`, and the order and bounds written beside it, with the values the stage's settings bind ([Methodization](../Bellman-Sym/04-methodization.md) §3). The step returned, `step(value, marginal)`, takes the continuation value and its derivative as functions of the continuation state and returns the arrays of one endogenous grid step, `EndogenousGridStep`: the control, the continuation state, the value and the marginal value on the evaluation grid, and the endogenous grid with its control and value on the savings grid. The three functions the step applies are compiled once for their text, and the parameter values are passed at each call, so a new calibration needs no compilation. The lesson `tutorials/topics/kernels.ipynb` of the repository shows the records the step is built from.

## References

- Carroll, C. D. (2006). "The method of endogenous gridpoints for solving dynamic stochastic optimization problems." *Economics Letters* 91(3), 312–320.
