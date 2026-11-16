"""The boundary nodes, the routes and the ports of a trellis view in Model
Explorer: the boundary nodes and the route records of the durables trellis,
the wires that a join pairs by its route, and the ports of the state fields
that joins reach or leave unjoined."""

import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest
from application_files import DURABLES, PENSION
from model_explorer_views import (
    attribute_of,
    attributes,
    graph_named,
    needs_viewer,
    occurrence_of,
)
from stage_texts import changed
from trellises import declarations_copy, rewrite_once
from two_sets import one_row_by_default

from bellman.factory.connections import Component, FieldUse, Pair, Route
from bellman.factory.model_explorer import LAW_RULE, _Join, _route_pairs
from bellman.trellis import (
    connection_report,
    elaborate_trellis,
    load_recipe,
    load_trellis,
    specify_trellis,
    to_model_explorer,
    unjoined_fields,
)

# the kinds of the nodes at which a wire enters or leaves a trellis graph
BOUNDARY_KINDS = ("start", "end", "outside")

# the template of the durables trellis file, which repeats its period fifty
# times after the terminal period
DURABLES_TEMPLATE = "{template: period.yml, repeat: 50}"

# the default row is the durables trellis cut to four periods; the row of
# the whole trellis, of 51 periods, is in the complete set
DURABLES_ROWS = pytest.mark.parametrize(
    "durables_life_cycle",
    one_row_by_default(("durables_trellis_four_periods", "durables_trellis")),
    ids=["four-periods", "fifty-one-periods"],
    indirect=True,
)

# the two views of the durables trellis whose edges are read: the whole
# trellis and periods 0 to 2
DURABLES_VIEWS = pytest.mark.parametrize(
    "view",
    ["durables_view", "durables_view_of_three_periods"],
    ids=["whole", "periods-0-to-2"],
)


def boundary_nodes(graph):
    """The boundary nodes of a graph of a trellis view, each as its id, its
    attributes, the ids of its ports and its edges, `(source node, source
    port, target port)`, sorted by id."""
    return sorted(
        (
            node.id,
            attributes(node),
            [m.id for m in (*node.outputsMetadata, *node.inputsMetadata)],
            [
                (e.sourceNodeId, e.sourceNodeOutputId, e.targetNodeInputId)
                for e in node.incomingEdges
            ],
        )
        for node in graph.nodes
        if not node.namespace and attributes(node).get("kind") in BOUNDARY_KINDS
    )


def edges_from(graph, node_id):
    """The edges of a graph that leave the node `node_id`, each as the node
    it enters and its two ports."""
    return sorted(
        (node.id, e.sourceNodeOutputId, e.targetNodeInputId)
        for node in graph.nodes
        for e in node.incomingEdges
        if e.sourceNodeId == node_id
    )


def edges_with_ends(view):
    """Each edge of each graph of a trellis view, as the graph's id, the
    node the edge enters, the edge, and the occurrences of its two ends,
    None for an end at the graph's root."""
    return [
        (graph.id, node, edge, (occurrence_of(edge.sourceNodeId), occurrence_of(node.id)))
        for graph in view.graphs
        for node in graph.nodes
        for edge in node.incomingEdges
    ]


def joining_edges(view):
    """Each edge of a trellis view between two stage occurrences, as the
    graph's id, the route record that the edge carries, and the occurrences
    of its two ends."""
    return [
        (graph_id, attribute_of(edge, "route"), ends)
        for graph_id, _, edge, ends in edges_with_ends(view)
        if None not in ends and ends[0] != ends[1]
    ]


def route_keys(report):
    """The routes of a connection report, each by the address of its source
    occurrence, its branch and the address of its destination occurrence."""

    def address(position):
        return f"periods[{position[0]}]/{position[1]}"

    return {
        (address(route.source), route.branch, address(route.destination)): route
        for route in report.routes
    }


def route_records(view):
    """The route records that the edges of a trellis view carry, by their
    source and their destination occurrence."""
    return {
        (record["source"], record["destination"]): record
        for graph in view.graphs
        for node in graph.nodes
        for edge in node.incomingEdges
        if (record := attribute_of(edge, "route")) is not None
    }


def unjoined_ports(collection, direction):
    """The ports of the graph `direction` of a view that are marked
    `unjoined`, as `{(node id, port id): {key: value}}`."""
    graph = graph_named(collection, direction)
    return {
        (node.id, item.id): {pair.key: pair.value for pair in item.attrs}
        for node in graph.nodes
        for item in (*node.inputsMetadata, *node.outputsMetadata)
        if any(pair.key == "unjoined" for pair in item.attrs)
    }


def all_edges(collection, direction):
    """Every edge of the graph `direction` of a view, as `(target node,
    source node, source port, target port)`, sorted."""
    graph = graph_named(collection, direction)
    return sorted(
        (node.id, edge.sourceNodeId, edge.sourceNodeOutputId, edge.targetNodeInputId)
        for node in graph.nodes
        for edge in node.incomingEdges
    )


def ports_of(graph, node_id, side):
    """The ports on `side` of a node of a graph, each as the last part of
    its id and its attributes."""
    node = next(node for node in graph.nodes if node.id == node_id)
    return [
        (item.id.rsplit("/", 1)[1], {pair.key: pair.value for pair in item.attrs})
        for item in getattr(node, side)
    ]


