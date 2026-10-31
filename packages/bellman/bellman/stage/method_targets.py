"""Where a numerical method attaches in a stage: the targets of a methods file
(spec 0.3c §3.4, §4.3).

A target is a place in the stage where a numerical method attaches. The
places a stage has are: a builder — a whole forward step over states
(`arvl_to_dcsn`, `dcsn_to_cntn`), a whole backward step over values
(`cntn_to_dcsn`, `dcsn_to_arvl`), or the policy between them; a line the
modeler named with `[id=…]`; an operator inside a line — the expectation over
the shocks in `V = E_{Ψ,θ}(V[>])`, the root of a first-order condition in
`ς = solve_{ς}(…)`, the `solve` that an implicit statement `c = c[>]`
records, an `argmax`, an `upper_env`, an authored interpolation
`evaluate(…)`; and the representation of a value function among a backward
builder's outputs, the boundary representation — the interpolation that makes
the value function V(m) of the decision state from the value field computed
on the perch grid. A methods file names one place per entry (`on: policy`,
`on: E_Ψ_θ`, `on: policy.foc.solve`, `on: evaluate`), and `methodize` records
the entry's method in the stage's `methods`, the one record of attachments.
This module resolves a name to its place (`resolve_target`), lists the places
a stage has (`target_inventory`), and tells a line attached to another as its
property (`is_property`, `properties_of`).

The places in the graph. A builder is a `Builder` bubble of the stage
hypergraph; a `!node` line is a bubble inside its builder, named by the
line's address; every other line is a box named by its address inside the
bubble that holds it; an operator occurrence is a query on the line's
retained term; the boundary representation is a marker beside the backward
builder (`ValueRepresentation`). A target resolves by these rules:

(a) `<block-id>` is the builder box (`policy`, `dcsn_to_cntn`). The
    spelling `<block-id>_builder` names the same box when the block is a
    forward block, and is refused for a backward builder or the policy,
    which have no forward builder. The resolution is the very box object, so
    that two spellings that reach one place compare identical.
(b) `<block-id>.<statement-id>` is the node bubble when that line
    carries `!node`.
(c) `<block-id>.<statement-id>` is otherwise the line, returned as
    `(holder, Line)` with the box that holds it: the builder bubble for a
    line at the block level, the node bubble for an alias folded into a node.
    An output line, an alias and a `!doc` line are all addressable this way;
    an alias or a `!doc` line with no operator occurrence (`policy.InvEuler`)
    resolves for inspection only — it is not a method target, and
    `methodize` refuses a method on it (spec 0.3c §4.3: "an alias with no
    operator in it is not a method target"). An output statement with no
    operator occurrence — `cntn_to_dcsn.value`, `cntn_to_dcsn.marginal` in
    `cons` — names the representation of the output field it defines on the
    decision-perch grid; a method on it (the `!Cartesian` entry) is held in
    `methods` under the statement's address. A positional address
    `<block-id>.<n>` — the address of a line without an id — is refused with
    a request for an id: an inserted `!doc` line would renumber what follows.
    A line whose id is dotted, `x.y`, is attached to the line `x` of its
    block as a property (`optimality.euler`, the first-order condition of the
    maximization `optimality`): it forms no operation and is no place of its
    own, so no inventory lists it and a target naming it is refused. A dotted
    id whose block holds no line `x` is refused where the stage is
    constructed.
(d) `<operator>` — the stage-wide name of an operator, `E_` followed by its
    shock names in the authored order (`E_Ψ_θ`, `E_θ`), or `solve`, `argmax`,
    `upper_env` — is every occurrence of that operator in the stage, each as
    (the box holding the line, the line, the occurrence), in source order;
    one method then governs them all. `evaluate` has its own rule, (g); `D`
    occurs only in top-level definitions (below). A `!doc` line records no
    occurrence. A name that no statement records is refused naming the
    occurrences the stage has and, where the operator is written in a `!doc`
    line, naming that line and the block's defining statements: no operator
    is derived from a method name, and `upper_env` is an occurrence only
    where authored.
(e) `<block-id>.<statement-id>.<operator>` is the one occurrence of that
    operator in that line; the line must carry an id, and a line with two
    occurrences of one operator is refused naming both, since no finer
    address exists (the stage-wide name governs both). A line that carries
    no occurrence of the named operator is refused naming where a method
    attaches.
(f) Resolution is method-blind: a block id is the builder box under (a)
    whatever the entry's method. `methodize`, which reads the method table
    (`method_table.METHOD_TYPES`), moves a method whose placement rule stands
    inside the builder to its place there: `!egm` to the Evaluation that
    closes a policy block which writes the grid line, or to the maximization
    that carries its first-order condition as a property; a representation
    to the closing Evaluation.
(g) `evaluate`: in a stage that authors exactly one `evaluate` occurrence,
    that occurrence, in the form of (d); in a stage that authors two or more,
    refused naming their addresses `<block-id>.<statement-id>.evaluate`; in a
    stage that authors none and has no implicit statement (`port`, `noport`,
    `disc`), the boundary representation of the backward builder from the
    continuation perch to the decision perch — the builder that writes the
    decision-perch value fields, `cntn_to_dcsn` — returned as (that
    box, `ValueRepresentation`); in a stage with an implicit statement and
    no authored occurrence (`cons`, `cons_savings_iid`), refused naming the
    implicit statement.
(h) A comma-separated entry is not one target: each part is an entry of its
    own, and `resolve_target` receives one target.

A target that reaches two places — two lines with one id, which only a
decoded saved term can carry to construction, since a fresh parse refuses
them (`bellman.syntax.lower.parse_with_spans`) — is refused naming both places.

Every refusal is a `TargetError` of `bellman.refusals`, a `LookupError`, under
one rule of its `TARGET_RULES`, whose message names the target, the stage,
the rule that failed, and the places the stage has, and which carries them as
attributes (`target`, `stage`, `rule`, `candidates`). `methodize` raises
every such refusal.

Source order. The order of the inventory and of every stage-wide resolution
is the order of the builder boxes in the hypergraph, which is the textual
order of the blocks (`construction._builder_boxes`), each block's lines by
their place in the block, a line folded into a node included.

An operator occurrence inside a top-level function definition (the
derivative `D_{c}(𝑢)` of `𝑑𝑢 := D_{c}(𝑢)`) is held in the stage annotation,
not in a box; a definition is a named function inlined where it is used
(spec 0.3c §4.3), and this module resolves no target to it.
"""

