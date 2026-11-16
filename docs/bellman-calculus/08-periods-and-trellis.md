---
title: Periods and the trellis
short_title: Periods and trellis
status: drafted
tags:
  - bellman-calculus
  - period
  - trellis
  - inter-period-connector
audience: user
type: theory
topic: [calculus]
---

# Periods and the trellis

> [!summary]
> A trellis is a diagram of periods joined by connections. Each period takes a tuple of continuation fields and returns a tuple for the preceding period. Repeated modular declarations share one family of operators; their supplied fields may differ. Finite-horizon recursion starts from terminal data, while a stationary problem requires a fixed point of all the fields sent backward.

> [!info]- Relationship with other documents
> **Builds on** — [Stage composition](./07-stage-composition.md) defines compatible within-period connections; [Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §6 defines the partial operators and their domains.
> **See also** — [Modularity](./APPX-H-MODULARITY.md) states the equality of repeated declaration meanings and the restriction on calibration sources.
> **Used by** — [Periods](../Bellman-Sym/06-period.md) and [Trellis](../Bellman-Sym/07-trellis.md) give the corresponding source forms.

<a id="1-period-as-a-local-namespace"></a>

## 1 Period declarations

A **period** contains stages and their connections. A **stage occurrence** is one use of a stage declaration. Its fields keep their stage-local names. Within one period, stages that declare the same parameter name share that parameter coordinate and must state compatible declared sets.

In a general trellis, parameter coordinates may differ between periods. A **modular model** has the stricter meaning of [Modularity](./APPX-H-MODULARITY.md): every occurrence takes calibration from the sources recorded by its declaration, with no rule addressed to its position. Methods and settings lie outside this condition. Distinct occurrence objects may therefore share one declared family of mathematical operators without sharing mutable data.

A fixed declaration has no date argument. A quantity such as age is supplied as a field. A fixed wage table or function read at that age can consequently give different wages at different uses of one operator.

<a id="2-inter-period-connectors"></a>

## 2 Inter-period connections

An **inter-period connection** joins one period's continuation state to the following period's arrival state. It also pairs the value-type fields sent backward by the following period with the fields required by the earlier one. The pairing preserves each local name and computes no economic transformation. A transformation belongs in a stage equation.

For a state-coordinate map $\varphi$, a backward representing function $f$ becomes $f\circ\varphi$ on the preimage of its domain. A constant remains a constant. The supplied declared set and dependence must satisfy the recipient's requirements. A complete route also requires the joint forward law; marginal laws alone do not determine it.

<a id="3-the-trellis"></a>

## 3 The map on pairs

Let $\varsigma\in\mathsf P$ collect the state-independent fields whose backward equations read only those fields and parameters. Their period update is a partial map $\tau$. Let $v\in\mathsf B_\varsigma$ collect the other representing functions. Include the connection to the earlier period in $\mathbb T_\varsigma$. The **map on pairs** is

$$
\Phi(\varsigma,v)=(\tau\varsigma,\mathbb T_\varsigma v).
$$

It is defined where both components have values. Repeated applications give

$$
\Phi^k(\varsigma,v)=
(\tau^k\varsigma,\mathbb T_{\tau^{k-1}\varsigma}\cdots\mathbb T_\varsigma v).
$$

This follows by substitution and associativity wherever successive applications are defined. Different period declarations contribute their own maps in backward order. A finite path of $N$ periods has $N-1$ internal connections; comparison with $\Phi^N$ additionally includes the earlier-end connection. Terminal data supply the last period's input. Maximizing rules require measurable maximizing policies at every application.

<a id="4-infinite-horizon-and-the-fixed-point"></a>

## 4 Stationary and seasonal problems

A stationary pair satisfies

$$
\tau\varsigma^*=\varsigma^*,\qquad
\mathbb T_{\varsigma^*}v^*=v^*.
$$

Thus every field sent backward must be fixed. An age update that subtracts one has no fixed point. Existence, uniqueness and convergence require separate assumptions.

For seasonal declarations, list their maps in backward order as $\Phi_1,\ldots,\Phi_m$. A fixed point of $\Phi_m\circ\cdots\circ\Phi_1$ gives the cycle, provided every application is defined. When the seasonal maps all equal $\Phi$, the composite is $\Phi^m$.

<a id="5-why-this-matters-for-the-calculus-framing"></a>

## 5 Information and composition

A staged description records the information available for each choice and the dependence of its equations. Composition preserves this order. Associativity allows regrouping a fixed sequence of compatible partial maps; it neither changes that sequence nor proves convergence.

A supplied constant can select a shock law or a forward transition. Repeated modular declarations then share the family of kernels, although different supplied ages may select different kernels. A forward map on pairs needs an authored update of those constants. A backward update is not assumed invertible.

<a id="6-composition-as-identification-of-fields"></a>

## 6 Field identification

A **field** is a declared random quantity, and its **representing function** gives its value at a state on a specified domain. Neither a declared set nor a pairing establishes square integrability. [Fields, functions and types](./04-fields%2C%20functions%20and%20types.md) states these distinctions.

Equal names and compatible sets do not by themselves establish the intended economic identification. Assets and age may both be nonnegative while having different meanings. A connection records the chosen pairing; the model must justify its units and information. Under that interpretation, the paired state coordinates agree almost surely. A nonidentity transformation instead requires an authored measurable equation.

The initial joint arrival law must assign probability one to the first period's admissible arrival set. Terminal data must meet the last period's input requirements. These are separate conditions on the two ends of the trellis, not fields of its declaration.

<a id="see-also"></a>

## 7 Related documents

- [Stage composition](./07-stage-composition.md)
- [Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md)
- [Modularity](./APPX-H-MODULARITY.md)

[Next → Branching](./09-branching.md)
