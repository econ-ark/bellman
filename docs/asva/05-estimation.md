---
audience: user
type: user-guide
topic: [numerical-representation]
---
# Estimation

> [!summary]
> Estimation by the simulated method of moments chooses the parameter values whose simulated moments come closest to the moments of the data. The reader writes a trial function, from a dictionary of parameter values to simulated panels; `make_moment_fn` turns a moment specification into a function from panels to named moments; `make_criterion` composes the two with the data moments into a loss; `estimate` minimizes the loss by the cross-entropy method; and `diagnostics` tabulates the fit.

> [!info]- Relationship with other documents
> **Builds on** — [Parameter sweeps](03-parameter-sweeps.md) §4: the functions of MPI with which an estimation divides its work among processes.
> **Used by** — [The cross-entropy method](06-cross-entropy-method.md): the steps and options of the minimization that `estimate` runs.

The parts compose as follows, the loss being minimized over θ by `estimate`:

```text
θ  →  trial(θ): panels  →  moment_fn(panels): simulated moments  →  loss against the data moments
```

## 1 The trial function

The trial function is the reader's. It takes a dictionary of parameter values, such as `{"β": 0.95, "ρ": 2.0}`, solves and simulates the model at those values with the reader's own code, and returns the **panels**: a dictionary from variable names to arrays of shape (T, N), with the T periods in rows and the N simulated agents in columns. A missing observation is NaN, and a discrete choice is a number, such as 0 or 1, and not a string. The trial function draws its shocks from one fixed seed at every call, so that every candidate θ is evaluated on the same shocks and the loss is a deterministic function of θ; `estimate` passes it no seed.

## 2 The moment specification

A moment specification is a dictionary, usually read from YAML, with three keys:

