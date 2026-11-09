---
title: The stage
tags:
  - docs/api
  - stage
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# The stage

> [!summary]
> `elaborate_stage` turns one [stage file](../../01-stage.md), a `.bl` file, into one Python object, the stage. This page states how a stage is made, the seven attributes it holds and the questions it answers about itself: its printed view, its contents, its [fields](../../../wiki/field.md), its conditions, its diagnostics and its encoding. Every listing is printed by the package from the consumption stage `applications/portfolio-choice/declaration/stages/cons/cons.bl`.

> [!info]- Relationship with other documents
> **Builds on** — [Stage tutorial](../../01-stage.md): the stage file line by line.
> **Used by** — [The initial diagrams](02-initial.md), [The builders graphs](03-build.md) and the pages after them: the pieces reached from the stage.
> **See also** — [API](../index.md): the functions that make a stage in §2.1 and every path of the stage in §2.4; [The factory API](../factory/index.md): the functions that load, elaborate and bind a trellis of stages.

Each python block on this page runs after the blocks above it, in one session started at the repository's root, and the text below a block is what that block prints.

## 1 Making a stage

A stage file holds declarations and [blocks](../../01-stage.md#3-builder-blocks). Each block lists the fields it reads and the fields it writes, and it denotes an operator: on value functions when it is read backward, on finite measures over the states when it is read forward. The consumption stage of the portfolio application, from which the listings of these pages are printed, is the running example. The household holds resources `m` at the arrival [perch](../../../wiki/perch.md); the block `arvl_to_dcsn` writes `m_d = m` at the decision perch, where consumption `c` is chosen, and the block `dcsn_to_cntn` writes savings `a = m_d - c`. The policy block states the choice by its maximization, the line `optimality`; the three lines of the endogenous grid method, `InvEuler`, `grid` and `identification`, stand in the methods file beside the stage file, `methods.bl`, which [A builder](04-builder.md) §2 reads one by one after methodization ([Methodization](../../04-methodization.md)). The block `cntn_to_dcsn` writes the value `V` and states its derivative in `m_d` by a derivative line, `D_{m_d}V = 𝑑𝑢(c)`. The line `InvEuler` of the methods file reads the derivative of the continuation value in `a` by the derivative term `D_{a}V[>]`; neither derivative is a field of a header. The file, as the repository holds it:

```python
from pathlib import Path

print(Path("applications/portfolio-choice/declaration/stages/cons/cons.bl").read_text(), end="")
```

```text
@stage: cons

Xm := ℝ₊₊
Xa := ℝ₊

ρ : [1, inf)

𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)         :: [id=util]
𝑑𝑢(c : ℝ₊₊) := c^(-ρ)               :: [id=marginal_utility]
Γ(x : ℝ₊₊) := (0, x]

[id=arvl_to_dcsn, (m : Xm, l : ℝ₊) : !arvl -> (m_d : Xm) : !dcsn] {
    m_d = m
}

[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : Xa) : !cntn] {
    a = m_d - c
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V        = 𝑢(c) + V[>]          :: [id=value]
    D_{m_d}V = 𝑑𝑢(c)                :: [id=marginal]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}

[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality]
}
```

`load_stage(path)` reads a stage file into its **record**, a dictionary that holds the file's text and origin under `stage`, the calibration and the settings as empty mappings, under `methods` the list of the additions it read, `[]` for the stage file alone, and the file's origin and digest under `provenance`; `load_stage(path, [methods_path])` reads the stage file with the methods files its list names, and `methods` then holds one record with the keys `origin` and `text` for each addition, in the order given. `elaborate_stage(record)` parses the text and constructs the stage. The result is a **stage occurrence**: the file elaborated once, with its own bindings, sharing no object with any other elaboration of the same file. One file may be elaborated at several positions, in one [period](../../../wiki/period.md) or across periods, and each elaboration is a separate stage occurrence, which prints the name the file declares and, when it stands in a [trellis](../../../wiki/trellis.md), records its position there in its `provenance`. A stage occurrence is never adjusted in place: it varies only through one of its three bindings or through a different text, which is elaborated again, and a text derived from the file is elaborated as a stage occurrence of its own, with its origin recorded.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
print(repr(stage))
```

```text
ElaboratedStage('cons', symbolic)
```

The short form names the class, the declared name of the stage and its version. Where the bindings present follow the order calibration, methodization, configuration from its start, the version is one word: `symbolic` before any binding, then `calibrated`, `methodized` and `specified` as the verbs of [The binding verbs](09-binding-verbs.md) are applied in that order. Otherwise the version is the list of the bindings present, in that order: a stage occurrence constructed with its methods files and not yet calibrated prints `methods`, and `methods, settings` once it is configured.

A record may also hold, as mappings, the sources of the calibration and the settings, and under `methods` the additions `load_stage` read, which are read with the stage text when the stage is constructed and bound by no verb: `elaborate_stage(record)` constructs the stage from the stage file with its additions and binds each source the record supplies, in the order of [The binding verbs](09-binding-verbs.md) §1, a non-empty `calibration` as `calibrate` binds it and a non-empty `settings` as `configure` binds it. Under `methods` anything but that list is refused under `record-shape`, the mapping `{"methods": []}` among it, and the refusal says to write `methods: []`; an empty mapping is admitted as the empty source of a record written by hand. An empty source binds nothing, so the record `load_stage(path)` returns gives the symbolic stage, as above, and `elaborate_stage(record, bind=False)` gives the symbolic stage whatever the record holds, the additions left out with the other sources. The stage is constructed, the bindings are made on it, and it is copied once, at the end; for a record without additions the result equals, provenance included, the stage the two verbs bind one after another on `elaborate_stage(record, bind=False)` with the record's own mappings, each binding that stage itself. A source is refused as its verb refuses it.

```python
record = load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl")
record["calibration"] = {"ρ": 6.0}
calibrated = elaborate_stage(record)
print(repr(calibrated), calibrated.par.ρ)
print(repr(elaborate_stage(record, bind=False)))
```

```text
ElaboratedStage('cons', calibrated) 6.0
ElaboratedStage('cons', symbolic)
```

Two further functions of `bellman.stage` construct the same kind of object. `elaborate_text(text, origin)` elaborates a text held in memory and records `origin` as its source. `make_stage(term, spans)` constructs a stage from a syntax tree that `parse_with_spans`, of `bellman.syntax.lower`, has already read, where `spans` holds the source positions that a refusal cites, or is `None` for a tree without positions; calling the two separately distinguishes a parsing error from a construction error.

```python
from pathlib import Path

from bellman.stage import elaborate_text, make_stage
from bellman.syntax.lower import parse_with_spans

text = Path("applications/portfolio-choice/declaration/stages/cons/cons.bl").read_text(encoding="utf-8")
print(repr(elaborate_text(text, "applications/portfolio-choice/declaration/stages/cons/cons.bl")))
term, spans = parse_with_spans(text, filename="cons.bl")
print(repr(make_stage(term, spans)))
```

```text
ElaboratedStage('cons', symbolic)
ElaboratedStage('cons', symbolic)
```

A stage keeps no syntax tree: the tree is discarded once the stage is constructed, and every later answer is read from the stage. A file that construction cannot read is refused with a `ConstructionError`, which names the file position, the rule the file does not satisfy and what to write instead; a form of the language that no construction rule reads is refused with `NotConstructed`, a kind of `ConstructionError`. Both are exported by `bellman.refusals`, and [Refusals](../../reference/refusals.md) gives an example of every rule.

## 2 The seven attributes

A stage is a frozen record, a Python object whose attributes cannot be reassigned once it is built, with seven attributes and no others. `definitions`, `initial` and `_builders` state the model, the third under a private name: it is the stored record of the two builders graphs, which a reader reaches through `stage.builder` ([The builders graphs](03-build.md) §1); `bindings` holds the three bindings of this version; `provenance` records the file, its digest and where each binding was read from.

```python
import dataclasses

print([field.name for field in dataclasses.fields(stage)])
print(stage.bindings)
print(stage.provenance)
```

```text
['name', 'metadata', 'definitions', 'initial', '_builders', 'bindings', 'provenance']
calibration   none   calibrate(stage, source)
settings      none   configure(stage, source)
origin   applications/portfolio-choice/declaration/stages/cons/cons.bl
sha256   e60110b0b964ce482812c558922bc7aa6eaaf14421e2e162b9f87cc7b120a667
```

| Attribute | Python type | What it holds |
|---|---|---|
| `name` | `str` | the name the stage declares |
| `metadata` | read-only mapping | the file's `@` lines other than `@stage` |
| `definitions` | read-only mapping from an identity to a `Definition` | every declared name once, and one record for each line of a block |
| `initial` | record of two graphs | the graphs on fields, `backward` and `forward` |
| `_builders` | record of two graphs | the graphs on functions and measures, backward and forward, which `stage.builder` reads by the pair of perches each builder joins |
| `bindings` | record of three mappings | the calibration and the settings of this version, each `None` until bound, and `blocks`, the rows a solution method's lines add at the operative level, by the builder each opens; the methods of a version are no binding but the components of its signatures, read from the typing entries of the definitions table ([Methods and places](07-methods.md)) |
| `provenance` | read-only mapping | the file's path, text and digest, under `versions` the version of the package and the digests of its grammar files, and under `sources` where each binding was read from and its digest; on a bound version, the verb that made it, its source and, under `parent`, the provenance of the version it was made from; for a stage occurrence in a trellis, also its position there |

Nothing else is stored. Whatever the definitions, the graphs and the bindings determine is computed when it is asked for, and the answer is then kept on the version it was asked of. `calibrate` and `configure` keep the answers the stage had computed from the definitions and the graphs alone, which neither changes, and discard those that read a binding, which the stage computes again when they are asked for; `methodize` elaborates the stage anew from the union of the stage file with its methods file, whose entries and lines enter the definitions table and whose solution method's lines change the operative builders, and keeps only the answers of the stage file's own construction and of the initial diagrams ([The binding verbs](09-binding-verbs.md) §1). Of the three bindings, the calibration completes the economic problem, and the methods and the settings record how it is to be computed, changing no assertion of the model.

```python
print(stage.name, len(stage.definitions))
print(sorted(stage.provenance))
```

```text
cons 17
['origin', 'sha256', 'sources', 'text', 'versions']
```

The attributes that hold the model, the mapping of the builders and the three tables read from the model answer objects of their own, each of which has a page; the three perches answer objects too, which have a section, [The builders graphs](03-build.md) §2:

```python
for name in ("definitions", "initial", "builder", "arvl", "dcsn", "cntn", "par", "settings", "methods"):
    print(f"stage.{name:<12} {type(getattr(stage, name)).__name__}")
```

```text
stage.definitions  Definitions
stage.initial      Initial
stage.builder      BuilderPairs
stage.arvl         PerchHandle
stage.dcsn         PerchHandle
stage.cntn         PerchHandle
stage.par          Parameters
stage.settings     Settings
stage.methods      BoundMethods
```

`stage.definitions` is [the definitions table](08-definitions.md); `stage.initial` holds [the initial diagrams](02-initial.md); `stage.builder` reaches each builder by the pair of perches it joins; of the three [perches](../../../wiki/perch.md), `stage.arvl` and `stage.dcsn` each reach the builders of the edge that leaves the perch, the step from that perch to the next, and `stage.cntn`, which no edge of the stage leaves, refuses both directions with the reason ([The builders graphs](03-build.md) §§1 and 2); `stage.par` and `stage.settings` are [the parameters and the settings](06-par-and-settings.md); and `stage.methods` holds [the bound methods](07-methods.md). No attribute can be assigned after construction, and no answer changes the stage: a version with other bindings is a new object.

## 3 The printed view

`stage.view()` answers the stage's **printed view**, a text the package writes each time it is asked and stores nowhere; `print(stage)` prints the same text. It lists the [perches](../../../wiki/perch.md) with their fields, the fields by role, the [blocks](../../01-stage.md#3-builder-blocks) with the fields they read and write, the definitions by kind, the four graphs, the bindings and the directions of the two initial diagrams. Its block signatures come from the file, the inputs, the outputs and the perches of each block as its header declares them; the rest are the package's own summaries, such as the count of definitions by kind.

```python
print(stage.view())
```

```text
BELLMAN-SYM / STAGE cons                                  [VERSION = SYMBOLIC]
a stage occurrence of
applications/portfolio-choice/declaration/stages/cons/cons.bl
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PERCHES ──────────────────────────────────────────────────────────────────────
  ≺ arrival        m≺ state, l≺ state, V≺ value
  ∼ decision       m_d state, c control, V value
  ≻ continuation   a≻ state, V≻ value

FIELDS ───────────────────────────────────────────────────────────────────────
  states           m≺ at arrival, l≺ at arrival, m_d at decision, a≻ at
                   continuation
  controls         c at decision
  values           V at every perch
  shocks           none

BLOCKS ───────────────────────────────────────────────────────────────────────
  → arvl_to_dcsn   (m≺, l≺) : !arvl -> (m_d) : !dcsn
  → dcsn_to_cntn   (m_d) : !dcsn, at c -> (a≻) : !cntn
  ← cntn_to_dcsn   (V≻) : !cntn, at c -> (V) : !dcsn
  ← dcsn_to_arvl   (V) : !dcsn -> (V≺) : !arvl
  ← policy         (V≻) : !cntn -> (c) : !dcsn

DEFINITIONS ──────────────────────────────────────────────────────────────────
  kind                 count   in file order
  ───────────────────  ─────   ─────────────────────────────────────────────
  sets                     2   Xm := ℝ₊₊, Xa := ℝ₊
  parameters               1   ρ : [1, inf)
  functions                2   𝑢, 𝑑𝑢 on ℝ₊₊
  correspondences          1   Γ : ℝ₊₊ ⇉ ℝ₊₊
  laws of motion           2   m_d = m; a = m_d - c
  value aggregators        3   V = 𝑢(c) + V[>], D_{m_d}(V) = 𝑑𝑢(c); V[<] = V;
                               c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])
  block lines              6   arvl_to_dcsn.1, dcsn_to_cntn.1,
                               cntn_to_dcsn.value, cntn_to_dcsn.marginal,
                               dcsn_to_arvl.value, policy.optimality

