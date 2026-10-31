---
audience: user
type: example
topic: [applications]
---
# Stage 4: Renter Housing Choice

Discrete choice over rental services $S$ from a finite grid.  The constraint $P_r \cdot S \leq w_r$ ensures non-negative cash after rental payment.

## Bellman calculus

Rent path, $x_\prec = \{w_r, y_r\}$, $x_\succ = \{w_{\text{rc}}, S, y_r\}$.

$$
\mathrm{g}_{\sim\succ}: \quad w_{\text{rc}} = w_r - P_r\,S
$$

$$
\mathbb{B}: \quad \mathrm{v}(w_r, y_r) = \max_{S} \mathrm{v}_\succ(w_r - P_r S, S, y_r)
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec = \mathrm{v} \qquad\text{(identity)}
$$

## Stage YAML

```yaml
name: RenterHousingChoice

symbols:
  spaces:
    Xa: "@def R+"
    XS: "@def linspace(S_min, S_max, n_S)"
    XY: "@def {0, ..., n_y - 1}"

  prestate:
    w_r: "@in Xa"         # cash from tenure_choice rent branch
    y_r: "@in XY"

  states:
    w_r: "@in Xa"
    y_r: "@in XY"

  poststates:
    w_rc: "@in Xa"        # cash after rental payment
    S: "@in XS"           # chosen rental services
    y_r: "@in XY"

  controls:
    S_choice: "@in XS"

  exogenous: {}

  values:
    V[>]: "@in [-inf, inf)"
    V[<]: "@in [-inf, inf)"
    V: "@in [-inf, inf)"

  parameters: [P_r, n_S, S_min, S_max]

equations:
  arvl_to_dcsn_transition: |
    w_r = w_r[<]
    y_r = y_r[<]

  dcsn_to_cntn_transition: |
    w_rc[>] = w_r - P_r * S_choice
    S[>] = S_choice
    y_r[>] = y_r

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{S_choice}(V[>])

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

## Methodization

```yaml
stage: RenterHousingChoice

methods:
  - on: cntn_to_dcsn_builder
    schemes:
      - scheme: discrete_choice
        method: !max
```
