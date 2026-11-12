---
title: "The consumption–savings stage in Bellman-SYM (.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The consumption–savings stage in Bellman-SYM (.bl)

> [!summary]
> This page explains `cons_savings_iid.bl` for readers new to
> Bellman-SYM, the language used for `.bl` stage files. The code blocks
> quote selected lines from the working copy beside this page. When that
> file changes, these excerpts and their explanations must change with it.

## Declarations

The first line names the stage. `Y := ℝ₊` defines the set of possible
income values. A declaration is a name, a colon, and a type: `γ : (1, inf)`
introduces a parameter and states its allowed values. Its numerical value is supplied separately.

```bl
@stage: cons_savings_iid

Y := ℝ₊

β : ℝ₊₊ :: ["discount factor must be a strictly positive number"]
γ : (1, inf) :: ["Relative risk aversion must be greater than 1"]
R : ℝ₊₊
μ_y : ℝ
σ_y : ℝ₊
p_zero : (0,1)
```

The file states `β : ℝ₊₊`: the discount factor is a strictly positive
number, as its description says. This declaration permits `β ≥ 1`, and
under it the standard guarantee that repeated Bellman updates converge to a
unique value function does not follow. The usual restriction for a discount
factor is `β : (0,1)`.

The tilde line assigns the distribution of income `y`. Income is
zero with probability `p_zero`; otherwise it follows the lognormal law
with parameters `μ_y` and `σ_y`. Since `p_zero : (0,1)` makes that
probability positive, future income has no strictly positive lower bound. The **natural borrowing limit**—the most
the household can borrow while remaining able to repay along the
lowest-income path—is therefore zero.

```bl
y : Y
y ~ Mixture((p_zero, 0), (1 - p_zero, LogNormal(μ_y, σ_y)))
```

## Utility functions

Mathematical italics are an authoring convention, but the glyph remains
part of the identifier: `𝑢` and `u` are different names. In the editor,
typing `_duinv` produces `𝑑𝑢𝑖𝑛𝑣`. The function declaration—not the
typography—makes `𝑢` a function: `c : ℝ₊₊` declares its strictly
positive argument, and the expression after `:=` defines its value.

Each `id` gives the equation a name that later files can reference; it is
not part of the equation's mathematical meaning. `D_{c}(𝑢)`
differentiates `𝑢` with respect to `c`, and `Inv(𝑑𝑢)` denotes the inverse
of that derivative. Bellman-SYM must verify that the inverse exists,
although that check is not implemented yet.

```bl
𝑢(c : ℝ₊₊) := c^(1-γ)/(1-γ)         :: [id=util]
𝑑𝑢     := D_{c}(𝑢)                   :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)                    :: [id=inv_marg_util]
```

The displayed constant-relative-risk-aversion (CRRA) formula is undefined
at `γ = 1`, while at `γ = 0` its derivative is constant and has no inverse.
The declaration `γ : (1, inf)` excludes both values: it admits a relative
risk aversion greater than 1 alone, as its description says, and calibration
refuses a value outside that set.

## Transitions and value equations

Each block header lists its inputs and outputs and marks each side with a
perch. A **perch** is one of the stage's three information sets: arrival,
decision, or continuation. In `(b : ℝ₊, y) : !arvl`, the set applies
to `b`, while the vocabulary word `!arvl` locates the side at
arrival. The shock `y` is data on
the arrival-to-decision edge and is observed when the decision state is
formed. The source and target perch marks identify the edge and classify
the block as a transition or a backward value block; its equations define
the mapping. The `id` only names the block. The formal typing account is in
[Appendix D](../../../../../docs/bellman-calculus/APPX-D-KINDS-AND-SORTS.md).

The language requires the fixed block IDs `arvl_to_dcsn`,
`dcsn_to_cntn`, `cntn_to_dcsn`, `dcsn_to_arvl`, and `policy`, in the
order shown below.

