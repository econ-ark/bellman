---
audience: user
type: example
topic: [applications]
---
# Application 2: Continuous Housing Investment with Frictions

*Source: Dobrescu and Shanker (2026), Section 2.2. The paper is the canonical reference for the economic model; this page records the notation and staged Bellman representation used in the codebase.*

## Notation

| Symbol | Meaning |
|--------|---------|
| $a_t$ | Financial (liquid) assets at time $t$ |
| $H_t$ | Housing (illiquid) assets at time $t$ |
| $c_t$ | Non-housing consumption at time $t$ |
| $y_t$ | Stochastic wage at time $t$ (Markov process) |
| $d_t \in \{0,1\}$ | Housing adjustment indicator ($1$ = adjust, $0$ = keep) |
| $r$ | Rate of return on financial assets |
| $\tau > 0$ | Proportional housing adjustment cost |
| $\beta$ | Discount factor |
| $x_t = (1+r)a_t + y_t + d_t H_t$ | Total wealth at time $t$ |
| $u : \mathbb{R}_+ \times \mathbb{R}_+ \to \mathbb{R} \cup \{-\infty\}$ | Per-period utility over consumption and housing |
| $\theta : \mathbb{R}_+ \to \mathbb{R} \cup \{-\infty\}$ | Bequest function |
| $V_t(a, H, y)$ | Value function |
| $\sigma_t^{a,d}$, $\sigma_t^{H,d}$ | Choice-specific policy functions for assets and housing |
| $\mathcal{I}_t(a, H, y)$ | Discrete choice policy function |
| $\Theta_t(a, H, y)$ | Continuation marginal value of housing if not adjusted |
| $\iota$ | Random stopping time: next period when $d_\iota = 1$ |

## 1. Model in recursive sequence notation 

Households hold non-negative financial assets $a_t$ and non-negative housing $H_t$. Financial assets earn a rate of return $r$; housing earns no return. Liquid assets adjust frictionlessly, while adjusting housing to a new level $H_{t+1}$ costs $\tau H_{t+1}$, $\tau > 0$. In period $t \in \{0, 1, \ldots, T\}$, the household consumes $c_t$, chooses $a_{t+1}$, and selects a discrete adjustment indicator $d_t \in \{0, 1\}$: when $d_t = 0$ housing is held fixed, $H_{t+1} = H_t$; when $d_t = 1$ a new $H_{t+1}$ is chosen subject to the adjustment cost. Income $y_t$ is exogenous and follows a Markov process.

The period budget constraint is

$$
(1+r)a_t + y_t + d_t H_t \geq a_{t+1} + c_t + d_t (1+\tau) H_{t+1},
$$

where $x_t = (1+r)a_t + y_t + d_t H_t$ is total available wealth. The household lives through $t = 0, \ldots, T$ and values terminal bequests via $\theta : \mathbb{R}_+ \to \mathbb{R} \cup \{-\infty\}$. Per-period utility $u(c_t, H_{t+1})$ is concave, jointly differentiable, and increasing in non-housing consumption and end-of-period housing (Yogo, 2016). The sequential problem is

$$
V_0(a_0, H_0, y_0)
= \max_{(c_t, a_{t+1}, H_{t+1}, d_t)_{t=0}^{T}}
\left\{
\sum_{t=0}^{T} \beta^t \mathbb{E}\, u(c_t, H_{t+1})
\;+\;
\mathbb{E}\, \beta^{T+1} \theta\bigl((1+r)a_{T+1} + H_{T+1}\bigr)
\right\},
$$

subject to the budget constraint, $H_t \geq 0$, $a_t \geq 0$, and given $(a_0, H_0, y_0)$. The terminal value is $V_{T+1}(a_{T+1}, H_{T+1}) = \theta\bigl((1+r)a_{T+1} + H_{T+1}\bigr)$, and for $t \leq T$ the Bellman equation is

$$
V_t(a, H, y) = \max_{a', H', d} \left\{ u(c, H') + \beta \mathbb{E}_y V_{t+1}(a', H', y') \right\},
$$

with primes denoting continuation states satisfying the budget constraint, $c = y + (1+r)a + dH - a' - d(1+\tau)H'$, and $H' = H$ if $d = 0$.

### 1.2 Euler equations

The weak inequalities below allow for the occasionally binding non-negativity constraint on liquid assets.

There is one Euler equation for each state. The financial-asset Euler equation is

