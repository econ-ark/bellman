---
title: "Epstein–Zin savings"
audience: developer
type: index
---
# Epstein–Zin savings

A household with Epstein–Zin preferences chooses its consumption out of its resources and saves the rest at a lognormal gross return drawn after the decision.

The stage file `declaration/stages/ez_savings/ez_savings.bl` states the model. The methods file `methods.bl` beside it is an addition to the stage file, which selects the numerical methods, and `declaration/settings/ez_savings.yml` gives the values of the settings those methods read. The folder holds no recipe, so `load_stage` is given the stage file and the methods file together.

The command `bellman-workbench applications/epstein-zin-savings` opens the model in the Workbench.

A program run on this model writes its output into `results/`, which git ignores.
