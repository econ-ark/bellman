"""The algebra of the declared sets of a stage, on retained set terms.

A field is declared with a set at each of its declaration sites, and a line
writes a value of one set where another is required. Two questions follow: the
meet of the sets a field is declared with, which is the set its sort records,
and whether one declared set lies in another, which decides a range obligation,
an argument obligation or the refusal `set-mismatch`. Both are answered here,
on the retained set terms of `bellman.syntax.terms`. No printed set is read,
since a display string determines no mathematical behavior.

**The primitive sets.** The thirteen spellings of a primitive set stand in
the one table `PRIMITIVE_SETS` of `bellman.syntax.vocabulary`, with the glyph,
kind, order and endpoints of each. Every other name is a set the stage defines,
or a set it does not define.

**The decision table.** `meet` decides a pair of real sets, a real set against
an interval and an interval against an interval, where an interval's endpoints
are numbers or infinity; the meet is the intersection of the two endpoint
pairs, written as the glyph of a real set where it is one. It decides no other
pair, and sets that are one and the same term meet in themselves whatever their
form. `within` decides those same pairs and, besides, the integers: ℕ lies in
ℤ; ℤ lies in ℝ and in neither ℝ₊ nor ℝ₊₊; ℕ, whose members the construction
reads as positive, lies in each of the three. An interval that closes on an
infinite endpoint lies in no real set, since it holds a value no real set
holds, so `[-inf, inf)` is not within ℝ, while ℝ is within `[-inf, inf)`. Two
sets that are the same term, after each name is replaced by the set the stage
defines it as, are one set.

**Undecided forms.** Every other form is undecided: a product, a finite
set, a comprehension over a base with conditions, a set defined by a grid
constructor such as `linspace`, an interval with a symbolic endpoint, an
extended real, and a name the stage does not define. `meet` then answers None
and the declaration sites stand as they are written; `within` answers None and
the construction records the obligation the caller names. An undecided form is
never refused. A distribution family is no set, and neither function reads one.

**The finite index sets.** A finite set of labels, `{work, retire}`, an
integer range with parameter-dependent bounds, `{0, …, J}`, and a listed set
of numbers, `{0, θ} ⊂ ℝ`, each denote a finite ordered set once the
parameters they read have values, and a collection declared on the functions
from such a set to an entry set, `q : I_J → ℝ₊`, denotes a function on it.
The operations of the last section read them: `number_at` is the one
arithmetic interpretation of a retained term at parameter values, which the
calibration, the connections and the selection checks share; `finite_members`
answers the members in the set's order; `finite_count` their number;
`key_position` the position of a key among them; `index_sets` the first index
set of a collection and the set its entries lie in; `index_within` whether one
index set lies in another where the terms alone decide it; and
`finite_set_conditions` the conditions a range or a listed set owes before its
parameters have values. Numerical members and keys are integer-valued and
read as integers without rounding; `same_number` compares represented numbers
exactly, and no tolerance is applied.
"""

from __future__ import annotations

import math
import operator
from fractions import Fraction
from typing import NamedTuple

from bellman.native.predicates import And, Compare, IsInteger, Member, Not
from bellman.syntax import terms as T
from bellman.syntax.vocabulary import INTEGER, PRIMITIVE_SETS, REAL, Primitive


def primitive_of(setterm) -> Primitive | None:
    """The primitive set a term names, or None where the term names none."""
    return PRIMITIVE_SETS.get(setterm.name) if isinstance(setterm, T.Named) else None


def numeric_primitive(setterm) -> bool:
    """Whether a term names a primitive set whose members are numbers: one of
    the three real sets or one of the two integer sets. An extended real is not
    one, since it holds the adjoined infinities, which the rules of the
    arithmetic do not read as numbers."""
    primitive = primitive_of(setterm)
    return primitive is not None and primitive.kind in (REAL, INTEGER)


