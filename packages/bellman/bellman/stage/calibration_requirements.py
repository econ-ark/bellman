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

An infinite value has one reading (AMD-GRAM-006; AAS, 12 November 2026). An
endpoint of an interval, or a side of a condition, that is the bare name of
a parameter or of a derived parameter valued at `inf` or `-inf` is read as
that infinity, whatever supplies the value (`_endpoint_at`). No arithmetic
of infinities is defined, so a bound that computes with such a name, or
with the written infinity, `2*inf`, has no value, and its set is refused as
a set with a bound that divides by zero is (`_bound_at`). A finite number
lies in every set of extended reals, and an infinity lies in a set exactly
where the set holds it; `membership` and `predicate_value`, the two
procedures that judge a membership, give that one answer (`_infinity_in`).
"""

import math
import operator
from collections.abc import Mapping, Sequence

from bellman.fold.block_lines import parameter_sets
from bellman.fold.derived_parameters import derived_order, derived_value, derived_value_of
from bellman.fold.stage_names import StageNames
from bellman.native.identity import Identity
from bellman.native.predicates import And, Compare, IsInteger, Member, Not, Or
from bellman.native.records import UNDECLARED_SET, Condition
from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.source import condition_text, is_infinity, may_hold_infinity, to_source
from bellman.syntax.vocabulary import EXTENDED_REAL, INTEGER, PRIMITIVE_SETS
from bellman.syntax.walk import nodes
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
    parameter. The derived parameters are then valued (`_derived_values`),
    which refuses a definition that has no value; before a definition is
    evaluated, each value it reads is judged against its own declared set,
    with the values that set reads, so that a value outside its set is
    refused at its own name, and not at a definition that computes with it
    or at a name whose set reads it. Last, at the declared and the derived
    values together, the set each derived parameter's definition declares,
    `q : (0,1) := (β*R)^(1/ρ)/R`, is judged with every membership the
    earlier steps left undecided, such as a bound that reads a derived
    parameter whose own definition reads the bounded parameter; a derived
    value outside its set is refused as a parameter's is, naming the
    definition and the values it reads (AMD-GRAM-005).

    In each step a set of which a bound has no value at the values, `β : (0,
    1/(R - 2))` at R = 2, is refused at its own name, with the bound, the
    values it reads and the operation that fails. A bound is valued as a
    derived parameter's definition is, so it may call `log`, `exp`, `min` and
    `max` (`_bound_at`), and one that computes with a name valued at an
    infinity, or with the written `inf`, has no value. A bound that reads a
    name without a value yet, or an expectation, leaves the membership
    undecided.
    """
    definitions = dict(stage.definitions)
    _refuse_derived_values(stage, definitions, values)
    # a parameter declared without a set lies in the reals
    declared = {name: setexpr or T.Named("ℝ") for name, setexpr in parameter_sets(stage).items()}
    undecided = _undecided(stage, definitions, declared, values)
    derived = _derived_values(stage, definitions, declared, undecided, values)
    if derived:
        declared = _sets_to_judge(definitions, declared, undecided)
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


def _sets_to_judge(definitions, declared, undecided):
    """The sets that the declared values do not decide, by name and in the
    order of the file: the set a derived parameter's definition declares,
    its record's one coordinate, and the set of each parameter whose
    membership the declared values left undecided, the names of
    `undecided`."""
    return {
        d.identity.field: d.coordinates[0][1]
        if d.kind == "derived_parameter"
        else declared[d.identity.field]
        for d in definitions.values()
        if (d.kind == "derived_parameter" and d.coordinates)
        or (d.kind == "parameter" and d.identity.field in undecided)
    }


