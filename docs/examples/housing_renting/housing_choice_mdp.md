---
audience: user
type: example
topic: [applications]
---
# Formal MDP: Housing Choice Stage (`OwnerHousingChoice`)

> Source: the stage file `housing_owner_only_doloplus/stages/housing_choice.yaml` of the [earlier dolo-plus YAML design](../index.md); the file is no longer in the repository.

## Rosetta Stone

| DDSL abstract | This stage |
|---|---|
| Stage name | `OwnerHousingChoice` |
| Arrival state $x_{\prec}$ | $(b, H, y_\text{pre})$ |
| Decision state $x$ | $(w, H, y)$ |
| Continuation state $x_{\succ}$ | $(w', H', y)$ |
| Control | $H_\text{choice} \in \mathcal{H}$ (discrete) |
| Exogenous shock | $y$ (discrete Markov, pre-decision) |

## Model

This is the first stage in a two-stage housing period.  An agent enters with assets $b \in \mathbb{R}_+$, housing stock $H \in \mathcal{H}$, and previous income index $y_\text{pre}$.  An income shock is realized, and the agent then chooses a new housing stock from a finite set.

**State and action spaces.**  We collect the states at each perch as follows.  The arrival state is

$$
x_{\prec} \coloneqq (b,\, H,\, y_\text{pre}) \in \mathbb{R}_+ \times \mathcal{H} \times \mathcal{Y},
$$

the decision state is $(w, H, y) \in \mathbb{R}_+ \times \mathcal{H} \times \mathcal{Y}$, and the continuation state is $(w', H', y) \in \mathbb{R}_+ \times \mathcal{H} \times \mathcal{Y}$.  The housing grid $\mathcal{H} \coloneqq \{H_1, \ldots, H_{n_H}\} = \text{linspace}(H_\text{min}, H_\text{max}, n_H)$ is a discrete mathematical space whose constructor arguments $(n_H, H_\text{min}, H_\text{max})$ are parameters of the model.  The income-state space is $\mathcal{Y} \coloneqq \{1, \ldots, n_y\}$.  The action set is $\mathcal{H}$ (discrete).

**Shock process.**  A discrete Markov income shock is realized between arrival and decision.  Let $\Pi$ denote the transition matrix and $z_\text{vals}$ the vector of income-state values.  Conditional on $y_\text{pre}$, the new income index $y$ is drawn from $\Pi(y_\text{pre}, \cdot)$.

**Transitions.**  The arrival-to-decision transition incorporates the shock realization:

$$
w = (1+r)\,b + z_\text{vals}(y).
$$

After observing $(w, H, y)$, the agent chooses a new housing stock $H_\text{choice} \in \mathcal{H}$.  The decision-to-continuation transition is

$$
w' = w + H - \bigl(1 + \phi \cdot \mathbf{1}\{H_\text{choice} \neq H\}\bigr)\,H_\text{choice},
\qquad
H' = H_\text{choice},
$$

where $\phi > 0$ is a proportional transaction cost incurred whenever the agent adjusts housing.

**Feasibility.**  The feasible set is

$$
\Gamma(w, H) \coloneqq \bigl\{ H_\text{choice} \in \mathcal{H} : w + H - (1 + \phi \cdot \mathbf{1}\{H_\text{choice} \neq H\})\,H_\text{choice} \geq 0 \bigr\}.
$$

## Bellman Equation

The Bellman equation decomposes into two sub-problems.

**Decision value (discrete max).**  Conditional on $(w, H, y)$, the agent maximizes over the finite housing set:

$$
v(w, H, y) = \max_{H_\text{choice} \in \Gamma(w, H)} \; v_{\succ}\!\bigl(w + H - (1 + \phi \cdot \mathbf{1}\{H_\text{choice} \neq H\})\,H_\text{choice},\; H_\text{choice},\; y\bigr).
$$

The optimal housing choice is $H^*(w, H, y) \coloneqq \operatorname*{arg\,max}_{H_\text{choice} \in \Gamma(w,H)} \{ \cdots \}$.

The shadow value passes through the discrete envelope:

$$
v'(w, H, y) = v'_{\succ}(w'^*,\, H^*,\, y),
$$

where $w'^*$ is the optimal continuation-state cash-on-hand.

**Arrival value (conditional expectation).**  Before the income shock is observed, the arrival value integrates over the Markov transition:

$$
v_{\prec}(b, H, y_\text{pre}) = \sum_{y \in \mathcal{Y}} \Pi(y_\text{pre}, y) \; v\!\bigl((1+r)\,b + z_\text{vals}(y),\; H,\; y\bigr).
$$

Similarly, $v'_{\prec}(b, H, y_\text{pre}) = \sum_y \Pi(y_\text{pre}, y) \; v'\bigl((1+r)\,b + z_\text{vals}(y),\, H,\, y\bigr)$.

## First-Order Conditions

Not applicable.  The optimization is a discrete choice (enumeration over the finite set $\mathcal{H}$).

## Forward Operator (Population Dynamics)

Given a distribution $\mu$ over $(b, H, y_\text{pre})$, the forward operator acts in two steps.

1. **Income shock.** Draw $y \sim \Pi(y_\text{pre}, \cdot)$ and form $w = (1+r)\,b + z_\text{vals}(y)$.

2. **Housing choice.** Apply $H^*(w, H, y)$ to obtain $(w', H', y)$ and push the distribution forward.

## Calibration

| Symbol | Value | Description |
|---|---|---|
| $r$ | 0.06 | interest rate |
| $\phi$ | 0.07 | proportional housing transaction cost |
| $n_H$ | 7 | housing grid points |
| $H_\text{min}$ | 0.0 | housing grid lower bound |
| $H_\text{max}$ | 5.0 | housing grid upper bound |
| $\Pi$ | (external) | $49 \times 49$ Markov transition matrix |
| $z_\text{vals}$ | (external) | 49-state income grid |