def numeric(setterm, definitions) -> bool | None:
    """Whether the members of the set a term denotes are numbers: True, False
    where they are identifier labels, and None where the rules do not decide.

    `definitions` are the sets the stage defines by name, through which each
    name is resolved first; a chain of definitions that returns to a name it
    has already resolved is undecided. A product is numeric only when every
    factor is, and is undecided where one factor is undecided: an obligation
    recorded where a set is undecided is the safer answer. A tuple of set terms
    — the sets declared for one field at its sites — is read by the same rule.
    """

    def decide(setterm, active):
        if isinstance(setterm, T.Space):
            return decide(setterm.set, active)
        if isinstance(setterm, T.Named):
            if numeric_primitive(setterm):
                return True
            if setterm.name in definitions and setterm.name not in active:
                return decide(definitions[setterm.name], active + (setterm.name,))
            return None
        if isinstance(setterm, T.Interval):
            return True
        if isinstance(setterm, T.FiniteSet):
            return all(not isinstance(member, str) for member in setterm.members)
        if isinstance(setterm, (T.IntegerRange, T.Points)):
            return True
        if isinstance(setterm, T.Functions):
            # a collection is no number: its entries are
            return None
        if isinstance(setterm, T.Comprehension):
            return decide(setterm.base, active)
        if isinstance(setterm, (T.Product, tuple)):
            factors = setterm.factors if isinstance(setterm, T.Product) else setterm
            answers = [decide(factor, active) for factor in factors]
            return False if False in answers else True if all(answers) else None
        return None

    return decide(setterm, ())


class Bounds(NamedTuple):
    """The bounds of a set of numbers: its lower and upper endpoints and
    whether the set holds each. An endpoint is a number or infinity; the
    restriction of a control in `ranges` also holds a term there. A named
    tuple, so that it equals the plain tuple of the same four values."""

    lower: object
    lower_closed: bool
    upper: object
    upper_closed: bool


def endpoints(setterm) -> Bounds | None:
    """The bounds of the set a term denotes: a primitive real set, or an
    interval whose endpoints are numbers or infinity. None for every other
    form, an interval with a symbolic endpoint and an interval missing an end
    marker included."""
    primitive = primitive_of(setterm)
    if primitive is not None:
        return None if primitive.bounds is None else Bounds._make(primitive.bounds)
    if isinstance(setterm, T.Interval) and isinstance(setterm.bounds, T.Range):
        bounds = setterm.bounds
        lower, upper = _endpoint_value(bounds.lower), _endpoint_value(bounds.upper)
        if lower is None or upper is None or bounds.left is None or bounds.right is None:
            return None
        return Bounds(
            lower=lower,
            lower_closed=isinstance(bounds.left, T.Closed),
            upper=upper,
            upper_closed=isinstance(bounds.right, T.Closed),
        )
    return None


def meet(setterms) -> object | None:
    """The meet of the sets declared for one field at its sites, as one
    retained set term: the largest set contained in each of them
    (ℝ₊ and ℝ₊₊ meet in ℝ₊₊).

    A site that declares no set is passed as None and is skipped, and a field
    with no declared set at any site has no meet. Sets that are one term
    meet in themselves. Otherwise the endpoints of each are intersected, and
    the meet is written as the glyph of the real set it is, else as a term
    one of the sites declares, else as the interval the endpoints give. The
    meet is None where a site declares a form the table does not read, or
    where the intersection is empty; the declaration sites then stand as
    they are written."""
    declared = [setterm for setterm in setterms if setterm is not None]
    if not declared:
        return None
    if all(setterm == declared[0] for setterm in declared):
        return declared[0]
    bounds = [endpoints(setterm) for setterm in declared]
    if any(pair is None for pair in bounds):
        return None
    lower, lower_closed, upper, upper_closed = bounds[0]
    for site in bounds[1:]:
        if site.lower > lower:
            lower, lower_closed = site.lower, site.lower_closed
        elif site.lower == lower:
            lower_closed = lower_closed and site.lower_closed
        if site.upper < upper:
            upper, upper_closed = site.upper, site.upper_closed
        elif site.upper == upper:
            upper_closed = upper_closed and site.upper_closed
    if lower > upper or (lower == upper and not (lower_closed and upper_closed)):
        return None
    return _set_term(
        Bounds(lower=lower, lower_closed=lower_closed, upper=upper, upper_closed=upper_closed),
        declared,
    )


