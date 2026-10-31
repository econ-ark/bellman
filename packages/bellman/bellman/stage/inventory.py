"""The printed inventory of a stage: the stage sheet, the definitions sheet
and the directions of an initial diagram, composed from the stage's queries
and set by `bellman.display.sheets` (AMD-SG-015 §§2-4).

- `stage_sheet`: the stage sheet, what `str(stage)` and `stage.view()` print,
  one section each for the perches, the fields, the blocks, the definitions,
  the graphs, the bindings and the directions; and `version_word`, the
  version of a stage occurrence in one word, which its stamp and its short
  form print.
- `direction_entries` and `directions`: the chains of an initial diagram, as
  label and content pairs and as printed lines, which the stage sheet and the
  card of an initial diagram print.
- `DefinitionsListing` and `definitions_sheet`: the listing
  `stage.definitions.list()` answers and the definitions sheet it prints.

A sheet is written each time it is asked for and is stored nowhere.
"""

from __future__ import annotations

from bellman.display import sheets
from bellman.display.cards import definition_listing, mapping_line
from bellman.display.printed_records import NamedListing
from bellman.fold.block_lines import (
    block_coordinates,
    blocks_in_file_order,
    header_of,
    header_wire_sorts,
    side_perch,
)
from bellman.fold.stage_names import StageNames
from bellman.fold.wire_terms import term_nodes
from bellman.native.identity import Identity
from bellman.native.labels import italic, wire_spelling
from bellman.native.records import DEFINITION_KINDS_TABLE
from bellman.native.versions import kept_answer, stored
from bellman.stage.boxes import builder_rows_of
from bellman.stage.builder_pairs import DIRECTION_WORDS
from bellman.stage.grains import DIRECTIONS, graph_of, graph_refusal, stored_graph_name
from bellman.stage.stage_answers import fields
from bellman.syntax import terms as T
from bellman.syntax.source import comprehension_text, set_text, to_source
from bellman.syntax.vocabulary import (
    DECISION,
    PERCH_SIGN,
    PERCH_WORD,
    VALUE_ROLES,
)
from bellman.typing.typed_expressions import UNDECLARED_SET_TEXT, clauses

# --- the stage sheet ---


# the bindings in the order a stage is bound, calibrate then methodize then
# configure, with the stopping-point word each initial segment reaches
_BINDING_ORDER = (
    ("calibration", "calibration", "calibrated"),
    ("methods", "methods", "methodized"),
    ("settings", "settings", "specified"),
)


def stage_sheet(stage) -> str:
    """The stage sheet (AMD-SG-015 §3), what `str` of an `ElaboratedStage`
    returns: the title block naming the file and calling the object what it is,
    with the version as its stamp; the perches with the fields at each and
    their roles; the same fields by role; the blocks in file order with their
    direction, their inputs, the coordinate they are read at and their outputs;
    the definitions table by kind, with the records of each kind in file order;
    the graphs as present or refused; the three bindings, ruled with dashes
    until every one is made; and the directions the two initial diagrams
    answer."""
    source = stage.provenance.get("path") or stage.provenance.get("origin")
    table = fields(stage)
    bound = all(
        getattr(stage.bindings, attribute) is not None for attribute, _, _ in _BINDING_ORDER
    )
    # the entries of the perches, the fields, the blocks and the graphs are
    # written once: the column the five upper sections share is read from
    # them, and the sections are set from them; the bindings are written whole
    # for the column and again broken at it
    perches = _perch_entries(stage, table)
    by_role = _field_entries(stage, table)
    blocks = _block_lines(stage)
    graphs = _graph_entries(stage)
    bindings = stage.bindings.entries()
    upper = sheets.label_column_width(perches + by_role + blocks + graphs + bindings, separation=1)
    # the column the bindings section's content begins at, so that a settings
    # entry breaks under its own third column and not into the second
    at = sheets.INDENT + sheets.label_column_width(bindings, upper, separation=2)
    return sheets.sheet(
        f"BELLMAN-SYM / STAGE {stage.name}",
        (
            (
                "PERCHES",
                sheets.label_columns(perches, upper, separation=2),
            ),
            ("FIELDS", sheets.label_columns(by_role, upper, separation=2)),
            ("BLOCKS", sheets.label_columns(blocks, upper, separation=2)),
            ("DEFINITIONS", _definition_table(stage)),
            ("GRAPHS", sheets.label_columns(graphs, upper, separation=2)),
            (
                "BINDINGS",
                sheets.label_columns(stage.bindings.entries(at), upper, separation=2),
                bound,
            ),
            ("DIRECTIONS", sheets.label_columns(_direction_entries(stage))),
        ),
        stamp=_version_stamp(stage),
        subtitle=(
            f"a stage occurrence of {source}"
            if source
            else "a stage occurrence, source not recorded"
        ),
    )


