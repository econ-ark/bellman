"""Drawings of graphs, periods and trellises."""

import os
import re
import subprocess
import sys

import pytest
from application_files import CORPUS, ROOT, stage_file_id
from discopy.frobenius import Bubble, Cap, Cup, Hypergraph
from skips import require_package
from stage_builders import stage_from_text
from stage_graphs import GRAINS

from bellman.display import drawing as drawing_module
from bellman.display.drawing import FAILED_IMPORT, NO_LAYOUT, Drawing, to_drawing
from bellman.graphs.builders_graphs import bundles
from bellman.native.identity import box_identity
from bellman.native.labels import is_wiring
from bellman.period import diagram_period
from bellman.refusals import FactoryError
from bellman.stage.grains import graph_of
from bellman.stage.pieces import GraphHandle
from bellman.trellis import diagram_trellis, elaborate_trellis, load_recipe

# a stage whose value block authors a node: the expectation of W over the
# income shock, marked `!node` and named `integrate`
STAGE_WITH_AN_AUTHORED_NODE = """@stage: arrival_value
β : (0,1)
R : ℝ₊₊
y : ℝ₊
y ~ LogNormal(0, 1)
[id=income, (a : ℝ₊, y) : !arvl -> (m : ℝ₊) : !dcsn] {
    m = R*a + y
}
[id=expected_value, (W : ℝ @ !vlu) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    EW = E_{y}(W) :: [id=integrate, !node]
    V[<] = β*EW
}
"""


# the twelve drawings of one stage: the two initial diagrams and the two
# builders graphs at the five grains
DRAWINGS = [("initial", direction, "builder") for direction in ("backward", "forward")] + [
    ("builders", direction, grain) for direction in ("backward", "forward") for grain in GRAINS
]


# the three models that carry a whole economic problem, by the stage name that
# the shared fixtures give them
MODELS = ("cons", "cons_savings_iid", "sa_savings")


# the width of a notebook cell and the height of a page, in inches
WIDTH_LIMIT, HEIGHT_LIMIT = 7.0, 13.5


# the drawings that stand taller than a page, each with its height in inches.
# Graphviz measures a label with the fonts of the machine, so a height
# differs a little between machines. A listed drawing that grows taller fails
# as an unlisted one does, and one that comes to fit fails until its entry is
# deleted. No drawing is listed.
OVER_THE_PAGE_TODAY = {}


NODE = re.compile(r'^\s*"(\w+)"\s*\[(.*)\];$')


EDGE = re.compile(r'^\s*"(\w+)"\s*->\s*"(\w+)"\s*(?:\[(.*)\])?;$')


ATTRIBUTE = re.compile(r'(\w+)="((?:[^"\\]|\\.)*)"')


SIZE = re.compile(r'<svg width="([\d.]+)pt" height="([\d.]+)pt"')


# (stage, level, direction, grain) of each graph whose drawing is compared
# with its printed listing: the backward builders graph of `ez_savings`, and
# every graph of the stage with an authored node
LISTED_GRAPHS = [
    ("ez_savings", "builders", "backward", "builder"),
    ("ez_savings", "builders", "backward", "sub-builder"),
    ("ez_savings", "builders", "backward", "primitive"),
    *[
        ("arrival_value", "builders", direction, grain)
        for direction in ("backward", "forward")
        for grain in ("builder", "sub-builder", "primitive")
    ],
    ("arrival_value", "initial", "backward", "builder"),
    ("arrival_value", "initial", "forward", "builder"),
]


def tooltip_identity(attributes):
    """The identity that a tooltip names: the text before the em dash that
    separates it from the sentence that the card prints."""
    return attributes.get("tooltip", "").split(" — ", 1)[0]


