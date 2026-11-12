"""The parameters, and the settings, the stages of one period share
(AMD-COMP-001 §2.3; specification 0.7, S1).

A parameter name that two or more stage occurrences of a period declare
names one parameter of the period, whatever stage declares it: `a_min` in
two stages of one period is one parameter, and the same spelling in another
period is another. The declarations of such a parameter are reconciled and
its value is supplied once for the period. A setting name that two or more
occurrences declare in their methods files names one setting of the period
in the same way, its declared sets reconciled and its value supplied once
for the period (`period_settings`).

`shared_parameters` reads the stage occurrences of one period and answers,
for each parameter name two or more of them declare, the keys that declare
it and the one set the declarations agree on: the set they all declare, or,
where they declare different sets the package reads, a real set or an
interval with numeric endpoints, the intersection of those sets, which
`typing.sets.meet` writes. Two declarations whose intersection is empty,
or is not one the package reads, are refused under
`period-parameter-agreement`; a value cannot establish such an
intersection. It reads no value, so that the symbolic elaboration
identifies the shared parameters without borrowing a calibration.

`period_calibrations` reads the positions of a trellis with the records
the syntactic trellis holds there, and the stage occurrences placed at
them, and answers the calibration mapping to bind at each position: the
record's own mapping, after the recipe's precedence among the stage's own
sources, with the one value the period supplies for each shared parameter.
The suppliers of a shared parameter are the records of the stages that
declare it, and the calibration a stage object placed by hand already
holds. Two suppliers whose values differ are refused, and so is a value
that decidably lies outside the set a declaring stage writes, each
refusal naming the period, the parameter, the stages and the sources, and
carrying the notes of a refused binding, the stage occurrence and the
kind, so that a reader that binds the other kinds after a refused
calibration tells the refusal from one of the elaboration. A position
whose record is a stage object has no mapping to bind and keeps its
calibration; a stage that declares a shared parameter its own sources do
not supply takes the period's value. `period_settings` answers the settings
mapping to bind at each position in the same way, from the records'
settings mappings and the settings a stage object holds, for the settings
the stages of the period share.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import NamedTuple

from bellman.factory.loading import plain_python
from bellman.fold.block_lines import parameter_sets, setting_sets
from bellman.native.identity import Identity
from bellman.refusals import FactoryError
from bellman.stage.elaborated import ElaboratedStage
from bellman.stage.sources import load_calibration, load_settings
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.typing import sets

__all__ = ["SharedParameter", "period_calibrations", "period_settings", "shared_parameters"]

RULE = "period-parameter-agreement"


class SharedParameter(NamedTuple):
    """One parameter, or one setting, two or more stages of a period declare:
    its `name`, the `keys` of the stages that declare it, in the period's
    order, the `domain`, the one retained set term the declarations agree
    on, and its `kind`, `parameter` or `setting`, the same in every
    declaring stage. A setting two stages of one period declare is one
    setting of the period, as a parameter is one parameter (specification
    0.7, S1)."""

    name: str
    keys: tuple
    domain: object
    kind: str = "parameter"


class _Declaration(NamedTuple):
    """One stage's declaration of a parameter: the stage's `key`, the
    `stage`, the set `resolved` through the sets the stage defines by name,
    the reals where the declaration names none, and the set as `written`."""

    key: str
    stage: ElaboratedStage
    resolved: object
    written: str


# --- the declarations of one period reconciled ---


def shared_parameters(stages, address="periods[?]", file=None):
    """The `SharedParameter` of each parameter name two or more of the stage
    occurrences `stages`, by key, declare, by name. The declared sets are
    read through the sets each stage defines by name; sets that are one
    term agree, and sets the package reads meet in their intersection
    (`sets.meet`). Refused under `period-parameter-agreement`, at
    `address`, where two declarations meet in no nonempty set the package
    reads; a refusal names `file`, the trellis file, where one is given."""
    declared = {}
    kinds = {}
    for key, stage in stages.items():
        definitions = _set_definitions(stage)
        for kind, declarations in (
            ("parameter", parameter_sets(stage)),
            ("setting", setting_sets(stage)),
        ):
            for name, setterm in declarations.items():
                resolved = T.Named("ℝ") if setterm is None else sets.resolved(setterm, definitions)
                written = "ℝ" if setterm is None else to_source(setterm)
                declared.setdefault(name, []).append(_Declaration(key, stage, resolved, written))
                kinds.setdefault(name, set()).add(kind)
    shared = {}
    for name, sites in declared.items():
        if len(sites) < 2:
            continue
        if len(kinds[name]) > 1:
            # a name one stage declares as a parameter of the model and
            # another as a setting of a methods file names two things
            raise FactoryError(
                f"the stages {_stages(sites)} of the period declare {name!r} as a parameter "
                "in one and as a setting in another; a name two stages of one period declare "
                "names one parameter or one setting of the period",
                rule=RULE,
                file=file,
                address=address,
                written="; ".join(f"{name} : {site.written} in {site.key}" for site in sites),
                write=f"{name!r} declared as a parameter in every stage of the period, or as "
                "a setting in every methods file, or distinct names",
            )
        terms = [site.resolved for site in sites]
        if all(term == terms[0] for term in terms):
            domain = terms[0]
        else:
            readable = all(sets.endpoints(term) is not None for term in terms)
            domain = sets.meet(terms) if readable else None
            if domain is None:
                differing = sites
                reason = (
                    "which have no nonempty intersection"
                    if readable
                    else "and the package reads no intersection of them, since one is neither "
                    "a real set nor an interval with numeric endpoints"
                )
                raise FactoryError(
                    f"the stages {_stages(differing)} of the period declare the parameter "
                    f"{name!r} with the sets {_sets(differing)}, {reason}; a parameter name "
                    "names one parameter of the period, shared by the stages that declare "
                    "it, so their declared sets agree",
                    rule=RULE,
                    file=file,
                    address=address,
                    written="; ".join(f"{name} : {site.written} in {site.key}" for site in sites),
                    write=f"one set for {name!r} in every stage of the period, or sets the "
                    "package reads whose intersection is not empty, or distinct names for "
                    "distinct parameters",
                )
        shared[name] = SharedParameter(
            name, tuple(site.key for site in sites), domain, next(iter(kinds[name]))
        )
    return shared


def _set_definitions(stage):
    """The sets a stage defines by name, each by its retained term, through
    which a declared set is read."""
    return {
        definition.identity.field: definition.equations[0]
        for definition in stage.definitions.values()
        if definition.kind == "set" and definition.equations
    }


def _stages(sites):
    """The stages of the declarations `sites` in words, each by its key and
    the address of its declaration."""
    return " and ".join(
        f"{site.key} ({_declaration_address(site.stage, site.key)})" for site in sites
    )


def _sets(sites):
    """The sets of the declarations `sites` in words, each as written; a set
    that reads a name its stage defines is followed by the set the stage
    reads it as, since two stages may define one name as two sets."""
    read = [to_source(site.resolved) for site in sites]
    words = [
        site.written if text == site.written else f"{site.written}, read in {site.key} as {text}"
        for site, text in zip(sites, read)
    ]
    return (" and " if words == [site.written for site in sites] else ", and ").join(words)


def _declaration_address(stage, name):
    """The address of a stage's declaration of the parameter or the setting
    `name`, as its definitions table records it, else the stage's origin."""
    definition = stage.definitions.get(
        Identity("parameter", stage=stage.name, field=name)
    ) or stage.definitions.get(Identity("setting", stage=stage.name, field=name))
    address = getattr(definition, "address", None)
    return address or stage.provenance.get("origin") or stage.name


