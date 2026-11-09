"""The semgraph of a stage or of a trellis as the graph Google's Model
Explorer draws.

`to_model_explorer(stage)` answers the viewer's `GraphCollection`: four
graphs, first the two initial diagrams, `backward initial diagram` and
`forward initial diagram`, the authored surface, and then `backward` and
`forward`, the builders graphs at the primitive grain. An initial diagram is
drawn as the field diagram of the calculus is drawn (`docs/bellman-calculus/
04-fields, functions and types.md` §2; AAS, 1 October 2026: the nodes of a
field diagram are the fields): each perch that holds a field of the diagram
is a layer named by the perch's word, `arvl`, `dcsn` or `cntn`, every field
wire is a node inside the layer of its perch, named by the wire's identity,
labeled as the drawing labels the wire, `V≻`, `m_d`, and holding the field's
kind, perch, role, declared set and the line of the header that first lists
it (`field_attributes`), a shock, which belongs to no perch, standing outside
the layers; and every block is a node outside the layers, labeled by its
block id, with its header, its statements and its lines as its attributes
(`block_attributes`), an edge from each field it reads and an edge to each
field it writes. The layers and the root are laid out left to right, so that
the forward diagram reads arrival, decision, continuation and the backward
one continuation, decision, arrival, and the fields of one perch stand one
under another. The diagram has no nodes `Inputs` and `Outputs`: a field no
block writes is one the diagram takes, and a field no block reads one it
gives (`_initial_graph`). The diagram carries no method. In a builders graph
every primitive operator is a node whose namespace names the builder and
the sub-builder that hold it, so that the viewer shows each builder as a
layer that opens to its sub-builders and then to its primitives. Every wire
is an edge from the box that writes it to each box that reads it, its port
id the wire's identity string at both ends, and the two ends carry the
wire's label, its perch where it stands at one, its role where it has one,
and its type, or for a field its declared set (`_port_item`); an attribute
that would hold nothing is not written. A builders graph's own inputs and
outputs are the ports of two nodes of this module, `Inputs` and `Outputs`,
whose attributes `inputs` and `outputs` print the graph's signature as its
handle prints it, the wires as one object.

The edges that cross a layer's border are the wires its primitives read and
write. A wire of a builder's signature that none of its primitives reads is
therefore no edge of its layer: the policy builder of `cons.bl` takes 𝑉≻ and
𝑑𝑉≻, and its primitives read 𝑑𝑉≻ alone. The signature itself, as the
builder's `signature()` prints it, stands in the layer's attributes `inputs`
and `outputs`, which the side panel shows when the layer is selected. The
layer of a builder, and not of a sub-builder, also holds what its
primitives share (`_builder_attributes`): `where`, the rows of the `Where`
section of the builder's card, the local abbreviations of their rules; on a
policy builder's layer `feasible set`, the definition of each feasible set
its policy names, `Γ(x : ℝ₊₊) := (0, x]`; `parameter`, each parameter the
primitives read, as `stage.par` prints it with its declared set and, on a
calibrated version, its value; and `setting`, every setting the version
binds, as `stage.settings` prints it, whether or not a method names it.

Selecting a primitive shows the rows of its card and its kernel in the side
panel, each attribute one line, in the order an economist reads them
(`box_attributes`): `kind`; `rule`, the rules of the card's `Rule` section,
each on one line with the region it holds on after it (`cards.rule_rows`),
where an evaluation, whose kernel is the identity, lists only its typing
rows and no rule of the box before it; `kernel`, the lines the box's
`kernel()` prints, the function from which the card's `Where` and `Rule`
sections are written; the method bound within the box; and `lines`, the
file and the numbers of the lines the card's `Source` section quotes,
`cons.bl 22–23` (`cards.source_lines`). A kernel of one line and a section
of one row are one attribute named by its word, `rule`, and several lines
or rows are numbered from one, `rule 1`, `rule 2` (`_numbered`). The rules
and the lines are read from the card's record by the card module, so no
printed card is read back. The rows of the card's `Conditions` are not
shown (AAS, 30 September 2026), and those of its `Where` stand on the
builder's layer. A primitive within which a method is bound also shows
`method`, its tag, `handler`, `option`, the rows of the card's `Options`
section, and `setting`, each setting those options name as the version's
settings print it, numbered in the same way. A method bound at a builder,
and at none of its primitives, stands in the attributes of the builder's
layer. The node's rows, its label and the layer read a piece's method in
one way (`_bound_method`).

`perch_overlays(stage)` gives the three edge overlays, arrival, decision and
continuation, each in its perch's color (`PERCH_COLORS`) and each an edge,
with no label, for every edge of the view whose wire lives at its perch.
The graphs do not carry them, so the view opens without them: the viewer
draws an overlay edge as a straight line between the borders of its two
nodes, not along the graph's edge, and neither an overlay nor its edges has
a field that asks for the graph's route (AAS, 30 September 2026). They
stand in the second file of a view, which a reader loads through the
viewer's panel of edge overlays. They are read from the edges of the
collection's graphs, so that no overlay names a node or an edge the view
lacks.

`to_model_explorer(trellis)`, given the dictionary `elaborate_trellis`
answers or one the trellis verbs bound, answers the two builders graphs of
the trellis, and since design pass 14 §7 its two initial diagrams as well
(`_trellis_initial_graph`). Each period is a layer `periods[h]`, the
periods side by side as the trellis drawing places them, its attribute `age`
where the registry gives one; each stage occurrence is a layer
`periods[h]/<key>` inside its period, the stages of a period in their forward
order, holding the occurrence's builders exactly as the stage view does,
every id and every namespace prefixed by the occurrence's address; and each
join of the trellis, a pair of the trellis's one selection of its
connections (`factory.connections`, AMD-COMP-001 §3), is an edge at the
grain of the wire, from the node of one occurrence that writes the wire the
join carries to each node of the other occurrence that reads it, labeled on
the reading port by its attribute `join` with the text of the trellis
drawing, `m_next → m` or `inter_connectors[0] a → k`. The wires a join
carries are those the selection's route between its two occurrences
establishes (`_route_pairs`): forward, the joint law the source's branch
writes on the route's state tuple supplies the destination's arrival
measure; backward, the arrival value and marginal values the destination
supplies answer the continuation value and marginal values the source's
branch requires, each paired as the route's backward component records
it, by the coordinate the two names declare under the route's map, by one
wire of a role on each side, or by equal names where the route's
permutation is the identity (`connections.PAIRING_RULES`), and the reading
port of a backward join names that rule in its attribute `paired by` and,
where the component is not compatible, its status in `compatibility`, so
that a pairing by equal names and an uncertified pair are never silent. No
rule of pairing is the view's own. Each edge of a join carries, under its
attribute `route`, the record of the route that establishes it, read from
the native `Route` (`_route_record`): its branch, its two occurrences, the
two state tuples in the route's order, its pairs with their origin and
address, its status and its law (design pass 10 §6; unit N, Task 6). A
join whose route leaves a wire unpaired, as a crossed pair leaves two
marginal values whose names declare no coordinate, or whose source's
branch writes no joint law on the route's tuple, refuses the graph of its
direction, each such join on a row of the refusing node
(`_unpaired_attributes`). The trellis has no `Inputs` and no `Outputs` of
its own: a wire no join supplies enters the graph at a boundary node of
kind `start`, and a wire no join reads leaves it at one of kind `end`, each
a node at the graph's root labeled by the word of its role and the wire's
label, `starting data μ≺`, `terminal μ`, `terminal condition 𝑉≻()` or
`result 𝑉≺(a, h, z)` (`_boundary_node`, `BOUNDARY_WORDS`; decision N-D7); a
wire a join supplies that no primitive of its occurrence reads ends at the
occurrence's own `Inputs`, a node inside its layer, so that the join is
drawn, and an occurrence's policy ends at its own `Outputs` inside its
layer, so that no edge of a policy crosses the periods.

`to_model_explorer(trellis, periods=…, stages=…)` restricts the view to the
occurrences of the periods and the stage keys given, the periods selected as
`diagram_trellis` selects them (`_selection`); a join that leaves the
occurrences held is no edge, and the wire it carries enters or leaves the
graph at a boundary node of kind `outside` for each occurrence outside the
view that such joins reach, labeled with that occurrence's address, which
its attribute `target` holds; the wire's port names the join in `join` and
those occurrences in `outside` (`_leaving`). `unpaired_joins`
answers the rows `join n` of a refused backward graph as records, each
join's connector and the header line that declares each wire it leaves
unpaired among them, so that a page links them to the files.

`to_model_explorer(trellis, unjoined=True)` adds to the forward graph one
port for each state field of a stage occurrence at its arrival and its
continuation perch: an arrival field among the inputs of its stage
occurrence's own `Inputs`, `periods[h]/<key>/GraphInputs`, and a
continuation field among the outputs of its own `Outputs`,
`periods[h]/<key>/GraphOutputs`, each port named by the field's identity
and carrying no wire, so that a drag in Bellman Workbench can name one
field where the joint measure wire names none (model interface spec 0.4
§3.4; `_with_field_ports`). A field that no join of the whole trellis
reaches (`joins.unjoined_fields`, read before a view is restricted), the
two ends of the trellis among them, is marked `unjoined`; an arrival field
that joins reach counts them in `sources`, since an arrival field takes
several sources; and a continuation field of a branching stage carries its
branch's label in its own, `keep: w_kp≻`, the ports grouped by branch (unit
J's decisions J-D41 to J-D43). The ports are added after the stage views
are read from the cache and are never written into a cached stage view,
and with the keyword off, the default, the view is unchanged.

The view writes no mathematics of its own. The node of a primitive shows
two short lines (`node_label`): the kind of its operator, with the policies
its row is held at, `Pullback at 𝑐`, and the head of the symbol the drawing
shows for the box (`box_symbol`), in which no law and no aggregator is
written out at a policy and a law of motion is named as the box's card
names it, `𝑉≻ ∘ 𝑔≻`, followed by the tag of a method bound within the box,
`𝑉(m_d), 𝑑𝑉(m_d) · !Linear`; the arguments stand in the box's `rule`
rows. A block of an initial diagram shows the drawing's symbol on one line.
A port's label is the wire's label in the drawing (`wire_label`). The
symbol and the port's label are read from what the drawing of the graph
reads (`label_sources`), and a port's type is the type the signature prints
for the wire (`carriers.wire_type`). A shorter form the study of 30
September 2026 proposed, a result wire labeled by the function it carries
at its coordinates, changes labels the drawing shares and waits for AAS's
decision behind the module's switch `SHORT_LABELS`, which defaults to the
recorded form.

The view's colors are the brand's, each a token of `PALETTE`, whose values
are those of `docs/_stylesheets/bellman.css`, and they tell the levels of
the structure apart: navy for every border and every label, white and three
steps of the ice for the fills, ultramarine for what a builder delivers,
and orange for a refusal. A node is white with a navy border and a navy
label (`NODE_STYLE`), `Inputs`, `Outputs` and the nodes of an initial
diagram among them. The node of a primitive operator that writes a wire
read outside its builder's layer, by another builder, by `Outputs` or by a
join of a trellis, has an ultramarine border (`OUTPUT_STYLE`, `_style`),
since the viewer colors no edge and no port. The one node of a refused
graph has an orange border (`REFUSAL_STYLE`). The border of a node under
the pointer is ultramarine, and navy for a node in the output style, whose
border is ultramarine already. A layer's fill names its level
(`LAYER_COLORS`), each layer with a navy border and a navy label: a period
of a trellis is white, a stage occurrence stands on the first step of the
ice, a builder on the second and a sub-builder on the third; the perch
layers of an initial diagram stand on the first. The kind of a box's
operator stands on the first line of its label and has no color. The color
of a node's label and the colors of a layer are fields the viewer's page
reads and its Python classes do not declare, so the view writes a node's
style and a layer's configuration as records of this module, `_NodeStyle`
and `_LayerConfig`, whose fields are the page's.

`write_model_explorer(stage, folder)` writes a view to two JSON files named
by the collection's label, each in the form the viewer loads: the collection,
which the viewer's JSON adapter reads as a model file; and the three perch
overlays as one `EdgeOverlaysData`, which the viewer's edge-overlay panel
reads from a file. The collection is built once and the overlays are read
from it. Each file holds ASCII alone, every other character written as the
JSON escape of its code point: the viewer's server opens a file without
naming an encoding, so that Python reads it in the system's default
encoding, and ASCII is read alike under any code page.
`layers_to_open`, `node_place` and `wire_counts` read a view back, from the
collection or from the document of its graph file: the layers a page opens,
the occurrence and the block of a node, and the distinct wires of each
builders graph.
`serve(graph_path)` answers the address of a page on the viewer's server
that shows the graph file with chosen layers opened, located on a chosen
layer where one is named. Every view is served from one port, 8080 unless
another is given, since the browser keeps the viewer's settings, the text
renderer among them, for each address and port; a server that already
answers there is used, whichever process started it, and otherwise one is
started in a daemon thread, which the caller waits for only until it
answers, `SERVER_WAIT_SECONDS` and at most one second more.
`explore(stage)` writes the files and opens the view in the default
browser, from a daemon thread as well, a trellis located on its first
period after the terminal one (`LOCATED_PERIOD`).

The viewer is the extra `explore` of the package (`pip install -e
"packages/bellman[explore]"`); this module imports it when first asked and
refuses in one sentence where it is missing. The Graphviz drawing of
`diagram()` remains the recorded picture of a graph; this is its interactive
reading.
"""

from __future__ import annotations

import contextlib
import dataclasses
import functools
import hashlib
import http.client
import json
import os
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from collections import namedtuple
from collections.abc import Mapping
from importlib import import_module, metadata
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote, unquote

from discopy.frobenius import Bubble

from bellman.display.cards import (
    card_body_lines,
    card_sections,
    header_line,
    rule_rows,
    source_lines,
)
from bellman.display.drawing import (
    _operator_kind,
    box_symbol,
    drawn_sorts,
    wire_label,
)
from bellman.display.printed_records import SIDE_WORDS
from bellman.factory.connections import (  # noqa: F401, PAIRING_RULES keeps its name here
    AUTHORED,
    COMPATIBLE,
    PAIRING_RULES,
    trellis_selection,
)
from bellman.factory.joins import forward_order, unjoined_fields
from bellman.factory.trellis import written_bindings
from bellman.factory.trellis_drawings import chosen_periods, join_label, period_age
from bellman.fold.block_lines import blocks_in_file_order, header_of
from bellman.fold.conditions import parameters_named
from bellman.native.identity import SEPARATOR, Identity, box_identity
from bellman.native.labels import (
    function_field,
    function_wire_name,
    is_wiring,
    italic,
    value_aggregations_of,
)
from bellman.native.provenance import package_version, source_file
from bellman.native.records import setting_names
from bellman.native.versions import kept_answer
from bellman.refusals import ConstructionError, FactoryError, NotConstructed
from bellman.stage.boxes import boxes_inside, piece_named, row_of
from bellman.stage.builder_pairs import DIRECTION_WORDS
from bellman.stage.carriers import wire_type
from bellman.stage.denotations import box_signature
from bellman.stage.grains import DIRECTIONS, bound_blocks, graph_of, wire_table
from bellman.stage.kernels import kernel
from bellman.stage.levels import declared_version
from bellman.syntax import terms as T
from bellman.stage.pieces import drawing_arguments
from bellman.stage.places import is_methodized
from bellman.stage.stage_answers import branches, entry_perch, fields
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    PERCH_SIGN,
    PERCHES,
    VALUE,
    WRITTEN_MARK,
)
from bellman.typing import typed_expressions as S

PERCH_NAMES = {"arvl": "arrival", "dcsn": "decision", "cntn": "continuation"}
# the ids of the two initial diagrams of a stage view, the documentation's
# words for them (02-initial.md), by direction; the two builders graphs keep
# the ids `backward` and `forward`, by which the lessons and Bellman Workbench
# name them
INITIAL_IDS = {direction: f"{direction} initial diagram" for direction in ("backward", "forward")}
# the graph a view opens on, the backward builders graph
OPENED_GRAPH = "backward"
# The label form the study of 30 September proposed (line 6) and AAS has
# not yet ruled on, since the drawing shares it (`_short_names`,
# `port_label`): False, the recorded form, a result wire labeled by the
# expression it denotes, `m_d ↦ 𝑢(𝑐(m_d)) + 𝑉≻(𝑔(m_d, 𝑐(m_d)))`; True, the
# proposed form, a result wire that carries a function by the function at
# its coordinates, `𝑉(m_d)`, a candidate set keeping its expression.
SHORT_LABELS = False
# the words by which a reading port of a forward join names what supplies
# its measure: the joint law the route's source branch writes on the route's
# state tuple; a backward join names one of `connections.PAIRING_RULES`,
# imported above under its name
LAW_RULE = "joint law"
# the ids of the two nodes whose ports are a builders graph's own inputs and
# outputs; the viewer has no node of this kind, and these two are this
# module's. An initial diagram has neither: its fields are its nodes.
BOUNDARY_IDS = ("GraphInputs", "GraphOutputs")
# The kinds of the boundary nodes of a trellis graph, which stand at its root
# in place of the trellis's own `Inputs` and `Outputs` (design pass 10 §6;
# unit N, Task 6): `start`, a wire that enters the graph and that no join
# supplies; `end`, a wire that leaves it and that no join reads; and
# `outside`, the wires that the joins between one occurrence of a restricted
# view and one occurrence outside it carry, each wire a port of the node
# (design pass 12 §2). The node's attribute `kind` holds one of them.
BOUNDARY_KINDS = ("start", "end", "outside")
# The word of each role of a `start` and an `end` node by direction, which
# its label writes before the label of its wire, `starting data μ≺` (design
# pass 10 §6; decision N-D7). An `outside` node is labeled by the occurrence
# it reaches.
BOUNDARY_WORDS = {
    "forward": {"start": "starting data", "end": "terminal"},
    "backward": {"start": "terminal condition", "end": "result"},
}
# the key of the attribute under which an edge of a trellis graph carries the
# record of the route that establishes it (`_route_record`)
ROUTE_KEY = "route"
# the endings of the names of a view's two files, which follow the stem:
# the collection and the perch overlays
FILE_ENDINGS = (".graph.json", ".edge-overlays.json")
# the host on which the viewer's server is started: this machine's own name
VIEWER_HOST = "localhost"
# the wait, in seconds, for a server just started to answer
# (the request in progress when the wait ends adds up to one second)
SERVER_WAIT_SECONDS = 5
# the port every view is served from unless another is given, the viewer's
# own default; the browser keeps the viewer's settings for each port
VIEWER_PORT = 8080
# the text the viewer's server answers at its route `check_health`
VIEWER_HEALTH = "model_explorer_ok"
# the ending the viewer writes after a layer's namespace to form its id
LAYER_ID_ENDING = "___group___"
# the namespace of the layer a view of a trellis opens located on: the first
# period after the terminal period, `periods[0]`
LOCATED_PERIOD = "periods[1]"
# the sentence that tells the reader how to see the mathematical labels
SVG_TEXT_SENTENCE = (
    'The mathematical labels are drawn once "Use SVG text renderer" is turned on in the '
    "viewer's settings, behind the gear icon; the browser keeps the setting for this address."
)
# the label of the view of a trellis dictionary that holds no name
TRELLIS_LABEL = "trellis"
# the roles of the wires a join of a trellis carries in each direction
# (the wire table gives a measure the role `measure`)
JOINED_ROLES = {"backward": (VALUE,), "forward": ("measure",)}


def _imported(names):
    """The modules of the viewer and its dependencies named, imported by name
    when first asked, so that the package imports without them and no module
    of the package imports inside a function; refused in one sentence where
    one of them is missing."""
    try:
        return tuple(import_module(name) for name in names)
    except ImportError as missing:
        raise ImportError(
            "The interactive view needs Google's Model Explorer, the extra `explore` of the "
            'package: pip install -e "packages/bellman[explore]" (or pip install '
            "ai-edge-model-explorer)."
        ) from missing


def _viewer():
    """The viewer's module of data classes, `graph_builder` (`_imported`)."""
    (graph_builder,) = _imported(("model_explorer.graph_builder",))
    return graph_builder


