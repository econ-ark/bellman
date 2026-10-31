"""The fold of the policy block (AMD-SG-008 §7).

The rows of the policy builder carry the standard kinds of the constituent
operations and no other: `Pullback`, `Aggregation`, `Expectation`,
`Evaluation` and `Argmax`. A row's kind names the operator its rule applies,
its outputs are the fields its line defines, and a row whose rule holds its
outputs on both sides keeps them as its unknowns.

An operative `argmax` line forms the rows of its objective, the pullbacks,
the expectations and the `Aggregation` that write it, and one `Argmax` row
whose rule is the maximization statement and whose output is the policy. A
relational line forms one `Aggregation` whose rule is its relation: an
inequality or a complementarity on a named field with its clause, the
candidate line of `cons.bl`; a system of candidate statements, the relation of
its members in their candidates; a `solve` line, its residual system with the
line's outputs as the unknowns, the joint solve of `adjuster_cons.bl`. The
candidate's row holds its clause among its equations and the explicit side as
its map, and the rows are the same with or without the clause: the set of
values the clause admits at each point, and the reading of a solve's residual
against such a candidate, `c − c[>]`, as the membership `c ∈ 𝑐≻(…)`, are read
from these rows by the queries of `stage/defining_expressions.py`, the wires
that carry a set of values being `graphs/wire_sorts.correspondence_wires`.
The line that identifies an output of the block with the fields its lines
define at the continuation perch, `c = c[>]`, forms one `Pullback`, the
output pulled back along the coordinate functions those lines define and
equated to the line's right side. Adjacent explicit lines on the continuation
grid are one `Aggregation` of the functions they read there. A line whose id
is dotted, `optimality.euler`, states a property of the line `optimality`: it
forms no row, and the row of that line holds it. `candidate_systems` groups
the candidate statements of a block into the systems the header's order
states (AMD-SG-035 §5).
"""

from __future__ import annotations

import dataclasses
from typing import NamedTuple

from bellman.fold.backward import (
    Slice,
    WorkingRows,
    aggregation_row,
    backward_block,
    check_output_shocks,
    check_value_roles,
    expectation_rows,
    folded_line,
    line_domain,
    pullback_wire,
    pullbacks_in_header_order,
    reduced_term,
    refuse_backward_block,
    refuse_second_definition,
    retained_relations,
    shocks_in_header_order,
    sub_builder_rows,
    value_role_of,
)
from bellman.fold.block_lines import property_owners
from bellman.fold.table import BlockRows, OperatorRow
from bellman.fold.value_bundles import (
    bundled_pullbacks,
    primitive_grain_rows,
    pullbacks_after_their_writers,
)
from bellman.fold.wire_terms import (
    BlockLine,
    defined_field,
    defined_name,
    expectation_nodes,
    is_wire_symbol,
    names_no_field,
    nodes_outside_expectations,
    right_side,
    statement_core,
    substitute_wires,
    wire_symbol,
    wires_read,
)
from bellman.native.identity import Identity
from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import ALIAS, DOC, NODE, OUTPUT_LINE, VALUE_ROLES
from bellman.typing.line_unknowns import (
    candidates_of_statement,
    maximand,
    names_fields,
    systems_by_shared_candidate,
)


