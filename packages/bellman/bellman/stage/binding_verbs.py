"""The three binding verbs of a stage (AMD-SG-006 §4; AMD-SG-007 §3), in the
order a stage is bound: `calibrate`, `methodize` and `configure`. A reader
calls each as the stage's method, `stage.calibrate(x)`, `stage.methodize(x)`
and `stage.configure(x)`, since the class body of `ElaboratedStage` binds
them. Each verb binds the stage it is called on and returns that stage:
nothing is copied, and a later binding replaces the earlier one
(specification 0.6 §4.1 and decision 1).

Each verb is its inner form: `calibrated_version`, `methodized_version` and
`configured_version` bind the stage they are given in place through
`versions.bind_in_place` or `versions.rebuild_in_place` and refuse as the
verb refuses, a refused binding leaving the stage as it was.
`elaborate_stage` binds the sources a record supplies by the inner forms on
the stage it constructs and copies that stage once, at the end; the
trellis's route binds each stage occurrence by them on a version of its own.

`calibrate` decides the conditions of the stage that its parameters alone
settle at the values (`calibrated_obligations`); `methodize` reads an
addition, a `.bl` file of typing entries and lines, into the stage through
the union of the files (`bellman.syntax.union`), so that the components of
its signatures are those the stage file and the addition type
(specification 0.7 §6); `configure` values the settings the methods file
declares and checks each place's keyword arguments and grid at the values
(`components.check_bound_values`).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Union

from bellman.distributions.families import law_support
from bellman.fold.block_lines import parameter_sets, setting_sets
from bellman.fold.conditions import check_calibrated_distributions
from bellman.fold.derived_parameters import derived_values
from bellman.fold.stage_fold import stage_blocks_of
from bellman.fold.stage_names import StageNames
from bellman.fold.wire_terms import term_nodes
from bellman.native.frozen import freeze
from bellman.native.identity import Identity
from bellman.native.predicates import Predicate
from bellman.native.provenance import binding_provenance, source_description
from bellman.native.records import Provenance
from bellman.native.versions import StageVersion, bind_in_place, rebuild_in_place, stored
from bellman.refusals import ConstructionError, Location
from bellman.stage.calibration_requirements import (
    UNVALUED,
    calibration_requirements,
    collection_values,
    declared_set_terms,
    judged,
    predicate_value,
)
from bellman.stage.components import check_bound_values, check_components
from bellman.stage.grains import construction_table
from bellman.stage.levels import (
    addition_records,
    construct,
    load_additions,
    methods_location,
    methods_source,
    source_texts,
)
from bellman.stage.places import typings
from bellman.stage.sources import load_calibration, load_settings, settings_key_positions
from bellman.syntax.lower import parse_with_spans
from bellman.syntax.union import union
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.typing.sets import endpoints
from bellman.typing.typed_expressions import predicate_text

# --- the three binding verbs ---


def calibrate(stage, calibration_source: Union[str, Path, dict]):
    """The stage itself, with values for all declared parameters.

    The source must supply each parameter in its declared set. Extra names
    are not bound. Retained parameter-only conditions are decided at those
    values: false conditions refuse; true conditions are established with the
    values as evidence; undecided conditions remain required. The source is
    recorded in provenance; a later calibration replaces the earlier one, and
    a refused calibration leaves the stage as it was.

    See `docs/Bellman-Sym/API/stage/09-binding-verbs.md` §2."""
    return calibrated_version(stage, calibration_source)


def methodize(stage, additions):
    """The stage itself with the additions read into it: the stage file's
    tree with each addition attached, in the order given, elaborated anew
    and held by the stage, so that the components of its signatures, the
    rows a solution method's lines add at the operative level and the lines
    an addition appends are those the union of the files gives.
    `additions` is one addition or a list of them, each the path of a `.bl`
    file or a mapping `{text, origin}` holding its text. A
    call is the whole selection of the occurrence: the additions it names
    replace those read before. The calibration bound before stays bound; the
    settings stay bound and are checked against the new declarations and
    components. Refused as the elaboration of the union refuses, and where
    an addition names another stage, leaving
    the stage as it was.

    See `docs/Bellman-Sym/API/stage/09-binding-verbs.md` §3."""
    return methodized_version(stage, additions)


def configure(stage, settings_source: Union[str, Path, dict]):
    """The stage itself, with settings bound. Every setting the methods file
    declares has a value in the source or in the settings bound before, and
    that value lies in the declared set; every name a bound method's keyword
    arguments or grid write has a value; a keyword's value lies in the
    domain the method's row names and a grid's bounds, counts and nodes are
    in order. A value the source supplies for a name no declaration and no
    bound method names is bound and listed, so that nothing is dropped. A
    later value of a setting replaces the earlier one, and a refused
    configuration leaves the stage as it was.

    See `docs/Bellman-Sym/API/stage/09-binding-verbs.md` §3."""
    return configured_version(stage, settings_source)


# --- the inner forms, each binding the stage it is given in place ---


def calibrated_version(stage, calibration_source):
    """`stage` with the calibration bound in place, the version `calibrate`
    returns. Refuses as `calibrate` refuses, leaving the stage as it was."""
    if not isinstance(stage, StageVersion):
        raise TypeError(
            "calibrate requires an ElaboratedStage, the "
            "stage elaborate_stage and make_stage return"
        )
    values = load_calibration(calibration_source)
    # refuses a missing value, a value outside its declared set and a value
    # for a derived parameter
    calibration_requirements(stage, values)
    # a collection given as a mapping is bound as the sequence of its entries
    # in the order of the members of its index set at the values, so that a
    # version binds one representation, every check reads it and a compiled
    # kernel reads an array
    bound = collection_values(stage, values)
    _check_at_calibration(stage, bound)
    # Parameters remain named in the retained equations; the bound values are
    # the calibration mapping of the new version, inspectable beside the
    # declarations. A derived parameter's value is computed from them where it
    # is read and is not bound.
    calibration = freeze({name: bound[name] for name in parameter_sets(stage)})
    provenance = binding_provenance(stage, "calibrate", calibration_source, values)
    return bind_in_place(
        stage,
        bindings=replace(stage.bindings, calibration=calibration),
        provenance=_provenance_record(provenance),
    )


def methodized_version(stage, additions):
    """`stage` with the additions read into it in place, the version
    `methodize` returns: the stage file's text, which the provenance holds,
    unioned with each addition's (`bellman.syntax.union`), the whole
    elaborated at its two levels and its records written over the stage's,
    every kept answer discarded.
    Refuses as `methodize` refuses, leaving the stage as it was."""
    if not isinstance(stage, StageVersion):
        raise TypeError(
            "methodize requires an ElaboratedStage, the "
            "stage elaborate_stage and make_stage return"
        )
    read = load_additions(additions)
    text, origin, _ = source_texts(stage)
    if not text:
        raise ValueError(
            f"stage {stage.name!r}: its provenance holds no stage text, and an addition is "
            "read with the stage file's tree (specification 0.7 §6); elaborate the stage from "
            "its file with elaborate_stage(load_stage(path))"
        )
    unioned = union(
        parse_with_spans(text, filename=origin),
        [parse_with_spans(held, filename=where) for held, where in read],
    )
    fresh = type(stage)(**construct(type(stage), unioned.term, unioned.spans))
    typings(fresh, unioned.spans)
    check_components(fresh)
    bind_in_place(
        fresh,
        bindings=replace(
            stored(fresh, "bindings"),
            calibration=stage.bindings.calibration,
            settings=stage.bindings.settings,
        ),
    )
    if fresh.bindings.calibration is not None:
        # the additions may define derived parameters and distributions, so
        # the checks the calibration's values decide are made again on the
        # stage they make (AMD-MT-003, build contract §5)
        _check_at_calibration(fresh, fresh.bindings.calibration)
    if fresh.bindings.settings is not None:
        _check_declared_settings(fresh, fresh.bindings.settings, ())
        check_bound_values(fresh, fresh.bindings.settings)
    # the source is described as every binding source is, by its path or
    # origin and the digest of the loaded mapping, and the additions are
    # held with their texts, from which the tree is made again
    description = source_description(methods_source(additions), methods_location(read))
    provenance = freeze(
        {
            **stage.provenance,
            "operation": "methodize",
            "parent": stage.provenance,
            "source": description,
            "sources": {**dict(stage.provenance.get("sources", {})), "methods": description},
            "additions": addition_records(read),
        }
    )
    return rebuild_in_place(
        stage,
        fresh,
        provenance=_provenance_record(provenance),
    )


def _check_at_calibration(stage, bound):
    """The checks the calibration values `bound`, the declared parameters'
    values, decide on `stage`: each derived parameter's value, its definition
    evaluated at them (`derived_values`), which refuses a definition that has
    no value there; then the conditions of the distributions
    (`check_calibrated_distributions`, AMD-SG-009 §4), the parameter-only
    obligations and the supports of the laws (`calibrated_supports`), each at
    the declared values joined by the derived ones, so that every check that
    reads a derived parameter reads its value (AMD-MT-003, build contract
    §5)."""
    known = {**bound, **derived_values(stage, bound)}
    check_calibrated_distributions(stage, known)
    calibrated_supports(stage, calibrated_obligations(stage, stage.obligations(), known), known)


def _provenance_record(provenance):
    """The provenance a binding records, held as the record a stage holds."""
    return Provenance(freeze(dict(provenance)))


def configured_version(stage, settings_source, *, files=None):
    """`stage` with the settings bound in place, the version `configure`
    returns: the settings bound before, each a later value of the source
    replacing its earlier one. Refuses as `configure` refuses, leaving the
    stage as it was. `files` names the settings files whose keys supplied
    the values, in the order they were merged, so that a refused setting
    carries its key's position in its file as a related location; where it
    is None, the source itself where it is a path, and no file otherwise."""
    if not isinstance(stage, StageVersion):
        raise TypeError(
            "configure requires an ElaboratedStage, the "
            "stage elaborate_stage and make_stage return"
        )
    values = load_settings(settings_source)
    if files is None:
        files = (settings_source,) if isinstance(settings_source, (str, Path)) else ()
    merged = {**(stage.bindings.settings or {}), **values}
    _check_declared_settings(stage, merged, tuple(str(path) for path in files))
    check_bound_values(stage, merged)
    provenance = binding_provenance(stage, "configure", settings_source, values)
    return bind_in_place(
        stage,
        bindings=replace(stage.bindings, settings=freeze(merged)),
        provenance=_provenance_record(provenance),
    )


# --- configuration: the declared settings at the values ---


def _check_declared_settings(stage, values, files):
    """The check of every setting the methods file declares at the settings
    `values` (specification 0.7, S1): a declared setting with no value is
    refused under `setting-unvalued`, and a value outside the declared set
    under `setting-outside-set`, each at the position of the declaration,
    which the setting's record carries as `<file>:<line>`. The settings
    files `files`, in the order they were merged, give the related locations
    of a refusal: a value outside its set carries its key's position in its
    file (`settings_key_positions`) under the role `rejected setting`, and
    an unvalued setting carries each file under the role `settings source`.
    The membership is decided as a parameter's is
    (`calibration_requirements`), at the calibration bound and the values
    given, and a faulty value is refused at its own setting, not at a
    setting whose set reads it (`judged`); a membership the set algebra does
    not decide is admitted."""
    definitions = dict(stage.definitions)
    declared = setting_sets(stage)
    memberships = judged(stage, definitions, declared, values, settled=stage.bindings.calibration)
    for name, status, reason in memberships:
        if status is not UNVALUED and status is not False:
            continue
        definition = definitions[Identity("setting", stage=stage.name, field=name)]
        file, _, line = definition.address.rpartition(":")
        position = dict(
            stage=stage.name,
            file=file or stage.provenance.get("origin"),
            line=int(line) if line.isdigit() else None,
            column=1 if line.isdigit() else None,
            address=definition.address,
        )
        if status is UNVALUED:
            raise ConstructionError(
                f"stage {stage.name!r}, setting {name!r}: the settings source supplies no "
                f"value for it; every setting the methods file declares is valued when "
                f"settings are bound; write `{name}: <value>` in the settings source",
                rule="setting-unvalued",
                related=tuple(Location("settings source", file=path) for path in files),
                **position,
            )
        written = to_source(declared[name])
        reason = reason or f"the value {values[name]!r} lies outside the declared set {written}"
        key = settings_key_positions(files).get(name)
        raise ConstructionError(
            f"stage {stage.name!r}, setting {name!r}: {reason}; a setting's value lies in "
            f"the set its declaration names; write a value in {written}",
            rule="setting-outside-set",
            related=() if key is None else (Location("rejected setting", *key, address=name),),
            **position,
        )


# --- calibration: the conditions decided at the values ---


def calibrated_obligations(stage, obligations, values):
    """The obligations of a stage decided at parameter values: an obligation
    made of numeric predicates and owner identities is established where its
    predicates hold at the values, refused where one is false and left
    required where one is not decided; any other obligation stays as it is.

    Only declared parameters and derived parameters are available, a derived
    parameter where `values` holds its value (`derived_values`). Formal
    coordinates and operator binders are excluded even when a parameter has
    the same spelling. No analytic condition or unsupported predicate is
    claimed established.
    """

    derived = [
        d.identity.field for d in stage.definitions.values() if d.kind == "derived_parameter"
    ]
    parameters = {
        name: values[name] for name in (*parameter_sets(stage), *derived) if name in values
    }
    set_terms = declared_set_terms(stage)
    scopes = {}
    for recorded in construction_table(stage).obligations:
        if len(recorded) > 3:
            # the recorded entries are the place, the condition and the node
            # the condition is about; the held item keeps the first two
            scopes.setdefault((recorded[0], tuple(recorded[1][:2])), set()).add(recorded[3])
    result = []
    for item in obligations:
        predicates = tuple(entry for entry in item.entries if isinstance(entry, Predicate))
        # a term among the entries, the power or the division a definedness
        # condition is about, is not evaluated; the two set terms of an
        # inclusion and the place of the selection that owes it are its record
        inert = (Identity, Predicate, T.expr) + (
            (T.setexpr, str) if item.condition == "set-inclusion" else ()
        )
        if not predicates or any(not isinstance(entry, inert) for entry in item.entries):
            result.append(item)
            continue
        formal = {
            name
            for entry in item.entries
            if isinstance(entry, Identity)
            for definition in (stage.definitions.get(entry),)
            if definition is not None
            for name, _ in definition.coordinates
        }
        local_scopes = scopes.get((item.condition, tuple(item.entries[:2])), (formal,))
        answers = tuple(
            (
                predicate,
                predicate_value(
                    predicate,
                    {name: value for name, value in parameters.items() if name not in local},
                    set_terms,
                ),
            )
            for local in local_scopes
            for predicate in predicates
        )
        read = frozenset().union(*(answer.read for _, answer in answers))
        decided = tuple((predicate, answer.value) for predicate, answer in answers)
        evidence = "calibration " + (
            ", ".join(f"{name} = {parameters[name]!r}" for name in parameters if name in read)
            or "(no parameters)"
        )
        if any(value is False for _, value in decided):
            condition = "; ".join(
                dict.fromkeys(
                    predicate_text(predicate) for predicate, value in decided if value is False
                )
            )
            owners = ", ".join(str(entry) for entry in item.entries if isinstance(entry, Identity))
            raise ValueError(
                f"stage {stage.name!r}, {owners}: {evidence} makes {condition} false; "
                f"calibrate requires every parameter-only obligation to hold (AMD-SG-022 §4); "
                f"write parameter values satisfying {condition} in the calibration source"
            )
        if any(value is None for _, value in decided):
            result.append(item)
            continue
        result.append(replace(item, status="established", evidence=(evidence,)))
    return tuple(result)


# --- calibration: the supports decided at the values ---


def calibrated_supports(stage, obligations, values):
    """The `law-support` conditions of a stage decided at parameter values
    (AMD-SG-036 §4): where the package knows a declared law's support at the
    values, `families.law_support`, and reads the bounds of each subject's
    declared set, the condition is established when the support lies within
    every one of those sets, with the values and the support as evidence, and
    refused when it does not; a support the package does not know, or a
    declared set whose bounds it does not read, leaves the condition
    required. Every other obligation stays as it is. The evidence and the
    refusal name the declared parameters and the derived parameters the law
    reads, the names among the symbols of its term, with their values, a
    derived parameter where `values` holds its value, as
    `calibrated_obligations` names them (AMD-MT-003, build contract §5)."""
    ctx = StageNames(stage)
    owners = {tuple(owner.subjects): owner for owner in stage_blocks_of(stage).owners}
    derived = [
        d.identity.field for d in stage.definitions.values() if d.kind == "derived_parameter"
    ]
    result = []
    for item in obligations:
        if item.condition != "law-support" or item.status != "required":
            result.append(item)
            continue
        subjects = tuple(entry.field for entry in item.entries if isinstance(entry, Identity))
        owner = owners.get(subjects)
        support = law_support(owner, values) if owner is not None else None
        declared = [ctx.sets.get(ctx.resolve(name, None)) for name in subjects]
        bounds = [endpoints(setexpr) if setexpr is not None else None for setexpr in declared]
        if support is None or any(found is None for found in bounds):
            result.append(item)
            continue
        symbols = {
            node.symbol.name
            for node in term_nodes(owner.term)
            if isinstance(node, T.Sym) and isinstance(node.symbol, T.Constant)
        }
        read = ", ".join(
            f"{name} = {values[name]!r}"
            for name in (*parameter_sets(stage), *derived)
            if name in values and name in symbols
        )
        printed = (
            f"{'[' if support.lower_closed else '('}{support.lower:.6g}, "
            f"{support.upper:.6g}{']' if support.upper_closed else ')'}"
        )
        within = all(_interval_within(support, found) for found in bounds)
        sets = ", ".join(to_source(setexpr) for setexpr in declared)
        if not within:
            raise ValueError(
                f"stage {stage.name!r}, {owner.identity}: calibration {read or '(no parameters)'} "
                f"gives the distribution of {', '.join(subjects)} the support {printed}, which "
                f"lies outside the declared set {sets}; calibrate requires every parameter-only "
                f"obligation to hold (AMD-SG-036 §4); write a declared set that contains the "
                f"support, or arguments whose support the set contains"
            )
        result.append(
            replace(
                item,
                status="established",
                evidence=(
                    f"calibration {read or '(no parameters)'}; the support {printed} lies "
                    f"within {sets}",
                ),
            )
        )
    return tuple(result)


def _interval_within(support, bounds):
    """Whether the interval `support` lies within the interval `bounds`, each
    end compared with its closure: an end the support attains must lie
    strictly inside or on a closed end of the bounds."""
    lower_ok = bounds.lower < support.lower or (
        bounds.lower == support.lower and (bounds.lower_closed or not support.lower_closed)
    )
    upper_ok = support.upper < bounds.upper or (
        support.upper == bounds.upper and (bounds.upper_closed or not support.upper_closed)
    )
    return lower_ok and upper_ok
