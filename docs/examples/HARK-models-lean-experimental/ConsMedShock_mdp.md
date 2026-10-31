---
audience: user
type: example
topic: [applications]
---
# ConsMedShock — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Medical Shock Model

## 1. Rosetta Stone

| HARK Variable | DDSL Concept | Mathematical Notation | Perch |
|--------------|--------------|----------------------|-------|
| `kLvl` | Capital at arrival (pre-shock) | $k_t$ | Arrival |
| `pLvlPrev` | Permanent income at arrival | $p_{t-1}$ | Arrival |
| `PermShk` | Permanent income shock | $\Psi_t$ | Decision |
| `TranShk` | Transitory income shock | $\theta_t$ | Decision |
| `pLvl` | Permanent income post-shock | $p_t$ | Decision |
| `yLvl` | Labor income | $y_t$ | Decision |
| `bLvl` | Bank balances | $b_t$ | Decision |
| `mLvl` | Market resources | $m_t$ | Decision |
| `MedShk` | Medical need shock | $\xi_t$ | Decision |
| `cLvl` | Consumption (control) | $c_t$ | Decision |
| `MedLvl` | Medical expenditure (control) | $\mu_t$ | Decision |
| `xLvl` | Total expenditure | $x_t$ | Decision |
| `aLvl` | End-of-period assets | $a_t$ | Continuation |
| `live` | Survival indicator | $\mathbb{1}_{\text{live}}$ | Continuation |
| `Rfree` | Gross interest rate | $R$ | Parameter |
| `LivPrb` | Survival probability | $\pi$ | Parameter |
| `MedPrice` | Relative price of medical care | $p_M$ | Parameter |

## 2. Model

### 2.1 Overview

The consumption-medical shock model extends the standard incomplete-markets consumption-saving problem by introducing a second consumption good—medical care—with stochastic marginal utility. The agent faces three sources of uncertainty: permanent income shocks $\Psi_t$, transitory income shocks $\theta_t$, and medical need shocks $\xi_t$ that modulate the marginal utility derived from medical expenditure.

### 2.2 State Space

The **arrival state** (beginning-of-period, pre-shock) consists of:
- Capital holdings: $k_t \in \mathbb{R}_+$
- Previous period's permanent income: $p_{t-1} \in \mathbb{R}_{++}$

The **decision state** (post-shock, pre-decision) augments the arrival state with realized shocks:
- Market resources: $m_t = R k_t + y_t \in \mathbb{R}_+$
- Current permanent income: $p_t = \mathbb{E}[p_t | p_{t-1}] \cdot \Psi_t$
- Medical need shock: $\xi_t \in \mathbb{R}_{++}$

### 2.3 Action Space

The agent chooses two control variables:
- Consumption expenditure: $c_t \in [0, m_t + p_M \mu_t]$
- Medical care: $\mu_t \in \mathbb{R}_+$

These must satisfy the budget constraint:
$$x_t \coloneqq c_t + p_M \mu_t \leq m_t$$

Equivalently, end-of-period assets must be non-negative:
$$a_t \coloneqq m_t - x_t \geq 0$$

### 2.4 Shock Distributions

**Income shocks** $(\Psi_t, \theta_t)$ follow a joint distribution:
$$(\Psi_t, \theta_t) \sim F_{\text{Inc}}$$

with properties:
- $\mathbb{E}[\Psi_t] = 1$ (permanent shocks are mean-preserving)
- $\mathbb{E}[\theta_t] = 1$ (transitory shocks are mean-preserving)
- $\Psi_t, \theta_t \in \mathbb{R}_{++}$

**Medical need shocks** $\xi_t$ follow an independent distribution:
$$\xi_t \sim F_{\text{Med}}$$

with $\xi_t \in \mathbb{R}_{++}$ representing the multiplicative factor on marginal utility from medical care.

**Survival shocks** are Bernoulli:
$$\mathbb{1}_{\text{live}} \sim \text{Bernoulli}(\pi)$$

where $\pi \in (0,1]$ is the survival probability.

### 2.5 Permanent Income Dynamics

Permanent income follows a deterministic growth path with stochastic innovations:
$$\mathbb{E}[p_t | p_{t-1}] = G(p_{t-1})$$

where $G: \mathbb{R}_{++} \to \mathbb{R}_{++}$ is the expected permanent income function. The realized permanent income incorporates the multiplicative shock:
$$p_t = G(p_{t-1}) \cdot \Psi_t$$

