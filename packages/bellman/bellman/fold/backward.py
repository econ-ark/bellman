"""The fold of one backward block (AMD-SG-008).

The block is constructed in slices: the slice of each `!node` statement, in
block order, then the block-level slice of its outputs. A slice holds its own
pullback of each value input by the law of motion g of the associated forward
builder, made once; each resolved occurrence E_S(t) once, as an `Aggregation`
row for its integrand unless the integrand is one bare result, then an
`Expectation` row under the conditional distribution the occurrence selects
from the edge that draws its shocks; and a finish: a node's aggregation unless
its term is one bare wire, with the `Evaluation` that creates the node's
output, or the block's one outside aggregation. Each folded result carries its
active shocks, its integrated shocks and the shocks integrated on each of its
paths, from which the refusals `shock-reintroduced` and `shock-observed` are
decided; an aggregation with no value dependency reads a value input formally.
A statement whose value inputs mix a value and a marginal value is refused
naming both. The rows are the sub-builder grain (the construction table's
`sub_builder_rows`); the primitive grain (`primitive_rows`) opens the
sub-builders, keeps their evaluations, composes adjacent pointwise
aggregations and merges parallel boxes on one value bundle (`value_bundles`).

The construction rules of AMD-SG-008 §3 stand after the fold of the block:
`folded_line` reads one line, `reduced_term` one term, and
`_block_outputs` is rule 5.
"""

from __future__ import annotations

import dataclasses
from dataclasses import KW_ONLY, dataclass

from bellman.distributions.conditionals import (
    check_conditioning_covariance,
    conditioning_shocks,
    expectation_words,
    select_conditional,
)
from bellman.distributions.edges import JointDistribution
from bellman.fold.table import BlockRows, OperatorRow
from bellman.fold.value_bundles import (
    bundled_pullbacks,
    primitive_grain_rows,
    pullbacks_after_their_writers,
)
from bellman.fold.wire_terms import (
    BlockLine,
    authored_spelling,
    defined_field,
    defined_name,
    defining_line,
    expectation_nodes,
    is_wire_symbol,
    retained_term_at,
    right_side,
    spelled_with_mark,
    stated_derivative,
    statement_core,
    symbol_occurrences,
    wire_symbol,
    wires_read,
)
from bellman.native.identity import Identity, piece_identity
from bellman.refusals import METHOD_CONDITIONS, ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import DOC, NODE, VALUE_ROLES, WRITTEN_MARK

# --- the fold of one backward block, slice by slice ---


def fold_backward_block(plan, block, records, dom, cod, obligations) -> BlockRows:
    """The rows of one backward value block (AMD-SG-008) at the primitive and
    the sub-builder grain.

    The block is constructed slice by slice — the slice of each `!node`
    statement in block order, then the block-level slice — and its steps stand
    in this order: the node of each `!node` line, the finishing evaluation of
    the block-level slice, the merge of the pullbacks of one slice into one
    box on the value bundle, their order after the boxes whose outputs they
    read, and the retained relations of the lines no row realizes. The rows of
    the primitive grain are then derived from the rows of the sub-builder
    grain by opening the sub-builders, which keeps their evaluations,
    composing adjacent pointwise aggregations and merging parallel boxes on
    one value bundle (`value_bundles.primitive_grain_rows`).
    """
    lines = tuple(
        BlockLine(address=r.address, role=r.role, core=statement_core(plan.items[r.address]))
        for r in records
        if r.role != DOC
    )
    by_spelling = {defined_name(line.core): line for line in lines}
    block = backward_block(plan, block, dom, cod, lines, by_spelling, {})
    acc = WorkingRows([], obligations)
    for address, role, core in block.lines:
        if role == NODE:
            sub_builder_rows(block, Slice(address, address, block.domain), acc, address, core)
    _block_outputs(block, Slice(block.name, None, block.domain), acc)
    acc.rows[:] = pullbacks_after_their_writers(bundled_pullbacks(acc.rows))
    retained_relations(block, acc, acc.rows)
    closed = tuple(acc.rows)
    return BlockRows(primitive=primitive_grain_rows(closed), sub_builder=closed)


def backward_block(plan, name, dom, cod, lines, by_spelling, seeds) -> BackwardBlock:
    """The construction environment of one block, built once before the fold
    from the plan, the block's header and its lines: the law of motion g of
    the forward builder that produces the perch of its value inputs, the
    argument domain of its block-level slice, the coordinates its functions
    are written in, and the owners of the slices that fold each line."""
    ctx = plan.ctx
    dom, cod = tuple(dom), tuple(cod)
    perch_in = next((i.perch for i in dom if ctx.role(i) in VALUE_ROLES), None)
    perch_out = next((i.perch for i in cod), None)
    source = plan.forward_by_target.get(perch_in)
    g = plan.law_of_motion(source) if source else None
    target_coordinates = (
        {
            identity: right_side(core)
            for core in g.equations
            for identity in ctx.defined(core, source)
            if identity in g.outputs
        }
        if g is not None
        else {}
    )
    if g is not None:
        # the coordinates in the order of the header of the block that
        # declares them, which is the order of g's input side (AMD-SG-017 §5.8)
        base = tuple(i for i in g.inputs if ctx.role(i) in ("state", "control"))
        shocks = _transition_shocks(ctx, g)
    else:
        base = ctx.coordinates(perch_in, roles=("state", "control"))
        shocks = ()
    mentioned = tuple(m for _, _, core in lines for m in ctx.mentioned(right_side(core), name))
    controls = tuple(dict.fromkeys(i for i in dom + base + mentioned if ctx.role(i) == "control"))
    written_controls = tuple(i for i in cod if ctx.role(i) == "control")
    states = ctx.coordinates(perch_out, roles=("state",))
    if controls and not written_controls:
        base = states
    domain = _ArgumentDomain(
        perch=perch_out,
        base=base,
        g=g,
        edge=plan.edges.get(source) if source else None,
        target_coordinates=target_coordinates,
        shocks=shocks,
    )
    return BackwardBlock(
        plan=plan,
        ctx=ctx,
        name=name,
        dom=dom,
        cod=cod,
        lines=lines,
        by_spelling=by_spelling,
        perch_out=perch_out,
        Gid=Identity("G", stage=ctx.stage_name, address=name),
        domain=domain,
        states_out=states,
        inputs=tuple(i for i in dom if ctx.role(i) in VALUE_ROLES),
        controls=controls,
        readers=_slices_of_lines(ctx, name, lines, by_spelling, cod, seeds),
        written_controls=written_controls,
    )


