"""The components typed at the places of a stage, checked against the rows
of the catalogue (specification 0.7 §5, D1, D5; the grid note §3).

At binding, once the typing entries of a stage file and its additions are
resolved to their places (`places.typings`), `check_components` reads the
`Components` of each place against the row of its method word: a keyword
the row requires is written (`method-admission`) and no argument of the
word is written as a number (`method-setting-declared`); every factor of a grid
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
strictly increasing (`grid-bounds`). The records of the grid constructors,
the checks of a grid that read them beside these, and the domain a grid
discretizes (`grid_domain`) stand in `stage/grids.py`, which the two grid
checks here call (`check_grid_at_binding`, `check_grid_at_configuration`).

The checks of the data a function representation reads stand in
`stage/representation_checks.py`, which `check_components` and
`check_bound_values` call; a grid typed at the Evaluation of a `!node` line
is checked against the representation typed at the node's line, the two
entries being one assignment (`representation_checks.assigned_components`).
At binding, `check_components` also compiles the kernel of each output of a
builder whose method is `!explicit` (`explicit-solution`), the part of the
explicit check that reads the kernel compiler, `stage/kernels.py`, which
the construction's own check (`explicit.check_explicit`) stands below.
"""

from __future__ import annotations

import dataclasses
import math

from bellman.fold.block_lines import blocks_of, header_of, setting_sets
from bellman.fold.stage_names import StageNames
from bellman.fold.wire_terms import term_nodes
from bellman.native.identity import Identity
from bellman.native.records import grid_factors, refuse_at_entry, setting_names, typing_text
from bellman.refusals import ConstructionError
from bellman.stage.grains import construction_table
from bellman.stage.grids import (
    SETTING,
    SPACING,
    calibration_values,
    check_grid_at_binding,
    check_grid_at_configuration,
    expectation_names,
    factor_form_of,
    grid_domain,
    parameters_read_at,
    place_row,
    point_in_declared_set,
)
from bellman.stage.kernels import compile_kernel
from bellman.stage.method_rows import KEYWORD_DOMAINS
from bellman.stage.places import components_by_place, typings
from bellman.stage.representation_checks import (
    assigned_components,
    check_sources,
    check_table_supports,
)
from bellman.stage.representations import EXPLICIT, bound_row
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import WRITTEN_MARK

# --- the components at binding ---


def check_components(stage):
    """The check of the components typed at every place of `stage` against
    the rows of the catalogue, made where the stage is constructed and
    where an addition is read into it: first the compiled kernel of each
    output of every builder whose method is `!explicit`
    (`_check_explicit_kernels`); then the required keywords, and the
    coordinates and the names of each grid, a grid at the Evaluation of a
    `!node` line read with the representation typed at the node's line
    (`representation_checks.assigned_components`); then the data source of
    every function representation (`representation_checks.check_sources`).
    Each refusal stands at the position of the entry, with the place as its
    address. A row is the one the version reads
    (`representations.bound_row`)."""
    _check_explicit_kernels(stage)
    for place, held, records in _typed_places(stage):
        row = bound_row(stage, held.method.name) if held.method is not None else None
        # a generated method, the closed form at an `!explicit` builder's
        # Evaluation, has no entry and writes no keyword
        if row is not None and "method" in records:
            _check_keywords(stage, place, held, row, records["method"])
        if held.grid is not None:
            assigned = assigned_components(stage, place, held)
            assigned_row = (
                bound_row(stage, assigned.method.name) if assigned.method is not None else None
            )
            _check_grid(stage, place, assigned, assigned_row, records["grid"])
    check_sources(stage)


