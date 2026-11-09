---
title: "The keeper's consumption stage (keeper_cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The keeper's consumption stage (keeper_cons.bl)

> [!summary]
> `keeper_cons.bl` is the consumption problem of a household that has just
> decided to keep its house: it chooses consumption out of cash on hand, with
> the housing stock fixed, and carries savings and that stock into the next
> period. The stage constructs its three views and reaches the specified
> version; the elaboration is quoted at the end of this page. The economic
> environment and the composition of the four stages (a period before the
> terminal one holds three, and the terminal period adds the bequest) are in
> `economics.md`.

## What the stage does

The household enters the stage at its decision perch with the cash on hand, the
housing stock and the income state that the keep branch of the tenure stage
produced. Nothing is drawn inside the stage, so the stage has no arrival perch:
the period's connector joins the branch's fields `w_kp`, `h_kp` and `z_kp` to
the decision states `w_d`, `h_d` and `z_d`. It chooses
consumption `c`, and the continuation state is savings, the unchanged housing
stock and the unchanged income state. The housing stock is not chosen here; it
enters utility, because utility is over consumption and the stock held at the
end of the period, and it is carried forward.

| Perch | What the household knows | Fields |
|---|---|---|
| Decision | Cash on hand, the kept housing stock and the income state; consumption is chosen here. | `w_d`, `h_d`, `z_d`, and the control `c` |
| Continuation | Savings, housing and the income state. | `a_nxt_kp`, `h_nxt_kp`, `z_nxt_kp` |

## Declarations

The stage declares the discount factor and the four parameters of utility. The
two curvatures are declared above one: at unit curvature the written expression
divides by zero, and above one utility tends to minus infinity as consumption or
housing tends to zero, which is what keeps both strictly positive. The
calibration has 3.5 and 1.5.

```bl
β   : (0,1)       :: ["discount factor"]
α   : (0,1)       :: ["weight of consumption in utility"]
γ_c : (1, inf)    :: ["curvature of utility from consumption"]
γ_h : (1, inf)    :: ["curvature of utility from housing services"]
κ   : ℝ₊₊         :: ["housing services per unit of the housing stock"]
```

Utility, its two partial derivatives and the inverse of the first are written in
closed form, and the feasible set of consumption is a correspondence from cash
on hand to an interval. A name such as `𝑢_c` carries no meaning to the language:
these are four function definitions and one correspondence definition, and what
they mean is what their bodies say.

```bl
𝑢(c : ℝ₊₊, h : ℝ₊₊) := α*c^(1-γ_c)/(1-γ_c) + (1-α)*(κ*h)^(1-γ_h)/(1-γ_h)   :: [id=util]
𝑢_c(c : ℝ₊₊) := α*c^(-γ_c)                                                :: [id=marg_util_cons]
𝑢_h(h : ℝ₊₊) := (1-α)*κ^(1-γ_h)*h^(-γ_h)                                  :: [id=marg_util_housing]
𝑢_c_inv(x : ℝ₊₊) := (α/x)^(1/γ_c)                                         :: [id=inv_marg_util_cons]
Γ(x : ℝ₊₊) := (0, x]                                                      :: [id=feasible]
```

Utility is additively separable, so the marginal utility of consumption does not
read the housing stock and the marginal utility of housing does not read
consumption. The second parameterisation of the replication code, described in
`economics.md`, is not separable, and there each of these would read both.

## Transitions

The tenure stage has already formed cash on hand and depreciated the house, so
the stage begins at the decision edge, the budget, whose header types the
decision states. Savings are declared non-negative, so the equation and the
declared sets together state that consumption cannot exceed cash on hand.

```bl
[id=dcsn_to_cntn, (w_d : ℝ₊₊, h_d : ℝ₊₊, z_d : ℝ₊₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_nxt_kp : ℝ₊, h_nxt_kp : ℝ₊₊, z_nxt_kp : ℝ₊₊) : !cntn] {
    a_nxt_kp = w_d - c                                 :: [id=savings]
    h_nxt_kp = h_d                                     :: [id=housing]
    z_nxt_kp = z_d                                     :: [id=income_state]
}
```

The income state is carried into the continuation because the continuation value
depends on it: the next period's income is drawn from the state reached here.

## Values

