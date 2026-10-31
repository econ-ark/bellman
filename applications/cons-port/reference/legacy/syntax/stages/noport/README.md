---
title: "noport stage"
audience: developer
type: index
---
# `noport` stage

This folder holds the stage YAML (Bellman-SYM's earlier YAML surface; the
`.bl` form is `applications/portfolio-choice/noport.bl`) for the `noport`
stage of the portfolio-choice-with-correlated-shocks application, together
with its companion methodization.

The `noport` stage is a shock-realization stage with no decision. It carries
investable assets `k` (the arrival and decision state), realizes the
post-decision transitory income shock `θ` between decision and continuation,
and produces cash-on-hand `m = k*R + θ` as the continuation state. The stage
plays two roles in the application: it is the "no-portfolio" leg of a
`noport → cons` period, and it serves as a bridge whenever the model needs to
move from an `a`-ending object to an `m`-starting object across periods.

This README records the explanation that previously lived as inline comments
inside the two YAML files. Each file has its own section below, and within a
file each block has a heading carrying that block's headline comment, the
explanation rewritten as prose, and the cleaned YAML block.

## `noport_stage.yaml`

The stage YAML declares the symbols and the four backward/forward transition
blocks. It carries no methods, no parameter values, and no settings values;
those belong to the methodization and calibration layers.

### Stage name

The stage is named `noport_stage`.

```yaml
# Stage name
name: noport_stage
```

### Symbol declarations

The symbol block declares the spaces, the perch states, the post-decision
shock, the value functions, the parameters, and the numerical settings.

The spaces are the positive reals for investable assets (`Xk`),
cash-on-hand (`Xm`), and the income shock support (`Θ`). The arrival prestate
is `k`. The exogenous shock `θ` is realized after the (trivial) decision; it
takes values in `Θ` and follows a lognormal distribution with parameters
`μ_θ` and `σ_θ`. The decision state is `k_d`, and the continuation poststate
is cash-on-hand `m`. The value functions at the three perches are `V[<]`
(arrival), `V` (decision), and `V[>]` (continuation). The parameters are the
gross return `R`, the income-shock location `μ_θ`, and the income-shock scale
`σ_θ`. The settings block holds the numerical knobs referenced by
`noport_stage_methods.yml`: the cash-on-hand grid size `n_m` and bounds
`m_min`, `m_max`; the number of income quadrature nodes `n_θ_nodes`; and the
simulation sample size `n_sim` and seed `sim_seed`.

```yaml
# Symbol declarations
symbols:
  spaces:
    Xk: "@def R++"
    Xm: "@def R++"
    Θ:  "@def R++"

  prestate:
    k: "@in Xk"

  exogenous:
    θ:
      - "@in Θ"
      - "@dist LogNormal(μ_θ, σ_θ)"

  states:
    k_d: "@in Xk"

  poststates:
    m: "@in Xm"

  values:
    V[<]: "@in R"
    V: "@in R"
    V[>]: "@in R"

  parameters:
    R: "@in R++"
    μ_θ: "@in R"
    σ_θ: "@in R+"

  settings:
    n_m: "@in Z+"
    m_min: "@in R+"
    m_max: "@in R+"
    n_θ_nodes: "@in Z+"
    n_sim: "@in Z+"
    sim_seed: "@in Z+"
```

### Stage equations

The equations block holds the four transition sub-blocks.

```yaml
# Stage equations
equations:
```

#### Arrival to decision transition

There is no shock between arrival and decision: the decision state simply
copies the prestate, `k_d = k`.

```yaml
  # Arrival to decision transition
  arvl_to_dcsn:
    - k_d = k
```

#### Decision to continuation transition

The income shock is realized after the decision. Cash-on-hand at the
continuation perch is the return on investable assets plus the realized
income shock, `m = k_d*R + θ`.

```yaml
  # Decision to continuation transition
  dcsn_to_cntn:
    - m = k_d*R + θ
```

#### Continuation to decision backward evaluation

Because there is no choice in this stage, the decision value carries no
maximization. It is simply the expectation of the continuation value over the
post-decision income shock, `V = E_{θ}(V[>])`.

```yaml
  # Continuation to decision backward evaluation (expectation, no max)
  cntn_to_dcsn:
    - V = E_{θ}(V[>])
```

#### Decision to arrival backward evaluation

There is no expectation at arrival; the arrival-to-decision step is
deterministic, so the arrival value equals the decision value, `V[<] = V`.

```yaml
  # Decision to arrival backward evaluation
  dcsn_to_arvl:
    - V[<] = V
```

## `noport_stage_methods.yml`

The methodization binds each named node of the stage to a numerical method tag
and a realizing handler (the "horse," the actual solver callable; this is the
field formerly written as `tool:`).

