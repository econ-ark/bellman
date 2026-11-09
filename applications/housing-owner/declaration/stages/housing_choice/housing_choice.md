---
title: "The housing-choice stage (housing_choice.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The housing-choice stage (housing_choice.bl)

The owner's housing-choice stage: a discrete choice over the housing
stock with a proportional transaction cost, income following a discrete
Markov law. Translated from the archived stage under
`applications/pre-dynspec/housing-owner/`. A walkthrough page is still
to be written.

## Notes

- `I(H_choice, H_d)` stands for the move indicator `1{H_choice ≠ H_d}`;
  relational operators cannot yet appear in formula position.
- `E_{y}(·)` is the Markov expectation; conditioning on `y_pre` is
  carried by the `DiscreteMarkov` law, since a conditional subscript
  `E_{y|y_pre}` does not parse.
- `XH := linspace(H_min, H_max, n_H)` is a space-defining call: the
  housing grid is part of the model, not a numerical setting.
- `Y` and `n_H` use `ℕ` for the source's `Z+`; no `ℤ₊` glyph is
  reserved.
- `Pi` (the income transition matrix) and `z_vals` (the income vector)
  are typed `: ℝ` as stand-ins; no matrix or vector spaces exist in the
  grammar yet.
- The policy block's header carries perch words since 9 September 2026:
  `(V[>] : ℝ @ !vlu) : !cntn -> (H_choice : XH @ !ctrl) : !dcsn`.
- The derivatives of the decision value in cash on hand and of the arrival
  value in assets, the second with the factor `R` of the law
  `w = R*b + z_vals[y]`, are stated by the two lines that the stage's
  methods file, `declaration/stages/housing_choice/methods.bl`, appends to
  the two value builders' blocks; the file types no method, since the
  earlier form bound none on this stage.
- The income family `z_vals[y]` is still refused by the family-selection
  rule: the source supplies 49 income states from files, a count that
  comes from a discretisation, so the literal-member spelling chosen for
  the Benhabib types does not fit.