def _transition_shocks(ctx, g):
    """The shock names the complete law of motion g reads: the right sides of
    the lines that define its output states, its local definitions followed."""
    block = g.identity.address
    found = []
    for core in g.equations:
        if not any(i in g.outputs for i in ctx.defined(core, block)):
            continue
        term = right_side(core)
        for name, side in symbol_occurrences(term):
            if (
                side is None
                and ctx.role(ctx.resolve(name, block)) == "shock"
                and name not in found
            ):
                found.append(name)
    return tuple(found)


@dataclass(eq=False, kw_only=True)
class _ArgumentDomain:
    """The argument domain of a slice: the perch whose functions the slice
    constructs, the coordinates those functions are written in (`base`, the
    states and controls the law of motion g reads on an edge, the states of
    the perch on a grid), the g composing a function of the target perch that
    is read there (None on the grid of that perch, where such a function is
    read at its own coordinates), the right sides g gives a target state read
    there, the shocks g reads and the edge whose joint distribution its
    expectations select. A backward value block has one domain, its edge. The
    policy builder has its edge, on which objectives and residuals are
    written, and the grid of each perch at which its lines define fields
    (AMD-SG-008 §7): the candidate `c[>]` is a function of the saving a, read
    from the marginal value at a. Exists during one fold."""

    perch: str | None
    base: tuple
    g: object = None
    edge: object = None
    target_coordinates: dict = dataclasses.field(default_factory=dict)
    shocks: tuple = ()

    @property
    def target(self):
        """The perch of the states g produces, None without g."""
        return self.g.outputs[0].perch if self.g is not None and self.g.outputs else None


@dataclass(frozen=True, eq=False, kw_only=True)
class BackwardBlock:
    """The construction environment of one backward block (AMD-SG-008 §3;
    AMD-SG-018 §1): the fifteen fields `backward_block` computes, for the fold
    of a value block and of the policy block alike, before the fold, and every
    primitive step reads. The value is immutable and no step writes into it.

    `plan` is the stage the block stands in and `ctx` the names of that stage;
    `name` is the block's own name; `dom` and `cod` its declared input and
    output identities; `lines` its lines as `BlockLine` records and
    `by_spelling` the line each spelling on a left side defines; `perch_out`
    the perch of its outputs; `Gid` the identity of its G; `domain` the
    argument domain of its block-level slice; `states_out` the states of the
    perch of its outputs; `inputs` the value inputs its header lists and its
    lines read, a listed value input no line reads being no input of the
    block's box (`construction._read_signatures`; AAS, 17 October 2026);
    `controls` the controls its statements and its domain read; `readers` the
    owners of the slices that fold each line.

    `written_controls` are the controls its header declares as outputs. A
    backward block that writes a control is the policy builder, which
    AMD-SG-008 §7 gives rules of its own — several argument domains, and
    kernels that need no formal value input — and the steps read that fact
    from the block's roles here, as `block_rows_of` reads it to choose between
    the two folds. No argument selects a mode and no block identifier selects
    a rule.
    """

    plan: object
    ctx: object
    name: str
    dom: tuple
    cod: tuple
    lines: tuple
    by_spelling: dict
    perch_out: str | None
    Gid: object
    domain: _ArgumentDomain
    states_out: tuple
    inputs: tuple
    controls: tuple
    readers: dict
    written_controls: tuple


def _slices_of_lines(ctx, name, lines, by_spelling, cod, seeds):
    """Each line with the owners of the slices that fold it: a node's own
    address, or the block for the block-level slice (AMD-SG-008 §2). `seeds`
    gives the owner of the slice that folds each line that is not a `!node`
    line and seeds one: empty in a value block, where the nodes and the lines
    defining the block's outputs are the only seeds, and given by the policy
    fold for its own lines (§7)."""
    found = {}
    at = {line.address: line for line in lines}

    def visit(address, owner, seen):
        if address in seen:
            return
        seen.add(address)
        owners = found.setdefault(address, [])
        if owner not in owners:
            owners.append(owner)
        for spelling in dict.fromkeys(symbol_occurrences(right_side(at[address].core))):
            line = by_spelling.get(spelling)
            if line is not None and line.address != address and line.role != NODE:
                visit(line.address, owner, seen)

    for address, role, core in lines:
        if role == NODE:
            visit(address, address, set())
        elif address in seeds:
            visit(address, seeds[address], set())
    for identity in cod:
        line = defining_line(ctx, name, lines, identity)
        if line is not None and line.role != NODE:
            visit(line.address, name, set())
    return found


@dataclass(eq=False)
class WorkingRows:
    """The working state of one fold (AMD-SG-018 §1): the seven members the
    primitive steps write, which each fold function creates, passes to every
    step it calls and reads at its end.

    `rows` are the rows of the block in the order the steps append them;
    `roles` the value role of each wire; `wires` the wire carrying the
    function each perch-marked field of a policy line defines; `node_results`
    and `node_domains` the output and the argument domain of each `!node`
    line; `grids` the argument domain of each perch at which a policy line
    defines a field; `obligations` the conditions list of the whole fold,
    which the caller owns and every block appends to. Exists during one fold.
    """

    rows: list
    obligations: list
    roles: dict = dataclasses.field(default_factory=dict)
    wires: dict = dataclasses.field(default_factory=dict)
    node_results: dict = dataclasses.field(default_factory=dict)
    node_domains: dict = dataclasses.field(default_factory=dict)
    grids: dict = dataclasses.field(default_factory=dict)


