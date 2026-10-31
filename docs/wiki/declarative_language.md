---
slug: declarative_language
title: declarative language
tags:
- foundations
- semantics
- syntax
- bellman-calculus
description: A language is declarative to the degree that its texts state what an object is, take their meaning from the meanings of their parts with no appeal to an order of execution, and leave the procedure that computes the object to be supplied separately; how Bellman-SYM meets this, the declarative statement and its realization, and where the design looks procedural.
wiki_status: budding
last_reviewed: '2026-09-13'
reviewed_by: "Claude (session of 13 September 2026), at AAS's request; source-checked against the works and the documents its sources name"
updated: '2026-09-13'
needs_resolution: true
flags: []
sources:
- reference: "Backus, J. (1978). Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs. Communications of the ACM 21(8): 613–641. §4, §5.2 and §11.4.4."
  class: literature
  date: '2026-09-13'
- reference: "Bandali, A. (2020). A Comprehensive Study of Declarative Modelling Languages. MA thesis. §§1.1–1.2."
  class: literature
  date: '2026-09-13'
- reference: "Stan Development Team (2025). Stan Reference Manual, version 2.39. Overview, §6.12, chapter 7, §7.3, §7.7 and §7.13."
  class: literature
  date: '2026-09-13'
- reference: "Carpenter, B., et al. (2017). Stan: A Probabilistic Programming Language. Journal of Statistical Software 76(1). §4, §§5.1–5.2 and §7.1."
  class: literature
  date: '2026-09-13'
- reference: "Scott, D. and Strachey, C. (1971). Toward a Mathematical Semantics for Computer Languages. Technical monograph PRG-6, Oxford University Computing Laboratory. p. 1."
  class: literature
  date: '2026-09-13'
- reference: "Schmidt, D. A. (1986). Denotational Semantics: A Methodology for Language Development. Introduction."
  class: literature
  date: '2026-09-13'
- reference: "Winskel, G. (1993). The Formal Semantics of Programming Languages: An Introduction. MIT Press. §5.2."
  class: literature
  date: '2026-09-13'
- reference: "Hutton, G. (2023). Programming Language Semantics: It's Easy as 1,2,3. Journal of Functional Programming 33, e9. §3."
  class: literature
  date: '2026-09-13'
- reference: "Stoy, J. E. (1977). Denotational Semantics: The Scott–Strachey Approach to Programming Language Theory. MIT Press. §1.1."
  class: literature
  date: '2026-09-13'
- reference: "Naish, L. (1996). Higher-order Logic Programming in Prolog. Technical report 96/2, University of Melbourne. §9.3."
  class: literature
  date: '2026-09-13'
- reference: "Pfenning, F. (2021). Lecture Notes on Elaboration. Lecture 11 of course 15-814, Carnegie Mellon University. §1."
  class: literature
  date: '2026-09-13'
- reference: "Oliveira, B. C. d. S. and Löh, A. (2012). Abstract Syntax Graphs for Domain Specific Languages. §§2.1–2.2."
  class: literature
  date: '2026-09-13'
- path: docs/wiki/semantics.md
  class: canonical
  date: '2026-09-13'
- path: docs/Bellman-Sym/04-methodization.md
  class: canonical
  date: '2026-09-13'
audience: user
type: concept
---

# declarative language

A language is **declarative** to the degree that a text written in it states
what an object is, through its sets, probability distributions, equations and choices; takes its
meaning from the meanings of its parts, with no appeal to an order of
execution; and leaves the procedure that computes the object to be supplied
separately. The three clauses are tested against published sources in the
sections below. The phrase "to the degree" is deliberate: the modeling
languages economists use occupy different positions on this scale, and the
Stan and BUGS comparison below shows two of them.

