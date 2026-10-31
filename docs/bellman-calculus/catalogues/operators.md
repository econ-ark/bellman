---
title: "Appendix E.3 — Operators"
short_title: "E.3 Operators"
status: drafted
tags:
  - bellman-calculus
  - operator
  - builder
  - branching
  - catalogue
authors:
  - Akshay Shanker
audience: user
type: reference
---

# Appendix E.3 — Operators

> [!summary]
> This catalogue lists mathematical operations and their input and output types. It distinguishes transition expectation, reward-bearing evaluation and optimizing selection, and records the conditions needed for each operation. §4 names the eight operations a builder is composed of by the kinds under which the package prints them.

> [!info]- Relationship with other documents
> **Builds on** — [Functions](./functions.md) describes the model functions used by these operators.
> **Used by** — [Operations](../../Bellman-Sym/reference/operations.md) and [Shock distributions](../../Bellman-Sym/reference/laws.md), the reference catalogues of the language, whose rows link to what they denote here; [Field equations](../../Bellman-Sym/03-field-equations.md) and [Methodization](../../Bellman-Sym/04-methodization.md) give the block and method-target forms, and Bellman-SYM's [Appendix D](../../Bellman-Sym/appendices/15-appendix-d-node-tag-and-field-indexing.md) defines the supported method targets that §8 names.
> **Formal account** — [Operator algebra](../APPX-F-OPERATOR-ALGEBRA.md) qualifies composition, copying and numerical approximation.
> **See also** — [Methods](../06-Methods.md) discusses numerical procedures.

An **operator** maps objects in a declared domain to a declared codomain. Its **rank** lists its input and output sorts. In a first-order signature, operators can be operation symbols without an additional carrier of operator-valued data; they are nevertheless typed. Whether a builder is primitive or a named composite depends on the chosen signature.

At perch $p$, $\mathsf X_p$ is the state space, $\mathsf V_p$ a chosen value-function space, and $\mathsf M_p$ the probability measures on $\mathsf X_p$. Let $\mathsf L$ be the scalar value domain, $\Gamma(x)$ the feasible actions, $\mathsf Q_\Gamma$ the choice-value functions on $\operatorname{Gr}(\Gamma)=\{(x,a):a\in\Gamma(x)\}$, and $\Pi_\Gamma$ the feasible measurable policies. Domains below are restricted so the operations are defined, integrable when required, and closed under the stated compositions.

<a id="structural-morphisms-category-plumbing"></a>

## 1. Structural operations

These operations describe composition of inputs and alternatives. They do not alone prove that a software graph has a categorical universal property. Here $s,t$ denote types, $I$ the one-point type, $\otimes$ a product in the deterministic interpretation, and $\bigsqcup$ a labeled disjoint union.

| Operation | Rank | Role |
|---|---|---|
| $\Delta_s$ | $s\to s\otimes s$ | duplicate an input; duplicating one draw differs from independent resampling |
| $!_s$ | $s\to I$ | discard an input; probability propagation to a one-point space retains total mass |
| $\sigma_{s,t}$ | $s\otimes t\to t\otimes s$ | reorder paired coordinates |
| $\iota_j$ | $\mathsf X_j\to\bigsqcup_k\mathsf X_k$ | identify an alternative by its label |
| $[f_j]_j$ | $\bigsqcup_j\mathsf X_j\to\mathsf Y$ | apply the corresponding $f_j$ to a labeled input |
| $\operatorname{codiag}$ | $\bigsqcup_j\mathsf X\to\mathsf X$ | discard a label when all alternatives share the same state space |
| Connector | compatible boundary types | identify or rename fields between stages |
| Inter-period connector | compatible boundary types | identify or rename fields between periods |

A nonidentity state transformation must be authored explicitly; a connector renaming does not define it. Copying is available in the probability-kernel interpretation, but a general stochastic map need not preserve it. [Operator algebra](../APPX-F-OPERATOR-ALGEBRA.md) §§2–3 gives the distinction.

<a id="backward-builders"></a>

## 2. Backward builders