def shown_in_drawing(source):
    """The boxes, the wires and the incidences that one drawing shows, read
    back from its DOT text: each box and each wire by the identity that its
    tooltip names, and each incidence as (box, wire, `in` or `out`). An arrow
    that carries a label is a wire folded into it and gives both of its
    incidences."""
    nodes = {
        found.group(1): dict(ATTRIBUTE.findall(found.group(2)))
        for found in (NODE.match(line) for line in source.splitlines())
        if found and not EDGE.match(found.string)
    }
    boxes = {
        tooltip_identity(attributes) for name, attributes in nodes.items() if name.startswith("b")
    }
    wires = {
        tooltip_identity(attributes) for name, attributes in nodes.items() if name.startswith("w")
    }
    incidences = set()
    for line in source.splitlines():
        found = EDGE.match(line)
        if not found:
            continue
        source_name, target_name = found.group(1), found.group(2)
        attributes = dict(ATTRIBUTE.findall(found.group(3) or ""))
        if not attributes:
            if source_name.startswith("w"):
                incidences.add(
                    (
                        tooltip_identity(nodes[target_name]),
                        tooltip_identity(nodes[source_name]),
                        "in",
                    )
                )
            else:
                incidences.add(
                    (
                        tooltip_identity(nodes[source_name]),
                        tooltip_identity(nodes[target_name]),
                        "out",
                    )
                )
            continue
        folded = tooltip_identity(attributes)
        wires.add(folded)
        incidences.add((tooltip_identity(nodes[source_name]), folded, "out"))
        incidences.add((tooltip_identity(nodes[target_name]), folded, "in"))
    return boxes, wires, incidences


def held_in_graph(graph):
    """The boxes, the wires and the incidences that one graph holds, in the
    same three sets: every operator box at every depth, and every wire by the
    spelling of the identities that it carries, a value bundle by its
    components in order, which is the one wire that the drawing gives it."""
    bundled = bundles(graph)

    def spelled(sort):
        return ", ".join(str(member) for member in bundled.get(sort.identity, (sort.identity,)))

    boxes, wires, incidences = set(), set(), set()

    def walk(part):
        inside = part if isinstance(part, Hypergraph) else Hypergraph.from_diagram(part)
        for spider in inside.spider_types:
            for ob in spider.inside:
                wires.add(spelled(ob))
        for box in part.to_diagram().boxes if isinstance(part, Hypergraph) else part.boxes:
            if is_wiring(box):
                continue
            if isinstance(box, Bubble):
                for ob in box.dom.inside + box.cod.inside:
                    wires.add(spelled(ob))
                walk(box.arg)
                continue
            boxes.add(str(box_identity(box)))
            for ob in box.dom.inside:
                wires.add(spelled(ob))
                incidences.add((str(box_identity(box)), spelled(ob), "in"))
            for ob in box.cod.inside:
                wires.add(spelled(ob))
                incidences.add((str(box_identity(box)), spelled(ob), "out"))

    for ob in graph.dom.inside + graph.cod.inside:
        wires.add(spelled(ob))
    walk(graph)
    return boxes, wires, incidences


def bubbles(diagram):
    """The number of bubbles of a diagram, at every depth."""
    return sum(1 + bubbles(box.arg) for box in diagram.boxes if isinstance(box, Bubble))


def kinds_of_cups_and_caps(diagram):
    """The kinds, `Cup` or `Cap`, of the cups and caps of a diagram, at every
    depth."""
    found = set()
    for box in diagram.boxes:
        if isinstance(box, Bubble):
            found |= kinds_of_cups_and_caps(box.arg)
        elif isinstance(box, (Cup, Cap)):
            found.add("Cup" if isinstance(box, Cup) else "Cap")
    return found


def graph_at(stage, level, direction, grain):
    """The graph of `stage` at a level, a direction and a grain: an initial
    diagram as `stage.initial` answers it, and a builders graph by
    `graph_of`."""
    if level == "initial":
        return getattr(stage.initial, direction).graph
    return graph_of(stage, level, direction, grain)


def lines_with_tooltip(source, identity):
    """The lines of a DOT text whose tooltip opens with `identity`."""
    return [line for line in source.splitlines() if f'tooltip="{identity}' in line]


@pytest.fixture(scope="module")
def period_of_two_stages(cons, port):
    """The drawing of one period of the portfolio stage and the consumption
    stage, which the connector `m_next → m` joins."""
    trellis = {
        "periods": [{"stages": {"cons": cons, "port": port}, "connectors": [{"m_next": "m"}]}],
        "inter_connectors": [],
    }
    return diagram_period(trellis, 0)


