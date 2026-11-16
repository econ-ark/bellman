---
title: Fields, functions and types
short_title: Fields
status: drafted — Phase 1
tags:
  - bellman-calculus
  - field
  - semgraph
  - perch
  - syntax
  - semantics
  - initial-algebra
authors:
  - Christopher Carroll
  - Akshay Shanker
wip_revision: docs/bellman-calculus/04-fields-functions-and-types--WIP-revision.md  # in-progress draft revision of this chapter (not canonical)
audience: user
type: theory
topic: [calculus]
---

# Fields, functions and types

> [!summary]
> Fields name random quantities at a stage’s information sets. Their representing functions state how those quantities depend on the chosen state and any retained controls. We explain the assumptions behind substitution, the distinction between explicit definitions and implicit relations, and how the same authored model determines value recursion and distribution propagation.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md) defines state spaces, transition expectations, and backward builders.
> **Used by** — [Stages](../Bellman-Sym/01-stage.md) declares the fields in `.bl`; Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) gives the binding and state-representation rules, and its [Appendix D](../Bellman-Sym/appendices/15-appendix-d-node-tag-and-field-indexing.md) specifies local arguments, substitution, and retained outputs; [Methodization](../Bellman-Sym/04-methodization.md) states the supported addresses and attachment forms.

<a id="1-why-fields-the-declaration-problem"></a>

## 1. Declaring quantities and equations

[Stages and perches](./03-Stages%20and%20perches.md) names the two backward builders of a stage,

$$
\mathbb{T}_{\succ,\pi} : \mathsf{V}_\succ \to \mathsf{V}_\sim,
\qquad
\mathbb{T}_{\prec} : \mathsf{V}_\sim \to \mathsf{V}_\prec,
$$

and their composition is the **policy-evaluation Bellman operator** for the stage,

$$
\mathbb{T}_{\pi} = \mathbb{T}_{\prec}\circ\mathbb{T}_{\succ,\pi}.
$$

These are the central objects of a [recursive dynamic program](../wiki/recursive_decision_process.md) — the objects to which numerical and methodological assumptions attach. They are not, however, what a modeler should have to write down by hand each time they build an application. The surface syntax should ask for something closer to the economics: the concrete quantities — assets, income, consumption — and the equations relating them.

For the buffer-stock stage, the transition equations are

$$
m=Rk+y,\qquad a=m-c,
$$

with $k\geq0$, income $y>0$, $R>0$, and feasible consumption $0<c\leq m$. The stage declares these relationships, its utility function, discount factor $0<\beta<1$, income law, and choice rule. The stage syntax of [Bellman-SYM](../wiki/sym.md) specifies their `.bl` authoring form.

The [illustrative example](./02-Illustrative%20example.md) places next period's income expectation in the continuation function on assets. For a supplied measurable function $v_\succ$ on assets, the optimizing decision operator is

$$
(\mathbb T_\succ v_\succ)(m)
=\sup_{0<c\leq m}\{u(c)+\beta v_\succ(m-c)\}.
$$

For fixed $m$, the right side is a value; as $m$ varies, it defines a function. We require the displayed values to be well-defined and the output to belong to the chosen function domain. A fixed measurable feasible consumption policy $\pi$ instead gives

$$
(\mathbb T_{\succ,\pi}v_\succ)(m)
=u(\pi(m))+\beta v_\succ(m-\pi(m)).
$$

These are different operators. A supremum need not be attained, and an attained optimum still requires a measurable policy selection when a policy is needed. The fields and their representing functions allow the pointwise and function-valued statements to be connected explicitly.

<a id="so-what"></a>

### 1.1 Binding and composition

A **binder** introduces a local variable in an expression. In a supremum over consumption, consumption is bound; in an income integral, income is bound. The integrand may also depend on a free continuation function and on other state arguments. A grammar and its abstract syntax tree can record the binder and its body. Interpreting their scope and substituting expressions without capturing another local variable require the contextual rules of Bellman-SYM's Appendix C, §2.5 and rule R4.

The **composition** of two operators applies the first and then the second when their domains match. Here $\mathbb T_\prec\circ\mathbb T_{\succ,\pi}$ evaluates the decision value under $\pi$ and then the arrival value. The source equations, types, and bound and free arguments determine these operations under their declared mathematical assumptions. Arithmetic is parsed, and local scopes remain relevant after parsing. The operator description supplements the economic equations; it does not require the modeler to author an independent second model.

