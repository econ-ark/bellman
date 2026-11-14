---
title: "The execution of the-factory-on-benhabib.ipynb (AMD-FAC-002, F17)"
audience: developer
type: model-note
topic: [applications]
---
# The execution of `the-factory-on-benhabib.ipynb` (AMD-FAC-002, F17)

The notebook is now the lesson [`tutorials/models/benhabib-2019/the-factory-on-benhabib.ipynb`](../../../tutorials/models/benhabib-2019/the-factory-on-benhabib.ipynb) of the tutorials
collection; the record below describes it as it stood before its conversion
to a lesson on 26 September 2026, at its former path in `applications/benhabib-2019/`.

The notebook `applications/benhabib-2019/the-factory-on-benhabib.ipynb` has 53
cells, 27 of them code, and 1,665 words of markdown. It calls public names of
`bellman` alone, as the verification of F17 asked; the listing below shows
the call that replaced each helper. Its markdown follows the econ-tribe
reading of F17: the field `a` is the wealth, the terms
of the factory are glossed or linked to
`docs/Bellman-Sym/08-bellman-factory.md`, and a stage prints a sheet.
It was executed again on 25 September 2026, on `main` in the repository's
main checkout above `825f17695`, after
unit C12 of the structure review (`73b4e71c9`) renamed `rebound` to
`changed_positions` in nine of its cells; the section "What changed at this
execution" lists them. The execution before it, on 23 September, ran in a
worktree of the repository, on
branch `codex/f17-benhabib` above `feca97b6b`. Nothing is solved.

## The command

Run from the repository root on 25 September 2026:

```text
BELLMAN_DDSL_ROOT="$PWD" PYTHONPATH=packages/bellman ./venv/bin/python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 applications/benhabib-2019/the-factory-on-benhabib.ipynb
```

The command exited with status 0 after 24 seconds. Two conditions of the
environment matter:

- The notebook's kernelspec names `bellman-ddsl`, the kernel of the project's
  virtual environment. Because the notebook stands in `applications/`, its first
  cell puts the folder of the C07 notebooks on the path and imports `checkout`
  from there. `checkout` puts the `packages/bellman` of the checkout that
  `BELLMAN_DDSL_ROOT` names first on the kernel's path; the kernel starts in
  the notebook's folder, where the relative `PYTHONPATH` names no folder.
  Otherwise the notebook imports only the standard library and twelve of the
  thirteen factory functions of `bellman`, all but `load_trellis`.
- Graphviz's `dot` is not on the PATH. The drawings are therefore laid out by
  the Node renderer beside those notebooks, whose package
  `tools/node_modules/@viz-js/viz`, version 3.25.0 (ignored by git), is
  installed in this checkout.

Every output was read cell by cell. The one cell that is meant to fail has the
tag `raises-exception`. It fails under `connector-names-no-field` and
names `a_pre`. No other cell fails.

## What changed at this execution

C12 edited the sources of nine cells: the import in cell 2, the sentence of
the markdown cell 15 that names the function, and the calls in cells 18, 19,
20, 22, 41, 43 and 45. Against the outputs of 23 September, four cells print
differently, in the table below. Cells 22 and 49 print the same text, which
the file now stores in two stream outputs in place of three and in one in
place of two, because the kernel sent the printed lines in fewer messages.
Every other output, the two drawings included, is identical.

| Cell | 23 September | 25 September |
|---|---|---|
| 12, `elaborate_trellis` | 0.87 seconds | 0.44 seconds |
| 37, `assemble_trellis` | 6.94 seconds | 5.00 seconds |
| 24, the bequest's sheet, GRAPHS, `builders` | `signature  wire  carrier` for each direction | `𝑉≻ ↦ (𝑉≺, 𝑑𝑉≺)` backward, `μ≺ ↦ μ` forward |
| 27, the sheet of age 25, GRAPHS, `builders` | `signature  wire  carrier` for each direction | `(𝑉≻, 𝑑𝑉≻) ↦ (𝑉≺, 𝑑𝑉≺), 𝑐≻` backward, `μ≺ ↦ μ≻` forward |

The two sheets changed through unit C5 of the structure review
(`849151a62`), which replaced the heading row of the card's signature table,
printed in that line since AMD-SG-034, with each builders graph's mapping.
The backward mapping of the within-life stage spells the policy `𝑐≻`, the
spelling of `c[>]`, which the policy block computes on the continuation grid
before `c = c[>]`; BLOCKS gives the policy's output as `c` at the decision
perch.