def _viewer_server():
    """The viewer's two modules that start its server and write the address
    of a page, `apis` and `config` (`_imported`)."""
    return _imported(("model_explorer.apis", "model_explorer.config"))


# --- the colors ---

# The brand's colors, each under the name of the custom property by which
# `docs/_stylesheets/bellman.css` defines it and with the value the
# stylesheet gives it there; a test reads the stylesheet. Every color the
# view writes, in its nodes, its layers and its overlays, is one of these.
# The slate is written by no view: the display of a view in the lessons
# (`tutorials/checkout.py`) reads it, with the navy, the ice, the
# ultramarine and the white.
PALETTE = {
    "--bf-face": "#FFFFFF",
    "--bl-navy": "#172A52",
    "--bl-slate": "#4B5A7A",
    "--bl-ultramarine": "#214EDA",
    "--bl-ice": "#EDF7FC",
    "--bl-ice-2": "#C5E5F1",
    "--bl-ice-3": "#91BED7",
    "--bf-arvl": "#172A52",
    "--bf-accent-line": "#C45C1D",
    "--bf-cntn-line": "#214EDA",
}


@dataclasses.dataclass(frozen=True)
class _NodeStyle:
    """The style of a node as the viewer's page reads it: the three fields
    of the viewer's `GraphNodeStyle` and `textColor`, the color of the
    node's label, which the page reads (its `types.ts`) and that class does
    not declare. The page reads a style on the nodes of operators alone,
    `Inputs` and `Outputs` among them, and on no layer."""

    backgroundColor: str
    borderColor: str
    hoveredBorderColor: str
    textColor: str


@dataclasses.dataclass(frozen=True)
class _LayerConfig:
    """The configuration of the layers whose namespace `namespaceRegex`
    matches, as the viewer's page reads it: the two fields of the viewer's
    `GroupNodeConfig` and a layer's fill, border and label colors, which the
    page reads (its `types.ts`) and that class does not declare. The page
    lays a layer out by the first configuration whose pattern matches it,
    and takes each color from the first that matches it and sets that
    color; a color left None is not set."""

    namespaceRegex: str
    layoutDirection: int | None = None
    backgroundColor: str | None = None
    borderColor: str | None = None
    textColor: str | None = None


@dataclasses.dataclass
class _RouteEdge:
    """An edge of a trellis graph that a route of the trellis's selection
    establishes (unit N, Task 6): the three fields of the viewer's
    `IncomingEdge` and `attrs`, the viewer's `KeyValue` pairs, which hold
    the route's record under `ROUTE_KEY` (`_route_record`). The viewer's
    classes declare no attribute of an edge and its page reads none; Bellman
    Workbench reads this one."""

    sourceNodeId: str
    sourceNodeOutputId: str
    targetNodeInputId: str
    attrs: list


def _node_style(fill, ink, label=None):
    """The style of a node (`_NodeStyle`): its fill, its border in `ink`,
    its label in `label` or else in `ink`, and its border in ultramarine
    while the pointer is over it."""
    return _NodeStyle(
        backgroundColor=fill,
        borderColor=ink,
        hoveredBorderColor=PALETTE["--bl-ultramarine"],
        textColor=label or ink,
    )


# The style of a node, white with a navy border and a navy label and an
# ultramarine border while the pointer is over it: the node of a primitive
# operator whose outputs are read within its builder's layer alone, the
# nodes `Inputs` and `Outputs`, and the fields and blocks of an initial
# diagram.
NODE_STYLE = _node_style(PALETTE["--bf-face"], PALETTE["--bl-navy"])
# The style of the node of a primitive operator that writes a wire read
# outside its builder's layer, by another builder, by `Outputs` or by a join
# of a trellis: white with an ultramarine border and a navy label, so that
# what each builder delivers is seen at a glance. The viewer colors no edge
# and no port, so the border of the box that writes them shows the outputs.
# Its border is navy while the pointer is over it, so that it changes under
# the pointer as every other node does.
OUTPUT_STYLE = _NodeStyle(
    backgroundColor=PALETTE["--bf-face"],
    borderColor=PALETTE["--bl-ultramarine"],
    hoveredBorderColor=PALETTE["--bl-navy"],
    textColor=PALETTE["--bl-navy"],
)
# the style of the one node of a refused graph: a navy label on white, in
# a border of the orange the site gives a warning, in its form for a line
REFUSAL_STYLE = _node_style(
    PALETTE["--bf-face"], PALETTE["--bf-accent-line"], PALETTE["--bl-navy"]
)
# The colors of a layer by its level, (fill, border, label), each with a
# navy border and a navy label: a period of a trellis white, a stage
# occurrence on the first step of the ice, a builder on the second, and a
# sub-builder, with every layer within one, on the third, so that each
# level a reader opens is one step darker. The perch layers of an initial
# diagram, which divide one stage, stand on the stage's step.
LAYER_COLORS = {
    "period": (PALETTE["--bf-face"], PALETTE["--bl-navy"], PALETTE["--bl-navy"]),
    "stage": (PALETTE["--bl-ice"], PALETTE["--bl-navy"], PALETTE["--bl-navy"]),
    "builder": (PALETTE["--bl-ice-2"], PALETTE["--bl-navy"], PALETTE["--bl-navy"]),
    "sub-builder": (PALETTE["--bl-ice-3"], PALETTE["--bl-navy"], PALETTE["--bl-navy"]),
}
# The color of each perch's overlay, the stylesheet's token of the perch in
# the form it takes for a line: arrival `--bf-arvl`, navy; decision
# `--bf-accent-line`, the orange of `--bf-dcsn` darkened for a line; and
# continuation `--bf-cntn-line`, ultramarine. The page draws an overlay's
# labels in its color as well, so each is dark enough to read on white.
PERCH_COLORS = {
    "arvl": PALETTE["--bf-arvl"],
    "dcsn": PALETTE["--bf-accent-line"],
    "cntn": PALETTE["--bf-cntn-line"],
}


# --- the stage view ---


def to_model_explorer(
    stage_or_trellis,
    *,
    periods=None,
    stages=None,
    unjoined=False,
    selection=None,
    initial=False,
    declared=False,
):
    """The `GraphCollection` of a stage version or of a trellis dictionary:
    its two builders graphs at the primitive grain, `backward` and
    `forward`, each primitive a node, and, for a stage version, its two
    initial diagrams before them. The collection of a stage version holds
    four graphs, first its two initial diagrams, `backward initial diagram`
    and `forward initial diagram` (`INITIAL_IDS`, `_initial_graph`), the
    authored surface, each field a node in the layer of its perch and each
    block a node that relates the fields it reads to the fields it writes,
    and then its backward and its forward builders graphs (`_graph`), each
    builder a layer. A direction the construction refused is a graph of one
    node that states the refusal. The collection of a stage version is
    labeled with the stage's name and the bindings the version holds,
    `cons` or `cons calibrated`. A trellis dictionary, a mapping, answers
    the two builders graphs of the trellis and, with `initial`, its two
    initial diagrams after them (`_trellis_initial_graph`; design pass 14
    §7; S-D30), which the page asks for once its Initial view is chosen,
    since those of a long trellis are large (`_trellis_collection`);
    `periods`, indices of its periods, and
    `stages`, keys of its stages, restrict that view to the occurrences
    both select (`_selection`), and a join that leaves them is marked by
    the `outside` node at which its wire then enters or leaves the graph,
    and on that wire's port (`_leaving`, `_boundary_node`). A stage version
    takes no selection, and one given with it is refused with a TypeError.
    With `unjoined`, the forward graph
    of a trellis holds one port for each state field of a stage occurrence
    at its arrival and its continuation perch, on the occurrence's own
    `Inputs` or `Outputs` and carrying no wire, a field that no join of the
    whole trellis reaches marked `unjoined` and an arrival field that joins
    reach counting them in `sources` (model interface spec 0.4 §3.4; unit
    J's decisions J-D41 to J-D43; `_with_field_ports`); a stage version
    given it is refused with a TypeError, as one given a selection is.
    `selection` reuses the connections selected for this exact trellis
    version, including on a restriction-only redraw. With `declared`, a
    stage version answers its declared builders, `stage.declared`, in place
    of its operative builders, `stage.builder` (specification 0.6 §§7 and
    9; decision SE-8): the builders graphs of the version the stage file
    declares, under the stage's own label, the layer of each builder a bound
    method block opens holding the row `method`, the binding as the card's
    `Method` section prints it without its site, `!egm   block
    methods/cons_egm.bl` (`_opened_lines`); for a stage no block opens it
    answers the collection it answers without `declared`. A trellis
    dictionary given `declared` is refused with a TypeError."""
    graph_builder = _viewer()
    if isinstance(stage_or_trellis, Mapping):
        if declared:
            raise TypeError(
                "the declared builders are exported for a stage version; give the stage "
                "version of an occurrence of the trellis"
            )
        return _trellis_collection(
            graph_builder, stage_or_trellis, periods, stages, unjoined, selection, initial
        )
    if initial:
        raise TypeError(
            "a view of a stage version holds its initial diagrams always; `initial` asks "
            "for a trellis's"
        )
    if periods is not None or stages is not None or selection is not None:
        raise TypeError(
            "a view of a stage version selects no periods and no stages; give the "
            "trellis that holds the stage"
        )
    if unjoined:
        raise TypeError(
            "a view of a stage version marks no unjoined field, since which fields no "
            "join reaches is a fact of a trellis; give the trellis that holds the stage"
        )
    stage = stage_or_trellis
    shown = declared_version(stage) if declared else stage
    opened = _opened_lines(stage) if shown is not stage else {}
    return graph_builder.GraphCollection(
        label=_collection_label(stage),
        graphs=[_initial_graph(graph_builder, shown, direction) for direction in DIRECTIONS]
        + [_graph(graph_builder, shown, direction, opened) for direction in DIRECTIONS],
    )


def _opened_lines(stage):
    """The line of each method block bound to `stage`, by the builder it
    opens: the binding as the operative builder's card prints it in its
    `Method` section, without the site at its margin, `!egm   block
    methods/cons_egm.bl` (`card_body_lines` of the record's method clause
    with no address), which the declared builder's layer shows as its row
    `method` (specification 0.6 §9: the declared builders with the bound
    method)."""
    directions = wire_table(stage).direction
    lines = {}
    for block in bound_blocks(stage):
        graph = getattr(stage.builder, DIRECTION_WORDS[directions[block.builder]])
        for clause in graph[block.builder].denote().method:
            if getattr(clause, "block", ""):
                unsited = dataclasses.replace(clause, address=None)
                lines[block.builder] = card_body_lines(unsited)[0]
    return lines


def _collection_label(stage):
    """The label of the collection: the stage's name followed by a word for
    each binding the version holds, `cons` or `cons calibrated`. The version
    is methodized where an operator's signature carries a method component,
    a handler alone leaving it symbolic (`places.is_methodized`, decision
    S7-W7 of specification 0.7)."""
    bound = [
        word
        for word, held in (
            ("calibrated", stage.bindings.calibration is not None),
            ("methodized", is_methodized(stage)),
            ("configured", stage.bindings.settings is not None),
        )
        if held
    ]
    return " ".join([stage.name, *bound])


def _graph(graph_builder, stage, direction, opened=None):
    """One builders graph at the primitive grain as a viewer `Graph`, or the
    graph of one node that states the refusal of a direction the
    construction refused, labeled with the direction and the rule the
    refusal names. The edges that cross a layer's border are the wires its
    primitives read and write, and a layer's attributes hold its builder's
    signature (`_layer_attributes`), whose wires no primitive reads among
    them, and on a builder's layer what its primitives share: the local
    abbreviations of their rules, the feasible sets of a policy, the
    parameters they read and the version's settings. A builder's layer
    stands on the second step of the ice and a sub-builder's on the third
    (`LAYER_COLORS`), and the node of a primitive operator that writes a
    wire read outside its builder's layer has an ultramarine border
    (`_style`). The perch overlays are read from its edges
    (`perch_overlays`) and are not carried in it. `opened` gives, by the
    builder a bound method block opens, the row `method` its layer holds in
    the declared builders graph (`_opened_lines`). An input of such a
    builder that no operation inside it reads is named under `unread` on a
    reading port inside it (`_unread_inputs`)."""
    try:
        hypergraph = graph_of(stage, "builders", direction, grain="primitive")
    except NotConstructed as refusal:
        return _refused_graph(
            graph_builder, direction, _refused_label(direction, refusal), {"refusal": str(refusal)}
        )
    wiring = _wiring(stage, hypergraph)
    holders = _holders(stage, direction)
    unread = _unread_inputs(stage, holders, wiring)
    # the graph's signature, as the builders handle prints it, on its two
    # boundary nodes: the sides the ports give wire by wire, as one object
    sides = _signature_sides(getattr(stage.builder, DIRECTION_WORDS[direction]).signature())
    nodes = _boundary_nodes(
        graph_builder,
        stage,
        hypergraph,
        wiring,
        [
            graph_builder.GraphNode(
                id=str(box_identity(box)),
                label=node_label(stage, direction, wiring.sources, box),
                namespace=_namespace(box, holders),
                attrs=_key_values(graph_builder, box_attributes(stage, direction, box)),
                incomingEdges=_edges(graph_builder, wiring, box.dom.inside),
                outputsMetadata=_ports(graph_builder, stage, wiring, box.cod.inside),
                inputsMetadata=_with_unread(
                    graph_builder,
                    _ports(graph_builder, stage, wiring, box.dom.inside),
                    unread,
                    str(box_identity(box)),
                ),
                style=_style(box, wiring),
            )
            for box in wiring.boxes
        ],
        {"inputs": sides["inputs"]},
        {"outputs": sides["outputs"]},
    )
    # The viewer applies the first configuration whose pattern it finds in
    # a layer's namespace, so the deeper level stands first.
    top_bottom = graph_builder.LayoutDirection.TOP_BOTTOM
    layouts = [
        # a sub-builder, `cntn_to_dcsn/risk_ce`, and every layer within one
        _layer_config("/", top_bottom, LAYER_COLORS["sub-builder"]),
        # a builder, `policy`, and the graph's root, which is no layer
        _layer_config(".*", top_bottom, LAYER_COLORS["builder"]),
    ]
    # the targets of the methods bound within the primitives
    # (a layer shows only the methods bound within it at no primitive)
    held = {
        target for box in wiring.boxes for target in piece_handle(stage, direction, box).methods
    }
    rows = _layer_attributes(stage, direction, holders, held, wiring.boxes)
    for builder, line in (opened or {}).items():
        if builder in rows:
            rows[builder] = {**rows[builder], "method": line}
    return graph_builder.Graph(
        id=direction,
        nodes=nodes,
        groupNodeAttributes=rows,
        groupNodeConfigs=layouts,
    )


def _unread_inputs(stage, holders, wiring):
    """The inputs of each builder a bound method block opens that no
    operation inside it reads, as a block may leave an input of its header
    unread, as the endogenous-grid block leaves `V[>]` (specification 0.6
    §4.1), by the reading port that names them: the port of the first
    operation inside the builder that reads a wire of the same writer, by
    `(node id, port id)`, each input `<writer>::<identity>` and several
    joined by `; `. The graph's layout draws such an input among the wires
    of that port's line, so that the line entering the opened builder is
    the bundle of the wires its header lists (the controller's first ruling
    on design pass 15; SE-19)."""
    opened = {block.builder for block in bound_blocks(stage)}
    found = {}
    for address, holder in holders.items():
        if holder.within is not None or address not in opened:
            continue
        inside = [box for box in wiring.boxes if box_identity(box).block == address]
        read = {ob.identity for box in inside for ob in box.dom.inside}
        for ob in holder.bubble.dom.inside:
            if ob.identity in read:
                continue
            writer = wiring.writers.get(ob.identity)
            port = next(
                (
                    (str(box_identity(box)), str(wire.identity))
                    for box in inside
                    for wire in box.dom.inside
                    if wiring.writers.get(wire.identity) == writer
                ),
                None,
            )
            if port is not None:
                named = f"{writer}::{ob.identity}"
                found[port] = f"{found[port]}; {named}" if port in found else named
    return found


def _with_unread(graph_builder, items, unread, node_id):
    """The metadata items of the reading ports `items` of the node
    `node_id`, each port that `unread` names holding the inputs it names
    under the attribute `unread` (`_unread_inputs`)."""
    for item in items:
        named = unread.get((node_id, item.id))
        if named:
            item.attrs.append(graph_builder.KeyValue(key="unread", value=named))
    return items


def _refused_graph(graph_builder, graph_id, label, attributes):
    """The graph `graph_id` of one node that states why it is refused: the
    node's id is `<graph id>:refused`, its label `label`, and its attributes
    `attributes`, one line each, the refusal's sentence under `refusal` and,
    for a trellis graph whose joins leave wires unpaired, each such join on a
    row of its own (`_unpaired_attributes`)."""
    return graph_builder.Graph(
        id=graph_id,
        nodes=[
            graph_builder.GraphNode(
                id=f"{graph_id}:refused",
                label=label,
                attrs=_key_values(graph_builder, attributes),
                style=REFUSAL_STYLE,
            )
        ],
    )


def _refused_label(direction, refusal, level="builders"):
    """The label of the node that states the refusal of a graph, `backward
    builders graph refused (not-constructed)` or `backward initial diagram
    refused (…)`: the graph's name, by its direction and its level, and the
    rule the refusal names (`ConstructionError.rule`), the word its text
    closes with; the name alone where the refusal names no rule. The whole
    text stands in the node's attribute `refusal`."""
    rule = getattr(refusal, "rule", None)
    name = INITIAL_IDS[direction] if level == "initial" else f"{direction} builders graph"
    return f"{name} refused" + (f" ({rule})" if rule else "")


def _key_values(graph_builder, attributes):
    """The attributes of a node as the viewer's `KeyValue` pairs, in the
    order given."""
    return [graph_builder.KeyValue(key=key, value=value) for key, value in attributes.items()]


def _ports(graph_builder, stage, wiring, wires):
    """The metadata items of the ports of `wires` (`_port_item`)."""
    return [_port_item(graph_builder, stage, wiring.sources, ob.identity) for ob in wires]


def _edges(graph_builder, wiring, wires):
    """The edges into the ports of `wires`, each from the node that writes
    the wire (`_edge`)."""
    return [_edge(graph_builder, wiring.writers, ob.identity) for ob in wires]


def _boundary_nodes(graph_builder, stage, hypergraph, wiring, nodes, inputs, outputs):
    """The nodes of one graph of the view: `Inputs`, whose ports are the
    graph's own inputs and whose attributes are `inputs`; the nodes of the
    boxes, `nodes`; and `Outputs`, whose ports are the graph's own outputs,
    each with an edge from the node that writes it, and whose attributes are
    `outputs`."""
    return [
        graph_builder.GraphNode(
            id=BOUNDARY_IDS[0],
            label="Inputs",
            attrs=_key_values(graph_builder, inputs),
            outputsMetadata=_ports(graph_builder, stage, wiring, hypergraph.dom.inside),
            style=NODE_STYLE,
        ),
        *nodes,
        graph_builder.GraphNode(
            id=BOUNDARY_IDS[1],
            label="Outputs",
            attrs=_key_values(graph_builder, outputs),
            incomingEdges=_edges(graph_builder, wiring, hypergraph.cod.inside),
            inputsMetadata=_ports(graph_builder, stage, wiring, hypergraph.cod.inside),
            style=NODE_STYLE,
        ),
    ]


# --- the initial diagrams ---

# the perches in the order a direction reads them, the order in which the
# layers of an initial diagram stand from left to right: the forward diagram
# arrival, decision, continuation, and the backward diagram the reverse
PERCH_ORDER = {"forward": PERCHES, "backward": tuple(reversed(PERCHES))}