def _perch_entries(stage, table):
    """The perches section: each perch's fields with their roles; then one
    line per edge that draws a shock, saying which shocks it draws and
    between which two perches, since a shock belongs to no perch and is
    known only at the later one (AMD-SG-021 §4.1)."""
    entries = []
    for perch, word in PERCH_WORD.items():
        named = [
            f"{wire_spelling(identity)} {sort.role}"
            for identity, sort in table.items()
            if sort.perch == perch
        ]
        entries.append((f"{PERCH_SIGN[perch]} {word}", ", ".join(named) if named else "none"))
    for (source, target), identities in _shocks_by_edge(table).items():
        entries.append(
            (
                f"{PERCH_SIGN[source]} → {PERCH_SIGN[target]}",
                f"{_shocks_drawn(stage, identities)} drawn after {PERCH_WORD[source]}, "
                f"before {PERCH_WORD[target]}",
            )
        )
    return entries


def _shocks_by_edge(table):
    """The shocks each edge draws, by the pair of perches of that edge, in the
    order `fields()` gives them: the one place the sheet groups the shocks
    (AMD-SG-021 §4.1)."""
    found = {}
    for identity, edge in table.edges.items():
        found.setdefault(edge, []).append(identity)
    return found


def _shocks_drawn(stage, identities):
    """The shocks of one edge in the words the sheet writes them: their names
    in declaration order, `Ψ, θ`; a shock whose own law reads another written
    `Ψ given ν` and joined to it by `then`, `ν then Ψ given ν`, so that the
    line says in which order the two are drawn (AMD-SG-021 §4.1; the
    terminology row **shock probability distribution**). Empty where the edge
    draws none. A shock no block reads stands on the edge of the shock whose
    law reads it."""
    names = [identity.field for identity in identities]
    if not names:
        return ""
    parents = _shock_parents(stage, names)
    text = ""
    for place, name in enumerate(names):
        given = parents.get(name, ())
        token = f"{name} given {', '.join(given)}" if given else name
        if not place:
            text = token
        elif any(parent in names[:place] for parent in given):
            text += f" then {token}"
        else:
            text += f", {token}"
    return text


def _shock_parents(stage, names):
    """The shocks of `names` that each shock's own law reads, by name, read
    from the coordinates of the distribution declaration whose subjects hold
    it: `Ψ ~ LogNormal(ν, σ_Ψ)` of `sa_savings.bl` gives `Ψ` the parent `ν`."""
    found = {}
    for definition in stage.definitions.values():
        if definition.kind != "distribution":
            continue
        read = [name for name, _ in definition.coordinates if name in names]
        for subject in definition.equations[0].subjects:
            found[subject] = tuple(name for name in read if name != subject)
    return found

def _field_entries(stage, table):
    """The fields section: the same fields by role, so that the states, the
    controls, the value bundle and the shocks are each read in one line."""

    def by_role(*roles):
        return [
            f"{wire_spelling(identity)} at {PERCH_WORD[sort.perch]}"
            for identity, sort in table.items()
            if sort.role in roles and sort.perch in PERCH_WORD
        ]

    carried = {}
    for perch in PERCH_WORD:
        for identity, sort in table.items():
            if sort.role in VALUE_ROLES and sort.perch == perch:
                carried.setdefault(identity.stem, []).append(perch)
    values = "; ".join(
        f"{name} at every perch"
        if len(set(perches)) == len(PERCH_WORD)
        else f"{name} at the {', '.join(PERCH_WORD.get(perch, perch) for perch in perches)} "
        + ("perches" if len(perches) > 1 else "perch")
        for name, perches in carried.items()
    )
    drawn = [
        f"{_shocks_drawn(stage, identities)}, drawn between {PERCH_WORD[source]} "
        f"and {PERCH_WORD[target]}"
        for (source, target), identities in _shocks_by_edge(table).items()
    ]
    return [
        ("states", ", ".join(by_role("state")) or "none"),
        ("controls", ", ".join(by_role("control")) or "none"),
        ("values", values or "none"),
        ("shocks", "; ".join(drawn) if drawn else "none"),
    ]


