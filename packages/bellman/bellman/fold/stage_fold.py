"""The fold of a stage (AMD-SG-004 and AMD-SG-005).

One pass over the statements of a stage file produces, for each builder, the
operators of Appendix C R7 that the builder is composed of, and the
definitions table: every authored definition (a set, a distribution, a
function, a correspondence, a forward builder's g, a backward builder's G) and
every authored line, once, as `Definition` records. `fold_stage_file` folds a
parsed file during construction; `fold_stage` folds the constructed stage
again, so that a query that needs a row's reading of a box, its bound
coordinates, the statements it realizes or its map reads the same fold.
`_StageBlocks` is the stage as one fold reads it: the blocks with their
directions and lines, the definitions table, the retained statements by
address, the laws of motion of the forward blocks, the edges on which the
shocks are drawn and the branches of a branching block.
`_construction_table` composes the steps: the conditions of the definitions,
of the lines and of the laws of motion and aggregators, the plan, the
conditions of the shock distributions, and the rows of each block
(`block_rows_of`). The rows of a forward block are its `Pushforward` and
`DistributionExtension` under the law of motion, whose equations
`law_of_motion_equations` writes with the local names substituted.

Wires. A backward wire carries either a function or a set of functions: a
value function `<stage>:function:<perch>:<field>`, its composition with g
`…:g`, an occurrence's result `<address>:Expectation:<n>:result`, an inside
aggregation's result `<address>:Aggregation:<n>:result`, a sub-builder's named
output, a policy function, the set of policies a selection returns, or a
function a policy line defines on the continuation states. A state, a control
or a shock written in an equation is a bound argument of the functions an
operator defines, never an input (Appendix C R5). The forward view's
wires are measures. Parameters are named inside the terms.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from bellman.distributions.edges import drawn_edges, factorization_obligation, joint_distribution
from bellman.distributions.families import (
    NORMAL,
    bernoulli_probability,
    check_family_conditions,
    check_real_parameter_shapes,
    check_weights,
    parameter_condition,
    product_law,
    weight_matrix_text,
    weights_condition,
    weights_of,
)
from bellman.fold.backward import fold_backward_block
from bellman.fold.block_lines import (
    block_direction,
    blocks,
    header_wire_sorts,
)
from bellman.fold.declared_sets import REAL, check_declared_sets, subject_dimension
from bellman.fold.derived_parameters import derived_order
from bellman.fold.policy import fold_policy_block
from bellman.fold.stage_names import (
    StageNames,
    branches_of,
    family_term_arguments,
    label_coordinate,
    lines_of,
)
from bellman.fold.table import BlockRows, ConstructionTable, OperatorRow
from bellman.fold.wire_terms import (
    path_text,
    coordinate_declared_set,
    defined_name,
    expectation_occurrences,
    external_calls,
    header_identities,
    right_side,
    spelled_with_mark,
    statement_core,
    symbol_occurrences,
    wire_identities,
)
from bellman.native.identity import Identity, piece_identity
from bellman.native.predicates import Member
from bellman.native.records import Definition
from bellman.native.versions import StageVersion
from bellman.refusals import ConstructionError, NotConstructed, construction_error, location
from bellman.syntax import terms as T
from bellman.syntax.lower import file_position, item_addresses
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import DOC, VALUE_ROLES
from bellman.typing.category_codes import (
    CategoryCodesFault,
    category_codes,
    coded_meaning,
    reserved_entries,
)
from bellman.syntax.union import is_typing_entry
from bellman.typing.declarations import (
    TOP_LEVEL,
    derived_parameter_body,
    derived_parameter_declaration,
)
from bellman.typing.line_unknowns import selection_positions
from bellman.typing.sets import defined, index_factors

# --- the entry points and the driver ---


def fold_stage_file(term, stage, spans=None) -> ConstructionTable:
    """One traversal of the statements of ``term`` (the parsed stage file) with
    the names of the working ``stage`` (`StageNames`): the definitions table in
    file order, the rows of every builder, and the obligations the conditions
    raise. `spans` is the source-span table of the parse, from which the record
    of a top-level item takes its file position (AMD-SG-017 §4); None for a
    term decoded from a saved AST, which carries no positions. `fold_stage` is
    the same fold of a constructed stage, read from its table in place of the
    term."""
    ctx = StageNames(stage)
    definitions = _definitions_of(term, ctx, stage, spans)
    # the rows are folded with the functions, sets and multipliers the
    # definitions table holds, the context the re-fold of the constructed
    # stage reads; the construction records no obligation, since nothing of
    # the construction reads one and the queries derive them from the
    # version's table
    return _construction_table(stage, StageNames(stage, definitions), definitions)


def fold_stage(stage) -> ConstructionTable:
    """The construction table of a constructed stage, folded again from its
    definitions table and its blocks (AMD-SG-006 §5): the rows of every
    builder and the obligations of the definitions and the lines, by the one
    fold that produced them at construction."""
    definitions = tuple(stage.definitions.values())
    return _construction_table(stage, StageNames(stage, definitions), definitions)


def _construction_table(stage, ctx, definitions) -> ConstructionTable:
    """The rows of every builder and the obligations of a stage from its
    definitions table: the definedness conditions of the arithmetic of the
    function bodies, the lines, the g and the G (`finite-real-arithmetic`),
    the external callables the laws and the lines name, then the rows of each
    block. At construction, where `stage` is the `WorkingStage`, the declared
    sets of a field produced by one block and consumed by another are compared
    as well (`check_declared_sets`); the obligations are returned on a
    `StageVersion` alone."""
    # the conditions are read at every fold, since reading them refuses a
    # written form the rules do not admit; the obligations they leave are
    # returned for a constructed stage alone
    obligations = []
    table = {d.identity: d for d in definitions}
    _definition_obligations(ctx, definitions, obligations)
    blocks, directions, lines = _blocks_of(stage)
    _line_obligations(ctx, blocks, lines, table, obligations)
    _law_obligations(ctx, blocks, table, obligations)
    plan = _StageBlocks(
        ctx=ctx,
        blocks=blocks,
        directions=directions,
        definitions=tuple(definitions),
        lines=lines,
        items=_retained_statements(blocks, lines, table),
    )
    # the distribution checks refuse a declaration the rules do not
    # admit at construction; the obligations they leave are read on
    # the constructed stage
    _distribution_obligations(plan, obligations)
    operations, closed = [], {}
    for box in blocks:
        rows = block_rows_of(plan, box, obligations)
        operations.extend(rows.primitive)
        if rows.sub_builder is not rows.primitive:
            closed[box.name] = tuple(rows.sub_builder)
    constructed = isinstance(stage, StageVersion)
    if not constructed:
        # the controls the lines marked `!doc` select, whose feasible sets are
        # the inclusions to establish (AMD-SG-034 §11 item 1: the line forms
        # no piece, so the selected controls are read from the lines); the
        # check refuses a mismatch, and the inclusions it would record go
        # with the construction's other obligations, which nothing reads
        check_declared_sets(stage, obligations, _selected_controls(ctx, blocks, lines, table))
    return ConstructionTable(
        stage=ctx.stage_name,
        definitions=_definitions_used(ctx, blocks, definitions, operations),
        primitive_rows=tuple(operations),
        obligations=tuple(dict.fromkeys(obligations)) if constructed else (),
        sub_builder_rows=tuple(closed.items()),
    )


def _definition_obligations(ctx, definitions, obligations):
    """The conditions of the body of every function and correspondence; for
    each derived parameter, only where the declared sets leave its
    definition open or the definition calls log or exp, the one obligation
    that its value is a finite real number (`_derived_definedness`); and an
    obligation for each external callable a distribution declaration
    names."""
    for d in definitions:
        if d.kind in ("function", "correspondence"):
            ctx.conditions(
                (d.equations[0].body,), obligations, d.identity, local=dict(d.coordinates)
            )
        elif d.kind == "derived_parameter":
            # the conditions of the definition's arithmetic are read only to
            # learn whether the declared sets leave one open, as a call of log
            # or exp always does; none of them is recorded, so that a clause
            # drawn from the declared sets alone, such as a positive base for
            # a power whose exponent's set holds a noninteger, refuses no
            # value the definition takes (AMD-MT-003, build contract §5)
            held = []
            ctx.conditions((d.equations[0],), held, d.identity)
            if held or external_calls(d.equations[0], ctx.function_names):
                obligations.append(_derived_definedness(d))
        elif d.kind == "distribution":
            for call in external_calls(d.equations[0].law, ctx.function_names, distributions=True):
                # the place is the record's identity, as it is on every other
                # obligation; the record's address is the file position of the
                # declaration, `<path>:<line>`, which names where it is written
                # and not what it is (AMD-SG-014 §3; AMD-SG-017 §4)
                obligations.append(
                    (
                        "external-callable-signature-and-provider",
                        (Identity("external", field=call), d.identity),
                        f"The callable {call} used by {d.identity} "
                        f"needs a declared signature and provider.",
                    )
                )


def _derived_definedness(definition):
    """The obligation a derived parameter owns, `h ∈ ℝ`: its value is a
    finite real number, which states every condition of its definition's
    arithmetic and calls at once. It is `arithmetic-definedness` on the
    derived parameter's identity, with the empty scope of a condition read
    outside every binder. The calibration reads it at the value the
    definition takes there (`derived_parameters.derived_values`), so that it
    is established wherever the definition has a value, and a definition
    without one has been refused under `derived-parameter` at that
    definition before any obligation is read (AMD-MT-003, build contract
    §5). The set a definition declares, `q : (0,1) := (β*R)^(1/ρ)/R`, is no
    part of this obligation: calibration judges the value against it with
    the declared sets of the parameters (`calibration_requirements`)."""
    name = definition.identity.field
    return (
        "arithmetic-definedness",
        (definition.identity, Member(T.Sym(T.Constant(name)), REAL)),
        f"The derived parameter {name}, defined as `{to_source(definition.equations[0])}`, "
        "must have a finite real value at the calibration.",
        (),
    )


def _line_obligations(ctx, blocks, lines, table, obligations):
    """The conditions of every line but a line marked `!doc`, and an
    obligation for each external callable the line names."""
    for box in blocks:
        for _, record in lines[box.name]:
            if record.role == DOC:
                continue
            core = table[record.address].equations[0]
            # a line's conditions are recorded on the line, so that two
            # occurrences of one term on two lines are two conditions,
            # each owned by the piece realizing its line
            ctx.conditions((core,), obligations, piece_identity(record.address), block=box.name)
            for call in external_calls(core, ctx.function_names):
                obligations.append(
                    (
                        "external-callable-signature-and-provider",
                        (Identity("external", field=call), piece_identity(record.address)),
                        f"The callable {call} used at {record.address} "
                        f"needs a declared signature and provider.",
                    )
                )


def _law_obligations(ctx, blocks, table, obligations):
    """The conditions of each block's retained law of motion g or aggregator
    G, recorded on the line that holds each equation."""
    for box in blocks:
        owned = table.get(Identity("g", stage=ctx.stage_name, address=box.name)) or table.get(
            Identity("G", stage=ctx.stage_name, address=box.name)
        )
        if owned is not None:
            for a in owned.equations:
                ctx.conditions(
                    (table[a].equations[0],), obligations, piece_identity(a), block=box.name
                )


def _retained_statements(blocks, lines, table):
    """The retained statement of every line of the blocks, by its address."""
    return {
        record.address: T.Statement(table[record.address].equations[0])
        for box in blocks
        for _, record in lines[box.name]
    }


def _selected_controls(ctx, blocks, lines, table):
    """The controls the lines marked `!doc` select."""
    return {
        identity
        for box in blocks
        for _, record in lines[box.name]
        if record.role == DOC
        for identity in ctx.defined(table[record.address].equations[0], box.name)
    }


def _definitions_used(ctx, blocks, definitions, operations):
    """The definitions table without the G of a block that writes a control
    and that no aggregation row references."""
    policy_G = {
        Identity("G", stage=ctx.stage_name, address=box.name)
        for box in blocks
        if any(ctx.role(i) == "control" for i in wire_identities(box.cod))
    }
    used_G = {op.definition for op in operations if op.kind == "Aggregation"}
    return tuple(d for d in definitions if d.identity not in policy_G or d.identity in used_G)


def block_rows_of(plan, box, obligations) -> BlockRows:
    """The rows of one block at the primitive and the sub-builder grain: for a
    forward block its `DistributionExtension` rows, its `Pushforward` under the
    law of motion and, for a branching block, the obligation that the masses of
    the branches sum to the mass pushed forward; for a backward block the fold
    of the policy block where it writes a control and of a value block
    otherwise; none for a block no directional rule reads."""
    ctx, block = plan.ctx, box.name
    direction = plan.directions[block]
    if direction is None:
        return BlockRows(primitive=(), sub_builder=())
    dom, cod = header_identities(box)
    records = [record for _, record in plan.lines[block]]
    items = plan.items
    if direction == "forward":
        rows = []
        gid = plan.g_identity[block]
        lines = [(record.address, items[record.address]) for record in records]
        cores = tuple(statement_core(stmt) for _, stmt in lines)
        edge = plan.edges.get(block)
        controls = tuple(i for i in dom if ctx.role(i) == "control")
        policies = tuple(
            Identity("function", stage=ctx.stage_name, perch=c.perch, field=c.field)
            for c in controls
        )
        for owner in edge.declarations if edge is not None else ():
            rows.append(
                OperatorRow(
                    Identity(
                        "DistributionExtension", address=block, subjects=tuple(owner.subjects)
                    ),
                    kind="DistributionExtension",
                    builder=block,
                    direction="forward",
                    statements=(),
                    inputs=tuple(
                        Identity("field", stage=ctx.stage_name, perch="shck", field=s)
                        for s in owner.subjects
                    ),
                    outputs=(Identity("distribution-extended-measure", address=block),),
                    references=(owner.identity,) + policies,
                    distribution=owner.identity,
                    equations=(owner.term,),
                    policy=policies,
                )
            )
        rows.append(
            OperatorRow(
                Identity("Pushforward", address=block),
                kind="Pushforward",
                builder=block,
                direction="forward",
                statements=tuple(a for a, _ in lines),
                inputs=dom,
                outputs=cod,
                references=(gid,) + policies,
                parameters=ctx.parameters(cores),
                definition=gid,
                equations=cores,
                policy=policies,
                conditions=ctx.conditions(cores, obligations, block, block=block),
            )
        )
        if block in plan.labels:
            # the conservation identity of a push-forward into the branches:
            # its subjects the row, the law of a drawn label and the branch
            # lines, whose weights and ranges establish it; no card prints it
            key = label_coordinate(ctx.stage_object, box)
            drawn = (
                edge.declaration_of(key.field)
                if edge is not None and ctx.role(key) == "shock"
                else None
            )
            routing = (
                f"the distribution of {key.field} gives the labels probabilities that sum to one"
                if drawn is not None
                else "the policy sends every decision state to one label"
            )
            obligations.append(
                (
                    "mass-conservation",
                    (Identity("Pushforward", address=block),)
                    + ((drawn.identity,) if drawn is not None else ())
                    + tuple(Identity("line", address=a) for a, _ in lines),
                    f"The masses of "
                    f"{', '.join('μ_' + label + '≻' for label in plan.labels[block])} sum to the "
                    f"mass of μ: {routing}, and every line of a branch writes a value in the "
                    f"declared set of its field.",
                )
            )
        return BlockRows(primitive=rows, sub_builder=rows)
    if any(ctx.role(i) == "control" for i in cod):
        return fold_policy_block(
            plan,
            block,
            records,
            dom,
            cod,
            obligations,
            transition=plan.g_identity.get(plan.forward_by_target.get("cntn")),
        )
    return fold_backward_block(plan, block, records, dom, cod, obligations)


def stage_blocks_of(stage):
    """The plan of a constructed stage, read from its definitions table and
    its blocks."""
    ctx = StageNames(stage)
    blocks, directions, lines = _blocks_of(stage)
    table = dict(stage.definitions)
    return _StageBlocks(
        ctx=ctx,
        blocks=blocks,
        directions=directions,
        definitions=tuple(table.values()),
        lines=lines,
        items=_retained_statements(blocks, lines, table),
    )


@dataclass(kw_only=True)
class _StageBlocks:
    """What the fold of one block reads of the whole stage. Given: the names
    of the stage (`ctx`), the blocks in file order, the direction of each
    (`directions`), the definitions table, each block's lines and the retained
    statements by address (`items`). Derived from them: the forward builder
    that produces each perch (`forward_by_target`) and the identity of each
    forward builder's g (`g_identity`); the owners of the shocks (`owners`),
    those owners in dependency order (`ordered`) and the edge each forward
    builder draws its shocks on (`edges`); and the fields of each branch's
    section by (block, label) (`sections`), the labels of each branching block
    (`labels`) and the (block, label) whose section each continuation value
    is pulled back along (`bases`)."""

    ctx: object
    blocks: tuple
    directions: dict
    definitions: tuple
    lines: dict
    items: dict

    def __post_init__(self):
        self.forward_by_target, self.g_identity = _forward_blocks(
            self.ctx, self.blocks, self.directions
        )
        self.owners, self.ordered, self.edges = _forward_edges(
            self.ctx, self.blocks, self.directions, self.definitions
        )
        self.sections, self.labels, self.bases = _branches(
            self.ctx, self.blocks, self.directions, self.lines, self.items
        )

    def distributions_of(self, shocks):
        """The owners of the given shocks, in dependency order."""
        return tuple(owner for owner in self.ordered if set(owner.subjects) & set(shocks))

    def definition(self, identity):
        """The record of the definitions table with this identity, or None."""
        return next((d for d in self.definitions if d.identity == identity), None)

    def law_of_motion(self, block):
        """The law of motion g of a forward builder as the fold reads it: its
        identity, the block's inputs and outputs, and the retained terms of
        its lines, resolved from the line identities its record holds."""
        box = next(b for b in self.blocks if b.name == block)
        record = self.definition(self.g_identity[block])
        inputs, outputs = header_identities(box)
        return _LawOfMotion(
            identity=record.identity,
            inputs=inputs,
            outputs=outputs,
            equations=law_of_motion_equations(
                self.ctx,
                block,
                tuple(statement_core(self.items[address]) for address in record.equations),
            ),
        )


def _forward_blocks(ctx, blocks, directions):
    """The forward builder that produces each perch, by the perch of its first
    output, and the identity of the g of each forward builder."""
    by_target, g_identity = {}, {}
    for box in blocks:
        if directions[box.name] == "forward":
            cod = wire_identities(box.cod)
            by_target[cod[0].perch if cod else None] = box.name
            g_identity[box.name] = Identity("g", stage=ctx.stage_name, address=box.name)
    return by_target, g_identity


def _forward_edges(ctx, blocks, directions, definitions):
    """The owners of the shocks, the owners in dependency order, and the edge
    each forward builder draws its shocks on (AMD-SG-009 §2)."""

    def refuse(rule, address, message, related=(), write=None):
        # `related` pairs each second item's role with its address
        raise ConstructionError(
            message,
            stage=ctx.stage_name,
            address=address,
            rule=rule,
            related=tuple(location(role, address=at) for role, at in related),
            write=write,
        )

    subjects = {
        s for d in definitions if d.kind == "distribution" for s in d.equations[0].subjects
    }
    forward = tuple(
        (box.name, tuple(i.field for i in header_identities(box).inputs if ctx.role(i) == "shock"))
        for box in blocks
        if directions[box.name] == "forward"
    )
    owners, ordered, assignment = drawn_edges(
        definitions,
        lambda name: name in subjects
        or ctx.role(Identity("field", stage=ctx.stage_name, perch="shck", field=name)) == "shock",
        forward,
        refuse,
    )
    edges = {}
    for box in blocks:
        if directions[box.name] == "forward":
            dom = header_identities(box).inputs
            base = tuple(i for i in dom if ctx.role(i) == "state") + tuple(
                i for i in dom if ctx.role(i) == "control"
            )
            edges[box.name] = joint_distribution(
                block=box.name,
                base=base,
                in_file_order=owners,
                in_dependency_order=ordered,
                shock_edges=assignment,
            )
    return owners, ordered, edges


def _branches(ctx, blocks, directions, lines, items):
    """The branches of each forward block and the base of each value its
    selection tuples read, from the blocks and the retained lines and never
    stored: the fields of each section by (block, label), the labels of each
    branching block, and the (block, label) whose section each continuation
    value is pulled back along."""
    sections, labels, bases = {}, {}, {}
    entries = [
        (record.address, statement_core(items[record.address]))
        for held in lines.values()
        for _, record in held
    ]
    for box in blocks:
        found = branches_of(ctx.stage_object, box) if directions[box.name] == "forward" else ()
        if not found:
            continue
        labels[box.name] = tuple(label for label, _ in found)
        sections.update(((box.name, label), fields) for label, fields in found)
        key = label_coordinate(ctx.stage_object, box)
        positions = selection_positions(
            entries,
            key.field,
            lambda address, name, side: ctx.resolve(
                name, Identity("line", address=address).block, side
            ),
        )
        bases.update(
            (identity, (box.name, labels[box.name][held[0][0]]))
            for identity, held in positions.items()
            if ctx.role(identity) in VALUE_ROLES and identity.perch == "cntn"
        )
    return sections, labels, bases


def _blocks_of(stage):
    """The builders of a stage in file order with the direction of each
    (`forward`, `backward`, or None for a block no directional rule reads)
    and the lines each holds."""
    ports = header_wire_sorts(stage)
    try:
        found = tuple(blocks(stage))
    except NotConstructed:
        found = ()
    directions = {}
    for box in found:
        try:
            directions[box.name] = block_direction(stage, box, ports)
        except NotConstructed:
            directions[box.name] = None
    return found, directions, {box.name: tuple(lines_of(stage, box)) for box in found}


def _distribution_obligations(plan, obligations):
    """The conditions of the shock distributions (AMD-SG-009 §§3–4; AMD-SG-010
    §3): the family conditions decided from numbers, refused where they fail;
    a uniform, truncated normal or type-I extreme-value law of several
    subjects or of a parameter declared on a collection, refused; the
    positive semidefiniteness of a covariance matrix whose entries are not
    all numbers; the weights of a mixture or a categorical whose terms are not
    all numbers; the parameters of a uniform, truncated normal or type-I
    extreme-value law whose arguments are not all numbers; and the
    factorization of the joint distribution of each edge, which states the
    independence of the components of a collection whose law is the product
    of one scalar law."""
    ctx = plan.ctx

    def refuse(rule, address, message, write=None):
        raise ConstructionError(
            message, stage=ctx.stage_name, address=address, rule=rule, write=write
        )

    # the parameters whose values are no real numbers: those declared on a
    # collection, `μ : I_J → ℝ`, and on a product set, `b : ℝ × ℝ`
    non_real = {}
    for name, declared in ctx.parameter_sets.items():
        if declared is None:
            continue
        if index_factors(declared, ctx.set_terms) is not None:
            non_real[name] = (declared, "a collection")
        elif isinstance(defined(declared, ctx.set_terms), T.Product):
            non_real[name] = (declared, "a product set")
    products = set()
    for owner in plan.owners:
        indexed, dimension = subject_dimension(ctx, owner, {})
        decided = check_family_conditions(owner, {}, refuse, indexed=indexed, dimension=dimension)
        check_real_parameter_shapes(owner, non_real, refuse)
        if indexed and product_law(owner.term):
            products.add(owner.identity)
        if decided:
            continue
        if (
            weights_of(owner)
            or weight_matrix_text(owner) is not None
            or bernoulli_probability(owner) is not None
        ):
            # the weights alone: a mixture's component may be what is
            # undecided
            if not check_weights(owner, {}, refuse, dimension=dimension):
                obligations.append(
                    (
                        "distribution-weights-are-a-probability-vector",
                        (owner.identity,),
                        weights_condition(owner),
                    )
                )
        elif len(owner.subjects) > 1 or (
            indexed and isinstance(owner.term, T.Call) and owner.term.fun == NORMAL
        ):
            obligations.append(
                (
                    "covariance-positive-semidefinite",
                    (owner.identity,),
                    f"The covariance matrix of {owner.identity} must be positive semidefinite.",
                )
            )
        condition = parameter_condition(owner)
        if condition is not None:
            obligations.append(("distribution-parameters-in-domain", (owner.identity,), condition))
    for edge in plan.edges.values():
        if edge.declarations:
            obligations.append(
                factorization_obligation(edge, tuple(i.field for i in edge.base), products)
            )


# --- the definitions table ---


def _definitions_of(term, ctx, stage, spans=None) -> tuple:
    """The definitions table of a stage file (AMD-SG-006 §2): every name the
    file declares, once, in file order — a parameter with its declared set,
    a setting a methods file declares with its declared set,
    a named space, a value definition (`du := D_{c}(u)`) as a function alias
    whose identity kind is `function` and definition kind is `function_alias`,
    an authored function or correspondence, a distribution declaration with
    its shocks — then every authored line as a `line` record keyed by its
    address, and the g of each forward builder and the G of each backward
    builder, each holding the addresses of its block's lines in block order,
    which is a dependency order because a line reads only names defined before
    it.

    The items are read with the addresses `item_addresses` gives them, the
    scheme of the span table, so that a line of a nested block has its
    span-table address under its label, `dcsn_to_cntn.keep.cash_on_hand`. A
    top-level item's record is addressed by its file position, read from
    `spans`; a line record by its block-line address and a `g` or a `G` by its
    block, both of which a reader of the stage follows (AMD-SG-017 §4). The
    declared tags of a set, a function alias, a function and a correspondence
    are kept as a parameter's and a distribution's are, so that the record
    keeps the description an author wrote after `::`. A set marked
    `!categories` holds its category map, and a field declared on it names it
    at every site that names a set (`_coded_field_sites`)."""
    definitions = _declared_definitions(term, ctx, spans)
    # each derived parameter reads declared parameters, numbers and derived
    # parameters without a cycle, through the forms its definition admits
    # (AMD-MT-003, build contract §5)
    derived_order(definitions, spans)
    _coded_field_sites(stage, ctx, definitions, term, spans)
    items = {address: item for address, item in item_addresses(term)}
    blocks, directions, lines = _blocks_of(stage)
    return (
        definitions
        + _line_definitions(blocks, lines, items)
        + _law_definitions(ctx, blocks, directions, lines, items)
        + _typing_definitions(term, ctx, spans)
    )


def _typing_definitions(term, ctx, spans):
    """A `typing` record for every typing entry and handler binding of the
    file, at file level or in a block's header (specification 0.7 §4): its
    identity names the place the entry types, as an absolute path, and the
    component, `method`, `grid` or `handler`; its one equation is the method
    word, the grid or the handler's program; its tags hold the subject as
    written; its address is the entry's file position with its column,
    `cons.bl:14:5`, from which the file it was written in is read and at
    which a refusal of the entry is placed. An entry in a block's header whose subject
    does not start with the block's own id is read relative to the block
    (rule 7). Two entries at one place for one component are refused here,
    naming both (`component-typed-twice`)."""
    found, held = [], {}
    for address, item in item_addresses(term):
        if isinstance(item, T.Declare) and is_typing_entry(item.declaration):
            entries = ((item.declaration, (), address),)
        elif isinstance(item, T.Block):
            scope = tuple(address.split("."))
            entries = tuple(
                (entry.typing, scope, f"{address}.{to_source(entry.typing.subject)}")
                for entry in item.tag.entries
                if isinstance(entry, T.Typer) and is_typing_entry(entry.typing)
            )
        else:
            continue
        for typing, scope, key in entries:
            span = None if spans is None else spans.get(key)
            written = key if span is None or span.line is None else (
                f"{file_position(span)}:{span.column}"
            )
            path = typing.subject
            segments = tuple(path.segments)
            if scope and segments[0].name != scope[0]:
                segments = tuple(T.Segment(name, ()) for name in scope) + segments
            place = path_text(T.Path(segments[:-1]))
            component = segments[-1].name
            value = (
                typing.program
                if isinstance(typing, T.Handler)
                else _classifier_value(typing.classifiers[0])
            )
            identity = Identity("typing", stage=ctx.stage_name, address=place, field=component)
            if identity in held:
                first_written, first_key = held[identity]
                raise construction_error(
                    f"the {component} component of `{place}` is typed twice, at {first_written} "
                    f"and at {written}; a component is typed by one entry; remove one of the two",
                    stage=ctx.stage_name,
                    address=key,
                    span=None if spans is None else spans.get(key),
                    rule="component-typed-twice",
                    related=(
                        location(
                            "original declaration",
                            address=first_key,
                            span=None if spans is None else spans.get(first_key),
                        ),
                    ),
                    write=f"Remove the entry at {first_written} or the entry at {written}",
                )
            held[identity] = (written, key)
            found.append(
                Definition(
                    identity,
                    kind="typing",
                    coordinates=(),
                    equations=(value,),
                    tags=(to_source(path),),
                    address=written,
                )
            )
    return tuple(found)


def _classifier_value(classifier):
    """The term a typing entry's classifier carries: the method word or the
    grid."""
    return classifier.m if isinstance(classifier, T.Method) else classifier.g


def _declared_definitions(term, ctx, spans):
    """The records of the file's top-level declarations and statements, in
    file order: a multiplier, a derived parameter with its declared set or
    the parameters a declaration names, and a set,
    a derived parameter, a function alias, a function, a correspondence or a
    distribution a statement defines. The marker `!categories` on any item but
    a top-level named set is refused where it is written
    (`_misplaced_marker`)."""
    definitions = []
    derived = _derived_parameters(term)
    for address, item in item_addresses(term):
        if isinstance(item, T.Declare) and is_typing_entry(item.declaration):
            continue  # a typing entry declares no name; `_typing_definitions` records it
        written = _written_at(address, spans)
        _misplaced_marker(item, ctx, address, written)
        if isinstance(item, T.Declare) and is_typing_entry(item.declaration):
            # a typing entry or a handler binding the union left at file
            # level, which the semantics reads (specification 0.7, unit U3)
            continue
        if isinstance(item, T.Declare):
            definitions.extend(_declaration_definitions(item, ctx, address, written))
        elif isinstance(item, T.Statement):
            definitions.extend(_statement_definitions(item, ctx, written, derived))
    return tuple(definitions)


def _derived_parameters(term):
    """The names of the file's derived parameters: the definitions without
    arguments whose right side `derived_parameter_body` reads as an
    arithmetic expression, against the right side of every definition without
    arguments, the named sets and the functions and correspondences with
    arguments (AMD-MT-003, build contract §5). A declaration that carries a
    value, `q : (0,1) := (β*R)^(1/ρ)/R`, is a definition without arguments
    here, as the declaration pass reads it."""
    bodies, defined = {}, set()
    for _, item in item_addresses(term):
        typed = _typed_derived_parameter(item)
        if typed is not None:
            bodies[typed[0]] = item.declaration.value
        if not isinstance(item, T.Statement):
            continue
        core = item.core
        if isinstance(core, T.Assignment):
            if isinstance(core.value, T.Space):
                defined.add(core.target.name)
            else:
                bodies[core.target.name] = core.value
        elif isinstance(core, (T.FuncDef, T.CorrDef)):
            defined.add(core.name)
    return frozenset(
        name
        for name, body in bodies.items()
        if derived_parameter_body(body, bodies, frozenset(defined), frozenset({name}))
    )


def _typed_derived_parameter(item):
    """The name and the declared set of an item that defines a derived
    parameter with a declared set, `q : (0,1) := (β*R)^(1/ρ)/R`, as
    `derived_parameter_declaration` reads its declaration; None for any other
    item."""
    if (
        isinstance(item, T.Declare)
        and isinstance(item.declaration, T.Declaration)
        and item.declaration.value is not None
    ):
        return derived_parameter_declaration(item.declaration)
    return None


def _declaration_definitions(item, ctx, address, written):
    """The records a declaration makes: the multiplier of a bound declared in
    a block body, the derived parameter of a declaration that carries a
    value, or a record for each parameter or setting the declaration
    names."""
    typed = _typed_derived_parameter(item)
    if typed is not None:
        # the record of `q := e` with one coordinate, the derived parameter
        # with the set its definition declares, as a multiplier's record
        # holds the multiplier with its declared set (AMD-GRAM-005)
        name, declared = typed
        return (
            Definition(
                Identity("derived", stage=ctx.stage_name, field=name),
                kind="derived_parameter",
                coordinates=((name, declared),),
                equations=(item.declaration.value,),
                tags=_declared_tags(item.annot),
                address=written,
            ),
        )
    if isinstance(item.declaration, T.Complementary):
        # the multiplier of a bound declared in a block body: the record
        # holds the declaration with its clause as written, its declared
        # set and its block-line address (AMD-SG-035 §5)
        coordinate = item.declaration.declaration.subject.coordinates[0]
        declared = next(
            c.space for c in item.declaration.declaration.classifiers if isinstance(c, T.Domain)
        )
        return (
            Definition(
                Identity("multiplier", stage=ctx.stage_name, field=coordinate.stem),
                kind="multiplier",
                coordinates=((coordinate.stem, declared),),
                equations=(item.declaration,),
                tags=_declared_tags(item.annot),
                address=address,
            ),
        )
    found = []
    for coordinate in item.declaration.subject.coordinates:
        if not isinstance(coordinate, T.Coordinate):
            continue
        # a top-level declaration of the stage file is a parameter, and one
        # of a methods file, an addition, a setting (specification 0.7, S1):
        # the declaration pass tells them apart by the file of the item
        if coordinate.stem in ctx.parameter_names:
            kind, declared = "parameter", ctx.parameter_sets.get(coordinate.stem)
        elif coordinate.stem in ctx.setting_sets:
            kind, declared = "setting", ctx.setting_sets.get(coordinate.stem)
        else:
            continue
        found.append(
            Definition(
                Identity(kind, stage=ctx.stage_name, field=coordinate.stem),
                kind=kind,
                coordinates=(),
                equations=() if declared is None else (declared,),
                tags=_declared_tags(item.annot),
                address=written,
            )
        )
    return tuple(found)


def _statement_definitions(item, ctx, written, derived):
    """The record a top-level statement makes: a named set, a derived
    parameter, a function alias, a function, a correspondence or a
    distribution declaration; none for any other statement. A definition
    without arguments whose name is among `derived` is a derived parameter, a
    constant of the stage its definition writes from the parameters, with the
    kind `derived_parameter` and an identity of the kind `derived`,
    `<stage>:derived:h` (AMD-MT-003, build contract §5); any other value
    definition is a function alias."""
    core = item.core
    if isinstance(core, T.Assignment):
        if isinstance(core.value, T.Space):
            return (
                Definition(
                    Identity("set", stage=ctx.stage_name, field=core.target.name),
                    kind="set",
                    coordinates=(),
                    equations=(core.value.set,),
                    tags=_declared_tags(item.annot),
                    address=written,
                    categories=_set_categories(core, item.annot, ctx, written),
                ),
            )
        derived_parameter = core.target.name in derived
        return (
            Definition(
                Identity(
                    "derived" if derived_parameter else "function",
                    stage=ctx.stage_name,
                    field=core.target.name,
                ),
                kind="derived_parameter" if derived_parameter else "function_alias",
                coordinates=(),
                equations=(core.value,),
                tags=_declared_tags(item.annot),
                address=written,
            ),
        )
    if isinstance(core, (T.FuncDef, T.CorrDef)):
        kind = "correspondence" if isinstance(core, T.CorrDef) else "function"
        params = tuple((c.stem, coordinate_declared_set(c)) for c in core.params)
        return (
            Definition(
                Identity(kind, stage=ctx.stage_name, field=core.name),
                kind=kind,
                coordinates=params,
                equations=(core,),
                tags=_declared_tags(item.annot),
                address=written,
            ),
        )
    if isinstance(core, T.Law):
        subjects = tuple(core.subjects)
        # the coordinates are the declaration's state, control and shock
        # arguments; the retained Law keeps its subject (AMD-SG-009 §1)
        return (
            Definition(
                Identity("distribution", stage=ctx.stage_name, subjects=subjects),
                kind="distribution",
                coordinates=tuple(
                    (name, ctx.sets.get(identity))
                    for name, identity in family_term_arguments(core.law, ctx)
                ),
                equations=(core,),
                tags=_declared_tags(item.annot),
                address=written,
            ),
        )
    return ()


# --- the category codes of a named set (`typing/category_codes.py`) ---


def _set_categories(assignment, annot, ctx, written):
    """The category map of a named set marked `!categories`, None for an
    unmarked set. A map its annotation and its set do not give is refused under
    `category-codes` at the set's file position, the message naming every
    failed check."""
    try:
        return category_codes(assignment.value.set, annot, assignment.target.name)
    except CategoryCodesFault as fault:
        raise ConstructionError(
            fault.message, stage=ctx.stage_name, address=written, rule="category-codes"
        ) from None


def _misplaced_marker(item, ctx, address, written):
    """Refuses, under `category-codes`, an entry the marker `!categories`
    reserves on any item but a top-level assignment of a named set, the one
    item on which category codes are written; a field declared on that set
    has them. The entries read are a statement's or a declaration's
    annotation and a block's header; a top-level item is refused at its file
    position and a block or a line of one at its own address."""
    if isinstance(item, T.Block):
        annotation, place, words = item.tag, address, f"the header of block {address!r}"
    elif isinstance(item, (T.Statement, T.Declare)):
        top_level = address.isdigit()
        if top_level and isinstance(item, T.Statement):
            core = item.core
            if isinstance(core, T.Assignment) and isinstance(core.value, T.Space):
                return
        annotation = item.annot
        place = written if top_level else address
        words = _item_words(item) if top_level else f"the line {address!r}"
    else:
        return
    reserved = reserved_entries(annotation)
    if not reserved:
        return
    entry = reserved[0]
    text = entry.tag if isinstance(entry, T.Tag) else f"{entry.key}={entry.value}"
    raise ConstructionError(
        f"{words} writes `{text}`; category codes are written only on a named set defined by "
        f"a comprehension, `H := {{i : ℤ | i >= 0, i <= 1}} :: [!categories, newborn=0, "
        f"old=1]`, and a field declared on that set has them. Remove `{text}` here",
        stage=ctx.stage_name,
        address=place,
        rule="category-codes",
    )


def _item_words(item) -> str:
    """A top-level statement or declaration in words, `the function alias 𝑑𝑢`,
    as a refusal names it."""
    if isinstance(item, T.Declare):
        declaration = item.declaration
        if is_typing_entry(declaration):
            return f"the entry of {to_source(declaration.subject)}"
        if isinstance(declaration, T.Complementary):
            declaration = declaration.declaration
        stems = [c.stem for c in declaration.subject.coordinates if isinstance(c, T.Coordinate)]
        return f"the declaration of {', '.join(stems)}"
    core = item.core
    if isinstance(core, T.Assignment):
        return f"the function alias {core.target.name}"
    if isinstance(core, T.FuncDef):
        return f"the function {core.name}"
    if isinstance(core, T.CorrDef):
        return f"the correspondence {core.name}"
    if isinstance(core, T.Law):
        return f"the distribution of {', '.join(map(str, core.subjects))}"
    return "the statement"


def _coded_field_sites(stage, ctx, definitions, term, spans):
    """Refuses, under `category-codes`, a field declared on a set with
    category codes at one site and on another set at another: every site that
    names a set for the field names that set, so that the field's sort, the
    meet of its sites' sets, keeps it. The sites are those of the working
    stage's fields table; the refusal stands at the site that names the other
    set."""
    sets = {d.identity.field: d.equations[0] for d in definitions if d.kind == "set"}
    categories = {
        d.identity.field: d.categories
        for d in definitions
        if d.kind == "set" and d.categories is not None
    }
    if not categories:
        return
    for identity, (_, _, _, sites) in stage.data["fields"].items():
        named = [site for site in sites if site[2] is not None]
        coded = next(
            (site for site in named if coded_meaning(site[2], sets, categories, None) is not None),
            None,
        )
        other = next((site for site in named if site[2] != coded[2]), None) if coded else None
        if other is None:
            continue
        stem, coded_set, other_set = identity.field, to_source(coded[2]), to_source(other[2])
        raise ConstructionError(
            f"the field {stem} is declared on `{coded_set}` {_site_words(coded)} and on "
            f"`{other_set}` {_site_words(other)}; `{coded_set}` has category codes, and "
            f"every site that declares a set for {stem} declares `{coded_set}`. Declare {stem} "
            f"on `{coded_set}` {_site_words(other)}, or on no set there",
            stage=ctx.stage_name,
            address=_site_address(other, stem, term, spans),
            rule="category-codes",
        )


def _site_words(site) -> str:
    """A declaration site of a field in words: `at the top level`, `on the
    input side of block 'b'`."""
    where, side, _ = site
    if where == TOP_LEVEL:
        return "at the top level"
    if side is None:
        return f"in block {where!r}"
    return f"on the {side} side of block {where!r}"


def _site_address(site, stem, term, spans):
    """The address of a declaration site of a field: the file position of the
    top-level declaration of `stem`, or the site's block."""
    where = site[0]
    if where != TOP_LEVEL:
        return where
    for address, item in item_addresses(term):
        if (
            address.isdigit()
            and isinstance(item, T.Declare)
            and isinstance(item.declaration, T.Declaration)
            and isinstance(item.declaration.subject, T.Subject)
            and any(
                isinstance(c, T.Coordinate) and c.stem == stem
                for c in item.declaration.subject.coordinates
            )
        ):
            return _written_at(address, spans)
    return None


