---
audience: user
type: example
topic: [applications]
---
# Periods and calibration

## 1 Connections within a period

The five stages have local field names. The intended connections pair each
branch's continuation fields with the arrival fields of its successor.
Equal names permit inference only when the compatible connection is unique
and creates no cycle; they do not identify variables throughout the period.
The two branches of `tenure_choice` share that stage's local names, so their
distinct outputs keep distinct names. See [Periods](../../Bellman-Sym/06-period.md).

The current declaration lists the stages by key:

```yaml
!period
name: housing_tenure
stages:
  - tenure_choice
  - owner_housing
  - owner_cons
  - renter_housing
  - renter_cons
connectors: []
```

| Intended connection | Continuation and arrival fields |
|---|---|
| `tenure_choice.own` → `owner_housing` | `(a_o, H_o, y_o)` match by name |
| `tenure_choice.rent` → `renter_housing` | `(w_r, y_r)` match by name |
| `owner_housing` → `owner_cons` | `(w_own, H_own, y_own)` match by name |
| `renter_housing` → `renter_cons` | `(w_rent, S_rent, y_rent)` match by name |

The application has no recipe supplying the stage records for these keys,
and its standalone stage files have unresolved construction refusals. This
page describes the intended composition; it is not a successfully loaded
trellis example. The calibration listing below is retained from the earlier
YAML model.

## 2 Connections between periods

Both consumption stages produce poststates that map to the next period's
arrival $(a, H, y_{\text{pre}})$. The renter stage writes zero housing itself;
the connector contains only pairs of fields. The period list counts back
from the terminal date: `periods[0]` is terminal, and `inter_connectors[h]`
connects `periods[h + 1]` to `periods[h]`.

```
periods[T-1] ──▶ ... ──▶ periods[1] ──▶ periods[0] (terminal)
```

```yaml
inter_connectors:
  - {a_nxt_o: a, H_nxt_o: H, y_nxt_o: y_pre, a_nxt_r: a, H_nxt_r: H, y_nxt_r: y_pre}
```

This is the mapping written in the application's trellis declaration. The
file currently contains only one period and one inter-period mapping; its
comment describes twenty periods, but the declaration does not repeat them.
It therefore does not yet encode a sequence of adjacent dates. The intended
mapping selects two separate routes into `tenure_choice`: the complete owner
tuple and the complete renter tuple, without combining coordinates from the
two alternatives. A bare endpoint is sufficient only when it names one eligible
field on its side of the adjacent period pair. If a stage is added with the
same eligible name, qualify the endpoint, for example `owner_cons.a_nxt_o`.
Once a complete period sequence is authored, a shared mapping is checked
separately for every adjacent pair; it does not bypass terminal differences.

## 3 Calibration

Following Fella (2014):

```yaml
calibration:
  # Preferences
  beta: 0.93           # discount factor
  gamma: 2.0           # CRRA risk aversion
  rho: 0.58            # CES elasticity (0 → Cobb-Douglas)
  theta: 0.77          # consumption weight
  kappa: 0.075         # housing service scale
  iota: 0.01           # housing service shift
  # Prices
  r: 0.06              # interest rate
  phi: 0.07            # housing transaction cost
  P_r: 0.1             # rental price per unit
  # Housing grid (defines XH — these are parameters, not settings)
  n_H: 7
  H_min: 0.0
  H_max: 5.0
  # Rental grid (defines XS)
  n_S: 7
  S_min: 0.0
  S_max: 5.0
  # Income process
  n_y: 48
  Pi: !include Pi_matrix.yaml
  z_vals: !include z_vals.yaml
  # Horizon
  T: 20

settings:
  # Asset grids (numerical approximation — settings, not parameters)
  n_w: 500             # owner cash-on-hand grid
  w_min: 1.0e-10
  w_max: 50.0
  n_w_rent: 500        # renter cash-on-hand grid
  w_rent_min: 1.0e-10
  w_rent_max: 50.0
  # FUES
  m_bar: 1.0           # jump detection threshold (owner)
  m_bar_rent: 1.0      # jump detection threshold (renter)
```

## 4 Economic operations

- **Five stages, two branches, CES utility.**  The branching stage (`tenure_choice`) fans out to owner and renter paths, each comprising a discrete housing choice followed by continuous consumption.
- **FUES on both consumption stages.**  The discrete housing/rental grid creates non-concavities in the value function; FUES cleans the upper envelope on both paths.  The CES inverse Euler requires numerical inversion.
- **Inter-period connections.** The renter consumption stage writes zero housing explicitly. Each complete continuation tuple is connected to the next period's arrival $(a, H, y_{\text{pre}})$; the connector makes no constant assignment.
