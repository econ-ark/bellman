---
title: Matsya
audience: user
type: user-guide
topic: [matsya]
---

# Matsya

> [!summary]
> Matsya is the service of Project Bellman that helps an economist state a dynamic model in [Bellman-SYM](../wiki/sym.md), the project's language for staged Bellman problems. This page says in one paragraph what Matsya does and for whom, and then maps its documentation: four groups of pages, read in order, from what Matsya is, through how it is used and the exact forms looked up while using it, to how it is built.

> [!info]- Relationship with other documents
> **Continued by** — [Matsya in three parts](user-guide/index.md), the user guide's first page, which defines the words that every later page uses.
> **Explained for developers in** — the [Matsya developer guide](dev-guide/index.md), which describes the program, the configuration and the parts of Matsya that training revises.
> **See also** — [For an assistant using Matsya](user-guide/00-for-a-local-model.md), the same map for an assistant that runs Matsya's commands for a user, with the files the client keeps on the user's machine.

## 1 What Matsya does and for whom

Matsya reads a description of a dynamic economic model, written in prose and displayed equations as a paper's model section is written, or the text of a paper, and writes the model's declaration in Bellman-SYM: its stage files and, at the level the user names, the files that join the stages into periods and the periods in time, with the methods and values that Bellman Workbench loads. It restates the model in prose before it writes, checks the files with the program that reads the language, reads the checked files back into prose and compares that prose with its restatement, so that what it returns either says what the source says or reports where it does not; where the source leaves something necessary unsaid, it ends its work with a question instead of supplying an answer. It also answers questions about a model, about its declaration, about the language and about the literature on dynamic programming, and it quotes and cites the passages on which each answer rests. Matsya is for an economist who has a model and wants its declaration, whether the economist types Matsya's commands or has a language model running on the same machine, such as Claude Code, run them; the developer guide is for those who build and train Matsya itself.

## 2 The map of these pages

The pages form one argument in four groups: what Matsya is, how it is used, the exact forms that are looked up while using it, and how it is built. The words that every page uses are defined in the first group, and the later pages link to their definitions.

### 2.1 What Matsya is

- [Matsya](index.md), this page: what Matsya does, for whom, and the map of its pages.
- [Matsya in three parts](user-guide/index.md): matsya-client, matsya-architect and matsya-master; the session, the job, the turn, the version, the label and the target; how a piece of work moves between the parts.
- [The roles and the work of a job](user-guide/01-the-roles-and-the-work-of-a-job.md): the roles of a job and the cycle in which they run, the role of a turn and the elaborator, what each receives and returns, and which command answers which request.

An assistant that runs the commands for a user reads [For an assistant using Matsya](user-guide/00-for-a-local-model.md) first: this map in one page, with the files the client keeps on the user's machine and the commands of a project folder in their order.

### 2.2 Using Matsya

- [Working with Matsya from the command line](user-guide/02-working-from-the-command-line.md): one piece of work followed through the commands, from the installation to the folder of stage files.
- [Working on a project folder](user-guide/03-working-on-a-project-folder.md): the project folder, its session and its files, and a job's files written back into the folder or into a sub-folder of it.
- [Reaching the service by HTTP](user-guide/04-the-service-by-http.md): every request of the service with a `curl` example, for a user without the client and for a program.

### 2.3 Reference

- [The command reference](user-guide/05-the-command-reference.md): every command with its options, printed lines, exit statuses and JSON fields.
- [The Python module and the files the client writes](user-guide/06-the-python-module.md): the module's functions, the model folder and the report.
- [Collections and weights](user-guide/07-collections-and-weights.md): the collections of the retrieval index, the grants that open them and the weights of a search.

### 2.4 How Matsya is built

- [Matsya developer guide](dev-guide/index.md): the program and the configuration that training revises, and the path of one job.
- [The retrieval index](dev-guide/01-the-retrieval-index.md): how the index is built and how a search runs.
- [What Matsya reads](dev-guide/02-what-matsya-reads.md): the message that each call of a language model sends, and the bounds on its language-model tokens.
- [The Matsya handlers](dev-guide/03-matsya-handlers.md): the functions of the configuration that run a job and a turn.
- [Updating Matsya configurations](dev-guide/04-updating-configurations.md): the current selection method and the proposed procedure for publishing, comparing and making a configuration the default.
