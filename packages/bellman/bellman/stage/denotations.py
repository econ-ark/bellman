"""What a stage and each of its pieces denote (AMD-SG-021 §§2.2, 3): the
dispatch, which reads what a piece is and answers the record its card prints
(`denotation`, `denotation_of` and the `denotation_of_*` functions, with
`card`, the printed card); the signature of a piece (`box_signature`,
`graph_signature`); and the records themselves, made clause by
clause in the order a card prints them: the title, the wires, the kernel, the
at and where clauses, the coordinate, the method and the declarations, then
the cards of the definitions and the last step on every record. A record is
derived from the constructed stage and is independent of it once made.

Each record is kept for the version it was asked of, and so are the
identities each term of a record reads and the objects each identity
reaches, which a card's `definitions` block lists (`_kept_for`,
`versions.kept_answer`): a version is immutable, so a card printed again is
printed from the record made the first time. None of these answers is kept
through a binding (`versions.CARRIED`), since a card prints the bindings and
the source of its own version.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
import dataclasses
from dataclasses import replace
from types import MappingProxyType
from typing import NamedTuple

from discopy.frobenius import Bubble

from bellman.display import sheets
from bellman.display.cards import (
    AuthoredCard,
    BlockDenoted,
    Composite,
    Declared,
    DefinitionCard,
    Denoted,
    ImageAtPoint,
    ImageByName,
    ImageSet,
    KernelClause,
    MethodClause,
    OperatorCard,
    Piece,
    Rule,
    StageDenotation,
    Statement,
    Textual,
    TitleBlock,
    Wire,
)
from bellman.display.printed_records import SIDE_WORDS, Signature
from bellman.fold.block_lines import (
    block_coordinates,
    blocks_of,
    doc_lines,
    field_role,
    header_wire_sorts,
    perches_of,
)
from bellman.fold.derived_parameters import derived_values
from bellman.fold.stage_names import StageNames, branches_of
from bellman.fold.wire_terms import term_nodes
from bellman.native.identity import Identity, box_identity, piece_identity
from bellman.native.labels import box_label, is_wiring, italic, value_aggregations_of
from bellman.native.predicates import Compare
from bellman.native.records import Definition, typing_text
from bellman.native.versions import kept_answer, stored
from bellman.refusals import METHOD_CONDITIONS, NotConstructed, TargetError
from bellman.stage.boxes import (
    box_obligations,
    boxes_inside,
    builder_rows_of,
    is_block,
    methods_bound_within,
    methods_of_line,
    methods_within,
    piece_and_place,
    piece_named,
    row_at,
    row_of,
)
from bellman.stage.builder_pairs import arrow, builder_pairs
from bellman.stage.carriers import (
    coordinate_domain,
    declared_set_term,
    definition_type,
    policy_carrier,
    product,
    wire_type,
)
from bellman.stage.defining_expressions import (
    bound_point,
    declared_statement,
    definition_expression,
    definition_measure,
    distribution_symbol,
    law_outputs_read,
    law_outputs_rule,
    local_abbreviation,
    observable_set,
    observable_set_rule,
    operator_expression,
    section_identity,
    wire_expression,
    wire_name,
    wire_residual_rules,
    wire_rules,
)
from bellman.stage.grains import (
    ApplicationOrder,
    answering_row,
    answers_function_set,
    block_id_of,
    bound_blocks,
    chain_order,
    declared_definitions,
    derived_graph_at_grain,
    graph_of,
    graph_refusal,
    is_relation,
    kind_of,
    pieces_in_dependency_order,
    stored_graph_name,
    wire_table,
)
from bellman.stage.inventory import address_of, block_arrow, direction_entries
from bellman.stage.kernel_records import aggregator_kernel, kernel_record, law_of_motion_kernel
from bellman.stage.kernels import affine, conditioning, coordinates_of, integrated_shocks
from bellman.stage.levels import declared_version, is_declared_version, source_texts
from bellman.stage.places import block_box, components_of_box
from bellman.stage.stage_answers import descriptions, fields, obligations, source_spans
from bellman.stage.term_operations import reference_term, tuple_term
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import ARRIVAL, CONTINUATION, DECISION, PERCH_MARK, VALUE_ROLES
from bellman.typing import typed_expressions as S
from bellman.typing.primitive_definitions import primitive_definition
from bellman.typing.typed_expressions import WireType

# --- the answers kept for the version ---


def _kept_for(stage, key, held, compute):
    """The answer `compute` gives, kept for this version under `key` and the
    `id` of each object of `held`, the box, the definition record or the term
    the answer is of (`versions.kept_answer`). Each object is kept beside its
    answer, so that no other object takes its `id` while the answer is kept.
    No key is among `versions.CARRIED`, so a stage computes these answers
    again after a binding: a card prints the bindings and the source of its
    own version."""
    return kept_answer(stage, key + tuple(id(item) for item in held), lambda: (held, compute()))[1]


# --- the denotation of a stage and of a piece ---


def denote(stage):
    """The stage's backward and forward builders-graph denotations, under those
    two direction names. A refused direction carries its refusal instead.
    The printed answer is the same mathematical record a caller reads, kept
    for the version.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""

    def compute():
        shown = []
        for word in ("backward", "forward"):
            held = graph_refusal(stage, "builders", word)
            if held is not None:
                # the graph answers the record whose printed form is its
                # REFUSED sheet, and the stage's own answer is one line that
                # names the rule and points to GRAPHS (AMD-SG-021 §2.1)
                shown.append((word, f"refused under {held.diagnostic['rule']}; see GRAPHS"))
                continue
            try:
                shown.append((word, denotation_of_graph(stage, level="builders", direction=word)))
            except NotConstructed as refusal:
                shown.append((word, str(refusal)))
        return with_definitions_and_source(
            stage,
            StageDenotation(
                directions=tuple(shown), stage=stage.name, conditions=tuple(obligations(stage))
            ),
        )

    return kept_answer(stage, "stage denotation", compute)


def card(stage, box):
    """The printed card of a box or a definition of this version, as a string
    (AMD-SG-021 §3): the title block of the piece and, beneath it under no
    label, the statement of what it denotes. It is the printed form of the
    record `denote()` answers, `str(denotation_of(stage, box))`, and is
    the implementation beneath the card, bound as no method of the stage
    (AMD-SG-010 §4).

    `box` is a box or a definition record of this version, or the unambiguous
    name of one; a box or record of another version, a name that names nothing
    and an ambiguous name are refused as `TargetError`. Computed from the
    retained definitions and the native graphs; the record is kept for the
    version, and the card is printed from it at each call."""
    return str(denotation_of(stage, box))


def denotation_of(stage, box):
    """What one box or definition of this version denotes, as the record of
    AMD-SG-021 §2.2 whose printed form is its card: an `OperatorCard` for a
    primitive operator, a `Composite` for a builder or a sub-builder, an
    `AuthoredCard` for a block, an authored line or an initial diagram, and
    a `DefinitionCard` for another record of the definitions table. Every
    handle's `denote()` and `__str__` pass through this function or through
    the one for its own level."""
    derived = derived_graph_at_grain(stage, box)
    if derived is not None:
        return denotation_of_builder(stage, box)
    target, entry = piece_and_place(stage, box)
    if isinstance(target, Definition):
        return denotation_of_definition(stage, target)
    if isinstance(target, Bubble):
        return (
            denotation_of_block(stage, target)
            if is_block(target)
            else denotation_of_builder(stage, target)
        )
    if kind_of(target) is None:
        return denotation_of_definition(stage, stage.definitions[target.name], target)
    return denotation_of_operator(stage, target, entry)


def denotation_of_operator(stage, box, entry=None):
    """What a primitive operator denotes, as the `OperatorCard` record of
    AMD-SG-021 §2.2: the mapping with its image, the typed wires, the
    feasibility, the kernel with the statements it denotes and the objects
    they denote, the hypotheses, the conditions and, on a methodized version,
    the method bound within the piece. The record's printed form is the
    piece's card, and `operator_card` builds it."""
    if entry is None:
        # the place the box stands in, as `card` resolves it: a box of two
        # folds is read at the grain its own card names
        box, entry = piece_and_place(stage, box)
    return operator_card(stage, box, placement=entry)


def denotation_of_builder(stage, box):
    """What a builder or a sub-builder denotes, as the `Composite` record of
    AMD-SG-021 §2.2, built by `_composite` from its pieces' own records and
    the wiring; kept for the version by the bubble."""

    def compute():
        return _composite(
            stage,
            box_signature(stage, box),
            list(boxes_inside(box)),
            holder=box.name,
            header=_header_of_bubble(stage, box),
            coordinate=_coordinate_answer(stage, _card_coordinate_names(stage, box)),
            title=_title_of_bubble(stage, box),
            bound=methods_within(stage, box),
            # the lines marked `!doc` of the block are the conditions on the
            # constructed output, held on `doc` and printed there, not among
            # the conditions (AMD-SG-034 §3 `declared`)
            doc=_declared(stage, box.name),
            conditions=tuple(box_obligations(stage, box)),
            declarations=_declarations(stage, box.name),
            free=(),
        )

    return _kept_for(stage, ("builder card",), (box,), compute)


def denotation_of_block(stage, box):
    """What a block or a sub-block of an initial diagram denotes, as the
    `AuthoredCard` record of AMD-SG-021 §2.2: its typed wires, its authored
    lines with their file positions, its header and the control it is read
    at; kept for the version by the bubble. The statements are the lines the
    box holds (`_statements_of_block`), each read as `denote_line` reads it
    (`_line_version`): a line of the stage file on the stage as declared
    (`levels.declared_version`), so that no binding changes it (decision
    SC-13), and a line an addition appends on the version that holds it. The
    wires, the header, the method clause and the conditions are read on the
    declared version, which prints no method clause and no condition of a
    method, the methods a stage binds being answered by
    `stage.initial.methods` and printed on the cards of the operative
    builders; a block the stage file does not write, one an addition adds
    whole, is read on the version that holds it."""
    declared = declared_version(stage)
    reading = declared if _declares_block(declared, box) else stage

    def compute():
        signature = box_signature(reading, box)
        statements = []
        for address in _statements_of_block(stage, box):
            record = stage.definitions[address]
            on = _line_version(stage, declared, record)
            doc = _WORDS["doc"] in (getattr(record, "tags", ()) or ())
            statements.append(
                Statement(
                    address,
                    _authored_text(on, address),
                    written_at(on, address) or "",
                    doc=doc,
                    no_wire=doc,
                )
            )
        return with_definitions_and_source(
            reading,
            AuthoredCard(
                kind="block",
                inputs=_card_wires(reading, signature.inputs),
                outputs=_card_wires(reading, signature.outputs),
                statements=tuple(statements),
                tags=tuple(held.address for held in statements if held.doc),
                header=_header_of_bubble(reading, box),
                coordinate=_coordinate_answer(reading, _coordinate_sorts(reading, box)),
                method=_method_clause(reading, methods_within(reading, box)),
                conditions=tuple(box_obligations(reading, box)),
                title=_title_of_bubble(reading, box),
            ),
        )

    return _kept_for(reading, ("block card",), (box,), compute)