| Operator | Rank | Meaning |
|---|---|---|
| $\mathbb T_\succ$ | $\mathsf V_\succ\to\mathsf V_\sim$ | optimize the pointwise choice value over feasible actions |
| $\mathbb T_{\succ,\pi}$ | $\mathsf V_\succ\to\mathsf V_\sim$ | evaluate that choice value under a supplied policy |
| $\mathbb T_\prec$ | $\mathsf V_\sim\to\mathsf V_\prec$ | arrival aggregation and pre-decision shock integration |
| $\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ$ | $\mathsf V_\succ\to\mathsf V_\prec$ | optimizing stage evaluation |
| $\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi}$ | $\mathsf V_\succ\to\mathsf V_\prec$ | fixed-policy stage evaluation |

These are mathematical names, not prescribed YAML stage keys. Stage equations are `.bl`; current block and method-target forms belong to Bellman-SYM's pages on field equations and methodization.

<a id="forward-builders-measure-side"></a>

## 3. Forward builders and transition expectations

| Forward operator | Rank | Induced by |
|---|---|---|
| $\mathbb M_\prec$ | $\mathsf M_\prec\to\mathsf M_\sim$ | arrival transition and conditional shock law |
| $\mathbb M_{\succ,\pi}$ | $\mathsf M_\sim\to\mathsf M_\succ$ | decision transition, conditional shock law and policy |
| $\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec$ | $\mathsf M_\prec\to\mathsf M_\succ$ | composed stage transition |

The corresponding undiscounted expectations $P_\prec$, $P_{\succ,\pi}$ and $P_\pi=P_\prec\circ P_{\succ,\pi}$ act in the reverse direction on test functions. With $\langle\mu,f\rangle=\int f\,d\mu$,

$$
\langle\mathbb M_\prec\mu,f\rangle=\langle\mu,P_\prec f\rangle,
\qquad
\langle\mathbb M_{\succ,\pi}\mu,f\rangle=\langle\mu,P_{\succ,\pi}f\rangle.
$$

The equalities hold for bounded measurable test functions, or absolutely integrable evaluations. Reward-bearing $\mathbb T_{\succ,\pi}$ is not $P_{\succ,\pi}$: with constant discount $\beta$ and expected reward $\bar r_\pi$, it equals $\bar r_\pi+\beta P_{\succ,\pi}$. General arrival aggregation and optimization also remain outside this pairing.

<a id="primitive-operators"></a>

## 4. Constituent operations

The induced aggregator $B_\succ$ maps a continuation function to its choice-value function. It composes pullback along the law of motion, pointwise aggregation by the value aggregator and shock integration on every required feasible pair. The optimizing decision builder then takes two further steps, which the table keeps apart: $\operatorname{argmax}$ answers the set of maximizing policies and chooses none of them, and a selection chooses one member of that set.

For $Q\in\mathsf Q_\Gamma$ the **maximizing set** is

$$
\operatorname{argmax}Q=\bigl\{\pi\in\Pi_\Gamma : Q(x,\pi(x))\ge Q(x,a)\ \text{for every } x\in\mathsf X_\sim \text{ and every } a\in\Gamma(x)\bigr\},
$$

the feasible measurable policies that attain the maximum of $Q(x,\cdot)$ over $\Gamma(x)$ at every state. It is empty when that maximum is not attained at some state, and also when no measurable policy attains it at every state. A **selection** is a partial map $s:\mathsf Q_\Gamma\rightharpoonup\Pi_\Gamma$ with $s(Q)\in\operatorname{argmax}Q$ for every $Q$ in its domain $\operatorname{dom}s$, which is therefore contained in $\{Q:\operatorname{argmax}Q\neq\varnothing\}$. The maximizing set supplies no selection; a composite that needs one policy names its selection.

Every member $\pi$ of $\operatorname{argmax}Q$ gives $Q(x,\pi(x))=\max_{a\in\Gamma(x)}Q(x,a)$ at every state, so a composite of the form below takes the same value whichever selection it names. The optimizing decision builder, $(\mathbb T_\succ v)(x)=\sup_{a\in\Gamma(x)}(B_\succ v)(x,a)$ where that supremum lies in $\mathsf L$, is an explicit selection from the maximizing set followed by the insertion of the selected policy into the choice-value function:

$$
\mathbb T_\succ=\iota^{*}\circ\langle B_\succ,s\circ B_\succ\rangle\ \text{on}\ \{v\in\mathsf V_\succ:B_\succ v\in\operatorname{dom}s\},
\qquad
\mathbb T_\prec=B_\prec,
$$

