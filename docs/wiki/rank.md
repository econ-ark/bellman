---
slug: rank
title: rank
tags:
- foundations
- universal-algebra
description: An operator input/output profile in local usage; ADJ uses rank for the number of arguments.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-D-KINDS-AND-SORTS.md
  class: canonical
  date: '2026-11-11'
- reference: "Goguen, J. A., Thatcher, J. W., Wagner, E. G. and Wright, J. B. (1977). Initial Algebra Semantics and Continuous Algebras. Journal of the ACM 24(1): 68–95. §2, p. 70."
  class: external
  date: '2026-09-07'
- reference: "Goguen, J. A. and Meseguer, J. (1992). Order-Sorted Algebra I: Equational Deduction for Multiple Inheritance, Overloading, Exceptions and Partial Operations. Theoretical Computer Science 105(2): 217–273. Definition 2.1, as cited in Appendix D of the Bellman calculus."
  class: external
  date: '2026-11-11'
audience: user
type: concept
---

# Rank

In the local typed-operator vocabulary, an operator's **rank** is its input/output profile $s_1\times\cdots\times s_n\to s$ ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §3). It states which sorts an operation accepts and which sort it returns. Distinct named operations can have the same profile; the profile does not determine their meaning.

Terminology varies by source. Goguen, Thatcher, Wagner and Wright (1977), §2, p. 70, call the full pair of input sorts and output sort the **type**, the input-sort string the **arity**, and its length the **rank**. Thus their rank is an argument count. Goguen and Meseguer (1992, Definition 2.1) call the full pair the rank, which is the usage here. State the convention when comparing sources.

## Model and numerical types

A [[signature]] declares operation profiles. The interpreted operation acts on the corresponding chosen carrier sets, while the type of a [[field]] also names its role, its declared set and, unless it is a shock, its [[perch]]. The input/output profile of one operation is not a complete description of the model's typing context.

A numerical method may approximate the same mathematical operation using grids or other representations. Equal mathematical ranks do not make numerical arrays interchangeable or guarantee equal answers. State the numerical domains, comparison maps and approximation conditions; see [[adequacy]] and [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md#7-types-and-identities).

See [[operator]], [[sort]] and [[signature]].
