---
title: "Pensions and housing over the life cycle in Australia"
audience: developer
type: model-note
topic: [applications]
---
# Pensions and housing over the life cycle in Australia

> [!summary]
> A worker enrolled in a sector pension plan chooses, each year, a voluntary
> contribution rate and a risky share for the pension balance, and whether to
> rent, to keep the house owned or to change it, with nondurable consumption
> and a mortgage; at 65 the pension is paid out, and the wealth left at death
> is bequeathed. This page states the economic environment of the paper, the
> eleven stages the model is written in, how they are joined into a period
> and the periods into a life cycle of 85 periods, the calibration, what the
> stage files cannot state, and the numerical methods that fit each block.
> Nothing is built yet: the stage files are to be written in the Workbench
> from this page, and the lines below written in the language's spelling are
> the lines an author copies.

## The model and its source

The model is that of Dobrescu, Shanker, Bateman, Newell and Thorp (2023),
*Eggs and Baskets: Lifecycle Portfolio Dynamics*, version 43, "the paper"
below: Section 4, "The model", states the environment in paragraphs A
(preferences) to F (timing and Bellman equation), equations (1) to (25);
Section 5 gives the calibration and the estimation target, equation (26);
Appendix D, "Computation", gives the grids, equations (79) to (81), and the
solution procedure, equations (82) to (86); the paper's online Appendix C
derives the Euler equations, cited here by its printed numbers, (27) to (78).
The equations were checked against the paper's code, the repository
`eggsandbaskets` (its `readme.md`, `lifecycle_model.py`, the solvers, the
tools and the two development settings files), which supplies values the
paper does not print; where the code and the paper differ, both are named
here or in the table of differences of `model-brief.md`. The paper belongs to
the housing-frictions literature of Kaplan, Mitman and Violante (2020) and
Yogo (2016), from which it takes the utility function and the housing return,
and to the pension-default literature of Rust (1987) for the discrete choices
with taste shocks.

An individual works from age t₀ = 17, retires at T_R = 65, exogenously and
with certainty, and lives to T = 100 at the latest (Section 4, opening
paragraph; Section 5). Each year she survives into the next with probability
p_t. Her per-period utility is a constant-elasticity-of-substitution aggregate
of nondurable consumption c and housing services S, equation (1):

u(c, S; α) = ( [(1 − α) c^ρ + α S^ρ]^{(1−γ)/ρ} − 1 ) / (1 − γ),

with α ∈ (0, 1) the weight on housing, a state that follows a two-point
Markov chain whose transition from the low to the high taste is scaled by a
binary belief shock (conviction or hesitation, Section 4.A), 1/(1 − ρ) the
elasticity of substitution between the two goods, and 1/γ the intertemporal
elasticity. The discount factor β_t is itself a three-state Markov chain
(Section 4.F). At death the wealth left, B, gives the warm-glow utility
b(B) = θ (B + k)^{1−γ}/(1 − γ), equation (2); B is the sum of the liquid
assets with their return, the pension balance with its return and the
depreciated house at its price, less the mortgage with its interest, the
online Appendix C's equation (33), the beginning-of-period wealth after all
returns have accrued.

She holds four assets. Liquid assets a earn the fixed gross return R and may
not be negative (Section 4.E, text after equation 14). The pension balance
a^{dc} receives the employer's contribution v_E, the standard contribution v_S
and the voluntary contribution v_t, as shares of earnings y_t, and earns the
return of a portfolio with the risky share π_t, equation (6):

a^{dc}_{t+1} = [π_t R^r_t + (1 − π_t) R^s_t] · [a^{dc}_t + ((1 − o) v_E + v_t) y_t] in a DB plan,
a^{dc}_{t+1} = [π_t R^r_t + (1 − π_t) R^s_t] · [a^{dc}_t + (v_E + v_S + v_t) y_t] in a DC plan,

where ln R^i_t = r^i + i ε^d_t for i ∈ {r, s} with one common shock ε^d_t,
equation (7). A member of the defined-benefit plan also has an entitlement
a^{db}_t = f^{ACF}(v_S) · f^{LSF}(t) · f^{ASF} · τ · ȳ_t, equation (5), a product
of three contribution and service factors, the tenure τ and the average ȳ_t of
the current and the two previous wages. The housing stock H depreciates at the
rate δ and is changed by the investment h_t, equation (8), at the unit price
P_t, which moves with the housing return R^h_t = (1 − δ) P_t / P_{t−1},
equation (9), with R^h_t = 1 + r^h + ε^h_t (text after equation 14). A
mortgage m is repaid at the gross rate R^m_t with ln R^m_t = β^m r^s + κ ε^d_t,
equation (10) read with the mean safe return r^s in the markup term: Section
5's β^m = 3.36 and κ = 0.33 reproduce the mean real mortgage rate 0.0649 and
its standard deviation 0.021 only so (3.36 × 0.0193 = 0.0649 and
0.33 × 0.064 = 0.0211), and the code's mortgage chain has the standard
deviation 0.0213; the shock ε^d_t is the pension-return shock of equation
(7). The mortgage is bounded by the collateral constraint
m_{t+1} ≤ (1 − φ^C) P_t H_t, equation (11); a
non-adjusting owner may also vary the balance only within the redraw limit ι
above the balance with its interest, m_{t+1} ≤ R^m_t m_t + ι (Section 4.D,
text after equation 11). An owner consumes S_t = H_t; a renter buys S_t at
the rate P^S_t = φ^S P_t, pays no transaction cost and holds no house and no
mortgage; changing the stock costs τ_H P_t H_t, charged on the stock after the
change (Section 4.D; equation 12). The budget while working, equation (12):

a_{t+1} = R a_t + (1 − v_t − v_S) y_t − c_t − P^S_t S_t − P_t h_t − 1{h_t ≠ 0} τ_H P_t H_t + m_{t+1} − R^m_t m_t,

and at retirement the balances a^{db} + a^{dc} are paid into liquid wealth
while earnings and contributions stop, equation (14). Earnings are
ln y_t = y(t, τ) + ξ_t with ξ_t a first-order autoregression, equation (3).

Three pension choices carry switching costs in utility, equation (4): the
one-off, irreversible switch from the default DB plan to the DC plan in the
first year, u_p; a voluntary contribution rate other than the default of zero,
u_v, decreasing in the liquid assets a_t, the asset entering the period before
its return (equation 12 writes R a_t; ν^v_3 < 0 in Table 4); a risky share
other than the default of 0.7, u_π, increasing in the balance at stake a^{dc}_t
(ν^r_3 > 0 in Table 4). Each of these discrete choices also carries a type-I
extreme value taste shock, so that the plan is chosen by equation (15) with
the probability (16), the contribution by (17) and (18) with the log-sum (22)
and the probability (24), and the share by (19) and (20) with (23) and (25).
The Bellman equation (20) chooses consumption, housing services and the
housing investment given the share and the contribution, and discounts the
expectation of surviving into next period's value or dying into the bequest;
the online Appendix C's equation (37) writes the same equation with the
bequest utility b(B_{t+1}) and defines B_{t+1} in (38).

The paper estimates 27 parameters by the simulated method of moments, by
gender, equation (26), on the moments (i) to (vii) of Section 5, and reports
them in Table 4; it checks the fit by cohort in Figures 3 to 11 and runs six
counterfactuals in Section 6.3. The paper's two housing frictions and three
discrete pension choices make the value functions non-concave, which is why
the paper solves it with the endogenous grid method and the fast upper
envelope scan (Appendix D.2).

The paper's own partition of the period is in `model-brief.md`, "Timing map",
with the three points its code names, `_next`, `_start` and `_curr`.

## The stages and the order of a period

A stage is one decision step with three information sets, arrival, decision
and continuation. A block of a stage file denotes a **builder**, the operator
that carries the block's equations: backward, on value functions, for the two
blocks `cntn_to_dcsn` and `dcsn_to_arvl` and the policy block; forward, on
distributions of households, for `arvl_to_dcsn` and `dcsn_to_cntn`
([Stages](../../docs/Bellman-Sym/01-stage.md) §5). The model has eleven
stages; a working year before 65 holds nine of them, a retirement year seven,
the first year eight, with the plan choice and without the survival draw and
the bequest, the year of retirement eight with the payout, and the period
after the last age two.

| Stage key | What happens in it | Where in the paper |
|---|---|---|
| `shocks` | The period's shocks are drawn on the arrival edge: the wage innovation, the housing taste, the discount factor, the pension-return shock and the house-price shock. The returns are applied to the liquid assets, the pension balance and the mortgage, the house depreciates, the price moves and earnings are formed. No choice. | equations (3), (6), (7), (8), (9), (10), the text after (14) |
| `survival` | Nature draws survival or death with probabilities (p, 1 − p). The survivor's state continues to the decisions of the period; the decedent's wealth continues to the bequest. No choice. | equation (20), the weights p_t and 1 − p_t; online Appendix C (37) |
| `plan_choice` | In the first period alone: the plan, DB or DC, chosen once and for good, at the cost u_p on the DC alternative. | equations (4), (15) |
| `contribution` | The voluntary contribution rate v is chosen from six rates, the default of zero among them, at the cost u_v off the default; take-home earnings and the contributions to the balance follow. | equations (4), (6), (12), (18) |
| `allocation` | The risky share π is chosen from six shares, the default of 0.7 among them, at the cost u_π off the default; the share is carried to the next period's returns. | equations (4), (6), (19), (20) |
| `payout` | In the year of retirement alone: the defined-benefit entitlement and the pension balance are paid into liquid wealth. No choice. | equations (5), (14) |
| `tenure` | The household chooses among renting, adjusting the house and keeping it; the three branches end in different continuation spaces. | equation (12); Appendix D.2, the labels `rent`, `adj_own`, `nadj_own` |
| `renter_cons` | The renter chooses consumption and housing services out of cash on hand. | equations (1), (12), (20); online Appendix C (64), (74) |
| `keeper_cons` | The keeper chooses the next mortgage and consumption, with the stock fixed. | equations (1), (11), (12), (20); online Appendix C (64) to (69), (78) |
| `adjuster_cons` | The adjuster chooses consumption, the new stock and the next mortgage out of total wealth. | equations (1), (8), (11), (12), (20); online Appendix C (64) to (70) |
| `bequest` | The wealth of a decedent is valued by the bequest function; the continuation value is zero. No choice. | equation (2); online Appendix C (33) |

Forward, a working period runs `shocks`, `survival`, `contribution`,
`allocation`, `tenure` and then one of the three consumption stages, the one
the tenure choice selects; a decedent runs `shocks`, `survival`, `bequest`.
Backward, the bequest and the three consumption stages are computed first, in
any order, because none reads another; `tenure` then compares their arrival
values, `allocation` and `contribution` add their costs and choose,
`survival` weights the two routes, and `shocks` integrates over the period's
draws. The order of the stages is derived from their fields and not from the
list in the period file ([Periods](../../docs/Bellman-Sym/06-period.md) §3).
The order follows the paper's main text, Section 4.F: the plan at t₀ by
(15), then each period the contribution by (18), the share by (20) and the
continuous choices inside (20); Appendix D.2 and the code place the share
choice after the continuous choices, inside the expectation of the
consumption Euler equation, and "Assumptions to confirm" puts that
difference to AAS.

### The spellings used

Every line below written in the language's spelling is one the pages or the
application files show. Where a construct of the paper has no shown spelling,
the line is prose, and the section "What the stage files cannot state" lists
it.

