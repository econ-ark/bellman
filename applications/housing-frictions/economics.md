---
title: "Housing investment with adjustment frictions"
audience: developer
type: model-note
topic: [applications]
---
# Housing investment with adjustment frictions

> [!summary]
> Application 2 of Dobrescu and Shanker (2024), *Using Inverse Euler Equations
> to Solve Multidimensional Discrete-Continuous Dynamic Models*, §6.2 (pp. 21
> to 23). A household holds financial assets and a house; each period it
> chooses whether to adjust the house, then consumption, and the adjuster the
> new house at a cost proportional to its value. Three stages, in the pattern
> of `applications/durables/`, which writes the same model in the forms of the
> FUES paper: `house_choice`, `keeper_saving`, `adjuster_saving`. The policy
> blocks are written in the spelling of the Kuhn–Tucker condition at the
> decision perch with the complementary-slackness clause, the paper's
> equations (28) and (29).

## The model, in the paper's equations

The state is $(w, m_f, m_h)$, the earnings shock, financial assets and the
housing stock; the post-state is $(y_f, y_h)$. Financial assets move by
$m_f' = (1 + r)\, y_f + w'$ with $w' = W \eta'$ and $\eta'$ equal to $0.1$ or
$1$ with equal probability; housing brings no return, $m_h' = y_h$. The
discrete choice $d$ allows adjustment, $(y_h - m_h)(1 - d) = 0$; an adjuster
sells the house at its value and buys $y_h$ at the price $1 + \tau$, so that
consumption is $c = m_f + d\, m_h - y_f - d\,(1 + \tau)\, y_h$ (equation 24).
Utility is $(c^{1-\rho} - 1)/(1 - \rho) + (1 - \alpha) \log y_h$ (equation
23, the exponent read as $1 - \rho$, since $\rho = 3$ and the printed
$c^{\rho - 1}$ would be convex; AAS to confirm).

The financial Euler equation (28) is the statement after the maximization in
both saving policy blocks, $u_c(c) = \beta\, \partial_{y_f} V^{\succ}$ with
the bound $y_f \ge 0$, the derivative of the continuation value read by the
term `D_{y_f_kp}V[>]` or `D_{y_f_adj}V[>]`; the housing Euler equation of an
adjuster (29) is the statement after it in `adjuster_saving.bl`,
$(1 + \tau)\, u_c(c) = u_h(y_h) + \beta\, \partial_{y_h} V^{\succ}$, where
$\partial_{y_h} V^{\succ}$ is the shadow value of housing (30): on the choice
stage, the keeper's marginal value of housing,
$u_h(h) + \beta\, \partial_{y_h} V^{\succ}$, or the adjuster's marginal value
of resources, the house being sold at its value. The derivative lines of the
value builders, the envelope conditions among them, stand in the marginal
blocks of `declaration/methods/marginals_<stage>.bl`, which each stage's
methods file binds with `!marginals`.

## The period and the trellis

The stage files stand under `declaration/stages/`. The two saving stages draw
nothing before their choice and begin at their decision perch, so `period.yml`
lists the three stages and one connector, `{w_kp: m_d, h_kp: h_d, w_adj: m}`,
which joins the keep branch's `w_kp` and `h_kp` to the decision states of
`keeper_saving` and the adjust branch's `w_adj` to that of `adjuster_saving`.
`trellis.yml` holds sixty periods, one per date, as
`declaration/calibration/housing_frictions.yml` states (T = 60, §6.2.4). Its
terminal period, `periods[0]`, is written out with a fourth stage,
`declaration/stages/terminal/terminal.bl`, and two connectors, the first from
both saving stages' post-states to the terminal stage's arrival fields `y_f_T`
and `y_h_T` and the second that of `period.yml`; the fifty-nine earlier
periods repeat `period.yml`. The terminal stage keeps the arrival block that
copies `y_f_T` and `y_h_T` to its decision states: it writes no block from
decision to continuation, so that block alone declares its states. One inter-period
mapping carries both saving stages' post-states to next period's
`house_choice`. Neither the application nor §6.2 states a terminal value:
the terminal stage's continuation value is the zero boundary data and its
two derivatives are zero, as the marginal block of
`declaration/methods/marginals_terminal.bl` states. AAS to confirm. The
earnings level `W` is 1.0 in every period until the paper's age profile is
supplied.
