"""Functions that read a view of Model Explorer, the rows of a table over the
stages that fixtures give, a stage whose backward builders graph is refused, a
trellis of two periods, the mark of a test that needs the viewer, and a server
that answers every request with one text."""

import contextlib
import dataclasses
import http.server
import json
import re
import threading

import pytest
from application_files import ROOT
from stage_graphs import DIRECTIONS

from bellman.native.identity import box_identity
from bellman.stage import elaborate_stage, load_stage
from bellman.trellis import accrete

# a stage with two forward blocks and no backward block: the construction
# refuses its backward builders graph, "no backward builder", under the rule
# not-constructed, and constructs its forward builders graph
FORWARD_ONLY_STAGE = """@stage: forward_only
[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=dcsn_to_cntn, (x_d) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d
}
"""


# the mark of a test that needs the viewer, the package model_explorer of the
# extra `explore`: the test requests the fixture `model_explorer_package`, so
# that it is skipped where the viewer is not installed, before the fixtures
# that it names are built
needs_viewer = pytest.mark.usefixtures("model_explorer_package")


def attributes(item):
    """The attributes of a node or of a port, by key."""
    return {pair.key: pair.value for pair in item.attrs}


def attribute_of(item, key):
    """The value of the attribute `key` of a node, a port or an edge, None
    where it has none."""
    pairs = getattr(item, "attrs", None) or []
    return next((pair.value for pair in pairs if pair.key == key), None)


def occurrence_of(node_id):
    """The period and the key of the stage occurrence that a node of a
    trellis view stands in, `("periods[1]", "disc")`, read from the prefix of
    its id; None for a boundary node, `start:periods[5]/port/…`, which stands
    at the graph's root."""
    parts = node_id.split("/")
    return tuple(parts[:2]) if parts[0].startswith("periods[") else None


# the words by which the id of a row names the stage that a fixture gives
STAGE_WORDS = {
    "cons_methodized_without_calibration": "methodized cons",
    "cons_configured": "configured cons",
    "house_choice_methodized": "methodized house_choice",
    "keeper_cons_methodized": "methodized keeper_cons",
}


def stage_rows(*names):
    """The rows of a table over the stages that the fixtures `names` give,
    each with its id."""
    return [pytest.param(name, id=STAGE_WORDS.get(name, name)) for name in names]


def direction_rows(*names):
    """The rows `(name, direction)` of a table over both directions of the
    stages that the fixtures `names` give, each with its id."""
    return [
        pytest.param(name, direction, id=f"{STAGE_WORDS.get(name, name)} {direction}")
        for name in names
        for direction in DIRECTIONS
    ]


# the four graphs of a stage view, in the order the collection lists them:
# the two initial diagrams, then the two builders graphs
STAGE_GRAPHS = ["backward initial diagram", "forward initial diagram", "backward", "forward"]


def graph_named(collection, graph_id):
    """The graph of a collection by its id."""
    return next(graph for graph in collection.graphs if graph.id == graph_id)


def builders_graphs(collection):
    """The two builders graphs of a collection, `backward` and `forward`."""
    return [graph_named(collection, direction) for direction in DIRECTIONS]


def reached_box_identity(stage, direction, namespace, identity):
    """The identity of the box the stage's handles reach by the segments of
    a namespace, a builder and then a sub-builder, and then by the key of
    the box within the last of them."""
    handle = stage.builder.bwd if direction == "backward" else stage.builder.fwd
    for segment in namespace.split("/"):
        handle = handle[segment]
    return box_identity(handle[identity.key_within(handle.box.name)].box)


def collection_in_viewer_classes(collection):
    """A view as the viewer's own Python classes hold it: its JSON form read
    back by dacite, which leaves out the fields the viewer's page reads and
    those classes do not declare, the color of a node's label and the colors
    of a layer (the records `_NodeStyle` and `_LayerConfig` of the package's
    module `bellman.factory.model_explorer`)."""
    import dacite
    from model_explorer import graph_builder as gb

    return dacite.from_dict(gb.GraphCollection, dataclasses.asdict(collection))


def collection_as_json(collection):
    """A view's collection as its file holds it, read back as JSON."""
    return json.loads(json.dumps(dataclasses.asdict(collection)))


def layers_of(graph):
    """The namespaces of the layers the viewer draws for a graph: every
    leading part of a node's namespace, `periods[2]`, `periods[2]/cons` and
    `periods[2]/cons/policy` for a node in `periods[2]/cons/policy`."""
    return {
        "/".join(parts[:count])
        for parts in (node.namespace.split("/") for node in graph.nodes if node.namespace)
        for count in range(1, len(parts) + 1)
    }


def applied_layer_style(configs, namespace):
    """The layout and the fill, border and label colors the viewer's page
    gives the layer `namespace` from a graph's layer configurations
    `configs`: the layout of the first configuration whose pattern it finds
    in the namespace (`RegExp.test`), and each color from the first such
    configuration that sets that color; None for what none gives."""
    found = [config for config in configs if re.search(config.namespaceRegex, namespace)]
    applied = [found[0].layoutDirection if found else None]
    for color in ("backgroundColor", "borderColor", "textColor"):
        given = [getattr(config, color) for config in found if getattr(config, color) is not None]
        applied.append(given[0] if given else None)
    return tuple(applied)


@contextlib.contextmanager
def answering_server(text, status=200):
    """A standard-library server on a free port of this machine that answers
    every request with `status` and `text`, run in a daemon thread; yields
    its port. No viewer is needed."""

    class Handler(http.server.BaseHTTPRequestHandler):
        """A handler that answers every request alike."""

        def do_GET(self):
            self.send_response(status)
            self.end_headers()
            self.wfile.write(text.encode("utf-8"))

        def log_message(self, *args):
            """Nothing is logged, so the test prints nothing."""

    server = http.server.HTTPServer(("localhost", 0), Handler)
    # the server asks every twentieth of a second whether it is to stop
    threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
    ).start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


def two_period_lesson_trellis(cons, port):
    """The trellis of two periods of the lesson on periods and trellises, with
    the stages port, cons and disc in each,
    the arrival `m` joined to `m_next` within a period and the saving `a` to
    `k` between the periods."""
    disc = elaborate_stage(
        load_stage(str(ROOT / "applications/portfolio-choice/declaration/stages/disc/disc.bl"))
    )
    period = {
        "stages": {"port": port, "cons": cons, "disc": disc},
        "connectors": [{"m_next": "m"}],
    }
    return accrete(accrete({"periods": [], "inter_connectors": []}, period), period, {"a": "k"})
