---
title: "Recipe functions"
tags:
  - docs/api
  - status/draft
  - spec_factory
  - implementation
status: Draft
related:
  - "[[08-bellman-factory]]"
date: 2026-09-23
audience: user
type: api
topic: [factory]
---

# Recipe functions

> [!summary]
> `load_recipe(directory, recipe, **fills)` of `bellman.trellis` reads a [registry](../../../wiki/spec_factory.md) through its recipe and returns the [syntactic trellis](../../../wiki/trellis.md), the model as written, with the three mappings of every [stage occurrence](../stage/01-the-stage.md) merged from the sources the recipe names. `assemble_trellis(directory, recipe, **fills)`, also of `bellman.trellis`, goes on to elaborate and bind that trellis and returns it specified. This page states what each reads, what it returns and what it refuses, and the form of the recipe.

> [!info]- Relationship with other documents
> **Builds on** — [The Bellman factory](../../08-bellman-factory.md) §3: the registry and the recipe of the durables model; [Model directory layout](../../reference/model-directory-layout.md): the folders of a registry.
> **Used by** — [The trellis factory](trellis-factory.md): the functions that elaborate and bind the syntactic trellis a recipe gives.
> **See also** — [Stage functions](stage-factory.md) §3: the form of a methods entry.

## 1 The smallest registry

A registry with one stage, the discounting stage `disc.bl` of the portfolio application, needs eight files, which a model folder keeps in its subfolder `declaration/` ([Model directory layout](../../reference/model-directory-layout.md)). The stage file and its methods file stand in the stage's folder, `stages/disc/disc.bl` and `stages/disc/methods.yml`, the second holding `methods: [{on: cntn_to_dcsn}]`, an entry that recognizes the discounting builder without selecting a numerical routine; `calibration/main.yml` holds `calibration: {β: 0.96}` and `calibration/near_terminal.yml` holds `calibration: {β: 0.98}`; `settings/main.yml` holds `settings: {}`; the [period](../../../wiki/period.md) template `period.yml` and the trellis file `trellis.yml` are:

```yaml
!period
name: discounting_period
stages: [disc]
connectors: []
```

```yaml
!trellis
name: discounting_example
periods:
  - {template: period.yml, repeat: 3}
inter_connectors:
  - {a: a}
```

The recipe, `spec.yml`, names the trellis file and the stage file by their paths from its own folder, and for the one stage and each kind an ordered list of sources, with a slot `$fill` in the calibration list and a range `"0-1"` that applies to the terminal period and the one before it:

```yaml
trellis: trellis.yml
stages:
  disc:
    stage: stages/disc/disc.bl
    calibration:
      all: [calibration/main, $fill]
      "0-1": [calibration/near_terminal]
    settings:
      all: [settings/main]
    methods:
      all: [stages/disc/methods]
```

One call reads the registry, here the folder `declaration/` of a model folder `discounting/`, and binds the slot:

```python
from bellman.trellis import load_recipe

syntactic = load_recipe("discounting/declaration", "spec.yml", fill={"β": 0.95})
syntactic["periods"][0]["stages"]["disc"]["calibration"]   # {'β': 0.98}: the range source stands after the fill
syntactic["periods"][2]["stages"]["disc"]["calibration"]   # {'β': 0.95}: the fill stands after the file
```

The index counts periods before the terminal one, so `"0-1"` is the terminal period and its predecessor, not the first two dates of life. The values satisfy the stage's declaration `β : (0,1)`; loading does not check that they do, since it constructs no stage.

## 2 load_recipe

```python
bellman.trellis.load_recipe(directory, recipe, **fills)
```

`directory` is the registry directory, `recipe` the name of its recipe file, and each keyword of `fills` binds the slot of that name. The call reads the recipe, the trellis file the recipe names under `trellis:`, the stage file each entry names under `stage:`, the period templates the trellis file names and every source file the recipe names, each once. It expands each `{template, repeat}` entry of the trellis file and repeats a single inter-period connector for each adjacent pair; puts each fill in its slot; merges each source list; and writes one record per stage and period, holding the stage's text and digest, its three merged mappings and the ordered sources that produced them. It returns the [syntactic trellis](../../../wiki/trellis.md): `periods`, `inter_connectors`, `registry` and `provenance`. Nothing is elaborated, and the stage files' declarations are read only to check the names a fill gives.

### 2.1 The recipe file

The recipe is a mapping with three keys, and it names every file it reads by its path from its own folder, the registry directory. `trellis:` names the trellis file, `trellis: trellis.yml`, and is required. `stages:` maps each stage key to a mapping whose `stage`, required, names the stage file, `stage: stages/disc/disc.bl`; whose `calibration`, `settings` and `methods` blocks each hold an `all` list and any number of range lists keyed `"lo-hi"`; and whose optional `periods: [lo, hi]` restricts the stage to an interval of periods; a kind whose block is absent gets the empty mapping. `registry:` maps a kind to a list of sources whose names no stage declares. A source is named relative to the registry without its extension, `calibration/main`; a slot is a `$name`. No file is read in place of a path the recipe does not write: an entry that names no stage file is refused even where a file `stages/<key>/<key>.bl` stands in the registry.

### 2.2 The merge

For a stage, a kind and a period, the list is the `all` list followed by the range list whose interval holds the period, if one does, and its entries are merged in that order:

| Values being merged | Rule |
|---|---|
| Mappings | Merge matching keys recursively and add new keys. |
| Methods lists | Match entries by their `on` target; merge matching entries and append new targets. |
| Scalars and ordinary lists | The later value replaces the earlier one. |

