---
title: "Appendix D — Kinds, sorts, and types"
short_title: "Appendix D: Kinds and sorts"
status: drafted — Phase 1
tags:
  - bellman-calculus
  - type
  - universal-algebra
  - field
authors:
  - Akshay Shanker
audience: user
type: theory
topic: [calculus]
---

# Appendix D — Kinds, sorts, and types

> [!summary]
> We distinguish declared sorts from the sets that interpret them, and kinds from greatest sorts. The field classification uses information context, role, and value domain, with shocks treated separately. The propositions state which conclusions follow from these declarations and which require additional conventions or nonempty examples. The grid of a numerical method is a sort of its own and no subsort of a state space.

> [!info]- Relationship with other documents
> **Builds on** — [Fields, functions and types](./04-fields%2C%20functions%20and%20types.md) distinguishes random fields, value domains, and representing functions.
> **Used by** — Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) states the current typing context and information rules.
> **See also** — [Stage term](./APPX-C-STAGE-TERM.md) describes the mathematical signature; [Methods](./06-Methods.md) §5 states the grid as the discretized domain, with a representation as a retract on it.

<a id="0-setup"></a>

## 1 Setup

A **many-sorted signature** $\Sigma=\langle S,\Omega\rangle$ lists sorts and operations with specified input and output sorts. We fix an interpretation assigning each sort $s$ a carrier $A_s$, the set interpreting it. A declared sort name, its carrier, and an element of that carrier are different objects.

The subset construction below is a local mathematical account of field classifications. It does not assert that every proposed type-theoretic extension is already part of the source language. Current `.bl` declaration rules are owned by §§1–2 of Bellman-SYM's Appendix C.

<a id="1-definitions"></a>

## 2 Definitions

**D1 (Signature).** The sort set $S$ specifies categories of inputs and outputs. For a finite sequence $w=(s_1,\ldots,s_n)$ and output sort $s$, $\Omega_{w,s}$ is the set of operation symbols with those input sorts and that output sort. Its number of arguments is $n$. We call the input–output specification its type or rank; terminology concerning “rank” differs between sources (Goguen, Thatcher, Wagner and Wright 1977, §2).

**D2 (Carrier).** An interpretation gives sets $A_s$ and, for each symbol $o\in\Omega_{w,s}$, an operation $o_A:A_{s_1}\times\cdots\times A_{s_n}\to A_s$. These are the carriers and operations of a $\Sigma$-algebra. A function's own domain and codomain are not erased when it occurs inside another operation.

**D3 (Kind).** A kind groups sorts in a connected component of the declared subsort order. Connected means that sorts can be joined by a finite sequence of comparisons, allowing either direction. A component need not have a greatest sort: an order with $a\leq b$ and $a\leq c$, with $b,c$ incomparable, has no greatest element. If a membership presentation supplies a carrier $K$ for the whole kind, that is distinct from declaring a greatest sort with carrier $K$. Below we explicitly supply such ambient carriers and, where useful, a named greatest sort.

**D4 (Membership).** Within an ambient kind carrier $K$, a sort may be interpreted by a predicate whose satisfying elements form $A_s\subseteq K$. The judgment $t:s$ asserts that the interpreted term belongs to $A_s$. An expression can have an ambient kind before membership in a more restrictive sort has been established.

**D5 (Subsort).** A declared subsort relation $s\leq s'$ requires compatible carrier inclusion,

$$
s\leq s'\quad\Longrightarrow\quad A_s\subseteq A_{s'}.
$$

Carrier inclusion in one interpretation does not establish the converse declaration. In particular, two incomparable sort names can have equal carriers. Multiple inheritance permits a sort to be below several incomparable sorts. For the local classifier construction below we explicitly declare the inclusion relations induced by domain inclusion and intersection; these declarations are additional to the one-way requirement (Martí-Oliet and Meseguer 1996, §2.1, Definition 2.2).

**D6 (Classifier).** A classifier is a total function $c:K\to I$ on a specified domain $K$. Its **fibers** $c^{-1}(i)=\{x\in K:c(x)=i\}$ are disjoint and exhaustive. We may introduce sorts interpreted by these fibers; the function itself is not a sort. For value-domain classification, let $D_f$ be the domain recorded for field declaration $f$ and define the subset

