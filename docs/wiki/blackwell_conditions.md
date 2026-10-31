---
slug: blackwell_conditions
title: Blackwell's sufficient conditions
tags:
- dp
- foundations
description: Monotonicity and a discounted constant-shift bound imply contraction on a closed bounded-function
  domain.
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
- reference: "Hernández-Lerma, O., Laura-Guarachi, L. R., Mendoza-Palacios, S. and González-Sánchez, D. (2023). An Introduction to Optimal Control Theory: The Dynamic Programming Approach. Springer. §2.3.3, Proposition 2.36 and Theorem 2.38, pp. 47–49."
  class: external
  date: '2026-09-07'
- reference: "Stokey, N. L. and Lucas, R. E., Jr., with Prescott, E. C. (1989). Recursive Methods in Economic Dynamics. Harvard University Press. §3.2, Theorem 3.3, p. 54."
  class: external
  date: '2026-09-07'
audience: user
type: concept
---

# Blackwell's sufficient conditions

Blackwell's conditions provide a sufficient test for a contraction. Let $B(X)$ be the bounded real-valued functions on a nonempty set $X$, equipped with the supremum norm, and let $T:B(X)\to B(X)$. Assume:

1. $f\leq g$ implies $Tf\leq Tg$.
2. For some $0\leq\beta<1$, every $f\in B(X)$ and constant $c\geq0$ satisfy $T(f+c)\leq Tf+\beta c$.

To see the contraction bound, set $d=\|f-g\|_\infty$. Since $f\leq g+d$, the two conditions give $Tf\leq Tg+\beta d$. Interchanging $f$ and $g$ gives the reverse bound, hence

$$
\|Tf-Tg\|_\infty\leq\beta\|f-g\|_\infty.
$$

The same argument applies on bounded measurable functions when $T$ maps that space into itself. [[banach_contraction|Banach contraction theorem]] then gives a unique fixed point and convergence of exact iteration.

## Application and limits

An additive discounted Bellman update often has these properties when its rewards, feasibility and transitions ensure a bounded output. Positive rewards or costs alone do not establish that closure. Existence of a maximizing policy is also separate from the contraction inequality for a supremum-value update.

For a weight $w\geq1$, an analogous argument uses $f\leq g+dw$ and a bound $T(f+cw)\leq Tf+qc w$ for $c\geq0$ and $q<1$ on a specified complete weighted function space. The model must provide the corresponding reward and transition-growth bounds. This is useful for some unbounded problems, not a theorem for every lifecycle model.

These are mathematical assumptions to check for an interpreted [[operator]]. EGM, Euler equations and a method assignment do not establish them. See [Operator algebra](../bellman-calculus/APPX-F-OPERATOR-ALGEBRA.md) and [[bellman_operator|Bellman operator]].

## References

- Stokey, N. L., and Lucas, R. E., Jr., with Prescott, E. C. (1989). *Recursive Methods in Economic Dynamics*. Harvard University Press, §3.2, Theorem 3.3, p. 54.
- Hernández-Lerma, O., Laura-Guarachi, L. R., Mendoza-Palacios, S., and González-Sánchez, D. (2023). *An Introduction to Optimal Control Theory: The Dynamic Programming Approach*. Springer, §2.3.3, Proposition 2.36 and Theorem 2.38, pp. 47–49, for the weighted-norm argument.
