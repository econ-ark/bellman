---
title: "Project Bellman"
audience: developer
type: index
---
# Project Bellman

This repository holds Bellman-SYM, a language in which an economist writes a dynamic program one stage at a time, and `bellman`, the Python package that reads it. A stage is one step of a period's Bellman problem. Its file, a `.bl` file, declares the stage's states, controls and shocks, its laws of motion and its value equations at three perches, the information sets at arrival, at the decision and at continuation. The package parses a stage file and constructs the stage as an object that prints its equations beside the operators they denote, draws those operators and compiles the equations into Python functions. It binds a stage to its parameter values, numerical methods and numerical settings, joins stages into a period wherever one stage produces a field, a named state or value, that another takes, and builds a trellis, the sequence of a model's periods, backwards from the last period. The Bellman calculus, the mathematics that gives a stage its meaning, is set out in the documentation. Beside `bellman` stands `asva`, a package of numerical code, such as the step of the endogenous grid method, that imports nothing of `bellman`; an application that solves its model does so with its own numerical tool, which evaluates only the functions the package compiles from the stage files. This is the internal developer release 0.01, and [`docs/changelog.md`](docs/changelog.md) records what it contains.

## Installing

For the browser editor and desktop application, follow [Install Bellman Workbench](docs/overview/00-install.md). The instructions below install the full development environment.

The release needs Python 3.12 or later and git. The repository is cloned by

```bash
git clone https://github.com/econ-ark/bellman.git
cd bellman
```

The following commands create a virtual environment in `venv/` and install the repository’s dependencies and its three Python packages in editable form, so that changes to their code take effect without a new install:

```bash
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip install -e packages/bellman
venv/bin/python -m pip install -e packages/asva
venv/bin/python -m pip install -e packages/bellman-workbench
```

`./install-dev.sh` runs the same commands. Both call the interpreter `python3`; where that is older than 3.12, the first line names the interpreter instead, for example `python3.13 -m venv venv`, and the remaining commands are typed. The environment keeps the name `venv`, since the tests that execute notebooks read its interpreter, and `source venv/bin/activate` activates it in each new shell. Then

```bash
python -m bellman applications/portfolio-choice/declaration/stages/cons/cons.bl
```

prints the sheet of the consumption stage of the portfolio–consumption model, the stage's printed summary of its perches, fields and equations, which shows that the install works.

`requirements.txt` pins the packages the repository's code imports or runs, the packages of the documentation site among them; a package that a pinned package requires by its own metadata, such as Markdown with MkDocs, has no line of its own, except `filelock`, which Solara's server requires and which is held at the release its line names, for the reason written above that line. An install of `bellman` without `requirements.txt` takes the site's packages from the package's extra `docs`, `pip install -e "packages/bellman[docs]"`, and those of the tests and of the formatter from its extra `dev`.

A drawing of a stage, a period or a trellis is laid out by Graphviz's `dot` where that program is on the path; Graphviz comes from the system's package manager, for example `brew install graphviz` on macOS. Otherwise the drawing is laid out by Node.js with the WebAssembly build of Graphviz, which `npm install`, run once in the repository's folder, installs. Without either program everything but drawing works, and a drawing is refused with a message that names what to install.

## What the repository holds

| Folder | What it holds |
|---|---|
| [`packages/bellman/`](packages/bellman/README.md) | The package `bellman`: the parser of stage files, the construction of a stage, the binding of parameter values, methods and settings, the assembly of periods and trellises, and what a stage prints and draws. Its README maps the package's folders and modules; its tests are in `packages/bellman/tests/`. |
| [`packages/asva/`](packages/asva/README.md) | The package `asva`: the functions that build the step of the endogenous grid method, from functions the reader writes or from the record of a builder's kernels that `bellman` answers; an interpolant composed with a law of motion; numerical utilities; and `asva.run`, a runner for parameter sweeps, moments and estimation. Its tests are in `packages/asva/tests/`. |
| [`applications/`](applications/README.md) | The worked models, one folder each: stage files, methods files, parameter values, settings, the trellis files that assemble a model, and the tests that construct them. |
| `docs/` | The source of the documentation site. `docs/Bellman-Sym/` documents the language in four parts: the user guide in its root pages, `API/` for the functions of the Bellman factory and the methods of the stage object, `appendices/` for the technical details, and `reference/` for the catalogues of what a stage file may write. `docs/bellman-calculus/` holds the mathematics, `docs/overview/` the informal overviews, `docs/examples/` the example models, `docs/wiki/` the concept wiki, which defines the project's terms, `docs/asva/` the pages of `asva`, and `docs/changelog.md` the changelog. |
| [`tutorials/`](tutorials/README.md) | The lessons, Jupyter notebooks in three groups, Getting started, Specific topics and Model walkthroughs, with their reading order in `tutorials/README.md` and the record of their last execution in `tutorials/lessons.json`. |
| [`editor/`](editor/README.md) | An extension of VS Code and Cursor for stage files: highlighting, with each declared name colored by its role, and the input of mathematical italic letters, `_c` becoming 𝑐. Its README gives the two ways to install it, a symbolic link from the repository or a packaged file. |
| `tests/` | The tests of the repository as a whole, as distinct from those of one package. |

