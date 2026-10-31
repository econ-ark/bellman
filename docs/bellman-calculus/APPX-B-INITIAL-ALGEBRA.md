---
title: Appendix B — Initial-algebra semantics
short_title: "Appendix B: Initial algebra"
status: drafted
tags:
  - bellman-calculus
  - appendix
  - initial-algebra
  - universal-algebra
  - semantics
authors:
  - Akshay Shanker
  - Christopher Carroll
audience: user
type: theory
topic: [calculus]
---
# Appendix B — Initial-algebra semantics

> [!summary]
> A signature lists the mathematical operations and their input and output sorts. Once their interpretation and any free inputs are fixed, the term algebra determines the interpretation of composite expressions. Exact refinement preserves the interpretation under stated assignments; numerical approximation requires additional assumptions.

> [!info]- Relationship with other documents
> **Builds on** — [Fields, functions and types](./04-fields,%20functions%20and%20types.md) gives the field and function distinctions.
> **See also** — [Operators and builders](./05-Operators%20and%20builders.md) supplies the stage operators used below.
> **Used by** — Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) specifies binding and substitution.

We use the many-sorted algebra account of Goguen, Thatcher, Wagner, and Wright (1977, hereafter ADJ), §2. The results concern a specified mathematical signature and interpretation; they do not prescribe a stored software representation.

<a id="b1-signature-and-term-algebra"></a>

## 1. Signature and term algebra

A many-sorted **signature** $\Sigma = \langle S, \Omega \rangle$ declares a set $S$ of sorts and a family $\Omega$ of operator symbols, each with an arity (a string of input sorts) and an output sort, and nothing else: no carriers, no functions (ADJ 1977, §2; [signature](../wiki/signature.md)). A **$\Sigma$-algebra** $A$ supplies a carrier set $A_s$ for each sort and an actual operation per symbol of matching rank. A **homomorphism** $h : A \to A'$ is a sort-indexed family of maps commuting with every operation.

The **coarse stage signature** contains perch-indexed value-function sorts $\mathsf V_p$, distribution sorts $\mathsf M_p$, and typed backward and forward builder symbols. The model supplies state spaces, feasible actions, shock laws, transitions and local payoff functions. These data determine the operations under the conditions in [Stages and perches](./03-Stages%20and%20perches.md). A diagram records a finite expression using those operations; the signature also specifies their ranks and cannot be inferred from unlabeled arrows alone.

The ground terms over $\Sigma$ form the **term algebra** $T_\Sigma$, whose operations construct terms. Ground terms contain no free inputs. For a sort-indexed family of free input names $X$, use the **free algebra** $T_\Sigma(X)$. An environment $e_s:X_s\to A_s$ assigns a value to every free input of sort $s$. The environment and the target operations together determine evaluation. A finite acyclic term graph can represent such an expression with shared subterms (§6); this is mathematical notation, not a claim that the parser's abstract syntax tree is retained.

<a id="b2-initiality"></a>

## 2. Initiality

**Definition (ADJ 1977, p. 68).** An algebra $S$ is *initial* in a class $\mathbf{C}$ of algebras iff for every $A \in \mathbf{C}$ there exists a unique homomorphism $h_A : S \to A$.

**Theorem (ADJ 1977, §2, Proposition 2.1, p. 71).** The term algebra $T_\Sigma$ is initial in the category of all $\Sigma$-algebras. Any two initial algebras over $\Sigma$ are canonically isomorphic (ADJ Prop. 1.1), so one may speak of *the* initial algebra.

Thus a fixed target algebra determines a unique interpretation of ground terms. For terms with free inputs, ADJ Propositions 2.3 and 2.6 (pp. 72, 75) give the unique homomorphism $h_{A,e}:T_\Sigma(X)\to A$ extending the environment $e$. Neither the target operations nor the environment is chosen by initiality.

<a id="b3-the-two-target-algebras-and-the-valuation"></a>

## 3. Value and measure interpretations

A target for the combined stage signature must interpret every declared sort and symbol. Its value-function part uses chosen spaces $\mathsf V_p$ on the perch state spaces; its measure part uses $\mathsf M_p$. We may discuss these parts separately by restricting to their respective subsignatures. Reversing arrows alone does not turn a value algebra into a measure algebra of the same rank signature.

Write $\mathcal V$ for the target algebra of the value-operation subsignature and $\Pi_\Gamma$ for its feasible measurable policies. For the value interpretation, let $\operatorname{Gr}(\Gamma)$ be the feasible state–action pairs and $\mathsf Q_\Gamma$ the choice-value functions on those pairs. With an integrable payoff at every required pair, the pointwise objective is

