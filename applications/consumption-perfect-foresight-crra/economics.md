---
title: "The perfect foresight consumption model with CRRA utility"
audience: developer
type: model-note
topic: [applications]
---
# The perfect foresight consumption model with CRRA utility

> [!summary]
> A household with constant relative risk aversion knows its future income
> with certainty. Each period it chooses its consumption out of its market
> resources, saves the rest at a fixed gross return, and may borrow against
> the income it will receive, whose present value is its human wealth. Its
> consumption function is known in closed form: a fixed fraction of its total
> wealth, nonhuman and human. This page states the problem in levels and
> normalized by permanent income, the Bellman equation the stage writes, the
> closed-form solution and the domain on which it holds, the conditions under
> which the infinite-horizon solution exists and how the files refuse a
> calibration that breaks them, the calibration, and the two numerical
> routes. The stage file itself is explained in
> `declaration/stages/perfect_foresight/perfect_foresight.md`.

## The model and its source

The model is that of Carroll and Lujan Solis, *A Gentle Introduction to
Intertemporal Choice*, chapter "Consumption Under Perfect Foresight and CRRA
Utility", at intertemporal-choice.github.io (read on 8 November 2026),
sections 2 and 3. The chapter derives the finite-horizon solution, its
infinite-horizon limit and the conditions under which that limit exists, and
gives the numerical example that this folder's calibration takes. The
notation follows the buffer-stock stage of this repository,
`applications/buffer-stock/`, of which this stage is the case without income
shocks: the growth factor of permanent income is written $\Gamma$ where the
chapter writes $G$, and a lowercase letter is a variable normalized by
permanent income, as in the chapter.

## The problem

The household lives from period $t$ to period $T$, or forever. It receives
permanent income $P_t$, which grows by the factor $\Gamma$ each period, holds
market resources $M_t$, consumes $C_t$ and saves the rest at the gross
interest factor $R$:

$$
A_t = M_t - C_t, \qquad B_{t+1} = R\,A_t, \qquad M_{t+1} = B_{t+1} + P_{t+1},
\qquad P_{t+1} = \Gamma\,P_t .
$$

Its preferences are $u(C) = C^{1-\rho}/(1-\rho)$ with $\rho > 1$, discounted
by the factor $\beta \in (0, 1)$ per period. It may borrow, but must be able
to repay: the present value of its consumption is at most its total wealth,
the sum of its nonhuman wealth $B_t$ and its human wealth
$H_t = \sum_{n \ge 0} P_{t+n}/R^n$, the present value of its current and
future income.

Dividing by permanent income, with $m_t = M_t/P_t$ and likewise for the other
variables, the budget constraint is

$$
a_t = m_t - c_t, \qquad m_{t+1} = (R/\Gamma)\,a_t + 1 .
$$

In the infinite horizon normalized human wealth is
$h = \sum_{n \ge 0} (\Gamma/R)^n = 1/(1 - \Gamma/R)$, and total wealth is
$w = m - 1 + h = m - L$, where $L = 1 - h$ is the natural borrowing limit on
market resources. The natural borrowing constraint, $c < m - L$, is the
feasible set of the stage. Along the law of motion total wealth evolves as
$w_{t+1} = (R/\Gamma)(w_t - c_t)$, so consumption with $0 < c < w$ keeps the
next period's total wealth positive, and a saving $a > L$ gives next-period
resources $m > L$.

## The Bellman equation

With $V_t(M_t, P_t) = P_t^{1-\rho}\,v_t(m_t)$, the normalized problem is

