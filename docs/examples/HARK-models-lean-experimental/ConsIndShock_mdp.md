---
audience: user
type: example
topic: [applications]
---
# ConsIndShock — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Saving Model with Permanent and Transitory Income Shocks

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation |
|---------------|--------------|----------------------|
| `kNrm` | Prestate/Arrival perch | $k_t$ |
| `pLvlPrev` | Prestate/Arrival perch | $P_{t-1}$ |
| `PermShk` | Shock realization | $\Psi_t$ |
| `TranShk` | Shock realization | $\theta_t$ |
| `yNrm` | Post-shock intermediate | $y_t$ |
| `pLvl` | Post-shock state | $P_t$ |
| `G` | Growth factor realization | $G_t$ |
| `bNrm` | Post-shock intermediate | $b_t$ |
| `mNrm` | Decision perch state | $m_t$ |
| `cNrm` | Control/Action | $c_t$ |
| `aNrm` | Continuation perch state | $a_t$ |
| `live` | Survival indicator | $\mathbb{1}_{\text{survive}}$ |
| `cFunc` | Policy function | $c(m_t, P_t)$ |
| `Rfree` | Risk-free return | $R$ |
| `PermGroFac` | Expected growth factor | $\Gamma$ |
| `LivPrb` | Survival probability | $\mathcal{L}$ |

## 2. Model

### 2.1 Overview

We consider an infinite-horizon consumption-saving problem for a household facing idiosyncratic income risk. The household receives labor income subject to both **permanent shocks** and **transitory shocks**, and can save in a risk-free asset yielding gross return $R > 0$. The household faces **mortality risk** with survival probability $\mathcal{L} \in (0,1]$ each period.

All individual-level variables are normalized by the household's **permanent income level** $P_t$, which follows a stochastic growth process. This normalization ensures stationarity of the problem despite permanent income shocks.

### 2.2 Timing and Information Structure

The model follows a four-perch structure within each period $t$:

1. **Arrival Perch**: The agent enters period $t$ with normalized assets $k_t$ (capital carried forward from period $t-1$, normalized by $P_{t-1}$) and previous permanent income $P_{t-1}$.

2. **Decision Perch**: After observing current income shocks $(\Psi_t, \theta_t)$, permanent income updates to $P_t = P_{t-1} \cdot \Gamma \cdot \Psi_t$, and the agent computes normalized market resources $m_t$ (bank balances plus current income). The agent chooses consumption $c_t$ given information set $\mathcal{F}_t = \{k_t, P_{t-1}, \Psi_t, \theta_t\}$.

3. **Continuation Perch**: After consumption, the agent holds normalized end-of-period assets $a_t = m_t - c_t$. Survival is then determined.

4. **Twist/Transition**: Surviving agents carry forward $a_t$ as next period's $k_{t+1}$, and $P_t$ becomes $P_{t}$ (the "previous" permanent income for period $t+1$). Non-survivors exit the model.

### 2.3 State Space

**Arrival State Space**: The prestate is $\mathcal{S}_{\text{arr}} = \mathbb{R}_+ \times \mathbb{R}_{++}$, with elements $(k_t, P_{t-1})$ where:
- $k_t \in \mathbb{R}_+$ denotes normalized assets (beginning-of-period capital)
- $P_{t-1} \in \mathbb{R}_{++}$ denotes the permanent income level from the previous period

**Decision State Space**: After shocks realize, the decision state is $(m_t, P_t) \in \mathbb{R}_+ \times \mathbb{R}_{++}$ where:
- $m_t \coloneqq b_t + y_t$ represents normalized market resources
- $P_t$ is the updated permanent income level

**Continuation State Space**: After consumption choice, the continuation state is $(a_t, P_t) \in \mathbb{R}_+ \times \mathbb{R}_{++}$ where:
- $a_t \coloneqq m_t - c_t$ represents normalized end-of-period assets

### 2.4 Action Space

At the decision perch, the agent chooses normalized consumption $c_t \in [0, m_t]$. The budget constraint requires $c_t \leq m_t$, ensuring non-negative assets.

### 2.5 Shock Structure

**Income Shocks**: Each period, the household draws a shock pair $(\Psi_t, \theta_t)$ from a joint distribution:
$$(\Psi_t, \theta_t) \sim F_{\text{inc}}$$

