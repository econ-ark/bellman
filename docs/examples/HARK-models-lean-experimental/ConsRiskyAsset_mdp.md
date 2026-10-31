---
audience: user
type: example
topic: [applications]
---
# ConsRiskyAsset — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Saving with Risky Asset Allocation

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation |
|---------------|--------------|----------------------|
| `kNrm` | Prestate (arrival perch) | $k_t$ |
| `pLvlPrev` | Prestate (arrival perch) | $p_{t-1}$ |
| `PermShk` | Arrival shock | $\psi_t$ |
| `TranShk` | Arrival shock | $\theta_t$ |
| `yNrm` | Post-shock state | $y_t$ |
| `G` | Post-shock state | $G_t$ |
| `pLvl` | Post-shock state | $p_t$ |
| `bNrm` | Post-shock state | $b_t$ |
| `mNrm` | Decision perch state | $m_t$ |
| `cNrm` | Control (decision) | $c_t$ |
| `Share` | Control (decision) | $\varsigma_t$ |
| `wNrm` | Post-decision state | $w_t$ |
| `Risky` | Continuation shock | $R_t$ |
| `Rport` | Post-continuation state | $R_t^{\text{port}}$ |
| `aNrm` | Continuation perch state | $a_t$ |
| `qNrm` | Post-continuation state | $q_t$ |
| `live` | Survival shock | $\mathbb{1}_{\text{live},t}$ |
| `dead` | Death indicator | $\mathbb{1}_{\text{dead},t}$ |

**Timing convention:** The model operates in normalized space where all monetary variables are divided by permanent income from the previous period. The `twist` mapping connects end-of-period normalized assets $a_t$ to beginning-of-next-period normalized wealth $k_{t+1}$, and current permanent income $p_t$ to next period's incoming permanent income $p_t$ (which becomes $p_{t}$ at the start of period $t+1$).

## 2. Model

### 2.1 State Spaces

**Arrival (Prestate) Space:** At the beginning of period $t$, the agent arrives with:
- $k_t \in \mathbb{R}_+$ — normalized wealth (assets from previous period divided by $p_{t-1}$)
- $p_{t-1} \in \mathbb{R}_{++}$ — permanent income level carried forward from previous period

**Decision Space:** After observing income shocks, the agent has:
- $m_t \in \mathbb{R}_+$ — normalized market resources (cash-on-hand)
- $p_t \in \mathbb{R}_{++}$ — updated permanent income level

**Continuation Space:** After making consumption and portfolio decisions but before observing asset returns:
- $w_t \in \mathbb{R}_+$ — normalized wealth after consumption
- $\varsigma_t \in [0,1]$ — portfolio share in risky assets
- $p_t \in \mathbb{R}_{++}$ — permanent income level

**Terminal Space:** After asset returns realize:
- $a_t \in \mathbb{R}_+$ — normalized end-of-period assets
- $p_t \in \mathbb{R}_{++}$ — permanent income level

### 2.2 Action Spaces

The agent chooses:
- $c_t \in [0, m_t]$ — normalized consumption
- $\varsigma_t \in [0,1]$ — portfolio share allocated to risky assets

### 2.3 Shock Distributions

**Income Shocks (Arrival):** The joint distribution of permanent and transitory income shocks is given by
$$(\psi_t, \theta_t) \sim F_{\text{Inc}}$$
where $\psi_t \in \mathbb{R}_{++}$ is the permanent income shock (typically mean-one) and $\theta_t \in \mathbb{R}_+$ is the transitory income shock (also typically mean-one).

**Asset Return Shocks (Continuation):** The risky asset return is drawn from
$$R_t \sim F_{\text{Risky}}$$
where $R_t \in \mathbb{R}_+$ is the gross return factor on the risky asset.

**Survival Shocks:** At the end of each period, the agent survives with probability $\pi \in (0,1]$:
$$\mathbb{1}_{\text{live},t} \sim \text{Bernoulli}(\pi)$$

### 2.4 Transition Equations

The dynamics unfold in three stages within each period:

**Stage 1 (Arrival to Decision):** Given prestate $(k_t, p_{t-1})$ and income shocks $(\psi_t, \theta_t)$:

The permanent income growth factor is
$$G_t \coloneqq \Gamma \cdot \psi_t$$
where $\Gamma > 0$ is the deterministic permanent income growth factor.

