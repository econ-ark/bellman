---
title: "The housing model with renting and a capital income tax"
audience: developer
type: model-note
topic: [applications]
---
# The housing model with renting and a capital income tax

This folder writes, in Bellman-SYM, the discrete housing choice model of
Dobrescu and Shanker, "A fast upper envelope scan method for
discrete-continuous dynamic programming" (SSRN Working Paper No. 4181302;
the draft of 6 August 2026 is the one read here), §2.3, "Application 3: a
discrete housing choice model", equations (27) to (38), Box 3 and Tables 3
and 4. That application extends the housing model of Fella, G. (2014), "A
generalized endogenous grid method for non-smooth and non-concave problems",
*Review of Economic Dynamics* 17(2), 329-344 (checked here in its
working-paper version, Queen Mary University of London, School of Economics
and Finance, Working Paper 677, 2011, §2 and §5), in two ways: the household
may rent instead of owning, and the return on financial assets is taxed by a
piecewise-linear schedule with kinks and jumps.

The model is the paper's illustration of an upper envelope that has to work
without monotone policies. The discrete housing choice makes the continuation
value non-concave, and the tax thresholds add flat segments and jumps to the
savings policy, so the candidate points the endogenous grid method produces
are a correspondence rather than a function.

## The economic environment

A household lives twenty periods. It enters a period with financial assets
`a ≥ 0`, a housing stock `H ≥ 0` and last period's income `y_pre`. Income
follows a finite Markov chain on a set of positive levels. After the income
draw the household chooses between owning and renting.

An owner chooses a housing size `H_new` from a finite set, pays
`(1 + φ)·H_new` for it and receives `H` for the stock it holds, both only
when the size changes, and consumes out of what is left of

    (1 + r)·a − T(a) + y,

where `T` is the tax on assets. A renter sells the house, rents a quantity
`S` of housing services from a finite set at the price `P_r`, and consumes
out of

    (1 + r)·a − T(a) + H + y − P_r·S.

Both save what they do not consume, and no borrowing is allowed, so savings
are non-negative. Utility in a period is

$$u(c, h) = \alpha \log c + (1 - \alpha)\log\bigl(\kappa (h + \iota)\bigr),$$

with `h = H_new` for an owner and `h = ϑ·S` for a renter. The tax is the
schedule of equation (27),

$$T(a) = B_k + \tau_k\,(a - a^0_k) \quad\text{for } a \text{ in bracket } k,$$

ten brackets whose base values `B_k` make the schedule continuous except at
three thresholds, where it jumps.

## The stages and their order

Each of the five stages is one `.bl` file with its own page.

| Stage | File | What it decides |
|---|---|---|
| Tenure choice | `tenure_choice.bl` | Draws income and chooses between owning and renting. |
| Owner housing | `owner_housing.bl` | Chooses the housing size an owner holds at the end of the period. |
| Owner consumption | `owner_cons.bl` | Chooses an owner's consumption and savings. |
| Renter housing | `renter_housing.bl` | Chooses the quantity of housing services a renter rents. |
| Renter consumption | `renter_cons.bl` | Chooses a renter's consumption and savings. |

In forward time the tenure choice comes first; its own branch leads to the
owner's two stages and its rent branch to the renter's two. Value runs the
other way, from the two consumption stages back to the tenure choice. The
stage-dependency graph the period factory derives from the fields has the
edges tenure choice to owner housing, tenure choice to renter housing, owner
housing to owner consumption, and renter housing to renter consumption.

The two housing stages and the two consumption stages have no arrival perch:
each is entered at its decision perch, and since several of them name their
decision states alike, `period.yml` writes each join as a connector between
two named stages: `(a_o, H_o, y_o)` of the own branch to the owner's housing
stage's `(a_d, H_d, y_d)`, `(w_r, y_r)` of the rent branch to the renter's
housing stage's `(w_d, y_d)`, `(w_own, H_own, y_own)` of the owner's housing
stage to the owner's consumption stage's `(w_d, H_d, y_d)`, and
`(w_rent, S_rent, y_rent)` of the renter's housing stage to the renter's
consumption stage's `(w_d, S_d, y_d)`.

