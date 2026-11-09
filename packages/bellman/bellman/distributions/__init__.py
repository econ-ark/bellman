"""The shock distributions of a stage.

- `families`: the shock families a stage may declare and what their arguments
  mean; the one table of the arguments each family takes; the conditions on a
  declaration's arguments that the calibration's numbers decide; the number a
  term takes at those numbers.
- `edges`: where a shock is drawn: each `~` declaration as the owner of its
  shocks, the dependency order of the declarations, the edge of the forward
  builder each is assigned to, and the joint distribution of an edge as the
  product of its declarations' conditional distributions.
- `conditionals`: the conditional distribution an expectation selects from the
  joint distribution of an edge, the check that its conditioning covariance
  block is positive definite, and its printed form.

The fold composes them. For the edges of its plan it calls `drawn_edges`,
which composes `distribution_declarations`, `dependency_order` and
`shock_builders`, and then `joint_distribution` for each forward builder. For
each expectation of a backward builder it calls `conditioning_shocks`,
`select_conditional` and `check_conditioning_covariance`. For the conditions
of the shock distributions it calls `check_family_conditions`,
`weights_condition` and `factorization_obligation`, and at the calibration's
numbers `check_family_conditions` and `check_conditioning_covariance` again.

Every function that takes `refuse` calls it as `refuse(rule, address,
message)`, with the action as the keyword `write` where the sentence gives an
edit, and relies on it to raise.
"""
