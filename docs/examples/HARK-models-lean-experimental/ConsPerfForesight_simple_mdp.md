---
audience: user
type: example
topic: [applications]
---
# ConsPerfForesight_simple — Formal MDP Document

*Auto-generated from HARK model specification*

---

# Formal MDP Document: Perfect Foresight Consumption-Saving Model with Mortality Risk

## 1. Rosetta Stone

| HARK variable | DDSL concept | Mathematical notation | Description |
|--------------|--------------|----------------------|-------------|
| `kNrm` | Prestate (arrival perch) | $k_t$ | Normalized capital at beginning of period |
| `pLvlPrev` | Prestate (arrival perch) | $p_{t-1}$ | Permanent income level from previous period |
| `yNrm` | Intermediate | $y_t$ | Normalized income (deterministic) |
| `pLvl` | Intermediate | $p_t$ | Current permanent income level |
| `bNrm` | Intermediate | $b_t$ | Normalized bank balances (post-return capital) |
| `mNrm` | Decision perch state | $m_t$ | Normalized market resources |
| `cNrm` | Control (action) | $c_t$ | Normalized consumption |
| `aNrm` | Continuation perch state | $a_t$ | Normalized end-of-period assets |
| `live` | Shock | $\zeta_t$ | Survival indicator |
| `cFunc` | Policy function | $c(\cdot)$ | Consumption policy |
| `Rfree` | Parameter | $R$ | Gross risk-free interest rate |
| `PermGroFac` | Parameter | $\Gamma$ | Permanent income growth factor |
| `LivPrb` | Parameter | $\mathcal{L}$ | Survival probability |

## 2. Model

We consider an infinite-horizon consumption-saving problem with deterministic income growth and mortality risk. Time is discrete and indexed by $t \in \{0, 1, 2, \ldots\}$.

**State Variables.** The agent's state at the beginning of period $t$ (arrival perch) consists of:
- Normalized capital holdings $k_t \in \mathbb{R}_+$, representing assets carried forward from the previous period
- Previous period's permanent income level $p_{t-1} \in \mathbb{R}_{++}$

**Action Space.** At the decision perch, the agent observes normalized market resources $m_t \in \mathbb{R}_+$ and chooses normalized consumption $c_t \in [0, m_t]$.

**Permanent Income Dynamics.** Permanent income evolves deterministically:
$$p_t \coloneqq p_{t-1} \cdot \Gamma$$
where $\Gamma > 0$ is the permanent income growth factor.

**Budget Constraint.** The agent receives deterministic normalized labor income $y_t = 1$ each period. After the risk-free return $R$ is applied to beginning-of-period capital, normalized bank balances are:
$$b_t \coloneqq R \cdot \frac{k_t}{\Gamma}$$

The normalization by $\Gamma$ accounts for permanent income growth between periods. Normalized market resources are then:
$$m_t \coloneqq b_t + y_t = R \cdot \frac{k_t}{\Gamma} + 1$$

After choosing consumption $c_t$, normalized end-of-period assets are:
$$a_t \coloneqq m_t - c_t$$

**Mortality Risk.** At the end of each period, the agent survives with probability $\mathcal{L} \in (0, 1]$ and dies with probability $1 - \mathcal{L}$. We represent this via a survival indicator:
$$\zeta_t \sim \text{Bernoulli}(\mathcal{L})$$

**State Transition.** If the agent survives ($\zeta_t = 1$), next period's normalized capital is:
$$k_{t+1} \coloneqq a_t$$

If the agent dies ($\zeta_t = 0$), the optimization problem terminates (or the agent is replaced by a newborn with initial distribution).

**Information Structure.** At the beginning of period $t$, the agent observes $(k_t, p_{t-1})$. The permanent income update and budget constraint computations occur before the consumption choice, so at the decision perch the agent observes $(m_t, p_t)$. The mortality shock $\zeta_t$ is realized after the consumption-saving decision.

**Initial Distribution.** The agent begins with initial draws:
$$k_0 \sim \mu_{k,0}, \quad p_{-1} \sim \mu_{p,0}$$
where $\mu_{k,0}$ and $\mu_{p,0}$ are specified initial distributions.

## 3. Bellman Equation

The value function can be decomposed according to the ADC (Arrival-Decision-Continuation) perch structure.

