---
audience: user
type: example
topic: [applications]
---
# Formal MDP: Consumption Stage (`cons_stage`)
#no-port-cons
> Source: the stage file `port-with-shocks/library/cons_stage.yaml` of the [earlier dolo-plus YAML design](../index.md); the file is no longer in the repository.

## Rosetta Stone

| DDSL abstract | This stage |
|---|---|
| Stage name | `cons_stage` |
| Arrival state $x_{\prec}$ | $m$ |
| Decision state $x$ | $m$ |
| Continuation state $x_{\succ}$ | $a$ |
| Control | $c$ |
| Exogenous shock | (none) |

## Model

A household enters the stage with cash-on-hand $m \in \mathbb{R}_{++}$ and chooses consumption $c$.  There are no shocks within this stage; any stochastic elements (income, returns) are handled by preceding stages in the period.

**State and action spaces.** The state space is $X_m \coloneqq \mathbb{R}_{++}$ and the action space is $\mathbb{R}_+$.  The feasibility correspondence is

$$
\Gamma(m) \coloneqq \{c \in \mathbb{R}_+ : 0 < c \leq m \}.
$$

**Transitions.** The arrival-to-decision transition is the identity $m_d = m$. After the consumption choice, end-of-period assets are

$$
a = m - c.
$$

**Preferences.** The per-period reward is CRRA utility $u(c) \coloneqq \frac{c^{1-\rho}}{1-\rho}$, with risk-aversion parameter $\rho > 0$, and the discount factor is $\beta \in (0,1)$.

## Bellman Equation

Since the arrival-to-decision transition is identity and there are no shocks, the arrival and decision value functions coincide.  The Bellman equation for this stage is:

$$
v(m) = \max_{c \in \Gamma(m)} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta \, v_{\succ}(m-c) \right\},
$$

where $v_{\succ} \colon \mathbb{R}_+ \to \mathbb{R}$ is the continuation value function (supplied by the next stage or the next-period arrival value through inter-stage wiring).  The optimal policy is

$$
c^*(m) \coloneqq \operatorname*{arg\,max}_{c \in \Gamma(m)} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta \, v_{\succ}(m-c) \right\}.
$$

The arrival value function is the identity:

$$
v_{\prec}(m) = v(m).
$$

**Marginal value.**  By the envelope theorem, the marginal value at the decision perch is

$$
v'(m) = \bigl(c^*(m)\bigr)^{-\rho}.
$$

Since the arrival transition is identity, $v'_{\prec}(m) = v'(m)$.

## First-Order Conditions and EGM Representation

At an interior optimum the Euler equation holds:

$$
c^{-\rho} = \beta \, v'_{\succ}(a).
$$

The endogenous grid method (EGM) exploits this by working on the continuation grid.  Given $v'_{\succ}(a)$ for each grid point $a$:

1. **Inverse Euler.**  Recover consumption on the continuation grid:

$$
\hat{c}(a) = \bigl(\beta \, v'_{\succ}(a)\bigr)^{-1/\rho}.
$$

2. **Reverse transition.**  Recover the endogenous decision-grid point:

$$
\hat{m}(a) = a + \hat{c}(a).
$$

This produces pairs $(\hat{m}(a), \hat{c}(a))$ on an endogenous grid, which are interpolated onto a regular $m$-grid to obtain $c^*(m)$.

## Forward Operator (Population Dynamics)

Given a distribution $\mu$ over arrival states $m$, the forward operator pushes $\mu$ through the optimal policy.  Since the stage is deterministic:

$$
a = m - c^*(m), \qquad m \sim \mu,
$$

and the continuation-state distribution is $\mu_{\succ} = (m \mapsto m - c^*(m))_\# \, \mu$.

## Calibration

| Symbol | Value | Description |
|---|---|---|
| $\beta$ | 0.96 | discount factor |
| $\rho$ | 2.0 | CRRA risk aversion |