`trellis.yml` repeats the period twenty times and joins period `h+1` to
period `h` with one inter-period connector,

    {a_nxt_o: a, H_nxt_o: H, y_nxt_o: y_pre,
     a_nxt_r: a, H_nxt_r: H, y_nxt_r: y_pre}

which carries both routes into the one arrival perch of the next tenure
choice: savings become assets, the housing size chosen (zero on the renter's
route, written as an equation in `renter_cons.bl`) becomes the stock held,
and this period's income becomes next period's `y_pre`. Each arrival field
therefore has two sources, one on each branch of the discrete choice, and a
household is on exactly one of them. The trellis pages state that a connector
for one adjacent period pair contains every route that is needed; they do not
yet say how a connector that merges two branch routes into one arrival field
is read, and this is the place where that question arises.

## The Bellman equations

Write `V_t(a, H, y_pre)` for the value at the arrival perch of the tenure
stage, `V^oh` and `V^rh` for the values of owning and of renting once income
is known, and `V^oc`, `V^rc` for the values at the two consumption stages.
With `w_own` and `w_rent` the cash of the two routes,

$$V^{oc}_t(w, H_{new}, y) = \max_{0 < c \le w}\bigl\{u(c, H_{new}) + \beta\,V_{t+1}(w - c,\ H_{new},\ y)\bigr\},$$

$$V^{rc}_t(w, S, y) = \max_{0 < c \le w}\bigl\{u(c, \vartheta S) + \beta\,V_{t+1}(w - c,\ 0,\ y)\bigr\},$$

$$V^{oh}_t(a, H, y) = \max_{H_{new} \in \mathcal H} V^{oc}_t(w_{own},\ H_{new},\ y),\qquad V^{rh}_t(w_r, y) = \max_{S \in \mathcal S} V^{rc}_t(w_{rent},\ S,\ y),$$

$$V_t(a, H, y_{pre}) = \sum_{y} \Pi(y_{pre}, y)\, \max\bigl\{V^{oh}_t(a, H, y),\ V^{rh}_t((1+r)a - T(a) + H,\ y)\bigr\}.$$

These are equations (32) to (36) of the paper with the expectation over
income moved from the consumption stages to the arrival edge of the next
tenure stage, which is where the FUES solver takes it. The two readings give
the same model: the paper's `V_t(a, y, H)`, whose state includes the income
just drawn, is the quantity inside the sum above.

The first-order condition of the consumption stages is equation (37),
`α/c = β(1 + r − τ_k)·E[α/c']`, with inequality at zero savings and the
one-sided conditions (38) at a bracket threshold. The stage files state the
interior condition and the condition at zero savings; §"What the stages do
not state" below records what they leave to the method.

## Calibration

`declaration/calibration/housing-renting.yml` takes its values from the configuration
`STD_RES_SETTINGS_4_TAXES` of the replication code of the paper. It is the
configuration the tax runs name, and the grid sizes and numbers of housing
sizes of its experiment set are the design of Table 4; Table 3 is the same
model with the tax switched off. Its values are `β = 0.93`, `r = 0.06`,
`α = 0.77`, `κ = 0.075`, `ι = 0.01`, `φ = 0.07`, `P_r = 0.1`, `ϑ = 0.5`,
seven housing sizes and seven rental quantities equally spaced on the interval
from zero to five, and the ten tax brackets of the schedule whose picture is
the paper's Appendix Figure 9. The same values appear in the notes to Table 3,
which write the transaction cost as `τ = 0.07`; the services scale `ϑ = 0.5`
appears in the notes to Appendix Table 7. Setting every `B_T` and every `τ_T`
to zero gives the model without the tax, the model of Table 3.

`declaration/settings/housing-renting.yml` holds the numerical choices: the asset, cash and savings grids
of 4,000 points on the interval from `1e-8` to 40, the upper envelope FUES
with its options, the number of candidate points at the borrowing limit and
at each tax threshold, and the dense grid of the value function iteration the
paper compares against.

