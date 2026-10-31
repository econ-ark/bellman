---
slug: sub_builder
title: sub-builder
tags:
- semgraph
- builder
- operator
- backward
- bellman-calculus
description: The operator a statement marked `!node` denotes inside a backward builder, a factor of the builder's composition on the wires its statements read, with its own aggregation, a possible expectation and an evaluation at its output.
wiki_status: budding
last_reviewed: '2026-09-12'
reviewed_by: "Claude (session of 12 September 2026); source-checked against the project's specification and the rulings of 12 September"
updated: '2026-09-12'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
  class: canonical
  date: '2026-09-12'
audience: user
type: concept
---

# sub-builder

A **node statement** is a [[statement]] of a [block](../Bellman-Sym/01-stage.md#3-builder-blocks) that the author marks
`!node`, thereby making its left-side [[field]] an [[builder|evaluated field]]: an expected
continuation value, a post-decision value, or a candidate consumption
function. An **intermediate function** formed by a subexpression remains
unnamed. The **sub-builder**
is the [[operator]] that statement denotes inside its [[backward_builder|backward builder]]. The
pair follows block against [[builder]]: the block and the node are authored
text, the builder and the sub-builder are what they denote. In the
[[semgraph]] a sub-builder is a bubble inside the builder's bubble, named by
the statement's address; in code the [[semgraph|grain]] at which sub-builders are closed
keeps the token `node`, and prose says "the sub-builder grain". Never call
the operator a node, and never call a branch a node (see [[branch]]).

## The slice and the cut

The statements a node's statement depends on, cut at earlier nodes and at
the block's inputs, form its **slice**. Read as one operator, the slice is a
factor of the builder's sequential composition on the sub-tensor of [[semgraph|wires]] it
reads: a **cut** in the sense of the calculus's Appendix B §5, and opening
the bubble and composing its interior leaves the builder unchanged by the
factorization theorem of Appendix B §4. The same word names the statements
any wire depends on, so the slices of a builder's outputs, one for each
output wire, are its parallel strands, parallel when they share no statement and meeting at a
copy where they do.

## What a sub-builder contains

Inside the bubble the same fold as for the containing builder applies to the slice: the
[[builder|pullback]] of every continuation function it reads along the block's
[[operator#Kernels|law of motion]], then its pointwise aggregations and expectations in the authored
order, then identity evaluation on the resulting function into the evaluated
field's declared carrier. Its G's are the maps of its [[aggregation]]
boxes, one inside and one outside each expectation it contains; they are
not separate authored definitions but the slice of the block's one G record
that its statements form. The [[signature|inputs and outputs]] of a sub-builder are its
domain and codomain tensors, `dom` and `cod`; "boundary" is reserved for
"the evaluation at a sub-builder's output".

## Its signature and kernels

A sub-builder's signature consists of the function wires it actually reads
and writes. Its output is a function on the coordinates left after the
shocks named by its expectations have been integrated, restricted to the
feasible pairs when a control is among those coordinates. The control is a
coordinate of that function, not a separate input wire. Its [[sort]] records
the coordinates on which the function varies.

A [[operator#Kernels|kernel]] is the mathematical data an operator uses; a
policy used by a builder indexes its pullback, aggregation or conditional
distribution. These kernels have different domains and must not all be
assigned the scalar aggregator type
$G : \mathsf L^{m} \times \mathsf X \times \mathsf A \times \mathsf Z \to \mathsf L$.
The compiled callable for such data is the compiled kernel.

A **value input** is a value function, its derivative read by a derivative
term such as `D_{a}V[>]`, or any function formed by composing one into an
expression: the pulled-back continuation
function $v \circ g$, an expectation's result, an aggregation's output, or
a sub-builder's output. An unmarked line's left-side field is not evaluated;
its expression is substituted where used. The `!node` mark instead makes the
line's left-side field an evaluated output and adds its evaluation. The
output is a value when every value input is a value. A line whose left side
is a derivative term is a derivative line: it states a derivative of the value
its builder writes and adds no output.

## Grains, [[semgraph|parallel wires]] and branches

At the sub-builder grain each sub-builder is a closed bubble and its output
cuts a pointwise segment. At the primitive grain every bubble is open, only
the sub-builders' identity evaluations are dropped, and adjacent pointwise
aggregations merge by composing their terms, never across an expectation or
two parallel paths; a merged box keeps its place after [[calibration]]. Each
slice constructs its own copy of an unmarked statement it shares with another
slice, and slices share only earlier sub-builder outputs and the block's
inputs, a block input two slices read being substituted in each. A [[branch]] is a bubble
of the forward [[semgraph|initial diagram]] and no sub-builder; a sub-builder may sit inside one branch's
slice or around the selection statement, never across part of the selection's tuple.

## Forward blocks

A `!node` in a forward block marks a **sub-transition**, a factor of the law
of motion $g = g_2 \circ g_1$, which the two readings inherit as
$(g_2)_\# \circ (g_1)_\#$ on measures and $K_{g_1} \circ K_{g_2}$ on
functions. Forward markers are preserved, and g is not split at them. The
rule that a sub-builder maps value inputs to value inputs is a rule for
[backward blocks](../Bellman-Sym/01-stage.md#3-builder-blocks).

## Related concepts

[[semgraph]] owns the graphs, grains and [[semgraph|value bundles]]; [[aggregation]] the
kernel G and its two maps; [[statement]] the authored line and its record;
[[branch]] the discrete alternatives; [[backward_builder|backward builder]] the operator a
backward block denotes.
