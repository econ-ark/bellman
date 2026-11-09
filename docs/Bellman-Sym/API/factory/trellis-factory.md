---
title: The trellis factory
tags:
  - docs/api
audience: user
type: api
topic: [factory]
---

# The trellis factory

> [!summary]
> A [trellis](../../../wiki/trellis.md) is a dictionary, `{"periods": [...], "inter_connectors": [...]}`, its terminal period first. The functions of `bellman.trellis` act on it: `load_trellis(file)` reads one from a trellis file; `elaborate_trellis` constructs its stages; `calibrate_trellis`, `methodize_trellis` and `configure_trellis` bind them; `specify_trellis` constructs and binds them in one call; `respecify_trellis` binds again the stage occurrences whose records changed; `changed_positions` lists what a verb bound, a copy of a binding among them ([The Bellman factory](../../08-bellman-factory.md) §6); and `diagram_trellis` draws the periods with their [inter-period connectors](../../../wiki/connector.md).

> [!info]- Relationship with other documents
> **Builds on** — [Trellises](../../07-trellis.md): period indices and records; [Period functions](period-factory.md): accretion and the order of a period.
> **See also** — [Recipe functions](spec-factory.md): the syntactic trellis a registry gives; [The Bellman factory](../../08-bellman-factory.md) §5: what each call prints on the durables model.

## 1 The trellis file

A **trellis file**, `trellis.yml` by convention, lists the periods of a model. Its `periods` list writes a period out, its `stages` and its `connectors`, or gives `{template: <period file>, repeat: n}` for a run of `n` equal periods, and its `inter_connectors` list holds one mapping per adjacent pair or one mapping that stands for every pair. Two readers of `bellman.trellis` read the form. `load_trellis` reads a file whose stages are records: each names its stage file under `stage` and gives its three mappings inline or as paths to files, both relative to the file's directory, and a stage with no `methods` reads as the empty methods mapping. `load_recipe` reads a file whose stages are named by key, the recipe supplying each stage's source and mappings ([Recipe functions](spec-factory.md) §2). A file of the first kind, with a terminal period written out and two equal periods before it:

```yaml
periods:
  - stages:
      cons:
        stage: stages/cons/cons.bl
        calibration: calibration/ρ.yml
        settings: {n_m: 10, n_a: 10, a_min: 0.001, a_max: 10.0}
        methods:
          stage: cons
          methods:
            - on: policy
              method: !egm
              handler: cons-port:egm
              settings: {grid: !Cartesian, orders: {a: n_a}, bounds: {a: [a_min, a_max]}}
    connectors: []
  - {template: period.yml, repeat: 2}
inter_connectors:
  - {a: m}
```

Here `period.yml` writes the same record for `cons` without the methods, and the one mapping `{a: m}` stands for both adjacent pairs.

## 2 load_trellis

```python
bellman.trellis.load_trellis(file)
```

The call reads the trellis file at `file`, each period template it names and each stage file once, for its text and digest, and returns the [syntactic trellis](../../../wiki/trellis.md): `periods`, one record per stage and period with its three mappings and, under `provenance`, the origin and digest of the stage's text and the ordered sources of each mapping; `inter_connectors`, one mapping per adjacent pair; and, under the trellis's own `provenance`, the file's path and digest. A mapping given as a path is read from that file. A single standing mapping is read at `repeat: 1` as well, where it stands for no pair and `inter_connectors` is empty. A file without `periods`, or a record without `stage`, is refused under `trellis-file-shape`. Nothing is elaborated. The package writes no file of constructed stages: a trellis is rebuilt from its source records, whose provenance holds the path and digest of every source.

For a source editor, `bellman.trellis.read_trellis_file(file, texts=None)` expands the period templates and inter-period mappings without loading stage files or constructing stages. The returned period records retain the stage keys or records as written. `texts` may supply proposed file contents by resolved path; the result records the digests of those contents. This lets an editor check changed connectors against its existing stage occurrences.

## 3 elaborate_trellis

```python
bellman.trellis.elaborate_trellis(syntactic, previous=None)
```

The call returns the elaborated trellis, symbolic: the same dictionary with an `ElaboratedStage` at every key. It constructs each distinct stage text once per origin and places a full copy at each of its positions, each copy carrying its position in its provenance; copies a position that already holds a stage, the copy at its new position; and, given `previous`, copies from it every position whose record has the digest and origin of the stage held there and constructs the others, which is how a changed stage file alone is constructed again while the rest is kept. Every other key of the argument, `inter_connectors`, `registry`, `provenance` and an optional `solutions` list, is copied. The connections are selected from the fields and authored connectors, including mappings between periods. Missing or ambiguous endpoints, incompatible connections, repeated endpoint claims and cycles remain recorded as connection problems on the returned model. Read them with `connection_report` (§9). A returned object does not imply that every connection is valid or that the model can yet be computed. The call binds nothing; the calibration, settings and methods stand in the records and are read by the verbs.

