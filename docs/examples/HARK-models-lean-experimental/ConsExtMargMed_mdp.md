---
audience: user
type: example
topic: [applications]
---
# ConsExtMargMed — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Saving with Medical Shocks

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation |
|--------------|--------------|----------------------|
| `kLvl` | Prestate (arrival perch) | $k \in \mathbb{R}_+$ |
| `pLvlPrev` | Prestate (arrival perch) | $p^- \in \mathbb{R}_{++}$ |
| `PermShk` | Permanent income shock | $\Psi \in \mathbb{R}_{++}$ |
| `TranShk` | Transitory income shock | $\xi \in \mathbb{R}_+$ |
| `pLvl` | Post-income-shock state | $p \in \mathbb{R}_{++}$ |
| `yLvl` | Labor income realization | $y \in \mathbb{R}_+$ |
| `wLvl` | Wealth from assets | $w \in \mathbb{R}_+$ |
| `mLvl` | Market resources (decision perch) | $m \in \mathbb{R}_+$ |
| `MedCost` | Medical cost shock | $\mu \in \mathbb{R}_+$ |
| `MedShk` | Medical utility shock | $\zeta \in \mathbb{R}_+$ |
| `Care` | Medical care decision | $\mathbb{1}_{\text{care}} \in \{0,1\}$ |
| `MedLvl` | Realized medical expenditure | $\tilde{\mu} \in \mathbb{R}_+$ |
| `bLvl` | Bank balances post-medical | $b \in \mathbb{R}_+$ |
| `cLvl` | Consumption (control) | $c \in \mathbb{R}_+$ |
| `aLvl` | End-of-period assets (continuation perch) | $a \in \mathbb{R}_+$ |
| `live` | Survival indicator | $\mathbb{1}_{\text{live}} \in \{0,1\}$ |

**Timing Convention:** The model features a four-perch structure within each period:
1. **Arrival perch:** Agent begins with state $(k, p^-)$
2. **Post-income perch:** After permanent income growth/shocks, state becomes $(m, p)$
3. **Decision perch:** After medical shock realization, agent chooses care and consumption
4. **Continuation perch:** End-of-period state $(a, p)$ transitions to next period's $(k', p'^-)$

## 2. Model

### 2.1 State Spaces

The agent's economic state evolves through multiple perches within each period:

**Arrival State:** At the beginning of period $t$, the agent possesses:
- Capital holdings $k_t \in \mathbb{R}_+ \coloneqq [0, \infty)$
- Previous permanent income level $p_t^- \in \mathbb{R}_{++} \coloneqq (0, \infty)$

**Post-Income State:** After income realization but before decisions:
- Market resources $m_t \in \mathbb{R}_+$
- Current permanent income $p_t \in \mathbb{R}_{++}$

**Decision State:** After observing medical shocks:
- Market resources $m_t$
- Permanent income $p_t$
- Medical cost $\mu_t$
- Medical utility shock $\zeta_t$

**Continuation State:** After all within-period decisions:
- End-of-period assets $a_t \in \mathbb{R}_+$
- Current permanent income $p_t \in \mathbb{R}_{++}$

### 2.2 Action Spaces

The agent makes two sequential decisions each period:

**Medical Care Decision:** $\mathbb{1}_{\text{care},t} \in \{0, 1\}$ — binary choice of whether to purchase medical care at cost $\mu_t$.

**Consumption Decision:** $c_t \in [0, b_t]$ where $b_t$ denotes bank balances after medical expenditure.

### 2.3 Shock Distributions

**Income Shocks:** The joint distribution of permanent and transitory income shocks is denoted $F_{\Psi, \xi}$, with support $\mathbb{R}_{++} \times \mathbb{R}_+$. Each period, the agent draws:
$$(\Psi_t, \xi_t) \sim F_{\Psi, \xi}$$

**Medical Shocks:** The joint distribution of medical costs and utility penalties is denoted $G_{\mu, \zeta}$, with support $\mathbb{R}_+ \times \mathbb{R}_+$. Each period, independently of income shocks:
$$(\mu_t, \zeta_t) \sim G_{\mu, \zeta}$$

**Survival Shock:** At the end of each period, the agent survives with probability $\pi \in (0, 1]$:
$$\mathbb{1}_{\text{live},t} \sim \text{Bernoulli}(\pi)$$

