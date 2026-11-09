"""The questions a stage answers about itself (AMD-SG-006 §5; AMD-SG-007 §3;
AMD-SG-020 §3.1).

Four of them are methods of the stage under the same name: its fields, the
conditions it leaves to be established, the answers of the construction table
and its places; what it denotes is `denotations.denote`. Its parameters and
its settings are the records `parameters_of` and `settings_of` answer, which
the stage's tables `stage.par` and `stage.settings` read, with the tables
they print, `parameter_rows` and `setting_rows`; its places are
`places.places`. The rest are functions of this module and are bound as no
method, because they name a piece the navigation already resolves or have no
reader on the surface (AMD-SG-020 §2, clauses 2 and 4): `kind`, `branches`
and `combination`, which answer from the line records whether a stage
branches, the continuation fields of each branch and how the branches
combine; and the helpers beneath the printed forms. The components within a
graph or a piece are the piece's own `methods`, answered by
`boxes.methods_within` alone. Every answer is derived from the definitions
table, the stored graphs and the bindings; nothing is stored beside them.

A question about one graph is `grains`, about one box `boxes`,
about the kernel a box applies `kernels`.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType
from typing import NamedTuple

from bellman.display.printed_records import (
    Diagnostics,
    Fields,
    Obligations,
    Rows,
    SectionedListing,
)
from bellman.distributions.families import FAMILY_ARGUMENTS
from bellman.fold.block_lines import (
    block_direction,
    blocks_in_file_order,
    blocks_of,
    fields_of,
    header_of,
    header_wire_sorts,
    parameter_sets,
    perches_of,
    require_stage,
    setting_sets,
    transition_between,
    unread_inputs_of,
)
from bellman.fold.conditions import domain_conditions
from bellman.fold.stage_names import StageNames, branches_of, lines_of
from bellman.fold.wire_terms import symbol_occurrences, term_nodes
from bellman.native import predicates as P
from bellman.native.identity import OPERATOR_KINDS, Identity, piece_identity
from bellman.native.records import Condition, Refusal
from bellman.native.versions import StageVersion, kept_answer, stored
from bellman.refusals import METHOD_CONDITIONS, Diagnostic, NotConstructed
from bellman.stage.binding_verbs import calibrated_obligations, calibrated_supports
from bellman.stage.calibration_requirements import calibration_requirements
from bellman.stage.carriers import declared_set_term, law_range_evidence, written_name
from bellman.stage.defining_expressions import (
    bound_point,
    matching_term,
    points_at_policy,
    spelled_condition,
    term_by_reference,
)
from bellman.stage.grains import (
    DIRECTIONS,
    bound_blocks,
    construction_table,
    graph_of,
    stored_graph_name,
    wire_table,
)
from bellman.native.records import setting_names
from bellman.stage.levels import is_declared_version, source_texts
from bellman.stage.method_table import row_of
from bellman.stage.places import components_by_place, components_of_box
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.union import union
from bellman.stage.term_operations import reference_term, relation_of, tuple_term
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    ARRIVAL,
    CONTINUATION,
    DECISION,
    PERCHES,
    PERCH_OF_SIDE,
    SHCK,
    STAGE_BUILDERS,
    VALUE_ROLES,
    WRITTEN_MARK,
)
from bellman.typing import typed_expressions as S
from bellman.typing.line_unknowns import CALL_OPERATORS

# --- the fields ---


def fields(stage):
    """The sort of every field wire by identity, in first-listing order,
    followed by declared shocks not listed in a header, then the multipliers
    the block bodies declare, which no header lists either. The read-only
    mapping prints each field's perch, role and declared set. A shock belongs
    to no perch; its `edges` entry names the edge on which it is drawn.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""
    return Fields(*fields_of(stage))


def field_role(stage, identity):
    """The role of a field wire, read from its sort; None for no such wire."""
    sort = fields(stage).get(identity)
    return sort.role if sort is not None else None


# --- the conditions, in the order they are applied ---


