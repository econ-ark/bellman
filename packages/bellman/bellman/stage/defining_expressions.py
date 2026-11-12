"""The typed defining expressions of a stage, read from native stage data:
what a wire denotes, what an operator and a definition denote, and the names
a card, a kernel and a drawing give the wires, the measures and the results.

The expressions name mathematical functions and laws, not numerical methods.
Their restricted domains state requirements; construction proves no analytic
closure theorem. No expression is retained on the stage or recovered from text.

The expression a wire denotes (`wire_expression`) is read from the rows of the
native semgraph that produce it: the query expands the generated intermediate
wires and stops at the evaluated fields and the authored function names, and
the rules and the residual lines an operation declares on its output are read
from the same row (`wire_rules`, `wire_residual_rules`). It adds no expression
field to the stage or a graph; an answer is kept in the version's own cache of
derived answers.

The derived records are made by the named operations on terms of
`term_operations` (AMD-SG-034 §2 item 0a; AMD-SG-035 §3), composed: substitute
a variable (`S.substitute`), apply a function at a point, restrict a domain,
compose two maps, and the residual, the slack and the Kuhn–Tucker system of a
relation and its bound; this module adds the reading of a declaration by its
identity (`declared_set_of`), the reading of a line at the point
(`line_at_point`) and the relation a row of candidate statements holds
there, the conjunction of its members so read (`system_relation`). A short
form of §4 is one such composition, and no derivation branches on the shape
of a particular stage.

A row is read by its kind after two tests (`grains.is_relation`): an
`Argmax` row by the definition of its kind, and a row whose output is its
own unknown by the one relation definition, `RELATION`, unless its relation
holds an explicit side (`grains.explicit_side`), which the row maps by the
definition of its kind, the relation standing as its rule.

A candidate line written with a clause, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0`,
admits at each saving the set of values its clause admits, read by the
regions of its Kuhn–Tucker condition (`ranges.clause_regions`): one value
where the bound is slack and a segment where it binds. Its output carries a
correspondence (`WireTable.carries_correspondence`), and so does every
output an aggregation or a pullback forms by reading it at its point, each
taking the values its map gives at the admitted values. The identification
`c = c[>]` then ranges over the admitted pairs, the grid line read at each
admitted value, and the residual of a joint solve that is the difference
between a control and such a candidate is read as the control's membership
in the candidate's values. Where the rules of a row read the outputs of a
law of motion that writes several coordinates, they read them by the
coordinates' names, and the row states the law's line once under `where`
(`law_outputs_read`).
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

from discopy.frobenius import Bubble

from bellman.display.cards import Rule
from bellman.display.drawing import drawn_sorts
from bellman.distributions.families import (
    FAMILY_ARGUMENTS,
    LOGNORMAL,
    MIXTURE,
    NORMAL,
    SCALAR_FAMILIES,
    TRUNCATED_LOGNORMAL,
    product_law,
)
from bellman.fold.block_lines import fields_of, perches_of
from bellman.fold.stage_names import StageNames, branches_of
from bellman.fold.wire_terms import is_wire_symbol, label_case, wire_symbol, wires_read
from bellman.native.identity import Identity, box_identity
from bellman.native.labels import (
    AGGREGATOR_LETTER,
    LAW_OF_MOTION_LETTER,
    function_field,
    function_name,
    is_wiring,
    italic,
    wire_spelling,
)
from bellman.native.predicates import And, Compare, Complementarity, Member, Not, Or
from bellman.native.versions import kept_answer
from bellman.refusals import NotConstructed
from bellman.stage.boxes import builder_rows_of, row_of
from bellman.stage.carriers import (
    coordinate_bindings,
    coordinate_domain,
    declared_set_term,
    definition_type,
    joint_name,
    policy_carrier,
    product,
    resolve_set,
    wire_type,
    written_name,
)
from bellman.stage.grains import (
    answering_row,
    answers_function_set,
    explicit_side,
    is_relation,
    wire_table,
)
from bellman.stage.kernel_records import (
    aggregator_kernel,
    distribution_arguments,
    law_of_motion_kernel,
    stems_of,
)
from bellman.stage.places import block_box
from bellman.stage.term_operations import (
    SIGN,
    apply_at,
    component,
    compose,
    kuhn_tucker,
    reduced,
    reference_term,
    relation_of,
    restrict,
    tuple_term,
)
from bellman.syntax import terms as T
from bellman.syntax.vocabulary import CONTINUATION, PERCH_MARK, SHCK
from bellman.typing import typed_expressions as S
from bellman.typing.line_unknowns import maximand
from bellman.typing.primitive_definitions import (
    PRIMITIVE_DEFINITIONS,
    bound_variable,
    instantiated_definition,
    measurable_sets,
    point_mass,
    primitive_definition,
)
from bellman.typing.ranges import clause_regions, solved_for
from bellman.typing.sets import defined
from bellman.typing.typed_expressions import OPEN_ARGUMENT, format_expression, printed_name

# --- the expression a wire denotes ---


def wire_expression(stage, sort_or_identity, *, expand=False, explicit=False):
    """The structured expression one wire denotes.

    With the default ``expand=False``, an evaluated field or authored function
    is its own reference, and an operation's result is its producer's own
    equation over the producer's input wires, an unnamed input read by
    reference.  ``expand=True`` derives the complete defining expression
    of that requested output, through the unnamed results it reads, while
    recursive inputs still stop at the nearest evaluated field or authored
    function.  A field wire is always a value reference and is never passed
    through a functional producer.  The answer is the formula in its defining
    operator's context; that operator's expression retains the restricted
    input domain and is not broadened here. The candidate of a line written
    with a clause denotes the set of the values the clause admits at each
    point; ``explicit=True`` asks for the explicit side its line writes
    instead, `a ↦ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a))`, the requested wire's alone.
    """
    rendering, producers = _producer_index(stage)
    sort = (
        rendering.sort_of(sort_or_identity)
        if isinstance(sort_or_identity, Identity)
        else sort_or_identity
    )
    if not hasattr(sort, "identity"):
        raise TypeError("wire_expression requires a native wire sort or identity")
    memo = {}

    def derive(current, force, active, complete):
        identity = current.identity
        producer = producers.get(identity)
        row = producer[0] if producer is not None else None
        if active:
            # read as an input, the component of a merged G that reads a
            # wire and writes it again is that wire: the reference follows
            # the record's map to the wire it passes
            passed = _passed(row, identity)
            if passed is not None:
                return derive(rendering.sort_of(passed), False, active + (identity,), complete)
        # an operation's result asked for is its producer's equation; read as
        # an input of another wire's producer, it is a reference to itself in
        # the record's own equation and is derived in the complete definition;
        # an Evaluation's output is the name it writes and is no equation
        unnamed = identity.is_result and not (row is not None and row.kind == "Evaluation")
        asked = not active and unnamed
        through = complete and unnamed
        if identity.kind == "field" or (
            _named_boundary(current, row) and not force and not asked and not through
        ):
            return reference_term(identity)
        if producer is None:
            return reference_term(identity)
        if identity in active:
            return S.Unresolved(identity, "acyclic wire expression")
        force = bool(force and _named_boundary(current, row))
        # the explicit side is asked of the requested wire alone; every input
        # is read as it denotes
        side = bool(explicit and not active)
        key = identity, force, complete, side
        if key in memo:
            return memo[key]

        def compute():
            row, inputs, outputs = producer
            expression = _one_step(stage, row, inputs, outputs, current, explicit=side)
            replacements = {
                input_sort.identity: derive(input_sort, False, active + (identity,), complete)
                for input_sort in inputs
            }
            return reduced(S.substitute(expression, replacements), beta=True)

        answer = kept_answer(
            stage,
            ("wire-expression", identity, force, complete) + (("explicit",) if side else ()),
            compute,
        )
        memo[key] = answer
        return answer

    return derive(sort, bool(expand), (), bool(expand))


def wire_rules(stage, sort_or_identity):
    """The rules the operation that writes a wire declares on it, each a
    `Rule` at the point (AMD-SG-034 §4 item 3): the relation a row whose
    output is its own unknown states, an inequality with its clause, the
    grid relation of the identification on its image or a solve head; the
    membership an `Argmax` row states and the properties attached to its
    line; the composite a pullback writes, at a point of its domain; the
    expectation at a point of its domain; the relation of an aggregation on
    a named output; the mass a forward row gives an event. An Evaluation
    names what the operation before it made, so its output holds that
    operation's rules and then its own, the `Member` statements of its
    declared carrier with its feasibility; every other wire holds none
    (`output_rules`)."""
    rendering, producers = _producer_index(stage)
    sort = (
        rendering.sort_of(sort_or_identity)
        if isinstance(sort_or_identity, Identity)
        else sort_or_identity
    )

    def compute():
        current, held = sort, producers.get(sort.identity)
        own = ()
        while held is not None and held[0].kind == "Evaluation":
            row, inputs, outputs = held
            own = tuple(output_rules(stage, row, current, inputs, outputs)) + own
            current = inputs[tuple(o.identity for o in outputs).index(current.identity)]
            held = producers.get(current.identity)
        if held is None:
            return own
        return tuple(output_rules(stage, held[0], current, held[1], held[2])) + own

    return kept_answer(stage, ("wire-rules", sort.identity), compute)


def wire_residual_rules(stage, sort_or_identity):
    """The lines an unnamed input of a solve is made from, one `Rule` per
    residual (AMD-SG-034 §4 item 9); empty on every other wire."""
    rendering, _ = _producer_index(stage)
    sort = (
        rendering.sort_of(sort_or_identity)
        if isinstance(sort_or_identity, Identity)
        else sort_or_identity
    )

    def compute():
        return residual_rules(stage, sort)

    return kept_answer(stage, ("wire-lines", sort.identity), compute)


# --- the producer of a wire ---


def _producer_index(stage):
    """The immutable producer index of the wire table, kept once for this
    version."""
    rendering = wire_table(stage)
    producers = kept_answer(
        stage, ("wire-expression", "producers"), lambda: MappingProxyType(_producers(rendering))
    )
    return rendering, producers


def _producers(rendering):
    """Rendered producer row and wires, by the identity each row writes."""
    found = {}
    for direction in ("backward", "forward"):
        try:
            held = rendering.rows(direction)
        except NotConstructed:
            continue
        for _, rows in held:
            for row, inputs, outputs in rows:
                input_sorts = tuple(rendering.sort_of(identity) for identity in inputs)
                output_sorts = tuple(rendering.sort_of(identity) for identity in outputs)
                for output in output_sorts:
                    found[output.identity] = row, input_sorts, output_sorts
    return found


def _one_step(stage, row, inputs, outputs, output, *, explicit=False):
    """One component formula under its operator's retained input domain;
    `explicit` is `_operator_components`'s."""
    components = _operator_components(stage, row, inputs, outputs, explicit=explicit)
    if isinstance(components, S.Unresolved):
        return components
    pack, bodies, _ = components
    argument = tuple_term(reference_term(sort.identity) for sort in inputs)
    position = tuple(sort.identity for sort in outputs).index(output.identity)
    if row.kind == "Evaluation" and len(bodies) == 1:
        selected = component(bodies[0], position, len(outputs))
    elif len(bodies) != len(outputs):
        missing = next(
            (body.missing for body in bodies if isinstance(body, S.Unresolved)),
            "output component projection",
        )
        return S.Unresolved(output.identity, missing)
    else:
        selected = bodies[position]
    body = S.substitute(selected, {pack.variable.identity: argument})
    return reduced(body, beta=True)


def _named_boundary(sort, row):
    """Whether a wire is its own reference in a defining expression, not
    expanded into its producer's equation: a field, a measure, the output of
    an Evaluation, an operation's result, and a function, a choice or an
    alias that is no composite with the law of motion."""
    identity = sort.identity
    if identity.kind == "field":
        return True
    if identity.kind == "measure":
        # a measure is its own reference, the perch's `μ≻` and an extension's
        # `μ⊗P_ν` alike: the rule on its wire states what it is
        return True
    if row is not None and row.kind == "Evaluation":
        return True
    if identity.is_result:
        # an operation's result is its own reference: an operation's record
        # holds its equation over its input wires and copies no producer's
        # term; a card prints the reference by the producer's row
        return True
    return identity.kind in ("function", "choice", "alias") and identity.mark != "g"


def _passed(row, identity):
    """The input an Aggregation's output is the identity on: the map the
    record holds for that output is the input's own wire symbol, as a merged
    G writes for the component it leaves alone (`_paired_segment`) and the
    block's outside aggregation writes for a line whose term is one bare
    wire; None for every other output, and for every output of a relation,
    whose map is no equation of its output (`grains.is_relation`)."""
    if (
        row is None
        or row.kind != "Aggregation"
        or is_relation(row)
        or len(row.maps) != len(row.outputs)
    ):
        return None
    held = row.maps[tuple(row.outputs).index(identity)]
    if is_wire_symbol(held) and held.symbol.name in row.inputs:
        return held.symbol.name
    return None


# --- the defining expression of an operator ---


def operator_expression(stage, box, row):
    """The shared primitive definition at this occurrence's declared data."""
    return _operator_expression(stage, row, tuple(box.dom.inside), tuple(box.cod.inside))


def _operator_expression(stage, row, inputs, outputs):
    """The primitive definition on explicitly supplied native wire sorts."""
    components = _operator_components(stage, row, inputs, outputs)
    if isinstance(components, S.Unresolved):
        return components
    pack, bodies, guards = components
    outputs = tuple(outputs)
    result = product(wire_type(stage, sort).carrier for sort in outputs)
    guards = tuple(guards) + (Member(tuple_term(bodies), result),)
    domain = T.Comprehension(pack.variable, pack.domain, guards) if guards else pack.domain
    return S.Lambda(((pack.variable, domain),), tuple_term(bodies))


def _operator_components(stage, row, inputs, outputs, *, explicit=False):
    """The component formulas and guards shared by an operator and its wires:
    the binding of the operator's inputs as one pack, the formula of each
    output and the guards under which the formulas hold, from the step of
    the row's reading: an `Argmax` by its definition, a row whose output is
    its own unknown and whose relation holds no explicit side by the one
    relation definition, and every other row, a relation with an explicit
    side included, by its kind; a kind no step reads, and an expectation
    whose input is not mapped, answer `Unresolved`. With `explicit`, the
    candidate of a line written with a clause is its explicit side and not
    the set its clause admits (`_aggregation_components`)."""
    ctx = StageNames(stage)
    inputs, outputs = tuple(inputs), tuple(outputs)
    owner = row.identity
    types = tuple(wire_type(stage, sort) for sort in inputs)
    pack = bound_variable(
        owner,
        inputs[0].identity.field or "w" if len(inputs) == 1 else "w",
        product(answer.carrier for answer in types),
        0,
        role="input",
    )
    given = reference_term(pack.variable.identity)
    references = {sort.identity: component(given, n, len(inputs)) for n, sort in enumerate(inputs)}
    if row.kind == "Argmax":
        parts = _one_formula(_argmax_definition(ctx, row, inputs, outputs, references))
    elif answers_function_set(stage, row):
        parts = _one_formula(_relation_definition(ctx, row, inputs, outputs, references, pack))
    elif row.kind == "Pullback":
        parts = _pullback_components(ctx, row, inputs, outputs, types, references)
    elif row.kind == "Aggregation":
        parts = _aggregation_components(ctx, row, inputs, outputs, references, explicit=explicit)
    elif row.kind == "Expectation":
        parts = _expectation_components(ctx, row, inputs, outputs, references)
    elif row.kind == "Evaluation":
        parts = ((given,), ())
    elif row.kind in ("Pushforward", "PolicyInsertion", "DistributionExtension"):
        parts = _forward_components(ctx, row, inputs, outputs, references)
    else:
        return S.Unresolved(owner, "instantiated " + row.kind + " definition")
    if isinstance(parts, S.Unresolved):
        return parts
    bodies, guards = parts
    return pack, bodies, guards


def _one_formula(held):
    """The one formula and the guard of an `Argmax` or of a relation, as the
    component formulas and guards of its operator; an `Unresolved` formula
    stands as the one formula."""
    body, guard = held
    return (body,), (() if guard is None else (guard,))


def _pullback_components(ctx, row, inputs, outputs, types, references):
    """The formula and the guard of each output of a pullback: the input
    function pulled back along the law of motion, held as the composition
    with the law or with its section at a label, by reference, and at the
    policy with the law at the policy written out as a map of the point,
    `m_d ↦ 𝑔≻(m_d, 𝑐(m_d))` (RL14)."""
    bodies, guards = [], []
    for n, output in enumerate(outputs):
        source = inputs[n]
        g = _law_map_at_policy(ctx, row, output.coordinates, source.coordinates)
        body, guard = _instantiate(
            "Pullback",
            {
                "D": coordinate_domain(ctx, output.coordinates, row.identity),
                "Y": types[n].sort[3],
                "L": types[n].sort[4],
                "g": g,
            },
            references[source.identity],
            {T.Named("D"): g.bindings} if isinstance(g, S.Lambda) else None,
        )
        # the pulled-back function is the composition with the law of
        # motion or with its section at a label, held by reference, and at
        # the policy with the law at the policy written out as a map of the
        # point, `m_d ↦ 𝑔≻(m_d, 𝑐(m_d))`, which no name abbreviates, so that
        # the composite read at a point is `𝑉≻(𝑔≻(m_d, 𝑐(m_d)))` (RL14); each
        # with the coordinates the law writes (AMD-SG-034 §4 item 6; §5)
        if (
            isinstance(g, S.Lambda)
            and isinstance(g.body, S.Apply)
            and isinstance(g.body.function, T.Sym)
        ):
            forward, law_outputs = _law_outputs(ctx, row, row.section)
            inner = (
                reference_term(section_identity(ctx, row.builder, row.section))
                if row.section is not None
                else g
                if row.policy
                else reference_term(row.definition)
            )
            body = compose(references[source.identity], inner, law_outputs)
        bodies.append(body)
        guards.append(guard)
    return tuple(bodies), tuple(guards)


def _aggregation_components(ctx, row, inputs, outputs, references, *, explicit=False):
    """The formula and the guard of each output of an aggregation: the map
    its line writes, at the point. An output that carries a correspondence
    (`WireTable.carries_correspondence`) takes a set of values at each
    point: the candidate of a line written with a clause, the values its
    clause admits (`_admitted_values`), unless `explicit` asks for the
    explicit side its line writes; any other output, the values its map
    takes at the values each correspondence it reads admits
    (`_image_at_admitted`). The guard is the aggregation's own in every
    case."""
    stage = ctx.stage_object
    rendering = wire_table(stage)
    clause = _candidate_clause(stage, row)
    bodies, guards = [], []
    for output in outputs:
        body, guard = _aggregate(ctx, row, inputs, output, references)
        if rendering.carries_correspondence(output.identity):
            if clause is not None and not explicit:
                body = _admitted_values(ctx, row, output, body, clause)
            elif clause is None:
                body = _image_at_admitted(ctx, row, inputs, output, references)
        bodies.append(body)
        guards.append(guard)
    return tuple(bodies), tuple(guards)


# the base of the variables a value a correspondence admits is bound as
ADMITTED = 150


