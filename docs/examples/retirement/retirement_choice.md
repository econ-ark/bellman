---
audience: user
type: example
topic: [applications]
---
# Retirement choice

> [!summary]
> A worker chooses at the start of each period whether to work or to retire, and then how much to consume; retirement is permanent. The model of Iskhakov, Jørgensen, Rust and Schjerning (2017) is written as three stage files: the choice between working and retiring, the consumption of a worker and the consumption of a retiree. The derivatives of the values, the steps of the endogenous grid method and the numerical methods stand in a methods file beside each stage file, an addition to the stage file that the package reads with it. A period file joins the three stages, and a trellis file joins the periods. Every file on this page is quoted from the application folder `applications/retirement-choice/`, and every result is printed from the package.

> [!info]- Relationship with other documents
> **Builds on** — [Branching](../../Bellman-Sym/05-branching.md): the rules of the choice stage, whose file this page quotes again.
> **See also** — [Periods](../../Bellman-Sym/06-period.md), [Trellis syntax](../../Bellman-Sym/07-trellis.md) and [Methodization](../../Bellman-Sym/04-methodization.md): the connectors within a period and between periods, and how a methods file attaches a numerical method.

## 1 The model

An agent lives from date 0 to date $T$. She holds assets $a \ge 0$, which earn the gross return $R$, consumes $c > 0$ with utility $\log c$, and discounts the future by $\beta$. In a period of work she earns the wage $y$ and bears the utility cost $\delta$ of working. She may retire, and retirement is permanent: a retiree never returns to work. There is no income risk and no taste shock, so every quantity is deterministic given the state.

Iskhakov, Jørgensen, Rust and Schjerning (2017) solve this model with the endogenous grid method for discrete-continuous choice, which computes consumption by inverting the Euler equation on a grid of savings, and Dobrescu and Shanker make it the first application of their fast upper envelope scan (FUES), whose code's retirement example supplies the calibration and settings of §7. The option to retire later makes the worker's continuation value non-concave: it is the upper envelope of concave values, one for each future sequence of work and retirement. The Euler equation then has several solutions at some levels of wealth, and a method that inverts it must select among the candidate solutions by their value.

In the stage files the choice made at the start of a period governs that period: the wage enters that period's cash on hand, and the cost $\delta$ is charged in that period's choice. In the two papers the choice made at a date governs the next date's wage. The two recursions describe the same model when the papers' cost of work equals $\beta\delta$; the application's `economics.md` sets out the comparison.

## 2 Bellman equation

Write $\mathcal W_t(a)$ for the value of a worker who begins date $t$ with assets $a$, before she chooses whether to work; $Q_t(a)$ for the value of working at date $t$ before the cost of work is charged; and $\mathcal U_t(a)$ for the value of a retiree who begins date $t$ with assets $a$. The stage files state

$$
\mathcal W_t(a) = \max\bigl\{ Q_t(a) - \delta,\; \mathcal U_t(a) \bigr\},
$$

$$
Q_t(a) = \max_{0 < c \le Ra + y} \bigl\{ \log c + \beta\, \mathcal W_{t+1}(Ra + y - c) \bigr\},
\qquad
\mathcal U_t(a) = \max_{0 < c \le Ra} \bigl\{ \log c + \beta\, \mathcal U_{t+1}(Ra - c) \bigr\}.
$$

A worker's savings $Ra + y - c$ are the assets with which she begins the next date, when she chooses again; a retiree's savings $Ra - c$ are the assets with which she begins the next date as a retiree. After the last date $T$, $\mathcal W_{T+1}$ and $\mathcal U_{T+1}$ are the terminal value, which §5 describes.

## 3 The stages of one period

A **stage** is one step of the recursion, written as one file with three perches, the information sets at arrival, at the decision and at continuation ([Stage tutorial](../../Bellman-Sym/01-stage.md)). One period of this model has three stages, and none of them has a shock:

| Stage | Arrival | Decision | Continuation |
|---|---|---|---|
| `ret_choice` | assets `a` | `a_d = a`; the control `d` chooses a label in `{work, retire}` | `a_w = a_d` on the work branch, `a_r = a_d` on the retire branch |
| `worker_cons` | assets `a_w` | cash on hand `w = R*a_w + y`; consumption `c` is chosen | savings `b = w - c` |
| `retiree_cons` | assets `a_ret` | cash on hand `w_ret = R*a_ret`; consumption `c` is chosen | savings `b_ret = w_ret - c` |

### 3.1 The choice between work and retirement

The choice stage is `applications/retirement-choice/declaration/stages/ret_choice/ret_choice.bl`:

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