def obligations(stage, level=None, direction=None):
    """The stage's conditions, in first-appearance order, with their sentences,
    statuses and evidence. The answer preserves each condition's identities.

    A symbolic condition remains required unless the construction records an
    assumption or calibration establishes it. Calibration refuses a false
    parameter-only condition; an undecided condition remains required.
    `level` and `direction` restrict the answer to that graph's builders and
    the conditions of the whole stage.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""
    require_stage(stage)
    items = kept_answer(stage, "obligations", lambda: _obligations(stage))
    if level is None:
        return Obligations(items)
    level, direction = stored_graph_name(level, direction)
    try:
        builders = {box.name for box in graph_of(stage, level, direction, "builder").boxes}
    except NotConstructed:
        builders = set()
    blocks = {box.name for box in blocks_of(stage)}

    def owner(item):
        """The block a condition belongs to: the block of the first entry where
        that entry is an identity, and no block otherwise. Every other kind of
        entry — a retained term, the head of an arithmetic operation, a
        predicate, the record of an undeclared set — names no block, and the
        condition is then stage-wide (AMD-SG-017 §4)."""
        first = item.entries[0] if item.entries else None
        if isinstance(first, Identity):
            return first.block or first.stage or ""
        return ""

    # a condition is owned by the block whose name its first identity carries;
    # the two graphs of one direction hold the same blocks, so `level` narrows
    # nothing here and `direction` does the work
    return Obligations(
        item for item in items if owner(item) in builders or owner(item) not in blocks
    )


def _obligations(stage):
    """The stage's conditions in first-appearance order: its symbolic
    conditions, and on a calibrated version the memberships the calibration
    leaves, the conditions made of numeric predicates then decided at the
    values."""
    found = _symbolic_obligations(stage)
    if stage.bindings.calibration is not None:
        for item in calibration_requirements(stage, stage.bindings.calibration):
            found.setdefault((item.condition, item.entries), item)
    if stage.bindings.calibration is not None:
        calibration = stage.bindings.calibration
        decided = calibrated_obligations(stage, found.values(), calibration)
        return calibrated_supports(stage, decided, calibration)
    return tuple(found.values())


def _symbolic_obligations(stage):
    """The conditions of a stage before any calibration, by condition and
    identities, each held once under one owner: the conditions the fold
    records and the domain conditions; a range condition the analysis of
    ranges decides, established with its evidence; each condition written as
    a term where its entries hold one; a push-forward's conservation of mass,
    established where the conditions it rests on are; and, where the stage's
    field relations are incomplete, the condition that the stage supply them.
    A line marked `!doc` declares what the construction is to reach and is
    held on the builder, not among the conditions: no condition states that
    the constructed policy attains it, and none states a hypothesis of
    monotonicity, injectivity, coverage or concavity."""
    found = {}
    for item in (*construction_table(stage).obligations, *domain_conditions(stage)):
        condition, identities = item[0], item[1]
        found.setdefault(
            (condition, identities),
            Condition(
                condition,
                identities,
                status="required",
                explanation=item[2] if len(item) > 2 else "",
            ),
        )
    # the condition each solution method whose rows open a builder requires,
    # under the name its row of the catalogue gives it, required and checked
    # by nothing (specification 0.6 §4.1 and decision 2); a derivative line's
    # condition, `marginal-reading`, is listed by the fold once per line
    # (AMD-MB-001 §4.3; decisions MB-B13)
    for block in bound_blocks(stage):
        if block.condition is not None:
            entries = (piece_identity(block.builder),)
            found.setdefault(
                (block.condition, entries),
                Condition(
                    block.condition,
                    entries,
                    status="required",
                    explanation=METHOD_CONDITIONS[block.condition],
                ),
            )
    # the same condition where a builder's method component names the
    # method and no row of the method is appended (specification 0.7 D8);
    # not on the declared version, which holds the method's construction
    # at no level and whose cards no binding changes (decision SC-13)
    components = () if is_declared_version(stage) else components_by_place(stage).items()
    for place, held in components:
        row = row_of(held.method.name) if held.method is not None else None
        if row is None or row.condition is None or "." in place or "[" in place:
            continue
        entries = (piece_identity(place),)
        found.setdefault(
            (row.condition, entries),
            Condition(
                row.condition,
                entries,
                status="required",
                explanation=METHOD_CONDITIONS[row.condition],
            ),
        )
    ranges = law_range_evidence(stage)
    for key, item in tuple(found.items()):
        if item.condition == "range-compatibility" and len(item.entries) == 3:
            answer = ranges.get(str(item.entries[0]))
            if answer is not None:
                enclosed, evidence = answer
                identities = (item.entries[0], enclosed, item.entries[2])
                found[key] = Condition(
                    condition=item.condition,
                    entries=identities,
                    status="established",
                    evidence=evidence,
                    explanation="The restricted law of motion "
                    "takes values in its declared output set.",
                )
    # every condition a term where its entries hold one (AMD-SG-034 §10 item
    # 5): a range compatibility as the membership of the field the line
    # writes, at the point, in its declared set; an
    # aggregation's admissibility as the membership of each output in its
    # declared set; a definedness condition owned by the piece whose
    # expression holds the power or the division and spelled there;
    # and each condition held once, under one owner
    termed = {}
    for key, item in found.items():
        if item.condition == "aggregation-admissibility":
            for made in _admissibility_terms(stage, item):
                termed[(made.condition, made.entries)] = made
            continue
        if (
            item.condition == "range-compatibility"
            and item.predicate is None
            and len(item.entries) == 3
            and all(isinstance(entry, (T.setexpr, S.Unresolved)) for entry in item.entries[1:])
        ):
            for made in _range_terms(stage, item):
                termed[(made.condition, made.entries)] = made
            continue
        if item.condition == "arithmetic-definedness":
            item = _owned_definedness(stage, item)
        termed[(item.condition, item.entries)] = item
    # the conservation identity of a push-forward into the branches is
    # established where the range condition of every branch line is,
    # and, for a draw, by the law's weights condition
    for key, item in tuple(termed.items()):
        if item.condition != "mass-conservation":
            continue
        subjects = set(item.named_identities[1:])
        drawn = any(subject.kind == "distribution" for subject in subjects)
        open_conditions = [
            held
            for held in termed.values()
            if held.condition
            in ("range-compatibility", "distribution-weights-are-a-probability-vector")
            and held.entries
            and held.entries[0] in subjects
            and held.status != "established"
        ]
        if not open_conditions:
            termed[key] = Condition(
                condition=item.condition,
                entries=item.entries,
                status="established",
                evidence=(
                    (
                        "the weights of the label's law a probability vector"
                        if drawn
                        else "one label per state"
                    ),
                    "the range conditions of the branch lines established",
                ),
                explanation=item.explanation,
            )
    found = _each_condition_once(termed)
    if not diagnostics(stage)["complete_signature"]:
        # the stage as a whole is what this condition is about; the identity
        # record names no stage of its own, so the stage's name is written as
        # the piece it addresses (AMD-SG-017 §4)
        whole = (piece_identity(stage.name),)
        found.setdefault(
            ("partial-field-stage", whole),
            Condition(
                "partial-field-stage",
                whole,
                status="required",
                explanation=f"The stage {stage.name} must supply its missing field relations.",
            ),
        )
    return found


def _admissibility_terms(stage, item):
    """An `aggregation-admissibility` condition as terms, one per output of
    the aggregation: the membership, in the declared set of the output, of
    the output's name at the point where it has one, `𝑉(m_d) ∈ [−∞, ∞)`,
    `𝑚_d≻(a) ∈ Xm`, of the residuals an unnamed input of a solve is made of,
    `(r₁, r₂) ∈ ℝ × ℝ`, and of the output's expression, the coordinates
    free, otherwise, `𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))^(1 − γ) ∈ ℝ₊₊` (AMD-SG-034
    §10 item 5). The item as recorded where the wire table holds no row of
    the aggregation."""
    rendering = wire_table(stage)
    ctx = StageNames(stage)
    identity = item.entries[0]
    rows = tuple(rendering.table.primitive_rows)
    # the condition is recorded at the line's occurrence; the row may be the
    # merge of the occurrences of several lines at the block's address
    row = next((op for op in rows if op.identity == identity), None)
    outputs = tuple(row.outputs) if row is not None else ()
    if row is None:
        row = next(
            (
                op
                for op in rows
                if op.kind == "Aggregation"
                and op.identity.occurrence == identity.occurrence
                and identity.address in op.statements
            ),
            None,
        )
        if row is None:
            return (item,)
        statements = tuple(row.statements)
        outputs = (
            tuple(
                row.outputs[n]
                for n, address in enumerate(statements)
                if address == identity.address
            )
            if len(statements) == len(row.outputs)
            else tuple(row.outputs)
        )

    def declared(output):
        # the declared set of the output: the set the file declares for the
        # field the output is, or the Evaluation names it as; an unnamed
        # output has none, and the set the analysis computed for it says
        # nothing, so no condition is formed
        named = written_name(stage, output)
        if named is None:
            return None
        port = rendering.sort_of(named)
        if getattr(port, "domain", None) is None:
            return None
        return declared_set_term(ctx, port.domain, named)

    # the entries are the identities the fold recorded, the output and the
    # term; the source equations the fold appended are not repeated, since
    # the term holds them resolved and a bare name of a source term encodes
    # by the names in scope
    held = tuple(entry for entry in item.entries if isinstance(entry, Identity))
    made = []
    for output in outputs:
        sort = rendering.sort_of(output)
        target = declared(output)
        if target is None:
            continue
        named = written_name(stage, output)
        point, points = bound_point(ctx, row.identity, sort.coordinates)
        subject = (
            S.Apply(reference_term(named), (tuple_term(points[i] for i in sort.coordinates),))
            if sort.coordinates
            else reference_term(named)
        )
        predicate = P.Member(subject, target)
        made.append(
            Condition(
                condition=item.condition,
                entries=held + (output, predicate),
                status=item.status,
                evidence=item.evidence,
                explanation=item.explanation,
            )
        )
    return tuple(made)


def _range_terms(stage, item):
    """A `range-compatibility` condition as the membership, at the point, of
    the field the line writes in its declared set, `𝑑𝑉≺(m) ∈ (0, ∞]`, one
    item per field the line defines; the inclusion the
    fold recorded is the analysis's evidence and no condition. The item as
    recorded where the line defines no field of the stage."""
    ctx = StageNames(stage)
    first = item.entries[0]
    address = getattr(first, "address", None)
    definition = stage.definitions.get(address) if address is not None else None
    core = definition.equations[0] if definition is not None and definition.equations else None
    core = relation_of(core)
    if not isinstance(core, T.Equation):
        return (item,)
    block = definition.identity.block
    targets = tuple(ctx.defined(core, block))
    if not targets or any(identity not in ctx.ports for identity in targets):
        return (item,)
    declared = item.entries[2]
    evidence = item.evidence
    rendering = wire_table(stage)
    if rendering.direction.get(block) == "forward":
        # a forward field is a coordinate of the next perch, and its
        # membership is of the expression that defines it, the line's right
        # side at the source point, the controls at the policy where the
        # forward row is at one, `m_f − 𝑐(m_f, m_p, w_d) − 𝑐_p(m_f, m_p, w_d)
        # ∈ Xf`
        row = next(
            (
                op
                for op in rendering.table.primitive_rows
                if op.kind == "Pushforward" and address in op.statements
            ),
            None,
        )
        if row is None:
            return (item,)
        source = tuple(row.inputs)
        point, points = bound_point(ctx, row.identity, source)
        local = {**points, **{identity.field: value for identity, value in points.items()}}
        for identity, value in points_at_policy(ctx, row, points).items():
            local[identity] = value
            local[identity.field] = value
        subject = term_by_reference(
            ctx, core.rhs, definition.identity, block, local, declared=True
        )
        return (
            Condition(
                condition=item.condition,
                entries=item.entries + (P.Member(subject, declared),),
                status=item.status,
                evidence=evidence,
                explanation=item.explanation,
            ),
        )
    made = []
    for target in targets:
        states = ctx.coordinates(target.perch, roles=("state",))
        point, points = bound_point(ctx, definition.identity, states)
        x = tuple_term(points[identity] for identity in states)
        subject = (
            S.Apply(reference_term(ctx.function_wire(target)), (x,))
            if states
            else reference_term(ctx.function_wire(target))
        )
        made.append(
            Condition(
                condition=item.condition,
                entries=item.entries + (P.Member(subject, declared),),
                status=item.status,
                evidence=evidence,
                explanation=item.explanation,
            )
        )
    return tuple(made)


def _owned_definedness(stage, item):
    """A definedness condition the fold records on a block, owned by the
    piece whose own terms hold the power or the division and read in that
    piece's spelling, `𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ)) > 0`; the item as
    recorded where no piece holds the node, as on a declared function."""
    first = item.entries[0]
    node = next((entry for entry in item.entries if isinstance(entry, (T.Pow, T.Div))), None)
    if node is None:
        return item
    # the node found the owner; it is held no further, a source term among
    # the entries encoding by the names in scope and not by identity
    without = tuple(entry for entry in item.entries if entry is not node)
    held = Condition(
        condition=item.condition,
        entries=without,
        status=item.status,
        evidence=item.evidence,
        explanation=item.explanation,
    )
    if (
        not isinstance(first, Identity)
        or first.kind not in ("block", "line")
        or item.predicate is None
    ):
        return held
    for row in wire_table(stage).table.primitive_rows:
        realises = (
            row.builder == first.address
            if first.kind == "block"
            else first.address in row.statements
        )
        matched = matching_term(row, node) if realises else None
        if matched is not None:
            # the condition over the row's own term, its inputs by reference:
            # the node's operands are read as the slice holds them
            predicate = spelled_condition(stage, row, _rebased(item.predicate, node, matched))
            identities = (row.identity,) + tuple(
                predicate if entry is item.predicate else entry for entry in without[1:]
            )
            return Condition(
                condition=item.condition,
                entries=identities,
                status=item.status,
                evidence=item.evidence,
                explanation=item.explanation,
            )
    return held


def _rebased(predicate, node, held):
    """The predicate with each operand of `node`, the power or the division
    of the line, replaced by the same operand of `held`, the row's own term
    for it, which reads the row's inputs by their wires."""
    operands = {
        field.name: (getattr(node, field.name), getattr(held, field.name))
        for field in dataclasses.fields(node)
    }
    pairs = [(source, own) for source, own in operands.values() if source != own]

    def rebase(term):
        for source, own in pairs:
            if term == source:
                return own
        if isinstance(term, tuple):
            return tuple(rebase(item) for item in term)
        if (
            dataclasses.is_dataclass(term)
            and not isinstance(term, type)
            and not isinstance(term, Identity)
        ):
            return dataclasses.replace(
                term,
                **{
                    field.name: rebase(getattr(term, field.name))
                    for field in dataclasses.fields(term)
                },
            )
        return term

    return rebase(predicate)


