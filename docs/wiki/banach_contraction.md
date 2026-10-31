---
slug: banach_contraction
title: Banach contraction theorem
tags:
- dp
- foundations
description: A contraction on a nonempty complete metric space has a unique fixed point and convergent exact
  iterates.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
updated: '2026-09-07'
needs_resolution: false
flags: []
sources:
- path: docs/bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md
  class: canonical
  date: '2026-09-07'
- reference: "Hernández-Lerma, O., Laura-Guarachi, L. R., Mendoza-Palacios, S. and González-Sánchez, D. (2023). An Introduction to Optimal Control Theory: The Dynamic Programming Approach. Springer. §2.3.3, pp. 44–49."
  class: external
  date: '2026-09-07'
- reference: "Stokey, N. L. and Lucas, R. E., Jr., with Prescott, E. C. (1989). Recursive Methods in Economic Dynamics. Harvard University Press. §3.2, Theorem 3.2, pp. 50–52."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Banach contraction theorem

Let $(X,d)$ be a nonempty complete metric space and $T:X\to X$ satisfy

$$
d(Tx,Ty)\leq q\,d(x,y)\quad\text{for all }x,y\in X,
\qquad 0\leq q<1.
$$

Then $T$ has a unique fixed point $x^*$ and its exact iterates satisfy

$$
d(T^n x,x^*)\leq q^n d(x,x^*).
$$

Completeness, closure under $T$ and a modulus strictly below one are essential hypotheses. Nonexpansiveness alone does not give this conclusion.

## Dynamic programming

A stationary [[bellman_operator|Bellman operator]] can satisfy these conditions on a specified space of bounded functions with the supremum norm. [[blackwell_conditions|Blackwell's sufficient conditions]] provides one sufficient test. Identifying the resulting fixed point with the economic value also uses the assumptions connecting the Bellman recursion to the policy problem.

For unbounded rewards, a weighted norm can be useful. Given a positive weight $w\geq1$, define $\|v\|_w=\sup_x|v(x)|/w(x)$ on a suitable complete function class. If a transition expectation $P$ satisfies $Pw\leq Cw$, constant discount $\beta$ gives a candidate modulus $\beta C$; the contraction argument requires $\beta C<1$ and closure of the full value update on that class. For an optimizing update, the same bound must hold uniformly across all feasible actions or policies in its transition family. Discounting alone is insufficient.

A finite-horizon model instead uses its terminal condition and backward recursion. A geometric truncation estimate from a stationary contraction applies only with the same [[operator]] and a finite initial distance in the chosen metric. Convergence of approximate iterates or approximate fixed points needs further error and stability assumptions; see [[adequacy]].

The theorem is used conditionally in [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md#6-model-interpretation-and-numerical-realization). It is not a source-language validation rule.

## References

- Stokey, N. L., and Lucas, R. E., Jr., with Prescott, E. C. (1989). *Recursive Methods in Economic Dynamics*. Harvard University Press, §3.2, Theorem 3.2, pp. 50–52.
- Hernández-Lerma, O., Laura-Guarachi, L. R., Mendoza-Palacios, S., and González-Sánchez, D. (2023). *An Introduction to Optimal Control Theory: The Dynamic Programming Approach*. Springer, §2.3.3, pp. 44–49, for the weighted-norm approach.
