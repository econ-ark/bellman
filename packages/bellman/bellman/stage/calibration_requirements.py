"""The check of parameter values against the declared sets of the parameter
definitions.

The membership of a value in a declared set is decided from the one table of
the primitive sets, `vocabulary.PRIMITIVE_SETS`, and the endpoints `sets.py`
reads, so that a set has one table and one reading (AMD-SG-017 §5.11). A set
the module keeps no entry for is a set the file defines, or a set the file
does not define; in the second case the membership is not decided, by the
fall-through rule of AMD-SG-016 §4. A bare `R` is therefore the named set
`R`, and no spelling of ℝ.

A value of a parameter declared on a product, `ℝ₊ × ℝ₊ × ℝ₊`, is a sequence
of one entry per factor, each in its factor's set. A value of a collection,
`q : I → A`, is a function on the index set `I` at the values: a sequence of
one entry per member in the set's order, or a mapping keyed by the members,
each entry in `A`, level by level for a product domain; a wrong count, a
missing or surplus key and an entry outside its set are refused, naming the
parameter and the key or ordered pair. A value of a parameter declared on an
integer range or a listed set of numbers is one member of the set at the
values. The members, the counts and the key positions are those of
`typing.sets`, which the connections and the compiled selections read too.
"""

import math
import operator
from collections.abc import Mapping, Sequence

from bellman.fold.block_lines import parameter_sets
from bellman.native.identity import Identity
from bellman.native.predicates import And, Compare, IsInteger, Member, Not, Or
from bellman.native.records import UNDECLARED_SET, Condition
from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import condition_text, to_source
from bellman.syntax.vocabulary import INTEGER, PRIMITIVE_SETS
from bellman.typing import sets

# --- the check of the parameter values against their declared sets ---


def calibration_requirements(stage, values):
    """The memberships a calibration leaves to be established: a missing
    value and a value outside its declared set are refused, and a membership
    this module does not decide is answered as a required
    `calibration-domain-membership` obligation.

    The checker reads the retained set terms of the declared parameter
    domains (a reserved glyph, a named set of the definitions table, an
    interval whose endpoints are numbers or valued parameters, a finite set
    of labels, an integer range, a listed set of numbers, a product, a set
    of functions and a set with conditions, whose conditions compare terms of
    numbers and valued parameters). It does not interpret equations,
    functions or source strings. Every declared parameter needs a value. A
    value for a derived parameter, which its definition gives, is refused
    under `derived-parameter` at the definition (AMD-MT-003, build contract
    §5).

    Where a set reads another parameter, as a bound or as an endpoint, a
    faulty value is refused at its own parameter and not at the parameter
    whose set reads it, in whatever order the file declares the two
    (`judged`; AMD-GRAM-004 §4).
    """
    definitions = dict(stage.definitions)
    _refuse_derived_values(stage, definitions, values)
    declared = parameter_sets(stage)
    # a parameter declared without a set lies in the reals
    sets_judged = {name: setexpr or T.Named("ℝ") for name, setexpr in declared.items()}
    undecided = set()
    for name, status, reason in judged(stage, definitions, sets_judged, values):
        if status is True:
            continue
        identity = Identity("parameter", stage=stage.name, field=name)
        # a refusal says where, what happened, why and what to write
        # (AMD-SG-006 §6a)
        where = (
            f"stage {stage.name!r}, parameter {name!r} "
            f"(address {_parameter_address(stage, identity)!r})"
        )
        if status is UNVALUED:
            raise ValueError(
                f"{where}: the calibration source supplies no value for it; every declared "
                "parameter is valued when values are bound (AMD-SG-006 §4, "
                f"rule 8); write `{name}: <value>` in the calibration source"
            )
        if status is False:
            raise ValueError(_outside(where, declared[name], values[name], reason))
        undecided.add(name)
    return tuple(
        Condition(
            condition="calibration-domain-membership",
            entries=(
                Identity("parameter", stage=stage.name, field=name),
                declared_set_reference(stage, setexpr),
            ),
            status="required",
            explanation=f"The value {values[name]!r} of {name} "
            f"must belong to {to_source(setexpr)}.",
        )
        for name, setexpr in declared.items()
        if name in undecided
    )