def _each_condition_once(found):
    """The conditions each held once: of two items whose
    terms are one condition, the same term up to the names of its bound
    variables, the one an operation owns is kept, else the first; a
    condition without a term is kept as it is. A condition on a parameter
    read by identity and one on a name a line binds are two conditions,
    however alike they print."""
    kept, owners = {}, {}
    for key, item in found.items():
        if item.predicate is None:
            kept[key] = item
            continue
        text = _condition_key(item.predicate)
        held = owners.get(text)
        first = item.entries[0] if item.entries else None
        operation = isinstance(first, Identity) and first.kind in OPERATOR_KINDS
        if held is None:
            owners[text] = (key, operation)
            kept[key] = item
        elif operation and not held[1]:
            del kept[held[0]]
            owners[text] = (key, operation)
            kept[key] = item
    return kept


def _condition_key(predicate):
    """What makes two terms one condition: their printed form, with each
    name it refers to by what it is, a parameter, a function, a coordinate's
    variable by its field, or a name a line binds; two coordinates' variables
    of one field bound by two operations are one coordinate."""
    references = frozenset(
        (identity.kind, identity.field)
        if isinstance(identity, Identity)
        else ("name", str(identity))
        for identity in S.free_identities(predicate)
    )
    return S.format_expression(predicate, width=None), references


