"""The method table and the attachment of numerical choices to the places of
a stage: the one record of attachments, `bindings.methods` (AMD-SG-005 §4;
AMD-SG-006 §4). The page `docs/Bellman-Sym/reference/methods.md` is printed
from `METHOD_TYPES`, one row for each method type.

`attach_methods`, which `binding_verbs.methodized_version` calls on the
entries of a methods file, resolves each entry's target to its public place in
the stage (`method_targets.resolve_target`), applies the method's placement
rule, and returns a new version whose `bindings.methods` holds every
attachment once, keyed by the resulting builder, sub-builder, operator or
authored definition. Each attachment is a `Method` (its method, handler and
settings). No box and no record carries a method: the new version holds the
argument's graphs, unchanged, and its caller copies it once. Method
attachment adds no analytic, existence or convergence condition.

Every method has a row in `METHOD_TYPES`, the one place a method is named.
The row states its admitted places, typed options and private placement rule.
A method stands at one of three places by what it does
(`docs/Bellman-Sym/04-methodization.md` §3): a handler for a whole builder on
the builder, `!vfi` on the backward decision builder alone; a method that
computes the row whose output is the policy on that row, a maximizer or a
root finder on an `Argmax` row, and `!egm` on one that carries its
first-order condition as a property; a method that stores a function at the
Evaluation that closes it, a representation, and `!egm` named with no block
file at the Evaluation of a policy block that writes the grid line. The
author writes the place of a representation, the Evaluation of a builder
by `<block-id>.evaluate`, `<block-id>.evaluate.value` or
`<block-id>.evaluate.marginal` (AMD-MB-002 §3); a representation named on a
builder or on a derivative line is refused naming that address.

A representation names its basis as the method, `!Linear` or `!pchip`, and
its grid under `settings`: the kind of the grid is the tag on the value of
the setting `grid`, and the grid's fields, `orders` and `bounds`, stand
beside it as settings of the entry; `!egm` names its exogenous grid of
savings the same way (AMD-MB-003 §§1 to 3). The kinds of grid and the fields
each admits are the table `GRID_KINDS`; `!Cartesian` is a kind of grid and
no method.
"""

import dataclasses
from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import NamedTuple

from discopy.frobenius import Box

from bellman.display.cards import method_card
from bellman.fold.block_lines import (
    blocks_in_file_order,
    header_of,
    header_wire_sorts,
    is_implicit_solve,
    is_node,
    require_stage,
)
from bellman.fold.stage_names import StageNames, lines_of
from bellman.native.identity import Identity, box_identity, piece_identity
from bellman.native.labels import is_wiring
from bellman.native.records import Line, Method, MethodOption, bound_at
from bellman.native.versions import replace_stage, stored
from bellman.refusals import (
    GRID_KIND_AS_METHOD,
    GRID_UNDER_EGM,
    GRID_WITHOUT_KIND,
    METHOD_ATTACHMENT,
    REPRESENTATION_ON_BUILDER,
    REPRESENTATION_ON_DERIVATIVE_LINE,
    ConstructionError,
    TargetError,
)
from bellman.stage.boxes import builder_rows_of, merged_lines, names_merged_line
from bellman.stage.grains import graph_of
from bellman.stage.method_blocks import (
    block_source,
    held_source,
    operative_definitions,
    read_blocks,
)
from bellman.stage.method_targets import (
    _is_transition,
    _what_block_is,
    _writes_role,
    backward_builders_to_decision,
    derivative_lines,
    evaluation_addresses,
    is_property,
    properties_of,
    resolve_target,
    target_inventory,
)
from bellman.syntax.vocabulary import CONTINUATION, CONTROL, DECISION, DOC, STATE, VALUE

# --- attaching methods ---

_RESERVED_ENTRY_KEYS = frozenset(("resolved", "attached", "diagnostic", "requirements", "record"))
_BINDING_ENTRY_KEYS = frozenset(("method", "handler", "settings", "block"))


def attach_methods(stage, loaded, *, provenance, base=None):
    """The version of `stage` with loaded choices attached to its places,
    holding the records of `stage`, which its caller copies once: the
    bindings and the definitions table `attached_bindings` answers. The
    factory's routes bind a stage occurrence by it; the verb `methodize`
    writes the same records into the stage it is called on."""
    bindings, definitions = attached_bindings(stage, loaded, base=base)
    changes = {"bindings": bindings, "provenance": provenance}
    if bindings.blocks is not stage.bindings.blocks:
        changes["definitions"] = definitions
    return replace_stage(stage, **changes)


def attached_bindings(stage, loaded, *, base=None, replace_all=False):
    """The bindings of `stage` with the loaded choices attached to its places,
    and its definitions table with what the method blocks they name add: the
    bindings' `methods` holds every attachment once under the name the
    method's placement rule selects after target resolution (AMD-SG-006 §4,
    §7 rule 9), and `blocks` each method block under the builder it opens
    (specification 0.6 §7). `base` is the folder of the methods file, against
    which a block file's path is read. With `replace_all`, the methods and
    the blocks bound before are left out, so that the source's bindings
    replace them as a whole.

    An entry that names no method, handler or setting is resolved and binds
    nothing. An entry whose target resolves to no place is refused. A
    target named by its address governs a box also named by a stage-wide
    operator name; two entries that otherwise reach one box are refused. The
    entries that name a block file are attached first, and the others are
    resolved on the stage with those blocks in place, so that a field a block
    adds is a target of the same file (decision SD-15). A box holds one
    method of each kind, a solution, a representation and a marginal block:
    a later binding of the kind a box holds replaces the earlier one, and a
    binding of another kind stands beside it. Method choices do not solve
    equations or establish analytic, existence or convergence conditions.
    Loading a
    methods source is `load_methods` of `sources.py`; `binding_provenance`
    records it.
    """
    require_stage(stage)
    # a refusal says where, what happened, why and what to write
    # (AMD-SG-006 §6a)
    if "stage" in loaded and loaded["stage"] != stage.name:
        raise ValueError(
            f"stage {stage.name!r}: the methods source names the stage {loaded['stage']!r}; a "
            f"methods file binds the stage it names (spec 0.3c §4.3); write `stage: {stage.name}` "
            f"in the source or apply it to the stage {loaded['stage']!r}"
        )
    blocks = {box.name: box for box in blocks_in_file_order(stage)}
    order = _occurrence_order(stage, blocks)
    with_block = [entry for entry in loaded["methods"] if "block" in entry]
    entries = tuple(_resolved_entry(stage, entry, blocks, order) for entry in with_block)
    held_methods = None if replace_all else stage.bindings.methods
    earlier_blocks = {} if replace_all else dict(stage.bindings.blocks or {})
    bound = dict(earlier_blocks)
    for entry in entries:
        if entry.inadmissible:
            _refuse(stage, *entry.inadmissible[0])
        rule = METHOD_TYPES.get(entry.method.tag)
        if rule is None:
            _refuse(
                stage,
                entry.target,
                f"the entry names the block file {entry.method.block!r} and no method; a "
                "block file is named with a method whose row of the method table takes a "
                "block, such as !egm on the policy builder; write `method: !egm` in the entry",
            )
        for place in entry.places:
            bound[place.block] = block_source(
                entry.method,
                place.block,
                base,
                condition=rule.condition,
                marginal=rule.kind == "marginal block",
            )
    if entries:
        # the blocks bound before and those of the source, read together
        # (specification 0.6 §§4.1, 5.1)
        sources = {
            builder: held_source(block)
            if builder in earlier_blocks and block is earlier_blocks[builder]
            else block
            for builder, block in bound.items()
        }
        bound = read_blocks(stage, tuple(sources.items()))
    held_blocks = MappingProxyType(bound) if bound else None
    if bound != dict(stage.bindings.blocks or {}):
        definitions = operative_definitions(stage, tuple(bound.values()))
        # the lines without a block are resolved on the stage with the
        # blocks in place (decision SD-15)
        placed = replace_stage(
            stage,
            definitions=definitions,
            bindings=replace(stage.bindings, blocks=held_blocks),
        )
    else:
        definitions, placed, held_blocks = (
            stored(stage, "definitions"),
            stage,
            stage.bindings.blocks,
        )
    # the operator occurrences of the blocks' lines are ordered beside the
    # declared ones, so that a stage-wide operator name, `E_Ψ_θ`, reaches
    # an occurrence in a block's line too
    beside = order if placed is stage else {**order, **_occurrence_order(placed, blocks)}
    entries += tuple(
        _resolved_beside_blocks(stage, placed, entry, (blocks, beside), held_blocks)
        for entry in loaded["methods"]
        if "block" not in entry
    )
    pending = tuple(entry for entry in entries if entry.attach)
    inadmissible = [refusal for entry in entries for refusal in entry.inadmissible]
    found, targets = _box_assignments(stage, pending)
    # Existing conflicts take precedence; no pending inadmissible entry
    # is bound.
    _one_method_per_merged_box(placed, found, targets)
    if inadmissible:
        _refuse(stage, *inadmissible[0])
    # the setting names the attachments reference and the conditions they
    # add are queries
    methods = _merged(held_methods, found)
    # the options are checked against the methods bound after the binding,
    # since a representation at the policy builder's Evaluation writes no
    # grid where `!egm` stands in that builder (AMD-MB-003 §1)
    knots = _evaluations_of_egm_pairs(stage, methods)
    for entry in pending:
        rule = METHOD_TYPES.get(entry.method.tag)
        if rule is not None:
            _check_authored_options(stage, entry, rule, knots)
    # a representation an earlier source bound at a policy builder's
    # Evaluation is checked again where this source adds `!egm` in that
    # builder or replaces it by another solution method
    _check_held_representations(stage, held_methods, methods, knots, pending)
    # a block stands while a method naming it holds its builder; a later
    # binding that replaces that method drops the block (decision SA-16)
    named = {_builder_of_box(bound_at(key)) for key, method in methods.items() if method.block}
    if held_blocks and any(builder not in named for builder in held_blocks):
        kept = {builder: block for builder, block in held_blocks.items() if builder in named}
        held_blocks = MappingProxyType(kept) if kept else None
        definitions = operative_definitions(stage, tuple(kept.values()))
    return replace(stage.bindings, methods=methods, blocks=held_blocks), definitions


