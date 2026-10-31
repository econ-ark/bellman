---
slug: signature
title: Signature
tags:
- foundations
- type
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/bellman-calculus/11-abstract-grammar.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-C-STAGE-TERM.md
  class: canonical
  date: '2026-09-07'
- reference: "Goguen, J. A., Thatcher, J. W., Wagner, E. G. and Wright, J. B. (1977). Initial Algebra Semantics and Continuous Algebras. Journal of the ACM 24(1): 68–95. §2, p. 70."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Signature

A **signature** is a typed vocabulary of operation symbols. It specifies each operation's ordered input types and output type. An interpretation supplies the actual operations on objects of those types; listing a symbol is not yet giving its mathematical behavior.

In a many-sorted algebra, sorts form an index set and each sort has a carrier set of objects. For each input word of sorts and output sort, the signature provides operation symbols of that type. Their interpretations map products of the corresponding input carriers to the output carrier. Goguen, Thatcher, Wagner and Wright (1977), *Initial Algebra Semantics and Continuous Algebras*, §2 p. 70, gives this definition. That source uses **rank** for the length of the input word; a full input/output type contains more information.

## Builder signatures and mathematical signatures

A [block](../Bellman-Sym/01-stage.md#3-builder-blocks) header declares the input and output [[field|fields]] of authored text, with their sets, roles and [[perch|perches]]. A [[sym|Bellman-SYM]] [[builder]] signature instead gives the actual function or measure [[semgraph|wires]] of the [[operator]] constructed from that block; `signature()` answers it as one record with two parts, `inputs` and `outputs`. On a controlled backward edge, the control is a coordinate of the functions carried by the wires and is not itself an input wire. A state of the perch at which a [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks)'s output stands is likewise a coordinate of the output function and is listed on no backward header ([Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md#r1-blocks-and-their-headers) R1). The policy is an index on the [[builder|builder at a policy]] and is not an argument of the [[builder|decision value function]]. A block identifier names the authored block; its [[statement|statements]] and dependencies determine the constructed operator.

A mathematical signature for [[stage]] composition instead specifies operations such as combining compatible builders or stages. Its terms, their interpretations and the `.bl` constructor grammar are distinct objects. [The stage term](../bellman-calculus/APPX-C-STAGE-TERM.md) and [Abstract grammar](../bellman-calculus/11-abstract-grammar.md) give the mathematical account.

Neither a signature nor matching **inputs and outputs** prove integrability, an attained maximum or admissibility of a numerical method. [[methodization|Methodization]] requires a supported existing computation and the method's contract. See [[sort]], [[syntax]] and [[expression]].
