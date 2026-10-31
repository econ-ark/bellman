---
title: Handler
slug: handler
description: An executable implementation of a selected numerical operation.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- docs/Bellman-Sym/04-methodization.md
- docs/bellman-calculus/06-Methods.md
tags: []
audience: user
type: concept
---

# Handler

A **handler** is the executable callable used to carry out a selected numerical operation. A **method** is the algorithmic choice; the handler is its particular implementation. [[methodization|Methodization]] associates a method with a supported operation of a [[stage]], while [[settings]] supply numerical choices such as a grid size or tolerance.

## Implementation and mathematical meaning

A handler's [[signature|inputs and outputs]] must match the operation's required objects. Where a toolkit uses a different representation, an **adapter** converts the inputs into that representation and converts the results back. The adapter and the callable are distinct parts of the calculation.

For example, a solver may represent a continuation value by an interpolated function and the probability distribution of a shock by finitely many weighted outcomes. Its recorded contract must state where it is exact and which approximations are introduced. Neither an import path nor a method name proves [[adequacy|correctness]] or [[semiconjugacy|semiconjugacy (strong / order)]].

## Finding an implementation

A methods file names the handler beside the method it carries out, as a package and the name of a callable in it: the consumption stage of the portfolio application binds `!egm` with `handler: cons-port:egm`, and the retirement application's consumption stages bind it with `handler: asva:make_egm_1d`, the one-dimensional endogenous-grid step of asva, the numerical toolkit installed beside the package. A handler builds its numerical [[operator]] from the records that a [[builder]]'s `kernels()` answers, which refer to no stage, and from the grids it reads from the settings ([Methodization](../Bellman-Sym/04-methodization.md) §4).

A handler is not the mathematical definition of the operation. Those definitions remain in the stage and the [[bellman_calculus|Bellman calculus]].