[[sym|Bellman-SYM]] is declarative in this sense. A [[stage|stage file]] states the
domains, information, choices, equations and [[operator#Kernels|shock probability distributions]]
of one stage. Elaboration, the step that reads the stage files, assigns each
file its meaning, the [[semgraph]], which records the [[operator|operators]]
the stage [[semantics|denotes]] and holds no procedure for computing them.
The routines that compute the stage are supplied afterwards, under
[[methodization]], and the methods file
"names computations that the stage file created; it creates none"
([Methodization](../Bellman-Sym/04-methodization.md)).

## The style it is contrasted with

Backus (1978, §4, pp. 615–616) explains the conventional imperative style by
its origin in the machine: "Von Neumann programming languages use variables
to imitate the computer's storage cells; control statements elaborate its
jump and test instructions; and assignment statements imitate its fetching,
storing, and arithmetic." The assignment statement "is the von Neumann
bottleneck of programming languages and keeps us thinking in word-at-a-time
terms in much the same way the computer's bottleneck does." Of the functional
program for the inner product, Backus records (§5.2, p. 617) that "It
operates only on its arguments. There are no hidden states or complex
transition rules" and that "It is static and nonrepetitive, in the sense that
its structure is helpful in understanding it without mentally executing it."

The last property is the one an economist recognizes. The Bellman equation
of the buffer-stock problem, as a paper writes it, is read without being run.
A value-iteration loop that solves it must be traced, and in the project's
interoperability talk the procedural approach is summarized by the
observation that "the loop *is* the model", so that "changing the method or
reusing one piece means editing the loop". A declarative text names the
object; a procedure produces one approximation to it.

Bandali (2020, §1.1, p. 2) characterizes declarative modeling languages as
those that "describe the transitions in a declarative manner using
constraints, rather than through imperative calculations and/or statements"
and "have a formal mathematical and logical foundation". The thesis's
subjects are software specification languages (TLA+, Alloy, Event-B); the
characterization applies equally to a model file whose equations are
constraints on functions.

## What is declared, and what is supplied separately

Stan is the published case closest to the separation of a semgraph from its
numerical realization. The Stan Reference Manual (Stan Development Team 2025,
Overview, p. 1) states that "The language is responsible for defining a log
density function conditioned on data", and that Stan "only requires models to
be defined up to a constant that does not depend on the parameters" (§7.3,
p. 77). Carpenter et al. (2017, §4, p. 16) add that the program's execution
"details are the same whether a Stan program is being used by one of the
built-in samplers or optimizers or being used externally by a user-defined
sampler or optimizer", because other algorithms are implemented "using the
log density and derivative functions supplied by a model" (§7.1, p. 26). A
Stan program declares one mathematical object; the sampler is chosen
separately and can be exchanged. Bandali (2020, §1.2, p. 3) states the same
separation as a rule of method: "tool support and the analysis performance of
those tools are subject to change, and can change much more easily than the
logic and semantics of the language".

In the [[bellman_calculus|Bellman calculus]] the separation is the distinction between
[Υ](upsilon.md), the mathematical interpretation of a stage file, and
[Ρ](rho.md), its numerical realization. The entry [[semantics]] states it: "The
mathematical model specifies domains, equations, shock probability
distributions and feasible choices. A
numerical method supplies a procedure and representations intended to
approximate or compute that model." [[parameters|Parameters]] belong to Υ and
define the mathematical problem; [[settings]] belong to Ρ and configure its
approximation. A method tag such as `!egm` "selects a numerical technique for
these equations; it supplies no missing condition"
([Methodization](../Bellman-Sym/04-methodization.md)).

## Meaning assigned part by part

A text that appeals to no order of execution must take its meaning from the
mathematical objects its parts denote. Scott and Strachey (1971, p. 1) draw
the founding distinction: "The numerals are *expressions* in a certain
familiar language; while the numbers are mathematical *objects* (abstract
objects) which provide the intended *interpretations* of the expressions."
Schmidt (1986, Introduction, p. 1) separates syntax, "the appearance and
structure of its sentences", from semantics, "the assignment of meanings to
the sentences", and from pragmatics, "the usability of the language". The
assignment is **compositional** when, in the words of Winskel (1993, §5.2,
p. 60), "the denotation of a command is constructed from the denotations of
its immediate subcommands", a property Winskel calls "a hallmark of
denotational semantics" and one that fails for the operational semantics of
a while-loop. Hutton (2023, §3, p. 3) states the consequence: "the meaning of
a compound term is defined purely in terms of the meaning of its subterms.
Compositionality aids understanding by ensuring that the semantics is modular
and supports the use of simple equational reasoning techniques." Goguen,
Thatcher, Wagner and Wright (1977, §3.2, p. 76) give the algebraic form: a
grammar "yields an initial many-sorted algebra", "semantics arises from an
algebra of the same type, and 'meaning' is the unique homomorphism" (see
[[initial_algebra|initial algebra]]).

None of these authors discusses declarativeness; the connection is this
entry's reading, and the reader should weigh it as such. Winskel's remark
supplies the connection: a compositional meaning has to be constructed from
the parts of the text, and the one meaning that cannot be so constructed is
the trace of a loop. In this repository Υ is the meaning map and the
[[semgraph]] is its result; the fold of the statements of a [block](../Bellman-Sym/01-stage.md#3-builder-blocks) into the boxes
of a [[builder]] is the construction by structural recursion.

Compositional meaning is what licenses the substitution of equals for equals,
the convention Stoy (1977, §1.1, pp. 5–7) calls "one particularly important
convention in mathematics" and the entry [[referential_transparency|referential transparency]] states
for this project. Backus (1978, §11.4.4, p. 624) attributes the simplicity of
his systems to "the most elementary fixed naming system (naming a function in
a definition) with a simple fixed rule of substituting a function for its
name". A stage file follows the same discipline: a function is defined once
and its name is used in the statements.