def _check_explicit_kernels(stage):
    """The check, where the version is bound, that each output of every
    builder of `stage` whose method is `!explicit` has an executable
    compiled kernel (AMD-MT-003 build contract §5): the rows of the
    operative builder that compute the output from the block's lines are
    compiled (`kernels.compile_kernel`), and an output that no row computes,
    or whose row the compiler refuses, is refused under `explicit-solution`
    at the position of the entry that types the method. The construction
    has refused the lines an explicit solution excludes before
    (`explicit.check_explicit`)."""
    for typing in typings(stage):
        if typing.component != "method" or typing.place.kind != "builder":
            continue
        if typing.value.name != EXPLICIT:
            continue
        block, record = typing.place.address, typing.record
        box = next(held for held in blocks_of(stage) if held.name == block)
        ctx = StageNames(stage)
        outputs = tuple(sort.identity for sort in header_of(box).outputs)
        wires = {ctx.function_wire(identity): identity for identity in outputs}
        rows = construction_table(stage).by_builder(block)
        for wire, identity in wires.items():
            found = [
                row
                for row in rows
                if row.kind in ("Aggregation", "Pullback")
                and any(_carries(output, wire) for output in row.outputs)
            ]
            spelled = identity.field + WRITTEN_MARK.get(identity.perch, "")
            if not found:
                refuse_at_entry(
                    stage,
                    block,
                    record,
                    "explicit-solution",
                    f"no row of the operative builder {block!r} computes its output {spelled} "
                    "from the block's lines, so the output has no kernel to compile",
                    write=f"Write the line `{spelled} = <expression>` in the block {block!r}",
                    kind="builder",
                )
            for row in found:
                try:
                    compile_kernel(stage, str(row.identity))
                except ConstructionError as error:
                    refuse_at_entry(
                        stage,
                        block,
                        record,
                        "explicit-solution",
                        f"the output {spelled} has no executable compiled kernel: the row "
                        f"{row.identity} is refused under {error.rule}, "
                        f"{error.message.split('; ')[0]}",
                        write="Write the output as an expression the kernel compiler writes",
                        kind="builder",
                    )


def _carries(output, wire):
    """Whether a row's output is the function wire `wire`, or the result a
    row names for it."""
    if output == wire:
        return True
    return (
        isinstance(output, Identity)
        and getattr(output, "field", None) == wire.field
        and getattr(output, "mark", None) == "result"
    )


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
    written `n_<shock>`. Every bare name in an argument is a declared setting,
    and an argument written as a number is refused at every depth of the
    word's tuples and nested words (`method-setting-declared`; AAS,
    14 November 2026)."""
    declared = setting_sets(stage)
    for argument in _word_arguments(held.method):
        if isinstance(argument, T.Literal):
            refuse_at_entry(
                stage,
                place.address,
                record,
                "method-setting-declared",
                f"the entry `{typing_text(record)}` writes the number {to_source(argument)} "
                "among the arguments of its method; a number that a method reads is a "
                "setting declared in the methods file and valued in the settings file",
                write="Declare a setting with its set in the methods file, write the "
                "setting's name in place of the number, and give the number in the "
                "settings file",
            )
        if isinstance(argument, T.Name) and argument.name not in declared:
            refuse_at_entry(
                stage,
                place.address,
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
        refuse_at_entry(
            stage,
            place.address,
            record,
            "method-admission",
            f"the entry `{typing_text(record)}` names `!{held.method.name}` without the "
            f"keyword{'' if len(missing) == 1 else 's'} {', '.join(missing)}, which its row of "
            f"the catalogue requires; write every required keyword using the names shown by "
            f"method_types of bellman.stage",
        )


def _check_grid(stage, place, held, row, record):
    """The rules of the grid note §3 that bind before configuration: a grid
    at a word that reads none, and a factor that names no coordinate,
    control or shock of the place, under `grid-coordinate`; a number or an
    undeclared name among the factors under `grid-setting-declared`; and the
    checks the records of the grid constructors state, their sites, their
    required arguments, the base and the fibre of `!Fibred`, the predicate
    words and the declared points of `!Points` (`grids.check_grid_at_binding`).
    An entry that names no method word binds its grid as the discretized
    domain of the place, which the handler reads."""
    if row is not None and row.grid is None:
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-coordinate",
            f"!{held.method.name} reads no grid, and the place writes the grid "
            f"{to_source(held.grid)}; a grid is read by a representation, by a solution "
            f"method on the states of a perch and by a handler; remove the grid entry",
            write=f"Remove the grid entry of `{place.address}`",
        )
    check_grid_at_binding(stage, place, held, row, record)
    for box in place.boxes:
        _check_grid_coordinates(
            stage, place, record, held.grid, box, grid_domain(stage, box, place.block, row)
        )
    _check_grid_names(stage, place, record, held.grid)


def _check_grid_coordinates(stage, place, record, grid, box, domain):
    """The rule `grid-coordinate` at one box of the place: every factor of
    the grid, the factors of each Cartesian term it holds (`grid_factors`),
    names a coordinate of the function the box holds, a control of the
    stage for a feasible factor, or a shock for a quadrature factor. A
    grid may name a factor for some coordinates of the function and none for
    the others: a coordinate no factor names takes the default, as every
    coordinate does where the place writes no grid entry (decision S7-C17).
    The entry is recorded as written, with the named factors alone."""
    coordinates = ", ".join(domain.states) or "none"
    for factor in grid_factors(grid):
        name = factor.coordinate
        if isinstance(factor, T.Feasible):
            if name not in domain.controls:
                refuse_at_entry(
                    stage,
                    place.address,
                    record,
                    "grid-coordinate",
                    f"the factor {to_source(factor)} of the grid names {name!r} as a control, "
                    f"and the controls of the stage are "
                    f"{', '.join(domain.controls) or 'none'}; a feasible factor is written for "
                    f"a control, its feasible set with a count",
                )
        elif isinstance(factor, T.Listed) and factor.nodes in domain.expectations:
            if name not in domain.shocks:
                refuse_at_entry(
                    stage,
                    place.address,
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
            refuse_at_entry(
                stage,
                place.address,
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
        refuse_at_entry(
            stage,
            place.address,
            record,
            "grid-setting-declared",
            f"the factor {to_source(factor)} of the grid {reason}; {write}",
        )

    for factor in grid_factors(grid):
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
    """The arguments of a factor that name a setting or write a number, read
    from the record of its form (`grids.factor_form_of`): each part of the
    kind `setting`, the bounds and the count of a spaced factor and the count
    of a feasible factor, with the keyword arguments of a spacing word."""
    found = []
    for name, option in factor_form_of(factor).arguments.items():
        value = getattr(factor, name)
        if option.kind == SETTING:
            found.append(value)
        elif option.kind == SPACING and value is not None:
            found.extend(_word_arguments(value))
    return tuple(found)


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
    row = place_row(stage, box)
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
    §3); then the optional grid beside each authored table, whose finite
    support equals the table's where both are given exactly
    (`representation_checks.check_table_supports`). A set the stage defines
    and an expectation operator, which a listed factor may name, need no
    value. A row is the one the version reads (`representations.bound_row`),
    so that a family registered or removed after binding leaves the check as
    the version was bound."""
    expectations = expectation_names(stage)
    defined = {
        d.identity.field
        for d in stage.definitions.values()
        if d.kind in ("set", "correspondence")
    }
    for place, held, _ in _typed_places(stage):
        row = bound_row(stage, held.method.name) if held.method is not None else None
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
    check_table_supports(stage, values)


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


