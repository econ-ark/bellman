---
slug: grid
title: Grid
description: The finite set of points of a function's domain at which a method computes and stores the function, written as the grid component of an operator's signature.
tags:
- methodization
- type
- grid
wiki_status: budding
last_reviewed: '2026-11-10'
reviewed_by: Claude (Fable), session of 5 November 2026, at AAS's request; written from the decisions of 4 November 2026 on the grid, checked against the Bellman calculus page on methods, and revised after one adversarial review round; revised by Claude (Opus) on 10 November 2026 to the three grid constructors, their requirements and the realized grids of the package
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
> A **grid** is the finite set of points of a function's domain at which a numerical method computes and stores the function; between the points the method's interpolant supplies the values. It is the discretized domain, a typed object of the [[signature]] of the [[operator]] that holds the function, written at the operator's place as its own entry by one of three constructors: `!Cartesian`, a product of one node set per coordinate, `policy.grid : !Cartesian(a=(a_min, a_max, n_a))`; `!Points`, a finite set of declared points; and `!Fibred`, the feasible values of a control at each state of a base grid. A grid names [[settings]] or sets the stage defines, and holds no number.

> [!info]- Relationship with other documents
> **Formal account** — [Methods](../bellman-calculus/06-Methods.md) §5: the grid as a finite subset of the domain and a representation as a section over it.
> **Builds on** — [[methods|Methods]]: the method component the grid stands beside; [[settings|Settings]]: the declared names a factor reads.
> **Used by** — [Methodization](../Bellman-Sym/04-methodization.md): the written form of a methods file; [Method types](../Bellman-Sym/reference/methods.md): the method words that read a grid and the grid constructors.

## 1 What is written

A grid is written at the place of the operator whose function it discretizes, as the typing of the operator's grid component, and the entry holds one of three grid constructors, the words that say how the points are built. The constructor `!Cartesian` is a product of one node set per coordinate of the function, keyed by the coordinate's name as the [[stage|stage file]] declares it; at least one factor is written:

```bl
policy.grid : !Cartesian(a=(a_min, a_max, n_a))
dcsn_to_arvl.evaluate.grid : !Cartesian(k=(k_min, k_max, n_k), p=(p_min, p_max, n_p))
cntn_to_dcsn.evaluate.grid : !Cartesian(m=(m_min, m_max, n_m, !expmult(nest=grid_phi)))
risk_ce.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m), ν=E_ν)
policy.grid : !Cartesian(c=(Γ_c, n_c))
```

A factor takes one of four shapes. A triple of declared settings gives the lower bound, the upper bound and the count of evenly spaced points, with an optional fourth element naming an uneven spacing by a word with its own keyword arguments: `!expmult(nest=grid_phi)`, the multi-exponential spacing, denser near the lower bound, whose nesting factor is the setting `grid_phi`, or `!geometric`, the geometric spacing. A declared node set, `m=M_nodes`, lists the points. The expectation operator whose quadrature nodes the coordinate takes, `ν=E_ν`, stands for a coordinate represented on a shock, as the smooth-ambiguity application's `risk_ce` is represented on resources and on the ambiguity shock. A control's factor is its feasible set with a count, `c=(Γ_c, n_c)`, where `Γ_c` is the set of feasible consumption the stage defines: the grid of a maximization lies in the states and the control it searches, so the feasible set at each state is discretized with that count. Written in `!Cartesian` without `!Fibred`, such a factor states a family of grids of the control indexed by the states, one at each state, and no one grid of pairs. The spelling follows the EconForge interpolation library, whose uniform Cartesian grid is a tuple of lower bound, upper bound and count, one per axis.

The constructor `!Points(nodes=P)` is the finite set of the declared points `P`, each point written in the domain's declared coordinate order, and `!Points` alone is the empty grid. The points are a set the stage defines by its finite members, `B := {1, 2}`, or a setting declared on a fixed finite product of points, `P : ℝ₊ × ℝ₊ × ℝ₊`, which the settings file values by the list of its points; on a domain of two coordinates each point is a pair, declared through a product set, `X2 := ℝ × ℝ` and `P : X2 × X2 × X2`. Repeated points collapse in the set, and an interpolation may still require at least two points.

The constructor `!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))` pairs each state of the base grid with `n_c` points of the control's feasible set `Γ_c` at that state, so that its points lie in the graph of the feasible set, the set of feasible pairs of states and controls. The base is `!Points` or a `!Cartesian` term without feasible factors, and the fibre a `!Cartesian` term of feasible factors. At each state the package places the count of evenly spaced points on the closed feasible interval, both endpoints included: with `B := {1, 2}`, `Γ_c(m) := [0, m]` and `n_c = 2`, the grid is the four pairs (1, 0), (1, 1), (2, 0) and (2, 2). A feasible interval that is open or unbounded, and a fibre of several controls, whose joint sampling is not supported, are reported as unresolved and not sampled.

