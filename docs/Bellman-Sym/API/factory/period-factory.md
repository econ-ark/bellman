---
title: Period functions
tags:
  - docs/api
audience: user
type: api
topic: [factory]
---

# Period functions

> [!summary]
> A [period](../../../wiki/period.md) is a dictionary, `{"stages": {key: record or stage}, "connectors": [...]}`. `accrete(trellis, period, inter_connector=None)` of `bellman.trellis` appends one to a [trellis](../../../wiki/trellis.md), `diagram_period(trellis, h)` of `bellman.period` draws one, and `period_joins(period)` with three further functions of `bellman.period` and `inter_period_joins` of `bellman.trellis` read its joins and the order of its stages. No call constructs one period on its own: `elaborate_trellis` of `bellman.trellis` constructs the stages of every period of a trellis, and the order of a period's stages is derived from their fields, never from the template's list.

> [!info]- Relationship with other documents
> **Builds on** — [Periods](../../06-period.md): the period template and the joins between stages; [Stage functions](stage-factory.md): the record and the stage.
> **See also** — [The trellis factory](trellis-factory.md): elaborating and binding every period of a trellis; [Trellis Syntax](../../07-trellis.md) §6: a trellis built by accretion on the durables model; [The Bellman factory](../../08-bellman-factory.md) §7: the order of a period.

## 1 A period with one stage

A period holds one record for each [stage occurrence](../stage/01-the-stage.md), under its key, and the **within-period connectors**, which identify continuation fields of one stage with arrival fields of another. This period holds the discounting stage alone and needs no connector. From the repository root, the period's one record is written from the stage file, the period is appended to an empty trellis as its terminal period, and the trellis is elaborated and bound:

```python
from bellman.stage import load_stage
from bellman.trellis import (accrete, calibrate_trellis, configure_trellis, elaborate_trellis,
                             methodize_trellis)

records = {
    "disc": {
        **load_stage("applications/portfolio-choice/declaration/stages/disc/disc.bl"),
        "methods": {"methods": [{"on": "cntn_to_dcsn"}]},
        "calibration": {"β": 0.96},
    }
}
trellis = accrete({"periods": [], "inter_connectors": []},
                  {"stages": records, "connectors": []})
elaborated = elaborate_trellis(trellis)
specified = configure_trellis(
    methodize_trellis(
        calibrate_trellis(elaborated, trellis), trellis), trellis)
disc = specified["periods"][0]["stages"]["disc"]
```

The `on`-only entry recognizes the discounting builder without selecting a numerical routine. The calls construct and bind one stage; they supply no terminal continuation value and solve nothing.

## 2 A period read from a file

A **period template** is the YAML file of one period, which lists its stage occurrences, as keys or as records, and its connectors. The template of the period of §1 reads:

```yaml
!period
name: discounting_period
stages: [disc]
connectors: []
```

No call reads a template on its own: a trellis file names it, `{template: period.yml, repeat: n}` for a run of `n` equal periods, and the call that reads the trellis file reads the template with it. `load_recipe(directory, recipe)` of `bellman.trellis` reads a template that lists stage keys, as this one does, and the recipe supplies each key's record; [Recipe functions](spec-factory.md) §1 builds the smallest [registry](../../../wiki/spec_factory.md) around this template. `load_trellis(file)`, also of `bellman.trellis`, reads a template whose `stages` maps each key to a record, which names its stage file and gives its three mappings ([The trellis factory](trellis-factory.md) §1). Either call returns a trellis whose periods have the form of §1. A key identifies a record and need not be the stage file's declared name; two uses of one stage file in a period take distinct keys.

## 3 accrete

```python
bellman.trellis.accrete(trellis, period, inter_connector=None)
```

The call returns a new trellis with `period` appended at the end of `periods`, the period earlier in time, and `inter_connector`, the mapping from the continuation fields that leave it to the arrival fields of the period appended before it, written at `inter_connectors[len(periods) - 2]`; `{}` is written when none is given. The terminal period, appended first, takes no mapping, so `len(inter_connectors)` is `len(periods) - 1`, and no entry is reserved for the boundary: the terminal value is the continuation value a stage of the terminal period reads. No existing record is rewritten. The period may hold records, stage objects or both; the appended period is copied, its stages by a full copy, so that no object of the caller's stands inside the trellis, and a stage object placed by hand receives its position in its provenance on the copy. A stage object placed by hand is later copied by a verb as it stands, bound or not, since the syntactic trellis holds no mapping to bind it with.

