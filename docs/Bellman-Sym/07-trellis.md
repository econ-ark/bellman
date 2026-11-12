---
title: Trellis Syntax
tags:
  - trellis
  - syntax-rules
status: Draft — rewritten 2 October 2026
related:
  - "[[06-period]]"
  - "[[08-periods-and-trellis]]"
  - "[[08-bellman-factory]]"
  - "[[model-directory-layout]]"
date: 2026-10-02
audience: user
type: user-guide
topic: [factory, syntax]
---

# Trellis Syntax

<!-- tags: backus-functionals, function-composition -->
#trellis

> [!summary]
> A **trellis** is the sequence of a model's periods, counted backward from the terminal period, together with the connectors that join each period to the one after it in time. Three files describe it in the route a recipe reads, and the first two suffice when the periods carry their own records (§3). The trellis file lists the periods and the connectors between them; the period file is the template of one period, which the trellis file repeats; and the recipe names the trellis file and, for every stage key those two files use, the stage's file and the files of its parameter values, settings and methods, each by a path written from the recipe's own folder. This page explains how a trellis is loaded as it is written: what each file holds and what it leaves to the others, how periods are written out or repeated, where the files' paths are read from, and how the same trellis is built in Python one period at a time with no file at all. What a recipe does with the files it names, the order of its sources and the values supplied at the call, is the subject of the page that follows.

> [!info]- Relationship with other documents
> **Builds on** — [Periods](06-period.md): stage occurrences, connectors and the order of a period from its fields.
> **Used by** — [The Bellman factory](08-bellman-factory.md): the recipe route in full, from these files to a trellis whose every stage holds its values, methods and settings; [Recipe functions](API/factory/spec-factory.md) and [The trellis factory](API/factory/trellis-factory.md): the calls that read the files and what they return.
> **See also** — [Model directory layout](reference/model-directory-layout.md): where the files of a model stand.
> **Formal account** — [Periods and the trellis](../bellman-calculus/08-periods-and-trellis.md): composition and boundary data.

> [!note]- Key terminology
> | Term | Meaning |
> |---|---|
> | **Trellis** | The sequence of a model's periods, `periods[0]` the terminal one, with the connectors between adjacent periods ([wiki](../wiki/trellis.md)). |
> | **Trellis file** | `trellis.yml`: the periods, each written out or given as a template repeated, and the inter-period connectors (§§1, 4). |
> | **Period file** | `period.yml`: the template of one period, its stages and its connectors, which the trellis file names under `template:` ([Periods](06-period.md); [wiki](../wiki/period.md)). |
> | **Recipe** | `spec.yml`: the trellis file under `trellis:` and, for each stage key, the stage's file and the files of its values, settings and methods, each by a path written from the recipe's folder; the file of the **specification factory**, the part of the Bellman factory that merges the sources a recipe names, which the next page explains ([The Bellman factory](08-bellman-factory.md); [wiki](../wiki/spec_factory.md)). |
> | **Stage key** | The name an author gives one use of a stage in a period, `tenure`; the recipe says which file it names. |
> | **Stage occurrence** | One use of a stage file at one position of one period, an object of its own ([Periods](06-period.md) §1). |
> | **Record** | The entry at one stage key of the syntactic trellis: the stage's text and origin and its three mappings, held as data ([The factory API](API/factory/index.md) §2). |
> | **Syntactic trellis** | The model as written, the dictionary of records that `bellman.trellis.load_trellis` and `bellman.trellis.load_recipe` return ([wiki](../wiki/trellis.md)). |
> | **Inter-period connector** | The mapping `inter_connectors[h]` from the continuation fields that leave `periods[h + 1]` to the arrival fields of `periods[h]` ([wiki](../wiki/connector.md)). |

## 1 The three files

The preceding pages wrote one stage, and then one period. A model with a horizon uses several stages at many dates, and the durables model of the repository, `applications/durables/`, the housing model of Dobrescu and Shanker (2026) in which a household keeps or adjusts its housing stock at each of fifty-one ages, is the example of this page: four stage files, for the tenure choice, the keeper's consumption, the adjuster's consumption and the bequest, and three files that say how the stages are used. Each of the three answers one question, and none answers another's.

