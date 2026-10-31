---
audience: user
type: example
topic: [applications]
---
# ConsKinkedR — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Specification: Kinked Interest Rate Consumption-Saving Model

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation |
|---------------|--------------|----------------------|
| `kNrm` | Prestate (arrival perch) | $k_t \in \mathbb{R}$ |
| `pLvlPrev` | Prestate (arrival perch) | $p_{t-1} \in \mathbb{R}_{++}$ |
| `PermShk` | Shock (decision perch) | $\psi_t \in \mathbb{R}_{++}$ |
| `TranShk` | Shock (decision perch) | $\theta_t \in \mathbb{R}_{++}$ |
| `yNrm` | Decision perch variable | $y_t \coloneqq \theta_t$ |
| `pLvl` | Decision perch variable | $p_t \in \mathbb{R}_{++}$ |
| `bNrm` | Decision perch variable | $b_t \in \mathbb{R}$ |
| `mNrm` | Decision perch variable | $m_t \in \mathbb{R}$ |
| `cNrm` | Control (decision perch) | $c_t \in \mathbb{R}_+$ |
| `aNrm` | Continuation perch variable | $a_t \in \mathbb{R}$ |
| `Rfree` | State-dependent rate | $R_t \in \{R^{\text{save}}, R^{\text{boro}}\}$ |
| `boro` | Borrowing indicator | $\mathbb{1}_{k_t < 0}$ |
| `live` | Survival shock | $\ell_{t+1} \in \{0,1\}$ |

## 2. Model

### 2.1 Overview

The ConsKinkedR model describes an infinitely-lived agent facing idiosyncratic income risk who accumulates a risk-free asset to smooth consumption over time. The key friction is a **kinked interest rate schedule**: the agent faces interest factor $R^{\text{save}}$ when saving ($k_t \geq 0$) but pays a higher interest factor $R^{\text{boro}} > R^{\text{save}}$ when borrowing ($k_t < 0$). This asymmetry captures realistic credit market imperfections such as credit card interest rates exceeding savings account returns.

The agent receives labor income subject to both **permanent shocks** $\psi_t$ (affecting the income level permanently) and **transitory shocks** $\theta_t$ (affecting only current income). Permanent income follows a geometric random walk with trend growth $\Gamma$. The agent optimizes consumption to maximize expected discounted lifetime utility, subject to this kinked budget constraint and the risk of mortality.

### 2.2 State Space

**Arrival (Prestate) Variables:**
- $k_t \in \mathbb{R}$: normalized capital holdings at the beginning of period $t$, measured relative to permanent income $p_{t-1}$ from the previous period
- $p_{t-1} \in \mathbb{R}_{++}$: permanent income level from period $t-1$

The arrival state space is $\mathcal{K} \times \mathcal{P} \coloneqq \mathbb{R} \times \mathbb{R}_{++}$.

**Decision (Post-Shock) Variables:**
After observing shocks $(\psi_t, \theta_t)$, the agent computes:
- $G_t \coloneqq \Gamma \psi_t$: realized permanent income growth factor
- $p_t \coloneqq p_{t-1} G_t$: updated permanent income level
- $R_t \coloneqq R^{\text{save}} + (R^{\text{boro}} - R^{\text{save}}) \mathbb{1}_{k_t < 0}$: realized interest factor
- $b_t \coloneqq \frac{R_t k_t}{G_t}$: normalized bank balances (capital plus interest, re-normalized by new permanent income)
- $y_t \coloneqq \theta_t$: normalized labor income
- $m_t \coloneqq b_t + y_t$: normalized market resources (total resources available for consumption)

**Continuation (Post-Decision) Variables:**
- $a_t \coloneqq m_t - c_t \in \mathbb{R}$: normalized end-of-period assets

### 2.3 Action Space

The agent chooses normalized consumption $c_t \in [0, m_t]$, implicitly determining end-of-period assets $a_t = m_t - c_t$.

### 2.4 Shock Distributions

**Income Shocks:**
Joint distribution of permanent and transitory shocks:
$$(\psi_t, \theta_t) \sim F_{\text{inc}} \quad \text{with support on } \mathbb{R}_{++}^2$$

Typically specified with $\mathbb{E}[\psi_t] = 1$ (so $\Gamma$ captures expected growth) and $\mathbb{E}[\theta_t] = 1$ (so the transitory shock is mean-preserving).

