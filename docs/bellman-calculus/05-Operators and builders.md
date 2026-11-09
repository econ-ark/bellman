---
title: Operators and builders
short_title: Operators and builders
status: stub notes only
tags:
  - bellman-calculus
  - forward
  - backward
  - operator
  - builder
  - optimization
  - evaluate
  - status/stub
audience: user
type: theory
topic: [calculus]
---

# Operators and builders

> [!summary]
> These unfinished notes distinguish transition expectation, reward aggregation, policy selection, and a builder at a policy. They record the operator types and the assumptions needed when an implicit equation is interpreted as a function. The outline and its placeholders remain incomplete.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md) defines the stage operators and their information requirements.
> **Builds on** — [Fields, functions and types](./04-fields,%20functions%20and%20types.md) states the field and function distinction.
> **Used by** — Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md), whose rules R7–R10 distinguish evaluation, selection, and implicit relations, and its [Appendix D](../Bellman-Sym/appendices/15-appendix-d-node-tag-and-field-indexing.md), whose §7 distinguishes an implicit policy relation from a selection and which defines the source marks; [Field equations](../Bellman-Sym/03-field-equations.md) and [Methodization](../Bellman-Sym/04-methodization.md), the source forms and attachment forms of the operators defined here.

> [!note] Not yet drafted — stub notes only
> Structural outline and placeholders only; not yet a finished chapter.

An **operator** maps objects in a specified domain to objects in a specified codomain. A **builder** composes simpler operators into a value-recursion step. We use $\mathbb T_{\succ,\pi}$ for decision evaluation under a fixed policy, $\mathbb T_\succ$ for optimization, and $\mathbb T_\prec$ for arrival evaluation. The corresponding stage compositions are $\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi}$ and $\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ$. A **handler** is a numerical routine attached to an operator.

Here $\mathsf L$ is the scalar value domain, $\eta$ and $\zeta$ are the post-decision and pre-decision shocks on spaces $\mathsf Z_\eta$ and $\mathsf Z_\zeta$, and $\Upsilon$ interprets the declared equations as mathematical operations. At perch $p$, $\mathsf V_p$ is a chosen space of value functions on state space $\mathsf X_p$. The feasible state–action pairs form $\operatorname{Gr}(\Gamma)=\{(x,a):a\in\Gamma(x)\}$, and $\mathsf Q_\Gamma$ is a chosen space of choice-value functions on those pairs. Policies in $\Pi_\Gamma$ are measurable and feasible. These domains must make each displayed operation defined and closed under the required compositions. Every expectation below requires absolute integrability on its stated domain; fixed shock laws in the displays are conditional laws independent of the source information. State-dependent laws retain their conditioning arguments.

## 1. The forward reading

Forward operators act on **distributions** over state vectors; measurable transitions with specified shock laws induce **pushforwards**, the resulting distributions. *(Placeholder.)* Defines the push-forward (transfer / Perron–Frobenius operator); states the running example forward (the buffer-stock population transition).

## 2. The backward reading

The field reading starts from a random continuation field $\mathrm V_\succ$, a decision state $\mathrm X$, and a feasible decision action $\mathrm A$, with the latter two measurable at decision information $\mathcal F_\sim$. For integrable local payoff,

$$
\mathrm Q=\mathbb E[G_\succ(\mathrm V_\succ,\mathrm X,\mathrm A,\eta)\mid\mathcal F_\sim].
$$

This is a field identity along the chosen trajectory. To compare every feasible action, specify a continuation representative $v_\succ$, the transition, and the conditional shock law on all required states and actions. Then the pointwise choice value is

$$
B_\succ(x,a,v_\succ)
=\int_{\mathsf Z_\eta}G_\succ\bigl(v_\succ(g_\succ(x,a,\eta)),x,a,\eta\bigr)\,\mu_\eta(\mathrm d\eta).
$$