from __future__ import annotations

import dataclasses as _dc

from bellman.fold.block_lines import (
    blocks_of,
    header_wire_sorts,
    is_implicit_solve,
    node_address,
    perches_of,
    require_stage,
    symbol_groups,
)
from bellman.fold.stage_names import lines_of
from bellman.native.identity import Identity
from bellman.native.records import ValueRepresentation
from bellman.refusals import (
    RULE_A,
    RULE_B_C,
    RULE_D,
    RULE_E,
    RULE_FORM,
    RULE_G,
    RULE_H,
    RULE_II,
    RULE_TWO,
    TargetError,
)
from bellman.syntax import terms as T
from bellman.syntax.source import to_source
from bellman.syntax.vocabulary import (
    CONTROL,
    DOC,
    NODE,
    OUTPUT_LINE,
    PERCHES,
    VALUE,
)
from bellman.typing.line_unknowns import OPERATOR_VOCABULARY, occurrence_paths

# --- a target's place, the targets of a stage, the properties of a line ---


def resolve_target(stage, target):
    """The place in `stage` that the methods-file target `target` names.

    A builder box for a block id or its `_builder` spelling (a); a node bubble
    for a `!node` line (b); `(holder, Line)` for any other line named by
    `<block-id>.<statement-id>`, the holder being the bubble that holds the
    line's box (c); a tuple of `(holder, Line, OperatorOccurrence)` for a
    stage-wide operator name, one entry per occurrence in source order (d);
    one such triple for an occurrence address (e); for `evaluate`, the one
    authored occurrence as a one-entry tuple, a refusal naming the occurrence
    addresses when the stage authors two or more, or `(box,
    ValueRepresentation)` for the backward builder's boundary
    representation (g). A block id is the builder box whatever method the
    entry carries (f). A name that reaches no place, a positional address, a
    comma-separated entry, a property of a line, or a name that reaches two
    places raises `TargetError`; an argument of the wrong type raises
    `TypeError`.
    """
    require_stage(stage)
    if not isinstance(target, str):
        raise TypeError(
            f"a target is the string written after `on:` in a methods file; "
            f"got {type(target).__name__}"
        )
    if "," in target:
        _refuse(
            stage,
            target,
            RULE_H,
            (
                "lists several targets separated by commas, and an entry names one "
                "target (spec 0.3c §4.3: a comma-containing string is not an "
                "operator identifier); the migration L02 splits such an entry, "
                "and each part resolves on its own"
            ),
        )
    parts = target.split(".")
    if not target or any(part == "" for part in parts) or len(parts) > 3:
        _refuse(
            stage,
            target,
            RULE_FORM,
            (
                "is not the form of a target: a block id, `<block-id>."
                "<statement-id>`, `<block-id>.<statement-id>.<operator>`, a "
                "stage-wide operator name, or `evaluate`"
            ),
        )
    if len(parts) == 1:
        return _resolve_name(stage, target)
    if len(parts) == 2:
        return _resolve_line(stage, target, *parts)
    return _resolve_occurrence(stage, target, *parts)


