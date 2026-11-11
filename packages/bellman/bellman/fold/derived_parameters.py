"""The derived parameters of a stage (AMD-MT-003, build contract §5).

A derived parameter is a constant of the stage that a definition without
arguments writes from the stage's parameters, `h := 1/(1 - Γ/R)`. Its
definition reads declared parameters, finite numbers and other derived
parameters, and it is formed by signs, sums, differences, products,
quotients, powers and the two calls `log` and `exp`. The calibration supplies
no value for it: its value is its definition evaluated at the values the
calibration binds, after the derived parameters it reads. Which definitions
are derived parameters is decided by the outermost form of the right side
(`typing.declarations.derived_parameter_body`), so that the typing walk and
the fold read one rule; this module checks what a derived parameter's
definition reads and evaluates it.

- `derived_order` answers the derived parameters of a definitions table, each
  after those it reads, and refuses at elaboration a definition that reads a
  name other than a declared parameter or a derived parameter, that calls a
  function other than `log` or `exp`, that writes any other form, or that
  reaches itself through the derived parameters it reads.
- `derived_value` evaluates one definition's term at numbers by the rules of
  real arithmetic: a divisor is not zero; the argument of `log` is positive;
  a power with an integer exponent is defined at every base but zero, where
  the exponent is positive; a power with a noninteger exponent requires a
  positive base; and every value is a finite real number. A value that a
  floating-point operation rounds to zero satisfies no requirement of a
  positive number.
- `derived_values` answers the value of every derived parameter of a stage at
  the calibration values and refuses, at the definition whose arithmetic
  fails, a calibration at which a definition has no value.

The refusals are made under the rule `derived-parameter`.
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Mapping
from typing import NamedTuple

from bellman.refusals import construction_error
from bellman.syntax import terms as T
from bellman.syntax.lower import span_at
from bellman.syntax.source import to_source
from bellman.typing.declarations import (
    DERIVED_PARAMETER_CALLS,
    derived_parameter_fault,
    derived_parameters_read,
)

__all__ = ("derived_order", "derived_value", "derived_values")

# the rule of every refusal this module makes
_RULE = "derived-parameter"


# --- the order of the derived parameters, and what each may read ---


def derived_order(definitions, spans=None):
    """The derived parameters of a definitions table, the records of kind
    `derived_parameter`, in an order in which each follows the derived
    parameters it reads, file order otherwise. `definitions` holds the
    records of the table, as a mapping by identity or as a sequence.

    Refused under `derived-parameter`, at the definition: a name its
    definition reads that is neither a declared parameter nor a derived
    parameter, such as a setting, a shock, a field, a set, a function or
    `inf`; a call of a function other than `log` or `exp`, or of either with
    other than one argument; any other form, such as an expectation or a
    selection; a number that is not finite (`derived_parameter_fault`); and a
    cycle among the derived parameters. The declaration pass makes the same
    check before any line is read and refuses a cycle among the definitions
    under `definition-order`, so that on a stage under construction these
    refusals are made there first. `spans`, the span table of a fresh parse,
    positions a refusal at the definition's text; without it the refusal
    names the definition's file position alone."""
    records = tuple(definitions.values() if isinstance(definitions, Mapping) else definitions)
    derived = {d.identity.field: d for d in records if d.kind == "derived_parameter"}
    if not derived:
        return ()
    parameters = {d.identity.field for d in records if d.kind == "parameter"}
    kinds = _kinds(records)
    for name, definition in derived.items():
        refused = derived_parameter_fault(
            name, definition.equations[0], parameters, derived, kinds
        )
        if refused is not None:
            raise _refusal(definition, *refused, spans)
    order, done, active = [], set(), []

    def visit(name):
        if name in done:
            return
        if name in active:
            cycle = active[active.index(name) :] + [name]
            chain = ", ".join(f"{one} reads {other}" for one, other in zip(cycle, cycle[1:]))
            raise _refusal(
                derived[name],
                f"the derived parameters form a cycle: {chain}; each derived parameter is "
                "evaluated after the derived parameters it reads, which a cycle does not allow",
                "Define one derived parameter of the cycle from declared parameters and numbers",
                spans,
            )
        active.append(name)
        for other in derived_parameters_read(derived[name].equations[0], derived):
            visit(other)
        active.pop()
        done.add(name)
        order.append(derived[name])

    for name in derived:
        visit(name)
    return tuple(order)