def fold_policy_block(plan, name, records, dom, cod, obligations, transition=None) -> BlockRows:
    """The rows of the policy builder (AMD-SG-008 §7) at the primitive and the
    sub-builder grain.

    Each objective or residual is constructed before the row that chooses
    or solves over the ordered controls, with the pullback, aggregation and
    expectation rules of a backward value block on the decision edge: a value
    input is composed with the forward-owned g, and a candidate function
    defined at the continuation perch is composed with g when a residual reads
    it there. The line that chooses, solves or identifies an output forms its
    row by `_output_rows`: an `Argmax`, an `Aggregation` in its unknowns or
    the `Pullback` of the identification. Adjacent explicit equations
    defining perch-marked fields (`c[>]`, `m_d[>]`) form one pointwise G on
    the states of their perch, reading a value input of that perch at its
    own coordinates and no law of motion (`_explicit_lines_aggregation`); an
    inequality, a complementarity or an implicit left side is one
    `Aggregation` whose map is its explicit right side and whose rule is the
    line's relation (`_relation`); a `!node` line is a sub-builder
    (`sub_builder_rows`); a local name is pending arithmetic, folded where it
    is read. Every wire is a function of its domain's coordinates, and the
    relation between a candidate on the continuation states and the policy on
    the decision states goes through the coordinate functions the policy lines
    define there (`m_d[>](·)`); `transition` is the identity of the law of
    motion from the decision to the continuation perch, which an `Argmax`
    reading such functions references. A property line, attached to another
    line by a dotted id, forms no row and seeds no slice; the row of the line
    it is attached to holds its address (`_with_properties`). Every row is
    formed from a line the file writes: a block that omits the line defining
    an output is refused at construction, and no row is inferred for it.

    The steps stand in this order: the systems of candidate statements; then,
    line by line in file order, the segment of the adjacent explicit lines, the
    relation of a retained inequality or implicit left side, the node of a
    `!node` line, the pre-choice objective or residual with its expectations
    and pullbacks, and the row of a line that chooses, solves or identifies an
    output (`_output_rows`); then the merge of the pullbacks along a law of
    motion into one box on the value bundle, their order after the boxes
    whose outputs they read, and the evaluation of the outputs
    (`_policy_evaluation`); then the properties held by the rows of their
    lines; then the retained relations of the lines no row realizes. The
    primitive grain opens the sub-builders as in a value block.
    """
    properties = property_owners(r.address for r in records)
    operative = tuple(r for r in records if r.address not in properties)
    lines = tuple(
        BlockLine(address=r.address, role=r.role, core=statement_core(plan.items[r.address]))
        for r in operative
    )
    by_spelling = {defined_name(line.core): line for line in lines if line.role == ALIAS}
    block = backward_block(
        plan, name, dom, cod, lines, by_spelling, _policy_seeds(plan.ctx, name, lines)
    )
    acc = WorkingRows([], obligations)
    edge = Slice(
        block.name, None, block.domain
    )  # the decision edge: objectives, residuals and their local names
    entries = {line.address: line for line in block.lines}
    systems = candidate_systems(block.ctx, block.name, block.cod, block.lines)
    held = {address for system in systems.values() for address in system.addresses}
    decision = block.ctx.coordinates("dcsn", roles=("state",))
    pending = []  # adjacent explicit lines not yet folded
    for record in operative:
        entry, system = entries[record.address], systems.get(record.address)
        if _forms_no_row(record, system, held):
            continue
        if names_no_field(entry.core):
            # an inequality whose left side is not a name states a relation and
            # no equation, and no operator of the builder realizes it
            # (AMD-SG-017 §§1, 5.6)
            _flush(block, acc, pending)
            continue
        _check_system(block, record.address, system)
        targets = (
            system.unknowns if system is not None else block.ctx.defined(entry.core, block.name)
        )
        if _solves(record, entry.core, system, targets, block.cod):
            _flush(block, acc, pending)
            _output_rows(block, acc, edge, record, system, targets, entries, transition, decision)
        elif _explicit(entry.core, targets) and record.role != NODE:
            pending.append(entry)
        elif _explicit(entry.core, targets):
            _flush(block, acc, pending)
            domain = line_domain(block, acc, defined_field(block.ctx, block.name, entry.core))
            sub_builder_rows(
                block,
                Slice(record.address, record.address, domain),
                acc,
                record.address,
                entry.core,
            )
        else:
            _flush(block, acc, pending)
            _relation(block, acc, entry, targets, record.role == NODE, edge)
    _flush(block, acc, pending)
    closed = _with_properties(block, _policy_evaluation(block, acc.rows, decision), properties)
    retained_relations(block, acc, closed)
    return BlockRows(primitive=primitive_grain_rows(closed), sub_builder=closed)


def _policy_seeds(ctx, name, lines):
    """The owner of the slice that folds each line of the policy builder that
    seeds a slice: a choice, a solve or the identification is folded in the
    slice of the edge, the builder's own; a perch-marked line or a relation in
    a slice of its own, its address; a local name nowhere of its own, since it
    is folded where it is read."""
    seeds = {}
    for address, role, core in lines:
        if role in (NODE, DOC):
            continue
        defined = defined_field(ctx, name, core)
        local = defined is not None and defined.perch is None and isinstance(core, T.Equation)
        if role == OUTPUT_LINE:
            seeds[address] = name
        elif not local:
            seeds[address] = address
    return seeds