The backward block states current utility plus the discounted continuation
value.

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c, h_d) + β*V[>]                             :: [id=value]
}
```

The value line is the objective before a policy is substituted: with the
continuation value function written $W$ and the budget substituted, it is
$Q(w, H, z, c) = u(c, H) + \beta W(w - c, H, z)$.

The two derivatives of the decision value the tenure stage reads are stated by
the two lines the methods file `methods.bl`, the addition beside this file,
appends to the decision value builder's block `cntn_to_dcsn`, whose header
types one representation of the value and both derivatives on the grid of cash
on hand and housing.

```bl
[id=cntn_to_dcsn
    | evaluate.method : !Linear(extrapolate=extrap_policy, clamp_factor=clamp_max_factor)
    | evaluate.handler : "dcsmm:interp_as"
    | evaluate.grid : !Cartesian(w_d=(a_min, a_max, n_a), h_d=(h_min, h_max, n_h))] {
    D_{w_d}V = 𝑢_c(c)                                  :: [id=marginal_cash]
    D_{h_d}V = 𝑢_h(h_d) + β*D_{h_nxt_kp}V[>]           :: [id=marginal_housing]
}
```

The two lines are envelope conditions at the chosen consumption. The
derivative with respect to cash on hand is the marginal utility of
consumption. The derivative with respect to housing has two parts, the housing
services of this period and the discounted derivative of the continuation value
in housing, read by the term `D_{h_nxt_kp}V[>]`; that sum is the shadow value of
housing which the paper writes $\Theta$ and which the tenure stage reads on the
keep branch. Neither line differentiates anything: each is the model's
assertion that an envelope condition holds, which `stage.obligations()` lists
under `marginal-reading`.

The discount factor appears in the two consumption stages and in neither of the
tenure stage's blocks, so it is applied once per period.

The decision value is the value the stage exports, which the tenure stage reads
on the keep branch; no expectation appears because nothing is drawn in this
stage.

## Policy

The policy block of the stage file states the choice alone.

```bl
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(w_d)}(𝑢(c, h_d) + β*V[>])        :: [id=optimality]
}
```

The line is the definition of the control: consumption maximises current
utility plus the discounted continuation value over the feasible set, the
interval the correspondence gives at this state.

The block `policy` of the methods file, whose header types the policy builder's
method `!egm` with the routine's keyword arguments, its handler and its grid of
savings, is the endogenous grid method's reading of the same choice, written on
the continuation state; the union appends its three lines to the stage's policy
block, and with `!egm` in the method component they stand in place of the
maximization at the operative level while `stage.declared` keeps it.

```bl
[id=policy, policy.method : !egm(spacing=grid_phi, savings_floor=b,
        upper_envelope=keeper_upper_envelope, jump_threshold=m_bar,
        lookback=fues_lb, eps_d=fues_eps_d, eps_sep=fues_eps_sep,
        eps_fwd_back=fues_eps_fwd_back, parallel_guard=fues_parallel_guard,
        include_intersections=keeper_include_intersections,
        no_double_jumps=keeper_no_double_jumps,
        single_intersection=keeper_single_intersection,
        disable_jump_checks=keeper_disable_jump_checks)
    | policy.handler : "fues-durables:make_keeper_ops"
    | policy.grid : !Cartesian(a_nxt_kp=(a_min, a_max, n_a))] {
    c[>]   <= 𝑢_c_inv(β*D_{a_nxt_kp}V[>])              :: [id=InvEuler]
    w_d[>] = a_nxt_kp + c[>]                          :: [id=endoggrid]
    c      = c[>]                                     :: [id=cons_choice]
}
```

The first line inverts the Euler equation, reading the derivative of the
continuation value in savings by the term `D_{a_nxt_kp}V[>]`: it is an
inequality, and an inequality defines its left side as the set of values
satisfying it, so candidate consumption is a single value wherever saving is
positive and a segment at zero saving, where marginal utility may exceed the
discounted marginal value of saving. That segment is the borrowing constraint,
and writing the line as an inequality keeps it in the statement of the
addition's block `policy` rather than in the method's code. The second line
recovers the cash on hand at which each candidate is optimal, inverting the
budget. The third identifies the control with the candidate; read through the
budget, it is the Euler equation
$u_c(c) = \beta\, \partial_a W(w - c, H, z)$ in the unknown consumption.

The lines read the continuation value alone, whose derivative the first line
reads. The grid of savings on which the method tabulates the candidates is the
grid entry of the block's header, not a field of the block.

## Elaboration

```text
applications/durables/declaration/stages/keeper_cons/keeper_cons.bl: ElaboratedStage('keeper_cons', symbolic)
```

Read with its addition `declaration/stages/keeper_cons/methods.bl`, and with
`declaration/settings/durables.yml` and `declaration/calibration/durables.yml`
bound, the same stage reaches the specified version, and `stage.methods` prints
the components its places carry:

```text
ElaboratedStage('keeper_cons', specified)
cntn_to_dcsn.evaluate   !Linear(extrapolate=extrap_policy, clamp_factor=clamp_max_factor)   !Cartesian(w_d=(a_min, a_max, n_a), h_d=(h_min, h_max, n_h))   "dcsmm:interp_as"
policy                  !egm(spacing=grid_phi, savings_floor=b, upper_envelope=keeper_upper_envelope, jump_threshold=m_bar, lookback=fues_lb, eps_d=fues_eps_d, eps_sep=fues_eps_sep, eps_fwd_back=fues_eps_fwd_back, parallel_guard=fues_parallel_guard, include_intersections=keeper_include_intersections, no_double_jumps=keeper_no_double_jumps, single_intersection=keeper_single_intersection, disable_jump_checks=keeper_disable_jump_checks)   !Cartesian(a_nxt_kp=(a_min, a_max, n_a))   "fues-durables:make_keeper_ops"
```

The method `!egm` on the policy builder makes the addition's three lines the
builder's rows, whose identification `policy.cons_choice` is the implicit
statement the method solves, and the binding adds the condition the method
requires,
`egm-eligibility`, which `stage.obligations()` lists: a concave and continuously
differentiable continuation value with a finite positive right derivative at
zero saving. The addition declares the constrained segment in its inverse
Euler line; the binding neither supplies it nor proves that a candidate is
optimal. The two derivative lines stand at the Evaluation of the decision value
builder, beside the representation the addition types there.

## References

- Carroll, C. D. (2006). "The method of endogenous gridpoints for solving dynamic
  stochastic optimization problems." *Economics Letters* 91(3), 312–320.
- Dobrescu, L. I. and Shanker, A. (2026). "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN 4181302,
  Section 2.2.
- Dobrescu, L. I. and Shanker, A. (2024). "Discrete-continuous high dimensional
  dynamic programming." SSRN working paper 4850746, which is the treatment of
  occasionally binding constraints the paper above follows.
