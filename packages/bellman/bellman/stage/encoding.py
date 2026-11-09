"""The JSON record of one elaborated stage version."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping

from discopy.frobenius import Bubble, Cap, Hypergraph, Spider

from bellman.display.answer_encoding import encode_answer
from bellman.native.hypergraphs import BellmanHypergraph
from bellman.native.identity import Identity, box_identity
from bellman.native.labels import box_label, is_wiring, value_aggregations_of
from bellman.native.provenance import package_version
from bellman.native.records import DEFINITION_KIND_WORDS, Provenance, Refusal
from bellman.native.versions import stored
from bellman.stage.boxes import methods_within, piece_word
from bellman.stage.denotations import denotation_of_definition, denotation_of_graph, denote
from bellman.stage.grains import bound_blocks, graph_of
from bellman.stage.inventory import version_word
from bellman.stage.places import components_by_place
from bellman.stage.stage_answers import descriptions
from bellman.syntax.lower import to_json
from bellman.typing.typed_expressions import obligation_entry

SCHEMA = "https://econ-ark.org/bellman-sym/stage-encoding/2.6"

# each section of the encoding that holds the graphs of one level, with the
# stored record it is written from: the schema's section names, the version's
# attributes `initial` and `_builders`
_GRAPH_SECTIONS = (("initial_diagrams", "initial"), ("builders", "_builders"))


def encoding(stage):
    """The definitions, stored graph hierarchy, bindings, provenance and
    conditions of this version as a fresh JSON-compatible mapping.
    `json.dumps` accepts the answer unchanged. No encoding is stored on the
    stage, and the package provides no decoder.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""
    definitions = []
    for record in stage.definitions.values():
        addresses = record.kind in ("g", "G")
        definitions.append(
            {
                "identity": str(record.identity),
                "kind": DEFINITION_KIND_WORDS[record.kind],
                "coordinates": [[name, to_json(domain)] for name, domain in record.coordinates],
                "equations": [
                    {
                        "address": str(term) if addresses else record.address,
                        "term": None if addresses else to_json(term),
                    }
                    for term in record.equations
                ],
                "tags": list(record.tags),
                "address": record.address,
                "ordinal": record.ordinal,
                "describes": "\n".join(descriptions(record)) or None,
            }
        )
        # the category map of a set marked `!categories`, which no other
        # entry writes
        if record.categories is not None:
            definitions[-1]["categories"] = {
                "identifier": record.categories.identifier,
                "codes": [[code, name] for code, name in record.categories.codes],
            }
    bound = stage.bindings
    graphs = {
        section: {
            direction: _graph_json(stage, _held_graph(stage, held, direction))
            for direction in ("backward", "forward")
        }
        for section, held in _GRAPH_SECTIONS
    }
    table = stored(stage, "definitions")
    derived = {
        "stage": encode_answer(denote(stage)),
        "initial_diagrams": {
            direction: encode_answer(
                denotation_of_graph(stage, level="initial", direction=direction)
            )
            for direction in ("backward", "forward")
        },
        "primitives": {
            direction: encode_answer(
                denotation_of_graph(
                    stage, level="builders", direction=direction, grain="primitive"
                )
            )
            for direction in ("backward", "forward")
        },
        "definitions": [
            encode_answer(denotation_of_definition(stage, table[identity])) for identity in table
        ],
        "structural_sources": {
            section: {
                direction: _structural_sources(_held_graph(stage, held, direction))
                for direction in ("backward", "forward")
            }
            for section, held in _GRAPH_SECTIONS
        },
    }
    return StageEncoding(
        package_version=package_version(),
        derived=derived,
        schema=SCHEMA,
        version=version_word(stage),
        name=stage.name,
        metadata=_plain(dict(stage.metadata)),
        definitions=definitions,
        **graphs,
        bindings={
            "calibration": _plain(bound.calibration),
            "methods": {at: _components(held) for at, held in components_by_place(stage).items()}
            or None,
            "settings": _plain(bound.settings),
        },
        provenance=_plain(dict(stage.provenance), without_text=True),
        obligations=[
            {
                "condition": item.condition,
                "entries": [obligation_entry(entry) for entry in item.entries],
                "explanation": item.explanation,
                "status": item.status,
                "evidence": _plain(item.evidence),
            }
            for item in stage.obligations()
        ],
        diagnostics=_plain(_diagnostics_json(stage)),
    )


def _diagnostics_json(stage):
    """The answers of `stage.diagnostics()` as a mapping, each `Diagnostic`
    of `unread_inputs` and `derivative_missing` written as a mapping of its
    fields, so that a reader of the record finds the rule, the address, the
    message and the candidates by name."""
    answers = dict(stage.diagnostics())
    for name in ("unread_inputs", "derivative_missing"):
        if name in answers:
            answers[name] = [dict(item._asdict()) for item in answers[name]]
    return answers


