"""The label one box of a graph shows, a function's name in italic, and the
printed listing of a graph.

A label is read from the box, its name, its references and the sorts of its
wires, and, for an aggregation, from the Evaluation it feeds in the graph that
holds it (`value_aggregations_of`), so that the card, the listing and the
drawing show one label for one box. `graph_text` is what `str` of a stored or
a derived graph returns. `italic` is the one mapping from a letter to its
mathematical italic: a function's name is written in italic, and everything
else in roman. `is_wiring` says whether a box is a spider, a swap, a cup or a
cap, which no label names and no listing shows.
"""

from discopy import frobenius

from bellman.native.identity import Identity, box_identity
from bellman.syntax.vocabulary import PERCH_MARK, VALUE_ROLES


def graph_text(graph) -> str:
    """The printed listing of a graph, which `str` of a stored or a derived
    graph returns: one line per box, in the order its drawing lists them,
    under the label its card and its drawing show (`box_label`); a builder's
    or a sub-builder's bubble is followed by the lines of its interior,
    indented; the wiring is not listed."""
    valued = value_aggregations_of(graph)
    return "\n".join(
        "  " * depth + box_label(box, valued) for depth, box in _boxes_in_order(graph)
    )


def _boxes_in_order(part, depth=0):
    """(depth, box) for every box of a graph or a diagram, in the order of the
    diagram `to_diagram` makes of the graph, a bubble followed by the boxes
    inside it one level deeper; the wiring, a spider, a swap, a cup or a cap,
    is not listed."""
    boxes = part.to_diagram().boxes if isinstance(part, frobenius.Hypergraph) else part.boxes
    for box in boxes:
        if is_wiring(box):
            continue
        yield depth, box
        if isinstance(box, frobenius.Bubble):
            yield from _boxes_in_order(box.arg, depth + 1)


def is_wiring(box) -> bool:
    """Whether a box of a graph or a diagram is wiring, a spider, a swap, a
    cup or a cap, and not an operator, a statement or a builder."""
    return isinstance(box, (frobenius.Spider, frobenius.Swap, frobenius.Cup, frobenius.Cap))


def value_aggregations_of(graph) -> frozenset:
    """The identities of the aggregation boxes of `graph`, at every depth,
    whose G yields value functions at a perch: an Evaluation box reads each
    output of the aggregation, and every output of that Evaluation is a field
    at a perch whose role is a value role. An aggregation writes its result at
    no perch and the Evaluation it feeds writes the field, so whether G yields
    a value function at a perch is read from that Evaluation. `graph` is a
    hypergraph or the diagram inside a bubble; the
    aggregation and the Evaluation it feeds stand in one bubble at every
    grain."""
    boxes = [box for _, box in _boxes_in_order(graph)]
    readers = {}
    for box in boxes:
        for ob in box.dom.inside:
            readers.setdefault(ob.identity, []).append(box)

    def evaluated(ob):
        evaluations = [
            reader
            for reader in readers.get(ob.identity, ())
            if _operator_kind(reader) == "Evaluation"
        ]
        return bool(evaluations) and all(
            getattr(field, "perch", None) is not None
            and getattr(field, "role", None) in VALUE_ROLES
            for evaluation in evaluations
            for field in evaluation.cod.inside
        )

    return frozenset(
        box_identity(box)
        for box in boxes
        if _operator_kind(box) == "Aggregation"
        and box.cod.inside
        and all(evaluated(ob) for ob in box.cod.inside)
    )


def _operator_kind(box):
    """The kind of the primitive operator a box applies, read from its
    identity, or None for a bubble, a statement box or a wiring box."""
    if isinstance(getattr(box, "data", None), tuple) and box_identity(box).kind not in (
        "block",
        "line",
    ):
        return box_identity(box).kind
    return None


