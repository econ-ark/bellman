---
title: "The retirement model"
audience: developer
type: model-note
topic: [applications]
---
# The retirement model

> [!summary]
> A finite-horizon consumption and retirement model: an agent consumes,
> works if she chooses to, and saves, until retirement, which is
> permanent. This page states the economic environment, the paper the
> stages follow, how the three stages are joined into a period and the
> periods into a trellis, the calibration, and what the stage files do not
> state. The three stage files have their own pages, `ret_choice.md`,
> `worker_cons.md` and `retiree_cons.md`.

## The economic environment

An agent lives from date 0 to date `T`. She holds assets `a ≥ 0` earning
the gross return `R`, consumes `c > 0` with utility `log c`, and
discounts the future by `β`. In a period of work she earns the wage `y`
and bears a utility cost of working. She may retire, and retirement is
permanent: a retiree never returns to work. There is no income risk, no
mortality risk and, in this version, no taste shock, so every quantity in
the files is deterministic given the state.

The model is the one Iskhakov, Jørgensen, Rust and Schjerning (2017)
solve in section 2 and Dobrescu and Shanker use as the first application
of the fast upper envelope scan. Its interest is that the option to
retire later makes the worker's continuation value non-concave: it is the
upper envelope of concave values, one for each feasible future sequence
of work and retirement. The Euler equation then has several solutions at
some levels of wealth, and a method that inverts it must select among the
candidates by value.

## The paper the stages follow

Iskhakov, Jørgensen, Rust and Schjerning (2017), section 2.1, write the
problem in resources `M`. The consumption and retirement decisions are
made at the start of each period, while interest and labour income are
paid at the end of it, so

```text
M[t+1] = R*(M[t] - c[t]) + y*d[t],     utility  log c[t] - δ*d[t],
```

with `d[t] = 1` for work and `d[t] = 0` for retirement. Their equations
(2) to (5) are the worker's and the retiree's Bellman equations, and
their equations (10) and (11) the two Euler equations. Dobrescu and
Shanker write the same model in beginning-of-period assets,
`a[t+1] = (1+r)*a[t] + d[t]*y - c[t]` with utility `log c[t] - τ*d[t+1]`,
and it is their retirement example that decomposes it into the three
stages used here.

**The staged timing and the cost.** In the stage files the choice is made
at the start of a period and governs that period: the wage enters that
period's cash on hand and the cost `δ` is charged in that period's choice
value. In both papers the choice made at a date governs the following
date's wage and its cost falls at the date of the choice. Writing `𝒲` for
the choice stage's arrival value and `V^w`, `V^r` for the two consumption
stages' decision values, the stages state

```text
𝒲[t](a)    = max( V^w[t](R*a + y) - δ,  V^r[t](R*a) )
V^w[t](w)  = max over c of  log c + β*𝒲[t+1](w - c)
V^r[t](w)  = max over c of  log c + β*V^r[t+1](w - c)
```

Substituting the first line into the second gives the papers' worker
recursion with `β*δ` in place of their cost. The two recursions therefore
describe the same model exactly when the papers' cost equals `β` times
the `δ` of these files. At the calibration below, `δ = 1` here is a cost
of `0.96` in the papers' notation. The same reading applies to the
working paper's tables, whose cost values are the ones its code charges
in the period of the wage.

## The stages and their order in a period

| Stage | Arrival | Decision | Continuation |
|---|---|---|---|
| `ret_choice` | assets `a` | `a_d = a`; the label `d` in `{work, retire}` is chosen | `a_w = a_d` on the work branch, `a_r = a_d` on the retire branch |
| `worker_cons` | assets `a_w` | cash on hand `w = R*a_w + y`; consumption `c` is chosen | savings `b = w - c` |
| `retiree_cons` | assets `a_ret` | cash on hand `w_ret = R*a_ret`; consumption `c` is chosen | savings `b_ret = w_ret - c` |

None of the three has a shock, so no expectation appears in any of their
equations. The fields the stages share fix the order: the choice stage
supplies the arrival assets of both consumption stages, so in forward
time it comes first, and value is computed backwards from the two
consumption stages to the choice.