def _resolved_beside_blocks(stage, placed, entry, context, held_blocks):
    """An entry that names no block file, resolved on the stage with the
    blocks in place (decision SD-15); where it binds a solution method at the
    level of a builder that a solution method's block opens, it replaces that
    method and its block, and it is resolved again on the stage without that
    block, so that it stands where the builder as declared admits it
    (decision SA-16)."""
    blocks, order = context
    found = _resolved_entry(placed, entry, blocks, order)
    # the declared lines a solution block stands in for, which form no
    # operation of the opened builder (specification 0.6 §4.1): a stage-wide
    # operator name reaches no occurrence in them (decision SC-14), and an
    # entry that names one is refused (decision SC-23)
    stands_in = {
        line: block
        for block in (held_blocks or {}).values()
        if _block_kind(block) == "solution"
        for line in block.declared_lines
    }
    if found.stage_wide:
        found = found._replace(
            places=tuple(place for place in found.places if place.address not in stands_in)
        )
    else:
        for place in found.places:
            if place.address in stands_in:
                _refuse_a_line_a_block_stands_in_for(
                    placed, entry, place, stands_in, (blocks, order)
                )
    if not found.attach or binding_kind(found.method) != "solution" or not held_blocks:
        return found
    replaced = {
        place.block
        for place in found.places
        if _builder_of_box(place.box) == place.block
        and place.block in held_blocks
        and _block_kind(held_blocks[place.block]) == "solution"
    }
    if not replaced:
        return found
    kept = {builder: block for builder, block in held_blocks.items() if builder not in replaced}
    without = replace_stage(
        stage,
        definitions=operative_definitions(stage, tuple(kept.values())),
        bindings=replace(stage.bindings, blocks=MappingProxyType(kept) if kept else None),
    )
    return _resolved_entry(without, entry, blocks, order)


def _refuse_a_line_a_block_stands_in_for(placed, entry, place, stands_in, context):
    """The refusal of an entry that names a place in a declared line a
    solution block stands in for: the line is printed under `Declared` and
    forms no operation of the opened builder (specification 0.6 §4.1). The
    refusal names the line, the block and its file, and the block's own
    lines that hold the same operator, `policy.euler.E_Ψ_θ`, or else the
    block's lines (decision SC-23)."""
    block = stands_in[place.address]
    own = ()
    if place.operator is not None:
        named = _resolved_entry(placed, {**entry, "on": place.operator}, *context)
        own = tuple(
            f"{other.address}.{other.operator}"
            for other in named.places
            if other.block == block.builder and other.address not in stands_in
        )
    if not own:
        own = tuple(
            str(record.address)
            for record in block.definitions
            if record.kind == "line" and str(record.address).startswith(block.builder + ".")
        )
    _refuse(
        placed,
        entry["on"],
        f"names a place in the line {place.address}, the declared line of the builder "
        f"{block.builder!r}, which the method block {block.block!r} of {block.path} stands in "
        "for; the line is printed under `Declared` and forms no operation of the opened "
        "builder (specification 0.6 §4.1); write the target in a line of the block"
        + (f", such as {', '.join(own)}" if own else ""),
    )


def _block_kind(block):
    """The kind of the method that binds a block, its row's `kind`."""
    rule = METHOD_TYPES.get(block.tag)
    return rule.kind if rule is not None else "solution"


def _builder_of_box(box):
    """The builder a box stands at the level of: the builder a box name
    names, or the builder whose closing Evaluation the box is; None for any
    other box, an operator, a node or a definition."""
    if isinstance(box, str):
        return box if "." not in box else None
    if isinstance(box, Identity) and box.kind == "Evaluation":
        address = str(box.address or "")
        return address if address and "." not in address else None
    return None


def _merged(held, found):
    """The methods bound after a binding: those `held` already and those
    `found`, a box holding one method of each kind (decision SD-15): a method
    of the kind a box holds already replaces that one under its key, and a
    method of another kind stands beside it, under the pair (box, kind). Two
    solution methods at the level of one builder, on the builder or at its
    closing Evaluation, are of one target, and the later replaces the
    earlier (decision SA-16)."""
    merged = dict(held or {})
    for key, method in found.items():
        box, kind = bound_at(key), binding_kind(method)
        level = _builder_of_box(box) if kind == "solution" else None
        same = next(
            (
                held_key
                for held_key, held_method in merged.items()
                if binding_kind(held_method) == kind
                and (
                    bound_at(held_key) == box
                    or (level is not None and _builder_of_box(bound_at(held_key)) == level)
                )
            ),
            None,
        )
        if same is not None and bound_at(same) == box:
            merged[same] = method
            continue
        if same is not None:
            del merged[same]
        if any(bound_at(held_key) == box for held_key in merged):
            merged[box, kind] = method
        else:
            merged[box] = method
    return merged


def binding_kind(method):
    """The kind of a bound method, its row's `kind`: a solution method, such
    as `!egm` or `!vfi`, a representation method, such as `!Linear` or
    `!deterministic`, or a marginal block, `!marginals` (decision SD-15). An
    entry that names a handler and no method is a solution."""
    rule = METHOD_TYPES.get(method.tag)
    return rule.kind if rule is not None else "solution"


def attached_methods(stage):
    """The attachments of a stage as `(box name, Method)` pairs, read from
    `bindings.methods` in the order the entries attached. Empty before
    methodization."""
    require_stage(stage)
    return tuple((stage.bindings.methods or {}).items())


def admitted_methods(stage, target):
    """The tags of the method table `method_types`, in its order, that
    `methodize` attaches at the target `target` of `stage`: each method whose
    `admits` holds the kind of every place an entry naming it resolves the
    target to, and whose placement rule stands it at each, so that `!egm` is
    admitted at a block that writes the grid line or at a maximization that
    carries its first-order condition as a property, and `!vfi` at the
    backward decision builder alone.

    The target is resolved as `methodize` resolves it (`resolve_target`), and
    a target that reaches no place is refused by its `TargetError`. Each
    method is tried at the place alone: the options an entry must write,
    which the entry supplies and the place does not, are not checked, nor are
    the other entries of a methods file. The Methods tab of Bellman Workbench
    offers these tags at the target (model interface specification 0.4, unit
    L, Task 18)."""
    require_stage(stage)
    resolved = resolve_target(stage, target)
    blocks = {box.name: box for box in blocks_in_file_order(stage)}
    return tuple(
        f"!{tag}"
        for tag, rule in METHOD_TYPES.items()
        if _stands_at(stage, target, resolved, blocks, tag, rule)
    )