<a id="variables-as-fields"></a>

### 1.2 Variables as fields

A **field** is a named random variable that a stage declares ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §5). A field other than a shock is measurable at its **perch**, one of the arrival, decision, or continuation information sets. On the underlying probability space $(\Omega,\Sigma,\mathbb P)$, a field $Z$ at perch $p$ takes values in its declared set $D$ and is measurable with respect to $\mathcal F_p$. A realization $Z(\omega)$ is a point of $D$; the field itself is not that point.

The state vector $X_p$ takes values in the state space $\mathsf X_p$. A measurable function $z:E\to D$, on a measurable domain $E\subseteq\mathsf X_p$, represents the field when $X_p\in E$ and $Z=z(X_p)$ almost surely. This requires a version of $Z$ measurable with respect to $\sigma(X_p)$, the information generated by the state; a version agrees with $Z$ almost surely. Measurability with respect to the larger $\mathcal F_p$ alone is insufficient. Relevant conditional laws and payoff arguments must also be determined by the chosen state. A declared set such as $\mathbb R$ establishes neither integrability nor square integrability of $Z$.

Fields are classified by **perch**, **role**, **declared set**, and **origins**, the arrival states, shocks and choice on which they depend ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §5). Perch marks `[<]`, the unmarked decision form (equivalently `[~]`), and `[>]` identify information contexts. The roles are state, control, value, shock and multiplier, the last being the multiplier of a constraint on a choice. A shock takes its role from its law, is supplied on a transition with its timing, and belongs to no perch. In `.bl`, a type is written after a colon, its components with `@` between them, and the components are conditions that hold together ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §3, D7); §2 of Bellman-SYM's Appendix C specifies those declarations.

For a continuation value field, $\mathrm V_\succ=v_\succ(\mathrm X_\succ)$ almost surely. Its representing function $v_\succ:D_\succ\to\mathsf L$ has measurable domain $D_\succ\subseteq\mathsf X_\succ$. It maps states to the field's declared set $\mathsf L$; evaluation at a point $x_\succ$ gives a scalar $v_\succ(x_\succ)$, while evaluation at $X_\succ$ gives the random field. The declared set may include extended values only when the expressions involving them remain defined. We do not introduce a separately authored `V_fn` source variable.

In the stage syntax the derivative of a value is read by a derivative term, `D_{a}V[>]`, the operator applied to the declared value field in the coordinate of its subscript; it is no field and has no role. Three different objects must not be conflated in one identifier. `D_{x}` is an operator, the derivative with respect to the variable in its subscript applied to the function that follows it — `D_{c}(𝑢)` is the function c ↦ ∂𝑢/∂c, and `D_{a}V[>]` is the derivative of the continuation value in savings — and it is never glued into a name. A derivative line, `D_{m}V = 𝑑𝑢(c)`, states what the derivative of the value its builder writes equals. A name such as `𝑑𝑢` is an ordinary function name the modeler chose, whose letters mean nothing to the language; it may be defined through the operator (`𝑑𝑢 := D_{c}(𝑢)`) or in closed form (`𝑑𝑢(c : ℝ₊₊) := c^(-ρ)`). In that example $\rho>0$ is the coefficient of relative risk aversion, and the marginal-utility function has positive-real argument and result domains.

For the buffer-stock stage, the mathematical declarations are:

| Field | Perch or transition | Role | Declared set | Meaning |
|---|---|---|---|---|
| $k$ | arrival | state | $\mathbb R_+$ | assets on arrival |
| $y$ | arrival to decision | shock | $\mathsf Z_\zeta\subseteq\mathbb R_{++}$ | income observed before choice |
| $m$ | decision | state | $\mathbb R_{++}$ | resources |
| $c$ | decision | control | $\mathbb R_{++}$, with $c\leq m$ | consumption |
| $a$ | continuation | state | $\mathbb R_+$ | assets after consumption |
| $\mathrm V_\succ$ | continuation | value | $\mathsf L$ | continuation value field |

The constraint $c\leq m$ relates two quantities; it is additional to the declared set $\mathbb R_{++}$. The derivative term `D_{a}V[>]` requires a differentiable representing function where it is read; neither the term nor a derivative line proves differentiability or positivity. [Appendix D](./APPX-D-KINDS-AND-SORTS.md) formalizes the classifications. The [field](catalogues/fields.md), [function](catalogues/functions.md), and [operator](catalogues/operators.md) catalogues collect the objects used here.