A later source changes the entries it names and keeps the rest. A methods entry lacking `on` cannot be matched, and a list holding one replaces the earlier list whole. Methods use the [form of a methods entry](stage-factory.md#3-methodization), `on` required and `method`, `handler`, `block` and `settings` optional. The merge resolves data; it does not check that a method suits the equations it is attached to, which is the stage's own methodize verb's work.

### 2.3 Slots and fills

A slot's position in its list is its precedence, a slot bound by no keyword contributes nothing, and the same slot may stand in the lists of several stages and kinds, where one fill is read wherever the slot stands. A slot name is a Python identifier other than `directory` and `recipe`. A fill takes one of three shapes:

| Shape | Example | Read as |
|---|---|---|
| Flat | `fill={"β": 0.95}` | read against the declarations of the stages that receive the slot; refused when it names both parameters and settings |
| By kind | `fill={"calibration": {"β": 0.95}, "settings": {"n_a": 200}}` | split, each list taking the part of its kind |
| Methods | `adjuster_method={"methods": [{"on": "policy", "method": "!egm"}]}` | a methods mapping, merged into the methods list by `on`, an entry of `!marginals` matched only by another of `!marginals` |

A mapping whose every top-level key is one of `calibration`, `settings` and `methods` is read by kind; any other mapping is flat. For a calibration fill a stage declares its parameters; for a settings fill it declares the keys of the settings files its settings list names and the setting names its methods files reference, since a stage file declares no setting. A methods fill is a method choice, and a recipe gives each stage its own methods slot, because one slot named by two stages' lists would attach one stage's handler to the other. The record's provenance holds, for each slot of each list, an entry `{"slot": name, "bound": whether the keyword was given, "names": the fill's names the stage declares}`.

### 2.4 The registry block

A source named under `registry:` assigns names that no stage declares. They stand under the trellis's top-level `registry` key, `{kind: {name: value}}`, with their sources under the trellis's `provenance`, are bound to no stage, and are copied unread by `elaborate_trellis` and the trellis verbs; a fill of such a name changes the `registry` mapping and nothing else. They are data for the application's own functions, such as the function that evaluates the durables model's wage schedule.

### 2.5 Files and parents

A source name resolves to the file spelled `.yml` or `.yaml`, and the file's kind is read from its top key, `calibration`, `settings` or `methods`, not from its name or extension. A file may name a `parent:` source, which is read first and merged as an earlier entry of the same list; a parent chain is limited to ten files and may not cycle. The keys `parent`, `description`, `version` and `__comment__` of a source file are not part of the mapping it contributes.

### 2.6 Refusals

Each refusal is a `FactoryError` carrying its rule name. `recipe-shape`: the recipe has no `stages` key, or names no trellis file; a stage entry or a kind's block is not a mapping; a stage entry names no stage file; a kind's block has no `all` list; `periods:` is not a pair; a range is not written `lo-hi`; two ranges of one stage and kind overlap; a stage key is listed twice. `readable-file`: the path an entry writes under `stage:` names no file, or no `.bl` file, refused as `load_stage` refuses it, at the address `stages.<key>.stage`. `recipe-source`: a source name is written absolute or with `..`; a source file is not in the registry; a `parent:` is not a name, or its chain cycles or exceeds ten files. `recipe-slot-unknown`: a keyword names no slot. `recipe-template-agreement`: the recipe names a stage that no period of the trellis file holds, or a period holds a stage the recipe omits at a period it occupies, the stage and both files named. `slot-value-not-a-mapping`: a slot is given a string. `fill-names-nothing`: a fill key that no receiving stage declares and no `registry` block admits, the receiving stages and their declarations named. `fill-mixes-kinds`: a flat fill names both parameters and settings. `trellis-file-shape`: the trellis file has no `periods`, or a record has no `stage`.

## 3 The syntactic trellis it returns

The result is a dictionary and is read by key. Every adjustment to the model, a fill, a value that differs by period or a method choice, is made in it before elaboration and binding.

| Access | Result |
|---|---|
| `syntactic["periods"][h]["stages"]` | the records of period `h`, by stage key, `h = 0` the terminal period |
| `syntactic["periods"][h]["stages"][key]["calibration"]`, and `["settings"]`, `["methods"]` | the merged mappings of that stage at that period |
| `key in syntactic["periods"][h]["stages"]` | whether the stage is active at `h` |
| `syntactic["periods"][h]["stages"][key]["provenance"]["source_lists"]` | the ordered sources of each mapping, with paths, digests and slot entries |
| `syntactic["inter_connectors"][h]` | the mapping joining `periods[h + 1]` to `periods[h]` |
| `syntactic["registry"]` | the registry-level names by kind |
| `syntactic["provenance"]` | the recipe and the trellis file with their paths and digests, and the sources of the registry block |

The syntactic trellis holds no stage, no graph and no solution.

## 4 assemble_trellis

```python
bellman.trellis.assemble_trellis(directory, recipe, **fills)
```

The call returns the specified trellis that `load_recipe(directory, recipe, **fills)`, `elaborate_trellis`, `calibrate_trellis`, `methodize_trellis` and `configure_trellis` make in this order, each verb given the syntactic trellis of the first call, and copies each stage occurrence once. It refuses whatever any of the five refuses, in the same order. A family of fills is a sweep, `[assemble_trellis(directory, recipe, fill=f) for f in fills]`; an estimation is the same expression inside its criterion function.
