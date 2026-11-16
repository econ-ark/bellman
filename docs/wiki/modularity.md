---
title: Modularity
slug: modularity
wiki_status: canonical
last_reviewed: '2026-11-15'
reviewed_by: Codex agents; mathematical consistency and readability reviews
sources:
- docs/bellman-calculus/APPX-H-MODULARITY.md
audience: user
type: concept
---

# Modularity

**Modularity** requires every occurrence of a [[stage]] or [[period]] declaration to use its declared [[operator|operators]] at every admissible calibration and obtain its parameter values from the declaration's fixed [[calibration]] sources. Assigning calibration sources by position fails this requirement even when their values agree. Copies and consistent renamings that preserve [[sort|sorts]], equations and parameter roles retain the same declaration identity.

[[field|Fields]] remain arguments: age and continuation values may change while the operator remains fixed. Compatible stages compose into periods, and periods into a [[trellis]]; distinct declarations may supply distinct operators. [[methods|Methods]] and [[settings|numerical settings]] may vary by position without changing these mathematical operators.

[Appendix H](../bellman-calculus/APPX-H-MODULARITY.md) gives the formal definition and calibration proposition.