def judged(stage, definitions, declared, values, settled=None):
    """The membership of each value in its declared set, as `(name, status,
    reason)` in the order in which a refusal is to be given. `declared` maps
    each name to its set, None for a name with no set to judge; `values`
    holds the value of each name; and `settled` holds the values of an
    earlier binding, the calibration where settings are judged. The status
    is that of `membership` at all the values, or `UNVALUED` for a name
    `values` does not hold.

    A set may read another name, as a bound or as an endpoint, `β : (0,1) @
    (0, R)`, so a value may lie outside its set only because a value it
    reads is faulty. The faulty names that stand first are therefore those
    without a value and those whose value lies outside its set also when the
    other faulty values are left out, in the order of the file: a faulty
    value is refused at its own name, and not at a name whose set reads it,
    in whatever order the file declares the two (AMD-GRAM-004 §4). The other
    names follow in the order of the file, so that where every faulty value
    reads another, the first of the file is named."""
    everything = {**(settled or {}), **values}

    def judge(name, at):
        if name not in values:
            return UNVALUED, ""
        if declared[name] is None:
            return True, ""
        return membership(stage, definitions, declared[name], values[name], at)

    answers = {name: judge(name, everything) for name in declared}
    faulty = [
        name for name, (status, _) in answers.items() if status is False or status is UNVALUED
    ]
    first = []
    for name in faulty:
        others = {
            read: value for read, value in everything.items() if read == name or read not in faulty
        }
        status, reason = judge(name, others)
        if status is False or status is UNVALUED:
            # the reason names what the value breaks by itself
            answers[name] = (status, reason)
            first.append(name)
    return [
        (name, *answers[name])
        for name in first + [name for name in declared if name not in first]
    ]


def _outside(where, setexpr, value, reason):
    """The sentence that refuses a parameter's value outside its declared
    set: where, why and what to write."""
    declared = "ℝ" if setexpr is None else to_source(setexpr)
    reason = reason or f"the value {value!r} lies outside the declared set {declared}"
    return (
        f"{where}: {reason}; a parameter's value lies in the set its declaration names "
        f"(AMD-SG-006 §2, the parameter record); write a value in {declared}"
    )


def _refuse_derived_values(stage, definitions, values):
    """The refusal of a calibration source that supplies a value for a
    derived parameter, `h := 1/(1 - Γ/R)`, whose value is its definition
    evaluated at the calibration: under `derived-parameter`, at the
    definition, naming the definition."""
    for definition in definitions.values():
        name = definition.identity.field
        if definition.kind != "derived_parameter" or name not in values:
            continue
        raise ConstructionError(
            f"stage {stage.name!r}, derived parameter {name!r}: the calibration source supplies "
            f"the value {values[name]!r} for {name}, which the stage defines as "
            f"`{to_source(definition.equations[0])}`; a derived parameter takes its value from "
            "its definition at the calibration, and the calibration supplies none",
            stage=stage.name,
            address=definition.address,
            rule="derived-parameter",
            write=f"Remove {name} from the calibration source",
        )


def collection_values(stage, values):
    """The calibration values with every collection written as a mapping
    replaced by the sequence of its entries in the order of the members of
    its index set at the values, level by level, so that the version binds
    one representation and a compiled kernel reads an array; a value that
    is no collection, or that the checks have not admitted, is left as it
    is."""
    definitions = dict(stage.definitions)
    set_terms = _set_terms(definitions)
    bound = dict(values)
    for name, setexpr in parameter_sets(stage).items():
        if name in bound and setexpr is not None:
            bound[name] = _sequenced(setexpr, bound[name], values, set_terms)
    return bound


