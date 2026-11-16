"""The set that holds every value an arithmetic term can take, from the
declared sets of the names it reads: an interval whose endpoints are rounded
outward, so that it holds the exact values.

Beside the ranges, three operations on terms of the same kind as the
Kuhn–Tucker system of `stage/term_operations.py`: `clause_regions`, the
regions of a clause, its Kuhn–Tucker condition written case by case on the
slacks; `law_solved_for`, the law of motion solved for one decision
coordinate at the candidates of the controls; and `compare_terms`, two terms
compared by algebraic simplification with every function read as an opaque
symbol. The construction reads the last two to check a grid line against the
law of motion (the rule `grid-line-consistency`).

The functions in this module inspect terms and declared sets only. They do
not read calibration values and do not assert that a restricted domain is
nonempty.
"""

from __future__ import annotations

import dataclasses
import math
from fractions import Fraction
from numbers import Real
from typing import NamedTuple

from bellman.native.predicates import And, Compare, Or
from bellman.syntax import terms as T
from bellman.syntax.vocabulary import EXTENDED_REAL
from bellman.typing import sets
from bellman.typing.sets import Bounds, set_of_bounds

_INF = math.inf


def arithmetic_range(term, declared_sets):
    """The set that holds every value of an arithmetic term, or None where the
    term is not one the rules read.

    `declared_sets` maps every resolved identifier in `term` to its declared
    set. The rules read numbers, symbols, addition, subtraction,
    multiplication, division, powers and negation.
    """
    bounds = _arithmetic_bounds(term, declared_sets)
    return None if bounds is None else set_of_bounds(bounds)


def convex_hull(setterm):
    """The closure of a set of extended reals under convex combination, as a
    set term: the interval between the set's bounds, each end included where
    the set includes it, `ℝ₊₊` for `ℝ₊₊`, `[0, 1]` for `{0, 1}`; None where
    the set's bounds are not read. It is the range of an expectation of a
    function with values in the set."""
    if isinstance(setterm, T.FiniteSet) and setterm.members:
        values = tuple(
            _number(member.value) if isinstance(member, T.Number) else None
            for member in setterm.members
        )
        if any(value is None for value in values):
            return None
        return set_of_bounds(
            Bounds(lower=min(values), lower_closed=True, upper=max(values), upper_closed=True)
        )
    bounds = _bounds_of_set(setterm)
    return None if bounds is None else set_of_bounds(bounds)


def range_within(term, target, declared_sets, restrictions=()):
    """Whether every feasible value of `term` lies in `target`: `(True,
    evidence)` where an enclosing interval shows it, the evidence naming each
    endpoint substitution used and then the interval, and `(None, ())`
    otherwise; never False.

    `declared_sets` maps resolved identifiers to declared sets. Each
    restriction is `(control identifier, expanded correspondence set)` in
    declaration order. Endpoint substitutions are made in reverse order, so a
    later control may depend on an earlier one.
    """
    direct = arithmetic_range(term, declared_sets)
    if direct is not None and sets.within(direct, target, {}) is True:
        return True, (("range", direct),)

    enclosure, substitutions = _restricted_range(term, declared_sets, restrictions)
    if enclosure is not None and sets.within(enclosure, target, {}) is True:
        evidence = tuple(
            ("endpoint-substitution", control, domain) for control, domain in substitutions
        )
        return True, evidence + (("range", enclosure),)
    return None, ()


def _arithmetic_bounds(term, declared_sets):
    if isinstance(term, T.Number):
        value = _number(term.value)
        return (
            None
            if value is None
            else Bounds(lower=value, lower_closed=True, upper=value, upper_closed=True)
        )
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        declared = declared_sets.get(term.symbol.name)
        return _bounds_of_set(declared)
    if isinstance(term, T.Neg):
        value = _arithmetic_bounds(term.operand, declared_sets)
        return None if value is None else _negate_bounds(value)
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div, T.Pow)):
        left_term, right_term = (
            (term.base, term.exponent) if isinstance(term, T.Pow) else (term.left, term.right)
        )
        left = _arithmetic_bounds(left_term, declared_sets)
        right = _arithmetic_bounds(right_term, declared_sets)
        if left is None or right is None:
            return None
        if isinstance(term, T.Add):
            return _add_bounds(left, right)
        if isinstance(term, T.Sub):
            return _add_bounds(left, _negate_bounds(right))
        if isinstance(term, T.Mul):
            return _multiply_bounds(left, right)
        if isinstance(term, T.Div):
            reciprocal = _reciprocal_bounds(right)
            return None if reciprocal is None else _multiply_bounds(left, reciprocal)
        return _power_bounds(left, right)
    return None


def _bounds_of_set(setterm):
    if isinstance(setterm, T.Space):
        return _bounds_of_set(setterm.set)
    if isinstance(setterm, T.Comprehension):
        return _bounds_of_set(setterm.base)
    primitive = sets.primitive_of(setterm)
    if primitive is not None and primitive.kind == EXTENDED_REAL:
        return Bounds(
            -_INF, primitive.glyph != "ℝ_{+∞}", _INF, primitive.glyph != "ℝ_{-∞}"
        )
    return sets.endpoints(setterm) if setterm is not None else None


