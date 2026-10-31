"""The joins of a period and of a trellis, and the orders the joins
determine, each projected from the one selection of the connections
(`bellman.factory.connections`).

Field dependencies determine economic order; the list order of a period
template does not. A continuation state field of one stage joins an arrival
state field of another stage of the period where the selection pairs the
two: as an authored connector maps them, or by the unique admissible
inference of equal names no authored connector claims. A continuation
state field no join within the period reads is an output of the period,
joined to the next period by the inter-period mapping. The forward order,
the backward order and the stages computable together are functions of the
joins; nothing is stored on the dictionary. `unjoined_fields` answers the
state fields of a trellis that no join reaches, and the entries that write
the joins reaching each other arrival state field.

Each function takes the `Selection` of the trellis it reads from where the
caller holds one (`connections.trellis_selection`), so that one reading of
a trellis selects once and every answer is taken from that result; given
none, it selects the periods it is given, under the calibration their
occurrences hold. A malformed connector is refused. Duplicate claims and
authored cycles remain in the selection and its connection report.
`forward_order`, `backward_order` and `computable_together` refuse those
conflicts because they require a valid dependency order. An unresolved
endpoint, incompatible pair or uncertified route also remains on the draft.
"""

from __future__ import annotations

from bellman.factory.connections import (
    AUTHORED,
    CERTIFIED,
    REFUSING_RULES,
    _unjoined_from_selection,
    held_calibrations,
    select_connections,
    trellis_selection,
)
from bellman.native.versions import StageVersion
from bellman.refusals import Diagnostic, FactoryError
from bellman.stage.grains import graph_of, graph_refusal
from bellman.native.identity import Identity
from bellman.stage.stage_answers import (
    derivative_reads,
    entry_perch,
    fields,
    passed_through,
    value_carries_derivative,
)
from bellman.syntax.vocabulary import CONTINUATION, WRITTEN_MARK

__all__ = [
    "backward_order",
    "checked_selection",
    "computable_together",
    "forward_order",
    "inter_period_joins",
    "derivative_missing",
    "period_joins",
    "unjoined_fields",
]


# --- the selection a public reading projects from ---


def checked_selection(
    periods, inter_connectors, first=0, file=None, selection=None, *, rules=REFUSING_RULES
):
    """The `Selection` a public reading of `periods`, numbered from `first`,
    and the mappings `inter_connectors` between them projects its answers
    from: `selection` where the caller holds one, else
    `connections.select_connections` of the periods under the calibration
    each occurrence holds (`held_calibrations`). A period holding a record
    in place of a stage occurrence is refused under `record-shape`, since a
    record has no fields. A diagnostic whose rule is in `rules` is refused;
    the default applies to a request for a valid dependency order."""
    if selection is None:
        for h, period in enumerate(periods, first):
            _records_refused(period["stages"], f"periods[{h}]", file)
        selection = select_connections(
            periods, inter_connectors, held_calibrations(periods, first), first=first
        )
    refused(selection, file, rules=rules)
    return selection


