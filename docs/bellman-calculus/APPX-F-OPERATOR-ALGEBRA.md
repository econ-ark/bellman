---
title: "Appendix F — Operator algebra"
short_title: "F. Operator algebra"
status: drafted
tags:
  - bellman-calculus
  - universal-algebra
  - category-theory
  - branching
  - methodization
  - foundations
authors:
  - Akshay Shanker
audience: user
type: theory
topic: [calculus]
---

# Appendix F — Operator algebra

> [!summary]
> Operator composition combines transition, reward, selection and evaluation operations with compatible types. The transition operators have a distribution/function pairing; optimizing operations require additional assumptions. This appendix distinguishes exact algebraic identities from numerical convergence claims.

> [!info]- Relationship with other documents
> **Builds on** — [Operators and builders](./05-Operators%20and%20builders.md) defines the stage operators.
> **Formal account** — [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) proves exact refinement for specified interpretations.
> **Used by** — [Methodization](../Bellman-Sym/04-methodization.md) attaches the methods, settings and calibration whose obligations §6 states; Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) and [Appendix D](../Bellman-Sym/appendices/15-appendix-d-node-tag-and-field-indexing.md) state the reading of the authored equations and their boundaries.
> **See also** — [The stage term](./APPX-C-STAGE-TERM.md) distinguishes mathematical composition from concrete source and storage.

“Operator algebra” here concerns composition of the Bellman calculus's operations, not a functional-analytic algebra of bounded operators. We state which additional structures each interpretation uses.

<a id="f1-signature-objects-and-morphisms"></a>

## 1. Signatures and operator types

A stage has two mathematical many-sorted signatures, together with model data and an interpretation. The **sorts** of its state signature name state spaces, and those of its operator signature name spaces of value functions, spaces of measures and the set of policies. The **operation symbols** of a signature have ranks $\omega:s_1\times\cdots\times s_n\to s$. In a categorical presentation, objects represent these sorts and a **morphism** is a typed operation between them. A signature alone does not supply categorical products or coproducts.

At perch $p$, write $\mathsf V_p$ for a chosen value-function space on state space $\mathsf X_p$, and $\mathsf M_p$ for the finite measures on that state space, of which the probability measures are those of mass one ([Stages and perches](./03-Stages%20and%20perches.md) §1.2). Let $\mathsf L$ be the value line, the declared set of a value field, $\Gamma(x)$ the feasible actions, $\operatorname{Gr}(\Gamma)=\{(x,a):a\in\Gamma(x)\}$, and $\mathsf Q_\Gamma$ a chosen space of measurable choice-value functions on those pairs. The spaces must satisfy the closure and integrability requirements of the displayed operations.

Operators have domain sorts and a codomain sort, which together form the operator's rank. A first-order signature can treat them solely as operation symbols, without declaring an additional carrier of operator-valued data. This is a choice of signature, not a claim that functions can never be elements of a function space. [Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §3, D1, defines the signature and the rank, and §6 there gives the two signatures of a stage.

<a id="f2-the-operator-category"></a>

## 2. Composition and builders

A categorical presentation must declare its generators, their types, the allowed composition operations and equations. For deterministic functions, product domains support pairing and copying of common inputs. A disjoint union represents labeled alternatives; its injections put each alternative into that union. These descriptions do not prove that every Bellman graph supports all the stated operations and identities.

Composition $g\circ f$ requires compatible intermediate types. In the deterministic interpretation, a tensor $f\otimes g$ acts on paired inputs. In a stochastic interpretation a tensor typically specifies independent joint transitions; this is not automatically a categorical product. Builder symbols can be primitive in a coarse signature and derived compositions in a finer one.

For a continuation field $V_\succ$ with decision-measurable state $X$ and feasible action $A$, the trajectory payoff field is

$$
Q=\mathbb E[\mathrm G_\succ(V_\succ,X,A,\eta)\mid\mathcal F_\sim].
$$

Here $\mathcal F_\sim$ is decision information and $\eta$ the post-decision shock. The integrability actually required is that of the displayed local payoff. To compare every feasible action, specify instead the pointwise objective

$$
(B_\succ\mathrm v_\succ)(x,a)
=\int\mathrm G_\succ\bigl(\mathrm v_\succ(\mathrm g_\succ(x,a,\eta)),x,a,\eta\bigr)\,\mu_\eta(d\eta),
$$