GRAPHS ───────────────────────────────────────────────────────────────────────
  initial diagrams  backward present, forward present
  builders          backward   𝑉≻ ↦ 𝑉≺, 𝑐(m_d)
                    forward    μ≺ ↦ μ≻

BINDINGS ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  calibration      none   calibrate(stage, source)
  methods          none   methodize(stage, source)
  settings         none   configure(stage, source)

DIRECTIONS ───────────────────────────────────────────────────────────────────
  forward    ≺ m≺, l≺  →  ∼ m_d  →  ≻ a≻
  backward   ≺ V≺  ←  ∼ V  ←  ≻ V≻
  policy     ∼ c  ←  ≻ V≻
```

The view is a **sheet**, the printed form every view of the package takes. Its first line is the sheet's address, `BELLMAN-SYM / STAGE cons`, with the version at the right margin; the second says what the object is, one stage occurrence of the file it was elaborated from; a heavy line closes the title. Each section opens with its label in capitals and a hairline to column 78, and no line of the sheet is wider. The printed record of a piece below the stage, its card, has the same width and a title over a heavy line, and opens each of its sections with a heading at the left margin instead ([A piece](05-piece.md) §1).

| Section | What it prints |
|---|---|
| `PERCHES` | the fields of each perch with their roles, the marks ≺ ∼ ≻ standing for arrival, decision and continuation |
| `FIELDS` | the same fields by role, the states, the controls, the values and the shocks each on one line |
| `BLOCKS` | the blocks in file order, each with the arrow of its direction, its inputs, the coordinate it is read at and its outputs; a control a block names among its inputs is that coordinate and no wire, so it stands after `at` ([The initial diagrams](02-initial.md) §3) |
| `DEFINITIONS` | the records by kind, with the count of each kind and the records in file order, the laws of motion and the value aggregators by their rules, so that the table says what the model is ([The definitions table](08-definitions.md)) |
| `GRAPHS` | the two initial diagrams as present or refused, and each builders graph's mapping, its inputs to its outputs, so that the sheet says what each graph maps and where each is asked for ([The builders graphs](03-build.md)) |
| `BINDINGS` | the three bindings, the section's hairline drawn in dashes while one is missing, each missing binding naming the verb that supplies it ([The binding verbs](09-binding-verbs.md)) |
| `DIRECTIONS` | one line for each chain of blocks, the wires of each block grouped by perch on either side of the direction's arrow, the policy block on its own line; the card of each initial diagram prints the lines of its own direction under `Source` |

## 4 What the stage contains

`stage.list()` names the pieces the stage contains directly: the blocks of the two initial diagrams under `initial`, each with its kind and direction, and the builders of the two builders graphs under `builder`, each by the id of its block with the pair of perches it joins, or `policy` for the policy builder, and the word of its direction, the listing that `stage.builder.list()` answers.

```python
print(stage.list())
```

```text
initial
  cntn_to_dcsn   block, backward
  dcsn_to_arvl   block, backward
  policy         block, backward
  arvl_to_dcsn   block, forward
  dcsn_to_cntn   block, forward