# --- the entry perch, the derivative reads and what a value carries ---


def entry_perch(stage):
    """The perch at which the stage is entered, where a trellis joins the
    previous stage's continuation and the backward value the stage exports
    stands: the arrival perch where a header names it, else the decision
    perch, for a stage that declares no arrival perch (AMD-MB-001 D8 and
    the plan's P2)."""
    perches = {sort.perch for sort in header_wire_sorts(stage).values()}
    return ARRIVAL if ARRIVAL in perches else DECISION


class DerivativeRead(NamedTuple):
    """One derivative term of a value field that a line of the stage reads,
    `D_{a}V[>]` (AMD-MB-001 §§3, 5.3): the `builder` whose row holds it; the
    `value`, the field identity of the value read, with its perch; the
    `coordinates`, the names the term's subscripts write, outermost first,
    one per order of the derivative; and the `term` as the row holds it.
    `spelling` is the term as the amendment writes it."""

    builder: str
    value: Identity
    coordinates: tuple
    term: object

    @property
    def spelling(self):
        return "".join(f"D_{{{name}}}" for name in self.coordinates) + (
            f"{self.value.field}{WRITTEN_MARK[self.value.perch]}"
        )


def derivative_reads(stage):
    """Every derivative term of a value field that a row of the stage's
    operative builders reads, one `DerivativeRead` per distinct term in the
    order of the blocks and their rows (AMD-MB-001 §5.3): the reading a
    block declares, read from the rows and stored nowhere else, from which
    the requirement on the stage that supplies the value is derived
    (`bellman.trellis.derivative_missing`). A derivative of a declared
    function, `D_{c}(𝑢)`, is no reading of a value field and is left out."""
    ports = header_wire_sorts(stage)
    table = construction_table(stage)
    found = []
    for box in blocks_in_file_order(stage):
        for row in table.by_builder(box.name):
            for term in _derivative_terms(row.equations):
                read = _derivative_read(stage, box.name, term, ports)
                if read is not None and read not in found:
                    found.append(read)
    return tuple(found)


def _derivative_terms(node):
    """The outermost derivative operators of a term, in pre-order; the
    operand of one is not entered, so a second derivative is one term."""
    if isinstance(node, T.Operator) and node.head == "D":
        yield node
        return
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        for field in dataclasses.fields(node):
            yield from _derivative_terms(getattr(node, field.name))
    elif isinstance(node, tuple):
        for item in node:
            yield from _derivative_terms(item)


def _derivative_read(stage, builder, term, ports):
    """The `DerivativeRead` of a derivative operator whose operand, under
    its nested derivatives, is a value field of the stage; None for any
    other operand."""
    coordinates, inner = [], term
    while isinstance(inner, T.Operator) and inner.head == "D":
        if len(inner.args) != 1 or len(inner.subs) != 1 or not isinstance(inner.subs[0], T.Var):
            return None
        coordinates.append(inner.subs[0].name)
        inner = inner.args[0]
    if not isinstance(inner, T.Sym):
        return None
    symbol = inner.symbol
    if isinstance(symbol, T.Constant):
        field, perch = symbol.name, DECISION
    elif isinstance(symbol, T.Variable) and isinstance(symbol.when, T.At):
        field, perch = symbol.name, PERCH_OF_SIDE[type(symbol.when.side)]
    else:
        return None
    identity = Identity("field", stage=stage.name, perch=perch, field=field)
    sort = ports.get(identity)
    if sort is None or sort.role not in VALUE_ROLES:
        return None
    return DerivativeRead(builder, identity, tuple(coordinates), term)


def value_carries_derivative(stage, value, coordinates):
    """Whether the value wire `value`, the identity of a function wire the
    stage writes, carries the derivative in `coordinates`, the coordinate
    names of the perch the value stands at, one per order (AMD-MB-001 §3,
    D1 and D6): by a stated line, the Sort's `derivatives` naming the one
    coordinate of a first derivative; or by a representation typed at the
    Evaluation of the builder that writes it, for every object it stores or
    for the value itself, whose row of the catalogue evaluates a derivative
    of that order; or, for an arrival value, by
    the pass-through of a stated derivative of the decision value
    (`_passed_through`; D3 and the plan's P1). The builder that reads the
    derivative knows none of this; the answer is information for the stage
    that writes the value and for the trellis."""
    sort = wire_table(stage).sort_of(value)
    stated = tuple(coordinate.field for coordinate in sort.derivatives)
    if len(coordinates) == 1 and coordinates[0] in stated:
        return True
    table = construction_table(stage)
    written = value.field + WRITTEN_MARK.get(value.perch, "")
    for box in blocks_in_file_order(stage):
        for row in table.by_builder(box.name):
            if row.kind != "Evaluation" or value not in row.outputs:
                continue
            for place, held in components_of_box(stage, row.identity):
                if held.method is None or written not in {obj for _, obj in place.keys}:
                    continue
                row_of_method = row_of(held.method.name)
                if row_of_method is not None and len(coordinates) in row_of_method.derivatives:
                    return True
    upstream = passed_through(stage, value, coordinates) if value.perch == ARRIVAL else None
    return upstream is not None and value_carries_derivative(stage, *upstream)


def value_builder(stage, value):
    """The id of the builder whose Evaluation writes the value wire `value`,
    the identity of a function wire of the stage, or None where no builder of
    the stage writes it."""
    table = construction_table(stage)
    for box in blocks_in_file_order(stage):
        for row in table.by_builder(box.name):
            if row.kind == "Evaluation" and value in row.outputs:
                return box.name
    return None


