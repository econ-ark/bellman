---
audience: user
type: example
topic: [applications]
---
# ConsPrefShock — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Saving Model with Preference Shocks

## 1. Rosetta Stone

This table maps HARK variable names to DDSL/ADC concepts and establishes the formal mathematical notation used throughout this document.

| HARK variable | DDSL concept | Mathematical notation | Description |
|--------------|--------------|----------------------|-------------|
| `kNrm` | Prestate (arrival) | $k_t$ | Normalized capital at period start |
| `pLvlPrev` | Prestate (arrival) | $P_{t-1}$ | Permanent income from previous period |
| `yNrm` | Intermediate | $y_t$ | Normalized labor income (transitory shock) |
| `pLvl` | Intermediate | $P_t$ | Current permanent income level |
| `bNrm` | Intermediate | $b_t$ | Normalized bank balances after returns |
| `mNrm` | Decision perch | $m_t$ | Normalized market resources |
| `PrefShk` | Shock (decision) | $\xi_t$ | Marginal utility multiplier |
| `cNrm` | Control (decision) | $c_t$ | Normalized consumption choice |
| `aNrm` | Continuation perch | $a_t$ | Normalized end-of-period assets |
| `live` | Survival indicator | $\mathbb{1}_{\text{live}}$ | Binary survival outcome |
| `PermShk` | Shock (permanent) | $\psi_t$ | Permanent income shock |
| `TranShk` | Shock (transitory) | $\theta_t$ | Transitory income shock |

**Timing convention**: Period $t$ begins with prestate $(k_t, P_{t-1})$. Income shocks $(\psi_t, \theta_t)$ realize, transforming the state to decision perch $m_t$. The agent observes preference shock $\xi_t$ and chooses $c_t$, yielding continuation state $a_t$. The twist mapping connects $a_t \to k_{t+1}$ and $P_t \to P_t$ (carried forward).

## 2. Model

### 2.1 State Spaces

**Prestate (Arrival Perch)**: The agent begins period $t$ with:
- Normalized capital holdings: $k_t \in \mathbb{R}_+$
- Previous period's permanent income: $P_{t-1} \in \mathbb{R}_{++}$

**Decision Perch**: After income realization but before consumption choice:
- Normalized market resources: $m_t \in \mathbb{R}_+$
- Preference shock realization: $\xi_t \in \mathbb{R}_{++}$

**Continuation Perch**: After consumption choice:
- Normalized end-of-period assets: $a_t \in \mathbb{R}_+$
- Updated permanent income: $P_t \in \mathbb{R}_{++}$

### 2.2 Action Space

The agent's control is normalized consumption:
$$\mathcal{C}(m_t, \xi_t) = \{c_t \in \mathbb{R}_+ : c_t \leq m_t\}$$

The budget constraint requires consumption not to exceed available market resources.

### 2.3 Shock Distributions

**Income Shocks**: The joint distribution of permanent and transitory income shocks is:
$$(\psi_t, \theta_t) \sim F_{\text{Inc}}$$
where $\psi_t \in \mathbb{R}_{++}$ is the permanent shock and $\theta_t \in \mathbb{R}_+$ is the transitory shock (normalized labor income).

**Preference Shocks**: The marginal utility multiplier follows:
$$\xi_t \sim F_{\text{Pref}}$$
where $\xi_t \in \mathbb{R}_{++}$ scales the marginal utility of consumption.

**Survival**: At the end of each period:
$$\mathbb{1}_{\text{live},t+1} \sim \text{Bernoulli}(\pi)$$
where $\pi \coloneqq \texttt{LivPrb}$ is the survival probability.

**Initial Conditions**: At model birth ($t=0$):
$$P_{-1} \sim F_{P,\text{init}}, \quad k_0 \sim F_{k,\text{init}}$$

### 2.4 State Transitions

The state evolves through the following sequence within period $t$:

**Step 1 (Income Realization)**: Shocks realize and permanent income updates:
$$\begin{align}
(\psi_t, \theta_t) &\sim F_{\text{Inc}} \\
G_t &\coloneqq \Gamma \cdot \psi_t \\
P_t &= P_{t-1} \cdot G_t
\end{align}$$
where $\Gamma \coloneqq \texttt{PermGroFac}$ is the deterministic growth factor.

