"""The declarations of a stage and the type of every line: the declaration pass
and the typing walk of the construction, the algebra of the declared sets, and
the typed expressions with their notation.

- `line_unknowns`: a line's operators and unknowns, read from its retained
  term: the operator occurrences a right side holds and the kind of target
  each seeks, the names an expression reads that no operator binds, the fields
  a left side names, the candidate statements of a policy block and their
  systems, and the expressions of a bound.
- `declarations`: the declaration pass, which reads every top-level item and
  every block header in textual order, checks them, and holds the working
  records the construction of the builder boxes and the typing walk read; its
  ten steps, the nine checks and the annotation, stand in the order
  `make_stage` calls them.
- `context`: the typing walk, which gives each line its kind, its operators,
  its unknowns and the typed wires of its box, and refuses a line it cannot
  type.
- `sets`: the algebra of the declared sets, on the retained set terms.
- `category_codes`: the category map of a named set marked `!categories`,
  the codes of a declared domain, and whether values of one coded
  domain may be copied into another.
- `ranges`: the interval that encloses the values an arithmetic term takes on
  the declared sets.
- `typed_expressions`: the typed expressions of the construction and their
  notation, `format_expression`, which writes every formula a card prints,
  and the answer record of a wire's carrier.
- `primitive_definitions`: the definitions of the primitive operations,
  stated once, which the typed defining expressions, the carrier expressions
  and the stage encoding read.
- `type_table`: the objects of a stage with the type each declaration
  writes, the forms of a set expression and the limits of the language on a
  type, three tables from which the reference page of the types is printed.

The refusal of a stage file that cannot be constructed, with the rules it
names, stands at the root, in `bellman.refusals`.
"""
