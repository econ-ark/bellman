---
title: "The consumption-choice stage (consumption_choice.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The consumption-choice stage (consumption_choice.bl)

The owner's consumption-choice stage: continuous consumption by the
endogenous grid method, given cash on hand and the housing stock chosen
in the housing stage; no shock realizes here. Translated from the
archived stage under `applications/pre-dynspec/housing-owner/`. A
walkthrough page is still to be written.

## Notes

- `Y` and `n_H` use `ℕ` for the source's `Z+`; no `ℤ₊` glyph is
  reserved.
- The decision states carry the corpus's perch-suffix names (`w_d`,
  `H_d`, `y_d`; continuation `a_nxt`, `H_c`, `y_c`) and are typed in the
  header of `dcsn_to_cntn`: the stage enters at its decision perch, and the
  source's identity arrival transition and its arrival value, the value
  itself, are written as no block.
- The backward block `cntn_to_dcsn` reads the housing stock at the
  decision perch, `H_d`, a coordinate of its output that its header does
  not list. The source's decision-side marginal (its ShadowBellman) is the
  derivative line `D_{w_d}V = …` of the marginal block of
  `declaration/methods/marginals_consumption_choice.bl`, which the stage's
  methods file binds on the decision value builder with `!marginals`.
- The policy block's input is the continuation value `V[>]` alone, at the
  perch word `!cntn`; the decision states `w_d` and `H_d` are not in the
  signature, consumption being decision-measurable (AAS, 9 September 2026).
  Its one line is the declarative maximisation over the feasible set,
  `c = argmax_{cp : Γ(w_d)}(…)`, with `Γ(x : ℝ₊) := (0, x]` defined at
  file level. The method block `egm` of
  `declaration/methods/consumption_choice_egm.bl`, which the methods file
  binds on the policy builder with `!egm`, holds the inverse Euler line on
  `H_c`, reading the derivative of the continuation value by the term
  `D_{a_nxt}V[>]`, the endogenous grid `w[>] = a_nxt + c[>]`, and
  `c = c[>]` in the spelling of the portfolio corpus.
- Statement ids follow the corpus convention (`optimality`, `InvEuler`,
  `regrid`, `cons_choice`).
- The inverse-Euler exponent is carried verbatim from the source YAML;
  it corresponds to the compiled inverse marginal utility of the
  methods file, not the algebraic inverse of the marginal line above.
- Construction stops at `XH := linspace(H_min, H_max, n_H)`: a set
  defined by a grid constructor has no construction rule yet.