with absolute integrability on every required pair. The map $\mathrm g_\succ$ is the decision-to-continuation transition, $\mathrm G_\succ$ the scalar payoff aggregator, and $\mu_\eta$ its conditional shock law, with state/action arguments suppressed only when unnecessary. State representation and conditional-law assumptions relate this function to the trajectory identity almost surely; that identity does not determine counterfactual action values. A map written outside the integral, $B_\succ=\mathrm G^{\mathrm{out}}_\succ(\int\cdots)$, is the two-map form of [Stages and perches](./03-Stages%20and%20perches.md) §2.3a; the display is its case with the outer map the identity.

Let $\Pi_\Gamma$ be feasible measurable policies. On a domain admitting a specified measurable maximizing selection,

$$
\operatorname{argmax}:\mathsf Q_\Gamma\to\Pi_\Gamma,
\qquad
\operatorname{evaluate}:\mathsf Q_\Gamma\times\Pi_\Gamma\to\mathsf V_\sim,
\qquad
\operatorname{evaluate}(Q,\pi)(x)=Q(x,\pi(x)).
$$

Then optimizing evaluation and its derived maximum satisfy

$$
\mathbb T_\succ=\operatorname{evaluate}\circ\langle B_\succ,\operatorname{argmax}\circ B_\succ\rangle,
\qquad
\max=\operatorname{evaluate}\circ\langle\mathrm{id}_{\mathsf Q_\Gamma},\operatorname{argmax}\rangle.
$$

Without attainment the supremum value need not have this selected-policy representation. Direct search and first-order inversion approximate the same optimum only under their feasibility, sufficiency, selection and domain-coverage assumptions; at ties they need not select the same policy. Fixed-policy evaluation is $\mathbb T_{\succ,\pi}v=\operatorname{evaluate}(B_\succ v,\pi)$.

For the arrival transition $\mathrm g_\prec$, pre-decision shock $\zeta$, law $\mu_\zeta$, and local aggregator $\mathrm G_\prec$, arrival evaluation is

$$
\mathbb T_\prec=B_\prec:\mathsf V_\sim\to\mathsf V_\prec,
\qquad
(B_\prec v)(x_\prec)=\int\mathrm G_\prec\bigl(v(\mathrm g_\prec(x_\prec,\zeta)),x_\prec,\zeta\bigr)\,\mu_\zeta(d\zeta).
$$

The optimizing stage operator is $\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ$, and its fixed-policy counterpart is $\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi}$.

A joint implicit system may specify several outputs with a product codomain. It defines a selected function only where existence and a specified measurable selection are established; roots need separate optimality conditions. A nested builder may appear inside another mathematical expression. These facts do not supply either a generic solver theorem or a new source grammar.

<a id="f3-algebras-and-the-meaning-map"></a>

## 3. Interpretation and copying

An algebra supplies carriers and operations of the declared ranks. For ground terms its interpretation extends uniquely to composite terms; free-input terms also require an environment. For a category presented by generators and equations, an interpretation must additionally respect those equations and whichever categorical structures are required. The many-sorted initial-algebra theorem alone does not establish those further properties. [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) gives the precise term-level statement.

| Interpretation | Objects and operations | Conditions |
|---|---|---|
| Value recursion | value functions, local aggregation and selection/evaluation | pointwise domains, integrability and specified selection where required |
| Probability propagation | state distributions and transition kernels under a supplied policy | measurable transitions and conditional laws |

Copying is available in the Markov category of probability kernels: a state can be duplicated by the diagonal map. What fails for a general stochastic transition is preservation of that copying. Duplicating one random draw produces the same outcome twice, while two independent draws need not agree. Deterministic transitions preserve the diagonal. Fritz (2020), §10, Definition 10.1 and Remark 10.2, describes this distinction; it does not prove that every operation in a particular Bellman diagram preserves copying.

DisCoPy supplies typed graph representations and composition operations. Any claimed universal property or equation-preserving interpretation still needs its own mathematical argument. The field and functional graphs represent the same authored equations under the assumptions of Bellman-SYM's Appendix C; they are not independently authored model sources.

<a id="f4-two-readings-transpose-under-the-pairing"></a>

## 4. Transition pairing

Write $P_\prec$ and $P_{\succ,\pi}$ for undiscounted transition expectations and $\mathbb M_\prec,\mathbb M_{\succ,\pi}$ for their forward probability propagation. With $\langle\mu,f\rangle=\int f\,d\mu$,

$$
\langle\mathbb M_\prec\mu,f\rangle=\langle\mu,P_\prec f\rangle,
\qquad
\langle\mathbb M_{\succ,\pi}\mu,f\rangle=\langle\mu,P_{\succ,\pi}f\rangle.
$$

