---
slug: matsya_handler
title: Matsya handler
tags:
- matsya
description: The Python functions in a Matsya configuration that coordinate language-model calls, select material, process answers and run a job of architect mode or, when the configuration enables the conversation role, a turn of conversation mode.
wiki_status: budding
last_reviewed: '2026-10-09'
reviewed_by: Codex; checked against the configuration's function requirements, the frame and the job processor. The names of the roles, the module and the job frame adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026. The reading controller and the requests of the source preparer and the Bellman-SYM writer described by Claude (Opus) on 9 October 2026, checked against the controller, the processor and the Matsya handler module. The optional fourteenth Matsya handler, `conversation_reply`, which runs a turn of conversation mode, described by Claude (Opus) on 9 October 2026, checked against the configuration loader, the turn runner and the Matsya handler module. The rule that a role receives the passages of every collection the user may read applied by Claude (Opus) on 9 October 2026, checked against the reading controller, the processor and the Matsya handler `writer_references`.
sources:
- path: packages/matsya/matsya_service/configuration.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/frame.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/processor.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/meaning.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/retrieval/context.py
  class: working
  date: '2026-10-09'
- path: packages/matsya/matsya_service/conversation.py
  class: working
  date: '2026-10-09'
audience: user
type: concept
topic: [matsya]
---

# Matsya handler

> [!summary]
> A **Matsya handler** is a Python function in a configuration's `matsya_handler.py` file. These functions coordinate the work of a job of architect mode (a request to `POST /v1/model-iterations`): they select input material, call language-model roles, process their answers and arrange the elaboration of the declarations and the comparison of the elaborated semantic objects ([[elaborated_stage|elaborated stage]]). A configuration that enables the optional conversation role holds a fourteenth Matsya handler, `conversation_reply`, which answers one question asked in a session, a **turn** of conversation mode (a request to `POST /v1/sessions/{session_id}/turns`). Python executes the Matsya handler; a language model is called only where that function requests one.

> [!info]- Relationship with other documents
> **Uses:** [[matsya_instructions|Matsya instructions]] specify what the language model should do, while [[reference-guides-matsya|Reference guides in Matsya]] supply documentation.
> **See also:** [[handler|Handler]] describes the separate use of this word for an implementation of a numerical operation in a solver.

## 1 Where Matsya handlers belong

A **configuration** is the folder containing Matsya's instructions, guides, settings and coordinating functions. Its `matsya_handler.py` file contains thirteen required functions and, in a configuration that enables the conversation role, a fourteenth, `conversation_reply`, which only such a configuration must hold. These are executable code, stored separately from the instruction texts supplied to language models.

The **frame** is the Matsya package that loads the configuration, defines the required function names and parameters, and provides access to language-model calls, the Bellman-SYM elaborator, the comparator and job records. For each job it builds one record holding these facilities and the job's data, the **job frame** (the class `Frame`), which most Matsya handlers receive as their `frame` argument. Small functions such as `select_pages` and `normalize_source` receive their inputs directly.

A Matsya handler coordinates a task such as writing a declaration. A [[handler|numerical handler]] implements a selected numerical operation, such as an endogenous-grid step. Keeping the qualifier “Matsya” identifies which meaning is intended.

## 2 The required functions

| Function | Work performed |
|---|---|
| `cycle` | Coordinate preparation, declaration writing, prose writing, judging and reconstruction; repeat or stop according to the job's results and limits. |
| `prepare` | Obtain the economic description of the model, BellmanStageProse, from the source preparer, the role `SourceMaterial_to_BellmanStageProse`, and check its form and, through the role `BellmanStageProse_judge`, its agreement with the source material. The source preparer may first request further documentation within its allowances. |
| `write` | Ask the Bellman-SYM writer, the role `BellmanStageProse_to_BellmanSYMDeclaration`, for declarations, pass them to the Bellman-SYM elaborator, and request corrections after a refusal within the configured limit. The Bellman-SYM writer may first request further documentation within its allowances. |
| `verify_distribution` | Ask the role `distribution_check` whether the description supplies a usable law for a named random variable. |
| `prose_write` | Ask the prose writer, the role `ElaboratedSemanticObject_to_BellmanStageProse`, for a description of the elaborated semantic object $E$ and check the answer's required form. |
| `judge` | Ask the role `BellmanStageProse_judge` to compare descriptions and process its reports of agreement or disagreement. |
| `compare` | Call `ElaboratedSemanticObject_comparator`, the program that compares two elaborated semantic objects. This comparison does not call a language model. |
| `citations` | Check whether quotations attached to declaration blocks occur in the supplied description. |
| `unresolved_note` | Treat the Bellman-SYM writer's note as unresolved unless it says `none`, with an optional final period and ignoring case. |
| `call` | Assemble the role's instructions and input material, invoke the configured language-model caller and record the call's outcome. |
| `writer_references` | Make the initial search of a preparation or a reconstruction through the reading controller: a query built from the concepts the source material or the description names, and at most the configured number of passages of the collections the user may read. |
| `select_pages` | Select named pages from a saved reference guide in guide order. |
| `normalize_source` | Convert the request's source material into the source record used by the job. |
| `conversation_reply` | Optional, for a configuration that enables the conversation role: answer one question asked in a session. It searches the index once from the question, assembles the role's message from the guide pages, the passages found, the session's entries before the question, the outputs of the job this conversation discusses, the session's selected job or else its latest current job, and, for a stage file the question names, its dossier with the prose writer's description of it; it calls the conversation role, has the reading controller answer the role's requests, checks each answer's citations against the material supplied in the turn and sends a failed answer back for repair within the configured rounds. |