def evaluation_value_address(stage, value):
    """The written address of the Evaluation of the builder that writes the
    value wire `value`, `<block-id>.evaluate`, at which a representation of
    what the builder stores is typed (AMD-MB-002 §3; specification 0.7 D4);
    the placeholder `<block-id>` stands where no builder of the stage writes
    the value."""
    builder = value_builder(stage, value) if value is not None else None
    return f"{builder or '<block-id>'}.evaluate"


# the perch a value is passed through from, and the two perches of the forward
# block whose lines carry the coordinates between them, by the perch of the
# value passed to (D3, the plan's P1)
_PASSED_FROM = {ARRIVAL: (DECISION, (ARRIVAL, DECISION)), DECISION: (CONTINUATION, (DECISION, CONTINUATION))}


def passed_through(stage, value, coordinates):
    """The value and the coordinates one step upstream within the stage from
    which `value` carries its derivative in `coordinates` by the pass-through
    of AMD-MB-001 D3, as the plan's P1 bounds it, or None where it carries
    none that way: the builder that writes `value` reads one value of the
    perch before, and each of its lines, the Pullback and the Evaluation
    apart, is an identity, an expectation or a scaling by parameters of that
    value, `V[<] = V`, `V[<] = E_{y}V`, `V = β*V[>]`; and the forward block
    between the two perches carries each coordinate by an identity line,
    `a_d = a` or `a[>] = a_d`, so that the derivative in a coordinate of the
    value's perch is, up to the scaling, the derivative of the value read in
    the coordinate so reached. A linear map carries derivatives of every
    order; where the law is not the identity the author writes the line, and
    nothing is differentiated here. An arrival value is passed through from
    the decision value, a decision value from the continuation value, a
    continuation value from nothing."""
    if value.perch not in _PASSED_FROM:
        return None
    earlier, law_perches = _PASSED_FROM[value.perch]
    ports = header_wire_sorts(stage)
    table = construction_table(stage)
    writer = next(
        (
            box
            for box in blocks_in_file_order(stage)
            if any(
                row.kind == "Evaluation" and value in row.outputs for row in table.by_builder(box.name)
            )
        ),
        None,
    )
    if writer is None:
        return None
    values = {
        f"{sort.identity.field}{WRITTEN_MARK[earlier]}": sort.identity.field
        for sort in header_of(writer).inputs
        if sort.role in VALUE_ROLES and sort.identity.perch == earlier
    }
    parameters = set(parameter_sets(stage))
    written, read = f"{value.field}{WRITTEN_MARK[value.perch]}", None
    for row in table.by_builder(writer.name):
        if row.kind in ("Evaluation", "Pullback"):
            continue
        for equation in row.equations:
            if not isinstance(equation, T.Equation) or to_source(equation.lhs) != written:
                return None
            read = _passed_value(equation.rhs, values, parameters)
            if read is None:
                return None
    if read is None:
        return None
    law = _identity_law(stage, ports, table, law_perches)
    mapped = tuple(law.get(name) for name in coordinates)
    if None in mapped:
        return None
    return Identity("function", stage=stage.name, perch=earlier, field=read), mapped


def _passed_value(term, values, parameters):
    """The value a pass-through right side reads, by the field name of the
    spelling in `values`: for `V`, `E_{y}V`, `β*V`, `V*β` or `V/β`, and for
    `V[>]` under the same forms, with the scalings by parameters or numbers
    alone; None for any other term (D3)."""
    if isinstance(term, T.Sym) and isinstance(term.symbol, (T.Constant, T.Variable)):
        return values.get(to_source(term))
    if isinstance(term, T.Operator) and term.head == "E" and len(term.args) == 1:
        return _passed_value(term.args[0], values, parameters)
    if isinstance(term, T.Mul):
        if _is_scalar(term.left, parameters):
            return _passed_value(term.right, values, parameters)
        if _is_scalar(term.right, parameters):
            return _passed_value(term.left, values, parameters)
    if isinstance(term, T.Div) and _is_scalar(term.right, parameters):
        return _passed_value(term.left, values, parameters)
    return None


def _is_scalar(term, parameters):
    """Whether a term is a number or a parameter's name."""
    return isinstance(term, T.Number) or (
        isinstance(term, T.Sym)
        and isinstance(term.symbol, T.Constant)
        and term.symbol.name in parameters
    )


def _identity_law(stage, ports, table, perches):
    """The state of the later of the two `perches` that each coordinate of
    the earlier is carried to by an identity line of the forward block
    between them, `a_d = a` from the arrival to the decision perch or
    `a[>] = a_d` from the decision to the continuation perch, by field name;
    a coordinate the law sends elsewhere has no entry (the plan's P1)."""
    earlier, later = perches
    states = {
        perch: {identity.field for identity, sort in ports.items() if sort.perch == perch and sort.role == "state"}
        for perch in perches
    }
    found = {}
    for box in blocks_in_file_order(stage):
        if perches_of(box, ports) != perches:
            continue
        for row in table.by_builder(box.name):
            for equation in row.equations:
                if not isinstance(equation, T.Equation):
                    continue
                lhs, rhs = equation.lhs, equation.rhs
                if not (
                    isinstance(lhs, T.Sym)
                    and isinstance(lhs.symbol, (T.Constant, T.Variable))
                    and lhs.symbol.name in states[later]
                    and isinstance(rhs, T.Sym)
                    and isinstance(rhs.symbol, (T.Constant, T.Variable))
                    and rhs.symbol.name in states[earlier]
                ):
                    continue
                found.setdefault(rhs.symbol.name, lhs.symbol.name)
    return found


# --- the answers about the completeness of the stage ---