def _candidate_clause(stage, row):
    """The line of a relational row written with a clause on a candidate,
    `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0`, a clause statement: the relation's
    explicit side (`grains.explicit_side`) is the part a kernel computes, and
    the clause admits at each point the values `_admitted_values` reads.
    None for every other row."""
    if not is_relation(row) or explicit_side(stage, row) is None:
        return None
    core = stage.definitions[row.statements[0]].equations[0]
    return core if isinstance(core, T.Slack) else None


def _admitted_values(ctx, row, output, explicit, core):
    """The formula of the candidate a line written with a clause defines,
    `c[>] <= 𝑑𝑢𝑖𝑛𝑣(dV[>]) ⟂ a >= 0`: at each point, the set of the values
    `x` of the candidate's declared set that the clause admits there, the
    regions of the Kuhn–Tucker condition of the line's relation in `x`,
    `x ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a))` in the order and with the sign the line writes, and
    of its bound read at the point (`ranges.clause_regions`):

        a ↦ {x ∈ ℝ₊₊ | a > 0 ∧ x − 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) = 0
                        ∨ a = 0 ∧ x − 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) ≤ 0}

    one value where the bound is slack and, where it binds, every value on
    the side of the explicit value the sign admits. `explicit` is the
    aggregation's formula of the explicit side, a map of the point, and
    `core` the line, a clause statement."""
    stage = ctx.stage_object
    point, points = bound_point(ctx, row.identity, output.coordinates)
    at = tuple_term(points[identity] for identity in output.coordinates)
    side = apply_at(explicit, at)
    result = wire_type(stage, output).sort[4]
    taken = bound_variable(row.identity, "x", result, ADMITTED)
    value = reference_term(taken.variable.identity)
    relation = relation_of(core)
    sign = SIGN[type(relation.op)] if isinstance(relation, T.Inequality) else "="
    statement = (
        Compare(value, sign, side)
        if explicit_side(stage, row) == relation.rhs
        else Compare(side, sign, value)
    )
    local = {**points, **{identity.field: held for identity, held in points.items()}}
    bound = term_by_reference(ctx, core.bound, row.identity, row.builder, local, declared=True)
    admits = clause_regions(kuhn_tucker(statement, bound))
    return S.Lambda(point, T.Comprehension(T.Subject((taken.variable,)), result, (admits,)))


def _image_at_admitted(ctx, row, inputs, output, references):
    """The formula of an output an aggregation writes by reading a
    correspondence at its point, `m_d[>] = a + c[>]` over the candidate of a
    line written with a clause: at each point, the set of the values its
    map takes where each correspondence it reads is read at a value it
    admits there and every other input at the point,

        a ↦ {m_d ∈ Xm | ∃ x ∈ 𝑐≻(a): (m_d = a + x)}

    so that where the candidate admits a segment the output takes the value
    of the map at each of its values. The map is the row's kernel
    (`_aggregator_kernel_and_carrier`)."""
    rendering = wire_table(ctx.stage_object)
    kernel, carrier, point, points, used = _aggregator_kernel_and_carrier(ctx, row, inputs, output)
    bindings, values = [], []
    for n, sort in enumerate(used):
        read = _at(sort, references[sort.identity], points)
        if not rendering.carries_correspondence(sort.identity):
            values.append(read)
            continue
        held = bound_variable(
            row.identity, "x", wire_type(ctx.stage_object, sort).sort[4], ADMITTED + 1 + n
        )
        bindings.append((held.variable, read))
        values.append(reference_term(held.variable.identity))
    arguments = (tuple_term(values),) + tuple(
        reference_term(variable.identity) for variable, _ in point
    )
    taken = bound_variable(
        row.identity,
        output.identity.field or "y",
        carrier.codomain,
        ADMITTED + 1 + len(used),
    )
    image = reduced(S.Apply(kernel, arguments), beta=True)
    member = Compare(reference_term(taken.variable.identity), "=", image)
    holds = _quantified("exists", bindings, member) if bindings else member
    return S.Lambda(
        point, T.Comprehension(T.Subject((taken.variable,)), carrier.codomain, (holds,))
    )


def _expectation_components(ctx, row, inputs, outputs, references):
    """The formula of each output of an expectation, as the file declares
    it, `E_{Ψ}[body]`: the shocks bound one variable each under their names,
    the input read at the point and the shocks, and the law reached by the
    shocks' names, the declaration listed under `definitions`; no measure is
    constructed (AMD-SG-034 §4 item 7). An output whose input is
    not mapped answers `Unresolved`."""
    bodies = []
    for n, output in enumerate(outputs):
        mapped = row.maps[n] if n < len(row.maps) else None
        source_identity = mapped.symbol.name if is_wire_symbol(mapped) else None
        source = next((held for held in inputs if held.identity == source_identity), None)
        if source is None:
            return S.Unresolved(output.identity, "expectation input mapping")
        point, points = bound_point(ctx, row.identity, output.coordinates)
        shocks = tuple(
            Identity("field", stage=ctx.stage_name, perch=SHCK, field=name)
            for name in row.integrated
        )
        drawn, draws = bound_point(ctx, row.identity, shocks, 200)
        integrand = _at(source, references[source.identity], {**points, **draws})
        bodies.append(S.Lambda(point, expectation(drawn, integrand)))
    return tuple(bodies), ()


def _forward_components(ctx, row, inputs, outputs, references):
    """The formula of each output of a push-forward, a policy insertion or a
    distribution extension, and the guards some of them hold."""
    bodies, guards = [], []
    for output in outputs:
        body, guard = _forward_measure(ctx, row, inputs[0], output, references[inputs[0].identity])
        bodies.append(body)
        if guard is not None:
            guards.append(guard)
    return tuple(bodies), tuple(guards)


# --- a pullback: the law of motion at the point ---


def _law_map_at_policy(ctx, row, source_coordinates, target_coordinates):
    """The map a row composes with, from the source coordinates to the
    target coordinates, at the policy the row is held at: the law of motion
    applied by reference to the point, `m_d ↦ 𝑔≻(m_d, 𝑐(m_d))`, where the
    target coordinates are the outputs the law writes in their order; where
    they are not, the outputs bound by their names and read in the target's
    order, `((a, h, z) ↦ (h, a))(𝑔≻(m, z_d, c, h_choice))`. No projection of
    the image is written (AMD-SG-034 §4 item 6). A row that composes with
    the law's section at a label applies the section to the point,
    `(a_d, h_d, z_d) ↦ 𝑔_keep≻(a_d, h_d, z_d)`."""
    if row.section is not None:
        point, points = bound_point(ctx, row.identity, source_coordinates)
        return S.Lambda(
            point,
            S.Apply(
                reference_term(section_identity(ctx, row.builder, row.section)),
                (tuple_term(points[i] for i in source_coordinates),),
            ),
        )
    spec = law_of_motion_kernel(ctx.stage_object, row.definition)
    point, points = bound_point(ctx, row.identity, source_coordinates)
    points = points_at_policy(ctx, row, points)
    if any(identity not in points for identity in spec.index):
        return S.Unresolved(row.identity, "law-of-motion coordinate adaptation")
    image = S.Apply(
        reference_term(row.definition), (tuple_term(points[identity] for identity in spec.index),)
    )
    forward, outputs = _law_outputs(ctx, row)
    if forward is None:
        return S.Unresolved(row.identity, "forward-owned law-of-motion outputs")
    target = tuple(target_coordinates)
    if target == tuple(forward.outputs):
        return S.Lambda(point, image)
    produced = {
        identity: reference_term(variable.identity)
        for identity, (variable, _) in zip(forward.outputs, outputs)
    }
    combined = {**points, **produced}
    if any(identity not in combined for identity in target):
        return S.Unresolved(row.identity, "law-of-motion output projection")
    read = S.Lambda(outputs, tuple_term(combined[identity] for identity in target))
    return S.Lambda(point, S.Apply(read, (image,)))


# the base of the variables a law of motion's outputs are bound as
LAW_OUTPUTS = 700


def _law_forward(ctx, law):
    """The forward row that applies the law of motion `law`, the one
    `Pushforward` whose definition it is; None where no forward row applies
    it."""
    return next(
        (
            op
            for op in wire_table(ctx.stage_object).table.primitive_rows
            if op.kind == "Pushforward" and op.definition == law
        ),
        None,
    )


def _law_outputs(ctx, row, label=None):
    """The forward row that applies the law of motion a row composes with,
    and the continuation coordinates that law writes, bound one variable each
    under the coordinate's name (AMD-SG-034 §4 item 6); `(None, ())` where no
    forward row applies it. Where a label is given, or the row composes with
    the law's section at a label, the coordinates are those of that label's
    branch."""
    forward = _law_forward(ctx, row.definition)
    if forward is None:
        return None, ()
    outputs = tuple(forward.outputs)
    label = label or row.section
    if label is not None:
        written = dict(
            branches_of(ctx.stage_object, block_box(ctx.stage_object, forward.builder))
        )[label]
        outputs = tuple(o for o in outputs if o in written)
    return forward, coordinate_bindings(ctx, outputs, row.identity, LAW_OUTPUTS)


def law_outputs_rule(ctx, row, source_coordinates, label=None):
    """The outputs of the law of motion a row composes with, as the statement
    a card states once under `where` (AMD-SG-034 §4 item 6):
    `(a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔≻(m, z_d, c, h_choice)` at no policy,
    and at the policy the row is held at the law written out, each control
    read as its policy at the point, `= 𝑔≻(m, z_d, 𝑐(m, z_d), ℎ_choice(m,
    z_d))` (RL14); at a label, the outputs of that label's branch as the
    section at the decision states, `(w_kp, h_kp, z_kp) = 𝑔_keep≻(a_d, h_d,
    z_d)`; None where the law writes one coordinate, whose name the
    coordinate's own set states."""
    label = label or row.section
    forward, outputs = _law_outputs(ctx, row, label)
    if forward is None or len(outputs) <= 1:
        return None
    point, points = bound_point(ctx, row.identity, source_coordinates)
    if label is not None:
        applied = S.Apply(
            reference_term(section_identity(ctx, row.builder, label)),
            (tuple_term(points[i] for i in source_coordinates if not ctx.labels(i)),),
        )
    else:
        spec = law_of_motion_kernel(ctx.stage_object, row.definition)
        points = points_at_policy(ctx, row, points)
        if any(identity not in points for identity in spec.index):
            return None
        applied = S.Apply(
            reference_term(row.definition),
            (tuple_term(points[identity] for identity in spec.index),),
        )
    return Rule(
        Compare(
            tuple_term(reference_term(variable.identity) for variable, _ in outputs), "=", applied
        )
    )


# --- an aggregation ---


def _aggregate(ctx, row, inputs, output, references):
    """The Aggregation rule instantiated pointwise on the coordinates the row
    reads."""
    kernel, carrier, point, points, used = _aggregator_kernel_and_carrier(ctx, row, inputs, output)
    domain = coordinate_domain(ctx, output.coordinates, row.identity)
    joined = S.Lambda(
        point, tuple_term(_at(sort, references[sort.identity], points) for sort in used)
    )
    return _instantiate(
        "Aggregation",
        {
            "D": domain,
            "L": kernel.bindings[0][1],
            "Lout": carrier.codomain,
            "G": kernel,
            "Q_G": carrier.domain,
        },
        joined,
        {T.Named("D"): point},
    )


def _aggregator_kernel_and_carrier(ctx, row, inputs, output):
    """The policy-specialized scalar kernel and its exact
    restricted carrier."""
    point, points = bound_point(ctx, row.identity, output.coordinates)
    domain = coordinate_domain(ctx, output.coordinates, row.identity)
    points = points_at_policy(ctx, row, points)
    spec = aggregator_kernel(ctx.stage_object, row)
    position = tuple(row.outputs).index(output.identity)
    mentioned = {
        term.symbol.name
        for term in _walk(spec.terms[position])
        if isinstance(term, T.Sym) and is_wire_symbol(term)
    }
    # the value a derivative term differentiates is read by the row as well,
    # though the kernel takes the derivative as one argument (MB-A16, MB-A19)
    mentioned |= {
        term.symbol.name
        for node, _ in spec.derivative_terms
        for term in _walk(node)
        if isinstance(term, T.Sym) and is_wire_symbol(term)
    }
    used = tuple(sort for sort in inputs if sort.identity in mentioned)
    ranges = tuple(wire_type(ctx.stage_object, sort).sort[4] for sort in used)
    value = bound_variable(row.identity, "r", product(ranges), 110)
    scalar_values = {
        sort.identity: component(reference_term(value.variable.identity), n, len(used))
        for n, sort in enumerate(used)
    }
    local = dict(points)
    local.update({identity.field: value for identity, value in points.items()})
    local.update(scalar_values)
    # a derivative term of a value the row reads stands in the kernel as one
    # argument (MB-A16); here it is the operator D applied to the value as
    # the row reads it, `D_{m_next}𝑉≻(…)`, and nothing is differentiated
    for node, key in spec.derivative_terms:
        local[key] = T.Operator(
            "D",
            node.subs,
            (term_by_reference(ctx, node.args[0], row.identity, row.builder, local),),
        )
    scalar = term_by_reference(ctx, spec.terms[position], row.identity, row.builder, local)
    result = wire_type(ctx.stage_object, output).sort[4]
    # The carrier's domain is the pack of the value inputs and the point. That
    # the aggregator's value lies in the declared set of its output is the
    # arithmetic-definedness the obligations record, not a restriction of the
    # domain.
    kernel = S.Lambda((value,) + point, scalar)
    return kernel, S.FunctionSet(product((value.domain, domain)), result), point, points, used


# --- an expectation ---


def expectation(bindings, body):
    """The expectation as the file writes it, `E_{Ψ}[body]`: the operator `E`
    binding the shocks one variable each under their names, the body read at
    them (§4 item 7). The law is the shock's declaration, which
    the shock's name reaches; no measure is constructed here."""
    return T.Operator("E", tuple(T.Var(variable.identity) for variable, _ in bindings), (body,))


# --- a push-forward, a policy insertion and a distribution extension ---

# the base of the event a measure is read at
EVENT = 800


def _forward_measure(ctx, row, source, output, reference):
    """The measure a forward row writes, by the mass it gives an event `B` of
    the target space, `B` ranging over its measurable sets: a
    push-forward along the law at the policy by the mass of the preimage,
    the law written out with each control read as its policy at the point,
    `B ↦ μ({m_d ∈ Xm | 𝑔≻(m_d, 𝑐(m_d)) ∈ B})` (restrict a domain, apply at a
    point; RL14);
    a policy insertion by the mass of the states whose pair with the policy
    lies in the event; an extension by a declared law by the integral, over
    the source point, of the law's mass on the event's section,
    `B ↦ ∫_{(m_d, ν) ∈ ℝ₊₊ × ℝ} [P_{Ψ|ν}(ν)({Ψ ∈ Xψ | (m_d, ν, Ψ) ∈ B})]
    μ(d(m_d, ν))`, the law by reference to its declaration, applied at the
    coordinates it is conditioned on, and the shocks' sets by their declared
    names; a push-forward into one label's branch by the mass of the states
    the policy sends to that label whose section value lies in the event,
    `μ_keep≻(B) = μ({x | 𝑑(x) = keep ∧ 𝑔_keep≻(x) ∈ B})`, and, for a
    draw, `μ_survive≻(B) = μ⊗P_s({x, s | s = survive ∧ 𝑔_survive≻(x) ∈ B})`.
    No measure is constructed from indicators (§4 item 7)."""
    owner = row.identity
    source_domain = coordinate_domain(ctx, source.coordinates, owner)
    target_domain = coordinate_domain(ctx, output.coordinates, owner)
    event = bound_variable(owner, "B", measurable_sets(target_domain, owner), EVENT)
    B = reference_term(event.variable.identity)
    # the source coordinates as `restrict` binds them, by their identities
    names = {identity: reference_term(identity) for identity in source.coordinates}
    if row.kind == "Pushforward":
        label = output.identity.field
        if label is not None:
            # the states the policy sends to the label, pushed along the
            # section: μ_keep≻(B) = μ({x | 𝑑(x) = keep ∧ 𝑔_keep≻(x) ∈ B})
            chosen = points_at_policy(ctx, row, names)
            # the label coordinate: the policy's value at the state for a
            # choice, the drawn coordinate of the extended measure for a draw
            key = next(identity for identity in chosen if ctx.labels(identity))
            image = S.Apply(
                reference_term(section_identity(ctx, row.builder, label)),
                (
                    tuple_term(
                        names[identity]
                        for identity in source.coordinates
                        if not ctx.labels(identity)
                    ),
                ),
            )
            preimage = restrict(
                source.coordinates,
                source_domain,
                (Compare(chosen[key], "=", T.Sym(T.Constant(label))), Member(image, B)),
            )
            return S.Measure(target_domain, event, S.Apply(reference, (preimage,))), None
        # at the policy the law is written out, each control read as its
        # policy at the source point, `𝑔≻(m_d, 𝑐(m_d))` (RL14)
        index = law_of_motion_kernel(ctx.stage_object, row.definition).index
        values = points_at_policy(ctx, row, names)
        if any(identity not in values for identity in index):
            return S.Unresolved(owner, "law-of-motion coordinate adaptation"), None
        image = S.Apply(
            reference_term(row.definition), (tuple_term(values[identity] for identity in index),)
        )
        preimage = restrict(source.coordinates, source_domain, (Member(image, B),))
        return S.Measure(target_domain, event, S.Apply(reference, (preimage,))), None
    if row.kind == "PolicyInsertion":
        values = points_at_policy(ctx, row, names)
        if any(identity not in values for identity in output.coordinates):
            return S.Unresolved(owner, "policy coordinate adaptation"), None
        pair = tuple_term(values[identity] for identity in output.coordinates)
        preimage = restrict(source.coordinates, source_domain, (Member(pair, B),))
        return S.Measure(target_domain, event, S.Apply(reference, (preimage,))), None
    # the extension integrates over the source point, its coordinates bound
    # one variable each, and reads the shocks under their own names
    held = coordinate_bindings(ctx, source.coordinates, owner, 100)
    binder = (
        held[0].variable if len(held) == 1 else T.Subject(tuple(variable for variable, _ in held))
    )
    points = {
        identity: reference_term(variable.identity)
        for identity, (variable, _) in zip(source.coordinates, held)
    }
    shocks = tuple(
        identity for identity in output.coordinates if identity not in source.coordinates
    )
    ordered = {**points, **{identity: reference_term(identity) for identity in shocks}}
    section = restrict(
        shocks,
        coordinate_domain(ctx, shocks, owner),
        (Member(tuple_term(ordered[identity] for identity in output.coordinates), B),),
    )
    law = _declared_law(ctx, row, points_at_policy(ctx, row, points))
    if isinstance(law, S.Unresolved):
        return law, None
    body = S.Integral((binder, source_domain), reference, S.Apply(law, (section,)))
    return S.Measure(target_domain, event, body), None


def _declared_law(ctx, row, values):
    """The declared law an extension draws its shocks under, by reference to
    its declaration and, where the file conditions it, applied at the
    coordinates it reads, `P_{Ψ|ν}(ν)`; `values` holds each coordinate's
    reference, the controls read as the policy."""
    table = ctx.stage_object.definitions
    laws = [
        table[reference]
        for reference in row.references
        if reference in table and table[reference].kind == "distribution"
    ]
    if len(laws) != 1:
        return S.Unresolved(row.identity, "one declared distribution for the extension")
    definition = laws[0]
    given = tuple(name for name, _ in definition.coordinates)
    if not given:
        return reference_term(definition.identity)
    arguments = []
    for name in given:
        identity = next((held for held in values if held.field == name), None)
        if identity is None:
            return S.Unresolved(row.identity, "distribution conditioning coordinate " + name)
        arguments.append(values[identity])
    return S.Apply(reference_term(definition.identity), (tuple_term(arguments),))


