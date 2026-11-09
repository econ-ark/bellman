"""One stage's elaborated object: its definitions, its four graphs and its
bindings.

A stage is the unit a modeler writes in Bellman-SYM: one modular Bellman
operator with its three information sets — arrival, decision, continuation —
and the laws of motion, the value recursion, and the policy between them.
`ElaboratedStage` is the object built for one occurrence of a stage in one
period: the stage after elaboration. It holds seven attributes and no other:
the declared name; the metadata of the file's `@` lines; the definitions
table, every declared name once as retained terms, an ordered read-only
mapping from each identity to its record; `initial`, the two initial
diagrams, the backward blocks and the forward blocks on the fields they read
and write; `_builders`, the record of the two builders graphs, the backward
builders on function wires and the forward builders on measure wires, which
the property `builder` reads by the pair of perches each builder joins, each
of the four graphs a `Refusal` where the construction could not build it; the
bindings of the version; and the record of how the occurrence was built.
No syntax tree or span table is retained. Whatever the definitions, the
graphs and the bindings determine is a query, answered by level
(`stage_answers.py`, `grains.py`, `boxes.py`,
`kernels.py`), and the six questions an economist puts to the stage
itself, `QUERY_METHODS`, are methods of the object under the same name, with
the three binding verbs `calibrate`, `methodize` and `configure`; its
parameters, its settings and its methods are the tables `par`, `settings`
and `methods`, and its builders the mapping `builder`, read as properties
beside the three perches `arvl`, `dcsn` and `cntn`. A question about one
piece is put to that piece and is a method of no stage.

Every mapping attribute is a `types.MappingProxyType` over a private dict built
fresh for the object, its values frozen recursively by `freeze`, and
`provenance` is the `Provenance` record over such a proxy.
The constructor stores a fresh copy of each mapping, so the dict beneath every
attribute is private to the object: a `MappingProxyType` is a read-only view
of the dict beneath it, not a copy, and without the copy a caller who kept and
edited its own dict would change the stage. The attributes themselves are
fixed at construction (a frozen dataclass). Equality compares the seven
attributes, a refusal without its position.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType

from discopy.frobenius import Hypergraph

from bellman.native.frozen import check_frozen_mapping, freeze, is_frozen
from bellman.native.hypergraphs import comparison_answered_once, freeze_native
from bellman.native.records import (
    Bindings,
    Builders,
    Definition,
    InitialDiagrams,
    Metadata,
    Provenance,
    Refusal,
    canonical_text,
    values_equal,
)
from bellman.native.versions import (
    GRAPH_RECORDS,
    STORED,
    StageVersion,
    passed_from_version,
    stored,
)

# the class body below binds a function of each of these modules as a method
from bellman.stage import binding_verbs, denotations, stage_answers
from bellman.stage.encoding import encoding
from bellman.stage.inventory import stage_sheet, version_word
from bellman.stage.components import check_components
from bellman.stage.levels import construct, declared_version
from bellman.stage.pieces import (
    BoundMethods,
    BuilderPairs,
    Parameters,
    PerchHandle,
    Settings,
    StoredAttribute,
)
from bellman.stage.places import components_by_place, places, typings
from bellman.syntax.vocabulary import ARRIVAL, CONTINUATION, DECISION


@dataclasses.dataclass(frozen=True, eq=False, kw_only=True)
class ElaboratedStage(StageVersion):
    """One version of a stage, with its declarations, graphs and bindings.

    `name` is the authored stage name and `metadata` its authored annotations.
    `definitions` is the read-only table of declarations and authored lines.
    `initial` gives the two initial diagrams, `backward` and `forward`, and
    `_builders` holds the record of the two builders graphs, which the
    property `builder` reads: `builder["cntn", "dcsn"]` is the builder that
    joins the two perches, `builder.policy` the policy builder, and
    `builder.bwd` and `builder.fwd` the two builders graphs. The perches
    `arvl`, `dcsn` and `cntn` reach the builders of the edge that leaves
    each, `dcsn.builder.bwd`. `bindings` holds calibration, methods and
    settings; `provenance` records the source and the bindings that produced
    this version. These seven attributes are retained; queries compute their
    answers without storing another model.

    `view()` prints the inventory; `denote()` answers the two builders
    graphs' denotations. `list()` names the contents and `encoding()` supplies
    this version's machine-readable record. `par`, `settings` and `methods`
    are the tables of the parameters, the settings and the bound methods, each
    read by its key, `par["ρ"]`. `methodize`, `calibrate` and `configure` each
    add their binding to the stage they are called on and return it; nothing
    is copied, and a later binding of a target replaces the earlier one
    (specification 0.6 §4.1 and decision 1).

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""

    name: str
    metadata: Mapping
    definitions: Mapping = StoredAttribute()
    initial: object = StoredAttribute()
    _builders: object = StoredAttribute()
    bindings: object = StoredAttribute()
    provenance: Mapping = StoredAttribute()

    # --- the verbs the stage answers ---

    def view(self):
        """The stage inventory as a printed sheet: its perches, fields, blocks,
        definitions, graphs, bindings and directions. Below the stage, ask a
        piece for its `denote()`.

        See `docs/Bellman-Sym/API/stage/01-the-stage.md` §3."""
        return str(self)

    def list(self):
        """The blocks of the two initial diagrams under `initial`, each with
        its kind and direction, and the builders under `builder`, each by its
        block identifier with the pair of perches it joins and its direction
        word, the listing that `builder.list()` answers.

        See `docs/Bellman-Sym/API/stage/01-the-stage.md` §4."""
        return stage_answers.stage_listing(self)

    @property
    def methods(self):
        """The components typed at the places of this version, by place, as
        a read-only mapping, `methods["policy"]`: the method word with its
        arguments, the grid and the handler the typing entries at the place
        give it. The answer is empty for a stage whose signatures carry no
        component; each piece answers the components within it.

        See `docs/Bellman-Sym/API/stage/07-methods.md` §2."""
        return BoundMethods(self, dict(components_by_place(self)))

    @property
    def par(self):
        """The parameters of this version, a read-only mapping from each
        parameter's name, as the file declares it, to its record, `par["ρ"]`,
        whose `value` is the number a calibration binds.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §1."""
        return Parameters(self)

    @property
    def settings(self):
        """The settings bound to this version, a read-only mapping from each
        setting's name to its record, `settings["n_a"]`, with its configured
        value and the methods that read it; empty before `configure`.

        See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §2."""
        return Settings(self)

    @property
    def builder(self):
        """The builders by the pair of perches each joins,
        `stage.builder["cntn", "dcsn"]`, with the two builders graphs at `bwd`
        and `fwd` and the policy builder at `policy`.

        See `docs/Bellman-Sym/API/stage/03-build.md` §1."""
        return BuilderPairs(self)

    @property
    def declared(self):
        """The declared builders, the operators the blocks of the stage file
        denote as elaboration builds them, with the interface of
        `stage.builder`: `stage.declared.policy`, `stage.declared["cntn",
        "dcsn"]`, `stage.declared.bwd`. Until a solution method's rows open a
        builder they are the operative builders `stage.builder` answers; the
        rows change the operative builders and leave these as they were.

        See `docs/Bellman-Sym/API/stage/03-build.md` §1."""
        return BuilderPairs(declared_version(self))

    @property
    def arvl(self):
        """The arrival perch: `stage.arvl.builder.fwd` is the forward builder
        from arrival.

        See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""
        return PerchHandle(self, ARRIVAL)

    @property
    def dcsn(self):
        """The decision perch: `stage.dcsn.builder.bwd` is the backward
        decision builder, `stage.dcsn.builder.policy` the policy builder.

        See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""
        return PerchHandle(self, DECISION)

    @property
    def cntn(self):
        """The continuation perch, the last of the stage: no edge of the
        stage leaves it, so its `builder` refuses both directions with the
        reason.

        See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""
        return PerchHandle(self, CONTINUATION)

    # --- the questions the stage answers and the three binding verbs ---
    # Each name is the module function itself, so that the method and the
    # function are one object. Nothing binds them by `setattr`.

    fields = stage_answers.fields
    obligations = stage_answers.obligations
    diagnostics = stage_answers.diagnostics
    denote = denotations.denote
    encoding = encoding
    places = places

    methodize = binding_verbs.methodize
    calibrate = binding_verbs.calibrate
    configure = binding_verbs.configure

    def __dir__(self):
        """What a reader who completes `stage.` sees (AMD-SG-007 §3; AMD-SG-010
        §4; AMD-SG-020 §3.1): the attributes and the public names of the class
        body, the verbs `view` and `list`, the tables `methods`, `par` and
        `settings`, the mapping `builder` and the three perches, the questions
        the stage answers about itself and the three binding verbs, with
        Python's own protocol names beside them, as inspection lists them for
        every object. The stored record `_builders` is left out, as every
        private name is."""
        protocol = {name for name in object.__dir__(self) if name.startswith("__")}
        return sorted(
            {field.name for field in dataclasses.fields(self) if not field.name.startswith("_")}
            | {name for name in vars(ElaboratedStage) if not name.startswith("_")}
            | protocol
        )

    # --- the printed description ---

    def __repr__(self):
        """The short form: `ElaboratedStage('cons', symbolic)` for a
        version with no binding; the stopping-point word `calibrated`,
        `methodized` or `specified` where the bindings present are an initial
        segment of the order calibrate, methodize, configure; else the bindings
        present in that order, `ElaboratedStage('cons', methods)`."""
        return f"ElaboratedStage({self.name!r}, {version_word(self)})"

    def __str__(self):
        """The stage's sheet (`inventory.stage_sheet`), in this order: the
        stage name and its source; the perches with the fields at each; the
        fields by role; the blocks in file order with their inputs and outputs
        as the author wrote them; the definitions table by kind; the two
        initial diagrams and the two builders graphs as present or refused,
        with a refusal's rule; one status line per binding, an absent binding
        naming the verb that supplies it; and the directions of the two
        initial diagrams."""
        return stage_sheet(self)

    def __hash__(self):
        values = [
            (
                field.name,
                _comparable_graphs(stored(self, field.name))
                if field.name in GRAPH_RECORDS
                else _compared_value(self, field.name),
            )
            for field in dataclasses.fields(self)
        ]
        return hash(canonical_text(tuple(values)))

    @comparison_answered_once
    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        for field in dataclasses.fields(self):
            left, right = _compared_value(self, field.name), _compared_value(other, field.name)
            if field.name in GRAPH_RECORDS:
                left, right = _comparable_graphs(left), _comparable_graphs(right)
            if not values_equal(left, right):
                return False
        return True

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise TypeError(f"ElaboratedStage.name must be a non-empty string; got {self.name!r}")
        for attribute, expected in (("initial", InitialDiagrams), ("_builders", Builders)):
            if not isinstance(stored(self, attribute), expected):
                raise TypeError(
                    f"ElaboratedStage.{attribute} must be a {expected.__name__} record holding "
                    f"{' and '.join(expected.MEMBERS)}; got "
                    f"{type(stored(self, attribute)).__name__}"
                )
        table = stored(self, "definitions")
        if not isinstance(table, Mapping) or not all(
            isinstance(value, Definition) and key == value.identity for key, value in table.items()
        ):
            raise TypeError(
                "ElaboratedStage.definitions must be an ordered "
                "mapping from each identity to its Definition record"
            )
        if not isinstance(self.bindings, Bindings):
            raise TypeError(
                "ElaboratedStage.bindings must be a Bindings "
                f"record; got {type(self.bindings).__name__}"
            )
        # A record `replace_stage` passes from a constructed version is held
        # as it is. A constructed version holds each stored record in its
        # frozen form, made by its constructor (`ElaboratedStage.__post_init__`),
        # by the copier (`copy_native`) or read back by the standard pickle, so
        # the record is not frozen again.
        for attribute in GRAPH_RECORDS:
            record = stored(self, attribute)
            if not passed_from_version(record):
                object.__setattr__(self, attribute, freeze_native(record))
        # A definitions table so passed is held as a new read-only mapping
        # of the same records.
        object.__setattr__(
            self,
            "definitions",
            MappingProxyType(dict(table))
            if passed_from_version(table)
            else freeze_native(dict(table)),
        )
        for attribute in _MAPPINGS:
            held = getattr(self, attribute)
            # a version built from another version is given that version's own
            # provenance and metadata records, whose mappings are
            # already frozen
            check_frozen_mapping(attribute, _frozen_mapping_of(held))
        # The stored mapping is `freeze` of the argument: a fresh proxy over a
        # fresh dict, so the dict beneath the attribute is private to this
        # object. A frozen dataclass assigns a field during construction
        # through `object.__setattr__`, the form the dataclasses module itself
        # uses in the `__init__` it generates. `provenance` is then held as the
        # record that prints its path and its digest and holds its six keys, so
        # that a bare `stage.provenance` does not print the stage file.
        for attribute in _MAPPINGS:
            frozen = freeze(_frozen_mapping_of(getattr(self, attribute)))
            object.__setattr__(
                self,
                attribute,
                Provenance(frozen) if attribute == "provenance" else Metadata(frozen),
            )


def make_stage(term, spans):
    """The `ElaboratedStage` of the stage that `term`, the parsed AST of a
    stage file or of its union with its additions, describes, with the span
    table `spans` of its parse, or None for a decoded term: the stage of the
    fields `construction.stage_fields` constructs, which states the pipeline
    and its refusals, read at its two levels by `levels.construct`, with
    every typing entry resolved to its place (`places.typings`) and the
    components checked against the catalogue's rows
    (`components.check_components`), so that an entry that names no place,
    types a component twice, omits a keyword its row requires or writes a
    grid the place does not admit is refused where the stage is made."""
    stage = ElaboratedStage(**construct(ElaboratedStage, term, spans))
    typings(stage, spans)
    check_components(stage)
    return stage


# The questions the stage answers about itself, each a method of the same
# name; a question about one piece, a query that takes a box among them, is a
# method of that piece and of no stage.
QUERY_METHODS = (
    "fields",
    "obligations",
    "diagnostics",
    "denote",
    "places",
    "encoding",
)


# the two verbs of the stage itself, its three tables, read as properties:
# the bound methods, the parameters and the settings, and the declared
# builders (specification 0.6 §7); and the three binding verbs
STAGE_VERBS = ("view", "list", "methods", "par", "settings", "declared")
BINDING_VERBS = ("methodize", "calibrate", "configure")


# The entries of a refusal's diagnostic that place it in a file; two stages
# built from one text, with and without positions, are equal.
_POSITION = ("file", "line", "column", "end_line", "end_column")


def _comparable_graphs(record):
    """The members of a stored graph record as equality reads them: a refusal
    without its position."""
    return {
        name: (
            Refusal(
                reason=value.reason,
                diagnostic={
                    key: item for key, item in value.diagnostic.items() if key not in _POSITION
                },
            )
            if isinstance(value, Refusal)
            else value
        )
        for name in record.MEMBERS
        for value in (getattr(record, name),)
    }


def _compared_value(stage, attribute):
    """The value of one attribute as equality and hashing read it: the record
    for the three of `STORED`, the attribute itself for the rest."""
    return stored(stage, attribute) if attribute in STORED else getattr(stage, attribute)


# The mapping attributes of a stage, always a read-only mapping.
_MAPPINGS = ("metadata", "provenance")


def _frozen_mapping_of(held):
    """The read-only mapping beneath one of the two mapping attributes: the
    record's own mapping where a version built from another version was given
    the `Provenance` or the `Metadata` record, and the value itself where the
    factory passed the mapping."""
    return held.entries if isinstance(held, (Provenance, Metadata)) else held
