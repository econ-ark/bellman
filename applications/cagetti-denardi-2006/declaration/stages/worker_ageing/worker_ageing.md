---
title: "Ageing of a young worker (worker_ageing.bl)"
audience: developer
type: model-note
topic: [applications]
---
# Ageing of a young worker (worker_ageing.bl)

A household that worked in the previous year starts this year by learning its new abilities and whether it has aged. With probability $\pi_y$ it remains young and makes the occupational choice again; with probability $1-\pi_y$ it becomes old, and an old worker is retired. Its working ability $y$ and entrepreneurial ability $\theta$ follow independent Markov chains. The stage states the continuation value of the worker's problem (8) of Cagetti and De Nardi (2006),

$$
\beta\pi_yE\bigl[V(a',y',\theta')\mid y,\theta\bigr]+\beta(1-\pi_y)W_r(a'),
$$

where $V$ is the value of the young before the occupational choice (the stage `young_choice`) and $W_r$ the retiree's value (the stage `retiree`). The stage has no decision; it holds the two random events between two years and the discount factor. `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_wa`, `y_wa`, `θ_wa` | The worker's assets at the end of the previous year and that year's abilities, joined from `worker` by the inter-period connector. |
| Decision | `a`, `y`, `θ` | Assets and this year's abilities, after the draws. |
| Continuation, young | `a_wa_yc`, `y_wa_yc`, `θ_wa_yc` | Joined to the arrival fields of `young_choice`. |
| Continuation, old | `a_wa_rt` | Joined to the arrival field of `retiree`. |

## Declarations and laws

```bl
β      : (0,1)   :: ["discount factor"]
π_y    : [0,1]   :: ["probability that a young person remains young for another period"]
P_y    : [0,1]   :: ["transition matrix of working ability; the set of one probability stands in for the matrix"]
y_grid : ℝ₊₊     :: ["grid points of working ability, normalised to an average of one; the positive reals stand in for the vector"]
ρ_θ0   : [0,1]   :: ["probability that zero entrepreneurial ability persists"]
ρ_θ1   : [0,1]   :: ["probability that the positive entrepreneurial ability persists"]
θ_e    : ℝ₊₊     :: ["the positive level of entrepreneurial ability"]

y_n : Y
y_n ~ MarkovChain(P_y, y_grid, y_wa)
θ_n : Θ
θ_n ~ MarkovChain(((ρ_θ0, 1 - ρ_θ0), (1 - ρ_θ1, ρ_θ1)), (0, θ_e), θ_wa)
s : {young, old}
s ~ Categorical((π_y, 1 - π_y))
```

The laws are quoted without their annotations. Working ability follows the chain with transition matrix `P_y` on the grid `y_grid`, drawn from the row at last year's ability `y_wa`. The grid has as many points as the discretisation of the income process chooses (five in the paper, Appendix A), and no finite set or vector with an open number of members can be written, so `Y`, `P_y` and `y_grid` are declared in sets that contain them. Entrepreneurial ability takes the two levels $0$ and $\theta_e$; its transition matrix is written from the two persistence probabilities the paper calibrates, since each row sums to one. The demographic label `s` is `young` with probability $\pi_y$ and `old` otherwise, the probabilities listed in the order of the labels. The paper assumes the two ability processes independent of each other (Section III.G) and the probability of ageing constant, so the demographic event does not depend on the abilities either; the three laws are declared separately, and their independence is that assumption of the model, not a consequence of the separate declarations.

The last argument of each `MarkovChain` law names the ability the draw is conditioned on. No spelling of a conditional law is settled, and the third argument is this example's; `economics.md`, Section 4, item 6, explains the choice.

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_wa : Xa, y_wa : Y, θ_wa : Θ, y_n, θ_n) : !arvl -> (a : Xa, y : Y, θ : Θ) : !dcsn] {
    a = a_wa
    y = y_n
    θ = θ_n
}
```

The arrival edge draws this year's abilities. The paper places these draws between two years, before any decision (Section III.E); here they are the first events of the year that follows.

```bl
[id=dcsn_to_cntn, (a, y, θ, s) : !dcsn -> ()] {
    [label=young, () -> (a_wa_yc : Xa, y_wa_yc : Y, θ_wa_yc : Θ) : !cntn] {
        a_wa_yc = a
        y_wa_yc = y
        θ_wa_yc = θ
    }
    [label=old, () -> (a_wa_rt : Xa) : !cntn] {
        a_wa_rt = a
    }
}
```

The decision edge is a branch chosen by nature: the shock `s` selects the labelled block. A household that remains young carries its assets and abilities to the occupational choice; one that ages carries only its assets to retirement, since a retiree's value does not depend on the abilities.

```bl
[id=cntn_to_dcsn, (V_young[>] : ℝ @ !vlu, W_r[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*E_{s}((V_young[>], W_r[>])[s])     :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y_n,θ_n}(V)                    :: [id=value]
}
```

`V_young[>]` is the arrival value of `young_choice`, the paper's $V$, and `W_r[>]` the arrival value of `retiree`. The backward value is the expectation over the demographic label of the value it selects, discounted once: $\beta[\pi_yV+(1-\pi_y)W_r]$. The arrival value integrates the ability draws conditional on last year's abilities. It is the continuation value `V[>]` of the worker's problem in the year before.

## Elaboration

Elaborated alone, `elaborate_stage(load_stage("applications/cagetti-denardi-2006/declaration/stages/worker_ageing/worker_ageing.bl"))` constructs every builder, and the three queries of a branching stage answer:

```text
kind(stage)          branching
branches(stage)      young: (worker_ageing:cntn:a_wa_yc, worker_ageing:cntn:y_wa_yc, worker_ageing:cntn:θ_wa_yc)   old: (worker_ageing:cntn:a_wa_rt,)
combination(stage)   expectation
```

The label `s` is drawn by nature, so the branches combine by the expectation over its law.

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.A, Section III.E, equation (8), Section III.G and Appendix A.
