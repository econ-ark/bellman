---
title: "The old entrepreneur (old_entrepreneur.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The old entrepreneur (old_entrepreneur.bl)

An old household that stays in business faces the problem of the young entrepreneur with the differences that follow. Working ability is neither a state nor a source of income for the old, and the probability of leaving the household's problem is the probability of dying, $1-\pi_o$, rather than of ageing. When it dies, its offspring enters the model with its assets, and it weighs the offspring's value by $\eta$. If it ran away with the fraction $f$ of its working capital, it would retire, and a retiree cannot start a business again. The stage states equations (11) and (12) of Cagetti and De Nardi (2006) with the budget (4) and the constraints (6) and (7):

$$
W_e(a,\theta)=\max_{c,k,a'}\bigl\{u(c)+\beta\pi_oEW(a',\theta')+\eta\beta(1-\pi_o)EV(a',y',\theta')\bigr\}
$$

subject to $a'=(1-\delta)k+\theta k^\nu-(1+r)(k-a)-c$, $a'\ge0$, $k\ge0$ and

$$
u(c)+\beta\pi_oEW(a',\theta')+\eta\beta(1-\pi_o)EV(a',y',\theta')\ \ge\ W_r(fk).
$$

The discounted continuation value $\beta\pi_oEW+\eta\beta(1-\pi_o)EV$ is the arrival value of `entrepreneur_death` in the next year, received here as `V_repay[>]`. Working ability does not enter the old entrepreneur's problem. The structure of the file and the reading of each statement are those of `young_entrepreneur.md`; `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_oe`, `θ_oe` | Assets and ability of an old household that stays in business. |
| Decision | `a`, `θ` | The same quantities, at which capital `k`, consumption `c` and repayment `d` are chosen. |
| Continuation, repay | `a_oe_ed`, `θ_oe_ed` | Assets at the end of the year and this year's ability, joined in the next year to `entrepreneur_death`. |
| Continuation, default | `a_oe_rt` | The capital kept by an entrepreneur who runs away, joined to the arrival field of `retiree` in the same year. |

## Declarations

The parameters `σ`, `δ`, `ν`, `f` and `r`, the utility `𝑢` and the correspondence `Γ` are declared as in `young_entrepreneur.bl`; the sets are `Xa` and `Θ`.

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_oe : Xa, θ_oe : Θ) : !arvl -> (a : Xa, θ : Θ) : !dcsn] {
    a = a_oe
    θ = θ_oe
}

[id=dcsn_to_cntn, (a, θ, k : ℝ₊ @ !ctrl, c : ℝ₊₊ @ !ctrl, d : !ctrl @ {repay, default}) : !dcsn -> ()] {
    [label=repay, () -> (a_oe_ed : Xa, θ_oe_ed : Θ) : !cntn] {
        a_oe_ed = (1 - δ)*k + θ*k^ν - (1 + r)*(k - a) - c       :: [id=budget]
        θ_oe_ed = θ
    }
    [label=default, () -> (a_oe_rt : Xa) : !cntn] {
        a_oe_rt = f*k                                          :: [id=kept_capital]
    }
}
```

The repay branch is the budget (4). The default branch keeps $fk$ and leads to retirement, so its continuation value is the retiree's value $W_r(fk)$.

```bl
[id=cntn_to_dcsn, (V_repay[>] : ℝ @ !vlu, W_r[>] : ℝ @ !vlu, c, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = (𝑢(c) + V_repay[>], W_r[>])[d]                         :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                                                  :: [id=value]
}

[id=policy, (V_repay[>] : ℝ @ !vlu, W_r[>] : ℝ @ !vlu) : !cntn -> (k : ℝ₊ @ !ctrl, c : ℝ₊₊ @ !ctrl, d : {repay, default} @ !ctrl) : !dcsn] {
    (k, c) = argmax_{k, c : Γ(a, θ, k)}(𝑢(c) + V_repay[>])      :: [id=optimality]
    𝑢(c) + V_repay[>] >= W_r[>]                                 :: [id=enforcement]
    d = argmax_{d}(𝑢(c) + V_repay[>], W_r[>])                   :: [id=repayment]
}
```

The enforcement statement is constraint (12). As for the young entrepreneur, the maximisation and the constraint are read together as problem (11), the binder of the maximisation carrying only `Γ`; where the constraint binds the two branch values are equal, and the file states no rule for that tie, the rule intended being that a household indifferent between the two repays. The working-paper version of the article lists the old entrepreneur's constraints as (4), (7) and (12); the published text adds $a'\ge0$, which `Γ` imposes here.

## Elaboration

```text
applications/cagetti-denardi-2006/declaration/stages/old_entrepreneur/old_entrepreneur.bl:20:1-28:2: block 'dcsn_to_cntn' lists the controls 'k', 'c', 'd' beside its branches; this version of the package constructs a branching block whose branches state equations alone and whose label coordinate is its one control, or a shock over a finite set in a stage that chooses nothing (docs/Bellman-Sym/05-branching.md) (address 'dcsn_to_cntn'; rule not-constructed)
```

No view is constructed. The first missing construct is a branching block that lists continuous controls beside its label. Scratch copies of 14 September 2026 found the same sequence of refusals as for `young_entrepreneur.bl`: with the branches written as one block, "this statement has a Tuple as its left side" at `policy.optimality`; without that statement, "this statement has a Add as its left side" at `policy.enforcement`; without both, rule `output-defined`, "the relation for 'old_entrepreneur:dcsn:k' requires one formula for k[>]"; with separate maximisations over capital and consumption, rule `output-defined`, a circular dependence between them. The missing constructs are a branching block with continuous controls beside its label, a joint maximization with a tuple on its left side, and an inequality statement whose left side is an expression; no road-map brief records the last two.

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.D and Section III.E, equations (4), (6), (7), (11) and (12).
