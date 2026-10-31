"""The three binding verbs of a stage (AMD-SG-006 §4; AMD-SG-007 §3), in the
order a stage is bound: `calibrate`, `methodize` and `configure`. A reader
calls each as the stage's method, `stage.calibrate(x)`, `stage.methodize(x)`
and `stage.configure(x)`, since the class body of `ElaboratedStage` binds
them. Each verb adds its bindings, and `methodize` the rows of the method
blocks it binds, to the stage it is called on and returns that stage: nothing
is copied, and a later binding of a target replaces the earlier one
(specification 0.6 §4.1 and decision 1).

Each verb is its inner form: `calibrated_version`, `methodized_version` and
`configured_version` bind the stage they are given in place through
`versions.bind_in_place` and refuse as the verb refuses, a refused binding
leaving the stage as it was. `elaborate_stage` binds the sources a record
supplies by the inner forms on the stage it constructs and copies that
stage once, at the end; the trellis's route binds each stage occurrence by
them on a version of its own.

`calibrate` decides the conditions of the stage that its parameters alone
settle at the values (`calibrated_obligations`); `methodize` attaches the
methods a methods file names (`method_table.attached_bindings`); `configure`
checks each option of an attached method at the settings bound.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import NamedTuple, Union

from bellman.distributions.families import law_support
from bellman.fold.block_lines import fields_of, parameter_sets, require_stage
from bellman.fold.conditions import check_calibrated_distributions
from bellman.fold.stage_fold import stage_blocks_of
from bellman.fold.stage_names import StageNames
from bellman.native.frozen import freeze
from bellman.native.identity import Identity
from bellman.native.predicates import Predicate
from bellman.native.provenance import binding_provenance
from bellman.native.records import Provenance, bound_at
from bellman.native.versions import StageVersion, bind_in_place, stored
from bellman.refusals import ConstructionError
from bellman.stage.boxes import builder_rows_of
from bellman.stage.calibration_requirements import (
    calibration_requirements,
    collection_values,
    declared_set_terms,
    predicate_value,
)
from bellman.stage.grains import construction_table, declared_table
from bellman.stage.method_table import METHOD_TYPES, attached_bindings
from bellman.stage.sources import load_calibration, load_methods, load_settings
from bellman.fold.wire_terms import term_nodes
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.typing import sets
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


def methodize(stage, methods_source):
    """The stage itself, with the supplied methods bound to their targets
    and the rows of the method blocks they name in its operative builders
    (specification 0.6 §§4.1, 7).

    A path or source mapping supplies the entries; a block file an entry
    names under `block:` is read relative to the methods file. Each known
    method must admit its target's kind. Unknown methods, unresolved
    targets, a block whose header does not match its builder and a line of a
    block that calls an undefined function refuse, and a refused binding
    leaves the stage as it was. A target holds one binding of each kind, and
    a later binding replaces the earlier. Nothing is copied, and the initial
    diagrams and the declared builders, `stage.declared`, do not change.

    See `docs/Bellman-Sym/API/stage/09-binding-verbs.md` §3."""
    return methodized_version(stage, methods_source)


def _methods_folder(source, provenance):
    """The folder of the methods file, against which the paths of the block
    files it names are read: the folder of a source given by its path, and
    otherwise the folder `methods_folder` reads from the provenance."""
    if isinstance(source, (str, Path)):
        return Path(source).parent
    return methods_folder(provenance)


def methods_folder(provenance):
    """The folder of the methods file a provenance records, of a stage or of
    a record a recipe or a trellis file supplies, for a methods source given
    as the mapping a factory read from that file: the folder of the path
    under `sources`, or else the one folder in which every file its
    `source_lists` names for the methods stands; None where none is
    known."""
    recorded = (provenance.get("sources") or {}).get("methods") or {}
    if "path" in recorded:
        return Path(recorded["path"]).parent
    listed = (provenance.get("source_lists") or {}).get("methods") or ()
    folders = {Path(entry["path"]).parent for entry in listed if "path" in entry}
    return folders.pop() if len(folders) == 1 else None


def configure(stage, settings_source: Union[str, Path, dict]):
    """The methodized stage itself, with settings bound. Every name an
    attached method's settings reference, including names in nested grids or
    mappings, must have a value in the source or in the settings bound
    before; a later value of a setting replaces the earlier one, and a refused
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
    calibration_requirements(
        stage, values
    )  # refuses a missing value and a value outside its declared set
    # a collection given as a mapping is bound as the sequence of its entries
    # in the order of the members of its index set at the values, so that a
    # version binds one representation, every check reads it and a compiled
    # kernel reads an array
    bound = collection_values(stage, values)
    check_calibrated_distributions(
        stage, bound
    )  # refuses a distribution the values make invalid (AMD-SG-009 §4)
    calibrated_supports(stage, calibrated_obligations(stage, stage.obligations(), bound), bound)
    # Parameters remain named in the retained equations; the bound values are
    # the calibration mapping of the new version, inspectable beside the
    # declarations.
    calibration = freeze({name: bound[name] for name in parameter_sets(stage)})
    provenance = binding_provenance(stage, "calibrate", calibration_source, values)
    return bind_in_place(
        stage,
        bindings=replace(stage.bindings, calibration=calibration),
        provenance=_provenance_record(provenance),
    )