builder
  arvl_to_dcsn   arvl → dcsn, fwd
  dcsn_to_cntn   dcsn → cntn, fwd
  cntn_to_dcsn   cntn → dcsn, bwd
  dcsn_to_arvl   dcsn → arvl, bwd
  policy         policy, bwd
```

`stage.denote()` answers the stage's two operators, the backward builders graph on value functions and the forward builders graph on measures, under the words `backward` and `forward`: the same two records that `stage.builder.bwd.denote()` and `stage.builder.fwd.denote()` answer on [The builders graphs](03-build.md) §3. The stage answers no `signature()`, since it is two operators and not one, and its sheet holds no card. Its record prints the two graphs' inputs and outputs and their builders in order, the line the policy is declared by, the conditions, the lines of the file, and at its foot the file, the perch marks the file writes and the appendix whose rules read it:

```python
print(stage.denote())
```

```text
STAGE cons
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  backward
    in   𝑉≻  : Xa → [−∞, ∞)
         ──────────────────────────────────────
    out  𝑉≺  : Xm × ℝ₊ → ℝ
         𝑐   : Xm → ℝ₊₊,  𝑐(m_d) ∈ Γ(m_d)
  forward
    in   μ≺  : finite measure on Xm × ℝ₊
         ──────────────────────────────────────
    out  μ≻  : finite measure on Xa