def texts_of_two_periods(file):
    """The argument `texts` of `load_trellis` that shortens the trellis file
    `file`, which repeats its period six times, to two periods."""
    text = file.read_text(encoding="utf-8")
    return {str(file.resolve()): changed(text, ("    repeat: 6\n", "    repeat: 2\n"))}


def trellis_with_connector_emptied(folder):
    """The trellis file of records of a copy under `folder` of the
    declaration folders of the portfolio and cons-port models
    (`declarations_copy`), with its connector `{w: m}` emptied to `{}`, so
    that in no period does a line join `port`'s `w` to `cons`'s `m`; the
    inter-period mapping `{disc.a: k}` is kept."""
    _, trellis = declarations_copy(folder)
    rewrite_once(trellis, "- {w: m}", "- {}")
    return trellis


def pension_with_mapping_emptied(folder):
    """A copy under `folder` of the pension model's declaration folder, at
    its path in the repository, whose one standing inter-period mapping is
    emptied to `{}`, so that in `periods[1]` and every earlier period no join
    reads the two continuation states `y_f_ret` and `y_p_ret` of
    `retiree_saving`."""
    registry = Path(folder) / "applications/pension-retirement/declaration"
    shutil.copytree(PENSION, registry)
    rewrite_once(
        registry / "trellis.yml",
        "  - {y_f_wk: y_f_w, y_p_wk: y_p_w, y_f_rt: y_f_r, y_p_rt: y_p_r, "
        "y_f_ret: y_f_r, y_p_ret: y_p_r}\n",
        "  - {}\n",
    )
    return registry


class WireIdentity(SimpleNamespace):
    """The identity of a wire as a join reads it, its field and its perch,
    printed as its field."""

    def __str__(self):
        return str(self.field)


@dataclass(frozen=True, eq=False)
class WireRecord:
    """The record of a wire as a join reads it: its identity, its role and
    its coordinates; each record is a key of its own."""

    identity: WireIdentity
    role: str
    coordinates: tuple


def record_of_wire(name, role, perch, *fields):
    """The record of a wire named `name` of role `role` at `perch`, whose
    coordinates are the fields `fields` at that perch."""
    points = tuple(SimpleNamespace(perch=perch, field=field) for field in fields)
    return WireRecord(WireIdentity(field=name, perch=perch), role, points)


def stage_graph(reads=(), writes=()):
    """The graph of a stage occurrence as a join reads it: the wire records
    that it reads and those that it writes."""
    return SimpleNamespace(dom=SimpleNamespace(inside=reads), cod=SimpleNamespace(inside=writes))


def field_pair(writer, field, reader, arrival):
    """A pair of a route of period 0 that an authored connector writes: the
    continuation field `field` of `writer` to the arrival field `arrival`
    of `reader`."""
    return Pair(
        FieldUse(0, writer, "cntn", field, None),
        FieldUse(0, reader, "arvl", arrival, None),
        "authored",
        "periods[0].connectors[0]",
    )


def certified_route(pairs, components=(), law=None):
    """A certified route of period 0 that holds the pairs `pairs`, the
    components `components` and the joint law `law`."""
    return Route(
        source=(0, pairs[0].writing.key),
        branch=None,
        destination=(0, pairs[0].reading.key),
        source_fields=(),
        destination_fields=(),
        pairs=tuple(pairs),
        permutation=(),
        inverse=(),
        state="complete",
        compatibility="compatible",
        law=law,
        components=tuple(components),
        backward="compatible",
        status="certified",
        obligations=(),
        basis=(),
    )


def view_join(writer, field, reader, arrival):
    """The join of a trellis view from the field `field` of `writer` to the
    field `arrival` of `reader` in period 0."""
    return _Join(
        f"periods[0]/{writer}", field, f"periods[0]/{reader}", arrival, f"{field} → {arrival}", ""
    )


def wire_component(required, supplied, role, status, rule):
    """A component of a route that pairs the wire `required` with the wire
    `supplied`, or with none, under the rule `rule`."""
    return Component(
        str(required.identity),
        None if supplied is None else str(supplied.identity),
        role,
        status,
        "",
        (),
        rule,
    )


def forward_measures():
    """The continuation measures of two stages `work` and `retire`, and the
    graphs of the occurrences of these two stages and of a stage `next`
    that reads one arrival measure."""
    work = record_of_wire("work", "measure", "cntn", "a")
    retire = record_of_wire("retire", "measure", "cntn", "a")
    arrival = record_of_wire(None, "measure", "arvl", "a")
    graphs = {
        "periods[0]/work": stage_graph(writes=[work]),
        "periods[0]/retire": stage_graph(writes=[retire]),
        "periods[0]/next": stage_graph(reads=[arrival]),
    }
    return work, retire, graphs


@pytest.fixture(scope="session")
def durables_trellis_four_periods():
    """The life-cycle trellis of the durables application cut to four
    periods, the terminal period and three repeats of its template where the
    file writes fifty, elaborated once for the session from the recipe
    `spec.yml`, whose trellis file `load_recipe` reads from its argument
    `texts`. The tests read it and do not bind it."""
    file = (DURABLES / "trellis.yml").resolve()
    text = file.read_text(encoding="utf-8")
    cut = changed(text, (DURABLES_TEMPLATE, "{template: period.yml, repeat: 3}"))
    return elaborate_trellis(load_recipe(DURABLES, "spec.yml", {str(file): cut}))