@pytest.fixture(scope="module")
def trellis_of_three_periods(two_nodes_registry):
    """The elaborated trellis of three periods of the small registry, whose
    registry names no `last_age`."""
    return elaborate_trellis(load_recipe(two_nodes_registry, "spec.yml"))


@pytest.fixture(scope="module")
def drawing_with_a_last_age(trellis_of_three_periods):
    """The drawing of the trellis of three periods, with a registry that
    names the last age 65."""
    return diagram_trellis(
        {**trellis_of_three_periods, "registry": {"calibration": {"last_age": 65}}}
    )


@pytest.fixture(scope="module")
def drawing_of_periods_0_and_1(trellis_of_three_periods):
    """The drawing of the periods 0 and 1 of the trellis of three periods."""
    return diagram_trellis(trellis_of_three_periods, periods=[0, 1])


@pytest.fixture(scope="module")
def arrival_value():
    """The symbolic stage of `STAGE_WITH_AN_AUTHORED_NODE`."""
    return stage_from_text(STAGE_WITH_AN_AUTHORED_NODE)


@pytest.fixture(scope="module")
def primitive_drawing_of_port(port):
    """The DOT text of the drawing of the backward builders graph of the
    portfolio stage at the primitive grain."""
    return port.builder.bwd.primitives.diagram().source


# the three models are in the default set: a layout starts no program, and
# the size of a picture depends on the fonts of the machine, so each machine
# that runs the tests measures every drawing
@pytest.fixture(
    scope="module",
    params=[ROOT / CORPUS[name] for name in MODELS],
    ids=stage_file_id,
)
def drawings_of_a_model(request, read_only_stage_from_file):
    """(name, SVG text) of each of the twelve drawings of the stage file of
    the case, laid out by `Drawing.svg()`."""
    require_package("pygraphviz")
    stage = read_only_stage_from_file(request.param)
    return [
        (
            f"{stage.name} {level} {direction} {grain}",
            GraphHandle(stage, level, direction, grain).diagram().svg(),
        )
        for level, direction, grain in DRAWINGS
    ]


def test_a_drawing_is_laid_out_with_no_program_on_the_search_path(cons, tmp_path, monkeypatch):
    """`svg()` answers the SVG text of a drawing where the search path of
    programs names an empty folder, so the layout uses no program on that
    path. `_repr_svg_()`, which a notebook calls, answers the same text."""
    require_package("pygraphviz")
    monkeypatch.setenv("PATH", str(tmp_path))
    drawing = cons.builder.bwd.diagram()
    svg = drawing.svg()
    assert svg.startswith("<?xml") and svg.rstrip().endswith("</svg>")
    assert "cntn_to_dcsn" in svg
    assert drawing._repr_svg_() == svg


def test_a_drawing_refuses_with_a_message_where_pygraphviz_is_not_installed(cons, monkeypatch):
    """Where the Python package `pygraphviz` is not installed, `svg()` refuses
    with the message `NO_LAYOUT`, and `_repr_svg_()` answers None, so that a
    notebook shows the drawing's short form. The test sets the module's name
    `pygraphviz` to None, the value it has where the package is absent."""
    monkeypatch.setattr(drawing_module, "pygraphviz", None)
    drawing = cons.builder.bwd.diagram()
    with pytest.raises(RuntimeError) as refused:
        drawing.svg()
    assert str(refused.value) == NO_LAYOUT
    assert drawing._repr_svg_() is None
    assert repr(drawing).startswith("Drawing of ")


# what a new interpreter runs to read how a drawing answers there: it imports
# the module of the stage's pieces, which imports the drawing module, then
# prints what `_repr_svg_()` answers and the message that `svg()` refuses with
REFUSAL_IN_A_NEW_INTERPRETER = """
import bellman.stage.pieces
from bellman.display.drawing import Drawing
drawing = Drawing("digraph { a -> b }", ("a", "b"))
print(drawing._repr_svg_())
try:
    drawing.svg()
except RuntimeError as refused:
    print(refused)
"""