def refused(selection, file=None, *, rules=REFUSING_RULES):
    """Raises the refusal of the first diagnostic of `selection` whose rule
    is one of `REFUSING_RULES`, naming `file`, the trellis file, where one
    is given: `connector-names-no-field` for an entry of no admitted shape
    (`connector-shape`) and for a continuation field two entries map
    (`use-claimed-twice`); `period-join-cycle` for a cycle among the pairs
    of a period (`authored-cycle`, `selected-cycle`), each pair on it
    named, and for a pair from a stage to itself. Returns None where none
    stands. `rules` can restrict a projection to malformed input alone."""
    for diagnostic in selection.diagnostics:
        if diagnostic.rule not in rules:
            continue
        if diagnostic.rule == "connector-shape":
            (entry,) = diagnostic.candidates
            raise FactoryError(
                diagnostic.message,
                rule="connector-names-no-field",
                file=file,
                address=diagnostic.address,
                written=repr(entry)[:80],
                write="{<continuation field>: <arrival field>}, or within a period "
                "{from: <stage key>, to: <stage key>, fields: {<continuation field>: "
                "<arrival field>}}",
            )
        if diagnostic.rule == "use-claimed-twice":
            (pair,) = diagnostic.candidates
            raise FactoryError(
                diagnostic.message,
                rule="connector-names-no-field",
                file=file,
                address=diagnostic.address,
                written=f"{pair.writing.field}: {pair.reading.field}",
                write="the pairs of both under one entry, or no second entry for "
                f"{pair.writing.field!r}",
            )
        pairs = diagnostic.candidates
        if len(pairs) == 1 and pairs[0].writing.key == pairs[0].reading.key:
            (pair,) = pairs
            raise FactoryError(
                diagnostic.message,
                rule="period-join-cycle",
                file=file,
                address=diagnostic.address,
                written=f"{pair.writing.field}: {pair.reading.field}",
                write=f"a connector from {pair.writing.key}'s {pair.writing.field!r} to an "
                "arrival field of another stage",
            )
        named = "; ".join(
            f"{pair.writing.key} continues to {pair.writing.field!r} and {pair.reading.key} "
            f"arrives at {pair.reading.field!r}"
            for pair in pairs
        )
        h = pairs[0].writing.h if pairs else diagnostic.address
        raise FactoryError(
            f"the joins of the period form a cycle: {named}; the stages of a period are ordered "
            "by their field dependencies, so no stage may take a field it produces through the "
            "others",
            rule="period-join-cycle",
            file=file,
            address=f"periods[{h}]" if pairs else diagnostic.address,
            written=named or diagnostic.message,
            write="remove or redirect an authored connector so that the stage dependencies "
            "have no cycle; qualify an endpoint with its stage key where its bare name "
            "is ambiguous",
        )
    return None


def _index(address, default):
    """The integer written between the brackets of an address, `periods[2]`
    or `inter_connectors[0]`; `default` where none is written."""
    number = address.partition("[")[2].partition("]")[0]
    return int(number) if number.isdigit() else default


def _records_refused(stages, address, file=None):
    """Refuses under `record-shape` a key of `stages` holding a record and
    not a stage occurrence, since a record has no fields."""
    for key, stage in stages.items():
        if not isinstance(stage, StageVersion):
            raise FactoryError(
                f"{address}.stages[{key!r}] holds a {type(stage).__name__}, not an "
                "ElaboratedStage; the joins of a period are "
                "read from the fields of elaborated stages",
                rule="record-shape",
                file=file,
                address=f"{address}.stages[{key!r}]",
                written=type(stage).__name__,
                write="elaborate_trellis(syntactic) before the joins are read",
            )


def _state_fields(stages, perch, address, file=None):
    """`[(key, name)]` of the state fields at `perch` of every stage of a
    period, in key order. A record in place of a stage has no fields."""
    _records_refused(stages, address, file)
    return [
        (key, identity.field)
        for key, stage in stages.items()
        for identity, sort in fields(stage).items()
        if sort.perch == perch and sort.role == "state"
    ]


def _join(pair):
    """The join a selected pair is answered as, `{"from": (key, field),
    "to": (key, field)}`."""
    return {
        "from": (pair.writing.key, pair.writing.field),
        "to": (pair.reading.key, pair.reading.field),
    }


# --- the orders the joins determine ---


def backward_order(period, address="periods[?]", file=None, selection=None):
    """The keys in the order the backward operators are applied: the reverse
    of the forward order."""
    return list(reversed(forward_order(period, address, file, selection)))


def forward_order(period, address="periods[?]", file=None, selection=None):
    """The keys of the period's stages in dependency order: a stage after
    every stage whose continuation fields it takes; the list order of the
    period carries no meaning."""
    return [
        key for layer in computable_together(period, address, file, selection) for key in layer
    ]


