---
audience: user
type: example
topic: [applications]
---
# Perfect foresight consumption with CRRA utility

> [!note] Source
> The [application folder](https://github.com/econ-ark/bellman/tree/main/applications/consumption-perfect-foresight-crra) holds the stage, both methods selections, and calibration in the [model directory layout](../../Bellman-Sym/reference/model-directory-layout.md). Its `economics.md` gives the problem in levels and normalized units, the stationary solution, and its domain and conditions.

**The consumption-savings model without uncertainty, normalized by permanent income, whose consumption function is known in closed form.**

This example presents the perfect foresight consumption model with constant relative risk aversion (CRRA) utility in its normalized form. A household knows its future income with certainty. Each period it chooses its consumption out of its market resources, saves the rest at a fixed gross return, and may borrow against the income it will receive, whose present value is its human wealth. The stage is the [buffer stock stage](../buffer-stock/buffer_stock.md) without its two income shocks, and its notation follows that stage. Its consumption function is a fixed fraction of total wealth. The same stage file is solved in two ways, by the closed form that one methods file types and by the endogenous grid method that the other selects, and the two solutions are compared.

> [!note] Source
> Based on Carroll and Lujan Solis, *A Gentle Introduction to Intertemporal Choice*, chapter "Consumption Under Perfect Foresight and CRRA Utility", sections 2 and 3, with the numerical example of section 4.1. The chapter writes the growth factor of permanent income $G$; this page writes $\Gamma$, as the buffer stock example does.

## 1 Model overview

| Feature | Description |
|---------|-------------|
| **Stages** | 1 (consumption-savings with maximization; no expectation) |
| **Shocks** | None |
| **Solution** | Closed form (`!explicit`), or the endogenous grid method (EGM) |
| **State** | Normalized market resources $m$ |
| **Horizon** | Infinite (stationary) |

## 2 Bellman equation

With $V_t(M_t, P_t) = P_t^{1-\rho}\,v_t(m_t)$, the normalized problem is

$$
v(m) = \max_{c \in \Gamma_c(m)} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta\,\Gamma^{1-\rho}\,v(m') \right\}
$$

subject to:

$$
\begin{aligned}
a &= m - c \\
m' &= \frac{R}{\Gamma}\, a + 1
\end{aligned}
$$

where the feasible set $\Gamma_c(m) = \{c > 0 : c < m - L\}$ is the natural borrowing constraint.

Variables (all normalized by permanent income $P_t$):

- $m$ = market resources
- $c$ = consumption
- $a$ = end-of-period assets, the saving
- $R$ = gross interest factor
- $\Gamma$ = growth factor of permanent income, $P_{t+1} = \Gamma P_t$
- $\beta$ = discount factor
- $\rho$ = coefficient of relative risk aversion ($\rho > 1$)
- $h = 1/(1 - \Gamma/R)$ = human wealth, the present discounted value of current and future income
- $L = 1 - h$ = the natural borrowing limit on market resources

Total wealth is $w = m - 1 + h = m - L$, the resources less this period's income plus human wealth, and it is positive exactly above the limit. Along the law of motion total wealth evolves as $w' = (R/\Gamma)(w - c)$, so consumption with $0 < c < w$ keeps the next period's total wealth positive, and a saving $a > L$ gives next-period resources $m' > L$.

## 3 First-order conditions

**Euler equation** (in levels):

$$
u'(C_t) = \beta R\, u'(C_{t+1}), \qquad \frac{C_{t+1}}{C_t} = (R\beta)^{1/\rho},
$$

so consumption grows by the absolute patience factor $(R\beta)^{1/\rho}$ whatever the household's wealth.

**Envelope condition:**

$$
v'(m) = u'(c(m))
$$

## 4 Closed-form solution

Substituting the consumption path of the Euler equation into the intertemporal budget constraint gives consumption as a fixed fraction of total wealth, the chapter's equations (32) and (35):

$$
c(m) = \kappa\,(m - L), \qquad \kappa = 1 - q, \qquad q = \frac{(R\beta)^{1/\rho}}{R}, \qquad h = \frac{1}{1 - \Gamma/R}, \qquad L = 1 - h,
$$

on the domain $m > L$, where total wealth is positive. Here $q$ is the return patience factor and $\kappa$ the marginal propensity to consume. The value is known in closed form too,

$$
v(m) = \frac{u(c(m))}{\kappa} = \kappa^{-\rho}\,\frac{(m - L)^{1-\rho}}{1-\rho},
$$

and the arrival value, the decision value at the resources the law of motion gives, normalized by $\Gamma^{1-\rho}$, is

$$
V^{<}(k) = \Gamma^{1-\rho}\, v(Rk/\Gamma + 1) = R^{1-\rho}\,\kappa^{-\rho}\,\frac{(k - L)^{1-\rho}}{1-\rho}
$$

on $k > L$. The derivation and the finite-horizon solution are in the folder's `economics.md`.

## 5 State-space diagram

```
(k) ──m = R k/Γ + 1──▶ (m) ──c──▶ (a)
```

A single stage per period: the arrival state $k$, the saving of the previous period normalized by that period's permanent income, becomes market resources $m = Rk/\Gamma + 1$ with no shock; consumption $c$ determines the end-of-period assets $a = m - c$.

## 6 Stage file

The stage file declares resources and savings on the real line, since the household may borrow against future income. It states four parameters, the derived return patience factor, utility, and feasible consumption. Its blocks give two forward transitions, two backward value operations, and the consumption choice.

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

### 6.1 Arrival transition

The arrival block `arvl_to_dcsn` writes $m = Rk/\Gamma + 1$: the return $R$ on the saving $k$, divided by the growth factor $\Gamma$ to normalize by this period's permanent income, plus this period's income, which is one. The decision block `dcsn_to_cntn` is the saving, $a = m - c$. Neither line has a shock.

### 6.2 Derived parameters

The stage defines one derived parameter, `q : (0,1) := (β*R)^(1/ρ)/R`. Its declared set imposes return impatience. Calibration supplies the four underlying parameters, and refuses a supplied value for `q`.

Human wealth is a constant field: `!cnst` states that it does not depend on state. The stage takes in `h[>]`, computes `h = 1 + h[>]`, and sends `h[<] = h*Γ/R`. Feasibility reads the supplied continuation wealth. The stationary constants `h_lim` and `L_lim` belong to the closed-form methods (§7.1).

### 6.3 Builders

- `cntn_to_dcsn`, the decision value builder: $V = u(c) + \beta V^{>}$ at the chosen consumption, and `h = 1 + h[>]`.
- `policy`, the policy builder: the maximization of $u(c') + \beta V^{>}$ over consumption `0 < cp < m + h[>]`.
- `dcsn_to_arvl`, the arrival value builder: $V^{<} = \Gamma^{1-\rho}\, V$ puts value in the previous period's income units. It also sends `h[<] = h*Γ/R`. There is no expectation because income growth is known.

The stage file states no derivative and no numerical method: the two methods files beside it state the solutions, as the next section shows.

## 7 Methods and settings

Two methods files stand beside the stage. Each uses the same grammar and names the stage's blocks by their ids ([Methodization](../../Bellman-Sym/04-methodization.md)). The stage binds one selection at a time: `methods.egm.bl` replaces `methods.bl`.

### 7.1 Closed form

The addition `methods.bl` defines `κ = 1 - q`, `h_lim`, and `L_lim` as derived parameters. Its positive `h_lim` requires `Γ < R`. It types [`!explicit`](../../Bellman-Sym/reference/methods.md#explicit) on the policy builder and both value builders.

Each block writes its outputs as functions of its own perch's state and the parameters. The policy block gives consumption. The value blocks give decision and arrival values, their marginals, and stationary human wealth. The arrival formula includes the law of motion and the normalization $\Gamma^{1-\rho}$.

The operative equations replace the declared equations for computation. `stage.declared` retains the maximization and original value equations ([Methodization](../../Bellman-Sym/04-methodization.md) §5). Each builder's [Evaluation](../../Bellman-Sym/reference/operations.md#evaluation) uses [`!closed_form`](../../Bellman-Sym/reference/methods.md#closed-form). Derivatives are available only where the file supplies their equations.

The power `κ^(-ρ)` requires `κ > 0`. Calibration therefore enforces return impatience, `q < 1`. The closed form reads no setting.

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

### 7.2 Endogenous grid method

The methods file `methods.egm.bl` declares the savings grid's bounds and count. Its policy builder uses the endogenous grid method, [`!egm`](../../Bellman-Sym/reference/methods.md#egm), on `!Cartesian(a=(a_min, a_max, n_a))`. The program supplies those three settings.

The method writes the inverse Euler equation, computes resources from savings and candidate consumption, and selects those pairs. Linear interpolation evaluates consumption between the pairs. Its Evaluation reads the pairs as nodes, so no separate grid is needed there.

The decision value builder gains the envelope equation `D_{m}V = c^(-ρ)`. The arrival derivative is `D_{k}V[<] = R*Γ^(-ρ)*D_{m}V`. The factor combines the derivative `R/Γ` of the law of motion with the normalization `Γ^(1-ρ)`.

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

### 7.3 Binding the closed form

The application binds the four steps separately. The methods file supplies the stationary constants as well as the explicit expressions:

```python
from bellman.stage import elaborate_stage, load_stage

declaration = "applications/consumption-perfect-foresight-crra/declaration"
stage = elaborate_stage(load_stage(
    f"{declaration}/stages/perfect_foresight/perfect_foresight.bl"))
stage.methodize(f"{declaration}/stages/perfect_foresight/methods.bl")
stage.calibrate(f"{declaration}/calibration/perfect_foresight.yml")
stage.configure({"settings": {}})
print(stage.par)
```

```text
name   set                      value                describes
β      ℝ₊₊ @ (0, R^(ρ - 1))     0.9615384615384616   discount factor; its upper bound R^(ρ-1) is the return impatience condition, q < 1
ρ      (1, inf)                 2.0                  coefficient of relative risk aversion, greater than one
R      ℝ₊₊                      1.04                 gross interest factor
Γ      ℝ₊₊                      1.02                 permanent income growth factor
q      (0, 1) := (β*R)^(1/ρ)/R  0.9615384615384615   the return patience factor; the return impatience condition is q < 1
κ      1 - q                    0.03846153846153855  the marginal propensity to consume, one minus the return patience factor
h_lim  ℝ₊₊ := 1/(1 - Γ/R)       51.999999999999886   human wealth at the infinite horizon, the value that h = 1 + h*Γ/R maps to itself; positive exactly where Γ < R, the finite human wealth condition
L_lim  1 - h_lim                -50.999999999999886  the natural borrowing limit on market resources at the infinite horizon
```

The stage defines `q`; the methods define `κ`, `h_lim`, and `L_lim`. Human wealth `h` is a field, so `stage.par["h"]` is no longer a parameter query. `stage.methods` lists the three builders typed `!explicit` and the closed form of each builder's Evaluation, generated from the builder's method entry:

```python
print(stage.methods)
```

```text
cntn_to_dcsn            !explicit
cntn_to_dcsn.evaluate   !closed_form   generated from cntn_to_dcsn.method
dcsn_to_arvl            !explicit
dcsn_to_arvl.evaluate   !closed_form   generated from dcsn_to_arvl.method
policy                  !explicit
policy.evaluate         !closed_form   generated from policy.method
```

The endogenous grid method is bound in the same way from `methods.egm.bl`, with the three settings of the grid of savings given to `configure` as `{"settings": {"n_a": ..., "a_min": ..., "a_max": ...}}`.

## 8 Period and trellis

The stationary solution repeats one stage declaration with the same calibration sources and requires every backward field at its fixed point, including human wealth and the value field. Savings from one period become arrival assets in the next. The application holds no recipe or trellis file; [Trellises](../../Bellman-Sym/07-trellis.md) describes that declaration.

Human wealth also has a finite backward recursion. With zero supplied continuation wealth, the stage computes `h = 1`. Each preceding period adds current income to discounted future wealth. At the stationary calibration, the recursion is `51 → 52 → 51`.

The strict feasibility inequality excludes consuming all resources in the last period. With increasing utility and zero continuation value, that problem has no maximizer. The stationary coefficient `κ` also differs from its finite-horizon counterpart. The human-wealth check alone does not solve finite-horizon consumption.

## 9 Solution methods

Every route checks the complete continuation mapping before constructing kernels or grids, including under `!explicit`. The mapping supplies `V[>]` and `h[>]`. The returned `input_conditions` retain callable conditions that the package cannot decide.

**Closed form.** The module `code/closed_form_check.py` binds all four construction steps. It evaluates consumption, decision value, and arrival value through compiled kernels ([A builder](../../Bellman-Sym/API/stage/04-builder.md) §5).

The module compares the solution with the declared Bellman equation and arrival normalization. It also checks the relative Euler residual, feasibility, and present-value budget. The value functions require positive total wealth, $m > L$ at decision and $k > L$ at arrival. The module refuses evaluations elsewhere.

**Endogenous grid method.** The module binds `methods.egm.bl` with the three settings of the grid of savings and iterates the method to its fixed point on the compiled kernels of its lines, from a first iterate that consumes half of total wealth. One iteration applies the lines in the stage's backward order:

1. **Start** with the continuation marginal value $dV^{>}(a)$ on the exogenous grid of savings $\{a_1, \dots, a_n\}$, whose first point lies above $L$.
2. **InvEuler**: $c_i = (\beta\, dV^{>}(a_i))^{-1/\rho}$.
3. **Endogenous grid** (`g_cntn_to_dcsn`): $m_i = a_i + c_i$.
4. **Envelope** (the derivative line of `cntn_to_dcsn`): $dV_i = c_i^{-\rho}$.
5. **Arrival marginal** (the derivative line of `dcsn_to_arvl`): $dV^{<}(k) = R\,\Gamma^{-\rho}\, dV(Rk/\Gamma + 1)$, which is the next iteration's continuation marginal value at $k = a$.
6. **Iterate** until convergence. Human wealth is iterated with the policy: each step takes in the `h[>]` that the step after it hands back, `h = 1 + h[>]` and `h[<] = h*Γ/R`, starting from `h[>] = 0`, and uses the savings above its own limit `-h[>]`.

Calibration refuses a calibration at which $q \ge 1$, by the declared set of the discount factor and by the set that the definition of $q$ declares. The module refuses savings grids that start at or below $L$ and intermediate values that are not finite. It also refuses infeasible extrapolation and iterations that exhaust their limit without convergence. The consumption function is linear in $m$, and the linear interpolant of a linear function is exact, so the gridded route reaches the closed form on a grid of five points as on one of five hundred. The test of interpolation accuracy is therefore the comparison of the value function's interpolation by the module's linear and PCHIP (piecewise cubic Hermite) evaluators on 5, 50 and 500 nodes. The notebook `code/closed-form-and-grid.ipynb` shows each step and each comparison.

The function `gridded_step` computes one backward step for supplied continuation value, human wealth, and marginal value. It admits finite inputs when `Γ >= R`. The stationary function `gridded_route` and the closed-form methods require `Γ < R`.

## 10 Calibration

The calibration file, `declaration/calibration/perfect_foresight.yml`, holds the example of the chapter's section 4.1, an interest rate $r = 0.04$, a time preference rate $\vartheta = 0.04$, income growth $g = 0.02$ and $\rho = 2$, written as the factors the stage declares: $R = 1 + r$, $\beta = 1/(1 + \vartheta)$ and $\Gamma = 1 + g$.

```yaml
# The calibration of the perfect foresight stage: the example of Carroll and
# Lujan Solis, "Consumption Under Perfect Foresight and CRRA Utility" (A Gentle
# Introduction to Intertemporal Choice), section 4.1, r = ϑ = 0.04, g = 0.02
# and ρ = 2, written as factors: R = 1 + r, β = 1/(1 + ϑ) and Γ = 1 + g. At
# these values the return patience factor q = (Rβ)^(1/ρ)/R is 1/1.04, the
# marginal propensity to consume κ = 1 - q = 0.04/1.04, human wealth h = 52 and
# the natural borrowing limit L = 1 - h = -51, so a household with no assets,
# m = 1, consumes twice its permanent income (economics.md, "Calibration").
calibration:
  β: 0.9615384615384616
  ρ: 2.0
  R: 1.04
  Γ: 1.02
```

At these values

| Quantity | Value |
|---|---|
| return patience factor $q = (R\beta)^{1/\rho}/R$ | $1/1.04 \approx 0.9615$ |
| marginal propensity to consume $\kappa = 1 - q$ | $0.04/1.04 \approx 0.0385$ |
| human wealth $h = 1/(1 - \Gamma/R)$ | $52$ |
| natural borrowing limit $L = 1 - h$ | $-51$ |
| growth patience factor $(R\beta)^{1/\rho}/\Gamma$ | $1/1.02 \approx 0.9804$ |

so a household with no assets, $m = 1$, consumes $c = \kappa h = 2$, twice its permanent income.

## 11 Conditions for the solution

Two conditions, the chapter's equations (15) and (16), make the infinite-horizon solution well defined:

- **The return impatience condition**, $q < 1$: the marginal propensity to consume $\kappa = 1 - q$ is positive.
- **The finite human wealth condition**, $\Gamma < R$: human wealth is finite. At $\Gamma = R$ its formula divides by zero, and at $\Gamma > R$ the formula gives a finite negative number that is not human wealth.

The closed form needs neither the growth impatience condition nor a normalized discount factor $\beta\,\Gamma^{1-\rho} < 1$, and it holds for every $\rho > 1$; logarithmic utility, $\rho = 1$, needs its own utility and is not this stage. The files state each condition so that a calibration that breaks it is refused, with the condition named:

| Condition | Declaration | Refusal |
|---|---|---|
| $\Gamma < R$ | `h_lim : ℝ₊₊ := 1/(1 - Γ/R)` in the closed-form methods | `calibrate` with those methods; the stationary grid route also requires this condition |
| $q < 1$ | the declared set of the discount factor, `β : ℝ₊₊ @ (0, R^(ρ-1))`, whose upper bound $R^{\rho-1}$ is the condition written for $\beta$, and the set that the definition of the return patience factor declares, `q : (0,1) := (β*R)^(1/ρ)/R` | `calibrate`, under each methods file |
| $\rho > 1$ | the declared set `ρ : (1, inf)` | `calibrate` |
| finite parameters | the declared sets of the four parameters | `calibrate` |
| $m > L$, and $k > L$ at the arrival perch | the domain of each function of the closed form | the module, at each evaluation |

## 12 References

Carroll, C. D. and Lujan Solis, A. E. *A Gentle Introduction to Intertemporal Choice*, chapter "Consumption Under Perfect Foresight and CRRA Utility", sections 2 to 4. https://intertemporal-choice.github.io/content/consumption/perfforesightcrra.
