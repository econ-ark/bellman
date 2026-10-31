"""The construction of a semgraph's four graphs: the two initial diagrams, the
blocks on the fields they read and write, and the two builders graphs,
backward on value functions and forward on probability measures. The
identities, conditions, boxes and records the graphs are made of are in
`bellman.native`.

- `wire_sorts`: the wire table of a stage, `WireTable`: the sort of every
  wire, the blocks with the direction of each, and the rows and the inputs
  and outputs of each builder; `WiredRow` and `WiredBox`, a row or a box with
  the identities of the wires it reads and writes; `connect`, the wiring of a
  graph by the identities of its wires, which `wired_boxes` reads back; and
  `needed`, the boxes on a path to an output.
- `initial_diagrams`: every step of the two initial diagrams: the blocks'
  statement graphs at construction, the undirected graph of the whole stage
  and the cut of the two diagrams from it, and the finer grains of a stored
  diagram.
- `builders_graphs`: the four stored graphs, built at construction from the
  construction table; the builders graphs at every grain; one piece of
  either kind of graph at a grain; and the value bundles of a graph.
"""