# --- the values of one period reconciled ---

# for each binding kind whose values a period supplies: the kind of the
# shared names it values and the reader of a record's source
_SUPPLIED = {
    "calibration": ("parameter", load_calibration),
    "settings": ("setting", load_settings),
}


def period_calibrations(found, by_period, file=None):
    """The calibration mapping to bind at each position `(h, key)` of
    `found`, the positions `(h, key, address, record)` with the record the
    syntactic trellis holds at each, given `by_period`, the stage
    occurrences placed at the positions, by period and key, every position
    of each period among them: the record's own mapping where the period
    supplies nothing beyond it, the same object; a flat mapping of the
    record's values with the period's value for each shared parameter the
    record does not supply or supplies otherwise; and None for a position
    whose record is a stage object, which has no mapping to bind. The
    suppliers of a shared parameter are the records of its declaring stages
    and the calibration a stage object among them holds. Refused under
    `period-parameter-agreement` where two suppliers' values differ, or a
    supplied value decidably lies outside a declaring stage's set, and as
    `shared_parameters` refuses the declarations; a refusal of a value
    carries the notes `Stage occurrence: <address>` and `Binding kind:
    calibration`."""
    return _period_values(found, by_period, file, "calibration")


def period_settings(found, by_period, file=None):
    """The settings mapping to bind at each position of `found`, as
    `period_calibrations` answers the calibration mapping, for the settings
    two or more stages of a period declare in their methods files
    (specification 0.7, S1): the record's own mapping where the period
    supplies nothing beyond it, the same object; a flat mapping of the
    record's values with the period's value for each shared setting the
    record does not supply or supplies otherwise; and None for a position
    whose record is a stage object. The suppliers of a shared setting are
    the records of its declaring stages and the settings a stage object
    among them holds; two suppliers whose values differ are refused under
    `period-parameter-agreement`, the refusal carrying the notes `Stage
    occurrence: <address>` and `Binding kind: settings`."""
    return _period_values(found, by_period, file, "settings")