These identities hold for bounded measurable $f$ and extend to absolutely integrable evaluations. They compose with reversed order. Constant-discount expected utility instead gives $\mathbb T_{\succ,\pi}f=\bar r_\pi+\beta P_{\succ,\pi}f$, where $\bar r_\pi$ is expected reward and $0<\beta<1$ is the constant discount factor. An arrival reward or nonlinear aggregator also remains outside the transition pairing. Neither optimization nor a generic reward-bearing backward graph is the transpose of probability propagation.

<a id="f5-branching"></a>

## 5. Branching

A disjoint union $\mathsf X_\succ=\bigsqcup_{j\in J}\mathsf X_{\succ,j}$ can represent labeled continuation alternatives, with $J$ a finite label set. Two economic mechanisms determine how the label is obtained.

- **Agent choice:** the policy chooses an alternative, possibly together with continuous controls. Branch values may be compared by a maximum when an optimum and a measurable maximizing selection exist. For a deterministic branch choice $\pi_J(x)$, routing uses $\mathbf1\{j=\pi_J(x)\}$. The maximizing decision is nonlinear in branch values; propagation under the resulting fixed policy is linear in the source measure.
- **Exogenous selection:** a conditional law $p(j\mid x)$ assigns branch probabilities. The backward expectation is a weighted sum of branch continuation values; the forward distribution is split using the same law. Finite mixtures need no action-feasibility coproduct condition. A persistent label is retained in the state when it affects future laws or payoffs; independence and persistence are model assumptions, not numerical methods.

For exhaustive mutually exclusive alternatives, the component output measures satisfy mass conservation:

$$
\sum_{j\in J}\mu_{\succ,j}(\mathsf X_{\succ,j})=\mu_\sim(\mathsf X_\sim).
$$

An optimizing policy must specify its choice on ties, or supply an admissible randomized rule. Ties can occupy a positive-measure region even when states have an atomless law. A fixed tie-breaking rule makes the selected policy definite but does not by itself guarantee convergence of approximate policies. Exogenous routing is supplied by the model's conditional law; fixed-policy simulation can use an externally supplied policy.

Nonempty feasible sets, attainment and measurable selection are separate assumptions. Empty feasible sets may be assigned value $-\infty$ in an extended-real convention, but have no feasible policy; this is not automatically the interpretation of a categorical initial object. [Branching](./09-branching.md) develops the economic cases.

**Scope.** Stationary distributions and tail behavior of iterated random transitions require invariant-measure and asymptotic analysis. They do not follow from the finite branching representation alone. A stationary distribution is a fixed point of probability propagation; one may introduce an operator that returns such a fixed point under additional assumptions.

<a id="f6-the-graded-realisation-tower"></a>

## 6. Model interpretation and numerical realization

We distinguish the authored equations, a calibrated mathematical operator, a reference numerical approximation, and the package routine that computes it. These are different assignments, not automatically a chain of categorical functors:

$$
\text{equations and model parameters}
\longrightarrow\text{mathematical operator}
\longrightarrow\text{reference approximation}
\longrightarrow\text{package computation}.
$$

Calibration fixes parameter values in the model, at one point of their admissible set ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §4). Method assignment specifies a numerical procedure; settings choose its resolution or tolerances. A **reference approximation** is the numerical map defined by that procedure and its settings, independently of one implementation. A **handler** is the package routine intended to compute it. Equations and stages are authored in `.bl`, and so are the methods, in a methods file that declares the settings they read; the calibration and the values of the settings are YAML, as Bellman-SYM's rules for [methodization](../wiki/methodization.md) describe.

### 6.1 Conditions on realization

- **L1 — Types.** A numerical representation must state its own input and output domains and any maps between grid and exact objects. Equal mathematical ranks do not make different numerical representations identical.
- **L2 — Exact agreement.** A definitionally expanded operator preserves its interpretation under the assignments in [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md). Changing a method is intended to approximate the same calibrated target; initiality does not prove that the method succeeds.
- **L3 — Approximation.** An error or convergence statement must specify the spaces, observables, approximation family and hypotheses. Convergence of individual primitive approximations requires suitable stability or continuity to yield convergence of their compositions. Value convergence need not imply policy convergence at ties. An envelope comparison can discard inferior candidates where its method applies; it is not a universal remedy for discontinuity or missing candidates.
- **L4 — Iteration.** On a nonempty complete metric space, a self-map with a contraction modulus strictly below one has a unique fixed point and convergent exact iterates. Nonexpansiveness alone is insufficient. Convergence of approximate fixed points or iterates needs approximation and stability conditions beyond this exact contraction statement. Distributional convergence requires its own assumptions on the transition kernels and invariant measures.