## The period and the trellis

`period.yml` lists the three occurrences and the one rename within the
period:

```yaml
!period
name: retirement_period
stages:
  - ret_choice
  - worker_cons
  - retiree_cons
connectors:
  - {a_r: a_ret}
```

The work branch's continuation field `a_w` and the worker's arrival field
have the same name, so they join without a rename; the retire branch's
`a_r` is renamed onto the retiree's arrival assets. `trellis.yml` writes
the terminal period out, the three stages with the bequest and a second
connector from both consumption stages to the bequest's arrival field,
repeats the period nineteen times before it, and joins consecutive periods
with one mapping:

```yaml
periods:
  - stages: [ret_choice, worker_cons, retiree_cons, bequest]
    connectors:
      - {a_r: a_ret}
      - {b: a_bq, b_ret: a_bq}
  - {template: period.yml, repeat: 19}
inter_connectors:
  - {b: a, b_ret: a_ret}
```

The trellis has twenty periods, the horizon of the FUES retirement example
whose calibration and settings the application holds; `periods[0]` is the
terminal date. The bequest, `declaration/stages/bequest/bequest.bl`, arrives at `a_bq`, a name
of its own: `ret_choice` of the terminal period arrives at `a` and
`retiree_cons` at `a_ret`, so a connector to either name would join the
consumption stages to those stages as well.

A worker's savings become the next period's arrival assets at the choice
stage, and a retiree's savings the next period's retiree assets. Nothing
sends a retiree to the choice stage, which is what makes retirement
permanent: the stage files themselves do not say so.

**The retiree's arrival assets have two sources.** Within a period they
come from the retire branch, through the period's connector `{a_r: a_ret}`,
and between periods from the previous period's retiree, through the
inter-period mapping's pair `b_ret: a_ret`. The package records both joins,
`ret_choice:a_r → retiree_cons:a_ret` within each period and
`retiree_cons:b_ret → retiree_cons:a_ret` across each pair of periods: an
arrival field may take several sources, within its period and across a
pair, and the distribution of assets at `a_ret` is the sum of the two
incoming distributions (`docs/Bellman-Sym/07-trellis.md` §2). The two
sources are disjoint parts of the population, since an agent is either a
worker who retires this period or a retiree from before; the package
records the joins and does not check that they are disjoint.

## Calibration and settings

`declaration/calibration/retirement.yml` holds the benchmark of the FUES retirement
example, which states the interest rate `r = 0.02`, so that the gross
return is `R = 1 + r`:

```yaml
calibration:
  β: 0.96
  R: 1.02
  y: 20
  δ: 1
```

The working paper's tables for this application use these values with
fifty dates and costs of 0.25, 0.5, 1 and 2, read in the code's sense of
the cost, that is charged in the period of the wage. Iskhakov, Jørgensen,
Rust and Schjerning instead use twenty dates, `β = 0.98`, `y = 20`, a
cost of 1 in their own timing, and a gross return of 1 in their figures 1
and 2 and of `1/β = 1.02` in their figure 3.

`declaration/settings/retirement.yml` holds the numerical choices, which are not
part of the model: three thousand asset grid points between `1e-10` and
500 for each consumption stage, and the jump-detection threshold 1.01 of
the upper envelope scan. The horizon is not a setting of any stage: it is
the number of periods the trellis holds.

## Elaboration

The four stage files construct, the choice stage as a branching stage:

```text
applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl: ElaboratedStage('ret_choice', symbolic)
applications/retirement-choice/declaration/stages/worker_cons/worker_cons.bl: ElaboratedStage('worker_cons', symbolic)
applications/retirement-choice/declaration/stages/retiree_cons/retiree_cons.bl: ElaboratedStage('retiree_cons', symbolic)
applications/retirement-choice/declaration/stages/bequest/bequest.bl: ElaboratedStage('bequest', symbolic)
```