def _stands_at(stage, target, resolved, blocks, tag, rule) -> bool:
    """Whether the method `tag`, whose row of the method table is `rule`,
    stands at the places `resolved`, the resolution of `target`, names, as
    `_resolved_entry` attaches an entry naming that method: the method
    admits the kind of every place an entry naming it resolves to, and its
    placement rule stands it at each, refusing none."""
    try:
        places = attachment_places(
            stage,
            target,
            resolved,
            True,
            representation=rule._place is _representation_place,
        )
        if any(_kind_of(place) not in rule.admits for place in places):
            return False
        for place in places:
            rule._place(stage, target, place, blocks, tag)
    except (ValueError, LookupError):
        # a refusal of the place, a TargetError, or of the rows of a builder
        # the construction refuses, a ConstructionError
        return False
    return True


def _occurrence_order(stage, blocks):
    """The position of every operator occurrence of the stage, by its line's
    address, its stage-wide name and its position in the line: the block's
    place in the file, the line's ordinal and the occurrence's place in the
    line, by which the places of a stage-wide operator name are ordered."""
    order = {}
    for block_index, block in enumerate(blocks.values()):
        for _, record in lines_of(stage, block):
            for index, op in enumerate(record.operators):
                order[record.address, op.stage_wide_name, op.position] = (
                    block_index,
                    record.ordinal,
                    index,
                )
    return order


class _ResolvedEntry(NamedTuple):
    """One authored entry of a methods source, resolved: its target and
    method, the places it binds the method at, the statements among them,
    whether it names the target by a stage-wide operator name, whether it
    binds anything, and the refusal of each place its method does not admit,
    which waits until every entry is resolved."""

    target: str
    method: object
    places: tuple
    components: frozenset
    stage_wide: bool
    attach: bool
    inadmissible: tuple


def _resolved_entry(stage, entry, blocks, order):
    """The `_ResolvedEntry` of one authored entry: a key the entry may not
    write, a target that reaches no place and an unknown method refused, each
    place its method admits replaced by the place its placement rule
    selects."""
    collision = _RESERVED_ENTRY_KEYS.intersection(entry)
    if collision:
        raise ValueError(
            f"authored methods entry uses reserved metadata: {tuple(sorted(collision))!r}"
        )
    target, attach = entry["on"], bool(_BINDING_ENTRY_KEYS.intersection(entry))
    method = _method(entry)
    if "grid" in entry:
        _refuse(
            stage,
            target,
            "the entry writes `grid` beside `method`, which is not read: a grid is a setting "
            "of the entry, its kind the tag on the value of `grid` and its fields beside it; "
            "write `grid: !Cartesian` under `settings`, with `orders` and `bounds` beside it",
        )
    if attach and method.tag in GRID_KINDS:
        _refuse(
            stage,
            target,
            f"!{method.tag} is a kind of grid and not a method; write the basis as the method, "
            "`method: !Linear` for piecewise linear interpolation or `method: !pchip` for "
            "shape-preserving cubic interpolation, and the grid as its setting, "
            f"`grid: !{method.tag}` under "
            "`settings` with `orders` and `bounds` beside it",
            rule=GRID_KIND_AS_METHOD,
        )
    rule = METHOD_TYPES.get(method.tag)
    places = attachment_places(
        stage,
        target,
        resolve_target(stage, target),
        attach,
        representation=bool(rule and rule._place is _representation_place),
    )
    # the statements and the written Evaluations an entry names, by which two
    # entries of one method at one Evaluation join (decision SD-15): the value
    # and its stated derivative, `<block-id>.evaluate.value` and
    # `<block-id>.evaluate.marginal`, are two such names of one box
    components = frozenset(
        place.address for place in places if place.kind == "statement"
    ) | frozenset(target for place in places if place.evaluates)
    stage_wide = (
        "." not in target
        and target not in blocks
        and all(place.kind == "operator" for place in places)
    )
    if places and all(place.kind == "operator" and not place.evaluates for place in places):
        places = tuple(
            sorted(places, key=lambda place: order[place.address, place.operator, place.position])
        )
    if attach and method.tag is not None and rule is None:
        message = (
            f"unknown method !{method.tag}; method-attachment requires a public method type; "
            "write a tag listed by `method_types` of bellman.stage"
        )
        _refuse(stage, target, message)
    inadmissible = []
    if attach and rule is not None:
        resolved = []
        for place in places:
            kind = _kind_of(place)
            if place.kind == "builder" and rule._place is _representation_place:
                _refuse_representation_on_builder(stage, target, place, method.tag, blocks)
            if kind not in rule.admits:
                admitted = ", ".join(
                    " ".join(k) if isinstance(k, tuple) else k for k in rule.admits
                )
                named = " ".join(kind) if isinstance(kind, tuple) else kind
                inadmissible.append(
                    (
                        target,
                        f"!{method.tag} does not admit target kind {named}; "
                        f"method-attachment admits {admitted}; {_write_instead(stage, rule)}",
                    )
                )
                resolved.append(place)
                continue
            if method.block is not None:
                resolved.append(_block_place(stage, target, place, rule, method, blocks))
                continue
            resolved.append(rule._place(stage, target, place, blocks, method.tag))
        places = tuple(resolved)
    return _ResolvedEntry(
        target=target,
        method=method,
        places=places,
        components=components,
        stage_wide=stage_wide,
        attach=attach,
        inadmissible=tuple(inadmissible),
    )


def _box_assignments(stage, pending):
    """The methods each box holds, one of each kind (decision SD-15), and the
    target that bound each, the entries named by a stage-wide operator name
    first: an entry named by its address governs a box a stage-wide name also
    reaches, one method bound to lines no other entry of the box binds joins
    them, and two entries of one kind that otherwise reach one box are
    refused. A method stands under its box, and a method of another kind at
    a box that holds one already under the pair (box, kind)."""
    found, priorities, targets, output_lines = {}, {}, {}, {}
    for entry in sorted(pending, key=lambda item: not item.stage_wide):
        for place in entry.places:
            box, slot = place.box, (place.box, binding_kind(entry.method))
            if slot in found:
                if (
                    found[slot] == entry.method
                    and entry.components
                    and output_lines[slot]
                    and entry.components.isdisjoint(output_lines[slot])
                ):
                    output_lines[slot] |= entry.components
                    continue
                if not (priorities[slot] and not entry.stage_wide):
                    raise ValueError(
                        f"stage {stage.name!r}, box {box!r}: the targets {targets[slot]!r} and "
                        f"{entry.target!r} conflict, both reaching it with a method; a box holds "
                        "one method (AMD-SG-006 §4, rule 9); write one entry for that box"
                    )
            found[slot], priorities[slot], targets[slot] = (
                entry.method,
                entry.stage_wide,
                entry.target,
            )
            output_lines[slot] = entry.components
    keyed, named = {}, {}
    for (box, kind), method in found.items():
        key = (box, kind) if any(bound_at(held) == box for held in keyed) else box
        keyed[key], named[key] = method, targets[box, kind]
    return keyed, named


