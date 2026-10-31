---
audience: user
type: example
topic: [applications]
---
# consumer — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Portfolio Choice Model

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation | Perch |
|--------------|--------------|----------------------|-------|
| `k` | Normalized capital (arrival) | $k_t$ | Arrival/Prestate |
| `live` | Survival shock | $\ell_t \in \{0,1\}$ | Arrival |
| `theta` | Transitory income shock | $\theta_t \in \mathbb{R}_+$ | Arrival |
| `b` | Bank balances | $b_t \coloneqq k_t R_{t-1} / \Gamma$ | Decision/Postshock |
| `m` | Market resources | $m_t \coloneqq b_t + \theta_t$ | Decision |
| `c` | Consumption (control) | $c_t \in [0, m_t]$ | Decision |
| `a` | Assets after consumption | $a_t \coloneqq m_t - c_t$ | Continuation |
| `stigma` | Portfolio share (control) | $\varsigma_t \in [0,1]$ | Continuation |
| `risky_return` | Risky asset return shock | $R^e_t \in \mathbb{R}_+$ | Continuation |
| `R` | Realized portfolio return | $R_t \coloneqq R_f + (R^e_t - R_f)\varsigma_t$ | Continuation |
| `u` | Flow utility | $u(c_t)$ | Reward |

**Timing Convention**: The model operates in normalized units where all level variables are divided by permanent income. The state variable $k_t$ represents normalized capital at the beginning of period $t$ (arrival perch), before shocks are realized.

## 2. Model

### 2.1 Primitive Spaces

**State Space**: $\mathcal{K} = \mathbb{R}_+ \cup \{0\}$ represents normalized capital holdings.

**Action Spaces**: 
- Consumption choice: $\mathcal{C}(m) = [0, m]$ where $m \in \mathbb{R}_+$ is market resources
- Portfolio share: $\mathcal{S} = [0, 1]$ represents the fraction invested in the risky asset

**Shock Spaces**:
- Survival: $\mathcal{L} = \{0, 1\}$ where $\ell = 1$ indicates survival
- Transitory income: $\Theta = \mathbb{R}_+$
- Risky return: $\mathcal{R}^e = \mathbb{R}_+$

### 2.2 Preferences and Technology

The agent has CRRA preferences with risk aversion parameter $\rho > 0$:
$$u(c) \coloneqq \frac{c^{1-\rho}}{1-\rho}$$

The agent discounts future utility at rate $\beta \in (0,1)$ and faces survival probability $p \in (0,1]$ each period.

### 2.3 Shock Distributions

**Survival shock**: $\ell_t \sim \text{Bernoulli}(p)$ where $\mathbb{P}(\ell_t = 1) = p$.

**Transitory income shock**: $\theta_t$ follows a mean-one lognormal distribution:
$$\log \theta_t \sim \mathcal{N}\left(-\frac{\sigma_\theta^2}{2}, \sigma_\theta^2\right)$$
such that $\mathbb{E}[\theta_t] = 1$.

**Risky asset return**: $R^e_t$ follows a lognormal distribution:
$$\log R^e_t \sim \mathcal{N}\left(\log(R_f + \pi) - \frac{\sigma_r^2}{2}, \sigma_r^2\right)$$
where $R_f$ is the risk-free gross return, $\pi$ is the equity premium, and $\mathbb{E}[R^e_t] = R_f + \pi$.

All shocks are mutually independent across time and within periods.

### 2.4 Dynamics and Timing

The model unfolds in two blocks corresponding to distinct decision stages:

**Block 1: Consumption-Normalized** (within period $t$)

1. Agent arrives with normalized capital $k_t$
2. Survival shock $\ell_t$ and income shock $\theta_t$ are realized
3. If $\ell_t = 0$, the agent dies and receives terminal value zero
4. If $\ell_t = 1$, portfolio from previous period returns, generating bank balances:
   $$b_t \coloneqq \frac{k_t R_{t-1}}{\Gamma}$$
   where $\Gamma > 0$ is the permanent income growth factor and $R_{t-1}$ was the realized return from period $t-1$
5. Market resources combine balances and income:
   $$m_t \coloneqq b_t + \theta_t$$
6. Agent chooses consumption $c_t \in [0, m_t]$ observing $m_t$
7. Assets after consumption:
   $$a_t \coloneqq m_t - c_t$$

**Block 2: Portfolio-Choice** (continuation of period $t$)