def computable_together(period, address="periods[?]", file=None, selection=None):
    """The keys of the period's stages in dependency layers. Each layer has
    the stages whose taken fields are all produced by
    earlier layers, listed by key, so that the list order of the period
    determines no order. The joins are those `period_joins` answers; a
    cycle among them is refused under `period-join-cycle`, the pairs on it
    named."""
    h = _index(address, 0)
    selected = checked_selection([period], [], h, file, selection)
    joins = period_joins(period, address, file, selected)["joins"]
    remaining = {key: sum(join["to"][0] == key for join in joins) for key in period["stages"]}
    layers, placed = [], set()
    while len(placed) < len(remaining):
        layer = sorted(key for key, count in remaining.items() if count == 0 and key not in placed)
        if not layer:
            left = [key for key in remaining if key not in placed]
            raise FactoryError(
                f"the joins of the period form a cycle among {', '.join(left)}; the stages of a "
                "period are ordered by their field dependencies, so no stage may take a field "
                "it produces through the others",
                rule="period-join-cycle",
                file=file,
                address=address,
                written=", ".join(left),
                write="distinct names for the field a stage continues to and the field the "
                "other arrives at, or a connector that maps them",
            )
        for key in layer:
            placed.add(key)
            for join in joins:
                if join["from"][0] == key:
                    remaining[join["to"][0]] -= 1
        layers.append(layer)
    return layers


# --- the joins within a period ---


def period_joins(period, address="periods[?]", file=None, selection=None):
    """The joins of one period, `{"joins": [{"from": (key, field), "to": (key,
    field)}], "outputs": [(key, field)]}`, both lists sorted: one join per
    pair the selection holds between two stages of the period, a
    continuation state field of one stage and an arrival state field of
    another, authored by a connector of the period or inferred where the
    two names are equal and the pair is the unique admissible one; the
    outputs are the continuation state fields no
    join within the period reads, those that leave it. `address` is the
    period's address, `periods[h]`, whose index numbers the pairs; with
    `selection`, the selection of the trellis the period stands in, the
    joins are read from it, else the period alone is selected, under the
    calibration its occurrences hold. A malformed entry or a period holding
    records is refused. A duplicate claim or cycle remains in the selection
    and is refused by an operation that requires an order. An unresolved
    endpoint makes no join; an incompatible selected pair remains a join
    with its diagnostic and uncertified route."""
    h = _index(address, 0)
    selected = checked_selection([period], [], h, file, selection, rules=("connector-shape",))
    joins = [
        _join(pair)
        for pair in selected.pairs
        if pair.writing.h == h and pair.reading.h == h and pair.writing.key != pair.reading.key
    ]
    read = {join["from"] for join in joins}
    outputs = sorted(
        {
            (use.key, use.field)
            for use in selected.uses
            if use.h == h and use.perch == "cntn" and (use.key, use.field) not in read
        }
    )
    return {
        "joins": sorted(joins, key=lambda join: (join["from"], join["to"])),
        "outputs": outputs,
    }


# --- the joins an inter-period mapping makes ---


def inter_period_joins(
    mapping,
    later,
    earlier,
    address="inter_connectors[?]",
    file=None,
    *,
    later_address="periods[?]",
    selection=None,
):
    """The joins an inter-period mapping makes, `[{"from": (key, field), "to":
    (key, field)}]`, in the mapping's order: each key a continuation state
    field that leaves `later`, the period appended later and earlier in
    time, each value an arrival state field of `earlier`, the period
    appended before it, which it joins; a key may name the stage before the
    field, `cons.a`, where the bare name is shared. `address` is the
    mapping's, `inter_connectors[h]`, joining `periods[h + 1]`, which
    `later_address` names, to `periods[h]`; with `selection`, the selection
    of the trellis, the joins are read from it, else the two periods and
    the mapping are selected alone. A connector entry or its keyed `fields`
    entry must be a mapping. A source field claimed twice, or
    a key or value naming no field or several, remains in the selection's
    diagnostics; only the first resolved claim makes a join."""
    h = _index(address, max(_index(later_address, 1) - 1, 0))
    if selection is None:
        selection = checked_selection(
            [earlier, later], [mapping], h, file, rules=("connector-shape",)
        )
    else:
        refused(selection, file, rules=("connector-shape",))
    return _between(selection, h)


