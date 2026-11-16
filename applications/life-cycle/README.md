---
title: "Life-cycle household model"
audience: developer
type: index
---
# Life-cycle household model

The household chooses consumption and saving over eight ages, with mortality and a productivity shock before its choice. The stage order follows Section 2, equations (1)–(8), of Bardóczy, Shanker and Velásquez-Giraldo, [*Sequence-Space Jacobians of Life-Cycle Models*](https://www.federalreserve.gov/econres/feds/files/2026046pap.pdf). The numerical example uses selected preference and price parameters from Appendix D, with its own eight-age schedules, three productivity states and 40 asset points. It is a small household comparison, not a replication of the paper's general-equilibrium results.

## Model files

[The recipe](declaration/spec.yml) names five stage declarations. Each period contains entry, mortality, the productivity draw and consumption. The terminal stage closes the last period. Age is a constant field: one supplied value for all productivity and asset states at that step. The consumption stage sends back the preceding age; survival, productivity and income tables are read at that age.

The mortality stage's death branch retains the realized mortality label with the assets left as a bequest. Only the survivor branch connects to the next stage. The entry stage preserves a cohort's supplied state; a newborn distribution is external data. The forward calculation constructs a cohort transition matrix and checks the surviving mass. It does not construct a population path or add newborn cohorts.

## Numerical comparison

From the repository root, with Bellman and the application dependencies installed:

```bash
python applications/life-cycle/code/household.py --terminal-age 8
python -m pytest applications/life-cycle/tests/test_household.py
```

The command supplies terminal age 8 and zero terminal value and marginal value. A program may instead call `solve(trellis, terminal_inputs, terminal_marginal=...)` with its chosen functions and age. The solver checks these inputs before constructing grids or numerical operators.

[household.py](code/household.py) performs elaboration, methodization, calibration and configuration in that order. It evaluates the compiled forward equations, backward value equations, authored derivatives and Euler equations. Numerical handlers perform interpolation and sum the finite distributions that the stages supply.

The terminal stage’s authored grid supplies the points at which the solver evaluates the continuation value and its asset derivative. The terminal builder supplies those points after the solver checks the inputs and before it selects a consumption method.

The application selects the consume-all policy when the represented continuation is asset-independent and the supplied marginal values are zero. It selects the endogenous grid method only when the discounted marginal values on the grid are positive. The application holds endpoint values outside the grid, so a flat row represents an asset-independent function at each productivity. The endogenous grid method retains its differentiability and concavity requirements.

[reference.py](code/reference.py) independently computes the same problem with arrays indexed by age. The comparison covers consumption, savings, all four stage values and marginal values, and every cohort transition matrix. A test deliberately reads income at the wrong age and checks that the comparison detects the change.

The original research calculation can also be compared by supplying its path:

```bash
python applications/life-cycle/code/household.py --terminal-age 8 --research-reference /path/to/check_age_as_a_field.py
```

The [executed notebook](notebooks/life-cycle.ipynb) shows the stage connections, terminal inputs, selected survival and productivity laws, and numerical differences. Its final section leaves space for the reader's observations and decision.