def points_at_policy(ctx, row, points):
    """The points with each control read as the supplied policy at its state
    coordinates."""
    result = dict(points)
    for identity in row.policy:
        sort = wire_table(ctx.stage_object).sort_of(identity)
        field = Identity("field", stage=ctx.stage_name, perch=identity.perch, field=identity.field)
        result[field] = _at(sort, reference_term(identity), points)
    return result


def _policy_data(ctx, row, source_coordinates, target_coordinates):
    """The free policy reference and its coordinate insertion, not
    a selector."""
    point, points = bound_point(ctx, row.identity, source_coordinates)
    controls, values = [], []
    for identity in row.policy:
        sort = wire_table(ctx.stage_object).sort_of(identity)
        field = Identity("field", stage=ctx.stage_name, perch=identity.perch, field=identity.field)
        controls.append(field)
        values.append(_at(sort, reference_term(identity), points))
    policy = S.Lambda(point, tuple_term(values))
    # The generic policy rule uses (state, control); adaptation keeps the
    # native coordinate order rather than changing a graph's wire order.
    chosen, choices = bound_point(ctx, row.identity, controls, 200)
    adapted = {**points, **choices}
    if any(identity not in adapted for identity in target_coordinates):
        return None
    return point, policy, chosen, adapted, coordinate_domain(ctx, controls, row.identity)


def state_choice_measure(stage, box):
    """The joint finite measure obtained by applying (id, policy)."""
    ctx = StageNames(stage)
    row = next(
        (
            row
            for row in wire_table(stage).table.primitive_rows
            if row.builder == box.name and row.kind == "Pushforward" and row.policy
        ),
        None,
    )
    if row is None:
        return S.Unresolved(box.name, "forward decision builder with a supplied policy")
    states = ctx.coordinates(row.policy[0].perch, roles=("state",))
    controls = tuple(
        Identity("field", stage=stage.name, perch=p.perch, field=p.field) for p in row.policy
    )
    point, points = bound_point(ctx, row.identity, states)
    domain = coordinate_domain(ctx, states, row.identity)
    values = points_at_policy(ctx, row, points)
    joint_domain = coordinate_domain(ctx, states + controls, row.identity)
    measure = bound_variable(row.identity, "mu", S.FiniteMeasureSet(domain), 400, role="input")
    insertion = S.Lambda(point, tuple_term(values[i] for i in states + controls))
    body, guard = _instantiate(
        "Pushforward",
        {
            "D": domain,
            "Y": joint_domain,
            "g": insertion,
        },
        reference_term(measure.variable.identity),
        {T.Named("D"): point},
    )
    return S.Lambda(
        ((measure.variable, T.Comprehension(measure.variable, measure.domain, (guard,))),), body
    )


# --- an argmax ---


def _argmax_definition(ctx, row, inputs, outputs, references):
    """The formula of an `Argmax` row's one output and its guard: the
    `Argmax` definition at the maximand, read at the point and at the
    choice, the controls together one variable, over the graph of the
    feasibility correspondence; the answer is the set of the maximizers.
    `Unresolved` where the row writes several outputs or names no unknown,
    holds no `argmax` with one binder per unknown, or reads no input."""
    if len(outputs) != 1 or not row.unknowns:
        return S.Unresolved(row.identity, "joint policy candidate representation"), None
    declaration = next(
        (
            term
            for term in _walk(row.equations)
            if isinstance(term, T.Operator) and term.head == "argmax"
        ),
        None,
    )
    source = inputs[0] if inputs else None
    if declaration is None or len(declaration.subs) != len(row.unknowns) or source is None:
        return S.Unresolved(row.identity, "maximisation objective and feasible set"), None
    output = outputs[0]
    point, points = bound_point(ctx, row.identity, output.coordinates)
    domain = coordinate_domain(ctx, output.coordinates, row.identity)
    # the choice is one variable: the control, or the controls together
    (choice,), chosen = _joint_point(ctx, row.identity, row.unknowns, 130)
    local = {**points, **{i.field: value for i, value in points.items()}}
    feasible = choice.domain
    for unknown, sub in zip(row.unknowns, declaration.subs):
        selected = chosen[unknown]
        declared = (
            term_by_reference(ctx, sub.set, row.identity, row.builder, local)
            if isinstance(sub, T.In)
            else declared_set_term(ctx, ctx.declared_set(unknown), unknown)
        )
        if len(row.unknowns) == 1:
            feasible = declared
        elif isinstance(sub, T.In):
            feasible = T.Comprehension(
                T.Subject((choice.variable,)), feasible, (Member(selected, declared),)
            )
        local[unknown] = selected
        local[sub.var if isinstance(sub, T.In) else sub.name] = selected
    gamma = S.Lambda(point, feasible)
    state = tuple_term(points[identity] for identity in output.coordinates)
    graph = T.Comprehension(
        T.Subject(tuple(variable for variable, _ in point) + (choice.variable,)),
        product(tuple(held for _, held in point) + (choice.domain,)),
        (Member(reference_term(choice.variable.identity), S.Apply(gamma, (state,))),),
    )
    adapted = {**points, **chosen}
    objective = S.Lambda(point + (choice,), _at(source, references[source.identity], adapted))
    candidate = bound_variable(
        row.identity,
        joint_name(row.unknowns),
        S.MeasurableMapSet(domain, choice.domain),
        132,
        role="control",
        perch=row.unknowns[0].perch,
    )
    X, C = T.Named("X"), T.Named("C")
    return _instantiate(
        "Argmax",
        {
            "X": domain,
            "C": choice.domain,
            "H": graph,
            "L": wire_type(ctx.stage_object, source).sort[4],
            "Gamma": gamma,
        },
        objective,
        {
            X: point,
            C: (choice,),
            T.Product((X, C)): point + (choice,),
            S.MeasurableMapSet(X, C): (candidate,),
        },
    )


# --- a row whose output is its own unknown ---

# The key of the one relation definition of the table of primitive
# definitions, which a row whose output is its own unknown instantiates where
# its relation holds no explicit side (`grains.explicit_side`), whatever the
# kind of the row. Its free names: the inputs' set `W`, the domain `X` and the
# codomain `C` of the candidates, the set `D` of the pairs the relation may
# admit, the candidates `F`, the pairs `A(w)` the inputs admit, the point
# `h(w, d)` a candidate is read at, and the relation `R(w, d, y)` in the
# candidate's value `y` there.
RELATION = "Relation"


def _relation_definition(ctx, row, inputs, outputs, references, pack):
    """The formula of the one output of a row whose output is its own
    unknown and whose relation holds no explicit side, and its guard: the
    relation definition `RELATION` at the candidate policies. A solve and a
    system of candidate statements range over the decision states, every
    state admitted and the candidate read at the state itself, their
    relation the residuals equal to zero or the members read at the point,
    the policy's value at the point being the candidate's. The
    identification ranges over the admitted pairs `(a, x)` of a point of its
    candidate's grid and a value the candidate admits there, the candidate
    policy read at the grid line's value at that pair, `a + x`, and its
    relation the truth of that value's equality with `x`:
    `∀ a ∈ Xa, x ∈ 𝑐≻(a): (f(a + x) = x)` where the candidate carries a
    correspondence, `x ∈ {x ∈ ℝ₊₊ | x = 𝑐≻(a)}` where it is a function
    (`_grid_pairs`). No record states whether some function satisfies the
    relation: where two admitted pairs reach one value of the grid line with
    different values, the set it defines is empty.
    `Unresolved` where the row writes several outputs, names no unknown, or
    forms no relation."""
    if len(outputs) != 1 or not row.unknowns:
        return S.Unresolved(row.identity, "joint solution candidate representation"), None
    output = outputs[0]
    domain = coordinate_domain(ctx, output.coordinates, row.identity, use_choice_sets=False)
    result = wire_type(ctx.stage_object, output).sort[4]
    # the candidates are the policies with the feasibility the file declares,
    # by the correspondence where it declares one and by the law's image
    # otherwise, the same set the Evaluation carries (AMD-SG-034 §10 item 4)
    candidate = bound_variable(
        row.identity,
        joint_name(row.unknowns),
        policy_carrier(
            ctx, output.coordinates, row.unknowns, Identity("Evaluation", address=row.builder)
        ),
        140,
        role="control",
        perch=row.unknowns[0].perch,
    )
    # the candidate's value at the point it is read at
    value = bound_variable(row.identity, "y", result, 142)
    held = reference_term(value.variable.identity)
    narrowed = False
    if _solve_head(row) is not None or _formed_at_the_point(ctx, row):
        pairs, points = bound_point(ctx, row.identity, output.coordinates)
        pair_set, admitted = domain, domain
        at = tuple_term(points[identity] for identity in output.coordinates)
        holds = _holds_at_the_point(ctx, row, references, pairs, points, held)
        if isinstance(holds, S.Unresolved):
            return holds, None
    else:
        # the grid line gives one coordinate of the policy's domain
        read = (
            _grid_pairs(ctx, row, inputs, references, result)
            if len(output.coordinates) == 1
            else S.Unresolved(row.identity, "solution coordinate relation")
        )
        if isinstance(read, S.Unresolved):
            return read, None
        pairs, pair_set, admitted, at, taken, narrowed = read
        holds = Compare(held, "=", taken)
    # the pairs are bound in the quantifier's own subscripts, each over the
    # values it may take there, so that the pairs the quantifier ranges over
    # are the admitted ones, `A(w)`
    body, guard = _instantiate(
        RELATION,
        {
            "W": pack.domain,
            "X": domain,
            "C": result,
            "D": pair_set,
            "F": candidate.domain,
            "A": S.Lambda((pack,), admitted),
            "h": S.Lambda((pack,) + tuple(pairs), at),
            "R": S.Lambda((pack,) + tuple(pairs) + (value,), _truth(row.identity, holds)),
        },
        reference_term(pack.variable.identity),
        {
            S.MeasurableMapSet(T.Named("X"), T.Named("C")): (candidate,),
            T.Named("D"): tuple(pairs),
        },
    )
    return (_admitted_subscripts(body) if narrowed else body), guard


def _admitted_subscripts(term):
    """The term with each subscript that ranges over the values of a set a
    correspondence admits written over that set: `x ∈ {x ∈ ℝ₊₊ | x ∈
    𝑐≻(a)}` as `x ∈ 𝑐≻(a)`, the two being one set, since a correspondence's
    values lie in its declared set. A caller's bindings over a set are made
    by `S.rebind`, which binds over a set expression, and the value of a
    correspondence at a point is an application; the subscript is written
    over it here, as an argmax's is written over `Γ(m_d)`."""
    if isinstance(term, T.In):
        held = term.set
        if (
            isinstance(held, T.Comprehension)
            and len(held.conds) == 1
            and isinstance(held.conds[0], Member)
        ):
            variables = S.subject_coordinates(held.bound)
            element = held.conds[0].subject
            if (
                len(variables) == 1
                and isinstance(element, T.Sym)
                and S.variable_identity(element.symbol) == S.variable_identity(variables[0])
            ):
                return dataclasses.replace(term, set=held.conds[0].set)
        return term
    if isinstance(term, tuple):
        return tuple(_admitted_subscripts(item) for item in term)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return dataclasses.replace(
            term,
            **{
                field.name: _admitted_subscripts(getattr(term, field.name))
                for field in dataclasses.fields(term)
            },
        )
    return term


def _holds_at_the_point(ctx, row, references, point, points, held):
    """The relation of a solve or of a system of candidate statements at a
    decision state, in the value `held` the candidate takes there: of a
    solve that reads its residuals from an input, that input at the state
    and the value, equal to zero; of a solve whose residuals are its own
    terms (`_own_residuals`), those residuals at the state and the value,
    equal to zero; of a system (`system_relation`), the relation read at the
    state with the policy's value there the candidate's."""
    unknowns = tuple(row.unknowns)
    valued = {identity: component(held, n, len(unknowns)) for n, identity in enumerate(unknowns)}
    if _solve_head(row) is None:
        relation = system_relation(ctx, row, points)
        if isinstance(relation, S.Unresolved):
            return relation
        # the policy read at the state is the candidate's value there
        read = {ctx.function_wire(unknowns[0]): S.Lambda(tuple(point), held)}
        return _reduced(S.substitute(relation, read))
    residual = _residual_input(ctx, row)
    if residual is not None:
        target = resolve_set(ctx, wire_type(ctx.stage_object, residual).sort[4], residual.identity)
        zero = (
            T.Tuple(tuple(T.Number(0) for _ in target.factors))
            if isinstance(target, T.Product)
            else T.Number(0)
        )
        at = {**points, **valued}
        return Compare(_at(residual, references[residual.identity], at), "=", zero)
    own = _own_residuals(ctx.stage_object, ctx, row)
    if own is None:
        return S.Unresolved(row.identity, "solve relation")
    _, own_points, residuals = own
    # the unknowns, bound at the point beside the states, take the
    # candidate's value there
    taken = {
        S.variable_identity(own_points[identity]): value for identity, value in valued.items()
    }
    if not any(isinstance(residual, Member) for residual in residuals):
        zero = (
            T.Number(0) if len(residuals) == 1 else T.Tuple(tuple(T.Number(0) for _ in residuals))
        )
        return _reduced(S.substitute(Compare(zero, "=", tuple_term(residuals)), taken))
    # a residual read as a membership holds as that membership, and every
    # other residual equals zero; the conditions conjoined in the line's
    # order, the conjunction nested on the left
    held = [
        residual if isinstance(residual, Member) else Compare(T.Number(0), "=", residual)
        for residual in residuals
    ]
    relation = held[0]
    for part in held[1:]:
        relation = And(relation, part)
    return _reduced(S.substitute(relation, taken))


def _grid_pairs(ctx, row, inputs, references, result):
    """The pairs the identification `c = c[>]` ranges over, as the relation
    definition reads them: the bindings of a point `a` of its candidate's
    grid and of a value `x`, `x` bound over the values the candidate admits
    at `a`; the set of the pairs, the grid's points and the values; the
    pairs admitted, those whose value the candidate admits at their point;
    the grid line read at the admitted value, `a + x` of `m_d[>] = a +
    c[>]`, where the policy is read (`_grid_line_at`); `x`, the value the
    policy equals there; and whether the candidate carries a
    correspondence. A candidate that carries one admits the values of the
    correspondence at `a`, `𝑐≻(a)`, the segment `(0, 𝑐≻(0)]` at zero saving
    included, so that the relation pairs each admitted value with its own
    value of the grid line and not the image of one correspondence with the
    image of another; a candidate that is a function admits its one value,
    `{x ∈ ℝ₊₊ | x = 𝑐≻(a)}`, where the grid line's value is `𝑚_d≻(a)`. A
    grid that holds a multiplier is bound as one variable over the
    observable set (AMD-SG-035 §5, fold B)."""
    if len(row.unknowns) != 1:
        return S.Unresolved(row.identity, "joint solution candidate representation")
    read = _identification_wires(ctx, row, inputs)
    if isinstance(read, S.Unresolved):
        return read
    value, field, _, grid = read
    point, points = (
        _joint_point(ctx, row.identity, value.coordinates, 100)
        if any(ctx.role(identity) == "multiplier" for identity in value.coordinates)
        else bound_point(ctx, row.identity, value.coordinates)
    )
    taken = bound_variable(row.identity, "x", result, 143)
    x = reference_term(taken.variable.identity)
    candidate = _at(value, references[value.identity], points)
    several = wire_table(ctx.stage_object).carries_correspondence(value.identity)
    admits = Member(x, candidate) if several else Compare(x, "=", candidate)
    pair_set = product(tuple(held for _, held in point) + (result,))
    admitted = T.Comprehension(
        T.Subject(tuple(variable for variable, _ in point) + (taken.variable,)),
        pair_set,
        (admits,),
    )
    values = T.Comprehension(T.Subject((taken.variable,)), result, (admits,))
    pairs = tuple(point) + ((taken.variable, values),)
    at = _grid_line_at(ctx, row, grid, field, x, points, references)
    return pairs, pair_set, admitted, at, x, several


def _identification_wires(ctx, row, inputs):
    """The wires the identification `c = c[>]` is read through, by the rules
    of a statement across two perches: the candidate its line's right side
    names at the continuation perch, `𝑐≻`, with that field's identity; and
    the coordinate function of the grid, `𝑚_d≻`, with the address of the
    line that writes it, the line of the block whose left side is a state
    coordinate of the unknown's perch under the continuation mark, `m_d[>] =
    a + c[>]`. `Unresolved` where the line's right side names no one field
    whose wire the row reads, or no such line writes an input of the row."""
    stage = ctx.stage_object
    table = stage.definitions
    core = relation_of(table[row.statements[0]].equations[0]) if row.statements else None
    named = tuple(ctx.mentioned(core.rhs, row.builder)) if isinstance(core, T.Equation) else ()
    wires = {sort.identity: sort for sort in inputs}
    if len(named) != 1 or ctx.function_wire(named[0]) not in wires:
        return S.Unresolved(row.identity, "solution coordinate relation")
    field = named[0]
    value = wires[ctx.function_wire(field)]
    perch = row.unknowns[0].perch
    for sort in inputs:
        address = _coordinate_line(ctx, sort.identity, perch)
        if sort is not value and address is not None:
            return value, field, sort, address
    return S.Unresolved(row.identity, "solution coordinate relation")


def _coordinate_line(ctx, identity, perch):
    """The address of the line that writes the wire `identity` where its
    left side is a state coordinate of `perch` under the continuation mark,
    `m_d[>] = a + c[>]`, the grid line; None for any other wire."""
    stage = ctx.stage_object
    producer = wire_table(stage).produced.get(identity)
    if producer is None or not producer.statements:
        return None
    position = tuple(producer.outputs).index(identity)
    statements = tuple(producer.statements)
    address = statements[position] if len(statements) == len(producer.outputs) else statements[0]
    line = stage.definitions.get(address)
    core = relation_of(line.equations[0]) if line is not None and line.equations else None
    if not (isinstance(core, T.Equation) and isinstance(core.lhs, T.Sym)):
        return None
    symbol = core.lhs.symbol
    marked = (
        isinstance(symbol, T.Variable)
        and isinstance(symbol.when, T.At)
        and isinstance(symbol.when.side, T.Continuation)
    )
    coordinate = Identity("field", stage=ctx.stage_name, perch=perch, field=symbol.name)
    return address if marked and ctx.role(coordinate) == "state" else None


def _grid_line_at(ctx, row, address, field, x, points, references):
    """The grid line read at an admitted value: the right side of the line
    at `address`, `a + c[>]` of `m_d[>] = a + c[>]`, read at the point
    `points` with the candidate `field` the identification names read as
    the admitted value `x`, `a + x`, and every other function the line reads
    as the identification's input at the point. The grid line is read as
    the file writes it, not as a merged row's map, which may hold the
    candidate's own map in its place."""
    stage = ctx.stage_object
    rendering = wire_table(stage)
    rhs = relation_of(stage.definitions[address].equations[0]).rhs
    local = {**points, **{identity.field: value for identity, value in points.items()}}
    local[field] = x
    local[ctx.function_wire(field)] = x
    for identity, reference in references.items():
        if identity == ctx.function_wire(field) or identity in local:
            continue
        sort = rendering.sort_of(identity)
        if all(coordinate in points for coordinate in sort.coordinates):
            read = _at(sort, reference, points)
            local[identity] = read
            if identity.kind in ("function", "choice") and identity.perch is not None:
                port = Identity(
                    "field", stage=ctx.stage_name, perch=identity.perch, field=identity.field
                )
                local.setdefault(port, read)
    return term_by_reference(ctx, rhs, row.identity, row.builder, local, declared=True)


