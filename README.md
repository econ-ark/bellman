# Project Bellman

Project Bellman provides a modular and highly expressive language system and AI-interface for recursive dynamic programming in economics and finance. 

The project is in pre-release. The core of the language and of the package is in place, 
and the syntax and the interfaces may still change between versions, with no promise of 
backward compatibility. The documentation and the applications are under active development. 
Feedback and contributions are welcome.

## Install

Python 3.12 or later and git are required.

```bash
git clone https://github.com/econ-ark/bellman.git
cd bellman
./install-dev.sh
source venv/bin/activate
```

`install-dev.sh` creates `venv/`, installs `requirements.txt`, and installs 
`bellman` and `bellman-workbench` in editable mode.

To check the install:

```bash
python -m bellman applications/cons-port/declaration/stages/cons/cons.bl
```

This prints the consumption stage of the portfolio–consumption model.

<!-- AAS to AI: can we do this wihtout an extra step? these are drawings in the denotatiosn I assume? any other way to frame this? also "Node.js after `npm ci`" makes no sense to me. -->


### Installing workbench 

For the Workbench and the desktop application, see [Install Bellman Workbench](docs/overview/00-install.md).

## Contents

| Folder | Contents |
|---|---|
| [`packages/bellman/`](packages/bellman/README.md) | The parser, the stage object, the binding of parameters, methods and settings, periods and trellises, printing and drawing. |
| [`packages/asva/`](packages/asva/README.md) | Numerical routines: the endogenous grid step, interpolants, and a runner for parameter sweeps, moments and estimation. |
| [`packages/bellman-workbench/`](packages/bellman-workbench/README.md) | The Workbench page and its server. |
| [`packages/bellman-desktop/`](packages/bellman-desktop/README.md) | The desktop application that runs the Workbench in its own window. |
| [`packages/bellman-matsya-client/`](packages/bellman-matsya-client/README.md) | The command-line client of Matsya, a service that drafts stage files from a paper. |
| [`applications/`](applications/README.md) | Worked models, one folder each: stage files, methods, parameters, settings, trellis files and tests. |
| `docs/` | The documentation site: the language reference, the API, the Bellman calculus, the examples, the concept wiki and the changelog. |
| [`tutorials/`](tutorials/README.md) | Jupyter notebook lessons; the folder's README gives the reading order. |
| [`editor/`](editor/README.md) | A VS Code and Cursor extension for stage files. |
| [`tests/`](tests/README.md) | Repository-level tests, and the instructions for running every test. |

## A first model

The portfolio–consumption model is four stage files in [`applications/cons-port/declaration/stages/`](applications/cons-port/declaration/stages/): a household consumes, splits its savings between a safe and a risky asset, draws its income, and discounts. Two recipes next to them order the year with consumption first or with the portfolio choice first. Three lessons in [`tutorials/models/cons-port/`](tutorials/models/cons-port/) build the stages, assemble a life cycle backwards, and solve both orders. Register the Jupyter kernel once, in the activated environment:

```bash
python -m ipykernel install --user --name bellman-ddsl
```

`bellman` does not solve or simulate a model itself. An application solves its model with its own numerical code, which calls the functions the package compiles and the routines of `asva`. Simulation is not implemented yet.

## Documentation

Published at <https://econ-ark.github.io/bellman/>. `mkdocs serve` serves the site locally; `mkdocs build --strict` builds it into `site/`.

## License

Apache License 2.0; see [`LICENSE`](LICENSE). Project Bellman is part of [Econ-ARK](https://econ-ark.org) and is supported by the Alfred P. Sloan Foundation.