$$
(B_\succ\mathrm v_\succ)(x,a)
=\int \mathrm G_\succ\bigl(\mathrm v_\succ(\mathrm g_\succ(x,a,\eta)),x,a,\eta\bigr)\,\mu_\eta(d\eta).
$$

Here $\mathrm G_\succ$ acts on a scalar value, state, action and shock, and $\mu_\eta$ is the conditional shock law, displayed without state arguments only when those arguments are unnecessary. A trajectory conditional expectation agrees almost surely with this pointwise expression only under the state-representation and conditional-law conditions of [Stages and perches](./03-Stages%20and%20perches.md) §2. It does not define counterfactual action values by itself. A statement may apply a further map outside the integral; the two-map form of [Stages and perches](./03-Stages%20and%20perches.md) §2.3a adds one fine symbol, and the factorization below applies to it unchanged.

On a domain admitting the specified measurable maximizing selection, the optimizing builder is

$$
\mathbb T_\succ
=\operatorname{evaluate}\circ
\langle B_\succ,\operatorname{argmax}\circ B_\succ\rangle.
$$

The fixed-policy builder instead satisfies $\mathbb T_{\succ,\pi}v=\operatorname{evaluate}(B_\succ v,\pi)$. Evaluation means $\operatorname{evaluate}(Q,\pi)(x)=Q(x,\pi(x))$. Arrival evaluation is the policy-free aggregator $\mathbb T_\prec=B_\prec$. Domains must be chosen so all operations are defined and closed under these compositions; initiality supplies no selection or integrability theorem.

The measure interpretation uses transition pushforwards $\mathbb M_\prec$ and $\mathbb M_{\succ,\pi}$. Write $P_\prec$ and $P_{\succ,\pi}$ for the corresponding undiscounted Markov expectations and $\langle\mu,f\rangle=\int f\,d\mu$. For bounded measurable $f$, or when both sides are absolutely integrable, their pairing is

$$
\langle\mathbb M_\prec\mu,f\rangle=\langle\mu,P_\prec f\rangle,
\qquad
\langle\mathbb M_{\succ,\pi}\mu,f\rangle=\langle\mu,P_{\succ,\pi}f\rangle.
$$

These identities extend to composites of the paired transition operators, with order reversed. Reward-bearing evaluation, nonlinear aggregation and optimizing selection are not the probability-transition expectations. No carrier isomorphism is asserted.

The valuation $\Upsilon$ is the unique interpretation homomorphism after these target choices and any free-input environment have been supplied. A term is syntax; its image is its mathematical meaning. Additional equations may restrict admissible targets, but an equation imposed on a quotient syntax also requires its interpretation to satisfy that equation.

<a id="b4-refinement-derived-operations-and-the-factorisation-theorem"></a>

## 4. Exact refinement

Let $\Sigma$ be the coarse signature with optimizing builder $\mathbb T_\succ$ and arrival builder $\mathbb T_\prec$, and $\Sigma'$ a finer signature containing the operations used to define them. A **derived signature morphism** $\delta:\Sigma\to\Sigma'$ assigns each coarse symbol a fine term of the same input and output ranks. The sorts are held fixed here, and the term's formal inputs are explicit. Composition and pairing below abbreviate substitution into ordinary many-sorted terms. For the stage builders, the assignment is

$$
\delta(\mathbb T_\succ)=\operatorname{evaluate}\circ\langle B_\succ,\operatorname{argmax}\circ B_\succ\rangle,
\qquad
\delta(\mathbb T_\prec)=B_\prec.
$$

The fine operations may further express pullback along the law of motion, local aggregation and shock integration, with the domains and selection conditions of §3. A numerical envelope routine is not automatically one of these exact operations.