def target_inventory(stage):
    """Every target string of `stage`, in source order: each builder box,
    then, line by line, the box's lines that carry `[id=…]` — a node bubble or
    a line — each followed by the addresses of its operator occurrences; then
    the stage-wide operator names in first-occurrence order, `evaluate` among
    them only when the stage authors exactly one occurrence; then `evaluate`
    where rule (g) admits the boundary representation; then the authored
    functions. A line without an id is not listed (its address is
    positional), nor is the `_builder` spelling."""
    require_stage(stage)
    inventory = tuple(_TargetInventory(stage).inventory)
    functions = tuple(
        name for name in symbol_groups(stage).get("functions", ()) if name not in inventory
    )
    return inventory + functions


def is_property(lines, record) -> bool:
    """Whether a line is attached to another line of its block as a property:
    its id is dotted, `x.y`, and the block holds the line `x`, whose address
    is the line's own address up to its last dot (`optimality.euler` is a
    property of the maximization `optimality`). A property forms no operation
    and is no place of its own; a dotted id whose block holds no line `x` is
    refused where the stage is constructed. `lines` is the block's
    `(holder, Line)` pairs, as `lines_of` answers them."""
    owner = _owner_address(record)
    return any(other.address == owner for _, other in lines)


def properties_of(stage, box, address) -> tuple:
    """The lines attached as properties to the line at `address` of the
    builder `box`, in the order of the lines: the first-order condition
    `optimality.euler` of the maximization `policy.optimality`."""
    return tuple(record for _, record in lines_of(stage, box) if _owner_address(record) == address)


def _owner_address(record):
    """The address a line would be attached to as a property: its own address
    up to its last dot (`policy.optimality` for `policy.optimality.euler`),
    which is the address of a line of the block only where the line's id is
    dotted."""
    return record.address.rpartition(".")[0]


# --- resolution by rule ---

# The suffix of the spelling `<block-id>_builder` of a forward block's
# target, which names the forward builder.
BUILDER_SUFFIX = "_builder"


# The boundary-representation spelling, a target name with a rule of its own.
EVALUATE = "evaluate"


def _resolve_name(stage, name):
    """A one-part target: a builder box (a), a stage-wide operator (d), or
    `evaluate` (g); a name that reaches two of these is refused."""
    builders = {box.name: box for box in blocks_of(stage)}
    found = []  # (what the name reaches, the resolution)
    if name in builders:
        found.append((f"the builder box {name!r}", builders[name]))
    definition = next(
        (
            d
            for d in stage.definitions.values()
            if d.identity
            in (
                Identity("function", stage=stage.name, field=name),
                Identity("correspondence", stage=stage.name, field=name),
            )
            and getattr(d, "kind", None) in ("function", "function_alias", "correspondence")
        ),
        None,
    )
    if definition is not None:
        # a method attaches to an authored function at its definition
        found.append((f"the definition of {name!r}", ("definition", definition)))
    if name.endswith(BUILDER_SUFFIX) and name[: -len(BUILDER_SUFFIX)] in builders:
        box = builders[name[: -len(BUILDER_SUFFIX)]]
        if not _is_transition(stage, box):
            transitions = [b.name for b in blocks_of(stage) if _is_transition(stage, b)]
            _refuse(
                stage,
                name,
                RULE_A,
                (
                    f"carries the retired suffix `_builder`, which names the forward "
                    f"builder of a transition block, and {box.name!r} is "
                    f"{_what_block_is(stage, box)}, which has no forward builder; "
                    f"the transition blocks are "
                    f"{', '.join(transitions) or 'none'}"
                ),
            )
        found.append((f"the builder box {box.name!r} under the suffix `_builder`", box))
    occurrences = tuple(
        entry for entry in _occurrences_of_stage(stage) if entry[2].stage_wide_name == name
    )
    if occurrences:
        found.append(
            (f"the {len(occurrences)} occurrence(s) of the operator {name!r}", occurrences)
        )
    if name == EVALUATE and not occurrences:
        found.append(("the boundary representation `evaluate`", None))
    if len(found) > 1:
        _refuse_two_places(stage, name, [what for what, _ in found])
    if not found:
        _refuse_unauthored_name(stage, name)
    if name == EVALUATE and len(occurrences) > 1:
        _refuse_several_evaluate(stage, name, occurrences)
    _, place = found[0]
    if place is None:
        return _resolve_value_representation(stage, name)
    return place


