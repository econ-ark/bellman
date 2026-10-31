---
title: "The retiree-consumption stage (retiree_cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The retiree-consumption stage (retiree_cons.bl)

> [!summary]
> This page explains `retiree_cons.bl`, the retiree's consumption stage of
> the retirement model. The code blocks quote the working copy,
> `declaration/stages/retiree_cons/retiree_cons.bl`, and the two block files
> that hold its derivative lines and its endogenous grid method,
> `declaration/methods/marginals_retiree_cons.bl` and
> `declaration/methods/retiree_cons_egm.bl`; when those files change, these
> excerpts and their explanations must change with them. `economics.md` states the whole
> model; `worker_cons.md` explains the worker's consumption stage, whose
> blocks this one follows, and `ret_choice.md` the discrete choice.

## The model

A retiree arrives with assets `a_ret`, earns the gross return `R` on
them, consumes, and carries savings into the next period, where the same
stage receives them again. There is no wage and no further discrete
choice, so the retiree's problem is the concave consumption-savings
problem that Iskhakov, Jørgensen, Rust and Schjerning (2017) write as
their equation (5), whose closed-form solution under log utility they
attribute to Phelps (1962). The decision value is

```text
V(w_ret) = max over c in (0, w_ret] of  𝑢(c) + β*V[>](w_ret - c),
```

and the first-order condition is `𝑑𝑢(c) = β*D_{b_ret}V[>]`, the derivative
of the continuation value read at the savings `b_ret`, the paper's
equation (11) once the return factor of the arrival edge is composed with
it. The paper records that the credit constraint never binds in this
problem, and that under log utility consumption is a fixed share of cash
on hand at each date, the share depending on how many dates remain.

Two routes reach this stage: a worker who chooses to retire this period,
and a retiree from the previous period. The first is a connector within
the period, the second an inter-period connector; `economics.md` states both,
and the question they raise.

## Declarations

```bl
@stage: retiree_cons

Xa := ℝ₊

β : (0,1)        :: ["discount factor"]
R : ℝ₊₊          :: ["gross return on assets"]

𝑢(c : ℝ₊₊) := log(c)                :: [id=util]
𝑑𝑢(c : ℝ₊₊) := 1/c                  :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := 1/x               :: [id=inv_marg_util]
Γ(x : ℝ₊) := (0, x]                 :: [id=feasible, "empty at zero resources"]
```

The declarations are the worker's without the wage. The feasible set is
empty at zero resources, where the retiree has nothing to consume and the
value is minus infinity; that is why the value fields below admit minus
infinity.

## Transitions and value equations

The retiree earns no wage, so cash on hand is the return on assets alone.

```bl
[id=arvl_to_dcsn, (a_ret : Xa) : !arvl -> (w_ret : Xa) : !dcsn] {
    w_ret = R*a_ret                 :: [id=cash_on_hand]
}

[id=dcsn_to_cntn, (w_ret, c : ℝ₊₊ @ !ctrl) : !dcsn -> (b_ret : Xa) : !cntn] {
    b_ret = w_ret - c               :: [id=savings]
}
```

The fields carry the suffix `_ret` because the period holds the worker's
and the retiree's fields at once, and each join between stages must name
one field.

The backward blocks are the worker's. The stage file writes the two value
lines:

```bl
[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}
```

and the derivative lines, the same envelope condition and the same
chain-rule factor in the derivative of the arrival value, stand in the two
marginal blocks of `declaration/methods/marginals_retiree_cons.bl`, which
the methods file binds on the two value blocks with `!marginals`:

```bl
@methods: retiree_cons
# The derivatives of the retiree's two values, each stated by the marginal
# block of the value builder that writes the value. The decision value's line
# is the envelope condition; the arrival value's line keeps the factor R of the
# law w_ret = R*a_ret, which is not the identity.

[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {
    D_{w_ret}V = 𝑑𝑢(c)              :: [id=marginal]
}

[id=arvl_marginal, (V) : !dcsn -> (V[<]) : !arvl] {
    D_{a_ret}V[<] = R*D_{w_ret}V    :: [id=marginal]
}
```

The FUES retirement example carries the return factor inside its inverse
Euler recipe instead, and the identity in the derivative of its arrival
value; the composed Euler equation is the same.

## Policy

```bl
[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(w_ret)}(𝑢(c) + β*V[>])     :: [id=optimality]
}
```

The policy block's one statement is the definition of the control, the
maximizer over the feasible set. The endogenous grid method that computes
it is the method block `egm` of `declaration/methods/retiree_cons_egm.bl`,
which the methods file binds on the policy builder:

```bl
@methods: retiree_cons
# The endogenous grid method as the method block of the retiree's policy
# builder, whose stage file states the maximization alone. The candidate line
# reads the derivative of the continuation value by the term D_{b_ret}V[>].

[id=egm, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn, "method = egm! will look for policy[>] and x[>] grid and invert it. Important here that the grids contain all constrained sections"] {
    c[>]     <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b_ret}V[>])                :: [id=InvEuler, "Implies a correspondence: where equality holds, c[>] takes on a single value, where inequality holds, it is multiple values"]
    w_ret[>] = b_ret + c[>]                          :: [id=endoggrid]
    c        = c[>]                                  :: [id=cons_choice]
}
```

Its first two statements are the endogenous grid method's candidate and
its cash-on-hand coordinate, and the last identifies the control with the
candidate at its own saving, an implicit equation in consumption through
the budget identity `b_ret = w_ret - c`. The candidate line reads the
derivative of the continuation value by the term `D_{b_ret}V[>]`, and the
header lists the continuation value and the control alone.

The retiree's continuation value is concave, so the coordinates do not
fold back, the candidates define one consumption at each cash on hand,
and no envelope operation is needed. This is the only difference from the
worker's method block.

The two quoted strings are notes retained with the lines they describe:
the first, on the method block's header, records what an endogenous-grid
method reads from the block, the second the reading of the inequality as a
correspondence, single-valued where the Euler equation holds with equality
and a segment where the borrowing constraint binds.

## Numerical method

`declaration/stages/retiree_cons/methods.yml` attaches the endogenous grid method
to the policy block with the method block of `retiree_cons_egm.bl`, whose
lines then form the policy builder's operations; the two marginal blocks
of `marginals_retiree_cons.bl` to the two value blocks with `!marginals`;
and a tabulation on the retiree's asset grid to the arrival value and to
the stated derivative of the arrival value.

## Elaboration

The stage is constructed:

```text
applications/retirement-choice/declaration/stages/retiree_cons/retiree_cons.bl: ElaboratedStage('retiree_cons', symbolic)
```

## References

- Iskhakov, F., Jørgensen, T. H., Rust, J., and Schjerning, B. (2017).
  "The endogenous grid method for discrete-continuous dynamic choice
  models with (or without) taste shocks." *Quantitative Economics* 8(2),
  317–365. Equation (5) is the retiree's Bellman equation, equation (11)
  its Euler equation, and section 2.2 the closed-form policy in the last
  periods.
- Dobrescu, L. I., and Shanker, A. "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN No.
  4181302.