Its methods file, `applications/retirement-choice/declaration/stages/ret_choice/methods.bl`, is an **addition** to the stage file: a `.bl` file that opens with `@methods:` and that the package reads with the stage file, whose blocks name blocks of the stage by their ids and add their entries and their lines to them, and whose file-level entries type a place by its path (§6). It types the policy builder with the method `!max` and its handler, and appends the derivative line to the decision value block:

```bl
@methods: ret_choice
# The methods of the choice between work and retirement, written as an
# addition to ret_choice.bl beside this file: the discrete maximum on the
# policy builder with the handler of the FUES retirement example that
# compares the two branch values, and the derivative of the choice value in
# assets, the derivative of the branch value the choice d selects, as an
# authored line of the decision value builder. The policy builder gains no
# line, and a block of a methods file may not have an empty body, so its
# method and its handler are file-level lines routed by their paths to the
# block policy. The branching block dcsn_to_cntn, whose two nested blocks are
# labeled work and retire, takes nothing: the union keeps it as the stage file
# writes it.

policy.method : !max
policy.handler : "fues-retirement:dcsn_mover"

[id=cntn_to_dcsn] {
    D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]  :: [id=marginal]
}
```

The forward block `dcsn_to_cntn` holds one nested block for each label of the control `d`, and each writes its own branch's field: `a_w` on the work branch and `a_r` on the retire branch. A **branch** is one alternative of the choice, with its own continuation ([branch](../../wiki/branch.md)). The value statement `V = …` selects, by the tuple indexed by `d`, the worker's value less the cost of work or the retiree's value; the derivative line `D_{a_d}V = …` of the methods file selects the derivative in assets of the chosen branch's value, in the same order; and the policy statement `d = argmax_{d}(…)` chooses a label whose entry of the same tuple is largest. [Branching](../../Bellman-Sym/05-branching.md) reads this file line by line. The package's queries `kind`, `branches` and `combination` answer, for this stage:

```text
kind(stage)          branching
branches(stage)      work: a_w
                     retire: a_r
combination(stage)   choice
```

The stage is branching, its branch `work` writes `a_w` and its branch `retire` writes `a_r`, and the branches combine by the choice of a label.

### 3.2 The worker's consumption

The worker's stage is `applications/retirement-choice/declaration/stages/worker_cons/worker_cons.bl`:

```bl
@stage: worker_cons

Xa := ℝ₊

β : (0,1)        :: ["discount factor"]
R : ℝ₊₊          :: ["gross return on assets"]
y : ℝ₊₊          :: ["wage paid in a period of work"]

𝑢(c : ℝ₊₊) := log(c)                :: [id=util]
𝑑𝑢(c : ℝ₊₊) := 1/c                  :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := 1/x               :: [id=inv_marg_util]
Γ(x : ℝ₊₊) := (0, x]                :: [id=feasible]

[id=arvl_to_dcsn, (a_w : Xa) : !arvl -> (w : ℝ₊₊) : !dcsn] {
    w = R*a_w + y                   :: [id=cash_on_hand]
}

[id=dcsn_to_cntn, (w, c : ℝ₊₊ @ !ctrl) : !dcsn -> (b : Xa) : !cntn] {
    b = w - c                       :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}

[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(w)}(𝑢(c) + β*V[>])        :: [id=optimality]
}
```

Its methods file, `applications/retirement-choice/declaration/stages/worker_cons/methods.bl`, types the policy builder with the endogenous grid method, its grid of savings and its handler, writes the steps of the method in its block `policy`, types the operator `upper_env` of the last of them with the fast upper envelope scan, appends the derivative lines of the two values to the two value blocks, and represents the arrival value on the asset grid (§6):

