---
slug: builder
title: builder
tags:
- semgraph
- builder
- operator
- bellman-calculus
description: The operator a block of a stage denotes, one box at the builder grain, composing the pullbacks, expectations, aggregations and evaluation its statements fold to.
wiki_status: budding
last_reviewed: '2026-09-12'
reviewed_by: "Claude (session of 12 September 2026), at AAS's request; source-checked against the project's terminology and specification, the calculus chapter and the constructed buffer-stock stage"
updated: '2026-09-12'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/05-Operators and builders.md
  class: canonical
  date: '2026-09-12'
- path: docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
  class: canonical
  date: '2026-09-12'
- path: packages/bellman/bellman/native/hypergraphs.py
  class: code
  date: '2026-09-28'
audience: user
type: concept
---

# builder

A **builder** is the [[operator]] a block of a [[stage]] [[semantics|denotes]]. The block is
the authored text of the `.bl` file; the builder is what that text means,
and the two words are kept apart. The calculus defines a builder as a named
composition of operators constituting a stage's input-to-output interface
([Operators and builders](../bellman-calculus/05-Operators%20and%20builders.md) §6).
In the [[semgraph]] it is one box at the builder [[semgraph|grain]], a `Builder` bubble
whose name is the block's identifier, and opening the bubble shows the operators
it composes. A builder is reached from the stage by the ordered pair of
perches it joins, the key the package resolves whatever the block's
identifier, or from the [[perch]] its edge leaves; the policy builder is read
by its own key, `policy`.

## One builder per block

A [[stage|stage file]] writes one block for each edge it uses in each direction,
together with a policy block, and elaboration constructs one builder for
each. The buffer-stock stage has five, each reached from the perch its edge
leaves ([The builders graphs](../Bellman-Sym/API/stage/03-build.md) §2): the
forward builders `arvl_to_dcsn` and `dcsn_to_cntn`, at
`stage.arvl.builder.fwd` and `stage.dcsn.builder.fwd`; the backward builders
`cntn_to_dcsn` and `dcsn_to_arvl`, at `stage.dcsn.builder.bwd` and
`stage.arvl.builder.bwd`; and the policy builder, at
`stage.dcsn.builder.policy`. Each path reads one key of `stage.builder`, the
pair of perches its builder joins or, for the policy builder, the key
`"policy"`: `stage.dcsn.builder.bwd` is `stage.builder["cntn", "dcsn"]`.

