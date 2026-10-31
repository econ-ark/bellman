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
(a) ──shocks (ψ, ξ)──▶ (m) ──c──▶ (a_nxt)
```

A single stage per period: the prestate $a$ (end-of-period assets from the previous period) is transformed by two shocks into market resources $m$; consumption $c$ determines end-of-period assets $a_{\text{nxt}} = m - c$.

## Stage YAML

```yaml
name: BufferStockConsumption

symbols:
  spaces:
    Xm: "@def R+"       # market resources
    Xa: "@def R+"        # end-of-period assets

  prestate:
    a: "@in Xa"          # end-of-period assets (from previous period)

  exogenous:
    psi:
      - "@in R++"
      - "@dist LogNormal(1, sigma_psi)"     # permanent shock, E[psi] = 1
    xi:
      - "@in R+"
      - "@dist Mixture(p_zero, 0, LogNormal(1, sigma_xi) / (1 - p_zero))"
                                             # transitory shock, E[xi] = 1

  states:
    m: "@in Xm"          # market resources (after shocks)

  poststates:
    a_nxt: "@in Xa"      # end-of-period assets

  controls:
    c: "@in R+"

  values:
    V[<]: "@in R"
    V: "@in R"

  values_marginal:
    dV[<]: "@in R+"
    dV: "@in R+"

  parameters:
    beta: "@in (0,1)"
    rho: "@in (1, Inf)"
    R: "@in R++"
    G: "@in R++"
    sigma_psi: "@in R+"
    sigma_xi: "@in R+"
    p_zero: "@in [0,1)"

equations:
  arvl_to_dcsn_transition: |
    m = R * a[<] / (G * psi) + xi

  dcsn_to_cntn_transition: |
    a_nxt[>] = m - c

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_c{c^(1-rho)/(1-rho) + beta * V[>]}
    InvEuler: |
      c = (beta * dV[>])^(-1/rho)
    ShadowBellman: |
      dV = c^(-rho)

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = E_{psi, xi}[(G * psi)^(1-rho) * V]
    ShadowBellman: |
      dV[<] = R * E_{psi, xi}[(G * psi)^(-rho) * dV]
```

### Arrival Transition

The arrival transition $m = R\,a^{<}\!/(\Gamma\psi) + \xi$ combines two steps from the levels problem:

1. **Bank balances**: $b = R\,a\,/(\Gamma\psi)$, where the denominator $\Gamma\psi$ is the realized permanent income growth factor.
2. **Market resources**: $m = b + \xi$, adding transitory income.

### Builders

**cntn_to_dcsn_builder** ($\mathbb{B}$): The decision builder contains the maximization problem and its EGM sub-equations:

- `Bellman`: the Bellman equation at the decision perch
- `InvEuler`: inverted Euler equation for EGM (consumption from marginal continuation value)
- `ShadowBellman`: envelope condition (marginal value from consumption)

**dcsn_to_arvl_builder** ($\mathbb{I}$): The arrival builder integrates over both shocks with the normalization weight:

- `Bellman`: $V^{<}(a) = \mathbb{E}_{\psi,\xi}[(\Gamma\psi)^{1-\rho}\, V(m)]$ where $m = Ra/(\Gamma\psi) + \xi$
- `ShadowBellman`: $dV^{<}(a) = R\,\mathbb{E}_{\psi,\xi}[(\Gamma\psi)^{-\rho}\, dV(m)]$

The $R$ factor in the marginal-value propagation arises from differentiating the arrival transition with respect to $a$.

## Period and Trellis

### Period Template

```yaml
name: BufferStockPeriod

stages:
  - consumption: !stage
```

A single non-branching stage per period.

### Stationary Trellis

```yaml
name: BufferStockLifecycle

periods:
  - buffer_stock_period: !period    # repeated identically (stationary)

inter_connectors:
  - rename: {a_nxt: a}             # end-of-period assets → next period's prestate
```

The model is stationary: every period uses the same stage file with the same parameters. The inter-period connector maps the poststate `a_nxt` to the next period's prestate `a`.

## Solution Method: EGM

The Endogenous Grid Method solves this model by inverting the Euler equation:

1. **Start** with continuation marginal value $dV^{>}(a)$ on an exogenous grid of end-of-period assets $\{a_1, \dots, a_n\}$.
2. **Expectation** (dcsn_to_arvl_builder): $dV^{<}(a_i) = R\,\mathbb{E}_{\psi,\xi}[(\Gamma\psi)^{-\rho}\, dV(Ra_i/(\Gamma\psi) + \xi)]$.
3. **InvEuler**: $c_i = (\beta \cdot dV^{<}(a_i))^{-1/\rho}$.
4. **Endogenous grid**: $m_i = a_i + c_i$.
5. **Envelope**: $dV_i = c_i^{-\rho}$.
6. **Iterate** until convergence.

The normalization weight $(\Gamma\psi)^{-\rho}$ in the marginal-value expectation (step 2) is the key difference from a model without permanent income growth.

## Calibration (Baseline)

```yaml
calibration:
  R: 1.03              # gross interest rate
  beta: 0.96           # discount factor
  G: 1.03              # permanent income growth factor
  rho: 2               # CRRA coefficient
  sigma_psi: 0.1       # std dev of log permanent shock
  sigma_xi: 0.1        # std dev of log transitory shock (conditional on employment)
  p_zero: 0.005        # unemployment probability

settings:
  grid_max_a: 50        # maximum assets for grid
  grid_size: 100        # number of grid points
```

## Key Features

### Permanent Income Normalization

Dividing by $P_t$ (for quantities) and $P_t^{1-\rho}$ (for the value function) eliminates the permanent income state. The cost is a growth-adjusted arrival transition and a normalization weight $(\Gamma\psi)^{1-\rho}$ inside the expectation operator.

### Natural Borrowing Constraint

The transitory shock $\xi$ has a point mass at zero (probability $\wp > 0$): the agent may receive zero income. This prevents the agent from choosing $c = m$ (which would risk zero consumption next period), generating a natural borrowing constraint without an explicit lower bound on assets.

### Weighted Expectations in the Arrival Builder

The dcsn_to_arvl_builder propagates both value and marginal value through a $(\Gamma\psi)$-weighted expectation. This weight is an artifact of the normalization, not an economic primitive: in the levels problem, the arrival builder would be a plain expectation $V^{<} = \mathbb{E}[V]$.
