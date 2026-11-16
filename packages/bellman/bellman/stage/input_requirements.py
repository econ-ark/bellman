"""Checks of supplied continuation fields against their declared sorts."""

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType

import numpy as np

from bellman.fold.block_lines import blocks_in_file_order, header_of
from bellman.fold.derived_parameters import derived_values
from bellman.native.records import UNDECLARED_SET, Condition
from bellman.refusals import ConstructionError, NotConstructed
from bellman.stage.calibration_requirements import _UnvaluedBound, membership
from bellman.stage.levels import declared_version
from bellman.syntax import terms as T
from bellman.syntax.source import may_hold_infinity, to_source
from bellman.syntax.vocabulary import CONTINUATION, EXTENDED_REAL, PRIMITIVE_SETS, VALUE_ROLES
from bellman.typing import sets


def continuation_inputs(stage):
    """External continuation inputs by their authored names, in header order.

    Backward value headers supply the names before policy and forward headers.
    The declared version preserves this contract after a method is selected.
    """
    declared = declared_version(stage)
    boxes = blocks_in_file_order(declared)
    produced = {
        output.identity
        for box in boxes
        for inputs, outputs in (header_of(box),)
        for output in outputs
        if output.identity not in {sort.identity for sort in inputs}
    }

    def priority(box):
        outputs = header_of(box).outputs
        if any(sort.role in VALUE_ROLES for sort in outputs):
            return 0
        return 1 if any(sort.role == "control" for sort in outputs) else 2

    found, identities = {}, set()
    for box in sorted(boxes, key=priority):
        sorts = header_of(box).inputs
        spellings = box.data.input_spellings
        for index, sort in enumerate(sorts):
            if sort.perch != CONTINUATION or sort.role not in VALUE_ROLES:
                continue
            if sort.identity in identities or sort.identity in produced:
                continue
            if len(spellings) != len(sorts):
                raise NotConstructed(
                    "The block has no retained authored names for its continuation inputs.",
                    stage=stage.name,
                    address=box.name,
                    rule="not-constructed",
                )
            found[spellings[index]] = sort
            identities.add(sort.identity)
    return MappingProxyType(found)


def supplied_constants(stage, inputs):
    """Whole constant values by native identity, without copying their data.

    The caller validates a supplied mapping with `check_inputs` first.
    """
    if inputs is None:
        return {}
    return {
        sort.identity: inputs[name]
        for name, sort in continuation_inputs(stage).items()
        if sort.constant and name in inputs
    }


def input_conditions(stage):
    """Requirements on continuation fields before they are supplied."""
    return tuple(_condition(name, sort) for name, sort in continuation_inputs(stage).items())


def check_inputs(stage, values):
    """Check complete continuation data and return the undecided conditions.

    Constants are whole values, including tables and fixed functions. Other
    fields require representing functions on their ordered state coordinates.
    No supplied function is evaluated and no stage binding is changed.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5.1.
    """
    required = continuation_inputs(stage)
    if not isinstance(values, Mapping):
        _refuse(stage, "inputs", "Continuation inputs must be supplied as a mapping.")
    missing = [name for name in required if name not in values]
    unknown = [name for name in values if name not in required]
    if missing or unknown:
        details = []
        if missing:
            details.append("missing " + ", ".join(repr(name) for name in missing))
        if unknown:
            details.append("unknown " + ", ".join(repr(name) for name in unknown))
        _refuse(
            stage,
            "inputs",
            "Continuation inputs have "
            + "; ".join(details)
            + ". Supply exactly "
            + (", ".join(repr(name) for name in required) or "the empty mapping")
            + ".",
        )
    calibration = stage.bindings.calibration
    at = {} if calibration is None else {**calibration, **derived_values(stage, calibration)}
    at.update(
        {
            sort.identity.field: _checking_value(values[name])
            for name, sort in required.items()
            if sort.constant
        }
    )
    constants = supplied_constants(stage, values)
    at.update({str(identity): _checking_value(value) for identity, value in constants.items()})
    set_terms = {
        d.identity.field: d.equations[0]
        for d in stage.definitions.values()
        if d.kind == "set" and d.equations
    }
    undecided = []
    for name, sort in required.items():
        value = values[name]
        if not sort.constant:
            if not callable(value):
                coordinates = ", ".join(identity.field for identity in sort.coordinates)
                _refuse(
                    stage,
                    name,
                    f"Continuation field {name} requires a representing function "
                    f"on ({coordinates}); the supplied value is {value!r}.",
                )
            undecided.append(_condition(name, sort))
            continue
        domain = sets.resolved(sort.domain, set_terms)
        if callable(value) and isinstance(domain, T.Functions):
            undecided.append(_condition(name, sort))
            continue
        domain = _checking_domain(domain, constants)
        try:
            answer, reason = membership(
                stage, dict(stage.definitions), domain, _checking_value(value), at
            )
        except _UnvaluedBound as error:
            _refuse(
                stage, name, f"Continuation field {name} has an undefined declared set: {error}."
            )
        if answer is False:
            _refuse(stage, name, f"Continuation field {name}: {reason}.")
        if answer is not True:
            undecided.append(_condition(name, sort))
    return tuple(undecided)


def _condition(name, sort):
    domain = to_source(sort.domain) if sort.domain is not None else "its declared set"
    if sort.constant:
        explanation = f"The whole constant value of {name} must belong to {domain}."
    else:
        coordinates = ", ".join(identity.field for identity in sort.coordinates)
        explanation = (
            f"The representing function for {name} must be measurable on its "
            f"declared domain, depend only on ({coordinates}) in that order, "
            f"and take values in {domain}."
        )
    return Condition(
        "continuation-input",
        (sort.identity, sort.domain or UNDECLARED_SET, *sort.coordinates),
        status="required",
        explanation=explanation,
    )


def _checking_value(value):
    """A Python checking view that preserves the supplied NumPy data."""
    if isinstance(value, np.ndarray):
        return _checking_value(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {key: _checking_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(_checking_value(item) for item in value)
    return value


def _checking_domain(term, constants):
    """Explicit numeric sets and distinct constant names for input checking."""
    if isinstance(term, T.Named):
        primitive = PRIMITIVE_SETS.get(term.name)
        if primitive is not None and primitive.kind == EXTENDED_REAL:
            return sets.set_of_bounds(
                sets.Bounds(
                    -float("inf"),
                    may_hold_infinity(term, negative=True),
                    float("inf"),
                    may_hold_infinity(term, negative=False),
                )
            )
    if (
        isinstance(term, T.Sym)
        and isinstance(term.symbol, T.Variable)
        and isinstance(term.symbol.when, T.At)
        and isinstance(term.symbol.when.side, T.Continuation)
        and not term.symbol.shift
    ):
        for identity in constants:
            if identity.field == term.symbol.name:
                return T.Sym(T.Constant(str(identity)))
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return dataclasses.replace(
            term,
            **{
                field.name: _checking_domain(getattr(term, field.name), constants)
                for field in dataclasses.fields(term)
            },
        )
    if isinstance(term, tuple):
        return tuple(_checking_domain(item, constants) for item in term)
    return term


def _refuse(stage, name, reason):
    raise ConstructionError(
        reason,
        stage=stage.name,
        file=stage.provenance.get("origin"),
        address="inputs" if name == "inputs" else f"inputs.{name}",
        rule="continuation-input",
    )
