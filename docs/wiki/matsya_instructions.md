---
slug: matsya_instructions
title: Matsya instructions
tags:
- matsya
description: The saved instruction texts that tell Matsya's language-model roles what task to perform, what evidence to use and what answer to return.
wiki_status: budding
last_reviewed: '2026-10-09'
reviewed_by: Codex; checked against configuration loading, role definitions and message construction. The names of the roles and of the instruction files adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026. The request form that the texts of the source preparer and the Bellman-SYM writer explain described by Claude (Opus) on 9 October 2026, checked against the reading controller and the two texts. The optional instruction text of the conversation role described by Claude (Opus) on 9 October 2026, checked against the configuration loader, the turn runner and the text.
sources:
- path: packages/matsya/matsya_service/configuration.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/roles.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/frame.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/README.md
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/retrieval/context.py
  class: working
  date: '2026-10-09'
- path: packages/meaning-map-training/meaning_map_training/round_trip.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/conversation.py
  class: working
  date: '2026-10-09'
audience: user
type: concept
topic: [matsya]
---

# Matsya instructions

> [!summary]
> **Matsya instructions** (`matsya_instructions`; in prose, the instruction texts) are the saved texts that tell each language-model role what task to perform, which evidence it may use and what answer it must return. They are stored in the configuration's `texts/` folder and supplied when the language model is called. Earlier project documents call them skills. Editing them changes the instructions supplied to a language model; it does not change the language model's learned numerical parameters.

> [!info]- Relationship with other documents
> **Used by:** [[matsya_handler|Matsya handlers]] assemble the language model's input and process its answer.
> **See also:** [[reference-guides-matsya|Reference guides in Matsya]] supply documentation alongside the instructions; [[bellman_sym_writer|Bellman-SYM writer]] describes one role governed by them.

## 1 What an instruction text specifies

A **role** is a task assigned to a language model, such as writing a Bellman-SYM declaration or comparing two descriptions. Its instruction text specifies the permitted evidence, the task's rules and the required answer format. For example, the Bellman-SYM writer's instructions require it to base a declaration on the supplied economic description of the model, BellmanStageProse, and identify the statements supporting its equations.

The instructions form one part of the **prompt**, the text supplied to a language model for a call. Other parts may include reference-guide pages, retrieved passages, the particular economic description and feedback on an earlier answer; the messages of the source preparer and the Bellman-SYM writer also list the addresses of further documentation they may request, with their remaining allowances, and the material their earlier requests added. The economic description states the model to represent; the instructions state what to do with that description.

A **configuration** is the folder containing these texts, the reference guides, settings and the Python functions that coordinate the roles. The settings select the language model for each role separately from its instruction text. A role, its instructions and the language model executing it are therefore three distinct objects. The settings also limit how many **language-model tokens** one call and a whole job may use; a token is the unit of text, a word or part of a word, in which the language model's provider counts and prices a message.

The Bellman-SYM writer's instructions allow joined fields to retain the same local name. They ask for a short mapping such as `{a: b}` whether the names agree or differ, and a stage-qualified endpoint only when the bare field name is ambiguous. A parameter's supplied value is shared across the stages of its period.

## 2 The seven instruction texts

The configuration contains one file for each role. A file's name is the role's key with each underscore written as a hyphen: for example, `BellmanStageProse-to-BellmanSYMDeclaration.md` supplies the role `BellmanStageProse_to_BellmanSYMDeclaration`, the Bellman-SYM writer.

