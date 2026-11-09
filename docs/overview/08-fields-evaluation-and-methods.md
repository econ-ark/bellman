---
title: Fields, evaluation and methods
tags:
  - bellman-sym
  - user-facing
  - field
  - semantics
  - methodization
status: Draft
related:
  - "[[02-stage]]"
  - "[[04-methodization]]"
  - "[[14-appendix-c-syntax-to-semantics]]"
date: 2026-09-21
audience: user
type: overview
---

# Fields, evaluation and methods

> [!summary]
> Every name of a stage file stands for one thing. A field is a named quantity at a perch: a state, a control, a shock or a value; a declared function and a parameter are not fields. At a policy, each field becomes a function of the state, and the policy is no argument of that function. Some fields are evaluated, which means that the stage returns their functions by name; the others are parts of a longer expression. The distinction decides where a numerical method may stand: a method that computes an operation stands on the operator, and a method that stores a function stands where a function has a name.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](02-stage.md): perches, fields and blocks.
> **Formal account** — [From source to semantics](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the rule that reads fields as functions.
> **Used by** — [Methodization](../Bellman-Sym/04-methodization.md): how a methods file names a place of the stage.

We use the consumption stage `applications/portfolio-choice/declaration/stages/cons/cons.bl`. The decision state $\mathrm m_d$, cash on hand, lies in $\mathsf X_m = \mathbb R_{++}$, and saving $\mathrm a$ lies in $\mathsf X_a = \mathbb R_+$. A consumption value $\mathrm c$ is feasible at $\mathrm m_d$ when $\mathrm c \in \Gamma(\mathrm m_d) = (0, \mathrm m_d]$. The law of motion is $g_\succ(\mathrm m_d, \mathrm c) = \mathrm m_d - \mathrm c$, utility is $u$, and the continuation value function is $V_\succ : \mathsf X_a \to [-\infty, \infty)$. A policy is a measurable function $c : \mathsf X_m \to \mathbb R_{++}$ with $c(\mathrm m_d) \in \Gamma(\mathrm m_d)$ for every $\mathrm m_d$. Roman $\mathrm c$ is a consumption value and italic $c$ is a policy.

## 1 A value function at a policy

The block `cntn_to_dcsn` holds the line `V = 𝑢(c) + V[>]`, an equation between fields. At a policy $c$, consumption is $c(\mathrm m_d)$ and saving is $\mathrm m_d - c(\mathrm m_d)$, so the line defines the decision value function

$$V(\mathrm m_d) = u(c(\mathrm m_d)) + V_\succ(\mathrm m_d - c(\mathrm m_d)) \qquad (\mathrm m_d \in \mathsf X_m).$$

The function $V$ has the single argument $\mathrm m_d$, and the policy is no argument of it. The policy enters wherever the control appears, in the reward and in the law of motion alike, and we write the two at the policy as

$$G_{\succ, c}(\mathrm m_d, \mathrm w) = u(c(\mathrm m_d)) + \mathrm w, \qquad g_{\succ, c}(\mathrm m_d) = g_\succ(\mathrm m_d, c(\mathrm m_d)),$$

so that $V(\mathrm m_d) = G_{\succ, c}\big(\mathrm m_d, (V_\succ \circ g_{\succ, c})(\mathrm m_d)\big)$. The convention follows Sargent and Stachurski, who set $r_\sigma(x) = r(x, \sigma(x))$ and $P_\sigma(x, x') = P(x, \sigma(x), x')$, and their policy operator is $(T_\sigma v)(x) = r(x, \sigma(x)) + \beta \sum_{x'} v(x') P(x, \sigma(x), x')$, a function of the state alone; Hernández-Lerma et al. abbreviate $c(x, f(x))$ and $F(x, f(x))$ to $c(x, f)$ and $F(x, f)$.

A function of the state and a consumption value together, $(\mathrm m_d, \mathrm c) \mapsto u(\mathrm c) + V_\succ(g_\succ(\mathrm m_d, \mathrm c))$, is needed in one place only: inside a maximization, where $\mathrm c$ is the variable that the maximization ranges over. The line `c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])` of the policy block is such a place. A policy found by inverting an Euler equation forms no such function.

## 2 Which fields are evaluated

The **header** of a block is its bracketed first line, which lists the block's inputs and outputs with their perches. A field is **evaluated**, meaning that the stage returns its function under the field's name, in two cases.

1. The field is an output in a block's header. The header `[id=cntn_to_dcsn, (V[>], c) : !cntn -> (V) : !dcsn]`, written here without its types, returns $V$; a derivative line of the block, `D_{m_d}V = 𝑑𝑢(c)`, states the derivative of that value in the decision coordinate and returns no further field. The header of the policy block returns the control $c$. The inputs of a header are evaluated elsewhere: $V_\succ$ by the stage that follows, and the policy by the policy block.
2. The field is the left side of a line marked `!node`. In `applications/smooth-ambiguity-savings/declaration/stages/sa_savings/sa_savings.bl` the line `CE = E_{Ψ}(V[>]^(1-γ))^(1/(1-γ)) :: [id=risk_ce, !node]` returns the certainty equivalent $CE$.

Every other field is a part of a longer expression. For an unmarked line such as `W = β*V[>]`, the expression of $W$ is substituted wherever $W$ is used, and the stage returns no function under that name. A block defines a symbol once.

## 3 Evaluation

**Evaluation** takes the expression on the right side of an evaluated field's line, such as $x \mapsto f(g(h(x, l(x))))$, and returns a function $p$ with $p(x)$ equal to the expression at every $x$. In the exact mathematics $p$ is the expression computed at each $x$, and evaluation changes nothing. Numerically, $p$ may be an approximation, such as an interpolant of the expression's values on a grid. The approximation is a different function, with mathematics of its own, which the stage does not describe: the stage records the method, its options and what it requires.

## 4 Where a method stands

A methods file attaches numerical methods to places of the stage.

```yaml
stage: sa_savings
methods:
  - on: E_Ψ
    method: !gauss-hermite
    settings:
      n_nodes: [n_Ψ_nodes]
  - on: cntn_to_dcsn.risk_ce
    method: !Linear
    settings:
      grid: !Cartesian
      orders: {m_d: n_m}
      bounds: {m_d: [m_min, m_max]}
```

A method that computes an operation stands on the operator. Gauss–Hermite quadrature is a rule for one integral against a normal or lognormal distribution, and `E_Ψ` names the expectation. A method that stores a function stands where a function has a name: `!Linear` holds $CE$ by its values on a grid and reads it between them by linear interpolation, and `cntn_to_dcsn.risk_ce` names the line that returns $CE$. The setting `grid` names the grid by its kind, `!Cartesian`, a product of one grid for each coordinate, and the grid's order and bounds stand beside it. A method of one kind is refused at a place of the other. Quadrature says how the expectation inside the line is computed and says nothing about how $CE$ is held, so the package refuses it on the line:

```text
!gauss-hermite does not admit target kind node; method-attachment admits operator E
```

An option a method requires is written beside it, and `configure` refuses a value outside its type.

The places a stage admits are its own answer, `stage.places()`, with the kind of each. A method that stores a function admits the evaluated fields, a declared function and the stored form of a builder's output, at the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that closes the builder, which the methods file names by what it stores: `policy.evaluate` for the policy function, and `cntn_to_dcsn.evaluate.value` and `cntn_to_dcsn.evaluate.marginal` for a value function and the derivative of it that a derivative line states. A method that computes an operation admits the operator. A function that the file does not name, such as $V_\succ \circ g_\succ$, is no place at all: an author who wants it stored writes it on a line of its own and marks the line `!node`.

## References

Hernández-Lerma, O., Laura-Guarachi, L. R., Mendoza-Palacios, S. and González-Sánchez, D. (2022). *An Introduction to Optimal Control Theory: The Dynamic Programming Approach*. Springer. Remark 2.19.

Sargent, T. J. and Stachurski, J. (2025). *Dynamic Programming, Volume II: General States*. Chapter 1, equations (1.16) and (1.18).