class Slice:
    """The construction environment of one slice (AMD-SG-008 §3): the address
    of the node whose output it constructs, or the block for the block-level
    slice; its argument domain; the substituted block value inputs, the
    results of the resolved occurrences and the folds of the lines, each made
    once in the slice; the lines being folded. Exists during one fold."""

    def __init__(self, owner, node, domain):
        self.owner, self.node, self.domain = owner, node, domain
        self.pullbacks, self.occurrences, self.lines = {}, {}, {}
        self.folding = []


def sub_builder_rows(block, env, acc, address, core):
    """The slice of one `!node` statement: its operations, the aggregation
    of its outside arithmetic unless its term is one bare wire, and the
    identity evaluation that creates its output. In the policy builder the
    output of a node defining a perch-marked field is that field's
    function on the states of its perch, with the field's own role; a
    node computing from coordinates alone reads no formal value input."""
    ctx = block.ctx
    defined = defined_field(ctx, block.name, core)
    domain = env.domain
    marked = (
        bool(block.written_controls)
        and defined is not None
        and defined.perch is not None
        and defined not in block.cod
    )
    if marked:
        refuse_second_definition(block, acc, defined, address)
    start = len(acc.rows)
    folded = folded_line(block, env, acc, (address, NODE, core))
    name = defined.field if defined else defined_name(core)[0]
    if marked:
        output = ctx.function_wire(defined)
    else:
        output = Identity(
            "function",
            stage=ctx.stage_name,
            perch=block.perch_out,
            field=name,
            owner=address if defined in block.cod else None,
        )
    coordinates = domain.base + shocks_in_header_order(block, env, folded.shocks)
    role = value_role_of(acc, folded.term) or (ctx.role(defined) if defined in block.cod else None)
    if role is None and not block.written_controls:
        refuse_backward_block(
            block,
            "value-input-role",
            address,
            f"the node {address} defines {name} from no value input, and {name} has "
            f"no declared role; `!node` gives no value role to a line, so its kernel has "
            f"no value or marginal value to act on; read a value input in the line, or "
            f"define an output of the block whose header declares its role",
            write=(
                f"Read a value input on line {address}, or define an output of block "
                f"{block.name!r} whose header declares its role"
            ),
        )
    if is_wire_symbol(folded.term):
        last = folded.term.symbol.name
    else:
        last = Identity("Aggregation", address=address, mark="result")
        statements = tuple(a for a, _, _ in block.lines if a in env.lines)
        cores = tuple(c for a, _, c in block.lines if a in env.lines)
        check_value_roles(block, acc, address, folded.term)
        inputs = wires_read(folded.term) or (
            () if block.written_controls else (_formal(block, env, acc, role, address),)
        )
        aggregation_row(
            block,
            env,
            acc,
            Identity("Aggregation", address=address),
            statements=statements,
            inputs=inputs,
            outputs=(last,),
            maps=(folded.term,),
            cores=cores,
            coordinates=coordinates,
        )
        if not marked:
            acc.roles[last] = role
    acc.rows.append(
        OperatorRow(
            Identity("Evaluation", address=address),
            kind="Evaluation",
            builder=block.name,
            direction="backward",
            statements=(address,),
            inputs=(last,),
            outputs=(output,),
            references=(),
            arguments=coordinates,
            node=address,
        )
    )
    if not marked:
        acc.roles[output] = role
    acc.node_results[defined_name(core)] = (output, folded)
    acc.node_domains[defined_name(core)] = domain
    if marked:
        acc.wires[defined] = output
    pullbacks_in_header_order(block, acc, start)


def refuse_second_definition(block, acc, identity, address, seen=()):
    """A perch-marked field is defined by one policy line
    (rule declared-once)."""
    if identity in acc.wires or identity in seen:
        spelled = identity.field + WRITTEN_MARK.get(identity.perch, "")
        refuse_backward_block(
            block,
            "declared-once",
            address,
            f"the line {address} defines {spelled}, which an earlier line of builder "
            f"{block.name!r} defines already; a policy line defines each field once "
            f"(rule declared-once); remove one definition or give the second field "
            f"its own name",
            write=f"Remove one definition of {spelled}, or give the second field its own name",
        )


def _block_outputs(block, env, acc):
    """The aggregation and the evaluation that end a value block: the right
    sides of the lines that define its declared outputs paired in one
    aggregation, then identified with those outputs."""
    ctx = block.ctx
    start = len(acc.rows)
    outputs, maps = [], []
    for identity in block.cod:
        line = defining_line(ctx, block.name, block.lines, identity)
        if line is None:
            continue
        address, role, core = line
        if role == NODE:
            wire, folded = acc.node_results[defined_name(core)]
            folded = dataclasses.replace(folded, term=wire_symbol(wire))
        else:
            folded = folded_line(block, env, acc, line)
            check_value_roles(block, acc, address, folded.term)
        check_output_shocks(block, env, identity, address, folded)
        outputs.append(identity)
        maps.append(folded.term)
    if not outputs:
        return
    statements = tuple(a for a, _, _ in block.lines if a in env.lines)
    cores = tuple(c for a, _, c in block.lines if a in env.lines)
    results = [row.outputs[0] for row in acc.rows if row.kind == "Expectation"]
    nodes = [wire for wire, _ in acc.node_results.values()]
    read = [w for term in maps for w in wires_read(term)]
    inputs = tuple(
        dict.fromkeys(
            [w for w in read if w not in results and w not in nodes]
            + [w for w in results if w in read]
            + [w for w in read if w in nodes]
        )
    )
    if not inputs:
        inputs = (
            _formal(
                block, env, acc, ctx.role(outputs[0]), statements[0] if statements else block.name
            ),
        )
    choice = {
        identity: Identity("Aggregation", address=block.name, field=identity.field, mark="result")
        for identity in outputs
    }
    aggregation_row(
        block,
        env,
        acc,
        Identity("Aggregation", address=block.name),
        statements=statements,
        inputs=inputs,
        outputs=tuple(choice[o] for o in outputs),
        maps=tuple(maps),
        cores=cores,
        coordinates=block.states_out,
    )
    for identity in outputs:
        acc.roles.setdefault(choice[identity], ctx.role(identity))
    acc.rows.append(
        OperatorRow(
            Identity("Evaluation", address=block.name),
            kind="Evaluation",
            builder=block.name,
            direction="backward",
            statements=(),
            inputs=tuple(choice[identity] for identity in outputs),
            outputs=tuple(ctx.function_wire(identity) for identity in outputs),
            arguments=block.states_out,
            derivatives=stated_derivatives(block, acc, outputs),
        )
    )
    pullbacks_in_header_order(block, acc, start)


