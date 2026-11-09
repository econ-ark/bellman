---
title: "The worker-consumption stage (worker_cons.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The worker-consumption stage (worker_cons.bl)

> [!summary]
> This page explains `worker_cons.bl`, the worker's consumption stage of
> the retirement model, for readers new to Bellman-SYM, the language used
> for `.bl` stage files. The code blocks quote the working copy,
> `declaration/stages/worker_cons/worker_cons.bl`, and the methods file
> beside it, `declaration/stages/worker_cons/methods.bl`, which holds its
> derivative lines, its endogenous grid method and the representation of its
> arrival value; when those files change, these
> excerpts and their explanations must change with them. `economics.md` states the whole model;
> `ret_choice.md` explains the discrete-choice stage and `retiree_cons.md`
> the retiree's consumption stage.

## The model

The stage is the worker's consumption problem in the retirement model of
Iskhakov, Jørgensen, Rust and Schjerning (2017), in the staged form the
fast upper envelope scan of Dobrescu and Shanker solves. It is the
log-utility version without taste shocks. Within the period a worker
arrives with assets `a_w`, earns the gross return `R` on them and the
wage `y` to form cash on hand `w = R*a_w + y`, consumes `c`, and carries
end-of-period savings `b = w - c` into the next period. The worker's
decision value is

```text
V(w) = max over c in (0, w] of  𝑢(c) + β*V[>](w - c),
```

where `V[>]` is the continuation value of holding savings `b`. At an
interior choice the first-order condition is `𝑑𝑢(c) = β*D_{b}V[>]`, the
derivative of the continuation value read at the savings `b`, and where
the borrowing constraint binds marginal utility exceeds the discounted
marginal value of saving. Composed across the period, this is the Euler
equation `u'(c) ≥ β*R*u'(c')` of the paper, since the return factor
stands in the derivative of this stage's arrival value.

The continuation value is the value of entering the next period's choice
stage with savings `b`. That link is specified in the period and the
trellis, not in this file. The work disutility `δ` does not appear in
this stage: it is charged once, in the choice stage's value selection.

The option to retire in future periods makes `V[>]` non-concave. It is
the pointwise maximum of concave values, one for each feasible future
sequence of work and retirement, which is the source of the secondary
kinks that Iskhakov, Jørgensen, Rust and Schjerning (2017) describe in
their sections 2.1 and 2.2. The
endogenous grid method inverts the first-order condition on a grid of
savings; where `V[>]` is non-concave the resulting cash-on-hand
coordinates fold back on themselves and the candidate points form a
correspondence rather than a function. Only the candidates on the upper
envelope of the value correspondence are optimal. The fast upper envelope
scan recovers that envelope in a single ordered pass; in the method block
of this stage the envelope is written as its own operation.

## Declarations

`Xa := ℝ₊` defines a named set, reused wherever the block headers need
the asset domain. The parameters follow, each declared by a name, a colon
and a type. The discount factor lies in the open unit interval; the wage
is strictly positive, so cash on hand is positive even at zero assets.

```bl
@stage: worker_cons

Xa := ℝ₊

β : (0,1)        :: ["discount factor"]
R : ℝ₊₊          :: ["gross return on assets"]
y : ℝ₊₊          :: ["wage paid in a period of work"]
```

Here `y` is a parameter: the wage is constant and there is no income
risk. A name becomes a shock only through a tilde line assigning it a
law, and no tilde line appears in this file.

## Utility functions

A function is declared by a name, a parenthesised typed argument, and a
defining expression after `:=`. Mathematical italics are an authoring
convention, but the glyph is part of the identifier: `𝑢` and `u` are
different names. The feasible set of consumption is a correspondence
whose body is a set rather than a formula.

```bl
𝑢(c : ℝ₊₊) := log(c)                :: [id=util]
𝑑𝑢(c : ℝ₊₊) := 1/c                  :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := 1/x               :: [id=inv_marg_util]
Γ(x : ℝ₊₊) := (0, x]                :: [id=feasible]
```

Marginal utility and its inverse are written in closed form. Under log
utility both are `1/·`, which is why the inverse Euler statement of the
method block needs no numerical root finding. The stage file defines them
although none of its own lines calls them: the two block files call them,
and a block file reads the stage's definitions. They can also be written
with the derivative and inverse operators, `𝑑𝑢 := D_{c}(𝑢)` and
`𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)`, as other stages of this corpus do; with that spelling
the stage elaborates and its methods file binds as well.

