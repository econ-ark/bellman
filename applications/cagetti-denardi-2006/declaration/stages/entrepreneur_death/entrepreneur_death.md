---
title: "Survival or death of an old entrepreneur (entrepreneur_death.bl)"
audience: developer
type: model-note
topic: [applications]
---
# Survival or death of an old entrepreneur (entrepreneur_death.bl)

A household that ran a business as an old entrepreneur in the previous year starts this year by learning whether it has survived. With probability $\pi_o$ it survives and decides again whether to keep the business; with probability $1-\pi_o$ it dies, and its offspring enters the model as a young household with the bequeathed assets. The parent weighs the offspring's value by $\eta$. The offspring inherits the firm, so its entrepreneurial ability is drawn from the row of the ability chain at the parent's ability, while its working ability is drawn from the invariant distribution of the income chain. The stage states the continuation value of the old entrepreneur's problem (11) of Cagetti and De Nardi (2006),

$$
\beta\pi_oE\bigl[W(a',\theta')\mid\theta\bigr]+\eta\beta(1-\pi_o)E\bigl[V(a',y',\theta')\mid\theta\bigr],
$$

with $y'$ from the invariant distribution of $P_y$ in the second term. $W$ is the old entrepreneur's value before he decides whether to continue (the stage `old_choice`) and $V$ the value of the young before the occupational choice (the stage `young_choice`). The file has the form of `worker_ageing.bl`, whose page explains the shock-keyed branch. `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_ed`, `θ_ed` | The old entrepreneur's assets at the end of the previous year and that year's ability, joined from the repay branch of `old_entrepreneur` by the inter-period connector. |
| Decision | `a`, `y`, `θ` | Assets, the working ability drawn for an offspring, and this year's entrepreneurial ability. |
| Continuation, survive | `a_ed_oc`, `θ_ed_oc` | Joined to the arrival fields of `old_choice`. |
| Continuation, die | `a_ed_yc`, `y_ed_yc`, `θ_ed_yc` | Joined to the arrival fields of `young_choice`. |

## Declarations and laws

Besides the parameters of `worker_ageing.bl`, with `π_o : [0,1]` in place of `π_y`, the stage declares the weight on the offspring's utility, `η : [0,1]`. The laws are:

```bl
y_n : Y
y_n ~ Invariant(P_y, y_grid)
θ_n : Θ
θ_n ~ MarkovChain(((ρ_θ0, 1 - ρ_θ0), (1 - ρ_θ1, ρ_θ1)), (0, θ_e), θ_ed)
s : {survive, die}
s ~ Categorical((π_o, 1 - π_o))
```

`Invariant(P_y, y_grid)` is the invariant distribution of the income chain on its grid. It is a function of `P_y`, so the stage names the chain rather than declaring the stationary probabilities as a further parameter; the name of the law is this example's. Entrepreneurial ability is drawn from the row at last year's ability, for the survivor and for an offspring alike, as the paper specifies: "the one with respect to θ′ is conditional on the parent's θ and evolves according to the same Markov process that each person faces for θ while alive".

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_ed : Xa, θ_ed : Θ, y_n, θ_n) : !arvl -> (a : Xa, y : Y, θ : Θ) : !dcsn] {
    a = a_ed
    y = y_n
    θ = θ_n
}

[id=dcsn_to_cntn, (a, y, θ, s) : !dcsn -> ()] {
    [label=survive, () -> (a_ed_oc : Xa, θ_ed_oc : Θ) : !cntn] {
        a_ed_oc = a
        θ_ed_oc = θ
    }
    [label=die, () -> (a_ed_yc : Xa, y_ed_yc : Y, θ_ed_yc : Θ) : !cntn] {
        a_ed_yc = a
        y_ed_yc = y
        θ_ed_yc = θ
    }
}

[id=cntn_to_dcsn, (W_old[>] : ℝ @ !vlu, V_young[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*E_{s}((W_old[>], η*V_young[>])[s])     :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y_n,θ_n}(V)                        :: [id=value]
}
```

The offspring's working ability is drawn on the arrival edge for every household, before survival is known; the survivor's value does not depend on it, so the arrival value is the paper's. The backward value is $\beta[\pi_oW+(1-\pi_o)\eta V]$, the weight $\eta$ entering the offspring's branch only. The arrival value is the continuation value `V_repay[>]` of the old entrepreneur's problem in the year before.

## Elaboration

Elaborated alone, `elaborate_stage(load_stage("applications/cagetti-denardi-2006/declaration/stages/entrepreneur_death/entrepreneur_death.bl"))` constructs, and the three queries of a branching stage answer:

```text
kind(stage)          branching
branches(stage)      survive: (entrepreneur_death:cntn:a_ed_oc, entrepreneur_death:cntn:θ_ed_oc)   die: (entrepreneur_death:cntn:a_ed_yc, entrepreneur_death:cntn:y_ed_yc, entrepreneur_death:cntn:θ_ed_yc)
combination(stage)   expectation
```

The label `s` is drawn by nature, so the branches combine by the expectation over its law. The backward builders construct. The forward builders are refused, since the working ability of an offspring is drawn from the family `Invariant`, which the package does not admit:

```text
applications/cagetti-denardi-2006/declaration/stages/entrepreneur_death/entrepreneur_death.bl:17:1-17:165: the forward measures are not constructed: the distribution of y_n is written with the family 'Invariant', whose result set is not declared (opaque:external:Invariant:result); under the rule not-constructed the forward measure is extended only by the families N, LogNormal, Uniform, TruncatedNormal, TruncatedLogNormal, TypeIExtremeValue, DiscreteMarkov, MarkovChain, Mixture, Categorical, Bernoulli; write the declaration with one of those families, or read the backward builders graph, which does not use it (address 'applications/cagetti-denardi-2006/declaration/stages/entrepreneur_death/entrepreneur_death.bl:17'; rule not-constructed)
```

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.A, Section III.E, equation (11) and the paragraph after equation (12), and Appendix A.
