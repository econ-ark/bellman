---
audience: user
type: example
topic: [applications]
---
# Port-with-Shocks Model

> [!note] Source
> The YAML stages of this page are the earlier form of the portfolio–consumption model, kept as recorded sources of its fixed reference under [`applications/cons-port/reference/legacy/syntax/`](https://github.com/econ-ark/bellman/tree/main/applications/cons-port/reference/legacy/syntax). The model's current stage files are the `.bl` files under `applications/cons-port/declaration/stages/`, written with the maximization alone, and its recipes and trellis files stand beside them in `applications/cons-port/declaration/` ([Model directory layout](../../Bellman-Sym/reference/model-directory-layout.md)).
> Earlier reference notebook: `applications/cons-port/notebooks/port-cons/solve_port_cons_ffp.ipynb`

**A modular lifecycle model with portfolio choice and correlated shocks.**

This example demonstrates how dolo-plus stages compose into different period configurations, showing the power of modular stage-based specification.

## Model Overview

| Feature | Description |
|---------|-------------|
| **Stages** | 3 reusable stages (noport, port, cons) |
| **Periods** | 3 configurations from same stage library |
| **Shocks** | Log-normal income and return shocks |
| **Solution** | EGM for consumption, grid search for portfolio |

## Core Idea

The port-with-shocks model separates three concerns:

1. **Shock realization** (`noport_stage`): Transforms assets to cash-on-hand via income shock
2. **Portfolio allocation** (`port_stage`): Allocates wealth before shocks resolve
3. **Consumption choice** (`cons_stage`): Optimizes consumption given cash-on-hand

By combining these stages differently, we get distinct economic models from the same building blocks.

## Stages

| Stage | Type | Decision | Prestate → Poststate |
|-------|------|----------|----------------------|
| `noport_stage` | Shock realization | None | `k → m` via `m = k*R + θ` |
| `port_stage` | Portfolio | `ς` (continuous) | `k → m` via `m = k*(ς*Ψ + (1-ς)*R) + θ` |
| `cons_stage` | Consumption | `c` (continuous) | `m → a` via `a = m - c` |

### noport_stage (Shock Realization)

No decision—just shock realization:

```
k ──[θ shock]──▶ m = k*R + θ
```

| Symbol | Role |
|--------|------|
| `k` | Investable assets (prestate) |
| `θ` | Transitory income shock |
| `m` | Cash-on-hand (poststate) |

### port_stage (Portfolio Choice)

Portfolio decision before joint shocks:

```
k ──[choose ς]──[Ψ,θ shocks]──▶ m = k*(ς*Ψ + (1-ς)*R) + θ
```

| Symbol | Role |
|--------|------|
| `k` | Investable assets (prestate) |
| `ς` | Risky share (control) |
| `Ψ, θ` | Return and income shocks |
| `m` | Cash-on-hand (poststate) |

### cons_stage (Consumption)

Deterministic consumption (EGM-compatible):

```
m ──[choose c]──▶ a = m - c
```

| Symbol | Role |
|--------|------|
| `m` | Cash-on-hand (prestate) |
| `c` | Consumption (control) |
| `a` | End-of-period assets (poststate) |

## Period Configurations

The library defines three period YAML files, each composing stages in a different order.

### Period 1: `cons_period` (noport → cons)

**File**: `cons_period.yaml`

```yaml
name: cons_period

stages:
  - noport_stage
  - cons_stage
```

**Flow**: `k ──[θ shock]──▶ m ──[choose c]──▶ a`

- No portfolio decision; income shock is realized via `noport_stage`
- `noport_stage` outputs `m`, `cons_stage` expects `m` — **implicit identity connector** (no connector needed)
- Between-period link: `k_{t+1} = a_t` (rename at trellis/assembly level)

This is the simplest consumption-savings model with exogenous income risk.

### Period 2: `port_cons_period` (port → cons)

**File**: `port_cons_period.yaml`

```yaml
name: port_cons_period

stages:
  - port_stage
  - cons_stage
```

**Flow**: `k ──[choose ς, then Ψ,θ shocks]──▶ m ──[choose c]──▶ a`

- Portfolio allocation is made first, then joint return and income shocks are realized
- `port_stage` outputs `m`, `cons_stage` expects `m` — **implicit identity connector**
- Between-period link: `k_{t+1} = a_t`

This is the standard lifecycle portfolio-consumption model (e.g. Cocco, Gomes, Maenhout 2005).

### Period 3: `cons_port_period` (cons → port)

**File**: `cons_port_period.yaml`

```yaml
name: cons_port_period

stages:
  - cons_stage
  - port_stage

connectors:
  - from: cons_stage
    to: port_stage
    rename: {a: k}
```

**Flow**: `m ──[choose c]──▶ a = k ──[choose ς, then Ψ,θ shocks]──▶ m'`

- Consumption is chosen first, then remaining assets are allocated across portfolio
- `cons_stage` outputs `a` but `port_stage` expects `k` — **explicit rename connector** `{a: k}` is required
- Between-period link: `m_{t+1} = m'_t` (identity, since port outputs `m` and cons expects `m`)

This reversal illustrates the key composition feature: the **same stages** produce a different economic model simply by changing the order and adding a connector.

## Connectors and Inter-period Connectors

The three period files show how modular stage composition works in practice:

| Period | Stages | Connector | Between-period rename |
|--------|--------|-----------|-----------------------|
| `cons_period` | noport → cons | identity (omitted) | `a → k` |
| `port_cons_period` | port → cons | identity (omitted) | `a → k` |
| `cons_port_period` | cons → port | `{a: k}` (explicit) | `m → m` (identity) |

**Key observation**: When stage output names match the next stage's input (`m → m`), the connector is identity and is omitted. When they differ (`a → k`), an explicit connector provides the rename. This is the **inter-period connector condition** from the DDSL foundations.

## Trellis Construction

A trellis composes periods across time with **inter-period connectors**. For example, an infinite-horizon `cons_period` trellis:

```yaml
periods:
  - cons_period       # noport → cons, outputs a

inter_connectors:
  - rename: {a: k}    # between-period: a_t → k_{t+1}
```

For `cons_port_period`, the inter-period connector would be identity since the period already outputs `m` and expects `m` at arrival.

## Stage Composition Diagram

```
                      ┌─────────────────────────────────────────┐
                      │           STAGE LIBRARY                 │
                      ├─────────────┬─────────────┬─────────────┤
                      │  noport     │    port     │    cons     │
                      │  k ──▶ m    │  k ──▶ m    │  m ──▶ a    │
                      │   (θ)       │  (ς,Ψ,θ)    │   (c)       │
                      └──────┬──────┴──────┬──────┴──────┬──────┘
                             │             │             │
              ┌──────────────┼─────────────┼─────────────┼──────────────┐
              ▼              ▼             ▼             ▼              ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐
     │ cons_period │  │port_cons_   │  │    cons_port_period     │
     │             │  │   period    │  │                         │
     │ noport─cons │  │ port─cons   │  │ cons ─{a→k}─ port       │
     │  k───▶a     │  │  k───▶a     │  │      m───▶m'            │
     └─────────────┘  └─────────────┘  └─────────────────────────┘
```

## Key Concepts Illustrated

### Post-Decision Shock Timing

In `port_stage`, the portfolio decision `ς` is made *before* shocks `(Ψ, θ)` resolve. This is expressed by:

1. Shocks in `exogenous` block (not in `arvl_to_dcsn_transition`)
2. Bellman: `V = max_{ς}(E_{Ψ,θ}(V[>]))`

### EGM Compatibility

The `cons_stage` is designed for EGM solution:

- Contains `InvEuler` equation: `c[>] = (β*dV[>])^(-1/ρ)`
- Contains reverse transition: `m_d[>] = a + c[>]`
- No shocks within the stage (expectation handled by preceding stage)

## Files

The YAML files of this page stand, as recorded sources of the fixed reference, under `applications/cons-port/reference/legacy/syntax/`:

```
applications/cons-port/reference/legacy/syntax/
├── stages/
│   ├── noport/
│   │   ├── noport_stage.yaml         # Shock realization stage
│   │   └── noport_stage_methods.yml  # noport methods
│   ├── port/
│   │   ├── port_stage.yaml           # Portfolio stage
│   │   └── port_stage_methods.yml    # port methods (VFI)
│   └── cons/
│       ├── cons_stage.yaml           # Consumption stage
│       └── cons_stage_methods.yml    # cons methods (EGM)
├── cons_period.yaml          # noport → cons
├── port_cons_period.yaml     # port → cons
├── cons_port_period.yaml     # cons → port
├── calibration.yaml          # Parameter values
└── settings.yaml             # Grid configuration
```

Today the language reads the application's recipes, trellis files, calibration and settings files under `applications/cons-port/declaration/`, and its `.bl` stage files under `applications/cons-port/declaration/stages/`, each with its methods files beside it, `methods.bl` and the replacing selections `methods.<variant>.bl`, which are additions to the stage file.

## Related Documentation

- **Stage Details**: [noport_stage](noport_stage.md) | [port_stage](port_stage.md) | [cons_stage](cons_stage.md)
- **Theory**: [Solving via conjugation](solving-conjugates.md)