The **trellis file**, `trellis.yml`, composes. It lists the periods of the model, the terminal period first, and the connectors that join each period to the one after it in time. The durables file, with its comment lines left out:

```yaml
!trellis
name: durables_life_cycle
periods:
  - stages: [tenure, keeper_cons, adjuster_cons, bequest]
    connectors:
      - {a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}
      - {w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}
  - {template: period.yml, repeat: 50}
inter_connectors:
  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}
```

Its first entry writes the terminal period out, because that period alone holds the bequest and the connector that carries the savings, the housing and the income state of both consumption stages onto the bequest's arrival fields, and the template's connector after it, which joins the tenure stage's branches to the consumption stages; its second entry gives the fifty earlier periods as one template repeated. The one mapping under `inter_connectors` stands for every adjacent pair, and joins the continuation fields of both consumption stages to the arrival fields `a`, `h` and `z` of the next period's tenure stage.

The **period file**, `period.yml`, is a template: one period, written once and repeated by the trellis file under `template:`. It lists the keys of the stages the period holds and the connectors within the period. The order of its list carries no meaning, since the order of the stages is derived from their fields ([Periods](06-period.md) §3). Its one connector joins the fields each branch of the tenure stage ends at to the decision states of the consumption stage the branch enters, each consumption stage beginning at its decision perch; `z_d`, which both consumption stages read, is written with its stage key:

```yaml
!period
name: durables_period
stages:
  - tenure
  - keeper_cons
  - adjuster_cons
connectors:
  - {w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}
```

The **recipe**, `spec.yml`, names the files. At its top it names the trellis file under `trellis:`, and for each stage key the two files above use it names the stage's file under `stage:` and the files whose values the stage receives, each by a path written from the recipe's own folder. What the recipe does with those files, the order of its lists, the entries written `$fill`, the `registry` block and the bequest's `periods: [0, 0]`, is the subject of [The Bellman factory](08-bellman-factory.md) §3; on this page the recipe is read for what it names. The durables recipe, with its comment lines left out:

```yaml
trellis: trellis.yml
stages:
  tenure:        {stage: stages/tenure/tenure.bl,               calibration: {all: [calibration/durables, $fill]}, settings: {all: [settings/durables, $fill]}, methods: {all: [stages/tenure/methods.bl]}}
  keeper_cons:   {stage: stages/keeper_cons/keeper_cons.bl,     calibration: {all: [calibration/durables, $fill]}, settings: {all: [settings/durables, $fill]}, methods: {all: [stages/keeper_cons/methods.bl]}}
  adjuster_cons: {stage: stages/adjuster_cons/adjuster_cons.bl, calibration: {all: [calibration/durables, $fill]}, settings: {all: [settings/durables, $fill]}, methods: {all: [stages/adjuster_cons/methods.bl]}}
  bequest:       {stage: stages/bequest/bequest.bl,             calibration: {all: [calibration/durables, $fill]}, methods: {all: [stages/bequest/methods.bl]}, periods: [0, 0]}
registry:
  calibration: [calibration/wage_schedule]
```

The division of labor is strict. The trellis file and the period file hold stage keys, connectors and inter-period connectors, and the trellis file the path of the period file it repeats, under `template:`; they hold no value, no method, no setting and no stage file. Reading them tells the package which stages occur where and how their fields are joined, and tells it nothing about what any stage receives. A stage key is a name the author chooses; which file it names, and which files that stage is bound from, the recipe says, and the recipe in turn writes no connector and determines the sequence of periods only through the trellis file it names at its top. The recipe is the file of the **specification factory**, the part of the Bellman factory that merges the sources a recipe names, which the next page explains ([wiki](../wiki/spec_factory.md)). The call `bellman.trellis.load_recipe("applications/durables/declaration", "spec.yml")` reads the three files and returns the syntactic trellis, one record per stage and period (§6). A recipe cannot make a trellis on its own: without the trellis file it names there is no list of periods to write records for.

### 1.1 Periods counted backward