def _method(entry):
    """The `Method` of an authored entry: its method tag without the `!`, its
    handler, and its settings — the entry's `settings` and the payload of a
    tagged method mapping (`!Linear {grid: !Cartesian, orders: …, bounds: …}`).
    A grid a mapping source
    writes as the string `"!Cartesian"` is held as the reader holds the tag
    `!Cartesian` a methods file writes, `{"__yaml_tag__": "Cartesian",
    "value": ""}`, as a method written `"!Linear"` is read as the tag
    `!Linear` (AMD-MB-003 §3)."""
    value = entry.get("method")
    settings = {}
    if isinstance(value, Mapping):
        # the loader writes a bare tag `!<name>` as
        # {'__yaml_tag__': '<name>', 'value': ''}
        name = value.get("__yaml_tag__")
        settings.update(
            (key, item)
            for key, item in value.items()
            if key != "__yaml_tag__" and not (key == "value" and item == "")
        )
    else:
        name = value
    if name is not None:
        name = name.removeprefix("!")
    settings.update(entry.get("settings", {}))
    grid = settings.get("grid")
    if isinstance(grid, str) and grid.startswith("!"):
        settings["grid"] = {"__yaml_tag__": grid[1:], "value": ""}
    return Method(name, entry.get("handler"), settings, block=entry.get("block"))


@dataclasses.dataclass(frozen=True)
class _AttachmentPlace:
    """The place a method target resolves to (AMD-SG-018 §2): its `kind`, one
    of `builder`, `node`, `statement`, `operator` and `definition`; the
    `block` that holds it; the `address` of the line or of the definition
    where it has one; the stage-wide name and the `position` of an operator
    occurrence where it is one; `box`, the name of the box the attachment
    binds the method to; and `evaluates`, for the Evaluation of a builder
    named by its written address, what it evaluates, `policy`, `value` or
    `marginal` (AMD-MB-002 §3). Exists during one attachment."""

    kind: str
    block: str
    address: object = None
    operator: str | None = None
    position: tuple = ()
    box: object = None
    head: str | None = None
    evaluates: str | None = None


def _kind_of(place):
    """The kind of a place as the `admits` of a method's row writes it: the
    pair `("operator", <head>)` for an operator occurrence, `("operator",
    "E")`, and the place's kind otherwise."""
    return (place.kind, place.head) if place.kind == "operator" else place.kind


def attachment_places(stage, target, resolved, attach, representation=False):
    """The places a resolution names, each with the box it resolves to,
    without interpreting a method name."""
    if isinstance(resolved, tuple) and len(resolved) == 2 and resolved[0] == "definition":
        return (
            _AttachmentPlace(
                "definition", stage.name, resolved[1].identity, box=resolved[1].identity
            ),
        )
    if isinstance(resolved, Box):
        if is_node(resolved):
            return (
                _AttachmentPlace(
                    "node", _owner(stage, resolved), resolved.name, box=resolved.name
                ),
            )
        return (_AttachmentPlace("builder", resolved.name, box=resolved.name),)
    if len(resolved) == 3 and isinstance(resolved[0], str) and resolved[0] == "evaluation":
        # the Evaluation of a builder by its written address (AMD-MB-002 §3)
        _, box, evaluates = resolved
        return (_evaluation_place(box.name, box.name, evaluates),)
    if len(resolved) == 2 and isinstance(resolved[1], Line):
        holder, record = resolved
        implicit = [op for op in record.operators if is_implicit_solve(op)]
        if len(implicit) == 1 and not representation:
            return (_operator_place(stage, _owner(stage, holder), record, implicit[0]),)
        if len(implicit) > 1 and not representation:
            _refuse(stage, target, "ambiguous implicit solve occurrences")
        if attach and (record.role != "output" or (record.operators and not representation)):
            _refuse(
                stage,
                target,
                "this statement does not accept a representation method; "
                "name an actual operator with its explicit .operator address",
            )
        return (
            _AttachmentPlace(
                "statement", _owner(stage, holder), record.address, box=record.address
            ),
        )
    return tuple(_operator_place(stage, _owner(stage, place[0]), *place[1:]) for place in resolved)


def _operator_place(stage, block, statement, occurrence):
    return _AttachmentPlace(
        kind="operator",
        block=block,
        address=statement.address,
        operator=occurrence.stage_wide_name,
        position=occurrence.position,
        box=_operator_box(stage, block, statement, occurrence),
        head=occurrence.head,
    )


def _evaluation_place(block, address, evaluates=None):
    """The place of the Evaluation that closes `address` in the builder
    `block`, the builder itself or a `!node` line of it: the operator
    `evaluate` whose box is `<address>:Evaluation`, with what it evaluates
    where the target names the Evaluation of the builder by its written
    address (AMD-MB-002 §3)."""
    return _AttachmentPlace(
        kind="operator",
        block=block,
        address=address,
        operator="evaluate",
        box=Identity("Evaluation", address=address),
        head="evaluate",
        evaluates=evaluates,
    )


def _operator_box(stage, block, statement, occurrence):
    """The name of the primitive box that represents an occurrence: the
    expectation row born of the line; for a `solve` or an `argmax`, the row
    of the builder born at the line whose outputs are its own unknowns
    (`row.unknowns` of the construction table), the `Argmax` row of a
    maximization and the row of a solve's residuals; the line itself for an
    operator written as a call (`evaluate`, `upper_env`), which the fold
    carries inside the line's map, and for a choice whose row the
    construction table does not single out."""
    if occurrence.head == "E":
        n = 1 + sum(
            1
            for o in statement.operators[: statement.operators.index(occurrence)]
            if o.head == "E"
        )
        return Identity("Expectation", address=statement.address, occurrence=n)
    if occurrence.head in ("solve", "argmax"):
        try:
            rows = builder_rows_of(stage, block).opened
        except ConstructionError:
            rows = ()
        own = [row for row in rows if row.identity.address == statement.address and row.unknowns]
        if len(own) == 1:
            return own[0].identity
    return piece_identity(statement.address)


def _owner(stage, holder):
    """The name of the builder that is this retained box or holds it among
    its lines."""
    for builder in blocks_in_file_order(stage):
        if holder is builder or any(box is holder for box, _ in lines_of(stage, builder)):
            return builder.name
    raise ValueError("a method target has no owning builder in this stage")


def _refuse(stage, target, message, candidates=None, rule=METHOD_ATTACHMENT):
    raise TargetError(
        target=target,
        stage=stage.name,
        rule=rule,
        candidates=target_inventory(stage) if candidates is None else candidates,
        message=f"Method target {target!r} in stage {stage.name!r}: {message}",
    )


def _refuse_representation_on_builder(stage, target, place, tag, blocks):
    """The refusal of a representation named on a builder, in one sentence
    naming the written address of the builder's Evaluation, where a
    representation is attached (AMD-MB-002 §4)."""
    box = blocks[place.block]
    written = evaluation_addresses(stage, box)
    if written:
        named = " or ".join(f"`on: {address}`" for address in written)
        sentence = (
            f"!{tag} is a representation, attached to the Evaluation of a builder and not to "
            f"the builder; write {named}"
        )
    elif _is_transition(stage, box):
        evaluations = ", ".join(
            f"`on: {address}`"
            for other in blocks.values()
            for address in evaluation_addresses(stage, other)
        )
        sentence = (
            f"!{tag} is a representation, attached to the Evaluation of the policy builder or "
            f"of a backward value builder, and {place.block!r} is a forward builder, the "
            "push-forward of a measure through its law of motion, which closes with no "
            "Evaluation; write the representation at one of the stage's Evaluations, "
            f"{evaluations or 'of which the stage has none'}, or bind on {place.block!r} a "
            "method of its law of motion, `!deterministic`, `!monte-carlo`, `!histogram` or "
            "`!identity`"
        )
    else:
        sentence = (
            f"!{tag} is a representation, attached to the Evaluation of the policy builder or "
            f"of a backward value builder, and {place.block!r} is "
            f"{_what_block_is(stage, box)}, which writes neither a value nor a policy and has "
            "no Evaluation a representation is attached to"
        )
    _refuse(stage, target, sentence, rule=REPRESENTATION_ON_BUILDER)