Declared functions keep their typed arguments and result domains when their bodies are substituted into another expression. An argument local to a utility function is distinct from a same-named stage control. A constant field has empty state dependence in both its value and its domain. Its value may be a number, a table or a measurable function; it remains a field rather than a parameter. The perch classifier gives the earliest information at which a field is known, and the origins classifier records the arrival states, shocks and choice on which it depends (Appendix D §5).

An operator has a domain and a codomain too, the space it reads and the space it writes; they are the carriers of the source sort and the target sort that form its **rank** ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §§3 and 6).

> [!note] One authored model
> In the buffer-stock stage the transition $a=m-c$, together with utility, discounting, and the feasible set, determines the optimizing decision operator displayed in §1. The income transition and its specified law determine the arrival expectation. Under a fixed policy, those transitions also determine the induced distribution laws. The forward reading uses the transition and policy; the backward reading additionally uses the authored value evaluation and, if requested, optimization.

The field and explicit-function diagrams are two mathematical representations of these same equations under the stated assumptions. The intended construction derives them from one `.bl` source, with its arithmetic and binding interpreted; the source contract does not itself establish completed software support. The temporary parsed tree is not an independently retained second source.

<a id="2-the-field-diagram-what-the-modeller-declares"></a>

## 2. Field equations

The **field diagram** records the typed fields and the equations that relate them. Declared state coordinates determine the state vector at each perch. If a decision state has coordinates $m\in\mathbb R_{++}$ and $h\in\mathbb R_+$ with no further joint restriction, its state space is $\mathbb R_{++}\times\mathbb R_+$. The declarations constrain the fields' values; they do not turn random fields into deterministic scalars.

The forward maps $g_\prec$ and $g_\succ$ determine later state coordinates from the required state, control, and shock arguments. A **forward state transition** is one equation producing a state field. A **backward field transition** is one equation producing a value-type field. Backward equations specify the latter fields’ values, including fields such as age and a borrowing bound. An expectation is applied where it is authored and under its conditional-law assumptions, not inserted merely because an intermediate expression mentions a later shock.

A transition with several outputs must determine every declared output. An explicit definition names a function once its dependencies and domains are established. An implicit equation instead specifies a relation in its unknowns; it defines a function only where uniqueness or a specified selection, with the required measurability, supplies one. Attaching a numerical handler does not establish existence, uniqueness, or optimality of its solution.

Explicit definitions may be substituted in dependency order, preserving local binding, controls, shock arguments, and every declared output. A fresh left-hand name alone does not make an equation explicit if the right side depends on the unknown being determined. Bellman-SYM's Appendix D, §§2–5, gives these rules. Named computation boundaries do not conceal dependencies or convert an implicit relation into an assignment.

For the buffer-stock stage, the field diagram is small:

```text
┌───────────────┐  g≺    ┌───────────────┐  g≻    ┌────────────────┐
│  arrival  ≺   │ ─────▶ │  decision  ·  │ ─────▶ │ continuation ≻ │
│   k : ℝ₊      │        │   m : ℝ₊₊     │        │   a : ℝ₊       │
└───────────────┘        └───────────────┘        └────────────────┘
   g≺ : m = R·k + y                         g≻ : a = m − c
```

The arrows are the declared transitions $g_\prec$ and $g_\succ$ of [Stages and perches](./03-Stages%20and%20perches.md) §1.2, now annotated with their field equations. The diagram shows only the forward state transitions. The states of the three perches as vertices and the two transitions as edges form the declaration graph of the stage ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §6). The stage also needs its value equations and policy rule for backward evaluation; a transition alone does not determine preferences or optimal choice.

Larger stages change the names inside the boxes, not the discipline. A housing stage can carry decision state $(m,h)$, controls $(c,h')$, and continuation state $(a,h')$; the decision-to-continuation edge then has two output equations, not two separate topological arrows. A genuine disjoint union of continuation spaces is different: that is branching, and belongs to [Branching](./09-branching.md), not to the product structure of an unbranched perch.

