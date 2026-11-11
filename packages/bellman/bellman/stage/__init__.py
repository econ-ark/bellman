"""The elaborated stage: the object a construction returns, what it answers
about itself, how it is printed, and how it is bound. Its modules form four
groups.

The stage object:

- `elaborated`: the class `ElaboratedStage`, whose class body binds the
  queries and the binding verbs as its methods.
- `construction`: the construction, from a parsed AST to the fields of a
  stage, which `make_stage` of `elaborated` constructs the stage from.
- `pieces`: the pieces of a stage, each reached from the piece that
  contains it, a builder by the pair of perches it joins, and the verbs each
  piece answers; the tables of the parameters, the settings and the methods.

The queries, which answer what a stage and its pieces are asked:

- `stage_answers`: what the stage answers about itself.
- `grains`: the graphs of a stage and their grains.
- `builder_pairs`: the builders of a stage by the pair of perches each
  joins, which `stage.builder` reads.
- `boxes`: one box, read at the place it stands.
- `denotations`: what a stage and each of its pieces denote, the
  record each answers and its card, and the signature of a piece.
- `kernels`: the kernel a primitive operator applies, as text and
  compiled.
- `kernel_records`: the records of the kernels of the laws of motion and of
  the value aggregators.
- `carriers`: the carrier expressions of the wires, the sets their
  objects belong to.
- `defining_expressions`: the expressions the function and measure wires
  denote, the typed defining expressions of the functions and the primitive
  operations, and the names of the wires, measures and results a card, a
  kernel and a drawing print.
- `term_operations`: the named operations on terms those expressions are
  composed of, which read no stage.
- `semgraph`: the record of one stored or derived graph, with the sorts of
  its inputs and outputs, the conditions of the stage and the parameters its
  equations name, reached as the submodule `bellman.stage.semgraph`.

The printed forms, which the stage composes from its queries and
`bellman.display` sets:

- `inventory`: the stage sheet, what `str(stage)` prints; the definitions
  sheet, which `stage.definitions.list()` prints; and the directions of an
  initial diagram.
- `encoding`: the JSON document of a stage version, which `stage.encoding()`
  answers.

The binding:

- `binding_verbs`: the three binding verbs, `calibrate`, `methodize` and
  `configure`, with the conditions calibration decides and the checks of the
  options at the settings.
- `method_table`: the catalogue of the methods, `method_types`.
- `method_rows`: the rows of the catalogue of the methods that are no
  representation family, the record of a row and the domains of a keyword's
  value, which the registry of the representation families reads.
- `representations`: the registry of the representation families and the
  data a representation reads at its place.
- `representation_checks`: the checks of the data a representation reads,
  at binding and at configuration, and the conditions it owes.
- `grids`: the records of the grid constructors, their checks and the grids
  they construct.
- `explicit`: the explicit solution of a builder, `!explicit`, and the
  exclusions the construction checks.
- `places`: the places of a stage, the typing entries resolved to them and
  the components typed at each; the methods a place admits,
  `admitted_methods`.
- `levels`: the two levels of a stage, declared and operative, and the
  additions a methods source names.
- `components`: the checks of the components typed at the places against
  the rows of the catalogue, at binding and at configuration.
- `calibration_requirements`: the check of parameter values against their
  declared sets.
- `sources`: the readers of a calibration or a settings source, a mapping
  or a file, and `read_yaml_mapping`, the one reader of a YAML file, which
  reads every file the binding verbs and the factory are given, keeps every
  tag and refuses a key written twice.

The verbs a user calls, and the function that answers each (the class body of
`ElaboratedStage` in `elaborated` binds the stage's; the handles of `pieces`
call the rest):

| Verb | Asked of | Answered by |
|---|---|---|
| `view()`, `str(stage)` | the stage | `inventory.stage_sheet` |
| `list()` | the stage | `stage_answers.stage_listing` |
| `fields()`, `obligations()`, `diagnostics()` | the stage | the functions of the same names in `stage_answers` |
| `places()` | the stage | `places.places` |
| `denote()` | the stage | `denotations.denote` |
| `encoding()` | the stage | `encoding.encoding` |
| `calibrate(x)`, `methodize(x)`, `configure(x)` | the stage | `binding_verbs` |
| `list()` | a graph; a bubble | `boxes.graph_listing`; `boxes.bubble_listing` |
| `denote()` | a graph; a bubble; a box | `denotations.denotation_of_graph`; `denotation_of_block` or `denotation_of_builder`; `denotation_of` |
| `signature()` | a graph; a bubble or a box | `denotations.graph_signature`; `denotations.box_signature` |
| `obligations()` | a graph; a bubble or a box | `stage_answers.obligations`; `boxes.box_obligations` |
| `methods` | a graph, a bubble or a box | `boxes.methods_within` |
| `diagram()` | a graph or a bubble | `display.drawing`, through `pieces` |
| `kernel()`, `compile_kernel()` | a box | `kernels.kernel`, `kernels.compile_kernel` |
| `kernels()` | a bubble that is a builder or a sub-builder | `pieces.builder_kernels` |

The stage's tables `par` and `settings` read `stage_answers.parameters_of`
and `settings_of`, and print `parameter_rows` and `setting_rows`; the
components at a place are read from `methods` at every level by the place as
written through `pieces.components_bound_at`; and a builder is read by the pair of perches
it joins, `stage.builder["cntn", "dcsn"]`, through
`builder_pairs.builder_pairs`, a perch path such as `stage.dcsn.builder.bwd`
reading one key of that mapping.

The base class of a stage version, `StageVersion`, with `WorkingStage` beside
it, and the provenance of a version stand beneath the fold, in
`bellman.native`, since the fold and the construction of the graphs read them.
"""