def _period_values(found, by_period, file, kind):
    """The mapping of the binding `kind`, `calibration` or `settings`, to
    bind at each position of `found`, as `period_calibrations` and
    `period_settings` answer it."""
    word, load = _SUPPLIED[kind]
    effective = {}
    by_h = {}
    for h, key, address, record in found:
        by_h.setdefault(h, []).append((key, address, record))
    for h, places in by_h.items():
        where = f"periods[{h}]"
        shared = {
            name: parameter
            for name, parameter in shared_parameters(by_period[h], where, file).items()
            if parameter.kind == word
        }
        supplied = {}
        for key, address, record in places:
            if isinstance(record, ElaboratedStage):
                held = getattr(record.bindings, kind)
                supplied[key] = (dict(held) if held is not None else {}, address)
                effective[h, key] = None
            else:
                mapping = record[kind]
                try:
                    values = plain_python(load(mapping)) if mapping else {}
                except Exception as error:
                    # a source the reader refuses is a refused binding, as
                    # the stage verb's refusal of it is noted
                    error.add_note(f"Stage occurrence: {address}")
                    error.add_note(f"Binding kind: {kind}")
                    raise
                supplied[key] = (values, address)
                effective[h, key] = mapping
        period = {}
        for name, parameter in shared.items():
            suppliers = [
                (key, supplied[key][0][name])
                for key in parameter.keys
                if key in supplied and name in supplied[key][0]
            ]
            if not suppliers:
                continue
            first, value = suppliers[0]
            for key, other in suppliers[1:]:
                if not _equal(other, value):
                    _refuse_value(
                        f"the stages {first} and {key} of the period supply the {word} "
                        f"{name!r} with the values {value!r} and {other!r}; a {word} name "
                        f"names one {word} of the period, shared by the stages that declare "
                        f"it, so their sources supply it one value",
                        where,
                        file,
                        written=f"{name}: {value!r} ({_sources(first, places, kind)}); "
                        f"{other!r} ({_sources(key, places, kind)})",
                        write=f"one value of {name!r} in the sources of "
                        f"{', '.join(parameter.keys)}, or distinct names for distinct {word}s",
                        position=supplied[key][1],
                        kind=kind,
                    )
            for key in parameter.keys:
                declared = _declared_set(by_period[h][key], name, word)
                if _outside(value, declared):
                    _refuse_value(
                        f"the value {value!r} of the {word} {name!r}, supplied by {first}, "
                        f"lies outside the set {to_source(declared)} that {key} declares it "
                        f"with; a {word} name names one {word} of the period, so its "
                        f"value lies in the set every declaring stage writes",
                        where,
                        file,
                        written=f"{name}: {value!r} ({_sources(first, places, kind)}); "
                        f"{name} : {to_source(declared)} in {key}",
                        write=f"a value of {name!r} in {to_source(declared)}, or a declared set "
                        f"of {name!r} in every stage that holds the value",
                        position=supplied[first][1],
                        kind=kind,
                    )
            period[name] = value
        for key, address, record in places:
            if effective[h, key] is None:
                continue
            own = supplied[key][0]
            added = {
                name: value
                for name, value in period.items()
                if key in shared[name].keys and (name not in own or not _equal(own[name], value))
            }
            if added:
                effective[h, key] = {**own, **added}
    return effective


def _refuse_value(message, address, file, *, written, write, position, kind):
    """Raise the refusal of a supplied value, with the notes of a refused
    binding of `kind` at `position`."""
    error = FactoryError(
        message, rule=RULE, file=file, address=address, written=written, write=write
    )
    error.add_note(f"Stage occurrence: {position}")
    error.add_note(f"Binding kind: {kind}")
    raise error


def _declared_set(stage, name, word):
    """The set `stage` declares the parameter or the setting `name` with,
    `word` saying which, read through the sets the stage defines by name;
    the reals where it names none."""
    declarations = parameter_sets(stage) if word == "parameter" else setting_sets(stage)
    setterm = declarations.get(name)
    return T.Named("ℝ") if setterm is None else sets.resolved(setterm, _set_definitions(stage))


def _outside(value, declared):
    """Whether a numeric value decidably lies outside a declared set: a
    finite number as a point interval against the set, by `sets.within`;
    False where the value is no number or the pair is not decided, which
    the stage's own calibration then reads."""
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        return False
    point = T.Interval(
        T.Range(left=T.Closed(), lower=T.Number(value), upper=T.Number(value), right=T.Closed())
    )
    return sets.within(point, declared, {}) is False


def _equal(left, right):
    """Whether two supplied values are equal, as `already_bound` compares a
    held value with a given one."""
    try:
        return bool(plain_python(left) == plain_python(right))
    except (TypeError, ValueError):
        return False


def _sources(key, places, kind):
    """The sources of the binding of `kind` at the position `key` of
    `places`, in words: the names of the record's source list of that kind,
    a slot as `$<slot>`, the file a held binding names, or the record
    itself."""
    record = next(record for other, _, record in places if other == key)
    if isinstance(record, ElaboratedStage):
        source = record.provenance.get("sources", {}).get(kind, {})
        return "its binding from " + str(source.get("path") or source.get("origin") or "memory")
    entries = []
    if isinstance(record.get("provenance"), Mapping):
        entries = record["provenance"].get("source_lists", {}).get(kind, [])
    names = [
        entry.get("source") or (f"${entry['slot']}" if entry.get("slot") else None)
        for entry in entries
    ]
    names = [name for name in names if name]
    return ", ".join(names) if names else "its record"