def stated_derivatives(block, acc, outputs):
    """The derivative lines of a value block, `D_{m_d}V = 𝑑𝑢(c)`, as the
    Evaluation that writes the value records them (AMD-MB-001 §4.3, D4): for
    each line whose left side is a derivative term of one of `outputs`, the
    identity of the coordinate its subscript names among the states of the
    perch of the outputs, the right-side term, the line's address and its
    source. The reading of each line is the obligation `marginal-reading`,
    listed and checked by nothing. A line whose subscript names no state of
    that perch is left as written, for the typing to refuse."""
    # the written spelling of each output, `V` at the decision perch, `V[<]` at
    # the arrival perch, which the line's left side names
    spellings = {
        identity.field + WRITTEN_MARK.get(identity.perch, ""): identity for identity in outputs
    }
    found = []
    for address, role, core in block.lines:
        if role == DOC:
            continue
        parts = stated_derivative(core)
        if parts is None or parts[0] not in spellings:
            continue
        coordinate = next((s for s in block.states_out if s.field == parts[1]), None)
        if coordinate is None:
            continue
        found.append((coordinate, parts[2], address, to_source(core)))
        acc.obligations.append(
            (
                "marginal-reading",
                (Identity("line", address=address),),
                METHOD_CONDITIONS["marginal-reading"],
            )
        )
    return tuple(found)


def retained_relations(block, acc, rows):
    """`retained-relation` for every operative line of the block that no
    row of the builder realizes (AMD-SG-017 §5.6): an inequality or a
    complementarity whose subjects other lines determine, an inequality
    whose left side is not a name, and a candidate statement with no
    candidate (AMD-SG-018 §1). The file states the relation and the builder
    computes nothing from it, so it is retained on the initial diagram and
    named here. The one entry is the line's identity, so that no obligation
    names a line by a string (AMD-SG-016 §3)."""
    realised = {address for row in rows for address in row.statements}
    # a derivative line is recorded at the Evaluation and is no retained relation
    realised |= {entry[2] for row in rows for entry in row.derivatives}
    for address, role, _ in block.lines:
        if role == DOC or address in realised:
            continue
        acc.obligations.append(
            (
                "retained-relation",
                (Identity("line", address=address),),
                f"The file states the relation at {address}, "
                f"and no operator of the builder realises it.",
            )
        )


def pullbacks_in_header_order(block, acc, start):
    """The pullbacks of a slice that read no box output first, in the
    header's order: they read block inputs only, so the order stays a
    dependency order. A pullback that reads the output of a box of the
    builder stays where the fold placed it and is brought after the last
    box whose output it reads by `pullbacks_after_their_writers`
    (AMD-SG-017 §5.10)."""
    segment = acc.rows[start:]
    written = {wire for row in acc.rows for wire in row.outputs}
    order = {
        ctx_wire: index
        for index, ctx_wire in enumerate(block.ctx.function_wire(i) for i in block.inputs)
    }
    pullbacks = sorted(
        (
            row
            for row in segment
            if row.kind == "Pullback" and not any(wire in written for wire in row.inputs)
        ),
        key=lambda row: order.get(row.inputs[0], len(order)),
    )
    leading = {id(row) for row in pullbacks}
    acc.rows[start:] = pullbacks + [row for row in segment if id(row) not in leading]


# --- the construction rules of AMD-SG-008 §3; rule 5 is `_block_outputs` ---


def folded_line(block, env, acc, entry):
    """The fold of a line's right side in a slice, made once there."""
    address, role, core = entry
    if address in env.lines:
        return env.lines[address]
    if address in env.folding:
        cycle = " → ".join(env.folding[env.folding.index(address) :] + [address])
        refuse_backward_block(
            block,
            "definition-order",
            address,
            f"the lines of builder {block.name!r} read one another in a "
            f"cycle, {cycle}; a line reads only names defined before it "
            f"(AMD-SG-008 §2, rule definition-order); break the cycle",
        )
    env.folding.append(address)
    order = {id(node): n for n, node in enumerate(expectation_nodes(core), 1)}
    folded = reduced_term(block, env, acc, right_side(core), address, order)
    env.folding.remove(address)
    env.lines[address] = folded
    return folded


def reduced_term(block, env, acc, term, address, order):
    """The dispatch of the fold (AMD-SG-005 §1): an expectation operator to
    `expectation_rows`, a symbol to `_reduced_name`, a selection key to
    its resolution, and any other constructor to its folded children
    joined by `_join`."""
    if isinstance(term, T.Operator) and term.head == "E":
        return expectation_rows(block, env, acc, term, address, order)
    if (
        isinstance(term, T.Sym)
        and isinstance(term.symbol, (T.Variable, T.Constant))
        and not is_wire_symbol(term)
    ):
        return _reduced_name(block, env, acc, term, address)
    if isinstance(term, T.Key) and isinstance(term.at, str):
        folded = _reduced_name(block, env, acc, T.Sym(T.Constant(term.at)), address)
        value = folded.term
        if not isinstance(value, T.Sym) or not isinstance(value.symbol, T.Constant):
            refuse_backward_block(
                block,
                "not-constructed",
                address,
                f"the selection key {term.at!r} is defined by {to_source(value)}; the retained "
                f"selector requires a name, so this pullback needs a construction for a "
                f"computed selection key",
            )
        return dataclasses.replace(folded, term=T.Key(value.symbol.name))
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        children = [
            reduced_term(block, env, acc, getattr(term, f.name), address, order)
            for f in dataclasses.fields(term)
        ]
        return _join(block, type(term)(*(child.term for child in children)), children)
    if isinstance(term, tuple):
        children = [reduced_term(block, env, acc, item, address, order) for item in term]
        return _join(block, tuple(child.term for child in children), children)
    return _ReducedTerm(term)