$$
\mathrm{Dom}[D]=\{f:D_f\subseteq D\}.
$$

This is a domain refinement rather than an exact-domain fiber. In this appendix classifier elements are field declarations with their metadata, not realized numbers. A declaration's value domain $D_f$ is distinct from the carrier of the sort of such declarations and from a space of random variables.

**D7 (Intersection sort).** We explicitly close the local collection of classifier subsets under intersections, identifying extensionally equal subsets. In this local inclusion order the meet is the intersection,

$$
A_{s\wedge s'}=A_s\cap A_{s'}.
$$

It is the greatest lower bound because every subset contained in both components is contained in their intersection. An arbitrary order-sorted signature need not already contain a sort denoting every such intersection. A **combined field sort** intersects one perch sort, one role sort, and one domain refinement where those classifiers are defined.

<a id="2-the-field-type-system-step-by-step"></a>

## 3 Field classification

**Step 1 — the ambient declarations.** Let $F$ be the set of declared random-quantity names with their metadata, including shocks. Let $F_{\mathrm{loc}}\subseteq F$ be the declarations assigned a native perch. Shock declarations are classified by their transition and law separately; they need not belong to $F_{\mathrm{loc}}$. We explicitly use `Field` as an ambient kind and a greatest local declaration sort with carrier $F$. This greatest-sort convention does not follow merely from connectedness in D3.

**Step 2 — the classifiers.** The perch classifier is total on $F_{\mathrm{loc}}$:

$$
\mathrm{perch}:F_{\mathrm{loc}}\to\{\prec,\sim,\succ\}.
$$

Role is total on $F$, with values state, control, value, and shock. The domain assignment records each declaration's value set $D_f$. A shock can be measurable at a later information set without being a state coordinate there. A decision control remains a decision control when listed as an available argument at a later perch. §2.2 of Bellman-SYM's Appendix C gives these exceptions.

**Step 3 — the component sorts.** The perch fibers are `ArrivalField`, `DecisionField`, and `ContinuationField`, subsets of $F_{\mathrm{loc}}$. The role fibers in $F$ are `StateField`, `ControlField`, `ValueField`, and `ShockField`. Domain refinements include $\mathrm{Dom}[\mathbb R]$, $\mathrm{Dom}[\mathbb R_+]$, and $\mathrm{Dom}[\mathbb R_{++}]$. The Sort of a value lists under `derivatives` the coordinates of its stated derivatives; the derivative of a value is read by the derivative term `D_{a}V[>]`, which is distinct from a function name and is no field.

**Step 4 — domain order.** Since $\mathbb R_{++}\subseteq\mathbb R_+\subseteq\mathbb R$, the domain-refinement subsets satisfy the corresponding non-strict inclusions by D6. We declare those relations in this local system. Strictness additionally requires declarations distinguishing the subsets (P3).

**Step 5 — combined field sorts.** For a classified declaration,

$$
\mathsf{Field}[p,r,D]
:=\mathrm{PerchField}[p]\cap\mathrm{RoleField}[r]\cap\mathrm{Dom}[D].
$$

This is a local intersection sort under D7, not an assertion that three arbitrary classifiers are probabilistically independent or that every combination is inhabited.

**Step 6 — other mathematical objects.** We distinguish the following families by declaration. Their mathematical encodings do not by themselves prove that they are separate connected components of a subsort order.

