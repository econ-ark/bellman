---
audience: user
type: example
topic: [applications]
---
# cons_stage
#no-port-cons
**Deterministic consumption stage (EGM-compatible).**

This stage models the consumption choice given cash-on-hand. It's designed to be compatible with the Endogenous Grid Method (EGM).

## Stage Structure

```
[ARRIVAL] ──g_ad──▶ [DECISION] ──g_de──▶ [CONTINUATION]
    m                   m_d       c           a
```

- **Arrival state**: `m` (cash-on-hand from noport/port stage)
- **Decision state**: `m_d = m` (trivial transition)
- **Control**: `c ∈ (0, m)` (consumption)
- **Continuation state**: `a = m_d - c` (post-consumption assets)

## YAML Specification

```yaml
name: cons_stage

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

equations:
  # Trivial arrival-to-decision
  arvl_to_dcsn_transition: |
    m_d = m

  # Budget constraint
  dcsn_to_cntn_transition: |
    a = m_d - c

  # Backward builders (multiple sub-equations for EGM)
  cntn_to_dcsn_builder:
    Bellman: |
      u = (c^(1-ρ))/(1-ρ)
      V = max_{c}(u + β*V[>])
      c = argmax_{c}((c^(1-ρ))/(1-ρ) + β*V[>])
    InvEuler: |
      c[>] = (β*dV[>])^(-1/ρ)
    MarginalBellman: |
      dV = (c)^(-ρ)
    cntn_to_dcsn_transition: |
      m_d[>] = a + c[>]

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
    ShadowBellman: |
      dV[<] = dV

dolo_plus:
  dialect: adc-stage
  version: 0.1
  equation_symbols:
    arvl_to_dcsn_transition: g_ad
    dcsn_to_cntn_transition: g_de
    cntn_to_dcsn_builder: T_ed
    dcsn_to_arvl_builder: T_da
  builder_sub_equations:
    T_ed:
      Bellman: T_ed_Bellman
      InvEuler: T_ed_InvEuler
      MarginalBellman: T_ed_MarginalBellman
      cntn_to_dcsn_transition: g_ed
    T_da:
      Bellman: T_da_Bellman
      ShadowBellman: T_da_ShadowBellman
  slot_map:
    prestate: m
    poststate: a
```

## Key Features

### EGM Sub-Equations

The `cntn_to_dcsn_builder` contains multiple sub-equations for EGM:

| Sub-equation | Purpose |
|--------------|---------|
| `Bellman` | Standard value function recursion |
| `InvEuler` | Inverse Euler equation: `c = (β * dV)^(-1/ρ)` |
| `MarginalBellman` | Envelope condition: `dV = u'(c)` |
| `cntn_to_dcsn_transition` | Reverse state: `m = a + c` |

### Marginal Values

The `values_marginal` group declares shadow values `dV` (with perch tags) used by EGM. These represent marginal utility of wealth at each perch.

### Slot Map

- Input: `m` (cash-on-hand)
- Output: `a` (post-consumption assets)