The call keeps every check the elaborator makes: the shape of the trellis and of each record, and a supplied digest or location that disagrees with the source; a refusal names the affected stage occurrence. It writes into the provenance of each stage occurrence the `label` of its record, where the record has one, and, under `versions`, the version of the package and the digests of its grammar files, read once per call. It takes its own copies of each record's mappings, so a later change to the caller's dictionary alters no stage occurrence, and a source-shape, stage-construction or inconsistent period-parameter failure raises without returning a partial trellis. Connection diagnostics, by contrast, are available on the returned object (§9). It is built period by period by `accrete`, and it merges nothing: precedence is settled in the syntactic trellis before the call.

## 4 calibrate_trellis, methodize_trellis and configure_trellis

```python
bellman.trellis.calibrate_trellis(elaborated, syntactic)
bellman.trellis.methodize_trellis(elaborated, syntactic)
bellman.trellis.configure_trellis(elaborated, syntactic)
```

Each verb takes the elaborated trellis and the syntactic trellis it is to be bound with, and returns a new elaborated trellis. For each period `h` and key, it reads the mapping of its own kind, `syntactic["periods"][h]["stages"][key]["calibration"]` for `calibrate_trellis`, and applies the stage's own verb, `stage.calibrate`, `stage.methodize` or `stage.configure`, to the stage occurrence at the same key of the elaborated trellis where that mapping differs from what the stage occurrence holds: for calibration, in a value at a name the stage declares, compared by numeric equality; for settings, in any value; for methods, in the digest of the mapping against the one the stage occurrence's provenance records. The trellis verb applies the stage's verb once for each distinct stage occurrence and mapping and places a copy of the result, equal to what the stage's verb gives there, at the other positions of that pair ([The Bellman factory](../../08-bellman-factory.md) §6). A stage occurrence whose mapping is unchanged is copied, as is one at a key where the syntactic trellis itself holds a stage object, a period built by hand. The verbs are applied in the order calibrate, methodize, configure; `configure_trellis` is defined on methodized stage occurrences, since the settings are read against the methods that name them.

A parameter name that two or more stages of one period declare names one parameter of the period, shared by those stages, and the same spelling in another period is another parameter ([Periods](../../06-period.md) §5). The elaboration reconciles the declarations of such a parameter in each period: sets that are one set agree, and sets the package reads, a real set or an interval with numeric endpoints, agree in their intersection, so that `ℝ₊` in one stage and `ℝ₊₊` in another make the parameter's set `ℝ₊₊`; two sets whose intersection is empty, or is not one the package reads, are refused under `period-parameter-agreement`, with the period, the parameter, the stages and their declarations named, and no value establishes such an intersection. `calibrate_trellis` then supplies the parameter once for the period: the value the sources of the declaring stages give it, after the precedence among each stage's own sources, which the stages whose own sources do not supply it take as well; two sources that give it two values, and a value that lies outside the set a declaring stage writes, are refused under the same rule, with the period, the parameter, the stages and their sources named, and the refusal names the stage occurrence and the kind in its notes as a stage verb's refusal does. A stage occurrence placed by hand keeps its own calibration, which counts among the values the period's sources give.

Three properties hold of the verbs, on a trellis as on a stage. The sources are merged before a verb binds, so no verb resolves precedence, and a verb refuses a source that values fewer names than the stage requires. The last binding stands: calibrating a version twice gives the bindings of calibrating it once with the second source, its methods and settings kept, and the same for configuring; a version holds one methods binding, so `methodize_trellis` makes a stage occurrence whose methods changed anew from a fresh elaboration of its record, calibrated with the values it holds, methodized with the new mapping and configured with the settings it holds where it holds any. Binding changes no graph: the [semgraphs](../../../wiki/semgraph.md), the semantic graphs, of a bound version equal those of the symbolic one. [Appendix G](../../../bellman-calculus/APPX-G-FUNCTIONAL-PROGRAMMING.md) §7 states the three trellis verbs, with their mappings held fixed, as maps from stage versions to stage versions. A verb's refusals are the stage verb's: a calibration that values fewer names than the stage declares, a method whose tag is unknown or whose target does not resolve, a settings source that lacks a name an attached method reads.

