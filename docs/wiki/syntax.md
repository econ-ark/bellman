---
slug: syntax
title: Syntax
tags:
- syntax
- grammar
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/bellman-calculus/11-abstract-grammar.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/API/stage/01-the-stage.md
  class: canonical
  date: '2026-09-28'
merged_from:
- panini_backus_form
audience: user
type: concept
---

# Syntax

**Syntax** specifies the forms that expressions and declarations can take. Concrete syntax is the text a modeler writes. Abstract syntax records its structure without incidental punctuation. Neither alone establishes what the model means or whether it has a solution.

[[sym|Bellman-SYM]] stage source uses `.bl` [[stage|stage files]], including declarations, equations, function definitions, arithmetic and local binders. Supporting YAML supplies composition and binding records. Parsing constructs a temporary **parsed AST** (abstract syntax tree); checking and interpretation construct retained equations and diagrams. The constructed [[semgraph]] (semantic graph) retains the interpreted equations in its two [[semgraph|initial diagrams]], on the [[field|fields]] of the stage; it is not another name for the parsed AST.

## Grammar and contextual checks

A context-free grammar rule has one nonterminal on its left and alternative sequences of terminals and nonterminals on its right, conventionally written `A ::= ... | ...`. Nonterminals name grammatical categories; terminals are source tokens. The name Pāṇini–Backus Form also refers to this production notation. [[asdl|ASDL]] instead describes abstract constructor structures.

A grammar may recognize `E_{y}(V) + y` as an expression while construction rejects it as arrival value when income is not yet observed. Name resolution, type agreement, binding and information availability are contextual checks, not consequences of punctuation. Integrability, sufficient states, attained optima and numerical accuracy require further conditions.

Mathematical composition terms describe specified operations on functions or measures. They are distinct from both the concrete stage grammar and a chosen runtime representation. A compositional interpretation needs specified operations and assignments to free inputs; grammar alone does not supply missing economic equations or prove equivalence of different models.

See [[expression]], [[signature]], [The stage](../Bellman-Sym/API/stage/01-the-stage.md) §1 and [Abstract grammar](../bellman-calculus/11-abstract-grammar.md).