This is the form with the aggregation inside the integral. A statement may also apply a map outside it, $B_\succ=G^{\mathrm{out}}_\succ(\int\cdots)$, the two-map form of [Stages and perches](./03-Stages%20and%20perches.md) §2.3a.

The corresponding almost-sure representation requires $\mathrm V_\succ=v_\succ(\mathrm X_\succ)$ and state-generated measurability, as in [Stages and perches](./03-Stages%20and%20perches.md) §2.2. A value-domain declaration alone supplies no square-integrability claim. Selection chooses a policy; the transition, conditional shock law and aggregator indexed by that policy define the builder at the policy.

| Level | Input | Operation |
|---|---|---|
| Field | random continuation field and random state/action | conditional expectation of the integrable local payoff |
| Function | a specified continuation function | pullback along the law of motion, pointwise aggregation inside the integral, the authored shock integral, then any aggregation written outside it |

**Pullback along the law of motion** evaluates a function at the transition's output. A pointwise aggregation can also be applied to a function already expressed in the required arguments; no universal rule requires an immediately preceding substitution node.

<a id="3-conjugate-duality"></a>

## 3. Transition pairing

Write $\mathsf M_p$ for finite measures on $\mathsf X_p$, and $\langle\mu,f\rangle=\int f\,\mathrm d\mu$. Probability measures form the mass-one subset of $\mathsf M_p$. For bounded measurable functions, define the undiscounted transition expectations

$$
(P_\prec f)(x)=\int f(g_\prec(x,\zeta))\,\mu_\zeta(\mathrm d\zeta),
\qquad
(P_{\succ,\pi}f)(x)=\int f(g_\succ(x,\pi(x),\eta))\,\mu_\eta(\mathrm d\eta).
$$

The forward operators $\mathbb M_\prec:\mathsf M_\prec\to\mathsf M_\sim$ and $\mathbb M_{\succ,\pi}:\mathsf M_\sim\to\mathsf M_\succ$ satisfy

$$
\langle\mathbb M_\prec\mu,f\rangle=\langle\mu,P_\prec f\rangle,
\qquad
\langle\mathbb M_{\succ,\pi}\mu,f\rangle=\langle\mu,P_{\succ,\pi}f\rangle.
$$

*(Placeholder.)* Develop the pairing from integration against the transition laws. The formulas extend to absolutely integrable evaluations. They do not pair probability propagation with reward-bearing Bellman evaluation: in constant-discount expected utility, $\mathbb T_{\succ,\pi}f=\bar r_\pi+\beta P_{\succ,\pi}f$, where $\bar r_\pi$ is expected reward under $\pi$. Optimization and nonlinear aggregation remain separate operations.

## 4. Why the field graph supports both

The same authored `.bl` equations specify transitions, laws, and value evaluation. *(Placeholder.)* Explain how forward propagation uses the transitions and a supplied policy, while backward evaluation additionally uses the reward and policy rule. The field and function diagrams are representations of that model under their stated assumptions; a bare transition graph does not determine preferences.

<a id="5-operators-point-kernels-induced-aggregators-selection-and-evaluation"></a>

## 5. Evaluating and selecting actions

**How a builder becomes a term.** A builder equation is not a single edge but a typed composition inserted by the meaning map. The continuation-to-decision builder $\mathbb{T}_{\succ}$ factors through:

1. the **point backward kernel**

    $$
    G_\succ:\mathsf L\times\operatorname{Gr}(\Gamma)\times\mathsf Z_\eta\to\mathsf L,
    $$

    acting on a value variable, not a value function;

2. the **induced aggregator**

    $$
    B_\succ:\mathsf V_\succ\to\mathsf Q_\Gamma,
    \qquad
    (B_\succ v_\succ)(x,a)
    =
    \int_{\mathsf Z_\eta}
    G_\succ\bigl(v_\succ(g_\succ(x,a,\eta)),x,a,\eta\bigr)\,\mu_\eta(d\eta);
    $$