Permanent income evolves as
$$p_t \coloneqq p_{t-1} \cdot G_t = p_{t-1} \cdot \Gamma \cdot \psi_t$$

Normalized bank balances account for permanent income growth:
$$b_t \coloneqq \frac{k_t}{G_t}$$

Normalized labor income equals the transitory shock:
$$y_t \coloneqq \theta_t$$

Normalized market resources combine bank balances and labor income:
$$m_t \coloneqq b_t + y_t = \frac{k_t}{G_t} + \theta_t$$

**Stage 2 (Decision to Continuation):** Given decision state $m_t$ and choices $(c_t, \varsigma_t)$:

Normalized wealth after consumption is
$$w_t \coloneqq m_t - c_t$$

**Stage 3 (Continuation to Terminal):** Given continuation state $(w_t, \varsigma_t)$ and risky return $R_t$:

The realized portfolio return is
$$R_t^{\text{port}} \coloneqq R_f + (R_t - R_f) \cdot \varsigma_t$$
where $R_f > 0$ is the risk-free return factor.

Normalized end-of-period assets are
$$a_t \coloneqq R_t^{\text{port}} \cdot w_t = [R_f + (R_t - R_f) \cdot \varsigma_t] \cdot w_t$$

Risky asset holdings are
$$q_t \coloneqq a_t \cdot \varsigma_t$$

**Twist (Terminal to Next Arrival):** The normalized assets and permanent income from period $t$ become the arrival state for period $t+1$:
$$k_{t+1} \coloneqq a_t, \quad p_t^{\text{incoming}} \coloneqq p_t$$

where $p_t^{\text{incoming}}$ serves as $p_t$ in the next period's dynamics (i.e., what we called $p_{t-1}$ when indexing from period $t+1$'s perspective).

### 2.5 Preferences

The agent has time-separable CRRA preferences over consumption with discount factor $\beta \in (0,1)$ and relative risk aversion $\rho > 0$:
$$u(C) \coloneqq \frac{C^{1-\rho}}{1-\rho}$$

In normalized form, with consumption $c_t$ measured relative to $p_{t-1}$, actual consumption is $C_t = c_t \cdot p_{t-1}$, giving:
$$u(c_t \cdot p_{t-1}) = \frac{(c_t \cdot p_{t-1})^{1-\rho}}{1-\rho} = p_{t-1}^{1-\rho} \cdot \frac{c_t^{1-\rho}}{1-\rho}$$

### 2.6 Initial Conditions

At model birth (period 0), the agent draws:
- $p_{-1} \sim F_{p,\text{init}}$ — initial permanent income level
- $k_0 \sim F_{k,\text{init}}$ — initial normalized wealth

## 3. Bellman Equation

The value function is decomposed across three perches, each corresponding to a different information set within the period.

### 3.1 Arrival Value Function (Pre-Income Shock)

At the arrival perch, before income shocks are observed, the value function is:
$$\mathcal{V}_t^{\text{arr}}(k_t, p_{t-1}) \coloneqq \mathbb{E}_{\psi_t, \theta_t}\left[\mathcal{V}_t^{\text{dec}}(m_t, p_t) \,\big|\, k_t, p_{t-1}\right]$$

where the expectation is over income shocks $(\psi_t, \theta_t) \sim F_{\text{Inc}}$, and market resources are determined by:
$$m_t = \frac{k_t}{\Gamma \psi_t} + \theta_t, \quad p_t = p_{t-1} \cdot \Gamma \cdot \psi_t$$

**Information set at arrival perch:** $\mathcal{I}_t^{\text{arr}} = \{k_t, p_{t-1}\}$

### 3.2 Decision Value Function (Post-Income, Pre-Decision)

At the decision perch, after observing income shocks, the agent solves:
$$\mathcal{V}_t^{\text{dec}}(m_t, p_t) \coloneqq \max_{c_t \in [0, m_t], \,\varsigma_t \in [0,1]} \left\{p_{t-1}^{1-\rho} \cdot u(c_t) + \beta \pi \cdot \mathcal{V}_t^{\text{cont}}(w_t, \varsigma_t, p_t)\right\}$$

where $w_t = m_t - c_t$ and $p_{t-1}$ is the permanent income level used for normalization.

