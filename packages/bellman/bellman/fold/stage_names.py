"""The names of one stage as the fold and the queries read them.

`StageNames` holds the sort of every wire (the fields, the shocks, the local
aliases), the fields with their roles and declared sets, the functions, the
distributions and the parameters with their declared sets, and answers the
identity a bare name resolves to in a block, the wires a term reads, the
coordinates of a perch and the labels of a label shock. It is read from the
`WorkingStage` during construction and from a `StageVersion` afterwards;
the two readings are one rule. `family_term_arguments` reads the arguments
a law of motion names and `_latent_shocks` the shocks a stage declares that
no block header lists.

The lines of a block are read here as well, since their reading and the names
read each other: `StageNames.alias_body` reads the roles `lines_of` gives the
lines, and `StageNames.labels` the branches `branches_of` and
`label_coordinate` give a block, while each of those reads a line's names with
a `StageNames`. `lines_of` gives each line of a block with the holder it
stands in, its role, its ordinal and its operator occurrences: during
construction from the block's own record, and afterwards from the `line`
records of the definitions table, which hold a line's tags, its retained term
and its ordinal (AMD-SG-005 §4). `occurrences_of` gives the operator
occurrences of one line.
"""

from __future__ import annotations

from discopy.frobenius import Bubble

from bellman.fold.block_lines import (
    SOLVE,
    blocks_in_file_order,
    forward_chain_reads,
    header_of,
    header_wire_sorts,
    multiplier_sorts,
    parameter_sets,
    setting_sets,
    property_owners,
    wire_sorts,
)
from bellman.fold.declared_sets import binder_sets, definedness_obligation, operand_set
from bellman.fold.policy import candidate_systems
from bellman.fold.wire_terms import (
    BlockLine,
    arithmetic_nodes_with_scopes,
    defined_field,
    defined_name,
    names_no_field,
    right_side,
    symbol_occurrences,
    term_of_name,
)
from bellman.native.identity import Identity, box_identity
from bellman.native.predicates import Member
from bellman.native.records import BlockData, Definition, Line, NodeData, OperatorOccurrence, Sort
from bellman.native.versions import StageVersion
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    ALIAS,
    CONTROL,
    DOC,
    NODE,
    OUTPUT_LINE,
    PERCH_OF_SIDE,
    SHCK,
    VALUE_ROLES,
)
from bellman.typing.line_unknowns import (
    CONSTRAINED_OPTIMUM,
    INTERIOR_ROOT,
    occurrence_paths,
    system_occurrence,
)


