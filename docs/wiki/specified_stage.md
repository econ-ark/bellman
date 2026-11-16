---
slug: specified_stage
title: Specified stage
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
- path: docs/Bellman-Sym/API/factory/index.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Specified stage

A **specified stage** is a constructed [[stage]] with its method, numerical-setting and parameter values supplied, the version that [Kinds and sorts](../bellman-calculus/APPX-D-KINDS-AND-SORTS.md) §6 lists as configured. The name distinguishes the resulting [[stage|stage occurrence]] from the [[wiki/spec_factory|recipe]] and partial source mappings used to prepare them. It is not a synonym for a solved model or a callable numerical implementation.

## Specification order

For one stage, the examples retain four explicit steps:

```text
elaboration → methodization → calibration → configuration
```

Calibration requires a value for every declared parameter and refuses values at which it finds a condition of the parameter lines or of the definitions of [[parameters|derived parameters]] to fail ([[calibration]]). Methodization reads the stage's methods files: the methods, grids and handlers they type and the lines they add. Configuration values the settings those files declare and checks each value against its declared set and the methods that read it, so it is made after methodization; calibration may also come after either of the others. Each binding adds to the [[stage|stage occurrence]] it is called on and returns it; nothing is copied, and a later binding replaces the earlier binding made by the same verb ([The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md) §1). This does not imply that the operations commute.

The trellis factory uses calibration before methodization. Its four stopping points, the symbolic trellis and the trellis after each verb, are the results of the four calls: `elaborate_trellis`, then `calibrate_trellis`, `methodize_trellis` and `configure_trellis`, each reading its mapping from the [[trellis|syntactic trellis]] given as its second argument. Each binding verb with its source held fixed is a **binding map**, written $\mathcal C_c$, $M_m$ and $K_s$ in [Appendix G](../bellman-calculus/APPX-G-FUNCTIONAL-PROGRAMMING.md) §7, so that a specified stage is $K_s\,M_m\,\mathcal C_c(S)$.

## Meaning and numerical execution

A method word typed without a handler leaves the routine unspecified even when the required mappings exist. Numerical use additionally needs compatible [[handler|handlers]], representations, supplied data for every continuation value-type field, feasible boundary treatment and accuracy checks. The user supplies terminal data at realization; the trellis file holds none. Analytic assumptions are not supplied by settings or calibration.

The [[wiki/spec_factory|specification factory]] resolves inputs to these operations; the syntactic trellis it returns is a dictionary of bindings, not the stage's mathematical graph. The entries [[symbolic_stage|symbolic stage]], [[methodization]], [[settings]], [[calibration]] and [[parameters]] explain the individual concepts. Exact signatures and the behavior at the places are in [Stage functions](../Bellman-Sym/API/factory/stage-factory.md).
