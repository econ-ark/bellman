---
title: "The renter's consumption stage (renter_cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The renter's consumption stage (renter_cons.bl)

The last stage of a renter's period. The household arrives with the cash the
rental stage left it, the quantity of services it rents and this period's
income, chooses consumption, and carries the rest into the next period as
savings, holding no house. The stage is equation (33) of Dobrescu and
Shanker, §2.3.

It repeats the owner's consumption stage with two differences: housing
services are rented rather than owned, so the services scale `ϑ` multiplies
the quantity in utility, and the household leaves the period with no housing.

The code blocks below quote the stage file beside this page. Where a line
carries a written note, the quote shortens it to `...`.

## Perches

| Perch | What the household knows | Fields |
|---|---|---|
| Decision | Cash, the services rented, this period's income; consumption is chosen here. | `w_d`, `S_d`, `y_d` |
| Continuation | Savings, no housing, this period's income. | `a_nxt_r`, `H_nxt_r`, `y_nxt_r` |

## Declarations

Utility, its derivative in consumption, the inverse of that derivative and
the feasible set are those of the owner's stage. The stage adds

```bl
ϑ : ℝ₊₊      :: ["housing enjoyed per unit of rented services; the printed model is the case ϑ = 1"]
```

Equation (30) of the paper has a renter enjoy the quantity rented, which is
`ϑ = 1`. The solver behind the paper's tables multiplies the quantity by a
parameter it sets to 0.5, in the endogenous grid routine and in the value
function iteration alike, and the notes to Appendix Table 7 list `ϑ = 0.5`.
The stage therefore carries the parameter and `declaration/calibration/housing-renting.yml` sets it to
0.5, so that the file reproduces the published runs and `ϑ = 1` gives the
utility function as printed.

## Blocks

The stage has no arrival perch: it is entered at its decision perch, which
holds what the stage before it leaves, the period's connector joining that
stage's continuation fields `w_rent`, `S_rent` and `y_rent` to the decision states named here. The
decision-to-continuation transition is the budget, and it writes the zero
housing stock a renter carries forward:

```bl
[id=dcsn_to_cntn, (w_d : ℝ₊₊, S_d : ℝ₊, y_d : ℝ₊₊, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_nxt_r : ℝ₊, H_nxt_r : ℝ₊, y_nxt_r : ℝ₊₊) : !cntn] {
    a_nxt_r = w_d - c    :: [id=savings]
    H_nxt_r = 0          :: [id=no_housing, ...]
    y_nxt_r = y_d
}
```

The zero is an equation of the stage and not a value written into a
connector: a connector identifies fields and computes nothing.

The backward blocks, the policy block and the two block files,
`declaration/methods/marginals_renter_cons.bl` and
`declaration/methods/renter_cons_egm.bl`, are those of the owner's stage
with `ϑ*S_d` in place of the housing stock and `a_nxt_r` in place of
`a_nxt_o`. The value line and the maximization stand in the stage file:

```bl
    V = 𝑢(c, ϑ*S_d) + β*V[>]    :: [id=value]
```

```bl
    c = argmax_{c : Γ(w_d)}(𝑢(c, ϑ*S_d) + β*V[>])    :: [id=optimality]
```

The derivative line stands in the marginal block, and the three lines of the
endogenous grid method in the method block:

```bl
    D_{w_d}V = 𝑑𝑢(c)                   :: [id=marginal]
```

```bl
    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a_nxt_r}V[>])                   :: [id=InvEuler]
    w_d[>] = a_nxt_r + c[>]                              :: [id=endoggrid]
    c      = c[>]                                        :: [id=cons_choice]
```

The continuation value is the arrival value of the next period's tenure
stage, read at no housing, so a renter's continuation differs from an
owner's only through the state the inter-period connector supplies. The
reading of the statements is the owner's: the declarative maximization,
then the inverse Euler correspondence, the endogenous grid and the
identification of the control with the candidate.

## Elaboration

```text
applications/housing-renting/declaration/stages/renter_cons/renter_cons.bl: ElaboratedStage('renter_cons', symbolic)
  view ('field', None): constructed
  view ('operator', 'backward'): constructed
  view ('operator', 'forward'): constructed
```

## Numerical methods

`declaration/stages/renter_cons/methods.yml` is the owner's file with the renter's stage name
and block files: the endogenous grid method at the policy block with the same savings grid,
upper envelope and candidate settings, and the decision value and its
derivative on the cash grid. The solver runs the same routine for both
stages, with the services scale and the zero housing stock the only
differences in what it computes.
