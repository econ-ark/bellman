# asva

The package `asva` is the numerical toolkit beside `bellman`. It imports
nothing of `bellman`: it works on the functions, arrays and plain records its
caller passes it.

| Module | What it holds |
|---|---|
| `asva.egm_1d` | `make_egm_1d` and `make_egm`, which build the endogenous grid step on a one-dimensional or a K-dimensional continuation grid from pointwise functions; `egm`, which builds the one-dimensional step from the records of a stage's kernels, `stage.dcsn.builder.policy.kernels()` and `stage.dcsn.builder.bwd.kernels()`, with the parameter values passed at each call |
| `asva.compose_interp` | `make_compose_interp`, which composes a decision-perch function with the arrival-to-decision transition and interpolates it on the arrival grid |
| `asva.numerics` | the clamping of value and policy arrays and of scalars |
| `asva.simulate` | the one-stage forward step, the connectors' renames and the shock draws of the forward Monte Carlo simulator |
| `asva.run` | the runner: the records of a run and its test set, parameter sweeps, solution files, tables of results, moments, estimation and MPI helpers |

It is installed after `bellman`, from the repository root, with
`pip install -e packages/asva`. Its tests are under `packages/asva/tests/`,
which the root `pytest.ini` collects.
