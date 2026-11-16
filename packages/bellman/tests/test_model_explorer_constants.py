"""Constants in the Model Explorer's views: the joins of a trellis carry the
constants that their routes pair, in the full view and in a restricted one,
and a table that a constant field holds has a view."""

import importlib.util

import pytest
from test_modular_fields import KEPT_BOUND, PENSION, period

from bellman.factory import model_explorer as me
from bellman.stage import elaborate_text
from bellman.trellis import elaborate_trellis

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("model_explorer") is None,
    reason="the viewer's package is not installed",
)

_CONSTANT = "consumption:function:cntn:L"


def _trellis(*texts, connectors):
    """A trellis of one consumption stage per period, the last period first."""
    return elaborate_trellis(
        {
            "periods": [period({"consumption": text}) for text in texts],
            "inter_connectors": list(connectors),
        }
    )


def _backward(trellis, **view):
    """The backward graph of a trellis view."""
    (graph,) = (g for g in me.to_model_explorer(trellis, **view).graphs if g.id == "backward")
    return graph


def _attributes(graph, occurrence, wire):
    """The attributes of each input port that reads `wire` in an occurrence."""
    port = f"{occurrence}/{wire}"
    return [
        {entry.key: entry.value for entry in item.attrs}
        for node in graph.nodes
        for item in node.inputsMetadata or ()
        if item.id == port
    ]


def test_a_join_carries_the_constant_that_its_route_pairs():
    """The later period's kept bound is supplied by the earlier period's
    arrival bound along the join, under the rule that paired the two names.
    It is a terminal condition of the last period alone."""
    graph = _backward(_trellis(KEPT_BOUND, KEPT_BOUND, connectors=[{"a": "k"}]))
    terminal = [node.id for node in graph.nodes if node.id.startswith("start:")]
    assert f"start:periods[0]/consumption/{_CONSTANT}" in terminal
    assert f"start:periods[1]/consumption/{_CONSTANT}" not in terminal
    (read,) = _attributes(graph, "periods[1]/consumption", _CONSTANT)
    assert read["join"] == "inter_connectors[0] a → k"
    assert read["paired by"] == "equal name"


def test_a_restricted_view_shows_a_paired_constant_as_coming_from_outside():
    """In the view of the middle period alone, the bound enters from the
    period before it in the recursion and leaves to the period after it. It
    is drawn as no terminal condition and as no result."""
    trellis = _trellis(
        KEPT_BOUND, KEPT_BOUND, KEPT_BOUND, connectors=[{"a": "k"}, {"a": "k"}]
    )
    graph = _backward(trellis, periods=[1])
    kinds = {node.id.split(":")[0] for node in graph.nodes}
    assert "outside" in kinds
    assert not {"start", "end"} & kinds


def test_a_kept_constant_that_no_rule_pairs_is_reported():
    """Where the earlier period sends back `M` and the later period keeps
    `L`, with no pair written, the join leaves `L[>]` unpaired."""
    earlier = KEPT_BOUND.replace("L[<]", "M[<]")
    (join,) = me.unpaired_joins(_trellis(earlier, KEPT_BOUND, connectors=[{"a": "k"}]))
    assert [wire.name for wire in join.wires] == ["L[>]"]


def test_a_stage_that_reads_a_table_from_a_constant_field_has_a_view():
    """A line that selects an entry of a table held by a constant field reads
    the table through its wire, and the stage's view is constructed."""
    text = PENSION.replace("Y_tab : Age → ℝ\n", "").replace(
        "(age[>] : Age", "(Y_tab : Age → ℝ @ !vlu @ !cnst, age[>] : Age"
    )
    collection = me.to_model_explorer(elaborate_text(text, "pension.bl"))
    assert {graph.id for graph in collection.graphs} >= {"backward"}
