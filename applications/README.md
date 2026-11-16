---
title: Applications
audience: developer
type: index
---
# Applications

Worked economic models written in Bellman-SYM. Bellman-SYM is the
language: a stage is written in a `.bl` file, which parses and produces
the stage's semantic graph; the Bellman calculus supplies the rules by
which that graph is read as Bellman operators. (The distinction that
remains is between the Bellman calculus — the rules — and Bellman-SYM —
the language. There is no separate user-facing language for the graph.)
The `.bl` surface is a conservative extension of dynspec with stage
typing. Files are parsed by the spec 0.3 grammars; the package is
`packages/bellman` (distribution `bellman`). New applications are added
here, one folder per model.

The canonical grammar lives with the package:
`packages/bellman/bellman/syntax/grammars/` (the typed stage grammar and
term listings). The worked models live here, one folder per model, each
in the layout below; the spec's §2 listings mirror their stage files. The
corpus test's recordings of the stage files, their parsed terms and the
printed texts of their stages, stand with the package's tests, in
`packages/bellman/tests/snapshot/corpus/<model>/`.

## The layout of a model folder

Every folder keeps the files the language reads in its subfolder
`declaration/`, and the rest beside it:

```text
<model>/
├── README.md           the model in one sentence, a drawing where the folder holds one and the command that opens it
├── economics.md        the economics in full
├── declaration/        every file the language reads
│   ├── spec.yml        the recipe; a variant's recipe is spec.<name>.yml
│   ├── trellis.yml     the trellis file; a variant's is trellis.<name>.yml
│   ├── period.yml      the period file; a variant's is period.<name>.yml
│   ├── stages/<stage>/ the stage file <stage>.bl, its methods file methods.bl and its note <stage>.md
│   ├── calibration/    the parameter values
│   └── settings/       the numerical settings
├── code/               the model's programs
├── results/            what the programs write; git ignores it
├── tests/              the model's tests
└── reference/          README.md, a note that cites the papers kept for reference; their PDF files are not kept here
```

A folder holds the parts its model has. The documentation page
[Model directory layout](../docs/Bellman-Sym/reference/model-directory-layout.md)
states the rules of the layout, its variants and the paths a model's
documents write, and `tests/test_application_layout.py` checks every
folder against it.

## Structural tests

The structural tests of a model, its files `tests/test_*_ast.py`, parse the
model's stage files and compare each parsed term with a term that the test
writes. They import the module `stage_ast`, which gives the parsed term of a
stage file, the spellings in which those tests write their expected terms
and `check`, which names the first place where a parsed term and an expected
one differ.

## Naming

Bellman-SYM had an earlier surface: stage files written in YAML and read
by the dolo and dolang pipeline, archived outside the repository on 13 September 2026. Older text
called that surface *dolo-plus*, *dolo+*, or *dolang+*. In these
applications the language is called Bellman-SYM throughout, and the YAML
files are referred to as its earlier YAML surface. Folder and code names
that contain `doloplus` (registry folders, module names) are identifiers
and are left as they are.

## Folders

- `benhabib-2019/`, `consumption-savings-iid/`, `housing-owner/`,
  `portfolio-choice/`, `retirement-choice/` — `.bl` stage files with
  their walkthrough pages and structural tests.
- `cons-port/` — the portfolio–consumption application: its stages
  written with the maximization alone and the methods files that
  complete them, with the two recipes of its two orders, in `declaration/`;
  the model's numerical tool in `code/`; the tests of its stages, its
  recipes and its solve in `tests/`; and the fixed reference with its
  recorded sources in the earlier YAML form in `reference/legacy/`. Its
  three lessons stand in `tutorials/models/cons-port/`.
- `consumption-perfect-foresight-crra/` holds the perfect foresight
  consumption model with CRRA utility, the buffer-stock stage without
  its income shocks. Its stage file, which sends human wealth backward as
  a constant field and has one derived parameter, the
  methods file `methods.bl` that solves it in closed form with
  `!explicit`, the methods file `methods.egm.bl` that solves it by the
  endogenous grid method and its calibration stand in `declaration/`;
  the module that binds both methods files and compares the two
  solutions, with the notebook that shows each step, stands in `code/`.
  Its documentation page is
  `docs/examples/consumption-perfect-foresight-crra/perfect_foresight.md`.
- `portfolio-choice/` — the earlier folder of the same model, written
  the explicit way; superseded by `cons-port/` and marked for deletion
  (AAS, 28 October 2026).

## Archived applications

The applications written against the earlier stage-YAML surface and the
dolo and dolang pipeline, and the pipeline demonstrations on that surface,
were archived outside the repository on 13 September 2026, from their
paths under `applications/`.
