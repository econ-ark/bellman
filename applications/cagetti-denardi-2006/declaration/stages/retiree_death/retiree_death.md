---
title: "Survival or death of a retiree (retiree_death.bl)"
audience: developer
type: model-note
topic: [applications]
---
# Survival or death of a retiree (retiree_death.bl)

A household that was retired in the previous year starts this year by learning whether it has survived. With probability $\pi_o$ it survives and remains retired; with probability $1-\pi_o$ it dies, and its offspring enters the model as a young household with the bequeathed assets, its value weighted by $\eta$. Both abilities of the offspring are drawn from the invariant distributions of their chains, as the paper states; a retiree has no ability among its own states. The stage states the continuation value of the retiree's problem (13) of Cagetti and De Nardi (2006),

$$
\beta\pi_oW_r(a')+\eta\beta(1-\pi_o)E\,V(a',y',\theta'),
$$

where $W_r$ is the retiree's value (the stage `retiree`), $V$ the value of the young before the occupational choice (the stage `young_choice`), and the expectation is under the invariant distributions of $y'$ and $\theta'$. The file has the form of `entrepreneur_death.bl`. `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_rd` | The retiree's assets at the end of the previous year, joined from `retiree` by the inter-period connector. |
| Decision | `a`, `y`, `θ` | Assets and the abilities drawn for an offspring. |
| Continuation, survive | `a_rd_rt` | Joined to the arrival field of `retiree`. |
| Continuation, die | `a_rd_yc`, `y_rd_yc`, `θ_rd_yc` | Joined to the arrival fields of `young_choice`. |

## Declarations and laws

The parameters are those of `entrepreneur_death.bl`. The laws are:

```bl
y_n : Y
y_n ~ Invariant(P_y, y_grid)
θ_n : Θ
θ_n ~ Invariant(((ρ_θ0, 1 - ρ_θ0), (1 - ρ_θ1, ρ_θ1)), (0, θ_e))
s : {survive, die}
s ~ Categorical((π_o, 1 - π_o))
```

Both abilities are drawn from the invariant distributions of their chains, as the paper specifies for "the child's value function" of a retiree. The ability chain has two states, so its invariant distribution puts probability $(1-\rho_{\theta0})/(2-\rho_{\theta0}-\rho_{\theta1})$ on $\theta_e$, about 0.149 in the calibration; the law names the chain, as for working ability, whose invariant distribution has no closed form for a grid of open size.

## Blocks and equations

```bl
[id=arvl_to_dcsn, (a_rd : Xa, y_n, θ_n) : !arvl -> (a : Xa, y : Y, θ : Θ) : !dcsn] {
    a = a_rd
    y = y_n
    θ = θ_n
}

[id=dcsn_to_cntn, (a, y, θ, s) : !dcsn -> ()] {
    [label=survive, () -> (a_rd_rt : Xa) : !cntn] {
        a_rd_rt = a
    }
    [label=die, () -> (a_rd_yc : Xa, y_rd_yc : Y, θ_rd_yc : Θ) : !cntn] {
        a_rd_yc = a
        y_rd_yc = y
        θ_rd_yc = θ
    }
}

[id=cntn_to_dcsn, (W_r[>] : ℝ @ !vlu, V_young[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*E_{s}((W_r[>], η*V_young[>])[s])       :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y_n,θ_n}(V)                        :: [id=value]
}
```

The surviving retiree carries its assets alone back to the retiree's problem; the offspring carries the assets and its drawn abilities to the occupational choice. The abilities are drawn for every household before survival is known, which leaves the survivor's value unchanged. The backward value is $\beta[\pi_oW_r+(1-\pi_o)\eta V]$, and the arrival value is the continuation value `V[>]` of the retiree's problem in the year before.

## Elaboration

Elaborated alone, `elaborate_stage(load_stage("applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl"))` constructs, and the three queries of a branching stage answer:

```text
kind(stage)          branching
branches(stage)      survive: (retiree_death:cntn:a_rd_rt,)   die: (retiree_death:cntn:a_rd_yc, retiree_death:cntn:y_rd_yc, retiree_death:cntn:θ_rd_yc)
combination(stage)   expectation
```

The label `s` is drawn by nature, so the branches combine by the expectation over its law. The backward builders construct. The forward builders are refused, since the working ability of an offspring is drawn from the family `Invariant`, which the package does not admit:

```text
applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl:17:1-17:165: the forward measures are not constructed: the distribution of y_n is written with the family 'Invariant', whose result set is not declared (opaque:external:Invariant:result); under the rule not-constructed the forward measure is extended only by the families N, LogNormal, Uniform, TruncatedNormal, TruncatedLogNormal, TypeIExtremeValue, DiscreteMarkov, MarkovChain, Mixture, Categorical, Bernoulli; write the declaration with one of those families, or read the backward builders graph, which does not use it (address 'applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl:17'; rule not-constructed)
```

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.A, Section III.E, equation (13) and the paragraph after equation (14), and Appendix A.