def _derived_values(stage, definitions, declared, undecided, values):
    """The value of each derived parameter of the stage at the calibration
    values `values`, by name and in file order, as `derived_values` answers
    them, with each value judged against its own declared set before a
    definition that reads it is evaluated (CDC, 12 November 2026).

    A definition may compute with a value only where the value lies in its
    set: `μ := log(s)` has a value where `s` is positive, which the set of
    `s`, or of a parameter `s` is defined from, states. So before a
    definition is evaluated, each name it reads is judged: a declared
    parameter whose membership the declared values left undecided, the
    names of `undecided`, since its set reads a derived parameter, and a
    derived parameter whose definition declares a set. Where the set of
    such a name reads a derived parameter, that one is valued first. A
    value outside its set is refused there, at its own name, as `_undecided`
    refuses it, and the definition that reads it is not evaluated.

    The names that the set of such a name reads are judged with it, and
    those that their sets read, a set written by name being read through
    its definition (AAS's review, 13 November 2026). `judged` refuses a
    faulty value at its own name, and not at a name whose set reads it,
    among the names it is given (AMD-GRAM-004 §4). So with `x : (0, b)`,
    `y : (x, c)` and a definition that reads `y` alone, a value of `x`
    outside `(0, b)` is refused at `x`, and not at `y`, which lies outside
    `(x, c)` only at the faulty `x`; and a derived value outside the set
    its definition declares is refused at that definition, and not at a
    parameter whose set reads it.

    Before a definition a value is refused only where it lies outside its
    set by itself, and of several such values judged together the first of
    the file is named. Values that lie outside their sets only at the value
    of each other, or of a name whose own membership is not yet decided,
    are left for the judgment that follows the last definition, which has
    every value before it and names a value faulty by itself where there is
    one (`judged`, `by_itself`).

    A membership that cannot be decided yet is left for the judgment that
    follows the last definition: that of a name whose set reads the derived
    parameter being valued, or a derived parameter whose value needs it, so
    that the two read each other, and one that `membership` does not
    decide. The definitions are evaluated in the order `derived_order`
    answers, except that a derived parameter a set reads is valued before
    the definition that waits for that set, where its value needs no
    derived parameter that is being valued: no definition is evaluated
    before a derived parameter it reads has its value. Every order gives
    each definition the same value."""
    order = derived_order(stage.definitions)
    by_name = {definition.identity.field: definition for definition in order}
    # the sets still to be judged, by name and in the order of the file
    open_sets = _sets_to_judge(definitions, declared, undecided)
    names = {*declared, *by_name}
    set_terms = _set_terms(definitions)
    # the derived parameters that the value of each one needs, itself among
    # them; `order` lists each after those its definition reads
    needs = {}
    for name, definition in by_name.items():
        own = derived_parameters_read(definition.equations[0], by_name)
        needs[name] = {name}.union(*(needs[other] for other in own))
    found, active = {}, set()

    def read_by(setexpr):
        # the names a set reads, also through the sets the file defines by
        # name, as `membership` reads them; each named set is read once
        read, seen, pending = [], set(), [setexpr]
        while pending:
            term = pending.pop()
            read.extend(derived_parameters_read(term, names))
            for node in nodes(term):
                named = isinstance(node, T.Named) and node.name in set_terms
                if named and node.name not in seen:
                    seen.add(node.name)
                    pending.append(set_terms[node.name])
        return read

    def judge(read):
        # the names of `read` whose sets are still to be judged and that
        # have a value, in the order of the file, in which `judged` names
        # the first of several faulty values. Only a value that lies
        # outside its set by itself is refused here; a value that lies
        # outside its set only at the value of a name that is faulty or
        # not yet decided waits for the judgment that follows the last
        # definition, where every value is present
        at = {**values, **found}
        group = {
            name: setexpr for name, setexpr in open_sets.items() if name in read and name in at
        }
        if group:
            still = _undecided(stage, definitions, group, at, by_itself=True)
            for name in group:
                if name not in still:
                    del open_sets[name]

    def value(name):
        if name in found:
            return
        active.add(name)
        # the names the definition reads and, with each whose set is still
        # to be judged, the names that set reads, and so on: `judged`
        # refuses a faulty value at its own name, and not at a name whose
        # set reads it, among the names it is given (AMD-GRAM-004 §4)
        read = list(derived_parameters_read(by_name[name].equations[0], names))
        for other in read:  # the list grows while it is read
            if other in open_sets:
                for more in read_by(open_sets[other]):
                    if more not in read:
                        read.append(more)
            # a derived parameter is valued before it is read or judged. One
            # that a set reads waits where its value needs a derived
            # parameter that is being valued, and that set is judged later;
            # one that the definition reads needs none, since the
            # definitions form no cycle (`derived_order`)
            if other in by_name and not needs[other] & active:
                value(other)
        judge(read)
        found[name] = derived_value_of(stage, by_name[name], {**values, **found})
        active.discard(name)

    for definition in order:
        value(definition.identity.field)
    return {
        d.identity.field: found[d.identity.field]
        for d in stage.definitions.values()
        if d.kind == "derived_parameter"
    }


