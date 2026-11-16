"""Constraints read at numbers: the values that a complementary-slackness
clause admits at each saving, the policies that the identification admits,
the membership that the durables solve reads, and a feasible set read at a
point, each read with the exact arithmetic of the fixture `at_numbers`."""

import itertools
import math
import operator
from fractions import Fraction

import pytest
from stage_builders import stage_from_text
from stage_texts import (
    BUDGET_SET_LINE,
    CANDIDATE_LINE,
    EGM_LINES,
    JOINT_CHOICE,
    changed,
    cons_text_with_policy_lines,
)

from bellman.native import predicates
from bellman.native.identity import Identity
from bellman.native.records import ResolvedName
from bellman.stage.boxes import kind_of
from bellman.stage.term_operations import kuhn_tucker
from bellman.syntax import terms
from bellman.typing import typed_expressions
from bellman.typing.ranges import clause_regions

# the calibration of the consumption stage that the tests read: with ρ = 2 and
# the continuation marginal value D_{a}𝑉≻ ≡ 1, the interior value
# 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) = 1^(−1/2) is 1 at every saving, so that 𝑐≻(a) is 1 and
# 𝑚_d≻(a) is a + 1 at a positive saving, and at zero saving the two take
# every value of the segment (0, 1] together
RHO_IS_TWO = {"ρ": 2}


# pairs (cash on hand, consumption), each at its saving. With the clause the
# relation holds the first four: the corner pairs (1/2, 1/2) and (1/4, 1/4)
# and the interior pairs (1, 1) and (2, 1). Without it, the interior pairs
# alone. The pair (3/2, 1/2) at a positive saving lies off the candidate. The
# pair (1/2, 1/4) is the value of 𝑐(x) = x²/m̄ at x = 1/2 with m̄ = 1: 1/2 is
# the cash on hand of a value admitted at zero saving and 1/4 a value
# admitted there, so a relation read over the images of the two
# correspondences would hold it, and the relation over the admitted pairs
# does not. The pair (3/2, 3/2) lies above the segment of the corner.
PAIRS = (
    (0, (Fraction(1, 2), Fraction(1, 2))),
    (0, (Fraction(1, 4), Fraction(1, 4))),
    (0, (1, 1)),
    (1, (2, 1)),
    (1, (Fraction(3, 2), Fraction(1, 2))),
    (0, (Fraction(1, 2), Fraction(1, 4))),
    (0, (Fraction(3, 2), Fraction(3, 2))),
)


# the durables adjuster with the clause `⟂ a_nxt_adj >= 0` on its candidate
# line, read at numbers under which every value is exact: the utility of the
# file with α = 1/2, γ_c = γ_h = 2 and κ = 1, so that 𝑢_c(c) = 1/(2c²),
# 𝑢_h(h) = 1/(2h²) and 𝑢_c_inv(x) = (1/(2x))^(1/2); the adjustment cost τ = 1;
# the discount factor β = 1/2; the borrowing limit b = 0 that the clause
# writes; and the continuation value 𝑉≻(a, h, z) = ln(1 + a) + ln h, whose
# derivatives, under the names that the terms of the stage give them, are
# D_{a_nxt_adj}V≻(a, h, z) = 1/(1 + a) and D_{h_nxt_adj}V≻(a, h, z) = 1/h
DURABLES = {
    "α": Fraction(1, 2),
    "γ_c": 2,
    "γ_h": 2,
    "κ": 1,
    "τ": 1,
    "β": Fraction(1, 2),
    "D_{a_nxt_adj}V≻": lambda a, h, z: 1 / (1 + Fraction(a)),
    "D_{h_nxt_adj}V≻": lambda a, h, z: 1 / Fraction(h),
}


BORROWING_LIMIT = 0


# the two housing choices h′ at the borrowing limit, each with the
# consumption c* at which the housing condition
# (1 + τ)·𝑢_c(c) = 𝑢_h(h′) + β·𝑑𝑉_h≻(b, h′, z′) holds, the decision point
# (m, z_d, c, h_choice) whose saving is b, m = c* + b + (1 + τ)·h′, and
# whether c* passes the test 𝑢_c(c*) ≥ β·𝑑𝑉_a≻(b, h′, z′) by which an
# endogenous grid solver of the durables model adds the point at the
# borrowing limit: at h′ = 1/8, c* = 1/6 lies in the segment (0, 1] and
# passes; at h′ = 7/2, c* = 7/3 lies above it and fails
HOUSING_CHOICES = [
    pytest.param(
        Fraction(1, 8),
        Fraction(1, 6),
        (Fraction(5, 12), 1, Fraction(1, 6), Fraction(1, 8)),
        True,
        id="small-house-passes",
    ),
    pytest.param(
        Fraction(7, 2),
        Fraction(7, 3),
        (Fraction(28, 3), 1, Fraction(7, 3), Fraction(7, 2)),
        False,
        id="large-house-fails",
    ),
]


# the writings of a clause on the candidate line of `cons.bl`: each of the
# five relations of the line, with each of the four clauses of one bound on
# the saving and its cap 2, and, after an equation, the chain of two bounds
# ascending and with its endpoints reversed; a chain after an inequality is
# refused under `readable-form` and has no reading
RELATIONS = {"=": "equation", "<=": "at-most", ">=": "at-least", "<": "below", ">": "above"}


ONE_BOUND = {
    "a >= 0": "saving-at-least-0",
    "a > 0": "saving-above-0",
    "a <= 2": "saving-at-most-2",
    "a < 2": "saving-below-2",
}


CLAUSE_WRITINGS = [
    pytest.param(relation, bound, id=f"{name}-{bound_name}")
    for relation, name in RELATIONS.items()
    for bound, bound_name in ONE_BOUND.items()
] + [
    pytest.param("=", "0 <= a <= 2", id="equation-saving-between-0-and-2"),
    pytest.param("=", "2 <= a <= 1", id="equation-endpoints-reversed"),
]


# the savings and the consumptions at which each clause is read: the slack of
# each bound takes both signs and zero, and so does the residual, the
# consumption less the interior value 1
SAVINGS = (-1, 0, 1, 2, 3)


CONSUMPTIONS = (Fraction(1, 2), 1, Fraction(3, 2), 2)