def _number(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _negate_bounds(bounds):
    return Bounds(
        lower=-bounds.upper,
        lower_closed=bounds.upper_closed,
        upper=-bounds.lower,
        upper_closed=bounds.lower_closed,
    )


def _add_bounds(left, right):
    if _negative_extended(left) and _finite_real(right):
        return left
    if _negative_extended(right) and _finite_real(left):
        return right
    if (_includes_positive_infinity(left) and _includes_negative_infinity(right)) or (
        _includes_negative_infinity(left) and _includes_positive_infinity(right)
    ):
        return None
    for bounds in (left, right):
        if _singleton(bounds) and _includes_infinity(bounds):
            return bounds
    lower = _rounded_outward(left.lower, right.lower, "add", lower=True)
    upper = _rounded_outward(left.upper, right.upper, "add", lower=False)
    if lower is None or upper is None:
        return None
    lower_closed = (
        (
            lower.value == -_INF
            and (_includes_negative_infinity(left) or _includes_negative_infinity(right))
        )
        or left.lower_closed
        and right.lower_closed
        and lower.exact
    )
    upper_closed = (
        (
            upper.value == _INF
            and (_includes_positive_infinity(left) or _includes_positive_infinity(right))
        )
        or left.upper_closed
        and right.upper_closed
        and upper.exact
    )
    return Bounds(
        lower=lower.value, lower_closed=lower_closed, upper=upper.value, upper_closed=upper_closed
    )


def _negative_extended(bounds):
    return bounds == (-_INF, True, _INF, False)


def _finite_real(bounds):
    return not (
        (bounds.lower == -_INF and bounds.lower_closed)
        or (bounds.upper == _INF and bounds.upper_closed)
    )


def _multiply_bounds(left, right):
    if (_contains_zero(left) and _includes_infinity(right)) or (
        _contains_zero(right) and _includes_infinity(left)
    ):
        return None
    if _negative_extended(left) and _strict_positive(right):
        return left
    if _negative_extended(right) and _strict_positive(left):
        return right
    if _singleton_zero(left) or _singleton_zero(right):
        return Bounds(lower=0, lower_closed=True, upper=0, upper_closed=True)
    if _nonnegative(left) and _nonnegative(right):
        return _multiply_nonnegative(left, right)
    if _nonpositive(left) and _nonpositive(right):
        return _multiply_nonnegative(_negate_bounds(left), _negate_bounds(right))
    if _nonnegative(left) and _nonpositive(right):
        product = _multiply_nonnegative(left, _negate_bounds(right))
        return None if product is None else _negate_bounds(product)
    if _nonpositive(left) and _nonnegative(right):
        product = _multiply_nonnegative(_negate_bounds(left), right)
        return None if product is None else _negate_bounds(product)
    return _finite_product_bounds(left, right)


def _multiply_nonnegative(left, right):
    if left.lower == _INF or right.lower == _INF:
        return Bounds(_INF, True, _INF, True)
    lower, lower_exact = _rounded_outward(left.lower, right.lower, "mul", lower=True)
    lower_closed = left.lower_closed and right.lower_closed and lower_exact
    if lower == 0:
        lower_closed = lower_exact and (
            (left.lower == 0 and left.lower_closed and _has_finite_member(right))
            or (right.lower == 0 and right.lower_closed and _has_finite_member(left))
        )

    if left.upper == _INF or right.upper == _INF:
        upper = _INF
        upper_closed = _includes_positive_infinity(left) or _includes_positive_infinity(right)
    else:
        upper, upper_exact = _rounded_outward(left.upper, right.upper, "mul", lower=False)
        upper_closed = left.upper_closed and right.upper_closed and upper_exact
    return Bounds(lower=lower, lower_closed=lower_closed, upper=upper, upper_closed=upper_closed)


def _finite_product_bounds(left, right):
    if any(math.isinf(value) for value in (left.lower, left.upper, right.lower, right.upper)):
        return None
    endpoints = (
        (left.lower, right.lower, left.lower_closed and right.lower_closed),
        (left.lower, right.upper, left.lower_closed and right.upper_closed),
        (left.upper, right.lower, left.upper_closed and right.lower_closed),
        (left.upper, right.upper, left.upper_closed and right.upper_closed),
    )
    lower_candidates = tuple(
        (*_rounded_outward(a, b, "mul", lower=True), closed) for a, b, closed in endpoints
    )
    upper_candidates = tuple(
        (*_rounded_outward(a, b, "mul", lower=False), closed) for a, b, closed in endpoints
    )
    lower = min(value for value, _exact, _closed in lower_candidates)
    upper = max(value for value, _exact, _closed in upper_candidates)
    lower_closed = any(
        exact and closed for value, exact, closed in lower_candidates if value == lower
    )
    upper_closed = any(
        exact and closed for value, exact, closed in upper_candidates if value == upper
    )
    return Bounds(lower=lower, lower_closed=lower_closed, upper=upper, upper_closed=upper_closed)


def _reciprocal_bounds(bounds):
    if _includes_infinity(bounds):
        return None
    if _strict_negative(bounds):
        positive = _reciprocal_bounds(_negate_bounds(bounds))
        return None if positive is None else _negate_bounds(positive)
    if not _strict_positive(bounds):
        return None
    if bounds.upper == _INF:
        reciprocal_lower, reciprocal_lower_closed = 0, False
    else:
        reciprocal_lower, exact = _rounded_outward(1, bounds.upper, "div", lower=True)
        reciprocal_lower_closed = bounds.upper_closed and exact
    if bounds.lower == 0:
        reciprocal_upper, reciprocal_upper_closed = _INF, False
    else:
        reciprocal_upper, exact = _rounded_outward(1, bounds.lower, "div", lower=False)
        reciprocal_upper_closed = bounds.lower_closed and exact
    return Bounds(
        lower=reciprocal_lower,
        lower_closed=reciprocal_lower_closed,
        upper=reciprocal_upper,
        upper_closed=reciprocal_upper_closed,
    )


def _power_bounds(base, exponent):
    if _includes_infinity(exponent):
        return None
    if _strict_positive(base) and _includes_positive_infinity(base) and _strict_negative(exponent):
        if base.lower == _INF:
            return Bounds(0, True, 0, True)
        return Bounds(0, True, _INF, False)
    if _includes_infinity(base):
        return None
    if _strict_positive(base) and _finite_real(base) and _finite_real(exponent):
        return Bounds(lower=0, lower_closed=False, upper=_INF, upper_closed=False)
    if _singleton(exponent):
        power = exponent.lower
        if isinstance(power, int) and power > 0 and _nonnegative(base):
            lower, lower_exact = _rounded_outward(base.lower, power, "pow", lower=True)
            if base.upper == _INF:
                upper, upper_exact = _INF, False
            else:
                upper, upper_exact = _rounded_outward(base.upper, power, "pow", lower=False)
            return Bounds(
                lower=lower,
                lower_closed=base.lower_closed and lower_exact,
                upper=upper,
                upper_closed=base.upper_closed and upper_exact,
            )
        if _singleton(base) and isinstance(power, int):
            lower = _rounded_outward(base.lower, power, "pow", lower=True)
            upper = _rounded_outward(base.lower, power, "pow", lower=False)
            if lower is None or upper is None:
                return None
            return Bounds(
                lower=lower.value,
                lower_closed=lower.exact,
                upper=upper.value,
                upper_closed=upper.exact,
            )
    return None


class _Rounded(NamedTuple):
    """A floating result rounded outward, and whether it is exact."""

    value: object
    exact: bool


def _rounded_outward(left, right, operation, lower):
    """A floating result rounded outward, and whether it is exact."""
    if (
        isinstance(left, float)
        and math.isinf(left)
        or isinstance(right, float)
        and math.isinf(right)
    ):
        try:
            value = {
                "add": lambda: left + right,
                "mul": lambda: left * right,
                "div": lambda: left / right,
                "pow": lambda: left**right,
            }[operation]()
        except (ArithmeticError, OverflowError, TypeError, ValueError):
            return None
        return None if isinstance(value, float) and math.isnan(value) else _Rounded(value, True)
    try:
        if operation == "add":
            value = left + right
            exact = _fraction(left) + _fraction(right)
        elif operation == "mul":
            value = left * right
            exact = _fraction(left) * _fraction(right)
        elif operation == "div":
            value = left / right
            exact = _fraction(left) / _fraction(right)
        else:
            value = left**right
            exact = _fraction(left) ** right
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return None
    if not isinstance(value, float):
        return _Rounded(value, _fraction(value) == exact)
    if math.isnan(value):
        return None
    represented = None if math.isinf(value) else Fraction.from_float(value)
    if represented == exact:
        return _Rounded(value, True)
    lower_needs_widening = represented is None and value > 0
    lower_needs_widening |= represented is not None and represented > exact
    upper_needs_widening = represented is None and value < 0
    upper_needs_widening |= represented is not None and represented < exact
    if lower and lower_needs_widening:
        value = math.nextafter(value, -_INF)
    if not lower and upper_needs_widening:
        value = math.nextafter(value, _INF)
    return _Rounded(value, False)


def _fraction(value):
    return Fraction.from_float(value) if isinstance(value, float) else Fraction(value)


def _nonnegative(bounds):
    return bounds.lower >= 0


def _strict_positive(bounds):
    return bounds.lower > 0 or bounds.lower == 0 and not bounds.lower_closed


def _nonpositive(bounds):
    return bounds.upper <= 0


def _strict_negative(bounds):
    return bounds.upper < 0 or bounds.upper == 0 and not bounds.upper_closed


def _singleton(bounds):
    return bounds.lower == bounds.upper and bounds.lower_closed and bounds.upper_closed


def _singleton_zero(bounds):
    return _singleton(bounds) and bounds.lower == 0


def _has_finite_member(bounds):
    return not (
        bounds.lower == bounds.upper
        and math.isinf(bounds.lower)
        and bounds.lower_closed
        and bounds.upper_closed
    )


def _contains_zero(bounds):
    left = bounds.lower < 0 or bounds.lower == 0 and bounds.lower_closed
    right = bounds.upper > 0 or bounds.upper == 0 and bounds.upper_closed
    return left and right


def _includes_infinity(bounds):
    return _includes_negative_infinity(bounds) or _includes_positive_infinity(bounds)


def _includes_negative_infinity(bounds):
    return bounds.lower == -_INF and bounds.lower_closed


def _includes_positive_infinity(bounds):
    return bounds.upper == _INF and bounds.upper_closed


def _restricted_range(term, declared_sets, restrictions):
    lower, lower_closed = term, True
    upper, upper_closed = term, True
    used = []
    for control, domain in reversed(tuple(restrictions)):
        endpoints = _restriction_endpoints(domain, control)
        if endpoints is None:
            if _depends(lower, control) or _depends(upper, control):
                return None, ()
            continue
        next_lower = _extreme(lower, control, endpoints, declared_sets, minimum=True)
        next_upper = _extreme(upper, control, endpoints, declared_sets, minimum=False)
        if next_lower is None or next_upper is None:
            return None, ()
        lower, endpoint_closed, lower_used = next_lower
        lower_closed = lower_closed and endpoint_closed
        upper, endpoint_closed, upper_used = next_upper
        upper_closed = upper_closed and endpoint_closed
        if lower_used or upper_used:
            used.append((control, domain))

    lower_bound = _endpoint_bound(lower, declared_sets, lower=True)
    upper_bound = _endpoint_bound(upper, declared_sets, lower=False)
    if lower_bound is None or upper_bound is None:
        return None, ()
    lower_value, lower_attained = lower_bound
    upper_value, upper_attained = upper_bound
    bounds = Bounds(
        lower=lower_value,
        lower_closed=lower_closed and lower_attained,
        upper=upper_value,
        upper_closed=upper_closed and upper_attained,
    )
    if lower_value > upper_value:
        return None, ()
    if lower_value == upper_value and not (bounds.lower_closed and bounds.upper_closed):
        return None, ()
    return set_of_bounds(bounds), tuple(used)


def _endpoint_bound(endpoint, declared_sets, lower):
    if isinstance(endpoint, float) and math.isinf(endpoint):
        return endpoint, False
    value = _arithmetic_bounds(_simplify(endpoint, declared_sets), declared_sets)
    if value is None:
        return None
    return (value.lower, value.lower_closed) if lower else (value.upper, value.upper_closed)


def _extreme(term, control, endpoints, declared_sets, minimum):
    if isinstance(term, float) and math.isinf(term):
        return term, False, False
    affine = _affine(term, control, declared_sets)
    if affine is None:
        return None
    coefficient, remainder = affine
    if _is_zero(coefficient):
        return remainder, True, False
    coefficient_range = _arithmetic_bounds(coefficient, declared_sets)
    if coefficient_range is None:
        return None
    positive = _strict_positive(coefficient_range)
    negative = _strict_negative(coefficient_range)
    if not positive and not negative:
        return None
    lower, lower_closed, upper, upper_closed = endpoints
    choose_lower = minimum == positive
    endpoint = lower if choose_lower else upper
    closed = lower_closed if choose_lower else upper_closed
    if isinstance(endpoint, float) and math.isinf(endpoint):
        value = endpoint if positive else -endpoint
        return value, False, True
    value = _simplify(T.Add(remainder, T.Mul(coefficient, endpoint)), declared_sets)
    return value, closed, True


def _affine(term, control, declared_sets):
    term = _simplify(term, declared_sets)
    if _is_symbol(term, control):
        return T.Number(1), T.Number(0)
    if not _depends(term, control):
        return T.Number(0), term
    if isinstance(term, T.Neg):
        inner = _affine(term.operand, control, declared_sets)
        return (
            None
            if inner is None
            else tuple(_simplify(T.Neg(part), declared_sets) for part in inner)
        )
    if isinstance(term, (T.Add, T.Sub)):
        left = _affine(term.left, control, declared_sets)
        right = _affine(term.right, control, declared_sets)
        if left is None or right is None:
            return None
        operation = T.Add if isinstance(term, T.Add) else T.Sub
        return tuple(_simplify(operation(a, b), declared_sets) for a, b in zip(left, right))
    if isinstance(term, T.Mul):
        left_depends = _depends(term.left, control)
        right_depends = _depends(term.right, control)
        if left_depends and right_depends:
            return None
        dependent, factor = (term.left, term.right) if left_depends else (term.right, term.left)
        affine = _affine(dependent, control, declared_sets)
        if affine is None:
            return None
        return tuple(_simplify(T.Mul(part, factor), declared_sets) for part in affine)
    if isinstance(term, T.Div) and not _depends(term.right, control):
        affine = _affine(term.left, control, declared_sets)
        if affine is None or not _known_nonzero(term.right, declared_sets):
            return None
        return tuple(_simplify(T.Div(part, term.right), declared_sets) for part in affine)
    return None


def _restriction_endpoints(setterm, control):
    if isinstance(setterm, T.Space):
        return _restriction_endpoints(setterm.set, control)
    if isinstance(setterm, T.Interval) and isinstance(setterm.bounds, T.Range):
        bounds = setterm.bounds
        if bounds.left is None or bounds.right is None:
            return None
        return Bounds(
            lower=bounds.lower,
            lower_closed=isinstance(bounds.left, T.Closed),
            upper=bounds.upper,
            upper_closed=isinstance(bounds.right, T.Closed),
        )
    numeric = sets.endpoints(setterm)
    if numeric is not None:
        return Bounds(
            lower=_symbolic_endpoint(numeric.lower),
            lower_closed=numeric.lower_closed,
            upper=_symbolic_endpoint(numeric.upper),
            upper_closed=numeric.upper_closed,
        )
    if not isinstance(setterm, T.Comprehension):
        return None
    endpoints = _restriction_endpoints(setterm.base, control)
    if endpoints is None:
        return None
    accepted = {control, *_bound_identifiers(setterm.bound)}
    for condition in setterm.conds:
        endpoints = _tightened_endpoints(endpoints, condition, accepted)
        if endpoints is None:
            return None
    return endpoints


def _symbolic_endpoint(value):
    return value if math.isinf(value) else T.Number(value)


def _bound_identifiers(bound):
    if isinstance(bound, T.Subject):
        return tuple(
            coordinate.stem
            for coordinate in bound.coordinates
            if isinstance(coordinate, T.Coordinate)
        )
    if isinstance(bound, T.Coordinate):
        return (bound.stem,)
    return ()


def _tightened_endpoints(endpoints, condition, accepted):
    if not isinstance(condition, T.Rel):
        return None
    if _symbol_identifier(condition.left) in accepted:
        operation, value = type(condition.op), condition.right
    elif _symbol_identifier(condition.right) in accepted:
        operation, value = _reverse_relation(type(condition.op)), condition.left
    else:
        return endpoints
    lower, lower_closed, upper, upper_closed = endpoints
    if operation in (T.Gt, T.Ge, T.Eq):
        tightened = _tighten(lower, lower_closed, value, operation in (T.Ge, T.Eq), lower=True)
        if tightened is None:
            return None
        lower, lower_closed = tightened
    if operation in (T.Lt, T.Le, T.Eq):
        tightened = _tighten(upper, upper_closed, value, operation in (T.Le, T.Eq), lower=False)
        if tightened is None:
            return None
        upper, upper_closed = tightened
    return Bounds(lower=lower, lower_closed=lower_closed, upper=upper, upper_closed=upper_closed)


def _reverse_relation(operation):
    return {T.Lt: T.Gt, T.Le: T.Ge, T.Eq: T.Eq, T.Ge: T.Le, T.Gt: T.Lt}[operation]


def _tighten(current, current_closed, candidate, candidate_closed, lower):
    if current == candidate:
        return current, current_closed and candidate_closed
    if isinstance(current, float) and math.isinf(current):
        if lower and current < 0 or not lower and current > 0:
            return candidate, candidate_closed
    current_number = _literal_number(current)
    candidate_number = _literal_number(candidate)
    if current_number is None or candidate_number is None:
        return None
    if lower:
        return (
            (candidate, candidate_closed)
            if candidate_number > current_number
            else (current, current_closed)
        )
    return (
        (candidate, candidate_closed)
        if candidate_number < current_number
        else (current, current_closed)
    )


def _literal_number(term):
    if isinstance(term, (int, float)):
        return term
    if isinstance(term, T.Number):
        return _number(term.value)
    if isinstance(term, T.Neg) and isinstance(term.operand, T.Number):
        value = _number(term.operand.value)
        return None if value is None else -value
    return None


def _symbol_identifier(term):
    return (
        term.symbol.name
        if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant)
        else None
    )


