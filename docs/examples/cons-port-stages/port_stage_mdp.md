---
audience: user
type: example
topic: [applications]
---
# Formal MDP: Portfolio Stage (`port_stage`)
#no-port-cons
> Source: the stage file `port-with-shocks/library/port_stage.yaml` of the [earlier dolo-plus YAML design](../index.md); the file is no longer in the repository.

## Rosetta Stone

| DDSL abstract | This stage |
|---|---|
| Stage name | `port_stage` |
| Arrival state $x_{\prec}$ | $k$ |
| Decision state $x$ | $k$ |
| Continuation state $x_{\succ}$ | $m$ |
| Control | $\varsigma$ |
| Exogenous shocks | $\Psi, \theta$ (post-decision) |

## Model

A household enters the stage with investable assets $k \in \mathbb{R}_{++}$ and chooses a risky portfolio share $\varsigma \in [0,1]$.  After the portfolio decision, a joint shock vector $\zeta \coloneqq (\Psi, \theta)$ is realized, determining the continuation state.

**State and action spaces.**  The state space is $X_k \coloneqq \mathbb{R}_{++}$ and the action space is $\Pi \coloneqq [0,1]$.  The feasibility correspondence is $\Gamma(k) = [0,1]$ for all $k$.

**Shock process.**  The shocks are realized *after* the portfolio decision (post-decision timing):

$$
\Psi \sim \text{LogNormal}(\mu_\Psi, \sigma_\Psi), \qquad
\theta \sim \text{LogNormal}(\mu_\theta, \sigma_\theta).
$$

A correlation parameter $\rho_\zeta$ is declared but not yet wired.

**Transitions.**  The arrival-to-decision transition is the identity $k_d = k$.  After the decision and shock realization, cash-on-hand is

$$
m = k \bigl(\varsigma \, \Psi + (1-\varsigma)\, R\bigr) + \theta,
$$

where $R > 0$ is the gross risk-free return.

## Bellman Equation

This stage has a "max-over-expectation" structure: the agent chooses $\varsigma$ before the shocks are realized, so the expectation is inside the max.  The arrival-to-decision transition is identity, so the Bellman equation is:

$$
v(k) = \max_{\varsigma \in [0,1]} \; \mathbb{E}_{\Psi,\theta} \Bigl[ v_{\succ}\!\bigl(k(\varsigma \Psi + (1-\varsigma)R) + \theta\bigr) \Bigr],
$$

where $v_{\succ} \colon \mathbb{R}_{++} \to \mathbb{R}$ is the continuation value function.  The optimal risky share is

$$
\varsigma^*(k) \coloneqq \operatorname*{arg\,max}_{\varsigma \in [0,1]} \; \mathbb{E}_{\Psi,\theta} \Bigl[ v_{\succ}\!\bigl(k(\varsigma \Psi + (1-\varsigma)R) + \theta\bigr) \Bigr].
$$

The arrival value function is the identity: $v_{\prec}(k) = v(k)$.

## First-Order Conditions

At an interior solution $\varsigma^* \in (0,1)$, the first-order condition is

$$
\mathbb{E}_{\Psi,\theta} \Bigl[ v'_{\succ}(m) \cdot k\,(\Psi - R) \Bigr] = 0,
$$

where $m = k(\varsigma^* \Psi + (1-\varsigma^*)R) + \theta$.  This is a nonlinear equation in $\varsigma$ that typically requires numerical root-finding for each $k$.

## Forward Operator (Population Dynamics)

Given a distribution $\mu$ over arrival states $k$, the forward operator pushes $\mu$ through the optimal policy and shock realization:

$$
m = k\bigl(\varsigma^*(k)\,\Psi + (1-\varsigma^*(k))\,R\bigr) + \theta,
\qquad k \sim \mu, \quad (\Psi,\theta) \text{ drawn independently}.
$$

The continuation-state distribution is

$$
\mu_{\succ}(A) = \int \Pr\!\bigl(k(\varsigma^*(k)\Psi + (1-\varsigma^*(k))R) + \theta \in A\bigr)\, \mathrm{d}\mu(k).
$$

## Calibration

| Symbol | Value | Description |
|---|---|---|
| $R$ | 1.02 | gross risk-free return |
| $\mu_\Psi$ | 0.04 | log-mean of risky return |
| $\sigma_\Psi$ | 0.15 | log-std of risky return |
| $\mu_\theta$ | 0.0 | log-mean of transitory income |
| $\sigma_\theta$ | 0.1 | log-std of transitory income |
| $\rho_\zeta$ | 0.0 | shock correlation (placeholder) |