def within(inner, outer, definitions) -> bool | None:
    """Whether the set `inner` lies in the set `outer`: True, False, or None
    where the pair is not one the table decides. `definitions` are the sets the
    stage defines by name, through which each name is resolved first."""
    a, b = defined(inner, definitions), defined(outer, definitions)
    if a == b:
        return True
    if isinstance(a, (T.IntegerRange, T.Points, T.FiniteSet)) or isinstance(
        b, (T.IntegerRange, T.Points, T.FiniteSet)
    ):
        return _finite_within(a, b, definitions)
    left, right = primitive_of(a), primitive_of(b)
    inner_real = left.order if left is not None and left.kind == REAL else None
    outer_real = right.order if right is not None and right.kind == REAL else None
    inner_integer = left.order if left is not None and left.kind == INTEGER else None
    outer_integer = right.order if right is not None and right.kind == INTEGER else None
    inner_bounds = endpoints(a) if isinstance(a, T.Interval) else None
    outer_bounds = endpoints(b) if isinstance(b, T.Interval) else None
    if inner_real is not None and outer_real is not None:
        return inner_real >= outer_real
    if inner_integer is not None and outer_integer is not None:
        return inner_integer >= outer_integer
    if inner_integer is not None and outer_real is not None:
        # ℤ lies in ℝ alone; ℕ, whose members the construction reads as
        # positive, lies in each of the three real sets
        return outer_real == 0 or left.glyph == "ℕ"
    if inner_bounds is not None and outer_real is not None:
        return _interval_in_real(inner_bounds, outer_real)
    if inner_bounds is not None and outer_bounds is not None:
        return _interval_in_interval(inner_bounds, outer_bounds)
    if inner_real is not None and outer_bounds is not None:
        return _real_in_interval(inner_real, outer_bounds)
    return None


_INF = math.inf


def _endpoint_value(expr):
    """The number an interval endpoint denotes: a number, infinity, or the
    negation of one. None for a symbolic endpoint."""
    if (
        isinstance(expr, T.Number)
        and isinstance(expr.value, (int, float))
        and not isinstance(expr.value, bool)
    ):
        return expr.value
    if (
        isinstance(expr, T.Sym)
        and isinstance(expr.symbol, T.Constant)
        and expr.symbol.name == "inf"
    ):
        return _INF
    if isinstance(expr, T.Neg):
        inner = _endpoint_value(expr.operand)
        return None if inner is None else -inner
    return None


# the glyph of the real set given by its endpoints, for writing a meet; the
# three spellings of one real set carry one glyph, so there is one entry each
_REAL_GLYPH = {
    primitive.bounds: primitive.glyph
    for primitive in PRIMITIVE_SETS.values()
    if primitive.kind == REAL
}


def _set_term(bounds, declared):
    """The term of a set given by its endpoints: the glyph of the real set it
    is, else the term of the first site that declares that same set, else the
    interval the endpoints give."""
    if bounds not in _REAL_GLYPH:
        for setterm in declared:
            if endpoints(setterm) == bounds:
                return setterm
    return set_of_bounds(bounds)


def set_of_bounds(bounds):
    """The term of the set given by its `Bounds`: the glyph of the real set it
    is, else the interval the endpoints give."""
    glyph = _REAL_GLYPH.get(bounds)
    if glyph is not None:
        return T.Named(glyph)
    return T.Interval(
        T.Range(
            left=T.Closed() if bounds.lower_closed else T.Open(),
            lower=_endpoint_term(bounds.lower),
            upper=_endpoint_term(bounds.upper),
            right=T.Closed() if bounds.upper_closed else T.Open(),
        )
    )


