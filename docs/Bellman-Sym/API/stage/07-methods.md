---
title: Methods and places
tags:
  - docs/api
  - method
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# Methods and places

> [!summary]
> `stage.places()` answers the places of a stage at which a methods file may bind a method, and `methods`, at every level, answers the methods bound within the piece it is asked of, read by the target the method is bound at or by the target as the methods file writes it, `stage.methods["policy"]`. Choosing a method changes no equation and runs no computation. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl` and its methods file `methods.yml`.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the object `stage` below; [The binding verbs](09-binding-verbs.md): `methodize`, which binds the methods.
> **Used by** — [Parameters and settings](06-par-and-settings.md): the settings the bound methods read.
> **See also** — [Methods](../../reference/methods.md): every method type and the places it may be bound at; [Methodization](../../04-methodization.md): the methods file; [API](../index.md) §2.4: every path of the stage object in one table.

A [method](../../../wiki/methodization.md) names a numerical technique for one piece of a stage, such as the endogenous grid method for the policy, and a [handler](../../../wiki/handler.md) names the routine that carries it out. The methods file binds each at a **target**, an address in the stage: a [block](../../01-stage.md#3-builder-blocks), a line, an operator of a line or of the whole stage, or a definition. Binding a method records the choice on the version; nothing in the package executes it.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
specified = (stage.calibrate("applications/cons-port/reference/legacy/syntax/calibration.yaml")
             .methodize("applications/portfolio-choice/declaration/stages/cons/methods.yml")
             .configure("applications/cons-port/reference/legacy/syntax/settings.yaml"))
```

## 1 The places

`stage.places()` answers one row per place at which a method may be bound, its address as a methods file writes it in the first column and its kind in the second: a builder, by the id of its block; a statement, by the line's address `<block>.<line>`; an operator of one line, `<block>.<line>.<operator>`, or of every line of the stage that holds it, by the operator's name alone; and a definition, by its name. A line marked `!node` is a place of the kind `node`, and on some stages `evaluate`, the representation of the value function a backward builder delivers, is a place of the kind `boundary`; the consumption stage has neither ([Methods](../../reference/methods.md) §1). The kinds are read from the objects of the stage, whatever method is later bound there.

```python
print(stage.places())
```

```text
address                   kind
arvl_to_dcsn              builder
dcsn_to_cntn              builder
cntn_to_dcsn              builder
cntn_to_dcsn.value        statement
cntn_to_dcsn.marginal     statement
dcsn_to_arvl              builder
dcsn_to_arvl.value        statement
dcsn_to_arvl.marginal     statement
policy                    builder
policy.optimality         statement
policy.InvEuler           statement
policy.endoggrid          statement
policy.cons_choice        statement
policy.cons_choice.solve  operator solve
solve                     operator solve
𝑢                         definition
𝑑𝑢                        definition
𝑑𝑢𝑖𝑛𝑣                     definition
Γ                         definition
```

A target that names no place is refused when the methods file is bound, as is an unknown method and a known method at a place it does not admit: a quadrature rule, for instance, belongs to an expectation and not to the policy builder. [Methods](../../reference/methods.md) states the places each method type admits. Choosing a method adds no condition of convergence or of existence, and runs nothing.

## 2 The methods of a version

`specified.methods` answers every method the version binds, one line each: the target the method is bound at and the method, or `handler only` where the entry names a handler and no method. Before methodization it is empty and prints `none`.

```python
print(stage.methods)
print(specified.methods)
```

```text
none
policy:Evaluation         !egm
cntn_to_dcsn:Evaluation   !Cartesian
arvl_to_dcsn              !deterministic
dcsn_to_cntn              handler only
```

The methods file `methods.yml` writes six entries:

```python
from pathlib import Path

print(Path("applications/portfolio-choice/declaration/stages/cons/methods.yml").read_text(encoding="utf-8"), end="")
```

```text
stage: cons

methods:
  - on: policy
    method: !egm
    handler: cons-port:egm

  - on: cntn_to_dcsn.value
    method: !Cartesian
    settings:
      orders:
        m_d: n_m
      bounds:
        m_d: [m_min, m_max]
    handler: cons-port:_make_interp

  - on: cntn_to_dcsn.marginal
    method: !Cartesian
    settings:
      orders:
        m_d: n_m
      bounds:
        m_d: [m_min, m_max]
    handler: cons-port:_make_interp

  - on: dcsn_to_arvl

  - on: arvl_to_dcsn
    method: !deterministic

  - on: dcsn_to_cntn
    handler: cons-port:transition_fwd
```

The version binds four methods, the four lines `specified.methods` prints above. A method bound at a builder's output, the policy or a value function, is kept at the evaluation that closes the builder, where that output is represented ([Methodization](../../04-methodization.md) §3): the entry `on: policy` of `!egm` is kept at `policy:Evaluation`, and the two `!Cartesian` entries on the lines `cntn_to_dcsn.value` and `cntn_to_dcsn.marginal` are one method kept at `cntn_to_dcsn:Evaluation`. The entry `on: dcsn_to_arvl`, which names no method, handler, setting or grid, is checked against the places and binds nothing.

The mapping's entries give each target's method and [handler](../../../wiki/handler.md), the registered routine that carries the method out. An entry may name a method, a handler or both, and `None` marks the one it omits:

```python
for name, method in specified.methods.items():
    print(f"{name:<32} {method.tag!r:<16} {method.handler!r}")
```

```text
policy:Evaluation                'egm'            'cons-port:egm'
cntn_to_dcsn:Evaluation          'Cartesian'      'cons-port:_make_interp'
arvl_to_dcsn                     'deterministic'  None
dcsn_to_cntn                     None             'cons-port:transition_fwd'
```

One method is read by the target it is bound at, or by the target as the methods file writes it: `specified.methods["policy"]` answers the one method bound within the policy block. The answer is the method's record, with its tag, its handler and the settings it names.

```python
print(repr(specified.methods["policy"]))
print(repr(specified.methods["cntn_to_dcsn.value"]))
```

```text
Method(tag='egm', handler='cons-port:egm', settings={})
Method(tag='Cartesian', handler='cons-port:_make_interp', settings={'bounds': {'m_d': ('m_min', 'm_max')}, 'orders': {'m_d': 'n_m'}})
```

A target within which no method is bound, or within which two different methods are bound, is refused with a `KeyError` that names the methods bound there.

## 3 Methods at every level

Every piece answers `methods`, the methods bound at it or inside it, read from the one store `stage.bindings.methods`; no piece keeps a copy. A graph answers the methods bound within it, and `stage.builder` those bound within both builders graphs; a builder answers those bound at it or inside it, and an operation or a line the method bound at it.

```python
print(specified.builder.bwd.methods)
print()
print(specified.dcsn.builder.bwd.methods)
print()
print(specified.dcsn.builder.bwd["evaluation"].methods)
```

```text
policy:Evaluation         !egm
cntn_to_dcsn:Evaluation   !Cartesian

cntn_to_dcsn:Evaluation   !Cartesian

cntn_to_dcsn:Evaluation   !Cartesian
```