def answer_in_a_new_interpreter(set_up, search_path=()):
    """The lines that `REFUSAL_IN_A_NEW_INTERPRETER` prints in a new
    interpreter that first runs the statement `set_up` and that reads the
    folders of `search_path` before its installed packages. The interpreter
    starts in the folder of the package, so that it imports the package of
    this checkout."""
    folders = [str(folder) for folder in search_path] + [os.environ.get("PYTHONPATH", "")]
    done = subprocess.run(
        [sys.executable, "-c", set_up + REFUSAL_IN_A_NEW_INTERPRETER],
        cwd=ROOT / "packages" / "bellman",
        env={**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, folders))},
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    return done.stdout.splitlines()


def test_the_drawing_module_is_imported_where_pygraphviz_is_not_installed():
    """In an interpreter where the import of `pygraphviz` fails as that of a
    package that is not installed, the drawing module is imported,
    `_repr_svg_()` answers None and `svg()` refuses with the message
    `NO_LAYOUT`. The test starts a new interpreter, since its own process
    has imported the module."""
    shown, refusal = answer_in_a_new_interpreter("import sys; sys.modules['pygraphviz'] = None")
    assert shown == "None"
    assert refusal == NO_LAYOUT


def test_an_installed_pygraphviz_that_cannot_be_imported_is_reported_with_its_error(tmp_path):
    """Where a `pygraphviz` stands on the import path and its import raises,
    as an installed package whose Graphviz library cannot be loaded, the
    drawing module is imported, `_repr_svg_()` answers None and `svg()`
    refuses with the error of the import after the words of `FAILED_IMPORT`,
    and not with the message of a package that is not installed."""
    stand_in = 'raise ImportError("the library of Graphviz cannot be loaded")\n'
    (tmp_path / "pygraphviz.py").write_text(stand_in, encoding="utf-8")
    shown, refusal = answer_in_a_new_interpreter("", search_path=[tmp_path])
    assert shown == "None"
    assert refusal == FAILED_IMPORT + "ImportError: the library of Graphviz cannot be loaded"


def test_svg_refuses_with_a_runtime_error_a_source_that_graphviz_does_not_read():
    """`svg()` raises a `RuntimeError` for a source that Graphviz does not
    read, here a DOT text that ends inside an arrow, so that a caller catches
    one kind of error for every drawing that is not laid out."""
    require_package("pygraphviz")
    with pytest.raises(RuntimeError, match="Graphviz did not lay out the drawing"):
        Drawing("digraph { a -> ", ()).svg()


def test_each_cluster_of_a_drawing_has_an_identifier_of_its_own(
    read_only_stage_from_file, corpus_path
):
    """No two clusters in the DOT text of a drawing have the same identifier.
    The test reads the branching stage `tenure`: in its forward initial
    diagram a builder's last box is a sub-builder. Graphviz warns where two
    clusters have the same identifier."""
    stage = read_only_stage_from_file(corpus_path("tenure"))
    for level, direction, grain in DRAWINGS:
        source = GraphHandle(stage, level, direction, grain).diagram().source
        names = re.findall(r'subgraph "(cluster_\w+)"', source)
        assert len(names) == len(set(names)), f"{level} {direction} {grain}: {names}"
    nested = GraphHandle(stage, "initial", "forward", "builder").diagram().source
    assert len(re.findall(r'subgraph "cluster_', nested)) > 2


def test_diagram_period_draws_one_box_for_each_stage_in_forward_order(period_of_two_stages):
    """`diagram_period` draws one box for each stage of the period, the stage
    that comes first in forward order first."""
    assert repr(period_of_two_stages) == "Drawing of 2 boxes"
    assert period_of_two_stages.labels == ("port: port", "cons: cons")


def test_diagram_period_draws_a_connector_as_a_wire_labeled_with_its_two_fields(
    period_of_two_stages,
):
    """`diagram_period` draws the connector of the period as a wire between
    the two stages, labeled with the field that it sends and the field that it
    fills."""
    assert '"port" -> "cons" [label="m_next → m"]' in period_of_two_stages.source


def test_diagram_period_draws_a_continuation_field_that_no_stage_takes_as_a_plain_label(
    period_of_two_stages,
):
    """`diagram_period` draws the continuation field `a`, which no stage of
    the period takes, as a plain label reached by a wire that carries no label
    of its own."""
    source = period_of_two_stages.source
    assert 'label="a"' in source
    assert '"cons" -> "out0";' in source