### 2.6 Labor Income

Labor income is the product of permanent income and the transitory shock:
$$y_t = \theta_t \cdot p_t = \theta_t \cdot G(p_{t-1}) \cdot \Psi_t$$

### 2.7 Capital Accumulation

Bank balances at the decision node equal the risk-free return on capital:
$$b_t = R \cdot k_t$$

Market resources are bank balances plus labor income:
$$m_t = b_t + y_t = R k_t + \theta_t p_t$$

End-of-period assets are market resources minus total expenditure:
$$a_t = m_t - c_t - p_M \mu_t$$

### 2.8 State Transition

The continuation state $(a_t, p_t)$ maps to the next period's arrival state conditional on survival:
$$k_{t+1} = \begin{cases}
a_t & \text{with probability } \pi \\
\text{terminal} & \text{with probability } 1-\pi
\end{cases}$$

$$p_t \to p_{t+1}^{\text{prev}} = p_t$$

The twist operator connects end-of-period to beginning-of-period variables: $(a_t, p_t) \mapsto (k_{t+1}, p_t)$.

### 2.9 Initial Distribution

At birth, the agent draws:
- Normalized capital: $k_0/p_{-1} \sim F_{k,\text{init}}$
- Initial permanent income: $p_{-1} \sim F_{p,\text{init}}$

with capital level $k_0 = p_{-1} \cdot (k_0/p_{-1})$.

## 3. Bellman Equation

The value function is decomposed across three perches following the Abel-Eberly-Panageas timing structure.

### 3.1 Arrival Value (Pre-Shock)

At the arrival perch, the agent holds capital $k_t$ and permanent income level $p_{t-1}$ from the previous period. The arrival value is the expectation over all shocks before observing their realizations:

$$V^A(k_t, p_{t-1}) = \mathbb{E}_{(\Psi_t, \theta_t, \xi_t)} \left[ V^D(m_t, p_t, \xi_t) \mid k_t, p_{t-1} \right]$$

where the decision state variables are:
\begin{align}
p_t &= G(p_{t-1}) \cdot \Psi_t \\
y_t &= \theta_t \cdot p_t \\
m_t &= R k_t + y_t
\end{align}

**Information set:** $\mathcal{I}_t^A = \{k_t, p_{t-1}\}$

### 3.2 Decision Value (Post-Shock, Pre-Decision)

At the decision perch, all shocks have been realized. The agent observes $(m_t, p_t, \xi_t)$ and chooses consumption $c_t$ and medical expenditure $\mu_t$ to maximize:

$$V^D(m_t, p_t, \xi_t) = \max_{c_t, \mu_t} \left\{ u(c_t, \mu_t; \xi_t) + \beta \pi V^C(a_t, p_t) \right\}$$

subject to:
\begin{align}
a_t &= m_t - c_t - p_M \mu_t \\
a_t &\geq 0 \\
c_t &\geq 0, \quad \mu_t \geq 0
\end{align}

The utility function $u(c_t, \mu_t; \xi_t)$ depends on the medical need shock $\xi_t$, which modulates the marginal utility of medical care. A natural specification would be:
$$u(c_t, \mu_t; \xi_t) = \frac{c_t^{1-\rho}}{1-\rho} + \xi_t \cdot \frac{\mu_t^{1-\rho_M}}{1-\rho_M}$$

where $\rho$ is the coefficient of relative risk aversion for consumption and $\rho_M$ is the curvature parameter for medical care utility.

**Information set:** $\mathcal{I}_t^D = \{m_t, p_t, \xi_t\}$

### 3.3 Continuation Value (Post-Decision)

At the continuation perch, the agent has chosen $(c_t, \mu_t)$, determined end-of-period assets $a_t$, and survival uncertainty remains. The continuation value is:

$$V^C(a_t, p_t) = V^A(a_t, p_t)$$

This reflects the twist: end-of-period assets $a_t$ become next period's capital $k_{t+1} = a_t$, and current permanent income $p_t$ becomes next period's lagged permanent income $p_{t+1}^{\text{prev}} = p_t$.

**Information set:** $\mathcal{I}_t^C = \{a_t, p_t\}$

### 3.4 Complete Recursion

Combining the three perches, the full Bellman equation is:

\begin{align}
V^A(k_t, p_{t-1}) &= \mathbb{E}_{\Psi_t, \theta_t, \xi_t} \left[ V^D(R k_t + \theta_t G(p_{t-1}) \Psi_t, G(p_{t-1}) \Psi_t, \xi_t) \right] \\[0.5em]
V^D(m_t, p_t, \xi_t) &= \max_{c_t, \mu_t \geq 0} \left\{ u(c_t, \mu_t; \xi_t) + \beta \pi V^A(m_t - c_t - p_M \mu_t, p_t) \right\} \\[0.5em]
&\quad \text{s.t. } c_t + p_M \mu_t \leq m_t
\end{align}

## 4. First-Order Conditions

### 4.1 Euler Equations

The first-order conditions for interior solutions with respect to consumption and medical expenditure are:

**Consumption:**
$$u_c(c_t, \mu_t; \xi_t) = \beta \pi \mathbb{E}_{t+1} \left[ R \cdot u_c(c_{t+1}, \mu_{t+1}; \xi_{t+1}) \right]$$

**Medical expenditure:**
$$\xi_t \cdot u_{\mu}(c_t, \mu_t; \xi_t) = p_M \cdot u_c(c_t, \mu_t; \xi_t)$$

This second condition states that the marginal rate of substitution between medical care and consumption equals the relative price:
$$\frac{\xi_t \cdot u_{\mu}(c_t, \mu_t; \xi_t)}{u_c(c_t, \mu_t; \xi_t)} = p_M$$

### 4.2 Envelope Conditions

The envelope theorem applied to the decision problem yields:

**With respect to market resources:**
$$V^D_m(m_t, p_t, \xi_t) = u_c(c_t, \mu_t; \xi_t)$$

**With respect to permanent income:**
$$V^D_p(m_t, p_t, \xi_t) = \beta \pi V^A_p(a_t, p_t)$$

### 4.3 Combined Euler Equation

Substituting the envelope condition into the consumption Euler equation:
$$V^D_m(m_t, p_t, \xi_t) = \beta \pi R \mathbb{E}_{t+1} \left[ V^D_m(m_{t+1}, p_{t+1}, \xi_{t+1}) \right]$$

This is the fundamental intertemporal optimality condition.

### 4.4 Endogenous Grid Method (EGM) Representation

The EGM algorithm exploits the Euler equation structure. For a given end-of-period assets $a_t$, the right-hand side of the Euler equation can be computed:
$$u_c(c_t, \mu_t; \xi_t) = \beta \pi R \mathbb{E}_{\Psi_{t+1}, \theta_{t+1}, \xi_{t+1}} \left[ u_c(c_{t+1}, \mu_{t+1}; \xi_{t+1}) \right]$$

Given the medical expenditure first-order condition:
$$\mu_t = \left( \frac{\xi_t}{p_M} \right)^{1/\rho_M} c_t^{\rho/\rho_M}$$

(assuming power utility), we can invert to find $c_t$ as a function of $a_t$, then compute:
$$m_t = c_t + p_M \mu_t + a_t$$

This generates the policy function on an endogenous grid of $m_t$ values.

### 4.5 Corner Solutions

If the borrowing constraint binds ($a_t = 0$), then:
$$m_t = c_t + p_M \mu_t$$

The consumption Euler equation becomes an inequality:
$$u_c(c_t, \mu_t; \xi_t) \geq \beta \pi R \mathbb{E}_{t+1} \left[ u_c(c_{t+1}, \mu_{t+1}; \xi_{t+1}) \right]$$

## 5. Forward Operator

### 5.1 Individual State Transition

Given the policy functions $c^*(m, p, \xi)$ and $\mu^*(m, p, \xi)$, an individual agent with state $(k_t, p_{t-1})$ transitions to next period's state $(k_{t+1}, p_t)$ according to:

\begin{align}
p_t &= G(p_{t-1}) \cdot \Psi_t, \quad \Psi_t \sim F_{\text{Inc}}^{\Psi} \\
y_t &= \theta_t \cdot p_t, \quad \theta_t \sim F_{\text{Inc}}^{\theta} \\
m_t &= R k_t + y_t \\
\xi_t &\sim F_{\text{Med}} \\
c_t &= c^*(m_t, p_t, \xi_t) \\
\mu_t &= \mu^*(m_t, p_t, \xi_t) \\
a_t &= m_t - c_t - p_M \mu_t \\
k_{t+1} &= a_t \cdot \mathbb{1}_{\
