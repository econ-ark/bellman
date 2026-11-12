---
slug: elaborated_stage
title: elaborated stage
tags:
- semgraph
- ffp
- builder
- bellman-calculus
description: "The object elaboration produces from a stage file, read as a Backus FFP system: definitions as named objects and functions, sorts on the wires, boxes as functional forms applied to kernels, and queries as functions on the object."
wiki_status: budding
last_reviewed: '2026-10-08'
reviewed_by: Claude (session of 14 September 2026), at AAS's request; written against the stage-object amendment and decisions of 14 September. The section on the complete typed statement, Claude (Fable), session of 7 October 2026, at AAS's request; its statement of the object $E$ of Matsya's round trip, Claude (Opus), session of 8 October 2026
updated: '2026-10-08'
needs_resolution: false
flags: []
sources:
- reference: "Backus, J. (1978). Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs. Communications of the ACM 21(8): 613–641. §13, the formal systems for functional programming."
  class: literature
  date: '2026-09-14'
- reference: "Guizzardi, G. and Guarino, N. (2024). Explanation, semantics, and ontology. Data & Knowledge Engineering 153, 102325. §2.1."
  class: literature
  date: '2026-10-07'
- reference: "Pfenning, F. (2021). Lecture Notes on Elaboration. 15-814: Types and Programming Languages, Lecture 11, 5 October 2021. §1, p. L11.1, and §4, p. L11.6."
  class: literature
  date: '2026-10-07'
- reference: "Ferreira, F. and Pientka, B. (2014). Bidirectional Elaboration of Dependently Typed Programs. PPDP '14, Canterbury, 8–10 September 2014, ACM. Abstract and §1."
  class: literature
  date: '2026-10-07'
- path: docs/Bellman-Sym/API/stage/01-the-stage.md
  class: canonical
  date: '2026-10-07'
- path: packages/bellman/bellman/factory/elaboration.py
  class: working
  date: '2026-10-07'
audience: user
type: concept
---

# elaborated stage

> [!summary]
> The **elaborated stage** is the object the elaborator constructs from a stage file: the complete typed statement of the problem the file states, with every field, shock, law, builder and kernel explicit. It is read as a Backus FFP system, with definitions as the named objects and functions, sorts on the wires, boxes as functional forms applied to kernels, and queries as functions on the object. It is the object that is inspected, compared and described; the file is not read as text once it elaborates.

> [!info]- Relationship with other documents
> **Builds on** — [Υ](upsilon.md) §1: the elaborator, the computed step of the meaning map, which constructs this object; [The stage](../Bellman-Sym/API/stage/01-the-stage.md): how a stage is made and the seven attributes it holds.
> **Used by** — [[prose_writer|Prose writer]]: the description of this object in words from its printed form; [[judge|Judge]] §4: the comparator, which compares two of these objects up to a renaming.
> **See also** — [[semgraph]]: the four graphs the object holds; [[ffp|Functional programming and FFP]]: the reading of §2.

