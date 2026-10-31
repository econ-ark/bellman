<!-- notebook cell 29 | id: cell-16 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

<div style="border-top: 2px solid rgba(0,0,0,0.15); margin: 2.5em 0 1em;"></div>

## 2. Beginning-returns (port → cons → disc, EGM)

The classic portfolio-consumption model with beginning-of-period
returns. Portfolio stage solves:
$\mathrm{v}(k) = \max_\varsigma \mathbb{E}_{\Psi,\theta}[\mathrm{v}_\succ(k(\varsigma\Psi + (1-\varsigma)R) + \theta)]$.
Cons stage solves:
$\max_c u(c) + \mathrm{v}_\succ(m - c)$.

- No intra-period connector (port output $m$ = cons input $m$)
- Inter-period connector: $\{a \to k\}$
- Backward: disc → cons → port