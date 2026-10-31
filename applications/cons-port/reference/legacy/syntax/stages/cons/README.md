---
title: "cons stage — stage YAML"
audience: developer
type: index
---
# `cons` stage — stage YAML

This folder holds the stage YAML (Bellman-SYM's earlier YAML surface; the
`.bl` form is `applications/portfolio-choice/cons.bl`) for the deterministic
consumption-choice stage `cons`, part of the *Portfolio Choice with Correlated
Shocks* application. Two files describe the stage:

- `cons_stage.yaml` — the symbolic stage (pure mathematical content: symbols and
  equations, no handlers or numerical settings beyond the declared `settings`
  block).
- `cons_stage_methods.yml` — the methodization: it pairs each named node of the
  stage with a solution method and the solver callable (handler) that realizes
  it.

The commentary that used to live inline in the two YAML files has been moved
here. Each YAML now carries exactly one short headline comment above each block;
the full explanation for each block is in the matching section below, followed by
the cleaned YAML.

## `cons_stage.yaml`

The symbolic stage for the deterministic consumption choice. The stage is
EGM-friendly: its policy block is written so that the solution method can be the
endogenous-grid method.

### Stage name

The stage identifier used throughout the application and referenced from the
methodization file.

```yaml
# Stage name
name: cons_stage
```

### Symbol declarations

The symbols carried by the stage, grouped by role. `spaces` declares the
mathematical domains `Xm` (strictly positive reals, cash-on-hand) and `Xa`
(non-negative reals, post-decision assets). The remaining groups declare the
prestate `m`, the decision state `m_d`, the post-state `a`, the control `c`, the
value fields at the three perches (`V[<]` arrival, `V` decision, `V[>]`
continuation), and their marginal counterparts (`dV[<]`, `dV`, `dV[>]`). The
parameters are the discount factor `β` and the relative-risk-aversion coefficient
`ρ`. The `settings` group holds the numerical and simulation knobs: the
cash-on-hand grid size `n_m` with bounds `m_min`/`m_max`, and the simulation draw
count `n_sim` with seed `sim_seed`.

```yaml
# Symbol declarations
symbols:
  spaces:
    Xm: "@def R++"
    Xa: "@def R+"
  prestate:
    m: "@in Xm"
  states:
    m_d: "@in Xm"
  poststates:
    a: "@in Xa"
  controls:
    c: "@in R+"
  values:
    V[<]: "@in R"
    V: "@in R"
    V[>]: "@in R"
  values_marginal:
    dV[<]: "@in R+"
    dV: "@in R+"
    dV[>]: "@in R+"
  parameters:
    β: "@in (0,1)"
    ρ: "@in R+"
  settings:
    n_m: "@in Z+"
    m_min: "@in R+"
    m_max: "@in R+"
    n_sim: "@in Z+"
    sim_seed: "@in Z+"
```

### Stage equations

The `equations` block collects the forward transitions, the backward movers, and
the policy-construction step. It is organised into the sub-blocks documented
below.

```yaml
# Stage equations
equations:
```

#### Arrival to decision transition (g_av)

There is no shock between arrival and decision, so the decision state equals the
arrival state. This line defines the `g_av` function — a canonical core
mathematical object that must be defined in the stage syntax (see the
documentation on the math / stage-syntax mapping).

```yaml
  # Arrival to decision transition (g_av)
  arvl_to_dcsn:
    - m_d = m
```

#### Decision to continuation transition (g_ve savings law)

This line defines the `g_ve` function, the post-decision savings law: assets
carried forward are cash-on-hand at decision minus consumption.

```yaml
  # Decision to continuation transition (g_ve savings law)
  dcsn_to_cntn:
    - a = m_d - c
```

#### Backward decision mover (induced aggregator, no max)

This is the backward-iteration evaluation slot — the induced aggregator (`T_σ`),
which carries no maximisation. It has three lines:

- `reward` — the per-period felicity as a function of the control `c`. Written as
  `u[c] = (c^(1-ρ))/(1-ρ)`, this defines `u` as a *function of* `c`: the line
  does not get its own node, but `u_fn` is defined and can be used downstream. An
  equivalent bare form would have been `= (c^(1-ρ))/(1-ρ)`.
- `dcsn_val` — the inner objective `V = u_fn[c] + β*V[>]` (no max). Both
  `V = u + β*V[>]` and `V = u_fn[c] + β*V[>]` are valid here.
- `marginal` — the marginal (envelope) value `dV = (c)^(-ρ)`. It is named so that
  methods can target it as `on: cntn_to_dcsn.marginal`.

