---
title: Illustrative example
short_title: Illustrative example
status: drafted — Phase 1
tags:
  - bellman-calculus
  - foundations
  - mdp
  - stage
  - perch
authors:
  - Akshay Shanker
  - Christopher Carroll
audience: user
type: theory
topic: [calculus]
---
# Illustrative example

> [!summary]
> We use the buffer-stock consumption–savings problem to factor a Bellman equation through assets held after consumption. The factorization separates the income transition from the consumption choice and identifies three information sets within a stage. We distinguish policy evaluation from optimization, and the propagation of distributions from reward-bearing value recursion.

> [!info]- Relationship with other documents
> **Formal account** — [Stages and perches](./03-Stages%20and%20perches.md) defines the stage and its information sets.
> **See also** — [Fields, functions and types](./04-fields,%20functions%20and%20types.md) distinguishes random fields from their representing functions.
> **Used by** — Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) states the conditions for state representation and forward/backward pairing.

> [!note] A note on notation
> Throughout, unless otherwise stated, three categories are written in two types. A function is italic, so $v\colon \mathbb{R}_{+}\rightarrow \mathbb{R}$ is a value function and $g$ a law of motion. A field is a roman capital with the same letter, $\mathrm V_\succ$ for the value at the continuation perch. A variable is italic as in ordinary mathematics, and a scalar value is written $w$. Roman type also carries the symbols that name no quantity of the model: the differential $\mathrm d$, the identity $\mathrm{id}$, and the kernels $\mathrm P$ and $\mathrm K$. The notion of a value is developed further in [Fields, functions and types](./04-fields,%20functions%20and%20types.md), where **[fields](../wiki/field.md)** are introduced as the central object in Bellman calculus.

<a id="the-primitive-form-bellman-equation"></a>

## 1. Bellman equation

The buffer-stock consumption–savings problem (Deaton 1991; Carroll 1997)[^buffer-stock] is the standard continuous-state model of consumption under income risk.

--8<-- "examples/buffer-stock/_buffer-stock-running-example.md"

**Two readings.** Under a fixed consumption policy, the transition describes the state sequence $k_t \to m_t \to a_t \to k_{t+1}$, with $m_t = R\,k_t + y_t$, $a_t = m_t - c_t$, and $k_{t+1} = a_t$. Backward recursion uses the same law to evaluate next period's value at $m_{t+1}=R\,a_t+y_{t+1}$. The shock occurs at the start of the next period in both readings. Its expectation appears in the current choice value because the agent evaluates future income risk before consuming.

**Why factor the equation.** The equation defines a Bellman operator on a suitable function space.[^slp-operator] Writing the income transition and the consumption transition separately makes their reuse explicit. We may form an expected continuation function before optimizing, provided that it retains every state argument needed for the conditional income law. This does not allow an expectation to be moved arbitrarily through a supremum: the choice must still use only information available when it is made.

> [!note]- Functions, random states, and code
> A value function $v$ maps states to values. If $\mathrm M$ is a random state, then $v(\mathrm M)$ is a random variable; if $m$ is a realized state, then $v(m)$ is a value. Both evaluations are mathematically valid when their domains match and the required measurability holds. In an integral over income, the income variable is bound, while the continuation function remains an input. Bellman-SYM's Appendix C, §1.2 and rule R4, distinguishes these objects and bindings.
>
> The corresponding programming discipline is **referential transparency**: an expression may be replaced by its denotation without changing the computation.[^stoy] Reading a value array from mutable external storage can make a routine depend on more than its explicit inputs. Passing the continuation function and declaring the transition separately makes those dependencies visible. Conventional mathematical notation does not itself violate this discipline.

<a id="modular-representation-of-the-problem"></a>

## 2. Modular representation of the problem

First we split the bundled transition $m_{t+1} = R\,(m_t - c_t) + y_{t+1}$ into the two events it conflates, and rename the resulting states by their *position in the stage* rather than by date. Then we drop the time subscripts, name the operators that act on the value functions defined at each position, and introduce the structure that makes the stage modular, developed in full in [Stages and perches](./03-Stages%20and%20perches.md).

**Forward transitions.** The primitive transition form above bundles return-and-income with the consumption choice. Let's split it as follows: at the start of period $t$, return and income realize on yesterday's assets,

$$
m_t = R\,a_{t-1} + y_t,
$$

after observing $m_t$, the agent chooses $c_t$, leaving assets,

$$
a_t = m_t - c_t.
$$

Three states now sit *inside* a single period: $k_t \equiv a_{t-1}$, the **arrival state**, assets held before income resolves; $m_t$, the **decision state**, the object on which the choice is conditioned; and $a_t$, the **continuation state**, assets after the choice and after all of this period's shocks have resolved. The boundary between this period and the next is the identity $k_{t+1} \equiv a_t$, which identifies the asset coordinate at the continuation perch with the asset coordinate at the next arrival perch.

