---
audience: user
type: example
topic: [applications]
---
# Formal MDP: Unemployment Branching Portfolio-Consumption

> Source: the folder of stage files `unemployment_branching_doloplus/` of the [earlier dolo-plus YAML design](../index.md); the folder is no longer in the repository.

## Model

An agent enters the period with investable assets $k \in \mathbb{R}_{++}$. Employment status is then realized exogenously:

- with probability $p_e$, the agent is employed and enters the `worker_port` stage,
- with probability $1-p_e$, the agent is unemployed and enters the `unemployed_port` stage.

In the employed branch, the agent chooses a risky portfolio share $\varsigma \in [0,1]$ before the joint shocks $(\Psi_w, \theta_w)$ are realized. Cash-on-hand is

$$
m = k\bigl(\varsigma \Psi_w + (1-\varsigma)R\bigr) + \theta_w.
$$

In the unemployed branch, the agent chooses a risky portfolio share $\varsigma \in [0,1]$ before a single placeholder return shock $\Psi_u$ is realized. There is no labor-income shock in this branch, so cash-on-hand is

$$
m = k\bigl(\varsigma \Psi_u + (1-\varsigma)R\bigr).
$$

After either branch, the period fans in to a common consumption stage. The agent chooses consumption $c \in (0,m]$, end-of-period assets are

$$
a = m - c,
$$

and the next period is reached via the inter-period connector

$$
\tau : a \mapsto k.
$$

That is, the current continuation field `a` is renamed to the next-period arrival field `k`; this is a wiring map, not a new economic transition equation.

Preferences are CRRA:

$$
u(c) = \frac{c^{1-\rho}}{1-\rho},
$$

with discount factor $\beta \in (0,1)$ and risk-aversion parameter $\rho > 0$.

## Perch-Value Bellman Factorization

Let $\mathrm{v}_{\prec}^{+}(k)$ denote the next-period arrival value function. Under the inter-period connector $\tau : a \mapsto k$, the continuation value entering the current consumption stage is

$$
\mathrm{v}_{\succ}(a) \coloneqq (\tau^{*}\mathrm{v}_{\prec}^{+})(a) = \mathrm{v}_{\prec}^{+}(\tau(a)).
$$

This is the canonical pullback rule from the syntax-semantic composition pages: the predecessor stage consumes a continuation value $\mathrm{v}_{\succ}$, while the successor period provides the arrival value $\mathrm{v}_{\prec}^{+}$.

Let $\mathrm{v}_{\mathrm{cons}}$, $\mathrm{v}_{\mathrm{worker}}$, and $\mathrm{v}_{\mathrm{unemployed}}$ denote the decision-perch values of the three non-trivial stages. Then:

$$
\mathrm{v}_{\mathrm{cons}}(m)
= \max_{0 < c \le m} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta \mathrm{v}_{\succ}(a) \right\},
\qquad a = m-c.
$$

$$
\mathrm{v}_{\mathrm{worker}}(k)
= \max_{\varsigma \in [0,1]} \mathbb{E}_{\Psi_w,\theta_w}\left[\mathrm{v}_{\mathrm{cons}}\!\left(k(\varsigma \Psi_w + (1-\varsigma)R) + \theta_w\right)\right].
$$

$$
\mathrm{v}_{\mathrm{unemployed}}(k)
= \max_{\varsigma \in [0,1]} \mathbb{E}_{\Psi_u}\left[\mathrm{v}_{\mathrm{cons}}\!\left(k(\varsigma \Psi_u + (1-\varsigma)R)\right)\right].
$$

$$
\mathrm{v}(k)
= p_e\, \mathrm{v}_{\mathrm{worker}}(k) + (1-p_e)\, \mathrm{v}_{\mathrm{unemployed}}(k).
$$

## Stage Decomposition

### Employment status

This is a nature-controlled branching stage with arrival state $x_{\prec} = \{k\}$, decision state $x = \{k\}$, and branch-keyed continuation states

$$
x_{\succ,\mathrm{worker}} = \{k_w\}, \qquad x_{\succ,\mathrm{unemployed}} = \{k_u\}.
$$

In the syntax-semantic reading, the equality blocks implicitly define

$$
\mathrm{g}_{\prec\sim}^{\mathrm{empl}}(k_{\prec}) = k_{\prec}, \qquad
\mathrm{g}_{\sim\succ,\mathrm{worker}}^{\mathrm{empl}}(k) = k, \qquad
\mathrm{g}_{\sim\succ,\mathrm{unemployed}}^{\mathrm{empl}}(k) = k.
$$

Equivalently, in SYM surface syntax,

$$
k = k[<], \qquad
k_w[>] = k, \qquad
k_u[>] = k.
$$

The branch-specific continuation-value family is
$\left(\mathrm{v}_{\succ,\mathrm{worker}}, \mathrm{v}_{\succ,\mathrm{unemployed}}\right)$, so the backward builder is the probability-weighted aggregation

In YAML surface syntax, this is the branch family declared by `values.V[>] = {worker: V_worker, unemployed: V_unemployed}`, so the builder reads as `V = p_e*V[>][worker] + (1-p_e)*V[>][unemployed]`.

$$
\mathrm{v}(k)
= p_e\, \mathrm{v}_{\succ,\mathrm{worker}}(k)
+ (1-p_e)\, \mathrm{v}_{\succ,\mathrm{unemployed}}(k),
\qquad
\mathrm{v}_{\prec}(k) = \mathrm{v}(k).
$$

### Worker portfolio

