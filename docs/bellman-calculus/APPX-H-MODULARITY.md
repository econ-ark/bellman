---
title: "Appendix H — Modularity"
short_title: "H. Modularity"
audience: user
type: theory
topic: [calculus]
---
# Modularity

> [!summary]
> In a modular model, repeated uses of a declaration share its operators and calibration rule. Fields remain arguments of those operators.

> [!info]- Relationship with other documents
> **Builds on** — [Kinds and sorts](APPX-D-KINDS-AND-SORTS.md) §§3 and 6 defines sorts and operator interpretations.
> **Builds on** — [Functional programming](APPX-G-FUNCTIONAL-PROGRAMMING.md) §6 defines calibration as evaluation.

## 1 Modular models

Let $K$ be a set of stage or period declarations. Copies and consistent renamings preserving sorts, equations and parameter roles retain their declaration's identity. Each declaration $s$ records its parameter sources in $b_s$. Let $\Theta$ consist of joint parameter assignments for which the stages satisfy [Kinds and sorts](APPX-D-KINDS-AND-SORTS.md) §6, with one parameter vector per declaration.

At each $\theta\in\Theta$, let $\mathcal S_\theta$ have declared sorts as objects and composable strings of symbols of the operator signature as arrows, including connections and declared period operators. Tuple-valued inputs or outputs may constitute one sort. Form $\mathcal O_\theta$ similarly from individual sort and operator occurrences. Composition concatenates strings with matching endpoints; empty strings are identities. Declaration labels fix the functor $q_\theta:\mathcal O_\theta\to\mathcal S_\theta$.

Let $\mathcal C$ be the category of sets and partial functions. The functors

$$
D_\theta:\mathcal S_\theta\to\mathcal C,
\qquad A_\theta:\mathcal O_\theta\to\mathcal C
$$

give the prescribed declaration meanings and independently specified occurrence meanings.

**Definition.** A model is **modular** if each occurrence of $s$ obtains its calibration from $b_s$, without binding rules addressed to positions, and

$$
A_\theta=D_\theta\circ q_\theta
\qquad(\theta\in\Theta).
\tag{1}
$$

Equality includes interpreting sets and partial functions with their domains. Methods and numerical settings are excluded. Identical calibration values do not establish the required binding rule.

## 2 Calibration and repetition

**Proposition.** Equation (1), as an equality of indexed families, holds if and only if $A_c=D_c\circ q_c$ at every $c\in\Theta$.

**Proof.** Evaluation selects one component and preserves composition. Conversely, equality at every component is equality of the families. ∎

Let $P$ be the positions and $t:P\to K$ their declaration assignment. Positions in the **fibre** $t^{-1}(s)$ share the operator family of $s$. Equation (1) also constrains constituent operations, which need not be determined by their composite.

For example, let a period update a field $z\in Z$ by $\tau:Z\to Z$. For each $z$, let $\mathcal V_z$ be its continuation-value space and $T_z:\mathcal V_z\rightharpoonup\mathcal V_{\tau(z)}$ its Bellman operator. Define

$$
X=\{(z,v):z\in Z,\ v\in\mathcal V_z\},
\qquad \Phi(z,v)=(\tau(z),T_zv).
$$

The partial map $\Phi:X\rightharpoonup X$ is defined where $v\in\operatorname{dom}T_z$ and remains fixed as $z$ changes. For $\Phi_M,\Phi_N:X\rightharpoonup X$ and positive integers $m,n$, the composite $\Phi_M^m\circ\Phi_N^n$ applies $N$ first, wherever successive applications are defined.

## 3 Natural isomorphisms

A natural isomorphism $\alpha_\theta:D_\theta\Rightarrow D'_\theta$, with $D'_\theta:\mathcal S_\theta\to\mathcal C$, consists of bijections commuting with every declared operation. Precomposition gives $\alpha_\theta q_\theta:A_\theta\Rightarrow A'_\theta$ when $A_\theta=D_\theta q_\theta$ and $A'_\theta=D'_\theta q_\theta$. Each component belongs to one declared sort and is used at every occurrence of that sort. Evaluation at $c$ selects $\alpha_c q_c$; this comparison does not replace (1).

## 4 References

Jacobs, B. (1999). *Categorical Logic and Type Theory*, §1.1, pp. 20–24: fibres and substitution.

Riehl, E. (2016). *Category Theory in Context*, §§1.4 and 1.7, pp. 25 and 47–49: natural transformations and composition with functors.