### Whole-step semiconjugate solve

The single most important fact about this methodization is that the `noport`
stage is not solved on its own. It is the expectation leg `E` of the composed
period `Ŝ = M ∘ E`, where the consumption stage is `M` and the `noport` stage
is `E`. The solver in `code/semiconjugate_solve.py` does two things. First, in
the translation step, `translate_doloplus_to_horse()` calling
`doloplus_to_dolo()` turns the composed Bellman-SYM period into one vanilla-Dolo
horse that implements `Ŝ`. Second, in the solve step, `solve_nest_egm()`
calling `dolo.algos.egm.egm(maxit=1)` solves that whole horse with Dolo's
native EGM, one `Ŝ` step per period.

Every node below is therefore realized inside that single whole-step Dolo EGM
solve of the translated horse; there is no independent per-node Dolo call. The
application's own contribution is the semiconjugate wrapping: the translation
and the `solve_nest_egm` driver, which compose Dolo's EGM beneath them. (Per
the card schemas, an application handler may compose a packaged-toolkit handler
beneath it.) The composition of `dolo:egm` is a stop-gap: no Dolo Rosetta-stone
card exists yet, so the dependency is recorded informally pending a future Dolo
Rosetta stone.

The `handler:` field pins the horse. For every numerical node here the horse is
the same whole-step driver `cons-port:solve_nest_egm`
(`code/semiconjugate_solve.py:solve_nest_egm`); the prose for each node names
which Dolo internal carries that node inside it.

### Stage this methodization targets

The methodization targets `noport_stage`.

```yaml
# Stage this methodization targets
stage: noport_stage
```

### Node-to-method-and-handler bindings

The `methods` block lists one entry per named node. Each entry names the node
under `on:`, optionally a method tag under `method:`, optionally a handler, and
optionally node-specific settings. The individual node bindings follow.

```yaml
# Node-to-method-and-handler bindings
methods:
```

#### `E_θ` — expectation leg

`E_θ` is the expectation leg of `Ŝ`. It is carried inside the whole-step EGM as
the translated horse's `expectation` gufunction, summed over Dolo's discretized
IID income process (Gauss–Hermite atoms and weights). The method tag is
therefore `!gauss-hermite`. It is honoured by the whole-step driver and is not
a separate Dolo call; inside the Dolo EGM this node corresponds to
`funs["expectation"]`. The node carries the number of quadrature nodes
`n_θ_nodes`.

```yaml
  - on: E_θ
    method: !gauss-hermite
    handler: cons-port:solve_nest_egm
    settings:
      n_nodes: n_θ_nodes
```

#### `evaluate` — m-space EGM decision rule

`evaluate` is the cash-on-hand-space EGM decision rule carried by `egm()`,
which performs linear interpolation on the endogenous grid. It is honoured
inside the same whole-step solve; inside the Dolo EGM the rule is evaluated by
`eval_linear` on the endogenous grid. The method tag is `!Cartesian`, with the
grid order taken from `n_m` and the grid bounds from `m_min` and `m_max`.

```yaml
  - on: evaluate
    method: !Cartesian
    handler: cons-port:solve_nest_egm
    settings:
      orders: [n_m]
      bounds: [[m_min, m_max]]
```

#### `dcsn_to_arvl` — arrival evaluation block

The arrival evaluation block is the identity `V[<] = V`. It has no method and
no horse.

```yaml
  - on: dcsn_to_arvl
```

#### `arvl_to_dcsn` — arrival to decision

The arrival-to-decision step is the identity `k_d = k`. It has no method and no
horse.

```yaml
  - on: arvl_to_dcsn
```

#### `dcsn_to_cntn` — decision to continuation transition

The decision-to-continuation transition `m = k_d·R + θ` is realized as the
translated horse's `half_transition` gufunction inside the whole-step EGM;
inside the Dolo EGM this node corresponds to `funs["half_transition"]`.

```yaml
  - on: dcsn_to_cntn
    handler: cons-port:solve_nest_egm
```

#### `arvl_to_dcsn_builder` — forward builder

The forward builders are for simulation. No forward-simulation code exists in
this application, so the builder tags below have no realizing horse and the
handler is left blank. The arrival forward builder carries the
`!deterministic` method tag.

```yaml
  - on: arvl_to_dcsn_builder
    method: !deterministic
```

#### `dcsn_to_cntn_builder` — forward builder

The decision-to-continuation forward builder carries the `!monte-carlo` method
tag, with the number of simulation paths taken from `n_sim` and the seed from
`sim_seed`. As with the arrival builder, no forward-simulation code realizes it,
so the handler is left blank.

```yaml
  - on: dcsn_to_cntn_builder
    method: !monte-carlo
    settings:
      n_paths: n_sim
      seed: sim_seed
```