@pytest.fixture(scope="module")
def durables_life_cycle(request):
    """The durables trellis that the fixture named by the row gives."""
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="module")
def durables_report(durables_life_cycle):
    """The connection report of the whole selection of the durables
    trellis."""
    return connection_report(durables_life_cycle)


@pytest.fixture(scope="module")
def durables_view(durables_life_cycle, durables_report):
    """The view of the whole durables trellis, drawn from the selection of
    its connection report."""
    return to_model_explorer(durables_life_cycle, selection=durables_report.selection)


@pytest.fixture(scope="module")
def durables_view_of_three_periods(durables_life_cycle, durables_report):
    """The view of the durables trellis restricted to periods 0 to 2, drawn
    from the selection of its connection report."""
    return to_model_explorer(
        durables_life_cycle, periods=range(3), selection=durables_report.selection
    )


@pytest.fixture(scope="module")
def durables_reached(durables_life_cycle, durables_report):
    """The occurrences outside periods 0 to 2 that a route of the connection
    report of those three periods joins to an occurrence inside them,
    sorted."""
    chosen = {(h, key) for h in range(3) for key in durables_life_cycle["periods"][h]["stages"]}
    three = connection_report(
        durables_life_cycle, periods=range(3), selection=durables_report.selection
    )
    return sorted(
        {
            f"periods[{h}]/{key}"
            for route in three.routes
            for h, key in (route.source, route.destination)
            if (route.source in chosen) != (route.destination in chosen) and (h, key) not in chosen
        }
    )


@pytest.fixture(scope="module")
def field_ports_view(durables_life_cycle):
    """The view of periods 0 and 1 of the durables trellis with the ports
    of the state fields of each occurrence."""
    return to_model_explorer(durables_life_cycle, periods=[0, 1], unjoined=True)


@pytest.fixture(scope="module")
def two_period_trellis(tmp_path_factory):
    """The trellis file of records of a copy of the declaration folders of
    the portfolio and cons-port models (`declarations_copy`), shortened to
    two periods and specified."""
    _, file = declarations_copy(tmp_path_factory.mktemp("two-periods"))
    return specify_trellis(load_trellis(file, texts_of_two_periods(file)))


@pytest.fixture(scope="module")
def unjoined_view(two_period_trellis):
    """The view of the trellis of records of two periods with its unjoined
    ports marked."""
    return to_model_explorer(two_period_trellis, unjoined=True)


@pytest.fixture(scope="module")
def emptied_trellis(tmp_path_factory):
    """The trellis of records of six periods with its connector `{w: m}`
    emptied, specified."""
    folder = tmp_path_factory.mktemp("emptied")
    return specify_trellis(load_trellis(trellis_with_connector_emptied(folder)))


@pytest.fixture(scope="module")
def emptied_view_of_two_periods(emptied_trellis):
    """The view of periods 0 and 1 of the trellis with its connector
    emptied, with its unjoined ports marked."""
    return to_model_explorer(emptied_trellis, periods=[0, 1], unjoined=True)


@pytest.fixture(scope="module")
def emptied_pension_view(tmp_path_factory):
    """The view, with its unjoined ports marked, of the pension trellis with
    its standing inter-period mapping emptied, shortened to the terminal
    period and one period of `period.yml`."""
    registry = pension_with_mapping_emptied(tmp_path_factory.mktemp("pension"))
    file = registry / "trellis.yml"
    text = file.read_text(encoding="utf-8")
    cut = changed(
        text, ("{template: period.yml, repeat: 14}", "{template: period.yml, repeat: 1}")
    )
    trellis = elaborate_trellis(load_recipe(registry, "spec.yml", {str(file.resolve()): cut}))
    return to_model_explorer(trellis, unjoined=True)


@pytest.fixture
def backward_join():
    """A join from `early` to `late` in period 0 whose route has three
    components: the first pairs the value `V_w` that `early` reads with the
    value `V` that `late` writes under the rule one wire per role, the
    second pairs `V_a` with `V_a` under the rule equal name with the status
    incompatible, and the third supplies no wire for `V_h`; with the graphs
    of the two occurrences and the selection that holds the route."""
    reads = [
        record_of_wire("V_w", "value", "cntn", "a_w"),
        record_of_wire("V_a", "value", "cntn", "a_w"),
        record_of_wire("V_h", "value", "cntn", "a_w"),
    ]
    writes = [
        record_of_wire("V", "value", "arvl", "a"),
        record_of_wire("V_a", "value", "arvl", "a"),
        record_of_wire("V_h", "value", "arvl", "a"),
    ]
    components = [
        wire_component(reads[0], writes[0], "value", "compatible", "one wire per role"),
        wire_component(reads[1], writes[1], "value", "incompatible", "equal name"),
        wire_component(reads[2], None, "value", "not-established", ""),
    ]
    route = certified_route([field_pair("early", "a_w", "late", "a")], components)
    return SimpleNamespace(
        reads=reads,
        writes=writes,
        joins=[view_join("early", "a_w", "late", "a")],
        graphs={
            "periods[0]/early": stage_graph(reads=reads),
            "periods[0]/late": stage_graph(writes=writes),
        },
        selection=SimpleNamespace(routes=[route]),
    )


