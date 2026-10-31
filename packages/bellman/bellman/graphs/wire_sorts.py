"""The wire table of a stage and the wiring of a graph by the identities of
its wires.

`WireTable` reads one stage, the working stage while it is constructed or a
stage version, with its construction table: the sort of every field and shock
wire (`ports`) and of every other wire, the blocks with the direction of each,
the policy builders, the lines of each authored node, the row that writes each
wire, the wires whose functions take a set of values at each point
(`correspondence_wires`), and, for each builder, the rows of its operators
with the wires they read and write (`WiredRow`), and the builder's inputs and
outputs. The sort of a wire a row writes is made once, when the wire is first
asked for.

`connect` wires boxes into a graph by the identities of their wires, one
spider per identity: the one wiring of every graph of the semgraph. A box it
wires is a `WiredBox`, the box with the identities of the wires it reads and
writes, as `wired_boxes` reads them back from a graph. `needed` keeps the
boxes on a path to an output, the combined grain of either kind of graph;
`group_inputs_outputs` gives the inputs and outputs of the bubble around a
group of boxes, and `captures` the wires a builder reads that none of its rows
writes and its declaration does not list. The functions of
`initial_diagrams.py` and `builders_graphs.py` build the four graphs and their
grains from the table, each taking it as its first argument, `wires`.
"""

from __future__ import annotations

import copy
import weakref
from typing import NamedTuple

from discopy.frobenius import Ty

from bellman.distributions.families import FAMILY_ARGUMENTS
from bellman.fold.block_lines import (
    block_direction,
    blocks,
    header_wire_sorts,
    is_node,
    node_address,
    parameter_sets,
    perches_of,
    wire_sorts,
)
from bellman.fold.conditions import parameters_named
from bellman.fold.stage_names import branches_of, lines_of
from bellman.fold.wire_terms import wires_read
from bellman.native.hypergraphs import BellmanHypergraph
from bellman.native.identity import Identity
from bellman.native.records import Sort
from bellman.refusals import NotConstructed
from bellman.syntax import terms as T
from bellman.syntax.vocabulary import VALUE_ROLES

# --- the wire table ---

# the roles of the fields that are bound arguments of the functions of the
# backward builders graph, not wires
BOUND_ROLES = ("state", "shock")
# the operator kinds of a forward builder, which the rows of a backward builder
# leave out
MEASURE_KINDS = ("DistributionExtension", "PolicyInsertion", "Pushforward")


class WiredRow(NamedTuple):
    """One row of a builder's operators with the identities of the wires it
    reads and writes, in order: an entry of `WireTable.rows`."""

    row: object
    inputs: tuple
    outputs: tuple