### 4.1 specify_trellis

```python
bellman.trellis.specify_trellis(syntactic, previous=None, kinds=KINDS)
```

The call returns the trellis that `elaborate_trellis(syntactic, previous)` (§3) and then the verbs of `kinds` return. `kinds` names any of the three kinds of mapping a record holds, `"calibration"`, `"methods"` and `"settings"`, all three by default, as `KINDS` holds them; the verbs are applied in the order calibrate, methodize, configure, whatever order `kinds` writes, and a kind that is none of the three is refused with a `ValueError`. Each distinct stage text is constructed once, or taken from `previous` as `elaborate_trellis` takes it, and each stage occurrence is copied once, where the elaboration and each verb copy every occurrence. The call refuses what that route refuses, and a refusal of a binding names the stage occurrence and the kind in its notes, `Stage occurrence: <address>` and `Binding kind: <kind>`. `assemble_trellis(directory, recipe, **fills)` is `specify_trellis(load_recipe(directory, recipe, **fills))` ([Recipe functions](spec-factory.md) §4).

### 4.2 respecify_trellis

```python
bellman.trellis.respecify_trellis(specified, before, syntactic, kinds=KINDS)
```

The call returns the trellis that `specify_trellis(syntactic, kinds=kinds)` returns, where `specified` is the trellis that `specify_trellis(before, kinds=kinds)` returned for an earlier syntactic trellis `before`. A position whose record is the same in both syntactic trellises keeps the stage occurrence `specified` holds there; every other position is constructed, bound and copied as `specify_trellis` does it. A record holds its stage's text, its three mappings and the digest of each file read for them, so that a change of one stage's text, calibration, methods or settings binds that stage's occurrences again and no other, except that a changed value of a parameter the stage shares with other stages of its period (§4) binds those stages' occurrences in that period again as well, since the period supplies them the changed value. The two syntactic trellises must hold the same periods, the same stage keys and the same connectors; otherwise the call refuses under `trellis-file-shape`, and such a trellis is specified whole by `specify_trellis`. A trellis given with occurrences bound under other kinds than `kinds` is refused under `record-shape`.

## 5 changed_positions

```python
bellman.trellis.changed_positions(before, after)
```

The call returns the list of positions `(h, key)` whose stage occurrence in `after` is a new version of the one in `before`, or stands at a position `before` lacks. A verb writes the earlier version into the new one's provenance as its parent, a copy of a binding included, and a copy of an unchanged stage occurrence keeps its provenance equal, so the two provenances are compared; the length of the list is the count of what a verb bound, a copy of a binding among them, since it is a new version of its position ([The Bellman factory](../../08-bellman-factory.md) §6), and the count of stage occurrences less that length is what it copied unchanged.

## 6 diagram_trellis

```python
bellman.trellis.diagram_trellis(trellis, periods=None)
```

The call returns a drawing of the periods of an elaborated trellis, every one or those whose indices `periods` lists, of the kind a graph's `diagram()` returns. Each period is drawn as `diagram_period` draws it, inside a frame labeled `periods[h]` with `h` and, where the trellis's `registry` holds `last_age`, the age `last_age − h`; the drawing's `labels` name each stage `periods[h] <key>`, its period's address and its key. The terminal period stands at the right and the earlier periods to its left, so that economic time runs from left to right and the backward computation from right to left, the two directions written in the drawing's title. Every inter-period connector `inter_connectors[h]` whose two periods are drawn is drawn as [wires](../stage/02-initial.md) from the continuation fields that leave `periods[h + 1]` to the arrival fields of `periods[h]`, each wire labeled with the mapping's index and its field pair; a period with no mapping to its neighbor is drawn with no wire. The drawing is built from the dictionary when it is asked for and stored nowhere; the trellis is not itself a graph object. The same trellis is read interactively in Google's Model Explorer, where each period and each stage occurrence inside it is a box that opens with a click, and each join is drawn between the wires of the two occurrences it joins ([The view in Model Explorer](../stage/10-model-explorer.md) §5).

## 7 Period indices and the terminal value

The index `h` counts periods before the terminal one. `periods[0]` is the terminal period, `periods[h + 1]` lies one period before `periods[h]`, and `inter_connectors[h]` joins the continuation fields that leave `periods[h + 1]` to the arrival fields of `periods[h]`, so that backward computation proceeds from `h = 0` to larger `h`. The **terminal value** is the continuation value that a stage of the terminal period reads, for the durables model the bequest stage, whose continuation value is zero and is supplied as boundary data at realization; no entry of `inter_connectors` is reserved for it, and `len(inter_connectors)` is `len(periods) - 1`.

