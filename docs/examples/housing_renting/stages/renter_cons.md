---
audience: user
type: example
topic: [applications]
---
# Stage 5: Renter Consumption

Same EGM structure as owner consumption, but utility uses rental services $S$ instead of owned housing.  The poststate $H_r = 0$ ensures renters arrive at the next period with no housing stock.

## Bellman calculus

Rent path, $x_\prec = \{w_{\text{rc}}, S, y_r\}$, $x_\succ = \{b_r, H_r, y_r\}$.

$$
\mathrm{g}_{\sim\succ}: \quad b_r = w_{\text{rc}} - c, \quad H_r = 0
$$

$$
\mathbb{B}: \quad \mathrm{v}(w_{\text{rc}}, S, y_r) = \max_c\bigl\{u(c, S) + \beta\, \mathrm{v}_\succ(w_{\text{rc}} - c, 0, y_r)\bigr\}
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec = \mathrm{v} \qquad\text{(identity)}
$$

## Stage YAML

```yaml
name: RenterConsumptionChoice

symbols:
  spaces:
    Xa: "@def R+"
    XS: "@def linspace(S_min, S_max, n_S)"
    XH: "@def linspace(H_min, H_max, n_H)"
    XY: "@def {0, ..., n_y - 1}"

  prestate:
    w_rc: "@in Xa"        # cash after rental payment
    S: "@in XS"           # rental services (already chosen)
    y_r: "@in XY"

  states:
    w_rc: "@in Xa"
    S: "@in XS"
    y_r: "@in XY"

  poststates:
    b_r: "@in Xa"         # end-of-period assets (renter)
    H_r: "@in XH"         # housing stock = 0 (renter carries no housing)
    y_r: "@in XY"

  controls:
    c: "@in R+"

  exogenous: {}

  values:
    V[>]: "@in [-inf, inf)"
    V[<]: "@in [-inf, inf)"
    V: "@in [-inf, inf)"

  values_marginal:
    dV[>]: "@in R+"
    dV: "@in R+"

  parameters: [beta, gamma, rho, theta, kappa, iota, n_S, S_min, S_max, n_H, H_min, H_max]

equations:
  arvl_to_dcsn_transition: |
    w_rc = w_rc[<]
    S = S[<]
    y_r = y_r[<]

  dcsn_to_cntn_transition: |
    b_r[>] = w_rc - c
    H_r[>] = 0
    y_r[>] = y_r

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_c{u(c, S) + beta * V[>]}
    InvEuler: |
      c = u_c_inv(beta * dV[>], S)
    MarginalBellman: |
      dV = u_c(c, S)

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

## Methodization

EGM with FUES upper envelope.  The discrete rental grid creates non-concavities analogous to the owner path.

```yaml
stage: RenterConsumptionChoice

methods:
  - on: cntn_to_dcsn_builder
    schemes:
      - scheme: bellman_backward
        method: !egm

      - scheme: interpolation
        method: !Linear
        settings:
          grid: !Cartesian
          orders: [n_w_rent]
          bounds: [ [w_rent_min, w_rent_max] ]

      - scheme: upper_envelope
        method: !FUES
        settings:
          m_bar: m_bar_rent
```
