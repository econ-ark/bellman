"""The selection of the connections between the stage occurrences of a
trellis: the one operation that resolves the endpoints
an author writes, groups the candidates of inference, establishes the
compatibility of each pair, selects the unique admissible inferred pairs
and certifies the complete routes, from the placed stage occurrences, the
authored connectors of each period, the indexed inter-period mappings and
the effective period bindings.

A field of a stage occurrence is identified by its period, its stage key,
its perch and its local name: `cons.a` and `port.a` are two fields. A
**use** eligible for a connection is a state field at the continuation
perch, which leaves its stage, or at the entry perch, which enters it.
An authored connector may also pair a continuation value requirement
with a value supplied at the entry perch. An authored endpoint resolves to exactly one
eligible use: a bare name `a` where one use of that name stands at the
perch in the period, a qualified name `cons.a` naming the exact stage key
before the final dot, a keyed connector `{from: cons, to: port, fields:
{a: b}}` naming the two stages. An endpoint with no use or several is a
diagnostic naming the address and the candidates, and makes no pair; a
type makes no bare endpoint unambiguous. The authored pairs are resolved as
one group, before any inference, and claim their uses; an inferred
candidate is a same-name pair of uses no authored pair claims, in the
forward direction within a period, kept with every other candidate of the
same destination stage.

**Compatibility** (§3.3) is established for each pair from the declared
sets of its two uses, each read through the sets its own stage defines by
name: the set the continuation use writes lies in the set the arrival use
reads where the two resolved terms are one term, or where the package
decides the pair, a real set, an integer set or an interval with numeric
endpoints against another (`typing.sets.within`), or products of such sets
coordinate by coordinate. A set written with one condition that compares
the name it binds with a bound, `{x : ℝ | x > 0}`, is decided as the
interval with that bound, `(0, inf)`, within the set that the condition
restricts (`_one_bound`). A bound written as a parameter name is one bound
on both sides where the two stages stand in one period, since a parameter
name names one parameter of the period (§2.3); the same spelling in two
periods names two parameters and proves nothing, and the comparison is
then made at the values the effective bindings supply, the result naming
the bindings it read. A bound that names a derived parameter is read at
the value its definition takes at those bindings. A set with category codes
(`typing.category_codes.coded_meaning`: a set marked `!categories`, a
restriction of one, or a product with such a coordinate) is compared by its
codes, read before any name is resolved: the pair is compatible only where
each code the writing set may hold is a member of the reading set and
stands there for the same category, coordinate by coordinate, and a set with
codes and a set without them are incompatible. Every other
comparison, a set with several conditions or with a condition of another
form, a finite set or a bound without a value among them, is **not
established**: it is never accepted by optimism. An
authored pair that is incompatible or not established stands among the
pairs with its reason and a diagnostic, and certifies no complete route.

**Inference** selects a candidate pair only where its compatibility is
established and the choice is unique in a globally consistent set: one
compatible candidate for the arrival use, that continuation use the unique
candidate of one arrival use, and no cycle among the selected pairs: every
inferred pair whose two stages lie in one strongly connected component of
the graph of the authored and the selected pairs is withdrawn, whatever
the order the pairs were read in. Where two candidates compete, or two
directions close a cycle, the pairs stay unresolved with the reason
recorded, and no tie is broken.

**A route** is the set of selected pairs from one source stage, on one
branch where the source branches, into one destination stage. It is
certified where it carries the complete ordered state tuple, every arrival
coordinate of the destination supplied once by a continuation coordinate of
the source's branch and every coordinate of that branch mapped, so that the
pairs give a coordinate permutation; where every pair is compatible; where
the source's forward builders graph writes the joint law of that branch on
those coordinates, the finite measure that holds the branch's mass; and
where the backward components agree: the arrival value functions the
destination supplies answer the continuation value functions the source's
branch requires, each required component paired with a supplied one of its
role. Explicit pairs are resolved first, then equal names with perch marks
removed, and finally a sole remaining pair when the required field is
not kept. The supplied function may depend only on states that the state
pairs associate with permitted coordinates of the required field. Its
result set must lie in the required set. An authored cycle that includes a route, or a second authored claim
on one of its continuation fields, withholds its certificate. A
nonnegative marginal value admits zero and so
does not satisfy a strictly positive requirement. One coordinate from each
of two mutually exclusive branches supplies no jointly available state;
separate marginals supply no joint law. Nothing is differentiated and no
kernel is executed.

`select_connections` constructs no stage, binds no value, reads no file
and changes nothing it is given; it answers one immutable `Selection`,
from which the public joins (`bellman.factory.joins`), the drawings, the
Model Explorer view and the source writer (`file_entries.connector_entry`)
project their answers, so that no second rule decides a pair.
`trellis_selection` is the selection of an elaborated or specified
trellis, read from its periods, its inter-period mappings and the
calibration each occurrence holds; `connection_report` presents it, with
the diagnostics of the authored connectors that resolve to no certified
pair, from the occurrences of the same reading and no other, so that a
trellis whose connector resolves to no pair is a draft, a trellis answered
with the diagnostics of its selection standing, and no second set of
stage graphs is made for the report. Nothing is
written on the trellis dictionary: a change of a connector or of a bound
value changes the next reading's selection and no occurrence.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping
from numbers import Real
from types import MappingProxyType
from typing import NamedTuple

from bellman.fold.block_lines import blocks_in_file_order, header_of, parameter_sets
from bellman.fold.derived_parameters import derived_order, derived_value
from bellman.fold.stage_fold import stage_blocks_of
from bellman.fold.stage_names import StageNames, lines_of
from bellman.native.identity import Identity
from bellman.native.records import Condition
from bellman.native.provenance import source_description
from bellman.native.versions import StageVersion
from bellman.refusals import Diagnostic, FactoryError, written_kind
from bellman.stage.grains import graph_of, graph_refusal
from bellman.stage.stage_answers import branches, entry_perch, fields
from bellman.syntax import terms as T
from bellman.syntax.source import bound_name, bracket_of, to_source
from bellman.syntax.vocabulary import DOC, VALUE_ROLES
from bellman.typing import category_codes, sets
from bellman.typing.typed_expressions import substitute

__all__ = [
    "Candidate",
    "CandidateGroup",
    "Component",
    "ConnectionReport",
    "Diagnostic",
    "FieldUse",
    "PAIRING_RULES",
    "Pair",
    "REFUSING_RULES",
    "Rejection",
    "Route",
    "Selection",
    "connection_report",
    "select_connections",
    "trellis_selection",
]

# the two sides of a connector an eligible use stands on, named by the
# perch of the usual case: a use at the continuation perch writes, a use at
# the stage's entry perch reads, the arrival perch or, for a stage that
# declares none, the decision perch (`_side`; AMD-MB-001 P2)
WRITING, READING = "cntn", "arvl"
# the origin of a pair
AUTHORED, INFERRED = "authored", "inferred"
# the three answers of a compatibility check
COMPATIBLE, INCOMPATIBLE, NOT_ESTABLISHED = "compatible", "incompatible", "not-established"
# the two states of a route
CERTIFIED, UNCERTIFIED = "certified", "uncertified"
# the three keys of a keyed connector
_KEYED = ("from", "to", "fields")
# the two rules by which a required backward component is paired with a
# supplied one where no connector writes its pair (`EXPLICIT_PAIR`):
# `_paired` takes a written pair first, then equal names, then the one
# field left on each side; the pairing by the coordinates two marginal
# values' names declared is retired with the marginal roles (AMD-MB-001 R2)
PAIRING_RULES = ("one wire per role", "equal name")
EXPLICIT_PAIR = "explicit connector"
# A constructed draft retains semantic conflicts. Operations that require a
# valid dependency order still refuse the rules below.
REFUSING_RULES = ("connector-shape", "use-claimed-twice", "authored-cycle", "selected-cycle")


class FieldUse(NamedTuple):
    """One eligible use of a state field: the period `h`, the stage `key`,
    the `perch`, `cntn` for a field that leaves the stage and the entry
    perch for one that enters it, `arvl` or, for a stage that declares no
    arrival perch, `dcsn` (AMD-MB-001 P2), the local `field` name and the `branch`, the label of
    the branch whose block writes a continuation field, None elsewhere."""

    h: int
    key: str
    perch: str
    field: str
    branch: object

    def __str__(self):
        return f"periods[{self.h}].{self.key}.{self.field}"


class Pair(NamedTuple):
    """One selected connection: the `writing` and the `reading` use; its
    `origin`, `authored` or `inferred`; the `address` of the entry that
    writes an authored pair, `periods[0].connectors[1]` or
    `inter_connectors[2]`, and the period an inferred pair stands in; its
    `compatibility`, `compatible`, `incompatible` or `not-established`,
    with the `reason`, the comparison made; and the `basis`, the bindings
    the comparison read, `(h, key, digest)` per position, empty where it
    read none. For an authored pair, `source_address` names the expanded
    YAML mapping that writes it, `address` or `address.fields` in the keyed
    form, and `source_key` and `source_value` retain its endpoint spellings.
    These differ from the resolved local fields when an endpoint is
    qualified. `written_at` locates that mapping in the source files; the
    three source fields are None for an inferred pair."""

    writing: FieldUse
    reading: FieldUse
    origin: str
    address: str
    compatibility: str = NOT_ESTABLISHED
    reason: str = ""
    basis: tuple = ()
    source_address: str | None = None
    source_key: str | None = None
    source_value: str | None = None


class Candidate(NamedTuple):
    """One candidate of inference for a destination stage: the `source`
    stage's position `(h, key)` and the `pairs` of same-name uses it
    offers, each `(writing, reading)`, kept together as the coordinates one
    source supplies."""

    source: tuple
    pairs: tuple


class CandidateGroup(NamedTuple):
    """The candidates of one destination stage, kept together: the
    `destination` position `(h, key)`, its `reading` uses, the ordered
    arrival state tuple of the stage, and the `candidates`, one per source
    stage that offers a same-name use no authored pair claims."""

    destination: tuple
    reading: tuple
    candidates: tuple


class Rejection(NamedTuple):
    """One candidate pair of inference not selected: its `writing` and
    `reading` use, the `rule`, `candidate-incompatible`,
    `candidate-not-established`, `inference-disputed` or `inference-cycle`,
    and the `message`, why."""

    writing: FieldUse
    reading: FieldUse
    rule: str
    message: str


class Component(NamedTuple):
    """One backward component of a route checked: the `required` function
    wire of the source's branch at its continuation perch, by its spelling;
    the `supplied` wire of the destination's arrival perch paired with it,
    or None; the `role`; the `status`; the `reason`; the `basis`, the
    bindings the comparison of the result sets read; and the `rule` that
    paired the two, `EXPLICIT_PAIR` or one of `PAIRING_RULES`, empty where
    none did."""

    required: str
    supplied: object
    role: str
    status: str
    reason: str
    basis: tuple = ()
    rule: str = ""


class Route(NamedTuple):
    """One route of selected pairs from the `source` position, on its
    `branch` (a label, or None), into the `destination` position: the
    `source_fields`, the ordered continuation state tuple of the branch, and
    the `destination_fields`, the ordered arrival state tuple; the `pairs`,
    in the destination's order where the tuple is complete; the
    `permutation`, the index in `source_fields` of the source coordinate
    whose image is each destination index, and its `inverse`, the
    destination index that is the image of each source coordinate, both
    empty where the tuple is not complete; the `state`, `complete` or
    `incomplete`; the `compatibility` of the state pairs together; the
    `law`, the spelling of
    the joint measure the source writes on the branch, or None; the backward
    `components` and their `backward` status together; the `status`,
    `certified` or `uncertified`; the `obligations`, the sentences that
    withhold the certificate; and the `basis`, the bindings read."""

    source: tuple
    branch: object
    destination: tuple
    source_fields: tuple
    destination_fields: tuple
    pairs: tuple
    permutation: tuple
    inverse: tuple
    state: str
    compatibility: str
    law: object
    components: tuple
    backward: str
    status: str
    obligations: tuple
    basis: tuple


# `Diagnostic`, what the selection records without raising, is the record
# `bellman.refusals.Diagnostic`, imported above and shared with the stage's
# diagnostics; its docstring there lists the rules of a connection a selection
# records under, what their candidates are and what `source_entries` holds.


class Selection(NamedTuple):
    """What `select_connections` answers: `uses`, every eligible use of the
    trellis in period, key and header order; `pairs`, the authored pairs
    resolved and then the inferred pairs selected, each with its
    compatibility; `candidates`, the candidate groups of inference, one per
    destination stage that has one; `routes`, one per source stage, branch
    and destination stage among the pairs, certified or not; `rejected`, the
    candidate pairs not selected, with why; `diagnostics`; `counts`; and
    `bindings`, the digest of the effective calibration at each position the
    selection was given, the basis a compatibility result names; and
    `value_uses`, the eligible endpoints of explicit backward pairs."""

    uses: tuple
    pairs: tuple
    candidates: tuple
    routes: tuple
    rejected: tuple
    diagnostics: tuple
    counts: Mapping
    bindings: Mapping
    value_uses: tuple = ()


def select_connections(periods, inter_connectors, calibrations=None, *, first=0):
    """The `Selection` of a trellis: `periods`, its periods in order, each
    a mapping with the stage occurrences under `stages`, by key, and the
    authored connectors under `connectors`; `inter_connectors`, one mapping
    per adjacent pair, `inter_connectors[h]` joining `periods[h + 1]`, the
    earlier in time, to `periods[h]`; and `calibrations`, the effective
    calibration mapping at each position `(h, key)`, as
    `period_parameters.period_calibrations` answers it, or None, under
    which no comparison reads a value. `first` is the index of the first
    period given, so that a reading of some periods of a trellis numbers
    its positions and addresses as the trellis does: `periods[first]` is
    the first, `inter_connectors[first]` joins the second to it. Every
    stage occurrence is a constructed version; a position that holds none
    is a caller's error, refused with a TypeError. Otherwise refuses
    nothing: what an author wrote that resolves to no pair, and what cannot
    be certified, stands in `diagnostics`."""
    uses, domains = _uses(periods, first)
    types = _Types(periods, domains, calibrations, first)
    value_uses = tuple(_value_uses(types))
    index = _connection_index(uses, value_uses)
    pairs, diagnostics, reserved, value_pairs = _authored_connections(
        periods, inter_connectors, index, first=first
    )
    groups, excluded = _candidates(periods, index, pairs, reserved, first)
    pairs = [types.checked(pair) for pair in pairs]
    for pair in pairs:
        if pair.compatibility != COMPATIBLE:
            diagnostics.append(
                Diagnostic(
                    f"pair-{pair.compatibility}",
                    pair.address,
                    f"{pair.writing} → {pair.reading}: {pair.reason}",
                    source_entries=_sources((pair,)),
                )
            )
    inferred, rejected = _inferred(groups, pairs, types)
    selected = pairs + inferred
    # the final check of the selected dependency graph, once: the inferred
    # pairs on a cycle were withdrawn, so a cycle left is among authored
    # pairs and was recorded; one not recorded would be a defect, named
    edges = _edges(selected)
    for cycle in _cycles(edges):
        if not any(diagnostic.rule == "authored-cycle" for diagnostic in diagnostics):
            diagnostics.append(
                Diagnostic(
                    "selected-cycle",
                    f"periods[{cycle[0][0]}]",
                    "the selected pairs form a cycle: " + " → ".join(node[1] for node in cycle),
                    tuple(p for a, b in zip(cycle, cycle[1:]) for p in edges[a][b]),
                    _sources(p for a, b in zip(cycle, cycle[1:]) for p in edges[a][b]),
                )
            )
    cyclic_components = (
        _components(edges)
        if any(d.rule in ("authored-cycle", "selected-cycle") for d in diagnostics)
        else ()
    )
    component_of = {
        node: component
        for component in cyclic_components
        if len(component) > 1
        for node in component
    }
    cyclic_pairs = {
        pair
        for pair in selected
        if component_of.get((pair.writing.h, pair.writing.key)) is not None
        and component_of[pair.writing.h, pair.writing.key]
        is component_of.get((pair.reading.h, pair.reading.key))
    }
    routes = []
    built = _routes(selected, types, value_pairs, diagnostics)
    for route, depends_on in _conflicted_routes(built, diagnostics, cyclic_pairs):
        routes.append(route)
        if route.status != CERTIFIED:
            diagnostics.append(_route_diagnostic(route, depends_on))
    cycles = sum(1 for diagnostic in diagnostics if diagnostic.rule == "authored-cycle")
    counts = {
        "uses": len(uses),
        "pairs": len(pairs),
        "inferred": len(inferred),
        "groups": len(groups),
        "candidates": sum(len(group.candidates) for group in groups),
        "excluded": excluded,
        "rejected": len(rejected),
        "routes": len(routes),
        "certified": sum(1 for route in routes if route.status == CERTIFIED),
        "cycles": cycles,
        "diagnostics": len(diagnostics),
    }
    return Selection(
        uses=tuple(uses),
        pairs=tuple(selected),
        candidates=tuple(groups),
        routes=tuple(routes),
        rejected=tuple(rejected),
        diagnostics=tuple(diagnostics),
        counts=MappingProxyType(counts),
        bindings=MappingProxyType(types.bindings),
        value_uses=value_uses,
    )


def _sources(pairs):
    """Each distinct authored mapping entry that writes one of `pairs`."""
    return tuple(
        dict.fromkeys(
            (pair.source_address, pair.source_key, pair.source_value)
            for pair in pairs
            if pair.origin == AUTHORED
        )
    )


def _conflicted_routes(routes, diagnostics, cyclic_pairs):
    """Withhold route certificates affected by a duplicate source claim or
    an authored cycle, including edges omitted from a cycle witness. Other
    routes retain their own certificate. Answers each route paired with the
    address of the diagnostic its withholding rests on, the cycle's or the
    claim's, which the route's own diagnostic names as `depends_on`, and
    with None where the route keeps its certificate."""
    claimed_twice = {
        pair.writing: diagnostic.address
        for diagnostic in diagnostics
        if diagnostic.rule == "use-claimed-twice"
        for pair in diagnostic.candidates
    }
    cycles = [d for d in diagnostics if d.rule in ("authored-cycle", "selected-cycle")]
    found = []
    for route in routes:
        on_cycle = [pair for pair in route.pairs if pair in cyclic_pairs]
        claimed = [pair for pair in route.pairs if pair.writing in claimed_twice]
        if not on_cycle and not claimed:
            found.append((route, None))
            continue
        if on_cycle:
            obligation = "an authored cycle includes this route"
            # the cycle one of the route's pairs lies on, else the first
            # recorded, since a cycle's witness may leave out an edge
            witness = next(
                (d for d in cycles if any(pair in d.candidates for pair in on_cycle)),
                cycles[0] if cycles else None,
            )
            depends_on = None if witness is None else witness.address
        else:
            obligation = "two authored entries claim a continuation field of this route"
            depends_on = claimed_twice[claimed[0].writing]
        withheld = route._replace(
            status=UNCERTIFIED, obligations=route.obligations + (obligation,)
        )
        found.append((withheld, depends_on))
    return found


# --- the eligible uses ---


def _digest(stage):
    """The key under which the readings of one construction are kept: the
    text's digest with the digest of each addition read into it, since two
    occurrences of one text with different additions declare different
    fields (specification 0.7, F42); the object itself where the stage holds
    no digest."""
    provenance = stage.provenance
    if not provenance.get("sha256"):
        return id(stage)
    return provenance["sha256"], tuple(held["sha256"] for held in provenance.get("additions", ()))


def _uses(periods, first=0):
    """Every eligible use of the trellis, in period, key and header order,
    the periods numbered from `first`: the state fields at the continuation
    and the arrival perch of each stage occurrence, a continuation field
    with the label of the branch whose block writes it; and the declared
    set of each use, by `(h, key, perch, field)`."""
    found, domains, readings = [], {}, {}
    for h, period in enumerate(periods, first):
        for key, stage in period["stages"].items():
            if not isinstance(stage, StageVersion):
                raise TypeError(
                    f"periods[{h}].stages[{key!r}] holds a {type(stage).__name__}, not a "
                    "constructed stage occurrence; the connections are selected among the "
                    "fields of constructed stages"
                )
            # Formal field declarations and branches are the same for every
            # occurrence of one text with the same additions; values remain
            # separate in _Types.
            digest = _digest(stage)
            if digest not in readings:
                labels = {
                    identity.field: label
                    for label, written in branches(stage).items()
                    for identity in written
                }
                readings[digest] = fields(stage), labels, entry_perch(stage)
            table, labels, entry = readings[digest]
            for identity, sort in table.items():
                if sort.role != "state" or sort.perch not in (WRITING, entry):
                    continue
                branch = labels.get(identity.field) if sort.perch == WRITING else None
                found.append(FieldUse(h, key, sort.perch, identity.field, branch))
                domains[h, key, sort.perch, identity.field] = sort.domain
    return found, domains


def _connection_index(uses, value_uses):
    """The state and value endpoint indexes for one selection."""
    return _Index(uses, values=_Index(value_uses))


def _value_uses(types):
    """The continuation requirements and the entry supplies of each stage."""
    for h, period in enumerate(types.periods, types.first):
        for key in period["stages"]:
            text = types.text((h, key))
            for sort in text.required:
                name = sort.identity.field
                yield FieldUse(h, key, WRITING, name, text.value_branches.get(name))
            for sort in text.supplied:
                yield FieldUse(h, key, text.entry, sort.identity.field, None)


def _side(perch):
    """The side of a connector a use at `perch` stands on: `WRITING` at the
    continuation perch, `READING` at the entry perch, the arrival perch or,
    for a stage that declares none, the decision perch (AMD-MB-001 P2)."""
    return WRITING if perch == WRITING else READING


class _Index:
    """The uses by period, side and field name, and by period, key and side;
    a side is named by `WRITING` or `READING` (`_side`)."""

    def __init__(self, uses, *, values=None):
        self.values = values
        self.by_name = {}
        self.by_key = {}
        for use in uses:
            self.by_name.setdefault((use.h, _side(use.perch), use.field), []).append(use)
            self.by_key.setdefault((use.h, use.key, _side(use.perch)), []).append(use)

    def names(self, h, perch):
        """The field names of the uses at `perch` in period `h`."""
        return {field for (period, p, field) in self.by_name if period == h and p == perch}

    def resolve(self, token, h, perch, key=None):
        """The uses the endpoint `token` names at `perch` in period `h`: the
        one use of a bare name, every use of a name that several stages
        hold, none of a name no stage holds; `key`, from a keyed connector,
        restricts the stages. A token with a dot names the exact stage key
        before its final dot and the field after it."""
        if "." in token:
            stage, field = token.rsplit(".", 1)
            if key is not None and key != stage:
                return []
            return [use for use in self.by_key.get((h, stage, perch), []) if use.field == field]
        return [use for use in self.by_name.get((h, perch, token), []) if key in (None, use.key)]


# --- the authored pairs ---


def _authored_connections(periods, inter_connectors, index, *, first=0):
    """Resolve authored entries against an existing index of eligible uses.

    Return the pairs, diagnostics and set of reserved endpoints.
    Each writing use is claimed at most once; a resolved endpoint stays
    reserved when its other endpoint fails. No type or route is checked.
    """
    pairs, diagnostics, claimed, reserved = [], [], {}, set()
    value_pairs = {}
    for h, period in enumerate(periods, first):
        for number, connector in enumerate(period.get("connectors") or []):
            address = f"periods[{h}].connectors[{number}]"
            _authored(
                connector, h, h, address, index, pairs, diagnostics, claimed, reserved,
                value_pairs=value_pairs,
            )
    for i, mapping in enumerate(inter_connectors):
        if i + 1 >= len(periods):
            break
        h = first + i
        address = f"inter_connectors[{h}]"
        _authored(
            mapping,
            h + 1,
            h,
            address,
            index,
            pairs,
            diagnostics,
            claimed,
            reserved,
            between=True, value_pairs=value_pairs,
        )
    _authored_cycles(pairs, diagnostics)
    return pairs, diagnostics, reserved, value_pairs


def _authored(
    connector,
    h_from,
    h_to,
    address,
    index,
    pairs,
    diagnostics,
    claimed,
    reserved,
    between=False,
    *,
    value_pairs,
):
    """The pairs the connector at `address` writes, from the continuation
    uses of `periods[h_from]` to the arrival uses of `periods[h_to]`,
    appended to `pairs`, each writing use claimed once; an endpoint that
    resolves to no use or several, a keyed connector of another shape and
    a writing use claimed twice are appended to `diagnostics`. Each resolved
    endpoint is reserved against inference even when its other endpoint
    fails, so inference cannot replace the requested arrow."""
    what = "inter-period mapping" if between else "connector"
    if not isinstance(connector, Mapping):
        diagnostics.append(
            Diagnostic(
                "connector-shape",
                address,
                f"the {what} is written as {written_kind(connector)}, and a connector is a "
                f"mapping, `{{<continuation field>: <arrival field>}}`",
                (connector,),
                ((address, None, None),),
            )
        )
        return
    from_key = to_key = None
    entries = connector
    source_address = address
    if any(name in connector for name in _KEYED):
        missing = [name for name in _KEYED if name not in connector]
        extra = [name for name in connector if name not in _KEYED]
        if between:
            shape = (
                "the inter-period mapping is written in the keyed form, which names the two "
                "stages of one period; between two periods a mapping is {<continuation "
                "field>: <arrival field>}, a stage key before a field where the name is shared"
            )
        elif missing or extra:
            shape = "the connector is written in the keyed form and " + (
                f"lacks {', '.join(missing)}"
                if missing
                else f"has the key {extra[0]!r} beside from, to and fields"
            )
        elif not isinstance(connector["fields"], Mapping):
            shape = "the connector's `fields` is no mapping"
        else:
            shape = None
        if shape is not None:
            diagnostics.append(
                Diagnostic(
                    "connector-shape", address, shape, (connector,), ((address, None, None),)
                )
            )
            return
        from_key, to_key, entries = connector["from"], connector["to"], connector["fields"]
        source_address = f"{address}.fields"
    for source, target in entries.items():
        source_entry = (source_address, str(source), str(target))
        owner, role = index, "state"
        source_name, target_name = str(source), str(target)
        if index.values is not None:
            values = index.values
            state_from = index.resolve(source_name, h_from, WRITING, from_key)
            state_to = index.resolve(target_name, h_to, READING, to_key)
            value_from = values.resolve(_bare_field(source_name), h_from, WRITING, from_key)
            value_to = values.resolve(_bare_field(target_name), h_to, READING, to_key)
            if state_from and state_to and value_from and value_to:
                diagnostics.append(Diagnostic(
                    "endpoint-ambiguous", address,
                    f"{source!r} and {target!r} name both state and value pairs; "
                    "qualify the fields with their stage keys",
                    tuple(state_from + state_to + value_from + value_to), (source_entry,),
                ))
                continue
            if not (state_from and state_to) and (value_from or value_to):
                owner, role = values, "value"
                source_name, target_name = _bare_field(source_name), _bare_field(target_name)
        writing = _one(
            owner,
            source_name,
            h_from,
            WRITING,
            from_key,
            address,
            diagnostics,
            between,
            source_entry,
            role=role,
        )
        reading = _one(
            owner,
            target_name,
            h_to,
            READING,
            to_key,
            address,
            diagnostics,
            between,
            source_entry,
            role=role,
        )
        if role == "state":
            reserved.update(use for use in (writing, reading) if use is not None)
        elif writing is not None and reading is None:
            value_pairs.setdefault(writing, None)
        if writing is None or reading is None:
            continue
        pair = Pair(
            writing,
            reading,
            AUTHORED,
            address,
            source_address=source_address,
            source_key=str(source),
            source_value=str(target),
        )
        if writing.h == reading.h and writing.key == reading.key:
            diagnostics.append(
                Diagnostic(
                    "authored-cycle",
                    address,
                    f"the {what} maps {source!r} to {target!r}, and both fields are "
                    f"{writing.key}'s: a stage cannot take a field it produces",
                    (pair,),
                    (source_entry,),
                )
            )
            continue
        if writing in claimed:
            diagnostics.append(
                Diagnostic(
                    "use-claimed-twice",
                    address,
                    f"{claimed[writing].address} and {address} both map the continuation field "
                    f"{writing.field!r} of {writing.key} in periods[{writing.h}]; one entry maps "
                    "a continuation field, to one or several arrival fields",
                    (pair,),
                    _sources((claimed[writing], pair)),
                )
            )
            if role == "value":
                value_pairs[writing] = None
            continue
        claimed[writing] = pair
        if role == "value":
            value_pairs[writing] = pair
        else:
            pairs.append(pair)


def _bare_field(token):
    """The connector spelling with any perch mark removed."""
    return token.removesuffix("[>]").removesuffix("[<]")


def _one(index, token, h, perch, key, address, diagnostics, between, source_entry, *, role="state"):
    """The one use the endpoint `token` names, or None with a diagnostic
    appended: `endpoint-unresolved` for no use, `endpoint-ambiguous` for
    several, which names them."""
    found = index.resolve(token, h, perch, key)
    side = "continuation" if perch == WRITING else "arrival"
    where = f"periods[{h}]" if key is None else f"{key} in periods[{h}]"
    pair = (
        f" (the pair periods[{h}] → periods[{h - 1}])"
        if between and perch == WRITING
        else (f" (the pair periods[{h + 1}] → periods[{h}])" if between else "")
    )
    if len(found) == 1:
        return found[0]
    if not found:
        stage = key
        if key is None and "." in token:
            # the stage the token names before its final dot, or none
            stage = token.rsplit(".", 1)[0]
            keys = sorted({k for (period, k, _) in index.by_key if period == h})
            if stage not in keys:
                diagnostics.append(
                    Diagnostic(
                        "endpoint-unresolved",
                        address,
                        f"{token!r} names the stage {stage!r}, which periods[{h}] does not "
                        f"hold{pair}; the stages there are {', '.join(keys) or 'none'}",
                        source_entries=(source_entry,),
                    )
                )
                return None
            where = f"{stage} in periods[{h}]"
        held = sorted(
            index.names(h, perch)
            if stage is None
            else {use.field for use in index.by_key.get((h, stage, perch), [])}
        )
        there = f"of {stage} there" if stage is not None else "there"
        diagnostics.append(
            Diagnostic(
                "endpoint-unresolved",
                address,
                f"{token!r} names no {side} {role} field of {where}{pair}; the {side} "
                f"{role} fields {there} are {', '.join(held) or 'none'}",
                source_entries=(source_entry,),
            )
        )
        return None
    diagnostics.append(
        Diagnostic(
            "endpoint-ambiguous",
            address,
            f"{token!r} names {len(found)} {side} {role} fields of {where}{pair}: "
            + ", ".join(f"{use.key}.{use.field}" for use in found)
            + "; write the stage key before the field, `<key>.<field>`",
            tuple(found),
            (source_entry,),
        )
    )
    return None


# --- the dependency graph within each period and its cycles ---


def _edges(pairs):
    """The dependency graph the pairs within each period form, from the
    writing stage to the reading stage: `{position: {position: [pairs]}}`,
    a pair between periods and a pair from a stage to itself left out."""
    edges = {}
    for pair in pairs:
        if pair.writing.h != pair.reading.h or pair.writing.key == pair.reading.key:
            continue
        edges.setdefault((pair.writing.h, pair.writing.key), {}).setdefault(
            (pair.reading.h, pair.reading.key), []
        ).append(pair)
    return edges


def _cycles(edges):
    """The cycles of the graph `edges`, one per back edge of a depth-first
    walk, each as the closed path of positions it runs through; the walk
    keeps its own stack and recurses nowhere."""
    state, path, found = {}, [], []
    for start in list(edges):
        if start in state:
            continue
        state[start] = "open"
        path.append(start)
        frames = [(start, iter(edges.get(start, {})))]
        while frames:
            node, targets = frames[-1]
            advanced = False
            for target in targets:
                if state.get(target) == "open":
                    found.append(path[path.index(target) :] + [target])
                elif target not in state:
                    state[target] = "open"
                    path.append(target)
                    frames.append((target, iter(edges.get(target, {}))))
                    advanced = True
                    break
            if not advanced:
                frames.pop()
                path.pop()
                state[node] = "closed"
    return found


def _authored_cycles(pairs, diagnostics):
    """The cycles among the authored pairs within each period, each appended
    to `diagnostics` as `authored-cycle`. The dependency runs from the
    writing stage to the reading stage; two authored pairs in opposite
    directions between two stages are a cycle, two in one direction are
    not."""
    edges = _edges(pairs)
    for cycle in _cycles(edges):
        named = "; ".join(
            f"{a[1]} → {b[1]} ({', '.join(p.address for p in edges[a][b])})"
            for a, b in zip(cycle, cycle[1:])
        )
        diagnostics.append(
            Diagnostic(
                "authored-cycle",
                edges[cycle[0]][cycle[1]][0].address,
                f"the authored connections of periods[{cycle[0][0]}] form a cycle: {named}",
                tuple(p for a, b in zip(cycle, cycle[1:]) for p in edges[a][b]),
                _sources(p for a, b in zip(cycle, cycle[1:]) for p in edges[a][b]),
            )
        )


# --- the candidates of inference ---


def _candidates(periods, index, pairs, reserved, first=0):
    """The candidate groups of inference, one per destination stage that
    has a candidate, and the number of same-name pairs excluded: a
    candidate is a continuation use of one stage and an arrival use of
    another stage of the same period with the same name, neither reserved by
    an authored endpoint, from a source the destination does not reach through
    the authored pairs; a self-pair is no candidate. The periods are
    numbered from `first`."""
    reached = _reach(pairs)
    groups, excluded = [], 0
    for h, period in enumerate(periods, first):
        for key in period["stages"]:
            reading = tuple(index.by_key.get((h, key, READING), []))
            if not reading:
                continue
            by_source = {}
            for use in reading:
                for writing in index.by_name.get((h, WRITING, use.field), []):
                    source = (writing.h, writing.key)
                    if writing.key == key:
                        excluded += 1
                        continue
                    if writing in reserved or use in reserved:
                        excluded += 1
                        continue
                    if source in reached.get((h, key), ()):
                        # the destination reaches the source through the
                        # authored pairs, so this direction reverses them
                        excluded += 1
                        continue
                    by_source.setdefault(source, []).append((writing, use))
            if by_source:
                groups.append(
                    CandidateGroup(
                        (h, key),
                        reading,
                        tuple(
                            Candidate(source, tuple(found)) for source, found in by_source.items()
                        ),
                    )
                )
    return groups, excluded


def _reach(pairs):
    """The positions each position reaches through the authored pairs
    within its period, transitively."""
    edges = {}
    for pair in pairs:
        if pair.writing.h == pair.reading.h and pair.writing.key != pair.reading.key:
            edges.setdefault((pair.writing.h, pair.writing.key), set()).add(
                (pair.reading.h, pair.reading.key)
            )
    reached = {}
    for start in edges:
        seen, stack = set(), list(edges[start])
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(edges.get(node, ()))
        reached[start] = frozenset(seen)
    return reached


# --- the typed readings the compatibility checks need ---


def _bindings(calibrations):
    """The digest of the effective calibration at each position, None for a
    position with no mapping; empty where no calibrations are given."""
    if not calibrations:
        return {}
    return {
        position: (None if mapping is None else source_description(mapping)["sha256"])
        for position, mapping in calibrations.items()
    }


class _Text:
    """What the compatibility checks read of one stage text, read once per
    text: the sets it defines by name, the category codes of each set it
    marks `!categories` and the text's digest, which keys the categories of
    a set marked without an identifier (None for a stage that holds no
    digest), the names of its parameters, the
    continuation state fields of each branch and of the stage, the state
    fields of its entry perch (`entry`, the arrival perch or, for a stage
    that declares none, the decision perch; AMD-MB-001 P2), the joint
    measures its forward builders graph writes at the continuation perch
    by branch label, the function wires its backward builders graph
    requires at the continuation perch and supplies at the entry perch,
    and the reason either graph is not constructed."""

    def __init__(self, stage):
        self.name = stage.name
        self.entry = entry_perch(stage)
        self.definitions = {
            definition.identity.field: definition.equations[0]
            for definition in stage.definitions.values()
            if definition.kind == "set" and definition.equations
        }
        self.functions = {
            definition.identity.field: definition.equations[0]
            for definition in stage.definitions.values()
            if definition.kind == "function" and definition.equations
            and isinstance(definition.equations[0], T.FuncDef)
        }
        self.categories = {
            definition.identity.field: definition.categories
            for definition in stage.definitions.values()
            if definition.kind == "set" and definition.categories is not None
        }
        self.digest = stage.provenance.get("sha256")
        self.parameters = frozenset(parameter_sets(stage))
        table = fields(stage)
        self.writing_fields = tuple(
            identity.field
            for identity, sort in table.items()
            if sort.perch == WRITING and sort.role == "state"
        )
        self.reading_fields = tuple(
            identity.field
            for identity, sort in table.items()
            if sort.perch == self.entry and sort.role == "state"
        )
        self.branch_fields = {
            label: tuple(identity.field for identity in written)
            for label, written in branches(stage).items()
        }
        self.laws, self.forward_refusal = {}, None
        refusal = graph_refusal(stage, "builders", "forward")
        if refusal is None:
            for sort in graph_of(stage, "builders", "forward").cod.inside:
                if sort.kind == "measure" and sort.perch == WRITING:
                    self.laws[sort.identity.field] = (
                        str(sort.identity),
                        tuple(coordinate.field for coordinate in sort.coordinates),
                    )
        else:
            self.forward_refusal = refusal.reason
        self.required, self.supplied, self.backward_refusal = (), (), None
        self.kept, self.value_branches = frozenset(), {}
        refusal = graph_refusal(stage, "builders", "backward")
        if refusal is None:
            graph = graph_of(stage, "builders", "backward")
            self.required = tuple(
                sort
                for sort in graph.dom.inside
                if sort.kind == "function" and sort.perch == WRITING and sort.role in VALUE_ROLES
            )
            self.supplied = tuple(
                sort
                for sort in graph.cod.inside
                if sort.kind == "function" and sort.perch == self.entry and sort.role in VALUE_ROLES
            )
            self.kept = _kept_requirements(stage)
            if self.branch_fields:
                self.value_branches = {
                    identity.field: branch
                    for identity, (_, branch) in stage_blocks_of(stage).bases.items()
                }
        else:
            self.backward_refusal = refusal.reason


def _kept_requirements(stage):
    """Continuation names returned unchanged by a backward block."""
    ctx = StageNames(stage)
    kept = set()
    for box in blocks_in_file_order(stage):
        inputs, outputs = header_of(box)
        required = {sort.identity.field for sort in inputs
                    if sort.perch == WRITING and sort.role in VALUE_ROLES}
        if not required:
            continue
        written = {
            identity for _, line in lines_of(stage, box) if line.role != DOC
            for identity in ctx.defined(line.core, box.name)
        }
        kept.update(
            sort.identity.field for sort in outputs
            if sort.perch == "dcsn" and sort.role in VALUE_ROLES
            and sort.identity.field in required and sort.identity not in written
        )
    return frozenset(kept)


class _Types:
    """The typed readings of the placed occurrences, by position, and the
    effective bindings: what `_coded_included` and `_included` compare and
    `_routes` certifies from. A text is read once however many positions
    hold it."""

    def __init__(self, periods, domains, calibrations, first=0):
        self.periods = periods
        self.first = first
        self.domains = domains
        self.calibrations = calibrations or {}
        self.bindings = _bindings(calibrations)
        self._texts = {}
        self._derived = {}

    def stage(self, position):
        h, key = position
        return self.periods[h - self.first]["stages"][key]

    def text(self, position):
        """The `_Text` of the stage at `position`."""
        stage = self.stage(position)
        digest = _digest(stage)
        held = self._texts.get(digest)
        if held is None:
            held = self._texts[digest] = _Text(stage)
        return held

    def domain(self, use):
        """The declared set of a use, a retained term or None."""
        return self.domains.get((use.h, use.key, use.perch, use.field))

    def derived(self, position):
        """The value of each derived parameter of the stage at `position`
        at the effective calibration there, by name: each definition
        evaluated by `derived_value` after the derived parameters it reads
        (`derived_order`), as `derived_values` evaluates them at a
        calibration. A definition that has no value at the calibration, one
        that reads a parameter the calibration does not bind among them,
        gives its name no value and is refused nowhere."""
        if position not in self._derived:
            mapping, found = self.calibrations.get(position) or {}, {}
            for definition in derived_order(self.stage(position).definitions):
                try:
                    found[definition.identity.field] = derived_value(
                        definition.equations[0], {**mapping, **found}
                    )
                except ValueError:
                    continue
            self._derived[position] = found
        return self._derived[position]

    def values(self, position, names):
        """The finite numbers the effective calibration at `position`
        supplies for the parameter `names`, a derived parameter read at the
        value its definition takes at that calibration (`derived`), and the
        basis, `((h, key, digest),)` where a value was read, else `()`; a
        value that is no finite number is no value."""
        mapping = self.calibrations.get(position)
        if not mapping:
            return {}, ()
        if any(name not in mapping for name in names):
            mapping = {**self.derived(position), **mapping}
        found = {
            name: mapping[name]
            for name in names
            if name in mapping
            and isinstance(mapping[name], Real)
            and not isinstance(mapping[name], bool)
            and math.isfinite(mapping[name])
        }
        basis = ((position[0], position[1], self.bindings.get(position)),) if found else ()
        return found, basis

    def codes(self, position, term):
        """The category codes of the declared set `term` of the stage at
        `position`, read through the sets its text defines and marks before
        any name is resolved (`category_codes.coded_meaning`); None for a
        set without codes."""
        text = self.text(position)
        return category_codes.coded_meaning(term, text.definitions, text.categories, text.digest)

    def checked(self, pair):
        """The pair with its compatibility: whether the set its writing use
        is declared in lies in the set its reading use is declared in, and,
        where either set has category codes, whether each code written
        stands for the same category where it is read (`_coded_included`)."""
        source = (pair.writing.h, pair.writing.key)
        destination = (pair.reading.h, pair.reading.key)
        written, read = self.domain(pair.writing), self.domain(pair.reading)
        status, reason, basis = _coded_included(
            self,
            source,
            written,
            self.codes(source, written),
            destination,
            read,
            self.codes(destination, read),
            f"the continuation set of {pair.writing}",
            f"the arrival set of {pair.reading}",
        )
        return pair._replace(compatibility=status, reason=reason, basis=basis)


def _bounds(term):
    """The names a set term writes as bounds, `a_min` in `[a_min, inf)`:
    every constant symbol inside it but the infinity and, inside a set with
    conditions, the name that the set binds, the `x` of `{x : ℝ | x >
    a_min}`, which is the variable of the conditions."""
    found = set()

    def walk(value, bound=frozenset()):
        if isinstance(value, T.Sym) and isinstance(value.symbol, T.Constant):
            name = value.symbol.name
            if isinstance(name, str) and name != "inf" and name not in bound:
                found.add(name)
            return
        if isinstance(value, T.Comprehension) and isinstance(value.bound, T.Subject):
            bound = bound | {
                c.stem for c in value.bound.coordinates if isinstance(c, T.Coordinate)
            }
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            for field in dataclasses.fields(value):
                walk(getattr(value, field.name), bound)
        elif isinstance(value, tuple):
            for item in value:
                walk(item, bound)

    walk(term)
    return frozenset(found)


def _interval_calls(term, functions, endpoint=False, active=frozenset()):
    """Read calls in interval endpoints using the definitions of their stage."""
    if endpoint and isinstance(term, T.Call) and term.fun in functions and term.fun not in active:
        definition = functions[term.fun]
        if len(definition.params) == len(term.args):
            arguments = tuple(_interval_calls(arg, functions, True, active) for arg in term.args)
            names = (param.stem for param in definition.params)
            body = substitute(definition.body, dict(zip(names, arguments)))
            return _interval_calls(body, functions, True, active | {term.fun})
    endpoint = endpoint or isinstance(term, T.Interval)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        changes = {}
        for field in dataclasses.fields(term):
            old = getattr(term, field.name)
            new = _interval_calls(old, functions, endpoint, active)
            if new is not old:
                changes[field.name] = new
        return dataclasses.replace(term, **changes) if changes else term
    if isinstance(term, tuple):
        new = tuple(_interval_calls(item, functions, endpoint, active) for item in term)
        return new if any(a is not b for a, b in zip(new, term)) else term
    return term


def _valued(term, values):
    """The set term with each bound named in `values` replaced by its
    number, `[a_min, inf)` at `a_min = 1` being `[1, inf)` and at
    `a_min = -1` being `[-1, inf)`."""
    if (
        isinstance(term, T.Sym)
        and isinstance(term.symbol, T.Constant)
        and term.symbol.name in values
    ):
        value = values[term.symbol.name]
        if not isinstance(value, int):
            # an integral value is written as the integer, as
            # `sets.set_of_bounds` writes an endpoint
            value = int(value) if float(value).is_integer() else float(value)
        # the grammar writes a sign as the negation of a magnitude
        number = T.Number(abs(value))
        return T.Neg(number) if value < 0 else number
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        changes = {}
        for field in dataclasses.fields(term):
            old = getattr(term, field.name)
            new = _valued(old, values)
            if new is not old:
                changes[field.name] = new
        return dataclasses.replace(term, **changes) if changes else term
    if isinstance(term, tuple):
        new = tuple(_valued(item, values) for item in term)
        return new if any(a is not b for a, b in zip(new, term)) else term
    return term


def _within(inner, outer, inner_values=None, outer_values=None):
    """Whether the resolved set `inner` lies in the resolved set `outer`,
    each read at its occurrence's parameter values: True or False where the
    package decides the pair, a real set, an
    integer set or an interval with numeric endpoints against another
    (`typing.sets.within`), two products of equal length coordinate by
    coordinate, two finite index sets by their members, where a field valued
    in the set connects whenever every member of the writing set is a member
    of the reading set, and two sets of functions, where a field valued in
    functions on an index set connects only when the two index sets have the
    same members in the same order, since an array passed unchanged would
    exchange values at keys otherwise, and the entry sets are included. A
    set with one condition that compares the name it binds with a bound is
    decided as the interval it denotes at the values (`_one_bound`). None
    otherwise, a set with other conditions or a product against a scalar set
    among the undecided, unless the two are one term whose conditions read
    numbers and names alone (`_conditions_in_names`)."""
    inner_values, outer_values = inner_values or {}, outer_values or {}
    if inner == outer and inner_values == outer_values and _conditions_in_names(inner):
        return True
    inner, outer = _one_bound(inner, inner_values), _one_bound(outer, outer_values)
    if isinstance(inner, T.Product) and isinstance(outer, T.Product):
        if len(inner.factors) != len(outer.factors):
            return False
        answers = [
            _within(a, b, inner_values, outer_values)
            for a, b in zip(inner.factors, outer.factors)
        ]
        return False if False in answers else (True if all(answers) else None)
    if isinstance(inner, T.Functions) or isinstance(outer, T.Functions):
        if not (isinstance(inner, T.Functions) and isinstance(outer, T.Functions)):
            return False
        writing = _domain_members(inner, inner_values)
        reading = _domain_members(outer, outer_values)
        if writing is None or reading is None:
            forward = _within(inner.domain, outer.domain, inner_values, outer_values)
            reverse = _within(outer.domain, inner.domain, outer_values, inner_values)
            if forward is not True or reverse is not True:
                return None
            return _within(inner.codomain, outer.codomain, inner_values, outer_values)
        if len(writing) != len(reading) or any(
            len(a) != len(b)
            or any(sets.key_position((right,), left) is None for left, right in zip(a, b))
            for a, b in zip(writing, reading)
        ):
            return False
        return _within(inner.codomain, outer.codomain, inner_values, outer_values)
    finite = (T.IntegerRange, T.Points, T.FiniteSet)
    if isinstance(inner, finite) and isinstance(outer, finite):
        writing = sets.finite_members(inner, inner_values, {})
        reading = sets.finite_members(outer, outer_values, {})
        if writing is None or reading is None:
            return None
        return all(sets.key_position(reading, member) is not None for member in writing)
    if isinstance(inner, (T.Product, T.Comprehension, T.FiniteSet)) or isinstance(
        outer, (T.Product, T.Comprehension, T.FiniteSet)
    ):
        return None
    inner = _evaluated(_valued(inner, inner_values))
    outer = _evaluated(_valued(outer, outer_values))
    if not (_conditions_in_names(inner) and _conditions_in_names(outer)):
        return None
    return sets.within(inner, outer, {})


def _conditions_in_names(term):
    """Whether a set term has only explicit arithmetic and comparisons."""
    if isinstance(term, (T.Call, T.Select)):
        return False
    if isinstance(term, T.Interval) and not _bounds(term):
        return sets.endpoints(_evaluated(term)) is not None
    if isinstance(term, T.Comprehension) and not all(
        isinstance(condition, T.Rel)
        and sets.parameters_read(condition.left) is not None
        and sets.parameters_read(condition.right) is not None
        for condition in term.conds
    ):
        return False
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        return all(
            _conditions_in_names(getattr(term, field.name)) for field in dataclasses.fields(term)
        )
    if isinstance(term, tuple):
        return all(_conditions_in_names(item) for item in term)
    return True


def _one_bound(term, values=None):
    """The set that a set with one condition denotes at the parameter values
    `values`, where the condition compares the name that the set binds with
    a bound that is a number at the values, and the set that it restricts is
    a real set or an interval with numeric endpoints: `{x : ℝ | x > a_min}`
    at `a_min = 0` is `(0, inf)`, and `{x : ℝ₊ | x < 5}` is `[0, 5)`, the
    members of the restricted set that lie in the interval from the bound
    (`typing.sets.meet`). Every other term is answered as it is: a set with
    several conditions, a condition of another form, a bound without a
    value, a restricted set of another form, and a set that holds no
    number."""
    if not isinstance(term, T.Comprehension) or term.base is None or len(term.conds) != 1:
        return term
    name, (condition,) = bound_name(term.bound), term.conds
    if (
        name is None
        or not isinstance(condition, T.Rel)
        or not isinstance(condition.op, (T.Gt, T.Ge, T.Lt, T.Le))
    ):
        return term
    below = isinstance(condition.op, (T.Gt, T.Ge))
    if condition.left == name:
        bound = condition.right
    elif condition.right == name:
        # `0 < x` bounds the name as `x > 0` does
        bound, below = condition.left, not below
    else:
        return term
    values = values or {}
    bound, bracket = _evaluated(_valued(bound, values)), bracket_of(condition.op)
    infinity = T.Sym(T.Constant("inf"))
    interval = T.Interval(
        T.Range(bracket, bound, infinity, T.Open())
        if below
        else T.Range(T.Open(), T.Neg(infinity), bound, bracket)
    )
    met = sets.meet((_evaluated(_valued(term.base, values)), interval))
    if met is None:
        return term
    return interval if sets.endpoints(met) == sets.endpoints(interval) else met


def _domain_members(functions, values):
    """The members of each index set of a collection's domain at the values,
    one tuple per factor in the domain's order, so that two collections are
    compared key by key; None where a factor's members are not decided."""
    domain = functions.domain
    factors = domain.factors if isinstance(domain, T.Product) else (domain,)
    members = tuple(sets.finite_members(factor, values, {}) for factor in factors)
    if any(found is None for found in members):
        return None
    return members


