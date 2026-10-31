---
slug: initial_algebra
title: Initial algebra
tags:
- foundations
- universal-algebra
- category-theory
description: Unique interpretation of ground terms, or free terms under an assigned environment, in a specified
  target algebra.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
merged_from:
- f_algebra
sources:
- path: docs/bellman-calculus/APPX-B-INITIAL-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- reference: "Goguen, J. A., Thatcher, J. W., Wagner, E. G. and Wright, J. B. (1977). Initial Algebra Semantics and Continuous Algebras. Journal of the ACM 24(1): 68–95. §1, Proposition 1.1; §2, Propositions 2.1, 2.3 and 2.6, pp. 71–75."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Initial algebra

An **initial algebra** is an algebra from which there is exactly one structure-preserving homomorphism to every algebra in the specified category. For an ordinary many-sorted signature, the ground term algebra has this property. The target operations must already be supplied; initiality does not choose their meanings or prove their analytic assumptions.

## Ground terms and free inputs

A [[signature]] specifies [[sort|sorts]] and typed operation symbols. Its ground terms contain no free inputs. Their interpretation in a target algebra $A$ is the unique homomorphism $T_\Sigma\to A$.

For terms with free input names $X$, use the free algebra $T_\Sigma(X)$. An environment assigns each input a value of its declared sort in $A$. There is a unique homomorphism extending that environment. Different environments or target operations can give different interpretations; uniqueness is conditional on those choices.

Goguen, Thatcher, Wagner and Wright (1977), §2, Proposition 2.1, p. 71, establishes initiality of the many-sorted term algebra. Their Propositions 2.3 and 2.6, pp. 72 and 75, give the free-input extension. Their Proposition 1.1 states uniqueness of an initial algebra up to isomorphism within the specified category.

## F-algebras

For an endofunctor $F:C\to C$, an **F-algebra** consists of an object $A$ and a map $\alpha:F(A)\to A$. A homomorphism $h:(A,\alpha)\to(B,\gamma)$ satisfies $h\circ\alpha=\gamma\circ F(h)$. An initial F-algebra, when it exists, has exactly one such homomorphism into every F-algebra.

For a one-sorted operation signature, the polynomial functor $F_\Sigma(X)=\coprod_{\omega\in\Sigma}X^{n_\omega}$ records the argument count $n_\omega$ of each symbol. Its initial algebra is the ordinary ground term algebra, with the appropriate convention for empty carriers. A many-sorted version instead acts on families of sets indexed by the sorts. This construction is a mathematical description, not an identification with a particular software graph.

## Application to the Bellman calculus

In the [[bellman_calculus|Bellman calculus]], a coarse [[builder]] can be assigned a finer expression of the same type. Exact interpretation agrees with that expansion when the target uses those assigned operations and the same free inputs. If the theory imposes equations, the expansion must respect them. Numerical approximation needs a separate argument; see [[adequacy]].

Source binding, implicit equations and graph storage have additional requirements. [[sym|Bellman-SYM]] uses a transient **parsed AST** (abstract syntax tree) and a retained [[semgraph]] (semantic graph). Shared term evaluation preserves meaning under the required purity and input assumptions; it does not equate sharing one random draw with independent resampling. Initiality establishes neither runtime correctness nor an automatic functor from the [[semgraph|initial diagrams]], the graphs of a [[stage]] on its [[field|fields]], to the builders graphs, on functions; *initial* there names the graph elaboration constructs first and not an initial algebra.

See [Initial-algebra semantics](../bellman-calculus/APPX-B-INITIAL-ALGEBRA.md), [[bellman_algebra|Bellman algebra]] and [[lawvere_theory|Lawvere theory]].
