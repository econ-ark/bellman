---
title: Introduction to Bellman calculus
short_title: Introduction
status: drafted — Phase 1
tags:
  - bellman-calculus
  - foundations
  - syntax
  - semantics
  - semgraph
  - trellis
  - rdp
authors:
  - Christopher Carroll
  - Akshay Shanker
audience: user
type: theory
topic: [calculus]
---
# Introduction to Bellman calculus

<a id="introduction-to-t-calculus"></a>

> [!summary]
> The Bellman calculus describes a recursive decision problem as a composition of operations with declared inputs and outputs. It separates the economic equations, their mathematical interpretation and the numerical procedures used to approximate their solution.

> [!info]- Relationship with other documents
> **Used by** — [Bellman-SYM](../Bellman-Sym/index.md) introduces the authored source; Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) specifies how source constructs are interpreted.
> **See also** — [Illustrative example](./02-Illustrative%20example.md) develops the buffer-stock model.

The **Bellman calculus** is a mathematical account of staged **recursive dynamic programs**, sequential decision problems specified by states, feasible actions, rewards, transitions and continuation values. The modeler writes stage equations in `.bl`, with supporting YAML for composition and numerical choices. Their [semantics](../wiki/semantics.md) states what those expressions mean. Numerical methods approximate the resulting operations under separate assumptions.

> [!info] Recursive dynamic programs
> A fixed-policy operator $\mathbb T_\pi$ evaluates a specified policy $\pi$; an optimizing Bellman operator $\mathbb T$ takes the supremum over feasible actions. Finite-horizon problems use backward recursion from a terminal value. In a stationary infinite-horizon problem, a value can be characterized by a fixed point under suitable existence and optimality conditions. A type signature alone does not establish those conditions; see [Periods and the trellis](./08-periods-and-trellis.md).

A [stage](./03-Stages%20and%20perches.md) organizes a local decision around its available information, transitions, rewards and controls. Stages compose into [periods](./07-stage-composition.md), and periods compose across time into a [trellis](./08-periods-and-trellis.md), the declared sequence of period occurrences and their inter-period connections. A stage can be examined separately once its continuation input and other required inputs have been supplied. Replacing it in a larger model requires compatible boundaries and may change values elsewhere in that model.

<a id="modularity"></a>

## 1. Modularity

Dynamic programming studies operators on value functions; their composition makes the dependence between local problems explicit.[^dp-tradition] Consider two fixed-policy operators

$$
\mathbb T_{A,\pi}:\mathsf V_0\to\mathsf V_1,
\qquad
\mathbb T_{B,\pi}:\mathsf V_1\to\mathsf V_2.
$$

Here each $\mathsf V_i$ is a specified class of functions on the corresponding state space, and $\pi$ collects the relevant fixed policies. With primitives and other free inputs held fixed, define $v_A=\mathbb T_{A,\pi}v$ and $v_B=\mathbb T_{B,\pi}v_A$. The second operation receives the first operation's result as its continuation input. More generally, $K$ operators with matching types $\mathbb T_{k,\pi}:\mathsf V_{k-1}\to\mathsf V_k$ compose as

$$
\mathbb T_\pi=\mathbb T_{K,\pi}\circ\mathbb T_{K-1,\pi}\circ\cdots\circ\mathbb T_{1,\pi},
\qquad
v_k=\mathbb T_{k,\pi}v_{k-1},\quad k=1,\ldots,K.
$$

This is an order of backward calculation: the rightmost operator acts first. Each output must lie in the next operator's domain, including its regularity and integrability requirements. Once the common parameters and policies are fixed, the displayed chain connects the operators through the value functions $v_k$.

Combining functions through explicit composition follows the functional-programming approach illustrated by Backus.[^backus1978] **Referential transparency** means that an expression can be replaced by another with the same denotation in the same context.[^stoy1977] It does not mean an operator is independent of its arguments or that changing it preserves the result.

[Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) gives the full account of objects, functions, application, combining forms and definitions, then explains represented functions and the connection to typed economic operations. It defines calibration and methodization on those objects and works through the distinction between a stage, its mathematical target and its numerical realization.

For example, changing an interpolation method produces a different numerical approximation to a specified mathematical operation. A compatible input/output representation permits substitution in the calculation, but the approximation error can affect every subsequent value in backward order. Inserting or removing a type-compatible operator likewise defines a composition; it need not preserve the economic problem. Exact replacement requires equality of the relevant operations, as qualified in [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md).

Modularity has four intended uses:

- **Write the economic equations once.** Their definitions can be used in exposition and numerical construction.
- **Compare numerical choices.** Alternative approximations can be attached to a declared operation and assessed for accuracy.
- **Inspect what is computed.** An explicit interpretation connects equations to mathematical objects; implementation correctness still requires verification.
- **Communicate at different levels of detail.** A stage operator can be examined as a whole or through its defined constituent operations.