def _sequenced(setexpr, value, values, set_terms):
    """A collection's value as nested sequences in member order, where the
    declared set is a set of functions and the members are decided; the value
    unchanged otherwise."""
    indexed = sets.index_sets(setexpr, set_terms)
    if indexed is None:
        return value
    first, rest = indexed
    members = sets.finite_members(first, values, set_terms)
    if members is None:
        return value
    if isinstance(value, Mapping):
        entries = []
        for member in members:
            key = next((k for k in value if sets.key_position((member,), k) == 0), None)
            if key is None:
                return value
            entries.append(value[key])
    elif isinstance(value, Sequence) and not isinstance(value, str) and len(value) == len(members):
        entries = list(value)
    else:
        return value
    return tuple(_sequenced(rest, entry, values, set_terms) for entry in entries)


# the answer of a membership the module does not decide
_UNDECIDED = object()

# the answer for a name the values do not hold
UNVALUED = object()


def declared_set_terms(stage):
    """The sets a stage defines by name, through which the predicates decided
    at calibration read a named set."""
    return _set_terms(stage.definitions)


def _set_terms(definitions):
    """The sets a stage defines by name, through which a name is read."""
    return {
        identity.field: definition.equations[0]
        for identity, definition in definitions.items()
        if definition.kind == "set" and definition.equations
    }


