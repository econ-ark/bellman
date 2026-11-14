"""The forward record of one period: what each forward builder of the period
needs and what it gives, as plain data that refers to no stage.

`forward_record` reads a period of elaborated stages and answers a
`ForwardRecord`. For each forward builder, in the order the builders are
applied, a `ForwardStep` names the state fields the builder reads from the
measure that reaches it, each shock it draws with the law the stage declares
(`ForwardShock`), each control with the states its policy is read at
(`ForwardControl`), the law of motion as the function `compile_kernel()`
answers with its parameters and their values, and the state fields of the
measure it gives. The record then holds the joins within the period, the
state fields at which a measure enters and leaves the period, and, where an
inter-period mapping is given, the joins it makes: to another period, or to
the period itself, which is the reading under which one period's forward map
has a fixed point.

The record states the needs; it supplies none of them. A numerical forward
step needs, besides the record, nodes and weights for the shocks of each
builder and a function for each control, which the code that solved the
stage supplies. `asva.forward` computes with the record and those supplies,
and imports nothing of this package.
"""

from __future__ import annotations

from collections import namedtuple

from bellman.distributions.families import numeric_value
from bellman.factory.joins import forward_order, inter_period_joins, period_joins
from bellman.fold.stage_fold import stage_blocks_of
from bellman.fold.wire_terms import term_nodes
from bellman.stage.stage_answers import entry_perch, parameters_of
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import PERCH_MARK

# the two forward builders of a stage, by the ordered pair of perches each joins
_FORWARD_PAIRS = (("arvl", "dcsn"), ("dcsn", "cntn"))


class ForwardShock(
    namedtuple(
        "ForwardShock",
        "name set law family arguments argument_values parameters parameter_values jointly given",
    )
):
    """One shock a forward builder draws, as the stage declares it.

    `name` is the shock's name and `set` its declared set, as the file writes
    it. `law` is the right side of its distribution declaration, as source
    text, `family` the family that text names, and `arguments` the source
    text of each argument of the family. `argument_values` holds, in the same
    order, the number each argument takes at the calibration of the stage,
    None for an argument that is no single number at it, a tuple of means or
    a covariance matrix among them; it is None on a stage with no
    calibration. `parameters` names the parameters of the stage the law
    reads, derived parameters among them, in order of first occurrence, and
    `parameter_values` holds the value of each at the calibration, None on a
    stage with no calibration. `jointly` names the shocks the one declaration draws
    together, this shock among them, in the declaration's order. `given`
    names the states, controls and shocks the law reads, empty for a law that
    reads none."""

    __slots__ = ()


class ForwardControl(namedtuple("ForwardControl", "name set read_at")):
    """One control a forward builder reads: its name, its declared set as the
    file writes it, and under `read_at` the state fields of the decision
    perch, in declared order, at which its policy is read. A numerical step
    is given a function of those states for it."""

    __slots__ = ()


class ForwardStep(
    namedtuple(
        "ForwardStep",
        "stage builder source target states shocks controls function arguments roles "
        "outputs writes parameters parameter_values kernels",
    )
):
    """One forward builder of a period: what it needs and what it gives.

    `stage` is the key of the stage in the period and `builder` the name of
    the builder; `source` and `target` are the perches it joins. `states`
    names the state fields of the source perch that it reads from the measure
    that reaches it; `shocks` holds one `ForwardShock` for each shock it
    draws, in declared order; `controls` one `ForwardControl` for each
    control it reads.

    `function` is the law of motion, the function the push-forward's
    `compile_kernel()` answers: it takes the values of `arguments` in order,
    then the value of each parameter `parameters` names,
    `step.function(*values, *step.parameter_values)`. `roles` says of each
    argument, in the same order, whether it is a `"state"`, a `"shock"` or a
    `"control"`. `parameter_values` is None on a stage with no calibration.
    `outputs` names what the function returns, as its printed kernel names
    it, and `writes` the state fields of the target perch those outputs are,
    in the same order: the fields of the measure the builder gives.

    `kernels` is the builder's whole `kernels()` record.

    See `forward_record`."""

    __slots__ = ()