3. the **policy selection and indexed-builder layer**, on the domain of objectives admitting the specified measurable maximizer selection

    $$
    \operatorname{argmax}:\mathsf Q_\Gamma\to\mathcal P(\Pi_\Gamma).
    $$

    Here $\operatorname{argmax}Q$ is the possibly empty set of feasible measurable policies that maximize $Q$ at every state. On the domain where a measurable maximizer is specified, write

    $$
    s:\mathsf Q_\Gamma\rightharpoonup\Pi_\Gamma,
    \qquad s(Q)\in\operatorname{argmax}Q
    $$

    for the selection rule. Thus $\operatorname{argmax}$ states the maximizing correspondence, while $s$ supplies one policy. For each $\pi\in\Pi_\Gamma$, define the builder at that policy by

    $$
    (B_{\succ,\pi}v_\succ)(x)
    =
    \int_{\mathsf Z_\eta}
    G_{\succ,\pi}\bigl(v_\succ(g_{\succ,\pi}(x,\eta)),x,\eta\bigr)\,
    \mu_{\eta,\pi}(d\eta\mid x).
    $$

    Here the policy is part of the indexed law of motion, aggregator and conditional distribution. Exact Evaluation is an identity on a function or a set of feasible policies; it neither supplies nor applies $\pi$. In the endogenous grid method (EGM) and non-concave refinements a numerical method may also apply $\operatorname{upper\_env}$ to its candidate representation.

Thus

$$
\mathbb{T}_{\succ}v_\succ
=B_{\succ,s(B_\succ v_\succ)}v_\succ,
\qquad
(\max Q)(x)=Q(x,s(Q)(x)).
$$

The maximum is recovered on this attained-selection domain. Without attainment the optimizing value is a supremum and this selection formula need not be defined. For additive expected utility with constant discount, $B_\succ$ can be decomposed internally into pullback along $g_\succ$, Markov expectation over $\eta$, and reward aggregation. In the nonlinear-kernel case, that separation is not generally valid: $B_\succ$ is the displayed integral of the pointwise aggregator.

Numerical methods may approximate expectations by quadrature, simulation, or finite summation. A first-order inversion approximates the same optimum as direct maximization only under its feasibility, optimality, selection, and domain-coverage conditions. Interpolation and candidate-envelope comparisons may be internal steps of a numerical method; choosing that method does not add an authored envelope equation or change exact Evaluation. An authored envelope operation has its own mathematical meaning and assumptions. Supported attachment forms are specified by Bellman-SYM's rules for [methodization](../wiki/methodization.md).

The transition maps, shock laws, feasibility graph, and aggregator kernels are model data. They generate operators under $\Upsilon$, but their mathematical content is fixed by the stage declaration. A handler may fuse neighboring operators in the realized computation, but the model-side term remains the same. Which operators become separate code and which are lumped is a methodization choice — a *cut* through the operator hierarchy — not something the calculus fixes.

The decision-to-arrival builder $\mathbb{T}_\prec$ is the policy-free induced aggregator

$$
\mathbb{T}_\prec=B_\prec:\mathsf V_\sim\to\mathsf V_\prec,
\qquad
(B_\prec v)(x_\prec)
=
\int_{\mathsf Z_\zeta}
G_\prec\bigl(v(g_\prec(x_\prec,\zeta)),x_\prec,\zeta\bigr)\,\mu_\zeta(d\zeta).
$$

With the identity arrival aggregator, $G_\prec(w,x_\prec,\zeta)=w$, so $\mathbb{T}_\prec$ is the pure Markov expectation over the pre-decision shock. The difference between the two backward edges is not "max versus no max"; it is that the decision edge has a policy selection and an indexed-builder layer while the arrival edge does not.