def membership(stage, definitions, setexpr, value, values, active=frozenset(), path=()):
    """Whether a value lies in a declared set: `(True, "")`, `(False,
    reason)` or `(_UNDECIDED, "")`, which the check of the parameter values
    at calibration and the check of the declared settings at configuration
    (`binding_verbs`) both read. A primitive set is read from its domain,
    a set the file defines through its definition, an interval from its
    endpoints at the values, a finite set of labels from its members, an
    integer range or a listed set from its members at the values, a product
    entry by entry, a set of functions key by key and a set with conditions
    from its base and its conditions at the values (`_conditioned`); an
    extended real, a set the file does not define and any other form are not
    decided. `path`
    names the keys that lead to the value inside a collection, for the
    reason of a refusal."""
    set_terms = _set_terms(definitions)
    at = _at(path)

    def outside(declared):
        if path:
            return False, f"the entry{at} {value!r} lies outside {declared}"
        return False, f"the value {value!r} lies outside the declared set {declared}"

    if isinstance(setexpr, T.Space):
        return membership(stage, definitions, setexpr.set, value, values, active, path)
    if isinstance(setexpr, T.Named):
        primitive = PRIMITIVE_SETS.get(setexpr.name)
        if primitive is not None:
            # an extended real carries no domain, so its membership is a
            # membership the module does not decide
            if primitive.domain is None:
                return _UNDECIDED, ""
            answer = _in_primitive_domain(primitive.domain, value)
            return (answer, "") if answer is not False else outside(setexpr.name)
        identity = Identity("set", stage=stage.name, field=setexpr.name)
        if identity in active:
            return _UNDECIDED, ""
        definition = definitions.get(identity)
        if definition is None or definition.kind != "set":
            return _UNDECIDED, ""
        return membership(
            stage, definitions, definition.equations[0], value, values, active | {identity}, path
        )
    if isinstance(setexpr, T.Interval):
        if not _is_number(value):
            return outside(to_source(setexpr))
        bounds = sets.endpoints(setexpr)
        if bounds is None:
            bounds = _valued_endpoints(setexpr, values)
        if bounds is None:
            return _UNDECIDED, ""
        lower, lower_closed, upper, upper_closed = bounds
        left_ok = value >= lower if lower_closed else value > lower
        right_ok = value <= upper if upper_closed else value < upper
        return (True, "") if left_ok and right_ok else outside(to_source(setexpr))
    if isinstance(setexpr, T.FiniteSet):
        if isinstance(value, bool):
            member = "true" if value else "false"
            return (True, "") if member in setexpr.members else outside(to_source(setexpr))
        if isinstance(value, str) and not isinstance(value, bool) and value in setexpr.members:
            return True, ""
        return outside(to_source(setexpr))
    if isinstance(setexpr, (T.IntegerRange, T.Points)):
        members = sets.finite_members(setexpr, values, set_terms)
        if members is None:
            return _UNDECIDED, ""
        if not sets.is_number(value):
            return False, f"the value{at} {value!r} is no number of {to_source(setexpr)}"
        if sets.key_position(members, value) is None:
            return (
                False,
                f"the value{at} {value!r} is none of the members {_listed(members)} of "
                f"{to_source(setexpr)} at the values",
            )
        return True, ""
    if isinstance(setexpr, T.Product):
        if isinstance(value, str) or not isinstance(value, Sequence):
            return False, (
                f"the value{at} {value!r} is one value where {to_source(setexpr)} has "
                f"{len(setexpr.factors)} coordinates; write one entry per coordinate"
            )
        if len(value) != len(setexpr.factors):
            return False, (
                f"the value{at} has {len(value)} entries where {to_source(setexpr)} has "
                f"{len(setexpr.factors)} coordinates"
            )
        return _entries(
            stage, definitions, setexpr.factors, value, values, active, path, positional=True
        )
    if isinstance(setexpr, T.Functions):
        indexed = sets.index_sets(setexpr, set_terms)
        first, rest = indexed
        members = sets.finite_members(first, values, set_terms)
        if members is None:
            return _UNDECIDED, ""
        if isinstance(value, Mapping):
            matched, keys = {}, list(value)
            for member in members:
                keys_of_member = [key for key in keys if sets.key_position((member,), key) == 0]
                if not keys_of_member:
                    return False, (
                        f"the value{at} supplies no entry at the key {member!r} of "
                        f"{to_source(first)}, whose members at the values are {_listed(members)}"
                    )
                if len(keys_of_member) > 1:
                    return False, (
                        f"the value{at} supplies the keys {keys_of_member[0]!r} and "
                        f"{keys_of_member[1]!r}, which are "
                        f"one number, the member {member!r} of {to_source(first)}; write one "
                        f"entry per member"
                    )
                matched[member] = value[keys_of_member[0]]
                for key in keys_of_member:
                    keys.remove(key)
            if keys:
                return False, (
                    f"the value{at} supplies an entry at the key {keys[0]!r}, which is no member "
                    f"of {to_source(first)}; the members at the values are {_listed(members)}"
                )
            entries = [matched[member] for member in members]
        elif isinstance(value, Sequence) and not isinstance(value, str):
            if len(value) != len(members):
                return False, (
                    f"the value{at} has {len(value)} entries where {to_source(first)} has "
                    f"{len(members)} members at the values, {_listed(members)}; write one entry "
                    f"per member, in the order of the members"
                )
            entries = list(value)
        else:
            return False, (
                f"the value{at} {value!r} is one value where {to_source(setexpr)} takes one entry "
                f"per member of {to_source(first)}; write a sequence or a mapping"
            )
        return _entries(
            stage, definitions, [rest] * len(members), entries, values, active, path, keys=members
        )
    if isinstance(setexpr, T.Comprehension):
        return _conditioned(stage, definitions, setexpr, value, values, active, path)
    return _UNDECIDED, ""


# the comparison of two numbers that each relation of a condition of a set
# states; two numbers are equal as `sets.same_number` compares two keys
_COMPARISON_OF_RELATION = {
    T.Lt: operator.lt,
    T.Le: operator.le,
    T.Eq: sets.same_number,
    T.Ge: operator.ge,
    T.Gt: operator.gt,
}


