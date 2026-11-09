---
title: "The tenure stage (tenure.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The tenure stage (tenure.bl)

> [!summary]
> `tenure.bl` is the discrete-choice stage of the durables model: the income
> innovation is drawn, and the household chooses between keeping its house and
> selling it to buy another. The two alternatives lead to different continuation
> spaces, so the stage branches. The economic environment and the composition of
> the three stages are in `economics.md`.

## What the stage does

The household arrives with financial assets `a`, a housing stock `h` and last
period's income state `z`. On the arrival edge the innovation `ε` is drawn and
the income state becomes `z_d`; income is then observed, and the choice is made
knowing it, as the paper's Bellman equation (14) has it. The choice `d` is
between `keep` and `adjust`.

On the keep branch the house is retained after depreciation and cash on hand is
the return on assets plus income. On the adjust branch the house is sold, so the
household carries one number forward, total wealth, which is cash on hand plus
the resale value of the house. Nothing is consumed in this stage and no utility
is charged here: the two branches hand their states to the two consumption
stages, whose decision states the period's connector joins them to,
`{w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}`.

| Perch | What the household knows | Fields |
|---|---|---|
| Arrival | Assets, housing and the previous income state, before the innovation is drawn. | `a`, `h`, `z` |
| Decision | The same, with the new income state observed; the tenure choice is made here. | `a_d`, `h_d`, `z_d` |
| Continuation, keep | Cash on hand, the depreciated house and the income state. | `w_kp`, `h_kp`, `z_kp` |
| Continuation, adjust | Total wealth and the income state. | `w_adj`, `z_adj` |

## Declarations

The parameters are the two gross returns, the depreciation rate, the two
parameters of the income process, and the two that fix income at the age of this
period. The depreciation rate is declared below one, so that a kept house is
positive: at the curvature the model uses, utility tends to minus infinity as
housing tends to zero.

```bl
R   : ℝ₊₊       :: ["gross return on financial assets"]
R_H : ℝ₊₊       :: ["gross return on housing, received when the house is sold"]
δ   : [0,1)     :: ["depreciation rate of housing"]
ρ_z : (0,1)     :: ["persistence of log income"]
σ_z : ℝ₊        :: ["standard deviation of the innovation to log income"]
Y   : ℝ₊        :: ["earnings per unit of the income state at the age of the period"]
y_R : ℝ₊        :: ["income that does not depend on the income state at the age of the period"]
```

A stage has no age index, so the age profile of earnings cannot be written
inside it. What the stage states is the shape of income, a function of the
income state with two parameters, and the application evaluates those two
parameters at the age of each occurrence:

```bl
𝑦(z : ℝ₊₊) := Y*z + y_R                                 :: [id=income]
```

While the household works, `Y` is positive and `y_R` is zero; after it retires,
`Y` is zero and `y_R` is the retirement income. Income is strictly positive
under the calibration, which the declared sets alone do not require; that is an
assumption of the model, recorded here and not checked.

The innovation is declared and given its law on its own line. The law is the
continuous one; the finite chain the numerical method integrates against is in
the methods and settings files.

```bl
ε : ℝ
ε ~ N(0, 1)
```

## Transitions

The arrival edge draws the innovation and updates the income state; assets and
housing pass through.

```bl
[id=arvl_to_dcsn, (a : ℝ₊, h : ℝ₊₊, z : ℝ₊₊, ε) : !arvl -> (a_d : ℝ₊, h_d : ℝ₊₊, z_d : ℝ₊₊) : !dcsn] {
    a_d = a
    h_d = h
    z_d = z^ρ_z*exp(σ_z*ε)                              :: [id=income_state]
}
```

Listing `ε` on the arrival side makes it an argument of the transition; it does
not say that the innovation is known at arrival. Written in logarithms, the
equation is the autoregression $\log z_d = \rho_z \log z + \sigma_z \varepsilon$.

The decision edge is the discrete choice. Its output side is empty and its body
holds one labelled block per alternative, each defining that alternative's
continuation fields. The control `d` is typed by the set of labels, and the
order of that set is the order of the branches everywhere else in the file.

```bl
[id=dcsn_to_cntn, (a_d, h_d, z_d, d : !ctrl @ {keep, adjust}) : !dcsn -> ()] {
    [label=keep, () -> (w_kp : ℝ₊₊, h_kp : ℝ₊₊, z_kp : ℝ₊₊) : !cntn] {
        w_kp = R*a_d + 𝑦(z_d)                           :: [id=cash_on_hand]
        h_kp = (1 - δ)*h_d                              :: [id=housing_kept]
        z_kp = z_d
    }
    [label=adjust, () -> (w_adj : ℝ₊₊, z_adj : ℝ₊₊) : !cntn] {
        w_adj = R*a_d + R_H*(1 - δ)*h_d + 𝑦(z_d)        :: [id=total_wealth]
        z_adj = z_d
    }
}
```