def methodized_version(stage, methods_source, *, replace_all=False, base=None):
    """`stage` with the methods of `methods_source` bound in place, the
    version `methodize` returns, the rows of the method blocks they name in
    its operative builders. With `replace_all`, the methods bound before and
    the blocks they opened are replaced by those of the source as a whole, as
    the trellis's route replaces a position's methods when its methods source
    changes; otherwise a later binding replaces an earlier binding of its own
    kind at its target. `base` is the folder against which the block paths of
    a source given as a mapping are read, where the caller knows it from the
    record that supplies the mapping (`bind_stage`); otherwise the folder is
    read from the source's path or the stage's provenance. Refuses as
    `methodize` refuses, leaving the stage as it was."""
    if not isinstance(stage, StageVersion):
        raise TypeError(
            "methodize requires an ElaboratedStage, the "
            "stage elaborate_stage and make_stage return"
        )
    loaded = load_methods(methods_source)
    provenance = binding_provenance(stage, "methodize", methods_source, loaded)
    # the declared rows are folded before a block adds its definitions
    declared_table(stage)
    bindings, definitions = attached_bindings(
        stage,
        loaded,
        base=_methods_folder(methods_source, provenance)
        if base is None or isinstance(methods_source, (str, Path))
        else base,
        replace_all=replace_all,
    )
    rows_changed = bindings.blocks is not stored(stage, "bindings").blocks
    records = {"bindings": bindings, "provenance": _provenance_record(provenance)}
    if rows_changed:
        records["definitions"] = definitions
    return bind_in_place(stage, rows_changed=rows_changed, **records)


def _provenance_record(provenance):
    """The provenance a binding records, held as the record a stage holds."""
    return Provenance(freeze(dict(provenance)))


def configured_version(stage, settings_source):
    """`stage` with the settings bound in place, the version `configure`
    returns: the settings bound before, each a later value of the source
    replacing its earlier one. Refuses as `configure` refuses, leaving the
    stage as it was."""
    if not isinstance(stage, StageVersion):
        raise TypeError(
            "configure requires an ElaboratedStage, the "
            "stage elaborate_stage and make_stage return"
        )
    # a refusal says where, what happened, why and what to write
    # (AMD-SG-006 §6a)
    if stage.bindings.methods is None:
        raise ValueError(
            f"stage {stage.name!r}: no methods are bound, so no setting is named; settings are "
            "bound after methods (AMD-SG-006 §4); apply methodize(stage, source) first"
        )
    values = load_settings(settings_source)
    merged = {**(stage.bindings.settings or {}), **values}
    _check_bound_options(stage, merged)
    provenance = binding_provenance(stage, "configure", settings_source, values)
    return bind_in_place(
        stage,
        bindings=replace(stage.bindings, settings=freeze(merged)),
        provenance=_provenance_record(provenance),
    )


