---
title: Model directory layout
tags:
  - docs/reference
audience: user
type: reference
---

# Model directory layout

> [!summary]
> Each model of the repository has a folder of its own under `applications/`, and every such folder keeps the files the language reads in one subfolder, `declaration/`: the recipe, the trellis and period files, the calibration and settings files, and one folder for each stage, holding the stage file, its methods file and its note. Beside `declaration/` stand the folder's first page, `README.md`, its `economics.md`, and its code, tests, papers and results. This page states the layout, the rules it follows and the variants of a model it admits. The package's functions that read these files require no layout, since they read the paths a recipe or a trellis file writes; the layout is the convention of the repository's model folders, which Bellman Workbench reads and a test of the repository checks.

> [!info]- Relationship with other documents
> **Builds on** — [Trellises](../07-trellis.md) §§1, 5: the trellis file, the period file and the recipe, and the paths a recipe writes; [Methodization](../04-methodization.md): the methods, settings and calibration files.
> **Used by** — [The Bellman factory](../08-bellman-factory.md) §3 and [Recipe functions](../API/factory/spec-factory.md): the registry a recipe is read from; [Bellman Workbench](../../overview/07-workbench.md): the folder it opens and the folder its form `new trellis` writes.

> [!note]- Key terminology
> | Term | Meaning |
> |---|---|
> | **Model folder** | The folder of one model under `applications/`, laid out as this page states. |
> | **Stage key** | The name under which a period lists a stage, chosen by the author. A model's recipe normally uses the name of the stage's folder, which the stage file and the note share; an equation variant or a second use of a stage lists the folder under another key (§§2.3, 3). |
> | **Registry** | The folder a recipe stands in, from which every path the recipe writes is read; in a model folder, its `declaration/` ([wiki](../../wiki/spec_factory.md)). |
> | **Recipe** | The file `spec.yml` that names the trellis file, each stage's file and, for each stage, the ordered files from which its parameter values, its settings and its methods are read ([wiki](../../wiki/spec_factory.md)). |
> | **Source** | A file of one kind a recipe names: a calibration or settings file of assignments, by its path without the extension, as `calibration/durables`, or a methods file, the `.bl` addition beside a stage file, by its path with it, as `stages/tenure/methods.bl` ([wiki](../../wiki/spec_factory.md)). |
> | **Variant** | A second version of a model, written beside the first in the same folder (§3). |

## 1 The layout

The durables model of Dobrescu and Shanker (2026), in which a household keeps or adjusts its housing stock over fifty-one ages, shows the layout:

```text
applications/durables/
├── README.md                   the first page: the model in one sentence, a drawing where the folder holds one and the command that opens it
├── economics.md                the economics in full
├── declaration/                every file the language reads
│   ├── spec.yml                the recipe: trellis: trellis.yml and, for each stage, its stage file and its sources
│   ├── spec.two-stages.yml     a second recipe: trellis: trellis.two-stages.yml, with the same stage files
│   ├── trellis.yml             the periods, counted backward from the terminal one
│   ├── trellis.two-stages.yml
│   ├── period.yml              the template of one period, which the trellis file repeats
│   ├── period.two-stages.yml
│   ├── stages/
│   │   ├── tenure/             tenure.bl  methods.bl  tenure.md
│   │   ├── keeper_cons/        keeper_cons.bl  methods.bl  keeper_cons.md
│   │   ├── adjuster_cons/      adjuster_cons.bl  methods.bl  methods.adjuster_method.bl  adjuster_cons.md
│   │   └── bequest/            bequest.bl  methods.bl
│   ├── calibration/            durables.yml  wage_schedule.yml
│   └── settings/               durables.yml
├── code/                       wage_schedule.py, which writes each period's income into the trellis
├── results/                    what the code writes; git ignores it
└── tests/                      test_durables_ast.py
```

