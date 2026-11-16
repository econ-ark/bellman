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
> `stage.calibrate(source)`, `stage.methodize(source)` and `stage.configure(source)` each add one binding to the stage they are called on and return that stage: the values of the parameters, the methods of its pieces, or the settings those methods read. Nothing is copied, a later binding replaces the earlier one of its kind, and no verb solves anything. Every listing is printed by the package from `applications/portfolio-choice/declaration/stages/cons/cons.bl`, calibrated by `applications/portfolio-choice/declaration/calibration/portfolio.yml`, configured by `applications/portfolio-choice/declaration/settings/cons.yml`, and methodized by `applications/portfolio-choice/declaration/stages/cons/methods.bl`, the addition beside the stage file; the listing of §2 is calibrated instead at the mapping `{"ρ": 2.0}`.

> [!info]- Relationship with other documents
> **Builds on** — [The stage](01-the-stage.md): the symbolic stage the verbs bind.
> **Used by** — [Parameters and settings](06-par-and-settings.md) and [Methods and places](07-methods.md): the tables that read the bindings.
> **See also** — [The trellis factory](../factory/trellis-factory.md): the same three verbs applied to every stage of a trellis; [API](../index.md) §2.4: every path of the stage object in one table.

`calibrate` and `configure` each take one **source**, the path of a YAML file or a mapping of the same content, and `methodize` the path of a `.bl` addition or a list of them. `calibrate` binds a value to every declared parameter; `methodize` reads the additions with the stage file and holds the methods their entries type at their places; `configure` binds the settings those methods read. The recommended order is calibration, methodization and configuration: the parameter values complete the economic problem before the numerical choices are made, and the settings are read against the methods that name them.

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl"))
```

## 1 The three verbs in order

The short form of a version names what it binds: `symbolic`, `calibrated`, `methodized` and `specified` are the four stopping points of the recommended order.

```python
print(repr(stage))
backward = stage.initial.backward.graph
calibrated = stage.calibrate("applications/portfolio-choice/declaration/calibration/portfolio.yml")
print(repr(stage))
methodized = stage.methodize("applications/portfolio-choice/declaration/stages/cons/methods.bl")
print(repr(stage))
specified = stage.configure("applications/portfolio-choice/declaration/settings/cons.yml")
print(repr(stage))
```

```text
ElaboratedStage('cons', symbolic)
ElaboratedStage('cons', calibrated)
ElaboratedStage('cons', methodized)
ElaboratedStage('cons', specified)
```

Each verb adds its binding to the stage it is called on and returns that stage, so `calibrated`, `methodized` and `specified` are three names of `stage`, and nothing is copied. A later binding replaces the earlier one of its kind: a second calibration replaces the values of the parameters, a second methodization replaces the whole selection of methods files, and a setting given again replaces its value. A binding that is refused leaves the stage as it was. The initial diagrams and the declared builders, `stage.declared`, are those the stage file states before and after every binding: `calibrate` and `configure` keep the objects, and `methodize`, which elaborates the stage anew from the union of the stage file with its addition, makes them again, equal to the ones before; the addition's entries and lines change the operative builders `stage.builder` and the definitions table `stage.definitions`, and nothing else ([Methods and places](07-methods.md)):

```python
print(specified is stage)
print(stage.initial.backward.graph == backward)
```

```text
True
True
```

A record may hold the three sources itself, the calibration and the settings as mappings and the methods as the texts of its additions, and then one call binds them: `elaborate_stage(record)` reads the additions with the stage text and binds the calibration and the settings on the stage it constructs, copies that stage once, at the end, and a record whose sources are empty, such as the one `load_stage(path)` returns, gives the symbolic stage ([The stage](01-the-stage.md) §1). The verbs remain the route for a version already made, such as `stage` here, and for a binding made after elaboration. An addition is read into the record by `load_stage`, given its path beside the stage file's:

```python
from bellman.stage.sources import load_calibration, load_settings

record = load_stage("applications/portfolio-choice/declaration/stages/cons/cons.bl",
                    ["applications/portfolio-choice/declaration/stages/cons/methods.bl"])