Operations
  backward
    1  cntn_to_dcsn
       in: 𝑉≻                           out: 𝑉

    2  dcsn_to_arvl
       in: 𝑉                            out: 𝑉≺

    3  policy
       in: 𝑉≻                           out: 𝑐

  forward
    1  arvl_to_dcsn
       in: μ≺                           out: μ

    2  dcsn_to_cntn
       in: μ                            out: μ≻

Conditions
  cntn_to_dcsn:Aggregation  𝑉(m_d) ∈ [−∞, ∞)
  dcsn_to_arvl:Aggregation  𝑉≺(m, l) ∈ ℝ
  𝑢                         ¬(1 − ρ = 0)
  cntn_to_dcsn.marginal     marginal-reading: the right side of each
                              derivative line equals the derivative, in the
                              named coordinate, of the value the builder
                              writes, under the envelope conditions: concavity
                              of the continuation value, interiority of the
                              maximizer or the multiplier's term at a binding
                              constraint, differentiability of the reward in
                              the control, a measurable selection of the
                              policy, and differentiability of the value at
                              the point read; listed and not checked
                              [required]
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  13  m_d = m
  17  a = m_d - c
  21  V        = 𝑢(c) + V[>]                       :: [id=value]
  22  D_{m_d}V = 𝑑𝑢(c)                             :: [id=marginal]
  26  V[<] = V                                     :: [id=value]
  30  c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])  :: [id=optimality]

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  ρ     cons:parameter:ρ
  𝑢     cons:function:𝑢
  Γ     cons:correspondence:Γ