class StageEncoding(dict):
    """One version's JSON-compatible mapping, displayed as indented JSON with
    sorted keys. A second tool can read it directly; it does not rebuild
    a stage.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""

    def __str__(self):
        return json.dumps(self, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)

    __repr__ = __str__


def _graph_json(stage, graph):
    """The encoding of one stored graph: the rule and the message of a
    refused graph; otherwise its inputs, its outputs, every wire with its
    kind, perch, role, domain and coordinates, the wires inside its bubbles
    included, and its boxes other than the wiring."""
    if isinstance(graph, Refusal):
        return {"rule": graph.diagnostic["rule"], "message": graph.reason}
    wires = {}

    def collect(held):
        for wire in held.spider_types:
            for sort in wire.inside:
                wires.setdefault(
                    str(sort.identity),
                    {
                        "identity": str(sort.identity),
                        "kind": sort.kind,
                        "perch": sort.perch,
                        "role": sort.role,
                        "domain": to_json(sort.domain),
                        "coordinates": [str(name) for name in sort.coordinates],
                    },
                )
        for box in held.boxes:
            if isinstance(box, Bubble):
                collect(BellmanHypergraph.from_diagram(box.arg))

    collect(graph)
    valued = value_aggregations_of(graph)
    return {
        "inputs": [str(sort.identity) for sort in graph.dom.inside],
        "outputs": [str(sort.identity) for sort in graph.cod.inside],
        "wires": list(wires.values()),
        "boxes": [_box(stage, box, valued) for box in graph.boxes if not is_wiring(box)],
    }


def _box(stage, box, valued):
    """The encoding of one box: its name, kind, label, inputs and outputs,
    the address of the line a line box represents, the pieces inside a
    bubble, and on a methodized version the methods bound within it;
    `valued` holds the value aggregations of the graph, which the label
    reads."""
    identity = box_identity(box)
    composite = isinstance(box, Bubble)
    kind = (
        {"Block": "block", "Builder": "builder", "SubBuilder": "sub-builder"}[piece_word(box)]
        if composite
        else identity.kind
    )
    answer = {
        "name": box.name,
        "kind": kind,
        "label": box_label(box, valued),
        "in": [str(sort.identity) for sort in box.dom.inside],
        "out": [str(sort.identity) for sort in box.cod.inside],
    }
    definition = stage.definitions.get(identity.address)
    if definition is not None and definition.kind == "line":
        answer["address"] = definition.address
    if composite:
        answer["pieces"] = [
            _box(stage, held, valued) for held in box.arg.boxes if not is_wiring(held)
        ]
    if components_by_place(stage):
        answer["methods"] = [
            {"at": at, **_components(held)} for at, held in methods_within(stage, box).items()
        ]
    return answer


def _components(held):
    """The encoding of the components typed at one place: the method word
    and the grid as terms, each null where not typed, and the handler's
    program."""
    return {
        "method": None if held.method is None else to_json(held.method),
        "grid": None if held.grid is None else to_json(held.grid),
        "handler": held.handler,
    }


def _held_graph(stage, held, direction):
    """The graph a section of the encoding writes for one direction: the
    stored record, or its refusal, and for the builders the operative graph
    `graph_of` answers, which is the stored record where no method block
    opens a builder of the direction (specification 0.6 §7)."""
    record = getattr(stored(stage, held), direction)
    if held == "_builders" and not isinstance(record, Refusal) and bound_blocks(stage):
        return graph_of(stage, "builders", direction)
    return record


def _plain(value, without_text=False):
    """A copy of a retained value in strict JSON: a non-finite float marked,
    and an authored mapping escaped where it holds the reserved key."""
    if isinstance(value, Identity):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return {"$bellman": ["float", str(value)]}
    if isinstance(value, (Mapping, Provenance)):
        return _mapping(
            {
                str(key): _plain(item, without_text)
                for key, item in value.items()
                if not (without_text and key == "text")
            }
        )
    if isinstance(value, (tuple, list)):
        return [_plain(item, without_text) for item in value]
    return value


def _mapping(items):
    """An authored mapping, escaped where it holds the reserved key of the
    scalar tag."""
    if "$bellman" in items:
        return {"$bellman": ["mapping", [[key, value] for key, value in items.items()]]}
    return items


def _structural_sources(graph):
    """The wiring boxes of one stored graph that read no wire, each `Spider`
    or `Cap` by the path of the graph that holds it and the identities of its
    outputs: the graph keys of the document hold no wiring box, and an input
    such a box writes has a producer only here (AMD-SG-029)."""
    if isinstance(graph, Refusal):
        return []
    sources = []

    def collect(part, path):
        diagram = part.to_diagram() if isinstance(part, Hypergraph) else part
        for box in diagram.boxes:
            if not box.dom and box.cod and isinstance(box, (Cap, Spider)):
                sources.append(
                    {
                        "path": list(path),
                        "kind": "Cap" if isinstance(box, Cap) else "Spider",
                        "outputs": [str(sort.identity) for sort in box.cod.inside],
                    }
                )
        economic = [box for box in part.boxes if not is_wiring(box)]
        for index, box in enumerate(economic):
            if isinstance(box, Bubble):
                collect(box.arg, (*path, index))

    collect(graph, ())
    return sources
