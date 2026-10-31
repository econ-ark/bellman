---
audience: user
type: user-guide
topic: [numerical-representation]
---
# The cross-entropy method

> [!summary]
> `estimate` minimizes a criterion by the cross-entropy method of Kroese, Porotsky and Rubinstein (2006). At each iteration it draws candidate parameter values, evaluates the criterion at each, keeps the best of them, the **elite**, and refits the sampling distribution to the elite; it stops when the mean loss of the elite changes by less than a tolerance. This page states the steps, the options, the division of the work among MPI processes, what happens when a step fails, and the checkpoints from which an estimation resumes.

> [!info]- Relationship with other documents
> **Builds on** — [Estimation](05-estimation.md): the criterion that the method minimizes and the result it returns.
> **See also** — [Parameter sweeps](03-parameter-sweeps.md) §4: the functions of MPI.

## 1 The steps

The free parameters are ordered by name, and every draw comes from one random generator, `numpy.random.default_rng(sampling_seed)`, so that one seed gives one sequence of candidates. Before the first iteration the best values are the midpoints of the bounds with the loss $10^{10}$, a placeholder that is never evaluated. Each iteration then makes six steps:

1. **Draw.** At the first iteration, `n_samples` candidates are drawn independently and uniformly within the bounds. At later iterations they are drawn from the multivariate normal distribution with the current mean and covariance; a draw outside the bounds is drawn again, up to a thousand times, and then clipped to the bounds. A share `noise_fraction` of the candidates is drawn uniformly instead.
2. **Evaluate.** The criterion is evaluated at every candidate.
3. **Select.** The `n_elite` candidates with the lowest losses form the elite.
4. **Record the best.** An elite candidate whose loss is below the best loss so far becomes the best.
5. **Refit.** The new mean and covariance are the weighted mean and covariance of the elite, the weight of candidate i proportional to $\exp(-(L_i - \min_j L_j))$ for the losses $L$, with $10^{-12}$ times the identity added to the covariance. With `alpha_smooth` below one, from the second iteration the mean and the covariance are `alpha_smooth` times the new ones plus `1 − alpha_smooth` times the previous ones.
6. **Stop or continue.** From the second iteration, the estimation has converged when the mean loss of the elite differs from that of the previous iteration by less than `tol`. It stops then, after `max_iter` iterations, or after `max_iter_this_run` iterations of the present call.

The weights make the refit depend on the scale of the losses: a candidate whose loss exceeds the elite's lowest by ten has about $4.5 \times 10^{-5}$ times the weight of the best. The result's `theta` and `objective` are the best candidate and its loss ([Estimation](05-estimation.md) §5).

## 2 The options

The options are the entries of `method_options`, in Python or under `estimation.method_options` of the YAML file that `load_estimation_spec` reads:

| Option | Default | Meaning |
|---|---|---|
| `n_samples` | 48 | the number of candidates drawn at each iteration |
| `n_elite` | 10 | the size of the elite, at least 1 and at most `n_samples` |
| `max_iter` | 50 | the largest number of iterations |
| `tol` | 0.01 | the change in the elite's mean loss below which the estimation has converged |
| `sampling_seed` | 0 | the seed of the draws |
| `noise_fraction` | 0.0 | the share of the candidates drawn uniformly after the first iteration |
| `alpha_smooth` | 1.0 | the weight of the new mean and covariance against the previous ones |
| `max_iter_this_run` | `max_iter` | the largest number of iterations of one call |
| `checkpoint_dir` | `None` | a folder in which the state is written after every iteration (§5) |

```yaml
estimation:
  free:
    beta: {bounds: [0.88, 0.99]}
    rho: {bounds: [1.0, 5.0]}
  method: cross-entropy
  method_options:
    n_samples: 48
    n_elite: 10
    max_iter: 50
    tol: 1.0e-3
    sampling_seed: 42
```

The number of candidates sets how widely an iteration explores the box: ten to twenty candidates for each free parameter is a common choice. The elite's size sets how many candidates the refit averages: a small elite follows the few best candidates, and a large one moves the distribution slowly; five to twenty percent of the candidates is a common choice. The tolerance is in the units of the loss, and a smaller one continues the iterations until the elite's losses agree more closely.

