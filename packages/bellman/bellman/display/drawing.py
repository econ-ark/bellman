"""The drawing of one graph in Graphviz's DOT language: `to_drawing` answers
a `Drawing`, the DOT source and the labels of the boxes. The drawing reads no
stage. The names the stage gives the wires, the laws and the aggregators its
boxes apply where the box does not name them, and the title are given to it
by the piece's `diagram()`, which composes them from the stage's queries
(`drawing_title`; `bellman.stage.defining_expressions.drawn_wire_names` and
`drawn_laws`). `wire_label` writes the label of a wire, `box_symbol` the
symbol a box shows, and `dot_head` the first lines of a DOT source, which the
drawings of a period and of a trellis write as well
(`factory/trellis_drawings.py`). A `Drawing` is laid out by `graphviz_layout`
beside this module, with `dot` or with the WebAssembly build of Graphviz.
"""

from __future__ import annotations

import dataclasses
from collections import namedtuple

from discopy.frobenius import Bubble, Hypergraph

from bellman.display.graphviz_layout import layout_command, layout_svg
from bellman.graphs.builders_graphs import bundles
from bellman.native.hypergraphs import BellmanHypergraph
from bellman.native.identity import box_identity
from bellman.native.labels import (
    AGGREGATOR_LETTER,
    EXPECTATION_LETTER,
    LAW_OF_MOTION_LETTER,
    box_label,
    function_field,
    function_name,
    is_wiring,
    italic,
    italic_wire_name,
    pulled_back_along,
    value_aggregations_of,
    wire_spelling,
)
from bellman.syntax.vocabulary import PERCH_MARK

# --- the drawing of one graph ---
#
# The values below are the drawing's presentation and are written here and
# nowhere else. Every color is the light-scheme fallback of a `--bf-*` custom
# property of `docs/_stylesheets/extra.css`, save the three perch tints, which
# are the perch hues lightened for a fill, and the two darkened perch strokes,
# which reach the 3:1 that WCAG 2.2 Success Criterion 1.4.11 asks of a
# graphical object (`#007ea8` is the existing token `--bf-cntn-line`). The
# three stroke weights are the overview figures' construction line, flow arrow
# and object edge (`bf.py` of the figure scripts). The type face is the one
# `mkdocs.yml` sets for the site's text; Graphviz documents no comma stack, but
# the Graphviz gallery writes one and the renderer passes it through to the
# SVG.

_DRAWING_FONT = "Inter,Helvetica Neue,Helvetica,Arial,sans-serif"
_INK = "#1f476b"  # --bf-ink: every operator box's stroke and label, the title
_FACE = "#ffffff"  # --bf-face: every operator box's fill
_MUTED = "#64717d"  # --bf-muted: every wire name, every cluster name
_LINE = "#8a96a3"  # --bf-line: every arrow, every cluster border
_REGION = "#f3f6fa"  # --bf-region: the fill of a combining operator
_PORT_STROKE = {"arvl": "#2e8f3b", "dcsn": "#c96f00", "cntn": "#007ea8"}
_PORT_FILL = {"arvl": "#eef9ef", "dcsn": "#fff3e3", "cntn": "#e6f7fd"}
_PORT_STROKE_AT_NO_PERCH, _PORT_FILL_AT_NO_PERCH = "#8a96a3", "#f7fafb"

# The eight kinds of `Identity.OPERATOR_KINDS` a box carries, in four families
# by what the operator does. The families differ by fill and stroke weight
# alone, so that the drawing prints in black and white without loss and the
# three perch hues stay the only colors that carry meaning.
_OPERATOR_FAMILIES = {
    "Pullback": "transport",
    "Pushforward": "transport",
    "Aggregation": "combination",
    "Expectation": "combination",
    "DistributionExtension": "combination",
    "Argmax": "choice",
    "Evaluation": "reference",
    "PolicyInsertion": "reference",
}
_FAMILY_ATTRIBUTES = {
    "transport": {},
    "combination": {"style": "rounded,filled", "fillcolor": _REGION},
    "choice": {"style": "rounded,filled", "fillcolor": _FACE, "penwidth": "1.8"},
    "reference": {"style": "rounded,dashed", "penwidth": "0.9"},
}
# a statement box of an initial diagram and any box that applies no primitive
# operator are drawn as the plain box of the defaults
_FAMILY_AT_NO_OPERATOR = "transport"

