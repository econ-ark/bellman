# bellman

The package `bellman` reads a stage file written in Bellman-SYM, the language
of this repository (`.bl` files). A [stage](../../docs/Bellman-Sym/01-stage.md)
is one step of a dynamic program, with three perches, the information sets at
arrival, at the decision and at continuation. From the file the package
constructs the stage's **semgraph**, its semantic graph: the typed fields,
equations and operators of the stage, held in four graphs of the DisCoPy
library. The package binds numerical methods, parameter values and numerical
settings to a stage. It joins stages into periods by their fields and
constructs trellises, the author's diagrams of periods and their connections.
It also prints what a stage holds. This file maps the package for a
reader of its code. Its words are those of the documentation, whose concept
wiki, [`docs/wiki/`](../../docs/wiki/index.md), defines them, and the objects
a user meets are stated in
[the API](../../docs/Bellman-Sym/API/index.md) and
[The Bellman factory](../../docs/Bellman-Sym/08-bellman-factory.md).

A field name belongs to its stage occurrence. Two stages may each declare `a`
without sharing a field, while two stages in one period that declare the same
parameter name share one parameter and its value. An authored connector
`{a: k}` selects a continuation state field and an arrival state field when
each name has one eligible use; `{disc.a: port.k}` qualifies an endpoint by
stage key when a name has several. Authored pairs take precedence over
automatic matching. An unclaimed equal-name pair is inferred only when its
declared sets are compatible and it is the unique globally consistent choice.
The public `bellman.trellis.connection_report` records selected pairs,
rejected automatic candidates, diagnostics, unjoined fields and complete state
routes without constructing another stage. Ordinary construction retains
representable connection problems on an inspectable model; the report gives
their reasons and authored source origins. Computation along an uncertified
route and ordering cyclic dependencies remain refused. See [Periods](../../docs/Bellman-Sym/06-period.md)
for the source notation and [stage composition](../../docs/bellman-calculus/07-stage-composition.md)
for the mathematical interpretation.

## 1 What a user imports

A public name is imported from the namespace of the object it concerns:
`bellman.stage` for a stage, `bellman.period` for a period and
`bellman.trellis` for a trellis and the factory route that assembles one.
Each namespace is a package whose `__init__.py` holds one table from each
public name to the module that defines it and derives `__all__` from that
table; the module is imported when the name is first used, so that importing
the parser imports no DisCoPy. The root package `bellman` exports nothing.
The four refusal classes, `ConstructionError`, `NotConstructed`,
`TargetError` and `FactoryError`, are imported from `bellman.refusals`, and
the module `bellman.stage.semgraph` as a submodule, `from bellman.stage
import semgraph`.

`from bellman.stage import …`

| What the names do | Names |
|---|---|
| read a stage file into its record, and construct the stage | `load_stage`; `elaborate_stage`, `elaborate_text`, `make_stage` |
| answer the spans of a text, and bind a stage with a report of what bound | `source_spans`; `bind_stage` |
| name the class of a stage and the method table, and answer the methods of that table a target admits under their placement rules | `ElaboratedStage`; `method_types`; `admitted_methods` |
| name the perches in a key of `stage.builder`, `stage.builder[cntn, dcsn]` | `arvl`, `dcsn`, `cntn` |
| answer the refusal held in the place of a graph, the line of a block's header and the lines a card quotes | `graph_refusal`; `header_line`, `source_lines` |
| view a stage in Model Explorer, and read the view back | `explore`, `write_model_explorer`; `to_model_explorer`, `perch_overlays`, `box_attributes`, `layers_to_open`, `node_place`, `wire_counts`; `BOUNDARY_IDS`, `INITIAL_IDS`, `LAYER_ID_ENDING`, `LAYER_COLORS`, `NODE_STYLE`, `OUTPUT_STYLE`, `PERCH_COLORS` |
| answer the sides a block's header declares, the field each listing of a header names in a text, the fields of each branch and the `.bl` text of a term, such as a set, and name the word of each role, the primitive set of each spelling and the mark a printed name carries for each perch | `header_of`, `header_fields`, `branches`, `to_source`; `ROLE_WORD`, `PRIMITIVE_SETS`, `PERCH_MARK` |

`from bellman.period import …`

| What the names do | Names |
|---|---|
| read the joins of a period and the orders they determine | `period_joins`, `computable_together`, `forward_order`, `backward_order` |
| draw one period of a trellis | `diagram_period` |
| answer the forward record of a period, what each of its forward builders needs and gives as plain data, with or without the inter-period mapping that joins it to the period that follows or to itself | `forward_record`; `ForwardRecord`, `ForwardStep`, `ForwardShock`, `ForwardControl` |

