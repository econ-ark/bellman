---
title: Connector
slug: connector
description: An authored pairing of stage-local continuation and arrival fields.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- docs/Bellman-Sym/06-period.md
- docs/Bellman-Sym/07-trellis.md
- docs/bellman-calculus/07-stage-composition.md
tags: []
audience: user
type: concept
---

# Connector

A **connector** selects an outgoing continuation state [[field]] of one [[stage|stage occurrence]] and an incoming arrival state field of another for composition. It does not rename either field. Within a [[period]] it joins stages; between periods it is an **inter-period connector**.

## What a pair states

In the [period example](../Bellman-Sym/06-period.md), `{k_next: k}` pairs outgoing capital `k_next` with incoming capital `k`. The outgoing name is first. A bare name is admitted when exactly one eligible field of that name stands on its side of the connection; otherwise prefix that endpoint with its stage key, as in `{disc.k_next: port.k}`. The two endpoints must have compatible declared sets. The author remains responsible for their economic meaning, units, and information at the join; matching names or sets alone cannot establish those assumptions.

A connector performs no calculation. A change of units, return, depreciation, or other state transformation must be authored as an equation. An authored pair takes precedence over any automatic same-name matching of its endpoints. Automatic matching selects a pair only when it is uniquely compatible without conflicting with other pairs or forming a cycle. A connection report records unresolved candidates and incomplete state routes.

## Values move by composition

More generally, for a measurable state map $\tau:X\to Y$ and a value function $v:Y\to\mathbb R$, the induced **pullback** is $K_\tau v=v\circ\tau$. It needs no inverse of $\tau$. A complete connector route pairs the ordered state coordinates as a permutation; partial or crossed pairs must be assessed together with the stage's joint law and backward value components. Neither matching type labels nor separate marginal laws alone establish that route.

## Between periods

The [[trellis]] index counts backwards from terminal. An inter-period connector indexed by $h$ joins the continuation of period $h+1$ to the arrival of period $h$. For the consumption–investment example, `{m_next: m}` belongs at this boundary. Placing this join inside the same period would instead close a cycle. See [inter-period connections](../Bellman-Sym/07-trellis.md#2-inter-period-connectors).
