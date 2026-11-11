"""The fold: the reading of a block's lines into the operator rows of the
builder the block denotes, and the conditions the construction assumes.

- `block_lines`: the blocks of a stage in file order and the direction of
  each, what each block's header declares (`DeclaredSides`), the sort of every
  wire, the fields, the declared sets of the parameters and the symbol groups,
  the forward chain between two perches and the lines marked `!doc`: what is
  read of a stage's blocks before a name is resolved.
- `wire_terms`: the symbol of a wire in a reduced term, the wires a term
  reads, the left side of a statement, a block's line as the fold reads it
  (`BlockLine`), and the walks over a term.
- `declared_sets`: the set a term takes its values in, read from the declared
  sets, and the definedness of a node.
- `stage_names`: `StageNames`, the names of one stage with their roles, sets,
  wires and identities, read from the working stage during construction and
  from the constructed stage afterwards; and the lines of a block, with their
  roles, ordinals and operator occurrences, and its branches, read with those
  names.
- `table`: the construction table, its rows, and the rows of one block at
  the primitive and the sub-builder grain (`BlockRows`).
- `value_bundles`: the primitive grain and the merges of parallel boxes on one
  value bundle.
- `backward`: the fold of one backward block, slice by slice, and the
  construction rules of AMD-SG-008 §3.
- `policy`: the fold of the policy block, and the systems of candidate
  statements (`CandidateSystem`).
- `derived_parameters`: the derived parameters of a stage, constants its
  definitions write from its parameters: the order in which they are
  evaluated, the check of what each reads, and their values at a calibration.
- `stage_fold`: the entry points `fold_stage_file` and `fold_stage`, the
  driver, the definitions table and the rows of a forward block.
- `conditions`: the conditions of a stage, the conditional distribution an
  expectation selects, the edge that draws a set of shocks, and the checks the
  calibration's numbers decide.
"""