**Arrival Value Function.** At the arrival perch, the agent has state $(k_t, p_{t-1})$ and has not yet computed market resources. The arrival value is:
$$V^A(k_t, p_{t-1}) = V^D(m_t, p_t)$$
where the transition to the decision perch involves the deterministic transformations:
$$p_t = p_{t-1} \cdot \Gamma, \quad m_t = R \cdot \frac{k_t}{\Gamma} + 1$$

Since these are deterministic, there is no expectation operator between arrival and decision perches.

**Decision Value Function.** At the decision perch, the agent observes $(m_t, p_t)$ and chooses consumption $c_t$ to maximize:
$$V^D(m_t, p_t) = \max_{c_t \in [0, m_t]} \left\{ u(c_t \cdot p_t) + \beta \mathbb{E}[\zeta_t \cdot V^C(a_t, p_t)] \right\}$$
subject to $a_t = m_t - c_t$, where:
- $u: \mathbb{R}_+ \to \mathbb{R}$ is the period utility function (typically CRRA: $u(C) = \frac{C^{1-\rho}}{1-\rho}$ for $\rho > 0, \rho \neq 1$)
- $\beta \in (0,1)$ is the time discount factor
- Consumption in levels is $C_t = c_t \cdot p_t$
- The expectation is taken over the survival shock $\zeta_t \sim \text{Bernoulli}(\mathcal{L})$

**Continuation Value Function.** At the continuation perch, the agent has chosen assets $a_t$ and observes permanent income $p_t$. Before the survival shock realizes:
$$V^C(a_t, p_t) = V^A(k_{t+1}, p_t)$$
where $k_{t+1} = a_t$ (the twist operation).

The survival shock expectation yields:
$$\mathbb{E}[\zeta_t \cdot V^C(a_t, p_t)] = \mathcal{L} \cdot V^A(a_t, p_t) + (1-\mathcal{L}) \cdot 0 = \mathcal{L} \cdot V^A(a_t, p_t)$$

**Normalized Bellman Equation.** Combining the perches, the recursive problem can be written in normalized form. Define the normalized value function $v(m_t) \coloneqq V^D(m_t, p_t) / p_t^{1-\rho}$ (under CRRA utility). Then:
$$v(m_t) = \max_{c_t \in [0, m_t]} \left\{ u(c_t) + \beta \Gamma^{1-\rho} \mathcal{L} \cdot v(m_{t+1}) \right\}$$
where $m_{t+1} = R \cdot \frac{a_t}{\Gamma} + 1$ and the optimization is over normalized quantities.

**Information Sets.**
- Arrival perch $\mathcal{F}^A_t$: $\{k_t, p_{t-1}, \text{history up to } t-1\}$
- Decision perch $\mathcal{F}^D_t$: $\mathcal{F}^A_t \cup \{p_t, m_t\}$ (deterministic updating)
- Continuation perch $\mathcal{F}^C_t$: $\mathcal{F}^D_t \cup \{c_t, a_t\}$

## 4. First-Order Conditions

**Euler Equation.** The first-order condition for consumption $c_t$ is:
$$u'(c_t \cdot p_t) \cdot p_t = \beta \mathcal{L} \cdot \mathbb{E}_t\left[\frac{\partial V^A(a_t, p_t)}{\partial a_t}\right]$$

By the envelope theorem at the next period's arrival perch:
$$\frac{\partial V^A(k_{t+1}, p_t)}{\partial k_{t+1}} = \frac{\partial V^D(m_{t+1}, p_{t+1})}{\partial m_{t+1}} \cdot \frac{\partial m_{t+1}}{\partial k_{t+1}} = u'(c_{t+1} \cdot p_{t+1}) \cdot p_{t+1} \cdot \frac{R}{\Gamma}$$

Substituting $k_{t+1} = a_t$ and $p_{t+1} = p_t \cdot \Gamma$:
$$u'(c_t \cdot p_t) \cdot p_t = \beta \mathcal{L} \cdot R \cdot u'(c_{t+1} \cdot p_{t+1}) \cdot p_{t+1} / \Gamma$$

**Normalized Euler Equation.** Dividing through by $p_t$ and using $p_{t+1} = p_t \cdot \Gamma$:
$$u'(c_t) = \beta \mathcal{L} \cdot R \cdot \Gamma^{-\rho} \cdot u'(c_{t+1})$$

For CRRA utility $u(c) = \frac{c^{1-\rho}}{1-\rho}$, we have $u'(c) = c^{-\rho}$, so:
$$c_t^{-\rho} = \beta \mathcal{L} \cdot R \cdot \Gamma^{-\rho} \cdot c_{t+1}^{-\rho}$$

