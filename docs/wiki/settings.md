---
slug: settings
title: Settings
tags:
- methodization
- stage-lifecycle
wiki_status: canonical
last_reviewed: '2026-11-14'
reviewed_by: Codex (Astra); source-checked. Revised by Claude (Fable), session of 5 November 2026, at AAS's request, for the settings declared with their domains in the methods file, checked against the Bellman calculus page on methods, and revised after one adversarial review round. Revised by Claude (Fable), session of 14 November 2026, for AAS's ruling of that day that a method's entry writes no number
sources:
- path: docs/bellman-calculus/06-Methods.md
  class: canonical
  date: '2026-11-14'
- path: docs/Bellman-Sym/API/factory/stage-factory.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/API/factory/spec-factory.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Settings

> [!summary]
> **Settings** are the numerical choices a method reads: the bounds and the count of a [[grid]], a tolerance, an iteration limit, the number of quadrature nodes, a rule chosen among finitely many labels. They configure how a computation is approximated; [[parameters|parameters]] define the economic model. A **setting** is a name declared with a set in a methods file, the [[addition]] to the stage file, and its value, written in the settings file, is bound by `configure`, which refuses a value outside the declared set.

> [!info]- Relationship with other documents
> **Formal account** — [Methods](../bellman-calculus/06-Methods.md) §6: a setting as a declared name a method's label reads, with no value in the signature.
> **Builds on** — [[grid|Grid]]: the component whose factors name settings; [[methods|Methods]]: the words whose keyword arguments name them.
> **Used by** — [Parameters and settings](../Bellman-Sym/API/stage/06-par-and-settings.md): the table `stage.settings`; [Stage functions](../Bellman-Sym/API/factory/stage-factory.md): the verb `configure`.

A setting is told from a parameter by the file that declares it: a parameter is declared by the [[stage|stage file]] and defines the model, including any discrete domain that is part of the model; a setting is declared by the methods file and configures a method. A methods file may also define a [[parameters|derived parameter]] by `:=` from the parameters, with or without a declared set, which is a parameter and no setting.

## 1 Declared with their domains

A methods file declares each setting it reads at file level, in the form the stage file declares a parameter, with its set and a description:

```bl
n_a : ℕ              :: ["number of points of the savings grid"]
a_min : Xa           :: ["lower bound of the savings grid"]
a_max : Xa           :: ["upper bound of the savings grid"]
n_ψ_nodes : ℕ        :: ["quadrature nodes of the permanent shock"]
tol_v : ℝ₊₊          :: ["tolerance of value function iteration"]
```

A bound of a grid is a point of the set the stage declares for the coordinate, `Xa` for the savings `a` or a literal set such as `ℝ₊`; a count is a natural number; a tolerance is a positive real; a setting valued in a finite set of labels, such as a tie-breaking rule, is declared on that set. A declared set may name a parameter or a derived parameter, as `tol_s : (0, ρ)` does. A name is declared once in a stage, and two declarations of one name with different sets are refused. The scope of a declaration is the addition and the stage it is unioned with; where two stages of one [[period]] each declare one name, they denote one setting of that period, as a parameter name does. A grid entry names settings and holds no number: `policy.grid : !Cartesian(a=(a_min, a_max, n_a))` names three. A method word's keyword argument names a declared setting for every number the method reads, `!gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)`, and holds no number: an entry that writes one is refused, as a grid entry that writes one is. An argument may hold a quoted string, which is the value of the argument and no setting. An undeclared name is refused as any other is.

## 2 Bound by configure

The values stand in the settings file, and the [[stage]] verb `stage.configure(settings_source)`, with a path or a mapping, binds them as `calibrate`, the verb of [[calibration]], binds a parameter's value; `configure_trellis(elaborated, syntactic)` applies it at every position of a [[trellis]]. In the recommended order configuration follows the union of the stage file with its additions and the elaboration of the unioned stage, so that the settings it binds are those the methods file declares, read against the methods and grids that name them. It judges each value against the setting's declared set, reading each parameter that the set names at its calibrated value, and each derived parameter at the value its definition takes at the calibration. It refuses a value outside the declared set, naming the line of the methods file where the setting is declared, and a name with no value. A value inside its declared set is still refused where the method or the grid that reads it does not admit it: a keyword's value outside the domain the method's row names, or a bound or a count of a grid that fails the checks stated below ([The binding verbs](../Bellman-Sym/API/stage/09-binding-verbs.md) §3). A key of a shared settings file that no declaration names declares no new setting and is read by no method: `configure` binds its value, and `stage.settings` lists it after the declared settings with no set, which is where a misspelled key shows. A configuration with a misspelled key is refused, under `setting-unvalued`, only where the setting the key was meant for has no value from the source and none from an earlier configuration; after an earlier configuration the earlier value stays bound, and the misspelled key is bound beside it. The bound values stand in the stage's record of bindings; no value is part of a signature.

`stage.settings` lists every declared setting with its value, the [[operator]] that reads it, the method there and, where the setting is a factor of that operator's grid or the declared points of `!Points`, the grid constructor; `stage.settings["n_a"]` answers one setting's record, whose `value` is the configured value ([Parameters and settings](../Bellman-Sym/API/stage/06-par-and-settings.md) §2). `stage.par` lists the parameters and no setting.

An empty settings mapping is admissible for a stage whose methods declare no setting; it chooses no method. Recording a grid size demonstrates neither numerical accuracy nor adequate treatment of the bounds: at configuration the package checks each bound pair ordered and inside the coordinate's set, each count at least two, each node set strictly increasing, the shape, finite coordinates and decidable membership of declared points, the requirements written after `require=` that the bound values decide and the equality of the points of a grid beside an authored table with the table's knots, where both are known exactly at configuration, and nothing more ([Methods](../bellman-calculus/06-Methods.md) §5). Where the coordinate's set names a parameter, as a definition `Xa := [a_lo, inf)` would, a bound must lie in that set at the parameter's calibrated value. The package does not yet check this ([Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) §5.3). It decides the membership from the set's definition alone, so it refuses such a bound under `grid-bounds`. The entry [[specified_stage|specified stage]] states the order in which the three bindings, calibration, [[methodization]] and configuration, are made, and the [[wiki/spec_factory|specification factory]] states how the sources of a [[wiki/spec_factory|recipe]] combine. Exact configuration behavior is in [Stage functions](../Bellman-Sym/API/factory/stage-factory.md).