# the definitions of two stages read at numbers, each with the stage, the
# numbers, the name of the definition, its arguments and its value there
DEFINITIONS_AT_NUMBERS = [
    # 𝑑𝑢𝑖𝑛𝑣(x) = x^(−1/ρ) at ρ = 2: (16/9)^(−1/2) = 3/4 and 1^(−1/2) = 1
    pytest.param(
        "cons_with_egm_lines",
        RHO_IS_TWO,
        "𝑑𝑢𝑖𝑛𝑣",
        (Fraction(16, 9),),
        Fraction(3, 4),
        id="inverse-marginal-utility-at-16-ninths",
    ),
    pytest.param(
        "cons_with_egm_lines", RHO_IS_TWO, "𝑑𝑢𝑖𝑛𝑣", (1,), 1, id="inverse-marginal-utility-at-1"
    ),
    # 𝑑𝑢(c) = c^(−ρ): (1/2)^(−2) = 4
    pytest.param(
        "cons_with_egm_lines", RHO_IS_TWO, "𝑑𝑢", (Fraction(1, 2),), 4, id="marginal-utility"
    ),
    # the arguments are the cash on hand and the consumption; the saving
    # is 2 − 1/2 = 3/2
    pytest.param(
        "cons_with_egm_lines",
        RHO_IS_TWO,
        "dcsn_to_cntn",
        (2, Fraction(1, 2)),
        Fraction(3, 2),
        id="law-of-motion-of-cons",
    ),
    # the arguments are (m, z_d, c, h_choice) = (3, 1, 1, 1) at τ = 1/10:
    # the saving m − c − (1 + τ)·h_choice = 3 − 1 − 11/10 = 9/10, the
    # housing h_choice and the shock z_d
    pytest.param(
        "adjuster_cons_with_egm_lines",
        {**DURABLES, "τ": Fraction(1, 10)},
        "dcsn_to_cntn",
        (3, 1, 1, 1),
        (Fraction(9, 10), 1, 1),
        id="law-of-motion-of-the-durables-adjuster",
    ),
    # 𝑢_c_inv(x) = (1/(2x))^(1/2): (1/(2·1/8))^(1/2) = 4^(1/2) = 2
    pytest.param(
        "adjuster_cons_with_egm_lines",
        {**DURABLES, "τ": Fraction(1, 10)},
        "𝑢_c_inv",
        (Fraction(1, 8),),
        2,
        id="inverse-marginal-utility-of-durables",
    ),
    # 𝑢_h(h) = 1/(2h²): 1/(2·4) = 1/8
    pytest.param(
        "adjuster_cons_with_egm_lines",
        {**DURABLES, "τ": Fraction(1, 10)},
        "𝑢_h",
        (2,),
        Fraction(1, 8),
        id="marginal-utility-of-housing",
    ),
]


# the stage of a joint choice with the budget set of the public page on
# constraints, a comprehension whose first two coordinates sum to its
# argument, declared and not named by the maximization statement
BUDGET_SET = changed(
    JOINT_CHOICE,
    (
        "@stage: joint_choice\n",
        "@stage: joint_choice\n" + BUDGET_SET_LINE + "\n",
    ),
)


# the sets that the language names by a word, each as the test that a number
# passes to be a member
NUMBER_SETS = {
    "ℝ": lambda number: -math.inf < number < math.inf,
    "ℝ₊": lambda number: 0 <= number < math.inf,
    "ℝ₊₊": lambda number: 0 < number < math.inf,
}


# the mark after the name of a function read at the continuation or the
# arrival perch, as a card prints it, by the perch of an identity and by the
# perch that a stage file's mark names, `c[>]`
PERCH_MARKS = {"cntn": "≻", "arvl": "≺", "Continuation": "≻", "Arrival": "≺"}


# the comparisons by the sign that a predicate holds, and the signs of the
# written relations by their class name
COMPARISONS = {
    "<": operator.lt,
    "<=": operator.le,
    "=": operator.eq,
    ">=": operator.ge,
    ">": operator.gt,
}


SIGNS = {"Lt": "<", "Le": "<=", "Eq": "=", "Ge": ">=", "Gt": ">"}


# the references that a term of a stage holds by name
REFERENCES = (Identity, ResolvedName, terms.Sym, terms.Constant, terms.Variable)


def candidate_text(name, line, declarations=""):
    """`cons.bl` renamed `name`, its candidate line replaced by `line`, and
    the declarations `declarations` added after the declaration of `ρ`."""
    text = cons_text_with_policy_lines(name, EGM_LINES.replace(CANDIDATE_LINE, line))
    if declarations:
        text = changed(text, ("ρ : [1, inf)\n", "ρ : [1, inf)\n" + declarations))
    return text


def clause_stage(relation, bound):
    """`cons.bl` with the candidate line written with the relation
    `relation` and the clause `⟂ bound`."""
    line = f"    c[>]   {relation} 𝑑𝑢𝑖𝑛𝑣(D_{{a}}V[>]) ⟂ {bound}           :: [id=InvEuler]\n"
    return stage_from_text(candidate_text("clause", line), "clause.bl")


def identification(stage):
    """The relation that the identification of a stage's policy builder
    holds, the set of policies that its `signature()` answers."""
    return stage.builder.policy["cons_choice:Pullback"].denote().outputs[0].expression


def clause_condition_and_regions(stage):
    """The Kuhn–Tucker condition of the clause of the candidate line, as the
    definitions table holds the line, and the split of that condition into
    its regions, the cases by which the package reads a clause: one where
    the slack is positive and one where the bound binds, and three for a
    chain."""
    line = stage.definitions["policy.InvEuler"].equations[0]
    condition = kuhn_tucker(line.core, line.bound)
    return condition, clause_regions(condition)


def name_at_numbers(reference):
    """The name under which the numbers of `at_numbers` give a reference its
    value: the name that the file writes, with `≻` after a function read at
    the continuation perch and `≺` after one read at the arrival perch (`V≻`,
    `c≻`, `m_d≻`, `𝑑𝑢𝑖𝑛𝑣`, `ρ`, `a`), a field that a stage file writes under
    a perch mark likewise (`c[>]` as `c≻`), and a law of motion by the block
    that writes it (`dcsn_to_cntn`)."""
    if isinstance(reference, terms.Sym):
        reference = reference.symbol
    if isinstance(reference, terms.Variable):
        side = type(getattr(reference.when, "side", None)).__name__
        return f"{reference.name}{PERCH_MARKS.get(side, '')}"
    if isinstance(reference, (terms.Constant, terms.Var)):
        reference = reference.name
    if isinstance(reference, terms.Coordinate):
        reference = reference.stem
    if isinstance(reference, ResolvedName):
        reference = reference.identity
    if not isinstance(reference, Identity):
        return str(reference)
    if reference.kind == "g":
        return reference.address
    mark = PERCH_MARKS.get(reference.perch, "") if reference.kind == "function" else ""
    return f"{reference.field}{mark}"


