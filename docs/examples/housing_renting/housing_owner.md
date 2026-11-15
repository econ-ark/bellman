---
audience: user
type: example
topic: [applications]
---
# Housing model

> [!note] Source
> Application folder: [`applications/housing-owner/`](https://github.com/econ-ark/bellman/tree/main/applications/housing-owner), which holds the model's two stage files, `declaration/stages/housing_choice/housing_choice.bl` and `declaration/stages/consumption_choice/consumption_choice.bl`, each with its methods file `methods.bl` beside it, an addition to the stage file that the package reads with it, in the layout of [Model directory layout](../../Bellman-Sym/reference/model-directory-layout.md). The YAML files shown on this page are the model's earlier dolo-plus form, which is no longer in the repository.

**Sequential composition and branching in a housing tenure-choice model.**

This example demonstrates two compositions:

1. **Owner-only period** (sequential): a discrete housing adjustment followed by continuous consumption, with connections between their stage-local fields.
2. **Tenure-choice period** (branching): a branching stage fans out to owner and renter paths, each with its own housing and consumption stages.

## 1 Model overview

| Feature | Description |
|---------|-------------|
| **Stages** | 2 (housing_choice → consumption_choice) |
| **Period** | HousingOwnerPeriod |
| **Shocks** | Markov income process |
| **Solution** | Discrete choice + EGM with upper envelope (FUES-style) |

## 2 Economic problem

The agent solves a two-stage problem each period:

**Stage 1 (Housing Choice):**
$$
V^H(a, H, y) = \mathbb{E}_{y'|y} \left[ \max_{H'} V^C(w, H', y') \right]
$$

**Stage 2 (Consumption Choice):**
$$
V^C(w, H', y) = \max_c \left\{ u(c, H') + \beta V^H(a', H', y) \right\}
$$

where:
- `a` = beginning-of-period assets
- `H` = current housing stock
- `y` = income state (Markov)
- `H'` = chosen housing (discrete)
- `w` = cash-on-hand after housing adjustment
- `c` = consumption
- `a'` = end-of-period assets

## 3 Period structure

```
┌──────────────── PERIOD ────────────────┐
│                                        │
│  [housing_choice] ──▶ [consumption_choice]
│       │                      │         │
│   discrete H'            EGM for c     │
│                                        │
└────────────────────────────────────────┘
```

### 3.1 State spaces and transitions

```
(b, H, y_pre) ──shock y──▶ (w, H, y) ──g: H'──▶ (w, H_nxt, y) ──g: c──▶ (a_nxt, H_nxt, y)
   arvl             dcsn             cntn / dcsn             cntn
        housing_choice                    consumption_choice
```