where:
- $\Psi_t \in \mathbb{R}_{++}$ is a **permanent income shock** with $\mathbb{E}[\Psi_t] = 1$
- $\theta_t \in \mathbb{R}_+$ is a **transitory income shock** with $\mathbb{E}[\theta_t] = 1$

The permanent shock multiplies the permanent income level, creating a unit root component, while the transitory shock affects only current income.

**Survival Shock**: At the end of each period, the agent survives with probability $\mathcal{L}$:
$$\mathbb{1}_{\text{survive}} \sim \text{Bernoulli}(\mathcal{L})$$

Non-survivors exit the model (die without bequest motive in the baseline specification).

### 2.6 Transition Dynamics

The dynamics unfold sequentially within each period:

1. **Income shock realization**:
   $$(\Psi_t, \theta_t) \sim F_{\text{inc}}$$

2. **Normalized transitory income**:
   $$y_t \coloneqq \theta_t$$

3. **Permanent income growth**:
   $$G_t \coloneqq \Gamma \cdot \Psi_t$$
   $$P_t \coloneqq P_{t-1} \cdot G_t$$

4. **Normalized bank balances** (return on assets, adjusted for permanent income growth):
   $$b_t \coloneqq \frac{R \cdot k_t}{G_t}$$

   This captures that the gross return $R \cdot k_t$ (in period $t-1$ permanent income units) must be renormalized by $G_t$ to express in period $t$ permanent income units.

5. **Normalized market resources**:
   $$m_t \coloneqq b_t + y_t = \frac{R \cdot k_t}{G_t} + \theta_t$$

6. **Consumption decision**:
   $$c_t = c(m_t, P_t)$$

7. **End-of-period assets**:
   $$a_t \coloneqq m_t - c_t$$

8. **Survival determination**:
   $$\mathbb{1}_{\text{survive}} \sim \text{Bernoulli}(\mathcal{L})$$

9. **Twist to next period** (for survivors):
   $$k_{t+1} \coloneqq a_t, \quad P_{t} \to P_{t} \text{ (as } P_{t-1} \text{ for next period)}$$

### 2.7 Initial Distribution