| Spelling | Shown in |
|---|---|
| a declaration `name : set :: ["…"]`, a named set `X := ℝ₊`, a finite set of labels `{DB, DC}`, a bound as a second set written after `@`, `ρ : ℝ @ (-inf, 1)` | [Symbol conventions](../../docs/Bellman-Sym/reference/symbols-conventions.md) §9 |
| a function `𝑢(c : ℝ₊₊, h : ℝ₊₊) := …` with a state passed as an argument; a correspondence `Γ(x : ℝ₊₊) := (0, x]`, with two arguments `Γ(x : ℝ₊₊, h : ℝ₊) := (0, x + θ*p*h]` | `applications/durables/declaration/stages/keeper_cons/keeper_cons.bl`; [Constraints](../../docs/Bellman-Sym/10-constraints.md) §§1, 5.2 |
| a shock drawn on the arrival edge, `ε ~ N(0, 1)`; `N(μ, v)` takes the variance | `applications/durables/declaration/stages/tenure/tenure.bl`; [Shock distributions](../../docs/Bellman-Sym/reference/laws.md) §1 |
| a chain conditioned on the previous state, `DiscreteMarkov(Π, points, z_pre)`; a matrix and a vector as parameters, `Pi : ℝ`, `z_vals : ℝ` | [Shock distributions](../../docs/Bellman-Sym/reference/laws.md) §2; `applications/housing-owner/declaration/stages/housing_choice/housing_choice.bl` |
| a branch drawn by nature, `s : {survive, die}`, `s ~ Categorical((π_o, 1 - π_o))`, its backward block listing the two branch values alone and reading `s` under the expectation, `V = β*E_{s}((W_r[>], η*V_young[>])[s])` | [Branching](../../docs/Bellman-Sym/05-branching.md) §4; `applications/cagetti-denardi-2006/declaration/stages/retiree_death/retiree_death.bl` |
| a branching block on a control, `d : !ctrl @ {keep, adjust}`, with labeled blocks that compute on each branch; the value and marginal lines selecting by `[d]`; `d = argmax_{d}(V_kp[>], V_adj[>])` | [Branching](../../docs/Bellman-Sym/05-branching.md) §1; `tenure.bl` of the durables model |
| a finite-set control that enters the law of motion arithmetically, `H_choice : !ctrl @ XH`, chosen by `argmax_{H_choice}(V[>])`; an intermediate line in a forward block, `moved = …` | `housing_choice.bl` of the housing-owner model |
| selection from a tuple by the label a coordinate takes, `(x, y)[d]`, `(V_young[>], W_old[>])[s]`; the rule `family-selection` asks only for a key the family admits | [Expression forms](../../docs/Bellman-Sym/reference/forms.md) §2; [Refusals](../../docs/Bellman-Sym/reference/refusals.md), `family-selection` |
| `exp(…)`, `log(…)`, powers `x^(…)` | [Expression forms](../../docs/Bellman-Sym/reference/forms.md) §§1, 2; `tenure.bl` of the durables model |
| a decision state used as a coordinate of a backward value, `𝑢(c, h_d)`, without listing `h_d` in the header; a value declared on `[-inf, inf)`; a marginal value `dV : ℝ₊₊ @ !mrgnvl`; a state as a factor in a backward line, read as a pointwise map of an Aggregation | `keeper_cons.bl` of the durables model; `applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl`; [Constraints](../../docs/Bellman-Sym/10-constraints.md) §4 |
| the maximization written without `!doc`, the operation that outputs the policy, with its first-order conditions attached as properties by dotted ids, `:: [id=optimality.euler]`, printed under the Argmax operation with their corners | [Constraints](../../docs/Bellman-Sym/10-constraints.md) §4.1 (the stage `cons_argmax`), §5.1, §5.3 |
| the operative-line spelling, where the condition names the control: `𝑑𝑢(c) = β*dV_f[>] ⟂ m_f - c - c_p >= 0` and the two-bound chain `𝑑𝑢(c) = β*(1 + 𝑑𝜒(c_p))*dV_p[>] ⟂ 0 <= c_p <= w_d`; `𝑢_c(c) = β*dV_f[>] ⟂ m_d - c >= 0`; a binder whose set depends on another control, `argmax_{c : Γ_c(m), h_choice : Γ_h(m - c)}`; the bound of a clause as an expression in declared quantities | `applications/pension-retirement/declaration/stages/worker_saving/worker_saving.bl`; `applications/housing-frictions/declaration/stages/keeper_saving/keeper_saving.bl` and `adjuster_saving.bl`; [Constraints](../../docs/Bellman-Sym/10-constraints.md) §3, the Slack box |
| policy headers listing value and marginal-value fields but no state, `(dV[>] …, V[>] …) : !cntn`; the continuation states `k_n`, `a` and `h_n` are omitted from those headers | [Constraints](../../docs/Bellman-Sym/10-constraints.md) §§5.1, 5.2 |
| the candidate line of the endogenous grid method without a clause, `c[>] <= 𝑢_c_inv(β*dV_a[>])`, and with the clause, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0`, the grid line and the identification | `keeper_cons.bl` of the durables model; `applications/portfolio-choice/declaration/stages/cons/cons.bl`; [Constraints](../../docs/Bellman-Sym/10-constraints.md) §4.3 |
| a constant line in a forward block, `y_p_ret = 0` | `applications/pension-retirement/declaration/stages/retiree_saving/retiree_saving.bl` |
| the bequest as a stage: one marginal value at the decision perch and the chain rule in the arrival builder; a zero continuation value | `applications/durables/declaration/stages/bequest/bequest.bl` |

The marginal values carried through the model are those the paper's code
carries, the shadow values of liquid assets, of the housing stock and of the
mortgage (`solvers/Bellman.py`, `Lambda_A`, `Lambda_H`, `Lambda_M`), written
`dV_a`, `dV_h` and `dV_m` and named after the state coordinate of their perch
where the rule `marginal-value-pairing` requires it; the mortgage's marginal
value is declared on ℝ, since more debt lowers value. The value fields are
declared on `[-inf, inf)` because a keeper with no housing consumes no
housing services and utility (1) is then minus infinity at the paper's
negative ρ. Each coordinate a stage does not change is carried by one
identity line, `x_out = x_in`, which the fragments below abbreviate as "the
other coordinates pass through".

The ten coordinates of the paper's state vector X_t (Section 4.F, after
equation 15), and the share added by its online Appendix C, are, in the
stages: `a` liquid assets in ℝ₊; `a_dc` the pension balance in ℝ₊; `π` the
risky share in [0,1]; `h` the housing stock in ℝ₊, zero for a renter; `m` the
mortgage in ℝ₊; `P` the house price in ℝ₊₊; `ξ` the wage state in ℝ; `α` the
housing taste in (0,1); `β` the discount factor in (0,1); `plan` in
`Plan := {DB, DC}`. Tenure τ is a function of age, since enrollment age is
common and there is no unemployment (Section 5), and is a per-period
parameter. The plan is carried as a label-valued state through the working
periods; the paper's code solves the two plans as two separate problems
(Appendix D.3), which the pages admit equally as two routes of stages, and
"Assumptions to confirm" leaves that choice to AAS.

### `shocks`

| Perch | Fields |
|---|---|
| arrival | `a : ℝ₊`, `a_dc : ℝ₊`, `π_pre : [0,1]`, `h : ℝ₊`, `m : ℝ₊`, `P_pre : ℝ₊₊`, `ξ_pre : ℝ`, `α_pre : (0,1)`, `β_pre : (0,1)`, `plan : Plan`: the state at the end of the previous period, before this period's shocks; and the shocks `u`, `ε_d`, `ε_h`, `α`, `β` as arguments of the transition |
| decision | `a_s : ℝ₊` liquid assets with the return; `y_s : ℝ₊` earnings; `adc_s : ℝ₊` the balance with its return; `h_s : ℝ₊` the depreciated stock; `m_s : ℝ₊` the mortgage with interest; `P_s : ℝ₊₊`; `ξ_s : ℝ`; `α_s : (0,1)`; `β_s : (0,1)`; `plan_s : Plan`; `π_s : [0,1]` |
| continuation | the same eleven fields, unchanged |

The laws, written as the pages write them; `N` takes the variance:

```bl
u   : ℝ
u   ~ N(0, σ_u^2)                                :: ["innovation to the wage state, equation (3)"]
ε_d : ℝ
ε_d ~ N(0, σ_d^2)                                :: ["the pension-return shock of equation (7), shared by the mortgage rate of equation (10)"]
ε_h : ℝ
ε_h ~ N(0, σ_h^2)                                :: ["the housing-return shock, text after equation (14)"]
α   : (0,1)
α   ~ DiscreteMarkov(Π_α, α_pts, α_pre)          :: ["the housing taste, Section 4.A"]
β   : (0,1)
β   ~ DiscreteMarkov(Π_β, β_pts, β_pre)          :: ["the discount factor, Section 4.F"]
```

The arrival block applies the returns and forms earnings; `Y` is the level
exp(y(t, τ)) at the age of the period, a per-period parameter, zero from the
year of retirement on (equation 14, the cases t = T_R and t > T_R), and the
scale factors `scale_r` and `scale_s` are the paper's r and s of equation (7):

```bl
[id=arvl_to_dcsn, (a : ℝ₊, a_dc : ℝ₊, π_pre : [0,1], h : ℝ₊, m : ℝ₊, P_pre : ℝ₊₊, ξ_pre : ℝ, α_pre : (0,1), β_pre : (0,1), plan : Plan, u, ε_d, ε_h, α, β) : !arvl -> (a_s : ℝ₊, y_s : ℝ₊, adc_s : ℝ₊, h_s : ℝ₊, m_s : ℝ₊, P_s : ℝ₊₊, ξ_s : ℝ, α_s : (0,1), β_s : (0,1), plan_s : Plan, π_s : [0,1]) : !dcsn] {
    a_s    = R*a                                                                              :: [id=liquid_return]
    ξ_s    = φ*ξ_pre + u                                                                      :: [id=wage_state]
    y_s    = Y*exp(ξ_s)                                                                       :: [id=earnings]
    adc_s  = (π_pre*exp(r_r + scale_r*ε_d) + (1 - π_pre)*exp(r_s + scale_s*ε_d))*a_dc        :: [id=pension_return]
    h_s    = (1 - δ)*h                                                                        :: [id=depreciation]
    P_s    = (1 + r_h + ε_h)*P_pre/(1 - δ)                                                    :: [id=house_price]
    m_s    = exp(β_m*r_s + κ_m*ε_d)*m                                                         :: [id=mortgage_interest]
    α_s    = α
    β_s    = β
    plan_s = plan
    π_s    = π_pre
}
```

The three lines `liquid_return`, `pension_return` and `mortgage_interest` are
equations (12), (6) with (7), and (10) with the mean safe return r^s in its
markup term and the text after (12); `earnings` is
equation (3); `depreciation` is equation (8) before the investment; and
`house_price` is equation (9) with R^h_t = 1 + r^h + ε^h_t. One shock `ε_d`
drives the two pension returns and the mortgage rate, as equations (7) and
(10) write it, and it is realized at the start of the period with the price
and the wage shocks: the footnote of Appendix D.1 says that the pension and
the mortgage grids represent the state after the returns realized at the
start of the period, so the share chosen in the previous period and the
mortgage carried in both meet this period's draw. The code applies the price
shock without the division by 1 − δ (`solvers/conditionalExp.py`,
`gen_x_iid_prime_vals`), draws the two pension returns as independent chains
and the mortgage rate as a third chain aligned with the safe return
(`lifecycle_model.py`, lines 643 to 663 and 680 to 686); these are recorded
differences, and the stage follows the paper's equations. The
decision-to-continuation block is the identity on the eleven fields.
Backward, the decision builder is the identity on the value and the three
marginal values, and the arrival builder integrates over the five draws, the
marginal value of liquid assets multiplied by the return `R`, that of housing
by `1 - δ`, and that of the mortgage by the gross mortgage rate written out as
in `mortgage_interest`, as `dV_f[<] = E_{w}((1 + r_f)*dV_f)` of the pension
application writes a return inside the expectation. No policy block.

### `survival`

| Perch | Fields |
|---|---|
| arrival | the eleven fields of the continuation of `shocks`, `a_s` to `π_s` |
| decision | the same eleven, as `a_d` to `π_d` |
| continuation, branch `survive` | `a_sv : ℝ₊`, `y_sv : ℝ₊`, `adc_sv : ℝ₊`, `h_sv : ℝ₊`, `m_sv : ℝ₊`, `P_sv : ℝ₊₊`, `ξ_sv : ℝ`, `α_sv : (0,1)`, `β_sv : (0,1)`, `plan_sv : Plan`, `π_sv : [0,1]` |
| continuation, branch `die` | `a_bq : ℝ₊`, `adc_bq : ℝ₊`, `h_bq : ℝ₊`, `m_bq : ℝ₊`, `P_bq : ℝ₊₊`, the five quantities the bequest base of equation (33) reads |

The draw and the branches, written as [Branching](../../docs/Bellman-Sym/05-branching.md)
§4 and `retiree_death.bl` write a branch drawn by nature; `p_s` is the
probability of surviving into the age of the period, a per-period parameter
(the paper's p_{t−1} for the period of age t):

```bl
p_s : [0,1]                                      :: ["probability of surviving into the age of the period, Section 5"]