def _truth(owner, predicate):
    truth = bound_variable(owner, "truth", T.FiniteSet((T.Number(0), T.Number(1))), 141)
    ref = reference_term(truth.variable.identity)
    condition = Or(
        And(Compare(ref, "=", T.Number(1)), predicate),
        And(Compare(ref, "=", T.Number(0)), Not(predicate)),
    )
    domain = T.Comprehension(truth.variable, truth.domain, (condition,))
    return S.Sup((truth.variable, domain), ref)


def _formed_at_the_point(ctx, row):
    """Whether a relation is formed from lines read at the point: no `solve`
    head, and its lines not all coordinate relations `c = c[>]`, which the
    identification writes."""
    table = ctx.stage_object.definitions
    cores = [table[a].equations[0] for a in row.statements if a in table and table[a].equations]
    return (
        _solve_head(row) is None
        and bool(cores)
        and not all(isinstance(c, T.Equation) and isinstance(c.rhs, T.Sym) for c in cores)
    )


def system_relation(ctx, row, points, *, by_name=False):
    """The relation a row of candidate statements holds at the point
    (AMD-SG-035 §3): its members in file order, each read at `points` by
    `line_at_point`, a member with a clause as its `Complementarity` and one
    without as its equation, conjoined, the conjunction nested on the left.
    With `by_name`, the outputs of a law of several coordinates are read
    under the names the row binds them by, and the controls at a point that
    is a tuple by their bare names, as the row's rule states them
    (`_rules_at_the_point`); the relation of the row's formula reads the law
    itself and each control at the point."""
    table = ctx.stage_object.definitions
    held = [
        line_at_point(
            ctx, table[a], tuple(row.unknowns), points, owner=row.identity, by_name=by_name
        )
        for a in row.statements
        if a in table and table[a].equations
    ]
    if not held or any(isinstance(part, S.Unresolved) for part in held):
        return S.Unresolved(row.identity, "system relation")
    relation = held[0]
    for part in held[1:]:
        relation = And(relation, part)
    return relation


def _solve_head(row):
    """The `solve` operator of a relation's statement, or None where the
    statement writes no `solve`, as the identification's `c = c[>]` does."""
    return next(
        (
            term
            for term in _walk(row.equations)
            if isinstance(term, T.Operator) and term.head == "solve"
        ),
        None,
    )


def _own_residuals(stage, ctx, row, *, by_name=False):
    """The residuals of a solve whose residuals are the row's own terms, and
    no input of the row, at the point of the decision states and the
    unknowns: the bindings of that point, each coordinate's reference, and
    one residual per argument the line writes under `solve`, read from the
    row's maps, the residuals as the fold reduced them, a local name the line
    reads being the wire it was folded to. A value at the next perch is the
    function the block pulls back, at the point (`_row_scope`), and an
    unnamed result the row reads is its own expression there,
    `r₁ = c − 𝑐≻(𝑔≻(m, z_d, c, h_choice))`; with `by_name`, where the law
    writes several coordinates, that function at the names the row binds the
    law's outputs by, `𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)`, whose line
    `law_outputs_read` states once under `where`. A residual that is the
    difference between a term and a correspondence the row reads,
    `c − c[>]` against the candidate of a line written with a clause, is
    read as the membership of the term in the correspondence's values,
    `c ∈ 𝑐≻(…)`, since the residual is zero exactly where the term is one of
    the values the correspondence admits (`_membership`): equality where the
    candidate admits one value and the segment where it admits several.
    None where the maps hold no one residual per argument."""
    head = _solve_head(row)
    if head is None or not head.args:
        return None
    count = len(head.args)
    terms = tuple(row.maps)
    if (
        len(terms) == 1
        and count > 1
        and isinstance(terms[0], T.Tuple)
        and len(terms[0].items) == count
    ):
        terms = tuple(terms[0].items)
    if len(terms) != count:
        return None
    states = ctx.coordinates(row.unknowns[0].perch, roles=("state",))
    coordinates = tuple(states) + tuple(i for i in row.unknowns if i not in states)
    point, points = bound_point(ctx, row.identity, coordinates)
    scope = _row_scope(stage, row, terms, coordinates)
    rendering = wire_table(stage)
    for identity in row.inputs:
        sort = rendering.sort_of(identity)
        if identity.is_result and all(i in points for i in sort.coordinates):
            scope[identity] = apply_at(
                wire_expression(stage, sort, expand=True),
                tuple_term(points[i] for i in sort.coordinates),
            )
    if by_name:
        scope.update(_law_named_reads(stage, ctx, row, points))
    residuals = tuple(_membership(ctx, row, term, scope) for term in terms)
    return point, points, residuals


def _membership(ctx, row, term, scope):
    """One residual of a solve read in `scope`. A residual that reads one
    wire carrying a correspondence (`WireTable.carries_correspondence`), the
    candidate of a line written with a clause pulled back along the law,
    once and affinely with a nonzero coefficient is zero exactly where that
    wire takes the value the residual set to zero solved for it gives
    (`ranges.solved_for`, the rearrangement of an explicit statement), so
    it is read as the membership of that value in the correspondence's
    values: `c − c[>]` as `c ∈ 𝑐≻(…)`. Every other residual is read as the
    fold reduced it."""
    rendering = wire_table(ctx.stage_object)

    def read(part):
        return _reduced(
            term_by_reference(ctx, part, row.identity, row.builder, scope, declared=True)
        )

    held = [w for w in dict.fromkeys(wires_read(term)) if rendering.carries_correspondence(w)]
    if len(held) == 1:
        value = solved_for(T.Number(0), term, held[0], rendering.parameter_sets)
        if value is not None:
            return Member(read(value), read(wire_symbol(held[0])))
    return read(term)


def _law_names(stage, ctx, row):
    """The law of motion a row reads by name, the coordinates it writes and
    the variables the row binds them by: the one law that reads the row's
    unknowns (`_law_reading`), where it writes several coordinates; None
    where it writes one, whose name the coordinate's own set states, or no
    one law reads the unknowns."""
    law = _law_reading(ctx, tuple(row.unknowns))
    forward = _law_forward(ctx, law) if law is not None else None
    if forward is None or len(forward.outputs) <= 1:
        return None
    outputs = tuple(forward.outputs)
    return law, outputs, coordinate_bindings(ctx, outputs, row.identity, LAW_OUTPUTS)


def _law_named_reads(stage, ctx, row, points):
    """The values at the next perch a solve reads, each read at the names of
    the law's outputs (`_law_names`): the output of each pullback of the
    row's block along that law, `𝑐≻ ∘ 𝑔≻`, as the function it pulls back at
    those names, `𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)`, by its wire and by
    its field, where every coordinate the law reads stands at the row's
    point `points`, so that the names stand for the law at that point;
    nothing otherwise."""
    held = _law_names(stage, ctx, row)
    if held is None:
        return {}
    law, outputs, bindings = held
    spec = law_of_motion_kernel(stage, law)
    if any(identity not in points for identity in spec.index):
        return {}
    names = {
        identity: reference_term(variable.identity)
        for identity, (variable, _) in zip(outputs, bindings)
    }
    rendering = wire_table(stage)
    found = {}
    for other in rendering.table.primitive_rows:
        if (
            other.builder != row.builder
            or other.kind != "Pullback"
            or is_relation(other)
            or other.definition != law
            or other.section is not None
        ):
            continue
        for source, identity in zip(other.inputs, other.outputs):
            coordinates = rendering.sort_of(source).coordinates
            if not coordinates or any(i not in names for i in coordinates):
                continue
            value = S.Apply(reference_term(source), (tuple_term(names[i] for i in coordinates),))
            found[identity] = value
            if identity.perch is not None:
                port = Identity(
                    "field", stage=ctx.stage_name, perch=identity.perch, field=identity.field
                )
                found[port] = value
    return found


def law_outputs_read(stage, row):
    """The outputs of the law of motion the rules of a row read by name, as
    the statement its card states once under `where` (AMD-SG-034 §4 item 6;
    `card-redesign.md` §2, change 3): for a relation formed from lines read
    at the point, the law at the decision states with each control the
    policy there as the row's rules read it, by its bare name where the
    point is a tuple, `(y_f, y_p) = 𝑔≻(m_f, m_p, w_d, 𝑐, 𝑐_p)`, and at the
    point where it is one coordinate, `(y_f_ret, y_p_ret) = 𝑔≻(m_r,
    𝑐(m_r))` (change 4); for a solve whose residuals are its own terms, the
    law at the decision states and the unknowns, `(a_nxt_adj, h_nxt_adj,
    z_nxt_adj) = 𝑔≻(m, z_d, c, h_choice)`. The names are the variables the
    row binds the law's outputs by, which its rules read (`line_at_point`,
    `_law_named_reads`). None for every other row, and where the law writes
    one coordinate, whose name the coordinate's own set states. Kept for the
    version by the row."""
    if not is_relation(row):
        return None
    return kept_answer(
        stage, ("law outputs read", row.identity), lambda: _outputs_read(stage, row)
    )


def _outputs_read(stage, row):
    """`law_outputs_read` of a row whose output is its own unknown."""
    ctx = StageNames(stage)
    if explicit_side(stage, row) is not None:
        return None
    held = _law_names(stage, ctx, row)
    if held is None:
        return None
    law, _, bindings = held
    states = ctx.coordinates(row.unknowns[0].perch, roles=("state",))
    if _formed_at_the_point(ctx, row):
        _, points = bound_point(ctx, row.identity, states)
        arguments = {
            **points,
            **{
                control: _policy_at_point(ctx, control, points, bare=True)
                for control in row.unknowns
            },
        }
    elif _solve_head(row) is not None and _residual_input(ctx, row) is None:
        coordinates = tuple(states) + tuple(i for i in row.unknowns if i not in states)
        _, arguments = bound_point(ctx, row.identity, coordinates)
    else:
        return None
    spec = law_of_motion_kernel(stage, law)
    if any(identity not in arguments for identity in spec.index):
        return None
    applied = S.Apply(
        reference_term(law), (tuple_term(arguments[identity] for identity in spec.index),)
    )
    names = tuple_term(reference_term(variable.identity) for variable, _ in bindings)
    return Rule(Compare(names, "=", applied))


# --- the rules on an output ---


def output_rules(stage, row, output, inputs=None, outputs=None):
    """The relations a row declares on one of its outputs, each a `Rule` at
    the point (AMD-SG-034 §4 item 3, §10 items 8 and 10). An `Argmax` row's
    are the membership its line holds, `𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)}
    [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]`, and each property attached to its line by a
    dotted id, read at the point on the domain of the decision states,
    `𝑑𝑢(𝑐(m_d)) = 𝑑𝑉≻(𝑔≻(m_d, 𝑐(m_d))) ⟂ 𝑔≻(m_d, 𝑐(m_d)) ≥ 0 on Xm`. A row
    whose output is its own unknown (`grains.is_relation`) declares its
    relation: with an explicit side (`grains.explicit_side`) the relation its
    line writes with the sign the line writes, `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a))`,
    held with its clause read at the grid point where the line carries one
    (AMD-SG-035 §2); formed from candidate statements, `system_relation` on
    the domain of the decision states, `𝑑𝑢(𝑐(m_d)) = 𝑑𝑉≻(𝑔≻(m_d, 𝑐(m_d)))
    ⟂ 𝑔≻(m_d, 𝑐(m_d)) ≥ 0 on Xm` (AMD-SG-035 §3), the outputs of a law of
    several coordinates read by their names, `⟂ y_f ≥ 0`, and where the
    point is a tuple the controls by their bare names with the point named
    in the region note, `on (m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊`; the
    identification, the grid relation on the image of the grid,
    `𝑐(𝑚_d≻(a)) = 𝑐≻(a) on 𝑚_d≻(Xa)`, where a candidate written with a
    clause and its grid take every value the clause admits at zero saving;
    a solve, the head `(c, h_choice) = solve_{c, h_choice}(r₁, r₂)`, the
    residuals named as the lines of the unnamed input name them, and where
    the residuals are the row's own terms, those lines before the head, a
    residual read as a membership standing in the head as that membership,
    `c ∈ 𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)`. A pullback's on each
    output is the composite at a point of its domain, the law at the policy
    written out (RL14), `(𝑉≻ ∘ 𝑔≻(·, 𝑐))(m_d) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))`; an
    expectation's the integral at a point of its domain, the output at the
    point equal to the expectation there over the declared law of the
    shocks, `(2)(k_d) = E_{Ψ, θ}[𝑉≻(𝑔≻(k_d, 𝜍(k_d), Ψ, θ))]`; an
    Evaluation's the `Member` statements of the output's declared
    carrier with its feasibility, `𝑐 ∈ (Xm → ℝ₊₊) ∧ 𝑐(m_d) ∈ Γ(m_d)` (the
    plan's K row; `card-redesign.md` §2, change 2). An aggregation's on a
    named output is the line's relation at the point; a forward row's on
    its measure the mass it gives an event, `μ≻(B) = μ({m_d ∈ Xm |
    𝑔≻(m_d, 𝑐(m_d)) ∈ B})`, the measure read at the event its own binding
    names. Every other row declares no rule on its outputs.
    `inputs` and `outputs` are the row's wire sorts where the caller holds
    them, the measures of a forward row; the wire table's sorts otherwise."""
    if row.kind in ("Pushforward", "PolicyInsertion", "DistributionExtension"):
        return _forward_rules(stage, row, output, inputs, outputs)
    ctx = StageNames(stage)
    if row.kind == "Argmax":
        return _argmax_rules(stage, ctx, row)
    if is_relation(row):
        if explicit_side(stage, row) is not None:
            return _explicit_relation_rules(stage, ctx, row, output)
        if _formed_at_the_point(ctx, row):
            return _rules_at_the_point(ctx, row)
        if _solve_head(row) is not None:
            return _solve_rules(stage, ctx, row)
        return _grid_rules(stage, ctx, row, output)
    if row.kind == "Pullback":
        return _pullback_rules(stage, ctx, row, output)
    if row.kind == "Expectation":
        return _expectation_rules(stage, ctx, row, output)
    if row.kind == "Evaluation":
        return _evaluation_rules(stage, ctx, row, output)
    if row.kind == "Aggregation":
        return _aggregation_rules(stage, row, output)
    return ()


def _pullback_rules(stage, ctx, row, output):
    """The rule a pullback declares on an output: the composite the output
    is, applied at a point of its domain, equals the input function read at
    the value there of the map it composes with, the law at the policy
    written out (RL14), `(𝑉≻ ∘ 𝑔≻(·, 𝑐))(m_d) = 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))`; on a
    policy block, whose point holds the controls,
    `(𝑑𝑉_f≻ ∘ 𝑔≻)(m_f, m_p, w_d, c, c_p) = 𝑑𝑉_f≻(𝑔≻(m_f, m_p, w_d, c,
    c_p))`, and at a label, `(𝑉_kp≻ ∘ 𝑔_keep≻)(a_d, h_d, z_d) =
    𝑉_kp≻(𝑔_keep≻(a_d, h_d, z_d))` (`card-redesign.md` §2, change 2). The
    point is the output's coordinates, and the right side is the composite
    applied there (`term_operations.apply_at`). An output whose expression
    is no composite declares none."""
    composite = wire_expression(stage, output)
    if not isinstance(composite, S.Compose):
        return ()
    _, points = bound_point(ctx, row.identity, output.coordinates)
    x = tuple_term(points[identity] for identity in output.coordinates)
    return (Rule(Compare(S.Apply(composite, (x,)), "=", apply_at(composite, x))),)


def _expectation_rules(stage, ctx, row, output):
    """The rule an expectation declares on an output: the integral at a
    point of its domain, the output read there equal to the expectation of
    its input over the declared law of the shocks at that point, in the
    file's notation, `(2)(k_d) = E_{Ψ, θ}[𝑉≻(𝑔≻(k_d, 𝜍(k_d), Ψ, θ))]`, where
    `(2)` is the output's own reference. A result an Evaluation names reads
    by that name, as an aggregation's does (`carriers.written_name`). The
    right side is the output's expression, a map, applied at the point
    (`term_operations.apply_at`); no measure is constructed (AMD-SG-034 §4
    item 7). An output that a solve reads as its residuals declares none of
    its own: its residual lines state the integral at the point under the
    residual's name, `r₁ = E_{Ψ, θ}[𝑑𝑉≻(𝑔≻(k_d, ς, Ψ, θ)) · (Ψ − R)]`
    (`wire_residual_rules`; AMD-SG-034 §4 item 9). Nor does an output whose
    input is not mapped."""
    mapping = wire_expression(stage, output)
    if not isinstance(mapping, S.Lambda) or wire_residual_rules(stage, output):
        return ()
    _, points = bound_point(ctx, row.identity, output.coordinates)
    x = tuple_term(points[identity] for identity in output.coordinates)
    named = written_name(stage, output.identity)
    held = reference_term(named if named is not None else output.identity)
    return (Rule(Compare(S.Apply(held, (x,)), "=", apply_at(mapping, x))),)


def _evaluation_rules(stage, ctx, row, output):
    """The rule an Evaluation declares on an output, the identity from the
    derived carrier into the declared one: the `Member` statements of the
    declared carrier with its feasibility, the output in the set of maps and
    each condition of the carrier read at the point, conjoined, the
    conjunction nested on the left: `𝑐 ∈ (Xm → ℝ₊₊) ∧ 𝑐(m_d) ∈ Γ(m_d)` for
    a policy, `(𝑐, 𝑐_p) ∈ (ℝ₊₊ × Xp × ℝ₊₊ → ℝ₊₊ × ℝ₊) ∧ 𝑐(m_f, m_p, w_d) ∈
    Γ_c(m_f) ∧ 𝑐_p(m_f, m_p, w_d) ∈ Γ_p(w_d)` for a joint policy,
    `𝑉 ∈ (Xm → [−∞, ∞))` for a value function, and the policy's statement
    again, `𝑐 ∈ (Xm → ℝ₊₊) ∧ 𝑐(m_d) ∈ Γ(m_d)`, for a builder's closing
    Evaluation that reads the output of a `!node` Evaluation, the form the
    fold makes of `c = c[>] :: [id=cons_choice, !node]` (`card-redesign.md`
    §2, change 2). The carrier is the one `carriers.wire_type` derives, a set
    of policies read without its power set
    (`typed_expressions.policy_set_parts`).
    A policy is named by the function wires of its controls: the unknowns
    of the row that answers the wire the Evaluation reads
    (`grains.answering_row`), where that row answers a set of functions
    (`grains.answers_function_set`). The function wires stand for the
    carrier's bound functions in its conditions; every other output is named
    by itself."""
    source = row.inputs[tuple(row.outputs).index(output.identity)]
    answering = answering_row(stage, source)
    controls = (
        tuple(answering.unknowns)
        if answering is not None and answers_function_set(stage, answering)
        else ()
    )
    variables, base, conditions = S.policy_set_parts(wire_type(stage, output).carrier)
    functions = {control.field: reference_term(ctx.function_wire(control)) for control in controls}
    subject = (
        tuple_term(functions[control.field] for control in controls)
        if controls
        else reference_term(output.identity)
    )
    bound = {
        variable: functions[variable.field]
        for variable in variables
        if getattr(variable, "field", None) in functions
    }
    statement = Member(subject, base)
    for condition in conditions:
        statement = And(statement, S.substitute(condition, bound))
    rules = [Rule(statement)]
    for coordinate, right_side, _address, _source in getattr(row, "derivatives", ()):
        rules.append(_stated_derivative_rule(stage, ctx, row, output, coordinate, right_side))
    return tuple(rules)


