"""What an identity, a condition, a sort, a box and a stored record are, and
the stage version that holds them: the objects every later folder reads.

- `identity`: the identity of a wire, a box, a definition and a condition.
- `predicates`: the conditions under which a retained equation is read.
- `frozen`: the read-only copy of an annotation value.
- `hypergraphs`: the DisCoPy classes of a stage, their immutable subclasses,
  and the copy of a stage version's objects.
- `labels`: the label a box shows, a function's name in italic, and the
  listing of a graph.
- `records`: the records of a stage version and of its construction, and the
  sort of a wire.
- `versions`: the base class `StageVersion` of a stage version, its three
  stored records and the answers kept for it, and beside it
  `WorkingStage`, the stage while it is constructed, the two objects a
  reader reads a stage from.
- `provenance`: the description and digest of each source of a stage
  version, the provenance a binding verb records with the one before it as
  its parent, and the versions of the package and of its grammar files.

`versions` and `provenance` stand here, beneath the fold, because the fold and
the construction of the graphs read them.
"""
