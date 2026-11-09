---
title: "Entrepreneurship, frictions and wealth: the model of Cagetti and De Nardi (2006)"
audience: developer
type: model-note
topic: [applications]
---
# Entrepreneurship, frictions and wealth: the model of Cagetti and De Nardi (2006)

> [!summary]
> This folder writes the household problems of Cagetti and De Nardi (2006) as ten Bellman-SYM stages joined into one model year. Young households choose between working and running a business, old entrepreneurs between staying in business and retiring; entrepreneurs borrow against a limit that the threat of default sets; ageing and death are random, and a dying household leaves its assets to an offspring whom it values. Eight stages construct; the two entrepreneur stages are refused, each for the construct its page names; the corporate sector and the equilibrium that sets the prices are not stated by any stage. The lesson [Branching](../../tutorials/topics/branching.ipynb) of the tutorials collection constructs the retiree's stage, `retiree_death.bl`.

## 1 The paper

Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870. The stages follow the published text; the working-paper version was read beside it. The parts checked are these:

| Part of the paper | Pages | What it gives |
|---|---|---|
| Section III.A, Demographics | 843 | Two stages of life; a young person ages with probability $1-\pi_y$ and an old person dies with probability $1-\pi_o$ in each year; the offspring enters with the bequeathed assets. |
| Section III.B, Preferences | 843 | Utility $c^{1-\sigma}/(1-\sigma)$, discount factor $\beta$, weight $\eta$ on the offspring's utility, exogenous labour supply. |
| Section III.C, Technology | 843–844 | Working ability $y$ and entrepreneurial ability $\theta$, exogenous, persistent and uncorrelated with each other; the entrepreneur's output $\theta k^\nu$ with $\nu\in[0,1]$; workers save but do not borrow; the corporate sector $F(K_c,L_c)=AK_c^\alpha L_c^{1-\alpha}$, equation (1); depreciation $\delta$ in both sectors. The first-order Markov process $F(y',\theta'\mid y,\theta)$ is stated in Section III.E and its independence in Section III.G. |
| Section III.D, Credit market constraints | 844–845 | An entrepreneur who borrows may repay or run away with a fraction $f$ of his working capital $k$ and be a worker for one period; lenders lend only what will be repaid. |
| Section III.E, Households | 845–847 | The young's problem, equations (2) to (9); the old's problem, equations (10) to (14); the offspring's abilities. |
| Section III.F, Equilibrium | 847–848 | The stationary equilibrium in $r$, $w$ and $\tau$. |
| Section III.G, Calibration, and Table 5 | 848–850 | The fixed and calibrated parameters. |
| Section IV.B | 852 | The equilibrium interest rate of the baseline, 6.5 percent. |
| Section IV.D | 860 | The discount factor of the baseline written as .867. |
| Appendix A | 866–867 | The five-point income chain and the two-state ability chain. |
| Appendix B | 868 | The algorithm: value function iteration, the iteration on the largest enforceable capital $\hat k(x)$, the invariant distribution and the price iteration. |

## 2 The economic environment

A continuum of households lives through two stages of life, with constant probabilities of ageing and of death, the device of Blanchard (1985) that Gertler (1999) extended to the life cycle. A young household starts each year with assets $a$ and knows its working ability $y$ and its entrepreneurial ability $\theta$ for the year; it chooses to work for the wage $w$, paying the payroll tax $\tau$, or to run a business. An entrepreneur borrows $k-a$ at the risk-free rate $r$, invests $k$ in a technology that yields $\theta k^\nu$, and may not borrow more than he would repay: if he ran away he would keep $fk$ and be a worker for the year, so lenders lend only amounts at which repaying is at least as good. The borrowing limit therefore arises from the imperfect enforcement of contracts, as in Kehoe and Levine (1993). A young household becomes old with probability $1-\pi_y$ each year; a worker who ages retires, and an entrepreneur who ages may continue his business. A retiree receives the pension $p$ and cannot start a business. An old household dies with probability $1-\pi_o$ each year, and its offspring enters as a young household with the bequeathed assets; the parent weighs the offspring's utility by $\eta$. Consumption is enjoyed at the end of the year. A corporate sector with the production function (1) employs the workers and the capital that entrepreneurs do not use, and its marginal products fix the prices.

