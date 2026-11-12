"""The check of parameter values against the declared sets of the parameter
definitions, and of each derived parameter's value against the set its
definition declares.

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
from bellman.fold.derived_parameters import derived_value, derived_values
from bellman.fold.stage_names import StageNames
from bellman.native.identity import Identity
from bellman.native.predicates import And, Compare, IsInteger, Member, Not, Or
from bellman.native.records import UNDECLARED_SET, Condition
from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import condition_text, to_source
from bellman.syntax.vocabulary import INTEGER, PRIMITIVE_SETS
from bellman.typing import sets
from bellman.typing.declarations import derived_parameter_fault, derived_parameters_read

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
    of functions, a union, a difference and a set with conditions, whose
    conditions compare terms of numbers and valued parameters). It does not
    interpret equations, functions or source strings. Every declared
    parameter needs a value. A value for a derived parameter, which its
    definition gives, is refused under `derived-parameter` at the definition
    (AMD-MT-003, build contract §5).

    Where a set reads another parameter, as a bound or as an endpoint, a
    faulty value is refused at its own parameter and not at the parameter
    whose set reads it, in whatever order the file declares the two
    (`judged`; AMD-GRAM-004 §4).

    The values are judged in three steps. The declared values are judged
    first, so that a fault they decide alone is refused at its own
    parameter. The derived parameters are then valued (`derived_values`),
    which refuses a definition that has no value. Last, at the declared and
    the derived values together, the set each derived parameter's definition
    declares, `q : (0,1) := (β*R)^(1/ρ)/R`, is judged with every membership
    the declared values left undecided, such as a bound that reads a derived
    parameter; a derived value outside its set is refused as a parameter's
    is, naming the definition and the values it reads (AMD-GRAM-005).

    In each step a set of which a bound has no value at the values, `β : (0,
    1/(R - 2))` at R = 2, is refused at its own name, with the bound, the
    values it reads and the operation that fails. A bound is valued as a
    derived parameter's definition is, so it may call `log` and `exp`
    (`_bound_at`). A bound that reads a name without a value yet, or an
    expectation, leaves the membership undecided.
    """
    definitions = dict(stage.definitions)
    _refuse_derived_values(stage, definitions, values)
    # a parameter declared without a set lies in the reals
    declared = {name: setexpr or T.Named("ℝ") for name, setexpr in parameter_sets(stage).items()}
    undecided = _undecided(stage, definitions, declared, values)
    derived = derived_values(stage, values)
    if derived:
        # in the order of the file: the set a derived parameter's definition
        # declares, its record's one coordinate, and the set of each
        # parameter whose membership the declared values left undecided
        declared = {
            d.identity.field: d.coordinates[0][1]
            if d.kind == "derived_parameter"
            else declared[d.identity.field]
            for d in definitions.values()
            if (d.kind == "derived_parameter" and d.coordinates)
            or (d.kind == "parameter" and d.identity.field in undecided)
        }
        values = {**values, **derived}
        undecided = _undecided(stage, definitions, declared, values)
    return tuple(
        Condition(
            condition="calibration-domain-membership",
            entries=(
                _judged_identity(stage, definitions, name),
                declared_set_reference(stage, setexpr),
            ),
            status="required",
            explanation=f"The value {values[name]!r} of {name} "
            f"must belong to {to_source(setexpr)}.",
        )
        for name, setexpr in declared.items()
        if name in undecided
    )


