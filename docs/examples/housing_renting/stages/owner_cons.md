---
audience: user
type: example
topic: [applications]
---
# Stage 3: Owner Consumption

Continuous consumption via EGM.  The CES utility $u(c, H_{\text{nxt}})$ couples consumption and the (already chosen) housing stock.  The inverse Euler step requires numerical inversion for general CES; the solver handles this.

## Bellman calculus

Own path, $x_\prec = \{w_{\text{oc}}, H_{\text{nxt}}, y_o\}$, $x_\succ = \{b_o, H_{\text{nxt}}, y_o\}$.

$$
\mathrm{g}_{\sim\succ}: \quad b_o = w_{\text{oc}} - c
$$

$$
\mathbb{B}: \quad \mathrm{v}(w_{\text{oc}}, H_{\text{nxt}}, y_o) = \max_c\bigl\{u(c, H_{\text{nxt}}) + \beta\, \mathrm{v}_\succ(w_{\text{oc}} - c, H_{\text{nxt}}, y_o)\bigr\}
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec = \mathrm{v} \qquad\text{(identity)}
$$

Here `u_c` and `u_c_inv` are the marginal utility of consumption and its inverse, both depending on housing $H_{\text{nxt}}$ through the CES aggregator.  The borrowing constraint $b_o \geq 0$ is enforced via endogenous grid truncation in EGM.

## Stage YAML

```yaml
name: OwnerConsumptionChoice

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"
    XY: "@def {0, ..., n_y - 1}"

  prestate:
    w_oc: "@in Xa"        # cash after housing adjustment
    H_nxt: "@in XH"       # chosen housing
    y_o: "@in XY"

  states:
    w_oc: "@in Xa"
    H_nxt: "@in XH"
    y_o: "@in XY"

  poststates:
    b_o: "@in Xa"         # end-of-period assets (owner)
    H_nxt: "@in XH"       # housing (pass-through)
    y_o: "@in XY"         # income (pass-through)

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

  parameters: [beta, gamma, rho, theta, kappa, iota, n_H, H_min, H_max]

equations:
  arvl_to_dcsn_transition: |
    w_oc = w_oc[<]
    H_nxt = H_nxt[<]
    y_o = y_o[<]

  dcsn_to_cntn_transition: |
    b_o[>] = w_oc - c
    H_nxt[>] = H_nxt
    y_o[>] = y_o

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_c{u(c, H_nxt) + beta * V[>]}
    InvEuler: |
      c = u_c_inv(beta * dV[>], H_nxt)
    MarginalBellman: |
      dV = u_c(c, H_nxt)

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

## Methodization

EGM with FUES upper envelope.  The discrete housing grid creates non-concavities in the value function that FUES cleans.

```yaml
stage: OwnerConsumptionChoice

methods:
  - on: cntn_to_dcsn_builder
    schemes:
      - scheme: bellman_backward
        method: !egm

      - scheme: interpolation
        method: !Linear
        settings:
          grid: !Cartesian
          orders: [n_w]
          bounds: [ [w_min, w_max] ]

      - scheme: upper_envelope
        method: !FUES
        settings:
          m_bar: m_bar
```