`!Cartesian` and `!Points` stand wherever a method reads a grid, and at a place with no method word whose [[handler]] reads it. `!Fibred` stands where the domain of the problem is the base's states followed by the fibre's controls: at a solution method that chooses over the controls on the states of its output perch, such as value function iteration, and at a representation only of a function of those states and those controls. It is refused at the continuation grid of the endogenous grid method, which holds no control, and at a representation of a function of the states alone.

Each constructor may end with `require=` and one predicate word, or a tuple of them, that the resulting grid must satisfy: `!Empty`, the grid holds no point; `!Cartesian`, the grid is nonempty and holds every combination of its projected coordinate values; `!NonCartesian`, the grid is nonempty and misses some combination of them; and `!UniformCartesian`, the grid is Cartesian on at least one real coordinate, with at least two distinct, equally spaced values in every coordinate. A requirement is a property of the grid and no further component, and the predicate `!Cartesian` is distinct from the constructor of the same name. Outside the fibre of `!Fibred` a requirement concerns the joint grid, and inside it the grid of the control at each state. The fibred grid above is `!NonCartesian`, since it misses the combination (1, 2) of its projected values, and the requirement `!Cartesian` there is refused at configuration. An unknown word, and two words that contradict each other, are refused where they are written.

Every name in a factor is a declared setting, a declared node set, the feasible set of a control or an expectation operator of the stage, and the points of `!Points` are a declared setting or a set the stage defines; a number is refused. The settings are declared in the methods file with their domains, `n_a : ℕ`, `a_min : Xa`, and the values stand in the settings file ([[settings]]). At configuration the package checks each bound pair ordered and inside the coordinate's declared set, each count at least two, each node set strictly increasing, each declared point's shape and finite coordinates, inside the coordinates' declared sets where that is decided, and each requirement that the bound values decide; it checks nothing about accuracy.

Once the settings are bound, the package constructs each grid at their values, and a builder's `kernels().grids` holds, for each place within the builder that types a grid, the realized grid, with its coordinates in declared order and its finite points, or the reason the construction cannot establish them and every required property, such as a coordinate that no factor names; no default is supplied ([A builder](../Bellman-Sym/API/stage/04-builder.md) §5).

## 2 The default and what lies outside

An operator that writes no grid entry has a grid of the kind `!Cartesian` over every state coordinate of the domain of the function it holds, in declared order: for the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that stores a builder's result, the states of the [[perch]] at which the stored function stands; for a solution method, the states its rows name, which for the endogenous grid method are the states of the continuation perch, the input perch of the policy [[builder]], since the method's grid is the predetermined grid of end-of-period assets from which the points of the policy are generated (Carroll 2006, §2.2, p. 315). The default fixes the kind and the coordinates and supplies no number; where a method needs bounds and counts, the entry writes them. The representation of the policy at the closing Evaluation of an `!egm` builder writes no grid entry, and one written there is refused: it reads the pairs of resources and consumption that the endogenous grid method computes at the savings on its grid, which give its nodes.

What a method does outside its grid, extrapolation or clamping at the bounds, is a keyword argument of the method word, its value a declared setting, as the durables application writes `!Linear(extrapolate=extrap_policy)` with `extrap_policy : {0, 1}`, and no part of the grid, which states its bounds only.

## 3 What a grid is not

A grid is a numerical object and no part of the model. A discrete set that belongs to the economics, such as the set of housing sizes a household chooses among, is a domain declared in the stage file, and the scalars that define it are [[parameters]]. A grid approximates a continuous domain and names settings. The grid is the object a representation is built on, and the representation, `!Linear` or `!pchip`, is a method: two methods over one grid store different functions between the same points. A representation may also be built from data that need no grid of its own, an authored table, the pairs of the endogenous grid method or the authored expression that `!closed_form` reads ([Methods](../bellman-calculus/06-Methods.md) §5).

Formally, a grid on a domain $X$ is a finite subset $G \subset X$ with its inclusion $\iota : G \to X$; restriction $r(f) = f \circ \iota$ takes a function to its values at the nodes, and a representation is an interpolant $s$ with $r \circ s = \mathrm{id}$, a section in the sense of Adámek, Herrlich and Strecker (2004, Definitions 7.19 and 7.24, pp. 106–107), so that the represented functions form a retract of the function space. [Methods](../bellman-calculus/06-Methods.md) §5 states this with its consequences. The inclusion of $G$ in $X$ is a map of sets and establishes no subsort relation ([[sort]]).