def _line_definitions(blocks, lines, items):
    """A `line` record for every authored line, keyed by its address, in
    block order."""
    return tuple(
        Definition(
            Identity("line", address=record.address),
            kind="line",
            coordinates=(),
            equations=(statement_core(items[record.address]),),
            tags=tuple(record.tags),
            address=record.address,
            ordinal=record.ordinal,
        )
        for box in blocks
        for _, record in lines[box.name]
    )


def _law_definitions(ctx, blocks, directions, lines, items):
    """The g of each forward builder and the G of each backward builder, each
    holding the addresses of its block's lines in block order; a forward line
    that takes an expectation is refused."""
    definitions = []
    for box in blocks:
        if directions[box.name] == "forward":
            for _, record in lines[box.name]:
                if expectation_occurrences(statement_core(items[record.address])):
                    raise ConstructionError(
                        f"the transition block {box.name!r} integrates over a shock in statement "
                        f"{record.address!r}; a forward builder is the push-forward of a measure "
                        f"through the law of motion 𝑔 and takes no expectation; write the "
                        f"integration in a backward block",
                        stage=ctx.stage_name,
                        address=record.address,
                        rule="transition-without-expectation",
                    )
            definitions.append(
                Definition(
                    Identity("g", stage=ctx.stage_name, address=box.name),
                    kind="g",
                    coordinates=tuple(
                        (i.field, ctx.declared_set(i)) for i in header_identities(box).inputs
                    ),
                    equations=tuple(r.address for _, r in lines[box.name]),
                    tags=(),
                    address=box.name,
                )
            )
        elif directions[box.name] == "backward":
            definitions.append(
                Definition(
                    Identity("G", stage=ctx.stage_name, address=box.name),
                    kind="G",
                    coordinates=tuple(
                        (i.field, ctx.declared_set(i)) for i in header_identities(box).inputs
                    ),
                    equations=tuple(
                        r.address
                        for _, r in lines[box.name]
                        if r.role != DOC
                        or any(ctx.role(i) == "control" for i in header_identities(box).outputs)
                    ),
                    tags=(),
                    address=box.name,
                )
            )
    return tuple(definitions)


