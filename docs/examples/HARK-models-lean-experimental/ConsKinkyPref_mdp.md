---
audience: user
type: example
topic: [applications]
---
# ConsKinkyPref — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Consumption-Saving Model with Kinky Preferences

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation | Perch |
|---------------|--------------|----------------------|-------|
| `kNrm` | Pre-decision normalized capital | $k_t$ | Arrival |
| `pLvlPrev` | Pre-decision permanent income | $p_{t-1}$ | Arrival |
| `PermShk` | Permanent income shock | $\psi_t$ | Decision |
| `TranShk` | Transitory income shock | $\xi_t$ | Decision |
| `yNrm` | Normalized labor income | $y_t$ | Decision |
| `pLvl` | Updated permanent income | $p_t$ | Decision |
| `G` | Realized permanent growth | $G_t$ | Decision |
| `Rfree` | Realized interest factor | $R_t$ | Decision |
| `bNrm` | Normalized bank balances | $b_t$ | Decision |
| `mNrm` | Normalized market resources | $m_t$ | Decision |
| `PrefShk` | Marginal utility shock | $\eta_t$ | Decision |
| `cNrm` | Normalized consumption | $c_t$ | Decision (control) |
| `aNrm` | Normalized end-of-period assets | $a_t$ | Continuation |
| `live` | Survival indicator | $\mathbb{1}_{\text{live}}$ | Continuation |

**Timing convention**: Variables at the arrival perch are indexed by $t$ (current period, pre-shock). Post-shock decision variables are also indexed by $t$. The twist mapping connects continuation perch variables $a_t, p_t$ to next period's arrival perch variables $k_{t+1} = a_t, p_t$ (which enters as `pLvlPrev` in period $t+1$).

## 2. Model

### 2.1 Primitives

This is an infinite-horizon consumption-saving model with a representative household facing idiosyncratic income risk and preference shocks. The household's problem features a **kinky interest rate structure**: the risk-free rate differs between borrowing and saving positions.

**State space at arrival perch**: $\mathcal{S}_{\text{arrival}} = \mathbb{R}_+ \times \mathbb{R}_+$, where the state is $(k_t, p_{t-1})$ with:
- $k_t \in \mathbb{R}$: normalized capital holdings (can be negative if borrowing)
- $p_{t-1} \in \mathbb{R}_+$: permanent income level from previous period

**Action space**: $\mathcal{A} = \mathbb{R}_+$, where $c_t \in [0, m_t]$ is normalized consumption.

**Shock structure**: At each period $t$, three independent shocks are realized:

1. **Income shocks** $(\psi_t, \xi_t) \sim F_{\text{inc}}$ where:
   - $\psi_t \in \mathbb{R}_+$ is a permanent income shock with $\mathbb{E}[\psi_t] = 1$
   - $\xi_t \in \mathbb{R}_+$ is a transitory income shock with $\mathbb{E}[\xi_t] = 1$

2. **Preference shock** $\eta_t \sim F_{\text{pref}}$ affecting marginal utility

3. **Mortality shock** with survival probability $\pi \in [0,1]$

**Parameters**:
- $R_{\text{boro}} > 1$: gross interest rate when borrowing ($k_t < 0$)
- $R_{\text{save}} > 1$: gross interest rate when saving ($k_t \geq 0$)
- $\Gamma > 0$: expected permanent income growth factor
- $\pi \in [0,1]$: survival probability

Typically, $R_{\text{boro}} > R_{\text{save}}$, creating a kink at zero assets.

### 2.2 Timing and Information Structure

The within-period timing follows the Arrival-Decision-Continuation (ADC) protocol:

**Arrival perch** (beginning of period $t$, pre-shock):
- Agent enters with state $(k_t, p_{t-1})$
- Information set: $\mathcal{F}_t^{\text{arr}} = \sigma\{k_t, p_{t-1}\}$

**Decision perch** (post-shock, pre-decision):
- Shocks $(\psi_t, \xi_t, \eta_t)$ realize
- Permanent income updates: $p_t = p_{t-1} \cdot \Gamma \cdot \psi_t \eqqcolon p_{t-1} \cdot G_t$
- Normalized labor income: $y_t = \xi_t$
- Interest factor realizes: $R_t = \begin{cases} R_{\text{boro}} & \text{if } k_t < 0 \\ R_{\text{save}} & \text{if } k_t \geq 0 \end{cases}$
- Bank balances: $b_t = \frac{R_t \cdot k_t}{G_t}$
- Market resources: $m_t = b_t + y_t$
- Information set: $\mathcal{F}_t^{\text{dec}} = \sigma\{k_t, p_{t-1}, \psi_t, \xi_t, \eta_t\}$
- Agent chooses consumption $c_t \in [0, m_t]$

