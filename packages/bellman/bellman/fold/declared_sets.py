"""The declared sets of a field at the sites that produce and consume it, and
the definedness of a node (AMD-SG-017 §4): the set a term takes its values in,
read from the sets its names declare and enclosed for arithmetic through the
interval algebra of `typing.ranges`; the check that a field produced by one
block and consumed by another is declared on one set; the range an `argmax`
binder ranges over; and the condition under which a node is defined, decided
from the sets where they decide it and left as an obligation otherwise.
"""

from __future__ import annotations

import dataclasses
import functools
import math

from bellman.fold.wire_terms import term_nodes
from bellman.native.identity import Identity, piece_identity
from bellman.native.predicates import And, Compare, IsInteger, Member, Not, Or
from bellman.native.records import ArithmeticHead
from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.typing import sets
from bellman.typing.line_unknowns import CALL_OPERATORS
from bellman.typing.ranges import arithmetic_range, convex_hull

# --- the declared sets of a field at its sites ---


def check_declared_sets(stage, obligations, selected=frozenset()):
    """A field produced on one declared set and consumed on another: the
    inclusion holds, or the control's feasible set (the binder of the
    `argmax` of the line marked `!doc` that selects it, `selected`) is
    recorded as the inclusion to establish, or the stage is refused (rule
    set-mismatch). The sets are the retained terms the sites carry, and an
    obligation records each of them as it is written, with the inclusion as
    a term (AMD-SG-034 §10 item 5)."""
    spaces = dict(stage.data.get("spaces", {}))
    for identity, (perch, role, meet, sites) in dict(stage.data.get("fields", {})).items():
        producers = [
            (block, term) for block, side, term in sites if side == "output" and term is not None
        ]
        consumers = [
            (block, term) for block, side, term in sites if side == "input" and term is not None
        ]
        for pblock, produced_term in producers:
            for cblock, consumed_term in consumers:
                relation = sets.within(produced_term, consumed_term, spaces)
                if relation is True:
                    continue
                produced, consumed = to_source(produced_term), to_source(consumed_term)
                inclusion = Compare(produced_term, "⊆", consumed_term)
                if role == "control" and identity in selected:
                    # the feasible set of the selection is the inclusion to
                    # establish; the sentence that says so is the explanation
                    obligations.append(
                        (
                            "set-inclusion",
                            (identity, produced_term, consumed_term, inclusion),
                            f"The feasible set selected for {identity} "
                            f"must place {produced} within {consumed}.",
                        )
                    )
                    continue
                if relation is None:
                    obligations.append(
                        (
                            "set-inclusion",
                            (identity, produced_term, consumed_term, inclusion),
                            f"The set {produced} of {identity} must lie within {consumed}.",
                        )
                    )
                    continue
                raise ConstructionError(
                    f"the field {identity.field} is produced by {pblock!r} on {produced} and "
                    f"consumed by {cblock!r} on {consumed}, and {produced} does not lie in "
                    f"{consumed}; declare the field with one set in both blocks, or state the "
                    f"control's feasible set in the maximization line",
                    stage=stage.name,
                    address=pblock,
                    rule="set-mismatch",
                    write=(
                        f"Declare {identity.field} with one set in blocks {pblock!r} and "
                        f"{cblock!r}, or state the control's feasible set in the maximization "
                        f"line"
                    ),
                )


REAL = T.Named("ℝ")
# the answer of `_declared_set` for a term that names no declared value, told
# apart from the answer for a value whose declaration names no set
_UNNAMED = object()


