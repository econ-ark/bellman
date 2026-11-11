"""The checks of the data a function representation reads, at binding and at
configuration, and the conditions a representation owes (AMD-MT-003 build
contract §§3, 4).

`representations.selected_source` selects, from the combined declarations of
a version, the data each representation reads; this module checks the
selection. `check_sources`, at binding, refuses a representation whose family
does not accept the data its place supplies, a grid where the family reads
the pairs of `!egm`, a grid beside an authored table that discretizes another
coordinate domain than the table's, and a local expression whose explicit
kernel the compiler cannot write; `check_table_supports`, at configuration,
compares the optional grid beside an authored table with the table, by
`representations.supports_equal`; and `representation_conditions` answers the
conditions each representation owes, which `stage.obligations()` lists.

A representation typed at a `!node` line, `<node>.method : !Linear`, and a
grid or a handler typed at the node's Evaluation, `<node>.evaluate.grid :
!Points(nodes=P)`, assign one representation to the function the node
computes, which its Evaluation holds (build contract §3, the canonical
resolution). The checks read the two entries as one assignment at the
Evaluation (`assigned_components`), so that such a grid is compared with the
node's table, and the check of a grid at binding reads the representation
typed at the node's line (`components.check_components`).

The checks read the places, the grids and the kernels of the stage, and the
places read the selection of `stage/representations.py`; this module stands
above `stage/places.py`, `stage/grids.py` and `stage/kernels.py`, and below
`stage/components.py` and `stage/stage_answers.py`, which call it.
"""

from __future__ import annotations

import dataclasses

from bellman.fold.wire_terms import term_nodes
from bellman.native.records import Components, Condition, refuse_at_entry
from bellman.refusals import ConstructionError
from bellman.stage.grains import construction_table
from bellman.stage.grids import place_coordinates
from bellman.stage.kernels import kernel
from bellman.stage.places import EVALUATE, components_by_place, places_by_address, typings
from bellman.stage.representations import (
    bound_family,
    data_site,
    declared_functions,
    evaluation_of_builder,
    evaluation_of_node,
    function_body,
    grid_support,
    line_record,
    supports_equal,
    table_support,
)
from bellman.syntax import terms as T
from bellman.syntax.source import to_source

__all__ = (
    "assigned_components",
    "check_sources",
    "check_table_supports",
    "representation_conditions",
)

# --- the assignments of the representations ---


def assigned_components(stage, place, held):
    """The components the checks read at the place `place` of `stage`, where
    `held` are the components typed there: at the Evaluation of a `!node`
    line where no method is typed, the function representation typed at the
    node's line, with the source it reads, joins the grid and the handler
    typed at the Evaluation, since the two entries assign one
    representation to the function the Evaluation holds (AMD-MT-003 build
    contract §3); `held` itself at every other place."""
    if held.method is not None or not evaluation_of_node(place):
        return held
    node = components_by_place(stage).get(place.boxes[0].address)
    if node is None or node.source is None:
        return held
    return dataclasses.replace(held, method=node.method, source=node.source)


def _represented(stage):
    """Each function representation of `stage`, one for each represented
    function, as `(Place, Components, address)` triples in the order of the
    inventory: the place the assignment is read at, the components assigned
    there and the address of the entry that types the method. The place is
    the one the typing entries at the address resolve to
    (`places.places_by_address`), the Evaluation of a `!node` line for
    `<node>.evaluate`; a representation typed at the node's line `<node>` is
    read at the node's Evaluation, with the grid and the handler typed there
    (`assigned_components`), so that the source is checked there."""
    by_place = components_by_place(stage)
    by_address = places_by_address(stage)
    found = []
    for address, place in by_address.items():
        held = by_place.get(address)
        if held is None or held.source is None:
            continue
        if place.kind == "node":
            place = by_address[f"{address}.{EVALUATE}"]
            held = assigned_components(stage, place, by_place.get(place.address, Components()))
        found.append((place, held, address))
    return tuple(found)


