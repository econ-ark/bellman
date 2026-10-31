---
slug: asdl
title: ASDL
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
- reference: "Wang, D. C., Appel, A. W., Korn, J. L. and Serra, C. S. (1997). The Zephyr Abstract Syntax Description Language. Conference on Domain-Specific Languages (DSL '97), USENIX Association. §§2.2–2.7 and §3.1."
  class: external
  date: '2026-09-07'
merged_from:
- head_marks
audience: user
type: concept
---

# ASDL

**ASDL**, the Abstract Syntax Description Language, describes the structure of tree-shaped data independently of a concrete source spelling. A type lists possible constructors; each constructor has typed positions called **ASDL fields**. The prefix distinguishes a constructor position from an economic [[field]].

For example, `exp = Num(int value) | Add(exp left, exp right)` describes two expression forms. `*` after a type denotes a sequence and `?` an optional position. These qualifiers describe structure; they are not arithmetic. Named positions make generated representations easier to read. The original notation also supports product types, with restrictions on recursion.

## Grammar and concrete spelling

A concrete grammar determines how text is written. An ASDL description determines the abstract structure represented after parsing. Neither establishes name resolution, information availability or mathematical validity. [[sym|Bellman-SYM]] parses arithmetic, function definitions and local binders in `.bl`; equations are not opaque terminal strings. See [[syntax]] and [the abstract-grammar discussion](../bellman-calculus/11-abstract-grammar.md).

A concrete encoding may identify a variant by a tag, its position or its shape. The historical name **head mark** refers to such an identifying tag. The ASDL paper's binary exchange format uses constructor tags and declared field order, but that does not prescribe Bellman-SYM's source format. Current [[period]], [[trellis]] and binding YAML mappings are read according to their own contracts.

The project's generated syntax fixtures use the [[term_json_encoding|term JSON encoding]]. They are distinct from both the paper's binary format and the retained [[semgraph]] (semantic graph) of a [[stage]].

Wang, Appel, Korn and Serra (1997), *The Zephyr Abstract Syntax Description Language*, §§2.2–2.7, describes constructors, fields, qualifiers and exchange. Its §3.1 illustrates that contextual restrictions can exceed what the abstract description expresses.