def _declares_block(declared, box):
    """Whether the stage file writes the block `box`, or the block it is
    nested in, so that the declared version holds a block of that name: an
    addition adds a nested block under a label its parent writes already
    (`label-not-in-parent`) and adds a top-level block whole."""
    return box.name.split(".", 1)[0] in {held.name for held in blocks_of(declared)}


def _line_version(stage, declared, definition):
    """The version an authored line is read on: the stage as declared,
    `declared`, where its definitions hold the line, which the stage file
    writes, and `stage` itself for a line an addition appends, which the
    declared version does not hold."""
    if stored(declared, "definitions").get(definition.identity) is not None:
        return declared
    return stage


# the record kinds in the terminology's words, as the stamp of a sheet prints
# them
_RECORD_STAMP = {
    "set": "SET",
    "distribution": "DISTRIBUTION",
    "parameter": "PARAMETER",
    "derived_parameter": "DERIVED PARAMETER",
    "setting": "SETTING",
    "function": "FUNCTION",
    "function_alias": "FUNCTION ALIAS",
    "correspondence": "CORRESPONDENCE",
    "g": "LAW OF MOTION",
    "G": "VALUE AGGREGATOR",
    "line": "BLOCK LINE",
    "typing": "TYPING ENTRY",
}


def denotation_of_definition(stage, definition, box=None):
    """What one record of the definitions table denotes: the `AuthoredCard`
    record of an authored line, and the `DefinitionCard` of a set, a parameter,
    a function, a correspondence, a distribution, a law of motion or a value
    aggregator (AMD-SG-021 §3.5). `box` is the line box the record is read at,
    where the record is reached as a box of an initial diagram. Kept for the
    version by the record and the box."""
    return _kept_for(
        stage,
        ("definition card",),
        (definition, box),
        lambda: (
            denote_line(stage, definition, box)
            if definition.kind == "line"
            else typing_card(stage, definition)
            if definition.kind == "typing"
            else definition_card(stage, definition)
        ),
    )


def denotation_of_graph(stage, *, level=None, direction=None, grain="builder"):
    """What a graph denotes: for a builders graph the `Composite` record of
    AMD-SG-021 §2.2, its pieces' own records in the order of application of
    §3.4 and, on the backward graph, the free name the notation cannot carry;
    for an initial diagram the `AuthoredCard` record of its blocks (§3.5); and
    for a graph the construction refused the record whose printed form is the
    REFUSED sheet (§2.1). Kept for the version by the level, the direction and
    the grain as they are written."""

    def compute():
        refusal = graph_refusal(stage, level, direction)
        if refusal is not None:
            return denote_refusal(stage, level, direction, grain, refusal)
        if level == "initial":
            return denote_diagram(stage, level, direction, grain)
        held = graph_of(stage, level, direction, grain)
        signature = graph_signature(stage, level=level, direction=direction, grain=grain)
        inside = [part for part in held.boxes if not is_wiring(part)]
        return _composite(
            stage,
            signature,
            inside,
            holder=None,
            header=(),
            coordinate=(),
            title=graph_title(stage, level, direction, grain),
            bound=methods_within(stage, inside),
            doc=(),
            conditions=tuple(obligations(stage)),
            declarations=(),
            free=(
                _free_name(stage, inside) if (level, direction) == ("builders", "backward") else ()
            ),
        )

    return _kept_for(stage, ("graph card", level, direction, grain), (), compute)


# --- the signature of a piece ---


def box_signature(stage, box):
    """The inputs and the outputs of one box, as the `Signature` record of
    AMD-SG-013 §2, read from the sorts of its wires. One function serves
    `signature()` at both levels of the navigation, a bubble and a primitive
    box (AMD-SG-014 §2). A bubble is a builder, a block or a sub-builder: a
    block of an initial diagram answers with its field wires, the control it is
    read at among none of them, and the builder of the same name answers with
    the wires of its own graph, functions or measures. A primitive box's
    answer prints the value bundles as bundles (AMD-SG-011 §2):

        in          (𝑉, 𝑑𝑉) : Xm × ℝ₊₊ → [-inf, inf) × (0, inf]
        out         (𝑉, 𝑑𝑉) : Xm → [-inf, inf) × (0, inf]

    so that a reader sees that the two wires are one object into a product and
    does not assemble that from the card's `wire in` and `wire out` lines. A
    decision builder's signature is the signature of the operator at the
    policy, and a box held at a policy names the policy on its `applies` and
    `operator` lines and on no line of its signature; the policy is typed on
    the output of the policy builder. After the field component stand the
    components typed at the piece (specification 0.7, the ruling "On
    structure"): a builder's or a block's own, `policy.method : !egm`, and a
    primitive operator's, the Evaluation's with the object each is typed for.

    Each wire's identity stands on the record, not on the printed line. A
    primitive operator's lines are set as its card sets them under
    DENOTATION, so that `str(signature())` is that contiguous block of
    `str(denote())`. A bubble's and a line's are set as `signature_lines`
    of `display/printed_records.py` sets the same entries."""
    if isinstance(box, Bubble):
        components = tuple(
            (place.address, held) for place, held in components_of_box(stage, box.name)
        )
    else:
        components = tuple(methods_within(stage, box).items())
    return Signature(
        wire_records(stage, box.dom.inside, with_definitions=False),
        wire_records(stage, box.cod.inside, with_definitions=False),
        components,
    )


def graph_signature(stage, *, level, direction=None, grain="builder"):
    """The inputs and the outputs of one graph, as the `Signature` record of
    AMD-SG-013 §2. An input the source supplies among the stage's declared
    inputs is listed by its type alone; an input some builder consumes that
    nothing produces and no header declares carries the words `supplied by no
    builder`. In the backward builders graph every input and output is a
    function; a state, a control or a shock is a bound argument of those
    functions and is not listed. The policy is an output of the backward graph,
    written by the policy builder, and is an input of no graph."""
    graph = graph_of(stage, level, direction, grain)
    level, direction = stored_graph_name(level, direction)
    inputs, outputs = tuple(graph.dom.inside), tuple(graph.cod.inside)
    declared = getattr(stored(stage, "initial"), direction if level == "initial" else "backward")
    declared_in = {ob.identity for ob in declared.dom.inside}
    if (level, direction) == ("builders", "backward"):
        declared_in = {
            Identity("function", stage=stage.name, perch=i.perch, field=i.field)
            if field_role(stage, i) in VALUE_ROLES
            else i
            for i in declared_in
        }
    if (level, direction) == ("builders", "forward"):
        declared_in = {
            p.identity for p in inputs if p.role == "measure"
        }  # the measure no forward builder produces
    given = tuple(
        Wire(
            wire.name,
            wire.identity,
            wire.sort,
            mathematical_type=wire.mathematical_type,
            note="" if wire.identity in declared_in else "supplied by no builder",
            controls=wire.controls,
            rules=wire.rules,
            residuals=wire.residuals,
        )
        for wire in wire_records(stage, inputs, with_definitions=False)
    )
    return Signature(given, wire_records(stage, outputs, with_definitions=False))


# --- the records a card prints ---

# the operator kinds of AMD-SG-010 to 012 in the terminology's words, as the
# stamp of a sheet prints them
_KIND_STAMP = {
    "DistributionExtension": "DISTRIBUTION EXTENSION",
    "PolicyInsertion": "POLICY INSERTION",
}


# The words of a card this module reads by their keys (AMD-SG-021 §2.3).
_WORDS = {
    # the words an authored piece's card carries (§3.5)
    "doc": "!doc",
    "rule": "rule",
    "address": "address",
    "reason": "reason",
    "no rule": "no rule named",
    "of": "of",
    "none": "none",
    "no value input": "no value input",
}


def operator_card(stage, box, *, placement=None):
    """The operator's expression, typed data and existing stage conditions,
    read at the row that produced the box at `placement`, the `Place` its card
    names, and where no place is given at the row of the place the box stands
    at (`boxes.row_of`); kept for the version by the box and by the level and
    the grain of the place."""

    def compute():
        row = row_of(stage, box) if placement is None else row_at(stage, box, placement)
        ins, outs = tuple(box.dom.inside), tuple(box.cod.inside)
        kind = box_identity(box).kind
        expression = operator_expression(stage, box, row)
        body = expression.body if isinstance(expression, S.Lambda) else expression
        if isinstance(expression, S.Lambda) and len(expression.bindings) == 1:
            names = tuple(T.Sym(T.Constant(sort.identity)) for sort in ins)
            argument = names[0] if len(names) == 1 else T.Tuple(names)
            body = S.substitute(body, {expression.bindings[0][0].identity: argument})
        image = (
            ImageAtPoint(body)
            if isinstance(body, S.Lambda)
            else ImageSet(body)
            if isinstance(body, T.Comprehension)
            else ImageByName(body)
        )
        kernel = _kernel_clause(stage, box, row)
        conditions = card_conditions(tuple(box_obligations(stage, box)))
        inputs, outputs = wire_records(stage, ins), wire_records(stage, outs)
        return with_definitions_and_source(
            stage,
            OperatorCard(
                kind=kind,
                policies=tuple(_policies_within(stage, box)),
                inputs=inputs,
                outputs=outputs,
                image=image,
                feasible=(),
                affine=_affine_text(stage, box, row),
                kernel=kernel,
                required=(),
                coordinate=_coordinate_answer(stage, _card_coordinates(stage, box, row)),
                conditions=conditions,
                method=_method_clause(stage, methods_within(stage, box)),
                title=_title_block(
                    stage,
                    address_of(stage, f"OPERATOR {box.name}"),
                    subtitle=box_label(
                        box, _value_aggregations(stage) if kind == "Aggregation" else frozenset()
                    ),
                    stamp=sheets.stamp("KIND", _KIND_STAMP.get(row.kind, row.kind.upper())),
                    identity=box_identity(box),
                    level=placement.level if placement is not None else "builders",
                    grain=placement.grain if placement is not None else "builder",
                ),
                expression=expression,
                at=_policy_denoted(stage, row.policy, row.identity),
                where=_local_abbreviations(
                    stage, box, row, _referenced_aliases(inputs + outputs, conditions)
                ),
            ),
        )

    # the two parts of the place the record reads: the level and the grain
    # its title names, the grain choosing the fold the row is read from
    place = None if placement is None else (placement.level, placement.grain)
    return _kept_for(stage, ("operator card", place), (box,), compute)


