---
title: Bellman-SYM
slug: sym
description: The declarative language for writing staged Bellman problems.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- docs/Bellman-Sym/index.md
- docs/Bellman-Sym/01-stage.md
tags: []
audience: user
type: concept
---

# Bellman-SYM

**Bellman-SYM** is the declarative language used to write a staged Bellman problem. A modeler states domains, information, choices, equations, and [[operator#Kernels|shock probability distributions]] in a `.bl` [[stage|stage file]]. The expression syntax comes from **dynspec**, the host language for these declarations and equations. Outer YAML files assemble stage files into [[period|periods]] and a [[trellis]], and supply [[methodization|methods]], [[settings]], and [[calibration]].

## Start with an economic model

The [stage walkthrough](../Bellman-Sym/01-stage.md) introduces consumption after income is observed. It explains why beginning assets, resources at the consumption decision, and savings for continuation have different information contexts. The later [field-equation example](../Bellman-Sym/03-field-equations.md) separates consumption into a reusable stage file before adding discounting and investment.

A stage identifier or [block](../Bellman-Sym/01-stage.md#3-builder-blocks) name supplies an address; it does not supply an equation. A solver choice likewise cannot fill in a missing budget constraint or objective. The modeler states these relationships explicitly.

## Syntax, meaning, and computation

[[syntax|Syntax]] describes the written source and its parsed abstract syntax tree (AST). [[upsilon|The meaning construction]] interprets that temporary AST as a [[semgraph|semgraph (semantic graph)]] with retained equations and definitions. [[methodization|Methodization]], calibration, and settings provide the numerical choices and values required for a particular calculation. Successful parsing alone establishes neither an economically admissible model nor a solved policy.

The [language guide](../Bellman-Sym/index.md) explains what to write and inspect. The [[bellman_calculus|Bellman calculus]] develops the mathematical interpretation and its assumptions in [its chapters](../bellman-calculus/index.md).