def _order_detail(inner, outer, inner_values=None, outer_values=None):
    """The words added to the reason of an incompatible pair of collections
    whose index sets hold the same members in another order: an array passed
    unchanged would exchange values at keys."""
    if not (isinstance(inner, T.Functions) and isinstance(outer, T.Functions)):
        return ""
    writing = _domain_members(inner, inner_values or {})
    reading = _domain_members(outer, outer_values or {})
    if writing is None or reading is None:
        return ""
    same_order = len(writing) == len(reading) and all(
        len(a) == len(b)
        and all(sets.key_position((right,), left) is not None for left, right in zip(a, b))
        for a, b in zip(writing, reading)
    )
    same_members = len(writing) == len(reading) and all(
        len(a) == len(b) and all(sets.key_position(b, member) is not None for member in a)
        for a, b in zip(writing, reading)
    )
    if same_members and not same_order:
        return (
            ", the same members in another order, so an array passed unchanged would exchange "
            "the values at the keys"
        )
    return ""


def _evaluated(term):
    """A set term with every bound or member written as arithmetic of numbers
    replaced by its number, read through the one arithmetic interpretation,
    so that `{0, …, J − 1}` at `J = 3` is compared as `{0, …, 2}`."""
    if isinstance(term, (T.Add, T.Sub, T.Mul, T.Div, T.Pow, T.Neg)):
        value = sets.number_at(term, {}).value
        if value is not None:
            return _number_term(value)
    if isinstance(term, (T.Call, T.Conditional, T.Add, T.Sub, T.Mul, T.Div, T.Pow, T.Neg)):
        try:
            value = derived_value(term, {})
        except (ValueError, KeyError):
            return term
        if math.isinf(value):
            infinity = T.Sym(T.Constant("inf"))
            return T.Neg(infinity) if value < 0 else infinity
        return _number_term(value)
    if dataclasses.is_dataclass(term) and not isinstance(term, type):
        changes = {}
        for field in dataclasses.fields(term):
            old = getattr(term, field.name)
            new = _evaluated(old)
            if new is not old:
                changes[field.name] = new
        return dataclasses.replace(term, **changes) if changes else term
    if isinstance(term, tuple):
        new = tuple(_evaluated(item) for item in term)
        return new if any(a is not b for a, b in zip(new, term)) else term
    return term