class StageNames:
    """The names of a stage as the fold and the queries read them: the sort
    of every wire (the fields, the shocks, the local aliases), the parameters
    with their declared sets, the functions, the distributions, and the
    declared sets of the coordinates (each wire's sort, each parameter's
    definition). Read from the `WorkingStage` during construction and from a
    `StageVersion` afterwards; the two readings are one rule."""

    def __init__(self, stage, definitions=None):
        self.stage_name = stage.name
        # the stage object itself and the fields each block's header names,
        # read once per block: `resolve` resolves a bare name by the header of
        # its own block (AMD-SG-017 §5.5), which the line above, keeping the
        # stage's name alone, does not reach
        self.stage_object, self.header_fields = stage, {}
        # the body of each alias line, by block and by the bare name the line
        # writes: an alias has the set of its body (AMD-SG-017 §4), read once
        # per block
        self.block_aliases = {}
        self.ports = header_wire_sorts(stage)
        self.ports.update(_latent_shocks(stage, self.ports))
        # the multipliers the block bodies declare, fields no header lists
        # (AMD-SG-035 §5), as `_latent_shocks` adds the shocks no header lists
        self.ports.update(multiplier_sorts(stage))
        self.by_name = {}
        for identity in self.ports:
            self.by_name.setdefault(identity.field, []).append(identity)
        self.parameter_sets = parameter_sets(stage)
        self.parameter_names = set(self.parameter_sets)
        # the settings a methods file declares, which no line of the model
        # reads and only a grid factor or a keyword argument names
        self.setting_sets = setting_sets(stage)
        # the definitions table the context reads: the table given, which the
        # construction's fold makes before the working stage holds one, or the
        # constructed stage's own; the working stage alone holds none
        definitions = (
            tuple(definitions)
            if definitions is not None
            else tuple(stage.definitions.values())
            if isinstance(stage, StageVersion)
            else ()
        )
        # the record of each declared multiplier by the identity of its field,
        # empty on the working stage (AMD-SG-035 §5)
        self.multipliers = {
            Identity("field", stage=self.stage_name, perch="cntn", field=d.identity.field): d
            for d in definitions
            if d.kind == "multiplier"
        }
        # the block that declares each multiplier, in declaration order: the
        # block of its record's address on a constructed stage, and during a
        # construction the one site of its field in the working stage's fields
        # table, `(block, None, set)`
        self.multiplier_blocks = (
            {
                identity: record.address.split(".", 1)[0]
                for identity, record in self.multipliers.items()
            }
            if isinstance(stage, StageVersion)
            else {
                identity: sites[0][0]
                for identity, (_, role, _, sites) in stage.data["fields"].items()
                if role == "multiplier"
            }
        )
        # the names a term writes that stand for a definition and for no
        # wire: the functions, the function aliases and the correspondences,
        # and the derived parameters, constants the stage defines from its
        # parameters, which a kernel writes through their definitions
        # (AMD-MT-003, build contract §5)
        self.functions = {
            d.identity.field: d
            for d in definitions
            if isinstance(d, Definition)
            and d.kind in ("function", "function_alias", "correspondence", "derived_parameter")
        }
        self.derived = {
            d.identity.field: d
            for d in definitions
            if isinstance(d, Definition) and d.kind == "derived_parameter"
        }
        self.sets = {
            identity: sort.domain
            for identity, sort in self.ports.items()
            if sort.domain is not None
        }
        self.sets.update(
            {
                Identity("parameter", stage=self.stage_name, field=name): declared
                for name, declared in self.parameter_sets.items()
                if declared is not None
            }
        )
        # the sets the stage defines by name, through which the set algebra
        # resolves a name before it decides an inclusion (AMD-SG-016 §4)
        self.set_terms = {d.identity.field: d.equations[0] for d in definitions if d.kind == "set"}

    @property
    def function_names(self):
        """The names of the functions the stage defines: the keys of
        `functions`, held once."""
        return set(self.functions)

    def role(self, identity):
        """The role of a wire's field, or None for a name that is no wire."""
        return self.ports[identity].role if identity in self.ports else None

    def role_by_name(self, identity):
        """The role of a field, also for a marked occurrence at another perch
        (`m_d[>]`, the decision state written on the continuation grid)."""
        role = self.role(identity)
        if role is None:
            for candidate in self.by_name.get(identity.field, []):
                return self.ports[candidate].role
        return role

    def declared_set(self, identity):
        """The set a field or a parameter is declared in, or None."""
        return self.sets.get(identity)

    def alias_body(self, name, block):
        """The right side of the alias or `!node` line of `block` whose left
        side writes the bare name `name`, or None where the block has no such
        line. An alias has the set of its body (AMD-SG-017 §4), and so has
        the name a `!node` line defines; the body kept here is the term whose
        set `operand_set` reads. The roles are
        those `lines_of` computes, so that a `!doc` line is no alias here
        either."""
        if block is None:
            return None
        held = self.block_aliases.get(block)
        if held is None:
            held = {}
            for box in blocks_in_file_order(self.stage_object):
                if box.name != block:
                    continue
                for _, line in lines_of(self.stage_object, box):
                    # a `!node` line's name has the set of its body as an alias
                    # has, `CE ∈ ℝ₊₊` for `CE = E_{Ψ}(V[>]^(1−γ))^(1/(1−γ))`;
                    # it forms a piece, which an alias does not
                    if line.role not in (ALIAS, NODE) or not isinstance(line.core, T.Equation):
                        continue
                    left = line.core.lhs
                    if isinstance(left, T.Sym) and isinstance(left.symbol, T.Constant):
                        held.setdefault(left.symbol.name, line.core.rhs)
                break
            self.block_aliases[block] = held
        return held.get(name)

    def function_wire(self, identity):
        """The wire carrying a field as a function of its perch's
        state: a value function, a policy function, or a function a
        policy line defines."""
        return Identity(
            "function", stage=self.stage_name, perch=identity.perch, field=identity.field
        )

    def coordinates(self, perch, roles=("state", "control", "shock")):
        """The identities of the fields of the given roles at a perch, in
        declaration order: the bound arguments of the functions there."""
        return tuple(i for i, p in self.ports.items() if p.role in roles and p.perch == perch)

    def labels(self, identity):
        """The labels of the branching block whose label coordinate `identity`
        is, in the set literal's order: a control, or a shock over a finite set
        where the block names no control; `()` for every other field, a
        continuous control included."""
        if self.role(identity) not in ("control", "shock"):
            return ()
        for box in blocks_in_file_order(self.stage_object):
            if (
                identity in tuple(sort.identity for sort in header_of(box).inputs)
                and label_coordinate(self.stage_object, box) == identity
            ):
                return tuple(label for label, _ in branches_of(self.stage_object, box))
        return ()

    def perch_coordinates(self, block, perch):
        """The coordinates of the functions the lines of a policy block define
        at `perch` (AMD-SG-035 §5): the states of that perch, then the
        multipliers `block` declares there, in declaration order."""
        return self.coordinates(perch, roles=("state",)) + tuple(
            identity
            for identity, owner in self.multiplier_blocks.items()
            if owner == block and identity.perch == perch
        )

    def wires(self, term, block, wires, skip_expectations=False):
        """The function wires a term reads: a value function of any perch, or
        the wire `wires` maps it to (its composition with g, a function a
        policy line defines); a state, a control, a shock or a parameter is a
        bound argument, not a wire."""
        out = []
        for identity in self.mentioned(term, block, skip_expectations):
            wire = wires.get(identity)
            if wire is None and self.role(identity) in VALUE_ROLES:
                wire = self.function_wire(identity)
            if wire is not None and wire not in out:
                out.append(wire)
        return tuple(out)

    def symbol(self, identity):
        """The term of a field as a line writes it, under the perch mark of its
        perch, `m_d[>]`, or bare at the decision perch."""
        perch = identity.perch
        name = identity.field
        side = {"arvl": T.Arrival(), "cntn": T.Continuation()}.get(perch)
        return (
            T.Sym(T.Variable(name, T.At(side), 0)) if side is not None else T.Sym(T.Constant(name))
        )

    def resolve(self, name, block, side=None):
        """The identity of an occurrence: a perch-marked field by its perch; a
        bare field by the header of the block the occurrence stands in, which
        names the field by its identity, its stem and its perch together and
        not by its stem alone (AMD-SG-017 §5.5), so that on a stage where an
        arrival state and a continuation state share a stem the bare name of a
        line of the arrival block is the arrival field; where the header of
        that block names the stem at no perch, as in a policy block, whose
        header lists the value functions alone, or at more than one, a bare
        field at the decision perch when one exists, else the unique field of
        that name; parameters, functions and shocks by their kind."""
        if side is not None:
            perch = PERCH_OF_SIDE[type(side)]
            return Identity("field", stage=self.stage_name, perch=perch, field=name)
        if name in self.parameter_names:
            return Identity("parameter", stage=self.stage_name, field=name)
        candidates = self.by_name.get(name, [])
        header = self.header_fields.get(block)
        if header is None:
            header = ()
            for box in blocks_in_file_order(self.stage_object):
                if box.name == block:
                    declared_in, declared_out = header_of(box)
                    header = tuple(sort.identity for sort in declared_in + declared_out)
                    break
            self.header_fields[block] = header
        listed = [identity for identity in candidates if identity in header]
        if len(listed) == 1:
            return listed[0]
        for identity in listed or candidates:
            if self.ports[identity].perch in ("dcsn", "shck"):
                return identity
        if len(candidates) == 1:
            return candidates[0]
        return Identity("unplaced", stage=self.stage_name, field=name)

    def mentioned(self, core, block, skip_expectations=False):
        """The identities of the fields and shocks a term names in `block`,
        each once in order of first mention; functions and parameters are
        not mentioned, and with `skip_expectations` neither is a name
        inside an expectation."""
        out = []
        for name, side in symbol_occurrences(core, skip_expectations):
            if name in self.function_names:
                continue
            identity = self.resolve(name, block, side)
            if identity not in out and identity.kind != "parameter":
                out.append(identity)
        return tuple(out)

    def defined(self, core, block):
        """The identities of the fields a statement of `block` defines on its
        left side; `()` for a statement that names none."""
        if names_no_field(core):
            return ()
        lhs = core.lhs if isinstance(core, (T.Equation, T.Inequality)) else core.core.lhs
        return tuple(self.resolve(n, block, s) for n, s in symbol_occurrences(lhs))

    def parameters(self, cores):
        """The identities of the parameters the terms name, each once in order
        of first mention, a derived parameter a term names standing for the
        parameters its definition reads (AMD-MT-003, build contract §5)."""
        out, seen, pending = [], set(), list(cores)
        while pending:
            core = pending.pop(0)
            for name, side in symbol_occurrences(core):
                if side is not None:
                    continue
                if name in self.parameter_names:
                    identity = Identity("parameter", stage=self.stage_name, field=name)
                    if identity not in out:
                        out.append(identity)
                elif name in self.derived and name not in seen:
                    seen.add(name)
                    pending.append(self.derived[name].equations[0])
        return tuple(out)

    def conditions(self, cores, obligations, owner, block=None, local=None):
        """Membership of every mentioned symbol in its declared set, and the
        definedness predicate of every arithmetic node the declared sets do not
        settle; the obligations the definedness records are appended to
        `obligations`, owned by `owner`.

        The conditions of a function's body are recorded once, on the function,
        with its parameters' declared sets as the operands' sets, and are not
        recorded again where the function is applied: the application records
        `function-argument-domain-inclusion` for each argument the declarations
        do not place within its parameter's set, and that inclusion is what
        carries the body's conditions to the argument (AMD-SG-017 §4)."""
        out = []
        for core in cores:
            domains = binder_sets(core, local or {})
            for name, side in symbol_occurrences(core):
                if name in self.function_names:
                    continue
                if local and name in local:
                    setexpr = local[name]
                else:
                    setexpr = self.sets.get(self.resolve(name, block, side))
                if setexpr is not None:
                    out.append(Member(term_of_name(name, side), setexpr))
            for node, scope in arithmetic_nodes_with_scopes(core, self, block, local or {}):
                held = []
                out.extend(
                    definedness_obligation(
                        node,
                        held,
                        owner,
                        self,
                        lambda term: operand_set(term, self, block, domains),
                    )
                )
                # Equal predicates may occur both inside and outside a binder.
                # Keep each contributing scope until calibration decides them.
                obligations.extend(
                    (*item, tuple(sorted(scope))) if item[0] == "arithmetic-definedness" else item
                    for item in held
                )
        return tuple(dict.fromkeys(out))