def diagnostics(stage):
    """Nine answers about the completeness of the stage, read from its block
    headers, lines and stored graphs, as a read-only mapping, and a tenth on
    a stage whose lines read a derivative of a value it writes,
    `derivative_missing`.

    `complete_signature` asks whether the declared output relations and both
    chains are present. `missing_builders`, `exposed_inputs` and
    `unused_outputs` name absent relations and unmatched fields.
    `forward_map` names lines without a required forward block;
    `builder_choice` names competing builders. `external_calls` names
    undeclared callables with their source address and arity.
    `unread_inputs` names, for each backward block, the value inputs its
    header lists and no line of the block reads, each a `Diagnostic` in the
    form of the connection diagnostics, under the rule `unread-input`, with
    the block as its address, the input's identity as its one candidate and
    the sentence "the header lists `dV[>]`, which no line of the block
    reads"; the block's builder leaves the input out, and the header is not
    refused (AAS, 17 October 2026). `ready_for_interpretation` requires both
    builders graphs constructed and no external callables.
    `derivative_missing` names each derivative a line reads of a value the
    stage writes, at its decision or its arrival perch, that the value
    carries neither by a stated line nor by a representation whose row
    evaluates it, a `Diagnostic` under the rule `derivative-missing` with
    the reading builder as its address and the value and the coordinates as
    its candidates, information and no refusal.

    A complete stage establishes neither existence, uniqueness nor optimality.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""
    require_stage(stage)
    # the entries are kept as a read-only mapping, which a version made from
    # this one carries as the same class, and the record that prints them is
    # made on return, as `obligations` makes its own
    return Diagnostics(
        kept_answer(stage, "diagnostics", lambda: MappingProxyType(_diagnostics(stage)))
    )


def _diagnostics(stage):
    """The nine answers of `diagnostics`, as a mapping from each answer's
    name to its value, each read by its step from the block headers, the
    lines and the stored graphs."""
    ports = header_wire_sorts(stage)
    blocks = tuple(blocks_in_file_order(stage))
    entry = entry_perch(stage)
    exposed, unused = _unmatched_fields(ports, blocks, entry)
    candidates = _builder_candidates(ports, blocks, entry)
    missing = tuple(pair for pair, found in candidates.items() if not found)
    external = _external_calls(stage)
    forward_map = _forward_map(stage, ports, blocks)
    builder_choice = [
        (choices[0], "builder-choice", ", ".join(choices))
        for choices in candidates.values()
        if len(choices) > 1
    ]
    rendered = _rendered(stage, ports, blocks)
    answers = {
        "complete_signature": not (missing or exposed or unused or forward_map or builder_choice),
        "missing_builders": missing,
        "exposed_inputs": exposed,
        "unused_outputs": unused,
        "forward_map": tuple(forward_map),
        "builder_choice": tuple(builder_choice),
        "external_calls": tuple(external),
        "unread_inputs": _unread_inputs(blocks),
        "ready_for_interpretation": rendered and not external,
    }
    reads = tuple(
        read for read in derivative_reads(stage) if read.value.perch != CONTINUATION
    )
    if reads:
        answers["derivative_missing"] = _derivative_missing(stage, reads)
    return answers


def _derivative_missing(stage, reads):
    """One `Diagnostic` under `derivative-missing` for each derivative a
    line of the stage reads of a value the stage itself writes, at its
    decision or its arrival perch, that the value does not carry
    (`value_carries_derivative`): the reading builder as its address, the
    value's function identity and the coordinates as its candidates, and a
    sentence naming the stage, the term and the value. Information and no
    refusal (AMD-MB-001 §5.3, D6)."""
    found = []
    for read in reads:
        value = Identity(
            "function", stage=stage.name, perch=read.value.perch, field=read.value.field
        )
        if value_carries_derivative(stage, value, read.coordinates):
            continue
        found.append(
            Diagnostic(
                "derivative-missing",
                read.builder,
                f"stage {stage.name!r}: the block {read.builder!r} reads `{read.spelling}`, and "
                f"the value `{read.value.field}{WRITTEN_MARK[read.value.perch]}` carries no "
                f"derivative in {', '.join(read.coordinates)}; state it with a derivative line "
                "of the builder that writes the value, in the stage file or in an addition, or "
                f"type at that builder's Evaluation, `{evaluation_value_address(stage, value)}"
                ".method : …`, a representation whose row of the catalogue evaluates it",
                candidates=(str(value), *read.coordinates),
            )
        )
    return tuple(found)


def _unread_inputs(blocks):
    """One `Diagnostic` under `unread-input` for each value input a backward
    block's header lists and no line of the block reads, in file and header
    order: the block as its address, the input's identity as its one
    candidate, and the sentence naming the input as the file spells it, with
    its perch mark (AAS, 17 October 2026). The inputs are read from the
    retained header of each block (`unread_inputs_of`), since the block's own
    inputs leave them out."""
    found = []
    for box in blocks:
        for sort in unread_inputs_of(box):
            written = f"{sort.identity.field}{WRITTEN_MARK.get(sort.identity.perch, '')}"
            found.append(
                Diagnostic(
                    "unread-input",
                    box.name,
                    f"the header lists `{written}`, which no line of the block reads",
                    candidates=(sort.identity,),
                    write=f"Remove `{written}` from the header, or read it on a line of the block",
                )
            )
    return tuple(found)


def _unmatched_fields(ports, blocks, entry=ARRIVAL):
    """The fields a block reads that no block writes and the stage does not
    receive, and the fields a block writes that no block reads and the stage
    does not deliver, each in port order, shocks apart. A state of a perch at
    which a backward block writes a value field is read by that block as a
    coordinate of the value function, since a backward header lists no state
    (AAS, 12 October 2026), so it is never an unused output. The stage
    receives its fields and delivers its values at `entry`, its entry perch
    (`entry_perch`)."""
    # the inputs and outputs are a question about the authored blocks, so the
    # fields a block reads are its header's, the control it is read at among
    # them (AMD-SG-013 §3)
    inputs = {ob.identity for box in blocks for ob in header_of(box).inputs}
    outputs = {ob.identity for box in blocks for ob in header_of(box).outputs}
    coordinate_perches = {
        ports[i].perch for i in outputs if i in ports and ports[i].role in VALUE_ROLES
    }
    inputs |= {
        i for i, s in ports.items() if s.role == "state" and s.perch in coordinate_perches
    }
    received = {
        i
        for i, s in ports.items()
        if s.perch == entry or (s.perch == CONTINUATION and s.role in VALUE_ROLES)
    }
    delivered = {
        i
        for i, s in ports.items()
        if (s.perch == entry and s.role in VALUE_ROLES)
        or (s.perch == CONTINUATION and s.role == "state")
    }
    exposed = tuple(
        i
        for i, s in ports.items()
        if i in inputs and i not in outputs | received and s.perch != SHCK
    )
    unused = tuple(
        i
        for i, s in ports.items()
        if i in outputs and i not in inputs | delivered and s.perch != SHCK
    )
    return exposed, unused


def _builder_candidates(ports, blocks, entry=ARRIVAL):
    """The blocks that can build each of the four builders of a stage, by
    their pair of perches: the blocks between the two perches that write a
    state forward or a value backward. A stage entered at its decision perch
    has the two builders between its decision and its continuation perch
    alone (AMD-MB-001 D8, P2)."""
    candidates = {}
    for pair in STAGE_BUILDERS:
        if entry != ARRIVAL and ARRIVAL in pair:
            continue
        roles = ("state",) if PERCHES.index(pair[0]) < PERCHES.index(pair[1]) else VALUE_ROLES
        candidates[pair] = [
            box.name
            for box in blocks
            if perches_of(box, ports) == pair
            and any(
                ports[ob.identity].role in roles for ob in box.cod.inside if ob.identity in ports
            )
        ]
    return candidates


def _external_calls(stage):
    """The calls of a function the stage does not declare, each as its
    address, name and number of arguments, in the order of the definitions
    table."""
    ctx = StageNames(stage)
    external = []
    for definition in stage.definitions.values():
        if definition.kind == "distribution":
            law = definition.equations[0].law
            if not isinstance(law, T.Call) or law.fun not in FAMILY_ARGUMENTS:
                continue
            terms = law.args
        elif definition.kind in ("function", "function_alias", "correspondence", "line"):
            terms = definition.equations
        else:
            continue
        for node in term_nodes(terms):
            # a family nested inside an admitted family — the LogNormal
            # component of a Mixture — is the declared distribution algebra,
            # not an external provider (AMD-SG-010 §3)
            if (
                isinstance(node, T.Call)
                and node.fun not in ctx.function_names
                and node.fun not in CALL_OPERATORS
                and node.fun != "Inv"
                and node.fun not in FAMILY_ARGUMENTS
                and node.fun not in ctx.by_name
                and node.fun not in ctx.parameter_names
            ):
                entry = (definition.address, node.fun, len(node.args))
                if entry not in external:
                    external.append(entry)
    return external


def _forward_map(stage, ports, blocks):
    """The lines whose right side reads a field at a later perch than the
    field they define with no chain of forward builders between the two
    perches, each as its address, the rule and the two perches."""
    ctx = StageNames(stage)
    forward_map = []
    for box in blocks:
        perch_from, perch_to = perches_of(box, ports)
        forward = (
            perch_from in PERCHES
            and perch_to in PERCHES
            and PERCHES.index(perch_from) < PERCHES.index(perch_to)
        )
        cod = {ob.identity for ob in box.cod.inside}
        for _, record in lines_of(stage, box):
            core = record.core
            equation = relation_of(core)
            defined = ctx.defined(equation, box.name)
            left = defined[0].perch if defined else None
            if left not in PERCHES:
                continue
            direct = (
                frozenset((perch_from, perch_to))
                if forward and defined[0] in cod and ports[defined[0]].role == "state"
                else frozenset()
            )
            for name, side in symbol_occurrences(equation.rhs):
                perch = ctx.resolve(name, box.name, side).perch
                if perch not in PERCHES or perch == left or perch in direct:
                    continue
                if PERCHES.index(perch) > PERCHES.index(left) and not _chained(
                    stage, left, perch, ports
                ):
                    entry = (record.address, "forward-map", f"{left} -> {perch}")
                    if entry not in forward_map:
                        forward_map.append(entry)
    return forward_map


def _chained(stage, perch_from, perch_to, ports):
    """Whether a forward builder joins each pair of adjacent perches from one
    perch to a later one."""
    start, end = PERCHES.index(perch_from), PERCHES.index(perch_to)
    return all(
        transition_between(stage, PERCHES[i], PERCHES[i + 1], ports) is not None
        for i in range(start, end)
    )


def _rendered(stage, ports, blocks):
    """Whether both builders graphs are constructed: both directions have a
    block, every block has a direction and neither builders graph was
    refused; a `WorkingStage` holds no stored graph yet, a `StageVersion` holds
    the four."""
    directions, refused = set(), False
    for box in blocks:
        try:
            directions.add(block_direction(stage, box, ports))
        except NotConstructed:
            refused = True
    record = stored(stage, "_builders") if isinstance(stage, StageVersion) else None
    return (
        record is not None
        and not refused
        and set(DIRECTIONS) <= directions
        and not any(isinstance(getattr(record, direction), Refusal) for direction in DIRECTIONS)
    )


# --- the parameters, the settings and the places ---

# the value of a parameter that no calibration binds, and of its record
UNBOUND = "unbound"


class Parameter(NamedTuple):
    """One parameter of a version, `stage.par["ρ"]`: its `name` as the file
    declares it, its declared set `domain`, a retained term or None where no
    declaration names one, its `value`, the number a calibration binds or the
    word `unbound`, and the author's description `describes`. It prints as
    one line, `ρ = 6.0 : [1, inf)`, or `ρ : [1, inf), unbound`.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §1."""

    name: str
    domain: object
    value: object
    describes: str

    def __str__(self):
        declared = "" if self.domain is None else f" : {to_source(self.domain)}"
        if isinstance(self.value, str) and self.value == UNBOUND:
            return f"{self.name}{declared}, {UNBOUND}"
        return f"{self.name} = {self.value!r}{declared}"

    __repr__ = __str__


class Setting(NamedTuple):
    """One setting of a version, `stage.settings["n_a"]`: its `name`; its
    `domain`, the set its declaration in the methods file names, None for a
    setting no file declares; its configured `value`, or `unbound` where no
    configuration has valued it; and `readers`, the triples of the place
    that reads it, the method word there and the kind of the grid where the
    setting is a bound or a count of a factor of the grid typed at that
    place, `("policy", "!egm", "!Cartesian")`, the kind empty otherwise,
    `("dcsn_to_arvl.E_ψ_ξ", "!gauss_hermite", "")`; `readers` is empty for
    a setting no component names. It prints as one line,
    `n_a = 960 : ℕ, read at policy by !egm for its grid !Cartesian`
    (AMD-MB-003 §3; specification 0.7 D5).

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §2."""

    name: str
    value: object
    readers: tuple
    domain: object = None

    def __str__(self):
        read = "; ".join(
            f"{place} by {by}" + (f" for its grid {grid}" if grid else "")
            for place, by, grid in self.readers
        )
        declared = "" if self.domain is None else f" : {to_source(self.domain)}"
        if isinstance(self.value, str) and self.value == UNBOUND:
            return f"{self.name}{declared}, {UNBOUND}" + (f", read at {read}" if read else "")
        return f"{self.name} = {self.value!r}{declared}" + (f", read at {read}" if read else "")

    __repr__ = __str__


def parameters_of(stage):
    """Every parameter of the version by the name the file declares, in
    declaration order, each its `Parameter` record: the declaration the
    definitions table holds for it and the value the calibration bound in the
    version's bindings, which is all a parameter is. Computed at each call and
    kept nowhere.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §1."""
    require_stage(stage)
    values = stage.bindings.calibration
    found = {}
    for definition in stage.definitions.values():
        if definition.kind != "parameter":
            continue
        name = definition.identity.field
        found[name] = Parameter(
            name=name,
            domain=definition.equations[0] if definition.equations else None,
            value=values[name] if values is not None and name in values else UNBOUND,
            describes="; ".join(descriptions(definition)),
        )
    return found


def parameter_rows(stage):
    """The parameters in declaration order, as read-only rows with `name`,
    `domain`, `value` and `describes`, the table `stage.par` prints. The
    retained declared set is `domain`, printed under `set`; a missing
    declaration is None. The value is the bound calibration value or
    `unbound`. The description is the author's text.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §1."""
    return Rows(
        [MappingProxyType(record._asdict()) for record in parameters_of(stage).values()],
        {"domain": "set"},
    )


