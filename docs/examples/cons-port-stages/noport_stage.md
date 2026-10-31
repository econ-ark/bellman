---
audience: user
type: example
topic: [applications]
---
# noport_stage
#no-port-cons
**Shock realization stage with no decision.**

This stage models the realization of an income shock without any choice by the agent. It's used as:

- A "no-portfolio" period (noport → cons)
- A bridge when converting from post-consumption assets `a` to cash-on-hand `m`

## Stage Structure

```
[ARRIVAL] ──g_ad──▶ [DECISION] ──g_de──▶ [CONTINUATION]
    k                   k_d        θ           m
```

- **Arrival state**: `k` (investable assets from previous period)
- **Decision state**: `k_d = k` (trivial, no choice)
- **Shock**: `θ ~ LogNormal(μ_θ, σ_θ)` realized after decision
- **Continuation state**: `m = k_d * R + θ` (cash-on-hand)

## YAML Specification

```yaml
name: noport_stage

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

equations:
  # Trivial transition (no shock between arrival and decision)
  arvl_to_dcsn_transition: |
    k_d = k

  # Shock realized after decision
  dcsn_to_cntn_transition: |
    m = k_d*R + θ

  # Backward builders
  cntn_to_dcsn_builder:
    Bellman: |
      V = E_{θ}(V[>])

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V

dolo_plus:
  dialect: adc-stage
  version: 0.1
  equation_symbols:
    arvl_to_dcsn_transition: g_ad
    dcsn_to_cntn_transition: g_de
    cntn_to_dcsn_builder: T_ed
    dcsn_to_arvl_builder: T_da
  slot_map:
    prestate: k
    poststate: m
```

## Key Features

1. **No decision**: The `cntn_to_dcsn_builder` is pure expectation (no `max` or `argmax`)
2. **Shock timing**: Income shock `θ` is realized *after* the trivial decision
3. **Slot map**: Defines how this stage connects to others (`k` in, `m` out)
