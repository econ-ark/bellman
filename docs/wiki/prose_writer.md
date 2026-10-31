---
slug: prose_writer
title: Prose writer
tags:
- matsya
description: "The map Υ₁ from the object the elaboration of a declaration constructs to a description of the model it states, written from that object's printed form, the dossier, and from nothing else; computed by a language model in the role ElaboratedSemanticObject_to_BellmanStageProse under an instruction text."
wiki_status: budding
last_reviewed: '2026-10-09'
reviewed_by: Claude (Fable), session of 7 October 2026, at AAS's request; checked against the Matsya package's processor and instruction texts, the dossier module and the pages of the stage object. The names of the roles, the objects and the files adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026, and checked against the configuration Matsya runs under The prose writer's call in a turn of conversation mode described by Claude (Opus) on 9 October 2026, checked against the turn runner and the Matsya handler `conversation_reply`.
sources:
- path: packages/matsya/matsya_service/processor.py
  class: working
  date: '2026-10-07'
- path: packages/bellman/bellman/dossier.py
  class: working
  date: '2026-10-07'
- path: docs/Bellman-Sym/API/index.md
  class: canonical
  date: '2026-10-07'
audience: user
type: concept
---

# Prose writer

> [!summary]
> The **prose writer** is the map $\Upsilon_1 : E \to M'$ from the object the elaboration of a declaration constructs, $E$, named ElaboratedSemanticObject (an [[elaborated_stage|elaborated stage]] for one stage file, an [[trellis#The syntactic and the elaborated trellis|elaborated trellis]] for several), to a description $M'$ of the model $E$ states, in prose and displayed equations, an object of the same kind as the description $M$ the round trip starts from, BellmanStageProse. It writes $M'$ from the printed form of $E$, the dossier, and from nothing else. A language model computes it in the [[matsya_instructions|role]] `ElaboratedSemanticObject_to_BellmanStageProse`, under that role's instruction text; the map is not that text. It reads $E$ and never the stage files: a declaration is elaborated before anything reads it.

> [!info]- Relationship with other documents
> **Builds on** — [[elaborated_stage|Elaborated stage]]: the object described when the declaration is one stage file; [Υ](upsilon.md): the meaning map, of which the Bellman-SYM elaborator followed by the prose writer is a reading in words; [The stage](../Bellman-Sym/API/stage/01-the-stage.md) and the pages after it: the queries the dossier prints.
> **Used by** — [[judge|Judge]]: the role `BellmanStageProse_judge`, which compares $M'$ with the description the writing started from; [[bellman_sym_writer|Bellman-SYM writer]]: the map that writes $M'$ as a declaration again in the round trip.

## 1 The map

The prose writer takes $E$ and returns a **description** $M'$: the model $E$ states, written as the model section of a paper would state it, in prose and displayed equations, in a fixed order: the states, the controls, the shocks and their timing, the laws of motion, the recursion, the condition that determines the policy, and the parameters. Where $E$ states a problem of several stages joined in a [[period]], $M'$ describes the stages in the order of the period and says which quantity one stage passes to the next.

What the prose writer reads is the **dossier**: the numbered printed description of $E$ assembled from the stage object's public queries, the stage's printed view, its definitions, its [[builder|builders]] with their [[signature|signatures]], its primitive [[operator|operators]] with their kernels and typed wires, its initial diagrams and its obligations ([API](../Bellman-Sym/API/index.md)), printed by `dossier_lines` of `bellman.dossier`. The dossier the prose writer receives is anonymous: the stage's own name is replaced by the word `stage`, and every source path is removed. The prose writer receives the dossier and the pages of the stage object's interface, uses no tool, opens no file and keeps no memory between calls.

## 2 How it is computed

A language model computes the map under the prose writer's **instruction text**, one of the [[matsya_instructions|Matsya instructions]]. The text exists in two forms, and the map has two forms with it.

- The **paper form**, whose answer is $M'$: a model section of 300 to 800 words under seven fixed headings, with no dossier line numbers and no spelling of the stage-file language, so that the description states the economics and does not transcribe the file. A program checks the headings, the length and the absence of line numbers and language tokens before anyone reads the description, and where the check fails the prose writer is called once more with its findings.
- The **canonical form**, whose answer is the typed form $B'$: the problem under the headings of the formal pages, with the line of the dossier cited under every equation and an equation that rests on no line marked *inferred*. It is used where a judge compares a reading with a paper.

In the configuration folder Matsya runs under the two texts are `texts/ElaboratedSemanticObject-to-BellmanStageProse.md` and `texts/typed-form-writer.md`, the second being the text of a separate role, `typed_form_writer`, and the [[matsya_handler|Matsya handler]] `prose_write` of its module `matsya_handler.py` prints the dossier, builds the message and checks the form. The map is not its instruction text; training revises the text and leaves the map's domain and codomain as they are.

For a period or trellis, the dossier also states which continuation field of which stage is connected to which arrival field, both within a period and between periods. A recipe dossier states the parameter values supplied in each period and identifies a period whose `$fill` value remains unbound. These are read from the elaborated object rather than inferred from the author's connector spelling.

## 3 Why $E$ and not the file

Nothing reads a declaration $D$ as text. $D$ is elaborated first, and the prose writer describes $E$, because $E$ is the complete typed statement of the problem ([[elaborated_stage|Elaborated stage]] §1): it lists every field with its perch and its set, every shock with its timing, every law, every builder as a typed map between function spaces and the kernel of every box, so that the prose writer describes what is printed and infers nothing. The Bellman-SYM elaborator followed by the prose writer is a reading of the meaning map [Υ](upsilon.md) in words, and it is the simpler of the two directions of the round trip; the [[bellman_sym_writer|Bellman-SYM writer]] must find a file whose meaning is the model, and many files have one meaning.

A description that quoted the file's lines in order would let the Bellman-SYM writer copy them in the reconstruction and would test nothing about meaning. The paper form, the check of the form, the different families of language model behind the two maps, and a paraphrase of $M'$ by a model of a third family in the measuring runs guard against it.

The prose writer serves conversation mode as well, in a configuration that enables the conversation role: when a question asked in a session names a stage file, the program elaborates the file, the prose writer describes its dossier as it does in a cycle, and the conversation role receives the dossier and that description and never the file's text. The conversation role cites the dossier, since the description is a reading of it by a language model.

## Related

[Υ](upsilon.md) · [[elaborated_stage|elaborated stage]] · [[bellman_sym_writer|Bellman-SYM writer]] · [[judge]] · [[semgraph]]
