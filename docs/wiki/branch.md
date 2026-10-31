---
slug: branch
title: branch
tags:
- semgraph
- bellman-calculus
- grammar
- forward
- backward
description: One alternative of a discrete choice with its own continuation, written as a labeled nested block; a summand of the continuation state space and a bubble of the forward initial diagram, selected backward by the aggregation of the selection line and forward by the push-forward at the policy.
wiki_status: budding
last_reviewed: '2026-09-24'
reviewed_by: Claude (session of 24 September 2026, the first build of branching); source-checked against D02, the specification §3.2.1, Appendix F §5, the D24 record of 12 September and the decisions of step F
updated: '2026-09-25'
needs_resolution: false
flags: []
sources:
- path: docs/Bellman-Sym/05-branching.md
  class: canonical
  date: '2026-09-24'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-12'
audience: user
type: concept
---

<!-- synth: class=canonical, source=docs/Bellman-Sym/05-branching.md, date=2026-09-24 -->
# branch

A **branch** is one alternative of a discrete choice, with its own
continuation state and its own section of the [[operator#Kernels|law of motion]]: work or
retire, adjust or keep. In a [[stage|stage file]] the decision-to-continuation [block](../Bellman-Sym/01-stage.md#3-builder-blocks)
declares the **label coordinate**, a control typed by the finite set of
labels, `d : !ctrl @ {work, retire}`, and contains one labeled nested block
per branch defining that branch's continuation [[field|fields]]; the [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks)
lists the per-branch continuation values as separate fields and selects
among them by tuple selection indexed by the label coordinate, and the
maximization line of the policy block, over the same tuple, forms a row of
kind [`Argmax`](../Bellman-Sym/reference/operations.md#argmax), whose output is the set of policies that choose a largest
entry ([Branching](../Bellman-Sym/05-branching.md) §§1 and 3). A
stage is branching if and only if that block has labeled nested blocks;
nothing else declares it.

## The mathematics

The continuation state space is a disjoint union of the branches' spaces,
$\mathsf X_\succ = \bigsqcup_{j \in J} \mathsf X_{\succ, j}$ (the operator
algebra, Appendix F §5), one **summand** per label, named by the fields its
branch writes: in the retirement choice the summand of `work` is the set of
`a_w` and the summand of `retire` the set of `a_r`. The label adds no
[[perch]] and is no state field. A function on a disjoint union is the tuple of its
restrictions to the summands, and a finite measure on it the tuple of its
restrictions, so a continuation value is the tuple of the branches' values,
each a function on its own summand.

In the [[semgraph]] the branching block `dcsn_to_cntn` is one box of the
forward [[semgraph|initial diagram]], whose outputs are the fields of every branch,
`a_w` and `a_r`, in label order. Each branch is a bubble inside it,
`dcsn_to_cntn.work`, holding the block's lines read at that label. The
block owns one law of motion, and its **section** at a label,
`𝑔_work≻ = 𝑔≻(·, work)`, is an abbreviation of the builder that reads it.
Each branch value is typed on its own summand, the branch at whose position
it stands in the selection tuples, and no [[semgraph|wire]] carries a label in its type:
the wire of `a_w` is `ret_choice:cntn:a_w`. The branches meet the rest of
the [[builder|builders]] at two [[operator|operators]] of the existing kinds. Backward, the
**selection** is the aggregation of the selection line, whose [[operator#Kernels|kernel]] is the
tuple indexed by the label, `(V_w[>] - δ, V_r[>])[d]`, read at the policy
after one [[builder|pullback]] per branch along its section; the maximization over the
label that the choice line writes is that line's own `Argmax` row and not
the selection. Forward, the **fork** is
the push-forward at the policy into the disjoint union, one measure per
label: the mass of the decision states the policy sends to that label,
pushed along its section. Since the policy sends every decision state to one
label, and where every branch line writes into its field's declared set, the
masses of the branch measures sum to the mass of the decision measure; the
package records this as a condition, established for `ret_choice` and
required for `tenure`, whose keep line's range is not established.
A branch may also be drawn by nature: the label is then a shock with its
probability distribution, the value is the branch values weighted by that
distribution, Σ_j p(j | x) Q_j(x), and the fork is the push-forward of the
measure extended by the distribution, routed by the drawn label.

## Branch against sub-builder

A labeled branch block is a bubble inside the forward block of the initial
diagram, as a [[sub_builder|sub-builder]] is a bubble inside a builder, and the two are
told apart by role, not by depth. A
sub-builder is a factor of the builder's sequential composition on a
sub-tensor of wires, so that opening it preserves the morphism. A branch
bubble holds the block's lines read at its label and names one summand of
the continuation space, joined to the others only by the fork or the
selection; it cannot be inlined into a neighbor. No builders graph holds a
bubble for a branch: there the branches are wires and boxes of the
existing kinds. The name forms record the distinction: the label stands in
the address, `dcsn_to_cntn.work`, against a [[statement]] address,
`policy.InvEuler`. A sub-builder may sit inside one branch's slice or
around the selection statement, never across part of the selection's
tuple.

## Branching stages in the applications

The finite-branch interpretation is stated in
[Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md) §5. A
stage whose branches a control selects is constructed, the retirement
choice `ret_choice.bl` and the durables model's `tenure.bl` among them, and
so is a stage whose branches a shock selects, as the worker's aging stage
`worker_ageing.bl` of the Cagetti–De Nardi application. The
[branching guide](../Bellman-Sym/05-branching.md) states what a branching
block may contain.

## Related concepts

[[semgraph]], [[sub_builder|sub-builder]], [[forward_builder|forward builder]], [[backward_builder|backward builder]],
[[stage]].
<!-- /synth -->
