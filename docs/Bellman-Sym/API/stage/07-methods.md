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

`stage.places()` answers one row per place at which a method may be bound, its address as a methods file writes it in the first column and its kind in the second: a builder, by the id of its block; a statement, by the line's address `<block>.<line>`; an operator of one line, `<block>.<line>.<operator>`, or of every line of the stage that holds it, by the operator's name alone; and a definition, by its name. A line marked `!node` is a place of the kind `node`, and the consumption stage has no such line. After the lines of the policy builder and of each backward value builder stand the addresses of the [Evaluation](../../reference/operations.md#evaluation) that closes it, of the kind `operator evaluate`, where a representation of what the builder writes is bound: `policy.evaluate` for the policy function, and for a backward value builder `cntn_to_dcsn.evaluate.value` for the value function, with `cntn_to_dcsn.evaluate.marginal` for the derivative of it that a derivative line states, where one stands ([Methodization](../../04-methodization.md) §2). A representation is bound at these addresses and at no builder. The kinds are read from the objects of the stage, whatever method is later bound there.

```python
print(stage.places())
```

```text
address                         kind
arvl_to_dcsn                    builder
dcsn_to_cntn                    builder
cntn_to_dcsn                    builder
cntn_to_dcsn.value              statement
cntn_to_dcsn.marginal           statement
cntn_to_dcsn.evaluate.value     operator evaluate
cntn_to_dcsn.evaluate.marginal  operator evaluate
dcsn_to_arvl                    builder
dcsn_to_arvl.value              statement
dcsn_to_arvl.evaluate.value     operator evaluate
policy                          builder
policy.optimality               statement
policy.optimality.argmax        operator argmax
policy.InvEuler                 statement
policy.InvEuler.D               operator D
policy.grid                     statement
policy.identification           statement
policy.evaluate                 operator evaluate
argmax                          operator argmax
D                               operator D
𝑢                               definition
𝑑𝑢                              definition
Γ                               definition
𝑑𝑢𝑖𝑛𝑣                           definition
```

A target that names no place is refused when the methods file is bound, as is an unknown method and a known method at a place it does not admit: a quadrature rule, for instance, belongs to an expectation and not to the policy builder. [Methods](../../reference/methods.md) states the places each method type admits. Choosing a method adds no condition of convergence or of existence, and runs nothing.

## 2 The methods of a version

`specified.methods` answers every method the version binds, one line each: the target the method is bound at and the method, or `handler only` where the entry names a handler and no method. Before methodization it is empty and prints `none`, as a stage elaborated afresh from the same file shows; the binding verbs bind the stage they are called on, so `stage` and `specified` above name one stage.

```python
print(elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl")).methods)
print(specified.methods)
```

```text
none
policy                    !egm   block ../../methods/cons_egm.bl
cntn_to_dcsn:Evaluation   !Linear
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
    block: ../../methods/cons_egm.bl
    handler: cons-port:egm
    settings:
      grid: !Cartesian
      orders:
        a: n_a
      bounds:
        a: [a_min, a_max]

  - on: cntn_to_dcsn.evaluate.value
    method: !Linear
    settings:
      grid: !Cartesian
      orders:
        m_d: n_m
      bounds:
        m_d: [m_min, m_max]
    handler: cons-port:_make_interp

  - on: cntn_to_dcsn.evaluate.marginal
    method: !Linear
    settings:
      grid: !Cartesian
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

The version binds four methods, the four lines `specified.methods` prints above. A solution method is kept on the builder its entry names: the entry `on: policy` of `!egm`, which names the block file the method opens the builder with and its exogenous grid of savings, is kept at `policy`. A representation is kept at the Evaluation that closes the builder, where the builder's output is represented, and the methods file writes that place ([Methodization](../../04-methodization.md) §2): the two `!Linear` entries, written at the decision builder's Evaluation for the value, `cntn_to_dcsn.evaluate.value`, and for its stated derivative, `cntn_to_dcsn.evaluate.marginal`, are one method kept at `cntn_to_dcsn:Evaluation`. Each entry names the grid of resources on which the representation stores its values by the setting `grid`, whose value is the grid's kind, the tag `!Cartesian`, with the grid's order and bounds beside it ([Methodization](../../04-methodization.md) §3). The entry `on: dcsn_to_arvl`, which names no method, handler or setting, is checked against the places and binds nothing.

The mapping's entries give each target's method and [handler](../../../wiki/handler.md), the registered routine that carries the method out. An entry may name a method, a handler or both, and `None` marks the one it omits:

```python
for name, method in specified.methods.items():
    print(f"{name:<32} {method.tag!r:<16} {method.handler!r}")
```

```text
policy                           'egm'            'cons-port:egm'
cntn_to_dcsn:Evaluation          'Linear'         'cons-port:_make_interp'
arvl_to_dcsn                     'deterministic'  None
dcsn_to_cntn                     None             'cons-port:transition_fwd'
```

One method is read by the target it is bound at, or by the target as the methods file writes it: `specified.methods["policy"]` answers the one method bound within the policy block, and `specified.methods["cntn_to_dcsn.evaluate.value"]` the representation bound at the decision builder's Evaluation. The answer is the method's record, with its tag, its handler and the settings it names. The record prints the kind of a grid as the methods file writes it, `'grid': '!Cartesian'`, and its `settings` hold it as `load_methods` of `bellman.stage.sources` holds a tag written alone, `{'__yaml_tag__': 'Cartesian', 'value': ''}`.

```python
print(repr(specified.methods["policy"]))
print(repr(specified.methods["cntn_to_dcsn.evaluate.value"]))
```

```text
Method(tag='egm', handler='cons-port:egm', settings={'bounds': {'a': ('a_min', 'a_max')}, 'grid': '!Cartesian', 'orders': {'a': 'n_a'}}, block='../../methods/cons_egm.bl')
Method(tag='Linear', handler='cons-port:_make_interp', settings={'bounds': {'m_d': ('m_min', 'm_max')}, 'grid': '!Cartesian', 'orders': {'m_d': 'n_m'}}, block=None)
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
policy                    !egm   block ../../methods/cons_egm.bl
cntn_to_dcsn:Evaluation   !Linear

cntn_to_dcsn:Evaluation   !Linear

cntn_to_dcsn:Evaluation   !Linear
```