There is a useful spectrum of how much of this composition to expose. A modeler may write a generated Bellman line such as
$v(x)=\sup_{a\in\Gamma(x)}B_\succ(x,a,v_\succ)$,
or may expose the induced aggregator and policy separately:
$Q=B_\succ(v_\succ)$, $\pi=s(Q)\in\operatorname{argmax} Q$, and
$v_\sim=B_{\succ,\pi}v_\succ$. These denote the same exact Bellman operator when the selection is greedy and measurable. Named equations can provide attachment points for methods that use post-decision values or marginal relations. A numerical recipe may instead compute intermediate objects internally; they need not all be authored equations.

<a id="6-builders-mathbbt_succpi-and-mathbbt_prec"></a>

## 6. Backward builders

A **builder** is a named composition of operators that constitutes a stage's input-to-output interface. The continuation-to-decision builder is

$$
\mathbb{T}_{\succ}v_\succ
=B_{\succ,s(B_\succ v_\succ)}v_\succ,
\qquad
\mathbb T_\succ:\mathsf V_\succ\to\mathsf V_\sim,
$$

and the decision-to-arrival builder is

$$
\mathbb{T}_\prec=B_\prec:\mathsf V_\sim\to\mathsf V_\prec.
$$

The full **optimizing stage operator** is $\mathbb{T}=\mathbb{T}_\prec\circ\mathbb{T}_{\succ}$. A fixed-policy builder is also available:

$$
\mathbb T_{\succ,\pi}v_\succ=B_{\succ,\pi}v_\succ.
$$

At the supplied continuation function, the fixed-policy builder equals the optimizing value whenever the policy selects a maximizer at every decision state. This need not be the particular selection supplied by $s$, and does not identify the two operators on all continuation functions. The selection and indexed-builder layer of a controlled-field builder is the subject of §7.

**The builder at a policy and the policy layer.** The builder at a policy is $\mathbb T_{\succ,\pi} \colon \mathsf V_\succ \to \mathsf V_\sim$, one operator for each $\pi \in \Pi_\Gamma$; $\mathbb T_\succ$ keeps its meaning above, the optimizing builder. The policy layer is a second operator, typed by its route. On the selection route, $s \circ B_\succ \colon \mathsf V_\succ \rightharpoonup \Pi_\Gamma$, where $s(B_\succ v_\succ)\in\operatorname{argmax}(B_\succ v_\succ)$ under the measurable-maximizer condition of §7.3. On the relation route, the method supplies a selection into $\Pi_\Gamma$ from the solution of an authored relation.

The semantic graph constructs the builder at a policy and the policy layer and does not compose them. In this construction, the decision builder is the operator at a policy, its signature the inputs and outputs of $\mathbb T_{\succ,\pi}$. The policy is a free name used by its indexed pullback, aggregation or conditional distribution, typed on the output of the policy builder and carried on no input wire. The policy builder stands in the same graph as its own part, inputs and output. Where a policy block reads a value the backward builders produce, that wire joins the two parts; no wire runs from the policy builder into a backward builder.

A method states how the two parts are combined: the optimizing rule $v_\succ\mapsto B_{\succ,s(B_\succ v_\succ)}v_\succ$ of value-function iteration, the alternation of policy evaluation and policy improvement of Howard, or a route through a first-order condition such as the endogenous grid. The abstract dynamic programs of Sargent and Stachurski have the same two-part form: a value poset with a family of policy operators $\{T_\sigma\}_{\sigma \in \Sigma}$ and a selection made outside the family. Their Bellman operator is $Tv = \bigvee_\sigma T_\sigma v$ whenever the supremum exists, and it equals the optimizing rule under the attainment and measurable-selection conditions of §7.3. In their recursive decision process $(\Gamma, V, B)$, the policy operator is $T_\sigma v = B(\cdot, \sigma(\cdot), v)$ and a greedy selector satisfies $\sigma(x) \in \arg\max_{a \in \Gamma(x)} B(x, a, v)$. Their operators are self-maps of one value space, so the counterpart of $T_\sigma$ is the stage composite $\mathbb T_\prec \circ \mathbb T_{\succ,\pi}$ under the period identification (Sargent and Stachurski 2025, *Dynamic Programming*, vol. 2, chapters "Abstract Decision Processes", sections "ADPs on Posets" and "The Bellman Equation", and "Recursive Decision Processes", sections "Definition" and "Existence of Greedy Policies"). A fixed-policy calculation uses the operator at a policy supplied from outside.

