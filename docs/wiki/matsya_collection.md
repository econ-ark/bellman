---
slug: matsya_collection
title: Matsya collection
tags:
- matsya
description: "One of the five groups into which the list of indexed sources divides the files of Matsya's retrieval index; a search names the collections it reads, each collection carries one ranking weight, and a private collection is read only under a grant."
wiki_status: budding
last_reviewed: '2026-10-09'
reviewed_by: Claude (Fable), session of 8 October 2026, at AAS's request; checked against the Matsya package's API, collection-access and retrieval-index modules. The names of the roles adopted on 8 October 2026 applied by Claude (Opus), session of 8 October 2026, and the roles that receive the passages of a job's search checked against the configuration Matsya runs under. The records of documents, sections, links and tags that the index keeps within each collection described by Claude (Opus) on 9 October 2026, checked against the extractor and the retrieval index; the searches and requests of a job through the reading controller described by Claude (Opus) on 9 October 2026, checked against the controller and the Matsya handler module; the rule that a role receives every collection the user may read, and the grant file's default, applied by Claude (Opus) on 9 October 2026, checked against the reading controller, the collection-access module and the Matsya handler module
sources:
- path: packages/matsya/matsya_service/collection_access.py
  class: working
  date: '2026-10-08'
- path: packages/matsya/matsya_service/retrieval/index.py
  class: working
  date: '2026-10-09'
- path: packages/matsya/matsya_service/retrieval/extract.py
  class: working
  date: '2026-10-09'
- path: packages/matsya/matsya_service/api.py
  class: working
  date: '2026-10-08'
audience: user
type: concept
---

# Matsya collection
#rag 
> [!summary]
> A **Matsya collection** is one of the five groups into which the list of indexed sources divides the files of Matsya's retrieval index: this project's repository, the private literature, the journal articles gathered for the iteration of the meaning map [Υ](upsilon.md), HARK and Buffer Stock Theory. Matsya is the project's service that writes a model's description in prose, named BellmanStageProse, and its Bellman-SYM declaration from source material, and answers questions with passages retrieved from that index. A search names the collections it reads, each collection carries one ranking weight, and a user reads a private collection only under a grant.

> [!info]- Relationship with other documents
> **Used by** — [[bellman_sym_writer|Prose-to-Bellman-Sym]]: the passages sent to Prose-to-Bellman-Sym, and to the Model-prose-writer, the role that prepares the description from the source material, come from searches and requests that read every collection the user may read (§4).
> **See also** — [[prose_writer|Prose writer]] and [[judge|Judge]]: the two other maps of the Matsya service recorded in this wiki; [[handler|Handler]]: the Rosetta-stone term, which names a solver and has nothing to do with a collection.

## 1 The five collections

| Collection | What it holds | Access |
|---|---|---|
| `repository` | The public pages of this project's repository, and a private part of its development notes | public, with a private part under grant |
| `literature` | The private literature collection: books and papers on dynamic programming, category theory and computation | grant |
| `articles` | The journal articles gathered for the iteration of the meaning map Υ | grant |
| `hark` | The files of HARK, Econ-ARK's Heterogeneous Agents Resources and toolKit, at one fixed version | public |
| `buffer_stock` | The source of the Buffer Stock Theory paper at one fixed version | public |

The list of indexed sources, selected on 7 October 2026 and renewed on 9 October, holds 814 sources: 197 of the repository, 153 of the literature, 230 articles, 209 of HARK and 25 of Buffer Stock Theory. The service's list of indexed sources, and the index itself, record each source's collection under the name `corpus`. A collection is not the same as a checkout: the journal articles are drawn from the literature checkout, 220 of them, and from this repository, the other 10.

The index also records, within each collection, each admitted document with the sections its headings open, the links its authors wrote and the tags it carries. A link resolves only to an admitted document of its own collection read from the same checkout: a destination that names a document of another collection, as when an article text names a note of the literature collection kept in the same checkout, is recorded as unavailable for that reason, and a link is never followed to read the file it names. Two documents are associated through a shared tag only when the tag is on their collection's list of usable topic tags: nineteen tags that name objects of the language for the repository, twenty-two topic tags of its notes for the literature, and none for the articles, HARK and Buffer Stock Theory. The two operations that read these records, `related` and `read`, apply the permissions a search applies, by collection and access class, to every document they would name.

## 2 What a collection does in a search

A request names the collections to read; when the request omits that field, the service reads the repository and Buffer Stock Theory, and an empty list is refused. Every candidate passage is scored by one formula,

$$
\text{score} = 0.7\,\text{lexical} + 0.3\,\max(0, \text{dense}) + 0.3\,[\text{phrase}],
$$

where lexical is the larger of two numbers, the passage's full-text rank score, $1/(1 + r)$ for its rank $r$ among the passages that best match the query's words, and the share of the query's mathematical symbols the passage contains; dense is the cosine similarity between the embeddings of the query and of the passage, the numerical vectors that the embedding model assigns to a text; and the last term is added when the whole query, ignoring case, occurs in the passage's heading or text. The score is then multiplied by the collection's weight. Every collection has weight 1 except Buffer Stock Theory, whose weight is 0.01 in a search that reads more than one collection without naming sources, so that the paper's own passages do not outrank the passages of the other collections; a search of one collection, or of named sources, gives every collection weight 1. A request may multiply the weight of a collection it reads by a factor from 0 to 1000.

## 3 Access by collection

The public parts of the repository, HARK and Buffer Stock Theory are open to every authenticated user. The literature, the articles and the private part of the repository each require a grant, recorded against the user in the service's grant file, which may also give a default list of grants to every user it does not name, while a user it names holds exactly the grants named there. A request that names a collection the user holds no grant for is refused, and a passage is returned only when the user may read its collection and, within the repository, the public or private part it belongs to.

## 4 The searches made in a job

A job is the run that one request to Matsya starts, in which language models write a description and a declaration and the round trip repeats until the two agree. In a job the [[matsya_handler|Matsya handlers]] read the index through the **reading controller**, the part of Matsya's program that stands between them and the index and holds every search and request within fixed permissions. The Matsya handler `writer_references` makes the initial search of preparation, whose query names the concepts the source material names, for the passages sent to the source preparer, the role `SourceMaterial_to_BellmanStageProse`, which prepares the description from the source material, and to the Bellman-SYM writer, the role `BellmanStageProse_to_BellmanSYMDeclaration`; the reconstruction, in which the Bellman-SYM writer writes again from the prose writer's description, makes a search of its own from that description; and the two roles may request further passages within allowances set in the configuration folder Matsya runs under. Every search and every request reads the collections the user may read, the public collections for every user and each private collection only under a grant, whether or not a page is marked for use in a language model's message, with the sources of the paper under study left out, and an initial search returns at most the number of passages that configuration sets, four at present. The passages of the literature and the articles are therefore placed in the messages of a job only for a user granted those collections.
