---
title: Ρ — numerical representation
slug: rho
description: Realizing mathematical operations with specified numerical representations.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- docs/Bellman-Sym/04-methodization.md
- docs/bellman-calculus/06-Methods.md
- docs/bellman-calculus/10-semi-conjugacy.md
tags: []
audience: user
type: concept
---

# Ρ — numerical representation

**Ρ (Rho)** names the passage from specified mathematical operations to numerical representations and executable calculations. The uppercase letter distinguishes this project notation from a risk-aversion parameter written $\rho$.

A calculation needs the model's [[parameters]], selected [[methodization|methods]], numerical [[settings]], and compatible executable [[handler|handlers]]. A graph with bound parameters is not by itself a solver. Each method has requirements on the operation it implements and on the objects used to represent its [[signature|inputs and outputs]].

## Exactness and approximation

Suppose a mathematical [[operator]] is $T:V\to V$, a numerical operator is $\widehat T:\widehat V\to\widehat V$, and maps $E:V\to\widehat V$ and $D:\widehat V\to V$ encode and decode values. The expression

$$D\circ\widehat T\circ E$$

is a candidate realization of $T$. Equality with $T$ must be justified on a stated domain. A grid, quadrature rule, interpolation scheme, or finite tolerance generally introduces an approximation that needs an error criterion. Neither this three-part expression nor [[calibration]] establishes equality or [[semiconjugacy|semiconjugacy (strong / order)]].

The [methods chapter](../bellman-calculus/06-Methods.md) separates a mathematical operation from the algorithm used for it. [[adequacy]] concerns the relationship between the intended meaning and its implementation; convergence claims require additional hypotheses.