## A matter of degree

The Stan Reference Manual shows that "declarative" names a position on a
scale, by contrasting Stan with BUGS: "Unlike programs in BUGS, the
declarations and statements making up a Stan program are executed in the
order in which they are written" (ch. 7, p. 72); "In BUGS, for loops are
declarative, defining plates in directed graphical model notation, which can
be thought of as repeated substructures in the graphical model. Therefore, it
is illegal in BUGS or JAGS to have a for loop that repeatedly reassigns a
value to a variable" (§7.7, pp. 89–90); and "Because Stan is an imperative
language, print statements can be very useful for debugging" (§7.13, p. 99).
Carpenter et al. (2017, §5.2, p. 22) say the same, and add that a sampling
statement "is nothing more than shorthand for incrementing the log density
accumulator" (§5.1, p. 21). The object a Stan program defines, a density, is
declared; the text that defines it is an ordered sequence of statements. BUGS
is declarative in both respects, at the cost recorded below. Dynare's `.mod`
file, which the project's toolkit comparison describes as "a declarative
`.mod` language" with a separate engine, is the other declarative tool most
economists have used.

## The declarative statement and its realization

A stage file may contain both a declaration and the lines of a method that
realize it, and the mark **`!doc`** tells the two apart. The policy block of the
consumption stage `cons.bl` states the choice as a maximization over the
feasible set,

```
c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality, !doc]
```

The mark `!doc` identifies the declarative statement of what the control is, the
mathematical definition of the object; it is neither documentation to be
skipped nor an implementation detail. The other lines of the block, the
inverse Euler inequality with its clause, the endogenous-grid line and the
identification `c = c[>]`, are one realization of that statement by a
method, the endogenous grid method. The file thus reads as the economist
writes the problem, a maximization subject to a feasibility constraint, with
the numerical method's lines recognizable as a realization of it. The card
of the policy [[builder]] prints the `!doc` line under `Declared` and the
other lines as the builder's operations
([The builders graphs](../Bellman-Sym/API/stage/03-build.md) §3;
[A builder](../Bellman-Sym/API/stage/04-builder.md) §2 for the operations): the `!doc` line
forms no operation, and the feasible set its binder declares enters the type
of the policy.

