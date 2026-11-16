---
title: Accretion modules
slug: accretion-modules
description: Building a finite-horizon model backwards from its terminal period using reusable stages and explicit connections.
wiki_status: draft
last_reviewed: '2026-09-23'
reviewed_by: Codex; checked against current documentation, package code and public references; not a record of human acceptance
sources:
- docs/Bellman-Sym/06-period.md
- docs/Bellman-Sym/07-trellis.md
- docs/Bellman-Sym/08-bellman-factory.md
- packages/bellman/bellman/factory/trellis.py
- https://doi.org/10.1016/j.econlet.2005.09.013
- https://docs.econ-ark.org/docs/overview/ARKitecture.html
- https://docs.econ-ark.org/examples/Gentle-Intro/Cycles-Intro.html
tags:
- accretion
- trellis
- period
- builder
audience: user
type: concept
---

# Accretion modules

**Accretion** constructs a finite-horizon model backwards, adding one [[period]] at a time to the periods already specified. In [[sym|Bellman-SYM]] the resulting [[trellis]] is a diagram of periods joined by connections. The reusable components are [[stage|stage files]], which state the equations, and period descriptions, which specify how the [[stage|stage occurrences]], the elaborations of a stage file at the positions of a period, are connected.

For example, we can first specify the final year of a household's life, then add the preceding retirement years, and finally the working years. Each addition connects a period to its successor. In a [modular model](../bellman-calculus/APPX-H-MODULARITY.md), a repeated declaration keeps its operators and calibration sources. Income or survival profiles are fixed tables or functions read at an age field. A period with different available decisions may use different stages.

## Backward construction

We start with an empty sequence and construct the model in the following order.

1. Specify the terminal period and add it to the sequence. Separately supply, at realization, the terminal data for every backward field its stages require after their decisions.
2. Construct the preceding period from its stage files, with the parameter values and the numerical choices, its methods and [[settings]], appropriate to that period.
3. Declare the [[connector|inter-period connector]], which identifies compatible outgoing [[field|fields]] of the earlier period with incoming fields of its successor. Add the new period and its connection to the sequence.
4. Repeat until the sequence includes every period to be modeled.

A period can contain several stages. Within-period connectors state which stage outputs supply which subsequent inputs; inter-period connectors do the same across dates. A connector identifies or renames compatible fields. Changes in resources, income or other quantities require equations in the stages, rather than an implicit transformation inside the connector.

The period records are ordinary dictionaries and lists, assembled interactively or in a loop. Neither a stage file nor a period file receives the horizon or a position as an argument that adjusts a parameter. Each use of a stage file creates a separate stage occurrence. In a modular model, repeated declarations share calibration sources; their field inputs, methods and settings may differ. The recipe also permits positional calibration, methods and settings, without enforcing modularity.

## Relation to backward induction

Accretion assembles a model; **backward induction** solves its successive decision problems using the solution already obtained for the next period. The two can be interleaved: after specifying and solving the terminal period, we can add and solve one earlier period at a time. Alternatively, we can assemble the finite sequence before solving it. Assembly alone produces no policy function.

Consider a final-period problem in which resources are nonnegative, any consumption between zero and available resources is feasible, utility is strictly increasing in consumption, and unspent resources have no terminal value. Its solution is to consume all resources. The preceding period's problem then uses that terminal rule to value saving. [Carroll (2006, §2)](https://doi.org/10.1016/j.econlet.2005.09.013) describes the recursion from a final-period consumption rule to earlier rules. The choice of numerical method for each step is separate from the order of the recursion.

HARK provides a related computational arrangement: its one-period solver receives the next period's solution and the inputs for the current period. Its [architecture guide](https://docs.econ-ark.org/docs/overview/ARKitecture.html#agenttype-class) documents this separation. The accretion convention of the Bellman factory uses the same backward dependence, while keeping model assembly distinct from numerical solution.

## Period indices

Let the nonnegative integer $h$ count periods before the terminal period. A trellis stores its periods in accretion order: `periods[0]` is the terminal period, `periods[1]` is its predecessor, and so on. Chronological order is the reverse. If the sequence contains $n \ge 1$ periods, its inter-period joins have indices $0 \le h < n-1$: `inter_connectors[h]` joins the continuation fields of `periods[h + 1]` to the arrival fields of `periods[h]`. There is no inter-period join in a one-period model. Values used in backward induction are read in the opposite direction to the forward evolution of the state.