def right_side_set(term, ctx, block, local, active=()):
    """The set the values a term writes lie in, as a line's range obligation
    reads it (AMD-SG-006 §5): a number's sign class, a field's or a parameter's
    declared set, the set a coordinate is bound in, a sound enclosure for an
    arithmetic node, the body's set for a call to an authored function, and
    the unknown's set for a `solve`; None where no rule applies.

    This is the reading of a whole right side. The set of an *operand* of an
    arithmetic node is `operand_set`'s, which AMD-SG-017 §4 fixes by its own
    clauses; a line whose right side is an `argmax` has the obligation of §5.4
    and reaches neither."""
    declared = _declared_set(term, ctx, block, local)
    if declared is not _UNNAMED:
        return declared
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div, T.Pow, T.Neg)):
        return _arithmetic_enclosure(term, ctx, block, local, active)
    if isinstance(term, T.Call):
        return _call_set(term, ctx, block, local, active, right_side_set)
    if isinstance(term, T.Operator):
        if term.head == "E" and term.args:
            return _expectation_set(term, ctx, block, local, active) or REAL
        if term.head == "D":
            return REAL
        if term.head == "solve" and term.subs:
            first = term.subs[0]
            if isinstance(first, T.In):
                return first.set
            return ctx.sets.get(ctx.resolve(first.name, block))
        if term.head == "argmax" and term.args:
            return right_side_set(term.args[0], ctx, block, local, active)
    if isinstance(term, T.Select) and isinstance(term.sel, T.Key):
        # one key of a collection on an index set fixed: the entries' set, or
        # the collection on the remaining factors; a selection from a product
        # or a tuple keeps its earlier reading
        family = right_side_set(term.family, ctx, block, local, active)
        indexed = sets.index_sets(family, ctx.set_terms) if family is not None else None
        if indexed is not None:
            return indexed[1]
    return None


POSITIVE_REAL = T.Named("ℝ₊₊")
NONNEGATIVE_REAL = T.Named("ℝ₊")


def _declared_set(term, ctx, block, local, active=()):
    """The set a number or a named value lies in: a number's sign class; the
    declared set of a parameter, a field, a shock, the bound variable of a
    binder or a parameter of a function inside that function's body, which for
    a field is the meet its sort holds and for a bound variable the binder's
    set; for a derived parameter, the reals, since its value at a calibration
    is a finite real number (AMD-MT-003, build contract §5), whatever set its
    definition declares, unless that set may hold an infinity, and then that
    set, as for a parameter declared on it (AMD-GRAM-006); and, for the bare
    name an alias line of the block writes, the set of that line's body
    (AMD-SG-017 §4). A field under a perch mark, `c[>]`, has
    the declared set of its own listing and borrows none, since whether a
    candidate lies in the control's set is what `range-compatibility` records.
    `_UNNAMED` for a term that is neither, which the two readings below answer
    for themselves. `active` holds the aliases whose bodies are being read, so
    that an alias written in terms of itself is read once and has no set."""
    if isinstance(term, T.Number):
        return POSITIVE_REAL if term.value > 0 else NONNEGATIVE_REAL if term.value == 0 else REAL
    if isinstance(term, T.Sym):
        symbol = term.symbol
        if isinstance(symbol, T.Constant) and symbol.name in local:
            return local[symbol.name]
        if isinstance(symbol, T.Constant) and symbol.name in ("inf", "∞"):
            return None
        if isinstance(symbol, T.Constant) and symbol.name in ctx.derived:
            # a derived parameter's value is a finite real number, which the
            # calibration establishes or refuses (AMD-MT-003, build contract
            # §5); the set its definition declares is judged there as well
            # and settles no condition of a line here. Where that set may
            # hold an infinity, the value may be one, and the line is read
            # as it is for a parameter declared on that set
            return ctx.extended_derived_sets.get(symbol.name, REAL)
        if isinstance(symbol, T.Constant) and symbol.name not in active:
            body = ctx.alias_body(symbol.name, block)
            if body is not None:
                return operand_set(body, ctx, block, local, active + (symbol.name,))
        side = (
            symbol.when.side
            if isinstance(symbol, T.Variable) and isinstance(symbol.when, T.At)
            else None
        )
        return ctx.sets.get(ctx.resolve(symbol.name, block, side))
    return _UNNAMED