# The one mapping from a letter to its mathematical italic:
# Latin capitals at U+1D434, small letters at U+1D44E with small h at U+210E,
# Greek capitals at U+1D6E2 and small letters at U+1D6FC, final sigma included
# in the small run at U+1D70D. Every other character, and a letter already in
# the italic block, is left as it is.
_ITALIC_LATIN_CAPITAL, _ITALIC_LATIN_SMALL = 0x1D434, 0x1D44E
_ITALIC_SMALL_H = 0x210E
_ITALIC_GREEK_CAPITAL, _ITALIC_GREEK_SMALL = 0x1D6E2, 0x1D6FC
_ITALIC = str.maketrans(
    {
        chr(code): chr(_ITALIC_LATIN_CAPITAL + code - ord("A"))
        for code in range(ord("A"), ord("Z") + 1)
    }
    | {
        chr(code): chr(_ITALIC_LATIN_SMALL + code - ord("a"))
        for code in range(ord("a"), ord("z") + 1)
    }
    | {chr(code): chr(_ITALIC_GREEK_CAPITAL + code - 0x0391) for code in range(0x0391, 0x03A9 + 1)}
    | {chr(code): chr(_ITALIC_GREEK_SMALL + code - 0x03B1) for code in range(0x03B1, 0x03C9 + 1)}
    | {"h": chr(_ITALIC_SMALL_H)}
)


def italic(text: str) -> str:
    """A function's name in mathematical italic, letter by letter: `V[>]`
    reads `𝑉[>]`, `dV` reads `𝑑𝑉`, `g` reads `𝑔`, `π` reads `𝜋`. Marks,
    digits, operator glyphs and a letter the author already wrote in italic
    are unchanged, so `𝑢` and `𝑑𝑢𝑖𝑛𝑣`, which a stage file writes in italic,
    read as they were written. A subscript after an underscore is the
    author's spelling and is not set in italic: `u_c_inv` reads `𝑢_c_inv`,
    `h_choice` reads `ℎ_choice`, `dV_f` reads `𝑑𝑉_f`. A field, a state, a
    control, a shock, a parameter, a set and an operator symbol are roman and
    are not passed here."""
    head, underscore, tail = text.partition("_")
    return head.translate(_ITALIC) + underscore + tail


def function_name(field: str, perch=None) -> str:
    """A function's printed name with its perch mark: the letters before a
    subscript in italic, the subscript after the underscore as the file
    writes it, since `d` has no subscript glyph, and the perch mark directly
    after: `𝑉≻`, `𝑚_d≻`, `𝑐`, `𝑑𝑢𝑖𝑛𝑣`, `𝐺_value≻`."""
    head, underscore, tail = field.partition("_")
    return italic(head) + underscore + tail + PERCH_MARK.get(perch, "")


# the italic letters the printed forms are built from, spelled once
LAW_OF_MOTION_LETTER, AGGREGATOR_LETTER, EXPECTATION_LETTER = italic("g"), italic("G"), "E"
_ALONG_G = f"along the law of motion {LAW_OF_MOTION_LETTER}"


# The labels of the operator kinds that take no name from the box: the
# terminology table's description of the operator, in the register of the
# other labels.
_KIND_LABELS = {
    "PolicyInsertion": "Insertion of the policy",
    "Pushforward": f"Push-forward through the law of motion {LAW_OF_MOTION_LETTER}",
}


def box_label(box, value_aggregations) -> str:
    """The label of one box of a graph, which its drawing shows, its card
    names and `str` of the graph lists. It is read from the box, its name,
    its references and the sorts of its wires, and, for an aggregation, from
    the Evaluation it feeds: `value_aggregations` holds the identities
    `value_aggregations_of` answers for the graph that holds the box, and is
    empty where the box is no aggregation. Every printed form passes them,
    so that every printed form shows one label.

    A builder's bubble is labeled by its block id; a sub-builder's bubble by
    its statement's identifier and the function it makes, `risk_ce →
    𝐶𝐸(m_d, ν)`, or in an initial diagram the field it makes, `risk_ce → CE`;
    a statement box of an initial diagram by its address. An operator box is
    labeled by its kind, through the table `_OPERATOR_LABELS`: `Pullback of
    𝑉≻ along the law of motion 𝑔`, naming the function pulled back, and for
    a pullback that references no law of motion, the identification of a
    policy block, `Pullback of 𝑐 along 𝑚_d≻`, naming the map it pulls back
    along; for an aggregation, `Value aggregation 𝐺` where the Evaluation it
    feeds writes value functions at a perch, and `Apply 𝐺` otherwise, for the
    map inside an occurrence, whose result an expectation reads, and for the
    kernel of a policy builder, which yields a candidate control or a
    coordinate; for the other kinds, the terminology table's description of
    the operator in the same register: `Expectation under the distribution of
    Ψ_θ`, `Evaluation of 𝑉`, `Argmax of the statement objective`, `Extension
    of the measure by the distribution of Ψ_θ`, `Insertion of the policy`,
    `Push-forward through the law of motion 𝑔`. The wiring, a spider, a swap,
    a cup or a cap, keeps its own name and is not listed."""
    if is_wiring(box):
        return box.name
    if isinstance(box, frobenius.Bubble):
        return _bubble_label(box)
    label = _OPERATOR_LABELS.get(_operator_kind(box))
    return box.name if label is None else label(box, value_aggregations)


