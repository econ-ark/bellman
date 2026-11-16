"""Trellis positions do not determine an economic age."""

import importlib.util

import pytest

from bellman.factory import model_explorer
from bellman.trellis import diagram_trellis, elaborate_trellis, load_recipe


def test_registry_age_does_not_change_the_trellis_drawing(two_nodes_registry):
    model = elaborate_trellis(load_recipe(two_nodes_registry, "spec.yml"))
    plain = diagram_trellis({**model, "registry": {}})
    labelled = diagram_trellis({**model, "registry": {"calibration": {"last_age": 65}}})
    assert labelled.source == plain.source
    assert labelled.labels == plain.labels
    for h in range(3):
        assert f"periods[{h}]: h = {h}" in labelled.source
    assert "inter_connectors[0]" in labelled.source
    assert "inter_connectors[1]" in labelled.source


@pytest.mark.skipif(
    importlib.util.find_spec("model_explorer") is None, reason="Model Explorer is not installed"
)
def test_period_layers_keep_positions_without_registry_ages(two_nodes_registry):
    model = elaborate_trellis(load_recipe(two_nodes_registry, "spec.yml"))
    plain = model_explorer.to_model_explorer({**model, "registry": {}}, periods=[0, 2])
    model["registry"] = {"calibration": {"last_age": 65}}
    shown = model_explorer.to_model_explorer(model, periods=[0, 2])
    for graph, original in zip(shown.graphs, plain.graphs, strict=True):
        layers = graph.groupNodeAttributes
        assert layers["periods[0]"] == {}
        assert layers["periods[2]"] == {}
        assert "periods[1]" not in layers
        assert (
            layers["periods[0]/two_nodes"] == original.groupNodeAttributes["periods[0]/two_nodes"]
        )
