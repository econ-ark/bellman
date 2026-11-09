---
audience: user
type: example
topic: [applications]
---
# Consumption-Savings with IID Shocks

> [!note] Source
> Application folder: [`applications/consumption-savings-iid/`](../../../applications/consumption-savings-iid), which holds the model's stage file, `declaration/stages/cons_savings_iid/cons_savings_iid.bl`, in the layout of [Model directory layout](../../Bellman-Sym/reference/model-directory-layout.md). The YAML files shown on this page are the model's earlier dolo-plus form, which is no longer in the repository.

**A single-stage lifecycle model solved via EGM.**

This example demonstrates the simplest complete dolo-plus model: a single stage containing both expectation and maximization, designed for solution via the Endogenous Grid Method (EGM).

## Model Overview

| Feature | Description |
|---------|-------------|
| **Stages** | 1 (self-contained stage with both expectation and maximization) |
| **Shocks** | IID log-normal income shock |
| **Solution** | Endogenous Grid Method (EGM) |
| **State** | Wealth `w` (cash-on-hand) |

## Economic Problem

The agent solves:
$$
V(b) = \mathbb{E}_y \left[ \max_c \left\{ u(c) + \beta V(a) \right\} \right]
$$

where:
- `b` = beginning-of-period assets (prestate)
- `y` = income shock (exogenous)
- `w = exp(y) + b*r` = cash-on-hand (state after shock)
- `c` = consumption (control)
- `a = w - c` = end-of-period assets (poststate)

## ADC Stage Structure

```
[ARRIVAL] ───g_ad───▶ [DECISION] ───g_de───▶ [CONTINUATION]
    b          y           w        c            a
              shock       choice
```

- **Arrival → Decision**: Income shock realized, `w = exp(y) + b*r`
- **Decision → Continuation**: Consumption choice, `a = w - c`

## Files

The application folder holds the stage file and its note in the stage's folder, the methods file and the two block files it binds under `declaration/methods/`, the settings file under `declaration/settings/`, and the structural test:

| File | Purpose |
|------|---------|
| `declaration/stages/cons_savings_iid/cons_savings_iid.bl` | The stage file: declarations, the values and the maximization |
| `declaration/stages/cons_savings_iid/cons_savings_iid.md` | The stage's note, which explains the stage file and the two block files |
| `declaration/methods/cons_savings_iid.yml` | The methods file: the endogenous grid method on the policy builder and the marginal blocks on the two value builders |
| `declaration/methods/cons_savings_iid_egm.bl` | The method block of the policy builder: the inverse Euler line, the endogenous grid and the identification of the policy |
| `declaration/methods/marginals.bl` | The marginal blocks: the derivatives of the decision value and the arrival value |
| `declaration/settings/cons_savings_iid.yml` | The settings file: the exogenous grid of savings of the endogenous grid method, `n_a`, `a_min` and `a_max` |
| `tests/test_cons_savings_iid_ast.py` | The structural test, which parses the stage file and compares its terms with terms written by hand |

The earlier dolo-plus form, from which the listings below are taken, kept the model in four YAML files:

| File | Purpose |
|------|---------|
| `stage.yaml` | Stage syntax (symbols, equations) |
| `calibration.yaml` | Parameter values |
| `settings.yaml` | Grid sizes, bounds |
| `methodization.yml` | Solution scheme (EGM recipe) |

## Stage YAML

```yaml
name: consumption_savings_iid_egm_doloplus

symbols:
  spaces:
    Xb: "@def R+"     # prestate assets
    Xw: "@def R+"     # cash-on-hand
    Xa: "@def R+"     # end-of-period assets
    Y:  "@def R"      # income support

  prestate:
    b: "@in Xb"
  exogenous:
    y:
      - "@in Y"
      - "@dist Normal(μ_y, σ_y)"
  states:
    w: "@in Xw"
  poststates:
    a: "@in Xa"
  controls:
    c: "@in R+"

  values:
    V: "@in R"
  values_marginal:
    dV: "@in R+"

  parameters:
    β: "@in (0,1)"
    γ: "@in R+"
    r: "@in R++"
    μ_y: "@in R"
    σ_y: "@in R+"

equations:
  # Half-transition: shock realization
  arvl_to_dcsn_transition: |
    w = exp(y) + b*r

  # Budget constraint
  dcsn_to_cntn_transition: |
    a = w - c

  # Reverse state for EGM
  cntn_to_dcsn_transition: |
    w = a + c

  # Backward builder with EGM sub-equations
  cntn_to_dcsn_opr:
    Bellman: |
      V = max_{c}((c^(1-γ))/(1-γ) + β*V[>])
    InvEuler: |
      c[>] = (β*dV[>])^(-1/γ)
    MarginalBellman: |
      dV = (c)^(-γ)

  # Expectation operator
  dcsn_to_arvl_opr:
    Bellman: |
      V[<] = E_{y}(V)
    MarginalBellman: |
      dV[<] = r * E_{y}(dV)
```

## Key Features

### Single Stage with Both Operators

Unlike the port-with-shocks model (which separates expectation and maximization), this model contains both in one stage:
- `dcsn_to_arvl_opr`: Expectation over income shock
- `cntn_to_dcsn_opr`: Maximization via EGM

### EGM Sub-Equations

The `cntn_to_dcsn_opr` block contains:
1. `InvEuler`: Compute consumption from marginal value
2. `MarginalBellman`: Envelope condition for marginal value
3. `cntn_to_dcsn_transition`: Reverse mapping `w = a + c`

### Marginal Value Propagation

The `MarginalBellman` in `dcsn_to_arvl_opr`:
```yaml
dV[<] = r * E_{y}(dV)
```
propagates the expected marginal value, accounting for the return `r`.