def _forms_no_row(record, system, held) -> bool:
    """Whether a policy line forms no row of its own: a line marked `!doc`,
    which declares what the construction is to reach and which the builder
    holds as the condition on its constructed output (AMD-SG-034 §3
    `declared`, §11 item 1); a later statement of a system, whose row stands at
    the address of the system's first statement and carries every member's
    equation; and a candidate statement with no candidate, which determines
    nothing the block must supply, so that no operator realizes it, it is
    retained on the initial diagram and records retained-relation
    (AMD-SG-017 §§1, 5.6)."""
    return (
        record.role == DOC
        or (system is None and record.address in held)
        or (system is not None and not system.unknowns)
    )


def _check_system(block, address, system):
    """The check that a system of implicit statements has exactly as many
    statements as unknowns, the condition under which it is constructed; a
    refusal otherwise."""
    if system is not None and len(system.addresses) != len(system.unknowns):
        spelled = ", ".join(i.field for i in system.unknowns)
        listed = ", ".join(system.addresses)
        refuse_backward_block(
            block,
            "not-constructed",
            address,
            f"{len(system.addresses)} statements of builder {block.name!r} ({listed}) state a "
            f"relation in {len(system.unknowns)} unknowns ({spelled}); a system of implicit "
            f"statements is constructed where its statements are exactly as many as its unknowns. "
            f"Write as many equations as there are unknowns, or name the unknowns a statement "
            f"determines by the solve_{{…}} spelling, `{spelled} = solve_{{{spelled}}}(…)`",
        )


def _solves(record, core, system, targets, cod) -> bool:
    """Whether a policy line chooses, solves or identifies an output, and so
    forms its row by `_output_rows`: its right side is an `argmax` or a
    `solve`, it states a system of candidate statements, it records a
    `solve`, or it defines an output of the block."""
    return (
        _choice(core) is not None
        or system is not None
        or any(o.head == "solve" for o in record.operators)
        or any(target in cod for target in targets)
    )


def _choice(core):
    """The `argmax` or the `solve` a line's right side is, or None."""
    choice = right_side(core)
    return (
        choice if isinstance(choice, T.Operator) and choice.head in ("argmax", "solve") else None
    )


def _flush(block, acc, pending):
    """The one G of the adjacent explicit lines held in `pending`, which it
    then empties (`_explicit_lines_aggregation`)."""
    if pending:
        _explicit_lines_aggregation(block, acc, tuple(pending))
        del pending[:]


