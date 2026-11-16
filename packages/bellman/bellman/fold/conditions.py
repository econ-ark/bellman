"""The conditions of a stage and the readings the stage's questions make of
the fold: `domain_conditions`, the conditions a stage's lines leave
undischarged, each a term with the identities it names;
`conditional_distribution_of`, the conditional distribution an expectation's
row selects; `edge_drawing`, the forward block whose edge draws a set of
shocks; `check_calibrated_distributions`, the conditions on a distribution's
arguments that the calibration's numbers decide; and `parameters_named`, the
parameters a builder's rows name.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping

from bellman.distributions.conditionals import (
    check_conditioning_covariance,
    conditioning_shocks,
    select_conditional,
)
from bellman.distributions.edges import JointDistribution
from bellman.distributions.families import check_family_conditions, specialize_distribution
from bellman.fold.block_lines import blocks_in_file_order
from bellman.fold.declared_sets import (
    argmax_of,
    binder_sets,
    binder_value_set,
    callable_at,
    inverted_function,
    right_side_set,
    set_lies_within,
    subject_dimension,
)
from bellman.fold.derived_parameters import derived_values
from bellman.fold.stage_fold import block_rows_of, stage_blocks_of
from bellman.fold.stage_names import StageNames, lines_of
from bellman.fold.wire_terms import (
    arithmetic_nodes,
    guarded_term_nodes,
    symbol_occurrences,
    term_nodes,
)
from bellman.native.identity import Identity, piece_identity
from bellman.native.predicates import Compare, Member, Not, Or
from bellman.native.provenance import source_file
from bellman.native.records import UNDECLARED_SET, Refusal
from bellman.native.versions import kept_answer
from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.typing import sets
from bellman.typing import typed_expressions as S
from bellman.typing.line_unknowns import CALL_OPERATORS
from bellman.typing.primitive_definitions import primitive_definition


def domain_conditions(stage) -> tuple:
    """The domain conditions of a stage that the construction cannot
    discharge, computed on the retained terms with the sets the sorts and
    the definitions carry (AMD-SG-006 §5; AMD-SG-017 §4), as (condition,
    identities) pairs, with the explanation third where one is written, in
    order of first appearance. Each entry of an obligation is one of the five
    typed kinds of AMD-SG-017 §4:

    - `range-compatibility` (the line, the set of the right side, the set
      of the field the line defines) when the right side is not known to lie
      in the declared set of the left side — the sets compared by
      `sets.within`, so that `m_d = m` with both fields on `Xm` raises
      nothing and `a = m_d - c` with `a` on `ℝ₊` does; a candidate with no
      declared range stands as the record of an undeclared set and never as a
      word. On a line whose right side is an `argmax` the obligation is §5.4's:
      the binder's set against the declared set of the control in the same
      position of the left side;
    - `function-argument-domain-inclusion` (the line, the function, the
      parameter of its definition, the argument's set, the parameter's set)
      when an argument is not known to lie in the set of the coordinate it is
      passed to;
    - `binding-domain` (the binder, the line) for a binder of an `argmax` or
      a `solve` that no field or parameter declares;
    - `numeric-domain-compatibility` (the set, the line) when an operand of
      the arithmetic lies in a set the rules do not decide numeric;
    - `external-callable-result-domain` (the callable's result, the line) for
      a call no definition of the stage declares;
    - `inverse-function-domain` (the definition, the function inverted) for an
      inverse the file takes;
    - `law-support` (the shock identities) for every
      distribution declaration.

    The set of a term is `right_side_set`'s and no other."""
    ctx = StageNames(stage)
    found = {}
    for box in blocks_in_file_order(stage):
        for _, line in lines_of(stage, box):
            _line_conditions(ctx, box.name, line, found)
    for definition in stage.definitions.values():
        _definition_conditions(ctx, definition, found)
    _index_set_conditions(ctx, stage, found)
    return tuple(found.values())


def _index_set_conditions(ctx, stage, found):
    """`index-set-bounds` and `index-set-members` for every integer range and
    every listed set of integers in a retained definition or a field's
    declared set, function parameters and nested set expressions included.
    Each condition belongs to the definition or field that writes the set
    and is decided when its parameters have values
    (`sets.finite_set_conditions`)."""
    owners = [
        (definition.identity, equation)
        for definition in stage.definitions.values()
        for equation in definition.equations
    ]
    owners.extend((identity, declared) for identity, declared in ctx.sets.items())
    for identity, declared in owners:
        for subterm in term_nodes(declared):
            if not isinstance(subterm, (T.IntegerRange, T.Points)):
                continue
            for condition, predicate in sets.finite_set_conditions(subterm):
                if condition == "index-set-bounds":
                    sentence = (
                        f"The bounds of {to_source(subterm)}, declared for {identity}, must be "
                        "integers in order."
                    )
                else:
                    sentence = (
                        f"The members of {to_source(subterm)}, declared for {identity}, must "
                        "be distinct integers"
                        + (
                            f" and lie in {to_source(subterm.superset)}."
                            if subterm.superset is not None
                            else "."
                        )
                    )
                _record(found, condition, (identity, predicate), sentence)


def _record(found, condition, identities, explanation=""):
    """The entry of a condition in `found`, made once, with the explanation of
    its first occurrence: `found` maps (condition, identities) to the entry,
    in order of first appearance."""
    found.setdefault(
        (condition, identities),
        (condition, identities, explanation) if explanation else (condition, identities),
    )


def _line_conditions(ctx, block, line, found):
    """The conditions of one line: the range of the field it defines (§5.4's
    for an `argmax`), then those of its right side, whose `argmax` binders
    range over the sets they bind, and of the bound of its clause."""
    core = line.core
    equation = core.core if isinstance(core, T.Slack) else core
    defined = ctx.defined(equation, block) if isinstance(equation, T.Equation) else ()
    maximisation = argmax_of(equation.rhs)
    if isinstance(equation, T.Equation):
        if maximisation is not None:
            _argmax_range(equation, defined, line.address, ctx, found)
        elif defined:
            _range_condition(ctx, block, line.address, equation, defined[0], found)
    local = {}
    if maximisation is not None:
        for position, sub in enumerate(maximisation.subs):
            if isinstance(sub, T.In) and position < len(defined):
                local[sub.var] = binder_value_set(sub.set, ctx)
    _term_conditions(ctx, equation.rhs, line.address, block, local, found)
    if isinstance(core, T.Slack):
        _term_conditions(ctx, core.bound, line.address, block, {}, found)


def _range_condition(ctx, block, address, equation, field, found):
    """`range-compatibility` for a line whose right side lies in a set outside
    the declared set of the field it defines."""
    declared = ctx.sets.get(field)
    if declared is None:
        return
    produced = right_side_set(equation.rhs, ctx, block, binder_sets(equation.rhs, {}))
    # Where the right side declares no range, the declared set of the left
    # side is where the line's values lie and no condition is formed. A
    # produced set outside the declared one is recorded with a sentence that
    # names the fields as the file writes them, not by the kernel's letters.
    if produced is not None and not set_lies_within(produced, declared, ctx):
        outer = to_source(declared)
        left = to_source(equation.lhs)
        right = to_source(equation.rhs)
        _record(
            found,
            "range-compatibility",
            (piece_identity(address), produced, declared),
            f"{left} is declared in {outer} while {right} "
            f"is declared in {to_source(produced)}, so the construction "
            f"assumes every value the line {address} writes lies in {outer}",
        )


def _term_conditions(ctx, term, address, block, local, found):
    """The conditions of one term at its place: those of each call and of each
    binder in the order the walk meets them, then those of the operands of its
    arithmetic. `local` holds the sets of the bound names in scope."""
    place = address if isinstance(address, Identity) else piece_identity(address)
    local = binder_sets(term, local)
    for node, guard in guarded_term_nodes(term):
        if isinstance(node, T.Call):
            _call_conditions(ctx, node, place, block, local, found, guard)
        elif isinstance(node, T.Operator) and node.head != "E":
            _binder_conditions(ctx, node, place, block, found)
        elif isinstance(node, T.Select) and isinstance(node.sel, (T.Key, T.Term)):
            _selection_conditions(ctx, node, place, block, local, found)
    _arithmetic_conditions(ctx, term, place, block, local, found)


def _selection_conditions(ctx, node, place, block, local, found, *, formal=None, guard=None):
    """`set-inclusion` for a selection from a collection on an index set by
    a key whose declared set the terms alone do not place within that index
    set. An unapplied law formal has a membership condition at the point
    until its argument supplies a set."""
    family = right_side_set(node.family, ctx, block, local)
    indexed = sets.index_sets(family, ctx.set_terms) if family is not None else None
    if indexed is None:
        return
    first, _ = indexed
    key = node.sel.at if isinstance(node.sel, T.Term) else T.Sym(T.Constant(node.sel.at))
    key_set = right_side_set(key, ctx, block, local)
    if (
        isinstance(key_set, T.Sym)
        and isinstance(key_set.symbol, T.Constant)
        and key_set.symbol.name in ctx.set_terms
    ):
        # a binder's set is read as the name it writes, `argmax_{jp : L_J}`
        key_set = T.Named(key_set.symbol.name)
    if key_set is None:
        if formal is not None:
            index_set = sets.defined(first, ctx.set_terms)
            predicate = Member(T.Sym(T.Constant(formal)), index_set)
            _record(
                found,
                "set-inclusion",
                (place, formal, predicate if guard is None else Or(Not(guard), predicate)),
                f"The argument {formal.field} must belong to the index set "
                f"{to_source(index_set)} of {to_source(node.family)} when it is selected.",
            )
        return
    if sets.index_within(key_set, first, ctx.set_terms) is not None:
        return
    index_set = sets.defined(first, ctx.set_terms)
    key_set = sets.defined(key_set, ctx.set_terms)
    _record(
        found,
        "set-inclusion",
        (place, key_set, index_set, Compare(key_set, "⊆", index_set)),
        f"The set {to_source(key_set)} of {to_source(key)} must lie within the index set "
        f"{to_source(index_set)} of {to_source(node.family)} at {place}.",
    )


def _call_conditions(ctx, node, place, block, local, found, guard):
    """The conditions of one call: `inverse-function-domain` for an inverse,
    `external-callable-result-domain` for a callable no definition of the
    stage declares, and `function-argument-domain-inclusion` for each argument
    not known to lie in the set of the coordinate it is passed to."""
    if node.fun in ctx.law_formals:
        return
    functions = ctx.functions
    if node.fun == "Inv":
        # the obligation names the function inverted, so that the
        # object states the relation the inverse stands in
        # (AMD-SG-017 §5.1; AMD-SG-014 §3)
        _record(
            found,
            "inverse-function-domain",
            (place, inverted_function(node, functions)),
            f"The function {inverted_function(node, functions)} inverted at {place} must be "
            "one-to-one on its domain, and the arguments of the inverse must lie in its image.",
        )
        return
    definition = functions.get(node.fun)
    if definition is not None:
        identity, coordinates = definition.identity, definition.coordinates
    elif node.fun in ("exp", "log"):
        primitive = primitive_definition(node.fun)
        identity = primitive.identity
        ((formal, domain),) = primitive.equations[0].bindings
        # The primitive term uses a numerical endpoint for infinity.
        if node.fun == "log":
            domain = T.Named("ℝ₊₊")
        coordinates = ((formal.identity.field, domain),)
    else:
        declared = callable_at(node.fun, ctx, block, local)
        if declared is None:
            if node.fun not in CALL_OPERATORS:
                _record(
                    found,
                    "external-callable-result-domain",
                    (Identity("external", field=node.fun, mark="result"), place),
                    f"The result of {node.fun} at {place} must lie in the set required there.",
                )
            return
        identity = ctx.resolve(node.fun, block)
        coordinates = (("argument", declared.domain),)
    for index, ((name, declared), argument) in enumerate(zip(coordinates, node.args)):
        if declared is None:
            continue
        actual = right_side_set(argument, ctx, block, local)
        if actual is None or not set_lies_within(actual, declared, ctx):
            coordinate = Identity(
                "function-parameter", owner=identity, occurrence=index, field=name
            )
            _record(
                found,
                "function-argument-domain-inclusion",
                (
                    place, identity, coordinate,
                    UNDECLARED_SET if actual is None else actual, declared,
                    node,
                ) + ((guard,) if guard is not None else ()),
                f"The argument for {name} of {identity} at {place}, from "
                f"{to_source(actual) if actual is not None else 'an undeclared set'}, "
                f"must belong to {to_source(declared)}.",
            )


def _binder_conditions(ctx, node, place, block, found):
    """`binding-domain` for each variable an operator binds bare, as
    `argmax_{c}` does, that no field or parameter declares."""
    for sub in node.subs:
        if isinstance(sub, T.In):
            continue
        if sub.name not in ctx.parameter_names and ctx.resolve(sub.name, block) not in ctx.ports:
            _record(
                found,
                "binding-domain",
                (T.Sym(T.Constant(sub.name)), place),
                f"The bound variable {sub.name} at {place} needs a declared domain.",
            )


def _arithmetic_conditions(ctx, term, place, block, local, found):
    """`numeric-domain-compatibility` for each name an arithmetic node of the
    term reads whose set the rules do not decide numeric."""
    for node in arithmetic_nodes(term):
        operands = [getattr(node, f.name) for f in dataclasses.fields(node)]
        for operand in operands:
            if isinstance(operand, T.Sym):
                setterm = right_side_set(operand, ctx, block, local)
                if setterm is not None and sets.numeric(setterm, ctx.set_terms) is None:
                    _record(
                        found,
                        "numeric-domain-compatibility",
                        (setterm, place),
                        f"The set {to_source(setterm)} used in "
                        f"arithmetic at {place} must be numeric.",
                    )


def _definition_conditions(ctx, definition, found):
    """The conditions of one definition: those of a function's or a
    correspondence's body, its parameters' declared sets in scope, and of a
    function alias's term, placed at the definition's identity, which resolves
    in the definitions table, its address being the ordinal of the item in the
    file (AMD-SG-014 §3); and `law-support` for a distribution. A derived
    parameter has here no condition of its own: where the declared sets
    leave its definition open, the definition calls log, exp, min or max or
    it is written by cases, and only there, the fold records for it the one
    obligation that its value is a finite real number, or a finite real
    number or an infinity that its declared set may hold, which the
    calibration decides by evaluating its definition
    (`stage_fold._derived_definedness`; AMD-MT-003, build contract §5;
    AMD-GRAM-006)."""
    if definition.kind in ("function", "correspondence"):
        _term_conditions(
            ctx,
            definition.equations[0].body,
            definition.identity,
            None,
            {name: s for name, s in definition.coordinates if s is not None},
            found,
        )
    elif definition.kind == "function_alias":
        _term_conditions(ctx, definition.equations[0], definition.identity, None, {}, found)
    elif definition.kind == "distribution":
        law = definition.equations[0]
        subjects = law.subjects
        _record(
            found,
            "law-support",
            tuple(
                Identity("field", stage=ctx.stage_name, perch="shck", field=name)
                for name in subjects
            ),
            f"The distribution of {', '.join(subjects)} gives probability only to values "
            f"in the declared shock set{'s' if len(subjects) > 1 else ''}.",
        )
        _law_index_conditions(ctx, definition, law, found)


def _law_index_conditions(ctx, definition, law, found):
    """Membership requirements for local law indices whose sets are unknown."""
    formals = dict(distribution_formal_fields(ctx.stage_object, definition))
    local = {name: ctx.declared_set(identity) for name, identity in formals.items()}
    if None not in local.values():
        return
    bound = {name: T.Sym(T.Constant(identity)) for name, identity in formals.items()}
    for node, guard in guarded_term_nodes(law.law):
        if (
            isinstance(node, T.Select)
            and isinstance(node.sel, T.Key)
            and node.sel.at in local
            and local[node.sel.at] is None
        ):
            _selection_conditions(
                ctx, node, definition.identity, None, local, found,
                formal=formals[node.sel.at],
                guard=S.substitute(guard, bound) if guard is not None else None,
            )


def _argmax_range(equation, defined, address, ctx, found):
    """The range obligation of a line whose right side is an `argmax`
    (AMD-SG-017 §5.4).

    The value of an `argmax` is a point of its binder's set, so the obligation
    compares the binder's set with the declared set of the control in the same
    position of the statement's left side, and not the objective's range with
    it. A bound variable written bare ranges over the control's own set and
    records nothing; a binder that lists several variables is read variable by
    variable; and a declared correspondence used there is read from its
    retained body, with only sound outer enclosures discharged."""
    for position, sub in enumerate(argmax_of(equation.rhs).subs):
        if not isinstance(sub, T.In) or position >= len(defined):
            continue
        declared = ctx.sets.get(defined[position])
        inner_set = binder_value_set(sub.set, ctx)
        if declared is None or set_lies_within(inner_set, declared, ctx):
            continue
        name, inner, outer = defined[position].field, to_source(inner_set), to_source(declared)
        _record(
            found,
            "range-compatibility",
            (piece_identity(address), inner_set, declared),
            f"{name} is declared in {outer} while the argmax binds {sub.var} in {inner}, "
            f"so the construction assumes every value the line {address} writes lies in {outer}",
        )


def check_calibrated_distributions(stage, values):
    """The distribution conditions the parameter values decide (AMD-SG-009 §4),
    checked when values are bound: every family condition of
    `distributions.check_family_conditions`, and, for each expectation of a
    backward value builder whose selected conditional inverts a covariance
    block of a joint normal declaration, that the block is positive definite. A
    violation is refused under `distribution-domain` or
    `conditional-not-declared`."""
    plan = stage_blocks_of(stage)
    bound = {
        name: value
        for name, value in dict(values).items()
        if (isinstance(value, (int, float)) and not isinstance(value, bool))
        or isinstance(value, (list, tuple, Mapping))
    }

    def refuse_at(address):
        def refuse(rule, _, message, write=None):
            raise ConstructionError(
                f"with the calibration values, {message}",
                stage=stage.name,
                address=address,
                rule=rule,
                write=write,
            )

        return refuse

    for owner in plan.owners:
        indexed, dimension = subject_dimension(plan.ctx, owner, bound)
        check_family_conditions(
            owner, bound, refuse_at(owner.address), indexed=indexed, dimension=dimension
        )
    for box in plan.blocks:
        if plan.directions[box.name] != "backward":
            continue
        for row in block_rows_of(plan, box, []).sub_builder:
            selection = conditional_distribution_of(stage, row, plan)
            if selection is not None:
                check_conditioning_covariance(
                    selection, bound, row.identity, refuse_at(row.statements[0])
                )


def conditional_distribution_of(stage, row, plan=None):
    """The conditional distribution an expectation row of a backward value
    builder selects (AMD-SG-009 §5), rebuilt from the shocks the row integrates
    and conditions on and the edge's joint distribution; None for an
    expectation of the policy builder, whose row records no conditioning."""
    if row.kind != "Expectation" or row.given is None:
        return None
    plan = stage_blocks_of(stage) if plan is None else plan
    edge = _edge_drawing(plan, row.integrated)
    if edge is None:
        owners = plan.distributions_of(row.integrated)
        edge = JointDistribution(
            block=None,
            base=(),
            shocks=tuple(s for owner in owners for s in owner.subjects),
            declarations=owners,
        )

    def refuse(rule, address, message, write=None):
        raise ConstructionError(
            message, stage=stage.name, address=address, rule=rule, write=write
        )

    return select_conditional(edge, row.integrated, row.given, row.identity, refuse)


def numerical_law(stage, *, builder, integrated=None, given=(), inputs=None, plan=None):
    """The derived joint law of an edge or conditional law of an expectation.

    The caller has checked any supplied continuation values. The returned
    record owns its specialized terms and does not change the stage.
    """
    from bellman.stage.input_requirements import continuation_inputs, supplied_constants

    plan = stage_blocks_of(stage) if plan is None else plan
    edge = plan.edges.get(builder) if integrated is None else _edge_drawing(plan, integrated)
    if edge is None:
        if integrated is None:
            return None
        owners = plan.distributions_of(integrated)
        edge = JointDistribution(
            block=None,
            base=(),
            shocks=tuple(shock for owner in owners for shock in owner.subjects),
            declarations=owners,
        )

    def refuse(rule, address, message, write=None):
        raise ConstructionError(
            message, stage=stage.name, address=address, rule=rule, write=write
        )

    calibration = stage.bindings.calibration
    values = {} if calibration is None else {**calibration, **derived_values(stage, calibration)}
    constants = supplied_constants(stage, inputs)
    declarations = []
    for owner in edge.declarations:
        missing = tuple(field for field in owner.actuals if field not in constants)
        requirement = None
        if owner.formals and not owner.actuals:
            requirement = (
                f"the arguments {', '.join(owner.formals)}. "
                "Supply them as constant fields on its forward edge."
            )
        elif missing:
            names = {sort.identity: name for name, sort in continuation_inputs(stage).items()}
            fields = ", ".join(names.get(field, field.field) for field in missing)
            requirement = f"continuation fields {fields}."
        if requirement is not None:
            return Refusal(
                f"The distribution of {', '.join(owner.subjects)} at {builder} "
                f"requires {requirement}",
                {
                    "stage": stage.name,
                    "address": builder,
                    "rule": "law-requirement",
                    "file": source_file(stage),
                },
            )
        bound = {
            formal: constants[field]
            for formal, field in zip(owner.formals, owner.actuals)
        }
        domains = {
            formal: plan.ctx.declared_set(field)
            for formal, field in zip(owner.formals, owner.actuals)
        }
        indexed, dimension = subject_dimension(plan.ctx, owner, values)
        declarations.append(
            specialize_distribution(
                owner,
                {**values, **bound},
                indexed=indexed,
                dimension=dimension,
                domains={**plan.ctx.parameter_sets, **domains},
                set_terms=plan.ctx.set_terms,
                functions=plan.ctx.functions,
            )
        )
    edge = dataclasses.replace(edge, declarations=tuple(declarations))
    if integrated is None:
        return edge
    if given is None:
        given = conditioning_shocks(edge, integrated, (), ())
    occurrence = piece_identity(builder)
    selection = select_conditional(edge, integrated, given, occurrence, refuse)
    check_conditioning_covariance(selection, {}, occurrence, refuse)
    return selection


def distribution_formal_fields(stage, definition):
    """A law's local arguments and the fields supplied on its edge."""
    declaration = definition.equations[0]
    if not isinstance(declaration, T.ParameterizedLaw):
        return ()

    def read():
        owner = next(
            owner for owner in stage_blocks_of(stage).owners if owner.identity == definition.identity
        )
        fields = owner.actuals or tuple(
            Identity("function-parameter", owner=definition.identity, occurrence=i, field=name)
            for i, name in enumerate(declaration.arguments)
        )
        return tuple(zip(declaration.arguments, fields, strict=True))

    return kept_answer(
        stage,
        ("distribution formal fields", definition.identity),
        read,
    )


def edge_drawing(stage, shocks):
    """The forward block whose edge draws every shock of `shocks`, or None
    where no one edge draws them all: the edge an expectation's kernel line
    names, read by the one rule by which the conditional an expectation
    selects is read."""
    edge = _edge_drawing(stage_blocks_of(stage), shocks)
    return None if edge is None else edge.block


def _edge_drawing(plan, shocks):
    """The joint distribution of the edge that draws every shock of `shocks`,
    the edge of the forward builder each is assigned to (AMD-SG-009 §2), or
    None where no one edge draws them all."""
    return next((edge for edge in plan.edges.values() if set(shocks) <= set(edge.shocks)), None)


def parameters_named(stage, rows):
    """The parameters the retained terms of operator rows name, directly or
    through the functions they call, in order of first appearance."""
    functions = {
        d.identity.field: d
        for d in stage.definitions.values()
        if d.kind in ("function", "function_alias", "correspondence")
    }
    return _parameters_used(
        tuple(term for row in rows for term in _applied_terms(stage, row)),
        StageNames(stage),
        functions,
    )


def _parameters_used(terms, ctx, functions):
    """The parameters the terms name, through the definitions of the
    functions they call (`𝑢(c)` names ρ through `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)`)
    and of the derived parameters they read (`h` names Γ and R through
    `h := 1/(1 - Γ/R)`), in order of first appearance."""
    found, seen = [], set()
    pending = list(terms)
    while pending:
        term = pending.pop(0)
        for name, side in symbol_occurrences(term):
            if side is None and name in ctx.parameter_names and name not in found:
                found.append(name)
            elif side is None and name in ctx.derived and name not in seen:
                seen.add(name)
                pending.extend(ctx.derived[name].equations)
        for node in term_nodes(term):
            if isinstance(node, T.Call) and node.fun in functions and node.fun not in seen:
                seen.add(node.fun)
                pending.extend(functions[node.fun].equations)
            elif isinstance(node, T.Select) and isinstance(node.sel, (T.Key, T.Term)):
                # a selection from a collection reads the parameters its
                # index sets name, the bounds of a range and the members of
                # a listed set, which decide the entry the key selects
                pending.extend(index_set_terms(ctx, node))
    return tuple(found)


def index_set_terms(ctx, select):
    """The retained terms the index sets of a selected collection read
    numbers from: the bounds of each range and the members of each listed set
    among the factors of its domain, through the stage's named sets; none for
    a selection from a product or a tuple."""
    family = select.family
    while isinstance(family, T.Select):
        family = family.family
    if not (isinstance(family, T.Sym) and isinstance(family.symbol, T.Constant)):
        return ()
    name = family.symbol.name
    if isinstance(name, Identity):
        # a table that a constant field holds is read through its wire
        identity = Identity("field", stage=name.stage, perch=name.perch, field=name.field)
    else:
        identity = (
            Identity("parameter", stage=ctx.stage_name, field=name)
            if name in ctx.parameter_names
            else ctx.resolve(name, None)
        )
    indexed = sets.index_factors(ctx.declared_set(identity), ctx.set_terms)
    if indexed is None:
        return ()
    terms = []
    for factor in indexed[0]:
        resolved = sets.defined(factor, ctx.set_terms)
        if isinstance(resolved, T.IntegerRange):
            terms.extend((resolved.lower, resolved.upper))
        elif isinstance(resolved, T.Points):
            terms.extend(resolved.members)
    return tuple(terms)


def _applied_terms(stage, row):
    """The retained terms an operator row applies: the lines of the g it
    substitutes or pushes forward, otherwise its authored equations and its
    maps, and for an expectation or an extension the declarations of the
    distributions it reads."""
    table = stage.definitions
    if row.kind in ("Pullback", "Pushforward"):
        terms = [table[address].equations[0] for address in table[row.definition].equations]
    else:
        terms = list(row.equations) + list(row.maps)
    if row.kind in ("Expectation", "DistributionExtension"):
        terms.extend(
            table[reference].equations[0].law
            for reference in row.references
            if reference in table and table[reference].kind == "distribution"
        )
    return tuple(terms)
