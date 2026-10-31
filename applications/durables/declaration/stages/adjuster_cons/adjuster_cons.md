---
title: "The adjuster's consumption stage (adjuster_cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The adjuster's consumption stage (adjuster_cons.bl)

> [!summary]
> `adjuster_cons.bl` is the problem of a household that has just sold its house:
> it chooses consumption and a new housing stock out of total wealth, and
> carries savings and that stock into the next period. The stage file states
> the two choices together as one maximization; the method block of
> `declaration/methods/adjuster_cons_egm.bl` solves for them as one solution
> statement with two unknowns, and the marginal block of
> `declaration/methods/marginals_adjuster_cons.bl` states the derivative of the
> value; the elaboration is quoted at the end of this page. The economic
> environment and the composition of the stages are in `economics.md`.

> [!note]
> The stage constructs and reaches the specified version; bound with its
> methods file, its joint choice is read as a solution statement with two
> unknowns.

## What the stage does

The household enters the stage at its decision perch with the total wealth and
the income state that the adjust branch of the tenure stage produced: the house
has been sold, so wealth is one number. Nothing is drawn inside the stage, so
the stage has no arrival perch: the period's connector joins the branch's
fields `w_adj` and `z_adj` to the decision states `m` and `z_d`. The household
chooses consumption `c` and the new stock `h_choice`, paying `1 + τ` per unit
of housing, and the continuation state is savings, the new stock and the income
state. The new stock
is what utility is over, because utility is over consumption and the housing
held at the end of the period.

| Perch | What the household knows | Fields |
|---|---|---|
| Decision | Total wealth and the income state; consumption and the new house are chosen here. | `m`, `z_d`, and the controls `c`, `h_choice` |
| Continuation | Savings, the new housing stock and the income state. | `a_nxt_adj`, `h_nxt_adj`, `z_nxt_adj` |

## Declarations

The parameters are those of the keeper's stage and the adjustment cost. Utility
and its derivatives are the same closed forms, since both stages are the same
household in the same period.

```bl
β   : (0,1)       :: ["discount factor"]
α   : (0,1)       :: ["weight of consumption in utility"]
γ_c : (1, inf)    :: ["curvature of utility from consumption"]
γ_h : (1, inf)    :: ["curvature of utility from housing services"]
κ   : ℝ₊₊         :: ["housing services per unit of the housing stock"]
τ   : ℝ₊₊         :: ["cost of adjusting housing, per unit of housing bought"]
```

The feasible set is written as two correspondences, read in the order the
maximisation binds them: consumption lies in the interval up to total wealth,
and the new stock in the interval up to what wealth is left, divided by the unit
price.

```bl
Γ_c(x : ℝ₊₊) := (0, x]                                                    :: [id=feasible_consumption]
Γ_h(x : ℝ₊) := (0, x/(1 + τ)]                                             :: [id=feasible_housing]
```

Together they are the set of pairs with positive consumption, a positive house
and non-negative savings, which is the model's constraint. At the upper endpoint
of the first interval the second is empty, so the pair of intervals states the
budget exactly; the endpoints are closed because the grammar writes an interval
open at the left only, and the set that closes at the right differs from the
model's by a boundary the household never chooses.

## Transitions

The decision edge is the budget; its header types the decision states, which
no arrival block declares.

```bl
[id=dcsn_to_cntn, (m : ℝ₊₊, z_d : ℝ₊₊, c : ℝ₊₊ @ !ctrl, h_choice : ℝ₊₊ @ !ctrl) : !dcsn -> (a_nxt_adj : ℝ₊, h_nxt_adj : ℝ₊₊, z_nxt_adj : ℝ₊₊) : !cntn] {
    a_nxt_adj = m - c - (1 + τ)*h_choice               :: [id=savings]
    h_nxt_adj = h_choice                               :: [id=housing]
    z_nxt_adj = z_d                                    :: [id=income_state]
}
```

Savings are declared non-negative, so the budget equation and the declared sets
state the constraint the feasible sets above repeat for the maximisation.

## Values

