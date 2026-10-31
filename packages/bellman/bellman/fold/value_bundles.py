"""The primitive grain of a builder's rows and the value bundles the rows act
on (AMD-SG-011).

A value bundle is the tuple of value wires on one base that one box writes
and one box reads (§1). It is derived from the rows and stored nowhere; every
wire keeps its own identity, role and domain. A pullback, an evaluation at a
policy and an expectation act on the whole bundle in one box whenever every
component shares the base coordinates and the kernel (§2), which
`bundled_pullbacks` and the finish of the backward fold emit directly. At the
primitive grain, the parallel boxes that separate authored lines produce are
merged by `merged_in_parallel` under the same condition (§3), which also pairs
the pointwise segment before a merged expectation into one G, the identity on
a component it leaves alone.

A merge never crosses a sub-builder. The holder of a row is the builder or the
authored `!node` that holds it: the marker is the author's instrument for
keeping two computations apart, a method attaches to a node, and a navigation
key reaches a box through one bubble, so a box spanning two bubbles would have
no address. `holder_of_each_row` reads each row's holder before the primitive
grain clears the mark, and `merged_in_parallel` carries the map through.
"""

from __future__ import annotations

import dataclasses
from typing import NamedTuple

from bellman.fold.wire_terms import substitute_wires, wire_symbol, wires_read
from bellman.native.identity import Identity

# --- the primitive grain ---


def primitive_grain_rows(rows):
    """The rows of the primitive grain (AMD-SG-008 §5, AMD-SG-011 §3): the
    sub-builders opened, their evaluations retained, and each aggregation whose
    one output only one aggregation reads merged into that reader by
    composition of their terms. No sequential merge crosses an expectation or
    joins two aggregation paths; the policy evaluation and the outside
    aggregation remain. An aggregation with unknowns is not merged, since
    its rule states a relation in its output and its map, the explicit side
    of that relation, does not define the output. Then the parallel boxes of
    one owner, one kernel and one history become one box on the value bundle
    (`merged_in_parallel`). The owner of each row is read here, while the
    rows still carry the mark the opening clears."""
    owners = holder_of_each_row(rows)
    if not any(row.node is not None for row in rows):
        return merged_in_parallel(rows, owners)
    opened = [dataclasses.replace(row, node=None) for row in rows]
    merged = True
    while merged:
        merged = False
        for first in opened:
            if first.kind != "Aggregation" or len(first.outputs) != 1 or first.unknowns:
                continue
            wire = first.outputs[0]
            readers = [row for row in opened if wire in row.inputs]
            if len(readers) != 1 or readers[0].kind != "Aggregation":
                continue
            second = readers[0]
            producers = [
                row
                for row in opened
                if row.kind == "Aggregation" and set(row.outputs) & set(second.inputs)
            ]
            if len(producers) != 1:
                continue
            combined = dataclasses.replace(
                second,
                statements=tuple(dict.fromkeys(first.statements + second.statements)),
                inputs=tuple(
                    dict.fromkeys(
                        i for w in second.inputs for i in (first.inputs if w == wire else (w,))
                    )
                ),
                maps=tuple(substitute_wires(m, {wire: first.maps[0]}) for m in second.maps),
                parameters=tuple(dict.fromkeys(first.parameters + second.parameters)),
                equations=tuple(dict.fromkeys(first.equations + second.equations)),
                conditions=tuple(dict.fromkeys(first.conditions + second.conditions)),
            )
            opened[opened.index(second)] = combined
            opened.remove(first)
            merged = True
            break
    return merged_in_parallel(opened, owners)


def holder_of_each_row(rows):
    """The builder or authored `!node` that holds each row, by row identity.
    The primitive grain clears `node` when it opens the bubbles, so the map is
    read from the rows that still carry the mark and passed to the merge."""
    return {row.identity: row.node or row.builder for row in rows}


