---
title: "The portfolio stage (port.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The portfolio stage (port.bl)

The portfolio-choice stage of the portfolio–consumption model: the household divides its capital `k` between a risky asset with gross return Ψ and a safe asset with gross return R, choosing the risky share ς before the return and the transitory income θ are drawn, and the resources `w = k*(ς*Ψ + (1-ς)*R) + θ` form the continuation state, the resources of the consumption stage that follows, in the same period or in the next. The stage file writes the feasible set `Γ_ς(k) = [0, 1]`, the joint law of the shocks, the law of motion, the value `V = E_{Ψ,θ}(V[>])` and the policy as the argmax of the expected continuation value over the share, and nothing else.

## Notes

- The risky return Ψ and the transitory income shock θ follow a joint lognormal law: their logarithms are normal with correlation ρ_ζ, declared by one tilde line with a tuple subject.
- The first-order condition of the share is a method, not a line of the stage file. The methods file `methods.bl` beside this file, an addition to it, names `!time_iteration` on the policy builder with its handler and the shares the search compares, and adds the line that defines the share as the zero of `E_{Ψ,θ}(D_{w}V[>]*(Ψ - R))` at each level of capital; the application's tool realizes the builder by a search over the declared objective at those shares. The replacing selections beside it, `methods.reference.bl` and `methods.without_marginals.bl`, serve the fixed reference's trellis files and the two recipes under `notebooks/without-portfolio-marginals/`.
- The derivative of the decision value in capital, `D_{k}V = E_{Ψ,θ}(D_{w}V[>]*(ς*Ψ + (1-ς)*R))`, is the line the same methods file adds to the decision value builder; nothing is differentiated.
- The stage declares no arrival perch: `k` is the state of the decision perch, joined by the connector `{disc.a: k}` to the savings that leave the discount stage.