$$
u_1(c_t, H_{t+1}) \geq \beta(1+r)\, \mathbb{E}_t\, u_1(c_{t+1}, H_{t+2}),
$$

with $u_1$ and $u_2$ denoting partial derivatives of $u$ with respect to its first and second arguments. When $d_t = 1$, the housing Euler equation is

$$
(1+\tau)\, u_1(c_t, H_{t+1}) \geq \underbrace{\mathbb{E}_t \sum_{k=t}^{\iota-1} \beta^{k-t}\, u_2(c_k, H_{k+1})}_{\text{marginal value of the housing-services stream}} + \underbrace{\mathbb{E}_t\, \beta^{\iota-t}\, u_1(c_\iota, H_{\iota+1})}_{\text{marginal value of liquidating housing at time } \iota}.
$$

The financial Euler equation is standard. The housing Euler equation features a random stopping time $\iota$, defined as the next period with $d_\iota = 1$. The shadow value of housing is the discounted expected marginal utility at the next liquidation date plus the intervening stream of housing-services utilities.

**Functional form.** The recursive solution implies measurable policy functions $\sigma_t^a$, $\sigma_t^H$, and $\mathcal{I}_t$, with branch-specific versions $\sigma_t^{a,d}$ and $\sigma_t^{H,d}$. On the adjust branch at time $t$,

$$
c = (1+r)a + H + y - \sigma_t^{a,1}(a, H, y) - (1+\tau)\sigma_t^{H,1}(a, H, y),
$$

with

$$
a' = \sigma_t^{a,1}(a, H, y), \qquad H' = \sigma_t^{H,1}(a, H, y).
$$