_BOX_LABEL_WIDTH, _WIRE_LABEL_WIDTH, _CLUSTER_LABEL_WIDTH = 18, 16, 40
_LABEL_LINES = 2


def to_drawing(graph, *, title=None, wire_names=None, laws=None) -> Drawing:
    """The readable drawing of one graph: every box a rounded box carrying the
    repository's symbol for its operator (`box_symbol`), its family told by
    fill and stroke weight; a block, a builder or a sub-builder bubble drawn
    as a cluster with its name at the top left; a wire with one writing box
    and one reading box drawn as the label of the one arrow between them, a
    branching wire as plain text with no enclosing shape, and a wire the graph
    itself takes or gives as a small filled box in the hue of its perch. The
    drawing reads down the page, and each builder's chain stands in one
    column. It lists the boxes in the order and under the sentences that `str`
    of the graph prints, which are what the card beside it prints and what
    each tooltip carries after the identity. It is built from the native
    objects of the graph and stores nothing on them. An initial diagram of one
    direction is drawn on its own; the two are never drawn together.

    The drawing reads no stage. `wire_names` maps the identity of a wire to
    the name its stage gives it, and `laws` the identity of a box to the law
    or the aggregator it applies at a label or at a policy, `𝑔_keep≻`,
    `𝑔(·, 𝑐)` and `𝐺(·, ·, 𝑐)`, both of which the piece's `diagram()`
    supplies (`defining_expressions.drawn_wire_names`, `drawn_laws`); without
    them a function is named by its field at its coordinates, an
    occurrence's result by its key, a pullback is composed with `𝑔`, a
    push-forward moves the measure along `𝑔` and an aggregation applies
    `𝐺`. `title` is the drawing's title, which `diagram()` writes from the
    graph's level, direction and grain (`drawing_title`); without it the
    drawing carries none."""
    if not isinstance(graph, Hypergraph):
        raise TypeError(
            "to_drawing draws one stored or derived graph, what the attribute graph of a graph "
            "answers, stage.builder.bwd.graph or stage.initial.backward.primitives.graph; got "
            f"{type(graph).__name__}"
        )
    bundled = bundles(graph)
    writers, readers = _incidences(graph, bundled)
    inputs = _DrawingInputs(
        bundled=bundled,
        names=wire_names or {},
        laws=laws or {},
        value_aggregations=value_aggregations_of(graph),
        writers=writers,
        readers=readers,
        ports={_drawn_wire(bundled, ob.identity) for ob in graph.dom.inside + graph.cod.inside},
    )
    written = _WrittenParts(sorts=drawn_sorts(graph))
    lines = []
    for ob in graph.dom.inside + graph.cod.inside:
        _wire_node(inputs, written, ob, lines)
    _draw_part(inputs, written, graph, 0, lines)
    edges = written.edges + _arrow_label_edges(written.arrow_labels)
    source = "\n".join(dot_head(title) + lines + list(dict.fromkeys(edges)) + ["}"]) + "\n"
    return Drawing(source, written.labels)


# What one drawing reads: the bundles of the graph (`builders_graphs.bundles`),
# the names the stage gives the wires, the law each pullback is composed with,
# the value aggregations of the graph, the boxes that write and that read each
# wire, and the wires the graph itself takes or gives.
_DrawingInputs = namedtuple(
    "_DrawingInputs", "bundled names laws value_aggregations writers readers ports"
)


@dataclasses.dataclass
class _WrittenParts:
    """The parts of one drawing written so far: the sort of every wire met,
    the label of each box in the order drawn (`Drawing.labels`), the name of
    each wire's node, the wires drawn as arrow labels, and the edges."""

    sorts: dict
    labels: list = dataclasses.field(default_factory=list)
    wires: dict = dataclasses.field(default_factory=dict)
    arrow_labels: dict = dataclasses.field(default_factory=dict)
    edges: list = dataclasses.field(default_factory=list)


