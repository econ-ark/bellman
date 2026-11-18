---
title: "Tutorials"
tags: [tutorial]
audience: user
type: tutorial
---

# Tutorials

> [!IMPORTANT]
> **Summary**
>
> This collection holds the lessons of Bellman calculus, notebooks that build and inspect models from the repository's files, in three groups. Start with the first lesson of Getting started; each later lesson names the lessons it builds on.

## 1 Getting started

The main Bellman objects and operations, in five lessons read in order, on the stages of the portfolio–consumption model.

1. [The stage as an object](getting-started/01-the-stage.ipynb): how a [[stage]], one step of a period's Bellman problem, is constructed from its file, and what the object holds. No prerequisite.
2. [Value functions and the backward builders](getting-started/02-value-functions.ipynb): how a stage computes the value at each [[perch]] from the value at the next, and where its file states a value's derivative. After lesson 1.
3. [Distributions and the forward builders](getting-started/03-distributions.ipynb): how the declared shocks carry the distribution of the state through a stage, paired with the expectation. After lessons 1 and 2.
4. [Parameter values, methods and settings](getting-started/04-parameters-methods-and-settings.ipynb): how a stage is bound to its parameter values, numerical methods and settings, and what each binding changes. After lessons 1 and 2.
5. [Periods and trellises](getting-started/05-periods-and-trellises.ipynb): how stages join into a [[period]] by the fields they share, and periods into a [[trellis]] built backwards. After lessons 1 and 4.

## 2 Specific topics

One further idea each; a lesson can be read once the lessons its entry names have been read, in any order among themselves.

- [Expectations and nested aggregation](topics/expectations.ipynb): how a value taking two expectations, one inside the other, is stated with the maps around each. After Getting started 2 and 3.
- [The mathematics a stage carries](topics/the-native-mathematics.ipynb): how a stage holds its declarations as a [[signature]], a typed vocabulary of the sets and functions the file declares, and its functions, laws of motion and operations as terms, expressions written in that vocabulary; what each denotes in a forward and a backward model; which conditions the construction records with their status and what decides each; and what another program reads. After Getting started 1 and 2.
- [Branching](topics/branching.ipynb): how a stage whose continuation branches, by a choice or a draw, is written, constructed and drawn in a period and a trellis. After Getting started 1, 3 and 5.
- [Kernels as functions](topics/kernels.ipynb): how the rule an operation applies is read as the source text of a plain Python function, evaluated on a grid, composed with another into one step of a builder, compiled by Numba and given the values of a new calibration without compiling again, and what a solver reads from a builder's record of its kernels. After Getting started 2 and 4.

## 3 Model walkthroughs

How the parts fit together for a named economic model: construction, numerical solution and results, where the model supports them. A lesson's folder under `models/` is named as the folder of `applications/` holding the model's parameter values, methods and numerical tool.

The portfolio–consumption model, in order:

1. [Two stages, two orders](models/cons-port/01-two-stages-two-orders.ipynb): how a consumption stage and a portfolio stage form a period in either order, the order following from the fields they share. After Getting started 1.
2. [A trellis built backwards](models/cons-port/02-a-life-cycle-built-backwards.ipynb): how the stages are bound, one period is repeated six times, and terminal inputs are supplied separately. After lesson 1 of this model.
3. [Solving the two orders](models/cons-port/03-solving-the-two-orders.ipynb): how both orders are solved, one order's value recovered from the other's, and one stage's method changed. After lessons 1 and 2 of this model.

The within-life model of Benhabib, Bisin and Luo:

- [The Bellman factory on the Benhabib–Bisin–Luo model](models/benhabib-2019/the-factory-on-benhabib.ipynb): how a model kept in a registry, the folder of its stage files and their parameter values, methods and settings, is read through its recipe into a trellis of 37 periods, bound, changed by a fill and a sweep, and rebuilt by hand; [[spec_factory]] defines the recipe, the fill and the sweep. After Getting started 5.

## 4 Rules of the collection

Each lesson has one maintained source, its notebook here, which the documentation site does not publish, and runs on its own from a fresh kernel, building what it uses from the files. In its first cell, a colored box summarizes what the reader does, what is inspected, and whether the lesson constructs, evaluates or solves; a second colored box names its prerequisites and the pages that give the mathematics; and a bordered box holds a table that defines its terms. None of the boxes folds. Its second cell lists the files it reads. `tutorials/tools/execute_lessons.py --record` executes each lesson (several at a time in separate processes; `--jobs` sets how many) and records in `tutorials/lessons.json` the digests of the lesson and of those files; `tutorials/tests/test_lessons.py` fails when either has changed since. A notebook that reproduces a paper's tables or explores research results stays with its application.

## 5 Requirements

The lessons run in the repository's Python environment, which `install-dev.sh` at the repository root creates. Each lesson names the Jupyter kernel `bellman-ddsl`, which `python -m ipykernel install --user --name bellman-ddsl`, run once in that environment, registers. A lesson's first code cell, `import checkout`, reads the module `checkout.py` of this folder through a symbolic link in the lesson's folder; the module makes the package importable and sets the working directory to the repository root. The drawings need nothing more: `install-dev.sh` installs the Python package `pygraphviz`, whose Graphviz libraries lay them out. A reader who runs a lesson by hand needs the viewer of its interactive view, Google's Model Explorer, which `pip install -e "packages/bellman[explore]"` installs from the repository root, while a recorded run of the lessons writes the view's two files and starts no server.