def _is_symbol(term, identifier):
    return _symbol_identifier(term) == identifier


def _depends(term, identifier):
    if _is_symbol(term, identifier):
        return True
    if isinstance(term, tuple):
        return any(_depends(child, identifier) for child in term)
    if dataclasses.is_dataclass(term):
        return any(
            _depends(getattr(term, field.name), identifier) for field in dataclasses.fields(term)
        )
    return False


def _simplify(term, declared_sets):
    if isinstance(term, (T.Number, T.Sym)):
        return term
    if isinstance(term, T.Neg):
        operand = _simplify(term.operand, declared_sets)
        if isinstance(operand, T.Number):
            return T.Number(-operand.value)
        if isinstance(operand, T.Neg):
            return operand.operand
        return T.Neg(operand)
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div)):
        left = _simplify(term.left, declared_sets)
        right = _simplify(term.right, declared_sets)
        if isinstance(term, T.Add):
            if isinstance(left, T.Number) and isinstance(right, T.Number):
                value = _exact_number_result(left.value, right.value, "add")
                if value is not None:
                    return T.Number(value)
            if _is_zero(left):
                return right
            if _is_zero(right):
                return left
            if (
                isinstance(right, T.Neg)
                and _algebraically_equal(left, right.operand)
                and _known_finite(left, declared_sets)
            ):
                return T.Number(0)
            if (
                isinstance(left, T.Neg)
                and _algebraically_equal(left.operand, right)
                and _known_finite(right, declared_sets)
            ):
                return T.Number(0)
            return T.Add(left, right)
        if isinstance(term, T.Sub):
            if isinstance(left, T.Number) and isinstance(right, T.Number):
                value = _exact_number_result(left.value, right.value, "sub")
                if value is not None:
                    return T.Number(value)
            if _is_zero(right):
                return left
            if _algebraically_equal(left, right) and _known_finite(left, declared_sets):
                return T.Number(0)
            return _simplify(T.Add(left, T.Neg(right)), declared_sets)
        if isinstance(term, T.Mul):
            return _simplify_product(left, right, declared_sets)
        if _is_zero(left) and _known_nonzero(right, declared_sets):
            return T.Number(0)
        if _is_one(right):
            return left
        if isinstance(left, T.Number) and isinstance(right, T.Number):
            value = _exact_number_result(left.value, right.value, "div")
            if value is not None:
                return T.Number(value)
        return T.Div(left, right)
    return term


