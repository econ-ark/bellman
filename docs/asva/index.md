---
audience: user
type: user-guide
topic: [numerical-representation]
---
# Asva

> [!summary]
> Asva is the numerical toolkit beside `bellman`. It builds two numerical steps of [backward builders](../wiki/backward_builder.md) from functions the reader writes: the endogenous grid step, which it also builds from the records of a stage's kernels, and the step that evaluates functions known on a grid of decision states at the points of an arrival grid, through the transition from arrival to decision. It also replaces missing and infinite entries of value and policy arrays, and its runner repeats a computation over the variants of a model, saves solutions, computes moments of simulated data and estimates parameters, in one process or in several. Its functions take arrays, functions, dictionaries and those records, and import nothing of `bellman`: the structure of a model, its stages, periods, [trellis](../wiki/trellis.md) and [inter-period connectors](../wiki/connector.md), is defined in `bellman`, and asva holds none of it.

> [!info]- Relationship with other documents
> **Builds on** — [The Bellman factory](../Bellman-Sym/08-bellman-factory.md): the recipe and the specified trellis, the runner's tests holding the fills of a recipe's slots; [A builder](../Bellman-Sym/API/stage/04-builder.md) §5: the record of a builder's kernels, from which `egm` builds the endogenous grid step.
> **Used by** — [Numerical steps](01-numerical-steps.md), [The runner](02-the-runner.md), [Parameter sweeps](03-parameter-sweeps.md), [Saving solutions](04-saving-solutions.md), [Estimation](05-estimation.md) and [The cross-entropy method](06-cross-entropy-method.md): the reference pages of the package.
> **See also** — [Handler](../wiki/handler.md): the routine a methods file names for a method.

> [!note]- Key terminology
> | Term | Meaning |
> |---|---|
> | **Perch** | One of the three information sets within a stage: arrival, when the stage begins; decision, when the choice is made; continuation, after the choice ([wiki](../wiki/perch.md)). |
> | **Handler** | The routine a methods file names for a method, written `package:function`, such as `asva:make_egm_1d` ([wiki](../wiki/handler.md)). |
> | **Record of a builder's kernels** | What a builder's `kernels()` answers: for each of the builder's operations, in the order they apply, its printed kernel and the wires it reads and writes, and, where its kernel is an explicit function, its compiled function with the names of its arguments and outputs, or, for a row that states a relation its output satisfies, such as the identification of a policy block, its printed relation; the parameters' names and values; and the declared sets; with no reference to the stage ([A builder](../Bellman-Sym/API/stage/04-builder.md) §5). |
> | **Endogenous grid method** | The method that computes the optimal choice at each point of a grid of the continuation state by inverting the Euler equation, and then the decision state at which that choice is made (Carroll 2006). |
> | **Upper envelope** | Where the continuation value is not concave, the Euler equation has several solutions at some decision states; the upper envelope keeps, at each such state, the solution with the highest value. |
> | **Registry** and **recipe** | A registry is the folder that holds a model's stage files and the files of their calibration, settings and methods; a recipe, a file such as `spec.yml`, lists for each stage the files from which its calibration, settings and methods are read ([wiki](../wiki/spec_factory.md)). |
> | **Slot** and **fill** | A slot is a `$name` in a recipe's list of files; a fill is the dictionary bound to it by the keyword of the same name ([wiki](../wiki/spec_factory.md)). |
> | **Test** | One variant of a model in a run: the fills of a recipe's slots, with a label, held as a `TestSpec` ([The runner](02-the-runner.md)). |
> | **Simulated method of moments** | Estimation that chooses the parameter values whose simulated moments come closest to the moments of the data ([Estimation](05-estimation.md)). |
> | **Cross-entropy method** | A minimization method that draws candidate parameter values from a distribution and refits the distribution to the best of them ([The cross-entropy method](06-cross-entropy-method.md)). |
> | **MPI** | The Message Passing Interface, the standard for running one program as several processes that exchange data; Python uses it through the package `mpi4py`. |

## 1 Installing and importing

From the root of the repository, `pip install -e packages/asva` installs the package into the active environment. Each module is imported by its name, for instance `from asva.egm_1d import make_egm_1d` or `from asva.run.sweep import sweep`. The functions of `asva.run.mpi` use the package `mpi4py` when it is installed and run in one process when it is not; `pip install -e "packages/asva[mpi]"` installs asva together with `mpi4py`.

## 2 The modules

| Module | Holds | Page |
|---|---|---|
| `asva.egm_1d` | `make_egm_1d` and `make_egm`, the endogenous grid step on a grid of one dimension and of K dimensions; `egm`, the one-dimensional step built from the records of a stage's kernels | [Numerical steps](01-numerical-steps.md) §2, §3, §6 |
| `asva.compose_interp` | `make_compose_interp`, the step that evaluates functions known on a grid of decision states at the points of an arrival grid | [Numerical steps](01-numerical-steps.md) §4 |
| `asva.numerics` | `clamp_value`, `clamp_policy` and `clamp_scalar` | [Numerical steps](01-numerical-steps.md) §5 |
| `asva.simulate` | the forward simulator | §4 |
| `asva.run.types`, `asva.run.make_test` | `TestSpec`, `SimSpec`, `RunSpec` and `make_test` | [The runner](02-the-runner.md) |
| `asva.run.sweep`, `asva.run.metrics`, `asva.run.mpi` | `param_grid`, `sweep` and `SweepResult`; the tables; the functions of MPI | [Parameter sweeps](03-parameter-sweeps.md) |
| `asva.run.io` | `save_solution` and `load_solution` | [Saving solutions](04-saving-solutions.md) |
| `asva.run.moments`, `asva.run.estimate` | the moment functions; the criterion, `estimate` and `diagnostics` | [Estimation](05-estimation.md), [The cross-entropy method](06-cross-entropy-method.md) |

## 3 Asva and bellman

A methods file may name an asva function as the [handler](../wiki/handler.md) of a method. The [retirement-choice application](../examples/retirement/retirement_choice.md) attaches the endogenous grid method to the consumption stages of its retiree and its worker with the entry

```yaml
  - on: policy
    method: !egm
    handler: asva:make_egm_1d
```

`bellman` binds the method at the [Evaluation](../Bellman-Sym/reference/operations.md#evaluation) that closes the policy block, `policy:Evaluation`, the operation that places the policy in its declared set of functions ([the method type `!egm`](../Bellman-Sym/reference/methods.md#egm)), and records the handler's name with it; it neither imports the function nor calls it. The reader's own code builds the step and applies it: from the [specified stage](../wiki/specified_stage.md) it computes the arrays and the functions that `make_egm_1d` or another asva function takes, or it passes the records of the stage's kernels to `egm` ([Numerical steps](01-numerical-steps.md) §6).

A test of the runner holds fills keyed by slot name, and these are the keyword arguments of `load_recipe` and `assemble_trellis` of `bellman.trellis`, so that one test selects one variant of the model that a registry's recipe describes ([The runner](02-the-runner.md) §2).

## 4 Simulation

This release of asva does not simulate. The module `asva.simulate` is installed with the package, and its two functions that simulate a population of agents, `simulate` over the periods and `simulate_period` over the stages of one period, raise an error when they are called. The simulated panels that an estimation needs are therefore computed by the reader's own code ([Estimation](05-estimation.md) §1).

## References

- Carroll, C. D. (2006). "The method of endogenous gridpoints for solving dynamic stochastic optimization problems." *Economics Letters* 91(3), 312–320.