The mark draws the Stan and BUGS contrast inside one file: the
[[statement]] marked `!doc` declares what the control is, and the other
statements of the block record one way to compute it. An `argmax` line
written without `!doc` is itself operative: it forms a row of kind [`Argmax`](../Bellman-Sym/reference/operations.md#argmax),
whose output is the set of maximizing policies, and a numerical method bound
to the row makes the selection
([operations](../Bellman-Sym/reference/operations.md#argmax)).

## What declaring does not settle

Declaring a meaning leaves the behavior of a computation open, in two
directions. First, two texts with one [[semantics|denotation]] can compute differently. The
Stan Reference Manual (§6.12, pp. 70–71), on derivatives taken statement by
statement through an expression of the form x − x, warns: "Rather than the
x − x canceling out, it introduces a 0 into the numerator and denominator of
the chain-rule evaluation. The only way to avoid this kind problem is to be
careful to do the necessary algebraic reductions as part of the model". In
the calculus this is a fact about Ρ, not Υ, and the entry
[[referential_transparency|referential transparency]] makes the same distinction: replacing exact
expectation by a quadrature approximation "requires an error argument rather
than an appeal to equality". Two realizations of one declared stage need not
agree numerically, and nothing in the declaration guarantees that they do.

Second, a language that is declarative throughout forbids constructions that
some computations use; the BUGS prohibition on reassignment quoted above is
the example. Naish (1996, §9.3, pp. 14–15) records a related gap, between
equality as written and equality in the intended interpretation: "there is
nothing to prevent Prolog from attempting to unify these two terms and
failing, even though they are equal in this interpretation."

## The declared artifact and its reading

Declaring requires an artifact that can be read. Pfenning (2021, §1,
p. L11.1) defines elaboration as "a translation mediating between specific
forms of concrete syntax and internal representation in abstract syntax"; in
this project the word names the step that reads the stage files and
constructs the semgraph, and the entry [[syntax]] separates the concrete
syntax a modeler writes from the abstract syntax that records its structure.
Oliveira and Löh (2012, §2.1–2.2, pp. 2–3) name the price of writing a
language directly as code in a host language: "shallow embeddings come at a
price. We are committing to a specific semantics — in this case, evaluation."
The project's review of carrier formats makes the same division, between
languages with their own grammar, "Dynare `.mod`, dyno `.dyno`, Stan,
Modelica, gEcon `.gcn`", and tools embedded in a host language, "JuMP,
Pyomo/CVXPY, SSJ blocks, HARK objects, POMDPs.jl", which offer "free syntax
and tooling, but **no declarative artifact** — nothing for Υ to read." The
toolkit comparison records in the same spirit that QuantEcon "is a LIBRARY of
numerical primitives, not a model-specification language". A stage file kept
as abstract syntax can be read by more than one interpretation, of which the
semgraph is the first.

## Where the design looks procedural

Three features of the design look procedural; the documents state the
following about each.

1. **The order of the bindings.** A [[stage|stage version]] is the [[stage|stage occurrence]]
   as it stands after elaboration or after one of its three bindings, the
   [[calibration]], the methods and the settings. Methodization precedes
   configuration, because the methods name the settings, and calibration
   may come at any point; each binding returns a new stage version and
   changes nothing of the version it is given
   ([The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md) §§1 and 3;
   [[specified_stage|specified stage]]).
2. **Statement order within a block.** The boxes of a builder are emitted in
   the order the terms nest them, and a builder's card lists its operations
   in the order of application, each after every operation whose output it
   reads ([operations](../Bellman-Sym/reference/operations.md) §1).
3. **Method names in outer files.** A methods file names algorithms such as
   the endogenous grid method. It names computations that the stage file
   created and creates none, and a method tag supplies no missing condition
   ([Methodization](../Bellman-Sym/04-methodization.md) §§1 and 2), which is
   the declarative reading this entry gives.

## Related concepts

- [[sym|Bellman-SYM]]: the language whose declarative character this entry defines.
- [[semgraph]] and [[upsilon|Υ — meaning construction]]: the meaning a stage file is assigned, and the map that assigns it.
- [[rho|Ρ — numerical representation]] and [[methodization]]: the numerical realization supplied separately, and the step that names it.
- [[semantics]]: the distinction between interpretation, representation and realization.
- [[syntax]] and [[statement]]: the concrete and abstract forms of what is declared, and the `!doc` mark.
- [[referential_transparency|Referential transparency]] and [[ffp|Functional programming and FFP]]: substitution of equals, and Backus's functional style.
- [[initial_algebra|Initial algebra]]: the algebraic form of compositional meaning.
- [[specified_stage|Specified stage]]: the stage after methods, settings and parameter values are attached.
- [Workflow](../overview/06-workflow.md) §1: the workflow in which the declaration is the first step.

## References

- Backus, J. (1978). Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs. *Communications of the ACM* 21(8): 613–641. §4, §5.2, §11.4.4.
- Bandali, A. (2020). *A Comprehensive Study of Declarative Modelling Languages*. MA thesis. §1.1–1.2.
- Carpenter, B., et al. (2017). Stan: A Probabilistic Programming Language. *Journal of Statistical Software* 76(1). §4, §5.1–5.2, §7.1.
- Goguen, J. A., Thatcher, J. W., Wagner, E. G. and Wright, J. B. (1977). Initial Algebra Semantics and Continuous Algebras. *Journal of the ACM* 24(1): 68–95. §3.2.
- Hutton, G. (2023). Programming Language Semantics: It's Easy as 1,2,3. *Journal of Functional Programming* 33, e9. §3.
- Naish, L. (1996). *Higher-order Logic Programming in Prolog*. Technical report 96/2, University of Melbourne. §9.3.
- Oliveira, B. C. d. S. and Löh, A. (2012). Abstract Syntax Graphs for Domain Specific Languages. §2.1–2.2.
- Pfenning, F. (2021). *Lecture Notes on Elaboration*. Lecture 11 of course 15-814, Carnegie Mellon University. §1.
- Schmidt, D. A. (1986). *Denotational Semantics: A Methodology for Language Development*. Introduction.
- Scott, D. and Strachey, C. (1971). *Toward a Mathematical Semantics for Computer Languages*. Technical monograph PRG-6, Oxford University Computing Laboratory. p. 1.
- Stan Development Team (2025). *Stan Reference Manual*, version 2.39. Overview, §6.12, ch. 7, §7.3, §7.7, §7.13.
- Stoy, J. E. (1977). *Denotational Semantics: The Scott–Strachey Approach to Programming Language Theory*. MIT Press. §1.1.
- Winskel, G. (1993). *The Formal Semantics of Programming Languages: An Introduction*. MIT Press. §5.2.
