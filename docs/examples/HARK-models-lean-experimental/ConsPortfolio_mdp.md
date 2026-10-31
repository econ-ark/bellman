---
audience: user
type: example
topic: [applications]
---
# ConsPortfolio — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Portfolio Choice with Risky Assets

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation | Perch |
|--------------|--------------|----------------------|-------|
| `kNrm` | Beginning-of-period normalized wealth | $k_t$ | Arrival (prestate) |
| `pLvlPrev` | Inbound permanent income level | $P_{t-1}$ | Arrival (prestate) |
| `SharePrev` | Previous period risky share | $\varsigma_{t-1}$ | Arrival (prestate) |
| `Risky` | Risky asset return realization | $R_t$ | Shock |
| `Rport` | Portfolio return realization | $\mathcal{R}_t$ | Post-shock |
| `Adjust` | Portfolio adjustment indicator | $\mathbb{1}_{\text{adj},t}$ | Shock |
| `yNrm` | Normalized labor income | $y_t$ | Post-shock |
| `pLvl` | Current permanent income level | $P_t$ | Post-shock |
| `bNrm` | Normalized bank balances | $b_t$ | Post-shock |
| `mNrm` | Normalized market resources | $m_t$ | Decision (poststate) |
| `cNrm` | Normalized consumption | $c_t$ | Control (decision) |
| `Share` | Current risky share | $\varsigma_t$ | Control (decision) |
| `aNrm` | Normalized end-of-period assets | $a_t$ | Continuation |
| `live` | Survival indicator | $\mathbb{1}_{\text{live},t+1}$ | End-of-period shock |
| `PermShk` | Permanent income shock | $\psi_t$ | Shock |
| `TranShk` | Transitory income shock | $\theta_t$ | Shock |

**Perch Structure:**
- **Arrival Perch**: $(k_t, P_{t-1}, \varsigma_{t-1})$ — agent enters period with these state variables
- **Decision Perch**: $(m_t, P_t, \varsigma_{t-1}, \mathbb{1}_{\text{adj},t})$ — agent makes consumption and portfolio decisions
- **Continuation Perch**: $(a_t, P_t, \varsigma_t)$ — agent ends period with these state variables

## 2. Model

### 2.1 State Spaces

The **arrival state** consists of three variables:
- $k_t \in \mathbb{R}_+$ — normalized wealth at the beginning of period $t$, representing assets carried forward from period $t-1$, normalized by permanent income $P_{t-1}$
- $P_{t-1} \in \mathbb{R}_{++}$ — permanent income level from the previous period
- $\varsigma_{t-1} \in [0,1]$ — the share of wealth allocated to risky assets in the previous period

The **decision state** augments the arrival state with realizations of shocks:
- $m_t \in \mathbb{R}_+$ — normalized market resources available for consumption and saving
- $P_t \in \mathbb{R}_{++}$ — updated permanent income level
- $\varsigma_{t-1} \in [0,1]$ — previous risky share (still relevant if adjustment is not possible)
- $\mathbb{1}_{\text{adj},t} \in \{0,1\}$ — indicator for whether portfolio rebalancing is feasible this period

The **continuation state** consists of:
- $a_t \in \mathbb{R}_+$ — normalized end-of-period assets
- $P_t \in \mathbb{R}_{++}$ — permanent income level
- $\varsigma_t \in [0,1]$ — risky asset share chosen this period

### 2.2 Action Spaces

The agent chooses:
- $c_t \in [0, m_t]$ — normalized consumption
- $\varsigma_t \in [0,1]$ — share of end-of-period assets invested in risky assets (subject to adjustment constraints)

When $\mathbb{1}_{\text{adj},t} = 0$, the agent cannot adjust the portfolio share, so $\varsigma_t = \varsigma_{t-1}$ is enforced.

### 2.3 Shock Distributions

**Within-period shocks** are drawn from a joint distribution:
$$(\psi_t, \theta_t, R_t) \sim F_{\text{shock}}$$
where:
- $\psi_t \in \mathbb{R}_{++}$ — permanent income shock with $\mathbb{E}[\psi_t] = 1$
- $\theta_t \in \mathbb{R}_+$ — transitory income shock with $\mathbb{E}[\theta_t] = 1$
- $R_t \in \mathbb{R}_{++}$ — gross return on risky assets

The **adjustment opportunity** occurs with probability:
$$\mathbb{P}(\mathbb{1}_{\text{adj},t} = 1) = \lambda$$
where $\lambda \coloneqq \texttt{AdjustPrb}$.

