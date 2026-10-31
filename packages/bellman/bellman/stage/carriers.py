"""A stage's carrier expressions, derived from its declarations and operations.

These queries do not modify a stage. A declared result set specifies a
function carrier; it does not prove that its defining rule is total there.
"""

from __future__ import annotations

import dataclasses

from bellman.fold.block_lines import doc_lines
from bellman.fold.stage_names import StageNames, family_term_arguments
from bellman.fold.wire_terms import is_wire_symbol, term_nodes
from bellman.native import predicates as P
from bellman.native.identity import Identity
from bellman.native.versions import kept_answer
from bellman.stage.grains import answers_function_set, declared_table, is_relation, wire_table
from bellman.stage.kernel_records import aggregator_kernel, law_of_motion_kernel
from bellman.stage.term_operations import relation_of, restrict, slack
from bellman.syntax import terms as T
from bellman.syntax.vocabulary import CONTINUATION, PRIMITIVE_SETS, SHCK
from bellman.typing import sets
from bellman.typing import typed_expressions as S
from bellman.typing.primitive_definitions import bound_variable
from bellman.typing.ranges import arithmetic_range, range_within
from bellman.typing.sets import within
from bellman.typing.typed_expressions import WireType

# --- the carrier of a wire ---


def wire_type(stage, sort):
    """The mathematical carrier of an initial, backward or forward wire."""
    key = (
        "wire carrier",
        sort.identity,
        S.alpha_key(
            (sort.kind, sort.domain, tuple(sort.coordinates), sort.perch, sort.role, sort.z)
        ),
    )
    return kept_answer(stage, key, lambda: _wire_type(stage, sort))


def _wire_type(stage, sort):
    """The type of one wire: its sort, `(kind, classification, coordinates,
    domain, result)`, the carrier of its values and the declarations of the
    sets they name. A field's carrier is the fields its classifier admits, a
    measure's the finite measures on its domain, and a function's the
    measurable functions from its domain to its result set; an Evaluation's
    output keeps the carrier of the wire it evaluates where that is a set of
    sets or unresolved, the output of a row that answers a set of functions
    of its unknowns (`answers_function_set`) carries the sets of the joint
    policies of its controls, and a control's function no row produces
    carries the policies of that control where it is the one control at its
    perch."""
    ctx = StageNames(stage)
    classification = _classified_field(ctx, sort)
    coordinates = tuple(sort.coordinates)
    domain = coordinate_domain(ctx, coordinates, sort.identity)
    result = result_set(ctx, sort) if sort.kind != "measure" else None
    if sort.kind == "field":
        carrier = _field_carrier(ctx, sort, classification)
    elif sort.kind == "measure":
        carrier = S.FiniteMeasureSet(domain)
    else:
        carrier = S.MeasurableMapSet(domain, result)
        # a wire that takes a set of values at each point, the candidate of a
        # line written with a clause, carries maps into the subsets of its
        # result set, a correspondence `Xa ⇉ ℝ₊₊`
        if wire_table(stage).carries_correspondence(sort.identity):
            carrier = S.MeasurableMapSet(domain, S.PowerSet(result))
        row = wire_table(stage).produced.get(sort.identity)
        if row is not None and row.kind == "Evaluation":
            source = wire_table(stage).sort_of(row.inputs[tuple(row.outputs).index(sort.identity)])
            source_carrier = wire_type(stage, source).carrier
            if isinstance(source_carrier, (S.PowerSet, S.Unresolved)):
                carrier = source_carrier
        if row is not None and answers_function_set(stage, row):
            # A joint choice writes one policy. Its wires are the declared
            # controls, as a value bundle's wires are the declared value
            # functions, and each carries the one set of joint policies the
            # choice determines; `component` projects it (AMD-SG-030 §§1, 2).
            # the feasibility is by the correspondence where the file
            # declares one and by the law's image otherwise, on the row as
            # on the Evaluation (AMD-SG-034 §10 item 4)
            carrier = S.PowerSet(
                policy_carrier(
                    ctx, coordinates, row.unknowns, Identity("Evaluation", address=row.builder)
                )
            )
        if row is None and sort.identity.kind == "function" and sort.role == "control":
            controls = tuple(
                i for i in ctx.ports if ctx.role(i) == "control" and i.perch == sort.identity.perch
            )
            if len(controls) == 1:
                carrier = policy_carrier(ctx, coordinates, controls, sort.identity)
            else:
                carrier = S.Unresolved(sort.identity, "joint relation projection")
    declarations = _set_declarations(
        ctx, tuple(ctx.declared_set(i) for i in coordinates) + (sort.domain,)
    )
    return WireType(
        (sort.kind, classification, coordinates, domain, result), carrier, declarations
    )


def _classified_field(ctx, sort):
    identity = sort.identity
    if identity.kind in ("function", "choice") and identity.perch is not None:
        identity = Identity(
            "field", stage=ctx.stage_name, perch=identity.perch, field=identity.field
        )
    field = ctx.ports.get(identity)
    if field is None or field.perch == SHCK:
        return None
    return (field.perch, field.role, resolve_set(ctx, field.domain, identity))


