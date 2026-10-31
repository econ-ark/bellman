---
slug: term_json_encoding
title: Term JSON encoding
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
merged_from:
- decoder
audience: user
type: concept
---

# Term JSON encoding

A [[sym|Bellman-SYM]] syntax fixture records the **parsed AST** (abstract syntax tree) of a `.bl` [[stage|stage file]]. `bellman.syntax.lower.to_json(term)` converts that tree into Python values suitable for JSON serialization. `bellman.syntax.decode.from_json(data)` decodes a supported encoding into a generated `FILE` object; it accepts already-parsed JSON values, not JSON text or a file path.

## Encoding and decoding

Each generated constructor becomes an object with a `"__class__"` tag and its declared [[asdl|ASDL fields]], the named positions of the constructor, which are no economic [[field|fields]]. Absent optional positions are explicit `null` values; sequences become arrays. The encoder emits fields in declaration order. The serializer determines whitespace and other textual formatting, so equality of JSON values does not promise preservation of arbitrary input JSON bytes.

The decoder accepts constructors defined by the generated grammar, requires exactly their fields and checks sequence versus single-value positions. It rejects unknown constructors, missing or extra keys, arrays in single-value positions and non-FILE roots. `TermDecodeError`, a `ValueError`, identifies the defect with a descriptive path into the encoding. No data-provided name is evaluated or imported.

For supported FILE fixtures, encoding after decoding recovers the encoded values, and decoding an encoded FILE recovers the generated structure. This claim is restricted to the codec's accepted inputs: `to_json` can also encode subnodes that are not accepted roots of `from_json`. Generated single-value positions do not themselves enforce all grammar [[sort|sorts]] or contextual rules.

## Purpose and limits

A **parser** reads concrete `.bl` syntax; a **decoder** reconstructs syntax from its saved representation. Parsing is not generally an inverse of source printing. Both routes can supply `make_stage(term, spans)`, with `None` for the absent [[source_span|span table]] of a decoded fixture. Construction checks remain necessary.

Fixtures support parser and construction conformance tests. They are not persistence for the [[semgraph]] (semantic graph), and applications load `.bl` source rather than fixtures. After construction the stage retains interpreted equations and definitions, not this tree. See [[term_address|term address]], [[asdl|ASDL]] and [The stage](../Bellman-Sym/API/stage/01-the-stage.md) §1.
