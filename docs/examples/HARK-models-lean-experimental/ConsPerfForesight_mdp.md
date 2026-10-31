---
audience: user
type: example
topic: [applications]
---
# ConsPerfForesight — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Perfect Foresight Consumption-Saving Model with Mortality Risk

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation |
|--------------|--------------|----------------------|
| `kNrm` | Prestate / Arrival perch | $k_t$ (normalized capital) |
| `pLvlPrev` | Prestate / Arrival perch | $P_{t-1}$ (permanent income) |
| `yNrm` | Computed constant | $y = 1$ (normalized income) |
| `pLvl` | Decision perch state | $P_t = P_{t-1} \cdot \Gamma$ |
| `bNrm` | Decision perch state | $b_t = R k_t / \Gamma$ |
| `mNrm` | Decision perch state | $m_t = b_t + y$ |
| `cNrm` | Control / Decision perch | $c_t$ (normalized consumption) |
| `aNrm` | Continuation perch | $a_t = m_t - c_t$ |
| `live` | Mortality shock | $\xi_t \in \{0,1\}$ with $\mathbb{P}(\xi_t=1) = \pi$ |
| `Rfree` | Parameter | $R$ (gross interest rate) |
| `PermGroFac` | Parameter | $\Gamma$ (permanent income growth) |
| `LivPrb` | Parameter | $\pi$ (survival probability) |

**Perch Structure:**
- **Arrival perch**: Agent begins period with $(k_t, P_{t-1})$
- **Decision perch**: After income realization, state is $(m_t, P_t)$
- **Continuation perch**: After consumption choice, state is $(a_t, P_t)$, then mortality shock realizes

## 2. Model

### 2.1 Primitives

The agent lives in discrete time $t = 0, 1, 2, \ldots$ and faces mortality risk each period. The agent has CRRA preferences over consumption sequences with discount factor $\beta$ and relative risk aversion $\rho$.

### 2.2 State Variables

At the **arrival perch** (beginning of period $t$), the state is $(k_t, P_{t-1})$ where:
- $k_t \in \mathbb{R}_+$ denotes normalized capital holdings (assets carried forward from period $t-1$, normalized by permanent income $P_{t-1}$)
- $P_{t-1} \in \mathbb{R}_{++}$ denotes the permanent income level from the previous period

### 2.3 Within-Period Dynamics

The within-period state evolution follows this sequence:

**Step 1: Permanent income growth.** At the start of period $t$, permanent income grows deterministically:
$$P_t \coloneqq P_{t-1} \cdot \Gamma$$
where $\Gamma > 0$ is the permanent income growth factor.

**Step 2: Bank balances.** The agent receives the return on capital, normalized by the new permanent income level:
$$b_t \coloneqq \frac{R \cdot k_t}{\Gamma}$$
where $R > 0$ is the gross risk-free interest rate.

**Step 3: Labor income.** The agent receives normalized labor income:
$$y_t \coloneqq 1$$
This normalization implies that labor income grows at rate $\Gamma$ in levels (i.e., level labor income is $P_{t-1}$, which after growth becomes $P_t$, and $P_t / P_t = 1$).

**Step 4: Market resources.** Total normalized resources available for consumption are:
$$m_t \coloneqq b_t + y_t = \frac{R \cdot k_t}{\Gamma} + 1$$

### 2.4 Action Space

At the **decision perch**, given market resources $m_t$ and permanent income $P_t$, the agent chooses normalized consumption:
$$c_t \in [0, m_t]$$

### 2.5 End-of-Period Assets

After the consumption decision, normalized end-of-period assets are:
$$a_t \coloneqq m_t - c_t$$

### 2.6 Mortality Shock

At the **continuation perch**, the agent faces a mortality shock $\xi_t \in \{0, 1\}$ where:
$$\xi_t \sim \text{Bernoulli}(\pi)$$
with $\pi \in (0,1]$ denoting the survival probability. If $\xi_t = 1$, the agent survives to period $t+1$; if $\xi_t = 0$, the agent dies and receives continuation value zero.

### 2.7 State Transition

For surviving agents ($\xi_t = 1$), the state at the arrival perch of period $t+1$ is:
$$k_{t+1} \coloneqq a_t, \quad P_t \mapsto P_t$$
where the twist mapping sends continuation perch state $(a_t, P_t)$ to arrival perch state $(k_{t+1}, P_{t+1}^{\text{prev}}) = (a_t, P_t)$.