def _block_lines(stage):
    """The blocks section: the five blocks in file order with their direction,
    their inputs, the coordinate they are read at and their outputs (§5 item
    6k). The header as the author wrote it stays on the block's own sheet."""
    ports = header_wire_sorts(stage)
    entries = []
    for box in blocks_in_file_order(stage):
        coordinates = block_coordinates(box, ports)
        sides = []
        for declared in header_of(box):
            kept = [ob for ob in declared if ob.identity not in coordinates]
            perch = side_perch(tuple(ob.identity for ob in kept), ports)
            named = [
                wire_spelling(ob.identity) + (f" : !{ob.perch}" if not perch and ob.perch else "")
                for ob in kept
            ]
            sides.append("(" + ", ".join(named) + ")" + (f" : !{perch}" if perch else ""))
        at = "".join(f", at {wire_spelling(identity)}" for identity in coordinates)
        entries.append((f"{block_arrow(stage, box)} {box.name}", f"{sides[0]}{at} -> {sides[1]}"))
    return entries


def block_arrow(stage, box):
    """The arrow of a block's direction, → forward and ← backward (§2)."""
    for direction, arrow in (("forward", "→"), ("backward", "←")):
        graph = getattr(stored(stage, "initial"), direction)
        if (
            not isinstance(graph, tuple)
            and hasattr(graph, "boxes")
            and any(inner.name == box.name for inner in graph.boxes)
        ):
            return arrow
    return " "


# the column the direction word takes in the graphs section: the longer word
# and three spaces after it, as a label column of a card is set
_GRAPH_DIRECTION_COLUMN = 11


def _graph_entries(stage):
    """The graphs section: the initial diagrams present or refused, each with
    the rule a refused one does not satisfy; then each builders graph's
    mapping, its inputs to its outputs named as its card names its wires,
    `(𝑉≻, 𝑑𝑉≻) ↦ (𝑉≺, 𝑑𝑉≺), 𝑐(m_d)`, one direction to a line, as FIELDS
    summarizes `fields()` (AMD-SG-021 §4.3), spelled as the card spells it.
    The mapping is read from
    the graph's signature, which is the card's, without building the card. A
    refused graph of either level reads `refused under <rule>`, the words the
    DIRECTIONS section and the stage's own denotation use for the same fact,
    so that the section says one fact in one form."""
    said = []
    for direction in DIRECTIONS:
        refusal = graph_refusal(stage, "initial", direction)
        said.append(
            f"{direction} refused under {refusal.diagnostic['rule']}"
            if refusal is not None
            else f"{direction} present"
        )
    lines = []
    for direction in DIRECTIONS:
        # a refused graph answers a record whose printed form is the REFUSED
        # sheet (§2.1), so the refusal is read before the record and not from
        # the sheet's first line
        held = graph_refusal(stage, "builders", direction)
        if held is not None:
            text = f"refused under {held.diagnostic['rule']}"
        else:
            graph = getattr(stage.builder, DIRECTION_WORDS[direction])
            text = mapping_line(graph.signature())
        lines.append(f"{direction:<{_GRAPH_DIRECTION_COLUMN}}{text}")
    return [("initial diagrams", ", ".join(said)), ("builders", tuple(lines))]


# the kinds of the definitions table in the terminology's words, never g and G
_RECORD_WORDS = {
    "set": "sets",
    "distribution": "distributions",
    "parameter": "parameters",
    "function": "functions",
    "function_alias": "function aliases",
    "correspondence": "correspondences",
    "g": "laws of motion",
    "G": "value aggregators",
    "line": "block lines",
    "multiplier": "multipliers",
}