# what to write for a value outside each domain of a keyword's value, one
# entry for each kind of `method_rows.KEYWORD_DOMAINS`
_WRITE = {
    "positive integer": "write an integer greater than zero",
    "positive real": "write a finite value greater than zero",
    "seed": "write a nonnegative integer",
}


def _check_domain(stage, place, held, name, keyword, value):
    """The refusal of a keyword's value outside the domain its row names,
    under `method-option-value`."""
    if keyword.kind not in KEYWORD_DOMAINS:
        raise RuntimeError(f"unknown keyword domain {keyword.kind!r}")
    reason = KEYWORD_DOMAINS[keyword.kind](value)
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
    two. A factor on a control or a shock has no declared set to check. A
    declared set that reads a parameter, `Xa := [a_Art, inf)`, is read at
    the calibration that is bound, as the declared set of a setting is
    (`grids.point_in_declared_set`); before a calibration is bound nothing
    decides such a membership, and the point is refused. The configured
    points of `!Points` and the requirements the bound values decide are
    then checked from the records of the grid constructors
    (`grids.check_grid_at_configuration`)."""
    calibration = calibration_values(stage)

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
        member = point_in_declared_set(stage, point, declared, calibration)
        if member is not True:
            word = "lies outside" if member is False else "is not decidably inside"
            refuse(
                factor,
                f"writes the point {point!r}, which {word} the declared set "
                f"{to_source(declared)} of {factor.coordinate}"
                f"{parameters_read_at(stage, declared, calibration)}",
                "write points inside the declared set",
            )

    for factor in grid_factors(held.grid):
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
    check_grid_at_configuration(stage, place, held, values, domain)


def _positive_integer(value):
    return type(value) is int and value > 0


def _finite_real(value):
    return type(value) is int or type(value) is float and math.isfinite(value)