def test_diagram_period_labels_a_box_by_its_key_and_by_its_stage_where_the_two_differ(
    cons, period_of_two_stages
):
    """The box of a stage prints its key once where the key is the stage's
    name, and the stage's name in brackets below the key where the two
    differ."""
    assert '"cons" [label="cons"];' in period_of_two_stages.source
    renamed = diagram_period(
        {"periods": [{"stages": {"consumption": cons}, "connectors": []}], "inter_connectors": []},
        0,
    )
    assert '"consumption" [label="consumption\\n(cons)"];' in renamed.source


@pytest.mark.parametrize(
    "index", [5, -1, "0"], ids=["past the last period", "negative", "a string"]
)
def test_diagram_period_draws_index_0_of_a_trellis_of_one_period_and_refuses_any_other(
    cons, index
):
    """`diagram_period` draws the one period of a trellis of one period at
    index 0, and refuses any other index under the rule of the shape of a
    trellis file, with the indices that the trellis holds."""
    # as `diagram_trellis` refuses an index that it does not hold, where
    # Python's own IndexError, or a negative index counted from the end,
    # would otherwise reach the reader
    trellis = {"periods": [{"stages": {"cons": cons}, "connectors": []}], "inter_connectors": []}
    assert repr(diagram_period(trellis, 0)) == "Drawing of 1 boxes"
    with pytest.raises(FactoryError) as refused:
        diagram_period(trellis, index)
    assert (refused.value.rule, refused.value.address, refused.value.written) == (
        "trellis-file-shape",
        "periods",
        repr(index),
    )
    assert "the trellis holds 1 periods" in refused.value.message
    assert refused.value.write == "an index between 0 and 0"


def test_diagram_trellis_lists_its_boxes_as_the_trellis_lists_its_periods(drawing_with_a_last_age):
    """`diagram_trellis` draws one box for each period and lists the boxes as
    the trellis lists its periods, the terminal period first."""
    assert repr(drawing_with_a_last_age) == "Drawing of 3 boxes"
    assert drawing_with_a_last_age.labels == (
        "periods[0] two_nodes: two_nodes",
        "periods[1] two_nodes: two_nodes",
        "periods[2] two_nodes: two_nodes",
    )


def test_diagram_trellis_labels_a_period_by_its_index_alone_where_the_registry_names_a_last_age(
    drawing_with_a_last_age, drawing_of_periods_0_and_1
):
    """`diagram_trellis` draws each period as a cluster labeled by its index
    h alone, also where the registry names `last_age`."""
    # the registry names last_age 65, and no label states an age
    labels = [
        'label="periods[0]: h = 0"',
        'label="periods[1]: h = 1"',
        'label="periods[2]: h = 2"',
    ]
    assert [label for label in labels if label not in drawing_with_a_last_age.source] == []
    # the registry of the trellis of three periods names no last_age, and each
    # cluster is labeled by its index alone there as well
    assert ", age " not in drawing_of_periods_0_and_1.source
    alone = ['label="periods[0]: h = 0"', 'label="periods[1]: h = 1"']
    assert [label for label in alone if label not in drawing_of_periods_0_and_1.source] == []


def test_diagram_trellis_writes_the_periods_in_economic_time_the_earliest_first(
    drawing_with_a_last_age,
):
    """The DOT text of the drawing of a trellis writes its periods in the
    order of economic time, `periods[2]` first and the terminal period
    last."""
    source = drawing_with_a_last_age.source
    assert (
        source.index('"periods[2] two_nodes"')
        < source.index('"periods[1] two_nodes"')
        < source.index('"periods[0] two_nodes"')
    )


def test_diagram_trellis_draws_each_inter_period_connector_with_its_index_and_its_two_fields(
    drawing_with_a_last_age,
):
    """Each mapping `inter_connectors[h]` is a wire from the continuation
    field `a` of `periods[h + 1]` to the arrival field `k` of `periods[h]`,
    labeled with its index and its pair of fields."""
    source = drawing_with_a_last_age.source
    assert (
        '"periods[1] two_nodes" -> "periods[0] two_nodes" [label="inter_connectors[0]\\na → k"]'
        in source
    )
    assert (
        '"periods[2] two_nodes" -> "periods[1] two_nodes" [label="inter_connectors[1]\\na → k"]'
        in source
    )