```bl
@methods: worker_cons
# The methods of the worker's consumption stage, written as an addition to
# worker_cons.bl beside this file: the endogenous grid method on the policy
# builder with its grid of savings and its handler, and the four lines of the
# method, the inverted Euler relation, the endogenous grid of cash on hand,
# the candidate value and the upper envelope that gives c from the
# candidates; the fast upper envelope scan, FUES, on the operator upper_env
# of the last of them, with its threshold m_bar; the envelope line of the
# decision value and the derivative line of the arrival value; and one linear
# representation of the arrival value and of its stated derivative on the
# asset grid. The four settings the file reads are declared at the top with
# their sets. Each grid is its own typing entry at its place, one factor
# keyed by its coordinate: the savings b, the continuation state on which
# !egm builds its grid and which the policy builder's signature does not
# list, and the assets a_w at the arrival builder's Evaluation, both on the
# bounds and the count of the settings file's asset grid.
#
# With the solution method !egm on the policy builder, the four lines stand
# in place of the declared maximization at the operative level, and the
# declared level keeps the stage file's line, so the line envelope, which
# defines c, meets no second definition, and the entry on upper_env names the
# operator of that line.

n_a : ℕ              :: ["number of points of the asset grid"]
a_min : Xa           :: ["lower bound of the asset grid"]
a_max : Xa           :: ["upper bound of the asset grid"]
m_bar : ℝ₊₊          :: ["jump-detection threshold of the upper envelope scan"]

[id=policy, method : !egm | grid : !Cartesian(b=(a_min, a_max, n_a)) | handler : "asva:make_egm_1d"
    | upper_env.method : !FUES(m_bar=m_bar) | upper_env.handler : "dcsmm:EGM_UE"] {
    c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])                 :: [id=InvEuler]
    w[>] = b + c[>]                            :: [id=endoggrid]
    v[>] = 𝑢(c[>]) + β*V[>]                    :: [id=cand_value]
    c    = upper_env(w[>], c[>], v[>])          :: [id=envelope]
}

[id=cntn_to_dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | evaluate.method : !Linear | evaluate.grid : !Cartesian(a_w=(a_min, a_max, n_a)) | evaluate.handler : "dcsmm:interp_as_2"] {
    D_{a_w}V[<] = R*D_{w}V          :: [id=marginal]
}
```

Cash on hand is `w = R*a_w + y`, and consumption lies in `Γ(w) = (0, w]`. The value statement adds the discounted continuation value to the utility of consumption, and the policy block states the maximization, which also declares the feasible set of consumption. The derivative line `D_{w}V = 𝑑𝑢(c)` appended to `cntn_to_dcsn` states the derivative of the value in cash on hand, `1/c`, and the line appended to `dcsn_to_arvl` multiplies it by `R`, the factor of the law `w = R*a_w + y`, to state the derivative of the arrival value in assets. The block `policy` of the methods file writes the steps of the endogenous grid method as equations, which stand in place of the maximization at the operative level while the declared level keeps the maximization. The inverse Euler inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])`, which reads the derivative of the continuation value in savings, gives the candidate consumption at each level of savings. It carries no complementary-slackness clause `⟂ b >= 0`, which would pair the Euler equation with the borrowing limit, so it is read as the equation `c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])`: at every level of savings the candidate is the interior value, at which the Euler equation holds with equality ([Constraints](../../Bellman-Sym/10-constraints.md#43-the-clause-on-the-candidate-line) §4.3). The endogenous grid is `w[>] = b + c[>]`, the value of each candidate is `v[>]`, and the upper envelope `upper_env(w[>], c[>], v[>])` keeps, at each level of cash on hand, the candidate of largest value. The worker needs the upper envelope because her continuation value is not concave.

### 3.3 The retiree's consumption

The retiree's stage is `applications/retirement-choice/declaration/stages/retiree_cons/retiree_cons.bl`:

```bl
@stage: retiree_cons

Xa := ℝ₊

β : (0,1)        :: ["discount factor"]
R : ℝ₊₊          :: ["gross return on assets"]

𝑢(c : ℝ₊₊) := log(c)                :: [id=util]
𝑑𝑢(c : ℝ₊₊) := 1/c                  :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := 1/x               :: [id=inv_marg_util]
Γ(x : ℝ₊) := (0, x]                 :: [id=feasible, "empty at zero resources"]

[id=arvl_to_dcsn, (a_ret : Xa) : !arvl -> (w_ret : Xa) : !dcsn] {
    w_ret = R*a_ret                 :: [id=cash_on_hand]
}

[id=dcsn_to_cntn, (w_ret, c : ℝ₊₊ @ !ctrl) : !dcsn -> (b_ret : Xa) : !cntn] {
    b_ret = w_ret - c               :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu, c) : !cntn -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = V                        :: [id=value]
}

[id=policy, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{c : Γ(w_ret)}(𝑢(c) + β*V[>])     :: [id=optimality]
}
```

Its methods file, `applications/retirement-choice/declaration/stages/retiree_cons/methods.bl`, types the policy builder as the worker's does, writes the steps of the method in its block `policy`, appends the derivative lines of the two values, and represents the arrival value and its stated derivative on the asset grid, one entry for each stored object (§6):

```bl
@methods: retiree_cons
# The methods of the retiree's consumption stage, written as an addition to
# retiree_cons.bl beside this file: the endogenous grid method on the policy
# builder with its grid of savings and its handler, and the three lines of
# the method, the inverted Euler relation with its note, the endogenous grid
# of cash on hand and the identification of c with the candidate; the
# envelope line of the decision value and the derivative line of the arrival
# value; and the linear representation of the arrival value and of its stated
# derivative on the asset grid, each named at its own Evaluation. The three
# settings the file reads are declared at the top with their sets. Each grid
# is its own typing entry at its place, one factor keyed by its coordinate:
# the savings b_ret, the continuation state on which !egm builds its grid,
# and the assets a_ret at each of the two Evaluations of the arrival builder.
#
# With the solution method !egm on the policy builder, the three lines stand
# in place of the declared maximization at the operative level, and the
# declared level keeps the stage file's line.