def _latent_shocks(stage, ports):
    """The sort of each shock with a declared distribution that no builder
    signature lists, such as ν of `Ψ ~ LogNormal(ν, σ_Ψ)` (AMD-SG-009 §2): the
    sort construction gave the wire of a node that reads it, else a shock
    with the set its child declaration records. The subjects are the laws the
    `WorkingStage` holds while the stage is constructed, and on a
    `StageVersion` the declarations of its definitions table."""
    if not isinstance(stage, StageVersion):
        subjects = [s for group in stage.law_terms for s in group]
    else:
        subjects = [
            s
            for d in stage.definitions.values()
            if d.kind == "distribution"
            for s in d.equations[0].subjects
        ]
    latent = [
        s
        for s in subjects
        if Identity("field", stage=stage.name, perch="shck", field=s) not in ports
    ]
    if not latent:
        return {}
    known = wire_sorts(stage)
    recorded = {}
    if isinstance(stage, StageVersion):
        for d in stage.definitions.values():
            if d.kind == "distribution":
                for name, declared in d.coordinates:
                    if declared is not None:
                        recorded.setdefault(name, declared)
    shocks = {
        name: Identity("field", stage=stage.name, perch="shck", field=name) for name in latent
    }
    return {
        identity: known.get(identity)
        or Sort(identity, "field", perch="shck", role="shock", domain=recorded.get(name))
        for name, identity in shocks.items()
    }