def bundled_pullbacks(rows):
    """The rows with the pullbacks of one slice that apply one law of motion on
    one base merged into one box on the value bundle (AMD-SG-011 §2), placed
    where the first of them stands and named for the slice without a field
    segment, `dcsn_to_arvl:Pullback`. A slice that pulls two bundles back along
    different laws or on different bases keeps two boxes, and each then keeps
    the field it acts on, `policy:Pullback:V` beside `policy:Pullback:dV`,
    since a counter hides the field a reader is looking for. The pullbacks
    along the sections of a branching law are one box per section, named by
    its label, `cntn_to_dcsn:Pullback:keep`."""
    groups, order = {}, []
    for row in rows:
        if row.kind != "Pullback":
            continue
        key = _PullbackKey(
            holder=row.node or row.builder,
            law=row.definition,
            arguments=row.arguments,
            section=row.section,
        )
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(row)
    if not groups:
        return list(rows)
    held = {}
    for key in order:
        held.setdefault(key.holder, []).append(key)
    names = {}
    for owner, keys in held.items():
        for key in keys:
            # the field where the box acts on one, a counter where two boxes of
            # one owner each act on several: a name never carries a list
            fields = [_field_segment(row, "Pullback") for row in groups[key]]
            # a box along a section is named by the section's label
            segment = key.section or (
                fields[0] if len(fields) == 1 and fields[0] else str(keys.index(key) + 1)
            )
            names[key] = Identity(
                "Pullback", address=owner, field=segment if key.section or len(keys) > 1 else None
            )
    merged = {id(group[0]): _combined(group, names[key]) for key, group in groups.items()}
    dropped = {id(row) for group in groups.values() for row in group[1:]}
    return [merged.get(id(row), row) for row in rows if id(row) not in dropped]


class _PullbackKey(NamedTuple):
    """What the pullbacks of one box share: the builder or `!node` that holds
    them, the law of motion they compose with, the coordinates their functions
    are written in, and the section of a branching law they compose with, None
    for a law without branches."""

    holder: str
    law: object
    arguments: tuple
    section: str | None


def _field_segment(row, kind):
    """The field a kernel box's identity carries after its kind, `V` in
    `dcsn_to_arvl:Pullback:V`, or the empty string where it carries none."""
    return row.identity.field if row.identity.kind == kind and row.identity.field else ""


def pullbacks_after_their_writers(rows):
    """The rows in an order in which every pullback stands after the last box
    whose output it reads (AMD-SG-017 §5.10). A pullback that reads no box
    output stands where the merge places it, and a list in which no pullback
    reads a box output is returned unchanged, so the stored order of a builder
    the rule does not reach is untouched. Where the merge of AMD-SG-011 §2
    joins the pullback of a header value input with the pullback of a function
    a policy line defines, the merged box reads that line's output, and the
    boxes that read the merged box follow it."""
    rows = list(rows)
    written = {wire for row in rows for wire in row.outputs}
    if not any(
        row.kind == "Pullback" and any(wire in written for wire in row.inputs) for row in rows
    ):
        return rows
    return in_dependency_order(rows) or rows


def in_dependency_order(pending):
    """The rows in an order in which every row stands after the rows that write
    its inputs, taking at each step the first row of `pending` whose inputs are
    all written. Rows already in such an order are returned unchanged, so a
    merge that needs no move reorders nothing; None where no such order exists.
    """
    written = {output: row for row in pending for output in row.outputs}
    emitted, ordered, waiting = set(), [], list(pending)
    while waiting:
        ready = next(
            (
                row
                for row in waiting
                if all(
                    wire not in written or written[wire] is row or id(written[wire]) in emitted
                    for wire in row.inputs
                )
            ),
            None,
        )
        if ready is None:
            return None  # no reading order: the merge is refused
        waiting.remove(ready)
        emitted.add(id(ready))
        ordered.append(ready)
    return ordered


# --- the merges of parallel boxes on one value bundle (AMD-SG-011 §3) ---

_MERGE_KEY = {
    # the kernel and the base each kind compares: a pullback its law of motion
    # and the section it composes with, so that two sections are never joined,
    # an expectation its distribution, its integrated and conditioning shocks,
    # an evaluation the policy functions it reads
    "Pullback": lambda row: (row.definition, row.arguments, row.policy, row.section),
    "Expectation": lambda row: (
        row.references,
        row.integrated,
        row.given,
        row.arguments,
        row.policy,
    ),
    "Evaluation": lambda row: (row.policy, row.arguments),
    "PolicyInsertion": lambda row: (row.policy, row.arguments),
}