def operand_set(term, ctx, block, local, active=()):
    """The set of an operand of an arithmetic node, by the clauses of
    AMD-SG-017 §4 and no other; None where those clauses give it none.

    A number, a parameter, a field, a shock, a bound variable and a function's
    parameter have the declared set `_declared_set` answers. An authored
    function application has the real operand range derived from its body
    under its separately retained arithmetic conditions. An expectation has ℝ
    where its integrand's set lies in ℝ, its integrability being the separate
    obligation `expectation-integrability`, and no set otherwise. Arithmetic
    uses a sound enclosure where one is available and otherwise retains the
    established broad real-set reading. An alias has the set of its body, which
    `_declared_set` reads. Any other operand has no set."""
    declared = _declared_set(term, ctx, block, local, active)
    if declared is not _UNNAMED:
        return declared
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Neg, T.Div, T.Pow)):
        # the sound enclosure where the operands' sets give one (`CE ∈ ℝ₊₊`
        # for `E_{Ψ}[V[>]^(1 − γ)]^(1/(1 − γ))`), the broad real reading
        # otherwise
        enclosure = _arithmetic_enclosure(term, ctx, block, local, active)
        if enclosure is not None:
            return enclosure
        operands = [getattr(term, field.name) for field in dataclasses.fields(term)]
        return (
            REAL
            if all(
                _real_valued(operand_set(operand, ctx, block, local, active), ctx)
                for operand in operands
            )
            else None
        )
    if isinstance(term, T.Call):
        return _call_set(term, ctx, block, local, active, operand_set)
    if isinstance(term, T.Operator) and term.head == "E" and term.args:
        hull = _expectation_set(term, ctx, block, local, active)
        if hull is not None:
            return hull
        return (
            REAL
            if _real_valued(operand_set(term.args[0], ctx, block, local, active), ctx)
            else None
        )
    return None


def _call_set(term, ctx, block, local, active, reading):
    """The set of a call, read by `reading` (`right_side_set` or
    `operand_set`): the reals for an operator of `CALL_OPERATORS`, else the
    set of the called function's body with each argument's set bound to its
    coordinate; None for an unknown or recursive call and for a
    correspondence."""
    if term.fun in CALL_OPERATORS:
        return REAL
    definition = ctx.functions.get(term.fun)
    if definition is None or term.fun in active:
        return None
    core = definition.equations[0]
    if isinstance(core, T.FuncDef):
        bound = {
            name: (reading(argument, ctx, block, local, active) or declared_set)
            for (name, declared_set), argument in zip(definition.coordinates, term.args)
        }
        return reading(core.body, ctx, None, bound, active + (term.fun,))
    if isinstance(core, T.CorrDef):
        return None
    return reading(core, ctx, None, {}, active + (term.fun,))


def _arithmetic_enclosure(term, ctx, block, local, active=()):
    """A sound range for supported retained arithmetic, or ``None``."""
    return _arithmetic_node_range(
        term, lambda operand: operand_set(operand, ctx, block, local, active), ctx
    )


def _arithmetic_node_range(node, set_of, ctx):
    """A sound enclosure of one arithmetic node from the sets of its immediate
    operands; a number written in the node stands as itself, the point it is,
    so that `1 − γ` with `γ ∈ (1, ∞)` is enclosed in `(−∞, 0)`."""
    parts = tuple(getattr(node, field.name) for field in dataclasses.fields(node))
    names = tuple(f"operand_{position}" for position in range(len(parts)))
    values = {
        name: _range_set(set_of(part), ctx)
        for name, part in zip(names, parts)
        if not isinstance(part, T.Number)
    }
    operation = type(node)(
        *(
            part if isinstance(part, T.Number) else T.Sym(T.Constant(name))
            for name, part in zip(names, parts)
        )
    )
    return arithmetic_range(operation, values)


def _range_set(setterm, ctx):
    """A set term with the named sets it is defined by expanded, as the
    arithmetic enclosures read it."""
    seen = set()
    while (
        isinstance(setterm, T.Named) and setterm.name in ctx.set_terms and setterm.name not in seen
    ):
        seen.add(setterm.name)
        setterm = ctx.set_terms[setterm.name]
    return setterm


def _expectation_set(term, ctx, block, local, active=()):
    """The set an expectation's values lie in: the closure under convex
    combination of the set the integrand's values lie in, the integrand read
    as a whole right side (`right_side_set`), `ℝ₊₊` for `E_{Ψ}[V[>]^(1 − γ)]`
    with `V[>] : ℝ₊₊`; None where the integrand's set is not read. Its
    integrability is the separate obligation `expectation-integrability`."""
    integrand = right_side_set(term.args[0], ctx, block, local, active)
    return convex_hull(_range_set(integrand, ctx)) if integrand is not None else None


def binder_sets(term, local):
    """The sets the binders of a term's operators range over, over the sets
    already in scope. An expectation binds its shocks, whose sets their
    declarations carry, so its binders are not read here."""
    out = dict(local)
    for node in term_nodes(term):
        if isinstance(node, T.Operator) and node.head != "E":
            for sub in node.subs:
                if isinstance(sub, T.In):
                    out.setdefault(sub.var, sub.set)
    return out


