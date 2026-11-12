---
title: "The retiree (retiree.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The retiree (retiree.bl)

A retired household receives the pension and social security payment $p$, earns interest on its assets, and at the end of the year consumes and saves. It cannot borrow and cannot start a business. The stage states equations (13) and (14) of Cagetti and De Nardi (2006),

$$
W_r(a)=\max_{c,a'}\bigl\{u(c)+\beta\pi_oW_r(a')+\eta\beta(1-\pi_o)EV(a',y',\theta')\bigr\},\qquad a'=(1+r)a+p-c,\quad a'\ge0.
$$

The discounted continuation value, surviving as a retiree with probability $\pi_o$ or dying and leaving the assets to an offspring whose value is weighted by $\eta$, is the arrival value of `retiree_death` in the next year; the stage receives it as `V[>]`. The retiree's arrival value is the paper's $W_r$, which `old_choice` reads as the value of retiring and `old_entrepreneur` as the value of defaulting. `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_rt` | The assets of a household that is retired this year: a worker who aged, a retiree who survived, an old entrepreneur who retired, or one who ran away with the capital $fk$. |
| Decision | `m` | Cash on hand after interest and the pension. |
| Continuation | `a_rt_rd` | Assets at the end of the year, joined in the next year to `retiree_death`. |

## Declarations

```bl
Xa := ℝ₊
Xm := ℝ₊₊

σ : ℝ₊₊ \ {1}    :: ["relative risk aversion; the utility formula requires σ different from 1"]
r : (-1, inf)    :: ["risk-free interest rate, a price fixed by the stationary equilibrium"]
p : ℝ₊₊          :: ["pension and social security payment, 40 percent of average yearly income net of taxes"]

𝑢(c : ℝ₊₊) := c^(1-σ)/(1-σ)        :: [id=util]
Γ(x : ℝ₊₊) := (0, x]                 :: [id=feasible]
```

The pension is a declared parameter. The paper sets it at 40 percent of average yearly income (Table 5), net of taxes (Section III.G), an average over the population that the stationary equilibrium determines and that no stage can state. A retiree carries no ability: its value depends on assets alone, and the abilities of an offspring are drawn in `retiree_death`.

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_rt : Xa) : !arvl -> (m : Xm) : !dcsn] {
    m = (1 + r)*a_rt + p                 :: [id=cash_on_hand]
}

[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_rt_rd : Xa) : !cntn] {
    a_rt_rd = m - c                      :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]                      :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                             :: [id=value]
}

[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{c : Γ(m)}(𝑢(c) + V[>])   :: [id=choice]
}
```

The forward blocks split equation (14) into cash on hand $m=(1+r)a+p$ and saving $a'=m-c$, with the nonnegative set of `a_rt_rd` as constraint (6). The value adds utility to a continuation value that already includes $\beta$, the survival probability and the weight $\eta$. The policy states the maximisation over $(0,m]$.

## Elaboration

```text
applications/cagetti-denardi-2006/declaration/stages/retiree/retiree.bl: ElaboratedStage('retiree', symbolic)
  view ('field', None): constructed
  view ('operator', 'backward'): constructed
  view ('operator', 'forward'): constructed
```

The stage constructs all three views. Elaborated alone on 14 September 2026 with `bellman.elaborate`, which AMD-FAC-002 removed for `elaborate_stage` and the three binding verbs, from its methods file (then a YAML file; since 5 November 2026 the addition `declaration/stages/retiree/methods.bl`), `declaration/settings/cagetti-denardi-2006.yml` and `declaration/calibration/cagetti-denardi-2006.yml`, it was methodized and configured, every method target resolving, and its calibration was refused because the paper reports no value of the pension:

```text
elaborate(retiree alone, upto='specified'): ValueError: stage 'retiree', parameter 'p' (term address '6'): the calibration source supplies no value for it; every declared parameter is valued when values are bound […]; write `p: <value>` in the calibration source
```

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.E, equations (6), (13) and (14); Section III.G and Table 5.
