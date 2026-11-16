!!! example "Running example: buffer-stock consumption–savings"

    An agent arrives at date $t$ holding **beginning-of-period assets** $k_t$. A shock then resolves, a gross (constant) return $R$ on those assets together with a labour-income draw $y_t$ leaves **market resources** (cash-on-hand) $m_t = R\, k_t + y_t$. Out of $m_t$ the agent chooses **consumption** $c_t$ subject to $0 < c_t \le m_t$, enjoys utility $\mathrm{u}(c_t)$ (say CRRA, $\mathrm{u}(c_t) = c_t^{1-\rho}/(1-\rho)$ for $\rho>0$, $\rho\ne1$), and carries the remainder forward as **assets** $a_t = m_t - c_t$, which become next period's beginning-of-period assets $k_{t+1} = a_t$.

    The problem has a finite horizon, and we solve by **backward induction** starting at the last period. At the terminal date $T$ nothing follows, so the agent consumes everything available, $\mathrm{v}_T(m_T) = \mathrm{u}(m_T)$, attained at $c_T = m_T$ (a bequest motive would replace this terminal condition without changing what follows). At a generic date $t$, with discount factor $\beta \in (0,1)$, this backward step defines the **primal Bellman equation**, written with time $t$ **market resources** as the **decision state**. The agent decides on,

    $$
    \mathrm{v}_t(m_t)
    = \sup_{0 < c_t \le m_t}
    \Bigl\{
    \mathrm{u}(c_t)
    + \beta\, \mathbb{E}\bigl[\mathrm{v}_{t+1}(m_{t+1})\bigr]
    \Bigr\},
    \qquad m_{t+1} \;=\; R\,(m_t - c_t) + y_{t+1},
    $$

    where the next period's state $m_{t+1}$ is produced by a transition from the current state, the savings choice $a_t = m_t - c_t$, and the **next-period shock** $y_{t+1}$ realised at the start of next period. The expectation is taken over $y_{t+1}$, a *fresh, next-period* draw of the same income process that produced the current $m_t$ through $m_t = R\, k_t + y_t$, not the $y_t$ already baked into $m_t$. In the running example this same draw becomes the next stage's *pre-decision* shock.

    These date subscripts distinguish successive value fields. Each backward step applies the same declared operator to the next tuple; the operator itself has no date argument. The terminal tuple is supplied when the model is realized.