def _simplify_product(left, right, declared_sets):
    if (
        _is_zero(left)
        and _known_finite(right, declared_sets)
        or _is_zero(right)
        and _known_finite(left, declared_sets)
    ):
        return T.Number(0)
    if isinstance(left, T.Number) and isinstance(right, T.Number):
        value = _exact_number_result(left.value, right.value, "mul")
        if value is not None:
            return T.Number(value)
    if _is_one(left):
        return right
    if _is_one(right):
        return left
    if _is_minus_one(left):
        return _simplify(T.Neg(right), declared_sets)
    if _is_minus_one(right):
        return _simplify(T.Neg(left), declared_sets)
    if isinstance(left, T.Neg):
        return _simplify(T.Neg(T.Mul(left.operand, right)), declared_sets)
    if isinstance(right, T.Neg):
        return _simplify(T.Neg(T.Mul(left, right.operand)), declared_sets)
    if isinstance(right, T.Div) and _algebraically_equal(left, right.right):
        if _known_nonzero(left, declared_sets) and _known_finite(left, declared_sets):
            return right.left
    if isinstance(left, T.Div) and _algebraically_equal(right, left.right):
        if _known_nonzero(right, declared_sets) and _known_finite(right, declared_sets):
            return left.left
    return T.Mul(left, right)