def _conditioned(stage, definitions, setexpr, value, values, active, path):
    """The membership of a value in a set with conditions, `{x ∈ B | x < b}`:
    the set that a declaration's several sets are kept as, and the set a
    definition writes with a bar (AMD-GRAM-004 §4).

    The value lies outside the set where it lies outside the base, or at the
    first condition that compares two numbers and is false; the reason names
    the condition and the values it read. It lies in the set where the base
    and every condition are decided so. The membership is not decided where
    the base is not, where a condition is not, or where the set binds more
    than one name.

    The name the set binds is read at the value, also where a parameter has
    that spelling. A side of a condition is read as an interval's endpoint
    is: `inf` and `-inf` are the two infinities, and a side that is no
    finite number otherwise, one that reads a field, an expectation, a
    derived parameter or a value that is no finite number, leaves the
    condition undecided. The value itself is read where it is infinite, so
    that an open infinite endpoint excludes the infinity."""
    coordinates = setexpr.bound.coordinates if isinstance(setexpr.bound, T.Subject) else ()
    if (
        len(coordinates) != 1
        or not isinstance(coordinates[0], T.Coordinate)
        or setexpr.base is None
    ):
        return _UNDECIDED, ""
    status, reason = membership(stage, definitions, setexpr.base, value, values, active, path)
    if status is False:
        return False, reason
    undecided = status is _UNDECIDED
    bound = coordinates[0].stem
    at_value = {**values, bound: value}
    for condition in setexpr.conds:
        compare = _COMPARISON_OF_RELATION.get(type(getattr(condition, "op", None)))
        if compare is None:
            undecided = True
            continue
        left, right = (
            (_side_at(side, bound, at_value), sets.number_at(side, at_value).read)
            for side in (condition.left, condition.right)
        )
        if left[0] is None or right[0] is None:
            undecided = True
        elif not compare(left[0], right[0]):
            read = ", ".join(
                f"{name} = {values[name]!r}"
                for name in values
                if name in left[1] | right[1] and name != bound
            )
            where = f" at {read}" if read else ""
            return False, (
                f"the value{_at(path)} {value!r} does not satisfy the condition "
                f"{condition_text(condition)} of the declared set{where}"
            )
    return (_UNDECIDED, "") if undecided else (True, "")


def _side_at(term, bound, values):
    """The number a side of a condition denotes at the values, None where it
    is not decided: an interval's endpoint is read so (`_endpoint_at`), and
    the name the set binds, `bound`, is read also at an infinite value."""
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        value = values.get(bound) if term.symbol.name == bound else None
        if type(value) is float and math.isinf(value):
            return value
    return _endpoint_at(term, values, math.inf)


def _endpoint_at(term, values, infinity):
    """The number an interval endpoint denotes at the values: `infinity` for
    the constant `inf` or its negation, else the term's number, None where it
    is not decided."""
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        if term.symbol.name == "inf":
            return abs(infinity)
    if isinstance(term, T.Neg) and _endpoint_at(term.operand, values, infinity) == abs(infinity):
        return -abs(infinity)
    return sets.number_at(term, values).value


def _entries(
    stage, definitions, sets_of, entries, values, active, path, positional=False, keys=()
):
    """The membership of each entry of a product or a collection in its set:
    the first entry outside its set decides the answer, with the reason naming
    its key or its position; undecided where no entry is outside and one is
    undecided."""
    undecided = False
    for index, (setexpr, entry) in enumerate(zip(sets_of, entries)):
        key = _Position(index + 1) if positional else keys[index]
        status, reason = membership(
            stage, definitions, setexpr, entry, values, active, path + (key,)
        )
        if status is False:
            return False, reason
        if status is _UNDECIDED:
            undecided = True
    return (_UNDECIDED, "") if undecided else (True, "")


class _Position(int):
    """The position of an entry of a product, counted from one, told apart
    from a key of a collection in the words of a refusal."""

    def __repr__(self):
        return f"position {int(self)}"


