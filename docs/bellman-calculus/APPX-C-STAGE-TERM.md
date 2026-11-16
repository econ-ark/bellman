---
title: Appendix C — The stage term
short_title: "Appendix C: Stage term"
status: drafted
tags:
  - bellman-calculus
  - appendix
  - stage
  - universal-algebra
  - initial-algebra
authors:
  - Akshay Shanker
  - Christopher Carroll
audience: user
type: theory
topic: [calculus]
---
# Appendix C — The stage term

> [!summary]
> This appendix records the typed builder symbols and their stage compositions. The mathematical term specifies which operations compose; the model supplies their interpretation. The term notation is distinct from the concrete stage grammar and its temporary parsed syntax tree.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md) supplies the stage data and operator definitions.
> **Formal account** — [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) states the conditional interpretation and refinement results.
> **Used by** — [Stages](../Bellman-Sym/01-stage.md) describes `.bl` authoring; [Period Syntax](../Bellman-Sym/06-period.md) and [The factory API](../Bellman-Sym/API/factory/index.md) describe the application representation of periods and trellises.

<a id="c1-the-signature-named"></a>

## 1. The stage signature

A **many-sorted signature** $\Sigma=(S,\Omega)$ has sort names $S$ and operator symbols $\Omega$, each symbol with a **rank**, its ordered input sorts and output sort, written $\mathrm{op}:s_1\times\cdots\times s_n\to s$. An **algebra** assigns a carrier set to each sort and a function of its rank to each symbol. No order between sorts is declared: one sort lies below another when its condition implies the other's in every stage and at every assignment of values to the parameters, so that the carriers are included. An inclusion of carriers in one interpretation does not establish that order. [Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §3 gives these definitions in D1 and D2, and the derived order in D5.

The stage tuple of [Stages and perches](./03-Stages%20and%20perches.md) §1 supplies mathematical data for the interpretation: state spaces, feasible actions, shock laws, transitions and local payoff maps. It is not the list of sort names. Writing $\mathsf L$ for the value line, the declared set of a value field, $\operatorname{Gr}(\Gamma)$ for feasible state–action pairs, and $\mathsf Z_\eta,\mathsf Z_\zeta$ for post- and pre-decision shock spaces, the pointwise aggregators have types

$$
\mathrm G_\succ:\mathsf L\times\operatorname{Gr}(\Gamma)\times\mathsf Z_\eta\to\mathsf L,
\qquad
\mathrm G_\prec:\mathsf L\times\mathsf X_\prec\times\mathsf Z_\zeta\to\mathsf L.
$$

Here $\mathsf X_\prec$ is the arrival state space. These maps act on scalar continuation values. Pullback along the law of motion and shock integration define the function-valued aggregators $B_\succ,B_\prec$ on stated domains. Policy evaluation at a supplied policy and optimization are then distinct operations. Neither a type declaration nor a numerical routine proves integrability, existence of a maximizing policy, or convergence.

<a id="c2-the-skeleton-is-the-generating-data"></a>

## 2. Perch indices and builder symbols

The three perch indices and two directed edges form the stage's indexing path:

$$
\prec\;\xrightarrow{e_\prec}\;\sim\;\xrightarrow{e_\succ}\;\succ.
$$

The indices stand for arrival, decision and continuation information sets. State spaces are assigned to these indices; the indices are not themselves state spaces. The path generates a free category of paths once identities and composition are included. This is a different construction from a many-sorted term algebra, to which §4 relates it, and neither says the bare graph is initial in an unspecified category.

The coarse stage signature uses representing-function tuple and distribution sort names:

$$
S=\{\mathtt B_p:p\in\{\prec,\sim,\succ\}\}
\cup\{\mathtt M_p:p\in\{\prec,\sim,\succ\}\}.
$$

The carriers are $\mathsf B_p$, the tuples of representing functions, and $\mathsf M_p$, the finite measures on the corresponding state spaces. Probability measures have mass one. Operations require their stated closure and integrability conditions. Each tuple coordinate has its own domain. A random value field has a representing function only under the state-generated measurability conditions in [Fields, functions and types](./04-fields,%20functions%20and%20types.md); it is not that function itself.

| Operator symbol | Rank | Interpretation |
|---|---|---|
| $\mathbb T_{\succ,\pi}$ | $\mathtt B_\succ\to\mathtt B_\sim$ | decision evaluation under a fixed feasible measurable policy $\pi$ |
| $\mathbb T_\succ$ | $\mathtt B_\succ\to\mathtt B_\sim$ | optimizing decision evaluation on its stated domain |
| $\mathbb T_\prec$ | $\mathtt B_\sim\to\mathtt B_\prec$ | arrival evaluation |
| $\mathbb M_\prec$ | $\mathtt M_\prec\to\mathtt M_\sim$ | arrival transition pushforward |
| $\mathbb M_{\succ,\pi}$ | $\mathtt M_\sim\to\mathtt M_\succ$ | decision transition pushforward under $\pi$ |

