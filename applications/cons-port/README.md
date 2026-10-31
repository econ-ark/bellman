---
title: "The portfolio-consumption application"
tags:
  - application
date: 2026-10-28
audience: developer
type: index
---

# The portfolio-consumption application

A household consumes out of its resources and divides its savings between a safe asset and a risky one, choosing the share before the risky return and next year's income are drawn. This folder is the model: its consumption and portfolio [[stage|stages]] are written with the maximization alone, each stage file stating the utility, the laws of motion, the feasible set and the argmax, and no marginal value. The numerical method is chosen in the [[methodization|methods files]], each of which names a block file beside it, a file of blocks written in the language of the stage files: `declaration/methods/cons_egm.bl` computes the consumption policy by the endogenous grid method (Carroll 2006), `declaration/methods/port_foc.bl` computes the risky share from its first-order condition, and each states the derivative of the value of its stage.

Two recipes join the stages in the two orders of a [[period]], over six periods: consumption first, `declaration/spec.cons-port.yml`, and portfolio first, `declaration/spec.port-cons.yml`; each names its trellis file beside it, `declaration/trellis.cons-port.yml` and `declaration/trellis.port-cons.yml`.

The command `bellman-workbench applications/cons-port` opens the folder in the Workbench, on the trellis of the recipe `declaration/spec.cons-port.yml`; a click on `declaration/stages/cons/cons.bl` in the tree, or the address `http://localhost:8765/?file=declaration/stages/cons/cons.bl`, shows the consumption stage with its declared builders, and the button `Operative builders` at the foot of the graph shows the builders its method block opens. The desktop application opens the consumption stage from the link `bellman://open?folder=<absolute path>&file=declaration/stages/cons/cons.bl&line=1`, with the folder's absolute path URL-encoded in place of `<absolute path>`.

A program run on this model writes its output into `results/`, which git ignores. The application's acceptance test writes its comparison with the fixed reference into `code/tests/evidence/`, a record kept on purpose.

## The notebooks

The model's three lessons are in the [tutorials collection](../../tutorials/README.md), under Model walkthroughs:

- [`tutorials/models/cons-port/01-two-stages-two-orders.ipynb`](../../tutorials/models/cons-port/01-two-stages-two-orders.ipynb): a consumption stage and a portfolio stage form a [[period]] in either order; the order follows from selected connections between their stage-local [[field|fields]]. Authored [[connector|connectors]] take precedence over inference; an authored cycle is refused.
- [`tutorials/models/cons-port/02-a-life-cycle-built-backwards.ipynb`](../../tutorials/models/cons-port/02-a-life-cycle-built-backwards.ipynb): a life cycle of six periods built backwards from an empty [[trellis]], the list of a model's periods, drawn as it grows and equal to the trellis its recipe writes; nothing is solved.
- [`tutorials/models/cons-port/03-solving-the-two-orders.ipynb`](../../tutorials/models/cons-port/03-solving-the-two-orders.ipynb): both orders solved with a method chosen for each stage, each order's value recovered from the other's, and the method of one stage changed.

The five lessons of Getting started, from [The stage as an object](../../tutorials/getting-started/01-the-stage.ipynb) to [Periods and trellises](../../tutorials/getting-started/05-periods-and-trellises.ipynb), are written on the portfolio-consumption model, and the fourth and fifth read this folder's calibration, methods, settings and recipe files.

The notebook `notebooks/declared-and-operative.ipynb` shows what a method block does to a stage: the declared builders, `stage.declared`, and the operative builders, `stage.builder`, of the consumption and portfolio stages, and the derivative each order of the trellis requires, met and then unmet. The folder `notebooks/port-cons/` keeps the earlier reference notebook, one of the recorded sources of the fixed reference described below.

## The folders

`declaration/` holds the files the language reads: `declaration/stages/<key>/<key>.bl`, the stage files, each with its note `<key>.md` beside it; `declaration/methods/`, the methods files and the block files they name; `declaration/calibration/portfolio.yml`, the parameter values, one mapping for every stage; `declaration/settings/`, the numbers the methods read, among them the spacing of each grid; the two recipes and their trellis files; and the trellis files of records, which name every file of a stage occurrence themselves and are read with no recipe: `trellis.port-cons-vfi.yml`, portfolio first with consumption chosen by a grid search, and the five `trellis.reference-<name>.yml` of the fixed reference. `tests/` holds the tests of the folder's stages, recipes and the solve of both orders; `code/tests/` holds the acceptance tests of the fixed reference and the recorded comparison.

## Connections between stages

The fields `cons.a` and `disc.a` belong to different stage occurrences. The connector `{disc.a: k}` selects the savings after discounting, either within the consumption-first period or between portfolio-first periods; it changes no field's local name. The source needs `disc.` because both stages continue to a field called `a`. The destination `k` is unique and stays bare. The portfolio stage continues to the resources `w` the draws give, which the connector `{w: m}` joins to the resources at which consumption is chosen. The discount stage carries the same local field `a` from its arrival to its continuation while multiplying the backward value by `β`; the derivative values stored with the value pass through the identity law by the same map.

## The tool

[`code/cons_port_tool.py`](code/cons_port_tool.py) is the model's numerical tool. It carries the model's name because it belongs to this application and not to the package: the package constructs the stages and binds their values, methods and settings, and the tool solves the specified trellis. A methods file names, beside each method, its [[handler]], the function of the tool that carries the method out; the tool refuses a handler it does not realize, and every equation it evaluates is one the package compiles from a stage file or a block file.

## The fixed reference

[`reference/legacy/port_cons_h5.npz`](reference/legacy/port_cons_h5.npz) holds 360 arrays that the earlier implementation of the model computed once, five configurations over horizons 0 to 5, described by [its manifest](reference/legacy/port_cons_h5.manifest.json). The five trellis files `declaration/trellis.reference-<name>.yml` reproduce them to 10⁻¹² in four configurations and in structure in the fifth, the grid-search run (items 2 and 3 of [`code/tests/test_cons_port_acceptance.py`](code/tests/test_cons_port_acceptance.py)); [`tests/test_reference_solve.py`](tests/test_reference_solve.py) reproduces the two orders of the recipes on the reference's settings. The one exception is the portfolio share at a level of capital where its objective takes the same value at two adjacent shares: the grid search then chooses between them by the rounding of a sum, which differs with the library numpy uses for linear algebra (OpenBLAS under Python 3.12, Apple's Accelerate under Python 3.14 on macOS), and item 3 accepts a share one step of the grid from the reference's where the objective at the two shares agrees to 10⁻¹⁴ of its size. The portfolio stage of the reference trellis files reads [`declaration/methods/port_reference.yml`](declaration/methods/port_reference.yml), whose two handlers repeat the reference's departures from `port.bl`: its quadrature added the mean of the logarithms of the shocks twice, and its marginal value was the difference quotient of the values.

The reference's recorded sources are not changed: the earlier notebook `notebooks/port-cons/solve_port_cons_ffp.ipynb`, its helper `code/ffp_utils.py`, and the stages, their methods files, the calibration and the settings in the earlier YAML form under `reference/legacy/syntax/`. The one exception is the notebook's first cell, a markdown cell, whose last two lines, a citation of an unpublished research note, were removed on 28 September 2026; no code cell and no output changed. [`code/tests/test_legacy_reference.py`](code/tests/test_legacy_reference.py) checks their digests, the notebook's as it stands since that edit, and that of the reference file.
