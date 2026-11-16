---
title: "The perfect foresight consumption stage with CRRA utility"
audience: developer
type: index
---
# The perfect foresight consumption stage with CRRA utility

A household with constant relative risk aversion chooses consumption from its market resources and saves the rest at a fixed return. Permanent income grows at a known factor. At the stationary solution, consumption is a fixed fraction of total wealth.

The stage file `declaration/stages/perfect_foresight/perfect_foresight.bl` sends human wealth backward as a constant field. It takes in `h[>]`, computes `h = 1 + h[>]`, and sends `h[<] = h*Γ/R`. Feasibility requires `c < m + h[>]`. Only the return patience factor `q` is a derived stage parameter.

Two methods files stand beside the stage:

- `methods.bl` gives the stationary closed form. Its derived parameters are the marginal propensity to consume `κ`, human wealth `h_lim`, and the borrowing limit `L_lim`. Its positive finite human wealth requires `Γ < R`.
- `methods.egm.bl` selects the endogenous grid method on savings points. The program supplies its three grid settings. With finite continuation inputs, one backward step also admits `Γ >= R`.

The calibration remains in `declaration/calibration/perfect_foresight.yml`. [The economics](economics.md) gives the stationary solution and its conditions. [The stage description](declaration/stages/perfect_foresight/perfect_foresight.md) explains the declarations and methods.

The module `code/closed_form_check.py` calls `elaborate`, `methodize`, `calibrate`, and `configure` separately. Every numerical route checks the complete continuation mapping before constructing kernels or grids. The returned `input_conditions` retain callable conditions that the package cannot decide.

`closed_form` evaluates the compiled stationary solution. `gridded_route` iterates the endogenous grid method to its stationary solution. `gridded_step` computes one backward step for supplied continuation value, human wealth, and marginal value. The notebook `code/closed-form-and-grid.ipynb` shows these computations and the human-wealth recursion.

The command `bellman-workbench applications/consumption-perfect-foresight-crra` opens the model in the Workbench. Programs write output into `results/`, which git ignores.
