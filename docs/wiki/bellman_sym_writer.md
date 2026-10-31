---
slug: bellman_sym_writer
title: Bellman-SYM writer
tags:
- matsya
description: "The map Υ₀ from a description of an economic model to its Bellman-SYM declaration, computed by a language model in the role BellmanStageProse_to_BellmanSYMDeclaration under an instruction text; the files it returns are elaborated, never read as text."
wiki_status: budding
last_reviewed: '2026-10-09'
reviewed_by: Claude (Fable), session of 7 October 2026, at AAS's request; checked against the Matsya package's processor and instruction texts and the pages of the stage object. The names of the roles, the objects and the files adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026, and checked against the configuration Matsya runs under. The parts of the writer's message and its requests for further documentation brought to the build of 9 October 2026 by Claude (Opus), checked against the Matsya handler module, the reading controller and the writer's instruction text
sources:
- path: packages/matsya/matsya_service/processor.py
  class: working
  date: '2026-10-07'
- path: packages/matsya/matsya_service/meaning.py
  class: working
  date: '2026-10-07'
- path: packages/matsya/matsya_service/retrieval/context.py
  class: working
  date: '2026-10-09'
- path: docs/Bellman-Sym/API/factory/stage-factory.md
  class: canonical
  date: '2026-10-07'
- path: docs/Bellman-Sym/API/stage/01-the-stage.md
  class: canonical
  date: '2026-10-07'
audience: user
type: concept
---

# Bellman-SYM writer

> [!summary]
> The **Bellman-SYM writer** is the map $\Upsilon_0 : M \to D$ from the description $M$ of an economic model in prose and displayed equations, named BellmanStageProse, to the model's declaration $D$ in Bellman-SYM, named BellmanSYMDeclaration: the stage files with the period and trellis files. A language model computes it in the [[matsya_instructions|role]] `BellmanStageProse_to_BellmanSYMDeclaration`, under that role's instruction text; the map is not that text. The files it returns are never read as text: they are elaborated, and what is then compared or described is the object their elaboration constructs, $E$, named ElaboratedSemanticObject.

> [!info]- Relationship with other documents
> **Builds on** — [Υ](upsilon.md): the meaning map from a stage file to the model it states, against which the Bellman-SYM writer works, and its computed part, the Bellman-SYM elaborator; [[sym|Bellman-SYM]]: the language the declaration is written in.
> **Used by** — [[prose_writer|Prose writer]]: the map back from $E$ to a description; [[judge|Judge]]: the role `BellmanStageProse_judge`, which compares the description the round trip returns with the one the Bellman-SYM writer started from.
> **See also** — [The factory API](../Bellman-Sym/API/factory/index.md): the functions that elaborate the files the Bellman-SYM writer returns.

## 1 The map

The writer takes a **description** $M$: a statement of a dynamic program in prose and displayed equations, as the model section of a paper states it, with its states and their sets, its controls and their feasible sets, each shock with its distribution and its timing, the laws of motion, the recursion, the condition that determines the policy, and the parameters. One description may state several stages and the connections between them. It returns a **declaration** $D$: one [[stage|stage file]] for each stage of the model and, for a model of several stages, the [[period]] file and the [[trellis]] file that join them, that is, the [[trellis|syntactic trellis]] and its stages. Beside the files it returns a note of what $M$ left open and what the files therefore omit.

$M$ is prepared from the **source material** $P$, named SourceMaterial: the paper, if there is one, together with the user's prompts and the exchange with Matsya, the project's service that writes a model's description and declaration from such material. A description the user types is a $P$ too, and it is prepared into $M$ by the same path as a paper, by the source preparer, the role `SourceMaterial_to_BellmanStageProse`, the map $P \to M$. Before it writes $M$, the source preparer may request further pages of the calculus guide or the language guide, two of Matsya's [[reference-guides-matsya|reference guides]], or passages of the retrieval index, the searchable store of passages from the documents of Matsya's [[matsya_collection|collections]], in the way §2 describes for the writer.

## 2 How it is computed

A language model computes the map. Each call sends it one message whose first part is the writer's **instruction text**, one of the [[matsya_instructions|Matsya instructions]], and whose remaining parts are the pages of the language guide; the passages retrieved from the published documentation, if any; the addresses of further documentation the writer may request and, after its first request, the material its requests added; and $M$. In place of its files the writer may answer a call with one **request**, a JSON object of the form its instruction text explains, to read a saved page of the language guide or a passage of the retrieval index, to list what is recorded as related to a page or passage it has been shown, or to search the index again. The program answers the request within the allowances the configuration's settings set under `reading` and places the result in the writer's next message, after the instruction text and the guide pages, which stay the same from call to call; the writer then writes its files or makes a further request. Such documentation explains how the language states a model and supplies no fact about the model that $M$ describes. The instruction text says what the map does: write from $M$ alone, name no known model, fill no gap, copy the spellings of the guide, and write under each block the sentence of $M$ it comes from. In the configuration folder Matsya runs under the text is `texts/BellmanStageProse-to-BellmanSYMDeclaration.md`, and the [[matsya_handler|Matsya handler]] `write` of its module `matsya_handler.py` builds the message and reads the answer.

The map is not its instruction text. Training the writer revises the text and the program around the call; it changes neither the map's domain nor its codomain. A revision is kept when the measures taken on a set of descriptions held out from the revision do not fall.

## 3 What follows the writer

Nothing reads $D$ as text. The Bellman-SYM elaborator `BellmanSYMDeclaration_to_ElaboratedSemanticObject`, $S : D \to E$, a program and not a role, elaborates every file the writer returns, with `elaborate_text` of `bellman.factory.elaboration` for one stage and `elaborate_trellis` for a model of several stages, and so obtains $E$, the [[elaborated_stage|elaborated stage]] of one stage file or the [[trellis#The syntactic and the elaborated trellis|elaborated trellis]] of several, or a refusal that names the rule, the line and the form expected ([Stage functions](../Bellman-Sym/API/factory/stage-factory.md) §2). On a refusal the writer is called again with its own refused files and the refusal, up to three calls in all under the present configuration, besides the calls it answers with a request, which have an allowance of their own; a file that still does not elaborate ends the attempt, and no later step sees it.

The writer works against the meaning map [Υ](upsilon.md): it must find a file whose meaning is the model, and many files have one meaning. Two calls on one $M$ give two files that need not agree in spelling or in the order of their blocks. They are therefore compared through their elaborations, by the comparator `ElaboratedSemanticObject_comparator`, $\cong$, a program that decides whether two elaborations agree up to a renaming of their names ([[judge|Judge]] §4), and never as text. The round trip $M \to D \to E \to M' \to D' \to E'$ tests whether the writer and the [[prose_writer|prose writer]] are consistent with each other; $D'$ is written from $M'$ by the same role, the Bellman-SYM writer, and $E'$ is its elaboration. Whether $D$ is faithful to $M$ is tested outside it: by pairs of a description and a stage file that a person or a judge has checked, by a numerical representation [Ρ](rho.md) that reproduces a result of the paper or fails to, and by the [[judge]], the role `BellmanStageProse_judge`.

For a model of several stages, elaboration selects the actual pair of stage fields at each connection. The dossier prints those resolved pairs. A connection or route that Bellman cannot certify, including one with incompatible continuation values, is returned to the writer for correction. A recipe also carries the parameter values supplied in each period, and those values enter the deterministic comparison.

## Related

[Υ](upsilon.md) · [[elaborated_stage|elaborated stage]] · [[prose_writer|prose writer]] · [[judge]] · [[sym|Bellman-SYM]] · [[trellis]]