def _one_method_per_merged_box(stage, found, targets):
    """The refusal of two different methods bound to lines the primitive
    grain reads as one box (AMD-SG-011 §3). A merged box is one operator, so
    it holds one method; the author keeps two computations apart, and two
    methods, by marking one line `!node`. Two entries that bind the same
    method to both lines are admitted. A stage whose backward cut is refused
    has no primitive grain and is left alone."""
    if not found:
        return
    try:
        graph = graph_of(stage, "builders", "backward", "primitive")
    except Exception:
        return  # a stage whose backward cut is refused has no primitive grain
    for box in graph.boxes:
        if is_wiring(box):
            continue
        lines = set(merged_lines(stage, box))
        kind = box_identity(box).kind
        bound = [(key, found[key]) for key in found if names_merged_line(key, lines, kind)]
        if len(bound) < 2:
            continue
        first, second = bound[0], next(((m, k) for m, k in bound[1:] if k != bound[0][1]), None)
        if second is None:
            continue
        lines = [key.address for key, _ in (first, second)]
        raise TargetError(
            target=targets[second[0]],
            stage=stage.name,
            rule=METHOD_ATTACHMENT,
            candidates=target_inventory(stage),
            message=f"Method target {targets[second[0]]!r} in stage {stage.name!r}: the lines "
            f"{lines[0]} and {lines[1]} are one box, {box.name}, at the primitive grain, and the "
            f"targets {targets[first[0]]!r} and {targets[second[0]]!r} bind two methods to it; a "
            "box holds one method (AMD-SG-006 §4, rule 9). Write one method for both lines, or "
            "write `!node` in the annotation of one of them, "
            "so that the two computations stay two boxes.",
        )


def _check_authored_options(stage, entry, rule, knots):
    """The check of the keys an entry writes against its method's option
    record and the fields of the grid kind its setting `grid` names
    (AMD-MB-003 §3). A grid written on the policy builder's Evaluation where
    `!egm` stores the knots there (`knots`), the fields of a grid written
    without its kind, and a value of `grid` that names no kind of the table
    `GRID_KINDS` are refused, each in one sentence; a representation at such
    an Evaluation writes no grid, and one at an authored `evaluate(knots,
    values, x)` occurrence, whose first argument holds its knots, needs none.
    Then a required key the entry omits is refused, and so is a key that
    neither the row nor the grid's kind admits where the entry names no
    handler to read it."""
    target, method = entry.target, entry.method
    written = set(method.settings)
    representation = "grid" in rule.options and rule.kind == "representation"
    at_knots = representation and any(place.box in knots for place in entry.places)
    authored = (
        representation
        and bool(entry.places)
        and all(
            place.kind == "operator"
            and place.head == "evaluate"
            and getattr(place.box, "kind", None) != "Evaluation"
            for place in entry.places
        )
    )
    fields = tuple(field for field in GRID_FIELDS if field in written)
    if at_knots and ("grid" in written or fields):
        shown = _listed(("grid",) * ("grid" in written) + fields)
        _refuse(
            stage,
            target,
            f"!{method.tag} at the Evaluation of the policy builder interpolates the policy "
            "between the pairs of the decision state and the control that !egm computes at the "
            "points of its exogenous grid and stores there, which are its knots, so the entry "
            f"writes no grid; remove {shown} from its settings, the exogenous grid standing in "
            "the settings of the !egm entry",
            rule=GRID_UNDER_EGM,
        )
    if "grid" in rule.options and "grid" not in written and fields:
        shown = _listed(fields)
        _refuse(
            stage,
            target,
            f"!{method.tag} writes {shown} without the setting `grid`; a grid is written by its "
            "kind, the tag on the value of `grid`, with its fields beside it: write "
            f"`grid: !Cartesian` in the entry's settings beside {shown}",
            rule=GRID_WITHOUT_KIND,
        )
    if "grid" in rule.options and "grid" in written:
        _check_grid_kind(stage, target, method)
    options = admitted_options(
        rule, method.settings, knots="stored" if at_knots else "authored" if authored else None
    )
    required = {name for name, option in options.items() if option.required}
    missing = tuple(sorted(required - written))
    unknown = tuple(sorted(written - set(options)))
    if missing:
        details = f"missing required option{'' if len(missing) == 1 else 's'} {', '.join(missing)}"
        if unknown:
            details += f"; unknown option{'' if len(unknown) == 1 else 's'} {', '.join(unknown)}"
        grid = (
            "; a grid is the setting `grid: !Cartesian` with `orders` and `bounds` beside it"
            if "grid" in missing
            else ""
        )
        _refuse(
            stage,
            target,
            f"!{method.tag} has {details}; write every required option using "
            f"the keys shown by method_types of bellman.stage{grid}",
        )
    if unknown and method.handler is None:
        _refuse(
            stage,
            target,
            f"!{method.tag} has unknown option{'' if len(unknown) == 1 else 's'} "
            f"{', '.join(unknown)} and names no handler; "
            "remove them or name the handler that reads them",
        )


def _check_held_representations(stage, held, methods, knots, pending):
    """The refusal of a representation an earlier source bound at the
    Evaluation of a policy builder, which the source being bound leaves in
    place, where that source makes the Evaluation a place whose knots `!egm`
    computes (`knots`) or no longer one (AMD-MB-003 §1): a representation
    that writes a grid where `!egm` now stands in the builder is refused
    under `grid-under-egm`, and one that writes no grid where `!egm` no
    longer stands there under `method-attachment`. Each refusal names, as its
    target, the entry of the source that binds the solution method in that
    builder, and asks in one sentence for the representation to be written
    again in the same source at its written address, `<block-id>.evaluate`,
    without a grid or with one."""
    before = _evaluations_of_egm_pairs(stage, held or {})
    for key, method in methods.items():
        box = bound_at(key)
        if box not in before ^ knots or (held or {}).get(key) is not method:
            continue
        if binding_kind(method) != "representation":
            continue
        builder = _builder_holding(box)
        written = f"{builder}.evaluate"
        solution = next(
            (
                entry
                for entry in pending
                if binding_kind(entry.method) == "solution"
                and any(_builder_holding(place.box) == builder for place in entry.places)
            ),
            None,
        )
        target = solution.target if solution is not None else written
        named = (
            f"!{solution.method.tag}"
            if solution is not None and solution.method.tag
            else (solution.method.handler if solution is not None else "a solution method")
        )
        if box in knots and "grid" in method.settings:
            _refuse(
                stage,
                target,
                f"!egm now stands in the policy builder {builder!r}, and !{method.tag}, bound "
                f"at its Evaluation by an earlier source, writes a grid there, where the knots of "
                "its interpolant are the pairs of the decision state and the control that !egm "
                f"computes; write the representation again in this source at `{written}` without "
                "a grid",
                rule=GRID_UNDER_EGM,
            )
        if box in before - knots and "grid" not in method.settings:
            _refuse(
                stage,
                target,
                f"{named} replaces !egm in the policy builder {builder!r}, and !{method.tag}, "
                "bound at its Evaluation by an earlier source, writes no grid, which it needs "
                "once !egm no longer computes its knots; write the representation again in this "
                f"source at `{written}` with its grid, `grid: !Cartesian` with `orders` and "
                "`bounds` beside it",
            )


def _listed(names):
    """The names `names` in code type, the last two joined by `and`, the
    others by commas."""
    shown = [f"`{name}`" for name in names]
    return " and ".join(shown) if len(shown) < 3 else ", ".join(shown[:-1]) + " and " + shown[-1]


def _check_grid_kind(stage, target, method):
    """The refusal of a value of the setting `grid` that names no kind of
    grid: a value that is no tag written alone, such as a setting name
    written in the place of the kind, a kind the table `GRID_KINDS` does not
    hold, or the grid's fields written inside the tag, which stand beside it
    (AMD-MB-003 §3)."""
    value = method.settings["grid"]
    kind = grid_kind(value)
    if kind in GRID_KINDS:
        return
    if isinstance(value, Mapping) and "__yaml_tag__" in value and kind is None:
        written = f"the fields of its grid inside the tag !{value['__yaml_tag__']}"
    elif kind is not None:
        written = f"the tag !{kind}, which is no kind of grid"
    else:
        written = f"{value!r}, which is no tag naming a kind of grid"
    kinds = ", ".join(f"!{name}" for name in GRID_KINDS)
    _refuse(
        stage,
        target,
        f"!{method.tag} writes under `grid` {written}; the value of `grid` is the tag of the "
        f"grid's kind written alone, one of {kinds}, and the grid's fields stand beside it in "
        "the entry's settings: write `grid: !Cartesian` with `orders` and `bounds` beside it",
    )