def _bubble_label(box) -> str:
    """A sub-builder bubble's label, its statement's identifier and what the
    statement makes; a builder's or a block's bubble, its block id."""
    if box_identity(box).kind != "line":  # a builder or a block
        return box.name
    made = ", ".join(
        f"{italic(function_wire_name(ob.identity))}({', '.join(a.stem for a in ob.coordinates)})"
        if getattr(ob, "kind", None) == "function"
        else ob.identity.stem
        for ob in box.cod.inside
    )
    return f"{box_identity(box).statement} → {made}"


def pulled_back_along(box) -> tuple:
    """The input wires a pullback box is pulled back along where it references
    no law of motion: the coordinate functions among its inputs, the wires
    whose role is a state, `𝑚_d≻` of the identification `𝑐 ∘ 𝑚_d≻ = 𝑐≻` of a
    policy block, whose output is the function pulled back. Empty for a
    pullback along a law of motion, which references its law, and for any
    other box."""
    references = getattr(box, "data", None)
    if not isinstance(references, tuple) or any(
        isinstance(ref, Identity) and ref.kind == "g" for ref in references
    ):
        return ()
    return tuple(ob for ob in box.dom.inside if getattr(ob, "role", None) == "state")


def italic_wire_name(ob) -> str:
    """The name of a wire an operator reads or writes, in mathematical
    italic: the field of an occurrence's or a builder's result, `𝑐`; the
    field with its perch mark of any other wire, `𝑉≻`, `𝑚_d≻`."""
    identity = ob.identity
    return italic(
        identity.field
        if identity.is_result and identity.field is not None
        else wire_spelling(function_field(identity))
    )


def _pullback_label(box, value_aggregations) -> str:
    """`Pullback of 𝑉≻ along the law of motion 𝑔`, or `along 𝑔 at 𝑐` at a
    policy; `Pullback of 𝑐 along 𝑚_d≻` for a pullback along the coordinate
    functions it reads (`pulled_back_along`), naming its output, the
    function pulled back, and the map."""
    along = pulled_back_along(box)
    if along:
        pulled = ", ".join(italic_wire_name(ob) for ob in box.cod.inside)
        return f"Pullback of {pulled} along {', '.join(italic_wire_name(ob) for ob in along)}"
    acted = ", ".join(italic(wire_spelling(function_field(ob.identity))) for ob in box.dom.inside)
    policies = _policies(box)
    if policies:
        return (
            f"Pullback of {acted} along {LAW_OF_MOTION_LETTER} at "
            f"{', '.join(italic(ref.field) for ref in policies)}"
        )
    return f"Pullback of {acted} {_ALONG_G}"


def _aggregation_label(box, value_aggregations) -> str:
    """`Value aggregation 𝐺` or `Apply 𝐺`, with the statement and the
    occurrence."""
    # G yields value functions at a perch where the Evaluation it feeds
    # writes them there; a candidate control or a coordinate a policy line
    # defines, or a result inside an occurrence, is not a value aggregation
    word = (
        f"Value aggregation {AGGREGATOR_LETTER}"
        if box_identity(box) in value_aggregations
        else f"Apply {AGGREGATOR_LETTER}"
    )
    statement = box_identity(box).statement
    # a builder that holds several aggregations names each by its statement,
    # as the expectation and the argmax labels do, and a statement that
    # folds to several of them names the occurrence its box name carries,
    # so that the listing and the drawing tell every one of them apart
    #
    # a box merged across lines is owned by its builder and names no
    # statement, so its counter, which counts the boxes of that owner, is not
    # read as an occurrence
    if statement is not None:
        word = f"{word} of the statement {statement}"
        if box_identity(box).occurrence is not None:
            word = f"{word}, occurrence {box_identity(box).occurrence}"
    return word