In an applied model, separately maintained equations and solver routines can disagree about timing, shock placement or feasible choices. Declared domains, information and dependencies help identify such disagreements. This is a reason to record the relation between the model and its computation, not a claim that other mathematical notation or programming styles cannot express it.

The calculus therefore names the operations and the inputs on which they depend. It also distinguishes the **Υ** (Upsilon) interpretation, which assigns mathematical meaning, from the **Ρ** (Rho) numerical construction, which uses selected methods, calibration and settings to obtain executable computations. An interpretation of the equations does not itself certify a numerical procedure's accuracy or convergence.

<a id="overview-of-t-calculus-semantics"></a>

## 2. Mathematical interpretation

A [denotational semantics](../wiki/semantics.md) assigns mathematical meanings to expressions, with a compound expression interpreted from its constituents and the relevant input environment.[^stoy-denotation] The environment assigns values to free inputs, such as a continuation function. In the specified construction, arithmetic in `.bl` equations is parsed; the temporary **abstract syntax tree**, a record of the source's grammatical structure, and the recorded source locations are used during interpretation. Retained stage equations, local definitions and typed diagrams record the interpreted structure. This is the specified construction rather than a statement that every runtime component already implements it.

YAML declarations of [periods](../wiki/period.md) and the [trellis](../wiki/trellis.md) retain the outer model organization, and each occurrence has fresh stage objects. A connector identifies compatible boundary quantities by declared renaming; a nonidentity economic transformation requires an authored equation. No single stored graph of the entire trellis is required by these statements.

Several related calculations may be derived from a model. Under a fixed feasible policy $\pi$, the backward transition expectation $P_\pi$ and forward distribution operator $\mathbb M_\pi$ satisfy the restricted expectation–measure pairing described in [Operators and builders](./05-Operators%20and%20builders.md) §3. A reward-bearing or optimizing Bellman operator $\mathbb T$ does not have that linear-distribution pairing in general. Relations between alternative value representations require their own conditions; see [Semi-conjugacy](./10-semi-conjugacy.md).

A typed diagram records which operations can compose. It does not by itself establish that states are sufficient, integrals finite, maximizing policies measurable, fixed points unique or numerical approximations convergent. Those properties can be stated mathematically and checked under explicit hypotheses. They do not depend on whether source code gives every intermediate operation a name.

<a id="components-of-t-calculus"></a>

## 3. Source and numerical construction

The source and mathematical components have distinct roles:

- **Stage source.** [Bellman-SYM](../wiki/sym.md) defines `.bl` declarations and equations, including local functions and arithmetic expressions.
- **Model composition.** Supporting YAML describes periods, the trellis, connectors, calibration, method assignments and settings. The current forms are documented with the source language.
- **Mathematical interpretation.** The calculus describes fields, functions and composed operators. [The stage term](./APPX-C-STAGE-TERM.md) distinguishes this mathematical structure from concrete syntax.
- **Numerical construction.** [Methodization](../wiki/methodization.md) attaches supported numerical procedures to declared equations. A **handler** is the implementation of such a procedure; its requirements include the mathematical and representation assumptions it needs. Bellman-SYM's Python API documents construction and use from Python.

Parsing, interpretation, method assignment, calibration and numerical execution must agree for a computed result to approximate the declared problem. These notes describe the mathematical relations, while the source documentation states the authoring and API rules. Comparisons with alternative solver formulations remain conditional on the correspondence and approximation results established for them.

The following chapters introduce the buffer-stock Bellman equation, stages and perches, fields and functions, operators and builders, and the composition of stages into periods and trellises. The branching and semi-conjugacy chapters retain their unfinished example outlines.

[Next → Illustrative example](./02-Illustrative%20example.md)

[^dp-tradition]: Stokey, N. L. and Lucas, R. E., with Prescott, E. C. (1989). *Recursive Methods in Economic Dynamics*. Harvard University Press, §4.2, Theorem 4.6, p. 79, and §9.2, Theorem 9.6, p. 263. These are background results under their stated hypotheses, not a claim that every model below satisfies them.

[^backus1978]: Backus, J. (1978). Can programming be liberated from the von Neumann style? A functional style and its algebra of programs. *Communications of the ACM* 21(8), 613–641, §5.2, pp. 616–617.

[^stoy1977]: Stoy, J. E. (1977). *Denotational Semantics: The Scott-Strachey Approach to Programming Language Theory*. MIT Press, §1.1, pp. 5–7.

[^stoy-denotation]: Stoy (1977), §2.2, p. 11.
