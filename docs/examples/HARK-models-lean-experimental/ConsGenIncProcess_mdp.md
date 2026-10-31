---
audience: user
type: example
topic: [applications]
---
# ConsGenIncProcess — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Specification: Consumption-Saving with General Income Process

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation |
|--------------|--------------|----------------------|
| `kLvl` | Arrival state (capital) | $k_t$ |
| `pLvlPrev` | Arrival state (permanent income) | $p_{t-1}$ |
| `PermShk` | Permanent income shock | $\psi_t$ |
| `TranShk` | Transitory income shock | $\xi_t$ |
| `pLvl` | Decision state (current permanent income) | $p_t$ |
| `yLvl` | Labor income realization | $y_t$ |
| `bLvl` | Bank balances (capital income) | $b_t$ |
| `mLvl` | Market resources (decision state) | $m_t$ |
| `cLvl` | Control variable (consumption) | $c_t$ |
| `aLvl` | Continuation state (assets) | $a_t$ |
| `live` | Survival indicator | $\mathbb{1}_{\text{survive}}$ |
| `Rfree` | Risk-free return factor | $R$ |
| `LivPrb` | Survival probability | $\pi$ |
| `pLvlNextFunc` | Permanent income growth function | $\mathbb{G}(\cdot)$ |
| `IncShkDstn` | Joint shock distribution | $F_{\psi,\xi}$ |

**Timing convention**: The subscript $t$ denotes the period. Variables with "Prev" suffix or subscript $t-1$ represent the value from the previous period that arrives at the beginning of period $t$.

## 2. Model

### 2.1 State Spaces

The model features a consumption-saving problem with income uncertainty. The state space evolves through three perches within each period:

**Arrival Perch** (pre-shock): At the beginning of period $t$, the agent arrives with:
- Capital holdings $k_t \in \mathbb{R}_+$, which are the assets carried forward from period $t-1$
- Permanent income level from the previous period $p_{t-1} \in \mathbb{R}_{++}$

**Decision Perch** (post-shock, pre-decision): After observing income shocks $(\psi_t, \xi_t)$, the agent observes:
- Updated permanent income level $p_t = \mathbb{G}(p_{t-1}) \cdot \psi_t \in \mathbb{R}_{++}$
- Market resources $m_t = R k_t + \xi_t p_t \in \mathbb{R}_+$

**Continuation Perch** (post-decision): After choosing consumption $c_t$, the agent reaches:
- End-of-period assets $a_t = m_t - c_t \in \mathbb{R}_+$
- Current permanent income level $p_t$ (carried forward)
- Survival status determined by mortality shock

### 2.2 Action Space

At the decision perch, the agent chooses consumption $c_t \in [0, m_t]$, subject to the liquidity constraint that consumption cannot exceed available market resources.

### 2.3 Shock Distributions

**Income shocks**: The pair $(\psi_t, \xi_t)$ is drawn from a joint distribution $F_{\psi,\xi}$ at the beginning of each period, where:
- $\psi_t \in \mathbb{R}_{++}$ is the permanent income shock
- $\xi_t \in \mathbb{R}_{++}$ is the transitory income shock

**Mortality shock**: At the end of each period, the agent survives with probability $\pi \in [0,1]$. If the agent dies, they are replaced by a newborn with initial state drawn from the initialization distribution.

**Initial distribution**: Newborn agents draw:
- Initial permanent income $p_0 \sim F_{p,\text{init}}$
- Initial normalized capital holdings $\kappa_0 \sim F_{\kappa,\text{init}}$, with $k_0 = p_0 \kappa_0$

### 2.4 Permanent Income Process

The permanent income component evolves according to a general function $\mathbb{G}: \mathbb{R}_{++} \to \mathbb{R}_{++}$ that captures deterministic growth, mean reversion, or other dynamics:

$$p_t = \mathbb{G}(p_{t-1}) \cdot \psi_t$$

This specification nests several common processes:
- **Constant growth**: $\mathbb{G}(p) = \Gamma \cdot p$ yields $p_t = \Gamma \psi_t p_{t-1}$
- **Mean reversion**: $\mathbb{G}(p) = \bar{p}^\alpha p^{1-\alpha}$ yields partial adjustment toward $\bar{p}$
- **General nonlinear dynamics**: Any smooth function of past permanent income

### 2.5 Transition Equations

The within-period dynamics proceed sequentially:

1. **Income realization**: Draw shocks $(\psi_t, \xi_t) \sim F_{\psi,\xi}$

2. **Permanent income update**: 
   $$p_t = \mathbb{G}(p_{t-1}) \cdot \psi_t$$

3. **Labor income**: 
   $$y_t = \xi_t p_t$$

4. **Bank balances**: 
   $$b_t = R k_t$$

5. **Market resources**: 
   $$m_t = b_t + y_t = R k_t + \xi_t p_t$$

6. **Consumption decision**: 
   $$c_t = \mathfrak{c}(m_t, p_t)$$
   where $\mathfrak{c}$ is the policy function to be solved for.

7. **Asset accumulation**: 
   $$a_t = m_t - c_t$$

8. **Survival**: Draw $\mathbb{1}_{\text{survive}} \sim \text{Bernoulli}(\pi)$

9. **State transition**: 
   $$k_{t+1} = \begin{cases} a_t & \text{if survive} \\ p_t \kappa_0' & \text{if die, where } \kappa_0' \sim F_{\kappa,\text{init}} \end{cases}$$
   $$p_t^{\text{next}} = \begin{cases} p_t & \text{if survive} \\ p_0' & \text{if die, where } p_0' \sim F_{p,\text{init}} \end{cases}$$

## 3. Bellman Equation

The agent's problem admits a recursive formulation decomposed into three value functions corresponding to the three perches.

### 3.1 Arrival Value (Pre-Shock Expectation)

At the arrival perch, before observing income shocks, the agent's value function is:

$$V^A(k_t, p_{t-1}) = \mathbb{E}_{\psi_t, \xi_t} \left[ V^D(m_t, p_t) \mid k_t, p_{t-1} \right]$$

where the expectation is taken over the joint shock distribution $F_{\psi,\xi}$, and the decision state variables are determined by:
$$p_t = \mathbb{G}(p_{t-1}) \cdot \psi_t, \quad m_t = R k_t + \xi_t p_t$$

**Information set at arrival perch**: $\mathcal{I}_t^A = \{k_t, p_{t-1}\}$

### 3.2 Decision Value (Post-Shock Optimization)

At the decision perch, after observing shocks and computing market resources, the agent solves:

$$V^D(m_t, p_t) = \max_{c_t \in [0, m_t]} \left\{ u(c_t) + \beta V^C(a_t, p_t) \right\}$$

subject to:
$$a_t = m_t - c_t$$

where:
- $u(\cdot)$ is the per-period utility function (typically $u(c) = \frac{c^{1-\rho}}{1-\rho}$ for CRRA preferences)
- $\beta \in (0,1)$ is the time discount factor
- $V^C$ is the continuation value function

**Information set at decision perch**: $\mathcal{I}_t^D = \{m_t, p_t, k_t, p_{t-1}\}$ (though the optimization problem depends only on $(m_t, p_t)$ due to Markovian structure)

### 3.3 Continuation Value (Post-Decision)

At the continuation perch, after choosing consumption but before mortality is resolved, the continuation value is:

$$V^C(a_t, p_t) = \pi \cdot V^A(a_t, p_t) + (1-\pi) \cdot V^{\text{newborn}}$$

where:
- $\pi$ is the survival probability
- $V^A(a_t, p_t)$ is the arrival value for next period with state $(k_{t+1}, p_t^{\text{next}}) = (a_t, p_t)$
- $V^{\text{newborn}} \coloneqq \mathbb{E}_{p_0, \kappa_0} [V^A(p_0 \kappa_0, p_0)]$ is the value of a newborn agent drawing from initial distributions

**Information set at continuation perch**: $\mathcal{I}_t^C = \{a_t, p_t\}$ plus the history, but future uncertainty remains.

### 3.4 Complete Bellman System

Combining the three perches, the complete recursive problem is:

$$\begin{aligned}
V^A(k, p_{-1}) &= \int \int V^D(Rk + \xi p, p) \, dF_{\psi,\xi}(\psi, \xi) \\
&\quad \text{where } p = \mathbb{G}(p_{-1}) \psi \\[1em]
V^D(m, p) &= \max_{c \in [0,m]} \left\{ u(c) + \beta V^C(m-c, p) \right\} \\[1em]
V^C(a, p) &= \pi V^A(a, p) + (1-\pi) \mathbb{E}_{p_0, \kappa_0}[V^A(p_0 \kappa_0, p_0)]
\end{aligned}$$