def _value_aggregations(stage):
    """The identities of the value aggregations of the stage, read from its
    backward builders graph at the primitive grain, where every aggregation
    stands beside the Evaluation it feeds; an aggregation has one identity at
    every grain, so the answer serves a box of any grain. Kept for the
    version; the graph it is read from is itself kept."""
    return kept_answer(
        stage,
        "value aggregations",
        lambda: value_aggregations_of(graph_of(stage, "builders", "backward", "primitive")),
    )


def _composite(
    stage,
    signature,
    inside,
    *,
    holder,
    header,
    coordinate,
    title,
    bound,
    doc,
    conditions,
    declarations,
    free,
):
    """The `Composite` record of §2.2 of a builder, a sub-builder or a
    builders graph, built from its pieces' own records and the wiring (§2.3),
    with the parts only a bubble or only a graph has given by its caller.

    Its `order` is the order of application of §3.4: the chain where the
    wiring gives one, and otherwise the dependency order, each piece after
    every piece that writes a wire it reads. `holder` is the name of the
    bubble a piece's key is read from, None for a graph."""
    order = chain_order(inside)
    ordered, order_kind = (
        ApplicationOrder(order, "application")
        if order is not None
        else pieces_in_dependency_order(inside)
    )
    pieces = tuple(
        Piece(piece_named(part, holder), str(box_identity(part)), _record_of(stage, part))
        for part in ordered
    )
    # the policy the builder is at and the local abbreviations its pieces
    # introduce, each once (AMD-SG-034 §3, §10 items 3 and 11)
    policies = tuple(
        dict.fromkeys(
            identity for box in inside for identity in _policy_identities_within(stage, box)
        )
    )
    where = []
    for piece in pieces:
        for item in getattr(piece.record, "where", ()):
            if item not in where:
                where.append(item)
    return with_definitions_and_source(
        stage,
        Composite(
            policies=tuple(
                dict.fromkeys(name for box in inside for name in _policies_within(stage, box))
            ),
            inputs=_card_wires(stage, signature.inputs),
            outputs=_card_wires(stage, signature.outputs),
            pieces=pieces,
            chain=order is not None,
            order=tuple(piece.key for piece in pieces),
            order_kind=order_kind,
            free=free,
            header=header,
            coordinate=coordinate,
            conditions=conditions,
            method=_method_clause(stage, bound),
            title=title,
            at=_policy_denoted(stage, policies),
            where=tuple(where),
            doc=doc,
            declarations=declarations,
        ),
    )


def _record_of(stage, part):
    """The record of one piece of a composite: its own `OperatorCard` where it
    is a primitive operator, its own `Composite` where it is a bubble."""
    if isinstance(part, Bubble):
        return denotation_of_builder(stage, part)
    return operator_card(stage, part)


def denote_line(stage, definition, box=None):
    """What one authored line of a block denotes (§3.5): its statement with its
    address in the label column and its file position at the right margin, then
    `tags`, the control it is read at where it reads no wire, `describes` and
    `method`. A line of the stage file is read on the stage as declared
    (`levels.declared_version`), as the card of its block is, so that no
    binding changes its card (decision SC-22); a line an addition appends is
    read on the stage that holds it (`_line_version`)."""
    stage = _line_version(stage, declared_version(stage), definition)
    return with_definitions_and_source(
        stage,
        AuthoredCard(
            kind="line",
            statements=(
                Statement(
                    definition.address,
                    _authored_text(stage, definition.address),
                    written_at(stage, definition.address) or "",
                ),
            ),
            tags=_marks(definition),
            coordinate=_coordinate_answer(stage, _line_coordinates(stage, definition, box)),
            describes=descriptions(definition),
            method=_method_clause(stage, methods_of_line(stage, definition)),
            title=_title_block(
                stage,
                address_of(stage, f"LINE {definition.address}"),
                subtitle=f"line of {definition.address.split('.', 1)[0]}",
                stamp=sheets.stamp("KIND", _RECORD_STAMP["line"]),
                identity=definition.identity,
                level="initial",
            ),
            conditions=_definition_conditions(stage, definition),
        ),
    )


def definition_card(stage, definition):
    """What one record of the definitions table denotes (§3.5): the declaration
    as the file writes it under its own label, the object it denotes as
    `↦ symbol : type := rule` with the rule that constructs it cited by number,
    the descriptions the author wrote, the parameters the declaration names and
    the bindings within the record.

    A declaration cites Appendix C §2.1; a law of motion cites R1 and a value
    aggregator R5, which are the numbers their kernel's clause cites, so that
    the definition card, the operator's card and the listing state one fact one
    way."""
    kind = definition.kind
    denoted = (
        _kernel_denoted(stage, definition)
        if kind in ("g", "G")
        else _declared_denoted(stage, definition)
    )
    return with_definitions_and_source(
        stage,
        DefinitionCard(
            kind=kind,
            statement=_definition_statements(stage, definition),
            denoted=denoted,
            hypotheses=(),
            describes=descriptions(definition),
            conditions=_definition_conditions(stage, definition),
            method=_method_clause(stage, methods_bound_within(stage, {definition.identity})),
            title=_title_block(
                stage,
                address_of(stage, f"DEFINITION {definition.identity}"),
                subtitle=_definition_subtitle(stage, definition),
                stamp=sheets.stamp("KIND", _RECORD_STAMP.get(kind, kind.upper())),
                identity=definition.identity,
                level="definition",
            ),
        ),
    )


def typing_card(stage, definition):
    """What a typing record denotes: the entry as the file writes it under
    its own label, `policy.method : !egm`, and the place and the component
    it types."""
    return DefinitionCard(
        kind=definition.kind,
        statement=Statement(definition.identity.address, typing_text(definition), definition.address),
        denoted=(),
        hypotheses=(),
        describes=(),
        conditions=(),
        method=(),
        title=_title_block(
            stage,
            address_of(stage, f"DEFINITION {definition.identity}"),
            subtitle=f"the {definition.identity.field} component of {definition.identity.address}",
            stamp=sheets.stamp("KIND", _RECORD_STAMP["typing"]),
            identity=definition.identity,
            level="definition",
        ),
    )


def denote_diagram(stage, level, direction, grain):
    """What an initial diagram denotes (§3.5): its `in` wires, one record per
    block, its `out` wires, and the directions of the diagram, which its
    DIRECTIONS section prints. Its card keeps one section per block, the one
    card below the stage that holds more than a statement."""
    graph = graph_of(stage, level, direction, grain)
    signature = graph_signature(stage, level=level, direction=direction, grain=grain)
    return with_definitions_and_source(
        stage,
        AuthoredCard(
            kind="initial diagram",
            inputs=_card_wires(stage, signature.inputs),
            outputs=_card_wires(stage, signature.outputs),
            pieces=tuple(
                Piece(_arrowed(stage, box), box.name, denotation_of_block(stage, box))
                for box in graph.boxes
                if not is_wiring(box)
            ),
            statements=tuple(
                Statement(word, text, "") for word, text in direction_entries(stage, direction)
            ),
            title=graph_title(stage, level, direction, grain),
        ),
    )


def denote_refusal(stage, level, direction, grain, refusal):
    """What a graph the construction refused answers (§2.1): the record whose
    printed form is the REFUSED sheet, holding the rule, the authored item
    responsible with the file and line it was written at, and the sentence the
    refusal states. The stage sheet's GRAPHS section names the same refusal in
    one line (AMD-SG-015 §3)."""
    diagnostic = refusal.diagnostic
    written, line = diagnostic.get("file"), diagnostic.get("line")
    statements = [Statement(_WORDS["rule"], diagnostic.get("rule") or _WORDS["no rule"], "")]
    if diagnostic.get("address"):
        # a refusal of a term decoded from a saved AST carries no position and
        # the line holds the address alone
        statements.append(
            Statement(
                _WORDS["address"],
                diagnostic["address"],
                f"{written.rsplit('/', 1)[-1]}:{line}" if written and line is not None else "",
            )
        )
    statements.append(Statement(_WORDS["reason"], refusal.reason, ""))
    return with_definitions_and_source(
        stage,
        AuthoredCard(
            kind="refusal",
            statements=tuple(statements),
            title=graph_title(stage, level, direction, grain),
        ),
    )


# --- the title of a card ---


def _pair_of(stage, block):
    """`cntn → dcsn` for the block id of a backward or a forward builder, from
    the wire table (`builder_pairs`); `""` for a block the mapping does not
    classify, including the policy builder, whose title carries no pair
    (the plan `builder-names-pair-base`, task 3)."""
    pairs, _, _ = builder_pairs(stage)
    return next(
        (arrow(pair) for pair, boxes in pairs.items() if any(box.name == block for box in boxes)),
        "",
    )


def _title_block(
    stage,
    address,
    *,
    subtitle="",
    stamp="",
    identity=None,
    level="builders",
    direction="",
    grain="builder",
):
    """The title block of a card: its address, subtitle and stamp, and the
    native components of the address, the stage, the identity, the level, the
    direction, the keys, the grain and, for a builder, the pair of perches it
    joins, never recovered from display text. The pair is the builder's
    identity, so every title at the builders level names it by the pair,
    whatever grain the piece stands at and whatever handle reached it."""
    keys = ()
    pair = ""
    if identity is not None:
        block = identity.block
        if level != "definition" and block is not None:
            rendering = wire_table(stage)
            direction = (
                "policy"
                if block in rendering.policy_blocks
                else rendering.direction.get(block, direction)
            )
            keys = (block,) + ((identity.key_within(block),) if identity.key_within(block) else ())
            if level == "builders":
                pair = _pair_of(stage, block)
    return TitleBlock(
        address=address,
        subtitle=subtitle,
        stamp=stamp,
        stage=stage.name,
        identity=identity,
        level=level,
        direction=direction,
        keys=keys,
        grain=grain,
        pair=pair,
    )


def _title_of_bubble(stage, bubble, grain=None):
    """The title block of a builder, a sub-builder, a block or a sub-block
    (AMD-SG-015 §2): its address with the arrow of its direction, the stamp of
    its grain on a builder and of its wires on a block, and the label of a
    piece named by a node id as its subtitle. The level is read from the class
    of the box, a block of an initial diagram being a `Block` and a builder a
    `Builder`, and a sub-builder or a sub-block, born of an authored `!node`
    line, from the kind of its identity, as its short form reads it
    (`piece_word`), never from a name's text: a nested block of a branching,
    `dcsn_to_cntn.keep`, is a block."""
    if grain is None:
        derived = derived_graph_at_grain(stage, bubble)
        grain = derived.grain if derived is not None else "builder"
    block = is_block(bubble)
    node = box_identity(bubble).kind == "line"
    word = "BLOCK" if block else "BUILDER"
    address = address_of(
        stage, f"{'SUB-' if node else ''}{word} {bubble.name if node else _arrowed(stage, bubble)}"
    )
    stamp = sheets.stamp("WIRES", "FIELDS") if block else _grain_stamp(grain)
    return _title_block(
        stage,
        address,
        subtitle=box_label(bubble, frozenset()) if node else "",
        stamp=stamp,
        identity=box_identity(bubble),
        level="initial" if block else "builders",
        grain=grain,
    )