def binder_value_set(setterm, ctx):
    """A sound value-set enclosure for an explicit binder."""
    if isinstance(setterm, T.Call):
        definition = ctx.functions.get(setterm.fun)
        if definition is not None and definition.kind == "correspondence":
            body = definition.equations[0].body
            if isinstance(body, T.Comprehension):
                return body.base
            if isinstance(body, T.Interval) and isinstance(body.bounds, T.Range):
                if sets.endpoints(body) is not None:
                    return body
                lower = _constant(body.bounds.lower)
                upper_domains = {
                    name: _range_set(declared, ctx)
                    for name, declared in ctx.parameter_sets.items()
                    if declared is not None
                }
                upper_domains.update(
                    {
                        name: _range_set(declared, ctx)
                        for name, declared in definition.coordinates
                        if declared is not None
                    }
                )
                upper = arithmetic_range(body.bounds.upper, upper_domains)
                if lower is not None and set_lies_within(upper, REAL, ctx):
                    if lower > 0 or lower == 0 and isinstance(body.bounds.left, T.Open):
                        return POSITIVE_REAL
                    if lower == 0 and isinstance(body.bounds.left, T.Closed):
                        return NONNEGATIVE_REAL
            return body
    return setterm


def argmax_of(term):
    """The `argmax` a term is, and None where it is not one. A line whose right
    side is one has the range obligation of AMD-SG-017 §5.4 and no other."""
    return term if isinstance(term, T.Operator) and term.head == "argmax" else None


def inverted_function(node, functions):
    """The function an `Inv` inverts: the identity of its definition where the
    stage declares one, and the retained term otherwise (AMD-SG-017 §5.1;
    AMD-SG-014 §3)."""
    argument = node.args[0] if node.args else node
    if isinstance(argument, T.Sym) and isinstance(argument.symbol, T.Constant):
        definition = functions.get(argument.symbol.name)
        if definition is not None:
            return definition.identity
    return argument


# --- the definedness of a node (AMD-SG-017 §4) ---


def definedness_condition(node):
    """The condition under which one arithmetic node is defined, where the node
    is undefined for some real values of its operands: a divisor that does not
    vanish, and a power whose base is positive, or zero under a positive
    exponent, or negative under an integer exponent. None for a node defined
    wherever its operands are real, and for a division by a written constant.

    It is the part of `definedness_obligation` that restricts the arguments,
    and a printed view asks for it where a map's domain is at issue
    (AMD-SG-019 §2.4)."""
    kind = type(node).__name__
    if kind == "Div":
        return None if _constant(node.right) == 0 else Not(Compare(node.right, "=", T.Number(0)))
    if kind == "Pow":
        base, exponent, zero = node.base, node.exponent, T.Number(0)
        return Or(
            Compare(base, ">", zero),
            Or(
                And(Compare(base, "=", zero), Compare(exponent, ">", zero)),
                And(Compare(base, "<", zero), IsInteger(exponent)),
            ),
        )
    return None


def definedness_obligation(node, obligations, owner, ctx, set_of):
    """The condition under which one arithmetic node is defined, recorded as an
    obligation only where the declared sets of its operands do not decide it
    (AMD-SG-017 §4).

    A sum, a difference, a product or a negation asks nothing where sound
    arithmetic enclosure decides the operation, and records
    `finite-real-arithmetic` where it does not; its entries are the owner and
    the head, so that two sums of one owner are recorded once. A division asks
    nothing where the set algebra decides that 0 is no member of the
    denominator's set, and otherwise records `arithmetic-definedness` with the
    one clause that the denominator is not zero. A power asks nothing where the
    base's set is contained in ℝ₊₊ and the exponent's in ℝ, and otherwise
    records the clauses the sets leave open. A condition that is not recorded
    is not returned either, so that no card prints under `where` what the
    declarations already settle. Each obligation recorded is appended to
    `obligations`.

    `set_of` answers the set of an operand in the scope the caller reads it
    in, and `None` where the declarations give it none; `ctx` carries the sets
    the stage defines by name, through which the set algebra resolves one."""
    place = owner if isinstance(owner, Identity) else piece_identity(owner)
    kind = type(node).__name__
    if kind in ("Add", "Sub", "Mul"):
        return _finite_operands(node, obligations, place, ctx, set_of)
    if kind == "Neg":
        return _finite_operand(node, obligations, place, ctx, set_of)
    if kind == "Div":
        return _nonzero_divisor(node, obligations, place, ctx, set_of)
    if kind == "Pow":
        return _power_domain(node, obligations, place, ctx, set_of)
    return ()