def _entry_records(stage):
    """The typing record of each component, by the place's address and the
    component's name."""
    return {(typing.place.address, typing.component): typing.record for typing in typings(stage)}


# --- the checks of the selected sources ---


def check_sources(stage):
    """The check of the data source of every function representation of
    `stage` at binding (build contract §3), each refusal positioned at the
    entry that types the representation, or at the `!explicit` entry of a
    generated closed form, and a refusal of a grid at the grid's entry: a
    family that does not accept the data its place supplies is refused
    under `representation-source`, an authored table at a family that
    accepts no table, the closing Evaluation of an `!egm` builder at a
    family that accepts neither pairs nor its own nodes, and a family that
    accepts only an expression at a place with no complete authored
    expression among them; a family that reads the pairs of an `!egm`
    builder refuses a representation grid under `grid-coordinate`; a local
    expression whose explicit kernel the compiler cannot write is refused
    under `representation-source`; and so is a grid beside an authored table
    that discretizes another coordinate domain than the table's
    (`_table_grid_fault`)."""
    records = _entry_records(stage)
    for place, held, address in _represented(stage):
        family = bound_family(stage, held.method.name)
        record = records.get((address, "method"))
        if record is None and held.generated_from is not None:
            record = records.get((held.generated_from.rsplit(".", 1)[0], "method"))
        site = data_site(stage, place)
        word = f"!{held.method.name}"
        if held.source not in family.sources:
            accepted = ", ".join(family.sources)
            if site == "table":
                reason = (
                    f"the place holds an authored table `evaluate(knots, values, x)`, and {word} "
                    f"accepts no table; its data sources are {accepted}"
                )
                write = f"Type a family that reads a table, such as !Linear, at `{address}`"
            elif site == "pairs":
                reason = (
                    f"the place is the closing Evaluation of the builder {place.block!r}, whose "
                    f"method !egm selects policy pairs, and {word} accepts neither those pairs "
                    f"nor its own nodes, from which the pairs could be sampled; its data "
                    f"sources are {accepted}"
                )
                write = f"Type a family that reads the pairs, such as !Linear, at `{address}`"
            elif "expression" in family.sources:
                reason = (
                    f"{word} reads a complete authored expression with an explicit kernel, and "
                    f"the place supplies none: the closing Evaluation of an !explicit builder, "
                    f"a line that defines one name by an expression, or a declared function "
                    f"supplies one, and a label without its expression does not; its data "
                    f"sources are {accepted}"
                )
                write = (
                    f"Type a family that samples the function on its own grid, such as "
                    f"!Linear, at `{address}`, or write the function's expression"
                )
            else:
                reason = (
                    f"the place supplies neither an authored table nor the pairs of an !egm "
                    f"builder, so a representation samples the function on its own grid, and "
                    f"{word} accepts no nodes of its own; its data sources are {accepted}"
                )
                write = (
                    f"Type a family that accepts its own nodes, such as !Linear, at `{address}`"
                )
            refuse_at_entry(stage, address, record, "representation-source", reason, write=write)
        if held.source == "pairs" and held.grid is not None:
            refuse_at_entry(
                stage,
                place.address,
                records.get((place.address, "grid"), record),
                "grid-coordinate",
                f"{word} at the closing Evaluation of the builder {place.block!r}, whose method "
                f"is !egm, reads the policy pairs the method selects, and the place writes the "
                f"grid {to_source(T.Grid(held.grid))}; a family that reads those pairs reads no "
                f"grid there, and the grid of !egm is the entry of its builder",
                write=f"Remove the grid entry of `{place.address}`",
            )
        if held.source == "table" and held.grid is not None:
            _check_table_coordinate(
                stage, place, held, records.get((place.address, "grid"), record)
            )
        if (
            held.source == "expression"
            and site == "expression"
            and not evaluation_of_builder(place)
        ):
            _check_local_kernel(stage, place, held, record, address)