n_a_ret : ℕ          :: ["number of points of the retiree's asset grid"]
a_ret_min : Xa       :: ["lower bound of the retiree's asset grid"]
a_ret_max : Xa       :: ["upper bound of the retiree's asset grid"]

[id=policy, policy.method : !egm | policy.grid : !Cartesian(b_ret=(a_ret_min, a_ret_max, n_a_ret)) | policy.handler : "asva:make_egm_1d"] {
    c[>]     <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b_ret}V[>])                :: [id=InvEuler, "Implies a correspondence: where equality holds, c[>] takes on a single value, where inequality holds, it is multiple values"]
    w_ret[>] = b_ret + c[>]                          :: [id=endoggrid]
    c        = c[>]                                  :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{w_ret}V = 𝑑𝑢(c)              :: [id=marginal]
}

[id=dcsn_to_arvl
    | evaluate[V[<]].method : !Linear | evaluate[V[<]].grid : !Cartesian(a_ret=(a_ret_min, a_ret_max, n_a_ret)) | evaluate[V[<]].handler : "dcsmm:interp_as_3"
    | evaluate[D_{a_ret}V[<]].method : !Linear | evaluate[D_{a_ret}V[<]].grid : !Cartesian(a_ret=(a_ret_min, a_ret_max, n_a_ret)) | evaluate[D_{a_ret}V[<]].handler : "dcsmm:interp_as_3"] {
    D_{a_ret}V[<] = R*D_{w_ret}V    :: [id=marginal]
}
```

Cash on hand is `w_ret = R*a_ret`, with no wage. The block `policy` of the methods file writes the inverse Euler inequality and the endogenous grid as the worker's does, and then the **identification** `c = c[>]`, which equates the policy at the cash on hand of each level of savings with the candidate there. The package forms from the policy block the **policy builder**, the operator whose output is the policy. With the solution method on the builder, the builder's operations are the lines of that block, and `stage.dcsn.builder.policy.denote()` prints its card, a statement of its operations, with the maximization of the stage file under `Declared`. The card gives the identification as the operation `cons_choice:Pullback`, the policy composed with the cash on hand at each level of savings, with the rule `𝑐(𝑤_ret≻(b_ret)) = 𝑐≻(b_ret)` on `𝑤_ret≻(Xa)`, the set of cash on hand that the candidates reach. The inverse Euler inequality carries no clause, so the policy is stated on that set and not below it, where the borrowing limit binds ([Constraints](../../Bellman-Sym/10-constraints.md#43-the-clause-on-the-candidate-line) §4.3). The retiree's continuation value is concave, so the block needs no upper envelope. At zero assets the feasible set `(0, w_ret]` is empty, as the description of `Γ` in the file records.

## 4 The period

A **period** is the stages of one date, joined by connectors ([Periods](../../Bellman-Sym/06-period.md)). The period file is `applications/retirement-choice/declaration/period.yml`:

```yaml
!period
name: retirement_period

# One period of the retirement model: the choice between work and retirement,
# then consumption on the branch that choice selects. The order of the stages
# is derived from their fields, not from this list. The work branch joins the
# worker's arrival assets by name (a_w); the retire branch connects to the
# retiree's arrival assets. The terminal period, which adds the bequest, is
# written out in trellis.yml, since its connector names the bequest's arrival
# field and a connector to a stage absent from a period is refused.
stages:
  - ret_choice
  - worker_cons
  - retiree_cons
connectors:
  - {a_r: a_ret}
```

A **connector** connects a continuation field of one stage to an arrival field of another ([Periods](../../Bellman-Sym/06-period.md#2-connectors) §2). The work branch's `a_w` has one compatible reading occurrence, the worker's arrival field, so the package infers that connection. The connector `{a_r: a_ret}` selects the retire branch's continuation and the retiree's arrival assets without changing either local name. These two endpoints are unique, so no stage prefix is needed. The package derives the order of the stages from the selected connections; the order of the list in the file carries no meaning:

```text
period_joins(period)["joins"]
  ret_choice:a_r → retiree_cons:a_ret
  ret_choice:a_w → worker_cons:a_w
