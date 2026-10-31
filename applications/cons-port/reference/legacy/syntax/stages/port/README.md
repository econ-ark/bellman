---
title: "Portfolio choice stage (port)"
audience: developer
type: index
---
# Portfolio choice stage (`port`)

This folder holds the stage YAML (Bellman-SYM's earlier YAML surface; the
`.bl` form is `applications/portfolio-choice/port.bl`) for a single
portfolio-choice stage with post-decision correlated shocks. The two files are:

- `port_stage.yaml` — the symbolic stage (symbols, spaces, equations); pure
  mathematical content, no methods or settings.
- `port_stage_methods.yml` — the methodization (operator-slot surface): which
  numerical scheme and which solver callable realize each named node.

The stage describes portfolio choice in which a correlated shock vector is
realized *after* the portfolio decision is taken (post-decision timing). The
arrival and decision states both carry `k`, the stock of investable assets. The
single decision is the risky share `ς ∈ [0,1]`. After the decision, the joint
shock vector `ζ = (Ψ, θ)` is realized, where `Ψ` is the risky return and `θ` is
an additive income term; the two are correlated log-normals built from an
underlying bivariate normal. The continuation state is

```
m = k·(ς·Ψ + (1−ς)·R) + θ,
```

the post-shock resources carried into the next stage. The Bellman form is a
maximization over an expectation,

```
V(k) = max_ς E_{Ψ,θ}[ V[>](m) ],
```

solved by value-function iteration (VFI).

## `port_stage.yaml`

The symbolic stage. It declares the spaces and symbols and the five equation
blocks that wire the three perches (arrival, decision, continuation) together.

### Stage name

The stage identifier. Period and connector files refer to the stage by this
name.

```yaml
# Stage name
name: port_stage
```

### Symbol declarations

The symbol table. Each group plays a fixed role in the stage:

- `spaces` declare the carrier sets. `Xk` and `Xm` are the asset and resource
  spaces (the strictly positive reals `R++`); `Π = [0,1]` is the unit interval
  that the risky share lives in; `Rp` and `Θ` are the supports of the two shock
  components.
- `prestate` carries `k`, the arrival-perch asset stock.
- `states` carries `k_d`, the decision-perch asset stock.
- `controls` carries the risky share `ς`.
- `exogenous` declares the shocks realized *after* the portfolio decision
  (post-decision timing). The joint vector `ζ = (Ψ, θ)` is a pair of correlated
  log-normals built from an underlying bivariate `Normal` with mean vector
  `Μ = [μ_Ψ, μ_θ]` and covariance matrix `Σ` whose off-diagonal entries carry
  the correlation `ρ_ζ` of the underlying normals.
- `poststates` carries the continuation resources `m`.
- `values` declares the value function on each perch: arrival `V[<]`, decision
  `V`, and continuation `V[>]`.
- `parameters` declare the gross safe return `R`, the shock means and standard
  deviations (`μ_Ψ, σ_Ψ, μ_θ, σ_θ`), and the correlation `ρ_ζ ∈ [-1,1]` of the
  underlying normals in the joint vector `ζ`.

```yaml
# Symbol declarations
symbols:
  spaces:
    Xk: "@def R++"
    Xm: "@def R++"
    Π:  "@def [0,1]"
    Rp: "@def R++"
    Θ:  "@def R++"

  prestate:
    k: "@in Xk"

  states:
    k_d: "@in Xk"

  controls:
    ς: "@in Π"

  exogenous:
    Ψ: "@in Rp"
    θ: "@in Θ"
    ζ:
      "@dist": Normal
      Μ: [μ_Ψ, μ_θ]
      Σ: [[σ_Ψ^2, ρ_ζ*σ_Ψ*σ_θ], [ρ_ζ*σ_Ψ*σ_θ, σ_θ^2]]

  poststates:
    m: "@in Xm"

  values:
    V[<]: "@in R"
    V: "@in R"
    V[>]: "@in R"

  parameters:
    R: "@in R++"
    μ_Ψ: "@in R"
    σ_Ψ: "@in R+"
    μ_θ: "@in R"
    σ_θ: "@in R+"
    ρ_ζ: "@in [-1,1]"
```

