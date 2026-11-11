---
title: The definitions table
tags:
  - docs/api
  - stage
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# The definitions table

> [!summary]
> `stage.definitions` is the read-only table of everything a stage file declares, each name once, and of every line its [blocks](../../01-stage.md#3-builder-blocks) write, in file order. A record is read by its identity as a key, `list()` answers the table grouped by kind and `denote(identity)` the card of one record. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`, except the last, which is printed from the perfect-foresight stage file `applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/perfect_foresight.bl` with its methods file `methods.bl`, which defines a derived parameter, and its calibration file.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the object `stage` below; [Stage tutorial](../../01-stage.md): the declarations as the file writes them.
> **Used by** — [A piece](05-piece.md): the kernels an operation reads from this table.
> **Formal account** — [Fields, functions and types](../../../bellman-calculus/04-fields,%20functions%20and%20types.md): the sets and functions a record denotes.
> **See also** — [API](../index.md) §2.4: every path of the stage object in one table.

The graphs of a stage refer to its definitions by **identity**, a key of the form `<stage>:<kind>:<name>`, `cons:parameter:ρ`, whose middle segment names the kind of the record; a line's record is keyed by the line's address instead, `cntn_to_dcsn.value`. Two kinds are made by the construction from the blocks: a record of kind `g` is a **law of motion**, the map a forward block applies to the state, and a record of kind `G` is a **value aggregator**, the pointwise function a backward block applies to the continuation value.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 The table

`stage.definitions` is a read-only mapping from each identity to its record, in file order. `list()` answers the records grouped by kind, each with the set, the map or the relation it denotes, so that the table says what the model is.

```python
print(repr(stage.definitions))
print(stage.definitions.list())
```

```text
Definitions('cons', 17 records)
BELLMAN-SYM / STAGE cons / DEFINITIONS                          [RECORDS = 17]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SETS 2 ───────────────────────────────────────────────────────────────────────
  cons:set:Xm   Xm  = ℝ₊₊
  cons:set:Xa   Xa  = ℝ₊

PARAMETERS 1 ─────────────────────────────────────────────────────────────────
  cons:parameter:ρ   ρ  ∈ [1, ∞)

FUNCTIONS 2 ──────────────────────────────────────────────────────────────────
  cons:function:𝑢    𝑢  : ℝ₊₊ → ℝ,  c ↦ c^(1 − ρ)/(1 − ρ)
                     conditions ¬(1 − ρ = 0)
  cons:function:𝑑𝑢   𝑑𝑢  : ℝ₊₊ → ℝ₊₊,  c ↦ c^(−ρ)

CORRESPONDENCES 1 ────────────────────────────────────────────────────────────
  cons:correspondence:Γ   Γ  : ℝ₊₊ ⇉ ℝ₊₊,  x ↦ (0, x]

LAWS OF MOTION 2 ─────────────────────────────────────────────────────────────
  cons:g:arvl_to_dcsn   𝑔≺  : Xm × ℝ₊ → Xm,  (m, l) ↦ m
  cons:g:dcsn_to_cntn   𝑔≻  : {m_d, c ∈ Xm × ℝ₊₊ | c ∈ Γ(m_d)} → Xa,
                              (m_d, c) ↦ m_d − c

VALUE AGGREGATORS 3 ──────────────────────────────────────────────────────────
  cons:G:cntn_to_dcsn   𝐺≻  : {V≻, m_d, c ∈ [−∞, ∞) × Xm × ℝ₊₊ | c ∈ Γ(m_d)}
                                → [−∞, ∞),
                              (V≻, m_d, c) ↦ 𝑢(c) + V≻
                        conditions 𝑉(m_d) ∈ [−∞, ∞)
                                   marginal-reading: the right side of each
                                     derivative line equals the derivative, in
                                     the named coordinate, of the value the
                                     builder writes, under the envelope
                                     conditions: concavity of the continuation
                                     value, interiority of the maximizer or
                                     the multiplier's term at a binding
                                     constraint, differentiability of the
                                     reward in the control, a measurable
                                     selection of the policy, and
                                     differentiability of the value at the
                                     point read; listed and not checked
                                     [required]
  cons:G:dcsn_to_arvl   𝐺≺  : [−∞, ∞) × Xm × ℝ₊ → ℝ,  (V, m, l) ↦ V
                        conditions 𝑉≺(m, l) ∈ ℝ
  cons:G:policy         𝐺≻  : {V≻, m_d, c ∈ [−∞, ∞) × Xm × ℝ₊₊ | c ∈ Γ(m_d)}
                                → UNRESOLVED[𝐺; result set],
                              (V≻, m_d, c) ↦ 𝑢(c) + V≻

BLOCK LINES 6 ────────────────────────────────────────────────────────────────
  arvl_to_dcsn.1          m_d = m
  dcsn_to_cntn.1          a = m_d - c
  cntn_to_dcsn.value      V        = 𝑢(c) + V[>]          :: [id=value]
                          conditions 𝑉(m_d) ∈ [−∞, ∞)
  cntn_to_dcsn.marginal   D_{m_d}V = 𝑑𝑢(c)                :: [id=marginal]
                          conditions marginal-reading: the right side of each
                                       derivative line equals the derivative,
                                       in the named coordinate, of the value
                                       the builder writes, under the envelope
                                       conditions: concavity of the
                                       continuation value, interiority of the
                                       maximizer or the multiplier's term at a
                                       binding constraint, differentiability
                                       of the reward in the control, a
                                       measurable selection of the policy, and
                                       differentiability of the value at the
                                       point read; listed and not checked
                                       [required]
  dcsn_to_arvl.value      V[<] = V                        :: [id=value]
                          conditions 𝑉≺(m, l) ∈ ℝ
  policy.optimality       c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])
                            :: [id=optimality]
```

The answer of `list()` also reads as a mapping from each kind to the identities of its records:

```python
for kind, identities in stage.definitions.list().items():
    print(f"{kind:<14} {', '.join(identities)}")
```

```text
set            cons:set:Xm, cons:set:Xa
parameter      cons:parameter:ρ
function       cons:function:𝑢, cons:function:𝑑𝑢
correspondence cons:correspondence:Γ
line           arvl_to_dcsn.1, dcsn_to_cntn.1, cntn_to_dcsn.value, cntn_to_dcsn.marginal, dcsn_to_arvl.value, policy.optimality
g              cons:g:arvl_to_dcsn, cons:g:dcsn_to_cntn
G              cons:G:cntn_to_dcsn, cons:G:dcsn_to_arvl, cons:G:policy
```

## 2 One record

A record is read by its identity as a key and has eight attributes, which are attributes and not fields, a field being an economic quantity of the model: `identity`; `kind`, one of `set`, `parameter`, `derived_parameter`, `distribution`, `function`, `function_alias`, `correspondence`, `g`, `G`, `line` and `multiplier`; `coordinates`, the record's named coordinates, each with its declared set where the file declares one; `equations`, which for a law of motion or an aggregator holds the addresses of the block's lines and no copy of their algebra, and for a derived parameter the term of its definition; `tags`, the entries of a line's annotation; `address`, where the file writes the record, the block for a law of motion or an aggregator; `ordinal`, the position of a line among the items of its block's body, counted from 1 with the branches of a branching block counted in turn, which outside a branch is the `n` of an unnamed line's address `<block>.<n>` and is the number a refusal names a line by, and `None` on a record of any other kind; and `categories`, on a set marked `!categories` ([Symbol conventions](../../reference/symbols-conventions.md) §9.2), its category map as one frozen `CategoryCodes` record of the identifier written after the marker, or `None`, and the pairs of a code and its category's name in increasing code order, `CategoryCodes(identifier='household_status', codes=((0, 'newborn'), (1, 'old')))` for the set `HouseholdStatus` of that section, and `None` on every other record.

```python
record = stage.definitions["cons:G:cntn_to_dcsn"]
for attribute in ("identity", "kind", "equations", "tags", "address", "ordinal"):
    print(f"{attribute:<12} {getattr(record, attribute)!r}")
print(f"{'coordinates':<12} {[name for name, _ in record.coordinates]!r}")
```

```text
identity     'cons:G:cntn_to_dcsn'
kind         'G'
equations    ('cntn_to_dcsn.value', 'cntn_to_dcsn.marginal')
tags         ()
address      'cntn_to_dcsn'
ordinal      None
coordinates  ['V', 'c']
```

## 3 The card of a record

`stage.definitions.denote(identity)` answers the card of one record: the function or set it defines, the conditions on its values, the lines of the file it comes from and the records of the declared names it refers to. The card is asked of the table, since a record does not hold the stage it belongs to. The card of a set marked `!categories` prints the set's category map, the second object the set denotes ([A piece](05-piece.md) §6), on the row under the set, `0 ↦ newborn, 1 ↦ old (categories household_status)`, and `list()` prints the same row. The card of a distribution declared by `N`, `LogNormal`, `Uniform`, `TruncatedNormal` or `TypeIExtremeValue` prints in the same way the second object the declaration denotes, its measure at the written arguments ([Shock distributions](../../reference/laws.md) §1), on the row under the law: `y ~ N(0, 1)` is followed by `P_y = measure on ℝ given by B ↦ …`, and `list()` prints the same row. The row stands on the declaration's own card alone: the card of another record that reads the declaration lists it by its law.

```python
print(stage.definitions.denote("cons:G:cntn_to_dcsn"))
```

```text
STAGE cons / VALUE AGGREGATOR cntn_to_dcsn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Defines
  𝐺≻  : {V≻, m_d, c ∈ [−∞, ∞) × Xm × ℝ₊₊ | c ∈ Γ(m_d)} → [−∞, ∞),
        (V≻, m_d, c) ↦ 𝑢(c) + V≻

Conditions
  𝑉(m_d) ∈ [−∞, ∞)
  marginal-reading: the right side of each derivative line equals the
    derivative, in the named coordinate, of the value the builder writes,
    under the envelope conditions: concavity of the continuation value,
    interiority of the maximizer or the multiplier's term at a binding
    constraint, differentiability of the reward in the control, a measurable
    selection of the policy, and differentiability of the value at the point
    read; listed and not checked   [required]
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  21  V        = 𝑢(c) + V[>]  :: [id=value]
  22  D_{m_d}V = 𝑑𝑢(c)        :: [id=marginal]

Definitions referenced
  Xm    cons:set:Xm
  𝑢     cons:function:𝑢
  Γ     cons:correspondence:Γ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The card of a law of motion states the map on the feasible pairs, since the policy block binds the control to a correspondence; its type is derived when the card is asked for and stored nowhere, and its `Source` section holds the line of the file with its number:

```python
print(stage.definitions.denote("cons:g:dcsn_to_cntn"))
```

```text
STAGE cons / LAW OF MOTION dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Defines
  𝑔≻  : {m_d, c ∈ Xm × ℝ₊₊ | c ∈ Γ(m_d)} → Xa,  (m_d, c) ↦ m_d − c
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  17  a = m_d - c

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  Γ     cons:correspondence:Γ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

A **derived parameter**, a constant that a definition without arguments writes from the stage's parameters ([Parameters and settings](06-par-and-settings.md) §1.1), is a record of the kind `derived_parameter`, whose identity is `<stage>:derived:<name>`. Its card prints its definition after `:=` and, on a calibrated version, the value the definition takes at the calibration on the row under it, and `list()` prints the same two rows under the heading `DERIVED PARAMETERS`, after the parameters. The listing reads the perfect-foresight stage with the addition `methods.bl` beside it, a methods file whose line `κ := 1 - q` defines the marginal propensity to consume κ from the stage's own derived parameter q, and calibrates the stage:

```python
derived = elaborate_stage(load_stage(
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/perfect_foresight.bl"))
derived.methodize(
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/methods.bl")
derived.calibrate(
    "applications/consumption-perfect-foresight-crra/declaration/calibration/perfect_foresight.yml")
print(derived.definitions.denote("perfect_foresight:derived:κ"))
```

```text
STAGE perfect_foresight / DERIVED PARAMETER κ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Defines
  κ  := 1 − q
     = 0.03846153846153855
──────────────────────────────────────────────────────────────────────────────
Source  methods.bl
  24  κ := 1 - q
        :: ["the marginal propensity to consume, one minus the return patience
        factor"]

Definitions referenced
  q     perfect_foresight:derived:q
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

A parameter's declaration is a record of this table; its value is not, since calibration binds the values, and [Parameters and settings](06-par-and-settings.md) reads the two together. A derived parameter's value is not a record either: it is computed from the definition at the calibration whenever the card or `stage.par` shows it, and no binding holds it.
