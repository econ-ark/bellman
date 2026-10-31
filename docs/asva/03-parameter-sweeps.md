---
audience: user
type: user-guide
topic: [numerical-representation]
---
# Parameter sweeps

> [!summary]
> `sweep(solve_fn, points, metric_fns)` calls the reader's function at every point of a list, repeats each call, keeps at each point the repetition that is best by the first metric, and returns one `SweepResult` per point. The points are dictionaries from `param_grid` or tests from [The runner](02-the-runner.md). `write_results_table` writes the results of a sweep over tests as a Markdown or LaTeX table, and `format_table` and `write_table` format any list of dictionaries. Given an MPI communicator, the object through which the processes of a program run under MPI exchange data, `sweep` divides the points among the processes and collects the results on the first of them.

> [!info]- Relationship with other documents
> **Builds on** — [The runner](02-the-runner.md): tests and `param_grid`.
> **Used by** — [The cross-entropy method](06-cross-entropy-method.md) §3: the functions of MPI that §4 states.

## 1 Running a sweep

```python
sweep(solve_fn, points, metric_fns, n_reps=3, warmup=True, best="min", on_error="raise", verbose=True, comm=None)
```

| Argument | Default | Meaning |
|---|---|---|
| `solve_fn` | | the reader's function of one point, returning any result |
| `points` | | the list of points, dictionaries or tests |
| `metric_fns` | | a dictionary of named functions, each from a result to a number; the first is the **primary metric** |
| `n_reps` | `3` | the number of repetitions at each point |
| `warmup` | `True` | whether `solve_fn` is called once at each point before the repetitions, its result discarded, so that the time of compilation and of reading files falls outside them |
| `best` | `"min"` | `"min"` keeps the repetition with the lowest primary metric, `"max"` the one with the highest |
| `on_error` | `"raise"` | `"raise"` stops at the first exception; `"skip"` issues a warning and continues |
| `verbose` | `True` | whether each point and each repetition are printed, by the process of rank 0 (§4) |
| `comm` | `None` | an MPI communicator, which divides the points among processes (§4) |

At each point `sweep` makes the warm-up call when `warmup` is true and then `n_reps` calls, evaluating every metric function on each result, and it keeps the metrics and the result of the repetition whose primary metric is best. It returns a list of `SweepResult(point, metrics, result)`, one for each point in the order of the points: `metrics` are the best repetition's metrics, not averages over the repetitions, and `result` is that repetition's result. With `on_error="skip"`, a failed call gives NaN for every metric, and a point at which every repetition failed has NaN metrics and the result `None`.

The example computes the mean of a lognormal income shock, $E[e^{\sigma\varepsilon}] = e^{\sigma^2/2}$ with $\varepsilon$ standard normal and $\sigma = 0.5$, by Gauss–Hermite quadrature with two, four and six nodes, and records the time of each computation and its error:

```python
import time
import numpy as np
from asva.run.sweep import param_grid, sweep

σ = 0.5

def solve(point):
    start = time.perf_counter()
    nodes, weights = np.polynomial.hermite.hermgauss(point["n_nodes"])
    mean = (weights * np.exp(σ * np.sqrt(2.0) * nodes)).sum() / np.sqrt(np.pi)
    return {"seconds": time.perf_counter() - start, "mean": mean}

metric_fns = {
    "seconds": lambda r: r["seconds"],
    "error": lambda r: abs(r["mean"] - np.exp(σ ** 2 / 2)),
}
results = sweep(solve, param_grid(n_nodes=[2, 4, 6]), metric_fns, verbose=False)
for r in results:
    print(r.point, f"error {r.metrics['error']:.1e}")
```

```text
{'n_nodes': 2} error 5.5e-03
{'n_nodes': 4} error 2.5e-06
{'n_nodes': 6} error 3.9e-10
```

The primary metric is the time, so each point keeps the fastest of its three repetitions; the error is the same in every repetition.

## 2 Sweeping over tests

A sweep over the tests of [The runner](02-the-runner.md) passes each test to the reader's function, which reads its slots. The function of a model assembles the test's model with `assemble_trellis(registry, recipe, **test.slots)` of `bellman.trellis` and solves it with the reader's own code; here the slot `quadrature` holds the number of nodes of the example of §1, and each test has its label:

```python
from asva.run.types import TestSpec

tests = [TestSpec(slots={"quadrature": {"n_nodes": n}}, label=f"{n} nodes") for n in (2, 4, 6)]
results = sweep(
    lambda test: solve(test.slots["quadrature"]),
    tests,
    {"error": metric_fns["error"]},
    verbose=False,
)
print([(r.point.label, f"{r.metrics['error']:.1e}") for r in results])
```

