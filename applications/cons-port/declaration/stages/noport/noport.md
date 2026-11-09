---
title: "The no-portfolio stage (noport.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The no-portfolio stage (noport.bl)

The shock stage of the portfolio–consumption model without a portfolio choice: capital `k` earns the safe return `R`, the transitory income shock θ is drawn between decision and continuation, and the resources `m = k*R + θ` form the continuation state, at which the consumption stage decides. The consumption-only configuration of the fixed reference, `trellis.reference-cons-only.yml`, binds this stage in place of the portfolio stage.

## Notes

- The stage has no control, so the decision value is the plain expectation `E_{θ}(V[>])` and there is no policy block: nothing is chosen.
- The stage declares no arrival perch: `k` is the state of the decision perch, joined by the connector `{disc.a: k}` to the savings that leave the discount stage.
- The derivative of the decision value in capital, `D_{k}V = E_{θ}(D_{m}V[>]*R)`, is the line the methods file `methods.bl` beside this file, an addition to it, adds to the decision value builder; nothing is differentiated.
- The grids, the quadrature nodes and the simulation settings are numerical configuration and belong to the methods and settings files, not to the stage file.