def _drawn_wire(bundled, identity):
    """The wire a wire is drawn as: a bundle's first component, which is the
    wire the label of the whole bundle stands on."""
    return bundled.get(identity, (identity,))[0]


def _incidences(graph, bundled):
    """The boxes that write and the boxes that read each wire, by the wire it
    is drawn as, over the whole graph and the bubbles inside it, each box by
    its place in the order met and counted once however many of one wire's
    ends it holds. A bubble repeats the wires of the boxes inside it and is no
    further writer or reader (`builders_graphs.bundles`)."""
    writers, readers = {}, {}
    for at, box in enumerate(_operator_boxes(graph), start=1):
        for ob in box.dom.inside:
            readers.setdefault(_drawn_wire(bundled, ob.identity), set()).add(at)
        for ob in box.cod.inside:
            writers.setdefault(_drawn_wire(bundled, ob.identity), set()).add(at)
    return writers, readers


def _operator_boxes(part):
    """The boxes of a graph or a bubble's interior that are neither wiring nor
    bubbles, depth first, the interior of each bubble in its place."""
    for box in part.to_diagram().boxes if isinstance(part, Hypergraph) else part.boxes:
        if is_wiring(box):
            continue
        if isinstance(box, Bubble):
            yield from _operator_boxes(box.arg)
            continue
        yield box


def _wire_role(identity, inputs):
    """How a wire is drawn: `port` where the graph itself takes or gives it,
    or where no box in the drawing writes it or none reads it; `branch` where
    two or more boxes write it or two or more read it; `arrow` where one box
    writes it and one box reads it, which is the label of the arrow between
    them and no node at all."""
    if (
        identity in inputs.ports
        or not inputs.writers.get(identity)
        or not inputs.readers.get(identity)
    ):
        return "port"
    if len(inputs.writers[identity]) > 1 or len(inputs.readers[identity]) > 1:
        return "branch"
    return "arrow"


def _wire_node(inputs, written, sort, lines):
    """The name of the wire, its node written into `lines` where it keeps
    one. A value bundle is one wire labeled with its components in the
    order the box that writes them lists them, known by that label and by no
    weight of its own."""
    written.sorts.setdefault(sort.identity, sort)
    identity = _drawn_wire(inputs.bundled, sort.identity)
    if identity in written.wires:
        return written.wires[identity]
    written.wires[identity] = name = f"w{len(written.wires)}"
    components = inputs.bundled.get(sort.identity, (sort.identity,))
    label = ", ".join(
        wire_label(written.sorts[member], inputs.names.get(member))
        for member in components
        if member in written.sorts
    ) or wire_label(sort, inputs.names.get(sort.identity))
    spelled = ", ".join(str(component) for component in components)
    # the three perches are the only ones a color is given to; a shock and
    # a wire at no perch are alike here
    perch = next(
        (
            component.perch
            for component in components
            if getattr(component, "perch", None) in _PORT_STROKE
        ),
        None,
    )
    drawn = _wire_role(identity, inputs)
    if drawn == "arrow":
        written.arrow_labels[identity] = _ArrowLabel(
            label=label, spelled=spelled, perch=perch, sources=[], targets=[]
        )
        return name
    attributes = {
        "label": _clipped(label, _WIRE_LABEL_WIDTH, _LABEL_LINES),
        "tooltip": f"{spelled} — {label}",
        "fontsize": "9",
        "fontcolor": _MUTED,
        "class": f"wire-{perch or 'none'}",
    }
    if drawn == "port":
        # the graph's inputs and outputs are the only colored objects in
        # the drawing, and the perch stands in the wire's own name as well
        attributes |= {
            "shape": "box",
            "style": "rounded,filled",
            "margin": "0.08,0.035",
            "height": "0.26",
            "color": _PORT_STROKE.get(perch, _PORT_STROKE_AT_NO_PERCH),
            "fillcolor": _PORT_FILL.get(perch, _PORT_FILL_AT_NO_PERCH),
            "penwidth": "1.2",
            "fontcolor": _INK,
        }
    else:
        attributes |= {"shape": "plaintext", "margin": "0.04,0.02", "height": "0.2"}
    lines.append(f"  {dot_quoted(name)}{dot_attributes(attributes)};")
    return name


