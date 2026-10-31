---
slug: bellman_operator
title: Bellman operator
tags: []
description: An optimizing continuation-value update, distinguished from fixed-policy evaluation and finite-horizon
  recursion.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/05-Operators and builders.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Bellman operator

A **Bellman operator** is an [[operator]] that updates a continuation value by evaluating current rewards and future consequences and optimizing over feasible actions. A **fixed-policy operator** performs the value update under a supplied policy. These are different maps even when they share transitions and rewards.

For state $x$, feasible actions $\Gamma(x)$ and choice-value aggregator $B$, the optimizing update is

$$
(Tv)(x)=\sup_{a\in\Gamma(x)}B(x,a,v).
$$

Its domain is a chosen class of continuation functions for which the required choice values and supremum are defined and the output belongs to the declared value space. An attained maximum and a measurable maximizing policy require additional assumptions. For a feasible measurable policy $\pi$, fixed-policy evaluation is $(T_\pi v)(x)=B(x,\pi(x),v)$.

## Stage factorization

In the staged reading, write $\mathbb T_\succ$ for optimizing continuation-to-decision evaluation and $\mathbb T_\prec$ for decision-to-arrival aggregation; in a [[stage]] these are the decision and the arrival [[builder|builders]]. Then

$$
\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ,
\qquad
\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi}.
$$

The arrival operation integrates information revealed before the decision; the decision operation retains the choice and subsequent uncertainty in the declared order. Each map must have compatible input and output spaces. The entry [[backward_builder|backward builder]] defines the factors, including the distinction between constructing a choice value and selecting a policy.

A stationary Bellman operator may be a self-map whose fixed point characterizes optimal value under a verification theorem. A finite-horizon recursion can map between different time-indexed spaces and starts from specified terminal data. Neither a unique fixed point nor a convergence theorem follows from a typed stage declaration.

See [[abstract_decision_process|abstract dynamic program (ADP)]] for the supremum over policy operators, [[banach_contraction|Banach contraction theorem]] and [[blackwell_conditions|Blackwell's sufficient conditions]] for conditional convergence results, and [Operators and builders](../bellman-calculus/05-Operators%20and%20builders.md) for the detailed stage interpretation.