def _endpoint_term(value):
    """The term of an interval endpoint given as a number: the constant
    `inf` or its negation for an infinite endpoint, else the number, a
    negative one written as the negation of its magnitude, which is how the
    grammar writes a sign."""
    if value == _INF:
        return T.Sym(T.Constant("inf"))
    if value == -_INF:
        return T.Neg(T.Sym(T.Constant("inf")))
    magnitude = abs(value)
    if isinstance(magnitude, float) and magnitude.is_integer():
        magnitude = int(magnitude)
    number = T.Number(magnitude)
    return T.Neg(number) if value < 0 else number


def defined(setterm, definitions):
    """The set a term denotes once each name the stage defines is replaced by
    the set it is defined as. A name the stage does not define stands for
    itself, and a chain of definitions that returns to a name it has already
    replaced stops there."""
    seen = set()
    while (
        isinstance(setterm, T.Named) and setterm.name in definitions and setterm.name not in seen
    ):
        seen.add(setterm.name)
        setterm = definitions[setterm.name]
    return setterm


def _interval_in_real(bounds, order) -> bool:
    """Whether an interval lies in the real set of that order. An interval
    that closes on an infinite endpoint holds a value no real set holds, so
    `[-inf, inf)` is not within ℝ and the construction records the
    assumption that the value is finite."""
    if (bounds.lower_closed and bounds.lower == -_INF) or (
        bounds.upper_closed and bounds.upper == _INF
    ):
        return False
    if order == 0:
        return True
    if order == 1:
        return bounds.lower >= 0
    return bounds.lower > 0 or (bounds.lower == 0 and not bounds.lower_closed)


def _interval_in_interval(inner, outer) -> bool:
    """Whether one interval lies in another: each end of the inner interval is
    inside the outer one, or on the same endpoint with no wider closure."""
    left = inner.lower > outer.lower or (
        inner.lower == outer.lower and (outer.lower_closed or not inner.lower_closed)
    )
    right = inner.upper < outer.upper or (
        inner.upper == outer.upper and (outer.upper_closed or not inner.upper_closed)
    )
    return left and right


def _real_in_interval(order, bounds) -> bool:
    """Whether the real set of that order lies in an interval: ℝ needs
    (-inf, inf); ℝ₊, which is [0, inf), needs a lower endpoint below 0 or 0
    included; ℝ₊₊, which is (0, inf), needs a lower endpoint at or below 0."""
    if bounds.upper != _INF:
        return False
    if order == 0:
        return bounds.lower == -_INF
    if order == 1:
        return bounds.lower < 0 or (bounds.lower == 0 and bounds.lower_closed)
    return bounds.lower <= 0


# --- the finite index sets ---


class NumberValue(NamedTuple):
    """A retained numeric term read at parameter values: its `value`, an
    integer, a fraction or a float, None where the term is not decided, and
    `read`, the names of the parameters the reading took a value of."""

    value: object
    read: frozenset


_OPERATIONS = {
    T.Add: operator.add,
    T.Sub: operator.sub,
    T.Mul: operator.mul,
    T.Div: operator.truediv,
    T.Pow: operator.pow,
}
_COMPARISONS = {
    "=": operator.eq,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}