def _what_block_is(stage, box) -> str:
    if _writes_role(stage, box, (VALUE,)):
        return "a backward builder over values"
    if _writes_role(stage, box, (CONTROL,)):
        return "the policy block"
    perch_from, perch_to = perches_of(box, header_wire_sorts(stage))
    return f"a block whose sides are at the perches {perch_from!r} and {perch_to!r}"


# What each operator of the vocabulary (construction.py, OPERATOR_VOCABULARY)
# is, for the refusal of a name that no line authors.
_OPERATOR_IS = {
    "E": "the expectation over the shocks",
    "argmax": "the maximiser of an objective",
    "solve": "the root of an equation in its unknown",
    "D": "the derivative of a function",
    "evaluate": "an interpolation written explicitly",
    "upper_env": "the upper envelope of the candidate solutions",
}


def _refuse_unauthored_name(stage, name) -> None:
    """The refusal of a one-part target that reaches nothing: an operator
    that no statement records — one written only in a `!doc` line or in a
    top-level definition, or nowhere — or a name that is neither a builder
    nor an operator nor `evaluate`."""
    head = "E" if name.startswith("E_") else name
    if head in OPERATOR_VOCABULARY:
        explanation = f"names {_OPERATOR_IS[head]}"
        for box, record in _doc_lines_writing(stage, name):
            explanation += (
                f"; the operator is written in the `!doc` line {record.address} "
                f"(`{_source(stage, record)}`), and a `!doc` line is documentation that "
                f"records no operator occurrence; "
                f"{_defining_statements(stage, box)}"
            )
        explanation += (
            f"; no statement of the stage records an occurrence of {name!r}, and "
            f"an operator is a target only where a statement records it — none "
            f"is derived from a method name"
        )
        function_names = {
            Identity(kind, stage=stage.name, field=name): name
            for name in symbol_groups(stage)["functions"]
            for kind in ("function", "correspondence")
        }
        for definition in stage.definitions.values():
            if definition.kind not in ("function", "function_alias", "correspondence"):
                continue
            if name in _term_operator_names(stage, definition.equations):
                display_name = function_names.get(definition.identity, definition.identity)
                explanation += (
                    f"; the operator occurs in the definition of {display_name!r} "
                    f"(address {getattr(definition, 'address', definition.identity)!r}), a named "
                    "function inlined where it is used and not a box of the stage (spec 0.3c "
                    "§4.3), so that occurrence is not a target here"
                )
        _refuse(stage, name, RULE_D, explanation)
    _refuse(
        stage,
        name,
        RULE_A,
        (
            "names no builder of the stage, no operator a statement of it records, "
            "and not its boundary representation"
        ),
    )


def _term_operator_names(stage, equations):
    """Authored operator names in retained equations (the
    fold's definitions)."""
    shocks = set(symbol_groups(stage)["exogenous"])

    def walk(node):
        yield node
        if _dc.is_dataclass(node) and not isinstance(node, type):
            for f in _dc.fields(node):
                yield from walk(getattr(node, f.name))
        elif isinstance(node, tuple):
            for item in node:
                yield from walk(item)

    for equation in equations:
        for node in walk(equation):
            if isinstance(node, T.Operator):
                if node.head == "E":
                    names = [s.var if isinstance(s, T.In) else s.name for s in node.subs]
                    if all(n in shocks for n in names):
                        yield "E_" + "_".join(names)
                elif node.head in OPERATOR_VOCABULARY:
                    yield node.head
            elif isinstance(node, T.Call) and node.fun in ("evaluate", "upper_env"):
                yield node.fun


def _source(stage, record):
    """The authored text of a line: its retained term printed."""
    return to_source(record.core) if record.core is not None else None


def _doc_lines_writing(stage, name) -> tuple:
    """The `!doc` lines whose right side writes the operator `name` (a
    stage-wide operator name), with the builders that hold them: documentary
    references, not mathematical operations, read from the retained terms."""
    found = []
    for box in blocks_of(stage):
        for _, record in lines_of(stage, box):
            if record.role != DOC or record.core is None:
                continue
            slack = isinstance(record.core, T.Slack)
            equation = record.core.core if slack else record.core
            if name in {
                occurrence.stage_wide_name
                for occurrence in occurrence_paths(equation.rhs, ("rhs",), slack=slack)
            }:
                found.append((box, record))
    return tuple(found)


