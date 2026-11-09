"""The acceptance file of AMD-MI-001, the legend, the box text and the colors
of the graph pane. The amendment is AMD-MI-001, "Model interface spec 0.3,
amendment 1 — the legend under the graph", and its brief is "Brief: the
legend, the box text and the colors of the graph pane".
The file holds one test for each acceptance item of the brief's §3 that a
test closes, each a corpus stage, a public query and the value it prints, and
is deleted when the next amendment is accepted."""

import json
import re
import subprocess

import pytest
from conftest import CORPUS, ROOT

from bellman.display.drawing import box_symbol
from bellman.factory.model_explorer import label_sources, port_label
from bellman.native.identity import box_identity
from bellman.native.labels import is_wiring
from bellman.refusals import NotConstructed
from bellman.stage import to_model_explorer, write_model_explorer


def test_item_1_each_box_reads_its_kind_and_the_head_of_its_symbol_on_two_lines(
    cons_methods_only, request
):
    pytest.importorskip("model_explorer")
    labels = {
        graph.id: {node.id: node.label for node in graph.nodes}
        for graph in to_model_explorer(cons_methods_only).graphs
    }
    # the brief's slash between a box's two lines is the line break
    assert labels["backward"] == {
        "GraphInputs": "Inputs",
        "cntn_to_dcsn:Pullback": "𝑉≻ ∘ 𝑔≻",
        "cntn_to_dcsn:Aggregation": "𝐺",
        "cntn_to_dcsn:Evaluation": "𝑉(m_d), 𝑑𝑉(m_d) · !Linear",
        "dcsn_to_arvl:Pullback": "𝑉, 𝑑𝑉 ∘ 𝑔≺",
        "dcsn_to_arvl:Aggregation": "𝐺",
        "dcsn_to_arvl:Evaluation": "𝑉≺(m), 𝑑𝑉≺(m)",
        "policy.InvEuler:Aggregation": "𝐺 · InvEuler",
        "policy.endoggrid:Aggregation": "𝐺 · endoggrid",
        "policy.cons_choice:Pullback": "𝑐 ∘ 𝑚_d≻",
        "policy:Evaluation": "𝑐(m_d) · !egm",
        "GraphOutputs": "Outputs",
    }
    assert labels["forward"] == {
        "GraphInputs": "Inputs",
        "arvl_to_dcsn:Pushforward": "𝑔≺∗μ",
        "dcsn_to_cntn:Pushforward": "𝑔≻∗μ",
        "GraphOutputs": "Outputs",
    }
    # no node label of the views of the eight corpus stages holds the words
    # `at the output`, or a law or an aggregator written out at a policy
    for name in CORPUS:
        for graph in to_model_explorer(request.getfixturevalue(name)).graphs:
            for node in graph.nodes:
                assert "at the output" not in node.label, (name, node.id)
                assert "(·" not in node.label, (name, node.id)


def test_item_2_the_drawing_labels_each_evaluation_by_its_outputs_as_the_view_labels_their_ports(
    cons, tenure, request
):
    # the DOT statement of a box writes its label and then its tooltip,
    # which names the box before an em dash
    source = cons.builder.bwd.diagram().source
    for name, label in (
        ("cntn_to_dcsn:Evaluation", "𝑉(m_d), 𝑑𝑉(m_d)"),
        ("dcsn_to_arvl:Evaluation", "𝑉≺(m), 𝑑𝑉≺(m)"),
        ("policy:Evaluation", "𝑐(m_d)"),
    ):
        assert f'[label="{label}" tooltip="{name} — ' in source, name
    assert "at the output" not in source
    # an evaluation with three outputs, longer than one line of its box, is
    # drawn as its first two outputs and the count of the third, three whole
    # lines, which DOT separates by `\n`; the tooltip names every output
    source = tenure.builder.bwd.diagram().source
    for name, lines, outputs in (
        (
            "cntn_to_dcsn:Evaluation",
            ("𝑉(a_d, h_d, z_d),", "𝑑𝑉_a(a_d, h_d, z_d)", "and 1 more"),
            "𝑉, 𝑑𝑉_a, 𝑑𝑉_h",
        ),
        (
            "dcsn_to_arvl:Evaluation",
            ("𝑉≺(a, h, z),", "𝑑𝑉_a≺(a, h, z)", "and 1 more"),
            "𝑉≺, 𝑑𝑉_a≺, 𝑑𝑉_h≺",
        ),
    ):
        label = "\\n".join(lines)
        assert f'[label="{label}" tooltip="{name} — Evaluation of {outputs}"' in source, name
    # on every corpus stage, an evaluation's symbol is the labels the view
    # gives its output ports, the first two joined by commas and the others
    # counted, in each builders graph at the primitive grain, the grain the
    # view draws; and no evaluation's label is cut with `…` in the drawings
    # of the builders graph at the builder, sub-builder and primitive grains
    compared, drawn = set(), set()
    for name in CORPUS:
        stage = request.getfixturevalue(name)
        for builders in (stage.builder.bwd, stage.builder.fwd):
            # a graph the construction refuses, such as the forward graph of
            # `retiree_death`, has no boxes to compare and is skipped
            try:
                graph = builders.primitives.graph
            except NotConstructed:
                continue
            sources = label_sources(stage, graph)
            for box in graph.boxes:
                if is_wiring(box) or box_identity(box).kind != "Evaluation":
                    continue
                ports = [port_label(sources, ob.identity) for ob in box.cod.inside]
                named = ", ".join(ports[:2])
                if len(ports) > 2:
                    named += f" and {len(ports) - 2} more"
                assert box_symbol(box, sources.value_aggregations) == named, (name, box.name)
                compared.add(name)
            for drawing in (
                builders.diagram(),
                builders.sub_builders.diagram(),
                builders.primitives.diagram(),
            ):
                for line in drawing.source.splitlines():
                    if " — Evaluation of " in line:
                        assert "…" not in line.split(' tooltip="')[0], (name, line)
                        drawn.add(name)
    # every corpus stage holds at least one evaluation compared and drawn
    assert compared == drawn == set(CORPUS)


