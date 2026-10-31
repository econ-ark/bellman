---
title: Ingredients — symbol reference
short_title: Ingredients
status: stub — symbol reference remains incomplete
tags:
  - bellman-calculus
  - catalogue
  - glossary
  - status/stub
audience: user
type: theory
topic: [calculus]
---
# Ingredients

> [!summary]
> This reference card lists the principal symbols used in the calculus. It distinguishes fields from their representing functions, fixed-policy evaluation from optimization, and transition expectation from reward-bearing Bellman operators.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md) defines the stage notation.
> **See also** — [Catalogues](./catalogues/index.md) gives the longer type and method inventories.
> **Used by** — [Symbol conventions](../Bellman-Sym/reference/symbols-conventions.md) and Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) §1.5 record the source notation for these symbols.

> [!note] Stub
> This reference remains incomplete. The table summarizes the settled symbols; it does not define an additional source grammar or certify numerical-handler support.

<a id="reading-guide"></a>

## 1. Reading guide

Follow the linked chapter for the domain restrictions and assumptions. At a perch $p\in\{\prec,\sim,\succ\}$, $\mathsf X_p$ is a measurable state space, $\mathsf V_p$ a chosen function space and $\mathsf L$ the value domain. Let $\mathsf A$ be the action space, $\Gamma(x)\subseteq\mathsf A$ the feasible actions and $\operatorname{Gr}(\Gamma)=\{(x,a):a\in\Gamma(x)\}$. The letters $x,a$ denote a generic state and action; in the buffer-stock example $m,c,a$ instead denote resources, consumption and assets after consumption.

<a id="symbols"></a>

## 2. Symbols