**Note on normalization:** Since $p_t = p_{t-1} \cdot G_t$, we have $p_{t-1}^{1-\rho} = (p_t / G_t)^{1-\rho}$. The normalized flow utility is:
$$p_{t-1}^{1-\rho} \cdot \frac{c_t^{1-\rho}}{1-\rho} = \left(\frac{p_t}{G_t}\right)^{1-\rho} \cdot \frac{c_t^{1-\rho}}{1-\rho}$$

**Information set at decision perch:** $\mathcal{I}_t^{\text{dec}} = \{m_t, p_t, p_{t-1}\} = \{m_t, G_t, p_{t-1}\}$

### 3.3 Continuation Value Function (Post-Decision, Pre-Return)

At the continuation perch, after making consumption and portfolio choices but before observing asset returns:
$$\mathcal{V}_t^{\text{cont}}(w_t, \varsigma_t, p_t) \coloneqq \mathbb{E}_{R_t}\left[\mathcal{V}_{t+1}^{\text{arr}}(a_t, p_t) \,\big|\, w_t, \varsigma_t, p_t\right]$$

where the expectation is over risky returns $R_t \sim F_{\text{Risky}}$, and end-of-period assets are:
$$a_t = [R_f + (R_t - R_f) \cdot \varsigma_t] \cdot w_t$$

By the twist mapping, $a_t$ becomes $k_{t+1}$ and $p_t$ becomes $p_t^{\text{incoming}}$ (the permanent income at arrival in period $t+1$).

**Information set at continuation perch:** $\mathcal{I}_t^{\text{cont}} = \{w_t, \varsigma_t, p_t\}$

### 3.4 Complete Recursive Formulation

Combining all three perches, the complete Bellman equation is:

$$\mathcal{V}_t^{\text{arr}}(k_t, p_{t-1}) = \mathbb{E}_{\psi_t, \theta_t}\left[\max_{c_t, \varsigma_t} \left\{p_{t-1}^{1-\rho} \cdot u(c_t) + \beta \pi \cdot \mathbb{E}_{R_t}\left[\mathcal{V}_{t+1}^{\text{arr}}(a_t, p_t)\right]\right\}\right]$$

subject to:
\begin{align}
G_t &= \Gamma \cdot \psi_t\\
p_t &= p_{t-1} \cdot G_t\\
b_t &= k_t / G_t\\
m_t &= b_t + \theta_t\\
w_t &= m_t - c_t\\
a_t &= [R_f + (R_t - R_f) \cdot \varsigma_t] \cdot w_t\\
c_t &\in [0, m_t]\\
\varsigma_t &\in [0,1]
\end{align}

### 3.5 Stationary Formulation

For an infinite horizon problem with no explicit time dependence in primitives, we drop time subscripts and write:

$$\mathcal{V}^{\text{arr}}(k, p) = \mathbb{E}_{\psi, \theta}\left[\max_{c, \varsigma} \left\{p^{1-\rho} \cdot u(c) + \beta \pi \cdot \mathbb{E}_{R}\left[\mathcal{V}^{\text{arr}}(a, p')\right]\right\}\right]$$

where primes denote next-period values and:
- $m = k/(\Gamma \psi) + \theta$
- $p' = p \cdot \Gamma \cdot \psi$
- $w = m - c$
- $a = [R_f + (R - R_f) \cdot \varsigma] \cdot w$

## 4. First-Order Conditions

### 4.1 Consumption Euler Equation

The first-order condition with respect to consumption $c_t$ is:

$$p_{t-1}^{1-\rho} \cdot u'(c_t) = \beta \pi \cdot \frac{\partial \mathcal{V}_t^{\text{cont}}}{\partial w_t}(w_t, \varsigma_t, p_t)$$

By the envelope theorem on the continuation value:
$$\frac{\partial \mathcal{V}_t^{\text{cont}}}{\partial w_t} = \mathbb{E}_{R_t}\left[R_t^{\text{port}} \cdot \frac{\partial \mathcal{V}_{t+1}^{\text{arr}}}{\partial k_{t+1}}(a_t, p_t)\right]$$

where $R_t^{\text{port}} = R_f + (R_t - R_f) \cdot \varsigma_t$.

The envelope condition from the arrival value with respect to $k_{t+1}$ involves:
$$\frac{\partial \mathcal{V}_{t+1}^{\text{arr}}}{\partial k_{t+1}} = \mathbb{E}_{\psi_{t+1}, \theta_{t+1}}\left[\frac{1}{G_{t+1}} \cdot p_t^{1-\rho} \cdot u'(c_{t+1