def grid_kind(value):
    """The kind of grid a value of the setting `grid` names, the tag on the
    value without its `!`, `Cartesian`, where the value is a tag written
    alone, as the reader of a methods file holds it,
    `{"__yaml_tag__": "Cartesian", "value": ""}`; None for any other value.
    The kind is a word of the entry and no setting name, so `configure` reads
    no value for it (AMD-MB-003 §3)."""
    if (
        isinstance(value, Mapping)
        and set(value) == {"__yaml_tag__", "value"}
        and value["value"] == ""
    ):
        return value["__yaml_tag__"]
    return None


def admitted_options(rule, settings, *, knots=None):
    """The options an entry of the method whose row is `rule` admits, each
    with its `MethodOption`: the row's options, and beside a setting `grid`
    that names a kind of `GRID_KINDS` the fields that kind admits
    (AMD-MB-003 §3). Where the knots of a representation are given, it
    admits no grid at the policy builder's Evaluation where `!egm` stores
    them, `knots="stored"`, and requires none at an authored `evaluate`
    occurrence, whose first argument holds them, `knots="authored"`.
    `methodize` checks the keys an entry writes against these options and
    `configure` the values it binds."""
    options = {
        name: replace(option, required=False) if knots == "authored" and name == "grid" else option
        for name, option in rule.options.items()
        if not (knots == "stored" and name == "grid")
    }
    kind = grid_kind(settings.get("grid")) if "grid" in options else None
    if kind in GRID_KINDS:
        options.update(GRID_KINDS[kind])
    return options


def _evaluations_of_egm_pairs(stage, methods):
    """The Evaluations whose interpolant's knots `!egm` stores: the closing
    Evaluation of each policy builder, a builder that writes a control, in
    which `!egm` is bound, on the builder, at its Evaluation or on a row of
    its lines, among the methods `methods` (AMD-MB-003 §1)."""
    builders = {box.name: box for box in blocks_in_file_order(stage)}
    held = {
        _builder_holding(bound_at(key)) for key, method in methods.items() if method.tag == "egm"
    }
    return frozenset(
        Identity("Evaluation", address=name)
        for name in held
        if name in builders and _writes_role(stage, builders[name], (CONTROL,))
    )


def _builder_holding(box):
    """The block id of the builder a bound box stands in, the first part of
    the box's address: the builder a box name names, or the builder whose
    Evaluation, row or line the box is; None for a box with no address."""
    address = box if isinstance(box, str) else getattr(box, "address", None)
    return str(address).split(".")[0] if address else None


# --- the method table, its parts first ---


@dataclasses.dataclass(frozen=True)
class _MethodType(Mapping):
    """One authoritative method row.

    The mapping exposes the two parts of AMD-SG-025. Placement remains private
    implementation data in this row.
    """

    admits: tuple
    options: Mapping
    _place: object
    _tag: str
    # the columns of specification 0.6 decision 2 as AMD-MB-001 §5.2 amends
    # them, read as attributes and not among the two parts of the mapping:
    # whether the method takes a block, the name of the condition its
    # construction requires, which `stage.obligations()` lists, and the
    # derivatives a representation evaluates, by order, with the sentence
    # that says what they are; what a method reads is read from the rows
    # of the block it binds (`stage_answers.derivative_reads`)
    takes_block: bool = False
    condition: str | None = None
    derivatives: tuple = ()
    evaluates: str | None = None
    # the kind of binding the method makes, of which a target holds one
    # (decision SD-15): `solution`, `representation` or `marginal block`
    kind: str = "solution"

    def __post_init__(self):
        object.__setattr__(self, "admits", tuple(self.admits))
        object.__setattr__(self, "options", MappingProxyType(dict(self.options)))

    def __getitem__(self, key):
        if key not in ("admits", "options"):
            raise KeyError(key)
        return getattr(self, key)

    def __iter__(self):
        return iter(("admits", "options"))

    def __len__(self):
        return 2

    def __hash__(self):
        return hash(
            (
                self.admits,
                frozenset(self.options.items()),
                self._place,
                self._tag,
                self.takes_block,
                self.condition,
                self.derivatives,
                self.evaluates,
                self.kind,
            )
        )

    def __str__(self):
        return method_card(self)

    __repr__ = __str__


def _method_type(
    tag,
    admits,
    options=None,
    *,
    place,
    block=False,
    condition=None,
    kind=None,
    derivatives=(),
    evaluates=None,
):
    """One named row of the method table, `(tag, _MethodType)`, the tag
    written once, with the columns of specification 0.6 decision 2 as
    AMD-MB-001 §5.2 amends them: whether the method takes a block, the
    condition its construction requires, and for a representation the
    derivatives it evaluates, by order, with the sentence that says what
    they are; and the kind of binding it makes (decision SD-15), a
    representation for a method placed at the Evaluation that stores a
    function and a solution otherwise, unless `kind` names it."""
    if kind is None:
        kind = "representation" if place is _representation_place else "solution"
    return tag, _MethodType(
        admits=admits,
        options=options or {},
        _place=place,
        _tag=tag,
        takes_block=block,
        condition=condition,
        kind=kind,
        derivatives=tuple(derivatives),
        evaluates=evaluates,
    )


# --- the placement rules: each takes the stage, the target as written, the
# place it resolves to, the blocks by name and the method's tag, and answers
# the place the method stands at or refuses it ---


def _egm_place(stage, target, place, blocks, tag):
    """The place `!egm` stands at, read from the lines of the block its
    target names.

    A block that writes the grid line, a line whose left side is a decision
    coordinate under the continuation mark (`m_d[>] = a + c[>]` in `cons.bl`),
    gives the candidate and the cash on hand at each saving by its lines
    alone, and the relation of its identification holds at every such pair,
    so the method stores the policy from those pairs and stands at the
    Evaluation that closes the block, which `_closing_evaluation` finds. A
    block whose maximization is operative and carries its first-order
    condition as a property, attached by a dotted id (`optimality.euler`),
    has that maximization as the row that outputs the policy; the method
    inverts the property and stands on that row, as it does where the target
    names the maximization. Any other place is refused, with the reason."""
    block = blocks[place.block]
    if place.kind == "builder":
        if _grid_lines(stage, block):
            return _closing_evaluation(stage, target, place.block, place.block)
        choices = _maximizations_with_a_property(stage, block)
        if len(choices) == 1:
            record, occurrence = choices[0]
            return _operator_place(stage, block.name, record, occurrence)
        if choices:
            named = ", ".join(f"{record.address}.argmax" for record, _ in choices)
            _refuse(
                stage,
                target,
                f"block {block.name!r} writes {len(choices)} maximizations that carry a "
                f"first-order condition as a property, and !{tag} stands on one of them; "
                f"name it by its occurrence, {named}",
            )
        _refuse(
            stage,
            target,
            f"!{tag} is written on the policy builder by its block id, `on: {block.name}`, "
            "with `block:` naming a method block, or with no block where the policy block "
            "writes the grid line, a line whose left side is a decision coordinate under the "
            "continuation mark such as `m_d[>] = a + c[>]`, or on a maximization that "
            "carries its first-order condition as a property by a dotted id such as "
            f"`optimality.euler`; block {block.name!r} writes neither the grid line nor such "
            "a maximization; name a method block under `block:`, write the grid line in the "
            "block, or attach to the row that outputs its policy a method that computes it, "
            "such as a root finder",
        )
    if _conditions_attached(stage, block, place.address):
        return place
    _refuse(
        stage,
        target,
        f"!{tag} stands on a maximization that carries its first-order condition as a "
        "property, attached by a dotted id such as `optimality.euler`, which the method "
        f"inverts; the line {place.address} carries no property; write the condition under "
        "the id of the maximization followed by a dot and a name, or attach a maximizer "
        "to the maximization",
    )