class ForwardRecord(
    namedtuple("ForwardRecord", "period steps arrival leaving joins connector joined_to")
):
    """The forward record of one period, which `forward_record` answers:
    plain data that refers to no stage.

    `period` names the period: its address in a trellis where
    `forward_record` was given one, else the name the period carries, else
    the keys of its stages. `steps` holds one `ForwardStep` for each forward
    builder of each stage, the stages in the period's forward order.

    `arrival` names the state fields at which a measure enters the period,
    each `(stage key, field, declared set)`: the states of each stage's
    entry perch that no join within the period reaches, the arrival perch
    or, for a stage that declares none, the decision perch. `leaving` names,
    in the same form, the state fields at which it leaves: the continuation
    states that no join within the period reads. `joins` holds the joins
    within the period, each `((stage key, field), (stage key, field))` from
    a continuation state to an arrival state.

    `connector` holds the joins of the inter-period mapping the record was
    given, in the form of `joins`, from a field of `leaving` to an arrival
    state of the period it joins, and is empty where none was given. `joined_to` is
    `"itself"` where the mapping joins the period to itself, the name of the
    other period where it joins another, and None where none was given.

    `needs()` lists what a numerical step must be given."""

    __slots__ = ()

    def closed(self):
        """Whether the inter-period mapping joins the period to itself and
        reaches every field at which a measure enters it, so that one
        period's forward map carries a measure on those fields to a measure
        on the same fields."""
        reached = {target for _, target in self.connector}
        entered = {(stage, field) for stage, field, _ in self.arrival}
        return self.joined_to == "itself" and reached == entered

    def needs(self):
        """What a numerical forward step must be given, as a mapping with
        three entries. `"shocks"` maps `(stage key, builder)` to the names of
        the shocks that builder draws, for which nodes and weights are
        given; `"policies"` maps `(stage key, control)` to the state fields
        the control's policy is read at, for which a function is given;
        `"parameters"` lists `(stage key, builder, parameter)` for each
        parameter of a law of motion that has no value, which a calibration
        of the stage binds."""
        shocks, policies, parameters = {}, {}, []
        for step in self.steps:
            if step.shocks:
                shocks[(step.stage, step.builder)] = tuple(shock.name for shock in step.shocks)
            for control in step.controls:
                policies[(step.stage, control.name)] = control.read_at
            if step.parameter_values is None:
                parameters.extend((step.stage, step.builder, name) for name in step.parameters)
        return {"shocks": shocks, "policies": policies, "parameters": parameters}

    def __str__(self):
        lines = [f"forward record of {self.period}"]
        lines.append("enters at   " + _fields_text((s, f) for s, f, _ in self.arrival))
        for number, step in enumerate(self.steps, start=1):
            lines.append(f"{number}  {step.stage}.{step.builder}: {step.source} → {step.target}")
            lines.append("     reads     " + (", ".join(step.states) or "no state"))
            for shock in step.shocks:
                # one declaration that draws several shocks is printed once
                if shock.name == shock.jointly[0]:
                    drawn = shock.name if len(shock.jointly) == 1 else f"({', '.join(shock.jointly)})"
                    lines.append(f"     draws     {drawn} ~ {shock.law}")
            for control in step.controls:
                lines.append(
                    f"     policy    {control.name}({', '.join(control.read_at)}), to be given"
                )
            called = ", ".join(step.arguments) + (
                f"; {', '.join(step.parameters)}" if step.parameters else ""
            )
            lines.append(
                f"     function  {step.function.__name__}({called}) → {', '.join(step.outputs)}"
            )
            lines.append("     gives     " + ", ".join(step.writes))
        for origin, target in self.joins:
            lines.append(f"join        {_field_text(origin)} → {_field_text(target)}")
        lines.append("leaves at   " + _fields_text((s, f) for s, f, _ in self.leaving))
        for origin, target in self.connector:
            lines.append(
                f"connector   {_field_text(origin)} → {_field_text(target)} of {self.joined_to}"
            )
        return "\n".join(lines)

    __repr__ = __str__


def _field_text(pair):
    return f"{pair[0]}.{pair[1]}"


def _fields_text(pairs):
    return ", ".join(_field_text(pair) for pair in pairs) or "no field"