## 8 The entries of a model's files

```python
from bellman.trellis import (
    append_to_mapping,
    append_to_sequence,
    connector_entry,
    entry_span,
    entry_value,
    insert_in_sequence,
    period_entries,
    remove_from_mapping,
    remove_from_sequence,
    replace_entry,
    split_entry,
    written_at,
    written_spans,
)
```

These functions read and edit one entry of a recipe, a trellis file, a period file or a calibration, settings or methods file as text, or find the entry that writes a part of a trellis, so that a program edits a model without rewriting its files. An entry is named by its address, written as the factory's refusals write one, `stages.cons.methods.all[0]` or `periods[0].connectors[0]`. `entry_span(text, address)` answers the line and the column of the entry's value and those just after it, counted from one, the columns in code points; `entry_value(text, address)` answers the value as the package's reader of YAML files reads it, every tag kept, and refuses with a ValueError a text that does not read as YAML or that holds a value the reader cannot build, such as `!!bool abc`; and `replace_entry(text, address, written)` answers the text with that value's characters alone replaced by `written`, a string, a number, a boolean or a tag, so that the comments, the other entries and the layout stay as written. A string is written within the value's quotes where the value is written in single or double quotes, and otherwise plain, or in double quotes where the plain text would read as another type than a string; a number or a boolean is written plain as YAML writes it, `1.05`, `400` or `true`, and a tag, given as `entry_value` reads it, `{"__yaml_tag__": "pchip", "value": ""}`, plain as `!pchip`. The result is read back, and one in which the entry does not read as `written`, or another entry changed, is refused, as is a mapping or a list given as `written`. `append_to_mapping(text, address, key, value)` and `append_to_sequence(text, address, item)` answer the text with one entry, `key: value` or `item`, added at the end of the mapping or the list at `address`, on a line of its own after its last entry where the collection is written in block style and before its closing brace or bracket where it is written in flow style, every other character kept; the result is read back, and one in which the collection does not hold its former entries and then the new one is refused. `insert_in_sequence(text, address, index, item)` answers the text with `item` placed before the item at `index` of the list at `address`, on a line of its own just before that item's line where the list is written in block style and before the item, followed by a comma, where it is written in flow style, an `index` equal to the list's length appending `item`; the result is read back as an append's is. `split_entry(text, address, at)` answers the text with the entry at `address`, an item of a list that writes `repeat: n`, written twice in its place, the first time with `repeat: at` and the second with `repeat: n - at`, so that `{template: period.yml, repeat: 6}` split at 3 becomes two entries that each write `repeat: 3`; an entry that takes its repeat from the period file it names is refused, since the entry does not write the repeat. `remove_from_sequence(text, address, index)` and `remove_from_mapping(text, address, key)` answer the text with the item at `index` of the list at `address`, or the key `key` of the mapping there with its value, taken out, the lines of the entry going with the comment lines just above it where it is not the first, and a collection whose only entry goes written `[]` or `{}` in its place, so that `{a: k}` becomes `{}` and the list of inter-period mappings keeps its length; the result is read back, and one in which the collection does not hold its former entries but the one taken out is refused. `written_at(file, address)` moves an address of the trellis that `load_recipe` or `load_trellis` expands, `periods[5].connectors[0]`, to the file and the address that write it, here `period.yml` and `connectors[0]` where the trellis file's entry `{template: period.yml, repeat: 14}` writes the period. `period_entries(file)` answers, for each period of that expanded trellis, the file and the address of the entry that writes the period and every period that entry writes, reading the trellis file once. `connector_entry(trellis, writing, reading, texts=None, *, selection=None, replacing=())` answers where the connector from the continuation field `writing` to the arrival field `reading` of an elaborated trellis is written, each field given as `(h, key, field)`: a `ConnectorEntry` that names the file, the address, the periods the line reaches and the line itself, `{m_next: m}` in a period's `connectors` or `m_next: m` in an inter-period mapping, or, for two fields that no connector may join, the reason, with no exception raised: `not-adjacent` where the reading field stands neither in the writing field's period nor in the next period in time, `port-joined` where a join already reads the continuation field, since a continuation field joins one arrival field, `no-mapping` where the file writes no list or mapping to hold the line, and `name-shared` where no compact spelling, including qualified endpoints, resolves to the chosen pair at every period reached by the shared source. The writer tries bare names first, then qualifies only the endpoints that need their stage key. A key containing dots is separated from its field at the final dot. `selection` may reuse the selected result for this exact trellis version. To move an inferred arrow, `replacing` names its selected pair; its writing port becomes available to the replacement. An authored arrow must first be removed from its mapping. The writer checks source resolution; the caller checks compatibility of the complete proposed connection set before saving it. An arrival field that a join already reaches takes a further source, as an arrival field may take several ([Trellis](../../07-trellis.md) §2): the line is then a further key of the connector of the period that writes such a join, `{a_nxt_adj: a_bq}` added to `{a_nxt_kp: a_bq, …}`, where the connector is flat or names the two stages of the drag, and otherwise a line as for an arrival no join reaches, so that the number of mappings never changes. Bellman Workbench edits a recipe's entry through `replace_entry` when a file is chosen for a cell of its recipe table, and the entry of a calibration, settings or methods file when a parameter's value, a setting or a method's tag is written in its BellmanType panel ([Bellman Workbench](../../../overview/07-workbench.md) §2), adding through `append_to_mapping` the value of a parameter that no file writes and the method of an entry that names none; it adds a stage or a period to a model folder it wrote through `append_to_mapping` and `append_to_sequence`.