def resolve_set(ctx, term, identity, missing="result set", active=()):
    """A set term with its acyclic set aliases expanded, read without the
    calibration or the methods."""
    if term is None:
        return S.Unresolved(identity, missing)
    if isinstance(term, T.Space):
        return resolve_set(ctx, term.set, identity, missing, active)
    if isinstance(term, T.Named):
        if term.name in PRIMITIVE_SETS:
            return T.Named(PRIMITIVE_SETS[term.name].glyph)
        if term.name in ctx.set_terms and term.name not in active:
            return resolve_set(
                ctx, ctx.set_terms[term.name], identity, missing, active + (term.name,)
            )
        return S.Unresolved(identity, missing + ": " + str(term.name))
    if isinstance(term, T.Product):
        return product(resolve_set(ctx, part, identity, missing, active) for part in term.factors)
    if isinstance(term, T.Comprehension):
        expanded = _expand_nested_sets(ctx, term, identity, missing, active)
        return dataclasses.replace(
            expanded, base=resolve_set(ctx, expanded.base, identity, missing, active)
        )
    if isinstance(term, S.Unresolved):
        return term
    if isinstance(
        term,
        (
            T.Interval,
            T.FiniteSet,
            T.IntegerRange,
            T.Points,
            T.Functions,
            S.FunctionSet,
            S.MeasurableMapSet,
            S.StochasticKernelSet,
            S.FiniteMeasureSet,
            S.ProbabilityMeasureSet,
            S.PowerSet,
        ),
    ):
        return _expand_nested_sets(ctx, term, identity, missing, active)
    return S.Unresolved(identity, missing)


def product(factors):
    """The ordered Cartesian product, with a singleton for no factors."""
    factors = tuple(factors)
    return factors[0] if len(factors) == 1 else T.Product(factors)


def _expand_nested_sets(ctx, term, identity, missing, active):
    names = _named_sets(term) & S.free_identities(term)
    replacements = {
        name: resolve_set(ctx, T.Named(name), identity, missing, active) for name in names
    }
    return S.substitute(term, replacements)


def _named_sets(value):
    if isinstance(value, T.Named):
        return {value.name}
    if isinstance(value, tuple):
        return set().union(*(_named_sets(child) for child in value))
    if dataclasses.is_dataclass(value):
        return set().union(
            *(_named_sets(getattr(value, field.name)) for field in dataclasses.fields(value))
        )
    return set()


# --- the domain of a wire's coordinates ---


def coordinate_domain(ctx, coordinates, owner, *, use_choice_sets=True):
    """The ordered coordinate domain, retaining authored joint restrictions
    and the restriction of each declared multiplier among the coordinates,
    its bound and the product of the multiplier with the bound's slack
    (`observable_restriction`; AMD-SG-035 §5). A domain a multiplier
    restricts is the observable set, whose coordinates are bound as
    variables (`bind_coordinates`)."""
    coordinates = tuple(coordinates)
    domain = _joint_domain(
        coordinates,
        (
            declared_set_term(ctx, ctx.declared_set(identity), identity, "argument set")
            for identity in coordinates
        ),
    )
    observable = tuple(
        condition
        for identity in coordinates
        if ctx.role(identity) == "multiplier"
        for condition in observable_restriction(
            ctx, ctx.multipliers[identity], ctx.multiplier_blocks[identity]
        )
    )
    domain = _feasible_domain(
        ctx,
        coordinates,
        restrict(coordinates, domain, observable),
        use_choice_sets=use_choice_sets,
    )
    return bind_coordinates(ctx, coordinates, owner, domain) if observable else domain


def _joint_domain(coordinates, domains):
    """The domain of several coordinates: the product of their declared
    sets, a set declared by comprehension giving its base, and its conditions
    restricting the product as one comprehension over the coordinates."""
    factors, restrictions = [], []
    for identity, term in zip(coordinates, domains):
        if isinstance(term, T.Comprehension):
            factors.append(term.base)
            variables = S.subject_coordinates(term.bound)
            subject = T.Sym(T.Constant(identity))
            if len(variables) == 1:
                restrictions.extend(
                    S.substitute(term.conds, {S.variable_identity(variables[0]): subject})
                )
            else:
                restrictions.append(P.Member(subject, term))
        else:
            factors.append(term)
    domain = product(factors)
    if restrictions:
        domain = T.Comprehension(
            T.Tuple(tuple(T.Sym(T.Constant(i)) for i in coordinates)), domain, tuple(restrictions)
        )
    return domain


def declared_set_term(ctx, term, identity, missing="result set"):
    """The set a declaration writes, held as written: a primitive spelling
    under its glyph, a set the stage defines by name under that name, a name
    the stage does not define as `Unresolved`, and every other form with the
    names inside it read the same way. A record built from it prints `Xa`
    where the file writes `Xa`; a reader that decides an inclusion resolves it
    first with `resolve_set` (AMD-SG-034 §2 item 0, §4 item 12)."""
    if term is None:
        return S.Unresolved(identity, missing)
    if isinstance(term, T.Space):
        return declared_set_term(ctx, term.set, identity, missing)
    if isinstance(term, T.Named):
        if term.name in PRIMITIVE_SETS:
            return T.Named(PRIMITIVE_SETS[term.name].glyph)
        if term.name in ctx.set_terms:
            return term
        return S.Unresolved(identity, missing + ": " + str(term.name))
    if isinstance(term, T.Product):
        return product(declared_set_term(ctx, part, identity, missing) for part in term.factors)
    if isinstance(term, S.Unresolved):
        return term
    if isinstance(
        term,
        (
            T.Interval,
            T.FiniteSet,
            T.Comprehension,
            T.IntegerRange,
            T.Points,
            T.Functions,
            S.FunctionSet,
            S.MeasurableMapSet,
            S.StochasticKernelSet,
            S.FiniteMeasureSet,
            S.ProbabilityMeasureSet,
            S.PowerSet,
        ),
    ):
        names = _named_sets(term) & S.free_identities(term)
        replacements = {
            name: declared_set_term(ctx, T.Named(name), identity, missing)
            for name in names
            if name not in ctx.set_terms
        }
        return S.substitute(term, replacements) if replacements else term
    return S.Unresolved(identity, missing)


