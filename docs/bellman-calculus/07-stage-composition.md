---
title: Stage composition — within a period
short_title: Stage composition
status: not yet drafted — stub notes only
tags:
  - bellman-calculus
  - composition
  - connector
  - period
  - status/stub
audience: user
type: theory
topic: [calculus]
---

# Stage composition

> [!summary]
> These unfinished notes describe composition of stages through compatible boundary fields. A connector selects a continuation-to-arrival field pair without renaming either field; a transformation must be specified by an equation.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md) defines the stage operators.
> **See also** — [Periods and the trellis](./08-periods-and-trellis.md) discusses joins across dates.
> **Used by** — [Period Syntax](../Bellman-Sym/06-period.md) defines the YAML outer composition whose joins this chapter describes.

> [!note] Not yet drafted — stub notes only
> Structural outline only; the within-period composition chapter is not yet written.

Consider a period whose stage dependencies form a chain, indexed in forward economic order by $k=1,\ldots,K$. The continuation fields of stage $\mathbb{S}_k$ and the arrival fields of $\mathbb{S}_{k+1}$ have separate stage-local identities. Selected pairs relate their eligible uses; an authored **connector** states a pair explicitly. Suppose the ordered state coordinates form a compatible complete route and each stage operator is defined on the required tuples. Let $C_k$ be the backward connection from stage $k+1$ to stage $k$. The backward period operator is

$$
\mathbb T_{\mathrm{period}}=\mathbb T_{\mathbb S_1}\circ C_1\circ\mathbb T_{\mathbb S_2}\circ\cdots\circ C_{K-1}\circ\mathbb T_{\mathbb S_K}.
$$

Each stage operator acts on the complete tuple of representing functions. Each earlier stage reads the fields returned by its successor. Every composite is restricted to the domain where successive applications are defined. This conditional display is not a general composition theorem for all period shapes.

## 1. Connectors

A **connector** pairs an eligible continuation state field with an arrival state field of the following stage. It also pairs the following stage’s arrival value-type fields with the earlier stage’s continuation inputs. These pairings have opposite directions. It does not change either stage's field name or equations. *(Placeholder.)* A simple pairing is $a'\mapsto a$ when the two fields have compatible declared sets and the author establishes their common economic meaning, units and boundary information.

Declared sets are compatible when the continuation field's set is contained in the arrival field's. In the terms of [Appendix D](./APPX-D-KINDS-AND-SORTS.md), the continuation declaration $f$ lies in $\mathrm{Dom}[D_g]$ for the arrival declaration $g$, that is, $D_f\subseteq D_g$ (D6), so that the pairing sends every value of the continuation field to a value the arrival field admits. Equality $D_f=D_g$ is not required: a declared set contains a field's values and need not be exhausted by them.

When a route pairs whole ordered state tuples, the induced coordinate map reads the destination coordinates from those of the source; a crossed pairing can therefore be a permutation without an inverse state transition. A nonidentity economic transformation must appear in an authored stage equation. Equal names or domains alone do not identify arbitrary fields.

## 2. Composing stages into periods

The input-to-output signature is also the rule for joining stages. A **period** is
a collection of stage occurrences (uses of stage modules) with selected connections. In the chain considered here, joining compatible boundary fields pairs the continuation state coordinates of one stage with the arrival state coordinates of its successor. The successor's arrival tuple supplies the predecessor's continuation fields under that coordinate map, field by field. Each supplied value-type field must satisfy the recipient's declared set and dependence requirements. Each continuation state field's declared set must lie in that of its paired arrival state field. Separate marginal shock laws do not establish the joint forward law needed for a complete route.

<figure markdown="span">
  ![Two stages composed into a period: the continuation perch ≻⁰ of the first stage is joined by a double line to the arrival perch ≺¹ of the second, identifying the shared boundary.](../_assets/stage-period-diagram.svg){ width="700" }
  <figcaption>Two stages composed into a period; the double line in the center identifies the shared boundary perch $\succ^{0} = \prec^{1}$.</figcaption>
</figure>

The double line denotes the boundary identification in this example. Operators compose right to left in the backward calculation, provided their domains and codomains agree after that identification. The equations, feasible sets and conditional laws retain their stage-specific assumptions.

Changing the order of names in a period's YAML list does not change the economic dependencies. Reordering the economic stages or changing a successor can instead change information, feasibility or rewards, and requires the model to be checked again. A stage can be reused with a compatible continuation problem; the composition rule is not a general invariance theorem for arbitrary swaps. Branch-specific successors require their explicit routes, as in [Branching](./09-branching.md).

## 3. Intra-period vs inter-period connectors

This file covers **intra-period** wiring (stage-to-stage within one period). Inter-period wiring (period-to-period, reusing the same connection where the declarations and pairings repeat) is covered in [Periods and the trellis](./08-periods-and-trellis.md).

<a id="see-also"></a>

## 4. Related documents

- **Across:** [Fields, functions and types](./04-fields,%20functions%20and%20types.md), [Periods and the trellis](./08-periods-and-trellis.md), [Ingredients](./ingredients.md)

[Next → 8. Periods and trellis](./08-periods-and-trellis.md)
