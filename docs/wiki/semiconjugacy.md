---
slug: semiconjugacy
title: semiconjugacy (strong / order)
tags:
- foundations
- dp
- sargent-stachurski
- semi-conjugacy
description: Intertwining and paired factorization relate specified recursive maps; fixed-point, order and
  convergence claims have different hypotheses.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
merged_from:
- stachurski_transform
sources:
- path: docs/bellman-calculus/10-semi-conjugacy.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- reference: "Sargent, T. J. and Stachurski, J. (2026). Dynamic Programming, Volume II: General States. Edition of 10 April 2026. §5.2.1, pp. 160–163, equations (5.14)–(5.15), Lemmas 5.2.1–5.2.2 and Theorem 5.2.3."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Semiconjugacy

A **semiconjugacy** between self-maps $S:V\to V$ and $\widehat S:\widehat V\to\widehat V$ is a map $F:V\to\widehat V$ satisfying $F\circ S=\widehat S\circ F$. It sends exact iterates and fixed points of the first system to those of the second. This identity alone does not recover every original solution or establish equivalence of economic problems.

## Strong semiconjugacy

Sargent and Stachurski use the stronger paired factorization

$$
S=G\circ F,\qquad \widehat S=F\circ G,
\qquad F:V\to\widehat V,\quad G:\widehat V\to V.
$$

Their definition on posets does not require the maps to preserve order. The two intertwining identities follow by associativity. For $n\geq1$,

$$
S^n=G\circ\widehat S^{n-1}\circ F,
\qquad \widehat S^n=F\circ S^{n-1}\circ G.
$$

On fixed points, $F$ and $G$ are inverse correspondences: if $Sv=v$, then $GFv=v$, and similarly $FGw=w$ when $\widehat Sw=w$. Consequently existence and uniqueness of fixed points correspond. This argument needs neither invertibility on the whole spaces nor a convergence theorem.

For their order-stability result, both maps are order preserving or both are order reversing. Their convergence result adds the stated order-continuity and initial-point assumptions. Conjugacy via an order isomorphism is stronger: the bijection and its inverse both preserve order. An order-preserving bijection alone need not do so.

## Finite horizons and timing

Let $F_n:V_n\to W_n$ and $G_n:W_n\to V_{n-1}$ for $n=1,\ldots,H$. Define $T_n=G_n\circ F_n$ and $\widehat T_n=F_n\circ G_{n+1}$ for $n<H$. Associativity gives

$$
T_1\circ\cdots\circ T_H
=G_1\circ\widehat T_1\circ\cdots\circ\widehat T_{H-1}\circ F_H.
$$

Both endpoint maps remain. Applying this identity to a terminal value requires a terminal element of $V_H$ and the displayed transformation $F_H$. Reordering [[stage|stages]] while keeping an unrelated terminal state or value does not follow from this identity. The finite-horizon result is separate from stationary fixed-point correspondence.

## Numerical reformulation

A post-decision reformulation can be useful when the relevant transition, expectation and choice maps have the required domains and identities. It does not justify exchanging expectation and optimization in one formula. Smoothness, Euler inversion, feasibility and selected policies require their own assumptions. Similarly, a value/policy correspondence does not automatically transfer convergence in ordinary policy norms.

The project calls a reformulation justified by such a factorization a “Stachurski transform”. The name is no claim that two reordered [[operator|operators]] are equal or that a particular [[handler]] supports a source key. An adapter that calls a package has a broader computational role; its correctness still requires the relevant input, output and approximation checks.

The transition pairing stated in the entry [[forward_builder|forward builder]] relates the probability transport of a [[builder]] to an undiscounted expectation. It is distinct from semiconjugacy between value updates and does not include rewards or optimization.

**Reference:** Sargent and Stachurski, *Dynamic Programming, Volume II: General States*, 10 April 2026 edition, §5.2.1, pp. 160–163, equations (5.14)–(5.15), Lemmas 5.2.1–5.2.2 and Theorem 5.2.3. The project's [Semi-conjugacy chapter](../bellman-calculus/10-semi-conjugacy.md) treats particular applications.
