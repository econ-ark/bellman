---
audience: user
type: example
topic: [applications]
---
# ConsMarkov — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Saving Model with Markov State Transitions

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation |
|--------------|--------------|----------------------|
| `kNrm` | Prestate (Arrival perch) | $k_t \in \mathbb{R}_+$ |
| `pLvlPrev` | Prestate (Arrival perch) | $p_{t-1} \in \mathbb{R}_{++}$ |
| `zPrev` | Prestate (Arrival perch) | $z_{t-1} \in \{1, \ldots, N_z\}$ |
| `Mrkv`, `z` | Poststate (Decision perch) | $z_t \in \{1, \ldots, N_z\}$ |
| `PermShk` | Shock realization | $\psi_t \in \mathbb{R}_{++}$ |
| `TranShk` | Shock realization | $\theta_t \in \mathbb{R}_+$ |
| `yNrm` | Income at decision perch | $y_t \coloneqq \theta_t$ |
| `pLvl` | Permanent income at decision | $p_t \in \mathbb{R}_{++}$ |
| `bNrm` | Bank balances at decision | $b_t \in \mathbb{R}$ |
| `mNrm` | Market resources (decision state) | $m_t \in \mathbb{R}_+$ |
| `cNrm` | Control variable | $c_t \in [0, m_t]$ |
| `aNrm` | Postdecision state (Continuation perch) | $a_t \in \mathbb{R}_+$ |
| `live` | Survival indicator | $\ell_{t+1} \in \{0, 1\}$ |
| `Rfree[z]` | State-dependent return factor | $R(z) \in \mathbb{R}_{++}$ |
| `PermGroFac[z]` | State-dependent growth factor | $\Gamma(z) \in \mathbb{R}_{++}$ |
| `LivPrb[z]` | State-dependent survival probability | $\pi(z) \in [0, 1]$ |
| `MrkvArray` | Markov transition matrix | $\mathbb{P}_{z' \mid z} \in [0,1]^{N_z \times N_z}$ |
| `IncShkDstn[z]` | State-dependent shock distribution | $F_z(\psi, \theta)$ |
| `cFuncX` | Policy function | $c^*(z, m)$ |

**Timing convention**: Variables at the arrival perch are indexed by their continuation-perch origin. The twist operation maps continuation-perch variables from period $t$ to arrival-perch variables for period $t+1$.

## 2. Model

### 2.1 State and Action Spaces

The model features a three-dimensional state space at the **arrival perch**:
- **Normalized capital**: $k_t \in \mathbb{R}_+ \coloneqq [0, \infty)$, representing assets brought into period $t$, normalized by permanent income $p_{t-1}$ from the previous period.
- **Previous permanent income level**: $p_{t-1} \in \mathbb{R}_{++} \coloneqq (0, \infty)$, the level of permanent income from the end of period $t-1$.
- **Previous Markov state**: $z_{t-1} \in \mathcal{Z} \coloneqq \{1, 2, \ldots, N_z\}$, a finite discrete state space.

The arrival state is thus $(k_t, p_{t-1}, z_{t-1}) \in \mathbb{R}_+ \times \mathbb{R}_{++} \times \mathcal{Z}$.

At the **decision perch**, after observing the current Markov state $z_t$ and income shocks $(\psi_t, \theta_t)$, the agent observes:
- **Current Markov state**: $z_t \in \mathcal{Z}$
- **Permanent income level**: $p_t = p_{t-1} \cdot \Gamma(z_t) \cdot \psi_t$
- **Market resources** (normalized): $m_t = b_t + y_t$ where:
  - $b_t \coloneqq \frac{R(z_t) \cdot k_t}{\Gamma(z_t) \cdot \psi_t}$ (normalized bank balances)
  - $y_t \coloneqq \theta_t$ (normalized labor income)

The decision state is $(z_t, m_t, p_t) \in \mathcal{Z} \times \mathbb{R}_+ \times \mathbb{R}_{++}$.

The **action space** consists of normalized consumption $c_t \in [0, m_t]$, which determines normalized end-of-period assets $a_t \coloneqq m_t - c_t \in \mathbb{R}_+$.

The **continuation perch** state is $(a_t, p_t, z_t)$, from which the agent may die with probability $1 - \pi(z_t)$ or survive to enter the next period.

### 2.2 Shock Distributions

The model features two sources of randomness:

**Markov state transitions**: Given the previous discrete state $z_{t-1}$, the current state evolves according to
$$z_t \sim \mathbb{P}(\cdot \mid z_{t-1}), \quad \text{where } \mathbb{P}_{ij} \coloneqq \Pr(z_t = j \mid z_{t-1} = i).$$

**Income shocks**: Conditional on the realized Markov state $z_t$, the agent draws permanent and transitory income shocks from a state-dependent joint distribution:
$$(\psi_t, \theta_t) \sim F_{z_t}(\psi, \theta).$$
Here $\psi_t \in \mathbb{R}_{++}$ is a multiplicative permanent shock and $\theta_t \in \mathbb{R}_+$ is a transitory shock to normalized labor income.

**Mortality**: At the end of the period, conditional on discrete state $z_t$, the agent survives to period $t+1$ with probability $\pi(z_t)$:
$$\ell_{t+1} \sim \text{Bernoulli}(\pi(z_t)).$$
If the agent dies ($\ell_{t+1} = 0$), we assume the value is zero and the agent is replaced by a newborn agent drawn from the initial distribution.

### 2.3 State Transitions

The timing and information structure follow the ADC perch decomposition:

1. **Arrival perch → Decision perch**: The agent enters period $t$ with arrival state $(k_t, p_{t-1}, z_{t-1})$. The Markov state transitions:
   $$z_t \sim \mathbb{P}(\cdot \mid z_{t-1}).$$
   Income shocks are then realized:
   $$(\psi_t, \theta_t) \sim F_{z_t}(\psi, \theta).$$
   The permanent income level evolves:
   $$p_t = p_{t-1} \cdot \Gamma(z_t) \cdot \psi_t,$$
   where $\Gamma(z_t)$ is the state-dependent expected permanent income growth factor. Normalized bank balances and market resources are computed:
   $$b_t = \frac{R(z_t) \cdot k_t}{\Gamma(z_t) \cdot \psi_t}, \quad m_t = b_t + \theta_t.$$
   The information set at the decision perch is $\mathcal{F}_t^d = \{z_t, m_t, p_t\}$ (plus all history).

2. **Decision perch → Continuation perch**: The agent chooses consumption $c_t$, determining end-of-period assets:
   $$a_t = m_t - c_t.$$
   The continuation state is $(a_t, p_t, z_t)$. The information set at the continuation perch is $\mathcal{F}_t^c = \{a_t, p_t, z_t\}$.

3. **Continuation perch → Next arrival perch (twist)**: The agent's survival is realized:
   $$\ell_{t+1} \sim \text{Bernoulli}(\pi(z_t)).$$
   If the agent survives ($\ell_{t+1} = 1$), the continuation state maps to the next period's arrival state via:
   $$k_{t+1} = a_t, \quad p_t \to p_t, \quad z_t \to z_t.$$
   More precisely, the twist operation is:
   $$\text{twist}: (a_t, p_t, z_t) \mapsto (k_{t+1}, p_{t}, z_{t}) \coloneqq (a_t, p_t, z_t).$$
   This prepares the state for the next period's arrival perch, where $z_t$ becomes $z_{t-1}$ in the next iteration and $p_t$ becomes $p_{t-1}$.

### 2.4 Preferences

The model implicitly assumes time-separable CRRA preferences. Although not explicitly stated in the YAML, the typical specification is:
$$u(c) = \frac{c^{1-\rho}}{1-\rho}, \quad \rho > 0,$$
with time discount factor $\beta \in (0, 1)$. The value function at the decision perch is:
$$v(z, m, p) = \max_{c \in [0, m]} \left\{ u(c) + \beta \pi(z) \mathbb{E}_{z', \psi', \theta' \mid z} w(a, p, z) \right\},$$
where $a = m - c$ and $w$ denotes the continuation value.

For normalized problems, it is common to assume that the value function is homogeneous of degree $1-\rho$ in $p$, so we can write:
$$v(z, m, p) = p^{1-\rho} \tilde{v}(z, m),$$
where $\tilde{v}$ is the normalized value function depending only on the discrete state and normalized market resources.

## 3. Bellman Equation

We decompose the recursive problem into three perches following the ADC framework.

### 3.1 Arrival Perch: Pre-Shock Expectation

At the **arrival perch**, the agent has state $(k_t, p_{t-1}, z_{t-1})$ and awaits the realization of the Markov state $z_t$ and income shocks $(\psi_t, \theta_t)$.

The **arrival value function** $V^a(k, p_{-1}, z_{-1})$ represents the expected value before these shocks are realized:
$$V^a(k, p_{-1}, z_{-1}) = \mathbb{E}_{z, \psi, \theta \mid z_{-1}} \left[ V^d(z, m, p) \right],$$
where the expectation is taken over:
- $z \sim \mathbb{P}(\cdot \mid z_{-1})$ (Markov transition),
- $(\psi, \theta) \sim F_z(\psi, \theta)$ (state-dependent income shocks),

and the decision-perch state is constructed via:
$$p = p_{-1} \cdot \Gamma(z) \cdot \psi, \quad b = \frac{R(z) \cdot k}{\Gamma(z) \cdot \psi}, \quad m = b + \theta.$$

**Information set at arrival perch**: $\mathcal{F}^a = \{k, p_{-1}, z_{-1}\}$.

### 3.2 Decision Perch: Post-Shock Optimization

At the **decision perch**, the agent observes the realized state $(z, m, p)$ and chooses consumption $c$ to maximize:
$$V^d(z, m, p) = \max_{c \in [0, m]} \left\{ u(c \cdot p) + \beta V^c(a, p, z) \right\},$$
where $a = m - c$ is normalized end-of-period assets.

For normalized models with CRRA utility, we typically exploit homogeneity. Defining the normalized value function $\tilde{V}^d(z, m) = p^{\rho-1} V^d(z, m, p)$ and normalizing $\tilde{c} = c$, the normalized Bellman equation becomes:
$$\tilde{V}^d(z, m) = \max_{c \in [0, m]} \left\{ u(c) + \beta \tilde{V}^c(a, z) \right\},$$
where
$$\tilde{V}^c(a, z) = \pi(z) \mathbb{E}_{z', \psi', \theta' \mid z} \left[ (\Gamma(z') \psi')^{1-\rho} \tilde{V}^d(z', m') \right],$$
and $m' = \frac{R(z') a}{\Gamma(z') \psi'} + \theta'$.

**Information set at decision perch**: $\mathcal{F}^d = \{z, m, p\}$ (or $\{z, m\}$ in normalized form).

The optimal consumption policy is denoted $c^*(z, m)$ (the function `cFuncX` in HARK).

### 3.3 Continuation Perch: Post-Decision Value

At the **continuation perch**, after choosing $c$ and thereby determining $a = m - c$, the agent faces mortality risk. The **continuation value function** is:
$$V^c(a, p, z) = \pi(z) \mathbb{E}_{z', \psi', \theta' \mid z} \left[ V^d(z', m', p') \right] + (1 - \pi(z)) \cdot 0,$$
where the second term reflects that the agent receives zero continuation value if they die.

Given survival, the next-period decision state evolves as:
$$p' = p \cdot \Gamma(z') \cdot \psi', \quad k' = a, \quad m' = \frac{R(z') k'}{\Gamma(z') \psi'} + \theta'.$$

In normalized form:
$$\tilde{V}^c(a, z) = \pi(z) \mathbb{E}_{z', \psi', \theta' \mid z} \left[ (\Gamma(z') \psi')^{1-\rho} \tilde{V}^d(z', m') \right],$$
where
$$m' = \frac{R(z') a}{\Gamma(z') \psi'} + \theta'.$$

**Information set at continuation perch**: $\mathcal{F}^c = \{a, p, z\}$ (or $\{a, z\}$ in normalized form).

### 3.4 Recursive Structure Summary

The full recursive structure is:
$$\begin{aligned}
V^a(k, p_{-1}, z_{-1}) &= \mathbb{E}_{z \sim \mathbb{P}(\cdot|z_{-1})} \mathbb{E}_{(\psi,\theta) \sim F_z} \left[ V^d(z, m, p) \right], \\
V^d(z, m, p) &= \max_{c \in [0,m]} \left\{ u(c \cdot p) + \beta V^c(m-c, p, z) \right\}, \\
V^c(a, p, z) &= \pi(z) \mathbb{E