s : {survive, die}
s ~ Categorical((p_s, 1 - p_s))                  :: ["surviving or dying, with probabilities in the order of the labels"]

[id=dcsn_to_cntn, (a_d, y_d, adc_d, h_d, m_d, P_d, ξ_d, α_d, β_d, plan_d, π_d, s) : !dcsn -> ()] {
    [label=survive, () -> (a_sv : ℝ₊, y_sv : ℝ₊, adc_sv : ℝ₊, h_sv : ℝ₊, m_sv : ℝ₊, P_sv : ℝ₊₊, ξ_sv : ℝ, α_sv : (0,1), β_sv : (0,1), plan_sv : Plan, π_sv : [0,1]) : !cntn] {
        a_sv = a_d
        y_sv = y_d
        adc_sv = adc_d
        h_sv = h_d
        m_sv = m_d
        P_sv = P_d
        ξ_sv = ξ_d
        α_sv = α_d
        β_sv = β_d
        plan_sv = plan_d
        π_sv = π_d
    }
    [label=die, () -> (a_bq : ℝ₊, adc_bq : ℝ₊, h_bq : ℝ₊, m_bq : ℝ₊, P_bq : ℝ₊₊) : !cntn] {
        a_bq = a_d
        adc_bq = adc_d
        h_bq = h_d
        m_bq = m_d
        P_bq = P_d
    }
}

[id=cntn_to_dcsn, (V_sv[>] : [-inf, inf) @ !vlu, V_bq[>] : ℝ @ !vlu, dV_a_sv[>] : ℝ₊₊ @ !mrgnvl, dV_a_bq[>] : ℝ₊₊ @ !mrgnvl, dV_h_sv[>] : ℝ₊₊ @ !mrgnvl, dV_h_bq[>] : ℝ₊₊ @ !mrgnvl, dV_m_sv[>] : ℝ @ !mrgnvl, dV_m_bq[>] : ℝ @ !mrgnvl) : !cntn -> (V : [-inf, inf) @ !vlu, dV_a : ℝ₊₊ @ !mrgnvl, dV_h : ℝ₊₊ @ !mrgnvl, dV_m : ℝ @ !mrgnvl) : !dcsn] {
    V    = E_{s}((V_sv[>], V_bq[>])[s])                   :: [id=value]
    dV_a = E_{s}((dV_a_sv[>], dV_a_bq[>])[s])             :: [id=marginal_liquid]
    dV_h = E_{s}((dV_h_sv[>], dV_h_bq[>])[s])             :: [id=marginal_housing]
    dV_m = E_{s}((dV_m_sv[>], dV_m_bq[>])[s])             :: [id=marginal_mortgage]
}
```

The backward block lists the branch values alone, and `E_{s}` names the
shock, as `retiree_death.bl` writes it. The value line is the bracket of
equation (20), p_t V_{t+1} + (1 − p_t) b(B_{t+1}), without the factor β_t,
which the consumption stages of the previous period apply once. Equation (20)
prints the bequest term as B_{t+1}; the online Appendix C's Bellman equation
(37) prints b(B_{t+1}) with B_{t+1} defined in (38), and the stage follows
(37). The arrival block and the arrival builder are identities. No policy
block: the label is drawn, and the stage chooses nothing, which is the
condition under which a branching block on a shock is constructed
([Branching](../../docs/Bellman-Sym/05-branching.md) §4). Forward, the
distribution at the decision perch is extended by the law of `s`, and the
households drawn at each label are carried along that label's section; the
two masses add up to the mass at the decision perch.

### `plan_choice`

In the first period alone. Its arrival fields are the continuation fields of
`shocks`, `a_s` to `π_s`, so that it stands where `survival` stands in the
other periods, and its continuation fields are the survive-branch names,
`a_sv` to `π_sv`, so that `contribution` follows it by name. The control is
`plan_c : !ctrl @ Plan`, and the one line of its forward block that is not an
identity writes `plan_sv = plan_c`, as `housing_choice.bl` of the housing-owner
model writes `H_nxt = H_choice` for a finite-set control. The cost of the DC
alternative is the parameter `u_p`, the first line of equation (4) evaluated
at the enrollment age; the value line is `V = (0, -u_p)[plan_c] + V[>]`, the
deterministic part of equation (15), and the policy line
`plan_c = argmax_{plan_c}((0, -u_p)[plan_c] + V[>])`. The taste shocks ζ_db
and ζ_dc of equation (15) and the probability (16) are not written (see "What
the stage files cannot state"). The marginal values pass through.

### `contribution`

| Perch | Fields |
|---|---|
| arrival | `a_sv`, `y_sv`, `adc_sv`, `h_sv`, `m_sv`, `P_sv`, `ξ_sv`, `α_sv`, `β_sv`, `plan_sv`, `π_sv`, with the sets of the survive branch |
| decision | the same, as `a_d` to `π_d`; the control `v : !ctrl @ Vol`, `Vol := {v0, v1, v2, v3, v4, v5}`, the label `v0` the default rate of zero |
| continuation | `w_c : ℝ₊` cash on hand after take-home earnings; `adc_c : ℝ₊` the balance after the contributions; `adc_pre_c : ℝ₊` the balance before them, read by the cost of the next stage; `h_c`, `m_c`, `P_c`, `ξ_c`, `α_c`, `β_c`, `plan_c`, `π_c` unchanged |

The forward block, equations (12) and (6); the parameters `v_1` to `v_5` are
the five rates other than zero, `v_S` the standard rate, `v_E` the employer's
rate and `o` the share of the employer's contribution the DB account absorbs:

```bl
[id=dcsn_to_cntn, (a_d, y_d, adc_d, h_d, m_d, P_d, ξ_d, α_d, β_d, plan_d, π_d, v : !ctrl @ Vol) : !dcsn -> (w_c : ℝ₊, adc_c : ℝ₊, adc_pre_c : ℝ₊, h_c : ℝ₊, m_c : ℝ₊, P_c : ℝ₊₊, ξ_c : ℝ, α_c : (0,1), β_c : (0,1), plan_c : Plan, π_c : [0,1]) : !cntn] {
    v_rate    = (0, v_1, v_2, v_3, v_4, v_5)[v]                                             :: [id=contribution_rate]
    w_c       = a_d + (1 - v_S - v_rate)*y_d                                                :: [id=take_home]
    adc_c     = adc_d + (((1 - o)*v_E + v_rate)*y_d, (v_E + v_S + v_rate)*y_d)[plan_d]    :: [id=contributions]
    adc_pre_c = adc_d                                                                       :: [id=balance_before_contributions]
    h_c       = h_d
    m_c       = m_d
    P_c       = P_d
    ξ_c       = ξ_d
    α_c       = α_d
    β_c       = β_d
    plan_c    = plan_d
    π_c       = π_d
}
```

The value line adds the cost of equation (4) off the default,
`V = (0, -𝑢_v(a_d/R), -𝑢_v(a_d/R), -𝑢_v(a_d/R), -𝑢_v(a_d/R), -𝑢_v(a_d/R))[v] + V[>]`,
the deterministic part of equation (18) with the inner maximization over the
share left to the next stage, and the policy line is the maximization of the
same expression over `v`, as `housing_choice.bl` maximizes over its finite
control. The cost is read at `a_d/R`, the liquid asset before this period's
return, which is the a_t of equation (4): equation (12) applies the return as
R a_t, and the code passes the asset before returns
(`solvers/discreteChoice.py` 222, the grid coordinate that
`solvers/keeperEgm.py` 300 names "next liquid assets (before returns)"); the
stage declares `R` for the purpose. The cost function 𝑢_v(a) = ψ + exp(ν^v_0
+ ν^v_2 (t − ν^v_1)² + ν^v_3 max{0, ln a}) of equation (4) is written in prose
here: the age t is a per-period parameter, and the term max{0, ln a} has no
shown spelling. The marginal value of liquid assets passes through as that of
cash on hand, `dV_a = dV_w_c[>]`; the cost's own dependence on liquid assets
is left out of the marginal value, as the code leaves it out. The paper's
equation (24), the logit probability of each rate, is not written; the code
carries backward the probability-weighted average of the six values without
the cost and without the log-sum of (22), the cost entering the choice
probability alone (`model-brief.md` §5).

### `allocation`

| Perch | Fields |
|---|---|
| arrival | `w_c`, `adc_c`, `adc_pre_c`, `h_c`, `m_c`, `P_c`, `ξ_c`, `α_c`, `β_c`, `plan_c`, `π_c` |
| decision | the same, as `w_d`, `adc_d`, `adc_pre_d` to `π_d`; the control `π : !ctrl @ Share`, `Share := {π0, π1, π2, π3, π4, π5}`, the label `π3` the default share of 0.7 |
| continuation | `w_a : ℝ₊`, `adc_a : ℝ₊`, `π_a : [0,1]` the share chosen, as a number; `h_a`, `m_a`, `P_a`, `ξ_a`, `α_a`, `β_a`, `plan_a` unchanged |

The one forward line that is not an identity is
`π_a = (0, π_1, π_2, π_d, π_4, π_5)[π]`, the numeric share the next period's
`shocks` applies to the balance, equation (6); the first label is the share of
zero and `π_d` the default of 0.7. The field `adc_pre_d` is read by the cost
and passed on by no line. The value line is
`V = (-𝑢_π(adc_pre_d), -𝑢_π(adc_pre_d), -𝑢_π(adc_pre_d), 0, -𝑢_π(adc_pre_d), -𝑢_π(adc_pre_d))[π] + V[>]`,
the cost of equation (20) off the default, and the policy line maximizes the
same expression over `π`. The cost is read at the balance before this
period's contributions, the a^{dc}_t of the state vector X_t: by equation (6)
with the footnote of Appendix D.1 that balance is last period's balance with
the start-of-period return, before the contributions of equation (6) are
added; the code reads the cost at the balance after the contributions
(`solvers/conditionalExp.py` 307, its index 6), a recorded difference. The
cost 𝑢_π(a^{dc}) = ψ + exp(ν^r_0 + ν^r_1 t + ν^r_2 t² + ν^r_3 max{0, ln a^{dc}}
+ ν^r_4 u_p), equation (4), is prose for the same reasons as 𝑢_v. The
marginal values pass through. Equation (25) is not written. The paper's main
text places this stage before the consumption decisions, as here; its
Appendix D.2 and the code place the share choice after them, inside the
expectation (`model-brief.md`, "Timing map", difference 1).

### `payout`

In the year of retirement alone. Its arrival fields are the survive-branch
names `a_sv` to `π_sv`, and its continuation fields are those `tenure` arrives
at, `w_a` to `plan_a`. Equation (14), the case t = T_R: liquid wealth receives
the defined-benefit entitlement of a DB member and the balance of either plan,
`w_a = a_sv + (a_db, 0)[plan_sv] + adc_sv`, and the balance is emptied,
`adc_a = 0`; earnings are zero at this age by the parameter `Y` of `shocks`,
and the stage reads `y_sv` and adds nothing of it. The entitlement a^{db} =
f^{ACF} f^{LSF}(65) f^{ASF} τ_R ȳ of equation (5) is a product of parameters and
of the three-year average wage ȳ, which reads the earnings level at 65, not
the zero `Y` of the year of retirement, and the expectation of the two
previous wages given the current wage state under the reversed chain
(Appendix D.1, "Wages"); the code evaluates it at the age of retirement as
`DB_benefit(t, t − tzero, y(t, E[i]), …)` with t = R (`solvers/retiree_solver.py`
1624 to 1629; `tools/ls_model_functions.py` 301 to 331). The line is prose,
and its parameters are the age-65 earnings level and the deterministic
earnings levels at 64 and 63, the exp(y(t − j, τ − j)) of Appendix D.1's
formula for j = 1, 2, see "What the stage files cannot state". No policy
block; the value and the marginal values pass through, the marginal value of
liquid assets being that of cash on hand.

### `tenure`

| Perch | Fields |
|---|---|
| arrival | `w_a : ℝ₊` cash on hand, `adc_a : ℝ₊`, `π_a : [0,1]`, `h_a : ℝ₊` the depreciated stock, `m_a : ℝ₊` the mortgage due with interest, `P_a : ℝ₊₊`, `ξ_a : ℝ`, `α_a : (0,1)`, `β_a : (0,1)`, `plan_a : Plan` |
| decision | the same, as `w_d` to `plan_d`; the control `d : !ctrl @ {rent, adjust, keep}` |
| continuation, `rent` | `w_rt : ℝ₊` wealth after selling the house and repaying the mortgage; `adc_rt`, `π_rt`, `P_rt`, `ξ_rt`, `α_rt`, `β_rt`, `plan_rt` |
| continuation, `adjust` | `w_adj : ℝ₊` the same total wealth; `adc_adj`, `π_adj`, `P_adj`, `ξ_adj`, `α_adj`, `β_adj`, `plan_adj` |
| continuation, `keep` | `w_kp : ℝ₊` cash on hand before the mortgage is settled; `h_kp : ℝ₊` the stock kept; `m_kp : ℝ₊` the mortgage due, read by the redraw limit; `adc_kp`, `π_kp`, `P_kp`, `ξ_kp`, `α_kp`, `β_kp`, `plan_kp` |

```bl
[id=dcsn_to_cntn, (w_d, adc_d, π_d, h_d, m_d, P_d, ξ_d, α_d, β_d, plan_d, d : !ctrl @ {rent, adjust, keep}) : !dcsn -> ()] {
    [label=rent,   () -> (w_rt : ℝ₊, adc_rt : ℝ₊, π_rt : [0,1], P_rt : ℝ₊₊, ξ_rt : ℝ, α_rt : (0,1), β_rt : (0,1), plan_rt : Plan) : !cntn] {
        w_rt = w_d + P_d*h_d - m_d                       :: [id=wealth_after_sale]
        adc_rt = adc_d
        π_rt = π_d
        P_rt = P_d
        ξ_rt = ξ_d
        α_rt = α_d
        β_rt = β_d
        plan_rt = plan_d
    }
    [label=adjust, () -> (w_adj : ℝ₊, adc_adj : ℝ₊, π_adj : [0,1], P_adj : ℝ₊₊, ξ_adj : ℝ, α_adj : (0,1), β_adj : (0,1), plan_adj : Plan) : !cntn] {
        w_adj = w_d + P_d*h_d - m_d                      :: [id=total_wealth]
        adc_adj = adc_d
        π_adj = π_d
        P_adj = P_d
        ξ_adj = ξ_d
        α_adj = α_d
        β_adj = β_d
        plan_adj = plan_d
    }
    [label=keep,   () -> (w_kp : ℝ₊, h_kp : ℝ₊, m_kp : ℝ₊, adc_kp : ℝ₊, π_kp : [0,1], P_kp : ℝ₊₊, ξ_kp : ℝ, α_kp : (0,1), β_kp : (0,1), plan_kp : Plan) : !cntn] {
        w_kp = w_d                                       :: [id=cash_on_hand]
        h_kp = h_d                                       :: [id=housing_kept]
        m_kp = m_d                                       :: [id=mortgage_due]
        adc_kp = adc_d
        π_kp = π_d
        P_kp = P_d
        ξ_kp = ξ_d
        α_kp = α_d
        β_kp = β_d
        plan_kp = plan_d
    }
}