def number_at(term, values) -> NumberValue:
    """The one arithmetic interpretation of a retained numeric term at
    parameter values, `values` a mapping from parameter name to value: a
    number, a parameter named as written or by its identity, a negation, a
    sum, a difference, a product, a quotient or a power. An integer and a
    ratio of integers are read exactly, as an `int` or a `Fraction`; every
    other arithmetic is in double precision. The value is None where the
    term is no arithmetic of numbers and valued parameters, where a value is
    a boolean or not a number, or where the result is not finite. The
    calibration's predicate reading, the connections' bounds, the entry
    checks of a collection and the key checks of a selection all read a
    number through this function and no other."""
    read = frozenset()
    if isinstance(term, T.Number):
        value = term.value
    elif isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        name = term.symbol.name
        if not isinstance(name, str):
            # a parameter referred to by identity, as a condition spelled
            # in a piece's own terms refers to it; a bound variable is no
            # parameter
            if getattr(name, "kind", None) != "parameter":
                return NumberValue(None, read)
            name = name.field
        if name not in values:
            return NumberValue(None, read)
        read = frozenset((name,))
        value = values[name]
        if not is_number(value):
            return NumberValue(None, read)
    elif isinstance(term, T.Neg):
        operand = number_at(term.operand, values)
        value, read = operand.value, operand.read
        if value is not None:
            value = -value
    elif isinstance(term, (T.Add, T.Sub, T.Mul, T.Div, T.Pow)):
        left, right = (
            (term.base, term.exponent) if isinstance(term, T.Pow) else (term.left, term.right)
        )
        left, right = number_at(left, values), number_at(right, values)
        read = left.read | right.read
        left, right = left.value, right.value
        if left is None or right is None:
            return NumberValue(None, read)
        try:
            if isinstance(left, (int, Fraction)) and isinstance(right, (int, Fraction)):
                if isinstance(term, T.Div) or isinstance(term, T.Pow) and right.denominator == 1:
                    left = Fraction(left)
                    if isinstance(term, T.Pow):
                        right = int(right)
            value = _OPERATIONS[type(term)](left, right)
        except (ArithmeticError, ValueError):
            return NumberValue(None, read)
    else:
        return NumberValue(None, read)
    try:
        finite = type(value) in (int, Fraction) or type(value) is float and math.isfinite(value)
    except (ArithmeticError, TypeError, ValueError):
        return NumberValue(None, read)
    return NumberValue(value if finite else None, read)


def parameters_read(term):
    """The names of the parameters an arithmetic term of numbers and
    parameters reads, a parameter named as written or by its identity; None
    where the term holds any other node, a field, a bound variable, a
    selection or a call."""
    if isinstance(term, T.Number):
        return frozenset()
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        name = term.symbol.name
        if isinstance(name, str):
            return frozenset((name,))
        if getattr(name, "kind", None) == "parameter":
            return frozenset((name.field,))
        return None
    if isinstance(term, T.Neg):
        return parameters_read(term.operand)
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div, T.Pow)):
        left, right = (
            (term.base, term.exponent) if isinstance(term, T.Pow) else (term.left, term.right)
        )
        left, right = parameters_read(left), parameters_read(right)
        return None if left is None or right is None else left | right
    return None


def invalid_number(term, values) -> bool:
    """Whether an arithmetic term of numbers and parameters, all valued, still
    denotes no number at the values: a value that is a boolean, infinite or
    undefined, or arithmetic that fails there. Such a value as a member, a
    bound, a key or an entry refuses a calibration rather than leaving its
    condition undecided. A term that reads a field or a bound variable is
    never invalid; it is undecided."""
    names = parameters_read(term)
    if names is None or any(name not in values for name in names):
        return False
    return number_at(term, values).value is None


def is_number(value) -> bool:
    """Whether a value is a number a key, a member, a bound or an entry may
    take: an integer that is no boolean, a fraction, or a finite float."""
    return (
        type(value) is int
        or isinstance(value, Fraction)
        or (type(value) is float and math.isfinite(value))
    )


def integer_valued(value) -> bool:
    """Whether a number equals its integer part: `3`, `3.0` and `6/2` are
    integer-valued, `2.5` is not."""
    return is_number(value) and value == int(value)


def same_number(a, b) -> bool:
    """Whether two represented numbers are equal, without rounding or
    tolerance. Integral representations such as `3`, `3.0` and `6/2` agree;
    distinct exact integers remain distinct beside floating-point values."""
    return a == b