Field diagrams compose through selected boundary pairings. A field belongs to its stage occurrence: a continuation field named $a$ in one stage and an arrival field named $a$ in another remain distinct until a connection pairs their eligible uses. Equal names can suggest a pair, but they establish neither its compatibility nor its economic meaning. If the names differ, as with post-decision assets $a$ closing one buffer-stock stage and beginning-of-period assets $k$ opening the next, a connector records the pairing without renaming either field.

The resulting coordinate map reads the destination's ordered state coordinates from the source's ordered continuation coordinates. A substantive law of motion, such as return accumulation or an income draw, remains a transition inside a stage, not a connector. The same connection pairs the later stage’s value-type outputs with the earlier stage’s required inputs. A backward field transition remains an equation inside its own stage. This is the field-level content of stage composition in [Stage composition](./07-stage-composition.md) and the trellis construction in [Periods and the trellis](./08-periods-and-trellis.md).

At this point we have a diagram, but not yet $\mathbb{T}_{\succ,\pi}$, $\mathbb{T}_{\prec}$, $\mathbb{M}_{\prec}$, or $\mathbb{M}_{\succ,\pi}$. The diagram represents the authored field equations; interpreting its complete context gives the functional operators.

<a id="3-the-morphism-upsilon-reads-syntax-into-mathematics"></a>

## 3. Interpreting equations

Write $\Upsilon$ for the interpretation from a typed expression, with its context and free inputs, to its mathematical meaning. Schematically,

```text
field equations with context  -- Υ -->  explicit functions and relations
```

A **signature** lists sorts and operation symbols, each symbol with its input and output sorts ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §3, D1). A **target algebra** supplies a mathematical set for each sort and an operation for each symbol. For an ordinary many-sorted signature, its ground terms (expressions with no free inputs) form an initial algebra: there is a unique operation-preserving interpretation into each specified target algebra. With free inputs, the corresponding free algebra additionally requires an environment assigning those inputs their meanings.[^adj] Binding and substitution require the context-sensitive interpretation discussed in §1.1; a list of symbol arities does not prove those rules.

This uniqueness is conditional on the supplied interpretation. It does not choose a missing shock law, a continuation-function representative, or a selection from an implicit relation. The full stage equations specify transition, value evaluation, and policy operations. Interpreting those equations yields the operators used to solve and simulate the model.

The functional representation retains the equations' inputs, outputs, and dependencies. Equal mathematical expressions may be substituted in a compatible context, but every declared output remains part of the resulting function. A boundary shared by adjacent stages identifies compatible fields rather than duplicating their authored definitions. Actual stage occurrences remain distinct objects. In a [modular model](./APPX-H-MODULARITY.md), repeated occurrences share their declaration’s calibration sources and operator family. Supplied field arguments may differ. Positional calibration remains permitted outside that modularity condition. The retained interpreted equation diagrams and definitions are described in Bellman-SYM's Appendices C and D.

<a id="4-the-functional-diagram-one-signature-two-readings"></a>

## 4. Functions and distributions

The **functional diagram** represents the declared equations using explicit state arguments, functions, and relations. Value recursion and distribution propagation use the same transitions and laws. They use different mathematical objects and operations, so their relation must be stated rather than inferred from a similar drawing.

<a id="41-backward-value-objects-and-the-builders"></a>

### 4.1 Value recursion

Let $\mathsf V_p$ be a specified domain of value functions at perch $p$ for which the relevant operations are defined. In the notation of [Stages and perches](./03-Stages%20and%20perches.md), the complete decision block defines either fixed-policy evaluation or optimization. The latter has the rank $\mathbb T_\succ:\mathsf V_\succ\to\mathsf V_\sim$, while arrival evaluation has the rank $\mathbb T_\prec:\mathsf V_\sim\to\mathsf V_\prec$. Thus

$$
\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ:
\mathsf V_\succ\to\mathsf V_\prec.
$$

These builders depend on the declared rewards, laws, feasible set, and policy operation in addition to the transition maps.

For buffer-stock, the decision edge $a=m-c$, with the supremum over feasible consumption, is read into

$$
(\mathbb{T}_\succ\,v_\succ)(m)
=
\sup_{0<c\le m}
\{u(c)+\beta\,v_\succ(m-c)\},
$$

while the arrival edge $m=Rk+y$ is read into

$$
(\mathbb{T}_{\prec}\,v)(k)=\mathbb{E}_y[v(R\,k+y)].
$$

