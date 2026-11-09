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

**Calibration** supplies values for the model's declared economic [[parameters]]. It is distinct from [[settings]], which configure numerical approximation. Declaring risk aversion in a `.bl` [[stage|stage file]] fixes its name and admissible domain; supplying a particular value calibrates that declaration.

The stage verb is `stage.calibrate(calibration_source)`, with a source path or mapping; `calibrate_trellis(elaborated, syntactic)` applies it at every position of a [[trellis]] with the calibration the [[trellis|syntactic trellis]] holds there. It requires a value for every declared parameter, adds the values to the [[stage|stage occurrence]] it is called on and returns it, with the mapping among its bindings; `stage.par["ρ"]` then answers the parameter's record, whose `value` is the number bound. Parameter names remain symbolic in retained equations. Additional shared-source keys can remain in the mapping without creating new declarations. In a trellis, a parameter name two stages of one period declare is one [[parameters|parameter]] of the period: `calibrate_trellis` supplies it once, from the sources of the stages that declare it, and refuses two sources that give it two values or a value outside a declaring stage's set ([The trellis factory](../Bellman-Sym/API/factory/trellis-factory.md) §4).

In the recommended order calibration comes first, followed by [[methodization]] and configuration. Only methodization must precede configuration, because the methods name the settings, so calibration may also be applied after either. Applying it again returns another stage version with new values; this does not prove that the binding operations commute. A failed calibration leaves the earlier stage version unchanged. A subsequent connection report on that earlier trellis reads the values it still holds, not values from the failed request. See [[specified_stage|specified stage]] for the complete lifecycle.

A recipe can combine baseline and overriding parameter sources before calibration: the syntactic trellis holds the merged mappings, and the stage verb binds. The merge and parent-source rules are those of the [[wiki/spec_factory|specification factory]]. Merging source mappings does not itself validate stage mathematics or produce a numerical solution. A calibrated stage still needs the applicable analytic assumptions, compatible methods and continuation data.

See [Stage functions](../Bellman-Sym/API/factory/stage-factory.md) and [Recipe functions](../Bellman-Sym/API/factory/spec-factory.md).