def _stated_derivative_rule(stage, ctx, row, output, coordinate, right_side):
    """The rule a derivative line states on the value an Evaluation writes,
    read at the point (AMD-MB-001 §4.3, D4): the derivative of the output in
    the coordinate the line names, at the point of the output's coordinates,
    `D_{m_d}𝑉(m_d)`, equal to the line's right side read in the row's
    spelling, the controls as the policy at the point, `𝑑𝑢(𝑐(m_d))`. The
    package reads the line and differentiates nothing."""
    _, points = bound_point(ctx, row.identity, output.coordinates)
    x = tuple_term(points[identity] for identity in output.coordinates)
    left = T.Operator("D", (T.Var(coordinate.field),), (S.Apply(reference_term(output.identity), (x,)),))
    # the right side is read in the scope of the row that computes the value,
    # which is held at the policy, so that a control reads as the policy at
    # the point, `𝑐(m_d)`, as the aggregation's own rule reads it
    source = row.inputs[tuple(row.outputs).index(output.identity)]
    producer = answering_row(stage, source) or row
    right = term_by_reference(
        ctx,
        right_side,
        producer.identity,
        producer.builder,
        _row_scope(stage, producer, right_side),
        declared=True,
    )
    return Rule(Compare(left, "=", right))


def _forward_rules(stage, row, output, inputs, outputs):
    """The rule a forward row declares on its measure: the mass it gives an
    event, the measure read at the event its own binding names; none where
    the caller holds no wire sorts."""
    if inputs is None or outputs is None:
        return ()
    held = _one_step(stage, row, tuple(inputs), tuple(outputs), output)
    if not isinstance(held, S.Measure):
        return ()
    event, _ = held.binding
    return (
        Rule(
            Compare(
                S.Apply(reference_term(output.identity), (reference_term(event.identity),)),
                "=",
                held.body,
            )
        ),
    )


def _explicit_relation_rules(stage, ctx, row, output):
    """The relation the line of a row with an explicit side writes
    (`grains.explicit_side`), with the sign and in the order the line writes
    them: the output at the point against the explicit side read there, the
    row's own map expanded, `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a))`, held with its clause
    read at the row's own point, the grid point, where the line carries one:
    `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) ⟂ a ≥ 0`. The clause's segment at the zero
    saving is the relation's and no part of the explicit side: the explicit
    side is read as the line writes it (`wire_expression`, `explicit`), and
    the set of the values the clause admits is the output's formula
    (`_admitted_values`). Where the point has several coordinates, the
    output and each wire read at the point print by their bare names and
    the rule's region note names the point and its domain, `𝑐≻ ≤
    𝑢_c_inv(β · 𝑑𝑉_a≻) ⟂ a_nxt_adj ≥ 0 on (a_nxt_adj, h_nxt_adj, z_nxt_adj)
    ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊` (`_read_bare`, `_point_region`; `card-redesign.md` §2,
    change 4)."""
    point, points = bound_point(ctx, row.identity, output.coordinates)
    x = tuple_term(points[identity] for identity in output.coordinates)
    region = _point_region(ctx, row, output.coordinates, points)
    core = stage.definitions[row.statements[0]].equations[0]
    # the sign is the relation's own, a clause's line read through its
    # core
    relation = relation_of(core)
    sign = SIGN[type(relation.op)] if isinstance(relation, T.Inequality) else "="
    held = S.Apply(reference_term(output.identity), (x,))
    explicit = apply_at(wire_expression(stage, output, expand=True, explicit=True), x)
    if region is not None:
        held, explicit = reference_term(output.identity), _read_bare(explicit, x)
    statement = (
        Compare(held, sign, explicit)
        if explicit_side(stage, row) == relation.rhs
        else Compare(explicit, sign, held)
    )
    if not isinstance(core, T.Slack):
        return (Rule(statement, (), region),)
    # the clause read at the row's own point, the grid point
    local = {**points, **{identity.field: value for identity, value in points.items()}}
    return (
        Rule(
            Complementarity(
                statement,
                term_by_reference(
                    ctx, core.bound, row.identity, row.builder, local, declared=True
                ),
            ),
            (),
            region,
        ),
    )


def _aggregation_rules(stage, row, output):
    """The relation the line of an aggregation declares on a named output,
    read at the point; none on an unnamed result. Where the point has
    several coordinates, the output and each wire read at the point print by
    their bare names and the rule's region note names the point and its
    domain, `𝑚≻ = a_nxt_adj + 𝑐≻ + (1 + τ) · h_nxt_adj on (a_nxt_adj,
    h_nxt_adj, z_nxt_adj) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊` (`_read_bare`, `_point_region`;
    `card-redesign.md` §2, change 4)."""
    ctx = StageNames(stage)
    # a named field an aggregation writes satisfies the relation its line
    # declares, read at the point: `𝑚_d≻(a) = a + 𝑐≻(a)` (§2 item 5, the
    # rail under `endoggrid:Aggregation` in the drawing of §4 item 12);
    # so does the field an Evaluation names the aggregation's result as,
    # `𝑉(m_d) = 𝑢(𝑐(m_d)) + 𝑉≻(𝑔≻(m_d, 𝑐(m_d)))`; an unnamed
    # result prints its map in the `out` column instead. The relation is
    # the line's own right side read in the row's spelling, the earlier
    # outputs of a merged row by name and no substitution
    named = written_name(stage, output.identity)
    if named is None:
        return ()
    position = tuple(row.outputs).index(output.identity)
    statements = tuple(row.statements)
    address = (
        statements[position]
        if len(statements) == len(row.outputs)
        else statements[0]
        if statements
        else None
    )
    definition = stage.definitions.get(address) if address is not None else None
    core = definition.equations[0] if definition is not None and definition.equations else None
    core = relation_of(core)
    point, points = bound_point(ctx, row.identity, output.coordinates)
    x = tuple_term(points[identity] for identity in output.coordinates)
    region = _point_region(ctx, row, output.coordinates, points)
    if isinstance(core, T.Equation):
        right = term_by_reference(
            ctx,
            core.rhs,
            row.identity,
            row.builder,
            _row_scope(stage, row, core.rhs),
            declared=True,
        )
    else:
        right = apply_at(wire_expression(stage, output, expand=True), x)
    if region is None:
        return (Rule(Compare(S.Apply(reference_term(named), (x,)), "=", right)),)
    return (Rule(Compare(reference_term(named), "=", _read_bare(right, x)), (), region),)


def _argmax_rules(stage, ctx, row):
    """The rules of an `Argmax` row: the membership its line holds,
    `𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]`, then each
    property the row holds, a line attached to its line by a dotted id
    (`row.properties`), read at the point on the domain of the decision
    states as a relation of candidate statements is, `𝑑𝑢(𝑐(m_d)) =
    𝑑𝑉≻(𝑔≻(m_d, 𝑐(m_d))) ⟂ 𝑔≻(m_d, 𝑐(m_d)) ≥ 0 on Xm`. A property is what the
    author asserts of the maximization; the elaborator neither checks it
    against the objective nor derives anything from it (the sub-brief
    `inv-Euler-functional-operation.md` §2a)."""
    table = stage.definitions
    rules = []
    for address in row.statements:
        if address not in table or not table[address].equations:
            continue
        statement = declared_statement(stage, table[address], unknowns=tuple(row.unknowns))
        if not isinstance(statement, S.Unresolved):
            rules.append(Rule(statement))
    held = [address for address in row.properties if address in table]
    if held:
        states = ctx.coordinates(row.unknowns[0].perch, roles=("state",))
        _, points = bound_point(ctx, row.identity, states)
        domain = coordinate_domain(ctx, states, row.identity, use_choice_sets=False)
        for address in held:
            relation = line_at_point(ctx, table[address], tuple(row.unknowns), points)
            if not isinstance(relation, S.Unresolved):
                # the card labels the property by its line's id,
                # `optimality.euler`
                label = Identity("line", address=address).statement
                rules.append(Rule(relation, (), domain, label=label))
    return tuple(rules)


def _rules_at_the_point(ctx, row):
    """The rules of a relation formed from lines read at the point: the
    members of a system as one `Rule`, their conjunction at the point on the
    domain of the decision states, which every output of the row holds and
    the card prints once (AMD-SG-035 §3), each value at the next perch and
    each bound read through a law of several coordinates read at the names
    of the law's outputs, `𝑑𝑉_f≻(y_f, y_p)` and `⟂ y_f ≥ 0`, whose line the
    row states under `where` (`law_outputs_read`). Where the point is one
    coordinate, each control keeps it, `𝑑𝑢(𝑐(m_d))`, and the rule holds on
    the domain, `on Xm`; where the point is a tuple, each control is read
    by its bare name, `𝑑𝑢(𝑐)`, and the rule's region note names the point
    and its domain, `on (m_f, m_p, w_d) ∈ ℝ₊₊ × Xp × ℝ₊₊`, so that the
    reader knows at which coordinates the bare names are read
    (`card-redesign.md` §2, change 4). A coordinate relation, `c = c[>]`,
    holds the grid relation of `_grid_rules`."""
    states = ctx.coordinates(row.unknowns[0].perch, roles=("state",))
    _, points = bound_point(ctx, row.identity, states)
    relation = system_relation(ctx, row, points, by_name=True)
    if isinstance(relation, S.Unresolved):
        return ()
    region = _point_region(ctx, row, states, points)
    if region is None:
        region = coordinate_domain(ctx, states, row.identity, use_choice_sets=False)
    return (Rule(relation, (), region),)


def _point_region(ctx, row, coordinates, points):
    """The region note of a rule read at a point of several coordinates,
    which names the coordinates at which its bare names are read: the
    membership of the point in its domain, `(a_nxt_adj, h_nxt_adj,
    z_nxt_adj) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊` and `(m, z_d, c, h_choice) ∈ ℝ₊₊ × ℝ₊₊ ×
    ℝ₊₊ × ℝ₊₊`. The domain is the product of the coordinates' declared sets,
    the domain `coordinate_domain` starts from before it restricts a
    control by its feasibility, and the block's observable set by reference
    where a coordinate is a multiplier, `(a, μ) ∈ A≻,policy`, as the grid
    relation holds the image of the grid (`_grid_rules`). None where the
    point is one coordinate, at which every name keeps its argument
    (`card-redesign.md` §2, change 4). `points` maps each coordinate to its
    reference."""
    coordinates = tuple(coordinates)
    if len(coordinates) <= 1:
        return None
    domain = (
        reference_term(observable_set(ctx, row.builder))
        if any(ctx.role(identity) == "multiplier" for identity in coordinates)
        else product(
            declared_set_term(ctx, ctx.declared_set(identity), identity, "argument set")
            for identity in coordinates
        )
    )
    return Member(tuple_term(points[identity] for identity in coordinates), domain)


def _read_bare(term, x):
    """`term` with each function the file names without arguments, applied
    at the point `x`, written by its bare name, which stands for its value
    there: the policy of a control, `𝑐` for `𝑐(m, z_d)`, and a wire read at
    the point, `𝑑𝑉_a≻` for `𝑑𝑉_a≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)`
    (`card-redesign.md` §2, change 4). A declared function, a law of motion,
    a composite and an abbreviation the card introduces keep their
    arguments, and so does a function applied at anything but the point.
    The rule that holds the term names the point in its region note
    (`_point_region`)."""
    if isinstance(term, tuple):
        items = tuple(_read_bare(item, x) for item in term)
        return term if all(a is b for a, b in zip(items, term)) else items
    if isinstance(term, Identity) or not dataclasses.is_dataclass(term) or isinstance(term, type):
        return term
    if isinstance(term, S.Apply) and _file_function(term.function) and tuple_term(term.args) == x:
        return term.function
    parts = {
        field.name: _read_bare(getattr(term, field.name), x) for field in dataclasses.fields(term)
    }
    if all(parts[name] is getattr(term, name) for name in parts):
        return term
    return dataclasses.replace(term, **parts)


def _file_function(term):
    """Whether `term` refers to a function the file names without arguments:
    a function wire at a perch that no law of motion composes, the policy
    of a control, `c`, or a field under a perch mark, `dV_a[>]`, `c[>]`."""
    identity = term.symbol.name if is_wire_symbol(term) else None
    return (
        identity is not None
        and identity.kind == "function"
        and identity.perch is not None
        and identity.mark != "g"
    )


def _solve_rules(stage, ctx, row):
    """The head of a relation on a solve, `(c, h_choice) = solve_{c,
    h_choice}(r₁, r₂)`: the residuals named as the lines of the unnamed
    input name them, or, where the residuals are the row's own terms, named
    by the row and preceded by their lines, a residual read as a membership
    standing in the head as that membership, `solve_{c, h_choice}(c ∈
    𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj), r₂)` (`_own_residual_rules`).
    Where the residuals are the row's own terms at a point of several
    coordinates, the point is named once in a region note, `on (m, z_d, c,
    h_choice) ∈ ℝ₊₊ × ℝ₊₊ × ℝ₊₊ × ℝ₊₊`, under the last residual line, as
    `card-redesign.md` §5 draws it, and under the head where the row has
    no residual line."""
    residual = _residual_input(ctx, row)
    region = None
    if residual is not None:
        variables, lines = _residual_variables(ctx, residual), ()
        arguments = tuple(reference_term(variable.identity) for variable, _ in variables)
    else:
        arguments, lines, region = _own_residual_rules(stage, ctx, row)
        if not arguments:
            return ()
    point, points = bound_point(ctx, row.identity, row.unknowns)
    unknowns = tuple(points[identity] for identity in row.unknowns)
    head = T.Operator(
        "solve", tuple(T.Var(S.variable_identity(unknown)) for unknown in unknowns), arguments
    )
    rules = tuple(lines) + (Rule(Compare(tuple_term(unknowns), "=", head)),)
    if region is None:
        return rules
    place = len(lines) - 1 if lines else len(rules) - 1
    noted = dataclasses.replace(rules[place], on=region)
    return rules[:place] + (noted,) + rules[place + 1 :]


def _own_residual_rules(stage, ctx, row):
    """The arguments of the head of a solve whose residuals are the row's own
    terms, and no input of the row, and the lines that name them, at the
    point of the decision states and the unknowns, the outputs of a law of
    several coordinates read by their names (`_own_residuals`): for each
    residual in the line's order, the variable `rₙ` the row owns, `n` its
    place among the arguments, with the `Rule` that names it, `r₂ =
    (1 + τ) · 𝑢_c(c) − 𝑢_h(h_choice) − β · 𝑑𝑉_h≻(a_nxt_adj, h_nxt_adj,
    z_nxt_adj)`; and for a residual read as a membership, the membership
    itself and no line, `c ∈ 𝑐≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)`; and the
    region note of that point (`_point_region`), `(m, z_d, c, h_choice) ∈
    ℝ₊₊ × ℝ₊₊ × ℝ₊₊ × ℝ₊₊`, where each wire read at the point prints by its
    bare name (`_read_bare`), and None where the point is one coordinate.
    Nothing where the row's maps hold no one residual per argument of its
    `solve`."""
    own = _own_residuals(stage, ctx, row, by_name=True)
    if own is None:
        return (), (), None
    _, points, residuals = own
    region = _point_region(ctx, row, tuple(points), points)
    if region is not None:
        x = tuple_term(points.values())
        residuals = tuple(_read_bare(residual, x) for residual in residuals)
    arguments, lines = [], []
    for n, residual in enumerate(residuals):
        if isinstance(residual, Member):
            arguments.append(residual)
            continue
        variable, _ = bound_variable(
            row.identity,
            "r" + str(n + 1).translate(_SUBSCRIPT_DIGITS),
            T.Named("ℝ"),
            n,
            role="residual",
        )
        arguments.append(reference_term(variable.identity))
        lines.append(Rule(Compare(reference_term(variable.identity), "=", residual)))
    return tuple(arguments), tuple(lines), region


def _grid_rules(stage, ctx, row, output):
    """The grid relation of the identification, a relation on a coordinate
    relation `c = c[>]`, on the image of the grid: `𝑐(𝑚_d≻(a)) = 𝑐≻(a) on
    𝑚_d≻(Xa)`, the wires read as `_identification_wires` reads them. Where
    the candidate carries a correspondence, `𝑐≻(a)` and `𝑚_d≻(a)` are the
    values it admits at `a`, each paired with its own, which the relation of
    the row's output states (`_grid_pairs`)."""
    inputs = tuple(wire_table(stage).sort_of(identity) for identity in row.inputs)
    if len(row.unknowns) != 1 or len(output.coordinates) != 1:
        return ()
    read = _identification_wires(ctx, row, inputs)
    if isinstance(read, S.Unresolved):
        return ()
    value, _, coordinate, _ = read
    point, points = bound_point(ctx, row.identity, value.coordinates)
    a = tuple_term(points[identity] for identity in value.coordinates)
    grid = S.Apply(reference_term(coordinate.identity), (a,))
    statement = Compare(
        S.Apply(reference_term(ctx.function_wire(row.unknowns[0])), (grid,)),
        "=",
        S.Apply(reference_term(value.identity), (a,)),
    )
    # the image of the grid: of the block's observable set by reference where
    # the grid holds a multiplier (AMD-SG-035 §10), of the coordinate domain
    # otherwise; the statement keeps its coordinates free
    held = (
        reference_term(observable_set(ctx, row.builder))
        if any(ctx.role(identity) == "multiplier" for identity in value.coordinates)
        else coordinate_domain(ctx, value.coordinates, row.identity)
    )
    return (Rule(statement, (), S.Apply(reference_term(coordinate.identity), (held,))),)


def residual_rules(stage, sort):
    """The lines an unnamed input of a solve is made from, one `Rule` per
    residual at the point of the wire's coordinates, `r₁ = c − 𝑐≻(…)`, the
    controls read as the coordinates the line writes (AMD-SG-034 §4 item 9,
    §10 item 8); empty on every other wire."""
    ctx = StageNames(stage)
    solves = [
        row
        for row in wire_table(stage).table.primitive_rows
        if is_relation(row)
        and _solve_head(row) is not None
        and getattr(_residual_input(ctx, row), "identity", None) == sort.identity
    ]
    if not solves:
        return ()
    variables = _residual_variables(ctx, sort)
    point, points = bound_point(ctx, sort.identity, sort.coordinates)
    value = apply_at(
        wire_expression(stage, sort, expand=True),
        tuple_term(points[identity] for identity in sort.coordinates),
    )
    return tuple(
        Rule(
            Compare(
                reference_term(variable.identity),
                "=",
                _reduced(component(value, n, len(variables))),
            )
        )
        for n, (variable, _) in enumerate(variables)
    )


