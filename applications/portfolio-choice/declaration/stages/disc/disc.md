---
title: disc
audience: developer
type: model-note
topic: [applications]
---
# disc

The discount stage of the portfolio model, translated from the legacy
`disc_stage.yaml` under `applications/cons-port/reference/legacy/syntax/stages/disc/`.
It is the last stage of every period and the sole bearer of the
discount factor β, as `unified.md` articulates: every economic stage
has β = 1, and this stage multiplies the continuation value and its
marginal by β.

## Notes

- The state passes through unchanged: `a_d = a` on the way in,
  `a[>] = a_d` on the way out, so the same name `a` appears at the
  arrival and continuation perches with perch marks.
- The legacy YAML discounts only the value `V`. The `.bl` also
  discounts the marginal value (`dV = β*dV[>]`), since the
  endogenous-grid method downstream consumes a discounted marginal;
  this matches what the legacy notebook's discount operator does to
  the value function it is handed.
- No control, no shock, no reward. The backward blocks are
  deterministic, so no expectation appears.