def _finite_operands(node, obligations, place, ctx, set_of):
    """The definedness of a sum, a difference or a product: nothing where a
    sound enclosure of the node exists or both operands are known real, and
    `finite-real-arithmetic` otherwise."""
    kind = type(node).__name__
    if _arithmetic_node_range(node, set_of, ctx) is not None:
        return ()
    if _real_valued(set_of(node.left), ctx) and _real_valued(set_of(node.right), ctx):
        return ()
    obligations.append(
        (
            "finite-real-arithmetic",
            (place, ArithmeticHead(kind)),
            f"The operands of {kind} at {place} must be finite real numbers.",
        )
    )
    return (And(Member(node.left, REAL), Member(node.right, REAL)),)


def _finite_operand(node, obligations, place, ctx, set_of):
    """The definedness of a negation: nothing for a written infinity, where a
    sound enclosure exists, or where the operand is known real, and
    `finite-real-arithmetic` otherwise."""
    kind = type(node).__name__
    value = _constant(node.operand)
    if value is not None and not math.isfinite(value):
        return ()
    if _arithmetic_node_range(node, set_of, ctx) is not None:
        return ()
    if _real_valued(set_of(node.operand), ctx):
        return ()
    obligations.append(
        (
            "finite-real-arithmetic",
            (place, ArithmeticHead(kind)),
            f"The operand of {kind} at {place} must be a finite real number.",
        )
    )
    return (Member(node.operand, REAL),)


def _nonzero_divisor(node, obligations, place, ctx, set_of):
    """The definedness of a division: a written zero divisor refused, nothing
    where the set algebra decides that 0 is no member of the divisor's set, and
    `arithmetic-definedness` with the one clause that the divisor is not zero
    otherwise."""
    if _constant(node.right) == 0:
        raise ConstructionError(
            f"`{to_source(node)}` divides by zero, which is defined at no point; a divisor "
            f"the file writes as a number is not zero. Write a divisor other than zero",
            stage=ctx.stage_name,
            address=_authored_address(place, ctx),
            rule="divisor-nonzero",
        )
    if _excludes_zero(set_of(node.right), ctx):
        return ()
    condition = definedness_condition(node)
    # the node stands among the entries, so that the piece whose
    # expression holds it is found and the condition spelled there
    obligations.append(
        (
            "arithmetic-definedness",
            (place, condition, node),
            f"The divisor {to_source(node.right)} at {place} must be nonzero.",
        )
    )
    return (condition,)


def _power_domain(node, obligations, place, ctx, set_of):
    """The definedness of a power: nothing where the base's set lies in ℝ₊₊ and
    the exponent's in ℝ, and otherwise `arithmetic-definedness` with the
    clauses the sets leave open."""
    base, exponent = set_of(node.base), set_of(node.exponent)
    clauses = []
    if not set_lies_within(base, POSITIVE_REAL, ctx):
        # the condition reduced by the exponent's range where that range
        # settles integrality: an integer exponent asks nothing of the
        # base, a possibly non-integer one its positivity; an exponent
        # of unknown range the whole restriction
        integral = _integer_exponent(node.exponent, exponent, ctx)
        if integral is None:
            clauses.append(definedness_condition(node))
        elif not integral:
            clauses.append(Compare(node.base, ">", T.Number(0)))
    if not _real_valued(base, ctx):
        clauses.append(Member(node.base, REAL))
    if not _real_valued(exponent, ctx):
        clauses.append(Member(node.exponent, REAL))
    if not clauses:
        return ()
    condition = functools.reduce(And, _one_membership(clauses))
    obligations.append(
        (
            "arithmetic-definedness",
            (place, condition, node),
            f"The power {to_source(node)} at {place} requires real operands and either "
            "a positive base, a zero base with positive exponent, or a negative base "
            "with integer exponent.",
        )
    )
    return (condition,)