def test_diagram_trellis_states_the_direction_of_economic_time_and_of_the_computation(
    drawing_with_a_last_age,
):
    """The drawing of a trellis states that economic time runs from left to
    right and the backward computation from right to left."""
    source = drawing_with_a_last_age.source
    assert (
        "economic time runs left to right" in source
        and "the backward computation right to left" in source
    )


def test_diagram_trellis_keeps_two_periods_that_no_wire_joins_in_order_by_an_invisible_edge(
    drawing_with_a_last_age, trellis_of_three_periods
):
    """An invisible edge keeps the earlier of two drawn periods at the left
    where no inter-period connector joins them, and the drawing of three
    neighboring periods, which their wires order, holds no invisible edge."""
    assert 'style="invis"' not in drawing_with_a_last_age.source
    apart = diagram_trellis(trellis_of_three_periods, periods=[0, 2]).source
    assert "inter_connectors" not in apart and '-> "periods[0] two_nodes" [style="invis"]' in apart


def test_diagram_trellis_draws_the_listed_periods_alone_and_refuses_one_that_it_does_not_hold(
    trellis_of_three_periods, drawing_of_periods_0_and_1
):
    """`diagram_trellis` draws only the periods that its argument `periods`
    lists, and refuses a period that the trellis does not hold under the rule
    of the shape of a trellis file."""
    drawn = drawing_of_periods_0_and_1
    assert repr(drawn) == "Drawing of 2 boxes" and "periods[2]" not in drawn.source
    with pytest.raises(FactoryError) as refused:
        diagram_trellis(trellis_of_three_periods, periods=[3])
    assert (refused.value.rule, refused.value.address) == ("trellis-file-shape", "periods")


def test_diagram_trellis_draws_only_the_wires_between_the_periods_that_it_lists(
    drawing_of_periods_0_and_1,
):
    """The drawing of the periods 0 and 1 holds the wire of
    `inter_connectors[0]`, which joins them, and not that of
    `inter_connectors[1]`."""
    source = drawing_of_periods_0_and_1.source
    assert "inter_connectors[0]" in source and "inter_connectors[1]" not in source


@pytest.mark.parametrize(
    ("stage_name", "level", "direction", "grain"),
    LISTED_GRAPHS,
    ids=[" ".join(row) for row in LISTED_GRAPHS],
)
def test_the_labels_of_the_drawing_of_a_graph_are_the_lines_of_its_printed_listing(
    request, stage_name, level, direction, grain
):
    """The labels of the drawing of a graph, in order, are the lines of the
    graph's printed listing."""
    graph = graph_at(request.getfixturevalue(stage_name), level, direction, grain)
    assert str(graph).splitlines() == list(to_drawing(graph).labels)


@pytest.mark.parametrize(
    ("stage_name", "grain", "count"),
    [
        pytest.param(
            "ez_savings", "builder", 2, id="ez_savings at the builder grain, two bubbles"
        ),
        pytest.param(
            "ez_savings", "sub-builder", 0, id="ez_savings at the sub-builder grain, no bubble"
        ),
        pytest.param(
            "ez_savings", "primitive", 0, id="ez_savings at the primitive grain, no bubble"
        ),
    ],
)
def test_the_dot_text_of_the_drawing_of_a_graph_is_a_digraph_with_a_subgraph_for_each_bubble(
    request, stage_name, grain, count
):
    """The DOT text of the drawing of a backward builders graph is a digraph
    that holds one subgraph for each bubble of the graph, at every depth, and
    none where the graph holds no bubble."""
    graph = graph_of(request.getfixturevalue(stage_name), "builders", "backward", grain)
    source, held = to_drawing(graph).source, bubbles(graph.to_diagram())
    # the graph holds the bubbles that the row states: two at the builder
    # grain, and none at the finer grains of a stage that writes no line
    # marked `!node`
    assert held == count
    assert source.startswith("digraph {") and source.count("subgraph ") == held


