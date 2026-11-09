---
title: "Savings and retirement choice with pension assets"
audience: developer
type: model-note
topic: [applications]
---
# Savings and retirement choice with pension assets

> [!summary]
> Application 1 of Dobrescu and Shanker (2024), *Using Inverse Euler Equations
> to Solve Multidimensional Discrete-Continuous Dynamic Models*, §6.1 (pp. 18
> to 20). A worker holds financial and pension assets, earns a stochastic wage,
> consumes, contributes to the pension under an incentive, and chooses whether
> to work next period; a retiree receives the pension balance as a lump sum
> and a benefit each period. Three stages: `worker_saving`, `retire_choice`,
> `retiree_saving`. The policy blocks state the maximizations; the methods
> file beside each stage file, `declaration/stages/<stage>/methods.bl`, an
> addition to it, writes the first-order conditions in the spelling of the
> Kuhn–Tucker condition at the decision perch with the complementary-slackness
> clause (`docs/Bellman-Sym/10-constraints.md` §3), the paper's equations (16)
> to (20).

## The model, in the paper's equations

The state of a worker is $(m_f, m_p, w)$, financial assets, pension assets and
the earnings draw; the choices are consumption $c$ and the pension
contribution $c_p$, and the post-states are $y_f = m_f - c - c_p$ and
$y_p = m_p + c_p + \chi(c_p)$ with the incentive $\chi(x) = \chi_s \log(1 + x)$
(equation 15 and the factor $1 + \chi'(c_p)$ of equation 17). Financial assets
move by equation (13), $m_f' = (1 + r_f)\, y_f + w'$ for a worker and
$m_f' = (1 + r_f)\, y_f + w_R + (1 + r_p)\, y_p$ for a retiree, who receives
the pension balance once and the benefit $w_R$ each period; pension assets by
equation (14), $m_p' = (1 + r_p)\, y_p$ for a worker and zero for a retiree. A
worker chooses at the end of the period whether to work next period,
$z' = d\, z$, so a retiree never works again. Utility is CRRA with $\rho > 1$
and the discount factor is $\beta$.

`worker_saving.bl`'s policy block states the worker's maximization over
consumption and the contribution. Its first-order conditions, equations (16)
to (20), are the two lines the worker's methods file,
`declaration/stages/worker_saving/methods.bl`, adds to the policy builder
under the method `!time_iteration`, with the decision grid on which they are
solved: the financial Euler equation
$u'(c) = \beta\, \partial_{y_f} V^{\succ}$ with the bound
$y_f \ge 0$ and its multiplier $\mu_f$ (18), and the pension Euler equation
$u'(c) = \beta\,(1 + \chi'(c_p))\, \partial_{y_p} V^{\succ}$ with the bounds
$0 \le c_p \le w$ and their multipliers $\mu_p$ (19) and $\mu_{\bar p}$ (20).
The shadow values (21) and (22) are the derivative lines the same file adds
to the two value builders:
$\partial_{m_f} V = u'(c)$ at the decision perch and
$\partial_{m_p} V = \beta\, \partial_{y_p} V^{\succ}$ for a worker, and
$(1 + r_p)\, u'(c)$ for a retiree, who consumes the balance. The return
factors stand on the arrival value builders' derivative lines, as in the
other applications.

## The period and the trellis

The stage files stand under `declaration/stages/`. `period.yml` lists the three
stages; `retire_choice` has no arrival perch and is entered at its decision
perch, and the period's connector `{y_f: y_f_d, y_p: y_p_d}` joins the
worker's post-states `y_f` and `y_p` to its decision states. `trellis.yml`
holds fifteen periods, the number the paper solves (§6.1). Its terminal
period, `periods[0]`, is written out with a fourth stage,
`declaration/stages/terminal/terminal.bl`, a connector from the six
continuation fields that leave the period, both branches of
`retire_choice` and the retiree's own savings, to the terminal stage's
arrival fields `y_f_T` and `y_p_T`, and the connector of `period.yml`
written again; the fourteen earlier periods repeat `period.yml`. One inter-period mapping carries the work branch to next
period's `worker_saving`, and the retire branch and the retiree's savings
to next period's `retiree_saving`, so no path leads back to work. The
model states no terminal value, so the terminal stage writes the boundary
data alone: its continuation value is zero, and its methods file,
`declaration/stages/terminal/methods.bl`, states its two derivatives as
zero. AAS to confirm. The recipe
`spec.yml` names the slot `$fill` for the calibration of the two
saving stages, since no calibration file is written (below), and the
settings files `declaration/settings/<stage>.yml` for their decision grids,
whose values are placeholders until AAS supplies them.

## What the stage files do not state

- **The contribution cap** (constraint iv, $c_p \le w$, multiplier
  $\mu_{\bar p}$ of equation 20) is stated by the two-sided clause of
  `euler_pension`, the second line the methods file adds to the policy builder,
  `⟂ 0 <= c_p <= w_d`, which with the feasibility
  correspondence $\Gamma_p(w) = [0, w]$ of the declared maximization
  transcribes equations (17), (19) and (20). The residual of that line is
  $\mu_p - \mu_{\bar p}$, the difference of the multipliers of the two bounds:
  nonnegative where the contribution is zero, zero between the bounds and
  nonpositive at the cap. The paper prints equation (17) without $\beta$,
  which the file writes. What the file does not state is a check of the chain
  $0 \le c_p \le w_d$ against the declared set of $c_p$; none is made.
- **The incentive function.** The build of the paper prints equation (15) as
  $y_p = m_p + \chi(c_p)$ and $\chi(x) = 1 + \bar\chi \log(1 + x)$, and the
  derivative in (17) as $1 + \chi'(c_p)$; the file follows the derivative,
  $y_p = m_p + c_p + \chi(c_p)$ with $\chi(x) = \chi_s \log(1 + x)$.
  AAS to confirm.
- **The calibration.** The paper takes its baseline from a cited paper whose
  reference the build does not resolve; no calibration file is written until
  the values are supplied.