**Backward operators.** Write $v_\succ$ for a continuation value function on assets $a\geq0$, $v$ for a decision value function on resources $m>0$, and $v_\prec$ for an arrival value function on assets $k\geq0$. We assume that income draws have a common law $\nu$, independent of past information, and that $Rk+y>0$ on the states and shocks considered. These assumptions make assets sufficient for the next income transition; sufficiency does not require recovering all past observations. All expectations below require measurable integrands and finite absolute integrals; the Bellman formulas apply on continuation functions for which their displayed values are finite.

The **optimizing decision operator** $\mathbb T_\succ$ maps continuation functions to decision functions:

$$
(\mathbb{T}_\succ\,v_\succ)(m) \;=\; v(m)
\;=\; \sup_{0 < c \le m}
\Bigl\{ u(c) + \beta\, v_\succ(m - c) \Bigr\}.
$$

This formula defines the objective on every feasible pair $(m,c)$, not just along a realized policy. For a fixed measurable feasible **policy** $\pi$, a consumption function satisfying $0<\pi(m)\leq m$ for every $m>0$, the **policy-evaluation operator** is instead

$$
(\mathbb T_{\succ,\pi}v_\succ)(m)
=u(\pi(m))+\beta\,v_\succ(m-\pi(m)).
$$

An optimal policy can be substituted here only when the supremum is attained and a measurable maximizer has been selected. We do not assume this solely from the displayed supremum.

The **arrival expectation operator** $P_\prec$ maps decision functions to arrival functions:

$$
(P_\prec\,v)(k) \;=\; v_\prec(k)
\;=\; \int v(R\,k+y)\,\nu(\mathrm dy).
$$

In this example the integration builder $\mathbb T_\prec$ is exactly $P_\prec$. It adds neither reward nor discount.

The subscripts $\succ$ and $\prec$ index the **continuation** and **arrival** information sets respectively; the decision value has no subscript when no ambiguity arises (written $v_\sim$ when the middle index needs to be displayed). #ambiguity [Note: characterise $\succ$ and $\prec$ formally as supremum and infimum of the stage's information sets — to be resolved in [Fields, functions and types](./04-fields,%20functions%20and%20types.md).]

**The stage operator.** Composing the two steps gives the **optimizing stage operator** $\mathbb T$ and, separately, the **policy-evaluation stage operator** $\mathbb T_\pi$:

$$
\mathbb T=P_\prec\circ\mathbb T_\succ,
\qquad
\mathbb T_\pi=P_\prec\circ\mathbb T_{\succ,\pi}.
$$

Both take a continuation value function as input and return an arrival value function. The three value functions are defined on states at the three **perches**, or information sets, of the stage: arrival, decision, and continuation. [Stages and perches](./03-Stages%20and%20perches.md) develops this arrival–decision–continuation structure.

> **The backward builders.** A builder specifies how a value function at one perch determines a value function at an earlier perch. Here $\mathbb T_\succ$ is the optimizing **Bellman builder**, $\mathbb T_{\succ,\pi}$ is its policy-evaluation counterpart, and $\mathbb T_\prec=P_\prec$ is the **integration builder**. Optimization followed by integration gives $\mathbb T$; evaluating a specified policy followed by integration gives $\mathbb T_\pi$.

**Forward–backward duality.** The distribution pairing concerns undiscounted transition expectations. Define $P_{\succ,\pi}$ on continuation test functions $f$ and $P_\pi$ on the same domain by

$$
(P_{\succ,\pi}f)(m)=f(m-\pi(m)),
\qquad P_\pi=P_\prec\circ P_{\succ,\pi}.
$$

Thus $P_{\succ,\pi}$ returns a decision function and $P_\pi$ an arrival function. For decision reward $r_\pi(m)=u(\pi(m))$, policy evaluation satisfies

$$
\mathbb T_{\succ,\pi}f=r_\pi+\beta P_{\succ,\pi}f,
\qquad
\mathbb T_\pi f=P_\prec r_\pi+\beta P_\pi f.
$$

The transition operators $P$ are linear on bounded measurable test functions, and on other integrable domains where the formulas are defined. Policy evaluation is affine: it is a linear map plus the fixed reward function. The supremum generally makes optimization nonlinear.

> **Forward builders.** A **pushforward** is the distribution induced by a transition. Write $\mathbb M_\prec$ for the operator taking an arrival law $\mu_\prec$ to the decision law under $m=Rk+y$, and $\mathbb M_{\succ,\pi}$ for the operator taking a decision law $\mu$ to the continuation law under $a=m-\pi(m)$. These operators act on probability measures on their respective state spaces. Their composition is $\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec$.

With $\langle\mu,f\rangle=\int f\,\mathrm d\mu$, the pairing identities for bounded measurable test functions are