@pytest.mark.parametrize("grain", ["builder", "sub-builder", "primitive"])
@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_each_listing_of_the_stage_with_an_authored_node_holds_at_least_one_line(
    arrival_value, direction, grain
):
    """The printed listing of each builders graph of the stage with an
    authored node holds at least one line."""
    # the statement also checks that no line opens with `Cup(` or `Cap(`, the
    # names of two kinds of wiring box; no graph of this stage holds a wiring
    # box, so that part of the statement cannot fail here
    lines = str(graph_of(arrival_value, "builders", direction, grain)).splitlines()
    assert lines and not any(line.strip().startswith(("Cup(", "Cap(")) for line in lines)


def test_the_listing_of_a_graph_that_holds_a_cup_and_a_cap_names_neither_of_them(tenure):
    """The printed listing of the backward builders graph of the stage
    `tenure`, which holds a cup and a cap, holds at least one line, and no line
    of it opens with `Cup(` or `Cap(`."""
    graph = graph_of(tenure, "builders", "backward", "builder")
    # the guard of the comparison: without a cup and a cap in the graph, no
    # listing would name one
    assert kinds_of_cups_and_caps(graph.to_diagram()) == {"Cup", "Cap"}
    lines = str(graph).splitlines()
    assert lines and not any(line.strip().startswith(("Cup(", "Cap(")) for line in lines)


# each label is the description of the operator that the printed listing
# gives: the authored node by its id and the field it writes, the evaluation
# of that field, and the extension of the measure by the income shock
@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        pytest.param(
            "backward",
            {"integrate → 𝐸𝑊(a)", "Evaluation of 𝐸𝑊≺"},
            id="backward: the authored node and the evaluation of its field",
        ),
        pytest.param(
            "forward",
            {"Extension of the measure by the distribution of y"},
            id="forward: the extension of the measure by the income shock",
        ),
    ],
)
def test_the_listings_of_the_stage_with_an_authored_node_name_its_operators(
    arrival_value, direction, expected
):
    """The printed listings of the builders graph of the stage with an
    authored node, at the builder, sub-builder and primitive grains, hold the
    labels of its operators."""
    labels = {
        line.strip()
        for grain in ("builder", "sub-builder", "primitive")
        for line in str(graph_of(arrival_value, "builders", direction, grain)).splitlines()
    }
    assert expected <= labels


@pytest.mark.parametrize(
    "stage_name", ["cons", "port", "ez_savings", "cons_savings_iid", "sa_savings"]
)
def test_every_drawing_of_a_stage_shows_the_boxes_the_wires_and_the_incidences_of_its_graph(
    request, stage_name
):
    """At every grain of every graph of the stage, the boxes, the wires and
    the incidences that the drawing shows are those that the graph holds, a
    folded wire read from the arrow that carries it."""
    stage = request.getfixturevalue(stage_name)
    differ = []
    for level, direction, grain in DRAWINGS:
        graph = graph_of(stage, level, direction, grain)
        drawing = GraphHandle(stage, level, direction, grain).diagram()
        shown, held = shown_in_drawing(drawing.source), held_in_graph(graph)
        if shown != held:
            parts = [
                word
                for word, one, two in zip(("boxes", "wires", "incidences"), shown, held)
                if one != two
            ]
            differ.append(f"{stage.name} {level} {direction} {grain}: {', '.join(parts)}")
    assert differ == []


def test_the_result_of_the_expectation_of_a_value_line_is_one_plain_wire_naming_the_composite(
    cons_savings_iid,
):
    """In the primitive drawing of the backward graph of `cons_savings_iid`,
    the result of the expectation of the value line is one wire, drawn with
    no weight of its own, whose tooltip prints the expression it holds,
    `𝑉(𝑔(b, y))`."""
    # the expectation reads the output of the pullback, printed as the
    # composite of the value function with the law of motion, whose
    # arguments are the coordinates, the state b and the shock y
    source = cons_savings_iid.builder.bwd.primitives.diagram().source
    named = lines_with_tooltip(source, "dcsn_to_arvl.value:Expectation:1:result")
    assert len(named) == 1
    _, tooltip = named[0].split(' tooltip="', 1)
    assert "𝑉(𝑔(b, y))" in tooltip
    assert 'class="wire-' in named[0] and 'penwidth="3"' not in named[0]


