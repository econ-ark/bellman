---
title: "The consumption stage (cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The consumption stage (cons.bl)

The consumption stage of the portfolio–consumption model: the household holds resources `m` at its decision, consumes `c` and carries savings `a = m - c` as the continuation state. No expectation appears in the value equation: the shocks are drawn in the portfolio stage, or in the stage without a portfolio choice. The stage file writes the utility `𝑢`, the feasible set `Γ(m) = (0, m]`, the law of motion, the value `V = 𝑢(c) + V[>]` and the policy as the argmax of `𝑢(cp) + V[>]` over the feasible set, and nothing else: no derivative line and no candidate equation.

## Notes

- The endogenous grid method is a method, not a line of the stage file. The methods file `methods.bl` beside this file, an addition to it, names `!egm` on the policy builder with its savings grid and its handler, writes the marginal utility `𝑑𝑢(c) := c^(-ρ)` and its inverse `𝑑𝑢𝑖𝑛𝑣(x) := x^(-1/ρ)` in closed form, so that the numerical realization needs no differentiation, and computes the candidate consumption at each saving from the inverse Euler line `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0`, the resources `m[>] = a + c[>]` at which that saving is chosen, and the policy on those resources. The replacing selections beside it, `methods.reference.bl`, `methods.vfi.bl` and `methods.vfi_reference.bl`, serve the other groups of occurrences: the fixed reference's evenly spaced grids, and the grid search over consumption on either spacing.
- The derivative of the decision value, the envelope condition `D_{m}V = 𝑑𝑢(c)`, is the line the same methods file adds to the decision value builder; nothing is differentiated.
- The stage is β-free. Discounting is the separate `disc` stage, the sole bearer of β, so the value equation is `V = 𝑢(c) + V[>]` and the inverse Euler line reads `D_{a}V[>]`, the continuation objects arriving already discounted. The legacy YAML carried β inside the stage and its solver removed it again.
- The stage declares no arrival perch: `m` is the state of the decision perch, and the stage before it in a period, or the inter-period connector, joins its continuation field to `m` directly.
- The grids, the quadrature and the simulation settings are numerical configuration and belong to the methods and settings files, not to the stage file.
