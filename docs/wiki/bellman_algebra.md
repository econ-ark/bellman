---
slug: bellman_algebra
title: Bellman algebra
tags:
- foundations
- bellman-core
- bellman-calculus
- semantics
- universal-algebra
description: A specified signature, its formal terms and chosen mathematical operations; interpretation and
  analytic validity remain distinct.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Bellman algebra

An **algebra** assigns mathematical sets and operations to a specified [[signature]]. In the [[bellman_calculus|Bellman calculus]] these include chosen value-function and distribution spaces, transition operations, payoff aggregation and policy evaluation or selection. This use of “operator algebra” concerns their composition, not an algebra of bounded linear operators from functional analysis.

## Terms and interpretations

A signature lists [[sort|sorts]] and operation symbols with input and output types. Its term algebra $T_\Sigma$ consists of formal expressions built from those symbols. A target algebra $\mathcal B$ assigns a carrier set to each sort and an operation of the required type to each symbol. The interpretation $\Upsilon$ maps terms to their mathematical meanings.

Once the target operations are fixed, ground terms have a unique homomorphic interpretation. Terms with free inputs also require an environment assigning those inputs. [[initial_algebra|Initial algebra]] gives that result and distinguishes it from assumptions about domains, binding and software representation. If additional equations are imposed on the terms, the interpretation must satisfy them; associativity or monotonicity alone does not determine an algebra up to isomorphism.

A categorical presentation needs its own objects, morphisms and equations. A [[lawvere_theory|Lawvere theory]] model is a finite-product-preserving functor from the specified theory to sets. A many-sorted signature alone does not establish that all Bellman graph operations have this structure.

## Bellman operations

A [[backward_builder|backward builder]] can construct choice values, evaluate a supplied policy, or optimize when the appropriate selection exists. A [[forward_builder|forward builder]] propagates probability through transitions under a supplied policy. Both are [[builder|builders]], the operators the [blocks](../Bellman-Sym/01-stage.md#3-builder-blocks) of a [[stage|stage file]] denote, and they use different domains. The probability/function pairing relates forward transport to undiscounted transition expectation, not to reward-bearing optimization.

The [[bellman_operator|Bellman operator]] is one recursive value update. An [[abstract_decision_process|abstract dynamic program (ADP)]] describes a value space and a family of policy self-maps, while a [[recursive_decision_process|recursive decision process (RDP)]] additionally specifies feasible actions and an aggregator. These are useful comparisons with parts of the Bellman interpretation, not identities with the entire many-sorted algebra.

## Mathematical terms and stored graphs

A finite acyclic term graph can share repeated subexpressions. For pure operations with identical input assignments, evaluating a shared subterm once agrees with evaluating its copies. Sharing a random draw and independently resampling are different operations.

This mathematical account does not prescribe parser storage. [[sym|Bellman-SYM]] parses `.bl` source into a temporary **parsed AST** (abstract syntax tree) and constructs a retained [[semgraph]] (semantic graph). Authored names and boundaries can distinguish graphs with equal mathematical [[semantics|denotations]]. Functional interpretations require the premises stated in [Syntax to semantics](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md).

See [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md) for the target structures and [[operator]] for the symbol/operation distinction.
