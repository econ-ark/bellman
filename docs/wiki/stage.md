---
title: Stage
slug: stage
description: A module of a Bellman problem with three information contexts.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- docs/Bellman-Sym/01-stage.md
- docs/Bellman-Sym/03-field-equations.md
tags: []
audience: user
type: concept
---

# Stage

A **stage** is a module of a Bellman problem with arrival, decision, and continuation [[perch|information contexts]]. It declares the quantities relevant there and the equations for state transitions, value calculations, and policy relations. Its source is a `.bl` **stage file** in [[sym|Bellman-SYM]], and in Python it is the [[elaborated_stage|elaborated stage]] that `elaborate_stage` of `bellman.stage` makes of the file.

## A consumption example

A household begins with assets $b$, observes income $y$, and chooses consumption $c$ from resources $w=Rb+y$, leaving savings $a=w-c$. Arrival information precedes income, decision information includes observed income, and continuation information includes the consumption choice. Assume resources suffice for the consumption decision and savings suffice for continuation value; the household's information can be richer than these scalar states.

For an admissible continuation function $W$, the objective is $Q(w,c)=u(c)+\beta W(w-c)$. A policy selects a feasible maximizer, and arrival value averages the resulting decision value over income. Existence of that maximizer, measurability, and finiteness of the expectation are assumptions to check. The [complete walkthrough](../Bellman-Sym/01-stage.md) states domains, a conditional distribution of income, and sufficient conditions.

## A stage file and its stage occurrences

A **stage occurrence** is one use of the stage file in a [[period]] at a particular position in the model: the file elaborated there, with its own three bindings. Its [[field|fields]], policy and numerical choices remain local to that occurrence. A parameter name declared by two stages of the same period, however, names one [[parameters|period parameter]] with one reconciled declaration and value; the same name in another period names another parameter. The construction gives each stage occurrence its own semgraph and specification, prints the file's declared name for every one, and records the position in the occurrence's provenance. Each binding adds to the elaborated object in place and returns it; a **stage version** is the stage occurrence as it stands after elaboration or after one of its bindings.

The stage's [[semgraph|semgraph (semantic graph)]] retains its interpreted equations and definitions. Whole [[builder|builders]], named Bellman operations, and authored `!node` computations provide inspection boundaries. Scalar arithmetic inside a state transition or [[aggregation|value aggregator]] is not another advertised level of that semgraph.

The [field-equation tutorial](../Bellman-Sym/03-field-equations.md) develops consumption as a separate stage file, which can then be joined to discounting and portfolio choice through compatible [[connector|connectors]].
