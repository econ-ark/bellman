<!-- notebook cell 4 | id: bab0nyjnu7e -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

### Consumption stage

This stage is a deterministic consumption–savings decision. The agent enters
with cash-on-hand $m \in \mathbb{R}_{++}$ at the arrival perch, the cash on hand is transformed to the decision stage by the transition function $m_d = m$. 
At the decision perch, the agent chooses consumption $c \in (0, m_d)$ at the decision perch, and exits with post-consumption assets $a = m - c$, where $a$ is the continuation state. 

In general, if the state transition is an identity, we can use the same variable name for the source and target perch and do not explicitly need to write out the transition function.  However, we are going to do so here to demonstrate the information structure of the stage in a simple example. 

The continuation value function is given by $\mathrm{v}_{\succ}$, and the transformation (`builder`) from the continuation perch to the decision perch is given by the maximization problem:

$$
\mathrm{v}_{\sim}(m_d) = \max_{c \in (0,\, m_d)}
\left\{
  \frac{c^{1-\rho}}{1-\rho}
  + \, \mathrm{v}_\succ(m_d - c)
\right\}
$$

Since the arrival-to-decision transition is identity ($m_d = m$), the arrival value is $\mathrm{v}_\prec(m) = \mathrm{v}_{\sim}(m)$. Thus the Bellman operator of the stage. This maximization defines the backward decision builder $\mathbb{G}$; since the arrival transition is identity, the arrival builder $\mathbb{I}$ is trivial, and the stage operator is $\mathbb{S} = \mathbb{I} \circ \mathbb{G}$.

**EGM representation (inverse Euler).**

$$
\mathrm{c}_{\succ}(a) = \bigl(\beta \, \partial\mathrm{v}_\succ(a)\bigr)^{-1/\rho},
\qquad
\mathrm{m}_{\succ}(a) = a + \mathrm{c}_{\succ}(a)
$$

Importantly, consumption here is a function of the continuation state $a$, so the above equation defines a function $\mathrm{c}_{\succ}$ to represent it (this is the consumed function). One way to view EGM is that it involves inverting an approximation of $\mathrm{m}_{\succ}(a)$ by interpolation to recover the decision policy $\mathrm{c}(m)$.

Let's use matsya to convert this math description into a `dolo-plus` stage YAML. First we write out the decription as text. 
