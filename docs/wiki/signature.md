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
- path: docs/bellman-calculus/APPX-D-KINDS-AND-SORTS.md
  class: canonical
  date: '2026-11-11'
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

A **signature** has a set of [[sort|sorts]] and a set of operation symbols, each with a [[rank]]: its ordered input sorts and its output sort ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §3). An interpretation supplies the actual operations on the carriers of those sorts; listing a symbol is not yet giving its mathematical behavior.

In a many-sorted algebra, sorts form an index set and each sort has a carrier set of objects. For each input word of sorts and output sort, the signature provides operation symbols of that rank. Their interpretations map products of the corresponding input carriers to the output carrier. Goguen, Thatcher, Wagner and Wright (1977), *Initial Algebra Semantics and Continuous Algebras*, §2 p. 70, gives this definition. That source uses **rank** for the length of the input word and calls the pair of the input word and the output sort the symbol's type; the entry [[rank]] states the usage followed here.

## Builder signatures and mathematical signatures

A [block](../Bellman-Sym/01-stage.md#3-builder-blocks) header declares the input and output [[field|fields]] of authored text, with their sets, roles and [[perch|perches]]. A [[sym|Bellman-SYM]] [[builder]] signature instead gives the actual function or measure [[semgraph|wires]] of the [[operator]] constructed from that block; `signature()` answers it as one record with two parts, `inputs` and `outputs`. On a controlled backward edge, the control is a coordinate of the functions carried by the wires and is not itself an input wire. A state of the perch at which a [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks)'s output stands is likewise a coordinate of the output function and is listed on no backward header ([Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md#r1-blocks-and-their-headers) R1). The policy is an index on the [[builder|builder at a policy]] and is not an argument of the [[builder|decision value function]]. A block identifier names the authored block; its [[statement|statements]] and dependencies determine the constructed operator.

A [[stage]] has two mathematical signatures ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §6). The sorts of its **state signature** name the state spaces of its perches, and its symbols are the stage's transitions, each a [[operator#Kernels|law of motion]] with its shock law. Its **operator signature** has two sorts for each perch, which name a space of value functions and a space of measures on the state space of the perch, and a sort of policies, and its symbols are the builders; a builder signature gives the rank of one of them. Composition is no operation of either signature. A term is a path of symbols, an arrow of the free category of the signature, whose objects are the sorts, and two builders compose by the concatenation of their paths. The terms of a signature, their interpretations and the `.bl` constructor grammar are distinct objects. [The stage term](../bellman-calculus/APPX-C-STAGE-TERM.md) and [Abstract grammar](../bellman-calculus/11-abstract-grammar.md) give the mathematical account.

Neither a signature nor matching **inputs and outputs** prove integrability, an attained maximum or admissibility of a numerical method. [[methodization|Methodization]] requires a supported existing computation and the method's contract. See [[sort]], [[syntax]] and [[expression]].
