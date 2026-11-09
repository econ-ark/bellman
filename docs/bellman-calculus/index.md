---
title: Bellman calculus — foundations
short_title: bellman-calculus
tags:
  - bellman-calculus
  - foundations
  - semantics
  - catalogue
audience: user
type: theory
topic: [calculus]
---

# Bellman calculus

> [!summary]
> The Bellman calculus describes staged recursive decision problems through their states, information, equations and composed operators. These pages explain the mathematical interpretation, with one buffer-stock running example and explicitly unfinished chapters on composition.

> [!info]- Relationship with other documents
> **Used by** — [Bellman-SYM](../Bellman-Sym/index.md) documents the `.bl` stage source and supporting YAML whose meaning these pages state; Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) states the interpretation rules and their assumptions.
> **See also** — [Concept wiki](../wiki/index.md) provides linked definitions.

<a id="what-this-documentation-is-for"></a>

## 1. Purpose

A recursive dynamic program specifies sequential choices, current rewards and continuation values. The calculus records which information is available at each stage and how its operations compose. It distinguishes random fields from representing functions, mathematical interpretation from numerical approximation, and fixed-policy evaluation from optimization.

The intended reader is an economist interpreting or constructing a model. The exposition uses mathematical prose and selected derivations; unfinished sections remain labeled. A typed graph does not by itself prove integrability, optimal selection or numerical convergence. The source rules and Python interfaces belong to [Bellman-SYM](../wiki/sym.md), while these pages discuss their mathematical meaning.

<a id="contents-and-reading-order"></a>

## 2. Reading order

Start with [Introduction](./01-Introduction%20to%20T-calculus.md) and the [buffer-stock example](./02-Illustrative%20example.md), then read stages, fields and operators. The branching notes contain further example outlines; they are not additional fully developed running examples.

| Page | Subject |
|---|---|
| [Introduction](./01-Introduction%20to%20T-calculus.md) | Source, mathematical interpretation and numerical computation. |
| [Illustrative example](./02-Illustrative%20example.md) | The buffer-stock Bellman equation and staged factorization. |
| [Stages and perches](./03-Stages%20and%20perches.md) | Information, sufficient states, conditional laws and stage operators. |
| [Fields, functions and types](./04-fields,%20functions%20and%20types.md) | Random quantities, value domains, representative functions and binding. |
| [Operators and builders](./05-Operators%20and%20builders.md) | Unfinished notes on transition expectation, evaluation, selection and implicit relations. |
| [Methods](./06-Methods.md) | The signature of an operator with its method and grid components, composition over the field component, the grid as a retract, the handler, the two erasures and the two levels of a stage. |
| [Stage composition](./07-stage-composition.md) | Unfinished notes on compatible joins within periods. |
| [Periods and the trellis](./08-periods-and-trellis.md) | Unfinished notes on occurrence-specific composition and boundary data. |
| [Branching](./09-branching.md) | Unfinished notes on labeled choices and exogenous selection. |
| [Semi-conjugacy](./10-semi-conjugacy.md) | Unfinished notes on conditional relations between operator forms. |
| [Abstract grammar](./11-abstract-grammar.md) | Mathematical composition notation and its distinction from concrete source grammar. |
| [Ingredients](./ingredients.md) | Symbol and terminology reference. |

## 3. Appendices and catalogues

| Reference | Subject |
|---|---|
| [Appendix A — Semantics](./APPX-A-SEMANTICS.md) | Source interpretation, retained equations and numerical attachments. |
| [Appendix B — Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) | Ground/free terms, specified interpretations and exact refinement. |
| [Appendix C — The stage term](./APPX-C-STAGE-TERM.md) | Typed builder symbols and compatible stage compositions. |
| [Appendix D — Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) | Declared type order, interpreted inclusion and local classification conventions. |
| [Appendix F — Operator algebra](./APPX-F-OPERATOR-ALGEBRA.md) | Composition, transition pairing, branching and numerical obligations. |
| [Appendix G — Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) | Primitive objects, typed expressions, stages, calibration and methodization functors, and numerical realization. |
| [Catalogue index](./catalogues/index.md) | Field, function, operator and parameter/settings inventories. |
| [Fields](./catalogues/fields.md) | Field declarations, value domains and representatives. |
| [Functions](./catalogues/functions.md) | Typed functions and their mathematical roles. |
| [Operators](./catalogues/operators.md) | Operations and their input/output types. |
| [Parameters and settings](./catalogues/parameters-settings.md) | Economic model inputs and numerical choices. |
