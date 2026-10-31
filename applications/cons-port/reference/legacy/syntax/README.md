---
title: "cons-port syntax folder"
audience: developer
type: index
---
# cons-port syntax folder

This folder holds the stage YAML for the *port-with-shocks* application —
Bellman-SYM's earlier YAML surface (older text calls it dolang+ or dolo-plus),
read by the legacy dolo and dolang pipeline, archived outside the repository on 13 September 2026. The same stages in the
current `.bl` surface are `applications/portfolio-choice/{cons,port,noport,disc}.bl`.
The files here describe shared parameter values, numerical settings, and the
period templates that sequence the individual stages. The stage definitions
themselves live in the `stages/` subfolder and are documented separately.

The YAML files have been cleaned so that each block carries a single short
headline comment; the longer explanations that previously lived inline are
collected here as prose.

## calibration.yaml

Unified calibration covering all stages in this library: the
consumption-savings stage (`cons_stage`) with CRRA utility, the portfolio
choice stage (`port_stage`) with risky and safe assets, and the no-portfolio
shock-realization stage (`noport_stage`). Parameters are shared across stages
wherever their names overlap.

### Calibration block

The `calibration` block holds parameter values used to instantiate the
mathematical problem.

The `parameters` map collects every shared parameter:

- **Preferences (used by `cons_stage`).** `β` is the discount factor and `ρ`
  is the coefficient of CRRA risk aversion, equal to the reciprocal of the
  elasticity of intertemporal substitution.
- **Returns (used by `port_stage` and `noport_stage`).** `R` is the gross
  risk-free return.
- **Risky return shock `Ψ` (used by `port_stage` only).** The risky return is
  log-normal, `LogNormal(μ_Ψ, σ_Ψ)`, calibrated so that the expected return is
  approximately 1.06, an expected excess return of about six per cent. Here
  `μ_Ψ` is the log-mean and `σ_Ψ` the log-standard-deviation of the risky
  return.
- **Transitory income shock `θ` (used by `port_stage` and `noport_stage`).**
  Transitory income is log-normal, `LogNormal(μ_θ, σ_θ)`, calibrated so that
  its expectation equals one. The log-mean `μ_θ` is set to zero to normalize
  the level, and `σ_θ` is the log-standard-deviation.
- **Shock correlation (placeholder in `port_stage`).** `ρ_ζ` is the
  correlation between the risky return shock `Ψ` and the transitory income
  shock `θ`. It is a placeholder and is not yet wired into the model.

```yaml
# Calibration block
calibration:
  # Parameter values shared across stages
  parameters:
    β: 0.96
    ρ: 2.0
    R: 1.02
    μ_Ψ: 0.04
    σ_Ψ: 0.15
    μ_θ: 0.0
    σ_θ: 0.1
    ρ_ζ: 0.0
```

## settings.yaml

Numerical settings for the port-with-shocks stages: grid sizes, bounds, and
simulation parameters. These values are referenced by the per-stage methods
files (`stages/*/*_stage_methods.yml`) through their settings symbol names.

### Numerical settings block

The `settings` block collects the numerical and solver knobs.

The state-space grids are defined as follows. The cash-on-hand grid `m` for
`cons_stage` uses `n_m` points between `m_min` and `m_max`. The assets grid
`a` for the `cons_stage` continuation uses `n_a` points between `a_min` and
`a_max`. The investable-assets grid `k` for `port_stage` and `noport_stage`
uses `n_k` points between `k_min` and `k_max`.

Expectations are evaluated by quadrature. The transitory income shock `θ`
uses `n_θ_nodes` nodes and the risky return shock `Ψ` uses `n_Ψ_nodes` nodes.
If the joint `(Ψ, θ)` quadrature is formed as a tensor product, it has
`n_joint_nodes` nodes, equal to the product of the two marginal node counts
(here seven by seven).

For simulation, `n_sim` sets the number of simulated paths and `sim_seed`
fixes the random seed. For the solver, `tol_vfi` is the value-function-
iteration tolerance and `max_iter` the maximum number of iterations.

```yaml
# Numerical settings block
settings:
  n_m: 100
  m_min: 0.01
  m_max: 200.0
  n_a: 100
  a_min: 0.0
  a_max: 200.0
  n_k: 200
  k_min: 0.01
  k_max: 200.0
  n_θ_nodes: 7
  n_Ψ_nodes: 7
  n_joint_nodes: 49
  n_sim: 10000
  sim_seed: 42
  tol_vfi: 1.0e-8
  max_iter: 1000
```

## cons_period.yaml

Period template of the first type, `cons_period`, which carries the state from
investable assets `k` through to terminal assets `a`. Within the period the
stages run in the order `noport` then `cons`.

The intra-period wiring is trivial: `noport` outputs `m` and `cons` expects
`m`, so the connector between them is the identity and may be omitted.

For the between-period link, the default is infinite-horizon recursion: the
next period's investable assets `k` are fed from this period's terminal assets
`a`, that is `k_{t+1} = a_t`, possibly with an explicit rename applied at the
assembly level.

### Period name

The `name` key identifies the period template.

### Stage sequence within the period

The `stages` list gives the within-period order in which the stages run.

```yaml
# Period name
name: cons_period

# Stage sequence within the period
stages:
  - noport_stage
  - cons_stage
```

## cons_port_period.yaml

Period template `cons_port_period`, which runs `cons` then `port`.

The intra-period wiring requires a rename: `cons` outputs `a` while `port`
expects `k`, so an internal connector maps `k = a`.

### Period name

The `name` key identifies the period template.

### Stage sequence within the period

The `stages` list gives the within-period order in which the stages run.

### Intra-period connector declarations

The `connectors` block declares the explicit wiring for period assembly. It is
optional: the current repository examples keep the connections implicit, and
this block documents the intended wiring. Here a single connector runs from
`cons_stage` to `port_stage`, renaming `a` to `k`.

```yaml
# Period name
name: cons_port_period

# Stage sequence within the period
stages:
  - cons_stage
  - port_stage

# Intra-period connector declarations
connectors:
  - {a: k}
```

## port_cons_period.yaml

Period template of the second type, `port_cons_period`, which carries the
state from investable assets `k` through to terminal assets `a`. Within the
period the stages run in the order `port` then `cons`.

The intra-period wiring is trivial: `port` outputs `m` and `cons` expects `m`,
so the connector between them is the identity and may be omitted.

For the between-period link, the default is infinite-horizon recursion: the
next period's investable assets `k` are fed from this period's terminal assets
`a`, that is `k_{t+1} = a_t`, possibly with an explicit rename applied at the
assembly level.

### Period name

The `name` key identifies the period template.

### Stage sequence within the period

The `stages` list gives the within-period order in which the stages run.

```yaml
# Period name
name: port_cons_period

# Stage sequence within the period
stages:
  - port_stage
  - cons_stage
```