$$
\langle\mathbb M_\prec\mu_\prec,v\rangle
=\langle\mu_\prec,P_\prec v\rangle,
\qquad
\langle\mathbb M_{\succ,\pi}\mu,f\rangle
=\langle\mu,P_{\succ,\pi}f\rangle,
$$

and hence

$$
\langle\mathbb M_\pi\mu_\prec,f\rangle
=\langle\mu_\prec,P_\pi f\rangle.
$$

The same identities apply whenever the displayed integrals are absolutely finite. They pair the forward operators with $P$, rather than with reward-bearing $\mathbb T$. [Periods and trellises](./08-periods-and-trellis.md) develops the forward composition.

<a id="what-is-new"></a>

### 2.1 Role of the representation

Bellman operators and factorizations through post-decision states have established treatments in dynamic programming (Bellman 1957; Stokey, Lucas, and Prescott 1989; Powell 2011). Here we give the income and decision operators separate names so that the stage's composition and its numerical treatment can be specified separately. The buffer-stock factorization establishes this representation for the stated income law and feasible choices; it is not a universality or priority claim for all recursive problems.

> **Scope of the builders.** In this example $\mathbb T_\succ$ uses a supremum and $\mathbb T_\prec$ an expectation. A different preference specification or information structure requires its own operators and assumptions. In particular, the linear distribution pairing above does not automatically extend to a nonlinear evaluation of risk.

> [!todo]
> **AAS to AI (7 Sep 2026):** The earlier note requesting more detail on the mathematical assumptions remains open. State any additional measure or topology assumptions where the subsequent construction requires them; the present example does not establish that such assumptions can always be dispensed with.

**Why builders.** The Bellman calculus distinguishes a mathematical operator from the numerical method used to evaluate it. **Methodization** attaches a numerical scheme to that operator, as developed in [Methods](./06-Methods.md). Numerical integration rules for a fixed income law are method choices. Replacing independent and identically distributed income by an autoregressive process of order one changes the economic model and generally requires retaining income as an additional state coordinate.

The intended source representation writes stage declarations and equations in `.bl` files. The YAML formats for [periods](../wiki/period.md), their connectors and [trellises](../wiki/trellis.md) specify how stages are composed. Methods files, numerical [settings](../wiki/settings.md) and [calibration](../wiki/calibration.md) specify numerical schemes and parameter values; specification recipes also remain YAML. The field and explicit-function representations express the same declared model under the state-sufficiency and binding conditions of Bellman-SYM's Appendix C; they are not separately authored models. This describes the target representation, not a claim that every part is implemented.

> [!objection]- Why do we need semantics for functions and operators?
>
> **Objection.** The transition $m_t=R\,a_{t-1}+y_t$ already states how resources depend on assets and income. Why name additional operators?
>
> **Counter-point.** The operator representation makes the inputs and composition explicit. Evaluating a function at a random state is valid; its result is a random variable. Evaluating it at a realized state gives a value. A state-space declaration alone does not establish that either evaluation is integrable. Keeping these distinctions explicit helps the numerical method use the intended conditional law and continuation function.
>
> Mathematical properties can be stated for an operator even when source code does not give it a separate name. Monotonicity (preservation of pointwise order) and contraction (reduction of distances in a specified function norm) require the appropriate assumptions on rewards, discounting, transitions, and function spaces; the notation does not prove them. Naming operators makes those assumptions and compositions easier to connect to a written model. It does not replace the mathematical argument.

**Wiring.** For the identity boundary $k_{t+1}=a_t$, the continuation function supplied to a stage is its successor's arrival value, $v_\succ=v_\prec^{\text{next}}$. The successor's arrival integration has already accounted for next period's income, so the current decision builder evaluates that function without integrating the same shock again. Backward composition of the optimizing operators, with the terminal condition stated above, reproduces the buffer-stock recursion. Composition of $\mathbb T_\pi$ instead evaluates specified policies. [Stages and perches](./03-Stages%20and%20perches.md) develops the interface; [Semi-conjugacy](./10-semi-conjugacy.md) discusses the relation between alternative placements of the expectation.

[Next → 03. Stages and perches](./03-Stages%20and%20perches.md)

[^buffer-stock]:
    Deaton, A. (1991). Saving and liquidity constraints. *Econometrica* 59(5), 1221–1248.

    Carroll, C. D. (1997). Buffer-stock saving and the life cycle/permanent income hypothesis. *Quarterly Journal of Economics* 112(1), 1–55.

[^slp-operator]:
    Bellman, R. (1957). *Dynamic Programming*. Princeton University Press.

    Stokey, N. L. and Lucas, R. E., with E. C. Prescott (1989). *Recursive Methods in Economic Dynamics*. Harvard University Press, §4.2, Theorem 4.6, p. 79, and §9.2, Theorem 9.6, p. 263.

[^stoy]:
    Stoy, J. E. (1977). *Denotational Semantics: The Scott-Strachey Approach to Programming Language Theory*. MIT Press, §1.1, pp. 5–7, on referential transparency and substitution.