The terminal period can contain decisions of its own. Every continuation field required after those decisions needs supplied terminal data, including age or a bound where declared. These data are not part of the trellis file, an additional period or an inter-period connector. The [trellis guide](../Bellman-Sym/07-trellis.md) states this convention.

Appending an earlier period does not change the indices of periods already present. An index is an address, not an age. If the stages compute `age = age_next - 1` and the user supplies terminal age $T$, that recurrence gives the computed age $T-h-1$ at position $h$, from the incoming age $T-h$; the position alone does not imply it. A fixed table or function gives wages or survival probabilities at the computed age. A forward line reads the incoming `age_next` and evaluates `age_next - 1`, rather than reading the same stage's backward output. Where age is stochastic or chosen, the model must declare the corresponding information and transitions.

An extensible sequence is still a finite-horizon model. An infinite-horizon problem needs its own formulation or a justified limit of finite-horizon problems. Stationarity requires every backward field at its fixed point, and numerical solutions require convergence and accuracy checks. A terminal decision problem and a terminal value supplied to initialize a recursion are distinct modeling choices; HARK's [discussion of terminal solutions](https://docs.econ-ark.org/examples/Gentle-Intro/Cycles-Intro.html) illustrates the distinction.

## Reusing model components

The [[wiki/spec_factory|Bellman factory]] organizes inputs for repeated construction. A [[wiki/spec_factory|registry]] stores named sources of parameter values, numerical settings and methods; a [[wiki/spec_factory|recipe]] selects and combines those sources for the required stage occurrences; `load_recipe(directory, recipe, **fills)` of `bellman.trellis` returns the [[trellis|syntactic trellis]] whose records hold the merged mappings, and `assemble_trellis`, also of `bellman.trellis`, elaborates and binds it in one call. A model-building loop can repeat a declaration whose equations read a fixed profile at its supplied age field, without writing the life cycle into that stage file.

The registry and recipe are optional means of supplying these inputs. A modeler can instead construct the period records directly. The [trellis guide](../Bellman-Sym/07-trellis.md) describes those records, and the [factory guide](../Bellman-Sym/08-bellman-factory.md) describes the factory's calls. Neither route makes a terminal condition, an equation or a numerical method unnecessary.

## Current implementation

Accretion is how `accrete` and `elaborate_trellis` of `bellman.trellis` work. A trellis is a dictionary, `{"periods": [...], "inter_connectors": [...]}`, each period `{"stages": {key: record or stage}, "connectors": [...]}`; an empty one is `{"periods": [], "inter_connectors": []}`. `accrete(trellis, period, inter_connector)` appends a period and the mapping that joins it to the period appended before it, and rewrites no existing record. `elaborate_trellis(syntactic, previous=None)` constructs the stage occurrences from the records, copies those that are already elaborated and, given a second argument, those whose record is unchanged, and derives each period's joins from the fields; the three trellis verbs `calibrate_trellis`, `methodize_trellis` and `configure_trellis` bind every stage occurrence from the mapping the syntactic trellis holds at its key.

The application supplies the sequence of periods and its connections; no function of the package appends a period of its own accord, runs backward induction or solves a life-cycle model. The [trellis guide](../Bellman-Sym/07-trellis.md) distinguishes the representation from the operations available on it.

## References

- Carroll, Christopher D. (2006). [The method of endogenous gridpoints for solving dynamic stochastic optimization problems](https://doi.org/10.1016/j.econlet.2005.09.013). *Economics Letters*, 91(3), 312–320, especially §2 on recursion.
- Econ-ARK. [ARKitecture of Econ-ARK](https://docs.econ-ark.org/docs/overview/ARKitecture.html), especially the description of the one-period solver and its inputs.
- Econ-ARK. [The Nature of Time for AgentTypes](https://docs.econ-ark.org/examples/Gentle-Intro/Cycles-Intro.html), on time-varying inputs, finite horizons and terminal solutions.