def test_item_3_four_colors_tell_the_levels_apart_and_ultramarine_lines_each_builders_outputs(
    cons, cons_methods_only, port_cons, sa_savings, tmp_path
):
    pytest.importorskip("model_explorer")
    # every value of every color key in the two files of the bound stage and
    # of the trellis, gathered from each JSON object as a file is read
    written = set()

    def gathered(pairs):
        """One object of a file, the values of its color keys added to
        `written`."""
        written.update(
            value for key, value in pairs if key.endswith("Color") and value is not None
        )
        return dict(pairs)

    for view, folder in ((cons_methods_only, "stage"), (port_cons, "trellis")):
        for path in write_model_explorer(view, tmp_path / folder):
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=gathered)
    assert written == {
        "#FFFFFF",  # white, `--bf-face`
        "#EDF7FC",  # the first step of the ice, `--bl-ice`
        "#C5E5F1",  # the second step of the ice, `--bl-ice-2`
        "#91BED7",  # the third step of the ice, `--bl-ice-3`
        "#172A52",  # navy, `--bl-navy`
        "#214EDA",  # ultramarine, `--bl-ultramarine`
        "#C45C1D",  # the orange line, `--bf-accent-line`
    }
    # on `cons`, the boxes lined in ultramarine are the three evaluations
    # and the two push-forwards, each of which writes its builder's outputs
    assert {
        (graph.id, node.id)
        for graph in to_model_explorer(cons).graphs
        for node in graph.nodes
        if node.style.borderColor == "#214EDA"
    } == {
        ("backward", "cntn_to_dcsn:Evaluation"),
        ("backward", "dcsn_to_arvl:Evaluation"),
        ("backward", "policy:Evaluation"),
        ("forward", "arvl_to_dcsn:Pushforward"),
        ("forward", "dcsn_to_cntn:Pushforward"),
    }
    # on `sa_savings`, the fill of a layer as the viewer applies the graph's
    # configurations: that of the first whose pattern it finds in the
    # layer's namespace and that sets a fill
    graphs = to_model_explorer(sa_savings).graphs
    (backward,) = [graph for graph in graphs if graph.id == "backward"]
    assert "cntn_to_dcsn/risk_ce" in {node.namespace for node in backward.nodes}
    fills = {
        layer: next(
            config.backgroundColor
            for config in backward.groupNodeConfigs
            if config.backgroundColor is not None and re.search(config.namespaceRegex, layer)
        )
        for layer in ("cntn_to_dcsn/risk_ce", "cntn_to_dcsn")
    }
    assert fills == {"cntn_to_dcsn/risk_ce": "#91BED7", "cntn_to_dcsn": "#C5E5F1"}


def test_item_4_the_view_is_written_to_two_files_and_no_searched_file_holds_a_retired_name(
    cons, tmp_path
):
    # the retired names of the method overlay, its tints, the family styles
    # and the node data, each written in two joined parts so that no line of
    # the repository, this file's among them, holds one
    retired = (
        "method" + "_overlay",
        "METHOD" + "_TINTS",
        "FAMILY" + "_STYLES",
        "node" + "-data",
        "node" + "_data",
    )
    # the brief's paths
    paths = (
        "packages/bellman",
        "packages/bellman-workbench/bellman_workbench",
        "packages/bellman-workbench/tests",
        "tutorials",
        "docs/_hooks",
        "docs/Bellman-Sym",
        "docs/overview",
    )
    searched = subprocess.run(
        ["git", "grep", "-n", "-E", "|".join(retired), "--", *paths],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    # no tracked file under those paths holds one (git grep exits with 1
    # where it finds nothing)
    assert (searched.returncode, searched.stdout) == (1, ""), searched.stderr
    pytest.importorskip("model_explorer")
    # the paths of the graph file and of the file of the perch overlays
    assert write_model_explorer(cons, tmp_path) == (
        tmp_path / "cons.graph.json",
        tmp_path / "cons.edge-overlays.json",
    )
    # the folder holds these two files alone
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "cons.edge-overlays.json",
        "cons.graph.json",
    ]