def _grid_lines(stage, block):
    """The addresses of the grid lines of a block: its operative lines whose
    left side is a decision coordinate under the continuation mark, a field
    at the continuation perch whose name is a state of the decision perch
    (`m_d[>]` in `cons.bl`, `m[>]` in `adjuster_cons.bl`). A line marked
    `!doc` and a property are not operative."""
    names, sorts = StageNames(stage), header_wire_sorts(stage)
    lines = lines_of(stage, block)
    found = []
    for _, record in lines:
        if record.role == DOC or record.core is None or is_property(lines, record):
            continue
        for defined in names.defined(record.core, block.name):
            if defined.perch != CONTINUATION or not defined.field:
                continue
            coordinate = Identity("field", stage=stage.name, perch=DECISION, field=defined.field)
            if coordinate in sorts and sorts[coordinate].role == STATE:
                found.append(record.address)
                break
    return tuple(found)


def _maximizations_with_a_property(stage, block):
    """The operative maximizations of a block that carry a property, each as
    the line and its `argmax` occurrence, in the order of the lines."""
    lines = lines_of(stage, block)
    return tuple(
        (record, occurrence)
        for _, record in lines
        if record.role != DOC
        and not is_property(lines, record)
        and _conditions_attached(stage, block, record.address)
        for occurrence in record.operators
        if occurrence.head == "argmax"
    )


def _conditions_attached(stage, block, address):
    """The properties of the line at `address` that state a condition, the
    first-order condition `optimality.euler` of a maximization: its
    properties not marked `!doc`, which document and state nothing."""
    return tuple(record for record in properties_of(stage, block, address) if record.role != DOC)


def _block_place(stage, target, place, rule, method, blocks):
    """The place of a method entry that names a block file: the builder its
    target names, which the block opens (specification 0.6 §4), or for
    `!marginals` the Evaluation of the value builder the block adds lines to
    (§5.1). A method whose row takes no block and a target that names no
    builder are refused with the reason."""
    if not rule.takes_block:
        _refuse(
            stage,
            target,
            f"!{method.tag} takes no block, and the entry names the block file "
            f"{method.block!r}; a block file is named by a method whose row of the method "
            "table takes a block, such as !egm on the policy builder; remove `block:` from "
            "the entry or name such a method",
        )
    if place.kind != "builder":
        _refuse(
            stage,
            target,
            f"a method block opens a builder, and the target names a {place.kind}; write "
            "the builder's block id as the target, such as `on: policy`",
        )
    if rule._place is _marginals_place:
        return _marginal_block_place(stage, target, place, blocks, method.tag)
    return place


def _marginals_place(stage, target, place, blocks, tag):
    """The place rule of `!marginals` for an entry that names no block file,
    which it refuses: the method adds the lines of a marginal block, and an
    entry with `block:` is placed by `_marginal_block_place`. So
    `admitted_methods` answers `!marginals` at no target, since a methods
    source of that one entry binds nowhere (specification 0.6 §5.1)."""
    _refuse(
        stage,
        target,
        f"!{tag} adds the lines of a marginal block to the builder, and the entry names no "
        "block file; write `block: <block file>` in the entry, the file that holds the "
        "marginal block (specification 0.6 §5.1)",
    )


def _marginal_block_place(stage, target, place, blocks, tag):
    """The place of `!marginals` with a block file, the Evaluation of a
    backward value builder, a builder whose outputs are values
    (specification 0.6 §5.1): the block's lines stand before it, and it
    writes the marginal values beside the values. Any other place, the
    policy builder and a forward builder among them, is refused with the
    reason."""
    block = blocks.get(place.block) if place.kind == "builder" else None
    outputs = header_of(block).outputs if block is not None else ()
    if not any(sort.role == VALUE for sort in outputs):
        _refuse(
            stage,
            target,
            f"!{tag} adds a marginal block's lines to a backward value builder, a builder "
            f"whose outputs are values, and stands at its Evaluation; {place.block!r} writes "
            "no value; write the value builder's block id as the target, such as "
            "`on: cntn_to_dcsn`",
        )
    return _closing_evaluation(stage, target, place.block, place.block)


def _backward_decision_builder_place(stage, target, place, blocks, tag):
    """The place of a handler for the whole backward decision builder, the
    builder from the continuation perch to the decision perch that writes the
    decision-perch values (`cntn_to_dcsn`): the handler realizes the
    maximization there and needs no policy builder, so any other builder, the
    policy block among them, is refused."""
    builders = backward_builders_to_decision(stage)
    if any(box.name == place.block for box in builders):
        return place
    _refuse(
        stage,
        target,
        f"!{tag} is a handler for the whole backward decision builder, the builder from the "
        "continuation perch to the decision perch that writes the decision-perch values, "
        "which it realizes with its maximization and without a policy builder; "
        f"{place.block!r} is not that builder; {_backward_decision_builders(builders)}",
    )


def _backward_decision_builders(builders):
    """The words that name the backward decision builders of a stage and
    what to write."""
    if len(builders) == 1:
        return f"write `on: {builders[0].name}`"
    if not builders:
        return "the stage has no such builder"
    return f"the stage has {len(builders)}: {', '.join(box.name for box in builders)}"


def _write_instead(stage, rule):
    """What a refusal of a target kind a method does not admit tells the
    author to write: a target of an admitted kind, and where the method's
    placement rule narrows the kinds, the place itself, the backward decision
    builder of a handler for it and the two places of `!egm`."""
    if rule._place is _backward_decision_builder_place:
        return (
            f"!{rule._tag} stands on the backward decision builder alone, the builder from the "
            "continuation perch to the decision perch that writes the decision-perch values; "
            f"{_backward_decision_builders(backward_builders_to_decision(stage))}"
        )
    if rule._place is _egm_place:
        return (
            f"!{rule._tag} is written on the policy builder by its block id, `on: policy`, "
            "with `block:` naming a method block, or with no block where the policy block "
            "writes the grid line, or on a maximization that carries its first-order "
            "condition as a property; write an on: target of one of these kinds"
        )
    if rule._place is _representation_place:
        return (
            "a representation is attached to the Evaluation of a builder, "
            "`<block-id>.evaluate`, `<block-id>.evaluate.value` or "
            "`<block-id>.evaluate.marginal`; write an on: target of one of these kinds"
        )
    return "write an on: target of one of these kinds"


def _representation_place(stage, target, place, blocks, tag):
    """The Evaluation that stores an evaluated field, or a named definition.

    A declared function is stored at its definition, and an authored
    `evaluate` occurrence is its own place. The Evaluation of a builder named
    by its written address, a `!node` line and a value line name the
    Evaluation that closes the builder or the node. A derivative line is
    refused naming `<block-id>.evaluate.marginal`, where the derivative it
    states is represented, and is not moved to the Evaluation (AMD-MB-002
    §4); a representation named on a builder is refused in `_resolved_entry`
    before this rule is reached.
    """

    if place.kind == "definition":
        definition = stage.definitions[place.address]
        if definition.kind not in ("function", "function_alias"):
            _refuse(
                stage,
                target,
                f"a representation method does not admit a definition of kind {definition.kind}; "
                "name a declared function or an evaluated field instead",
            )
        return _same_place(stage, target, place, blocks, tag)
    if place.kind == "operator" and place.head == "evaluate" and place.evaluates:
        return _closing_evaluation(stage, target, place.block, place.block, place.evaluates)
    if place.kind == "operator" and place.head == "evaluate":
        return _same_place(stage, target, place, blocks, tag)
    if place.kind == "statement" and place.address in derivative_lines(stage, blocks[place.block]):
        written = f"{place.block}.evaluate.marginal"
        _refuse(
            stage,
            target,
            f"!{tag} is a representation, and {place.address} is a derivative line, which "
            f"states a derivative of the value the builder writes; write `on: {written}`, the "
            f"Evaluation of the builder {place.block!r}, at which the stated derivative is "
            "represented",
            rule=REPRESENTATION_ON_DERIVATIVE_LINE,
        )
    address = place.address if place.kind == "node" else place.block
    return _closing_evaluation(stage, target, place.block, address)


def _closing_evaluation(stage, target, block, address, evaluates=None):
    """The place of the Evaluation that closes `address`, the builder
    `block` itself or a `!node` line of it, read from the builder's closed
    rows; refused where the builder holds no such Evaluation, or two."""
    identity = Identity("Evaluation", address=address)
    evaluations = tuple(
        row for row in builder_rows_of(stage, block).closed if row.identity == identity
    )
    if len(evaluations) != 1:
        described = ", ".join(str(row.identity) for row in evaluations) or "none"
        _refuse(
            stage,
            target,
            f"names an evaluated field whose closing Evaluation is not unique; "
            f"the matching Evaluations are {described}",
        )
    (evaluation,) = evaluations
    place = _evaluation_place(block, evaluation.identity.address, evaluates)
    # the box is the row's own identity, the object a binding is keyed by
    return replace(place, box=evaluation.identity)