All graphs ending in `V` and `dV` carry an implicit `evaluate` tag, so
`dcsn_val: V = u_fn[c] + β*V[>]` is the same as
`V = evaluate(u_fn[c] + β*V[>])`. See the note on implicit versus explicit
`evaluate` at the end of this file.

```yaml
  # Backward decision mover (induced aggregator, no max)
  cntn_to_dcsn:
    - reward: u[c] = (c^(1-ρ))/(1-ρ)
    - dcsn_val: V = u_fn[c] + β*V[>]
    - marginal: dV = (c)^(-ρ)
```

#### Backward arrival mover (deterministic, no max)

The deterministic arrival-to-decision mover, carrying no maximisation: the value
then the marginal value pass through unchanged from the decision perch to the
arrival perch.

```yaml
  # Backward arrival mover (deterministic, no max)
  dcsn_to_arvl:
    - V[<] = V
    - dV[<] = dV
```

#### Policy construction (EGM kernel/policy)

The policy-construction slot follows the kernel/policy schema. It constructs the
policy `σ` and carries the solution method: the `!egm` tag attaches to the
`policy` node in `cons_stage_methods.yml`. The optimiser max is derived
(`max := evaluate ∘ ⟨id, argmax⟩`), so no `max` is written here. This mirrors the
reference EGM stage in `applications/consumption-savings-iid/stage.yaml`.

The three lines are:

- `InvEuler` — the inverse-Euler / endogenous-grid step. Consumption as a
  function of the post-state `a`: `c[>] = (β*dV[>])^(-1/ρ)`. There is no
  interpolant here; it is the scalar first-order-condition inversion.
- `reverse_state` — the EGM endogenous-grid regrid `m_d[>] = a + c[>]`, the
  endogenous cash-on-hand on which `c[>]` lives.
- `pol_func` — the evaluation that builds the decision-perch policy function `c`
  on the decision state `m_d` from the EGM candidates `c[>]` over the endogenous
  grid `m_d[>]`: `c = evaluate(c[>], m_d[>], m_d)`. `evaluate` is a node by
  nature; it carries the interpolation/representation method (`on: evaluate`).

The two named scalar lines (`InvEuler`, `reverse_state`) are addressable
composition boundaries via their node names; methods target them as
`on: policy.<name>`. They carry the `@node` marker — the explicit
lift-to-node marker, which the cat parser strips and records (`node_tagged`);
their names remain the method-attachment targets.

A VFI alternative, mutually exclusive with the EGM lines above, would be a single
line `c = argmax_{c}((c^(1-ρ))/(1-ρ) + β*V[>])`.

```yaml
  # Policy construction (EGM kernel/policy)
  policy:
    - InvEuler: "c[>] = (β*dV[>])^(-1/ρ) @node"
    - reverse_state: "m_d[>] = a + c[>] @node"
    - pol_func: c = evaluate(c[>], m_d[>], m_d)
```

### Note: `evaluate` — same-grid (implicit) versus regrid (explicit)

These are two shapes of one operator.

- **Same-grid (implicit):** represent a value field on its own state grid. A
  value or marginal-value field (`V`, `dV`) denotes a function on the perch
  state, so it always ends in an implicit `evaluate` — the type of the left-hand
  side implies it:

  `V = u_fn[c] + β*V[>]   ==   V = evaluate(u_fn[c] + β*V[>])`

  The source grid equals the output grid, so nothing is named and the call can be
  dropped.

- **Regrid (explicit):** move data between grids — this is the EGM swap:

  `c = evaluate(c[>], m_d[>], m_d)`

  Interpolate the candidates `c[>]` (on the endogenous knots `m_d[>]`) onto the
  decision grid `m_d`. The grids must be named, so this `evaluate` is always
  written — it is where EGM actually happens.

The rule: `evaluate` is implicit when the source grid equals the output grid (a
representation carrier); it must be written when it regrids (source grid not equal
to query grid).

## `cons_stage_methods.yml`

The methodization for `cons_stage.yaml`, written on the operator-slot surface:
one entry per named node (`on: <node>` paired with `method: !tag`, with no
`schemes:` list). This is a deterministic consumption-choice stage that is
EGM-friendly. Stage-specific methodization lets EGM attach here without affecting
expectation-only stages such as `noport_stage`.

Under the kernel/policy schema the EGM solution method attaches to the `policy`
node; the evaluation block carries only the representation slot (`evaluate`). The
scheme-to-node map follows the operator-slot specification.

