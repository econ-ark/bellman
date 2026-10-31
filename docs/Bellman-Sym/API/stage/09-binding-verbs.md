---
title: The binding verbs
tags:
  - docs/api
  - calibration
  - methodization
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# The binding verbs

> [!summary]
> `stage.calibrate(source)`, `stage.methodize(source)` and `stage.configure(source)` each add one binding to the stage they are called on and return that stage: the values of the parameters, the methods of its pieces, or the settings those methods read. Nothing is copied, a later binding of a target replaces the earlier one, and no verb solves anything. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`, calibrated and configured by `applications/cons-port/reference/legacy/syntax/calibration.yaml` and `settings.yaml`, and methodized by `applications/portfolio-choice/declaration/stages/cons/methods.yml`; the listing of §2 is calibrated instead at the mapping `{"ρ": 2.0}`.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the symbolic stage the verbs bind.
> **Used by** — [Parameters and settings](06-par-and-settings.md) and [Methods and places](07-methods.md): the tables that read the bindings.
> **See also** — [The trellis factory](../factory/trellis-factory.md): the same three verbs applied to every stage of a trellis; [API](../index.md) §2.4: every path of the stage object in one table.

Each verb takes one **source**: the path of a YAML file or a mapping of the same content. `calibrate` binds a value to every declared parameter; `methodize` binds the methods a methods file names to their targets; `configure` binds the settings those methods read. The recommended order is calibration, methodization and configuration: the parameter values complete the economic problem before the numerical choices are made, and the settings are read against the methods that name them.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 The three verbs in order

The short form of a version names what it binds: `symbolic`, `calibrated`, `methodized` and `specified` are the four stopping points of the recommended order.

```python
print(repr(stage))
backward = stage.initial.backward.graph
calibrated = stage.calibrate("applications/cons-port/reference/legacy/syntax/calibration.yaml")
print(repr(stage))
methodized = stage.methodize("applications/portfolio-choice/declaration/stages/cons/methods.yml")
print(repr(stage))
specified = stage.configure("applications/cons-port/reference/legacy/syntax/settings.yaml")
print(repr(stage))
```

```text
ElaboratedStage('cons', symbolic)
ElaboratedStage('cons', calibrated)
ElaboratedStage('cons', methodized)
ElaboratedStage('cons', specified)
```

Each verb adds its binding to the stage it is called on and returns that stage, so `calibrated`, `methodized` and `specified` are three names of `stage`, and nothing is copied. A later binding replaces the earlier one of its target: a second calibration replaces the values of the parameters, a method bound again at a target replaces the method of its kind there, and a setting given again replaces its value. A binding that is refused leaves the stage as it was. The initial diagrams and the declared builders, `stage.declared`, are those the stage file states, the same objects before and after every binding; a method block that `methodize` binds changes the operative builders `stage.builder` and the definitions table `stage.definitions`, which gains the block's definitions and lines, and nothing else ([Methods and places](07-methods.md)):

```python
print(specified is stage)
print(stage.initial.backward.graph is backward)
```

```text
True
True
```

A record may hold the three sources itself, as mappings, and then one call binds them: `elaborate_stage(record)` binds every source the record supplies in the order above, on the stage it constructs, and copies that stage once, at the end, and a record whose sources are empty, such as the one `load_stage` returns, gives the symbolic stage ([The stage](01-the-stage.md) §1). The verbs remain the route for a version already made, such as `stage` here, and for a binding made after elaboration. A methods file is read into a mapping by `load_methods` of `bellman.stage.sources`, which keeps each method's tag:

```python
from bellman.stage.sources import load_calibration, load_methods, load_settings

record = load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl")
record["calibration"] = load_calibration("applications/cons-port/reference/legacy/syntax/calibration.yaml")
record["methods"] = load_methods("applications/portfolio-choice/declaration/stages/cons/methods.yml")
record["settings"] = load_settings("applications/cons-port/reference/legacy/syntax/settings.yaml")
in_one_call = elaborate_stage(record)
print(repr(in_one_call), in_one_call.bindings == specified.bindings)
```

```text
ElaboratedStage('cons', specified) True
```

## 2 Calibration

`calibrate` requires a value for every declared parameter, in the set the file declares it on; a name the stage does not declare is not bound. A parameter declared on the functions from a finite integer or label set, `δ : L_J → ℝ`, takes a sequence with one entry per member in the members' order, nested for a product of index sets, or a mapping keyed by those integers or labels. The entries may be real-valued; the integer keys identify the entries and are not their values. The version holds the sequence, and a wrong count, a key the set does not hold or an entry outside the entries' set is refused naming the declaration and the key.

Calibration then decides every condition of the stage that involves parameters and numbers alone: a condition that holds becomes established, with the values as its evidence, and a condition that fails refuses the calibration. So `stage.calibrate({"ρ": 1.0})` is refused, since the utility `c^(1-ρ)/(1-ρ)` divides by `1 - ρ`, while at `ρ = 2.0` that condition is established, as the listing below shows; a condition that involves a [field](../../../wiki/field.md), a control, a function the file does not declare or an expression calibration cannot evaluate stays as the construction left it, and is never turned into a claim of proof. A source may be a mapping as well as a file:

```python
at_rho_2 = stage.calibrate({"ρ": 2.0})
print(repr(at_rho_2), at_rho_2.par["ρ"])
print(at_rho_2.obligations())
```

```text
ElaboratedStage('cons', calibrated) ρ = 2.0 : [1, inf)
arithmetic-definedness      ¬(1 − ρ = 0)   [established]
finite-real-arithmetic      The operands of Add at policy.endoggrid must be finite real numbers.
finite-real-arithmetic      The operands of Add at policy.optimality must be finite real numbers.
aggregation-admissibility   V(m_d) ∈ [−∞, ∞)
marginal-reading            The right side of cntn_to_dcsn.marginal equals the derivative of V in m_d under the envelope conditions.
aggregation-admissibility   V≺(m) ∈ ℝ
finite-real-arithmetic      The operands of Add at policy must be finite real numbers.
aggregation-admissibility   m_d≻(a) ∈ Xm
range-compatibility         m_d − c(m_d) ∈ Xa   [established]
```

## 3 Methodization and configuration

`methodize` binds each entry of a methods file at the place its target names: a method must admit the kind of place it is bound at, and an unknown method, a target that names no place and a method at a place it does not admit are each refused. `configure` requires a value for every setting the bound methods name, and is refused on a version with no methods bound, since a setting is read against the method that names it. Methodization may also precede calibration:

```python
other_order = (stage.methodize("applications/portfolio-choice/declaration/stages/cons/methods.yml")
               .configure("applications/cons-port/reference/legacy/syntax/settings.yaml")
               .calibrate("applications/cons-port/reference/legacy/syntax/calibration.yaml"))
print(repr(other_order), other_order.bindings.methods == specified.bindings.methods)
```

```text
ElaboratedStage('cons', specified) True
```

No method changes a graph, and nothing in the package executes a method: a method records how a piece is to be computed, and the routine that computes it is supplied outside the package. [Methods and places](07-methods.md) reads the bound methods, and [Parameters and settings](06-par-and-settings.md) the bound values.