Any $\Sigma'$-algebra $A'$ becomes a $\Sigma$-algebra $A'|_\delta$ (the **reduct**) by letting each coarse symbol act as its assigned composite. In particular the fine term algebra $T_{\Sigma'}$ becomes a $\Sigma$-algebra $T_{\Sigma'}|_\delta$, and initiality of $T_\Sigma$ yields a unique homomorphism

$$
\mathrm{tr}_\delta : T_\Sigma \to T_{\Sigma'}|_\delta,
$$

the **term translation**: the map that expands every occurrence of every builder symbol into its assigned sub-term. Uniqueness is the coherence claim of [Fields, functions and types](./04-fields,%20functions%20and%20types.md) §5: a homomorphism uses the same interpretation for repeated occurrences of a symbol. Occurrence-specific data must therefore be supplied as inputs or distinguished in the signature.

**Factorization theorem.** For every $\Sigma'$-algebra $A'$, the unique $\Sigma$-homomorphism $T_\Sigma \to A'|_\delta$ factors through the fine term algebra:

$$
h_{A'|_\delta} \;=\; \bigl(h_{A'}\bigr)\big|_\delta \circ\, \mathrm{tr}_\delta .
$$

*Proof.* Both sides are $\Sigma$-homomorphisms from $T_\Sigma$ to $A'|_\delta$; the left by definition, the right as a composite of $\mathrm{tr}_\delta$ with the $\delta$-reduct of the fine valuation $h_{A'} : T_{\Sigma'} \to A'$, reducts preserving homomorphy. Initiality of $T_\Sigma$ admits only one such map. $\square$

For free-input terms, the same argument uses $T_\Sigma(X)$ and the same input assignment on both sides: translation leaves the free generators fixed, and uniqueness is the free-algebra extension property. Applied to an exact target algebra, the theorem says that a coarse term and its assigned fine translation have equal meanings. It does not say that an approximate numerical routine equals either meaning.

**The additional proof obligations.** If a coarse theory imposes equations, the assigned fine terms must satisfy those equations for translation to descend to the quotient theory. Monotonicity and contraction are order and metric properties, not plain signature equations; they require the corresponding structures and separate proofs. A definitionally expanded builder satisfies its defining equality by construction, but an independently proposed formula must be checked against it.

A hierarchical mathematical expression can retain a builder name together with its assigned expansion. Compatible derived translations compose, giving a chain $\Sigma^0\to\Sigma^1\to\cdots\to\Sigma^k$. This describes exact expression refinement. It does not assert that every period or trellis is stored as a nested syntax graph; the source and retained representations are described in [The stage term](./APPX-C-STAGE-TERM.md).

<a id="b5-cuts-methodisation-at-arbitrary-granularity"></a>

## 5. Method assignment at different levels

A **handler** is a numerical routine assigned to a mathematical operation. Methods may evaluate an individual operation, such as an expectation by quadrature, a whole builder, or a composite expression. The following cut specifies the level of assignment in the hierarchy of §4.

**Definition (cut).** Let $t$ be a finite hierarchical tree term over the chain $\Sigma^0 \to \cdots \to \Sigma^k$, its boxes partially ordered by containment. A **cut** $C$ is a set of boxes of $t$ that contains no two boxes nested inside one another and covers $t$: every maximal path from the outermost box to a fine leaf meets exactly one element of $C$.

**Induced signature and method algebra.** For a fixed finite hierarchical tree, a cut $C$ supplies the operation boundaries at which methods are assigned. Use distinct typed symbols when identically named boxes have different data or interpretations. Unfolding the boxes above the cut produces a term $t_C$ over this signature. Once carrier representations, routines and any free inputs are assigned, the term has a unique evaluation. A compatible refinement of the cut has the exact factorization of §4 when its operations agree with the original assignments. This statement does not require a general lattice claim for arbitrary shared graphs. The finest cut contains the fine leaves and the coarsest contains the outermost box. A shared subterm reached from two boxes of the cut must be treated consistently, either by unraveling or by an explicit ownership convention; the representation choice remains open. #ambiguity

**Admissibility (per-box agreement).** An atomic handler $\widehat{b}$ for a box $b \in C$, with interior term $\delta(b)$ over the next-finer signature, is **exactly admissible** iff its denotation equals the valuation of the interior,

$$
\llbracket\, \widehat{b}\, \rrbracket \;=\; h_{\mathcal{V}}\bigl(\delta(b)\bigr),
$$

Here $h_{\mathcal V}(\delta(b))$ denotes the induced operation for every admissible assignment of its formal inputs, with other parameters fixed; the equality is between operations, not just one evaluated output. This equality is the **commuting-square condition**: evaluating the whole box and evaluating its assigned interior give the same result. It is an assumption to verify for an independently supplied handler. If every box satisfies it, composition and the factorization theorem give equality of the resulting exact composite interpretations. Retaining names can make this agreement easier to state, but equalities can also be stated directly between expressions; naming is not a mathematical necessity.

For an approximate handler, state an error or convergence claim in specified spaces and observables, together with the required stability assumptions. Initiality neither chooses that claim nor proves it. A method may use a fixed tolerance, a sequence of grids, or another approximation family; no one numerical criterion is imposed by the term algebra.

<a id="b6-term-graphs-not-trees"></a>

## 6. Shared term representations

Initiality above concerns tree terms. A finite acyclic term graph represents a tree by **unraveling**: duplicate each shared subterm at its uses. With pure deterministic operations, the same environment and the same input arguments, evaluating equal subterms once or repeatedly gives equal values. Under those hypotheses, sharing changes representation without changing denotation. Sharing a sampled outcome and independently resampling are different stochastic operations; the deterministic argument does not equate them. The mathematical graph notation does not identify the retained equation graph with the temporary parsed abstract syntax tree.

<a id="b7-binders"></a>

## 7. Binders

The first-order mathematical signature can treat $\operatorname{argmax}:\mathsf Q_\Gamma\to\Pi_\Gamma$ as an operation on functions, on the restricted domain admitting its stated selection. Its function input then already contains the argument dependence. This is distinct from the concrete source syntax, where expectation, maximization and solve expressions have local variables. Parsing records their binders and bodies; interpretation resolves scope and capture-avoiding substitution. Free inputs still require an environment. Bellman-SYM's Appendix C, §2.5 and rule R2, specifies these requirements. First-order initiality for the mathematical operation signature is not a claim that source binding disappears.

<a id="b8-the-adequacy-obligation"></a>

## 8. The adequacy obligation

Initiality determines the meaning of composite terms once primitive meanings and free inputs have been fixed. It does not certify a backend. For an exact implementation, verify agreement at the chosen operation boundaries and then use the factorization result. For an approximate method, identify the reference numerical operation, its relation to the mathematical operator, and whether the package computes that reference.

Convergence requires method-specific approximation and stability results in declared spaces. Optimization may also require selection assumptions; value convergence alone need not imply policy convergence. The defining identities of [Stages and perches](./03-Stages%20and%20perches.md) provide mathematical checks, but a finite collection of numerical tests is not a proof of those identities on their full domains. No general adequacy or convergence theorem follows from the architecture.

## 9. Related documents

- **Pedagogical companion:** [Fields, functions and types](./04-fields,%20functions%20and%20types.md) §§4–5 (the same claims in prose, on the buffer-stock example)
- **The elaboration:** [Appendix A — Semantics](./APPX-A-SEMANTICS.md) (syntax, interpretation and numerical methods)
- **Wiki:** [initial algebra](../wiki/initial_algebra.md), [signature](../wiki/signature.md), [Lawvere theory](../wiki/lawvere_theory.md), [semgraph](../wiki/semgraph.md), [Υ](../wiki/upsilon.md)

**References.** Goguen, J. A., Thatcher, J. W., Wagner, E. G., and Wright, J. B. (1977). Initial algebra semantics and continuous algebras. *Journal of the ACM* 24(1), 68–95. Burris, S. and Sankappanavar, H. P. (1981). *A Course in Universal Algebra*. Springer. Lawvere, F. W. (1963). Functorial semantics of algebraic theories. *PNAS* 50(5), 869–872. Sannella, D. and Tarlecki, A. (2012). *Foundations of Algebraic Specification and Formal Software Development*. Springer. Plotkin, G. and Pretnar, M. (2013). Handling algebraic effects. *Logical Methods in Computer Science* 9(4). Barendregt, H. P. et al. (1987). Term graph rewriting. *PARLE*, LNCS 259. Plump, D. (1999). Term graph rewriting. In *Handbook of Graph Grammars and Computing by Graph Transformation*, Vol. 2. Drewes, F., Hoffmann, B., and Plump, D. (2002). Hierarchical graph transformation. *JCSS* 64(2), 249–283. Oliveira, B. C. d. S. and Löh, A. (2012). Abstract syntax graphs for domain specific languages. *PEPM '12*. Fiore, M., Plotkin, G., and Turi, D. (1999). Abstract syntax and variable binding. *LICS '99*. Lamiaux, T. and Ahrens, B. (2024). An introduction to initial semantics. arXiv:2401.09366. Aho, A. V. and Johnson, S. C. (1976). Optimal code generation for expression trees. *JACM* 23(3), 488–501. Blindell, G. H. (2016). *Instruction Selection: Principles, Methods, and Applications*. Springer. Morris, F. L. (1973). Advice on structuring compilers and proving them correct. *POPL '73*. Thatcher, J. W., Wagner, E. G., and Wright, J. B. (1981). More on advice on structuring compilers and proving them correct. *Theoretical Computer Science* 15(3), 223–249.