period_joins(period)["outputs"]
  retiree_cons:b_ret
  worker_cons:b
computable_together(period)
  1  ret_choice
  2  retiree_cons, worker_cons
```

`computable_together` lists the stages in layers, each layer computable once the layers before it are: in forward time the choice stage comes first and the two consumption stages follow it, and value is computed backward, from the two consumption stages to the choice. The savings `b` and `b_ret` are the fields that leave the period. In the figure, workers begin the period at `a`, the choice stage's arrival assets, and retirees of the date before begin it at `a_ret`, the retiree stage's arrival assets, which also receive the workers who retire.

<div markdown="0">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 280" style="max-width:680px;width:100%;">
  <defs>
    <style>
      .dag-edge   { fill: none; stroke: currentColor; stroke-width: 1.2px; stroke-linecap: round; }
      .dag-arrow  { fill: currentColor; }
      .dag-perch  { fill: var(--md-default-bg-color, white); stroke: currentColor; stroke-width: 1.2px; }
      .dag-stg    { fill: currentColor; stroke: none; }
      .dag-bound  { fill: none; stroke: currentColor; stroke-width: 0.8px; stroke-dasharray: 4 3; opacity: 0.25; }
      .dag-field  { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 15px; fill: currentColor; }
      .dag-sub    { font-size: 10.5px; }
      .dag-ptag   { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 9.5px; fill: currentColor; opacity: 0.40; }
      .dag-slabel { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 11px; fill: currentColor; }
      .dag-branch { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 10px; fill: currentColor; font-style: italic; }
      .dag-period { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 9.5px; fill: currentColor; opacity: 0.30; font-style: italic; }
      .dag-legend { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 8px; fill: currentColor; opacity: 0.45; }
    </style>
    <marker id="dag-ah" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L8,3 L0,6 L1.5,3 Z" class="dag-arrow"/>
    </marker>
  </defs>
  <rect class="dag-bound" x="14" y="14" width="652" height="252" rx="8"/>
  <text class="dag-period" x="26" y="30">retirement_period</text>
  <circle class="dag-stg" cx="548" cy="27" r="3.5"/>
  <text class="dag-legend" x="555" y="30">stage</text>
  <circle class="dag-perch" cx="600" cy="27" r="3.5"/>
  <text class="dag-legend" x="607" y="30">perch field</text>
  <circle class="dag-perch" cx="68" cy="105" r="6"/>
  <text class="dag-field" x="68" y="88" text-anchor="middle">a</text>
  <text class="dag-ptag" x="68" y="124" text-anchor="middle">&#x227A;</text>
  <circle class="dag-perch" cx="68" cy="210" r="6"/>
  <text class="dag-field" x="68" y="198" text-anchor="middle">a<tspan class="dag-sub" dy="3">ret</tspan></text>
  <text class="dag-ptag" x="68" y="230" text-anchor="middle">&#x227A;</text>
  <circle class="dag-stg" cx="220" cy="105" r="7"/>
  <text class="dag-slabel" x="220" y="82" text-anchor="middle">ret_choice</text>
  <circle class="dag-stg" cx="415" cy="65" r="7"/>
  <text class="dag-slabel" x="415" y="48" text-anchor="middle">worker_cons</text>
  <circle class="dag-stg" cx="415" cy="192" r="7"/>
  <text class="dag-slabel" x="415" y="222" text-anchor="middle">retiree_cons</text>
  <circle class="dag-perch" cx="575" cy="65" r="6"/>
  <text class="dag-field" x="575" y="48" text-anchor="middle">b</text>
  <text class="dag-ptag" x="575" y="84" text-anchor="middle">&#x227B;</text>
  <circle class="dag-perch" cx="575" cy="192" r="6"/>
  <text class="dag-field" x="575" y="180" text-anchor="middle">b<tspan class="dag-sub" dy="3">ret</tspan></text>
  <text class="dag-ptag" x="575" y="212" text-anchor="middle">&#x227B;</text>
  <line class="dag-edge" x1="75" y1="105" x2="212" y2="105" marker-end="url(#dag-ah)"/>
  <path class="dag-edge" d="M228,102 C265,82 360,65 407,65" marker-end="url(#dag-ah)"/>
  <text class="dag-branch" x="310" y="72">work</text>
  <path class="dag-edge" d="M228,109 C268,140 355,182 407,192" marker-end="url(#dag-ah)"/>
  <text class="dag-branch" x="298" y="165">retire</text>
  <path class="dag-edge" d="M75,210 C185,210 335,198 407,193" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="423" y1="65" x2="568" y2="65" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="423" y1="192" x2="568" y2="192" marker-end="url(#dag-ah)"/>
</svg>
</div>

## 5 The trellis

A trellis is a diagram of periods joined by connections. Repeated uses of a period retain the same declarations and calibration sources in a [modular model](../../bellman-calculus/APPX-H-MODULARITY.md). The user supplies terminal data for every backward field when realizing the model; this application declares no age field.

The Python representation lists the periods backward from the last date: `periods[0]` is the terminal period, and `periods[h+1]` is the period one date before `periods[h]` ([Trellis syntax](../../Bellman-Sym/07-trellis.md)). The trellis file is `applications/retirement-choice/declaration/trellis.yml`:

```yaml
!trellis
name: retirement_lifecycle
# periods[h] is the date T - h: periods[0] is the terminal period. The model
# has twenty dates, the horizon of the FUES retirement example whose
# calibration and settings this registry holds (economics.md, "Calibration and
# settings"); the working paper's tables use fifty, which is `repeat: 49`.
# The terminal period is written out, since its connector names the bequest,
# which no other period holds: it adds the bequest, the terminal value as a
# stage, and the connector from both consumption stages to its
# arrival field a_bq, a name of its own, since the savings left after the last
# date begin no further date. The nineteen earlier periods repeat the template.
periods:
  - stages: [ret_choice, worker_cons, retiree_cons, bequest]
    connectors:
      - {a_r: a_ret}
      - {b: a_bq, b_ret: a_bq}
  - {template: period.yml, repeat: 19}