def family_term_arguments(term, ctx):
    """(name, identity) of every state, control and shock a distribution
    declaration's family term reads, in order of first occurrence; parameters
    and functions are not arguments (AMD-SG-009 §1).

    A state is read wherever the family term names it, and no position is
    privileged (AMD-SG-017 §5.2): the third argument of a chain family,
    `DiscreteMarkov(Π, z_vals, z_pre)`, is the state the draw is conditioned
    on, and so is a state written inside the first argument of a two-argument
    call, as `bloom-2009/unit.bl` writes it."""
    found = []
    for name, side in symbol_occurrences(term):
        if side is None and (
            name in ctx.parameter_names or name in ctx.function_names or name in ("inf", "∞")
        ):
            continue
        identity = ctx.resolve(name, None, side)
        if ctx.role(identity) in ("state", "control", "shock") and (name, identity) not in found:
            found.append((name, identity))
    return tuple(found)


# --- the lines of a block, read with the names of the stage ---


def lines_of(stage, box) -> tuple:
    """Each line of a builder with the holder it stands in, in source order,
    as `(holder, Line)` pairs; the holder is the builder's box or, for a
    node's line, the node's own `NodeData` record during construction and the
    node's bubble afterwards, and `node_address` reads its address. During
    construction the builder's own record holds the working lines; afterwards
    the lines are the `line` records of the definitions table whose address
    lies under the block, read into `Line` values with the ordinal each record
    holds and their role and operator occurrences computed from the retained
    term and the blocks; a line marked `!doc` and a line a dotted id attaches
    to another line as its property record no occurrence, as the construction
    records none for them. The bubble of a node is refused: its lines stand in
    its builder, whose lines name the node as their holder."""
    if isinstance(getattr(box, "data", None), BlockData):
        held = [(box, record) for record in box.data.statements_outside_nodes]
        for node in box.data.nodes:
            held.extend((node, record) for record in node.statements)
        held.sort(key=lambda pair: pair[1].ordinal)
        return tuple(held)
    if isinstance(box, NodeData):
        return tuple((box, record) for record in box.statements)
    if not isinstance(box, Bubble):
        raise TypeError(
            f"lines_of reads a builder bubble or a block record; got {type(box).__name__}"
        )
    if box_identity(box).kind == "line":
        raise TypeError(
            f"lines_of reads a builder bubble or a block record; got the bubble of the node "
            f"{box.name!r}, whose lines stand in its builder: read the lines of the builder and "
            f"keep those whose holder has the node address {box.name!r}"
        )
    holders = _node_holders(box)
    ctx = StageNames(stage)
    ports = header_wire_sorts(stage)
    cod = tuple(ob.identity for ob in box.cod.inside)
    records = [
        d for d in stage.definitions.values() if d.kind == "line" and d.identity.block == box.name
    ]
    roles = _line_roles(ctx, box.name, cod, records)
    # the systems of candidate statements, which record one `solve` each, at
    # the first statement (AMD-SG-035 §5)
    systems = candidate_systems(
        ctx,
        box.name,
        cod,
        tuple(
            BlockLine(address=record.address, role=role, core=record.equations[0])
            for record, role in zip(records, roles)
        ),
    )
    later = {address for system in systems.values() for address in system.addresses[1:]}
    properties = property_owners(record.address for record in records)
    out, earlier = [], []
    for record, role in zip(records, roles):
        core = record.equations[0]
        tags = tuple(record.tags)
        system = systems.get(record.address, () if record.address in later else None)
        held = role == DOC or record.address in properties
        operators = (
            ()
            if held
            else occurrences_of(
                stage, box, core, role, earlier, ctx=ctx, ports=ports, system=system
            )
        )
        # a line's address stays the authored address it is written at; its
        # record of the definitions table is keyed by the identity of that
        # address (AMD-SG-016 §3)
        line = Line(
            address=record.address,
            ordinal=record.ordinal,
            role=role,
            tags=tags,
            operators=operators,
            core=core,
        )
        out.append((holders.get(record.address, box), line))
        if not held:
            earlier.append(line)
    return tuple(out)


