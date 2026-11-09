---
slug: sort
title: Sort
tags:
- foundations
- type
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/Bellman-Sym/reference/symbols-conventions.md
  class: canonical
  date: '2026-09-07'
- reference: "Goguen, J. A., Thatcher, J. W., Wagner, E. G. and Wright, J. B. (1977). Initial Algebra Semantics and Continuous Algebras. Journal of the ACM 24(1): 68–95. §2, p. 70."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Sort

A **sort** identifies a kind of object in a typed mathematical vocabulary. Its **carrier** is the set of objects assigned to that sort by an interpretation. The sort and its carrier are distinct: one is an index, the other a set.

An operation's type lists ordered input sorts and an output sort. Its interpretation maps the corresponding carriers. This is the many-sorted definition in Goguen, Thatcher, Wagner and Wright (1977), *Initial Algebra Semantics and Continuous Algebras*, §2 p. 70; see [[signature]].

## Distinctions in a stage

In a [[stage]], a grammar sort classifies a source constructor. A [[field]] domain constrains the quantity it denotes. An economic role, such as control or value, and an information context supply further meaning. A state value, a scalar payoff, a function on states and a measure over states therefore cannot be interchanged merely because a diagram connects them.

The [[semgraph|builders graphs]], the graphs of the [[builder|builders]], keep state-space, value and function-space types explicit: the sort of a function [[semgraph|wire]] holds its coordinates and its value set. A numerical [[grid]] representation is not automatically a subsort of the exact function space: such a claim needs an embedding and its interpretation. Method labels alone do not establish carrier inclusion or derivative agreement.

See [[semgraph|initial diagrams]], [[parameters]], [[settings]] and [Fields and types](../Bellman-Sym/reference/symbols-conventions.md).