def _number_term(value):
    """The term of a number a bound or a member evaluates to: an integer as
    the integer, a ratio as its double, a negative number as the negation of
    its magnitude, which is how the grammar writes a sign."""
    if not isinstance(value, (int, float)):
        value = int(value) if value.denominator == 1 else float(value)
    number = T.Number(abs(value))
    return T.Neg(number) if value < 0 else number


def _included(
    types, inner_position, inner_term, outer_position, outer_term, inner_said, outer_said
):
    """Whether the set `inner_term`, declared at `inner_position`, lies in
    the set `outer_term`, declared at `outer_position`: `(status, reason,
    basis)`. Each term is read through the sets its own stage defines by
    name. Two resolved terms that are one term are one set where they
    write no bound, and where they write bounds that name parameters both
    stages of one period declare, one parameter of the period each (§2.3);
    the same spelling in two periods proves nothing. A term that writes a
    bound is otherwise compared at the values the effective bindings
    supply, a derived parameter at the value of its definition there
    (`_Types.derived`), and the result names them; without a value the
    comparison is not established. The name that a set with conditions
    binds is no bound (`_bounds`), and a term with a condition that calls a
    function or selects an entry is one set with no other use of it
    (`_conditions_in_names`). Terms without bounds are decided by
    `_within`."""
    if inner_term is None or outer_term is None:
        return (
            NOT_ESTABLISHED,
            f"no set is declared for {inner_said if inner_term is None else outer_said}",
            (),
        )
    inner_text, outer_text = types.text(inner_position), types.text(outer_position)
    inner = _interval_calls(sets.resolved(inner_term, inner_text.definitions), inner_text.functions)
    outer = _interval_calls(sets.resolved(outer_term, outer_text.definitions), outer_text.functions)
    inner_bounds, outer_bounds = _bounds(inner), _bounds(outer)
    one_term = inner == outer and _conditions_in_names(inner)
    if one_term and not inner_bounds:
        return COMPATIBLE, f"{inner_said} and {outer_said} are one set, {to_source(inner)}", ()
    if (
        one_term
        and inner_position[0] == outer_position[0]
        and inner_bounds <= inner_text.parameters
        and inner_bounds <= outer_text.parameters
    ):
        return (
            COMPATIBLE,
            f"{inner_said} and {outer_said} are one set, {to_source(inner)}, whose bound"
            f"{'s' if len(inner_bounds) > 1 else ''} {', '.join(sorted(inner_bounds))} "
            f"name{'' if len(inner_bounds) > 1 else 's'} one parameter of "
            f"periods[{inner_position[0]}]",
            (),
        )
    if inner_bounds or outer_bounds:
        inner_values, inner_basis = types.values(inner_position, inner_bounds)
        outer_values, outer_basis = types.values(outer_position, outer_bounds)
        missing = sorted(
            [f"{name} of {_at(inner_position)}" for name in inner_bounds - set(inner_values)]
            + [f"{name} of {_at(outer_position)}" for name in outer_bounds - set(outer_values)]
        )
        if missing:
            spelled = (
                f"the same spelling {to_source(inner)} in periods[{inner_position[0]}] and "
                f"periods[{outer_position[0]}] names two parameters, and "
                if inner == outer and inner_position[0] != outer_position[0]
                else ""
            )
            return (
                NOT_ESTABLISHED,
                f"{spelled}the bound{'s' if len(missing) > 1 else ''} {' and '.join(missing)} "
                f"{'have' if len(missing) > 1 else 'has'} no finite value in the bindings "
                "given, so "
                f"{inner_said}, {to_source(inner)}, against {outer_said}, {to_source(outer)}, "
                "is not decided",
                (),
            )
        decided = _within(inner, outer, inner_values, outer_values)
        at = ", ".join(
            f"{name} = {value!r} of periods[{position[0]}].{position[1]}"
            for position, values in (
                (inner_position, inner_values),
                (outer_position, outer_values),
            )
            for name, value in sorted(values.items())
        )
        compared = ""
        inner_read, outer_read = _one_bound(inner, inner_values), _one_bound(outer, outer_values)
        if isinstance(inner_read, (T.Interval, T.Named)) and isinstance(
            outer_read, (T.Interval, T.Named)
        ):
            inner_at = _evaluated(_valued(inner_read, inner_values))
            outer_at = _evaluated(_valued(outer_read, outer_values))
            compared = f": {to_source(inner_at)} against {to_source(outer_at)}"
        return (
            _status(decided),
            f"{inner_said}, {to_source(inner)}, {_verb(decided)} {outer_said}, "
            f"{to_source(outer)}, at the values {at}{compared}"
            f"{_order_detail(inner, outer, inner_values, outer_values)}",
            inner_basis + outer_basis,
        )
    decided = _within(inner, outer)
    return (
        _status(decided),
        f"{inner_said}, {to_source(inner)}, {_verb(decided)} {outer_said}, {to_source(outer)}"
        f"{_order_detail(inner, outer)}",
        (),
    )