@dataclass(frozen=True)
class _ReducedTerm:
    """The fold of one expression inside a slice (AMD-SG-008 §§3–4): its
    pending scalar term, with a wire symbol for each result it reads; the
    shock names active through its value inputs (`active`) and the shocks it
    reads explicitly outside every expectation, with the address of each read
    (`read`); the shocks already integrated on its producing paths, with the
    occurrence that integrated each (`history`); and its genuine value or
    shock paths, each a description with the shocks integrated on it
    (`paths`). A constant has none of these. Exists during one fold."""

    term: object
    _: KW_ONLY
    active: frozenset = frozenset()
    read: tuple = ()
    history: tuple = ()
    paths: tuple = ()

    @property
    def shocks(self):
        return self.active | frozenset(shock for shock, _ in self.read)


def _reduced_name(block, env, acc, term, address):
    """Rules 1 and 2: a coordinate, a parameter or a constant is pending
    arithmetic; a block value input is its pullback along g, made once
    in the slice; an earlier node's output is its wire; a function a
    policy line defined is read on its domain (`_read`); another line is
    its fold."""
    ctx = block.ctx
    name = term.symbol.name
    side = (
        term.symbol.when.side
        if isinstance(term.symbol, T.Variable) and isinstance(term.symbol.when, T.At)
        else None
    )
    spelling = (name, side)
    if side is None and (name in ctx.function_names or name in ("inf", "∞")):
        return _ReducedTerm(term)
    identity = ctx.resolve(name, block.name, side)
    if identity in acc.wires:
        return _read(block, env, acc, identity, spelling)
    if spelling in acc.node_results:
        if acc.node_domains.get(spelling, env.domain) is not env.domain:
            _refuse_domains(block, env, identity, spelling)
        wire, folded = acc.node_results[spelling]
        return _ReducedTerm(
            wire_symbol(wire), active=folded.shocks, history=folded.history, paths=folded.paths
        )
    line = block.by_spelling.get(spelling)
    if line is not None and line.address != address and line.role != NODE:
        # a perch-marked field is read on its own domain; a local name is
        # folded in the reader's domain
        defined = defined_field(ctx, block.name, line.core)
        if (
            block.written_controls
            and defined is not None
            and defined.perch is not None
            and line_domain(block, acc, defined) is not env.domain
        ):
            _refuse_domains(block, env, identity, spelling)
        return folded_line(block, env, acc, line)
    role = ctx.role(identity)
    domain = env.domain
    if role == "state" and identity in domain.target_coordinates and identity not in domain.base:
        return reduced_term(block, env, acc, domain.target_coordinates[identity], address, {})
    if identity in block.inputs:
        if block.written_controls and identity.perch != (
            domain.perch if domain.g is None else domain.target
        ):
            _refuse_domains(block, env, identity, spelling)
        wire = pullback_wire(block, env, acc, identity)
        label = f"the value input {spelled_with_mark(spelling)}"
        return _ReducedTerm(
            wire_symbol(wire), active=frozenset(domain.shocks), paths=((label, frozenset()),)
        )
    if role in VALUE_ROLES:
        wire = ctx.function_wire(identity)
        acc.roles.setdefault(wire, role)
        return _ReducedTerm(
            wire_symbol(wire),
            paths=((f"the function {spelled_with_mark(spelling)}", frozenset()),),
        )
    if role == "shock" and side is None and domain.edge is not None and name in domain.edge.shocks:
        return _ReducedTerm(
            term,
            read=((name, address),),
            paths=((f"the shock {name} read in {address}", frozenset()),),
        )
    return _ReducedTerm(term)


def _read(block, env, acc, identity, spelling):
    """A function a policy line defines, read in a slice: at its own
    coordinates on the grid of its perch, through the law of motion g on
    the edge whose g produces that perch; refused between other domains."""
    domain = env.domain
    label = f"the function {spelled_with_mark(spelling)}"
    if identity.perch == domain.perch or domain.g is None and domain.perch is None:
        return _ReducedTerm(wire_symbol(acc.wires[identity]), paths=((label, frozenset()),))
    if domain.g is not None and identity.perch == domain.target:
        wire = pullback_wire(block, env, acc, identity)
        return _ReducedTerm(
            wire_symbol(wire), active=frozenset(domain.shocks), paths=((label, frozenset()),)
        )
    _refuse_domains(block, env, identity, spelling)


def _refuse_domains(block, env, identity, spelling):
    """The refusal of a read of a function on coordinates other than the
    slice's, which no law of motion of the stage relates."""
    ctx = block.ctx
    stems = ", ".join(i.field for i in env.domain.base) or "no coordinate"
    own = ", ".join(i.field for i in ctx.coordinates(identity.perch, roles=("state",)))
    refuse_backward_block(
        block,
        "not-constructed",
        env.owner,
        f"the computation of {env.owner} on ({stems}) reads {spelled_with_mark(spelling)}, "
        f"a function of ({own}); two functions on different coordinates have no pointwise "
        f"combination, and no law of motion of the stage relates these coordinates; "
        f"read {spelled_with_mark(spelling)} where it is defined, or "
        f"through a solution relation",
        write=(
            f"Read {spelled_with_mark(spelling)} where it is defined, or through a solution "
            f"relation"
        ),
    )


def line_domain(block, acc, identity):
    """The domain a policy line defining `identity` is written on: the
    block's edge for a local name or a field of the output perch, the grid
    of its perch for a field marked at another perch (`c[>]`)."""
    perch = identity.perch if identity is not None else None
    return (
        block.domain
        if perch is None or perch == block.perch_out
        else perch_domain(block, acc, perch)
    )


def perch_domain(block, acc, perch):
    """The domain of the functions a policy line defines at `perch`: the
    states of that perch, then the multipliers the block declares at it
    (AMD-SG-035 §5, fold B), on which a value input of that perch is read at
    its own coordinates and no law of motion is substituted. `policy.py`
    reads it for a line that defines an output of the block as an explicit
    function of the output perch's states."""
    if perch not in acc.grids:
        acc.grids[perch] = _ArgumentDomain(
            perch=perch, base=block.ctx.perch_coordinates(block.name, perch)
        )
    return acc.grids[perch]


