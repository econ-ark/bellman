---
slug: settings
title: Settings
tags:
- methodization
- stage-lifecycle
wiki_status: canonical
last_reviewed: '2026-09-07'
reviewed_by: Codex (Astra); source-checked
sources:
- path: docs/Bellman-Sym/API/factory/stage-factory.md
  class: canonical
  date: '2026-09-07'
- path: docs/Bellman-Sym/API/factory/spec-factory.md
  class: canonical
  date: '2026-09-07'
audience: user
type: concept
---

# Settings

**Settings** specify numerical choices such as approximation-grid size, tolerance and iteration limits. They configure how a computation is approximated. [[parameters|Parameters]] instead define the economic model, including any discrete domain that is part of that model.

The [[stage]] verb is `stage.configure(settings_source)`, with a path or mapping; `configure_trellis(elaborated, syntactic)` applies it at every position of a [[trellis]]. Configuration requires prior [[methodization]] and values for all settings referenced by the methods. The values are stored in the version's bindings, while method records retain the authored setting names.

`stage.settings` lists every configured setting with its value, the place that reads it and the method there; a setting that no method bound to the stage reads, such as a key of a settings file that several stages share, stands with the last two empty. `stage.settings["n_m"]` answers one setting's record, whose `value` is the configured value ([Parameters and settings](../Bellman-Sym/API/stage/06-par-and-settings.md) §2). A spelling mistake in a key therefore declares no new required setting and does not establish that a [[handler]] uses it.

An empty settings mapping is legitimate for a recognition-only example, but it supplies no algorithm. Conversely, recording a grid size does not demonstrate numerical accuracy or adequate boundary treatment. A compatible handler must state which options it supports and how they relate to the declared mathematical domain.

The entry [[specified_stage|specified stage]] explains the order of the bindings and why each binding gives a new [[stage|stage version]]; neither implies commutativity. The [[trellis|syntactic trellis]] holds the merged mappings, and the stage verb binds; the [[wiki/spec_factory|specification factory]] explains how sources combine. Exact configuration behavior is in [Stage functions](../Bellman-Sym/API/factory/stage-factory.md).