File
  applications/portfolio-choice/declaration/stages/cons/cons.bl

Perches
  ≺  arrival, written [<]
  ≻  continuation, written [>]
     unmarked: decision

Appendix
  Bellman-SYM, Appendix C
  docs/Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 5 The stage's questions about itself

`stage.fields()` answers every field of the stage by its identity, with its perch, its role and its declared set.

```python
print(stage.fields())
```

```text
cons:arvl:m     ≺ arvl  state  in Xm
cons:arvl:l     ≺ arvl  state  in ℝ₊
cons:dcsn:m_d   ∼ dcsn  state  in Xm
cons:dcsn:c     ∼ dcsn  control  in ℝ₊₊
cons:cntn:a     ≻ cntn  state  in Xa
cons:cntn:V     ≻ cntn  value  in [-inf, inf)
cons:dcsn:V     ∼ dcsn  value  in [-inf, inf)
cons:arvl:V     ≺ arvl  value  in ℝ
```

`stage.obligations()` answers every condition the construction states, each under its name, with its formula or, where it has none, its sentence, and its status: `[established]` marks a condition that the declarations or the calibration settle, and a condition without the mark remains to be checked. A condition is `required` where no declaration settles it, which does not make it hold; `assumed` where the construction states it without deciding it; and `established` where the declarations or the calibration settle it, the declaration or the values it was decided on being its evidence. A status other than `required` is printed in brackets, and a part the package cannot derive is marked unresolved and never silently replaced. `stage.diagnostics()` answers nine questions about the completeness of the stage, in this order: `complete_signature`, whether every declared output is constructed; `missing_builders`, the blocks with no builder; `exposed_inputs`, the fields no block supplies; `unused_outputs`, the outputs nothing reads; `forward_map`, the lines that read a field of a later perch through a transition the stage does not write; `builder_choice`, the pairs of perches that several builders could serve; `external_calls`, the functions the lines call that no definition of the stage declares; `unread_inputs`, the value fields a backward block's header lists and no line of the block reads, each recorded as a diagnostic that names the block and the field and left out of the block's builder; and `ready_for_interpretation`, whether the stage is ready to be interpreted.

