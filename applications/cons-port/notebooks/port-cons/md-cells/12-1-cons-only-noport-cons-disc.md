<!-- notebook cell 27 | id: cell-11-7bc769d8 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

<div style="border-top: 2px solid rgba(0,0,0,0.15); margin: 2.5em 0 1em;"></div>

## 1. Cons-only (noport → cons → disc)

A simple consumption-savings model with no portfolio choice.
The noport stage realizes income shocks: $m = kR + \theta$.
The cons stage solves:
$\max_c u(c) + \mathrm{v}_\succ(m - c)$.

- Inter-period connector: $\{a \to k\}$ — cons output $a$ becomes noport
  input $k$
- Backward: disc → cons → noport