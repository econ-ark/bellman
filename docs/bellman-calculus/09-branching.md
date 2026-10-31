---
title: Branching — discrete choice and coproduct continuations
short_title: Branching
status: not yet drafted — stub notes only
tags:
  - bellman-calculus
  - branching
  - discrete-choice
  - dcegm
  - status/stub
audience: user
type: theory
topic: [calculus]
---

# Branching

> [!summary]
> These unfinished notes distinguish choices between labeled alternatives from exogenous branch selection. Branch values must be evaluated at the same decision state before comparison, with feasibility and selection conditions stated.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md) supplies the decision-state and continuation-value conventions.
> **Formal account** — [Operator algebra](./APPX-F-OPERATOR-ALGEBRA.md) §5 states the finite-branch interpretation.
> **Used by** — [Branching](../Bellman-Sym/05-branching.md) gives current source examples; Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) reads their selection and evaluation forms.

> [!note] Not yet drafted — stub notes only
> Structural outline only; the branching and coproduct chapter is not yet written.

A branch label distinguishes alternative continuations, such as work or retirement. A finite disjoint union can represent those labeled state spaces. A product state, by contrast, records several coordinates of one state; these constructions serve different purposes.

## 1. The coproduct continuation

For a finite number $N$ of alternatives, a labeled continuation state space may be represented as a disjoint union:

$$
\mathsf{X}_\succ \;=\; \mathsf{X}_{\succ,\,1} \,\sqcup\, \mathsf{X}_{\succ,\,2} \,\sqcup\, \ldots \,\sqcup\, \mathsf{X}_{\succ,\,N},
$$

one summand per branch $j$. *(Placeholder.)* Each branch has its own law of motion, possibly its own dimensionality, and its own continuation value $v_{\succ, j}$.

<a id="2-the-diagnostic-when-is-the-continuation-actually-a-coproduct"></a>

## 2. Labeled alternatives and state coordinates

A disjoint union records a label even when two alternatives use the same underlying state space or differ only in parameters. Conversely, different transition formulas do not by themselves force a particular representation. Choose a representation that retains the information needed for future laws, rewards and feasible choices. *(Placeholder.)* The relation between labeled alternatives and a common state space with a label coordinate remains to be explained.

## 3. Worked examples

<a id="31-work-or-retire-iskhakovjrgensenrustschjerning-2017"></a>

### 3.1 Work or retire

The agent at the decision perch chooses $d \in \{\text{work}, \text{retire}\}$. *(Placeholder.)* Retirement is absorbing only when the declared retired route excludes return to work. Let $Q_{\mathrm{work}}(m)$ and $Q_{\mathrm{retire}}(m)$ be branch decision values at current resources $m$, including branch-specific rewards, transitions and any conditional continuous optimization. When the relevant maxima exist,

$$
v(m) \;=\; \max\bigl\{\, Q_{\mathrm{work}}(m),\; Q_{\mathrm{retire}}(m)\,\bigr\}.
$$

A numerical candidate-envelope method may compare the branch candidates when its feasibility, coverage and selection conditions hold.

<a id="32-default-or-repay-arellano-2008"></a>

### 3.2 Default or repay

The sovereign chooses $d \in \{\text{repay}, \text{default}\}$. *(Placeholder.)* The model specifies the default regime, market access and any return to borrowing. Its continuation can be represented by a labeled alternative; the representation alone does not determine its state dimension or economic rules.

<a id="33-housing-adjust-or-keep-iskhakovkruegerpavoni-2020-and-the-dc-egm-literature"></a>

### 3.3 Adjust or keep housing

The household chooses $d \in \{\text{adjust}, \text{keep}\}$. *(Placeholder.)* The declared housing transitions and feasible regions determine the difference between the alternatives.

<a id="4-aggregation-at-the-branch-point-agent-max-vs-nature-expectation"></a>

## 4. Choice and exogenous selection

Let $Q_j(x)$ be the branch decision values on a common current state $x$. There are two distinct aggregations:

- **Agent choice:** $v(x)=\max_{j\in J(x)}Q_j(x)$ for the finite nonempty feasible label set $J(x)$, with a specified measurable maximizing selection when a policy is needed.
- **Exogenous selection:** $v(x)=\sum_j p(j\mid x)Q_j(x)$ for declared conditional branch probabilities $p(j\mid x)$.

*(Placeholder.)* Develop numerical methods for these declared operations. A persistent regime requires the state to retain its relevant information; the label need not be a separate coordinate if a sufficient state already encodes it.

> [!note] Selection and numerical envelopes
> Finite choice and continuous choice can both be written as optimization, while a finite mixture is an expectation. Their domains and economic interpretation remain distinct. An envelope operation compares a specified candidate family and selected outputs; numerical candidate comparisons may also be internal to a method. An `upper_env` name does not guarantee candidate completeness, optimality or convergence. Ties may have positive probability, including under atomless state laws.

<a id="41-canonical-kernelpolicy-form-agent-max-branch"></a>

### 4.1 Branch values and policies

The mathematical decomposition is

$$
\pi(x)\in\operatorname*{argmax}_{j\in J(x)}Q_j(x),
\qquad
v(x)=Q_{\pi(x)}(x),
$$

where a measurable selection is required for $\pi$ to be an admissible policy. Equal branch values need not select a unique branch. Differentiating the selected branch gives a value derivative only under the appropriate envelope and differentiability conditions; no such conclusion is automatic at a tie.

Stage and branch equations are authored in `.bl`. The modeler chooses block and control names, including the branch label. Current branch indexing and authored selection/evaluation forms are specified in Bellman-SYM's Branching page and in rules R8 and R12 and §4.7 of its Appendix C. These source rules do not infer missing rewards or maximization conditions.

<a id="5-the-conditional-unconditional-value-function-convention"></a>

## 5. Choice-conditional values

A **choice-conditional value** is the value of a specified branch, evaluated at the current decision state after accounting for that branch's reward and continuation problem. The optimized value is the maximum over feasible branch values, as in §4. This must not be confused with a continuation function on a branch's next-state space. *(Placeholder.)* Complete the literature discussion and worked calculations for these examples.

<a id="see-also"></a>

## 6. Related documents

- **Across:** [Fields, functions and types](./04-fields,%20functions%20and%20types.md), [Methods](./06-Methods.md), [Ingredients](./ingredients.md)

[Next → Semi-conjugacy](./10-semi-conjugacy.md)
