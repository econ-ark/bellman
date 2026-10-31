---
audience: user
type: example
topic: [applications]
---

# Solving a finite-horizon consumption problem via Stachurski's Slider

This note works through a concrete example — the portfolio-choice and consumption-savings problem over a finite horizon — to show how "order semiconjugate transform" connects a particular ordering of operators within a stage to the dolo solver -- which uses an alternative ordering of operators. 

We begin from the terminal period, build the object we need to iterate on, and show that two natural orderings of the same Bellman operator are semiconjugate. We use this duality relationship to transform one ordering to the other, send it to dolo, and bring it back via the "slider". 
## 1. The problem

Let's start with two equivalent formulations of the same finite-horizon consumption–savings problem.

- **Problem A**: a single operator on cash-on-hand (dolo’s EGM “one-stage” view) where the decision problem computes the expectation. 
- **Problem B**: a two-stage factorization of the same period operator into a **noport stage** (pure expectation) and a **cons stage** (pure maximization). 

Suppose we have technology (code) to solve problem A, but we actually want to solve problem B. On the surface these two views look irreconcilable, and one may retort, "but problem B is totally different and cannot be solved using machinery used to solve problem A". 

However, these two dynamical systems *are related* by **order semiconjugacy** (due to Stachurski and Sargent (2026) and other references): they use the same sub-operators in opposite order.

Thankfully, Bellman calculus stages can represent both problem A and problem B as stages, and we can see their duality clearly. 

### A. The primal sequence problem with shocks after decision

Let's start with the sequence problem that problem A tries to tackle. An agent lives for $H$ periods. In each period $t = 0, \ldots, H-1$ the agent:

1. enters with assets $a_{t-1}$,
2. receives a stochastic income shock $\theta_t \sim \text{LogNormal}(\mu_\theta, \sigma_\theta)$,
3. observes cash-on-hand $m_t = a_{t-1} R + \theta_t$,
4. chooses consumption $c_t \in (0, m_t)$,
5. exits with assets $a_t = m_t - c_t$.

The objective is to maximize

$$
\mathbb{E}_0 \sum_{t=0}^{H-1} \beta^t \, u(c_t),
\qquad u(c) = \frac{c^{1-\rho}}{1-\rho}.
$$

The continuation value at the horizon is an asset-space function $w_H(a)$ (e.g. $w_H(a)=0$ for no bequest).

#### A1. The Bellman equation

Working backwards from the terminal period, the Bellman equation at period $t$ is

$$
V_t(m) = \max_{c \in (0,m)} \Bigl\{ u(c) + \beta \, \mathbb{E}_{\theta'}\bigl[ V_{t+1}\bigl( (m - c)\,R + \theta' \bigr) \bigr] \Bigr\}.
\tag{B}
$$

Write $a = m - c$ for the post-consumption assets. The operator that maps the period $t+1$ value function to the period-\(t\) value function is

$$
(\hat{\mathbf{S}}\, V)(m) = \max_{c} \Bigl\{ u(c) + \beta \, \mathbb{E}_{\theta'}\bigl[ V(aR + \theta') \bigr] \Bigr\}.
$$

Solving the finite-horizon problem amounts to computing the iterates $\hat{\mathbf{S}}^n V_H$ for $n = 1, \ldots, H$.

#### The Bellman equation at the three perches

Map the period into a single stage with the three [perches](../../wiki/perch.md), the information sets arrival, decision and continuation (ADC). The shock $\theta'$ occurs *after* the decision — it is a post-decision shock in $\mathrm{g}_{\sim\succ}$. The three perches carry:

| Perch | Variable | Description |
|-------|----------|-------------|
| $\prec$ (arrival) | $m$ | cash-on-hand (shock already resolved) |
| $\cdot$ (decision) | $m,\; c$ | cash-on-hand and consumption choice |
| $\succ$ (continuation) | $m'$ | next period's cash-on-hand (after post-decision shock) |

Forward transitions:

$$
\mathrm{g}_{\prec\sim} \colon m \mapsto m
\qquad\text{(identity)},
\qquad
\mathrm{g}_{\sim\succ} \colon (m, c, \theta') \mapsto m' = (m - c)\,R + \theta',
$$

where $\theta' \sim \text{LogNormal}(\mu_\theta, \sigma_\theta)$ is the post-decision shock and $\mathrm{g}_{\prec\sim}$ is trivial. The backward builders are:

- $\mathbb{B}$ (continuation → decision): combines the max *and* the expectation, because the shock sits inside $\mathrm{g}_{\sim\succ}$:

$$
(\mathbb{B}\, \mathrm{v}_\succ)(m) = \max_{c \in (0,m)} \bigl\{ u(c) + \beta\, \mathbb{E}_{\theta'}\bigl[\mathrm{v}_\succ\bigl((m - c)\,R + \theta'\bigr)\bigr] \bigr\}.
$$

- \(\mathbb{I}\) (decision → arrival): identity, \(\mathrm{v}_\prec(m) = \mathrm{v}_\cdot(m)\).

The full stage operator is just $\mathbb{B}$ (since $\mathbb{I}$ is trivial). With the inter-period connector identifying $m' = m$, this gives exactly (B). The expectation is locked inside $\mathbb{B}$ — inseparable from the maximization.

#### Factoring the operator

Although $\mathbb{B}$ is monolithic in the ADC, it decomposes analytically into two sub-operators:

$$
(\mathbf{E}\, v)(a) = \mathbb{E}_\theta\bigl[v(aR + \theta)\bigr],
\qquad
(\mathbf{M}\, w)(m) = \max_{c \in (0,m)}\bigl\{u(c) + \beta\, w(m - c)\bigr\}.
$$

$\mathbf{E}$ maps a function on cash-on-hand to a function on assets (integration); $\mathbf{M}$ maps a function on assets to a function on cash-on-hand (optimization). Then

$$
\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E},
$$

since $(\mathbb{B}\,v)(m) = \max_c\bigl\{u(c) + \beta\, \underbrace{\mathbb{E}_\theta[v((m-c)R + \theta)]}_{(\mathbf{E}\,v)(m-c)}\bigr\} = (\mathbf{M} \circ \mathbf{E}\, v)(m)$. Since $\mathbb{I}$ is trivial, the full stage operator $\mathbb{I} \circ \mathbb{B}$ equals $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$ — the period operator on $m$-space.

### B. The continuation value formulation

The **reverse factoring** $\mathbf{S} = \mathbf{E} \circ \mathbf{M}$ defines the period operator on asset-space values:

$$
(\mathbf{S}\, w)(a) = \mathbb{E}_\theta \Bigl[ \max_{c} \bigl\{ u(c) + \beta\, w\bigl( aR + \theta - c \bigr) \bigr\} \Bigr].
\tag{B$'$}
$$

This operator splits into two self-contained stages:

- **cons stage** ($\mathbf{M}$): $(\mathbf{M}\,w)(m) = \max_c\{u(c) + \beta\, w(m-c)\}$. Pure optimization — no stochastic integration.
- **noport stage** ($\mathbf{E}$): $(\mathbf{E}\,v)(a) = \mathbb{E}_\theta[v(aR + \theta)]$. Pure expectation — no decision.

Each stage is a complete ADC unit with its own perches, transitions, and backward builders. The stages compose via a connector identifying post-consumption assets $a$ with investable assets $k$. The period backward sweep reads right-to-left: $\mathbf{S} = \mathbf{E} \circ \mathbf{M}$.



## 2. Solving Problem B via semiconjugacy
<!-- tags: transform-stachurski, no-port-cons -->

We want to iterate Problem B's modular operator $\mathbf{S} = \mathbf{E} \circ \mathbf{M}$ on asset-space values. Problem A's monolithic operator $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$ acts on cash-on-hand values — the same sub-operators in reverse order. Stachurski's semiconjugate transform connects the two.

> **Definition** (Stachurski 2009, 2022). Dynamical systems $(V, \mathbf{S})$ and $(\hat V, \hat{\mathbf{S}})$ on posets are *order semiconjugate under $\mathbf{F}, \mathbf{G}$* when there exist order-preserving maps $\mathbf{F} \colon V \to \hat V$ and $\mathbf{G} \colon \hat V \to V$ satisfying
>
> $$
> \mathbf{S} = \mathbf{G} \circ \mathbf{F}
> \qquad\text{and}\qquad
> \hat{\mathbf{S}} = \mathbf{F} \circ \mathbf{G}.
> $$

From this, two commuting identities follow:

$$
\mathbf{F} \circ \mathbf{S} = \hat{\mathbf{S}} \circ \mathbf{F}
\qquad\text{and}\qquad
\mathbf{G} \circ \hat{\mathbf{S}} = \mathbf{S} \circ \mathbf{G}.
$$

> **Iterates Lemma.** For all $n \geq 1$,
>
> $$
> \mathbf{S}^n = \mathbf{G} \circ \hat{\mathbf{S}}^{\,n-1} \circ \mathbf{F}
> \qquad\text{and}\qquad
> \hat{\mathbf{S}}^n = \mathbf{F} \circ \mathbf{S}^{\,n-1} \circ \mathbf{G}.
> $$

The proof is by induction on $n$ and uses the key step $\mathbf{F} \circ \mathbf{G} = \hat{\mathbf{S}}$; the concept wiki's entry [semiconjugacy](../../wiki/semiconjugacy.md) states the identity with its source.

### Identifying $\mathbf{F}$, $\mathbf{G}$, $\mathbf{S}$, $\hat{\mathbf{S}}$

| Object                                           | Definition                                                         | Description                   |
| ------------------------------------------------ | ------------------------------------------------------------------ | ----------------------------- |
| $\mathbf{E}$                                     | $(\mathbf{E}\,v)(a) = \mathbb{E}_\theta[v(aR + \theta)]$           | Integration over income shock |
| $\mathbf{M}$                                     | $(\mathbf{M}\,w)(m) = \max_{c \in (0,m)}\{u(c) + \beta\, w(m-c)\}$ | Bellman maximization          |
| $\mathbf{S} = \mathbf{E} \circ \mathbf{M}$       | Problem B's period operator (on $a$-space)                         | optimize, then integrate      |
| $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$ | Problem A's operator (on $m$-space)                                | integrate, then optimize      |
| $\mathbf{F} = \mathbf{M}$                        | $V \to \hat V$ (a-space → m-space)                                 |                               |
| $\mathbf{G} = \mathbf{E}$                        | $\hat V \to V$ (m-space → a-space)                                 |                               |

Check: $\mathbf{S} = \mathbf{G} \circ \mathbf{F} = \mathbf{E} \circ \mathbf{M}$ ✓ and $\hat{\mathbf{S}} = \mathbf{F} \circ \mathbf{G} = \mathbf{M} \circ \mathbf{E}$ ✓. The iterates lemma gives, for the finite-horizon problem:

$$
\mathbf{S}^n = \mathbf{E} \circ (\mathbf{M} \circ \mathbf{E})^{n-1} \circ \mathbf{M}.
$$

Reading right-to-left: apply $\mathbf{M}$ once to the terminal value, iterate $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$ for $n-1$ steps, then apply one final $\mathbf{E}$. Each application of $\hat{\mathbf{S}}$ first integrates ($\mathbf{E}$), then optimizes ($\mathbf{M}$) — EGM-compatible, since $\mathbf{M}$ maximizes over a smooth expected continuation value.

## 3. The syntax

> [!note] The earlier YAML design
> Sections 3 and 4 write the stages in the dolo-plus YAML of the project's earlier design and solve problem A through its translator to Dolo. The dolo-plus files and the translator `doloplus_to_dolo` were archived with that design on 13 September 2026, and the other files the steps name are no longer in the repository, so the steps of §4 cannot be run from this repository. The current stage files of the portfolio-consumption model are under `applications/portfolio-choice/`, and the lesson `tutorials/models/cons-port/03-solving-the-two-orders.ipynb` solves both orders of its portfolio and consumption stages and recovers the portfolio-first order's value from the consumption-first order's.

### 3.1 Problem A: single-stage representation

**Existing Dolo syntax.** The Dolo EGM model represents the full period as a single monolithic step. The state is cash-on-hand $w$ and the transition folds both the decision and the next-period shock into one equation — exactly $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$:

```yaml
# consumption_savings_iid_egm.yaml (existing Dolo format)
symbols:
    exogenous: [y]
    states: [w]
    expectations: [mr]
    poststates: [a]
    controls: [c]
    parameters: [β, γ, σ, ρ, r]

equations:
    transition:
        - w[t] = exp(y[t]) + (w[t-1]-c[t-1])*r

    arbitrage:
        - β*( c[t+1]/c[t] )^(-γ)*r - 1  | 0.0<=c[t]<=w[t]

    half_transition: |
        w[t] = exp(y[t]) + a[t-1]*r

    auxiliary_direct_egm: |
        a[t] = w[t] - c[t]

    reverse_state: |
        w[t] = a[t] + c[t]

    expectation: |
        mr[t] = β*( c[t+1] )^(-γ)*r

    direct_response_egm: |
        c[t] = (mr[t])^(-1/γ)
```

The `transition` equation `w[t] = exp(y[t]) + (w[t-1]-c[t-1])*r` composes the decision ($a = w - c$) with the next-period shock realization ($w' = \exp(y') + a \cdot r$) into a single step — the hallmark of $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$. The Dolo solver internally separates the expectation (`expectation:`) from the policy update (`direct_response_egm:`, `reverse_state:`) to implement EGM, but the YAML presents the problem monolithically.