def exact(number):
    """A number as a fraction where it is finite, a decimal written in a
    file or a test read at its decimal value, so that the arithmetic of the
    tests is exact; an infinity as a float."""
    if isinstance(number, bool):
        raise TypeError("a truth value is no number")
    if isinstance(number, (int, Fraction)):
        return Fraction(number)
    if isinstance(number, float):
        return Fraction(str(number)) if math.isfinite(number) else number
    if number in ("inf", "-inf"):
        return float(number)
    raise TypeError(f"{number!r} is no number")


def _numbers(values):
    """The values with every number made exact; a function or a set is
    kept."""
    return {
        name: exact(value)
        if isinstance(value, (int, float, Fraction)) and not isinstance(value, bool)
        else value
        for name, value in values.items()
    }


def _integer_root(number, degree):
    """The integer whose `degree`-th power is `number`, or None."""
    guess = round(number ** (1 / degree))
    return next((k for k in (guess - 1, guess, guess + 1) if k >= 0 and k**degree == number), None)


def _power(base, exponent):
    """`base` to the power `exponent`: exact where the exponent is an
    integer, or where the root that it takes of a positive fraction is a
    fraction; a float otherwise."""
    if isinstance(base, Fraction) and isinstance(exponent, Fraction):
        if exponent.denominator == 1:
            return base**exponent.numerator
        if base > 0:
            roots = [
                _integer_root(part, exponent.denominator)
                for part in (base.numerator, base.denominator)
            ]
            if None not in roots:
                return Fraction(*roots) ** exponent.numerator
    return float(base) ** float(exponent)


def _spread(arguments):
    """The arguments of an application, one tuple spread into its items, as
    a function of several coordinates is applied to a point."""
    arguments = tuple(arguments)
    return arguments[0] if len(arguments) == 1 and isinstance(arguments[0], tuple) else arguments