Let $d_{t+1} = \mathcal{I}_{t+1}(a', H', y')$. Next-period consumption is then determined by the same budget constraint on the realized branch:

$$
c' = (1+r)a' + d_{t+1} H' + y' - \sigma_{t+1}^{a,d_{t+1}}(a', H', y') - d_{t+1}(1+\tau)\sigma_{t+1}^{H,d_{t+1}}(a', H', y').
$$

Define

$$
H'' =
\begin{cases}
\sigma_{t+1}^{H,1}(a', H', y'), & d_{t+1} = 1, \\
H', & d_{t+1} = 0 .
\end{cases}
$$

Substituting the policies into the housing Euler equation yields

$$
(1+\tau)\, u_1(c, H') \geq u_2(c, H') + \beta \mathbb{E}_y \left\{ \mathcal{I}_{t+1}(a', H', y')\, u_1(c', H'') \right\} + \beta \mathbb{E}_y \left\{ (1 - \mathcal{I}_{t+1}(a', H', y')) \bigl[ \Theta_{t+1}(a', H', y') + u_2(c', H') \bigr] \right\}.
$$

The multiplier $\Theta_t$ collects the continuation marginal value of housing when the household does not adjust:

$$
\Theta_t(a, H, y) = \beta \mathbb{E}_y \left\{ \mathcal{I}_{t+1}(a', H', y')\, u_1(c', H'') \right\} + \beta \mathbb{E}_y \left\{ (1 - \mathcal{I}_{t+1}(a', H', y')) \bigl[ \Theta_{t+1}(a', H', y') + u_2(c', H') \bigr] \right\}.
$$

The functional financial Euler equation is

$$
u_1(c, H') \geq \beta(1+r)\, \mathbb{E}_y\, u_1(c', H''),
$$

with $c$, $c'$, and $H''$ defined as above.

## 2. Modular Bellman form

The formulation above is the standard one: one Bellman equation with a discrete choice embedded in the budget constraint. We now rewrite the same model in staged Bellman form. In the code, each period is split into linked subproblems with their own state spaces and Bellman operators.

> [!note] Timing and naming
> We use the multi-stage Bellman notation of [Carroll (2026)](https://llorracc.github.io/SolvingMicroDSOPs/) and [Carroll and Shanker (2026)](../../bellman-calculus/index.md). Each stage has three perches — by which we mean ordered locations, each associated with a distinct information set:
>
> - **Arrival** ($\prec$): perch on entering the stage.
> - **Decision** (unmarked): perch on which the agent makes a decision.
> - **Continuation** ($\succ$): perch after the choice and transition.
>
> Within a stage we use perch indices. The paper's time subscripts label periods in the mathematical exposition; a trellis position is only an address. The application sends age backward as a constant field and reads fixed income tables at that age. Greek letters denote arrival quantities (e.g. $\xi$ for the persistent income state at arrival); Roman letters denote quantities realized or chosen inside the period (e.g. $z$ once the income innovation resolves, $\nu$ for housing at the continuation perch). Housing at arrival is $h$; the carried or chosen housing at the continuation perch is $\nu$.
>


A household lives for $T$ periods, holding financial assets $a \ge 0$ and housing $h \ge 0$ at the start of each period.

Each period it draws an i.i.d. innovation $\varepsilon \sim N(0,1)$, updates the persistent income state via $\log z = \rho \log \xi + \sigma \varepsilon$, earns income $\mathrm{y}(z)$, and makes a discrete tenure choice $d \in \{0, 1\}$ — keep or adjust housing — followed by a non-durable consumption choice $c$ (plus, on the adjuster branch, a choice of the housing $\nu$ held at the continuation perch). Financial assets earn gross return $R = 1+r$; adjusting housing costs $\tau\,\nu$. The stage equations below keep $\delta$ (housing depreciation) and $R_\nu$ (housing gross return) as free parameters; the simplest case of the main text sets $\delta = 0$ and $R_\nu = 1$.

### Stage decomposition

Each period decomposes into stages, solved in reverse. The decision-to-continuation transition of `tenure` *branches* into the keep and adjust alternatives: they share a single decision perch, split only on the way to the continuation perch, and remain alternatives of one branching until each one leaves the stage. The forward layout is therefore:

1. **`tenure`** (branching + $\mathbb{E}$) — discrete choice $\max(\mathrm{v}_{\mathrm{kp},\succ},\, \mathrm{v}_{\mathrm{adj},\succ})$; income innovation $\varepsilon$ draws; asset returns realized; durables liquidated on the adjuster branch.
   - Keeper continuation state: $w_{\mathrm{kp}} = R\,a + \mathrm{y}(z)$, with carried housing $\nu_{\mathrm{kp}} = (1-\delta)\,h$.
   - Adjuster continuation state: $w_{\mathrm{adj}} = R\,a + R_\nu(1-\delta)\,h + \mathrm{y}(z)$.

2. **Branch alternatives** (no order between them):
   - **`keeper_cons`** (1D EGM + FUES) — consumption choice on cash-on-hand $w_{\mathrm{kp}}$; carried housing $\nu_{\mathrm{kp}}$ passes through.
   - **`adjuster_cons`** (2D partial EGM + FUES) — joint choice of consumption and new housing $\nu_{\mathrm{adj}}$ on total wealth $w_{\mathrm{adj}}$.

`keeper_cons` and `adjuster_cons` are the two alternatives of the same decision-to-continuation branching; neither precedes the other. The Bellman equations below are written conditional on the realized income state $z$. Economically this is a one-dimensional EGM problem for each $(z, \nu)$ slice of the keeper problem and a one-dimensional wealth problem for each $z$ slice of the adjuster problem.

### Stage `tenure` — branching and the income shock

The bequest takes in age 71. Each consumption stage keeps the age it takes in. The tenure stage sends back the keep branch's incoming age minus one. Each branch reads the wage and retirement tables at its incoming age to obtain the amounts for the age one year younger.

| Perch | States | Description |
|-------|-----------------|-------------|
| Arrival $(\prec)$ | $a,\; h,\; \xi$ | Assets, housing, arrival persistent income state |
| Decision | $a,\; h,\; \xi$ | Identity transition; single perch shared by both alternatives |
| Continuation $(\succ)$ — **kp** | $w_{\mathrm{kp}},\; \nu_{\mathrm{kp}},\; z$ | Cash-on-hand, carried housing, realized income (keep arm) |
| Continuation $(\succ)$ — **adj** | $w_{\mathrm{adj}},\; z$ | Total liquid wealth, realized income (adjust arm) |

The two continuation rows are the two alternatives of the same decision-to-continuation transition, not stages encountered in sequence.

**Arrival → decision (identity).** Identity transformation; the arrival state passes through unchanged.

**Decision → continuation (the branching).** The branching lives on this transition, not at the decision perch. The innovation $\varepsilon \sim N(0,1)$ resolves here, producing $z = \xi^{\rho}\exp(\sigma\,\varepsilon)$, and the transition divides into two alternatives that each map the same decision-perch $(a, h)$ into a branch-specific continuation:

- *Keep arm* — housing depreciates and is retained:

  $$
  w_{\mathrm{kp}} = R\,a + \mathrm{y}(z), \qquad \nu_{\mathrm{kp}} = (1-\delta)\,h.
  $$

- *Adjust arm* — housing is liquidated at resale value $R_\nu(1-\delta)\,h$ and folded into liquid wealth:

  $$
  w_{\mathrm{adj}} = R\,a + R_\nu(1-\delta)\,h + \mathrm{y}(z).
  $$

**Bellman step $\mathbb{B}$.** Conditional on $z$, the agent picks the better arm:

$$
\mathrm{v}(a, h, z) = \max\bigl(\,\mathrm{v}_{\mathrm{kp},\succ}(w_{\mathrm{kp}},\, \nu_{\mathrm{kp}}),\;\; \mathrm{v}_{\mathrm{adj},\succ}(w_{\mathrm{adj}})\,\bigr).
$$

**Marginal-value propagation.** Writing $\mathbb{1}_{\mathrm{adj}}$ for the branch indicator, the envelope conditions at the decision perch are

$$
\partial_a \mathrm{v} = \mathbb{1}_{\mathrm{adj}}\, R\, \partial_{w_{\mathrm{adj}}} \mathrm{v}_{\mathrm{adj},\succ} + (1 - \mathbb{1}_{\mathrm{adj}})\, R\, \partial_{w_{\mathrm{kp}}} \mathrm{v}_{\mathrm{kp},\succ},
$$

$$
\partial_h \mathrm{v} = \mathbb{1}_{\mathrm{adj}}\, R_\nu(1-\delta)\, \partial_{w_{\mathrm{adj}}} \mathrm{v}_{\mathrm{adj},\succ} + (1 - \mathbb{1}_{\mathrm{adj}})\, (1-\delta)\, \partial_{\nu_{\mathrm{kp}}} \mathrm{v}_{\mathrm{kp},\succ}.
$$

**Expectation step $\mathbb{I}$.** Integrate over $\varepsilon$ given $\xi$, with $z = \xi^{\rho}\exp(\sigma\,\varepsilon)$:

$$
\mathrm{v}_{\prec}(a, h, \xi) = \mathbb{E}_{\varepsilon}\!\bigl[\mathrm{v}(a, h, z)\bigr], \qquad \partial_a \mathrm{v}_{\prec} = \mathbb{E}_{\varepsilon}\!\bigl[\partial_a \mathrm{v}\bigr], \qquad \partial_h \mathrm{v}_{\prec} = \mathbb{E}_{\varepsilon}\!\bigl[\partial_h \mathrm{v}\bigr].
$$

### The branch alternatives: `keeper_cons` and `adjuster_cons`

These two stages sit at the same depth: they are the two alternatives of the `tenure` decision-to-continuation transition and remain alternatives until each one reaches its continuation perch and exits the period. There is no partial order between them; ex post the agent travels along exactly one arm, but the formal description carries both.

#### Stage `keeper_cons` — keeper consumption (1D EGM + FUES)

| Perch | Variables | Description |
|-------|-----------|-------------|
| Decision | $w,\, \nu$ | Cash-on-hand and carried housing from `tenure-kp`; no within-stage shock before optimization |
| Continuation $(\succ)$ | $a_{\succ},\, \nu_{\succ} = \nu$ | Post-savings assets; housing passes through |

**Bellman step $\mathbb{B}$.** The keeper optimizes over consumption alone:

$$
\mathrm{v}_{\mathrm{kp}}(w, \nu) = \max_{c \ge 0}\;\bigl\{\mathrm{u}(c, \nu) + \beta\,\mathrm{v}_{\succ}(w - c,\; \nu)\bigr\},
$$

subject to $a_{\succ} = w - c \ge 0$ and $\nu_{\succ} = \nu$. The FOC is

$$
\partial_c \mathrm{u}(c, \nu) = \beta\, \partial_a \mathrm{v}_{\succ}(a_{\succ}, \nu).
$$

*EGM step.* Fix $a_{\succ}$ on the exogenous grid. The financial Euler inverts analytically:

$$
c_{\succ} = (\partial_c \mathrm{u})^{-1}\!\bigl(\beta\, \partial_a \mathrm{v}_{\succ}(a_{\succ}, \nu)\bigr), \qquad w_{\succ} = a_{\succ} + c_{\succ},
$$

which yields the endogenous cash-on-hand grid. FUES selects the upper envelope from the pooled constrained and unconstrained EGM points.

*Non-concavity.* The continuation $\mathrm{v}_{\succ}(a_{\succ}, \nu)$ is next period's tenure-stage arrival value. The branching $\max$ introduces primary kinks at the keep/adjust switching threshold; future switching thresholds propagate backward as *secondary kinks* — the DC-EGM mechanism of [Iskhakov et al. (2017)](https://doi.org/10.3982/QE643). $\partial_a \mathrm{v}_{\succ}(\cdot, \nu)$ is non-monotone, and the EGM-constructed $w_{\succ}(a_{\succ})$ mapping has crossing segments.

**Envelope conditions.** The stage declares no arrival perch, since nothing is drawn before the choice: its decision value is the value the stage exports, which the tenure stage reads on the keep branch. The envelope theorem gives

$$
\partial_w \mathrm{v}_{\mathrm{kp}}(w, \nu) = \partial_c \mathrm{u}(c^\star, \nu), \qquad \partial_\nu \mathrm{v}_{\mathrm{kp}}(w, \nu) = \partial_\nu \mathrm{u}(c^\star, \nu) + \beta\, \partial_\nu \mathrm{v}_{\succ}(a_{\succ}, \nu).
$$

The marginal $\partial_\nu \mathrm{v}_{\mathrm{kp}}$ — housing-services value plus the continuation shadow value — is the quantity $\Theta$ in §2's stopping-time representation.

#### Stage `adjuster_cons` — adjuster consumption (2D partial EGM + FUES)

| Perch | Variables | Description |
|-------|-----------|-------------|
| Decision | $m$ | Total liquidated wealth from `tenure-adj` |
| Continuation $(\succ)$ | $a_{\succ},\, \nu_{\succ}$ | New savings and new housing |

**Bellman step $\mathbb{B}$.** The adjuster jointly chooses consumption and new housing:

$$
\mathrm{v}_{\mathrm{adj}}(m) = \max_{c,\, \nu_{\succ} \ge 0}\;\bigl\{\mathrm{u}(c, \nu_{\succ}) + \beta\,\mathrm{v}_{\succ}(m - c - (1+\tau)\,\nu_{\succ},\; \nu_{\succ})\bigr\},
$$

subject to $a_{\succ} = m - c - (1+\tau)\, \nu_{\succ} \ge 0$. The two FOCs are

$$
\partial_c \mathrm{u}(c, \nu_{\succ}) = \beta\, \partial_a \mathrm{v}_{\succ}, \qquad
(1+\tau)\, \partial_c \mathrm{u}(c, \nu_{\succ}) = \partial_\nu \mathrm{u}(c, \nu_{\succ}) + \beta\, \partial_\nu \mathrm{v}_{\succ}.
$$

The housing FOC equates the marginal cost $(1+\tau)\, \partial_c \mathrm{u}$ to the marginal benefit $\partial_\nu \mathrm{u} + \beta\, \partial_\nu \mathrm{v}_{\succ}$.

*Partial EGM.* Fix $\nu_{\succ}$ on an exogenous grid. For each $\hat{\nu}_i$: invert the financial Euler to obtain $c_{\succ}(a_{\succ}, \hat{\nu}_i)$, recover the endogenous wealth $m_{\succ} = a_{\succ} + c_{\succ} + (1+\tau)\, \hat{\nu}_i$, and evaluate the Bellman value $\hat{\mathrm{v}}$. Pool candidates across the full $(a_{\succ}, \hat{\nu}_i)$ grid and apply FUES to recover $(c^\star, \nu_{\succ}^\star)$ as functions of $m$.

*Multiple roots.* The mapping $a_{\succ} \mapsto m_{\succ}$ is **non-monotone** for two compounding reasons: (i) secondary kinks from future tenure switches make $\partial_a \mathrm{v}_{\succ}(\cdot, \nu)$ non-monotone; (ii) housing is simultaneously a consumption good and an asset, and the resulting intertemporal income effects produce discontinuous drops in housing investment at tenure-switch thresholds. The housing policy $\nu_{\succ}^\star(m)$ exhibits upward and downward jumps. MSS and LTM require locally isolated monotone segments and cannot resolve this structure. FUES scans the full cloud in a single $O(n \log n)$ pass.

**Envelope condition.** The stage declares no arrival perch: its decision value is the value the stage exports, which the tenure stage reads on the adjust branch. The envelope theorem gives

$$
\partial_m \mathrm{v}_{\mathrm{adj}}(m) = \partial_c \mathrm{u}(c^\star, \nu_{\succ}^\star).
$$
