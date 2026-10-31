---
audience: user
type: example
topic: [applications]
---
# Retirement choice

> [!summary]
> A worker chooses at the start of each period whether to work or to retire, and then how much to consume; retirement is permanent. The model of Iskhakov, Jørgensen, Rust and Schjerning (2017) is written as three stage files: the choice between working and retiring, the consumption of a worker and the consumption of a retiree. The derivatives of the values and the steps of the endogenous grid method stand in block files, which the stages' methods files bind. A period file joins the three stages, and a trellis file joins the periods. Every file on this page is quoted from the application folder `applications/retirement-choice/`, and every result is printed from the package.

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

Its derivative line stands in the block file `applications/retirement-choice/declaration/methods/marginals_ret_choice.bl`, as the **marginal block** of the decision builder, a block of derivative lines that the stage's methods file binds with `!marginals` (§6):

```bl
@methods: ret_choice
# The derivative of the value of the discrete choice in assets, stated by the
# marginal block of the decision value builder: the derivative of the branch
# value the choice d selects; the cost of work, a constant, contributes nothing.

[id=dcsn_marginal, (V_w[>], V_r[>], d) : !cntn -> (V) : !dcsn] {
    D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]  :: [id=marginal]
}
```

The forward block `dcsn_to_cntn` holds one nested block for each label of the control `d`, and each writes its own branch's field: `a_w` on the work branch and `a_r` on the retire branch. A **branch** is one alternative of the choice, with its own continuation ([branch](../../wiki/branch.md)). The value statement `V = …` selects, by the tuple indexed by `d`, the worker's value less the cost of work or the retiree's value; the derivative line `D_{a_d}V = …` of the marginal block selects the derivative in assets of the chosen branch's value, in the same order; and the policy statement `d = argmax_{d}(…)` chooses a label whose entry of the same tuple is largest. [Branching](../../Bellman-Sym/05-branching.md) reads this file line by line. The package's queries `kind`, `branches` and `combination` answer, for this stage:

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

The derivative lines of its two values stand in the marginal blocks of `applications/retirement-choice/declaration/methods/marginals_worker_cons.bl`:

```bl
@methods: worker_cons
# The derivatives of the worker's two values, each stated by the marginal
# block of the value builder that writes the value. The decision value's line
# is the envelope condition; the arrival value's line keeps the factor R of the
# law w = R*a_w + y, which is not the identity.

[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {
    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]
}

[id=arvl_marginal, (V) : !dcsn -> (V[<]) : !arvl] {
    D_{a_w}V[<] = R*D_{w}V          :: [id=marginal]
}
```

and the steps of the endogenous grid method in the **method block** of `applications/retirement-choice/declaration/methods/worker_cons_egm.bl`, a block whose lines compute the output of the builder it opens, here the policy builder (§6):

```bl
@methods: worker_cons
# The endogenous grid method as the method block of the worker's policy
# builder, whose stage file states the maximization alone. The candidate line
# reads the derivative of the continuation value by the term D_{b}V[>]; the
# worker's continuation value need not be concave, so the block selects among
# the candidates by their values with an upper envelope.

[id=egm, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])                 :: [id=InvEuler]
    w[>] = b + c[>]                            :: [id=endoggrid]
    v[>] = 𝑢(c[>]) + β*V[>]                    :: [id=cand_value]
    c    = upper_env(w[>], c[>], v[>])          :: [id=envelope]
}
```

Cash on hand is `w = R*a_w + y`, and consumption lies in `Γ(w) = (0, w]`. The value statement adds the discounted continuation value to the utility of consumption, and the policy block states the maximization, which also declares the feasible set of consumption. The derivative line `D_{w}V = 𝑑𝑢(c)` of the first marginal block states the derivative of the value in cash on hand, `1/c`, and the second marginal block's line multiplies it by `R`, the factor of the law `w = R*a_w + y`, to state the derivative of the arrival value in assets. The method block writes the steps of the endogenous grid method as equations. The inverse Euler inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])`, which reads the derivative of the continuation value in savings, gives the candidate consumption at each level of savings. It carries no complementary-slackness clause `⟂ b >= 0`, which would pair the Euler equation with the borrowing limit, so it is read as the equation `c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{b}V[>])`: at every level of savings the candidate is the interior value, at which the Euler equation holds with equality ([Constraints](../../Bellman-Sym/10-constraints.md#43-the-clause-on-the-candidate-line) §4.3). The endogenous grid is `w[>] = b + c[>]`, the value of each candidate is `v[>]`, and the upper envelope `upper_env(w[>], c[>], v[>])` keeps, at each level of cash on hand, the candidate of largest value. The worker needs the upper envelope because her continuation value is not concave.

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

