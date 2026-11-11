---
title: "Appendix E.4 — Parameters and settings"
short_title: "E.4 Parameters and settings"
status: drafted — Phase 1
tags:
  - bellman-calculus
  - parameters
  - settings
  - calibration
  - catalogue
authors:
  - Akshay Shanker
audience: user
type: reference
---
# Appendix E.4 — Parameters and settings

> [!summary]
> Parameters help define the economic model; settings control its numerical approximation. Their role depends on what they change, not on whether their values are real numbers, integers, arrays or flags.

> [!info]- Relationship with other documents
> **Builds on** — [Fields](./fields.md), [Functions](./functions.md) and [Operators](./operators.md) describe the mathematical inputs and operations.
> **Used by** — [Method types](../../Bellman-Sym/reference/methods.md): the method types a methods file names, with the settings each reads; [Methodization](../../Bellman-Sym/04-methodization.md) and [The Bellman factory](../../Bellman-Sym/08-bellman-factory.md): the source and binding rules that supply parameter values and settings; Bellman-SYM's [Appendix C](../../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the specified construction.

A **parameter** is an input on which the mathematical problem depends. A **setting** controls the numerical representation or algorithm used for that problem. The interpretation Υ and numerical construction Ρ distinguish these roles; they are maps, not stages in the economic model. Inputs may be scalar or structured, according to the declared problem.

| Role | What the value determines | Source |
|---|---|---|
| Parameter | A reward, transition, conditional law, constraint or economic domain. | Typed declarations in `.bl`, with values supplied through calibration bindings; a derived parameter is defined from other parameters by `:=` and evaluated at calibration ([parameters](../../wiki/parameters.md)). |
| Setting | A numerical grid, quadrature size, stopping tolerance or other method input. | Declared with its set in the methods file and valued in the settings file, in the forms Bellman-SYM's Methodization page gives. |

A constant has a declared type and admissible value domain. That type may include a real interval, integers, vectors, matrices or a finite set of symbols. A domain does not by itself determine a unique source type name or a declared subsort relation; [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) distinguishes those choices. A parameter supplied to an occurrence is held fixed in that occurrence's equations, even when other occurrences use different values.

The calibration and settings files and the methods file supply calibration, methods and settings through occurrence bindings. The stage equations themselves are `.bl`. The specified construction of Bellman-SYM's Appendix C retains interpreted equations and definitions; a completed numerical solution additionally needs admissible inputs and supported methods.

> [!note] Classifying an input
> Ask whether the input changes the declared economic problem or how that fixed problem is approximated. Finer discretization does not automatically remove every setting's effect: convergence requires a suitable method and refinement sequence. An economic parameter may also be irrelevant to a particular outcome, so sensitivity alone is not the classification test.

A grid defining discrete economic choices is part of the model. A grid approximating a continuous domain is numerical data. Bounds and sizes have the corresponding role; a file named settings does not change their mathematical meaning. The current source rules determine how to declare the economic domain and supply numerical grids.

<a id="the-domains-a-constant-inhabits"></a>

## 1. Value domains

The following domains illustrate the existing parameter/setting distinction. Their types do not certify any particular handler option or source key.

| Domain | Example | Role depends on |
|---|---|---|
| Real interval | Discount $\beta\in(0,1)$, gross return $R\in\mathbb R_{++}$, persistence coefficient $\rho_\zeta$ in its declared admissible set. | These are economic parameters when they define preferences, returns or the income law. Stationarity may impose additional restrictions. |
| Integer | Grid size $n_m$, quadrature-node count, iteration limit. | Numerical approximation and iteration choices are settings; a count defining the economic domain is model data. |
| Vector or array | Wage-profile coefficients, a shock mean vector. | Parameters when they determine the economic equations or law; numerical arrays can instead be settings. |
| Matrix | Shock covariance or income transition matrix. | Parameters when they define the model law; numerical approximations of a fixed law have a separate approximation role. |
| Finite admissible set | A method choice, a jump-handling flag, or an initialization choice. | Settings when they select numerical behavior; model data when they select an economic regime or constraint. |

A numerical grid can be supplied as points or specified through a construction using sizes and bounds, according to the method's supported representation. A mathematical state or action space is a domain, and a function or distribution is a mathematical object; none is reduced to a scalar constant merely because it appears in a data file. [Fields](./fields.md) and [Functions](./functions.md) describe their types.

The same Boolean domain can have two roles. A flag changing an algorithm's jump handling is a setting; a flag adding a tax schedule to the budget changes the economic problem. These are conceptual examples, not new reserved YAML keys.

> [!note] Horizon and estimation bounds
> An economic finite horizon changes the decision problem; a numerical truncation of an infinite-horizon problem is an approximation choice. How to record the horizon in source remains open in this inventory; that question is separate from its mathematical role. A parameter's admissible domain, such as $\beta\in(0,1)$, is also distinct from a narrower search interval chosen for an estimation procedure. The latter is an estimation setting, subject to the model's admissible domain.

A method's documented settings describe the inputs and domains it accepts. A **handler**, the implementation of that procedure, must map those inputs to the package arguments it supports. A method type records the options it admits and the kind of value each takes; recording an option does not show that a handler reads it.