The mathematical obligations therefore have two parts: relate the reference approximation to the target, and relate the package computation to that reference. Floating-point and implementation error may prevent exact equality even when the reference scheme is well defined. Neither part is proved by attaching a method name.

### 6.2 Endogenous-grid methods and envelopes

Nested endogenous-grid methods and candidate-envelope methods may use different decompositions. Some methods compare outer choices while solving an inner conditional problem; others compare several candidate controls or values at the same state. Their dimensionality, interpolation and selection rules depend on the declared model and the method. A numerical envelope step need not be an authored `upper_env` equation, and a method name alone does not establish a particular rank or convergence theorem. The supported authoring boundaries are specified in Bellman-SYM's Appendix D.

<a id="f7-typing-operators"></a>

## 7. Types and identities

An operator's mathematical type is its rank, its domain and codomain. Its declared name identifies an occurrence or definition in the source; equal denotations need not collapse distinct authored names, and equal names in different contexts need not identify one operation. Locally bound functions retain typed arguments and results. A numerical method record additionally states the representation and settings used by its handler.

For a differentiable scalar function on a product domain, the gradient collects partial derivatives:

$$
\nabla f=\langle\partial_{x_i}f\rangle_i.
$$

The result has one component per coordinate, on the common domain where those derivatives exist. A scalar partial derivative alone does not specify that gradient.

<a id="f8-data-not-operators"></a>

## 8. Model data and induced operations

The transitions $\mathrm g_\prec,\mathrm g_\succ$, local aggregators $\mathrm G_\prec,\mathrm G_\succ$, feasibility correspondence $\Gamma$, and shock laws are model data. A coarse signature may use them only as the data that define its builders' interpretations. A finer signature may expose the functions as typed operations or values in chosen function spaces. The distinction depends on the chosen signature; it is not an absolute division between functions that may and may not be operators.

Transition expectations require measurable transitions and conditional laws. Value evaluation requires integrable local payoffs on its stated domain. Optimization additionally needs an appropriate objective, feasible actions, and selection conditions when a policy is required. A general recursive preference cannot be inferred from one pointwise integrand if it uses additional normalization or a different order of expectation and aggregation. The extension to such preferences remains unfinished. #todo

With identity payoff aggregation and one feasible action, the decision builder reduces to its transition expectation. When the transition kernel is the point mass at the current state, this expectation is the identity. A scalar-multiplication method is not implied by the absence of choice.

<a id="f9-cuts"></a>

## 9. Method assignment boundaries

For a finite hierarchical tree, a cut chooses operation boundaries so each path from the root to a leaf meets exactly one selected box and none is nested within another. Rank and coverage checks establish structural compatibility; exact operation agreement or a numerical error/convergence result requires a separate argument. [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) §5 states the exact case and preserves the open shared-graph question.

<a id="f10-summary"></a>

## 10. The roles of model and method data

| Assignment | Specifies | Obligation |
|---|---|---|
| Equations and domains | mathematical form and allowed arguments | well-defined operations under stated assumptions |
| Calibration | model parameter values | intended economic instance |
| Numerical method | approximation procedure | applicability to the target problem |
| Settings | resolution, tolerances and numerical conventions | stated accuracy or convergence conditions |
| Package handler | computation of the reference approximation | agreement with the reference, including implementation error |

Connectors identify compatible fields between stages or periods. A nonidentity transformation must be authored explicitly; a renaming alone does not define it. [Stage composition](./07-stage-composition.md) and [Periods and trellis](./08-periods-and-trellis.md) discuss these connections. A global categorical presentation remains subject to its declared equations and verified interpretation, rather than following from the table.

## 11. Related documents

- [The stage term](./APPX-C-STAGE-TERM.md) and [Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md).
- [Operator catalogue](./catalogues/operators.md) and [Branching](./09-branching.md).
- Goguen, Thatcher, Wagner and Wright (1977), “Initial algebra semantics and continuous algebras,” §2, pp. 71–75, for term and free-algebra interpretations.
- Fritz (2020), “A synthetic approach to Markov kernels, conditional independence and theorems on sufficient statistics,” §10, for stochastic copying and deterministic maps.

The full categorical presentation beyond these stated structures remains to be verified against its selected target category. #todo
