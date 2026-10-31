---
title: Periods and the trellis
short_title: Periods and trellis
status: not yet drafted — stub notes only
tags:
  - bellman-calculus
  - period
  - trellis
  - inter-period-connector
  - status/stub
audience: user
type: theory
topic: [calculus]
---

# Periods and the trellis

> [!summary]
> These unfinished notes extend stage composition across periods and distinguish finite-horizon recursion from a stationary fixed-point problem. Boundary identifications and terminal data must match the declared domains.

> [!info]- Relationship with other documents
> **Builds on** — [Stage composition](./07-stage-composition.md) defines compatible within-period joins.
> **See also** — [Stages and perches](./03-Stages%20and%20perches.md) states the local operators and information assumptions.
> **Used by** — [Period Syntax](../Bellman-Sym/06-period.md) and [Trellis Syntax](../Bellman-Sym/07-trellis.md) specify the outer YAML structure; [Stages](../Bellman-Sym/01-stage.md) describes the source's typed declarations.

> [!note] Not yet drafted — stub notes only
> Structural outline only; the multi-period and trellis chapter is not yet written.

A **period** contains stage occurrences (uses of stage modules) connected through their boundary fields. A **trellis** orders period occurrences and their inter-period connections. A recursive problem also supplies terminal or infinite-horizon conditions; a one-stage problem is included as a special case.

## 1. Period as a local namespace

A period contains stage occurrences and their dependencies, but each stage keeps its own field names. A name declared as a parameter by two stages of one period denotes one period parameter; the same spelling in another period denotes another. In a chain, selected dependencies determine a forward economic order. *(Placeholder.)* The period operator $\mathbb{T}_{\text{period}}$ has the conditional composition reading described in [Stage composition](./07-stage-composition.md) where compatible complete routes and operators are supplied; the period's *boundary fields* are the arrival of its first stage and the continuation of its last.

## 2. Inter-period connectors

Between-period connectors pair one period's boundary continuation fields with the next period's boundary arrival fields. *(Placeholder.)* These are the **inter-period connectors** in the project's vocabulary — occurrence-specific selections, not changes to a field's local name. A nonidentity transformation must be authored as a stage equation; the connector performs no calculation. They differ from intra-period connectors, which join stages within a single period.

## 3. The trellis

A trellis is a finite-horizon sequence of period instances wired by between-period connectors. *(Placeholder.)* The backward recursion runs:

$$
v_{T+1} \;=\; v_{\mathrm{terminal}}, \qquad v_t \;=\; \mathbb{T}_{t}\, v_{t+1}, \qquad t = T, T{-}1, \ldots, 0.
$$

Here $t$ is forward economic time, $T$ the last decision date, $v_{\mathrm{terminal}}$ the supplied terminal value, and $\mathbb T_t$ the possibly date-dependent period operator. The display uses compatible boundary identifications. The application's period index may instead count backward from terminal; §1 of Bellman-SYM's Trellis Syntax page defines that separate convention.

In the specified construction, each stage occurrence has a fresh graph and bindings even when module text is parsed once. The `.bl` syntax tree is temporary; interpreted equations and definitions remain. Periods, trellises, connectors, methods, settings and calibration retain their YAML outer forms. A mathematical composition expression does not assert one stored whole-trellis semantic graph.

## 4. Infinite horizon and the fixed point

For a stationary period operator mapping a chosen value-function space to itself, a candidate infinite-horizon value satisfies:

$$
v^\star \;=\; \mathbb{T}_{\text{period}}\, v^\star.
$$

*(Placeholder.)* State the model-specific conditions for existence, uniqueness and iteration convergence. A contraction on a nonempty complete metric space is one sufficient route; monotone or other fixed-point arguments need their own assumptions. A one-period composition alone establishes none of these results.

<a id="5-why-this-matters-for-the-calculus-framing"></a>

## 5. Information and composition

A staged description records the economic order, information available for each choice, and compatible interfaces. Composition then defines the larger recursion where each operation is well defined. *(Placeholder.)* Develop this account without treating every recursive program as an instance of the present finite stage representation.

## 6. Composition as identification of fields

For a chain of stages $S_1,S_2$, selected pairs relate the continuation state fields of $S_1$ to compatible arrival state fields of $S_2$. A connector declares a pair and leaves each field's local name intact. A complete route establishes a coordinate map only when all ordered state coordinates, the joint forward law and the backward value components agree. Mathematical transformations belong in the equations, as in [Stage composition](./07-stage-composition.md).

**Fields and value domains.** A field is a random quantity on the model's probability space. A declaration that its values lie in a domain $D$ does not make it square-integrable or select a particular function space. Measurability, integrability and a representative function require their stated assumptions. [Fields, functions and types](./04-fields,%20functions%20and%20types.md) distinguishes these objects; the source's typed declarations are described on Bellman-SYM's Stages page.

**Identification and names.** A common compatible value domain is needed for a direct pairing but is not sufficient: assets and age can both take nonnegative real values while denoting different quantities. A boundary join must pair the intended quantities with compatible units and information. Under a common probabilistic interpretation, the equality $X_{S_2,\prec}=X_{S_1,\succ}$ holds almost surely at that boundary when the connection pairs those coordinates; equality of their written names alone does not assert it. A declared transformation $X_{S_2,\prec}=\varkappa(X_{S_1,\succ})$ instead requires the typed measurable map $\varkappa$ in the model equations.

**Composition of meanings.** Under the fixed interpretation and compatible interfaces, evaluating a composition means composing its stage operators. The associativity of function composition permits regrouping an unchanged sequence; it does not permit arbitrary reordering or supply convergence. [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) states the corresponding exact term argument with free inputs fixed.

> [!note] Related theory
> Algebraic composition provides an account of how declared operations form a larger expression. Its applicability here requires compatible domains and the same target interpretation. The mathematical expression is distinct from the stage-dependency graph used to order computation and from the application's period dictionaries.

<a id="see-also"></a>

## 7. Related documents

- **Across:** [Illustrative example](./02-Illustrative%20example.md), [Stage composition](./07-stage-composition.md), [Ingredients](./ingredients.md)

[Next → 9. Branching](./09-branching.md)
