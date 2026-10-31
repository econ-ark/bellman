---
title: "The no-portfolio stage (noport.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The no-portfolio stage (noport.bl)

The shock-realization stage of the portfolio model: investable assets
pass through a trivial decision, the transitory income shock θ realizes
between decision and continuation, and cash on hand `m = k_d*R + θ`
forms as the continuation state. Translated from the archived stage
under `applications/pre-dynspec/cons-port/syntax/stages/noport/`. A
walkthrough page is still to be written.

## Notes

- The stage has no control, so the decision value is the plain
  expectation `E_{θ}(V[>])` and there is no policy block: nothing is
  constructed.
- The source's settings block (grid sizes, quadrature and simulation
  parameters) is numerical configuration; it belongs to the
  methodization and calibration layers, not to the stage file.
