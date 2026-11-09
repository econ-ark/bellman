---
audience: user
type: example
topic: [applications]
---
# Buffer Stock Consumption Model (Normalized)

> [!note] Source
> Application folder: [`applications/buffer-stock/`](../../../applications/buffer-stock/), which holds the model's stage file, `declaration/stages/buffer_stock/buffer_stock.bl`, and, in `declaration/methods/`, its methods file and the two block files that file binds, in the layout of [Model directory layout](../../Bellman-Sym/reference/model-directory-layout.md). A related single-stage model, whose income is drawn independently each period and has no permanent component, is the application [`applications/consumption-savings-iid/`](../../../applications/consumption-savings-iid/).

**The canonical consumption-savings model with permanent and transitory income shocks, normalized by permanent income.**

This example presents the buffer stock saving model (Carroll, 2024) in its normalized (ratio) form. Normalizing by permanent income reduces the state from two variables $(\mathbf{m}, \mathbf{P})$ to one $(m = \mathbf{m}/\mathbf{P})$, yielding a stationary single-stage problem suitable for EGM.

> [!note] Source
> Based on Carroll (2024), "Theoretical Foundations of Buffer Stock Saving," Problem $\mathscr{P}_N$.

## Model Overview

| Feature | Description |
|---------|-------------|
| **Stages** | 1 (consumption-savings with expectation and maximization) |
| **Shocks** | Permanent ($\psi$) and transitory ($\xi$), IID |
| **Solution** | Endogenous Grid Method (EGM) |
| **State** | Normalized market resources $m$ |
| **Horizon** | Infinite (stationary) |

## Bellman Equation

$$
v(m) = \max_{0 < c < m} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta \,\mathbb{E}\!\left[(\Gamma \psi')^{1-\rho}\, v\!\left(\frac{R\,(m - c)}{\Gamma \psi'} + \xi'\right)\right] \right\}
$$

subject to:

$$
\begin{aligned}
a &= m - c \\
m' &= \frac{R}{\Gamma \psi'}\, a + \xi'
\end{aligned}
$$

Variables (all normalized by permanent income $P_t$):

- $m$ = market resources
- $c$ = consumption
- $a$ = end-of-period assets
- $\psi$ = permanent income shock ($\mathbb{E}[\psi] = 1$, $\psi \in [\underline{\psi}, \bar{\psi}]$)
- $\xi$ = transitory income shock ($\mathbb{E}[\xi] = 1$; equals zero with probability $\wp > 0$)
- $R$ = gross interest rate
- $\Gamma$ = deterministic permanent income growth factor
- $\beta$ = discount factor
- $\rho$ = coefficient of relative risk aversion ($\rho > 1$)

The weighting factor $(\Gamma \psi)^{1-\rho}$ arises from normalizing the value function: $v(m) \;=\; \mathbf{V}(\mathbf{m}, \mathbf{P})\,/\,\mathbf{P}^{1-\rho}$.

## First-Order Conditions

**Euler equation:**

