---
audience: user
type: example
topic: [applications]
---
# Stage 1: Tenure Choice (Branching)

The agent observes the income shock, then chooses own or rent.  The backward builder takes $\max$ over branch continuation values; the arrival builder integrates over the Markov income process.

## Bellman calculus

Branching stage with $x_\prec = \{a, H, y_{\text{pre}}\}$, $x = \{a, H, y\}$.

$$
\mathrm{g}_{\prec\sim}: \quad a = a_\prec,\; H = H_\prec,\; y \sim \Pi(\cdot | y_{\text{pre},\prec})
$$

$$
\mathrm{g}_{\sim\succ}^{\text{own}}: \quad a_{o,\succ} = a,\; H_{o,\succ} = H,\; y_{o,\succ} = y
$$

$$
\mathrm{g}_{\sim\succ}^{\text{rent}}: \quad w_{r,\succ} = (1+r)a + z[y] + H,\; y_{r,\succ} = y
$$

$$
\mathbb{B}: \quad \mathrm{v}(a, H, y) = \max\bigl\{\mathrm{v}_{\succ}^{\text{own}}(a, H, y),\; \mathrm{v}_{\succ}^{\text{rent}}(w_r, y)\bigr\}
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec(a, H, y_{\text{pre}}) = \mathbb{E}_{y | y_{\text{pre}}}\bigl[\mathrm{v}(a, H, y)\bigr]
$$

## Stage YAML

The branch poststates are **disjoint** (`a_o, H_o, y_o` vs `w_r, y_r`) as required by spec 0.1l.  The rent branch folds income, assets, and housing liquidation into a single cash variable $w_r$.

```yaml
name: TenureChoice
kind: branching
branch_control: agent

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"
    XY: "@def {0, ..., n_y - 1}"

  prestate:
    a: "@in Xa"
    H: "@in XH"
    y_pre: "@in XY"

  exogenous:
    y:
      - "@in XY"
      - "@dist DiscreteMarkov(Pi, z_vals)"

  states:
    a: "@in Xa"
    H: "@in XH"
    y: "@in XY"

  poststates:
    own:
      a_o: "@in Xa"       # assets (pass-through to owner path)
      H_o: "@in XH"       # housing (pass-through to owner path)
      y_o: "@in XY"       # income index (pass-through)
    rent:
      w_r: "@in Xa"       # cash = (1+r)*a + z_vals[y] + H
      y_r: "@in XY"       # income index (pass-through)

  controls:
    d: "@in {own, rent}"

  values:
    V[<]: "@in [-inf, inf)"
    V: "@in [-inf, inf)"
    V_cntn:
      own: "@in [-inf, inf)"
      rent: "@in [-inf, inf)"

  parameters: [r, n_H, H_min, H_max, n_y, Pi, z_vals]

equations:
  arvl_to_dcsn_transition: |
    a = a[<]
    H = H[<]

  dcsn_to_cntn_transition:
    own: |
      a_o[>] = a
      H_o[>] = H
      y_o[>] = y
    rent: |
      w_r[>] = (1 + r) * a + z_vals[y] + H
      y_r[>] = y

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_d{V_cntn[>][own], V_cntn[>][rent]}

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = E_{y|y_pre}(V)
```

## Methodization

```yaml
stage: TenureChoice

methods:
  - on: cntn_to_dcsn_builder
    schemes:
      - scheme: branching_aggregator
        method: !max

  - on: dcsn_to_arvl_builder
    schemes:
      - scheme: expectation
        method: !DiscreteMarkov
```