def _at(path):
    """The words naming the place of an entry inside a collection: ` at the
    key 2`, ` at position 3`, ` at (1, 2)`, nothing for the value itself."""
    if not path:
        return ""
    if len(path) == 1:
        return f" at {path[0]!r}" if isinstance(path[0], _Position) else f" at the key {path[0]!r}"
    return (
        " at ("
        + ", ".join(repr(int(key)) if isinstance(key, _Position) else repr(key) for key in path)
        + ")"
    )


def _listed(members):
    """The members of a finite set as the file would list them."""
    return "(" + ", ".join(repr(member) for member in members) + ")"


def _valued_endpoints(setexpr, values):
    """The bounds of an interval whose endpoints name parameters, read at the
    values through the one arithmetic interpretation; None where an endpoint
    is not decided."""
    bounds = setexpr.bounds
    if not isinstance(bounds, T.Range) or bounds.left is None or bounds.right is None:
        return None
    lower, upper = (
        _endpoint_at(bounds.lower, values, -math.inf),
        _endpoint_at(bounds.upper, values, math.inf),
    )
    if lower is None or upper is None:
        return None
    return sets.Bounds(
        lower=lower,
        lower_closed=isinstance(bounds.left, T.Closed),
        upper=upper,
        upper_closed=isinstance(bounds.right, T.Closed),
    )


def _in_primitive_domain(domain, value):
    """Whether a value lies in the domain of a primitive set: True, False, or
    `_UNDECIDED` for zero among the naturals and for a domain the module
    keeps no rule for."""
    if domain == "primitive:boolean":
        return type(value) is bool
    if domain == "primitive:extended-real":
        return _is_number(value)
    if domain == "primitive:real":
        return _is_finite(value)
    if domain == "primitive:positive-real":
        return _is_finite(value) and value > 0
    if domain == "primitive:nonnegative-real":
        return _is_finite(value) and value >= 0
    if domain in ("primitive:integer", "primitive:natural"):
        integral = _is_finite(value) and (type(value) is int or value.is_integer())
        if not integral or domain == "primitive:integer":
            return integral
        return _UNDECIDED if value == 0 else value > 0
    return _UNDECIDED


def _is_number(value):
    """Whether a value is an integer or a float other than NaN."""
    return type(value) in (int, float) and not (type(value) is float and math.isnan(value))


def _is_finite(value):
    """Whether a value is an integer or a finite float."""
    return _is_number(value) and (type(value) is int or math.isfinite(value))


def _parameter_address(stage, identity):
    """The authored address of a parameter's declaration, from its record in
    the definitions table of a `StageVersion`; None on a `WorkingStage`, while
    the stage is constructed."""
    return getattr((getattr(stage, "definitions", None) or {}).get(identity), "address", None)


# --- the declared set an obligation names ---


def declared_set_reference(stage, setexpr):
    """The declared set an obligation names: the identity of a named set the
    stage defines, the retained set term for a primitive set and for every
    other form, and the record of an undeclared set where the declaration names
    none (AMD-SG-017 §4)."""
    if setexpr is None:
        return UNDECLARED_SET
    if isinstance(setexpr, T.Named) and setexpr.name not in PRIMITIVE_SETS:
        return Identity("set", stage=stage.name, field=setexpr.name)
    return setexpr


# --- a retained predicate read at parameter values ---


# the reading of a term at parameter values is `typing.sets.number_at`; a
# predicate's reading carries the same two parts
PredicateValue = sets.NumberValue