def _defining_statements(stage, box) -> str:
    """The output statements of the builder `box` — the lines that define
    its outputs — each with the addresses of its operator occurrences, for a
    refusal that points from a `!doc` line to the places a method attaches.
    A property of a line is no place of its own and is left out."""
    lines = lines_of(stage, box)
    defining = [
        record
        for _, record in lines
        if record.role == OUTPUT_LINE and not is_property(lines, record)
    ]
    if not defining:
        return f"block {box.name!r} has no defining statement"

    def described(record):
        if record.operators:
            return f"{record.address}, whose operators are " + ", ".join(
                _occurrence_address(record, o) for o in record.operators
            )
        return (
            f"{record.address} (`{_source(stage, record)}`), which carries no operator occurrence"
        )

    if len(defining) == 1:
        return f"the defining statement of the block is {described(defining[0])}"
    return "the defining statements of the block are " + "; ".join(described(r) for r in defining)


def _refuse_several_evaluate(stage, name, occurrences) -> None:
    """Rule (g) for a stage that authors two or more `evaluate` occurrences:
    the bare name is refused naming each occurrence's address."""
    named = ", ".join(
        f"{_occurrence_address(record, occurrence)} (`{_source(stage, record)}`)"
        for _, record, occurrence in occurrences
    )
    unnamed = any(not _has_id(record) for _, record, _ in occurrences)
    _refuse(
        stage,
        name,
        RULE_G,
        (
            f"names {_OPERATOR_IS[EVALUATE]}, and the stage authors {len(occurrences)} "
            f"such occurrences, each interpolating its own function on its own grid: "
            f"{named}; a bare `evaluate` names the one authored occurrence of a stage, "
            f"so name one of these by its address `<block-id>.<statement-id>.evaluate` "
            f"(spec 0.3c §4.3, the authored-`evaluate` row)"
            + ("; a line without an id needs `:: [id=<name>]` first" if unnamed else "")
        ),
    )


def _resolve_value_representation(stage, target):
    """Rule (g) for a stage that authors no `evaluate` occurrence."""
    places = _TargetInventory(stage)
    kind, *rest = places.boundary
    if kind == "implicit":
        implicit = [
            (box.name, record)
            for box in blocks_of(stage)
            for _, record, occurrence in _occurrences_of_box(stage, box)
            if is_implicit_solve(occurrence)
        ]
        named = "; ".join(
            f"{record.address} (`{_source(stage, record)}`)" for _, record in implicit
        )
        holders = ", ".join(
            f"`on: {name}`" for name in dict.fromkeys(name for name, _ in implicit)
        )
        representation = [box.name for box in backward_builders_to_decision(stage)]
        value_lines = [
            address for address in places.lines if address.split(".")[0] in representation
        ]
        _refuse(
            stage,
            target,
            RULE_G,
            (
                f"names no authored occurrence, and the stage has the implicit "
                f"statement {named}: the representation of that policy is a method at "
                f"the Evaluation of its block ({holders}), `!egm` among them where the "
                f"block writes the grid line, and the representation of the value "
                f"function at the decision perch is named by the lines of the "
                f"backward builder"
                + (f" ({', '.join(value_lines)})" if value_lines else "")
                + " (the consequence for a stage with an implicit "
                "statement; D07)"
            ),
        )
    if kind == "builder":
        return (rest[0], ValueRepresentation(rest[0].name))
    if not rest[0]:
        _refuse(
            stage,
            target,
            RULE_G,
            (
                "names no authored occurrence, and the stage has no backward "
                "builder from the continuation perch to the decision perch that "
                "writes a value field, whose boundary representation `evaluate` "
                "would name"
            ),
        )
    _refuse_two_places(
        stage, target, [f"the boundary representation of {box.name!r}" for box in rest[0]]
    )


def _resolve_line(stage, target, block_id, statement_id):
    """Rules (b) and (c): the node bubble, or the line with the box that
    holds it."""
    box = block_box(stage, target, block_id)
    if statement_id.isdigit():
        _refuse_positional(stage, target, box, int(statement_id))
    holder, record = _line(stage, target, box, target)
    if record.role == NODE:
        return holder
    return (holder, record)


