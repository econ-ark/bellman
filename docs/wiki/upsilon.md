---
title: Υ — meaning construction
slug: upsilon
description: Interpretation of checked syntax as mathematical structure, and the elaborator, its computed step.
wiki_status: canonical
last_reviewed: '2026-10-08'
reviewed_by: Codex (Astra); source-checked. The elaborator section, Claude (Fable), session of 7 October 2026, at AAS's request, checked against the package's elaboration module and the pages of the stage object. The name of the description $M$ adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026
updated: '2026-10-08'
sources:
- docs/Bellman-Sym/API/stage/01-the-stage.md
- docs/Bellman-Sym/API/factory/stage-factory.md
- docs/bellman-calculus/APPX-A-SEMANTICS.md
- docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
- packages/bellman/bellman/factory/elaboration.py
- reference: "Pfenning, F. (2021). Lecture Notes on Elaboration. 15-814: Types and Programming Languages, Lecture 11, 5 October 2021. §1, p. L11.1, and §4, p. L11.6."
  class: literature
  date: '2026-10-07'
- reference: "Ferreira, F. and Pientka, B. (2014). Bidirectional Elaboration of Dependently Typed Programs. PPDP '14, Canterbury, 8–10 September 2014, ACM. Abstract and §1."
  class: literature
  date: '2026-10-07'
tags: []
audience: user
type: concept
---

# Υ — meaning construction

> [!summary]
> **Υ (Upsilon)** is the meaning map from a stage file to the model it states. It has two steps: the elaboration, a program of the package that constructs the elaborated stage from the file or refuses it, and the interpretation of that stage, which the Bellman calculus defines and no function computes. This page names the computed step, the **elaborator** $S$, and states what it reads and what it does not.

> [!info]- Relationship with other documents
> **Formal account** — [Appendix A](../bellman-calculus/APPX-A-SEMANTICS.md) and [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the interpretation of the constructed stage and its rules.
> **Builds on** — [[syntax|Syntax]]: the parsed AST the elaboration reads and discards; [The stage](../Bellman-Sym/API/stage/01-the-stage.md): how a stage is made.
> **Used by** — [[elaborated_stage|Elaborated stage]]: the object the elaborator constructs; [[bellman_sym_writer|Bellman-SYM writer]] and [[prose_writer|Prose writer]]: the two maps a language model computes around the elaborator.

**Υ (Upsilon)** names the interpretation that assigns mathematical meaning to a declaration. It has two steps. Elaboration, which the package performs, takes a checked phrase of a [[stage|stage file]] to a piece of the [[semgraph|semgraph (semantic graph)]]: parsing first produces a temporary [[syntax|parsed AST]], and checked construction interprets its declarations, equations, and scoped operations as the semgraph, retaining the mathematical definitions needed for subsequent inspection and calculation. Interpretation, which the [[bellman_calculus|Bellman calculus]] and [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) define and no function of the package computes, takes that piece to its [[semantics|denotation]], the mathematical object it denotes.

## 1 The elaborator

The **elaborator** is the computed step of Υ, written as a map $S : D \to E$: from a Bellman-SYM declaration $D$, the stage files with the period and trellis files, that is, the [[trellis|syntactic trellis]] and its stages, to the [[elaborated_stage|elaborated stage]] $E$, or to a refusal that names the rule the file does not satisfy, the line, and what to write instead. It is a deterministic program of the package and not a skill: no language model computes it, and it has no instruction text. Its functions are `elaborate_text(text, origin)` of `bellman.factory.elaboration` for one text held in memory, `elaborate_stage(record)` for the record `load_stage` returns, and `elaborate_trellis(syntactic)` for a trellis ([The stage](../Bellman-Sym/API/stage/01-the-stage.md) §1; [Stage functions](../Bellman-Sym/API/factory/stage-factory.md) §2). Each parses the text into a temporary parsed AST, constructs the [[semgraph]] with its definitions, its two initial diagrams and its two builders graphs, and discards the parsed AST; the stage keeps no syntax tree.

Nothing reads $D$ as text. A declaration is elaborated before anything reads it, and what is then inspected, compared with the result of another declaration, or described in words is $E$: files that differ in spelling or in the order of their blocks elaborate to one stage, and the meaning of a file is read from its elaborated stage. The interpretation of $E$, the second step of Υ, is stated by the [[bellman_calculus|Bellman calculus]] and [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) and computed by no function.

The word is the one of programming-language theory, where elaboration translates a surface syntax into a fully explicit, typed core form and fails where the source does not type-check. Pfenning (2021, §1, p. L11.1) introduces it as "a translation mediating between specific forms of concrete syntax and internal representation in abstract syntax", whose result is a signature of typed definitions and which produces none when an expression does not type-check (§4, p. L11.6); Ferreira and Pientka (2014, abstract) elaborate a source language in which arguments may be omitted "to a fully explicit core language" and prove that what elaborates type-checks there. The elaborator of the package is such a translation: it makes every type and every structure the stage file leaves to be inferred explicit in $E$, or refuses the file ([[elaborated_stage|Elaborated stage]] §1).

Two maps that a language model computes stand around the elaborator. The [[bellman_sym_writer|Bellman-SYM writer]] $\Upsilon_0 : M \to D$ writes a declaration from a description $M$ of the model in prose and displayed equations, named BellmanStageProse, and the [[prose_writer|prose writer]] $\Upsilon_1 : E \to M'$ writes a description from the elaborated stage's printed form. Each is a map and not the instruction text under which the model computes it, and the elaborator followed by the prose writer, $\Upsilon_1 \circ S$, is a reading of Υ in words. The Bellman-SYM writer works against Υ: many files have one meaning, and it must find one of them.

## 2 What is interpreted

An equation supplies its mathematical relationship. The header of a [block](../Bellman-Sym/01-stage.md#3-builder-blocks) supplies its declared inputs, outputs, domains, and information contexts; the [[signature|builder signature]] is derived from the [[operator]] the block denotes. Scope determines which occurrences a definition or expectation binds. A block name identifies the block; its spelling does not manufacture a transition or objective.

The resulting stage can still have free [[parameters]] and continuation inputs. Construction does not solve the stage or supply values for those free inputs. [[calibration|Calibration]] supplies parameter values; [[methodization]] attaches numerical methods to supported operations.

## 3 The mathematical contract

For a fixed many-sorted signature, a chosen target interpretation, and fixed free inputs, a compositional interpretation satisfies

$$
\Upsilon\bigl(\omega(t_1,\ldots,t_n)\bigr)
 = \omega^{\mathcal B}\bigl(\Upsilon(t_1),\ldots,\Upsilon(t_n)\bigr).
$$

Here the $t_i$ are well-sorted syntactic arguments, $\omega$ is a constructor, and $\omega^{\mathcal B}$ is its declared interpretation. [[initial_algebra|Initial-algebra semantics]] states the setting in which this extension is unique. Binding and equations imposed on syntax require their own treatment; the display alone does not provide it.

Reading the stage's [[field|fields]] as functions of its states additionally needs conditions such as state sufficiency, integrability, and a measurable feasible policy. These obligations are distinct from grammar checks and from the correctness of a software implementation. [Semantics](../bellman-calculus/APPX-A-SEMANTICS.md) and the [construction account](../Bellman-Sym/API/stage/01-the-stage.md) distinguish these responsibilities.