### Stage equations

The five equation blocks define the forward transitions, the backward value
aggregation, and the policy. They are described block by block below.

```yaml
# Stage equations
equations:
```

#### Arrival to decision transition

There are no shocks between arrival and decision: the decision-perch asset stock
simply inherits the arrival stock, `k_d = k`. The equation is left unnamed,
which is fine — it is assigned an index automatically.

```yaml
  # Arrival to decision transition
  arvl_to_dcsn:
    - k_d = k
```

#### Decision to continuation transition

The joint post-decision shocks are realized in this transition. Resources
carried into the continuation perch are the portfolio return on the asset stock
plus the additive income shock,

```
m = k_d·(ς·Ψ + (1−ς)·R) + θ.
```

```yaml
  # Decision to continuation transition
  dcsn_to_cntn:
    - m = k_d*(ς*Ψ + (1-ς)*R) + θ
```

#### Backward value aggregation

Backward evaluation. This block forms the objective — the induced aggregator
that takes the expectation of the continuation value over the joint shocks, with
no maximization. The maximization over `ς` is lifted into the `policy` block
below.

```yaml
  # Backward value aggregation
  cntn_to_dcsn:
    - V = E_{Ψ,θ}(V[>])
```

#### Decision to arrival value

There is no expectation at arrival: the arrival-to-decision transition is
deterministic, so the arrival value equals the decision value, `V[<] = V`.

```yaml
  # Decision to arrival value
  dcsn_to_arvl:
    - V[<] = V
```

#### Policy construction

Policy construction, which carries the solution method. The policy is the direct
selection of the risky share that maximizes the expected continuation value
(VFI),

```
ς = argmax_ς E_{Ψ,θ}[ V[>] ].
```

```yaml
  # Policy construction
  policy:
    - ς = argmax_{ς}(E_{Ψ,θ}(V[>]))
```

## `port_stage_methods.yml`

The methodization for `port_stage.yaml`, following the operator-slot surface of
spec 0.1d / spec 0.1d.1: one entry per named node (`on: <node>` with a
`method: !tag`, and no `schemes:` list). Under the kernel/policy schema of spec
0.3, the VFI solution method and the maximization over `ς` attach to the
`policy` node; the expectation attaches to the `E_Ψ_θ` instance; and the value
representation (grid plus interpolation) attaches to `evaluate`. The scheme to
node map follows spec 0.1d.1 §3.

Handler citations pin "the horse" — the actual solver callable that realizes
each node (spec 0.1d.1, formerly `tool:`). The port stage is realized by the
application's own bespoke VFI solver in `code/solve_port_cons.py` (toolkit id
`cons-port`). The joint quadrature is built by hand from numpy's Gauss–Hermite
primitive.

### Stage this methodization applies to

Names the stage that the methodization binds to; it must match the `name:` in
`port_stage.yaml`.

```yaml
# Stage this methodization applies to
stage: port_stage
```

### Operator-slot methodization

One entry per named node. The entries, in order, cover: the expectation
operator, the policy (VFI) node, the value representation (`evaluate`), the
identity arrival evaluation, the three transitions, and the forward simulation
builders. Each is described below; the full block follows at the end of this
section.

**Expectation operator instance (`E_Ψ_θ`), over the joint shocks.** Realized by
tensor-product Gauss–Hermite quadrature. The handler
`cons-port:_build_joint_quadrature`
(`code/solve_port_cons.py:_build_joint_quadrature`) builds tensor-product
Gauss–Hermite nodes and weights; the integral is applied as
`np.dot(weights, ·)` inside `solve_stage_vfi`. The marginals come from
`numpy:hermegauss` (`numpy.polynomial.hermite_e.hermegauss`, via
`_build_gauss_hermite_lognormal`). The number of nodes is carried as the setting
`n_nodes: n_joint_nodes`.