## Transitions and value equations

Each block header lists its inputs and outputs and marks each side with a
perch, one of the stage's three information sets: arrival, decision or
continuation, written `!arvl`, `!dcsn` and `!cntn`. The forward
transitions state the budget.

```bl
[id=arvl_to_dcsn, (a_w : Xa) : !arvl -> (w : ℝ₊₊) : !dcsn] {
    w = R*a_w + y                   :: [id=cash_on_hand]
}

[id=dcsn_to_cntn, (w, c : ℝ₊₊ @ !ctrl) : !dcsn -> (b : Xa) : !cntn] {
    b = w - c                       :: [id=savings]
}
```

The arrival field is named `a_w`, the name of the work branch of the
choice stage, so that the two join within the period without a rename.
Because `b` is declared on `Xa = ℝ₊`, consumption must satisfy `c ≤ w`:
the domains of the transition state the borrowing constraint, and the
feasible set `Γ(w) = (0, w]` in the policy block states the same
restriction where the control is chosen.

The first backward block defines the decision value. The value fields
are typed on the half-open interval `[-inf, inf)`: a bracket includes its
endpoint and a parenthesis excludes it, so the type admits minus infinity
and excludes plus infinity. The lower endpoint must be admitted because
log utility is unbounded below.

```bl
[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}
```

The second backward block maps the value to its arrival counterpart. No
expectation appears because the stage has no shock.

```bl
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}
```

The derivatives of the two values are not written in the stage file. They
stand in the methods file `declaration/stages/worker_cons/methods.bl`, an
addition to the stage file: a `.bl` file that opens with `@methods:`, read
with the stage file, whose blocks name blocks of the stage by their ids and
add their entries and their lines to them. Its blocks `cntn_to_dcsn` and
`dcsn_to_arvl` each append one derivative line, and the second also
carries, in its bracket, one representation of the arrival value and of its
stated derivative on the asset grid: the method `!Linear`, the grid
`!Cartesian(a_w=(a_min, a_max, n_a))` and the handler, the routine outside
the language that executes the method:

```bl
[id=cntn_to_dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | evaluate.method : !Linear | evaluate.grid : !Cartesian(a_w=(a_min, a_max, n_a)) | evaluate.handler : "dcsmm:interp_as_2"] {
    D_{a_w}V[<] = R*D_{w}V          :: [id=marginal]
}
```

At the selected optimum, differentiating the decision value with respect
to cash on hand gives `D_{w}V = 𝑑𝑢(c)`, which is the envelope condition.
The line records the intended derivative relation; it does not prove it,
and the stage lists the reading as the obligation `marginal-reading`,
which nothing checks. The factor `R` in the derivative of the arrival
value is the derivative of cash on hand with respect to arrival assets,
the chain rule applied to the arrival transition.

Placing the gross return here is a convention: it gives the inverse Euler
statement its simple form `𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])`. The FUES retirement
example places the same factor differently, writing
`1/(β*(1+r)*D_{b}V[>])` in its inverse Euler and the identity in the
derivative of its arrival value. Composed across the period the two
placements give the same Euler equation `u'(c) = β*R*u'(c')` at interior
choices; only the line carrying the factor differs.

## Policy

The policy block states how consumption is chosen:

```bl
[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(w)}(𝑢(c) + β*V[>])        :: [id=optimality]
}
```

and the block `policy` of the methods file, whose bracket types the builder
with `!egm`, its grid on the savings `b` and its handler, and the operator
`upper_env` of its last line with the fast upper envelope scan and its
threshold `m_bar`, states how the endogenous grid method computes it; the
four settings the file reads are declared above it with their sets:

```bl
n_a : ℕ              :: ["number of points of the asset grid"]
a_min : Xa           :: ["lower bound of the asset grid"]
a_max : Xa           :: ["upper bound of the asset grid"]
m_bar : ℝ₊₊          :: ["jump-detection threshold of the upper envelope scan"]

[id=policy, method : !egm | grid : !Cartesian(b=(a_min, a_max, n_a)) | handler : "asva:make_egm_1d"
    | upper_env.method : !FUES(m_bar=m_bar) | upper_env.handler : "dcsmm:EGM_UE"] {
    c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])                 :: [id=InvEuler]
    w[>] = b + c[>]                            :: [id=endoggrid]
    v[>] = 𝑢(c[>]) + β*V[>]                    :: [id=cand_value]
    c    = upper_env(w[>], c[>], v[>])          :: [id=envelope]
}
```