def _definition_table(stage):
    """The definitions table of the stage sheet: a header row, a hairline,
    right-aligned counts, and in the last column the records of each kind in
    file order, the laws of motion and the aggregators by their rules so that
    the table says what the model is."""
    kinds, records = 19, 45
    lines = [
        "  " + "kind".ljust(kinds) + "  " + "count".rjust(5) + "   " + "in file order",
        "  " + "─" * kinds + "  " + "─" * 5 + "   " + "─" * records,
    ]
    for kind in DEFINITION_KINDS_TABLE:
        items = [d for d in stage.definitions.values() if d.kind == kind]
        if not items:
            continue
        parts, separator = _records_of_kind(stage, kind, items)
        head = "  " + _RECORD_WORDS[kind].ljust(kinds) + "  " + str(len(items)).rjust(5) + "   "
        broken = sheets.filled(parts, separator, len(head))
        lines.append(head + broken[0].lstrip())
        lines.extend(broken[1:])
    return lines


def _records_of_kind(stage, kind, items):
    """The records of one kind in file order, as the definitions table of the
    stage sheet prints them (AMD-SG-015 §3), and the separator between two of
    them: the sets and the parameters as declared, the plain functions grouped
    by the set they are defined on, the correspondences as maps between sets,
    the laws of motion and the value aggregators by their rules so that the
    table says what the model is, and the block lines by their addresses.

    The records are answered one by one, so that the table breaks between two
    of them and never inside one, a declared set such as `(1, inf)` containing
    a space (§2). A parameter's declared set is written by `clauses`, and a
    semicolon separates two parameters, since a comma stands inside one
    (AMD-SG-019 §5a item 5)."""
    if kind == "set":
        return [f"{d.identity.field} := {to_source(d.equations[0])}" for d in items], ", "
    if kind == "parameter":
        return [
            f"{d.identity.field} : "
            + (
                clauses(d.identity.field, to_source(d.equations[0]))
                if d.equations
                else "no set declared"
            )
            for d in items
        ], "; "
    if kind in ("function", "function_alias"):
        return list(_functions_on(items)), ", "
    if kind == "correspondence":
        return [_correspondence_signature(stage, d) for d in items], ", "
    if kind == "distribution":
        return [d.identity.stem for d in items], ", "
    if kind == "g":
        return [_law_rule(stage, d) for d in items], "; "
    if kind == "G":
        return [_aggregator_rules(stage, d) for d in items], "; "
    return [d.address for d in items], ", "


def _functions_on(items):
    """The plain functions, consecutive ones on one set written together,
    `𝑢, 𝑑𝑢, 𝑑𝑢𝑖𝑛𝑣 on ℝ₊₊`. A plain function declares no range and prints `on`
    its domain until the grammar has a place for one (AMD-SG-015 §2)."""
    groups = []
    for item in items:
        name = italic(item.identity.field)
        space = " × ".join(_declared_sets_of(item.equations[0]))
        if groups and groups[-1][0] == space:
            groups[-1][1].append(name)
        else:
            groups.append((space, [name]))
    return [", ".join(names) + (f" on {space}" if space else "") for space, names in groups]


def _declared_sets_of(core):
    """The declared sets of the parameters of a function or a correspondence
    definition, in the order the author wrote them."""
    declared = []
    for parameter in getattr(core, "params", ()) or ():
        domains = (
            [item for item in parameter.classifiers if isinstance(item, T.Domain)]
            if isinstance(parameter, T.Coordinate)
            else []
        )
        if len(domains) == 1:
            declared.append(set_text(domains[0].space))
    return declared


def _correspondence_signature(stage, definition):
    """A correspondence as a map between sets with the double arrow ⇉ of a
    set-valued map (AMD-SG-015 §2): its domain the declared sets of its
    arguments, its range the declared set of the control it constrains, read
    from the binder that applies it."""
    name = definition.identity.field
    declared = _declared_sets_of(definition.equations[0])
    use = _correspondence_use(stage, name)
    into = UNDECLARED_SET_TEXT
    if use is not None:
        into = (
            _declared_text(
                stage, Identity("field", stage=stage.name, perch=DECISION, field=use[0])
            )
            or UNDECLARED_SET_TEXT
        )
    return f"{name} : {' × '.join(declared) or '()'} ⇉ {into}"