def merged_in_parallel(rows, owners=None):
    """The rows of the primitive grain with the parallel boxes of one owner,
    one kernel and one history merged into one box on the value bundle
    (AMD-SG-011 §3). The owner is the builder or the authored `!node`, and no
    merge crosses a sub-builder. Within one owner, by kind: parallel pullbacks,
    evaluations and expectations merge when their kernels and bases are equal,
    an expectation also when it stands behind the same expectations, and in
    every case when the boxes that read the results read each result into a
    different output; then the pointwise segment before each merged expectation
    is made one G on the bundle; then the parallel aggregations on one base
    whose outputs one box reads are paired. A merged box is named for its
    owner, with a counter where that name is taken or the owner holds two
    merged boxes of one kind."""
    rows = list(rows)
    held = dict(owners or {})

    def owner_of(row):
        return held.get(row.identity) or row.node or row.builder

    changed = True
    while changed:
        rows, changed = _merged_boxes(rows, owner_of, held)
        if not changed:
            rows, changed = _merged_segments(rows, owner_of, held)
        if not changed:
            rows, changed = _merged_aggregations(rows, owner_of, held)
    return tuple(_named_merged_boxes(rows, held))


def _merged_boxes(rows, owner_of, held):
    """The rows with the first group of parallel pullbacks, evaluations or
    expectations of one owner, one kernel and one base, an expectation also
    behind the same expectations, merged into one box on the value bundle, and
    whether a group was merged; `held` records the merged box's owner. A row
    with unknowns, whose rule is a relation in its own output, is never
    merged, so that two identifications of one block stay two boxes."""
    for kind, key in _MERGE_KEY.items():
        groups = {}
        for row in rows:
            if row.kind != kind or row.unknowns:
                continue
            name = (owner_of(row), key(row))
            if kind == "Expectation":
                name += (_expectations_behind(rows, row),)
            groups.setdefault(name, []).append(row)
        for name, group in groups.items():
            if (
                len(group) < 2
                or not _parallel(rows, group)
                or not _distinct_components(rows, group)
            ):
                continue
            holder, *_ = name
            merged = _combined(group, Identity(kind, address=holder, mark="merged"))
            rebuilt = _replacing(rows, group, merged)
            if rebuilt is None:
                continue
            held[merged.identity] = holder
            return rebuilt, True
    return rows, False


def _merged_segments(rows, owner_of, held):
    """The rows with the pointwise segment before the first merged expectation
    that has one made one G on the bundle (`_paired_segment`), and whether one
    was; `held` records the G's owner."""
    for row in rows:
        if row.kind != "Expectation" or len(row.inputs) < 2:
            continue
        paired = _paired_segment(rows, row, owner_of(row), held)
        if paired is not None:
            held[Identity("Aggregation", address=owner_of(row), mark="merged")] = owner_of(row)
            return paired, True
    return rows, False


def _expectations_behind(rows, row):
    """The expectation boxes a row's inputs depend on through the rows,
    directly or through another box. AMD-SG-008 §4 defines a result's history
    as the shocks already integrated on the paths that produce it, with the
    occurrence that integrated each; no row stores it, so it is read off the
    graph here. Two parallel expectations integrate under the same
    conditioning when they integrate the same shocks and stand behind the
    same expectations."""
    return frozenset(
        source.identity
        for source in _rows_behind(_producers(rows), row)
        if source.kind == "Expectation"
    )


def _rows_behind(produced, row):
    """The rows a row's inputs depend on, directly or through another row,
    each once, in the order a depth-first walk from its inputs meets them;
    `produced` maps each wire to the row that writes it."""
    seen, pending = set(), list(row.inputs)
    while pending:
        source = produced.get(pending.pop())
        if source is None or id(source) in seen:
            continue
        seen.add(id(source))
        yield source
        pending.extend(source.inputs)


def _producers(rows):
    """Each wire the rows write, mapped to the row that writes it."""
    return {output: row for row in rows for output in row.outputs}


def _parallel(rows, group):
    """Whether no member of a group is reached from another
    through the rows."""
    produced = _producers(rows)
    members = {id(row) for row in group}
    return not any(
        id(source) in members and source is not row
        for row in group
        for source in _rows_behind(produced, row)
    )


