---
title: Field
slug: field
description: A named quantity at a perch; its stochastic interpretation after shocks are declared, and the distinctions from a representing function and a realized value.
wiki_status: budding
last_reviewed: '2026-09-12'
reviewed_by: "the session of 12 September 2026, at AAS's request; source-checked against the calculus pages and Stokey and Lucas (1989)"
sources:
- docs/bellman-calculus/04-fields, functions and types.md
- docs/bellman-calculus/03-Stages and perches.md
- docs/bellman-calculus/APPX-D-KINDS-AND-SORTS.md
- docs/bellman-calculus/08-periods-and-trellis.md
- docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md
- docs/Bellman-Sym/appendices/13-perch-tagging-rules.md
- docs/Bellman-Sym/01-stage.md
- "Stokey, N. L. and Lucas, R. E., Jr., with Prescott, E. C. (1989). Recursive Methods in Economic Dynamics. Harvard University Press. Chapter 9, §9.1."
tags:
- field
- semantics
- foundations
audience: user
type: concept
---

# Field

A **field** is a named quantity at a [[perch]], with a declared set: a state, a control, a shock, or a value. In the buffer-stock [[stage]], beginning assets are a field at arrival; resources and consumption are fields at decision; savings and the continuation value are fields at continuation. Once a stage declares shocks, its fields may be interpreted as random variables on an underlying probability space. The field, a function representing it in state coordinates, and the value of that function at one state are distinct objects. [Stages](../Bellman-Sym/01-stage.md) §2 explains declarations, and [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) §2 gives their interpretation.

A field name is local to its stage occurrence. The same spelling in another stage denotes another field, even when both stages stand in one [[period]]. An equation uses its own stage's declarations; a [[connector]] selects eligible continuation and arrival fields for composition without changing their names. All branches of one stage share that stage's field names, so distinct branch states require distinct names. A [[parameters|parameter]] follows a different rule: two stages in one period that declare the same parameter name share one period parameter.

## 1 What the word replaces

The word "variable" does five jobs in a written economic model. It is a symbol in an equation; a coordinate of the state space; a random quantity whose value depends on the history of shocks; a realized number; and, once the model is solved, a function of the state such as $v(x)$. An economist moves between these readings without noticing, and in a paper that costs nothing. A [[stage|stage file]] cannot afford the ambiguity, because the checks the construction performs each ask a question that only one of the five readings can answer: is this quantity known at arrival or only at decision? is this the value or the value function? is the `w` on the output side of one [block](../Bellman-Sym/01-stage.md#3-builder-blocks) the same object as the `w[>]` on the input side of the next?

"Field" names the declared quantity at a perch. Under a stochastic interpretation it is a random quantity at an information set. The other readings keep their own words: a **set** for the values a coordinate may take, a **realization** for a number, and a **representing function** for a function of state coordinates. The symbol is the field's name.

## 2 Why the word is "field"

In physics a field is a quantity attached to every point of a region: the temperature at each point of a room, the electric field at each point of space. Three features of that usage carry over. The field has a value at each point, and the value at a point is what an observer there can measure. The field is not any one of its values. And the field is not the law that determines it; Maxwell's equations relate the values of the electromagnetic field at neighboring points, but the field is the thing the equations are about, not the equations.

In a stage the points are the perches, the three information contexts of arrival, decision and continuation. Under the stochastic interpretation, measurability with respect to a perch's sigma-algebra states that the field's value can be read from the information available there. The same written base name at two perches, `w` and `w[>]`, identifies two fields, equal only when a statement says so ([Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) §1). The equations inside a block relate fields at neighboring perches, $X_\sim = \mathrm g_\prec(X_\prec,\zeta)$ almost surely under that interpretation.

The probabilist's usage supplies one interpretation rather than the definition. A random field is a family of random variables indexed by a set of points. After shocks and an underlying probability space have been specified, the fields of a stage can be read as such a family indexed by name and perch.

Economists already work with this object under another name. Stokey and Lucas define a plan as "a value $\pi_0 \in X$ and a sequence of measurable functions $\pi_t : Z^t \to X$" (Stokey and Lucas 1989, *Recursive Methods in Economic Dynamics*, chapter 9 §9.1): a choice that is a measurable function of the history of shocks observed so far. A field is that object, given a name and placed at an information set inside a [[period]] of the model's [[trellis]] rather than at a date.

## 3 Two senses the word does not have

The word has no connection with the algebraic field, the structure that makes $\mathbb R$ a field. Nor does it mean the field of a record in a data structure, a named position holding a value.

## 4 What the word buys

Four things become statable and checkable.

1. **Where a quantity is known.** A field has one declared or inferred perch. A shock field is known at the perch after its draw, according to the stage timing; a control is at decision wherever it is listed; a perch is never guessed ([Perch tagging rules](../Bellman-Sym/appendices/13-perch-tagging-rules.md)).
2. **A field and its representing function are distinct objects.** Under the stochastic interpretation, the continuation value `V[>]` is a random variable measurable at continuation. A representing function $\mathrm v_\succ : \mathsf X_\succ \to \mathsf L$ satisfies $V_\succ = \mathrm v_\succ(X_\succ)$ almost surely, and it exists only when a version of the field is measurable with respect to the information generated by the state. The [[semgraph|initial diagrams]] are drawn on fields; the [[semgraph|builders graph]] of the [[backward_builder|backward builders]] is drawn on functions.
3. **Sameness across perches is asserted, not assumed.** `w[>] = a + c[>]` is a statement the modeler writes; without it the two fields are unrelated.
4. **A domain is not integrability.** A field declared in $\mathbb R$ is not thereby integrable or square-integrable, and its representative is not thereby continuous; those remain obligations the construction records rather than facts it assumes ([Periods and trellis](../bellman-calculus/08-periods-and-trellis.md) §3).

## 5 Classification

A field is classified by its perch, its role and its value set, and its [[sort]] combines those declarations. The roles are state, control, shock and value. A [[parameters|parameter]] and a declared function are not fields. In one stage's semgraph, a field is a [[semgraph|wire]] of an initial diagram with local identity `<stage>:<perch>:<field>`; in a trellis, its stage occurrence address distinguishes it from the same local wire of another occurrence. A [[statement]] is represented by a box between field wires, and a [[builder]] acts on the functions or the measures that represent fields.