`from bellman.trellis import …`

| What the names do | Names |
|---|---|
| read a trellis file, or a registry and its recipe | `load_trellis`, `load_recipe` |
| construct and bind the stages of a trellis | `elaborate_trellis`, `accrete`, `changed_positions`; `calibrate_trellis`, `methodize_trellis`, `configure_trellis`, `specify_trellis`, `respecify_trellis`, `assemble_trellis` |
| read the joins between two periods, the state fields no join reaches, the marginal values a route requires that no stage exports, the one selection of a trellis's connections and its report, and transport a point, a vector, a Hessian, the atoms of a measure or a function along a certified route | `inter_period_joins`, `unjoined_fields`, `marginal_missing`, `trellis_selection`, `connection_report`, `transport_point`, `transport_vector`, `transport_hessian`, `transport_atoms`, `pull_back`; `Selection`, `ConnectionReport` |
| draw a trellis, view it in Model Explorer and read the view back | `diagram_trellis`; `explore`, `write_model_explorer`, `to_model_explorer`, `perch_overlays`, `layers_to_open`, `node_place`, `wire_counts`, `unpaired_joins`; `UnpairedJoin`, `UnpairedWire`; `BOUNDARY_IDS`, `LAYER_ID_ENDING`, `LAYER_COLORS`, `NODE_STYLE`, `OUTPUT_STYLE`, `PERCH_COLORS` |
| find, read, replace, append, insert, split and remove one entry of a model's YAML files, and name the entry that writes a period or a connector line | `entry_span`, `entry_value`, `replace_entry`, `append_to_mapping`, `append_to_sequence`, `insert_in_sequence`, `split_entry`, `remove_from_sequence`, `remove_from_mapping`, `written_at`, `written_spans`, `period_entries`, `connector_entry`; `EntrySpan`, `ConnectorEntry` |

The functions of the view that take a stage or a trellis, or read a view of
either, and six of the view's constants, `BOUNDARY_IDS`, `LAYER_ID_ENDING`
and its colors `LAYER_COLORS`, `NODE_STYLE`, `OUTPUT_STYLE` and
`PERCH_COLORS`, stand in both `bellman.stage` and
`bellman.trellis`, each naming the same module: one object in two tables
(D2 of the import-rules brief). `box_attributes` and `INITIAL_IDS` stand in
`bellman.stage` alone.

Everything else a user asks, the stage answers through its own methods, such
as `stage.view()`, `stage.fields()` and `stage.calibrate(x)`, and through its
**pieces**, the parts of a stage reached from it, such as the backward
builder `stage.builder["cntn", "dcsn"]`, read by the pair of perches it joins;
`stage.dcsn.builder.bwd` reads the same builder from the decision perch. The
command `python -m bellman <file.bl>` (`__main__.py`) prints a stage's sheet,
and with `--encoding`, `--dossier` or `--refusals` its encoding, its dossier or
the catalogue of refusals. `bellman/refusals.py` holds the four refusal
classes, the rules a refusal names and the names of the conditions a stage
states.

## 2 From a stage file to a stage

The composition a reader follows first is `elaborate_stage(load_stage(path))`,
followed by the three binding verbs:

1. `load_stage` (`factory/loading.py`) reads the file into its **source
   record**: the text and its origin, empty mappings for the calibration, the
   settings and the methods, and the digest of the text.
2. `elaborate_stage` (`factory/elaboration.py`) parses the text into the
   **parsed AST**, the abstract syntax tree whose classes `syntax/terms.py`
   defines, with a table of source positions (`parse_with_spans` of
   `syntax/lower.py`, over the parser of `syntax/parse.py`), and calls
   `make_stage` on the two.
3. `make_stage` (`stage/construction.py`) constructs the stage in order: the
   declaration pass of `typing/declarations.py` and the typing walk of
   `typing/context.py`; the fold of `fold/stage_fold.py`; the four graphs,
   built by `construct_graphs` of `graphs/builders_graphs.py` from the wire
   table of `graphs/wire_sorts.py`, the two initial diagrams by
   `graphs/initial_diagrams.py`; and the `ElaboratedStage` of
   `stage/elaborated.py`, the symbolic stage version.
