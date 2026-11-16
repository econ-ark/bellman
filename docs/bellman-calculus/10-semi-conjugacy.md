---
title: Semi-conjugacy — relating different operator forms
short_title: Semi-conjugacy
status: not yet drafted — stub notes only
tags:
  - bellman-calculus
  - semi-conjugacy
  - sargent-stachurski
  - status/stub
audience: user
type: theory
topic: [calculus]
---

# Semi-conjugacy

> [!summary]
> These unfinished notes describe maps relating two recursive operators. A semiconjugacy maps iterations in one direction; recovering solutions or transferring convergence requires additional assumptions.

> [!info]- Relationship with other documents
> **Builds on** — [Operators and builders](./05-Operators%20and%20builders.md) defines the alternative value calculations.
> **See also** — [Methods](./06-Methods.md) separates numerical approximation from mathematical reformulation.
> **Formal account** — [Operator algebra](./APPX-F-OPERATOR-ALGEBRA.md) §6 states the limits of numerical convergence claims.

> [!note] Not yet drafted — stub notes only
> Structural outline only; the semi-conjugacy chapter is not yet written. The intended reference is Sargent and Stachurski, *Dynamic Programming*, volume 2, §5.2 and §8.3.4; the specific domain and stability arguments remain to be completed.

Let $\mathbb T_1:V_1\to V_1$ and $\mathbb T_2:V_2\to V_2$ be recursive operators on specified function classes. A **semiconjugacy** is a map $\varphi:V_1\to V_2$ satisfying

$$
\varphi\circ\mathbb T_1=\mathbb T_2\circ\varphi.
$$

This identity maps a sequence of exact iterates of $\mathbb T_1$ to one of $\mathbb T_2$. It also maps a fixed point of the first operator to a fixed point of the second. It does not by itself recover the original point, reach every point in $V_2$, or prove that the operators describe the same economic solution.

## 1. The semi-conjugacy square

*(Placeholder.)* Develop the identity above on the declared domains. If $\varphi$ is a bijection, its inverse gives a **conjugacy** and exact iterations and fixed points correspond in both directions. Convergence still depends on the chosen topology and continuity of the relevant maps.

<a id="2-worked-examples-recognising-semi-conjugacy-in-everyday-dp"></a>

When a repeated operator also updates fields such as a borrowing bound, its fixed-point problem is posed on the complete pair of those fields and the remaining representing functions. A comparison of value functions alone omits this update unless it is held fixed. [Periods and the trellis](./08-periods-and-trellis.md) states the corresponding partial map.

## 2. Candidate reformulations

### 2.1 The post-decision reformulation (EGM)

*(Placeholder.)* For a post-decision continuation function $\mathfrak w$ that includes the relevant discounting, the candidate map to a decision value is $\varphi(\mathfrak w)(m)=\sup_{c\in\Gamma(m)}\{u(c)+\mathfrak w(m-c)\}$. Here $m$ is resources, $c$ consumption, $u$ utility and $\Gamma(m)$ feasible consumption. The two recursive operators and function classes preserved by those operators must be specified, and the displayed operator identity must hold, before calling this a semiconjugacy. [Operators and builders](./05-Operators%20and%20builders.md) §10 supplies the post-decision factorization, not a general EGM equivalence theorem.

### 2.2 The $Q$-function reformulation

*(Placeholder.)* A choice-value function $Q$ is defined on feasible state–action pairs. The candidate map $\varphi(Q)(x)=\sup_{a\in\Gamma(x)}Q(x,a)$ gives its optimizing value, where $x$ is the current state and $a$ the action. An operator on choice values and its relation to the value operator remain to be specified. Attainment and a measurable selector are additional requirements if a policy is to be recovered.

### 2.3 Time-iteration on policies

*(Placeholder.)* Sargent and Stachurski relate Bellman value iteration to **Coleman–Reffett time iteration**, which updates a consumption policy through an Euler equation. It is not generic Howard policy iteration. Their construction appears in volume 2, §8.3.4, Lemma 8.3.11 and Proposition 8.3.12, pp. 290–291.

The correspondence is used here only conditionally: choose value and policy classes preserved by the respective operators, verify a well-defined bijection and the displayed operator identity, and check both directions of the proposed inverse. An inverse defined by integrating marginal utility requires finite improper integrals at zero. The convergence discussion in §8.3.4.2, p. 292, measures the distance between policies by the distance between their corresponding value functions; this distance must be finite on the chosen class. It does not automatically give ordinary uniform policy convergence. These domain and topology checks remain part of the unfinished derivation.

<a id="3-why-it-matters-for-bellman-calculus"></a>

## 3. Reformulation and numerical methods

Alternative value, choice-value and post-decision forms can provide different numerical opportunities when their mathematical relations are established. A method assignment does not itself establish those relations. *(Placeholder.)* Compare the forms under explicit solution-recovery and approximation conditions rather than treating every change of representation as answer-preserving.

## 4. Order-semiconjugacy (Sargent–Stachurski Vol II)

*(Placeholder.)* An order-preserving map respects the chosen pointwise order, but one such map satisfying the displayed identity does not transfer all fixed-point or stability results. Sargent and Stachurski's volume 2, §5.2, pp. 160–163, uses a stronger paired factorization and additional order/continuity assumptions for its correspondence and stability results. The required maps and hypotheses must be checked for each proposed reformulation; no general transfer theorem is asserted here.

<a id="see-also"></a>

## 5. Related documents

- [Methodization](../wiki/methodization.md) — numerical attachment to declared equations.
- [Operators and builders](./05-Operators%20and%20builders.md), [Methods](./06-Methods.md), and [Ingredients](./ingredients.md).
- Sargent and Stachurski, *Dynamic Programming*, volume 2, §5.2, pp. 160–163, and §8.3.4, pp. 290–292 (authors' May 2026 edition).

[← Back to index](./index.md)