Where every stage of the appended period is an `ElaboratedStage`, the package selects the period's connections and checks the inter-period mapping. Unresolved names, incompatible pairs, repeated endpoint claims and cycles remain inspectable through the [connection report](trellis-factory.md#9-inspect-the-selected-connections). Construction preserves those authored entries without certifying them for computation. Invalid source structure still raises an error. A period holding records is checked when the trellis is elaborated. The trellis passed in may itself be `{"periods": [], "inter_connectors": []}`: a trellis is built backwards from an empty dictionary, and `elaborate_trellis` and the three trellis verbs are loops of this call ([The Bellman factory](../../08-bellman-factory.md) §3).

## 4 Stage order

Field dependencies determine the order of a period's stages, and the list order of the template carries no meaning. The joins are selected from authored connectors and the fields of the placed stages. An authored endpoint resolves to one continuation or arrival use, with a stage prefix where its bare name is ambiguous, and takes precedence over inference. Equal-name fields are inferred only where the package establishes a unique admissible connection; competing or cyclic inferred candidates remain unresolved. Several explicitly authored sources may reach one arrival field, with a separate complete-state route for each source branch. A continuation field that no selected join reads is an output of the period. The forward order, the backward order and the stages computable together follow from the joins; no graph is stored, and `diagram_period` of `bellman.period` draws the order on request (§5).

```python
bellman.period.period_joins(period)                          # {"joins": [...], "outputs": [...]}
bellman.period.computable_together(period)                   # the stage keys in layers
bellman.period.forward_order(period)                         # the stage keys in the order of computation
bellman.period.backward_order(period)                        # the stage keys in the reverse order
bellman.trellis.inter_period_joins(mapping, later, earlier)  # the joins an inter-period connector makes
```

Each function reads a period whose stages are elaborated, `specified["periods"][h]` for instance; a period that holds a record is refused under `record-shape`, since a record has no fields. `period_joins` returns the joins, each written `{"from": (key, field), "to": (key, field)}`, and the outputs, the continuation fields that no join reads. `computable_together` returns the stage keys in layers according to the selected dependencies; this is an ordering query, not a certificate that every connection and numerical method is valid; `forward_order` returns the keys layer by layer and `backward_order` the reverse, the order in which the backward operators are applied. `inter_period_joins(mapping, later, earlier)` returns the joins an inter-period connector makes from `later`, the period appended later and so earlier in time, to `earlier`, the period it joins.

The order queries refuse a cycle among authored joins under `period-join-cycle`, with the involved pairs named. The construction and connection report retain that cycle for inspection. Remove or redirect an authored arrow to establish an acyclic order. Local fields may retain the same spelling in different stages. The [connection report](trellis-factory.md#9-inspect-the-selected-connections) identifies unresolved endpoints and incompatible or incomplete routes; an unresolved arrow does not certify a complete composition.

Connections must join compatible fields with an unambiguous source and destination. Matching spellings alone do not establish compatible state domains or backward function components; [Periods](../../06-period.md#2-connectors) states these requirements. The order is separate from the [semgraph](../../../wiki/semgraph.md), the semantic graph, inside each stage and from the syntactic trellis, which holds the mappings as data; ordering stage occurrences does not reinterpret their equations or prove that their numerical methods are compatible.

## 5 diagram_period

```python
bellman.period.diagram_period(trellis, h)
```

The call returns a drawing of `trellis["periods"][h]`, of the kind a graph's `diagram()` returns, which a notebook displays: one box per stage, labeled by its key, with the stage's declared name in parentheses beneath where the two differ, standing in the forward order from left to right; one arrow per join, labeled by the field it carries, `field → arrival` for an authored connection; and one unlabeled arrow to a plain label for each continuation field that no stage of the period takes. `h` counts periods before the terminal one, `0` the terminal period. The period's stages must be elaborated, since the joins are read from their fields; the drawing is built from the dictionary when it is asked for and stored nowhere.