def _coded_included(
    types,
    inner_position,
    inner_term,
    writing,
    outer_position,
    outer_term,
    reading,
    inner_said,
    outer_said,
    restriction=None,
):
    """Whether values of the set `inner_term`, declared at `inner_position`
    with the category codes `writing`, may be copied into the set
    `outer_term`, declared at `outer_position` with the codes `reading`:
    `(status, reason, basis)`, as `_included` answers it. The codes are
    those `_Types.codes` reads: a `category_codes.CodedMeaning`, a tuple of
    a product's coordinates, or None for a set without codes.

    `_included` decides a pair where neither set has codes or a set is
    not declared. Two sets with codes are decided by
    `category_codes.compared`, and neither `_bounds` nor `_within` is read,
    since a comprehension's binder is no parameter: compatible where every
    code the writing set may hold is a member of the reading set with the
    same category, incompatible where a code it holds is no member or
    stands for another category, and not established where the answer
    depends on members a restriction leaves undetermined, except that two
    uses of one restriction of one coded set are one set where its
    conditions read only parameters of one period (`_one_restriction`, as
    `_included` decides one bounded set). Two products of
    equal length are decided coordinate by coordinate and the answers
    combined by `_together`; a pair of coordinates without codes is decided
    by `_included`, and is not established under the `restriction` of a
    product by a comprehension, which `_within` does not decide. A set with
    codes against a set without codes, or against a set of another shape,
    is incompatible."""
    if writing is None and reading is None and restriction is not None:
        return (
            NOT_ESTABLISHED,
            f"{inner_said}, {to_source(inner_term)}, against {outer_said}, "
            f"{to_source(outer_term)}, is not decided, since {to_source(restriction)} restricts "
            "the product by conditions the package does not compare",
            (),
        )
    if (writing is None and reading is None) or inner_term is None or outer_term is None:
        return _included(
            types, inner_position, inner_term, outer_position, outer_term, inner_said, outer_said
        )
    both = f"{inner_said}, {to_source(inner_term)}, and {outer_said}, {to_source(outer_term)},"
    if isinstance(writing, category_codes.CodedMeaning) and isinstance(
        reading, category_codes.CodedMeaning
    ):
        decided, why = category_codes.compared(writing, reading)
        if (
            decided is None
            and writing == reading
            and restriction is None
            and category_codes.identified(writing)
        ):
            read = _one_restriction(types, inner_position, inner_term, outer_position, outer_term)
            if read is not None:
                where = (
                    f", whose conditions read {', '.join(read)}, "
                    f"{'each ' if len(read) > 1 else ''}one parameter of "
                    f"periods[{inner_position[0]}]"
                    if read
                    else ", whose conditions read no parameter"
                )
                return (
                    COMPATIBLE,
                    f"{inner_said} and {outer_said} are one set with category codes, "
                    f"{to_source(inner_term)}{where}: {writing.description}",
                    (),
                )
        return _status(decided), f"{both} have category codes; {why}", ()
    inner = _coordinates(inner_term, types.text(inner_position))
    outer = _coordinates(outer_term, types.text(outer_position))
    if inner is not None and outer is not None:
        count = len(inner[0])
        writings = (None,) * count if writing is None else writing
        readings = (None,) * count if reading is None else reading
        if len(outer[0]) == count == len(writings) == len(readings):
            restricted = next(
                (found for found in (restriction, inner[1], outer[1]) if found is not None), None
            )
            answers = [
                _coded_included(
                    types,
                    inner_position,
                    a,
                    w,
                    outer_position,
                    b,
                    r,
                    f"coordinate {k} of {inner_said}",
                    f"coordinate {k} of {outer_said}",
                    restricted,
                )
                for k, (a, w, b, r) in enumerate(zip(inner[0], writings, outer[0], readings), 1)
            ]
            status = _together(answer[0] for answer in answers)
            return (
                status,
                f"{both} are compared coordinate by coordinate: "
                + "; ".join(answer[1] for answer in answers if answer[0] == status),
                tuple(dict.fromkeys(entry for answer in answers for entry in answer[2])),
            )
    return (
        INCOMPATIBLE,
        f"{inner_said}, {to_source(inner_term)}, {_codes_in_words(writing)}, and "
        f"{outer_said}, {to_source(outer_term)}, {_codes_in_words(reading)}; a value is copied "
        "from or into a set "
        "with category codes only where each code stands for the same category on both sides",
        (),
    )


