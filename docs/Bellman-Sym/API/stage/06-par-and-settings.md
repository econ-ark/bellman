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
> `stage.par` answers a table of the parameters of a stage, the derived parameters the stage defines from them standing after the declared ones, and `stage.settings` a table of its settings; each entry is read by the name the file declares, `stage.par["ρ"]` and `stage.settings["n_a"]`, and neither table can be edited. A parameter is part of the economic problem and is declared in the stage file; a setting is a numerical choice of a method, declared with its set in the methods file and valued by configuration. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`, calibrated by `applications/portfolio-choice/declaration/calibration/portfolio.yml`, configured by `applications/portfolio-choice/declaration/settings/cons.yml`, and methodized by `applications/portfolio-choice/declaration/stages/cons/methods.bl`, the methods file beside the stage file, whose declarations fill the settings table's `set` column and whose entries fill its last three columns: the place at which each setting is read, the method there and, where the setting is a bound or a count of that place's grid, the grid's kind. The listings of §1.1 read instead the perfect-foresight stage file, `applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/perfect_foresight.bl`, which defines the return patience factor, calibrated by `applications/consumption-perfect-foresight-crra/declaration/calibration/perfect_foresight.yml`.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the object `stage` below; [The binding verbs](09-binding-verbs.md): `calibrate` and `configure`, which bind the values these tables read.
> **Used by** — [Methods and places](07-methods.md): the methods that read the settings.
> **See also** — [API](../index.md) §2.4: every path of the stage object in one table; [Methodization](../../04-methodization.md) §4: the declaration of a setting and the settings file.

[Parameters](../../../wiki/parameters.md) are the declared constants of the model, such as the risk aversion `ρ`, each declared in the stage file on a set and given a value by [calibration](../../../wiki/calibration.md); change one and the economic problem changes. [Settings](../../../wiki/settings.md) are the numerical choices of the methods, such as the bounds and the count of a grid, each declared in the methods file on a set and given a value by configuration; none of them is an assertion of the model. The two tables are queries: each reads the one place the stage holds what it answers, and neither keeps a copy.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 The parameters

`stage.par` answers one row per declared parameter, with the set it is declared on, its value or, before calibration, the word `unbound`, and the description the file gives, and then one row per derived parameter (§1.1). `stage.par["ρ"]` answers the record of one parameter, keyed by its name as the file declares it, which prints on one line; its `value` is the number the calibration binds. `list()` answers the rows, a record that prints as the table, and `view()` the table as text. Since `calibrate` binds the stage it is called on, `calibrated` below is `stage` itself, now with its parameter's value:

```python
print(stage.par)
calibrated = stage.calibrate("applications/portfolio-choice/declaration/calibration/portfolio.yml")
print(calibrated.par)
print(calibrated.par["ρ"])
print(calibrated.par["ρ"].value, calibrated is stage)
```

```text
name  set       value    describes
ρ     [1, inf)  unbound
name  set       value  describes
ρ     [1, inf)  6.0
ρ = 6.0 : [1, inf)
6.0 True
```

The record is read from the parameter's declaration in the stage file and from the value calibration binds. The key is the name the file declares, and no other spelling is a key:

```python
try:
    stage.par["rho"]
except KeyError as refusal:
    print(refusal)
```

```text
"stage 'cons': 'rho' is no parameter of the stage; a parameter is read by the name the file declares, and the parameters are ρ"
```

### 1.1 Derived parameters

A **derived parameter** is a constant defined from calibrated parameters without arguments. The perfect-foresight stage defines the return patience factor `q : (0,1) := (β*R)^(1/ρ)/R`. [Equation parsing rules](../../appendices/12-equation-parsing-rules.md) §2 states the allowed definitions and their evaluation order.

`stage.par` lists derived parameters after the calibrated ones. Each row gives the definition, declared set, description, and current value. Before calibration the value is `unbound`. The table evaluates a derived definition when queried; it stores no duplicate value.

The stage's human wealth is a field sent backward. Its closed-form methods instead define the stationary constants `h_lim`, `L_lim`, and `κ` ([The definitions table](08-definitions.md) §3). Those derived parameters appear only while those methods are bound.

```python
derived = elaborate_stage(load_stage(
    "applications/consumption-perfect-foresight-crra/declaration/stages/perfect_foresight/perfect_foresight.bl"))
print(derived.par)
derived.calibrate(
    "applications/consumption-perfect-foresight-crra/declaration/calibration/perfect_foresight.yml")
