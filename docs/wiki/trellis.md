---
title: Trellis
slug: trellis
description: A finite sequence of period occurrences with inter-period connections.
wiki_status: canonical
last_reviewed: '2026-10-02'
reviewed_by: Claude (Fable); checked against the loaders and the trellis operations of packages/bellman/bellman/factory
sources:
- docs/Bellman-Sym/07-trellis.md
- docs/bellman-calculus/08-periods-and-trellis.md
- packages/bellman/bellman/factory/loading.py
- packages/bellman/bellman/factory/recipe.py
- packages/bellman/bellman/factory/trellis.py
tags: []
audience: user
type: concept
---

# Trellis

A **trellis** is a finite ordered collection of [[period|period occurrences]] and their inter-period [[connector|connections]]. It records uses of [[stage|stage files]] across dates. It is not a grid of individual state points and does not by itself assert one stored semgraph (semantic graph) for the entire horizon.

## Index and boundary data

The index $h$ counts backwards from terminal: `periods[0]` is terminal and `periods[h+1]` is one period earlier than `periods[h]`. An [[connector|inter-period connector]] indexed by $h$ joins the earlier period's continuation to the later period's arrival. Backward calculation uses terminal continuation data first, then proceeds to increasing $h$. The trellis is counted this way because it is built this way, the terminal period appended first and each earlier period after it, so that appending a period changes no index already present and the horizon is the number of periods built.

Terminal continuation data must match the terminal stage's declared inputs and domains. Calling an entry terminal does not automatically supply zero value, a terminal policy, or compatible derivatives. An infinite-horizon fixed-point condition is a different boundary problem.

## The three files and the two routes

A trellis is written in files or in Python. The **trellis file** lists the periods, the terminal period first, each written out or given as a period template repeated, together with the inter-period connectors; the **period file** is the template of one period; and the **recipe**, `spec.yml`, names for each stage key the stage's file and the ordered sources of its [[calibration]], [[settings]] and methods, every path relative to the recipe's own folder. The recipe is the file of the [[wiki/spec_factory|specification factory]].

The shape of a period's `stages` decides the route. Written as a list of keys, a period binds nothing, and `load_recipe(directory, "spec.yml")` reads the trellis file through the recipe, which supplies each key's file and mappings. Written as a mapping from each key to a record that names the stage file under `stage` and its three mappings inline or as paths, a period carries its bindings, and `load_trellis(file)` reads it with no recipe. The two shapes are not mixed in one file. A variant route is a second set of the three files beside the first, `spec.<name>.yml`, `trellis.<name>.yml` and `period.<name>.yml`. Without any file, `accrete` appends one period at a time to `{"periods": [], "inter_connectors": []}`, the terminal period first. [The trellis guide](../Bellman-Sym/07-trellis.md) §§1, 3, 5 and 6 state the three files, the two shapes, the paths and the Python route; what a recipe does with the files it names is [the factory guide](../Bellman-Sym/08-bellman-factory.md) §3.

## Reusing stage files

The same stage file may be parsed once and used for several [[stage|stage occurrences]]. Each stage occurrence receives its own semgraph, methods, and [[settings]]. Stages in one period share a parameter when they declare it under the same name; the same name in another period denotes another parameter. A value that differs by period is written in the recipe, as [the factory guide](../Bellman-Sym/08-bellman-factory.md) §3 states, or into the records by the application. The stage file itself need not encode a calendar date.

## The syntactic and the elaborated trellis

The **syntactic trellis** is the model as written: the dictionary `{"periods": [{"stages": {key: record}, "connectors": [...]}], "inter_connectors": [...]}`, each record holding the stage's source and its three mappings, [[calibration]], settings and methods, as data. `load_trellis(file)` and `load_recipe(directory, recipe, **fills)` return it, and every adjustment to a model, a fill of a [[wiki/spec_factory|recipe]]'s slot, a value that differs by period or a replacing selection, another methods file named in a stage's methods list, is made in it before elaboration and binding. The **elaborated trellis** is the same dictionary with an [[elaborated_stage|elaborated stage]] at every key: `elaborate_trellis(syntactic)` returns it symbolic, and `calibrate_trellis`, `methodize_trellis` and `configure_trellis`, each given the syntactic trellis as its second argument, return it specified. Neither dictionary holds a graph; the only graphs are the [[semgraph|semgraphs]] inside the stages.

[The trellis guide](../Bellman-Sym/07-trellis.md) shows the files, the records and the construction sequence. [[ordering_conventions|Ordering conventions]] distinguishes this backward index from forward economic time and ordinary function-composition order.