## 7. Policy selection and the builder at a policy

A controlled backward step separates the induced aggregator $Q=B_\succ(v_\succ)\in\mathsf Q_\Gamma$, the maximizing set $\operatorname{argmax}Q\subseteq\Pi_\Gamma$, a selected policy $\pi=s(Q)\in\operatorname{argmax}Q$, and the decision value $v_\sim=B_{\succ,\pi}v_\succ$. The surface may expose these as separate blocks or lines, but the semantic split is typed: $B_\succ$ constructs the objective, $\operatorname{argmax}$ gives its maximizing policies, $s$ selects one when the required selection exists, and $B_{\succ,\pi}$ contains the policy in its indexed transition, aggregator and conditional distribution.

<a id="71-the-objective-qb_succmathrm-v_succ"></a>

### 7.1 The choice-value function

The objective is the induced aggregator applied to the continuation value:

$$
Q(x,a)=(B_\succ v_\succ)(x,a)
=
\int_{\mathsf Z_\eta}
G_\succ\bigl(v_\succ(g_\succ(x,a,\eta)),x,a,\eta\bigr)\,\mu_\eta(d\eta).
$$

In expected-utility buffer-stock form this reduces to $Q(m,c)=u(c)+\beta\,v_\succ(m-c)$ when the post-decision shock is trivial. A map written outside the expectation gives the two-map form of [Stages and perches](./03-Stages%20and%20perches.md) §2.3a. Value function iteration (VFI), EGM under its applicability conditions, and policy iteration can use this same objective.

### 7.2 Selection and the indexed builder

The policy layer selects a policy, and the indexed builder returns the corresponding decision value:

$$
\pi=s(Q)\in\operatorname{argmax} Q,
\qquad
v_\sim=B_{\succ,\pi}v_\succ,
\qquad
v_\sim(x)=Q(x,\pi(x)).
$$

- **VFI / direct search:** calculate the maximizing set by maximizing $Q(x,\cdot)$ over $\Gamma(x)$ and apply the specified measurable selection $s$.
- **EGM / first-order inversion:** realize the same selection by solving the first-order or Euler relation, usually at an interior marginal node of $B_\succ$; if the endogenous-grid candidate needs envelope correction, apply $\operatorname{upper\_env}$ to the method's candidate representation before using the selected policy in the indexed builder.

The recipes are extensionally equivalent only under the usual optimality, monotonicity/concavity or envelope, and measurable-selection assumptions. The recipe specifies a numerical method for the stated mathematical operator.

The source can specify maximization or an implicit policy relation. After a continuation candidate has been defined, `c = c[>]` may identify the decision control implicitly through the saving transition. That equation remains a relation until a unique solution or a specified measurable selection determines a policy. The endogenous grid method approximates the relation by candidate pairs and interpolation; its numerical steps are not automatically authored operations. Bellman-SYM's Appendix D, §7, states the distinction.

### 7.3 Why split selection from the indexed builder

The traditional Bellman equation $v(x)=\sup_a B_\succ(x,a,v_\succ)$ gives the optimal value. Policy selection and the indexed builder provide its displayed decomposition under the stated attainment assumptions. The split keeps their types distinct. Direct search and first-order inversion can approximate the same selection target under the conditions stated above; their policies then index the law of motion, aggregator and conditional distribution. The bundled max form is recovered as

$$
(\max Q)(x)
=Q(x,s(Q)(x)),
\qquad s(Q)\in\operatorname{argmax}Q.
$$

## 8. The defined field function with a handler

An explicit equation defines a function once its inputs, dependencies, and domains are established. A fresh name on the left does not suffice if substitution reveals dependence on an undetermined output. A residual equation states a relation; uniqueness or a specified measurable selection is needed for a function, and optimality is a separate condition.