def _undecided(stage, definitions, declared, values, by_itself=False):
    """The names of `declared`, each a parameter or a derived parameter with
    its set, whose membership is not decided at `values`. A name that has no
    value, a value outside its set and a set with a bound that has no value
    at `values` are refused, a faulty value at its own name (`judged`).

    With `by_itself`, a value that lies outside its set only where another
    faulty value of `declared` is read is not refused: its name is answered
    among the undecided. A caller that judges some of the values before the
    others are present refuses in this way only a value that is faulty by
    itself, and leaves the others for a judgment of all the values
    (`_derived_values`)."""
    undecided = set()
    for name, status, reason in judged(stage, definitions, declared, values, by_itself=by_itself):
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


def judged(stage, definitions, declared, values, settled=None, by_itself=False):
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
    reads another, the first of the file is named. With `by_itself`, a
    faulty value is judged again with the values of the names that are not
    decided left out as well, since one of them may prove faulty where more
    values are present, and a faulty name that does not then stand first is
    answered as not decided: its value lies outside its set only where the
    value of such a name is read.

    A name whose set has a bound without a value at the values, `β : (0,
    1/(R - 2))` at R = 2, has the status `UNVALUED_BOUND`, with the reason
    that names the bound and the values it reads. It is a faulty name, and
    is ordered as the others are. So is a name whose set has a bound that
    computes with the written infinity, `(0, 2*inf)`, except in a stage that
    declares a name `inf`: there a bound reads that name where it has a
    value, as before, and the membership is not decided where it has none."""
    everything = {**(settled or {}), **values}
    declares_inf = any(identity.field == "inf" for identity in definitions)
    # a key `inf` of a calibration source or of a settings source is no name
    # of a stage that declares none, so it gives the written infinity no value
    if not declares_inf:
        everything.pop("inf", None)

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
            if fault.at_no_values and declares_inf:
                return _UNDECIDED, ""
            return UNVALUED_BOUND, _bound_reason(stage, definitions, declared[name], fault, at)

    answers = {name: judge(name, everything) for name in declared}
    faulty = [name for name, (status, _) in answers.items() if faulty_status(status)]
    # the names whose values are left out when a faulty value is judged
    # again: the faulty ones and, with `by_itself`, those not decided, each
    # of which may prove faulty where more values are present
    doubtful = faulty
    if by_itself:
        doubtful = [name for name, (status, _) in answers.items() if status is not True]
    first = []
    for name in faulty:
        others = {
            read: value
            for read, value in everything.items()
            if read == name or read not in doubtful
        }
        status, reason = judge(name, others)
        if faulty_status(status):
            # the reason names what the value breaks by itself
            answers[name] = (status, reason)
            first.append(name)
    if by_itself:
        for name in faulty:
            if name not in first:
                answers[name] = (_UNDECIDED, "")
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
    at which a bound of the set is read, where `values` holds it: a value
    refused before every definition is evaluated is refused at the values
    present (`_derived_values`)."""
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
            if other != name and other in values
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
    (`derived_value`). `at_no_values` is true for a bound that has a value
    at no values, since it computes with the written infinity. `membership`
    raises it, and `judged` answers it as the status `UNVALUED_BOUND`."""

    def __init__(self, bound, reason, at_no_values=False):
        super().__init__(reason)
        self.bound, self.reason, self.at_no_values = bound, reason, at_no_values


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
    by its definition (`_valued`). A bound that reads no name, `1/0`, and a
    bound that computes with the written infinity, `2*inf*R`, have no value
    at any values: no value is named, and the advice is another bound."""
    written = to_source(fault.bound)
    read = () if fault.at_no_values else derived_parameters_read(fault.bound, values)
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
    undecided where the other parts do not decide it. A set of extended
    reals holds every finite number and the infinities of the sides it
    reaches, `inf` for `ℝ_{+∞}`, `-inf` for `ℝ_{-∞}` and both for `ℝ̄`; a
    value there that is no number is not decided. A set the file does not
    define and any other form are not decided. `values` holds the value of
    each name an endpoint or a side of a condition may read: the declared
    parameters' and, where the caller has computed them, the derived
    parameters' (`calibration_requirements`); an endpoint or a side that
    reads a name `values` does not hold is not decided. `path` names the
    keys that lead to the value inside a collection, for the reason of a
    refusal.

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
            if primitive.kind == EXTENDED_REAL:
                # a finite number lies in every set of extended reals, and
                # an infinity in those that reach its side; the membership
                # of a value that is no number is not decided
                if _is_finite(value):
                    return True, ""
                if not _is_infinity(value):
                    return _UNDECIDED, ""
                held = may_hold_infinity(setexpr, negative=value < 0)
                return (True, "") if held else outside(setexpr.name)
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
    is: `inf`, `-inf` and a bare name valued at an infinity are the two
    infinities, and a side that is no finite number otherwise, one that
    reads a field, an expectation or a name `values` does not hold, leaves
    the condition undecided. A derived parameter is read at its value where
    `values` holds it, which it does once the derived values are computed
    (`calibration_requirements`). The value itself is read where it is
    infinite, so that an open infinite endpoint excludes the infinity.

    A side that does not read the name the set binds is a bound of the set.
    Where its arithmetic has no value at the values, although every name it
    reads has a value there, `_UnvaluedBound` is raised (`_side_at`). The
    sentence of a condition that is false gives the value of each name its
    two sides read, a name inside a call of `min` or `max` among them."""
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
    bound = coordinates[0].stem
    at_value = {**values, bound: value}
    failed, undecided = _conditions_at(setexpr, bound, at_value)
    if failed is not None:
        named = derived_parameters_read(failed.left, values) + derived_parameters_read(
            failed.right, values
        )
        read = ", ".join(
            _valued(stage, definitions, name, values[name])
            for name in values
            if name in named and name != bound
        )
        where = f" at {read}" if read else ""
        return False, (
            f"the value{_at(path)} {value!r} does not satisfy the condition "
            f"{condition_text(failed)} of the declared set{where}"
        )
    return (_UNDECIDED, "") if undecided or status is _UNDECIDED else (True, "")


def _conditions_at(setexpr, bound, at_value):
    """The conditions of a set with conditions read at `at_value`, which
    holds the value judged under the name the set binds, `bound`: as a pair,
    the first condition that compares two numbers and is false, or None
    where none is, and whether a condition before it is not decided.
    `membership` and `predicate_value` both read the conditions through
    this function."""
    undecided = False
    for condition in setexpr.conds:
        compare = _COMPARISON_OF_RELATION.get(type(getattr(condition, "op", None)))
        if compare is None:
            undecided = True
            continue
        left, right = (
            _side_at(side, bound, at_value) for side in (condition.left, condition.right)
        )
        if left is None or right is None:
            undecided = True
        elif not compare(left, right):
            return condition, undecided
    return None, undecided


def _side_at(term, bound, values):
    """The number a side of a condition denotes at the values, None where it
    is not decided. A side that reads `bound`, the name the set binds, is
    read as an interval's endpoint is (`_endpoint_at`), which reads the bare
    name also at an infinite value; a side that reads it inside arithmetic or
    a call, `log(x)`, has no number there and is not decided. A side that
    does not read `bound` is a bound of the set, and is read as one
    (`_bound_at`)."""
    if derived_parameters_read(term, (bound,)):
        return _endpoint_at(term, values, math.inf)
    return _bound_at(term, values, math.inf)


def _is_infinity(value):
    """Whether a value is the float `inf` or `-inf`."""
    return type(value) is float and math.isinf(value)


def _infinite_value(term, values):
    """The infinity that a bare name is valued at, `inf` or `-inf`: `term`
    is the name of a parameter or of a derived parameter, written bare or
    referred to by its identity, and `values` holds an infinite float for
    it. None for any other term and any other value. The value is read so
    whatever supplies it, a calibration for a parameter declared on a set
    that holds the infinity or a branch of a definition by cases
    (AMD-GRAM-006; AAS, 12 November 2026)."""
    if not (isinstance(term, T.Sym) and isinstance(term.symbol, T.Constant)):
        return None
    for name in sets.parameters_read(term) or ():
        if _is_infinity(values.get(name)):
            return values[name]
    return None


def _endpoint_at(term, values, infinity):
    """The number an interval endpoint denotes at the values: `infinity` for
    the constant `inf` and its negation for `-inf`, the infinity a bare name
    is valued at (`_infinite_value`), else the term's number, None where it
    is not decided. The negation of a name valued at an infinity is no
    endpoint read here: it computes with the infinity, and `_bound_at`
    answers that it has no value."""
    named = _infinite_value(term, values)
    if named is not None:
        return named
    if is_infinity(term, negative=False):
        return abs(infinity)
    if is_infinity(term, negative=True):
        return -abs(infinity)
    return sets.number_at(term, values).value


def _bound_at(term, values, infinity):
    """The number a bound of a declared set denotes at the values. It is
    read as an interval endpoint is (`_endpoint_at`). A bound that this
    reading does not value is valued as a derived parameter's definition is
    (`derived_value`), so that a bound may call `log`, `exp`, `min` and
    `max`, `(0, exp((ρ - 1)*μ))`.

    The answer is None where the bound is not decided: a name it reads has
    no value yet, or it holds an expectation or another form that no
    derived parameter's definition admits (`derived_parameter_fault`). A
    bound that has no value at the values raises `_UnvaluedBound` with the
    evaluator's reason: a division by zero, a negative base under a
    fractional power, `log` of a number that is not positive, a result
    beyond the floating-point numbers, or arithmetic, a call or a sign that
    reads a name valued at an infinity, since no arithmetic of infinities
    is defined (AMD-GRAM-006).

    A bound that computes with the written infinity, `2*inf` or `max(inf,
    1)`, has one answer with the same bound written with a name valued at an
    infinity: it has no value, at any values, and raises `_UnvaluedBound`
    where every name it reads has a value and its other forms are those that
    a derived parameter's definition admits."""
    value = _endpoint_at(term, values, infinity)
    if value is not None:
        return value
    valued = {
        name: held for name, held in values.items() if sets.is_number(held) or _is_infinity(held)
    }
    if derived_parameter_fault("", term, valued, (), {}) is not None:
        # the written infinity is the one form that no definition admits
        # here: read as a name valued at an infinity, the bound has no fault
        if (
            "inf" not in valued
            and derived_parameter_fault("", term, {**valued, "inf": math.inf}, (), {}) is None
        ):
            raise _UnvaluedBound(term, _COMPUTES_WITH_THE_INFINITY, at_no_values=True)
        return None
    try:
        return derived_value(term, valued)
    except ValueError as fault:
        raise _UnvaluedBound(term, str(fault)) from None