def _initial_graph(graph_builder, stage, direction):
    """One initial diagram as a viewer `Graph`, `INITIAL_IDS[direction]`, the
    authored surface, drawn as the field diagram of the calculus draws it:
    the fields are the nodes and the blocks relate them (AAS, 1 October
    2026). Each perch that holds a field of the diagram is a layer named by
    the perch's word, `arvl`, `dcsn` or `cntn`, in the order the direction
    reads them (`PERCH_ORDER`), on the first step of the ice, the step of a
    stage occurrence, since the perches divide one stage, with a navy border
    and a navy label (`LAYER_COLORS["stage"]`); a field is a node inside the
    layer of its perch (`_field_nodes`), a shock, which belongs to no perch,
    a node outside the layers; and each block is a node outside the layers,
    between the perches it joins as the chapter's arrows are, named and
    labeled by its block id, the symbol the drawing shows for a block
    (`box_symbol`), white with a navy border and a navy label as every node
    of the diagram is (`NODE_STYLE`), with the block's header, its
    statements and its lines as its attributes
    (`block_attributes`), an edge from the node of each field it reads
    (`_field_edge`) and an edge into the node of each field it writes, the
    port ids the wire's identity at both ends. The layers and the root are
    laid out left to right (`_layer_config(".*", LEFT_RIGHT, …)`), so that
    the forward diagram reads arrival, decision, continuation and the
    backward one continuation, decision, arrival, and the fields of one
    perch, which no edge joins, stand one under another.

    The diagram has no nodes `Inputs` and `Outputs`: a field no block writes
    is one the diagram takes, and a field no block reads one it gives, which
    is what the boundary of the hypergraph states. Its signature, as
    `stage.initial.backward.signature()` prints it, `V≻ : {V≻}`, restates
    each field's label and stands on no layer: the attributes `inputs` and
    `outputs` of a layer are, everywhere else in the view, the layer's own
    signature, and the diagram's on the layer of one perch would list the
    fields of the other perches under that perch. The diagram carries no
    method, which the builders graphs show on the operators. A diagram the
    construction refused is the graph of one node that states the refusal
    (`_refused_graph`)."""
    try:
        hypergraph = graph_of(stage, "initial", direction)
    except NotConstructed as refusal:
        return _refused_graph(
            graph_builder,
            INITIAL_IDS[direction],
            _refused_label(direction, refusal, "initial"),
            {"refusal": str(refusal)},
        )
    wiring = _wiring(stage, hypergraph)
    fields_ = _field_nodes(graph_builder, stage, direction, hypergraph, wiring)
    blocks = [
        graph_builder.GraphNode(
            id=str(box_identity(box)),
            label=node_label(stage, direction, wiring.sources, box),
            attrs=_key_values(graph_builder, block_attributes(stage, direction, box)),
            incomingEdges=[_field_edge(graph_builder, ob.identity) for ob in box.dom.inside],
            outputsMetadata=_ports(graph_builder, stage, wiring, box.cod.inside),
            inputsMetadata=_ports(graph_builder, stage, wiring, box.dom.inside),
            style=NODE_STYLE,
        )
        for box in wiring.boxes
    ]
    layout = _layer_config(".*", graph_builder.LayoutDirection.LEFT_RIGHT, LAYER_COLORS["stage"])
    return graph_builder.Graph(
        id=INITIAL_IDS[direction],
        nodes=fields_ + blocks,
        # a perch's layer holds no attribute: its fields are its nodes
        groupNodeAttributes={node.namespace: {} for node in fields_ if node.namespace},
        groupNodeConfigs=[layout],
    )


def _field_nodes(graph_builder, stage, direction, hypergraph, wiring):
    """The nodes of the fields of one initial diagram, perch by perch in the
    order the direction reads the perches (`PERCH_ORDER`), the shocks, which
    belong to no perch, after them, and within a perch in the order the
    diagram meets the fields, its own inputs first and then the outputs of
    each block: each named by the wire's identity, `cons:dcsn:m_d`, labeled
    as the drawing labels the wire (`port_label`), `m_d`, in the layer of its
    perch, with the field's attributes (`field_attributes`), an edge from
    the block that writes it where one does (`_edge`) and otherwise none,
    the field being one the diagram takes, and the port of the wire
    (`_port_item`) on its input side where a block writes it and on its
    output side where a block reads it."""
    read = {ob.identity for box in wiring.boxes for ob in box.dom.inside}
    met = dict.fromkeys(
        [ob.identity for ob in hypergraph.dom.inside]
        + [ob.identity for box in wiring.boxes for ob in box.cod.inside]
    )
    perches = {perch: [] for perch in PERCH_ORDER[direction]}
    perches[None] = []
    for identity in met:
        perches[identity.perch if identity.perch in PERCH_NAMES else None].append(identity)
    listed = _listing_lines(stage)
    edges = fields(stage).edges
    nodes = []
    for perch, identities in perches.items():
        for identity in identities:
            port = _port_item(graph_builder, stage, wiring.sources, identity)
            written = wiring.writers[identity] != BOUNDARY_IDS[0]
            nodes.append(
                graph_builder.GraphNode(
                    id=str(identity),
                    label=port_label(wiring.sources, identity),
                    namespace=perch or "",
                    attrs=_key_values(
                        graph_builder,
                        field_attributes(wiring.sources.sorts[identity], listed, edges),
                    ),
                    incomingEdges=[_edge(graph_builder, wiring.writers, identity)]
                    if written
                    else [],
                    outputsMetadata=[port] if identity in read else [],
                    inputsMetadata=[port] if written else [],
                    style=NODE_STYLE,
                )
            )
    return nodes


def field_attributes(sort, listed, edges) -> dict:
    """The attributes a field's node shows in the side panel, each one line,
    in the order the fields table prints a field's row (`stage.fields()`):
    `kind`, `field`; `perch`, the perch the field belongs to, or for a shock,
    which belongs to none, `edge`, the pair of perches of the transition that
    draws it as the fields table prints it, `∼→≻` (`edges`, the table's
    `edges`); `role`, where the sort carries one (`_role`); `set`, the
    field's declared set as the fields table prints it (`to_source` of the
    sort's domain), where a header declares one; and `lines`, the file and
    the line of the header that first lists the field (`listed`,
    `_listing_lines`), `cons.bl 13`, where a header at a position lists it.
    An attribute that would hold nothing is not written."""
    identity = sort.identity
    shown = {"kind": "field"}
    if identity.perch in PERCH_NAMES:
        shown["perch"] = identity.perch
    elif edges.get(identity):
        shown["edge"] = "→".join(PERCH_SIGN[perch] for perch in edges[identity])
    if _role(sort):
        shown["role"] = _role(sort)
    if sort.domain is not None:
        shown["set"] = to_source(sort.domain)
    line = listed.get(identity)
    if line is not None:
        shown["lines"] = _line_numbers([line])
    return shown


def _listing_lines(stage):
    """The line of the header that first lists each field, by the field's
    identity, as a `SourceLine`, read in the order of the file
    (`blocks_in_file_order`) from the headers the blocks of the two initial
    diagrams retain (`header_of`, the declared inputs with the controls among
    them and the outputs) and from the position each block's record holds
    beside its header (`header_line`): the order in which the fields table
    lists the fields. A block of a refused diagram, whose record no handle
    reaches, and a header at no position list no field here."""
    holders = {}
    for direction in DIRECTIONS:
        try:
            graph = graph_of(stage, "initial", direction)
        except NotConstructed:
            continue
        for box in graph.boxes:
            if not is_wiring(box):
                holders.setdefault(box.name, direction)
    found = {}
    for box in blocks_in_file_order(stage):
        if box.name not in holders:
            continue
        line = header_line(getattr(stage.initial, holders[box.name])[box.name].denote())
        if line is None:
            continue
        declared_in, declared_out = header_of(box)
        for sort in declared_in + declared_out:
            found.setdefault(sort.identity, line)
    return found


def _field_edge(graph_builder, identity):
    """The edge of one field into a block that reads it, from the node of the
    field, the wire's identity string the node's id and the port id at both
    ends."""
    return graph_builder.IncomingEdge(
        sourceNodeId=str(identity),
        sourceNodeOutputId=str(identity),
        targetNodeInputId=str(identity),
    )


def block_attributes(stage, direction, box) -> dict:
    """The attributes a block's node shows in the side panel, each one line,
    read from the block's record, `stage.initial.backward["cntn_to_dcsn"]
    .denote()`: `kind`, `block`; `header`, the block's header as the file
    writes it after the id, the fields it reads and writes with their
    declared sets and roles and the control it is read at; `statement`, each
    authored line of the block as the card's `Source` section quotes it,
    with its line number, numbered where there are several (`_numbered`);
    and `lines`, the file and the numbers of the header's line and the
    quoted lines, `cons.bl 21–23` (`_line_numbers`), by which a block's node
    returns to its header as a builder's box returns to its block."""
    record = getattr(stage.initial, direction)[box.name].denote()
    shown = {"kind": record.kind, "header": record.header[0]}
    shown.update(_numbered("statement", _rows(card_sections(record), "source")))
    header = header_line(record)
    lines = _line_numbers(([] if header is None else [header]) + list(source_lines(record)))
    if lines:
        shown["lines"] = lines
    return shown


# What the view reads from one builders graph for its edges: its operator
# boxes, what the drawing writes its labels from (`label_sources`), the node
# that writes each wire (`_writers`) and each wire a node reads (`_reads`).
_Wiring = namedtuple("_Wiring", "boxes sources writers reads")


def _wiring(stage, hypergraph):
    """The boxes of one graph of the view, the operators of a builders graph
    or the blocks of an initial diagram, its label sources, the writer of
    each wire and the wires each node reads, as a `_Wiring`."""
    boxes = [box for box in hypergraph.boxes if not is_wiring(box)]
    return _Wiring(
        boxes=boxes,
        sources=label_sources(stage, hypergraph),
        writers=_writers(hypergraph, boxes),
        reads=_reads(hypergraph, boxes),
    )


def _reads(hypergraph, boxes):
    """Each wire a node of the view reads, as the pair of the node's id and
    the wire's identity, in the order of the nodes and of their ports: the
    inputs of each box, then the graph's outputs, which the `Outputs` node
    of a builders graph reads and an initial diagram gives from the nodes of
    its fields."""
    return [(str(box_identity(box)), ob.identity) for box in boxes for ob in box.dom.inside] + [
        (BOUNDARY_IDS[1], ob.identity) for ob in hypergraph.cod.inside
    ]


def _writers(hypergraph, boxes):
    """The id of the node that writes each wire, by the wire's identity: the
    `Inputs` node for a wire the graph takes, which in an initial diagram
    stands for no node, since the field's own node is the source there, and
    otherwise the box whose output it is. A wire of a hypergraph has one
    writer, and every wire that a box or the graph's outputs read is
    written; a graph that breaks either is refused, since the view would
    otherwise show some of its edges and omit others without saying so."""
    written = {ob.identity: BOUNDARY_IDS[0] for ob in hypergraph.dom.inside}
    for box in boxes:
        name = str(box_identity(box))
        for ob in box.cod.inside:
            writer = written.setdefault(ob.identity, name)
            if writer != name:
                raise ValueError(
                    f"the wire {ob.identity} is written by both {writer} and {name}; a wire of "
                    "a hypergraph has one writer, and the view cannot show two"
                )
    for reader, identity in _reads(hypergraph, boxes):
        if identity not in written:
            raise ValueError(
                f"the wire {identity} that {reader} reads is written by no node of the graph "
                "and is not one of its inputs; the view has no edge to show for it"
            )
    return written


def _edge(graph_builder, writers, identity):
    """The edge of one wire into a node that reads it, from the node that
    writes it, the wire's identity string the port id at both ends."""
    return graph_builder.IncomingEdge(
        sourceNodeId=writers[identity],
        sourceNodeOutputId=str(identity),
        targetNodeInputId=str(identity),
    )


# --- the layers ---

# One builder or sub-builder of a builders graph: the namespace of its layer,
# its bubble in the stored graph, and `within`, the address of the builder or
# sub-builder it stands in, None for a builder.
_Holder = namedtuple("_Holder", "namespace bubble within")


def _holders(stage, direction):
    """Each builder and sub-builder of one builders graph by its address,
    with the namespace of its layer, its bubble and the address it stands
    in: a builder's namespace is its block id, and a sub-builder's is its
    builder's followed by its key within the builder (`piece_named`),
    `cntn_to_dcsn/risk_ce`. They are read from the bubbles of the stored
    graph, the builder grain, in which a sub-builder stands inside its
    builder."""
    found = {}

    def walk(boxes, holder):
        for box in boxes:
            if isinstance(box, Bubble):
                address = box_identity(box).address
                key = piece_named(box, holder)
                namespace = f"{found[holder].namespace}/{key}" if holder else key
                found[address] = _Holder(namespace, box, holder)
                walk(boxes_inside(box), address)

    walk(graph_of(stage, "builders", direction).boxes, None)
    return found


def _namespace(box, holders):
    """The namespace of a primitive, `policy` or `cntn_to_dcsn/risk_ce`: the
    namespace of the innermost builder or sub-builder its identity is rooted
    at (`Identity.key_within`). An address names the statement a box is born
    at even where that statement is no sub-builder, `policy.InvEuler` in
    `cons.bl`; such a box stands directly in its builder."""
    identity = box_identity(box)
    rooted = [address for address in holders if identity.key_within(address) is not None]
    return holders[max(rooted, key=len)].namespace if rooted else ""


def _layer_attributes(stage, direction, holders, held, boxes):
    """The attributes of each layer by its namespace, which the side panel
    shows when the layer is selected: `inputs` and `outputs`, the two sides
    of its builder's signature as the builder's `signature()` prints them
    (`box_signature`), each on one line, its entries separated by `, ` and an
    entry the printing breaks at the width of a card with its lines joined
    by one space (`_one_line`); on the layer of a builder, and not of a
    sub-builder, what its primitives `boxes` share (`_builder_attributes`);
    and the attributes of the method bound at the builder or the sub-builder
    itself (`_method_attributes`), read from its card: a binding within it
    that no primitive of the graph holds (`held`, the targets bound within
    the primitives) and no deeper layer holds. The viewer labels a layer
    by its namespace, so such a method stands in the layer's attributes
    alone. A builder's layer then lists every setting the version binds
    (`_version_settings`), so the method bound at the builder lists none of
    its own."""
    found = {}
    for address, holder in holders.items():
        found[holder.namespace] = _signature_sides(box_signature(stage, holder.bubble))
        if holder.within is None:
            inside = [box for box in boxes if box_identity(box).block == address]
            found[holder.namespace].update(
                _builder_attributes(stage, direction, holder.namespace, inside)
            )
    claimed = set(held)
    # the deepest layers are read first
    # (a binding within a sub-builder then stands on the sub-builder alone)
    for holder in sorted(holders.values(), key=lambda layer: -layer.namespace.count("/")):
        handle = _layer_handle(stage, direction, holder.namespace)
        own = [target for target in handle.methods if target not in claimed]
        if not own:
            continue
        method = _bound_method(stage, handle, own)
        if holder.within is None and method is not None:
            # the version's settings stand on the builder's layer below
            method = method._replace(settings=())
        found[holder.namespace].update(_method_attributes(method))
        claimed.update(own)
    settings = _numbered("setting", _version_settings(stage))
    for holder in holders.values():
        if holder.within is None:
            found[holder.namespace].update(settings)
    return found


def _signature_sides(signature):
    """The two sides of a signature as two attributes, `inputs` and
    `outputs`, as the signature prints them, each on one line, its entries
    separated by `, ` and an entry the printing breaks at the width of a
    card with its lines joined by one space (`_one_line`)."""
    return {
        side: ", ".join(
            _one_line(str(line).split("\n"))
            for word, line in signature.entries
            if word == SIDE_WORDS[key]
        )
        for side, key in (("inputs", "in"), ("outputs", "out"))
    }


def _builder_attributes(stage, direction, namespace, boxes):
    """The attributes of a builder's layer that its primitives `boxes`
    share, each one line and numbered where there are several
    (`_numbered`): `where`, the rows of the `Where` section of the builder's
    card, the local abbreviations its primitives' rules write, each once and
    on none of the primitives (`_rows`); `feasible set`, on the layer of a
    policy builder, the definition of each feasible set its policy names
    (`_feasible_sets`); and `parameter`, each parameter the primitives read
    (`_parameter_lines`). A builder's record holds the local abbreviations
    its pieces introduce (`Composite.where`), so its card is read only where
    the record of one of its primitives holds one."""
    handle = _layer_handle(stage, direction, namespace)
    introduced = any(piece_handle(stage, direction, box).denote().where for box in boxes)
    rows = _rows(card_sections(handle.denote()), "where") if introduced else []
    shown = _numbered("where", rows)
    if direction == "backward" and namespace in wire_table(stage).policy_blocks:
        shown.update(_numbered("feasible set", _feasible_sets(stage, handle)))
    shown.update(_numbered("parameter", _parameter_lines(stage, boxes)))
    return shown


def _feasible_sets(stage, handle):
    """The definition of each correspondence the record of a policy builder
    reaches (`Composite.definitions`), the feasible sets its controls are
    chosen from, as the stage's definitions table holds it and `to_source`
    writes it, `Γ_c(x : Xa) := [0, x]`, in the order of the file."""
    return [
        to_source(equation)
        for denoted in handle.denote().definitions
        if getattr(denoted.identity, "kind", None) == "correspondence"
        for equation in stage.definitions[denoted.identity].equations
    ]


def _parameter_lines(stage, boxes):
    """Each parameter the primitives `boxes` read, named by the retained
    terms of their rows directly or through the functions those terms call
    (`conditions.parameters_named`), in the order the file declares them, as
    the version prints it (`stage.par`): `β = 0.97 : (0,1)` where a
    calibration binds its value and `β : (0,1), unbound` where none does."""
    named = set(parameters_named(stage, [row_of(stage, box) for box in boxes]))
    parameters = stage.par
    return [str(parameters[name]) for name in parameters if name in named]


def _version_settings(stage):
    """Every setting the version binds, in binding order, as the version
    prints it (`stage.settings`), `n_a = 300`, with the places and the
    methods that read it after it where a method names it; none on a
    version no configuration has bound."""
    configured = stage.settings
    return [str(configured[name]) for name in configured]


def _layer_handle(stage, direction, namespace):
    """The handle of a builder or a sub-builder by the namespace of its
    layer, `cntn_to_dcsn/risk_ce`, read from the builders graph of its
    direction one segment at a time, as a reader reaches it:
    `stage.builder.bwd["cntn_to_dcsn"]["risk_ce"]`."""
    handle = getattr(stage.builder, DIRECTION_WORDS[direction])
    for segment in namespace.split("/"):
        handle = handle[segment]
    return handle


# --- the labels, the ports and the style ---

# What the drawing of one graph writes its labels from, read once for the
# graph: the sort of every wire, the name the stage gives each wire and the
# law or the aggregator each box applies where the box does not name it (the
# two arguments `pieces.drawing_arguments` gives `to_drawing`), the value
# aggregations of the graph, and the proposed form `SHORT_LABELS` chooses:
# the name of each result wire that carries a function, by the function at
# its coordinates.
LabelSources = namedtuple("LabelSources", "sorts names laws value_aggregations short_names")


def label_sources(stage, hypergraph) -> LabelSources:
    """What the drawing of `hypergraph` writes its labels from: the sorts and
    the value aggregations it reads itself (`drawn_sorts`,
    `value_aggregations_of`), the wire names and the laws it is given, by
    the one function that gives them to the drawing
    (`pieces.drawing_arguments`), and the proposed form of a result wire's
    label (`_short_names`)."""
    arguments = drawing_arguments(stage, hypergraph)
    sorts = drawn_sorts(hypergraph)
    return LabelSources(
        sorts=sorts,
        names=arguments["wire_names"],
        laws=arguments["laws"],
        value_aggregations=value_aggregations_of(hypergraph),
        short_names=_short_names(stage, sorts),
    )


def _short_names(stage, sorts):
    """The proposed label of each result wire that carries a function, by
    the wire's identity (line 6 of the study of 30 September): the function
    at its coordinates, `𝑉(m_d)`, the form the drawing gives a wire the stage
    names otherwise (`wire_label` with no name), the left side of the rule
    the operator states on it. A result that carries a set of candidate
    policies, `𝒫(…)`, is absent and keeps its expression."""
    return {
        identity: wire_label(sort)
        for identity, sort in sorts.items()
        if identity.is_result
        and isinstance(wire_type(stage, sort).carrier, S.MeasurableMapSet)
        and not isinstance(wire_type(stage, sort).carrier.codomain, S.PowerSet)
    }