$$
v(m) = \max_{c \in \Gamma_c(m)} \; u(c) + \beta\,\Gamma^{1-\rho}\,v(m'),
\qquad m' = R\,(m - c)/\Gamma + 1 .
$$

The stage writes it in its blocks. The arrival line $m = Rk/\Gamma + 1$
carries the saving $k$ of the previous period, normalized by that period's
permanent income, into this period's resources; the decision line
$a = m - c$ is the saving; the decision value $V = u(c) + \beta\,V_\succ$
reads the continuation value $V_\succ$ at the saving; and the arrival value
$V_\prec = \Gamma^{1-\rho}\,V$ is the decision value in the units of the
previous period's permanent income, which that period reads as its
continuation value. The policy block states the maximization alone.

## The solution in closed form

The Euler equation $u'(C_t) = \beta R\,u'(C_{t+1})$ gives
$C_{t+1}/C_t = (R\beta)^{1/\rho}$, the absolute patience factor, so
consumption grows at a constant rate whatever the household's wealth.
Substituting this path into the intertemporal budget constraint gives
consumption as a fixed fraction of total wealth, with the return patience
factor $q = (R\beta)^{1/\rho}/R$:

$$
c(m) = \kappa\,(m - L), \qquad \kappa = 1 - q, \qquad
h = \frac{1}{1 - \Gamma/R}, \qquad L = 1 - h,
$$

the chapter's equations (32) and (35), on the domain $m > L$, where total
wealth is positive. Concavity of $u$ and the present-value budget make this
path optimal, and its utility is finite because the discounted utility terms
have the ratio $q < 1$. The discounted total wealth left after $n$ periods is
$q^n w$, which tends to zero: the household consumes all its total wealth in
present value.

The value is known in closed form too. Along the optimal path normalized
consumption grows by the factor $(R\beta)^{1/\rho}/\Gamma$, so the normalized
discounted utility terms have the ratio $q$, and

$$
v(m) = \frac{u(c(m))}{\kappa} = \kappa^{-\rho}\,\frac{(m - L)^{1-\rho}}{1-\rho},
\qquad v'(m) = u'(c(m)),
$$

on $m > L$, the second equation the envelope condition. The arrival value is
the decision value at the resources the law of motion gives, normalized by
$\Gamma^{1-\rho}$,

$$
V_\prec(k) = \Gamma^{1-\rho}\,v(Rk/\Gamma + 1)
= R^{1-\rho}\,\kappa^{-\rho}\,\frac{(k - L)^{1-\rho}}{1-\rho},
$$

on $k > L$, since total wealth at those resources is $(R/\Gamma)(k - L)$. Its
derivative is $R\,\Gamma^{-\rho}\,v'(Rk/\Gamma + 1)$, the factor $R/\Gamma$ of
the law of motion times the normalization $\Gamma^{1-\rho}$. The second
derivatives, which bound the error of linear interpolation, are
$|v''(m)| = \rho\,\kappa^{-\rho}(m - L)^{-\rho-1}$ and
$|V_\prec''(k)| = \rho\,R^{1-\rho}\kappa^{-\rho}(k - L)^{-\rho-1}$.

Over a finite horizon of $N$ periods the coefficients are dated: human wealth
is $h_N = \sum_{n=0}^{N-1} (\Gamma/R)^n$, the marginal propensity to consume
is $\kappa_N = 1/\sum_{n=0}^{N-1} q^n$, and in the last period the household
consumes its resources, $c = m$. Repeating the stationary stage with constant
$h$ and $\kappa$ does not construct that problem, and no finite-horizon claim
is made here.

## The conditions

Two conditions, the chapter's equations (15) and (16), make the
infinite-horizon solution well defined.

- **The return impatience condition**, $q < 1$: the marginal propensity to
  consume $\kappa = 1 - q$ is positive.
- **The finite human wealth condition**, $\Gamma < R$: human wealth is
  finite. At $\Gamma = R$ its formula divides by zero, and at $\Gamma > R$ the
  formula gives a finite negative number that is not human wealth.

Neither the growth impatience condition nor a normalized discount factor
$\beta\,\Gamma^{1-\rho} < 1$ is needed for the closed form. At $\beta = 0.9$,
$\rho = 2$, $R = 1.04$ and $\Gamma = 0.5$ the normalized discount factor is
1.8 and the closed form satisfies the Bellman and Euler equations and the
present-value budget. The closed form holds for every $\rho > 1$; logarithmic
utility, $\rho = 1$, needs its own utility and its own convention for the
value, and is not this stage.

The files state each condition so that a calibration that breaks it is
refused, with the condition named:

| Condition | How it is stated | Where it is refused |
|---|---|---|
| $\Gamma < R$ | the declared set of the growth factor, `Γ : (0, R)` | `calibrate`, which decides an interval whose endpoints are parameters |
| $q < 1$ | the declared set of the discount factor, `β : ℝ₊₊ @ (0, R^(ρ-1))`, whose upper bound $R^{\rho-1}$ is the condition written for $\beta$, and the set that the definition of the return patience factor declares, `q : (0,1) := (β*R)^(1/ρ)/R` | `calibrate`, under each methods file; a discount factor one rounding step below the bound, at which $q$ computes to one, is refused by the set of $q$ |
| $\rho > 1$ | the declared set `ρ : (1, inf)` | `calibrate` |
| finite parameters | the declared sets of the four parameters | `calibrate` |
| $m > L$, and $k > L$ at the arrival perch | the domain of each function of the closed form | the module, at each evaluation |

## Calibration

`declaration/calibration/perfect_foresight.yml` holds the example of the
chapter's section 4.1, an interest rate $r = 0.04$, a time preference rate
$\vartheta = 0.04$, income growth $g = 0.02$ and $\rho = 2$, written as the
factors the stage declares: $R = 1 + r = 1.04$,
$\beta = 1/(1 + \vartheta) = 1/1.04$ and $\Gamma = 1 + g = 1.02$. At these
values

| quantity | value |
|---|---|
| return patience factor $q = (R\beta)^{1/\rho}/R$ | $1/1.04 \approx 0.9615$ |
| marginal propensity to consume $\kappa = 1 - q$ | $0.04/1.04 \approx 0.0385$ |
| human wealth $h = 1/(1 - \Gamma/R)$ | $52$ |
| natural borrowing limit $L = 1 - h$ | $-51$ |
| growth patience factor $(R\beta)^{1/\rho}/\Gamma$ | $1/1.02 \approx 0.9804$ |

so a household with no assets, $m = 1$, consumes $c = \kappa h = 2$, twice
its permanent income. A second calibration, $\beta = 0.9$, $\rho = 2$,
$R = 1.04$ and $\Gamma = 1.01$, gives $h = 1/(1 - 1.01/1.04) \approx 34.7$.

## What the stage file cannot state

- **The solution.** The stage file states the problem; the closed form is a
  method's. The addition `methods.bl` types `!explicit` on the policy builder
  and on the two value builders. The line of each block writes the output as
  an explicit function of the state of its own perch, and stands in place of
  the builder's declared line, the maximization or the value aggregation, at
  the operative level; `stage.declared` keeps the declared lines. `!explicit`
  gives each of those builders' Evaluations the closed form, `!closed_form`.
  Each value block also writes its marginal in closed form,
  $v'(m) = \kappa^{-\rho}(m - L)^{-\rho}$ and
  $V_\prec'(k) = R\,\Gamma^{-\rho} v'(Rk/\Gamma + 1)$.
- **The domain of the solution.** The ambient sets of the stage are the real
  line, and the feasible set is empty at $m \le L$. The closed form holds on
  $m > L$, and the module refuses an evaluation elsewhere.
- **The horizon.** The stage is one period of the stationary problem.

## The two numerical routes

The module `code/closed_form_check.py` binds each methods file through
`elaborate`, `methodize`, `calibrate` and `configure`.

The closed-form route reads the consumption function, the decision value and
the arrival value, with the two marginals, from the compiled kernels of the
three explicit blocks, and writes no formula of them. It checks them against the stage file's own
blocks, through their compiled kernels: the residual of the Bellman
equation, the residual of the arrival value's normalization, the relative
residual of the Euler equation, feasibility and the present-value budget. It
also compares them with the formulas of this page written in Python, which
the module labels as test references.

The gridded route binds `methods.egm.bl`: the endogenous grid method on the
policy builder with its grid of savings, `!Linear` at the policy builder's
Evaluation, read between the pairs the method computes, and the derivative
lines of the two value builders, the envelope condition $D_mV = c^{-\rho}$ and
the arrival marginal $D_kV_\prec = R\,\Gamma^{-\rho} D_mV$. The module iterates
the method to its fixed point on the compiled kernels of those lines, from a
first iterate that consumes half of total wealth. It refuses a calibration at
which $q \ge 1$, a grid of savings that starts at or below $L$, an
intermediate value that is not finite, an extrapolation that leaves the
feasible set and an iteration that reaches its limit without converging.
Beyond its pairs the policy continues its end secants, an extension that only
the policy comparison and an explicit request, `evaluate(m, extrapolate=True)`
of the fixed point, select, and that is reported at each use; it supplies no
claim of accuracy. The linear interpolant of a linear function is
exact, so the route reaches the closed form at five points of the grid as at
five hundred, and the comparison of the value function's interpolation by the
module's Linear and PCHIP evaluators, on 5, 50 and 500 nodes, is the test of
interpolation accuracy. Near the borrowing limit, on total wealth from
$10^{-3}$ to 1, the converged policy of a grid of savings that starts just
above $L$ is compared with the closed form by relative policy and Euler
errors and by a Bellman residual scaled by the value.

The notebook `code/closed-form-and-grid.ipynb` shows each step and each
comparison.

## References

Carroll, C. D. and Lujan Solis, A. E. *A Gentle Introduction to Intertemporal
Choice*, "Consumption Under Perfect Foresight and CRRA Utility".
https://intertemporal-choice.github.io/content/consumption/perfforesightcrra.
Read on 8 November 2026.