`declaration/` holds every file the language reads: the recipe, the [trellis](../../wiki/trellis.md) and [period](../../wiki/period.md) files, the folders `calibration/` and `settings/`, under `stages/` one folder for each [stage](../../wiki/stage.md), holding its stage file, written in `.bl`, its methods file `methods.bl`, an addition to the stage file written in the same language, and its note; a second selection of a stage's methods is another addition in the same folder, `methods.<variant>.bl`. Beside `declaration/` stand `README.md`, `economics.md`, `code/` for the folder's programs, `tests/` for its tests, `results/` for what its programs write, `paper/` for the descriptions of its stages that Bellman Workbench's button `paper` writes for a paper's model section (§4), and `reference/` for the papers it keeps, as PDF files, such as `applications/benhabib-2019/reference/benhabib-bisin-luo-2019.pdf`; the durables folder keeps none. A folder holds only the parts its model has: `applications/portfolio-choice/`, whose stage files the portfolio–consumption application assembles, holds its stage folders, a `README.md` and its tests, and no recipe.

The portfolio–consumption application, `applications/cons-port/`, holds its stages under `declaration/stages/`, each stage's methods files beside its stage file, `methods.bl` and the replacing selections `methods.<variant>.bl` its trellis files name, and two recipes, one for each order of its period, each with its trellis file. Beside them stand its trellis files of records, `declaration/trellis.<name>.yml`, each of which writes every stage of a period as a record naming the stage file and the calibration, settings and methods files the stage is bound from, all of the folder's own `declaration/`, and is read with no recipe ([Trellises](../07-trellis.md) §3). Beside `declaration/` it keeps `code/` for its numerical tool, `tests/`, `notebooks/` for its notebook and its earlier reference notebook, and `reference/legacy/` for its fixed numerical reference, with the reference's recorded sources in the earlier YAML form.

The form `new trellis` of Bellman Workbench writes a new model folder in this layout ([Bellman Workbench](../../overview/07-workbench.md) §6), with two more files at the folder's top, beside its `README.md`: the record of the form's answers, `answers.yml`, and a `.gitignore`. The repository's test `packages/bellman/tests/test_layout.py` fails on a folder under `applications/` that git tracks and that departs from the layout, so it fails on a tracked folder that holds those two files at its top.

## 2 The rules

### 2.1 What you write where

Every file the language reads stands under `declaration/`, and the only other files there are the notes of the stages, each in its stage's folder. A stage file holds the mathematics of one stage, its declarations, its typed blocks and its equations; its methods file, beside it, holds the numerical methods of its operators and the settings they read, declared with their sets ([Methodization](../04-methodization.md)); the YAML files hold the rest: the periods and the trellis that compose the stages, the values of the settings, the parameter values, and the recipe that names them all. What the folder holds for its readers and for its programs, the README, the economics, the code, the tests and the papers, stands beside `declaration/`.

The division between the stage file and the other files follows the economics. A finite set of choices belongs in the stage's domain definitions, and the grid sizes and tolerances that approximate a continuous domain belong in the settings. Keeping the files apart does not settle which is which, so decide for each number whether it changes the household's problem or only the numerical calculation.

`declaration/` is the model's **registry**, the folder a recipe stands in and from which every path the recipe writes is read. `load_recipe` of `bellman.trellis` is therefore given `declaration/` and the name of the recipe; run from the repository root, it reads the durables model:

```python
from bellman.trellis import load_recipe

syntactic = load_recipe("applications/durables/declaration", "spec.yml")
print(len(syntactic["periods"]), "periods, from", syntactic["provenance"]["trellis"]["path"])
tenure = syntactic["periods"][0]["stages"]["tenure"]
print(f"{'stage':12}{tenure['stage']['origin']}")
for kind in ("calibration", "settings", "methods"):
    for source in tenure["provenance"]["source_lists"][kind]:
        if "path" in source:
            print(f"{kind:12}{source['path']}")
```

```text
51 periods, from applications/durables/declaration/trellis.yml
stage       applications/durables/declaration/stages/tenure/tenure.bl
calibration applications/durables/declaration/calibration/durables.yml
settings    applications/durables/declaration/settings/durables.yml
methods     applications/durables/declaration/stages/tenure/methods.bl
```

The call returns the [syntactic trellis](../../wiki/trellis.md), the model as written, with one record for each stage and period. The record of the tenure stage in the terminal period, `periods[0]`, names the stage file and the three files the stage is bound from, each read at the path the recipe writes. Bellman Workbench reads the same folder: it opens on a model folder, binds the open stage file through the recipe `declaration/spec.yml` where the folder holds one, and shows the folder's files in its tree ([Bellman Workbench](../../overview/07-workbench.md) §1).

