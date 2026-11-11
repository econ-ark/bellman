---
audience: user
type: example
topic: [applications]
---
# Perfect foresight consumption with CRRA utility

> [!note] Source
> Application folder: [`applications/consumption-perfect-foresight-crra/`](../../../applications/consumption-perfect-foresight-crra/), which holds the model's stage file, `declaration/stages/perfect_foresight/perfect_foresight.bl`, beside it two methods files, `methods.bl`, an addition to the stage file that solves the model in closed form, and `methods.egm.bl`, which solves it by the endogenous grid method, and its calibration file, `declaration/calibration/perfect_foresight.yml`, in the layout of [Model directory layout](../../Bellman-Sym/reference/model-directory-layout.md). The folder's `economics.md` states the economics in full: the problem in levels and normalized by permanent income, the closed-form solution and its domain, and the conditions under which the solution exists.

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

The stage file, `declaration/stages/perfect_foresight/perfect_foresight.bl`, states the model: the sets of resources and savings, which are the whole real line since the household may borrow against its future income, the four parameters with their descriptions, the three derived parameters, utility and the set of feasible consumption, the two forward blocks, the two value blocks and the policy block, whose line is the maximization alone.

```bl
@stage: perfect_foresight

# The unconstrained perfect foresight consumption model with CRRA utility,
# normalized by permanent income: one state, market resources m, one control,
# consumption c, and no shock. It is the buffer-stock stage of
# applications/buffer-stock/ without its two income shocks. Two declared sets
# state the model's two conditions: the upper bound R^(ρ-1) of the discount
# factor is the return impatience condition, and the upper bound R of the
# growth factor is the finite human wealth condition. Three derived
# parameters, constants the stage defines from its parameters and the
# calibration does not supply, state the model's quantities: the return
# patience factor q, which is below one exactly under the return impatience
# condition, human wealth h, the present value of permanent income, and the
# natural borrowing limit L = 1 - h. Total wealth m - L, resources less this
# period's income plus human wealth, is positive exactly above the limit, and
# the feasible set is consumption below total wealth. The consumption
# function is known in closed form, c = κ(m - L) with κ = 1 - q, on m > L
# (economics.md).

Xm := ℝ
Xa := ℝ

β : (0,1) @ (0, R^(ρ-1))   :: ["discount factor; its upper bound R^(ρ-1) is the return impatience condition, q < 1"]
ρ : (1, inf)               :: ["coefficient of relative risk aversion, greater than one"]
R : ℝ₊₊                    :: ["gross interest factor"]
Γ : (0, R)                 :: ["permanent income growth factor; its upper bound R is the finite human wealth condition"]

q := (β*R)^(1/ρ)/R   :: ["the return patience factor; the return impatience condition is q < 1"]
h := 1/(1 - Γ/R)     :: ["human wealth, the present discounted value of permanent income"]
L := 1 - h           :: ["the natural borrowing limit on market resources, above which total wealth m - L is positive"]

𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]

Γ_c(x : Xm) := {c : ℝ₊₊ | c < x - L}   :: [id=feasible_consumption]

[id=arvl_to_dcsn, (k : Xa) : !arvl -> (m : Xm) : !dcsn] {
    m = R*k/Γ + 1                   :: [id=market_resources]
}

[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m - c                       :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = Γ^(1-ρ) * V              :: [id=value]
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])     :: [id=optimality]
}
```

### 6.1 Arrival transition

The arrival block `arvl_to_dcsn` writes $m = Rk/\Gamma + 1$: the return $R$ on the saving $k$, divided by the growth factor $\Gamma$ to normalize by this period's permanent income, plus this period's income, which is one. The decision block `dcsn_to_cntn` is the saving, $a = m - c$. Neither line has a shock.

### 6.2 Derived parameters