def _known_nonzero(term, declared_sets):
    value = _arithmetic_bounds(term, declared_sets)
    return value is not None and (_strict_positive(value) or _strict_negative(value))


def _known_finite(term, declared_sets):
    value = _arithmetic_bounds(term, declared_sets)
    return value is not None and _finite_real(value)


def _exact_number_result(left, right, operation):
    name = "add" if operation == "add" else "add" if operation == "sub" else operation
    operand = -right if operation == "sub" else right
    result = _rounded_outward(left, operand, name, lower=True)
    return result.value if result is not None and result.exact else None


def _is_zero(term):
    return isinstance(term, T.Number) and term.value == 0


def _is_one(term):
    return isinstance(term, T.Number) and term.value == 1


def _is_minus_one(term):
    return isinstance(term, T.Number) and term.value == -1


def _algebraically_equal(left, right):
    if left == right:
        return True
    return (
        isinstance(left, T.Mul)
        and isinstance(right, T.Mul)
        and left.left == right.right
        and left.right == right.left
    )


# --- the regions of a clause ---

# The signs of a real number that a comparison with zero admits: -1 for a
# negative number, 0 for zero and 1 for a positive number.
_ADMITTED_SIGNS = {
    "<": frozenset({-1}),
    "<=": frozenset({-1, 0}),
    "=": frozenset({0}),
    ">=": frozenset({0, 1}),
    ">": frozenset({1}),
}
_EVERY_SIGN = frozenset({-1, 0, 1})