**Survival Shock:**
$$\ell_{t+1} \sim \text{Bernoulli}(\Lambda)$$
where $\Lambda \in [0,1]$ is the survival probability (`LivPrb`).

**Initial Distributions:**
- $p_0 \sim F_{p,0}$: initial permanent income distribution
- $k_0 \sim F_{k,0}$: initial normalized capital distribution

### 2.5 State Transitions

The dynamics unfold in the following sequence:

1. **Arrival:** Agent enters period with $(k_t, p_{t-1})$
2. **Income realization:** Draw $(\psi_t, \theta_t) \sim F_{\text{inc}}$
3. **Income update:** Compute $G_t = \Gamma \psi_t$ and $p_t = p_{t-1} G_t$
4. **Interest rate determination:** Set $R_t = R^{\text{save}}$ if $k_t \geq 0$, else $R_t = R^{\text{boro}}$
5. **Resource calculation:**
   $$b_t = \frac{R_t k_t}{G_t}, \quad y_t = \theta_t, \quad m_t = b_t + y_t$$
6. **Consumption choice:** Agent chooses $c_t \in [0, m_t]$ optimally
7. **Asset accumulation:** $a_t = m_t - c_t$
8. **Survival:** Draw $\ell_{t+1} \sim \text{Bernoulli}(\Lambda)$
9. **Twist (if alive):** Set $k_{t+1} = a_t$ and $p_t$ carries forward as $p_t$

The state transition for survivors is:
$$k_{t+1} = a_t = m_t - c_t = \frac{R_t k_t}{G_t} + \theta_t - c_t$$

## 3. Bellman Equation

The agent's optimization problem decomposes into three value functions corresponding to the ADC (Arrival-Decision-Continuation) framework.

### 3.1 Arrival Value Function

At the **arrival perch**, before observing current income shocks, the agent's expected value is:
$$V^{\text{arr}}(k_t, p_{t-1}) = \mathbb{E}_{\psi_t, \theta_t}\left[V^{\text{dec}}(k_t, p_{t-1}; \psi_t, \theta_t)\right]$$

**Information set:** $\mathcal{F}_t^{\text{arr}} = \{k_t, p_{t-1}\}$

### 3.2 Decision Value Function

At the **decision perch**, after observing shocks $(\psi_t, \theta_t)$, the agent solves:
$$V^{\text{dec}}(k_t, p_{t-1}; \psi_t, \theta_t) = \max_{c_t \in [0, m_t]} \left\{u(c_t p_t) + \beta \Lambda V^{\text{cont}}(a_t, p_t)\right\}$$

where:
- $G_t = \Gamma \psi_t$
- $p_t = p_{t-1} G_t$
- $R_t = R^{\text{save}} + (R^{\text{boro}} - R^{\text{save}}) \mathbb{1}_{k_t < 0}$
- $b_t = R_t k_t / G_t$
- $m_t = b_t + \theta_t$
- $a_t = m_t - c_t$
- $u(\cdot)$ is the period utility function (typically CRRA: $u(C) = \frac{C^{1-\rho}}{1-\rho}$)
- $\beta$ is the time discount factor
- $\Lambda$ is the survival probability

**Information set:** $\mathcal{F}_t^{\text{dec}} = \{k_t, p_{t-1}, \psi_t, \theta_t\} = \{m_t, p_t, R_t\}$

Equivalently, working with normalized consumption $c_t$ (consumption divided by $p_t$):
$$V^{\text{dec}}(m_t, p_t) = \max_{c_t \in [0, m_t]} \left\{p_t^{1-\rho} u(c_t) + \beta \Lambda V^{\text{cont}}(m_t - c_t, p_t)\right\}$$

### 3.3 Continuation Value Function

At the **continuation perch**, after the consumption decision but before next period's arrival:
$$V^{\text{cont}}(a_t, p_t) = V^{\text{arr}}(k_{t+1}, p_t)$$

where the twist mapping gives $k_{t+1} = a_t$ and $p_t$ becomes next period's $p_{t-1}$.

**Information set:** $\mathcal{F}_t^{\text{cont}} = \{a_t, p_t\}$

### 3.4 Recursive Formulation

Combining the perches, the full Bellman equation is:
$$V^{\text{arr}}(k_t, p_{t-1}) = \mathbb{E}_{\psi_t, \theta_t}\left[\max_{c_t \in [0, m_t]} \left\{p_t^{1-\rho} u(c_t) + \beta \Lambda V^{\text{arr}}(m_t - c_t, p_t)\right\}\right]$$