**Step 2 (Market Resources)**: Capital earns returns and combines with labor income:
$$\begin{align}
b_t &= \frac{R \cdot k_t}{G_t} \\
m_t &= b_t + \theta_t
\end{align}$$
where $R \coloneqq \texttt{Rfree}$ is the gross risk-free rate. Note that $b_t$ represents normalized bank balances after both capital returns and permanent income growth.

**Step 3 (Preference Shock and Consumption)**: The preference shock realizes and consumption is chosen:
$$\begin{align}
\xi_t &\sim F_{\text{Pref}} \\
c_t &= c^*(m_t, \xi_t)
\end{align}$$
where $c^*(\cdot, \cdot)$ is the optimal consumption policy function.

**Step 4 (Asset Accumulation)**: End-of-period assets are determined by the budget constraint:
$$a_t = m_t - c_t$$

**Step 5 (Survival and Twist)**: The survival outcome realizes, and for survivors:
$$\begin{align}
\mathbb{1}_{\text{live},t+1} &\sim \text{Bernoulli}(\pi) \\
k_{t+1} &= a_t \\
P_t &\to P_t \text{ (carried forward)}
\end{align}$$

Non-survivors exit the model with terminal utility zero.

### 2.5 Preferences

The agent has time-separable preferences with CRRA utility modified by multiplicative preference shocks. The period utility function is:
$$u(c_t, \xi_t) = \xi_t \cdot \frac{c_t^{1-\rho}}{1-\rho}$$
where $\rho > 0$ is the coefficient of relative risk aversion (not explicitly in parameters but implicit in HARK's implementation). The preference shock $\xi_t$ multiplicatively scales marginal utility, creating heterogeneity in consumption propensities.

The discount factor is $\beta \in (0,1)$, and survival probability $\pi$ compounds with time preference.

## 3. Bellman Equation

The value function is decomposed across three perches following the ADC framework.

### 3.1 Arrival Value (Prestate)

At the beginning of period $t$, before income shocks realize, the agent's value is:
$$V^{\text{arr}}(k_t, P_{t-1}) = \mathbb{E}\left[V^{\text{dec}}(m_t, \xi_t, P_t) \,\Big|\, k_t, P_{t-1}\right]$$

The expectation is taken over $(\psi_t, \theta_t, \xi_t)$, which determine $(m_t, P_t)$ through:
$$\begin{align}
G_t &= \Gamma \psi_t \\
P_t &= P_{t-1} G_t \\
b_t &= \frac{R k_t}{G_t} \\
m_t &= b_t + \theta_t
\end{align}$$

**Information set**: $\mathcal{F}^{\text{arr}}_t = \{k_t, P_{t-1}\}$

### 3.2 Decision Value (Post-Shock, Pre-Choice)

After observing market resources $m_t$ and preference shock $\xi_t$, the agent solves:
$$V^{\text{dec}}(m_t, \xi_t, P_t) = \max_{c_t \in [0, m_t]} \left\{\xi_t \cdot \frac{c_t^{1-\rho}}{1-\rho} + \beta \pi \cdot V^{\text{cont}}(a_t, P_t)\right\}$$

subject to the budget constraint:
$$a_t = m_t - c_t$$

**Information set**: $\mathcal{F}^{\text{dec}}_t = \{m_t, \xi_t, P_t\}$

The term $\beta \pi$ combines time preference and survival probability. Non-survivors receive zero continuation value.

### 3.3 Continuation Value (Post-Choice)

After choosing consumption, the continuation value is:
$$V^{\text{cont}}(a_t, P_t) = V^{\text{arr}}(k_{t+1}, P_t)$$

where the twist mapping gives:
$$k_{t+1} = a_t$$

Note that $P_t$ carries forward unchanged: the permanent income state at the end of period $t$ becomes the "previous" permanent income for period $t+1$.

**Information set**: $\mathcal{F}^{\text{cont}}_t = \{a_t, P_t\}$

### 3.4 Recursive Formulation

Combining the three perches, the full Bellman equation is:
$$\begin{align}
V^{\text{arr}}(k_t, P_{t-1}) &= \mathbb{E}_{(\psi_t,\theta_t,\xi_t)}\left[\max_{c_t \leq m_t} \left\{\xi_t \cdot \frac{c_t^{1-\rho}}{1-\rho} + \beta \pi \cdot V^{\text{arr}}(m_t - c_t, P_{t-1}\Gamma\psi_t)\right\}\right] \\
\text{where} \quad m_t &= \frac{R k_t}{\Gamma \psi_t} + \theta_t
\end{align}$$

This formulation makes explicit that:
1. The expectation is taken before observing shocks
2. Market resources $m_t$ depend on realized permanent shock $\psi_t$
3. Permanent income evolves as $P_t = P_{t-1} \Gamma \psi_t$
4. The continuation value depends on assets $a_t = m_t - c_t$ and updated permanent income $P_t$

## 4. First-Order Conditions

### 4.1 Euler Equation

The first-order condition for optimal consumption, when interior ($c_t \in (0, m_t)$), is:
$$\xi_t \cdot c_t^{-\rho} = \beta \pi \cdot \frac{\partial V^{\text{arr}}(a_t, P_t)}{\partial a_t}$$

The left side is the marginal utility of consumption scaled by the preference shock. The right side is the expected marginal value of saving.

### 4.2 Envelope Condition

The marginal value of wealth at the arrival perch satisfies:
$$\frac{\partial V^{\text{arr}}(k_t, P_{t-1})}{\partial k_t} = \mathbb{E}\left[\frac{\partial V^{\text{dec}}(m_t, \xi_t, P_t)}{\partial m_t} \cdot \frac{\partial m_t}{\partial k_t} \,\Big|\, k_t, P_{t-1}\right]$$

where:
$$\frac{\partial m_t}{\partial k_t} = \frac{R}{G_t} = \frac{R}{\Gamma \psi_t}$$

At the decision perch, the envelope theorem gives:
$$\frac{\partial V^{\text{dec}}(m_t, \xi_t, P_t)}{\partial m_t} = \xi_t \cdot c_t^{-\rho}$$

Combining these:
$$\frac{\partial V^{\text{arr}}(k_t, P_{t-1})}{\partial k_t} = \mathbb{E}\left[\xi_t \cdot c_t^{-\rho} \cdot \frac{R}{\Gamma \psi_t} \,\Big|\, k_t, P_{t-1}\right]$$

### 4.3 Euler Equation in Expectation Form

Substituting the envelope condition into the Euler equation:
$$\xi_t \cdot c_t^{-\rho} = \beta \pi \cdot \mathbb{E}_{t+1}\left[\xi_{t+1} \cdot c_{t+1}^{-\rho} \cdot \frac{R}{\Gamma \psi_{t+1}}\right]$$

where $\mathbb{E}_{t+1}$ denotes expectation conditional on information at the end of period $t$ (i.e., conditional on $a_t, P_t$).

This can be rewritten in terms of normalized consumption growth:
$$\xi_t = \beta \pi R \cdot \mathbb{E}_{t+1}\left[\xi_{t+1} \cdot G_{t+1}^{\rho} \cdot \left(\frac{c_{t+1}}{c_t}\right)^{-\rho}\right]$$

### 4.4 Endogenous Grid Method (EGM) Representation

HARK implements this model using the Endogenous Grid Method. The algorithm works backward from a grid of end-of-period assets $\{a_j\}$:

**Step 1**: For each $(a_j, P_t)$ and each realization $(\psi_{t+1}, \theta_{t+1}, \xi_{t+1})$, compute:
$$\begin{align}
G_{t+1} &= \Gamma \psi_{t+1} \\
k_{t+1} &= a_j \\
m_{t+1} &= \frac{R k_{t+1}}{G_{t+1}} + \theta_{t+1} \\
c_{t+1} &= c^*(m_{t+1}, \xi_{t+1})
\end{align}$$

**Step 2**: Compute the expected marginal value:
$$\mathcal{E}_j(P_t) = \mathbb{E}\left[\xi_{t+1} \cdot c_{t+1}^{-\rho} \cdot \frac{R}{G_{t+1}} \,\Big|\, a_j, P_t\right]$$

**Step 3**: Use the Euler equation to find consumption on the endogenous grid:
$$c_j(\xi_t, P_t) = \left(\beta \pi \cdot \mathcal{E}_j(P_t) / \xi_t\right)^{-1/\rho}$$

**Step 4**: Invert the budget constraint to find the endogenous grid of market resources:
$$m_j(\xi_t, P_t) = a_j + c_j(\xi_t, P_t)$$

**Step 5**: Interpolate to construct $c^*(m, \xi_t)$ for all $m$.

The preference shock $\xi_t$ creates multiple consumption functions—one for each realization of $\xi_t$—that must be integrated over when computing expectations at the arrival perch.

## 5. Forward Operator

The forward operator describes how the cross-sectional distribution of agents evolves over time. Let $\Phi_t(k, P)$ denote the joint density of normalized capital and permanent income at