def _undecided(stage, definitions, declared, values):
    """The names of `declared`, each a parameter or a derived parameter with
    its set, whose membership is not decided at `values`. A name that has no
    value, a value outside its set and a set with a bound that has no value
    at `values` are refused, a faulty value at its own name (`judged`)."""
    undecided = set()
    for name, status, reason in judged(stage, definitions, declared, values):
        if status is True:
            continue
        identity = _judged_identity(stage, definitions, name)
        kind = "derived parameter" if identity.kind == "derived" else "parameter"
        # a refusal says where, what happened, why and what to write
        # (AMD-SG-006 §6a)
        where = (
            f"stage {stage.name!r}, {kind} {name!r} "
            f"(address {_parameter_address(stage, identity)!r})"
        )
        if status is UNVALUED:
            raise ValueError(
                f"{where}: the calibration source supplies no value for it; every declared "
                "parameter is valued when values are bound (AMD-SG-006 §4, "
                f"rule 8); write `{name}: <value>` in the calibration source"
            )
        if status is UNVALUED_BOUND:
            raise ValueError(f"{where}: {reason}")
        if status is False and identity.kind == "derived":
            raise ValueError(_derived_outside(stage, where, definitions, identity, values, reason))
        if status is False:
            raise ValueError(_outside(where, declared[name], values[name], reason))
        undecided.add(name)
    return undecided


def _judged_identity(stage, definitions, name):
    """The identity of a name whose value is judged: a derived parameter's
    where the stage defines one of that name, a parameter's otherwise."""
    derived = Identity("derived", stage=stage.name, field=name)
    if derived in definitions:
        return derived
    return Identity("parameter", stage=stage.name, field=name)


def judged(stage, definitions, declared, values, settled=None):
    """The membership of each value in its declared set, as `(name, status,
    reason)` in the order in which a refusal is to be given. `declared` maps
    each name to its set, None for a name with no set to judge; `values`
    holds the value of each name; and `settled` holds the values of an
    earlier binding, the calibration and the derived parameters' values at
    it where settings are judged. The status
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
    reads another, the first of the file is named.

    A name whose set has a bound without a value at the values, `β : (0,
    1/(R - 2))` at R = 2, has the status `UNVALUED_BOUND`, with the reason
    that names the bound and the values it reads. It is a faulty name, and
    is ordered as the others are."""
    everything = {**(settled or {}), **values}

    def faulty_status(status):
        return status is False or status is UNVALUED or status is UNVALUED_BOUND

    def judge(name, at):
        if name not in values:
            return UNVALUED, ""
        if declared[name] is None:
            return True, ""
        try:
            return membership(stage, definitions, declared[name], values[name], at)
        except _UnvaluedBound as fault:
            return UNVALUED_BOUND, _bound_reason(stage, definitions, declared[name], fault, at)

    answers = {name: judge(name, everything) for name in declared}
    faulty = [name for name, (status, _) in answers.items() if faulty_status(status)]
    first = []
    for name in faulty:
        others = {
            read: value for read, value in everything.items() if read == name or read not in faulty
        }
        status, reason = judge(name, others)
        if faulty_status(status):
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


def _derived_outside(stage, where, definitions, identity, values, reason):
    """The sentence that refuses a derived parameter's value outside the set
    its definition declares: where, the value its definition takes, why and
    what to write. It names the declared parameters that the definition and
    the set read, directly or through other derived parameters, in the order
    of the file, since the calibration supplies their values alone. Where
    `reason`, the answer of `membership`, names a part of the set that the
    value breaks, a condition, the base or the members, the reason follows.
    Otherwise each derived parameter the set reads follows with its value,
    at which a bound of the set is read."""
    definition = definitions[identity]
    name, term = identity.field, definition.equations[0]
    setexpr = definition.coordinates[0][1]
    declared = to_source(setexpr)
    names = StageNames(stage)
    named = {held.field for held in names.parameters((term, setexpr))}
    read = [parameter for parameter in parameter_sets(stage) if parameter in named]
    at = ", ".join(f"{parameter} = {values[parameter]!r}" for parameter in read)
    listed = " and ".join(", ".join(read).rsplit(", ", 1))
    if reason and reason != f"the value {values[name]!r} lies outside the declared set {declared}":
        detail = f": {reason}"
    else:
        others = [
            _valued(stage, definitions, other, values[other])
            for other in derived_parameters_read(setexpr, names.derived)
            if other != name
        ]
        detail = f", where {', '.join(others)}" if others else ""
    return (
        f"{where}: the value {values[name]!r} of {name}, which the stage defines as "
        f"`{to_source(term)}`, lies outside the declared set {declared}"
        + (f" at {at}" if read else "")
        + detail
        + "; a derived parameter's value lies in the set its definition declares; write "
        + (
            f"values of {listed} at which {name} lies in {declared}"
            if read
            else f"a definition of {name} whose value lies in {declared}"
        )
    )