def _join(block, term, children):
    """Rule 3: a pointwise combination. The shocks active through value
    inputs are joined; the already integrated shocks are those of the
    children less the active ones, and an explicit read of one of them is
    refused (AMD-SG-008 §4, rule shock-reintroduced)."""
    active = frozenset().union(*(child.active for child in children)) if children else frozenset()
    read = tuple(dict.fromkeys(pair for child in children for pair in child.read))
    history = tuple(
        dict.fromkeys(
            (shock, where)
            for child in children
            for shock, where in child.history
            if shock not in active
        )
    )
    integrated = {shock for shock, _ in history}
    for shock, where in read:
        if shock in integrated:
            expectations = ", ".join(
                dict.fromkeys(
                    f"the expectation over {shock} on line {getattr(o, 'address', o)}"
                    for s, o in history
                    if s == shock
                )
            )
            refuse_backward_block(
                block,
                "shock-reintroduced",
                where,
                f"the line reads the shock {shock} beside a term in which {expectations} has "
                f"already integrated {shock}, and no other value input of that combination still "
                f"depends on {shock}; a backward function does not read a shock again after "
                f"its expectation; move the read of {shock} inside that expectation, or "
                f"integrate the combination after it",
                write=(
                    f"Move the read of {shock} inside the expectation over {shock}, or "
                    f"integrate the combination after it"
                ),
            )
    paths = tuple(dict.fromkeys(path for child in children for path in child.paths))
    return _ReducedTerm(term, active=active, read=read, history=history, paths=paths)


def expectation_rows(block, env, acc, node, address, order):
    """Rule 4: the fold of the integrand, its pending aggregation unless it
    is one bare result, and one expectation under the conditional
    distribution the occurrence selects (AMD-SG-009 §5), made once in
    the slice for this occurrence."""
    n = order[id(node)]
    if (address, n) in env.occurrences:
        return env.occurrences[(address, n)]
    shocks = tuple(s.var if isinstance(s, T.In) else s.name for s in node.subs)
    label = _label_shock(block, shocks)
    if label is not None:
        return _label_expectation(block, env, acc, node, address, order, label)
    inner = reduced_term(block, env, acc, node.args[0], address, order)
    suffix = _suffix(block, env, address)
    occurrence = Identity("Expectation", address=address, occurrence=n, owner=suffix)
    if any(row.identity == occurrence for row in acc.rows):
        refuse_backward_block(
            block,
            "not-constructed",
            address,
            f"{expectation_words(occurrence, shocks)} would be constructed twice; mark the "
            f"line `!node` so that its result is read by its wire, or write it once for each "
            f"computation that reads it",
            write=(
                "Mark the line `!node`, so that its result is read by its wire, or write the "
                "expectation once for each computation that reads it"
            ),
        )
    given, selection = _selected_conditional(block, env, acc, shocks, inner, occurrence, address)
    integrand, printed = _integrand(block, env, acc, node, inner, address, n, suffix, shocks)
    result = dataclasses.replace(occurrence, mark="result")
    owners = selection.declarations
    acc.rows.append(
        OperatorRow(
            occurrence,
            kind="Expectation",
            builder=block.name,
            direction="backward",
            statements=(address,),
            inputs=(integrand,),
            outputs=(result,),
            references=tuple(owner.identity for owner in owners) + _policies(block),
            distribution=owners[0].identity if owners else None,
            arguments=env.domain.base + shocks_in_header_order(block, env, given),
            node=env.node,
            maps=(wire_symbol(integrand),),
            equations=(printed,),
            integrated=selection.integrated,
            given=selection.given,
            policy=_policies(block),
        )
    )
    acc.obligations.append(
        (
            "expectation-integrability",
            (occurrence, piece_identity(address), node.args[0])
            + tuple(owner.identity for owner in owners),
            f"The integrand {to_source(node.args[0])} at {address} must be integrable for "
            f"{occurrence} under {', '.join(str(owner.identity) for owner in owners)}.",
        )
    )
    acc.roles[result] = acc.roles.get(integrand)
    paths = tuple((label, cover | frozenset(shocks)) for label, cover in inner.paths)
    folded = _ReducedTerm(
        wire_symbol(result),
        active=frozenset(given),
        history=_history_after(inner, shocks, given, occurrence),
        paths=paths,
    )
    env.occurrences[(address, n)] = folded
    return folded


def _selected_conditional(block, env, acc, shocks, inner, occurrence, address):
    """The shocks an expectation conditions on and the conditional
    distribution it selects (AMD-SG-009 §5), from the joint distribution of the
    edge that draws the slice's shocks, or of the owners of its shocks where
    the slice has no edge; the positive definiteness of a conditioning
    covariance block the numbers do not decide is recorded as an obligation."""
    edge = env.domain.edge
    if edge is None:
        owners = block.plan.distributions_of(shocks)
        edge = JointDistribution(
            block=None,
            base=env.domain.base,
            shocks=tuple(s for o in owners for s in o.subjects),
            declarations=owners,
        )

    def refuse(rule, _, message, write=None):
        refuse_backward_block(block, rule, address, message, write=write)

    given = conditioning_shocks(edge, shocks, inner.shocks, {s for s, _ in inner.history})
    selection = select_conditional(edge, shocks, given, occurrence, refuse)
    if not check_conditioning_covariance(selection, {}, occurrence, refuse):
        acc.obligations.append(
            (
                "conditioning-covariance-positive-definite",
                (occurrence,) + tuple(owner.identity for owner in selection.declarations),
                f"The conditioning covariance block of "
                f"{', '.join(str(owner.identity) for owner in selection.declarations)} used by "
                f"{occurrence} must be positive definite.",
            )
        )
    return given, selection


