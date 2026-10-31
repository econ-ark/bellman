---
slug: reference-guides-matsya
title: Reference guides in Matsya
tags:
- matsya
description: Saved copies of published Bellman documentation, prepared with a Matsya configuration and supplied as selected pages to its language-model roles.
wiki_status: budding
last_reviewed: '2026-10-09'
reviewed_by: Codex; checked against guide construction, configuration loading and page selection. The names of the roles and of the guide builder adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026. The construction with links and tags described by Claude (Opus) on 9 October 2026, checked against the builder, its policy, the parser and the loader; the index's records of links and tags, read by the same parser, described by Claude (Opus) on 9 October 2026, checked against the extractor. The requests by which the source preparer and the Bellman-SYM writer read further saved pages described by Claude (Opus) on 9 October 2026, checked against the reading controller. The guide pages that the optional conversation role receives and requests described by Claude (Opus) on 9 October 2026, checked against the reading controller, the turn runner and the Matsya handler module.
sources:
- path: packages/matsya/matsya_service/document_metadata.py
  class: working
  date: '2026-10-09'
- path: packages/matsya/matsya_service/configuration.py
  class: working
  date: '2026-10-09'
- path: packages/matsya/matsya_service/guide_pages.py
  class: working
  date: '2026-10-09'
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

# Reference guides in Matsya

> [!summary]
> A **reference guide** in Matsya, one of the `matsya_guides` (in prose, the reference guides), is a saved file containing copies of published Bellman documentation pages, joined together: a fixed set of pages and the concept-wiki pages they link to or share a topic tag with. Matsya supplies selected pages to a language model as reference material alongside its role instructions and task material. The guides are produced by an operator running `matsya_guide_builder.py` with Python, when preparing or refreshing a configuration, and a record beside them lists each saved page's sections, links and tags. A language-model call reads the saved guides; rebuilding the retrieval index does not regenerate them.

> [!info]- Relationship with other documents
> **Used by:** [[bellman_sym_writer|Bellman-SYM writer]] and [[prose_writer|Prose writer]] explain the two writing roles that receive guide pages.
> **See also:** [[matsya_collection|Matsya collection]] describes the groups of sources searched for additional passages.
> **Related concepts:** [[matsya_instructions|Matsya instructions]] specify the tasks; [[matsya_handler|Matsya handlers]] select the material and coordinate the calls.

## 1 What each guide contains

A **configuration** is the folder containing Matsya's role instructions, reference guides, settings and the functions that coordinate the roles. Its `guides/` subfolder contains three guide files:

| Guide file | Documentation copied into it | Roles that receive selected pages |
|---|---|---|
| `writer-guide.md` | The overview pages, the main [Bellman-SYM guide](../Bellman-Sym/index.md) pages and the language reference pages; then the concept-wiki pages they link to or share a topic tag with | The source preparer, `SourceMaterial_to_BellmanStageProse`; the Bellman-SYM writer, `BellmanStageProse_to_BellmanSYMDeclaration`; and, in a configuration that enables it, the conversation role, `conversation_answer`, which receives the pages `conversation_pages` names from this guide |
| `reader-guide.md` | The [stage-interface overview](../Bellman-Sym/API/index.md) and the pages describing the stage object; then the concept-wiki pages they link to or share a topic tag with | The prose writer, `ElaboratedSemanticObject_to_BellmanStageProse`, and, in a configuration that enables it, the conversation role, `conversation_answer`, which receives the pages `conversation_pages` names from this guide |
| `calculus-guide.md` | The [Bellman calculus](../bellman-calculus/index.md) pages listed in the site's navigation, in navigation order; then the concept-wiki pages they link to or share a topic tag with | The source preparer, `SourceMaterial_to_BellmanStageProse`, and, in a configuration that enables it, the conversation role, `conversation_answer`, which receives the pages `conversation_pages` names from this guide |

The source preparer, the role `SourceMaterial_to_BellmanStageProse`, writes the economic description of the model, BellmanStageProse, from the source material, the supplied paper or user description. The Bellman-SYM writer then writes declarations from that description. The prose writer describes the elaborated semantic object $E$ ([[elaborated_stage|elaborated stage]]), the object the elaboration of those declarations constructs. Its reference file is named `reader-guide.md`. The conversation role, `conversation_answer`, which a configuration may enable, answers one question asked in a session, a **turn** of conversation mode, quoting the material each claim rests on; it writes no declaration. The setting `conversation_pages` lists the guide pages placed after the role's instruction text in each message of a turn, and each page it lists is taken from the first of `writer-guide.md`, `calculus-guide.md` and `reader-guide.md` that saves it, so that a page saved in two guides is supplied once.