def predicate_value(predicate, values, set_terms=None):
    """The `PredicateValue` of a retained numeric predicate, its value None
    for unsupported terms. `set_terms` are the sets the stage defines by
    name, through which a named index set is read.

    Both branches are read before deciding a conjunction or disjunction, so a
    true parameter comparison cannot establish a condition on an unbound field.
    Two numbers are compared through doubles where either is one, as
    `typing.sets.same_number` compares two keys. The inclusion `A ⊆ B` of two
    finite index sets and the membership of a number in one are decided from
    their members at the values. A term whose parameters all have values and
    which still denotes no number there, a boolean, an infinite or an
    undefined value, makes its predicate false.
    """
    set_terms = set_terms or {}
    if isinstance(predicate, Not):
        operand = predicate_value(predicate.operand, values, set_terms)
        return PredicateValue(None if operand.value is None else not operand.value, operand.read)
    if isinstance(predicate, (And, Or)):
        left = predicate_value(predicate.left, values, set_terms)
        right = predicate_value(predicate.right, values, set_terms)
        read = left.read | right.read
        if left.value is None or right.value is None:
            return PredicateValue(None, read)
        return PredicateValue(
            left.value and right.value
            if isinstance(predicate, And)
            else left.value or right.value,
            read,
        )
    if isinstance(predicate, Compare):
        if predicate.relation == "⊆":
            return _inclusion_value(predicate, values, set_terms)
        left = sets.number_at(predicate.left, values)
        right = sets.number_at(predicate.right, values)
        compare = {
            "=": sets.same_number,
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
        }.get(predicate.relation)
        undecided = left.value is None or right.value is None or compare is None
        if undecided:
            invalid = compare is not None and any(
                sets.invalid_number(term, values) for term in (predicate.left, predicate.right)
            )
            return PredicateValue(False if invalid else None, left.read | right.read)
        return PredicateValue(compare(left.value, right.value), left.read | right.read)
    if isinstance(predicate, IsInteger):
        operand = sets.number_at(predicate.operand, values)
        if operand.value is None:
            invalid = sets.invalid_number(predicate.operand, values)
            return PredicateValue(False if invalid else None, operand.read)
        return PredicateValue(sets.integer_valued(operand.value), operand.read)
    if isinstance(predicate, Member):
        subject = sets.number_at(predicate.subject, values)
        value = subject.value
        if value is None:
            invalid = sets.invalid_number(predicate.subject, values)
            return PredicateValue(False if invalid else None, subject.read)
        declared = sets.defined(predicate.set, set_terms)
        if isinstance(declared, T.Space):
            declared = sets.defined(declared.set, set_terms)
        if isinstance(declared, (T.IntegerRange, T.Points, T.FiniteSet)):
            members = sets.finite_members(declared, values, set_terms)
            if members is None:
                return PredicateValue(None, subject.read)
            return PredicateValue(sets.key_position(members, value) is not None, subject.read)
        primitive = sets.primitive_of(declared)
        if primitive is not None and primitive.kind == INTEGER:
            return PredicateValue(
                sets.integer_valued(value) and (primitive.order == 0 or value > 0), subject.read
            )
        # a ratio is written as its double, the number the interval reads
        point_value = value if isinstance(value, (int, float)) else float(value)
        point = T.Interval(
            T.Range(
                left=T.Closed(),
                lower=T.Number(point_value),
                upper=T.Number(point_value),
                right=T.Closed(),
            )
        )
        return PredicateValue(sets.within(point, declared, set_terms), subject.read)
    return PredicateValue(None, frozenset())


def _inclusion_value(predicate, values, set_terms):
    """The reading of `A ⊆ B` for two finite index sets at the values: True
    where every member of A is a member of B, False where one is not, None
    where the members of either are not decided."""
    inner = sets.finite_members(predicate.left, values, set_terms)
    outer = sets.finite_members(predicate.right, values, set_terms)
    read = frozenset()
    for term in (predicate.left, predicate.right):
        for bound in _bound_terms(term):
            read = read | sets.number_at(bound, values).read
    if inner is None or outer is None:
        return PredicateValue(None, read)
    return PredicateValue(
        all(sets.key_position(outer, member) is not None for member in inner), read
    )


def _bound_terms(setterm):
    """The retained terms a finite index set reads numbers from: the bounds
    of a range, the members of a listed set."""
    if isinstance(setterm, T.IntegerRange):
        return (setterm.lower, setterm.upper)
    if isinstance(setterm, T.Points):
        return tuple(setterm.members)
    return ()