def observable_restriction(ctx, record, block):
    """The conditions a declared multiplier puts on its block's grid
    (AMD-SG-035 §3): the bound as written and the product of the
    multiplier with the bound's slack, `a ≥ 0` and `μ · a = 0`, each over
    identities. `record` is the multiplier's record of kind `multiplier`,
    whose one equation is the declaration with its clause."""
    bound = with_names_as_identities(ctx, block, record.equations[0].bound)
    multiplier = T.Sym(
        T.Constant(
            Identity(
                "field", stage=ctx.stage_name, perch=CONTINUATION, field=record.identity.field
            )
        )
    )
    return bound, P.Compare(T.Mul(multiplier, slack(bound)), "=", T.Number(0))


def with_names_as_identities(ctx, block, term):
    """The term with each name read by its identity (AMD-SG-034 §2 item 0a):
    a field or a multiplier by `ctx.resolve` in `block`, a parameter by its
    identity, a number and `inf` as written; the reading in which
    `_joint_domain` writes its conditions."""
    if isinstance(term, T.Sym) and isinstance(term.symbol, (T.Constant, T.Variable)):
        if term.symbol.name in ("inf", "∞") or isinstance(term.symbol.name, Identity):
            return term
        side = (
            term.symbol.when.side
            if isinstance(term.symbol, T.Variable) and isinstance(term.symbol.when, T.At)
            else None
        )
        return T.Sym(T.Constant(ctx.resolve(term.symbol.name, block, side)))
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return dataclasses.replace(
            term,
            **{
                field.name: with_names_as_identities(ctx, block, getattr(term, field.name))
                for field in dataclasses.fields(term)
            },
        )
    if isinstance(term, tuple):
        return tuple(with_names_as_identities(ctx, block, part) for part in term)
    return term


def _feasible_domain(ctx, coordinates, domain, *, use_choice_sets=True):
    """The state-control coordinates restricted by their feasibility, each
    control by the correspondence the file declares for it, `c ∈ Γ(m_d)`,
    read by reference with the file's arguments (§4 item 5), a control the
    file declares no set for by the image of the law of motion in its
    declared target, `𝑔≻(m_d, c) ∈ Xa`, again by reference (§10 item 4), and
    a label control of a branching block by nothing, each section's range
    being the Pushforward's condition; every condition in one comprehension
    (§4 item 8)."""
    controls = tuple(i for i in coordinates if ctx.role(i) == "control")
    if not controls:
        return domain
    conditions = []
    declared = choice_sets(ctx) if use_choice_sets else ()
    for control, reference, _ in declared:
        if control in controls:
            condition = P.Member(T.Sym(T.Constant(control)), reference)
            if condition not in conditions:
                conditions.append(condition)
    restricted = {control for control, _, _ in declared}
    # a label control of a branching block is typed plainly: each section's
    # range is the Pushforward's condition
    unrestricted = [c for c in controls if c not in restricted and not ctx.labels(c)]
    if unrestricted:
        for definition in ctx.stage_object.definitions.values():
            if definition.kind != "g":
                continue
            spec = law_of_motion_kernel(ctx.stage_object, definition.identity)
            if not set(unrestricted).intersection(spec.index):
                continue
            nonshocks = tuple(i for i in spec.index if ctx.role(i) != "shock")
            if not set(nonshocks).issubset(coordinates):
                continue
            arguments = tuple(T.Sym(T.Constant(i)) for i in spec.index)
            image = S.Apply(
                T.Sym(T.Constant(definition.identity)),
                (arguments[0] if len(arguments) == 1 else T.Tuple(arguments),),
            )
            target = product(
                declared_set_term(ctx, term, definition.identity) for term in spec.output_sets
            )
            condition = P.Member(image, target)
            for shock in reversed(tuple(i for i in spec.index if ctx.role(i) == "shock")):
                condition = T.Operator(
                    "forall",
                    (T.In(shock, declared_set_term(ctx, ctx.declared_set(shock), shock)),),
                    (condition,),
                )
            conditions.append(condition)
    return restrict(coordinates, domain, conditions)