def _output_rows(block, acc, edge, record, system, targets, entries, transition, decision):
    """The rows of a line that chooses, solves or identifies an output of the
    block, constructed in the slice of the decision edge, or in a slice of its
    own for a `!node` line, whose computed functions the node's evaluation
    then names. Each row holds the fields it determines as its unknowns and
    reads, beside what its rule reads, the coordinate functions the block's
    lines define at the continuation perch.

    An operative `argmax` forms the rows of its complete objective and one
    `Argmax` row, whose rule is the maximization statement and whose map is
    the objective. A `solve` line forms one `Aggregation`, whose map is its
    residuals and whose rule is the residual system in the line's outputs, and
    no row of its own for the residuals. A system of candidate statements forms
    the pullbacks and expectations its members read and one `Aggregation`,
    whose rule is the relation of its members in their candidates and which
    has no map, since no member writes a candidate explicitly, and so
    references its statements and no G. Every other line
    that defines an output of the block, the identification `c = c[>]`, forms
    one `Pullback`, the output pulled back along the coordinate functions and
    equated to the line's right side, which references the block's G, since
    the lines of that G define those functions."""
    ctx, address = block.ctx, record.address
    choice = _choice(entries[address].core)
    env = Slice(address, address, block.domain) if record.role == NODE else edge
    start = len(acc.rows)
    # a system states one relation in several statements, in file order
    statements = system.addresses if system is not None else (address,)
    cores = tuple(entries[a].core for a in statements)
    outputs = tuple(ctx.function_wire(i) for i in targets)
    if choice is not None:
        expression, folded = _chosen(block, env, acc, choice, targets, address)
        if choice.head == "solve":
            read = wires_read(folded.term)
            _relation_row(
                block,
                acc,
                Identity("Aggregation", address=address),
                statements=statements,
                inputs=read + _coordinate_wires(ctx, acc, read),
                outputs=outputs,
                maps=(folded.term,),
                cores=cores,
                unknowns=targets,
                arguments=decision,
                node=env.node,
            )
        else:
            complete = _objective(block, env, acc, expression, folded, address)
            coordinates = _coordinate_wires(ctx, acc, (complete,))
            acc.rows.append(
                OperatorRow(
                    Identity("Argmax", address=address),
                    kind="Argmax",
                    builder=block.name,
                    direction="backward",
                    statements=statements,
                    inputs=(complete,) + coordinates,
                    outputs=outputs,
                    references=statements,
                    parameters=ctx.parameters(cores),
                    definition=transition if coordinates else None,
                    unknowns=targets,
                    arguments=decision,
                    node=env.node,
                    maps=(wire_symbol(complete),),
                    equations=cores,
                    conditions=ctx.conditions(
                        cores, acc.obligations, block.name, block=block.name
                    ),
                )
            )
    elif system is not None:
        mentioned = _residual_inputs(block, env, acc, cores, address)
        _relation_row(
            block,
            acc,
            Identity("Aggregation", address=address),
            statements=statements,
            inputs=mentioned + _coordinate_wires(ctx, acc, mentioned),
            outputs=outputs,
            maps=(),
            cores=cores,
            unknowns=targets,
            arguments=decision,
            node=env.node,
            references=statements,
            definition=None,
        )
    else:
        mentioned = _residual_inputs(block, env, acc, cores, address)
        # the unknown the construction's `solve` names on an implicit
        # statement, and the line's outputs otherwise
        unknowns = tuple(
            ctx.resolve(o.unknown, block.name)
            for o in record.operators
            if o.head == "solve" and o.unknown
        )
        acc.rows.append(
            OperatorRow(
                Identity("Pullback", address=address),
                kind="Pullback",
                builder=block.name,
                direction="backward",
                statements=statements,
                inputs=mentioned + _coordinate_wires(ctx, acc, mentioned),
                outputs=outputs,
                references=(block.Gid,),
                parameters=ctx.parameters(cores),
                definition=block.Gid,
                unknowns=unknowns or targets,
                arguments=decision,
                node=env.node,
                equations=cores,
                conditions=ctx.conditions(cores, acc.obligations, block.name, block=block.name),
            )
        )
    if env.node is not None:
        _evaluate_node(acc, env.node)
        pullbacks_in_header_order(block, acc, start)


def _coordinate_wires(ctx, acc, mentioned):
    """The coordinate functions the block's lines define at the continuation
    perch that a row reads beside the wires `mentioned`: the wire of each
    state a perch-marked line defines, `m_d[>](·)`, through which a policy on
    the decision states is related to its candidate on the continuation
    states (AMD-SG-035 §3)."""
    return tuple(
        w for f, w in acc.wires.items() if ctx.role_by_name(f) == "state" and w not in mentioned
    )


# the default of the references and of the definition of `_relation_row`:
# the block's G, which a relation with a map references
_BLOCK_G = object()


def _relation_row(
    block,
    acc,
    identity,
    *,
    statements,
    inputs,
    outputs,
    maps,
    cores,
    unknowns,
    arguments,
    node,
    references=_BLOCK_G,
    definition=_BLOCK_G,
):
    """One `Aggregation` row whose rule is a relation in its outputs, which
    it holds as its unknowns, appended to `acc.rows`: the lines at
    `statements`, whose terms (`cores`) give its parameters and conditions,
    read over the wires `inputs`, with the map `maps`, the explicit side of the
    relation where its line writes one or the residuals of a `solve`. A row
    with a map references the block's G and has it as its definition, the
    defaults of `references` and `definition`, since the map is an explicit
    function the lines of that G write; a row with no map, the relation of a
    system of candidate statements, references its statements and has no
    definition, since it holds no explicit function. The row records no
    obligation that its lines define its outputs on their declared sets,
    since a relation states a set of candidates and need not define one
    function."""
    ctx = block.ctx
    acc.rows.append(
        OperatorRow(
            identity,
            kind="Aggregation",
            builder=block.name,
            direction="backward",
            statements=tuple(statements),
            inputs=tuple(inputs),
            outputs=tuple(outputs),
            references=(block.Gid,) if references is _BLOCK_G else tuple(references),
            parameters=ctx.parameters(tuple(cores)),
            definition=block.Gid if definition is _BLOCK_G else definition,
            unknowns=tuple(unknowns),
            arguments=tuple(arguments),
            node=node,
            maps=tuple(maps),
            equations=tuple(cores),
            conditions=ctx.conditions(tuple(cores), acc.obligations, block.name, block=block.name),
        )
    )