The functions have different responsibilities. In particular, `write` includes a language-model call, whereas `compare` invokes a deterministic comparison program. The thirteen required functions therefore do not represent thirteen language-model roles or thirteen calls per job.

The `compare` handler receives the resolved connections selected from the same elaborated stages as the dossier. A recipe's effective period parameter values are compared with the connections. An uncertified connection or route is returned to `write` for correction before the comparison can report equality.

## 3 A declaration-writing example

Suppose the supplied description states a household's consumption problem.

1. The `write` Matsya handler selects the language-guide pages and combines them with the description, any permitted retrieved guidance and any correction feedback.
2. It calls the `call` Matsya handler for the role `BellmanStageProse_to_BellmanSYMDeclaration`, the Bellman-SYM writer. That function puts the writer's instruction text before the selected material and requests an answer from the configured language model.
3. The language model may answer with one request in place of the files, for instance to read the definition of a perch from a guide page that the stage page links to. The `write` Matsya handler recognizes the request before it parses any files, has the reading controller answer it, and calls the role again with the page placed after the stable beginning of the message. The requests count against an allowance of their own and not against the rounds of correction.
4. The language model returns declaration text. The `write` Matsya handler parses the returned files and calls the Bellman-SYM elaborator through the job frame.
5. If the elaborator refuses a declaration, the Matsya handler can return the refusal to the language model for correction within the configured round limit. Its result includes the files, the elaborated semantic object, where the elaboration succeeded, and the round records.

This separates three contributions: instructions tell the language model what to produce, reference pages explain the language, and Matsya handler code determines how the call and its answer are processed. The Matsya handler does not become the language model that writes the declaration.

## 4 How Matsya handlers are loaded and changed

At the start of a job, Matsya checks the configuration's files against its **manifest**, the record of their content hashes, and checks each [[reference-guides-matsya|reference guide]] against its **page manifest**, the record of the pages the guide holds. A page manifest of the form that the guide builder now writes, `matsya-guides/3`, also records each saved page's sections, links and tags, and Matsya checks those records against the saved guide. It then imports `matsya_handler.py`, requires each named Matsya handler to be callable and checks its **parameter list**, the ordered names of the arguments the function accepts, against the package's requirements. It requires `conversation_reply` only of a configuration that names the conversation role among its roles, which must then also hold the role's instruction text and settings; a configuration that holds some of these parts without the others is refused. These checks establish file identity and compatible parameter names; they do not prove that a Matsya handler implements the intended economic task correctly.

The processor builds the job frame from the loaded texts, guides, settings and program functions, then calls `cycle` with it to coordinate the job. The job frame's `index` is the **reading controller**, the part of the program through which the Matsya handlers read the retrieval index and the guides' records: a Matsya handler binds it to the role of each run of `prepare` or `write`, and it then answers that role's requests for further documentation, refuses an address the role was not shown, a guide the role may not read or a passage of a collection the user may not read, holds the role within the allowances of the settings, and keeps a record of each request's outcome, which the processor writes into the job's record. A Matsya handler may narrow its searches and cannot widen them. Matsya handlers use the job frame's functions for the elaboration and for the comparison of elaborated semantic objects. In the current configuration, language-model calls go through the `call` Matsya handler. These calls reach the language model's provider through the frame. The frame counts the **language-model tokens** of each message before sending it (a token is the unit of text, a word or part of a word, in which the provider counts and prices a message) and refuses a call that would carry the tokens charged to its role, or to the whole job, past a **ceiling**, a limit the settings place on those tokens over all of a job's calls. After such a refusal the processor ends the job `not_converged` with the reason `token_ceiling_reached`, whatever `cycle` returns or raises, so a Matsya handler that catches the refusal can neither continue the job nor report another outcome.

A turn of conversation mode is run by the program's **turn runner**, which builds a job frame for the turn as the processor builds one for a job and calls `conversation_reply` once. The turn runner binds the reading controller to the snapshot of the index the turn reads, to the collections the person asking may read, to the allowances of the conversation role and to three reference guides, so that the Matsya handler places in a message only passages of the collections the person may read, the rule a job's reading controller applies as well. It counts the turn's tokens against a ceiling of its own, and it checks the Matsya handler's answer: every citation must name material supplied to the role in the turn and quote it, and a call refused at a ceiling ends the turn `incomplete` with the reason `token_ceiling_reached`, whatever the Matsya handler returns. The Matsya handler chooses the reading and assembles the messages; the turn runner alone sets the permissions, the snapshot and the limits and accepts or refuses the answer.

A revised Matsya handler is a code change to the configuration and requires an updated manifest and evaluation of its behavior. Changing a required function's name or parameter list also requires a corresponding change to the package's interface. Rebuilding guides or the retrieval index does not rewrite `matsya_handler.py`, and replacing the language model used by a role does not itself rewrite its Matsya handler.

> [!important]
> Review this entry whenever the Matsya build changes. If the change affects the required Matsya handlers, their parameters, their responsibilities or their relation to the frame, update this entry in the same change.