```text
[('2 nodes', '5.5e-03'), ('4 nodes', '2.5e-06'), ('6 nodes', '3.9e-10')]
```

## 3 Tables

`format_table(rows, columns, fmt="markdown", float_fmt=".4f", caption=None)` returns a table of a list of dictionaries as text: in Markdown, or, with `fmt="latex"`, as a LaTeX `table` environment with the rules of the `booktabs` package and the caption when one is given. A floating-point number is formatted by `float_fmt` and any other value by `str`, and a column that a row lacks is left empty in that row. `write_table(path, rows, columns, fmt="markdown", **kwargs)` writes the same table to a file and creates the folders its path names; its further keywords, `float_fmt` and `caption`, are those of `format_table`. The results of `sweep` are not dictionaries, so a sweep over dictionaries is tabulated from `{**r.point, **r.metrics}`:

```python
from asva.run.metrics import format_table

rows = [{**r.point, **r.metrics} for r in sweep(solve, param_grid(n_nodes=[2, 4, 6]), metric_fns, verbose=False)]
print(format_table(rows, ["n_nodes", "error"], float_fmt=".1e"))
print(format_table(rows, ["n_nodes", "error"], fmt="latex", float_fmt=".1e", caption="Quadrature error"))
```

```text
| n_nodes | error   |
|---------|---------|
|       2 | 5.5e-03 |
|       4 | 2.5e-06 |
|       6 | 3.9e-10 |
\begin{table}[htbp]
\centering
\begin{tabular}{ll}
\toprule
n\_nodes & error \\
\midrule
2 & 5.5e-03 \\
4 & 2.5e-06 \\
6 & 3.9e-10 \\
\bottomrule
\end{tabular}
\caption{Quadrature error}
\end{table}
```

`write_results_table(results, path, fmt="markdown", float_fmt=".4f", display_max_label=200)` writes the results of a sweep over tests. Its first column holds each test's label, or, when the label is empty, the label derived from the test's slots ([The runner](02-the-runner.md) §3), cut to `display_max_label` characters; the other columns hold the metrics in alphabetical order. A result whose point is not a test is refused with `TypeError`.

```python
from asva.run.metrics import write_results_table

write_results_table(results, "tables/quadrature.md", float_fmt=".1e")
print(open("tables/quadrature.md").read())
```

```text
| label   | error   |
|---------|---------|
| 2 nodes | 5.5e-03 |
| 4 nodes | 2.5e-06 |
| 6 nodes | 3.9e-10 |
```

## 4 Processes

The functions of `asva.run.mpi` use the package `mpi4py` when it is installed. The processes of a program run under MPI are numbered from 0, the number of a process being its **rank**. A **communicator** is the object through which a group of processes exchange data; `get_comm()` returns the communicator of all the processes of the program, `MPI.COMM_WORLD`, or `None` when `mpi4py` is not installed; every function below takes `comm=None` to mean one process.

| Function | Returns |
|---|---|
| `get_comm()` | `MPI.COMM_WORLD`, or `None` without `mpi4py` |
| `rank_size(comm=None)` | the pair (rank of this process, number of processes); `(0, 1)` without a communicator |
| `is_root(comm=None)` | whether this process has rank 0; `True` without a communicator |
| `scatter_items(items, comm=None)` | the slice of a list that this process takes: contiguous slices in the order of the ranks, the first processes taking one item more when the division is not exact |
| `gather_results(local_results, comm=None)` | on rank 0, the lists of all the processes joined in the order of the ranks; an empty list on the others |
| `bcast_item(item, comm=None, root=0)` | the item of the process of rank `root`, on every process |
| `mpi_map(fn, items, comm=None)` | `[fn(x) for x in items]`, each process computing its slice, collected on rank 0 |

Given `comm`, `sweep` gives each process its slice of the points by `scatter_items` and collects the results by `gather_results`: rank 0 receives every result in the order of the points, and the other processes receive an empty list. The same script therefore runs in one process or in several:

```python
from asva.run.mpi import get_comm, is_root

comm = get_comm()
results = sweep(solve, param_grid(n_nodes=[2, 4, 6]), metric_fns, verbose=False, comm=comm)
if is_root(comm):
    print(len(results))
```

```text
3
```

Saved as `sweep_script.py`, it runs in four processes under the command `mpirun -n 4 python -m mpi4py sweep_script.py`, and in one process under `python sweep_script.py`.