# A wire drawn as the label of the arrows from the boxes that write it to the
# boxes that read it: its label, its identities as the tooltip spells them,
# the perch of its color, and the two lists of box nodes.
_ArrowLabel = namedtuple("_ArrowLabel", "label spelled perch sources targets")


def _draw_part(inputs, written, part, depth, lines):
    """The statements of a graph or of a bubble's interior, written into
    `lines`: a node for each wire of its own that no box takes or gives, then
    each box in order, a bubble as a cluster and any other box as a node with
    its arrows."""
    graph = part if isinstance(part, Hypergraph) else BellmanHypergraph.from_diagram(part)
    own = {ob.identity for ob in graph.dom.inside} | {ob.identity for ob in graph.cod.inside}
    for spider in graph.spider_types:
        for ob in spider.inside:
            if ob.identity not in own:
                _wire_node(inputs, written, ob, lines)
    for box in part.to_diagram().boxes if isinstance(part, Hypergraph) else part.boxes:
        if is_wiring(box):
            continue
        written.labels.append("  " * depth + box_label(box, inputs.value_aggregations))
        if isinstance(box, Bubble):
            _draw_bubble(inputs, written, box, depth, lines)
        else:
            _draw_box(inputs, written, box, lines)


def _draw_bubble(inputs, written, box, depth, lines):
    """A bubble as a cluster, numbered by the boxes labeled when its
    interior is drawn, with its name at the top left."""
    for ob in box.dom.inside + box.cod.inside:
        _wire_node(inputs, written, ob, lines)
    inner = []
    _draw_part(inputs, written, box.arg, depth + 1, inner)
    # a builder bubble is a line and a name; a sub-builder nested
    # inside one is dashed and lighter. No cluster is filled: a
    # group is marked by a line and by the space around it, which
    # leaves the region tint free to mean that a box combines
    weight = (
        'style="rounded" color="{0}" penwidth="1"'
        if depth == 0
        else 'style="rounded,dashed" color="{0}" penwidth="0.8"'
    ).format(_LINE)
    lines.append(f"  subgraph {dot_quoted(f'cluster_{len(written.labels)}')} {{")
    label = _clipped(box_label(box, inputs.value_aggregations), _CLUSTER_LABEL_WIDTH, 3)
    lines.append(
        f"    graph [label={dot_quoted(label)} "
        f'labelloc="t" labeljust="l" fontsize="9" fontcolor={dot_quoted(_MUTED)} '
        f'margin="7" {weight}];'
    )
    lines.extend("  " + line for line in inner)
    lines.append("  }")


def _draw_box(inputs, written, box, lines):
    """A box as a node, numbered by the boxes labeled so far, showing its
    symbol (`_box_text`) and its family, with an arrow to or from each of its
    wires."""
    node = f"b{len(written.labels)}"
    identity = box_identity(box)
    family = box_family(box)
    symbol = box_symbol(box, inputs.value_aggregations, inputs.laws.get(identity))
    attributes = {
        "label": _box_text(box, symbol),
        "tooltip": f"{box.name} — {box_label(box, inputs.value_aggregations)}",
        "class": f"op-{family}",
    }
    if identity.block:
        # the block keeps a builder's chain in one column, so that its
        # wires are drawn as straight vertical lines
        attributes["group"] = identity.block
    attributes |= _FAMILY_ATTRIBUTES[family]
    # `class` has no effect on the rendering; it lets the site's
    # stylesheet theme the drawings later
    lines.append(f"  {dot_quoted(node)}{dot_attributes(attributes)};")
    for ob in box.dom.inside:
        _join(inputs, written, node, ob, lines, writing=False)
    for ob in box.cod.inside:
        _join(inputs, written, node, ob, lines, writing=True)