At the root, `requirements.txt` and `install-dev.sh` make the environment, `pytest.ini` configures the tests, `mkdocs.yml` the documentation site, and `package.json` the Node package that lays drawings out.

## A first model: the two orders of the portfolio–consumption model

A household consumes out of its resources and divides its savings between a safe asset and a risky one, choosing the risky share before the return and next year's income are drawn. The model is four stage files in [`applications/cons-port/declaration/stages/`](applications/cons-port/declaration/stages/): consumption (`cons.bl`), the portfolio share (`port.bl`), income drawn with no portfolio choice (`noport.bl`) and discounting (`disc.bl`), each written with the maximization alone, the numerical method bound by a methods file and the block file it names. A year can begin with either choice: the recipe `applications/cons-port/declaration/spec.cons-port.yml` puts consumption first, and `spec.port-cons.yml` beside it puts the portfolio first. [`applications/cons-port/`](applications/cons-port/README.md) holds the model's parameter values, methods, settings and recipes, and its numerical tool, `code/cons_port_tool.py`.

Three lessons in [`tutorials/models/cons-port/`](tutorials/models/cons-port/) take the model from its files to its solution, read in order:

1. `01-two-stages-two-orders.ipynb` constructs the four stages and forms a period in each order; where two stages meet follows from the fields they share, not from the order in which the period lists them.
2. `02-a-life-cycle-built-backwards.ipynb` binds the stages to their parameter values, methods and settings, and builds a life cycle of six years backwards from the last year.
3. `03-solving-the-two-orders.ipynb` solves both orders, consumption by the endogenous grid method and the portfolio share by a search over the share, and recovers one order's value from the other's. The two orders end a life differently, so their risky shares in the first year nearly coincide rather than agree; the portfolio-first solution of six years equals, exactly, the portfolio stage's operator applied to a consumption-first solution of five years begun from the terminal value carried through the consumption and discount stages.

The lessons run in the environment the install made, under the Jupyter kernel `bellman-ddsl`, which one line, typed once in the activated environment, registers:

```bash
python -m ipykernel install --user --name bellman-ddsl
```

They open in any Jupyter front end, such as JupyterLab or VS Code. The first lesson of Getting started, `tutorials/getting-started/01-the-stage.ipynb`, introduces the stage as an object on the consumption stage of the same model and may be read before the three. This release does not simulate: `asva.simulate.simulate`, which would carry a population of households through the periods, raises an error when it is called, so the two orders are compared by their value functions and policies and not by simulated wealth.

## Running the tests

In the activated environment,

```bash
pytest packages/bellman -n auto
pytest packages/bellman -n auto -m sweep
pytest tests applications tutorials packages/asva/tests -n auto
```

The first line runs the fast core of the package's tests, against which a change to the package is checked. The second runs the sweeps: the tests that print in full every stage of the package's own collection of test stages, compare each stage with its stored record, run the command `python -m bellman` on files it must refuse, and assemble whole trellises. The sweeps take longer and are run before a change is merged; `-m "sweep or not sweep"` runs them together with the fast core. The third line runs the tests outside the package: those of the applications, of the lessons' record, of `asva` and of the repository as a whole. `-n auto` spreads the tests over the machine's cores.

## Reading and building the documentation

The documentation is read at <https://econ-ark.github.io/bellman/>. Its source is `docs/`, which `mkdocs.yml` configures. In the activated environment,

```bash
mkdocs serve
mkdocs build --strict
```

the first line serves the site at <http://127.0.0.1:8000> and reloads a page when its file is saved, and the second writes the site to `site/`, which git does not track; `--strict` stops the build at any warning, such as a link to a page that does not exist.

## License and acknowledgments

The repository is licensed under the Apache License 2.0 ([`LICENSE`](LICENSE)). The project is funded by the Alfred P. Sloan Foundation as part of [Econ-ARK](https://econ-ark.org).