**Initial Conditions:** At model initialization (period $t=0$), the agent draws:
- Permanent income: $p_0^- \sim F_{p,0}$
- Normalized capital: $\kappa_0 \sim F_{\kappa,0}$
- De-normalized capital: $k_0 = p_0^- \cdot \kappa_0$

### 2.4 Transition Dynamics

The within-period dynamics proceed sequentially through four distinct phases:

**Phase 1 — Income Realization:**
Beginning with arrival state $(k_t, p_t^-)$, the agent experiences income shocks and realizes:

1. Expected permanent income before shock: $\bar{p}_t = \mathbb{E}[p_t | p_t^-]$ (deterministic growth function)
2. Permanent income realization: $p_t = \bar{p}_t \cdot \Psi_t$
3. Labor income: $y_t = \xi_t \cdot p_t$
4. Wealth from assets: $w_t = R \cdot k_t$ where $R > 0$ is the gross risk-free return
5. Market resources: $m_t = w_t + y_t$

**Phase 2 — Medical Shock and Care Decision:**
After observing medical shock $(\mu_t, \zeta_t)$, the agent evaluates:

1. Bank balances if care purchased: $b_{\text{care}} = m_t - \mu_t$
2. Value if care purchased: $V^{\text{mid}}(b_{\text{care}}, p_t)$
3. Value if no care: $V^{\text{mid}}(m_t, p_t) - \zeta_t$
4. Optimal care decision:
$$\mathbb{1}_{\text{care},t} = \begin{cases} 1 & \text{if } V^{\text{mid}}(m_t - \mu_t, p_t) > V^{\text{mid}}(m_t, p_t) - \zeta_t \\ 0 & \text{otherwise} \end{cases}$$
5. Realized medical expenditure: $\tilde{\mu}_t = \mathbb{1}_{\text{care},t} \cdot \mu_t$
6. Bank balances post-medical: $b_t = m_t - \tilde{\mu}_t$

**Phase 3 — Consumption Decision:**
Given bank balances $b_t$ and permanent income $p_t$, the agent consumes:
$$c_t = c^*(b_t, p_t)$$
where $c^*: \mathbb{R}_+ \times \mathbb{R}_{++} \to \mathbb{R}_+$ is the optimal consumption policy function.

**Phase 4 — Asset Accumulation and Survival:**
1. End-of-period assets: $a_t = b_t - c_t$
2. Survival realization: $\mathbb{1}_{\text{live},t} \sim \text{Bernoulli}(\pi)$

**Twist (Between-Period Transition):**
For surviving agents ($\mathbb{1}_{\text{live},t} = 1$), the continuation state $(a_t, p_t)$ becomes next period's arrival state:
$$k_{t+1} = a_t, \quad p_{t+1}^- = p_t$$

Non-survivors exit the model (absorbing state).

### 2.5 Preferences

The agent has additively separable utility over consumption with medical utility shocks. The period utility function is:
$$u(c_t, \mathbb{1}_{\text{care},t}, \zeta_t) = u(c_t) - (1 - \mathbb{1}_{\text{care},t}) \cdot \zeta_t$$

The specific functional form of $u(\cdot)$ is not specified in the YAML but is typically CRRA:
$$u(c) = \frac{c^{1-\rho}}{1-\rho}$$
for relative risk aversion $\rho > 0$, with $u(c) = \log(c)$ when $\rho = 1$.

## 3. Bellman Equation

The agent's problem decomposes into a sequence of value functions corresponding to different information sets within the period.

### 3.1 Arrival Value Function

At the beginning of the period, before observing any within-period shocks, the agent's arrival value is:
$$V^{\text{arr}}(k, p^-) = \mathbb{E}_{\Psi, \xi, \mu, \zeta}\left[ V^{\text{dec}}(m, p, \mu, \zeta) \mid k, p^- \right]$$

where the expectation is taken over:
- Income shocks $(\Psi, \xi)$
- Medical shocks $(\mu, \zeta)$

and market resources and permanent income are determined by:
- $\bar{p} = \mathbb{E}[p | p^-]$
- $p = \bar{p} \cdot \Psi$
- $y = \xi \cdot p$
- $w = R \cdot k$
- $m = w + y$

**Information Set at Arrival:** $\mathcal{I}^{\text{arr}}_t = \{k_t, p_t^-\}$

### 3.2 Decision Value Function

After observing market resources $m$, permanent income $p$, and medical shocks $(\mu, \zeta)$, the agent solves:
$$V^{\text{dec}}(m, p, \mu, \zeta) = \max_{\mathbb{1}_{\text{care}} \in \{0,1\}} \left\{ V^{\text{mid}}(m - \mathbb{1}_{\text{care}} \cdot \mu, p) - (1 - \mathbb{1}_{\text{care}}) \cdot \zeta \right\}$$