The example minimizes a criterion whose minimum is known, at $x = 0.3$ and $y = -0.2$:

```python
from asva.run.estimate import estimate

def criterion(theta):
    return (theta["x"] - 0.3) ** 2 + (theta["y"] + 0.2) ** 2

free = {"x": {"bounds": [-1.0, 1.0]}, "y": {"bounds": [-1.0, 1.0]}}
options = {"n_samples": 30, "n_elite": 6, "max_iter": 40, "tol": 1e-8, "sampling_seed": 0}

result = estimate(criterion, free, method_options=options, verbose=False)
print({name: round(value, 3) for name, value in result.theta.items()}, result.converged)
```

```text
{'x': 0.3, 'y': -0.2} True
```

With `verbose=True`, the first process, of rank 0 ([Parameter sweeps](03-parameter-sweeps.md) §4), prints one line for each iteration, with the best loss, the elite's mean loss and the best values, and between iterations a line on the memory the process uses.

## 3 Processes

With `comm=get_comm()` from `asva.run.mpi`, the process of rank 0 draws the candidates and sends them to every process; `mpi_map` gives each process a contiguous slice of the candidates and collects the losses on rank 0 in the order of the candidates; rank 0 selects the elite, refits the distribution and sends the new state, and whether the stopping rule was met, to every process before the next draw. With `n_samples` equal to the number of processes, each process evaluates one candidate at each iteration; with more candidates some processes evaluate several in turn, and with fewer some are idle. Only rank 0 prints and writes checkpoints. A script that calls `estimate(..., comm=get_comm())`, saved as `estimate_script.py`, runs in 48 processes under the command `mpirun -n 48 python -m mpi4py estimate_script.py`.

## 4 Failures

| Failure | What happens |
|---|---|
| the criterion raises an exception at a candidate | the candidate's loss is $10^{10}$, and the first three exceptions are printed with their tracebacks, the lists of the calls at which they were raised |
| a draw stays outside the bounds after a thousand attempts | it is clipped to the bounds |
| the elite's weights sum to zero, or to a number that is not finite | the weights are equal |
| the elite's covariance is singular | adding $10^{-12}$ times the identity, as step 5 does, makes it positive definite |
| a process stops | the estimation stops; no other process evaluates that process's candidates |

## 5 Checkpoints and resuming

With `checkpoint_dir`, rank 0 writes the state after every iteration to the file `state.pkl` in that folder: a dictionary stored in the pickle format, Python's own format for storing objects, with the keys `means`, `cov`, `best_theta`, `best_loss`, `it` (the iteration just completed, counted from zero), `history`, `elite_mean_loss_prev` and `rng_state`, the state of the random generator. The file is written under another name and then renamed, so that an interrupted write leaves the previous state in place. `estimate(..., resume_state=state)`, with `state` the dictionary read from that file, continues at the next iteration with the same generator state, so that an estimation run in several calls draws the same candidates as one run in a single call. `max_iter_this_run` lets a long estimation run as a sequence of shorter calls in this way:

```python
import pickle

options = {**options, "max_iter": 6, "max_iter_this_run": 3, "checkpoint_dir": "checkpoints"}
first = estimate(criterion, free, method_options=options, verbose=False)
with open("checkpoints/state.pkl", "rb") as f:
    state = pickle.load(f)
second = estimate(criterion, free, method_options=options, verbose=False, resume_state=state)

in_one_call = estimate(criterion, free, method_options={**options, "max_iter_this_run": 6, "checkpoint_dir": None}, verbose=False)
print(first.n_iter, state["it"], second.n_iter, second.theta == in_one_call.theta)
```

```text
3 2 6 True
```

The first call stops after three iterations, and its last state records the iteration 2, counted from zero; the second call continues to the sixth iteration, and its best values equal those of one call of six iterations.

`checkpoint_fn`, a function of the state dictionary, takes the place of the file that `checkpoint_dir` writes, and `progress_fn(it, info)`, called after every iteration with `info` holding `best_theta`, `best_loss` and `elite_mean_loss`, takes the place of the line that `verbose` prints.

## References

- Kroese, D. P., Porotsky, S. and Rubinstein, R. Y. (2006). "The cross-entropy method for continuous multi-extremal optimization." *Methodology and Computing in Applied Probability* 8(3), 383–407.