def node_label(stage, direction, sources, box) -> str:
    """The text the node of `box` shows, a box of the graph of `direction`
    whose label sources are `sources`: one line, the head of the symbol the
    drawing shows for the box (`box_symbol`), given the law `_drawn_law`
    names, so that no law and no aggregator is written out at a policy,
    `𝑉≻ ∘ 𝑔≻`, `𝐺`, `𝑔≺∗μ`, followed, where a method is bound within the box,
    by ` · ` and its tag as its `method` row reads it (`_bound_method`),
    `𝑉(m_d), 𝑑𝑉(m_d) · !Linear`. The kind of the operator and the
    policies its row is held at are not written on the box (AAS, 4 October
    2026: "use clean symbols"); they stand in the box's `kind` and `policy`
    rows, which the card and the panel print, and the legend names the marks.
    A box that applies no primitive operator, a block of an initial diagram,
    shows the symbol the drawing shows."""
    kind = _operator_kind(box)
    if kind is None:
        return box_symbol(box, sources.value_aggregations)
    row = row_of(stage, box)
    symbol = box_symbol(
        box, sources.value_aggregations, _drawn_law(stage, direction, sources, box, row)
    )
    method = _bound_method(stage, piece_handle(stage, direction, box))
    if method is not None and method.tag:
        symbol += f" · {method.tag}"
    return symbol


def _drawn_law(stage, direction, sources, box, row):
    """The law the head of a box's symbol names on the box's node
    (`node_label`), the box's row being `row`. For a pullback or a
    push-forward at a label, the section `sources.laws` gives, `𝑔_keep≻`;
    for one whose row's `definition` is a law of motion, the name the
    card's record gives that law among the definitions of
    `piece_handle(stage, direction, box).denote()`, `𝑔≻` for
    `cons:g:dcsn_to_cntn`, so that the backward pullback and the forward
    push-forward that read one law name it alike (AMD-SG-001 §5). None for
    every other box, which references no map (ruling MI1-K2): an
    aggregation, which shows `𝐺`; a pullback or a push-forward whose row's
    `definition` is no law of motion, as an identification references its
    block's G, whose node then shows the drawing's own symbol with no law
    given, as `diagram()` shows the box; and a box of any other kind. Two
    inconsistencies within one stage are refused with a ValueError, each
    in its own sentence: a law of motion the record holds no definition of,
    named with the box, and a label whose section `sources.laws` does not
    hold; the node would otherwise show the bare `𝑔` that the name
    replaces."""
    if _operator_kind(box) not in ("Pullback", "Pushforward"):
        return None
    if row.section is not None:
        law = sources.laws.get(box_identity(box))
        if law is None:
            raise ValueError(
                f"{box.name} reads the section of the branch labeled {row.section}, and the "
                "drawing's laws hold no section for that label; a node names the section as "
                "the drawing names it, and the view writes no bare 𝑔 in its place"
            )
        return law
    if getattr(row.definition, "kind", None) != "g":
        return None
    definitions = piece_handle(stage, direction, box).denote().definitions
    named = [held.symbol for held in definitions if held.identity == row.definition]
    if not named:
        raise ValueError(
            f"{box.name} references the law of motion {row.definition}, and its card's record "
            "holds no definition of it, so the view refuses to label the box's node: a node "
            "names a law of motion as the box's card names it, and the view writes no bare 𝑔 "
            "in its place"
        )
    return named[0]


def port_label(sources, identity) -> str:
    """The label the drawing gives a wire, `𝑉≻(a)` or `μ≺`: its
    `wire_label`, with the name the stage gives the wire where it gives
    one; with `SHORT_LABELS`, a result wire that carries a function takes
    the proposed name `𝑉(m_d)` (`_short_names`)."""
    if SHORT_LABELS and identity in sources.short_names:
        return sources.short_names[identity]
    return wire_label(sources.sorts[identity], sources.names.get(identity))


def _port_item(graph_builder, stage, sources, identity):
    """The metadata item of one port, whose id is the wire's identity string,
    the same item at the two ends of the wire: the wire's label as
    `__tensor_tag`, the key under which the viewer names an input, and again
    as `label`; then its perch, where it stands at one; its role, where its
    sort carries one; and its type as the signature prints it, or, for a
    field wire of an initial diagram, `set`, the field's declared set as the
    fields table prints it (`to_source` of the sort's domain), where the
    header declares one. An attribute that would hold nothing is not
    written, since a row with no fact is no row. The side panel names an
    output that one node reads by that node's label, and lists no key of an
    output that begins with two underscores, so an output shows the wire's
    label under `label` alone."""
    sort = sources.sorts[identity]
    label = port_label(sources, identity)
    shown = {"__tensor_tag": label, "label": label}
    if identity.perch:
        shown["perch"] = identity.perch
    if _role(sort):
        shown["role"] = _role(sort)
    if getattr(sort, "derivatives", ()):
        # the coordinates in which the value carries its derivative by a
        # stated line (AMD-MB-001 §5.1), which the port's hover lists
        shown["derivatives"] = ", ".join(coordinate.field for coordinate in sort.derivatives)
    if getattr(sort, "kind", None) == "field":
        if sort.domain is not None:
            shown["set"] = to_source(sort.domain)
    else:
        shown["type"] = _type_text(stage, sort)
    return graph_builder.MetadataItem(id=str(identity), attrs=_key_values(graph_builder, shown))


def _type_text(stage, sort):
    """The type of a wire as the signature of a builder prints it, the
    carrier `wire_type` derives, `Xa → [−∞, ∞)`, `finite measure on Xm`, on
    one line: a carrier the printing breaks at the width of a card stands
    with its lines joined by one space (`_one_line`)."""
    return _one_line(str(wire_type(stage, sort)).split("\n"))


def _role(sort):
    """The role of a wire as its sort carries it, which the wire table
    gives: `value`, `control` or `state`, the role of the
    field the wire carries, or `measure`; empty where the sort carries
    none."""
    return sort.role or ""


def _style(box, wiring):
    """The style of the node of `box`, a primitive operator of the builders
    graph whose wiring is `wiring`: the output style, `OUTPUT_STYLE`, where
    the box writes a wire read outside its builder's layer, by a box of
    another builder or by `Outputs`, and the node style, `NODE_STYLE`,
    otherwise. The builder of a box is the block its identity names
    (`Identity.block`). A view of a trellis keeps the style of each node of
    an occurrence, and a join reads a wire of the occurrence's own outputs,
    which `Outputs` reads in the stage's view, so the box whose output a
    join reads has the output style there too."""
    builder = box_identity(box).block
    builders = {str(box_identity(other)): box_identity(other).block for other in wiring.boxes}
    written = {ob.identity for ob in box.cod.inside}
    for reader, identity in wiring.reads:
        if identity in written and (reader == BOUNDARY_IDS[1] or builders[reader] != builder):
            return OUTPUT_STYLE
    return NODE_STYLE


def _layer_config(pattern, direction, colors=None):
    """The configuration of the layers whose namespace `pattern` matches
    (`_LayerConfig`): their layout direction and, where `colors` gives them,
    their fill, border and label (`LAYER_COLORS`)."""
    fill, border, label = colors or (None, None, None)
    return _LayerConfig(
        namespaceRegex=pattern,
        layoutDirection=direction,
        backgroundColor=fill,
        borderColor=border,
        textColor=label,
    )


# --- the side panel: a primitive's card, one line to an attribute ---


def piece_handle(stage, direction, box):
    """The handle of a primitive, read from the builders graph of its
    direction at the primitive grain by its whole name,
    `stage.builder.bwd.primitives["cntn_to_dcsn:Pullback"]`: its `denote()`
    answers the box's card, and its `methods` the methods bound within the
    box."""
    return getattr(stage.builder, DIRECTION_WORDS[direction]).primitives[str(box_identity(box))]


def box_attributes(stage, direction, box) -> dict:
    """The attributes a primitive's node shows in the side panel, each one
    line, by key: `kind`, the kind of its operator; `policy`, the policies its
    row is held at, where it is held at any; `kernel`, the lines its
    `kernel()` prints, from which the card's `Where` and `Rule` sections are
    written; `rule`, the rules of the card's `Rule` section, each on one
    line with the region it holds on after it (`cards.rule_rows`); `lines`,
    the file and the numbers of the lines the card's `Source` section quotes
    (`_line_numbers`), `benhabib_bellman.bl 27–28`, where it quotes one; and
    the attributes of the method bound within the box
    (`_method_attributes`). An evaluation, whose kernel is the identity,
    lists under `rule` only the rules its card holds that no box writing a
    wire it reads holds (`_copied_rules`), its typing rows. A kernel of one
    line and a section of one row are one attribute, and several lines or
    rows are numbered, `rule 1`, `rule 2` (`_numbered`). The rows of the
    card's `Where` section stand once, on the layer of the box's builder
    (`_layer_attributes`), and the rows of its `Conditions` are not shown
    (AAS, 30 September 2026). The rules and the lines are those the card
    module answers from the box's record, so no printed card is read back."""
    handle = piece_handle(stage, direction, box)
    record = handle.denote()
    shown = {"kind": _operator_kind(box) or ""}
    held = ", ".join(italic(policy.field) for policy in row_of(stage, box).policy)
    if held:
        # the policies the box's row is held at, `𝑐`: the box applies its
        # operator with the control set to the policy (AMD-MI-001)
        shown["policy"] = held
    copied = _copied_rules(stage, direction, box) if _operator_kind(box) == "Evaluation" else ()
    shown.update(_numbered("rule", rule_rows(record, copied)))
    shown.update(_numbered("kernel", str(kernel(stage, box)).split("\n")))
    shown.update(_method_attributes(_bound_method(stage, handle)))
    lines = _line_numbers(source_lines(record))
    if lines:
        shown["lines"] = lines
    return shown


def _copied_rules(stage, direction, box):
    """The rules of the boxes before `box`, those of its builders graph that
    write a wire it reads, each a `Rule` record their cards hold on their
    outputs (`Wire.rules`): the rules an evaluation's card repeats. The
    records are compared, not their printing, since the card of the
    evaluation may spell a local abbreviation that its own record does not
    define otherwise than the card of the box before it, `𝐴≻,𝑝𝑜𝑙𝑖𝑐𝑦` for
    `A≻,policy` in `cons_obs.bl`."""
    graph = graph_of(stage, "builders", direction, grain="primitive")
    read = {ob.identity for ob in box.dom.inside}
    return {
        rule
        for other in graph.boxes
        if not is_wiring(other) and read.intersection(ob.identity for ob in other.cod.inside)
        for wire in piece_handle(stage, direction, other).denote().outputs
        for rule in wire.rules
    }


def _line_numbers(quoted):
    """The file and the numbers of the authored lines a card's `Source`
    section quotes (`cards.source_lines`), `benhabib_bellman.bl 27–28`: each
    file once, in the order the section quotes its lines, followed by their
    numbers (`_runs`), two files separated by `; `. A line that holds no
    position has neither a file nor a number and is left out, so a card
    that quotes no positioned line answers the empty text."""
    files = {}
    for line in quoted:
        if line.file is not None:
            files.setdefault(line.file, []).extend([] if line.number is None else [line.number])
    return "; ".join(" ".join((name, _runs(numbers))).strip() for name, numbers in files.items())


def _runs(numbers):
    """Line numbers as runs, `18–19, 22`: each run of consecutive numbers as
    its first and its last joined by an en dash, a run of one number as that
    number, the runs in order and separated by `, `."""
    runs = []
    for number in sorted(set(numbers)):
        if runs and number == runs[-1][1] + 1:
            runs[-1][1] = number
        else:
            runs.append([number, number])
    return ", ".join(str(first) if first == last else f"{first}–{last}" for first, last in runs)


def _one_line(row):
    """A row of a card on one line: the lines the row prints on, each without
    the columns it stands in, joined by one space."""
    return " ".join(line.strip() for line in row)


def _rows(sections, label):
    """The rows of a card's sections of the heading key `label`, `where` for
    `Where`, in order, each on one line (`_one_line`)."""
    return [
        _one_line(row) for section in sections if section.label == label for row in section.rows
    ]


def _numbered(word, values):
    """One attribute to a value, in order: named by the word alone where
    there is one value, `rule`, and numbered from one where there are
    several, `rule 1`, `rule 2`; none where there is no value."""
    if len(values) == 1:
        return {word: values[0]}
    return {f"{word} {number}": value for number, value in enumerate(values, 1)}


# The components typed within a piece, as the view shows them.
# `tag` is the method word as the card writes it, `!egm`, or empty where no
# method component is typed.
# `grid` is the grid component as the card writes it, or empty.
# `handler` is the program the card's `Method` row names, or empty.
# `options` holds the rows of the card's `Options` section, each on one line.
# `settings` holds the settings the components name, as the version prints them.
_BoundMethod = namedtuple("_BoundMethod", "tag grid handler options settings")


def _bound_method(stage, handle, targets=None):
    """The components typed within a piece (`_the_methods`), read from the
    piece's handle and its card, as one `_BoundMethod`: their method words
    joined by `, `, `!Linear, !pchip` for an Evaluation whose two stored
    objects are represented apart (specification 0.7 D4), their grids and
    their handlers likewise, and their options and settings in order; None
    where nothing is typed. `targets` restricts the places read to these,
    as a layer reads the places within it that no primitive holds. A
    primitive's rows, its label (`node_label`) and a builder's layer read a
    piece's methods here, so the three cannot disagree."""
    within = [target for target in handle.methods if targets is None or target in targets]
    if not within:
        return None
    record = handle.denote()
    bindings = [
        bound
        for bound in _bindings(record, card_sections(record))
        if bound.clause.address in within
    ]
    clauses = _the_methods([bound.clause for bound in bindings])
    if not clauses:
        return None
    options = [
        row
        for clause in clauses
        for row in next(bound.options for bound in bindings if bound.clause is clause)
    ]
    settings = [line for clause in clauses for line in _setting_lines(stage, clause)]
    return _BoundMethod(
        tag=", ".join(f"!{clause.method.name}" for clause in clauses if clause.method is not None),
        grid=", ".join(
            to_source(T.Grid(clause.grid)) for clause in clauses if clause.grid is not None
        ),
        handler=", ".join(clause.handler for clause in clauses if clause.handler),
        options=tuple(_one_line(row) for row in options),
        settings=tuple(dict.fromkeys(settings)),
    )


# One binding within a piece as its card prints it: the method clause of the
# card's record, and the rows of the `Options` section after its `Method`
# section.
_Bound = namedtuple("_Bound", "clause options")


def _bindings(record, sections):
    """The bindings within a piece, each method clause of its card's record
    with the rows of its `Options` section, in the order the card prints
    them: a `Method` section for each clause, followed by an `Options`
    section where the clause names options."""
    groups = []
    for section in sections:
        if section.label == "method":
            groups.append(())
        elif section.label == "options" and groups:
            groups[-1] = section.rows
    clauses = tuple(getattr(record, "method", ()))
    if len(groups) != len(clauses):
        raise ValueError(
            f"the card prints {len(groups)} `Method` sections for the {len(clauses)} methods "
            "its record binds; the view reads each method's options from its own section"
        )
    return [_Bound(clause, options) for clause, options in zip(clauses, groups)]


def _the_methods(bound):
    """The distinct components among the method clauses within a piece,
    each a `MethodClause` holding `method`, `grid` and `handler`, in the
    order of its card; none where nothing is typed. Two places of the piece
    typed alike, an operator head and its occurrences among them, are one
    entry."""
    found = []
    for method in bound:
        written = (method.method, method.grid, method.handler)
        if not any(written == (held.method, held.grid, held.handler) for held in found):
            found.append(method)
    return found


def _method_attributes(method):
    """The attributes of the components typed within a piece
    (`_bound_method`), each one line: `method`, the method word; `grid`;
    `handler`; `option`, the rows of the card's `Options`; and `setting`,
    the settings the components name, each numbered where there are several,
    `option 1`, `option 2` (`_numbered`). A component the piece does not
    hold is left out, and nothing is shown where nothing is typed."""
    if method is None:
        return {}
    shown = {
        key: value
        for key, value in (
            ("method", method.tag),
            ("grid", method.grid),
            ("handler", method.handler),
        )
        if value
    }
    shown.update(_numbered("option", method.options))
    shown.update(_numbered("setting", method.settings))
    return shown


def _setting_lines(stage, clause):
    """Each setting the components of a method clause name
    (`setting_names`), the keyword arguments of its method word and the
    factors of its grid, in the order they name them, as the version's
    settings print it, `stage.settings[name]`; a setting the version does
    not configure is left out."""
    configured = stage.settings
    return [
        str(configured[name])
        for name in dict.fromkeys([*setting_names(clause.method), *setting_names(clause.grid)])
        if name in configured
    ]


# --- the overlays ---


def _attribute(item, key):
    """The value of the attribute `key` of a node or of a port, or the empty
    text where it has none."""
    return next((pair.value for pair in item.attrs if pair.key == key), "")


def perch_overlays(stage_or_trellis):
    """The three perch overlays of a stage version or a trellis, arrival,
    decision and continuation, in the perches' colors (`PERCH_COLORS`): each
    holds every edge of every graph of the view whose wire lives at its
    perch (`_collected_overlays`), with no label. The view of a stage
    version holds four graphs, its two initial diagrams and its two builders
    graphs, and the view of a trellis its two builders graphs. The graphs of
    the view do not carry the overlays; `write_model_explorer` writes them
    to a file of their own, which a reader loads through the viewer's panel
    of edge overlays."""
    graph_builder = _viewer()
    return _collected_overlays(graph_builder, to_model_explorer(stage_or_trellis))


def _collected_overlays(graph_builder, collection):
    """The three perch overlays of a view, each in its perch's color
    (`PERCH_COLORS`): for each edge into a port whose wire lives at a perch,
    the port's attribute `perch`, an overlay edge from the node it leaves to
    the node it enters, in the order of the graphs, of their nodes and of
    the nodes' edges, so that the overlays paint edges of the view alone. A
    wire at no perch, a shock or the result of an operation, is in none, and
    a refused graph, whose one node reads no wire, adds none. An overlay
    edge has no label (AAS, 30 September 2026): the viewer draws an edge's
    label with a renderer that cannot draw the mathematical letters, and a
    name in ASCII, `V at continuation`, named the pulled-back wire 𝑉≻ ∘ 𝑔 as
    𝑉≻; the wire's label stands on its ports."""
    found = {perch: [] for perch in PERCH_NAMES}
    for graph in collection.graphs:
        for node in graph.nodes:
            perches = {item.id: _attribute(item, "perch") for item in node.inputsMetadata}
            for edge in node.incomingEdges:
                perch = perches[edge.targetNodeInputId]
                if perch in found:
                    found[perch].append(
                        graph_builder.Edge(sourceNodeId=edge.sourceNodeId, targetNodeId=node.id)
                    )
    return [
        graph_builder.EdgeOverlay(
            name=PERCH_NAMES[perch], edgeColor=PERCH_COLORS[perch], edges=edges
        )
        for perch, edges in found.items()
    ]


# --- the trellis view ---

# One stage occurrence of a trellis as the view names it: the index `h` of
# its period, its key in the period's `stages` mapping, the stage version at
# that position, and its address `periods[h]/<key>`, which is the namespace
# of its layer and the prefix of its ids.
_Occurrence = namedtuple("_Occurrence", "h key stage address")

# One join of a trellis: the address of the occurrence it leaves and the
# continuation field it carries, the address of the occurrence it reaches and
# the arrival field it joins, its label on one line, the text of the trellis
# drawing (`join_label`), after the mapping's index for a join between
# periods, `inter_connectors[0] a → k`, and the address in the trellis of the
# entry that writes it, `inter_connectors[0]` or `periods[0].connectors[1]`,
# the empty text for an inferred pair, which no entry writes (`_join`).
_Join = namedtuple("_Join", "source field target arrival label connector")