def _residual_input(ctx, row):
    """The unnamed input a `solve` reads its residuals from: the wire the
    row's map is, made from the authored lines (AMD-SG-034 §4 item 9); None
    where the row's maps are the residuals themselves, a solve formed in one
    row with its residuals (`_own_residual_rules`)."""
    rendering = wire_table(ctx.stage_object)
    if not row.maps or not all(is_wire_symbol(term) for term in row.maps):
        return None
    named = {term.symbol.name for term in row.maps}
    return next(
        (rendering.sort_of(identity) for identity in row.inputs if identity in named), None
    )


_SUBSCRIPT_DIGITS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _residual_variables(ctx, sort):
    """The residuals an unnamed input of a solve carries, one variable each,
    named `r₁`, `r₂`, … in the order the line writes them, over the set of
    the residual (AMD-SG-034 §4 item 9); their owner is the wire, so that the
    lines of the wire and the head of the solve name one residual alike."""
    target = resolve_set(ctx, wire_type(ctx.stage_object, sort).sort[4], sort.identity)
    factors = target.factors if isinstance(target, T.Product) else (target,)
    return tuple(
        bound_variable(
            sort.identity,
            "r" + str(n + 1).translate(_SUBSCRIPT_DIGITS),
            factor,
            n,
            role="residual",
        )
        for n, factor in enumerate(factors)
    )


def _reduced(term):
    """The term with its written projections taken and its applications of
    a Lambda beta-reduced (`term_operations.reduced`)."""
    return reduced(term, beta=True)


# --- the declared definitions ---


def definition_expression(stage, definition, row=None):
    """One declared function, forward-owned g, backward-owned G segment or
    declared distribution: a distribution as the file declares its law,
    `LogNormal(−σ_ψ²/2, σ_ψ)`, the product of that law over the index set
    where the subject is a collection and the family is a scalar family
    other than `N`, `⊗_{i ∈ I_J} TypeIExtremeValue(0, 1)`, and a kernel over
    the arguments the law reads only where the file conditions it
    (AMD-SG-034 §4 item 7); a law whose lines stand in branches as the tuple
    of its branches' values indexed by its label coordinate. A scalar `N` on
    a collection is the joint normal of its convention and is no product."""
    ctx = StageNames(stage)
    if definition.kind == "distribution":
        coordinates = definition_type(stage, definition).sort[2]
        point, points = bound_point(ctx, definition.identity, coordinates)
        local = {**points, **{i.field: value for i, value in points.items()}}
        declaration = definition.equations[0]
        law = term_by_reference(
            ctx, declaration.law, definition.identity, definition.address, local, declared=True
        )
        index = _index_set(ctx, declaration.subjects)
        if index is not None and product_law(declaration.law) and isinstance(law, S.Apply):
            # the index variable is `i`, or `i′` where the law reads a name `i`
            read = {getattr(free, "field", free) for free in S.free_identities(law)}
            variable = bound_variable(
                definition.identity,
                "i′" if "i" in read else "i",
                declared_set_term(ctx, index, definition.identity, "index set"),
                _PRODUCT_INDEX,
            )
            law = S.ProductMeasure(variable, law)
        return S.Lambda(point, law) if coordinates else law
    spec = (
        law_of_motion_kernel(stage, definition.identity)
        if definition.kind == "g"
        else aggregator_kernel(stage, row)
        if definition.kind == "G" and row is not None
        else None
    )
    if spec is not None:
        declared = tuple(zip(spec.index, spec.names, spec.argument_sets))
        terms, block = spec.terms, spec.builder
    elif definition.kind in ("function", "correspondence") and isinstance(
        definition.equations[0], (T.FuncDef, T.CorrDef)
    ):
        declared = tuple((name, name, domain) for name, domain in definition.coordinates)
        terms, block = (definition.equations[0].body,), definition.address
    else:
        return S.Unresolved(definition.identity, "typed defining function")
    bindings, local = [], {}
    for n, (key, name, domain) in enumerate(declared):
        # a law of motion binds each argument by the coordinate it reads, with
        # its perch and role; a declared function by the author's name
        coordinate = key if isinstance(key, Identity) and key in ctx.ports else None
        variable = bound_variable(
            definition.identity,
            name,
            declared_set_term(ctx, domain, definition.identity, "argument set"),
            n,
            role=(ctx.role(coordinate) or "bound") if coordinate is not None else "bound",
            perch=coordinate.perch if coordinate is not None else None,
        )
        bindings.append(variable)
        local[key] = reference_term(variable.variable.identity)
        local[name] = reference_term(variable.variable.identity)
    resolved = tuple(
        term_by_reference(
            ctx, term, definition.identity, block, local, active=(definition.identity,)
        )
        for term in terms
    )
    # a law whose lines stand in branches is the tuple of its sections' values
    # indexed by its label coordinate, the form of a branch value
    labels = (
        tuple(dict.fromkeys(Identity("line", address=a).branch for a in spec.sources))
        if definition.kind == "g" and spec is not None
        else ()
    )
    if labels and None not in labels:
        key = next(k for k in spec.index if ctx.labels(k))
        body = T.Select(
            T.Tuple(
                tuple(
                    tuple_term(
                        r
                        for r, a in zip(resolved, spec.sources)
                        if Identity("line", address=a).branch == label
                    )
                    for label in labels
                )
            ),
            T.Key(local[key]),
        )
    else:
        body = tuple_term(resolved)
    return S.Lambda(tuple(bindings), body)


# the position of the index variable of the product a law on a collection
# denotes, apart from the positions of the coordinates it is conditioned on
_PRODUCT_INDEX = 230


def _index_set(ctx, subjects):
    """The index set of the one subject of a distribution declaration where
    the subject is a collection, as its declared set of functions writes it,
    `I_J` for `ε : I_J → ℝ`; None for several subjects and for a subject of
    any other set."""
    if len(subjects) != 1:
        return None
    identity = Identity("field", stage=ctx.stage_name, perch=SHCK, field=subjects[0])
    declared = defined(ctx.declared_set(identity), ctx.set_terms)
    if isinstance(declared, T.Space):
        declared = defined(declared.set, ctx.set_terms)
    return declared.domain if isinstance(declared, T.Functions) else None


def definition_measure(stage, definition):
    """The measure a declared law of a scalar family denotes at its written
    parameters: the defining Lambda of the family's rule with the written
    arguments substituted for its bindings, `measure on ℝ given by B ↦ …`,
    the product of that measure over the index set where the law as
    declared is a product, and a kernel over the arguments the law reads
    where the file conditions it. None where the declaration is not one
    real-parameter call of a scalar family on one subject: a mixture, a
    tuple subject or argument, a scalar `N` on a collection and a family
    with no definition."""
    declaration = definition.equations[0]
    family = getattr(declaration.law, "fun", None)
    if definition.kind != "distribution" or family not in SCALAR_FAMILIES:
        return None
    if len(declaration.subjects) != 1:
        return None
    if family == NORMAL and _index_set(StageNames(stage), declaration.subjects) is not None:
        return None
    declared = definition_expression(stage, definition)
    kernel = declared if isinstance(declared, S.Lambda) else None
    law = kernel.body if kernel is not None else declared
    indexed = law if isinstance(law, S.ProductMeasure) else None
    law = indexed.body if indexed is not None else law
    primitive = primitive_definition(family)
    rule = primitive.equations[0]
    if (
        not isinstance(law, S.Apply)
        or S.variable_identity(law.function) != primitive.identity
        or len(law.args) != len(rule.bindings)
        or any(isinstance(argument, T.Tuple) for argument in law.args)
    ):
        return None
    # a variable the rule's body binds whose name a written argument or the
    # kernel's point reads is primed, `z′`, so that the printed measure tells
    # the two apart: `z + 1^(1/2) · z′ ∈ B` for `y ~ N(z, 1)`
    taken = {
        getattr(free, "field", free)
        for argument in law.args
        for free in S.free_identities(argument)
    }
    if kernel is not None:
        taken |= {variable.identity.field for variable, _ in kernel.bindings}
    body = rule.body
    for bound in S.bound_domains(rule.body):
        if isinstance(bound, Identity) and bound.field in taken:
            body = S.renamed_bound(
                body, bound, dataclasses.replace(bound, field=bound.field + "′")
            )
    measure = S.substitute(
        body,
        {variable.identity: argument for (variable, _), argument in zip(rule.bindings, law.args)},
    )
    if indexed is not None:
        measure = S.ProductMeasure(indexed.binding, measure)
    return S.Lambda(kernel.bindings, measure) if kernel is not None else measure


# --- a line read at the point ---


def declared_statement(stage, definition, unknowns=None):
    """A line marked `!doc` as the condition on the constructed output of its
    builder (AMD-SG-034 §3 `declared`), by the named
    operations: the line's equation is read by identity; each control on its
    left is replaced by the policy at the state coordinates, `𝑐(m_d)`, the
    coordinates free; each continuation field its right side reads is
    replaced by the function at that perch pulled back along the law of
    motion that reads the controls, by reference, `𝑉≻(𝑔≻(m_d, cp))`, the
    controls read as the binders the author wrote; a binder written without
    a set ranges over the control's declared set; an operator the rules do
    not define, `argmax`, `E`, stands as written; and an equation whose right
    side is an `argmax` is read as a membership,
    `𝑐(m_d) ∈ argmax_{cp ∈ Γ(m_d)} [𝑢(cp) + 𝑉≻(𝑔≻(m_d, cp))]`.

    A line a relation is formed from, and a property of an operative
    `argmax` line, is read at the point by `line_at_point`, its unknowns
    given (AMD-SG-035 §3)."""
    ctx = StageNames(stage)
    core = definition.equations[0]
    equation = relation_of(core)
    if not isinstance(equation, T.Equation):
        return S.Unresolved(definition.identity, "declared statement of an equation")
    controls = (
        tuple(unknowns) if unknowns else tuple(ctx.defined(equation, definition.identity.block))
    )
    if not controls or any(identity not in ctx.ports for identity in controls):
        return S.Unresolved(definition.identity, "declared statement of a defined field")
    states = ctx.coordinates(controls[0].perch, roles=("state",))
    _, points = bound_point(ctx, definition.identity, states)
    return line_at_point(ctx, definition, unknowns, points)


def line_at_point(ctx, definition, unknowns, points, *, owner=None, by_name=False):
    """A line read at the point (AMD-SG-035 §3): each control as the policy
    at the state coordinates `points`, `𝑐(m_d)`, or as the binder of a
    maximization; each value read at the next perch as the function there
    applied to the law at the point, by reference, `𝑑𝑉≻(𝑔≻(m_d, 𝑐(m_d)))`;
    where the unknowns are given and the line is no maximization, each
    continuation coordinate the law writes as the law at the point where the
    law writes one, `𝑔≻(m_d, 𝑐(m_d))`, and as its component where it writes
    several, and otherwise under its name; parameters and numbers as
    written. With `by_name`, where the law writes several coordinates, each
    coordinate it writes is read under its name and each value at the next
    perch as the function there at those names, `𝑑𝑉_f≻(y_f, y_p)` and
    `⟂ y_f ≥ 0`, the names being the variables `owner` binds the law's
    outputs by (`law_outputs_read` states their line once under `where`);
    no projection of the law's value is written (AMD-SG-034 §4 item 6).
    With `by_name`, where the point is a tuple, each control is read by its
    bare name, which stands for its value at the point, `𝑑𝑢(𝑐)` and
    `⟂ 0 ≤ 𝑐_p ≤ w_d` (`_policy_at_point`).
    A clause is held with its statement as one `Complementarity`, its bound
    read at the same point; an `argmax` line is a membership. `points` maps
    each state coordinate to its reference, in the order of the coordinates;
    `owner` is the line's own identity where none is given."""
    stage = ctx.stage_object
    block = definition.identity.block
    core = definition.equations[0]
    clause = core.bound if isinstance(core, T.Slack) else None
    equation = relation_of(core)
    if not isinstance(equation, T.Equation):
        return S.Unresolved(definition.identity, "declared statement of an equation")
    targets = tuple(ctx.defined(equation, block))
    controls = tuple(unknowns) if unknowns else targets
    if not controls or any(identity not in ctx.ports for identity in controls):
        return S.Unresolved(definition.identity, "declared statement of a defined field")
    # the left side is the controls at the point where the line writes their
    # bare names, `c = argmax…`, `(c, c_p) = …`; a relation's left side,
    # `𝑑𝑢(c)`, is read as written, the controls as the policy
    names = equation.lhs.items if isinstance(equation.lhs, T.Tuple) else (equation.lhs,)
    bare = (
        targets and all(isinstance(name, T.Sym) for name in names) and len(names) == len(targets)
    )
    x = tuple_term(points.values())
    local = {**points, **{identity.field: value for identity, value in points.items()}}
    right = equation.rhs
    maximisation = isinstance(right, T.Operator) and right.head == "argmax"
    binders = {}
    if maximisation:
        subs = []
        for control, sub in zip(controls, right.subs):
            name = sub.name if isinstance(sub, T.Var) else sub.var
            binders[control] = T.Sym(T.Constant(name))
            subs.append(
                T.In(name, declared_set_of(ctx, control)) if isinstance(sub, T.Var) else sub
            )
        # the operator read over its maximand, one tuple indexed by the binder
        # where it maximizes over several arguments
        right = dataclasses.replace(right, subs=tuple(subs), args=(maximand(right),))
    else:
        binders = {
            control: _policy_at_point(ctx, control, points, bare=by_name) for control in controls
        }
    shocks = _bound_shocks(ctx, right, block, definition.identity)
    law = _law_reading(ctx, controls)
    if law is not None:
        spec = law_of_motion_kernel(stage, law)
        arguments = {**points, **binders, **shocks}
        if all(identity in arguments for identity in spec.index):
            image = S.Apply(
                reference_term(law), (tuple_term(arguments[identity] for identity in spec.index),)
            )
            forward = _law_forward(ctx, law)
            outputs = tuple(forward.outputs) if forward is not None else ()
            written = (
                coordinate_bindings(ctx, outputs, owner or definition.identity, LAW_OUTPUTS)
                if outputs
                else ()
            )
            # the coordinates a law of several outputs writes, read under
            # their names where the line is read by name
            named = {
                identity: reference_term(variable.identity)
                for identity, (variable, _) in zip(outputs, written)
                if by_name and unknowns and not maximisation and len(outputs) > 1
            }
            # a continuation field is read through the section its pullback in
            # the line's block composes with, where it has one
            sections = {
                wire: op.section
                for op in wire_table(stage).table.primitive_rows
                if op.builder == block and op.kind == "Pullback" and op.section
                for wire in op.inputs
            }
            for identity in ctx.mentioned((right, clause), block):
                if (
                    identity in ctx.ports
                    and identity.perch == CONTINUATION
                    and identity not in arguments
                ):
                    label = sections.get(ctx.function_wire(identity))
                    function = wire_table(stage).sort_of(ctx.function_wire(identity))
                    read = (
                        S.Apply(reference_term(section_identity(ctx, block, label)), (x,))
                        if label is not None
                        else tuple_term(named[i] for i in function.coordinates)
                        if named and all(i in named for i in function.coordinates)
                        else image
                    )
                    local[identity] = S.Apply(reference_term(ctx.function_wire(identity)), (read,))
            for n, (identity, (variable, _)) in enumerate(zip(outputs, written)):
                # a line a relation is formed from reads a continuation
                # coordinate as the law at the point, or its component, and
                # under its name where it is read by name; the `!doc` line
                # keeps it under its name
                local[identity] = (
                    named[identity]
                    if identity in named
                    else component(image, n, len(outputs))
                    if unknowns and not maximisation
                    else reference_term(variable.identity)
                )
    local.update(binders)
    resolved = term_by_reference(ctx, right, definition.identity, block, local, declared=True)
    if bare:
        left = tuple_term(
            _policy_at_point(ctx, identity, points, bare=by_name and not maximisation)
            for identity in targets
        )
    else:
        left = term_by_reference(
            ctx, equation.lhs, definition.identity, block, local, declared=True
        )
    statement = Member(left, resolved) if maximisation else Compare(left, "=", resolved)
    if clause is None:
        return statement
    # the bound read at the same point, each of its sides
    # by `term_by_reference`
    return Complementarity(
        statement, term_by_reference(ctx, clause, definition.identity, block, local, declared=True)
    )


def _policy_at_point(ctx, control, points, *, bare=False):
    """The policy of `control` read at the point `points`: its function
    applied there, `𝑐(m_d)`, and with `bare`, where the point is a tuple,
    its name alone, which stands for its value at the point, `𝑐` for
    `𝑐(m_f, m_p, w_d)`; a rule that reads it so names the point in its
    region note (`_rules_at_the_point`; `card-redesign.md` §2, change 4)."""
    function = reference_term(ctx.function_wire(control))
    if bare and len(points) > 1:
        return function
    return S.Apply(function, (tuple_term(points.values()),))


def _bound_shocks(ctx, term, block, owner):
    """The shocks a term binds under `E`, each as the variable an operator
    of `owner` binds it by (base 200, as an Expectation binds its shocks), by
    the shock's identity: the reading of `E_{Ψ}[…]` binds Ψ by that
    variable wherever the term reads it."""
    found = {}
    for node in _walk(term):
        if isinstance(node, T.Operator) and node.head == "E":
            for sub in node.subs:
                name = sub.name if isinstance(sub, T.Var) else sub.var
                identity = ctx.resolve(name, block) if isinstance(name, str) else name
                if (
                    isinstance(identity, Identity)
                    and identity in ctx.ports
                    and identity not in found
                ):
                    ((variable, _),) = coordinate_bindings(ctx, (identity,), owner, 200)
                    found[identity] = reference_term(variable.identity)
    return found


def _law_reading(ctx, controls):
    """The law of motion that reads the controls, the one `g` definition whose
    arguments include them all; None where none or several do."""
    found = [
        definition.identity
        for definition in ctx.stage_object.definitions.values()
        if definition.kind == "g"
        and set(controls) <= set(law_of_motion_kernel(ctx.stage_object, definition.identity).index)
    ]
    return found[0] if len(found) == 1 else None


def spelled_condition(stage, row, predicate):
    """A condition the fold records on a line, read in the spelling of the
    row whose expression holds it: `𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ)) > 0`
    for the fold's `V[>] > 0`."""
    ctx = StageNames(stage)
    return term_by_reference(
        ctx, predicate, row.identity, row.builder, _row_scope(stage, row, predicate), declared=True
    )


