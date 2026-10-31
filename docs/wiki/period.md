---
title: Period
slug: period
description: Stage occurrences and their declared within-period connections.
wiki_status: canonical
last_reviewed: '2026-10-02'
reviewed_by: Claude (Fable); checked against the loaders of packages/bellman/bellman/factory
sources:
- docs/Bellman-Sym/06-period.md
- docs/Bellman-Sym/07-trellis.md
- docs/bellman-calculus/08-periods-and-trellis.md
- packages/bellman/bellman/factory/loading.py
tags: []
audience: user
type: concept
---

# Period

A **period** collects [[stage|stage occurrences]] and their within-period [[connector|connections]]. Its fields remain local to each stage, while a [[parameters|parameter]] name declared by more than one stage denotes one parameter of that period. It also supplies a boundary through which the period joins its successor. The outer description is YAML; individual stage equations are written in `.bl`.

## The period file

The outer description of a period is the **period file**, `period.yml`, a template that a [[trellis|trellis file]] names under `template:` and repeats. Its `stages` take one of two shapes. Written as a list of stage keys, the file binds nothing, and the [[wiki/spec_factory|recipe]] `spec.yml` of the specification factory supplies each stage's file and its values, [[settings]] and methods. Written as a mapping from each key to a record that names the [[stage|stage file]] under `stage` and its three mappings, the file carries the bindings and needs no recipe. The two shapes are not mixed in one file, and a variant of the period stands beside it as `period.<name>.yml`. [Period Syntax](../Bellman-Sym/06-period.md) §1 writes the template, and [Trellis Syntax](../Bellman-Sym/07-trellis.md) §3 states the two shapes.

## Economic order

[[field|Field]] dependencies determine the order in which connected stages can be evaluated. Reordering names in a YAML list does not reorder economic decisions. Changing a dependency or successor can change the information and objective of the model.

The [period example](../Bellman-Sym/06-period.md) joins consumption, discounting, and investment. An authored connection selects a specified outgoing state field and incoming state field; a matching name supplies a connection only when one compatible, globally consistent choice is available. Interest, income, and discounting appear in equations; a connector selects fields but renames neither one.

## Backward composition

For a chain of stage [[operator|operators]] $T_1,\ldots,T_K$ listed in forward economic order, and after the identifications its connectors make, the period's backward operator is

$$T_{\mathrm{period}}=T_1\circ\cdots\circ T_K.$$

The rightmost operator acts first on continuation value. This formula assumes compatible value domains and well-defined component operators. Branching structures require their declared routes and continuation inputs rather than an arbitrary linear ordering.

A [[trellis]] assembles period occurrences across dates. The choice of a period boundary is part of the decomposition of the model; terminal conditions and numerical choices remain explicit.
