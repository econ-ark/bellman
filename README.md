# Project Bellman

A dynamic programming model in economics is usually written twice, as mathematics and as solver code, and its meaning, which operators it composes and under which assumptions, stays implicit in the code. So a new model starts again, and another person's is hard to read, check or reuse.

Project Bellman provides the language Bellman-SYM. A model is written in it once, as stages; a stage is one self-contained decision problem in a `.bl` file that both people and AI can read. The package `bellman` builds each stage as an object that prints its equations beside the operators they denote; their meaning is fixed by the Bellman calculus, the project's mathematics, with no solver attached. Stages written separately join into models, and a new model reuses them; parameter values and numerical methods are bound afterwards. The package does not solve or simulate a model.

## Install

Python 3.12 or later and git are required.

```bash
git clone https://github.com/econ-ark/bellman.git
cd bellman
./install-dev.sh
source venv/bin/activate
```

`install-dev.sh` creates `venv/`, installs `requirements.txt`, and installs `bellman`, `asva` and `bellman-workbench` in editable mode. If `python3` is older than 3.12, run the script's commands by hand with a newer interpreter, for example `python3.13 -m venv venv`.

To check the install:

```bash
python -m bellman applications/cons-port/declaration/stages/cons/cons.bl
```

This prints the consumption stage of the portfolio–consumption model.

Drawings use Graphviz's `dot` if it is installed (`brew install graphviz` on macOS). Otherwise they use Node.js after `npm install` in `packages/bellman/`. Without either, everything except drawing works.

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
| `tests/` | Repository-level tests. |

## A first model

The portfolio–consumption model is four stage files in [`applications/cons-port/declaration/stages/`](applications/cons-port/declaration/stages/): a household consumes, splits its savings between a safe and a risky asset, draws its income, and discounts. Two recipes next to them order the year with consumption first or with the portfolio choice first. Three lessons in [`tutorials/models/cons-port/`](tutorials/models/cons-port/) build the stages, assemble a life cycle backwards, and solve both orders. Register the Jupyter kernel once, in the activated environment:

```bash
python -m ipykernel install --user --name bellman-ddsl
```

`bellman` does not solve or simulate a model itself. An application solves its model with its own numerical code, which calls the functions the package compiles and the routines of `asva`. Simulation is not implemented yet.

## Tests

```bash
pytest packages/bellman -n auto             # the fast core
pytest packages/bellman -n auto -m sweep    # the corpus sweeps, run before a merge
pytest tests applications tutorials packages/asva/tests -n auto
```

## Documentation

Published at <https://econ-ark.github.io/bellman/>. `mkdocs serve` serves the site locally; `mkdocs build --strict` builds it into `site/`.

## License

Apache License 2.0; see [`LICENSE`](LICENSE). Project Bellman is part of [Econ-ARK](https://econ-ark.org) and is supported by the Alfred P. Sloan Foundation.

## Homepage media

The Mile 12 market sequence combines drone footage with a wider photograph of the same market in Lagos, both taken by Ayorinde Ogundele on 8 March 2025. The edit uses an animated crop and a navy-to-ice color treatment. Both sources and the edited sequence are licensed under CC BY-SA 4.0. [Market Movements](https://commons.wikimedia.org/wiki/File:Market_Movements.webm) · [Mile 12 market photograph](https://commons.wikimedia.org/wiki/File:Drone_shot_of_a_section_of_the_Mile_12_food_market.jpg) · [License](https://creativecommons.org/licenses/by-sa/4.0/)

The night-light sequence uses twelve annual satellite composites from 2012 to 2023 with the same crop and color treatment throughout. Credit to NASA’s Scientific Visualization Studio. [Change in Night Lights between 2012 and 2023](https://svs.gsfc.nasa.gov/5276)

The other photographs and the sculling video come from Wikimedia Commons and are shown in navy and ice. Adaptations of share-alike works retain their sources' licenses.

- Xabier Cañas. Video, CC BY-SA 4.0. [A single scull on the river Oria at Orio from the air, 2023](https://commons.wikimedia.org/wiki/File:Piragua_Oria_ibaian.webm)
- TudorTulok. CC0. [A quadruple scull at dawn, 2023](https://commons.wikimedia.org/wiki/File:Fluidesign_Quad_Rowing_Team_At_Dawn.jpg)
- Bmzuckerman. Photograph, CC BY 4.0. [The National Farmers' Bank, Owatonna, Minnesota, by Louis H. Sullivan, 1908](https://commons.wikimedia.org/wiki/File:Louis_H._Sullivan_-_National_Farmer%27s_Bank_Interior_(A),_Owatonna,_MN.jpg)
- John Shorten. CC BY-SA 2.0. [Glendora Avenue from the air, 2022](https://commons.wikimedia.org/wiki/File:Aerial_View_of_Glendora_Ave_-_geograph.org.uk_-_7187713.jpg)
- Rudolph A. Furtado. CC0. [A vegetable seller's boat on Dal Lake, Srinagar, 2013](https://commons.wikimedia.org/wiki/File:Vegetable_seller_on_Dal_Lake..JPG)
