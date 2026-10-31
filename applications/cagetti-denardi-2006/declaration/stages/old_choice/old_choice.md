---
title: "The old entrepreneur's choice to continue or retire (old_choice.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The old entrepreneur's choice to continue or retire (old_choice.bl)

An old household that ran a business in the previous year starts the year with assets $a$ and knows its entrepreneurial ability $\theta$. It chooses whether to keep the business going or to retire; a retiree cannot start a business again. The stage states equation (10) of Cagetti and De Nardi (2006),

$$
W(a,\theta)=\max\{W_e(a,\theta),\,W_r(a)\},
$$

where $W_e$ is the value of staying in business this year (the stage `old_entrepreneur`) and $W_r$ the value of retirement (the stage `retiree`). Working ability is not a state of the old, who do not work. The stage has the form of `young_choice.bl`; `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_oc`, `θ_oc` | The assets and this year's entrepreneurial ability of an old entrepreneur: a young entrepreneur who aged, or an old entrepreneur who survived. |
| Decision | `a`, `θ` | The same quantities. |
| Continuation, entrepreneur | `a_oe`, `θ_oe` | The arrival fields of `old_entrepreneur`, joined by their names. |
| Continuation, retiree | `a_oc_rt` | Joined to the arrival field `a_rt` of `retiree`. |

## Declarations

```bl
Xa := ℝ₊
Θ  := ℝ₊         :: ["entrepreneurial ability; the nonnegative reals stand in for its two levels, 0 and θ_e"]
```

The nonnegative reals stand in for the two ability levels, as in the other stages. The stage has no parameters.

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_oc : Xa, θ_oc : Θ) : !arvl -> (a : Xa, θ : Θ) : !dcsn] {
    a = a_oc
    θ = θ_oc
}

[id=dcsn_to_cntn, (a, θ, d : !ctrl @ {entrepreneur, retiree}) : !dcsn -> ()] {
    [label=entrepreneur, () -> (a_oe : Xa, θ_oe : Θ) : !cntn] {
        a_oe = a
        θ_oe = θ
    }
    [label=retiree, () -> (a_oc_rt : Xa) : !cntn] {
        a_oc_rt = a
    }
}
```

The control `d` takes the labels `{entrepreneur, retiree}`. A household that stays in business keeps its assets and its ability for the old entrepreneur's problem; one that retires keeps its assets alone, because a retiree's value does not depend on entrepreneurial ability.

```bl
[id=cntn_to_dcsn, (W_e[>] : ℝ @ !vlu, W_r[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = (W_e[>], W_r[>])[d]              :: [id=choice_value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                             :: [id=value]
}

[id=policy, (W_e[>] : ℝ @ !vlu, W_r[>] : ℝ @ !vlu) : !cntn -> (d : {entrepreneur, retiree} @ !ctrl) : !dcsn] {
    d = argmax_{d}(W_e[>], W_r[>])       :: [id=choice]
}
```

`W_e[>]` and `W_r[>]` are the arrival values of `old_entrepreneur` and `retiree`. The decision value `V` is the paper's $W(a,\theta)$, the value that `entrepreneur_ageing` and `entrepreneur_death` read as `W_old[>]`. Both the selection and the maximisation list the values in the order of the labels.

## Elaboration

Elaborated alone, `elaborate_stage(load_stage("applications/cagetti-denardi-2006/declaration/stages/old_choice/old_choice.bl"))` constructs every builder, and the three queries of a branching stage answer:

```text
kind(stage)          branching
branches(stage)      entrepreneur: (old_choice:cntn:a_oe, old_choice:cntn:θ_oe)   retiree: (old_choice:cntn:a_oc_rt,)
combination(stage)   choice
```

The label `d` is chosen by the household, so the branches combine by the choice of the policy.

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.E, equation (10).