- `setup` holds `t0`, the age of the first row (0 by default), and `age_groups`, which maps a group's name to a pair of ages `[first, last]`: the group takes the rows of the ages from `first` up to, but not including, `last`. Without `age_groups`, one group named `all` takes every row. `derived_variables` maps the name of a new variable to an expression in the panel's variables, computed before the moments; an expression may hold numbers, names, `+`, `-`, `*`, `/` and the functions `np.log`, `np.maximum`, `np.minimum` and `np.abs`, and nothing else is evaluated.
- `identification` names the moments computed in every group: `mean`, `sd` (the standard deviation, with the number of observations as divisor), `corrs` (pairs of variables), `autocorrs` (the correlation of a variable between each row of the group and the row after it), `branch_fractions` (for a variable with integer values, the share of the group's observations equal to each value the variable takes in the panel) and `conditional` (the mean, standard deviation or correlation among the observations at which a discrete variable takes a given value).
- `targets` lists moments under keys of the reader's choosing: `{key, stat, var}` with `stat` one of `mean`, `sd` and `autocorr`, `{key, stat: fraction, var, value}`, or `{key, stat: corr, vars: [x, y]}`.

A moment's key names the statistic, the variables and the group:

| Moment | Key |
|---|---|
| mean of `c` in group 1 | `mean_c__age1` |
| standard deviation of `c` | `sd_c__age1` |
| correlation of `c` and `a` | `corr_c_a__age1` |
| autocorrelation of `a` | `autocorr_a__age1` |
| share of the value 1 of `d` | `branch_frac_d_1__age1` |
| mean of `c` where `d` is 1 | `cond_d_1_mean_c__age1` |
| the target with key `avg_log_c` | `avg_log_c__age1` |

A statistic computed from fewer than ten observations that are not NaN is NaN. `make_moment_fn(spec)` returns the function from panels to moments, and `compute_moments_from_panels(panels, spec)` computes them in one call:

```python
import numpy as np
import yaml
from asva.run.moments import make_moment_fn

spec = yaml.safe_load("""
setup:
  t0: 20
  age_groups:
    1: [20, 25]
    2: [25, 30]
  derived_variables:
    log_c: np.log(np.maximum(c, 1e-10))
identification:
  mean: [c, a]
  sd: [c]
  corrs:
    - [c, a]
  autocorrs: [a]
  branch_fractions: [d]
  conditional:
    d:
      1: {mean: [c]}
targets:
  - {key: avg_log_c, stat: mean, var: log_c}
""")

rng = np.random.default_rng(0)
panels = {
    "c": rng.uniform(0.5, 1.5, (10, 200)),
    "a": rng.uniform(0.0, 2.0, (10, 200)),
    "d": (rng.uniform(size=(10, 200)) > 0.7).astype(float),
}
moments = make_moment_fn(spec)(panels)
print(len(moments))
print([key for key in moments if key.endswith("__age1")])
```

```text
18
['mean_c__age1', 'mean_a__age1', 'sd_c__age1', 'corr_c_a__age1', 'autocorr_a__age1', 'branch_frac_d_0__age1', 'branch_frac_d_1__age1', 'cond_d_1_mean_c__age1', 'avg_log_c__age1']
```

Each of the two groups gives nine moments: eight of `identification`, of which `branch_fractions` gives two since `d` takes the values 0 and 1, and the target.

`moment_names(spec)` lists the keys a specification gives on a synthetic panel of ten rows. It agrees with the keys of a real panel when every group lies within the first ten rows and the only variables of `branch_fractions` are `discrete` and `z_idx`, to which it gives the values 0 and 1; otherwise the keys of a real panel are `list(moment_fn(panels))`.

## 3 The data moments

The data moments are a dictionary with the same keys, from one of three sources:

- **Self-generated.** The moment function applied to panels simulated at known values, `moment_fn(trial(theta_true))`. An estimation on them tests whether the method recovers `theta_true`.
- **A table of moments.** `load_data_moments(path, spec)` reads a CSV file whose first column names the group and whose other columns are moments: the entry of the column `mean_c` in the row of group 5 becomes `mean_c__age5`, and an empty entry is left out. `spec["column_map"]`, when present, maps a column's name to a key written with `{age}` in the place of the group, such as `{"av_c": "mean_c__age{age}"}`.
- **Microdata.** With `data_source: microdata` in the specification, `load_data_moments(path, spec)` reads a table in long form, one row per agent and period, from a CSV file or a Parquet file (a compressed table format that pandas reads). The period stands in the column that `setup.time_var` names (`t` by default) and the agent in the column that `setup.id_var` names (`_idx` by default); `compute_moments_from_dataframe` turns the table into panels and applies the specification.

`load_data_moments` also accepts a dictionary of moments, of which it keeps the numbers that are not NaN.

## 4 The criterion

`make_criterion(trial_fn, moment_fn, data_moments, weights=None)` returns the loss as a function of a dictionary of parameter values. It orders the moments by their keys in alphabetical order and leaves out the data moments that are NaN. At each call it runs the trial function and the moment function, and returns

$$
\sum_i w_i\,(s_i - d_i)^2 \;+\; 10^6 \times n_{\text{missing}},
$$

where $d_i$ is a data moment, $s_i$ the simulated moment of the same key, the sum runs over the moments the simulation gives, and $n_{\text{missing}}$ counts the moments that are missing from the simulation or NaN in it. Without `weights`, $w_i = 1/d_i^2$ where $|d_i| \ge 1$, a squared relative deviation, and $w_i = 1$ otherwise, a squared absolute deviation, so that correlations and shares, which lie below one in absolute value, are not magnified. When it is given, `weights` is an array of the weights in the order of the moments. An exception in the trial or the moment function gives the loss $10^{10}$, and the first three exceptions are printed with their tracebacks, the lists of the calls at which they were raised. After each call the criterion holds the simulated moments that are not NaN in its attribute `last_sim_moments`, which is `None` after an exception.

## 5 Estimating

```python
estimate(criterion, param_spec, method="cross-entropy", method_options=None, comm=None, verbose=True, resume_state=None, checkpoint_fn=None, progress_fn=None)
```

`estimate` minimizes the criterion over the box that `param_spec` gives, a dictionary from each free parameter's name to `{"bounds": [low, high]}`. `method` accepts the cross-entropy method alone, written `"cross-entropy"`, `"ce"` or `"cross_entropy"`, and another value is refused with `ValueError`; [The cross-entropy method](06-cross-entropy-method.md) states its steps, the options of `method_options`, and the use of `comm`, `resume_state`, `checkpoint_fn` and `progress_fn`. The result is an `EstimationResult`:

| Field | Holds |
|---|---|
| `theta` | the best parameter values found |
| `objective` | the loss at `theta` |
| `converged` | whether the stopping rule was met before the iterations ran out |
| `n_iter` | the number of iterations, those of a resumed estimation included |
| `history` | for each iteration, the mean `means` and the covariance `cov` of the sampling distribution, the best loss so far `best_loss`, and the mean loss `elite_mean_loss` of the iteration's best candidates, the elite |
| `sim_moments` | the simulated moments of the last candidate the criterion evaluated on the first process (rank 0, [Parameter sweeps](03-parameter-sweeps.md) §4), which in general is not `theta` |

To read the fit at `theta`, the reader evaluates the criterion there and places its moments in the result before calling `diagnostics`, as the example of §6 does.

`diagnostics(result, data_moments, moment_names=None, weights=None)` returns a dictionary with three entries. `fit_table` holds one row for each data moment with its data value, simulated value, residual, contribution and share of the total contribution in percent; `total_loss` is the result's objective; and `worst_moments` holds the five largest contributions. A contribution is the squared residual, multiplied by the moment's weight when `weights` is given, and $10^6$ for a moment the simulation lacks; the criterion's default weights are not applied. `moment_names` gives names to display, as a dictionary by key or as a list in the keys' alphabetical order.

`load_estimation_spec(path)` reads a YAML file with an `estimation` block, which holds `free`, `method`, `method_options` and optionally `theta_true`, and a `moments` block, which is the moment specification. It returns a dictionary with the keys `free`, `moment_spec`, `data_moments`, `method` and `method_options`, and `theta_true` when the file gives it. With `data_source: precomputed`, which is the default, it reads the data moments from the CSV file that `data_file` names (`moments.csv` by default) in the folder of the YAML file, keeping the rows whose first entry is a number and not applying `column_map`; with another source its data moments are an empty dictionary.

## 6 A complete example

The model of the example is an outcome `y` equal to a mean μ plus σ times a standard normal shock, simulated for 500 agents over 20 periods, and the data moments are self-generated at μ = 1 and σ = 0.5:

```python
from asva.run.estimate import make_criterion, estimate, diagnostics

def trial(theta):
    shocks = np.random.default_rng(42).standard_normal((20, 500))
    return {"y": theta["mu"] + theta["sigma"] * shocks}

moment_fn = make_moment_fn({"identification": {"mean": ["y"], "sd": ["y"]}})
data_moments = moment_fn(trial({"mu": 1.0, "sigma": 0.5}))

criterion = make_criterion(trial, moment_fn, data_moments)
result = estimate(
    criterion,
    {"mu": {"bounds": [0.0, 2.0]}, "sigma": {"bounds": [0.1, 1.0]}},
    method_options={"n_samples": 40, "n_elite": 8, "max_iter": 30, "tol": 1e-6, "sampling_seed": 0},
    verbose=False,
)
print({name: round(value, 2) for name, value in result.theta.items()}, result.converged)

criterion(result.theta)
result.sim_moments = dict(criterion.last_sim_moments)
for row in diagnostics(result, data_moments)["fit_table"]:
    print(row["moment"], round(row["data"], 3), round(row["simulated"], 3))
```

```text
{'mu': 1.0, 'sigma': 0.5} True
mean_y__ageall 0.995 0.996
sd_y__ageall 0.503 0.503
```

Run under MPI with `comm=get_comm()` from `asva.run.mpi`, the same script evaluates the candidates of each iteration on several processes ([The cross-entropy method](06-cross-entropy-method.md) §3).
