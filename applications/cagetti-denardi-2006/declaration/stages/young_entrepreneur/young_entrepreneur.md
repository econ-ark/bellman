---
title: "The young entrepreneur (young_entrepreneur.bl)"
audience: developer
type: model-note
topic: [applications]
---
# The young entrepreneur (young_entrepreneur.bl)

A young household that has chosen to run a business borrows $k-a$ at the risk-free rate $r$ and invests $k$, its own assets included, in a technology that yields $\theta k^\nu$ at the end of the year, when it also consumes. Lenders cannot force repayment: the entrepreneur could run away with a fraction $f$ of the working capital and be a worker for the year, so they lend only amounts that he prefers to repay. The stage states equations (3) to (7) of Cagetti and De Nardi (2006):

$$
V_e(a,y,\theta)=\max_{c,k,a'}\bigl\{u(c)+\beta\pi_yEV(a',y',\theta')+\beta(1-\pi_y)EW(a',\theta')\bigr\}
$$

subject to the budget $a'=(1-\delta)k+\theta k^\nu-(1+r)(k-a)-c$, the enforcement constraint

$$
u(c)+\beta\pi_yEV(a',y',\theta')+\beta(1-\pi_y)EW(a',\theta')\ \ge\ V_w(fk,y,\theta),
$$

$a'\ge0$ and $k\ge0$. The discounted continuation value, $\beta\pi_yEV+\beta(1-\pi_y)EW$, is the arrival value of `entrepreneur_ageing` in the next year; this stage receives it as `V_repay[>]` and adds utility. `economics.md` describes the model and the year.

## Perches

A perch is one of the stage's three information sets; a field is a named quantity at a perch.

| Perch | Fields | What they are |
|---|---|---|
| Arrival | `a_ye`, `y_ye`, `θ_ye` | Assets and abilities of a young household that chose to run a business. |
| Decision | `a`, `y`, `θ` | The same quantities, at which capital `k`, consumption `c` and repayment `d` are chosen. |
| Continuation, repay | `a_ye_ea`, `y_ye_ea`, `θ_ye_ea` | Assets at the end of the year and this year's abilities, joined in the next year to `entrepreneur_ageing`. |
| Continuation, default | `a_ye_wk`, `y_ye_wk`, `θ_ye_wk` | The capital kept by an entrepreneur who runs away, with his abilities, joined to the arrival fields of `worker` in the same year. |

## Declarations

```bl
σ : ℝ₊₊          :: ["relative risk aversion; the utility formula requires σ different from 1"]
δ : [0,1]        :: ["depreciation rate of capital"]
ν : [0,1]        :: ["degree of decreasing returns of the entrepreneurial technology"]
f : [0,1]        :: ["fraction of working capital an entrepreneur keeps when he defaults"]
r : (-1, inf)    :: ["risk-free interest rate, a price fixed by the stationary equilibrium"]

𝑢(c : ℝ₊₊) := c^(1-σ)/(1-σ)                                        :: [id=util]
Γ(a : ℝ₊, θ : ℝ₊, k : ℝ₊) := (0, (1 - δ)*k + θ*k^ν - (1 + r)*(k - a)]  :: [id=feasible]
```

The interest rate `r` is a declared parameter: its value is set by the stationary equilibrium of the whole economy, which no stage states (`economics.md`, Section 7). The correspondence `Γ` gives the feasible consumption at assets `a`, ability `θ` and capital `k`: positive and no larger than the resources at the end of the year, so that saving is nonnegative, which is constraint (6). The sets `Xa`, `Y` and `Θ` are declared as in `young_choice.bl`.

## Blocks and equations

The arrival block copies assets and abilities to the decision perch. The decision block declares the three controls: capital `k` on the nonnegative reals, which is constraint (7); consumption `c`; and the repayment choice `d` on the labels `{repay, default}`.

```bl
[id=dcsn_to_cntn, (a, y, θ, k : ℝ₊ @ !ctrl, c : ℝ₊₊ @ !ctrl, d : !ctrl @ {repay, default}) : !dcsn -> ()] {
    [label=repay, () -> (a_ye_ea : Xa, y_ye_ea : Y, θ_ye_ea : Θ) : !cntn] {
        a_ye_ea = (1 - δ)*k + θ*k^ν - (1 + r)*(k - a) - c       :: [id=budget]
        y_ye_ea = y
        θ_ye_ea = θ
    }
    [label=default, () -> (a_ye_wk : Xa, y_ye_wk : Y, θ_ye_wk : Θ) : !cntn] {
        a_ye_wk = f*k                                          :: [id=kept_capital]
        y_ye_wk = y
        θ_ye_wk = θ
    }
}
```

The repay branch is the budget (4): undepreciated capital, output, and repayment of the loan with interest, less consumption. The default branch is the option Section III.D of the paper describes: the entrepreneur keeps $fk$ and becomes a worker for the year, so his continuation is the worker's problem at assets $fk$ with the same abilities. Writing the option as a labelled alternative gives the stage the value of defaulting, $V_w(fk,y,\theta)$, as the continuation value of that branch.

```bl
[id=cntn_to_dcsn, (V_repay[>] : ℝ @ !vlu, V_w[>] : ℝ @ !vlu, c, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = (𝑢(c) + V_repay[>], V_w[>])[d]                         :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                                                  :: [id=value]
}
```

The value of the chosen branch is utility plus the continuation value if the entrepreneur repays, and the worker's value at the kept capital if he defaults. Consumption enters only the repay branch: a defaulter consumes as a worker, in the worker's stage.

```bl
[id=policy, (V_repay[>] : ℝ @ !vlu, V_w[>] : ℝ @ !vlu) : !cntn -> (k : ℝ₊ @ !ctrl, c : ℝ₊₊ @ !ctrl, d : {repay, default} @ !ctrl) : !dcsn] {
    (k, c) = argmax_{k, c : Γ(a, θ, k)}(𝑢(c) + V_repay[>])      :: [id=optimality]
    𝑢(c) + V_repay[>] >= V_w[>]                                 :: [id=enforcement]
    d = argmax_{d}(𝑢(c) + V_repay[>], V_w[>])                   :: [id=repayment]
}
```

The first statement chooses capital and consumption jointly, over nonnegative capital and the consumption `Γ` admits. The second is the enforcement constraint (5): its left side is the objective of the first statement and its right side the value of defaulting. The two statements are read together as problem (3), the maximisation over the pairs $(k,c)$ that satisfy the constraint; the binder of the first statement alone does not carry the constraint, because the feasible set the language admits in a binder is a correspondence written in the states and the parameters, and this one is written in value functions. The stage therefore states the constraint beside the maximisation and leaves the two to be read together. The constraint binds for households with little collateral and is slack for rich ones, and an occasionally binding constraint is written either with a complementary-slackness clause or as an inequality statement (Bellman-SYM, *Constraints*, §1); the reading of an inequality statement given there, the left side as a candidate correspondence, is not the reading needed here.

The third statement chooses between repaying and defaulting at the chosen pair. Where the constraint is slack, repaying is strictly better; where it binds, the two values are equal, so a positive share of households is indifferent, and the file states no rule for that tie. The paper's lenders lend the largest amount the household will still repay, so the rule intended is that a household indifferent between the two repays, and under it no household defaults. The paper computes the constraint as a largest enforceable capital $\hat k(a,y,\theta)$ (Appendix B); that bound is part of the numerical method; the methods file `methods.bl` beside this file declares the two settings of the iteration that computes it, `k_max` and `tol_k`, and writes no entry for the iteration, since the language has no method word for it.

## Elaboration

```text
applications/cagetti-denardi-2006/declaration/stages/young_entrepreneur/young_entrepreneur.bl:22:1-33:2: block 'dcsn_to_cntn' lists the controls 'k', 'c', 'd' beside its branches; this version of the package constructs a branching block whose branches state equations alone and whose label coordinate is its one control, or a shock over a finite set in a stage that chooses nothing (docs/Bellman-Sym/05-branching.md) (address 'dcsn_to_cntn'; rule not-constructed)
```

No view is constructed. The first missing construct is a branching block that lists continuous controls beside its label. Scratch copies of 14 September 2026, before branching was constructed, found the refusals that follow it:

1. With the two branches written as one block: refused at `policy.optimality`, "this statement has a Tuple as its left side; a statement defines one field by name", rule `not-constructed`. The standard-stage construction reads one field on the left of a statement, and a joint maximisation over two controls has a tuple there.
2. Without the joint maximisation: refused at `policy.enforcement`, "this statement has a Add as its left side", rule `not-constructed`.
3. Without both statements: refused at `policy`, rule `output-defined`, "the relation for 'young_entrepreneur:dcsn:k' requires one formula for k[>]", since no statement then defines capital.
4. With the joint maximisation replaced by one maximisation over capital and another over consumption: refused at `policy.capital`, rule `output-defined`, "the ordinary output assignments depend circularly on one another: policy.capital -> policy.consumption -> policy.capital". The two controls are chosen together, and the joint statement is the one that states the problem.

The missing constructs are a branching block with continuous controls beside its label, a joint maximization with a tuple on its left side, and an inequality statement whose left side is an expression; no road-map brief records the last two.

## Reference

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. Section III.C (the technology), Section III.D (credit market constraints), Section III.E, equations (3) to (7), and Appendix B.
