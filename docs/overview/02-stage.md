---
title: The stage
tags:
  - bellman-sym
  - user-facing
  - stage
  - perch
  - field
status: Draft
related:
  - "[[01-stage]]"
  - "[[03-Stages and perches]]"
date: 2026-09-19
audience: user
type: overview
---
# The stage

#stage

> [!summary]
> We use a simple buffer-stock model to introduce the structure of a stage, a self-contained decision problem with three perches corresponding to the information sets at arrival, decision and continuation. Its economic quantities are fields, classified by role, by declared set and, except for shocks, by perch, and related across perches by two laws of motion and a value aggregator. The stage file states this theoretical model alone, as a **symbolic stage**.

A **stage** is a self-contained decision problem whose description uses no information or notation from elsewhere in the model. It can be viewed as a description of a **Bellman operator**, expressed through objects typed according to the **Bellman calculus**, Project Bellman’s type system. These types are general enough to represent any Bellman operator of a recursive decision process.

## 1 Structure of a stage

To make this concrete, consider a consumption–saving problem with i.i.d. income and no borrowing, the simplest buffer-stock model. The normalized buffer-stock model adds permanent shocks and income growth; here, the sequence within the stage is:

1. The household arrives with assets `b`.
2. Income `y` is drawn from a lognormal distribution, giving the household market resources `m = R*b + y`, where `R` is the gross return.
3. It chooses consumption `c`, subject to `0 < c ≤ m`.
4. It leaves with savings `a = m - c`, which it takes into the next stage.

Stage utility is `𝑢(c) = c^(1-ρ)/(1-ρ)`, with constant relative risk aversion `ρ > 1`. Before introducing the value functions and Bellman equation, we place these economic quantities at their respective perches.

### 1.1 Perches

#perch

A **perch** identifies a point in the stage by the information available to the household there—its viewpoint, hence the name. The stage begins at the **arrival** perch, before any within-stage shock has been drawn or decision made. Once the observable shocks have been revealed, the household reaches the **decision** perch, where it makes its choice. The **continuation** perch follows that choice.

In our example, step 1 is the arrival perch, where `b` is known. Steps 2 and 3 place the household at the decision perch, where it knows its resources `m` and chooses `c`, while step 4 is the continuation perch, where savings `a` are known.

The perch indices are `<` ($\prec$) for arrival, `>` ($\succ$) for continuation and `~` ($\sim$) for decision, with the decision mark usually omitted.

### 1.2 Fields

#fields

The economic quantities of a stage—assets `b`, income `y`, resources `m`, consumption `c`, savings `a` and the value at each perch—are called **fields**. A field appears in stage equations much as a variable does in a paper, but the term makes its mathematical classification explicit. In conventional notation, a *variable* may be a number, a vector, a random variable, a realization or a function of the state, with the distinction left to context.[^1]

For a stage file to determine a Bellman problem, each object must instead have a well-defined type. A field is classified by its **role**, which is state, control, shock, value or the multiplier of a constraint ([Constraints](../Bellman-Sym/10-constraints.md) §4.2), by its **declared set**, the set in which its values lie, and, unless it is a shock, by its **perch**. Its type states this classification. Together with the stage’s equations, which state the kernels (§1.3), the types of the fields determine the stage’s [semantic graph](../wiki/semgraph.md).

In the buffer-stock model, the value field is written `V[<]` at arrival, `V` at decision and `V[>]` at continuation. Parameters such as `β` and `R`, by contrast, are not fields: they are declared with their sets and receive values at [calibration](../wiki/calibration.md).

The table summarizes the fields of the example.

| Field | Perch | Role | Declared set |
|---|---|---|---|
| `b`, assets | arrival | state | $\mathbb R_+$ |
| `y`, income | drawn between arrival and decision | shock (lognormal) | $\mathbb R_{++}$ |
| `m`, resources | decision | state | $\mathbb R_{++}$ |
| `c`, consumption | decision | control | $\mathbb R_{++}$ with `c ≤ m` |
| `a`, savings | continuation | state | $\mathbb R_+$ |
| `V[<]`, `V`, `V[>]` | arrival, decision, continuation | value | $\mathbb R$ |

### 1.3 Kernels

#kernels

With the fields placed at their perches, we can write the stage’s Bellman equation in functional notation:

$$
V(m) = \max_{0 < c \le m}
\bigl\{u(c) + \beta V_{\succ}(m-c)\bigr\},
\qquad
V_{\prec}(b) = \mathbb E_y\bigl[V(Rb+y)\bigr],
$$

where $V_{\succ}$ is the continuation value function supplied to the stage. The conditions under which the maximum is attained and the expectation is finite are given in [Stages](../Bellman-Sym/01-stage.md) §4.

These equations combine maximization with four relations between fields at adjacent perches. Three are given by **kernels**, the pointwise functions used by the stage’s operations: two **laws of motion** and a **value aggregator**.

- The arrival law of motion, `m = R*b + y`, gives the decision state from arrival assets and realized income.
- The decision law of motion, `a = m - c`, gives the continuation state from resources and the consumption choice.
- The value aggregator, `V = 𝑢(c) + β*V[>]`, combines current utility with discounted continuation value.

The fourth relation, `V[<] = E_{y}(V)`, takes the expectation over income to obtain the arrival value from the decision value; its aggregator is the identity. The Bellman calculus denotes the two laws of motion by $g_{\prec}$ and $g_{\succ}$, and the value aggregator by $G$.

**The elements of a stage**

Together with the perches, fields and kernels described above, the buffer-stock stage declares its parameters, shock law and choice:

- Its **parameters** are `β` (the discount factor), `ρ` (relative risk aversion), `R` (the gross return), and `μ_y` and `σ_y` (the mean and standard deviation of log income). Each is declared with its set and receives a value at calibration.
- Its **shock** is income `y`, declared with its lognormal distribution.
- Its **choice** is stated in the policy block as `c = argmax_{c}(𝑢(c) + β*V[>])`, with maximization over feasible consumption, `0 < c ≤ m`.

The stage file brings these objects together and declares how the kernels combine with operations such as maximization and expectation. It states only the theoretical model, which elaborates as a **[symbolic stage](../wiki/symbolic_stage.md)**. Parameter values, methods and settings are attached afterwards to produce a **[specified stage](../wiki/specified_stage.md)** ([Core concepts](01-concepts.md) §3).

[^1]: Sussman, G. J. and Wisdom, J. (2014). *Structure and Interpretation of Classical Mechanics*, second edition, MIT Press, preface: “Symbols have ambiguous meanings that depend on context, and often even change within a given context.”