def finite_members(setterm, values, definitions):
    """The members of a finite index set at parameter values, in the set's
    order: the labels of a set of labels; the integers of a range from its
    lower to its upper bound, inclusive, an empty tuple where the lower bound
    exceeds the upper; and the integer members of a listed set. None where
    a bound or a member is no finite integer at the values,
    or where the term is no finite index set. `definitions` are the sets the
    stage defines by name."""
    term = defined(setterm, definitions)
    if isinstance(term, T.Space):
        term = defined(term.set, definitions)
    if isinstance(term, T.FiniteSet):
        return tuple(term.members)
    if isinstance(term, T.IntegerRange):
        lower, upper = number_at(term.lower, values).value, number_at(term.upper, values).value
        if lower is None or upper is None or not (integer_valued(lower) and integer_valued(upper)):
            return None
        return tuple(range(int(lower), int(upper) + 1))
    if isinstance(term, T.Points):
        members = tuple(number_at(member, values).value for member in term.members)
        if not all(integer_valued(member) for member in members):
            return None
        return tuple(int(member) for member in members)
    return None


def finite_count(setterm, values, definitions):
    """The number of members of a finite index set at parameter values, or
    None where `finite_members` does not decide them; for a product of index
    sets, the product of their counts."""
    term = defined(setterm, definitions)
    if isinstance(term, T.Product):
        counts = [finite_count(factor, values, definitions) for factor in term.factors]
        if any(count is None for count in counts):
            return None
        return math.prod(counts)
    members = finite_members(term, values, definitions)
    return None if members is None else len(members)


def key_position(members, key):
    """The position of a key among the members of a finite index set, the
    first member that is the same key, or None where none is: a label by
    equality of names, an integer-valued number by exact integer equality.
    A noninteger numerical key names no member."""
    for position, member in enumerate(members):
        if isinstance(member, str) or isinstance(key, str):
            if member == key:
                return position
        elif integer_valued(member) and integer_valued(key) and int(member) == int(key):
            return position
    return None


def index_sets(setterm, definitions):
    """The first index set of a collection declared on a set of functions and
    the set its entries lie in once that index is fixed: for `I → A` the pair
    `(I, A)`, for `I × K → A` the pair `(I, K → A)`, so that a nested
    selection reads one factor at a time, the first key on the first factor.
    None for a set that is no set of functions."""
    term = defined(setterm, definitions)
    if isinstance(term, T.Space):
        term = defined(term.set, definitions)
    if not isinstance(term, T.Functions):
        return None
    domain = defined(term.domain, definitions)
    if isinstance(domain, T.Product) and len(domain.factors) > 1:
        rest = domain.factors[1:]
        remainder = T.Functions(rest[0] if len(rest) == 1 else T.Product(rest), term.codomain)
        return domain.factors[0], remainder
    return domain, term.codomain


def index_factors(setterm, definitions):
    """The ordered index sets of a collection, every factor of its domain,
    and the set its entries lie in: for `I × K → A` the pair `((I, K), A)`.
    None for a set that is no set of functions."""
    term = defined(setterm, definitions)
    if isinstance(term, T.Space):
        term = defined(term.set, definitions)
    if not isinstance(term, T.Functions):
        return None
    domain = defined(term.domain, definitions)
    factors = tuple(domain.factors) if isinstance(domain, T.Product) else (domain,)
    return factors, term.codomain


def is_index_set(setterm, definitions) -> bool:
    """Whether a term denotes a finite index set a collection may be declared
    on: a set of labels, an integer range, a listed set of numbers, or a
    product of these."""
    term = defined(setterm, definitions)
    if isinstance(term, T.Space):
        term = defined(term.set, definitions)
    if isinstance(term, T.Product):
        return all(is_index_set(factor, definitions) for factor in term.factors)
    return isinstance(term, (T.FiniteSet, T.IntegerRange, T.Points))