def _chosen(block, env, acc, choice, targets, address):
    """What an `argmax` maximizes or a `solve` sets to zero, read with the
    line's outputs in place of its unknowns and folded in the slice: the term
    as the line writes it and its fold. The unknowns are checked against the
    line's outputs, in number and in order."""
    ctx = block.ctx
    unknowns = tuple(s.var if isinstance(s, T.In) else s.name for s in choice.subs)
    if len(unknowns) != len(targets):
        refuse_backward_block(
            block,
            "not-constructed",
            address,
            f"the ordered choice has {len(unknowns)} unknowns but its left side has "
            f"{len(targets)} outputs; each unknown needs its corresponding output",
        )
    names = tuple(identity.field for identity in targets)
    if unknowns != names and set(unknowns) == set(names):
        refuse_backward_block(
            block,
            "not-constructed",
            address,
            f"the choice names {unknowns} in a different order from its outputs {names}; "
            f"use the same order, or distinct dummy names to state the positional mapping",
        )
    bindings = {name: ctx.symbol(identity) for name, identity in zip(unknowns, targets)}
    # what the argmax maximizes: its one argument, or the tuple of its
    # arguments indexed by its binder; what a solve sets to zero: its
    # residuals
    expression = _substitute_arguments(maximand(choice), bindings, ctx.stage_name, address)
    order = {id(node): n for n, node in enumerate(expectation_nodes(expression), 1)}
    folded = reduced_term(block, env, acc, expression, address, order)
    check_value_roles(block, acc, address, folded.term)
    check_output_shocks(block, env, block.cod[0], address, folded)
    return expression, folded


def _objective(block, env, acc, expression, folded, address):
    """The result wire of the complete objective an `argmax` chooses over:
    the folded term's one bare result, or the result of the `Aggregation`
    made for it."""
    if is_wire_symbol(folded.term):
        return folded.term.symbol.name
    result = Identity("Aggregation", address=address, mark="result")
    role = value_role_of(acc, folded.term)
    inputs = wires_read(folded.term)
    aggregation_row(
        block,
        env,
        acc,
        Identity("Aggregation", address=address),
        statements=(address,),
        inputs=inputs,
        outputs=(result,),
        maps=(folded.term,),
        cores=(expression,),
        coordinates=env.domain.base,
    )
    acc.roles[result] = role or (acc.roles.get(inputs[0]) if inputs else None)
    return result


def _residual_inputs(block, env, acc, cores, address):
    """The wires a residual or a declarative statement reads: the function
    wires read outside the line's expectations, then the results of those
    expectations, each constructed once in the slice under the conditional
    distribution it selects."""
    results = ()
    for member in cores:
        order = {id(node): n for n, node in enumerate(expectation_nodes(member), 1)}
        results += tuple(
            expectation_rows(block, env, acc, node, address, order).term.symbol.name
            for node in nodes_outside_expectations(member)
            if isinstance(node, T.Operator) and node.head == "E"
        )
    return (
        tuple(dict.fromkeys(w for member in cores for w in _value_wires(block, env, acc, member)))
        + results
    )


def _value_wires(block, env, acc, core):
    """The function wires a residual or a declarative statement reads: the
    wire `acc.wires` holds for a function a policy line defines, and, for a
    value input of the perch the law of motion g produces, its composition
    with g (AMD-SG-017 §5.7). A residual on the decision control is a
    function of the decision states and the control, so the marginal value
    it reads is pulled back along g as the value of an objective is."""
    ctx = block.ctx
    out = []
    for identity in ctx.mentioned(right_side(core), block.name, skip_expectations=True):
        wire = acc.wires.get(identity)
        if wire is None and ctx.role(identity) in VALUE_ROLES:
            wire = (
                pullback_wire(block, env, acc, identity)
                if env.domain.g is not None and identity.perch == env.domain.target
                else ctx.function_wire(identity)
            )
        if wire is not None and wire not in out:
            out.append(wire)
    return tuple(out)