# --- calibration: the conditions decided at the values ---


def calibrated_obligations(stage, obligations, values):
    """The obligations of a stage decided at parameter values: an obligation
    made of numeric predicates and owner identities is established where its
    predicates hold at the values, refused where one is false and left
    required where one is not decided; any other obligation stays as it is.

    Only declared parameters are available. Formal coordinates and operator
    binders are excluded even when a parameter has the same spelling.
    No analytic condition or unsupported predicate is claimed established.
    """

    parameters = {name: values[name] for name in parameter_sets(stage) if name in values}
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
    required. Every other obligation stays as it is."""
    ctx = StageNames(stage)
    owners = {tuple(owner.subjects): owner for owner in stage_blocks_of(stage).owners}
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
        read = ", ".join(
            f"{name} = {values[name]!r}"
            for name in parameter_sets(stage)
            if name in values and name in to_source(owner.term)
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


# --- configuration: the options at the settings ---


def _check_bound_options(stage, values):
    """The check of every method option against the settings and the
    calibration bound."""
    for key, method in stage.bindings.methods.items():
        box = bound_at(key)
        options = {
            name: _resolved_option(value, values) for name, value in method.settings.items()
        }
        resolved = {name: option.value for name, option in options.items()}
        missing = tuple(
            dict.fromkeys(name for option in options.values() for name in option.missing)
        )
        if missing:
            name = missing[0]
            names = (
                f"the method !{method.tag} at that place names"
                if method.tag
                else "the entry at that place names"
            )
            raise ValueError(
                f"stage {stage.name!r}, box {str(box)!r}: the settings source supplies no value "
                f"for {name!r}, which {names}; every setting an attached method names is valued "
                "when settings are bound (AMD-SG-006 §4); "
                f"write `{name}: <value>` in the settings source"
            )
        rule = METHOD_TYPES.get(method.tag)
        if rule is not None:
            _check_configured_options(stage, box, method, rule, resolved)


def _check_configured_options(stage, box, method, rule, resolved):
    """The check of resolved values against the method row's closed option
    types: each option by the check of its kind, then the coordinate keys of
    `orders` and `bounds` against each other."""
    coordinates = _method_coordinates(stage, box)
    for name, option in rule.options.items():
        if name not in resolved:
            continue
        if option.kind not in _OPTION_CHECKS:
            raise RuntimeError(f"unknown method option type {option.kind!r}")
        _OPTION_CHECKS[option.kind](stage, box, method, name, resolved[name], coordinates)
    if "orders" in resolved and "bounds" in resolved:
        orders, bounds = resolved["orders"], resolved["bounds"]
        if (
            isinstance(orders, Mapping)
            and isinstance(bounds, Mapping)
            and set(orders) != set(bounds)
        ):
            _refuse_option(
                stage,
                box,
                method,
                "orders/bounds",
                f"their coordinate keys differ: {tuple(orders)!r} and {tuple(bounds)!r}",
                "write the same actual coordinate keys in both options",
            )


def _check_positive_integer(stage, box, method, name, value, coordinates):
    """An option of the kind `positive integer`."""
    if not _positive_integer(value):
        _refuse_option(
            stage,
            box,
            method,
            name,
            f"{value!r} is not a positive integer",
            "write an integer greater than zero",
        )


def _check_positive_real(stage, box, method, name, value, coordinates):
    """An option of the kind `positive real`."""
    if not (_finite_real(value) and value > 0):
        _refuse_option(
            stage,
            box,
            method,
            name,
            f"{value!r} is not a positive real",
            "write a finite value greater than zero",
        )


def _check_seed(stage, box, method, name, value, coordinates):
    """An option of the kind `seed`."""
    if not (type(value) is int and value >= 0):
        _refuse_option(
            stage, box, method, name, f"{value!r} is not a seed", "write a nonnegative integer"
        )


def _check_keyed_by_coordinate(stage, box, method, name, value, coordinates):
    """Refuse an option that is no nonempty mapping."""
    if not isinstance(value, Mapping) or not value:
        _refuse_option(
            stage,
            box,
            method,
            name,
            f"{value!r} is not keyed by coordinate",
            f"write a nonempty mapping keyed by coordinates {tuple(coordinates)!r}",
        )


def _check_orders(stage, box, method, name, value, coordinates):
    """An option of the kind `positive integers by coordinate`."""
    _check_keyed_by_coordinate(stage, box, method, name, value, coordinates)
    unknown = tuple(key for key in value if key not in set(coordinates))
    if unknown or any(not _positive_integer(item) for item in value.values()):
        reason = (
            f"unknown coordinate {unknown[0]!r}; the actual coordinates are {tuple(coordinates)!r}"
            if unknown
            else f"{value!r} does not give positive integers"
        )
        _refuse_option(
            stage, box, method, name, reason, "write positive integer orders at actual coordinates"
        )


def _check_bounds(stage, box, method, name, value, coordinates):
    """An option of the kind `ordered pairs by coordinate`: each pair ordered
    and each endpoint decidably inside the coordinate's declared set."""
    _check_keyed_by_coordinate(stage, box, method, name, value, coordinates)
    unknown = tuple(key for key in value if key not in set(coordinates))
    if unknown:
        _refuse_option(
            stage,
            box,
            method,
            name,
            f"unknown coordinate {unknown[0]!r}; the "
            f"actual coordinates are {tuple(coordinates)!r}",
            "write bounds only at actual coordinates",
        )
    for coordinate, pair in value.items():
        numeric = (
            isinstance(pair, (list, tuple))
            and len(pair) == 2
            and all(_finite_real(item) for item in pair)
        )
        if not numeric or pair[0] >= pair[1]:
            _refuse_option(
                stage,
                box,
                method,
                name,
                f"{pair!r} at {coordinate!r} is not an ordered pair",
                "write [lower, upper] with lower < upper",
            )
        for endpoint in pair:
            member = _point_in_declared_set(stage, endpoint, coordinates[coordinate])
            if member is not True:
                word = "lies outside" if member is False else "is not decidably inside"
                _refuse_option(
                    stage,
                    box,
                    method,
                    name,
                    f"endpoint {endpoint!r} {word} the declared set of {coordinate}",
                    "write endpoints decidably inside the declared set",
                )


