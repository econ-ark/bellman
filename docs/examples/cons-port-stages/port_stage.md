---
audience: user
type: example
topic: [applications]
---
# port_stage
#no-port-cons
**Portfolio allocation stage with post-decision correlated shocks.**

This stage implements portfolio choice where the agent allocates wealth between risky and risk-free assets *before* shocks are realized.

## Stage Overview

| Feature | Description |
|---------|-------------|
| **Prestate** | `k` (investable assets) |
| **Control** | `ς` (risky share ∈ [0,1]) |
| **Shocks** | Joint post-decision `(Ψ, θ)` |
| **Poststate** | `m` (cash-on-hand) |

## ADC Structure

```
[ARRIVAL] ───g_ad───▶ [DECISION] ───g_de───▶ [CONTINUATION]
    k                   k_d, ς       Ψ,θ           m
              identity          portfolio+shocks
```

- **Arrival → Decision**: Identity transition `k_d = k`
- **Decision → Continuation**: Portfolio return with shocks realized

## Economic Problem

The portfolio stage solves:
$$
V(k) = \max_{\varsigma} \mathbb{E}_{\Psi,\theta} \left[ V^{e}(m) \right]
$$

where cash-on-hand after portfolio choice and shock realization is:
$$
m = k \cdot (\varsigma \Psi + (1-\varsigma) R) + \theta
$$

- `ς` = risky share (fraction in risky asset)
- `Ψ` = risky return shock (log-normal)
- `θ` = transitory income shock (log-normal)
- `R` = risk-free gross return

## Stage YAML

```yaml
name: port_stage

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

  # Shocks realized after the portfolio decision (post-decision timing)
  exogenous:
    Ψ:
      - "@in Rp"
      - "@dist LogNormal(μ_Ψ, σ_Ψ)"
    θ:
      - "@in Θ"
      - "@dist LogNormal(μ_θ, σ_θ)"

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
    ρ_ζ: "@in [-1,1]"   # correlation parameter

equations:
  # No shocks between arrival and decision
  arvl_to_dcsn_transition: |
    k_d = k

  # Joint post-decision shocks realized in dcsn→cntn
  dcsn_to_cntn_transition: |
    m = k_d*(ς*Ψ + (1-ς)*R) + θ

  # Decision value: max-over-expectation (post-decision shocks)
  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{ς}(E_{Ψ,θ}(V[>]))
      ς = argmax_{ς}(E_{Ψ,θ}(V[>]))

  # No expectation at arrival (deterministic arvl→dcsn)
  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

## Key Features

### Post-Decision Shock Timing

Unlike the noport stage, the portfolio decision `ς` is made *before* shocks are realized. The shocks appear in the `dcsn_to_cntn_transition`, meaning:

1. Agent observes `k` at arrival
2. Agent chooses portfolio allocation `ς`
3. Shocks `(Ψ, θ)` are then realized
4. Cash-on-hand `m` is computed

### Max-over-Expectation Structure

The Bellman equation has the form:
```
V = max_{ς}(E_{Ψ,θ}(V[>]))
```

This is a max-over-expectation (rather than expectation-over-max), which is characteristic of portfolio problems where the decision must be made before uncertainty resolves.

### Joint Correlated Shocks

The shocks `Ψ` (risky return) and `θ` (income) can be correlated via the `ρ_ζ` parameter, allowing for realistic modeling of return-income correlations.

## Period Usage

This stage is used in:

- **port_cons_period**: `port → cons` (portfolio choice, then consumption)
- **cons_port_period**: `cons → port` (consumption first, then portfolio)

See [Port-with-Shocks](port_with_shocks.md) for composition details.