def _authored_address(place, ctx):
    """The address of the authored item the place of a condition names, which
    the construction positions: a line's or a block's own address, or, for a
    function or a correspondence, the address of its definition record."""
    if place.address is not None:
        return place.address
    record = ctx.functions.get(place.field)
    return record.address if record is not None else None


def _one_membership(clauses):
    """One membership per subject: the clauses that bound one expression,
    `e > 0` and `e ∈ ℝ`, are one membership in the intersection of their
    sets, `e ∈ ℝ₊₊`. The finiteness is kept inside the interval: `e > 0`
    alone admits +∞ in the extended reals, so neither clause implies the
    other and the intersection is the reduction."""
    reduced = list(clauses)
    for clause in clauses:
        if not (
            isinstance(clause, Compare) and clause.relation == ">" and _constant(clause.right) == 0
        ):
            continue
        real = next(
            (
                held
                for held in reduced
                if isinstance(held, Member) and held.subject == clause.left and held.set == REAL
            ),
            None,
        )
        if real is not None and clause in reduced:
            reduced[reduced.index(clause)] = Member(clause.left, POSITIVE_REAL)
            reduced.remove(real)
    return tuple(reduced)


def _integer_exponent(exponent, setterm, ctx):
    """Whether an exponent is an integer: True for a written integer or a set
    within ℤ, False for a set of reals that holds a non-integer, None where
    the exponent's range is not read."""
    value = _constant(exponent)
    if value is not None and math.isfinite(value):
        return float(value).is_integer()
    if setterm is None:
        return None
    if set_lies_within(setterm, T.Named("ℤ"), ctx):
        return True
    bounds = sets.endpoints(_range_set(setterm, ctx))
    if bounds is None:
        return None
    lower, lower_closed, upper, upper_closed = bounds
    if lower == upper:
        return float(lower).is_integer() if math.isfinite(lower) else None
    return False


def _real_valued(setterm, ctx) -> bool:
    """Whether a term's set is known to lie in ℝ. A term with no set is not."""
    return set_lies_within(setterm, REAL, ctx)


def set_lies_within(setterm, outer, ctx) -> bool:
    """Whether a set term lies in `outer`, each name resolved through the sets
    the stage defines. A set the algebra does not decide does not."""
    return setterm is not None and sets.within(setterm, outer, ctx.set_terms) is True


# the point 0 as a set, so that whether a denominator can vanish is asked of
# the set algebra and of nothing else (AMD-SG-017 §4)
ZERO = T.Interval(T.Range(left=T.Closed(), lower=T.Number(0), upper=T.Number(0), right=T.Closed()))


def _excludes_zero(setterm, ctx) -> bool:
    """Whether the set algebra decides that 0 is no member of a set: the point
    0, written as the degenerate closed interval, does not lie in it."""
    return setterm is not None and sets.within(ZERO, setterm, ctx.set_terms) is False


def _constant(node):
    """The number a term writes, a written infinity included; None for any
    other term."""
    if isinstance(node, T.Number):
        return node.value
    if isinstance(node, T.Neg):
        value = _constant(node.operand)
        return None if value is None else -value
    if (
        isinstance(node, T.Sym)
        and isinstance(node.symbol, T.Constant)
        and node.symbol.name in ("inf", "∞")
    ):
        return math.inf
    return None


# --- the dimension of a distribution's subject ---


def subject_dimension(ctx, owner, values):
    """Whether the one subject of a distribution declaration is a collection
    on an index set, and the number of its components at the values: the
    product of the counts of the index sets for a collection, the count of
    the members for a subject declared on a finite set, None where the count
    is not decided or the declaration has several subjects. `ctx` is the
    `StageNames` of the stage."""
    if len(owner.subjects) != 1:
        return False, None
    identity = Identity("field", stage=ctx.stage_name, perch="shck", field=owner.subjects[0])
    declared = ctx.declared_set(identity)
    if declared is None:
        return False, None
    indexed = sets.index_factors(declared, ctx.set_terms)
    if indexed is not None:
        factors, _ = indexed
        counts = [sets.finite_count(factor, values, ctx.set_terms) for factor in factors]
        return True, (None if any(count is None for count in counts) else math.prod(counts))
    return False, sets.finite_count(declared, values, ctx.set_terms)