def _distinct_components(rows, group):
    """Whether the results of a group are different value objects, which is
    what a value bundle is a tuple of (AMD-SG-011 §1). The boxes that read them
    decide it: each result must be read into a different output, as the outside
    aggregation of `cons_savings_iid.bl` reads the value result into V[<] and
    the marginal result into dV[<], and as the selection and the solution of
    `port.bl`'s policy read the objective's integral and the residual's. Two
    results one kernel reads together are two arguments of that kernel, as the
    two occurrences of the two-node stage of AMD-SG-008 §2 are two terms of one
    sum, and the boxes that produce them stay two."""
    written = {output for row in group for output in row.outputs}
    members = {id(row) for row in group}
    readers = [row for row in rows if id(row) not in members and written & set(row.inputs)]
    if not readers:
        return True  # the graph's own outputs, one per component
    seen = set()
    for reader in readers:
        if not reader.maps or len(reader.maps) != len(reader.outputs):
            # no kernel per output is printed: the reader takes one component
            # per output positionally, as a pullback, an expectation, an
            # evaluation, a selection or a solution does
            if reader.kind in _MERGE_KEY or len(written & set(reader.inputs)) == 1:
                continue
            return False
        for term in reader.maps:
            read = written & set(wires_read(term))
            if len(read) > 1 or read & seen:
                return False
            seen |= read
    return True


def _combined(group, identity):
    """One row for a group of rows that apply one kernel on one base: the
    components' wires in order, each keeping its identity, and the authored
    statements, references, conditions and parameters of every member, in the
    order the members stand."""
    return dataclasses.replace(
        group[0],
        identity=identity,
        inputs=_joined_field(group, "inputs"),
        outputs=_joined_field(group, "outputs"),
        statements=_joined_field(group, "statements"),
        references=_joined_field(group, "references"),
        parameters=_joined_field(group, "parameters"),
        conditions=_joined_field(group, "conditions"),
        equations=tuple(e for row in group for e in row.equations),
        maps=tuple(m for row in group for m in row.maps),
    )


def _joined_field(rows, field):
    """The items of one field of several rows, each once, in the order the
    rows and their items stand."""
    return tuple(dict.fromkeys(item for row in rows for item in getattr(row, field)))


def _replacing(rows, group, merged):
    """The rows with the members of a group replaced by one box on the value
    bundle, read in an order in which every box stands after the boxes that
    write its inputs. The merged box takes the place of the first member, and a
    box that read a later member's result and stood before that place moves
    after it: on `port.bl`'s policy the selection, which read the objective's
    integral, follows the merged expectation. None where no order exists."""
    members = {id(row) for row in group}
    first = min((place for place, row in enumerate(rows) if id(row) in members), default=0)
    ranked = [(place, row) for place, row in enumerate(rows) if id(row) not in members]
    ranked.append((first, merged))
    ranked.sort(key=lambda pair: pair[0])
    return in_dependency_order([row for _, row in ranked])


def _paired_segment(rows, expectation, owner, held):
    """The rows with the pointwise segment before a merged expectation made one
    G on the bundle (AMD-SG-011 §3): one box whose outputs are the integrands,
    each keeping its own map and argument list, and the identity on a component
    whose integrand is the bare result of an earlier box. None where one box
    already produces every integrand, where no component has a pointwise box of
    its own, where the components do not share their base, or where one of the
    aggregations sits in a sub-builder other than the expectation's owner."""
    produced = _producers(rows)
    sources, base = [], None
    for wire in expectation.inputs:
        source = produced.get(wire)
        pointwise = (
            source
            if source is not None and source.kind == "Aggregation" and len(source.outputs) == 1
            else None
        )
        if pointwise is not None and held.get(pointwise.identity, pointwise.builder) != owner:
            return None
        arguments = getattr(source, "arguments", None)
        if arguments is None or (base is not None and arguments != base):
            return None
        base = arguments
        sources.append((wire, pointwise))
    members = [pointwise for _, pointwise in sources if pointwise is not None]
    if (
        not members
        or len({id(member) for member in members}) == 1
        and len(members) == len(sources)
    ):
        return None
    inputs, outputs, maps = [], [], []
    for (wire, pointwise), result in zip(sources, expectation.outputs):
        if pointwise is None:
            # the identity on this component: the merged G reads the wire and
            # writes it again, under the name the fold gives the inside
            # aggregation of the occurrence that reads it
            inputs.append(wire)
            outputs.append(_segment_result(result))
            maps.append(wire_symbol(wire))
        else:
            inputs.extend(pointwise.inputs)
            outputs.extend(pointwise.outputs)
            maps.extend(pointwise.maps)

    segment = dataclasses.replace(
        members[0],
        identity=Identity("Aggregation", address=owner, mark="merged"),
        inputs=tuple(dict.fromkeys(inputs)),
        outputs=tuple(outputs),
        maps=tuple(maps),
        arguments=base,
        node=None,
        statements=tuple(
            dict.fromkeys(tuple(expectation.statements) + _joined_field(members, "statements"))
        ),
        equations=tuple(e for member in members for e in member.equations),
        conditions=_joined_field(members, "conditions"),
        parameters=_joined_field(members, "parameters"),
        references=_joined_field(members, "references"),
    )
    dropped = {id(member) for member in members}
    rebuilt = [row for row in rows if id(row) not in dropped]
    position = next(index for index, row in enumerate(rebuilt) if row is expectation)
    rebuilt[position] = dataclasses.replace(
        expectation, inputs=tuple(outputs), maps=tuple(wire_symbol(output) for output in outputs)
    )
    rebuilt.insert(position, segment)
    return in_dependency_order(rebuilt)