@DURABLES_ROWS
@needs_viewer
def test_neither_graph_of_the_durables_trellis_holds_an_inputs_or_outputs_node_at_its_root(
    durables_life_cycle, durables_view
):
    """Neither builders graph of the whole durables trellis holds a node
    `Inputs` or `Outputs` at its root."""
    for graph in durables_view.graphs:
        assert not [
            node.id
            for node in graph.nodes
            if not node.namespace and node.id.endswith(("GraphInputs", "GraphOutputs"))
        ], graph.id


@DURABLES_ROWS
@needs_viewer
def test_the_durables_forward_graph_starts_at_the_first_tenure_and_ends_at_bequest(
    durables_life_cycle, durables_view
):
    """The forward graph of the whole durables trellis starts at the arrival
    measure of the first `tenure` in time and ends at the decision measure
    of `bequest` in the last period, each at a boundary node with its
    edge."""
    first, last = (
        f"periods[{len(durables_life_cycle['periods']) - 1}]/tenure",
        "periods[0]/bequest",
    )
    forward = graph_named(durables_view, "forward")
    forward_start = f"{first}/tenure:measure:arvl"
    forward_end = f"{last}/bequest:measure:dcsn"
    assert boundary_nodes(forward) == [
        (
            f"end:{forward_end}",
            {"kind": "end", "label": "terminal μ"},
            [forward_end],
            [(f"{last}/arvl_to_dcsn:Pushforward", forward_end, forward_end)],
        ),
        (
            f"start:{forward_start}",
            {"kind": "start", "label": "starting data μ≺"},
            [forward_start],
            [],
        ),
    ]
    assert edges_from(forward, f"start:{forward_start}") == [
        (f"{first}/arvl_to_dcsn:DistributionExtension:ε", forward_start, forward_start)
    ]


@DURABLES_ROWS
@needs_viewer
def test_the_durables_backward_graph_starts_at_the_terminal_value_and_ends_at_the_first_tenure(
    durables_life_cycle, durables_view
):
    """The backward graph of the whole durables trellis starts at the
    terminal value of `bequest` and ends at the arrival value of the first
    `tenure` in time, each at a boundary node with its edge."""
    first, last = (
        f"periods[{len(durables_life_cycle['periods']) - 1}]/tenure",
        "periods[0]/bequest",
    )
    backward = graph_named(durables_view, "backward")
    terminal = f"{last}/bequest:function:cntn:V"
    result = f"{first}/tenure:function:arvl:V"
    # the terminal value's node, whose edge leaves for bequest's aggregation
    terminal_node = (
        f"start:{terminal}",
        {"kind": "start", "label": "terminal condition 𝑉≻()"},
        [terminal],
        [],
    )
    assert boundary_nodes(backward) == [
        (
            f"end:{result}",
            {"kind": "end", "label": "result 𝑉≺(a, h, z)"},
            [result],
            [(f"{first}/dcsn_to_arvl:Evaluation", result, result)],
        ),
        terminal_node,
    ]
    assert edges_from(backward, f"start:{terminal}") == [
        (f"{last}/cntn_to_dcsn:Aggregation", terminal, terminal)
    ]


@DURABLES_ROWS
@needs_viewer
def test_the_forward_graph_of_a_restricted_durables_view_marks_each_occurrence_reached_outside(
    durables_view_of_three_periods, durables_reached
):
    """Restricted to periods 0 to 2, the forward graph of the durables
    trellis marks with one `outside` node, which names it, each occurrence of
    `periods[3]` that the connection report joins to `tenure` of
    `periods[2]`, each node holding the arrival measure of that `tenure`."""
    assert durables_reached == ["periods[3]/adjuster_cons", "periods[3]/keeper_cons"]
    forward = graph_named(durables_view_of_three_periods, "forward")
    last = "periods[0]/bequest"
    forward_end = f"{last}/bequest:measure:dcsn"
    tenure = "periods[2]/tenure"
    measure = f"{tenure}/tenure:measure:arvl"
    assert boundary_nodes(forward) == [
        (
            f"end:{forward_end}",
            {"kind": "end", "label": "terminal μ"},
            [forward_end],
            [(f"{last}/arvl_to_dcsn:Pushforward", forward_end, forward_end)],
        )
    ] + [
        (
            f"outside:{tenure}:{where}",
            {"kind": "outside", "label": where, "target": where},
            [measure],
            [],
        )
        for where in durables_reached
    ]
    for where in durables_reached:
        assert edges_from(forward, f"outside:{tenure}:{where}") == [
            (f"{tenure}/arvl_to_dcsn:DistributionExtension:ε", measure, measure)
        ]


@DURABLES_ROWS
@needs_viewer
def test_the_backward_graph_of_a_restricted_durables_view_marks_each_occurrence_reached_outside(
    durables_view_of_three_periods, durables_reached
):
    """Restricted to periods 0 to 2, the backward graph of the durables
    trellis marks with one `outside` node each occurrence of `periods[3]`
    that the connection report joins to `tenure` of `periods[2]`, its one
    port the value that the evaluation of that `tenure` writes."""
    assert durables_reached == ["periods[3]/adjuster_cons", "periods[3]/keeper_cons"]
    backward = graph_named(durables_view_of_three_periods, "backward")
    terminal = "periods[0]/bequest/bequest:function:cntn:V"
    terminal_node = (
        f"start:{terminal}",
        {"kind": "start", "label": "terminal condition 𝑉≻()"},
        [terminal],
        [],
    )
    tenure = "periods[2]/tenure"
    leaving = [f"{tenure}/tenure:function:arvl:V"]
    assert boundary_nodes(backward) == sorted(
        [
            (
                f"outside:{tenure}:{where}",
                {"kind": "outside", "label": where, "target": where},
                leaving,
                [(f"{tenure}/dcsn_to_arvl:Evaluation", port, port) for port in leaving],
            )
            for where in durables_reached
        ]
        + [terminal_node]
    )