def _row_scope(stage, row, term, coordinates=None):
    """The scope a row's line is read in, so that a source term of the line
    is spelled as the record spells it: the row's
    coordinates as the variables of its point, a control the row is not
    bound at as the policy at the point, `𝑐(m_d)`; a shock the term binds
    under `E` by its name; a continuation field the block pulls back as the
    pulled-back function at the point, `𝑉≻(𝑔≻(m_d, 𝑐(m_d), Ψ))`; a named
    function the row reads as that function at its coordinates,
    `𝐶𝐸(m_d, ν)`; an earlier output of a merged row by its name at the
    point, `𝑐≻(a)`. The point is that of the row's first output unless
    `coordinates` names another, the decision states and the unknowns of a
    solve's residuals."""
    ctx = StageNames(stage)
    rendering = wire_table(stage)
    if coordinates is None:
        coordinates = tuple(rendering.sort_of(row.outputs[0]).coordinates) if row.outputs else ()
    point, points = bound_point(ctx, row.identity, tuple(coordinates))
    local = {**points, **{identity.field: value for identity, value in points.items()}}
    local.update(_bound_shocks(ctx, term, row.builder, row.identity))
    for identity, value in points_at_policy(ctx, row, points).items():
        local.setdefault(identity, value)

    def at(sort, function):
        # a wire of no coordinates, a field of a forward block, is a value
        # and is referred to, not applied
        if not sort.coordinates:
            return function
        if any(identity not in local for identity in sort.coordinates):
            return None
        return apply_at(function, tuple_term(local[identity] for identity in sort.coordinates))

    def port_of(identity):
        return Identity("field", stage=ctx.stage_name, perch=identity.perch, field=identity.field)

    for other in rendering.table.primitive_rows:
        # the identification, a Pullback whose output is its own unknown,
        # composes with no law of motion and is read as no composite
        if other.builder == row.builder and other.kind == "Pullback" and not is_relation(other):
            for identity in other.outputs:
                sort = rendering.sort_of(identity)
                value = at(sort, wire_expression(stage, sort, expand=True))
                if value is None:
                    continue
                # a Pullback's output is read as the composite at the point,
                # `𝑉≻(𝑔≻(m_d, c, Ψ))`, by the field it pulls back and by its
                # wire
                local[identity] = value
                if identity.perch is not None:
                    local[port_of(identity)] = value
    # a named function the block reads or writes is that function at its
    # coordinates, under the perch-marked name the line writes it by,
    # `𝑑𝑉≻(a)`, and under its bare name, `𝐶𝐸(m_d, ν)`: the row's own wires
    # first, so that a merged row's later line reads an earlier output by
    # name, `𝑐≻(a)`, then the wires of the block's other rows, which a line
    # computed in slices reads through its slices
    wires = list(row.inputs) + list(row.outputs)
    wires += [
        identity
        for other in rendering.table.primitive_rows
        if other.builder == row.builder
        for identity in tuple(other.inputs) + tuple(other.outputs)
        if identity not in wires
    ]
    for identity in wires:
        # an input read by its wire, an unnamed result included, is that wire
        # at the point: the wire symbol of a slice resolves here; the
        # component of a merged G that passes a wire unchanged is that wire,
        # and a Pullback's output the composite mapped above, under its bare
        # name too, so that an arrival block's line reads its input as the
        # composite, `𝑉≺(b) = E_{y}[𝑉(𝑔≺(b, y))]`
        target = identity
        while identity_input_of(stage, target) is not None:
            target = identity_input_of(stage, target)
        value = (
            local[target]
            if target in local
            else at(rendering.sort_of(target), reference_term(target))
        )
        if value is None:
            continue
        local.setdefault(identity, value)
        if written_name(stage, identity) is not identity or not identity.field:
            continue
        if identity.perch is not None:
            local.setdefault(port_of(identity), value)
        local.setdefault(identity.field, value)
    return local


def identity_input_of(stage, identity):
    """The wire an Aggregation's output passes unchanged (`_passed`),
    or None."""
    _, producers = _producer_index(stage)
    held = producers.get(identity)
    return _passed(held[0], identity) if held is not None else None


def matching_term(row, node):
    """The sub-term of a row's own terms that is `node` of its line, a wire
    standing for the sub-term it replaced, `w^((1 − ρ)/(1 − η))` for the
    line's `E_{ν}[…]^((1 − ρ)/(1 − η))`; None where the row holds none. A
    condition on the node is formed over this term, so that it reads the
    row's inputs by reference."""
    terms = tuple(row.maps) or tuple(row.equations)
    return next(
        (
            held
            for term in terms
            for held in _walk(term)
            if type(held) is type(node) and _same_term(node, held)
        ),
        None,
    )


def _same_term(source, held):
    if is_wire_symbol(held):
        return True
    if source == held:
        return True
    if type(source) is not type(held):
        return False
    if isinstance(source, tuple):
        return len(source) == len(held) and all(_same_term(a, b) for a, b in zip(source, held))
    if dataclasses.is_dataclass(source) and not isinstance(source, type):
        return all(
            _same_term(getattr(source, field.name), getattr(held, field.name))
            for field in dataclasses.fields(source)
        )
    return False


# --- the local abbreviations and their names ---
#
# The law of motion at the policy has no abbreviation: it is written out
# where a term reads it, `𝑔≻(m_d, 𝑐(m_d))` (RL14).


def section_identity(ctx, block, label):
    """The identity of the law of motion read at one label, `𝑔_keep≻`, a local
    abbreviation of the builder `block` that reads it: the letter,
    the label after an underscore, the perch mark; no policy, since the label
    fixes the branch."""
    return Identity(
        "alias",
        stage=ctx.stage_name,
        address=block,
        field=local_abbreviation(italic("g"), _perch_mark(ctx, block), (), label),
    )


def observable_set(ctx, block):
    """The identity of a policy block's observable set, `A≻,policy`
    (AMD-SG-035 §10): the letter `A`, the perch mark, the block; a
    local abbreviation of that block, as a law's section at a label,
    `𝑔_keep≻`, is of the block that reads it."""
    return Identity(
        "alias",
        stage=ctx.stage_name,
        address=block,
        field=local_abbreviation("A", _perch_mark(ctx, block), (block,)),
    )


def observable_set_rule(ctx, block, coordinates):
    """The defining line of the observable set on the grid `coordinates`,
    stated once under `where`: the set equals the coordinate domain of
    the grid, the product of the declared sets restricted by each
    multiplier's bound and product, `a ≥ 0` and `μ · a = 0`."""
    return Rule(
        Compare(
            reference_term(observable_set(ctx, block)),
            "=",
            coordinate_domain(ctx, coordinates, observable_set(ctx, block), use_choice_sets=False),
        )
    )


def local_abbreviation(letter, mark="", qualifiers=(), label=None):
    """The spelling of a local abbreviation (AMD-SG-034 §4 item 11): the
    letter, a label after an underscore, the perch mark directly after, and
    the names that qualify it after a comma: `𝑔_keep≻`, `𝐺_value≻`, and a
    policy block's observable set, `A≻,policy`."""
    return (
        letter
        + (f"_{label}" if label else "")
        + mark
        + ("," + ",".join(qualifiers) if qualifiers else "")
    )


def _perch_mark(ctx, block):
    """The mark of the perch a block reads or writes beside the decision
    perch, `≺` for the arrival perch and `≻` for the continuation perch."""
    box = wire_table(ctx.stage_object).box_of.get(block)
    if box is None:
        return ""
    perches = perches_of(box, ctx.ports)
    return next((PERCH_MARK[perch] for perch in perches if PERCH_MARK.get(perch)), "")


# --- the operations that read the stage ---


def declared_set_of(ctx, identity):
    """The set a coordinate is declared in, as the file writes it."""
    return declared_set_term(ctx, ctx.declared_set(identity), identity, "argument set")


def term_by_reference(ctx, term, owner, block, local, *, active=(), declared=False):
    """A term with its references resolved, its source arithmetic and its
    local scope kept.

    With `declared`, the term is a law as the file declares it: a `Mixture`
    stays the application of its rule to the written pairs, a numeric atom
    left as the number the rule interprets, and no measure is constructed
    (AMD-SG-034 §4 item 7)."""
    if isinstance(term, T.Sym):
        return _resolved_symbol(ctx, term, block, local)
    if isinstance(term, T.Call):
        return _resolved_call(ctx, term, owner, block, local, active=active, declared=declared)
    if isinstance(term, T.Operator):
        return _resolved_operator(ctx, term, owner, block, local, active=active, declared=declared)
    if isinstance(term, T.Comprehension):
        base = term_by_reference(
            ctx, term.base, owner, block, local, active=active, declared=declared
        )
        scope = dict(local)
        for coordinate in S.subject_coordinates(term.bound):
            identity = S.variable_identity(coordinate)
            scope[identity] = reference_term(identity)
        return dataclasses.replace(
            term,
            base=base,
            conds=tuple(
                term_by_reference(
                    ctx, condition, owner, block, scope, active=active, declared=declared
                )
                for condition in term.conds
            ),
        )
    if isinstance(term, tuple):
        return tuple(
            term_by_reference(ctx, item, owner, block, local, active=active, declared=declared)
            for item in term
        )
    if isinstance(term, T.Key) and isinstance(term.at, str):
        return _resolved_key(ctx, term, block, local)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return dataclasses.replace(
            term,
            **{
                field.name: term_by_reference(
                    ctx,
                    getattr(term, field.name),
                    owner,
                    block,
                    local,
                    active=active,
                    declared=declared,
                )
                for field in dataclasses.fields(term)
            },
        )
    return term


def _resolved_symbol(ctx, term, block, local):
    """A name resolved: an input function by the scope, a name the scope
    binds, an identity by reference, infinity as written, and a name of the
    stage by the identity it resolves to in `block`."""
    symbol = term.symbol
    if is_wire_symbol(term):
        return local.get(symbol.name, S.Unresolved(symbol.name, "input function reference"))
    qualified = isinstance(symbol, T.Variable) and isinstance(symbol.when, T.At)
    if not qualified and symbol.name in local:
        return local[symbol.name]
    if isinstance(symbol.name, Identity):
        return reference_term(symbol.name)
    if isinstance(symbol, T.Constant) and symbol.name in ("inf", "∞"):
        return term
    side = (
        symbol.when.side
        if isinstance(symbol, T.Variable) and isinstance(symbol.when, T.At)
        else None
    )
    identity = ctx.resolve(symbol.name, block, side)
    if identity in local:
        return local[identity]
    if not qualified and symbol.name in ctx.functions:
        return reference_term(ctx.functions[symbol.name].identity)
    if identity in ctx.sets:
        return reference_term(identity)
    return S.Unresolved(identity, "free mathematical reference")


def _resolved_call(ctx, term, owner, block, local, *, active, declared):
    """A call resolved: of a function the stage defines as its application,
    of a rule the definitions hold as the rule's application, of `max`,
    `min` and a mixture as the finite form the rule reads, and of a law the
    rules do not define, where the term is declared, as the file writes it."""
    arguments = tuple(
        term_by_reference(ctx, a, owner, block, local, active=active, declared=declared)
        for a in term.args
    )
    definition = ctx.functions.get(term.fun)
    if definition is not None:
        if definition.identity in active:
            return S.Unresolved(definition.identity, "acyclic function definition")
        return S.Apply(reference_term(definition.identity), arguments)
    rule = primitive_definition(term.fun)
    if rule is None and declared and term.fun in FAMILY_ARGUMENTS:
        # a declared law of a family the rules do not define stands as the
        # file writes it, under the convention of its family
        return T.Call(term.fun, arguments)
    if rule is None:
        return S.Unresolved(Identity("external", field=term.fun), "mathematical definition")
    if term.fun in ("exp", "log") and len(arguments) != 1:
        return S.Unresolved(owner, "one argument for " + term.fun)
    if term.fun in ("max", "min"):
        return _finite_extremum(owner, term.fun, arguments)
    if term.fun == MIXTURE and not declared:
        return _finite_mixture(owner, arguments)
    if (
        term.fun in SCALAR_FAMILIES
        and not declared
        and (
            len(arguments) != len(rule.equations[0].bindings)
            or any(isinstance(arg, T.Tuple) for arg in arguments)
        )
    ):
        # a law as the file declares it keeps its written parameters, a
        # vector and a matrix included (§4 item 7); the measure a
        # multivariate law constructs is what is not resolved here
        return S.Unresolved(owner, "scalar " + term.fun + " parameters")
    if term.fun == "Inv":
        return S.Unresolved(owner, "inverse function domain and image")
    return S.Apply(reference_term(rule.identity), arguments)


def _resolved_operator(ctx, term, owner, block, local, *, active, declared):
    """An operator resolved: a case operation by its weighted case, an
    operator the rules do not define as the file writes it where the term is
    declared, a derivative of one argument by the rule `D`, and any other by
    the rule's identity."""
    case = None if declared else label_case(ctx, term, block)
    if case is not None:
        # the weighted case operation; the card's rule, read declared, keeps
        # the file's line
        return term_by_reference(ctx, case, owner, block, local, active=active, declared=declared)
    rule = primitive_definition(term.head)
    if rule is None and declared:
        return _resolved_declared_operator(
            ctx, term, owner, block, local, active=active, declared=declared
        )
    if rule is None:
        return S.Unresolved(owner, "mathematical definition of " + str(term.head))
    if term.head == "D" and len(term.subs) == 1 and len(term.args) == 1:
        return _resolved_derivative(ctx, term, owner, block, local, active=active)
    return T.Operator(
        rule.identity,
        term.subs,
        tuple(
            term_by_reference(ctx, a, owner, block, local, active=active, declared=declared)
            for a in term.args
        ),
    )


def _resolved_declared_operator(ctx, term, owner, block, local, *, active, declared):
    """An operator the rules do not define, `argmax`, `E`, as the file writes
    it: its binders under the author's names, each set read in the scope of
    the binders before it, its arguments read in the scope of them all
    (AMD-SG-034 §3 `declared`)."""
    scope, subs = dict(local), []
    for sub in term.subs:
        name = sub.name if isinstance(sub, T.Var) else sub.var
        # a binder the scope holds a variable for, a shock bound
        # under `E` by its own variable, is bound by that variable,
        # so that the term encodes the same in every bundle; any other
        # binder stands under its name
        variable = (
            _bound_variable(local.get(ctx.resolve(name, block))) if isinstance(name, str) else None
        )
        bound = variable if variable is not None else name
        if isinstance(sub, T.In):
            subs.append(
                T.In(
                    bound,
                    term_by_reference(
                        ctx, sub.set, owner, block, scope, active=active, declared=declared
                    ),
                )
            )
        else:
            subs.append(T.Var(bound))
        scope[name] = reference_term(variable) if variable is not None else T.Sym(T.Constant(name))
    return T.Operator(
        term.head,
        tuple(subs),
        tuple(
            term_by_reference(ctx, a, owner, block, scope, active=active, declared=declared)
            for a in term.args
        ),
    )


def _resolved_derivative(ctx, term, owner, block, local, *, active):
    """A derivative of one argument by the rule `D`: of a function the stage
    defines, the derivative at a bound variable of its declared domain; of
    an expression, the derivative of its lambda at the argument."""
    sub = term.subs[0]
    name = sub.name if isinstance(sub, T.Var) else sub.var
    identity = ctx.resolve(name, block)
    domain = resolve_set(ctx, ctx.declared_set(identity), identity, "derivative argument")
    argument = term.args[0]
    if is_wire_symbol(argument):
        # a derivative of a value the row reads is the operator D applied to
        # the value as the row reads it, at the law's image or at its own
        # coordinate (AMD-MB-001 §4.2; MB-A19); no limit is expanded
        return T.Operator(
            "D", (T.Var(name),), (term_by_reference(ctx, argument, owner, block, local, active=active),)
        )
    defined = ctx.functions.get(argument.symbol.name) if isinstance(argument, T.Sym) else None
    if defined is not None:
        domain = definition_type(ctx.stage_object, defined).sort[3]
        # a derived parameter is a constant: the one coordinate its record
        # may hold is the set its definition declares and no argument
        if defined.kind == "derived_parameter" or len(defined.coordinates) != 1:
            return S.Unresolved(owner, "differentiated function coordinate")
    variable = bound_variable(owner, name, domain, 200)
    unit = bound_variable(owner, "unit", T.Product(()), 201)
    body = (
        S.Apply(reference_term(defined.identity), (reference_term(variable.variable.identity),))
        if defined is not None
        else term_by_reference(
            ctx,
            argument,
            owner,
            block,
            {**local, name: reference_term(variable.variable.identity)},
            active=active,
        )
    )
    derivative = S.Apply(
        instantiated_definition("D", {"C": domain, "Y": unit.domain}),
        (S.Lambda((variable, unit), body),),
    )
    if defined is not None:
        return S.Lambda(
            (variable,),
            S.Apply(derivative, (reference_term(variable.variable.identity), T.Tuple(()))),
        )
    return S.Apply(derivative, (local.get(name, reference_term(identity)), T.Tuple(())))


def _resolved_key(ctx, term, block, local):
    """A key read at the point: the value its name has in scope, the policy
    at the point for a control the row is held at, `[𝑑(a_d, h_d, z_d)]`
    (§3 item 5); a key nothing in scope binds, and one whose value
    there is a name or a bound variable, the binder of an `argmax` or the
    argument of a declared law, stays the name the author wrote
    (AMD-SG-034 §4 item 2)."""
    value = local.get(ctx.resolve(term.at, block), local.get(term.at))
    return term if value is None or isinstance(value, T.Sym) else T.Key(value)


def _finite_extremum(owner, name, arguments):
    if not arguments:
        return S.Unresolved(owner, "nonempty finite extremum")
    inputs = bound_variable(owner, "a", product(T.Named("ℝ") for _ in arguments), 210)
    values = tuple(
        component(reference_term(inputs.variable.identity), n, len(arguments))
        for n in range(len(arguments))
    )
    if name == "min":
        values = tuple(T.Neg(value) for value in values)
    variable = bound_variable(owner, "r", T.FiniteSet(values), 211)
    result = S.Sup(variable, reference_term(variable.variable.identity))
    if name == "min":
        result = T.Neg(result)
    return S.Apply(S.Lambda((inputs,), result), (tuple_term(arguments),))


def _finite_mixture(owner, arguments):
    """The finite sum in the Mixture rule, with declared atoms as
    Dirac laws."""
    if not arguments or any(
        not isinstance(arg, T.Tuple) or len(arg.items) != 2 for arg in arguments
    ):
        return S.Unresolved(owner, "finite mixture weight-law pairs")
    domain = T.Named("ℝ")
    unit = T.Interval(
        T.Range(left=T.Closed(), lower=T.Number(0), upper=T.Number(1), right=T.Closed())
    )
    pairs = bound_variable(
        owner,
        "p",
        product(product((unit, S.ProbabilityMeasureSet(domain))) for _ in arguments),
        220,
    )
    ref = reference_term(pairs.variable.identity)
    event = bound_variable(owner, "B", measurable_sets(domain, owner), 221)
    total, result, supplied = T.Number(0), T.Number(0), []
    for n, argument in enumerate(arguments):
        pair = component(ref, n, len(arguments))
        weight, law = component(pair, 0, 2), component(pair, 1, 2)
        total = T.Add(total, weight)
        result = T.Add(
            result, T.Mul(weight, S.Apply(law, (reference_term(event.variable.identity),)))
        )
        actual_weight, actual_law = argument.items
        if isinstance(actual_law, (T.Number, T.Neg)):
            actual_law = point_mass(actual_law, domain)
        elif (
            isinstance(actual_law, S.Apply)
            and isinstance(actual_law.function, T.Sym)
            and getattr(actual_law.function.symbol.name, "field", None)
            in (LOGNORMAL, TRUNCATED_LOGNORMAL)
        ):
            # a lognormal component, truncated or not, is a measure on (0, ∞),
            # pushed forward into ℝ by the inclusion (AMD-SG-036 §3)
            positive = bound_variable(owner, "positive", T.Named("ℝ₊₊"), 222)
            inclusion = S.Lambda((positive,), reference_term(positive.variable.identity))
            actual_law = _instantiate(
                "Pushforward",
                {
                    "D": positive.domain,
                    "Y": domain,
                    "g": inclusion,
                },
                actual_law,
            )[0]
        supplied.append(T.Tuple((actual_weight, actual_law)))
    admissible = T.Comprehension(pairs.variable, pairs.domain, (Compare(total, "=", T.Number(1)),))
    return S.Apply(
        S.Lambda(((pairs.variable, admissible),), S.Measure(domain, event, result)),
        (tuple_term(supplied),),
    )