**End-of-period survival** occurs with probability:
$$\mathbb{P}(\mathbb{1}_{\text{live},t+1} = 1) = \mathfrak{p}$$
where $\mathfrak{p} \coloneqq \texttt{LivPrb}$.

### 2.4 Parameters

- $\mathsf{R} \coloneqq \texttt{Rfree} \in \mathbb{R}_{++}$ — gross risk-free return factor
- $\Gamma \coloneqq \texttt{PermGroFac} \in \mathbb{R}_{++}$ — expected permanent income growth factor
- $\mathfrak{p} \coloneqq \texttt{LivPrb} \in [0,1]$ — survival probability
- $\lambda \coloneqq \texttt{AdjustPrb} \in [0,1]$ — probability of being able to adjust portfolio share

### 2.5 Transition Dynamics

**From arrival to decision perch:**

Upon arrival with state $(k_t, P_{t-1}, \varsigma_{t-1})$, shocks are realized:
1. Draw $(\psi_t, \theta_t, R_t) \sim F_{\text{shock}}$
2. Calculate permanent income growth: $G_t \coloneqq \Gamma \cdot \psi_t$
3. Update permanent income: $P_t = P_{t-1} \cdot G_t$
4. Calculate realized portfolio return: $\mathcal{R}_t \coloneqq \mathsf{R} + (R_t - \mathsf{R}) \cdot \varsigma_{t-1}$
5. Calculate normalized bank balances: $b_t \coloneqq \mathcal{R}_t \cdot k_t / G_t$
6. Calculate normalized labor income: $y_t \coloneqq \theta_t$
7. Calculate normalized market resources: $m_t \coloneqq b_t + y_t$
8. Draw adjustment opportunity: $\mathbb{1}_{\text{adj},t} \sim \text{Bernoulli}(\lambda)$

**From decision to continuation perch:**

Given decisions $(c_t, \varsigma_t)$:
1. Calculate normalized end-of-period assets: $a_t \coloneqq m_t - c_t$
2. The continuation state is $(a_t, P_t, \varsigma_t)$

**From continuation to next arrival perch (twist):**

The mapping from continuation perch at time $t$ to arrival perch at time $t+1$ is:
1. Draw survival: $\mathbb{1}_{\text{live},t+1} \sim \text{Bernoulli}(\mathfrak{p})$
2. If $\mathbb{1}_{\text{live},t+1} = 1$: $(k_{t+1}, P_t, \varsigma_t) \leftarrow (a_t, P_t, \varsigma_t)$
3. If $\mathbb{1}_{\text{live},t+1} = 0$: agent is replaced by a newborn with initial distribution

This twist operation reveals the recursive structure: end-of-period normalized assets $a_t$ become next period's normalized wealth $k_{t+1}$, permanent income $P_t$ becomes $P_t$ (carried forward as $P_{t-1}$ notation in next period), and the chosen risky share $\varsigma_t$ becomes $\varsigma_{t-1}$ in the next period.

### 2.6 Preferences

The agent has time-separable CRRA preferences over consumption in levels:
$$u(C_t) = \frac{C_t^{1-\rho}}{1-\rho}$$

where $C_t = c_t \cdot P_t$ is consumption in levels. The normalization by permanent income yields utility from normalized consumption:
$$\tilde{u}(c_t, P_t) = \frac{(c_t \cdot P_t)^{1-\rho}}{1-\rho} = \frac{P_t^{1-\rho} \cdot c_t^{1-\rho}}{1-\rho}$$

The agent maximizes expected discounted lifetime utility with discount factor $\beta$.

## 3. Bellman Equation

The recursive structure decomposes across three perches, reflecting the timing of information revelation and decisions.

### 3.1 Arrival Value Function

At the **arrival perch**, the agent holds state $(k_t, P_{t-1}, \varsigma_{t-1})$ and faces uncertainty about shocks $(\psi_t, \theta_t, R_t, \mathbb{1}_{\text{adj},t})$. The arrival value is:

$$V^{\text{arr}}(k_t, P_{t-1}, \varsigma_{t-1}) = \mathbb{E}_{(\psi, \theta, R, \mathbb{1}_{\text{adj}})} \left[ V^{\text{dec}}(m_t, P_t, \varsigma_{t-1}, \mathbb{1}_{\text{adj},t}) \right]$$

