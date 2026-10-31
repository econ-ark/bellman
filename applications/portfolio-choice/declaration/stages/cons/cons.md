---
title: "The consumption stage of the portfolio model (cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The consumption stage of the portfolio model (cons.bl)

The consumption stage of the portfolio model: the agent enters with
cash on hand m, consumes c, and carries assets `a = m_d - c` as the
continuation state. No expectation appears in the value equations: the
shocks realize in the portfolio (or no-portfolio) stage. Translated
from the archived stage under
`applications/cons-port/reference/legacy/syntax/stages/cons/` (the legacy reference copy). A walkthrough
page is still to be written.

## Notes

- The source's inline reward `c^(1-ρ)/(1-ρ)`, marginal `c^(-ρ)`, and
  inverse marginal `(·)^(-1/ρ)` are authored as three closed-form
  definitions, `𝑢`, `𝑑𝑢`, and `𝑑𝑢𝑖𝑛𝑣` (the corpus's other stages derive
  the latter two with `D_{c}` and `Inv`; this stage authors them so its
  numerical realization needs no differentiation).
- The stage is β-free. Discounting is the separate `disc` stage, the sole
  bearer of β, as `unified.md` articulates; so the value equation is
  `V = 𝑢(c) + V[>]` and the inverse Euler line is `𝑑𝑢𝑖𝑛𝑣(dV[>])`,
  the continuation objects arriving already discounted. The legacy YAML
  carried β inside the stage and its solver removed it again.
- Marginal values are typed `(0, inf]`, strengthening the source's `R+`:
  CRRA marginal utility is strictly positive and unbounded at zero
  consumption.
- The source's settings block is numerical configuration and belongs to
  the methodization and calibration layers.