def _node_holders(box):
    """The bubble of the `!node` line each line of a builder bubble stands in,
    by the line's address; a line of the builder itself has none."""
    holders = {}

    def visit(part, holder):
        for child in part.arg.boxes:
            held = getattr(child, "identity", None)
            if isinstance(child, Bubble):
                visit(child, child if held is not None and held.kind == "line" else holder)
            elif held is not None and held.kind == "line":
                holders.setdefault(child.name, holder)

    visit(box, box)
    return holders


def _line_roles(ctx, block, cod, records):
    """The role of each `line` record of a block, read from its tags and its
    term: `!node`, `!doc`, a line that defines an output of the block, or an
    alias."""
    roles = []
    for record in records:
        tags = tuple(record.tags)
        if "!node" in tags:
            roles.append(NODE)
        elif "!doc" in tags:
            roles.append(DOC)
        elif defined_field(ctx, block, record.equations[0]) in cod:
            roles.append(OUTPUT_LINE)
        else:
            roles.append(ALIAS)
    return tuple(roles)


def occurrences_of(stage, box, core, role, earlier, *, ctx=None, ports=None, system=None) -> tuple:
    """The operator occurrences of a line, in source order, each with the
    path of term fields from the statement's core to it; for an implicit
    statement, the one `solve` occurrence at the empty position. A candidate
    statement records the `solve` of its system (AMD-SG-035 §5): `system` is
    the `CandidateSystem` whose first statement the line is, and its one
    `solve` is `system_occurrence` of the unknowns; `()` for a later statement
    of a system, which records none; None for a line in no system."""
    ctx = ctx or StageNames(stage)
    ports = ports or header_wire_sorts(stage)
    slack = isinstance(core, T.Slack)
    equation = core.core if slack else core
    found = tuple(occurrence_paths(equation.rhs, ("rhs",), slack=slack))
    if system is not None:
        if found or not system or not system.unknowns or role not in (OUTPUT_LINE, NODE):
            return found
        clause = any(
            isinstance(stage.definitions[address].equations[0], T.Slack)
            for address in system.addresses
        )
        return (system_occurrence((identity.field for identity in system.unknowns), clause),)
    if (
        role in (OUTPUT_LINE, NODE)
        and not found
        and _is_implicit_statement(stage, box, equation, earlier, ctx, ports)
    ):
        unknown = to_source(equation.lhs)
        return (
            OperatorOccurrence(
                head=SOLVE,
                subscripts=(unknown,),
                position=(),
                unknown=unknown,
                target=CONSTRAINED_OPTIMUM if slack else INTERIOR_ROOT,
            ),
        )
    return found


