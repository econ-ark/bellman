---
title: Branching
tags:
  - branching
  - syntax-rules
status: Draft — 7 September 2026
related:
  - "[[01-stage]]"
  - "[[03-field-equations]]"
  - "[[06-period]]"
date: 2026-09-07

audience: user
type: user-guide
---

# Branching

#branching

> [!summary]
> A branching stage describes a discrete choice, or a draw by nature, with a separate continuation state for each alternative. We declare the choice labels, write each branch's continuation fields in its own labeled block, and select from the branch values in the order of the labels. The label is the stage's only control; a continuous choice made under one alternative is a stage of its own on that branch. The retirement example below distinguishes the value of a supplied choice from the policy that chooses the better alternative.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](01-stage.md) and [Field equations](03-field-equations.md): declarations, signatures, and equations.
> **Used by** — [Periods](06-period.md): connecting each branch to its successor; [Trellises](07-trellis.md): connecting periods.
> **Formal account** — [Branching](../bellman-calculus/09-branching.md) and [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md): branch values and selection assumptions.

## 1 Work or retire

This complete stage file is the retirement choice of the retirement application, `applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl`. Assets are unchanged by the choice itself; the two alternatives have separately named continuation assets and values. The parameter `δ` is the positive utility cost of working.

```bl
@stage: ret_choice

δ : ℝ₊₊          :: ["utility cost of working, charged in the period whose wage it earns"]

[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a                                   :: [id=assets]
}

[id=dcsn_to_cntn, (a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    [label=work,   () -> (a_w : ℝ₊) : !cntn] { a_w = a_d }
    [label=retire, () -> (a_r : ℝ₊) : !cntn] { a_r = a_d }
}

[id=cntn_to_dcsn, (V_w[>] : [-inf, inf) @ !vlu, V_r[>] : [-inf, inf) @ !vlu, d) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = (V_w[>] - δ, V_r[>])[d]                   :: [id=choice_value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = V                                  :: [id=value]
}

[id=policy, (V_w[>], V_r[>]) : !cntn -> (d : {work, retire} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_w[>] - δ, V_r[>])        :: [id=choice]
}
```

The derivative of the choice value in assets is not written in the stage file. It stands in the stage's block file, `applications/retirement-choice/declaration/methods/marginals_ret_choice.bl`, as a **marginal block**, a block of derivative lines that the stage's methods file binds on the decision builder with `!marginals` ([Methodization](04-methodization.md) §4.1):

```bl
@methods: ret_choice
# The derivative of the value of the discrete choice in assets, stated by the
# marginal block of the decision value builder: the derivative of the branch
# value the choice d selects; the cost of work, a constant, contributes nothing.

[id=dcsn_marginal, (V_w[>], V_r[>], d) : !cntn -> (V) : !dcsn] {
    D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]  :: [id=marginal]
}
```

The control `d` takes labels from `{work, retire}`. The two nested blocks, labeled `work` and `retire`, define `a_w` and `a_r`. No `kind: branching` YAML header is needed: the typed discrete control and the branch blocks declare the alternatives.