where the expectation is taken over the joint shock distribution, and the decision state variables are determined by:
- $G_t = \Gamma \cdot \psi_t$
- $P_t = P_{t-1} \cdot G_t$
- $\mathcal{R}_t = \mathsf{R} + (R_t - \mathsf{R}) \cdot \varsigma_{t-1}$
- $b_t = \mathcal{R}_t \cdot k_t / G_t$
- $y_t = \theta_t$
- $m_t = b_t + y_t$

**Information set at arrival:** $\mathcal{I}^{\text{arr}}_t = \{k_t, P_{t-1}, \varsigma_{t-1}\}$

### 3.2 Decision Value Function

At the **decision perch**, all within-period shocks have been realized. The agent observes $(m_t, P_t, \varsigma_{t-1}, \mathbb{1}_{\text{adj},t})$ and chooses $(c_t, \varsigma_t)$ to maximize:

$$V^{\text{dec}}(m_t, P_t, \varsigma_{t-1}, \mathbb{1}_{\text{adj},t}) = \max_{c_t, \varsigma_t} \left\{ \tilde{u}(c_t, P_t) + \beta V^{\text{cont}}(a_t, P_t, \varsigma_t) \right\}$$

subject to:
- $c_t \in [0, m_t]$
- $a_t = m_t - c_t$
- If $\mathbb{1}_{\text{adj},t} = 1$: $\varsigma_t \in [0,1]$ (free choice)
- If $\mathbb{1}_{\text{adj},t} = 0$: $\varsigma_t = \varsigma_{t-1}$ (constrained)

This can be written more explicitly as:
$$V^{\text{dec}}(m_t, P_t, \varsigma_{t-1}, \mathbb{1}_{\text{adj},t}) = \mathbb{1}_{\text{adj},t} \cdot V^{\text{adj}}(m_t, P_t) + (1 - \mathbb{1}_{\text{adj},t}) \cdot V^{\text{fxd}}(m_t, P_t, \varsigma_{t-1})$$

where:

**Adjustment case** ($\mathbb{1}_{\text{adj},t} = 1$):
$$V^{\text{adj}}(m_t, P_t) = \max_{c_t \in [0,m_t], \varsigma_t \in [0,1]} \left\{ \tilde{u}(c_t, P_t) + \beta V^{\text{cont}}(m_t - c_t, P_t, \varsigma_t) \right\}$$

**Fixed share case** ($\mathbb{1}_{\text{adj},t} = 0$):
$$V^{\text{fxd}}(m_t, P_t, \varsigma_{t-1}) = \max_{c_t \in [0,m_t]} \left\{ \tilde{u}(c_t, P_t) + \beta V^{\text{cont}}(m_t - c_t, P_t, \varsigma_{t-1}) \right\}$$

**Information set at decision:** $\mathcal{I}^{\text{dec}}_t = \{m_t, P_t, \varsigma_{t-1}, \mathbb{1}_{\text{adj},t}, \psi_t, \theta_t, R_t\}$

### 3.3 Continuation Value Function

At the **continuation perch**, the agent has made decisions $(c_t, \varsigma_t)$ and holds state $(a_t, P_t, \varsigma_t)$. The continuation value accounts for survival uncertainty:

$$V^{\text{cont}}(a_t, P_t, \varsigma_t) = \mathfrak{p} \cdot V^{\text{arr}}(a_t, P_t, \varsigma_t) + (1 - \mathfrak{p}) \cdot V^{\text{death}}$$

where $V^{\text{death}}$ is the value of death (typically normalized to zero), and we use the twist mapping: $(k_{t+1}, P_t, \varsigma_t) = (a_t, P_t, \varsigma_t)$ for the surviving agent.

Substituting $V^{\text{death}} = 0$:
$$V^{\text{cont}}(a_t, P_t, \varsigma_t) = \mathfrak{p} \cdot V^{\text{arr}}(a_t, P_t, \varsigma_t)$$

**Information set at continuation:** $\mathcal{I}^{\text{cont}}_t = \{a_t, P_t, \varsigma_t, m_t, c_t\}$ (all within-period information)

### 3.4 Complete Bellman Recursion

Combining all three perches, the complete Bellman equation is:

$$\begin{align}
V^{\text{arr}}(k, P_{-1}, \varsigma_{-1}) &= \mathbb{E}_{(\psi, \theta, R, \mathbb{1}_{\text{adj}})} \left[ V^{\text{dec}}(m, P, \varsigma_{-1}, \mathbb{1}_{\text{adj}