4. `stage.calibrate(x)`, `stage.methodize(x)` and `stage.configure(x)`,
   defined in `stage/binding_verbs.py`, each return a new **stage version**, the
   stage after one more binding of parameter values, numerical methods or
   numerical settings; a source given by its path is read by
   `stage/sources.py`.

A **block** is an authored group of typed lines of the stage file, and the
**builder** it denotes is the operator its lines state, on value functions
backward or on probability measures forward. The **fold** is the reading of a
block's lines into its builder's operator rows: `fold/stage_fold.py` writes
each builder as the primitive operators it composes, one row each, of a kind
that `typing/primitive_definitions.py` defines: `Pullback`, `Expectation`,
`Aggregation`, `Argmax` and `Evaluation` in the builders of
`stage.builder.bwd`, and `DistributionExtension` and `Pushforward` in those of
`stage.builder.fwd`;
the eighth kind the table defines, `PolicyInsertion`, is formed by no stage
file under `applications/`
([Operations](../../docs/Bellman-Sym/reference/operations.md)). The rows stand
in the **construction table**, which also holds the stage's definitions and
its **obligations**, the conditions the construction assumes and does not
verify. A line is read in three places: during construction
`typing/line_unknowns.py` finds its operators and its unknowns and the fold
reads its terms into rows, and after construction `fold/stage_names.py` reads
a stored block's lines again, with the names of the stage, for the pieces and
the method targets.

The Bellman factory, in `factory/`, makes the same calls for every stage of a
trellis. It reads files into a **syntactic trellis**, the model as written: a
dictionary of periods whose stages are source records. `elaborate_trellis`
returns the **elaborated trellis**, the same dictionary with a stage version
at every key, and the three trellis verbs bind it. A **stage occurrence** is a
stage file elaborated at one position of a trellis.

The position records an
address, not an economic input. A recipe may select different calibrations
or methods by ranges of positions. Reusing the same declarations and
bindings gives the same stage operator at each occurrence.

## 3 The folders

The eleven folders, in the order in which they depend on one another (§6); the
oracle of §6 reads this order from the first column of this table:

| Folder | Modules | Open it to learn |
|---|---|---|
| `syntax` | `grammars/`, `parse`, `lower`, `union`, `terms`, `decode`, `source`, `vocabulary`, `layout`, `walk` | why a text is refused as ill-formed; how a stage file and its additions are unioned on their terms; the words of the language; how text is set in 78 columns; how a term is walked |
| `native` | `identity`, `predicates`, `frozen`, `hypergraphs`, `labels`, `records`, `versions`, `provenance` | what an identity, a condition, a sort, a box and a stored record are; the stage version that holds them |
| `distributions` | `families`, `edges`, `conditionals` | what the arguments of a shock family mean; on which edge a shock is drawn; the conditional distribution an expectation selects |
| `typing` | `sets`, `category_codes`, `ranges`, `typed_expressions`, `line_unknowns`, `declarations`, `context`, `primitive_definitions`, `type_table` | why a declaration is refused; a line's operators, unknowns and type; the algebra of the declared sets; the category codes of a named set; how a formula is written; which objects a stage has, which forms a set is written in and which limits the language sets on a type |
| `fold` | `block_lines`, `wire_terms`, `declared_sets`, `stage_names`, `table`, `value_bundles`, `backward`, `policy`, `derived_parameters`, `stage_fold`, `conditions` | how a stage's blocks and lines are read; how a block's lines become its builder's operator rows; the conditions the construction assumes; what a derived parameter reads and its value at a calibration |
| `graphs` | `wire_sorts`, `initial_diagrams`, `builders_graphs` | how the four graphs and their grains are built |
| `display` | `sheets`, `printed_records`, `cards`, `drawing`, `graphviz_layout` with its Node script `graphviz_layout.mjs`, `answer_encoding`, `encoding_checks`, the schema file | how an answer is set as text, a drawing or JSON; how a drawing is laid out |
| `stage` | four groups (§4) | how a stage is built, what it answers, how it is printed and how it is bound |
| `factory` | `loading`, `recipe`, `file_entries`, `elaboration`, `trellis`, `joins`, `trellis_drawings`, `model_explorer` | how files become records, stages and trellises; the joins of a period; the drawings of a period and of a trellis; the interactive view of a stage or a trellis in Google's Model Explorer; the entries of a model's YAML files read and replaced as text |
| `period` | `__init__` alone: the table of the public names of a period (§1) | what a user imports for a period |
| `trellis` | `__init__` alone: the table of the public names of a trellis and of the factory route (§1) | what a user imports for a trellis |
| the root | `__init__`, `__main__`, `refusals`, `refusal_catalogue`, `refusal_examples`, `semantic_rules`, `dossier` | that the root exports nothing (§1); what a refusal carries; the catalogue of refusals; which functions implement and check each rule of the language; the dossier of a stage |