def forward_record(period, inter_connector=None, *, to=None, address=None, file=None):
    """The `ForwardRecord` of `period`, a period of elaborated stages,
    `{"stages": {key: stage}, "connectors": [...]}`, as a trellis holds it or
    as it is written by hand around one stage.

    `inter_connector` is the mapping from the continuation state fields that
    leave the period to arrival state fields of the period it joins, as an
    entry of a trellis's `inter_connectors` writes it, `{"a": "k"}`. With
    `to`, the period that follows `period` in time, the mapping joins
    `period` to it; without `to` it joins the period to itself, which states
    that the same period follows. `address`, the period's address in its
    trellis, `periods[1]`, and `file` name the period in a refusal, as
    `period_joins` reads them; a period that holds a record in place of an
    elaborated stage is refused there, under `record-shape`. The record
    names the period by `address` where one is given, else by the name the
    period carries, else by the keys of its stages.

    A stage's forward builder is recorded where its law of motion is one
    push-forward with an explicit function; a stage holds one such builder
    or two, since a stage that declares no arrival perch is entered at its
    decision perch and a stage that ends a model declares no continuation.
    A stage whose forward builders are not constructed is refused by the
    stage, with the refusal that says why. A builder with a sub-builder, a
    branch or no explicit function is refused with a ValueError that names
    the stage and the builder."""
    named, address = _name_of(period, address), "periods[?]" if address is None else address
    joins = period_joins(period, address, file)
    steps = []
    for key in forward_order(period, address, file):
        steps.extend(_stage_steps(key, period["stages"][key]))
    joined = {tuple(join["to"]) for join in joins["joins"]}
    arrival = tuple(
        (key, identity.field, _set_text(sort))
        for key in forward_order(period, address, file)
        for identity, sort in period["stages"][key].fields().items()
        if sort.role == "state"
        and identity.perch == entry_perch(period["stages"][key])
        and (key, identity.field) not in joined
    )
    connector, joined_to = (), None
    if inter_connector is not None:
        earlier = period if to is None else to
        connector = tuple(
            (tuple(join["from"]), tuple(join["to"]))
            for join in inter_period_joins(
                inter_connector, period, earlier, file=file, later_address=address
            )
        )
        joined_to = "itself" if to is None else _name_of(to, None)
    elif to is not None:
        raise ValueError(
            "forward_record was given the period that follows, `to`, and no inter-period "
            "mapping that joins the period to it; give the mapping, as an entry of a trellis's "
            'inter_connectors writes it, {"a": "k"}'
        )
    return ForwardRecord(
        period=named,
        steps=tuple(steps),
        arrival=arrival,
        leaving=tuple(
            (key, field, _continuation_set(period["stages"][key], field))
            for key, field in joins["outputs"]
        ),
        joins=tuple((tuple(join["from"]), tuple(join["to"])) for join in joins["joins"]),
        connector=connector,
        joined_to=joined_to,
    )


def _name_of(period, address):
    """The name by which a record names a period: its address in a trellis
    where one is given, else the name the period carries, else the keys of
    its stages."""
    if address is not None:
        return address
    name = period.get("name")
    if isinstance(name, str) and name:
        return name
    return "the period of " + ", ".join(period["stages"])


def _set_text(sort):
    return None if sort.domain is None else to_source(sort.domain)


def _continuation_set(stage, field):
    """The declared set of a continuation state field of a stage, as the
    file writes it."""
    return next(
        (
            _set_text(sort)
            for identity, sort in stage.fields().items()
            if sort.role == "state" and identity.perch == "cntn" and identity.field == field
        ),
        None,
    )


