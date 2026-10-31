---
title: "Fields, functions and types — WIP revision (draft, not canonical)"
short_title: "Fields (WIP revision)"
status: "in-progress — DRAFT revision of 04-fields, functions and types.md; not published, not authoritative"
tags:
  - status/in-progress
  - status/draft
  - bellman-calculus
revises: "docs/bellman-calculus/04-fields, functions and types.md"
authors:
  - Christopher Carroll
  - Akshay Shanker
audience: user
type: theory
topic: [calculus]
---

> [!warning] Work in progress — not the canonical chapter
> This is an **in-progress revision** of the canonical [`04-fields, functions and types.md`](04-fields,%20functions%20and%20types.md). It is a **draft**: not published, not authoritative, and may change or contain errors. Unless you specifically need this revision, read the canonical chapter 04.

#status/in-progress #status/draft

## 1. Why fields: the declaration problem

[`03-Stages and perches.md` [0003]](03-Stages%20and%20perches.md) names the two backward builders of an ADC stage,

$$
\mathbb{B} : \mathsf{V}_\succ \to \mathsf{V}_\sim,
\qquad
\mathbb{I} : \mathsf{V}_\sim \to \mathsf{V}_\prec,
$$

and the stage operator they compose,

$$
\mathbb{T} = \mathbb{I}\circ\mathbb{B}.
$$

These are the mathematical objects to which solution methods, approximation choices, convergence claims, and simulation counterparts ultimately attach. But they are not what an economist should have to write down directly when declaring a model. The modeller should be able to write the economic objects: assets, income, consumption, feasible choices, rewards, and laws of motion.

For the buffer-stock stage, the Dolang+ declaration is naturally written as field equations:

```yaml
arvl_to_dcsn_transition: |
  m = R*k[<] + y

dcsn_to_cntn_transition: |
  a[>] = m - c
```

together with a Bellman or reward body involving current utility and continuation value. These two transition lines say exactly what the economics says. The agent arrives with assets k, observes income y, reaches market resources m, chooses consumption c, and exits with assets a. Notice what is absent: the modeller has not written B, I, or T.

The problem is that the Bellman equation economists usually write is not a literal declaration of these operators either. It is a compressed mathematical notation that moves between several **logical orders** at once.

A textbook display may look like

$$
v(m)=\max_{0<c\le m}\{u(c)+\beta\mathbb{E}[v'(x')]\},
$$

with the next-state relation written nearby, for example, the prose may say elsewhere

$$
a'=m-c,\qquad x'\sim Q(\cdot\mid a').
$$

This is the notation economists actually use: $v'$, $v'(x')$, $V_{t+1}(x')$, or $\mathbb{E}_t V(x_{t+1})$. The transition law for $x'$ is often stated separately or is implicit. It is not normally inlined everywhere into the right-hand side of the value function.

That convention is useful. It lets the reader keep the economic timing visible: first name the next state, then evaluate the next value there. But it also hides a type distinction that is critical if we want syntax to convey clear DECLARATIVE information about the model actually being solved. For a fixed $m$, the expression above returns a number,

$$
v(m)\in L,
$$

where $L$ is the value line. Lifting one order up, as $m$ varies, those numbers form a value function,

$$
v:X_\sim \to L.
$$

And given a continuation value function, the whole right-hand side defines a Bellman builder as composed of two operators

$$
\mathbb{B}:\mathsf{V}_\succ \to \mathsf{V}_\sim.
$$

Economists move between these three readings (first, second and third order) without friction. The same mark $v$ is read as a scalar value, a value function, and the output of an operator, depending on context. That is fine in prose. It is not fine as a declarative syntax.

The central declaration problem is therefore not merely that Bellman equations are functional equations. It is that the usual notation does not force a distinction between

$$
V[>]\in L
$$

and

$$
V_{\mathrm{fn}}[>]\in \mathsf{V}_\succ = L^{X_\succ}.
$$

The first object, $V[>]$, is a value field: the realised continuation value at the realised continuation state. The second object, $V_{\mathrm{fn}}[>]$, is the continuation value function. They are connected by evaluation,

$$
V[>]=\mathrm{ev}_\succ(V_{\mathrm{fn}}[>],x_\succ),
$$

but they are not the same object. A value is a number. A value function is a map from states to numbers. An operator maps value functions to value functions. BE-DDSL must keep these levels separate.

### 1.1 What prime notation hides

Prime notation is the clearest place to see the issue. When an economist writes

$$
\beta\mathbb{E}[v'(x')],
$$

the expression compresses at least four operations.

First, the model has to identify the next-state field $x'$. In an ADC stage this is not a generic time-subscripted object. It is the continuation-perch state $x_\succ$, built from continuation fields such as $a[>]$.