def _named(reference, values):
    """The value that `values` gives a name; infinity for `inf`."""
    name = name_at_numbers(reference)
    if name == "inf":
        return math.inf
    if name not in values:
        raise KeyError(f"the term names {name}, and the numbers give it no value")
    value = values[name]
    return (
        exact(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value
    )


def _bound_names(bound):
    """The names that a comprehension binds, in order."""
    if isinstance(bound, terms.Subject):
        return [name_at_numbers(item) for item in bound.coordinates]
    if isinstance(bound, terms.Tuple):
        return [name_at_numbers(item) for item in bound.items]
    return [name_at_numbers(bound)]


def _sides(statement):
    """The two sides of an equation, held as a comparison or as a written
    equation."""
    if hasattr(statement, "relation"):
        if statement.relation != "=":
            raise TypeError(f"{statement!r} is no equation")
        return statement.left, statement.right
    return statement.lhs, statement.rhs


def _member(element, held_set, values):
    """Whether a number, or a tuple of numbers, is a member of a set of a
    stage: a set that the language names by a word, a set that the numbers
    give by name, an interval, a comprehension, a product, a finite set, or
    the value of a correspondence at a point, which the numbers give as the
    test of membership."""
    if isinstance(held_set, terms.Space):
        held_set = held_set.set
    if isinstance(held_set, terms.Named):
        if held_set.name in NUMBER_SETS:
            return NUMBER_SETS[held_set.name](element)
        named = _named(held_set.name, values)
        return named(element) if callable(named) else _member(element, named, values)
    if isinstance(held_set, terms.Interval):
        bounds = held_set.bounds
        lower = -math.inf if bounds.lower in (None, "-inf") else _value(bounds.lower, values)
        upper = math.inf if bounds.upper in (None, "inf") else _value(bounds.upper, values)
        above = element >= lower if isinstance(bounds.left, terms.Closed) else element > lower
        below = element <= upper if isinstance(bounds.right, terms.Closed) else element < upper
        return above and below
    if isinstance(held_set, terms.Comprehension):
        names = _bound_names(held_set.bound)
        point = element if len(names) > 1 else (element,)
        inner = {**values, **dict(zip(names, point))}
        if held_set.base is not None and not _member(element, held_set.base, values):
            return False
        return all(_value(condition, inner) for condition in held_set.conds)
    if isinstance(held_set, terms.Product):
        return len(element) == len(held_set.factors) and all(
            _member(item, factor, values) for item, factor in zip(element, held_set.factors)
        )
    if isinstance(held_set, terms.FiniteSet):
        return any(element == _value(member, values) for member in held_set.members)
    # the value of a correspondence at a point is the test of membership in
    # it; the value of a function at a point, a number, is the set that
    # holds that number alone
    test = _value(held_set, values)
    return test(element) if callable(test) else element == test


ARITHMETIC = {
    terms.Add: operator.add,
    terms.Sub: operator.sub,
    terms.Mul: operator.mul,
    terms.Div: operator.truediv,
}


# the terms that apply a function at a point
APPLICATIONS = (typed_expressions.Apply, terms.Call)


def _applied_function(term):
    """The function that an application applies."""
    return term.function if isinstance(term, typed_expressions.Apply) else term.fun


def _value(term, values):
    """The value of a term of a stage at the numbers `values`: a number, a
    truth value, a tuple, or a function of numbers."""
    if isinstance(term, bool):
        return term
    if isinstance(term, (int, float, Fraction)):
        return exact(term)
    if isinstance(term, (str, *REFERENCES)):
        return _named(term, values)
    if isinstance(term, terms.Number):
        return exact(term.value)
    if isinstance(term, terms.Neg):
        return -_value(term.operand, values)
    if type(term) in ARITHMETIC:
        return ARITHMETIC[type(term)](_value(term.left, values), _value(term.right, values))
    if isinstance(term, terms.Pow):
        return _power(_value(term.base, values), _value(term.exponent, values))
    if isinstance(term, terms.Tuple):
        return tuple(_value(item, values) for item in term.items)
    if isinstance(term, terms.Select) and isinstance(term.sel, terms.Pos):
        # a coordinate of a tuple, counted from 1 as a file writes it, `q[1]`
        return _value(term.family, values)[term.sel.at - 1]
    if isinstance(term, APPLICATIONS):
        function = _value(_applied_function(term), values)
        if not callable(function):
            raise TypeError(f"{term!r} applies a value that is no function")
        return function(*_spread(_value(argument, values) for argument in term.args))
    if isinstance(term, predicates.Compare):
        return COMPARISONS[term.relation](_value(term.left, values), _value(term.right, values))
    if isinstance(term, terms.Rel):
        sign = SIGNS[type(term.op).__name__]
        return COMPARISONS[sign](_value(term.left, values), _value(term.right, values))
    if isinstance(term, terms.Between):
        middle = _value(term.middle, values)
        lower, upper = SIGNS[type(term.lo).__name__], SIGNS[type(term.hi).__name__]
        return COMPARISONS[lower](_value(term.lower, values), middle) and COMPARISONS[upper](
            middle, _value(term.upper, values)
        )
    if isinstance(term, (predicates.And, predicates.Or)):
        left, right = _value(term.left, values), _value(term.right, values)
        return (left and right) if isinstance(term, predicates.And) else (left or right)
    if isinstance(term, predicates.Not):
        return not _value(term.operand, values)
    if isinstance(term, predicates.Member):
        return _member(_value(term.subject, values), term.set, values)
    if isinstance(term, (predicates.Complementarity, terms.Slack)):
        # a relation held with its bound states the Kuhn–Tucker system that
        # `kuhn_tucker` builds of the two, which defines the clause
        return _value(kuhn_tucker(term.core, term.bound), values)
    if isinstance(term, terms.Operator) and term.head == "D" and len(term.args) == 1:
        # the test gives the derivative by its name; nothing is differentiated
        argument = term.args[0]
        applied = isinstance(argument, APPLICATIONS)
        function = _applied_function(argument) if applied else argument
        subscripts = ", ".join(name_at_numbers(item) for item in term.subs)
        derivative = _named("D_{" + subscripts + "}" + name_at_numbers(function), values)
        if applied:
            return derivative(*_spread(_value(item, values) for item in argument.args))
        return derivative
    raise TypeError(f"a {type(term).__name__} is not read at numbers here: {term!r}")


def _function(definition, numbers):
    """The function that a definition `𝑓(x : X) := body` writes, read at
    the numbers."""
    names = [name_at_numbers(parameter) for parameter in definition.params]
    return lambda *point: _value(definition.body, {**numbers, **dict(zip(names, _spread(point)))})


def _correspondence(definition, numbers):
    """The correspondence that a definition `Γ(x : X) := set` writes, giving
    at a point the test of membership in its value."""
    names = [name_at_numbers(parameter) for parameter in definition.params]
    return lambda *point: lambda element: _member(
        element, definition.body, {**numbers, **dict(zip(names, _spread(point)))}
    )


def _law(names, lines, numbers):
    """The law of motion whose lines are `lines`, a function of the
    coordinates `names`: each line's right side is read in turn and its left
    side named, and the outputs are given in the order that the lines write
    them, one output alone as a number."""

    def law(*point):
        local = {**numbers, **dict(zip(names, _spread(point)))}
        outputs = []
        for line in lines:
            output = name_at_numbers(line.lhs)
            local[output] = _value(line.rhs, local)
            outputs.append(local[output])
        return outputs[0] if len(outputs) == 1 else tuple(outputs)

    return law


def _applies(term, name):
    """Whether a term is the function `name` applied at a point."""
    return isinstance(term, typed_expressions.Apply) and name_at_numbers(term.function) == name


def _core(rule):
    """The relation that a rule states, without its clause: a rule held with
    its bound, `r ⟂ s`, states `r` of its output."""
    statement = getattr(rule, "statement", rule)
    return statement.core if isinstance(statement, predicates.Complementarity) else statement


def terms_inside(term):
    """A term of a stage and every term inside it, the term first."""
    yield term
    if isinstance(term, (tuple, list)):
        for item in term:
            yield from terms_inside(item)
    elif hasattr(term, "__dataclass_fields__") and not isinstance(term, type):
        for field in term.__dataclass_fields__:
            yield from terms_inside(getattr(term, field))


def reads(term, name):
    """Whether a term of a stage reads the name `name`, as
    `name_at_numbers` writes it, anywhere inside it."""
    return any(
        isinstance(item, REFERENCES) and name_at_numbers(item) == name
        for item in terms_inside(term)
    )


def _point_of(rule, name):
    """The names of the coordinates at which a rule reads the function
    `name`: the arguments of the first application of `name` in the rule's
    statement whose arguments are coordinates, `(a,)` of
    `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a))`; or, where the statement writes `name` bare
    and the region note of the rule is the membership of a point of several
    coordinates in its domain, `𝑐≻ ≤ 𝑢_c_inv(β · 𝑑𝑉_a≻) on (a_nxt_adj,
    h_nxt_adj, z_nxt_adj) ∈ …`, the coordinates of that point; None where
    the rule has neither."""
    statement = getattr(rule, "statement", rule)
    for term in terms_inside(statement):
        if _applies(term, name):
            arguments = term.args
            if len(arguments) == 1 and isinstance(arguments[0], terms.Tuple):
                arguments = arguments[0].items
            if all(
                isinstance(argument, (terms.Sym, terms.Constant, str)) for argument in arguments
            ):
                return [name_at_numbers(argument) for argument in arguments]
    point = _point_named(rule)
    if point is not None and name in _bare_names(statement):
        return point
    return None


def _point_named(rule):
    """The names of the coordinates of the point that a rule's region note
    names, `(a_nxt_adj, h_nxt_adj, z_nxt_adj)` of `on (a_nxt_adj, h_nxt_adj,
    z_nxt_adj) ∈ ℝ₊ × ℝ₊₊ × ℝ₊₊`; None where the note names no point of
    several coordinates."""
    region = getattr(rule, "on", None)
    if isinstance(region, predicates.Member) and isinstance(region.subject, terms.Tuple):
        return [name_at_numbers(item) for item in region.subject.items]
    return None


def _bare_names(statement):
    """The names that a statement writes bare, applied to no argument: every
    reference in it that stands in no function position of an
    application, and every derivative of a function written bare."""
    # the function position of every application, with the terms inside it
    applied = {
        id(inner)
        for term in terms_inside(statement)
        if isinstance(term, APPLICATIONS)
        for inner in terms_inside(_applied_function(term))
    }
    names = {
        name_at_numbers(term)
        for term in terms_inside(statement)
        if isinstance(term, REFERENCES) and id(term) not in applied
    }
    names.update(
        "D_{"
        + ", ".join(name_at_numbers(item) for item in term.subs)
        + "}"
        + name_at_numbers(term.args[0])
        for term in terms_inside(statement)
        if isinstance(term, terms.Operator)
        and term.head == "D"
        and len(term.args) == 1
        and not isinstance(term.args[0], APPLICATIONS)
        and id(term) not in applied
    )
    return names


def _at_point(rule, numbers):
    """The numbers with the `Where` clauses of a rule read (`_where`) and,
    where the region note of the rule names a point of several coordinates,
    every function that the statement writes bare read at that point: a name
    whose value is a function of numbers is given its value at the point, so
    that `𝑐≻ ≤ 𝑢_c_inv(β · 𝑑𝑉_a≻)` reads `𝑐≻` and `𝑑𝑉_a≻` at
    `(a_nxt_adj, h_nxt_adj, z_nxt_adj)`."""
    numbers = _where(rule, numbers)
    point = _point_named(rule)
    if point is None or any(name not in numbers for name in point):
        return numbers
    values = tuple(numbers[name] for name in point)
    for name in _bare_names(getattr(rule, "statement", rule)):
        if callable(numbers.get(name)):
            numbers[name] = numbers[name](*values)
    return numbers


def _where(rule, numbers):
    """The numbers with the names of the `Where` clauses of a rule added,
    each clause giving the names on its left side the values of its right
    side, `(a_nxt_adj, h_nxt_adj, z_nxt_adj) = 𝑔≻(m, z_d, c, h_choice)`."""
    numbers = dict(numbers)
    for clause in getattr(rule, "where", ()):
        names, value = _sides(clause)
        targets = names.items if isinstance(names, terms.Tuple) else (names,)
        point = _value(value, numbers)
        point = point if len(targets) > 1 else (point,)
        numbers.update({name_at_numbers(target): item for target, item in zip(targets, point)})
    return numbers


class ReadingAtNumbers:
    """A term of a stage read at numbers: every name that the term mentions
    is given the number, the function of numbers or the set that `values`
    gives it, under the name that `name_at_numbers` writes, and the term is
    evaluated in exact rational arithmetic wherever the numbers allow. A
    relation held with its bound, `r ⟂ s`, reads as the Kuhn–Tucker system
    that `kuhn_tucker` builds of the two, the language's definition of the
    clause.

    Calling the object gives the value of a term. `stage` adds the stage's
    own definitions to the numbers and `rows` the outputs that a builder's
    rows define; `rule` reads a rule that a card prints, its `Where` clauses
    first; `admitted` gives the values that a rule admits for its output at
    one point; `demand` reads a relation on an unknown function at one point
    of its quantifier; `one_function` says whether one function meets a list
    of such demands."""

    def __call__(self, term, values):
        return _value(term, _numbers(values))

    def stage(self, stage, values):
        """`values` with the definitions of the stage added, each read at
        these numbers: a named set by its name (`Xa`), a function and a
        correspondence by theirs (`𝑑𝑢𝑖𝑛𝑣`, `Γ`), the correspondence giving
        at a point the test of membership in its value, and a law of motion
        by its block (`dcsn_to_cntn`), giving the outputs that its lines
        write, in their order. A name that `values` gives keeps the value
        given."""
        numbers = _numbers(values)
        for record in stage.definitions.values():
            name = name_at_numbers(record.identity)
            if name in numbers:
                continue
            if record.kind == "set":
                numbers[name] = record.equations[0]
            elif record.kind == "function":
                numbers[name] = _function(record.equations[0], numbers)
            elif record.kind == "correspondence":
                numbers[name] = _correspondence(record.equations[0], numbers)
            elif record.kind == "g":
                lines = [stage.definitions[address].equations[0] for address in record.equations]
                coordinates = [coordinate for coordinate, _ in record.coordinates]
                numbers[name] = _law(coordinates, lines, numbers)
        return numbers

    def rows(self, builder, values):
        """`values` with each output that an Aggregation row of the builder
        defines at a point added, the rows read in order. An output whose
        rule holds it at a point of coordinates, `𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(𝑑𝑉≻(a)) ⟂ a ≥
        0` or `𝑚_d≻(a) = a + 𝑐≻(a)`, is a correspondence where its rule
        carries a clause or its carrier is a correspondence (`Xa ⇉ ℝ₊₊`): at
        a point, the test that a number passes where it lies in the
        carrier's codomain, where the carrier names one, and the rule holds
        with the output read as that number. It is a function otherwise,
        whose value at a point is the side of its rule opposite the output:
        the interior value, for an inequality without a clause. A name that
        `values` gives keeps the value given."""
        numbers = _numbers(values)
        for key in builder.primitives.list():
            if kind_of(builder.primitives[str(key)].box) != "Aggregation":
                continue
            record = builder.primitives[str(key)].denote()
            for wire in record.outputs:
                name = name_at_numbers(wire.identity)
                rules = [rule for rule in wire.rules if _point_of(rule, name) is not None]
                if name in numbers or not rules:
                    continue
                statement = getattr(rules[0], "statement", rules[0])
                if isinstance(statement, predicates.Complementarity) or "⇉" in wire.type:
                    codomain = getattr(wire.mathematical_type.carrier, "codomain", None)
                    # a correspondence's carrier is a map into the power set
                    # of the set that its values lie in, `Xa ⇉ ℝ₊₊`
                    if isinstance(codomain, typed_expressions.PowerSet):
                        codomain = codomain.domain
                    numbers[name] = self.correspondence(rules[0], name, numbers, codomain)
                else:
                    numbers[name] = self.function(rules[0], name, numbers)
        return numbers

    def rule(self, rule, values):
        """The truth of a rule at numbers: its clauses under `Where` read
        first, each giving the names on its left side the values of its
        right side, then, where its region note names a point of several
        coordinates, every function that its statement writes bare read at
        that point, then its statement. A rule is a `Rule` that a card prints
        or a statement alone."""
        return _value(getattr(rule, "statement", rule), _at_point(rule, _numbers(values)))

    def admitted(self, rule, output, values):
        """The values that a rule admits for its output at one point, as the
        test that a number passes: a number `x` is admitted where the rule
        holds with the output named `output` (`c≻`) read as `x` at the point
        that the numbers give."""
        return lambda x: self.rule(rule, {**values, output: lambda *point: x})

    def correspondence(self, rule, output, values, codomain=None):
        """The correspondence that a rule holds its output to: at a point,
        the test that a number `x` passes where it lies in `codomain` and the
        rule holds with the output read as `x` there; the point names the
        coordinates at which the rule reads the output."""
        names = _point_of(rule, output)

        def at(*point):
            numbers = {**values, **dict(zip(names, _spread(point)))}
            admitted = self.admitted(rule, output, numbers)
            return lambda x: (codomain is None or _member(x, codomain, numbers)) and admitted(x)

        return at

    def function(self, rule, output, values):
        """The function that a rule holds its output to: at a point, the
        value of the side of the rule opposite the output, read there."""
        names, core = _point_of(rule, output), _core(rule)
        sides = (getattr(core, "left", None), getattr(core, "right", None))

        def is_output(side):
            """Whether a side is the output at the point, applied to it or
            written bare where the region note names the point."""
            return _applies(side, output) or (
                _point_named(rule) is not None and output in _bare_names(side)
            )

        if not any(is_output(side) for side in sides):
            raise TypeError(f"the rule {rule!r} holds no side that is {output} at a point")
        other = sides[1] if is_output(sides[0]) else sides[0]
        return lambda *point: _value(
            other, _at_point(rule, {**values, **dict(zip(names, _spread(point)))})
        )

    def demand(self, relation, values):
        """What a relation on an unknown function demands at one point of its
        quantifier, the binders read at `values`: the pair `(argument,
        value)` of the equation `f(argument) = value` that the relation
        states there, or None where the number of a binder lies outside the
        set that it ranges over, so that the relation demands nothing there.
        `relation` is the set of functions that a relation defines, as
        `signature()` answers it: `{f ∈ F | ∀ a ∈ Xa, ∀ x ∈ 𝑐≻(a): f(a + x) =
        x}`."""
        numbers = _numbers(values)
        (unknown,) = _bound_names(relation.bound)
        (statement,) = relation.conds
        while isinstance(statement, terms.Operator) and statement.head == "forall":
            for binder in statement.subs:
                name = name_at_numbers(binder.var)
                if name not in numbers:
                    raise KeyError(f"the relation binds {name}, and the numbers give it no value")
                if not _member(numbers[name], binder.set, numbers):
                    return None
            (statement,) = statement.args
        left, right = _sides(statement)
        applied, value = (left, right) if _applies(left, unknown) else (right, left)
        if not _applies(applied, unknown):
            raise TypeError(f"the statement of the relation applies no {unknown}: {statement!r}")
        point = _spread(_value(argument, numbers) for argument in applied.args)
        return (point[0] if len(point) == 1 else point), _value(value, numbers)

    @staticmethod
    def one_function(demands):
        """Whether one function meets every demand: no two demands ask it for
        two values at one argument. A demand is a pair `(argument, value)`;
        None stands for no demand."""
        asked = {}
        for demand in demands:
            if demand is not None and asked.setdefault(demand[0], demand[1]) != demand[1]:
                return False
        return True


def name_of(written):
    """The term that a file writes as the bare name `written`."""
    return terms.Sym(terms.Constant(written))


@pytest.fixture(scope="session")
def at_numbers():
    """`at_numbers(term, values)`: a term of a stage read at numbers, with
    the readings `stage`, `rows`, `rule`, `admitted`, `correspondence`,
    `function`, `demand` and `one_function` of `ReadingAtNumbers`, so that a
    test states what a relation holds at points and not only how it
    prints."""
    return ReadingAtNumbers()


@pytest.fixture(scope="session")
def cons_without_clause():
    """`cons.bl` with its candidate line written without the clause, the
    inequality `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])`, which reads as the interior value
    at every saving."""
    return stage_from_text(
        candidate_text("cons_without_clause", CANDIDATE_LINE.replace(" ⟂ a >= 0", "")),
        "cons_without_clause.bl",
    )


@pytest.fixture(scope="session")
def cons_with_a_cap():
    """`cons.bl` with a cap `ā` on the saving beside the borrowing limit,
    written as the equation with the chain on the bounded quantity `−a`,
    `−ā ≤ −a ≤ 0`, whose residual has the sign that each bound requires."""
    line = "    c[>]   = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ -ā <= -a <= 0 :: [id=InvEuler]\n"
    return stage_from_text(
        candidate_text("cons_with_a_cap", line, "ā : ℝ₊₊\n"), "cons_with_a_cap.bl"
    )


@pytest.fixture(scope="module")
def durables_numbers(adjuster_cons_with_clause_on_candidate_line, at_numbers):
    """The numbers `DURABLES` with the definitions of the durables adjuster
    with its clause and the outputs of its policy builder's rows added."""
    stage = adjuster_cons_with_clause_on_candidate_line
    return at_numbers.rows(stage.builder.policy, at_numbers.stage(stage, DURABLES))


@pytest.fixture(scope="module")
def durables_memberships(adjuster_cons_with_clause_on_candidate_line):
    """The memberships that the rules of the joint solve of the durables
    adjuster with its clause hold and that read the candidate `c≻`."""
    rules = (
        adjuster_cons_with_clause_on_candidate_line.builder.policy["choice:Aggregation"]
        .denote()
        .outputs[0]
        .rules
    )
    return [
        term
        for rule in rules
        for term in terms_inside(rule)
        if isinstance(term, predicates.Member) and reads(term, "c≻")
    ]


def durables_point(numbers, m, z_d, c, h_choice):
    """The numbers at the decision point `(m, z_d, c, h_choice)`, with the
    outputs of the law of motion there under the names that the line under
    `Where` gives them."""
    a, h, z = numbers["dcsn_to_cntn"](m, z_d, c, h_choice)
    return {
        **numbers,
        "m": m,
        "z_d": z_d,
        "c": c,
        "h_choice": h_choice,
        "a_nxt_adj": a,
        "h_nxt_adj": h,
        "z_nxt_adj": z,
    }


@pytest.mark.parametrize(
    "name, held",
    [
        pytest.param(
            "cons_with_egm_lines", [True, True, True, True, False, False, False], id="clause"
        ),
        pytest.param(
            "cons_without_clause", [False, False, True, True, False, False, False], id="no-clause"
        ),
    ],
)
def test_the_identification_demands_the_policy_at_the_pairs_its_candidate_admits(
    request, at_numbers, name, held
):
    """The identification demands 𝑐(m) = x at a pair (m, x) of `PAIRS`
    exactly where the candidate line admits x at the saving m − x: at the
    corner and the interior pairs with the clause, at the interior pairs
    alone without it."""
    stage = request.getfixturevalue(name)
    calibration = at_numbers.stage(stage, {**RHO_IS_TWO, "D_{a}V≻": lambda a: 1})
    numbers = at_numbers.rows(stage.builder.policy, calibration)
    relation = identification(stage)
    demanded = [
        at_numbers.demand(relation, {**numbers, "a": a, "x": pair[1]}) == pair for a, pair in PAIRS
    ]
    assert demanded == held, stage.name


def test_the_identification_has_no_solution_where_two_admitted_pairs_share_a_cash_on_hand(
    cons_with_egm_lines, at_numbers
):
    """Where an interior pair and a corner pair have one cash on hand and two
    consumptions, the identification demands two values of the policy there,
    which no function meets."""
    # at ρ = 2 and D_{a}𝑉≻(a) = (1 − 2a)⁻², the interior value at the saving
    # 1/8 is ((1 − 1/4)⁻²)^(−1/2) = 3/4, and the corner at zero saving admits
    # 7/8; both give the cash on hand 7/8, so the identification demands
    # 𝑐(7/8) = 3/4 and 𝑐(7/8) = 7/8
    marginal_value = {**RHO_IS_TWO, "D_{a}V≻": lambda a: (1 - 2 * Fraction(a)) ** -2}
    numbers = at_numbers.rows(
        cons_with_egm_lines.builder.policy, at_numbers.stage(cons_with_egm_lines, marginal_value)
    )
    demands = [
        at_numbers.demand(identification(cons_with_egm_lines), {**numbers, "a": a, "x": x})
        for a, x in ((Fraction(1, 8), Fraction(3, 4)), (0, Fraction(7, 8)))
    ]
    assert demands == [(Fraction(7, 8), Fraction(3, 4)), (Fraction(7, 8), Fraction(7, 8))]
    assert not at_numbers.one_function(demands) and at_numbers.one_function(demands[:1])


@pytest.mark.parametrize("relation, bound", CLAUSE_WRITINGS)
def test_the_regions_of_a_clause_agree_with_its_kuhn_tucker_condition_at_numbers(
    at_numbers, relation, bound
):
    """The split of the clause of a candidate line into its regions holds
    exactly where its Kuhn–Tucker condition holds, at every saving of
    `SAVINGS` and every consumption of `CONSUMPTIONS`."""
    stage = clause_stage(relation, bound)
    numbers = at_numbers.stage(stage, {**RHO_IS_TWO, "D_{a}V≻": 1})
    condition, regions = clause_condition_and_regions(stage)
    for a, x in itertools.product(SAVINGS, CONSUMPTIONS):
        point = {**numbers, "a": a, "c≻": x}
        assert at_numbers(regions, point) == at_numbers(condition, point), (a, x)


def test_a_clause_on_a_strict_relation_admits_no_point_of_positive_saving(at_numbers):
    """The clause `c[>] < 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0` admits no point of
    positive saving, in its Kuhn–Tucker condition and in its regions, since
    a strict relation admits no zero residual."""
    stage = clause_stage("<", "a >= 0")
    numbers = at_numbers.stage(stage, {**RHO_IS_TWO, "D_{a}V≻": 1})
    condition, regions = clause_condition_and_regions(stage)
    # the residual 0 and the slack 1
    point = {**numbers, "a": 1, "c≻": 1}
    assert not at_numbers(condition, point) and not at_numbers(regions, point)
    assert not any(
        at_numbers(regions, {**numbers, "a": a, "c≻": x})
        for a, x in itertools.product((1, 2, 3), CONSUMPTIONS)
    )


def test_a_chain_with_its_endpoints_reversed_admits_no_point(at_numbers):
    """The chain `2 <= a <= 1`, whose lower bound lies above its upper bound,
    admits no point in its Kuhn–Tucker condition or in its regions, since no
    saving meets both bounds."""
    stage = clause_stage("=", "2 <= a <= 1")
    numbers = at_numbers.stage(stage, {**RHO_IS_TWO, "D_{a}V≻": 1})
    condition, regions = clause_condition_and_regions(stage)
    # the saving 2 and the residual 1: the lower slack is zero and the upper
    # slack negative
    point = {**numbers, "a": 2, "c≻": 2}
    assert not at_numbers(condition, point) and not at_numbers(regions, point)
    assert not any(
        at_numbers(regions, {**numbers, "a": a, "c≻": x})
        for a, x in itertools.product(SAVINGS, CONSUMPTIONS)
    )


def test_a_cap_written_on_minus_the_saving_admits_values_above_the_candidate_where_it_binds(
    cons_with_a_cap, at_numbers
):
    """The cap written as the chain `−ā ≤ −a ≤ 0` on the candidate line, read
    at ā = 2 and the saving 2, where the cap binds, admits the consumption
    3, above the interior value 1, and not the consumption 1/2, in its
    Kuhn–Tucker condition and in its regions alike."""
    numbers = at_numbers.stage(cons_with_a_cap, {**RHO_IS_TWO, "ā": 2, "D_{a}V≻": 1})
    admitted = [
        (
            at_numbers(form, {**numbers, "a": 2, "c≻": 3}),
            at_numbers(form, {**numbers, "a": 2, "c≻": Fraction(1, 2)}),
        )
        for form in clause_condition_and_regions(cons_with_a_cap)
    ]
    assert admitted == [(True, False), (True, False)]


def test_the_durables_candidate_with_its_clause_admits_one_value_or_a_segment(
    durables_numbers,
):
    """With the clause, the candidate of the durables adjuster admits at a
    positive saving the interior value alone, 𝑢_c_inv(β·𝑑𝑉_a≻(3, h′, z′)) =
    𝑢_c_inv(1/8) = 2, and at the borrowing limit the segment (0,
    𝑢_c_inv(β)] = (0, 1]."""
    admitted = durables_numbers["c≻"]
    # the arguments of `admitted` are the saving, the housing and the shock
    assert [admitted(3, Fraction(1, 8), 1)(x) for x in (1, 2, 3)] == [False, True, False]
    assert [
        admitted(BORROWING_LIMIT, Fraction(1, 8), 1)(x)
        for x in (Fraction(1, 6), 1, Fraction(7, 3))
    ] == [True, True, False]


def test_the_first_residual_of_the_durables_solve_is_one_membership_in_the_admitted_values(
    durables_memberships,
):
    """The memberships that read the candidate `c≻` in the rules of the
    joint solve of the durables adjuster are one term, the consumption in
    the values that the candidate admits."""
    assert durables_memberships
    assert all(term == durables_memberships[0] for term in durables_memberships)


@pytest.mark.parametrize("h, c_star, decision_point, passes", HOUSING_CHOICES)
def test_at_the_borrowing_limit_the_membership_agrees_with_the_test_of_a_durables_solver(
    adjuster_cons_with_clause_on_candidate_line,
    durables_numbers,
    durables_memberships,
    at_numbers,
    h,
    c_star,
    decision_point,
    passes,
):
    """At a decision point whose saving is the borrowing limit and whose
    consumption solves the housing condition, the membership of the first
    residual holds exactly where the test 𝑢_c(c*) ≥ β·𝑑𝑉_a≻(b, h′, z′) of an
    endogenous grid solver of the durables model passes."""
    numbers = durables_numbers
    m, z_d, c, h_choice = decision_point
    # the law of motion takes the decision point to the borrowing limit
    assert numbers["dcsn_to_cntn"](m, z_d, c, h_choice) == (BORROWING_LIMIT, h, z_d)
    # the housing condition holds at c*: the second residual, r₂, is zero
    rules = (
        adjuster_cons_with_clause_on_candidate_line.builder.policy["choice:Aggregation"]
        .denote()
        .outputs[0]
        .rules
    )
    (housing,) = [
        rule for rule in rules if name_at_numbers(getattr(rule.statement, "left", None)) == "r₂"
    ]
    point = durables_point(numbers, m, z_d, c, h_choice)
    assert at_numbers.rule(housing, {**point, "r₂": 0})
    marginal_value = DURABLES["D_{a_nxt_adj}V≻"](BORROWING_LIMIT, h, z_d)
    test = numbers["𝑢_c"](c_star) >= numbers["β"] * marginal_value
    assert test is passes and at_numbers(durables_memberships[0], point) is passes, h


@pytest.mark.parametrize(
    "c, holds",
    [pytest.param(2, True, id="the-candidate"), pytest.param(1, False, id="below-the-candidate")],
)
def test_at_a_positive_saving_the_membership_holds_at_the_candidate_alone(
    durables_numbers, durables_memberships, at_numbers, c, holds
):
    """At the saving 3 and the housing 1/8, where the candidate is 2, the
    membership of the first residual holds at the consumption 2 and not at
    the consumption 1."""
    # the decision point (m, z_d, c, h_choice) with m = c + a + (1 + τ)·h′,
    # the saving a = 3, τ = 1 and h′ = 1/8
    point = durables_point(durables_numbers, c + 3 + 2 * Fraction(1, 8), 1, c, Fraction(1, 8))
    assert at_numbers(durables_memberships[0], point) is holds


@pytest.mark.parametrize("name, values, definition, arguments, value", DEFINITIONS_AT_NUMBERS)
def test_a_definition_of_a_stage_read_at_numbers_gives_its_value(
    request, at_numbers, name, values, definition, arguments, value
):
    """A function or a law of motion that a stage file defines, read at
    numbers, gives at a point the value of its formula there, exactly."""
    numbers = at_numbers.stage(request.getfixturevalue(name), values)
    assert numbers[definition](*arguments) == value


def test_the_feasible_set_of_the_consumption_stage_read_at_numbers_is_the_segment_up_to_1(
    cons_with_egm_lines, at_numbers
):
    """The feasible set `Γ(m_d) := (0, m_d]` of the consumption stage, read
    at the cash on hand 1, admits 1/2 and 1 and neither 0 nor 2."""
    numbers = at_numbers.stage(cons_with_egm_lines, RHO_IS_TWO)
    assert [numbers["Γ"](1)(x) for x in (0, Fraction(1, 2), 1, 2)] == [False, True, True, False]


def test_a_clause_read_at_numbers_admits_one_value_where_slack_and_a_segment_where_binding(
    at_numbers,
):
    """The clause `x ≤ 1 ⟂ a ≥ 0` read as its Kuhn–Tucker condition admits
    the value 1 alone at a positive saving and every value up to 1 at zero
    saving."""
    clause = predicates.Complementarity(
        predicates.Compare(name_of("x"), "<=", terms.Number(1)),
        terms.Rel(name_of("a"), terms.Ge(), terms.Number(0)),
    )
    points = ((1, 1), (1, Fraction(1, 2)), (0, Fraction(1, 2)), (0, 2))
    assert [at_numbers(clause, {"a": a, "x": x}) for a, x in points] == [True, False, True, False]


def test_the_reader_at_numbers_raises_key_error_for_a_name_that_the_numbers_do_not_give(
    at_numbers,
):
    """The reader `at_numbers` raises `KeyError` where the numbers give no
    value to a name that the term reads."""
    with pytest.raises(KeyError):
        at_numbers(name_of("ρ"), {})


def test_a_comprehension_read_at_numbers_holds_the_points_that_meet_its_conditions(at_numbers):
    """The budget set `Γ(z) = {q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z}` read at
    z = 3 holds (1, 2, 0) and not (1, 1, 0), whose first two coordinates sum
    to 2, nor (1, 2, −1), whose third coordinate is negative."""
    numbers = at_numbers.stage(stage_from_text(BUDGET_SET, "budget_set.bl"), {})
    points = ((1, 2, 0), (1, 1, 0), (1, 2, -1))
    assert [numbers["Γ"](3)(point) for point in points] == [True, False, False]
