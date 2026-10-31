---
title: Ordering conventions
slug: ordering_conventions
description: Distinguish economic time, backward indices, and composition order.
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- docs/Bellman-Sym/06-period.md
- docs/Bellman-Sym/07-trellis.md
- docs/bellman-calculus/03-Stages and perches.md
tags:
- foundations
- notation
audience: user
type: concept
---

# Ordering conventions

Three different orders appear in a model built from [[stage|stages]]. State which one is being used.

| Order | Meaning |
|---|---|
| Within-stage information | Arrival, then decision, then continuation, subject to the stage's declared observations and choices. |
| Forward economic time | Earlier decisions and states precede later ones. Dependencies determine this order. |
| Trellis index $h$ | Zero is terminal; a larger index is earlier in economic time. |

A **backward calculation** starts from supplied continuation values. In a chain with stage [[operator|operators]] $T_1,\ldots,T_K$ named in forward economic order, $T_1\circ\cdots\circ T_K$ applies $T_K$ first. Function composition is read right to left.

A **forward calculation** starts from a distribution and a specified policy, then follows transitions in economic order. It is not obtained by applying an inverse [[bellman_operator|Bellman operator]]. [[backward_builder|Backward builders]] and [[forward_builder|forward builders]], the two directions of [[builder]], define the two operations.

[[perch|Perch]] marks `[<]` and `[>]` describe information within one stage; they do not mean calendar lags and leads. YAML list order does not replace [[field]] dependencies. The [[period]] and [[trellis]] entries give the respective composition and index rules.