that is, $(\mathbb T_\succ v)(x)=(B_\succ v)\bigl(x,s(B_\succ v)(x)\bigr)=\max_{a\in\Gamma(x)}(B_\succ v)(x,a)$. Where the supremum is not attained, or is attained by no measurable policy, the optimizing value has no representation of this form.

**Domains and assumptions.** $\Pi_\Gamma$ holds the measurable maps $\pi$ from $\mathsf X_\sim$ to the action space with $\pi(x)\in\Gamma(x)$ at every state, and $\mathsf Q_\Gamma$ holds functions on $\operatorname{Gr}(\Gamma)$ measurable for the σ-algebra that the product σ-algebra induces on it. Then $x\mapsto(x,\pi(x))$ is measurable for every $\pi\in\Pi_\Gamma$, so $\iota^{*}(Q,\pi)$ is a measurable function, and $\mathsf V_\sim$ is chosen to contain these functions. The maximizing set is nonempty, for example, when the action space is finite, $\Gamma(x)$ is nonempty at every state, and for each action the states at which it is feasible form a measurable set on which $Q(\cdot,a)$ is measurable (Sargent and Stachurski 2026, *Dynamic Programming*, vol. 2, Lemma 7.1.1), or when the state and action spaces are metric spaces with their Borel σ-algebras, the action space is separable, $\Gamma$ is nonempty, compact-valued and continuous, and $Q$ is continuous on $\operatorname{Gr}(\Gamma)$ (ibid., Lemma 7.1.2 and Theorem A.3.3). These conditions are sufficient and are not part of the definitions: the factorization states what $\mathbb T_\succ$ is on the domain of the named selection, and asserts nothing about which continuation functions lie in that domain.

In the display, $\iota^{*}$ inserts a policy into a choice-value function, as the table defines. The first column of the table names the **kind** of each operation, the name under which the package lists it among the operations of a builder; the last column links to the reference row that states which lines of a stage form an operation of that kind. $B_\succ$ has no kind: a builder lists it as the operations it is composed of.

