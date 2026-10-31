---
title: Solutions at the perches
tags:
  - status/draft
  - perch
date: 2026-09-29
audience: user
type: user-guide
---

# Solutions at the perches

> [!summary]
> A stage holds its model and no numerical solution. A solver keeps what it computes in plain dictionaries, one for each stage occurrence: keyed by perch as the stage file marks it, `arvl`, `dcsn` or `cntn`, then by the name the file gives each field, each entry a NumPy array on the grid the settings define for that perch. A trellis's solutions are one such dictionary for each period and stage.

> [!info]- Relationship with other documents
> **Builds on** — [Parameters and settings](API/stage/06-par-and-settings.md) and [A piece](API/stage/05-piece.md) §2: the parameters, settings and kernels a stage answers; [Trellises](07-trellis.md): the periods of a model and their index.
> **See also** — [API](API/index.md): every path and verb of the stage object; the lesson `tutorials/topics/kernels.ipynb` of the repository, which computes the example of §2.

## 1 One dictionary for each stage occurrence

The package constructs and binds a stage; it computes and stores no value function. A solver keeps its results in one dictionary for each [stage occurrence](../wiki/stage.md), a stage file elaborated at one position of a period. Its keys are the [perches](../wiki/perch.md) as the stage file marks them: `arvl` for arrival, `dcsn` for decision, `cntn` for continuation. Under each perch is a dictionary keyed by the name the file gives each field there, such as `m`, `m_d`, `c`, `a` and `V`, holding NumPy arrays. A solver that stores the derivative of the value keeps it under `dV`: the keys `V` and `dV` of a perch hold the value and its derivative in the perch's coordinate, the function that the derivative term `D_{a}V[>]` reads at the continuation. The grid of a perch stands under the name of its coordinate, `m_d` at the decision of the consumption stage and `a` at its continuation, and every other array of the perch holds one entry for each grid point. The grid is the one the settings define: at the decision of the consumption stage, `n_m` points from `m_min` to `m_max`.

## 2 An example on the consumption stage

The lesson `tutorials/topics/kernels.ipynb` calibrates the consumption stage `applications/portfolio-choice/declaration/stages/cons/cons.bl` at $\rho = 6$, takes at the continuation ten levels of savings and the value of consuming all of them, and computes with the stage's kernels one step of the decision builder at the consumption rule $c(\mathrm m_d) = \mathrm m_d/2$. It keeps the results in this form:

```python
solution = {
    "cntn": {"a": a, "V": v, "dV": dv},
    "dcsn": {"m_d": m_d, "c": m_d / 2, "V": V, "dV": dV},
}
```

`a` holds the savings levels and `v` and `dv` the continuation value and its derivative at them; `m_d` holds the levels of resources, `c` the consumption the rule gives, and `V` and `dV` the value and its derivative at the decision. The value comes from the decision builder's two compiled kernels, the law of motion $g$ and the aggregator $G$, with $\rho$ passed at the call; the aggregator returns the value alone. The derivative is what the stated derivative line `D_{m_d}V = 𝑑𝑢(c)` of the decision builder gives, marginal utility $c^{-\rho}$ at the rule, with $\rho$ the one entry of `values`:

```python
g = cons.dcsn.builder.bwd["Pullback"].compile_kernel()
G = cons.dcsn.builder.bwd["Aggregation"].compile_kernel()
values = cons.dcsn.builder.bwd["Aggregation"].kernel().parameter_values
V = G(np.interp(g(m_d, m_d / 2), a, v), m_d, m_d / 2, *values)
dV = (m_d / 2) ** -values[0]
```

The lesson's ten points are its own, checkable by hand; a solver takes its grids from the settings.

## 3 A trellis

A [trellis](07-trellis.md) holds its periods in a list indexed by `h`, the number of periods before the last. Its solutions are held in the same way, one dictionary of perches for each period and stage, `solutions[h]["cons"]`, which a backward solver fills in the order $h = 0, 1, 2, \dots$. A stage's continuation arrays are the arrival arrays of the stage its continuation fields join, in the same period or, through the inter-period connector, in `solutions[h - 1]`.

## 4 What the stage supplies

The stage supplies the numbers and the functions. `stage.par["ρ"]` answers a parameter and its value, and `stage.settings["n_m"]` a setting and the places that read it. A builder's kernels compute the arrays of one perch from those of the next: `compile_kernel()` answers one kernel as a plain function, and a builder's `kernels()` answers all of them in the order they are applied, with the parameters' values, in a record that refers to no stage ([A builder](API/stage/04-builder.md) §5). A solver needs the records, the grids and the dictionaries, not the stage.
