---
audience: user
type: example
topic: [applications]
---
# Formal MDP: No-Portfolio Stage (`noport_stage`)
#no-port-cons
> Source: the stage file `port-with-shocks/library/noport_stage.yaml` of the [earlier dolo-plus YAML design](../index.md); the file is no longer in the repository.

## Rosetta Stone

| DDSL abstract | This stage | YAML |
|---|---|---|
| Arrival state $x_{\prec}$ | $k$ (investable assets) | `prestate: k` |
| Decision state $x$ | $k_d$ (identity) | `states: k_d` |
| Continuation state $x_{\succ}$ | $m$ (cash-on-hand) | `poststates: m` |
| Control $a$ | (none) | — |
| Pre-decision shock $\zeta$ | (none) | — |
| Post-decision shock $\eta$ | $\theta \sim \text{LogNormal}(\mu_\theta, \sigma_\theta)$ | `exogenous: θ` |
| $\mathrm{g}_{\prec\sim}$ | identity: $k_d = k$ | `arvl_to_dcsn_transition` |
| $\mathrm{g}_{\sim\succ}$ | $m = k_d R + \theta$ | `dcsn_to_cntn_transition` |
| $\mathbb{B}$ (decision builder) | $v(k) = \mathbb{E}_\theta[v_{\succ}(kR + \theta)]$ | `cntn_to_dcsn_builder` |
| $\mathbb{I}$ (arrival builder) | $v_{\prec} = v$ (identity) | `dcsn_to_arvl_builder` |

## Model

An agent enters the stage with investable assets $k \in \mathbb{R}_{++}$. There is no decision; the stage serves purely as a shock-realization bridge that converts an asset position into cash-on-hand.

**State space.** $\mathsf X_{\prec} = \mathsf X = \mathbb{R}_{++}$ (assets), $\mathsf X_{\succ} = \mathbb{R}_{++}$ (cash-on-hand). The action set is a singleton (no control).

**Shock process.** A transitory income shock $\theta$ is realized between decision and continuation (post-decision only configuration, $\mathsf Z_{\prec} = \{\varnothing\}$):

$$
\theta \sim \text{LogNormal}(\mu_\theta, \sigma_\theta).
$$

**Transitions.**

$$
\mathrm{g}_{\prec\sim} \colon k \mapsto k_d = k
\qquad\text{(identity)},
\qquad
\mathrm{g}_{\sim\succ} \colon (k_d, \theta) \mapsto m = k_d R + \theta.
$$

## Stage structure

### Perches

| Perch | Variable | Space | Description |
|-------|----------|-------|-------------|
| $\prec$ (arrival) | $k$ | $\mathsf X_{\prec} = \mathbb{R}_{++}$ | Investable assets |
| $\cdot$ (decision) | $k_d$ | $\mathsf X = \mathbb{R}_{++}$ | Investable assets (identity, no choice) |
| $\succ$ (continuation) | $m$ | $\mathsf X_{\succ} = \mathbb{R}_{++}$ | Cash-on-hand (after shock) |

### Filtration

$$
\mathcal F_{\prec} = \mathcal F \subset \mathcal F_{\succ}.
$$

The arrival and decision information sets coincide (no pre-decision shock). The continuation information set is strictly larger: the shock $\theta$ is revealed.

### Builders

**Decision builder $\mathbb{B}$** (cntn → dcsn). Since there is no control, $\mathbb{B}$ is a pure conditional expectation:

$$
(\mathbb{B}\, v_{\succ})(k) = \mathbb{E}_\theta\bigl[v_{\succ}(kR + \theta)\bigr].
$$

**Arrival builder $\mathbb{I}$** (dcsn → arvl). The identity:

$$
v_{\prec}(k) = v(k).
$$

**Stage operator.** $\mathbb{T} = \mathbb{I} \circ \mathbb{B} = \mathbb{B}$, since $\mathbb{I}$ is trivial:

$$
(\mathbb{T}\, v_{\succ})(k) = \mathbb{E}_\theta\bigl[v_{\succ}(kR + \theta)\bigr].
$$

This is the operator $\mathbf{E}$ in the [noport–cons conjugation](../cons-port-stages/solving-conjugates.md).

## Bellman Equation

Since there is no control, the stage Bellman equation reduces to:

$$
v_{\prec}(k) = \mathbb{E}_\theta\bigl[v_{\succ}(kR + \theta)\bigr].
$$

There is no optimization and hence no policy function, no Euler equation, and no first-order conditions.

## Forward Operator

Given a distribution $\mu_{\prec}$ over arrival states $k$, the forward operator pushes $\mu_{\prec}$ through the shock realization:

$$
\mu_{\succ}(A) = \int \Pr(kR + \theta \in A) \, \mathrm{d}\mu_{\prec}(k).
$$

Since the arrival builder is identity, $\mu = \mu_{\prec}$ and the full forward map is $\mathrm{F} = \mathrm{F}_{\succ}$.

## YAML

```yaml
name: noport_stage

symbols:
  spaces:
    Xk: "@def R++"
    Xm: "@def R++"
    Θ:  "@def R++"

  prestate:
    k: "@in Xk"

  exogenous:
    θ:
      - "@in Θ"
      - "@dist LogNormal(μ_θ, σ_θ)"

  states:
    k_d: "@in Xk"

  poststates:
    m: "@in Xm"

  values:
    V[<]: "@in R"
    V: "@in R"
    V[>]: "@in R"

  parameters:
    R: "@in R++"
    μ_θ: "@in R"
    σ_θ: "@in R+"

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

## Calibration

| Symbol | Value | Description |
|---|---|---|
| $R$ | 1.02 | gross risk-free return |
| $\mu_\theta$ | 0.0 | log-mean of transitory income |
| $\sigma_\theta$ | 0.1 | log-std of transitory income |

## See also

- [Solving via conjugation](../cons-port-stages/solving-conjugates.md) — how `noport_stage` ($E$) and `cons_stage` ($M$) compose into the period operator $S = E \circ M$ and relate to the conjugate $\hat S = M \circ E$
- [cons_stage MDP](../formal-mdps/cons_stage_mdp.md)
- [Symbol conventions](../../Bellman-Sym/reference/symbols-conventions.md)
