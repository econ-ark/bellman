---
slug: spec_factory
title: Specification factory
tags:
- source
- factory
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/Bellman-Sym/API/factory/spec-factory.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/08-bellman-factory.md
  class: canonical
  date: '2026-09-07'
merged_from:
- slot
audience: user
type: concept
---

# Specification factory

The specification factory merges parameter, numerical-setting and method sources according to an ordered YAML **recipe**, `spec.yml`. A recipe names every file it reads by its path from its own folder, the **registry** directory: the [[trellis]] file under `trellis:`, each [[stage]]'s file under `stage:` in the stage's entry, and the sources of its source lists; nothing is read in place of a path it does not write. In a model folder of the repository the registry is the subfolder `declaration/`, which holds every file the language reads, each stage's files in a folder of their own, so that `load_recipe("applications/durables/declaration", "spec.yml")` reads the durables model ([Model directory layout](../Bellman-Sym/reference/model-directory-layout.md)). `load_recipe(directory, recipe, **fills)` reads the recipe and the registry and returns the [[trellis|syntactic trellis]]; it constructs no [[stage]] and no [[semgraph]] (semantic graph), and reads the [[stage|stage files]]' declarations only to check the names a fill gives.

Each recipe stage names its stage file and supplies `all` **source lists** for calibration, settings and methods. Resolution applies those sources in order, then any matching inclusive [[period]]-range overrides. Binding ranges do not themselves restrict stage activity; an optional stage `periods` interval does that separately. Ranges within one stage and binding kind must not overlap.

## Source composition

Mappings merge recursively, and later scalars and ordinary lists replace earlier values. A methods list is not merged: the `.bl` additions it names are unioned with the stage file in the order written, so that the whole list is the stage occurrence's selection. This preserves omitted bindings without asserting a general categorical or algebraic theorem about arbitrary merge inputs.

Source names are relative to the registry directory. A parent source is read before its child's entries; parent cycles are rejected and recursion is limited. These rules resolve data, leaving the checks of method places and of [[parameters|parameter]] and setting completeness to the stage operations. The current reference specifies path resolution and accepted wrappers in detail.

## Recipe slots

A **slot** is a named place in a recipe source list, such as `$fill`, whose value is supplied with the keyword `fill=` of `load_recipe`; the value is the **fill**, a mapping. A slot affects only the source lists in which it is named, so one fill can be reused at several addresses.

`load_recipe` is one step of the **Bellman factory**, the part of the package from the files to the specified trellis; a **sweep** is a family of fills, one expression over them, such as `[assemble_trellis(directory, recipe, fill=f) for f in fills]`, with `assemble_trellis` of `bellman.trellis`.

A flat mapping supplies entries directly. A mapping whose top-level keys are all among `calibration` and `settings` is interpreted by specification kind; a mixture with other keys is treated as flat. A methods list takes no slot: a change of methods is a replacing selection, another addition named in the list. The shape must match the recipe's intended use.

An unfilled slot contributes an empty mapping. A keyword naming no slot is refused with `FactoryError` under the rule `recipe-slot-unknown`. Extra keys inside a declared slot do not become model declarations. Slots are not the only source of user data: files and direct stage bindings are separate supported routes. A recipe slot is also distinct from an [[asdl|ASDL field]], an economic [[field]] or an operation's argument.

## The syntactic trellis the recipe defines

`syntactic["periods"][h]["stages"][key]["calibration"]`, and the settings and methods beside it, are the merged mappings of that stage at period `h`, `h` counting periods before the terminal one; the record holds bindings as data, not a stage, and no policy or solved stage. `elaborate_trellis` constructs the [[stage|stage occurrences]], one for each stage file at each position, from the records, and `calibrate_trellis`, `methodize_trellis` and `configure_trellis` bind them, completing the lifecycle of a [[specified_stage|specified stage]].

Source precedence first determines each stage's record. When stages in one
period declare the same [[parameters|parameter]] name, calibration then
reconciles those records and binds one period value to every declaring stage;
two disagreeing supplied values are refused. A value at the same name in a
different period remains independent. This sharing of parameters does not
identify the stages' [[field|fields]].

See [Recipe functions](../Bellman-Sym/API/factory/spec-factory.md) for the signatures, the merge, the slot shapes and the refusals, and [The Bellman factory](../Bellman-Sym/08-bellman-factory.md) for the route through the calls. [[calibration|Calibration]], [[settings]] and [[methodization]] define the three kinds of input.
