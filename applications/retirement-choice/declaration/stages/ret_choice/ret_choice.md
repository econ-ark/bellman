---
title: "The retirement-choice stage (ret_choice.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The retirement-choice stage (ret_choice.bl)

> [!summary]
> This page explains `ret_choice.bl`, the discrete-choice stage of the
> retirement model, for readers new to Bellman-SYM, the language used for
> `.bl` stage files. The code blocks quote the working copy,
> `declaration/stages/ret_choice/ret_choice.bl`, and the methods file beside
> it, `declaration/stages/ret_choice/methods.bl`, which holds its derivative
> line and its method; when those files change, these excerpts and their
> explanations must change
> with them. `economics.md` states the whole model, its
> period and its calibration; `worker_cons.md` and `retiree_cons.md`
> explain the two consumption stages.

## The model

The stage comes from the retirement model of Iskhakov, Jørgensen, Rust
and Schjerning (2017), in the staged form the fast upper envelope scan of
Dobrescu and Shanker solves. An agent lives a finite number of periods,
holds assets `a ≥ 0`, consumes, and chooses whether to work. Working pays
a constant wage `y` at a utility cost `δ`; retirement is permanent. In
these files the choice is made at the start of each period and governs
that same period: a worker's wage enters the period's cash on hand, and
the disutility is charged in the period's choice value. The paper charges
its own disutility one period earlier, so the two recursions agree when
the paper's cost equals `β` times the cost written here; `economics.md`
carries that correspondence and the other differences from the paper.
The paper studies the model with and without taste shocks, and these
files encode the version without them, so the discrete choice below is a
deterministic comparison of two values.

In Bellman-SYM a period is decomposed into stages, each a self-contained
subproblem. This file is the choice stage: the agent compares the value
of working against the value of retiring, at unchanged assets, and
selects the work status `d`. Consumption is chosen in separate stages,
the worker's in `worker_cons.bl` and the retiree's in `retiree_cons.bl`.
The value of each branch is the value of entering the corresponding
consumption stage, that is its arrival value.

The permanence of retirement is not written inside this file. It is a
property of how stages are connected: a retiree's assets pass to the
retiree consumption stage and never return to this choice. That
connection belongs to the period and the trellis, not to any single
stage file.

## Declarations

The first line names the stage. The stage has one parameter, the utility
cost of working, declared by a name, a colon and a type: `δ : ℝ₊₊` states
that `δ` is a strictly positive real, as the paper assumes. Its numerical
value is supplied separately, by calibration. The paper writes this cost
`δ`; the calibration file of the FUES retirement example names it
`delta`, and the working paper of Dobrescu and Shanker writes `τ`.

```bl
@stage: ret_choice

δ : ℝ₊₊          :: ["utility cost of working, charged in the period whose wage it earns"]
```

The quoted note is documentation. A declaration carries no annotation in
the constructed stage, so the note lives in the source text alone.

## Transitions and value equations

Each block header lists its inputs and outputs and marks each side with a
perch. A **perch** is one of the stage's three information sets: arrival,
decision, or continuation. The vocabulary words `!arvl`, `!dcsn` and
`!cntn`, written after a side's closing parenthesis, locate that side at
the corresponding perch. Inside a side, a colon after a name gives that
field's set: in `(a : ℝ₊) : !arvl`, the set `ℝ₊` applies to `a` and the
side sits at arrival. [Stages](../../../../../docs/Bellman-Sym/01-stage.md) states
the typing rules in full.

A stage file has five blocks with fixed identifiers: `arvl_to_dcsn` and
`dcsn_to_cntn` are the forward transitions; `cntn_to_dcsn` and
`dcsn_to_arvl` are the backward value blocks; and `policy` is the policy
block.

The arrival-to-decision transition is the identity: nothing happens to
assets before the choice.

```bl
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a                                   :: [id=assets]
}
```

The decision-to-continuation transition introduces the control. The
declaration `d : !ctrl @ {work, retire}` gives `d` a type built from two
components joined by `@`: the vocabulary word `!ctrl` marks `d` as the
stage's control, and `{work, retire}` is the finite set of options. The
components of a type are unordered.

```bl
[id=dcsn_to_cntn, (a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    [label=work,   () -> (a_w : ℝ₊) : !cntn] { a_w = a_d }
    [label=retire, () -> (a_r : ℝ₊) : !cntn] { a_r = a_d }
}
```

The outer header's output side is the empty pair of parentheses: this
transition produces no single continuation state. Instead the body
contains one labelled block per branch, each with its own header and its
own continuation side. Each branch copies assets unchanged into its own
continuation field, `a_w` or `a_r`. The two fields are distinct because
each is the entry state of a different stage: `a_w` is the state at which
the worker's consumption stage is entered, `a_r` the state at which the
retiree's is. This is the branching form ruled canonical for the
language; [Branching](../../../../../docs/Bellman-Sym/05-branching.md) states it.

The first backward block evaluates the choice at a given `d`.

