---
title: "The perfect foresight stage"
audience: developer
type: model-note
topic: [applications]
---
# The perfect foresight stage

> [!summary]
> `perfect_foresight.bl` is the buffer-stock stage of
> `applications/buffer-stock/` without its two income shocks: one state,
> market resources `m`, one control, consumption `c`, and a law of motion
> with no random term. This page explains its lines and the two methods
> files beside it; the economics and the closed-form solution are in the
> folder's `economics.md`.

## Declarations

The two sets are the whole real line, since the unconstrained household may
borrow against its future income, where the buffer-stock stage keeps
resources and savings strictly positive. The four parameters are those of
that stage without the shocks'. The growth factor's set is the interval
`(0, R)`, whose upper endpoint is the interest factor: the bound is the
finite human wealth condition, and `calibrate`, which decides an interval
whose endpoints are parameters, refuses a growth factor at or above the
interest factor, naming the set. The discount factor's type holds two sets,
`(0,1)` and `(0, R^(ρ-1))` with `@` between them, and the discount factor
lies in both: the second bound is the return impatience condition, q < 1
written for β, and `calibrate` refuses a discount factor at or above it,
naming the condition.
The set `(1, inf)` of the coefficient of relative risk aversion refuses
ρ = 1, logarithmic utility, which needs another utility.

```bl
Xm := ℝ
Xa := ℝ

β : (0,1) @ (0, R^(ρ-1))   :: ["discount factor; its upper bound R^(ρ-1) is the return impatience condition, q < 1"]
ρ : (1, inf)               :: ["coefficient of relative risk aversion, greater than one"]
R : ℝ₊₊                    :: ["gross interest factor"]
Γ : (0, R)                 :: ["permanent income growth factor; its upper bound R is the finite human wealth condition"]
```

## The derived parameters

Three constants the stage defines from its parameters, which the calibration
does not supply: the return patience factor `q`, human wealth `h`, the
present value of current and future income normalized by permanent income,
and the natural borrowing limit `L = 1 - h`, above which total wealth `m - L`
is positive. `stage.par` lists them after the four declared parameters with
their definitions and, once a calibration is bound, their values: 1/1.04, 52
and -51 at the folder's calibration. A calibration source that names one of
them is refused.

```bl
q := (β*R)^(1/ρ)/R   :: ["the return patience factor; the return impatience condition is q < 1"]
h := 1/(1 - Γ/R)     :: ["human wealth, the present discounted value of permanent income"]
L := 1 - h           :: ["the natural borrowing limit on market resources, above which total wealth m - L is positive"]
```

## The utility and the feasible set

The utility is the CRRA function of the buffer-stock stage. The feasible set
is the natural borrowing constraint: consumption below total wealth, the
resources less the natural borrowing limit.

```bl
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]

Γ_c(x : Xm) := {c : ℝ₊₊ | c < x - L}   :: [id=feasible_consumption]
```

## The blocks

The arrival block carries the saving `k` of the previous period, normalized
by that period's permanent income, into this period's resources: the return
`R` on the saving, divided by the growth factor to normalize by this period's
permanent income, plus this period's income, which is one. The decision block
is the saving. Neither line has a shock.

```bl
[id=arvl_to_dcsn, (k : Xa) : !arvl -> (m : Xm) : !dcsn] {
    m = R*k/Γ + 1                   :: [id=market_resources]
}

[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m - c                       :: [id=savings]
}
```

The decision value reads the continuation value at the saving. The arrival
value is the decision value times `Γ^(1-ρ)`, which puts it in the units of
the previous period's permanent income, as the buffer-stock stage writes
`(Γ*ψ)^(1-ρ)` inside its expectation; here there is nothing to take an
expectation over.

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = Γ^(1-ρ) * V              :: [id=value]
}
```

The policy block states the maximization alone, over the feasible set at the
decision state.

```bl
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])     :: [id=optimality]
}
```

## The closed form, `methods.bl`

The addition beside the stage file defines the marginal propensity to
consume `κ = 1 - q`, the method's coefficient, and types `!explicit` on the
policy builder and on the two value builders. The line of each block writes
its output as an explicit function of the state of its own perch, the
parameters and the derived parameters: the consumption function, the
decision value and the arrival value, the last with the law of motion and
the normalization `Γ^(1-ρ)` written out. Each value block also writes its
marginal in closed form, `κ^(-ρ)(m - L)^(-ρ)` and `R*Γ^(-ρ)` times it at
the resources `R*k/Γ + 1`, since a representation offers a derivative only
where a line writes it; the application's module reads the arrival
marginal by its id, `arrival_marginal`. At the operative level each line
stands in place of the builder's declared line, which `stage.declared` keeps,
and the compiled kernel of each line evaluates the function. `!explicit`
gives the Evaluation of each builder the closed form, `!closed_form`, which
`stage.methods` shows as generated from the builder's method entry. The
power `κ^(-ρ)` is defined for every ρ > 1 only at κ > 0, which is the
return impatience condition, the upper bound of the discount factor in the
stage file: `calibrate` refuses a calibration outside that bound, and one at
which the computed κ is not positive. The folder has no settings file, and
`configure` binds the stage from an empty settings source.

```bl
κ := 1 - q    :: ["the marginal propensity to consume, one minus the return patience factor"]

[id=policy, policy.method : !explicit] {
    c = κ*(m - L)                                        :: [id=consumption]
}

[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit] {
    V = κ^(-ρ)*(m - L)^(1-ρ)/(1-ρ)                       :: [id=closed_value]
    D_{m}V = κ^(-ρ)*(m - L)^(-ρ)                         :: [id=marginal]
}

[id=dcsn_to_arvl, dcsn_to_arvl.method : !explicit] {
    V[<] = Γ^(1-ρ)*κ^(-ρ)*(R*k/Γ + 1 - L)^(1-ρ)/(1-ρ)    :: [id=closed_value]
    D_{k}V[<] = R*Γ^(-ρ)*κ^(-ρ)*(R*k/Γ + 1 - L)^(-ρ)     :: [id=arrival_marginal]
}
```

## The endogenous grid method, `methods.egm.bl`

The replacing selection declares the three settings of the grid of savings
and types `!egm` on the policy builder with that grid. The three lines of its
block, the inverted Euler equation with the inverse marginal utility written
out, the inverted law of motion and the identification of the chosen
consumption with the candidate, stand in place of the maximization when the
stage is solved. `!Linear` at the policy builder's Evaluation reads the
consumption function between the pairs the method computes, and that
Evaluation takes no grid, since the pairs give its nodes. Each value builder
gains its derivative line: the envelope condition of the decision value and
the derivative of the arrival value. The module
`code/closed_form_check.py` supplies the three settings and iterates the
method on the compiled kernels of these lines.

```bl
n_a : ℕ              :: ["number of points of the savings grid"]
a_min : Xa           :: ["lower bound of the savings grid"]
a_max : Xa           :: ["upper bound of the savings grid"]

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))
    | policy.evaluate.method : !Linear] {
    c[>] = (β*D_{a}V[>])^(-1/ρ)     :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{m}V = c^(-ρ)                         :: [id=marginal]
}

[id=dcsn_to_arvl] {
    D_{k}V[<] = R * Γ^(-ρ) * D_{m}V         :: [id=marginal]
}
```