def _one_restriction(types, inner_position, inner_term, outer_position, outer_term):
    """The parameters the conditions of one restriction of a coded set read,
    sorted, where `inner_term` and `outer_term`, resolved through their own
    texts, are one term whose conditions compare terms written in numbers,
    its binders and parameters both texts declare, and, where they read a
    parameter, the two positions stand in one period, a parameter name
    naming one parameter of the period (§2.3); None otherwise, a condition
    that calls a function or selects an entry included, since the names
    alone do not fix its value."""
    inner_text, outer_text = types.text(inner_position), types.text(outer_position)
    inner = sets.resolved(inner_term, inner_text.definitions)
    if inner != sets.resolved(outer_term, outer_text.definitions):
        return None
    names = _condition_names(inner)
    if names is None:
        return None
    read = names - _binders(inner)
    if read and not (
        inner_position[0] == outer_position[0]
        and read <= inner_text.parameters & outer_text.parameters
    ):
        return None
    return tuple(sorted(read))


def _condition_names(term):
    """The names the conditions of a restriction read, through the
    comprehensions it is built on: each condition a comparison of two terms
    written in numbers and names (`sets.parameters_read`). None where a
    condition reads anything else, a call or a selection among them, or the
    restriction stands on a set that is neither a comprehension nor a name."""
    if isinstance(term, T.Named):
        return frozenset()
    if not isinstance(term, T.Comprehension) or term.base is None:
        return None
    found = _condition_names(term.base)
    for condition in term.conds:
        if found is None or not isinstance(condition, T.Rel):
            return None
        for side in (condition.left, condition.right):
            read = sets.parameters_read(side)
            if read is None:
                return None
            found = found | read
    return found