The input of the policy block is the continuation value alone, and no
continuation state: the decision state is the argument of the policy the
block produces, and the savings at which the candidates are computed are
the bound argument of those functions. The block of the methods file
carries no signature, since it adds no coordinate; its lines read the
derivative of the continuation value by the term `D_{b}V[>]`, and `V[>]`
itself because the envelope compares candidate values, not only candidate
consumptions.

The policy block's one statement is the definition of the control:
consumption maximizes current utility plus discounted continuation value
over the feasible set `Γ(w) = (0, w]`. The four statements of the methods
file's block are one realization of it, which stand in place of the
maximization at the operative level while the declared level keeps it; the
stage records the condition under which they reach it as the obligation
`egm-eligibility`, which nothing checks.

The first statement of that block inverts the first-order
condition. It is written as an inequality, which defines candidate
consumption as a correspondence:
marginal utility is at least the discounted marginal value of saving,
with equality wherever saving is positive. At zero saving the candidate
is the whole segment from zero up to the consumption the Euler equation
implies there, and the second statement maps that segment onto the corner
of the policy, so the constrained points belong to the endogenous grid
rather than to a separate case added by the method.

The second statement uses the budget constraint to recover the cash on
hand at which each candidate is optimal, and the third computes the
candidate's value, the utility of candidate consumption plus the
discounted continuation value. This line exists because the first-order
condition alone does not select the optimum when the continuation value
is non-concave: each candidate satisfies it on one of the concave pieces
whose pointwise maximum forms `V[>]`, and the optimal candidates are
found by comparing values.

The last statement selects among the candidates by value and defines the
control: at each cash on hand, `upper_env` takes the candidate with the
largest value and returns its consumption. Writing the envelope in the
block makes the method correct as written; which routine computes it is
the handler the same file binds on the operator `upper_env`.

## Numerical method

The methods file `declaration/stages/worker_cons/methods.bl` types the
policy builder with the endogenous grid method, whose four lines form the
policy builder's operations, with its grid of savings and its handler;
types the envelope operation of its last line with the fast upper envelope
scan, with the jump-detection threshold `m_bar` as its keyword argument;
appends the two derivative lines to the two value blocks; and represents the
arrival value and its stated derivative on the asset grid by linear
interpolation. The file is read with the stage file at every occurrence of
the retirement trellis (`economics.md`, "Elaboration").

## Elaboration

The stage is constructed:

```text
applications/retirement-choice/declaration/stages/worker_cons/worker_cons.bl: ElaboratedStage('worker_cons', symbolic)
```

At the primitive grain the policy builder opens into four boxes: a
pullback of the continuation value, the aggregation and the argmax of the
maximization, and the evaluation. With the methods file read, its four
boxes are those of the method: an aggregation for
candidate consumption, one aggregation for its cash-on-hand coordinate
and its value together, the pullback the envelope statement denotes,
which reads the three candidate functions and returns consumption, and
the evaluation. The policy builder's card prints the envelope's rule as
`𝑐(w) = UNRESOLVED[upper_env; mathematical definition]`: the construction
records `upper_env` as an external callable whose definition must be
supplied.

An earlier version of this file returned the refined grid and consumption
from the envelope and then defined the policy as a function inside the
block, `𝑐(x : ℝ₊₊) := evaluate(w_e[>], c_e[>], x)`, applied at `c = 𝑐(w)`.
Both spellings are refused: a statement whose left side is a tuple has no
construction rule, and neither has a function definition inside a block.
The road-map brief `in-block-function-definitions-and-policy-input-perches`
records the second question and its options.

## References

- Iskhakov, F., Jørgensen, T. H., Rust, J., and Schjerning, B. (2017).
  "The endogenous grid method for discrete-continuous dynamic choice
  models with (or without) taste shocks." *Quantitative Economics* 8(2),
  317–365. Section 2.2 gives the Euler equations (10) and (11), the
  exogenous grid over savings, and the treatment of the credit
  constraint.
- Dobrescu, L. I., and Shanker, A. "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN No.
  4181302. Application 1 is this model; the scan and its jump-detection
  threshold are stated there.
- Carroll, C. D. (2006). "The method of endogenous gridpoints for solving
  dynamic stochastic optimization problems." *Economics Letters* 91(3),
  312–320.
