---
title: "The durables model: keeping or adjusting a housing stock"
audience: developer
type: model-note
topic: [applications]
---
# The durables model: keeping or adjusting a housing stock

> [!summary]
> A household holds financial assets and a house. Each period it chooses
> between keeping the house and selling it to buy another, and then chooses
> consumption; the adjuster also chooses the new house. This page states the
> economic environment, the four stages the model is written in (a period
> before the terminal one holds three, and the terminal period adds the
> bequest), how they are joined into a period and the period into a life
> cycle, the calibration, and
> what the stage files cannot state. The stages themselves are explained in
> `tenure.md`, `keeper_cons.md` and `adjuster_cons.md`. The lesson
> [Branching](../../tutorials/topics/branching.ipynb) of the tutorials
> collection constructs the tenure stage and draws a period and the trellis.

## The model and its source

The model is Application 2 of Dobrescu, L. I. and Shanker, A. (2026), "A fast
upper envelope scan method for discrete-continuous dynamic programming",
working paper, SSRN 4181302 (first draft 2022; the draft read here is that of
6 August 2026), Section 2.2: the environment and the Bellman equation in
equations (12) to (14), the Euler equations in (15) to (22), the solution
procedure in Box 2, the utility function in (26), and the calibration and the
accuracy results in Table 2. It belongs to the housing-frictions literature the
paper cites, Kaplan and Violante (2014) and Yogo (2016), from which the
dependence of utility on end-of-period housing is taken. The equations below
were also checked against the paper's replication code, the `examples/durables`
application of the FUES repository, whose Python code shows how the model is
solved and supplies the values the paper does not print.

A household lives from age $t_0$ to age $T$. It holds financial assets
$a \ge 0$, which earn the gross return $R$, and a housing stock $H > 0$, which
depreciates at the rate $\delta$ and is sold at the gross return $R_H$. Its
income $y_t(z)$ has an age profile and a persistent income state $z$ whose
logarithm follows a first-order autoregression,
$\log z' = \rho_z \log z + \sigma_z \varepsilon$ with $\varepsilon$ standard
normal. After the income state is observed, the household makes a discrete
choice: it keeps the house, consumes $c$ out of cash on hand $Ra + y_t(z)$ and
carries the depreciated house forward; or it sells the house, consumes out of
total wealth $Ra + R_H(1-\delta)H + y_t(z)$ and buys a new stock $H'$ at the
unit price $1 + \tau$. Per-period utility