def _binders(term):
    """The names the comprehensions inside a set term bind."""
    found = set()

    def walk(value):
        if isinstance(value, T.Comprehension) and isinstance(value.bound, T.Subject):
            found.update(c.stem for c in value.bound.coordinates if isinstance(c, T.Coordinate))
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            for field in dataclasses.fields(value):
                walk(getattr(value, field.name))
        elif isinstance(value, tuple):
            for item in value:
                walk(item)

    walk(term)
    return frozenset(found)


def _coordinates(term, text, active=()):
    """The factors of the product set `term` and the comprehension that
    restricts it, `(factors, restriction)`, the restriction None where none
    does: `term` read through each name `text` defines without category
    codes, as `category_codes.coded_meaning` reads it, so that the factors
    stand in the order of the codes it answers. None for a set that is no
    product, and for a name whose chain of definitions returns to it."""
    if isinstance(term, T.Space):
        return _coordinates(term.set, text, active)
    if isinstance(term, T.Named):
        if (
            term.name in text.categories
            or term.name in active
            or term.name not in text.definitions
        ):
            return None
        return _coordinates(text.definitions[term.name], text, active + (term.name,))
    if isinstance(term, T.Product):
        return term.factors, None
    if isinstance(term, T.Comprehension) and term.base is not None:
        found = _coordinates(term.base, text, active)
        return None if found is None else (found[0], term)
    return None


def _codes_in_words(codes):
    """The category codes of a set, in words: none, the map
    `category_codes.describe` writes, or the coordinates of a product that
    have codes."""
    if codes is None:
        return "has no category codes"
    if isinstance(codes, category_codes.CodedMeaning):
        return f"has the category codes {codes.description}"
    coded = [str(k) for k, factor in enumerate(codes, 1) if factor is not None]
    return (
        f"is a product of {len(codes)} coordinates with category codes at coordinate"
        f"{'s' if len(coded) > 1 else ''} {', '.join(coded)}"
    )


def _status(decided):
    return COMPATIBLE if decided else (INCOMPATIBLE if decided is False else NOT_ESTABLISHED)


def _verb(decided):
    if decided:
        return "lies in"
    if decided is False:
        return "does not lie in"
    return "is of a form the package does not compare against"


# --- the inferred pairs selected ---


def _inferred(groups, authored, types):
    """The inferred pairs selected among the candidate groups, and the
    rejections: a candidate pair is selected where its compatibility is
    established, it is the one candidate of its arrival use the package
    does not exclude, its continuation use is the one such candidate of one
    arrival use alone, and its two stages lie in no one strongly connected
    component of the graph of the authored and the selected pairs within
    its period, where every pair is on a cycle; otherwise it is rejected
    with the reason, and no tie is broken. A candidate the package does not
    decide competes as a compatible one does, since at a value it may be
    compatible; an incompatible one is excluded."""
    offers, rejected = {}, []
    for group in groups:
        for candidate in group.candidates:
            for writing, reading in candidate.pairs:
                pair = types.checked(Pair(writing, reading, INFERRED, f"periods[{reading.h}]"))
                if pair.compatibility == INCOMPATIBLE:
                    rejected.append(
                        Rejection(writing, reading, "candidate-incompatible", pair.reason)
                    )
                else:
                    offers.setdefault(reading, []).append(pair)
    singles = {}
    for reading, found in offers.items():
        if len(found) == 1:
            singles[reading] = found[0]
            continue
        rejected.extend(
            Rejection(
                pair.writing,
                pair.reading,
                "inference-disputed",
                f"{reading} has {len(found)} candidates the package does not exclude, "
                f"{_candidates_named(found)}; no pair is selected among them",
            )
            for pair in found
        )
    by_writing = {}
    for pair in singles.values():
        by_writing.setdefault(pair.writing, []).append(pair)
    kept = []
    for writing, found in by_writing.items():
        if len(found) == 1:
            pair = found[0]
            if pair.compatibility == COMPATIBLE:
                kept.append(pair)
            else:
                rejected.append(
                    Rejection(pair.writing, pair.reading, "candidate-not-established", pair.reason)
                )
            continue
        rejected.extend(
            Rejection(
                pair.writing,
                pair.reading,
                "inference-disputed",
                f"{writing} is the one candidate of {len(found)} arrival fields, "
                f"{', '.join(str(pair.reading) for pair in found)}; a continuation field "
                "joins one arrival field, and no pair is selected among them",
            )
            for pair in found
        )
    # a selected pair whose two stages lie in one strongly connected
    # component of the graph of the authored and the selected pairs is on a
    # cycle, and every such pair is withdrawn, whatever the order the pairs
    # were read in, since no direction among them is chosen; what remains
    # has no cycle through an inferred pair
    component_of = {
        node: component
        for component in _components(_edges(authored + kept))
        if len(component) > 1
        for node in component
    }
    withdrawn = [
        pair
        for pair in kept
        if component_of.get((pair.writing.h, pair.writing.key)) is not None
        and component_of[pair.writing.h, pair.writing.key]
        is component_of.get((pair.reading.h, pair.reading.key))
    ]
    kept = [pair for pair in kept if pair not in withdrawn]
    for pair in withdrawn:
        stages = ", ".join(
            sorted(node[1] for node in component_of[pair.writing.h, pair.writing.key])
        )
        rejected.append(
            Rejection(
                pair.writing,
                pair.reading,
                "inference-cycle",
                f"{pair.writing} → {pair.reading} lies on a cycle among the stages {stages} of "
                f"periods[{pair.reading.h}]; no direction is chosen among the inferred pairs "
                "of a cycle",
            )
        )
    return kept, rejected


def _candidates_named(pairs):
    """The candidates of a disputed use in words, an undecided one with the
    comparison the package could not make."""
    return ", ".join(
        str(pair.writing)
        + ("" if pair.compatibility == COMPATIBLE else f" (not established: {pair.reason})")
        for pair in pairs
    )