def _resolve_occurrence(stage, target, block_id, statement_id, operator):
    """Rule (e): the one occurrence of `operator` in the named line; a line
    with no occurrence of it is refused naming where a method attaches and,
    for a `!doc` line, the block's defining statements. A target that spells
    the address of a property, `policy.optimality.euler`, is refused naming
    the line the property is attached to."""
    box = block_box(stage, target, block_id)
    if statement_id.isdigit():
        _refuse_positional(stage, target, box, int(statement_id))
    lines = lines_of(stage, box)
    for _, other in lines:
        if other.address == target and is_property(lines, other):
            owner = next(line for _, line in lines if line.address == _owner_address(other))
            places = ", ".join(_occurrence_address(owner, o) for o in owner.operators)
            _refuse(
                stage,
                target,
                RULE_E,
                (
                    f"names the line `{_source(stage, other)}`, which its dotted id attaches "
                    f"to the line {owner.address} as a property; a property forms no "
                    f"operation and is no place a method attaches to, and the places of "
                    f"the line {owner.address} are {places or 'none'}"
                ),
            )
    holder, record = _line(stage, target, box, f"{block_id}.{statement_id}")
    hits = [o for o in record.operators if o.stage_wide_name == operator]
    if len(hits) == 1:
        return (holder, record, hits[0])
    if len(hits) > 1:
        positions = " and ".join(f"{o.position!r}" for o in hits)
        _refuse(
            stage,
            target,
            RULE_E,
            (
                f"reaches two occurrences of {operator!r} in the line "
                f"`{_source(stage, record)}`, at the positions {positions}; an occurrence "
                f"address names one occurrence per line, and the stage-wide name "
                f"{operator!r} governs both"
            ),
        )
    if not record.operators:
        if record.role == DOC:
            what = "a `!doc` line, which records no occurrence"
        elif record.role == OUTPUT_LINE:
            what = f"the output statement {record.address}, which carries no operator occurrence"
        elif record.role == NODE:
            what = "a `!node` line, which carries no operator occurrence"
        else:
            what = "an alias, which carries no operator occurrence"
        names_this = (
            f" — `on: {record.address}` names this one"
            if record.role in (OUTPUT_LINE, NODE)
            else ""
        )
        defining = f"; {_defining_statements(stage, box)}" if record.role == DOC else ""
        node_clause = f", to a node box{names_this}" if record.role == NODE else ", to a node box"
        boundary_clause = (
            f" (the representation of the field it defines{names_this})"
            if record.role == OUTPUT_LINE
            else " (the representation of the field it defines)"
        )
        _refuse(
            stage,
            target,
            RULE_E,
            (
                f"names an operator in `{_source(stage, record)}`, {what}; a method attaches "
                f"to an operator occurrence, to the builder{node_clause}, to an "
                f"output statement with no operator occurrence{boundary_clause}, "
                f"to one occurrence of a named line that carries it, by "
                f"`<block-id>.<statement-id>.<operator>`, or to the boundary "
                f"representation{defining}"
            ),
        )
    others = ", ".join(f"{record.address}.{o.stage_wide_name}" for o in record.operators)
    _refuse(
        stage,
        target,
        RULE_E,
        (
            f"names {operator!r} in the line `{_source(stage, record)}`, whose operator "
            f"occurrences are {others}"
        ),
    )


def _line(stage, target, box, address):
    """The one `(holder, Line)` of the line at `address` in `box`; a line
    that does not exist, or two lines with one id, is refused."""
    lines = lines_of(stage, box)
    matches = [(holder, record) for holder, record in lines if record.address == address]
    if len(matches) == 1:
        return matches[0]
    if matches:
        _refuse_two_places(
            stage,
            target,
            [
                f"line {record.ordinal} `{_source(stage, record)}` (address {record.address!r}, "
                f"held by the box {node_address(holder)!r})"
                for holder, record in matches
            ],
        )
    statement_id = address.split(".", 1)[1]
    named = [
        record.address for _, record in lines if _has_id(record) and not is_property(lines, record)
    ]
    unnamed = [
        f"line {record.ordinal} `{_source(stage, record)}`"
        for _, record in lines
        if not _has_id(record)
    ]
    _refuse(
        stage,
        target,
        RULE_B_C,
        (
            f"names no line of block {box.name!r}: no line carries the id "
            f"{statement_id!r}; the block's named lines are "
            f"{', '.join(named) or 'none'}"
            + (f", and its lines without an id are {', '.join(unnamed)}" if unnamed else "")
        ),
    )