## The public calls

| Before | Now |
|---|---|
| `bound_and_copied(before, after)`, a function of cell 16 | `changed_positions(before, after)` and its length. The number copied is `occurrences` minus that length, where `occurrences`, counted in cell 16 from the trellis dictionary, is the number of positions, 37. |
| `plain(stage.provenance["source_lists"])` (cell 35) | The stage's own `provenance` attribute, each source printed as a `dict`. A list inside a source, the fill's `names`, prints as a tuple, since the provenance is frozen. |
| `load_calibration` of `declaration/calibration/main.yml` and of the sixth bracket's file, merged in cell 47 | The calibration of the record at `periods[1]`, which `load_recipe` merged from the same two files. |
| `same_graphs` and `same_stage`, functions of cell 49 | The stage's own attributes, printed for each position: `definitions`, the `graph` of each of its four handles (`initial_diagrams` and `builders`, `backward` and `forward`), `bindings`, and the sheet `str(stage)`. `==` is printed beside them. |

## The counts

| Call | Bound | Copied |
|---|---|---|
| `calibrate_trellis`, `methodize_trellis`, `configure_trellis` on the fresh elaboration | 37 each | 0 |
| each verb again, with the same mappings | 0 | 37 |
| `calibrate_trellis` with the fill β = 0.96, `n_a` = 500 | 37 (both stages declare β) | 0 |
| `configure_trellis` with that fill | 36 | 1 (the bequest, which has no settings list) |
| `calibrate_trellis` for the instances (q1, r1), (q5, r3), (q10, r5) | 0, 36, 36 | 37, 1, 1 (the bequest declares neither name) |
| `calibrate_trellis` after one entry of `bracket_6.yml` changed, on a temporary copy | 6 (`periods[1]` to `periods[6]`) | 31 |

- `load_recipe` gives 37 periods and 36 inter-period mappings, each
  `{'a': 'a_pre'}`. `periods[0]` holds `bequest`, and `periods[1]` to
  `periods[36]` hold `benhabib_bellman`.
- `elaborate_trellis` places 37 stage occurrences in 0.44 seconds.
- `assemble_trellis` takes 5.00 seconds, and its result equals the trellis
  built call by call at every position.
- The two periods accreted by hand, the bequest and age 60, have definitions,
  graphs, bindings and sheets equal to those of the same two periods of the
  assembled trellis. They are not equal by `==`, which also reads the
  provenance.

## What prints beyond the notebook's text

1. The bequest's sheet prints its value line as `A/β*a^(1 - μ)/(1 - μ)`. The
   sheet drops the parentheses of the file's `(A/β)`, and by the order of the
   operations the expression is the same.
2. The within-life stage's six settings are read at no place, because no
   methods entry of the legacy names a setting.
3. The drawings label the box of the within-life stage
   `benhabib_bellman (bellman)`. The first word is the key, the name of the
   file; the second is the stage's own name.

## What AAS should look at

1. **The terminal period** (section 4). The bequest's sheet shows the legacy's
   terminal block written in the stage's names, with `V[>]` added. Its methods
   and settings print `none bound` on a version marked specified, as the
   durables bequest's do.
2. **The trellis drawing** (section 5). The terminal period is labeled age 61,
   the paper's period T + 1. `inter_connectors[0]` joins `a → a_pre` from age
   60 to the bequest.
3. **The age brackets** (section 1 and `economics.md`, "The age brackets"). The
   range keys `"1-6"` to `"31-36"` are counted from the terminal period. They
   are the legacy's strings, applied to the brackets in the reverse order.
4. **The instances** (section 9 and `economics.md`, "The instances"). The
   calibration holds `q1` and `r1`, the legacy's tau 1 and r_type 1, because
   the legacy names no default. The sweep fills `q5` and `r3` (tau 5, r_type 3)
   and `q10` and `r5` (tau 10, r_type 5).
5. **The methods** (`economics.md`, "Numerical methods"). Three entries are copied
   from the legacy. The legacy's `!analytic-inverse` at `policy.InvEuler` is left
   out, because `configure` stops with an error at a method bound at a node.
6. **The calibration's source** (`economics.md`, "Calibration"). The values are
   those of the AER edition. The working paper, NBER Working Paper 21721 (2015), which the model folder's `reference/README.md` cites, reports others,
   in its Table 1 (the earnings) and its Table 2 (the estimates).
