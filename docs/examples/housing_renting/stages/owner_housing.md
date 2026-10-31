---
audience: user
type: example
topic: [applications]
---
# Stage 2: Owner Housing Choice

Discrete choice over housing stock with transaction costs.  Cash-on-hand $w_{\text{oc}}$ is computed after the housing adjustment.

## Bellman calculus

Own path, $x_\prec = \{a_o, H_o, y_o\}$, $x_\succ = \{w_{\text{oc}}, H_{\text{nxt}}, y_o\}$.

$$
\mathrm{g}_{\prec\sim}: \quad \text{identity}
$$

$$
\mathrm{g}_{\sim\succ}: \quad w_{\text{oc}} = (1+r)\,a_o + z[y_o] + H_o - (1 + \phi\,\mathbf{1}[H' \neq H_o])\,H', \quad H_{\text{nxt}} = H'
$$

$$
\mathbb{B}: \quad \mathrm{v}(a_o, H_o, y_o) = \max_{H'} \mathrm{v}_\succ(w_{\text{oc}}, H', y_o)
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec = \mathrm{v} \qquad\text{(identity)}
$$

When $H' = H_o$ (keep), the housing terms cancel: $w_{\text{oc}} = (1+r)a_o + z[y_o]$.  When $H' \neq H_o$ (adjust), the transaction cost $\phi$ applies to the purchase price.

## Stage YAML

```yaml
name: OwnerHousingChoice

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"
    XY: "@def {0, ..., n_y - 1}"

  prestate:
    a_o: "@in Xa"         # from tenure_choice own branch
    H_o: "@in XH"
    y_o: "@in XY"

  states:
    a_o: "@in Xa"
    H_o: "@in XH"
    y_o: "@in XY"

  poststates:
    w_oc: "@in Xa"        # cash after housing adjustment
    H_nxt: "@in XH"       # chosen housing
    y_o: "@in XY"

  controls:
    H_choice: "@in XH"

  exogenous: {}

  values:
    V[>]: "@in [-inf, inf)"
    V[<]: "@in [-inf, inf)"
    V: "@in [-inf, inf)"

  parameters: [r, phi, n_H, H_min, H_max, n_y, z_vals]

equations:
  arvl_to_dcsn_transition: |
    a_o = a_o[<]
    H_o = H_o[<]
    y_o = y_o[<]

  dcsn_to_cntn_transition: |
    w_oc[>] = (1 + r) * a_o + z_vals[y_o] + H_o - (1 + phi * (H_choice != H_o)) * H_choice
    H_nxt[>] = H_choice
    y_o[>] = y_o

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{H_choice}(V[>])

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

## Methodization

```yaml
stage: OwnerHousingChoice

methods:
  - on: cntn_to_dcsn_builder
    schemes:
      - scheme: discrete_choice
        method: !max
```
