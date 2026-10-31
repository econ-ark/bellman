---
title: "The occupational choice of the young (young_choice.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The occupational choice of the young (young_choice.bl)

A young household starts the year with assets $a$ and knows its working ability $y$ and its entrepreneurial ability $\theta$ for the year. It chooses whether to run a business or to work. The stage states equation (2) of Cagetti and De Nardi (2006),

$$
V(a,y,\theta)=\max\{V_e(a,y,\theta),\,V_w(a,y,\theta)\},
$$

where $V_e$ is the value of running a business this year (the stage `young_entrepreneur`) and $V_w$ the value of working (the stage `worker`). The choice changes no quantity: the household continues into one of the two problems with its assets and abilities unchanged. The stage is written in the form of the retirement choice of the corpus, `applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl`: a control over a finite set of labels, one nested block per label, a value selected by the control, and a policy that compares the same values in the same order. `economics.md` describes the whole model and the year the stage belongs to.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_yc`, `y_yc`, `θ_yc` | The assets and this year's abilities of a household that is young this year: a young household that did not age, or the offspring of a household that died. |
| Decision | `a`, `y`, `θ` | The same quantities; nothing is learned between arrival and decision. |
| Continuation, entrepreneur | `a_ye`, `y_ye`, `θ_ye` | The arrival fields of `young_entrepreneur`, joined by their names. |
| Continuation, worker | `a_yc_wk`, `y_yc_wk`, `θ_yc_wk` | Joined to the arrival fields `a_wk`, `y_wk`, `θ_wk` of `worker`. |

## Declarations

```bl
Xa := ℝ₊
Y  := ℝ₊₊        :: ["working ability; the positive reals stand in for its finite grid, whose number of points is a numerical choice"]
Θ  := ℝ₊         :: ["entrepreneurial ability; the nonnegative reals stand in for its two levels, 0 and θ_e"]
```

Assets are nonnegative. Working ability takes the values of a grid whose number of points the discretisation of the income process chooses, and entrepreneurial ability takes the two values $0$ and $\theta_e$; neither finite set can be written with its members, so the sets that contain them stand in, as the annotations say. The stage has no parameters.

## Blocks and equations

The arrival block copies the three quantities to the decision perch.

```bl
[id=arvl_to_dcsn, (a_yc : Xa, y_yc : Y, θ_yc : Θ) : !arvl -> (a : Xa, y : Y, θ : Θ) : !dcsn] {
    a = a_yc
    y = y_yc
    θ = θ_yc
}
```

The decision block declares the control `d` on the labels `{entrepreneur, worker}` and has an empty output side. Its body holds one labelled block per occupation, each copying the decision state into that occupation's continuation fields. The two sets of fields have distinct names because each is the arrival state of a different stage.

```bl
[id=dcsn_to_cntn, (a, y, θ, d : !ctrl @ {entrepreneur, worker}) : !dcsn -> ()] {
    [label=entrepreneur, () -> (a_ye : Xa, y_ye : Y, θ_ye : Θ) : !cntn] {
        a_ye = a
        y_ye = y
        θ_ye = θ
    }
    [label=worker, () -> (a_yc_wk : Xa, y_yc_wk : Y, θ_yc_wk : Θ) : !cntn] {
        a_yc_wk = a
        y_yc_wk = y
        θ_yc_wk = θ
    }
}
```

The backward block selects the value of the chosen occupation. `V_e[>]` and `V_w[>]` are the continuation values of the two branches, which are the arrival values of `young_entrepreneur` and `worker`. The tuple is written in the order of the labels, so `d = entrepreneur` selects $V_e$. The arrival value equals the decision value.

```bl
[id=cntn_to_dcsn, (V_e[>] : ℝ @ !vlu, V_w[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = (V_e[>], V_w[>])[d]              :: [id=choice_value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                             :: [id=value]
}
```

The policy block chooses the label with the larger value, comparing the same tuple in the same order. Its inputs are the two continuation values; the decision state is the argument of the policy it defines. A tie between the two values leaves both labels optimal, and the stage fixes no rule for it.

```bl
[id=policy, (V_e[>] : ℝ @ !vlu, V_w[>] : ℝ @ !vlu) : !cntn -> (d : {entrepreneur, worker} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_e[>], V_w[>])       :: [id=choice]
}
```

## Elaboration

Elaborated alone, `elaborate_stage(load_stage("applications/cagetti-denardi-2006/declaration/stages/young_choice/young_choice.bl"))` constructs every builder, and the three queries of a branching stage answer:

```text
kind(stage)          branching
branches(stage)      entrepreneur: (young_choice:cntn:a_ye, young_choice:cntn:y_ye, young_choice:cntn:θ_ye)   worker: (young_choice:cntn:a_yc_wk, young_choice:cntn:y_yc_wk, young_choice:cntn:θ_yc_wk)
combination(stage)   choice
```

The label `d` is chosen by the household, so the branches combine by the choice of the policy.

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.E, equation (2).
