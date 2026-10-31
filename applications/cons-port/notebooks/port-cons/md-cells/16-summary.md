<!-- notebook cell 40 | id: cell-17 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

<div style="border-top: 2px solid rgba(0,0,0,0.15); margin: 2.5em 0 1em;"></div>

## Summary

| Config | Stages | Key feature |
|--------|--------|------------|
| **Cons-only** | noport, cons | Income shocks only |
| **Beg-returns** | port, cons | Returns then consumption |
| **End-returns** | cons, port | Consumption then investment |
| **Port-only** | port | Pure Merton portfolio |

The design principles — modular operators, connector-driven
solve order, equations from the stage syntax — are
exercised throughout.

### References

- Backus, J. (1978). [Can Programming Be Liberated from the
  von Neumann Style? A Functional Style and Its Algebra of
  Programs.](https://dl.acm.org/doi/10.1145/359576.359579)
  *Communications of the ACM*, 21(8), 613–641.
- Carroll, C. D. (2006). *The Method of Endogenous
  Gridpoints for Solving Dynamic Stochastic Optimization
  Problems.* Economics Letters, 91(3).
- Sargent, T. J. & Stachurski, J. (2022).
  [*Economic and Financial Decisions under
  Uncertainty.*](https://johnstachurski.net/efd) Princeton
  University Press.
- Sargent, T. J. & Stachurski, J. (2026).
  *Dynamic Programming: General States.* Cambridge
  University Press.
- Bellman calculus foundations:
  `docs/theory/ddsl-foundations/` and
  `docs/theory/ddsl-foundations/core-ddsl-FFP-concepts.md`