**Continuation perch** (post-decision, pre-survival):
- End-of-period assets: $a_t = m_t - c_t$
- Information set: $\mathcal{F}_t^{\text{cont}} = \sigma\{k_t, p_{t-1}, \psi_t, \xi_t, \eta_t, c_t\}$
- Mortality shock realizes: agent survives with probability $\pi$

**Twist mapping** (connector to next period):
- If the agent survives: $(k_{t+1}, p_t) = (a_t, p_t)$
- If the agent dies: new agent drawn from initial distribution $(k_{t+1}, p_t) \sim F_{\text{init}}$

### 2.3 Preferences

The household has period utility over consumption with preference shocks:
$$u(c_t, \eta_t) = \eta_t \cdot u(c_t)$$

where $u(\cdot)$ is a standard CRRA utility function (typically) and $\eta_t$ is a multiplicative shock to marginal utility. The preference shock creates time-varying impatience or urgency to consume.

The household maximizes expected discounted lifetime utility:
$$\mathbb{E}_0 \left[ \sum_{t=0}^{\infty} \beta^t \pi^t \eta_t u(c_t) \right]$$

where $\beta \in (0,1)$ is the discount factor and $\pi^t$ accounts for survival probabilities.

### 2.4 Budget Constraint

The sequential budget constraints are:

1. **Beginning of period**: Capital $k_t$ earns interest rate depending on sign:
   $$b_t = \frac{R_t \cdot k_t}{G_t}$$
   where $R_t = \mathbb{1}_{\{k_t \geq 0\}} R_{\text{save}} + \mathbb{1}_{\{k_t < 0\}} R_{\text{boro}}$

2. **Market resources**: 
   $$m_t = b_t + y_t = \frac{R_t \cdot k_t}{G_t} + \xi_t$$

3. **End-of-period assets**:
   $$a_t = m_t - c_t$$

4. **Next period capital** (for survivors):
   $$k_{t+1} = a_t$$

The normalization by permanent income $p_t$ converts all nominal quantities to growth-adjusted terms, making the problem stationary despite permanent income growth.

## 3. Bellman Equation

The value function is decomposed according to the ADC perch structure.

### 3.1 Arrival Value Function

At the arrival perch, the agent has not yet observed the current period shocks. The arrival value function is:

$$V^{\text{arr}}(k_t, p_{t-1}) = \mathbb{E}_{\psi_t, \xi_t, \eta_t} \left[ V^{\text{dec}}(k_t, p_{t-1}, \psi_t, \xi_t, \eta_t) \mid \mathcal{F}_t^{\text{arr}} \right]$$

This represents the expected value before observing income and preference shocks, integrating over the joint distribution $F_{\text{inc}} \times F_{\text{pref}}$.

### 3.2 Decision Value Function

At the decision perch, after observing shocks, the agent solves:

$$V^{\text{dec}}(k_t, p_{t-1}, \psi_t, \xi_t, \eta_t) = \max_{c_t \in [0, m_t]} \left\{ \eta_t u(c_t) + \beta \pi V^{\text{cont}}(a_t, p_t) \right\}$$

where:
- $p_t = p_{t-1} \cdot \Gamma \cdot \psi_t$
- $G_t = \Gamma \cdot \psi_t$
- $R_t = \begin{cases} R_{\text{boro}} & \text{if } k_t < 0 \\ R_{\text{save}} & \text{if } k_t \geq 0 \end{cases}$
- $b_t = \frac{R_t \cdot k_t}{G_t}$
- $m_t = b_t + \xi_t$
- $a_t = m_t - c_t$

The information set $\mathcal{F}_t^{\text{dec}}$ includes all realized shocks: $\{k_t, p_{t-1}, \psi_t, \xi_t, \eta_t\}$.

### 3.3 Continuation Value Function

At the continuation perch, the agent has chosen consumption but not yet resolved mortality uncertainty:

$$V^{\text{cont}}(a_t, p_t) = V^{\text{arr}}(a_t, p_t)$$

This assumes that upon death, a new agent is born from the initial distribution, and we evaluate the equilibrium value at birth (in a stationary equilibrium, this equals the expected value of the initial distribution).

