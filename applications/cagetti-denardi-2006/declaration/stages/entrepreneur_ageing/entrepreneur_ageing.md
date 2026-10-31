---
title: "Ageing of a young entrepreneur (entrepreneur_ageing.bl)"
audience: developer
type: model-note
topic: [applications]
---
# Ageing of a young entrepreneur (entrepreneur_ageing.bl)

A household that ran a business as a young entrepreneur in the previous year starts this year by learning its new abilities and whether it has aged. With probability $\pi_y$ it remains young and makes the occupational choice again; with probability $1-\pi_y$ it becomes an old entrepreneur, who may keep the business going. The stage states the continuation value of the young entrepreneur's problem (3) of Cagetti and De Nardi (2006),

$$
\beta\pi_yE\bigl[V(a',y',\theta')\mid y,\theta\bigr]+\beta(1-\pi_y)E\bigl[W(a',\theta')\mid\theta\bigr],
$$

where $V$ is the value of the young before the occupational choice (the stage `young_choice`) and $W$ the value of the old entrepreneur before he decides whether to continue (the stage `old_choice`). The file has the form of `worker_ageing.bl`, whose page explains the laws and the shock-keyed branch; only the old branch differs. `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_ea`, `y_ea`, `θ_ea` | The young entrepreneur's assets at the end of the previous year and that year's abilities, joined from the repay branch of `young_entrepreneur` by the inter-period connector. |
| Decision | `a`, `y`, `θ` | Assets and this year's abilities, after the draws. |
| Continuation, young | `a_ea_yc`, `y_ea_yc`, `θ_ea_yc` | Joined to the arrival fields of `young_choice`. |
| Continuation, old | `a_ea_oc`, `θ_ea_oc` | Joined to the arrival fields of `old_choice`. |

## Declarations and laws

The parameters and sets are those of `worker_ageing.bl`. The laws draw the abilities from the rows at last year's abilities:

```bl
y_n : Y
y_n ~ MarkovChain(P_y, y_grid, y_ea)
θ_n : Θ
θ_n ~ MarkovChain(((ρ_θ0, 1 - ρ_θ0), (1 - ρ_θ1, ρ_θ1)), (0, θ_e), θ_ea)
s : {young, old}
s ~ Categorical((π_y, 1 - π_y))
```

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_ea : Xa, y_ea : Y, θ_ea : Θ, y_n, θ_n) : !arvl -> (a : Xa, y : Y, θ : Θ) : !dcsn] {
    a = a_ea
    y = y_n
    θ = θ_n
}

[id=dcsn_to_cntn, (a, y, θ, s) : !dcsn -> ()] {
    [label=young, () -> (a_ea_yc : Xa, y_ea_yc : Y, θ_ea_yc : Θ) : !cntn] {
        a_ea_yc = a
        y_ea_yc = y
        θ_ea_yc = θ
    }
    [label=old, () -> (a_ea_oc : Xa, θ_ea_oc : Θ) : !cntn] {
        a_ea_oc = a
        θ_ea_oc = θ
    }
}

[id=cntn_to_dcsn, (V_young[>] : ℝ @ !vlu, W_old[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*E_{s}((V_young[>], W_old[>])[s])   :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y_n,θ_n}(V)                    :: [id=value]
}
```

An entrepreneur who ages keeps his entrepreneurial ability as a state, since he may continue the business; working ability is not a state of the old. `W_old[>]` is the arrival value of `old_choice`, the paper's $W$. The arrival value, $E[\beta\{\pi_yV+(1-\pi_y)W\}\mid y,\theta]$, is the continuation value `V_repay[>]` of the young entrepreneur's problem in the year before; the expectation over working ability does not affect the old branch, whose value does not depend on it.

## Elaboration

Elaborated alone, `elaborate_stage(load_stage("applications/cagetti-denardi-2006/declaration/stages/entrepreneur_ageing/entrepreneur_ageing.bl"))` constructs every builder, and the three queries of a branching stage answer:

```text
kind(stage)          branching
branches(stage)      young: (entrepreneur_ageing:cntn:a_ea_yc, entrepreneur_ageing:cntn:y_ea_yc, entrepreneur_ageing:cntn:θ_ea_yc)   old: (entrepreneur_ageing:cntn:a_ea_oc, entrepreneur_ageing:cntn:θ_ea_oc)
combination(stage)   expectation
```

The label `s` is drawn by nature, so the branches combine by the expectation over its law.

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.A, Section III.E, equation (3), and Appendix A.