The policy-indexed rows have one symbol for each supplied policy. A finer signature can instead include a policy sort and policy as an explicit argument. The chosen convention indexes decision builders by their policy. A value-type field sent backward is instead a coordinate of the builder’s input and output tuple. In this coarse signature the pairing and function application are not additional symbols. They remain available when defining its target interpretation; mathematical properties can be stated without adding an authored name for every expression.

[Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §6 calls this signature, together with a sort of policies and the policy builder from $\mathtt B_\succ$ to that sort, the **operator signature** of a stage. It obtains the operator signature from the stage's state signature, whose sorts are the state sorts of the perches and whose symbols are the transitions, each a law of motion with its shock law. The symbols $\mathtt B_p$ and $\mathtt M_p$ name sorts; $\mathsf B_p$ and $\mathsf M_p$ are their carriers. The builder symbols of the table other than the optimizing $\mathbb T_\succ$ name the images that two models, one in representing-function tuples and one in measures, give the declaration graph of the stage. The vertices of that graph are the states of the three perches, and its edges are typed by the transitions.

<a id="c3-why-state-spaces-are-not-sorts"></a>

## 3. Coarse and fine signatures

State, action and shock sorts are omitted from this coarse signature because none of its displayed ranks uses them. That is a choice of abstraction, not a ban on unused sorts in a signature or a claim that no sort names a state space: the state sorts of the state signature (§2) name the state spaces of the perches. The underlying state, action and shock spaces enter the target operations. A finer signature can include them when it displays pullback along the law of motion, scalar aggregation, or selection explicitly; [Operators and builders](./05-Operators%20and%20builders.md) gives the ranks of these operations.

The mathematical signature is not a replacement for the concrete stage grammar. Stage equations are authored in `.bl`; arithmetic, binders and equation bodies are parsed. In the specified construction, interpretation maps the temporary abstract syntax tree into equations, definitions and typed graph connections. Scope and substitution use the declared context. The syntax tree and its source spans are not retained as the stage's mathematical representation. Distinct stage occurrences have fresh objects and bindings even if their common module text is parsed once. In a modular model, their declaration supplies the same calibration sources and family of operators; varying fields are arguments of that family. Methods and settings may differ.

Periods, trellises, connectors, specification recipes, the calibration and the values of the settings remain YAML. The methods are written in a methods file, a `.bl` file that also declares the settings they read. A mathematical composition expression does not assert a new stored whole-trellis graph. Bellman-SYM's factory API and its Period Syntax page describe the application representation.

<a id="c4-two-terms-one-path"></a>

## 4. Stage compositions

For a supplied policy, the backward and forward compositions are

$$
\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi},
\qquad
\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec.
$$

The optimizing stage operator is $\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ$. These are distinguished compositions, not the only possible terms over the signature. Their common perch indexing does not make the reward-bearing backward operators probability-transposes. If $P_\prec$ and $P_{\succ,\pi}$ denote undiscounted transition expectations, their composite $P_\pi=P_\prec\circ P_{\succ,\pi}$ satisfies

$$
\langle\mathbb M_\pi\mu,f\rangle=\langle\mu,P_\pi f\rangle,
\qquad
\langle\mu,f\rangle:=\int f\,d\mu,
$$

for bounded measurable $f$, or whenever the evaluations are absolutely integrable. [Stages and perches](./03-Stages%20and%20perches.md) defines these expectations. Rewards, discounting and selection require their own interpretation.

A ground term over total operations has a unique evaluation once those operations are fixed. For the partial operators here, evaluation is defined only where every required application is defined. A term with free continuation or distribution inputs also requires their assignment; [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) §2 states the free-algebra result.

[Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §6 supplies the relation between this term account and the indexing path for symbols with one input. The path, with the state of each perch at its index, is the declaration graph of the stage. The model in measures, which that section calls the model of laws, is a functor out of the free category of that graph. The model in representing-function tuples and partial maps, which it calls the backward model, is a functor out of the opposite of that category, in which every arrow is reversed.

The sorts of §2 and the builder symbols of its table other than the optimizing $\mathbb T_\succ$ name the carriers and the images that these two models give the graph. For total operations with several inputs, the finite-product term interpretation of Appendix D §6 supplies pairing. Ordinary products form the tuples; this makes no assertion of categorical products for arbitrary partial maps.
