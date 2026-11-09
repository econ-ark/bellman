---
title: "The owner's consumption stage (owner_cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The owner's consumption stage (owner_cons.bl)

The last stage of an owner's period. The household arrives with the cash the
housing stage left it, the housing size it has chosen and this period's
income, chooses consumption, and carries the rest into the next period as
savings. The stage is equation (32) of Dobrescu and Shanker, §2.3, and its
Euler equation is (37). It is the stage whose solution time the paper's
Tables 3 and 4 report, because it is the stage the upper envelope works in.

The code blocks below quote the stage file beside this page and the methods
file beside it, `methods.bl`, the addition that writes the stage's derivative
line and the lines of the endogenous grid method. Where a line carries a written
note, the quote shortens it to `...`.

## Perches

| Perch | What the household knows | Fields |
|---|---|---|
| Decision | Cash, the housing size chosen, this period's income; consumption is chosen here. | `w_d`, `H_d`, `y_d` |
| Continuation | Savings, the house held, this period's income. | `a_nxt_o`, `H_nxt_o`, `y_nxt_o` |

## Declarations

Utility is the logarithmic form of equation (30), in consumption and in
housing services, with its derivative in consumption and the inverse of that
derivative:

```bl
𝑢(c : ℝ₊₊, h : ℝ₊) := α*log(c) + (1 - α)*log(κ*(h + ι))    :: [id=util]
𝑑𝑢(c : ℝ₊₊) := α/c                                        :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := α/x                                     :: [id=inv_marg_util]
Γ(x : ℝ₊₊) := (0, x]                                      :: [id=feasible]
```

Both derivatives are written in closed form rather than derived with `D` and
`Inv`, so that the realisation needs no differentiation; the shift `ι` keeps
utility finite when housing is zero. `Γ` is the feasible set of consumption
at cash `x`: positive, and no larger than cash, which is the no-borrowing
constraint.

## Blocks

The stage has no arrival perch: it is entered at its decision perch, which
holds what the stage before it leaves, the period's connector joining that
stage's continuation fields `w_own`, `H_own` and `y_own` to the decision states named here. The
decision-to-continuation transition is the budget, and its header types the
decision states:

```bl
[id=dcsn_to_cntn, (w_d : ℝ₊₊, H_d : ℝ₊, y_d : ℝ₊₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_nxt_o : ℝ₊, H_nxt_o : ℝ₊, y_nxt_o : ℝ₊₊) : !cntn] {
    a_nxt_o = w_d - c    :: [id=savings]
    H_nxt_o = H_d
    y_nxt_o = y_d
}
```

Savings are declared non-negative, which together with the equation is the
no-borrowing constraint. The house and this period's income pass through:
the next tenure stage needs the stock held and reads this period's income as
its `y_pre`.

The first backward block is the Bellman line:

```bl
[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = 𝑢(c, H_d) + β*V[>]    :: [id=value]
}
```

The continuation value is the arrival value of the next period's tenure
stage, which already holds the expectation over next period's income, so no
expectation is written here. The housing size the aggregator reads is the
decision-perch field `H_d`, the size chosen in the housing stage.

The line the methods file appends to this builder's block `cntn_to_dcsn`, whose
header types the representations of the value and of this derivative on the cash
grid, states the envelope condition, the derivative of the optimized value with
respect to cash at the chosen consumption; the conditions under which it is the
derivative are the usual ones, which `stage.obligations()` lists under
`marginal-reading`:

```bl
[id=cntn_to_dcsn
    | evaluate[V].method : !Linear
    | evaluate[V].grid : !Cartesian(w_d=(w_min, w_max, w_points))
    | evaluate[D_{w_d}V].method : !Linear
    | evaluate[D_{w_d}V].grid : !Cartesian(w_d=(w_min, w_max, w_points))] {
    D_{w_d}V = 𝑑𝑢(c)                      :: [id=marginal]
}
```

The policy block states the choice:

```bl
[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(w_d)}(𝑢(c, H_d) + β*V[>])    :: [id=optimality]
}
```

The statement is the definition of the control: the maximizer of current
utility and discounted continuation value over the feasible set. The methods
file types the endogenous grid method on the policy builder, in the header of
its block `policy`, and appends to that block three statements, which are one
way of computing the control, not a second definition; with `!egm` in the method
component they stand in place of the maximization at the operative level, and
`stage.declared` keeps the maximization:

```bl
[id=policy, policy.method : !egm(upper_envelope=upper_envelope,
        c_max=c_max,
        n_constraint_points=n_constraint_points,
        n_constraint_points_nxt=n_constraint_points_nxt,
        fues_m_bar=fues_m_bar,
        fues_lb=fues_lb,
        fues_include_intersections=fues_include_intersections,
        fues_return_intersections_separately=fues_return_intersections_separately,
        fues_single_intersection=fues_single_intersection,
        fues_endog_mbar=fues_endog_mbar,
        fues_padding_mbar=fues_padding_mbar,
        fues_no_double_jumps=fues_no_double_jumps,
        fues_disable_jump_checks=fues_disable_jump_checks,
        fues_use_post_state_jump_test=fues_use_post_state_jump_test,
        fues_left_turn_no_jump_strict=fues_left_turn_no_jump_strict,
        fues_post_clean_double_jumps=fues_post_clean_double_jumps,
        fues_detect_decreasing_policy=fues_detect_decreasing_policy,
        fues_post_clean_passes=fues_post_clean_passes,
        fues_jump_check_tol=fues_jump_check_tol,
        fues_correct_jumps=fues_correct_jumps,
        fues_min_segment_length=fues_min_segment_length,
        fues_eps_d=fues_eps_d,
        fues_eps_sep=fues_eps_sep,
        fues_eps_fwd_back=fues_eps_fwd_back,
        fues_parallel_guard=fues_parallel_guard,
        tax_enabled=tax_enabled,
        tax_c_lb_pct=tax_c_lb_pct,
        tax_c_ub_pct=tax_c_ub_pct,
        tax_n_points_per_node=tax_n_points_per_node)
    | policy.grid : !Cartesian(a_nxt_o=(a_nxt_min, a_nxt_max, a_nxt_points))] {
    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a_nxt_o}V[>])    :: [id=InvEuler]
    w_d[>] = a_nxt_o + c[>]               :: [id=endoggrid]
    c      = c[>]                         :: [id=cons_choice]
}
```

The inequality inverts the Euler equation on a grid of savings: with
marginal utility decreasing, `c[>] ≤ 𝑑𝑢𝑖𝑛𝑣(β·D_{a_nxt_o}V[>])` says that
marginal utility is at least the discounted derivative of the continuation
value in savings, with equality where savings are positive. It is single valued at every positive saving and a segment at zero
saving, which is the constrained section of the policy. The second statement
recovers the cash at which each candidate is optimal, and the third
identifies the control with the candidate at the saving the budget implies.

Two things the Euler equation of the paper has are not in these statements.
The factor `1 + r − τ_k` of equation (37) is inside `D_{a_nxt_o}V[>]`: the
derivative this stage reads is a derivative with respect to next period's
assets, and the two stages that turn assets into cash, the owner's housing
stage and the tenure stage, are where that factor is written. The solver
places the same factor differently, in the inversion here, at the marginal
tax rate of each point of the savings grid; the composed Euler equation is
the same, and only the line that carries the factor differs. And the
one-sided conditions (38) at a tax threshold are not written: the
continuation value is not differentiable there, so the equality above does
not hold, and the candidates on the segment at each threshold are supplied by
the method, as Box 3 of the paper describes.

## Elaboration

```text
applications/housing-renting/declaration/stages/owner_cons/owner_cons.bl: ElaboratedStage('owner_cons', symbolic)
  view ('field', None): constructed
  view ('operator', 'backward'): constructed
  view ('operator', 'forward'): constructed
```

## Numerical methods

`declaration/stages/owner_cons/methods.bl`, the addition beside the stage file, types the
endogenous grid method on the policy builder, with the savings grid as its grid entry and, as
keyword arguments valued by declared settings, the upper envelope routine, the candidate points
at the borrowing limit and the candidate segments at the tax thresholds; it appends the method's
three lines to the policy block and the envelope line to the decision value builder, and holds
the decision value and its derivative on the cash grid by linear interpolation. The upper
envelope is not a statement of the stage: comparing the candidates is part of realizing the
maximization the first statement declares. The paper's reference solutions replace the whole
selection by value function iteration on a dense grid, the second addition `methods.vfi.bl`,
which a reader names in place of the first.

The `fues_` settings preserve the individual FUES options, and the `tax_` settings preserve the four options for candidates at tax thresholds. The DCEGM and CONSAV selections have no additional options. Each option has its own declared set. This application supplies no numerical handler.
