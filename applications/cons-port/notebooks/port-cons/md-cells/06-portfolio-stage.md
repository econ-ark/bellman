<!-- notebook cell 10 | id: p134dqzlqds -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

### Portfolio stage

A stochastic portfolio allocation decision. The agent enters
with investable wealth $k \in \mathbb{R}_{++}$, chooses risky
share $\varsigma \in [0,1]$, then realizes a post-decision
shock $\zeta = (\Psi, \theta)$ drawn from a bivariate
log-normal.

**Transition** (decision to continuation).

$$
m = k_d\bigl(\varsigma \Psi + (1-\varsigma)R\bigr) + \theta
$$

**Bellman equation** (decision perch).

$$
\mathrm{v}(k_d) = \max_{\varsigma \in [0,1]}
\;\mathbb{E}_{\Psi,\theta}
\!\left[
  \mathrm{v}_\succ\!\bigl(
    k_d(\varsigma \Psi + (1-\varsigma)R) + \theta
  \bigr)
\right]
$$

The arrival-to-decision transition is identity ($k_d = k$).
Shock timing is post-decision.