---
title: Overview
tags:
  - bellman-sym
  - user-facing
status: Draft
related:
  - "[[01-stage]]"
  - "[[01-the-stage]]"
  - "[[06-period]]"
  - "[[07-trellis]]"
date: 2026-09-19
audience: user
type: overview
---

# Overview

> [!summary]
> The overview pages give an informal account of the written Bellman-SYM language and its semantics. We start by reviewing Project Bellman's core concepts and terminology, including the stage, perches and fields, and the trellis, a diagram of periods joined by connections. We then turn to how a stage file (a `.bl` file) is written, and to the project workflow. We also describe what elaboration builds from a stage file, how parameter values, methods and settings are attached to a stage, and the functions that represent the fields a stage returns.

> [!info]- Relationship with other documents
> **Used by** — [Stages](../Bellman-Sym/01-stage.md): the line-by-line reading of a stage file like the one used here; [Periods](../Bellman-Sym/06-period.md) and [Trellises](../Bellman-Sym/07-trellis.md): several stages and several periods.
> **See also** — [API](../Bellman-Sym/API/index.md): the constructed object in detail; [Factory API](../Bellman-Sym/API/factory/index.md): the loading and binding calls in full.
> **Formal account** — [Bellman calculus](../bellman-calculus/index.md): the mathematics the graphs represent; [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the rules that interpret equations as functions.

| Page                                             | Contents                                                                                                                                                                                                                                                          |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Core concepts](01-concepts.md)                  | Introduces the necessary ideas and terminology to use Bellman-SYM. We cover how a model is written as stages, periods and a trellis, what the stage files mean, how a solver is built from that meaning through the Rosetta stone, and what follows for the workflow. |
| [The stage](02-stage.md)                         | Using a running example, reviews the components of a stage: perches, fields and kernels.                                                                                                                                                                          |
| [The Bellman-SYM language](03-language.md)       | Shows how a stage is written in a stage file. We read the buffer-stock file and explain how its objects are typed and how its blocks are written.                                                                                                                 |
| [Periods and trellis](04-periods-and-trellis.md) | Shows how connectors join stage files into periods, and periods into a trellis. We inspect a six-period reference variant from the repository's portfolio application.                                                                                                        |
| [Semantics](05-semantics.md)                     | Describes what elaboration builds from a stage file, on the buffer-stock stage: the table of definitions, the two initial diagrams and the two builders graphs, and how parameter values, methods and settings are then attached. |
| [Workflow](06-workflow.md)                       | Sets out the four steps of the workflow, and lists the files that make up a project and what each one states.                                                                                                                                                                                              |
| [Fields, evaluation and methods](08-fields-evaluation-and-methods.md) | Explains which fields a stage returns as functions, what the evaluation of a field does, and where a numerical method may stand. |

> [!note]- Key terminology
> | Term | Meaning |
> |---|---|
> | [Stage](../wiki/stage.md) | One self-contained decision problem, written as one stage file, a `.bl` file ([The stage](02-stage.md)). |
> | [Perch](../wiki/perch.md) | One of the three information sets within a stage: arrival, decision and continuation ([The stage](02-stage.md) §1.1). |
> | [Field](../wiki/field.md) | A typed economic quantity of a stage, such as a state, a control, a shock or a value, known at one perch ([The stage](02-stage.md) §1.2). |
> | Block | The unit that connects one perch to the next, forward or backward, with typed inputs, outputs and equations ([The Bellman-SYM language](03-language.md) §2.2). |
> | [Semgraph (semantic graph)](../wiki/semgraph.md) | What elaboration builds from the stage files: a typed table of every declared object and graphs whose boxes are the model's operators ([Core concepts](01-concepts.md) §3). |
> | Elaboration | The step that reads the stage files and constructs the semgraph ([Workflow](06-workflow.md) §1; [The stage](../Bellman-Sym/API/stage/01-the-stage.md)). |
> | Specifying a stage | The three bindings, [methodization](../wiki/methodization.md), [calibration](../wiki/calibration.md) and configuration, which attach methods, parameter values and settings to a stage; the trellis factory retains calibration before methodization ([Core concepts](01-concepts.md) §3; [The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md)). |
> | Initial diagram | The blocks of one direction on the fields they read and write; one graph backward and one forward ([The initial diagrams](../Bellman-Sym/API/stage/02-initial.md)). |
> | Builders graph | The same blocks as the operators they denote, on function wires backward and on measure wires forward ([The builders graphs](../Bellman-Sym/API/stage/03-build.md)). |
> | Grain | How far a graph's builders are opened: at the builder grain, one box per block; at the primitive grain, each block opened into its primitive operators ([The builders graphs](../Bellman-Sym/API/stage/03-build.md) §4). |
> | [Builder](../wiki/builder.md) | The operator a block denotes; one box at the builder grain ([A builder](../Bellman-Sym/API/stage/04-builder.md)). |
> | [Connector](../wiki/connector.md) | A mapping that identifies a field of one stage with a differently named field of another ([Periods and trellis](04-periods-and-trellis.md)). |
> | [Period](../wiki/period.md), [trellis](../wiki/trellis.md) | A period joins the stage occurrences of one horizon step; a trellis joins periods across time ([Core concepts](01-concepts.md) §2; [Periods and trellis](04-periods-and-trellis.md)). |
> | [Specified stage](../wiki/specified_stage.md) | A stage that has been elaborated, calibrated, methodized and configured ([Core concepts](01-concepts.md) §3; [The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md)). |