from importlib import import_module

# Each public name of a stage and the module that defines it, in the order a
# modeler meets them (packages/bellman/README.md §1). The functions of the
# view in Model Explorer that take a stage or a trellis, or read a view of
# either, and six of the view's constants, `BOUNDARY_IDS`,
# `LAYER_ID_ENDING` and the colors the legend of Bellman Workbench reads,
# `LAYER_COLORS`, `NODE_STYLE`, `OUTPUT_STYLE` and `PERCH_COLORS`, stand in
# `bellman.trellis` too, naming the same module there: one object in two
# tables; `box_attributes` and `INITIAL_IDS` stand in this table alone.
_EXPORTS = {
    "load_stage": "bellman.factory.loading",
    "elaborate_stage": "bellman.factory.elaboration",
    "elaborate_text": "bellman.factory.elaboration",
    "make_stage": "bellman.stage.elaborated",
    "source_spans": "bellman.factory.elaboration",
    "bind_stage": "bellman.factory.elaboration",
    "ElaboratedStage": "bellman.stage.elaborated",
    "arvl": "bellman.syntax.vocabulary",
    "dcsn": "bellman.syntax.vocabulary",
    "cntn": "bellman.syntax.vocabulary",
    "method_types": "bellman.stage.method_table",
    # The tags of the catalogue a place admits, which the Methods tab of
    # Bellman Workbench offers there (model interface specification 0.4, unit
    # L, Task 18).
    "admitted_methods": "bellman.stage.places",
    # The typing entries of a `.bl` text located and written as text, which
    # the Methods tab of Bellman Workbench reads and writes back
    # (specification 0.7 §6, the writer of the `.bl` declaration).
    "typing_entries": "bellman.syntax.typing_entries",
    "write_typing_entry": "bellman.syntax.typing_entries",
    "graph_refusal": "bellman.stage.grains",
    "header_line": "bellman.display.cards",
    "source_lines": "bellman.display.cards",
    # The sections of a card, which Details of Bellman Workbench prints a
    # builder's `Declared`, `Conditions` and `Method` from (specification 0.6
    # §9; decision SE-17).
    "card_sections": "bellman.display.cards",
    "to_model_explorer": "bellman.factory.model_explorer",
    "perch_overlays": "bellman.factory.model_explorer",
    "box_attributes": "bellman.factory.model_explorer",
    "layers_to_open": "bellman.factory.model_explorer",
    "node_place": "bellman.factory.model_explorer",
    "wire_counts": "bellman.factory.model_explorer",
    "BOUNDARY_IDS": "bellman.factory.model_explorer",
    "INITIAL_IDS": "bellman.factory.model_explorer",
    "LAYER_ID_ENDING": "bellman.factory.model_explorer",
    "LAYER_COLORS": "bellman.factory.model_explorer",
    "NODE_STYLE": "bellman.factory.model_explorer",
    "OUTPUT_STYLE": "bellman.factory.model_explorer",
    "PERCH_COLORS": "bellman.factory.model_explorer",
    "explore": "bellman.factory.model_explorer",
    "write_model_explorer": "bellman.factory.model_explorer",
    # The names the classification table of Bellman Workbench reads (model
    # interface specification 0.3, unit T), so that its backend imports from
    # this namespace alone (§6): the sides a block's header declares, the
    # fields of each branch, the printer of a declared set, and the words of
    # the roles and of the primitive sets.
    "header_of": "bellman.fold.block_lines",
    "branches": "bellman.stage.stage_answers",
    "to_source": "bellman.syntax.source",
    "ROLE_WORD": "bellman.syntax.vocabulary",
    "PRIMITIVE_SETS": "bellman.syntax.vocabulary",
    # The name the reference view of Bellman Workbench reads (model interface
    # specification 0.3, unit B, §3.2): the mark a printed name carries after
    # its letters for each perch, by which a kernel's `a≻` is the field `a`.
    "PERCH_MARK": "bellman.syntax.vocabulary",
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    """The public name `name`, read from the module that defines it, which is
    imported on this first use; every other name is refused with an
    AttributeError, so that a submodule is still imported as one."""
    try:
        module_name = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    return getattr(import_module(module_name), name)


def __dir__():
    return sorted(set(globals()) | set(__all__))