The four graphs of a stage are its two **initial diagrams**, one backward and
one forward, whose boxes are the blocks and whose wires are the fields the
blocks read and write, and its two **builders graphs**, whose boxes are the
builders and whose wires carry value functions backward and probability
measures forward. A **grain** chooses which boxes of a graph are opened: the
builders, their sub-builders or their primitive operators, among others.
Each folder's `__init__.py` maps its modules one by one.

## 4 The four groups of `stage`

`stage` holds four kinds of module, which `stage/__init__.py` lists group by
group:

- **the stage object**: `elaborated`, the class `ElaboratedStage`, whose body
  binds the queries and the binding verbs as its methods; `construction`, the
  construction; and `pieces`, the pieces and the verbs each answers;
- **the queries**, which answer what a stage and its pieces are asked:
  `stage_answers`, `grains`, `boxes`, `denotations`,
  `kernels`, `kernel_records`, `carriers`, `defining_expressions`,
  `term_operations`, and `semgraph`, the record of one stored or derived
  graph, reached as the submodule `bellman.stage.semgraph`;
- **the printed forms**, which the stage composes from its queries and
  `display` sets: `inventory`, the stage sheet, the definitions sheet and the
  directions of an initial diagram; and `encoding`, the JSON document of a
  stage version;
- **the binding**: `binding_verbs`, the three binding verbs; `method_table`,
  the catalogue of the methods, and `method_rows`, its rows of the methods
  that are no representation family; `representations`, the registry of the
  representation families and the data each representation reads, and
  `representation_checks`, the checks of those data; `grids`, the grid
  constructors and the grids they construct; `explicit`, the explicit
  solution of a builder; `places`, the places of a stage and the components
  typed at them; `components`, the checks of the components against the
  catalogue; `levels`, the two levels of a stage and the additions a methods
  source names; `calibration_requirements`, the check of parameter values
  against their declared sets; and `sources`, the readers of a calibration
  or a settings source and the one reader of a YAML file.

The interactive view of a stage in Google's Model Explorer reads these
queries and the drawing's labels, but it stands in `factory`, as
`factory/model_explorer.py`, since the view of a trellis also reads the
joins of its periods, which `factory/joins.py` answers, and the order of §6
forbids a module of `stage` to import from `factory`.

The base class of a stage version, `StageVersion`, with `WorkingStage`, the stage
while it is constructed, beside it, and the provenance of a version stand in
`native`, beneath the fold, because the fold and the construction of the
graphs read them.

## 5 The printed forms

Each printed form is written in two steps: one module writes its words, and
another sets them in lines and columns. A form is written each time it is
asked for and is stored nowhere.

