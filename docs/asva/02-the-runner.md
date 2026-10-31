---
audience: user
type: user-guide
topic: [numerical-representation]
---
# The runner

> [!summary]
> The runner, `asva.run`, is used from Python. The variants of a model in a run are its **tests**: a test is a `TestSpec`, which holds a **bundle**, the dictionary from the names of a recipe's slots to the fills bound to them, and a label; `make_test` turns a list of bundles into tests. The slots of a test are the keyword arguments of `load_recipe` and `assemble_trellis` of `bellman.trellis`, so a test selects one variant of the model a recipe describes. `RunSpec` records a run for the reader's script. The reader's own function turns a test into a result, and the other modules of the runner repeat that function over the tests, tabulate, save and estimate.

> [!info]- Relationship with other documents
> **Builds on** — [Recipe functions](../Bellman-Sym/API/factory/spec-factory.md): slots, fills, `load_recipe` and `assemble_trellis`.
> **Used by** — [Parameter sweeps](03-parameter-sweeps.md): the tests as the points of a sweep.
> **See also** — [Asva](index.md) §2: the modules of the package.

## 1 The modules of the runner

| Module | Holds | Page |
|---|---|---|
| `asva.run.types` | `TestSpec`, `SimSpec` and `RunSpec` | §2, §4 |
| `asva.run.make_test` | `make_test` | §2 |
| `asva.run.sweep` | `param_grid`, `sweep` and `SweepResult` | §3; [Parameter sweeps](03-parameter-sweeps.md) |
| `asva.run.metrics` | `format_table`, `write_table` and `write_results_table` | [Parameter sweeps](03-parameter-sweeps.md) §3 |
| `asva.run.mpi` | `get_comm`, `rank_size`, `is_root`, `scatter_items`, `gather_results`, `bcast_item` and `mpi_map` | [Parameter sweeps](03-parameter-sweeps.md) §4 |
| `asva.run.io` | `save_solution` and `load_solution` | [Saving solutions](04-saving-solutions.md) |
| `asva.run.moments` | `make_moment_fn`, `compute_moments_from_panels`, `compute_moments_from_dataframe`, `load_data_moments` and `moment_names` | [Estimation](05-estimation.md) §2, §3 |
| `asva.run.estimate` | `make_criterion`, `estimate`, `diagnostics`, `load_estimation_spec` and `EstimationResult` | [Estimation](05-estimation.md) §4, §5; [The cross-entropy method](06-cross-entropy-method.md) |

## 2 Tests

`TestSpec(slots={}, label="")` is a record that cannot be changed once it is made. `slots` maps the name of a slot, written without its `$`, to the fill bound to it, and `label` names the test in tables. `make_test(slot_bundles)` returns a tuple with one test for each bundle of the list, each with an empty label; an empty list gives one test with no slots, which is the model as its recipe writes it.

The durables registry, the folder `applications/durables/declaration/` ([Model directory layout](../Bellman-Sym/reference/model-directory-layout.md)), holds a recipe, `spec.two-stages.yml`, for the model without its tenure stage, the stage at which the household chooses whether to keep or adjust its housing; it names the slot `$fill` in the calibration list of every stage and in the settings lists of the two consumption stages ([The Bellman factory](../Bellman-Sym/08-bellman-factory.md) §3). Run from the root of the repository, two tests that differ in the discount factor β give two syntactic trellises, the model as written with its fills in place:

```python
from bellman.trellis import load_recipe
from asva.run.make_test import make_test

registry = "applications/durables/declaration"
recipe = "spec.two-stages.yml"

tests = make_test([{"fill": {"β": 0.93}}, {"fill": {"β": 0.95}}])
for test in tests:
    syntactic = load_recipe(registry, recipe, **test.slots)
    print(test.slots, syntactic["periods"][0]["stages"]["adjuster_cons"]["calibration"]["β"])
```

```text
{'fill': {'β': 0.93}} 0.93
{'fill': {'β': 0.95}} 0.95
```

`assemble_trellis(registry, recipe, **test.slots)` of `bellman.trellis` takes the same keywords and goes on to elaborate and bind: it returns the [specified trellis](../wiki/trellis.md) of the test's model, every stage of every period with its calibration, methods and settings bound, which the reader's own code solves. A slot that no test binds contributes nothing, so the tests of a run name only the slots they change ([Recipe functions](../Bellman-Sym/API/factory/spec-factory.md) §2.3).

## 3 Tests over several axes

`param_grid(**axes)`, from `asva.run.sweep`, returns the Cartesian product of named lists of values as a list of dictionaries, the last axis varying fastest. A test set over several axes writes each dictionary of the product into a bundle:

```python
from asva.run.sweep import param_grid
from asva.run.types import TestSpec

points = param_grid(β=[0.93, 0.945], n_a=[300, 500])
tests = tuple(
    TestSpec(
        slots={"fill": {"calibration": {"β": p["β"]}, "settings": {"n_a": p["n_a"]}}},
        label=f"β={p['β']}, n_a={p['n_a']}",
    )
    for p in points
)
print([test.label for test in tests])
```

```text
['β=0.93, n_a=300', 'β=0.93, n_a=500', 'β=0.945, n_a=300', 'β=0.945, n_a=500']
```

A fill keyed by kind, `{"calibration": …, "settings": …}`, is split between the calibration and the settings lists of the recipe, whereas a flat fill that names a parameter and a setting together is refused by `load_recipe` ([Recipe functions](../Bellman-Sym/API/factory/spec-factory.md) §2.3). A test with an empty label is named in tables by its slots: a flat fill as `fill.β=0.93`, and a fill keyed by kind by its kinds alone, `fill.calibration=…,fill.settings=…`, which is why the tests above are given labels.

## 4 The record of a run

`RunSpec` is the record of one run that the reader's script builds and reads. It cannot be changed once it is made, every field is required, and no function of asva reads it. `SimSpec(n_sim, seed, plots)` is the record of a simulation: the number of simulated agents, the seed of the draws and whether plots are drawn.

| Field | Holds |
|---|---|
| `name` | the run's name |
| `base_spec` | the path of the model's specification, such as a registry |
| `output_dir` | the folder the run writes to, such as the model folder's `results/` |
| `run_tag` | a label for the run's files, or `None` |
| `test_set` | the tests, a tuple of `TestSpec` |
| `sweep_runs` | the repetitions of each test in a sweep |
| `warmup` | whether a sweep calls each test once before its repetitions |
| `sim` | a `SimSpec`, or `None` |
| `mode` | the kind of run as a word, `"single"`, `"compare"` or `"sweep"`, which the script reads to decide what to run |
| `extra_args` | the model's own options, by name |
| `verbose`, `trace`, `mpi`, `gpu`, `skip_egm_plots`, `csv_export` | switches, each `True` or `False`, that the script reads |

```python
from pathlib import Path
from asva.run.types import RunSpec

run = RunSpec(
    name="durables", base_spec=Path(registry), output_dir=Path("applications/durables/results"), run_tag=None,
    test_set=tests, sweep_runs=3, warmup=True, sim=None, mode="sweep", extra_args={},
    verbose=False, trace=False, mpi=False, gpu=False, skip_egm_plots=False, csv_export=False,
)
print(run.mode, len(run.test_set))
```

```text
sweep 4
```

With a trial function that assembles and solves the model of one test, `sweep(trial, run.test_set, metric_fns, n_reps=run.sweep_runs, warmup=run.warmup)` runs the tests of the record ([Parameter sweeps](03-parameter-sweeps.md) §1).