def _trellis_collection(
    graph_builder, trellis, periods=None, stages=None, unjoined=False, selection=None, initial=False
):
    """The `GraphCollection` of a trellis dictionary: its two builders
    graphs, `backward` and `forward` (`_trellis_graph`), and, with
    `initial`, the initial diagrams of the two directions after them
    (`_trellis_initial_graph`; design pass 14 §7; S-D30), of the
    occurrences the
    selection holds (`_selection`), labeled with the dictionary's `name`
    where it holds one and `trellis` otherwise, since the loaders drop the
    name a trellis file writes. The connections of the trellis are selected
    once here (`connections.trellis_selection`), and the occurrences'
    order, the joins, the wires they carry and the fields no join reaches
    are all read from that one selection. With `unjoined`, the state fields
    no join reaches are read from the whole trellis
    (`joins.unjoined_fields`) before the selection of the view restricts
    it, so that a field whose join leaves the view is never taken for one
    no join reaches, and are given to the forward graph alone (model
    interface spec 0.4 §3.4)."""
    if selection is None:
        selection = trellis_selection(trellis)
    marked = unjoined_fields(trellis, selection) if unjoined else None
    occurrences, joins, crossing = _selection(trellis, periods, stages, selection)
    return graph_builder.GraphCollection(
        label=str(trellis.get("name") or TRELLIS_LABEL),
        graphs=[
            *(
                _trellis_graph(
                    graph_builder,
                    trellis,
                    occurrences,
                    joins,
                    direction,
                    selection,
                    crossing,
                    marked if direction == "forward" else None,
                )
                for direction in DIRECTIONS
            ),
            *(
                _trellis_initial_graph(
                    graph_builder, trellis, occurrences, joins, direction, selection, crossing
                )
                for direction in (DIRECTIONS if initial else ())
            ),
        ],
    )


def _selection(trellis, periods=None, stages=None, selection=None):
    """The occurrences of a trellis a view holds, the joins between two of
    them and the joins that leave them, each list in the order of
    `_occurrences` and `_joins`, read from `selection`, the trellis's
    selection of its connections, selected here where the caller holds
    none. With neither `periods` nor `stages`, every occurrence and every
    join, and no join leaves. Otherwise the occurrences of the periods
    `periods` lists, every period where it is None, whose key `stages`
    lists, every key where it is None: an index the trellis does not hold
    is refused as `diagram_trellis` refuses it (`chosen_periods`), and a
    key no period selected holds, and a selection of no occurrence, under
    `trellis-file-shape`, each in one sentence."""
    if selection is None:
        selection = trellis_selection(trellis)
    occurrences, joins = _occurrences(trellis, selection), _joins(selection, trellis)
    if periods is None and stages is None:
        return occurrences, joins, []
    held = chosen_periods(trellis["periods"], periods)
    keys = None if stages is None else list(dict.fromkeys(stages))
    if keys is not None:
        present = sorted({key for h in held for key in trellis["periods"][h]["stages"]})
        missing = [key for key in keys if key not in present]
        if missing:
            raise FactoryError(
                f"the periods selected hold no stage {missing[0]!r}; "
                f"they hold {', '.join(present)}",
                rule="trellis-file-shape",
                address="periods",
                written=", ".join(keys),
                write=f"stage keys among {', '.join(present)}",
            )
    chosen = {
        occurrence.address
        for occurrence in occurrences
        if occurrence.h in held and (keys is None or occurrence.key in keys)
    }
    if not chosen:
        raise FactoryError(
            "the selection holds no stage occurrence of the trellis",
            rule="trellis-file-shape",
            address="periods",
            written=repr({"periods": None if periods is None else list(periods), "stages": keys}),
            write="indices of periods the trellis holds, or no `periods` for every period",
        )
    return (
        [occurrence for occurrence in occurrences if occurrence.address in chosen],
        [join for join in joins if join.source in chosen and join.target in chosen],
        [join for join in joins if (join.source in chosen) != (join.target in chosen)],
    )


def _leaving(crossing, hypergraphs, direction, entries):
    """The wires the joins that leave a restricted view carry at the end the
    view holds, by that occurrence's address and the port id of the wire,
    each with the join's label and the address of the occurrence at the
    other end, outside the view. A join carries the wires of the roles of
    `JOINED_ROLES` whose coordinates hold its field (`_carried`): backward,
    the occurrence it leaves reads them at continuation and the occurrence
    it reaches writes them at its entry perch, `entries[address]`, the
    arrival perch where the stage declares one and the decision perch
    otherwise (AMD-MB-001, the plan's P2); forward, the other way. A wire
    the view's occurrence reads enters the graph at an `outside` node, and
    one it writes leaves the graph at one (`_boundary_node`)."""
    found = {}
    roles = JOINED_ROLES[direction]
    backward = direction == "backward"
    for join in crossing:
        entry = entries.get(join.target, "arvl")
        reader = (
            (join.source, "cntn", join.field) if backward else (join.target, entry, join.arrival)
        )
        writer = (
            (join.target, entry, join.arrival) if backward else (join.source, "cntn", join.field)
        )
        if reader[0] in hypergraphs:
            (inside, perch, field), outside = reader, writer[0]
            wires = _carried(hypergraphs[inside].dom.inside, perch, field, roles)
        else:
            (inside, perch, field), outside = writer, reader[0]
            wires = _carried(hypergraphs[inside].cod.inside, perch, field, roles)
        for sort in wires:
            found.setdefault((inside, str(sort.identity)), []).append((join.label, outside))
    return found


def _occurrences(trellis, selection):
    """The stage occurrences of a trellis in the order the trellis drawing
    places them: the periods from the last index to the first, `periods[0]`
    being the last period in time, and the stages of a period in their
    forward order (`forward_order`), read from `selection`."""
    periods = trellis["periods"]
    return [
        _Occurrence(h, key, periods[h]["stages"][key], f"periods[{h}]/{key}")
        for h in reversed(range(len(periods)))
        for key in forward_order(periods[h], f"periods[{h}]", selection=selection)
    ]


def _joins(selection, trellis):
    """The joins of a trellis in the order of time, each a selected pair of
    `selection`: for each period, from the last index to the first, the
    pairs the mapping `inter_connectors[h]` writes into it from
    `periods[h + 1]`, in the mapping's order, then the pairs within it,
    sorted as `period_joins` sorts them."""
    found = []
    for h in reversed(range(len(trellis["periods"]))):
        found += [
            _join(pair)
            for pair in selection.pairs
            if pair.reading.h == h and pair.writing.h == h + 1
        ]
        found += sorted(
            (
                _join(pair)
                for pair in selection.pairs
                if pair.reading.h == h and pair.writing.h == h
            ),
            key=lambda join: (join.source, join.field, join.target, join.arrival),
        )
    return found


def _join(pair):
    """The `_Join` of a selected pair: the addresses of its two occurrences,
    its two fields, its label, the drawing's text (`join_label`) after the
    mapping's address for a pair between periods, and the address of the
    entry that writes it, the empty text for an inferred pair."""
    writing, reading = pair.writing, pair.reading
    label = join_label({"from": (writing.key, writing.field), "to": (reading.key, reading.field)})
    return _Join(
        f"periods[{writing.h}]/{writing.key}",
        writing.field,
        f"periods[{reading.h}]/{reading.key}",
        reading.field,
        (f"{pair.address} " if writing.h != reading.h else "") + label,
        pair.address if pair.origin == AUTHORED else "",
    )


# The stage views and the hypergraphs of a trellis view, by version key and
# direction. Within a process both are kept in memory, in `_VIEW_CACHE` and
# `_HYPERGRAPH_CACHE`, across readings: a trellis read again after a save
# holds the same versions apart from the one changed, and each version's
# view is computed once. The two caches are bounded; the oldest entry leaves
# when a new one would exceed the bound. Between processes the stage views
# alone are kept, each as one JSON file, its entry, in the folder of the
# views under the user's cache folder (`_views_folder`), read before a view
# is computed and written after (`_kept_view`); the hypergraphs are kept in
# memory alone. The name of the folder of the views covers the package's
# version and source files, Python's major and minor version and the
# installed versions of the package's pinned dependencies and of the viewer,
# as they stand when this module is imported (`_source_version`); it does
# not cover a module the process loaded before a change of those files, the
# viewer's modules, loaded at the first export, or any other distribution.
# The name of an entry covers its version key, its direction and the value
# of the switch `SHORT_LABELS` (`_view_entry`). The folder can be removed at
# any time: the one cost is that the first export of each version computes
# its view again.
_VIEW_CACHE_BOUND = 256
_VIEW_CACHE = {}
_HYPERGRAPH_CACHE = {}
# the folder of the package, whose source files name the folder of the views
_PACKAGE_FOLDER = Path(__file__).resolve().parents[1]
# the folder of the package's grammar files
_GRAMMAR_FOLDER = _PACKAGE_FOLDER / "syntax" / "grammars"
# the folders of the views under the user's cache folder
_VIEWS_FOLDER = ("bellman-workbench", "views")
# The distributions whose code computes a stage view, by the names
# `importlib.metadata` reads: the package's run-time dependencies as its
# `pyproject.toml` pins them, and the viewer, whose classes hold a view. A
# change of a pin or an upgrade leaves every source file of the package
# unchanged, so their installed versions, as a process finds them when it
# imports this module, enter the name of the folder of the views
# (`_source_version`).
_VIEW_DISTRIBUTIONS = (
    "discopy",
    "jsonschema",
    "lark",
    "numpy",
    "pyyaml",
    "ai-edge-model-explorer",
)


def _cached(cache, key, make):
    """The value of `key` in `cache`, made by `make` and kept where absent,
    the oldest entry dropped at the bound."""
    if key in cache:
        return cache[key]
    value = make()
    if len(cache) >= _VIEW_CACHE_BOUND:
        del cache[next(iter(cache))]
    cache[key] = value
    return value


def _kept_view(graph_builder, key, make):
    """The stage view whose key in `_VIEW_CACHE` is `key`, a builders graph
    or an initial diagram of a version in one direction: rebuilt from its
    entry in the folder of the views (`_read_entry`) where one can be read,
    and otherwise computed by `make` (`_graph`, or `_initial_graph` for the
    trellis's initial diagrams, design pass 14 §7) and written to its entry
    (`_write_entry`). In a process with no folder of the views
    (`_views_folder`), the view is computed and no entry is read or
    written."""
    if _views_folder() is None:
        # with no name for the folder, an entry cannot be told to be one
        # computed by this process's files and versions
        return make()
    entry = _view_entry(key)
    view = _read_entry(graph_builder, entry)
    if view is None:
        view = make()
        _write_entry(entry, view)
    return view


@functools.cache
def _source_version():
    """The package version that names the folder of the views: the version
    `package_version` answers, a hyphen, and the first twelve hexadecimal
    digits of a SHA-256 digest that covers the package's source files, every
    `.py` file under the package's folder and every grammar file, `.lark` or
    `.asdl`, each by its path relative to that folder and its bytes, in the
    order of the paths, and then Python's major and minor version and the
    installed version of each distribution a stage view's computation
    imports (`_installed_versions`). Computed once in a process, when this
    module is imported (the call after `_installed_versions`), so that it
    describes the files and the distributions as they stood at that import;
    a module the process loaded before a change of the files, and the
    viewer's modules, loaded at the first export, are not described by it.
    The version alone has stayed `0.1.0` through development; the digest
    tells two states of the source, of Python's major or minor version or of
    those distributions apart. None where a file or a distribution's
    metadata cannot be read, so that the module still imports; the process
    then keeps no folder of the views (`_views_folder`)."""
    try:
        names = sorted(
            path.relative_to(_PACKAGE_FOLDER).as_posix()
            for path in (
                *_PACKAGE_FOLDER.rglob("*.py"),
                *_GRAMMAR_FOLDER.glob("*.lark"),
                *_GRAMMAR_FOLDER.glob("*.asdl"),
            )
            if path.is_file()
        )
        digest = hashlib.sha256()
        for name in names:
            content = (_PACKAGE_FOLDER / name).read_bytes()
            # the path and the number of bytes are digested before the bytes,
            # so that two different sets of files never give one sequence of
            # bytes
            digest.update(f"{name}\0{len(content)}\0".encode("utf-8"))
            digest.update(content)
        # a JSON object holds no NUL byte, so the versions after the files are
        # never read as a file's path and number of bytes
        digest.update(json.dumps(_installed_versions()).encode("utf-8"))
        return f"{package_version()}-{digest.hexdigest()[:12]}"
    # the errors of a file that cannot be read, of a metadata file that is no
    # UTF-8 or holds no version, and of a package without its metadata
    except (OSError, ValueError, KeyError, metadata.PackageNotFoundError):
        return None


def _installed_versions():
    """The versions a stage view's computation depends on beside the
    package's source: Python's major and minor version under `python`, and
    the installed version of each distribution of `_VIEW_DISTRIBUTIONS` as
    `importlib.metadata.version` reads it, None for a distribution that is
    not installed."""
    versions = {"python": f"{sys.version_info.major}.{sys.version_info.minor}"}
    for name in _VIEW_DISTRIBUTIONS:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


# The package version is computed now, as the module is imported, and held
# for the process: computed at the first export instead, it would describe
# files changed after the process loaded its code, and the views this
# process computes with its older code would be written into the folder
# named for the newer files, where every later process would read them as
# current.
_source_version()


def _views_folder():
    """The folder of the views: `bellman-workbench/views/<package version>`
    under the user's cache folder, the package version as `_source_version`
    writes it. The cache folder is the one `XDG_CACHE_HOME` names where that
    is an absolute path, and `~/.cache` where it is unset, empty or
    relative, as the XDG Base Directory Specification has it; nothing is
    written into a model folder or the repository. None where the package
    version could not be computed (`_source_version`)."""
    version = _source_version()
    if version is None:
        return None
    named = Path(os.environ.get("XDG_CACHE_HOME", ""))
    home = named if named.is_absolute() else Path.home() / ".cache"
    return home.joinpath(*_VIEWS_FOLDER, version)


def _view_entry(key):
    """The entry of the stage view whose key in `_VIEW_CACHE` is `key`: the
    file of the folder of the views named by the SHA-256 digest of the key
    as `repr` writes it, a key that holds the package version
    (`_version_key`), the direction and the value of the switch
    `SHORT_LABELS` (`_trellis_graph`)."""
    return _views_folder() / f"{hashlib.sha256(repr(key).encode('utf-8')).hexdigest()}.json"