$$
c^{-\rho} = R\,\beta\,\mathbb{E}\!\left[(\Gamma \psi')^{-\rho}\, c'(m')^{-\rho}\right]
$$

**Envelope condition:**

$$
v'(m) = c(m)^{-\rho}
$$

## State-Space Diagram

```
(k) ──shocks (ψ, ξ)──▶ (m) ──c──▶ (a)
```

A single stage per period: the arrival state $k$, the assets carried from the previous period, is transformed by two shocks into market resources $m$; consumption $c$ determines the end-of-period assets $a = m - c$.

## Stage File

The stage file, `declaration/stages/buffer_stock/buffer_stock.bl`, states the model: the sets of resources and assets, the parameters with their descriptions, the two shocks and their laws, utility and the set of feasible consumption, the two forward blocks, the two value blocks and the policy block, whose line is the maximization alone.

```bl
@stage: buffer_stock

Xm := ℝ₊₊
Xa := ℝ₊₊

β : (0,1)        :: ["discount factor"]
ρ : (1, inf)     :: ["coefficient of relative risk aversion, greater than one"]
R : ℝ₊₊          :: ["gross interest rate"]
Γ : ℝ₊₊          :: ["deterministic permanent income growth factor"]
σ_ψ : ℝ₊         :: ["standard deviation of the log permanent shock"]
σ_ξ : ℝ₊         :: ["standard deviation of the log transitory shock, conditional on a positive draw"]
μ_ξ : ℝ          :: ["log-mean of the positive transitory draw; E[ξ] = 1 requires μ_ξ = -log(1 - p_zero) - σ_ξ^2/2"]
p_zero : (0,1)   :: ["probability ℘ of a zero transitory draw"]

ψ : ℝ₊₊
ψ ~ LogNormal(-(σ_ψ^2)/2, σ_ψ)
ξ : ℝ₊
ξ ~ Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_ξ, σ_ξ)))

𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]
𝑑𝑢     := D_{c}(𝑢)                   :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)                    :: [id=inv_marg_util]

Γ_c(x : ℝ₊₊) := {c : ℝ₊₊ | c < x}   :: [id=feasible_consumption]

[id=arvl_to_dcsn, (k : Xa, ψ, ξ) : !arvl -> (m : Xm) : !dcsn] {
    m = R*k/(Γ*ψ) + ξ               :: [id=market_resources]
}

[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m - c                       :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])     :: [id=optimality]
}
```

### Arrival Transition

The arrival block `arvl_to_dcsn` writes $m = R\,k/(\Gamma\psi) + \xi$, which combines two steps from the levels problem:

1. **Bank balances**: $b = R\,k/(\Gamma\psi)$, where the denominator $\Gamma\psi$ is the realized permanent income growth factor.
2. **Market resources**: $m = b + \xi$, adding transitory income.

### Builders

- `cntn_to_dcsn`, the decision value builder: $V = u(c) + \beta V^{>}$, at the consumption the policy chooses.
- `policy`, the policy builder: the maximization of $u(c') + \beta V^{>}$ over consumption $c' < m$.
- `dcsn_to_arvl`, the arrival value builder: $V^{<} = \mathbb{E}_{\psi,\xi}[(\Gamma\psi)^{1-\rho}\, V]$, the decision value read at $m = R\,k/(\Gamma\psi) + \xi$.

The stage file states no derivative and no numerical method: the marginal blocks state the derivatives, and the methods file binds the methods, as the next section shows.

## Methods, Block Files and Settings

The methods file, `declaration/methods/buffer_stock.yml`, binds the endogenous grid method on the policy builder with its block file and its exogenous grid of savings; the linear interpolation of the consumption function at the policy builder's [Evaluation](../../Bellman-Sym/reference/operations.md#evaluation), `policy.evaluate`, which writes no grid, since its knots are the pairs the method computes; the marginal blocks of the decision and arrival value builders; Gauss–Hermite quadrature at the expectation over the two shocks; and the linear interpolation of the arrival value and its stated derivative at the arrival builder's Evaluation, `dcsn_to_arvl.evaluate.value` and `dcsn_to_arvl.evaluate.marginal`, on the grid of assets. Each grid is the setting `grid`, whose value is the grid's kind, the tag `!Cartesian`, with the grid's order and bounds beside it ([Methodization](../../Bellman-Sym/04-methodization.md) §3):

```yaml
stage: buffer_stock
# The buffer-stock stage's methods. The stage file writes the values and the
# maximization alone; the block file buffer_stock_egm.bl, beside this file,
# opens the policy builder with the endogenous grid method, and the block file
# marginals.bl states the derivatives of the decision value and the arrival
# value, one marginal block for each value builder.
#
# At the decision side, the endogenous grid method stands on the policy builder
# itself, and its setting grid names the exogenous grid of savings a on which
# its candidate line is evaluated: the kind of the grid is the tag on the value
# of grid, !Cartesian, and its order and bounds, the settings n_a, a_min and
# a_max, stand beside it. The consumption function is read by linear
# interpolation between the candidate pairs the method computes; the
# interpolation is bound at the policy builder's Evaluation, policy.evaluate,
# and writes no grid, since its knots are the pairs the method stores. The
# decision value's derivative, D_{m}V = 𝑑𝑢(c), is read through the interpolated
# consumption and takes no representation of its own, and the decision value
# is not represented, as the HARK solution builds no value function.
#
# At the arrival builder dcsn_to_arvl, the expectation over the two income
# shocks is taken by quadrature with the node counts the settings name, seven
# for each shock, the point mass of the transitory shock at zero exact; and the
# arrival value and its stated derivative, D_{k}V[<], are represented at the
# Evaluation of the arrival builder, dcsn_to_arvl.evaluate.value and
# dcsn_to_arvl.evaluate.marginal, by the basis !Linear, read between its nodes
# by linear interpolation, on the grid of assets k that the setting grid names
# by its kind, !Cartesian, with its order and bounds beside it.
# The counts and the grids are those of the HARK solution of this model in the
# QuantEcon community library (projects/HARK/buffer-stock/tutorial.ipynb,
# HARK 0.17.1), whose seven values per shock are equiprobable conditional means
# and whose 960 asset points from 0.001 to 20 are exponentially nested with
# factor 3, one grid serving as the exogenous grid of savings and as the grid of
# assets; the method table names no equiprobable rule and no nesting, so the
# rule here is Gauss-Hermite and each grid is stated by its order and bounds.
methods:
  - on: policy
    method: !egm
    block: buffer_stock_egm.bl
    settings: {grid: !Cartesian, orders: {a: n_a}, bounds: {a: [a_min, a_max]}}
  - on: policy.evaluate
    method: !Linear
  - on: cntn_to_dcsn
    method: !marginals
    block: marginals.bl
  - on: dcsn_to_arvl
    method: !marginals
    block: marginals.bl
  - on: E_ψ_ξ
    method: !gauss-hermite
    settings: {n_nodes: [n_ψ_nodes, n_ξ_nodes]}
  - on: dcsn_to_arvl.evaluate.marginal
    method: !Linear
    settings: {grid: !Cartesian, orders: {k: n_k}, bounds: {k: [k_min, k_max]}}
  - on: dcsn_to_arvl.evaluate.value
    method: !Linear
    settings: {grid: !Cartesian, orders: {k: n_k}, bounds: {k: [k_min, k_max]}}
```

The block file `buffer_stock_egm.bl` holds the method block of the endogenous grid method: the inverted Euler equation, the grid line that gives the resources at each saving, and the identification of consumption with its candidate.

```bl
@methods: buffer_stock
# The endogenous grid method as the method block of the policy builder, whose
# stage file states the maximization alone. The candidate line reads the
# derivative of the continuation value by the term D_{a}V[>].
# The grid line inverts the law of motion a = m - c, giving the decision state
# m at each saving, and is named g_cntn_to_dcsn, the map from the continuation
# perch to the decision perch; the methods file binds the interpolation of the
# consumption function at the policy builder's Evaluation, policy.evaluate.

[id=egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}
```

The block file `marginals.bl` holds the two marginal blocks. The decision value's line is the envelope condition; the arrival value's line keeps the factor $R/(\Gamma\psi)$ of the law of motion with the normalization $(\Gamma\psi)^{1-\rho}$, which together give the weight $R\,(\Gamma\psi)^{-\rho}$ inside the expectation.

```bl
@methods: buffer_stock
# The derivatives of the two values of the buffer-stock stage, each stated by
# the marginal block of the value builder that writes the value. The decision
# value's line is the envelope condition. The arrival value's line keeps the
# factor R/(Γ*ψ) of the law m = R*k/(Γ*ψ) + ξ and the normalization
# (Γ*ψ)^(1-ρ) of the value, since that law is not the identity.

[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {
    D_{m}V = 𝑑𝑢(c)                                  :: [id=marginal]
}

[id=arvl_marginal, (V) : !dcsn -> (V[<]) : !arvl] {
    D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)    :: [id=marginal]
}
```

The settings file, `declaration/settings/buffer_stock.yml`, gives the numbers of quadrature nodes of the two shocks, the exogenous grid of savings and the grid of assets:

```yaml
# The buffer-stock stage's numerical settings: the quadrature nodes of the two
# income shocks at the arrival builder's expectation, the exogenous grid of
# savings a of the endogenous grid method, and the grid of assets k on which
# the arrival value and its derivative are represented. The values are those
# of the HARK solution of this model in the QuantEcon community library
# (projects/HARK/buffer-stock/tutorial.ipynb): seven points per shock, and 960
# asset points from 0.001 to 20, one grid in that solution for savings and for
# assets.
settings:
  n_ψ_nodes: 7
  n_ξ_nodes: 7
  n_a: 960
  a_min: 0.001
  a_max: 20.0
  n_k: 960
  k_min: 0.001
  k_max: 20.0
```

## Period and Trellis

The model is stationary: every period holds the one stage with the same parameters, and the inter-period connector joins the end-of-period assets $a$ of one period to the arrival state $k$ of the next. The application holds no recipe and no trellis file; [Trellises](../../Bellman-Sym/07-trellis.md) states how a trellis is written.

## Solution Method: EGM

The Endogenous Grid Method solves this model by inverting the Euler equation:

1. **Start** with continuation marginal value $dV^{>}(a)$ on an exogenous grid of end-of-period assets $\{a_1, \dots, a_n\}$.
2. **Expectation** (the marginal block `arvl_marginal`): $dV^{<}(a_i) = R\,\mathbb{E}_{\psi,\xi}[(\Gamma\psi)^{-\rho}\, dV(Ra_i/(\Gamma\psi) + \xi)]$.
3. **InvEuler**: $c_i = (\beta \cdot dV^{<}(a_i))^{-1/\rho}$.
4. **Endogenous grid** (`g_cntn_to_dcsn`): $m_i = a_i + c_i$.
5. **Envelope** (the marginal block `dcsn_marginal`): $dV_i = c_i^{-\rho}$.
6. **Iterate** until convergence.

The normalization weight $(\Gamma\psi)^{-\rho}$ in the marginal-value expectation (step 2) is the key difference from a model without permanent income growth.

## Calibration (Baseline)

The application holds no calibration file. A baseline calibration takes `R` = 1.03, `β` = 0.96, `Γ` = 1.03, `ρ` = 2, `σ_ψ` = 0.1, `σ_ξ` = 0.1 and `p_zero` = 0.005; `μ_ξ` follows from `σ_ξ` and `p_zero` by the description the stage file gives it, `μ_ξ = -log(1 - p_zero) - σ_ξ^2/2`, so that the mean of $\xi$ is one. The numerical settings are those of the settings file above.

## Key Features

### Permanent Income Normalization

Dividing by $P_t$ (for quantities) and $P_t^{1-\rho}$ (for the value function) eliminates the permanent income state. The cost is a growth-adjusted arrival transition and a normalization weight $(\Gamma\psi)^{1-\rho}$ inside the expectation operator.

### Natural Borrowing Constraint

The transitory shock $\xi$ has a point mass at zero (probability $\wp > 0$): the agent may receive zero income. This prevents the agent from choosing $c = m$ (which would risk zero consumption next period), generating a natural borrowing constraint without an explicit lower bound on assets.

### Weighted Expectations in the Arrival Builder

The arrival builder `dcsn_to_arvl` writes the value, and the marginal block `arvl_marginal` states its derivative, each as a $(\Gamma\psi)$-weighted expectation. This weight is an artifact of the normalization, not an economic primitive: in the levels problem, the arrival builder would be a plain expectation $V^{<} = \mathbb{E}[V]$.
