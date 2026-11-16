---
slug: calibration
title: Calibration
tags:
- parameters
- stage-lifecycle
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/Bellman-Sym/API/factory/stage-factory.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/API/factory/spec-factory.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Calibration

**Calibration** supplies values for the model's declared economic [[parameters]]. It is distinct from [[settings]], which configure numerical approximation. Declaring risk aversion in a `.bl` [[stage|stage file]] fixes its name and its declared set; supplying a particular value calibrates that declaration. The parameter lines of a file together define one admissible set of parameter vectors, and each line adds one condition: a declaration adds that the parameter's value lies in its declared set, which may name other parameters, as `Γ : (0, R)` does, and the definition of a [[parameters|derived parameter]] adds that its formula has a value in the set the definition declares, which is `ℝ` where it declares none. The values a calibration supplies are one vector of that set ([Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §4).

The stage verb is `stage.calibrate(calibration_source)`, with a source path or mapping; `calibrate_trellis(elaborated, syntactic)` applies it at every position of a [[trellis]] with the calibration the [[trellis|syntactic trellis]] holds there. It requires a value for every declared parameter and refuses a value for a [[parameters|derived parameter]]. It judges the values in three steps. First it judges each declared value against the parameter's declared set and refuses a value outside it. Second it evaluates each derived parameter's definition at the declared values, and refuses a definition that has no value there. Third, at the declared and the derived values together, it judges each derived parameter's value against the set its definition declares, and every membership the first step left undecided, such as that of a set that names a derived parameter, and again refuses a value outside its set. Where the steps do not decide a membership, as for a parameter declared on a set whose bound holds an expectation over a shock `y`, `(0, E_{y}(y))`, the value is bound and `stage.obligations()` lists the membership as a condition that stays required ([The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md) §2). The checks of distributions and supports follow, and read the derived values as well. The verb adds the values to the [[stage|stage occurrence]] it is called on and returns it, with the mapping among its bindings; `stage.par["ρ"]` then answers the parameter's record, whose `value` is the number bound. Parameter names remain symbolic in retained equations. Additional shared-source keys can remain in the mapping without creating new declarations. In a trellis, a parameter name two stages of one [[period]] declare is one [[parameters|parameter]] of the period: `calibrate_trellis` supplies it once, from the sources of the stages that declare it, and refuses two sources that give it two values or a value outside a declaring stage's set ([The trellis factory](../Bellman-Sym/API/factory/trellis-factory.md) §4).

Stage examples apply elaboration, [[methodization]], calibration and configuration as four explicit steps. The trellis factory applies calibration before methodization. The stage API also permits other binding orders, with checks deferred until their inputs exist. Configuration applied before methodization binds the settings without judging them, since no methods file declares them yet; methodization then judges them against the settings its files declare, and refuses a declared setting with no value under `setting-unvalued` and a value outside its declared set under `setting-outside-set`. Calibration may likewise be applied after either ([The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md) §3). Applying `stage.calibrate` again binds the new values on the same stage, in place of the earlier ones, and returns that stage, so that every variable that refers to the stage reads the new values; `calibrate_trellis` applied again returns a new trellis whose stage occurrences hold the new values, and leaves the earlier trellis as it was. This does not prove that the binding operations commute. A refused calibration leaves the [[stage|stage version]] as it was, with its earlier values. A subsequent connection report on that earlier trellis reads the values it still holds, not values from the refused request. See [[specified_stage|specified stage]] for the complete lifecycle.

In a [modular model](../bellman-calculus/APPX-H-MODULARITY.md), repeated declarations share their operators and calibration sources. Their supplied fields may differ, and methods and settings remain separate numerical choices. A stage occurrence's position is an address in the trellis, not an input to its equations. The recipe may nevertheless select different calibration sources by position; the package accepts such models without asserting modularity.

A recipe can combine baseline and overriding parameter sources before calibration: the syntactic trellis holds the merged mappings, and the stage verb binds. The merge and parent-source rules are those of the [[wiki/spec_factory|specification factory]]. Merging source mappings does not itself validate stage mathematics or produce a numerical solution. A calibrated stage still needs the applicable analytic assumptions, compatible methods and continuation data.

See [Stage functions](../Bellman-Sym/API/factory/stage-factory.md) and [Recipe functions](../Bellman-Sym/API/factory/spec-factory.md).