class WireTable:
    """The wire table of one stage, read from the stage and its construction
    table: the sort of every wire, the blocks with the direction of each, and
    the rows and the inputs and outputs of each builder. The functions of
    `initial_diagrams.py` and `builders_graphs.py` build the graphs and their
    grains from it, each taking the table as its first argument, `wires`."""

    def __init__(self, stage, table):
        # The wire table is kept in the cache of the version it was made from,
        # so a strong reference here would keep that version alive for as long
        # as the table lives; the reference is weak, so that the version is
        # collected when its last other reference goes. A version made from
        # that one holds the table `for_version` makes, whose reference names
        # it.
        self._stage, self.table = weakref.ref(stage), table
        self.name = stage.name
        self.ports = header_wire_sorts(stage)  # the sort of every field and shock wire
        # every wire's sort, the local aliases included; a produced wire's is
        # added when asked for
        self.sorts = wire_sorts(stage)
        self.parameter_sets = parameter_sets(stage)
        self.roles = {}
        self.blocks, self.refusal = (), None
        try:
            self.blocks = tuple(blocks(stage))
        except NotConstructed as error:
            self.refusal = error
        self.direction, self.refusals = {}, {}
        for box in self.blocks:
            try:
                self.direction[box.name] = block_direction(stage, box, self.ports)
            except NotConstructed as error:
                self.refusals[box.name] = error
        self.box_of = {box.name: box for box in self.blocks}
        # the fields a bound block's header adds to a builder's outputs, by
        # builder (`add_outputs`); none under AMD-MB-001, whose blocks add no
        # field to a builder
        self.added_outputs = {}
        # the continuation fields of each branch of each block, keyed by
        # (block, label), the key `_function_sort` reads from a pullback's row
        self.sections = {
            (box.name, label): fields
            for box in self.blocks
            for label, fields in branches_of(stage, box)
        }
        # the policy builders: the backward blocks whose outputs are controls
        self.policy_blocks = {
            box.name
            for box in self.blocks
            if any(self.declared_role(ob.identity) == "control" for ob in box.cod.inside)
        }
        self.initial = None
        self.nodes = {}  # block -> {node address: its line addresses}
        for box in self.blocks:
            groups = {}
            for holder, record in lines_of(stage, box):
                if is_node(holder):
                    groups.setdefault(node_address(holder), []).append(record.address)
            self.nodes[box.name] = groups
        # the row that writes each wire: a row of the table, else a row of a
        # closed sub-builder
        self.produced = {o: op for op in table.primitive_rows for o in op.outputs}
        for rows in dict(table.sub_builder_rows).values():
            for op in rows:
                for o in op.outputs:
                    self.produced.setdefault(o, op)
        # the wires whose functions take a set of values at each point
        self.correspondences = correspondence_wires(table.primitive_rows)

    def add_ports(self, sorts):
        """The table with the sorts `sorts` of fields no stage file header
        lists, which the header of a bound method block declares
        (`dV[>] : ℝ₊₊ @ !mrgnvl`), among the sorts of its field wires; a
        field the stage file lists keeps its own sort. The two mappings are
        made anew, so that no mapping another answer holds is written."""
        added = {sort.identity: sort for sort in sorts if sort.identity not in self.ports}
        if added:
            self.ports = {**self.ports, **added}
            self.sorts = {**self.sorts, **added}

    def add_outputs(self, builder, sorts):
        """The table with the fields among `sorts` that stand at the perch of
        the outputs of the backward builder `builder` among its outputs, the
        fields a bound block's header adds, none under AMD-MB-001, whose
        marginal block adds no field (specification 0.6 §5). The
        mapping is made anew, so that no mapping another answer holds is
        written."""
        box = self.box_of.get(builder)
        if box is None:
            return
        perch = perches_of(box, self.ports)[1]
        added = tuple(sort.identity for sort in sorts if sort.perch == perch)
        if added:
            self.added_outputs = {**self.added_outputs, builder: added}

    def for_version(self, stage, copier):
        """This wire table for `stage`, a version holding the records of the
        one it was made from: every entry made by `copier`, the tables it
        fills as it is read rebuilt as tables of its own, and the weak
        reference naming `stage`. `copier` is the copier of the walk of
        `hypergraphs.copy_native` that made `stage`, so that the entries refer
        to its objects, or the identity where `replace_stage` gave `stage` the
        same records."""
        made = object.__new__(WireTable)
        made.__dict__.update(
            {
                name: _rebuilt(value, copier)
                for name, value in vars(self).items()
                if name != "_stage"
            }
        )
        made._stage = weakref.ref(stage)
        return made

    @property
    def stage(self):
        """The stage this wire table was made from, refused once that stage
        has been collected."""
        stage = self._stage()
        if stage is None:
            raise ReferenceError(
                f"the rendering of the stage {self.name!r} outlived the version it was made from"
            )
        return stage

    # --- the sorts of the wires ---

    def carries_correspondence(self, identity):
        """Whether the function a wire carries takes a set of values at each
        point of its domain, a correspondence `Xa ⇉ ℝ₊₊`, and not one value
        (`correspondence_wires`)."""
        return identity in self.correspondences

    def tensor_of_sorts(self, identities):
        """The DisCoPy type of ordered wires: the tensor of their sorts."""
        return Ty(*(self.sort_of(i) for i in identities))

    def sort_of(self, identity):
        """The sort of a wire: a field's own sort, or the sort of a wire a row
        writes, made once. A function wire carries the role of the value it
        carries and is free in the bound coordinates of the row that writes it
        (`arguments`); a declared input function, which no row writes, is free
        in the states of its perch, and a branch value in the fields of its
        branch, the section its pullback composes with; a measure wire carries
        a measure at its perch."""
        if identity in self.sorts:
            return self.sorts[identity]
        producer = self.produced.get(identity)
        arguments = tuple(getattr(producer, "arguments", ()))
        if identity.kind in ("function", "choice") and identity.perch is not None:
            sort = self._function_sort(identity, producer, arguments)
        elif identity.kind == "measure":
            sort = Sort(identity, "measure", perch=identity.perch, role="measure")
        elif identity.kind == "distribution-extended-measure":
            sort = Sort(identity, "measure", role="measure")
        elif identity.is_result:
            sort = self._result_sort(identity, producer, arguments)
        else:
            sort = Sort(identity, "field", role="derived")
        self.sorts[identity] = sort
        return sort

    def _function_sort(self, identity, producer, arguments):
        """The sort of a function wire at a perch: the role and the declared
        set of the field it carries, free in `arguments`, the bound
        coordinates of the row that writes it."""
        field = self.field_of(identity.stage, identity.perch, identity.field)
        if producer is None:
            # a branch value is free in its base's fields, read from the
            # section of the pullback that reads it
            held = {
                (op.definition.address, op.section)
                for op in self.table.primitive_rows
                if op.kind == "Pullback" and op.section is not None and identity in op.inputs
            }
            arguments = (
                self.sections[held.pop()]
                if len(held) == 1
                else tuple(
                    i
                    for i, s in self.ports.items()
                    if s.perch == identity.perch and s.role == "state"
                )
            )
        role = field.role if field is not None else self.role_of(identity)
        return Sort(
            identity,
            "function",
            perch=identity.perch,
            role=role,
            domain=field.domain if field is not None else None,
            coordinates=arguments,
            # the coordinates in which the writing Evaluation records a stated
            # derivative of the value (AMD-MB-001 §5.1)
            derivatives=tuple(entry[0] for entry in getattr(producer, "derivatives", ())),
        )

    def _result_sort(self, identity, producer, arguments):
        """The sort of a result wire: a control of the same name where a
        policy builder writes it, else a function with the role `role_of`
        reads back, free in `arguments`."""
        field = next(
            (
                field
                for field in self.ports.values()
                if producer is not None
                and producer.builder in self.policy_blocks
                and field.identity.field == identity.field
                and field.role == "control"
            ),
            None,
        )
        return Sort(
            identity,
            "function",
            role=field.role if field else self.role_of(identity),
            perch=field.perch if field else None,
            domain=field.domain if field else None,
            coordinates=arguments,
        )

    def field_of(self, stage_name, perch, name):
        """The sort of the field a function wire carries: the field at the
        wire's perch, else the field of that name at another perch, whose
        function a policy line defines at the wire's perch (`c[>]`, the
        candidate control on the saving grid; `m_d[>]`, the resources there);
        None for a local name."""
        field = self.ports.get(Identity("field", stage=stage_name, perch=perch, field=name))
        if field is None:
            field = next(
                (
                    sort
                    for identity, sort in self.ports.items()
                    if identity.field == name and sort.role != "shock"
                ),
                None,
            )
        return field

    def role_of(self, identity):
        """The role of a produced function wire: the role of the field it
        carries, or the role of the value inputs of the row that produces it,
        read back to a field. A name a policy line defines at a perch that no
        header declares, `c_save[>]`, carries no value role."""
        if identity in self.roles:
            return self.roles[identity]
        field = self.ports.get(identity)
        named = False
        if field is None:
            if identity.kind in ("function", "choice") and identity.perch is not None:
                named = True
                field = self.field_of(identity.stage, identity.perch, identity.field)
        producer = self.produced.get(identity)
        if field is not None:
            role = field.role
        elif named and producer is not None and producer.builder in self.policy_blocks:
            role = None
        else:
            self.roles[identity] = None  # a cycle reads as no role
            found = {
                r
                for r in (self.role_of(i) for i in self._value_reads(identity, producer))
                if r in VALUE_ROLES
            }
            role = next(iter(found)) if len(found) == 1 else None
        self.roles[identity] = role
        return role

    def _value_reads(self, identity, producer):
        """The wires whose roles give the role of `identity`, a wire
        `producer` writes: the inputs of the row, or, where the row writes one
        result per component of a value bundle, the inputs of that result's
        own component."""
        reads = getattr(producer, "inputs", ())
        kind = getattr(producer, "kind", None)
        if (
            kind == "Aggregation"
            and identity in producer.outputs
            and len(producer.maps) == len(producer.outputs)
        ):
            # an aggregation on a value bundle has one map per component, and
            # each component's role is the role of the value inputs its own
            # map reads, not of every input of the box
            return wires_read(producer.maps[producer.outputs.index(identity)]) or reads
        if kind in ("Pullback", "Expectation", "Evaluation") and identity in producer.outputs:
            # one kernel applied to every component of a value bundle writes
            # one result per component it reads, in the components' order, so
            # a result's role is the role of the value input at its own place
            # and not the union over the box's inputs; otherwise the merged box
            # of the primitive grain would record no role for a wire the other
            # grains carry with its own role
            values = [wire for wire in producer.inputs if self.role_of(wire) in VALUE_ROLES]
            if len(values) == len(producer.outputs):
                return (values[producer.outputs.index(identity)],)
        return reads

    # --- the rows of a builder and its inputs and outputs ---

    def rows(self, direction, closed=False):
        """(block, [`WiredRow`]) per builder of that direction, in source
        order; with ``closed`` the rows of a backward block with its
        sub-builders closed."""
        out = []
        for box in self.blocks:
            block = box.name
            if block in self.refusals:
                raise self.refusals[block]
            if self.direction[block] != direction:
                continue
            out.append(
                (
                    box,
                    self._forward_rows(box)
                    if direction == "forward"
                    else self._backward_rows(block, closed),
                )
            )
        return out

    def _forward_rows(self, box):
        """The rows of a forward builder, each on the measure wires it reads
        and writes."""
        rows = []
        # each measure wire is a distinct measure on its own coordinates: the
        # states of the source perch, then the control the policy inserts, then
        # each shock an extension adds, parents first; the push-forward through
        # g gives the measure on the states of the target perch
        perch_from, perch_to = perches_of(box, self.ports)
        current = Identity("measure", stage=self.name, perch=perch_from)
        coordinates = self.perch_states(perch_from)
        self.add_measure_sort(current, perch_from, coordinates)
        for op in self.table.by_builder(box.name):
            if op.kind == "PolicyInsertion":
                # the push-forward at a policy refers to the policy from its
                # insertion box and is wired to it at no level: the box reads
                # the measure alone
                coordinates = coordinates + tuple(op.outputs)
                nxt = Identity("measure", stage=self.name, perch=perch_from, mark="with-policy")
                self.add_measure_sort(nxt, perch_from, coordinates)
                rows.append(WiredRow(op, (current,), (nxt,)))
                current = nxt
            elif op.kind == "DistributionExtension":
                self.check_distribution(op)
                coordinates = coordinates + tuple(op.inputs)
                # the extension's output is named by its input and the
                # distribution it extends by, `μ≺⊗P_ψ⊗P_ξ`: the input measure
                # is the owner of the new one
                nxt = Identity(
                    "measure",
                    stage=self.name,
                    perch=perch_from,
                    mark="with-distribution",
                    subjects=op.identity.subjects,
                    owner=current,
                )
                self.add_measure_sort(nxt, perch_from, coordinates)
                rows.append(WiredRow(op, (current,), (nxt,)))
                current = nxt
            elif op.kind == "Pushforward":
                rows.append(WiredRow(op, (current,), self.measures_written(box, perch_to)))
        return rows

    def _backward_rows(self, block, closed):
        """The rows of a backward builder on the wires they read and write,
        the forward operators left out."""
        return [
            WiredRow(op, op.inputs, op.outputs)
            for op in self.table.by_builder(block, grain="node" if closed else "primitive")
            if op.kind not in MEASURE_KINDS
        ]

    def perch_states(self, perch):
        """The states of a perch in first-listing order: the coordinates of the
        measure at that perch, one tuple for the builder that ends there and
        the builder that starts there."""
        return tuple(
            identity
            for identity, sort in self.ports.items()
            if sort.perch == perch and sort.role == "state"
        )

    def add_measure_sort(self, identity, perch, coordinates):
        """The sort of a measure wire of the forward builders graph, on
        `coordinates` in order and each once, written into the table's
        sorts."""
        self.sorts[identity] = Sort(
            identity,
            "measure",
            perch=perch,
            role="measure",
            coordinates=tuple(dict.fromkeys(coordinates)),
        )

    def check_distribution(self, op):
        """The check that the distribution the extension `op` extends by is
        written with a family of `FAMILY_ARGUMENTS`, whose result set is
        declared; any other family is refused under the rule
        `not-constructed`. A call among the family's arguments does not change
        the family: a `LogNormal` component inside a `Mixture` is an argument
        of the mixture, and the mixture is the family."""
        declaration = next(
            (d for d in self.table.definitions if d.identity == op.distribution), None
        )
        for equation in declaration.equations if declaration is not None else ():
            equation = equation.law if isinstance(equation, T.Law) else equation
            if isinstance(equation, T.Call) and equation.fun not in FAMILY_ARGUMENTS:
                raise NotConstructed(
                    f"the forward measures are not constructed: the distribution of "
                    f"{', '.join(i.field for i in op.inputs)} is written with the family "
                    f"{equation.fun!r}, whose result set is not declared "
                    f"(opaque:{Identity('external', field=equation.fun, mark='result')}); under "
                    f"the rule not-constructed the forward measure is extended only by the "
                    f"families {', '.join(FAMILY_ARGUMENTS)}; write the declaration with one of "
                    f"those families, or read the backward builders graph, which does not use it",
                    stage=self.name,
                    address=(
                        declaration.address
                        if declaration is not None and declaration.address
                        else op.identity
                    ),
                    rule="not-constructed",
                )

    def measures_written(self, box, perch):
        """The measures a forward builder writes at `perch`: one on the states
        of the perch, or, where the builder's lines are read at labels, one on
        each label's continuation fields, `μ_keep≻`."""
        found = branches_of(self.stage, box)
        measures = (
            [
                (Identity("measure", stage=self.name, perch=perch, field=label), fields)
                for label, fields in found
            ]
            if found
            else [(Identity("measure", stage=self.name, perch=perch), self.perch_states(perch))]
        )
        for identity, coordinates in measures:
            self.add_measure_sort(identity, perch, coordinates)
        return tuple(identity for identity, _ in measures)

    def builder_inputs_and_outputs(self, box, direction, rows):
        """The declared inputs and outputs of a builder of that direction,
        then the captures: identities its rows consume that nothing inside
        produces and the declaration does not list."""
        if direction == "forward":
            perch_from, perch_to = perches_of(box, self.ports)
            # the measure alone: the push-forward at a policy answers the
            # measure it reads and the measure it writes
            return (
                (Identity("measure", stage=self.name, perch=perch_from),),
                self.measures_written(box, perch_to),
            )
        declared_inputs = tuple(ob.identity for ob in box.dom.inside)
        declared_outputs = tuple(ob.identity for ob in box.cod.inside)
        declared_outputs += self.added_outputs.get(box.name, ())
        if direction == "backward":
            # the value functions of the declared fields, the wires of the
            # backward builders graph (`backward_inputs`, `backward_outputs`)
            declared_inputs = self.backward_inputs(declared_inputs)
            declared_outputs = tuple(dict.fromkeys(self.backward_outputs(declared_outputs)))
        produced = {o for _, _, outs in rows for o in outs}
        consumed = [i for _, ins, _ in rows for i in ins]
        return declared_inputs + captures(consumed, produced, declared_inputs), declared_outputs

    def backward_inputs(self, declared):
        """The declared inputs of a backward builder, or of the backward
        builders graph, as the wires that graph carries: the value function of
        each declared field that is not a state, a shock or a control. A
        state or a shock is a bound argument of the functions, and a control
        the header names is the coordinate at which the block is read."""
        return tuple(
            self.to_function(i)
            for i in declared
            if self.declared_role(i) not in BOUND_ROLES + ("control",)
        )

    def backward_outputs(self, declared):
        """The declared outputs of a backward builder, or of the backward
        builders graph, as the wires that graph carries: the value function of
        each declared field that is not a state or a shock, and for a control
        the policy the policy builder returns."""
        return tuple(
            self.policy_output(self.to_function(i))
            for i in declared
            if self.declared_role(i) not in BOUND_ROLES
        )

    def to_function(self, identity):
        """The function wire at the perch of a value or control field, and
        `identity` itself for any other wire."""
        port = self.ports.get(identity)
        if (
            port is not None
            and port.role in VALUE_ROLES + ("control",)
            and port.perch in ("cntn", "arvl", "dcsn")
        ):
            return Identity("function", stage=self.name, perch=port.perch, field=identity.field)
        return identity

    def declared_role(self, identity):
        """The role a field's sort declares, and None for a wire that is no
        field."""
        port = self.ports.get(identity)
        return port.role if port is not None else None

    def policy_output(self, identity):
        """The wire of the policy a policy builder returns for the function
        `identity`, the output of the builder's evaluation with the same field
        name, as distinct from the policy function the builder reads;
        `identity` itself where no such output is."""
        if identity.kind == "function":
            for row in self.table.primitive_rows:
                if row.kind == "Evaluation" and row.builder in self.policy_blocks:
                    for output in row.outputs:
                        if output.field == identity.field:
                            return output
        return identity

    # --- the parameters ---

    def parameters(self, direction):
        """The sorts of the parameters the retained terms of the builders of
        that direction name, directly or through the functions they call, in
        order of first appearance (`conditions.parameters_named`): the
        parameters the record of a builders graph lists (`semgraph.record`)."""
        rows = [op for _, rows in self.rows(direction) for op, _, _ in rows]
        return tuple(
            self.parameter_sort(Identity("parameter", stage=self.name, field=name))
            for name in parameters_named(self.stage, rows)
        )

    def parameter_sort(self, identity):
        """The sort of a parameter for a graph's list of the parameters its
        equations name: no wire carries it; its declared set is its
        definition's."""
        if identity not in self.sorts:
            self.sorts[identity] = Sort(
                identity, "field", role="parameter", domain=self.parameter_sets.get(identity.field)
            )
        return self.sorts[identity]