At model "birth" (the agent's entry into the economy), the initial state is drawn from:
$$P_{-1} \sim F_{P,\text{init}}, \quad k_0 \sim F_{k,\text{init}}$$

where $F_{P,\text{init}}$ is the initial permanent income distribution and $F_{k,\text{init}}$ is the initial normalized capital distribution.

## 3. Bellman Equation

The household's problem is to maximize expected discounted utility over consumption, accounting for survival risk. We adopt the standard CRRA utility specification (though not explicitly given in the YAML, this is the HARK default):

$$u(C) = \frac{C^{1-\rho}}{1-\rho}$$

where $C$ denotes consumption in levels and $\rho > 1$ is the coefficient of relative risk aversion.

Given normalization by permanent income, we have $C_t = c_t \cdot P_t$, so:
$$u(C_t) = \frac{(c_t \cdot P_t)^{1-\rho}}{1-\rho} = \frac{c_t^{1-\rho} \cdot P_t^{1-\rho}}{1-\rho}$$

### 3.1 Continuation Value (Post-Decision)

At the continuation perch, after consuming $c_t$ and observing end-of-period assets $a_t$, the agent faces survival uncertainty. Let $\mathfrak{v}(a_t, P_t)$ denote the continuation value:

$$\mathfrak{v}(a_t, P_t) \coloneqq \mathcal{L} \cdot \mathbb{E}_t[\mathfrak{w}(a_t, P_t)]$$

where $\mathfrak{w}(a_t, P_t)$ is the arrival value for the next period (since $k_{t+1} = a_t$ and the permanent income $P_t$ is carried forward). The expectation is trivial here since no additional uncertainty realizes between the continuation perch and next period's arrival.

Thus:
$$\mathfrak{v}(a_t, P_t) = \mathcal{L} \cdot \mathfrak{w}(a_t, P_t)$$

Non-survivors receive zero continuation utility.

### 3.2 Decision Value (Post-Shock, Pre-Consumption)

At the decision perch, the agent observes market resources $m_t$ and current permanent income $P_t$. The information set is $\mathcal{F}_t = \{m_t, P_t\}$ (equivalently, $\{k_t, P_{t-1}, \Psi_t, \theta_t\}$). The agent chooses $c_t$ to maximize:

$$v(m_t, P_t) \coloneqq \max_{c_t \in [0, m_t]} \left\{ \frac{(c_t \cdot P_t)^{1-\rho}}{1-\rho} + \beta \cdot \mathfrak{v}(m_t - c_t, P_t) \right\}$$

where $\beta \in (0,1)$ is the time discount factor. Substituting the continuation value:

$$v(m_t, P_t) = \max_{c_t \in [0, m_t]} \left\{ \frac{(c_t \cdot P_t)^{1-\rho}}{1-\rho} + \beta \mathcal{L} \cdot \mathfrak{w}(m_t - c_t, P_t) \right\}$$

### 3.3 Arrival Value (Pre-Shock)

At the arrival perch, the agent holds normalized assets $k_t$ and previous permanent income $P_{t-1}$, but has not yet observed current period shocks. The arrival value is:

$$\mathfrak{w}(k_t, P_{t-1}) \coloneqq \mathbb{E}\left[v(m_t, P_t) \mid k_t, P_{t-1}\right]$$

Expanding the expectation over the shock distribution:

$$\mathfrak{w}(k_t, P_{t-1}) = \int \int v\left(\frac{R k_t}{\Gamma \Psi} + \theta, P_{t-1} \Gamma \Psi\right) dF_{\text{inc}}(\Psi, \theta)$$

This is the expected decision value, averaging over all possible realizations of permanent and transitory shocks.

### 3.4 Recursive Bellman System

Combining the three perches, the full Bellman system is:

**Arrival Value**:
$$\mathfrak{w}(k_t, P_{t-1}) = \mathbb{E}_{\Psi_t, \theta_t}\left[v\left(\frac{R k_t}{\Gamma \Psi_t} + \theta_t, P_{t-1} \Gamma \Psi_t\right)\right]$$

**Decision Value**:
$$v(m_t, P_t) = \max_{0 \leq c_t \leq m_t} \left\{ \frac{(c_t P_t)^{1-\rho}}{1-\rho} + \beta \mathcal{L} \cdot \mathfrak{w}(m_t - c_t, P_t) \right\}$$

**Continuation Value**:
$$\mathfrak{v}(a_t, P_t) = \mathcal{L} \cdot \mathfrak{w}(a_t, P_t)$$

The solution to this system is a policy function $c^*(m_t, P_t)$ (or, exploiting homogeneity, $c^*(m_t)$ in normalized terms).

### 3.5 Homogeneity and Normalization

A key property: with CRRA utility, the value function and policy functions are homogeneous of degree $1-\rho$ in permanent income. This allows us to work entirely in normalized variables. Define normalized value functions:

$$\tilde{v}(m_t) \coloneqq P_t^{\rho-1} \cdot v(m_t, P_t)$$
$$\tilde{\mathfrak{w}}(k_t) \coloneqq P_{t-1}^{\rho-1} \cdot \mathfrak{w}(k_t, P_{t-1})$$

Then the Bellman equations simplify to:

**Normalized Arrival Value**:
$$\tilde{\mathfrak{w}}(k_t) = \mathbb{E}_{\Psi_t, \theta_t}\left[(\Gamma \Psi_t)^{1-\rho} \cdot \tilde{v}\left(\frac{R k_t}{\Gamma \Psi_t} + \theta_t\right)\right]$$

**Normalized Decision Value**:
$$\tilde{v}(m_t) = \max_{0 \leq c_t \leq m_t} \left\{ \frac{c_t^{1-\rho}}{1-\rho} + \beta \mathcal{L} \cdot \tilde{\mathfrak{w}}(m_t - c_t) \right\}$$

The optimal consumption function $c^*(m_t)$ depends only on normalized market resources, not on the permanent income level.

## 4. First-Order Conditions

### 4.1 Euler Equation

The first-order condition for the consumption choice at the decision perch is:

$$u'(C_t) = \beta \mathcal{L} \cdot \mathbb{E}_t\left[\frac{\partial \mathfrak{w}(a_t, P_t)}{\partial a_t}\right]$$

In levels, with $C_t = c_t P_t$ and $u'(C_t) = C_t^{-\rho} = (c_t P_t)^{-\rho}$:

$$(c_t P_t)^{-\rho} = \beta \mathcal{L} \cdot \mathbb{E}_t\left[\frac{\partial \mathfrak{w}(a_t, P_t)}{\partial a_t}\right]$$