def _is_implicit_statement(stage, box, equation, earlier, ctx, ports):
    """Whether an operator-free line that defines an output of its block is
    an implicit statement (spec 0.3c §3.2): its right side, with the block's
    earlier aliases substituted, names no operator and mentions a field at a
    perch later than the left side's, and the forward transition blocks from
    the left side's perch to that perch read an output of this block."""
    lhs = defined_field(ctx, box.name, equation)
    cod = tuple(ob.identity for ob in box.cod.inside)
    if lhs not in cod:
        return False
    aliases = {
        defined_name(line.core): line.core
        for line in earlier
        if line.role == ALIAS
        or (line.role == NODE and defined_field(ctx, box.name, line.core) not in cod)
    }
    mentions, seen, has_operator = [], set(), False

    def visit(term):
        nonlocal has_operator
        if occurrence_paths(term, ()):
            has_operator = True
        for name, side in dict.fromkeys(symbol_occurrences(term)):
            if name in ctx.function_names or name in ctx.parameter_names:
                continue
            spelling = (name, side)
            if spelling not in mentions:
                mentions.append(spelling)
            if spelling in aliases and spelling not in seen:
                seen.add(spelling)
                visit(right_side(aliases[spelling]))

    visit(equation.rhs)
    if has_operator:
        return False
    left = lhs.perch
    listed = tuple(ob.identity for ob in header_of(box).inputs) + cod
    perches = set()
    for name, side in mentions:
        if side is not None:
            perches.add(PERCH_OF_SIDE[type(side)])
            continue
        role = next((ports[i].role for i in listed if i in ports and i.field == name), None)
        if role == CONTROL:
            perches.add("dcsn")
        elif role == "shock":
            continue
        else:
            found = [i for i in listed if i.field == name and i.perch != SHCK]
            if found:
                perches.add(found[0].perch)
    return any(
        forward_chain_reads(stage, left, perch, set(cod), ports)
        for perch in perches
        if perch is not None
    )


