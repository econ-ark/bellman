---
title: Functional form
slug: functional_form
description: An operation that combines functions or objects to form a function.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- "Backus, J. (1978). Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs. Communications of the ACM 21(8): 613–641. §11.2.4, pp. 621–622."
tags:
- ffp
- backus
- foundations
audience: user
type: concept
---

# Functional form

A **functional form**, in Backus's terminology, combines existing functions, or functions and objects, to form a new function. It describes how functions are assembled, rather than one particular evaluation at an argument.

## Two examples

For functions $f:Y\to Z$ and $g:X\to Y$, **composition** forms $f\circ g:X\to Z$, with $(f\circ g)(x)=f(g(x))$.

For functions $f_i:X\to Y_i$, **construction** forms the tuple-valued function

$$\langle f_1,\ldots,f_n\rangle:X\to\prod_iY_i,
\qquad x\mapsto(f_1(x),\ldots,f_n(x)).$$

These are typed mathematical examples; Backus presents FP on a common object domain with its own convention for undefined values. The notation here does not identify every Bellman operation with one of his primitive forms.

## In staged problems

After compatible [[connector|connectors]] identify their fields, the [[operator|operators]] of the [[stage|stages]] can be composed into the operator of a [[period]]. The [[operator#Kernels|law of motion]] and the [[aggregation|value aggregator]] remain whole operations in this account. Numerical methods used to implement them belong to [[methodization]].

Backus calls the functions or objects supplied to a form its parameters. In model documentation, reserve the bare word [[parameters]] for quantities defining the economy, and say *arguments of the form* when that distinction matters. [[asdl|ASDL fields]] are a different notion: named positions in a syntax constructor, not the economic [[field|fields]] of a stage.

## Reference

Backus, John (1978). “Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs.” *Communications of the ACM* 21(8), 613–641, §11.2.4, pp. 621–622. See [[ffp|Functional programming and FFP]] for FP and FFP.