**dolo-plus ADC form (one-stage).** A dolo-plus `adc-stage` version of the same one-stage dtcc/EGM model stood, before the archive of 13 September 2026, at:

- `packages/dolo/examples/models/doloplus/consumption_savings_iid_egm_doloplus/stage.yaml`

with split-file bindings:

- `calibration.yaml` (parameters), `settings.yaml` (numerical settings), `methodization.yml` (schemes)

An abbreviated excerpt (using Dolo’s parameter name `γ` for CRRA) is:

```yaml
# consumption_savings_iid_egm_doloplus/stage.yaml (abbreviated)
equations:
  arvl_to_dcsn_transition: |
    w = exp(y) + b*r

  dcsn_to_cntn_transition: |
    a = w - c

  cntn_to_dcsn_transition: |
    w = a + c

  cntn_to_dcsn_opr:
    InvEuler: |
      c[>] = (β*dV[>])^(-1/γ)
    MarginalBellman: |
      dV = (c)^(-γ)

  dcsn_to_arvl_opr:
    MarginalBellman: |
      dV[<] = r * E_{y}(dV)
```

Conceptually, this one-stage dolo-plus representation matches the vanilla Dolo dtcc blocks (`half_transition`, `auxiliary_direct_egm`, `reverse_state`, `expectation`, `direct_response_egm`) used by `egm()`. A fully “materialized” translator-ready instance (with `dolo_plus.equation_symbols`, `calibration`, `domain`, `options`) was `docs/old/examples/old/example-dolo-plus-consind-egm.yml`, archived with the design.

### 3.2 Problem B: noport–cons decomposition

The modular operator $\mathbf{S} = \mathbf{E} \circ \mathbf{M}$ factors the period into two stages:

**Stage 1: `noport_stage`** — pure expectation ($\mathbf{E}$), no decision.

```yaml
# noport_stage (abbreviated)
equations:
  arvl_to_dcsn_transition: |
    k_d = k
  dcsn_to_cntn_transition: |
    m = k_d*R + θ

  cntn_to_dcsn_builder:
    Bellman: |
      V = E_{θ}(V[>])
  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

Stage operator: $(\mathbf{E}\,v)(k) = \mathbb{E}_\theta[v(kR + \theta)]$.

**Stage 2: `cons_stage`** — pure optimization ($\mathbf{M}$), no shocks.

```yaml
# cons_stage (abbreviated)
equations:
  arvl_to_dcsn_transition: |
    m_d = m
  dcsn_to_cntn_transition: |
    a = m_d - c

  cntn_to_dcsn_builder:
    Bellman: |
      V = max_{c}(u + β*V[>])
    InvEuler: |
      c[>] = (β*dV[>])^(-1/ρ)
    cntn_to_dcsn_transition: |
      m_d[>] = c[>] + a
    MarginalBellman: |
      dV = (c)^(-ρ)
  dcsn_to_arvl_builder:
    Bellman: |
      V[<] = V