def _kinds(records):
    """The kind of each name of the definitions table that no derived
    parameter's definition may read, as `derived_parameter_fault` names it: a
    setting, a set, a function, a correspondence, a shock or a multiplier."""
    kinds = {
        "setting": "setting",
        "set": "set",
        "function": "function",
        "function_alias": "function",
        "correspondence": "correspondence",
        "multiplier": "multiplier",
    }
    found = {}
    for record in records:
        if record.kind == "distribution":
            for subject in record.identity.subjects:
                found.setdefault(subject, "shock")
        elif record.kind in kinds:
            found.setdefault(record.identity.field, kinds[record.kind])
    return found


def _refusal(definition, message, write, spans):
    """The refusal under `derived-parameter` of one derived parameter's
    definition, positioned at its text where `spans` holds it and named by
    its file position."""
    return construction_error(
        message,
        stage=definition.identity.stage,
        address=definition.address,
        span=span_at(definition.address, spans),
        rule=_RULE,
        write=write,
    )


# --- the value of a definition at numbers ---


class _Value(NamedTuple):
    """A number a definition's term takes, and whether a floating-point
    operation rounded a nonzero result to zero on the way to it."""

    number: float
    underflowed: bool = False


class _Undefined(ValueError):
    """A term that has no finite real value at the numbers, with the sentence
    that says which operation fails and why."""


def derived_value(term, values):
    """The number a derived parameter's definition `term` takes at `values`,
    a mapping from each name the term reads to its number, as a float.

    The arithmetic is that of the real numbers, computed in floating point. A
    divisor is not zero; the argument of `log` is positive; a power with an
    integer exponent is defined at every base except zero, where its exponent
    is positive; a power with a noninteger exponent requires a positive base;
    and the value of every operation is a finite real number. A number that
    a floating-point operation rounds to zero from a nonzero result satisfies
    no requirement of a positive number. A term that breaks one of these
    rules, that reads a name `values` does not bind or binds to a value that
    is no finite real number, or that holds another form, raises a
    `ValueError` whose sentence names the operation and the numbers."""
    return _evaluated(term, values).number


def _evaluated(term, values):
    """The `_Value` of a term at the numbers, refused as `derived_value`
    refuses."""
    if isinstance(term, T.Number):
        return _Value(_finite(term.value, f"the number {term.value!r}"))
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        name = term.symbol.name
        if name not in values:
            raise _Undefined(f"{name} has no value")
        return _Value(_finite(values[name], f"the value {values[name]!r} of {name}"))
    if isinstance(term, T.Neg):
        operand = _evaluated(term.operand, values)
        return _Value(-operand.number, operand.underflowed)
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div)):
        left, right = _evaluated(term.left, values), _evaluated(term.right, values)
        return _arithmetic(term, left, right, values)
    if isinstance(term, T.Pow):
        base, exponent = _evaluated(term.base, values), _evaluated(term.exponent, values)
        return _power(term, base, exponent, values)
    if isinstance(term, T.Call) and term.fun in DERIVED_PARAMETER_CALLS and len(term.args) == 1:
        return _elementary(term, _evaluated(term.args[0], values), values)
    raise _Undefined(f"`{to_source(term)}` is no form a derived parameter's definition admits")


def _arithmetic(term, left, right, values):
    """The value of a sum, a difference, a product or a quotient of two
    values."""
    a, b = left.number, right.number
    if isinstance(term, T.Div) and b == 0:
        raise _Undefined(
            f"the divisor `{to_source(term.right)}` is {b!r}{_by_underflow(right)}"
            f"{_at(term.right, values)}, and a division by zero has no value"
        )
    if isinstance(term, T.Add):
        number, underflowed = a + b, left.underflowed or right.underflowed
    elif isinstance(term, T.Sub):
        number, underflowed = a - b, left.underflowed or right.underflowed
    elif isinstance(term, T.Mul):
        number = a * b
        underflowed = (a != 0 and b != 0) or left.underflowed or right.underflowed
    else:
        number = a / b
        underflowed = a != 0 or left.underflowed
    return _Value(_result(number, term, values), underflowed and number == 0)


def _power(term, base, exponent, values):
    """The value of a power: with an integer exponent at every base but zero,
    where the exponent is positive, and with a noninteger exponent at a
    positive base."""
    b, e = base.number, exponent.number
    written = f"the power `{to_source(term)}` has the base {b!r}{_by_underflow(base)}"
    if not e.is_integer() and not b > 0:
        raise _Undefined(
            f"{written} and the exponent {e!r}, which is no integer{_at(term, values)}; a power "
            "with a noninteger exponent requires a positive base"
            + (", which numeric underflow does not supply" if base.underflowed else "")
        )
    if b == 0 and not e > 0:
        raise _Undefined(
            f"{written} and the exponent {e!r}{_at(term, values)}; a power of zero is defined "
            "for a positive exponent alone"
        )
    try:
        number = b**e
    except OverflowError:
        raise _Undefined(
            f"the power `{to_source(term)}`{_at(term, values)} exceeds the largest finite "
            "floating-point number"
        ) from None
    return _Value(_result(number, term, values), number == 0 and (b != 0 or base.underflowed))


