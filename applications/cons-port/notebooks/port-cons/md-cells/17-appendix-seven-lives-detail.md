<!-- notebook cell 41 | id: mhvxl2lusj -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

<div style="border-top: 2px solid rgba(0,0,0,0.15); margin: 2.5em 0 1em;"></div>

## Appendix: seven lives detail

| # | Level | What happens | Object | Source |
|---|-------|-------------|--------|--------|
| 1 | **Symbolic** | YAML parsed into symbols, equations, spaces | `dict` (raw parse tree) | `cons_stage.yaml` |
| 2 | **Parameterized** | Parameter values bound ($\beta$, $\rho$, $R$, ...) | `stage.param` | `calibration.yaml` |
| 3 | **Methodized** | Solution method attached (`!egm`, `!vfi`, ...) | `stage.methods` | `cons_stage_methods.yml` |
| 4 | **Configured** | Numerical settings bound (grid sizes, tolerances) | `stage.settings` | `settings.yaml` |
| 5 | **Callable** | Grids, interpolants, quadrature nodes built | `np.ndarray`, `interp1d` | builder code |
| 6 | **Solved** | Bellman operator iterated to convergence | `ValueFn` (policy + value) | builder code |
| 7 | **Simulated** | Policy applied to generate paths / distributions | `np.ndarray` (paths) | builder code |

Steps 1–4 produce a fully specified stage object (syntax layer).
Step 5 builds callable computational objects (representation).
Steps 6–7 are application (Backus): applying the callables to produce solutions and simulations.