[id=cntn_to_dcsn, (V_rt[>] : [-inf, inf) @ !vlu, V_adj[>] : [-inf, inf) @ !vlu, V_kp[>] : [-inf, inf) @ !vlu, dV_w_rt[>] : ℝ₊₊ @ !mrgnvl, dV_w_adj[>] : ℝ₊₊ @ !mrgnvl, dV_w_kp[>] : ℝ₊₊ @ !mrgnvl, dV_h_kp[>] : ℝ₊₊ @ !mrgnvl, dV_m_kp[>] : ℝ @ !mrgnvl, d : !dcsn) -> (V : [-inf, inf) @ !vlu, dV_w : ℝ₊₊ @ !mrgnvl, dV_h : ℝ₊₊ @ !mrgnvl, dV_m : ℝ @ !mrgnvl) : !dcsn] {
    V    = (V_rt[>], V_adj[>], V_kp[>])[d]                                        :: [id=choice_value]
    dV_w = (dV_w_rt[>], dV_w_adj[>], dV_w_kp[>])[d]                               :: [id=marginal_cash]
    dV_h = (P_d*dV_w_rt[>], P_d*dV_w_adj[>], dV_h_kp[>])[d]                       :: [id=marginal_housing]
    dV_m = (-dV_w_rt[>], -dV_w_adj[>], dV_m_kp[>])[d]                             :: [id=marginal_mortgage]
}

[id=policy, (V_rt[>] : [-inf, inf) @ !vlu, V_adj[>] : [-inf, inf) @ !vlu, V_kp[>] : [-inf, inf) @ !vlu) : !cntn -> (d : {rent, adjust, keep} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_rt[>], V_adj[>], V_kp[>])                                    :: [id=choice]
}
```

The branches carry the sale of the depreciated stock at the price and the
settlement of the mortgage into the renter's and the adjuster's wealth
(equations 12 and 13 taken together, with the renter's H_t = 0 and the
adjuster's purchase left to its own stage), and leave the keeper's house and
mortgage in place. The renter pays no transaction cost, because the charge of
equation (12) is on the stock after the change, zero for a renter, and
Appendix D.2's cash on hand W̄ of the renter has no such charge; where the
settlement is written is the author's design choice. The keep entry of
`marginal_mortgage` is the keeper's own marginal value of the mortgage due,
read at the keep section `m_kp = m_d`, where the keeper's savings line
already settles the balance (the keeper's block below); the rent and adjust
entries are minus the marginal value of the wealth the settlement reduces. At
the paper's calibration the sale proceeds cover the mortgage with its
interest at every node the methods file names, so `w_rt` and `w_adj` are
declared nonnegative: the mortgage carried in is at most (1 − φ^C) of last
period's value by equation (11); the three-point Gauss–Hermite rule for the
price shock has its lowest node at −√3 × 0.042, where the housing return is
1.032 − 0.073 = 0.959, and the two-point rule for `ε_d` has its highest node
at +0.064, where the gross mortgage rate is exp(0.0649 + 0.33 × 0.064) = 1.090;
with φ^C = 0.2 the equity per unit of last period's value is at least
0.959 − 0.8 × 1.090 = 0.087, positive; the paper has no default. The value tuple and
the policy tuple agree entry by entry and in order, as
[Branching](../../docs/Bellman-Sym/05-branching.md) §1 requires; the three
marginal lines select in the same order. The arrival block and the arrival
builder are identities. Forward, the policy splits the distribution at the
decision perch into three, one per label, carried along that label's section,
and the three masses add up to the mass at the decision perch
([Branching](../../docs/Bellman-Sym/05-branching.md) §3). Appendix D.2 gives
the keep alternative to incumbent owners only; the stage writes no such
restriction, and the section "What the stage files cannot state" says why.
Appendix D.2 also writes the choice as a comparison of the three branch
values, as the policy line does.

### `renter_cons`

| Perch | Fields |
|---|---|
| arrival | `w_rt`, `adc_rt`, `π_rt`, `P_rt`, `ξ_rt`, `α_rt`, `β_rt`, `plan_rt` |
| decision | the same, as `w_d` to `plan_d`; the controls `c : ℝ₊₊ @ !ctrl` and `S : ℝ₊₊ @ !ctrl` |
| continuation | `a_nxt_rt : ℝ₊`, `adc_nxt_rt : ℝ₊`, `π_nxt_rt : [0,1]`, `h_nxt_rt : ℝ₊`, `m_nxt_rt : ℝ₊`, `P_nxt_rt : ℝ₊₊`, `ξ_nxt_rt : ℝ`, `α_nxt_rt : (0,1)`, `β_nxt_rt : (0,1)`, `plan_nxt_rt : Plan` |

The utility and its two marginal utilities, equation (1), with the taste as a
third argument; the parameter `ρ` is declared `ρ : ℝ @ (-inf, 1)`, and the paper's
estimate is negative:

```bl
𝑢(c : ℝ₊₊, S : ℝ₊₊, α : (0,1))   := (((1 - α)*c^ρ + α*S^ρ)^((1 - γ)/ρ) - 1)/(1 - γ)                 :: [id=util]
𝑢_c(c : ℝ₊₊, S : ℝ₊₊, α : (0,1)) := (1 - α)*c^(ρ - 1)*((1 - α)*c^ρ + α*S^ρ)^((1 - γ)/ρ - 1)        :: [id=marg_util_cons]
𝑢_S(c : ℝ₊₊, S : ℝ₊₊, α : (0,1)) := α*S^(ρ - 1)*((1 - α)*c^ρ + α*S^ρ)^((1 - γ)/ρ - 1)              :: [id=marg_util_services]
Γ_c(x : ℝ₊) := (0, x]                                                                                :: [id=feasible_consumption]
Γ_S(x : ℝ₊, P : ℝ₊₊) := (0, x/(φ_S*P)]                                                               :: [id=feasible_services]