print(derived.par)
print(derived.par["q"])
```

```text
name  set                      value    describes
β     ℝ₊₊ @ (0, R^(ρ - 1))     unbound  discount factor; its upper bound R^(ρ-1) is the return impatience condition, q < 1
ρ     (1, inf)                 unbound  coefficient of relative risk aversion, greater than one
R     ℝ₊₊                      unbound  gross interest factor
Γ     ℝ₊₊                      unbound  permanent income growth factor
q     (0, 1) := (β*R)^(1/ρ)/R  unbound  the return patience factor; the return impatience condition is q < 1
name  set                      value               describes
β     ℝ₊₊ @ (0, R^(ρ - 1))     0.9615384615384616  discount factor; its upper bound R^(ρ-1) is the return impatience condition, q < 1
ρ     (1, inf)                 2.0                 coefficient of relative risk aversion, greater than one
R     ℝ₊₊                      1.04                gross interest factor
Γ     ℝ₊₊                      1.02                permanent income growth factor
q     (0, 1) := (β*R)^(1/ρ)/R  0.9615384615384615  the return patience factor; the return impatience condition is q < 1
q = 0.9615384615384615 : (0, 1) := (β*R)^(1/ρ)/R
```

Calibration supplies no value for a derived parameter. A source that supplies `q` is refused under `derived-parameter`, and leaves the stage unchanged. A definition with no value at the calibration is also refused. For example, the closed-form definition of `h_lim` divides by zero when `Γ = R`.

## 2 The settings

`stage.settings` answers one row per setting, with the setting's name, the set the methods file declares it on, its configured value or the word `unbound`, the place at which it is read, the method typed there and, where the setting is a bound or a count of a factor of that place's grid, the grid's kind. The settings the methods file declares come first, in declaration order; a key of the settings file that no declaration names follows, with its value and the other columns empty, since it binds nothing (the last listing of this section). A method reads a setting by its name: here the grid of the representation at the decision builder's Evaluation, `cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))`, reads `n_m`, `m_min` and `m_max` as the count and the bounds of its grid of resources, and the grid of the endogenous grid method on the policy builder, `grid : !Cartesian(a=(a_min, a_max, n_a))`, reads `n_a`, `a_min` and `a_max` as its grid of savings ([Methodization](../../04-methodization.md) §3.2). `stage.settings["n_m"]` answers the record of one setting, and its `value` is the configured value.

```python
specified = (calibrated.methodize("applications/portfolio-choice/declaration/stages/cons/methods.bl")
             .configure("applications/portfolio-choice/declaration/settings/cons.yml"))
print(specified.settings)
print(specified.settings["n_m"])
print(specified.settings["n_m"].value)
```

```text
name   set  value  read at                by       grid
n_a    ℕ    800    policy                 !egm     !Cartesian
a_min  Xa   1e-06  policy                 !egm     !Cartesian
a_max  Xa   100.0  policy                 !egm     !Cartesian
n_m    ℕ    100    cntn_to_dcsn.evaluate  !Linear  !Cartesian
m_min  Xm   0.01   cntn_to_dcsn.evaluate  !Linear  !Cartesian
m_max  Xm   10.0   cntn_to_dcsn.evaluate  !Linear  !Cartesian
n_m = 100 : ℕ, read at cntn_to_dcsn.evaluate by !Linear for its grid !Cartesian
100
```

Each record is read from the setting's declaration in the methods file, the value configuration binds and the entries that name the setting. A stage elaborated from its stage file alone holds no setting, and a key the stage does not hold is refused with the reason:

```python
bare = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
print(len(bare.settings))
try:
    bare.settings["n_a"]
except KeyError as refusal:
    print(refusal)
```

```text
0
"stage 'cons': 'n_a' is no setting of this version; its settings are none; a setting is declared in the methods file, and configure(stage, source) values it"
```

Before configuration a declared setting stands in the table with the value `unbound`, as a parameter does before calibration, with the place that reads it; `configure` refuses a value outside the declared set, under `setting-outside-set`, and a declared setting that neither the settings file nor an earlier configuration of the version values, under `setting-unvalued`; a later configuration keeps the values bound before and replaces those it names again ([The binding verbs](09-binding-verbs.md) §3; [Refusals](../../reference/refusals.md#setting-unvalued)). The listing reads a second elaboration of the stage file with its methods file, since the verbs bind the stage they are called on and `stage` above is configured already:

```python
methodized = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl",
                                        ["applications/portfolio-choice/declaration/stages/cons/methods.bl"]))
print(methodized.settings)
```

```text
name   set  value    read at                by       grid
n_a    ℕ    unbound  policy                 !egm     !Cartesian
a_min  Xa   unbound  policy                 !egm     !Cartesian
a_max  Xa   unbound  policy                 !egm     !Cartesian
n_m    ℕ    unbound  cntn_to_dcsn.evaluate  !Linear  !Cartesian
m_min  Xm   unbound  cntn_to_dcsn.evaluate  !Linear  !Cartesian
m_max  Xm   unbound  cntn_to_dcsn.evaluate  !Linear  !Cartesian
```

A settings file may hold the values of other stages of the application as well, so a stage can be given values that none of its declarations names. `configure` binds such a value, and `stage.settings` lists it after the declared settings, with no set and no place that reads it, which is where a misspelled key shows. A second configuration adds its values to those bound before, so the consumption stage configured by its own settings file and then by the settings file of the portfolio stage, `applications/portfolio-choice/declaration/settings/port.yml`, lists that file's keys, among them `n_k`, `n_Ψ_nodes` and `n_θ_nodes`, the grid and quadrature sizes of the portfolio stage:

```python
methodized.configure("applications/portfolio-choice/declaration/settings/cons.yml")
print(methodized.configure("applications/portfolio-choice/declaration/settings/port.yml").settings)
```

```text
name       set  value   read at                by       grid
n_a        ℕ    800     policy                 !egm     !Cartesian
a_min      Xa   1e-06   policy                 !egm     !Cartesian
a_max      Xa   100.0   policy                 !egm     !Cartesian
n_m        ℕ    100     cntn_to_dcsn.evaluate  !Linear  !Cartesian
m_min      Xm   0.01    cntn_to_dcsn.evaluate  !Linear  !Cartesian
m_max      Xm   10.0    cntn_to_dcsn.evaluate  !Linear  !Cartesian
n_k             800
k_min           1e-10
k_max           1000.0
n_Ψ_nodes       7
n_θ_nodes       7
n_ς             50
n_sim           10000
sim_seed        12345
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