def _between(selection, h):
    """The joins the authored pairs of `inter_connectors[h]` make, in the
    mapping's order."""
    at = f"inter_connectors[{h}]"
    return [
        _join(pair) for pair in selection.pairs if pair.origin == AUTHORED and pair.address == at
    ]


# --- the state fields no join reaches ---


def unjoined_fields(trellis, selection=None):
    """The state fields of an elaborated trellis that no join reaches,
    `{"writing": [(h, key, field)], "reading": [(h, key, field)], "sources":
    {(h, key, field): (address, …)}}`, the two lists sorted. A continuation
    state field of `periods[h]` is
    writing and unjoined where no pair of the selection, within its period
    or of `inter_connectors[h - 1]`, reads it; an arrival state field of
    `periods[h]` is reading and unjoined where no pair, within its period
    or of `inter_connectors[h]`, reaches it. The pairs are those of the
    trellis's selection, `selection` where the caller holds it, so that the
    terminal period's continuation state and the earliest period's arrival
    state, the two ends of the trellis, are among the fields answered.

    `sources` holds each arrival state field that pairs reach, an arrival
    field taking several sources (docs/Bellman-Sym/07-trellis.md §2), with
    the address of the entry that writes each pair reaching it, one per
    pair, those within its period first: None for an inferred pair, which
    no entry writes, `periods[h].connectors[n]` for the connector of the
    period's list that writes it, and `inter_connectors[h]` for the
    mapping that joins `periods[h + 1]` to it (unit J's decisions J-D41 and
    J-D42)."""
    periods = trellis["periods"]
    selected = checked_selection(
        periods, trellis["inter_connectors"], 0, None, selection,
        rules=("connector-shape",),
    )
    if selection is not None:
        for h, period in enumerate(periods):
            _records_refused(period["stages"], f"periods[{h}]")
    return _unjoined_from_selection(selected)


# --- the derivatives a trellis's blocks read that no route meets ---


def derivative_missing(trellis, selection=None):
    """The derivative readings of an elaborated or specified trellis that no
    route meets (AMD-MB-001 §5.3, D3, D5 and D6), read along the route
    certification of its selection: one `Diagnostic` under
    `derivative-missing` for each derivative term a block of a source
    occurrence reads of its continuation value, `D_{a}V[>]`
    (`stage_answers.derivative_reads`), on each route from that occurrence,
    where the requirement comes to rest at a value that carries no
    derivative (`_unmet_along`). The requirement is met where the
    destination's exported value carries the derivative in the coordinates
    the route's pairs send the term's coordinates to, by a stated line or by
    a representation whose row of the method table evaluates that order
    (`stage_answers.value_carries_derivative`); where the destination passes
    the value through instead, by lines that are identities, expectations or
    scalings of the value before it under an identity law between its
    perches (`stage_answers.passed_through`, D3), the requirement moves to
    that value and, from the destination's continuation value, along the next
    route of the selection, until a stated or represented derivative meets it
    or an occurrence whose value carries none is found, which is the one
    reported; a route that pairs no value with the one read, or sends a
    coordinate nowhere, is reported at its destination; a requirement that
    reaches the trellis's end falls to the terminal data (§5.3) and is not
    reported. The diagnostic's address is the reported occurrence,
    `periods[0].stages['port']`; its candidates are the identity of the
    value there and its coordinates; its sentence names that stage, the
    reading stage's block and its term as the amendment spells it, and the
    stages passed through. Information and no refusal: the join check
    compares values alone, and the block that reads the derivative declares
    the reading and nothing else. The connections are selected once for the
    answer (`connections.trellis_selection`), or taken from `selection`
    where the caller holds it for this trellis."""
    if selection is None:
        selection = trellis_selection(trellis)
    periods = trellis["periods"]
    found = []
    for route in selection.routes:
        source = periods[route.source[0]]["stages"][route.source[1]]
        for read in derivative_reads(source):
            if read.value.perch != CONTINUATION or any(
                name not in route.source_fields for name in read.coordinates
            ):
                continue
            required = str(
                Identity("function", stage=source.name, perch=CONTINUATION, field=read.value.field)
            )
            unmet = _unmet_along(selection, periods, route, required, read.coordinates)
            if unmet is None:
                continue
            position, value, coordinates, passed = unmet
            stage = periods[position[0]]["stages"][position[1]]
            at_source = f"periods[{route.source[0]}].{route.source[1]}"
            at = f"periods[{position[0]}].{position[1]}"
            named = (
                f"{value.field}{WRITTEN_MARK.get(value.perch, '')}"
                if value is not None
                else f"V{WRITTEN_MARK.get(entry_perch(stage), '')}"
            )
            through = (
                " through the pass-through of " + ", ".join(passed) + ","
                if passed
                else ""
            )
            found.append(
                Diagnostic(
                    "derivative-missing",
                    f"periods[{position[0]}].stages[{position[1]!r}]",
                    f"stage {stage.name!r} at {at} supplies,{through} the continuation of "
                    f"{at_source}, whose block {read.builder!r} reads `{read.spelling}`, and its "
                    f"value `{named}` carries no derivative in {', '.join(coordinates)}; state it "
                    f"with a derivative line of the builder that writes the value of stage "
                    f"{stage.name!r}, in its stage file or in a marginal block bound with "
                    "`!marginals`, or bind on that builder a representation whose row of the "
                    "method table evaluates it",
                    candidates=(str(value) if value is not None else required, *coordinates),
                )
            )
    return tuple(found)


