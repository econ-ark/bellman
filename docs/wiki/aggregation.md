---
slug: aggregation
title: aggregation
tags:
- semgraph
- bellman-calculus
- operator
- backward
description: The pointwise aggregator G of a backward block and the aggregation operator that applies it; a statement may place one map inside the shock integral and another outside it, and the aggregation reads whatever wire the construction hands it.
wiki_status: budding
last_reviewed: '2026-09-12'
reviewed_by: Claude (session of 12 September 2026); source-checked against Stages and perches §2.3a, D23, D25 and AMD-SG-005
updated: '2026-09-12'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/03-Stages and perches.md
  class: canonical
  date: '2026-09-12'
audience: user
type: concept
---

<!-- synth: class=canonical, source=docs/bellman-calculus/03-Stages and perches.md, date=2026-09-12 -->
# aggregation

The **value aggregator** $\mathrm G$ of a [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks), a block of a
[[stage|stage file]] whose [[builder]] carries value functions backward, is the
pointwise map that combines a continuation value with the current state,
the control and the shock, $\mathrm G_\succ(v, x, a, \eta)$ on the decision
edge and $\mathrm G_\prec(v, x_\prec, \zeta)$ on the arrival edge. In
expected utility $\mathrm G_\succ(v, x, a, \eta) = \mathrm r(x, a, \eta) + \beta v$.
The **aggregation** is the [[operator]] of the [[semgraph]] that applies it
pointwise to the functions its [[semgraph|wires]] carry; its kind is `Aggregation`
([operations](../Bellman-Sym/reference/operations.md#aggregation)). A
drawing labels it `Value aggregation 𝐺` where it yields the value functions
of a [[perch]], and `Apply 𝐺` for a map inside an expectation's brackets,
whose result the expectation reads, and for a line of a policy block, which
yields a candidate control or a coordinate.

## Two maps around the integral

A [[statement]] of a backward block may apply one map to the continuation
value before the shock is integrated and another to the result afterwards,
so for one statement with one expectation the choice-value aggregator has
the general form
$$
B_\succ(x,a,\mathrm v_\succ)
=\mathrm G^{\mathrm{out}}_\succ\Bigl(\int_{\mathsf Z_\eta}\mathrm G^{\mathrm{in}}_\succ\bigl(\mathrm v_\succ(\mathrm g_\succ(x,a,\eta)),x,a,\eta\bigr)\,\mu_\eta(\mathrm d\eta),\,x,\,a\Bigr)
$$
([Stages and perches §2.3a](../bellman-calculus/03-Stages%20and%20perches.md#aggregation-inside-and-outside-the-integral)).
The form with the aggregation inside the integral, the canonical display
of §2.2, is the case $\mathrm G^{\mathrm{out}}$ the identity. The
reward-plus-discounted-expectation statement `V = u(c) + β·E_η(V[>])` is
the case $\mathrm G^{\mathrm{in}}$ the identity, and there the aggregation
reads the expectation's result $w$ as its [[sub_builder|value input]],
$\mathrm G(w, m, c) = \mathrm u(c) + \beta w$. An Epstein–Zin
recursion has both maps nonlinear. The two placements coincide exactly when
$\mathrm G^{\mathrm{out}}$ is affine in $w$; otherwise the placement is
part of the specification.

## How the construction treats it

The fold follows the authored order and never moves arithmetic across an
expectation. The arithmetic inside the brackets of an occurrence, an
operator such as `E_η(·)` written inside a statement, is one aggregation
box before that expectation; the arithmetic outside every occurrence is one
aggregation box per maximal pointwise segment, for a block without
sub-builders one box after the expectations, producing the block's output
functions. Whether a box's map is affine in its value inputs is never a
condition of construction: a nonlinear function of an expectation is
admitted as written. Re-timing the shock to its own edge, which exposes
the intermediate information set as a perch, is available and not
required.

In a policy block the same kind carries the lines that define a candidate
or a coordinate. A relational line, such as the candidate inequality
`c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0` of the consumption stage, forms one
`Aggregation` whose rule is that relation with its clause, and a `solve`
line one `Aggregation` of its residuals. The output of such a row is among
the unknowns of its own rule, so the row denotes a relation, and no kind of
its own ([operations](../Bellman-Sym/reference/operations.md) §4;
[Constraints](../Bellman-Sym/10-constraints.md) §4).

## The kernel's domain

Every [[operator#Kernels|kernel]] of a backward block, the builder's and every
[[sub_builder|sub-builder]]'s, is a function of the states of the perch at which the
builder produces its function, the controls bound at that perch, the shocks
the edge integrates, and its value inputs; the shock argument is present
only before the expectation that integrates it. Monotonicity of the **induced aggregator**
in the value follows when each map is nondecreasing in its value
argument, the condition a recursive decision process requires of its
aggregator ([[recursive_decision_process|recursive decision process (RDP)]]).

## Representation

The aggregation box's data is the identity of the block's G record, the
block's [[statement|value statements]] retained as immutable terms; which part of them a
box applies is its position in the term. No string and no callable is
stored: the printer gives the equation, and the box's `compile_kernel()`
answers one plain Python function whose arguments are the value inputs and
coordinates of the [[operator#Kernels|kernel]] and then each
[[parameters|parameter]] it reads, made from the source text
`kernel().python`, with the parameters' values passed at each call in the
order `kernel().parameter_values` holds them. A row whose rule has no
explicit side, such as a residual system, is refused under the rule
`kernel-target` ([refusals](../Bellman-Sym/reference/refusals.md)).

## Related concepts

[[backward_builder|backward builder]], [[sub_builder|sub-builder]], [[semgraph]], [[operator]],
[[statement]].
<!-- /synth -->
