---
slug: lawvere_theory
title: Lawvere theory
tags:
- foundations
- category-theory
description: A finite-product theory of operations and equations; its models preserve the specified products.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Lawvere theory

A **single-sorted Lawvere theory** is a small category with finite products whose objects are the finite powers of a distinguished object. A morphism from its n-fold power to that object represents an n-argument operation; equations are represented by equalities of morphisms. A model in sets is a functor that preserves these finite products.

A [[signature]] lists operation symbols and their input/output types. It can generate a free theory; imposing equations produces an equational theory. A theory therefore specifies more than an arbitrary list of typed operations. In the many-sorted version, objects are finite products of a specified family of basic [[sort|sorts]].

## Relation to Bellman operations

This provides one possible categorical account of an algebraic language. Applying it to a Bellman model requires specifying the sorts, the [[operator|operators]] and the equations and checking that the proposed interpretation preserves them. In particular, stochastic tensor operations need not be categorical products, and copying a draw differs from independent resampling.

An interpretation homomorphism from a term algebra is not itself the same object as a model functor from a Lawvere theory. The general [[initial_algebra|initial-algebra]] theorem does not establish a complete Lawvere-theory model of every retained Bellman graph. [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md#3-interpretation-and-copying) states the structures and qualifications used in the current calculus.

See [[signature]], [[initial_algebra|initial algebra]] and [[bellman_algebra|Bellman algebra]].