### 2.2 What a recipe names

A recipe writes the path of every file it reads, from its own folder, and the package finds no file by a name or a suffix ([Trellises](../07-trellis.md) §5). In the durables recipe, `trellis: trellis.yml` names the trellis file, and the entry of the stage key `tenure` names its stage file, `stage: stages/tenure/tenure.bl`, and lists its sources, the calibration and settings files named by their paths without the extension, `calibration/durables` and `settings/durables`, and the stage's methods file, an addition, by its path with it, `stages/tenure/methods.bl`. A trellis file names the period file it repeats, `template: period.yml`, from its own folder in the same way. A recipe without `trellis:`, or an entry without `stage:`, is refused with a sentence that says what to write, `stage: stages/tenure/tenure.bl` for the entry `tenure` ([Refusals](refusals.md)). A recipe and a trellis file that disagree on the stage keys are refused under the rule `recipe-template-agreement`, so that a mismatched pair does not load. A suffix in a file's name, the `two-stages` of `spec.two-stages.yml`, is for the reader alone: the links between a recipe, its trellis file and its period file are the lines these files write.

### 2.3 One folder for each stage

The files of a stage stand together in one folder, `declaration/stages/<stage>/`: the stage file `<stage>.bl` and the note `<stage>.md`, the page that explains the stage, which share the folder's name, and the methods file `methods.bl`, an addition to the stage file. A method belongs to the operators of one stage, so a stage reused in another model is copied with its methods as one folder. Calibration and settings sources may be reused by stages, so they stand in `declaration/calibration/` and `declaration/settings/`. Sharing a source file does not identify all its names across the model: two stages in one period that declare one parameter name share that period parameter, while their field names remain local and the same parameter name in another period denotes another parameter. The recipe names the two files of a stage's folder that the language reads, `stage: stages/tenure/tenure.bl` and the methods file `stages/tenure/methods.bl`, and it normally lists the stage under the folder's name as its stage key, as the durables recipe lists `tenure`; an equation variant or a second use of the stage lists the folder under another key (§3). A stage's folder holds the files the stage has: the bequest of the durables model, which has no note, holds its stage file and its methods file; the adjuster's folder holds a second addition, `methods.adjuster_method.bl`, which a recipe may name after the first.

### 2.4 Variants side by side

A variant of a model stands beside the files it varies, in the same `declaration/`, and not in a folder of its own, and every link between its files is written in them. §3 sets out the three kinds.

### 2.5 The first page of a folder

`README.md` is the page a visitor reads first. It states the model in one sentence, shows a drawing of the model where the folder holds one, gives the command that opens the folder in Bellman Workbench, `bellman-workbench applications/durables`, and names the folder the code writes into. `economics.md`, where a folder has one, holds the economics in full: the model's equations, its calibration with its sources, and what the stage files cannot state. A folder without `economics.md`, such as `applications/portfolio-choice/`, explains its model in its `README.md` and in the notes of its stages.

### 2.6 Where generated files stand

The recordings of a model's stage files, the parsed term (`<stage>.bl.ast.json`) and the encoding of the elaborated stage (`<stage>.bl.stage.json`) of each, stand with the package's tests, in `packages/bellman/tests/snapshot/corpus/<model>/`, and not in the model folder. The test `packages/bellman/tests/sym/test_corpus.py` parses and elaborates every stage file under `applications/` and compares the results with these recordings, and `PYTHONPATH=. python tests/snapshot/record.py --corpus`, run from `packages/bellman/`, writes them again. The model's code writes into `results/`, which git ignores, as it ignores `model-explorer/`, where Bellman Workbench writes the views it exports. The generated files a folder tracks are records kept on purpose: the portfolio–consumption application keeps its fixed numerical reference, `reference/legacy/port_cons_h5.npz` with its manifest, and `reference/legacy/preflight.json`, the record that identifies the notebook and the helper from which the reference was computed; the record of the comparison with that reference that its acceptance test writes, `code/tests/evidence/reference-comparison.json` and `.txt`; and the figures its earlier reference notebook drew, the PNG files under `notebooks/port-cons/figures/`, beside which `stage_lifecycle.svg` is a drawing and not a generated file.