def _correspondence_use(stage, name):
    """The control a correspondence constrains and the binder that applies it:
    `('c', 'cp : Γ(m_d)', 'policy.optimality')` on `cons.bl`, or None where no
    line binds it. The range of a correspondence is an inference from the
    object, and the sheet states it as such (AMD-SG-015 §6 item 9)."""
    for definition in stage.definitions.values():
        if definition.kind != "line":
            continue
        for node in term_nodes(definition.equations):
            if not (isinstance(node, T.Operator) and node.head == "argmax"):
                continue
            for binder in node.subs:
                if not isinstance(binder, T.In):
                    continue
                text = to_source(binder.set)
                if not text.startswith(f"{name}("):
                    continue
                controls = _controls_defined(stage, definition)
                if controls:
                    return controls[0], f"{binder.var} : {text}", definition.address
    return None


def _controls_defined(stage, definition):
    """The names of the controls a line defines on its left side."""
    table = fields(stage)
    found = []
    for equation in definition.equations:
        if not isinstance(equation, T.Equation):
            continue
        left = equation.lhs
        written = (
            [getattr(getattr(left, "symbol", None), "name", None)]
            if getattr(left, "symbol", None) is not None
            else [
                getattr(getattr(item, "symbol", None), "name", None)
                for item in (getattr(left, "items", None) or ())
            ]
        )
        for name in written:
            sort = table.get(Identity("field", stage=stage.name, perch=DECISION, field=name))
            if name and sort is not None and sort.role == "control":
                found.append(name)
    return found


def _declared_text(stage, identity):
    """The declared set of a field, as the source writes it, or None: a named
    set by its name, an anonymous one by its expression, a set declared by
    comprehension by its expression. Read from the definitions table, kept
    nowhere but the memo of this version."""
    texts = kept_answer(stage, "declared sets", dict)
    if identity not in texts:
        ctx = StageNames(stage)
        # the context of the fold is built once and dropped: what is kept is
        # the text of each declared set, which is what this query reads, and
        # not the context, which holds the stage (AMD-SG-018 §4)
        for wanted in (identity,) + tuple(fields(stage)):
            if wanted not in texts:
                texts[wanted] = _set_source(ctx.declared_set(wanted))
    return texts[identity]


def _set_source(declared):
    """The source of a declared set, or None where the declaration names none.
    A set declared by comprehension is written as a declaration's condition
    tail, `ℝ, >= 0, <= 1`, which reads as three factors inside a product; the
    type line writes its body form instead."""
    return (
        None
        if declared is None
        else comprehension_text(declared)
        if isinstance(declared, T.Comprehension)
        else to_source(declared)
    )


def _law_rule(stage, definition):
    """A law of motion by its rule, `a = m_d - c`."""
    return (
        "; ".join(
            to_source(stage.definitions[address].equations[0])
            for address in definition.equations
            if isinstance(address, str) and address in stage.definitions
        )
        or definition.address
    )


_COUNT_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}


def _aggregator_rules(stage, definition):
    """A value aggregator by the rules of its lines, or the count of its
    kernels where it holds one per statement."""
    rows = [
        row
        for row in builder_rows_of(stage, definition.address).closed
        if row.kind == "Aggregation"
    ]
    lines = [
        address
        for address in definition.equations
        if isinstance(address, str) and address in stage.definitions
    ]
    if len(rows) > 1:
        return f"{definition.address}, {_COUNT_WORDS.get(len(rows), len(rows))} kernels"
    return (
        ", ".join(to_source(stage.definitions[address].equations[0]) for address in lines)
        or definition.address
    )


def _direction_entries(stage):
    """The chains the two initial diagrams answer, as label and content pairs.
    The pairs come from `direction_entries`, which knows the word and the wires
    apart; the sheet never recovers them from a joined line.

    A diagram the construction refused has no chains. It takes one line under
    its own direction word, saying that it is refused and under which rule, so
    that the sheet of a stage that elaborates prints whether or not every graph
    was built: a refused diagram is a fact the sheet states, as the graphs
    section states it (AMD-SG-015 §3). The refusal is read from the record that
    holds it, `graph_refusal`, and not from an exception
    of `direction_entries`."""
    entries = []
    for direction in ("forward", "backward"):
        refusal = graph_refusal(stage, "initial", direction)
        if refusal is not None:
            entries.append((direction, f"refused under {refusal.diagnostic['rule']}; see GRAPHS"))
        else:
            entries.extend(direction_entries(stage, direction))
    return entries


