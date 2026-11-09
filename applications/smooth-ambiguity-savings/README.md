---
title: "Smooth-ambiguity savings"
audience: developer
type: index
---
# Smooth-ambiguity savings

A household chooses its consumption out of its resources and saves the rest at a lognormal return whose mean is uncertain, with risk aversion, ambiguity aversion and the elasticity of intertemporal substitution separate.

The stage file `declaration/stages/sa_savings/sa_savings.bl` states the model. The methods file `methods.bl` beside it is an addition to the stage file, which selects the numerical methods, and `declaration/settings/sa_savings.yml` gives the values of the settings those methods read. The folder holds no recipe, so `load_stage` is given the stage file and the methods file together.

The command `bellman-workbench applications/smooth-ambiguity-savings` opens the model in the Workbench.

A program run on this model writes its output into `results/`, which git ignores.