### 2.8 Initial Distribution

At model initialization ($t=0$), the agent's state is drawn from:
$$(k_0, P_{-1}) \sim \mu_0$$
where $\mu_0 = \text{pLvlInitDstn} \times \text{kNrmInitDstn}$ is the product of independent marginal distributions over initial permanent income and normalized capital.

## 3. Bellman Equation

### 3.1 Utility Function

Let $u(c) = \frac{c^{1-\rho}}{1-\rho}$ denote the period utility function with relative risk aversion $\rho > 0$ (for $\rho = 1$, $u(c) = \log c$).

### 3.2 Three-Perch Decomposition

#### Arrival Value Function

At the **arrival perch**, the agent has state $(k_t, P_{t-1})$ and has not yet observed the deterministic income growth. The arrival value is:
$$V^{\text{arr}}_t(k_t, P_{t-1}) = V^{\text{dec}}_t(m_t, P_t)$$
where the transition to the decision perch is deterministic:
$$P_t = P_{t-1} \cdot \Gamma, \quad m_t = \frac{R \cdot k_t}{\Gamma} + 1$$

Since there are no shocks between arrival and decision perches in this perfect foresight model, the arrival value equals the decision value.

#### Decision Value Function

At the **decision perch**, the agent observes $(m_t, P_t)$ and chooses consumption $c_t$:
$$V^{\text{dec}}_t(m_t, P_t) = \max_{c_t \in [0, m_t]} \left\{ u(c_t \cdot P_t) + \beta \cdot V^{\text{cont}}_t(a_t, P_t) \right\}$$
where $a_t = m_t - c_t$. Note that utility is defined over consumption in levels, $C_t = c_t \cdot P_t$, but the value function is expressed in normalized terms.

#### Continuation Value Function

At the **continuation perch**, the agent has state $(a_t, P_t)$ and faces the mortality shock:
$$V^{\text{cont}}_t(a_t, P_t) = \pi \cdot V^{\text{arr}}_{t+1}(a_t, P_t) + (1-\pi) \cdot 0$$
where the agent survives with probability $\pi$ and transitions to the next period's arrival perch with $k_{t+1} = a_t$ and $P_t$ serving as $P_{t}^{\text{prev}}$ for the next period.

### 3.3 Normalized Bellman Equation

Define the normalized value function $v_t(m_t) \coloneqq V^{\text{dec}}_t(m_t, P_t) / P_t^{1-\rho}$. Then the Bellman equation in normalized form is:
$$v_t(m_t) = \max_{c_t \in [0, m_t]} \left\{ u(c_t) + \beta \pi \left(\frac{P_{t+1}}{P_t}\right)^{1-\rho} v_{t+1}(m_{t+1}) \right\}$$

Since $P_{t+1} = P_t \cdot \Gamma$, this simplifies to:
$$v_t(m_t) = \max_{c_t \in [0, m_t]} \left\{ \frac{c_t^{1-\rho}}{1-\rho} + \beta \pi \Gamma^{1-\rho} v_{t+1}\left(\frac{R(m_t - c_t)}{\Gamma} + 1\right) \right\}$$

### 3.4 Infinite Horizon Problem

In the infinite horizon stationary setting, the value function satisfies:
$$v(m) = \max_{c \in [0, m]} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta \pi \Gamma^{1-\rho} v\left(\frac{R(m - c)}{\Gamma} + 1\right) \right\}$$

The effective discount factor is $\tilde{\beta} \coloneqq \beta \pi \Gamma^{1-\rho}$, which incorporates both time preference, mortality risk, and the growth rate of permanent income.

## 4. First-Order Conditions

### 4.1 Euler Equation

The first-order condition for optimal consumption at interior solutions is:
$$u'(c_t) = \beta \pi \left(\frac{P_{t+1}}{P_t}\right)^{-\rho} \frac{R}{\Gamma} u'(c_{t+1})$$

With CRRA utility $u'(c) = c^{-\rho}$, this becomes:
$$c_t^{-\rho} = \beta \pi \Gamma^{-\rho} R c_{t+1}^{-\rho}$$

Rearranging:
$$\frac{c_{t+1}}{c_t} = \left(\beta \pi R \Gamma^{-\rho}\right)^{1/\rho} = (\beta \pi)^{1/\rho} \left(\frac{R}{\Gamma}\right)^{1/\rho}$$

### 4.2 Perfect Foresight Solution

