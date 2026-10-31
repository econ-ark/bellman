---
audience: user
type: example
topic: [applications]
---
# Formal MDP: Consumption--Savings with IID Income (`consumption_savings_iid_egm_doloplus`)

> Source: the stage file `consumption_savings_iid_egm_doloplus/stage.yaml` of the [earlier dolo-plus YAML design](../index.md); the file is no longer in the repository.

## Rosetta Stone

| DDSL abstract | This stage |
|---|---|
| Stage name | `consumption_savings_iid_egm_doloplus` |
| Arrival state $x_{\prec}$ | $b$ |
| Decision state $x$ | $w$ |
| Continuation state $x_{\succ}$ | $a$ |
| Control | $c$ |
| Exogenous shock | $y$ (pre-decision, IID) |

## Model

The agent enters with assets $b \in \mathbb{R}_+$, observes an IID income shock $y$, and chooses consumption $c$.

**State and action spaces.**  The arrival state space is $X_b \coloneqq \mathbb{R}_+$, the decision state space is $X_w \coloneqq \mathbb{R}_+$, the continuation state space is $X_a \coloneqq \mathbb{R}_+$, and the action space is $\mathbb{R}_+$.  The feasibility correspondence is

$$
\Gamma(w) \coloneqq \{c \in \mathbb{R}_+ : 0 < c \leq w\}.
$$

**Shock process.**  An IID log-income shock $y$ is drawn between arrival and decision:

$$
y \sim \mathcal{N}(\mu_y, \sigma_y).
$$

At the arrival perch the agent knows only $b$; at the decision perch the agent knows $(b, y)$ and hence $w$.  This is the canonical "expectation-outside-the-max" timing.

**Transitions.**  The arrival-to-decision transition maps the pre-decision state and shock to cash-on-hand:

$$
w = e^y + b\,r,
$$

where $r > 0$ is the gross interest rate.  The decision-to-continuation transition is

$$
a = w - c.
$$

**Preferences.**  The per-period reward is CRRA utility $u(c) \coloneqq \frac{c^{1-\gamma}}{1-\gamma}$ with $\gamma > 0$, and the discount factor is $\beta \in (0,1)$.

## Bellman Equation

The Bellman equation decomposes into two sub-problems, one at each builder.

**Decision value.**  Conditional on having observed $(b,y)$ and hence knowing $w = e^y + b\,r$, the agent solves

$$
v(w) = \max_{c \in \Gamma(w)} \left\{ \frac{c^{1-\gamma}}{1-\gamma} + \beta \, v_{\succ}(w - c) \right\},
$$

where $v_{\succ} \colon \mathbb{R}_+ \to \mathbb{R}$ is the continuation value function.  The optimal policy is $c^*(w) \coloneqq \operatorname*{arg\,max}_{c \in \Gamma(w)} \{ \cdots \}$.

**Arrival value.**  Before the shock is observed, the arrival value is an expectation:

$$
v_{\prec}(b) = \mathbb{E}_y \bigl[ v(e^y + b\,r) \bigr] = \int v(e^y + b\,r)\,\phi(y)\,\mathrm{d}y,
$$

where $\phi$ is the density of $\mathcal{N}(\mu_y, \sigma_y)$.

**Marginal values.**  By the envelope theorem,

$$
v'(w) = \bigl(c^*(w)\bigr)^{-\gamma}.
$$

At the arrival perch, $v'_{\prec}(b) = r \cdot \mathbb{E}_y\bigl[v'(e^y + b\,r)\bigr]$, where the factor $r = \partial w / \partial b$.

## First-Order Conditions and EGM Representation

At an interior optimum the Euler equation holds:

$$
c^{-\gamma} = \beta \, v'_{\succ}(a).
$$

The EGM exploits this by working on the continuation grid.  Given $v'_{\succ}(a)$ for each grid point $a$:

1. **Inverse Euler.**  Recover consumption on the continuation grid:

$$
\hat{c}(a) = \bigl(\beta \, v'_{\succ}(a)\bigr)^{-1/\gamma}.
$$

2. **Reverse transition.**  Recover the endogenous decision-grid point:

$$
\hat{w}(a) = a + \hat{c}(a).
$$

This produces pairs $(\hat{w}(a), \hat{c}(a))$ on an endogenous grid, which are interpolated onto a regular $w$-grid.

## Forward Operator (Population Dynamics)

Given a distribution $\mu_{\prec}$ over arrival states $b$, the forward operator acts in two steps.

1. **Shock realization.** Draw $y \sim \mathcal{N}(\mu_y, \sigma_y)$ and form $w = e^y + b\,r$.  The decision-state distribution is

$$
\mu(A) = \int \Pr(e^y + b\,r \in A)\,\mathrm{d}\mu_{\prec}(b).
$$

2. **Optimal savings.** Apply the policy $a = w - c^*(w)$ to push $\mu$ forward:

$$
\mu_{\succ} = (w \mapsto w - c^*(w))_\# \, \mu.
$$

## Calibration

| Symbol | Value | Description |
|---|---|---|
| $\beta$ | 0.96 | discount factor |
| $\gamma$ | 4.0 | CRRA risk aversion |
| $r$ | 1.00 | gross interest rate |
| $\mu_y$ | 0.0 | mean of log income |
| $\sigma_y$ | 0.1 | std of log income |