[id=dcsn_to_cntn, (w_d, adc_d, π_d, P_d, ξ_d, α_d, β_d, plan_d, c : ℝ₊₊ @ !ctrl, S : ℝ₊₊ @ !ctrl) : !dcsn -> (a_nxt_rt : ℝ₊, adc_nxt_rt : ℝ₊, π_nxt_rt : [0,1], h_nxt_rt : ℝ₊, m_nxt_rt : ℝ₊, P_nxt_rt : ℝ₊₊, ξ_nxt_rt : ℝ, α_nxt_rt : (0,1), β_nxt_rt : (0,1), plan_nxt_rt : Plan) : !cntn] {
    a_nxt_rt = w_d - c - φ_S*P_d*S                       :: [id=savings]
    h_nxt_rt = 0                                         :: [id=no_housing]
    m_nxt_rt = 0                                         :: [id=no_mortgage]
    adc_nxt_rt = adc_d
    π_nxt_rt = π_d
    P_nxt_rt = P_d
    ξ_nxt_rt = ξ_d
    α_nxt_rt = α_d
    β_nxt_rt = β_d
    plan_nxt_rt = plan_d
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c, S) -> (V : [-inf, inf) @ !vlu, dV_w : ℝ₊₊ @ !mrgnvl) : !dcsn] {
    V    = 𝑢(c, S, α_d) + β_d*V[>]                        :: [id=value]
    dV_w = 𝑢_c(c, S, α_d)                                 :: [id=marginal_cash]
}

[id=policy, (V[>] : [-inf, inf) @ !vlu, dV_a[>] : ℝ₊₊ @ !mrgnvl) : !cntn -> (c : ℝ₊₊ @ !ctrl, S : ℝ₊₊ @ !ctrl) : !dcsn] {
    (c, S) = argmax_{c : Γ_c(w_d), S : Γ_S(w_d - c, P_d)}(𝑢(c, S, α_d) + β_d*V[>])   :: [id=optimality]
    𝑢_c(c, S, α_d) = β_d*dV_a[>] ⟂ w_d - c - φ_S*P_d*S >= 0                           :: [id=optimality.euler_liquid]
    𝑢_S(c, S, α_d) = φ_S*P_d*𝑢_c(c, S, α_d)                                          :: [id=optimality.intratemporal]
}
```

The savings line is equation (12) for a renter, with P^S_t = φ^S P_t (Section
4.D) and the sale proceeds already in `w_d`; the value line is equation (20)
with the discount factor read from the state. The policy block is written in
the first spelling of [Constraints](../../docs/Bellman-Sym/10-constraints.md)
§4.1: the maximization without `!doc` is the operation that outputs the two
controls, and the two conditions are its properties, attached by the dotted
ids, which the loading software prints under the Argmax operation and checks
against nothing. The property `euler_liquid` is the liquid-asset Euler
equation with its binding case, using the savings expression from the forward
law instead of reading `a_nxt_rt` at the continuation perch. It represents
the online Appendix C's (64) and (65), with
one difference of form: (64) as printed carries the bequest term as
(1 − p_t) b′(B_{t+1}), without β_t (1 + r) and outside the expectation,
whereas the stage's line, through the arrival builder of `shocks` and the
weighting of `survival`, carries β R (1 − p) b′ inside the expectation, the
form of (37) and of Appendix D's root condition for the renter's liquid
assets. The property `intratemporal` is its equation (74). The arrival block
and the arrival builder are identities; the arrival builder renames the
marginal value of cash to `dV_w_rt[<]`.

### `keeper_cons`

| Perch | Fields |
|---|---|
| arrival | `w_kp`, `h_kp`, `m_kp`, `adc_kp`, `π_kp`, `P_kp`, `ξ_kp`, `α_kp`, `β_kp`, `plan_kp` |
| decision | the same, as `w_d` to `plan_d`; the controls `m_nxt : ℝ₊ @ !ctrl` and `c : ℝ₊₊ @ !ctrl`, in that order, since the feasible consumption depends on the mortgage chosen |
| continuation | `a_nxt_kp : ℝ₊`, `h_nxt_kp : ℝ₊`, `m_nxt_kp : ℝ₊`, and `adc_nxt_kp`, `π_nxt_kp`, `P_nxt_kp`, `ξ_nxt_kp`, `α_nxt_kp`, `β_nxt_kp`, `plan_nxt_kp` |

```bl
Γ_m(x : ℝ₊) := [0, x]                                    :: [id=feasible_mortgage]
Γ_c(x : ℝ) := (0, x]                                     :: [id=feasible_consumption]

[id=dcsn_to_cntn, (w_d, h_d, m_d, adc_d, π_d, P_d, ξ_d, α_d, β_d, plan_d, m_nxt : ℝ₊ @ !ctrl, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a_nxt_kp : ℝ₊, h_nxt_kp : ℝ₊, m_nxt_kp : ℝ₊, adc_nxt_kp : ℝ₊, π_nxt_kp : [0,1], P_nxt_kp : ℝ₊₊, ξ_nxt_kp : ℝ, α_nxt_kp : (0,1), β_nxt_kp : (0,1), plan_nxt_kp : Plan) : !cntn] {
    a_nxt_kp = w_d - c + m_nxt - m_d                     :: [id=savings]
    h_nxt_kp = h_d                                       :: [id=housing_kept]
    m_nxt_kp = m_nxt                                     :: [id=mortgage]
    adc_nxt_kp = adc_d
    π_nxt_kp = π_d
    P_nxt_kp = P_d
    ξ_nxt_kp = ξ_d
    α_nxt_kp = α_d
    β_nxt_kp = β_d
    plan_nxt_kp = plan_d
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, dV_h[>] : ℝ₊₊ @ !mrgnvl, c) -> (V : [-inf, inf) @ !vlu, dV_w : ℝ₊₊ @ !mrgnvl, dV_h : ℝ₊₊ @ !mrgnvl, dV_m : ℝ @ !mrgnvl) : !dcsn] {
    V    = 𝑢(c, h_d, α_d) + β_d*V[>]                      :: [id=value]
    dV_w = 𝑢_c(c, h_d, α_d)                               :: [id=marginal_cash]
    dV_h = 𝑢_S(c, h_d, α_d) + β_d*dV_h[>]                 :: [id=marginal_housing]
    dV_m = -𝑢_c(c, h_d, α_d)                              :: [id=marginal_mortgage]
}

[id=dcsn_to_arvl, (V, dV_w, dV_h, dV_m) : !dcsn -> (V[<] : [-inf, inf) @ !vlu, dV_w_kp[<] : ℝ₊₊ @ !mrgnvl, dV_h_kp[<] : ℝ₊₊ @ !mrgnvl, dV_m_kp[<] : ℝ @ !mrgnvl) : !arvl] {
    V[<]       = V                                       :: [id=value]
    dV_w_kp[<] = dV_w                                    :: [id=marginal_cash]
    dV_h_kp[<] = dV_h                                    :: [id=marginal_housing]
    dV_m_kp[<] = dV_m                                    :: [id=marginal_mortgage]
}

[id=policy, (V[>] : [-inf, inf) @ !vlu, dV_a[>] : ℝ₊₊ @ !mrgnvl, dV_m[>] : ℝ @ !mrgnvl) : !cntn -> (m_nxt : ℝ₊ @ !ctrl, c : ℝ₊₊ @ !ctrl) : !dcsn] {
    (m_nxt, c) = argmax_{m_nxt : Γ_m((1 - φ_C)*P_d*h_d), c : Γ_c(w_d - m_d + m_nxt)}(𝑢(c, h_d, α_d) + β_d*V[>])   :: [id=optimality]
    𝑢_c(c, h_d, α_d) = β_d*dV_a[>] ⟂ w_d - c + m_nxt - m_d >= 0                                         :: [id=optimality.euler_liquid]
    -β_d*dV_m[>] = 𝑢_c(c, h_d, α_d) ⟂ 0 <= m_nxt <= (1 - φ_C)*P_d*h_d                                  :: [id=optimality.euler_mortgage]
}
```

The savings line is equation (12) for a non-adjusting owner, S_t = H_t and
h_t = 0, with the mortgage settled and the new balance drawn in the same
line. The line `marginal_housing` is the keeper's marginal value of the stock
kept, the marginal utility of the services it yields plus the discounted
continuation marginal value; the online Appendix C's recursion (78) writes
the non-adjusting branch without the term u_2, which the first-order condition
(g^H_t) and the Euler equation (70) carry, and the stage keeps it. The line
`marginal_mortgage` is the envelope derivative of the savings line with
respect to the mortgage due, −u_c(c), the Lagrangian of the liquid constraint
making it exact at the corner as well; where the redraw limit binds, the
limit's multiplier is added, in prose (item 6 of "What the stage files cannot
state"); the code carries this derivative as `Lambda_M`. The policy block is
in the first spelling of Constraints §4.1, since the mortgage enters its
condition only through the law of motion and a block that stated it by an
operative line alone would be refused under `output-defined`
([Constraints](../../docs/Bellman-Sym/10-constraints.md) §3, §5.3). The
property `euler_mortgage` is the online Appendix C's (66) to (69), which
write u_1(c_t) against the discounted mortgage cost, in the eliminated form
Constraints §3 requires, each clause written so that its residual is the
multiplier of its own bound: a unit borrowed finances consumption worth u_c,
which equals β dV_a[>] where the liquid constraint is slack and exceeds it by
that constraint's multiplier where it binds, so a line with β dV_a[>] on its
right, the form of Appendix D's auxiliary (84), would set that multiplier to
zero where the keeper consumes all cash with an interior mortgage; the
residual −β dV_m[>] − u_c is the difference of the two bound multipliers,
nonnegative at a zero balance and nonpositive at the collateral cap
([Constraints](../../docs/Bellman-Sym/10-constraints.md) §§2, 3); as with
(64), the bequest term stands inside the expectation where (66) prints it
outside. The
binder's feasible set is exact for the collateral cap: the consumption
feasible at each mortgage is the cash after the settlement and the new
balance, so the liquid constraint of `euler_liquid` is the set's upper end.
That condition writes the forward savings expression rather than reading
`a_nxt_kp` at the continuation perch.
The redraw limit of a non-adjuster, m_{t+1} ≤ R^m_t m_t + ι (Section 4.D), is
the second cap on `m_nxt`; since `m_d` is the balance with its interest, the
cap is `m_d + ι`, and the lesser of the two caps has no shown spelling, so the
binder and the chain carry the collateral cap alone and the redraw cap is
prose. Appendix D's equation (85) writes the cap as m + ι with m the mortgage
grid state after the interest realized at the start of the period (the
footnote of Appendix D.1), the same quantity; the code caps the new balance at
the post-interest balance plus its parameter `Chi` (`solvers/keeperEgm.py` 391,
418 and 673; 0.75 in the development settings), reads `iota` in no solver, and
its retiree solver has no redraw cap (`solvers/retiree_solver.py` 562 to 563,
where the cap is the grid's maximum). The arrival block is the identity.

### `adjuster_cons`

| Perch | Fields |
|---|---|
| arrival | `w_adj`, `adc_adj`, `π_adj`, `P_adj`, `ξ_adj`, `α_adj`, `β_adj`, `plan_adj` |
| decision | the same, as `w_d` to `plan_d`; the controls `c : ℝ₊₊ @ !ctrl`, `h_choice : ℝ₊₊ @ !ctrl` and `m_nxt : ℝ₊ @ !ctrl` |
| continuation | `a_nxt_adj : ℝ₊`, `h_nxt_adj : ℝ₊₊`, `m_nxt_adj : ℝ₊`, and `adc_nxt_adj`, `π_nxt_adj`, `P_nxt_adj`, `ξ_nxt_adj`, `α_nxt_adj`, `β_nxt_adj`, `plan_nxt_adj` |

```bl
Γ_c(x : ℝ₊) := (0, x]                                    :: [id=feasible_consumption]
Γ_h(x : ℝ₊, P : ℝ₊₊) := (0, x/((τ_H + φ_C)*P)]           :: [id=feasible_housing]
Γ_m(x : ℝ₊) := [0, x]                                    :: [id=feasible_mortgage]