def _expectation_label(box, value_aggregations) -> str:
    """`Expectation of the statement … under the distribution of Ψ_θ`."""
    # an expectation names the statement it integrates, as an aggregation's
    # label does, so that two expectations of one builder never print the
    # same line; a box merged across several lines is owned by the builder
    # and names its distribution alone
    written = box_identity(box).statement
    statement = f" of the statement {written}" if written is not None else ""
    distributions = tuple(ref for ref in box.data if ref.kind == "distribution")
    return (
        f"Expectation{statement} under the distribution of "
        f"{' and '.join(r.stem for r in distributions)}"
        if distributions
        else f"Expectation{statement}"
    )


def _evaluation_label(box, value_aggregations) -> str:
    """`Evaluation of 𝑉, 𝑑𝑉`, naming the evaluated outputs."""
    return f"Evaluation of {', '.join(italic_wire_name(ob) for ob in box.cod.inside)}"


def _argmax_label(box, value_aggregations) -> str:
    """`Argmax of the statement objective`, naming the line that writes the
    maximization; `Argmax` where the box's identity is born at no line."""
    statement = box_identity(box).statement
    return "Argmax" if statement is None else f"Argmax of the statement {statement}"


def _extension_label(box, value_aggregations) -> str:
    """`Extension of the measure by the distribution of Ψ_θ`."""
    return f"Extension of the measure by the distribution of {box_identity(box).stem}"


def _pushforward_label(box, value_aggregations) -> str:
    """`Push-forward through the law of motion 𝑔`, or `through 𝑔 at 𝑐` at a
    policy."""
    policies = _policies(box)
    if policies:
        return (
            f"Push-forward through {LAW_OF_MOTION_LETTER} at "
            f"{', '.join(italic(ref.field) for ref in policies)}"
        )
    return _KIND_LABELS["Pushforward"]


def _named_label(box, value_aggregations) -> str:
    """The label of a kind that takes no name from the box (`_KIND_LABELS`)."""
    return _KIND_LABELS[_operator_kind(box)]


# The label of each operator kind, which `box_label` reads; a kind absent
# from the table is labeled by its box's name.
_OPERATOR_LABELS = {
    "Pullback": _pullback_label,
    "Aggregation": _aggregation_label,
    "Expectation": _expectation_label,
    "Evaluation": _evaluation_label,
    "Argmax": _argmax_label,
    "DistributionExtension": _extension_label,
    "PolicyInsertion": _named_label,
    "Pushforward": _pushforward_label,
}


def _policies(box) -> tuple:
    """The policies an operator box is applied at: the function identities
    among its references."""
    return tuple(
        ref
        for ref in (getattr(box, "data", ()) or ())
        if isinstance(ref, Identity) and ref.kind == "function"
    )


def wire_spelling(identity) -> str:
    """A field wire's name with its perch mark, `m≻` for `port:cntn:m`; the
    spelling of any other wire."""
    if identity.kind == "field":
        return identity.field + PERCH_MARK.get(identity.perch, "")
    return str(identity)


def function_field(identity):
    """The field a function wire carries: `cons:function:cntn:V` and
    `cons:choice:dcsn:V` are the fields `cons:cntn:V` and `cons:dcsn:V`."""
    if identity.kind in ("function", "choice") and identity.perch is not None:
        return Identity("field", stage=identity.stage, perch=identity.perch, field=identity.field)
    return identity


def function_wire_name(identity) -> str:
    """The field a function wire is named by,
    `cons:choice:dcsn:dV:cntn_to_dcsn.marginal` and `cons:function:dcsn:dV`
    both `dV`; the name another wire carries."""
    return (
        identity.field
        if identity.kind in ("function", "choice") and identity.perch
        else identity.stem
    )