def graph_title(stage, level, direction, grain):
    """The title block of a graph's card: its address, with the stamp of its
    grain on a builders graph and of its wires on an initial diagram."""
    word = "BUILDERS" if level == "builders" else "INITIAL DIAGRAM"
    stamp = _grain_stamp(grain) if level == "builders" else sheets.stamp("WIRES", "FIELDS")
    return _title_block(
        stage,
        address_of(stage, f"{direction.upper()} {word}"),
        stamp=stamp,
        level=level,
        direction=direction,
        grain=grain,
    )


def _header_of_bubble(stage, bubble):
    """The authored builder header and its retained file position."""
    if bubble.name not in {box.name for box in blocks_of(stage)}:
        return ()
    return (_authored_header(stage, bubble.name), written_at(stage, bubble.name) or "")


# --- the wires of a card ---


def wire_records(stage, sorts, *, with_definitions=True) -> tuple:
    """The wire answers of `sorts`, in order, each with the carrier `wire_type`
    derives, its controls, its rules and its residual lines; with its defining
    expressions (`expression`, `definition`) unless `with_definitions` is
    False, which a signature passes, since a signature prints no defining
    expression."""
    return tuple(
        Wire(
            wire_name(stage, sort),
            sort.identity,
            sort,
            mathematical_type=wire_type(stage, sort),
            expression=wire_expression(stage, sort) if with_definitions else None,
            definition=wire_expression(stage, sort, expand=True) if with_definitions else None,
            controls=_wire_controls(stage, sort),
            rules=wire_rules(stage, sort),
            residuals=wire_residual_rules(stage, sort),
        )
        for sort in sorts
    )


def _card_wires(stage, wires):
    """The wires of a card: each wire of a signature with its annotations
    kept and its expression, definition, controls, rules and residual lines
    derived."""
    return tuple(
        Wire(
            wire.name,
            wire.identity,
            wire.sort,
            mathematical_type=wire.mathematical_type,
            note=wire.note,
            expression=wire_expression(stage, wire.sort),
            definition=wire_expression(stage, wire.sort, expand=True),
            controls=_wire_controls(stage, wire.sort),
            rules=wire_rules(stage, wire.sort),
            residuals=wire_residual_rules(stage, wire.sort),
        )
        for wire in wires
    )


def _wire_controls(stage, sort):
    """The declared controls whose joint policies this set contains: the
    unknowns of the row that answers the set (`grains.answering_row`), where
    that row answers a set of functions (`grains.answers_function_set`), an
    `Argmax` or a relation with no explicit side."""
    row = answering_row(stage, sort.identity)
    return tuple(row.unknowns) if row is not None and answers_function_set(stage, row) else ()


# --- the kernel of a card ---


def _kernel_clause(stage, box, row):
    """The definitions and supplied policy data that determine
    this operator."""
    table = stage.definitions
    denoted, statements = [], list(_statements_of(stage, row))
    identity, symbol, owner = "", "", ""
    if answers_function_set(stage, row):
        # an argmax or a relation with no explicit side applies no law of
        # motion and no aggregator: the identification, a pullback, composes
        # with none
        word = "relation"
    elif row.kind in ("Pullback", "Pushforward", "Aggregation"):
        spec = kernel_record(stage, row)
        if spec is not None:
            identity, symbol, owner = spec.identity, italic(spec.letter), _spec_owner(stage, spec)
            denoted.append(
                _denoted_definition(
                    stage,
                    table[identity],
                    row,
                    symbol=symbol,
                    cited="R1" if spec.letter == "g" else "R5",
                )
            )
        word = "law of motion" if row.kind != "Aggregation" else "value aggregator"
    elif row.kind in ("Expectation", "DistributionExtension"):
        identity = row.identity
        symbol = distribution_symbol(integrated_shocks(stage, row), conditioning(stage, row))
        for reference in row.references:
            if reference in table:
                statements.append(_declared_statement(stage, table[reference]))
        # the law by reference: the declaration the row integrates against,
        # as the distribution's own card holds it first, the one place the
        # law is written (AMD-SG-034 §4 item 7); its measure at the written
        # parameters stands on the distribution's own card alone
        for reference in row.references:
            if reference in table and table[reference].kind == "distribution":
                denoted.append(_distribution_denoted(stage, table[reference])[0])
        word = "shock probability distribution"
    else:
        word = "policy" if row.policy else ""
    # the policy the box is at stands on the record's `at`, and the law of
    # motion or the aggregator at that policy on its `where` (AMD-SG-034 §3)
    if not word and not statements:
        return None
    return KernelClause(
        kind=word,
        symbol=symbol,
        owner=owner,
        identity=identity,
        statements=tuple(statements),
        denoted=tuple(denoted),
    )


def _spec_owner(stage, spec):
    """The owner of a law of motion or a value aggregator: the block that
    defines it, with the segment where an aggregation applies one of several
    (AMD-SG-019 §2.4)."""
    if spec.letter == "g":
        return spec.builder
    whole = Identity("Aggregation", address=spec.builder)
    return spec.builder if spec.segment == whole else f"{spec.builder}, segment {spec.segment}"


def _statements_of(stage, row):
    """The authored lines a kernel denotes, as `Statement` records: the lines
    whose operations the row represents, then the lines it holds as their
    properties (`row.properties`), and for a pullback and a push-forward the
    equations of the law of motion it composes with, which is the forward
    block's line (§3.3); the identification, a pullback whose output is its
    own unknown, composes with no law and denotes its own line. The left
    sides of a group are aligned at the equals sign, and a line written
    `!doc` carries its mark, which the card sets beside its address."""
    table = stage.definitions
    # a derivative line stands at the Evaluation of the value builder that
    # writes the value, so the Evaluation's card quotes it (AMD-MB-001 D4)
    written = (
        tuple(getattr(row, "statements", ()))
        + tuple(getattr(row, "properties", ()))
        + tuple(entry[2] for entry in getattr(row, "derivatives", ()))
    )
    addresses = [address for address in written if address in table]
    if (
        row.kind in ("Pullback", "Pushforward")
        and not is_relation(row)
        and getattr(row, "definition", None) in table
    ):
        addresses = [address for address in table[row.definition].equations if address in table]
    return tuple(
        Statement(
            address=address,
            text=_authored_text(stage, address),
            position=written_at(stage, address) or "",
            doc=_WORDS["doc"] in (getattr(table[address], "tags", ()) or ()),
        )
        for address in addresses
    )


def _declared_statement(stage, definition):
    """One declaration as a statement a kernel denotes: the label of §3.5 in
    the label column, its text as the file writes it, and its file position.
    The address of a record written at the top level is that position
    (AMD-SG-017 §4), which the span table does not key, so the position is read
    from the address where the spans hold none. The label is read by
    `_declared_label`, since a distribution's identity carries no field and the
    field alone would set `None` where a name belongs."""
    written = written_at(stage, definition.address)
    if written is None and not str(definition.address).isdigit():
        written = str(definition.address)
    return Statement(
        _declared_label(definition), _authored_text(stage, definition.address), written or ""
    )


def _declared_label(definition):
    """The label a declaration stands under: the `id` its annotation gives,
    where it gives one, and the record's own name otherwise (§3.5). A
    distribution's identity carries no field, so it stands under the subjects
    its law declares, which is how its identity is spelled."""
    for mark in definition.tags or ():
        if mark.startswith("id="):
            return mark[len("id=") :]
    if definition.identity.field is not None:
        return definition.identity.field
    law = definition.equations[0]
    return ", ".join(getattr(law, "subjects", ())) or str(definition.address)


def _affine_text(stage, box, row):
    """In which value inputs an aggregation is affine, as §3.1 item 5 states
    it: the affine outputs, `none` where no output is, and `no value input`
    where the aggregator reads none. The answer is `kernels.affine`, which
    reads the retained term of each output against the value inputs taken
    together; the value inputs are named by the aggregator's own argument
    names. No other kind of box carries the line, and no relation with no
    explicit side (`grains.answers_function_set`), which maps nothing."""
    if row.kind != "Aggregation" or answers_function_set(stage, row):
        return ""
    inputs = ", ".join(name for name, _ in _value_inputs(stage, box, row))
    if not inputs:
        return _WORDS["no value input"]
    answer = affine(stage, box)
    if isinstance(answer, Mapping):
        held = [output for output, yes in answer.items() if yes]
    else:
        outputs = aggregator_kernel(stage, row).parts.outputs
        held = list(outputs) if answer else []
    return f"{', '.join(held) or _WORDS['none']} {SIDE_WORDS['in']} {inputs}"


def _value_inputs(stage, box, row):
    """The value arguments of an aggregator, each as the name the aggregator
    gives it and the wire that carries it, in the order of the aggregator's own
    signature. The `value input` lines of the kernel and the `affine` line of
    the denotation both read this, so the two name one argument alike."""
    spec = aggregator_kernel(stage, row)
    held = {sort.identity: sort for sort in box.dom.inside}
    return tuple(
        (spec.shown[spec.index[key]], held[key])
        for key in sorted(spec.index, key=spec.index.get)
        if key in held
    )


# --- the at and where clauses of a card ---


