"""The components typed at the places of a stage, checked against the rows
of the catalogue (specification 0.7 §5, D1, D5; the grid note §3).

At binding, once the typing entries of a stage file and its additions are
resolved to their places (`places.typings`), `check_components` reads the
`Components` of each place against the row of its method word: a keyword
the row requires is written (`method-admission`); every factor of a grid
names a coordinate of the function the place holds, a control for a
feasible factor or a shock for a quadrature factor, and a word that reads no
grid has none written (`grid-coordinate`); every name a factor writes is a
setting a methods file declares, a node set the stage defines or an
expectation operator of the stage, never a number (`grid-setting-declared`).
A coordinate no factor names takes the default (decision S7-C17). At
configuration, `check_bound_values` reads the components at the settings
`configure` binds: every setting a component names has a value
(`setting-unvalued`), a keyword's value lies in the domain its row names
(`method-option-value`), and a grid's bounds are in order and inside the
coordinate's declared set, its counts at least two and its node sets
strictly increasing (`grid-bounds`). The domain a grid discretizes is read
from the stage (`grid_domain`): the coordinates of the function the place
holds, or the continuation states for a word whose row names that perch.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping
from typing import NamedTuple

from bellman.fold.block_lines import (
    blocks_in_file_order,
    fields_of,
    header_of,
    header_wire_sorts,
    setting_sets,
)
from bellman.fold.stage_names import lines_of
from bellman.fold.wire_terms import term_nodes
from bellman.native.identity import Identity
from bellman.native.records import setting_names, typing_text
from bellman.refusals import ConstructionError
from bellman.stage.boxes import builder_rows_of
from bellman.stage.method_table import row_of
from bellman.stage.places import components_by_place, typings
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import CONTINUATION, CONTROL, SHOCK, STATE
from bellman.typing import sets

# --- the components at binding ---


def check_components(stage):
    """The check of the components typed at every place of `stage` against
    the rows of the catalogue, made where the stage is constructed and
    where an addition is read into it: the required keywords, and the
    coordinates and the names of each grid. Each refusal stands at the
    position of the entry, with the place as its address."""
    for place, held, records in _typed_places(stage):
        row = row_of(held.method.name) if held.method is not None else None
        if row is not None:
            _check_keywords(stage, place, held, row, records["method"])
        if held.grid is not None:
            _check_grid(stage, place, held, row, records["grid"])


def _typed_places(stage):
    """Each typed place of the stage with its `Components` and the typing
    records of its components by component name, in the order of the
    places."""
    by_place = components_by_place(stage)
    records = {}
    for typing in typings(stage):
        records.setdefault(typing.place.address, (typing.place, {}))[1][typing.component] = (
            typing.record
        )
    return tuple(
        (place, by_place[address], held) for address, (place, held) in records.items()
    )


def _check_keywords(stage, place, held, row, record):
    """A keyword the row requires is written among the word's arguments,
    one per shock the expectation at the place integrates for a keyword
    written `n_<shock>`. Every bare name in an argument is a declared setting."""
    declared = setting_sets(stage)
    for argument in _word_arguments(held.method):
        if isinstance(argument, T.Name) and argument.name not in declared:
            _refuse(
                stage,
                place,
                record,
                "name-in-scope",
                f"the entry `{typing_text(record)}` reads the setting {argument.name!r}, "
                "which no methods file declares",
                write=f"Declare {argument.name!r} with its set in an addition, or quote "
                "the value if it is literal text",
            )
    written = {keyword.key for keyword in held.method.arguments}
    missing = tuple(
        dict.fromkeys(
            name
            for box in place.boxes
            for name, keyword in keywords_at(stage, row, box).items()
            if keyword.required and name not in written
        )
    )
    if missing:
        _refuse(
            stage,
            place,
            record,
            "method-admission",
            f"the entry `{typing_text(record)}` names `!{held.method.name}` without the "
            f"keyword{'' if len(missing) == 1 else 's'} {', '.join(missing)}, which its row of "
            f"the catalogue requires; write every required keyword using the names shown by "
            f"method_types of bellman.stage",
        )


def _check_grid(stage, place, held, row, record):
    """The two rules of the grid note §3 that bind before configuration: a
    grid at a word that reads none, and a factor that names no coordinate,
    control or shock of the place, under `grid-coordinate`; a number or an
    undeclared name among the factors under `grid-setting-declared`. An
    entry that names no method word binds its grid as the discretized
    domain of the place, which the handler reads."""
    if row is not None and row.grid is None:
        _refuse(
            stage,
            place,
            record,
            "grid-coordinate",
            f"!{held.method.name} reads no grid, and the place writes the grid "
            f"{to_source(held.grid)}; a grid is read by a representation, by a solution "
            f"method on the states of a perch and by a handler; remove the grid entry",
            write=f"Remove the grid entry of `{place.address}`",
        )
    for box in place.boxes:
        _check_grid_coordinates(
            stage, place, record, held.grid, box, grid_domain(stage, box, place.block, row)
        )
    _check_grid_names(stage, place, record, held.grid)


def _check_grid_coordinates(stage, place, record, grid, box, domain):
    """The rule `grid-coordinate` at one box of the place: every factor of
    the grid names a coordinate of the function the box holds, a control of
    the stage for a feasible factor, or a shock for a quadrature factor. A
    grid may name a factor for some coordinates of the function and none for
    the others: a coordinate no factor names takes the default, as every
    coordinate does where the place writes no grid entry (decision S7-C17).
    The entry is recorded as written, with the named factors alone."""
    coordinates = ", ".join(domain.states) or "none"
    for factor in grid.factors:
        name = factor.coordinate
        if isinstance(factor, T.Feasible):
            if name not in domain.controls:
                _refuse(
                    stage,
                    place,
                    record,
                    "grid-coordinate",
                    f"the factor {to_source(factor)} of the grid names {name!r} as a control, "
                    f"and the controls of the stage are "
                    f"{', '.join(domain.controls) or 'none'}; a feasible factor is written for "
                    f"a control, its feasible set with a count",
                )
        elif isinstance(factor, T.Listed) and factor.nodes in domain.expectations:
            if name not in domain.shocks:
                _refuse(
                    stage,
                    place,
                    record,
                    "grid-coordinate",
                    f"the factor {to_source(factor)} of the grid takes the nodes of the "
                    f"expectation {factor.nodes} for {name!r}, which is no shock of the stage; "
                    f"a quadrature factor is written for a shock, "
                    f"{', '.join(domain.shocks) or 'of which the stage has none'}",
                )
        elif name not in domain.states:
            # the edit is established where the function has one coordinate
            state = next(iter(domain.states)) if len(domain.states) == 1 else None
            _refuse(
                stage,
                place,
                record,
                "grid-coordinate",
                f"the factor {to_source(factor)} of the grid names {name!r}, which is no "
                f"coordinate of the function at {place.address}; the coordinates are "
                f"{coordinates}; a factor names one of them, keyed by its name, and a "
                f"coordinate no factor names takes the default",
                write=(
                    f"Write the factor for {state}, "
                    f"`{to_source(dataclasses.replace(factor, coordinate=state))}`"
                    if state is not None
                    else None
                ),
            )


def _check_grid_names(stage, place, record, grid):
    """The rule `grid-setting-declared`: every name a factor writes is a
    setting a methods file declares, a node set the stage defines or an
    expectation operator of the stage, and a bound or a count written as a
    number is refused."""
    declared = set(setting_sets(stage))
    defined = {
        definition.identity.field
        for definition in stage.definitions.values()
        if definition.kind in ("set", "correspondence")
    }
    expectations = expectation_names(stage)

    def refuse(factor, reason, write):
        _refuse(
            stage,
            place,
            record,
            "grid-setting-declared",
            f"the factor {to_source(factor)} of the grid {reason}; {write}",
        )

    for factor in grid.factors:
        for argument in _factor_arguments(factor):
            if isinstance(argument, T.Literal):
                refuse(
                    factor,
                    f"writes the number {to_source(argument)}",
                    "a bound and a count are settings declared in the methods file and valued "
                    "in the settings file; write the setting's name",
                )
            if argument.name not in declared:
                refuse(
                    factor,
                    f"names {argument.name!r}, which no methods file declares as a setting",
                    f"declare it with its set, `{argument.name} : ℕ` or "
                    f"`{argument.name} : <the coordinate's set>`, at file level",
                )
        if isinstance(factor, T.Listed):
            nodes = factor.nodes
            if not (nodes in defined or nodes in expectations or nodes in declared):
                refuse(
                    factor,
                    f"names {nodes!r}, which is no setting the methods file declares, no set the "
                    "stage defines and no expectation operator of the stage",
                    "write a declared setting valued by the nodes, a set defined by its "
                    "members, or the expectation whose quadrature nodes the coordinate takes",
                )
        if isinstance(factor, T.Feasible) and factor.set not in defined:
            refuse(
                factor,
                f"names {factor.set!r} as a feasible set, which the stage does not define",
                "write the correspondence or the set of the control, as the stage names it",
            )


def _factor_arguments(factor):
    """The arguments of a factor that name a setting or write a number: the
    bounds and the count of a spaced factor with the arguments of its spacing
    word, and the count of a feasible factor."""
    if isinstance(factor, T.Spaced):
        found = [factor.lower, factor.upper, factor.count]
        if factor.spacing is not None:
            found.extend(_word_arguments(factor.spacing))
        return tuple(found)
    if isinstance(factor, T.Feasible):
        return (factor.count,)
    return ()


def _word_arguments(word):
    """The `Name` and `Literal` arguments a word's keywords write, at every
    depth of its tuples and nested words."""

    def of(value):
        if isinstance(value, (T.Name, T.Literal)):
            yield value
        elif isinstance(value, T.Values):
            for item in value.items:
                yield from of(item)
        elif isinstance(value, T.Nested):
            yield from _word_arguments(value.word)

    return tuple(found for keyword in word.arguments for found in of(keyword.value))


def _refuse(stage, place, record, rule, message, *, write=None):
    """The refusal of a component typed at `place` under `rule`, at the
    position of the typing record `record`, which its address holds as
    `<file>:<line>:<column>`, with the place as the address the refusal
    names and the action `write` where the check establishes the edit."""
    file, _, column = str(record.address).rpartition(":")
    file, _, line = file.rpartition(":")
    positioned = line.isdigit() and column.isdigit()
    raise ConstructionError(
        f"stage {stage.name!r}, place {place.address!r}: {message}",
        stage=stage.name,
        file=(file or None) if positioned else stage.provenance.get("origin"),
        line=int(line) if positioned else None,
        column=int(column) if positioned else None,
        address=place.address,
        rule=rule,
        write=write,
    )


# --- the grid: the discretized domain of a place ---


class GridDomain(NamedTuple):
    """The coordinates a grid at one place may discretize: `states`, the
    coordinates of the function the place holds, each with its declared set,
    in declared order, for each of which a grid may name a factor;
    `controls`, the controls of the stage with their declared sets, for a
    feasible factor; `shocks`, the shocks of the stage, for a quadrature
    factor; and `expectations`, the stage-wide names of the expectation
    operators, `E_ψ_ξ`, whose nodes a quadrature factor takes."""

    states: Mapping
    controls: Mapping
    shocks: tuple
    expectations: frozenset


def grid_domain(stage, box, block, row):
    """The `GridDomain` of the box `box` in the builder `block`, for a word
    whose row is `row`, None for a place with no method word: the states
    are those of the continuation perch for a word whose row names it,
    `!egm`, and otherwise the coordinates of the function the box holds
    (`place_coordinates`)."""
    states = (
        _perch_states(stage, CONTINUATION)
        if row is not None and row.grid == CONTINUATION
        else place_coordinates(stage, box, block)
    )
    # the controls of the stage, which stand at the decision perch, for a
    # feasible factor; the shocks of the stage for a quadrature factor
    declared, _ = fields_of(stage)
    controls = {}
    for identity, sort in header_wire_sorts(stage).items():
        if sort.role == CONTROL:
            controls.setdefault(identity.field, sort.domain)
    shocks = tuple(dict.fromkeys(i.field for i, sort in declared.items() if sort.role == SHOCK))
    return GridDomain(states, controls, shocks, expectation_names(stage))


def place_coordinates(stage, box, block):
    """The coordinates of the function the box `box` holds, each with its
    declared set, in declared order: the arguments of the retained row at
    the box, the one Evaluation of the builder where the box is the builder
    itself, the coordinates of a declared function, and otherwise the states
    of the perch at which the outputs of the builder `block` stand, the
    output perch of a forward builder."""
    row = _place_row(stage, box)
    declared, _ = fields_of(stage)
    if row is not None and row.arguments:
        return {
            identity.field: declared[identity].domain
            for identity in row.arguments
            if identity in declared
        }
    definition = stage.definitions.get(box) if isinstance(box, Identity) else None
    if definition is not None:
        return _definition_coordinates(stage, definition)
    return _perch_states(stage, _output_perch(stage, block))


def _definition_coordinates(stage, definition, seen=frozenset()):
    """The coordinates of a declared function with their sets; for a function
    alias, those of the function its body refers to or differentiates,
    `𝑑𝑢 := D_{c}(𝑢)`, and none for an alias of another form, such as an
    inverse, whose argument is no named coordinate."""
    if definition.coordinates or definition.kind != "function_alias" or not definition.equations:
        return dict(definition.coordinates)
    body = definition.equations[0]
    if isinstance(body, T.Operator) and body.head == "D" and len(body.args) == 1:
        body = body.args[0]
    name = body.symbol.name if isinstance(body, T.Sym) and isinstance(body.symbol, T.Constant) else None
    if name is None or name in seen:
        return {}
    referred = next(
        (
            d
            for d in stage.definitions.values()
            if d.kind in ("function", "function_alias") and d.identity.field == name
        ),
        None,
    )
    return {} if referred is None else _definition_coordinates(stage, referred, seen | {name})


def _place_row(stage, box):
    """The retained operator row at a box, where there is one: the row whose
    identity is the box, or the one Evaluation of the builder for a box that
    is the builder itself; None otherwise, and for a builder whose rows the
    construction refuses."""
    block = box if isinstance(box, str) else getattr(box, "block", None)
    if block is None:
        return None
    try:
        rows = builder_rows_of(stage, block).closed
    except (KeyError, TypeError, ValueError, ConstructionError):
        return None
    found = tuple(row for row in rows if row.identity == box)
    if len(found) == 1:
        return found[0]
    evaluations = tuple(row for row in rows if row.kind == "Evaluation")
    return evaluations[0] if len(evaluations) == 1 else None


def _output_perch(stage, block):
    """The perch at which the outputs of the builder `block` stand, read
    from the sort of its first output wire; None for no such builder."""
    ports = header_wire_sorts(stage)
    held = next((b for b in blocks_in_file_order(stage) if b.name == block), None)
    if held is None:
        return None
    for wire in header_of(held).outputs:
        if wire.identity in ports:
            return wire.identity.perch
    return None


def _perch_states(stage, perch):
    """The declared states of the perch `perch` with their declared sets, in
    first-listing order."""
    declared, _ = fields_of(stage)
    return {
        identity.field: declared[identity].domain
        for identity, sort in header_wire_sorts(stage).items()
        if identity.perch == perch and sort.role == STATE and identity in declared
    }


def expectation_names(stage):
    """The stage-wide names of the expectation operators the lines of the
    stage write, `E_ψ_ξ`, which a quadrature factor names."""
    return frozenset(
        occurrence.stage_wide_name
        for block in blocks_in_file_order(stage)
        for _, record in lines_of(stage, block)
        for occurrence in record.operators
        if occurrence.head == "E"
    )


# --- the keyword arguments at a place ---


def keywords_at(stage, row, box):
    """The keyword arguments the row `row` reads at the box `box`, by name,
    each its `MethodOption`: the row's keywords, a keyword written
    `n_<shock>` expanded to one per shock the expectation at the box
    integrates, `n_ψ`, `n_ξ`."""
    found = {}
    for name, keyword in row.keywords.items():
        if "<shock>" in name:
            for shock in _integrated_shocks(stage, box):
                found[name.replace("<shock>", shock)] = keyword
        else:
            found[name] = keyword
    return found


def _integrated_shocks(stage, box):
    """The shocks the expectation at the box `box` integrates, by name: those
    of the retained operator row named by `box`, where the fold made one, and
    otherwise the subscript of the expectation occurrence the box names on
    its line, the expectation of a derivative line, which stands in no row
    of its own (AMD-MB-001 §4.3, D4; decision MB-A17)."""
    row = _place_row(stage, box)
    held = tuple(getattr(shock, "field", shock) for shock in row.integrated) if row else ()
    if row is not None and row.identity == box:
        return held
    address = getattr(box, "address", None)
    occurrence = getattr(box, "occurrence", None)
    if address is None:
        return held
    record = next(
        (d for d in stage.definitions.values() if d.kind == "line" and d.address == address),
        None,
    )
    if record is None or not record.equations:
        return held
    core = record.equations[0]
    core = core.core if isinstance(core, T.Slack) else core
    expectations = [
        node for node in term_nodes(core) if isinstance(node, T.Operator) and node.head == "E"
    ]
    position = 0 if occurrence is None else max(int(occurrence) - 1, 0)
    if position >= len(expectations):
        return held
    return tuple(getattr(sub, "name", sub) for sub in expectations[position].subs)


# --- the configured values: the keywords and the grids at the settings ---


def check_bound_values(stage, values):
    """The check of every place's keyword arguments and grid at the settings
    `values`, which `configure` makes: a name a keyword or a factor writes
    that the settings do not value is refused under `setting-unvalued`; a
    keyword's value outside the domain its row names under
    `method-option-value`; and a grid whose bounds are out of order or
    outside the coordinate's declared set, whose count is below two or whose
    node set is not strictly increasing, under `grid-bounds` (the grid note
    §3). A set the stage defines and an expectation operator, which a listed
    factor may name, need no value."""
    expectations = expectation_names(stage)
    defined = {
        d.identity.field
        for d in stage.definitions.values()
        if d.kind in ("set", "correspondence")
    }
    for place, held, _ in _typed_places(stage):
        row = row_of(held.method.name) if held.method is not None else None
        for name in dict.fromkeys(setting_names(held)):
            if name not in values and name not in defined and name not in expectations:
                named = (
                    f"the method !{held.method.name} at that place names"
                    if held.method is not None
                    else "the entry at that place names"
                )
                raise ConstructionError(
                    f"stage {stage.name!r}, place {place.address!r}: the settings source "
                    f"supplies no value for {name!r}, which {named}; every setting a bound "
                    f"method names is valued when settings are bound; write `{name}: <value>` "
                    f"in the settings source",
                    stage=stage.name,
                    file=stage.provenance.get("origin"),
                    address=place.address,
                    rule="setting-unvalued",
                )
        if row is not None:
            written = {keyword.key: keyword.value for keyword in held.method.arguments}
            for box in place.boxes:
                for name, keyword in keywords_at(stage, row, box).items():
                    if name in written:
                        _check_domain(
                            stage, place, held, name, keyword, _valued(written[name], values)
                        )
        if held.grid is not None:
            for box in place.boxes:
                _check_grid_bounds(
                    stage, place, held, values, grid_domain(stage, box, place.block, row)
                )


def _valued(argument, values):
    """A keyword argument or a factor's argument at the settings `values`:
    a setting's name replaced by its value, a number and a quoted string as
    written, a tuple entry by entry, and a word with its arguments as it
    stands, for its handler."""
    if isinstance(argument, T.Name):
        return values.get(argument.name, argument.name)
    if isinstance(argument, T.Literal):
        return argument.value
    if isinstance(argument, T.Quoted):
        return argument.text
    if isinstance(argument, T.Values):
        return tuple(_valued(item, values) for item in argument.items)
    return argument


# the domain of a keyword's value as a row names it, each a check that
# answers the reason a value lies outside it, or None
_DOMAINS = {
    "positive integer": lambda value: (
        None if _positive_integer(value) else f"{value!r} is not a positive integer"
    ),
    "positive real": lambda value: (
        None if _finite_real(value) and value > 0 else f"{value!r} is not a positive real"
    ),
    "seed": lambda value: (
        None if type(value) is int and value >= 0 else f"{value!r} is not a seed"
    ),
}

# what to write for a value outside each domain
_WRITE = {
    "positive integer": "write an integer greater than zero",
    "positive real": "write a finite value greater than zero",
    "seed": "write a nonnegative integer",
}


def _check_domain(stage, place, held, name, keyword, value):
    """The refusal of a keyword's value outside the domain its row names,
    under `method-option-value`."""
    if keyword.kind not in _DOMAINS:
        raise RuntimeError(f"unknown keyword domain {keyword.kind!r}")
    reason = _DOMAINS[keyword.kind](value)
    if reason is None:
        return
    raise ConstructionError(
        f"stage {stage.name!r}, place {place.address!r}, method !{held.method.name}, keyword "
        f"{name!r}: {reason}; configure requires the value to lie in the domain the method's "
        f"row names; {_WRITE[keyword.kind]}",
        stage=stage.name,
        file=stage.provenance.get("origin"),
        address=place.address,
        rule="method-option-value",
    )


def _check_grid_bounds(stage, place, held, values, domain):
    """The rule `grid-bounds` at the settings: for a spaced factor the lower
    bound below the upper, both finite and inside the coordinate's declared
    set, and the count an integer of at least two; for a listed factor
    valued by the settings a strictly increasing sequence of at least two
    finite reals inside the set; for a feasible factor a count of at least
    two. A factor on a control or a shock has no declared set to check."""

    def refuse(factor, reason, write):
        raise ConstructionError(
            f"stage {stage.name!r}, place {place.address!r}, grid {to_source(held.grid)}: the "
            f"factor {to_source(factor)} {reason}; configure requires the bounds of a factor in "
            f"order and inside the coordinate's declared set, its count at least two and a "
            f"node set strictly increasing; {write}",
            stage=stage.name,
            file=stage.provenance.get("origin"),
            address=place.address,
            rule="grid-bounds",
        )

    def inside(factor, point, declared):
        if declared is None:
            return
        member = _point_in_declared_set(stage, point, declared)
        if member is not True:
            word = "lies outside" if member is False else "is not decidably inside"
            refuse(
                factor,
                f"writes the point {point!r}, which {word} the declared set "
                f"{to_source(declared)} of {factor.coordinate}",
                "write points inside the declared set",
            )

    for factor in held.grid.factors:
        declared = domain.states.get(factor.coordinate)
        if isinstance(factor, T.Spaced):
            lower, upper, count = (
                _valued(part, values) for part in (factor.lower, factor.upper, factor.count)
            )
            if not (_finite_real(lower) and _finite_real(upper)) or lower >= upper:
                refuse(
                    factor,
                    f"has the bounds {lower!r} and {upper!r}, which are not two finite reals in "
                    "order",
                    "write a lower bound below the upper bound",
                )
            if not _positive_integer(count) or count < 2:
                refuse(factor, f"has the count {count!r}", "write an integer count of at least two")
            for point in (lower, upper):
                inside(factor, point, declared)
        elif isinstance(factor, T.Listed) and factor.nodes in values:
            points = values[factor.nodes]
            increasing = (
                isinstance(points, (list, tuple))
                and len(points) >= 2
                and all(_finite_real(point) for point in points)
                and all(lower < upper for lower, upper in zip(points, points[1:]))
            )
            if not increasing:
                refuse(
                    factor,
                    f"takes the node set {factor.nodes} = {points!r}, which is no strictly "
                    "increasing sequence of at least two finite reals",
                    "write the nodes in increasing order",
                )
            for point in points:
                inside(factor, point, declared)
        elif isinstance(factor, T.Feasible):
            count = _valued(factor.count, values)
            if not _positive_integer(count) or count < 2:
                refuse(factor, f"has the count {count!r}", "write an integer count of at least two")


def _point_in_declared_set(stage, value, declared):
    """True, False, or None for the membership of a number in a declared
    set, decided by the set algebra through the sets the stage defines."""
    definitions = {
        definition.identity.field: definition.equations[0]
        for definition in stage.definitions.values()
        if definition.kind == "set" and definition.equations
    }
    point = T.Interval(
        T.Range(left=T.Closed(), lower=T.Number(value), upper=T.Number(value), right=T.Closed())
    )
    return sets.within(point, declared, definitions)


def _positive_integer(value):
    return type(value) is int and value > 0


def _finite_real(value):
    return type(value) is int or type(value) is float and math.isfinite(value)
