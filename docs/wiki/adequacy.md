---
slug: adequacy
title: adequacy
tags:
- semantics
- methodization
- bellman-calculus
description: Exact mathematical agreement, numerical approximation and implementation error are separate obligations.
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

# Adequacy

For this project, **exact agreement** means that an implementation computes the declared mathematical operation on specified inputs and observables. An approximate method instead needs a stated error or convergence result. [[initial_algebra|Initiality]] determines how assigned operations compose; it proves neither kind of numerical claim.

## Two comparisons

Distinguish the exact mathematical target, a reference numerical approximation, and the package routine intended to compute that approximation. The reference approximation is defined by its method, representations and [[settings]] independently of one package implementation.

First compare the reference approximation with the target. State their domains and any maps between numerical arrays and mathematical functions, then specify the error criterion or limiting approximation family. A quadrature rule can be exact on a restricted function class while approximating a larger class. Its convergence depends on that class and the approximation assumptions.

Second compare the package computation with the reference approximation. Floating-point error and implementation error belong to this comparison; agreement to a tolerance is not exact equality. Both comparisons matter even when the same numerical routine performs several operations together.

## Composition and iteration

Exact agreement at compatible operation boundaries yields agreement of their composites. For approximate operations, composing individual approximations requires suitable stability or continuity estimates. Convergence of values need not imply convergence of selected policies, particularly at ties.

To study repeated Bellman updates, use a theorem suited to the declared value space. A [[banach_contraction|contraction on a nonempty complete metric space]] has a unique fixed point and convergent exact iterates. Affine dependence on continuation value alone does not establish contraction, and nonlinear dependence does not preclude it. An order-preserving map on a complete lattice can have several fixed points. Existence, uniqueness and convergence therefore require separate hypotheses.

Lax–Richtmyer and monotone-scheme convergence results apply to their particular numerical problems and assumptions. They are not general consequences of choosing quadrature, EGM or an envelope routine. A finite collection of numerical checks also does not prove an [[operator]] identity on its entire domain.

## Terminology

Computational adequacy in programming-language semantics relates a stated denotational interpretation to specified operational observations. The exact-agreement convention above is the project's numerical correctness obligation; it should not be substituted for every literature definition of adequacy.

The detailed project obligations are in [Initial-algebra semantics](../bellman-calculus/APPX-B-INITIAL-ALGEBRA.md#8-the-adequacy-obligation) and [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md#6-model-interpretation-and-numerical-realization). See also [[semantics]] and [[methodization]].