or equivalently:
$$c_{t+1} = c_t \cdot (\beta \mathcal{L} \cdot R)^{1/\rho} \cdot \Gamma^{-1}$$

**Perfect Foresight Solution.** In this perfect foresight model (no income shocks), the consumption function takes the form:
$$c_t = \chi(m_t)$$
where $\chi: \mathbb{R}_+ \to \mathbb{R}_+$ is the consumption policy function. Given the linear structure, this is typically:
$$c(m) = \kappa \cdot m$$
for some marginal propensity to consume $\kappa \in (0,1)$ determined by:
$$\kappa = \frac{1}{1 + \psi}$$
where $\psi$ satisfies:
$$\psi = \left(\frac{R \beta \mathcal{L}}{\Gamma^\rho}\right)^{1/\rho} (1 + \psi)$$

This can be solved for $\psi$ (and hence $\kappa$) given parameters.

**Envelope Condition.** The marginal value of market resources at the decision perch is:
$$\frac{\partial V^D(m_t, p_t)}{\partial m_t} = u'(c_t \cdot p_t) \cdot p_t = u'(c_t) \cdot p_t^{1-\rho} \cdot p_t^\rho = u'(c_t) \cdot p_t$$

**EGM Representation.** The Endogenous Grid Method can be applied by computing:
1. For a grid of end-of-period assets $\{a^i\}$, compute next period's resources: $m_{t+1}^i = R \cdot a^i / \Gamma + 1$
2. Evaluate next period's consumption: $c_{t+1}^i = c(m_{t+1}^i)$
3. Back out current consumption via the Euler equation: $c_t^i = [(\beta \mathcal{L} R / \Gamma^\rho) \cdot (c_{t+1}^i)^{-\rho}]^{-1/\rho}$
4. Compute current resources: $m_t^i = a^i + c_t^i$
5. Interpolate to obtain $c(m)$

## 5. Forward Operator

The forward operator describes how the distribution of agents evolves over time.

**Cross-Sectional Distribution.** Let $\Phi_t(k, p)$ denote the joint distribution of normalized capital and permanent income at the beginning of period $t$. 

**Transition Operator.** Given policy function $c(m)$, the distribution evolves as:
$$\Phi_{t+1}(k', p') = \int \mathbb{1}\{k' = a(k, p), p' = p \cdot \Gamma\} \cdot \mathcal{L} \, d\Phi_t(k, p)$$
where:
- $m = R \cdot k / \Gamma + 1$ (market resources)
- $c = c(m)$ (consumption policy)
- $a = m - c$ (end-of-period assets)

**Marginal Distributions.** The permanent income distribution evolves deterministically:
$$\Phi_{t+1}^p(p') = \Phi_t^p(p' / \Gamma)$$
since $p_{t+1} = p_t \cdot \Gamma$ with certainty (ignoring mortality exits).

The normalized capital distribution evolves according to:
$$\Phi_{t+1}^k(k') = \mathcal{L} \int \mathbb{1}\{k' = m - c(m)\} \, d\Phi_t^{k,m}(k, m)$$
where $\Phi_t^{k,m}$ is the joint distribution of $k$ and the induced $m = R k / \Gamma + 1$.

**Invariant Distribution.** A stationary distribution $\Phi^*(k, p)$ (if it exists) satisfies:
$$\Phi^*(k', p') = \int \mathbb{1}\{k' = a(k, p), p' = p \cdot \Gamma\} \cdot \mathcal{L} \, d\Phi^*(k, p)$$

However, with deterministic permanent income growth ($p_t = p_0 \cdot \Gamma^t$), the permanent income level grows without bound, so there is no invariant distribution in levels. The model is typically analyzed in normalized units or along a balanced growth path.

**Balanced Growth Path.** On a balanced growth path, the distribution of normalized variables $\Phi^*(k)$ (integrating out $p$) satisfies:
$$\Phi^*(k') = \mathcal{L} \int \mathbb{1}\{k' = a(k)\} \, d\Phi^*(k)$$
where $a(k) = m - c(m)$ with $m = R k / \Gamma + 1$.

**Mortality Replenishment.** The factor $\mathcal{L}$ represents survival. In steady state, the $(1-\mathcal{L})$ fraction who die are replaced by newborns drawn from the initial distribution $\mu_{k,0}$:
$$\Phi^*(k) = \mathcal{L} \cdot T[\Phi^*](k) + (1-\mathcal{L}) \cdot \mu_{k,
