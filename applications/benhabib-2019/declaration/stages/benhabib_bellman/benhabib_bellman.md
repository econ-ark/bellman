---
title: "The Benhabib–Bisin–Luo stage (benhabib_bellman.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The Benhabib–Bisin–Luo stage (benhabib_bellman.bl)

The within-life consumption–savings stage of Benhabib, Bisin and Luo
(2019): an earnings type entering the wage and a rate-of-return type
entering the savings transition, both fixed within a life. Translated
from the archived registry stage under
`applications/pre-dynspec/benhabib-2019/`. The file is
`declaration/stages/benhabib_bellman/benhabib_bellman.bl`; the model, its registry and its trellis are
described in `economics.md`. A walkthrough of this stage is still to be written.

## Notes

- The two types are parameters of the instance, not shocks: `tau : Tau`
  names the earnings decile and `r_type : R_type` the return type, and
  neither carries a law. In the source model each pair `(tau, r_type)` is
  one finite-horizon Bellman problem (the fifty-instance calibration
  family of `dolo-plus-draft.yaml`, whose within-life stage has `r` and
  `w` as parameters and no exogenous state); the intergenerational
  Markov chains of the paper belong to the dynasty layer
  (`dolo-plus-dynasty.yaml`), not to the within-life stage. The earlier
  translation held the types fixed with identity Markov chains (`I_10`,
  `I_5`); those declarations were removed on 9 September 2026.
- `Tau := {q1, …, q10}` and `R_type := {r1, …, r5}` are finite sets
  with named members; a finite set's members are names, so the paper's
  integer labels are written `q1`…`q10` and `r1`…`r5`.
- The stage declares two families,
  `wage_fn : Age × Tau → ℝ₊` and `R_vec : ℝ₊₊ × … × ℝ₊₊` (five factors).
  The calibration supplies one wage table, indexed by incoming age and
  earnings decile, and the five gross returns. Its row for `age[>]` stores
  earnings one year younger. The forward map and its inverse both read
  `wage_fn[age[>]][tau]`. The backward block sends back `age[>] - 1`.
- `μ` and `A` are the parameters of the warm-glow bequest, declared here
  because the source stage carries them. No line of this stage uses them;
  the bequest stage `declaration/stages/bequest/bequest.bl`, in the terminal period, does.
- The policy block states the maximization, as the source's argmax line
  does. The methods file beside this file,
  `declaration/stages/benhabib_bellman/methods.bl`, is an addition to it,
  read with it: its block `policy` types the policy builder with `!egm`, the
  grid of savings `!Cartesian(a=(a_min, a_max, n_a))` and the legacy's
  handler, and writes the endogenous-grid form of the portfolio corpus, the
  inverse Euler line, the endogenous grid
  `m[>] = c[>] + (a - wage_fn[age[>]][tau]) / R_vec[r_type]`, and `c = c[>]`, which
  stand in place of the maximization at the operative level while the
  declared level keeps it; the two coincide where the Euler equation
  characterizes the optimum.
- The derivative of the decision value in wealth, `D_{m}V = c^(-σ)`, is
  stated by the line the methods file appends to the block `cntn_to_dcsn`.