[id=dcsn_to_cntn, (w_d, adc_d, π_d, P_d, ξ_d, α_d, β_d, plan_d, c : ℝ₊₊ @ !ctrl, h_choice : ℝ₊₊ @ !ctrl, m_nxt : ℝ₊ @ !ctrl) : !dcsn -> (a_nxt_adj : ℝ₊, h_nxt_adj : ℝ₊₊, m_nxt_adj : ℝ₊, adc_nxt_adj : ℝ₊, π_nxt_adj : [0,1], P_nxt_adj : ℝ₊₊, ξ_nxt_adj : ℝ, α_nxt_adj : (0,1), β_nxt_adj : (0,1), plan_nxt_adj : Plan) : !cntn] {
    a_nxt_adj = w_d - c - (1 + τ_H)*P_d*h_choice + m_nxt    :: [id=savings]
    h_nxt_adj = h_choice                                     :: [id=housing]
    m_nxt_adj = m_nxt                                        :: [id=mortgage]
    adc_nxt_adj = adc_d
    π_nxt_adj = π_d
    P_nxt_adj = P_d
    ξ_nxt_adj = ξ_d
    α_nxt_adj = α_d
    β_nxt_adj = β_d
    plan_nxt_adj = plan_d
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c, h_choice) -> (V : [-inf, inf) @ !vlu, dV_w : ℝ₊₊ @ !mrgnvl) : !dcsn] {
    V    = 𝑢(c, h_choice, α_d) + β_d*V[>]                 :: [id=value]
    dV_w = 𝑢_c(c, h_choice, α_d)                          :: [id=marginal_wealth]
}

[id=policy, (V[>] : [-inf, inf) @ !vlu, dV_a[>] : ℝ₊₊ @ !mrgnvl, dV_h[>] : ℝ₊₊ @ !mrgnvl, dV_m[>] : ℝ @ !mrgnvl) : !cntn -> (c : ℝ₊₊ @ !ctrl, h_choice : ℝ₊₊ @ !ctrl, m_nxt : ℝ₊ @ !ctrl) : !dcsn] {
    (c, h_choice, m_nxt) = argmax_{c : Γ_c(w_d), h_choice : Γ_h(w_d - c, P_d), m_nxt : Γ_m((1 - φ_C)*P_d*h_choice)}(𝑢(c, h_choice, α_d) + β_d*V[>])   :: [id=optimality]
    𝑢_c(c, h_choice, α_d) = β_d*dV_a[>] ⟂ w_d - c - (1 + τ_H)*P_d*h_choice + m_nxt >= 0             :: [id=optimality.euler_liquid]
    (1 + τ_H)*P_d*𝑢_c(c, h_choice, α_d) = 𝑢_S(c, h_choice, α_d) + β_d*dV_h[>]                        :: [id=optimality.euler_housing]
    -β_d*dV_m[>] = 𝑢_c(c, h_choice, α_d) ⟂ 0 <= m_nxt <= (1 - φ_C)*P_d*h_choice                       :: [id=optimality.euler_mortgage]
}
```

The savings line is equation (12) for an adjuster with the sale proceeds in
`w_d`, the purchase P_t h_t and the transaction cost τ_H P_t H_t combined into
(1 + τ_H) P_t H_t; the mortgage is bounded by equation (11) alone, since an
adjuster refinances costlessly (Section 4.D). The feasible stock admits the
mortgage-financed purchase of equations (11) and (12): with the new balance
at most (1 − φ^C) P h, the liquid constraint a_{t+1} ≥ 0 allows a stock up to
(w_d − c)/((τ_H + φ^C) P), the upper end of `Γ_h`; a purchase above the cash
then needs a mortgage of at least (1 + τ_H) P h − (w_d − c), a state-dependent
lower bound that the binder cannot write, since the greater of two bounds has
no shown spelling, and that the property `euler_liquid` with its clause
`⟂ w_d - c - (1 + τ_H)*P_d*h_choice + m_nxt >= 0` states instead, using the
forward savings law (item 6 of "What the stage files cannot state"). The policy
block is in the first spelling of Constraints §4.1 for
the reason given for the keeper, and its property `euler_mortgage` is in the
same eliminated form, with u_c on its right, which matters here: the buyer
who puts all cash into the house and borrows the shortfall, whom `Γ_h`
admits, binds the liquid constraint with an interior mortgage, where the form
of Appendix D's (84) would misstate the condition. The property
`euler_housing` is the online
Appendix C's housing Euler equation (70) read with the continuation marginal
value of housing, the form Appendix D.2 solves (its root condition before
equation 85), and it holds where the collateral constraint is slack; where
that constraint binds, equation (70) adds the multiplier of the collateral
constraint times φ^C, a term the stage cannot write because the multiplier of
a bound that names a control cannot be declared
([Constraints](../../docs/Bellman-Sym/10-constraints.md) §4.2). The bound of
`euler_mortgage` names the control `h_choice`, which the Slack box of
Constraints §3 admits, a bound being an expression in the stage's declared
quantities. The arrival block and the arrival builder are identities.

### `bequest`

| Perch | Fields |
|---|---|
| arrival | `a_bq : ℝ₊`, `adc_bq : ℝ₊`, `h_bq : ℝ₊`, `m_bq : ℝ₊`, `P_bq : ℝ₊₊`, the decedent's assets after this period's returns |
| decision | `B : ℝ₊` the bequest base, `P_d : ℝ₊₊` |
| continuation | the value `V[>]`, zero: a stage with no continuation state |

```bl
[id=arvl_to_dcsn, (a_bq : ℝ₊, adc_bq : ℝ₊, h_bq : ℝ₊, m_bq : ℝ₊, P_bq : ℝ₊₊) : !arvl -> (B : ℝ₊, P_d : ℝ₊₊) : !dcsn] {
    B   = a_bq + adc_bq + P_bq*h_bq - m_bq               :: [id=bequest_base]
    P_d = P_bq
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu, dV_B : ℝ₊₊ @ !mrgnvl) : !dcsn] {
    V    = θ*(B + k)^(1 - γ)/(1 - γ) + V[>]              :: [id=value]
    dV_B = θ*(B + k)^(-γ)                                :: [id=marginal_wealth]
}

[id=dcsn_to_arvl, (V, dV_B) : !dcsn -> (V[<] : ℝ @ !vlu, dV_a_bq[<] : ℝ₊₊ @ !mrgnvl, dV_h_bq[<] : ℝ₊₊ @ !mrgnvl, dV_m_bq[<] : ℝ @ !mrgnvl) : !arvl] {
    V[<]       = V                                       :: [id=value]
    dV_a_bq[<] = dV_B                                    :: [id=marginal_liquid]
    dV_h_bq[<] = P_bq*dV_B                               :: [id=marginal_housing]
    dV_m_bq[<] = -dV_B                                   :: [id=marginal_mortgage]
}
```

The base is the online Appendix C's equation (33), the beginning-of-period
wealth after all returns have accrued, read after `shocks` has applied the
returns and the depreciation, so that `h_bq` is already (1 − δ) H and `P_bq`
the price of the period; the value is equation (2). The block writes one
marginal value at the decision perch and the chain rule in the arrival
builder, using `P_bq` on the arrival side of the identity `P_d = P_bq`, as
the durables `bequest.bl` does. `V[>]` is the boundary datum
zero, as the durables bequest reads it. In the period after the last age the
stage stands after `shocks` alone and values the certain bequest; in every
other period it stands on the die branch of `survival`, and whether the
package supplies the zero continuation value there as it does in the
terminal period is the second question of "Assumptions to confirm". The base
is positive at the paper's calibration for the reason given under `tenure`,
so b(B) is defined, B + k > 0, throughout.

## The period and the trellis

A **trellis** is the sequence of the model's periods, counted backward from
the terminal one, with the mappings that join each period to the next in time
([Trellises](../../docs/Bellman-Sym/07-trellis.md) §1); a **connector**
identifies a continuation field of one stage with an arrival field of another,
within a period or between adjacent periods, and performs no calculation
([Periods](../../docs/Bellman-Sym/06-period.md) §2); the **recipe**, the file
`spec.yml`, names the trellis file and, for each stage key, the stage's file
and the files from which its parameter values, its settings and its methods
are read ([Trellises](../../docs/Bellman-Sym/07-trellis.md) §1).

The model has 85 periods: `periods[0]` is the period after the last age, in
which the wealth left by a household that has reached 100 is bequeathed with
certainty; `periods[h]` for h ≥ 1 is the period of age 101 − h, so that
`periods[1]` is age 100, `periods[36]` age 65, the year of retirement, and
`periods[84]` age 17, the year of enrollment. Ages 100 to 66 are the 35
retirement periods, `periods[1]` to `periods[35]`; ages 64 to 18 are the 47
working periods, `periods[37]` to `periods[83]`.

One period file lists all eleven stage keys and no connector; the recipe
restricts the stages that occur in some periods only, by `periods: [lo, hi]`
on their entries, as the recipe of the within-life model
`applications/benhabib-2019/` places its bequest in `periods[0]` alone
([The Bellman factory](../../docs/Bellman-Sym/08-bellman-factory.md) §3.4):

```yaml
!period
name: pension_period
stages:
  - shocks
  - survival
  - plan_choice
  - contribution
  - allocation
  - payout
  - tenure
  - renter_cons
  - keeper_cons
  - adjuster_cons
  - bequest