# why a bound that computes with the written infinity has no value
_COMPUTES_WITH_THE_INFINITY = "it computes with `inf`, and no arithmetic of infinities is defined"


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
    or a difference from its membership in each part (`_number_in`). The
    membership of a bare name valued at an infinity is decided by whether
    the set holds that infinity (`_infinity_in`), as `membership` decides
    it. Every other term whose parameters all have values and which still
    denotes no number there, a boolean, an undefined value or arithmetic
    that reads an infinite value, makes its predicate false.
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
        infinite = _infinite_value(predicate.subject, values)
        if infinite is not None:
            # a name valued at an infinity lies in a set exactly where the
            # set holds that infinity; a set of which a bound has no value
            # at the values decides nothing here
            try:
                held = _infinity_in(infinite, predicate.set, values, set_terms)
            except _UnvaluedBound:
                held = None
            return PredicateValue(held, sets.parameters_read(predicate.subject))
        subject = sets.number_at(predicate.subject, values)
        if subject.value is None:
            invalid = sets.invalid_number(predicate.subject, values)
            return PredicateValue(False if invalid else None, subject.read)
        return PredicateValue(
            _number_in(subject.value, predicate.set, values, set_terms), subject.read
        )
    return PredicateValue(None, frozenset())


def _infinity_in(infinite, setterm, values, set_terms, active=frozenset()):
    """Whether a set holds the infinity `infinite`, `inf` or `-inf`, at the
    values: True, False, or None where it is not decided. The answer is the
    one `membership` gives for that value, form by form (AMD-GRAM-006). A
    set of extended reals holds the infinity of each side it reaches, and a
    real set and an integer set none. A set the stage defines is read
    through its definition, and a name it does not define is not decided.
    An interval is read from its endpoints at the values, where an endpoint
    that is a bare name valued at an infinity is that infinity
    (`_valued_endpoints`). A union holds it where one member does, and a
    difference where the left side does and the right side does not. A set
    with conditions holds it where its base does and every condition holds
    at it (`_conditions_at`). A set of labels, a product and a list or a
    range of finite numbers hold no infinity. `set_terms` are the sets the
    stage defines by name, and `active` the names being read."""
    if isinstance(setterm, T.Space):
        return _infinity_in(infinite, setterm.set, values, set_terms, active)
    if isinstance(setterm, T.Named):
        if setterm.name in PRIMITIVE_SETS:
            return may_hold_infinity(setterm, negative=infinite < 0)
        if setterm.name in active or setterm.name not in set_terms:
            return None
        defined = set_terms[setterm.name]
        return _infinity_in(infinite, defined, values, set_terms, active | {setterm.name})
    if isinstance(setterm, T.Interval):
        bounds = sets.endpoints(setterm) or _valued_endpoints(setterm, values)
        if bounds is None:
            return None
        lower, lower_closed, upper, upper_closed = bounds
        above = infinite >= lower if lower_closed else infinite > lower
        below = infinite <= upper if upper_closed else infinite < upper
        return above and below
    if isinstance(setterm, (T.SetUnion, T.SetDifference)):
        union = isinstance(setterm, T.SetUnion)
        parts = setterm.members if union else (setterm.left, setterm.right)
        answers = [_infinity_in(infinite, part, values, set_terms, active) for part in parts]
        if union:
            held = True in answers
            excluded = all(answer is False for answer in answers)
        else:
            held = answers[0] is True and answers[1] is False
            excluded = answers[0] is False or answers[1] is True
        return False if excluded else True if held else None
    if isinstance(setterm, T.Comprehension):
        coordinates = setterm.bound.coordinates if isinstance(setterm.bound, T.Subject) else ()
        if (
            len(coordinates) != 1
            or not isinstance(coordinates[0], T.Coordinate)
            or setterm.base is None
        ):
            return None
        held = _infinity_in(infinite, setterm.base, values, set_terms, active)
        if held is False:
            return False
        bound = coordinates[0].stem
        failed, undecided = _conditions_at(setterm, bound, {**values, bound: infinite})
        if failed is not None:
            return False
        return None if undecided else held
    if isinstance(setterm, (T.IntegerRange, T.Points)):
        # the members of a range or of a list are finite numbers, where
        # they are decided
        members = sets.finite_members(setterm, values, set_terms)
        return None if members is None else False
    if isinstance(setterm, T.Functions):
        first, _ = sets.index_sets(setterm, set_terms)
        return None if sets.finite_members(first, values, set_terms) is None else False
    if isinstance(setterm, (T.FiniteSet, T.Product)):
        return False
    return None


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
    if primitive is not None and primitive.kind == EXTENDED_REAL:
        # every extended real set holds every finite real number
        return True
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