def _components(edges):
    """The strongly connected components of the graph `edges`, each a
    frozenset of positions, by a depth-first walk that keeps its own stack
    (Tarjan's walk); a position with no edge is a component of its own."""
    index, low, on_stack, stack, found, counter = {}, {}, set(), [], [], 0
    nodes = list(edges) + [target for source in edges for target in edges[source]]
    for root in dict.fromkeys(nodes):
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        frames = [(root, iter(edges.get(root, {})))]
        while frames:
            node, targets = frames[-1]
            advanced = False
            for target in targets:
                if target not in index:
                    index[target] = low[target] = counter
                    counter += 1
                    stack.append(target)
                    on_stack.add(target)
                    frames.append((target, iter(edges.get(target, {}))))
                    advanced = True
                    break
                if target in on_stack:
                    low[node] = min(low[node], index[target])
            if advanced:
                continue
            frames.pop()
            if frames:
                parent = frames[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = set()
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.add(member)
                    if member == node:
                        break
                found.append(frozenset(component))
    return found


# --- the routes certified ---


def _routes(selected, types, value_pairs, diagnostics):
    """One route per source, branch and destination in state-pair order."""
    grouped, into, from_source = {}, {}, {}
    for pair in selected:
        source, destination = (
            (pair.writing.h, pair.writing.key),
            (pair.reading.h, pair.reading.key),
        )
        grouped.setdefault((source, pair.writing.branch, destination), []).append(pair)
        into.setdefault(destination, []).append(pair)
    for source, branch, destination in grouped:
        from_source.setdefault(source, []).append((branch, destination))

    explicit = {}
    for use, pair in value_pairs.items():
        source = (use.h, use.key)
        explicit.setdefault(source, {})[use.field] = pair
        if pair is None:
            continue
        destination = (pair.reading.h, pair.reading.key)
        if not any(
            target == destination and (use.branch is None or branch == use.branch)
            for branch, target in from_source.get(source, ())
        ):
            diagnostics.append(Diagnostic(
                "route-not-established", pair.address,
                f"the value pair {use} → {pair.reading} has no state route between "
                "those stage occurrences for that field",
                (pair,), _sources((pair,)),
            ))

    assigned = {
        source: _constant_suppliers(source, routes, explicit.get(source, {}), types)
        for source, routes in from_source.items()
    }
    return [
        _route(
            source, branch, destination, found, into[destination], types,
            explicit.get(source, {}), *assigned[source],
        )
        for (source, branch, destination), found in grouped.items()
    ]


def _constant_suppliers(source, routes, explicit, types):
    """The supplier of each constant whose name no selection tuple places."""
    text = types.text(source)
    if not text.branch_fields:
        return {}, ()
    reached = tuple(dict.fromkeys(destination for _, destination in routes))
    outside = [
        sort for sort in text.required
        if sort.constant and sort.identity.field not in text.value_branches
    ]
    found, ambiguous, unmatched = {}, {}, []
    for sort in outside:
        name = sort.identity.field
        if name in explicit:
            pair = explicit[name]
            target = (pair.reading.h, pair.reading.key) if pair is not None else None
            candidates = (target,) if target in reached else ()
        elif len(reached) == 1:
            candidates = reached
        else:
            candidates = tuple(
                target for target in reached
                if name not in _explicit_names(explicit, target).values()
                and any(other.identity.field == name and other.role == sort.role
                        for other in types.text(target).supplied)
            )
            if not candidates:
                unmatched.append(sort)
                continue
        if len(candidates) == 1:
            found[name] = candidates[0]
        else:
            ambiguous[name] = candidates

    remaining = {}
    for sort in unmatched:
        name = sort.identity.field
        candidates = tuple(
            target for target in reached
            if all(
                _sole_branch_supplier(text, branch, sort, types.text(target), explicit, target, found)
                for branch, destination in routes
                if destination == target
            )
        )
        if len(candidates) == 1:
            remaining[name] = candidates[0]
        else:
            ambiguous[name] = candidates
    found.update(remaining)
    missing = tuple(
        f"{sort.identity} has no unique supplier among "
        f"{', '.join(_at(target) for target in ambiguous[sort.identity.field] or reached)}. "
        f"Write an explicit connector pair for {sort.identity.field}"
        for sort in outside
        if sort.identity.field in ambiguous
    )
    return found, missing


def _sole_branch_supplier(text, branch, constant, supplier, explicit, destination, assigned):
    """Whether one field remains available for a constant at this supplier."""
    if constant.identity.field in text.kept:
        return False
    of_role = [
        sort for sort in text.required
        if sort.role == constant.role
        and (text.value_branches.get(sort.identity.field) == branch
             or assigned.get(sort.identity.field) == destination)
    ]
    supplied = [sort for sort in supplier.supplied if sort.role == constant.role]
    matched, refused = _paired(of_role, supplied, text.kept, _explicit_names(explicit, destination))
    return not refused and len(matched) == len(of_role) and len(supplied) - len(matched) == 1


def _explicit_names(explicit, destination):
    """Each expressly named value on the destination of this route."""
    return {
        name: pair.reading.field
        if pair is not None and (pair.reading.h, pair.reading.key) == destination else None
        for name, pair in explicit.items()
    }


def _route(source, branch, destination, found, into, types, explicit, suppliers, missing_values):
    """The route of the pairs `found` from `source` on `branch` into
    `destination` certified or not: the complete ordered state tuple, the
    compatibility of the pairs, the joint law of the branch and the
    backward components, each failure an obligation."""
    text_s, text_d = types.text(source), types.text(destination)
    source_fields = (
        text_s.branch_fields.get(branch, ()) if branch is not None else text_s.writing_fields
    )
    destination_fields = text_d.reading_fields
    obligations = list(missing_values)
    by_reading = {}
    for pair in found:
        by_reading.setdefault(pair.reading.field, []).append(pair)
    missing = [field for field in destination_fields if field not in by_reading]
    doubled = [field for field, pairs in by_reading.items() if len(pairs) > 1]
    written = {pair.writing.field for pair in found}
    unmapped = [field for field in source_fields if field not in written]
    for field in missing:
        obligations.append(_missing(field, source, branch, destination, into))
    for field in doubled:
        obligations.append(
            f"the arrival coordinate {field} of {_at(destination)} is supplied twice by "
            f"{_at(source, branch)}, by "
            + ", ".join(pair.writing.field for pair in by_reading[field])
        )
    for field in unmapped:
        obligations.append(
            f"the continuation coordinate {field} of {_at(source, branch)} is mapped to no "
            f"arrival coordinate of {_at(destination)}, so the pairs give no coordinate "
            "permutation of the complete state tuple"
        )
    complete = not missing and not doubled and not unmapped
    ordered = (
        tuple(by_reading[field][0] for field in destination_fields) if complete else tuple(found)
    )
    permutation = (
        tuple(source_fields.index(pair.writing.field) for pair in ordered) if complete else ()
    )
    inverse = tuple(permutation.index(j) for j in range(len(permutation))) if complete else ()
    compatibility = _together(pair.compatibility for pair in found)
    for pair in found:
        if pair.compatibility != COMPATIBLE:
            obligations.append(
                f"{pair.writing} → {pair.reading} is {pair.compatibility}: {pair.reason}"
            )
    law = None
    if text_s.forward_refusal is not None:
        obligations.append(
            f"the forward builders graph of {_at(source)} is not constructed, so no joint law "
            f"on {_tuple(source_fields)} is written: {text_s.forward_refusal}"
        )
    else:
        held = text_s.laws.get(branch)
        if held is not None and held[1] == tuple(source_fields):
            law = held[0]
        else:
            obligations.append(
                f"{_at(source, branch)} writes no joint law on its continuation state "
                f"{_tuple(source_fields)}"
                + (
                    f"; its forward builders graph writes {held[0]} on {_tuple(held[1])}"
                    if held is not None
                    else "; separate marginals or support restrictions supply none "
                    "on those coordinates"
                )
            )
    components, backward = _backward(
        source,
        branch,
        destination,
        ordered if complete else found,
        types,
        explicit,
        suppliers,
    )
    if missing_values:
        backward = _together((backward, NOT_ESTABLISHED))
    for component in components:
        if component.status != COMPATIBLE:
            obligations.append(
                f"the backward component {component.required} is {component.status}: "
                f"{component.reason}"
            )
    status = (
        CERTIFIED
        if complete and compatibility == COMPATIBLE and law is not None
        and backward == COMPATIBLE and not missing_values
        else UNCERTIFIED
    )
    basis = tuple(
        dict.fromkeys(
            [entry for pair in found for entry in pair.basis]
            + [entry for component in components for entry in component.basis]
        )
    )
    return Route(
        source=source,
        branch=branch,
        destination=destination,
        source_fields=tuple(source_fields),
        destination_fields=tuple(destination_fields),
        pairs=ordered,
        permutation=permutation,
        inverse=inverse,
        state="complete" if complete else "incomplete",
        compatibility=compatibility,
        law=law,
        components=tuple(components),
        backward=backward,
        status=status,
        obligations=tuple(obligations),
        basis=basis,
    )


def _missing(field, source, branch, destination, into):
    """The obligation of an arrival coordinate no pair of the route
    supplies: who supplies it instead, another branch of the same source,
    which supplies no jointly available state with this one, or another
    stage, or nobody."""
    others = [pair for pair in into if pair.reading.field == field]
    if not others:
        return f"no selected pair supplies the arrival coordinate {field} of {_at(destination)}"
    said = []
    for pair in others:
        other = (pair.writing.h, pair.writing.key)
        if other == source and pair.writing.branch != branch:
            said.append(
                f"{field} takes {pair.writing.field} of the branch {pair.writing.branch} of the "
                f"same stage; one coordinate from each of the mutually exclusive branches "
                f"{branch} and {pair.writing.branch} supplies no jointly available state"
            )
        else:
            said.append(f"{field} takes {pair.writing} of another stage")
    return (
        f"the route {_at(source, branch)} → {_at(destination)} supplies no arrival coordinate "
        f"{field}: " + "; ".join(said)
    )


def _backward(source, branch, destination, found, types, explicit, suppliers):
    """Pair the backward fields each route requires and compare their sorts."""
    text_s, text_d = types.text(source), types.text(destination)
    if text_s.backward_refusal is not None or text_d.backward_refusal is not None:
        at, reason = (
            (source, text_s.backward_refusal)
            if text_s.backward_refusal is not None
            else (destination, text_d.backward_refusal)
        )
        component = Component(
            f"the backward builders graph of {_at(at)}",
            None,
            "",
            NOT_ESTABLISHED,
            f"the graph is not constructed: {reason}",
        )
        return (component,), NOT_ESTABLISHED
    required = [
        sort for sort in text_s.required
        if branch is None
        or text_s.value_branches.get(sort.identity.field) == branch
        or suppliers.get(sort.identity.field) == destination
    ]
    explicit_names = _explicit_names(explicit, destination)
    components = []
    for role in dict.fromkeys(sort.role for sort in required):
        of_role = [sort for sort in required if sort.role == role]
        supplied = [sort for sort in text_d.supplied if sort.role == role]
        paired, refused = _paired(of_role, supplied, text_s.kept, explicit_names)
        taken = {other.identity.field for other, _ in paired.values()}
        for sort in of_role:
            name = str(sort.identity)
            if sort.identity.field in refused:
                components.append(
                    Component(name, None, role, INCOMPATIBLE, refused[sort.identity.field])
                )
                continue
            other, rule = paired.get(sort.identity.field, (None, ""))
            if other is not None:
                status, reason, basis = _result_within(
                    types, source, destination, sort, other, found
                )
                components.append(
                    Component(name, str(other.identity), role, status, reason, basis, rule)
                )
                continue
            if not supplied:
                components.append(
                    Component(
                        name,
                        None,
                        role,
                        INCOMPATIBLE,
                        f"{_at(destination)} supplies no {role} at its entry perch where "
                        f"{name} requires one",
                    )
                )
                continue
            free = [other for other in supplied if other.identity.field not in taken]
            if not free:
                components.append(
                    Component(
                        name,
                        None,
                        role,
                        INCOMPATIBLE,
                        f"every {role} {_at(destination)} supplies answers another requirement "
                        f"of {_at(source, branch)}, and none is left for {name}",
                    )
                )
                continue
            answers = [
                _result_within(
                    types, source, destination, sort, other, found
                )
                for other in free
            ]
            names = ", ".join(str(other.identity) for other in free)
            if all(answer[0] == INCOMPATIBLE for answer in answers):
                components.append(
                    Component(
                        name,
                        None,
                        role,
                        INCOMPATIBLE,
                        f"no {role} {_at(destination)} supplies lies in the set {name} "
                        f"requires: " + "; ".join(answer[1] for answer in answers),
                        tuple(dict.fromkeys(entry for answer in answers for entry in answer[2])),
                    )
                )
                continue
            why = (
                "a kept field needs its own name or an explicit connector pair;"
                if sort.identity.field in text_s.kept
                else "no explicit pair or unique remaining name tells"
            )
            components.append(
                Component(
                    name,
                    None,
                    role,
                    NOT_ESTABLISHED,
                    f"{why} which of {names} answers {name}, and the package chooses none",
                )
            )
    return tuple(components), _together(component.status for component in components)


def _result_within(types, source, destination, required, supplied, found):
    """Whether the supplied function has permitted coordinates and values."""
    inverse = {pair.reading.field: pair.writing.field for pair in found}
    allowed = {identity.field for identity in required.coordinates}
    for coordinate in supplied.coordinates:
        matched = inverse.get(coordinate.field)
        if matched is None:
            return (
                NOT_ESTABLISHED,
                f"{supplied.identity} reads {coordinate.field}, which has no paired state",
                (),
            )
        if matched not in allowed:
            return (
                INCOMPATIBLE,
                f"{supplied.identity} depends on {coordinate.field}, paired with {matched}, "
                f"which {required.identity} may not read",
                (),
            )
    return _included(
        types,
        destination,
        supplied.domain,
        source,
        required.domain,
        f"the result set of {supplied.identity}",
        f"the result set required of {required.identity}",
    )


def _paired(required, supplied, kept, explicit):
    """The explicit pairs, equal names and finally the sole remaining pair."""
    one_per_role, equal_name = PAIRING_RULES
    paired, refused, taken = {}, {}, set()
    by_name = {other.identity.field: other for other in supplied}
    for sort in required:
        name = sort.identity.field
        if name not in explicit:
            continue
        target = explicit[name]
        if target not in by_name:
            refused[name] = f"no explicit connector pair supplies {sort.identity} on this route"
        elif target in taken:
            refused[name] = f"another required field is already paired with {target}"
        else:
            paired[name] = (by_name[target], EXPLICIT_PAIR)
            taken.add(target)
    for sort in required:
        name = sort.identity.field
        if name not in paired and name not in refused and name in by_name and name not in taken:
            paired[name] = (by_name[name], equal_name)
            taken.add(name)
    remaining = [
        sort for sort in required
        if sort.identity.field not in paired and sort.identity.field not in refused
    ]
    free = [other for other in supplied if other.identity.field not in taken]
    if len(remaining) == len(free) == 1:
        name = remaining[0].identity.field
        if name not in kept:
            paired[name] = (free[0], one_per_role)
    return paired, refused


def _together(statuses):
    """The status of several checks together: incompatible where one is,
    else not established where one is, else compatible."""
    statuses = tuple(statuses)
    if INCOMPATIBLE in statuses:
        return INCOMPATIBLE
    if NOT_ESTABLISHED in statuses:
        return NOT_ESTABLISHED
    return COMPATIBLE


def _route_diagnostic(route, depends_on=None):
    """The diagnostic of a route not certified: its rule the first that
    applies of incomplete, incompatible, no law, not established. A route
    affected by a conflicting authored claim is not established as a
    transport even when its own field comparison succeeded; `depends_on` is
    then the address of the cycle's or the claim's diagnostic."""
    if route.state == "incomplete":
        rule = "route-incomplete"
    elif INCOMPATIBLE in (route.compatibility, route.backward):
        rule = "route-incompatible"
    elif route.law is None:
        rule = "route-no-law"
    else:
        rule = "route-not-established"
    sources = _sources(route.pairs)
    address = sources[0][0] if sources else f"periods[{route.destination[0]}]"
    return Diagnostic(
        rule,
        address,
        f"the route {_at(route.source, route.branch)} → {_at(route.destination)} is not "
        f"certified: " + "; ".join(route.obligations),
        source_entries=sources,
        depends_on=depends_on,
    )


def _at(position, branch=None):
    """A position in words, `periods[0].retire_choice`, with its branch."""
    said = f"periods[{position[0]}].{position[1]}"
    return said if branch is None else f"{said} (branch {branch})"


def _tuple(fields):
    return "(" + ", ".join(fields) + ")"


# --- the selection of a trellis, and its report ---


def held_calibrations(periods, first=0):
    """The calibration each stage occurrence of `periods` holds, by its
    position `(h, key)`, the periods numbered from `first`: the mapping the
    occurrence's `bindings.calibration` holds, as a plain mapping, or None
    for an occurrence that holds none, which no comparison reads a value
    under. This is the effective binding of a specified trellis: each
    occurrence was bound with the one value its period supplies for each
    shared parameter (`period_parameters.period_calibrations`)."""
    found = {}
    for h, period in enumerate(periods, first):
        for key, stage in period["stages"].items():
            held = getattr(getattr(stage, "bindings", None), "calibration", None)
            found[h, key] = None if held is None else dict(held)
    return found


def trellis_selection(trellis):
    """The `Selection` of an elaborated or specified trellis dictionary:
    `select_connections` over its `periods`, its `inter_connectors` and
    the calibration each occurrence holds (`held_calibrations`). A trellis
    whose occurrences are not bound is read symbolically, no comparison
    reading a value. Nothing is stored on the dictionary; a reading that
    takes several answers from one selection passes this one along."""
    periods = trellis["periods"]
    return select_connections(periods, trellis["inter_connectors"], held_calibrations(periods))


def _unjoined_from_selection(selection):
    """Open state fields and authored sources projected from one selection."""
    read, sources = set(), {}
    for pair in selection.pairs:
        read.add((pair.writing.h, pair.writing.key, pair.writing.field))
        between = pair.writing.h != pair.reading.h
        rank = 2 if between else (1 if pair.origin == AUTHORED else 0)
        tail = pair.address.rpartition(".")[2]
        digits = tail.partition("[")[2].partition("]")[0]
        number = int(digits) if pair.origin == AUTHORED and digits.isdigit() else -1
        sources.setdefault((pair.reading.h, pair.reading.key, pair.reading.field), []).append(
            (rank, number, pair.address if pair.origin == AUTHORED else None)
        )
    found = {
        side: sorted(
            (use.h, use.key, use.field)
            for use in selection.uses
            if _side(use.perch) == perch and (use.h, use.key, use.field) not in joined
        )
        for side, perch, joined in (("writing", "cntn", read), ("reading", "arvl", sources))
    }
    found["sources"] = {
        field: tuple(address for _, _, address in sorted(sources[field], key=lambda e: e[:2]))
        for field in sorted(sources)
    }
    return found


class ConnectionReport(NamedTuple):
    """What `connection_report` answers: `pairs`, the selected pairs of the
    positions chosen, each a `Pair` with its two uses, its origin and
    address, its compatibility, reason and basis; `routes`, the `Route` of
    each source branch and destination among those positions, certified or
    not, with its obligations; `diagnostics`, each `Diagnostic` at an entry
    of a chosen period, the authored connectors that resolve to no
    certified pair among them; `bindings`, the digest of the calibration
    each chosen position holds, None where it holds none; `counts`, the
    counts of the whole selection; `selection`, the whole `Selection` the
    report was taken from; `file`, the path of the trellis file the
    trellis's provenance names, or None; `rejected`, the unselected inferred
    candidates touching a chosen position; and `unjoined`, the open state
    fields at chosen positions, separated into internal and possible exterior
    writing and reading ports. `obligations` records the joint support
    condition on the external coordinates of the earliest period.
    `str` prints these records."""

    pairs: tuple
    routes: tuple
    diagnostics: tuple
    bindings: Mapping
    counts: Mapping
    selection: Selection
    file: object
    rejected: tuple = ()
    unjoined: Mapping | None = None
    obligations: tuple = ()

    def __str__(self):
        return "\n".join(report_lines(self))


def connection_report(trellis, *, periods=None, stages=None, selection=None):
    """The `ConnectionReport` of an elaborated or specified trellis
    dictionary: its selection (`trellis_selection`), read from the
    occurrences the trellis holds and the calibration each holds, and
    nothing constructed or bound for it. With `periods`, the indices of
    the periods reported, every period where it is None, and `stages`,
    the stage keys reported, every key where it is None, the pairs and the
    routes with an end at a chosen position and the diagnostics at an entry
    of a chosen period are reported, from the selection of the whole
    trellis, which no restriction changes; an index the trellis does not
    hold, and a key no chosen period holds, are refused under
    `trellis-file-shape`. A pair selected symbolically and a pair whose
    compatibility was read at a value are told apart by the pair's
    `basis`, the `(h, key, digest)` of each binding read, and by
    `bindings`; after a refused recalibration the trellis holds the
    bindings bound before it, and the report names those digests and no
    requested value. With `selection`, reuse the selection of this exact
    trellis version; restrictions change the reported positions alone."""
    if selection is None:
        selection = trellis_selection(trellis)
    chosen = _chosen(trellis, periods, stages)
    held = {h for h, _ in chosen}

    def at(use):
        return (use.h, use.key) in chosen

    pairs = tuple(pair for pair in selection.pairs if at(pair.writing) or at(pair.reading))
    routes = tuple(
        route
        for route in selection.routes
        if route.source in chosen or route.destination in chosen
    )
    diagnostics = tuple(
        diagnostic
        for diagnostic in selection.diagnostics
        if any(h in held for h in _periods_of(diagnostic.address))
    )
    bindings = MappingProxyType(
        {position: selection.bindings.get(position) for position in sorted(chosen)}
    )
    rejected = tuple(
        candidate
        for candidate in selection.rejected
        if at(candidate.writing) or at(candidate.reading)
    )
    open_fields = _unjoined_from_selection(selection)
    last = len(trellis["periods"]) - 1
    open_reading = set(open_fields["reading"])
    external = tuple(
        use for use in selection.uses
        if use.h == last and _side(use.perch) == READING
        and (use.h, use.key, use.field) in open_reading
    )
    obligations = _initial_law(external) if any(at(use) for use in external) else ()
    unjoined = MappingProxyType(
        {
            scope: MappingProxyType(
                {
                    side: tuple(
                        field
                        for field in open_fields[side]
                        if field[:2] in chosen
                        and (
                            (field[0] == (0 if side == "writing" else last))
                            == (scope == "exterior")
                        )
                    )
                    for side in ("writing", "reading")
                }
            )
            for scope in ("internal", "exterior")
        }
    )
    provenance = trellis.get("provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    file = (
        provenance.get("trellis", {}).get("path")
        if isinstance(provenance.get("trellis"), Mapping)
        else None
    )
    return ConnectionReport(
        pairs,
        routes,
        diagnostics,
        bindings,
        selection.counts,
        selection,
        file,
        rejected,
        unjoined,
        obligations,
    )


def _initial_law(external):
    """The joint support condition on the external coordinates of the earliest period."""
    identities = tuple(
        Identity("field", stage=f"periods[{use.h}].{use.key}", perch=use.perch, field=use.field)
        for use in external
    )
    fields = ", ".join(str(use) for use in external)
    return (Condition(
        "initial-law-supported",
        identities,
        status="required",
        explanation=(
            f"The joint initial law of ({fields}) must give mass one "
            "to the first chronological period's admissible arrival set."
        ),
    ),)


def _chosen(trellis, periods, stages):
    """The positions `(h, key)` a report covers: those of the periods
    `periods` lists, every period where it is None, whose key `stages`
    lists, every key where it is None; an index the trellis does not hold,
    a key no chosen period holds and a choice of no position are refused
    under `trellis-file-shape`."""
    held = trellis["periods"]
    indices = list(range(len(held))) if periods is None else list(periods)
    for h in indices:
        if isinstance(h, bool) or not isinstance(h, int) or not 0 <= h < len(held):
            raise FactoryError(
                f"the trellis holds {len(held)} periods, and periods[{h!r}] is none of them",
                rule="trellis-file-shape",
                address="periods",
                written=repr(periods),
                write=f"indices between 0 and {len(held) - 1}, or no `periods` for every period",
            )
    keys = None if stages is None else list(dict.fromkeys(stages))
    present = sorted({key for h in indices for key in held[h]["stages"]})
    if keys is not None:
        missing = [key for key in keys if key not in present]
        if missing:
            raise FactoryError(
                f"the periods chosen hold no stage {missing[0]!r}; they hold {', '.join(present)}",
                rule="trellis-file-shape",
                address="periods",
                written=", ".join(keys),
                write=f"stage keys among {', '.join(present)}",
            )
    chosen = {
        (h, key)
        for h in dict.fromkeys(indices)
        for key in held[h]["stages"]
        if keys is None or key in keys
    }
    if not chosen:
        raise FactoryError(
            "the choice holds no stage occurrence of the trellis",
            rule="trellis-file-shape",
            address="periods",
            written=repr({"periods": None if periods is None else list(periods), "stages": keys}),
            write="indices of periods the trellis holds, or no `periods` for every period",
        )
    return chosen


def _periods_of(address):
    """The indices of the periods an entry's address concerns:
    `periods[h]...` the period `h`, `inter_connectors[h]` the periods `h`
    and `h + 1`."""
    head, _, rest = address.partition("[")
    number = rest.partition("]")[0]
    if not number.isdigit():
        return ()
    h = int(number)
    return (h, h + 1) if head == "inter_connectors" else (h,)


def report_lines(report):
    """The lines `str` prints of a `ConnectionReport`: a heading with the
    counts; then each pair, its origin and address, its compatibility with
    its reason and the bindings it read, `no binding read` where it read
    none; then each route with its status and its obligations; each
    diagnostic with its source entries; each rejected inferred candidate;
    and each unjoined state field."""
    counts = report.counts
    lines = [
        f"connection report of {report.file or 'the trellis'}: {len(report.pairs)} pairs, "
        f"{len(report.routes)} routes, {len(report.diagnostics)} diagnostics, "
        f"{len(report.rejected)} rejected inferred candidates "
        f"(the whole selection: {counts['pairs']} pairs, {counts['inferred']} inferred, "
        f"{counts['routes']} routes, {counts['certified']} certified, "
        f"{counts['diagnostics']} diagnostics)"
    ]
    for pair in report.pairs:
        basis = (
            ", ".join(f"periods[{h}].{key}: {digest}" for h, key, digest in pair.basis)
            or "none (no binding read)"
        )
        lines.append(
            f"pair {pair.writing} → {pair.reading}: {pair.origin} ({pair.address}); "
            f"{pair.compatibility}: {pair.reason}; basis {basis}"
        )
    for route in report.routes:
        said = (
            f"route {_at(route.source, route.branch)} → {_at(route.destination)}: {route.status}"
            f", {_tuple(route.source_fields)} → {_tuple(route.destination_fields)}"
        )
        if route.obligations:
            said += "; " + "; ".join(route.obligations)
        lines.append(said)
    for diagnostic in report.diagnostics:
        lines.append(f"diagnostic {diagnostic.rule} at {diagnostic.address}: {diagnostic.message}")
        for address, source, target in diagnostic.source_entries:
            said = f"source {address}"
            if source is not None:
                said += f": {source!r} → {target!r}"
            lines.append(said)
    for candidate in report.rejected:
        lines.append(
            f"rejected inference {candidate.writing} → {candidate.reading}: "
            f"{candidate.rule}: {candidate.message}"
        )
    for scope, sides in (report.unjoined or {}).items():
        for side, fields in sides.items():
            for h, key, field in fields:
                lines.append(f"unjoined {scope} {side} state field: periods[{h}].{key}.{field}")
    for condition in report.obligations:
        lines.append(f"{condition.status} {condition.condition}: {condition.explanation}")
    return lines