connectors: []
```

| Stage key | Active in | Ages |
|---|---|---|
| `shocks` | every period | 17 to 100 and after |
| `survival` | `periods: [1, 83]` | 18 to 100 |
| `plan_choice` | `periods: [84, 84]` | 17 |
| `contribution`, `allocation` | `periods: [37, 84]` | 17 to 64 |
| `payout` | `periods: [36, 36]` | 65 |
| `tenure`, `renter_cons`, `keeper_cons`, `adjuster_cons` | `periods: [1, 84]` | 17 to 100 |
| `bequest` | `periods: [0, 83]` | 18 to 100 and after |

The joins within a period are by name wherever the fields allow it. The
continuation fields of `shocks`, `a_s` to `π_s`, are the arrival fields of
`survival` and, in the first period, of `plan_choice`; the survive branch of
`survival` ends at `a_sv` to `π_sv`, the arrival fields of `contribution` in a
working period and of `payout` at 65, and `plan_choice` ends at the same
names; `contribution` ends at `w_c` to `π_c`, the arrival fields of
`allocation`; `allocation` and `payout` end at `w_a` to `plan_a`, the arrival
fields of `tenure`; the three branches of `tenure` end at the arrival fields of
the three consumption stages, `w_rt`, `w_adj` and `w_kp` with their companions;
and the die branch of `survival` ends at `a_bq` to `P_bq`, the arrival fields of
`bequest`. Two periods need a connector. In a retirement period, where
`contribution`, `allocation` and `payout` are absent, the survive branch is
joined to `tenure` by the mapping

`{a_sv: w_a, adc_sv: adc_a, π_sv: π_a, h_sv: h_a, m_sv: m_a, P_sv: P_a, ξ_sv: ξ_a, α_sv: α_a, β_sv: β_a, plan_sv: plan_a}`,

written on the template entry of those periods, whose own keys stand over the
file's, so that the entry repeats the template with the connectors it writes
in place of the file's ([Trellises](../../docs/Bellman-Sym/07-trellis.md)
§4); the field `y_sv`, the earnings of a retiree, which the parameter `Y`
makes zero, is read by no stage, and a continuation field no stage of the
period takes is an output of the period, which the inter-period mapping may
leave unjoined ([The Bellman factory](../../docs/Bellman-Sym/08-bellman-factory.md)
§7). In the period after the last age, `shocks` is joined to `bequest` by

`{a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq}`,

and its remaining continuation fields leave the period unjoined in the same
way. A connector names states; the value fields at a join are identified
along the edge those states establish and not by their spelling, as the
durables note, `applications/durables/economics.md`, and its `tenure.bl` show:
the tenure stage's `V_kp[>]` is the arrival value of `keeper_cons` because the
keep branch ends where that stage begins, and here likewise `survival`'s
`V_bq[>]` is the arrival value of `bequest`, because the die branch ends at
its arrival fields.

Each consumption stage ends the period at its own ten continuation fields,
and one inter-period mapping, standing for every adjacent pair, joins all
three to the arrival fields of the next period's `shocks`:

`{a_nxt_rt: a, adc_nxt_rt: a_dc, π_nxt_rt: π_pre, h_nxt_rt: h, m_nxt_rt: m, P_nxt_rt: P_pre, ξ_nxt_rt: ξ_pre, α_nxt_rt: α_pre, β_nxt_rt: β_pre, plan_nxt_rt: plan, a_nxt_kp: a, adc_nxt_kp: a_dc, π_nxt_kp: π_pre, h_nxt_kp: h, m_nxt_kp: m, P_nxt_kp: P_pre, ξ_nxt_kp: ξ_pre, α_nxt_kp: α_pre, β_nxt_kp: β_pre, plan_nxt_kp: plan, a_nxt_adj: a, adc_nxt_adj: a_dc, π_nxt_adj: π_pre, h_nxt_adj: h, m_nxt_adj: m, P_nxt_adj: P_pre, ξ_nxt_adj: ξ_pre, α_nxt_adj: α_pre, β_nxt_adj: β_pre, plan_nxt_adj: plan}`.

Each arrival field of `shocks` therefore has three sources, one per tenure
branch; the three routes are exclusive, and the arrival measure, the
distribution of the households who arrive there, is the sum of the three
incoming measures ([Trellises](../../docs/Bellman-Sym/07-trellis.md) §2). The
same mapping reaches `periods[0]`, whose `shocks` arrives at the same names.
No route returns from retirement to work, because the stages that choose a
contribution or a share are absent from the retirement periods.

The trellis file writes the period after the last age out, repeats the
template for the retirement periods with their connector, and repeats it
again for the year of retirement, the working periods and the first period;
the three one-period entries differ from their neighbors only in which stages
the recipe makes active there:

```yaml
!trellis
name: pensions_australia_life_cycle
periods:
  - stages: [shocks, bequest]
    connectors:
      - {a_s: a_bq, adc_s: adc_bq, h_s: h_bq, m_s: m_bq, P_s: P_bq}
  - {template: period.yml, repeat: 35, connectors: [{a_sv: w_a, adc_sv: adc_a, π_sv: π_a, h_sv: h_a, m_sv: m_a, P_sv: P_a, ξ_sv: ξ_a, α_sv: α_a, β_sv: β_a, plan_sv: plan_a}]}
  - {template: period.yml, repeat: 1}
  - {template: period.yml, repeat: 47}
  - {template: period.yml, repeat: 1}
inter_connectors:
  - {a_nxt_rt: a, adc_nxt_rt: a_dc, π_nxt_rt: π_pre, h_nxt_rt: h, m_nxt_rt: m, P_nxt_rt: P_pre, ξ_nxt_rt: ξ_pre, α_nxt_rt: α_pre, β_nxt_rt: β_pre, plan_nxt_rt: plan, a_nxt_kp: a, adc_nxt_kp: a_dc, π_nxt_kp: π_pre, h_nxt_kp: h, m_nxt_kp: m, P_nxt_kp: P_pre, ξ_nxt_kp: ξ_pre, α_nxt_kp: α_pre, β_nxt_kp: β_pre, plan_nxt_kp: plan, a_nxt_adj: a, adc_nxt_adj: a_dc, π_nxt_adj: π_pre, h_nxt_adj: h, m_nxt_adj: m, P_nxt_adj: P_pre, ξ_nxt_adj: ξ_pre, α_nxt_adj: α_pre, β_nxt_adj: β_pre, plan_nxt_adj: plan}