def clause_regions(condition):
    """The regions of a clause `core ⟂ bound`: its Kuhn–Tucker condition,
    `kuhn_tucker(core, bound)` of `stage/term_operations.py`, written as the
    disjunction of its cases on the slacks, and equivalent to it at every
    point.

    The condition is a conjunction of comparisons with zero: the sign of the
    residual `r` where the core gives it one, `s ≥ 0` for each slack `s`, and
    the sign of each product `r · s`. Where a slack is positive its product
    has the sign of `r`; where it is zero its product is zero whatever `r`
    is. The regions are therefore the interior, where every slack is
    positive, and one region at each bound, where its slack is zero and every
    other slack is nonnegative, each admitting the signs of `r` that the
    core's own sign and the products of the other slacks admit together. For
    one bound this is `(s > 0 ∧ r = 0) ∨ (s = 0 ∧ r ⋚ 0)`, `⋚` the sign
    `kuhn_tucker` gives the residual; for the two bounds of a chain,
    `(s_lo > 0 ∧ s_hi > 0 ∧ r = 0) ∨ (s_lo = 0 ∧ s_hi ≥ 0 ∧ r ≥ 0) ∨
    (s_lo ≥ 0 ∧ s_hi = 0 ∧ r ≤ 0)`; where both slacks of a chain are zero the
    condition admits every residual, which the two regions at the bounds
    admit between them.

    A region that admits no sign is no region: a strict core, `r < 0`, admits
    no zero residual and so has no interior. Each region of a chain keeps the
    feasibility of both slacks, since no rule orders the endpoints of a
    chain, so a chain whose endpoints are reversed admits no point under
    either form. The disjunction and each conjunction are nested on the left,
    as `kuhn_tucker` nests its conjunction. A predicate that is not such a
    condition is refused with a `ValueError`."""
    residual, signs, products = _clause_parts(condition)
    own = _EVERY_SIGN
    for relation in signs:
        own = own & _ADMITTED_SIGNS[relation]
    zero = T.Number(0)
    count = len(products)
    # the interior, then the region at each bound, each with the positions of
    # the slacks whose products fix the sign of the residual there
    cases = [([Compare(slack, ">", zero) for slack, _ in products], range(count))]
    for bound in range(count):
        conditions = [
            Compare(slack, "=" if other == bound else ">=", zero)
            for other, (slack, _) in enumerate(products)
        ]
        cases.append((conditions, [other for other in range(count) if other != bound]))
    regions = []
    for conditions, positive in cases:
        admitted = own
        for other in positive:
            admitted = admitted & _ADMITTED_SIGNS[products[other][1]]
        if admitted:
            regions.append(_nested(And, conditions + _residual_sign(residual, admitted)))
    return _nested(Or, regions)


def _clause_parts(condition):
    """The residual, the relations of its own sign, and each slack with the
    relation of its product, read from a Kuhn–Tucker condition: a conjunction
    of comparisons with zero in which each product is the residual times a
    slack that another conjunct states nonnegative, one product for one bound
    and two for a chain."""
    conjuncts = _conjuncts(condition)
    zero = T.Number(0)
    refused = ValueError(f"{condition!r} is no Kuhn–Tucker condition of a clause")
    if not all(
        isinstance(conjunct, Compare)
        and conjunct.right == zero
        and conjunct.relation in _ADMITTED_SIGNS
        for conjunct in conjuncts
    ):
        raise refused
    nonnegative = [conjunct.left for conjunct in conjuncts if conjunct.relation == ">="]
    products = [
        conjunct
        for conjunct in conjuncts
        if isinstance(conjunct.left, T.Mul) and conjunct.left.right in nonnegative
    ]
    if not 1 <= len(products) <= 2:
        raise refused
    residual = products[0].left.left
    if any(product.left.left != residual for product in products):
        raise refused
    slacks = [product.left.right for product in products]
    signs = []
    for conjunct in conjuncts:
        if conjunct in products or (conjunct.relation == ">=" and conjunct.left in slacks):
            continue
        if conjunct.left != residual:
            raise refused
        signs.append(conjunct.relation)
    return (
        residual,
        tuple(signs),
        tuple((product.left.right, product.relation) for product in products),
    )


def _conjuncts(predicate):
    """The conjuncts of a conjunction in order, however it is nested."""
    if isinstance(predicate, And):
        return _conjuncts(predicate.left) + _conjuncts(predicate.right)
    return [predicate]


def _residual_sign(residual, admitted):
    """The comparison of the residual with zero that admits exactly the signs
    `admitted`, as a list of one, or the empty list where every sign is
    admitted. An intersection of the sets `_ADMITTED_SIGNS` holds is itself
    one of them."""
    if admitted == _EVERY_SIGN:
        return []
    (relation,) = [relation for relation, signs in _ADMITTED_SIGNS.items() if signs == admitted]
    return [Compare(residual, relation, T.Number(0))]


def _nested(kind, items):
    """The conjunction (`And`) or the disjunction (`Or`) of one item or more,
    nested on the left."""
    result = items[0]
    for item in items[1:]:
        result = kind(result, item)
    return result


# --- the law of motion solved for a decision coordinate ---

# The functions of the language whose value is positive at every real
# argument: the exponential, whose primitive definition has the output set
# ℝ₊₊ (`typing/primitive_definitions.py`).
_POSITIVE_FUNCTIONS = frozenset({"exp"})


class SolvedLaw(NamedTuple):
    """The law of motion solved for one decision coordinate at the
    candidates of the controls. `term` is the coordinate as a function of the
    outputs of the law of motion, the candidates and the names its lines read
    that are neither decision coordinates nor controls; `lines` holds, for
    each line of the law of motion that was solved, its output and the name
    it was solved for, the coordinate's line first; `candidates` the controls
    read at their candidates, in the order in which they were replaced."""

    term: object
    lines: tuple
    candidates: tuple


def solved_for(output, rhs, name, declared_sets):
    """The explicit line `output = rhs` solved for `name`: `(output − b)/a`,
    where `rhs` is `a·name + b` with `name` occurring in it once, `a` and `b`
    free of it and `a` nonzero on the declared sets. None where `name` occurs
    otherwise, and the line is then not solved for it. `output` is the term
    of the line's left side. A number `a` whose reciprocal is exact is
    written as that factor, `2·output − 2·b` for `a = 1/2`."""
    if _occurrences(rhs, name) != 1:
        return None
    affine = _affine(rhs, name, declared_sets)
    if affine is None:
        return None
    coefficient, remainder = affine
    if not _declared_nonzero(coefficient, declared_sets):
        return None
    if isinstance(coefficient, T.Number):
        reciprocal = _exact_number_result(1, coefficient.value, "div")
        if reciprocal is not None:
            if isinstance(reciprocal, float) and reciprocal.is_integer():
                reciprocal = int(reciprocal)
            factor = T.Number(reciprocal)
            return _simplify(T.Sub(T.Mul(factor, output), T.Mul(factor, remainder)), declared_sets)
    return _simplify(T.Div(T.Sub(output, remainder), coefficient), declared_sets)