def _refuse_positional(stage, target, box, n) -> None:
    """The refusal of a positional address, with a request for an id or
    with the id of the line that stands at that position: an inserted `!doc`
    line would renumber the lines that follow it."""
    at = [record for _, record in lines_of(stage, box) if record.ordinal == n]
    if not at:
        count = len(lines_of(stage, box))
        _refuse(
            stage,
            target,
            RULE_II,
            (
                f"is a positional address, and block {box.name!r} has {count} "
                f"line{'' if count == 1 else 's'}"
            ),
        )
    (record,) = at
    lines = lines_of(stage, box)
    if is_property(lines, record):
        _refuse(
            stage,
            target,
            RULE_II,
            (
                f"is a positional address; line {n} of block {box.name!r} is "
                f"`{_source(stage, record)}`, which its dotted id attaches to the line "
                f"{_owner_address(record)} as a property, and a property is no place a "
                "method attaches to"
            ),
        )
    if _has_id(record):
        _refuse(
            stage,
            target,
            RULE_II,
            (
                f"is a positional address; line {n} of block {box.name!r} is "
                f"`{_source(stage, record)}`, named {record.address!r} — name it by its id"
            ),
        )
    _refuse(
        stage,
        target,
        RULE_II,
        (
            f"is a positional address: line {n} of block {box.name!r}, "
            f"`{_source(stage, record)}`, carries no id, and a method target names a line by "
            f"its id, since an inserted `!doc` line would renumber what follows "
            f"(D06 sub-choice (ii)); add `:: [id=<name>]` to the line"
        ),
    )


def _refuse_two_places(stage, target, places) -> None:
    _refuse(
        stage,
        target,
        RULE_TWO,
        (f"reaches {len(places)} places, which is a construction defect: " + " and ".join(places)),
    )


def _refuse(stage, target, rule, explanation) -> None:
    """The `TargetError` of `target` in `stage`, raised: the message names
    the target, the stage, the explanation, and the places the stage has."""
    places = _TargetInventory(stage)
    raise TargetError(
        target=target,
        stage=stage.name,
        rule=rule,
        candidates=target_inventory(stage),
        message=f"{target!r} in stage {stage.name!r} {explanation}. {places.describe(stage.name)}",
    )


# --- the places of a stage ---


def block_box(stage, target, block_id):
    """The builder box named `block_id`, or a `TargetError` on `target`
    naming the builders the stage has."""
    for box in blocks_of(stage):
        if box.name == block_id:
            return box
    _refuse(
        stage,
        target,
        RULE_A,
        (f"names no builder of the stage: {block_id!r} is not the id of a block"),
    )