def _rebuilt(value, copier):
    """One entry of a wire table made for another version
    (`WireTable.for_version`): a dict, a list, a set and a tuple rebuilt of the
    same type from their entries, since the table fills some of them as it is
    read; a refusal copied without its notes, since a caller adds a note naming
    its own position to the refusal it catches and the copy begins a list of
    its own; every other value made by `copier`."""
    if type(value) is dict:
        return {copier(key): _rebuilt(item, copier) for key, item in value.items()}
    if type(value) in (list, set, tuple):
        return type(value)(_rebuilt(item, copier) for item in value)
    if isinstance(value, BaseException):
        made = copy.copy(value)
        made.__dict__.pop("__notes__", None)
        return made
    return copier(value)


def captures(consumed, produced, declared):
    """The captures of a builder or of a builders graph: the identities of
    `consumed`, once each and in order, that nothing of `produced` writes and
    `declared`, the declared inputs, does not list."""
    return tuple(dict.fromkeys(i for i in consumed if i not in produced and i not in declared))


# --- the wires that carry a correspondence ---


def correspondence_wires(rows):
    """The wires, among those `rows` write, whose functions take a set of
    values at each point of their domain, a correspondence, and not one
    value. A relational line written with a clause, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂
    a >= 0`, admits at each saving every value its clause admits, a segment
    where the bound binds, so the one output of its `Aggregation` carries a
    correspondence (`_admits_a_set`). An `Aggregation` or a `Pullback` that
    maps its inputs pointwise and reads such a wire takes at each point the
    values its map gives at the admitted values, so each of its outputs that
    reads one carries a correspondence too, `m_d[>] = a + c[>]` and
    `𝑐≻ ∘ 𝑔≻`. Any other row whose output is its own unknown, the
    identification and a joint solve among them, answers a set of functions
    of its unknowns and carries none. The rows are read until no wire is
    added, since a row may stand before a row it reads in the table's
    order."""
    rows = tuple(rows)
    found, added = set(), True
    while added:
        added = False
        for op in rows:
            for output in _set_valued_outputs(op, found):
                if output not in found:
                    found.add(output)
                    added = True
    return found