1. Agent observes assets $a_t$ after consumption
2. Agent chooses portfolio share $\varsigma_t \in [0,1]$ investing in risky asset
3. Risky return shock $R^e_t$ is realized
4. Portfolio return is determined:
   $$R_t \coloneqq R_f + (R^e_t - R_f)\varsigma_t = R_f(1-\varsigma_t) + R^e_t \varsigma_t$$
5. Capital evolves to next period:
   $$k_{t+1} \coloneqq a_t$$

The normalization by permanent income growth $\Gamma$ ensures stationarity of the distribution of normalized variables.

### 2.5 Borrowing Constraints

The specification includes `BoroCnstArt: None`, indicating no artificial borrowing constraint beyond the natural constraint that $c_t \leq m_t$ and $a_t \geq 0$.

## 3. Bellman Equation

The value function decomposes across three perches following the Arrival-Decision-Continuation (ADC) framework:

### 3.1 Arrival Value (Prestate Perch)

At the beginning of period $t$, before shocks are realized, the agent holds normalized capital $k_t$. The arrival value is:

$$v^A(k_t; R_{t-1}) \coloneqq \mathbb{E}_{\ell_t, \theta_t}\left[\ell_t \cdot v^D(m_t) \mid k_t, R_{t-1}\right]$$

where the expectation is over survival and income shocks, and conditional on surviving ($\ell_t = 1$), market resources are:
$$m_t = \frac{k_t R_{t-1}}{\Gamma} + \theta_t$$

**Information set**: $\{k_t, R_{t-1}\}$ and knowledge of shock distributions.

### 3.2 Decision Value (Postshock Perch)

After observing market resources $m_t$ (having survived and received income), the agent chooses consumption:

$$v^D(m_t) \coloneqq \max_{c_t \in [0, m_t]} \left\{u(c_t) + \beta p \cdot v^C(a_t)\right\}$$

where:
- $u(c_t) = \frac{c_t^{1-\rho}}{1-\rho}$ is flow utility
- $a_t = m_t - c_t$ are assets after consumption
- $\beta p$ is the effective discount factor accounting for survival probability
- $v^C(a_t)$ is the continuation value

**Information set**: $\{m_t\}$ and all parameters.

### 3.3 Continuation Value (Post-Decision Perch)

After choosing consumption, the agent holds assets $a_t$ and must choose portfolio allocation:

$$v^C(a_t) \coloneqq \max_{\varsigma_t \in [0,1]} \mathbb{E}_{R^e_t}\left[v^A(k_{t+1}; R_t) \mid a_t, \varsigma_t\right]$$

where:
- $R_t = R_f + (R^e_t - R_f)\varsigma_t$ is the portfolio return
- $k_{t+1} = a_t$ is capital entering next period
- The expectation is over the risky return shock $R^e_t$

**Information set**: $\{a_t\}$ and knowledge of the risky return distribution.

### 3.4 Complete Bellman Recursion

Combining all three perches, the complete recursion is:

$$v^A(k_t; R_{t-1}) = p \cdot \mathbb{E}_{\theta_t}\left[\max_{c_t \in [0, m_t]} \left\{u(c_t) + \beta p \cdot \max_{\varsigma_t \in [0,1]} \mathbb{E}_{R^e_t}\left[v^A(a_t; R_t)\right]\right\}\right]$$

subject to:
$$\begin{align}
m_t &= \frac{k_t R_{t-1}}{\Gamma} + \theta_t\\
a_t &= m_t - c_t\\
R_t &= R_f + (R^e_t - R_f)\varsigma_t\\
k_{t+1} &= a_t
\end{align}$$

## 4. First-Order Conditions

### 4.1 Consumption Euler Equation

The first-order condition for consumption $c_t$ yields the standard Euler equation:

$$u'(c_t) = \beta p \cdot \frac{\partial v^C(a_t)}{\partial a_t}$$

By the envelope theorem applied to the continuation value:

$$\frac{\partial v^C(a_t)}{\partial a_t} = \mathbb{E}_{R^e_t}\left[\frac{\partial v^A(k_{t+1}; R_t)}{\partial k_{t+1}} \cdot \frac{\partial k_{t+1}}{\partial a_t}\right] = \mathbb{E}_{R^e_t}\left[\frac{\partial v^A(a_t; R_t)}{\partial k}\right]$$

where we use $k_{t+1} = a_t$ and $\partial k_{t+1}/\partial a_t = 1$.