Its derivative lines stand in the marginal blocks of `applications/retirement-choice/declaration/methods/marginals_retiree_cons.bl`:

```bl
@methods: retiree_cons
# The derivatives of the retiree's two values, each stated by the marginal
# block of the value builder that writes the value. The decision value's line
# is the envelope condition; the arrival value's line keeps the factor R of the
# law w_ret = R*a_ret, which is not the identity.

[id=dcsn_marginal, (c) : !cntn -> (V) : !dcsn] {
    D_{w_ret}V = 𝑑𝑢(c)              :: [id=marginal]
}

[id=arvl_marginal, (V) : !dcsn -> (V[<]) : !arvl] {
    D_{a_ret}V[<] = R*D_{w_ret}V    :: [id=marginal]
}
```

and the steps of the endogenous grid method in the method block of `applications/retirement-choice/declaration/methods/retiree_cons_egm.bl`:

```bl
@methods: retiree_cons
# The endogenous grid method as the method block of the retiree's policy
# builder, whose stage file states the maximization alone. The candidate line
# reads the derivative of the continuation value by the term D_{b_ret}V[>].

[id=egm, (V[>] : [-inf, inf) @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn, "method = egm! will look for policy[>] and x[>] grid and invert it. Important here that the grids contain all constrained sections"] {
    c[>]     <= 𝑑𝑢𝑖𝑛𝑣(β*D_{b_ret}V[>])                :: [id=InvEuler, "Implies a correspondence: where equality holds, c[>] takes on a single value, where inequality holds, it is multiple values"]
    w_ret[>] = b_ret + c[>]                          :: [id=endoggrid]
    c        = c[>]                                  :: [id=cons_choice]
}
```

