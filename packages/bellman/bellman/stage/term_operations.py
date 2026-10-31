"""The named operations on terms (AMD-SG-034 §2 item 0a; AMD-SG-035 §3): the
total operations of which the defining expressions of a stage are composed,
each reading retained terms and no stage.

`apply_at` applies a function at a point and reduces the application;
`compose` composes two maps held by reference; `restrict` restricts a domain
by conditions in one comprehension; `residual` is the residual of a relation,
`slack` the slack of a bound, and `kuhn_tucker` the Kuhn–Tucker system of a
relation and its bound. `reduced` takes the written projections of a term and
beta-reduces its applications; `reference_term`, `tuple_term` and `component`
are the reference to an identity, a tuple of one term or more, and one
component of a point.
"""

from __future__ import annotations

import dataclasses

from bellman.native import predicates as P
from bellman.native.identity import Identity
from bellman.native.predicates import And, Compare
from bellman.native.records import ResolvedName
from bellman.syntax import terms as T
from bellman.typing import typed_expressions as S

# --- the operations ---


def apply_at(function, point):
    """The function at the point, reduced: an application of a Lambda is
    beta-reduced, a projection of a written tuple is taken, and a composition
    applied at a point reads the outer map at the inner map's value."""
    return reduced(S.Apply(function, (point,)), beta=True)


def compose(outer, inner, outputs):
    """The composition `outer ∘ inner` of two maps held by reference, with the
    coordinates the inner map writes, one binding each (§4 item 6)."""
    return S.Compose(outer, inner, tuple(outputs))


def restrict(coordinates, domain, conditions):
    """The domain of the coordinates restricted by the conditions, as one
    comprehension: a domain already written as a comprehension over the same
    coordinates gains the conditions it lacks, and no comprehension is nested
    in another (AMD-SG-034 §4 item 8, the named operation "restrict a
    domain")."""
    conditions = tuple(conditions)
    if not conditions:
        return domain
    bound = T.Tuple(tuple(T.Sym(T.Constant(i)) for i in coordinates))
    if isinstance(domain, T.Comprehension) and domain.bound == bound:
        added = tuple(condition for condition in conditions if condition not in domain.conds)
        return dataclasses.replace(domain, conds=tuple(domain.conds) + added)
    return T.Comprehension(bound, domain, conditions)


def relation_of(core):
    """The relation a line states without its clause: the core of a
    statement written with a clause, `𝑑𝑢(c) ≥ 𝑑𝑉≻(a) ⟂ a ≥ 0`, and any other
    statement as it is."""
    return core.core if isinstance(core, T.Slack) else core


def residual(core):
    """The residual of a relation, its left side less its right side, for an
    equation, an inequality, a clause statement or a relation read at a point
    (AMD-SG-035 §3)."""
    relation = relation_of(core)
    if isinstance(relation, Compare):
        return T.Sub(relation.left, relation.right)
    return T.Sub(relation.lhs, relation.rhs)


def slack(bound):
    """The slack of a bound (AMD-SG-035 §3): `x − b` of `x ≥ b`, `b − x` of
    `x ≤ b`, the pair `(x − lb, ub − x)` of `lb ≤ x ≤ ub`; a difference with
    the number zero is the other term, so the slack of `a ≥ 0` is `a`."""

    def difference(left, right):
        return left if right == T.Number(0) else T.Sub(left, right)

    if isinstance(bound, T.Between):
        return difference(bound.middle, bound.lower), difference(bound.upper, bound.middle)
    if isinstance(bound.op, (T.Ge, T.Gt)):
        return difference(bound.left, bound.right)
    return difference(bound.right, bound.left)


SIGN = {T.Ge: ">=", T.Gt: ">", T.Le: "<=", T.Lt: "<", T.Eq: "="}


def kuhn_tucker(core, bound):
    """The Kuhn–Tucker system of a relation and its bound (AMD-SG-035 §2
    "Signs", §3): `r ≥ 0 ∧ s ≥ 0 ∧ r · s = 0` for `≥`, `r ≤ 0 ∧ …` for `≤`,
    `s_lo ≥ 0 ∧ s_hi ≥ 0 ∧ r · s_lo ≤ 0 ∧ r · s_hi ≥ 0` for two bounds; an
    inequality core gives `r` its own sign. The conjunction is nested
    on the left, so that it prints without parentheses. A query; no
    card prints it."""
    relation = relation_of(core)
    r, zero = residual(relation), T.Number(0)
    if isinstance(bound, T.Between):
        low, high = slack(bound)
        return And(
            And(
                And(Compare(low, ">=", zero), Compare(high, ">=", zero)),
                Compare(T.Mul(r, low), "<=", zero),
            ),
            Compare(T.Mul(r, high), ">=", zero),
        )
    s = slack(bound)
    if isinstance(relation, T.Inequality):
        sign = SIGN[type(relation.op)]
    elif isinstance(relation, Compare) and relation.relation != "=":
        sign = relation.relation
    else:
        sign = ">=" if isinstance(bound.op, (T.Ge, T.Gt)) else "<="
    return And(
        And(Compare(r, sign, zero), Compare(s, ">=", zero)), Compare(T.Mul(r, s), "=", zero)
    )


# --- the reduction of a term ---


