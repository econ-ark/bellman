---
slug: symbolic_stage
title: Symbolic stage
tags:
- stage-lifecycle
- stage
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/Bellman-Sym/API/factory/stage-factory.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/API/stage/01-the-stage.md
  class: canonical
  date: '2026-09-28'
audience: user
type: concept
---

# Symbolic stage

A **symbolic stage** is the constructed [[stage]] before numerical methods, [[settings]] and [[calibration]] values are attached, the version that [Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §6 calls the stage as constructed. It is what `elaborate_stage(load_stage(path))` returns for one stage file, and what `elaborate_trellis` places at every position of a [[trellis]]. It does not mean that the stage retains a parser tree or has no interpreted mathematical equations.

`load_stage(path)` reads a `.bl` stage file into a source record, and `elaborate_stage(record)` parses and checks it and returns a stage containing its [[semgraph]] (semantic graph). On the symbolic stage `stage.methods` and `stage.settings` are empty, `stage.par` lists every [[parameters|parameter]] as `unbound`, and `repr(stage)` prints `ElaboratedStage('cons', symbolic)` for the consumption stage. Typed [[field|fields]], equations and definitions describe the problem, with parameter names still symbolic. Further functional interpretation requires its stated assumptions; construction is not a numerical solution.

A **stage file** is reusable `.bl` source; at the elaborator boundary it is also called a stage module. A **stage occurrence** is that file elaborated at one position of a [[period]], with its own three bindings; several stage occurrences of one file may sit in one period or across periods, each a separate constructed object that prints the file's declared name and records its position in its provenance. Each binding adds to the stage occurrence in place and returns it, and a text derived from the file is elaborated as its own stage occurrence with its origin recorded. Period and trellis assembly uses outer records; it elaborates the stage file at each position as its own stage occurrence and retains no whole-model syntax tree.

In a [modular model](../bellman-calculus/APPX-H-MODULARITY.md), repeated declarations share their operators and calibration sources. Their supplied fields may differ, and methods and settings remain separate numerical choices. A stage occurrence's position is an address in the trellis, not an input to its equations.

The entry [[specified_stage|specified stage]] describes the bindings that follow, with the stage examples applying [[methodization]], calibration and configuration after elaboration. The trellis factory retains its order calibration, methodization and configuration. Methodization supplies numerical choices without replacing missing mathematics.

See [Stage functions](../Bellman-Sym/API/factory/stage-factory.md) and [The stage](../Bellman-Sym/API/stage/01-the-stage.md).