def _check_nodes(stage, box, method, name, value, coordinates):
    """An option of the kind `positive integers by shock`: one node count for
    each shock the row at the box integrates, in shock order."""
    count = _integrated_count(stage, box)
    if (
        not isinstance(value, (list, tuple))
        or len(value) != count
        or any(not _positive_integer(item) for item in value)
    ):
        _refuse_option(
            stage,
            box,
            method,
            name,
            f"{value!r} does not give one positive integer for each of {count} shocks",
            "write the node counts as a list in shock order",
        )


def _integrated_count(stage, box):
    """The number of shocks the expectation at the box `box` integrates: those
    of the retained operator row named by `box`, where the fold made one, and
    otherwise the subscript of the expectation occurrence the box names on
    its line, the expectation of a derivative line, which stands in no row of
    its own (AMD-MB-001 §4.3, D4; decision MB-A17)."""
    row = _method_row(stage, box)
    if row is not None and row.identity == box:
        return len(row.integrated)
    address = getattr(box, "address", None)
    occurrence = getattr(box, "occurrence", None)
    if address is None:
        return len(row.integrated) if row is not None else 0
    record = next(
        (
            definition
            for definition in stage.definitions.values()
            if definition.kind == "line" and definition.address == address
        ),
        None,
    )
    if record is None:
        return len(row.integrated) if row is not None else 0
    core = record.equations[0] if record.equations else None
    core = core.core if isinstance(core, T.Slack) else core
    expectations = [
        node
        for node in term_nodes(core)
        if isinstance(node, T.Operator) and node.head == "E"
    ]
    position = 0 if occurrence is None else max(int(occurrence) - 1, 0)
    if position >= len(expectations):
        return len(row.integrated) if row is not None else 0
    return len(expectations[position].subs)