In the perfect foresight case, the consumption function is linear in market resources:
$$c_t = \kappa \cdot m_t$$
where the marginal propensity to consume $\kappa$ satisfies:
$$\kappa = \left(1 + \left(\frac{R}{\Gamma}\right)^{1/\rho} (\beta \pi)^{1/\rho - 1} \right)^{-1}$$

This can be derived by imposing the no-Ponzi condition and the transversality condition, along with the Euler equation.

### 4.3 Envelope Condition

The envelope theorem gives:
$$\frac{\partial v_t(m_t)}{\partial m_t} = u'(c_t(m_t))$$

This states that the marginal value of wealth equals the marginal utility of consumption at the optimal policy.

### 4.4 Return-Impatience Condition

For a well-defined solution, we require:
$$\tilde{\beta} R < \Gamma$$
or equivalently:
$$\beta \pi R \Gamma^{-\rho} < 1$$

This **return-impatience condition** ensures that the agent does not want to accumulate assets indefinitely. When $\tilde{\beta} R = \Gamma$, the consumption function has a non-zero lower bound (the agent never runs out of resources).

### 4.5 Analytical Solution

When $\tilde{\beta} R < \Gamma$, the consumption function takes the form:
$$c(m) = \kappa m$$
where:
$$\kappa = 1 - \left(\frac{\tilde{\beta} R}{\Gamma}\right)^{1/\rho} = 1 - (\beta \pi R \Gamma^{-\rho})^{1/\rho}$$

The value function is:
$$v(m) = \frac{(\kappa m)^{1-\rho}}{1-\rho} \cdot \left(1 - \tilde{\beta} \left(\frac{R}{\Gamma}(1-\kappa)\right)^{1-\rho}\right)^{-1}$$

## 5. Forward Operator

### 5.1 Distribution Dynamics

Let $\Phi_t(k, P)$ denote the joint distribution of agents over normalized capital $k$ and permanent income level $P$ at the arrival perch of period $t$.

The forward operator $\mathcal{T}$ maps $\Phi_t$ to $\Phi_{t+1}$ according to:

**Step 1: Deterministic transformation.** Given $(k_t, P_{t-1}) \sim \Phi_t$, compute:
- $P_t = P_{t-1} \cdot \Gamma$
- $m_t = \frac{R k_t}{\Gamma} + 1$
- $c_t = c(m_t)$ (apply optimal policy)
- $a_t = m_t - c_t$

**Step 2: Mortality selection.** The agent survives with probability $\pi$. For surviving agents:
$$k_{t+1} = a_t, \quad P_t^{\text{prev}} = P_t$$

**Step 3: Distribution update.** The distribution at $t+1$ is:
$$\Phi_{t+1}(dk', dP') = \pi \int \mathbb{1}\{a_t(k,P) \in dk', P\Gamma \in dP'\} \, \Phi_t(dk, dP)$$

where $a_t(k,P) = m_t(k,P) - c(m_t(k,P))$ with $m_t(k,P) = \frac{Rk}{\Gamma} + 1$ and $P' = P \cdot \Gamma$.

### 5.2 Ergodic Distribution

In the infinite horizon setting with constant parameters, if the system has a stationary distribution $\Phi^*$, it satisfies:
$$\Phi^* = \mathcal{T}(\Phi^*)$$

However, because permanent income grows deterministically at rate $\Gamma$, the level distribution of $P$ does not have a stationary distribution—it shifts rightward each period. The **normalized** distribution over $(k, P/\bar{P}_t)$ where $\bar{P}_t$ is the mean permanent income may converge to a stationary distribution under appropriate conditions.

### 5.3 Cohort Interpretation

Alternatively, we can interpret $\Phi_t$ as the distribution of a single cohort over time. With mortality rate $1-\pi$, the cohort size shrinks by factor $\pi$ each period. The distribution of survivors evolves according to the forward operator above.

### 5.4 Cross-Sectional Distribution

If we consider a steady-state economy with overlapping generations where new agents are born each period with distribution $\mu_0$, the cross-sectional distribution is:
$$\Phi^{\text{cross}}(dk, dP) = \sum_{s=0}^{\infty} \pi^s \mu_0^{(s)}(dk, dP)$$
where $\mu_0^{(s)}$ denotes the distribution of the cohort born $s$ periods ago, evolved forward $s$ periods under the policy function.

## 6. Calibration

| Symbol | Default | Description |
|--------|---------|-------------|
| $R$
