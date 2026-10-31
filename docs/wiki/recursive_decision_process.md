---
slug: recursive_decision_process
title: recursive decision process (RDP)
tags:
- dp
- sargent-stachurski
- foundations
description: Feasible actions, a value-function class and an aggregator determine policy updates under monotonicity
  and closure assumptions.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
merged_from:
- recursive_dynamic_programming_problem
sources:
- path: docs/bellman-calculus/05-Operators and builders.md
  class: canonical
  date: '2026-09-07'
- reference: "Sargent, T. J. and Stachurski, J. (2026). Dynamic Programming, Volume II: General States. Edition of 10 April 2026. Chapter 7, §7.1.1.1, pp. 206–207."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Recursive decision process (RDP)

A **recursive decision process** constructs policy evaluation maps from feasible actions and a choice-value aggregator. It refines the [[abstract_decision_process|abstract dynamic program (ADP)]] by specifying how the current state, current action and continuation value determine an update.

## Primitive data

Let $X$ and $A$ be measurable state and action spaces. A feasibility correspondence $\Gamma$ assigns a nonempty set $\Gamma(x)\subseteq A$ to each state. Its graph is $D=\{(x,a):a\in\Gamma(x)\}$. Let $\Pi$ be the feasible measurable policies and $V$ a specified class of real-valued functions on $X$.

An aggregator $B:D\times V\to\mathbb R$ supplies the choice value. It is monotone in its continuation argument, and each induced policy update must remain in $V$:

$$
(T_\pi v)(x)=B(x,\pi(x),v),\qquad T_\pi v\in V.
$$

A nonempty feasible set at every state alone does not establish a measurable policy. The associated policy family must meet the hypotheses of the ADP construction. Its Bellman supremum is defined only where that supremum exists in the chosen space. Replacing it by an attained maximum over actions additionally requires the relevant feasibility and measurable-selection conditions.

For additive expected utility, a common aggregator is

$$
B(x,a,v)=r(x,a)+\beta\int v(g(x,a,z))\,\kappa(x,a,dz),
$$

where $r$ is current reward, $g$ the [[operator#Kernels|law of motion]], $\kappa$ the conditional distribution of the shock and $\beta$ a discount factor. The integral must be defined on every required feasible pair. More general recursive preferences specify their own order of expectation and aggregation; they need not have this form.

## Relation to Bellman-SYM

A model written in [[sym|Bellman-SYM]] declares, [[stage]] by stage, feasible controls, transitions, [[operator#Kernels|shock probability distributions]] and value equations. Through the [[backward_builder|backward builders]] of each stage these can determine an RDP-like aggregator under the required domains and closure conditions. This is a mathematical comparison, not a one-for-one correspondence with source keys: a stage's continuation and decision value spaces can differ. See [Operators and builders](../bellman-calculus/05-Operators%20and%20builders.md).

The Coleman–Reffett [[operator]] updates consumption policies through an Euler equation, while the [[bellman_operator|Bellman operator]] updates value functions. A correspondence between them requires specified value and policy classes, a valid transformation and its inverse, and the operator identity. EGM uses additional differentiability, feasibility and inversion conditions. It is not available merely because a problem is an RDP. See [[semiconjugacy|semiconjugacy (strong / order)]] and [[methodization]].

**Reference:** Sargent and Stachurski, *Dynamic Programming, Volume II: General States*, recursive decision process definition and the construction of policy operators from an aggregator.