def _check_table_coordinate(stage, place, held, record):
    """The refusal of a grid beside an authored table that discretizes
    another coordinate domain than the table's (`_table_grid_fault`)."""
    for box, call in _authored_calls(stage, place):
        fault = _table_grid_fault(stage, place, box, call, held.grid)
        if fault is not None:
            refuse_at_entry(
                stage,
                place.address,
                record,
                "representation-source",
                fault,
                write=f"Remove the grid entry of `{place.address}`",
            )


def _table_grid_fault(stage, place, box, call, grid):
    """The sentence that says why the grid `grid` beside the authored table
    `call` of the box `box` discretizes another coordinate domain than the
    table, or None where the two agree (build contract §3, case 1). The
    table's knots are points of its third argument. A `!Points` grid
    discretizes the coordinates of the place, in whose domain its points
    lie, and a `!Cartesian` grid those coordinates, a coordinate no factor
    names taking the default, and each control or shock a factor names
    (`_grid_coordinates`). The two agree where the third argument is a name,
    or a tuple of names, equal in order to the coordinates the grid
    discretizes; a table written at the same names in another order is
    refused, since its knots are points in that order. A grid of another
    kind has no exact support before numerical preparation, where it is
    compared."""
    if not isinstance(grid, (T.PointGrid, T.Cartesian)):
        return None
    point = call.args[2] if len(call.args) == 3 else None
    discretized = _grid_coordinates(stage, place, box, grid)
    if _evaluated_names(point) == discretized:
        return None
    evaluated = "no third argument" if point is None else f"`{to_source(point)}`"
    return (
        f"the authored table `{to_source(call)}` is evaluated at {evaluated}, and the grid "
        f"{to_source(T.Grid(grid))} discretizes ({', '.join(discretized)}); an optional grid "
        f"beside a table discretizes the coordinates at which the table is evaluated, written "
        f"as a name or as a tuple of names in the order of the grid's coordinates, so that the "
        f"grid's points and the table's knots lie in one domain"
    )


def _grid_coordinates(stage, place, box, grid):
    """The coordinates the grid `grid` at `place` discretizes, in their
    order: the coordinates of the place's box `box`, in their declared order
    (`grids.place_coordinates`), and for a `!Cartesian` grid each further
    control or shock a factor names, in the order of the factors."""
    discretized = tuple(place_coordinates(stage, box, place.block))
    if isinstance(grid, T.Cartesian):
        discretized = tuple(
            dict.fromkeys((*discretized, *(factor.coordinate for factor in grid.factors)))
        )
    return discretized


def _evaluated_names(point):
    """The names at which an authored table is evaluated, its third argument
    `point`: one name, or a tuple of names, in their written order; None for
    any other argument."""
    items = point.items if isinstance(point, T.Tuple) else (point,)
    if not all(isinstance(item, T.Sym) and isinstance(item.symbol, T.Constant) for item in items):
        return None
    return tuple(item.symbol.name for item in items)


def _check_local_kernel(stage, place, held, record, address):
    """The refusal of a local expression that the kernel compiler writes as
    no explicit function, positioned at the entry `record` that types the
    representation at `address`. At a line or a node, every row the line
    forms, other than the Evaluation of a node, has an explicit kernel, so
    that the representation reads the expression through its kernels; an
    expectation, a choice or a symbolic derivative inside it forms a row
    with none, and a label without an expression is insufficient. At a
    declared function, which the compiler writes as an inner function of a
    kernel that calls it, every call in its body, and in the body of each
    function it calls, names a function the stage defines in closed form
    (`_unwritten_call`)."""
    if place.kind == "definition":
        functions = declared_functions(stage)
        name = stage.definitions[place.boxes[0]].identity.field
        fault = _unwritten_call(functions, function_body(functions, name))
        if fault is None:
            return
        refuse_at_entry(
            stage,
            address,
            record,
            "representation-source",
            f"!{held.method.name} reads the expression of the declared function {name!r}, and "
            f"the kernel compiler writes no explicit function of it: {fault}",
            write=(
                f"Define each function the expression calls in closed form, `𝑓(x) := "
                f"expression`, or type a family that samples the function on its own grid, "
                f"such as !Linear, at `{address}`"
            ),
        )
    line = place.address if place.kind in ("statement", "node") else place.boxes[0].address
    rows = [
        row
        for row in construction_table(stage).by_builder(place.block)
        if line in row.statements and row.kind != "Evaluation"
    ]

    def explicit(row):
        try:
            return kernel(stage, str(row.identity)).python is not None
        except ConstructionError:
            return False

    if rows and all(explicit(row) for row in rows):
        return
    refuse_at_entry(
        stage,
        address,
        record,
        "representation-source",
        f"!{held.method.name} reads the expression of the line {line!r}, and the kernel "
        f"compiler writes no explicit function of it: an expectation, a choice or a symbolic "
        f"derivative inside the expression has no explicit kernel",
        write=f"Type a family that samples the function on its own grid, such as !Linear, at "
        f"`{address}`",
    )