## 3 Variants

A **variant** is a second version of a model that shares most of its files with the first. It is written beside the first, in `declaration/`, in one of three ways, according to what it changes.

- **A variant of the route**, which changes the stages a period holds or how the periods are joined, is a second set of the three files: a recipe `spec.<name>.yml`, which names its trellis file under `trellis:`; the trellis file `trellis.<name>.yml`, which names its period file under `template:`; and the period file `period.<name>.yml`, the name between the dots being the author's choice. The durables folder keeps its route without the tenure stage in this way: `spec.two-stages.yml` names `trellis.two-stages.yml`, which names `period.two-stages.yml`, and the recipe names the same stage files and sources as `spec.yml`, without those of the tenure stage, so that `load_recipe("applications/durables/declaration", "spec.two-stages.yml")` reads the second route ([Trellises](../07-trellis.md) §5; [The Bellman factory](../08-bellman-factory.md) §3.6). Since the suffix links nothing, a recipe may name a trellis file of another suffix where that is the intent.
- **A variant of the values**, which changes the numbers a stage receives and not the route, needs no second set of files. It is a further source file, such as `calibration/near_terminal.yml` or `settings/fine.yml`, which a recipe lists after the common one in a stage's list of sources, or in the list of sources of a range of periods, so that its values stand over the common ones ([The Bellman factory](../08-bellman-factory.md) §§3.2, 3.4). A variant supplied when the recipe is read is a **fill**, a mapping given by keyword to a **slot**, a place written `$name` in a list of sources ([The Bellman factory](../08-bellman-factory.md) §3.3).
- **A variant of an equation** is another stage folder beside the first, holding the changed stage file, which a second recipe names under the same stage key in place of the first, as `tenure: {stage: stages/tenure_flat/tenure_flat.bl, …}` names the stage file of a folder `stages/tenure_flat/`.

Distinct uses of one stage file need distinct stage keys, each with its own bindings, also when the two uses stand in one period.

## 4 What each file contains

| File | Contents |
|---|---|
| `declaration/stages/<stage>/<stage>.bl` | The stage file: the declarations, typed blocks and equations of one stage. |
| `declaration/stages/<stage>/methods.bl` | The stage's methods file, an addition to the stage file beside it, which the package reads with the stage file: a `.bl` file that opens with `@methods:` and the stage's name, whose blocks name blocks of the stage by their ids and add their typing entries and their lines to them, and whose file-level entries type a place by its path ([Methodization](../04-methodization.md)). Each of the four stages of the retirement-choice application has one. A replacing selection stands beside it as `methods.<variant>.bl`, as `methods.bellman_method.bl` of the benhabib-2019 application does, and a recipe's methods list names the file it binds. No `.bl` file stands outside a stage's folder. |
| `declaration/stages/<stage>/<stage>.md` | The stage's note, which explains the stage file. |
| `declaration/calibration/<name>.yml` | Economic parameter values, under the top key `calibration`. |
| `declaration/settings/<name>.yml` | Numerical setting values, under the top key `settings`. |
| `declaration/period.yml` | The period file: the stage keys of one period and the connectors within it. |
| `declaration/trellis.yml` | The trellis file: the periods of the model, each written out or given by a period file repeated, and the inter-period connectors. |
| `declaration/spec.yml` | The recipe: the path of the trellis file and of each stage's file, from this folder; for each stage and each kind, the ordered sources and slots; the `registry` block. |
| `README.md` | The folder's first page (§2.5). |
| `economics.md` | The economics in full (§2.5). |
| `code/` | The model's programs: code that writes values into the syntactic trellis, supplies boundary data or calls numerical routines. |
| `tests/` | The model's tests, such as the structural test that parses each stage file and compares its terms with terms written by hand. |
| `reference/` | The papers the model rests on, as PDF files. |
| `results/` | What the model's programs write (§2.6). |
| `paper/` | For each stage, the two files Bellman Workbench's button `paper` writes once and never rewrites: `<stage>.md`, the printed card of each of the stage's [builders](../../wiki/builder.md) ([A builder](../API/stage/04-builder.md)), the link to the drawing and a footnote with the SHA-256 digest of the stage file and of each file the stage is bound from; and `<stage>.svg`, the drawing of the graph of the stage's [backward builders](../../wiki/backward_builder.md). An author converts the Markdown to LaTeX with Pandoc. |