The policy function $\mathfrak{c}(m,p)$ is characterized by the argmax in the decision value function.

## 4. First-Order Conditions

### 4.1 Euler Equation

The first-order condition for the consumption choice yields the standard Euler equation. Taking the derivative with respect to $c_t$ in the decision value function:

$$u'(c_t) = \beta \frac{\partial V^C}{\partial a_t}(a_t, p_t)$$

Using the envelope theorem on the continuation value:

$$\frac{\partial V^C}{\partial a}(a,p) = \pi \frac{\partial V^A}{\partial k}(a, p)$$

And applying the envelope theorem to the arrival value:

$$\frac{\partial V^A}{\partial k}(k, p_{-1}) = \mathbb{E}_{\psi,\xi} \left[ \frac{\partial V^D}{\partial m}(m, p) \cdot R \mid k, p_{-1} \right]$$

Since $\frac{\partial V^D}{\partial m}(m,p) = u'(c)$ by the envelope theorem at the decision stage, we obtain:

$$u'(c_t) = \beta \pi R \mathbb{E}_t \left[ u'(c_{t+1}) \right]$$

where the expectation $\mathbb{E}_t[\cdot]$ is taken over the period $t+1$ shocks $(\psi_{t+1}, \xi_{t+1})$ conditional on the end-of-period state $(a_t, p_t)$.

### 4.2 CRRA Specification

For constant relative risk aversion (CRRA) utility $u(c) = \frac{c^{1-\rho}}{1-\rho}$, we have $u'(c) = c^{-\rho}$, and the Euler equation becomes:

$$c_t^{-\rho} = \beta \pi R \mathbb{E}_t \left[ c_{t+1}^{-\rho} \right]$$

### 4.3 Endogenous Grid Method Representation

The model is particularly amenable to the Endogenous Grid Method (EGM). Define the marginal value of end-of-period assets:

$$\mathfrak{v}(a, p) \coloneqq \frac{\partial V^C}{\partial a}(a,p) = \pi \mathbb{E}_{\psi,\xi} \left[ u'(\mathfrak{c}(Ra + \xi p', p')) \cdot R \mid p \right]$$

where $p' = \mathbb{G}(p) \psi$.

Given a current iterate of the consumption function $\mathfrak{c}$, the EGM approach:

1. **Specifies exogenous grid**: Choose grid points $\{a^j\}$ for end-of-period assets

2. **Computes marginal value**: For each $(a^j, p^i)$:
   $$\mathfrak{v}(a^j, p^i) = \pi R \mathbb{E}_{\psi,\xi} \left[ u'(\mathfrak{c}(Ra^j + \xi p', p')) \right]$$
   where $p' = \mathbb{G}(p^i) \psi$

3. **Inverts FOC**: Use $u'(c) = \beta \mathfrak{v}(a,p)$ to find:
   $$c^j_i = (u')^{-1}(\beta \mathfrak{v}(a^j, p^i))$$

4. **Constructs endogenous grid**: Compute market resources:
   $$m^j_i = a^j + c^j_i$$

5. **Interpolates**: The consumption function is the interpolation of $(m^j_i, c^j_i)$ for each $p^i$

This method is efficient because it avoids root-finding in the optimization step.

### 4.4 Envelope Conditions

The envelope conditions with respect to the state variables are:

$$\frac{\partial V^A}{\partial k}(k, p_{-1}) = R \mathbb{E}_{\psi,\xi} \left[ u'(c) \mid k, p_{-1} \right]$$

$$\frac{\partial V^A}{\partial p_{-1}}(k, p_{-1}) = \mathbb{E}_{\psi,\xi} \left[ u'(c) \cdot \left(\xi \psi \mathbb{G}'(p_{-1}) + \frac{\partial \mathfrak{c}}{\partial p}(m,p) \cdot \psi \mathbb{G}'(p_{-1})\right) \mid k, p_{-1} \right]$$

These conditions are used in computing the distribution dynamics and welfare analysis.

## 5. Forward Operator

The forward operator $\mathcal{T}$ maps the distribution of agents at the arrival perch in period $t$ to the distribution in period $t+1$.

### 5.1 Distributional State

Let $\Phi_t(k, p_{-1})$ denote the joint distribution of agents over $(k_t, p_{t-1})$ at the beginning of period $t$. This is the measure of agents at the arrival perch.

### 5.2 Within-Period Transitions

Given initial state $(k, p_{