def law_solved_for(law, coordinate, unknowns, candidates, declared_sets):
    """The law of motion solved for the decision coordinate `coordinate` at
    the candidates, a `SolvedLaw`, or None where the law of motion is not
    solved so.

    `law` holds the lines of the law of motion as pairs of an output's name
    and the right side of its line, one line for each output, each right side
    reading the decision coordinates, the controls, the shocks and the
    parameters; `unknowns` names the decision coordinates and the controls;
    `candidates` maps each control that has a candidate line to the
    candidate's term, `c ↦ c[>]`. The one line that reads the coordinate is
    solved for it (`solved_for`). In the solution a control with a candidate
    is replaced by the candidate, and any other unknown the solution reads
    is solved for from the one line not yet solved that reads it, so that a
    law of motion with several outputs is solved only where its other lines
    give every such unknown. Where a name occurs in its line other than once
    and affinely, where no line or several read an unknown, and where the
    solution comes to read the coordinate again, the law of motion is not
    solved and None is returned; no hypothesis is stated in its place."""
    lines = tuple(law)
    used, steps, read = set(), [], []

    def solve(name):
        readers = [n for n, (_, rhs) in enumerate(lines) if n not in used and _depends(rhs, name)]
        if len(readers) != 1:
            return None
        output, rhs = lines[readers[0]]
        solution = solved_for(T.Sym(T.Constant(output)), rhs, name, declared_sets)
        if solution is not None:
            used.add(readers[0])
            steps.append((output, name))
        return solution

    term = solve(coordinate)
    while term is not None:
        pending = [name for name in unknowns if _depends(term, name)]
        if not pending:
            return SolvedLaw(_tidy(term), tuple(steps), tuple(read))
        name = pending[0]
        if name == coordinate:
            return None
        if name in candidates:
            replacement = candidates[name]
            if name not in read:
                read.append(name)
        else:
            replacement = solve(name)
        if replacement is None:
            return None
        term = _simplify(substituted(term, {T.Sym(T.Constant(name)): replacement}), declared_sets)
    return None


def substituted(term, replacements):
    """`term` with every subterm that is a key of `replacements` replaced by
    its value; a key is a term, a name being `T.Sym(T.Constant(name))`."""
    try:
        if term in replacements:
            return replacements[term]
    except TypeError:
        pass
    if isinstance(term, tuple):
        return tuple(substituted(item, replacements) for item in term)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return dataclasses.replace(
            term,
            **{
                field.name: substituted(getattr(term, field.name), replacements)
                for field in dataclasses.fields(term)
            },
        )
    return term


def _occurrences(term, identifier):
    """The number of occurrences of the name `identifier` in `term`."""
    if _is_symbol(term, identifier):
        return 1
    if isinstance(term, tuple):
        return sum(_occurrences(item, identifier) for item in term)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return sum(
            _occurrences(getattr(term, field.name), identifier)
            for field in dataclasses.fields(term)
        )
    return 0


def _declared_nonzero(term, declared_sets):
    """Whether the declarations show `term` nonzero: an enclosing interval
    that excludes zero; a product or a negation of nonzero terms; the
    exponential of a real number; or a coordinate of a family declared on a
    product of sets that are all positive or all negative, `R_vec[r_type]`
    with `R_vec` declared on `ℝ₊₊ × ℝ₊₊`."""
    if _known_nonzero(term, declared_sets):
        return True
    if isinstance(term, T.Mul):
        return _declared_nonzero(term.left, declared_sets) and _declared_nonzero(
            term.right, declared_sets
        )
    if isinstance(term, T.Neg):
        return _declared_nonzero(term.operand, declared_sets)
    if isinstance(term, T.Call):
        return isinstance(term.fun, str) and term.fun in _POSITIVE_FUNCTIONS
    if not isinstance(term, T.Select) or _symbol_identifier(term.family) is None:
        return False
    family = declared_sets.get(_symbol_identifier(term.family))
    if isinstance(family, T.Space):
        family = family.set
    factors = family.factors if isinstance(family, T.Product) else ()
    bounds = [_bounds_of_set(factor) for factor in factors]
    if not bounds or any(bound is None for bound in bounds):
        return False
    return all(_strict_positive(bound) for bound in bounds) or all(
        _strict_negative(bound) for bound in bounds
    )


def _tidy(term):
    """`term` with its sums written flat: a negation distributed over a sum,
    a double negation removed and a negative number written as a difference,
    the first positive summand first. `a − (−c − (1 + τ)·h)` is
    `a + c + (1 + τ)·h`. The value is unchanged; it is the form a refusal
    prints."""
    summands = []

    def collect(part, sign):
        if isinstance(part, T.Add):
            collect(part.left, sign)
            collect(part.right, sign)
        elif isinstance(part, T.Sub):
            collect(part.left, sign)
            collect(part.right, -sign)
        elif isinstance(part, T.Neg):
            collect(part.operand, -sign)
        elif _is_zero(part):
            return
        elif isinstance(part, T.Number) and _number(part.value) is not None and part.value < 0:
            summands.append((-sign, T.Number(-part.value)))
        elif isinstance(part, (T.Mul, T.Div)):
            summands.append((sign, type(part)(_tidy(part.left), _tidy(part.right))))
        elif isinstance(part, T.Pow):
            summands.append((sign, T.Pow(_tidy(part.base), _tidy(part.exponent))))
        else:
            summands.append((sign, part))

    collect(term, 1)
    if not summands:
        return T.Number(0)
    first = next((n for n, (sign, _) in enumerate(summands) if sign > 0), 0)
    summands.insert(0, summands.pop(first))
    sign, result = summands[0]
    result = result if sign > 0 else T.Neg(result)
    for sign, part in summands[1:]:
        result = T.Add(result, part) if sign > 0 else T.Sub(result, part)
    return result


# --- two terms compared by algebraic simplification ---

# The largest integer exponent a power is expanded to; a larger one leaves
# the power an opaque symbol.
_LARGEST_POWER = 16


