---
audience: user
type: user-guide
---
# Bellman-SYM

> [!summary]
> Write a household's consumption problem in `.bl`, inspect its equations, then separate consumption, discounting, and investment into reusable stages. YAML supplies their connections, numerical choices, and parameter values. This guide covers authoring, assembly, inspection, and the Python interfaces; Bellman calculus develops the mathematical foundations.

> [!info]- Relationship with other documents
> **Builds on** — [Overview](../overview/index.md): the stage, its perches and fields, and the joining of stages into periods and a trellis, in prose.
> **Used by** — [Stages](01-stage.md): the complete income-and-consumption tutorial.
> **Formal account** — [Bellman calculus](../bellman-calculus/index.md): staged Bellman problems and their mathematical interpretation.

## 1 Reading order

Begin with the [buffer-stock consumption tutorial](01-stage.md). The household observes income, consumes from its available resources, and saves without borrowing. A **[stage](../wiki/stage.md)** is a module of that decision problem with three information sets, its **[perches](../wiki/perch.md)**: arrival, decision and continuation. The later examples reuse consumption as a separate stage and join it to discounting and investment.

| Step | Read | What to establish |
|---|---|---|
| Write a stage | [Stages](01-stage.md) | The household's information, admissible choices, resource transitions, and value equations. |
| Inspect its meaning | [From syntax to a mathematical problem](09-from-syntax-to-formal-problem-definition.md), then [the API](API/index.md) | The same equations with explicit state arguments and their required assumptions. |
| Reuse and compose | [Field equations](03-field-equations.md), [Periods](06-period.md), and [Trellises](07-trellis.md) | Separate consumption, discounting, and investment; choose the period boundary and terminal inputs. |
| Choose methods and parameters | [Methodization](04-methodization.md) and [The Bellman factory](08-bellman-factory.md) | Numerical choices and economic parameter values for each use of a stage. |
| Keep numerical results | [Solutions at the perches](11-solutions-at-the-perches.md) | Where a solver keeps what it computes: one plain dictionary for each stage occurrence, keyed by perch and by field, filled by the stage's compiled kernels. |
| Examine a numerical application | the lesson `tutorials/models/cons-port/03-solving-the-two-orders.ipynb` of the repository | The portfolio–consumption model solved in both orders of its stages and the consumption rules and risky shares compared. |

The lesson solves with the model's own numerical tool; parsing or constructing a stage solves nothing. A **stage occurrence** is one use of a stage file at one position of a period. Each stage occurrence can have its own parameter values and numerical settings. Construction and specification prepare stage occurrences; solving additionally requires numerical routines and continuation or terminal data.

For discrete alternatives, read [Branching](05-branching.md), which uses the separate work-or-retire example. Choosing a continuous portfolio share is not a discrete branch.

For data indexed by a parameter-defined number of cities or shock outcomes, see [Indexed data](01-stage.md#21-indexed-data). For an integer state whose values mean, for example, newborn or old, see [Category codes](01-stage.md#22-category-codes); [Periods](06-period.md#2-connectors) explains how connections preserve those meanings.

## 2 Files and authoring reference

| File | Contents | Guide |
|---|---|---|
| `.bl` | Stage declarations, functions, shock laws, and equations. | [Stages](01-stage.md) and [Field equations](03-field-equations.md). |
| Period and trellis YAML | Stage occurrences and compatible field connections. | [Periods](06-period.md) and [Trellises](07-trellis.md). |
| Methods file (`.bl`), with the settings and calibration YAML | The methods, grids and handlers typed at the places of a stage, the settings they read and the economic parameter values. | [Methodization](04-methodization.md). |
| Specification-recipe YAML | Which sources supply methods, settings and calibration, their precedence, and period-dependent assignments. | [The Bellman factory](08-bellman-factory.md). |

For individual spellings, use [Equation parsing rules](appendices/12-equation-parsing-rules.md), [Perch tagging rules](appendices/13-perch-tagging-rules.md), [Constraints](10-constraints.md) for bounds and the complementary-slackness clause, [Expression forms](reference/forms.md), [Shock distributions](reference/laws.md), [Method types](reference/methods.md), and [Symbol conventions](reference/symbols-conventions.md). [Operations](reference/operations.md) lists the kinds of operation of which a [builder](../wiki/builder.md), the operator a block of a stage file defines, is composed, and [Refusals](reference/refusals.md) the rules under which a stage file, an entry of a methods file or a model's files are refused. The [model directory layout](reference/model-directory-layout.md) describes the files of a model and where each is kept.

## 3 Inspection and Python interfaces

Inspection is part of using Bellman-SYM. The [API](API/index.md) lists every function in three tables, one for each of `bellman.stage`, `bellman.period` and `bellman.trellis`, and every path of the stage object in a fourth, and its pages take the object one level at a time, from [the stage](API/stage/01-the-stage.md) to [the binding verbs](API/stage/09-binding-verbs.md): the mathematical structure a constructed stage retains, its equations, its typed quantities and its numerical attachments. The factories load and specify those stages:

| Page | Responsibility |
|---|---|
| [The factory API](API/factory/index.md) | The fourteen functions of the Bellman factory and the page that states each. |
| [Stage functions](API/factory/stage-factory.md) | Load a stage file into a record, elaborate it, and bind one stage. |
| [Recipe functions](API/factory/spec-factory.md) | Read a registry through its recipe: the merge, the slots and the fills. |
| [Period functions](API/factory/period-factory.md) | Append a period, derive the order of its stages from their fields, and make the drawing of the period. |
| [The trellis factory](API/factory/trellis-factory.md) | Read a trellis file, elaborate and bind every period, and make the drawing of the trellis. |

For a new stage occurrence, loading and elaboration come first, then calibration, methodization and configuration, the order the factory uses. Each of the three bindings adds its binding to the stage occurrence it is called on and returns that stage; methodization must precede configuration, since the methods name the settings ([Methodization](04-methodization.md) §5). Inspecting the equations and attachments is separate from obtaining numerical policies.

## 4 Mathematical reference

The [Bellman calculus guide](../bellman-calculus/index.md) explains the mathematical foundations. Within this language guide, [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) gives rules R1–R12 for interpreting equations, including the assumptions for representing fields as functions of states. [Appendix D](appendices/15-appendix-d-node-tag-and-field-indexing.md) explains computation boundaries, collection selection, and implicit policy relations.

Folded abstract-grammar boxes use [ASDL](../wiki/asdl.md), a notation describing syntax-tree structure. Their constructor listings do not prove the economic assumptions needed for an equation's interpretation. The [concept wiki](../wiki/index.md) defines recurring terms.