The first forward block computes cash on hand `w` from
beginning-of-period assets `b`, income `y`, and the gross return
`R`. The second computes end-of-period assets after consumption. Because
`a` is restricted to non-negative values, consumption must satisfy
`c ≤ w` for the transition to respect that declared domain. The source
does not yet state this feasibility condition or the corresponding
constrained policy. It also permits the boundary `w = c = 0`, while `𝑢`
and `𝑐` accept only strictly positive arguments; their value at that
boundary remains unspecified.

```bl
[id=arvl_to_dcsn, (b : ℝ₊, y) : !arvl -> (w : ℝ₊) : !dcsn] {
    w = y + b*R                 :: [id=cash_on_hand]
}

[id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = w - c
}
```

The first backward block defines the decision value `V`, and the second
averages it over income to obtain the arrival value. The stage file writes
the values alone; their derivatives stand in the methods file, quoted below.

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y}(V)                 :: [id=value]
}
```

The methods file `declaration/stages/cons_savings_iid/methods.bl`, an
addition to the stage file that the package reads together with it,
appends the derivative of each value as a line of the builder that writes
the value, under that builder's own id. At the selected optimum, differentiating the decision
value with respect to cash on hand gives `D_{w}V = 𝑑𝑢(c)`; this is the
envelope condition. The arrival line averages that derivative over income.
The factor `R` in it is the derivative of cash on hand with respect to
beginning-of-period assets.

```bl
[id=cntn_to_dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}

[id=dcsn_to_arvl] {
    D_{b}V[<] = E_{y}(R * D_{w}V)   :: [id=marginal]
}
```

## Policy

The stage file's policy block states the choice by the maximization over
the feasible set `Γ(w) = (0, w]`. It reads the continuation value `V[>]`
at the continuation perch and produces the consumption choice `c`, the
control, read at the decision perch. The perch marks on the two sides say
where the inputs are known and where the output is used.

```bl
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ(w)}(𝑢(cp) + β*V[>])  :: [id=optimality]
}
```

The methods file names the endogenous grid method, `!egm`, as the policy
builder's method, with its grid of savings beside it, and appends three
lines to the policy block, which compute the policy in place of the
maximization when the stage is solved; the maximization remains the
stage's statement of the choice.

```bl
[id=policy, method : !egm
    | policy.grid : !Cartesian(a=(a_min, a_max, n_a))] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    w[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}
```

The mark `[~]` on the left of the last line names the decision perch
explicitly; a bare `c` means the same, since a field at the decision perch
is written bare in a stage file, and either spelling gives the same term.

The first line applies inverse marginal utility to `β` times the
derivative of the continuation value at the saving `a`, read by the term
`D_{a}V[>]`; the second obtains the corresponding cash on
hand `w[>] = a + c[>]`. The `[>]` mark identifies both as quantities indexed
by the continuation state `a`: consumption and cash on hand as functions of
savings, not of the decision state.

The third line, `c[~] = c[>]`, is the policy statement. It identifies
consumption at the decision perch with the candidate consumption at the
continuation perch, which is the Euler equation written as an
identification: the consumption chosen at cash on hand `w` is the candidate
whose implied cash on hand `w[>]` equals `w`. The statement names no
operator and is not an alias to be substituted away; the stage reads it as
an equation to be solved for the block's output `c`, one solution at each
decision state (a `solve` occurrence, in the words of the decision
register). How that equation is solved is the numerical method's business:
the endogenous grid method tabulates the first two lines on a grid of `a`,
checks that the resulting cash-on-hand knots increase, and interpolates the
pairs `(w[>], c[>])` at the decision state; a root-finding method solves
the identification pointwise instead. Neither the interpolation nor the
inversion of the endogenous grid is written as an equation, for the same
reason that the representation of `V` on its grid is not: the lines name
the mathematical statements, and the method words of the methods file name
the devices that realize them.
