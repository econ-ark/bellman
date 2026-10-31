---
title: "The owner's housing stage (owner_housing.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The owner's housing stage (owner_housing.bl)

The stage a household reaches when it chooses to own. It arrives with assets,
the housing stock it holds and this period's income, and chooses the housing
size it will hold at the end of the period. Changing the size costs a
transaction fee on the size bought, so the choice is between keeping the
house and paying that fee. The stage is equation (34) of Dobrescu and
Shanker, §2.3, with the owner's budget constraint (28).

The code blocks below quote the stage file beside this page. Where a line
carries a written note, the quote shortens it to `...`.

## Perches

| Perch | What the household knows | Fields |
|---|---|---|
| Decision | Assets, the stock held, this period's income; the housing size is chosen here. | `a_d`, `H_d`, `y_d` |
| Continuation | The size chosen and the cash it leaves. | `w_own`, `H_own`, `y_own` |

## Declarations

The housing sizes are a set of the model, not a numerical grid: the household
may hold `n_H` equally spaced sizes between `H_min` and `H_max`, and those
three are parameters.

```bl
XH := linspace(H_min, H_max, n_H)
```

The tax schedule is declared and defined as in the tenure stage, since a
stage file is self-contained. The expense of a housing trade is a function of
the stock held and the stock chosen:

```bl
𝛷(h : ℝ₊, h_n : ℝ₊) := (step(h_n - h) + step(h - h_n))*((1 + φ)*h_n - h)
```

The two `step` terms are the indicator that the stock changes, one when
`h_n` and `h` differ and zero when they agree, so the expense is the purchase
price with its transaction cost less the value of the stock sold, and zero
when the stock is kept. This is the function the paper writes `Φ` in equation
(37), and it is what the solver computes.

## Blocks

The stage has no arrival perch: it is entered at its decision perch, which
holds what the stage before it leaves, the period's connector joining that
stage's continuation fields `a_o`, `H_o` and `y_o`, the tenure choice's branch `own`, to the decision states named here.
The decision-to-continuation transition is the owner's budget, and its
header types the decision states:

```bl
[id=dcsn_to_cntn, (a_d : ℝ₊, H_d : ℝ₊, y_d : ℝ₊₊, H_new : XH @ !ctrl) : !dcsn -> (w_own : ℝ₊₊, H_own : XH, y_own : ℝ₊₊) : !cntn] {
    w_own = (1 + r)*a_d - 𝑇(a_d) + y_d - 𝛷(H_d, H_new)    :: [id=owner_budget, ...]
    H_own = H_new
    y_own = y_d
}
```

Cash is assets after the return and the tax, plus income, less the housing
expense. The paper requires this cash to be non-negative; it is declared
strictly positive here, which removes only the sizes at which no positive
consumption is feasible and the value is minus infinity. Keeping the house
costs nothing, and at this calibration the tax never exceeds the return on
assets, so the cash of that size is at least this period's income, which is
positive: the choice set is never empty.

The backward block passes the owner's consumption value through:

```bl
[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, H_new) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = V[>]                                      :: [id=value]
}
```

The marginal block of `declaration/methods/marginals_owner_housing.bl`,
which the methods file binds on this builder with `!marginals`, turns the
derivative of that value with respect to cash into a derivative with respect
to assets:

```bl
[id=dcsn_marginal, (V[>]) : !cntn -> (V) : !dcsn] {
    D_{a_d}V = (1 + r - 𝑑𝑇(a_d))*D_{w_own}V[>]    :: [id=marginal, ...]
}
```

The factor is the derivative of the budget above in `a_d`. It is the factor
that appears in the Euler equation (37) of the paper as `1 + r − τ_k`, and it
is written in this stage because this is the stage whose law of motion turns
assets into cash. The marginal tax rate is undefined at a bracket threshold,
so this derivative holds away from the thresholds, as (38) records.

The policy block chooses the size:

```bl
[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (H_new : XH @ !ctrl) : !dcsn] {
    H_new = argmax_{H_new}(V[>])    :: [id=choice]
}
```

The continuation value is the owner's consumption value, read at the cash
each size leaves, which is what the substitution of the law of motion does.
The feasible set of the maximisation is the declared set of sizes; the
requirement that cash be positive is carried by the declared set of `w_own`,
since the language has no comprehension with which to write the sizes whose
cash is positive at a given state.

## Elaboration

```text
applications/housing-renting/declaration/stages/owner_housing/owner_housing.bl: REFUSED NotConstructed: not-constructed applications/housing-renting/declaration/stages/owner_housing/owner_housing.bl:3:1: no construction rule for the definition 'XH': its right side linspace(H_min, H_max, n_H) is not a function of the stage, and a set defined by a grid constructor is not yet constructed (term address '2'; rule not-constructed)
```

Decision D21 rules that `linspace(lo, hi, n)` in set position is a primitive
set constructor of the language and that its count is a parameter, because no
continuous space is being discretised: the household really does have `n_H`
sizes to choose from. Its admission is pending, and until it lands this stage
stops at line 3. With `XH := ℝ₊` in its place, the stage constructs its field
view and its backward and forward operator views, the tax function, the
expense function and the discrete maximisation included.

## Numerical methods

`declaration/stages/owner_housing/methods.yml` records the search over the sizes at the policy
block and the decision value and its derivative held on the asset grid by
linear interpolation. The solver reads the consumption value at the cash each
size leaves by interpolating on the cash grid, which belongs to the owner's
consumption stage.