def descriptions(definition):
    """The descriptions an author wrote on a record, without their quotation
    marks: the quoted entries of its tags, which a card prints under
    `describes` (AMD-SG-014 §§1, 3). A parameter, a shock and a line each
    carry theirs the same way, and so do a set, a function alias, a function
    and a correspondence (AMD-SG-017 §3); the `tags` line of a card that
    prints one carries the marks alone."""
    return tuple(tag[1:-1] for tag in definition.tags if tag.startswith('"') and tag.endswith('"'))


def settings_of(stage):
    """Every setting of the version, each its `Setting` record: first the
    settings the methods file declares, in declaration order, each with its
    declared set and the value configured in `stage.bindings.settings` or
    `unbound`; then the names a configuration bound that no file declares,
    in binding order. Each record lists the places whose components name
    the setting (`settings_readers`). A setting is listed here and never
    among the parameters (specification 0.7, S1). Computed at each call and
    kept nowhere.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §2."""
    require_stage(stage)
    readers = settings_readers(stage)
    values = stage.bindings.settings or {}

    def record(name, domain):
        return Setting(
            name=name,
            value=values[name] if name in values else UNBOUND,
            readers=tuple(
                (
                    place,
                    held.word or (f'"{held.handler}"' if held.handler else ""),
                    _grid_of_setting(held, name),
                )
                for place, held in readers.get(name, ())
            ),
            domain=domain,
        )

    found = {name: record(name, domain) for name, domain in setting_sets(stage).items()}
    found.update({name: record(name, None) for name in values if name not in found})
    return found