### 3.4 Complete Bellman Recursion

Combining all perches, the complete Bellman equation is:

$$\begin{aligned}
V^{\text{arr}}(k_t, p_{t-1}) &= \mathbb{E}_{\psi_t, \xi_t, \eta_t} \left[ \max_{c_t \in [0, m_t]} \left\{ \eta_t u(c_t) + \beta \pi V^{\text{arr}}(m_t - c_t, p_{t-1} \Gamma \psi_t) \right\} \right]
\end{aligned}$$

where $m_t = \frac{R_t k_t}{\Gamma \psi_t} + \xi_t$ and the kinked interest rate $R_t$ depends on the sign of $k_t$.

### 3.5 Normalized Formulation

Since the problem is normalized by permanent income, we can work with normalized variables exclusively. Define the normalized value function:

$$v(k_t) \coloneqq \frac{V^{\text{arr}}(k_t, p_{t-1})}{u(p_{t-1})}$$

Under CRRA utility $u(c) = \frac{c^{1-\rho}}{1-\rho}$, the normalized Bellman equation becomes:

$$v(k_t) = \mathbb{E}_{\psi_t, \xi_t, \eta_t} \left[ \max_{c_t \in [0, m_t]} \left\{ \eta_t \frac{c_t^{1-\rho}}{1-\rho} + \beta \pi (\Gamma \psi_t)^{1-\rho} v(a_t) \right\} \right]$$

This formulation isolates the scale-invariant structure of the problem.

## 4. First-Order Conditions

### 4.1 Euler Equation

The first-order condition for consumption at the decision perch is:

$$\eta_t u'(c_t) = \beta \pi \frac{\partial V^{\text{cont}}(a_t, p_t)}{\partial a_t}$$

By the envelope theorem applied at the continuation perch:

$$\frac{\partial V^{\text{cont}}(a_t, p_t)}{\partial a_t} = \frac{\partial V^{\text{arr}}(k_{t+1}, p_t)}{\partial k_{t+1}} \bigg|_{k_{t+1} = a_t}$$

At the arrival perch, integrating over next period's shocks:

$$\frac{\partial V^{\text{arr}}(k_{t+1}, p_t)}{\partial k_{t+1}} = \mathbb{E}_{\psi_{t+1}, \xi_{t+1}, \eta_{t+1}} \left[ \eta_{t+1} u'(c_{t+1}) \cdot \frac{R_{t+1}}{G_{t+1}} \mid k_{t+1}, p_t \right]$$

where:
- $R_{t+1} = \begin{cases} R_{\text{boro}} & \text{if } k_{t+1} < 0 \\ R_{\text{save}} & \text{if } k_{t+1} \geq 0 \end{cases}$
- $G_{t+1} = \Gamma \psi_{t+1}$

### 4.2 Complete Euler Equation

Combining these expressions, the complete Euler equation is:

$$\eta_t u'(c_t) = \beta \pi \mathbb{E}_{t+1} \left[ \eta_{t+1} u'(c_{t+1}) \cdot \frac{R_{t+1}}{\Gamma \psi_{t+1}} \right]$$

where the expectation $\mathbb{E}_{t+1}$ is taken over shocks $(\psi_{t+1}, \xi_{t+1}, \eta_{t+1})$ conditional on the end-of-period state $(a_t, p_t)$.

### 4.3 Envelope Condition

The marginal value of arriving wealth satisfies:

$$\frac{\partial V^{\text{arr}}(k_t, p_{t-1})}{\partial k_t} = \mathbb{E}_{\psi_t, \xi_t, \eta_t} \left[ \eta_t u'(c_t) \cdot \frac{R_t}{G_t} \right]$$

This reflects that an additional unit of capital $k_t$ increases market resources $m_t$ by $\frac{R_t}{G_t}$, with the marginal value weighted by the preference shock.

### 4.4 Kink at Zero Assets

The interest rate function $R_t$ is discontinuous at $k_t = 0$:

$$\lim_{k \to 0^-} R(k) = R_{\text{boro}} > R_{\text{save}} = \lim_{k \to 0^+} R(k)$$

This creates a kink in the value function and policy function at zero assets. The consumption function $c(m_t, \eta_t)$ will have a discontinuous derivative at the wealth level corresponding to $k_{t+1} = 0$.

### 4.5 Endogenous Grid Method (EGM) Representation

The model is solved using the End