| Family | Mathematical objects | Required types |
|---|---|---|
| `Field` declarations | names, roles, value domains, and information metadata | the classifier subsets above |
| Interpreted fields | measurable random variables | random variables valued in $D_f$ with the required information |
| `Transition` | measurable state-transition maps | $g_\prec:\mathsf X_\prec\times\mathsf Z_\zeta\to\mathsf X_\sim$ and $g_\succ:\operatorname{Gr}(\Gamma)\times\mathsf Z_\eta\to\mathsf X_\succ$ |
| `Kernel` | pointwise reward/continuation aggregators | $G_\succ(v,x,a,\eta)$ and $G_\prec(v,x_\prec,\zeta)$ with the domains in [Stages and perches](./03-Stages%20and%20perches.md); an outer map $G^{\mathrm{out}}_\succ(w,x,a)$ written outside the shock integral has the same sort without the shock argument (§2.3a there) |
| `Value` | representing value functions | specified function spaces $\mathsf V_p$ on $\mathsf X_p$ |
| `Policy` | measurable feasible action functions | $\Pi_\Gamma=\{\pi:\mathsf X_\sim\to\mathsf A:\pi\text{ measurable},\ \pi(x)\in\Gamma(x)\}$ |
| `Dist` | probability measures | $\mathsf M_p$ on $\mathsf X_p$ |
| `Grid` | the discretized domain of a function an operator stores or evaluates | the finite subsets $G \subset \mathsf X$ of the domain of that function, each with its inclusion $\iota : G \to \mathsf X$; one such subset is the grid component of the operator's signature ([Methods](./06-Methods.md) §5) |

Here $\Gamma(x)$ is the feasible action set and $\operatorname{Gr}(\Gamma)$ its set of feasible state–action pairs. The declared field $V[>]$ has a continuation representing function under the state-generated measurability and measurable-domain assumptions in [Fields, functions and types](./04-fields%2C%20functions%20and%20types.md). No separate `V_fn` source declaration is required. A law over population states is distinct from the law of an individual shock. Forward propagation uses the operators $\mathbb M_\prec$ and $\mathbb M_{\succ,\pi}$, under a specified policy.

**The grid is a sort of its own.** The grid component of an operator's signature is typed by the family `Grid`: the carrier of the sort is the set of finite subsets of the domain of the function the operator stores or evaluates, each with its inclusion, and one grid is an element of that carrier. The inclusion is a map in one interpretation and establishes no declared subsort relation between the grid and the state sort (D5). A function stored at the points of a grid is not thereby a member of the value sort $\mathsf V_p$: it becomes one through the interpolant that extends it, the section of [Methods](./06-Methods.md) §5. A discrete domain the model declares, such as a finite set of housing sizes, is a value domain $D_f$ of a field and no grid.

**Internal functions remain typed.** A utility function, a local function definition, and an intermediate expression retain their parameter and result types when substituted. A bound parameter may be renamed consistently, but its type and scope remain. No separate named sort for “reward function” is required to make $\mathrm u:\mathbb R_{++}\to\mathbb R$ a typed function. The pointwise-kernel description does not settle the unfinished representation of Epstein–Zin certainty equivalents. #todo

<a id="3-propositions"></a>

## 4 Propositions

**P1 (Partitions on the stated domains).** The perch classifier partitions $F_{\mathrm{loc}}$, while the role classifier partitions $F$.

For a total single-valued function $c:K\to I$, each $f\in K$ has one image $i$, so it belongs to one fiber. If it belonged to fibers $i$ and $j$, single-valuedness would give $i=j$. The fibers are therefore disjoint and exhaustive on $K$. Apply this argument to the two stated classifier domains. It makes no perch assignment for a shock outside $F_{\mathrm{loc}}$. ∎

**P2 (No inhabited common subsort of disjoint fibers).** Let $i\ne j$ be values of one classifier. By P1, its two fiber carriers have empty intersection. If $s$ is a declared subsort of both, D5 gives

$$
A_s\subseteq A_{\mathrm{Sort}_c[i]}\cap A_{\mathrm{Sort}_c[j]}=\varnothing.
$$

Thus $A_s=\varnothing$. The conclusion uses only the declared-order-to-inclusion implication. ∎

> **Corollary.** An inhabited field-declaration sort cannot be below both `ArrivalField` and `DecisionField`. Per-perch value-field sorts are instead $\mathrm{ValueField}\cap\mathrm{PerchField}[p]$, each below the cross-perch role sort `ValueField`. These declaration subsets are not the value-function spaces $\mathsf V_p$.

**P3 (Domain refinement inclusions).** If $D\subseteq D'$, then $D_f\subseteq D$ implies $D_f\subseteq D'$. By D6,

