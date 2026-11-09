---
slug: term_address
title: Term address
tags:
- syntax
- grammar
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: packages/bellman/bellman/syntax/lower.py
  class: canonical
  date: '2026-09-07'
- path: packages/bellman/bellman/syntax/decode.py
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Term address

A **term address** identifies an authored item of a [[stage|stage file]] from the **parsed AST** (abstract syntax tree) alone. `bellman.syntax.lower.item_addresses(term)` produces address–item pairs in source order. A fresh parse and its decoded [[term_json_encoding|term JSON encoding]] therefore have the same addresses without requiring source positions.

| Item | Address |
|---|---|
| Top-level item without an authored id | Its one-based position, written as a string. |
| Named [block](../Bellman-Sym/01-stage.md#3-builder-blocks) | Its header id, such as `policy`. |
| Named statement | Block address plus statement id, such as `policy.cons_choice`. |
| Unnamed statement | Block address plus one-based statement position. |
| Labeled nested block | Containing block address plus the label. |
| Statement in that block | Nested block address plus its id or position. |

Explicit ids survive changes that would shift ordinal positions, but no address is invariant under arbitrary source edits. Construction diagnostics use the address to look up a [[source_span|source span]], or report the address alone when positions are unavailable.

## Inspection and places

An address does not imply that its item is a separate graph box or a place a methods file can type. An alias can remain inspectable after substitution. Supported implicit [[statement|statements]] and named [[operator]] occurrences can receive methods without `!node`; an authored node needs an explicit id for method attachment. Positional statement addresses support records and diagnostics, not stable user bindings.

The entry [[methodization]] states the places a methods file can type: a whole [[builder]]; the Evaluation that closes a builder, where a representation of what it stores stands; a named statement; a function the stage file defines; the name of an operator, which stands for every occurrence of the operator in a block or in the stage; and one occurrence of the operator in one line. A name and one of its occurrences cannot both be typed: the package refuses the two entries together under the rule `component-typed-twice`. A place names an existing computation and creates no equation.

A [[term_json_encoding|decoder]]'s path such as `items[3].d.subject` locates a defect inside an encoded value. It is a descriptive structural path, not a term address or a promise of JSONPath-standard conformance. See [Methods and places](../Bellman-Sym/API/stage/07-methods.md).