def _version_stamp(stage):
    """The stamp of a stage sheet (§2): SYMBOLIC when nothing is bound; the
    stopping-point word CALIBRATED, METHODIZED or SPECIFIED when the bindings
    present are an initial segment of the order calibrate, methodize,
    configure; otherwise the bindings present, listed in that order."""
    return sheets.stamp("VERSION", version_word(stage).upper())


def version_word(stage) -> str:
    """The version of a stage occurrence in one word or a list: symbolic,
    calibrated, methodized, specified, or the bindings present in the order
    calibrate, methodize, configure where they are no initial segment of it."""
    present = [
        (name, word)
        for attribute, name, word in _BINDING_ORDER
        if getattr(stage.bindings, attribute) is not None
    ]
    if not present:
        return "symbolic"
    names = [name for name, _ in present]
    if names == [name for _, name, _ in _BINDING_ORDER[: len(names)]]:
        return present[-1][1]
    return ", ".join(names)


# --- the directions of an initial diagram ---


def direction_entries(stage, direction):
    """The directions of an initial diagram as pairs (AMD-SG-015 §2), the word
    naming a chain and the wires it joins: one pair per chain of blocks in the
    diagram, each block's input wires grouped by perch on one side of the
    direction's arrow and its output wires on the other, two perch groups on
    one side joined by `and`. A shock prints on the arrow of the edge that
    draws it, `→ y drawn →`, and in no perch group, so that the line says what
    is known when: a shock is supplied on an edge between two perches and is
    available at the later one (AMD-SG-021 §4.1). A control read as a
    coordinate is no wire and does not appear.

    The word and the content are answered apart: the sheet sets them in its two
    columns and `directions` joins them, so that a word as wide as the label
    column is never run into the content."""
    _, direction = stored_graph_name("initial", direction)
    graph = graph_of(stage, "initial", direction, "builder")
    table = fields(stage)
    drawn_on = _shocks_by_edge(table)
    arrow = "→" if direction == "forward" else "←"
    entries, used = [], set()
    for chain in _chains(graph):
        sides = [tuple(graph.boxes[chain[0]].dom.inside)]
        sides += [tuple(graph.boxes[index].cod.inside) for index in chain]
        made = [(at, text) for at, text in (_perch_groups(table, side) for side in sides) if text]
        groups = [text for _, text in made]
        # the shocks of the edge between two consecutive sides, read from the
        # two perches those sides stand at (AMD-SG-021 §4.1)
        shocks = [
            _shocks_drawn(stage, drawn_on.get((made[place][0], made[place + 1][0]), ()))
            for place in range(len(made) - 1)
        ]
        if direction == "backward":
            groups, shocks = list(reversed(groups)), list(reversed(shocks))
        text = groups[0] if groups else ""
        for phrase, part in zip(shocks, groups[1:]):
            joined = f"  {arrow} {phrase} drawn {arrow}  " if phrase else f"  {arrow}  "
            text += joined + part
        word = _chain_word(stage, graph, chain, direction, used)
        used.add(word)
        entries.append((word, text))
    return tuple(entries)


def _perch_groups(table, sorts):
    """The perch of one side of a chain and its wires grouped by perch, two
    groups joined by `and`. A shock is no member of a group: it stands on the
    arrow of the edge that draws it."""
    named, at = [], None
    for sort in sorts:
        field = table.get(sort.identity)
        if field is not None and field.role == "shock":
            continue
        mark = PERCH_SIGN.get(field.perch, "") if field is not None else ""
        at = at if at is not None else (field.perch if field is not None else None)
        named.append((mark, wire_spelling(sort.identity)))
    parts, seen = [], {}
    for mark, word in named:
        if mark in seen:
            parts[seen[mark]][1].append(word)
        else:
            seen[mark] = len(parts)
            parts.append((mark, [word]))
    return at, "  and  ".join(f"{mark} {', '.join(words)}".strip() for mark, words in parts)


# the label column of the directions, eleven characters as AMD-SG-014 §1 fixes
# the label column of a card
_DIRECTION_COLUMN = 11