class Comparison(NamedTuple):
    """Two terms compared by algebraic simplification, every function read as
    an opaque symbol: `equal`, whether their difference reduces to zero, and
    `functions`, by name, the functions a nonzero difference applies. Where
    `functions` is not empty the nonzero difference applies those functions,
    which the comparison reads as opaque symbols; whether an identity among
    them would make the two terms agree is not decided."""

    equal: bool
    functions: tuple


def compare_terms(left, right):
    """`left` and `right` compared by algebraic simplification. Each is read
    as a quotient of two polynomials with rational coefficients whose
    indeterminates are opaque symbols: a name, a marked field, a function
    applied to its arguments, one symbol for arguments that reduce to one
    another, and any other form the arithmetic does not read, a power whose
    exponent is not an integer among them. The two agree exactly when the
    numerator of their difference is the zero polynomial. A decimal literal
    is read as the rational number its spelling denotes, `0.9` as 9/10. None
    where a term is read as no such quotient: a division by a term that
    reduces to zero, or a number that is not finite."""
    difference = _quotient(T.Sub(left, right))
    if difference is None:
        return None
    numerator, _ = difference
    if not numerator:
        return Comparison(True, ())
    return Comparison(False, tuple(sorted(set(_functions_in(tuple(numerator))))))


def _quotient(term):
    """The term as a quotient `(numerator, denominator)` of two polynomials,
    each a mapping from a monomial, a tuple of (symbol, exponent) pairs
    sorted by symbol, to its nonzero rational coefficient; None where the
    term is read as no such quotient."""
    if isinstance(term, T.Number):
        value = _exact(term.value)
        return None if value is None else (_constant(value), _one())
    if isinstance(term, T.Neg):
        inner = _quotient(term.operand)
        return None if inner is None else (_scaled(inner[0], Fraction(-1)), inner[1])
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div)):
        left, right = _quotient(term.left), _quotient(term.right)
        if left is None or right is None:
            return None
        (a, b), (c, d) = left, right
        if isinstance(term, T.Add):
            return _reduced(_sum(_product(a, d), _product(c, b)), _product(b, d))
        if isinstance(term, T.Sub):
            return _reduced(
                _sum(_product(a, d), _scaled(_product(c, b), Fraction(-1))), _product(b, d)
            )
        if isinstance(term, T.Mul):
            return _reduced(_product(a, c), _product(b, d))
        if not c:
            return None
        return _reduced(_product(a, d), _product(b, c))
    if isinstance(term, T.Pow):
        power, base = _integer_power(term.exponent), _quotient(term.base)
        if power is None or base is None:
            return _symbol(("power", _key(term.base), _key(term.exponent)))
        numerator, denominator = base
        if power < 0:
            if not numerator:
                return None
            numerator, denominator, power = denominator, numerator, -power
        return _reduced(_power(numerator, power), _power(denominator, power))
    return _symbol(_atom(term))


def _atom(term):
    """The opaque symbol a term stands for in a quotient: a name, a marked
    field, a function applied to the keys of its arguments, or the term
    itself."""
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        return ("name", term.symbol.name)
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Variable):
        when = term.symbol.when
        side = type(when.side).__name__ if isinstance(when, T.At) else repr(when)
        return ("marked", term.symbol.name, side, term.symbol.shift)
    if isinstance(term, T.Call):
        return ("call", term.fun, tuple(_key(argument) for argument in term.args))
    return ("term", term)


def _key(term):
    """A term's quotient as one symbol can hold it, or the term itself where
    it is read as no quotient."""
    quotient = _quotient(term)
    if quotient is None:
        return ("term", term)
    numerator, denominator = quotient
    return ("quotient", _items(numerator), _items(denominator))


def _items(polynomial):
    return tuple(sorted(polynomial.items(), key=repr))


def _integer_power(exponent):
    """The exponent as an integer no larger in size than `_LARGEST_POWER`, or
    None."""
    quotient = _quotient(exponent)
    if quotient is None or quotient[1] != _one():
        return None
    numerator = quotient[0]
    if any(monomial != () for monomial in numerator):
        return None
    value = numerator.get((), Fraction(0))
    if value.denominator != 1 or abs(value) > _LARGEST_POWER:
        return None
    return int(value)


def _functions_in(item):
    """The names of the functions applied in a monomial, a symbol or a
    term."""
    if isinstance(item, tuple):
        if len(item) == 3 and item[0] == "call":
            yield str(item[1])
        for part in item:
            yield from _functions_in(part)
    elif dataclasses.is_dataclass(item) and not isinstance(item, type):
        if isinstance(item, T.Call):
            yield str(item.fun)
        for field in dataclasses.fields(item):
            yield from _functions_in(getattr(item, field.name))


def _exact(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return Fraction(repr(value)) if isinstance(value, float) else Fraction(value)


def _one():
    return {(): Fraction(1)}


def _constant(value):
    return {(): value} if value else {}


def _symbol(atom):
    return {((atom, 1),): Fraction(1)}, _one()


def _scaled(polynomial, factor):
    return (
        {monomial: coefficient * factor for monomial, coefficient in polynomial.items()}
        if factor
        else {}
    )


def _sum(left, right):
    total = dict(left)
    for monomial, coefficient in right.items():
        value = total.get(monomial, 0) + coefficient
        if value:
            total[monomial] = value
        else:
            total.pop(monomial, None)
    return total


def _product(left, right):
    total = {}
    for first, a in left.items():
        for second, b in right.items():
            monomial = _monomial_product(first, second)
            value = total.get(monomial, 0) + a * b
            if value:
                total[monomial] = value
            else:
                total.pop(monomial, None)
    return total


def _monomial_product(first, second):
    exponents = dict(first)
    for atom, exponent in second:
        exponents[atom] = exponents.get(atom, 0) + exponent
    return tuple(sorted(((atom, e) for atom, e in exponents.items() if e), key=repr))


def _power(polynomial, exponent):
    result = _one()
    for _ in range(exponent):
        result = _product(result, polynomial)
    return result


def _reduced(numerator, denominator):
    """A quotient whose denominator is a nonzero constant written over the
    denominator one."""
    if list(denominator) == [()]:
        return _scaled(numerator, Fraction(1) / denominator[()]), _one()
    return numerator, denominator
