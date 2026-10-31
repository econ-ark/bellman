---
title: Functional programming and FFP
slug: ffp
description: Backus’s functional programming systems and their relevance to composition.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- "Backus, J. (1978). Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs. Communications of the ACM 21(8): 613–641. §§11.2–11.2.4, 12 and 13.1–13.3.2; §14 for applicative state transition systems."
tags:
- ffp
- backus
- foundations
audience: user
type: concept
---

# Functional programming and FFP

Backus's **FP systems** distinguish objects, functions, application, functional forms, and definitions. A [[functional_form|functional form]] combines functions, or functions and objects, to form a function. Composition and construction are examples. An algebra of such forms supports reasoning about complete functions rather than an instruction sequence.

## What FFP adds

In Backus's **formal systems for functional programming (FFP)**, objects systematically represent functions, and object sequences can represent functional forms. The first element determines the form; the remaining elements supply its arguments. Backus distinguishes the meaning of an expression from the function represented by an object.

This is a source for the project's emphasis on explicit composition of meaningful operations. It does not require that a compiler avoid a parsed AST, that all expressions be opaque strings, or that a staged economic language contain no bound variables. Those are separate design questions. Backus's later abbreviation AST means *applicative state transition*, not abstract syntax tree.

## In the Bellman calculus

The useful connection to the [[bellman_calculus|Bellman calculus]] is composition of whole mathematical operations with known types and stated laws. The [[semgraph|semgraph (semantic graph)]] retains [[builder|builders]] and their named operations or authored computations. Internal scalar expressions still have representations, but scalar arithmetic is not an additional advertised level of that graph.

An algebraic identity applies only under its mathematical interpretation and domain assumptions. A numerical replacement also needs an [[adequacy|accuracy or correctness argument]]; functional style alone provides no such guarantee.

## Reference

Backus, John (1978). “Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs.” *Communications of the ACM* 21(8), 613–641. §§11.2–11.2.4, 12, 13.1–13.3.2; §14 for applicative state transition systems.
