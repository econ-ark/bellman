---
title: Bellman calculus
slug: bellman_calculus
description: Mathematical definitions and composition of staged Bellman problems.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- docs/bellman-calculus/index.md
- docs/bellman-calculus/03-Stages and perches.md
- docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
tags:
- bellman-calculus
- foundations
- bellman-core
audience: user
type: concept
---

# Bellman calculus

The **Bellman calculus** describes how the equations of a dynamic decision problem define mathematical operations and how those operations compose. A [[stage]] records transitions, value calculations, and policy relations at three [[perch|information sets]]. Compatible stages form [[period|periods]], and a [[trellis]] is a diagram of periods joined by connections.

## The objects being related

A [[field]] is a quantity interpreted in its declared information context. A **state vector** is a chosen collection of coordinates that may summarize that information. Representing a field by a function of those coordinates requires a sufficiency assumption; a type declaration does not prove it. [[field|The entry on fields]] distinguishes these descriptions.

A [[backward_builder|backward builder]] constructs values from continuation values. A [[forward_builder|forward builder]] constructs a distribution of later states from a distribution of earlier states under a policy. Both are [[builder|builders]], the operators the [blocks](../Bellman-Sym/01-stage.md#3-builder-blocks) of a stage denote. Their relationship depends on the transition, the conditional distribution of the shocks, and the reward structure. In particular, the distribution transition is dual to the reward-free expectation [[operator]], not to the whole reward-bearing [[bellman_operator|Bellman operator]].

## Composition and its limits

Compatible [[connector|connectors]], which identify the fields of adjoining stages, allow the operations of those stages to compose. Associativity permits regrouping an unchanged composition. It does not permit arbitrary changes in the order of decisions, observations, or expectations.

[[initial_algebra|Initial-algebra semantics]] explains the unique extension of a fixed interpretation of syntax constructors. It does not establish that this interpretation describes the intended economy, that numerical approximations are exact, or that an infinite-horizon fixed point exists. Those are separate questions of [[adequacy]], economic assumptions, and fixed-point theory.

Use the [mathematical chapters](../bellman-calculus/index.md) for these definitions and their qualifications. Use [[sym|Bellman-SYM]] for the modeler's syntax and workflow. [Υ](upsilon.md) denotes a meaning construction within this account; it is not another name for the entire calculus.