def _stage_steps(key, stage):
    """The `ForwardStep` of each forward builder the stage holds, the arrival
    builder first."""
    fields = stage.fields()
    edges = stage_blocks_of(stage).edges
    # every parameter's value at the calibration, a derived parameter's among
    # them; None on a stage with no calibration
    values = (
        None
        if stage.bindings.calibration is None
        else {name: record.value for name, record in parameters_of(stage).items()}
    )
    declared = frozenset(parameters_of(stage))
    decision_states = tuple(
        identity.field
        for identity, sort in fields.items()
        if sort.role == "state" and identity.perch == "dcsn"
    )
    steps = []
    for source, target in _FORWARD_PAIRS:
        try:
            handle = stage.builder[source, target]
        except KeyError:
            continue  # the stage holds no builder between these two perches
        try:
            kernels = handle.kernels()
        except Exception as error:
            raise ValueError(
                f"stage {stage.name!r} at key {key!r}: its forward builder from {source} to "
                f"{target} answers no kernels ({error}); a forward record holds a builder whose "
                "law of motion is compiled"
            ) from error
        name = kernels.builder
        laws = [piece for piece in kernels.pieces if piece.kind == "Pushforward"]
        others = [
            piece.relative_name
            for piece in kernels.pieces
            if piece.kind not in ("Pushforward", "DistributionExtension")
        ]
        if len(laws) != 1 or laws[0].function is None or others:
            raise ValueError(
                f"stage {stage.name!r} at key {key!r}: the forward builder {name!r} is not one "
                "push-forward with an explicit function after the extensions by its shocks; its "
                f"pieces are {', '.join(piece.relative_name for piece in kernels.pieces)}. A "
                "forward record holds no builder with a sub-builder, a branch or a law of motion "
                "that has no explicit function"
            )
        law = laws[0]
        edge = edges.get(name)
        base = () if edge is None else edge.base
        drawn = () if edge is None else edge.shocks
        roles_by_name = {identity.stem: fields[identity].role for identity in base}
        roles_by_name.update({shock: "shock" for shock in drawn})
        unknown = [argument for argument in law.arguments if argument not in roles_by_name]
        if unknown:
            raise ValueError(
                f"stage {stage.name!r} at key {key!r}: the law of motion of {name!r} reads "
                f"{', '.join(unknown)}, which is none of the builder's states, controls or shocks"
            )
        roles = tuple(roles_by_name[argument] for argument in law.arguments)
        steps.append(
            ForwardStep(
                stage=key,
                builder=name,
                source=source,
                target=target,
                states=tuple(i.field for i in base if fields[i].role == "state"),
                shocks=_shocks(edge, fields, values, declared),
                controls=tuple(
                    ForwardControl(i.field, _set_text(fields[i]), decision_states)
                    for i in base
                    if fields[i].role == "control"
                ),
                function=law.function,
                arguments=law.arguments,
                roles=roles,
                outputs=law.outputs,
                writes=_written_fields(stage, key, name, target, law.outputs, fields),
                parameters=law.parameters,
                parameter_values=law.parameter_values,
                kernels=kernels,
            )
        )
    if not steps:
        raise ValueError(
            f"stage {stage.name!r} at key {key!r} holds no forward builder: its forward builders "
            "are not constructed, as for a stage whose branches end at different continuations"
        )
    return steps


def _shocks(edge, fields, values, declared):
    """One `ForwardShock` for each shock the edge draws, in declared order;
    `values` maps each parameter to its value at the calibration, or is
    None, and `declared` holds the names of the stage's parameters."""
    if edge is None:
        return ()
    sets = {
        identity.field: _set_text(sort) for identity, sort in fields.items() if sort.role == "shock"
    }
    shocks = []
    for name in edge.shocks:
        owner = edge.declaration_of(name)
        arguments = tuple(getattr(owner.term, "args", ()))
        read = tuple(
            dict.fromkeys(
                node.symbol.name
                for node in term_nodes(owner.term)
                if isinstance(node, T.Sym)
                and isinstance(node.symbol, T.Constant)
                and node.symbol.name in declared
            )
        )
        shocks.append(
            ForwardShock(
                name=name,
                set=sets.get(name),
                law=to_source(owner.term),
                family=getattr(owner.term, "fun", None),
                arguments=tuple(to_source(argument) for argument in arguments),
                argument_values=(
                    None
                    if values is None
                    else tuple(numeric_value(argument, values) for argument in arguments)
                ),
                parameters=read,
                parameter_values=None if values is None else tuple(values[name] for name in read),
                jointly=tuple(owner.subjects),
                given=tuple(str(argument) for argument in owner.arguments),
            )
        )
    return tuple(shocks)


def _written_fields(stage, key, builder, target, outputs, fields):
    """The state field of the target perch each output of a law of motion
    is, in the outputs' order: an output is printed as its field with the
    mark of its perch, `a≻`."""
    printed = {
        identity.field + PERCH_MARK.get(identity.perch, ""): identity.field
        for identity, sort in fields.items()
        if sort.role == "state" and identity.perch == target
    }
    missing = [output for output in outputs if output not in printed]
    if missing:
        raise ValueError(
            f"stage {stage.name!r} at key {key!r}: the law of motion of {builder!r} returns "
            f"{', '.join(missing)}, which is no state field of the perch {target}"
        )
    return tuple(printed[output] for output in outputs)