In the value equation, `(V_w[>] - δ, V_r[>])[d]` selects the value for a supplied choice. The first component corresponds to `work`, and the second to `retire`. The derivative line of the marginal block, `D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]`, states the derivative of the value in assets as the derivative of the selected branch's value, in the same order; the cost of working does not depend on assets, so it has no counterpart there. The policy equation's `argmax` over `(V_w[>] - δ, V_r[>])` is read as that same tuple indexed by `d`: the policy chooses a label whose entry is largest. The two tuples agree entry by entry and in order. A policy that writes them in another order would select a label using the wrong payoff, and the stage is refused under the rule `branch-tuple-mismatch` ([Refusals](reference/refusals.md#3-the-catalogue)).

The parameter `δ` is charged on the working alternative once. Discounting, earnings, and subsequent consumption are not additional computations in this choice stage; they belong in whichever stages supply its continuation values.

The label is the only control of a branching block. A continuous choice that the agent makes under one alternative, consumption after choosing to work, is a stage of its own on that alternative's branch, and the period connects the branch to it: the retirement application's `period.yml` lists `ret_choice`, then `worker_cons` and `retiree_cons`; its connector joins `a_r` to the retiree's arrival field `a_ret`, and `a_w` joins the worker's arrival field of the same name ([Periods](06-period.md)). A paper that writes the two choices as one maximization over the pair, as the retirement model's Bellman equation does with consumption and next period's status, is stated in this language as the maximization over the label of the values the consumption stages supply; the iterated maximization equals the joint one wherever the inner maximum exists. A branching block that lists a continuous control beside its label is not constructed, and the stage holds a refusal under `not-constructed` ([Refusals](reference/refusals.md#not-constructed)); §4 states the same rule for a branch drawn by nature.

Alternatives that all lead to the same successor stage are not branches. A household choosing among `J` cities faces the same problem next period whichever city it chooses: the choice is an integer control `j : L_J @ !ctrl` over the city set `L_J := {1, …, J}`, and one block with no labels retains the chosen city as the integer continuation state, `i_n = j`; the cities' payoffs and distances are indexed data, `δ[j]` and `dist[j][i]` ([Stages §2.1](01-stage.md#21-indexed-data)). The number of alternatives then remains a parameter, which a branching block cannot admit, since it holds one labeled block for each member of a finite set of names. An alternative whose continuation problem differs from the others', an outside option with a state of its own, is a branch of a branching stage, and the choice among the remaining alternatives is a stage of its own on that branch.

## 2 Branch states and values

The continuation state space is a **disjoint union** of the branches' state spaces: each continuation state is a state of one branch together with that branch's label. Thus a working state consists of `work` and its `a_w`, while a retired state consists of `retire` and its `a_r`. Both asset fields have nonnegative-real domains, but they remain distinct branch fields.

This differs from a pair of simultaneous asset holdings. Even where alternatives share a common continuous domain, the branch label remains necessary to distinguish their continuation problems; where every alternative has the same continuation problem, there is no branch, and the chosen alternative is an integer state (§1). A value function on the disjoint union is equivalently a family of value functions, one on each branch. In this example, `V_w[>]` and `V_r[>]` are the separately declared value fields representing that family.

Ordinary brackets select a collection entry: the `[d]` in §1 selects a tuple component. The `[>]` in `V_w[>]` identifies the continuation information set. These uses of brackets have different meanings; see [Equation parsing rules](appendices/12-equation-parsing-rules.md#3-functions-and-collections).

## 3 Choosing an alternative

The value equation gives the payoff conditional on `d`. The `argmax` equation constrains `d` to an alternative attaining the largest payoff. The block identifiers `cntn_to_dcsn` and `policy` are descriptive addresses; the selection and maximization expressions specify the mathematical operations.

For the two finite, real-valued alternatives in §1, a maximum exists at each state where both values are defined. If the two values coincide, both labels maximize value. A numerical implementation needs a stated tie-breaking rule to return one control. A measurable policy requires measurable branch values and a suitable selection; an arbitrary tie rule is not a substitute for that requirement. If some alternatives are infeasible at a state, the admissible choice set must express that restriction.

The example states a deterministic discrete choice. A stochastic choice model needs its own declared probability law and equations; §4 gives the form. A probability-weighted value, an expectation, and an optimal discrete choice are different operations; a method tag does not supply one in place of another.

When the package constructs the stage from this file, the forward block `dcsn_to_cntn` keeps one law of motion, the map from the decision state and the label to the continuation state, and each branch reads it at its own label. The **section** of the law at a label is the law with `d` fixed at that label: the section at `work`, printed `𝑔_work≻`, sends decision assets to `a_w`, and the section at `retire`, printed `𝑔_retire≻`, sends them to `a_r`. The decision [builder](../wiki/builder.md) evaluates each branch's continuation value at the assets its own section gives, `𝑉_w≻ ∘ 𝑔_work≻` for `work`, forms the tuple of the value equation, and selects its entry at the policy; the policy builder's [Argmax](reference/operations.md#argmax) row, `choice:Argmax`, chooses a label that maximizes the same tuple. Forward, the policy splits the distribution of agents at the decision [perch](../wiki/perch.md) into one distribution for each label: the agents who choose `work` are carried along the work section to `a_w`, and those who choose `retire` to `a_r`, and the two masses add up to the mass at the decision perch. Each builder's card, what `denote()` prints ([A builder](API/stage/04-builder.md) §1), states the sections once, under the heading `Where`. The mathematics of a branching stage is in [Branching](../bellman-calculus/09-branching.md).

## 4 A branch drawn by nature

A retiree in the model of Cagetti and De Nardi (2006, "Entrepreneurship, Frictions, and Wealth", *Journal of Political Economy* 114, Section III.A) survives the year or dies and leaves the assets to an offspring. The stage file `applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl` declares the draw and its law:

```bl
s : {survive, die}
s ~ Categorical((π_o, 1 - π_o))                                             :: ["surviving or dying, with probabilities in the order of the labels"]
```

and writes the two branches and the value line:

```bl
[id=dcsn_to_cntn, (a, y, θ, s) : !dcsn -> ()] {
    [label=survive, () -> (a_rd_rt : Xa) : !cntn] {
        a_rd_rt = a
    }
    [label=die, () -> (a_rd_yc : Xa, y_rd_yc : Y, θ_rd_yc : Θ) : !cntn] {
        a_rd_yc = a
        y_rd_yc = y
        θ_rd_yc = θ
    }
}

[id=cntn_to_dcsn, (W_r[>] : ℝ @ !vlu, V_young[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*E_{s}((W_r[>], η*V_young[>])[s])       :: [id=value]
}
```

The [shock](01-stage.md) `s` takes the labels `{survive, die}`, and its law gives each label its probability in the order of the labels, `π_o` to `survive` and `1 − π_o` to `die`. No policy block chooses the label. The value line takes the expectation over `s` of the tuple indexed by `s`: the value is the sum of the branch values weighted by the law, 𝑉 = β · (π_o · 𝑊_r≻ + (1 − π_o) · η · 𝑉_young≻), each branch value read at the state its own section gives. The decision builder's card prints the line's rule in the form the file writes it, the expectation over `s` of the tuple indexed by `s`, with each branch value read at its own section; the definition of its [aggregation](../wiki/aggregation.md) states the weighted sum. Forward, the distribution at the decision perch is extended by the law of `s`, and the households drawn at each label are carried along that label's section; the two masses add up to the mass at the decision perch. This file's forward builders are refused for another reason: the offspring's abilities are drawn from the family `Invariant`, which the package does not admit, and `worker_ageing.bl`, the aging of a worker in the same model, shows the forward builder of a draw. A law that selects branches gives each label one probability: [`Categorical`](reference/laws.md#categorical) with one weight per label, or [`Bernoulli(p)`](reference/laws.md#bernoulli) over two labels, which gives the **second** label the probability `p`. A branching block is constructed when its branches state equations alone and the label that selects a branch is either the block's one control or a shock over a finite set in a stage that chooses nothing; a stage that draws its branch and also chooses a control is refused under the rule [`not-constructed`](reference/refusals.md#not-constructed), and [Refusals](reference/refusals.md#3-the-catalogue) lists the rules of a malformed draw.

A branch on which the model ends, death without an heir, keeps the continuation state its terminal value reads, the assets at death, and the value line reads a continuation value for that branch as it does for `die` above. In the terminal period that value comes from a stage that lists `V[>]` in its backward header and reads it, as the bequest stage of the retirement application does, `applications/retirement-choice/declaration/stages/bequest/bequest.bl`; the user supplies the function when the model is realized, zero where the paper gives no bequest value ([Trellises §2](07-trellis.md#2-inter-period-connectors)). Death does not set that value to zero by itself, and a zero value does not require removing the branch's field: the language has no empty branch, and a branch that writes no continuation field is refused under `branch-form`.

## 5 Connecting the branches

A period connects each continuation branch to the appropriate successor stage. In §1 those fields are `a_w` and `a_r`. The branches share one stage's field namespace, so these distinct states have distinct names. A working successor can declare arrival assets `a_w`, and a retirement successor can declare arrival assets `a_r`. Each name belongs to its own stage; the package infers a connection only when it is the unique compatible, globally consistent choice among eligible continuation and arrival uses.

An authored connector can select corresponding fields whether their names agree or differ. Use a bare name when its eligible endpoint is unique and a stage-key prefix where the name is ambiguous. A pair must pass the declared-set check; the author must also establish its economic meaning, units and information at the join. It does not compute returns or change units. The full rules are in [Periods](06-period.md#2-connectors).

The branch identity must remain unambiguous throughout this matching. Distinct names alone do not prove that all declared joins are compatible, and shared domains alone do not identify a successor. Do not infer a branch route merely from the order of the stages in the period file.

Whether retirement is absorbing is determined by the subsequent stages and inter-period connections. The choice stage alone does not prevent a future return to work. [Trellises](07-trellis.md#2-inter-period-connectors) explains how the retired continuation can remain connected to retired stages across periods.

## 6 Numerical methods

A method can attach to the authored policy builder, a supported named `!node`, or a supported operator occurrence. For §1, `on: argmax` applies to every `argmax` in the stage; `on: policy.choice.argmax` overrides that choice for the named statement. This attachment does not make the statement another authored node. [Methodization](04-methodization.md#2-computations-and-addresses) gives the address rules.

Neither the discrete control nor its labels create an `upper_env` equation. If a continuous-choice algorithm generates several candidates per branch, its candidate-selection and interpolation requirements must be stated in that algorithm's mathematical and numerical contracts; see [Methodization](04-methodization.md#6-candidate-consumption-and-interpolation).
