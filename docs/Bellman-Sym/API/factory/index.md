---
title: The factory API
tags:
  - docs/api
audience: user
type: api
topic: [factory]
---

# The factory API

> [!summary]
> The Bellman factory is fourteen public functions of the package `bellman`, which act on two dictionaries of one shape and on one stage class. Three read files into a record or into the [syntactic trellis](../../../wiki/trellis.md), the model as written, two elaborate, three bind, one appends a [period](../../../wiki/period.md), one elaborates and binds a syntactic trellis in one call, one runs the whole route, two draw and one counts what a verb changed. This page lists them, with the page that states each one's signature, what it reads, what it returns and what it refuses; [The Bellman factory](../../08-bellman-factory.md) is the route through them on the durables model.

> [!info]- Relationship with other documents
> **Builds on** — [The Bellman factory](../../08-bellman-factory.md): the route and the words; [The stage](../stage/01-the-stage.md): the stage that elaboration returns.
> **Used by** — [Stage functions](stage-factory.md), [Recipe functions](spec-factory.md), [Period functions](period-factory.md) and [The trellis factory](trellis-factory.md): the four reference pages.
> **See also** — [Model directory layout](../../reference/model-directory-layout.md): the folders of a registry.

## 1 The fourteen functions

A function of a stage is imported from `bellman.stage`, one of a period from `bellman.period` and one of a trellis from `bellman.trellis`, as `from bellman.trellis import load_recipe`; the refusal class `FactoryError` from `bellman.refusals`.

| Function | Returns | Reference |
|---|---|---|
| `bellman.stage.load_stage(path)` | the record of one stage file | [Stage functions](stage-factory.md) §2 |
| `bellman.stage.elaborate_stage(record, bind=True)` | the stage of a record, with the sources it supplies bound | [Stage functions](stage-factory.md) §2 |
| `bellman.trellis.load_recipe(directory, recipe, **fills)` | the syntactic trellis of a [registry](../../../wiki/spec_factory.md) | [Recipe functions](spec-factory.md) §2 |
| `bellman.trellis.assemble_trellis(directory, recipe, **fills)` | the specified trellis of a registry | [Recipe functions](spec-factory.md) §4 |
| `bellman.trellis.accrete(trellis, period, inter_connector=None)` | the trellis with the period appended | [Period functions](period-factory.md) §3 |
| `bellman.period.diagram_period(trellis, h)` | a drawing of one period | [Period functions](period-factory.md) §5 |
| `bellman.trellis.load_trellis(file)` | the syntactic trellis of a trellis file | [The trellis factory](trellis-factory.md) §2 |
| `bellman.trellis.elaborate_trellis(syntactic, previous=None)` | the elaborated trellis, symbolic | [The trellis factory](trellis-factory.md) §3 |
| `bellman.trellis.calibrate_trellis(elaborated, syntactic)` | a new elaborated trellis, its stages calibrated | [The trellis factory](trellis-factory.md) §4 |
| `bellman.trellis.methodize_trellis(elaborated, syntactic)` | a new elaborated trellis, its stages methodized | [The trellis factory](trellis-factory.md) §4 |
| `bellman.trellis.configure_trellis(elaborated, syntactic)` | a new elaborated trellis, its stages configured | [The trellis factory](trellis-factory.md) §4 |
| `bellman.trellis.specify_trellis(syntactic, previous=None, kinds=KINDS)` | the specified trellis of a syntactic trellis, bound under the kinds `kinds` names among `calibration`, `methods` and `settings`, the three kinds of `KINDS`, each stage occurrence copied once | [The trellis factory](trellis-factory.md) §4.1 |
| `bellman.trellis.respecify_trellis(specified, before, syntactic, kinds=KINDS)` | the trellis `specify_trellis(syntactic)` returns, made from the trellis specified for `before` by binding again the stage occurrences whose record changed | [The trellis factory](trellis-factory.md) §4.2 |
| `bellman.trellis.changed_positions(before, after)` | the positions a verb bound, a copy of a binding among them | [The trellis factory](trellis-factory.md) §5 |
| `bellman.trellis.diagram_trellis(trellis, periods=None)` | a drawing of the periods and their [inter-period connectors](../../../wiki/connector.md) | [The trellis factory](trellis-factory.md) §6 |

Five functions of a period are imported beside them, the first four from `bellman.period` and the fifth from `bellman.trellis`: `period_joins(period)`, the joins of a period and its outputs; `computable_together(period)`, its stage keys in layers; `forward_order(period)` and `backward_order(period)`, its stage keys in the order of computation and in the reverse order; and `inter_period_joins(mapping, later, earlier)`, the joins an inter-period connector makes. Each reads the fields of the period's elaborated stages; [Period functions](period-factory.md) §4 states them.

The stage's own verbs, `stage.calibrate`, `stage.methodize` and `stage.configure`, are methods of the stage object, and the trellis verbs apply them to each [stage occurrence](../stage/01-the-stage.md), one elaboration of a stage file at one position of the trellis.

## 2 The record