`load_recipe` reads the recipe `spec.yml` into twenty periods and
nineteen inter-period mappings; `elaborate_trellis` places the 61 stage
occurrences and `calibrate_trellis` calibrates all of them. The stage order
of a period is the choice stage, then the retiree's and the worker's
consumption stages, and in the terminal period the bequest.
`elaborate_trellis` reads each stage's methods file,
`declaration/stages/<stage>/methods.bl`, with its stage file at every
occurrence, as an addition to it, and `configure_trellis` binds its settings.
The stage files state the model alone: the derivative lines of the values and,
for the two consumption stages, the steps of the endogenous grid method stand
in the methods files, each line appended to the block of the stage it belongs
to, and the method words, grids and handlers at the places they type.

## What the stage files do not state

- **Taste shocks and income risk.** Iskhakov, Jørgensen, Rust and
  Schjerning (2017), section 3.1, add independent extreme-value taste
  shocks to the two choice-specific values, which gives the expected
  maximum a log-sum form and the choice probabilities a logit form, and
  reweights the Euler equation by them; the same section multiplies the
  wage by a lognormal shock. Neither is written here, and the staged
  timing would not reproduce the taste shock in any case: the shock
  deciding a date's work status would be drawn at the start of that date,
  one period after the date at which the paper's agent observes it.
- **The terminal continuation value.** It is written as a stage,
  `declaration/stages/bequest/bequest.bl`, active in the terminal period alone, whose
  continuation value `V[>]` is boundary data supplied at realization. The
  papers consume all resources at the last date, that is a continuation
  value identically zero, which the bequest states; its marginal value,
  the derivative of that value, is zero, which the bequest's marginal block
  states, and zero lies outside `ℝ₊₊`, the declared domain of the inverse
  marginal utility `𝑑𝑢𝑖𝑛𝑣` of the consumption stages, so at that date the
  maximization gives consumption equal to cash on hand while the
  endogenous-grid statements cannot be used. The FUES retirement example instead supplies the
  logarithm of savings and its derivative after the last date.
- **The first date.** The papers' agent starts as a worker and makes no
  choice at date 0. The trellis here repeats one period, so its earliest
  period also begins with a choice; a faithful first date either omits
  that stage or fixes its control to `work`.
- **Ties in the discrete choice.** Where the two branch values are equal,
  both labels attain the maximum. The files state no tie-break, and where
  the values cross the arrival value has a kink at which the marginal
  value the choice stage selects is a one-sided derivative.
- **Anything above the stage.** The structural estimation of the paper,
  which nests this solution inside a likelihood, is outside the model
  these files state.

## Differences from the example's code

The stage files state the model; the FUES retirement example's code
differs from them at two points a reader comparing the two will meet.
First, the code charges the work cost inside the worker's consumption
operators and then takes a plain maximum in the choice step, whereas the
files charge it in the choice stage's value selection. Both charge it
once, and the resulting choice value is the same. Second, the retiree's
step builds its endogenous grid in arrival assets, dividing by the gross
return, and then evaluates it at cash on hand; running one backward step
from the example's own terminal data returns `R` times the policy those
data imply, at each of the four grid points examined. The worker's step,
whose endogenous grid is in cash on hand, is exact at the same points.

## References

- Iskhakov, F., Jørgensen, T. H., Rust, J., and Schjerning, B. (2017).
  "The endogenous grid method for discrete-continuous dynamic choice
  models with (or without) taste shocks." *Quantitative Economics* 8(2),
  317–365. Section 2.1 (equations (1) to (5)), section 2.2 (equations
  (10) and (11), the terminal date and the credit-constrained point),
  section 3.1 (equations (12) to (15)) and section 3.2 (equation (17)).
- Dobrescu, L. I., and Shanker, A. "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN No.
  4181302. Application 1 states this model, its Euler equations and the
  scan, and its retirement example supplies the staged form, the
  calibration and the numerical settings used here.
- Phelps, E. S. (1962). "The accumulation of risky capital: a sequential
  utility analysis." *Econometrica* 30(4), 729–743. The closed-form
  retiree policy under log utility.
- Carroll, C. D. (2006). "The method of endogenous gridpoints for solving
  dynamic stochastic optimization problems." *Economics Letters* 91(3),
  312–320.
