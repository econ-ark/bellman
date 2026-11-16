---
title: Workflow
tags:
  - bellman-sym
  - user-facing
  - workflow
status: Draft
related:
  - "[[04-methodization]]"
  - "[[08-bellman-factory]]"
date: 2026-09-19
audience: user
type: overview
---

# Workflow

> [!summary]
> Project Bellman's workflow has four steps, from writing the stages to realizing them as code. We set out each step and the call that performs it, and then list the files that make up a project and what each one states. A numerical grid belongs to the settings, because it approximates a function on the domain that the stage file declares. The loaders read each file at the path written for it, and the repository's model folders keep their files in one layout.

## 1 The four steps

| Step | Description | Implemented by |
| --- | --- | --- |
| **Writing the stages** | Write a dynamic problem as stages, and join stages into [periods](../wiki/period.md) and periods into a [trellis](../wiki/trellis.md) ([The stage](02-stage.md), [the language](03-language.md), [periods and trellis](04-periods-and-trellis.md)). | One stage file per stage, and either a Python dictionary that arranges the stages into periods and the periods into a trellis, built one period at a time with `bellman.trellis.accrete`, or a period template, a trellis file and a recipe in a registry ([The Bellman factory](../Bellman-Sym/08-bellman-factory.md)). |
| **Elaboration** | Bellman-SYM reads the stage files and constructs a semantic graph for every stage the dictionary names ([The stage](../Bellman-Sym/API/stage/01-the-stage.md)). | `bellman.stage.load_stage` and `bellman.stage.elaborate_stage` for one stage file; `bellman.trellis.load_trellis` or `bellman.trellis.load_recipe`, then `bellman.trellis.elaborate_trellis`, for a trellis |
| **Specifying the stages** | For one stage, attach [numerical methods](../wiki/methodization.md), [parameter values](../wiki/calibration.md) and [settings](../wiki/settings.md). The trellis factory retains calibration before methodization ([The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md)). | `stage.methodize`, `stage.calibrate` and `stage.configure` for one stage; `bellman.trellis.calibrate_trellis`, `bellman.trellis.methodize_trellis` and `bellman.trellis.configure_trellis` for a trellis, each given the dictionary of records it binds with; or the single call `bellman.trellis.assemble_trellis(directory, recipe)` for a registry and its recipe |
| **Realization** | A [numerical routine](../wiki/handler.md) is supplied for each operator, and the routines together perform, for example, value iteration, policy iteration or simulation. | Code that you write, or a toolkit recorded in the Rosetta stone. |

Each attachment adds its binding to the stage it is called on and returns that stage; nothing is copied, and a later binding replaces the earlier one of its kind. Realization lies outside Bellman-SYM.

## 2 Structuring a project

| File or source | Contents |
|---|---|
| Stage files (`.bl`) | Declarations, functions, shock laws and equations. |
| Period YAML | Which stage occurrences a period contains and the connectors between them. |
| Trellis YAML, or a trellis assembled in Python as in [Periods and trellis](04-periods-and-trellis.md) | Which periods the model has, each written out or a period template repeated, and which fields join adjacent periods. |
| Methods file (`methods.bl` beside the stage file) | The methods, grids and handlers typed at the places of the stage, the lines a solution method brings, and the settings they read, declared with their sets. |
| Settings YAML | Numerical options and approximation grids. |
| Calibration YAML | Economic parameter values. |
| Recipe YAML (`spec.yml`) | The path of the trellis file and of each stage's file, from the recipe's folder; for each stage and each of the three kinds, the ordered files and slots that supply it, and the periods a file or a stage applies to. |

Recipe ranges select calibration, methods and settings by position, and `periods: [lo, hi]` restricts a stage's occurrences. These operations remain available. A [modular model](../bellman-calculus/APPX-H-MODULARITY.md) instead keeps each repeated declaration's calibration sources fixed and supplies age-dependent quantities through fields. Methods and settings may differ between occurrences.

A finite grid approximates a function on its mathematical domain; it does not replace the domain declared in the stage file.

The files above, kept in a registry, which in a model folder is its subfolder `declaration/`, are read in one call: `load_recipe(directory, recipe)` of `bellman.trellis` reads the registry through its recipe and returns the [syntactic trellis](../wiki/trellis.md), the model as written, a dictionary of records in which every adjustment is made, a value that differs by period among them; `elaborate_trellis` and the three trellis verbs, which `bellman.trellis` also holds, then construct and bind it, and its `assemble_trellis(directory, recipe)` returns in one call the trellis those calls make. A fill, a dictionary bound by keyword to a slot of the recipe, changes parameter values or settings without editing a file, and only the stages whose mapping changed are bound again. [The Bellman factory](../Bellman-Sym/08-bellman-factory.md) is the route through these calls on the durables model, and the [factory API](../Bellman-Sym/API/factory/index.md) lists them. #spec_factory

> [!important] The layout of a model folder
> #syntax-rules #bellman-sym
>
> A model folder keeps every file the language reads in its subfolder `declaration/`, the registry from which its recipe's paths are read, and gives each stage a folder there that holds the stage file, its methods file and its note; Bellman Workbench reads the model from `declaration/`. The loaders themselves require no layout, since they read the paths a recipe or a trellis file writes, and placing the files in one folder does not choose a horizon, connect fields or solve a model. [Model directory layout](../Bellman-Sym/reference/model-directory-layout.md) states the layout and its rules.