| Printed form | Asked by | Words written in | Set in |
|---|---|---|---|
| the stage's **sheet**, its inventory | `stage.view()`, `print(stage)` | `stage/inventory.py` (`stage_sheet`), from the stage's queries | `display/sheets.py` |
| a **short form** | `repr(stage)`, `repr(piece)` | `stage/inventory.py` (`version_word`); `stage/pieces.py` | the same modules |
| a **card**, a piece's denotation | `print(piece.denote())`, `stage.definitions.denote(identity)` | the record, `display/cards.py`; its formulas, `typing/typed_expressions.py` (`format_expression`); the names of its wires, `stage/defining_expressions.py` (`wire_name`); its labels, `native/labels.py`; its block words, `display/cards.py` | `display/cards.py`, with `syntax/layout.py` |
| a listing, a signature, obligations, a table of rows | `piece.list()`, `piece.signature()`, `obligations()`, `stage.par`, `stage.settings`, `stage.places()` | `display/printed_records.py`, from the stage's queries; the types in a signature, `stage/carriers.py` and `typing/typed_expressions.py` | `display/printed_records.py`, with `display/sheets.py` and `syntax/layout.py` |
| the fields, the diagnostics, the methods | `stage.fields()`, `stage.diagnostics()`, `stage.methods` | `display/printed_records.py`, from `fold/block_lines.py` and `stage/stage_answers.py` | `display/printed_records.py` |
| a **kernel**, with the source text of its function where it has one | `operator.kernel()` | `stage/kernels.py` | `stage/kernels.py` |
| a builder's record of its kernels | `builder.kernels()` | `stage/pieces.py` (`builder_kernels`), in the records `BuilderKernels` and `PieceKernel` | `display/printed_records.py` |
| a drawing | `graph.diagram()`, `diagram_period`, `diagram_trellis` | the names of the wires and the laws, `stage/defining_expressions.py`; the symbols of the boxes and the DOT text, `display/drawing.py`; `factory/trellis_drawings.py` | Graphviz, run by `display/graphviz_layout.py` |
| the **stage encoding** | `stage.encoding()`, `python -m bellman --encoding` | `stage/encoding.py`, with `display/answer_encoding.py` for the answer records, each node under a kind of the one table there | JSON, which the one schema file of `display/` describes |
| the **interactive view** | `explore(stage)` and `write_model_explorer(stage, folder)` of `bellman`, and `serve(graph_path)` of `bellman.factory.model_explorer` | `factory/model_explorer.py`, from the stage's queries, the symbols and labels of `display/drawing.py` and the sections of a card, `display/cards.py` | two JSON files, which Google's Model Explorer, the extra `explore` of the package, draws in the browser |
| the dossier | `python -m bellman --dossier` | `bellman/dossier.py`, from the public queries | `bellman/dossier.py` |
| a refusal | `str(error)` | the module that refuses, in the refusal's message and advice | `bellman/refusals.py` |
| the catalogue of refusals | `python -m bellman --refusals` | `bellman/refusal_catalogue.py`, from the examples of `bellman/refusal_examples.py` | `bellman/refusal_catalogue.py` |

A **sheet** is the printed view of the stage, `str(stage)`: an address and a
stamp, a heavy line, then its sections under headings in capitals, no line
wider than 78 characters. A **short form** is the one line `repr` prints,
such as `ElaboratedStage('cons', symbolic)`. A **card** is the printed form
of a piece's denotation, the mathematical object the piece denotes: a title,
a heavy line, then its sections, such as `Signature`, `Operations` and
`Source`, each heading at the margin with its content two columns in, and no
line wider than 78 characters. A **kernel** is the mathematical data an
operator applies, such as the law of motion a pullback reads, and `kernel()`
answers it as a record whose text is the kernel's line. Where the kernel is an
explicit function, a law of motion or a value aggregator, the record also
holds the source text of one plain Python function that computes it, and
`compile_kernel()` answers that function, the **compiled kernel**, which
refers to no stage. An operator with no explicit function refuses
`compile_kernel()` under `kernel-target`: the identification of a policy
block, which holds the relation its output satisfies in place of a function,
an expectation, whose kernel is a shock distribution, and an Evaluation, whose
kernel is the identity, among them. A builder's `kernels()` answers one record
of its operations in the order they apply, each with its printed kernel, its
wires and, where it has one, its compiled kernel or its relation, from which a
numerical operator is built without the stage. The **stage encoding** is the
JSON-compatible record of a stage version, for a second tool to read. The
**interactive view** is the two builders graphs of a stage version, or of
every stage occurrence of a trellis, written for Google's Model Explorer:
each builder a layer that opens to its sub-builders and its primitive
operators, each operator showing its kernel and the rows of its card, and
the labels of its operators and ports those that the drawing prints
([The view in Model Explorer](../../docs/Bellman-Sym/API/stage/10-model-explorer.md)).

A drawing is laid out by Graphviz, which the package does not install: either
Graphviz's `dot` is on the PATH, or Node.js runs the WebAssembly build of
Graphviz that `npm install` in this folder installs from its `package.json`
into the gitignored `node_modules/`; with neither, `svg()`
refuses and names both, and a notebook cell shows the drawing's short form.

## 6 The order of the folders

The eleven folders stand in the order `syntax`, `native`, `distributions`,
`typing`, `fold`, `graphs`, `display`, `stage`, `factory`, `period`,
`trellis`, each one layer of that order. A module imports at its head from its
own folder, from the folders before it, and from `bellman/refusals.py`, which
holds the refusal classes and the names of the rules and conditions and
imports nothing of the package: the one exception. The root's other modules,
`__init__`, `__main__`, `dossier`, `refusal_catalogue`, `refusal_examples`
and `semantic_rules`, stand above every folder. No module imports inside a function, and none reads
another's private name. `tests/import_rules.py` checks the rule: it
counts the imports inside functions and classes, prints the cycles among the
modules, and prints each import that reads a later folder or the root, reading
the order of the folders from the table of §3, and prints each table entry
that names no module or no defined name; with `--strict` any of the four fails
it. Run this source check explicitly with `--strict`; it is separate from
tests of public behavior. No module
reads another module's private name.

