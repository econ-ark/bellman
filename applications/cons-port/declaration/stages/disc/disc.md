---
title: "The discount stage (disc.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The discount stage (disc.bl)

The discount stage of the portfolio–consumption model, the last stage of every period and the sole bearer of the discount factor β: every economic stage has β = 1, and this stage multiplies the continuation value by β, `V = β*V[>]`, and passes it to its arrival perch unchanged, `V[<] = V`.

## Notes

- The state passes through unchanged: `a_d = a` on the way in, `a[>] = a_d` on the way out, so the same name `a` appears at the arrival and continuation perches with perch marks.
- The stage writes no derivative line. The laws between its perches are the identity, so the derivative values stored with the value pass through by the same map as the value, multiplication by β; the application's tool applies the aggregation to the values and to the derivative values alike.
- No control, no shock, no reward. The backward blocks are deterministic, so no expectation appears.