class _TargetInventory:
    """The places of one stage, from one walk in source order: `inventory`,
    the flat tuple `target_inventory` returns; and the same places grouped
    for a message — `builders`, `nodes`, `lines` (the named lines that are
    not nodes), `operators` (stage-wide name -> the addresses of its
    occurrences, a line without an id shown by its position), `implicit`
    (the addresses of the implicit statements), and `boundary`, the outcome
    of rule (g) for a bare `evaluate`: `("occurrences", addresses)` when the
    stage authors one or more, `("implicit", addresses)` when it has an
    implicit statement and no authored occurrence, `("builder", box)` when one
    backward builder to the decision perch carries the representation, and
    `("none", boxes)` otherwise, `boxes` the zero or several candidates. A
    property of a line is no place, and the walk passes over it."""

    def __init__(self, stage):
        self.builders, self.nodes, self.lines, self.implicit = [], [], [], []
        self.operators = {}
        inventory = []
        for box in blocks_of(stage):
            inventory.append(box.name)
            self.builders.append(box.name)
            lines = lines_of(stage, box)
            for holder, record in lines:
                if is_property(lines, record):
                    continue
                named = _has_id(record)
                if named:
                    inventory.append(record.address)
                    (self.nodes if record.role == NODE else self.lines).append(record.address)
                for occurrence in record.operators:
                    address = _occurrence_address(record, occurrence)
                    if named:
                        inventory.append(address)
                    self.operators.setdefault(occurrence.stage_wide_name, []).append(address)
                    if is_implicit_solve(occurrence):
                        self.implicit.append(record.address)
        inventory.extend(
            name
            for name, addresses in self.operators.items()
            if not (name == EVALUATE and len(addresses) > 1)
        )
        if EVALUATE in self.operators:
            self.boundary = ("occurrences", tuple(self.operators[EVALUATE]))
        elif self.implicit:
            self.boundary = ("implicit", tuple(self.implicit))
        else:
            candidates = backward_builders_to_decision(stage)
            if len(candidates) == 1:
                self.boundary = ("builder", candidates[0])
                inventory.append(EVALUATE)
            else:
                self.boundary = ("none", candidates)
        self.inventory = tuple(inventory)

    def describe(self, stage_name) -> str:
        """The places of the stage, grouped, for a refusal message."""

        def listed(names):
            return ", ".join(names) if names else "none"

        operators = (
            ", ".join(
                f"{name} ({', '.join(addresses)})" for name, addresses in self.operators.items()
            )
            or "none"
        )
        kind, *rest = self.boundary
        if kind == "occurrences" and len(rest[0]) == 1:
            evaluate = f"the authored occurrence {rest[0][0]}"
        elif kind == "occurrences":
            evaluate = (
                f"not a target here: the stage authors {len(rest[0])} "
                f"`evaluate` occurrences ({listed(rest[0])}), each named by "
                f"its own address"
            )
        elif kind == "implicit":
            evaluate = (
                f"not a target here, since the stage has the implicit statement {listed(rest[0])}"
            )
        elif kind == "builder":
            evaluate = f"the boundary representation of {rest[0].name}"
        elif not rest[0]:
            evaluate = (
                "not a target here: no backward builder from the "
                "continuation to the decision perch writes a value field"
            )
        else:
            evaluate = (
                f"not a target here: {len(rest[0])} backward builders to "
                f"the decision perch ({listed(b.name for b in rest[0])})"
            )
        parts = [f"builders: {listed(self.builders)}"]
        if self.nodes:
            parts.append(f"node boxes: {listed(self.nodes)}")
        parts.extend(
            [
                f"named lines: {listed(self.lines)}",
                f"operators: {operators}",
                f"`evaluate`: {evaluate}",
            ]
        )
        return f"The places of stage {stage_name!r} are — " + "; ".join(parts) + "."


def _occurrences_of_stage(stage) -> tuple:
    """`(holder, line, occurrence)` for every operator occurrence of the
    stage in source order. A `!doc` line carries none, and a property of a
    line is no place of its own."""
    return tuple(entry for box in blocks_of(stage) for entry in _occurrences_of_box(stage, box))


def _occurrences_of_box(stage, box) -> tuple:
    """`(holder, line, occurrence)` for every operator occurrence of the
    lines of one builder in source order, a property of a line left out."""
    lines = lines_of(stage, box)
    return tuple(
        (holder, record, occurrence)
        for holder, record in lines
        if not is_property(lines, record)
        for occurrence in record.operators
    )


def _has_id(record) -> bool:
    """Whether the line carries `[id=…]`, so that its address is its id and
    not its position."""
    return any(tag.startswith("id=") for tag in record.tags)


def _occurrence_address(record, occurrence) -> str:
    """The occurrence address `<block-id>.<statement-id>.<operator>` of an
    occurrence in a line with an id; for a line without one, its positional
    address marked `(no id)`, which is not a target."""
    if _has_id(record):
        return f"{record.address}.{occurrence.stage_wide_name}"
    return f"{record.address} (no id)"


def _is_transition(stage, box) -> bool:
    """Whether the block's sides go forward through the perches (arrival to
    decision, decision to continuation): the block is a forward block, the
    builder the `_builder` suffix names."""
    perch_from, perch_to = perches_of(box, header_wire_sorts(stage))
    return (
        perch_from in PERCHES
        and perch_to in PERCHES
        and PERCHES.index(perch_from) < PERCHES.index(perch_to)
    )


def _writes_role(stage, box, roles) -> bool:
    """Whether an output field of the box has one of the given roles, read
    from the sorts of its output wires."""
    ports = header_wire_sorts(stage)
    return any(ports[ob.identity].role in roles for ob in box.cod.inside if ob.identity in ports)


def backward_builders_to_decision(stage) -> tuple:
    """The builders from the continuation perch to the decision perch that
    write a value or marginal-value field: the backward decision builder,
    whose outputs carry the decision-perch value function that `on: evaluate`
    represents and which a handler for the whole builder realizes
    (`cntn_to_dcsn`). The policy block of a consumption stage has the same two
    perches but writes a control, not a value."""
    ports = header_wire_sorts(stage)
    return tuple(
        box
        for box in blocks_of(stage)
        if perches_of(box, ports) == (PERCHES[2], PERCHES[1])
        and _writes_role(stage, box, (VALUE,))
    )
