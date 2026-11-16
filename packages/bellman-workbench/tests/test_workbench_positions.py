"""Occurrence labels contain positions without inferred ages."""

from bellman_workbench import model, trellis
from bellman_workbench.recipe import Source


def test_occurrence_details_ignore_stale_age_metadata(consport_folder, own_cache_folder):
    folder = model.open_folder(consport_folder)
    source = Source("recipe", "declaration/spec.port-cons.yml")
    shown = trellis.show_trellis(folder, source, trellis.parse_restriction("periods 0–1")).shown
    for graph in shown.collection["graphs"]:
        graph["groupNodeAttributes"].setdefault("periods[0]", {})["age"] = "99"
        graph["groupNodeAttributes"]["periods[0]"]["note"] = "retained metadata"
        rows = trellis.occurrence_rows(folder, shown, graph["id"], (0, "cons"))
        assert rows.place == "periods[0]"
        period = trellis.describe_node(shown, graph["id"], "periods[0]___group___", {})
        assert period.rows == {"note": "retained metadata"}