```bl
[id=cntn_to_dcsn, (V_w[>] : [-inf, inf) @ !vlu, V_r[>] : [-inf, inf) @ !vlu, d) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = (V_w[>] - δ, V_r[>])[d]                   :: [id=choice_value]
}
```

The mark `[>]` after a name is the continuation perch mark: `V_w[>]` is
the continuation value of the work branch and `V_r[>]` that of the retire
branch, each the arrival value of the consumption stage that branch leads
to. Each is typed with the half-open interval `[-inf, inf)`, which admits
minus infinity because log utility is unbounded below; a retiree who
arrives with no assets has no feasible consumption. The word `!vlu` marks
the value role.

The right-hand side is a tuple selection. A parenthesised, comma-separated
list is a tuple, a finite family of expressions, and a bracket after it
selects one entry. Here `d` ranges over `{work, retire}`, so
`(V_w[>] - δ, V_r[>])[d]` is the work branch's value net of the work
disutility when `d = work`, and the retire branch's value when
`d = retire`.

The disutility `δ` is charged here and only here. The worker's
consumption stage contains no `δ` term; charging the cost in both stages
would count it twice. The numerical implementation of the FUES example
places the same charge inside the worker's consumption operators and then
takes a plain maximum in the choice step. Both placements charge the cost
exactly once and give the same choice value.

The decision-to-arrival block is the identity, matching the identity
transition: the arrival value is the decision value. No expectation
appears because the stage has no shock.

```bl
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = V                                  :: [id=value]
}
```

The mark `[<]` is the arrival perch mark: `V[<]` is the stage's arrival
value, the object the previous period takes as its continuation value.

## The derivative of the value

The derivative of the choice value in assets is not written in the stage
file. It stands in the methods file beside it,
`declaration/stages/ret_choice/methods.bl`, an **addition** to the stage
file: a `.bl` file that opens with `@methods:` and is read with the stage
file, whose blocks name blocks of the stage by their ids and add their
entries and their lines to them. Its block `cntn_to_dcsn` appends the
derivative line to the decision value block:

```bl
[id=cntn_to_dcsn] {
    D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]  :: [id=marginal]
}
```

The block carries the builder's id and no signature, since it adds no
coordinate; the line is read at the control `d`, as the value line is. It
selects the derivative in assets of the branch value the choice selects, in
the order of the value equation; it carries no cost term, the cost being a
constant. Where the two branch
values cross, the value function has a kink and no derivative, and the
selected derivative is the one-sided derivative of the branch the
tie-break chooses. Iskhakov, Jørgensen, Rust and Schjerning (2017, §2.1)
call that crossing the primary kink and record that the one-sided
derivatives differ there.

The arrival block writes no derivative line. Its law, `a_d = a`, is the
identity, so the derivative of the decision value is the derivative of the
arrival value, which the worker's inverse Euler line of the period before
reads by the term `D_{b}V[>]`.

## Policy

```bl
[id=policy, (V_w[>], V_r[>]) : !cntn -> (d : {work, retire} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_w[>] - δ, V_r[>])        :: [id=choice]
}
```

The inputs are the two continuation values and nothing else: a policy
block's inputs are continuation objects, never the decision state. The
decision state is the argument of the policy the block produces. Here the
choice depends on assets only through the two continuation values. The
block's output is `d`, the control declared in the decision-to-continuation
transition. The two values need no repeated type here, since the backward
block above declares them.

`argmax_{d}` is an operator with a subscript: the braces name the choice
variable and the arguments list the candidate values in the same order as
the tuple in the `choice_value` equation. It returns the label of the
larger entry. The two lines must list the alternatives in the same order;
a policy whose tuple lists them in another order is refused under
`branch-tuple-mismatch`. With no taste shock the selection is
deterministic; where the two values are equal both labels attain the
maximum and a numerical routine needs a stated tie-break rule.

## Numerical method

The methods file `declaration/stages/ret_choice/methods.bl` types the policy
builder with the method `!max`, the maximum over the two branch values, by
the file-level entry `policy.method : !max`, and binds the routine of the
FUES retirement example that compares them as its handler,
`policy.handler : "fues-retirement:dcsn_mover"`; its block `cntn_to_dcsn`
appends the derivative line, which the decision value builder's Evaluation
records as the stated derivative of the value in assets.

## Elaboration

The stage constructs as a branching stage: the two labeled blocks of
`dcsn_to_cntn` are read as that block's lines at the labels work and
retire, and the period and the trellis that contain the stage elaborate.
Loading and elaborating the file prints:

```text
applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl: ElaboratedStage('ret_choice', symbolic)
```

## References

- Iskhakov, F., Jørgensen, T. H., Rust, J., and Schjerning, B. (2017).
  "The endogenous grid method for discrete-continuous dynamic choice
  models with (or without) taste shocks." *Quantitative Economics* 8(2),
  317–365. Section 2.1 states the model, equations (1) to (5).
- Dobrescu, L. I., and Shanker, A. "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN No.
  4181302. Application 1 is this model, and its retirement example
  supplies the staged form used here.
