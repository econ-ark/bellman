---
slug: source_span
title: Source span
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
audience: user
type: concept
---

# Source span

A **source span** identifies the interval occupied by an authored item in a `.bl` file. `SourceSpan(file, line, column, end_line, end_column)` records one-based lines and columns; columns count Unicode code points and the end position is exclusive.

`bellman.syntax.lower.parse_with_spans(text, filename=None)` returns the **parsed AST** (abstract syntax tree) and a read-only **span table** keyed by [[term_address|term address]]. The caller supplies both to `make_stage(term, spans)`. Construction uses spans to locate diagnostics, then discards the table. Spans are not retained on the [[stage]] or included in the [[term_json_encoding|term JSON encoding]]. A decoded fixture supplies `None` instead; its construction errors still identify the item address.

Spans cover authored items such as declarations, definitions, [blocks](../Bellman-Sym/01-stage.md#3-builder-blocks) and their [[statement|statements]]. A block's span covers its whole interval, while an error inside an expression uses its enclosing item's span. Ignored comment tokens do not receive their own item spans, although an enclosing interval may include a comment. Duplicate item addresses cannot identify two entries in one span table.

A span is an interval; a source position is a point. Neither is a symbol table, which associates names with declarations. Later method-binding diagnostics must use their own available source or provenance information; they cannot assume the discarded construction span table remains accessible.

See [The stage](../Bellman-Sym/API/stage/01-the-stage.md) §§1 and 6 for the distinction between source structure, construction checks and mathematical conditions.
