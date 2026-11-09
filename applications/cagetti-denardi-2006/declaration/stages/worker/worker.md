---
title: "The young worker (worker.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The young worker (worker.bl)

A young household that works earns the wage $w$ on its working ability $y$, pays the proportional payroll tax $\tau$ that finances social security, earns interest on its assets, and at the end of the year consumes and saves. It cannot borrow. The stage states equations (8) and (9) of Cagetti and De Nardi (2006),

$$
V_w(a,y,\theta)=\max_{c,a'}\bigl\{u(c)+\beta\pi_yEV(a',y',\theta')+\beta(1-\pi_y)W_r(a')\bigr\},\qquad a'=(1+r)a+(1-\tau)wy-c,\quad a'\ge0.
$$

Entrepreneurial ability does not enter the worker's income, but the household keeps it: a worker who remains young may run a business next year. The discounted continuation value $\beta\pi_yEV+\beta(1-\pi_y)W_r$ is the arrival value of `worker_ageing` in the next year, and the stage receives it as `V[>]`. The worker's arrival value is the paper's $V_w$, which `young_choice` reads as the value of working and `young_entrepreneur` as the value of defaulting. `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_wk`, `y_wk`, `θ_wk` | Assets and abilities of a young household that works this year: one that chose to work, or an entrepreneur who ran away with the capital $fk$. |
| Decision | `m`, `y`, `θ` | Cash on hand after interest and after-tax wages, and the two abilities. |
| Continuation | `a_wk_wa`, `y_wk_wa`, `θ_wk_wa` | Assets at the end of the year and this year's abilities, joined in the next year to `worker_ageing`. |

## Declarations

```bl
Xa := ℝ₊
Xm := ℝ₊₊
Y  := ℝ₊₊        :: ["working ability; the positive reals stand in for its finite grid, whose number of points is a numerical choice"]
Θ  := ℝ₊         :: ["entrepreneurial ability; the nonnegative reals stand in for its two levels, 0 and θ_e"]

σ : ℝ₊₊          :: ["relative risk aversion; the utility formula requires σ different from 1"]
r : (-1, inf)    :: ["risk-free interest rate, a price fixed by the stationary equilibrium"]
w : ℝ₊₊          :: ["wage rate, a price fixed by the stationary equilibrium"]
τ : [0,1)        :: ["proportional payroll tax financing social security, fixed by the government budget"]

𝑢(c : ℝ₊₊) := c^(1-σ)/(1-σ)        :: [id=util]
Γ(x : ℝ₊₊) := (0, x]                 :: [id=feasible]
```

The interest rate, the wage and the tax are declared parameters. Their values are set by the stationary equilibrium of the economy (Section III.F of the paper), which no stage states; `economics.md`, Section 7, states what of it the stages cannot write. The utility formula is undefined at $\sigma=1$, which the declared set does not exclude. Cash on hand is positive because the wage, ability and after-tax share are positive.

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_wk : Xa, y_wk : Y, θ_wk : Θ) : !arvl -> (m : Xm, y : Y, θ : Θ) : !dcsn] {
    m = (1 + r)*a_wk + (1 - τ)*w*y_wk    :: [id=cash_on_hand]
    y = y_wk
    θ = θ_wk
}

[id=dcsn_to_cntn, (m, y, θ, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_wk_wa : Xa, y_wk_wa : Y, θ_wk_wa : Θ) : !cntn] {
    a_wk_wa = m - c                      :: [id=savings]
    y_wk_wa = y
    θ_wk_wa = θ
}
```

The two forward blocks split equation (9) at the decision: cash on hand $m=(1+r)a+(1-\tau)wy$, then saving $a'=m-c$. The nonnegative set of `a_wk_wa` is the borrowing constraint (6). There is no shock in the stage: this year's abilities were drawn before the occupational choice, and next year's are drawn in `worker_ageing`.

```bl
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

The value adds utility to the continuation value, which already includes the discount factor and the ageing probabilities; writing $\beta$ here would discount twice. The policy chooses consumption in $(0,m]$, the correspondence `Γ` at cash on hand. The paper solves the problem by value function iteration, so the policy block states the maximisation and no first-order condition.

## Elaboration

```text
applications/cagetti-denardi-2006/declaration/stages/worker/worker.bl: ElaboratedStage('worker', symbolic)
  view ('field', None): constructed
  view ('operator', 'backward'): constructed
  view ('operator', 'forward'): constructed
```

The stage constructs all three views. Elaborated alone on 14 September 2026 with `bellman.elaborate`, which AMD-FAC-002 removed for `elaborate_stage` and the three binding verbs, from its methods file (then a YAML file; since 5 November 2026 the addition `declaration/stages/worker/methods.bl`), `declaration/settings/cagetti-denardi-2006.yml` and `declaration/calibration/cagetti-denardi-2006.yml`, it was methodized and configured, every method target resolving, and its calibration was refused because the calibration supplies no wage:

```text
elaborate(worker alone, upto='specified'): ValueError: stage 'worker', parameter 'w' (term address '8'): the calibration source supplies no value for it; every declared parameter is valued when values are bound […]; write `w: <value>` in the calibration source
```

The paper reports neither the wage nor the payroll tax, so both are absent from the calibration.

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.E, equations (6), (8) and (9); Section III.F.