The two directions act on different objects. A [[backward_builder|backward builder]] carries
value functions backward: $\mathbb T_\succ$ on the decision edge,
$\mathbb T_\prec$ on the arrival edge, composing into the stage operator
$\mathbb T = \mathbb T_\prec \circ \mathbb T_\succ$, with
$\mathbb T_{\succ,\pi}$ the **builder at a policy**, one operator for each
policy, whose signature is its inputs and its outputs and which is wired to
the policy builder at no level. A
[[forward_builder|forward builder]] transports probability measures along the same declared
transitions, $\mathbb M_\prec$ and $\mathbb M_{\succ,\pi}$, composing into
$\mathbb M_\pi = \mathbb M_{\succ,\pi} \circ \mathbb M_\prec$. The policy
builder is named separately from the backward builders. Its operations are
those the lines of the policy block form: an [`Argmax`](../Bellman-Sym/reference/operations.md#argmax) row for an operative
maximization line, an `Aggregation` for a relational line or a `solve`
line, the `Pullback` of the identification where the block writes the grid
line, and the Evaluation at its output
([operations](../Bellman-Sym/reference/operations.md)).

## Its signature

A **builder signature** is the builder's actual input and output [[semgraph|wires]], its
`dom` and `cod`. It is derived from the operator constructed from the block;
it is not a copy of the [[field|fields]] listed in the block header.
`stage.dcsn.builder.bwd.signature()` answers one record with two parts,
`inputs` and `outputs`, each wire with its type. On a controlled backward edge, a continuation
value function is an input and the **decision value function** is an output. The
control is the coordinate at which the operator is stated, not an input wire;
the policy is an index on the operator at a policy, not an argument of its
decision value function. The entry [[signature]] separates a builder signature from
the signature of a many-sorted algebra.

Opening a builder preserves its signature. The boxes that replace it must
keep the ordered input and output identities and types, the operation on
every admissible assignment of the free inputs, the conditions under which
the formulas are defined, local scope, conditional distributions and shared
dependencies ([[semgraph]]).

## What a builder composes

The [[statement|statements]] of a [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks) fold into [[operator|primitive operator]] boxes of three kinds, `Pullback`, `Expectation` and `Aggregation`,
emitted in the order the terms nest them, with an `Evaluation` at each
**evaluated field**, a field whose function stands on a wire under the field's
name ([operations](../Bellman-Sym/reference/operations.md)).

A **pullback** composes a continuation function with the block's
[[operator#Kernels|law of motion]], $K_g : v \mapsto v \circ g$; every term of function [[sort]] typed at
the continuation perch receives one. An **expectation** integrates the
shocks an occurrence $E_S(\cdot)$ names under the conditional distribution
selected from the edge's joint distribution; its output is a function of the
source coordinates and the conditioning shocks that selection keeps, and a
shock integrated on an earlier path is not restored. An
**aggregation** applies a map $G$ pointwise ([[aggregation]]): the
arithmetic inside an occurrence's brackets is one aggregation box before
that occurrence's expectation, and the arithmetic outside every occurrence
is one box per maximal pointwise segment. For a builder at a policy, the
policy indexes the pullback, aggregation or conditional distribution in
which it occurs. Evaluation then returns the resulting function under the
evaluated field's name and reads no policy.

Whether a statement writes its arithmetic inside or outside the occurrence
decides which mathematical order it denotes,
$B_\succ = \mathbb E_\mu \circ \operatorname{lift}(G) \circ K_g$ or
$B_\succ = \operatorname{lift}(G) \circ \mathbb E_\mu \circ K_g$, and the
fold never moves arithmetic across an expectation. A sub-term carrying no
[[sub_builder|value input]] is never a box: a named function applied to fields, a
[[parameters|parameter]], an expression in fields and shocks are addends,
factors and formal arguments of the aggregation's map. Evaluation at an evaluated field is the identity
on a function or on a set of feasible policies into that field's declared
carrier, subject to range compatibility; it makes no selection, reads no
policy and inserts none. A numerical method may store an interpolant as its
representation of a function without changing exact Evaluation. A statement
marked `!node` cuts a factor out of the composition, a [[sub_builder|sub-builder]].

## What a builder owns

Each backward builder defines the aggregator $G$ of its block. Each forward
builder owns one complete law of motion $g$, referenced by identity both by
its own push-forward and by the backward pullback of the paired edge:
`arvl_to_dcsn` supplies the map `dcsn_to_arvl` uses, and `dcsn_to_cntn` the
map `cntn_to_dcsn` uses. Distinct forward builders own distinct maps, and no
backward builder holds a $g$ of its own. A builder's identifier is the name
of its box, with no second copy of that name stored beside it.

## Grains

A grain chooses which boxes are opened within a graph. The builder grain
keeps every builder closed; the sub-builder, primitive, combined and
factored grains open it further, and they need not nest. A reader reaches the
two public grains by an attribute of the piece, `primitives` and
`sub_builders`, on a graph and on a builder alike. The mathematics of
opening is exact refinement: the builders are the symbols of a coarse
signature, a derived signature morphism assigns each of them a term over the
finer operations, $\delta(\mathbb T_\succ)v =
B_{\succ,s(B_\succ v)}v$, where
$s(B_\succ v)\in\operatorname{argmax}(B_\succ v)$ and the policy indexes
the relevant pullback, aggregation or conditional distribution, and
$\delta(\mathbb T_\prec) = B_\prec$, and initiality makes the resulting term
translation unique
([Appendix B](../bellman-calculus/APPX-B-INITIAL-ALGEBRA.md) §4).
A builder is primitive in one signature and composite in another, which is what
[[operator]] means by the two words; [[semgraph]] owns the graphs and the
grains.

## What a builder is not

A builder is not its block, which is text; not a stage, which composes
the builders of its edges; and not a numerical routine. A method attaches to
a place, and a place may be a declared function, an evaluated field, a builder or an operator
occurrence, but attaching one neither supplies a routine nor runs it
([[methodization]]). The [[bellman_operator|Bellman operator]] of a stage is
the composite $\mathbb T$, not any one of its builders.

## Its kernels

`kernels()` on a builder answers one record that refers to no stage: each
operation in the order of application, with the plain Python function its
[[operator#Kernels|kernel]] compiles to, or its printed relation where its rule is no explicit
function, the names of the function's arguments and outputs, the
parameters with the values the [[calibration]] binds, and, once the [[settings]]
are bound, the [[grid]] of each place within the builder that types one,
constructed at their values. A numerical operator is
constructed from such records without the stage in hand
([A builder](../Bellman-Sym/API/stage/04-builder.md) §5).

## Related concepts

[[backward_builder|backward builder]] and [[forward_builder|forward builder]] give the mathematics of the two
directions; [[sub_builder|sub-builder]] the factor a `!node` cuts; [[operator]] and
[[aggregation]] the boxes inside; [[statement]] the authored line;
[[semgraph]] the graphs and grains; [[stage]] what the builders compose into.
