---
slug: backward_builder
title: backward builder
tags:
- backward
- builder
- bellman-calculus
- operator
description: Choice-value construction, fixed-policy evaluation and optimization are separate backward operations
  on specified function classes.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/05-Operators and builders.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Backward builder

A **backward builder** is an [[operator]] that maps continuation value functions, which represent the value [[field|fields]] of the continuation perch, to choice values or earlier value functions using the declared transitions, payoffs and information. It is the [[builder]] of a [backward block](../Bellman-Sym/01-stage.md#3-builder-blocks) of a [[stage|stage file]]: the decision builder, `stage.dcsn.builder.bwd`, of the block `cntn_to_dcsn`, and the arrival builder, `stage.arvl.builder.bwd`, of the block `dcsn_to_arvl`, each reached from the [[perch]] its edge leaves by a path that reads the pair of perches it joins, `stage.builder["cntn", "dcsn"]` for the decision builder ([The builders graphs](../Bellman-Sym/API/stage/03-build.md) §2); the policy builder, `stage.dcsn.builder.policy`, stands beside them in the same graph and is read by a key of its own. Constructing a choice value, evaluating a supplied policy and optimizing that choice value are distinct operations.

## Choice values

Let $X$ be the state space at the decision [[perch]], $\Gamma(x)$ the feasible actions, $D=\{(x,a):a\in\Gamma(x)\}$ and $Y$ the continuation-state space. Let $g:D\times Z\to Y$ be a measurable [[operator#Kernels|law of motion]], $\kappa((x,a),dz)$ the conditional distribution of the shock, and $G(\ell,x,a,z)$ a scalar [[aggregation|value aggregator]]. For a continuation function $v:Y\to\mathbb R$ in a specified value class, define

$$
(Bv)(x,a)=\int G(v(g(x,a,z)),x,a,z)\,\kappa((x,a),dz).
$$

The chosen domain of $B$ requires the integral to be finite on every required feasible pair, with the output in the specified choice-value class. The order of aggregation and integration follows this displayed model; a nonlinear operation authored outside expectation must not be moved inside it. Discounting appears only where the defining equations include it.

A [[statement]] may apply a second map outside the integral, $(Bv)(x,a)=G^{\mathrm{out}}\bigl(\int G^{\mathrm{in}}(v(g(x,a,z)),x,a,z)\,\kappa((x,a),dz),x,a\bigr)$, the general form of Stages and perches §2.3a; the display above is its case with $G^{\mathrm{out}}$ the identity. In the [[semgraph]] the aggregation box that applies $G^{\mathrm{out}}$ reads the expectation's result as its [[sub_builder|value input]], and whether $G^{\mathrm{out}}$ is affine in that input is never a condition of construction.

A trajectory conditional expectation gives an identity along the observed random state and action. Recovering a pointwise choice-value function requires sufficient state information, representative functions and conditional distributions. An almost-sure identity under one policy cannot determine payoffs for every unchosen action.

## Policy evaluation and optimization

For a supplied feasible measurable policy $\pi$, define

$$
(T_\pi v)(x)=(Bv)(x,\pi(x)).
$$

For optimizing evaluation, the value is $\sup_{a\in\Gamma(x)}(Bv)(x,a)$ where that supremum belongs to the output domain. For a choice-value function $Q$, $\operatorname{argmax}Q$ is the **maximizing set**: the feasible measurable policies that attain the maximum of $Q(x,\cdot)$ over $\Gamma(x)$ at every state. The set may be empty, and it chooses none of its members. A **selection** $s$ is a partial map that chooses one member, $s(Q)\in\operatorname{argmax}Q$, and is defined only where that set is nonempty. With the insertion of a policy into a choice-value function, $\iota^{*}(Q,\pi)(x)=Q(x,\pi(x))$, a named selection from the maximizing set followed by the insertion of the selected policy gives

$$
T=\iota^{*}\circ
\langle B,s\circ B\rangle
\quad\text{on } \{v: Bv\in\operatorname{dom}s\},
$$

and $Tv$ is the same for every selection whose domain holds $Bv$, since every member of the maximizing set attains the maximum ([Operators](../bellman-calculus/catalogues/operators.md) §4). An operative `argmax` line of a stage file forms a row of kind [`Argmax`](../Bellman-Sym/reference/operations.md#argmax), whose output is the maximizing set ([operations](../Bellman-Sym/reference/operations.md#argmax)); the Evaluation that follows it selects no member, and the selection belongs to the numerical method bound to the row at [[methodization]] ([method types](../Bellman-Sym/reference/methods.md)).

This is the optimizing map, not evaluation under an arbitrary supplied policy. An unattained supremum need not have this representation. An Euler equation or root relation requires feasibility and optimality conditions before its solution can supply the optimizing policy.

## Stage composition

The decision-to-arrival builder integrates the declared arrival aggregator and pre-decision shock using its conditional distribution. Write it as $\mathbb T_\prec$, the decision-edge optimizing map as $\mathbb T_\succ$, and fixed-policy evaluation as $\mathbb T_{\succ,\pi}$. The stage maps are

$$
\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ,
\qquad
\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi},
$$

on compatible value spaces. If the arrival payoff aggregator is the identity, its builder reduces to an undiscounted transition expectation. A general reward-bearing arrival aggregator does not have that interpretation.

The entry [[forward_builder|forward builder]] states the probability/function pairing for transition expectations. It is not a transpose formula for the full Bellman update. See [Operators and builders](../bellman-calculus/05-Operators%20and%20builders.md) for the mathematical factors and [Field equations](../Bellman-Sym/03-field-equations.md) and [Methodization](../Bellman-Sym/04-methodization.md) for current `.bl` authoring and outer YAML attachments.