The backward block states current utility plus the discounted continuation
value. The decision value is the value the stage exports, which the tenure
stage reads on the adjust branch.

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c, h_choice) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c, h_choice) + β*V[>]                        :: [id=value]
}
```

The derivative of the decision value with respect to wealth, which is the one
derivative the tenure stage reads on this branch, is stated by the marginal
block of `declaration/methods/marginals_adjuster_cons.bl`, which the methods file
binds on the decision value builder with `!marginals`. The line is the envelope
condition at the chosen consumption.

```bl
[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {
    D_{m}V = 𝑢_c(c)                                    :: [id=marginal_wealth]
}
```

The adjuster needs no derivative of the value in housing: it enters the period
with wealth only, and the tenure stage values an extra unit of housing on this
branch by its resale value times the derivative of the value in wealth.

## Policy

The policy block of the stage file states the choice alone.

```bl
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl, h_choice : ℝ₊₊ @ !ctrl) : !dcsn] {
    (c, h_choice) = argmax_{c : Γ_c(m), h_choice : Γ_h(m - c)}(𝑢(c, h_choice) + β*V[>])        :: [id=optimality]
}
```

The line defines the two controls together as the maximiser over the feasible
set. The two controls are bound in the order in which the feasible sets are
read, the set of the new stock reading the consumption bound before it, and the
tuple on the left lists them in that same order.

The method block `egm` of `declaration/methods/adjuster_cons_egm.bl`, which the
methods file binds on the policy builder with `!egm`, holds the endogenous grid
method of Box 2 of the paper, written on the continuation state.

```bl
[id=egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl, h_choice : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>]          <= 𝑢_c_inv(β*D_{a_nxt_adj}V[>])                                              :: [id=InvEuler]
    m[>]          = a_nxt_adj + c[>] + (1 + τ)*h_nxt_adj                                       :: [id=endoggrid]
    (c, h_choice) = solve_{c, h_choice}(c - c[>], (1 + τ)*𝑢_c(c) - 𝑢_h(h_choice) - β*D_{h_nxt_adj}V[>])   :: [id=choice]
}
```

The first line inverts the Euler equation for assets, reading the derivative of
the continuation value in savings by the term `D_{a_nxt_adj}V[>]`: as an
inequality it defines candidate consumption as a single value wherever saving is
positive and a segment at zero saving, so the borrowing constraint stays in the
method block. The second recovers the total wealth at which a candidate is
optimal by inverting the budget. The third is the pair of first-order
conditions in the two unknowns: the first residual identifies
consumption with the candidate, which read through the budget is the asset Euler
equation; the second is the housing condition, which equates the marginal cost of
a unit of housing, `(1 + τ)` times the marginal utility of consumption, to its
marginal benefit, the housing services of this period plus the discounted
marginal value of carrying the stock forward.

The two conditions are one system, not two equations solved in turn: each
residual reads both unknowns through the budget, and the method finds the pairs
that satisfy them both. That is why they are written as one solution statement
with two unknowns.

Where the paper's method fixes a grid of new housing and finds the roots in
savings along it, that is a realisation of this system: the exogenous grid and
the search for roots are settings of the method in
`declaration/stages/adjuster_cons/methods.yml`.
The candidates it produces are several at one wealth, because the policy is not
monotone, and the upper envelope that selects among them is a step of the
method; no line of the stage authors it.

## Elaboration

```text
applications/durables/declaration/stages/adjuster_cons/adjuster_cons.bl: ElaboratedStage('adjuster_cons', symbolic)
```

The joint maximisation `policy.optimality` states the problem, and the policy
builder the stage file declares is formed from it: a Pullback, an Aggregation,
the Argmax over the two feasible sets, and the Evaluation. With
`declaration/calibration/durables.yml`, `declaration/stages/adjuster_cons/methods.yml`
and `declaration/settings/durables.yml` attached, the method block opens the
policy builder: its joint `solve` statement `policy.choice` is read as one
Aggregation whose rule is the residual system with the two unknowns `c` and
`h_choice`, and the marginal block's derivative line stands at the Evaluation of
the decision value builder, beside the value's representation. The stage
reaches the specified version:

```text
ElaboratedStage('adjuster_cons', specified)
policy                    !egm   block ../../methods/adjuster_cons_egm.bl
cntn_to_dcsn:Evaluation   !marginals   block ../../methods/marginals_adjuster_cons.bl
cntn_to_dcsn:Evaluation   !Linear
```

The stage parses, and its parsed tree is recorded in
`packages/bellman/tests/snapshot/corpus/durables/adjuster_cons.bl.ast.json` and
checked by the structural test.

Writing the two choices as nested maximisations, one over housing of the
maximum over consumption, would state the problem in a form the paper does not
use. Checked with the present package on a copy of the file (the joint lines
replaced by `h_choice = argmax_{h_choice : Γ_h(m)}(max_{c : Γ_c(m - (1 + τ)*h_choice)}(…))`
and a second `argmax` over consumption), that form parses and is refused at
construction under `not-constructed`: the operator `max` has no supported
output-context rule, at `policy.optimality`.

## References

- Dobrescu, L. I. and Shanker, A. (2026). "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN 4181302,
  Section 2.2 and Box 2.
- Druedahl, J. and Jørgensen, T. H. (2017). "A general endogenous grid method for
  multi-dimensional models with non-convexities and constraints." *Journal of
  Economic Dynamics and Control* 74, 87–107.
- Iskhakov, F. (2015). "Multidimensional endogenous gridpoint method: solving
  triangular dynamic stochastic optimization problems without root-finding
  operations." *Economics Letters* 135, 72–76.