The two branches have different numbers of fields, which is the reason the
continuation is a labelled union rather than one space: a keeper still holds a
house, and an adjuster holds only wealth until it buys one. No field name is
shared between the branches.

## Values

The backward block receives the decision value of each consumption stage, the
value that stage exports, and selects between them by the control. The first
entry of every tuple is the keep alternative, in the order of the label set.

```bl
[id=cntn_to_dcsn, (V_kp[>] : ℝ @ !vlu, V_adj[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = (V_kp[>], V_adj[>])[d]                                                     :: [id=choice_value]
}
```

The value line charges nothing: the two alternatives differ in what they hand
the consumption stages, not in a cost paid here.

The derivatives of the decision value are stated by the two lines the methods
file `methods.bl`, the addition beside this file, appends to the decision value
builder's block `cntn_to_dcsn`, whose header types the representation of the
value on the grid of assets and housing. Its two lines read the derivatives of
the branch values by terms such as `D_{w_kp}V_kp[>]`, and each is the envelope
condition of the branch that is chosen, with the derivative of the branch
transition as the factor.

```bl
[id=cntn_to_dcsn
    | evaluate[V].method : !Linear(extrapolate=extrap_policy, clamp_factor=clamp_max_factor)
    | evaluate[V].handler : "dcsmm:interp_as_scalar"
    | evaluate[V].grid : !Cartesian(a_d=(a_min, a_max, n_a), h_d=(h_min, h_max, n_h))] {
    D_{a_d}V = (R*D_{w_kp}V_kp[>], R*D_{w_adj}V_adj[>])[d]                          :: [id=marginal_assets]
    D_{h_d}V = ((1 - δ)*D_{h_kp}V_kp[>], R_H*(1 - δ)*D_{w_adj}V_adj[>])[d]          :: [id=marginal_housing]
}
```

An extra unit of assets is worth `R` units of cash on hand under either
alternative. An extra unit of housing is worth `(1 - δ)` units of kept housing
to a keeper, valued by the keeper's marginal value of housing, and
`R_H*(1 - δ)` units of wealth to an adjuster, valued by the adjuster's marginal
value of wealth. These hold where one alternative is strictly better; at a tie
the value has no derivative, and neither line asserts one.

The arrival block integrates the value over the innovation. The income state is
the only thing the innovation changes, and the laws `a_d = a` and `h_d = h` are
the identity in the two coordinates of the derivatives, so the derivatives of
the arrival value are the integrated derivatives of the decision value and the
block writes no derivative line.

```bl
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<]    = E_{ε}(V)                                  :: [id=value]
}
```

## Policy

The policy block compares the same two alternatives and returns the label of the
better one. Its inputs are the two continuation values and nothing else: the
decision state is the argument of the policy the block produces, not an input.

```bl
[id=policy, (V_kp[>] : ℝ @ !vlu, V_adj[>] : ℝ @ !vlu) : !cntn -> (d : {keep, adjust} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_kp[>], V_adj[>])                   :: [id=choice]
}
```

The two alternatives are compared at the same decision state, which is what
makes the comparison a choice rather than a comparison of functions on different
spaces. Where the two values are equal both labels attain the maximum; the rule
that selects one is a setting of the method, not of the model.

## Elaboration

`tenure.bl` constructs as a branching stage: the decision edge's two labeled
blocks are read as that edge's lines at the labels keep and adjust. Loading
and elaborating the file prints:

```text
applications/durables/declaration/stages/tenure/tenure.bl: ElaboratedStage('tenure', symbolic)
```

The stage parses, and its parsed tree is recorded in
`packages/bellman/tests/snapshot/corpus/durables/tenure.bl.ast.json` and
checked by the structural test.

## References

- Dobrescu, L. I. and Shanker, A. (2026). "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN 4181302,
  Section 2.2.
- Iskhakov, F., Jørgensen, T. H., Rust, J. and Schjerning, B. (2017). "The
  endogenous grid method for discrete-continuous dynamic choice models with (or
  without) taste shocks." *Quantitative Economics* 8(2), 317–365.
- Tauchen, G. (1986). "Finite state Markov-chain approximations to univariate and
  vector autoregressions." *Economics Letters* 20(2), 177–181.