Cash on hand is `w_ret = R*a_ret`, with no wage. The method block writes the inverse Euler inequality and the endogenous grid as the worker's does, and then the **identification** `c = c[>]`, which equates the policy at the cash on hand of each level of savings with the candidate there. The package forms from the policy block the **policy builder**, the operator whose output is the policy. Once the methods file binds the method block, the builder's operations are the lines of that block, and `stage.dcsn.builder.policy.denote()` prints its card, a statement of its operations, with the maximization of the stage file under `Declared`. The card gives the identification as the operation `cons_choice:Pullback`, the policy composed with the cash on hand at each level of savings, with the rule `𝑐(𝑤_ret≻(b_ret)) = 𝑐≻(b_ret)` on `𝑤_ret≻(Xa)`, the set of cash on hand that the candidates reach. The inverse Euler inequality carries no clause, so the policy is stated on that set and not below it, where the borrowing limit binds ([Constraints](../../Bellman-Sym/10-constraints.md#43-the-clause-on-the-candidate-line) §4.3). The retiree's continuation value is concave, so the block needs no upper envelope. At zero assets the feasible set `(0, w_ret]` is empty, as the description of `Γ` in the file records.

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

A **trellis** is the sequence of periods, indexed backward from the last date: `periods[0]` is the terminal period, and `periods[h+1]` is the period one date before `periods[h]` ([Trellis syntax](../../Bellman-Sym/07-trellis.md)). The trellis file is `applications/retirement-choice/declaration/trellis.yml`:

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

Its derivative line stands in the marginal block of `applications/retirement-choice/declaration/methods/marginals_bequest.bl`, which the bequest's methods file binds (§6):

```bl
@methods: bequest
# The derivative of the terminal value in wealth, stated in closed form by the
# marginal block of the decision value builder: the savings left after the
# last date have no value, so the derivative is zero.

[id=dcsn_marginal, () -> (V) : !dcsn] {
    D_{x}V = 0                                         :: [id=marginal_wealth]
}
```

Its arrival field `a_bq` receives the savings of both consumption stages of the terminal period, through the connector `{b: a_bq, b_ret: a_bq}`. Its value is the continuation value `V[>]`, boundary data equal to zero, since the papers' agent consumes all her resources at the last date, and the derivative line `D_{x}V = 0` of its marginal block states that the derivative of its value in wealth is zero. The state-field connections are:

```text
period_joins(periods[0])["joins"]
  ret_choice:a_r → retiree_cons:a_ret
  ret_choice:a_w → worker_cons:a_w
  retiree_cons:b_ret → bequest:a_bq
  worker_cons:b → bequest:a_bq
```

The join check compares value fields alone. The terminal stage states the
derivative of its value in wealth, zero, by its marginal block, and the law
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

A methods file attaches a numerical method to a named place of a stage: a block, a line or an operator ([Methodization](../../Bellman-Sym/04-methodization.md)). The choice stage's methods file is `applications/retirement-choice/declaration/stages/ret_choice/methods.yml`:

```yaml
stage: ret_choice

methods:
  # The discrete choice is the larger of the two branch values. The handler is
  # the routine of the FUES retirement example that compares them.
  - on: policy
    method: !max
    handler: fues-retirement:dcsn_mover

  # The derivative of the choice value in assets, the derivative of the branch
  # value the choice selects, is stated by the marginal block of
  # marginals_ret_choice.bl on the decision value builder.
  - on: cntn_to_dcsn
    method: !marginals
    block: ../../methods/marginals_ret_choice.bl
```

The worker's is `applications/retirement-choice/declaration/stages/worker_cons/methods.yml`:

```yaml
stage: worker_cons

methods:
  # The endogenous grid method opens the policy builder with the method block
  # of worker_cons_egm.bl, which writes the grid line w[>] = b + c[>]; the
  # stage file states the maximization alone. The candidates the block
  # computes at each level of savings are selected by the upper envelope
  # below, since the worker's continuation value need not be concave.
  - on: policy
    method: !egm
    block: ../../methods/worker_cons_egm.bl
    handler: asva:make_egm_1d

  # The derivatives of the decision value and the arrival value are stated by
  # the two marginal blocks of marginals_worker_cons.bl, one for each value
  # builder.
  - on: cntn_to_dcsn
    method: !marginals
    block: ../../methods/marginals_worker_cons.bl

  - on: dcsn_to_arvl
    method: !marginals
    block: ../../methods/marginals_worker_cons.bl

  # The upper envelope over the candidates that satisfy the first-order
  # condition; m_bar is the jump-detection threshold of the scan.
  - on: upper_env
    method: !FUES
    handler: dcsmm:EGM_UE
    settings:
      m_bar: m_bar

  # The arrival value is tabulated on the asset grid; the entry on the line
  # dcsn_to_arvl.marginal represents the stated derivative of the arrival
  # value in assets on the same grid.
  - on: dcsn_to_arvl.value
    method: !Linear
    handler: dcsmm:interp_as_2
    settings:
      orders:
        a_w: n_a
      bounds:
        a_w: [a_min, a_max]

  - on: dcsn_to_arvl.marginal
    method: !Linear
    handler: dcsmm:interp_as_2
    settings:
      orders:
        a_w: n_a
      bounds:
        a_w: [a_min, a_max]
```

The retiree's is `applications/retirement-choice/declaration/stages/retiree_cons/methods.yml`:

```yaml
stage: retiree_cons

methods:
  # The endogenous grid method opens the policy builder with the method block
  # of retiree_cons_egm.bl, whose implicit statement c = c[>] gives the
  # policy; the stage file states the maximization alone. The retiree's
  # continuation value is concave, so no envelope operation is needed.
  - on: policy
    method: !egm
    block: ../../methods/retiree_cons_egm.bl
    handler: asva:make_egm_1d

  # The derivatives of the decision value and the arrival value are stated by
  # the two marginal blocks of marginals_retiree_cons.bl, one for each value
  # builder.
  - on: cntn_to_dcsn
    method: !marginals
    block: ../../methods/marginals_retiree_cons.bl

  - on: dcsn_to_arvl
    method: !marginals
    block: ../../methods/marginals_retiree_cons.bl

  # The arrival value is tabulated on the asset grid; the entry on the line
  # dcsn_to_arvl.marginal represents the stated derivative of the arrival
  # value in assets on the same grid.
  - on: dcsn_to_arvl.value
    method: !Linear
    handler: dcsmm:interp_as_3
    settings:
      orders:
        a_ret: n_a_ret
      bounds:
        a_ret: [a_ret_min, a_ret_max]

  - on: dcsn_to_arvl.marginal
    method: !Linear
    handler: dcsmm:interp_as_3
    settings:
      orders:
        a_ret: n_a_ret
      bounds:
        a_ret: [a_ret_min, a_ret_max]
```

The bequest's is `applications/retirement-choice/declaration/stages/bequest/methods.yml`:

```yaml
stage: bequest

methods:
  # The derivative of the terminal value in wealth, zero, is stated by the
  # marginal block of marginals_bequest.bl on the decision value builder.
  - on: cntn_to_dcsn
    method: !marginals
    block: ../../methods/marginals_bequest.bl
```

Binding each file to its stage with `methodize` gives:

```text
ret_choice    binds
worker_cons   binds
retiree_cons  binds
bequest       binds
```

The four files bind. The worker's endogenous grid entry opens the policy builder with the method block of `worker_cons_egm.bl`, whose four lines become the builder's operations, and the upper envelope over the candidates is the method `!FUES` on the block's line `envelope`, as the comment in the file records. The retiree's entry opens its policy builder with the method block of `retiree_cons_egm.bl`, which holds the identification `c = c[>]`. Each `!marginals` entry records the lines of a marginal block at the Evaluation of the value builder it names, as stated derivatives of the value, and adds no operation; the entries on `dcsn_to_arvl.marginal` represent the stated derivative of the arrival value on the asset grid. The worker's stage prints its methods, `str(stage.methods)`, as

```text
policy.envelope           !FUES
policy                    !egm   block ../../methods/worker_cons_egm.bl
cntn_to_dcsn:Evaluation   !marginals   block ../../methods/marginals_worker_cons.bl
dcsn_to_arvl:Evaluation   !marginals   block ../../methods/marginals_worker_cons.bl
dcsn_to_arvl:Evaluation   !Linear
```

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

The calibration is the benchmark of the FUES retirement example. The settings are numerical choices and no part of the model: the asset grids on which the methods tabulate the arrival values, and the jump-detection threshold of the upper envelope scan. The number of dates is not a setting; it is the number of periods the trellis holds.

The recipe, `applications/retirement-choice/declaration/spec.yml`, names the trellis file and, for each stage, its stage file and the calibration, settings and methods files it reads, each by its path from the recipe's folder, and `load_recipe` reads it with the trellis file ([The Bellman factory](../../Bellman-Sym/08-bellman-factory.md)):

```yaml
# The recipe of the retirement model: the trellis file and each stage's file,
# by their paths from this folder, and for each stage and each kind the
# ordered sources; `$fill` and the three methods slots are bound by keyword of
# `load_recipe`. Each stage has its own methods slot, `$ret_choice_method`,
# `$worker_method` and `$retiree_method`, so that a method choice reaches one
# stage. The bequest declares no parameter or setting; its one methods file
# binds the marginal block of its derivative, and it is active in the
# terminal period alone, `periods: [0, 0]`.
trellis: trellis.yml
stages:
  ret_choice:   {stage: stages/ret_choice/ret_choice.bl,     calibration: {all: [calibration/retirement, $fill]}, settings: {all: [settings/retirement, $fill]}, methods: {all: [stages/ret_choice/methods, $ret_choice_method]}}
  worker_cons:  {stage: stages/worker_cons/worker_cons.bl,   calibration: {all: [calibration/retirement, $fill]}, settings: {all: [settings/retirement, $fill]}, methods: {all: [stages/worker_cons/methods, $worker_method]}}
  retiree_cons: {stage: stages/retiree_cons/retiree_cons.bl, calibration: {all: [calibration/retirement, $fill]}, settings: {all: [settings/retirement, $fill]}, methods: {all: [stages/retiree_cons/methods, $retiree_method]}}
  bequest:      {stage: stages/bequest/bequest.bl,           methods: {all: [stages/bequest/methods]}, periods: [0, 0]}
```

## 8 References

- Dobrescu, L. I., and Shanker, A. "A fast upper envelope scan method for discrete-continuous dynamic programming." Working paper, SSRN No. 4181302.
- Iskhakov, F., Jørgensen, T. H., Rust, J., and Schjerning, B. (2017). "The endogenous grid method for discrete-continuous dynamic choice models with (or without) taste shocks." *Quantitative Economics* 8(2), 317–365.