def test_the_policy_of_port_draws_the_expectation_of_its_line_foc_and_none_of_its_doc_line(
    primitive_drawing_of_port,
):
    """The primitive drawing of the portfolio stage holds one result of the
    expectation of the policy's line `foc`, named by that line, and none of
    the expectation of its maximization, which is marked `!doc` and forms no
    operation."""
    objective = lines_with_tooltip(
        primitive_drawing_of_port, "policy.objective:Expectation:1:result"
    )
    foc = lines_with_tooltip(primitive_drawing_of_port, "policy.foc:Expectation:1:result")
    assert len(objective) == 0 and len(foc) == 1


def test_the_expectation_of_the_line_foc_binds_both_shocks_by_name_over_the_aggregation_it_reads(
    primitive_drawing_of_port,
):
    """The result of the expectation of the line `foc` of the portfolio stage
    prints `E_{Ψ, θ}`, as the file writes it, over the aggregation that it
    reads by reference, and no component of a joint variable."""
    foc = lines_with_tooltip(primitive_drawing_of_port, "policy.foc:Expectation:1:result")
    assert len(foc) == 1
    assert "E_{Ψ, θ}[policy.foc:Aggregation:1(k_d, ς, Ψ, θ)]" in foc[0]
    assert "(Ψ, θ)[1]" not in foc[0]


def test_the_result_of_the_aggregation_of_the_line_foc_holds_the_integrand_by_shock_names(
    primitive_drawing_of_port,
):
    """The result of the aggregation of the line `foc` of the portfolio stage
    holds the integrand of the expectation, which reads the two shocks by
    their names and no component of a joint variable."""
    integrand = lines_with_tooltip(primitive_drawing_of_port, "policy.foc:Aggregation:1:result")
    assert len(integrand) == 1
    assert "D_{m_next}𝑉≻(𝑔(k_d, ς, Ψ, θ)) · (Ψ − R)" in integrand[0]
    assert "(Ψ, θ)[1]" not in integrand[0]


def test_every_drawing_of_a_model_fits_a_notebook_cell_and_a_page_at_its_natural_size(
    drawings_of_a_model,
):
    """Every drawing of the model, drawn unscaled at its natural size, is at
    most 7.0 inches wide and 13.5 inches tall, those of `OVER_THE_PAGE_TODAY`
    excepted up to their recorded heights."""
    over, fitting = [], []
    for name, svg in drawings_of_a_model:
        # an SVG states its size in points, 72 to the inch
        width, height = (float(value) / 72 for value in SIZE.search(svg).groups())
        listed = OVER_THE_PAGE_TODAY.get(name)
        if width > WIDTH_LIMIT or height > HEIGHT_LIMIT:
            if listed is None or width > WIDTH_LIMIT or round(height, 2) > listed:
                over.append(f"{name}: {width:.2f} × {height:.2f} inches")
        elif listed is not None:
            fitting.append(
                f"{name} now fits, {width:.2f} × {height:.2f} inches; "
                "delete it from OVER_THE_PAGE_TODAY"
            )
    # a drawing that sets no `size` and no `ratio` is drawn at the scale 1,
    # so that a 10-point label is 10 points
    scaled = [
        name
        for name, svg in drawings_of_a_model
        if not ("scale(1 1)" in svg or "scale(" not in svg)
    ]
    assert scaled == []
    assert over == [] and fitting == []


def test_the_smallest_text_in_the_drawings_of_a_model_is_drawn_at_9_points(drawings_of_a_model):
    """The smallest font size in the twelve drawings of the model, none of
    which is scaled, is 9 points."""
    # a scaled drawing keeps the font size that its text states and draws the
    # text smaller, so that the stated sizes are those of the page only where
    # no drawing is scaled
    scaled = [
        name
        for name, svg in drawings_of_a_model
        if not ("scale(1 1)" in svg or "scale(" not in svg)
    ]
    assert scaled == []
    sizes = [
        float(value)
        for _, svg in drawings_of_a_model
        for value in re.findall(r'font-size="([\d.]+)"', svg)
    ]
    assert min(sizes, default=None) == 9.0
