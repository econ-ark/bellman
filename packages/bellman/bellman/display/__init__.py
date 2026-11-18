"""How an answer is set: as text, as a drawing or as JSON.

A printed form is written each time it is asked for, from the objects the
construction made, and is stored nowhere; the stage's queries say what a line
says, and this folder sets it.

- `sheets`: the setting of the stage sheet, a signature and a listing: an
  address and a stamp, a heavy rule, then a label column and a content
  column, in 78 columns; and `Sheet`, the text every printed view is. A card
  is set by `bellman.syntax.layout`.
- `drawing`: the drawing of one graph in Graphviz's DOT language, from the
  names the stage gives its wires, which the piece's `diagram()` supplies.
  `Drawing.svg()` lays the drawing out as SVG with the Graphviz libraries
  inside the Python package `pygraphviz`.
- `printed_records`: the records that print their own lines: the fields, the
  diagnostics and the methods, and the listings, signatures, obligations
  and tables of rows the pieces answer.
- `cards`: the records a denotation answers with, each printing itself, and
  the card of a piece or of a definition, set from them.
- `answer_encoding`: the answer records a stage encoding holds, written as
  JSON data, each node under a kind of the one schema,
  `stage-encoding-2.6.schema.json` beside it, which `encoding_checks` checks
  an encoding against. The stage composes the encoding in
  `bellman.stage.encoding`.
"""