```

Stage operator: $(\mathbf{M}\,w)(m) = \max_{c \in (0,m)} \{u(c) + \beta\, w(m - c)\}$.

The composed period operator reads right-to-left: $\mathbf{S} = \mathbf{E} \circ \mathbf{M}$. The connector $\mathrm{c} \colon a \mapsto k = a$ identifies post-consumption assets with investable assets.

## 4. Solving the finite-horizon problem

### The iterates formula

For $n$ steps back from the terminal period:

$$
\mathbf{S}^n \, w_H = \mathbf{E} \circ (\mathbf{M} \circ \mathbf{E})^{n-1} \circ \mathbf{M} \, w_H.
$$

Reading right-to-left: apply $\mathbf{M}$ once to the terminal value, iterate $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$ for $n-1$ steps, then apply one final $\mathbf{E}$. The inner iterates $(\mathbf{M} \circ \mathbf{E})^{n-1}$ are the conjugate operator $\hat{\mathbf{S}}$ applied $n-1$ times. Each application of $\hat{\mathbf{S}}$:

1. **\(\mathbf{E}\)**: integrate the current \(m\)-space value function \(v(\cdot)\) over the next-period shock to get an \(a\)-space continuation value \(w(a)=\mathbb{E}_\theta[v(aR+\theta)]\),
2. **\(\mathbf{M}\)**: maximize \(u(c) + \beta\, w(m - c)\) over \(c\) (EGM-compatible since \(w\) is a smooth expected continuation value).

**Conceptual seam (level values vs EGM objects).** The semiconjugacy identities above are stated for operators acting on level value functions (\(v, w, V\)). The dtcc/EGM “Dolo horse”, however, does not carry level values explicitly: it propagates a *marginal* object (`dV` in dolo-plus stage syntax, renamed to `mr` in vanilla Dolo) built from the envelope condition \(u'(c)\) and used in the inverse-Euler update. Accordingly, the translator synthesized the Dolo `expectation:` block from the stage’s marginal equations (e.g. `ShadowBellman` / `MarginalBellman`), and EGM’s inner loop accumulates `mr` (its internal `z`) rather than \(V\). This is why the final “\(\mathbf{E}\)” step in the code below returns `mr(a)` on the asset grid, not a level value function.

### Pseudocode

#### Step 1: Translate a one-stage dolo-plus model → vanilla Dolo (dtcc/EGM horse)

The translator `doloplus_to_dolo` (formerly `packages/dolo/dolo/compiler/doloplus_translator/core.py`, archived) converted a dolo-plus `adc-stage` YAML file to a vanilla Dolo dtcc model using external mapping tables.

Translation was driven entirely by the YAML payload (in particular `dolo_plus.equation_symbols`); the split-file attachments (`methodize`, `configure`, `calibrate`) were not consumed by the translator unless they were first materialized into the YAML.

The minimal dolo-plus input the steps read, already “materialized” (has `calibration`, `domain`, `options`, `exogenous`, and `dolo_plus.equation_symbols`), was:

- `docs/old/examples/old/example-dolo-plus-consind-egm.yml`

```python
from dolo.compiler.model_import import yaml_import
from dolo.compiler.doloplus_translator import doloplus_to_dolo

model_plus = yaml_import(
    "docs/old/examples/old/example-dolo-plus-consind-egm.yml",
    compile_functions=False,
)

model = doloplus_to_dolo(
    model_plus,
    mapping_tables="explore/transformations/egm-ADC-to-dolo/mapping_tables.yaml",
    compile_functions=True,
)
```

The expected translated output was documented at `explore/transformations/egm-ADC-to-dolo/transformation_example.yaml`, and a concrete output instance stood at `explore/transformations/egm-ADC-to-dolo/output_dolo.yaml`.

#### Step 2: Provide the terminal/initial decision rule `dr0`

In Dolo, terminal/initial conditions for decision rules are not part of the YAML surface syntax — they are supplied as an *argument* to the solver. For finite-horizon iterates, `dr0` plays the role of the rightmost \(\mathbf{M}\,w_H\) boundary condition in the semiconjugacy formula.

For the simple “no bequest” horizon \(w_H(a)=0\), the terminal maximization is “consume all”, i.e. \(c(m)=m\). We pass that as a decision rule `dr0`:

```python
import numpy as np

