---
slug: grid
title: Grid
description: The finite set of points of a function's domain at which a method computes and stores the function, written as the grid component of an operator's signature.
tags:
- methodization
- type
- grid
wiki_status: budding
last_reviewed: '2026-11-05'
reviewed_by: Claude (Fable), session of 5 November 2026, at AAS's request; written from the decisions of 4 November 2026 on the grid, checked against the Bellman calculus page on methods, and revised after one adversarial review round
sources:
- path: docs/bellman-calculus/06-Methods.md
  class: canonical
  date: '2026-11-05'
- reference: "Adámek, J., Herrlich, H. and Strecker, G. E. (2004). Abstract and Concrete Categories: The Joy of Cats. Free online edition (originally Wiley, 1990). Definitions 7.19 and 7.24, pp. 106–107."
  class: literature
  date: '2026-11-05'
- reference: "Carroll, C. D. (2006). The method of endogenous gridpoints for solving dynamic stochastic optimization problems. Economics Letters 91(3): 312–320. §2.2, p. 315."
  class: literature
  date: '2026-11-05'
audience: user
type: concept
---

# Grid

> [!summary]
> A **grid** is the finite set of points of a function's domain at which a numerical method computes and stores the function; between the points the method's interpolant supplies the values. It is the discretized domain, a typed object of the [[signature]] of the [[operator]] that holds the function, written at the operator's place as its own entry, `policy.grid : !Cartesian(a=(a_min, a_max, n_a))`, one factor per coordinate. A grid names [[settings]] and holds no number.

> [!info]- Relationship with other documents
> **Formal account** — [Methods](../bellman-calculus/06-Methods.md) §5: the grid as a finite subset of the domain and a representation as a section over it.
> **Builds on** — [[methods|Methods]]: the method component the grid stands beside; [[settings|Settings]]: the declared names a factor reads.
> **Used by** — [Methodization](../Bellman-Sym/04-methodization.md): the written form of a methods file; [Method types](../Bellman-Sym/reference/methods.md): the method words that read a grid.

## 1 What is written

A grid is written at the place of the operator whose function it discretizes, as the typing of the operator's grid component. The kind `!Cartesian` is a product of one node set per coordinate of the function, keyed by the coordinate's name as the [[stage|stage file]] declares it:

```bl
policy.grid : !Cartesian(a=(a_min, a_max, n_a))
dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k), p=(p_min, p_max, n_p))
cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_min, m_max, n_m, !expmult(nest=grid_phi)))
risk_ce.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m), ν=E_ν)
policy.grid : !Cartesian(c=(Γ_c, n_c))
```

A factor takes one of four shapes. A triple of declared settings gives the lower bound, the upper bound and the count of evenly spaced points, with an optional fourth element naming an uneven spacing by a word with its own keyword arguments: `!expmult(nest=grid_phi)`, the multi-exponential spacing, denser near the lower bound, whose nesting factor is the setting `grid_phi`, or `!geometric`, the geometric spacing. A declared node set, `m=M_nodes`, lists the points. The expectation operator whose quadrature nodes the coordinate takes, `ν=E_ν`, stands for a coordinate represented on a shock, as the smooth-ambiguity application's `risk_ce` is represented on resources and on the ambiguity shock. A control's factor is its feasible set with a count, `c=(Γ_c, n_c)`, where `Γ_c` is the set of feasible consumption the stage defines: the grid of a maximization lies in the states and the control it searches, so the feasible set at each state is discretized with that count. The spelling follows the EconForge interpolation library, whose uniform Cartesian grid is a tuple of lower bound, upper bound and count, one per axis. `!Cartesian` is the one kind of grid.

Every name in a factor is a declared setting, a declared node set, the feasible set of a control or an expectation operator of the stage; a number is refused. The settings are declared in the methods file with their domains, `n_a : ℕ`, `a_min : Xa`, and the values stand in the settings file ([[settings]]). At configuration the package checks each bound pair ordered and inside the coordinate's declared set, each count at least two and each node set strictly increasing; it checks nothing about accuracy.

## 2 The default and what lies outside

An operator that writes no grid entry has a grid of the kind `!Cartesian` over every state coordinate of the domain of the function it holds, in declared order: for the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that stores a builder's result, the states of the [[perch]] at which the stored function stands; for a solution method, the states its rows name, which for the endogenous grid method are the states of the continuation perch, the input perch of the policy [[builder]], since the method's grid is the predetermined grid of end-of-period assets from which the points of the policy are generated (Carroll 2006, §2.2, p. 315). The default fixes the kind and the coordinates and supplies no number; where a method needs bounds and counts, the entry writes them. The representation of the policy under `!egm` writes no grid: its knots are the pairs the method computes.

What a method does outside its grid, extrapolation or clamping at the bounds, is a keyword argument of the method word, `!Linear(extrap=clamp)`, and no part of the grid, which states its bounds only.

## 3 What a grid is not

A grid is a numerical object and no part of the model. A discrete set that belongs to the economics, such as the set of housing sizes a household chooses among, is a domain declared in the stage file, and the scalars that define it are [[parameters]]. A grid approximates a continuous domain and names settings. The grid is the object a representation is built on, and the representation, `!Linear` or `!pchip`, is a method: two methods over one grid store different functions between the same points.

Formally, a grid on a domain $X$ is a finite subset $G \subset X$ with its inclusion $\iota : G \to X$; restriction $r(f) = f \circ \iota$ takes a function to its values at the nodes, and a representation is an interpolant $s$ with $r \circ s = \mathrm{id}$, a section in the sense of Adámek, Herrlich and Strecker (2004, Definitions 7.19 and 7.24, pp. 106–107), so that the represented functions form a retract of the function space. [Methods](../bellman-calculus/06-Methods.md) §5 states this with its consequences. The inclusion of $G$ in $X$ is a map of sets and establishes no subsort relation ([[sort]]).