$$
u(c, H') = \alpha \frac{c^{1-\gamma_c}}{1-\gamma_c}
         + (1-\alpha) \frac{(\kappa H')^{1-\gamma_h}}{1-\gamma_h}
$$

depends on consumption and on the housing stock held at the end of the period.
After the last decision the wealth left is valued by the bequest stage,
`declaration/stages/bequest/bequest.bl`. The choice between keeping and adjusting, which the cost of
adjusting makes a real one, leaves the value function non-concave, so inverting
the Euler equation on a grid gives several candidate policies at one state and
the optimal ones have to be selected by value. That selection is what the
paper's method performs, and it is why the model is one of the paper's
applications.

## The stages and the order of a period

A stage is one decision step with up to three information sets, arrival,
decision and continuation; the two consumption stages draw nothing before their
choice and begin at their decision perch. The model has four stages: a period
before the terminal one holds three, and the terminal period adds the bequest.

| Stage | What happens in it |
|---|---|
| `tenure` | The innovation to income is drawn on the arrival edge and the household chooses between keeping and adjusting. Its two branches end in different continuation spaces. |
| `keeper_cons` | The keeper chooses consumption out of cash on hand, with its housing stock fixed. |
| `adjuster_cons` | The adjuster chooses consumption and the new housing stock out of total wealth. |
| `bequest` | In the terminal period alone: the wealth left after the last decision, $R a + R_H (1 - \delta) h$, is valued by the bequest function, with a continuation value of zero. No choice is made. |

Forward, the period runs `tenure` first and then one of the two consumption
stages, the one the tenure choice selects. Backward, the two consumption stages
are computed first, in either order, because neither reads the other; the
tenure stage then compares the values they export, their decision values.

Write $v_{t+1}(a', H', z)$ for the arrival value of the next period's tenure
stage, which is the continuation value both consumption stages receive, and
$\phi$ for the standard normal density. The stages state

$$
V^{K}_t(w, H, z) = \max_{0 < c \le w}
   \bigl\{ u(c, H) + \beta\, v_{t+1}(w - c,\; H,\; z) \bigr\},
$$

$$
V^{A}_t(m, z) = \max_{\substack{c > 0,\; H' > 0 \\ c + (1+\tau)H' \le m}}
   \bigl\{ u(c, H') + \beta\, v_{t+1}(m - c - (1+\tau)H',\; H',\; z) \bigr\},
$$

$$
V_t(a, H, z) = \max\bigl\{
   V^{K}_t(Ra + y_t(z),\, (1-\delta)H,\, z),\;
   V^{A}_t(Ra + R_H(1-\delta)H + y_t(z),\, z) \bigr\},
$$

$$
v_t(a, H, z_-) = \int V_t\bigl(a, H, z_-^{\rho_z} e^{\sigma_z \varepsilon}\bigr)\,
   \phi(\varepsilon)\, \mathrm d\varepsilon .
$$

Composed, these are the paper's equation (14) with its wealth definition (12),
written with the depreciation rate and the housing return the replication code
keeps as free parameters; the paper's own case is $\delta = 0$ and $R_H = 1$.

Consumption satisfies $u_c(c) \ge \beta\, \partial_a v_{t+1}(a', H', z)$, with
equality where saving is positive, and the adjuster's housing choice satisfies
$(1+\tau)\, u_c(c) = u_h(H') + \beta\, \partial_H v_{t+1}(a', H', z)$. The
envelope conditions are $\partial_w V^{K} = \partial_m V^{A} = u_c(c)$ and
$\partial_H V^{K} = u_h(H) + \beta\, \partial_H v_{t+1}$; at the tenure decision
the selected branch supplies $\partial_a V_t = R\,\partial_w V^{K}$ or
$R\,\partial_m V^{A}$ and $\partial_H V_t = (1-\delta)\,\partial_H V^{K}$ or
$R_H(1-\delta)\,\partial_m V^{A}$, and the arrival marginal values are their
expectations. Substituting the policy functions into them gives the paper's
functional Euler equations (22) and (17), whose multiplier $\Theta$ in (21) is
the keeper's marginal value of housing.

## The period and the trellis

The branches of `tenure` end at the fields `w_kp`, `h_kp` and `z_kp` on the
keep branch and `w_adj` and `z_adj` on the adjust branch, and the consumption
stages begin at their decision states, so `period.yml` joins them by one
connector, `{w_kp: w_d, h_kp: h_d, z_kp: keeper_cons.z_d, w_adj: m, z_adj: adjuster_cons.z_d}`;
the income state `z_d` of both consumption stages is written with its stage
key: a bare name that two stages of the period declare is reported under
`endpoint-ambiguous`, and nothing is paired to it.

Each consumption stage ends the period at its own savings, housing and income
fields, and `trellis.yml` joins both to the arrival fields `a`, `h` and `z` of
the next period's tenure stage. Each of those three arrival fields therefore has
two sources, one per branch. The two routes are exclusive, because a household
reaches the next period through the branch it chose, and they belong in the one
inter-period mapping: the connector of one adjacent pair of periods carries
every route between them.

A connector names states. The value fields at a join are identified along the
edge those states establish and not by their spelling, since a value name is
local to its stage: the tenure stage's `V_kp[>]` is the decision value of
`keeper_cons`, whose derivatives `D_{w_kp}V_kp[>]` and `D_{h_kp}V_kp[>]` the
derivative lines of `declaration/stages/tenure/methods.bl` read, and its
`V_adj[>]` that of `adjuster_cons`, whose derivative `D_{w_adj}V_adj[>]` they
read, because the keep branch ends where the first stage begins and the adjust
branch where the second does.

The index of `periods[h]` counts periods before terminal, so `periods[0]` is the
last age and `periods[h]` is age $T - h$. With the ages of
`declaration/calibration/wage_schedule.yml` the trellis has 51 periods. The bequest is a
stage, `declaration/stages/bequest/bequest.bl`, active in the terminal period alone: it arrives at
`a_bq`, `h_bq` and `z_bq`, the savings, the housing stock and the income state
the two consumption stages continue to, reads a continuation value of zero, and
writes the value of the wealth left after the last decision; its methods file,
`declaration/stages/bequest/methods.bl`, an addition to the stage file that the
recipes name, writes the derivative lines of its two value builders. `trellis.yml` writes the terminal period out, the three stages of
`period.yml` and the bequest, with two connectors: the first from both
consumption stages to the bequest's arrival fields,
`{a_nxt_kp: a_bq, h_nxt_kp: h_bq, z_nxt_kp: z_bq, a_nxt_adj: a_bq, h_nxt_adj: h_bq, z_nxt_adj: z_bq}`,
and the second that of `period.yml`; the fifty earlier periods repeat
`period.yml`. The bequest's arrival fields
have names of their own because `tenure` arrives at `a`, `h` and `z`: a
connector to those names would also join the consumption stages to `tenure`
within the terminal period, and the inter-period mapping would reach the
bequest as well as `tenure`. `trellis.two-stages.yml` keeps the terminal period
without `tenure` and the periods not joined to one another, the route the
factory's acceptance tests read.

## Calibration

`declaration/calibration/durables.yml` holds the values of the replication code, which
produced Table 2 of the paper: $\beta = 0.945$, $R = 1.045$, $R_H = 1$, $\delta = 0$,
$\tau = 0.12$, $\alpha = 0.7$, $\gamma_c = 3.5$, $\gamma_h = 1.5$,
$\kappa = 0.06$, $\rho_z = 0.82$ and $\sigma_z = 0.11$. Table 2 prints
$\beta = 0.94$ and $r = 0.04$, the first two of these to two decimal places, and
reports the adjustment cost at 0.05, 0.07 and 0.12. The bequest parameters are
$\theta = 1.3498$ and $K = 1.3$.

Income while the household works is
$Y_t = \nu \exp(\lambda_0 + \lambda_1 t + \lambda_2 t^2 + \lambda_3 t^3 +
\lambda_4 t^4 + \lambda_5 s_t + \lambda_6 s_t^2)$ per unit of the income state,
with $s_t = \min(30, t - 20)$ years of job tenure and $\nu = 10^{-5}$; from age
61 it is the retirement income 0.1, which does not depend on the income state.
At the calibrated coefficients, income per unit of the income state is about
0.75 at age 40 and about 0.90 at age 60. The paper takes the wage function from
Dobrescu, L. I., Shanker, A., Bateman, H., Newell, B. R. and Thorp, S. (2025),
"Housing and pensions: Complements or substitutes in portfolio allocation?",
SSRN working paper 4069226, whose earnings equation is a quartic in age and a
quadratic in job tenure for log earnings with an autoregressive component; the
seven coefficients are taken from the replication code, since that paper does
not print them.

The paper has the household start work at age 20, retire at 60 and live to 70,
and the run that produced Table 2 uses the first of these; the code's
calibration file instead starts at 40, which shortens the life cycle without
changing any equation.

Two equations here follow the replication code rather than the printed paper.
Equation (26) prints the utility function with the exponents $\gamma_C - 1$ and
$\gamma_H - 1$ and with $\kappa H^{\gamma_H - 1}$, which is convex at the
curvatures the paper calibrates, against the concavity Section 2.2.1 assumes;
the code has $1 - \gamma_c$ and $1 - \gamma_h$ and $(\kappa H)^{1-\gamma_h}$,
which is the form used above. The paper defines the bequest as
$\bar\theta\, u(x, 0)$, which is minus infinity under that utility whenever
housing curvature exceeds one; the code values the bequest as consumption of
the wealth left, shifted by $K$, and that is the function `declaration/stages/bequest/bequest.bl`
writes.

## What the stage files cannot state

1. **The age profile of income.** A stage carries no age index, so the earnings
   level $Y$ and the retirement income $y_R$ of `tenure.bl` are parameters of
   each occurrence. The application's function `write_wage_schedule` in
   `code/wage_schedule.py` evaluates the schedule of `declaration/calibration/wage_schedule.yml`
   at the age of each period, $T - h$, and writes $Y$ and $y_R$ into that
   period's `tenure` record, after every `load_recipe` and before the binding
   verbs; `declaration/calibration/durables.yml` holds no value for them. The stage states
   the shape $y(z) = Yz + y_R$ and no more.
2. **The initial distribution** of assets, housing and the income state, which
   the forward operators need and no stage declares.
3. **The discretisation of income.** The stages declare a continuous
   autoregression with a standard normal innovation. The finite Markov chain the
   code integrates against, the number of its states, the width it spans and the
   floor on its transition probabilities are numerical choices, and they are in
   `declaration/stages/tenure/methods.bl` and `declaration/settings/durables.yml`.
4. **The rule at a tie** between keeping and adjusting, which the code fixes at
   adjusting. A tie leaves the choice undetermined in the model, so the rule is a
   setting of the selection method.

## Numerical methods

`declaration/stages/keeper_cons/methods.bl`, `declaration/stages/adjuster_cons/methods.bl` and
`declaration/stages/tenure/methods.bl`, the methods files beside the stage files, are additions
to them: each types the routines of the replication code at the places of the stage, with the
settings they read as keyword arguments and declares those settings with their sets, and
`declaration/settings/durables.yml` supplies the values. The two consumption stages' files also
write the endogenous grid lines on the policy builder, whose stage files state the maximizations
alone, and every file writes the derivative lines of its value builders. In outline: the keeper inverts the Euler
equation on a grid of savings for each income state and housing point, adds the
constrained segment at the lowest saving, and selects among candidates by value
with the fast upper envelope scan; the adjuster follows Box 2 of the paper, with
the roots of the housing first-order condition along the savings grid for each
point of a grid of new housing, the point at the borrowing limit, the endogenous
grid of total wealth, and the same envelope scan over the pooled candidates; the
tenure stage compares the two branch values, reads the consumption stages'
decision functions by interpolation, and integrates over income with Tauchen's
chain. The nested alternative the paper benchmarks against, which maximizes over
new housing by a sectioned golden-section search, is a second addition of the
adjuster, `declaration/stages/adjuster_cons/methods.adjuster_method.bl`, which no
recipe of the folder names; a recipe that wants it names it after the first in
the stage's methods list.

Two conventions of the code differ from the stage files without changing the
model. The code multiplies the marginal values by the discount factor in the
tenure stage, whereas the stages here discount in the consumption stages, where
the utility is; the composed Euler equations agree. The code also reads the
keeper's continuation value and its marginals at the housing grid point the
household arrives with rather than at the depreciated stock it keeps; the two
coincide at the calibrated $\delta = 0$ and differ at any positive depreciation
rate, which the stage files admit.

## Elaboration

`keeper_cons.bl` and `adjuster_cons.bl` construct their three views and reach
the specified version with `declaration/calibration/durables.yml`, the additions
`methods.bl` in their stage folders and `declaration/settings/durables.yml` bound;
`bequest.bl` constructs, calibrates from the same calibration file and takes the
derivative lines its addition writes. `tenure.bl` constructs as a
branching stage, and a period listing it elaborates. Loading the four files
with the present package prints:

```text
applications/durables/declaration/stages/bequest/bequest.bl: ElaboratedStage('bequest', symbolic)
applications/durables/declaration/stages/keeper_cons/keeper_cons.bl: ElaboratedStage('keeper_cons', symbolic)
applications/durables/declaration/stages/adjuster_cons/adjuster_cons.bl: ElaboratedStage('adjuster_cons', symbolic)
applications/durables/declaration/stages/tenure/tenure.bl: ElaboratedStage('tenure', symbolic)
```

The trellis is assembled as a dictionary of periods and elaborated with
`elaborate_trellis`. The two period factory calls of the earlier design are not
in the package: `load_trellis` and `load_recipe` of `bellman.trellis` write the
records, and `load_recipe` reads `trellis.yml` through the recipe
`spec.yml`.

## The variant with Cobb–Douglas utility

The replication code carries a second parameterisation, in which utility is
$\bigl(c^{\alpha}(H' + \underline d)^{1-\alpha}\bigr)^{1-\rho}/(1-\rho)$ with a
floor $\underline d$ on housing services, the bequest is the indirect utility of
spending the wealth left, a zero housing stock is admissible, and the income
process has its own persistence and innovation standard deviation. Its states,
timing, choices and constraints are those above, and the model of Section 2.2 is
stated for any concave, jointly differentiable and increasing utility, so the
variant is a second specification of this model rather than a second model. It
is not written as stage files here: they would repeat these three stages with
another definition of $u$ and of its derivatives. Two of its consequences are
worth recording, because they show where the stage files would differ. The
marginal utility of consumption depends on housing, so the keeper's inverse
Euler equation reads the housing state; and the marginal utility of housing
depends on consumption, so the adjuster's point at the borrowing limit is the
root of a residual rather than a closed form.

## References

- Dobrescu, L. I. and Shanker, A. (2026). "A fast upper envelope scan method for
  discrete-continuous dynamic programming." Working paper, SSRN 4181302.
  Section 2.2, Box 2 and Table 2.
- Dobrescu, L. I., Shanker, A., Bateman, H., Newell, B. R. and Thorp, S. (2025).
  "Housing and pensions: Complements or substitutes in portfolio allocation?"
  SSRN working paper 4069226.
- Druedahl, J. and Jørgensen, T. H. (2017). "A general endogenous grid method for
  multi-dimensional models with non-convexities and constraints." *Journal of
  Economic Dynamics and Control* 74, 87–107.
- Iskhakov, F., Jørgensen, T. H., Rust, J. and Schjerning, B. (2017). "The
  endogenous grid method for discrete-continuous dynamic choice models with (or
  without) taste shocks." *Quantitative Economics* 8(2), 317–365.
- Kaplan, G. and Violante, G. L. (2014). "A model of the consumption response to
  fiscal stimulus payments." *Econometrica* 82(4), 1199–1239.
- Tauchen, G. (1986). "Finite state Markov-chain approximations to univariate and
  vector autoregressions." *Economics Letters* 20(2), 177–181.
- Yogo, M. (2016). "Portfolio choice in retirement: Health risk and the demand
  for annuities, housing, and risky assets." *Journal of Monetary Economics* 80,
  17–34.
