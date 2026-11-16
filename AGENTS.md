# AGENTS.md — econ-ark/bellman

> `CLAUDE.md` is a symbolic link to this file, so that Claude Code, Codex and Cursor read the same text. Edit `AGENTS.md`; never replace the link with a copy.

## What this repository is

A dynamic programming model in economics is usually written twice, as mathematics and as solver code, and its meaning, which operators it composes and under which assumptions, stays implicit in the code. So a new model starts again, and another person's is hard to read, check or reuse.

Project Bellman provides the language Bellman-SYM. A model is written in it once, as stages; a stage is one self-contained decision problem in a `.bl` file that both people and AI can read. The package `bellman` builds each stage as an object that prints its equations beside the operators they denote; their meaning is fixed by the Bellman calculus, the project's mathematics, with no solver attached. Stages written separately join into models, and a new model reuses them; parameter values and numerical methods are bound afterwards. The package does not solve or simulate a model. `README.md` describes the folders, the installation and the tests; `docs/changelog.md` records each release; the mathematics is in `docs/bellman-calculus/`; the project's terms are defined in the concept wiki under `docs/wiki/`.

This repository is the public export of the team's private development repository. Every commit on `main` is the public subset of one development commit, which the commit message names. Code and documentation are developed there and arrive here by export. A pull request opened here is reviewed here and carried into the development repository before the next export, so that the two never diverge; an issue is filed here.

## Commands

```bash
./install-dev.sh                      # venv/ with the dependencies and the packages bellman, asva, bellman-workbench
source venv/bin/activate
python -m bellman applications/cons-port/declaration/stages/cons/cons.bl   # prints one stage's sheet
pytest packages/bellman -n auto       # the default set of the package's tests: every case not marked complete_set
pytest packages/bellman -n auto --complete   # the complete set: every case, run before a merge
pytest tests applications tutorials packages/asva/tests -n auto
mkdocs build --strict                 # the documentation site into site/
```

## Rules for an agent working here

- **Verify names before use.** Before using any function, class, parameter or key of a stage file, find it with `rg` or a file search. A guessed name fails silently as a `NameError` or `AttributeError` far from its cause. For a stage file, copy the structure of the `.bl` files under `applications/` and their methods files rather than improvise.
- **Never overwrite a user's edits in a Jupyter notebook.** Before any notebook operation, re-read the notebook, since the user may have edited it since you last saw it; if its cells differ from what you expect, stop and ask; review `git diff` of a notebook before committing it.
- **Coding style.** Explicit composition of primitive operators, in the manner of Backus's functional programming; no stacks of pass-through wrappers. Each piece of a stage is reached from the piece that contains it, and every piece answers for itself with the same verbs, `view()`, `denote()`, `list()`, `diagram()`, `kernel()`, `compile_kernel()`, `signature()`.
- **The model and its numerics are kept apart.** Discrete grids of the model are declared in the stage file; numerical settings, such as the number of grid points or a tolerance, are settings; parameter values are the calibration. Nothing is differentiated automatically: the author writes marginal and envelope lines.
- **"Parameter" names an input of the model, and "setting" an input of a numerical method.** A parameter is an input on which the mathematical problem depends, the problem as it is stated before any numerical method is chosen: a stage file declares it and the calibration supplies its value, or a line defines it from other parameters by `:=` (`docs/wiki/parameters.md`). A setting is an input of a numerical method: the size or the bounds of a grid that approximates a continuous domain, a number of quadrature nodes, a tolerance, an iteration limit (`docs/wiki/settings.md`). Never call a setting a parameter, with or without a qualifier: not a grid parameter, a solver parameter, a method parameter, a tuning parameter or a hyperparameter. The rule holds in documentation, comments, docstrings, names, commit messages and chat, and it holds where another toolkit's documentation calls such an input a parameter: the number of points of a toolkit's asset grid is a setting of that toolkit's method. To classify an input, ask whether it changes the economic problem or only how that fixed problem is approximated (`docs/bellman-calculus/catalogues/parameters-settings.md`).
- **One changelog.** Every entry goes to `docs/changelog.md`; never create a root `CHANGELOG.md`.
- **Register.** Plain academic English in documentation, comments, docstrings, commit messages and chat, written for an applied economist: no engineering-status or startup phrasing, no colloquialisms, literal verbs. Define every technical term in plain words at first use, or link it to its page under `docs/wiki/`. A function is written in mathematical italic and everything else in roman on every printed surface.
- **Mathematics in chat is written in Unicode glyphs** (𝕋, ∘, ρ, ⟨ ⟩, subscripts); LaTeX belongs only in files.
- **Markdown under `docs/` is read by Obsidian and by MkDocs.** Keep `#tags`, `[[wikilinks]]` and `> [!note]` callouts; use headings, not `---`, between sections; a published page cites published material by a bibliographic reference, never by a path outside this repository.
- **Semgraph terminology and labels.** The semantic graph of a stage is the **semgraph**, and `semgraph` is the module name; an initial diagram, a builders graph, a grain or a value bundle is an aspect of a semgraph, not another named representation system. Say inputs and outputs, or builder signature, never boundary. `signature()` answers one record with two parts, `inputs` and `outputs`; a decision builder's or a decision push-forward's is the signature of the operator at a policy. A drawing displays **Pullback of the function 𝑉 along the law of motion 𝑔** for composition with 𝑔, **Value aggregation 𝐺** where it applies and otherwise **Apply 𝐺**, and a sub-builder by its retained function name or its ordered output fields. Parameters are named in complete definitions and are not separate wires; the policy is typed once, on the policy builder's output; a decision builder or a decision push-forward is the operator at a policy, refers to the policy from its evaluation or insertion box, and is wired to the policy builder at no level. Construct this in the native semgraph: the parameters and the policy are references in a box's data and are drawn as no wire, and the renderer draws what the graph holds.
- **A perch is an information set,** not an operator endpoint: the three perches are internal terminology, and a heading says "Bellman equation" or "first-order conditions", never "ADC".

## Where things are discussed

Issues and pull requests of this repository. The project is funded by the Alfred P. Sloan Foundation as part of [Econ-ARK](https://econ-ark.org).