def choice_sets(ctx):
    """The ordered control restrictions the `argmax` lines declare, each as
    `(control, reference, body)`: the reference is the declared set as the
    file writes it, a correspondence applied to the file's arguments,
    `Γ_h(m − c)`, which the records hold (§4 item 5); the body is the
    correspondence's defining set with the arguments substituted, which the
    analysis of ranges reads (`law_range_evidence`). Where the declared
    set is no correspondence, the two are the same term."""
    found = []
    for block, unknowns, equations in _maximisations(ctx):
        local = {name: T.Sym(T.Constant(ctx.resolve(name, block))) for name in ctx.by_name}
        local.update(
            {
                name: T.Sym(T.Constant(Identity("parameter", stage=ctx.stage_name, field=name)))
                for name in ctx.parameter_names
            }
        )
        for term in term_nodes(equations):
            if not isinstance(term, T.Operator) or term.head != "argmax":
                continue
            scope = dict(local)
            for control, sub in zip(unknowns, term.subs):
                if not isinstance(sub, T.In):
                    continue
                feasible = S.substitute(sub.set, scope)
                reference = feasible
                if isinstance(feasible, T.Call):
                    definition = ctx.functions.get(feasible.fun)
                    if definition is not None and definition.kind == "correspondence":
                        reference = S.Apply(T.Sym(T.Constant(definition.identity)), feasible.args)
                        replacements = dict(local)
                        replacements.update(
                            zip((n for n, _ in definition.coordinates), feasible.args)
                        )
                        feasible = S.substitute(definition.equations[0].body, replacements)
                entry = control, reference, feasible
                if entry not in found:
                    found.append(entry)
                scope[sub.var] = T.Sym(T.Constant(control))
    return tuple(found)


def _maximisations(ctx):
    """Every authored maximization with the block it stands in and the
    ordered controls it binds: the lines marked `!doc` of the stage, read by
    identity, and the `Argmax` rows of the declared builders, whose own line
    writes an `argmax`; each as `(block, controls, equations)`. The declared
    rows are read, so that a method block that opens the policy builder
    leaves the policy typed once, on its declared output (specification 0.6
    §4.2)."""
    found = []
    for definition in doc_lines(ctx.stage_object):
        core = definition.equations[0]
        equation = relation_of(core)
        block = definition.identity.block
        found.append((block, tuple(ctx.defined(equation, block)), (equation,)))
    for row in declared_table(ctx.stage_object).primitive_rows:
        if row.kind == "Argmax":
            found.append((row.builder, tuple(row.unknowns), tuple(row.equations)))
    return tuple(found)


# the base of the variables the observable set binds (AMD-SG-035), apart
# from the bases of the other coordinate bindings (100, 130, 200, 500, 600
# and LAW_OUTPUTS, 700)
OBSERVABLE_POINT = 800


def bind_coordinates(ctx, coordinates, owner, domain):
    """A comprehension over the coordinates with each coordinate bound as a
    variable named by its field, `{a, μ ∈ Xa × ℝ₊ | a ≥ 0 ∧ μ · a = 0}` for
    `{a≻, μ≻ ∈ Xa × ℝ₊ | a≻ ≥ 0 ∧ μ≻ · a≻ = 0}`: a bound variable of a
    comprehension is no field (AMD-SG-035). The variables are the
    `coordinate_bindings` of the coordinates at `owner`, and each condition
    reads them in place of the coordinates; a domain that is no
    comprehension over the coordinates is returned as it is."""
    coordinates = tuple(coordinates)
    if not (
        isinstance(domain, T.Comprehension)
        and domain.bound == T.Tuple(tuple(T.Sym(T.Constant(i)) for i in coordinates))
    ):
        return domain
    variables = tuple(
        variable for variable, _ in coordinate_bindings(ctx, coordinates, owner, OBSERVABLE_POINT)
    )
    replacements = {
        identity: T.Sym(T.Constant(variable.identity))
        for identity, variable in zip(coordinates, variables)
    }
    return T.Comprehension(
        T.Subject(variables),
        domain.base,
        tuple(S.substitute(condition, replacements) for condition in domain.conds),
    )


def coordinate_bindings(ctx, coordinates, owner, position):
    """One bound variable per coordinate, named by the coordinate's field
    with its perch and role, over the set the coordinate is declared in
    (AMD-SG-034 §4 item 2). The occurrence of each is `bound_variable_number`
    of `position` and the coordinate's place among the stage's ports, so that
    one coordinate is one variable at one owner and base wherever it is
    bound."""
    places = tuple(ctx.ports)
    return tuple(
        bound_variable(
            owner,
            identity.field,
            declared_set_term(ctx, ctx.declared_set(identity), identity, "argument set"),
            bound_variable_number(
                ctx, position, places.index(identity) if identity in places else 0
            ),
            role=ctx.role(identity) or "bound",
            perch=identity.perch,
        )
        for identity in coordinates
    )


# The occurrence of a coordinate's bound variable stands above every literal
# position the other bindings of the queries use (all below 1000), so that a
# coordinate named as one of them, `a`, `r`, never shares its identity.
COORDINATE_OCCURRENCE_BASE = 1000


def bound_variable_number(ctx, base, place):
    """The occurrence of the variable a coordinate is bound as, from a
    caller's base and the coordinate's place among the stage's ports: the
    base is stretched by one more than the number of ports, so that two
    coordinates at different bases or places never meet, for any number of
    ports, and the whole stands above the literal positions."""
    return COORDINATE_OCCURRENCE_BASE + base * (len(ctx.ports) + 1) + place


def joint_name(identities):
    """The name one variable is bound under for several coordinates together:
    the coordinate's own letter where there is one, `c`, and the letters in
    a tuple otherwise, `(c, h_choice)` for a joint policy, `(Ψ, θ)` for the
    shocks an integral reads under one law (AMD-SG-034 §4 item 2)."""
    names = tuple(identity.field for identity in identities)
    return names[0] if len(names) == 1 else "(" + ", ".join(names) + ")"