def _admits_a_set(op):
    """Whether a row is the `Aggregation` of a relational line written with a
    clause: a row whose output is its own unknown, with one output, one map,
    the explicit side of its relation, and one equation, the line, a clause
    statement."""
    return (
        op.kind == "Aggregation"
        and bool(op.unknowns)
        and len(op.outputs) == 1
        and len(op.maps) == 1
        and len(op.equations) == 1
        and isinstance(op.equations[0], T.Slack)
    )


def _set_valued_outputs(op, found):
    """The outputs of a row that carry a correspondence, given the wires
    `found` to carry one: the output of a relational line written with a
    clause; each output of a `Pullback` whose input at its place carries one;
    and each output of an `Aggregation` whose map reads one. A row whose
    output is its own unknown otherwise has none."""
    if _admits_a_set(op):
        return tuple(op.outputs)
    if op.unknowns or op.kind not in ("Aggregation", "Pullback"):
        return ()
    if op.kind == "Pullback":
        return tuple(o for o, i in zip(op.outputs, op.inputs) if i in found)
    if len(op.maps) == len(op.outputs):
        return tuple(o for o, term in zip(op.outputs, op.maps) if set(wires_read(term)) & found)
    reads = any(set(wires_read(term)) & found for term in op.maps)
    return tuple(op.outputs) if reads else ()