def _policy_denoted(stage, policies, owner=None):
    """The policy a piece or a builder is at, typed as the policy builder
    types it (AMD-SG-034 §3 `at`, §10 item 3): one `Denoted` per policy,
    its name, the carrier of its wire and its identity; several controls a
    box is held at together, one `Denoted` under their names with the
    carrier of the joint policies and the map that reads them at the point."""
    policies = tuple(policies)
    rendering = wire_table(stage)
    if len(policies) <= 1:
        return tuple(
            Denoted(
                symbol=wire_name(stage, rendering.sort_of(policy)),
                mathematical_type=wire_type(stage, rendering.sort_of(policy)),
                expression=None,
                cited="",
                identity=policy,
            )
            for policy in policies
        )
    ctx = StageNames(stage)
    coordinates = tuple(rendering.sort_of(policies[0]).coordinates)
    controls = tuple(
        Identity("field", stage=stage.name, perch=policy.perch, field=policy.field)
        for policy in policies
    )
    row = next((op for op in rendering.table.primitive_rows if tuple(op.policy) == policies), None)
    holder = (
        owner
        if owner is not None
        else (row.identity if row is not None else piece_identity(stage.name))
    )
    carrier = policy_carrier(ctx, coordinates, controls, holder)
    # the joint policy is held by its type and its components' feasibility,
    # as one policy is, and by no map
    expression = None
    declarations = tuple(
        dict.fromkeys(
            entry
            for policy in policies
            for entry in wire_type(stage, rendering.sort_of(policy)).declarations
        )
    )
    functions = carrier.base.factors if isinstance(carrier.base, T.Product) else (carrier.base,)
    mathematical_type = WireType(
        (
            "function",
            None,
            coordinates,
            functions[0].domain,
            product(function.codomain for function in functions),
        ),
        carrier,
        declarations,
    )
    return (
        Denoted(
            symbol="(" + ", ".join(italic(p.field) for p in policies) + ")",
            mathematical_type=mathematical_type,
            expression=expression,
            cited="",
            identity=None,
        ),
    )


def _policies_within(stage, box):
    """The policies a box, or a box inside it at any depth, is held at: the row
    of an evaluation or an insertion whose kernel is the policy (§3.4)."""
    return tuple(
        dict.fromkeys(italic(held.field) for held in _policy_identities_within(stage, box))
    )


def _policy_identities_within(stage, box):
    """The identities of the policies a box, or a box inside it at any depth,
    is held at (§2.2, the field `free`)."""
    if isinstance(box, Bubble):
        return tuple(
            held for part in boxes_inside(box) for held in _policy_identities_within(stage, part)
        )
    rows = [
        row
        for fold in builder_rows_of(stage, block_id_of(box))
        for row in fold
        if row.identity == box.name
    ]
    return tuple(rows[0].policy) if rows else ()


def _free_name(stage, inside):
    """The free name of a backward graph that holds an evaluation at a policy
    and a policy builder (§2.2): the policy's name, the piece that reads it,
    the identity it resolves to and the piece whose output carries that
    identity. A free name is no wire and orders no piece (AMD-SG-013 §1)."""
    at, writes, identity = None, None, None
    for box in inside:
        held = _policy_identities_within(stage, box)
        if held and at is None:
            at, identity = box_identity(box).block, held[0]
        if any(getattr(sort, "role", None) == "control" for sort in box.cod.inside):
            writes = box_identity(box).block
    if at is None or writes is None or at == writes:
        return ()
    return (italic(identity.field), at, identity, writes)


def _local_abbreviations(stage, box, row, referenced=()):
    """The `where` entries of a piece (AMD-SG-034 §3): the outputs of the
    law of motion as a `Rule` where the law writes several coordinates (§4
    item 6), at the point the row's own rules read them by name
    (`law_outputs_read`), `(y_f, y_p) = 𝑔≻(m_f, m_p, w_d, 𝑐, 𝑐_p)` for a
    relation read at the point and `(a_nxt_adj, h_nxt_adj, z_nxt_adj) =
    𝑔≻(m, z_d, c, h_choice)` for a solve, and the same of the Pullback or
    Pushforward of the row's own builder whose output the row reads, at
    that operation's point, the law at the policy written out, except a
    pullback's in a builder a row of which reads the law's outputs by name,
    whose line that row states; the law's section at each label a row reads
    it at with the outputs of that label's branch; and every abbreviation
    of the row's builder that a term of the piece refers to by identity
    (`referenced`: the aliases free in its wires' expressions, rules and
    residual lines and in its conditions), the block's observable set among
    them with its defining `Rule` (AMD-SG-035 §10), so that the piece's card
    states what its expressions refer to. The law of motion and the
    aggregator at the policy have no abbreviation and no entry: a term
    reads them written out, `𝑔≻(m_d, 𝑐(m_d))` (RL14)."""
    outputs, inputs = tuple(box.cod.inside), tuple(box.dom.inside)
    ctx = StageNames(stage)
    rendering = wire_table(stage)
    found = []

    def add(item):
        if item is not None and item not in found:
            found.append(item)

    def abbreviations(held, held_outputs, held_inputs):
        if answers_function_set(stage, held):
            # an argmax or a relation with no explicit side, the
            # identification among them, composes with no law of motion
            return
        labels = (
            (held.section,)
            if held.kind == "Pullback" and held.section is not None
            else tuple(
                sort.identity.field
                for sort in held_outputs
                if held.kind == "Pushforward"
                and sort.identity.kind == "measure"
                and sort.identity.field
            )
        )
        if labels:
            # a row that reads the law at a label reads its section, stated
            # once under `where` with the outputs it writes, and no law at
            # the policy
            source = (
                held_outputs[0].coordinates
                if held.kind == "Pullback"
                else held_inputs[0].coordinates
            )
            for label in labels:
                add(section_denoted(stage, held, label))
                add(law_outputs_rule(ctx, held, tuple(source), label))
            return
        if (
            held.kind in ("Pullback", "Pushforward")
            and held_outputs
            and held_inputs
            and not (held.kind == "Pullback" and held.builder in named)
        ):
            source = (
                held_outputs[0].coordinates
                if held.kind == "Pullback"
                else held_inputs[0].coordinates
            )
            add(law_outputs_rule(ctx, held, tuple(source)))

    # the builders a row of which reads the outputs of its law by name: there
    # that row states the law's line once, at the point its rules read it,
    # and a pullback's line, at the pullback's own point, would state the
    # same names a second time with another reading
    named = {
        other.builder
        for other in rendering.table.primitive_rows
        if other.builder == row.builder and law_outputs_read(stage, other) is not None
    }
    add(law_outputs_read(stage, row))
    if row.kind == "Evaluation":
        # an Evaluation's output holds the rules of the operation before it
        # (`wire_rules`), so it states the names those rules read as well
        for identity in row.inputs:
            answering = answering_row(stage, identity)
            if answering is not None:
                add(law_outputs_read(stage, answering))
    abbreviations(row, outputs, inputs)
    for producer, producer_inputs, producer_outputs in _producers_of_inputs(stage, row):
        abbreviations(producer, producer_outputs, producer_inputs)
    referenced = set(referenced)
    if referenced:
        # the sections of the other Pullbacks of the row's builder that the
        # piece's terms refer to, `𝑔_keep≻` on an Evaluation
        for held in rendering.table.primitive_rows:
            if held.identity == row.identity or held.builder != row.builder:
                continue
            if held.kind == "Pullback" and held.section is not None:
                item = section_denoted(stage, held, held.section)
                if item.identity in referenced:
                    add(item)
    if observable_set(ctx, row.builder) in referenced:
        # the defining line of the block's observable set, on the grid of the
        # input the row reads on it (AMD-SG-035 §10), or of the output it
        # writes there, whose rule names its point in that set
        # (`card-redesign.md` §2, change 4)
        grid = next(
            (
                sort.coordinates
                for sort in inputs + outputs
                if any(ctx.role(identity) == "multiplier" for identity in sort.coordinates)
            ),
            None,
        )
        if grid is not None:
            add(observable_set_rule(ctx, row.builder, grid))
    return tuple(found)


def section_denoted(stage, row, label):
    """The law of motion read at one label, stated once under `where`:
    `𝑔_keep≻ : X∼ → X_keep, 𝑔_keep≻(a_d, h_d, z_d) = 𝑔≻(a_d, h_d, z_d, keep)`,
    the label in roman."""
    ctx = StageNames(stage)
    identity = section_identity(ctx, row.builder, label)
    spec = law_of_motion_kernel(stage, row.definition)
    states = tuple(i for i in spec.index if not ctx.labels(i))
    fields = dict(
        branches_of(stage, block_box(stage, row.definition.address))
    )[label]
    point, points = bound_point(ctx, identity, states)
    arguments = tuple(points.get(i, T.Sym(T.Constant(label))) for i in spec.index)
    expression = S.Lambda(point, S.Apply(reference_term(row.definition), (tuple_term(arguments),)))
    carrier = S.MeasurableMapSet(
        coordinate_domain(ctx, states, identity), coordinate_domain(ctx, fields, identity)
    )
    mathematical_type = WireType(
        ("measurable", None, states, carrier.domain, carrier.codomain), carrier, ()
    )
    return Denoted(
        symbol=identity.field,
        mathematical_type=mathematical_type,
        expression=_defining_relation(identity, expression),
        cited="R1",
        identity=identity,
        specializes=row.definition,
    )


def _defining_relation(identity, expression):
    """A local abbreviation held with its defining relation at the point, the
    abbreviation applied to the coordinates its map binds and equated with
    the map's body there, `𝑔_keep≻(a_d, h_d, z_d) = 𝑔≻(a_d, h_d, z_d,
    keep)`; the map as held where it is no map."""
    if not isinstance(expression, S.Lambda):
        return expression
    point = tuple_term(reference_term(variable.identity) for variable, _ in expression.bindings)
    return Compare(S.Apply(reference_term(identity), (point,)), "=", expression.body)


def _referenced_aliases(wires, conditions):
    """The identities of the local abbreviations the terms of a piece refer
    to: the aliases free in its wires' expressions, rules and residual lines
    and in its conditions' terms."""
    terms = []
    for wire in wires:
        terms.append(wire.expression)
        for rule in (*wire.rules, *wire.residuals):
            terms.extend((rule.statement, *rule.where, rule.on))
    terms.extend(condition.predicate for condition in conditions)
    found = set()
    for term in terms:
        if term is None or isinstance(term, Textual):
            continue
        found.update(
            identity
            for identity in S.free_identities(term)
            if isinstance(identity, Identity) and identity.kind == "alias"
        )
    return found


def _producers_of_inputs(stage, row):
    """The Pullback or Pushforward rows of the row's own builder that produce
    one of its inputs, each with its input and output sorts: the operations
    whose local abbreviations the row reads. The identification, a Pullback
    whose output is its own unknown, composes with no law of motion and is
    none of them."""
    rendering = wire_table(stage)
    found = []
    for other in rendering.table.primitive_rows:
        if (
            other.identity != row.identity
            and other.builder == row.builder
            and other.kind in ("Pullback", "Pushforward")
            and not is_relation(other)
            and set(other.outputs) & set(row.inputs)
        ):
            found.append(
                (
                    other,
                    tuple(rendering.sort_of(i) for i in other.inputs),
                    tuple(rendering.sort_of(i) for i in other.outputs),
                )
            )
    return found


# --- the coordinate, the method and the declarations of a card ---