def _declared_tags(annot):
    """The tags an author wrote after `::` on a declaration, in the order
    written: `key=value` for a key-value entry and its text for a bare tag,
    which is how a line's tags are recorded. A description on a parameter or a
    shock declaration, `β : (0,1) :: ["discount factor"]`, is authored
    information the graph does not determine, so it is kept (AMD-SG-014 §3)."""
    if annot is None:
        return ()
    return tuple(
        f"{entry.key}={entry.value}" if isinstance(entry, T.KeyValue) else str(entry.tag)
        for entry in annot.entries
        if isinstance(entry, (T.KeyValue, T.Tag))
    )


def _written_at(address, spans) -> str:
    """The address a record of a top-level item carries: the file position
    `<path>:<line>` the span table gives for the item (AMD-SG-017 §4), and the
    term position itself where the term was decoded from a saved AST and no
    table was parsed with it.

    The term position that `item_addresses` yields stays the key of the span
    table and appears on no record: it names the place of an item inside one
    parse and resolves to nothing a reader of the stage can follow."""
    span = None if spans is None else spans.get(address)
    return address if span is None or span.line is None else file_position(span)


# --- the forward block: the law of motion and its equations ---


@dataclass(frozen=True, slots=True, kw_only=True)
class _LawOfMotion:
    """A forward builder's g as the fold of a backward block reads it: the
    identity of the `g` record, the block's input and output identities and
    the retained terms of its lines, in block order. Exists during a fold."""

    identity: str
    inputs: tuple
    outputs: tuple
    equations: tuple