def _box_text(box, symbol) -> str:
    """The text of a box's node, `symbol` being the box's symbol. An
    evaluation's symbol stands on one line where it fits one line of a box,
    and otherwise its parts stand one to a line, the count of the outputs it
    does not name on a line of its own (`_evaluation_parts`), each line whole
    however long, so that no output the box names is cut. Any other symbol
    stands on at most two lines of a box (`_clipped`)."""
    if _operator_kind(box) != "Evaluation":
        return _clipped(symbol, _BOX_LABEL_WIDTH, _LABEL_LINES)
    # a line is measured in characters, as `_clipped` measures one
    if len(symbol) <= _BOX_LABEL_WIDTH:
        return symbol
    return "\n".join(_evaluation_parts(box))


def _join(inputs, written, node, ob, lines, *, writing):
    """One end of one wire: an arrow to or from the wire's node where it
    keeps one, and otherwise the box remembered, so that the wire becomes
    the label of the one arrow from its writer to its reader."""
    name = _wire_node(inputs, written, ob, lines)
    identity = _drawn_wire(inputs.bundled, ob.identity)
    if identity in written.arrow_labels:
        arrow = written.arrow_labels[identity]
        (arrow.sources if writing else arrow.targets).append(node)
        return
    written.edges.append(
        f"  {dot_quoted(node)} -> {dot_quoted(name)};"
        if writing
        else f"  {dot_quoted(name)} -> {dot_quoted(node)};"
    )


def _arrow_label_edges(arrow_labels):
    """The arrows of the wires drawn as arrow labels, one from each box that
    writes such a wire to each box that reads it, labeled with the wire."""
    edges = []
    for arrow in arrow_labels.values():
        attributes = {
            "label": _clipped(arrow.label, _WIRE_LABEL_WIDTH, _LABEL_LINES),
            "tooltip": f"{arrow.spelled} — {arrow.label}",
            "class": f"wire-{arrow.perch or 'none'}",
        }
        edges.extend(
            f"  {dot_quoted(source)} -> {dot_quoted(target)}{dot_attributes(attributes)};"
            for source in arrow.sources
            for target in arrow.targets
        )
    return edges


# --- the drawing, and the labels of its wires and boxes ---


class Drawing:
    """A graph drawing with Graphviz DOT text in `source` and the box labels in
    `labels`. `svg()` lays the source out with Graphviz's `dot`, or without it
    with the WebAssembly build of Graphviz that Node runs (`graphviz_layout`),
    and a notebook cell holding the drawing alone shows the picture. Where
    neither program is installed, `svg()` refuses with the sentence that names
    what to install, and the cell shows the short form.

    See `docs/Bellman-Sym/API/stage/02-initial.md` §2."""

    def __init__(self, source, labels):
        self.source, self.labels = source, tuple(labels)

    def __str__(self):
        return "\n".join(self.labels)

    def __repr__(self):
        return f"Drawing of {len(self.labels)} boxes"

    def svg(self) -> str:
        """The drawing laid out as SVG text, by Graphviz's `dot` when it is on
        the PATH and otherwise by the WebAssembly build of Graphviz
        (`graphviz_layout.layout_svg`).

        See `docs/Bellman-Sym/API/stage/02-initial.md` §2."""
        return layout_svg(self.source)

    def _repr_svg_(self):
        """The SVG a notebook shows for the drawing, and None where no layout
        program is available, so that the cell shows the short form."""
        return self.svg() if layout_command() is not None else None


def drawn_sorts(graph) -> dict:
    """The sort of every wire of a graph and of the bubbles inside it, by the
    wire's identity, the first met: the wires a drawing names, so that a
    bundle's label names every component whichever component is drawn first."""
    sorts = {}

    def collect(part):
        graph = part if isinstance(part, Hypergraph) else BellmanHypergraph.from_diagram(part)
        for spider in graph.spider_types:
            for ob in spider.inside:
                sorts.setdefault(ob.identity, ob)
        for box in part.to_diagram().boxes if isinstance(part, Hypergraph) else part.boxes:
            for ob in box.dom.inside + box.cod.inside:
                sorts.setdefault(ob.identity, ob)
            if isinstance(box, Bubble):
                collect(box.arg)

    collect(graph)
    return sorts


