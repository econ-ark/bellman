---
slug: semantics
title: semantics
tags:
- foundations
- semantics
- bellman-calculus
description: Mathematical interpretation, source representation and numerical realization have distinct objects
  and correctness conditions.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-20'
needs_resolution: false
flags: []
merged_from:
- denotational_semantics
sources:
- path: docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Semantics

**Semantics** specifies what a language's expressions mean. A denotational account assigns mathematical objects compositionally; an operational account gives execution rules; an axiomatic account specifies logical assertions and proof rules. These are distinct ways to explain a language, and numerical implementation is not excluded from semantics by a general terminology rule.

## Denotation

A **denotation** is the mathematical object the interpretation assigns to a piece of a [[stage]] — a definition, a [block](../Bellman-Sym/01-stage.md#3-builder-blocks) or an authored [[statement|line]], a [[builder]], a [[sub_builder|sub-builder]], a primitive operator, a graph, or the stage itself — under the declarations of its file, the [[calibration]] of its version and, for a piece at a policy, a policy. It is a set, a map between sets, a probability measure or a [[operator#Kernels|stochastic kernel]], a relation, or an [[operator]], which is a map from functions to functions or from measures to measures. Every piece has a denotation, not the stage alone.

The box of a [[operator|primitive operator]] denotes the [[functional_form|form]] of its kind at its [[operator#Kernels|kernel]], one map, so the [[builder|pullback]] and the push-forward of one [[operator#Kernels|law of motion]] have one kernel and two denotations. An [`Argmax`](../Bellman-Sym/reference/operations.md#argmax) row, and a row whose output is among the unknowns of its own rule, denote a relation, a map only where a maximizer or a solution exists and one is selected. A piece with pieces within it denotes the composition, along the [[semgraph|wires]], of what they denote, and that composition is the same at every [[semgraph|grain]].

The verb *denotes* takes a phrase of the file or a piece of the [[semgraph]] as its subject and a mathematical object as its object; a printed view is text that states a denotation and is not one, and a [[rho|numerical representation]] approximates one under a stated contract. The package computes no denotation.

Below the stage `denote()` is the one verb that answers what a piece is and what it denotes, and `view()` is a verb of the stage alone. What `denote()` answers is a record: the mathematical structure of the denotation, with the typed wires, the rule, the kernel together with the statements of the [[stage|stage file]] it denotes and the objects those statements denote, the conditions and, on a methodized version, the method bound within the piece, which is part of what the piece denotes on the version asked. The record displays itself, and what it prints is the piece's **card**: a title naming the stage and the piece, a heavy line, then the sections that have content, `Signature` for the typed [[signature|inputs and outputs]], `At` for the policy at which a builder is stated, `Where` for local abbreviations such as the law of motion at the policy, `Declared` for a line marked [[declarative_language|`!doc`]], `Rule` for the rule at a point, `Operations` for the operations a builder composes, and `Conditions`; below a light line, `Source` with the lines of the stage file and their line numbers, and `Definitions referenced` ([A piece](../Bellman-Sym/API/stage/05-piece.md) §§1 and 5; [The builders graphs](../Bellman-Sym/API/stage/03-build.md) §3 for `At`, `Where` and `Declared`; [A builder](../Bellman-Sym/API/stage/04-builder.md) §1 for `Operations`). A block, an authored line and an [[semgraph|initial diagram]] answer the verb with the authored relation they denote. On a piece that answers them, `signature()` answers the inputs and outputs the card's `Signature` section prints, and `kernel()` the pointwise map its rule applies.

## The Bellman interpretation

The [[bellman_calculus|Bellman calculus]] distinguishes mathematical interpretation, denoted [Υ](upsilon.md), from numerical realization, denoted [Ρ](rho.md). The mathematical model specifies domains, equations, [[operator#Kernels|shock probability distributions]] and feasible choices. A numerical method supplies a procedure and representations intended to approximate or compute that model. [[adequacy]] explains the separate correctness obligations.

Compositional interpretation determines a compound expression from its constituents and their context. For an ordinary algebraic signature, [[initial_algebra|initiality]] gives a unique term interpretation once target operations and any free-input environment are fixed. It does not choose missing conditional distributions, solve implicit equations, or prove integrability and selection assumptions.

## Source and retained model

[[sym|Bellman-SYM]] stage equations are authored in `.bl` stage files. Parsing produces a temporary **parsed AST** (abstract syntax tree); construction interprets that syntax into the retained [[semgraph]] (semantic graph) and discards the parsed AST. The graph retains authored equations, values, typed operations and definitions. It is not a source string interpreted a second time.

The [[semgraph]] entry defines the four graphs of a stage, the two initial diagrams on [[field|fields]] and the two builders graphs, on functions backward and on measures forward, with their grains and [[semgraph|value bundles]]; a stage reaches them as `stage.initial.backward`, `stage.initial.forward`, `stage.builder.bwd` and `stage.builder.fwd`. Derived interpretations require sufficient state information, conditional distributions and analytic assumptions; an implicit relation remains a relation until a valid selection is supplied.

Typed composition alone does not prove an equation-preserving functor. Equal denotation also does not erase authored names and method-attachment boundaries or recover a unique source spelling. See [Syntax to semantics](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) and [Equation boundaries and indexing](../Bellman-Sym/appendices/15-appendix-d-node-tag-and-field-indexing.md).

The [[abstract_decision_process|abstract dynamic program (ADP)]] and [[recursive_decision_process|recursive decision process (RDP)]] supply useful mathematical descriptions of policy and value updates. They are not identical to the whole stored representation or every [[sort]] of the [[bellman_algebra|Bellman algebra]].
