---
title: Parameters and settings
tags:
  - docs/api
  - parameters
  - settings
date: 2026-09-28
audience: user
type: api
topic: [stage-object]
---

# Parameters and settings

> [!summary]
> `stage.par` answers the parameters of a stage and `stage.settings` the settings bound to it, each a read-only mapping read by the name the file writes, `stage.par["ρ"]` and `stage.settings["n_a"]`. A parameter is part of the economic problem; a setting is a numerical choice of the method that computes it. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`, calibrated and configured by `applications/cons-port/reference/legacy/syntax/calibration.yaml` and `settings.yaml`, and methodized by `applications/portfolio-choice/declaration/stages/cons/methods.yml`, whose methods fill the settings table's last two columns, the place at which each setting is read and the method that reads it.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the object `stage` below; [The binding verbs](09-binding-verbs.md): `calibrate` and `configure`, which bind the values these tables read.
> **Used by** — [Methods and places](07-methods.md): the methods that read the settings.
> **See also** — [API](../index.md) §2.4: every path of the stage object in one table; [Methodization](../../04-methodization.md): the settings file a method reads.

[Parameters](../../../wiki/parameters.md) are the declared constants of the model, such as the risk aversion `ρ`, each declared in the stage file on a set and given a value by [calibration](../../../wiki/calibration.md); change one and the economic problem changes. [Settings](../../../wiki/settings.md) are the numerical choices of the methods, such as a grid size or a tolerance, given by configuration; none of them is an assertion of the model. The two tables are queries: each reads the one place the stage holds what it answers, and neither keeps a copy.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
calibrated = stage.calibrate("applications/cons-port/reference/legacy/syntax/calibration.yaml")
specified = (calibrated.methodize("applications/portfolio-choice/declaration/stages/cons/methods.yml")
             .configure("applications/cons-port/reference/legacy/syntax/settings.yaml"))
```

## 1 The parameters

`stage.par` answers one row per declared parameter, with the set it is declared on, its bound value or the word `unbound`, and the description the file gives. `stage.par["ρ"]` answers the record of one parameter, keyed by its name as the file declares it, which prints on one line; its `value` is the number the calibration binds. `list()` answers the table the mapping prints, and `view()` the same table as text.

```python
print(stage.par)
print(stage.par["ρ"])
print()
print(calibrated.par)
print(calibrated.par["ρ"])
print(calibrated.par["ρ"].value)
```

```text
name  set       value    describes
ρ     [1, inf)  unbound
ρ : [1, inf), unbound

name  set       value  describes
ρ     [1, inf)  6.0
ρ = 6.0 : [1, inf)
6.0
```

The record is read from the parameter's declaration in the definitions table and the value in the version's bindings. The key is the name the file declares, and no other spelling is a key:

```python
try:
    stage.par["rho"]
except KeyError as refusal:
    print(refusal)
```

```text
"stage 'cons': 'rho' is no parameter of the stage; a parameter is read by the name the file declares, and the parameters are ρ"
```

## 2 The settings

`stage.settings` answers one row for each method that reads a setting, with the setting's name, its configured value, the place it is read at and the method that reads it; a setting that no method reads has one row with the last two empty. One settings file may serve every stage of an application, so a stage can be bound settings that no method bound to it reads, here among others `n_k`, `n_θ_nodes` and `n_Ψ_nodes`, the grid and quadrature sizes of the application's portfolio stage. `stage.settings["n_m"]` answers the record of one setting, and its `value` is the configured value.

```python
print(specified.settings)
print(specified.settings["n_m"])
print(specified.settings["n_m"].value)
```

```text
name           value    read at                  by
grid_spacing   expmult
n_m            8000     cntn_to_dcsn:Evaluation  !Cartesian
m_min          0.01     cntn_to_dcsn:Evaluation  !Cartesian
m_max          2000.0   cntn_to_dcsn:Evaluation  !Cartesian
n_a            800
a_min          1e-10
a_max          100.0
n_k            800
k_min          1e-10
k_max          1000.0
n_θ_nodes      7
n_Ψ_nodes      7
n_joint_nodes  49
n_sim          10000
sim_seed       42
tol_vfi        1e-08
max_iter       1000
n_m = 8000, read at cntn_to_dcsn:Evaluation by !Cartesian
8000
```

A setting has no declaration in the definitions table, so the table is read from the settings the version binds and the bound methods that name them. A version that no configuration has bound holds no setting, and a key it does not hold is refused with the reason:

```python
print(len(stage.settings))
try:
    stage.settings["n_a"]
except KeyError as refusal:
    print(refusal)
```

```text
0
"stage 'cons': 'n_a' is no setting of this version, which binds no settings; configure(stage, source) binds them"
```

## 3 One value by its name

Each table also answers one value alone, read by its name as an attribute: `calibrated.par.ρ` answers the number `calibrated.par["ρ"].value` holds and `specified.settings.n_a` the configured value of `n_a`, except that a parameter or a setting whose name is one of the table's own attributes, such as `list`, `view` or `values`, is read by its key alone.

```python
print(calibrated.par.ρ)
print(specified.settings.n_a)
```

```text
6.0
800
```