These displays are not additional declarations. They are the value-side reading of the field diagram. The backward model of [Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §6 sends the arrival edge to $\mathbb T_\prec$ and the decision edge at a policy $\pi$ to $\mathbb T_{\succ,\pi}$; the optimizing decision builder $\mathbb T_\succ$ is formed from the builders at a policy and is the image of no edge. The notation in [Appendix E.3](catalogues/operators.md) records their ranks.

<a id="42-forward-measures-and-push-forwards"></a>

### 4.2 Distribution propagation

Write $\mathsf M_p$ for the finite measures on the state space $\mathsf X_p$, of which the probability measures are those of mass one ([Stages and perches](./03-Stages%20and%20perches.md) §1.2). The transitions and their specified conditional laws induce

$$
\mathbb M_\prec:\mathsf M_\prec\to\mathsf M_\sim,
\qquad
\mathbb M_{\succ,\pi}:\mathsf M_\sim\to\mathsf M_\succ,
\qquad
\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec.
$$

Here $\pi$ is a measurable feasible policy. It may be supplied for simulation or obtained by solving the backward problem under its optimality assumptions. A supremum alone supplies a value, not a chosen policy.

For a bounded measurable test function $f$, define the undiscounted expectation operators by

$$
(P_\prec f)(x)=\int f(g_\prec(x,\zeta))\,\mu_\zeta(\mathrm d\zeta\mid x),
$$
$$
(P_{\succ,\pi}f)(x)=\int f(g_\succ(x,\pi(x),\eta))\,
\mu_\eta(\mathrm d\eta\mid x,\pi(x)),\qquad
P_\pi=P_\prec\circ P_{\succ,\pi}.
$$

The first operator takes decision functions to arrival functions; the second takes continuation functions to decision functions. With $\langle\mu,f\rangle=\int f\,\mathrm d\mu$, their distribution pairing is

$$
\langle\mathbb M_\prec\mu,f\rangle=\langle\mu,P_\prec f\rangle,
\qquad
\langle\mathbb M_{\succ,\pi}\mu,f\rangle=\langle\mu,P_{\succ,\pi}f\rangle.
$$

The identities also hold whenever the displayed integrals are absolutely finite. They follow from integration against the induced transition laws; composition reverses the order of the paired operators. No bijection between value functions and probability measures is claimed. Reward-bearing $\mathbb T$ is not the paired linear operator: for constant-discount expected utility, $\mathbb T_{\succ,\pi}f=\bar r_\pi+\beta P_{\succ,\pi}f$, where $\bar r_\pi$ is expected reward under $\pi$.

Changing the income process changes the model and may require different sufficient state coordinates. Both forward and backward interpretations must use that revised state and law. Merely changing numerical integration for the same law is a method choice.

<a id="5-methods-attach-afterwards-refinement"></a>

## 5. Refinement and numerical methods

Nothing above is yet a numerical method. The map $\Upsilon$ produces mathematical operators. Methodization assigns methods to those operators; a handler supplies the numerical computation. This order matters: methods label operators that already have ranks and meanings; they do not supply the model's semantics.

Refinement first expands coarse operator symbols into finer terms. The optimizing continuation-to-decision builder decomposes into an aggregator kernel, its induced aggregator, and policy selection followed by insertion:

$$
\mathbb{T}_{\succ}
\;\longmapsto\;
\iota^{*}\circ\langle B_\succ,\ \operatorname{argmax}\circ B_\succ\rangle,
\qquad
\max
:=
\iota^{*}\circ\langle \mathrm{id}_{\mathsf Q_\Gamma},\ \operatorname{argmax}\rangle,
$$

In this composition display, $B_\succ$ denotes the map from a continuation function $f$ to the function $(x,a)\mapsto B_\succ(x,a,f)$. Here $\mathsf Q_\Gamma$ denotes the chosen functions on feasible state–action pairs, and `argmax` denotes a specified measurable maximizer selection on the domain where one exists. [Policy insertion](./catalogues/operators.md#policyinsertion) maps a choice-value function and a measurable feasible policy to the decision function $\iota^{*}(Q,\pi)(x)=Q(x,\pi(x))$. It differs from exact Evaluation, which carries the retained function unchanged into the function space of its output and neither supplies nor applies a policy. The display assumes attainment, compatible domains, and finite integrals. For the fixed independent shock laws used in [Stages and perches](./03-Stages%20and%20perches.md), $B_\succ$ is the induced aggregator

$$
B_\succ(x, a, v_\succ)
\;=\;
\int_{\mathsf{Z}_\eta}
G_\succ\bigl(v_\succ(g_\succ(x, a, \eta)),\,x,\,a,\,\eta\bigr)\,
\mu_\eta(\mathrm{d}\eta),
$$

and the arrival builder is the policy-free aggregator $\mathbb{T}_{\prec}\longmapsto B_\prec$, with $B_\prec(x_\prec, v)=\int_{\mathsf{Z}_\zeta}G_\prec(v(g_\prec(x_\prec, \zeta)),\,x_\prec,\,\zeta)\,\mu_\zeta(\mathrm{d}\zeta)$.

A statement that applies a map outside the expectation denotes the two-map form of [Stages and perches](./03-Stages%20and%20perches.md) §2.3a; the displays here are its case with the outer map the identity.

A **derived signature morphism** assigns each coarse operation symbol a typed expression in finer operations. When every assigned expression denotes exactly the original operation under the chosen target interpretation, substitution preserves the meaning of a composite term. Free inputs retain their fixed environment. This is the exact-refinement argument developed in [Appendix B](./APPX-B-INITIAL-ALGEBRA.md); it does not imply an approximation bound or convergence of numerical policies.

The diagram can retain a builder as a named computation with operations inside it. An equation marked `!node` requests an authored computation boundary; arithmetic, expectation, and other operator occurrences remain represented inside equations even without that mark. Adding or removing a boundary preserves the mathematical function a builder denotes while changing the diagram available to numerical methods: the marked equation's result is a function in the diagram, which later operations consume and a method may represent exactly, through its definition, or by an approximation such as an interpolant; an unmarked intermediate expression is part of the operation that uses it and offers no such point. Bellman-SYM's Appendix D, §§3–4, gives the distinction.

A method may address an entire builder or a supported operation within it. A named inversion represents the solution relation of its equation until uniqueness or a specified measurable selection makes it a function. Numerical interpolation, differentiation, or root finding supplies an algorithm, not the missing existence or optimality argument. The supported addresses and attachment forms belong to Bellman-SYM's rules for [methodization](../wiki/methodization.md).

A **cut** in an explanatory hierarchy chooses which composite operations are evaluated as units. Exact interpretation can agree at different levels when the substitution condition above holds. An approximate handler instead requires its own error bounds and stability assumptions before local errors can be related to the final solution. Initiality supplies neither numerical tolerances nor policy convergence. [Methods](06-Methods.md) distinguishes a numerical method from the operation it approximates; unfinished method details remain with their owning chapters.

<a id="see-also"></a>

## 6. Related documents

- **Across (siblings):** [Illustrative example](./02-Illustrative%20example.md), [Stages and perches](./03-Stages%20and%20perches.md), [Operators and builders](./05-Operators%20and%20builders.md), [Ingredients](./ingredients.md)
- **Down (semantic implementation):** [Appendix A — Semantics](./APPX-A-SEMANTICS.md) (the elaboration and its hooks), [Appendix B — Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) (initiality, valuation, refinement, and cuts), [Appendix D — Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) (formal kinds and sorts), [Appendix E — Catalogues](catalogues/index.md)
- **Wiki:** [expression](../wiki/expression.md), [semgraph](../wiki/semgraph.md), [sub-builder](../wiki/sub_builder.md), [aggregation](../wiki/aggregation.md), [statement](../wiki/statement.md), [branch](../wiki/branch.md), [functional form](../wiki/functional_form.md), [signature](../wiki/signature.md), [initial algebra](../wiki/initial_algebra.md), [Lawvere theory](../wiki/lawvere_theory.md), [syntax](../wiki/syntax.md), [semantics](../wiki/semantics.md), [Υ](../wiki/upsilon.md), [Ρ](../wiki/rho.md)

[Next → 05. Operators and builders](./05-Operators%20and%20builders.md)

[^adj]:
    Goguen, J. A., Thatcher, J. W., Wagner, E. G., and Wright, J. B. (1977). Initial algebra semantics and continuous algebras. *Journal of the ACM* 24(1), 68–95. §2, Proposition 2.1, p. 71, gives the initial algebra for a specified signature; Propositions 2.3 and 2.6, pp. 72 and 75, give the unique interpretation extending an assignment of free inputs.