def _valued(stage, definitions, name, value):
    """A name with the value a refusal reads it at, `R = 1.04`. A derived
    parameter is followed by its definition, `q = 0.96 (the derived
    parameter q := β*R)`, since no calibration source supplies its value."""
    derived = definitions.get(Identity("derived", stage=stage.name, field=name))
    if derived is None:
        return f"{name} = {value!r}"
    return (
        f"{name} = {value!r} (the derived parameter {name} := {to_source(derived.equations[0])})"
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

# the answer of `judged` for a name whose declared set has a bound without a
# value at the values
UNVALUED_BOUND = object()


class _UnvaluedBound(ValueError):
    """A bound of a declared set that has no value at the values it is read
    at, although every name it reads has a number there. `bound` is the
    bound's term. `reason` is the sentence that names the operation that
    fails, as the evaluator of a derived parameter's definition words it
    (`derived_value`). `membership` raises it, and `judged` answers it as
    the status `UNVALUED_BOUND`."""

    def __init__(self, bound, reason):
        super().__init__(reason)
        self.bound, self.reason = bound, reason


class _BoundReason(str):
    """The sentence that refuses a declared set of which a bound has no
    value, with `read`, the names that bound reads, in the order of its
    text. The check of the settings relates its refusal to the key of each
    of them (`binding_verbs`)."""

    def __new__(cls, sentence, read):
        reason = super().__new__(cls, sentence)
        reason.read = tuple(read)
        return reason


def _bound_reason(stage, definitions, setexpr, fault, values):
    """The reason that refuses the declared set `setexpr`, of which the
    bound of `fault` has no value at `values`: the bound as the file writes
    it, the value of each name it reads, the operation that fails
    (`fault.reason`), why and what to write. A derived parameter is followed
    by its definition (`_valued`). A bound that reads no name, `1/0`, has no
    value at any values, and the advice is another bound."""
    written = to_source(fault.bound)
    read = derived_parameters_read(fault.bound, values)
    at = ", ".join(_valued(stage, definitions, name, values[name]) for name in read)
    advice = "another bound"
    if at:
        advice = f"values at which `{written}` has a value, or {advice}"
    return _BoundReason(
        f"the bound `{written}` of the declared set {to_source(setexpr)} has no value"
        + (f" at {at}" if at else "")
        + f": {fault.reason}; a declared set is defined at the values only where each of its "
        f"bounds has a value; write {advice}",
        read,
    )


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
    from its base and its conditions at the values (`_conditioned`). A value
    lies in a union where it lies in one member and outside it where it lies
    outside every member; it lies in a difference where it lies in the left
    side and outside the right side, and outside it where it lies outside
    the left side or in the right side; the reason of either refusal names
    the whole set, and a part that is not decided leaves the whole
    undecided where the other parts do not decide it. An
    extended real, a set the file does not define and any other form are not
    decided. `values` holds the value of each name an endpoint or a side of
    a condition may read: the declared parameters' and, where the caller has
    computed them, the derived parameters' (`calibration_requirements`); an
    endpoint or a side that reads a name `values` does not hold is not
    decided. `path`
    names the keys that lead to the value inside a collection, for the
    reason of a refusal.

    A bound whose arithmetic has no value at `values`, although every name it
    reads has a number there, `1/(R - 2)` at R = 2, gives none of the three
    answers: the set is no set at those values, and `_UnvaluedBound` is
    raised (`_bound_at`), which `judged` answers as `UNVALUED_BOUND`."""
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
    if isinstance(setexpr, (T.SetUnion, T.SetDifference)):
        union = isinstance(setexpr, T.SetUnion)
        parts = setexpr.members if union else (setexpr.left, setexpr.right)
        answers = [
            membership(stage, definitions, part, value, values, active, path)[0]
            for part in parts
        ]
        if union:
            held = True in answers
            excluded = all(answer is False for answer in answers)
        else:
            held = answers[0] is True and answers[1] is False
            excluded = answers[0] is False or answers[1] is True
        if excluded:
            return outside(to_source(setexpr))
        return (True, "") if held else (_UNDECIDED, "")
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
    finite number otherwise, one that reads a field, an expectation, a name
    `values` does not hold or a value that is no finite number, leaves the
    condition undecided. A derived parameter is read at its value where
    `values` holds it, which it does once the derived values are computed
    (`calibration_requirements`). The value itself is read where it is
    infinite, so that an open infinite endpoint excludes the infinity.

    A side that does not read the name the set binds is a bound of the set.
    Where its arithmetic has no value at the values, although every name it
    reads has a number there, `_UnvaluedBound` is raised (`_side_at`)."""
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
                _valued(stage, definitions, name, values[name])
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
    the name the set binds, `bound`, is read also at an infinite value. A
    side that does not read `bound` is a bound of the set, and is read as
    one (`_bound_at`). A side that reads `bound`, also inside a call,
    `log(x)`, is none."""
    if isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant):
        value = values.get(bound) if term.symbol.name == bound else None
        if type(value) is float and math.isinf(value):
            return value
    if derived_parameters_read(term, (bound,)):
        return _endpoint_at(term, values, math.inf)
    return _bound_at(term, values, math.inf)


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


def _bound_at(term, values, infinity):
    """The number a bound of a declared set denotes at the values. It is
    read as an interval endpoint is (`_endpoint_at`). A bound that this
    reading does not value is valued as a derived parameter's definition is
    (`derived_value`), so that a bound may call `log` and `exp`, `(0,
    exp((ρ - 1)*μ))`.

    The answer is None where the bound is not decided: a name it reads has
    no number yet, or it holds an expectation or another form that no
    derived parameter's definition admits (`derived_parameter_fault`). A
    value that is no finite number, an infinite value of a parameter
    declared on the extended reals, is no number here, so a bound that
    reads one is not decided either. A bound that has no value at the
    numbers raises `_UnvaluedBound` with the evaluator's reason: a division
    by zero, a negative base under a fractional power, `log` of a number
    that is not positive, or a result beyond the floating-point numbers."""
    value = _endpoint_at(term, values, infinity)
    if value is not None:
        return value
    numbers = {name: held for name, held in values.items() if sets.is_number(held)}
    if derived_parameter_fault("", term, numbers, (), {}) is not None:
        return None
    try:
        return derived_value(term, numbers)
    except ValueError as fault:
        raise _UnvaluedBound(term, str(fault)) from None


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
    is not decided. An endpoint whose arithmetic has no value at the values
    raises `_UnvaluedBound` (`_bound_at`)."""
    bounds = setexpr.bounds
    if not isinstance(bounds, T.Range) or bounds.left is None or bounds.right is None:
        return None
    lower, upper = (
        _bound_at(bounds.lower, values, -math.inf),
        _bound_at(bounds.upper, values, math.inf),
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
    their members at the values, and the membership of a number in a union
    or a difference from its membership in each part (`_number_in`). A term
    whose parameters all have values and which still denotes no number
    there, a boolean, an infinite or an undefined value, makes its predicate
    false.
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
        if subject.value is None:
            invalid = sets.invalid_number(predicate.subject, values)
            return PredicateValue(False if invalid else None, subject.read)
        return PredicateValue(
            _number_in(subject.value, predicate.set, values, set_terms), subject.read
        )
    return PredicateValue(None, frozenset())


def _number_in(value, setterm, values, set_terms):
    """Whether a number lies in a retained set at the values: True, False, or
    None where it is not decided. A finite index set is read from its members
    at the values, an integer set from the number itself, and every other set
    by the set algebra, the number written as the interval of one point. A
    number lies in a union where one member holds it and outside it where no
    member does; it lies in a difference where the left side holds it and the
    right side does not, and outside it where the left side does not hold it
    or the right side does."""
    declared = sets.defined(setterm, set_terms)
    if isinstance(declared, T.Space):
        declared = sets.defined(declared.set, set_terms)
    if isinstance(declared, T.SetUnion):
        answers = [_number_in(value, member, values, set_terms) for member in declared.members]
        if True in answers:
            return True
        return False if all(answer is False for answer in answers) else None
    if isinstance(declared, T.SetDifference):
        left = _number_in(value, declared.left, values, set_terms)
        right = _number_in(value, declared.right, values, set_terms)
        if left is False or right is True:
            return False
        return True if left is True and right is False else None
    if isinstance(declared, (T.IntegerRange, T.Points, T.FiniteSet)):
        members = sets.finite_members(declared, values, set_terms)
        return None if members is None else sets.key_position(members, value) is not None
    primitive = sets.primitive_of(declared)
    if primitive is not None and primitive.kind == INTEGER:
        return sets.integer_valued(value) and (primitive.order == 0 or value > 0)
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
    return sets.within(point, declared, set_terms)


def _inclusion_value(predicate, values, set_terms):
    """The reading of `A ⊆ B` at the values, for B a finite index set and A
    the set of a key, a finite index set or a union or a difference of
    finite sets (`_key_members`): True where every member of A is a member
    of B, False where one is not, None where the members of either are not
    decided."""
    inner = _key_members(predicate.left, values, set_terms)
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


def _key_members(setterm, values, set_terms):
    """The members of the set of a key at the values, where they are
    finitely many and decided: those of a finite index set
    (`sets.finite_members`); of a union, the members of each member; and of
    a difference, the members of its left side that its right side does not
    hold (`_number_in`). None where the members of a part are not decided,
    or the membership of one of them in a right side."""
    declared = sets.defined(setterm, set_terms)
    if isinstance(declared, T.Space):
        declared = sets.defined(declared.set, set_terms)
    if isinstance(declared, T.SetUnion):
        parts = [_key_members(member, values, set_terms) for member in declared.members]
        if any(part is None for part in parts):
            return None
        return tuple(member for part in parts for member in part)
    if isinstance(declared, T.SetDifference):
        left = _key_members(declared.left, values, set_terms)
        if left is None:
            return None
        removed = [_number_in(member, declared.right, values, set_terms) for member in left]
        if any(answer is None for answer in removed):
            return None
        return tuple(member for member, gone in zip(left, removed) if not gone)
    return sets.finite_members(declared, values, set_terms)


def _bound_terms(setterm):
    """The retained terms a set reads numbers from: the bounds of a range,
    the members of a listed set, the ends of an interval, and the terms of
    each member of a union and of each side of a difference."""
    if isinstance(setterm, T.IntegerRange):
        return (setterm.lower, setterm.upper)
    if isinstance(setterm, T.Points):
        return tuple(setterm.members)
    if isinstance(setterm, T.Interval) and isinstance(setterm.bounds, T.Range):
        return (setterm.bounds.lower, setterm.bounds.upper)
    if isinstance(setterm, T.SetUnion):
        return tuple(bound for member in setterm.members for bound in _bound_terms(member))
    if isinstance(setterm, T.SetDifference):
        return _bound_terms(setterm.left) + _bound_terms(setterm.right)
    return ()