def _policy_evaluation(block, rows, decision):
    """The rows of the policy builder in their final order, its outputs named:
    the pullbacks of one slice along one law of motion merged into one box on
    the value bundle (`_bundled_pullbacks`); the edge's pullbacks of the
    header's value inputs first, in the header's order, since they read block
    inputs only, and a pullback of a function a policy line defines after the
    row producing it; then each output of the block the rows produce renamed
    as the result of its row, and one `Evaluation` on the decision states
    naming the outputs."""
    ctx = block.ctx
    rows = _bundled_pullbacks(rows)
    written = {wire for row in rows for wire in row.outputs}
    order = {ctx.function_wire(i): index for index, i in enumerate(block.inputs)}
    first = sorted(
        (
            row
            for row in rows
            if row.kind == "Pullback"
            and row.node is None
            and row.inputs[0] in order
            and not any(wire in written for wire in row.inputs)
        ),
        key=lambda row: order[row.inputs[0]],
    )
    leading = {id(row) for row in first}
    closed = tuple(
        pullbacks_after_their_writers(first + [row for row in rows if id(row) not in leading])
    )
    produced = {wire: row for row in closed for wire in row.outputs}
    outputs = tuple(
        ctx.function_wire(identity)
        for identity in block.cod
        if ctx.function_wire(identity) in produced
    )
    if not outputs:
        return closed
    renamed = {
        wire: Identity(
            produced[wire].kind,
            address=produced[wire].identity.address,
            field=wire.field,
            mark="result",
        )
        for wire in outputs
    }
    replacements = {wire: wire_symbol(result) for wire, result in renamed.items()}
    closed = tuple(
        dataclasses.replace(
            row,
            inputs=tuple(renamed.get(wire, wire) for wire in row.inputs),
            outputs=tuple(renamed.get(wire, wire) for wire in row.outputs),
            maps=tuple(substitute_wires(term, replacements) for term in row.maps),
        )
        for row in closed
    )
    return closed + (
        OperatorRow(
            Identity("Evaluation", address=block.name),
            kind="Evaluation",
            builder=block.name,
            direction="backward",
            statements=(),
            inputs=tuple(renamed[wire] for wire in outputs),
            outputs=tuple(
                Identity("Evaluation", address=block.name, field=wire.field, mark="result")
                for wire in outputs
            ),
            arguments=decision,
        ),
    )


def _identifies(row) -> bool:
    """Whether a row is the `Pullback` of an identification, the only pullback
    that holds unknowns."""
    return row.kind == "Pullback" and bool(row.unknowns)


def _bundled_pullbacks(rows):
    """The rows with the pullbacks along a law of motion merged into one box on
    the value bundle (`bundled_pullbacks`), each identification kept as its own
    box: it pulls an output back along coordinate functions the block's lines
    define, which no value bundle shares. An identification stands after the
    last row other than a pullback that stood before it, since the merge moves
    a pullback to the place of the first of its group."""
    if not any(_identifies(row) for row in rows):
        return bundled_pullbacks(rows)
    placed = list(bundled_pullbacks([row for row in rows if not _identifies(row)]))
    anchor = None
    for row in rows:
        if _identifies(row):
            at = next((n + 1 for n, held in enumerate(placed) if held is anchor), 0)
            placed.insert(at, row)
            anchor = row
        elif row.kind != "Pullback":
            anchor = row
    return placed


def _with_properties(block, rows, properties):
    """The rows with the address of each property line held by the row of the
    line it is attached to (`properties`, by the property's address): the last
    row other than an `Evaluation` that realizes that line, the `Argmax` of an
    operative maximization. A line that forms no row holds no property, and a
    property attached to it is refused."""
    rows = list(rows)
    for address, owner in properties.items():
        at = next(
            (
                n
                for n in range(len(rows) - 1, -1, -1)
                if owner in rows[n].statements and rows[n].kind != "Evaluation"
            ),
            None,
        )
        if at is None:
            refuse_backward_block(
                block,
                "readable-form",
                address,
                f"the line {address} states a property of the line {owner}, which forms no "
                f"operation of builder {block.name!r}, so no row holds the property; attach it "
                f"to a line that forms an operation, or give it a plain id without a dot",
            )
        rows[at] = dataclasses.replace(rows[at], properties=rows[at].properties + (address,))
    return tuple(rows)