@DURABLES_ROWS
@DURABLES_VIEWS
@needs_viewer
def test_only_an_edge_between_two_occurrences_carries_a_route(request, durables_life_cycle, view):
    """An edge of a durables trellis view that stays within one occurrence
    or meets the graph's root carries no route record."""
    for graph_id, node, edge, ends in edges_with_ends(request.getfixturevalue(view)):
        if None in ends or ends[0] == ends[1]:
            assert attribute_of(edge, "route") is None, (graph_id, node.id, edge)


@DURABLES_ROWS
@DURABLES_VIEWS
@needs_viewer
def test_the_route_record_on_an_edge_is_the_route_of_the_connection_report(
    request, durables_report, view
):
    """The route record on each edge between two occurrences of a durables
    trellis view is the route of the connection report that joins them."""
    routes = route_keys(durables_report)
    joins = joining_edges(request.getfixturevalue(view))
    assert joins
    for _, record, _ in joins:
        key = (record["source"], record["branch"], record["destination"])
        route = routes[key]
        assert record == {
            "branch": route.branch,
            "source": key[0],
            "destination": key[2],
            "source_fields": list(route.source_fields),
            "destination_fields": list(route.destination_fields),
            "pairs": [
                {
                    "source_field": pair.writing.field,
                    "destination_field": pair.reading.field,
                    "origin": pair.origin,
                    "address": pair.address,
                }
                for pair in route.pairs
            ],
            "status": route.status,
            "law": route.law,
        }


@DURABLES_ROWS
@DURABLES_VIEWS
@needs_viewer
def test_an_edge_runs_from_the_routes_source_forward_and_from_its_destination_backward(
    request, durables_life_cycle, view
):
    """Each edge between two occurrences of a durables trellis view runs
    from the source of the route that it carries to the route's destination
    in the forward graph, the other way in the backward graph."""
    joins = joining_edges(request.getfixturevalue(view))
    assert joins
    for graph_id, record, ends in joins:
        key = (record["source"], record["branch"], record["destination"])
        drawn = tuple("/".join(end) for end in ends)
        along = (key[0], key[2]) if graph_id == "forward" else (key[2], key[0])
        assert drawn == along, (graph_id, drawn, key)


@DURABLES_ROWS
@DURABLES_VIEWS
@needs_viewer
def test_every_route_between_two_occurrences_of_a_view_is_carried_by_its_edges(
    request, durables_report, view
):
    """In each builders graph of a durables trellis view, the edges between
    two occurrences carry exactly the routes of the connection report whose
    two occurrences the view holds."""
    routes = route_keys(durables_report)
    collection = request.getfixturevalue(view)
    joins = joining_edges(collection)
    for graph in collection.graphs:
        held = {ns for ns in graph.groupNodeAttributes if ns.count("/") == 1}
        carried = {
            (record["source"], record["branch"], record["destination"])
            for graph_id, record, _ in joins
            if graph_id == graph.id
        }
        assert carried == {key for key in routes if key[0] in held and key[2] in held}, graph.id


# two authored routes of the durables trellis, each by its source and its
# destination occurrence, with the record that the view's edge carries
AUTHORED_ROUTES = [
    # the pairs that the period's connector writes, to the keeper's
    # decision states at its entry perch
    pytest.param(
        "periods[2]/tenure",
        "periods[2]/keeper_cons",
        {
            "branch": "keep",
            "source": "periods[2]/tenure",
            "destination": "periods[2]/keeper_cons",
            "source_fields": ["w_kp", "h_kp", "z_kp"],
            "destination_fields": ["w_d", "h_d", "z_d"],
            "pairs": [
                {
                    "source_field": f"{name}_kp",
                    "destination_field": f"{name}_d",
                    "origin": "authored",
                    "address": "periods[2].connectors[0]",
                }
                for name in ("w", "h", "z")
            ],
            "status": "certified",
            "law": "tenure:measure:cntn:keep",
        },
        id="branch-keep-within-periods-2",
    ),
    # the pairs that the inter-period mapping writes
    pytest.param(
        "periods[2]/keeper_cons",
        "periods[1]/tenure",
        {
            "branch": None,
            "source": "periods[2]/keeper_cons",
            "destination": "periods[1]/tenure",
            "source_fields": ["a_nxt_kp", "h_nxt_kp", "z_nxt_kp"],
            "destination_fields": ["a", "h", "z"],
            "pairs": [
                {
                    "source_field": f"{name}_nxt_kp",
                    "destination_field": name,
                    "origin": "authored",
                    "address": "inter_connectors[1]",
                }
                for name in ("a", "h", "z")
            ],
            "status": "certified",
            "law": "keeper_cons:measure:cntn",
        },
        id="inter-period-mapping-from-periods-2",
    ),
]


