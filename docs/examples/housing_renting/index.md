---
audience: user
type: example
topic: [applications]
---
# Housing Tenure-Choice Model

> [!note] Source
> **Canonical registry**: FUES, the code of the fast upper-envelope scan (the
> repository `akshayshanker/FUES` on GitHub, folder
> `examples/housing_renting/config_HR/`).
> FUES owns the housing-renting model registry (on its older
> config-driven schema; not dolo-plus stages). bellman-ddsl carries
> only the prose, stage docs, period diagrams, and converged-output
> markdown that you see in this folder.

An agent lives for $T$ periods holding assets $a \geq 0$ and a housing stock $H \geq 0$.  Each period she receives a Markov income shock $y$ and then decides whether to **own** or **rent** housing.  On the ownership path she adjusts her housing stock $H'$ (paying a transaction cost $\phi$ when $H' \neq H$) and consumes; on the rental path she liquidates housing into cash and rents services $S$ at unit price $P_r$.

This is the model of Fella (2014), solved via DC-EGM with the FUES upper envelope of Dobrescu & Shanker (2024).  See [Housing owner-only model](housing_owner.md) for the sequential (non-branching) submodel.

> [!note] Branching syntax
> See [[branch]] for what a branching stage is and how its branches are
> valued.

## Bellman Equation

Let $V_t(a, H, y_{\text{pre}})$ be the value of an agent entering period $t$ with assets $a$, housing $H$, and previous income state $y_{\text{pre}}$.  After the income shock $y$ is realized:

$$
V_t(a, H, y_{\text{pre}}) = \mathbb{E}_{y | y_{\text{pre}}} \Bigl[ \max_{d \in \{\text{own},\,\text{rent}\}} Q_t^{d}(a, H, y) \Bigr]
$$

**Own branch.**  The agent keeps or adjusts housing, then consumes:

$$
Q_t^{\text{own}}(a, H, y) = \max_{H'} \max_c \bigl\{ u(c, H') + \beta\, V_{t+1}\bigl(a', H', y\bigr) \bigr\}
$$

subject to $a' = w_{\text{oc}} - c \geq 0$, where cash-on-hand after housing adjustment is