def directions(stage, direction):
    """The directions of an initial diagram, one line per chain, which the
    diagram's own sheet prints under DIRECTIONS and the stage sheet prints for
    both diagrams together (AMD-SG-020 §3.2 item 3): the word of the chain in
    the label column and the wires it joins after it. It joins the pairs of
    `direction_entries` once, and is the only place they are joined."""
    return tuple(
        f"{word:<{_DIRECTION_COLUMN}}{text}" for word, text in direction_entries(stage, direction)
    )


def _chains(graph):
    """The chains of blocks of one initial diagram: each maximal run of blocks
    in which one block's outputs are the next block's inputs, in the order of
    the graph's boxes."""
    producer = {}
    for index, (_, outs) in enumerate(graph.box_wires):
        for wire in outs:
            producer[wire] = index
    following = {}
    for index, (ins, _) in enumerate(graph.box_wires):
        for wire in ins:
            if wire in producer and producer[wire] != index:
                following.setdefault(producer[wire], index)
    heads = [index for index in range(len(graph.boxes)) if index not in set(following.values())]
    chains = []
    for head in heads:
        chain, at = [head], head
        while at in following and following[at] not in chain:
            at = following[at]
            chain.append(at)
        chains.append(tuple(chain))
    return chains


def _chain_word(stage, graph, chain, direction, used):
    """The word naming one chain: `policy` for the chain that produces a
    control, the diagram's own direction for the value or state chain, and the
    first block's name where two chains would take one word."""
    ports = fields(stage)
    produces_control = any(
        ports[sort.identity].role == "control"
        for index in chain
        for sort in graph.boxes[index].cod.inside
        if sort.identity in ports
    )
    word = "policy" if produces_control else direction
    return word if word not in used else graph.boxes[chain[0]].name


# --- the definitions sheet ---


def definitions_listing(stage, table):
    """The definitions listing of AMD-SG-015 §4.6, which `stage.definitions
    .list()` answers: the identities of the records of each kind, in the order
    the kinds first appear. A listing is a printed form, so it gives the
    spelling of each identity and not the record the table is keyed by
    (AMD-SG-016 §3)."""
    found = {}
    for identity, record in table.items():
        found.setdefault(record.kind, []).append(str(identity))
    return DefinitionsListing(
        {kind: tuple(identities) for kind, identities in found.items()}, stage
    )


class DefinitionsListing(NamedListing):
    """The listing `stage.definitions.list()` answers: the identities of the
    records of each kind, in the order the kinds first appear, and, printed,
    the definitions sheet of the stage it holds, one keyed row per record from
    that record's own card (`definitions_sheet`).

    See `docs/Bellman-Sym/API/stage/08-definitions.md` §1."""

    def __init__(self, entries, stage):
        super().__init__(entries)
        self._stage = stage

    def __str__(self):
        return definitions_sheet(self._stage)

    __repr__ = __str__


def definitions_sheet(stage):
    """The keyed definition rows, grouped by kind in retained table order.

    Each row is formatted from the detached answer returned by
    ``definitions.denote`` (`cards.definition_listing`): the key, then the
    record's entry as the `Defines` section of its card lays it out, from
    the column after the key, or under the key where it would pass the
    width there. It therefore uses the definition card's derived types,
    expressions, conditions and generated set declarations instead of
    reconstructing a second mathematical description here.
    """
    sections = []
    for kind in DEFINITION_KINDS_TABLE:
        items = [
            (identity, definition)
            for identity, definition in stage.definitions.items()
            if definition.kind == kind
        ]
        if not items:
            continue
        keys = tuple(str(identity) for identity, _ in items)
        key_width = max(map(len, keys))
        made = tuple(
            line
            for key, (identity, _) in zip(keys, items)
            for line in definition_listing(stage.definitions.denote(identity), key, key_width)
        )
        sections.append((f"{_RECORD_WORDS[kind].upper()} {len(items)}", made))
    return sheets.sheet(
        address_of(stage, "DEFINITIONS"),
        sections,
        stamp=sheets.stamp("RECORDS", len(stage.definitions)),
    )


def address_of(stage, tail):
    return f"BELLMAN-SYM / STAGE {stage.name} / {tail}"