def index_within(inner, outer, definitions):
    """Whether the finite index set `inner` lies in the finite index set
    `outer` where the terms alone decide it, before any parameter has a
    value: True, False, or None. Two sets that are one term lie in each
    other; two ranges are compared bound by bound where each pair of bounds
    is two numbers or one term, `{1, …, J}` within `{0, …, J}` by 0 ≤ 1 and
    J = J; two listed sets or two sets of labels by their members, a member
    that is a term by the same term and a number by `same_number`."""
    a, b = defined(inner, definitions), defined(outer, definitions)
    if isinstance(a, T.Space):
        a = defined(a.set, definitions)
    if isinstance(b, T.Space):
        b = defined(b.set, definitions)
    if a == b:
        return True
    if not is_index_set(a, definitions):
        # a key declared on ℕ, on an interval or on a set the stage does not
        # define is not within a finite index set
        return False
    finite = (T.FiniteSet, T.IntegerRange, T.Points)
    if isinstance(a, finite) and isinstance(b, finite):
        if isinstance(a, T.FiniteSet) != isinstance(b, T.FiniteSet):
            # a label is never a number
            return False
    if isinstance(a, T.IntegerRange) and isinstance(b, T.IntegerRange):
        lower = _term_le(b.lower, a.lower)
        upper = _term_le(a.upper, b.upper)
        if lower is False or upper is False:
            return False
        return True if lower and upper else None
    if isinstance(a, T.FiniteSet) and isinstance(b, T.FiniteSet):
        return set(a.members) <= set(b.members)
    if isinstance(a, (T.Points, T.IntegerRange)) and isinstance(b, (T.Points, T.IntegerRange)):
        members_a = finite_members(a, {}, definitions)
        members_b = finite_members(b, {}, definitions)
        if members_a is not None and members_b is not None:
            return all(key_position(members_b, member) is not None for member in members_a)
        if isinstance(a, T.Points) and isinstance(b, T.Points):
            if all(member in b.members for member in a.members):
                return True
        return None
    return None


def _term_le(left, right):
    """Whether `left ≤ right` holds for two retained terms as they stand: True
    where the terms are one term or two numbers in that order, False where
    two numbers in the other order, None otherwise."""
    if left == right:
        return True
    a, b = number_at(left, {}).value, number_at(right, {}).value
    if a is None or b is None:
        return None
    return a <= b


def _finite_within(a, b, definitions):
    """`within` for a pair in which a finite index set stands: the integers
    of a range lie in ℤ, in ℕ where the lower bound is a number of at least
    one, and in a real set or an interval where its numeric bounds do; the
    numbers of a listed set lie in a set that holds each of them; a set of
    labels lies in no set but itself. None where the bounds or the members
    are not numbers, or where the pair is of another form."""
    if isinstance(b, (T.IntegerRange, T.Points, T.FiniteSet)):
        if isinstance(a, (T.IntegerRange, T.Points, T.FiniteSet)):
            return index_within(a, b, definitions)
        return None
    if isinstance(a, T.FiniteSet):
        return None
    primitive = primitive_of(b)
    if isinstance(a, T.IntegerRange):
        if primitive is not None and primitive.kind == INTEGER:
            if primitive.order == 0:
                return True
            lower = number_at(a.lower, {}).value
            if lower is None:
                return None
            # ℕ is the positive integers here, as the parameter check reads it
            return bool(lower >= 1)
        lower, upper = number_at(a.lower, {}).value, number_at(a.upper, {}).value
        if lower is None or upper is None:
            return None
        points = Bounds(lower=lower, lower_closed=True, upper=upper, upper_closed=True)
        return within(set_of_bounds(points), b, definitions)
    members = finite_members(a, {}, definitions)
    if members is None:
        return None
    answers = []
    for member in members:
        if primitive is not None and primitive.kind == INTEGER:
            answers.append(integer_valued(member) and (primitive.order == 0 or member > 0))
            continue
        point = Bounds(lower=member, lower_closed=True, upper=member, upper_closed=True)
        answers.append(within(set_of_bounds(point), b, definitions))
    if False in answers:
        return False
    return True if all(answers) else None