@DURABLES_ROWS
@needs_viewer
@pytest.mark.parametrize(("source", "destination", "record"), AUTHORED_ROUTES)
def test_an_authored_route_records_its_fields_pairs_status_and_law(
    durables_life_cycle, durables_view_of_three_periods, source, destination, record
):
    """The record of an authored route of the durables trellis holds its
    branch, its two occurrences, their fields in the route's order, its pairs
    with their origin and address, its status and its joint law."""
    assert route_records(durables_view_of_three_periods)[source, destination] == record


@needs_viewer
@pytest.mark.parametrize(
    ("direction", "ports"),
    [
        pytest.param("backward", {}, id="backward"),
        pytest.param(
            "forward",
            {
                ("periods[0]/disc/GraphOutputs", "periods[0]/disc/unjoined:disc:cntn:a"): {
                    "label": "a≻",
                    "perch": "cntn",
                    "role": "state",
                    "field": "a",
                    "unjoined": "true",
                },
                ("periods[1]/port/GraphInputs", "periods[1]/port/unjoined:port:dcsn:k"): {
                    "label": "k",
                    "perch": "dcsn",
                    "role": "state",
                    "field": "k",
                    "unjoined": "true",
                },
            },
            id="forward",
        ),
    ],
)
def test_the_unjoined_ports_of_a_complete_trellis_are_the_two_ends_of_its_forward_graph(
    unjoined_view, direction, ports
):
    """With `unjoined=True`, the ports marked `unjoined` in the view of the
    complete trellis of records are those of the two state fields that no
    join reaches, `disc`'s `a` in the terminal period and `port`'s `k` in
    the earliest, in the forward graph alone, each named by its field."""
    assert unjoined_ports(unjoined_view, direction) == ports


@needs_viewer
def test_a_node_made_for_an_unjoined_port_stands_in_the_layer_of_its_occurrence(unjoined_view):
    """The node `Outputs` or `Inputs` that holds an unjoined port, made where
    the occurrence has none, stands in the occurrence's layer."""
    forward = graph_named(unjoined_view, "forward")
    assert {
        node.id: (node.label, node.namespace)
        for node in forward.nodes
        if node.id in ("periods[0]/disc/GraphOutputs", "periods[1]/port/GraphInputs")
    } == {
        "periods[0]/disc/GraphOutputs": ("Outputs", "periods[0]/disc"),
        "periods[1]/port/GraphInputs": ("Inputs", "periods[1]/port"),
    }


@needs_viewer
@pytest.mark.parametrize("direction", ["backward", "forward"])
def test_the_keyword_unjoined_changes_no_edge_of_a_trellis_view(
    two_period_trellis, unjoined_view, direction
):
    """With `unjoined=True` the edges of each graph of a trellis view, the
    measure wires among them, are those of the view without the keyword, so
    that no edge names an unjoined port."""
    assert all_edges(unjoined_view, direction) == all_edges(
        to_model_explorer(two_period_trellis), direction
    )


@needs_viewer
def test_a_trellis_with_its_connector_emptied_leaves_w_and_m_unjoined_in_each_period(tmp_path):
    """With the connector `{w: m}` emptied, each of the two periods of the
    trellis of records adds `port`'s `w` and `cons`'s `m` to the two ends of
    the trellis among its unjoined ports."""
    file = trellis_with_connector_emptied(tmp_path / "emptied")
    emptied = specify_trellis(load_trellis(file, texts_of_two_periods(file)))
    ports = unjoined_ports(to_model_explorer(emptied, unjoined=True), "forward")
    assert sorted(ports) == sorted(
        [
            ("periods[0]/disc/GraphOutputs", "periods[0]/disc/unjoined:disc:cntn:a"),
            ("periods[1]/port/GraphInputs", "periods[1]/port/unjoined:port:dcsn:k"),
        ]
        + [
            (f"periods[{h}]/port/GraphOutputs", f"periods[{h}]/port/unjoined:port:cntn:w")
            for h in range(2)
        ]
        + [
            (f"periods[{h}]/cons/GraphInputs", f"periods[{h}]/cons/unjoined:cons:dcsn:m")
            for h in range(2)
        ]
    )


@needs_viewer
def test_a_restricted_view_marks_the_unjoined_fields_of_the_whole_trellis_in_its_periods(
    emptied_trellis, emptied_view_of_two_periods
):
    """The view of periods 0 and 1 of the trellis with its connector emptied
    marks as unjoined the state fields of those periods that no join of the
    whole trellis reaches."""
    whole = unjoined_fields(emptied_trellis)
    sides = (whole["writing"], whole["reading"])
    assert sorted(field for side in sides for field in side if field[0] in (0, 1)) == [
        (0, "cons", "m"),
        (0, "disc", "a"),
        (0, "port", "w"),
        (1, "cons", "m"),
        (1, "port", "w"),
    ]
    assert sorted(port for _, port in unjoined_ports(emptied_view_of_two_periods, "forward")) == [
        "periods[0]/cons/unjoined:cons:dcsn:m",
        "periods[0]/disc/unjoined:disc:cntn:a",
        "periods[0]/port/unjoined:port:cntn:w",
        "periods[1]/cons/unjoined:cons:dcsn:m",
        "periods[1]/port/unjoined:port:cntn:w",
    ]


