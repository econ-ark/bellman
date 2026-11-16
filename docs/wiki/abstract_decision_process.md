---
slug: abstract_decision_process
title: Abstract dynamic program (ADP)
tags:
- dp
- sargent-stachurski
- foundations
description: A partially ordered value space and monotone policy maps; Bellman suprema and optimality require
  additional assumptions.
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
- reference: "Sargent, T. J. and Stachurski, J. (2026). Dynamic Programming, Volume II: General States. Edition of 10 April 2026. Definition 2.1.1, §2.1.1, Theorem 2.1.7 and Corollary 2.1.8, pp. 66–67."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Abstract dynamic program (ADP)

An **abstract dynamic program** (ADP), in Sargent and Stachurski's terminology, was previously called an abstract decision process in this wiki. An ADP specifies a partially ordered value space and a family of policy evaluation maps; it does not require a particular state representation or source language.

## Definition

Let $V$ be a partially ordered set and $\{T_\sigma:\sigma\in\Sigma\}$ a nonempty family of order-preserving self-maps on $V$. The index $\sigma$ names a policy. When each $T_\sigma$ has a unique fixed point $v_\sigma$, that point is its policy value. The optimal value is $\sup_\sigma v_\sigma$ when this supremum exists in the specified value space.

The associated [[bellman_operator|Bellman operator]] is

$$
Tv=\sup_{\sigma\in\Sigma}T_\sigma v,
$$

where the supremum must exist in $V$. An arbitrary partially ordered set does not ensure this. A policy is **greedy for $v$** when its update attains that supremum; existence of the supremum does not imply existence of a greedy policy.

Sargent and Stachurski's fixed-point-to-optimality result assumes well-posed policy maps, a fixed point $\bar v$ of $T$, a $\bar v$-greedy policy, and the implication $T_\sigma v\leq v\Rightarrow v_\sigma\leq v$. These assumptions connect the operator equation to optimal policy values. They are not consequences of declaring an ADP.

## Relation to staged models

The [[recursive_decision_process|recursive decision process (RDP)]] adds feasible actions and a choice-value aggregator that constructs the policy maps. A stationary composition of [[stage|stages]] can define an ADP when it preserves a specified value space and order. An individual stage may instead map between the value spaces of different [[perch|perches]], and a finite-horizon problem requires terminal data rather than a stationary fixed point.

When a period also sends constants backward, its operator acts on the tuple of representing functions of all backward fields. A stationary fixed point requires each component to be fixed. A finite-horizon model instead follows the iterates from the user's terminal data wherever each composition is defined; a periodic model requires a cycle of the complete tuple. These interpretations do not by themselves provide the order or optimality hypotheses of an ADP. [Periods and trellis](../bellman-calculus/08-periods-and-trellis.md) states the construction.

Value-function iteration applies $T$ repeatedly. Policy iteration alternates policy evaluation and greedy policy selection. Their convergence requires additional assumptions; assigning a numerical method does not establish them. [[semiconjugacy|semiconjugacy (strong / order)]] describes specified relations between alternative [[operator]] forms.

**Reference:** Sargent and Stachurski, *Dynamic Programming, Volume II: General States*, 10 April 2026 edition, Definition 2.1.1, §2.1.1, and Theorem 2.1.7 and Corollary 2.1.8, pp. 66–67.
