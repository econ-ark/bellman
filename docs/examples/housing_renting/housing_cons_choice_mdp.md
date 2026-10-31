---
audience: user
type: example
topic: [applications]
---
# Formal MDP: Consumption Choice Stage (`OwnerConsumptionChoice`)

> Source: the stage file `housing_owner_only_doloplus/stages/consumption_choice.yaml` of the [earlier dolo-plus YAML design](../index.md); the file is no longer in the repository.

## Rosetta Stone

| DDSL abstract | This stage |
|---|---|
| Stage name | `OwnerConsumptionChoice` |
| Arrival state $x_{\prec}$ | $(w, H', y)$ |
| Decision state $x$ | $(w, H', y)$ |
| Continuation state $x_{\succ}$ | $(a, H', y)$ |
| Control | $c$ |
| Exogenous shock | (none) |

## Model

This is the second stage in a two-stage housing period.  The agent enters with cash-on-hand $w \in \mathbb{R}_+$, a housing stock $H' \in \mathcal{H}$ that was already chosen in the preceding housing stage, and the realized income index $y$.  The agent chooses consumption $c$.

**State and action spaces.**  The state at each perch is a triple $(w, H', y) \in \mathbb{R}_+ \times \mathcal{H} \times \mathcal{Y}$, where $\mathcal{H} \coloneqq \text{linspace}(H_\text{min}, H_\text{max}, n_H)$ is the discrete housing grid and $\mathcal{Y} \coloneqq \{1, \ldots, n_y\}$ is the income-state space.  The action space is $\mathbb{R}_+$ and the feasibility correspondence is

$$
\Gamma(w) \coloneqq \{c \in \mathbb{R}_+ : 0 < c \leq w\}.
$$

**No shocks.**  There are no exogenous shocks in this stage; the arrival-to-decision transition is identity.

**Transitions.**  The decision-to-continuation transition is

$$
a = w - c,
$$

with $H'$ and $y$ carried through unchanged.

**Preferences.**  The per-period reward is Cobb--Douglas utility in consumption and housing services:

$$
u(c, H') \coloneqq \frac{\bigl(c^\theta \, (\kappa\, H' + \iota)^{1-\theta}\bigr)^{1-\gamma}}{1-\gamma},
$$

where $\theta \in (0,1)$ is the consumption weight, $\kappa > 0$ scales housing services, $\iota > 0$ ensures positive housing services at $H' = 0$, and $\gamma > 0$ is the CRRA coefficient.  The discount factor is $\beta \in (0,1)$.

## Bellman Equation

Since the arrival-to-decision transition is identity and there are no shocks, the arrival and decision value functions coincide.  The Bellman equation is:

$$
v(w, H', y) = \max_{c \in \Gamma(w)} \left\{ \frac{\bigl(c^\theta\,(\kappa\,H' + \iota)^{1-\theta}\bigr)^{1-\gamma}}{1-\gamma} + \beta\, v_{\succ}(w - c,\, H',\, y) \right\},
$$

subject to $0 < c \leq w$.  The optimal policy is $c^*(w, H', y) \coloneqq \operatorname*{arg\,max}_{c \in \Gamma(w)} \{ \cdots \}$.  The arrival value function is the identity:

$$
v_{\prec}(w, H', y) = v(w, H', y).
$$

## First-Order Conditions and EGM Representation

At an interior optimum the Euler equation holds:

$$
\theta\, c^{\,\theta(1-\gamma)-1}\, (\kappa\, H' + \iota)^{(1-\theta)(1-\gamma)} = \beta\, v'_{\succ}(a, H', y).
$$

The EGM exploits this by working on the continuation grid.  Given $v'_{\succ}(a, H', y)$ for each grid point $a$ and each discrete pair $(H', y)$:

1. **Inverse Euler.**  Recover consumption on the continuation grid:

$$
\hat{c}(a, H', y) = \left(\frac{\beta\, v'_{\succ}(a, H', y)}{\theta\, (\kappa\, H' + \iota)^{(1-\theta)(1-\gamma)}}\right)^{-1/(\theta(1-\gamma) + \gamma - 1)}.
$$

2. **Reverse transition.**  Recover the endogenous decision-grid point:

$$
\hat{w}(a, H', y) = a + \hat{c}(a, H', y).
$$

This produces pairs $(\hat{w}(a), \hat{c}(a))$ for each $(H', y)$ on an endogenous grid.  A FUES-style upper-envelope step is applied before interpolating onto a regular $w$-grid.

**Shadow value.**  After obtaining the policy, the marginal value on the continuation grid is

$$
v'_{\succ}(a, H', y) = \theta\, \hat{c}(a, H', y)^{\,\theta(1-\gamma)-1}\, (\kappa\, H' + \iota)^{(1-\theta)(1-\gamma)}.
$$

## Forward Operator (Population Dynamics)

Given a distribution $\mu$ over $(w, H', y)$, the stage is deterministic, so the forward operator is the push-forward through the optimal policy:

$$
a = w - c^*(w, H', y), \qquad (w, H', y) \sim \mu,
$$

and $\mu_{\succ}(A \times \{H\} \times \{y\}) = \mu\!\bigl(\{w : w - c^*(w, H, y) \in A\} \times \{H\} \times \{y\}\bigr)$.

## Calibration

| Symbol | Value | Description |
|---|---|---|
| $\beta$ | 0.93 | discount factor |
| $\gamma$ | 2.0 | CRRA risk aversion |
| $\theta$ | 0.77 | consumption weight in utility |
| $\kappa$ | 0.075 | housing service scaling |
| $\iota$ | 0.01 | housing service constant |
| $n_H$ | 7 | housing grid points |
| $H_\text{min}$ | 0.0 | housing grid lower bound |
| $H_\text{max}$ | 5.0 | housing grid upper bound |
| $r$ | 0.06 | interest rate |