def _same_place(stage, target, place, blocks, tag):
    return place


_GRID_OPTIONS = {
    "orders": MethodOption("positive integers by coordinate"),
    "bounds": MethodOption(
        "ordered pairs by coordinate", conditions=("ordered", "inside declared coordinate set")
    ),
}


# the kinds of grid a method names by the tag on the value of its setting
# `grid`, each with the fields it admits beside `grid` as settings of the
# entry (AMD-MB-003 §2): `!Cartesian`, a product of one grid per coordinate,
# its order and its bounds in each coordinate and, where written, the spacing
# of its points or the points themselves
GRID_KINDS = MappingProxyType(
    {
        "Cartesian": MappingProxyType(
            {
                "orders": MethodOption("positive integers by coordinate", required=True),
                "bounds": MethodOption(
                    "ordered pairs by coordinate",
                    required=True,
                    conditions=("ordered", "inside declared coordinate set"),
                ),
                "spacing": MethodOption("spacing names by coordinate"),
                "nodes": MethodOption(
                    "increasing reals by coordinate",
                    conditions=("increasing", "inside declared coordinate set"),
                ),
            }
        ),
    }
)

# the fields of every kind of grid, in the order the table writes them, by
# which the fields written without the setting `grid` are found
GRID_FIELDS = tuple(dict.fromkeys(field for fields in GRID_KINDS.values() for field in fields))

# the setting `grid` of a representation, the kind of the grid on which the
# represented function is stored, and of `!egm`, the kind of its exogenous
# grid of savings, whose coordinates are the continuation states
_REPRESENTATION_GRID = MethodOption("grid kind", required=True)
_EXOGENOUS_GRID = MethodOption("grid kind on the continuation states", required=True)


# the places a representation is attached to: a `!node` line, a value line, a
# declared function, and the operator `evaluate`, an authored occurrence or the
# Evaluation of a builder by its written address; not a builder (AMD-MB-002)
_REPRESENTATION_ADMITS = (
    "node",
    "statement",
    "definition",
    ("operator", "evaluate"),
)


# Operator entries include the retained head, never a parsed target spelling.
# Each call names its method once and carries both public parts plus its
# private placement machinery in the same authoritative row.
METHOD_TYPES = dict(
    (
        _method_type(
            "egm",
            ("builder", ("operator", "argmax")),
            options={"grid": _EXOGENOUS_GRID},
            place=_egm_place,
            block=True,
            condition="egm-eligibility",
        ),
        # `!marginals` takes a marginal block and binds its derivative lines
        # at a value builder's Evaluation, beside the value's representation
        # (AMD-MB-001 §5.2, D4)
        _method_type(
            "marginals",
            ("builder",),
            place=_marginals_place,
            block=True,
            condition="marginal-reading",
            kind="marginal block",
        ),
        _method_type(
            "vfi",
            ("builder",),
            # `n_c`, the number of points of the finite feasible set the
            # search uses, named as the applications' settings name it
            # (`applications/cons-port/declaration/settings/cons_vfi.yml`)
            options={
                **_GRID_OPTIONS,
                "tol": MethodOption("positive real"),
                "n_c": MethodOption("positive integer"),
            },
            place=_backward_decision_builder_place,
        ),
        # time iteration solves the first-order condition a method block
        # writes, whose lines read the continuation value's derivative
        # (resolution SA-12 of 22 October 2026; AMD-MB-001 §4.2)
        _method_type(
            "time-iteration",
            ("builder", "node", ("operator", "solve")),
            place=_same_place,
            block=True,
        ),
        # a representation names its basis as the method and its grid by
        # the setting `grid` (AMD-MB-003); the derivatives it evaluates, by
        # order, are information for the stage that reads them and checked
        # by nothing (AMD-MB-001 §5.2, D6)
        _method_type(
            "Linear",
            _REPRESENTATION_ADMITS,
            options={"grid": _REPRESENTATION_GRID},
            place=_representation_place,
            derivatives=(1,),
            evaluates=(
                "the first derivative, piecewise constant between its nodes and so a step "
                "function, which an inverse Euler step that reads it turns into a step "
                "candidate; the second derivative is zero and is not offered"
            ),
        ),
        _method_type(
            "pchip",
            _REPRESENTATION_ADMITS,
            options={"grid": _REPRESENTATION_GRID},
            place=_representation_place,
            derivatives=(1, 2),
            evaluates="the first and second derivatives its basis admits",
        ),
        _method_type(
            "gauss-hermite",
            (("operator", "E"),),
            options={"n_nodes": MethodOption("positive integers by shock", required=True)},
            place=_same_place,
        ),
        _method_type("quadrature", (("operator", "E"),), place=_same_place),
        _method_type("exact", (("operator", "E"),), place=_same_place),
        _method_type("exact-markov", (("operator", "E"),), place=_same_place),
        _method_type("markov", (("operator", "E"),), place=_same_place),
        _method_type("markov-expectation", (("operator", "E"),), place=_same_place),
        _method_type("sum", (("operator", "E"),), place=_same_place),
        _method_type(
            "tauchen",
            (("operator", "E"),),
            options={
                "n_states": MethodOption("positive integer"),
                "n_income_states": MethodOption("positive integer"),
                "n_std": MethodOption("positive real"),
                "min_prob": MethodOption("positive real"),
            },
            place=_same_place,
        ),
        # the methods of a forward builder represent its measure
        # (decision SD-15)
        _method_type("deterministic", ("builder",), place=_same_place, kind="representation"),
        _method_type(
            "histogram",
            ("builder",),
            options=_GRID_OPTIONS,
            place=_same_place,
            kind="representation",
        ),
        _method_type("identity", ("builder",), place=_same_place, kind="representation"),
        _method_type(
            "monte-carlo",
            ("builder", ("operator", "E")),
            options={
                "n_paths": MethodOption("positive integer", required=True),
                "seed": MethodOption("seed"),
            },
            place=_same_place,
        ),
        _method_type("max", ("builder", ("operator", "argmax")), place=_same_place),
        _method_type("discrete-choice", ("builder", ("operator", "argmax")), place=_same_place),
        _method_type(
            "golden_section",
            (("operator", "argmax"),),
            options={"n_sections": MethodOption("positive integer")},
            place=_same_place,
        ),
        _method_type("scipy-bounded", (("operator", "argmax"),), place=_same_place),
        _method_type(
            "root-find",
            (("operator", "solve"), ("operator", "argmax")),
            options=_GRID_OPTIONS,
            place=_same_place,
        ),
        _method_type("newton", (("operator", "solve"),), place=_same_place),
        _method_type(
            "analytic-inverse", ("node", "definition", ("operator", "solve")), place=_same_place
        ),
        _method_type("FUES", ("node", ("operator", "upper_env")), place=_same_place),
    )
)


class _MethodTypes(Mapping):
    """The one method table, `METHOD_TYPES`, as a read-only mapping."""

    def __getitem__(self, tag):
        if not isinstance(tag, str) or not tag.startswith("!"):
            raise KeyError(tag)
        return METHOD_TYPES[tag[1:]]

    def __iter__(self):
        return (f"!{name}" for name in METHOD_TYPES)

    def __len__(self):
        return len(METHOD_TYPES)

    def __str__(self):
        return "\n".join(self)

    __repr__ = __str__


method_types = _MethodTypes()


def solution_words():
    """The method words whose row is of the kind `solution`, in the spelling
    of a stage file, with an underscore for the hyphen of the tag: the words
    under which the operative level of a stage file and its additions
    (`method_blocks.operative_level`) reads the rows an addition brings in
    place of the block's declared lines (specification 0.7 §4 rule 5, D8)."""
    return frozenset(
        tag.replace("-", "_") for tag, row in METHOD_TYPES.items() if row.kind == "solution"
    )
