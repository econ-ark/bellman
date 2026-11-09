"""Where a numerical method attaches in a stage: the targets of a methods file
(spec 0.3c §3.4, §4.3; AMD-MB-002).

A target is a place in the stage where a numerical method attaches. The
places a stage has are: a builder — a whole forward step over states
(`arvl_to_dcsn`, `dcsn_to_cntn`), a whole backward step over values
(`cntn_to_dcsn`, `dcsn_to_arvl`), or the policy between them; a line the
modeler named with `[id=…]`; an operator inside a line — the expectation over
the shocks in `V = E_{Ψ,θ}(V[>])`, the root of a first-order condition in
`ς = solve_{ς}(…)`, the `solve` that an implicit statement `c = c[>]`
records, an `argmax`, an `upper_env`, an authored interpolation
`evaluate(…)`; and the Evaluation of a builder, the operation that closes the
builder and stores what it writes, named by what it evaluates: the policy
function, `policy.evaluate`; the value function a backward value builder
writes, `cntn_to_dcsn.evaluate.value`; and the derivative of that value which
a derivative line states, `cntn_to_dcsn.evaluate.marginal` (AMD-MB-002 §3).
A methods file names one place per entry (`on: policy`, `on: E_Ψ_θ`,
`on: policy.foc.solve`, `on: cntn_to_dcsn.evaluate.value`), and `methodize`
records the entry's method in the stage's `methods`, the one record of
attachments. This module resolves a name to its place (`resolve_target`),
lists the places a stage has (`target_inventory`), and tells a line attached
to another as its property (`is_property`, `properties_of`).

The places in the graph. A builder is a `Builder` bubble of the stage
hypergraph; a `!node` line is a bubble inside its builder, named by the
line's address; every other line is a box named by its address inside the
bubble that holds it; an operator occurrence is a query on the line's
retained term; the Evaluation of a builder is the row that closes the
builder's bubble, `<block-id>:Evaluation`. A target resolves by these rules:

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
    operator occurrence, the value line `cntn_to_dcsn.value` in `cons`, names
    the line, and a representation named on it is held at the Evaluation
    that closes the builder. A derivative line, `cntn_to_dcsn.marginal` in
    `cons`, which states a derivative of the value and defines no field, is
    addressable in the same way, and a representation named on it is refused
    where the method is placed, since the derivative it states is
    represented at `<block-id>.evaluate.marginal` (rule (i)). Under (c.ii), a
    positional address `<block-id>.<n>` — the address of a line without an
    id — is refused with a request for an id: an inserted `!doc` line would
    renumber what follows.
    A line whose id is dotted, `x.y`, is attached to the line `x` of its
    block as a property (`optimality.euler`, the first-order condition of the
    maximization `optimality`): it forms no operation and is no place of its
    own, so no inventory lists it and a target naming it is refused. A dotted
    id whose block holds no line `x` is refused where the stage is
    constructed. A line of a branch is addressed under the branch's label,
    `<block-id>.<label>.<statement-id>` (`dcsn_to_cntn.work.working`), and
    an occurrence in it by the operator written after that.
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
(e) `<block-id>.<statement-id>.<operator>` is every occurrence of that
    operator in that line, in the form of (d); the line must carry an id,
    and a line that holds one head twice, `D_{a_d}V = (D_{a_w}V_w[>],
    D_{a_r}V_r[>])[d]`, is one address that governs both occurrences, since
    no finer address exists. A line that carries no occurrence of the named
    operator is refused naming where a method attaches; an `evaluate`
    named on a line that carries none, in the policy builder or a backward
    value builder, is refused naming the written address of that builder's
    Evaluation, rule (i).
(f) Resolution is method-blind: a block id is the builder box under (a)
    whatever the entry's method. `methodize`, which reads the method table
    (`method_table.METHOD_TYPES`), moves a solution method whose placement
    rule stands inside the builder to its place there: `!egm`, named with no
    block file, to the Evaluation that closes a policy block which writes the
    grid line, or to the maximization that carries its first-order condition
    as a property. A representation named on a value line or a `!node` line
    is held at the Evaluation that closes the builder or the node (rule
    (c)); one named on a builder or on a derivative line is refused naming
    the written address of the builder's Evaluation, rule (i) (AMD-MB-002
    §4).
(g) `evaluate` alone: in a stage that authors exactly one `evaluate`
    occurrence, that occurrence, in the form of (d); in a stage that authors
    two or more, refused naming their addresses
    `<block-id>.<statement-id>.evaluate`; in a stage that authors none,
    refused naming `<block-id>.evaluate.value` of the builder that writes
    the value, the backward builder from the continuation perch to the
    decision perch (`cntn_to_dcsn`), since the representation of that value
    is written at its Evaluation (AMD-MB-002 §4).
(h) A comma-separated entry is not one target: each part is an entry of its
    own, and `resolve_target` receives one target.
(i) `<block-id>.evaluate`, `<block-id>.evaluate.value` and
    `<block-id>.evaluate.marginal` name the Evaluation of the builder, and
    are read before (b), (c) and (e), so that no line whose id is
    `evaluate` is addressed; the resolution is `("evaluation", box, what)`,
    `what` being `policy`, `value` or `marginal`. `policy.evaluate` names the
    Evaluation of the policy builder, the builder that writes a control,
    where the policy function is stored; `.evaluate.value` names the value
    function a backward value builder writes, and `.evaluate.marginal` the
    derivative of that value a derivative line of the builder states, in the
    stage file or in a marginal block bound with `!marginals`. A form that
    names what its builder does not write is refused naming the forms the
    builder has: `.evaluate` alone for a backward value builder,
    `.evaluate.value` and `.evaluate.marginal` for the policy builder,
    `.evaluate.marginal` where no derivative line stands at the builder, any
    of the three for a forward builder, the push-forward of a measure through
    its law of motion, whose methods stand on the builder, and a third word
    other than `value` and
    `marginal` (AMD-MB-002 §§3, 4).

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
    node_address,
    perches_of,
    require_stage,
    symbol_groups,
)
from bellman.fold.stage_names import branches_of, lines_of
from bellman.fold.wire_terms import stated_derivative
from bellman.native.identity import Identity
from bellman.refusals import (
    RULE_A,
    RULE_B_C,
    RULE_D,
    RULE_E,
    RULE_FORM,
    RULE_G,
    RULE_H,
    RULE_I,
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
    the same for an occurrence address, every occurrence of the operator in
    that line (e); for `evaluate` alone, the
    one authored occurrence as a one-entry tuple, and a refusal naming the
    occurrence addresses when the stage authors two or more or the written
    address of the value's representation when it authors none (g);
    `("evaluation", box, what)` for the Evaluation of a builder named
    `<block-id>.evaluate`, `<block-id>.evaluate.value` or
    `<block-id>.evaluate.marginal`, `what` being `policy`, `value` or
    `marginal` (i). A block id is the builder box whatever method the entry
    carries (f). A name that reaches no place, a positional address, a
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
    branch_line = len(parts) >= 3 and _names_branch_line(stage, parts)
    if (
        not target
        or any(part == "" for part in parts)
        or len(parts) > 4
        or (len(parts) == 4 and not branch_line)
    ):
        _refuse(
            stage,
            target,
            RULE_FORM,
            (
                "is not the form of a target: a block id, `<block-id>."
                "<statement-id>`, `<block-id>.<statement-id>.<operator>`, a line of a "
                "branch, `<block-id>.<label>.<statement-id>`, with its operator after it, the "
                "Evaluation of a builder, `<block-id>.evaluate`, "
                "`<block-id>.evaluate.value` or `<block-id>.evaluate.marginal`, or a "
                "stage-wide operator name"
            ),
        )
    if len(parts) == 1:
        return _resolve_name(stage, target)
    # the Evaluation of a builder is read before a line and an occurrence
    # (rule (i))
    if parts[1] == EVALUATE:
        return _resolve_evaluation(stage, target, parts[0], parts[2] if len(parts) == 3 else None)
    if branch_line:
        # a line of a branch is addressed under its label, `dcsn_to_cntn.work.working`,
        # and an occurrence in it by the operator after that (rules (c) and (e))
        statement_id = f"{parts[1]}.{parts[2]}"
        if len(parts) == 3:
            return _resolve_line(stage, target, parts[0], statement_id)
        return _resolve_occurrence(stage, target, parts[0], statement_id, parts[3])
    if len(parts) == 2:
        return _resolve_line(stage, target, *parts)
    return _resolve_occurrence(stage, target, *parts)


def _names_branch_line(stage, parts) -> bool:
    """Whether the second part of a target names a branch of the block its
    first part names, so that the target addresses a line of that branch."""
    box = next((box for box in blocks_of(stage) if box.name == parts[0]), None)
    return box is not None and any(label == parts[1] for label, _ in branches_of(stage, box))


def target_inventory(stage):
    """Every target string of `stage`, in source order: each builder box,
    then, line by line, the box's lines that carry `[id=…]` — a node bubble or
    a line — each followed by the addresses of its operator occurrences, then
    the written addresses of the builder's Evaluation (`evaluation_addresses`);
    then the stage-wide operator names in first-occurrence order, `evaluate`
    among them only when the stage authors exactly one occurrence; then the
    authored functions. A line without an id is not listed (its address is
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


def evaluation_addresses(stage, box) -> tuple:
    """The written addresses of the Evaluation of the builder `box`, the
    operation that closes it (AMD-MB-002 §3): `<block-id>.evaluate` for the
    policy builder, the builder that writes a control, whose Evaluation
    stores the policy function; `<block-id>.evaluate.value` for a backward
    value builder, the builder that writes a value, followed by
    `<block-id>.evaluate.marginal` where a derivative line stands at it
    (`derivative_lines`); none for a forward builder, whose methods realize
    its law and stand on the builder."""
    if _writes_role(stage, box, (VALUE,)):
        marginal = (f"{box.name}.{EVALUATE}.{MARGINAL}",) if derivative_lines(stage, box) else ()
        return (f"{box.name}.{EVALUATE}.{VALUE_WORD}",) + marginal
    if _writes_role(stage, box, (CONTROL,)):
        return (f"{box.name}.{EVALUATE}",)
    return ()


def derivative_lines(stage, box) -> tuple:
    """The addresses of the derivative lines of the builder `box`, in the
    order of its lines: each line that states a derivative of the value the
    builder writes, `D_{m_d}V = 𝑑𝑢(c)`, written in the stage file or added by
    a marginal block bound with `!marginals` (AMD-MB-001 §4.3). A `!doc` line
    and a property of a line state nothing and are left out."""
    lines = lines_of(stage, box)
    return tuple(
        record.address
        for _, record in lines
        if record.role != DOC
        and record.core is not None
        and not is_property(lines, record)
        and stated_derivative(record.core) is not None
    )


# --- resolution by rule ---

# The suffix of the spelling `<block-id>_builder` of a forward block's
# target, which names the forward builder.
BUILDER_SUFFIX = "_builder"


# The name of the operator `evaluate`: alone, the authored occurrence of rule
# (g); after a block id, the Evaluation of that builder, rule (i).
EVALUATE = "evaluate"

# The words written after `<block-id>.evaluate` for a backward value builder:
# the value function it writes and the derivative of that value a derivative
# line states (AMD-MB-002 §3).
VALUE_WORD = "value"
MARGINAL = "marginal"

# What the Evaluation of the policy builder, `<block-id>.evaluate`, stores.
POLICY_FUNCTION = "policy"


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
    if len(found) > 1:
        _refuse_two_places(stage, name, [what for what, _ in found])
    if not found and name == EVALUATE:
        _refuse_evaluate_without_occurrence(stage, name)
    if not found:
        _refuse_unauthored_name(stage, name)
    if name == EVALUATE and len(occurrences) > 1:
        _refuse_several_evaluate(stage, name, occurrences)
    _, place = found[0]
    return place


def _resolve_evaluation(stage, target, block_id, word):
    """Rule (i): the Evaluation of the builder `block_id`, named by what it
    evaluates, `word` being the word written after `evaluate` or None, as
    `("evaluation", box, what)`; a form that names what the builder does not
    write is refused naming the written addresses the builder has."""
    box = block_box(stage, target, block_id)
    written = evaluation_addresses(stage, box)
    if target in written:
        return ("evaluation", box, word or POLICY_FUNCTION)
    named = " or ".join(f"`on: {address}`" for address in written)
    if not written and _is_transition(stage, box):
        explanation = (
            f"names an Evaluation of the forward builder {box.name!r}, which closes with no "
            f"Evaluation, since it is the push-forward of a measure through its law of motion; "
            f"a method of the law of motion, `!deterministic`, `!monte-carlo`, `!histogram` or "
            f"`!identity`, stands on the builder, `on: {box.name}`"
        )
    elif not written:
        explanation = (
            f"names the Evaluation of {box.name!r}, {_what_block_is(stage, box)}, which writes "
            f"neither a value nor a policy and has no Evaluation a representation is attached to"
        )
    elif word is not None and word not in (VALUE_WORD, MARGINAL):
        explanation = (
            f"names the Evaluation of {box.name!r} by the word {word!r}, but the word after "
            f"`evaluate` must be `{VALUE_WORD}` or `{MARGINAL}`; the Evaluation of "
            f"{box.name!r} is written {named}"
        )
    elif _writes_role(stage, box, (CONTROL,)):
        what = "a value" if word == VALUE_WORD else "the stated derivative of a value"
        explanation = (
            f"names {what} at the Evaluation of the policy builder {box.name!r}, which writes "
            f"the policy and neither a value nor its derivative; its Evaluation is written "
            f"{named}"
        )
    elif word is None:
        explanation = (
            f"names the Evaluation of the backward value builder {box.name!r} without the word "
            f"that says what it evaluates; write {named}"
        )
    else:
        explanation = (
            f"names the stated derivative of the value the builder {box.name!r} writes, and no "
            f"derivative line stands at that builder, in the stage file or in a marginal block "
            f"bound on it with `!marginals`; the value's representation is written {named}"
        )
    _refuse(stage, target, RULE_I, explanation)


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


def _refuse_evaluate_without_occurrence(stage, name) -> None:
    """Rule (g) for a stage that authors no `evaluate` occurrence: the bare
    name names no place, and the refusal names the written address of the
    Evaluation at which the value the stage's backward builder from the
    continuation perch to the decision perch writes is represented, or of
    each backward value builder's value where the stage has not exactly one
    such builder (AMD-MB-002 §4)."""
    writing = backward_builders_to_decision(stage)
    if len(writing) != 1:
        writing = tuple(box for box in blocks_of(stage) if _writes_role(stage, box, (VALUE,)))
    written = [f"`on: {box.name}.{EVALUATE}.{VALUE_WORD}`" for box in writing]
    if len(writing) == 1:
        where = (
            f"the value the builder {writing[0].name!r} writes is represented at its "
            f"Evaluation, {written[0]}"
        )
    elif writing:
        where = (
            "the value a backward builder writes is represented at its Evaluation, "
            f"{' or '.join(written)}"
        )
    else:
        where = "the stage has no backward builder that writes a value"
    _refuse(
        stage,
        name,
        RULE_G,
        f"names no place, since the stage authors no `evaluate` occurrence, and {where}",
    )


def _refuse_unauthored_name(stage, name) -> None:
    """The refusal of a one-part target that reaches nothing: an operator
    that no statement records — one written only in a `!doc` line or in a
    top-level definition, or nowhere — or a name that is neither a builder
    nor an operator."""
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
        "names no builder of the stage and no operator a statement of it records",
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
    """Rule (e): every occurrence of `operator` in the named line, each as
    `(holder, Line, OperatorOccurrence)` in the line's order, as rule (d)
    answers for the stage; a line that holds one head twice,
    `D_{a_d}V = (D_{a_w}V_w[>], D_{a_r}V_r[>])[d]`, is one address that
    governs both. A line with no occurrence of it is refused naming where a
    method attaches and, for a `!doc` line, the block's defining statements.
    A target that spells the address of a property, `policy.optimality.euler`,
    is refused naming the line the property is attached to."""
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
    hits = tuple((holder, record, o) for o in record.operators if o.stage_wide_name == operator)
    if hits:
        return hits
    written_here = evaluation_addresses(stage, box)
    if operator == EVALUATE and written_here:
        # the policy builder and a backward value builder close with an
        # Evaluation, which the methods file names by the builder's id and
        # not by a line's (AMD-MB-002 §3)
        _refuse(
            stage,
            target,
            RULE_E,
            (
                f"names an `evaluate` occurrence in `{_source(stage, record)}`, which carries "
                f"none; the Evaluation of the builder {box.name!r}, where a representation is "
                f"attached, is written {' or '.join(f'`on: {a}`' for a in written_here)}"
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
        names_this = f" — `on: {record.address}` names this one" if record.role == NODE else ""
        defining = f"; {_defining_statements(stage, box)}" if record.role == DOC else ""
        node_clause = f", to a node box{names_this}" if record.role == NODE else ", to a node box"
        # the representation of a field a builder writes is written at the
        # builder's Evaluation; a value line's own address, which binds there
        # too, is not offered (AMD-MB-002 §3)
        if written_here:
            representation_clause = (
                f" (the representation of the field it defines, written at the builder's "
                f"Evaluation, `on: {written_here[0]}`"
            )
        else:
            representation_clause = " (the representation of the field it defines"
        if record.role == OUTPUT_LINE and record.address in derivative_lines(stage, box):
            # a derivative line defines no field; the derivative it states is
            # represented at the builder's Evaluation (AMD-MB-002 §4)
            representation_clause += (
                f"; the derivative this line states is represented at "
                f"`on: {box.name}.{EVALUATE}.{MARGINAL}`"
            )
        representation_clause += ")"
        _refuse(
            stage,
            target,
            RULE_E,
            (
                f"names an operator in `{_source(stage, record)}`, {what}; a method attaches "
                f"to an operator occurrence, to the builder{node_clause}, to an "
                f"output statement with no operator occurrence{representation_clause}, "
                f"to one occurrence of a named line that carries it, by "
                f"`<block-id>.<statement-id>.<operator>`, or to the Evaluation of a "
                f"builder, written `<block-id>.evaluate` for the policy builder and "
                f"`<block-id>.evaluate.value` or `<block-id>.evaluate.marginal` for a "
                f"backward value builder{defining}"
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
    not nodes), `evaluations` (the written addresses of the builders'
    Evaluations, rule (i)), and `operators` (stage-wide name -> the addresses
    of its occurrences, a line without an id shown by its position), whose
    entry `evaluate`, where the stage authors one or more `evaluate`
    occurrences, is the outcome of rule (g) for the bare name. A property of
    a line is no place, and the walk passes over it."""

    def __init__(self, stage):
        self.builders, self.nodes, self.lines, self.evaluations = [], [], [], []
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
                    addresses = self.operators.setdefault(occurrence.stage_wide_name, [])
                    # two occurrences of one head in one line are one address (rule (e))
                    if address in addresses:
                        continue
                    if named:
                        inventory.append(address)
                    addresses.append(address)
            # the Evaluation of the builder, after its lines (AMD-MB-002 §4)
            written = evaluation_addresses(stage, box)
            inventory.extend(written)
            self.evaluations.extend(written)
        inventory.extend(
            name
            for name, addresses in self.operators.items()
            if not (name == EVALUATE and len(addresses) > 1)
        )
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
        occurrences = self.operators.get(EVALUATE, ())
        if len(occurrences) == 1:
            evaluate = f"the authored occurrence {occurrences[0]}"
        elif occurrences:
            evaluate = (
                f"not a target here: the stage authors {len(occurrences)} "
                f"`evaluate` occurrences ({listed(occurrences)}), each named by "
                f"its own address"
            )
        else:
            evaluate = "not a target here, since the stage authors no `evaluate` occurrence"
        parts = [f"builders: {listed(self.builders)}"]
        if self.nodes:
            parts.append(f"node boxes: {listed(self.nodes)}")
        parts.extend(
            [
                f"named lines: {listed(self.lines)}",
                f"Evaluations of the builders: {listed(self.evaluations)}",
                f"operators: {operators}",
                f"`evaluate` alone: {evaluate}",
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
    write a value field: the backward decision builder, whose outputs carry
    the decision-perch value function, represented at
    `<block-id>.evaluate.value`, and which a handler for the whole builder
    realizes (`cntn_to_dcsn`). The policy block of a consumption stage has the
    same two perches but writes a control, not a value."""
    ports = header_wire_sorts(stage)
    return tuple(
        box
        for box in blocks_of(stage)
        if perches_of(box, ports) == (PERCHES[2], PERCHES[1])
        and _writes_role(stage, box, (VALUE,))
    )