def _read_entry(graph_builder, entry):
    """The stage view the file `entry` holds, rebuilt (`_rebuilt_view`); None
    where the file is absent or unreadable, holds no JSON or holds no stage
    view, so that the view is then computed and its entry written again."""
    try:
        return _rebuilt_view(graph_builder, json.loads(entry.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


def _write_entry(entry, view):
    """The stage view `view` written to the file `entry` as plain JSON, the
    viewer's `Graph` as `dataclasses.asdict` writes it, in ASCII: first to a
    temporary file in the same folder, which one `os.replace` then puts in
    the entry's place, so that another process reading the folder finds the
    whole entry or none. A view that cannot be written, to a folder that
    cannot be written or as JSON, keeps no entry and raises nothing."""
    try:
        text = json.dumps(dataclasses.asdict(view))
        entry.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(suffix=".tmp", dir=entry.parent)
    except (OSError, TypeError, ValueError):
        return
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(text)
        os.replace(temporary, entry)
    except OSError:
        with contextlib.suppress(OSError):
            os.remove(temporary)


def _rebuilt_view(graph_builder, document):
    """The viewer's `Graph` of a stage view rebuilt from the plain JSON of
    its entry, equal to the one `_graph` computed: each node a `GraphNode`,
    its attributes `KeyValue` pairs, its edges `IncomingEdge`s, its ports
    `MetadataItem`s and its style a `_NodeStyle`, and each configuration of
    the layers a `_LayerConfig`. A field the classes do not declare is
    refused with a TypeError, and a field missing with a KeyError."""

    def pairs(entries):
        """The attributes `entries` as the viewer's `KeyValue` pairs."""
        return [graph_builder.KeyValue(**pair) for pair in entries]

    def items(entries):
        """The ports `entries` as the viewer's `MetadataItem`s."""
        return [
            graph_builder.MetadataItem(**{**item, "attrs": pairs(item["attrs"])})
            for item in entries
        ]

    nodes = [
        graph_builder.GraphNode(
            **{
                **node,
                "attrs": pairs(node["attrs"]),
                "incomingEdges": [
                    graph_builder.IncomingEdge(**edge) for edge in node["incomingEdges"]
                ],
                "outputsMetadata": items(node["outputsMetadata"]),
                "inputsMetadata": items(node["inputsMetadata"]),
                "style": None if node["style"] is None else _NodeStyle(**node["style"]),
                "config": (
                    None
                    if node["config"] is None
                    else graph_builder.GraphNodeConfig(**node["config"])
                ),
            }
        )
        for node in document["nodes"]
    ]
    configs = document["groupNodeConfigs"]
    return graph_builder.Graph(
        **{
            **document,
            "nodes": nodes,
            "groupNodeConfigs": (
                None if configs is None else [_LayerConfig(**config) for config in configs]
            ),
        }
    )


def _version_key(stage):
    """The identity of a stage version among the occurrences of a trellis:
    the package version (`_source_version`), the digest and origin of its
    text and its three bindings as `repr` writes them (the key
    `factory.trellis._pair` binds a verb under), so that two occurrences of
    one version, which hold the same graphs and bindings, share one stage
    view and one hypergraph in a trellis view, and the entry of a view kept
    between processes (`_view_entry`) is read only by a process whose
    package files and distributions, as they stood when it imported this
    module, were those of the process that wrote it."""
    recorded = tuple(stage.provenance.get(name) for name in ("sha256", "origin"))
    written = tuple(repr(held) for held in written_bindings(stage))
    return (_source_version(), *recorded, *written)


def _trellis_graph(
    graph_builder, trellis, occurrences, joins, direction, selection, crossing=(), unjoined=None
):
    """One graph of a trellis, `backward` or `forward`. Each occurrence's
    nodes are the nodes of its stage view (`_graph`), every id, port id and
    namespace prefixed by its address. A wire a join supplies to an
    occurrence is an edge from the node of the other occurrence that writes
    the wire it is paired with (`_route_pairs`), in place of the edge from
    the occurrence's `Inputs`, and the reading port names the joins in its
    attribute `join`; the edge carries the record of the route that holds
    the join under its attribute `route` (`_trellis_edge`). A wire a join
    supplies that no node of the occurrence reads is a port of the
    occurrence's own node `Inputs`, which stands in its layer with the id
    `periods[h]/<key>/GraphInputs`, so that the join is drawn. The trellis
    has no `Inputs` and no `Outputs` of its own (design pass 10 §6; unit N,
    Task 6): a wire no join supplies enters the graph at a boundary node of
    its own, and a wire no join reads leaves it at one (`_boundary_node`),
    except an occurrence's policy (`_policy_ports`), which is a port of the
    occurrence's own node `Outputs`, `periods[h]/<key>/GraphOutputs`, in
    its layer, so that no edge of a policy crosses the periods. The wires a
    join carries are those the routes of `selection`, the trellis's
    selection of its connections, establish (`_route_pairs`). In a view
    restricted to some occurrences (`_selection`), the wires that the joins
    leaving the view carry from or to one of its occurrences enter or leave
    at one `outside` node for each occurrence outside the view that those
    joins reach, labeled with that occurrence, each wire a port of the node
    that names the joins in `join` and the occurrences in `outside`
    (`_leaving`; design pass 12 §2), so that nothing is lost without a
    mark; any other such wire enters at a `start` node or leaves at an
    `end` node. The
    boundary nodes that wires enter at stand first among the graph's nodes
    and those they leave at last, each in the order in which the
    occurrences and their ports first reach it. `unjoined`, given to
    the forward graph alone, is the answer of `joins.unjoined_fields` for
    the whole trellis: each state field of an occurrence the graph holds at
    its arrival and its continuation perch is then a port of the
    occurrence's own `Inputs` or `Outputs` (`_with_field_ports`), marked
    `unjoined` where no join reaches it, added to the trellis's nodes of the
    occurrence after its stage view is read from the cache, so that no
    cached stage view holds it.

    The layers are the periods, laid out left to right, the occurrences
    inside them, left to right in the forward order, and the stage view's
    layers inside those, top to bottom (`_trellis_layers`), each filled by
    its level (`LAYER_COLORS`): a period white, an occurrence on the first
    step of the ice, a builder on the second, and a sub-builder, with every
    layer within one, on the third. The graph is one
    node stating the refusal where the construction refused an occurrence's
    graph of the direction, where `fields()` refuses an occurrence's stage
    under `PAIRING_REFUSAL` as the backward joins read it, or where a join
    leaves a wire unpaired (`_pairing`)."""
    refused, hypergraphs, supplied, undetermined = _pairing(
        occurrences, joins, direction, selection
    )
    if refused is not None:
        address, refusal = refused
        return _refused_graph(
            graph_builder,
            direction,
            _refused_label(direction, refusal),
            {"refusal": f"{address}: {refusal}"},
        )
    if undetermined:
        return _refused_graph(
            graph_builder,
            direction,
            _unpaired_label(direction, undetermined),
            _unpaired_attributes(direction, undetermined),
        )
    # the entry perch of each occurrence, at which its stage receives the
    # joins: the arrival perch where the stage declares one, the decision
    # perch otherwise (`stage_answers.entry_perch`; the plan's P2)
    entries = {occurrence.address: entry_perch(occurrence.stage) for occurrence in occurrences}
    # the wires of the joins that leave a restricted view, at the end it holds
    leaving = _leaving(crossing, hypergraphs, direction, entries)
    # one stage view per version: the occurrences of one version hold the
    # same graphs and bindings, so their views are one (`_version_key`)
    views = {}
    for occurrence in occurrences:
        # the switch `SHORT_LABELS` changes a view's labels and not the
        # hypergraph, so the views' key holds its value and `_version_key`,
        # which keys the hypergraphs as well, does not
        key = (_version_key(occurrence.stage), direction, SHORT_LABELS)
        views[occurrence.address] = _cached(
            _VIEW_CACHE, key, lambda: _kept_view(graph_builder, key, lambda: _graph(graph_builder, occurrence.stage, direction))
        )
    # the node of an occurrence's stage view that writes each wire, by the
    # occurrence's address and the wire's port id
    # the stage view's `Inputs` node writes each wire the occurrence takes
    written = {
        address: {item.id: node.id for node in view.nodes for item in node.outputsMetadata}
        for address, view in views.items()
    }

    def places(address, port):
        """The addresses of the occurrences outside a restricted view that
        the joins leaving it with the wire `port` of the occurrence at
        `address` reach, each once, in the order of the joins (`_leaving`);
        none where no such join carries the wire."""
        return list(dict.fromkeys(where for _, where in leaving.get((address, port), ())))

    def sources(address, port):
        """The node and the port of the trellis each wire an occurrence reads
        comes from, each with the route that establishes the edge, None for
        an edge no route establishes: the prefixed node of the occurrence
        that writes it; for a wire the occurrence takes, the writer of each
        wire a join supplies it from, with the route that holds the join,
        and where no join supplies it, its boundary node (`_boundary_id`),
        the `outside` node of the occurrence at `address` and of each
        occurrence outside the view whose join supplies it, and else its
        `start` node."""
        if written[address][port] != BOUNDARY_IDS[0]:
            return [(f"{address}/{written[address][port]}", f"{address}/{port}", None)]
        feeds = supplied.get((address, port))
        wire = f"{address}/{port}"
        if not feeds:
            outside = places(address, port)
            if outside:
                return [(_boundary_id("outside", address, where), wire, None) for where in outside]
            return [(_boundary_id("start", wire), wire, None)]
        # the joins of one feed belong to one route: a feed is the wire of
        # one branch of the source into one destination (`_route_pairs`)
        return [
            (source, output, supplies[0].route)
            for (writer, supplying), supplies in feeds.items()
            for source, output, _ in sources(writer, supplying)
        ]

    def edges(address, ports):
        """The edges of the trellis into the ports `ports` of a node of an
        occurrence, each named by its id in the occurrence's stage view, each
        from the node and the port its wire comes from (`sources`), carrying
        the record of the route that establishes it where one does
        (`_trellis_edge`)."""
        return [
            _trellis_edge(graph_builder, source, output, f"{address}/{port}", route)
            for port in ports
            for source, output, route in sources(address, port)
        ]

    def unread_named(address, value):
        """The value of the attribute `unread` of a reading port of the
        occurrence at `address` (`_unread_inputs`), each input
        `<writer>::<identity>` of its stage view named by the node and the
        output port of the trellis that write the wire (`sources`), as the
        edges into the port are, several joined by `; `; the stage view's
        `Inputs`, which the trellis does not hold, is never named (SE-40)."""
        return "; ".join(
            f"{source}::{output}"
            for named in value.split("; ")
            for source, output, _ in sources(address, named.partition("::")[2])
        )

    def port_item(address, port):
        """The metadata item of a port of an occurrence's node, its id
        prefixed, with the attribute `join` naming the joins that supply its
        wire where any do; on a backward join, `paired by` naming the rule
        that paired the wire with the one that supplies it
        (`PAIRING_RULES`), so that a pairing by equal names is never
        silent; `compatibility` naming the status of the route's component
        or law where it is not compatible, so that an uncertified pair is
        never silent; for a join that leaves a restricted view, `outside`,
        the address of the occurrence it reaches outside the view; and the
        attribute `unread` naming the trellis's writers (`unread_named`)."""
        feeds = supplied.get((address, port.id), {})
        outside = leaving.get((address, port.id), [])
        attrs = [
            graph_builder.KeyValue(key="unread", value=unread_named(address, pair.value))
            if pair.key == "unread"
            else pair
            for pair in port.attrs
        ] + _join_attributes(graph_builder, feeds, outside, direction)
        return graph_builder.MetadataItem(id=f"{address}/{port.id}", attrs=attrs)

    # the wires the joins read, by the writing occurrence's address and port
    read = {writer for feeds in supplied.values() for writer in feeds}
    # the names of the state fields no join reaches, by the occurrence's
    # address and the field's perch
    marked = {}
    for side, perch in (("reading", None), ("writing", "cntn")):
        for h, key, name in (unjoined or {}).get(side, ()):
            address = f"periods[{h}]/{key}"
            # a reading field stands at the occurrence's entry perch
            marked.setdefault((address, perch or entries.get(address, "arvl")), []).append(name)
    # the number of joins that reach each arrival state field joins reach,
    # by `(h, key, field)`
    reached = {
        field: len(entries) for field, entries in (unjoined or {}).get("sources", {}).items()
    }

    # the boundary nodes at which wires enter the graph and those at which
    # they leave it, which stand first and last among its nodes, each by its
    # id in the order in which a wire first reaches it, as `[kind, target,
    # label, items, edges]`: its kind, the occurrence an `outside` node
    # reaches, the label of the wire of a `start` or an `end` node, the
    # items of its ports and, for a node wires leave at, the edges from the
    # wires' writers
    entered, left = {}, {}

    def boundary(address, port, entering):
        """Records the wire `port` of the occurrence at `address` that no
        join of the view supplies, where `entering`, or reads, at its
        boundary nodes (`_boundary_node`): for each occurrence outside the
        view that a join carrying the wire reaches, the `outside` node of
        that occurrence and the occurrence at `address`, which holds the
        wire's port beside the ports of the other wires those joins carry
        (design pass 12 §2); and else the wire's own `start` or `end` node.
        A node wires leave at holds the edge from each wire's writer."""
        item = port_item(address, port)
        held = entered if entering else left
        outside = places(address, port.id)
        if outside:
            ends = [
                (_boundary_id("outside", address, where), "outside", where) for where in outside
            ]
        else:
            kind = "start" if entering else "end"
            ends = [(_boundary_id(kind, item.id), kind, None)]
        for node_id, kind, where in ends:
            found = held.setdefault(node_id, [kind, where, _attribute(port, "label"), [], []])
            if item.id not in {each.id for each in found[3]}:
                found[3].append(item)
            if not entering:
                found[4] += edges(address, [port.id])

    # the label sources of the forward initial diagram, the branches and the
    # fields of each stage version the graph holds, by the version's key,
    # each computed once
    diagrams = {}
    nodes = []
    for occurrence in occurrences:
        # the index of the occurrence's first node among the trellis's nodes
        first = len(nodes)
        address, view = occurrence.address, views[occurrence.address]
        # the wires the nodes of the occurrence's stage view read
        reads = {edge.targetNodeInputId for node in view.nodes for edge in node.incomingEdges}
        # the policy the occurrence gives, which ends inside its layer
        policy = _policy_ports(occurrence.stage, hypergraphs[address])
        for node in view.nodes:
            if node.id == BOUNDARY_IDS[0]:
                for port in node.outputsMetadata:
                    if (address, port.id) not in supplied:
                        boundary(address, port, True)
                unread = [
                    port
                    for port in node.outputsMetadata
                    if (address, port.id) in supplied and port.id not in reads
                ]
                if unread:
                    nodes.append(
                        graph_builder.GraphNode(
                            id=f"{address}/{BOUNDARY_IDS[0]}",
                            label="Inputs",
                            namespace=address,
                            incomingEdges=edges(address, [port.id for port in unread]),
                            inputsMetadata=[port_item(address, port) for port in unread],
                            style=NODE_STYLE,
                        )
                    )
            elif node.id == BOUNDARY_IDS[1]:
                given = [port for port in node.inputsMetadata if (address, port.id) not in read]
                for port in given:
                    if port.id not in policy:
                        boundary(address, port, False)
                own = [port for port in given if port.id in policy]
                if own:
                    nodes.append(
                        graph_builder.GraphNode(
                            id=f"{address}/{BOUNDARY_IDS[1]}",
                            label="Outputs",
                            namespace=address,
                            incomingEdges=edges(address, [port.id for port in own]),
                            inputsMetadata=[port_item(address, port) for port in own],
                            style=NODE_STYLE,
                        )
                    )
            else:
                nodes.append(
                    dataclasses.replace(
                        node,
                        id=f"{address}/{node.id}",
                        namespace=f"{address}/{node.namespace}" if node.namespace else address,
                        incomingEdges=edges(
                            address, [edge.targetNodeInputId for edge in node.incomingEdges]
                        ),
                        outputsMetadata=[
                            port_item(address, port) for port in node.outputsMetadata
                        ],
                        inputsMetadata=[port_item(address, port) for port in node.inputsMetadata],
                    )
                )
        if unjoined is not None:
            nodes[first:] = _with_field_ports(
                graph_builder, occurrence, nodes[first:], marked, reached, diagrams
            )
    nodes = [
        *(
            _boundary_node(graph_builder, direction, node_id, *found[:4], None)
            for node_id, found in entered.items()
        ),
        *nodes,
        *(
            _boundary_node(graph_builder, direction, node_id, *found)
            for node_id, found in left.items()
        ),
    ]
    left_right = graph_builder.LayoutDirection.LEFT_RIGHT
    top_bottom = graph_builder.LayoutDirection.TOP_BOTTOM
    # one configuration for each level, told apart by the depth of the
    # layer's namespace
    layouts = [
        _layer_config(pattern, layout, colors)
        for pattern, layout, colors in (
            # the periods side by side, as the trellis drawing places them
            # (the pattern matches the graph's root, which is no layer)
            ("^$", left_right, None),
            # a period, its stages in their forward order
            (r"^periods\[\d+\]$", left_right, LAYER_COLORS["period"]),
            # a stage occurrence, its builders as the stage view lays them out
            (r"^periods\[\d+\]/[^/]+$", top_bottom, LAYER_COLORS["stage"]),
            # a builder of an occurrence
            (r"^periods\[\d+\]/[^/]+/[^/]+$", top_bottom, LAYER_COLORS["builder"]),
            # a sub-builder of an occurrence, and every layer within one
            (r"^periods\[\d+\]/[^/]+/[^/]+/", top_bottom, LAYER_COLORS["sub-builder"]),
        )
    ]
    return graph_builder.Graph(
        id=direction,
        nodes=nodes,
        groupNodeAttributes=_trellis_layers(trellis, occurrences, views),
        groupNodeConfigs=layouts,
    )


def _join_attributes(graph_builder, feeds, outside, direction):
    """The attributes a port of a trellis graph carries for the joins that
    supply or read its wire, as `_trellis_graph` and `_trellis_initial_graph`
    write them: `join`, the labels of the joins of `feeds` (`_Supply`) and
    of those leaving a restricted view, `outside`, each once; on a backward
    join `paired by`, the rules that paired the wires (`PAIRING_RULES`);
    `compatibility`, each status of a route's component or law that is not
    compatible; and `outside`, the addresses the leaving joins reach."""
    attrs = []
    named = dict.fromkeys(supply.label for supplies in feeds.values() for supply in supplies)
    named.update(dict.fromkeys(label for label, _ in outside))
    if named:
        attrs.append(graph_builder.KeyValue(key="join", value="; ".join(named)))
    rules = dict.fromkeys(supply.rule for supplies in feeds.values() for supply in supplies)
    if rules and direction == "backward":
        attrs.append(graph_builder.KeyValue(key="paired by", value="; ".join(rules)))
    statuses = dict.fromkeys(
        supply.status
        for supplies in feeds.values()
        for supply in supplies
        if supply.status != COMPATIBLE
    )
    if statuses:
        attrs.append(graph_builder.KeyValue(key="compatibility", value="; ".join(statuses)))
    if outside:
        places = dict.fromkeys(where for _, where in outside)
        attrs.append(graph_builder.KeyValue(key="outside", value="; ".join(places)))
    return attrs


def _trellis_initial_graph(
    graph_builder, trellis, occurrences, joins, direction, selection, crossing=()
):
    """The initial diagram of a trellis in one direction, `INITIAL_IDS
    [direction]` (design pass 14 §7; S-D12, S-D13): for each occurrence of
    the view its stage's initial diagram of the direction as the stage view
    draws it (`_initial_graph`, kept in `_VIEW_CACHE` by version), every
    id, port id and namespace prefixed by the occurrence's address, the
    perch layers under the occurrence's layer, `periods[h]/<key>/cntn`, and
    the blocks in the occurrence's layer. A join is a wire from the field
    it reads to the field it supplies, carrying the route's record under
    `route` as the builders graph's edges do: backward, from the arrival
    value field the destination occurrence writes to the continuation value
    field the source requires, one wire for each function the route pairs
    (`_route_pairs`; the field of a function wire, `function_field`);
    forward, from the continuation state field of the source to the arrival
    state field of the destination, one wire for each pair of the route.
    The two field nodes carry the wire's port on the side the wire uses,
    added where the stage's diagram gives none, and the reading port names
    the joins in `join` (`_join_attributes`). A join that leaves a
    restricted view enters or leaves at an `outside` node for the
    occurrence outside the view (`_boundary_node`); no `start` and no `end`
    node is drawn, a field no join reaches standing as the stage's diagram
    draws it. The layers are the periods, the occurrences and the perches,
    the perches on the second step of the ice, every layer laid out left to
    right as the stage's diagram is. The graph is one node stating the
    refusal where the construction refused an occurrence's builders graph
    or its initial diagram, or where a join leaves a wire unpaired, as the
    builders graph of the direction is."""
    graph_id = INITIAL_IDS[direction]
    refused, hypergraphs, supplied, undetermined = _pairing(
        occurrences, joins, direction, selection
    )
    if refused is not None:
        address, refusal = refused
        return _refused_graph(
            graph_builder,
            graph_id,
            _refused_label(direction, refusal, "initial"),
            {"refusal": f"{address}: {refusal}"},
        )
    if undetermined:
        return _refused_graph(
            graph_builder,
            graph_id,
            _unpaired_label(direction, undetermined),
            _unpaired_attributes(direction, undetermined),
        )
    diagrams = {}
    for occurrence in occurrences:
        key = (_version_key(occurrence.stage), graph_id, SHORT_LABELS)
        stage = occurrence.stage
        # kept as the builders views are, in memory and as an entry of the
        # folder of the views
        diagram = _cached(
            _VIEW_CACHE,
            key,
            lambda: _kept_view(
                graph_builder, key, lambda: _initial_graph(graph_builder, stage, direction)
            ),
        )
        if len(diagram.nodes) == 1 and diagram.nodes[0].id == f"{graph_id}:refused":
            return _refused_graph(
                graph_builder,
                graph_id,
                diagram.nodes[0].label,
                {"refusal": f"{occurrence.address}: {_attribute(diagram.nodes[0], 'refusal')}"},
            )
        diagrams[occurrence.address] = diagram
    # the sorts of the wires the joins carry, by the occurrence's address and
    # the wire's id: the wires its builders graph takes and gives
    sorts = {
        occurrence.address: {
            str(ob.identity): ob
            for ob in (
                *hypergraphs[occurrence.address].dom.inside,
                *hypergraphs[occurrence.address].cod.inside,
            )
        }
        for occurrence in occurrences
    }
    # the name of each occurrence's stage as its field identities spell it
    stage_of = {
        address: next(
            (node.id.split(SEPARATOR)[0] for node in diagram.nodes if _attribute(node, "kind") == "field"),
            None,
        )
        for address, diagram in diagrams.items()
    }

    def prefixed(address, text):
        return f"{address}/{text}"

    nodes = {}
    for occurrence in occurrences:
        address = occurrence.address
        for node in diagrams[address].nodes:
            nodes[prefixed(address, node.id)] = dataclasses.replace(
                node,
                id=prefixed(address, node.id),
                namespace=prefixed(address, node.namespace) if node.namespace else address,
                incomingEdges=[
                    graph_builder.IncomingEdge(
                        sourceNodeId=prefixed(address, edge.sourceNodeId),
                        sourceNodeOutputId=prefixed(address, edge.sourceNodeOutputId),
                        targetNodeInputId=prefixed(address, edge.targetNodeInputId),
                    )
                    for edge in node.incomingEdges
                ],
                outputsMetadata=[
                    graph_builder.MetadataItem(id=prefixed(address, item.id), attrs=list(item.attrs))
                    for item in node.outputsMetadata
                ],
                inputsMetadata=[
                    graph_builder.MetadataItem(id=prefixed(address, item.id), attrs=list(item.attrs))
                    for item in node.inputsMetadata
                ],
            )

    def value_field(address, wire):
        """The node id of the field a function wire `wire` of the occurrence
        at `address` carries, None where the wire is none of its builders
        graph's."""
        sort = sorts[address].get(wire)
        return None if sort is None else prefixed(address, function_field(sort.identity))

    def state_field(address, perch, field):
        """The node id of the state field `field` at `perch` of the
        occurrence at `address`."""
        return prefixed(address, Identity("field", stage=stage_of[address], perch=perch, field=field))

    def port_on(node_id, side, attrs):
        """The port of the field node `node_id` on `side`, `in` or `out`,
        the wire's own id, added with the attributes of the node's other
        port where the stage's diagram gives none, and `attrs` added to
        it."""
        node = nodes[node_id]
        items = node.inputsMetadata if side == "in" else node.outputsMetadata
        found = next((item for item in items if item.id == node_id), None)
        if found is None:
            others = node.outputsMetadata if side == "in" else node.inputsMetadata
            base = list(others[0].attrs) if others else []
            found = graph_builder.MetadataItem(id=node_id, attrs=base)
            items.append(found)
        found.attrs.extend(attrs)

    def wire(source, reader, route, attrs):
        """The wire from the field node `source` into the field node
        `reader`, each carrying its port, the reader's with `attrs`; True
        where the wire is added, False where either node is not drawn or
        the wire stands already."""
        if source not in nodes or reader not in nodes:
            return False
        if any(edge.sourceNodeId == source for edge in nodes[reader].incomingEdges):
            return False
        port_on(source, "out", [])
        port_on(reader, "in", attrs)
        nodes[reader].incomingEdges.append(_trellis_edge(graph_builder, source, source, reader, route))
        return True

    # the entry perch of each occurrence, at which its stage receives the
    # joins (`stage_answers.entry_perch`; the plan's P2)
    entries = {occurrence.address: entry_perch(occurrence.stage) for occurrence in occurrences}
    # the label of each join by its two occurrences and its two fields, for
    # a forward pair's port
    labels = {(join.source, join.field, join.target, join.arrival): join.label for join in joins}
    for (address, port), feeds in supplied.items():
        if direction == "backward":
            reader = value_field(address, port)
            if reader is None:
                continue
            attrs = _join_attributes(graph_builder, feeds, [], direction)
            for (writer, supplying), supplies in feeds.items():
                source = value_field(writer, supplying)
                if source is not None and wire(source, reader, supplies[0].route, attrs):
                    attrs = []
            continue
        for (writer, supplying), supplies in feeds.items():
            route = supplies[0].route
            for pair in route.pairs:
                label = labels.get((writer, pair.writing.field, address, pair.reading.field))
                attrs = [graph_builder.KeyValue(key="join", value=label)] if label else []
                wire(
                    state_field(writer, "cntn", pair.writing.field),
                    state_field(address, entries.get(address, "arvl"), pair.reading.field),
                    route,
                    attrs,
                )
    # the joins that leave a restricted view, at the end the view holds: the
    # `outside` node of each occurrence outside the view that they reach,
    # which holds the wires' ports (design pass 12 §2)
    entered, left = {}, {}

    def mark(node_id, inside, where, label, entering):
        if node_id not in nodes:
            return
        attrs = [
            graph_builder.KeyValue(key="join", value=label),
            graph_builder.KeyValue(key="outside", value=where),
        ]
        port_on(node_id, "in" if entering else "out", attrs)
        node_id_outside = _boundary_id("outside", inside, where)
        held = entered if entering else left
        found = held.setdefault(node_id_outside, ["outside", where, label, [], []])
        if node_id not in {item.id for item in found[3]}:
            items = nodes[node_id].inputsMetadata if entering else nodes[node_id].outputsMetadata
            port = next(item for item in items if item.id == node_id)
            found[3].append(graph_builder.MetadataItem(id=node_id, attrs=list(port.attrs)))
        edge = graph_builder.IncomingEdge(
            sourceNodeId=node_id_outside if entering else node_id,
            sourceNodeOutputId=node_id,
            targetNodeInputId=node_id,
        )
        if entering:
            nodes[node_id].incomingEdges.append(edge)
        else:
            found[4].append(edge)

    roles = JOINED_ROLES[direction]
    for join in crossing:
        entry = entries.get(join.target, "arvl")
        if direction == "backward":
            if join.source in sorts:
                for sort in _carried(hypergraphs[join.source].dom.inside, "cntn", join.field, roles):
                    mark(value_field(join.source, str(sort.identity)), join.source, join.target, join.label, True)
            if join.target in sorts:
                for sort in _carried(hypergraphs[join.target].cod.inside, entry, join.arrival, roles):
                    mark(value_field(join.target, str(sort.identity)), join.target, join.source, join.label, False)
            continue
        if join.target in sorts and stage_of.get(join.target):
            mark(state_field(join.target, entry, join.arrival), join.target, join.source, join.label, True)
        if join.source in sorts and stage_of.get(join.source):
            mark(state_field(join.source, "cntn", join.field), join.source, join.target, join.label, False)
    ordered = [
        *(
            _boundary_node(graph_builder, direction, node_id, *found[:4], None)
            for node_id, found in entered.items()
        ),
        *nodes.values(),
        *(
            _boundary_node(graph_builder, direction, node_id, *found)
            for node_id, found in left.items()
        ),
    ]
    left_right = graph_builder.LayoutDirection.LEFT_RIGHT
    layouts = [
        _layer_config(pattern, left_right, colors)
        for pattern, colors in (
            ("^$", None),
            (r"^periods\[\d+\]$", LAYER_COLORS["period"]),
            (r"^periods\[\d+\]/[^/]+$", LAYER_COLORS["stage"]),
            (r"^periods\[\d+\]/[^/]+/[^/]+$", LAYER_COLORS["builder"]),
        )
    ]
    return graph_builder.Graph(
        id=graph_id,
        nodes=ordered,
        groupNodeAttributes=_trellis_layers(trellis, occurrences, diagrams),
        groupNodeConfigs=layouts,
    )


def _boundary_id(kind, held, target=None):
    """The id of a boundary node of a trellis graph (design pass 10 §6;
    unit N, Task 6), one of `BOUNDARY_KINDS`: its kind and `held`, for a
    `start` or an `end` node the id of the wire it marks,
    `start:periods[50]/tenure/tenure:measure:arvl`, and for an `outside`
    node the address of the occurrence of the view whose wires it marks,
    followed by the address of the occurrence it reaches, `target`,
    `outside:periods[2]/tenure:periods[3]/keeper_cons` (design pass 12
    §2)."""
    return f"{kind}:{held}" if target is None else f"{kind}:{held}:{target}"


def _boundary_node(graph_builder, direction, node_id, kind, target, label, items, edges):
    """The boundary node `node_id` of kind `kind` of a trellis graph of
    `direction` that stands, at the graph's root, for the wires whose ports
    are the metadata items `items` (design pass 10 §6; unit N, Task 6;
    decision N-D7): the one wire of a `start` or an `end` node, and the
    wires of an `outside` node, which the joins between one occurrence of
    the view and the occurrence `target` outside it carry (design pass 12
    §2). Its id, `_boundary_id`'s, is `node_id`. Its label, which its
    attribute `label` repeats, is the word of its role in the direction
    (`BOUNDARY_WORDS`) followed by the wire's label `label`, `starting data
    μ≺` or `result 𝑉≺(a, h, z)`, and for an `outside` node the address of
    the occurrence it reaches, `target`, which its attribute `target`
    holds as well; its attribute `kind` is `kind`. The node of wires that
    enter the graph, `edges` None, holds their ports among its outputs,
    from which the edges to the wires' readers leave; the node of wires
    that leave it holds the ports among its inputs, with `edges`, the edges
    from the wires' writers."""
    words = target if kind == "outside" else f"{BOUNDARY_WORDS[direction][kind]} {label}"
    shown = {"kind": kind, "label": words}
    if target is not None:
        shown["target"] = target
    sides = (
        {"outputsMetadata": list(items)}
        if edges is None
        else {"inputsMetadata": list(items), "incomingEdges": list(edges)}
    )
    return graph_builder.GraphNode(
        id=node_id,
        label=words,
        attrs=_key_values(graph_builder, shown),
        style=NODE_STYLE,
        **sides,
    )


def _trellis_edge(graph_builder, source, output, target, route):
    """An edge of a trellis graph from the port `output` of the node
    `source` into the port `target`: the viewer's `IncomingEdge` where no
    route establishes it, `route` None, and otherwise a `_RouteEdge` whose
    attribute `ROUTE_KEY` holds the route's record (`_route_record`; design
    pass 10 §6; unit N, Task 6)."""
    if route is None:
        return graph_builder.IncomingEdge(
            sourceNodeId=source, sourceNodeOutputId=output, targetNodeInputId=target
        )
    return _RouteEdge(
        sourceNodeId=source,
        sourceNodeOutputId=output,
        targetNodeInputId=target,
        attrs=[graph_builder.KeyValue(key=ROUTE_KEY, value=_route_record(route))],
    )


# The own node of a stage occurrence on which a field port stands, by the
# end of a join the field is: the node's id among `BOUNDARY_IDS`, its label
# and the side of the node that holds the port. A drag goes from a writing
# port to a reading port, so the continuation field, which writes, stands
# among the outputs of `Outputs` and the field of the entry perch, which
# reads, among the inputs of `Inputs` (decision J-D16 of unit J's plan); the
# entry perch is the arrival perch where the stage declares one and the
# decision perch otherwise (`stage_answers.entry_perch`; decision MB-U31).
_FIELD_SIDES = {
    "reading": (BOUNDARY_IDS[0], "Inputs", "inputsMetadata"),
    "writing": (BOUNDARY_IDS[1], "Outputs", "outputsMetadata"),
}


def _with_field_ports(graph_builder, occurrence, held, marked, reached, diagrams):
    """The trellis's nodes of one stage occurrence, `held`, with a port for
    each of its state fields at its entry and its continuation perch
    (model interface spec 0.4 §3.4; unit J's decisions J-D16, J-D41 to
    J-D43): a field of the entry perch, the arrival perch where the stage
    declares one and the decision perch otherwise, an input of the
    occurrence's own `Inputs`, `periods[h]/<key>/GraphInputs`, and a
    continuation field an output of its own `Outputs`,
    `periods[h]/<key>/GraphOutputs` (`_FIELD_SIDES`, `_field_item`). A name
    `marked[(address, perch)]` holds is a field no join reaches, and
    `reached[(h, key, field)]` is the number of joins that reach a field of
    the entry perch. The ports of a perch are ordered by the
    field's name, except that a branching stage's continuation fields are
    grouped by branch, in the order of the labels and, within one, of the
    branch's fields (`bellman.stage.branches`). The ports follow those of
    an own node that `held` holds, in a copy of that node; an own node the
    occurrence lacks is made in the occurrence's layer with `NODE_STYLE`
    and follows its other nodes. No node of `held` is changed in place, and
    no edge names a port. `diagrams` holds the label sources of the forward
    initial diagram, the branches and the fields of each stage version by
    its key (`_version_key`), and those this call computes are added to
    it."""
    stage = occurrence.stage
    sources, branched, sorts = _cached(
        diagrams,
        _version_key(stage),
        lambda: (_forward_field_labels(stage), _branch_of(stage), fields(stage)),
    )
    found = list(held)
    for end, (boundary, label, side) in _FIELD_SIDES.items():
        perch = entry_perch(stage) if end == "reading" else "cntn"
        unjoined = set(marked.get((occurrence.address, perch), ()))
        identities = sorted(
            (
                identity
                for identity, sort in sorts.items()
                if sort.perch == perch and sort.role == "state"
            ),
            key=lambda identity: (branched.get(identity, (len(branched), 0, "")), identity.field),
        )
        if not identities:
            continue
        items = [
            _field_item(
                graph_builder,
                occurrence,
                identity,
                sorts[identity],
                sources,
                identity.field in unjoined,
                reached.get((occurrence.h, occurrence.key, identity.field), 0),
                branched.get(identity, (None, None, None))[2],
            )
            for identity in identities
        ]
        node_id = f"{occurrence.address}/{boundary}"
        place = next((n for n, node in enumerate(found) if node.id == node_id), None)
        if place is None:
            found.append(
                graph_builder.GraphNode(
                    id=node_id,
                    label=label,
                    namespace=occurrence.address,
                    style=NODE_STYLE,
                    **{side: items},
                )
            )
        else:
            own = found[place]
            found[place] = dataclasses.replace(own, **{side: [*getattr(own, side), *items]})
    return found


def _forward_field_labels(stage):
    """The label sources of the forward initial diagram of `stage`
    (`label_sources`), whose field nodes the stage view labels by
    `port_label` (`_field_nodes`); None where the construction refused that
    diagram. The answer is kept for the version (`kept_answer`), so that a
    trellis view drawn again over the same versions, as after an edit that
    binds one stage's occurrences alone, computes it once for each version
    and not once for each view (unit L, Task 20)."""

    def compute():
        try:
            return label_sources(stage, graph_of(stage, "initial", "forward"))
        except NotConstructed:
            return None

    return kept_answer(stage, "forward field labels", compute)


def _branch_of(stage):
    """For each continuation field a branch of `stage` writes, by its
    identity, `(i, j, label)`: the position `i` of the branch's label among
    the labels `bellman.stage.branches` answers, the field's position `j`
    among the fields that branch writes, and the label; empty for a stage
    without branches (unit J's decision J-D43)."""
    return {
        identity: (i, j, label)
        for i, (label, written) in enumerate(branches(stage).items())
        for j, identity in enumerate(written)
    }


def _field_item(graph_builder, occurrence, identity, sort, sources, unjoined, count, branch):
    """The metadata item of the port of the state field `identity`, whose
    sort is `sort`, of a stage occurrence (model interface spec 0.4 §3.4;
    unit J's decisions J-D16, J-D41 to J-D43). Its id is
    `periods[h]/<key>/unjoined:<identity>` where the field is `unjoined`, no
    join reaching it, and `periods[h]/<key>/joined:<identity>` otherwise,
    the field's identity as `str` writes it, `cons:arvl:m`. Its attributes
    are `label`, the field's label as `port_label` writes it from `sources`,
    the label sources of the stage's forward initial diagram, `m≺`, or,
    where that diagram was refused (`sources` None) or holds no wire of the
    field, as `wire_label` writes the field's sort, preceded by the label of
    its branch where `branch` names one, `keep: w_kp≻`; `perch`; `role`,
    `state`; `field`, the name as the stage file writes it, `m`; `unjoined`,
    `true`, where no join reaches the field; and `sources`, `count`, the
    number of joins that reach an arrival field that joins reach."""
    drawn = (
        port_label(sources, identity)
        if sources is not None and identity in sources.sorts
        else wire_label(sort)
    )
    shown = {
        "label": drawn if branch is None else f"{branch}: {drawn}",
        "perch": identity.perch,
        "role": "state",
        "field": identity.field,
    }
    if unjoined:
        shown["unjoined"] = "true"
    elif count:
        shown["sources"] = str(count)
    port_id = (
        f"{occurrence.address}/unjoined:{identity}"
        if unjoined
        else f"{occurrence.address}/joined:{identity}"
    )
    return graph_builder.MetadataItem(id=port_id, attrs=_key_values(graph_builder, shown))


def _trellis_layers(trellis, occurrences, views):
    """The attributes of the layers of a graph of a trellis by namespace: a
    period's `h` and, where the trellis's registry gives the last age, `age`
    (`period_age`); an occurrence's `stage`, the label of its stage view;
    and the layers of each occurrence's stage view, `views[address]`, under
    the occurrence's address."""
    layers = {}
    for occurrence in occurrences:
        age = period_age(trellis, occurrence.h)
        # the period's index stands in the layer's name, `periods[1]`, and is
        # not written again
        layers.setdefault(f"periods[{occurrence.h}]", {} if age is None else {"age": str(age)})
        layers[occurrence.address] = {"stage": _collection_label(occurrence.stage)}
        for namespace, shown in views[occurrence.address].groupNodeAttributes.items():
            layers[f"{occurrence.address}/{namespace}"] = shown
    return layers


def _policy_ports(stage, graph):
    """The port ids of the outputs of a builders graph `graph` of `stage`
    that a policy builder writes, the builders whose outputs are controls
    (`WireTable.policy_blocks`): the policy, which the box of the policy
    builder's block writes, `policy:Evaluation`. The forward graph holds
    none."""
    blocks = wire_table(stage).policy_blocks
    given = {ob.identity for ob in graph.cod.inside}
    return {
        str(ob.identity)
        for box in graph.boxes
        if not is_wiring(box) and box_identity(box).block in blocks
        for ob in box.cod.inside
        if ob.identity in given
    }


def _pairing(occurrences, joins, direction, selection):
    """The pairing of the joins of a trellis view in one direction, which
    `_trellis_graph` draws and `unpaired_joins` answers as records, made by
    this one function so that the two agree on every refusal: the builders
    graph of the direction of every occurrence, at the primitive grain;
    then the wires the routes of `selection` establish for the joins
    (`_route_pairs`).

    Answers `(refused, hypergraphs, supplied, undetermined)`. `refused` is
    the address of the first occurrence, in the order of `occurrences`,
    whose graph the construction refused, with its refusal, and the other
    three are then None. Otherwise
    `refused` is None, `hypergraphs` holds the graph of each occurrence by
    its address, and `supplied` and `undetermined` are those `_route_pairs`
    answers."""
    hypergraphs = {}
    for occurrence in occurrences:
        key = (_version_key(occurrence.stage), direction)
        try:
            hypergraphs[occurrence.address] = _cached(
                _HYPERGRAPH_CACHE,
                key,
                lambda: graph_of(occurrence.stage, "builders", direction, grain="primitive"),
            )
        except NotConstructed as refusal:
            return (occurrence.address, refusal), None, None, None
    supplied, undetermined = _route_pairs(joins, hypergraphs, direction, selection)
    return None, hypergraphs, supplied, undetermined


def _route_pairs(joins, hypergraphs, direction, selection):
    """The wires the joins of a trellis view carry in one direction, as the
    routes of `selection` establish them, and the joins that leave a wire
    undetermined. The route of a join is the route of the selection whose
    pairs hold it, from the join's source occurrence, on its branch, into
    its target. Backward, each component of the route pairs one function
    wire the source's branch requires at its continuation perch with the
    wire the destination supplies at its arrival perch (`Route.components`,
    `connections._backward`); a component with no supplied wire leaves its
    required wire unpaired. Forward, the joint law the source's branch
    writes on the route's state tuple (`Route.law`) supplies each arrival
    measure of the destination whose coordinates hold the join's field; a
    route without a law leaves those measures unpaired. A join carries the
    wires of the roles of `JOINED_ROLES` whose coordinates hold its field
    (`_carried`), and is named on them.

    Answers `(supplied, undetermined)`: `supplied` holds, by the reading
    occurrence's address and the port id of the wire read, the wires that
    supply it, each by the writing occurrence's address and a port id, with
    one `_Supply` for each join that carries it, the join's label, the rule
    that paired the two wires, the status of the route's component or law
    and the route; `undetermined` holds each join that leaves a reader
    unpaired, with those readers. A wire read at a continuation perch that
    two routes supply is unpaired as well, since a value there has one
    source. The forward direction enters a reader at its entry perch, the
    perch of the measures its forward graph's domain holds, the arrival
    perch or, for a stage that declares none, the decision perch
    (`_entry_perch_of`; the plan's P2)."""
    backward, roles = direction == "backward", JOINED_ROLES[direction]
    routes = {}
    for route in selection.routes:
        for pair in route.pairs:
            routes[
                (
                    f"periods[{pair.writing.h}]/{pair.writing.key}",
                    pair.writing.field,
                    f"periods[{pair.reading.h}]/{pair.reading.key}",
                    pair.reading.field,
                )
            ] = route
    supplied, undetermined = {}, []
    for join in joins:
        route = routes[(join.source, join.field, join.target, join.arrival)]
        unpaired = []
        if backward:
            reader, writer = join.source, join.target
            carried = _carried(hypergraphs[reader].dom.inside, "cntn", join.field, roles)
            by_name = {str(sort.identity): sort for sort in carried}
            for component in route.components:
                sort = by_name.get(component.required)
                if sort is None:
                    continue
                if component.supplied is None:
                    unpaired.append(sort)
                    continue
                feeds = supplied.setdefault((reader, component.required), {})
                feeds.setdefault((writer, component.supplied), []).append(
                    _Supply(join.label, component.rule, component.status, route)
                )
                if len(feeds) > 1:
                    unpaired.append(sort)
        else:
            reader, writer = join.target, join.source
            for sort in _carried(
                hypergraphs[reader].dom.inside,
                _entry_perch_of(hypergraphs[reader]),
                join.arrival,
                roles,
            ):
                if route.law is None:
                    unpaired.append(sort)
                    continue
                feeds = supplied.setdefault((reader, str(sort.identity)), {})
                feeds.setdefault((writer, route.law), []).append(
                    _Supply(join.label, LAW_RULE, route.compatibility, route)
                )
        if unpaired:
            undetermined.append((join, unpaired))
    return supplied, undetermined


# One join's supply of a wire: the join's label, the rule by which the wire
# read was paired with the wire written (`PAIRING_RULES`, or `LAW_RULE` for
# a measure), the status of the route's component or law, and the route of
# the selection that holds the join, whose record the edge carries
# (`_route_record`).
_Supply = namedtuple("_Supply", "label rule status route")


def _route_record(route):
    """The record of a route of a trellis's selection that each edge it
    establishes carries under `ROUTE_KEY` (design pass 10 §6; unit N, Task
    6), every value read from the native `Route`: `branch`, the label of the
    source's branch, None for a stage without branches; `source` and
    `destination`, the addresses of its two occurrences, `periods[2]/tenure`;
    `source_fields` and `destination_fields`, the source's continuation
    state tuple and the destination's arrival state tuple in the route's
    order; `pairs`, each selected pair in the route's order as its two
    fields, its origin, `authored` or `inferred`, and its address, the entry
    that writes an authored pair or the period of an inferred one; `status`,
    `certified` or `uncertified`; and `law`, the joint measure the source's
    branch writes, None where it writes none. Lists stand for the route's
    tuples, so that the record is the same in memory and in the JSON
    document."""
    return {
        "branch": route.branch,
        "source": f"periods[{route.source[0]}]/{route.source[1]}",
        "destination": f"periods[{route.destination[0]}]/{route.destination[1]}",
        "source_fields": list(route.source_fields),
        "destination_fields": list(route.destination_fields),
        "pairs": [
            {
                "source_field": pair.writing.field,
                "destination_field": pair.reading.field,
                "origin": pair.origin,
                "address": pair.address,
            }
            for pair in route.pairs
        ],
        "status": route.status,
        "law": route.law,
    }


def _entry_perch_of(forward_graph):
    """The entry perch of the stage whose forward builders graph is given,
    read from the perches of the wires its domain holds: the arrival perch
    where one of them stands there, else the decision perch where one
    stands there, for a stage that declares no arrival perch; `arvl` where
    the domain holds neither (AMD-MB-001, the plan's P2;
    `stage_answers.entry_perch` answers the same of the stage)."""
    perches = {sort.identity.perch for sort in forward_graph.dom.inside}
    return "dcsn" if "dcsn" in perches and "arvl" not in perches else "arvl"


def _carried(wires, perch, field, roles):
    """The wires among `wires` a join carries at `perch` for its field
    `field`: those at the perch whose role is one of `roles` and whose
    coordinates hold the field, so that the fields a branch's wires are on
    choose the branch."""
    return [
        sort
        for sort in wires
        if sort.identity.perch == perch
        and sort.role in roles
        and any(point.perch == perch and point.field == field for point in sort.coordinates)
    ]


def _unpaired_label(direction, undetermined):
    """The label of the node that states the refusal of a graph of a trellis
    whose joins leave wires unpaired, `backward trellis graph refused
    (unpaired marginal values)`: the direction and the roles of those wires,
    in the form of `_refused_label`, which labels a refused builders graph,
    of a stage or of a trellis's stage occurrence."""
    roles = dict.fromkeys(sort.role for _, unpaired in undetermined for sort in unpaired)
    words = " and ".join(f"{role}s" for role in roles)
    return f"{direction} trellis graph refused (unpaired {words})"


def _written_name(sort):
    """The name of a wire as the stage file writes it, `dV_f_wk[>]`: the
    name of the field it carries (`function_wire_name`) followed by the mark
    of its perch, `[>]` at continuation and `[<]` at arrival
    (`WRITTEN_MARK`)."""
    return function_wire_name(sort.identity) + WRITTEN_MARK.get(sort.identity.perch, "")


class UnpairedWire(namedtuple("UnpairedWire", "occurrence name file line")):
    """One wire a join leaves unpaired: `occurrence`, the address of the
    occurrence that reads it, `periods[1]/retire_choice`; `name`, as the
    stage file writes it, `dV_f_wk[>]`; `file`, the stage file's origin as
    the occurrence's provenance records it; and `line`, the line of the
    header that first lists the field the wire carries (`_listing_lines`),
    None where no header at a position lists it."""

    __slots__ = ()


class UnpairedJoin(namedtuple("UnpairedJoin", "label source target connector wires")):
    """One join that leaves a wire unpaired, the row `join n` of a refusing
    node as a record: `label`, the drawing's text, `inter_connectors[0]
    y_f_wk → y_f_w`; `source` and `target`, the addresses of the occurrences
    it leaves and reaches; `connector`, the address in the trellis of the
    mapping that makes it, `inter_connectors[0]` or
    `periods[0].connectors[0]`, the empty text for an inferred pair;
    and `wires`, each `UnpairedWire` it leaves."""

    __slots__ = ()


def unpaired_joins(trellis, direction="backward", *, periods=None, stages=None, selection=None):
    """The joins of a trellis view that leave a wire unpaired in its graph of
    `direction`, as `UnpairedJoin` records in the order of the refusing
    node's rows `join n` (`_unpaired_attributes`), the view restricted by
    `periods` and `stages` as `to_model_explorer` restricts it and its joins
    paired as its graph pairs them (`_pairing`); none where the graph is
    drawn, or refused for another reason, an occurrence's graph the
    construction refused or a marginal value whose name declares two
    pairings. The trellis's connections are selected once for the answer
    (`connections.trellis_selection`), or reused from `selection` when the
    caller holds the result for this exact trellis version."""
    if selection is None:
        selection = trellis_selection(trellis)
    occurrences, joins, _ = _selection(trellis, periods, stages, selection)
    refused, _, _, undetermined = _pairing(occurrences, joins, direction, selection)
    if refused is not None:
        return ()
    held = {occurrence.address: occurrence.stage for occurrence in occurrences}
    listed, found = {}, []
    for join, unpaired in undetermined:
        # the occurrence that reads the wires: backward the one the join leaves
        reader = join.source if direction == "backward" else join.target
        if reader not in listed:
            listed[reader] = _listing_lines(held[reader])
        wires = tuple(
            UnpairedWire(
                reader,
                _written_name(sort),
                held[reader].provenance.get("origin"),
                getattr(listed[reader].get(function_field(sort.identity)), "number", None),
            )
            for sort in unpaired
        )
        found.append(UnpairedJoin(join.label, join.source, join.target, join.connector, wires))
    return tuple(found)


def _unpaired_attributes(direction, undetermined):
    """The attributes of the node that states why a graph of a trellis is
    refused, one line each: `refusal`, the sentence with the number of joins
    that leave a wire unpaired, then the rules of `_paired` in their order,
    and the name by which a marginal value declares its coordinate,
    `d_<coordinate><value>`, which the first rule reads; then `join`, each
    such join by its label, the addresses of its two occurrences and the
    wires it leaves unpaired, each as the stage file writes it, `dV_f_rt[>]`,
    numbered where there are several (`_numbered`), so that a reader finds
    each join on a row of its own and not inside one sentence."""
    count = f"{len(undetermined)} join" + ("s" if len(undetermined) > 1 else "")
    shown = {
        "refusal": (
            f"the {direction} graph of the trellis is not drawn: at {count} a wire one "
            "occurrence reads is paired with no wire the other occurrence writes, or with "
            "two; the selection of the connections pairs the marginal values a source's "
            "branch requires with those the destination supplies first by the coordinates "
            "their names declare, read under the route's coordinate map, then one wire of a "
            "role on each side, then equal names where the route's permutation is the "
            "identity, and a marginal value named `d_<coordinate><value>` declares its "
            "coordinate (AMD-COMP-001 §3.3; AMD-SG-030 §1 item 4); a measure is supplied by "
            "the joint law the source's branch writes on the route's state tuple, and "
            "separate marginals supply none"
        )
    }
    shown.update(
        _numbered(
            "join",
            [
                f"{join.label} from {join.source} to {join.target} leaves "
                + ", ".join(_written_name(sort) for sort in unpaired)
                + " unpaired"
                for join, unpaired in undetermined
            ],
        )
    )
    return shown


# --- the view read back: its layers, the place of a node, its wire counts ---


def _document(collection):
    """The view as the JSON document its graph file holds: a `GraphCollection`
    as `dataclasses.asdict` writes it, or, as given, that document as a
    mapping, which the lessons' helper reads from the file and Bellman
    Workbench holds."""
    return collection if isinstance(collection, Mapping) else dataclasses.asdict(collection)


def _graph_nodes(document, graph):
    """The nodes of the graph `graph` of a view's document; a name that is no
    graph of the view is refused."""
    graphs = {entry["id"]: entry["nodes"] for entry in document["graphs"]}
    if graph not in graphs:
        raise ValueError(
            f"The view holds the graphs {' and '.join(graphs)}, and none named {graph!r}."
        )
    return graphs[graph]


def layers_to_open(collection, graph, depth):
    """The namespaces of the layers a page opens on the graph `graph` of the
    view `collection`, a `GraphCollection` or the document of its graph file:
    of each node, the first `depth` parts of its namespace joined by "/",
    each once, in the order of the nodes, so that depth 1 names a stage's
    builders and depth 2 a trellis's stage occurrences. A node whose
    namespace has fewer parts adds none, the two boundary nodes among them."""
    parts = [
        node.get("namespace", "").split("/") for node in _graph_nodes(_document(collection), graph)
    ]
    return tuple(
        dict.fromkeys(
            "/".join(split[:depth]) for split in parts if len(split) >= depth and split[0]
        )
    )


class NodePlace(NamedTuple):
    """Where a node of a view stands: `occurrence`, the stage occurrence of a
    trellis view, `periods[0]/cons`, the period alone for a period's layer,
    and the empty text in a stage view; and `block`, the block of the stage
    file the node was born in, the empty text for a boundary node, a
    refusing node and a field."""

    occurrence: str
    block: str


def node_place(collection, graph, node_id):
    """The `NodePlace` of the node `node_id` of the graph `graph` of the view
    `collection`, or of the layer whose id it is, `policy___group___`
    (`LAYER_ID_ENDING`), read from the namespace the view holds and from no
    spelling of an identity: a trellis namespace opens with the period and
    the stage key, `periods[0]/cons/policy`, and a stage namespace with the
    block, `cntn_to_dcsn/risk_ce`. In an initial diagram, whose fields are
    the nodes, a block's node is its own block and a field's node has none.
    A graph the view does not hold is refused with a ValueError, a node it
    does not hold with a KeyError."""
    nodes = _graph_nodes(_document(collection), graph)
    if node_id.endswith(LAYER_ID_ENDING):
        namespace, node = node_id[: -len(LAYER_ID_ENDING)], None
    else:
        node = next((entry for entry in nodes if entry["id"] == node_id), None)
        if node is None:
            raise KeyError(f"the graph {graph!r} holds no node {node_id!r}")
        namespace = node.get("namespace", "")
    segments = namespace.split("/") if namespace else []
    occurrence = ""
    if segments and segments[0].startswith("periods["):
        occurrence, segments = "/".join(segments[:2]), segments[2:]
    if graph in INITIAL_IDS.values():
        # the layers of an initial diagram are the perches and its nodes the
        # fields and the blocks: a block's node is its own block, nothing
        # else has one; in a trellis's initial diagram (design pass 14 §7)
        # the occurrence is the address the namespace opens with, and a
        # block's id stands under it, `periods[0]/bequest/cntn_to_dcsn`
        kind = (
            ""
            if node is None
            else next(
                (pair["value"] for pair in node.get("attrs") or [] if pair["key"] == "kind"), ""
            )
        )
        block = node_id[len(occurrence) + 1 :] if occurrence else node_id
        return NodePlace(occurrence, block if kind == "block" else "")
    return NodePlace(occurrence, segments[0] if segments else "")


def wire_counts(collection):
    """The wires of each builders graph of the view `collection`, `backward`
    and `forward`, as distinct wire identities: the distinct ports the
    graph's edges leave from, so that a wire two boxes read counts once, 20
    for `cons.bl` over the two graphs; a refused graph counts none. The two
    initial diagrams, whose nodes are fields and blocks, are not counted."""
    return {
        graph["id"]: len(
            {
                edge["sourceNodeOutputId"]
                for node in graph["nodes"]
                for edge in node.get("incomingEdges") or []
            }
        )
        for graph in _document(collection)["graphs"]
        if graph["id"] in DIRECTIONS
    }


# --- the files and the browser window ---


def write_model_explorer(stage_or_trellis, folder):
    """The view of `stage_or_trellis`, what `to_model_explorer` answers,
    written to two JSON files in `folder`, which is made where it does not
    exist; answers their paths in this order: `<stem>.graph.json`, the
    collection, and `<stem>.edge-overlays.json`, the three perch overlays
    (`perch_overlays`) as one `EdgeOverlaysData` named `perches`. The stem
    is the collection's label with each space written as a hyphen, `cons`,
    `cons-methodized` or `trellis`. Each file holds what the viewer loads:
    the collection is read by the viewer's JSON adapter as a model file, and
    the overlays by the viewer's edge-overlay panel from a file. Each file
    holds ASCII alone, every other character, a mathematical letter among
    them, written as the JSON escape of its code point, since the viewer's
    server reads a file in the system's default encoding, which on some
    machines is not UTF-8. The collection is built once, and the overlays
    are read from it."""
    return _write_view(to_model_explorer(stage_or_trellis), folder)


def _write_view(collection, folder):
    """The two files of the view `collection`, written into `folder` as
    `write_model_explorer` describes; answers their paths."""
    graph_builder = _viewer()
    overlays = graph_builder.EdgeOverlaysData(
        name="perches", overlays=_collected_overlays(graph_builder, collection)
    )
    documents = (dataclasses.asdict(collection), dataclasses.asdict(overlays))
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stem = collection.label.replace(" ", "-")
    paths = tuple(folder / f"{stem}{ending}" for ending in FILE_ENDINGS)
    for path, document in zip(paths, documents, strict=True):
        # ASCII alone, each other character as its escape, which the viewer's
        # server reads alike under any code page
        text = json.dumps(document, ensure_ascii=True, indent=1)
        path.write_text(text + "\n", encoding="ascii")
    return paths


def explore(stage_or_trellis, *, folder=None, open_browser=True, port=VIEWER_PORT):
    """Write the view of `stage_or_trellis` to its two files
    (`write_model_explorer`) and open it in the default browser; answers the
    paths of the files and the address of the view, `(paths, url)`. The
    files are written into `folder`, by default `model-explorer/` beside the
    file the stage was elaborated from (`_default_folder`). Where
    `open_browser` is true, the address is the page `serve` answers on the
    viewer's server at `port`, with the top-level layers of the graph
    `backward` opened, a stage's builders or a trellis's periods, and a
    trellis located on the period `LOCATED_PERIOD`, the first after the
    terminal period, where the graph holds it, rather than fitted to the
    row of all its periods; two sentences are printed, the address, `The
    view is at <address>.`, and how to see the mathematical labels
    (`SVG_TEXT_SENTENCE`), and the browser is opened at the address from a
    daemon thread, so that a browser run in the console of a machine without
    a display cannot hold the call. Where `open_browser` is false, nothing is
    served and the address is None. Where `serve` starts a server, it waits
    for the server to answer, for `SERVER_WAIT_SECONDS` and at most one
    second more, and the call returns as soon as `serve` answers."""
    target = _default_folder(stage_or_trellis) if folder is None else folder
    collection = to_model_explorer(stage_or_trellis)
    paths = _write_view(collection, target)
    if not open_browser:
        return paths, None
    opened = next(graph for graph in collection.graphs if graph.id == OPENED_GRAPH)
    layers = dict.fromkeys(node.namespace.split("/")[0] for node in opened.nodes if node.namespace)
    located = LOCATED_PERIOD if isinstance(stage_or_trellis, Mapping) else None
    url = serve(
        paths[0],
        port=port,
        graph_id=opened.id,
        layers=tuple(layers),
        located=located if located in layers else None,
    )
    print(f"The view is at {url}.")
    print(SVG_TEXT_SENTENCE)
    threading.Thread(
        target=webbrowser.open, args=(url,), name="Model Explorer browser", daemon=True
    ).start()
    return paths, url


def _default_folder(stage_or_trellis):
    """The folder a view is written to when none is given: `model-explorer/`
    beside the file the stage was elaborated from, where its provenance
    names a file that exists (`source_file`), and otherwise
    `model-explorer/` in the working directory, among them for a trellis."""
    source = source_file(stage_or_trellis) if hasattr(stage_or_trellis, "provenance") else None
    if source and Path(source).is_file():
        return Path(source).parent / "model-explorer"
    return Path("model-explorer")


def serve(graph_path, *, port=VIEWER_PORT, graph_id=None, layers=(), located=None):
    """The address of a page on the viewer's server at `port` of this machine
    that shows the graph `graph_id` of the graph file `graph_path`, where
    None is given the graph `OPENED_GRAPH`, the backward builders graph,
    where the file holds it and the file's first graph otherwise, with the
    layers whose namespaces `layers` names opened, `("policy",)` or
    `("periods[0]",)`, and located on the layer whose namespace `located`
    names, `"periods[1]"`, which the page selects and fits to its window;
    fitted to the whole graph where `located` is None.

    The port is asked first whether the viewer's server answers there
    (`_viewer_answers`), whichever process started it; where it does, no
    server is started, since the page names the graph file by its path and
    the server reads it. Where nothing listens at the port, the
    viewer's `visualize_from_config` runs in a daemon thread, which ends with
    the process and opens no browser itself; the call waits until the server
    answers, for `SERVER_WAIT_SECONDS` and at most one second more, the time
    limit of the request in progress when the wait ends
    (`_wait_until_answered`), and returns either way, printing one sentence
    that names the port where the server has not answered, since a slow
    start may still succeed. A port at which another program answers is
    refused.

    The address is the viewer's own, the page followed by the configuration
    as the query parameter `data`, which names the graph file
    (`ModelExplorerConfig.to_url_param_value`), with the state of the page
    added under `uiState`: the graph shown and the label of its collection,
    read from the graph file, the layer `located` selected, each layer by its
    namespace followed by `LAYER_ID_ENDING`, the viewer's id of a layer, and
    the layers opened. The page fits its window to a node selected in this
    state, and to the whole graph where none is."""
    apis, viewer_config = _viewer_server()
    config = viewer_config.ModelExplorerConfig()
    config.add_model_from_path(str(graph_path))
    collection = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    # the host `VIEWER_HOST` is written out, since a colon between two
    # replacement fields is the form of an identity's spelling, which no
    # module but `native/identity.py` assembles
    # (tests/tools/identity_parse_sites.py)
    page = f"http://localhost:{port}/"
    if not _viewer_answers(port):
        threading.Thread(
            target=apis.visualize_from_config,
            kwargs={
                "config": config,
                "host": VIEWER_HOST,
                "port": port,
                "no_open_in_browser": True,
            },
            name=f"Model Explorer server on port {port}",
            daemon=True,
        ).start()
        if not _wait_until_answered(page):
            print(
                f"The viewer's server on port {port} has not answered within "
                f"{SERVER_WAIT_SECONDS} seconds; if the page does not load, reload it once the "
                "server has started."
            )
    data = json.loads(unquote(config.to_url_param_value()))
    ids = [graph["id"] for graph in collection["graphs"]]
    if graph_id is None:
        # the backward builders graph where the file holds it, as a stage
        # file and a trellis file do; otherwise the file's first graph
        graph_id = OPENED_GRAPH if OPENED_GRAPH in ids else ids[0]
    data["uiState"] = {
        "paneStates": [
            {
                "deepestExpandedGroupNodeIds": [f"{layer}{LAYER_ID_ENDING}" for layer in layers],
                "selectedNodeId": "" if located is None else f"{located}{LAYER_ID_ENDING}",
                "selectedGraphId": graph_id,
                "selectedCollectionLabel": collection["label"],
                "widthFraction": 1,
                "flattenLayers": False,
            }
        ]
    }
    return f"{page}?data={quote(json.dumps(data))}"


def _viewer_answers(port):
    """Whether the viewer's server answers at `port` of this machine: true
    where the route `check_health` answers with the text the viewer's server
    answers there, `VIEWER_HEALTH`, as the viewer itself asks; false where
    nothing listens at the port. A port at which another program answers is
    refused in one sentence, since the viewer's server cannot start there,
    and the viewer, given its default port while another program holds it,
    would take the next free port without saying so."""
    if not _port_in_use(port):
        return False
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://localhost:{port}/check_health", timeout=1) as answer:
            if answer.read().decode("utf-8", "replace") == VIEWER_HEALTH:
                return True
    except (OSError, http.client.HTTPException):
        # an error or no answer at all is not the viewer's answer
        pass
    raise ValueError(
        f"a program other than the viewer's server listens at the port {port}; give the "
        f"view another port with port=, such as port={port + 1}"
    )


def _port_in_use(port):
    """Whether a server listens at `port` on the viewer's host, which the
    viewer's server checks in the same way before it starts."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        return probe.connect_ex((VIEWER_HOST, port)) == 0


def _wait_until_answered(page):
    """Whether the server at the address `page` answered, asked again every
    tenth of a second until `SERVER_WAIT_SECONDS` have passed. Each request
    is given up to one second, so the request in progress when that time
    ends adds up to one second to the wait. An answer with a status of error
    counts as an answer. The request goes to the server directly, not
    through a proxy."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + SERVER_WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            with opener.open(page, timeout=1):
                return True
        except urllib.error.HTTPError as answer:
            # a status of error is an answer
            answer.close()
            return True
        except OSError:
            time.sleep(0.1)
    return False
