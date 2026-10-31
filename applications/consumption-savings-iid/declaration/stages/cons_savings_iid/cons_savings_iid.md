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

> [!warning]
> Bellman-SYM cannot yet parse and check the adjacent `.bl` file. It
> contains proposed syntax; the discussion below identifies each
> unresolved line where it appears.

## Declarations

The first line names the stage. `Y := ℝ₊` defines the set of possible
income values. A declaration is a name, a colon, and a type: `γ : ℝ₊`
introduces a parameter and states its allowed values. Its numerical value is supplied separately.

```bl
@stage: cons_savings_iid

Y := ℝ₊

β : (0,1) # this is beta.
γ : ℝ₊
R : ℝ₊₊
μ_y : ℝ
σ_y : ℝ₊
p_zero : [0,1)
```

The working copy states `β : (0,1)`, the usual restriction for a discount
factor, matching the committed ancestors and the formal MDP. An earlier
draft wrote `β : ℝ₊₊`, which permits `β ≥ 1`; under that declaration the
standard guarantee that repeated Bellman updates converge to a unique value
function no longer follows.

The tilde line assigns the distribution of income `y`. Income is
zero with probability `p_zero`; otherwise it follows the lognormal law
with parameters `μ_y` and `σ_y`. When `p_zero > 0`, future income has no
strictly positive lower bound. The **natural borrowing limit**—the most
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
The declaration `γ : ℝ₊` currently admits both values; it must eventually
exclude them or supply the corresponding special cases.

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
the values alone; their derivatives stand in the marginal blocks below.

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y}(V)                 :: [id=value]
}
```

The block file `declaration/methods/marginals.bl` states the derivative of
each value as a marginal block of the builder that writes the value, and
the methods file `declaration/methods/cons_savings_iid.yml` binds each block
with `!marginals`. At the selected optimum, differentiating the decision
value with respect to cash on hand gives `D_{w}V = 𝑑𝑢(c)`; this is the
envelope condition. The arrival line averages that derivative over income.
The factor `R` in it is the derivative of cash on hand with respect to
beginning-of-period assets.

```bl
[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}

[id=arvl_marginal, (V) : !dcsn -> (V[<]) : !arvl] {
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

The methods file opens the policy builder with the endogenous grid method,
`!egm`, and the method block `egm` of the block file
`declaration/methods/cons_savings_iid_egm.bl`, whose three lines compute the
policy in place of the maximization.

```bl
[id=egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
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
inversion of the endogenous grid is written in the stage file or in the
block file, for the same reason that the representation of `V` on its grid
is not: the files name the mathematical statements, and the methods file
names the device that realizes them.