```

The recipe names, for each stage key, its stage file and its sources, with
`$fill` in every calibration and settings list and one methods slot per stage,
and carries the `periods:` ranges of the table above; its `registry` block
admits the names of the age schedules, which no stage declares. The values
that vary with age, the earnings level `Y` of `shocks`, the survival
probability `p_s` of `survival`, the age that enters the cost functions of
`contribution` and `allocation`, and the age-65 earnings level, the tenure
and the lump-sum factor of `payout`, are written into each period's records
by a function of the application's `code/`, after every `load_recipe` and
before the binding verbs, as `write_wage_schedule` of the durables model
writes its `Y` and `y_R`
([The Bellman factory](../../docs/Bellman-Sym/08-bellman-factory.md) §3.5).

## Calibration

The paper calibrates the environment in Section 5 and estimates the
preference and cost parameters by gender in Table 4 (Section 6.1). The code's
development settings supply the few values the paper does not print, in units
of $100,000: `settings/Eggs3.0_dev/settings.yml` holds the grid points, the
contribution rates, the shares, the earnings coefficients and the survival
list cited below, but lacks twelve keys the solver reads (`lambdas_s`,
`theta_scale`, `tau_M`, `tau_av`, `LBXI`, `UBXI`, `LBUC`, `UBUC`, `LBVF`,
`UBVF_fac`, `adj_constant_pi`, `adj_constant_V`) and cannot build the model
as it stands;
`settings/Eggs3.0_dev_lite/settings.yml` holds them all, and gives k = 4.38930
and `Chi` = 0.65 where the first file gives 2.64169 and 0.75. A stage binds
the parameters it declares.

| Stage | Parameters it declares | Values and where the paper gives them |
|---|---|---|
| `shocks` | `R`; `δ`; `Y` by age; `φ`, `σ_u`; `r_r`, `r_s`, `scale_r`, `scale_s`, `σ_d`; `β_m`, `κ_m`; `r_h`, `σ_h`; the chains `Π_α`, `α_pts`, `Π_β`, `β_pts` | R = 1.0223 (Section 5); δ = 0.011 (Section 5, from Fox and Tulip 2014); Y from the earnings equation, a quartic in age and a quadratic in tenure (Section 5), whose coefficients the paper does not print and the development settings hold as `lambdas`; the wage persistence and innovation are estimated by OLS (Section 5) and not printed, the development settings' `phi_w = 0.9044`, `sigma_w = 0.0922`; r^s = 1.93%, r^r = 4.76%, r^d = 2.88%, s = 0.54, r = 1.68, σ_{ε^d} = 0.064 (Section 5); β^m = 3.36, κ = 0.33 (Section 5); r^h = 0.032, σ_{ε^h} = 0.042 (Section 5); the taste chain from ᾱ, ρ_α, σ_α of Table 4 (0.555, 0.893, 0.013 for males; 0.565, 0.912, 0.011 for females) with q = 0.4 and η = 80 (Section 5); the discount chain from β̄, ρ_β, σ_β of Table 4 (0.900, 0.477, 0.024; 0.892, 0.455, 0.024); P_0 = 1 in 2010 (text after equation 14) |
| `survival` | `p_s` by age | Human Mortality Database, gender-specific, averaged over 2010 and 2014 (Section 5); the development settings' list `survival` |
| `plan_choice` | `u_p` | ψ and ν^p_0, ν^p_1, ν^p_2 of Table 4 at t₀ = 17: ln ψ = −6.650, ν^p = (−3.007, −0.137, 0.785 × 10⁻²) for males; ln ψ = 1.381, ν^p = (−1.803, −0.127, 0.770 × 10⁻²) for females |
| `contribution` | `R`; `v_1` to `v_5`, `v_S`, `v_E`, `o`; `ψ`, `ν_v0` to `ν_v3`, the age | v_S = 2.35%, v_E = 17%, o = 100% (Section 5); the five rates other than zero are not printed, the development settings' `vol_cont_points` (0.0108, 0.0340, 0.0857, 0.1815, 0.2700); ν^v = (−6.142, 40.772, −0.352 × 10⁻³, −0.560) for males, (−5.071, 46.291, −0.038 × 10⁻³, −0.354) for females (Table 4) |
| `allocation` | `π_1`, `π_2`, `π_d`, `π_4`, `π_5`; `ψ`, `ν_r0` to `ν_r4`, `u_p`, the age | π^d = 0.7 (Section 4.C); the other shares are not printed, the development settings' `risk_share_points` (0.107, 0.504, 0.952, 1.0 beside 0 and 0.7); ν^r = (−4.158, −0.057, 0.406 × 10⁻³, 0.078, 1.333) for males, (−2.719, −0.058, 0.581 × 10⁻³, 0.091, 2.163) for females (Table 4) |
| `payout` | `f_ACF`, `f_LSF`, `f_ASF`, `τ_R`; the age-65 earnings level and the deterministic earnings levels at 64 and 63 | f^{ACF} = 86.0%, f^{ASF} = 100% (Section 5); f^{LSF}(65) = 23% (equation 5); τ_R = 48 (Appendix D.1); the three levels from the same equation as `Y` |
| `renter_cons`, `keeper_cons`, `adjuster_cons` | `γ`, `ρ`; `φ_S`; `φ_C`; `τ_H`; `ι` (keeper, in prose) | γ = 3.234, ρ = −1.582 for males and 2.894, −1.611 for females (Table 4); φ^S = 0.06, φ^C = 20%, τ_H = 0.08, ι = $120,000 (Section 5) |
| `bequest` | `θ`, `k`, `γ` | ln θ = 9.844 for males and 11.576 for females (Table 4); k from Ding (2013) by marital status (Section 5), not printed, 2.64169 in the development settings and 4.38930 in the lite settings |

The taste-shock scales σ_p, σ^{DB}_v, σ^{DC}_v, σ^{DB}_π, σ^{DC}_π of Table 4
belong to the logit of equations (16), (24) and (25), which the stages do not
write. The enrollment, retirement and last ages, 17, 65 and 100 (Section 5),
are the ages of the trellis above.

## What the stage files cannot state

1. **The taste shocks and the logit.** The type-I extreme value shocks on the
   plan, the contribution and the share (equations 15, 17, 19), the
   probabilities (16), (24) and (25) and the log-sum values (22) and (23) have
   no spelling: no family of the laws page is the extreme value law, a
   `Categorical` weight may name a parameter, a state, a control or a shock
   and not a value field, and the expectation of a maximum over an undeclared
   shock cannot be written; the stages write the deterministic maximization.
2. **Age in the stage.** A stage carries no age index, so the earnings level
   Y (equation 3), the survival probability p_t (equation 20), the age t and
   the enrollment age t₀ in the cost functions (equation 4), and the
   earnings level, the tenure and the lump-sum factor at retirement (equation
   5) are parameters of each occurrence, one use of the stage file at one
   period, written per period by the application's code.
3. **The cost functions' kink.** The term max{0, ln a} of u_v and u_π,
   equation (4), has no shown spelling; the form `max` stands in the table of
   expression forms with no file that writes it, so the two cost functions are
   prose.
4. **The three-year average wage.** The entitlement a^{db} of equation (5)
   averages the earnings at 65 with the two previous wages, which Appendix D.1
   replaces by their expectation given the current state under the reversed
   wage chain; a function of the wage state defined through the chain's matrix
   has no shown spelling, and a draw of the two lagged states by
   `DiscreteMarkov(Π_rev, ξ_pts, ξ_d)` with an expectation over them is a
   reading of the laws page the pages do not show. The earnings level the
   average reads at 65 is not the parameter `Y` of `shocks`, which is zero in
   the year of retirement by equation (14), so the `payout` occurrence carries
   the age-65 earnings level and the deterministic earnings levels at 64 and
   63 as parameters of its own, as the code evaluates `DB_benefit` at the age
   of retirement with `y(t, E[i])`.
5. **The feasibility of keeping.** Appendix D.2 gives the keep alternative to
   incumbent owners only; a feasible set of a discrete control that depends on
   the state has no shown spelling, and the stage relies on the keep branch at
   a zero stock being dominated, since utility (1) is minus infinity at zero
   housing services for the paper's negative ρ. The keep branch is likewise
   infeasible where the cash does not cover the mortgage due net of the
   largest new balance, where the keeper's `Γ_c` is empty; the stage does not
   state that restriction either.
6. **Two bounds on one control.** The non-adjuster's mortgage is bounded by
   the collateral constraint (11) and by the redraw limit (Section 4.D), and
   `euler_mortgage` of `keeper_cons` carries the collateral cap alone; the
   adjuster's mortgage has the state-dependent lower bound
   (1 + τ_H) P h − (w_d − c) where that is positive, by equations (11) and
   (12), which the binder of `adjuster_cons` cannot write. The lesser of two
   caps and the greater of two floors have no shown spelling: `min` and `max`
   stand in the table of expression forms with no file that writes them.
7. **The collateral multiplier in the housing condition.** The housing Euler
   equation (70) of the online Appendix C adds the multiplier of the collateral
   constraint where it binds; a declared multiplier's bound may not name a
   control, and the adjuster's bound names `h_choice`, so `euler_housing`
   holds where the constraint is slack and the binding case is prose.
8. **The belief state of the taste.** The conviction and hesitation states of
   Section 4.A split the low taste into two chain states with one taste value;
   whether a chain declared on three points two of which are equal is admitted,
   or the belief must be a label state of its own, is not shown.
9. **The initial distribution** of liquid assets by enrollment age, housing of
   one dollar, no pension balance and the price of one (Section 5), which the
   forward operators need and no stage declares; the plan and the share at the
   arrival of the first `shocks` stage are read from it before any choice.
10. **The discretizations.** The five-state wage chain by Kopecky and Suen
    (2010), the three-point taste and discount chains, the two-point returns
    and the three-point price shock (Appendix D.1) are numerical choices for
    the methods and settings files; the chains for the taste and the discount
    factor are declared with matrix parameters because the paper gives them as
    chains, while the wage follows its continuous law (3).
11. **The concessional contribution cap** of the footnote to Section 4.C, a tax
    rule that appears in no equation of the paper.

## Assumptions to confirm

1. **The timing of the share choice.** The stages follow the main text's
   order, in which the share π_t is chosen before the consumption and housing
   decisions (equations 18 to 20); Appendix D.2 and the code choose it after
   them, inside the expectation of the consumption Euler equation, with the
   choice probabilities on the end-of-period states
   (`solvers/conditionalExp.py`; `model-brief.md`, "Timing map", difference
   1). AAS decides which the stage files follow.
2. **The bequest's continuation value outside the terminal period.** The
   bequest stage stands in every period from age 18 on and reads a zero
   continuation value `V[>]` in each; the pages supply the terminal
   continuation value as boundary data for the terminal period alone
   ([Trellises](../../docs/Bellman-Sym/07-trellis.md) §2; [The Bellman factory](../../docs/Bellman-Sym/08-bellman-factory.md)
   §3.4). Whether the package supplies the same datum to a stage that reads
   no continuation state in an earlier period is for AAS or the package.
3. **The plan as a state or as two routes.** The plan is a label-valued state
   carried through the working periods; the paper solves the two plans as two
   separate problems (Appendix D.3), and the pages admit either a label state
   or two routes of stages. For AAS only if he prefers the DB and DC routes
   as separate trellises.

## Numerical methods

The method tags below are those of [Method types](../../docs/Bellman-Sym/reference/methods.md);
each stage's methods file names them, and the settings file supplies the grids
of 35 points for liquid assets, the balance, housing and the mortgage and 11
for the price, the node counts and the simulation size (Appendix D.1; Section
5). A **handler** is the numerical routine, or the adapter that calls one,
registered to carry a method out
([Methodization](../../docs/Bellman-Sym/04-methodization.md) §4). The arrival
builder of `shocks` takes one expectation over its five shocks, and the three
rows below bind three methods by shock; Method types binds a method at an
operator occurrence or at its stage-wide name, and no shown file binds one
method per shock of one occurrence (`tenure.bl`'s `E_ε` integrates one
shock), so how the five draws are split among `!tauchen`, `!markov` and
`!gauss-hermite` is open for the build.

| Block | Method tag | What it realizes |
|---|---|---|
| the `argmax` of `optimality` in `renter_cons`, `keeper_cons` and `adjuster_cons`, which carries the conditions as its properties | `!root-find` at the operator `argmax` | the conditions solved at each decision state, as Appendix D.2 solves the renter's consumption and the mortgage by root finding. Two pages conflict here: Constraints §4.1 says of a first-order condition written as an operative line that "a root finder is attached to that line", while Method types admits `!root-find` at the operators `solve` and `argmax` only and refuses a methods file that places a method at a kind of place its row does not admit (`method-attachment`). This note follows Method types, which is printed from the package's method table, and the §4.1 spelling of the three blocks makes the argmax the one place in any case |
| the same `argmax` | `!egm` at the operator `argmax`, which inverts the property for the candidate ([Methodization](../../docs/Bellman-Sym/04-methodization.md) §2, the last row of its table); or, in the candidate-line spelling of `cons.bl` of the portfolio model, `!egm` on `policy` | Appendix D.2's endogenous grid over savings; the inverse of the marginal utility of consumption at given services is a root the code finds numerically (`uc_inv`), not a closed form |
| the selection among the candidates of the non-concave problem | `!FUES` at an `upper_env` operator, where the block writes the candidate value and the envelope as `applications/retirement-choice/declaration/stages/worker_cons/worker_cons.bl` does; or a handler setting named as the durables methods files name theirs, `upper_envelope: keeper_upper_envelope`, a setting whose value is `FUES` | the fast upper envelope scan with the forward and backward scan (Appendix D.2) |
| the `argmax` of `tenure`, `contribution`, `allocation` and `plan_choice` | `!max` | the comparison of the branch values and the deterministic choice; the logit of the paper is not a method of a declared operation (item 1 above) |
| `E_{u}` of `shocks` | `!tauchen`, with `n_income_states: 5` | the five-state chain; the paper uses the method of Kopecky and Suen (2010), which the table does not list |
| `E_{α}`, `E_{β}` of `shocks` | `!markov` or `!exact-markov` | the declared chains |
| `E_{ε_d, ε_h}` of `shocks` | `!gauss-hermite`, `n_nodes: [2, 3]`, one positive integer per shock in shock order, as `applications/portfolio-choice/declaration/stages/port/methods.yml` writes `n_nodes: [n_Ψ_nodes, n_θ_nodes]` | the two-point returns and the three-point price shock |
| `E_{s}` of `survival` | `!sum` | the two labels |
| the outputs of every backward builder | `!Linear`, `orders` and `bounds` by coordinate | the tables the code reads by linear interpolation (`eval_linear`) |
| the forward builders of `shocks`, `survival` and `tenure` | `!monte-carlo`, `n_paths: 10000` | the 10,000 simulated paths of Section 5 |
| the identity forward blocks | `!deterministic` | |

## Elaboration

Nothing is built. When the files are written, an author checks that each of
the eleven stage files constructs as `ElaboratedStage('<key>', symbolic)`;
that `survival` and `tenure` construct as branching stages, the first on a
shock in a stage that chooses nothing, the second on its control, and that
their value and policy tuples are in the order of the labels; that the three
consumption stages' policy builders print the Argmax operation with the
properties under it and no `Declared` section; that the period's joins are
derived from the fields without a cycle and that the retirement periods join
the survive branch to `tenure` through their connector; that the trellis
holds 85 periods and that the one inter-period mapping checks against the
fields of every adjacent pair; that the recipe's `periods:` ranges place each
stage where the table above places it; that the calibration binds every
declared parameter in every period after the age schedules are written; and
that `places()` on each stage lists the targets the methods files name.

## References

- Carroll, C. D. (2006). "The method of endogenous gridpoints for solving
  dynamic stochastic optimization problems." *Economics Letters* 91(3),
  312–320.
- De Nardi, M., French, E. and Jones, J. B. (2010). "Why do the elderly save?
  The role of medical expenses." *Journal of Political Economy* 118(1), 39–75.
- Ding, J. (2013). "Australian retirees' preferences between consumption,
  government pension, bequest and housing." SSRN working paper 2249691.
- Dobrescu, L. I. and Shanker, A. (2022). "A fast upper envelope scan method
  for discrete-continuous dynamic programming." SSRN working paper 4181302.
- Dobrescu, L. I., Shanker, A., Bateman, H., Newell, B. R. and Thorp, S.
  (2023). "Eggs and Baskets: Lifecycle Portfolio Dynamics." Working paper,
  version 43, with the online Appendix C, "Derivation of Euler equations."
  Section 4, Section 5, Section 6, Appendix D.
- Fox, R. and Tulip, P. (2014). "Is housing overvalued?" Reserve Bank of
  Australia Research Discussion Paper 2014-06.
- Kaplan, G., Mitman, K. and Violante, G. L. (2020). "The housing boom and
  bust: Model meets evidence." *Journal of Political Economy* 128(9),
  3285–3345.
- Kopecky, K. A. and Suen, R. M. H. (2010). "Finite state Markov-chain
  approximations to highly persistent processes." *Review of Economic
  Dynamics* 13(3), 701–714.
- Rust, J. (1987). "Optimal replacement of GMC bus engines: An empirical
  model of Harold Zurcher." *Econometrica* 55(5), 999–1033.
- Sommer, K. and Sullivan, P. (2018). "Implications of US tax policy for
  house prices, rents, and homeownership." *American Economic Review* 108(2),
  241–274.
- Yogo, M. (2016). "Portfolio choice in retirement: Health risk and the demand
  for annuities, housing, and risky assets." *Journal of Monetary Economics*
  80, 17–34.