The `periods` list is read with the terminal period first. `periods[0]` is the terminal period, the last in time, and `periods[h]` lies `h` periods before it, so that the durables trellis has fifty-one entries, `periods[0]` being age 70 and `periods[50]` age 20. The index `h` is the number of periods before the last, not an age and not a calendar date. A stage file carries no index: the same file is used at every position where its key appears, and each use is a separate stage occurrence with its own bindings ([Periods](06-period.md) §5).

The trellis is counted this way because it is built this way. Backward induction values a period from the value of the period after it, so the terminal period is the first the package needs and the first it appends: the readers of the files write the records in this order, and the calls that construct a trellis append its periods in this order, the terminal period first (§6). Counting from the terminal period, an earlier period appended changes no index already present. The terminal period keeps the index 0 whatever the horizon, so that whatever a file writes for it means the same in a model of three periods as in one of fifty-one, and the horizon is the number of periods the trellis file lists, and nothing else sets it.

| Entry | Economic time | Backward computation |
|---|---|---|
| `periods[0]` | The terminal period. | Uses the supplied terminal continuation data (§2). |
| `periods[1]` | One period before the terminal one. | Uses the result for `periods[0]`. |
| `periods[h + 1]` | One period before `periods[h]`. | Uses the result for `periods[h]`. |

## 2 Inter-period connectors

`inter_connectors[h]` pairs continuation state fields that leave `periods[h + 1]` with arrival state fields of `periods[h]`; the mapping is written in the forward economic direction, from the earlier period to the later one, even though value computation proceeds from `periods[0]` to `periods[1]`. The list holds one mapping for each adjacent pair, so that its length is one less than the number of periods. In a trellis file, a list of one mapping stands for every pair, as the durables file writes it, and an absent or empty list stands for empty mappings, periods not joined to one another; the readers expand the list, so the trellis they return holds one mapping per adjacent pair. Each repeated mapping is resolved against its own period pair: an endpoint unique in one pair can be ambiguous in another. A trellis written in Python (§6) holds that many mappings itself, and any other length, in a file or in Python, is refused with the number of mappings to write.

