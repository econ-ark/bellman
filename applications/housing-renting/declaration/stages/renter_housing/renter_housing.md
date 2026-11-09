---
title: "The renter's rental stage (renter_housing.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The renter's rental stage (renter_housing.bl)

The stage a household reaches when it chooses to rent. It arrives with the
liquid wealth the tenure stage left it, the proceeds of the house included,
and this period's income, and chooses a quantity of housing services to rent
at a fixed price. The stage is equation (35) of Dobrescu and Shanker, §2.3,
with the income and the rent of the renter's budget constraint (29).

The code blocks below quote the stage file beside this page. Where a line
carries a written note, the quote shortens it to `...`.

## Perches

| Perch | What the household knows | Fields |
|---|---|---|
| Decision | Liquid wealth after the house is sold, this period's income; the rental quantity is chosen here. | `w_d`, `y_d` |
| Continuation | The quantity rented and the cash it leaves. | `w_rent`, `S_rent`, `y_rent` |

## Declarations

The rental quantities are a set of the model, `n_S` equally spaced
quantities between `S_min` and `S_max`, and the rental price is a parameter.
The stage has no tax term: the tax was charged in the tenure stage, which is
where the renter's assets were turned into liquid wealth.

```bl
XS := linspace(S_min, S_max, n_S)
P_r   : ℝ₊₊
```

## Blocks

The stage has no arrival perch: it is entered at its decision perch, which
holds what the stage before it leaves, the period's connector joining that
stage's continuation fields `w_r` and `y_r`, the tenure choice's branch `rent`, to the decision states named here.
The decision-to-continuation transition adds income and subtracts the rent,
and its header types the decision states:

```bl
[id=dcsn_to_cntn, (w_d : ℝ₊, y_d : ℝ₊₊, S : XS @ !ctrl) : !dcsn -> (w_rent : ℝ₊₊, S_rent : XS, y_rent : ℝ₊₊) : !cntn] {
    w_rent = w_d + y_d - P_r*S    :: [id=renter_budget, ...]
    S_rent = S
    y_rent = y_d
}
```

Cash is declared strictly positive, as in the owner's housing stage, and the
choice set is never empty because renting nothing leaves the wealth and the
income, which are positive.

The backward block passes the renter's consumption value through
unchanged, and the line the methods file `methods.bl`, the addition beside
this file, appends to that builder's block passes its derivative through:

```bl
    V = V[>]                     :: [id=value]
```

```bl
    D_{w_d}V = D_{w_rent}V[>]    :: [id=marginal, ...]
```

The derivative needs no factor because wealth enters cash one for one. The
derivative of the tenure stage's liquidation, one plus the interest rate less
the marginal tax rate, is applied in the tenure stage, where that law of
motion is written.

The policy block chooses the quantity:

```bl
[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (S : XS @ !ctrl) : !dcsn] {
    S = argmax_{S}(V[>])    :: [id=choice]
}
```

The continuation value is the renter's consumption value read at the cash
each quantity leaves.

## Elaboration

```text
applications/housing-renting/declaration/stages/renter_housing/renter_housing.bl: REFUSED NotConstructed: not-constructed applications/housing-renting/declaration/stages/renter_housing/renter_housing.bl:3:1: no construction rule for the definition 'XS': its right side linspace(S_min, S_max, n_S) is not a function of the stage, and a set defined by a grid constructor is not yet constructed (term address '2'; rule not-constructed)
```

This is the refusal of the owner's housing stage: decision D21 rules the grid
constructor a primitive of the language, and its admission is pending. With
`XS := ℝ₊` in its place the stage constructs its field view and its backward
and forward operator views.

## Numerical methods

`declaration/stages/renter_housing/methods.bl` types the discrete choice over the rental
quantities on the policy builder and the decision value and its derivative held on the cash
grid by linear interpolation, which is how the tenure stage reads the value
of renting at the liquidated wealth.