H = 50
a_grid = np.linspace(0.01, 10.0, 100)  # poststate grid for EGM

# dr0(i, s) -> controls at (future) state s
# Here: c = w (consume all cash-on-hand).
dr0 = lambda i, s: s
```

#### Step 3: Iterate $\hat{\mathbf{S}}^{H-1}$ with Dolo's EGM solver

With `dr0` from Step 2 as the starting point, iterate the conjugate operator $\hat{\mathbf{S}} = \mathbf{M} \circ \mathbf{E}$ for $H-1$ steps. To force exactly `H-1` iterations (rather than stopping early on convergence), set `η_tol=0`:

```python
from dolo.algos.egm import egm

sol = egm(model, dr0=dr0, a_grid=a_grid, maxit=H-1, η_tol=0.0, verbose=True)
# sol.dr is the final m-space decision rule iterate
```

After `H-1` iterations, `sol.dr` contains the $m$-space policies from $\hat{\mathbf{S}}^{H-1} \circ \mathbf{M}\, w_H$.

#### Step 4: Extract the final expectation output `mr(a)` (the “E-step” of EGM)

Dolo’s `egm()` returns a decision rule `sol.dr`. The expectation output that feeds the inverse-Euler step (often called `z` internally, and `mr` in dtcc models) is formed by the accumulation loop
\(z \mathrel{+}= w \cdot h(M,S,X,p)\).

We can run that **expectation-accumulation half** once and stop, using the compiled gufunctions from the same translated model:

```python
import numpy as np

funs = model.__original_gufunctions__
gt = funs["half_transition"]
h  = funs["expectation"]

dp = sol.dprocess
p  = model.calibration["parameters"]
a  = a_grid[:, None]

# For IID shocks, dp.n_nodes == 1 and i_m=0 is the only current node.
i_m = 0
m = dp.node(i_m)

mr = np.zeros((len(a_grid), 1))
for i_M in range(dp.n_inodes(i_m)):
    w = dp.iweight(i_m, i_M)
    M = dp.inode(i_m, i_M)
    S = gt(m, a, M, p)       # next-period cash-on-hand grid
    X = sol.dr(i_M, S)       # future consumption evaluated at S
    mr += w * h(M, S, X, p)  # accumulate into mr(a)
```

This is exactly the `z += w * h(...)` loop inside `dolo.algos.egm.egm`; we’re just stopping after forming `mr(a)` instead of proceeding to the policy update (`direct_response_egm`, `reverse_state`).

> **Convention note.** Whether `expectation:` computes \(mr = R\cdot\mathbb{E}[u'(c')]\) or \(mr = \beta R\cdot\mathbb{E}[u'(c')]\) is a *mapping-table convention* (β can live in `expectation:` or be applied in `direct_response_egm:`). The loop above always returns whatever object your compiled `h = funs["expectation"]` encodes.

## 5. Implementation agnosticism

The Bellman calculus representation is agnostic to how the sub-operators are executed. Nothing requires stage-by-stage solving:

- **Dolo's EGM solver**, run on the Dolo model the translator produced, can compute $\hat{\mathbf{S}}$ for an entire period as a single compiled step.
- A program that solves **stage by stage** can call the expectation and the maximization as separate compiled steps.
- A **generic operator** can replace $\mathbf{M}$ with policy iteration, marginal value iteration, or any other method with the same inputs and outputs.

The mathematical content — the stages, their transitions, and the semiconjugate relationship between the two orderings — is invariant across all three approaches.

### refs:
- [Semiconjugacy](../../wiki/semiconjugacy.md), the concept wiki's entry, with the iterates identity and its source. #semi-conjugacy
- Stachurski, J. (2009). *Economic Dynamics*. MIT Press.
- Stachurski, J. (2022). *Economic Dynamics*, 2nd ed. MIT Press.
- Sargent, T. J. and Stachurski, J. (2025). *Dynamic Programming*, vol. 2. Manuscript.
