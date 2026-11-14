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
> Parameters help define the economic model; settings control its numerical approximation. A parameter is told from a setting by the file that declares it: the stage file declares the parameters, and a methods file declares the settings. An author chooses the file by what a quantity changes, not by whether its values are real numbers, integers, arrays or flags.

> [!info]- Relationship with other documents
> **Builds on** — [Fields](./fields.md), [Functions](./functions.md) and [Operators](./operators.md) describe the mathematical inputs and operations.
> **Formal account** — [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §4 defines parameters, derived parameters and settings, and the admissible sets of the parameters and of the settings.
> **Used by** — [Method types](../../Bellman-Sym/reference/methods.md): the method types a methods file names, with the settings each reads; [Methodization](../../Bellman-Sym/04-methodization.md) and [The Bellman factory](../../Bellman-Sym/08-bellman-factory.md): the source and binding rules that supply parameter values and settings; Bellman-SYM's [Appendix C](../../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the specified construction.

A **parameter** is a name that the stage file declares with a set, as in `β : (0,1)`, with no role word, no perch word and no law, which no block header lists and no line writes. A **setting** is a name that a methods file declares with a set, as in `n_a : ℕ`. [Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §4 gives both definitions, under which a parameter is told from a setting by the file that declares it and not by what it changes. An author declares as a parameter an input on which the mathematical problem depends, and as a setting an input that controls the numerical representation or algorithm used for that problem. The interpretation Υ and numerical construction Ρ distinguish these roles; they are maps, not stages in the economic model. Inputs may be scalar or structured, according to the declared problem.

| Role | What the value determines | Source |
|---|---|---|
| Parameter | A reward, law of motion, conditional law, constraint or economic domain. | Declared with its set in the stage file, with values supplied through calibration bindings; a derived parameter is defined from other parameters by `:=` and evaluated at calibration, and it may declare a set, as in `q : (0,1) := e`, in which its value must lie ([parameters](../../wiki/parameters.md)). |
| Setting | A numerical grid, quadrature size, stopping tolerance or other method input. | Declared with its set in the methods file and valued in the settings file, in the forms Bellman-SYM's Methodization page gives. |

A parameter or a setting has a declared set, the set in which it takes its values, and that set may name parameters, as the set of a growth factor does in `Γ : (0, R)`. The parameter lines of a file, with its definitions of derived parameters, together define one admissible set of parameter vectors, each line adding one condition, and not one domain for each parameter. The settings of a methods file have an admissible set of their own at each parameter vector ([Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §4). A declared set is written as a set expression, such as an interval, a set of integers, a finite set of names, a product, or a union or a difference of sets of numbers (§2 there). A written type names a sort, and several written types can name one sort. No subsort relation is declared: one sort lies below another when its condition implies the other's in every stage and at every parameter vector (§3 there). A parameter supplied to a stage occurrence is held fixed in that occurrence's equations, even when stage occurrences in other periods use different values; two stages of one period that declare one parameter contribute their conditions to one admissible set (§6 there).

The calibration and settings files and the methods file supply calibration, methods and settings through the bindings of a stage occurrence. The stage equations themselves are `.bl`. The specified construction of Bellman-SYM's Appendix C retains interpreted equations and definitions; a completed numerical solution additionally needs admissible inputs and supported methods.

> [!note] Choosing the file for an input
> To decide whether to declare an input in the stage file, as a parameter, or in a methods file, as a setting, ask whether it changes the declared economic problem or how that fixed problem is approximated. Finer discretization does not automatically remove every setting's effect: convergence requires a suitable method and refinement sequence. An economic parameter may also be irrelevant to a particular outcome, so sensitivity alone is not the test for that choice.

A discrete set of economic choices that the model declares is the declared set of a field and no grid ([Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §5). A grid approximates a continuous domain, and the grid word that names it takes settings among its arguments ([Kinds and sorts](../APPX-D-KINDS-AND-SORTS.md) §4). The scalars that define a discrete economic set are parameters, which the stage file declares; the bounds and the size of a grid are settings, which a methods file declares and whose values the settings file holds. The current source rules determine how to declare the economic domain and supply numerical grids.

<a id="the-domains-a-constant-inhabits"></a>

## 1. Value domains

The following domains illustrate the existing parameter/setting distinction. They do not certify any particular handler option or source key.

| Domain | Example | Declared as a parameter or as a setting |
|---|---|---|
| Real interval | Discount $\beta\in(0,1)$, gross return $R\in\mathbb R_{++}$, persistence coefficient $\rho_\zeta$ in its declared set. | These are economic parameters when they define preferences, returns or the income law. Stationarity may impose additional restrictions. |
| Integer | Grid size $n_m$, quadrature-node count, iteration limit. | Numerical approximation and iteration choices are settings; a count defining the economic domain is a parameter. |
| Vector or array | Wage-profile coefficients, a shock mean vector. | Parameters when they determine the economic equations or law; numerical arrays can instead be settings. |
| Matrix | Shock covariance or income transition matrix. | Parameters when they define the model law; numerical approximations of a fixed law have a separate approximation role. |
| Finite set | A tie-breaking rule, a jump-handling flag, or an initialization choice. | Settings when they select numerical behavior; parameters when they select an economic regime or constraint. |

A numerical grid can be supplied as points or specified through a construction using sizes and bounds, according to the method's supported representation. A mathematical state or action space is a domain, and a function or distribution is a mathematical object; none is reduced to a scalar constant merely because it appears in a data file. [Fields](./fields.md) and [Functions](./functions.md) describe them.

The same Boolean domain can have two roles. A flag changing an algorithm's jump handling is a setting; a flag adding a tax schedule to the budget changes the economic problem. These are conceptual examples, not new reserved YAML keys.

> [!note] Horizon and estimation bounds
> An economic finite horizon changes the decision problem; a numerical truncation of an infinite-horizon problem is an approximation choice. How to record the horizon in source remains open in this inventory; that question is separate from its mathematical role. A parameter's declared set, such as $\beta\in(0,1)$, is also distinct from a narrower search interval chosen for an estimation procedure. The latter is a choice of the estimation procedure and no setting of the stage, and the parameter vectors it searches must lie in the admissible set of the parameters.

A method's documented options, the keyword arguments of its method word, describe the inputs and domains it accepts. A number that an option takes is written in the entry as the name of a declared setting and never as the number; the option itself is no setting, and neither is the choice of a method, which a typing entry of a methods file writes ([Methods](../06-Methods.md) §§2, 4 and 6). A **handler**, the implementation of that procedure, must map those inputs to the package arguments it supports. A method type records the options it admits and the set in which the value of each lies; recording an option does not show that a handler reads it.