This stage has arrival state $\{k_w\}$, control $\varsigma$, post-decision shocks $(\Psi_w,\theta_w)$, and continuation state $\{m\}$.

Its transition equalities define the implicit maps

$$
\mathrm{g}_{\prec\sim}^{\mathrm{worker}}(k_w) = k_w,
$$

$$
\mathrm{g}_{\sim\succ}^{\mathrm{worker}}(k_d,\varsigma,\Psi_w,\theta_w)
= k_d(\varsigma \Psi_w + (1-\varsigma)R) + \theta_w.
$$

Equivalently, the SYM equations are $k_d = k_w$ and $m = k_d(\varsigma \Psi_w + (1-\varsigma)R) + \theta_w$.

Because the shocks are realized after the portfolio decision, the expectation sits inside `cntn_to_dcsn_builder`, not in `dcsn_to_arvl_builder`. The backward recursion is

$$
\mathrm{v}_{\mathrm{worker}}(k_d)
= \max_{\varsigma \in [0,1]}
\mathbb{E}_{\Psi_w,\theta_w}\left[
\mathrm{v}_{\succ}\!\left(\mathrm{g}_{\sim\succ}^{\mathrm{worker}}(k_d,\varsigma,\Psi_w,\theta_w)\right)
\right],
\qquad
\mathrm{v}_{\prec,\mathrm{worker}}(k_w) = \mathrm{v}_{\mathrm{worker}}(k_w).
$$

### Unemployed portfolio

This stage has arrival state $\{k_u\}$, control $\varsigma$, shock $\Psi_u$, and continuation state $\{m\}$.

Its transition equalities define

$$
\mathrm{g}_{\prec\sim}^{\mathrm{unemployed}}(k_u) = k_u,
$$

$$
\mathrm{g}_{\sim\succ}^{\mathrm{unemployed}}(k_d,\varsigma,\Psi_u)
= k_d(\varsigma \Psi_u + (1-\varsigma)R).
$$

Equivalently, the SYM equations are $k_d = k_u$ and $m = k_d(\varsigma \Psi_u + (1-\varsigma)R)$.

Its backward recursion is

$$
\mathrm{v}_{\mathrm{unemployed}}(k_d)
= \max_{\varsigma \in [0,1]}
\mathbb{E}_{\Psi_u}\left[
\mathrm{v}_{\succ}\!\left(\mathrm{g}_{\sim\succ}^{\mathrm{unemployed}}(k_d,\varsigma,\Psi_u)\right)
\right],
\qquad
\mathrm{v}_{\prec,\mathrm{unemployed}}(k_u) = \mathrm{v}_{\mathrm{unemployed}}(k_u).
$$

### Consumption

This stage has arrival state $\{m\}$, control $c$, and continuation state $\{a\}$.

Its transition equalities define

$$
\mathrm{g}_{\prec\sim}^{\mathrm{cons}}(m) = m, \qquad
\mathrm{g}_{\sim\succ}^{\mathrm{cons}}(m_d,c) = m_d - c.
$$

Equivalently, the SYM equations are $m_d = m$ and $a = m_d - c$.

Its backward builder is

$$
\mathrm{v}_{\mathrm{cons}}(m_d)
= \max_{0 < c \le m_d} \left\{ \frac{c^{1-\rho}}{1-\rho} + \beta \mathrm{v}_{\succ}(a) \right\},
\qquad
\mathrm{v}_{\prec,\mathrm{cons}}(m) = \mathrm{v}_{\mathrm{cons}}(m).
$$

The EGM representation uses the marginal continuation value $\partial_a \mathrm{v}_{\succ}(a)$ and the inverse map associated with $\mathrm{g}_{\sim\succ}^{\mathrm{cons}}$:

$$
c(a) = \left(\beta\,\partial_a \mathrm{v}_{\succ}(a)\right)^{-1/\rho},
$$

and

$$
\left(\mathrm{g}_{\sim\succ}^{\mathrm{cons}}\right)^{-1}(a,c) = a + c.
$$

## Composition and Wiring

The period wiring is

```text
employment_status -> worker_port      -> cons_stage
employment_status -> unemployed_port  -> cons_stage
```

The branching stage fans out via the disjoint continuation fields `k_w` and `k_u`. The two portfolio stages then fan in to the shared arrival field `m` of `cons_stage`. In the syntax-semantic composition rules, this is an identity composition on a common arrival space: both upstream stages expose the same continuation field `m`, so no intra-period connector is needed.

The inter-period connector is the standard rename

```yaml
{a: k}
```

so the next period starts again from investable assets `k`. This inter-period connector induces the pullback $\mathrm{v}_{\succ} = \tau^{*}\mathrm{v}_{\prec}^{+}$ used in the Bellman factorization above.

## Calibration

| Symbol | Value | Description |
|---|---|---|
| $\beta$ | 0.96 | discount factor |
| $\rho$ | 2.0 | CRRA risk aversion |
| $R$ | 1.02 | gross risk-free return |
| $p_e$ | 0.95 | employment probability |
| $\mu_{\Psi_w}$ | 0.04 | worker risky-return log-mean |
| $\sigma_{\Psi_w}$ | 0.15 | worker risky-return log-std |
| $\mu_{\theta_w}$ | 0.0 | worker labor-income log-mean |
| $\sigma_{\theta_w}$ | 0.10 | worker labor-income log-std |
| $\rho_{\zeta_w}$ | 0.0 | worker shock-correlation placeholder |
| $\mu_{\Psi_u}$ | 0.04 | unemployed risky-return log-mean |
| $\sigma_{\Psi_u}$ | 0.15 | unemployed risky-return log-std |