def _elementary(term, argument, values):
    """The value of `log` of a positive argument or of `exp`."""
    x = argument.number
    if term.fun == "log":
        if not x > 0:
            raise _Undefined(
                f"the argument `{to_source(term.args[0])}` of log is {x!r}"
                f"{_by_underflow(argument)}{_at(term.args[0], values)}, and log is defined at "
                "positive numbers alone"
                + (", which numeric underflow does not supply" if argument.underflowed else "")
            )
        return _Value(math.log(x))
    try:
        number = math.exp(x)
    except OverflowError:
        raise _Undefined(
            f"`{to_source(term)}`{_at(term, values)} exceeds the largest finite floating-point "
            "number"
        ) from None
    return _Value(number, number == 0)


def _result(number, term, values):
    """The value of one operation where it is a finite real number, refused
    otherwise."""
    if not math.isfinite(number):
        raise _Undefined(
            f"the value of `{to_source(term)}`{_at(term, values)} is {number!r}, which is no "
            "finite real number"
        )
    return number


def _finite(value, words):
    """A number of the term, a literal or a name's value, as a float where it
    is a finite real number, refused otherwise."""
    if not _is_real_number(value):
        raise _Undefined(f"{words} is no real number")
    try:
        number = float(value)
    except OverflowError:
        raise _Undefined(f"{words} exceeds the largest finite floating-point number") from None
    if not math.isfinite(number):
        raise _Undefined(f"{words} is no finite number")
    return number


def _is_real_number(value):
    """Whether a value is a real number and no boolean."""
    return isinstance(value, numbers.Real) and not isinstance(value, bool)


def _by_underflow(value):
    """The words that say a zero is a nonzero result that floating point
    rounded to zero, and nothing for a zero of the arithmetic itself."""
    return " by floating-point underflow" if value.underflowed and value.number == 0 else ""


def _at(term, values):
    """The values of the names a term reads, ` at Γ = 1.04, R = 1.04`, or
    nothing for a term that reads none."""
    names = []
    for node in _nodes(term):
        if isinstance(node, T.Sym) and isinstance(node.symbol, T.Constant):
            name = node.symbol.name
            if name in values and name not in names:
                names.append(name)
    return " at " + ", ".join(f"{name} = {values[name]!r}" for name in names) if names else ""


def _nodes(term):
    """The nodes of an arithmetic term, the term first."""
    yield term
    if isinstance(term, T.Neg):
        yield from _nodes(term.operand)
    elif isinstance(term, T.Pow):
        yield from _nodes(term.base)
        yield from _nodes(term.exponent)
    elif isinstance(term, (T.Add, T.Sub, T.Mul, T.Div)):
        yield from _nodes(term.left)
        yield from _nodes(term.right)
    elif isinstance(term, T.Call):
        for argument in term.args:
            yield from _nodes(argument)


# --- the values of a stage's derived parameters at a calibration ---


def derived_values(stage, values):
    """The value of each derived parameter of the stage at the calibration
    values `values`, a mapping from each declared parameter to its number, by
    name and in file order: each definition evaluated by `derived_value` at
    the declared values and the derived values computed before it, in the
    order `derived_order` answers. A definition that has no value at the
    numbers is refused under `derived-parameter` at that definition, naming
    the operation that fails and the numbers it reads, so that the failure
    of a derived parameter another one reads is reported at its own
    definition."""
    order = derived_order(stage.definitions)
    found = {}
    for definition in order:
        name, term = definition.identity.field, definition.equations[0]
        try:
            found[name] = derived_value(term, {**values, **found})
        except _Undefined as fault:
            raise construction_error(
                f"with the calibration values, the derived parameter {name}, defined as "
                f"`{to_source(term)}`, has no value: {fault}; a derived parameter's value is "
                "its definition evaluated at the calibration, a finite real number",
                stage=stage.name,
                address=definition.address,
                span=None,
                rule=_RULE,
                write=f"Write parameter values at which the definition of {name} has a finite "
                "real value",
            ) from None
    return {
        d.identity.field: found[d.identity.field]
        for d in stage.definitions.values()
        if d.kind == "derived_parameter"
    }