def _integrand(block, env, acc, node, inner, address, n, suffix, shocks):
    """The wire an expectation integrates and the term its row prints: the
    folded integrand itself where it is one bare result; otherwise the result
    of the pending aggregation made for it, whose role is the integrand's value
    role or that of the output its line defines, printed as `E_{…}(w)`."""
    ctx = block.ctx
    role = value_role_of(acc, inner.term)
    if is_wire_symbol(inner.term):
        return inner.term.symbol.name, node.args[0]
    integrand = Identity("Aggregation", address=address, occurrence=n, owner=suffix, mark="result")
    check_value_roles(block, acc, address, inner.term)
    if role is None:
        defined = defined_field(ctx, block.name, retained_term_at(block.lines, address))
        role = ctx.role(defined) if defined in block.cod else None
    inputs = wires_read(inner.term) or (
        () if block.written_controls else (_formal(block, env, acc, role, address),)
    )
    aggregation_row(
        block,
        env,
        acc,
        Identity("Aggregation", address=address, occurrence=n, owner=suffix),
        statements=(address,),
        inputs=inputs,
        outputs=(integrand,),
        maps=(inner.term,),
        cores=(node.args[0],),
        coordinates=env.domain.base + shocks_in_header_order(block, env, inner.shocks),
    )
    acc.roles[integrand] = role or (acc.roles.get(inputs[0]) if inputs else None)
    return integrand, "E_{" + ",".join(shocks) + "}(w)"


def _history_after(inner, shocks, given, occurrence):
    """The shocks integrated on the paths of an expectation's result, each with
    the occurrence that integrated it: those of its integrand's history it does
    not condition on, then its own shocks it does not condition on."""
    return tuple((shock, where) for shock, where in inner.history if shock not in given) + tuple(
        (shock, occurrence) for shock in shocks if shock not in given
    )


def _label_shock(block, shocks):
    """The label shock an expectation integrates alone, or None."""
    if len(shocks) != 1:
        return None
    identity = Identity("field", stage=block.ctx.stage_name, perch="shck", field=shocks[0])
    return identity if block.ctx.labels(identity) else None


def _label_expectation(block, env, acc, node, address, order, label):
    """The expectation over the shock that selects a branch: the
    weighted case operation Σ_j p(j | x) Q_j(x) at the decision state, a term
    of the aggregation that holds the line and no row of its own; the label is
    integrated on every path and read on none. Made once in the slice for
    this occurrence."""
    n = order[id(node)]
    if (address, n) in env.occurrences:
        return env.occurrences[(address, n)]
    inner = reduced_term(block, env, acc, node.args[0], address, order)
    folded = _ReducedTerm(
        T.Operator("E", node.subs, (inner.term,)),
        active=inner.active - {label.field},
        read=tuple((shock, where) for shock, where in inner.read if shock != label.field),
        history=inner.history + ((label.field, address),),
        paths=tuple((text, cover | {label.field}) for text, cover in inner.paths),
    )
    env.occurrences[(address, n)] = folded
    return folded


def aggregation_row(
    block, env, acc, identity, *, statements, inputs, outputs, maps, cores, coordinates
):
    """One `Aggregation` row of the block, a G, appended to `acc.rows`: the
    pointwise map of each output (`maps`) over the wires it reads (`inputs`),
    written in the coordinates of the slice (`coordinates`) and realizing the
    lines at `statements`, whose terms (`cores`) give its parameters and
    conditions; with it, the obligation `aggregation-admissibility` on those
    lines."""
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
            references=(block.Gid,) + _policies(block),
            parameters=ctx.parameters(tuple(cores)),
            definition=block.Gid,
            arguments=tuple(coordinates),
            node=env.node,
            maps=tuple(maps),
            equations=tuple(cores),
            conditions=ctx.conditions(tuple(cores), acc.obligations, block.name, block=block.name),
            policy=_policies(block),
        )
    )
    acc.obligations.append(
        (
            "aggregation-admissibility",
            (identity,) + tuple(piece_identity(a) for a in statements) + tuple(cores),
            f"The equations at {', '.join(str(a) for a in statements)} must define "
            f"{identity} on its declared inputs with values in its declared output sets.",
        )
    )


def pullback_wire(block, env, acc, identity):
    """A block value input, or a function a policy line defines at the
    target perch, composed with the law of motion g of the slice's
    domain, made once in a slice; the function itself on a domain without
    g, where it is read at its own coordinates."""
    if identity in env.pullbacks:
        return env.pullbacks[identity]
    ctx = block.ctx
    g = env.domain.g
    function = ctx.function_wire(identity)
    if ctx.role(identity) in VALUE_ROLES:
        acc.roles.setdefault(function, ctx.role(identity))
    if g is None:
        env.pullbacks[identity] = function
        return function
    wire = dataclasses.replace(
        function,
        mark="g",
        owner=env.owner if env.node is not None or block.written_controls else None,
    )
    by_output = {}
    for core in g.equations:
        for defined in ctx.defined(core, block.name):
            by_output[defined] = right_side(core)
    # a branch value is pulled back along its section, at no policy and on the
    # decision states without the label control, since the section fixes the
    # label
    base = block.plan.bases.get(identity)
    if base is not None:
        _, section = base
        args = tuple(by_output[o] for o in block.plan.sections[base] if o in by_output)
        policies, arguments = (), tuple(i for i in env.domain.base if not ctx.labels(i))
        placed = {"section": section}
    else:
        args = tuple(by_output[o] for o in g.outputs if o in by_output and ctx.role(o) == "state")
        policies, arguments = _policies(block), env.domain.base
        placed = {"policy": policies}
    pulled = T.Equation(ctx.symbol(identity), T.Call(identity.field, args))
    owner = block.name if env.node is None else env.owner
    acc.rows.append(
        OperatorRow(
            Identity("Pullback", address=owner, field=identity.field),
            kind="Pullback",
            builder=block.name,
            direction="backward",
            statements=(),
            inputs=(function,),
            outputs=(wire,),
            references=(g.identity,) + policies,
            definition=g.identity,
            arguments=arguments + shocks_in_header_order(block, env, env.domain.shocks),
            node=env.node,
            equations=(pulled,),
            **placed,
        )
    )
    if ctx.role(identity) in VALUE_ROLES:
        acc.roles[wire] = ctx.role(identity)
    env.pullbacks[identity] = wire
    return wire