def reduced(expression, *, beta=False):
    """A term with its generated projections reduced and, in a typed
    producer context, its calls."""
    if isinstance(expression, (Identity, ResolvedName, str, bytes, int, float, bool, type(None))):
        return expression
    if isinstance(expression, tuple):
        return tuple(reduced(item, beta=beta) for item in expression)
    if isinstance(expression, frozenset):
        return frozenset(reduced(item, beta=beta) for item in expression)
    if not dataclasses.is_dataclass(expression) or isinstance(expression, type):
        return expression

    rewritten = dataclasses.replace(
        expression,
        **{
            field.name: reduced(getattr(expression, field.name), beta=beta)
            for field in dataclasses.fields(expression)
        },
    )
    if isinstance(rewritten, S.Apply) and isinstance(rewritten.function, S.Compose):
        # a composition at a point reads the outer map at the inner map's
        # value, `𝑐≻(𝑔≻(m, z_d, c, h_choice))`, for any number of coordinates
        # the inner map writes, since the outer map takes the tuple the
        # inner one returns; the names of those coordinates stand once, on
        # the rule under `where` (AMD-SG-034 §4 item 6)
        composed = rewritten.function
        inner = reduced(S.Apply(composed.inner, rewritten.args), beta=beta)
        return reduced(S.Apply(composed.outer, (inner,)), beta=beta)
    if beta and isinstance(rewritten, S.Apply) and isinstance(rewritten.function, S.Lambda):
        bindings = rewritten.function.bindings
        arguments = _spread(rewritten.args, len(bindings))
        if arguments is not None:
            replacements = {
                variable.identity: argument for (variable, _), argument in zip(bindings, arguments)
            }
            return reduced(S.substitute(rewritten.function.body, replacements), beta=True)
    if (
        isinstance(rewritten, T.Select)
        and isinstance(rewritten.family, T.Tuple)
        and isinstance(rewritten.sel, T.Pos)
        and isinstance(rewritten.sel.at, int)
        and 1 <= rewritten.sel.at <= len(rewritten.family.items)
    ):
        return reduced(rewritten.family.items[rewritten.sel.at - 1], beta=beta)
    if (
        isinstance(rewritten, P.Compare)
        and rewritten.relation == "="
        and _is_number(rewritten.right, 1)
    ):
        predicate = _truth_predicate(rewritten.left)
        if predicate is not None:
            return predicate
    return rewritten


def _spread(arguments, count):
    """The arguments of an application matched to the function's bindings: as
    given where their numbers agree, and otherwise with a tuple argument
    replaced by its components, the last such tuple whose components do not
    exceed the count first, again, until the numbers agree, so that a
    function bound one variable per coordinate is applied to a point written
    as one tuple (AMD-SG-034 §4 item 2), while a tuple a single binding takes
    whole, the value inputs of an aggregator, stays whole. None where the
    numbers never agree."""
    arguments = tuple(arguments)
    while len(arguments) < count:
        fitting = [
            n
            for n, argument in enumerate(arguments)
            if isinstance(argument, T.Tuple) and len(arguments) - 1 + len(argument.items) <= count
        ]
        if not fitting:
            return None
        n = fitting[-1]
        arguments = arguments[:n] + tuple(arguments[n].items) + arguments[n + 1 :]
    return arguments if len(arguments) == count else None


def _truth_predicate(value):
    """The predicate encoded by the exact two-point truth-value supremum."""
    if not isinstance(value, S.Sup):
        return None
    variable, domain = value.binding
    if not _is_reference(value.body, variable.identity):
        return None
    if not isinstance(domain, T.Comprehension) or len(domain.conds) != 1:
        return None
    if not isinstance(domain.base, T.FiniteSet) or domain.base.members != (
        T.Number(0),
        T.Number(1),
    ):
        return None
    condition = domain.conds[0]
    if not isinstance(condition, P.Or):
        return None
    true_case, false_case = condition.left, condition.right
    if not isinstance(true_case, P.And) or not isinstance(false_case, P.And):
        return None
    equals_one, predicate = true_case.left, true_case.right
    equals_zero, negated = false_case.left, false_case.right
    if not (
        isinstance(equals_one, P.Compare)
        and equals_one.relation == "="
        and _is_reference(equals_one.left, variable.identity)
        and _is_number(equals_one.right, 1)
    ):
        return None
    if not (
        isinstance(equals_zero, P.Compare)
        and equals_zero.relation == "="
        and _is_reference(equals_zero.left, variable.identity)
        and _is_number(equals_zero.right, 0)
    ):
        return None
    if not isinstance(negated, P.Not) or negated.operand != predicate:
        return None
    return predicate


def _is_reference(value, identity):
    return (
        isinstance(value, T.Sym)
        and isinstance(value.symbol, T.Constant)
        and value.symbol.name == identity
    )


def _is_number(value, number):
    return isinstance(value, T.Number) and value.value == number


# --- a reference, a tuple and a component ---


def reference_term(identity):
    return T.Sym(T.Constant(identity))


def tuple_term(items):
    items = tuple(items)
    return items[0] if len(items) == 1 else T.Tuple(items)


def component(point, position, count):
    """The term of coordinate `position`, counted from zero, of `point`, a
    term with `count` coordinates: `point` itself when `count` is one, and
    otherwise its selection at the one-based position `position + 1`."""
    return point if count == 1 else T.Select(point, T.Pos(position + 1))
