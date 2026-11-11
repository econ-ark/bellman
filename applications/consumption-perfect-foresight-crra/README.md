---
title: "The perfect foresight consumption stage with CRRA utility"
audience: developer
type: index
---
# The perfect foresight consumption stage with CRRA utility

A household with CRRA utility and no uncertainty, whose permanent income grows at a fixed factor, chooses its consumption out of its market resources and saves the rest at a fixed return; its consumption function is known in closed form, a fixed fraction of its total wealth.

The stage file `declaration/stages/perfect_foresight/perfect_foresight.bl` states the model, with three derived parameters: the return patience factor q, human wealth h and the natural borrowing limit L = 1 − h. Two methods files stand beside it. The addition `methods.bl` solves the model in closed form: it types `!explicit` on the policy builder and on the two value builders, whose lines write the consumption function κ(m − L), the decision value and the arrival value, each value with its marginal; the marginal propensity to consume κ = 1 − q is a derived parameter it defines. The replacing selection `methods.egm.bl` solves it by the endogenous grid method on a grid of savings, whose three settings the program supplies, so the folder holds no settings file. `declaration/calibration/perfect_foresight.yml` gives the parameter values of the book's example. The economics, the closed form and the conditions under which it holds are in `economics.md`; the stage file and its methods files are explained in `declaration/stages/perfect_foresight/perfect_foresight.md`.

The module `code/closed_form_check.py` binds both methods through `elaborate`, `methodize`, `calibrate` and `configure`, evaluates the closed form through its compiled kernels, the record of `closed_form` holding `return_patience`, `κ`, `h`, `limit`, `consumption`, `value`, `marginal`, `arrival_value` and `arrival_marginal`, iterates the endogenous grid method on the compiled kernels of its lines, and supplies the scalar Linear and PCHIP evaluators with which both are compared. The notebook `code/closed-form-and-grid.ipynb` shows each step and each comparison.

The command `bellman-workbench applications/consumption-perfect-foresight-crra` opens the model in the Workbench.

A program run on this model writes its output into `results/`, which git ignores.