def _formal(block, env, acc, role, address):
    """The value input used only formally by an aggregation with no real
    value dependency (AMD-SG-008 §3): a header input with the output's
    role, else the first header value input, substituted in the slice. The
    header inputs are those the block's lines read; a block whose lines read
    no value input keeps every value input its header lists for this use
    (`Declarations.unread_value_inputs`; AAS, 17 October 2026)."""
    if not block.inputs:
        refuse_backward_block(
            block,
            "value-input-role",
            address,
            f"the line {address} reads no value input, and the header of block "
            f"{block.name!r} lists none; a line of a backward block acts on a value or a "
            f"marginal value that its header lists; list a value input in the header and "
            f"read it on the line",
            write=(
                f"List a value input in the header of block {block.name!r} and read it on "
                f"line {address}"
            ),
        )
    chosen = next((i for i in block.inputs if block.ctx.role(i) == role), block.inputs[0])
    return pullback_wire(block, env, acc, chosen)


def _policies(block):
    """The supplied policies read by a value builder, not a policy equation."""
    return (
        ()
        if block.written_controls
        else tuple(block.ctx.function_wire(control) for control in block.controls)
    )


def _suffix(block, env, address):
    """The slice qualifier of a row made from a line that several slices fold,
    each slice constructing its own copy (AMD-SG-008 §2): the owner of the
    slice, which the identity carries as its `owner`, or None."""
    return env.owner if len(block.readers.get(address, ())) > 1 else None


def shocks_in_header_order(block, env, shocks):
    """Shock identities in the order of the block headers, which is the
    order in which a row's arguments are read (AMD-SG-017 §5.8); a shock
    no header lists follows, in the order of the slice's edge and then
    alphabetically. A joint declaration writes its subjects in its own
    order, `(ε_p, ε_β, ν, η) ~ N(…)` beside `ι ~ Bernoulli(…)` on
    `HksWealthDistribution/shocks.bl`, and that order is not the header's."""
    ctx = block.ctx
    listed = {
        identity.field: index
        for index, identity in enumerate(ctx.ports)
        if identity.perch == "shck"
    }
    edge = env.domain.edge
    order = edge.shocks if edge else ()
    rest = [s for s in order if s in shocks and s not in listed]
    rest += sorted(s for s in shocks if s not in order and s not in listed)
    names = sorted((s for s in shocks if s in listed), key=listed.__getitem__) + rest
    return tuple(Identity("field", stage=ctx.stage_name, perch="shck", field=s) for s in names)


# --- the checks ---


def check_output_shocks(block, env, identity, address, folded):
    """The check that an output of the block has no active shock and that
    every shock of the edge is integrated on each of its genuine paths
    (AMD-SG-008 §4; rule shock-observed)."""
    ctx = block.ctx
    edge = env.domain.edge
    output = spelled_with_mark(
        (identity.field, {"arvl": T.Arrival(), "cntn": T.Continuation()}.get(identity.perch))
    )
    residual = [s for s in (edge.shocks if edge else ()) if s in folded.shocks]
    residual += sorted(s for s in folded.shocks if s not in residual)
    base = ", ".join(i.field for i in env.domain.base)
    if residual:
        reads = "; ".join(f"{shock} is read in {where}" for shock, where in folded.read)
        refuse_backward_block(
            block,
            "shock-observed",
            address,
            f"the output {output} of builder {block.name!r} still depends on "
            f"{', '.join(residual)}{' (' + reads + ')' if reads else ''}: a backward builder "
            f"returns a function of ({base}), and every shock of the edge is integrated by an "
            f"expectation on each path to its output (AMD-SG-008 §4, rule shock-observed); write "
            f"E_{{{','.join(residual)}}}(…) around the term that depends on it",
            write=f"Write E_{{{','.join(residual)}}}(…) around the term that depends on it",
        )
    shocks = edge.shocks if edge else ()
    for label, cover in folded.paths:
        missing = [s for s in shocks if s not in cover]
        if missing:
            integrated = ", ".join(s for s in shocks if s in cover) or "no shock"
            refuse_backward_block(
                block,
                "shock-observed",
                address,
                f"the output {output} of builder {block.name!r} is reached from {label} by a path "
                f"that integrates {integrated} and not {', '.join(missing)}; every shock of the "
                f"edge of {edge.block!r} ({', '.join(shocks)}) is integrated on each path to an "
                f"output, and one path's integral does not cover another (AMD-SG-008 §4, D28; "
                f"rule shock-observed); integrate E_{{{','.join(shocks)}}}(…) on that path",
                write=f"Integrate E_{{{','.join(shocks)}}}(…) on that path",
            )


def check_value_roles(block, acc, address, term):
    """The check that a kernel reads values or marginal values, not both
    (AMD-SG-005 §1a rule 4); the candidate controls and coordinates a policy
    line defines carry no value role and enter no such check."""
    found = {}
    for wire in wires_read(term):
        role = acc.roles.get(wire)
        if role in VALUE_ROLES:
            found.setdefault(role, wire)
    if len(found) > 1:
        named = " and ".join(
            f"the {role} {authored_spelling(wire)}" for role, wire in found.items()
        )
        refuse_backward_block(
            block,
            "value-input-role",
            address,
            f"the line reads {named}; a kernel of a backward block acts on "
            f"values or on marginal values and its output has one role, so a line "
            f"mixing the two has no single kernel: write the value and the marginal "
            f"value on separate lines",
            write="Write the value and the marginal value on separate lines",
        )


def value_role_of(acc, term):
    """The one value role of the wires a term reads, or None where it reads
    none or several."""
    found = {acc.roles[w] for w in wires_read(term) if acc.roles.get(w) in VALUE_ROLES}
    return next(iter(found)) if len(found) == 1 else None


def refuse_backward_block(block, rule, address, message, *, write=None):
    """The refusal of a backward block under `rule`, at `address`, with the
    action `write` where the fold establishes the edit."""
    raise ConstructionError(
        message, stage=block.ctx.stage_name, address=address, rule=rule, write=write
    )