def _coordinate_answer(stage, sorts):
    """Bound coordinates with their declared scalar or product sets."""
    ctx, result = StageNames(stage), []
    for sort in sorts:
        domain = declared_set_term(ctx, ctx.declared_set(sort.identity), sort.identity)
        value_type = WireType(("scalar", None, (), T.Product(()), domain), domain)
        result.append(
            Denoted(
                symbol=sort.identity.field,
                mathematical_type=value_type,
                expression=None,
                cited="",
                identity=sort.identity,
            )
        )
    return tuple(result)


def _card_coordinates(stage, box, row):
    """The coordinates a box's card names: the controls its block is read at
    that the box's own terms mention (AMD-SG-014 §1)."""
    block = getattr(row, "builder", None)
    if not block or block not in {b.name for b in blocks_of(stage)}:
        return ()
    coordinates = block_coordinates(block_box(stage, block), header_wire_sorts(stage))
    reads = {identity for sort in box.dom.inside for identity in coordinates_of(sort)}
    reads |= {identity for sort in box.cod.inside for identity in coordinates_of(sort)}
    table = fields(stage)
    return tuple(
        table[identity] for identity in coordinates if identity in reads and identity in table
    )


def _printed_arguments(value):
    """A bound method's keyword arguments with each term among their values,
    a quoted string or a word with arguments, printed as the stage file
    writes it, at every depth of their mappings and tuples; a setting's name
    and a number stay as they are."""
    if dataclasses.is_dataclass(value):
        return to_source(value)
    if isinstance(value, Mapping):
        return {key: _printed_arguments(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_printed_arguments(item) for item in value)
    return value


def _method_clause(stage, bound):
    """The components within a piece as the `method` clause prints them
    (§3.1 item 11): per place the method word with its arguments, the grid
    and the handler, each where typed, the place's address, and the values
    of the settings the keyword arguments name on a specified version. A
    card of the declared level, read on the version `declared_version`
    makes, prints none, though its piece's `methods` answers them (decisions
    SC-13 and SC-24)."""
    if is_declared_version(stage):
        return ()
    values = stage.bindings.settings or {}
    return tuple(
        MethodClause(
            address=address,
            method=held.method,
            grid=held.grid,
            handler=held.handler,
            written=str(held),
            options=tuple(
                (keyword.key, _option_value(keyword.value, values))
                for keyword in (held.method.arguments if held.method is not None else ())
            ),
        )
        for address, held in bound.items()
    )


def _option_value(value, values):
    """A keyword argument's value as the `Options` row of a card prints it:
    the configured value of the setting a name names, where one is bound,
    and the argument as written otherwise."""
    if isinstance(value, T.Name) and value.name in values:
        return repr(values[value.name])
    return to_source(value)


def _declarations(stage, block):
    """The lines of a block that declare its multipliers (AMD-SG-035 §5), each
    as a `Statement` holding the line as the file writes it and its position,
    which stands in the `source` block and forms no piece."""
    return tuple(
        Statement(
            record.address,
            _authored_text(stage, record.address),
            written_at(stage, record.address) or "",
        )
        for record in stage.definitions.values()
        if record.kind == "multiplier" and record.address.split(".", 1)[0] == block
    )


def _declared(stage, block):
    """The lines marked `!doc` of a block as `Declared` records: the line as
    the file writes it with its position, and the line with the constructed
    output substituted (`defining_expressions.declared_statement`). For a
    builder a bound method block opens, the declared lines of the stage
    file's block come first, the statement the method rows are to reach,
    each read on the declared version (specification 0.6 §4.1)."""
    opened = next((held for held in bound_blocks(stage) if held.builder == block), None)
    declared = (
        tuple(stage.definitions[address] for address in opened.declared_lines)
        if opened is not None
        else ()
    )
    reading = declared_version(stage) if opened is not None else stage
    return tuple(
        Declared(
            Statement(
                definition.address,
                _authored_text(stage, definition.address),
                written_at(stage, definition.address) or "",
                doc=True,
            ),
            declared_statement(reading if definition in declared else stage, definition),
        )
        for definition in declared + tuple(doc_lines(stage, block))
    )


# --- the cards of the definitions ---


def _denoted_definition(stage, definition, row=None, *, symbol=None, cited=""):
    """A named definition with its carrier and defining expression
    already derived."""
    if definition.kind in ("g", "G"):
        block = next(
            (held for held in blocks_of(stage) if held.name == definition.identity.block), None
        )
        if block is not None:
            marks = perches_of(block, header_wire_sorts(stage))
            mark = next((PERCH_MARK[perch] for perch in marks if PERCH_MARK.get(perch)), "")
            # the segments of the aggregator: the maps the block's G applies,
            # each plain aggregation's and the explicit side of a relation
            # (`grains.explicit_side`); a relation with no explicit side, a
            # solve or a system of candidate statements, is no segment
            siblings = (
                [
                    entry
                    for entry in builder_rows_of(stage, definition.address).closed
                    if entry.kind == "Aggregation" and not answers_function_set(stage, entry)
                ]
                if definition.kind == "G" and row is not None
                else ()
            )
            # the one spelling of a subscript, `𝑔≻`, `𝐺_value≻` (AMD-SG-034
            # §4 item 11), is `defining_expressions.local_abbreviation`
            if len(siblings) > 1:
                line = stage.definitions[row.statements[0]].identity
                label = line.statement or row.identity.key_within(definition.identity.block)
                symbol = local_abbreviation(italic(definition.kind), mark, (), label)
            elif mark:
                symbol = local_abbreviation(italic(definition.kind), mark)
    return Denoted(
        symbol=symbol if symbol is not None else definition.identity.field,
        mathematical_type=definition_type(stage, definition, row),
        expression=definition_expression(stage, definition, row),
        cited=cited,
        identity=definition.identity,
    )


def _definition_subtitle(stage, definition):
    """The subtitle of a definition's card: the kind in the terminology's words
    with the record's own name, and the owner of a law of motion or a value
    aggregator (AMD-SG-015 §4.5)."""
    kind, name = definition.kind, definition.identity.field
    if kind == "g":
        return law_of_motion_kernel(stage, definition.identity).title
    if kind == "G":
        return f"{italic('G')} {_WORDS['of']} {definition.address}"
    if kind == "distribution":
        return f"distribution of {', '.join(definition.equations[0].subjects)}"
    return f"{kind.replace('_', ' ')} {name}"


def _definition_statements(stage, definition):
    """The statement of a definition's card (§3.5): the declaration as the file
    writes it, under the `id` its annotation gives or under the record's own
    name, with the file position it was written at. A law of motion and a value
    aggregator are defined by the authored lines of their block and hold those
    instead, as their kernel's clause does, the left sides of a group aligned
    at the equals sign."""
    table = stage.definitions
    if definition.kind in ("g", "G"):
        addresses = [address for address in definition.equations if address in table]
        return tuple(
            Statement(address, _authored_text(stage, address), written_at(stage, address) or "")
            for address in addresses
        )
    if definition.kind == "correspondence":
        statements = [_declared_statement(stage, definition)]
        for line in table.values():
            if line.kind != "line":
                continue
            used = any(
                isinstance(node, T.Operator)
                and node.head == "argmax"
                and any(
                    isinstance(binder, T.In)
                    and isinstance(binder.set, T.Call)
                    and binder.set.fun == definition.identity.field
                    for binder in node.subs
                )
                for node in term_nodes(line.equations)
            )
            if used:
                statements.append(
                    Statement(
                        line.address,
                        _authored_text(stage, line.address),
                        written_at(stage, line.address) or "",
                        doc="!doc" in (line.tags or ()),
                    )
                )
        return tuple(statements)
    return _declared_statement(stage, definition)


def _kernel_denoted(stage, definition):
    """The objects a law of motion or a value aggregator denotes, which the
    kernel's clause of the operator's card prints, one per segment of an
    aggregation (§3.5). A segment is a map the block's G applies: a plain
    aggregation's, and the explicit side of a relation
    (`grains.explicit_side`), `𝐺_InvEuler≻`. A relation with no explicit
    side, a solve or a system of candidate statements, answers the set of
    the solutions of its relation (`grains.answers_function_set`) and is no
    segment."""
    rows = (
        [None]
        if definition.kind == "g"
        else [
            row
            for row in builder_rows_of(stage, definition.address).closed
            if row.kind == "Aggregation" and not answers_function_set(stage, row)
        ]
    )
    specs = (
        [law_of_motion_kernel(stage, definition.identity)]
        if definition.kind == "g"
        else [aggregator_kernel(stage, row) for row in rows]
    )
    denoted = []
    for spec, row in zip(specs, rows):
        denoted.append(
            _denoted_definition(
                stage,
                definition,
                row,
                symbol=italic(spec.letter),
                cited="R1" if definition.kind == "g" else "R5",
            )
        )
    return tuple(denoted)


def _declared_denoted(stage, definition):
    """The object a declaration denotes, cited `[§2.1]`: a parameter as a point
    of its declared set, with its value on a calibrated version; a derived
    parameter as a point of the set its definition declares, the reals where
    it declares none, by its definition and, on a calibrated version, its
    value; a set as
    written, and a set marked `!categories` also as its category map, the
    `CategoryCodes` its record holds; a function and a function alias as a map
    from its declared sets; a correspondence with `⇉`; a distribution as a
    probability kernel from the arguments it is conditioned on to a measure,
    with the family's convention on a line beneath (§3.5)."""
    kind, name = definition.kind, definition.identity.field
    identity = definition.identity
    if kind in ("parameter", "setting"):
        # a parameter's value is bound by the calibration, a setting's by
        # the configuration (specification 0.7, S1)
        values = stage.bindings.calibration if kind == "parameter" else stage.bindings.settings
        declared = declared_set_term(
            StageNames(stage), definition.equations[0] if definition.equations else None, identity
        )
        mathematical_type = WireType(("scalar", None, (), T.Product(()), declared), declared)
        expression = T.Number(values[name]) if values is not None and name in values else None
        return (
            Denoted(
                symbol=name,
                mathematical_type=mathematical_type,
                expression=expression,
                cited="§2.1",
                identity=identity,
            ),
        )
    if kind == "derived_parameter":
        # a constant of the stage, written roman as a parameter is, a point of
        # the reals: its definition, and on a calibrated version, as its second
        # object, the value its definition takes there (AMD-MT-003, build
        # contract §5); where its definition declares a set, its record's one
        # coordinate, a point of that set, as a parameter is of its own
        declared = (
            declared_set_term(StageNames(stage), definition.coordinates[0][1], identity)
            if definition.coordinates
            else T.Named("ℝ")
        )
        mathematical_type = WireType(("scalar", None, (), T.Product(()), declared), declared)
        values = stage.bindings.calibration
        held = (definition.equations[0],)
        if values is not None:
            held += (T.Number(derived_values(stage, values)[name]),)
        return tuple(
            Denoted(
                symbol=name,
                mathematical_type=mathematical_type,
                expression=expression,
                cited="§2.1",
                identity=identity,
            )
            for expression in held
        )
    if kind == "set":
        held = (definition.equations[0],)
        if definition.categories is not None:
            held += (definition.categories,)
        return tuple(
            Denoted(
                symbol=name,
                mathematical_type=None,
                expression=expression,
                cited="§2.1",
                identity=identity,
            )
            for expression in held
        )
    if kind in ("correspondence", "function"):
        return (
            _denoted_definition(
                stage,
                definition,
                symbol=italic(name) if kind == "function" else name,
                cited="§2.1",
            ),
        )
    if kind == "function_alias":
        return (
            Denoted(
                symbol=italic(name),
                mathematical_type=definition_type(stage, definition),
                expression=Textual(to_source(definition.equations[0])),
                cited="§2.1",
                identity=identity,
            ),
        )
    if kind == "distribution":
        return _distribution_denoted(stage, definition)
    if kind == "multiplier":
        # the multiplier of a bound declared in a block body, a point of its
        # declared set, and its declaration with the clause as written (§5)
        declared = declared_set_term(StageNames(stage), definition.coordinates[0][1], identity)
        mathematical_type = WireType(("scalar", None, (), T.Product(()), declared), declared)
        return (
            Denoted(
                symbol=name,
                mathematical_type=mathematical_type,
                expression=Textual(to_source(definition.equations[0])),
                cited="R10",
                identity=identity,
            ),
        )
    return ()


def _distribution_denoted(stage, definition):
    """A declared distribution by its declared law (AMD-SG-034 §4 item 7,
    §10 item 7): an unconditional law under the subjects as the file writes
    them, `ψ`, `(Ψ, θ)`, the law as written and a member of the probability
    measures on the subjects' declared sets; a law the file conditions as a
    kernel from the arguments it reads, `P_{θ|η, s}`. A law of a scalar
    family the definitions define denotes a second object, its measure at
    the written parameters under the distribution's symbol, `P_ψ`
    (`definition_measure`). No convention sentence stands beneath: the
    family's rule is read on its own definition."""
    law = definition.equations[0]
    given = tuple(n for n, _ in definition.coordinates)
    subjects = tuple(law.subjects)
    symbol = (
        distribution_symbol(subjects, given)
        if given
        else subjects[0]
        if len(subjects) == 1
        else "(" + ", ".join(subjects) + ")"
    )
    first = _denoted_definition(stage, definition, symbol=symbol, cited="§2.1")
    measure = definition_measure(stage, definition)
    if measure is None:
        return (first,)
    second = Denoted(
        symbol=symbol if given else S.declared_distribution_symbol(subjects),
        mathematical_type=first.mathematical_type,
        expression=measure,
        cited="§2.1",
        identity=definition.identity,
    )
    return first, second


def _definition_conditions(stage, definition):
    """The parameters and conditions a declaration names, which its `where`
    clause prints, one conjunct to a line (§3.5)."""
    identities = {definition.identity}
    if definition.kind in ("g", "G"):
        identities.update(
            stage.definitions[address].identity
            for address in definition.equations
            if address in stage.definitions
        )
    return tuple(
        item
        for item in obligations(stage)
        if any(
            identity in identities for identity in item.entries if isinstance(identity, Identity)
        )
    )


# --- the last step on every record ---


def with_definitions_and_source(stage, answer):
    """A detached answer with its free declarations and its source
    information resolved."""
    if hasattr(answer, "conditions"):
        answer = replace(answer, conditions=card_conditions(answer.conditions))
    kernel = getattr(answer, "kernel", None)
    if kernel is not None:
        statements = list(kernel.statements)
        for condition in answer.conditions:
            for subject in condition.named_identities:
                definition = stage.definitions.get(subject.address)
                if definition is not None and definition.kind == "line":
                    statement = Statement(
                        definition.address,
                        _authored_text(stage, definition.address),
                        written_at(stage, definition.address) or "",
                        doc="!doc" in (definition.tags or ()),
                    )
                    if not any(item.address == statement.address for item in statements):
                        statements.append(statement)
        answer = replace(answer, kernel=replace(kernel, statements=tuple(statements)))
    return replace(
        answer,
        definitions=_with_block_files(stage, supporting_definitions(stage, answer)),
        source=stage.provenance.get("path") or stage.provenance.get("origin") or "",
    )


def _with_block_files(stage, denoted):
    """The objects `denoted`, each that an addition defines given as a
    `BlockDenoted`, with the addition's file name and the line of its
    definition, `methods.bl:3`, read from the address of its record in the
    definitions table; the objects the stage file defines as they are."""
    _, _, additions = source_texts(stage)
    files = {origin: origin.rpartition("/")[2] for _, origin in additions}
    if not files:
        return denoted
    table = stored(stage, "definitions")
    found = []
    for item in denoted:
        record = table.get(item.identity)
        path, _, line = str(getattr(record, "address", "") or "").rpartition(":")
        if path in files and line.isdigit():
            item = BlockDenoted(
                **{name: getattr(item, name) for name in item.__dataclass_fields__},
                written_at=f"{files[path]}:{line}",
            )
        found.append(item)
    return tuple(found)


def card_conditions(items):
    """The conditions a card prints: exactly the items that hold a predicate
    and that the analysis has not discharged, a condition being a term or no
    condition (AMD-SG-034 §2 items 0 and 3, §10 item 5). The
    stage retains every item: the sentence-only ones and the established
    ones, each with its evidence, on `obligations()`."""
    return tuple(
        item
        for item in items
        if item.status != "established"
        and (
            # the condition a bound method requires holds no term and prints
            # by its name (specification 0.6 §4.1)
            item.condition in METHOD_CONDITIONS
            or item.predicate is not None
            # a condition whose term holds an unresolved marker is no term
            # a reader can check: it stays on `obligations()` as a gap and
            # prints on no card
            and not any(isinstance(node, S.Unresolved) for node in term_nodes(item.predicate))
        )
    )


def supporting_definitions(stage, answer):
    """The declared objects reached by free references in this answer.

    References of a declared object's type and expression are followed once.
    No callable is executed and no mathematical property is inferred. The
    identities a term reads and what an identity reaches are kept for the
    version (`_identities_read`, `_reached`).
    """
    parts = list(_mathematical_parts(answer))
    for denoted in (
        *getattr(answer, "denoted", ()),
        *getattr(getattr(answer, "kernel", None), "denoted", ()),
    ):
        definition = stage.definitions.get(denoted.identity)
        if definition is not None and definition.kind in ("function_alias", "derived_parameter"):
            parts.append(definition.equations)
    found, seen = [], set()

    def reach(identities):
        for identity in identities:
            if identity in seen:
                continue
            seen.add(identity)
            reached = _reached(stage, identity)
            found.extend(reached.denoted)
            parts.extend(reached.terms)

    # the multiplier each line under `declarations` declares, a line the card
    # prints in its `source` block: its record, found by the line's address,
    # from which `_declarations` formed the line (AMD-SG-035 §5)
    lines = {statement.address for statement in getattr(answer, "declarations", ())}
    reach(
        definition.identity
        for definition in stage.definitions.values()
        if definition.kind == "multiplier" and definition.address in lines
    )
    while parts:
        term = parts.pop(0)
        if term is None or isinstance(term, Textual):
            continue
        reach(_identities_read(stage, term))
    order = _definition_order(stage)
    found.sort(key=lambda denoted: order.get(denoted.identity, len(order)))
    return tuple(found)


def _definition_order(stage):
    """The place of each identity in the stage's definitions table, the file's
    order of declaration, which is the order a card's `definitions` block
    lists them in (AMD-SG-034 §3); kept for the version."""
    return kept_answer(
        stage,
        "definition order",
        lambda: MappingProxyType(
            {identity: place for place, identity in enumerate(stage.definitions)}
        ),
    )


def _declarations_by_field(stage):
    """The declaration of each name a term can read free, by the name: every
    record of the definitions table that carries a field, save the authored
    lines, the laws of motion and the value aggregators; kept for the
    version."""
    return kept_answer(
        stage,
        "declarations by field",
        lambda: MappingProxyType(
            {
                definition.identity.field: definition
                for definition in stage.definitions.values()
                if definition.identity.field is not None
                and definition.kind not in ("line", "g", "G")
            }
        ),
    )


def _laws_by_subject(stage):
    """The distribution declaring each shock, by the shock's name, by the
    name of its field and, for shocks drawn jointly, by the one variable
    `(Ψ, θ)` they are bound as: a bound coordinate named after a shock, `ψ`
    in `(k, ψ, ξ) ↦ …` or in `∫_{ψ ∈ ℝ₊₊} […]`, writes the name the shock's
    law declares, `ψ ~ …`, and the distribution declaring it is reached as
    well (AMD-SG-034 §3 `definitions`: every name a card writes that the
    definitions hold). Kept for the version."""

    def compute():
        laws = {}
        for definition in stage.definitions.values():
            if definition.kind == "distribution":
                subjects = definition.identity.subjects
                joint = "(" + ", ".join(subjects) + ")" if len(subjects) > 1 else None
                for subject in (*subjects, definition.identity.field, joint):
                    if subject:
                        laws.setdefault(subject, definition)
        return MappingProxyType(laws)

    return kept_answer(stage, "laws by subject", compute)


def _identities_read(stage, term):
    """The identities a term reads, each free name by the declaration it
    names, in the order of their text, a coordinate named after a shock
    preceded by the shock's law; then the law of each shock a binder of the
    term binds. The answer reads the term's free identities and bound domains
    (`typed_expressions.free_identities`, `bound_domains`) and is kept for the
    version by the term, since the records a card reads again hold the same
    terms. A `Named` term is kept by its value, the name, and not by its `id`:
    `_semantic_type_parts` makes a new `Named` term for each declared set at
    every call, and its answer depends on the name alone."""

    def read():
        declarations, laws = _declarations_by_field(stage), _laws_by_subject(stage)
        for identity in sorted(S.free_identities(term), key=str):
            if isinstance(identity, str) and identity in declarations:
                identity = declarations[identity].identity
            # a coordinate named after a shock read free, `Ψ` in the
            # condition `𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))^(1 − γ) ∈ ℝ₊₊` at the point,
            # writes the shock's name as a bound one does
            if (
                isinstance(identity, Identity)
                and identity.kind == "function-parameter"
                and identity.field in laws
            ):
                yield laws[identity.field].identity
            yield identity
        for bound in S.bound_domains(term):
            # a variable a primitive definition binds, `z` of the measure of
            # `N(0, 1)`, is the definition's own and names no shock
            owner = getattr(bound, "owner", None)
            rule = primitive_definition(owner.field) if isinstance(owner, Identity) else None
            if rule is not None and rule.identity == owner:
                continue
            # an authored binder, `E_{Ψ}`, is bound by its name alone
            subjects = (
                (bound,)
                if isinstance(bound, str)
                else (*getattr(bound, "subjects", ()), getattr(bound, "field", None))
            )
            for subject in subjects:
                if subject in laws:
                    yield laws[subject].identity

    if isinstance(term, T.Named):
        return kept_answer(stage, ("identities read", term), lambda: tuple(read()))
    return _kept_for(stage, ("identities read",), (term,), lambda: tuple(read()))


class _Reached(NamedTuple):
    """What reaching one identity adds to the supporting definitions: the
    objects its declaration denotes, and the terms whose references are
    followed in turn."""

    denoted: tuple
    terms: tuple


def _reached(stage, identity):
    """The `_Reached` of one identity: nothing for an identity the
    definitions table does not hold and for an authored line; for a
    declaration, the objects it denotes, of a distribution the law as written
    alone, and the terms of a function alias and of a derived parameter, of
    each object's expression and of its type. Kept for the version by the
    identity, a name and an identity spelled alike reaching one record."""

    def compute():
        if identity not in stage.definitions:
            return _Reached((), ())
        definition = stage.definitions[identity]
        if definition.kind == "line":
            return _Reached((), ())
        terms = (
            [definition.equations]
            if definition.kind in ("function_alias", "derived_parameter")
            else []
        )
        denoted = (
            _kernel_denoted(stage, definition)
            if definition.kind in ("g", "G")
            else _declared_denoted(stage, definition)
        )
        for item in denoted:
            terms.append(item.expression)
            if item.mathematical_type is not None:
                terms.extend(_semantic_type_parts(item.mathematical_type))
        if definition.kind == "distribution":
            # another record reaches the law as written alone; the measure
            # at the written parameters stands on the distribution's own card
            # alone
            denoted = denoted[:1]
        return _Reached(tuple(denoted), tuple(terms))

    return kept_answer(stage, ("reached", identity), compute)


def _mathematical_parts(answer):
    """Expressions and carriers whose free names a card must resolve."""
    for wire in (*getattr(answer, "inputs", ()), *getattr(answer, "outputs", ())):
        yield wire.expression
        yield wire.definition
        yield from _semantic_type_parts(wire.mathematical_type)
        for rule in (*getattr(wire, "rules", ()), *getattr(wire, "residuals", ())):
            yield from _rule_parts(rule)
    for held in (
        *getattr(answer, "denoted", ()),
        *getattr(answer, "coordinate", ()),
        *getattr(getattr(answer, "kernel", None), "denoted", ()),
        *getattr(answer, "at", ()),
        *getattr(answer, "where", ()),
    ):
        if isinstance(held, Rule):
            yield from _rule_parts(held)
            continue
        yield held.expression
        if held.mathematical_type is not None:
            yield from _semantic_type_parts(held.mathematical_type)
    for held in getattr(answer, "doc", ()):
        yield held.statement
    yield getattr(answer, "expression", None)
    for condition in getattr(answer, "conditions", ()):
        yield condition.entries
    for part in getattr(answer, "pieces", ()):
        yield from _mathematical_parts(part.record)
    for _, part in getattr(answer, "directions", ()):
        if not isinstance(part, str):
            yield from _mathematical_parts(part)


def _semantic_type_parts(mathematical_type):
    """A carrier and the declared set names retained with it."""
    yield mathematical_type.carrier
    yield from (T.Named(name) for name, _ in mathematical_type.declarations)


def _rule_parts(rule):
    """The terms of a `Rule`: its statement, its clauses and the set it
    holds on."""
    yield rule.statement
    yield from rule.where
    yield rule.on


# --- the source text of a line ---


def _authored_text(stage, address):
    """The original excerpt; no equation is reconstructed for a
    source quotation."""
    span = _span_of(stage, address)
    if span is not None:
        quoted = _spanned_lines(stage, span)
        if span.end_column is not None:
            quoted[-1] = quoted[-1][: span.end_column - 1]
        quoted[0] = quoted[0][(span.column or 1) - 1 :]
        return "".join(quoted).rstrip("\r\n")
    definition = stage.definitions.get(address)
    if definition is None:
        return "source not retained [textual]"
    return str(Textual(to_source(definition.equations[0])))


def _authored_header(stage, address):
    """The header of a block as the file writes it: the text between the
    comma after the block's name and the brace that opens its body; the
    block's excerpt where no brace follows the header."""
    span = _span_of(stage, address)
    if span is not None:
        excerpt = "".join(_spanned_lines(stage, span))
        closing = re.search(r"\]\s*\{", excerpt)
        if closing is not None:
            return excerpt[excerpt.index(",") + 1 : closing.start()].strip()
    return _authored_text(stage, address)


def _span_of(stage, address):
    """The source span of an authored item, found by its address or by the
    file and line the address names; None where the version retains no text
    or no span with a line."""
    spans = source_spans(stage)
    span = spans.get(address)
    if span is None:
        span = next(
            (item for item in spans.values() if f"{item.file}:{item.line}" == str(address)), None
        )
    if stage.provenance.get("text") and span is not None and span.line is not None:
        return span
    return None


def _spanned_lines(stage, span):
    """The lines of the version's retained text a span covers, each with its
    line ending: the stage file's text, or an addition's where the span is a
    place in its file."""
    held, _, additions = source_texts(stage)
    text = next((text for text, origin in additions if origin == span.file), held)
    lines = text.splitlines(keepends=True)
    return lines[span.line - 1 : span.end_line or span.line]


# --- the words, the titles and the coordinates of a card ---


def written_at(stage, address):
    """Where an authored item was written,
    `applications/portfolio-choice/declaration/stages/cons/cons.bl:12`, or
    None where the version retains no text. A card prints it beside the term
    address, so that a reader need not count lines (AMD-SG-010 §4)."""
    span = source_spans(stage).get(address)
    if span is None or span.line is None:
        return None
    return f"{span.file}:{span.line}" if span.file else f"line {span.line}"


def _card_coordinate_names(stage, bubble):
    """The coordinates a block or builder is read at: the controls its header
    names, and on a policy block whose header lists no state the coordinates
    its `!doc` line mentions (AMD-SG-015 §6 item 14)."""
    if bubble.name not in {box.name for box in blocks_of(stage)}:
        return ()
    # a builder's box carries no retained header, so the coordinates are read
    # from the block of the same name; the builder is read at the same
    # coordinate as the block it is built from (AMD-SG-015 §4.3)
    block = block_box(stage, bubble.name)
    table = fields(stage)
    named = tuple(
        table[identity]
        for identity in block_coordinates(block, header_wire_sorts(stage))
        if identity in table
    )
    return named or _doc_coordinates(stage, block)


def _doc_coordinates(stage, box):
    """The sorts of the coordinates a policy block is read at, printed from its
    `!doc` line where its header lists no state: a policy header lists the
    value functions alone, and without the `!doc` line the block's card would
    print no argument of the policy (AMD-SG-015 §6 item 14)."""
    table, found = fields(stage), []
    for address in _statements_of_block(stage, box):
        definition = stage.definitions[address]
        if "!doc" not in (getattr(definition, "tags", ()) or ()):
            continue
        for node in term_nodes(definition.equations):
            name = getattr(getattr(node, "symbol", None), "name", None)
            if name is None:
                continue
            for perch in (DECISION, ARRIVAL, CONTINUATION):
                identity = Identity("field", stage=stage.name, perch=perch, field=name)
                sort = table.get(identity)
                if sort is not None and sort.role == "state" and sort not in found:
                    found.append(sort)
    return tuple(found)


def _arrowed(stage, part):
    """The name of a block or a builder with the arrow of its direction
    (AMD-SG-015 §2). A box opened at the sub-builder or the primitive grain is
    rooted at its block's address and takes that block's arrow; a box of no
    block of the stage takes none."""
    name, block = part.name, box_identity(part).block
    try:
        box = block_box(stage, block)
    except TargetError:
        return name
    arrow = block_arrow(stage, box)
    return f"{arrow} {name}" if arrow.strip() else name


def _grain_stamp(grain):
    return sheets.stamp(
        "GRAIN",
        {"builder": "BUILDERS", "node": "SUB-BUILDERS", "primitive": "PRIMITIVES"}.get(
            grain, grain.upper()
        ),
    )


def _statements_of_block(stage, box):
    """The addresses of the authored lines of one block of an initial
    diagram, in file order: the lines of the table the initial diagrams are
    built from (`grains.declared_definitions`), the stage file's lines and
    the lines an addition appends, a solution method's rows left out, since
    they stand in the operative table and in no block of an initial diagram.
    A sub-block is itself one authored line, marked `!node`, and its own
    statement is the line of its name: without it the card of a named
    intermediate quantity does not say what the quantity is."""
    return tuple(
        definition.address
        for definition in declared_definitions(stage).values()
        if definition.kind == "line"
        and (definition.address.split(".", 1)[0] == box.name or definition.address == box.name)
    )


def _coordinate_sorts(stage, box):
    """The sorts of the coordinates a block is read at: the controls its header
    names, and on a policy block whose header lists no state the states its
    `!doc` line mentions (AMD-SG-015 §6 item 14)."""
    table = fields(stage)
    named = tuple(
        table[identity]
        for identity in block_coordinates(box, header_wire_sorts(stage))
        if identity in table
    )
    return named or _doc_coordinates(stage, box)


def _marks(definition):
    """The tags of a record less its descriptions: `id=…`, `!doc`, `!node` and
    any other bare tag, which the card prints under `tags`."""
    return tuple(tag for tag in definition.tags if not (tag.startswith('"') and tag.endswith('"')))


def _line_coordinates(stage, definition, box):
    """The sorts of the controls a line box is read at, where the box reads no
    wire: the coordinates its block's header names that the line's own inputs
    mention (AMD-SG-014 §1). A line whose only field input is such a control
    would otherwise print a card that says it reads nothing. Empty for a line
    box that reads a wire, for a line of no block, and where the card is asked
    of the definitions table rather than of a box."""
    if box is None or box.dom.inside or "." not in definition.address:
        return ()
    block = definition.address.split(".", 1)[0]
    if block not in {b.name for b in blocks_of(stage)}:
        return ()
    coordinates = block_coordinates(block_box(stage, block), header_wire_sorts(stage))
    named = {
        node.symbol.name
        for node in term_nodes(definition.equations)
        if isinstance(node, T.Sym) and getattr(node.symbol, "name", None) is not None
    }
    table = fields(stage)
    return tuple(
        table[identity]
        for identity in coordinates
        if identity.field in named and identity in table
    )