A calibration or settings file is read whether it is spelled `.yml` or `.yaml`, and the two are told apart by their top keys, not by their names or their extensions; a methods file is a `.bl` file, told apart from a stage file by its first line, `@methods:`. A **connector** selects a continuation state field of one stage occurrence and an arrival state field of another without changing either local name; an **inter-period connector** does so between consecutive periods. A bare endpoint must identify one eligible field at its side of the connection; a stage key qualifies an ambiguous endpoint ([Periods](../06-period.md) §2). The recipe chooses the sources of each binding; it contains no stage equation and determines the sequence of periods only through the trellis file it names.

## 5 Paths in a model's documents

The documents of a model folder, its `README.md`, its `economics.md`, its stage notes and the docstrings of its code, write a path in one of two ways. A path that says where a file of the folder stands is written from the model folder, `declaration/stages/tenure/tenure.bl` or `declaration/calibration/durables.yml`, whichever document writes it. A path quoted as a recipe or a trellis file writes it is kept as that file writes it, from the file's own folder, and is introduced as that file's line: the recipe's `stage: stages/tenure/tenure.bl`, or its methods source `stages/tenure/methods`.

## 6 Paths and the readers

The functions that read files interpret their path arguments differently:

| Reader | Path supplied |
|---|---|
| `bellman.stage.load_stage(path)` | A `.bl` file, read into a record. |
| `bellman.trellis.load_trellis(file)` | A trellis file of records; the stage files and the mapping files it names are read from its folder. |
| `bellman.trellis.load_recipe(directory, recipe)` | A registry, in a model folder its `declaration/`, and the name of its recipe, `spec.yml` or a variant's `spec.<name>.yml`; the trellis file and the stage files are the paths the recipe writes, read from that folder. |
| `bellman.trellis.assemble_trellis(directory, recipe)` | The same two arguments; the specified trellis in one call. |

`load_recipe` returns the syntactic trellis, and `assemble_trellis` elaborates and binds it in one call. `load_trellis` reads a trellis file whose periods write their stages as records, each naming its stage file and its three mappings inline or as paths, and needs no recipe. An application can also build the trellis dictionary itself, one period at a time with `bellman.trellis.accrete`. [The trellis factory](../API/factory/trellis-factory.md) states these calls.

A record that `elaborate_trellis` of `bellman.trellis` reads holds a `stage` mapping with `text` and `origin`, as `load_stage` writes it, and mapping-valued `calibration`, `settings` and `methods`; a path string in place of the mapping is refused. Precedence is settled in the syntactic trellis before elaboration; the elaborator and the verbs merge no file and no default. [The factory API](../API/factory/index.md) gives the complete record. Moving a file requires updating the recipe, the trellis file or the application code that names it.

## 7 Stage files in the earlier YAML form

`load_stage` of `bellman.stage` reads a stage file written in `.bl` and refuses any other file under the rule `readable-file` of [Refusals](refusals.md). A stage written in the earlier YAML format is therefore rewritten in `.bl`, since changing its extension translates none of its declarations, type words, equations or shock laws. YAML remains the format of the recipe, the trellis and period files, and the calibration and settings files; a methods file is written in `.bl`, as an addition to its stage file. The earlier YAML stages of the portfolio–consumption application are kept, as recorded sources of its fixed reference, under `applications/cons-port/reference/legacy/syntax/`.

## 8 Related references

- [Trellises](../07-trellis.md) states the trellis file, the period file and the paths a recipe writes.
- [Methodization](../04-methodization.md) describes the methods file and the settings and calibration files beside it.
- [Stage functions](../API/factory/stage-factory.md) specifies loading, elaborating and binding one stage.
- [Period functions](../API/factory/period-factory.md) specifies accretion and the order of a period.
- [Recipe functions](../API/factory/spec-factory.md) specifies the recipe, its merge and its slots.
- [The trellis factory](../API/factory/trellis-factory.md) specifies the trellis file and the calls on a trellis.
- [Bellman Workbench](../../overview/07-workbench.md) opens a model folder and writes a new one in this layout.
