---
title: "The buffer-stock consumption stage"
audience: developer
type: index
---
# The buffer-stock consumption stage

A household whose income is hit by a permanent shock and by a transitory shock that is zero with a small probability chooses its consumption out of its market resources and saves the rest.

The stage file `declaration/stages/buffer_stock/buffer_stock.bl` states the model. The methods file `methods.bl` beside it is an addition to the stage file, which selects the numerical methods, and `declaration/settings/buffer_stock.yml` gives the values of the settings those methods read. The folder holds no recipe, so `load_stage` is given the stage file and the methods file together.

The command `bellman-workbench applications/buffer-stock` opens the model in the Workbench.

A program run on this model writes its output into `results/`, which git ignores.