Applying the envelope theorem to the arrival value:

$$\frac{\partial v^A(k_t; R_{t-1})}{\partial k_t} = p \cdot \mathbb{E}_{\theta_t}\left[u'(c_t) \cdot \frac{R_{t-1}}{\Gamma}\right]$$

Combining these, the consumption Euler equation becomes:

$$u'(c_t) = \beta p^2 \mathbb{E}_{R^e_t}\left[\mathbb{E}_{\theta_{t+1}}\left[u'(c_{t+1}) \cdot \frac{R_t}{\Gamma}\right]\right]$$

In CRRA form:

$$c_t^{-\rho} = \beta p^2 \mathbb{E}_{R^e_t}\left[\mathbb{E}_{\theta_{t+1}}\left[c_{t+1}^{-\rho} \cdot \frac{R_t}{\Gamma}\right]\right]$$

### 4.2 Portfolio Euler Equation

The first-order condition for portfolio share $\varsigma_t$ is:

$$\frac{\partial}{\partial \varsigma_t} \mathbb{E}_{R^e_t}\left[v^A(a_t; R_t)\right] = 0$$

Computing the derivative:

$$\mathbb{E}_{R^e_t}\left[\frac{\partial v^A(a_t; R_t)}{\partial R_t} \cdot (R^e_t - R_f)\right] = 0$$

Using the envelope condition:

$$\frac{\partial v^A(k_{t+1}; R_t)}{\partial R_t} = p \cdot \mathbb{E}_{\theta_{t+1}}\left[u'(c_{t+1}) \cdot \frac{k_{t+1}}{\Gamma}\right]$$

The portfolio Euler equation becomes:

$$\mathbb{E}_{R^e_t}\left[(R^e_t - R_f) \cdot \mathbb{E}_{\theta_{t+1}}\left[u'(c_{t+1}) \cdot \frac{a_t}{\Gamma}\right]\right] = 0$$

In CRRA form:

$$\mathbb{E}_{R^e_t}\left[(R^e_t - R_f) \cdot \mathbb{E}_{\theta_{t+1}}\left[c_{t+1}^{-\rho}\right]\right] = 0$$

### 4.3 Endogenous Grid Method (EGM) Representation

The consumption problem is well-suited for EGM. Given a grid of assets-after-consumption $\{a^{(i)}\}$, we can compute:

1. **Marginal continuation value**:
   $$v^C_a(a^{(i)}) = \mathbb{E}_{R^e_t}\left[\frac{\partial v^A(a^{(i)}; R_t)}{\partial k}\right]$$

2. **Consumption from Euler equation**:
   $$c^{(i)} = \left(\beta p \cdot v^C_a(a^{(i)})\right)^{-1/\rho}$$

3. **Endogenous market resources**:
   $$m^{(i)} = a^{(i)} + c^{(i)}$$

This generates policy function $c(m)$ by interpolation on the $(m^{(i)}, c^{(i)})$ pairs.

The portfolio choice typically requires numerical optimization or root-finding for each asset level $a_t$.

## 5. Forward Operator

The distribution of agents evolves through the joint dynamics of consumption and portfolio choices.

### 5.1 Distribution Evolution

Let $\Psi_t(k)$ denote the cumulative distribution function of normalized capital at the beginning of period $t$ across surviving agents. The forward operator maps $\Psi_t \mapsto \Psi_{t+1}$.

**Step 1: Portfolio returns and consumption**

Given $k_t$ drawn from $\Psi_t$ and previous period's return $R_{t-1}$ (which may be deterministic in steady state or drawn from an ergodic distribution):

1. Survival shock: agent survives with probability $p$
2. Market resources: $m_t = \frac{k_t R_{t-1}}{\Gamma} + \theta_t$ where $\theta_t$ is drawn from the transitory income distribution
3. Consumption: $c_t = c^*(m_t)$ from the consumption policy function
4. Assets: $a_t = m_t - c_t$

**Step 2: Portfolio choice and capital evolution**

5. Portfolio share: $\varsigma_t = \varsigma^*(a_t)$ from the portfolio policy function
6. Return realization: $R^e_t$ drawn from risky return distribution
7. Portfolio return: $R_t = R_f + (R^e_t - R_f)\varsigma_t$
8. Next period capital: $k_{t+1} = a_t$

### 5.2 Formal Operator

The forward operator $\mathcal{T}$ is defined by:

$$\Psi_{t+1}(k') = \int_{\mathc