Examples retained for this outline:

- A forward residual $F(a',d,c)=0$ determines the unknown $a'$ only where existence and a suitable selection are established. Newton iteration is a numerical method for that relation.
- An interior first-order condition $\partial_c Q=0$ does not by itself handle bounds or establish a maximum. A first-order or endogenous-grid method requires the appropriate sufficiency and boundary conditions.
- A function represented at grid points needs an interpolation rule for evaluation between those points. The table alone does not determine those values.

Function, relation, selection, and evaluation have different domains and meanings. A handler computes or approximates the chosen interpretation; it does not supply its mathematical selection theorem.

## 9. Forward builders

A **forward builder** pushes a distribution from one perch to the next along the same declared transitions: $\mathbb{M}_\prec$ from arrival to decision along $g_\prec$, and $\mathbb{M}_{\succ,\pi}$ from decision to continuation along $g_{\succ,\pi}(x,\eta)=g_\succ(x,\pi(x),\eta)$. The policy $\pi$ is supplied by the policy selection layer, or externally for a fixed-policy calculation. In the semantic graph the decision push-forward is the push-forward at a policy, $\mathbb M_{\succ,\pi} \colon \mathsf M_\sim \to \mathsf M_\succ$, its signature the measure it reads and the measure it writes; the policy indexes the transition and any policy-dependent conditional distribution, is typed on the output of the policy builder, and is carried on no input wire (§6).

The transition pairing is the one stated in §3, with $P_\prec$ and $P_{\succ,\pi}$. An arrival reward, discounted continuation, or nonlinear aggregator is not part of those probability-transition expectations.

*(Placeholder.)* Describe the available forward methods for the declared discrete-time transition, such as simulation and histogram approximation. Continuous-time evolution equations require a different model and are not automatically handlers of the displayed discrete-time stage.

<a id="10-operators-inside-a-builder-sub-transitions-and-the-post-decision-value"></a>

## 10. Intermediate post-decision values

When the decision-to-continuation transition $g_\succ$ factors through an intermediate state, its induced aggregator $B_\succ$ can contain a named intermediate operation. What the EGM literature calls the post-decision value or marginal value is one such inner node, exposed so a policy handler can attach to it.

Some decision-to-continuation transitions factor through an **intermediate post-decision state** — the savings level $a = m - c$ in consumption-savings, the post-adjustment housing $h'$ in housing models. The factorization matters because the **post-decision value function** $v_{\mathrm{pd}}$ can be represented as an intermediate function on the endogenous grid.

### 10.1 The factorization

For the alternative consumption–savings timing whose continuation state is next-period resources, let $g_1(m,c)=a=m-c$ and $g_2(a,y')=Ra+y'$. This differs from the earlier stage boundary, where continuation is saving and the next arrival stage contains income integration:

$$
m \;\xrightarrow{\,g_1:\, a = m - c\,}\; a \;\xrightarrow{\,g_2:\, m' = R a + y'\,}\; m'.
$$

*(Placeholder.)* The composite is $g_\succ(m,c,y')=g_2(g_1(m,c),y')$. The income shock $y'$ enters in $g_2$, with $R$ the fixed return — *after* the decision. This is one **timing convention** used for the endogenous grid method (EGM); not all stages factor this way, but applicability of an endogenous-grid method requires its own factorization and invertibility or selection conditions.

### 10.2 The post-decision value function

In the affine expected-utility case, pulling the continuation value back along $g_2$ and integrating out the post-decision shock produces the post-decision expectation node

$$
v_{\mathrm{pd}}(a)
=
\int v_\succ(g_2(a,\eta))\,\mu_\eta(d\eta),
$$

and the induced aggregator is then $B_\succ(m,c,v_\succ)=u(c)+\beta\,v_{\mathrm{pd}}(m-c)$ when the reward is decision-measurable. Its marginal $v_{\mathrm{pd}}'(a)$ is used in the EGM first-order inversion where that marginal exists.

For a nonlinear aggregator kernel, do not assume this separation: the induced aggregator is the integral of $G_\succ(v_\succ(g_\succ(x,a,\eta)),x,a,\eta)$ as a whole. A map written outside the integral stays outside it ([Stages and perches](./03-Stages%20and%20perches.md) §2.3a).

### 10.3 The factored induced aggregator

Returning to generic state $x$ and action $a$ (rather than the savings variable of §10.1), the sub-transition factorization records where the post-decision shock enters:

$$
(B_\succ v_\succ)(x,a)
=
\int
G_\succ\bigl(v_\succ(g_2(g_1(x,a),\eta)),x,a,\eta\bigr)\,\mu_\eta(d\eta).
$$

In the affine case, this may be implemented as an interior Markov expectation node followed by reward aggregation. The policy selection still sits outside the indexed builder:

$$
\mathbb{T}_{\succ}v_\succ
=B_{\succ,s(B_\succ v_\succ)}v_\succ.
$$

This is the operator-level reading of EGM: the handler may expose the post-decision expectation or marginal node, solve for a candidate policy, optionally apply $\operatorname{upper\_env}$ to the candidate representation, and then use that policy in the indexed builder.

<a id="11-granularity--option-b-lite"></a>

## 11. Numerical decomposition

An EGM recipe needs the relevant transition and marginal information. It may obtain these from a builder or from supported named intermediate places, and may perform interpolation, envelope comparisons, and evaluation internally. *(Placeholder.)* This is the partial-decomposition setting: the builder may remain opaque except for the named intermediate nodes a handler needs. The explanation of supported intermediate places remains unfinished; Bellman-SYM's Appendix D defines current source marks and numerical attachment boundaries.

## 12. Correspondence with Sargent–Stachurski

| This folder | Recursive dynamic programming reading |
|---|---|
| $G_\succ(w,x,a,\eta)$ | value aggregator, the aggregator kernel acting on a value variable |
| $B_\succ(x,a,v)$ | induced recursive dynamic programming aggregator after pullback along the law of motion and shock integration |
| $B_\succ:\mathsf V_\succ\to\mathsf Q_\Gamma$ | objective constructor $v\mapsto[(x,a)\mapsto B(x,a,v)]$ |
| $\operatorname{argmax}:\mathsf Q_\Gamma\to\mathcal P(\Pi_\Gamma)$ | set of greedy measurable policies, possibly empty |
| $s:\mathsf Q_\Gamma\rightharpoonup\Pi_\Gamma$ with $s(Q)\in\operatorname{argmax}Q$ | specified measurable selector on its domain |
| $B_{\succ,\pi}:\mathsf V_\succ\to\mathsf V_\sim$ | builder whose transition, aggregator and conditional distribution are indexed by $\pi$ |
| $(\max Q)(x)=Q(x,s(Q)(x))$ | derived Bellman max on the selected attained domain |
| $\mathbb{T}_{\succ}v=B_{\succ,s(B_\succ v)}v$ | optimal continuation-to-decision builder on that domain |
| $\mathbb{T}_\prec=B_\prec$ | policy-free arrival aggregator |
| $\mathbb{T}=\mathbb{T}_\prec\circ\mathbb{T}_{\succ}$ | stage operator |

*(Placeholder.)* Verify the detailed literature correspondence and complete its citations; the table is an explanatory comparison, not a completed literature argument.

<a id="see-also"></a>

## 13. Related documents

- **Across:** [Stages and perches](./03-Stages%20and%20perches.md), [Fields, functions and types](./04-fields,%20functions%20and%20types.md), [Methods](./06-Methods.md), [Appendix F — Operator algebra](./APPX-F-OPERATOR-ALGEBRA.md), [Ingredients](./ingredients.md)

[Next → 06. Methods](./06-Methods.md)