def settings_readers(stage):
    """The places whose components name each setting, by setting name: for
    each name a keyword argument of a method word or a factor of a grid
    writes, the pairs of the place and its `Components`, in the order of the
    places (`records.setting_names`)."""
    found = {}
    for place, held in components_by_place(stage).items():
        for name in dict.fromkeys(setting_names(held)):
            found.setdefault(name, []).append((place, held))
    return found


def _grid_of_setting(held, name):
    """The kind of the grid typed at a place, `!Cartesian`, where the
    setting `name` is a bound or a count of one of its factors; the empty
    text otherwise (specification 0.7 D5)."""
    return "!Cartesian" if held.grid is not None and name in set(setting_names(held.grid)) else ""


def setting_rows(stage):
    """The settings of this version, the declared ones first, the table
    `stage.settings` prints.

    A setting has one read-only row per method reader, with its declared set
    under `set`, its value or the word `unbound`, and the kind of the grid
    under `grid` where the setting is a factor of the place's grid. A
    setting with no reader remains in the listing with empty `read at`, `by`
    and `grid` entries.

    See `docs/Bellman-Sym/API/stage/06-par-and-settings.md` §2."""
    return Rows(
        [
            MappingProxyType(
                {
                    "name": record.name,
                    "domain": record.domain,
                    "value": record.value,
                    "read at": at,
                    "by": by,
                    "grid": grid,
                }
            )
            for record in settings_of(stage).values()
            for at, by, grid in record.readers or (("", "", ""),)
        ],
        {"domain": "set"},
    )


# --- the listing, the branches and the source spans ---


def stage_listing(stage):
    """What is inside a stage, which `stage.list()` answers, under two
    headings, the attributes that reach it: under `initial`, each block of
    the two initial diagrams by its name with its kind and direction; under
    `builder`, each builder by its block identifier with the pair of perches
    it joins, or `policy`, and its direction word, the listing that
    `stage.builder.list()` answers."""
    return SectionedListing({"initial": stage.initial.list(), "builder": stage.builder.list()})


def kind(stage):
    """The kind of the stage, read from its blocks (AMD-SG-006 §5):
    `branching` when a builder's outputs are split by branch labels,
    `standard` otherwise. The word the step that orders the stages of a
    period reads."""
    return "branching" if branches(stage) else "standard"


def branches(stage):
    """The branches of a branching stage, each label to the continuation
    fields its nested block writes; empty for a stage without branches."""
    require_stage(stage)
    found = {}
    for box in blocks_of(stage):
        found.update(branches_of(stage, box))
    return MappingProxyType(found)


def combination(stage):
    """How the branches of a stage combine: `choice` where the selection
    tuples of its lines are indexed by a control, `expectation` where by a
    declared shock, None for a stage without branches; read from the key of the
    retained `Select` terms, never from source text."""
    labels = tuple(branches(stage))
    if not labels:
        return None
    ctx = StageNames(stage)
    for definition in stage.definitions.values():
        if definition.kind != "line":
            continue
        for node in term_nodes(definition.equations[0]):
            if (
                isinstance(node, T.Select)
                and isinstance(node.family, T.Tuple)
                and len(node.family.items) == len(labels)
                and isinstance(node.sel, T.Key)
                and isinstance(node.sel.at, str)
            ):
                role = ctx.role(ctx.resolve(node.sel.at, definition.identity.block))
                return {"control": "choice", "shock": "expectation"}.get(role)
    return None


def source_spans(stage):
    """The source span of every authored item of the version, by address: the
    file, line and column it was written at, in the stage file or in an
    addition. After the authored items, the mapping holds the place of each
    side of a block header, each field the side lists, each component of
    that field's typing and each typing entry of the header (unit T of the
    model interface specification 0.3, the classification table). Parsed
    once per version from the texts its provenance retains, the stage file's
    with its additions unioned (`bellman.syntax.union`), and empty for a stage
    built from a term whose text the provenance does not hold. Nothing is
    stored on the stage."""

    def compute():
        text, origin, additions = source_texts(stage)
        if not text:
            return {}
        if additions:
            unioned = union(
                parse_with_spans(text, filename=origin),
                [parse_with_spans(held, filename=where) for held, where in additions],
            )
            return dict(unioned.spans)
        return dict(parse_with_spans(text, origin).spans)

    return kept_answer(stage, "spans", compute)
