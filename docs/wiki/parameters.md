---
slug: parameters
title: Parameters
tags:
- parameters
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/Bellman-Sym/API/factory/stage-factory.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/01-stage.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/03-field-equations.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Parameters

**Parameters** define the mathematical economic model: for example, discounting, risk aversion, the coefficients of [[operator#Kernels|shock probability distributions]] and scalars that define an economic state domain. A declaration in a `.bl` [[stage|stage file]] supplies a parameter's name and domain. [[calibration|Calibration]] supplies its value through a separate source mapping. A parameter is no [[field]] and no [[semgraph|wire]] of a graph: it is named inside the definitions that use it, and its declaration and value stay open to inspection.

`stage.par` lists the parameters of a [[stage|stage version]], each with its declared set and its bound value or the word `unbound`. `stage.par["ρ"]` answers one parameter's record, read by the name the file declares, and its `value` is the number calibration bound ([Parameters and settings](../Bellman-Sym/API/stage/06-par-and-settings.md) §1).

## Parameters versus settings

A discrete set of housing choices can be part of the model itself; the scalars defining that set are parameters. A finite [[grid]] used only to approximate a continuous savings domain is a numerical representation; its bounds and size belong to the [[settings]]. The classification depends on what the quantity means, not whether it happens to be an integer or is called a grid size.

In the constrained consumption example, `ρ : (1, inf)` declares risk aversion above one. A calibration mapping can supply `ρ: 2`. The domain belongs to the equation's meaning; a [[handler]] option cannot silently replace it. See [Stages](../Bellman-Sym/01-stage.md) and [Field equations](../Bellman-Sym/03-field-equations.md).

A parameter is declared by a stage and belongs to the [[period]] the stage stands in: a name two stages of one period declare is one parameter of that period. Its declared sets must be the same or have a nonempty intersection the package can establish for real sets and intervals with numeric endpoints; its calibration sources must supply one value. Conflicting declarations or values are refused with the period and declaring stages identified. The same spelling in another period is another parameter ([The trellis factory](../Bellman-Sym/API/factory/trellis-factory.md) §4). A field name, by contrast, is local to its stage. Every declared parameter needs a value for calibration. Shared mappings may contain extra keys, but those keys do not create new parameter declarations. The [[trellis|syntactic trellis]] holds the merged mappings that the [[wiki/spec_factory|specification factory]] produces from such sources, and the stage verb binds and checks its required inputs.

Parameter restrictions defining admissible economic models are distinct from search choices made by an external estimation algorithm. That distinction does not create an estimation API in [[sym|Bellman-SYM]]. Numerical feasibility, existence of an optimum and statistical identification also do not follow merely from supplying admissible parameter values.
