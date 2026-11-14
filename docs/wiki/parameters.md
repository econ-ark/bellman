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

**Parameters** define the mathematical economic model: for example, discounting, risk aversion, the coefficients of [[operator#Kernels|shock probability distributions]] and scalars that define an economic state domain. A **parameter** is a name declared in the `.bl` [[stage|stage file]] with a set, with no role word, no [[perch]] word and no law, which no block header lists and no line writes: `β : (0,1)`. A line of a block that writes a name so declared is refused under `parameter-or-field`. A role word, such as `!ctrl`, and a perch word, such as `!dcsn`, are written in the type of a [[field]], and a name that a block header lists is a field. A law, such as `z ~ N(0,1)`, gives a shock its distribution. The set is the parameter's declared set, which may name other parameters, as `Γ : (0, R)` does. [[calibration|Calibration]] supplies its value through a separate source mapping.

A **derived parameter** is a name defined by `:=`, without arguments, by a formula whose value is a number, from parameters, derived parameters and numbers, with or without a declared set: `h := 1/(1 - Γ/R)` or `q : (0,1) := (β*R)^(1/ρ)/R`. It is defined in the stage file or in a methods file, with signs, arithmetic, powers, `log`, `exp`, `min` and `max`, or by cases, `h : ℝ_{+∞} := if Γ < R then 1/(1 - Γ/R) else inf`, where a definition that may take an infinite value declares a set that holds it, and without a cycle among the definitions. A definition that declares a set must read at least one name. `ρ : ℝ := 2` is refused under `readable-form`, since a stage file declares the set of such a name and the calibration file supplies its number. Calibration supplies no value for a derived parameter and refuses one; its value is its definition evaluated at the calibrated values, and calibration refuses a value outside the set the definition declares. The parameter lines of a file together define one admissible set of parameter vectors, and each line adds one condition: a declaration adds that the parameter's value lies in its declared set, and a definition adds that its formula has a value in its declared set, which is `ℝ` where it declares none ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §4). A parameter is no [[field]] and no [[semgraph|wire]] of a graph: it is named inside the definitions that use it, and its declaration and value stay open to inspection.

`stage.par` lists the parameters of a [[stage|stage version]], each with its declared set and its bound value or the word `unbound`, and after them each derived parameter with its definition, written after its declared set where it declares one, and its value at the calibration. `stage.par["ρ"]` answers one parameter's record, read by the name the file declares, and its `value` is the number calibration bound ([Parameters and settings](../Bellman-Sym/API/stage/06-par-and-settings.md) §1).

## Parameters versus settings

A discrete set of housing choices can be part of the model itself; the scalars defining that set are parameters. A finite [[grid]] used only to approximate a continuous savings domain is a numerical representation; its bounds and size belong to the [[settings]]. The file that declares a quantity decides whether it is a parameter or a setting, and the author chooses the file by what the quantity means, not by whether it happens to be an integer or is called a grid size.

In the constrained consumption example, `ρ : (1, inf)` declares risk aversion above one. A calibration mapping can supply `ρ: 2`. The declared set belongs to the equation's meaning; a [[handler]] option cannot silently replace it. See [Stages](../Bellman-Sym/01-stage.md) and [Field equations](../Bellman-Sym/03-field-equations.md).

A parameter is declared by a stage and belongs to the [[period]] the stage stands in: a name two stages of one period declare is one parameter of that period. Its declared sets must be the same or have a nonempty intersection the package can establish for real sets and intervals with numeric endpoints; its calibration sources must supply one value. Conflicting declarations or values are refused with the period and declaring stages identified. The same spelling in another period is another parameter ([The trellis factory](../Bellman-Sym/API/factory/trellis-factory.md) §4). A field name, by contrast, is local to its stage. Every declared parameter needs a value for calibration. Shared mappings may contain extra keys, but those keys do not create new parameter declarations. The [[trellis|syntactic trellis]] holds the merged mappings that the [[wiki/spec_factory|specification factory]] produces from such sources, and the stage verb binds and checks its required inputs.

Parameter restrictions defining admissible economic models are distinct from search choices made by an external estimation algorithm. That distinction does not create an estimation API in [[sym|Bellman-SYM]]. Numerical feasibility, existence of an optimum and statistical identification also do not follow merely from supplying admissible parameter values.