def _bound_variable(value):
    """The identity of the variable a reference names, where `value` is a
    reference to a variable a binding made; None otherwise."""
    if isinstance(value, T.Sym) and isinstance(value.symbol, T.Constant):
        identity = value.symbol.name
        if isinstance(identity, Identity) and identity.kind == "function-parameter":
            return identity
    return None


def _instantiate(name, replacements, argument, binders=None):
    """The rule `name` at the sets and functions `replacements`, applied to
    `argument`: its body and the membership of the argument in its domain.

    `binders` maps a set as the rule declares it, `T.Named("D")`,
    `T.Product((T.Named("X"), T.Named("C")))` or `S.MeasurableMapSet(...)`,
    to the caller's bindings; every variable the rule binds over that set is
    replaced by them (`S.rebind`), so that the record reads at the stage's
    coordinates and not at the rule's letters (AMD-SG-034 §4 item 2)."""
    rule = instantiated_definition(name, replacements)
    variable, domain = rule.bindings[0]
    body = S.substitute(rule.body, {variable.identity: argument})
    condition = Member(argument, domain)
    if binders:
        declared = S.bound_domains(_rule_equation(name))
        mapping = {
            identity: bindings
            for identity, held in declared.items()
            for key, bindings in binders.items()
            if held is not None and held == key
        }
        if mapping:
            body, condition = S.rebind(body, mapping), S.rebind(condition, mapping)
    return body, condition


def _rule_equation(name):
    return PRIMITIVE_DEFINITIONS["definitions"][name].equations[1 if name == "Expectation" else 0]


def _quantified(head, bindings, body):
    """`∀ m_d ∈ Xm, c ∈ ℝ₊₊: body`, one subscript per binding."""
    return T.Operator(head, tuple(T.In(*held) for held in bindings), (body,))


def _forall(variable, condition):
    return T.Operator("forall", (T.In(*variable),), (condition,))


def _at(sort, reference, points):
    if any(identity not in points for identity in sort.coordinates):
        return S.Unresolved(sort.identity, "coordinate adaptation")
    return S.Apply(reference, (tuple_term(points[identity] for identity in sort.coordinates),))


def _walk(term):
    yield term
    if isinstance(term, tuple):
        for child in term:
            yield from _walk(child)
    elif dataclasses.is_dataclass(term) and not isinstance(term, type):
        for field in dataclasses.fields(term):
            yield from _walk(getattr(term, field.name))


# --- the point and its bound variables ---


def bound_point(ctx, owner, coordinates, position=100):
    """The coordinates bound one variable each, named by their fields
    (AMD-SG-034 §4 item 2), and each coordinate's reference by identity."""
    held = coordinate_bindings(ctx, tuple(coordinates), owner, position)
    parts = {
        identity: reference_term(variable.identity)
        for identity, (variable, _) in zip(coordinates, held)
    }
    return held, parts


def _joint_point(ctx, owner, coordinates, position):
    """The coordinates bound as one variable where a record binds one: an
    integral's variable, a joint choice. It is the coordinate's own variable
    where there is one coordinate, and otherwise one variable named by their
    fields together, `(Ψ, θ)`, over their domain, each coordinate read as a
    component of it. The answer is a one-entry tuple of bindings and the
    references, as `bound_point` answers."""
    coordinates = tuple(coordinates)
    if len(coordinates) == 1:
        return bound_point(ctx, owner, coordinates, position)
    held = bound_variable(
        owner,
        joint_name(coordinates),
        coordinate_domain(ctx, coordinates, owner, use_choice_sets=False),
        position,
    )
    parts = {
        identity: component(reference_term(held.variable.identity), n, len(coordinates))
        for n, identity in enumerate(coordinates)
    }
    return (held,), parts


# --- the names of wires, measures and results ---


def wire_name(stage, sort):
    """The source-notation name or structured expression of one wire.

    Evaluated fields and authored functions retain their names. Generated
    choices and occurrence results print as coordinate lambdas derived from
    wire_expression, stopping at the nearest evaluated or authored function.
    Measures retain their structured construction."""
    identity = sort.identity
    if identity.kind == "function" and identity.mark == "g":
        # a function composed with the law of motion, `𝑉∘𝑔`, and with the
        # law at the policy written out, `𝑉≻∘𝑔(·, 𝑐)` (RL14)
        row = wire_table(stage).produced.get(identity)
        law = _law_symbol(stage, row) if getattr(row, "policy", ()) else LAW_OF_MOTION_LETTER
        return italic(wire_spelling(function_field(identity))) + "∘" + law
    if identity.kind == "choice" and identity.perch is not None:
        expression = _wire_expression_text(stage, sort)
        if expression is not None:
            return expression
        return function_name(identity.field, identity.perch)
    if identity.kind == "function" and identity.perch is not None:
        return function_name(identity.field, identity.perch)
    if identity.kind == "measure":
        return _measure_name(stage, sort)
    if identity.kind == "alias":
        # `…:alias:<block>.<statement>:<name>` is the intermediate result a
        # marked statement defines; the author wrote its last segment
        return function_name(identity.field)
    if identity.is_result:
        # the result of an aggregation an Evaluation names carries that name,
        # `𝑉` for the result of the aggregation that computes `V = 𝑢(c) + V[>]`
        named = written_name(stage, identity)
        if named is not None and named.kind in ("function", "choice", "alias", "field"):
            return function_name(named.field, named.perch)
        return _result_name(stage, sort)
    return wire_spelling(identity)


def _wire_expression_text(stage, sort, points=None):
    """The text of a generated wire, its structured defining expression as
    the record holds it: its bound variables are the stage's coordinates
    (AMD-SG-034 §4 item 2), so nothing is substituted at printing time.

    A direct identity reference is an authored or evaluated name and therefore
    returns None to its caller. With `points`, the names a caller reads the
    wire at, a function is applied to those names; the source perch marks are
    used on this non-card surface.
    """

    expression = wire_expression(stage, sort)
    identity = sort.identity
    referenced = expression
    if isinstance(referenced, T.Sym):
        referenced = referenced.symbol
    if isinstance(referenced, T.Constant):
        referenced = referenced.name
    if referenced == identity:
        return None
    if points is not None and isinstance(expression, S.Lambda):
        expression = S.Apply(expression, tuple(T.Sym(T.Constant(point)) for point in points))
    return format_expression(
        expression, names=_wire_expression_names(stage, expression), width=None
    )


def _wire_expression_names(stage, expression):
    """Exact authored names used while displaying a structured wire formula."""
    expectations = {
        row.identity: row
        for row in wire_table(stage).table.primitive_rows
        if row.kind == "Expectation"
    }
    names = []

    def visit(value):
        if isinstance(value, Identity):
            if value.kind in ("function", "choice") and value.field is not None:
                name = function_name(value.field, value.perch)
                if value.mark == "g":
                    name += "∘" + LAW_OF_MOTION_LETTER
                names.append((value, name))
            elif value.kind == "alias" and value.field is not None:
                names.append((value, function_name(value.field)))
            elif value.kind == "g":
                names.append((value, LAW_OF_MOTION_LETTER))
            elif value.kind == "G":
                names.append((value, AGGREGATOR_LETTER))
            return
        if isinstance(value, S.Measure):
            owner = value.binding[0].identity.owner
            row = expectations.get(owner)
            if row is not None:
                names.append(
                    (value, distribution_symbol(tuple(row.integrated), tuple(row.given or ())))
                )
        if isinstance(value, tuple):
            for item in value:
                visit(item)
        elif dataclasses.is_dataclass(value) and not isinstance(value, type):
            for field in dataclasses.fields(value):
                visit(getattr(value, field.name))

    visit(expression)
    return tuple(names)


def distribution_symbol(subjects, given):
    """A shock probability distribution in a formula (§2.1 item 6): roman `P`
    with its shocks as subscript, `P_{Ψ, θ}`, and `P_{Ψ|ν}` where it is
    conditioned."""
    subscript = ", ".join(subjects) + (f"|{', '.join(given)}" if given else "")
    return f"P_{subscript}" if len(subjects) == 1 and not given else f"P_{{{subscript}}}"


def _measure_name(stage, sort):
    """A measure wire by its construction (§2.1 item 5): the measure of the
    perch, `μ[<]`, or of one branch, `μ_keep≻`; the image under the
    policy of the coordinates it carries a
    control in, `μ∘(id, 𝑐)⁻¹`; and one factor for each declaration whose shocks
    it carries, `⊗ P_{Ψ, θ}` and `⊗ P_{Ψ|ν}` where that declaration is
    conditioned. A measure is named by a formula and not by words such as
    `μ (with policy)`: words cannot be composed in a formula, and they do not
    say that a measure carries the policy and the earlier shock together."""
    if sort.identity.mark == "with-distribution":
        # a measure extended by a declared law is named by its input's name
        # and that law, `μ≺⊗P_ψ⊗P_ξ`, as a term refers to it,
        # the law as the file declares it, `P_{Ψ|ν}`
        return printed_name(sort.identity, _declared_law_names(stage))
    table, _ = fields_of(stage)
    coordinates = tuple(getattr(sort, "coordinates", ()))

    # the policy a control's coordinate carries is that control's own field,
    # which is the field the policy builder writes (AMD-SG-013 §2)
    controls = ", ".join(
        italic(c.stem) for c in coordinates if getattr(table.get(c), "role", None) == "control"
    )
    shocks = tuple(c for c in coordinates if c.perch == SHCK)
    identity = sort.identity
    text = (
        "μ" + (f"_{identity.field}" if identity.field else "") + PERCH_MARK.get(identity.perch, "")
    )
    if controls:
        text += f"∘(id, {controls})⁻¹"
    return text + "".join(f" ⊗ {factor}" for factor in _distribution_factors(stage, shocks))


def _declared_law_names(stage):
    """Each declared law by its declaration's identity and the symbol the
    file's declaration gives it, `P_ψ`, `P_{Ψ, θ}`, `P_{Ψ|ν}` where it is
    conditioned (§2.1 item 6): the names a measure's name reads its laws by."""
    return tuple(
        (
            definition.identity,
            distribution_symbol(
                tuple(definition.equations[0].subjects), distribution_arguments(definition)
            ),
        )
        for definition in stage.definitions.values()
        if definition.kind == "distribution"
    )


def _distribution_factors(stage, shocks):
    """The distribution factors a measure carries, one for each declaration
    whose subjects the measure's shock coordinates name, in the order of those
    coordinates: `P_ν`, `P_{Ψ, θ}`, and `P_{Ψ|ν}` where the declaration is
    conditioned (§2.1 item 6). Roman `P` with the shocks as subscript, since
    `P(Ψ, θ)` reads as a function of the values and `μ_Ψ` is a declared
    parameter of `port.bl`."""
    table = stage.definitions
    names = [shock.stem for shock in shocks]
    factors, seen = [], set()
    for name in names:
        owner = next(
            (
                definition
                for definition in table.values()
                if definition.kind == "distribution" and name in definition.equations[0].subjects
            ),
            None,
        )
        if owner is None:
            factors.append(distribution_symbol((name,), ()))
            continue
        if owner.identity in seen:
            continue
        seen.add(owner.identity)
        factors.append(
            distribution_symbol(tuple(owner.equations[0].subjects), distribution_arguments(owner))
        )
    return tuple(factors)


def _result_name(stage, sort):
    """The structured coordinate-lambda expression of an unnamed result wire;
    where the record holds none, the field the result is named by, and
    otherwise the wire's key."""
    expression = _wire_expression_text(stage, sort)
    if expression is not None:
        return expression
    identity = sort.identity
    if identity.field:
        points = tuple(stems_of(getattr(sort, "coordinates", ())))
        name = function_name(identity.field, identity.perch)
        return name + "(" + ", ".join(points) + ")" if points else name
    return str(identity)


def drawn_wire_names(stage, graph):
    """The name the stage gives each wire of a drawing of `graph`, by the
    wire's identity, which the drawing prints as the wire's label: a result an
    occurrence of a drawn block writes by its structured defining expression
    (`result_labels`), and every other wire but a measure by its value at its
    coordinates, `𝑉≻(a)` (`_applied_name`). A measure is named by the drawing
    from its sort alone."""
    named = result_labels(stage, _blocks_drawn(graph))
    found = {}
    for identity, sort in drawn_sorts(graph).items():
        if getattr(sort, "kind", None) == "measure":
            continue
        if identity.is_result and identity in named:
            found[identity] = named[identity]
        else:
            points = tuple(i.stem for i in getattr(sort, "coordinates", ()))
            found[identity] = _applied_name(stage, sort, points)
    return found


def result_labels(stage, blocks) -> dict:
    """The structured defining expression of each occurrence result.

    Drawings receive the same coordinate-lambda text as signatures and sheets;
    no expectation or aggregation result is replaced by an invented operator
    name (AMD-SG-028 requirement 5)."""
    found = {}
    for block in blocks:
        for rows in builder_rows_of(stage, block):
            for row in rows:
                for wire in row.outputs:
                    if wire.is_result:
                        sort = wire_table(stage).sort_of(wire)
                        found.setdefault(wire, _result_name(stage, sort))
    return found


def _blocks_drawn(graph) -> tuple:
    """The blocks whose boxes a graph holds, read from the box names: the
    segment before the first colon, without a sub-builder's own suffix."""
    found = {}

    def walk(part):
        for box in part.to_diagram().boxes if hasattr(part, "to_diagram") else part.boxes:
            if is_wiring(box):
                continue
            found.setdefault(box_identity(box).block, None)
            if isinstance(box, Bubble):
                walk(box.arg)

    walk(graph)
    return tuple(found)


def _applied_name(stage, sort, points):
    """The structured value of a wire at the supplied coordinate names.

    Authored functions retain their names. Generated choices and occurrence
    results substitute the supplied point into wire_expression."""
    identity = sort.identity
    at = ", ".join(points)
    if identity.kind == "function" and identity.mark == "g":
        row = wire_table(stage).produced.get(identity)
        law = _law_symbol(stage, row, dict(zip(sort.coordinates, points)))
        return italic(wire_spelling(function_field(identity))) + f"({law})"
    if identity.kind == "choice" and identity.perch is not None:
        expression = _wire_expression_text(stage, sort, points)
        if expression is not None:
            return expression
    if identity.kind in ("function", "choice") and identity.perch is not None:
        return function_name(identity.field, identity.perch) + f"({at})"
    if identity.kind == "alias":
        return function_name(identity.field) + f"({at})"
    if identity.kind == "measure":
        return _measure_name(stage, sort)
    if identity.is_result:
        expression = _wire_expression_text(stage, sort, points)
        if expression is not None:
            return expression
        # a result an Evaluation names by a field is that function at the point
        if identity.field:
            return function_name(identity.field, identity.perch) + f"({at})"
        return _result_name(stage, sort)
    return wire_spelling(identity)


def _law_symbol(stage, row, names=None):
    """The law a pulled-back function is composed with, or a measure pushed
    forward along, as a drawing writes it, and with `names`, the name of
    each coordinate of the point by its identity in the point's order, that
    law read at the point: at a label, the section `section_identity` names
    for the construction row the card reads, `𝑔_keep≻` and `𝑔_keep≻(a_d,
    h_d, z_d)`; at the policies the row is held at, the law written out
    (RL14), with a dot for each coordinate of the point and each policy by
    its name, `𝑔(·, 𝑐)`, and read at the point with each policy read at its
    own coordinates, `𝑔(m_d, 𝑐(m_d))`; otherwise the law, `𝑔` and
    `𝑔(m)`."""
    if getattr(row, "section", None) is not None:
        symbol = section_identity(StageNames(stage), row.builder, row.section).field
    elif getattr(row, "policy", ()):
        arguments = _law_arguments_at_policy(stage, row, names)
        return f"{LAW_OF_MOTION_LETTER}({', '.join(arguments)})"
    else:
        symbol = LAW_OF_MOTION_LETTER
    return symbol if names is None else f"{symbol}({', '.join(names.values())})"


def _law_arguments_at_policy(stage, row, names=None):
    """The arguments of the law of motion at the policies a row is held at,
    in the law's order (RL14): a coordinate of the point by its name in
    `names`, or by a dot where no names are given, and a control by its
    policy's name, read at the policy's own coordinates where names are
    given."""
    rendering = wire_table(stage)
    policies = {
        Identity("field", stage=stage.name, perch=policy.perch, field=policy.field): policy
        for policy in row.policy
    }
    found = []
    for identity in law_of_motion_kernel(stage, row.definition).index:
        policy = policies.get(identity)
        if policy is None:
            found.append(OPEN_ARGUMENT if names is None else names.get(identity, identity.stem))
        elif names is None:
            found.append(italic(policy.field))
        else:
            read = (names.get(i, i.stem) for i in rendering.sort_of(policy).coordinates)
            found.append(f"{italic(policy.field)}({', '.join(read)})")
    return found


def _aggregator_symbol(stage, row):
    """The aggregator an Aggregation at the policies it is held at applies,
    as a drawing writes it, written out (RL14): the letter with a dot for
    each argument left open, its value inputs and its coordinates, and each
    policy by its name, in the order of the aggregator's arguments,
    `𝐺(·, ·, 𝑐)`."""
    policies = {
        Identity("field", stage=stage.name, perch=policy.perch, field=policy.field): policy
        for policy in row.policy
    }
    arguments = (
        italic(policies[key].field) if key in policies else OPEN_ARGUMENT
        for key in aggregator_kernel(stage, row).index
    )
    return f"{AGGREGATOR_LETTER}({', '.join(arguments)})"


def drawn_laws(stage, graph):
    """The law or the aggregator each box of a drawing of `graph` applies, by
    the box's identity, where the drawing cannot write it from the box
    alone: for a pullback whose construction row reads the law at a label,
    the section the card writes, `𝑔_keep≻`; for a pullback and a
    push-forward at the policies their row is held at, the law written out,
    `𝑔(·, 𝑐)` (`_law_symbol`); and for an aggregation there, the aggregator
    written out, `𝐺(·, ·, 𝑐)` (`_aggregator_symbol`; RL14). A box at no
    label and no policy applies `𝑔` or `𝐺`, which the drawing writes, and
    is not listed."""
    rows = {}
    for row in wire_table(stage).table.primitive_rows:
        rows.setdefault(row.identity, row)
    found = {}

    def walk(part):
        for box in part.to_diagram().boxes if hasattr(part, "to_diagram") else part.boxes:
            if is_wiring(box):
                continue
            identity = box_identity(box)
            row = rows.get(identity)
            if row is None and identity.kind in ("Pullback", "Pushforward", "Aggregation"):
                row = row_of(stage, box)
            if identity.kind in ("Pullback", "Pushforward") and (
                getattr(row, "section", None) is not None or getattr(row, "policy", ())
            ):
                found[identity] = _law_symbol(stage, row)
            elif (
                identity.kind == "Aggregation"
                and getattr(row, "policy", ())
                and not answers_function_set(stage, row)
            ):
                found[identity] = _aggregator_symbol(stage, row)
            if isinstance(box, Bubble):
                walk(box.arg)

    walk(graph)
    return found