subject to the state evolution equations specified above.

The **kinked interest rate** creates a non-convexity in the budget constraint: the effective return on savings differs depending on whether $k_t \gtrless 0$. This kink propagates through the policy function, potentially creating a region of rapid adjustment near $k_t = 0$.

## 4. First-Order Conditions

### 4.1 Euler Equation

The first-order condition for consumption at the decision perch yields:
$$u'(c_t p_t) p_t = \beta \Lambda \frac{\partial V^{\text{cont}}(a_t, p_t)}{\partial a_t}$$

By the envelope theorem at the continuation perch:
$$\frac{\partial V^{\text{cont}}(a_t, p_t)}{\partial a_t} = \frac{\partial V^{\text{arr}}(k_{t+1}, p_t)}{\partial k_{t+1}} = \mathbb{E}_{\psi_{t+1}, \theta_{t+1}}\left[\frac{\partial V^{\text{dec}}}{\partial m_{t+1}} \cdot \frac{\partial m_{t+1}}{\partial k_{t+1}}\right]$$

Since $m_{t+1} = \frac{R_{t+1} k_{t+1}}{G_{t+1}} + \theta_{t+1}$ where $G_{t+1} = \Gamma \psi_{t+1}$ and $R_{t+1}$ depends on the sign of $k_{t+1} = a_t$:
$$\frac{\partial m_{t+1}}{\partial k_{t+1}} = \frac{R_{t+1}}{G_{t+1}} \quad \text{for } k_{t+1} \neq 0$$

At $k_{t+1} = 0$, there is a **kink** in the marginal return:
- Right derivative: $\frac{R^{\text{save}}}{\Gamma \psi_{t+1}}$
- Left derivative: $\frac{R^{\text{boro}}}{\Gamma \psi_{t+1}}$

The Euler equation becomes:
$$u'(c_t p_t) = \beta \Lambda \mathbb{E}_{\psi_{t+1}, \theta_{t+1}}\left[u'(c_{t+1} p_{t+1}) \cdot \frac{R_{t+1}}{\Gamma \psi_{t+1}}\right]$$

where $R_{t+1} = R^{\text{save}} \mathbb{1}_{a_t \geq 0} + R^{\text{boro}} \mathbb{1}_{a_t < 0}$.

### 4.2 Normalized Euler Equation

Working with normalized consumption $c_t \coloneqq C_t / p_t$ and assuming CRRA utility $u(C) = \frac{C^{1-\rho}}{1-\rho}$:
$$c_t^{-\rho} = \beta \Lambda \mathbb{E}_{\psi_{t+1}, \theta_{t+1}}\left[\left(\frac{R_{t+1}}{\Gamma \psi_{t+1}}\right) \psi_{t+1}^{-\rho} c_{t+1}^{-\rho}\right]$$

Simplifying:
$$c_t^{-\rho} = \beta \Lambda R_{t+1} \Gamma^{-1} \mathbb{E}_{\psi_{t+1}, \theta_{t+1}}\left[\psi_{t+1}^{-\rho} c_{t+1}^{-\rho}\right]$$

### 4.3 Envelope Condition

The envelope theorem at the decision perch gives:
$$\frac{\partial V^{\text{dec}}}{\partial m_t} = u'(c_t p_t) p_t = p_t^{1-\rho} c_t^{-\rho}$$

This marginal value of resources is used in the backward iteration of the solution algorithm.

### 4.4 Endogenous Gridpoint Method (EGM) Representation

The model is well-suited for the **Endogenous Gridpoint Method** (Carroll, 2006), which inverts the Euler equation:

1. Construct a grid over end-of-period assets: $\{a^{(j)}\}_{j=1}^{N_a}$
2. For each $a^{(j)}$, compute expected marginal value:
   $$\mathcal{E}_t^{(j)} = \mathbb{E}_{\psi_{t+1}, \theta_{t+1}}\left[\psi_{t+1}^{-\rho} u'(c_{t+1}(m_{t+1}))\right]$$
   where $m_{t+1} = \frac{R_{t+1} a^{(j)}}{\Gamma \psi_{t+1}} + \theta_{t+1}$ and $R_{t+1}$ depends on $\text{sgn}(a^{(j)})$
3. Invert the Euler equation to find implied consumption:
   $$c_t^