def candidate_systems(ctx, block, cod, lines):
    """The systems of candidate statements of a block (AMD-SG-017 §1), by the
    address of the first statement of each: its statements in file order and
    its unknowns, the candidates of its members in the order of the block's
    header with a marked field directly after the output it marks. The
    candidate statements that share a candidate form one system, and one that
    shares none is a system of one; the grouping is
    `systems_by_shared_candidate`, the one the construction's records and
    the occurrences of a constructed stage read, so that the records, the
    fold and `methodize` find the same systems (AMD-SG-035 §5). The rule of
    the candidates is the one the construction reads on the left side of
    each statement (`line_unknowns.candidates_of_statement`), in identities
    in place of spellings. A property line, attached to another line by a
    dotted id, is in no system and defines nothing (`property_owners`).
    `lines` is the block's lines as `BlockLine` records, in file order."""
    properties = property_owners(address for address, _, _ in lines)
    lines = tuple(line for line in lines if line.address not in properties)
    equations = {
        address: (core.core if isinstance(core, T.Slack) else core) for address, _, core in lines
    }
    aliases, defined = {}, []
    for address, role, core in lines:
        equation = equations[address]
        if role == DOC or _candidate_statement(core) or not isinstance(equation, T.Equation):
            continue
        for identity in ctx.defined(equation, block):
            defined.append(identity)
            if identity not in cod:
                aliases[identity] = equation.rhs

    def mentioned(equation):
        out = []

        def visit(term, seen):
            for identity in ctx.mentioned(term, block):
                if identity in aliases and identity not in seen:
                    visit(aliases[identity], seen | {identity})
                elif identity not in out:
                    out.append(identity)

        visit(equation, frozenset())
        return tuple(out)

    found = []
    for address, role, core in lines:
        if role == DOC or not _candidate_statement(core):
            continue
        found.append(
            (address, candidates_of_statement(mentioned(equations[address]), cod, tuple(defined)))
        )
    return {
        first: CandidateSystem(
            addresses=addresses, unknowns=candidates_of_statement(candidates, cod, ())
        )
        for first, (addresses, candidates) in systems_by_shared_candidate(found).items()
    }


class CandidateSystem(NamedTuple):
    """One system of candidate statements: the addresses of its statements in
    file order and its unknowns."""

    addresses: tuple
    unknowns: tuple


def _candidate_statement(core) -> bool:
    """Whether a line is a candidate statement (AMD-SG-017 §1): an equation,
    with or without a complementarity clause, whose left side is neither a
    name nor a tuple of names."""
    equation = core.core if isinstance(core, T.Slack) else core
    return isinstance(equation, T.Equation) and not names_fields(equation.lhs)


def _explicit(core, targets):
    """Whether a policy line is an explicit equation: one plain name on its
    left side and an equation, not an inequality or a complementarity."""
    return isinstance(core, T.Equation) and isinstance(core.lhs, T.Sym) and len(targets) == 1


def _explicit_lines_aggregation(block, acc, entries):
    """One retained G of adjacent explicit policy lines (AMD-SG-008 §7): the
    perch-marked fields the lines define are its ordered outputs, each a
    function of the states of its perch; a local name is pending arithmetic,
    folded where it is read. The G reads exactly the functions its terms
    read and no formal value input. Named by its last line."""
    ctx = block.ctx
    by_perch = {}
    for entry in entries:
        defined = defined_field(ctx, block.name, entry.core)
        if defined is not None and defined.perch is not None:
            by_perch.setdefault(defined.perch, []).append((entry, defined))
    for perch, fields in by_perch.items():
        _, first_field = fields[0]
        last_line, _ = fields[-1]
        domain = line_domain(block, acc, first_field)
        last = last_line.address
        env = Slice(last, None, domain)
        maps, outputs, shocks, seen = [], [], set(), set()
        for entry, defined in fields:
            refuse_second_definition(block, acc, defined, entry.address, seen)
            seen.add(defined)
            folded = folded_line(block, env, acc, entry)
            check_value_roles(block, acc, entry.address, folded.term)
            maps.append(folded.term)
            outputs.append(ctx.function_wire(defined))
            shocks |= folded.shocks
        statements = tuple(a for a, _, _ in block.lines if a in env.lines)
        cores = tuple(c for a, _, c in block.lines if a in env.lines)
        inputs = tuple(dict.fromkeys(w for term in maps for w in wires_read(term)))
        aggregation_row(
            block,
            env,
            acc,
            Identity("Aggregation", address=last),
            statements=statements,
            inputs=inputs,
            outputs=tuple(outputs),
            maps=tuple(maps),
            cores=cores,
            coordinates=domain.base + shocks_in_header_order(block, env, shocks),
        )
        for (_, defined), wire in zip(fields, outputs):
            acc.wires[defined] = wire