$$
\mathrm{Dom}[D]\subseteq\mathrm{Dom}[D'].
$$

These give the declared non-strict domain chain in Step 4. For strictness, one additionally needs a declaration $f\in\mathrm{Dom}[D']\setminus\mathrm{Dom}[D]$. For example, an assets declaration with $D_f=\mathbb R_+$ distinguishes $\mathrm{Dom}[\mathbb R_+]$ from $\mathrm{Dom}[\mathbb R_{++}]$ because $0\in D_f$. A declaration with $D_f=\mathbb R$ distinguishes the next inclusion because it admits negative values. Without such declarations, the corresponding classifier subsets can be equal. P2 excludes inhabited inclusions between distinct fibers of one partition; it does not prohibit further separately declared refinements. ∎

**P4 (Combined constraints).** Fix a declaration $f\in F_{\mathrm{loc}}$ with perch $p$, role $r$, and declared domain $D_f$. By the definitions, the combined subset is

$$
\mathsf{Field}[p,r,D]
=\{g\in F_{\mathrm{loc}}:\mathrm{perch}(g)=p,\ \mathrm{role}(g)=r,\ D_g\subseteq D\}.
$$

It is an intersection sort by D7. Within this family for fixed $p,r$, the choice $D=D_f$ gives the least subset containing $f$: every $D$ that admits $f$ satisfies $D_f\subseteq D$, so P3 gives the required inclusion. It is inhabited by $f$. A general combined sort is inhabited exactly when some declared field satisfies all three constraints; independence of the classifiers is unnecessary. ∎

**P5 (Arrival is a subsort under the local greatest-sort convention).** `ArrivalField` is the fiber $\mathrm{perch}^{-1}(\prec)\subseteq F_{\mathrm{loc}}\subseteq F$. Step 1 and the local inclusion declarations make it a subsort of the ambient `Field` sort. It is proper if a declaration outside that fiber exists, as the decision resource field $m$ does in the buffer-stock example. Without such a witness the inclusion need not be strict. The separate use of `Field` as an ambient kind is a presentation convention, not a consequence that every connected component has a top. ∎

**P6 (A field and its representative are distinct objects).** Let $V_\succ$ be a random field with value domain $\mathsf L$ at continuation information. It belongs to an appropriate space of measurable random variables, not to $\mathsf L$ itself; $V_\succ(\omega)$ is an element of $\mathsf L$. Its representing function is a map $\mathrm v_\succ:\mathsf X_\succ\to\mathsf L$.

When $V_\succ$ is measurable with respect to $\sigma(X_\succ)$ and the value space has the required measurable structure, the representation is

$$
V_\succ=\mathrm v_\succ(X_\succ)\quad\text{almost surely}.
$$

This is the state-representation rule of Bellman-SYM's Appendix C, §1.2. It does not imply square integrability, nor does it determine values of the representative on states outside the relevant state law. Pointwise representative choices are required for counterfactual evaluation. The field/function distinction applies to policy controls as well; the derivative of a value is a function determined by the value's function and is no field. It supplies no converse inference about subsort declarations merely from how the objects are encoded. ∎

**P7 (Distribution objects are separately declared).** In this local signature we assign probability laws to the family `Dist` and declare no subsort relations connecting it to any other family. Its sorts therefore share no connected component with a sort in another family. Treating all distribution sorts as one component would additionally require declared connections among those sorts. This follows from the chosen declarations, not from a claim that measures cannot be represented as functions or that unlike-looking carriers cannot be included in one another.

Its forward operators are $\mathbb M_\prec:\mathsf M_\prec\to\mathsf M_\sim$ and $\mathbb M_{\succ,\pi}:\mathsf M_\sim\to\mathsf M_\succ$. Their pairing is with the undiscounted transition expectations $P_\prec$ and $P_{\succ,\pi}$ defined in [Stages and perches](./03-Stages%20and%20perches.md) §2.7, not with reward-bearing Bellman evaluation. ∎

<a id="4-worked-example--buffer-stock"></a>

## 5 Buffer-stock example

| Declaration or object | Family | Classification or type | Interpretation |
|---|---|---|---|
| $k$ | `Field` | $\mathrm{ArrivalField}\cap\mathrm{StateField}\cap\mathrm{Dom}[\mathbb R_+]$ | random arrival assets |
| $m$ | `Field` | $\mathrm{DecisionField}\cap\mathrm{StateField}\cap\mathrm{Dom}[\mathbb R_{++}]$ | random resources |
| $c$ | `Field` | $\mathrm{DecisionField}\cap\mathrm{ControlField}\cap\mathrm{Dom}[\mathbb R_{++}]$ | consumption, additionally constrained by $c\leq m$ |
| $a$ | `Field` | $\mathrm{ContinuationField}\cap\mathrm{StateField}\cap\mathrm{Dom}[\mathbb R_+]$ | random assets after consumption |
| $y$ | `Field` | $\mathrm{ShockField}\cap\mathrm{Dom}[\mathsf Z_\zeta]$ | income supplied on the arrival-to-decision transition |
| $V[>]$ | `Field` | $\mathrm{ContinuationField}\cap\mathrm{ValueField}\cap\mathrm{Dom}[\mathsf L]$ | continuation random field |
| $\mathrm v_\succ$ | `Value` | $\mathsf V_\succ$ | specified measurable representative |
| $g_\succ$ | `Transition` | $\operatorname{Gr}(\Gamma)\times\mathsf Z_\eta\to\mathsf X_\succ$ | $g_\succ(m,c)=m-c$ for a trivial post-decision shock |
| $G_\succ$ | `Kernel` | $\mathsf L\times\operatorname{Gr}(\Gamma)\times\mathsf Z_\eta\to\mathsf L$ | $G_\succ(v,m,c,\eta)=\mathrm u(c)+\beta v$ where defined |
| $G^{\mathrm{out}}_\succ$ | `Kernel` | $\mathsf L\times\operatorname{Gr}(\Gamma)\to\mathsf L$ | the identity $G^{\mathrm{out}}_\succ(w,m,c)=w$ in the buffer-stock example |
| $G_\prec$ | `Kernel` | $\mathsf L\times\mathsf X_\prec\times\mathsf Z_\zeta\to\mathsf L$ | identity $G_\prec(v,k,\zeta)=v$ |
| $\mathrm u$ | typed function | $\mathbb R_{++}\to\mathbb R$ | utility function |

Here $0<\beta<1$ is the discount factor. The constraints and integrability conditions of the buffer-stock example remain additional to these type declarations. Declaring utility inside an aggregator does not remove its function type. The value field and its representative are related by P6; their evaluation is not an equality between a sort carrier and the value domain.

<a id="5-remarks-and-open-questions"></a>

## 6 Remarks and open questions

- A field's value domain, its space of random variables, and its representative-function space must remain distinct. [Fields, functions and types](./04-fields%2C%20functions%20and%20types.md) now uses this distinction throughout.
- Local functions retain typed parameters and results after substitution. Operators retain their domain/codomain types whether or not an operator-valued sort is introduced.
- A transition and a probability kernel are distinct objects: a measurable transition with its shock law induces a kernel. Rewards, conditional laws, and policy selection additionally determine Bellman evaluation.
- Domain refinement uses $D_f\subseteq D$, not $D_f=D$. The exact-domain fibers form a different partition and do not provide the same inclusion order.
- A discrete state domain is model data; a numerical grid approximating a continuous domain is the grid component of an operator's signature, a sort of its own (§3, Step 6). An encoding or embedding does not by itself establish a declared subsort relation.
- Whether to add a greatest `Function` sort encompassing value and policy functions is a further design choice. Connectedness alone cannot provide it. The general source-level treatment of all such intersection and kind constructions remains a design question; this appendix states the local conventions needed for its propositions.

<a id="6-sources"></a>

## 7 Sources

- Goguen, J. A., Thatcher, J. W., Wagner, E. G., and Wright, J. B. (1977). Initial algebra semantics and continuous algebras. *Journal of the ACM* 24(1), 68–95, §2, pp. 69–75. Signatures, carriers, and their interpretations.
- Martí-Oliet, N., and Meseguer, J. (1996). Inclusions and subtypes I: First-order case. *Journal of Logic and Computation* 6(3), 409–438, §2.1, Definition 2.2, p. 413. Declared subsort order requires compatible carrier inclusion.
- Meseguer, J. (1998). Membership algebra as a logical framework for equational specification. *WADT 1997*, LNCS 1376, 18–61. Background for distinguishing ambient kinds from membership in sorts.
