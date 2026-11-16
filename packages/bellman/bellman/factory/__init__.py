"""The Bellman factory: files into records, records into stages, the binding
of a trellis, the joins and drawings of its periods, and the interactive view
of a stage or a trellis.

A trellis is the author's diagram of periods and their connections.
Positions identify occurrences and select recipe bindings; they are not
implicit inputs to the stage operators. Recipes retain their calibration
lists and method assignments by ranges of positions.

- `loading`: `load_stage`, a stage file into its source record, and
  `load_trellis`, a trellis file into the syntactic trellis, the model as
  written.
- `recipe`: `load_recipe`, a registry directory and its recipe into the
  syntactic trellis, each fill bound to its slot.
- `elaboration`: `elaborate_stage`, a source record into a stage, with the
  sources the record supplies bound.
- `trellis`: `elaborate_trellis`, the three trellis verbs, `accrete` and
  `changed_positions`, each a loop over the positions of a trellis, and
  `assemble_trellis`, which returns the trellis that `load_recipe`,
  `elaborate_trellis` and the three verbs make in order, copying each stage
  occurrence once.
- `joins`: the joins of a period from the fields of its stages and its
  connectors, and the orders the joins determine.
- `trellis_drawings`: the drawings of a period and of a trellis.
- `model_explorer`: the two builders graphs of a stage version, or of a
  trellis with a layer for each period and each stage occurrence, as the
  graph Google's Model Explorer draws, which `to_model_explorer` answers,
  with its two files and the viewer's server; the viewer is the extra
  `explore` of the package.

A source file is read by `bellman.stage.sources`, and a stage is bound by its
own verbs, `stage.calibrate(x)`, `stage.methodize(x)` and
`stage.configure(x)`, or by `elaborate_stage` from the sources its record
supplies.
"""