| File under `texts/` | Task specified |
|---|---|
| `SourceMaterial-to-BellmanStageProse.md` | Extract an economic description from the supplied source material, or identify the information needed to do so (the source preparer); it also explains the request by which the role may first read further documentation. |
| `BellmanStageProse-to-BellmanSYMDeclaration.md` | Write a Bellman-SYM declaration from an economic description (the Bellman-SYM writer); it also explains the request by which the role may first read further documentation. |
| `ElaboratedSemanticObject-to-BellmanStageProse.md` | Write an economic description from the dossier, the printed form of the [[elaborated_stage|elaborated semantic object]] (the prose writer). |
| `BellmanStageProse-judge.md` | Compare descriptions and report omissions, additions and contradictions in the economic model (the judge). |
| `distribution-check.md` | Check whether the selected description specifies a usable probability law for a named random variable. |
| `paraphrase.md` | Rewrite a description in different words while preserving its mathematical statements, notation and assumptions. |
| `typed-form-writer.md` | Express the printed stage object in a prescribed form listing states, controls, shocks, equations and conditions, with supporting line references. |
| `conversation-answer.md`, optional | Answer a question asked in a session from the material supplied for it, quoting the material each claim rests on, keeping apart what a source says, a comparison and the role's own deductions, and asking the user when a choice is open (the conversation role, `conversation_answer`); it explains the requests by which the role may read further documentation and the outputs of the session's jobs, and states that the role writes no declaration. |

A job of architect mode (a request to `POST /v1/model-iterations`) uses the first five roles as needed. The program that measures a training pass (`round_trip.py`, kept with the training's records outside this repository) calls the role `paraphrase` to compare reconstructions under changed wording. The typed-form text is required in the configuration, but the current job and that program both write the description from the dossier with `ElaboratedSemanticObject-to-BellmanStageProse.md`. Seven required instruction files therefore do not imply seven roles running in every job. The eighth text, `conversation-answer.md`, belongs to the optional conversation role: a configuration holds it only when its settings name that role, and then a question asked in a session (a request to `POST /v1/sessions/{session_id}/turns`) is answered by the role under it, with the prose writer called on the dossier of a stage file the question names.

## 3 How a call uses the instructions

1. At the start of a job, Matsya loads the configuration and checks its files against the **manifest**, a record of the configuration's version and content hashes identifying the saved files.
2. The Matsya handler for the task selects the relevant material, such as an economic description, guide pages and feedback.
3. The `call` Matsya handler places the role's instruction text first, followed by those material parts. It uses the saved role text unless an explicit instruction text is supplied for that call.
4. Before the message is sent, Matsya asks the language model's provider to count its language-model tokens. It refuses a message that would not fit the language model's **context window**, the most text the model can hold in one call, its answer included, and a call that would carry the tokens used by the role, or by the whole job, past a limit of the settings; either refusal ends the job without that call's answer.
5. The selected language model produces an answer. The Matsya handler then parses the answer and applies the checks required for that task. The source preparer and the Bellman-SYM writer may instead answer with one **request**, a JSON object of a fixed form that their instructions explain, asking to read a guide page or an index passage, or to list what is recorded as related to one; the Matsya handler recognizes a request before it parses the answer, the program answers it within the role's allowances, and the role is called again with the result. Documentation obtained in this way explains how the language states a model; it supplies no fact about the user's model.

For the Bellman-SYM writer, the instructions require declaration files, the guide pages explain how to write them, and the task material states the particular economic model. The Matsya handler sends this input and passes the returned files to the Bellman-SYM elaborator. The language model produces the files; the elaboration is performed by the program.

## 4 When instructions change

Instruction texts are authored or revised as part of a configuration. After a text changes, the configuration's manifest must be updated before that configuration is used. The job record identifies the configuration and its file hashes, so the instruction version used in a run can be recovered from the corresponding saved configuration.

The guide builder, the script `matsya_guide_builder.py`, copies documentation pages into the reference guides under its construction policy and records their sections, links and tags. It does not generate these instruction texts. Rebuilding the retrieval index likewise leaves them unchanged. Revising instructions, changing the coordinating Matsya handlers and training a language model's numerical parameters are separate changes that can be evaluated separately.

> [!important]
> Review this entry whenever the Matsya build changes. If the change affects the roles, instruction files, loading or use of instructions in a call, update this entry in the same change.
