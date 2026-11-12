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
- path: docs/bellman-calculus/APPX-D-KINDS-AND-SORTS.md
  class: canonical
  date: '2026-11-11'
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

A **sort** is a name, or the condition that a written type states, interpreted by a subset of the carrier of one kind ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §3). A **kind** is a name for the objects of one nature, such as the [[field|fields]] that a [[stage]] declares or its [[operator|operators]], and its **carrier** is the set of those objects. The carrier of a sort is the subset that interprets it. The type `!ctrl @ ℝ₊₊`, for example, names the sort whose carrier holds the controls with a declared set inside $\mathbb R_{++}$. The sort and its carrier are distinct: one is a name or a condition, the other a set.

An operation's [[rank]] lists ordered input sorts and an output sort. Its interpretation maps the corresponding carriers. This is the many-sorted definition in Goguen, Thatcher, Wagner and Wright (1977), *Initial Algebra Semantics and Continuous Algebras*, §2 p. 70, who call the pair the operation's type; see [[signature]].

## Distinctions in a stage

In a [[stage]], a grammar sort, a sort of the [abstract grammar](../bellman-calculus/11-abstract-grammar.md) and no sort of the stage's signatures, classifies a source constructor. The type of a [[field]] names a sort of fields: the intersection of the sorts named by its role, such as control or value, by its [[perch]], where it has one, and by its declared set ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §5). Functions and measures are objects of two further kinds, with sorts of their own. A state value, a scalar payoff, a function on states and a measure over states therefore cannot be interchanged merely because a diagram connects them.

The [[semgraph|builders graphs]], the graphs of the [[builder|builders]], keep the sorts of their wires explicit: the package's `Sort` record of a function [[semgraph|wire]] holds its coordinates and the declared set of the value it carries. At the builder [[semgraph|grain]], a wire that carries a value function or a measure has a sort of the stage's [[signature|operator signature]], whose carriers are spaces of value functions and of measures ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §6). A function stored at the points of a numerical [[grid]] is no member of the exact function space, and it becomes one only through the interpolant that extends it ([Methods](../bellman-calculus/06-Methods.md) §5). The grids form a kind of their own, and sorts are ordered by inclusion inside one kind only, so no sort of grids lies below a sort of functions. Method labels alone do not establish carrier inclusion or derivative agreement.

See [[semgraph|initial diagrams]], [[parameters]], [[settings]], [Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) and [Fields and types](../Bellman-Sym/reference/symbols-conventions.md).