def branches_of(stage, box) -> tuple:
    """The branches of one block, `((label, fields), …)` in label order, each
    label with the continuation fields its nested block writes, in the order
    of the block's outputs: during construction the labels the block's record
    holds and the typed outputs of the lines under each label; afterwards the
    block's `line` records, a line's label the middle segment of its address
    and its fields what its term defines. `()` without branches."""
    cod = tuple(ob.identity for ob in box.cod.inside)
    data = getattr(box, "data", None)
    if isinstance(data, BlockData):
        written = {}
        for record in data.statements_outside_nodes:
            label = Identity("line", address=record.address).branch
            written.setdefault(label, set()).update(port.identity for port in record.outputs)
        return tuple(
            (label, tuple(i for i in cod if i in written.get(label, ())))
            for label in data.branch_labels
        )
    if not isinstance(box, Bubble):
        return ()
    ctx = StageNames(stage)
    found = {}
    for _, line in lines_of(stage, box):
        label = Identity("line", address=line.address).branch
        if label is None or line.core is None:
            continue
        found.setdefault(label, set()).update(ctx.defined(line.core, box.name))
    return tuple((label, tuple(i for i in cod if i in held)) for label, held in found.items())


def label_coordinate(stage, box):
    """The coordinate at which the lines of a branching block are read, its
    label coordinate: the control its header names among its inputs or, where
    it names no control, the shock over a finite set it names,
    `s : {survive, die}`; None for a block without branches. The rule
    is written here and nowhere else: the fold's plan, the context's `labels`
    and the conservation of mass read it."""
    ports = header_wire_sorts(stage)
    inputs = tuple(sort.identity for sort in header_of(box).inputs if sort.identity in ports)
    found = next((i for i in inputs if ports[i].role == "control"), None)
    if found is None:
        found = next(
            (
                i
                for i in inputs
                if ports[i].role == "shock" and isinstance(ports[i].domain, T.FiniteSet)
            ),
            None,
        )
    return found if found is not None and branches_of(stage, box) else None