def wire_label(sort, name=None) -> str:
    """The label of a wire in a drawing: a measure as `μ`, with its field as a
    subscript where it has one and its perch mark, and no coordinates, `μ≺`,
    `μ_keep≻` (AAS, 10 October 2026, M-D1); any other wire by `name`, the
    name its stage gives it, where one is given
    (`defining_expressions.drawn_wire_names`: a result an occurrence writes by
    its structured expression, every other wire by its value at its
    coordinates, `𝑉≻(a)`); and with no name given, a function by its field and
    perch mark at its coordinates, and any other wire by its field. No label is
    assembled from placeholders."""
    kind, points = (
        getattr(sort, "kind", None),
        tuple(i.stem for i in getattr(sort, "coordinates", ())),
    )
    identity = sort.identity
    if kind == "measure":
        return (
            "μ"
            + (f"_{identity.field}" if identity.field else "")
            + PERCH_MARK.get(identity.perch, "")
        )
    if name is not None:
        return name
    if kind == "function" and points and identity.field:
        return function_name(identity.field, identity.perch) + "(" + ", ".join(points) + ")"
    return wire_spelling(identity)


def box_symbol(box, value_aggregations, law=None) -> str:
    """The symbol a box shows in a drawing: the repository's own spelling of
    the operator, or of the outputs an evaluation produces, read from the
    box's identity and the sorts of its wires, not from the sentence
    `box_label` writes.

    A pullback shows the function it acts on composed with the law of motion,
    `𝑉≻ ∘ 𝑔`; a pullback the construction row holds at a label or at a
    policy is composed with `law`, that label's section as the card writes
    it, `𝑉_kp≻ ∘ 𝑔_keep≻`, or the law at the policy written out, `𝑉≻ ∘ 𝑔(·,
    𝑐)` (RL14), which the stage the drawing is made for supplies
    (`defining_expressions.drawn_laws`), as it supplies the law a
    push-forward at a policy moves the measure along, `𝑔(·, 𝑐)∗μ`, and the
    aggregator an aggregation there applies, `𝐺(·, ·, 𝑐)`; a pullback that
    references no law, the identification of a policy block, shows its
    output composed with the coordinate functions it reads, `𝑐 ∘ 𝑚_d≻`
    (`labels.pulled_back_along`).
    `E Ψ_θ` is the spelling of the stage-wide operator name `E_Ψ_θ`, and
    `argmax · objective` the operator symbol an Argmax row shows, written in
    roman, with the line it is born at. An evaluation shows the outputs it
    produces: the label `wire_label` gives each output with no name given,
    a function by its field and perch mark at its coordinates, the labels
    joined by commas in the order of the box's outputs, `𝑉(m_d), 𝑑𝑉(m_d)`.
    An evaluation with three or more outputs shows the first two and the
    number of the others, `𝑉(a_d, h_d, z_d), 𝑑𝑉_a(a_d, h_d, z_d) and 1 more`.
    A function is written in mathematical italic and everything else in
    roman. A box that applies no primitive operator keeps the label
    `box_label` gives it with the `value_aggregations` of the graph drawn: a
    statement of an initial diagram is named by its address and has no
    symbol.

    The sentence is not lost. It is `box_label(box, value_aggregations)`,
    which `Drawing.labels` keeps, the card prints and the box's tooltip
    carries after the identity."""
    kind = _operator_kind(box)
    identity = box_identity(box)
    along = pulled_back_along(box) if kind == "Pullback" else ()
    if along:
        return (
            f"{', '.join(italic_wire_name(ob) for ob in box.cod.inside)} ∘ "
            f"{', '.join(italic_wire_name(ob) for ob in along)}"
        )
    if kind == "Pullback":
        return f"{_acted_on(box.dom.inside)} ∘ {law if law is not None else LAW_OF_MOTION_LETTER}"
    if kind == "Pushforward":
        return f"{law if law is not None else LAW_OF_MOTION_LETTER}∗μ"
    if kind == "Aggregation":
        applied = law if law is not None else AGGREGATOR_LETTER
        return applied + _statement_mark(identity, occurrence=True)
    if kind == "Expectation" and box.data:
        return (
            f"{EXPECTATION_LETTER} {' and '.join(reference.stem for reference in box.data)}"
            + _statement_mark(identity)
        )
    if kind == "Evaluation":
        return " ".join(_evaluation_parts(box))
    if kind == "Argmax":
        return "argmax" + _statement_mark(identity)
    if kind == "DistributionExtension":
        return f"μ ⊗ {identity.stem}"
    return box_label(box, value_aggregations)


