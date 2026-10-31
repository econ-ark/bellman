"""The drawings over a trellis dictionary: `diagram_period` draws one period,
its stages as boxes joined by their joins; `diagram_trellis` draws the periods
of an elaborated trellis with their inter-period connectors,
`inter_connectors[h]` joining `periods[h + 1]` to `periods[h]`. Each drawing
is built for the call and stored nowhere, from one selection of the
trellis's connections (`connections.trellis_selection`), which the joins
and the orders it draws are projected from; a trellis whose authored
connector resolves to no pair is drawn as the draft it is, the diagnostic
standing in its connection report. A stage of a period is drawn as the
node its key names, and in a drawing of several periods as the node
`periods[h] <key>`, the address of its period and its key (`_node_in`), so
that no node name is written in the spelling of an identity.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple

from bellman.display.drawing import Drawing, dot_attributes, dot_head, dot_quoted
from bellman.factory.connections import trellis_selection
from bellman.factory.joins import forward_order, inter_period_joins, period_joins
from bellman.refusals import FactoryError

__all__ = ["chosen_periods", "diagram_period", "diagram_trellis", "join_label", "period_age"]


def join_label(join):
    """The label of a join, `{"from": (key, field), "to": (key, arrival)}`,
    as the drawings write it: the field it carries, `a`, or `m_next → m`
    where a connector renames it. The interactive view labels a join with
    the same text (`model_explorer`)."""
    (_, field), (_, arrival) = join["from"], join["to"]
    return field if field == arrival else f"{field} → {arrival}"


def period_age(trellis, h):
    """The age of `periods[h]`, `last_age − h`, where the calibration of the
    trellis's `registry` holds an integer `last_age`; None otherwise. The
    drawing of a trellis labels the period's cluster with it, and the
    interactive view the period's layer (`model_explorer`)."""
    last_age = _age_label(trellis)
    return last_age - h if isinstance(last_age, int) else None


def diagram_trellis(trellis, periods=None, selection=None):
    """A `Drawing` of the periods of an elaborated trellis, every one or those
    whose indices `periods` lists, in the format of a graph's `diagram()`.
    Each period is drawn as `diagram_period` draws it, its stages as the
    nodes `periods[h] <key>`, inside a cluster labeled
    `periods[h]` with `h` and, where the trellis's `registry` holds
    `last_age`, the age `last_age − h`; the terminal period `h = 0` stands at
    the right and the earlier periods to its left, so that economic time runs
    left to right and the backward computation right to left, the two
    directions written in the title; every inter-period mapping
    `inter_connectors[h]` whose two periods are drawn is drawn as wires from
    the continuation fields of `periods[h + 1]` to the arrival fields of
    `periods[h]`, each wire labeled with the mapping's index and its field
    pair; a period with no mapping to its
    neighbor is drawn with no wire, an invisible edge alone keeping the two
    periods in their order. The drawing's `labels` list the boxes as the
    trellis lists its periods, the terminal period first. An index the
    trellis does not hold is refused under `trellis-file-shape`. The joins
    drawn are those of `selection`, the trellis's selection where the
    caller holds one, else selected here once for the drawing."""
    held = trellis["periods"]
    drawn = chosen_periods(held, periods)
    if selection is None:
        selection = trellis_selection(trellis)
    wires = _inter_period_wires(trellis, drawn, selection)
    read = {(h + 1, join["from"]) for h, joins in wires.items() for join in joins}
    title = (
        "economic time runs left to right, the backward computation right to left;\n"
        "the terminal period periods[0] stands at the right"
    )
    lines, statements = dot_head(title, rankdir="LR"), {}
    for h in drawn:
        statements[h] = _period_drawing(
            held[h],
            f"periods[{h}]",
            _node_in(h),
            wired={position for at, position in read if at == h},
            selection=selection,
        )
        lines += _period_cluster(h, statements[h], period_age(trellis, h))
    labels = [f"periods[{h}] {name}" for h in sorted(statements) for name in statements[h].labels]
    lines += _inter_period_edges(wires) + _order_edges(drawn, wires, statements) + ["}"]
    return Drawing("\n".join(lines) + "\n", labels)


def chosen_periods(held, periods):
    """The indices of the periods to draw, every one or those `periods`
    lists, from the last to the first; an index the trellis does not hold is
    refused under `trellis-file-shape`."""
    chosen = list(range(len(held))) if periods is None else list(periods)
    for h in chosen:
        refusal = _no_period(
            held,
            h,
            repr(periods),
            f"indices between 0 and {len(held) - 1}, or no `periods` for every period",
        )
        if refusal is not None:
            raise refusal
    return sorted(set(chosen), reverse=True)


def _age_label(trellis):
    """The value `last_age` of the calibration of the trellis's `registry`,
    or None where it holds none."""
    registry = trellis.get("registry") if isinstance(trellis.get("registry"), Mapping) else {}
    calibration = (
        registry.get("calibration") if isinstance(registry.get("calibration"), Mapping) else {}
    )
    return calibration.get("last_age")


def _inter_period_wires(trellis, drawn, selection):
    """The joins of each inter-period mapping between two drawn neighbors,
    keyed by the index of the mapping, read from `selection`."""
    held = trellis["periods"]
    return {
        h: inter_period_joins(
            trellis["inter_connectors"][h],
            held[h + 1],
            held[h],
            f"inter_connectors[{h}]",
            later_address=f"periods[{h + 1}]",
            selection=selection,
        )
        for h in drawn
        if h + 1 in drawn
    }


