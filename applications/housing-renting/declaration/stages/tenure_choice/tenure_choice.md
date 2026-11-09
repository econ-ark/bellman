---
title: "The tenure-choice stage (tenure_choice.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The tenure-choice stage (tenure_choice.bl)

The first stage of the period. The household arrives with financial assets,
a housing stock and last period's income, draws this period's income from the
Markov chain, and chooses whether to own or to rent. Owning leaves assets and
the house untouched for the owner's housing stage; renting sells the house,
so the renter leaves the stage holding liquid wealth alone. The stage is
equation (36) of Dobrescu and Shanker, §2.3, together with the liquidation
term of the renter's budget constraint (29) and the tax schedule (27).

The code blocks below quote the stage file beside this page. Where a line
carries a written note, the quote shortens it to `...`.

## Perches

| Perch | What the household knows | Fields |
|---|---|---|
| Arrival | Last period's income, before this period's draw. | `a`, `H`, `y_pre` |
| Decision | This period's income as well; tenure is chosen here. | `a_d`, `H_d`, `y_d` |
| Continuation | The tenure chosen, and the house sold if it rents. | own: `a_o`, `H_o`, `y_o`; rent: `w_r`, `y_r` |

## Declarations

The interest rate and the tax schedule are parameters; the chain is the pair
`Π`, its transition matrix, and `z`, its levels. A matrix and a vector whose
length the discretisation fixes have no set in the language, so each is
declared in a set that stands in for it, and the annotation says so. The ten
tax brackets, by contrast, are a count of the model, so the three tax
families are declared as products of ten sets and calibration accepts a list
of ten values for each.

```bl
r      : ℝ₊       :: ["interest rate on financial assets"]
Π      : [0,1]    :: ["transition matrix of the income chain, one row for each income level; ..."]
z      : ℝ₊₊      :: ["the income levels of the chain, in the order of the rows of Π; ..."]
a0_T   : ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊ × ℝ₊    :: [...]
```

Income is the level itself, not an index of the chain, which is how the paper
writes it: the shocks take values in a finite subset of the positive reals.
The law names the row it is drawn from:

```bl
y : ℝ₊₊
y ~ MarkovChain(Π, z, y_pre)
```

A distribution declaration is the conditional law of the draw given the
information at the source perch of the edge, and its arguments are what its
formula reads. Writing `y_pre` in the law is therefore what makes the draw a
Markov chain rather than an independent draw; a law that named no state would
be constant in the arrival information.

The tax function is written as the paper's equation (27), bracket by bracket,
with `step(u)`, one for positive `u` and zero otherwise, cutting out each
bracket. Bracket `k` runs from `a0_T[k]`, excluded, to `a0_T[k+1]`, included,
which is the convention of the solver; the paper writes closed intervals,
which do not decide the value at a threshold. The marginal rate is the
derivative of that function, which exists away from the thresholds:

```bl
𝑑𝑇 := D_{x}(𝑇)
```

`step` is not defined in the stage. The construction reads a call to a name
the file does not declare as an external function and records the obligation
to supply its signature and its result set. The language has no relational
expression, so an indicator has no other spelling.

## Blocks

The arrival-to-decision transition carries assets and housing through and
puts the income draw into the decision state:

```bl
[id=arvl_to_dcsn, (a : ℝ₊, H : ℝ₊, y_pre : ℝ₊₊, y) : !arvl -> (a_d : ℝ₊, H_d : ℝ₊, y_d : ℝ₊₊) : !dcsn] {
    a_d = a
    H_d = H
    y_d = y
}
```

Listing `y` on the arrival side makes income an argument of the transition.
It does not say that income is known at arrival: it is drawn on the edge, and
the arrival value integrates it out.

The decision-to-continuation transition is the discrete choice. Its output
side is empty and one labelled block per alternative supplies the
continuation fields, as the branching page writes it. The two alternatives
have separately named fields because each is the entry state of a different
stage:

```bl
[id=dcsn_to_cntn, (a_d, H_d, y_d, d : !ctrl @ {own, rent}) : !dcsn -> ()] {
    [label=own,  () -> (a_o : ℝ₊, H_o : ℝ₊, y_o : ℝ₊₊) : !cntn] {
        a_o = a_d
        H_o = H_d
        y_o = y_d
    }
    [label=rent, () -> (w_r : ℝ₊, y_r : ℝ₊₊) : !cntn] {
        w_r = (1 + r)*a_d - 𝑇(a_d) + H_d    :: [id=liquidation, ...]
        y_r = y_d
    }
}
```

The renter's wealth is assets after the return and the tax plus the proceeds
of the house. Income is not added here: it is added in the renter's rental
stage, which is where the solver adds it.

The first backward block evaluates the choice at a given tenure, and the line
the methods file `methods.bl`, the addition beside this file, appends to that
builder's block states the derivative with respect to the assets held on
arrival:

```bl
    V = (V_o[>], V_r[>])[d]                                         :: [id=choice_value]
```

```bl
    D_{a_d}V = (D_{a_o}V_o[>], (1 + r - 𝑑𝑇(a_d))*D_{w_r}V_r[>])[d]  :: [id=choice_marginal, ...]
```

The bracket after a tuple selects the entry the control names, the first for
`own` and the second for `rent`, in the order the label set declares. The two
branch values are the arrival values of the owner's and the renter's housing
stages. The derivatives are not symmetric because the two branches differ
in what their continuation value is a function of: the owner's is already a
derivative with respect to assets, since the owner's housing stage holds the
transition from assets to cash, while the renter's is a derivative with
respect to the liquid wealth `w_r`, so the derivative of `w_r` in `a_d`,
which is one plus the interest rate less the marginal tax rate, is applied
here. Each stage differentiates its own law of motion.

The second backward block integrates the income draw:

```bl
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = E_{y}(V)     :: [id=value]
}
```

It writes no derivative line: the decision states are the arrival states
unchanged, so the derivative of the arrival value in assets is the
expectation of the decision value's derivative, which the line
`choice_marginal` of the methods file's block `cntn_to_dcsn` states.

Because the law names `y_pre`, the result is a function of last period's
income as well as of assets and housing, which is the state the inter-period
connector supplies.

The policy block compares the two branch values and returns the tenure:

```bl
[id=policy, (V_o[>] : [-inf, inf) @ !vlu, V_r[>] : [-inf, inf) @ !vlu) : !cntn -> (d : {own, rent} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_o[>], V_r[>])    :: [id=choice]
}
```

Its inputs are the two continuation values and nothing else; the decision
state is the argument of the policy the block produces, not an input. The
arguments of the maximisation are the same two values, in the same order, as
the selection in the value equation. Where the two are equal both tenures
maximise, and the rule that picks one is the method's; the solver prefers
renting.

Values are typed on `[-inf, inf)` because utility is logarithmic and is
unbounded below at zero consumption.

## Elaboration

```text
applications/housing-renting/declaration/stages/tenure_choice/tenure_choice.bl: REFUSED NotConstructed: not-constructed applications/housing-renting/declaration/stages/tenure_choice/tenure_choice.bl:32:5: make_stage cannot construct this nested block: task B02 (branching construction) adds its construction rule (term address 'dcsn_to_cntn.own'; rule not-constructed)
```

Task B02 adds the construction of branches. Nothing else in the file is
refused: with the two labelled blocks written as one product output, the
stage constructs its field view and its backward and forward operator views,
the tax function, the derivative, the tuple selections and the Markov law
included.

## Numerical methods

`declaration/stages/tenure_choice/methods.bl` types what the solver does: the discrete choice
between the two values on the policy builder; the expectation over the income chain by
`!markov` at its one occurrence, a sum over the row of the transition matrix, which the solver
computes as a matrix product; and the decision value and its derivative held on the asset
grid by linear interpolation, which is how the renter's value is read at the liquidated
wealth.
