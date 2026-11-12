---
slug: forward_builder
title: forward builder
tags: []
description: Probability transport through transitions, conditional distributions and a supplied policy; paired with
  undiscounted transition expectation.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/03-Stages and perches.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Forward builder

A **forward builder** propagates a probability distribution through declared transitions and the conditional distributions of the shocks. It is the [[builder]] of a forward [block](../Bellman-Sym/01-stage.md#3-builder-blocks) of a [[stage|stage file]], reached from the [[perch]] its edge leaves: `stage.arvl.builder.fwd` from arrival and `stage.dcsn.builder.fwd` from decision, the paths that read the pairs `stage.builder["arvl", "dcsn"]` and `stage.builder["dcsn", "cntn"]` ([The builders graphs](../Bellman-Sym/API/stage/03-build.md) §2). On the decision edge it also needs a supplied feasible measurable policy. It acts on measures, rather than returning a state-transition function alone: the package states its [[operator|operators]] on finite measures, of which a probability measure is the case of mass one, as a `Pushforward` along a [[operator#Kernels|law of motion]] and a `DistributionExtension` by the distribution of a shock ([operations](../Bellman-Sym/reference/operations.md) §2).

## Decision-edge construction

Let $X$ be the decision-state space, $\Gamma(x)$ the feasible actions, $D=\{(x,a):a\in\Gamma(x)\}$, $Z$ the shock space and $Y$ the continuation-state space. Assume a measurable law of motion $g:D\times Z\to Y$, a [[operator#Kernels|conditional probability kernel]] $\kappa(d,dz)$ and a feasible measurable policy $\pi$. Write $j_\pi(x)=(x,\pi(x))$.

For a measurable map $h$, its pushforward $h_\#$ gives the distribution of $h$ applied to a draw. Let $L_\kappa$ extend a measure $\nu$ on $D$ to the joint distribution $\nu(dd)\kappa(d,dz)$. Then

$$
M_\pi=g_\#\circ L_\kappa\circ(j_\pi)_\#:
\mathsf M(X)\to\mathsf M(Y),
$$

where $\mathsf M(S)$ is the set of finite measures on a measurable space $S$. The operator $M_\pi$ preserves mass, so it sends probability measures to probability measures. The construction uses a conditional joint distribution. A product of state and shock marginals is justified only by the declared independence assumptions. Transition guards must hold under the joint distribution; dropping infeasible probability mass would change the model. If a policy is only an implicit relation, the construction needs a valid selected policy: the decision push-forward is the operator at that policy, one operator for each policy, and reads the policy on no [[semgraph|wire]].

## Transition pairing

The corresponding undiscounted transition expectation is

$$
(P_\pi f)(x)=\int f(g(x,\pi(x),z))\,\kappa((x,\pi(x)),dz).
$$

For bounded measurable $f$, or when the required integrals are absolutely finite,

$$
\int f\,d(M_\pi\mu)=\int P_\pi f\,d\mu.
$$

This identity follows by evaluating the same transition conditionally on the source state and then integrating its distribution. It does not pair probability transport with the entire [[backward_builder|backward builder]]: rewards, discounting, nonlinear aggregation and optimization are separate operations.

The arrival builder has the corresponding law of motion and distribution extension and is stated at no policy, no choice being made there. At stage level, forward propagation composes arrival then decision transition, $\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec$. The paired expectations compose in reverse order. For a deterministic transition with no shock, the distribution extension is the identity.

## State sufficiency

A state representation must retain the information needed for the conditional distributions and the policy problem. Measurability of a trajectory at a perch does not prove that an arbitrarily chosen state suffices. Conditional-expectation projection of a history-dependent policy is not a general optimality-preserving construction.

See [Stages and perches](../bellman-calculus/03-Stages%20and%20perches.md#27-the-forward-builders), [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md#4-transition-pairing) and [[methodization]]. A numerical simulation or distribution approximation must support the declared transition and policy.