# --- the wiring of a graph ---


class WiredBox(NamedTuple):
    """A box of a graph with the identities of the wires it reads and writes,
    in the order of its inputs and outputs: an entry `connect` wires."""

    box: object
    inputs: tuple
    outputs: tuple


def connect(wires, boxes, *, inputs, outputs):
    """The hypergraph of the `WiredBox` entries `boxes`, with the inputs
    `inputs` and the outputs `outputs`, wired by identity: one spider per
    identity, to which every input and output of a box and of the graph
    with that identity is joined."""
    spiders = {}

    def spider(identity):
        return spiders.setdefault(identity, len(spiders))

    dom_wires = tuple(spider(i) for i in inputs)
    box_wires = tuple(
        (tuple(spider(i) for i in ins), tuple(spider(o) for o in outs)) for _, ins, outs in boxes
    )
    cod_wires = tuple(spider(o) for o in outputs)
    return BellmanHypergraph(
        dom=wires.tensor_of_sorts(inputs),
        cod=wires.tensor_of_sorts(outputs),
        boxes=tuple(b for b, _, _ in boxes),
        wires=(dom_wires, box_wires, cod_wires),
    )


def needed(boxes, outputs):
    """The entries of `boxes` on a path to one of `outputs`, in their order:
    the combined grain starts at the declared outputs and follows the wires
    back, and leaves out a box no output depends on."""
    wanted, kept, changed = set(outputs), [], True
    remaining = list(boxes)
    while changed:
        changed = False
        for entry in list(remaining):
            _, ins, outs = entry
            if any(o in wanted for o in outs):
                kept.append(entry)
                remaining.remove(entry)
                wanted.update(ins)
                changed = True
    order = {id(b): i for i, b in enumerate(boxes)}
    return sorted(kept, key=lambda entry: order[id(entry)])


def wired_boxes(graph):
    """The boxes of a hypergraph as `WiredBox` entries, the identities of
    their input and output wires read from the spiders they sit on."""

    def identity(wire):
        return graph.spider_types[wire].inside[0].identity

    return [
        WiredBox(box, tuple(identity(w) for w in ins), tuple(identity(w) for w in outs))
        for box, (ins, outs) in zip(graph.boxes, graph.box_wires)
    ]


def group_inputs_outputs(members, outside, exported):
    """The inputs and outputs of the bubble around a group of boxes or rows,
    `members`, among the other entries of its graph, `outside`: the wires the
    members read that none of them writes, and the wires they write that an
    entry outside reads or the graph exports (`exported`), or every wire they
    write where none is."""
    produced = {o for _, _, outs in members for o in outs}
    read_outside = {i for _, ins, _ in outside for i in ins} | set(exported)
    inputs = tuple(dict.fromkeys(i for _, ins, _ in members for i in ins if i not in produced))
    written = tuple(dict.fromkeys(o for _, _, outs in members for o in outs))
    return inputs, tuple(o for o in written if o in read_outside) or written
