---
description: The people and purpose behind Project Bellman, an Econ-ARK project supported by the Alfred P. Sloan Foundation.
audience: user
type: overview
hide:
  - byline
---

# About us

Project Bellman provides a [declarative](wiki/declarative_language.md), modular
and expressive language system for recursive dynamic programming, in economics
and in other fields. It is an [Econ-ARK](https://econ-ark.org) project.

## 1 The project

A dynamic programming model in economics is usually written twice: once as
mathematics, and again as the code that solves it. That code is particular to
the one model. The author of the next model therefore starts again, and another
person's model is hard to read.

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

Read the [overview](overview/index.md), explore a
[worked model](examples/index.md), or follow the
[mathematical foundations](bellman-calculus/index.md).

## 2 People and support

The Bellman language was created by Christopher D. Carroll and Akshay Shanker.
It is named in honor of Richard Bellman, whose ideas on breaking a dynamic
program into stages, linked by functional equations, are the foundation of the
language.[^bellman]

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

## 4 Take part

Questions, corrections and contributions to the code, documentation and
examples are welcome on [GitHub](https://github.com/econ-ark/bellman).
To report a problem or suggest an improvement,
[open an issue](https://github.com/econ-ark/bellman/issues).
For a model example, include the equations and the behavior you expect.

The software is available under the
[Apache License 2.0](https://github.com/econ-ark/bellman/blob/main/LICENSE).

## 5 Homepage media

The Mile 12 market sequence combines drone footage with a wider photograph of the same market in Lagos, both taken by Ayorinde Ogundele on 8 March 2025. The edit uses an animated crop and a navy-to-ice color treatment. Both sources and the edited sequence are licensed under CC BY-SA 4.0. [Market Movements](https://commons.wikimedia.org/wiki/File:Market_Movements.webm) · [Mile 12 market photograph](https://commons.wikimedia.org/wiki/File:Drone_shot_of_a_section_of_the_Mile_12_food_market.jpg) · [License](https://creativecommons.org/licenses/by-sa/4.0/)

The night-light sequence uses twelve annual satellite composites from 2012 to 2023 with the same crop and color treatment throughout. Credit to NASA’s Scientific Visualization Studio. [Change in Night Lights between 2012 and 2023](https://svs.gsfc.nasa.gov/5276)

Henderson, Storeygard and Weil (2012) show how satellite observations of night lights can supplement official estimates of income growth, especially where national accounts are poor. [Measuring Economic Growth from Outer Space](https://doi.org/10.1257/aer.102.2.994)

The sculling video comes from Wikimedia Commons and is shown in navy and ice. An adaptation of a share-alike work retains its source's license.

- Xabier Cañas. Video, CC BY-SA 4.0. [A single scull on the river Oria at Orio from the air, 2023](https://commons.wikimedia.org/wiki/File:Piragua_Oria_ibaian.webm)

## 6 Typefaces

The site sets its display line in Syne, its statements and headings in Space Grotesk, its text in Archivo and its code in IBM Plex Mono. All four are published under the SIL Open Font License and served from the site itself, with each family's license text beside its files.

[^bellman]: Richard Bellman, *Dynamic Programming* (Princeton University Press, 1957), Preface, pp. vii and xi–xii, and Chapter I, §§4–5, pp. 7–9.

[^dynspec]: Pablo Winant and Ousema Bouaneni, *Dyno*, EconForge, <https://github.com/EconForge/dyno.py>. The dynspec grammar is the file [`src/dyno/dynspec/grammars/grammar.lark`](https://github.com/EconForge/dyno.py/blob/312e8eaa456f5d9c23cfecdb09d979a58ec7acc4/src/dyno/dynspec/grammars/grammar.lark), cited at commit `312e8ea`.