# One mapping stands for every adjacent pair and holds both routes
# (docs/Bellman-Sym/07-trellis.md §2): the worker's savings go to the next
# period's choice stage, the retiree's to the next period's retiree stage, so
# no route returns a retiree to work. In periods[0] the name a is ret_choice's
# alone and a_ret retiree_cons's alone, so the mapping reaches the bequest
# nowhere.
inter_connectors:
  - {b: a, b_ret: a_ret}
```

The file writes the terminal period out, with the bequest stage, and repeats the period of §4 for the 19 dates before it, so that the package reads a trellis of 20 periods. Its one inter-period mapping stands for every pair of adjacent periods.

The mapping `{b: a, b_ret: a_ret}` joins each period to the one before it in the list, which is the next date: a worker's savings become the assets with which she begins the next date at the choice stage, and a retiree's savings the assets with which she begins it at the retiree stage. Between two adjacent periods the package makes these joins:

```text
inter_period_joins(mapping, periods[h + 1], periods[h])
  worker_cons:b → ret_choice:a
  retiree_cons:b_ret → retiree_cons:a_ret
```

Nothing sends a retiree to the choice stage, which is what makes retirement permanent; the stage files themselves do not say so. The retiree's arrival assets `a_ret` have two sources: within the period, the workers who retire at that date, through the connector `{a_r: a_ret}`; across the pair, the retirees of the date before. The distribution of assets at `a_ret` is the sum of the two incoming distributions ([Trellis syntax](../../Bellman-Sym/07-trellis.md#2-inter-period-connectors) §2).

The terminal period adds the bequest stage, `applications/retirement-choice/declaration/stages/bequest/bequest.bl`, the terminal value written as a stage:

```bl
@stage: bequest

# The terminal value of the retirement model, written as a stage. The papers
# consume all resources at the last date, so the savings left after the
# terminal period have no value (economics.md, "The terminal continuation
# value"). V[>] is the terminal boundary data, zero, supplied at
# realization. The arrival field is a_bq and not a
# or a_ret, the names at which ret_choice and retiree_cons of the terminal
# period arrive: the savings left after the last date begin no further date.

[id=arvl_to_dcsn, (a_bq : ℝ₊) : !arvl -> (x : ℝ₊) : !dcsn] {
    x = a_bq                                           :: [id=wealth]
}

[id=cntn_to_dcsn, (V[>] : [-inf, inf) @ !vlu) -> (V : [-inf, inf) @ !vlu) : !dcsn] {
    V = V[>]                                           :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : [-inf, inf) @ !vlu) : !arvl] {
    V[<] = V                                           :: [id=value]
}
```

Its methods file, `applications/retirement-choice/declaration/stages/bequest/methods.bl`, appends the derivative line to its decision value block and types no method (§6):

```bl
@methods: bequest
# The methods of the terminal stage, written as an addition to bequest.bl
# beside this file: the derivative of the terminal value in wealth, zero, as
# an authored line of the decision value builder. The block names the stage's
# block by its id and adds no coordinate, so it carries no signature. The
# stage takes no method: its values are closed forms.