def _relation(block, acc, entry, targets, node, edge):
    """The row of a relational line of the policy builder: an inequality, a
    complementarity or an equation without one plain name on its left side,
    one `Aggregation` whose outputs are its unknowns and whose rule is the
    line's relation, its clause included. Its map is the explicit right side,
    a pointwise function of the functions it reads, written in the
    coordinates of the line's perch. Nothing selects a solution: where the
    line carries a clause, its output takes at each point every value the
    clause admits, a segment where the bound binds, which the queries read
    from the clause the row holds among its equations."""
    ctx = block.ctx
    address, _, core = entry
    for target in targets:
        if target.perch is not None:
            refuse_second_definition(block, acc, target, address)
    domain = line_domain(block, acc, targets[0] if targets else None)
    env = (
        Slice(address, address, domain)
        if node
        else edge
        if domain is block.domain
        else Slice(address, None, domain)
    )
    start = len(acc.rows)
    folded = folded_line(block, env, acc, entry)
    check_value_roles(block, acc, address, folded.term)
    outputs = tuple(ctx.function_wire(target) for target in targets)
    _relation_row(
        block,
        acc,
        Identity("Aggregation", address=address),
        statements=(address,),
        inputs=wires_read(folded.term),
        outputs=outputs,
        maps=(folded.term,),
        cores=(core,),
        unknowns=targets,
        arguments=domain.base + shocks_in_header_order(block, env, folded.shocks),
        node=env.node,
    )
    acc.wires.update(zip(targets, outputs))
    if env.node is not None:
        _evaluate_node(acc, env.node)
        pullbacks_in_header_order(block, acc, start)


def _evaluate_node(acc, address):
    """The `Evaluation` of a `!node` line, appended after the row that
    computes its functions: that row's outputs renamed as its results, which
    the evaluation names as the node's outputs."""
    row = acc.rows[-1]
    results = tuple(
        Identity(row.kind, address=address, field=wire.field, mark="result")
        for wire in row.outputs
    )
    acc.rows[-1] = dataclasses.replace(row, outputs=results)
    acc.rows.append(
        OperatorRow(
            Identity("Evaluation", address=address),
            kind="Evaluation",
            builder=row.builder,
            direction="backward",
            statements=(address,),
            inputs=results,
            outputs=row.outputs,
            arguments=row.arguments,
            node=address,
        )
    )


def _substitute_arguments(term, arguments, stage, owner):
    """A term with a function's formal arguments replaced by the terms
    `arguments` maps them to, a name bound inside the term left alone; a
    selection key replaced by a name, and refused where its argument is no
    name."""
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        return arguments.get(term.symbol.name, term)
    if isinstance(term, T.Key) and isinstance(term.at, str) and term.at in arguments:
        value = arguments[term.at]
        if isinstance(value, T.Sym) and isinstance(value.symbol, T.Constant):
            return T.Key(value.symbol.name)
        raise ConstructionError(
            f"the function argument for selection key {term.at!r} is {to_source(value)}; "
            f"the retained selector requires a name, so its condition needs a construction "
            f"for a computed selection key",
            stage=stage,
            address=owner,
            rule="not-constructed",
        )
    if isinstance(term, T.Operator):
        bound = {s.var if isinstance(s, T.In) else s.name for s in term.subs}
        body_arguments = {name: value for name, value in arguments.items() if name not in bound}
        subs = tuple(
            dataclasses.replace(s, set=_substitute_arguments(s.set, arguments, stage, owner))
            if isinstance(s, T.In)
            else s
            for s in term.subs
        )
        return dataclasses.replace(
            term,
            subs=subs,
            args=tuple(
                _substitute_arguments(arg, body_arguments, stage, owner) for arg in term.args
            ),
        )
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return type(term)(
            *(
                _substitute_arguments(getattr(term, f.name), arguments, stage, owner)
                for f in dataclasses.fields(term)
            )
        )
    if isinstance(term, tuple):
        return tuple(_substitute_arguments(item, arguments, stage, owner) for item in term)
    return term