$$
w_{\text{oc}} = (1+r)\,a + z[y] + H - \bigl(1 + \phi\,\mathbf{1}[H' \neq H]\bigr)\,H'.
$$

**Rent branch.**  The agent liquidates housing, rents services $S$, then consumes:

$$
Q_t^{\text{rent}}(a, H, y) = \max_{S} \max_c \bigl\{ u(c, S) + \beta\, V_{t+1}\bigl(a', 0, y\bigr) \bigr\}
$$

subject to $a' = w_{\text{rc}} - c \geq 0$, where cash-on-hand after rental payment is

$$
w_{\text{rc}} = (1+r)\,a + z[y] + H - P_r\,S.
$$

Note that renters arrive at the next period with $H = 0$.

**Utility** is CES in consumption and housing services:

$$
u(c, h) = \frac{\bigl[\theta\, c^{\rho} + (1-\theta)\,(\kappa\, h + \iota)^{\rho}\bigr]^{(1-\gamma)/\rho}}{1-\gamma}
$$

where $h = H'$ for owners and $h = S$ for renters.  When $\gamma = 1$ this reduces to Cobb-Douglas; the solver handles this limit.

**Terminal condition**: $V_{T+1} \equiv 0$.

## Bellman-calculus decomposition

The period decomposes into five stages.  Each has forward transitions $\mathrm{g}_{\prec\sim}$, $\mathrm{g}_{\sim\succ}$ and backward builders $\mathbb{B}$, $\mathbb{I}$.

**TenureChoice** (branching, $x_\prec = \{a, H, y_{\text{pre}}\}$, $x = \{a, H, y\}$):

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

**OwnerHousing** (own path, $x_\prec = \{a_o, H_o, y_o\}$, $x_\succ = \{w_{\text{oc}}, H_{\text{nxt}}, y_o\}$):

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

**OwnerCons** (own path, $x_\prec = \{w_{\text{oc}}, H_{\text{nxt}}, y_o\}$, $x_\succ = \{b_o, H_{\text{nxt}}, y_o\}$):

$$
\mathrm{g}_{\sim\succ}: \quad b_o = w_{\text{oc}} - c
$$

$$
\mathbb{B}: \quad \mathrm{v}(w_{\text{oc}}, H_{\text{nxt}}, y_o) = \max_c\bigl\{u(c, H_{\text{nxt}}) + \beta\, \mathrm{v}_\succ(w_{\text{oc}} - c, H_{\text{nxt}}, y_o)\bigr\}
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec = \mathrm{v} \qquad\text{(identity)}
$$

**RenterHousing** (rent path, $x_\prec = \{w_r, y_r\}$, $x_\succ = \{w_{\text{rc}}, S, y_r\}$):

$$
\mathrm{g}_{\sim\succ}: \quad w_{\text{rc}} = w_r - P_r\,S
$$

$$
\mathbb{B}: \quad \mathrm{v}(w_r, y_r) = \max_{S} \mathrm{v}_\succ(w_r - P_r S, S, y_r)
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec = \mathrm{v} \qquad\text{(identity)}
$$

**RenterCons** (rent path, $x_\prec = \{w_{\text{rc}}, S, y_r\}$, $x_\succ = \{b_r, H_r, y_r\}$):

$$
\mathrm{g}_{\sim\succ}: \quad b_r = w_{\text{rc}} - c, \quad H_r = 0
$$

$$
\mathbb{B}: \quad \mathrm{v}(w_{\text{rc}}, S, y_r) = \max_c\bigl\{u(c, S) + \beta\, \mathrm{v}_\succ(w_{\text{rc}} - c, 0, y_r)\bigr\}
$$

$$
\mathbb{I}: \quad \mathrm{v}_\prec = \mathrm{v} \qquad\text{(identity)}
$$

## Period Composition

Both branches terminate with poststates that map to the next period's arrival $(a, H, y_{\text{pre}})$ via a uniform inter-period connector:

$$
(b_o, H_{\text{nxt}}, y_o) \;\xrightarrow{\text{connector}}\; (a, H, y_{\text{pre}}) \qquad\text{(owner exit)}
$$

$$
(b_r, 0, y_r) \;\xrightarrow{\text{connector}}\; (a, 0, y_{\text{pre}}) \qquad\text{(renter exit, } H = 0\text{)}
$$

A renter arriving with $H = 0$ who chooses `own` starts from $w_{\text{oc}} = (1+r)a + z[y]$ — no housing equity.

## Period Structure

<div markdown="0">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 320" style="max-width:820px;width:100%;">
  <defs>
    <style>
      .dag-edge   { fill: none; stroke: currentColor; stroke-width: 1.2px; stroke-linecap: round; }
      .dag-arrow  { fill: currentColor; }
      .dag-perch  { fill: var(--md-default-bg-color, white); stroke: currentColor; stroke-width: 1.2px; }
      .dag-stg    { fill: currentColor; stroke: none; }
      .dag-bound  { fill: none; stroke: currentColor; stroke-width: 0.8px; stroke-dasharray: 4 3; opacity: 0.25; }
      .dag-field  { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 14px; fill: currentColor; }
      .dag-sub    { font-size: 10px; }
      .dag-ptag   { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 9px; fill: currentColor; opacity: 0.40; }
      .dag-slabel { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 10.5px; fill: currentColor; }
      .dag-branch { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 10px; fill: currentColor; font-style: italic; }
      .dag-period { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 9.5px; fill: currentColor; opacity: 0.30; font-style: italic; }
      .dag-legend { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 8px; fill: currentColor; opacity: 0.45; }
    </style>
    <marker id="dag-ah" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L8,3 L0,6 L1.5,3 Z" class="dag-arrow"/>
    </marker>
  </defs>
  <rect class="dag-bound" x="14" y="14" width="792" height="292" rx="8"/>
  <text class="dag-period" x="26" y="30">HousingTenurePeriod</text>
  <circle class="dag-stg" cx="688" cy="27" r="3.5"/>
  <text class="dag-legend" x="695" y="30">stage</text>
  <circle class="dag-perch" cx="740" cy="27" r="3.5"/>
  <text class="dag-legend" x="747" y="30">perch field</text>
  <!-- Arrival perch fields -->
  <circle class="dag-perch" cx="56" cy="115" r="5.5"/>
  <text class="dag-field" x="56" y="100" text-anchor="middle">a</text>
  <circle class="dag-perch" cx="56" cy="155" r="5.5"/>
  <text class="dag-field" x="56" y="175" text-anchor="middle">H</text>
  <circle class="dag-perch" cx="56" cy="195" r="5.5"/>
  <text class="dag-field" x="56" y="215" text-anchor="middle">y<tspan class="dag-sub" dy="3">pre</tspan></text>
  <text class="dag-ptag" x="56" y="235" text-anchor="middle">&#x227A;</text>
  <!-- Tenure choice stage -->
  <circle class="dag-stg" cx="180" cy="155" r="7.5"/>
  <text class="dag-slabel" x="180" y="138" text-anchor="middle">tenure_choice</text>
  <!-- Edges: arrival to tenure_choice -->
  <line class="dag-edge" x1="62" y1="115" x2="172" y2="150" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="62" y1="155" x2="172" y2="155" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="62" y1="195" x2="172" y2="160" marker-end="url(#dag-ah)"/>
  <!-- Owner housing stage -->
  <circle class="dag-stg" cx="370" cy="80" r="7.5"/>
  <text class="dag-slabel" x="370" y="63" text-anchor="middle">owner_housing</text>
  <!-- Owner cons stage -->
  <circle class="dag-stg" cx="555" cy="80" r="7.5"/>
  <text class="dag-slabel" x="555" y="63" text-anchor="middle">owner_cons</text>
  <!-- Renter housing stage -->
  <circle class="dag-stg" cx="370" cy="235" r="7.5"/>
  <text class="dag-slabel" x="370" y="260" text-anchor="middle">renter_housing</text>
  <!-- Renter cons stage -->
  <circle class="dag-stg" cx="555" cy="235" r="7.5"/>
  <text class="dag-slabel" x="555" y="260" text-anchor="middle">renter_cons</text>
  <!-- Branch edges: tenure_choice to owner/renter housing -->
  <path class="dag-edge" d="M188,150 C230,120 310,85 362,80" marker-end="url(#dag-ah)"/>
  <text class="dag-branch" x="260" y="103">own</text>
  <path class="dag-edge" d="M188,162 C230,195 310,230 362,235" marker-end="url(#dag-ah)"/>
  <text class="dag-branch" x="258" y="218">rent</text>
  <!-- Sequential edges: housing to cons -->
  <line class="dag-edge" x1="378" y1="80" x2="547" y2="80" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="378" y1="235" x2="547" y2="235" marker-end="url(#dag-ah)"/>
  <!-- Continuation perch fields (owner) -->
  <circle class="dag-perch" cx="710" cy="60" r="5.5"/>
  <text class="dag-field" x="710" y="47" text-anchor="middle">b<tspan class="dag-sub" dy="3">o</tspan></text>
  <circle class="dag-perch" cx="710" cy="85" r="5.5"/>
  <text class="dag-field" x="710" y="104" text-anchor="middle">H<tspan class="dag-sub" dy="3">nxt</tspan></text>
  <text class="dag-ptag" x="730" y="74" text-anchor="start">&#x227B;</text>
  <!-- Continuation perch fields (renter) -->
  <circle class="dag-perch" cx="710" cy="220" r="5.5"/>
  <text class="dag-field" x="710" y="208" text-anchor="middle">b<tspan class="dag-sub" dy="3">r</tspan></text>
  <circle class="dag-perch" cx="710" cy="248" r="5.5"/>
  <text class="dag-field" x="710" y="268" text-anchor="middle">H<tspan class="dag-sub" dy="3">r</tspan><tspan class="dag-sub" dx="1">=0</tspan></text>
  <text class="dag-ptag" x="730" y="237" text-anchor="start">&#x227B;</text>
  <!-- Edges: cons to continuation perch fields -->
  <line class="dag-edge" x1="563" y1="76" x2="704" y2="62" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="563" y1="84" x2="704" y2="85" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="563" y1="231" x2="704" y2="220" marker-end="url(#dag-ah)"/>
  <line class="dag-edge" x1="563" y1="239" x2="704" y2="248" marker-end="url(#dag-ah)"/>
</svg>
</div>

The income shock $y$ is realized at `tenure_choice` (arrival to decision).  The own branch passes $(a, H, y)$ to `owner_housing`; the rent branch converts everything to cash $w_r = (1+r)a + z[y] + H$ and passes $(w_r, y)$ to `renter_housing`.  Both consumption stages output end-of-period assets and housing stock — the renter sets $H_r = 0$ explicitly, so the inter-period connector is a uniform rename.

## Stages

Each stage is documented with its dolo-plus YAML specification:

| # | Stage | Kind | Control | Method |
|---|-------|------|---------|--------|
| 1 | [tenure_choice](stages/tenure_choice.md) | branching | $d \in \{\text{own}, \text{rent}\}$ | `max` aggregator + $\mathbb{E}_{y\|y_{\text{pre}}}$ |
| 2 | [owner_housing](stages/owner_housing.md) | sequential | $H' \in X_H$ (discrete) | discrete `max` over housing grid |
| 3 | [owner_cons](stages/owner_cons.md) | sequential | $c > 0$ (continuous) | EGM + FUES |
| 4 | [renter_housing](stages/renter_housing.md) | sequential | $S \in X_S$ (discrete) | discrete `max` over rental grid |
| 5 | [renter_cons](stages/renter_cons.md) | sequential | $c > 0$ (continuous) | EGM + FUES |

## Period, Trellis, and Calibration

See [Period and trellis wiring](period_and_nest.md) for the period template, inter-period connectors, and calibration.
