---
slug: statement
title: statement
tags:
- semgraph
- grammar
- syntax
description: One equation line of a block as written; a value statement defines a value or marginal-value field; a statement is a box in an initial diagram, a `line` record in the definitions table, and is folded into operators in the builders graphs.
wiki_status: budding
last_reviewed: '2026-09-12'
reviewed_by: Claude (session of 12 September 2026); source-checked against the terminology rows of 12 September, D24 and the specification's representation table
updated: '2026-09-12'
needs_resolution: false
flags: []
sources:
- path: docs/Bellman-Sym/03-field-equations.md
  class: canonical
  date: '2026-09-28'
- path: docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md
  class: canonical
  date: '2026-09-28'
- path: docs/Bellman-Sym/appendices/15-appendix-d-node-tag-and-field-indexing.md
  class: canonical
  date: '2026-09-28'
- path: docs/Bellman-Sym/API/stage/02-initial.md
  class: canonical
  date: '2026-09-28'
audience: user
type: concept
---

# statement

A **statement** is one equation line of a [block](../Bellman-Sym/01-stage.md#3-builder-blocks) of a [[stage|stage file]], as written:
`V = u(c) + β*V[>] :: [id=value]`. A **value statement** is one whose
left-hand side is a value or marginal-value [[field]]; the phrase "value line"
is not used for it, because the calculus's value line $\mathsf L$ is the
set in which values lie. A statement's annotation `:: [...]` carries its
identifier and its marks, among them `!node`, which makes the statement a
node and its result a named [[semgraph|wire]] (see [[sub_builder|sub-builder]]), and [[declarative_language|`!doc`]], which
marks a declarative statement.

## Three readings

In an **initial diagram**, a graph of the stage on its fields
([[semgraph]]), a statement is a box inside its block's box unless it is
marked `!doc`: its input wires are the fields it reads and its output wire
the field it defines, so a name a statement introduces, an intermediate
field `y = l + h + x` or the candidate `c[>]` of a policy block, appears as
a wire. The initial diagrams are the only graphs in which such names are
recorded. In the **definitions table** every statement is a record of kind
`line`, keyed by its address and holding its tags and retained term; its
role, ordinal and operator occurrences are queries. In the **builders
graphs**, the graphs of the [[builder|builders]], a statement is not a box: the fold replaces it by the
[[operator|operators]] it denotes, a [[builder|pullback]], expectations and
aggregations for a value statement of a [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks), and an alias
statement is substituted at its uses
([Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) R2).

## Two kinds of statement in a backward block

A statement whose right-hand side carries no [[sub_builder|value input]], `y = l + h + x`,
is a field equation: it extends the typing context with a derived field and
belongs to the field reading. A statement whose right-hand side carries a
value input, a continuation function, an expectation's result or a
sub-builder's output, is folded into operators, and only such a statement
may carry `!node` in a backward block. In a forward block every statement
is a field equation and a `!node` marks a [[sub_builder|sub-transition]].

## A property of a line

A statement attached to an operative line by a dotted id, as the
first-order condition `optimality.euler` is attached to the maximization
line `optimality`, is that line's **property**: it forms no row, no address
and no method place of its own, and it prints under the row of its line,
read at the point, with its id. A dotted id whose first part names no line
of its block is refused.

## A clause after a statement

A statement may carry a clause `⟂` after it, the [complementary slackness](../Bellman-Sym/10-constraints.md#3-the-complementary-slackness-clause)
between the statement's residual and a bound, as the candidate line of the
consumption stage does, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0`. The Kuhn–Tucker
condition of a policy block has three spellings, the clause on the
first-order condition, a declared multiplier and the clause on the
candidate line, and the three denote one relation
([Constraints](../Bellman-Sym/10-constraints.md) §§3 and 4).

## An occurrence is not a statement

An **occurrence** is an operator written inside a statement, `E_η(·)`,
`argmax`, `solve`; its result is a wire the construction makes, free in the
remaining coordinates, and only the operation's own method attaches to it.
Marking a statement `!node` is the only way to make an occurrence's result
a named object.

## Related concepts

[[semgraph]], [[sub_builder|sub-builder]], [[aggregation]], [[semgraph|initial diagrams]],
[[expression]].