def law_of_motion_equations(ctx, block, equations):
    """The equations of g with local definitions and other outputs substituted.

    Authored equations remain in the definition records. These resolved terms
    are temporary, shared by the value fold and the numerical kernel query.
    """
    definitions = {defined_name(core): right_side(core) for core in equations}
    resolved, active = {}, []

    def definition(spelling):
        if spelling in resolved:
            return resolved[spelling]
        if spelling in active:
            cycle = " → ".join(spelled_with_mark(s) for s in active + [spelling])
            raise ConstructionError(
                f"the equations of the law of motion of block "
                f"{block!r} read one another in a cycle, {cycle}",
                stage=ctx.stage_name,
                address=block,
                rule="definition-order",
            )
        active.append(spelling)
        result = substitute(definitions[spelling])
        active.pop()
        resolved[spelling] = result
        return result

    def substitute(term):
        if isinstance(term, T.Sym) and isinstance(term.symbol, (T.Constant, T.Variable)):
            spelling = next(iter(symbol_occurrences(term)), None)
            return definition(spelling) if spelling in definitions else term
        if isinstance(term, T.Key) and isinstance(term.at, str):
            replacement = substitute(T.Sym(T.Constant(term.at)))
            if isinstance(replacement, T.Sym) and isinstance(replacement.symbol, T.Constant):
                return T.Key(replacement.symbol.name)
            raise ConstructionError(
                f"the selection key {term.at!r} in the law of motion of block {block!r} is "
                f"defined by {to_source(replacement)}; the retained selector requires a name, so "
                f"this pullback needs a construction for a computed selection key",
                stage=ctx.stage_name,
                address=block,
                rule="not-constructed",
            )
        if dataclasses.is_dataclass(term) and not isinstance(term, type):
            return type(term)(
                *(substitute(getattr(term, f.name)) for f in dataclasses.fields(term))
            )
        if isinstance(term, tuple):
            return tuple(substitute(item) for item in term)
        return term

    def equation(core):
        if isinstance(core, T.Slack):
            return dataclasses.replace(core, core=equation(core.core))
        return dataclasses.replace(core, rhs=definition(defined_name(core)))

    return tuple(equation(core) for core in equations)