def _check_untyped(stage, box, method, name, value, coordinates):
    """An option of the kind `untyped`, which its handler reads: no check."""


# the check of each kind of option a method row declares, after the checks
# it names, as Python requires
_OPTION_CHECKS = {
    "positive integer": _check_positive_integer,
    "positive real": _check_positive_real,
    "seed": _check_seed,
    "positive integers by coordinate": _check_orders,
    "ordered pairs by coordinate": _check_bounds,
    "positive integers by shock": _check_nodes,
    "untyped": _check_untyped,
}


class ResolvedOption(NamedTuple):
    """One authored option with the setting names it writes read at the bound
    settings: its `value`, of the shape the author wrote, and `missing`, the
    names it writes that the settings do not bind, in the order written."""

    value: object
    missing: tuple


def _resolved_option(value, values):
    """The `ResolvedOption` of one authored option, each setting name it
    writes replaced by the value the settings bind, its shape retained."""
    if isinstance(value, str):
        return (
            ResolvedOption(values[value], ())
            if value in values
            else ResolvedOption(value, (value,))
        )
    if isinstance(value, Mapping):
        if "__yaml_tag__" in value:
            return ResolvedOption(value, ())
        items = {key: _resolved_option(item, values) for key, item in value.items()}
        return ResolvedOption(
            {key: item.value for key, item in items.items()},
            tuple(name for item in items.values() for name in item.missing),
        )
    if isinstance(value, (list, tuple)):
        items = tuple(_resolved_option(item, values) for item in value)
        return ResolvedOption(
            type(value)(item.value for item in items),
            tuple(name for item in items for name in item.missing),
        )
    return ResolvedOption(value, ())


def _method_row(stage, box):
    """The retained operator row at a bound method box, where there is one."""

    try:
        block = box if isinstance(box, str) else box.block
        rows = builder_rows_of(stage, block).closed
    except (AttributeError, KeyError, TypeError, ValueError):
        return None
    found = tuple(row for row in rows if row.identity == box)
    if len(found) == 1:
        return found[0]
    evaluations = tuple(row for row in rows if row.kind == "Evaluation")
    return evaluations[0] if len(evaluations) == 1 else None


def _method_coordinates(stage, box):
    """The declared coordinates of the exact object at a method box."""
    row = _method_row(stage, box)
    if row is None:
        definition = stage.definitions.get(box)
        return dict(definition.coordinates) if definition is not None else {}
    declared, _ = fields_of(stage)
    return {
        identity.field: declared[identity].domain
        for identity in row.arguments
        if identity in declared
    }


def _point_in_declared_set(stage, value, declared):
    """True, false, or None for membership of a numeric endpoint."""

    definitions = {
        definition.identity.field: definition.equations[0]
        for definition in stage.definitions.values()
        if definition.kind == "set" and definition.equations
    }
    point = T.Interval(
        T.Range(left=T.Closed(), lower=T.Number(value), upper=T.Number(value), right=T.Closed())
    )
    return sets.within(point, declared, definitions) if declared is not None else None


def _refuse_option(stage, box, method, option, reason, correction):
    raise ConstructionError(
        f"stage {stage.name!r}, place {box!s}, method !{method.tag}, option {option!r}: {reason}; "
        f"configure requires the option value to have its declared type; {correction}",
        stage=stage.name,
        file=stage.provenance.get("origin"),
        address=str(box),
        rule="method-option-value",
    )


def _positive_integer(value):
    return type(value) is int and value > 0


def _finite_real(value):
    return type(value) is int or type(value) is float and math.isfinite(value)
