---
title: Stage functions
tags:
  - docs/api
audience: user
type: api
topic: [factory]
---

# Stage functions

> [!summary]
> `load_stage(path)` of `bellman.stage` reads one stage file into a record, and `elaborate_stage(record)`, also of `bellman.stage`, constructs from it a [symbolic stage](../../../wiki/symbolic_stage.md), whose [semgraph](../../../wiki/semgraph.md), the semantic graph, holds the typed fields and equations of the file. The stage's three verbs, `calibrate`, `methodize` and `configure`, each return a new version with one binding written, in that order.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](../../01-stage.md) and [Methodization](../../04-methodization.md): declarations and supported computations.
> **Used by** — [Period functions](period-factory.md) and [The factory API](./index.md): constructing independent stage occurrences.
> **Formal account** — [Appendix C](../../appendices/14-appendix-c-syntax-to-semantics.md): the assumptions needed to interpret equations as functions.

## 1 Loading and specifying a stage

The discounting stage leaves assets unchanged and multiplies the continuation value and the marginal value by its discount factor. From the repository root:

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/disc/disc.bl"))
calibrated = stage.calibrate({"β": 0.96})
methodized = calibrated.methodize({"methods": [{"on": "cntn_to_dcsn"}]})
specified = methodized.configure({})
```

An entry containing only `on` names a place of the stage, which methodization checks, and binds no method. The example binds the discount factor and supplies neither a solver nor a terminal continuation value; the empty settings mapping suffices because the entry references no setting. The trellis verbs apply the stage's three verbs to each [stage occurrence](../stage/01-the-stage.md) of a [trellis](../../../wiki/trellis.md).

For consumption, save the complete constrained stage from [Field equations](../../03-field-equations.md#1-consumption-and-savings) as `cons.bl` and use the `argmax` recognition entry from [Methodization](../../04-methodization.md#1-a-consumption-method). The separate [interior example](../../03-field-equations.md#3-an-implicit-policy-relation), `cons_interior.bl`, supplies the candidate and marginal-value equations required by the displayed `!egm` attachment. That attachment adds neither a missing boundary branch nor a proof of optimality.

## 2 Loading functions

### 2.1 load_stage and elaborate_stage

```python
record = bellman.stage.load_stage(path)
stage = bellman.stage.elaborate_stage(record)
```

`path` is a string or `Path` naming a `.bl` file. `load_stage` reads the file and returns its **record**: the text and the origin under `stage`, the calibration and the settings empty, the methods the empty methods mapping `{"methods": []}`, and the origin and the digest of the text under `provenance`. Nothing is parsed, and a caller completes the three mappings before elaboration binds them. `elaborate_stage` parses the record's text, constructs the stage at the record's origin with the record's provenance, binds the sources the record supplies, and returns the `ElaboratedStage`: the symbolic stage where the record supplies no source or `bind=False` is given, as for the record `load_stage` returns ([The stage](../stage/01-the-stage.md) §1); it reads no file. Given a path string, or a mapping that is not a record, it refuses under `record-shape` and says to write `elaborate_stage(load_stage(path))`. The temporary syntax tree and source-span table are discarded after construction; the retained semgraph holds the interpreted equations and typed definitions.

The application's helper `load_stage(name, lib)` has a different signature and resolves a module reference within a library; it is not `load_stage(path)` of `bellman.stage`. A caller that already holds a parsed term uses `make_stage(term, spans)` of `bellman.stage`, with the second argument supplied explicitly; a decoded term can use `spans=None`.

## 3 Methodization

```python
stage.methodize(methods_source)
```

`methods_source` is a methods YAML path or a mapping. The call adds the methods to the stage it is called on and returns that stage, whose read-only `methods` binding is keyed by the place at which each method is kept once its target is resolved: the entry `on: policy` of `!egm` with a block file is kept on the policy builder, `policy`; a representation entry is kept at the Evaluation it names, such as `cntn_to_dcsn.evaluate.value`; and an entry that names no method, handler or setting binds nothing ([Methods and places](../stage/07-methods.md) §2). A target holds one binding of each kind, and a later binding replaces the earlier one of its kind there, so a change of methods is made by calling `methodize` again. Read tagged YAML through `bellman.stage.sources.load_methods` when assembling a record yourself.

| Entry key | Requirement |
|---|---|
| `on` | Required; names one place of the stage: a builder, a line, an operator, a declared function or the Evaluation of the policy builder or of a backward value builder, written `policy.evaluate`, `<block-id>.evaluate.value` or `<block-id>.evaluate.marginal` (the paragraph below the table). |
| `method` | Optional numerical-method tag. |
| `handler` | Optional registered numerical-routine identifier. |
| `settings` | Optional values or setting references used by the method. A method that takes a grid, a representation such as `!Linear` or the endogenous grid method `!egm`, names its grid by the setting `grid`, whose value is the grid's kind written as a tag, `grid: !Cartesian`, with the grid's fields `orders` and `bounds` beside it ([Methodization](../../04-methodization.md) §3). |
| `block` | Optional path of a block file, for a method whose type takes a block. |

Each entry has one target, and each target appears at most once. An `on`-only entry is valid. Comma-separated targets and a nested `schemes:` list are not read. Method-specific equation-role bindings and options follow that method's contract.

An authored [block](../../01-stage.md#3-builder-blocks) describes a typed computation, and a method binds only at a place the stage holds: a builder, a line with an id, a line marked `!node`, an operator written in a line, a declared function, or the Evaluation that closes the policy builder or a backward value builder, at which a representation is written ([Methods and places](../stage/07-methods.md) §1). A statement marked `!node` is a place of its own, and its computation a [sub-builder](../../../wiki/sub_builder.md). An inspection address or a nested mathematical operation alone creates no place. [Appendix D](../../appendices/15-appendix-d-node-tag-and-field-indexing.md) §§3 and 6 tells an authored node from an operator occurrence inside an equation and states how an address names each.

Supported implicit equations and operator occurrences can receive methods without an added `!node`. For example, `policy.cons_choice` addresses the consumption relation, `argmax` addresses all such maximization occurrences in a stage, and `policy.choice.argmax` addresses the retirement example's specific occurrence. An occurrence-specific attachment overrides a stage-wide one. A `!node` target requires its own authored identifier; a positional address alone is insufficient. These addresses select computations without turning every containing statement into an authored node.

Duplicate targets, unknown method tags and unresolved targets are errors. A refusal names the entry and the stage's available places. Neither a method tag nor a block identifier supplies missing equations.

## 4 Calibration and configuration

```python
stage.calibrate(calibration_source)
stage.configure(settings_source)
```

Each source is a path or a mapping, and each call adds its binding to the stage it is called on and returns that stage. Calibration requires a value for every declared parameter, in the parameter's declared set, and stores them in the `calibration` binding, leaving the parameter names symbolic in the equations; extra names in a shared source are not bound. Retained conditions on the parameters alone are decided at the values: a false condition refuses, a true one is established with the values as evidence, and an undecided one remains required. Configuration requires prior methodization and a value for every setting an attached method references, names in nested grids or mappings included, and stores the values in the `settings` binding; the method records keep the authored setting names.

The bindings are made in the order calibrate, methodize, configure. Applying `calibrate` or `configure` again returns another version with the new values, the earlier version unchanged, and every version has its own copies of the graphs, sharing nothing with the version it came from. Mathematical domains remain declarations of the model; numerical grids and tolerances belong to the selected methods and settings.

## 5 Inspecting a stage

An `ElaboratedStage` has seven attributes, `name`, `metadata`, `definitions`, `initial`, `_builders`, `bindings` and `provenance`, the fifth the stored record of the builders graphs that `stage.builder` reads, and answers questions through them and through its own methods; [The stage](../stage/01-the-stage.md) and the pages after it state each with its printed form. `par` lists the declared parameters with their sets and, once calibrated, their values, and `par["ρ"]` answers one of them, whose `.value` is the bound value; `settings` lists each setting value with the place that reads it and the method that reads it, and `settings["n_a"]` answers one of them; `methods` prints the method bound at each place, and `methods["policy"]` answers the one bound at the target the methods file writes; `places()` lists the addresses that can receive a method; `obligations()` lists the conditions the construction states, each with its status; each of the stage's four graphs answers `diagram()` with a drawing, `stage.builder.bwd.diagram()` for the backward builders; and `print(stage)` prints the stage's sheet, its printed view ([The stage](../stage/01-the-stage.md) §3). `bindings` holds the three bindings, which `par`, `methods` and `settings` read, and `provenance` holds the origin, the text and the digest of the file, the source of each binding, the version of the package and the digests of its grammar files, and on a bound version the verb that made it, its source and, under `parent`, the provenance of the version it was made from, together with the stage occurrence's position and the ordered sources of its record when it stands in a trellis. Every projection is read-only; a version is never adjusted in place.