The pages listed first in each row are the guide's **core pages**. A page added because a core page links to it, or shares a topic tag with it, is a **supporting page**; a **topic tag** is a tag, a word written after `#` in a page or listed under `tags:` in its front matter, that names an object of the language, such as `stage` or `perch`. A supporting page is one link or one shared tag away from a core page and never further, and a guide holds at most as many supporting pages as core pages and at most twice the text of its core pages; the pages linked from more core pages are added first. The **construction policy**, the file `guide_policy.json` beside the guide builder, states each guide's core pages, the pages it may add, its topic tags and these limits. It changes only with the program, so that every configuration compared in a training pass holds the same guides.

The guide builder copies page text, removes HTML comments and trailing whitespace, and inserts a marker naming each source page. It never shortens a page and generates no summary. Settings select which saved pages each role receives; the full guide is not automatically included in every call. A supporting page reaches a language model when a setting names it or when the source preparer, the Bellman-SYM writer or, in a configuration that enables the conversation role, that role requests it: in place of an ordinary answer, each of these roles may ask to read a saved page or section of a guide it may read, or to list what the guide records as related to a page it has been shown, its authored links and the pages that share a topic tag with it. The source preparer may read `writer-guide.md` and `calculus-guide.md`, the Bellman-SYM writer `writer-guide.md` alone, and the conversation role all three guides. The program answers such a request from the guide and its manifest alone, places the requested text after the stable beginning of the role's next message, and counts the request against the role's own entry of the setting `reading`: for the source preparer and the Bellman-SYM writer within one run of the preparation or of the writing, and for the conversation role within one turn.

Beside the guides, the page manifest records each saved page's sections, the links written in it and the tags it carries. A link is recorded as available when its target is saved in the same guide, and otherwise with the reason it is not: no such page, no such section, a page the policy does not admit, a web address, a form of link the builder does not resolve, or a page the guide did not save. The builder never follows a link outside the pages its policy admits and never fetches a web address.

## 2 Reference material and instructions

A [[matsya_instructions|role instruction text]], one of the `matsya_instructions`, tells the language model what task to perform, which constraints to follow and what answer to return. A reference guide supplies documentation needed to perform that task. The two are stored separately and included as separate parts of the language model's input by the [[matsya_handler|Matsya handlers]].

For example, the Bellman-SYM writer receives instructions to produce a declaration, guide pages explaining the language's syntax and meaning, and the economic description to represent. The guide may state syntax rules, but it does not specify the particular economic model. Neither the instruction text nor the guide is a set of learned weights, the numerical parameters of the language model.

## 3 When the guides are produced

Preparing or updating a configuration has three relevant steps:

1. Run the operator's guide-construction script, `matsya_guide_builder.py`, with Python and `--output` naming the configuration's `guides/` folder. It reads the documentation pages its policy admits and writes the three guides and their page manifest, which records each saved page's source path, content hashes, sections, links and tags, and the policy the guides were built under. A build that cannot finish, because the policy is incomplete, a core page is missing or a page changed while the builder read it, leaves the earlier guides as they were.
2. Write the configuration's separate `manifest.json`, which records the version and hashes of the other configuration files, including the guides. The guide builder does not write this outer manifest.
3. At the start of a job of architect mode, and of each turn of conversation mode in a configuration that enables the conversation role, Matsya loads the configuration and checks its files against that manifest, and it checks the recorded sections and links against the saved guides. Calls of the source preparer, of the two writers and of the conversation role use the selected pages from those saved guides, and the source preparer, the Bellman-SYM writer and the conversation role may request further saved pages within their allowances.

Editing a documentation page does not change a saved guide, and loading the configuration does not check whether the original documentation has since changed. To make the language model receive the revised page, rebuild the guides and update the configuration manifest. Changing which already-saved pages a role receives changes the settings and configuration manifest; it does not require copying the documentation again.

## 4 Relation to retrieval

A **retrieval index** stores passages in a form that can be searched for a question. The operator builds it separately with `build_retrieval_index.py`, which extracts passages from reviewed sources, computes numerical text representations for similarity search, and checks the resulting index before making it available. It also records the sections, links and tags of the Markdown sources it admits, read by the same parser as the guides' and resolved by the same rules, against the sources of the link's own collection rather than the pages a guide saves. Its retrieved passages can supplement the fixed guide pages.

The guide builder reads documentation pages directly. It does not search the index, build an index or train a language model. Conversely, rebuilding the retrieval index does not refresh the guide files. When a documentation change should be reflected in both, update the saved guides and the index separately.

> [!important]
> Review this entry whenever the Matsya build changes. If the change affects the guides' contents, construction, page selection or use by a language-model role, update this entry in the same change so that it continues to describe the implemented behavior.