def _unmet_along(selection, periods, route, required, coordinates):
    """Where the requirement that `required`, a continuation value of the
    route's source, carry the derivative in `coordinates` comes to rest:
    None where a stated or represented derivative meets it, at the route's
    destination or, through the pass-through of D3, at an occurrence after
    it along the routes of the selection, or where the trellis ends before
    one is found; else the position of the occurrence whose value carries
    none, that value's identity (None where the route pairs no value with
    the one read), the coordinates there, and the names of the stages passed
    through on the way. A cycle of pass-throughs that states the derivative
    nowhere rests at the occurrence first revisited."""
    passed, visited = [], set()
    while True:
        destination = periods[route.destination[0]]["stages"][route.destination[1]]
        image = {pair.writing.field: pair.reading.field for pair in route.pairs}
        supplied = next(
            (component.supplied for component in route.components if component.required == required),
            None,
        )
        targets = tuple(image.get(name) for name in coordinates)
        if supplied is None or None in targets:
            named = tuple(target or name for target, name in zip(targets, coordinates))
            return route.destination, None, named, tuple(passed)
        value, coordinates = _identity_of(destination, supplied), targets
        while True:
            if value_carries_derivative(destination, value, coordinates):
                return None
            upstream = passed_through(destination, value, coordinates)
            if upstream is None:
                return route.destination, value, coordinates, tuple(passed)
            value, coordinates = upstream
            if value.perch == CONTINUATION:
                break
        key = (route.destination, str(value), coordinates)
        if key in visited:
            return route.destination, value, coordinates, tuple(passed)
        visited.add(key)
        passed.append(destination.name)
        required = str(value)
        route = next(
            (
                later
                for later in selection.routes
                if later.source == route.destination
                and all(name in later.source_fields for name in coordinates)
                and any(component.required == required for component in later.components)
            ),
            None,
        )
        if route is None:
            return None


def _identity_of(stage, supplied):
    """The identity of the function wire the destination supplies at its
    entry perch, from the spelling the route's component holds."""
    return next(
        sort.identity
        for sort in graph_of(stage, "builders", "backward").cod.inside
        if str(sort.identity) == supplied
    )


def _written_field(stage, required):
    """The field of the continuation input `required`, an identity as the
    route's component writes it, spelled as the stage file writes it,
    `dV[>]`."""
    sort = next(
        sort
        for sort in graph_of(stage, "builders", "backward").dom.inside
        if str(sort.identity) == required
    )
    return f"{sort.identity.field}{WRITTEN_MARK.get(sort.identity.perch, '')}"