Every function that elaborates or binds reads records of one form: `{"stage": {"text": text, "origin": origin}, "calibration": {...}, "settings": {...}, "methods": {...}, "provenance": {...}}`. `load_stage(path)` of `bellman.stage` writes this form with the three mappings empty; `load_trellis` and `load_recipe` of `bellman.trellis` write it complete for every period. The three mappings are present even when they are empty, and `None` is not an empty mapping; a loaded methods mapping may hold a `methods` list, and the record's `methods` value is the mapping, never the list. `label` is the one optional key besides `provenance`, and a path string in place of the `stage` mapping is refused, since elaboration reads no file. Nothing that elaborates or binds merges anything: precedence is settled in the syntactic trellis, by `load_recipe` when a registry is read, or by the application when it writes the records itself.

## 3 The order of the bindings

The bindings are made in the order calibrate, methodize, configure, on a trellis as on a stage. Configuration is defined on methodized versions only, because the settings are read against the methods that name them. A stage verb adds its binding to the stage it is called on and returns it; a trellis verb returns a new elaborated trellis and leaves its argument unchanged, and it binds a stage occurrence where the mapping the syntactic trellis holds at its key differs from what the stage occurrence holds, and copies it where it does not. The four stopping points, the symbolic trellis and the trellis after each verb, are therefore the results of the four calls, `elaborate_trellis` and then the three trellis verbs, each reading its mapping from the syntactic trellis given as its second argument. No call solves a model.

## 4 The refusals

A refusal of the factory is raised as `FactoryError`, which `bellman.refusals` exports, and carries a rule name under `.rule`. Each diagnostic names the rule, the address, the objects concerned and what to write. Each rule below links its entry on the [Refusals](../../reference/refusals.md) page, which gives the rule's claim, its smallest example and the refusal that example provokes.

| Rule | Raised by | When |
|---|---|---|
| [`recipe-shape`](../../reference/refusals.md#recipe-shape) | `load_recipe` | the recipe has no `stages` key; a stage entry or a kind's block is not a mapping; a kind's block has no `all` list; `periods:` is not a pair; a range is not written `lo-hi`; two ranges overlap; a stage key is listed twice or has no file under `stages/` |
| [`recipe-source`](../../reference/refusals.md#recipe-source) | `load_recipe` | a source name is written absolute or with `..`; a source file is not in the registry; a `parent:` is not a name, or its chain cycles or exceeds ten files |
| [`recipe-slot-unknown`](../../reference/refusals.md#recipe-slot-unknown) | `load_recipe` | a keyword names no slot of the recipe |
| [`recipe-template-agreement`](../../reference/refusals.md#recipe-template-agreement) | `load_recipe` | the recipe names a stage that no period of the trellis file holds, or a period holds a stage the recipe omits at a period it occupies |
| [`slot-value-not-a-mapping`](../../reference/refusals.md#slot-value-not-a-mapping) | `load_recipe` | a slot is given a string |
| [`fill-names-nothing`](../../reference/refusals.md#fill-names-nothing) | `load_recipe` | a fill key that no receiving stage declares and no `registry` block admits |
| [`fill-mixes-kinds`](../../reference/refusals.md#fill-mixes-kinds) | `load_recipe` | a flat fill names both parameters and settings |
| [`trellis-file-shape`](../../reference/refusals.md#trellis-file-shape) | `load_trellis`, `load_recipe`, `diagram_period`, `diagram_trellis` | a trellis file without `periods`, or a record without `stage`; a period index the trellis does not hold |
| [`record-shape`](../../reference/refusals.md#record-shape) | `elaborate_stage`; `elaborate_trellis`; `calibrate_trellis`, `methodize_trellis` and `configure_trellis`; the five functions of a period | a path string, or a dictionary that is not a record, in place of the record; a record whose `calibration`, `settings`, `methods` or `provenance` is no mapping, or whose supplied digest or location disagrees with its text; two records of one digest whose texts differ; a position of the elaborated trellis that holds a record, a position of the syntactic trellis that holds neither a record nor a stage, or a record whose text differs from the version held at its position; a record at a key of a period whose joins are read, where an elaborated stage must stand |
| [`period-join-cycle`](../../reference/refusals.md#period-join-cycle) | `elaborate_trellis`, `accrete` | the authored pairs of a period form a cycle, or a connector joins a stage to itself |
| [`connector-names-no-field`](../../reference/refusals.md#connector-names-no-field) | `elaborate_trellis`, `accrete` | a connector is no mapping or is written in the keyed form with other keys than `from`, `to` and `fields`, or two entries map one continuation field; a connector whose endpoint names no field, or several, is a diagnostic of the trellis's connection report and no refusal |
| [`period-parameter-agreement`](../../reference/refusals.md#period-parameter-agreement) | `elaborate_trellis`, `accrete`; `calibrate_trellis` and `configure_trellis` for the values | two or more stages of a period declare one parameter, or one setting in their additions, with sets that have no nonempty intersection the package reads, or supply it two values, or a value that lies outside a declared set |
| [`readable-file`](../../reference/refusals.md#readable-file) | `load_stage`; `stage.calibrate`, `stage.methodize`, `stage.configure` and `load_trellis` for a source file named by its path | a path that names no `.bl` file, or a stage file that does not exist or cannot be read as UTF-8 text; a source file that does not exist, does not read as one YAML mapping, or writes a key twice |