The lines `q := …`, `h := …` and `L := …` define three **derived parameters**, constants that the stage defines from its parameters and that the calibration does not supply: the return patience factor $q$, human wealth $h$ and the natural borrowing limit $L$. Their definitions follow the rule [`derived-parameter`](../../Bellman-Sym/reference/refusals.md#derived-parameter), and a calibration that names one of them is refused. `stage.par` lists them after the four declared parameters, with their definitions and, once a calibration is bound, their values (§7.3). The declared set of the growth factor, `Γ : (0, R)`, is an interval whose upper endpoint is the interest factor: the bound is the finite human wealth condition, and `calibrate` refuses a growth factor at or above the interest factor, naming the set (§11).

### 6.3 Builders

- `cntn_to_dcsn`, the decision value builder: $V = u(c) + \beta V^{>}$, at the consumption the policy chooses.
- `policy`, the policy builder: the maximization of $u(c') + \beta V^{>}$ over consumption $0 < c' < m - L$.
- `dcsn_to_arvl`, the arrival value builder: $V^{<} = \Gamma^{1-\rho}\, V$, which puts the decision value in the units of the previous period's permanent income, as the buffer stock stage writes $(\Gamma\psi)^{1-\rho}$ inside its expectation; here there is nothing to take an expectation over.

The stage file states no derivative and no numerical method: the two methods files beside it state the solutions, as the next section shows.

## 7 Methods and settings

Two methods files stand beside the stage file. Each is a `.bl` file read by the same grammar, whose blocks name the stage's blocks by their ids and add to them ([Methodization](../../Bellman-Sym/04-methodization.md)), and the stage is bound with one of them at a time: `methods.egm.bl` is given to the stage in place of `methods.bl`, not beside it.

### 7.1 Closed form

The addition `methods.bl` defines the marginal propensity to consume `κ = 1 - q`, the method's coefficient, as a derived parameter, and types [`!explicit`](../../Bellman-Sym/reference/methods.md#explicit) on the policy builder and on the two value builders. The line of each block writes the builder's output as an explicit function of the state of its own perch, the parameters and the derived parameters: the consumption function at the policy builder, the decision value at `cntn_to_dcsn` and the arrival value at `dcsn_to_arvl`, the last with the law of motion and the normalization $\Gamma^{1-\rho}$ written out. Each value block also writes its marginal in closed form, $\kappa^{-\rho}(m - L)^{-\rho}$ at the decision perch and $R\,\Gamma^{-\rho}$ times it at the resources $Rk/\Gamma + 1$ at the arrival perch, since a representation offers a derivative only where a line writes it. At the operative level, the builders the stage computes with, each line stands in place of the builder's declared line, the maximization or the value aggregation, which `stage.declared` keeps ([Methodization](../../Bellman-Sym/04-methodization.md) §5). `!explicit` gives the [Evaluation](../../Bellman-Sym/reference/operations.md#evaluation) of each of these builders the closed form, [`!closed_form`](../../Bellman-Sym/reference/methods.md#closed-form). The power `κ^(-ρ)` is defined for every $\rho > 1$ only at $\kappa > 0$, so `calibrate` refuses a calibration at which the return impatience condition $q < 1$ fails. The closed form reads no setting, and the folder holds no settings file.

```bl
@methods: perfect_foresight
# The closed-form solution of the perfect foresight stage, an addition to
# perfect_foresight.bl, the stage file beside this one (economics.md, "The
# solution in closed form"). The marginal propensity to consume κ = 1 - q is
# the method's coefficient and is defined here; the return patience factor q,
# human wealth h and the natural borrowing limit L = 1 - h are the stage's.
# Each of the three builders that the closed form solves is typed !explicit,
# and the lines of its block write its outputs as explicit functions of its
# own perch's state: the consumption function c = κ(m - L) at the policy
# builder, the decision value κ^(-ρ) (m - L)^(1-ρ)/(1-ρ) and its marginal at
# the decision value builder, and the arrival value, the decision value at
# the resources R*k/Γ + 1 normalized by Γ^(1-ρ), and its marginal at the
# arrival value builder, whose id arrival_marginal the module reads. At the
# operative level each line stands in place of the builder's declared line,
# which stage.declared keeps. !explicit gives the Evaluation of each builder
# the closed form, !closed_form. The power κ^(-ρ) is defined for every ρ > 1
# only at κ > 0, which is the return impatience condition q < 1, the upper
# bound of the discount factor in the stage file: calibrate refuses a
# calibration outside that bound, and one at which the computed κ is not
# positive. The functions hold on total wealth
# m - L > 0, and at the arrival perch on k > L; the application's module
# refuses an evaluation elsewhere.

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

### 7.2 Endogenous grid method

The methods file `methods.egm.bl` declares the three settings of the grid of savings with their sets, a count in ℕ and a bound a point of `Xa`, and names the endogenous grid method, [`!egm`](../../Bellman-Sym/reference/methods.md#egm), as the policy builder's method, with the exogenous grid of savings, `!Cartesian(a=(a_min, a_max, n_a))`, as its grid. Its three lines, the inverted Euler equation with the inverse marginal utility written out, the inverted law of motion and the identification of the chosen consumption with the candidate, stand in place of the maximization when the stage is solved. The consumption function is read by linear interpolation at the policy builder's Evaluation, `policy.evaluate`, between the pairs the method computes; those pairs give its nodes, so the entry writes no grid there. Each value builder gains its derivative line: the envelope condition `D_{m}V = c^(-ρ)` of the decision value, and the derivative of the arrival value, whose factor $R\,\Gamma^{-\rho}$ comes from the factor $R/\Gamma$ of the law of motion and the normalization $\Gamma^{1-\rho}$ of the value. The application's module supplies the three settings, so the folder holds no settings file.

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

The folder holds no recipe, so `load_stage` is given the stage file and its addition `methods.bl` together; `calibrate` then binds the calibration file, and `configure` binds an empty settings source, since the closed form reads no setting:

```python
from bellman.stage import elaborate_stage, load_stage

declaration = "applications/consumption-perfect-foresight-crra/declaration"
stage = elaborate_stage(load_stage(
    f"{declaration}/stages/perfect_foresight/perfect_foresight.bl",
    [f"{declaration}/stages/perfect_foresight/methods.bl"],
))
stage.calibrate(f"{declaration}/calibration/perfect_foresight.yml")
stage.configure({"settings": {}})
print(stage.par)
```

```text
name  set                      value                describes
β     (0, 1) @ (0, R^(ρ - 1))  0.9615384615384616   discount factor; its upper bound R^(ρ-1) is the return impatience condition, q < 1
ρ     (1, inf)                 2.0                  coefficient of relative risk aversion, greater than one
R     ℝ₊₊                      1.04                 gross interest factor
Γ     (0, R)                   1.02                 permanent income growth factor; its upper bound R is the finite human wealth condition
q     (β*R)^(1/ρ)/R            0.9615384615384615   the return patience factor; the return impatience condition is q < 1
h     1/(1 - Γ/R)              51.999999999999886   human wealth, the present discounted value of permanent income
L     1 - h                    -50.999999999999886  the natural borrowing limit on market resources, above which total wealth m - L is positive
κ     1 - q                    0.03846153846153855  the marginal propensity to consume, one minus the return patience factor
```

`stage.par` lists the four declared parameters with their sets and values, then the three derived parameters of the stage file and the coefficient `κ` of the methods file, each with its definition in place of a set and its value at the calibration: $q = 1/1.04$, $h = 52$, $L = -51$ and $\kappa = 0.04/1.04$, evaluated in floating point. `stage.methods` lists the three builders typed `!explicit` and the closed form of each builder's Evaluation, generated from the builder's method entry:

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

The model is stationary: every period holds the one stage with the same parameters, and the saving $a$ of one period is the arrival state $k$ of the next. The application holds no recipe and no trellis file; [Trellises](../../Bellman-Sym/07-trellis.md) states how a trellis is written. Over a finite horizon of $N$ periods, human wealth and the marginal propensity to consume depend on $N$, and in the last period the household consumes its resources, $c = m$; repeating the stationary stage with constant $h$ and $\kappa$ does not construct that problem, and the application makes no claim about a finite horizon.

## 9 Solution methods

**Closed form.** The module `code/closed_form_check.py` of the application binds `methods.bl` through `elaborate`, `methodize`, `calibrate` and `configure`, and reads the consumption function, the decision value and the arrival value from the compiled kernels of the three explicit blocks, the numerical functions the package compiles from their lines ([A builder](../../Bellman-Sym/API/stage/04-builder.md) §5); it writes no formula of them. It checks them against the stage file's own blocks, through their compiled kernels: the residual of the Bellman equation, the residual of the arrival value's normalization, the relative residual of the Euler equation, feasibility and the present-value budget. The three functions hold on total wealth $m - L > 0$, and at the arrival perch on $k > L$, and the module refuses an evaluation elsewhere.

**Endogenous grid method.** The module binds `methods.egm.bl` with the three settings of the grid of savings and iterates the method to its fixed point on the compiled kernels of its lines, from a first iterate that consumes half of total wealth. One iteration applies the lines in the stage's backward order:

1. **Start** with the continuation marginal value $dV^{>}(a)$ on the exogenous grid of savings $\{a_1, \dots, a_n\}$, whose first point lies above $L$.
2. **InvEuler**: $c_i = (\beta\, dV^{>}(a_i))^{-1/\rho}$.
3. **Endogenous grid** (`g_cntn_to_dcsn`): $m_i = a_i + c_i$.
4. **Envelope** (the derivative line of `cntn_to_dcsn`): $dV_i = c_i^{-\rho}$.
5. **Arrival marginal** (the derivative line of `dcsn_to_arvl`): $dV^{<}(k) = R\,\Gamma^{-\rho}\, dV(Rk/\Gamma + 1)$, which is the next iteration's continuation marginal value at $k = a$.
6. **Iterate** until convergence.

Calibration refuses a calibration at which $q \ge 1$, by the declared set of the discount factor. The module refuses a return patience factor that computes to one or more, a grid of savings that starts at or below $L$, an intermediate value that is not finite, an extrapolation that leaves the feasible set and an iteration that reaches its limit without converging. The consumption function is linear in $m$, and the linear interpolant of a linear function is exact, so the gridded route reaches the closed form on a grid of five points as on one of five hundred. The test of interpolation accuracy is therefore the comparison of the value function's interpolation by the module's linear and PCHIP (piecewise cubic Hermite) evaluators on 5, 50 and 500 nodes. The notebook `code/closed-form-and-grid.ipynb` shows each step and each comparison.

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

| Condition | How it is stated | Where it is refused |
|---|---|---|
| $\Gamma < R$ | the declared set of the growth factor, `Γ : (0, R)` | `calibrate` |
| $q < 1$ | the declared set of the discount factor, `β : (0,1) @ (0, R^(ρ-1))`, whose upper bound $R^{\rho-1}$ is the condition written for $\beta$ | `calibrate`, under each methods file |
| $\rho > 1$ | the declared set `ρ : (1, inf)` | `calibrate` |
| finite parameters | the declared sets of the four parameters | `calibrate` |
| $m > L$, and $k > L$ at the arrival perch | the domain of each function of the closed form | the module, at each evaluation |

## 12 References

Carroll, C. D. and Lujan Solis, A. E. *A Gentle Introduction to Intertemporal Choice*, chapter "Consumption Under Perfect Foresight and CRRA Utility", sections 2 to 4. https://intertemporal-choice.github.io/content/consumption/perfforesightcrra.