def _unwritten_call(functions, body):
    """The sentence that names the first call, in the expression `body` or in
    the body of a function it calls, that the kernel compiler writes into no
    explicit function; None where it writes every call. The compiler writes
    a call only of a function the stage defines in closed form, through that
    function's body (`representations.function_body`), and refuses under
    `kernel-form` a call of a function no definition declares, such as
    `log(x)`, and of a function defined in another form, such as an alias
    of a derivative."""
    for node in term_nodes(body):
        if not isinstance(node, T.Call):
            continue
        called = function_body(functions, node.fun)
        if called is None:
            reason = (
                "names a function no definition of the stage declares"
                if node.fun not in functions
                else f"names {node.fun}, whose definition is no expression in closed form"
            )
            return f"the call `{to_source(node)}` {reason}"
        fault = _unwritten_call(functions, called)
        if fault is not None:
            return fault
    return None


# --- the authored table and its optional grid ---


def _authored_calls(stage, place):
    """The authored `evaluate(knots, values, x)` calls of the lines the
    place's boxes name, each as a pair of its box and the call, in order."""
    found = []
    for box in place.boxes:
        record = line_record(stage, getattr(box, "address", None) or str(box))
        if record is None or not record.equations:
            continue
        found.extend(
            (box, node)
            for node in term_nodes(record.equations[0])
            if isinstance(node, T.Call) and node.fun == EVALUATE
        )
    return tuple(found)


def _concrete_supports(stage, place, box, call, grid, values):
    """The knots of the authored table `call` of the box `box` and the points
    of its grid `grid` as two tuples of points, where the grid discretizes
    the table's coordinate domain (`_table_grid_fault`) and both supports are
    given exactly at the bound `values`; None otherwise, the comparison then
    remaining the obligation `table-grid-support`."""
    if _table_grid_fault(stage, place, box, call, grid) is not None:
        return None
    knots = table_support(stage, call, values)
    points = grid_support(grid, values, _grid_coordinates(stage, place, box, grid))
    return None if knots is None or points is None else (knots, points)


def check_table_supports(stage, values):
    """The check, at configuration, of the optional grid beside each authored
    table at the bound settings `values` and the calibration of `stage`
    (build contract §§3, 4): where the grid discretizes the table's
    coordinate domain and the table's knots and the grid's points are both
    given exactly (`_concrete_supports`), the two finite supports are equal,
    compared exactly by `supports_equal`, with no sorting, resampling or
    tolerance; otherwise the comparison remains the obligation
    `table-grid-support`, checked before numerical preparation. A
    difference, and a point that is no finite real, is refused under
    `representation-source`. The grid of a table that is a node's function
    may stand at the node's Evaluation beside a representation typed at the
    node's line (`assigned_components`)."""
    bound = {**(stage.bindings.calibration or {}), **values}
    records = _entry_records(stage)
    for place, held, _ in _represented(stage):
        if held.source != "table" or held.grid is None:
            continue
        for box, call in _authored_calls(stage, place):
            supports = _concrete_supports(stage, place, box, call, held.grid, bound)
            if supports is None:
                continue
            knots, points = supports
            record = records.get((place.address, "grid"))
            try:
                equal = supports_equal(knots, points)
            except ValueError as error:
                refuse_at_entry(
                    stage,
                    place.address,
                    record,
                    "representation-source",
                    f"the authored table `{to_source(call)}` and its grid "
                    f"{to_source(T.Grid(held.grid))} are compared exactly at configuration, "
                    f"and {error}",
                    write="Write finite real points",
                )
            if not equal:
                refuse_at_entry(
                    stage,
                    place.address,
                    record,
                    "representation-source",
                    f"the grid {to_source(T.Grid(held.grid))} has the finite support "
                    f"{_printed(points)}, and the authored table `{to_source(call)}` has the "
                    f"knots {_printed(knots)}; an optional grid beside a table has exactly the "
                    f"table's finite support, compared with no tolerance, no sorting and no "
                    f"resampling",
                    write="Write the grid's points as the table's knots, or remove the grid entry",
                )


