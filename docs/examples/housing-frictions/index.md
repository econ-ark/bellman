---
audience: user
type: example
topic: [applications]
---
# Housing adjustment

A household holds financial assets and housing. After observing income, it chooses whether to keep its home or adjust its housing stock. Both paths include consumption and saving; the adjustment path also chooses a new housing stock and pays a proportional adjustment cost.

## 1 The choice shown

The homepage diagram shows the forward part of `house_choice`, the [stage](../../wiki/stage.md) that states the keep-or-adjust decision. It shows how incoming assets and earnings determine available resources, then how the two branches pass quantities to their respective saving stages. The Source tab shows the same forward declaration.

On the keep branch, housing remains available alongside financial resources. On the adjust branch, the existing house's value becomes available to finance consumption, saving and new housing. These later choices are written separately in `keeper_saving` and `adjuster_saving`.

## 2 Inspect the declaration

Read [the choice stage](https://github.com/econ-ark/bellman/blob/main/applications/housing-frictions/declaration/stages/house_choice/house_choice.bl) and the [model's source notes](https://github.com/econ-ark/bellman/blob/main/applications/housing-frictions/economics.md). The files are in `applications/housing-frictions/`; [Bellman Workbench](../../overview/07-workbench.md) displays their equations, quantities and diagrams.

The earnings profile, terminal value and consumption-utility exponent still require confirmation against the model's source, as the notes explain. This example is for inspecting the declaration; it reports no numerical solution.