# --- the result set of a wire ---


def result_set(ctx, sort, active=()):
    """The declared result, or a registered producing rule's guarded range."""
    if sort.domain is not None:
        return declared_set_term(ctx, sort.domain, sort.identity)
    if sort.identity in active:
        return S.Unresolved(sort.identity, "acyclic result definition")
    rendering = wire_table(ctx.stage_object)
    # one wire, one type: the result an Evaluation names carries the declared
    # set of the field it is named as
    named = written_name(ctx.stage_object, sort.identity)
    if named is not None and named != sort.identity:
        port = rendering.sort_of(named)
        if getattr(port, "domain", None) is not None:
            return declared_set_term(ctx, port.domain, named)
    row = rendering.produced.get(sort.identity)
    if row is None:
        return S.Unresolved(sort.identity, "result set")
    active += (sort.identity,)
    if row.kind == "Argmax" or is_relation(row):
        # the output of a choice or of a relation is its unknown: the
        # declared set of that unknown, and of several together where one
        # output carries them
        if len(row.outputs) == 1 and len(row.unknowns) > 1:
            return product(
                declared_set_term(ctx, ctx.declared_set(unknown), unknown)
                for unknown in row.unknowns
            )
        position = tuple(row.outputs).index(sort.identity)
        if position < len(row.unknowns):
            unknown = row.unknowns[position]
            return declared_set_term(ctx, ctx.declared_set(unknown), unknown)
        return S.Unresolved(sort.identity, "result set")
    if row.kind in ("Pullback", "Evaluation", "Expectation") and row.inputs:
        position = tuple(row.outputs).index(sort.identity)
        source = rendering.sort_of(row.inputs[min(position, len(row.inputs) - 1)])
        value = result_set(ctx, source, active)
        resolved = resolve_set(ctx, value, sort.identity)
        if row.kind != "Expectation" or isinstance(resolved, (T.Interval, T.Named)):
            return value
    if row.kind == "Aggregation":
        position = tuple(row.outputs).index(sort.identity)
        if position < len(row.maps):
            return expression_range(ctx, row.maps[position], row.builder, {}, active)
    return S.Unresolved(sort.identity, "result set")


def written_name(stage, identity):
    """The name a wire an operation writes carries: its own identity for a
    function, a choice, an alias or a field of the file; for an occurrence's
    result, the field the Evaluation reading it names it as, `V` for the
    result of the aggregation that computes `V = 𝑢(c) + V[>]`;
    None for a result no Evaluation names."""
    if not identity.is_result:
        return identity if identity.kind in ("function", "choice", "alias", "field") else None
    for row in wire_table(stage).table.primitive_rows:
        if row.kind == "Evaluation" and identity in row.inputs:
            return row.outputs[tuple(row.inputs).index(identity)]
    return None


def expression_range(ctx, term, block, local, active=()):
    """A range under the expression's definedness requirements, never a
    sample. A selection from a tuple, `(e₁, e₂)[d]`, has the set every entry's
    range is where the entries' ranges are one set, each derived from the
    declarations, and is unresolved where they differ."""
    owner = active[-1] if active else block
    if isinstance(term, T.Number):
        return arithmetic_range(term, {})
    if isinstance(term, T.Sym):
        symbol = term.symbol
        if is_wire_symbol(term):
            return result_set(ctx, wire_table(ctx.stage_object).sort_of(symbol.name), active)
        if symbol.name in local:
            return declared_set_term(ctx, local[symbol.name], owner)
        if isinstance(symbol.name, Identity):
            return declared_set_term(ctx, ctx.declared_set(symbol.name), symbol.name)
        side = (
            symbol.when.side
            if isinstance(symbol, T.Variable) and isinstance(symbol.when, T.At)
            else None
        )
        identity = ctx.resolve(symbol.name, block, side)
        return declared_set_term(ctx, ctx.declared_set(identity), identity)
    if isinstance(term, T.Tuple):
        return product(expression_range(ctx, child, block, local, active) for child in term.items)
    if (
        isinstance(term, T.Select)
        and isinstance(term.sel, T.Key)
        and not isinstance(term.family, T.Tuple)
    ):
        # one key of a collection on an index set fixed: the entries' set, or
        # the collection on the remaining factors, read through the stage's
        # named sets; a selection from a product keeps its earlier reading
        family = expression_range(ctx, term.family, block, local, active)
        indexed = (
            sets.index_sets(family, ctx.set_terms)
            if isinstance(family, T.setexpr) and not _has_unresolved(family)
            else None
        )
        if indexed is not None:
            return resolve_set(ctx, indexed[1], owner)
    if isinstance(term, T.Select) and isinstance(term.family, T.Tuple):
        # one entry of a tuple read by a key or a position: the set every
        # entry's range is where all are one set, each derived from the
        # declarations; unresolved where the entries' sets differ, since no
        # rule chooses among them
        values = tuple(
            expression_range(ctx, child, block, local, active) for child in term.family.items
        )
        if (
            values
            and not any(_has_unresolved(value) for value in values)
            and all(S.alpha_equivalent(value, values[0]) for value in values[1:])
        ):
            return values[0]
        return S.Unresolved(owner, "expression result")
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div, T.Pow, T.Neg)):
        # the operands' sets are read resolved: the arithmetic of ranges
        # decides on values, not on the names the file declares
        values = tuple(
            resolve_set(
                ctx, expression_range(ctx, getattr(term, field.name), block, local, active), owner
            )
            for field in dataclasses.fields(term)
        )
        if any(isinstance(value, S.Unresolved) for value in values):
            return S.Unresolved(owner, "arithmetic operand result")
        names = tuple("operand_" + str(n) for n in range(len(values)))
        operation = type(term)(*(T.Sym(T.Constant(name)) for name in names))
        enclosed = arithmetic_range(operation, dict(zip(names, values)))
        if enclosed is not None:
            return enclosed
        if all(within(value, T.Named("ℝ"), {}) is True for value in values):
            return T.Named("ℝ")
        if all(
            within(value, T.Named("ℝ"), {}) is True
            or isinstance(value, T.Interval)
            or isinstance(value, T.Named)
            and value.name in PRIMITIVE_SETS
            for value in values
        ):
            return T.Named("ℝ̄")
    if isinstance(term, T.Call):
        if term.fun in ("exp", "log", "max", "min"):
            for argument in term.args:
                value = expression_range(ctx, argument, block, local, active)
                if isinstance(value, S.Unresolved):
                    return value
                if _has_unresolved(value):
                    return S.Unresolved(owner, "argument result of " + str(term.fun))
            return T.Named("ℝ")
        definition = ctx.functions.get(term.fun)
        if definition is not None and definition.identity not in active:
            core = definition.equations[0]
            if isinstance(core, T.FuncDef):
                return expression_range(
                    ctx,
                    core.body,
                    definition.address,
                    dict(definition.coordinates),
                    active + (definition.identity,),
                )
        return S.Unresolved(owner, "result of " + str(term.fun))
    return S.Unresolved(owner, "expression result")


