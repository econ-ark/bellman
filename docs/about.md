---
description: The people and purpose behind Project Bellman, an Econ-ARK project supported by the Alfred P. Sloan Foundation.
audience: user
type: overview
hide:
  - byline
---

# About us

Project Bellman provides a [declarative](wiki/declarative_language.md), modular
and highly expressive language system for recursive dynamic programming, in economics
and in other fields. It is an [Econ-ARK](https://econ-ark.org) project.

## 1 The project

In the [Bellman language](Bellman-Sym/index.md), an economist writes the model
once, as stages. A [**stage**](wiki/stage.md) is one self-contained decision
problem, written as one stage file. Stages written separately join into a
model, and a new model reuses them. The same four stage files, for example,
build a portfolio–consumption model with consumption chosen first or with the
portfolio chosen first. Parameter values and numerical methods are attached to
a stage afterwards, so a change of method leaves the stage files unchanged.

We develop the language, its mathematical foundations and worked examples
together. The model's equations and structure remain available for people
and software to inspect.

The project is in pre-release, and its documentation and
[applications](examples/index.md) are under active development.

Read the [overview](overview/index.md), explore a
[worked model](examples/index.md), or follow the
[mathematical foundations](bellman-calculus/index.md).

## 2 People and support

The Bellman language was created by Christopher D. Carroll and Akshay Shanker.
It is named in honor of Richard Bellman, whose ideas are the foundation of the
language.[^bellman]

Team members 

| Contributors | Institution |
|---|---|
| [Christopher D. Carroll](https://www.econ2.jhu.edu/people/ccarroll/) | Johns Hopkins University |
| [Alan Lujan](https://alujan.dev) | Johns Hopkins University |
| [Akshay Shanker](https://github.com/akshayshanker) | Johns Hopkins University |

Project Bellman is a sub-project of [Econ-ARK](https://econ-ark.org) and is
supported by the [Alfred P. Sloan Foundation](https://sloan.org).

## 3 Acknowledgments

The grammar of the Bellman language is derived from dynspec, the grammar of
[Dyno](https://github.com/EconForge/dyno.py), a library written by Pablo Winant
and Ousema Bouaneni.[^dynspec]

The homepage shows video and satellite imagery adapted from the work of others.[^media]

## 4 Take part

Questions, corrections and contributions to the code, documentation and
examples are welcome on [GitHub](https://github.com/econ-ark/bellman).
To report a problem or suggest an improvement,
[open an issue](https://github.com/econ-ark/bellman/issues).
For a model example, include the equations and the behavior you expect.

The software is available under the
[Apache License 2.0](https://github.com/econ-ark/bellman/blob/main/LICENSE).

[^bellman]: Richard Bellman, *Dynamic Programming* (Princeton University Press, 1957), Preface, pp. vii and xi–xii, and Chapter I, §§4–5, pp. 7–9.

[^dynspec]: Pablo Winant and Ousema Bouaneni, *Dyno*, EconForge, <https://github.com/EconForge/dyno.py>. The dynspec grammar is the file [`src/dyno/dynspec/grammars/grammar.lark`](https://github.com/EconForge/dyno.py/blob/312e8eaa456f5d9c23cfecdb09d979a58ec7acc4/src/dyno/dynspec/grammars/grammar.lark), cited at commit `312e8ea`.

[^media]: The market sequence is adapted, by crop and color, from [Market Movements](https://commons.wikimedia.org/wiki/File:Market_Movements.webm) and a [photograph of the Mile 12 market](https://commons.wikimedia.org/wiki/File:Drone_shot_of_a_section_of_the_Mile_12_food_market.jpg), both by Ayorinde Ogundele. The sculling video is adapted, by color, from [A single scull on the river Oria at Orio from the air, 2023](https://commons.wikimedia.org/wiki/File:Piragua_Oria_ibaian.webm) by Xabier Cañas. The sources and the adaptations are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The night-light images come from [Change in Night Lights between 2012 and 2023](https://svs.gsfc.nasa.gov/5276), NASA’s Scientific Visualization Studio.