The income chain is the one place where a parameter has no value in the file.
The chain of the runs discretises `log y = ζ + ε`, with `ζ' = ρζ + η`,
`ρ = 0.977`, standard deviation of `η` equal to 0.024 and of `ε` equal to
0.063, by the Rouwenhorst method with seven points for each component, which
gives 49 states, and divides the levels by their mean. Its transition matrix
and its vector of levels cannot be written as values of the parameters `Π`
and `z`, for the reason in the next section.

## What the stages do not state

- **The horizon and the terminal value.** The twenty periods are the
  trellis's, not a stage's, and the terminal continuation value is boundary
  data the trellis receives, recorded in prose in `trellis.yml`.
- **A set of a matrix or of a vector whose length is open.** The income
  chain's transition matrix `Π` and its levels `z` are declared by stand-in
  sets, `[0,1]` and `ℝ₊₊`, since the language has no set expression for a
  matrix or for a vector whose length the discretisation fixes. Calibration
  refuses a matrix for such a parameter, so the chain is described in a
  comment in `declaration/calibration/housing-renting.yml` instead. The brief on parameter families
  indexed by a finite set records the question.
- **The support of the income chain.** `y_pre` is declared on the positive
  reals, which contain the chain's levels; that the arrival income is one of
  those levels is an assumption of the model and is not written.
- **The one-sided conditions at a tax threshold.** The continuation value is
  not differentiable where the tax jumps or kinks, so the Euler equality of
  (37) does not hold there; (38) states one-sided inequalities instead. The
  policy blocks write the interior condition and the segment at the borrowing
  limit; the candidate segments at the thresholds, Box 3 step 3, are settings
  of the endogenous grid entry in the methods files.
- **The upper envelope.** Comparing the candidates the endogenous grid
  produces is part of realising the maximisation the policy blocks declare,
  not a separate authored operation, so FUES is named in the settings and not
  in a stage file.
- **The tie in the tenure choice.** Where owning and renting are worth the
  same, both are maximisers; the selection rule is the method's. The solver
  chooses renting.

## Elaboration

Elaborating each stage on its own, with `elaborate_stage`, gives:

```text
applications/housing-renting/declaration/stages/tenure_choice/tenure_choice.bl: REFUSED NotConstructed: not-constructed applications/housing-renting/declaration/stages/tenure_choice/tenure_choice.bl:32:5: make_stage cannot construct this nested block: task B02 (branching construction) adds its construction rule (term address 'dcsn_to_cntn.own'; rule not-constructed)
applications/housing-renting/declaration/stages/owner_housing/owner_housing.bl: REFUSED NotConstructed: not-constructed applications/housing-renting/declaration/stages/owner_housing/owner_housing.bl:3:1: no construction rule for the definition 'XH': its right side linspace(H_min, H_max, n_H) is not a function of the stage, and a set defined by a grid constructor is not yet constructed (term address '2'; rule not-constructed)
applications/housing-renting/declaration/stages/owner_cons/owner_cons.bl: ElaboratedStage('owner_cons', symbolic)
  view ('field', None): constructed
  view ('operator', 'backward'): constructed
  view ('operator', 'forward'): constructed
applications/housing-renting/declaration/stages/renter_housing/renter_housing.bl: REFUSED NotConstructed: not-constructed applications/housing-renting/declaration/stages/renter_housing/renter_housing.bl:3:1: no construction rule for the definition 'XS': its right side linspace(S_min, S_max, n_S) is not a function of the stage, and a set defined by a grid constructor is not yet constructed (term address '2'; rule not-constructed)
applications/housing-renting/declaration/stages/renter_cons/renter_cons.bl: ElaboratedStage('renter_cons', symbolic)
  view ('field', None): constructed
  view ('operator', 'backward'): constructed
  view ('operator', 'forward'): constructed
```

Both refusals are constructions the language does not have yet: the branches
of a discrete choice, which task B02 adds, and a set defined by a grid
constructor, which decision D21 rules to be a primitive of the language and
whose admission is pending. Nothing else in the five files is refused: with
the tenure branches written as one product output and the two discrete sets
written as `ℝ₊`, each stage constructs its field view and its backward and
forward operator views.

