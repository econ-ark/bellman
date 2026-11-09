---
title: "The consumption–savings stage with independent income"
audience: developer
type: index
---
# The consumption–savings stage with independent income

A household chooses its consumption out of its cash on hand and saves the rest at a fixed return, its income drawn independently each period and zero with a small probability.

The stage file `declaration/stages/cons_savings_iid/cons_savings_iid.bl` states the model. The methods file `methods.bl` beside it is an addition to the stage file, which selects the numerical methods, and `declaration/settings/cons_savings_iid.yml` gives the values of the settings those methods read. The folder holds no recipe, so `load_stage` is given the stage file and the methods file together.

The command `bellman-workbench applications/consumption-savings-iid` opens the model in the Workbench.

A program run on this model writes its output into `results/`, which git ignores.