The **elaborated stage** (`ElaboratedStage`) is the object `elaborate_stage` and `elaborate_trellis` produce from a `.bl` [[stage|stage file]]. It is a [[stage|stage occurrence]], that file elaborated at one position of a [[period]] with its own three bindings; each binding adds to it in place and returns it, and a text derived from the file is elaborated as its own stage occurrence with its origin recorded. It has seven attributes and nothing else: `name`, `metadata`, `definitions`, `initial`, `_builders`, `bindings` and `provenance` ([The stage](../Bellman-Sym/API/stage/01-the-stage.md) §2). `initial` holds the two [[semgraph|initial diagrams]], `stage.initial.backward` and `stage.initial.forward`, the backward and the forward [blocks](../Bellman-Sym/01-stage.md#3-builder-blocks) on field wires, two separate graphs; `_builders` holds the two [[semgraph|builders graphs]] under a private name, and a reader reaches them through `stage.builder`: `stage.builder.bwd`, the [[backward_builder|backward builders]] and the policy builder on function wires, and `stage.builder.fwd`, the [[forward_builder|forward builders]] on measure wires, with each [[builder]] read by the ordered pair of [[perch|perches]] it joins, `stage.builder["cntn", "dcsn"]`, the policy builder by its own key, `policy`, or from the perch its edge leaves, `stage.dcsn.builder.bwd` ([The builders graphs](../Bellman-Sym/API/stage/03-build.md) §§1 and 2). The word for the seven is *attributes*, never fields, since a [[field]] is a named quantity of a stage, at a [[perch]] unless it is a shock. Everything the seven determine is a query, never a stored member.

## 1 The complete typed statement of the problem

The elaborated stage is the complete typed statement of the problem the stage file states, and the problem is of higher order, because its entities include functions on the sets of the [[perch|perches]] and the operators between them: every [[field]] with its perch and its set, every shock with its timing, every law, every [[builder]] as a typed map between function spaces, and the kernel of every box. In the round trip of Matsya, the project's service that writes a model's declaration from source material, the object that the elaboration of a declaration constructs is written $E$ and named ElaboratedSemanticObject: it is an elaborated stage when the declaration is one stage file, and an [[trellis#The syntactic and the elaborated trellis|elaborated trellis]], whose stages are elaborated stages, when the declaration states several. Neither the stage file nor a description of the model in prose is such a statement. The stage file declares a field's set and perch where it introduces the field and leaves the rest to be resolved: the sort of a wire, the domain of a function, the coordinates a function is written in, the perch at which a shock is available, and the operators a block's lines fold to are derived by the construction and written nowhere in the file. A prose description states them informally. The **elaborator**, the computed step of [Υ](upsilon.md), makes every such commitment explicit in the elaborated stage or refuses the file, so that two agents cannot agree falsely on an ambiguous text: an ambiguity in the file is a refusal, and an agreement on the elaborated stage is an agreement on the complete statement.

In the sense of formal ontology, the elaborated stage is the problem's ontology made explicit. Guizzardi and Guarino (2024, §2.1) define an ontology as "a specific theory about the kinds of entity and their ties that are assumed to exist by a given description of reality"; the kinds of entity here are the sets, the fields, the functions, the laws, the operators and the parameters, and their ties are the typed wires and the kernels that join them. The word *elaboration* is used in the sense of programming-language theory, the translation of a surface syntax into a fully explicit, typed core form, which fails where the source does not type-check (Pfenning 2021, §§1 and 4; Ferreira and Pientka 2014, abstract), as [Υ](upsilon.md) §1 states.

The elaborated stage is therefore the object that is compared and described. Two stage files that differ in spelling or in the order of their blocks elaborate to one stage; a comparison of two declarations is made on their elaborated stages, up to a renaming of names ([[judge|Judge]] §4), and a description of a declaration in words, by the [[prose_writer|prose writer]], is written from the elaborated stage's printed form and from nothing else. Nothing reads a stage file as text once it can be elaborated.

## 2 The object read as an FFP system

Backus's FFP has three tiers: objects, functions on objects, and functional forms that make functions from functions ([[ffp|Functional programming and FFP]], [[functional_form|functional form]]). The elaborated stage is an implementation of that reading.

- **Definitions are the named objects and functions.** `definitions` is an ordered mapping from an identity to a `Definition` record: a set, a [[operator#Kernels|shock probability distribution]] (record kind `distribution`), a [[parameters|parameter]], a function, a function alias, a correspondence, a `g`, a `G` or a `line`, the record of one [[statement]]. A set or a parameter is an object; a named function, a [[operator#Kernels|law of motion]] `g`, a [[aggregation|value aggregator]] `G` and a shock probability distribution are functions: the kernels, that is, in Backus's sense, the parameters of the operators' forms, which are no economic parameters. Each is held once and referred to by identity.
- **Wires carry objects, and each wire has a sort.** A wire carries one object, a field in an initial diagram, a function in the backward builders graph, a measure in the forward builders graph, and its [[sort]] is one `Sort` record: identity, kind, perch, role, domain, and for a function wire its coordinates. A DisCoPy type is a tuple of sorts, one per wire.
- **Boxes are functional forms applied to kernels.** A [[operator|primitive operator]] is a `Box` whose `data` is a tuple of references to definitions: a [[builder|pullback]] refers to a `g` record, an aggregation to a `G` record, an expectation to a `distribution` record. What the box denotes is the image of its kernel under a fixed functional form, precomposition for a pullback, postcomposition for an aggregation, integration for an expectation ([[operator]]); a builder is a `Bubble` composing them ([[builder]]).
- **Queries are functions on the object.** `denote()`, `view()` on the stage, `fields()`, `kernel()`, `compile_kernel()`, `par`, `settings` and the rest read the graphs and the table and store nothing. Each piece answers for itself: `stage.dcsn.builder.bwd["pullback"].denote()` answers the record whose printed form is that box's card, and `stage.definitions.denote("<identity>")` answers it for that definition; `stage.view()` is the stage's own [sheet](../Bellman-Sym/API/stage/01-the-stage.md#3-the-printed-view). A query that takes a box as an argument is implementation and is bound as no method. The graphs themselves are `stage.builder.bwd.graph` and `stage.initial.backward.graph`, and `stage.builder.bwd.primitives` and `stage.builder.bwd.sub_builders` are the same graph at the two [[semgraph|grains]] a reader is offered ([API](../Bellman-Sym/API/index.md) §1).

## 3 What an identity string is

An identity has the form `<stage>:<kind>:<name>`: `cons:set:Xm`, `cons:parameter:ρ`, `cons:g:dcsn_to_cntn`, `cons:correspondence:Γ`. The middle segment is the *kind of the record*, the package's word for what the record defines: `set` says the record defines a set, `g` that it defines a law of motion. It is no sort: the package's `Sort` records stand on wires, and the record kinds are a different list from the kinds of [Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §3. `Sort.domain` retains the set term or `None`, including named-set references, inline intervals and intersections; `Sort.coordinates` contains coordinate identities. A record's kind is not its domain. A field wire's identity is `<stage>:<perch>:<field>` (`cons:arvl:m`), with the word `shck` in the place of the perch for a shock, which belongs to no perch; a function wire's names the perch and the value it carries (`cons:function:cntn:V`), and a box's name is its block and operation kind, with the statement's address in place of the block for an operator belonging to one statement (`cntn_to_dcsn:Pullback`, `policy.InvEuler:Aggregation`).

## 4 How the queries read them

`stage.fields()` walks the blocks of the two initial diagrams in file order and reads the sorts on their input and output wires; it keeps no table. `stage.par` reads the `parameter` records of `definitions` and joins each with the value the [[calibration]] bound, `unbound` where there is none, and then the `derived_parameter` records, each with its declared set where it declares one and its definition evaluated at the calibration ([[parameters]]); `stage.par["ρ"]` answers one parameter's record, whose `value` is the number. A box's `kernel().origins` resolves its `data` through `definitions`. A box's own `denote()` builds its record from three sources: the `line` records for the statements the kernel denotes, the `g`, `G` or `distribution` record for the object those statements denote, and the box's `dom` and `cod` for the typed wires; the card is that record printed and is not made by taking a printed line apart. Its `compile_kernel()` executes the kernel's Python text, `kernel().python`, and answers one plain function of the kernel's arguments and then the parameters it reads, on a symbolic version as well, `kernel().parameter_values` giving the calibration's values in that order; a row whose rule has no explicit side, such as the identification of a policy block, is refused under the rule `kernel-target`. Nothing a query returns is stored as a member of the object: an answer is kept on the stage it was asked of, and a binding discards the kept answers it changes.

## Related

[[semgraph]] · [[builder]] · [[operator]] · [[field]] · [Υ](upsilon.md) · [[prose_writer|prose writer]] · [[judge]] · [[ffp|Functional programming and FFP]] · [[functional_form|Functional form]]