## 3 The household problems

With $u(c)=c^{1-\sigma}/(1-\sigma)$, the paper's value functions are the young's value $V(a,y,\theta)$, the young entrepreneur's $V_e$, the young worker's $V_w$, the old entrepreneur's value before he decides whether to continue, $W(a,\theta)$, the value of continuing, $W_e$, and the retiree's $W_r(a)$:

$$
V(a,y,\theta)=\max\{V_e(a,y,\theta),\,V_w(a,y,\theta)\},\tag{2}
$$

$$
V_e(a,y,\theta)=\max_{c,k,a'}\bigl\{u(c)+\beta\pi_yEV(a',y',\theta')+\beta(1-\pi_y)EW(a',\theta')\bigr\}\tag{3}
$$

subject to

$$
a'=(1-\delta)k+\theta k^\nu-(1+r)(k-a)-c,\tag{4}
$$

$$
u(c)+\beta\pi_yEV(a',y',\theta')+\beta(1-\pi_y)EW(a',\theta')\ \ge\ V_w(fk,y,\theta),\tag{5}
$$

$$
a'\ge0,\tag{6}
$$

$$
k\ge0;\tag{7}
$$

$$
V_w(a,y,\theta)=\max_{c,a'}\bigl\{u(c)+\beta\pi_yEV(a',y',\theta')+\beta(1-\pi_y)W_r(a')\bigr\}\tag{8}
$$

subject to (6) and $a'=(1+r)a+(1-\tau)wy-c$ (9);

$$
W(a,\theta)=\max\{W_e(a,\theta),\,W_r(a)\},\tag{10}
$$

$$
W_e(a,\theta)=\max_{c,k,a'}\bigl\{u(c)+\beta\pi_oEW(a',\theta')+\eta\beta(1-\pi_o)EV(a',y',\theta')\bigr\}\tag{11}
$$

subject to (4), (6), (7) and

$$
u(c)+\beta\pi_oEW(a',\theta')+\eta\beta(1-\pi_o)EV(a',y',\theta')\ \ge\ W_r(fk);\tag{12}
$$

$$
W_r(a)=\max_{c,a'}\bigl\{u(c)+\beta\pi_oW_r(a')+\eta\beta(1-\pi_o)EV(a',y',\theta')\bigr\}\tag{13}
$$

subject to (6) and $a'=(1+r)a+p-c$ (14). The expectations are over next year's abilities conditional on this year's, under independent Markov chains with transition matrices $P_y$ and $P_\theta$. The offspring of an entrepreneur draws $y'$ from the invariant distribution of $P_y$ and $\theta'$ from the row of $P_\theta$ at the parent's $\theta$, since he inherits the firm; the offspring of a retiree draws both from their invariant distributions.

## 4 Stages and their order in a year

A **stage** is one decision problem in its own `.bl` file, with three **perches**, the information sets at arrival, at decision and at continuation. A **field** is a named quantity at a perch. Each stage has a page beside its file.

| Stage | What it states | Paper | Elaboration |
|---|---|---|---|
| `worker_ageing.bl` | A young worker remains young or ages and retires; the new abilities are drawn. | the continuation of (8) | constructs |
| `entrepreneur_ageing.bl` | A young entrepreneur remains young or becomes an old entrepreneur; the new abilities are drawn. | the continuation of (3) | constructs |
| `entrepreneur_death.bl` | An old entrepreneur survives or dies and leaves an offspring; the abilities are drawn. | the continuation of (11) | constructs; forward builders refused (Invariant) |
| `retiree_death.bl` | A retiree survives or dies and leaves an offspring; the offspring's abilities are drawn. | the continuation of (13) | constructs; forward builders refused (Invariant) |
| `young_choice.bl` | The young choose an occupation. | (2) | constructs |
| `old_choice.bl` | The old entrepreneur continues or retires. | (10) | constructs |
| `young_entrepreneur.bl` | Investment, consumption and repayment of the young entrepreneur under the enforcement constraint. | (3) to (7) | refused: a control beside the label coordinate |
| `old_entrepreneur.bl` | The same for the old entrepreneur. | (11), (12), with (4), (6), (7) | refused: a control beside the label coordinate |
| `worker.bl` | The young worker's consumption and saving. | (8), (9) | all three views constructed |
| `retiree.bl` | The retiree's consumption and saving. | (13), (14) | all three views constructed |

A year runs in this forward order: the four demographic stages, then the two choices, then the two entrepreneurs, then the worker and the retiree, which are the successors of the entrepreneurs' default branches. The value computation runs the other way. The following choices of representation go beyond the paper's text; none changes an equation of Section 3.

1. **Default is a branch.** Each entrepreneur stage writes the option the paper describes, repaying or running away with $fk$, as a labelled alternative whose continuation is the worker (young) or the retiree (old) at assets $fk$. The enforcement constraint (5) or (12) is then the inequality between the two branch values, and it is written as a statement of the policy block beside the maximisation. The two statements are read together as problem (3) or (11), the maximisation over the pairs $(k,c)$ that satisfy the constraint: the binder of the maximisation carries only the correspondence `Γ`, since a feasible set written in a binder is a correspondence in the states and the parameters, and this one is written in value functions. Where the constraint binds, the value of repaying equals the value of defaulting, so a positive share of households is indifferent and the forward operator needs a rule for that tie; the paper's lenders lend the largest amount the household will still repay, so the rule intended is that an indifferent household repays, and under it no household defaults.
2. **The year begins with the demographic events.** The paper draws next year's abilities and the ageing or death event between two years; the stages place both at the start of the year that follows, before the occupational choices. The arrival value of each demographic stage is the continuation value of the problem that ended the year before.
3. **The discount factor and altruism are written in the demographic stages.** Their value statements are $\beta E_s[\cdot]$ with $\eta$ on the offspring's value, and the four decision stages add utility to a continuation value that is already discounted, so $\beta$ enters each problem once.
4. **An offspring's abilities are drawn before survival is known.** The death stages draw them for every household on the arrival edge. The surviving household's value does not depend on them, so each arrival value is the paper's.
5. **The abilities are levels.** The fields $y$ and $\theta$ hold the ability levels, as the paper writes them. The grid of $y$ has a number of points that the discretisation chooses, and no set with that open count has a spelling, so `Y := ℝ₊₊`, `P_y : [0,1]` and `y_grid : ℝ₊₊` stand in for the grid, the matrix and the vector of levels; `Θ := ℝ₊` stands in for the two levels $0$ and $\theta_e$. The road-map brief *Parameter families indexed by a finite set, and finite sets with numeric members* records the open question.
6. **Each law names the ability it is drawn from.** `MarkovChain(P_y, y_grid, y_wa)` names the transition matrix, the levels and last year's ability; `Invariant(P_y, y_grid)` names the invariant distribution of the same chain; `Categorical((π_y, 1 - π_y))` gives the probabilities of the two demographic labels in their declared order. A law is the conditional distribution of the draw given the information at the source perch of its edge, in the arguments it names (Bellman-SYM, *Equation parsing rules*, §4); no spelling of a law with a conditioning argument is settled, and the third argument of `MarkovChain` and the law name `Invariant` are this example's.
7. **The value names follow the paper, not the labels.** In every branching stage the tuple of branch values is written in the order of the labels, and that order is what associates a value with a branch; the names are the paper's functions, so the labels `young` and `old` of `worker_ageing` carry `V_young` and `W_r`, and the labels `repay` and `default` of the entrepreneurs carry the honour value and `V_w` or `W_r`.
8. **The problems are stated as maximisations.** The paper solves them by value function iteration (Appendix B) and uses no first-order conditions, so no stage writes marginal values or an endogenous-grid realisation.

## 5 Connectors

A **connector** identifies a continuation field of one stage with an arrival field of another; it computes nothing. The field names carry two-letter tags: `yc` young choice, `ye` young entrepreneur, `wk` worker, `oc` old choice, `oe` old entrepreneur, `rt` retiree, `wa` worker ageing, `ea` entrepreneur ageing, `ed` entrepreneur death, `rd` retiree death. An arrival field carries its own stage's tag (`a_wk`); a continuation field carries its stage's tag and its successor's (`a_yc_wk`, from the young choice to the worker), except on the two entrepreneur branches, whose fields carry the successor's tag alone (`a_ye`, `a_oe`) and meet the arrival fields of the same name. Fields that meet by the same name need no connector. The shocks `y_n`, `θ_n` and `s` of the demographic stages are drawn by the laws of those stages and join nothing. The within-year joins are those of `period.yml`:

| From (branch) | Fields | To | Fields |
|---|---|---|---|
| `worker_ageing` (young) | `a_wa_yc, y_wa_yc, θ_wa_yc` | `young_choice` | `a_yc, y_yc, θ_yc` |
| `entrepreneur_ageing` (young) | `a_ea_yc, y_ea_yc, θ_ea_yc` | `young_choice` | `a_yc, y_yc, θ_yc` |
| `entrepreneur_death` (die) | `a_ed_yc, y_ed_yc, θ_ed_yc` | `young_choice` | `a_yc, y_yc, θ_yc` |
| `retiree_death` (die) | `a_rd_yc, y_rd_yc, θ_rd_yc` | `young_choice` | `a_yc, y_yc, θ_yc` |
| `entrepreneur_ageing` (old) | `a_ea_oc, θ_ea_oc` | `old_choice` | `a_oc, θ_oc` |
| `entrepreneur_death` (survive) | `a_ed_oc, θ_ed_oc` | `old_choice` | `a_oc, θ_oc` |
| `young_choice` (entrepreneur) | `a_ye, y_ye, θ_ye` | `young_entrepreneur` | the same names |
| `young_choice` (worker) | `a_yc_wk, y_yc_wk, θ_yc_wk` | `worker` | `a_wk, y_wk, θ_wk` |
| `young_entrepreneur` (default) | `a_ye_wk, y_ye_wk, θ_ye_wk` | `worker` | `a_wk, y_wk, θ_wk` |
| `old_choice` (entrepreneur) | `a_oe, θ_oe` | `old_entrepreneur` | the same names |
| `old_choice` (retiree) | `a_oc_rt` | `retiree` | `a_rt` |
| `old_entrepreneur` (default) | `a_oe_rt` | `retiree` | `a_rt` |
| `worker_ageing` (old) | `a_wa_rt` | `retiree` | `a_rt` |
| `retiree_death` (survive) | `a_rd_rt` | `retiree` | `a_rt` |

Four arrival interfaces receive several sources: the young choice four, the old choice two, the worker two and the retiree four. For any one household exactly one of these sources applies. The inter-period connector of `trellis.yml` joins the end of year $h+1$ to the start of year $h$: the worker's `a_wk_wa, y_wk_wa, θ_wk_wa` to `worker_ageing`'s `a_wa, y_wa, θ_wa`; the young entrepreneur's repay branch `a_ye_ea, y_ye_ea, θ_ye_ea` to `entrepreneur_ageing`'s `a_ea, y_ea, θ_ea`; the old entrepreneur's repay branch `a_oe_ed, θ_oe_ed` to `entrepreneur_death`'s `a_ed, θ_ed`; and the retiree's `a_rt_rd` to `retiree_death`'s `a_rd`. No arrival field is both supplied within a year and joined between years (Bellman-SYM, *Trellis syntax*, §2).

The stage-dependency graph of the year cannot be derived from the files, since the two entrepreneur stages are not constructed. It was derived from scratch copies that keep every arrival and continuation field of each stage: the branching stages with their branches written as one block, and the two entrepreneurs with capital, consumption and repayment as parameters. `period_factory.period_to_graph` found fourteen dependencies between stages and no cycle, and `forward_order` returned `worker_ageing, entrepreneur_ageing, entrepreneur_death, retiree_death, old_choice, young_choice, old_entrepreneur, young_entrepreneur, retiree, worker`. A trellis of $H$ years also needs terminal continuation values for the worker, the two entrepreneurs' repay branches and the retiree of year $h=0$, and, for a forward calculation, an initial distribution over the arrival fields of the four demographic stages of the earliest year; the paper's stationary value functions are the fixed point of the year's backward operator, and no stage states that condition.

## 6 Calibration

`declaration/calibration/cagetti-denardi-2006.yml` holds the baseline calibration; each stage binds the names it declares.

| Parameter | Name | Value | Source |
|---|---|---|---|
| relative risk aversion | `σ` | 1.5 | Table 5, panel A |
| depreciation rate | `δ` | 0.06 | Table 5, panel A |
| probability of remaining young | `π_y` | 0.978 | Table 5, panel A; a working life of 45 years |
| probability of surviving when old | `π_o` | 0.911 | Table 5, panel A; a retirement of 11 years |
| weight on the offspring's utility | `η` | 1.0 | Table 5, panel A |
| grid of working ability | `y_grid` | 0.2468, 0.4473, 0.7654, 1.3097, 2.3742 | Appendix A |
| transition matrix of working ability | `P_y` | the $5\times5$ matrix of Appendix A | Appendix A; Table 5, panel A |
| discount factor | `β` | 0.865 | Table 5, panel B |
| positive entrepreneurial ability | `θ_e` | 0.514 | Appendix A; Table 5 writes .51 |
| persistence of zero ability | `ρ_θ0` | 0.964 | Appendix A, $P_\theta$ |
| persistence of positive ability | `ρ_θ1` | 0.794 | Appendix A, $P_\theta$ |
| degree of decreasing returns | `ν` | 0.88 | Table 5, panel B |
| capital kept on default | `f` | 0.75 | Table 5, panel B |
| interest rate | `r` | 0.065 | Section IV.B, the equilibrium of the baseline |
| capital share and scale of the corporate sector | `α`, `A` | 0.33, 1.0 | Table 5, panel A; declared by no stage |

Two numbers of the paper disagree: Table 5 gives $\beta=.865$ and the text of Section IV.D gives .867 for the same baseline; the file uses Table 5. The paper's calibration of $P_\theta$ is its two persistence probabilities, since each row sums to one, and the stages write the matrix from `ρ_θ0` and `ρ_θ1`. The income chain approximates, by the method of Tauchen and Hussey (1991), a lognormal AR(1) with persistence 0.95 whose variance matches an earnings Gini coefficient of 0.38 (Section III.G); the paper reports the chain, not the variance.

The wage $w$, the payroll tax $\tau$ and the pension $p$ have no values in the file. The paper fixes $w$ by the marginal product of labour in the corporate sector, $\tau$ by the balance of the social security budget, and $p$ as 40 percent of average yearly income (Table 5), net of taxes (Section III.G), and it reports none of the three. Specification of the stages that declare them is therefore refused (Section 9).

`declaration/settings/cagetti-denardi-2006.yml` names the numerical choices of Appendix B that the methods files reference: the asset grid, its maximum "chosen so that it is not binding", the capital grid, the maximum investment level $k_{\max}$ with which the iteration on $\hat k(x)$ starts, and the convergence criteria. The paper reports none of their values, so each is `null`, except the lowest asset level, which is the borrowing limit $a'\ge0$ of (6).

## 7 What the stages cannot state

1. **The equilibrium prices.** The interest rate $r$, the wage $w$ and the tax $\tau$ are fixed by the stationary equilibrium of Section III.F: the capital and labour markets clear, the prices equal the marginal products of the corporate sector (1), the return on capital there equals $r$, and the payroll tax finances the pensions. Each stage declares the prices it uses as parameters. The condition that the households' decisions, aggregated over the invariant distribution, reproduce those prices is a fixed point above the stages. Bellman-SYM's *Syntax to semantics* appendix, rule R8, places such a condition outside the rules that interpret a stage.
2. **The pension.** The pension $p$ is 40 percent of an average over the population, an aggregate of the same kind; the retiree's stage declares $p$ as a parameter.
3. **The invariant distribution.** The stationary distribution $m^*(x)$ over $x=(a,y,\theta,s)$, where $s$ records the household's kind, is invariant under the year's forward operator. The stages give the forward operators of one year; invariance is a condition on their composition over the trellis.
4. **The corporate sector.** Equation (1), the capital and labour it employs and the resulting output are not a household's decision, and no stage writes them.
5. **The bound on enforceable capital.** The stages state the enforcement constraints (5) and (12) themselves, as statements beside the maximisations they restrict, because a feasible set written in value functions has no place in the binder of a maximisation. The largest enforceable capital $\hat k(x)$ of Appendix B, and the iteration that computes it, belong to the numerical method.

## 8 Methods

Each stage has a methods file, the addition `methods.bl` beside its stage file, whose every selection is a typing line at file level, since no method adds a line. The choice stages type `!max` on the policy builder. The worker, the retiree and the entrepreneurs type `!vfi`, value function iteration, on the decision value builder with the grids of Appendix B as grid entries, and `!histogram` on the forward transition that builds the transition matrix over the grid. The entrepreneurs' files declare the two settings of the iteration on $\hat k(x)$, `k_max` and `tol_k`, and write no entry for that iteration, since the language has no method word for it. The demographic stages type `!exact_markov` at the expectation over the new abilities and `!sum` at the expectation over the demographic event.

## 9 Elaboration

Each stage was elaborated alone on 14 September 2026 with `bellman.elaborate(…, upto="symbolic")`, the call AMD-FAC-002 removed for `elaborate_stage`. `worker.bl` and `retiree.bl` constructed the field view and the backward and forward operator views, and the eight other stages were refused at their first labeled block, rule `not-constructed`, with the diagnostic "make_stage cannot construct this nested block: task B02 (branching construction) adds its construction rule".

Since 25 September 2026 the package constructs a branch that a declared shock selects as well as one that a control selects. Each stage elaborated alone with `elaborate_stage(load_stage(…))` answers as its page quotes:

- `young_choice` and `old_choice`: every builder constructs, and `combination` answers `choice`.
- `worker_ageing` and `entrepreneur_ageing`: every builder constructs, and `combination` answers `expectation`.
- `entrepreneur_death` and `retiree_death`: the backward builders construct, and `combination` answers `expectation`; the forward builders are refused, since the working ability of an offspring is drawn from the family `Invariant`, which the package does not admit: "the forward measures are not constructed: the distribution of y_n is written with the family 'Invariant', whose result set is not declared".
- `young_entrepreneur` and `old_entrepreneur`: refused at the branching block, rule `not-constructed`, "block 'dcsn_to_cntn' lists the controls 'k', 'c', 'd' beside its branches". Their pages list what scratch copies found missing beyond the branching block on 14 September 2026: the joint maximization over capital and consumption and the enforcement inequality.

Each builder, the operation that carries a value or a distribution from one perch to the next, prints a card stating what it computes, and the cards print the equations as the files write them. The decision builder of each demographic stage reads each branch value along its own section, the law of motion read at that branch's label, and prints the file's value line; in `retiree_death` the line is `𝑉(a, y, θ) = β · E_{s}[(𝑊_r≻(𝑔_survive≻(a, y, θ)), η · 𝑉_young≻(𝑔_die≻(a, y, θ)))[s]]`. The definition of its aggregation, the operation that combines the branch values, is their sum weighted by the law of `s`, `β · (π_o · W_r≻ + (1 − π_o) · (η · V_young≻))`; with the arrival builder's expectation over the offspring's abilities, `𝑉≺(a_rd) = E_{y_n, θ_n}[𝑉(𝑔≺(a_rd, y_n, θ_n))]`, this is the continuation in (13). The forward builders of `worker_ageing` and `entrepreneur_ageing` extend the distribution at the decision perch by the law of `s` and carry the households drawn at each label along that label's section. The decision builders of `young_choice` and `old_choice` read each branch value along its own section, and the policy chooses the branch of larger value.

A demographic fork keyed by a shock is a branch chosen by nature rather than by the household. The road-map brief *Whether a branching stage declares how its branches are chosen, or the reader derives it from the equations* records the reading written here, an expectation over a declared discrete shock of the branch value it selects; the package has constructed it since 25 September 2026, the value being the branch values weighted by the probabilities the law of `s` gives the labels.

The trellis assembled from `declaration/period.yml`, `declaration/trellis.yml`, the methods files, `declaration/settings/cagetti-denardi-2006.yml` and `declaration/calibration/cagetti-denardi-2006.yml`, two years long, was elaborated on 14 September 2026 with `bellman.elaborate`, which AMD-FAC-002 removed for `elaborate_trellis` and the three trellis verbs, and was refused at the first labeled block of `worker_ageing`. The file `trellis.yml` writes each period's stages as a list, the earlier form of a trellis file, which `load_trellis` refuses today:

```text
FactoryError trellis-file-shape: applications/cagetti-denardi-2006/declaration/trellis.yml: address 'periods[0].stages': periods[0].stages is no mapping of keys to records; write stages: {<key>: {stage: <file>.bl, calibration: ..., settings: ..., methods: ...}} (rule trellis-file-shape)
```

Written as a registry, with a terminal stage for each of the four households whose problems end the year, the whole trellis waits for the construction of the two entrepreneur stages. With those two stood in by standard stages that declare the same arrival and continuation fields, a year of the registry has 31 joins and nine outputs, the terminal year 40 joins and none, and four sources reach each arrival field of the young choice and the retiree's arrival field.

The two stages that construct were specified alone from the same files, in the same run of 14 September 2026 with `bellman.elaborate`, which AMD-FAC-002 removed for `elaborate_stage` and the three binding verbs. Every method target resolved and the settings were bound; calibration was refused for the unreported prices:

```text
elaborate(worker alone, upto='specified'): ValueError: stage 'worker', parameter 'w' (term address '8'): the calibration source supplies no value for it; every declared parameter is valued when values are bound […]; write `w: <value>` in the calibration source
elaborate(retiree alone, upto='specified'): ValueError: stage 'retiree', parameter 'p' (term address '6'): the calibration source supplies no value for it; every declared parameter is valued when values are bound […]; write `p: <value>` in the calibration source
```

The two makers of the factories, `period_factory.make` and `trellis_factory.make`, failed on these `.bl` records before any stage was constructed and are not in the package; `elaborate_trellis` and the three trellis verbs take the records instead.

## References

- Blanchard, O. J. (1985). "Debt, Deficits, and Finite Horizons." *Journal of Political Economy* 93(2), 223–247.
- Cagetti, M., and De Nardi, M. (2006). "Entrepreneurship, Frictions, and Wealth." *Journal of Political Economy* 114(5), 835–870.
- Gertler, M. (1999). "Government Debt and Social Security in a Life-Cycle Economy." *Carnegie-Rochester Conference Series on Public Policy* 50, 61–110.
- Kehoe, T. J., and Levine, D. K. (1993). "Debt-Constrained Asset Markets." *Review of Economic Studies* 60(4), 865–888.
- Tauchen, G., and Hussey, R. (1991). "Quadrature-Based Methods for Obtaining Approximate Solutions to Nonlinear Asset Pricing Models." *Econometrica* 59(2), 371–396.