def _period_cluster(h, statements, age):
    """The DOT lines of the cluster of period `h`, labeled with its index
    and, where `age` is not None, its age (`period_age`), holding the
    statements of the period."""
    label = f"periods[{h}]: h = {h}" + (f", age {age}" if age is not None else "")
    return [
        f"  subgraph {dot_quoted(f'cluster_{h}')} {{",
        f'    graph [label={dot_quoted(label)}, labelloc="t", labeljust="l"];',
        *("  " + statement for statement in statements.lines),
        "  }",
    ]


def _node_in(h):
    """The name of the node of a stage of `periods[h]` in a drawing of
    several periods, from the stage's key: `periods[h] <key>`, the address of
    the period, a space and the key, which no identity is spelled as."""
    return lambda key: f"periods[{h}] {key}"


def _inter_period_edges(wires):
    """One DOT edge per inter-period wire, from the continuation field of
    the later period to the arrival field of the earlier one, labeled with
    the mapping's index and its field pair."""
    lines = []
    for h, joins in wires.items():
        for join in joins:
            (source, _), (target, _) = join["from"], join["to"]
            pair = join_label(join)
            lines.append(
                f"  {dot_quoted(_node_in(h + 1)(source))} -> {dot_quoted(_node_in(h)(target))}"
                f"{dot_attributes({'label': f'inter_connectors[{h}]\n{pair}'})};"
            )
    return lines


def _order_edges(drawn, wires, statements):
    """The invisible DOT edges that keep two periods drawn side by side in
    their order where no wire joins them."""
    # two periods drawn side by side with no wire between them, neighbors with
    # an empty mapping or periods drawn apart, keep their order through
    # invisible edges from the rightmost nodes of the later period to the first
    # stage of the earlier one; Graphviz would otherwise stack them
    return [
        f'  {dot_quoted(sink)} -> {dot_quoted(statements[earlier].first)} [style="invis"];'
        for later, earlier in zip(drawn, drawn[1:])
        if not wires.get(earlier) or later != earlier + 1
        for sink in statements[later].sinks
    ]


def diagram_period(trellis, h, selection=None):
    """A `Drawing` of `trellis["periods"][h]`, in the format of a graph's
    `diagram()` (`drawing.dot_head`): one box per stage, labeled by its key,
    with its stage name in parentheses beneath where the two differ, standing
    in the forward order, left to right; one arrow per join, labeled by the
    field it carries, `field → arrival` where a connector renames it; one
    unlabeled arrow to a plain label per continuation field that no stage of
    the period takes. `h` counts the periods from the terminal period, 0; an
    index the trellis does not hold is refused under `trellis-file-shape`.
    The joins drawn are those of `selection`, the trellis's selection where
    the caller holds one, else selected here once for the drawing."""
    held = trellis["periods"]
    refusal = _no_period(held, h, repr(h), f"an index between 0 and {len(held) - 1}")
    if refusal is not None:
        raise refusal
    address = f"periods[{h}]"
    if selection is None:
        selection = trellis_selection(trellis)
    statements = _period_drawing(held[h], address, lambda name: name, selection=selection)
    return Drawing(
        "\n".join(dot_head(address, rankdir="LR") + statements.lines + ["}"]) + "\n",
        statements.labels,
    )


def _no_period(held, h, written, write):
    """The refusal of `h` where it is no index of the periods `held`, under
    `trellis-file-shape`, or None where it is one: an index is an integer
    from 0 to one less than the number of periods."""
    if isinstance(h, bool) or not isinstance(h, int) or not 0 <= h < len(held):
        return FactoryError(
            f"the trellis holds {len(held)} periods, and periods[{h!r}] is none of them",
            rule="trellis-file-shape",
            address="periods",
            written=written,
            write=write,
        )
    return None


def _period_drawing(period, address, node, wired=frozenset(), selection=None):
    """The `_PeriodDrawing` of one period: one box per stage, labeled by its
    key, with its stage name in parentheses beneath where the two differ,
    standing in the forward order, its node named by `node(key)`; one arrow per
    join, labeled by the field it carries, `field → arrival` where a connector
    renames it; one unlabeled arrow to a plain label per continuation field
    that no stage of the period takes and no inter-period wire in `wired`
    reads. The joins and the order are read from `selection`."""
    order = forward_order(period, address, selection=selection)
    found = period_joins(period, address, selection=selection)
    lines, labels, left = [], [], set()
    for key in order:
        name = period["stages"][key].name
        label = key if key == name else f"{key}\n({name})"
        lines.append(f"  {dot_quoted(node(key))}{dot_attributes({'label': label})};")
        labels.append(f"{key}: {name}")
    for join in found["joins"]:
        (source, _), (target, _) = join["from"], join["to"]
        lines.append(
            f"  {dot_quoted(node(source))} -> "
            f"{dot_quoted(node(target))}{dot_attributes({'label': join_label(join)})};"
        )
        left.add(source)
    sinks = []
    for number, (key, field) in enumerate(found["outputs"]):
        if (key, field) in wired:
            continue
        out = node(f"out{number}")
        lines.append(
            f"  {dot_quoted(out)}{dot_attributes({'shape': 'plaintext', 'label': field})};"
        )
        lines.append(f"  {dot_quoted(node(key))} -> {dot_quoted(out)};")
        left.add(key)
        sinks.append(out)
    return _PeriodDrawing(
        lines=lines,
        labels=labels,
        first=node(order[0]),
        sinks=[node(key) for key in order if key not in left] + sinks,
    )


class _PeriodDrawing(NamedTuple):
    """The DOT statements of one period, the labels of its boxes, the node of
    the first stage in the forward order and the nodes no arrow of the period
    leaves, the rightmost ones."""

    lines: list
    labels: list
    first: str
    sinks: list