def _segment_result(result):
    """The wire a merged G writes for the component it leaves alone, read from
    the occurrence's own result wire: the wire the fold gives the inside
    aggregation of that occurrence, its kind alone differing."""
    return dataclasses.replace(result, kind="Aggregation")


def _merged_aggregations(rows, owner_of, held):
    """The parallel pointwise aggregations of one owner on one base whose
    outputs one box reads, made one G by pairing their component maps
    (AMD-SG-011 §3, under the condition of §1 that a bundle is read by one
    box): two aggregations read by different boxes are two computations, not
    the components of one bundle."""
    for index, first in enumerate(rows):
        if first.kind != "Aggregation":
            continue
        owner = owner_of(first)
        group = [first] + [
            row
            for row in rows[index + 1 :]
            if row.kind == "Aggregation"
            and row.arguments == first.arguments
            and owner_of(row) == owner
        ]
        if len(group) < 2:
            continue
        if not _one_reader(rows, group) or not _parallel(rows, group):
            continue
        if not _distinct_components(rows, group):
            continue
        merged = _combined(group, Identity("Aggregation", address=owner, mark="merged"))
        rebuilt = _replacing(rows, group, merged)
        if rebuilt is None:
            continue
        held[merged.identity] = owner
        return rebuilt, True
    return rows, False


def _one_reader(rows, group):
    """Whether one box reads every result of a group, or none does and the
    results are the graph's own outputs. It is the condition on the pairing of
    parallel pointwise aggregations (AMD-SG-011 §3): two aggregations read by
    two boxes are two computations that happen to stand side by side, as the
    documentary objective and the Euler residual of `cons_childless.bl` are,
    and pairing them would put an objective and a residual in one kernel."""
    written = {output for row in group for output in row.outputs}
    members = {id(row) for row in group}
    return (
        len({id(row) for row in rows if id(row) not in members and written & set(row.inputs)}) <= 1
    )


def _named_merged_boxes(rows, held):
    """The names of the merged boxes: the owner and the kind, with a counter
    where that name is already taken at this grain or where the owner holds two
    merged boxes of one kind, in graph order (AMD-SG-011 §2). The merged
    pointwise segment of a value block therefore carries one, since the block's
    outside aggregation holds the plain name."""
    taken = {row.identity for row in rows if not row.identity.is_merged}
    found = {}
    for row in rows:
        if row.identity.is_merged:
            found.setdefault((held.get(row.identity, row.builder), row.kind), []).append(id(row))
    names = {}
    for (owner, kind), members in found.items():
        plain = Identity(kind, address=owner)
        if len(members) == 1 and plain not in taken:
            names[members[0]] = plain
            continue
        counter = 0
        for identity in members:
            counter += 1
            while Identity(kind, address=owner, occurrence=counter) in taken:
                counter += 1
            names[identity] = Identity(kind, address=owner, occurrence=counter)
    return [
        dataclasses.replace(row, identity=names[id(row)]) if id(row) in names else row
        for row in rows
    ]