**Policy construction (`policy`), VFI by direct maximization over `ς` — the spec
0.3 policy node.** The policy block authors the direct selection
`ς = argmax_ς(E_{Ψ,θ}(V[>]))`. The VFI selection method, which *is* the
maximization over `ς`, attaches to the `policy` node, following the spec 0.1d.1
retired-scheme map (maximization maps to the policy node) and the
one-method-per-node discipline. The optimizer's `max` is derived
(`max := evaluate ∘ ⟨id, argmax⟩`): the `argmax` node feeds the `evaluate` node
below, so `argmax_ς` and `evaluate` are both explicit graph nodes and the
`argmax` node needs no second method. The handler `cons-port:solve_stage_vfi`
(`code/solve_port_cons.py:solve_stage_vfi`) computes
`V(k) = max_ς E_{Ψ,θ}[V_cont(g(k,ς,Ψ,θ))]`; the inner grid search over
`s_candidates` is the argmax.

A note for review. A previous version of this file also carried a separate
`- on: argmax_ς` entry with `method: !scipy-bounded`. In this stage `argmax_ς`
and `policy` resolve to the *same* single argmax node, so that amounted to two
methods on one node (the second was never applied), and the `!scipy-bounded` tag
was wrong: the actual computation is a brute-force grid search over
`s_candidates = linspace(0,1,n_s)`, with no scipy call. The entry was removed to
honour one-method-per-node, and the maximization is carried by `!vfi` here. The
sibling `unemployment-branching/worker_port` stage still has the duplicate entry;
that is out of scope for this cons-port pass and is flagged for a later
consistency sweep.

**Backward evaluation block (`evaluate`), value representation.** Linear
interpolation of the value function between grid points. The decision-state grid
is a Cartesian discretization of `k`, with orders and bounds carried as
settings. The handler `cons-port:_make_interp`
(`code/solve_port_cons.py:_make_interp`) is an `np.interp` linear `V_cont`
carrier; the continuation value `V` is interpolated on the `k`/`m` grid. The
settings are `orders: [n_k]` and `bounds: [[k_min, k_max]]`.

**Arrival evaluation block (`dcsn_to_arvl`), identity — no method.** The
decision-to-arrival map is the identity (`V[<] = V`), and the
arrival-to-decision transition is `k_d = k`. Neither has a dedicated solver
callable, so the handler is left blank.

**Transitions (`arvl_to_dcsn`, `dcsn_to_cntn`), pure functions compiled from
the equation strings.** `arvl_to_dcsn` has no method. `dcsn_to_cntn` is the
post-decision returns and income law `m = k_d·(ς·Ψ + (1−ς)·R) + θ`; it is
realized inline in the VFI solver as the transition callable that maps
`(k_d, ς, Ψ, θ) → m` before the expectation. Its handler is
`cons-port:transition` (`code/solve_port_cons.py:compile_stage.transition`, the
exo branch).

**Forward builders (simulation).** No forward-simulation code exists in this
application, so the `!monte-carlo` tag below has no realizing horse and its
handler is left blank. `arvl_to_dcsn_builder` carries the `!deterministic`
method. `dcsn_to_cntn_builder` carries `!monte-carlo` with settings
`n_paths: n_sim` and `seed: sim_seed`.

```yaml
# Operator-slot methodization (one entry per named node)
methods:
  - on: E_Ψ_θ
    method: !gauss-hermite
    handler: cons-port:_build_joint_quadrature
    settings:
      n_nodes: n_joint_nodes

  - on: policy
    method: !vfi
    handler: cons-port:solve_stage_vfi

  - on: evaluate
    method: !linear
    handler: cons-port:_make_interp
    settings:
      orders: [n_k]
      bounds: [[k_min, k_max]]

  - on: dcsn_to_arvl

  - on: arvl_to_dcsn

  - on: dcsn_to_cntn
    handler: cons-port:transition

  - on: arvl_to_dcsn_builder
    method: !deterministic

  - on: dcsn_to_cntn_builder
    method: !monte-carlo
    settings:
      n_paths: n_sim
      seed: sim_seed
```
