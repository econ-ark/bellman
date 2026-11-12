---
slug: operator
title: operator
tags:
- foundations
- operator
- universal-algebra
- semantics
- bellman-calculus
description: Operation symbols, mathematical interpretations and numerical routines are distinct; primitive
  status depends on the chosen signature.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
merged_from:
- primitive_operators
- mathematized_operator
sources:
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/catalogues/operators.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Operator

An **operation symbol** names an operation in a [[signature]] and has a [[rank]], its input sorts and its output sort ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §3). Its interpretation is a mathematical map on the chosen domains. For example, the [[builder|pullback]] maps a continuation function to its composition with the law of motion.

The symbol and its interpretation are distinct. A first-order signature can treat an operation solely as a symbol without introducing operator-valued data. This is a choice of signature, not a claim that a mathematical operator can never be a function or an element of a function space. In a specified category, a typed operation may be represented as a morphism.

## Primitive and composite operations

An operation is **primitive relative to a signature** when it is taken as a generator. It is **composite** when it is expressed using other operations. A whole builder can be primitive in a coarse signature and have a composite expansion in a finer one. Calling a transition-induced operation “induced” describes how its meaning is supplied; it does not by itself determine whether the chosen signature treats it as primitive.

For the graphs and the inspection [[semgraph|grains]] of the [[semgraph]] (semantic graph), see that entry. Natural Bellman primitives include whole law-of-motion and scalar aggregator definitions. Authored nodes can contain several primitives or name part of one; arithmetic remains inside the complete definitions, not an additional advertised grain. Primitive status in a mathematical signature and the named primitive inspection grain should not be treated as a proof of the same representation at every level.

The [operator catalogue](../bellman-calculus/catalogues/operators.md) lists the mathematical operations. The entries [[backward_builder|backward builder]] and [[forward_builder|forward builder]] explain their value and probability domains. A selected maximum is a composite of choice-value construction, a selection from the maximizing set and the insertion of the selected policy, defined only on a domain where the stated selection exists.

## The operations of a builder

In a [[stage]], an operator is what a box of the backward or the forward builders graph denotes, and inside a [[builder]] the word means a **primitive operator**, the finest box. Each primitive operator is of one operation kind, the name under which the package lists it among the operations of a builder: `Pullback`, `Aggregation`, `Expectation`, `Evaluation` and [`Argmax`](../Bellman-Sym/reference/operations.md#argmax) in the backward builders graph, and `Pushforward` and `DistributionExtension` in the forward one ([operations](../Bellman-Sym/reference/operations.md) §2; [Operators](../bellman-calculus/catalogues/operators.md) §4). A relation, the rule of an `Aggregation` or a `Pullback` whose output is among its own unknowns, is no operation kind of its own. The package's table also defines `PolicyInsertion`, the insertion of a policy into a choice-value function, which no stage of the applications forms as a row of its own: at a policy the insertion is part of the indexed pullback or push-forward. The builder is the operator of a whole [block](../Bellman-Sym/01-stage.md#3-builder-blocks), and a [[sub_builder|sub-builder]] is the one box inside a builder that is not primitive.

## Kernels

A **kernel** is the mathematical data an operator uses: a law of motion for a pullback or a push-forward; a [[aggregation|value aggregator]] for an aggregation; a **shock probability distribution**, the distribution a `~` line of the [[stage|stage file]] declares for a shock, read as conditional on the information at the edge's source perch ([Shock distributions](../Bellman-Sym/reference/laws.md)), for an expectation or a distribution extension; a correspondence; or a policy reference, which at a policy is part of the indexed law of motion, aggregator or distribution. A **law of motion** is the map from the states of a [[perch]], with the control and the shock where the edge has them, to the states of the next perch; the forward block of the edge declares it. A kernel's [[signature|inputs and outputs]] are its arguments, which are points, while an operator's are its [[semgraph|wires]], which carry functions or measures. `kernel()` on an operation answers the kernel's line with its defining records under `origins`, and `compile_kernel()` the plain Python function made from the kernel's text, `kernel().python`, whose arguments are the kernel's own and then the parameters it reads ([A piece](../Bellman-Sym/API/stage/05-piece.md) §2). In Backus's sense a kernel is the parameter of the operator's form, never an economic [[parameters|parameter]].

## Mathematical interpretation

A **mathematized operator** is an operation supplied with its mathematical interpretation. The interpretation can remain parameterized; it need not have a numerical method or a fully chosen [[calibration]]. This is the same symbol/interpretation distinction, not an additional kind of runtime object.

Declared names also identify authored occurrences and boundaries. Two differently named equations may denote the same function without becoming one retained node. Equal ranks do not imply equal operations, and equal [[semantics|denotations]] do not erase method-attachment addresses.

A method specifies a numerical procedure ([[methodization]]); a [[handler]] is the package routine intended to compute it. Their correctness requires the domain and approximation checks in [[adequacy]]. [[initial_algebra|Initiality]] explains unique composition under fixed mathematical assignments, not the correctness of arbitrary routines.

See [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md) and [Equation boundaries and indexing](../Bellman-Sym/appendices/15-appendix-d-node-tag-and-field-indexing.md).
