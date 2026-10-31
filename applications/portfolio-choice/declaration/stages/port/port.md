---
title: "The portfolio stage (port.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The portfolio stage (port.bl)

The portfolio-choice stage of the portfolio model: the agent splits
investable assets between a risky return Ψ and the safe return R, and
cash on hand `m_next = k_d*(ς*Ψ + (1-ς)*R) + θ` forms as the
continuation state `m_next`, the resources of the consumption stage
that follows, in the same period or in the next. Translated from the
archived stage under
`applications/pre-dynspec/cons-port/syntax/stages/port/`. A walkthrough
page is still to be written.

## Notes

- The risky return Ψ and the transitory income shock θ follow a joint
  lognormal law: their logarithms are normal with correlation ρ_ζ,
  declared by one tilde line with a tuple subject.
- The policy block states the problem twice. The argmax line,
  marked `!doc`, documents what is being chosen and is not solved; the
  line `ς = solve_{ς}(E_{Ψ,θ}(dV[>]*(Ψ - R)))` defines the risky share
  as the zero of the first-order condition, an equation the stage reads
  as one to be solved for `ς` at each decision state. A root-finding
  method attaches to that statement; a grid-search method attaches to
  the block as a whole and uses the documented objective.
