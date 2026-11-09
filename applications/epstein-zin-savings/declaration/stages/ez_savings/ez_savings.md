---
title: "Epstein–Zin savings"
audience: developer
type: model-note
topic: [applications]
---
# Epstein–Zin savings

A consumption–savings stage with Epstein–Zin preferences, written on 12 September 2026 as the stage that exercises the general form of the backward builder: one pointwise map inside the shock integral and another outside it (Stages and perches §2.3a; AMD-SG-005 §1, acceptance item 3). It is a test of the construction, not a calibrated application, and no calibration file accompanies it. The methods file `methods.bl` beside the stage file, an addition to it, selects value function iteration on the decision value builder, Gauss–Hermite quadrature at the expectation over the return, the representations of the value, of its derivative and of the policy, and Monte Carlo draws for the forward builder; `declaration/settings/ez_savings.yml` gives the values of the settings it declares.

## Model

The household enters the decision perch with resources $m_d$ and chooses consumption $c \in (0, m_d]$, open at zero since the control is declared strictly positive; the grammar has no open-open correspondence body, so the upper endpoint, at which saving is zero, stays in the written set although $a$ is declared strictly positive. Savings $m_d - c$ earn a gross return $\Psi \sim \mathrm{LogNormal}(\mu_\Psi, \sigma_\Psi)$ drawn after the decision, so the continuation state is $a = (m_d - c)\,\Psi$. The stage has no arrival perch: it is entered at its decision perch, whose resources $m_d$ the forward block's header types, and the next period's resources are the continuation state of this one.

## Bellman equation

$$
V(m_d) = \sup_{c \in (0, m_d]} \Bigl( (1-\beta)\, c^{1-\rho} + \beta \bigl( \mathbb E_\Psi \bigl[ V_\succ(a)^{1-\gamma} \bigr] \bigr)^{\frac{1-\rho}{1-\gamma}} \Bigr)^{\frac{1}{1-\rho}},
\qquad a = (m_d - c)\,\Psi .
$$

In the terms of the backward builder the inside map is $v \mapsto v^{1-\gamma}$, the outside map is $(w, c) \mapsto \bigl((1-\beta)\,c^{1-\rho} + \beta\,w^{(1-\rho)/(1-\gamma)}\bigr)^{1/(1-\rho)}$, and neither is affine, so the `affine` query answers no for both aggregation boxes and the two placements of the maps denote different operators. The policy block states the choice as the maximizer of the same objective; the stage file writes no first-order condition and no marginal value, and the methods file selects value function iteration for the stage, not the endogenous grid method, while appending the envelope condition of the decision value as a stated derivative.

## What the stage tests

At the primitive grain of the backward view, `cntn_to_dcsn` renders substitution, aggregation inside, expectation over $\Psi$, aggregation outside and evaluation at the policy, five operators; the build before AMD-SG-005 renders four, carrying the inside arithmetic in the expectation box. The stage has no arrival block, so its backward view holds the decision and policy builders alone.