This can be written explicitly as:
$$V^{\text{dec}}(m, p, \mu, \zeta) = \max\left\{ V^{\text{mid}}(m - \mu, p), \; V^{\text{mid}}(m, p) - \zeta \right\}$$

The optimal medical care policy is:
$$\mathbb{1}_{\text{care}}^*(m, p, \mu, \zeta) = \begin{cases} 1 & \text{if } V^{\text{mid}}(m - \mu, p) \geq V^{\text{mid}}(m, p) - \zeta \\ 0 & \text{otherwise} \end{cases}$$

Equivalently, care is purchased if and only if:
$$\zeta \geq V^{\text{mid}}(m, p) - V^{\text{mid}}(m - \mu, p)$$

That is, care is purchased when the utility loss from the medical shock exceeds the value loss from paying the medical cost.

**Information Set at Decision:** $\mathcal{I}^{\text{dec}}_t = \{m_t, p_t, \mu_t, \zeta_t\}$

### 3.3 Mid-Period Value Function

After making the medical care decision, the agent has bank balances $b$ and must choose consumption:
$$V^{\text{mid}}(b, p) = \max_{c \in [0, b]} \left\{ u(c) + \beta \pi \cdot V^{\text{cont}}(b - c, p) \right\}$$

where $\beta \in (0, 1)$ is the time discount factor and $\pi$ is the survival probability.

**Information Set at Mid-Period:** $\mathcal{I}^{\text{mid}}_t = \{b_t, p_t\}$ (medical shocks and care decision already resolved)

### 3.4 Continuation Value Function

At the end of the period, with assets $a$ and permanent income $p$, the continuation value (for survivors) is:
$$V^{\text{cont}}(a, p) = V^{\text{arr}}(k', p'^-) \Big|_{k' = a, \, p'^- = p}$$

This reflects the transition from continuation perch to next period's arrival perch via the twist mapping.

**Information Set at Continuation:** $\mathcal{I}^{\text{cont}}_t = \{a_t, p_t\}$

### 3.5 Complete Bellman System

The complete recursive problem can be written as a system:

$$\begin{aligned}
V^{\text{arr}}(k, p^-) &= \mathbb{E}_{\Psi, \xi, \mu, \zeta}\left[ V^{\text{dec}}(R k + \xi \bar{p} \Psi, \bar{p} \Psi, \mu, \zeta) \right] \\[0.5em]
V^{\text{dec}}(m, p, \mu, \zeta) &= \max\left\{ V^{\text{mid}}(m - \mu, p), \; V^{\text{mid}}(m, p) - \zeta \right\} \\[0.5em]
V^{\text{mid}}(b, p) &= \max_{c \in [0, b]} \left\{ u(c) + \beta \pi \cdot V^{\text{arr}}(b - c, p) \right\} \\[0.5em]
\end{aligned}$$

where $\bar{p} = \mathbb{E}[p | p^-]$ and we've substituted the twist mapping in the final line.

## 4. First-Order Conditions

### 4.1 Consumption Euler Equation

For the consumption decision at the mid-period perch, the first-order condition with respect to $c$ is:
$$u'(c) = \beta \pi \cdot \frac{\partial V^{\text{arr}}}{\partial k}(a, p)$$

where $a = b - c$ denotes end-of-period assets.

By the envelope theorem applied to $V^{\text{arr}}(k, p^-)$:
$$\frac{\partial V^{\text{arr}}}{\partial k}(k, p^-) = R \cdot \mathbb{E}_{\Psi, \xi, \mu, \zeta}\left[ \frac{\partial V^{\text{dec}}}{\partial m}(m, p, \mu, \zeta) \mid k, p^- \right]$$

And by the envelope theorem applied to $V^{\text{dec}}$:
$$\frac{\partial V^{\text{dec}}}{\partial m}(m, p, \mu, \zeta) = \frac{\partial V^{\text{mid}}}{\partial b}(b, p)$$

where $b = m - \mathbb{1}_{\text{care}} \cdot \mu$ is bank balances after the optimal medical care decision.

Finally, applying the envelope theorem to $V^{\text{mid}}$:
$$\frac{\partial V^{\text{mid}}}{\partial b}(b, p) = u'(c)$$

where $c = c^*(