An existing connector key is preserved even when its destination is unresolved.
The writer tries an available qualified spelling; if the proposed entry would
replace an existing key, it returns `source-authored` and identifies that mapping.
Correct or remove the existing entry before asking to replace it.

## 9 Inspect the selected connections

```python
from bellman.trellis import connection_report, to_model_explorer

report = connection_report(trellis)
view = to_model_explorer(trellis, periods=(0, 1), selection=report.selection)
```

`connection_report(trellis, *, periods=None, stages=None, selection=None)` returns pairs of resolved field uses, complete-state routes, diagnostics, rejected automatic candidates, unjoined fields, effective bindings, operation counts, the selected result and the source file. A **route** is one source stage's ordered continuation state on a branch mapped to one destination stage's ordered arrival state. A certified route has established the state map, joint law and required backward value components; a visible pair alone does not establish those claims.

Each pair identifies both period indices, stage keys, local fields and perches, whether it was authored or inferred, and its compatibility judgment. An authored pair also records `source_address`, `source_key` and `source_value`: the expanded mapping address and exact written endpoints. `written_at(file, pair.source_address)` finds the physical mapping, including a shared period template. Inferred pairs have no authored source entry. The original `address` continues to name the connector group.

A period or stage restriction filters the report's pairs, routes, diagnostics, rejected candidates, unjoined fields and bindings. Its `selection` and `counts` still describe the complete trellis. Reuse `selection` only with the exact stage occurrences, connectors and effective bindings that produced it; a changed reading requires a new selection. The report, Model Explorer view and `unpaired_joins` can share that result, so changing a display restriction does not require another selection or stage construction.

### 9.1 Inspect an unfinished model

Ordinary construction returns an inspectable model when the stage declarations
can be constructed but their connections are incomplete or invalid. There is
no separate draft flag. Inspect the reasons before using a complete connection:

```python
report = connection_report(trellis)
print(report)
report.diagnostics
report.rejected
report.unjoined
```

`diagnostics` contains the rule, affected address and a specific reason. An
incompatible pair is different from one whose compatibility cannot be
established with the available declarations or values. `rejected` explains
why automatic candidates were not selected, including comparisons that require
an unavailable parameter value. A count of zero selected pairs must not hide
these reasons.

`unjoined` separates `internal` and `exterior` field uses; each contains
`writing` (continuation) and `reading` (arrival) entries. The exterior entries
are the earliest period's arrival uses and the terminal period's continuation
uses. An open field can be intentional while constructing a model. A field
with a selected pair can still have a type error, so read the diagnostics and
route status as well as this list. An operation that needs a certified route
refuses an uncertified one; ordering stages refuses a cyclic dependency.

A diagnostic's `source_entries` retains each authored origin as
`(address, source_key, source_value)`. Use `written_at(report.file, address)`
to find the physical source file and its local mapping address, then
`entry_span` on the current file text for its position. A shared period
source can concern several occurrences, and a route can cite several entries.
For several origins, `written_spans(report.file, addresses, texts=None)` returns
one `(path, EntrySpan)` or `None` per requested address, in the same order.
Include the source key in the address to locate that exact mapping entry.
The query reads period expansion once and composes each physical source once
for its spans; `texts` supplies current unsaved text by resolved path. A missing
or unreadable origin returns `None` without hiding other available origins.
An inferred candidate has no authored connector entry; its field occurrences
identify the declarations to inspect. Models built in memory without source
provenance still provide occurrence addresses, but no physical file is invented.
