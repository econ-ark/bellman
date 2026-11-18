---
title: "The perfect foresight stage"
audience: developer
type: model-note
topic: [applications]
---
# The perfect foresight stage

The stage describes one consumption decision with known income growth. Human wealth is the present value of income. It is a constant field at each perch: its value does not depend on that perch's state. [The economics](../../../economics.md) gives the stationary solution and its conditions.

<a id="the-derived-parameters"></a>
<a id="the-utility-and-the-feasible-set"></a>
<a id="the-blocks"></a>

## Declarations

The four calibrated parameters are discounting `β`, risk aversion `ρ`, the gross interest factor `R`, and income growth `Γ`. The return patience factor `q` is derived from them. Its declared set `(0,1)` imposes return impatience, which makes stationary consumption positive.

The continuation input `h[>]` determines feasible consumption, `c < m + h[>]`. The decision equation adds current income, `h = 1 + h[>]`. The arrival equation discounts that wealth, `h[<] = h*Γ/R`. Each human-wealth declaration includes `!cnst`, so the value is independent of state.

```bl
@stage: perfect_foresight

# Perfect foresight consumption with human wealth sent backward.
# The decision field h includes this period's income; h[>] is the present
# value of the next period's human wealth. The stage sends h*Γ/R backward.
# The last period takes in zero. Feasibility reads h[>], with bound -h[>].

Xm := ℝ
Xa := ℝ

β : ℝ₊₊ @ (0, R^(ρ-1))   :: ["discount factor; its upper bound R^(ρ-1) is the return impatience condition, q < 1"]
ρ : (1, inf)               :: ["coefficient of relative risk aversion, greater than one"]
R : ℝ₊₊                    :: ["gross interest factor"]
Γ : ℝ₊₊                    :: ["permanent income growth factor"]

q : (0,1) := (β*R)^(1/ρ)/R   :: ["the return patience factor; the return impatience condition is q < 1"]

𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]

Γ_c(x : Xm) := {c : ℝ₊₊ | c < x + h[>]}   :: [id=feasible_consumption]

[id=arvl_to_dcsn, (k : Xa) : !arvl -> (m : Xm) : !dcsn] {
    m = R*k/Γ + 1                   :: [id=market_resources]
}

[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m - c                       :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, h[>] : ℝ₊ @ !vlu @ !cnst, c) : !cntn -> (V : ℝ @ !vlu, h : ℝ₊ @ !vlu @ !cnst) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
    h = 1 + h[>]                    :: [id=human_wealth]
}

[id=dcsn_to_arvl, (V, h) : !dcsn -> (V[<] : ℝ @ !vlu, h[<] : ℝ₊ @ !vlu @ !cnst) : !arvl] {
    V[<] = Γ^(1-ρ) * V              :: [id=value]
    h[<] = h*Γ/R                    :: [id=human_wealth]
}

[id=policy, (V[>] : ℝ @ !vlu, h[>] : ℝ₊ @ !vlu @ !cnst) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])     :: [id=optimality]
}
```

## Human wealth

The last period takes in zero human wealth. Repeated backward steps give the finite geometric sum. At the calibration in this folder, stationary continuation wealth 51 becomes decision wealth 52 and returns as arrival wealth 51.

The strict consumption inequality excludes consuming all resources when continuation wealth is zero. With increasing utility and zero continuation value, that last-period problem has no maximizer. The human-wealth recursion alone does not solve finite-horizon consumption.

<a id="the-closed-form-methodsbl"></a>

## Stationary closed form

The methods file defines `κ`, `h_lim`, and `L_lim`. The declared positive set of `h_lim` requires `Γ < R`. The stage itself declares only positive growth, so a finite continuation step can use a larger growth factor.

Each `!explicit` block supplies every output of its builder. The value blocks therefore supply both value and human wealth. Their derivative lines remain authored equations; the package does not differentiate them automatically.

```bl
@methods: perfect_foresight
# The stationary closed form. The stage defines human wealth recursively;
# these methods state its fixed point. The declared set of h_lim requires Γ < R.

κ := 1 - q    :: ["the marginal propensity to consume, one minus the return patience factor"]
h_lim : ℝ₊₊ := 1/(1 - Γ/R)   :: ["human wealth at the infinite horizon, the value that h = 1 + h*Γ/R maps to itself; positive exactly where Γ < R, the finite human wealth condition"]
L_lim := 1 - h_lim           :: ["the natural borrowing limit on market resources at the infinite horizon"]

[id=policy, policy.method : !explicit] {
    c = κ*(m - L_lim)                                        :: [id=consumption]
}

[id=cntn_to_dcsn, cntn_to_dcsn.method : !explicit] {
    V = κ^(-ρ)*(m - L_lim)^(1-ρ)/(1-ρ)                       :: [id=closed_value]
    D_{m}V = κ^(-ρ)*(m - L_lim)^(-ρ)                         :: [id=marginal]
    h = h_lim                                                :: [id=closed_human_wealth]
}

[id=dcsn_to_arvl, dcsn_to_arvl.method : !explicit] {
    V[<] = Γ^(1-ρ)*κ^(-ρ)*(R*k/Γ + 1 - L_lim)^(1-ρ)/(1-ρ)    :: [id=closed_value]
    D_{k}V[<] = R*Γ^(-ρ)*κ^(-ρ)*(R*k/Γ + 1 - L_lim)^(-ρ)     :: [id=arrival_marginal]
    h[<] = h_lim*Γ/R                                         :: [id=closed_human_wealth]
}
```

<a id="the-endogenous-grid-method-methodsegmbl"></a>

## Endogenous grid method

The endogenous grid method inverts the Euler equation on savings points and computes the corresponding resources. Linear interpolation evaluates consumption between these pairs. The program supplies the grid bounds and count as settings.

```bl
@methods: perfect_foresight
# The gridded methods of the perfect foresight stage, a replacing selection
# beside methods.bl. The endogenous grid method stands on the policy builder
# with its exogenous grid of savings a, whose three settings the application's
# module supplies, so that the folder holds no settings file. Its three lines,
# the inverted Euler equation with the inverse marginal utility written out,
# the inverted law of motion and the identification of the chosen consumption
# with the candidate, stand in place of the maximization when the stage is
# solved. The consumption function is read by linear interpolation at the
# policy builder's Evaluation, between the pairs the method computes, and that
# Evaluation takes no grid of its own, since the pairs give its nodes. Each
# value builder gains its derivative line: the envelope condition of the
# decision value, and the derivative of the arrival value, whose factor
# R*Γ^(-ρ) comes from the law m = R*k/Γ + 1 and the normalization Γ^(1-ρ) of
# the value. The settings are declared first, with their sets: a count in ℕ
# and a bound a point of Xa, the set of the savings.

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

## Numerical inputs

The module `code/closed_form_check.py` constructs each stage through `elaborate`, `methodize`, `calibrate`, and `configure`. It supplies both `V[>]` and `h[>]` to `check_inputs` before requesting kernels or grids, including under the explicit methods.

The closed form and its value kernels use `h[>] = h_lim - 1`. The gridded route computes `h[>]` step by step from `0`, by the stage's lines, and reads `h_lim - 1` only to refuse a grid of savings that starts at or below the limit. `gridded_step` accepts a finite supplied continuation mapping and its marginal value. It remains usable when `Γ >= R`, where the stationary routes refuse finite human wealth. Each result retains unresolved callable conditions as `input_conditions`.