def finite_set_conditions(setterm):
    """The conditions a finite index set owes before its parameters have
    values, as retained predicates, each decided at calibration: for a range,
    that both bounds are integers and the lower does not exceed the upper;
    for a listed set, that its members are integers, pairwise distinct and,
    where the set its members lie in is named, that each member lies in it. A
    condition two numbers already decide true is left out. The answer is a
    tuple of `(condition name, predicate)` pairs."""
    found = []
    if isinstance(setterm, T.IntegerRange):
        bounds = []
        for bound in (setterm.lower, setterm.upper):
            value = number_at(bound, {}).value
            if value is None or not integer_valued(value):
                bounds.append(IsInteger(bound))
        order = Compare(setterm.lower, "<=", setterm.upper)
        if _term_le(setterm.lower, setterm.upper) is not True:
            bounds.append(order)
        if bounds:
            found.append(("index-set-bounds", _conjunction(bounds)))
    if isinstance(setterm, T.Points):
        distinct = []
        members = setterm.members
        for member in members:
            value = number_at(member, {}).value
            if value is None or not integer_valued(value):
                distinct.append(IsInteger(member))
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = number_at(members[i], {}).value, number_at(members[j], {}).value
                if a is not None and b is not None and not same_number(a, b):
                    continue
                distinct.append(Not(Compare(members[i], "=", members[j])))
        if setterm.superset is not None:
            for member in members:
                value = number_at(member, {}).value
                if value is not None:
                    point = Bounds(lower=value, lower_closed=True, upper=value, upper_closed=True)
                    if within(set_of_bounds(point), setterm.superset, {}) is True:
                        continue
                distinct.append(Member(member, setterm.superset))
        if distinct:
            found.append(("index-set-members", _conjunction(distinct)))
    return tuple(found)


def literal_faults(setterm, printer) -> tuple:
    """The faults of a finite index set that its written numbers decide
    before any parameter has a value, each as a clause of a refusal printed
    with `printer`: a literal bound that is no integer, a lower bound written
    above the upper, a member that is no integer, two members written as one
    number, and a member written outside the set the members lie in. A fault
    that reads a parameter is not among them; it is decided at calibration."""
    faults = []
    if isinstance(setterm, T.IntegerRange):
        lower, upper = number_at(setterm.lower, {}).value, number_at(setterm.upper, {}).value
        for bound, value in ((setterm.lower, lower), (setterm.upper, upper)):
            if invalid_number(bound, {}):
                faults.append(f"has the bound {printer(bound)}, which is no finite real number")
            elif value is not None and not integer_valued(value):
                faults.append(f"has the bound {printer(bound)}, which is no integer")
        if lower is not None and upper is not None and lower > upper:
            faults.append(
                f"has the lower bound {printer(setterm.lower)} above the upper bound "
                f"{printer(setterm.upper)}, so it is empty"
            )
    if isinstance(setterm, T.Points):
        members = setterm.members
        numbers = [number_at(member, {}).value for member in members]
        for member, value in zip(members, numbers):
            if invalid_number(member, {}):
                faults.append(f"lists {printer(member)}, which is no finite real number")
            elif value is not None and not integer_valued(value):
                faults.append(f"lists {printer(member)}, which is no integer")
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if numbers[i] is not None and numbers[j] is not None:
                    if same_number(numbers[i], numbers[j]):
                        faults.append(
                            f"lists {printer(members[i])} and {printer(members[j])}, which are "
                            "one number"
                        )
        if setterm.superset is not None:
            for member, value in zip(members, numbers):
                if value is None:
                    continue
                point = Bounds(lower=value, lower_closed=True, upper=value, upper_closed=True)
                if within(set_of_bounds(point), setterm.superset, {}) is False:
                    faults.append(
                        f"lists {printer(member)}, which lies outside {printer(setterm.superset)}"
                    )
    return tuple(faults)


def _conjunction(predicates):
    """One predicate standing for all of `predicates`: the predicate itself
    where there is one, else their conjunction, nested to the left."""
    head, *rest = predicates
    for predicate in rest:
        head = And(head, predicate)
    return head