record["calibration"] = load_calibration("applications/portfolio-choice/declaration/calibration/portfolio.yml")
record["settings"] = load_settings("applications/portfolio-choice/declaration/settings/cons.yml")
in_one_call = elaborate_stage(record)
print(repr(in_one_call), in_one_call.bindings == specified.bindings)
```

```text
ElaboratedStage('cons', specified) True
```

## 2 Calibration

`calibrate` requires a value for every declared parameter, in the set the file declares it on; a name the stage does not declare is not bound, except the name of a [derived parameter](../../../wiki/parameters.md), `h := 1/(1 - Γ/R)`, whose value is refused, since calibration computes it from the definition at the bound values before it decides the conditions below. Calibration judges the values in three steps. First it judges each declared value against its declared set, reading each parameter that the set names at its value, and refuses a value outside its set. Second it computes the value of each derived parameter from its definition at the declared values, and refuses a definition that has no value there, such as one that divides by zero. Third, at the declared and the derived values together, it judges the value of each derived parameter against the set its definition declares, as `q : (0,1) := (β*R)^(1/ρ)/R` declares `(0,1)`, and every membership the first step left undecided, such as that of a parameter declared on `(0, h)`. A derived value outside its set is refused with a sentence that names the derived parameter, its definition, the set and the values of the parameters read. A bound of a declared set whose arithmetic has no value at the calibration, such as `1/(R - 2)` at `R = 2`, refuses the calibration. Where the three steps do not decide a membership, as for a parameter declared on a set whose bound holds an expectation over a shock `y`, `(0, E_{y}(y))`, the package binds the value given, and `stage.obligations()` lists the membership as the condition `calibration-domain-membership`, which stays required. The value must still lie in the set. The package does not yet check this ([Appendix C](../../appendices/14-appendix-c-syntax-to-semantics.md) §5.3).

A parameter declared on the functions from a finite integer or label set, `δ : L_J → ℝ`, takes a sequence with one entry per member in the members' order, nested for a product of index sets, or a mapping keyed by those integers or labels. The entries may be real-valued; the integer keys identify the entries and are not their values. The version holds the sequence, and a wrong count, a key the set does not hold or an entry outside the entries' set is refused naming the declaration and the key.

Calibration then decides every condition of the stage that involves parameters and numbers alone: a condition that holds becomes established, with the values as its evidence, and a condition that fails refuses the calibration. So `stage.calibrate({"ρ": 1.0})` is refused, since the utility `c^(1-ρ)/(1-ρ)` divides by `1 - ρ`, while at `ρ = 2.0` that condition is established, as the listing below shows; a condition that involves a [field](../../../wiki/field.md), a control, a function the file does not declare or an expression calibration cannot evaluate stays as the construction left it, and is never turned into a claim of proof. A source may be a mapping as well as a file:

```python
at_rho_2 = stage.calibrate({"ρ": 2.0})
print(repr(at_rho_2), at_rho_2.par["ρ"])
print(at_rho_2.obligations())
```

```text
ElaboratedStage('cons', specified) ρ = 2.0 : [1, inf)
arithmetic-definedness               ¬(1 − ρ = 0)   [established]
finite-real-arithmetic               ¬(𝑢(cp) ∈ [∞, ∞] ∧ V[>] ∈ [−∞, −∞])
aggregation-admissibility            V(m_d) ∈ [−∞, ∞)
marginal-reading                     the right side of each derivative line equals the derivative, in the named coordinate, of the value the builder writes, under the envelope conditions: concavity of the continuation value, interiority of the maximizer or the multiplier's term at a binding constraint, differentiability of the reward in the control, a measurable selection of the policy, and differentiability of the value at the point read; listed and not checked
aggregation-admissibility            V≺(m) ∈ ℝ
aggregation-admissibility            m_d≻(a) ∈ Xm
range-compatibility                  m_d − c(m_d) ∈ Xa   [established]
range-compatibility                  V≺(m, l) ∈ ℝ
function-argument-domain-inclusion   The argument for x of cons:function:𝑑𝑢𝑖𝑛𝑣 at policy.InvEuler, from ℝ, must belong to ℝ₊₊.
egm-eligibility                      the construction satisfies the declared line where the continuation value 𝑉≻ is concave and continuously differentiable above the savings bound, with a positive right derivative at the bound, finite or infinite; an infinite derivative gives zero consumption as the interpolation endpoint, outside a strictly positive consumption domain
evaluation-domain                    The representation is evaluated inside the interval its nodes span, or outside it through an identified extension; the node interval does not replace the domain of the represented function.
continuation-input                   The representing function for V[>] must be measurable on its declared domain, depend only on (a) in that order, and take values in [-inf, inf).
```

## 3 Methodization and configuration

`methodize` holds each entry of an addition at the place its path names: a method must admit the kind of place it is typed at, and an unknown method word, a path that names no place and a method at a place it does not admit are each refused. `configure` requires a value for every setting the methods files declare and for every name a bound method writes, and judges each value against its declared set, reading each parameter that the set names at its calibrated value, and each derived parameter at the value its definition takes at the calibration. A value outside its declared set is refused under `setting-outside-set`, and a declared setting with no value under `setting-unvalued`. `configure` then judges the values where the methods read them, so that a value inside its declared set can still be refused. A keyword's value outside the domain the method's row names is refused under `method-option-value`, as `tol_v : ℝ` valued at `-1.0` is for `!vfi(tol=tol_v)`. A grid whose bounds are out of order or outside the coordinate's declared set, whose count is below two or whose node set is not strictly increasing is refused under `grid-bounds`. A requirement written after `require=` that the grid built at the bound values does not meet is refused under `grid-requirement`. A grid beside an authored table is refused under `representation-source` where its points and the table's knots are both known exactly at configuration and differ ([Settings](../../../wiki/settings.md) §2; [Refusals](../../reference/refusals.md)).

On a stage with no methods bound `configure` refuses nothing, and it binds the file's values as names no declaration holds, which `stage.settings` lists with no set; a later `methodize` judges them against the settings its additions declare. Where no calibration is bound, `configure` does not judge a value against a declared set that names a parameter, such as `tol_s : (0, ρ)`, and binds the value. A setting bound before a calibration must lie in its declared set at the values that calibration binds. The package does not yet check this ([Appendix C](../../appendices/14-appendix-c-syntax-to-semantics.md) §5.3). `calibrate` judges no setting bound before it. A later `configure` or `methodize` judges each bound setting at the calibration. Methodization may also precede calibration:

```python
other_order = (stage.methodize("applications/portfolio-choice/declaration/stages/cons/methods.bl")
               .configure("applications/portfolio-choice/declaration/settings/cons.yml")
               .calibrate("applications/portfolio-choice/declaration/calibration/portfolio.yml"))
print(repr(other_order), str(other_order.methods) == str(specified.methods))
```

```text
ElaboratedStage('cons', specified) True
```

No binding changes the initial diagrams or the declared builders, and the lines of a solution method change the operative builders alone (§1); nothing in the package executes a method: a method records how a piece is to be computed, and the routine that computes it is supplied outside the package. [Methods and places](07-methods.md) reads the bound methods, and [Parameters and settings](06-par-and-settings.md) the bound values.