def _printed(points):
    """A tuple of points as a refusal prints it, the first eight and the
    count of the rest."""
    shown = ", ".join(repr(point) for point in points[:8])
    more = f", and {len(points) - 8} more" if len(points) > 8 else ""
    return f"({shown}{more})"


# --- the conditions of the representations ---

# the sentence of each condition a representation owes, which
# `stage.obligations()` lists with its status
_TABLE_GRID_SUPPORT = (
    "The optional grid beside the authored table has exactly the table's finite support, "
    "compared with no tolerance before an evaluator is constructed."
)
_PAIR_RECONSTRUCTION = (
    "The policy is reconstructed by piecewise linear interpolation of the feasible, "
    "branch-selected, ordered pairs the endogenous grid method selects, sampled on the "
    "family's grid before the family is prepared."
)
_EVALUATION_DOMAIN = {
    "expression": (
        "The authored expression is defined, with its stated conditions, at every point of "
        "the represented function's domain at which the function is evaluated."
    ),
    "nodes": (
        "The representation is evaluated inside the interval its nodes span, or outside it "
        "through an identified extension; the node interval does not replace the domain of the "
        "represented function."
    ),
}


def representation_conditions(stage):
    """The conditions the function representations of `stage` owe, each a
    `Condition` naming the box of the place the representation is read at,
    the Evaluation of a `!node` line for a representation typed at the
    node's line: `evaluation-domain` for every representation, that it is
    evaluated only where its data support the represented function (build
    contract §§3, 4); `pair-reconstruction` for a family that reads its own
    nodes at the closing Evaluation of an `!egm` builder; and
    `table-grid-support` for the grid beside an authored table, established
    where configuration compared the two supports exactly, the grid
    discretizing the table's coordinate domain, and required where a support
    is given only at preparation."""
    found = []
    values = {**(stage.bindings.calibration or {}), **(stage.bindings.settings or {})}
    for place, held, _ in _represented(stage):
        entries = (place.boxes[0],)
        kind = "expression" if held.source == "expression" else "nodes"
        found.append(
            Condition(
                "evaluation-domain",
                entries,
                status="required",
                explanation=_EVALUATION_DOMAIN[kind],
            )
        )
        if held.source == "own nodes" and data_site(stage, place) == "pairs":
            found.append(
                Condition(
                    "pair-reconstruction",
                    entries,
                    status="required",
                    explanation=_PAIR_RECONSTRUCTION,
                )
            )
        if held.source == "table" and held.grid is not None:
            supports = [
                _concrete_supports(stage, place, box, call, held.grid, values)
                for box, call in _authored_calls(stage, place)
            ]
            decided = False
            if supports and all(pair is not None for pair in supports):
                try:
                    decided = all(supports_equal(*pair) for pair in supports)
                except ValueError:
                    decided = False
            found.append(
                Condition(
                    "table-grid-support",
                    entries,
                    status="established" if decided else "required",
                    evidence=(
                        ("the table's knots and the grid's points compared exactly",)
                        if decided
                        else ()
                    ),
                    explanation=_TABLE_GRID_SUPPORT,
                )
            )
    return tuple(found)