| Kind | Operation | Domain and codomain | Meaning | Reference |
|---|---|---|---|---|
| <a id="pullback"></a>`Pullback` | $K_g$ | functions on the output space of $g$ → functions on its input space | pullback along $g$, $K_gf=f\circ g$ | [realized by](../../Bellman-Sym/reference/operations.md#pullback) |
| <a id="aggregation"></a>`Aggregation` | pointwise $G$ | tuples of functions on a common domain → functions on that domain | apply the aggregator at each point, $(f_1,\dots,f_k)\mapsto\bigl(z\mapsto G(f_1(z),\dots,f_k(z),z)\bigr)$; where the aggregated equation holds its own output on both sides, as a relation or a residual system, the operation is the implicit solution of §7 | [realized by](../../Bellman-Sym/reference/operations.md#aggregation) |
| <a id="expectation"></a>`Expectation` | $\mathbb E_z$ | integrable functions of retained arguments $h$ and shock $z$ → functions of the retained arguments | $(\mathbb E_zf)(h)=\int f(h,z)\,\mu(dz\mid h)$, integration against the conditional distribution $\mu$ of the shock | [realized by](../../Bellman-Sym/reference/operations.md#expectation) |
| — | $B_\succ$ | $\mathsf V_\succ\to\mathsf Q_\Gamma$ | construct choice values on all feasible state–action pairs; composed of the three operations above | — |
| <a id="argmax"></a>`Argmax` | $\operatorname{argmax}$ | $\mathsf Q_\Gamma\to\mathcal P(\Pi_\Gamma)$ | the maximizing set: every feasible measurable policy that attains the maximum at every state; possibly empty; chooses no member, a selection from it being a numerical method's | [realized by](../../Bellman-Sym/reference/operations.md#argmax) |
| — | $s$ | $\mathsf Q_\Gamma\rightharpoonup\Pi_\Gamma$ | a named selection, $s(Q)\in\operatorname{argmax}Q$, defined only where the maximizing set is nonempty | — |
| <a id="policyinsertion"></a>`PolicyInsertion` | $\iota^{*}$, with $\iota_\pi(x)=(x,\pi(x))$ | $\mathsf Q_\Gamma\times\Pi_\Gamma\to\mathsf V_\sim$; on measures, for each $\pi\in\Pi_\Gamma$, finite measures on $\mathsf X_\sim$ → finite measures on $\operatorname{Gr}(\Gamma)$ | insert the policy: $\iota^{*}(Q,\pi)=Q\circ\iota_\pi$, the choice value $Q(x,\pi(x))$ at the policy; on measures $\lambda\mapsto(\iota_\pi)_\#\lambda$, and $\langle(\iota_\pi)_\#\lambda,Q\rangle=\langle\lambda,\iota^{*}(Q,\pi)\rangle$ for bounded measurable $Q$ | [realized by](../../Bellman-Sym/reference/operations.md#policy-insertion) |
| <a id="evaluation"></a>`Evaluation` | $f\mapsto f$ | the derived carrier of an object, the set its construction places it in → its declared carrier, the set the stage declares it to lie in | the identity into the declared carrier: a function is carried as the same function and a set of policies as the same set; defined where the object lies in the declared carrier, and an inclusion where the derived carrier does; selects nothing | [realized by](../../Bellman-Sym/reference/operations.md#evaluation) |
| <a id="pushforward"></a>`Pushforward` | $g_\#$ | finite measures on the domain of $g$ → finite measures on its codomain | the image measure, $(g_\#\lambda)(B)=\lambda(g^{-1}(B))$ | [realized by](../../Bellman-Sym/reference/operations.md#pushforward) |
| <a id="distributionextension"></a>`DistributionExtension` | $\lambda\mapsto\lambda\otimes\mu$ | finite measures on retained arguments $H$ → finite measures on $H\times\mathsf Z$ | extend a measure by the conditional distribution of the shock, $(\lambda\otimes\mu)(B)=\int\mu(\{z:(h,z)\in B\}\mid h)\,\lambda(dh)$; followed by $g_\#$ it gives the Markov propagation of a transition with a shock | [realized by](../../Bellman-Sym/reference/operations.md#distribution-extension) |

An operation whose result is a set, the maximizing set here or the solution set of §7, keeps that set until a selection is named. Placing a builder's result in the declared space of its output selects nothing: a function is carried as the same function, and a set of policies as the same set.

At a policy $\pi$, a law of motion $g_\succ$ on the feasible pairs is read at the policy, $g_{\succ,\pi}=g_\succ\circ\iota_\pi$, a shock coordinate carried unchanged. Then $K_{g_{\succ,\pi}}=K_{\iota_\pi}\circ K_{g_\succ}$ and $(g_{\succ,\pi})_\#=(g_\succ)_\#\circ(\iota_\pi)_\#$, where $K_{\iota_\pi}Q=\iota^{*}(Q,\pi)$: a builder at a policy composes the insertion of the policy with the pullback or the push-forward along $g_\succ$.

<a id="shock-distribution"></a>

The **conditional distribution** $\mu$ of a shock with values in $\mathsf Z$, given retained arguments with values in $H$, is a probability kernel: $\mu(\cdot\mid h)$ is a probability measure on $\mathsf Z$ for each $h\in H$, and $h\mapsto\mu(B\mid h)$ is measurable for each measurable $B\subseteq\mathsf Z$. A distribution that reads no retained argument is constant in $h$. The expectation integrates against it, the distribution extension extends a measure by it, and the shock discretization of §7 approximates it.

The value of a function at a point and a numerical interpolation of that function are different descriptions: a numerical routine may interpolate internally, and representing a function on a grid adds no operation to this catalogue.

For an invertible transformation $\varphi$ on the relevant value domain, a certainty equivalent may take the form $R_z^\varphi=\varphi^{-1}\circ\mathbb E_z\circ\varphi$ when the integrals and inverse are defined. It reduces to expectation for $\varphi=\mathrm{id}$. This formula does not make every recursive preference a single local integrand; that extension remains unfinished. #todo

A vector shock can be integrated sequentially with its conditional laws, under the conditions for iterated integration. Replacing those laws by independent marginals requires independence; the tower property does not supply it. Intermediate numerical integrations do not introduce new information perches by themselves.

<a id="derived-named-operators"></a>

## 5. Named composites

A named expression can remain a derived operation or be treated as a primitive symbol in a coarser signature. Exact agreement with its expansion is the condition in [Initial-algebra semantics](../APPX-B-INITIAL-ALGEBRA.md) §4.

| Composite | Rank | Meaning |
|---|---|---|
| $\max=\iota^{*}\circ\langle\mathrm{id},s\rangle$ | $\operatorname{dom}s\to\mathsf V_\sim$ | an explicit selection from the maximizing set followed by the insertion of the selected policy: $(\max Q)(x)=Q(x,s(Q)(x))=\max_{a\in\Gamma(x)}Q(x,a)$, the same for every selection $s$ whose domain holds $Q$ (§4) |
| $W=\mathbb E_\eta\circ K_{g_2}$ | continuation functions → post-decision functions | $Wf(a)=\int f(g_2(a,\eta))\,\mu_\eta(d\eta)$ |
| $\max_J$ | $\mathsf L^J\to\mathsf L$ for finite nonempty $J$ | largest branch value |
| $\mathbb E_J$ | $\mathsf L^J\to\mathsf L$ for a fixed finite probability vector | weighted branch value |

The post-decision value function is $\mathfrak w=Wf$. Its derivative $\mathfrak w'$ is the marginal value function where differentiability holds; in the language it is the derivative operator applied to the value field, the term `D_{a}V[>]`, and is no field of its own. Additive expected utility with constant discount separates the choice value into reward plus $\beta Wf$ after the appropriate post-decision transition. A general nonlinear aggregator need not have that separation. [Operators and builders](../05-Operators%20and%20builders.md) §10 fixes the timing convention.

<a id="branching-operators"></a>

## 6. Branch values and envelopes

For finite alternatives, a vector of branch values is the input to the maximum or weighted expectation. A single labeled value in a disjoint union is not that vector. Agent choice determines a policy; exogenous selection uses a declared conditional law. A persistent regime remains in the state where it affects future laws or payoffs. These economic choices are not interchangeable numerical methods.

| Operation | Domain and codomain | Role |
|---|---|---|
| Envelope selection | specified candidate-value/control representation → selected representation | compare candidates at common states under the declared criterion |

Envelope selection belongs to a numerical method and is not an operation a stage states: the comparison of candidates at common states is internal to the method. No envelope routine automatically resolves missing candidates, policy ties or convergence; [Methods](../06-Methods.md) discusses the numerical distinctions.

<a id="implicit-and-auxiliary-operators"></a>

## 7. Implicit and auxiliary operations

| Operation | Domain and codomain | Conditions |
|---|---|---|
| Implicit solution | a relation in unknown functions and given functions, such as a residual system $r(z,u(z))=0$ → the set of tuples of measurable functions that satisfy it at every point of its stated domain | the set may be empty or hold several members; a composite that needs one member names a selection from it, as §4 does for the maximizing set; that a member maximizes an objective is a separate statement |
| Differentiation | differentiable functions → derivative functions | coordinate and differentiation domain specified |
| Gradient | differentiable scalar functions → vector-valued derivatives | one partial derivative per coordinate |
| Shock discretization | specified law/kernel → finite approximation | approximation of that fixed law; source attachment remains method-specific #ambiguity |
| Linear solution | compatible $(A,b)$ → selected solution of $Ax=b$ | uniqueness or a specified solution rule |

> [!note] Derivatives and names
> A derivative operation and a name given to a function are distinct. Differentiation of a declared function in one of its formal coordinates yields a function, and the derivative term on a value field, `D_{a}V[>]`, yields the derivative of that value; naming a function defines nothing further, and no field stands for a derivative. [Functions](./functions.md) describes their types.

> [!note] Iterated transitions
> Stationary distributions are fixed points of probability propagation; tail behavior is an asymptotic property. They require further assumptions and analysis beyond a one-step transition or finite branch operation. This catalogue does not prohibit defining a solver operator for them.

<a id="addressable-sub-nodes-field-level-not-omega"></a>

## 8. Authored computation boundaries

Stage equations and definitions are authored in `.bl`. Block identifiers are addresses, not reserved formula names such as `InvEuler` or `MarginalBellman`. A marked `!node` retains an authored computation boundary; operation occurrences and dependencies can remain inside an unmarked equation. An implicit statement remains a relation until its selection conditions are met. The supported method targets are defined by Bellman-SYM's Appendix D, rather than inferred from this mathematical inventory.

## 9. Related documents

- [Operator algebra](../APPX-F-OPERATOR-ALGEBRA.md) — mathematical composition and approximation conditions.
- [Methods](../06-Methods.md) — numerical procedures and their requirements.
- [Operators and builders](../05-Operators%20and%20builders.md) and [Branching](../09-branching.md).
