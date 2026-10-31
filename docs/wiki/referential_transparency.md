---
title: Referential transparency
slug: referential_transparency
description: Replacing an expression by another with the same meaning in a fixed context.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- "Hutton, G. (2023). Programming Language Semantics: It's Easy as 1,2,3. Journal of Functional Programming 33, e9. §3, p. 3."
- docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
tags:
- foundations
- ffp
- semantics
audience: user
type: concept
---

# Referential transparency

**Referential transparency** permits an expression to be replaced by another with the same meaning without changing the meaning of the enclosing expression. The environment, types, and binding context must be fixed, and substitution must not capture a free variable.

## Compositional reasoning

For a compositional [[semantics]], the meaning of a compound expression is determined by the meanings of its parts. Equality of the relevant subexpression meanings then supports replacement in a well-formed context. Hutton illustrates this with arithmetic expressions in §3 of the reference below.

In a Bellman problem, equality must include the relevant continuation inputs, state domains, conditional distributions, and free [[parameters]]. Two policies that happen to coincide at a few grid points need not denote the same function. Replacing exact expectation by a quadrature approximation likewise requires an error argument rather than an appeal to equality.

## A programming discipline

Explicit inputs and immutable mathematical objects make these dependencies easier to inspect. Hidden mutable state can make an expression's result depend on more than its stated arguments. This motivates the project's [[ffp|functional programming style]], but does not prove that any particular [[handler]] is pure or mathematically correct.

The [initial-algebra account](../bellman-calculus/APPX-B-INITIAL-ALGEBRA.md) separates structural compositionality from a justified implementation.

## Reference

Hutton, Graham (2023). “Programming language semantics: it's easy as 1,2,3.” *Journal of Functional Programming* 33, e9, §3, p. 3. [Article](https://doi.org/10.1017/S0956796823000072).