As [within a period](06-period.md#2-connectors), a connector selects two stage-local fields and performs no interest, discounting, or unit conversion. A bare endpoint name must identify exactly one eligible use on its side of the period pair; prefix an ambiguous name with its stage key. The joined fields must be continuation fields that leave the earlier period in time, those that no join within that period reads. An arrival field may take several sources, within its period and from the period before, and its arrival measure, the distribution of the agents who arrive there, is the sum of the incoming measures: the retirement model's `a_ret` takes the workers who retire and the retirees of the period before. An empty mapping supplies no authored pair; it does not repair missing or incompatible boundary data.

The two period definitions of the preceding page leave different fields at their boundaries:

| Period definition | Within-period pair | Inter-period pair | Terminal continuation domain |
|---|---|---|---|
| Consumption, discounting, investment | `{k_next: k}` | `{m_next: m}` | Positive resources, $(0,\infty)$. |
| Investment, consumption, discounting | `{m_next: m}` | `{k_next: k}` | Nonnegative capital, $[0,\infty)$. |

For the first definition, `port.m_next` of period `h+1` supplies `cons.m` of period `h`. For the second, `disc.k_next` supplies `port.k`. Each pairing requires [compatible declared sets](06-period.md#2-connectors), the outgoing field's set contained in the incoming field's, and the author's economic justification for the quantity, units and information. Use the matching within-period and inter-period choices together; reversing a stage list does not move a boundary.

The **terminal continuation value** is the value function that a stage of the terminal period reads after its decisions. Keep its input explicit: declare `V[>]` in the backward block's input header, including when the terminal payoff is given in closed form. You supply the function on the declared continuation-state domain. It may be identically zero, as in the durables model's bequest stage, but death, exit or the end of the horizon does not set it to zero automatically. A zero value does not require removing the continuation-state fields.

Supply this function as terminal data when the model is realized; no entry of `inter_connectors` is reserved for it. For the value-only stage files of the preceding page, use the domain in the table and the analytic conditions in [Periods](06-period.md#31-choosing-the-period-boundary). A constant zero terminal value is admissible for those equations. Terminal data for a continuation given in closed form must also carry the derivatives that the blocks of the stage reading it name by their terms, `D_{a}V[>]`, agreeing with the supplied value function (§2.1). The join rule above prescribes no representation for terminal data.

In a retirement model, a connector for one adjacent period pair must contain both routes when both are needed: working continuation fields connect to the next working or choice stage, and retired continuation fields connect to the next retired stage. Writing the two routes as separate entries of `inter_connectors` would assign them to different period joins. Retirement is absorbing only if the retired route continues to exclude a return to working stages.

### 2.1 The derivative a method reads

The lines of a solution method, such as the lines of [`!egm`](reference/methods.md#egm) that a methods file writes in its block `policy`, may read the derivative of the stage's continuation value by the term `D_{a}V[>]` ([Field equations](03-field-equations.md) §2). The lines declare that reading and nothing else: how the derivative is evaluated is a property of the value, fixed by the stage that supplies the continuation, the stage whose exported value a connector joins to this stage's continuation fields ([Methodization](04-methodization.md) §5). That stage's value carries the derivative when its methods file fixed one, in one of two ways. The first is a derivative line, in its stage file or in its methods file, the addition unioned with it, whose values the representation at the value builder's [Evaluation](reference/operations.md#evaluation) stores; the methods file types that representation at the builder's Evaluation, `cntn_to_dcsn.evaluate.method : !Linear`. The second is a representation of the value whose row of the method table evaluates the derivative. A derivative line stated at the decision builder serves the arrival value through an arrival builder whose law between the perches is the identity, `V[<] = V` or `V[<] = E_{y}V`, where the stored derivative values pass through. Where that stage's derivative line in turn reads the derivative of the stage after it, as the portfolio stage's line reads `D_{m_next}V[>]` under its expectation, the requirement passes to that stage, and so on up to a stage whose continuation is given in closed form, such as the terminal continuation, whose derivatives are supplied with the terminal data (§2). The join of two stages compares value fields alone, and a connector selects values alone.

A reading that no route meets is reported, not refused: the trellis is built and bound, and the route that needs the derivative is left uncertified. `bellman.trellis.derivative_missing(trellis)` answers one `derivative-missing` diagnostic for each such reading, addressed to the stage occurrence whose value carries no derivative in the coordinate read, such as `periods[0].stages['port']`; its sentence names that stage, the value and the coordinate, as the reading block's term writes them, `D_{m_next}V[>]`, and the ways the stage's methods file may fix the derivative. When every value carries the derivatives its neighbors read, the query answers an empty tuple.

## 3 The two shapes of a period

A period's `stages:` takes one of two shapes, and the shape decides which call reads the file and where the bindings come from.

Written as a **list of keys**, `stages: [tenure, keeper_cons, adjuster_cons]`, a period names its stages and binds nothing. This is the shape of the durables files of §1 and of every period a recipe reads: `bellman.trellis.load_recipe(directory, "spec.yml")` reads the trellis file through the recipe, which supplies for each key the stage's file and its three mappings. Without a recipe a list of keys cannot be read, since nothing says which file a key names; and under a recipe a period of records is refused, the refusal saying that under a recipe a period template lists its stage keys and the recipe supplies their mappings.

Written as a **mapping from each key to a record**, a period carries its own bindings and needs no recipe. Each record names the stage's file under `stage:`, which is required, gives its calibration and its settings, each either inline as a mapping or as the path of a file, and names its methods as the path of one methods file, a `.bl` addition beside the stage file, or as a list of such paths, read in the order written and unioned with the stage file in that order; each of the three is optional and empty when left out; every path is read relative to the trellis file's own folder, and a `label` may name the occurrence. `bellman.trellis.load_trellis(file)` reads such a file. The terminal period of the durables model and one period before it, written in this shape and read by that call:

```yaml
!trellis
name: durables_records
periods:
  - stages:
      tenure:        {stage: stages/tenure/tenure.bl, calibration: calibration/durables.yml, settings: settings/durables.yml, methods: stages/tenure/methods.bl}
      keeper_cons:   {stage: stages/keeper_cons/keeper_cons.bl, calibration: calibration/durables.yml, settings: settings/durables.yml, methods: stages/keeper_cons/methods.bl}
      adjuster_cons: {stage: stages/adjuster_cons/adjuster_cons.bl, calibration: calibration/durables.yml, settings: settings/durables.yml, methods: stages/adjuster_cons/methods.bl}
      bequest:       {stage: stages/bequest/bequest.bl, calibration: calibration/durables.yml, methods: stages/bequest/methods.bl}
    connectors:
      - {a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}
      - {w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}
  - stages:
      tenure:        {stage: stages/tenure/tenure.bl, calibration: calibration/durables.yml, settings: settings/durables.yml, methods: stages/tenure/methods.bl}
      keeper_cons:   {stage: stages/keeper_cons/keeper_cons.bl, calibration: calibration/durables.yml, settings: settings/durables.yml, methods: stages/keeper_cons/methods.bl}
      adjuster_cons: {stage: stages/adjuster_cons/adjuster_cons.bl, calibration: calibration/durables.yml, settings: settings/durables.yml, methods: stages/adjuster_cons/methods.bl}
    connectors:
      - {w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}
inter_connectors:
  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}
```

The bequest's record names a calibration file and a methods file and no settings, so its settings are empty. A mapping written inline, `settings: {n_a: 200}`, stands where a path does. A record's methods are never written inline: `methods:` names a `.bl` file, the addition beside the stage file, or a list of additions applied in the order written, a structural addition followed by the addition that types the methods of the stage it enlarges, `methods: [additions/pension.bl, additions/egm.bl]`. A record that gives one stage file different methods at different periods names a replacing selection in place of the first in the other period's record, `methods: stages/cons/methods.vfi.bl` where the first period's record names `stages/cons/methods.bl`. A record holds one source of each kind and nothing more, so that a value which differs by period is written in this route directly, each period's records naming their own files; what a recipe writes instead is the subject of [The Bellman factory](08-bellman-factory.md) §3. The trellis files of records of `applications/cons-port/declaration/`, `trellis.port-cons-vfi.yml` and the five `trellis.reference-<name>.yml` of its fixed reference, are written in this shape, each `stage:` path naming a stage file of the folder's own `stages/`.

In this route the tenure record of each period gives a calibration, a file or an inline mapping, that holds that period's income `Y` and retirement income `y_R` beside the common values, since these vary with age and a record merges nothing; the fragment above names the common file in both periods, so `bellman.trellis.load_trellis` reads it and `bellman.trellis.elaborate_trellis` constructs it, but `bellman.trellis.calibrate_trellis` refuses it at `Y`.

The two shapes are told apart by the shape alone, a list or a mapping, and are not mixed: a file that writes one period as keys and another as records is refused by both calls, each naming the shape it reads. A stage entry of the second shape is a key with a record, never a key with a bare list of files. Either shape may stand in a period written out in the trellis file or in a period file named under `template:`, and whichever shape a model uses, the two calls return the same kind of dictionary, the syntactic trellis of §6, which the same calls then elaborate and bind.

## 4 Periods written out and repeated

The `periods` list is written entry by entry, and an entry is either a period written out or a template repeated.

A period **written out** is a mapping with `stages` and `connectors`, and a trellis file may write every period this way, one entry per period from the terminal period backward, with one inter-period mapping for each adjacent pair. The durables model with three periods, written out:

```yaml
!trellis
name: durables_three_periods
periods:
  - stages: [tenure, keeper_cons, adjuster_cons, bequest]
    connectors:
      - {a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}
      - {w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}
  - stages: [tenure, keeper_cons, adjuster_cons]
    connectors:
      - {w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}
  - stages: [tenure, keeper_cons, adjuster_cons]
    connectors:
      - {w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}
inter_connectors:
  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}
  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}
```

Read through the durables recipe, this file gives three periods and two inter-period connectors, and since the two mappings are equal the list may be written as one mapping standing for both pairs.

A period **repeated** is the entry `{template: <period file>, repeat: n}`: the period file, read relative to the trellis file's folder, is expanded to `n` equal periods, `n` a positive integer and one when `repeat` is left out. A period written out may carry `repeat` as well, as every trellis file of the cons-port application does.

The two kinds of entry stand in one list, which is how the periods that differ are written out and the rest repeated. The durables file of §1 writes the terminal period out and repeats the template fifty times; a first period of life that differed from the others would be a third entry, written out after the template's. A template entry may also change what the template says, since the entry's own keys stand over the file's: an entry `{template: period.yml, repeat: 2, connectors: [...]}` repeats the template with the connectors it writes in place of the file's. Whatever the entries, the readers expand them, so the trellis they return holds one entry per period and one mapping per adjacent pair, and `periods[h]` is read as §1 counts it.

## 5 The recipe's paths and variants side by side

A recipe names every file it reads by a path relative to its own folder, and it assumes nothing from a name or a layout. At its top, `trellis: trellis.yml` names the trellis file; in each stage entry, `stage: stages/tenure/tenure.bl` names the stage's file; and in the lists of files a stage receives, `calibration/durables` names a calibration file without its extension, `.yml` or `.yaml`, and `stages/tenure/methods.bl` a methods file with it, the addition beside the stage file ([Methodization](04-methodization.md) §6). Both `trellis:` and `stage:` are required. A recipe without the first, or an entry without the second, is refused with the sentence that shows what to write ([Refusals](reference/refusals.md)), and no file is found from a stage key's spelling. The recipe's folder, the one the first argument of `bellman.trellis.load_recipe(directory, "spec.yml")` names, is therefore the one place every path of the recipe is read from, and how that folder is arranged is a convention of the model, not a rule of the reader ([Model directory layout](reference/model-directory-layout.md)).

The trellis file resolves its own names the same way, relative to its own folder: the period file under `template:` and, in the records route, every `stage:` and every path of a record (§3). A trellis file beside its recipe therefore reads the same `stages/` folder, and the cons-port files reach stage files two folders up with `../../portfolio-choice/declaration/stages/port/port.bl`.

A second route through the same stages, a **variant**, is written as a second set of the three files beside the first and nothing else: `spec.<name>.yml`, `trellis.<name>.yml` and `period.<name>.yml`, the name between the dots chosen by the author. The variant recipe names its trellis file under `trellis:`, that file names its template under `template:`, and both share the stage files and the source files of the folder, so that the suffix is for the eye alone, every link between the three files being written in the files. The durables folder keeps its route without the tenure stage this way, as `spec.two-stages.yml`, `trellis.two-stages.yml` and `period.two-stages.yml`, and `bellman.trellis.load_recipe("applications/durables/declaration", "spec.two-stages.yml")` opens it. A variant that changes the values a stage receives and not the route needs no second set of files; how a recipe writes it is the subject of [The Bellman factory](08-bellman-factory.md) §3.

## 6 A trellis built in Python

Every route ends in the same dictionary, and the dictionary can be written without any file. A trellis is `{"periods": [...], "inter_connectors": [...]}`, each period `{"stages": {key: record}, "connectors": [...]}`, and a **record** is what `bellman.stage.load_stage(path)` returns: the stage's text and origin under `stage`, its calibration, settings and methods empty, and its provenance; the application completes the three mappings ([Periods](06-period.md) §4; [The factory API](API/factory/index.md) §2). A record may also be written from text, `{"stage": {"text": source_text, "origin": producer}, "calibration": {}, "settings": {}, "methods": {}}`, since elaboration reads no file; a path string in place of a record is refused.

`bellman.trellis.accrete(trellis, period, inter_connector=None)` appends one period, the one earlier in time, to a trellis that starts as `{"periods": [], "inter_connectors": []}`. The terminal period is appended first and takes no mapping; each earlier period is appended with the mapping that joins it to the period appended before it, which `accrete` writes at `inter_connectors[len(periods) - 2]`. The durables model with three periods, built this way from records and then elaborated, run from the repository root:

```python
from bellman.stage import load_stage
from bellman.trellis import accrete, elaborate_trellis

folder = "applications/durables/declaration"

def record(name):
    """The record of one durables stage file, its three mappings empty."""
    return load_stage(f"{folder}/stages/{name}/{name}.bl")

decisions = {"tenure": record("tenure"), "keeper_cons": record("keeper_cons"), "adjuster_cons": record("adjuster_cons")}
to_bequest = {"a_nxt_kp": "a_bq", "h_nxt_kp": "h_bq", "z_nxt_kp": "z_bq", "a_nxt_adj": "a_bq", "h_nxt_adj": "h_bq", "z_nxt_adj": "z_bq"}
to_tenure = {"a_nxt_kp": "a", "h_nxt_kp": "h", "z_nxt_kp": "z", "a_nxt_adj": "a", "h_nxt_adj": "h", "z_nxt_adj": "z"}

trellis = {"periods": [], "inter_connectors": []}
trellis = accrete(trellis, {"stages": {**decisions, "bequest": record("bequest")}, "connectors": [to_bequest]})
trellis = accrete(trellis, {"stages": decisions, "connectors": []}, to_tenure)
trellis = accrete(trellis, {"stages": decisions, "connectors": []}, to_tenure)
symbolic = elaborate_trellis(trellis)
for h, period in enumerate(symbolic["periods"]):
    print(f"periods[{h}]:", ", ".join(period["stages"]))
print(len(symbolic["inter_connectors"]), "inter-period connectors;", repr(symbolic["periods"][2]["stages"]["tenure"]))
```

```text
periods[0]: tenure, keeper_cons, adjuster_cons, bequest
periods[1]: tenure, keeper_cons, adjuster_cons
periods[2]: tenure, keeper_cons, adjuster_cons
2 inter-period connectors; ElaboratedStage('tenure', symbolic)
```

The same records are given to all three periods, and elaboration still constructs a separate stage occurrence at each position, each carrying its position in its provenance, since `accrete` copies what it appends and the elaborator places a full copy of each stage at each of its positions. `bellman.trellis.elaborate_trellis` constructs each distinct stage text once, selects the connections of each period and checks each inter-period mapping, retaining representable connection problems on the returned model for inspection through the [connection report](API/factory/trellis-factory.md#9-inspect-the-selected-connections); it binds nothing, so the calibration, settings and methods stand in the records as data. `bellman.trellis.calibrate_trellis`, `bellman.trellis.methodize_trellis` and `bellman.trellis.configure_trellis`, each given the elaborated trellis and the dictionary of records, then bind the three mappings in that order, and the four results, the symbolic trellis and the trellis after each verb, are the four stopping points of the construction ([The trellis factory](API/factory/trellis-factory.md) §§3, 4). A period whose stages are already elaborated, each by `bellman.stage.elaborate_stage(bellman.stage.load_stage(path))` and bound by the stage's own verbs, is appended in the same way and its joins are derived at once; a trellis verb later copies such a stage occurrence as it stands ([Period functions](API/factory/period-factory.md) §3). A bare period is not elaborated on its own: it is placed in a trellis first, by `accrete` or as `{"periods": [period], "inter_connectors": []}` ([Periods](06-period.md) §4).

The syntactic trellis that `bellman.trellis.load_recipe` or `bellman.trellis.load_trellis` returns from the files of §§1 and 3 is a dictionary of this same form, and the same four calls elaborate and bind it; `bellman.trellis.assemble_trellis("applications/durables/declaration", "spec.yml")` runs the whole route in one call ([The Bellman factory](08-bellman-factory.md) §2). The result of every call is a dictionary of `periods` and `inter_connectors`, beside which a reader writes the provenance of the files it read and `bellman.trellis.load_recipe` the recipe's registry-level names ([The Bellman factory](08-bellman-factory.md) §3.5), the later calls copying both; no graph is stored: the joins are derived from the fields when the trellis is elaborated, and `bellman.trellis.diagram_trellis(trellis)` draws the periods with their inter-period connectors on request ([The trellis factory](API/factory/trellis-factory.md) §6).