def _has_unresolved(value):
    if isinstance(value, S.Unresolved):
        return True
    if isinstance(value, tuple):
        return any(_has_unresolved(child) for child in value)
    if dataclasses.is_dataclass(value):
        return any(
            _has_unresolved(getattr(value, field.name)) for field in dataclasses.fields(value)
        )
    return False


# --- the carriers of a field and of a policy, and the sets a carrier names ---


def _field_carrier(ctx, sort, classification):
    """The carrier of a field wire: the finite set of the stage's fields at
    its perch and role whose declared sets lie in the classifier's result
    set; `Unresolved` where the field has no classification or an inclusion
    is not decided."""
    if classification is None:
        return S.Unresolved(sort.identity, "field classification")
    perch, role, result = classification
    if _has_unresolved(result):
        return S.Unresolved(sort.identity, "field classifier result set")
    members = []
    for identity, field in ctx.ports.items():
        if (field.perch, field.role) != (perch, role):
            continue
        declared = resolve_set(ctx, field.domain, identity)
        if _has_unresolved(declared):
            return S.Unresolved(sort.identity, "classifier inclusion for " + str(identity))
        inclusion = S.alpha_equivalent(declared, result) or within(declared, result, {})
        if inclusion is None:
            return S.Unresolved(sort.identity, "classifier inclusion for " + str(identity))
        if inclusion:
            members.append(identity)
    return T.FiniteSet(tuple(members))


# the bases of the bound variables of a policy's carrier: its functions, one
# per control, and the point they are read at
POLICY_FUNCTIONS, POLICY_POINT = 500, 600


def policy_carrier(ctx, coordinates, controls, owner, *, use_choice_sets=True):
    """The policies: the measurable functions of the controls, one per
    control and named by it, whose values at the point lie in the feasible
    set, `{𝑐 ∈ (Xm → ℝ₊₊) | 𝑐(m_d) ∈ Γ(m_d)}`, the state coordinate free and
    read at every point (AMD-SG-034 §4 items 3 to 5; §10 items 4 and 5); for
    several controls the functions together, `{𝑐, ℎ_choice ∈ (X → ℝ₊₊) ×
    (X → ℝ₊₊) | 𝑐(m, z_d) ∈ Γ_c(m) ∧ ℎ_choice(m, z_d) ∈ Γ_h(m − 𝑐(m, z_d))}`.
    The conditions are those of the feasible domain of the state-control
    pairs (`_feasible_domain`), with each control substituted by its function
    at the point and each state coordinate by its variable; with none, the
    carrier is the set of the measurable functions itself."""
    coordinates, controls = tuple(coordinates), tuple(controls)
    functions = policy_functions(ctx, coordinates, controls, owner)
    points = coordinate_bindings(ctx, coordinates, owner, POLICY_POINT)
    states = tuple(T.Sym(T.Constant(point.variable.identity)) for point in points)
    x = states[0] if len(states) == 1 else T.Tuple(states)
    feasible = coordinate_domain(
        ctx, coordinates + controls, owner, use_choice_sets=use_choice_sets
    )
    replacements = {identity: state for identity, state in zip(coordinates, states)}
    replacements.update(
        {
            control: S.Apply(T.Sym(T.Constant(function.variable.identity)), (x,))
            for control, function in zip(controls, functions)
        }
    )
    conditions = tuple(
        S.substitute(condition, replacements)
        for condition in (feasible.conds if isinstance(feasible, T.Comprehension) else ())
    )
    # a joint policy is one function of the state into the product of the
    # controls' sets, `(𝑐, 𝑐_p) : X → ℝ₊₊ × ℝ₊`, its components named by the
    # controls; one control's is its own function
    joint = S.MeasurableMapSet(
        functions[0].domain.domain, product(function.domain.codomain for function in functions)
    )
    # where no condition restricts the policies, their carrier is the set of
    # the measurable functions itself, `𝑑 : X∼ → J`
    return (
        T.Comprehension(
            T.Subject(tuple(function.variable for function in functions)), joint, conditions
        )
        if conditions
        else joint
    )


