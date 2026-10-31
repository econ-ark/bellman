---
slug: judge
title: Judge
tags:
- matsya
description: "The map J from two descriptions of a model to a table of agreement on ten items, computed by a language model in the role BellmanStageProse_judge under an instruction text; recorded and never a target, and distinct from ElaboratedSemanticObject_comparator, a program that compares two elaborated semantic objects."
wiki_status: budding
last_reviewed: '2026-10-08'
reviewed_by: Claude (Fable), session of 7 October 2026, at AAS's request; checked against the Matsya package's processor, its judge instruction text and its comparator. The names of the roles, the objects and the files adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026, and checked against the configuration Matsya runs under
sources:
- path: packages/matsya/matsya_service/processor.py
  class: working
  date: '2026-10-07'
- path: packages/meaning-map-training/meaning_map_training/compare.py
  class: working
  date: '2026-10-07'
audience: user
type: concept
---

# Judge

> [!summary]
> The **judge** is the map $J : (M, M') \to$ a table of agreement, from two descriptions of a model in prose and displayed equations, each named BellmanStageProse, to a table that says, on ten items, whether the second states what the first states. A language model computes it in the [[matsya_instructions|role]] `BellmanStageProse_judge`, under that role's instruction text; the map is not that text. Its table is recorded and is never the quantity a training revision is chosen to raise. It is not the comparator `ElaboratedSemanticObject_comparator`, $\cong$, the program that compares the objects the elaboration of two declarations constructs, each named ElaboratedSemanticObject.

> [!info]- Relationship with other documents
> **Builds on** — [[prose_writer|Prose writer]]: the map that writes the description $M'$ that $J$ compares; [[bellman_sym_writer|Bellman-SYM writer]]: the map that wrote the first description $M$ as a declaration.
> **See also** — [[elaborated_stage|Elaborated stage]]: the object the comparator compares when a declaration is one stage file; [Υ](upsilon.md): the meaning map whose computed part, the Bellman-SYM elaborator, stands between the two writers.

## 1 The map

$J$ takes two descriptions: a **write-up** $M$, the description from which the round trip started, prepared from the source material $P$ (SourceMaterial, the paper or the user's text that states the problem); and a **description** $M'$, written by the [[prose_writer|prose writer]] from $E$, the object the elaboration of the declaration written from $M$ constructs. It returns a table over ten items: the state space; timing and information; the shocks; the transitions; the payoff and the aggregator; the constraints; the recursion; the optimality condition; the terminal or boundary condition; the parameters. On each item it counts three things separately: the omissions, statements of $M$ on the item that $M'$ does not make; the additions, statements of $M'$ that $M$ does not make; and the contradictions, statements of $M'$ that contradict $M$. It quotes the passages behind every count. An item agrees when all three counts are zero. The table also says whether $M'$ has the form of a paper's model section and is not a transcription of a file.

## 2 How it is computed

A language model computes the map under the **instruction text** of `BellmanStageProse_judge`, one of the [[matsya_instructions|Matsya instructions]], the file `texts/BellmanStageProse-judge.md` of the configuration folder Matsya runs under. The program sends the message twice, with the two texts in both orders, and an item agrees only when both answers say so, since a language model that compares two texts can favor one for its position (the [[matsya_handler|Matsya handler]] `judge` of the configuration's module `matsya_handler.py`). In the measuring runs $J$ is run on a language model of a third family, never on the prose writer's, by the rule of independence those runs follow. The map is not its instruction text.

## 3 What the table is for

The table of $J$ is an instrument of measurement, recorded beside the trial it concerns and read by a person. It is never the quantity a revision of an instruction text is chosen to raise: a training revision is accepted on the mechanical measures, whether the files elaborate, whether the round trip closes under the comparator, agreement with checked pairs of a description and a stage file, and numerical reproduction, and $J$ checks the prose writer on a sample of trials. Within one job of the Matsya service the agreement of $J$ is one of the two conditions under which the job stops, the other being that the comparator finds the two elaborations $E$ and $E'$ equal. When the service prepares the description $M$ from the source material $P$, a paper's page text or a typed description, it also applies the judge to $P$ and the prepared $M$.

## 4 Comparing texts and comparing elaborated semantic objects

The **comparator**, `ElaboratedSemanticObject_comparator`, $\cong : (E, E') \to$ a comparison profile, is a program and not a role: no language model computes it and it has no instruction text. It compares $E$ and $E'$, the elaborations of the declarations written from $M$ and from $M'$, up to a renaming of their names, on every item the dossier prints: the fields with their perches and sets, the parameters, the functions with their definitions, the laws with their conditioning, the blocks with their typed inputs and outputs, and the kernel of every box. It answers a **profile** that reports, for each kind of item, agreement, difference or an undecided residue, with the renaming it used and the first item on which the two differ, and it calls no language model (`meaning_map_training/compare.py` of the package `packages/meaning-map-training/`, which the Matsya handler `compare` reaches through the job frame, the record a Matsya handler receives). Two elaborations are equal only when every compared stage is equal and the connections between the stages agree; equality is no proof that either states the source material $P$ faithfully. $J$ compares two texts; the comparator compares two elaborated semantic objects. The round trip, $E' \cong E$, is decided by the comparator, and the comparison of $M'$ with $M$ by $J$ is a check on the prose writer. Two texts have no canonical form, which is why the second comparison needs a language model and the first does not.

For a trellis, this program matches stage occurrences and their field names jointly with the selected connections within and between periods. For a recipe it also matches the effective parameter values after the same name correspondence. A value stated for one period is retained even when another period has an unbound `$fill` slot. Matching partial recipes can compare equal as declarations; the missing value remains unbound. A connection or route Bellman cannot certify yields a refusal before the program can report equality.

## Related

[[prose_writer|prose writer]] · [[bellman_sym_writer|Bellman-SYM writer]] · [[elaborated_stage|elaborated stage]] · [Υ](upsilon.md) · [[semantics]]