```python
print(stage.obligations())
print()
print(stage.diagnostics())
```

```text
arithmetic-definedness      ¬(1 − ρ = 0)
finite-real-arithmetic      The operands of Add at policy.optimality must be finite real numbers.
aggregation-admissibility   V(m_d) ∈ [−∞, ∞)
marginal-reading            the right side of each derivative line equals the derivative, in the named coordinate, of the value the builder writes, under the envelope conditions: concavity of the continuation value, interiority of the maximizer or the multiplier's term at a binding constraint, differentiability of the reward in the control, a measurable selection of the policy, and differentiability of the value at the point read; listed and not checked
aggregation-admissibility   V≺(m, l) ∈ ℝ
finite-real-arithmetic      The operands of Add at policy must be finite real numbers.
range-compatibility         m_d − c(m_d) ∈ Xa   [established]

complete_signature         True
missing_builders           none
exposed_inputs             none
unused_outputs             none
forward_map                none
builder_choice             none
external_calls             none
unread_inputs              none
ready_for_interpretation   True
```

Calibration establishes a condition at the bound values of the parameters ([The binding verbs](09-binding-verbs.md) §2), and a condition that the symbols alone do not decide is recorded for calibration to settle. The weights of a mixture written as parameter names are one such condition: a mixture of distributions is a probability measure only if its weights lie between zero and one and sum to one. The consumption stage declares no shock, so this listing reads the consumption–savings stage `applications/consumption-savings-iid/declaration/stages/cons_savings_iid/cons_savings_iid.bl`, whose income is a mixture of a point mass at zero with weight `p_zero` and a lognormal draw with weight `1 - p_zero`:

```python
savings = elaborate_stage(load_stage("applications/consumption-savings-iid/declaration/stages/cons_savings_iid/cons_savings_iid.bl"))
for obligation in savings.obligations():
    if obligation.condition == "distribution-weights-are-a-probability-vector":
        print(obligation.condition)
        print(obligation.entries)
        print(obligation.explanation)
```

```text
distribution-weights-are-a-probability-vector
('cons_savings_iid:distribution:y',)
the weights (p_zero, 1 - p_zero) of the Mixture declaration cons_savings_iid:distribution:y of y each lie in [0, 1] and sum to one
```

`stage.encoding()` answers a JSON-compatible mapping of this version, its definitions, its graphs, its bindings, its provenance, its conditions and its diagnostics, for a program that does not import the package; `json.dumps(stage.encoding())` accepts it unchanged, and the package provides no decoder: a stage is constructed from its file, not rebuilt from the encoding.

```python
print(sorted(stage.encoding()))
```

```text
['bindings', 'builders', 'definitions', 'derived', 'diagnostics', 'initial_diagrams', 'metadata', 'name', 'obligations', 'package_version', 'provenance', 'schema', 'version']
```