def policy_functions(ctx, coordinates, controls, owner):
    """One measurable function per control, bound under the control's own
    name, from the domain of the coordinates to the control's declared set
    (AMD-SG-034 §4 item 4): the candidates a policy's carrier ranges over."""
    domain = coordinate_domain(ctx, coordinates, owner)
    return tuple(
        bound_variable(
            owner,
            control.field,
            S.MeasurableMapSet(domain, declared_set_term(ctx, ctx.declared_set(control), control)),
            POLICY_FUNCTIONS + n,
            role="control",
            perch=control.perch,
        )
        for n, control in enumerate(controls)
    )


def _set_declarations(ctx, terms):
    """Named sets used by these declarations, with their
    mathematical expressions."""
    names = _named_sets(tuple(terms))
    return tuple(
        (name, resolve_set(ctx, T.Named(name), name))
        for name in sorted(names)
        if name in ctx.set_terms
    )


# --- the carrier of a definition ---


def definition_type(stage, definition, row=None, coordinates=None):
    """The carrier of a utility function or one retained g/G segment."""
    key = (
        "definition carrier",
        definition.identity if definition is not None else None,
        row.identity if row is not None else None,
        tuple(coordinates or ()),
    )
    return kept_answer(stage, key, lambda: _definition_type(stage, definition, row, coordinates))


def _definition_type(stage, definition, row, coordinates):
    """The type of a definition, or of the distribution a row integrates
    where no definition is given, a kernel from the row's coordinates to the
    shocks it integrates. A declared distribution is a kernel from the
    coordinates it is conditioned on to its subjects, or a probability
    measure on its subjects where it is unconditional; a law of motion g or a
    segment of G maps its arguments' feasible domain into the product of its
    output sets, a law whose lines stand in branches into the tuple of its
    branches' products indexed by its label coordinate; a correspondence
    maps into the sets of its values; and a declared function into the range
    of its body."""
    ctx = StageNames(stage)
    if definition is None and row is not None:
        coordinates = tuple(coordinates or ())
        shocks = row.integrated or tuple(
            name
            for identity in row.references
            if identity in stage.definitions and stage.definitions[identity].kind == "distribution"
            for name in stage.definitions[identity].equations[0].subjects
        )
        subjects = tuple(
            Identity("field", stage=ctx.stage_name, perch=SHCK, field=name) for name in shocks
        )
        domain = coordinate_domain(ctx, coordinates, row.identity)
        target = coordinate_domain(ctx, subjects, row.identity)
        return WireType(
            ("distribution", None, coordinates, domain, target),
            S.StochasticKernelSet(domain, target),
            _set_declarations(ctx, tuple(ctx.declared_set(i) for i in coordinates + subjects)),
        )
    if definition.kind == "distribution":
        law = definition.equations[0]
        coordinates = tuple(i for _, i in family_term_arguments(law.law, ctx))
        subjects = tuple(
            Identity("field", stage=ctx.stage_name, perch=SHCK, field=name)
            for name in law.subjects
        )
        domain = coordinate_domain(ctx, coordinates, definition.identity)
        target = coordinate_domain(ctx, subjects, definition.identity)
        # an unconditional law is a member of the probability measures on
        # its support; a kernel only where the file conditions the law
        # (AMD-SG-034 §4 item 7, §10 item 7)
        carrier = (
            S.StochasticKernelSet(domain, target)
            if coordinates
            else S.ProbabilityMeasureSet(target)
        )
        return WireType(
            ("distribution", None, coordinates, domain, target),
            carrier,
            _set_declarations(ctx, tuple(ctx.declared_set(i) for i in coordinates + subjects)),
        )
    spec = (
        law_of_motion_kernel(stage, definition.identity)
        if definition.kind == "g"
        else aggregator_kernel(stage, row)
        if definition.kind == "G" and row is not None
        else None
    )
    if spec is not None:
        coordinates = tuple(spec.index)
        domain = _joint_domain(
            coordinates,
            (
                declared_set_term(ctx, value, identity, "argument set")
                for identity, value in zip(coordinates, spec.argument_sets)
            ),
        )
        domain = _feasible_domain(ctx, coordinates, domain)
        result = product(
            declared_set_term(ctx, value, spec.identity) for value in spec.output_sets
        )
        # a law whose lines stand in branches writes into the tuple of its
        # branches' products indexed by its label coordinate,
        # `(ℝ₊₊ × ℝ₊₊ × ℝ₊₊, ℝ₊₊ × ℝ₊₊)[d]`, the form of its own value
        labels = (
            tuple(dict.fromkeys(Identity("line", address=a).branch for a in spec.sources))
            if definition.kind == "g"
            else ()
        )
        if labels and None not in labels:
            key = next(k for k in spec.index if ctx.labels(k))
            result = T.Select(
                T.Tuple(
                    tuple(
                        product(
                            declared_set_term(ctx, value, spec.identity)
                            for value, a in zip(spec.output_sets, spec.sources)
                            if Identity("line", address=a).branch == label
                        )
                        for label in labels
                    )
                ),
                T.Key(T.Sym(T.Constant(key))),
            )
    else:
        coordinates = tuple(
            Identity("function-parameter", owner=definition.identity, occurrence=n, field=name)
            for n, (name, _) in enumerate(definition.coordinates)
        )
        domain = _joint_domain(
            coordinates,
            (
                declared_set_term(ctx, value, identity, "argument set")
                for identity, (_, value) in zip(coordinates, definition.coordinates)
            ),
        )
        core = definition.equations[0]
        if isinstance(core, T.CorrDef):
            result = S.PowerSet(correspondence_values(ctx, definition))
            return WireType(
                ("function", None, coordinates, domain, result),
                S.FunctionSet(domain, result),
                _set_declarations(ctx, tuple(value for _, value in definition.coordinates)),
            )
        result = (
            expression_range(
                ctx,
                core.body,
                definition.address,
                dict(definition.coordinates),
                (definition.identity,),
            )
            if isinstance(core, T.FuncDef)
            else S.Unresolved(definition.identity, "defining function result")
        )
    declarations = _set_declarations(
        ctx,
        tuple(spec.argument_sets) + tuple(spec.output_sets)
        if spec is not None
        else tuple(value for _, value in definition.coordinates),
    )
    return WireType(
        ("function", None, coordinates, domain, result),
        (
            S.FunctionSet(domain, result)
            if definition.kind == "G"
            else S.MeasurableMapSet(domain, result)
        ),
        declarations,
    )