Handler citations (`handler: <id>`) pin the actual solver callable that realizes
each node. This stage is realized by the application's own bespoke EGM solver in
`code/solve_port_cons.py` (toolkit id `cons-port`). The same stage also has a
dolo-backed EGM path through `code/semiconjugate_solve.py`, which delegates the
inverse-Euler and regrid steps to `dolo.algos.egm` (there is no dolo Rosetta card
yet — a stop-gap `dolo:` comment is used there).

### Stage this methodization targets

Names the stage that the bindings below apply to.

```yaml
# Stage this methodization targets
stage: cons_stage
```

### Node-to-method-and-handler bindings

Each entry binds one named node to a solution method (where applicable) and to
the handler that realizes it. The entries are:

- **`policy`** — policy construction (EGM). This entry carries the solution
  method `!egm` and the handler `cons-port:solve_stage_egm`
  (`code/solve_port_cons.py:solve_stage_egm`, the bespoke EGM loop; the dolo path
  is `dolo:egm`, with the new dolo Rosetta stone to be confirmed, in
  `code/semiconjugate_solve.py`).
- **`policy.InvEuler`** — the inverse-Euler / endogenous-grid step, the named
  `policy.InvEuler` scalar node. As a scalar g-function node it is method-less and
  carries only a handler, `cons-port:inv_euler`
  (`code/solve_port_cons.py:compile_stage.inv_euler`, the closed-form
  first-order-condition inversion `c = (β·dV_cont)^(-1/ρ)`). The selection method
  `!egm` lives on the `policy` composite above.
- **`policy.reverse_state`** — the EGM endogenous-grid reverse map
  `m_d = a + c`, the named `policy.reverse_state` scalar node. A scalar g-function
  node is method-less; it carries only the handler `cons-port:transition_rev`
  (`code/solve_port_cons.py:compile_stage.transition_rev`, `m_d = a + c`).
- **The backward evaluation block** — value representation on the interpolation
  grid. This entry binds three evaluation sub-nodes
  (`evaluate.cntn_to_dcsn.dcsn_val.evaluate`,
  `evaluate.cntn_to_dcsn.marginal.evaluate`,
  `evaluate.cntn_to_dcsn.pol_func.evaluate`) to the `!Cartesian` method, with
  settings `orders: [n_m]` and `bounds: [[m_min, m_max]]`, and the handler
  `cons-port:_make_interp` (`code/solve_port_cons.py:_make_interp`, the `np.interp`
  linear value/policy carrier on `m_grid`; the dolo path uses a cubic decision-rule
  resample).
- **`cntn_to_dcsn.marginal`** — the marginal (envelope) value, the named
  `cntn_to_dcsn.marginal` scalar node. This is a separate value-side object; as a
  scalar node it is method-less and carries only the handler
  `cons-port:marginal_value` (`code/solve_port_cons.py:compile_stage.marginal_value`,
  the envelope condition `dV = c^(-ρ)`).
- **`dcsn_to_arvl`** and **`arvl_to_dcsn`** — the identity arrival block and the
  pure-substitution arrival-to-decision transition. `dcsn_to_arvl` is the identity
  (`V[<] = V`); `arvl_to_dcsn` is `m_d = m`. Neither has a dedicated solver
  callable, so the handler is left blank.
- **`dcsn_to_cntn`** — the forward savings law `a = m_d − c`. It is realized in the
  EGM solver as the forward transition used in value recovery, via the handler
  `cons-port:transition_fwd`
  (`code/solve_port_cons.py:compile_stage.transition_fwd`, `a = m_d − c`).
- **`arvl_to_dcsn_builder`** and **`dcsn_to_cntn_builder`** — the forward builders
  used in simulation. No forward-simulation code exists in this application, so the
  handler is left blank (no callable realizes the push-forward).
  `arvl_to_dcsn_builder` carries the `!deterministic` method.

```yaml
# Node-to-method-and-handler bindings
methods:
  - on: policy
    method: !egm
    handler: cons-port:solve_stage_egm

  - on: policy.InvEuler
    handler: cons-port:inv_euler

  - on: policy.reverse_state
    handler: cons-port:transition_rev

  - on: evaluate.cntn_to_dcsn.dcsn_val.evaluate, evaluate.cntn_to_dcsn.marginal.evaluate, evaluate.cntn_to_dcsn.pol_func.evaluate
    method: !Cartesian
    settings:
      orders: [n_m]
      bounds: [[m_min, m_max]]
    handler: cons-port:_make_interp

  - on: cntn_to_dcsn.marginal
    handler: cons-port:marginal_value

  - on: dcsn_to_arvl

  - on: arvl_to_dcsn

  - on: dcsn_to_cntn
    handler: cons-port:transition_fwd

  - on: arvl_to_dcsn_builder
    method: !deterministic

  - on: dcsn_to_cntn_builder
```