| Symbol | Meaning and type | Defining relation or qualification | Reference |
|---|---|---|---|
| $\mathcal F_\prec,\mathcal F_\sim,\mathcal F_\succ$ | available information at arrival, decision and continuation | $\mathcal F_\prec\subseteq\mathcal F_\sim\subseteq\mathcal F_\succ$; distinct from state sufficiency | [Stages](./03-Stages%20and%20perches.md) §1 |
| $X_p,\mathsf X_p$ | random state vector and its measurable state space | $X_p:\Omega\to\mathsf X_p$, where $\Omega$ is the outcome space | [Fields and functions](./04-fields,%20functions%20and%20types.md) §1 |
| $V_p,\mathrm v_p$ | value field and representing function | $V_p=\mathrm v_p(X_p)$ almost surely when state-generated measurability and representative-domain conditions hold; $\mathrm v_p\in\mathsf V_p$ | [Fields and functions](./04-fields,%20functions%20and%20types.md) §§1–2 |
| $\mathrm g_\prec$ | arrival transition | $\mathsf X_\prec\times\mathsf Z_\zeta\to\mathsf X_\sim$ | [Stages](./03-Stages%20and%20perches.md) §1 |
| $\mathrm g_\succ$ | controlled continuation transition | $\operatorname{Gr}(\Gamma)\times\mathsf Z_\eta\to\mathsf X_\succ$ | [Stages](./03-Stages%20and%20perches.md) §1 |
| $g_1,g_2$ | sub-transitions through an intermediate state | $g_\succ(x,a,\eta)=g_2(g_1(x,a),\eta)$ in the stated factorization | [Operators](./05-Operators%20and%20builders.md) §10 |
| $\Gamma$ | feasible-action correspondence | $\Gamma:\mathsf X_\sim\rightrightarrows\mathsf A$ | [Stages](./03-Stages%20and%20perches.md) §1 |
| $\zeta,\eta$ | pre-decision and post-decision shocks | random elements in $\mathsf Z_\zeta,\mathsf Z_\eta$ with declared conditional laws | [Stages](./03-Stages%20and%20perches.md) §1 |
| $\mathrm u,\beta$ | utility and discount in the consumption example | $\mathrm u:\mathbb R_{++}\to\mathbb R$, $\beta\in(0,1)$ | [Example](./02-Illustrative%20example.md) |
| $\mathrm G_\succ,\mathrm G_\prec$ | pointwise reward/continuation aggregators | scalar continuation value is first: $G_\succ(v,x,a,\eta)$ and $G_\prec(v,x_\prec,\zeta)$; a statement may supply an inner map inside the shock integral and an outer map outside it ([Stages](./03-Stages%20and%20perches.md) §2.3a) | [Functions](./catalogues/functions.md) §1 |
| $K_g$ | pullback along a measurable map $g$ | $K_gf=f\circ g$; functions on $g$'s codomain map to functions on its domain | [Operators](./05-Operators%20and%20builders.md) §2 |
| $\mathbb E_z$ | shock integration | maps an integrable function of retained arguments and $z$ to a function of retained arguments, using their conditional law for $z$ | [Operators](./05-Operators%20and%20builders.md) §5 |
| $B_\succ$ | induced aggregator, $\mathsf V_\succ\to\mathsf Q_\Gamma$ | $(B_\succ f)(x,a)=\int G_\succ(f(g_\succ(x,a,\eta)),x,a,\eta)K_\eta(x,a,d\eta)$, where $K_\eta$ is the conditional shock law; a map written outside the integral gives $G^{\mathrm{out}}_\succ(\int\cdots)$ ([Stages](./03-Stages%20and%20perches.md) §2.3a) | [Operators](./05-Operators%20and%20builders.md) §5 |
| $Q_f$ | choice-value function on $\operatorname{Gr}(\Gamma)$ | $Q_f=B_\succ f$; $\mathsf Q_\Gamma$ is the chosen class of such functions | [Operators](./05-Operators%20and%20builders.md) §7 |
| $\pi$ or $\sigma$ | feasible measurable policy, $\mathsf X_\sim\to\mathsf A$ | $\pi(x)\in\Gamma(x)$; optimality is additional | [Functions](./catalogues/functions.md) §1 |
| $\operatorname{argmax}$ | specified measurable maximizing selection on its admissible domain | maps suitable $Q$ to $\Pi_\Gamma$, the feasible measurable policies; requires attainment/selection | [Operators](./05-Operators%20and%20builders.md) §7 |
| $\operatorname{evaluate}$ | evaluate a choice value under a policy | $\operatorname{evaluate}(Q,\pi)(x)=Q(x,\pi(x))$; separate from ordinary function-at-state evaluation | [Operators](./05-Operators%20and%20builders.md) §7 |
| $\operatorname{upper\_env}$ | comparison of a specified candidate family | selected outputs and completeness/optimality requirements depend on the declared problem and method | [Operators](./05-Operators%20and%20builders.md) §7 |
| $\mathfrak w=Wf$ | post-decision expectation function, distinct from the operator $W$ | $W:\mathsf V_\succ\to\mathsf V_a$, $(Wf)(a)=\int f(g_2(a,\eta))K_\eta(a,d\eta)$ where this state/law factorization is valid; discounting is outside $W$ in this convention | [Operators](./05-Operators%20and%20builders.md) §10 |
| $\mathbb T_{\succ,\pi}$ | fixed-policy continuation-to-decision evaluation | $\mathbb T_{\succ,\pi}f=\operatorname{evaluate}(B_\succ f,\pi)$ | [Operators](./05-Operators%20and%20builders.md) §7 |
| $\mathbb T_\succ$ | optimizing continuation-to-decision operator | $(\mathbb T_\succ f)(x)=\sup_{a\in\Gamma(x)}(B_\succ f)(x,a)$; the selection/evaluation factorization requires attainment | [Operators](./05-Operators%20and%20builders.md) §7 |
| $\mathbb T_\prec$ | decision-to-arrival aggregation | $\mathbb T_\prec=B_\prec$ on specified function classes | [Operators](./05-Operators%20and%20builders.md) §5 |
| $\mathbb T_\pi,\mathbb T$ | fixed-policy and optimizing stage operators | $\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi}$; $\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ$ | [Stages](./03-Stages%20and%20perches.md) §2 |
| $P_\prec,P_{\succ,\pi},P_\pi$ | undiscounted transition expectations | $P_\pi=P_\prec\circ P_{\succ,\pi}$, distinct from reward-bearing Bellman evaluation | [Operators](./05-Operators%20and%20builders.md) §3 |
| $\mathbb M_\pi$ | probability propagation under a fixed feasible policy | $\langle\mathbb M_\pi\mu,f\rangle=\langle\mu,P_\pi f\rangle$ for bounded measurable or absolutely integrable tests, with $\langle\mu,f\rangle=\int f\,d\mu$ | [Operators](./catalogues/operators.md) §3 |
| $\mathbb T_{\mathrm{period}}$ | composition across a period's compatible boundaries | maps end-boundary functions to start-boundary functions; a self-map only under the required identification | [Stage composition](./07-stage-composition.md) §2 |
| $v^\star$ | stationary infinite-horizon fixed point when established | $\mathbb T_{\mathrm{period}}v^\star=v^\star$; existence/uniqueness/optimality require hypotheses | [Periods](./08-periods-and-trellis.md) §4 |
| $Q_j(x)$ | branch decision value at a common current state | includes the branch's current reward and continuation calculation, distinct from a function on its continuation state space | [Branching](./09-branching.md) §§4–5 |

The integral rows require joint measurability and pointwise integrability on their full declared domains. Independent shock laws are special cases of the conditional laws displayed here. A scalar field domain does not establish those analytic properties. The post-decision factorization is the alternative timing stated in its source section, not a redefinition of the running example's continuation boundary.

<a id="cross-references"></a>

## 3. Cross-references

- [Operators and builders](./05-Operators%20and%20builders.md) gives the mathematical definitions.
- [Semi-conjugacy](./10-semi-conjugacy.md) states the limits of operator reformulation claims.

[← Back to index](./index.md)