def box_family(box) -> str:
    """The family of the operator a box applies, which fixes the box's fill
    and stroke weight in a drawing: `transport`, `combination`, `choice` or
    `reference` (`_OPERATOR_FAMILIES`). A box that applies no primitive
    operator is drawn as the plain box of the defaults, the transport
    family's."""
    return _OPERATOR_FAMILIES.get(_operator_kind(box), _FAMILY_AT_NO_OPERATOR)


def _operator_kind(box):
    """The kind of the primitive operator a box applies, or None where it
    applies none — a bubble, a statement of an initial diagram. The test is
    `box_label`'s, so that the symbol a box shows and the sentence it keeps are
    read from one kind."""
    identity = box_identity(box)
    if isinstance(getattr(box, "data", None), tuple) and identity.kind not in ("block", "line"):
        return identity.kind
    return None


# the number of outputs an evaluation's symbol names; it counts the others
_NAMED_OUTPUTS = 2


def _evaluation_parts(box) -> list:
    """The parts of an evaluation's symbol, in order: the labels `wire_label`
    gives the box's first two outputs with no name given, each but the last
    of them followed by a comma, and, where the box has more outputs, the
    number of the others, `and 1 more`. `box_symbol` joins the parts by
    spaces, `𝑉(a_d, h_d, z_d), 𝑑𝑉_a(a_d, h_d, z_d) and 1 more`, and the
    drawing writes them one to a line where that one line is longer than a
    line of a box (`_box_text`)."""
    labels = [wire_label(ob) for ob in box.cod.inside]
    named, others = labels[:_NAMED_OUTPUTS], len(labels) - _NAMED_OUTPUTS
    parts = [label + "," for label in named[:-1]] + named[-1:]
    if others > 0:
        parts.append(f"and {others} more")
    return parts


def _acted_on(wires) -> str:
    """The functions a box acts on, named as `box_label` names them: the field
    each wire carries, in mathematical italic with its perch mark."""
    return ", ".join(italic(wire_spelling(function_field(ob.identity))) for ob in wires)


_SUPERSCRIPT_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _statement_mark(identity, occurrence=False) -> str:
    """` · <statement>` where the box's identity is born at one, with a
    superscript digit where the statement holds more than one box of the kind,
    `𝐺 · risk_ce ¹`. The statement and the occurrence are the two the sentence
    names, in the order it names them."""
    if identity.statement is None:
        return ""
    mark = f" · {identity.statement}"
    if occurrence and identity.occurrence is not None:
        mark += " " + str(identity.occurrence).translate(_SUPERSCRIPT_DIGITS)
    return mark