def correspondence_values(ctx, definition):
    """The declared control set of a correspondence, not an arbitrary
    real set."""
    for _, unknowns, equations in _maximisations(ctx):
        for term in term_nodes(equations):
            if isinstance(term, T.Operator) and term.head == "argmax":
                for unknown, sub in zip(unknowns, term.subs):
                    if (
                        isinstance(sub, T.In)
                        and isinstance(sub.set, T.Call)
                        and sub.set.fun == definition.identity.field
                    ):
                        return declared_set_term(ctx, ctx.declared_set(unknown), unknown)
    body = definition.equations[0].body
    base = body.base if isinstance(body, T.Comprehension) else body
    if isinstance(base, T.Interval):
        return T.Named("ℝ")
    if isinstance(base, (T.IntegerRange, T.Points)):
        return T.Named("ℤ")
    if isinstance(base, T.Product):
        return product(
            T.Named("ℝ")
            if isinstance(factor, T.Interval)
            else T.Named("ℤ")
            if isinstance(factor, (T.IntegerRange, T.Points))
            else declared_set_term(ctx, factor, definition.identity)
            for factor in base.factors
        )
    if isinstance(body, T.Comprehension):
        return declared_set_term(ctx, base, definition.identity)
    return S.Unresolved(definition.identity, "correspondence value set")


# --- the ranges of the laws of motion ---


def law_range_evidence(stage):
    """Decided memberships for the restricted laws, keyed by authored line."""
    ctx = StageNames(stage)
    domains = {
        identity: resolve_set(ctx, declared, identity) for identity, declared in ctx.sets.items()
    }
    # the analysis of ranges reads the bodies of the correspondences, the
    # records their references (AMD-SG-034 §4 item 5)
    restrictions = tuple((control, body) for control, _, body in choice_sets(ctx))
    found = {}

    def resolved(term, block):
        if isinstance(term, T.Sym):
            symbol = term.symbol
            if isinstance(symbol.name, Identity):
                return term
            side = (
                symbol.when.side
                if isinstance(symbol, T.Variable) and isinstance(symbol.when, T.At)
                else None
            )
            return T.Sym(T.Constant(ctx.resolve(symbol.name, block, side)))
        if isinstance(term, tuple):
            return tuple(resolved(part, block) for part in term)
        if dataclasses.is_dataclass(term):
            return dataclasses.replace(
                term,
                **{
                    field.name: resolved(getattr(term, field.name), block)
                    for field in dataclasses.fields(term)
                },
            )
        return term

    for definition in stage.definitions.values():
        if definition.kind != "g":
            continue
        spec = law_of_motion_kernel(stage, definition.identity)
        # a label control selects the line and enters no line's value, so a
        # branch line's range is decided by its arithmetic
        controls = tuple(i for i in spec.index if ctx.role(i) == "control" and not ctx.labels(i))
        restricted = tuple((i, domain) for i, domain in restrictions if i in controls)
        for line, term, target in zip(spec.sources, spec.terms, spec.output_sets):
            if target is None:
                continue
            target = resolve_set(ctx, target, definition.identity)
            if _has_unresolved(target):
                continue
            if controls and any(i not in dict(restricted) for i in controls):
                found[str(line)] = (
                    target,
                    ("restriction to the declared output set in D_g at " + str(line),),
                )
                continue
            answer, evidence = range_within(
                resolved(term, spec.builder), target, domains, restricted
            )
            if answer is True:
                enclosure = next(value[1] for value in evidence if value[0] == "range")
                declarations = tuple(
                    "declared choice set for " + str(identity) + ": " + S.format_expression(domain)
                    for identity, domain in restricted
                )
                found[str(line)] = (
                    enclosure,
                    declarations + ("arithmetic range inclusion at " + str(line),),
                )
    return found