[id=cntn_to_dcsn] {
    D_{x}V = 0                                         :: [id=marginal_wealth]
}
```

Its arrival field `a_bq` receives the savings of both consumption stages of the terminal period, through the connector `{b: a_bq, b_ret: a_bq}`. Its value is the continuation value `V[>]`, boundary data equal to zero, since the papers' agent consumes all her resources at the last date, and the derivative line `D_{x}V = 0` of its methods file states that the derivative of its value in wealth is zero. The state-field connections are:

```text
period_joins(periods[0])["joins"]
  ret_choice:a_r → retiree_cons:a_ret
  ret_choice:a_w → worker_cons:a_w
  retiree_cons:b_ret → bequest:a_bq
  worker_cons:b → bequest:a_bq
```

The join check compares value fields alone. The terminal stage states the
derivative of its value in wealth, zero, by the line its methods file appends, and the law
of its arrival block, `x = a_bq`, is the identity, so the stated derivative
passes through to the arrival value, which both consumption stages of the
terminal period read by the terms `D_{b}V[>]` and `D_{b_ret}V[>]`. The
inverse marginal utility `𝑑𝑢𝑖𝑛𝑣` of both consumption stages is declared on
`ℝ₊₊`, which excludes zero, so in the terminal period the inverse Euler line
reads the terminal derivative outside the declared domain of `𝑑𝑢𝑖𝑛𝑣`. Changing
the terminal treatment or the consumption declarations requires an economic
decision, not a different connector spelling. The nonterminal connections
preserve the route that keeps a retiree retired.

## 6 Methods

A methods file is an addition to a stage file: a `.bl` file that opens with `@methods:` and the stage's name, which the package reads with the stage file ([Methodization](../../Bellman-Sym/04-methodization.md)). A block of the methods file names a block of the stage by its id and adds to it. A typing entry in its bracket types a component of the builder's signature: `method : !egm` the method, `grid : !Cartesian(b=(a_min, a_max, n_a))` the grid, one factor for each coordinate it discretizes, keyed by the coordinate's name, with the lower bound, the upper bound and the count as declared settings, and `handler : "asva:make_egm_1d"` the handler, the routine outside the language that executes the method, written as a quoted string. An entry whose path names an operator of the block, `upper_env.method : !FUES(m_bar=m_bar)`, types that operator, and a keyword argument of a method word names a setting by its name. The block's lines are appended to the stage block's lines; where the block's method is a solution method, as `!egm` is, its lines stand in place of the stage block's maximization at the operative level, and the declared level keeps the maximization. A file-level entry with a full path, `policy.method : !max`, types the place the path names, and an Evaluation that stores a value and its stated derivative takes one entry for both, `evaluate.method`, or one for each stored object, `evaluate[V[<]].method` and `evaluate[D_{a_ret}V[<]].method`, as the worker's and the retiree's files write them. Every setting a grid or a method reads is declared at the top of the file with its set, `n_a : ℕ`, and valued by the settings file of §7. The four methods files are quoted in §3 and §5.

The recipe names each stage's methods file in the stage's methods list, and `elaborate_trellis` reads it with the stage file at every occurrence of the stage, so that the trellis holds the methods without a binding step: `methodize_trellis` changes nothing. After `calibrate_trellis` and `configure_trellis` the occurrences print as

```text
ret_choice      ElaboratedStage('ret_choice', specified)
worker_cons     ElaboratedStage('worker_cons', specified)
retiree_cons    ElaboratedStage('retiree_cons', specified)
bequest         ElaboratedStage('bequest', calibration, settings)
```

The bequest's methods file types no method, so its occurrence carries no method component and its word is not `specified`. The worker's stage prints its methods, `str(stage.methods)`, as

```text
dcsn_to_arvl.evaluate   !Linear   !Cartesian(a_w=(a_min, a_max, n_a))   "dcsmm:interp_as_2"
policy                  !egm   !Cartesian(b=(a_min, a_max, n_a))   "asva:make_egm_1d"
policy.upper_env        !FUES(m_bar=m_bar)   "dcsmm:EGM_UE"
```

one row for each place that carries a component: the Evaluation of the arrival value builder, which represents the arrival value and its stated derivative alike by linear interpolation on the asset grid; the policy builder, solved by the endogenous grid method on the grid of savings `b`; and the operator `upper_env` of its line `envelope`, the fast upper envelope scan with its threshold `m_bar`. The retiree's file names the two stored objects of its arrival Evaluation separately, which say the same here, and its methods print as

```text
dcsn_to_arvl.evaluate[V[<]]            !Linear   !Cartesian(a_ret=(a_ret_min, a_ret_max, n_a_ret))   "dcsmm:interp_as_3"
dcsn_to_arvl.evaluate[D_{a_ret}V[<]]   !Linear   !Cartesian(a_ret=(a_ret_min, a_ret_max, n_a_ret))   "dcsmm:interp_as_3"
policy                                 !egm   !Cartesian(b_ret=(a_ret_min, a_ret_max, n_a_ret))   "asva:make_egm_1d"
```

The settings a stage reads print beside the places that read them, `str(stage.settings)` of the worker's stage:

```text
name       set  value  read at                by       grid
n_a        ℕ    3000   dcsn_to_arvl.evaluate  !Linear  !Cartesian
n_a        ℕ    3000   policy                 !egm     !Cartesian
a_min      Xa   1e-10  dcsn_to_arvl.evaluate  !Linear  !Cartesian
a_min      Xa   1e-10  policy                 !egm     !Cartesian
a_max      Xa   500    dcsn_to_arvl.evaluate  !Linear  !Cartesian
a_max      Xa   500    policy                 !egm     !Cartesian
m_bar      ℝ₊₊  1.01   policy.upper_env       !FUES
n_a_ret         3000
a_ret_min       1e-10
a_ret_max       500
```

The three settings of the retiree's grid stand in the same settings file and are read at no place of the worker's stage, so they print with no place.

## 7 Calibration and settings

The calibration is `applications/retirement-choice/declaration/calibration/retirement.yml`:

```yaml
# The benchmark calibration of the FUES retirement example, which reports the
# interest rate r = 0.02, so that the gross return is R = 1 + r.
calibration:
  β: 0.96
  R: 1.02
  y: 20
  δ: 1