def _clipped(text, width, lines=2) -> str:
    """A label as at most `lines` lines of `width` characters, broken at a
    space; a token longer than the line is broken at the last place within
    the line that falls after a dot or before an opening parenthesis, so that
    `cntn_to_dcsn.marginal` reads `cntn_to_dcsn.` and `marginal`, and
    `𝑉_kp≻(𝑔_keep≻(a_d,` reads `𝑉_kp≻(𝑔_keep≻` and `(a_d,`, rather than
    breaking inside a name; a token with neither is cut at the line, and a
    label still too long is cut at the line and followed by `…`. The parts
    of one token stand together, with no space, where a line holds them.
    The full text is never lost: it stands in `Drawing.labels`, in the card
    beside the drawing and in the box's or the edge's tooltip."""
    words = []  # (part, joined to the part before)
    for word in str(text).split(" "):
        joined = False
        while len(word) > width:
            cuts = [at + 1 for at in range(width) if word[at] == "."] + [
                at for at in range(1, width + 1) if word[at] == "("
            ]
            if not cuts:
                break
            cut = max(cuts)
            words.append((word[:cut], joined))
            word, joined = word[cut:], True
        words.append((word, joined))
    broken, line = [], ""
    for word, joined in words:
        piece = word if not line else line + ("" if joined or line.endswith(".") else " ") + word
        if len(piece) > width and line:
            broken.append(line)
            piece = word
        while len(piece) > width:  # a token no dot divides
            broken.append(piece[:width])
            piece = piece[width:]
        line = piece
    if line:
        broken.append(line)
    if len(broken) <= lines:
        return "\n".join(broken)
    head = broken[:lines]
    head[-1] = head[-1][: max(width - 1, 1)].rstrip() + "…"
    return "\n".join(head)


# --- the title of a drawing ---


def drawing_title(stage_name, level, direction, grain) -> str:
    """The title at the top left of a drawing of one graph of the stage
    `stage_name`, the card's own heading in the register of a figure caption,
    so that the drawing and the card beside it announce themselves alike:
    `level`, `direction` and `grain` name
    the graph as they name it to `graph_of`, the grain by its token or its
    documented spelling. The drawing of the interior of one bubble names no
    graph and takes no title."""
    if level != "builders":
        return f"{stage_name} · {direction} initial diagram"
    return f"{stage_name} · {direction} builders · {grain_word(grain)} grain"


def grain_word(grain: str) -> str:
    """The word a printed line gives a grain. The code token for the authored
    decomposition is `node` and the word for it is `sub-builder`, which is the
    attribute's own name and the word the terminology table uses."""
    return "sub-builder" if grain == "node" else grain


# --- the DOT text, which the period and trellis drawings also write ---


def dot_head(title=None, rankdir="TB"):
    """The first lines of a DOT source in the format of a stage's drawing:
    `digraph {`, the graph attributes (the page, the font, the title where one
    is given), and the node and edge attributes (font, color, weight) every
    box and arrow of `to_drawing` carries.
    `factory.trellis_drawings.diagram_period` writes its source on the same
    lines, so that a period's drawing is in the format of a stage's."""
    settings = [
        f"rankdir={dot_quoted(rankdir)}",
        'bgcolor="white"',
        'pad="0.12"',
        'nodesep="0.18"',
        'ranksep="0.22"',
        f"fontname={dot_quoted(_DRAWING_FONT)}",
        'fontsize="9"',
        f"fontcolor={dot_quoted(_MUTED)}",
        'splines="spline"',
        'compound="true"',
    ]
    if title is not None:
        settings += [
            f"label={dot_quoted(title)}",
            'labelloc="t"',
            'labeljust="l"',
            'fontsize="10.5"',
            f"fontcolor={dot_quoted(_INK)}",
        ]
    return [
        "digraph {",
        "  graph [" + ", ".join(settings) + "];",
        f'  node [fontname={dot_quoted(_DRAWING_FONT)}, fontsize="10", shape="box", '
        f'style="rounded", color={dot_quoted(_INK)}, fontcolor={dot_quoted(_INK)}, '
        'penwidth="1.1", margin="0.09,0.045", height="0.30"];',
        f'  edge [fontname={dot_quoted(_DRAWING_FONT)}, fontsize="9", '
        f'fontcolor={dot_quoted(_MUTED)}, color={dot_quoted(_LINE)}, penwidth="0.9", '
        'arrowsize="0.6", arrowhead="normal"];',
    ]


def dot_attributes(attributes) -> str:
    """The bracketed attribute list of one DOT statement, empty when there are
    none."""
    if not attributes:
        return ""
    return " [" + " ".join(f"{key}={dot_quoted(value)}" for key, value in attributes.items()) + "]"


def dot_quoted(value) -> str:
    """A DOT double-quoted string: backslashes and quotes escaped, line breaks
    written as `\\n`."""
    text = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return '"' + text + '"'