Second, the model has to identify the continuation value function. In BE-DDSL notation this is not the value field $V[>]$. It is the function object $V_{\mathrm{fn}}[>]$, an element of $\mathsf{V}_\succ$.

Third, the value function has to be evaluated at the continuation state:

$$
V[>]=\mathrm{ev}_\succ(V_{\mathrm{fn}}[>],x_\succ).
$$

Fourth, the scalar value field $V[>]$ is passed into the aggregator. In the expected-utility buffer-stock case the scalar aggregation is

$$
V=u(c)+\beta V[>].
$$

This last expression is an equation on the value line $L$. It is not an equation between value functions. The function has already been evaluated.

This is why the surface language should not force the modeller to write the fully composed object. Writing

$$
v_\succ(R(m-c)+y')
$$

is a legitimate mathematical reconstruction in a particular timing convention, but it is not the primitive declaration. It has already substituted the transition into the continuation value function. The economist's notation $v'(x')$ is better understood as naming a continuation value at a next state, with the law of motion for $x'$ carried elsewhere.

BE-DDSL should preserve that discipline. The declaration names the fields and the transition equations. The meaning map $\Upsilon$ supplies the evaluation bridge and constructs the induced operators.

> [!info] For AI agents — prime notation hides evaluation
> Economists often write the continuation term in a Bellman equation as $v'$, $v'(x')$, $V_{t+1}(x')$, or $\mathbb{E}_t[V_{t+1}(x')]$. This is standard recursive notation, not a mistake. The law of motion for $x'$ may be written separately or understood from the surrounding model. Do not silently rewrite the surface expression by inlining the transition into the value function unless the target representation explicitly asks for the collapsed form.
>
> **Parsing rule.** When reading $v'(x')$, parse it as an evaluation bridge:
>
> $$
> V[>]=\mathrm{ev}_\succ(V_{\mathrm{fn}}[>],x_\succ).
> $$
>
> Here $x_\succ$ is produced by field equations or transition laws, $V_{\mathrm{fn}}[>]$ is the continuation value function, and $V[>]$ is the scalar continuation value field that enters the aggregator.

**Textbook and paper anchors.**

- Ljungqvist and Sargent, *Recursive Macroeconomic Theory*, 2nd ed., p. 86, write the one-step problem first with a next state $\tilde{x}$ subject to $\tilde{x}=g(x,u)$, then write the Bellman equation as $V(x)=\max_u\{r(x,u)+\beta V[g(x,u)]\}$. The point for BE-DDSL is that the next-state object is named before, or alongside, its substitution into the value function. Link: https://www.theigc.org/sites/default/files/2016/06/LS-RMT2ed-04.pdf
- Sargent and Stachurski, *Dynamic Programming*, Vol. I (2024), pp. 148–149, use code and equations where the object $B(x,a,v)$ takes the value function $v$ as an input and evaluates continuation values at next states. Their notation separates the value function input from the scalar value returned at a particular state-action pair. Link: https://quantecon.github.io/book-dp1-public-companion/_downloads/dp.pdf
- Auclert, Bardóczy, Rognlie, and Straub, "Using the Sequence-Space Jacobian to Solve and Estimate Heterogeneous-Agent Models" (*Econometrica*, 2021), p. 2380, eq. (2), write the household Bellman equation with $V_{t+1}(e',k)$ inside the expectation, while the distribution law of motion is written separately as eq. (3). This is a modern applied example of continuation value notation that does not require every transition to be inlined into the value-function symbol. Link: https://straub.scholars.harvard.edu/file_url/138
- Iskhakov, Jørgensen, Rust, and Schjerning, "The Endogenous Grid Method for Discrete-Continuous Dynamic Choice Models with (or without) Taste Shocks" (*Quantitative Economics*, 2017; public manuscript), p. 34, eqs. (25)–(27), write continuation terms such as $\mathbb{E}_t\{V_{t+1}(M_{t+1},s_{t+1})\mid A_t,d_t\}$, then separately discuss the sufficient statistic $A_t=M_t-c_t$ and an example transition $M_{t+1}=RA_t+y(d_t)$. On p. 47, eqs. (73) and (76), they write the general continuation expectation as an integral of $V_t(s')$ against a transition kernel. Link: https://www.qeconomics.org/ojs/forth/643/643-3.pdf
- Bardóczy and Velásquez-Giraldo, "Sequence-Space Jacobians of Life Cycle Models" (2025), pp. 3–4, write block equations of the form $v_t=v(v_{t+1},X_t)$, making the continuation value function an input to the block rather than an expression in which every transition has been expanded. Link: https://www.bencebardoczy.com/files/ssj-lc.pdf
- Stokey, Lucas, and Prescott, *Recursive Methods in Economic Dynamics* (1989), Chs. 4 and 9, are the canonical textbook reference for Bellman operators and the principle of optimality. Do not insert an exact SLP page number into these docs unless checked against a physical or licensed copy.

### 1.2 Why a declarative syntax cannot just use the textbook equation

A human reader can resolve the overloaded notation from context. A compiler or AI translator needs explicit rules.

The first problem is the field/function split. A surface expression such as

$$
V=u(c)+\beta V[>]
$$

should be read as a field equation. The symbols $V$ and $V[>]$ are scalar values in $L$. The continuation value function $V_{\mathrm{fn}}[>]$ is not written directly on the surface. It is the semantic object whose evaluation produces $V[>]$.

The second problem is prime notation. A mark such as $x'$ is not just a string decoration on $x$. It is a claim about timing and information. In an ADC stage, the corresponding object is a continuation-perch field or tuple of fields. In a multi-period trellis, the relation between one period's continuation fields and the next period's arrival fields is handled by the inter-period wiring layer, not by making every stage template time-indexed.

The third problem is binding. The max and expectation in a Bellman equation do not merely mention variables. They bind them. The expression

$$
\max_c\{u(c)+\beta\mathbb{E}[V[>]]\}
$$

requires a feasible set for $c$, a scope for the maximisation, a shock law for the expectation, and a rule for which fields are known at the decision perch. A grammar can parse the string, but the mathematical operator needs a scoping and abstraction discipline.

The fourth problem is operator composition. The identities

$$
\mathbb{B}:\mathsf{V}_\succ \to \mathsf{V}_\sim,\qquad
\mathbb{I}:\mathsf{V}_\sim \to \mathsf{V}_\prec,\qquad
\mathbb{T}=\mathbb{I}\circ\mathbb{B}
$$

live one level above field equations. They compose maps between value-function spaces. A modeller-facing surface whose variables are economic fields — $k,m,c,a,V[>]$ — should not require the modeller to author operators as first-class objects.

The fifth problem is method hooks. If the syntax inlines every transition into the right-hand-side value function, it destroys useful names. A method such as EGM wants to see the savings law $a[>]=m-c$ as a named relation. A simulator wants the same relation as a forward transition. A solver wants it as part of a backward builder. These are not three different model equations. They are one field equation read in different directions.

So the surface syntax should not be the full functional equation. It should be a typed field declaration from which the functional equation is recovered.

### 1.3 Variables as fields

The remaining question is what kind of object a surface variable is.

A surface variable is a field: a named, typed coordinate at a perch. The word "variable" is therefore used in the economist's pointwise sense. It denotes something that can take a value at a particular information point of the stage.

There are quantity fields,

$$
k[<],m,c,a[>],
$$

and there are value fields,

$$
V,V[>].
$$

The quantity fields take values in state, action, or shock spaces. The value fields take values in the value line $L$. Thus $m$ and $V$ are both fields, but their carriers differ:

$$
m\in\mathbb{R}_{++},\qquad V\in L.
$$

A value function is different. It is not a field. It is a function over a perch state space:

$$
v_\succ:X_\succ \to L,\qquad v_\succ \in \mathsf{V}_\succ.
$$

The continuation value field is the result of evaluating that function:

$$
V[>]=v_\succ(x_\succ).
$$

For the buffer-stock stage, the continuation state is the post-decision asset field $a[>]$, so the same statement is

$$
V[>]=v_\succ(a[>]).
$$

This is the bridge between the field level and the function level. The surface can mention $V[>]$, because $V[>]$ is a field. The semantics keeps the corresponding value function $V_{\mathrm{fn}}[>]$ one level above it.

Fields are typed along three axes.

**By perch**, a field belongs to arrival, decision, or continuation. Arrival fields carry $[<]$, decision fields are unmarked, and continuation fields carry $[>]$. The tag records where the field is known or settled in the ADC stage.

**By role**, a field may be a state, control, shock, or value field. Quantity fields such as $k,m,c,a$ describe economic coordinates. Value fields such as $V[>]$ live on the value line; the derivative of a value, read by the term `D_{a}V[>]`, is no field.

In the stage syntax the derivative of a value is read by a derivative term, `D_{a}V[>]`, the operator applied to the declared value field in the coordinate of its subscript; it is no field and has no role. Three different kinds of object must not be conflated in one identifier. `D_{x}` is an operator, the derivative with respect to the variable in its subscript applied to the function that follows it — `D_{c}(𝑢)` is the function c ↦ ∂𝑢/∂c, and `D_{a}V[>]` is the derivative of the continuation value in savings — and it is never glued into a name. A derivative line, `D_{m}V = 𝑑𝑢(c)`, states what the derivative of the value its builder writes equals. A name such as `𝑑𝑢` is an ordinary function name the modeller chose, whose letters mean nothing to the language; it may be defined through the operator (`𝑑𝑢 := D_{c}(𝑢)`) or in closed form (`𝑑𝑢(c : ℝ₊₊) := c^(-ρ)`).

**By domain**, the `@in` clause fixes the carrier: for example $\mathbb{R}_+$, $\mathbb{R}_{++}$, $(0,m]$, or $L$. Spaces are part of the mathematical model, not numerical configuration.

For the buffer-stock stage, the basic fields are:

| field | declared in | perch | role | domain | meaning |
| --- | --- | --- | --- | --- | --- |
| k [<] | prestate | arrival | state | $\mathbb{R}_+$ | assets on arrival |
| y | exogenous | arrival → decision | shock | $Z_\zeta$ | income draw observed before choice |
| m | states | decision | state | $\mathbb{R}_{++}$ | market resources |
| c | controls | decision | control | $(0,m]\subseteq A$ | consumption |
| a [>] | poststates | continuation | state | $\mathbb{R}_+$ | assets carried forward |
| V [>] | values | continuation | value | $L$ | continuation value at the realised continuation state |

This table is not mere notation. It is what prevents the ambiguous mark $v$ from doing three incompatible jobs.

| level | example | kind of object | carrier |
| --- | --- | --- | --- |
| scalar value field | $V[>]$ | value at the realised continuation state | $L$ |
| value function | $V_{\mathrm{fn}}[>]$, $v_\succ$ | map from continuation states to values | $L^{X_\succ}$ |
| evaluation bridge | $\mathrm{ev}_\succ(V_{\mathrm{fn}}[>],x_\succ)$ | function applied to a state | $L$ |
| builder | $\mathbb{B}$ | operator from continuation value functions to decision value functions | $\mathsf{V}_\succ \to \mathsf{V}_\sim$ |
| stage operator | $\mathbb{T}=\mathbb{I}\circ\mathbb{B}$ | operator across the stage | $\mathsf{V}_\succ \to \mathsf{V}_\prec$ |

Once this distinction is in place, the Bellman expression becomes unambiguous. The line

$$
V=u(c)+\beta V[>]
$$

is a scalar field equation. It lives on $L$. The value function $v$ is the function that collects those scalar values as the decision state varies. The builder $\mathbb{B}$ is the operator that constructs that function from the continuation value function.

### 1.4 What Υ reconstructs

The modeller declares fields, transitions, feasibility, and the aggregator. The meaning map $\Upsilon$ reads those declarations into the functional objects.

Forward, the buffer-stock field equations say:

$$
m=Rk[<]+y,\qquad a[>]=m-c.
$$

Backward, the continuation value function is first evaluated at the continuation state,

$$
V[>]=\mathrm{ev}_\succ(V_{\mathrm{fn}}[>],a[>]),
$$

and the scalar continuation value enters the aggregator,

$$
V=u(c)+\beta V[>].
$$

From these ingredients, the value-side reading of $\Upsilon$ induces the decision builder

$$
(\mathbb{B}v_\succ)(m)=\sup_{0<c\le m}\{u(c)+\beta v_\succ(a)\},\qquad a=m-c,
$$

and the arrival builder

$$
(\mathbb{I}v)(k)=\mathbb{E}_y[v(m)],\qquad m=Rk+y.
$$

These displays are not additional declarations. They are the value-side image of the field diagram. The transition equations are written once; $\Upsilon$ supplies the evaluation bridge, the value-function objects, and the operators.

The same source diagram also has a forward reading. Under a policy, the transition $m=Rk+y$ pushes an arrival distribution to a decision distribution, and the transition $a=m-c$ pushes a decision distribution to a continuation distribution. Thus the simulation law and the Bellman law are not separate model statements. They are the same field equations read in opposite directions.

### 1.5 So what?

The issue is not that economists are sloppy. The compressed notation is useful and standard. The problem is that prose silently performs type conversions that a declarative syntax must perform explicitly.

When an economist writes $v'(x')$, the reader knows that a continuation value function is being evaluated at a next state whose law of motion is specified elsewhere. When an economist writes $v=\max\{\cdots\}$, the reader knows whether the discussion is about a scalar value at a fixed state, a value function over all states, or the operator that maps one value function to another. In a model file, those distinctions cannot be left to context.

Fields solve the problem at the right level. The surface remains first-order and economic: it talks about $k,m,c,a[>],V[>]$. Value functions sit one level above fields. Operators sit one level above value functions. The modeller writes fields and field equations; $\Upsilon$ reconstructs evaluation, value functions, backward builders, and forward push-forwards.

This is why fields are needed. They are not just a naming convention for states and controls. They are the device that lets BE-DDSL preserve economist notation while making the hidden value-variab