```

and the settings are `applications/retirement-choice/declaration/settings/retirement.yml`:

```yaml
# Numerical choices, not model content: the asset grids the methods tabulate on
# and the jump-detection threshold of the upper envelope scan. The FUES
# retirement example uses 3,000 points on assets between 1e-10 and 500 for both
# consumption stages, and a threshold of 1.01.
settings:
  n_a: 3000
  a_min: 1.0e-10
  a_max: 500
  n_a_ret: 3000
  a_ret_min: 1.0e-10
  a_ret_max: 500
  m_bar: 1.01
```

The calibration is the benchmark of the FUES retirement example. The settings are numerical choices and no part of the model: the asset grids on which the methods tabulate the arrival values, which serve also as the exogenous grids of savings of the endogenous grid entries, and the jump-detection threshold of the upper envelope scan. The number of dates is not a setting; it is the number of periods the trellis holds.

The recipe, `applications/retirement-choice/declaration/spec.yml`, names the trellis file and, for each stage, its stage file and the calibration, settings and methods files it reads, each by its path from the recipe's folder, and `load_recipe` reads it with the trellis file ([The Bellman factory](../../Bellman-Sym/08-bellman-factory.md)):

```yaml
# The recipe of the retirement model: the trellis file and each stage's file,
# by their paths from this folder, and for each stage and each kind the
# ordered sources; `$fill` is bound by keyword of `load_recipe`. The methods
# of a stage are the addition its methods list names, the `.bl` file
# `methods.bl` in the stage's own folder, read with the stage file at every
# occurrence; a change of method is another addition named in the list. The
# bequest declares no parameter or setting; its methods file states the
# derivative of its value, and it is active in the terminal period alone,
# `periods: [0, 0]`.
trellis: trellis.yml
stages:
  ret_choice:   {stage: stages/ret_choice/ret_choice.bl,     calibration: {all: [calibration/retirement, $fill]}, settings: {all: [settings/retirement, $fill]}, methods: {all: [stages/ret_choice/methods.bl]}}
  worker_cons:  {stage: stages/worker_cons/worker_cons.bl,   calibration: {all: [calibration/retirement, $fill]}, settings: {all: [settings/retirement, $fill]}, methods: {all: [stages/worker_cons/methods.bl]}}
  retiree_cons: {stage: stages/retiree_cons/retiree_cons.bl, calibration: {all: [calibration/retirement, $fill]}, settings: {all: [settings/retirement, $fill]}, methods: {all: [stages/retiree_cons/methods.bl]}}
  bequest:      {stage: stages/bequest/bequest.bl,           methods: {all: [stages/bequest/methods.bl]}, periods: [0, 0]}
```

## 8 References

- Dobrescu, L. I., and Shanker, A. "A fast upper envelope scan method for discrete-continuous dynamic programming." Working paper, SSRN No. 4181302.
- Iskhakov, F., Jørgensen, T. H., Rust, J., and Schjerning, B. (2017). "The endogenous grid method for discrete-continuous dynamic choice models with (or without) taste shocks." *Quantitative Economics* 8(2), 317–365.