- $(b, H, y_\text{pre}) \xrightarrow{y} (w, H, y)$: income shock realized, $w = (1+r)b + z[y]$
- $(w, H, y) \xrightarrow{H'} (w, H_\text{nxt}, y)$: housing adjustment, $w \mapsto w + H - (1+\phi\cdot\mathbb{1})H'$
- $(w, H_\text{nxt}, y) \xrightarrow{c} (a_\text{nxt}, H_\text{nxt}, y)$: consumption, $a_\text{nxt} = w - c$

## 4 Files

The application folder holds each stage file with its methods file and its note in the stage's folder, the settings file of the consumption stage's exogenous grid of savings, a note that cites the paper the model follows and the structural tests. The methods file of the consumption stage types the policy builder with the endogenous grid method and its grid of savings and writes the method's lines; the methods file of the housing stage appends the derivative lines of its two values and types no method:

```
applications/housing-owner/
├── README.md
├── declaration/
│   ├── settings/                  housing-owner.yml
│   └── stages/
│       ├── housing_choice/        housing_choice.bl  methods.bl  housing_choice.md
│       └── consumption_choice/    consumption_choice.bl  methods.bl  consumption_choice.md
├── reference/                     README.md
└── tests/                         test_housing_choice_ast.py  test_consumption_choice_ast.py
```

The listings below are taken from the earlier dolo-plus folder, which held the model in YAML files:

```
housing_owner_only_doloplus/
├── period.yaml              # Period definition (stage list)
├── calibration.yaml         # Parameter values
├── settings.yaml            # Grid sizes, bounds
└── stages/
    ├── housing_choice.yaml          # Stage 1 syntax
    ├── housing_choice_methods.yml   # Stage 1 solution scheme
    ├── consumption_choice.yaml      # Stage 2 syntax
    └── consumption_choice_methods.yml   # Stage 2 solution scheme
```

## 5 Period declaration

```yaml
name: HousingOwnerPeriod

stages:
  - housing_choice
  - consumption_choice

# Connections are implicit via common namespace
```

## 6 Housing choice

Discrete choice over housing stock with transaction costs. The housing grid `XH` is defined as part of the mathematical model via `@def linspace(H_min, H_max, n_H)`.

```yaml
name: OwnerHousingChoice

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"  # discrete housing grid
    Xw: "@def R+"
    Y:  "@def Z+"

  prestate:
    b: "@in Xa"         # beginning assets
    H: "@in XH"         # current housing
    y_pre: "@in Y"      # previous income index

  exogenous:
    y:
      - "@in Y"
      - "@dist DiscreteMarkov(Pi, z_vals)"

  states:
    w: "@in Xa"         # cash-on-hand
    H: "@in XH"
    y: "@in Y"

  poststates:
    w: "@in Xw"         # cash after housing adjustment
    H_nxt: "@in XH"     # chosen housing
    y: "@in Y"

  controls:
    H_choice: "@in XH"  # discrete housing choice

  parameters:
    r: "@in R+"
    phi: "@in R+"
    n_H: "@in Z+"       # housing grid points (defines XH)
    H_min: "@in R+"     # housing grid lower bound (defines XH)
    H_max: "@in R+"     # housing grid upper bound (defines XH)

equations:
  # Income shock realized
  arvl_to_dcsn_transition: |
    w = (1 + r)*b[<] + z_vals[y]

  # Housing adjustment with transaction cost
  dcsn_to_cntn_transition: |
    w[>] = w + H - (1 + phi*(H_choice != H))*H_choice
    H_nxt[>] = H_choice

  # Discrete max over housing
  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{H_choice}(V[>])

  # Markov expectation
  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = E_{y|y_pre}(V)
```

## 7 Consumption choice

Continuous consumption via EGM, given housing already chosen. The housing grid `XH` is again declared as `linspace(...)` since it defines the domain of the `H_nxt` state carried through this stage.

```yaml
name: OwnerConsumptionChoice

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"
    Xw: "@def R+"
    Y:  "@def Z+"

  prestate:
    w: "@in Xw"         # cash-on-hand (from housing stage)
    H_nxt: "@in XH"     # housing (already chosen)
    y: "@in Y"

  exogenous: {}         # No shock in this stage

  poststates:
    a_nxt: "@in Xa"     # end-of-period assets
    H_nxt: "@in XH"
    y: "@in Y"

  controls:
    c: "@in R+"

  parameters:
    beta: "@in (0,1)"
    gamma: "@in R+"
    theta: "@in (0,1)"
    kappa: "@in R+"
    iota: "@in R+"
    n_H: "@in Z+"       # housing grid points (defines XH)
    H_min: "@in R+"     # housing grid lower bound (defines XH)
    H_max: "@in R+"     # housing grid upper bound (defines XH)

equations:
  dcsn_to_cntn_transition: |
    a_nxt = w - c

  cntn_to_dcsn_transition: |
    w_dcsn[>] = a_nxt + c_fn[>]

  cntn_to_dcsn_builder:
    # Cobb-Douglas utility in (c, H)
    Bellman: |
      V = max_{c}(u(c, H_nxt) + β*V[>])
    InvEuler: |
      c_fn[>] = (β*dV[>] / (θ * (κ*H_nxt + ι)^(...)))^(-1/...)
    ShadowBellman: |
      dV[>] = θ * c^(...) * (κ*H_nxt + ι)^(...)
```

## 8 Economic operations

### 8.1 Stage composition

The historical example intends these connections between two stages:
- Stage 1 outputs `(w, H_nxt, y)`
- Stage 2 inputs `(w, H_nxt, y)`
- An equal name permits inference only when the compatible connection is unique and introduces no cycle. An authored connector is needed otherwise; see [Periods](../../Bellman-Sym/06-period.md).

### 8.2 Discrete and continuous choices

- **Stage 1**: Discrete choice over finite housing grid
- **Stage 2**: Continuous consumption via EGM

### 8.3 Markov shocks

Income follows a Markov chain:
```yaml
y:
  - "@in Y"
  - "@dist DiscreteMarkov(Pi, z_vals)"
```

The expectation in Stage 1 conditions on previous income:
```yaml
V[<] = E_{y|y_pre}(V)
```

### 8.4 FUES upper envelope

Stage 2 uses FUES-style upper envelope to handle non-convexities from the discrete housing choice. The `ue_kwargs` setting configures the envelope algorithm.

## 9 A period with tenure choice

The owner-only model above assumes the agent always owns. A more general model introduces a **tenure choice**: each period the agent decides whether to **own** or **rent** housing. This is a branching composition — the two paths have different state spaces and different downstream stages.

> [!note] Branching syntax
> See [[branch]] for what a branching stage is and how its branches are
> valued.

### 9.1 Period structure

```
┌──────────────────── PERIOD ────────────────────────┐
│                                                    │
│                  ┌─ [owner_housing] ─▶ [owner_cons]│
│  [tenure_choice] ┤                                 │
│                  └─ [renter_housing] ▶ [renter_cons]│
│                                                    │
└────────────────────────────────────────────────────┘
```

The branching stage (`tenure_choice`) fans out to two paths. Each path has its own housing and consumption stages. The backward solve order is: `owner_cons` → `renter_cons` → `owner_housing` → `renter_housing` → `tenure_choice`.

### 9.2 State spaces and transitions

```
                                    ┌─own──▶ (w_own, H, y) ──H'──▶ (w_oc, H_nxt, y) ──c──▶ (a_nxt, H_nxt, y)
(b, H, y_pre) ──shock y──▶ (a, H, y)┤
                                    └─rent─▶ (w_rent, y) ────h'──▶ (w_rc, h, y) ──────c──▶ (a_nxt, y)
```

- $(b, H, y_\text{pre}) \xrightarrow{y} (a, H, y)$: income shock, $a = (1+r)b + z[y]$
- **Own branch**: $(a, H, y) \xrightarrow{\text{own}} (w_\text{own}, H, y)$: $w_\text{own} = a + H$
  - $(w_\text{own}, H, y) \xrightarrow{H'} (w_\text{oc}, H_\text{nxt}, y)$: housing adjustment
  - $(w_\text{oc}, H_\text{nxt}, y) \xrightarrow{c} (a_\text{nxt}, H_\text{nxt}, y)$: consumption
- **Rent branch**: $(a, H, y) \xrightarrow{\text{rent}} (w_\text{rent}, y)$: $w_\text{rent} = (1+r)a + H$
  - $(w_\text{rent}, y) \xrightarrow{h'} (w_\text{rc}, h, y)$: rent housing, $w_\text{rc} = w_\text{rent} - p \cdot h'$
  - $(w_\text{rc}, h, y) \xrightarrow{c} (a_\text{nxt}, y)$: consumption

The intermediate cash-on-hand fields have distinct names (`w_own`, `w_oc`, `w_rent`, `w_rc`) in this historical example. Current stage files may reuse a local name across stages; a connection selects the particular writing and reading occurrences.

### 9.3 Tenure choice

The tenure-choice stage declares two continuation branches (`own` and `rent`) with different state spaces. The backward builder combines the two branch values via `max_d{…}`. Both branches belong to the same stage, so different quantities need different local names, such as `w_own` and `w_rent`. This is a stage rule; it does not make field names unique throughout the period.

```yaml
name: TenureChoice

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"
    XY: "@def {1, ..., n_y}"
  prestate:
    b: "@in Xa"
    H: "@in XH"
    y_pre: "@in XY"
  states:
    a: "@in Xa"
    H: "@in XH"
    y: "@in XY"
  poststates:
    own:
      w_own: "@in Xa"     # cash-on-hand for owner path
      H: "@in XH"
      y: "@in XY"
    rent:
      w_rent: "@in Xa"    # cash-on-hand after liquidating housing
      y: "@in XY"
  controls:
    d: "@in {own, rent}"   # discrete branch selector
  exogenous:
    y:
      - "@in XY"
      - "@dist MarkovChain(Pi, z_vals)"
  values:
    V[<]: "@in R"
    V: "@in R"
    V_cntn:
      own: "@in R"         # continuation value from owner path
      rent: "@in R"        # continuation value from renter path
  parameters: [r, phi, H_min, H_max, n_H, n_y]

equations:
  arvl_to_dcsn_transition: |
    a = (1 + r)*b[<] + z_vals[y]
    H = H[<]
    y = y_shock

  dcsn_to_cntn_transition:
    own: |
      w_own[>] = a + H
      H[>] = H
      y[>] = y
    rent: |
      w_rent[>] = (1+r)*a + H
      y[>] = y

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_d{V_cntn[>][own], V_cntn[>][rent]}

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = E_y(V)
```

Key points:

- `poststates` is **branch-keyed** in this historical YAML: `own` has fields `(w_own, H, y)`, `rent` has fields `(w_rent, y)`. In current stage files, branch-specific quantities have distinct names within the stage; equal spelling in another stage identifies a separate field.
- `dcsn_to_cntn_transition` is also branch-keyed: the `own` branch computes owner cash-on-hand `w_own = a + H`; the `rent` branch liquidates housing `w_rent = (1+r)*a + H`.
- `V_cntn` is declared as a **branch-indexed family** with keys matching the `poststates` keys.
- The Bellman equation uses `max_d{…}` over the branch continuation values.

### 9.4 The owner's choices

The owner path receives `(w_own, H, y)` from the `own` continuation perch. Note the variable naming differs from the owner-only model above (which uses `w` generically) — in the branching context, `w_own` ensures uniqueness.

**Owner Housing Stage** (discrete $H'$ choice):

```yaml
name: OwnerHousingChoice

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"
    XY: "@def {1, ..., n_y}"

  prestate:
    w_own: "@in Xa"       # cash-on-hand (from tenure-choice own branch)
    H: "@in XH"
    y: "@in XY"

  states:
    w_own: "@in Xa"
    H: "@in XH"
    y: "@in XY"

  poststates:
    w_oc: "@in Xa"        # cash after housing adjustment → owner consumption
    H_nxt: "@in XH"
    y: "@in XY"

  controls:
    H_choice: "@in XH"

  parameters:
    phi: "@in R+"
    n_H: "@in Z+"
    H_min: "@in R+"
    H_max: "@in R+"

equations:
  arvl_to_dcsn_transition: |
    w_own = w_own[<]
    H = H[<]
    y = y[<]

  dcsn_to_cntn_transition: |
    w_oc[>] = w_own + H - (1 + phi*(H_choice != H))*H_choice
    H_nxt[>] = H_choice
    y[>] = y

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{H_choice}(V[>])

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

**Owner Consumption Stage** (EGM):

```yaml
name: OwnerConsumptionChoice

symbols:
  spaces:
    Xa: "@def R+"
    XH: "@def linspace(H_min, H_max, n_H)"
    XY: "@def {1, ..., n_y}"

  prestate:
    w_oc: "@in Xa"        # cash after housing adj. (from owner housing)
    H_nxt: "@in XH"
    y: "@in XY"

  poststates:
    a_nxt: "@in Xa"
    H_nxt: "@in XH"
    y: "@in XY"

  controls:
    c: "@in R+"

  parameters:
    beta: "@in (0,1)"
    gamma: "@in R+"
    theta: "@in (0,1)"
    kappa: "@in R+"
    iota: "@in R+"
    n_H: "@in Z+"
    H_min: "@in R+"
    H_max: "@in R+"

equations:
  dcsn_to_cntn_transition: |
    a_nxt[>] = w_oc - c

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{c}(u(c, H_nxt) + beta*V[>])

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

### 9.5 The renter's choices

The renter path receives `(w_rent, y)` from the `rent` continuation perch.

**Renter Housing Stage** (discrete rental housing choice):

```yaml
name: RenterHousingChoice

symbols:
  spaces:
    Xa: "@def R+"
    Xh: "@def linspace(h_min, h_max, n_h)"
    XY: "@def {1, ..., n_y}"

  prestate:
    w_rent: "@in Xa"      # cash-on-hand (from tenure-choice rent branch)
    y: "@in XY"

  states:
    w_rent: "@in Xa"
    y: "@in XY"

  poststates:
    w_rc: "@in Xa"        # cash after paying rent → renter consumption
    h: "@in Xh"
    y: "@in XY"

  controls:
    h_choice: "@in Xh"

  parameters:
    p_rent: "@in R+"
    n_h: "@in Z+"
    h_min: "@in R+"
    h_max: "@in R+"

equations:
  arvl_to_dcsn_transition: |
    w_rent = w_rent[<]
    y = y[<]

  dcsn_to_cntn_transition: |
    w_rc[>] = w_rent - p_rent * h_choice
    h[>] = h_choice

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{h_choice}(V[>])

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

**Renter Consumption Stage**:

```yaml
name: RenterConsumptionChoice

symbols:
  spaces:
    Xa: "@def R+"
    Xh: "@def linspace(h_min, h_max, n_h)"
    XY: "@def {1, ..., n_y}"

  prestate:
    w_rc: "@in Xa"        # cash after rent (from renter housing stage)
    h: "@in Xh"
    y: "@in XY"

  poststates:
    a_nxt: "@in Xa"
    y: "@in XY"
    H_nxt: "@in {0}"

  controls:
    c: "@in R+"

  parameters:
    beta: "@in (0,1)"
    gamma: "@in R+"
    theta: "@in (0,1)"
    n_h: "@in Z+"
    h_min: "@in R+"
    h_max: "@in R+"

equations:
  dcsn_to_cntn_transition: |
    a_nxt = w_rc - c
    H_nxt = 0

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{c}(u(c, h) + beta*V[>])

  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

### 9.6 Period template

This historical period sketch intends the connections listed below. The current rules check stage-local fields and complete routes; equal names alone do not establish that these connections can all be inferred.

```yaml
name: HousingTenurePeriod

stages:
  - tenure_choice: !stage         # branching stage (own vs rent)
  - owner_housing: !stage         # own path: discrete H' choice
  - owner_cons: !stage            # own path: consumption
  - renter_housing: !stage        # rent path: discrete h choice
  - renter_cons: !stage           # rent path: consumption
```

**Wiring explanation:**

| Connection | Namespace fields |
|---|---|
| `tenure_choice.own` → `owner_housing` | `(w_own, H, y)` match by name |
| `tenure_choice.rent` → `renter_housing` | `(w_rent, y)` match by name |
| `owner_housing` → `owner_cons` | `(w_oc, H_nxt, y)` match by name |
| `renter_housing` → `renter_cons` | `(w_rc, h, y)` match by name |

The distinct cash-on-hand names (`w_own`, `w_oc`, `w_rent`, `w_rc`) make the intended paths readable. If a bare connector endpoint has several eligible stages, write its stage key, for example `owner_housing.w_oc`; this selects an occurrence and leaves the field's local name unchanged.