@needs_viewer
def test_a_field_whose_join_leaves_a_restricted_view_reads_outside(emptied_view_of_two_periods):
    """In the view of periods 0 and 1, `port`'s `k` in `periods[1]`, which
    the inter-period mapping joins to `disc`'s `a` in `periods[2]`, reads
    `outside` on the port of the `outside` node at which its measure enters
    the graph."""
    forward = graph_named(emptied_view_of_two_periods, "forward")
    assert {
        (node.id, item.id, pair.value)
        for node in forward.nodes
        if not node.namespace
        for item in node.outputsMetadata
        for pair in item.attrs
        if pair.key == "outside"
    } == {
        (
            "outside:periods[1]/port:periods[2]/disc",
            "periods[1]/port/port:measure:dcsn",
            "periods[2]/disc",
        )
    }


@needs_viewer
def test_the_pension_trellis_with_its_mapping_emptied_holds_fourteen_unjoined_ports(
    emptied_pension_view,
):
    """The forward graph of the pension trellis of two periods with its
    standing inter-period mapping emptied holds fourteen unjoined ports, the
    two ends of the trellis counted."""
    ports = unjoined_ports(emptied_pension_view, "forward")
    # The one period of `period.yml` leaves ten state fields unjoined:
    # `worker_saving`'s arrival fields `y_f_w` and `y_p_w`, `retire_choice`'s
    # four continuation fields, and `retiree_saving`'s two arrival and two
    # continuation fields. The terminal period leaves four: the arrival
    # fields of `worker_saving` and `retiree_saving`. The earliest period's
    # arrival fields, one end of the trellis, are among the ten; the terminal
    # stage, the other end, declares no continuation state.
    assert len(ports) == 1 * 10 + 4


@needs_viewer
def test_each_continuation_state_that_no_join_reads_takes_an_unjoined_port(
    emptied_pension_view,
):
    """Each of the two continuation states of `retiree_saving` takes an
    unjoined port of its own among the outputs of its occurrence's `Outputs`
    only where no join reads it, in `periods[1]` and not in the terminal
    period, whose connector joins it."""
    ports = unjoined_ports(emptied_pension_view, "forward")
    assert {
        port: marked["field"]
        for (node, port), marked in ports.items()
        if node == "periods[1]/retiree_saving/GraphOutputs"
    } == {
        "periods[1]/retiree_saving/unjoined:retiree_saving:cntn:y_f_ret": "y_f_ret",
        "periods[1]/retiree_saving/unjoined:retiree_saving:cntn:y_p_ret": "y_p_ret",
    }
    assert not [port for (node, port) in ports if node == "periods[0]/retiree_saving/GraphOutputs"]


@needs_viewer
def test_the_continuation_measure_of_a_stage_with_two_continuation_states_leaves_at_one_end_node(
    emptied_pension_view,
):
    """The continuation measure of `retiree_saving` in `periods[1]`, a stage
    with two continuation states, is the one wire of that occurrence that
    leaves the forward graph at an `end` node."""
    forward = graph_named(emptied_pension_view, "forward")
    ends = [
        node
        for node in forward.nodes
        if not node.namespace and {"key": "kind", "value": "end"} in map(asdict, node.attrs)
    ]
    assert [
        item.id
        for node in ends
        for item in node.inputsMetadata
        if item.id.startswith("periods[1]/retiree_saving/")
    ] == ["periods[1]/retiree_saving/retiree_saving:measure:cntn"]


@DURABLES_ROWS
@needs_viewer
def test_an_arrival_field_that_joins_reach_is_a_port_that_counts_its_sources(
    durables_life_cycle, field_ports_view
):
    """An arrival field that joins reach is a port `joined:<identity>` of its
    occurrence's `Inputs` that counts those joins in `sources`: two for each
    of the three arrival fields of `bequest`, from the two consumption
    stages, and of `tenure` in `periods[1]`, from the period before."""
    forward = graph_named(field_ports_view, "forward")
    assert ports_of(forward, "periods[0]/bequest/GraphInputs", "inputsMetadata") == [
        (
            f"joined:bequest:arvl:{name}",
            {"label": f"{name}≺", "perch": "arvl", "role": "state", "field": name, "sources": "2"},
        )
        for name in ("a_bq", "h_bq", "z_bq")
    ]
    assert [
        (port, attrs["sources"])
        for port, attrs in ports_of(forward, "periods[1]/tenure/GraphInputs", "inputsMetadata")
    ] == [(f"joined:tenure:arvl:{name}", "2") for name in ("a", "h", "z")]


@DURABLES_ROWS
@needs_viewer
def test_a_branching_stage_labels_each_continuation_field_by_its_branch(
    durables_life_cycle, field_ports_view
):
    """The branching stage `tenure` labels the port of each continuation
    field with the field's branch, `keep: w_kp≻`, its ports grouped by
    branch in the order of the labels."""
    forward = graph_named(field_ports_view, "forward")
    assert [
        attrs["label"]
        for _, attrs in ports_of(forward, "periods[1]/tenure/GraphOutputs", "outputsMetadata")
    ] == ["keep: w_kp≻", "keep: h_kp≻", "keep: z_kp≻", "adjust: w_adj≻", "adjust: z_adj≻"]


