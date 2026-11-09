---
audience: user
type: example
topic: [applications]
---
# Pensions and retirement

A worker holds financial and pension assets and receives uncertain earnings. The worker chooses consumption and pension contributions before deciding whether to work or retire next period. Retirement is irreversible. On retirement, the pension balance is paid out once, while a benefit continues each period.

## 1 The decision sequence

The declaration separates three [stages](../../wiki/stage.md), each stating one decision problem. `worker_saving` writes consumption and contributions; `retire_choice` writes the choice of next period's employment status; `retiree_saving` writes consumption and saving after retirement. A terminal stage specifies the end of the horizon.

The retirement-choice stage passes financial and pension balances to the work or retire branch. The connections between periods determine which saving stage follows. This makes the order of saving and retirement decisions available for inspection separately from any numerical method.

## 2 Inspect the declaration

Read [the retirement-choice stage](https://github.com/econ-ark/bellman/blob/main/applications/pension-retirement/declaration/stages/retire_choice/retire_choice.bl) and the [model's source notes](https://github.com/econ-ark/bellman/blob/main/applications/pension-retirement/economics.md). The files are in `applications/pension-retirement/`; [Bellman Workbench](../../overview/07-workbench.md) displays their equations, quantities and diagrams.

Calibration and numerical settings are not supplied. The contribution incentive and terminal value still require confirmation against the model's source. Inspect the declaration as an illustrative model; this page reports no numerical solution.