The tables of `bellman.stage`, `bellman.period` and `bellman.trellis` (§1)
name modules of `factory/` by their dotted names, which no import statement
reads; for `bellman.stage`, `factory/` is a later folder, so the tables are
the package's facade, the one place a folder names a module above it (D1 of
the import-rules brief, AAS). The tool checks them as its fourth measure:
every entry names a module of the package that defines the name, and a name in
two tables names one module, so that a moved function cannot leave a dead
entry.

## 7 The target

The structure review of 24 September 2026 set the order of §6 and the
modules of each folder; the unit of names by meaning gave the modules of
`stage` and `display` the names above.

## 8 Generated files and tests

Two files are generated from the ASDL listings of `syntax/grammars/`, the
descriptions of the language's terms in the abstract syntax description
language, and a change is made in the listing and the file generated again: `syntax/terms.py`
from `dynspec_full.asdl` by `gen_types.py` beside this file, and the marked
region of `typing/typed_expressions.py` that holds its generated constructors from
`semantic.asdl` by `gen_semantic_types.py`. The tests are under `tests/`.

The folder `tests/snapshot/` stores four kinds of file:

- the parsed term of each stage file under `applications/`, at
  `corpus/<application>/<file>.bl.ast.json`;
- the printed text of the stage of each stage file that elaborates, at
  `corpus/<application>/<file>.bl.printed.txt`, and the printed text of the
  one fixture stage, under `corpus/fixtures/`;
- for each of the eight corpus stages, which `CORPUS` of `tests/conftest.py`
  lists, the text of its graphs, at
  `corpus/<application>/<file>.bl.graphs.txt`: the listing and the wiring
  of each graph at each grain, with the conditions and the sort of every
  wire;
- the table `encoding_digests.json`, which holds the SHA-256 digest of the
  schema of encodings and, for each stage file that elaborates, the digest
  of its encoding and of each section of that encoding.

`tests/test_applications.py` compares each stored file with the live value: the
parsed term, the printed text, the text of the graphs and the digests of the
live encoding. It also checks that
each stage file that the tables of `tests/snapshot/corpus_cases.py` hold as
refused is refused under its recorded rule. `tests/test_graphs_and_grains.py`
checks properties of the graphs of every stage file that elaborates, and
`tests/test_cards_and_sheets.py` checks that each piece of such a stage prints
one card whichever handle reaches it. Acceptance files check the current changes;
`tests/test_refusals.py` checks diagnostics, and the other test files, each
named for its subject, check public operations that a fixed recording cannot
establish.

Run the package's tests from the repository root. The command
`python -m pytest packages/bellman/tests` runs the default set: it skips
each case marked `complete_set`. The command
`python -m pytest packages/bellman/tests --complete` runs every case. In the
default set, each test of `test_applications.py`, `test_cards_and_sheets.py`,
`test_graphs_and_grains.py`, `test_field_equations.py` and `test_encoding.py`
that runs over the stage files runs on one file of
its list, in most of these tests the stage file of the consumption stage.
The complete set runs each such test on every file of its list. The optional test dependency `pytest-xdist` permits
parallel execution with `-n 4`.

Tests never write the stored files. After a change has been read, these
commands, run from `packages/bellman`, write each kind again:

- `python tests/snapshot/record.py --corpus` writes the parsed terms, the
  printed texts and the texts of the graphs under `tests/snapshot/corpus/`;
- `python tests/snapshot/validate_encodings.py` validates the live encoding
  of each stage file that elaborates against the schema, and only then
  writes `tests/snapshot/encoding_digests.json`.

Each of the two scripts, `record.py` and `validate_encodings.py`, reads the
package `bellman` of the checkout that holds it, whatever copy the
environment has installed. No encoding is stored. The command `python tests/snapshot/record.py --encodings FOLDER`
writes the encoding of each stage file that elaborates in FOLDER, which must
lie outside the repository, so that the encodings of two commits can be
compared. At a commit whose tests pass, the SHA-256 digest of each file it
writes equals the digest under `encoding` in the table.
`tests/test_encoding.py` checks that the schema refuses malformed encodings.

`applications/stage_ast.py` holds the helpers that the structural tests of the
applications import.