The package holds one schema, `bellman/display/stage-encoding-2.6.schema.json`, whose identifier ends in `/stage-encoding/2.6`; it describes the whole document, and every document the package's tests store for a stage file is written under it. Under `derived` stand the answers the denotations give, each node with a kind spelled `<namespace>.<Kind>`, such as `records.Wire` or `terms.Sym`, in one of the five namespaces the schema lists, `terms`, `semantic`, `records`, `predicates` and `methods`. A namespace is a name of the schema and names no module of the package, so the modules may be rearranged without changing a stored document. The methods stand within the pieces where they are bound, with the values of the settings they name on a configured version, and the source text is not encoded. Each application stage that elaborates has its document `<stage>.bl.stage.json` in `packages/bellman/tests/snapshot/corpus/<application>/`, written on one line, and the specified consumption stage also has `cons.bl.specified.stage.json`. One record of the definitions table, the law of motion of `dcsn_to_cntn`, as the encoding writes it:

```python
import json

held = stage.encoding()["definitions"]
[entry] = [item for item in held if item["identity"] == "cons:g:dcsn_to_cntn"]
print(json.dumps(entry, ensure_ascii=False, indent=1, sort_keys=True)[:700])
```

```text
{
 "address": "dcsn_to_cntn",
 "coordinates": [
  [
   "m_d",
   {
    "__class__": "Named",
    "name": "Xm"
   }
  ],
  [
   "c",
   {
    "__class__": "Named",
    "name": "ℝ₊₊"
   }
  ]
 ],
 "describes": null,
 "equations": [
  {
   "address": "dcsn_to_cntn.1",
   "term": null
  }
 ],
 "identity": "cons:g:dcsn_to_cntn",
 "kind": "law of motion",
 "ordinal": null,
 "tags": []
}
```

The entry of a set marked `!categories` ([Symbol conventions](../../reference/symbols-conventions.md) §9.2) holds one key more, `categories`, with the identifier written after the marker, or `null`, and the pairs of a code and its category's name in increasing code order, `{"identifier": "household_status", "codes": [ [0, "newborn"], [1, "old"] ]}`; no other entry holds the key, which the schema admits as optional. Under `derived` the set's category map is the second denoted object of the set's card, a node of kind `records.CategoryCodes` with the same two fields.

A value an author writes, in a binding, in a method's settings or in the provenance, is encoded with one reserved key, so that `json.dumps(stage.encoding(), allow_nan=False)` also accepts the answer. A floating-point positive infinity is written `{"$bellman": ["float", "inf"]}`, and negative infinity and NaN `"-inf"` and `"nan"` in the same form, while the strings `"inf"`, `"-inf"` and `"nan"` stay strings. An authored mapping that holds the key `$bellman` is written `{"$bellman": ["mapping", …]}`, with the list of its entries in their order, each a pair of the key and its encoded value, so that it is never read as a float. The rule applies to such values alone: the fixed fields of the graphs, the definitions and the methods are written as they are, and no admissible number is added or removed.

Within Python a version, and so a trellis of versions, is written and read back by the standard `pickle`, the form in which `multiprocessing` and `mpi4py` send an object from one process to another: what is read back equals what was written, and computes its answers again when they are asked for. Importing the module `bellman.native.hypergraphs`, which nearly every public name of the package imports (`load_stage`, `load_trellis`, the error classes and a bare `import bellman` do not) and which reading such a pickle imports, registers with the standard module `copyreg` a rule for `types.MappingProxyType` that holds in the whole Python process: `pickle` and `copy.deepcopy`, which otherwise refuse a read-only mapping, then accept any read-only mapping in that process and write it as a new read-only mapping over a copy of its entries.

From a shell, `python -m bellman applications/portfolio-choice/declaration/stages/cons/cons.bl` prints the printed view of §3; `--encoding` prints the encoding, `--dossier` the printed answers of the stage with its source, and `--refusals` the catalogue of refusals. A command that succeeds exits with status zero; a refused stage exits with status one and its explanation.

## 6 What each check establishes

| Check | What it establishes | Where it is reported |
|---|---|---|
| Parsing | The file is written in the grammar of the language. | A `ConstructionError` under the rule `syntax`, with the line and a mark under the column. |
| Construction | The declarations, the block headers and the equations satisfy the rules by which a stage is constructed. | A `ConstructionError` that names the rule and the item of the file. |
| The analytic conditions | That the declared sets contain the values and that each expectation is finite; the stage states no condition on whether a maximum is attained. | `stage.obligations()`, each condition required or established; construction establishes none that the declarations do not settle. |
| The numerical checks | That a chosen routine approximates the solution adequately. | Outside the package, with the routine. |

Success at one level establishes none of the levels below it: a stage that is constructed has solved no household problem.