`period_factory.make` and `trellis_factory.make` raised `KeyError: 'yaml_text'`
on `.bl` records, so the trellis was assembled as a dictionary from
`declaration/period.yml`, `declaration/trellis.yml`, the five methods files, `declaration/settings/housing-renting.yml` and
`declaration/calibration/housing-renting.yml`, twenty periods with nineteen copies of the inter-period
connector, and passed on 14 September 2026 to `bellman.elaborate`, which AMD-FAC-002
removed for `elaborate_trellis` and the three trellis verbs. It refuses at
the tenure branch, in every one of the twenty occurrences. With the two
refused constructions replaced as above, the whole trellis elaborates to
`symbolic`, its every methods entry resolves under `strict=True` and its
settings bind; `specified` then stops at the income chain, whose `Π` has no
value.

## Relation to the owner-only housing example

`applications/housing-owner/` writes the same housing model without the
renting alternative and without the tax: two stages, a housing choice and a
consumption choice, for a household that owns throughout. Read beside this
folder, the two differ in five ways.

1. **Tenure.** There is no tenure stage and no branch there, so that example
   needs no branch construction, while here the tenure stage is refused until
   task B02 lands. Its housing stage draws income; here income is drawn in
   the tenure stage, one stage earlier.
2. **Income.** That example keeps the income state as an index and reads the
   level from a declared family, `z_vals[y]`, which the family-selection rule
   refuses because the number of states comes from a discretisation. Here the
   field `y` is the income level itself, as the paper writes it, the chain's
   levels are an argument of the law rather than a family indexed by a state,
   and no selection is written. The two laws also differ in their arguments:
   that example's law names no state, and a law that names none is constant
   in the information at the source perch, which is an independent draw;
   the law here names `y_pre`, which is what makes the draw a Markov chain.
3. **Preferences.** That example uses the Cobb-Douglas aggregate inside a
   constant-relative-risk-aversion utility, with a separate risk aversion
   `γ`; here utility is the logarithmic form of equation (30), which is the
   configuration behind the paper's tables.
4. **Returns.** That example has a gross return `R` and no tax, so its
   marginal value carries no tax term; here the return is `1 + r` less the
   marginal tax rate, and the derivative of the tax appears in the two stages
   whose law of motion turns assets into cash.
5. **Policy blocks.** Its consumption policy block lists decision-perch and
   continuation-perch fields together, a question its own page records; the
   consumption policy blocks here read continuation objects only.

Both examples stop at the same grid constructor, and the pages of both record
it.

## Source check

The paper and the code of the replication disagree in three places. In each
of them the configuration that produced the published tables follows the
code, so the files here follow the code and say so.

1. **The services scale.** Equation (30) gives a renter utility from `S`
   itself. The code multiplies rented services by a parameter it sets to 0.5
   before they enter utility, in both the endogenous grid and the value
   function iteration routines, and the notes to Appendix Table 7 list
   `ϑ = 0.5`. `renter_cons.bl` therefore carries `ϑ`, the calibration sets it
   to 0.5, and `ϑ = 1` gives the utility function as printed.
2. **The terminal value.** Equation (31) writes a bequest function of
   liquidated wealth and leaves that function unspecified for this
   application; §2.3.4 says that agents consume all their wealth at the end
   of life. The code supplies the utility of consuming the savings while
   holding the house, which is the function recorded in `trellis.yml`.
3. **The zero housing size.** The paper writes the set of housing sizes as a
   subset of the strictly positive reals; the configuration's set begins at
   zero. Owning a zero house and renting zero services leave the same cash,
   the same utility and the same continuation state, so the two sets give the
   same value functions and differ only in the tenure label at those states.
   The calibration follows the configuration.

Two further differences are notation and timing rather than disagreements.
The paper writes the transaction cost as `τ`, the letter it also uses for the
marginal tax rates; the code and Fella write `φ`, which the stage files use.
And the paper places the expectation over income in the consumption stages,
while the code, the legacy stage files and this translation place it on the
arrival edge of the next tenure stage.