@DURABLES_ROWS
@needs_viewer
def test_a_continuation_field_that_joins_reach_is_a_port_labeled_by_its_field_alone(
    durables_life_cycle, field_ports_view
):
    """A continuation field of `keeper_cons`, which has no branches, that
    joins reach is a port `joined:<identity>` of its occurrence's `Outputs`
    labeled by its field alone, in the order of the fields' names."""
    forward = graph_named(field_ports_view, "forward")
    assert ports_of(forward, "periods[0]/keeper_cons/GraphOutputs", "outputsMetadata")[-3:] == [
        (
            f"joined:keeper_cons:cntn:{name}",
            {"label": f"{name}≻", "perch": "cntn", "role": "state", "field": name},
        )
        for name in ("a_nxt_kp", "h_nxt_kp", "z_nxt_kp")
    ]


@DURABLES_ROWS
@needs_viewer
def test_no_edge_names_the_port_of_a_field(durables_life_cycle, field_ports_view):
    """No edge of the forward graph enters or leaves the port of a state
    field that joins reach."""
    forward = graph_named(field_ports_view, "forward")
    assert not [
        edge
        for node in forward.nodes
        for edge in node.incomingEdges
        if "joined:" in edge.targetNodeInputId or "joined:" in edge.sourceNodeOutputId
    ]


def test_backward_a_join_pairs_each_wire_that_a_component_of_its_route_supplies(backward_join):
    """Backward, `_route_pairs` pairs each wire that a join's reader requires
    with the wire that a component of the join's route supplies, under the
    component's rule and status."""
    reads, writes = backward_join.reads, backward_join.writes
    supplied, _ = _route_pairs(
        backward_join.joins, backward_join.graphs, "backward", backward_join.selection
    )
    assert {
        reader[1]: [
            (writer[1], [(s.label, s.rule, s.status) for s in feed])
            for writer, feed in feeds.items()
        ]
        for reader, feeds in supplied.items()
    } == {
        str(reads[0].identity): [
            (str(writes[0].identity), [("a_w → a", "one wire per role", "compatible")])
        ],
        str(reads[1].identity): [
            (str(writes[1].identity), [("a_w → a", "equal name", "incompatible")])
        ],
    }


def test_backward_a_wire_that_no_component_supplies_is_left_unpaired(backward_join):
    """Backward, `_route_pairs` leaves unpaired at its join the wire whose
    component of the route supplies no wire."""
    one = backward_join.joins
    _, undetermined = _route_pairs(one, backward_join.graphs, "backward", backward_join.selection)
    ((found, unpaired),) = undetermined
    assert found is one[0] and [sort.identity.field for sort in unpaired] == ["V_h"]


def test_backward_a_value_that_two_routes_supply_from_two_writers_is_left_unpaired():
    """Backward, a value read at a continuation perch that two routes supply
    from two different writers is left unpaired at the second join."""
    value = record_of_wire("V", "value", "cntn", "a")
    keep, sell = (
        record_of_wire("V", "value", "arvl", "a"),
        record_of_wire("V", "value", "arvl", "a"),
    )
    graphs = {
        "periods[0]/early": stage_graph(reads=[value]),
        "periods[0]/keep": stage_graph(writes=[keep]),
        "periods[0]/sell": stage_graph(writes=[sell]),
    }
    selection = SimpleNamespace(
        routes=[
            certified_route(
                [field_pair("early", "a", "keep", "a")],
                [wire_component(value, keep, "value", "compatible", "one wire per role")],
            ),
            certified_route(
                [field_pair("early", "a", "sell", "a")],
                [wire_component(value, sell, "value", "compatible", "one wire per role")],
            ),
        ]
    )
    two = [view_join("early", "a", "keep", "a"), view_join("early", "a", "sell", "a")]
    _, undetermined = _route_pairs(two, graphs, "backward", selection)
    assert [(found.target, len(unpaired)) for found, unpaired in undetermined] == [
        ("periods[0]/sell", 1)
    ]


def test_forward_two_joint_laws_supply_one_arrival_measure_each_under_the_rule_joint_law():
    """Forward, the joint laws of two routes into one arrival measure both
    supply it, each under the rule `joint law`, leaving no reader
    unpaired."""
    work, retire, graphs = forward_measures()
    selection = SimpleNamespace(
        routes=[
            certified_route([field_pair("work", "a", "next", "a")], law=str(work.identity)),
            certified_route([field_pair("retire", "a", "next", "a")], law=str(retire.identity)),
        ]
    )
    joins = [view_join("work", "a", "next", "a"), view_join("retire", "a", "next", "a")]
    supplied, undetermined = _route_pairs(joins, graphs, "forward", selection)
    assert undetermined == []
    (feeds,) = supplied.values()
    assert {writer[1] for writer in feeds} == {str(work.identity), str(retire.identity)}
    assert all(s.rule == LAW_RULE for feed in feeds.values() for s in feed)


def test_forward_a_route_without_a_law_leaves_the_arrival_measure_unpaired():
    """Forward, a route that holds no joint law leaves the arrival measure of
    its join unpaired."""
    _, _, graphs = forward_measures()
    lawless = SimpleNamespace(routes=[certified_route([field_pair("work", "a", "next", "a")])])
    joins = [view_join("work", "a", "next", "a")]
    supplied, undetermined = _route_pairs(joins, graphs, "forward", lawless)
    assert supplied == {} and [sort.role for _, unpaired in undetermined for sort in unpaired] == [
        "measure"
    ]
