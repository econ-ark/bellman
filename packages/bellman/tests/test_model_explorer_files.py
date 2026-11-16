"""The files of the view of a stage or a trellis in Model Explorer, Google's
viewer of large graphs: the two files that `write_model_explorer` and
`explore` write, the viewer's server that `serve` uses or starts, and the
stage views that an export keeps in memory and in the user's cache folder."""

import contextlib
import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from dataclasses import asdict
from importlib import metadata
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote, unquote

import pytest
from application_files import ROOT
from model_explorer_views import (
    STAGE_GRAPHS,
    answering_server,
    attributes,
    collection_as_json,
    collection_in_viewer_classes,
    graph_named,
    needs_viewer,
)
from trellises import declarations_copy

import bellman.stage
import bellman.trellis

# The package's module of the view in Model Explorer, read for the functions
# and settings that no namespace exports, `serve` among them. The viewer
# itself is another package, `model_explorer`, of the extra `explore`.
from bellman.factory import model_explorer
from bellman.stage import (
    elaborate_stage,
    explore,
    load_stage,
    perch_overlays,
    to_model_explorer,
    write_model_explorer,
)
from bellman.trellis import load_trellis, specify_trellis

# A stage view is the graph of one direction of one stage version, which the
# view of a trellis places at each occurrence of that version. An export
# keeps each stage view in memory, in `_VIEW_CACHE`, and between processes
# as one file of the folder of the views under the user's cache folder.


def released_port():
    """A port of this machine just released, at which no server listens."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("localhost", 0))
        return probe.getsockname()[1]


@contextlib.contextmanager
def listening_without_answering():
    """A socket of this machine that listens at a free port and answers no
    request; yields its port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind(("localhost", 0))
        busy.listen()
        yield busy.getsockname()[1]


def configuration_stub():
    """A stand-in for the viewer's module `config`, whose configuration adds
    a graph file and writes an empty configuration into the address."""
    config = SimpleNamespace(
        add_model_from_path=lambda path: None,
        to_url_param_value=lambda: quote("{}"),
    )
    return SimpleNamespace(ModelExplorerConfig=lambda: config)


def replace_the_viewers_server(monkeypatch, viewer_config):
    """The viewer's function that runs its server replaced by one that
    records, for each call, whether its thread is a daemon and its keyword
    arguments, and starts nothing; `viewer_config` stands for the viewer's
    module `config`. Answers the list of the records and an event that each
    call sets."""
    started, called = [], threading.Event()

    def visualize_from_config(**kwargs):
        started.append((threading.current_thread().daemon, kwargs))
        called.set()

    apis = SimpleNamespace(visualize_from_config=visualize_from_config)
    monkeypatch.setattr(model_explorer, "_viewer_server", lambda: (apis, viewer_config))
    return SimpleNamespace(started=started, called=called)


def address_data(url):
    """The configuration and the state of the page that an address carries
    under its query parameter `data`, decoded."""
    return json.loads(unquote(url.partition("?data=")[2]))


@pytest.fixture
def small_graph_file(tmp_path):
    """A graph file of one collection, `cons`, with the graphs `backward`
    and `forward`, which `serve` reads for the graph and the label that the
    page shows."""
    path = tmp_path / "cons.graph.json"
    graphs = [{"id": "backward", "nodes": []}, {"id": "forward", "nodes": []}]
    path.write_text(json.dumps({"label": "cons", "graphs": graphs}), encoding="utf-8")
    return path


@pytest.fixture
def server_starts(monkeypatch):
    """The starts of the viewer's server recorded and nothing started, with
    the stand-in for the viewer's configuration (`configuration_stub`)."""
    return replace_the_viewers_server(monkeypatch, configuration_stub())


@pytest.fixture(scope="module")
def cons_files(cons, tmp_path_factory):
    """The two files of the view of `cons`, written once into a folder of
    their own: the graph file and the file of the perch overlays."""
    return write_model_explorer(cons, tmp_path_factory.mktemp("cons-view"))


@pytest.fixture(scope="module")
def port_files(port, tmp_path_factory):
    """The two files of the view of the stage `port`, the portfolio stage of
    the portfolio-choice application, written once into a folder of their
    own: the graph file and the file of the perch overlays."""
    return write_model_explorer(port, tmp_path_factory.mktemp("port-view"))


@pytest.fixture
def no_views_in_memory():
    """`_VIEW_CACHE`, the stage views kept in memory, emptied before the test
    and after it, so that an export of the test computes each stage view or
    reads it from the cache folder, and the next test reads no view that it
    kept."""
    model_explorer._VIEW_CACHE.clear()
    yield
    model_explorer._VIEW_CACHE.clear()


@pytest.fixture
def folder_name_restored():
    """The name of the folder of the views that the process holds, cleared
    after the test, so that the next test reads the name that the installed
    files and versions give."""
    yield
    model_explorer._source_version.cache_clear()


@pytest.fixture
def computed_views(monkeypatch):
    """The directions of the stage views that the test computes, in their
    order: `_graph`, which computes a stage view, records each call."""
    directions = []
    original_graph = model_explorer._graph

    def recorded(graph_builder, stage, direction):
        directions.append(direction)
        return original_graph(graph_builder, stage, direction)

    monkeypatch.setattr(model_explorer, "_graph", recorded)
    return directions


# The files of a view


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda stage: to_model_explorer(stage), id="to-model-explorer"),
        # `serve` is refused before it reads the graph file that it is given
        pytest.param(lambda stage: model_explorer.serve("cons.graph.json"), id="serve"),
    ],
)
def test_without_the_viewer_each_function_that_needs_it_names_the_command_that_installs_it(
    call, cons, monkeypatch
):
    """Without the viewer, a function of the module that needs it raises an
    ImportError whose sentence names the command `pip install` and the
    extra `explore`."""
    # An entry of None in `sys.modules` makes the import of that name fail,
    # whether or not the viewer is installed. Each module that the view
    # imports is hidden, since a module that an earlier test imported is
    # found under its own name.
    for name in (
        "model_explorer",
        "model_explorer.graph_builder",
        "model_explorer.apis",
        "model_explorer.config",
    ):
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(ImportError) as refusal:
        call(cons)
    assert [
        phrase for phrase in ("pip install", "explore") if phrase not in str(refusal.value)
    ] == []


@needs_viewer
@pytest.mark.parametrize(
    "stage, names",
    [
        pytest.param("cons", ("cons.graph.json", "cons.edge-overlays.json"), id="cons"),
        pytest.param(
            "cons_methodized_without_calibration",
            ("cons-methodized.graph.json", "cons-methodized.edge-overlays.json"),
            id="cons-methodized",
        ),
    ],
)
def test_write_model_explorer_names_its_two_files_by_the_label_of_the_view(
    stage, names, request, tmp_path
):
    """`write_model_explorer` answers the paths of the graph file and of the
    file of the perch overlays, named by the label of the view with each
    space written as a hyphen."""
    graph, overlays = names
    assert write_model_explorer(request.getfixturevalue(stage), tmp_path) == (
        tmp_path / graph,
        tmp_path / overlays,
    )


@needs_viewer
def test_the_folder_of_a_written_view_holds_its_two_files_alone(cons_files):
    """The folder that `write_model_explorer` writes into holds the graph
    file and the file of the perch overlays alone."""
    assert sorted(path.name for path in cons_files[0].parent.iterdir()) == [
        "cons.edge-overlays.json",
        "cons.graph.json",
    ]


@needs_viewer
def test_the_graph_file_holds_the_collection_that_to_model_explorer_answers(cons, cons_files):
    """The graph file holds, as JSON, the collection that `to_model_explorer`
    answers, with the fields that the viewer's page reads and the viewer's
    classes do not declare."""
    graph, _ = cons_files
    assert json.loads(graph.read_text(encoding="utf-8")) == collection_as_json(
        to_model_explorer(cons)
    )


@needs_viewer
def test_the_graph_file_loads_into_the_viewers_classes_as_the_collection_of_four_graphs(
    cons, cons_files
):
    """The graph file loads through dacite into the viewer's class
    `GraphCollection` as the collection of the four graphs of `cons`, with
    the fields that the viewer's classes do not declare left out."""
    # the viewer and its dependency dacite are imported here, since the file
    # is collected where they are not installed
    import dacite
    from model_explorer import graph_builder

    graph, _ = cons_files
    collection = dacite.from_dict(
        graph_builder.GraphCollection, json.loads(graph.read_text(encoding="utf-8"))
    )
    assert [g.id for g in collection.graphs] == STAGE_GRAPHS
    assert collection == collection_in_viewer_classes(to_model_explorer(cons))


@needs_viewer
@pytest.mark.parametrize(
    "files, index",
    [
        pytest.param("cons_files", 0, id="graph-file-of-the-consumption-stage"),
        # the perch overlays of the consumption stage `cons` hold no
        # mathematical letter, and those of the portfolio stage `port` do
        pytest.param("port_files", 1, id="overlays-file-of-the-portfolio-stage"),
    ],
)
def test_each_file_of_a_view_holds_ascii_alone_and_reads_alike_under_a_windows_code_page(
    files, index, request
):
    """Each file of a view holds ASCII alone, its mathematical letters
    written as escapes, so that the viewer's server, which opens a file in
    the system's default encoding, reads it alike under a Windows code
    page."""
    path = request.getfixturevalue(files)[index]
    assert path.read_bytes().isascii(), path.name
    assert json.loads(path.read_text(encoding="cp1252")) == json.loads(
        path.read_text(encoding="utf-8")
    )


@needs_viewer
def test_the_overlays_file_loads_into_the_viewers_class_as_the_three_perch_overlays(
    cons, cons_files
):
    """The file of the perch overlays loads through dacite into the viewer's
    class `EdgeOverlaysData` as the overlays of the arrival, the decision
    and the continuation perch, named `perches`."""
    # imported here for the reason given in the test of the graph file
    import dacite
    from model_explorer import graph_builder

    _, path = cons_files
    overlays = json.loads(path.read_text(encoding="utf-8"))
    assert [o["name"] for o in overlays["overlays"]] == ["arrival", "decision", "continuation"]
    assert all(overlay["edges"] for overlay in overlays["overlays"])
    assert dacite.from_dict(graph_builder.EdgeOverlaysData, overlays) == (
        graph_builder.EdgeOverlaysData(name="perches", overlays=perch_overlays(cons))
    )


# The view opened by explore


@pytest.fixture
def explore_records(monkeypatch):
    """`serve` and the browser replaced by records, so that the test starts
    no server and opens no browser: answers the calls of `serve`, which
    answers `http://localhost:0/`, the addresses that the browser is given,
    each with whether the thread that gives it is a daemon, and an event
    that the browser sets."""
    serve_calls, browser_calls, browser_opened = [], [], threading.Event()
    monkeypatch.setattr(
        model_explorer,
        "serve",
        lambda *args, **kwargs: serve_calls.append((args, kwargs)) or "http://localhost:0/",
    )

    def open_page(url, *args, **kwargs):
        browser_calls.append((url, threading.current_thread().daemon))
        browser_opened.set()

    monkeypatch.setattr(model_explorer.webbrowser, "open", open_page)
    return SimpleNamespace(
        serve_calls=serve_calls, browser_calls=browser_calls, browser_opened=browser_opened
    )


@pytest.fixture
def explorations(cons, tmp_path, explore_records, capsys):
    """`explore` of `cons` called twice into one folder under the records of
    `explore_records`, first without the browser and then with it: answers
    those records with the paths and the address of the second call and the
    lines that the two calls print."""
    explore(cons, folder=tmp_path, open_browser=False)
    paths, url = explore(cons, folder=tmp_path, open_browser=True)
    return SimpleNamespace(
        paths=paths,
        url=url,
        printed=capsys.readouterr().out.splitlines(),
        serve_calls=explore_records.serve_calls,
        browser_calls=explore_records.browser_calls,
        browser_opened=explore_records.browser_opened,
    )


@needs_viewer
def test_explore_without_the_browser_writes_the_two_files_serves_nothing_and_answers_no_address(
    cons, tmp_path, explore_records
):
    """`explore` with `open_browser=False` writes the two files, serves
    nothing and answers the address None."""
    paths, url = explore(cons, folder=tmp_path, open_browser=False)
    assert all(p.exists() for p in paths) and explore_records.serve_calls == [] and url is None


@needs_viewer
def test_explore_answers_the_address_that_serve_answers(explorations):
    """`explore` with the browser answers the address that `serve` answers,
    here that of the stand-in for `serve`."""
    assert explorations.url == "http://localhost:0/"


@needs_viewer
def test_explore_serves_the_graph_file_at_port_8080_on_the_backward_graph_with_its_builders_open(
    explorations,
):
    """Of the two calls of `explore`, one serves the graph file alone, at
    the viewer's default port, 8080, on the graph `backward` with the layers
    of its three builders opened."""
    ((args, kwargs),) = explorations.serve_calls
    assert args == explorations.paths[:1] and (kwargs["port"], kwargs["graph_id"]) == (
        8080,
        "backward",
    )
    assert set(kwargs["layers"]) == {"cntn_to_dcsn", "dcsn_to_arvl", "policy"}


@needs_viewer
def test_explore_prints_the_address_and_how_to_see_the_labels_only_where_it_opens_the_browser(
    explorations,
):
    """Of the two calls of `explore`, the call with the browser prints two
    sentences, the address of the view and how to see the mathematical
    labels, and the call without the browser prints nothing."""
    assert explorations.printed == [
        "The view is at http://localhost:0/.",
        model_explorer.SVG_TEXT_SENTENCE,
    ]


@needs_viewer
def test_explore_opens_the_browser_at_the_address_from_a_daemon_thread_only_where_asked(
    explorations,
):
    """Of the two calls of `explore`, only the call with the browser opens
    the browser, once, at the address that it answers and from a daemon
    thread, within five seconds."""
    assert explorations.browser_opened.wait(5) and explorations.browser_calls == [
        (explorations.url, True)
    ]


# The viewer's server


@pytest.mark.parametrize(
    "listening, refusal",
    [
        # no refusal: the port is used, and `serve` answers an address at it
        pytest.param(
            lambda: answering_server(model_explorer.VIEWER_HEALTH),
            None,
            id="the-viewers-server-answers",
        ),
        # this row also reads the argument `port=` that the sentence names
        pytest.param(
            lambda: answering_server("another program"),
            "port {port}; .* port=",
            id="another-program-answers",
        ),
        pytest.param(
            lambda: answering_server("", status=404),
            "port {port}",
            id="another-program-answers-with-an-error",
        ),
        pytest.param(
            listening_without_answering, "port {port}", id="another-program-answers-nothing"
        ),
    ],
)
def test_serve_starts_no_server_where_one_listens_and_refuses_the_port_unless_it_is_the_viewers(
    listening, refusal, small_graph_file, server_starts
):
    """At a port where a server listens, `serve` starts no server: where the
    viewer's server answers, whichever process started it, it answers an
    address at the port, and where another program listens, it refuses the
    port in a sentence that names it."""
    with listening() as port:
        if refusal is None:
            url = model_explorer.serve(small_graph_file, port=port)
            assert url.startswith(f"http://localhost:{port}/?data=")
        else:
            with pytest.raises(ValueError, match=refusal.format(port=port)):
                model_explorer.serve(small_graph_file, port=port)
    assert server_starts.started == []


def test_where_nothing_listens_serve_starts_the_server_in_a_daemon_thread_that_opens_no_browser(
    small_graph_file, server_starts, monkeypatch
):
    """Where nothing listens at the port, `serve` starts the viewer's server
    on this machine at that port in a daemon thread, and the server opens no
    browser."""
    # the server answers at once, so that the call does not wait
    monkeypatch.setattr(model_explorer, "_wait_until_answered", lambda page: True)
    port = released_port()
    model_explorer.serve(small_graph_file, port=port)
    # the thread is given five seconds to call the server's stand-in
    assert server_starts.called.wait(5)
    ((daemon, kwargs),) = server_starts.started
    assert daemon and (kwargs["host"], kwargs["port"], kwargs["no_open_in_browser"]) == (
        "localhost",
        port,
        True,
    )


@needs_viewer
def test_the_server_started_is_given_the_configuration_that_the_address_carries(
    small_graph_file, monkeypatch
):
    """Where nothing listens at the port, the server that `serve` starts is
    given the viewer's configuration that the address at that port carries
    under `data`, here a server that has not answered within the wait."""
    # the viewer's module `config`, which the viewer's function `config`
    # hides from `from model_explorer import config`
    viewer_config = importlib.import_module("model_explorer.config")
    server = replace_the_viewers_server(monkeypatch, viewer_config)
    # the stand-in starts no server, so the call waits the whole time
    monkeypatch.setattr(model_explorer, "SERVER_WAIT_SECONDS", 0.2)
    port = released_port()
    url = model_explorer.serve(small_graph_file, port=port)
    # the thread is given five seconds to call the server's stand-in before
    # its record is read
    server.called.wait(5)
    ((_, kwargs),) = server.started
    written = json.loads(unquote(kwargs["config"].to_url_param_value()))
    decoded = address_data(url)
    assert {key: decoded[key] for key in written} == written
    assert url.startswith(f"http://localhost:{port}/?data=")


@pytest.fixture(scope="module")
def methodized_addresses(cons_methodized_without_calibration, tmp_path_factory):
    """The graph file of `cons` methodized and two addresses that `serve`
    answers for it at the port of a server that answers as the viewer's
    does: one with the layers `cntn_to_dcsn` and `policy` opened, and one of
    the graph `forward`."""
    # a version within which a method is bound, whose label has two words
    graph, _ = write_model_explorer(
        cons_methodized_without_calibration, tmp_path_factory.mktemp("methodized")
    )
    with answering_server(model_explorer.VIEWER_HEALTH) as port:
        url = model_explorer.serve(graph, port=port, layers=("cntn_to_dcsn", "policy"))
        forward = model_explorer.serve(graph, port=port, graph_id="forward")
    return SimpleNamespace(graph=graph, port=port, url=url, forward=forward)


@needs_viewer
def test_the_address_is_the_page_at_the_port_with_a_configuration_naming_the_graph_file_alone(
    methodized_addresses,
):
    """The address is the page of the viewer's server at the port, followed
    by the viewer's configuration and the state of the page, the
    configuration naming the graph file by its path and no other file."""
    page, _, _ = methodized_addresses.url.partition("?data=")
    assert page == f"http://localhost:{methodized_addresses.port}/"
    decoded = address_data(methodized_addresses.url)
    assert set(decoded) == {"models", "uiState"}
    assert decoded["models"] == [{"url": os.path.abspath(methodized_addresses.graph)}]


@needs_viewer
def test_the_address_shows_the_backward_graph_of_the_file_with_the_layers_given_opened(
    methodized_addresses,
):
    """The state of the page that the address carries shows the graph
    `backward` under the label of the file's collection, with the layers
    given to `serve` opened and no layer selected."""
    assert address_data(methodized_addresses.url)["uiState"] == {
        "paneStates": [
            {
                "deepestExpandedGroupNodeIds": ["cntn_to_dcsn___group___", "policy___group___"],
                "selectedNodeId": "",
                "selectedGraphId": "backward",
                "selectedCollectionLabel": "cons methodized",
                "widthFraction": 1,
                "flattenLayers": False,
            }
        ]
    }


@needs_viewer
def test_an_address_of_the_graph_forward_shows_that_graph_with_no_layer_opened(
    methodized_addresses,
):
    """The address that `serve` answers for the graph `forward`, with no
    layers given, shows that graph with no layer opened."""
    (pane,) = address_data(methodized_addresses.forward)["uiState"]["paneStates"]
    assert pane["selectedGraphId"] == "forward" and pane["deepestExpandedGroupNodeIds"] == []


# The wait for a server just started


@pytest.mark.parametrize(
    "status", [pytest.param(200, id="status-200"), pytest.param(500, id="status-500-an-error")]
)
def test_the_wait_for_the_server_ends_answered_at_an_answer_of_any_status(status):
    """The wait for a server just started ends as answered at its first
    answer, an answer with a status of error among them."""
    # a standard-library server on a free port; no viewer is needed
    with answering_server("", status=status) as port:
        assert model_explorer._wait_until_answered(f"http://localhost:{port}/")


def test_where_nothing_listens_the_wait_ends_unanswered_once_its_time_has_passed(monkeypatch):
    """Where nothing listens, the wait for the server ends unanswered once
    its time of 0.3 seconds has passed and before 1.5 seconds."""
    monkeypatch.setattr(model_explorer, "SERVER_WAIT_SECONDS", 0.3)
    port = released_port()
    began = time.monotonic()
    assert not model_explorer._wait_until_answered(f"http://localhost:{port}/")
    # the bound 1.5 is the wait of 0.3 seconds, at most one second for the
    # last request, and a margin of 0.2 seconds
    assert 0.3 <= time.monotonic() - began < 1.5


@pytest.mark.usefixtures("server_starts")
def test_serve_answers_the_address_where_the_server_has_not_answered_within_the_wait(
    small_graph_file, monkeypatch
):
    """Where the server started has not answered within the wait, `serve`
    still answers the address, since a slow start may still succeed."""
    monkeypatch.setattr(model_explorer, "_wait_until_answered", lambda page: False)
    port = released_port()
    url = model_explorer.serve(small_graph_file, port=port)
    assert url.startswith(f"http://localhost:{port}/?data=")


@pytest.mark.usefixtures("server_starts")
def test_serve_prints_one_sentence_naming_the_port_only_where_the_server_has_not_answered(
    small_graph_file, monkeypatch, capsys
):
    """`serve` prints one sentence that names the port where the server
    started has not answered within the wait, and nothing where it has."""
    monkeypatch.setattr(model_explorer, "_wait_until_answered", lambda page: False)
    port = released_port()
    model_explorer.serve(small_graph_file, port=port)
    printed = capsys.readouterr().out
    assert printed.count("\n") == 1 and f"port {port}" in printed
    monkeypatch.setattr(model_explorer, "_wait_until_answered", lambda page: True)
    model_explorer.serve(small_graph_file, port=released_port())
    assert capsys.readouterr().out == ""


# The default folder and the namespaces


def test_the_default_folder_stands_beside_the_file_that_the_provenance_names(
    tmp_path, monkeypatch
):
    """Where the provenance of a stage names a file that exists, the folder
    that a view is written to by default is `model-explorer` beside it."""
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "stages" / "cons.bl"
    source.parent.mkdir()
    shutil.copyfile(ROOT / "applications/portfolio-choice/declaration/stages/cons/cons.bl", source)
    stage = elaborate_stage(load_stage(str(source)))
    assert model_explorer._default_folder(stage) == source.parent / "model-explorer"


def test_the_default_folder_is_in_the_working_directory_where_the_provenance_names_no_file(
    cons, tmp_path, monkeypatch
):
    """Where the provenance of a stage names no file that exists, the folder
    that a view is written to by default is `model-explorer` in the working
    directory."""
    monkeypatch.chdir(tmp_path)
    # the provenance of `cons` names its file by a path relative to the root
    # of the repository,
    # `applications/portfolio-choice/declaration/stages/cons/cons.bl`, which
    # names no file from this working directory
    assert model_explorer._default_folder(cons) == Path("model-explorer")


NAMESPACES = [
    pytest.param(bellman.stage, id="bellman.stage"),
    pytest.param(bellman.trellis, id="bellman.trellis"),
]


@pytest.mark.parametrize("namespace", NAMESPACES)
def test_a_namespace_exports_the_modules_explore_and_write_model_explorer(namespace):
    """The namespaces of a stage and of a trellis export the module's
    `explore` and `write_model_explorer` themselves."""
    assert (namespace.explore, namespace.write_model_explorer) == (
        model_explorer.explore,
        model_explorer.write_model_explorer,
    )


@pytest.mark.parametrize("namespace", NAMESPACES)
def test_a_namespace_does_not_export_serve(namespace):
    """The namespaces of a stage and of a trellis do not export `serve`,
    which stays a function of the module that `explore` calls."""
    assert "serve" not in namespace.__all__


# The folder of the views

# `importlib.metadata.version` and `Path.read_bytes` as installed, which the
# stand-ins below call for every name and file that they do not replace
INSTALLED_VERSION = metadata.version
READ_BYTES = Path.read_bytes


def another_discopy(name):
    """The installed version of `name`, and 0.0.1 for `discopy`."""
    return "0.0.1" if name == "discopy" else INSTALLED_VERSION(name)


def no_discopy(name):
    """The installed version of `name`; `discopy` is not installed."""
    if name == "discopy":
        raise metadata.PackageNotFoundError(name)
    return INSTALLED_VERSION(name)


def unreadable(path):
    """The bytes of the file `path`; a PermissionError for the package's
    `refusals.py`."""
    if path == model_explorer._PACKAGE_FOLDER / "refusals.py":
        # the error number 13 of a permission denied, its text and the file
        raise PermissionError(13, "Permission denied", str(path))
    return READ_BYTES(path)


def undecodable(name):
    """The installed version of `name`; for `lark`, the error of a METADATA
    file that is no UTF-8."""
    if name == "lark":
        # the encoding, the bytes read, the start and the end of the byte that
        # cannot be read, and the reason
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
    return INSTALLED_VERSION(name)


def folder_name_with(monkeypatch, version):
    """The name of the folder of the views computed anew with
    `importlib.metadata.version` replaced by `version`; the name that the
    process holds is cleared after."""
    with monkeypatch.context() as patch:
        patch.setattr(metadata, "version", version)
        model_explorer._source_version.cache_clear()
        name = model_explorer._source_version()
    model_explorer._source_version.cache_clear()
    return name


@pytest.mark.usefixtures("folder_name_restored")
def test_the_name_of_the_folder_of_the_views_follows_the_installed_version_of_a_distribution(
    monkeypatch,
):
    """The name of the folder of the views follows the installed version of
    `discopy`: another version gives another name, `discopy` not installed
    gives a third name, and the installed version gives the first name
    again."""
    model_explorer._source_version.cache_clear()
    installed = model_explorer._source_version()
    another = folder_name_with(monkeypatch, another_discopy)
    absent = folder_name_with(monkeypatch, no_discopy)
    assert len({installed, another, absent}) == 3
    assert absent is not None
    assert model_explorer._source_version() == installed


# The script that a fresh process runs on a copy of the package, whose folder
# its first argument names: it imports the module, appends a comment to a
# source file of the copy, and prints three lines, the file of the module that
# it imported, the name of the folder of the views that the process holds, and
# the name that the changed files give once the held name is cleared.
SCRIPT_THAT_CHANGES_A_FILE_AFTER_THE_IMPORT = """\
import sys
from pathlib import Path

from bellman.factory import model_explorer

source = Path(sys.argv[1]) / "bellman" / "refusals.py"
source.write_text(source.read_text(encoding="utf-8") + "\\n# a comment\\n", encoding="utf-8")
print(model_explorer.__file__)
print(model_explorer._source_version())
model_explorer._source_version.cache_clear()
print(model_explorer._source_version())
"""


def test_the_name_of_the_folder_of_the_views_is_computed_when_the_module_is_imported(tmp_path):
    """A fresh process holds the name of the folder of the views that the
    package's files gave when it imported the module: a source file changed
    after the import gives another name only once the held name is
    cleared."""
    package = tmp_path / "package"
    shutil.copytree(
        ROOT / "packages/bellman/bellman",
        package / "bellman",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copyfile(ROOT / "packages/bellman/pyproject.toml", package / "pyproject.toml")
    # the folder that a process starts in stands first on its path, so the
    # child starts in the test's own folder and not in the one pytest runs
    # from
    run = subprocess.run(
        [sys.executable, "-c", SCRIPT_THAT_CHANGES_A_FILE_AFTER_THE_IMPORT, str(package)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(package), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    imported, held, changed = run.stdout.splitlines()
    # the process ran the module of the copy
    assert Path(imported).is_relative_to(package)
    assert held != changed


@pytest.mark.usefixtures("folder_name_restored")
@pytest.mark.parametrize(
    "owner, name, stand_in",
    [
        pytest.param(Path, "read_bytes", unreadable, id="a-source-file-that-cannot-be-read"),
        pytest.param(metadata, "version", undecodable, id="metadata-that-is-no-utf-8"),
    ],
)
def test_the_name_of_the_folder_of_the_views_is_none_where_a_file_it_reads_cannot_be_read(
    owner, name, stand_in, monkeypatch
):
    """The name of the folder of the views is None, and its computation
    raises nothing, where a source file of the package or the metadata of a
    distribution cannot be read."""
    model_explorer._source_version.cache_clear()
    with monkeypatch.context() as patch:
        patch.setattr(owner, name, stand_in)
        assert model_explorer._source_version() is None


@needs_viewer
@pytest.mark.usefixtures("folder_name_restored", "no_views_in_memory")
def test_with_no_name_for_the_folder_of_the_views_an_export_keeps_no_view_in_the_cache_folder(
    one_period_cons_trellis, computed_views, monkeypatch, tmp_path
):
    """Where the name of the folder of the views cannot be computed, an
    export of a trellis computes its two stage views and reads or writes no
    file under the cache folder."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    model_explorer._source_version.cache_clear()
    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", unreadable)
        assert model_explorer._source_version() is None
    assert graph_named(to_model_explorer(one_period_cons_trellis), "backward").nodes
    assert sorted(computed_views) == ["backward", "forward"]
    assert list(tmp_path.iterdir()) == []


# The stage views kept in memory and in the cache folder

# `SHORT_LABELS` is a switch of the module. Off, its default, a result wire is
# labeled by the expression that it denotes; on, a result wire that carries a
# function is labeled by that function at its coordinates.


@pytest.fixture
def draw_trellis(one_period_cons_trellis, computed_views, monkeypatch):
    """A function that draws the trellis of `cons` with the switch
    `SHORT_LABELS` at the value given, the switch restored after, and
    answers the label of the value port of the first aggregation of the
    backward graph and the number of stage views that the drawing
    computed."""

    def draw(short):
        computed_views.clear()
        with monkeypatch.context() as patch:
            patch.setattr(model_explorer, "SHORT_LABELS", short)
            backward = graph_named(to_model_explorer(one_period_cons_trellis), "backward")
        labels = {
            port.id: attributes(port)["label"]
            for node in backward.nodes
            for port in node.outputsMetadata
        }
        return labels["periods[0]/consumption/cntn_to_dcsn:Aggregation:V:result"], len(
            computed_views
        )

    return draw


@needs_viewer
@pytest.mark.usefixtures("no_views_in_memory")
def test_a_drawing_with_the_short_labels_computes_its_own_stage_views_while_the_others_are_kept(
    draw_trellis, monkeypatch, tmp_path
):
    """A drawing of the trellis with the switch `SHORT_LABELS` on computes
    its own two stage views, while the two that a drawing with the switch
    off computed are kept, as the next drawing with it off computes none."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    # the label with the switch off and with it on
    written_out, short = "m_d ↦ 𝑢(𝑐(m_d)) + 𝑉≻(𝑔(m_d, 𝑐(m_d)))", "𝑉(m_d)"
    assert draw_trellis(False) == (written_out, 2)
    assert draw_trellis(True) == (short, 2)
    assert draw_trellis(False) == (written_out, 0)
    assert model_explorer.SHORT_LABELS is False


@needs_viewer
@pytest.mark.usefixtures("no_views_in_memory")
def test_with_no_view_in_memory_each_value_of_short_labels_reads_its_own_cache_entries(
    draw_trellis, monkeypatch, tmp_path
):
    """With no stage view in memory, each value of the switch `SHORT_LABELS`
    reads its own two entries of the cache folder, which holds four."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    # the label with the switch off and with it on
    written_out, short = "m_d ↦ 𝑢(𝑐(m_d)) + 𝑉≻(𝑔(m_d, 𝑐(m_d)))", "𝑉(m_d)"
    # the two drawings that compute the four stage views and write them
    draw_trellis(False)
    draw_trellis(True)
    model_explorer._VIEW_CACHE.clear()
    assert draw_trellis(True) == (short, 0)
    assert draw_trellis(False) == (written_out, 0)
    assert len(list(tmp_path.rglob("*.json"))) == 4
    assert model_explorer.SHORT_LABELS is False


# A view with the keyword unjoined


@pytest.fixture(scope="module")
def port_cons_vfi_trellis(tmp_path_factory):
    """The trellis that the file
    `applications/cons-port/declaration/trellis.port-cons-vfi.yml` writes,
    six periods of the portfolio stage `port`, the consumption stage `cons`
    and the stage `disc`, read from a copy of its declaration folders and
    specified."""
    _, file = declarations_copy(tmp_path_factory.mktemp("cons-port"))
    return specify_trellis(load_trellis(file))


@pytest.fixture
def views_without_unjoined(port_cons_vfi_trellis):
    """Two views of `port_cons_vfi_trellis` made in turn, with no stage view
    in memory before the first, so that making them reads or writes the
    entries of the cache folder: the view without the keyword `unjoined`,
    and the view with `unjoined=False`."""
    model_explorer._VIEW_CACHE.clear()
    plain = to_model_explorer(port_cons_vfi_trellis)
    off = to_model_explorer(port_cons_vfi_trellis, unjoined=False)
    return SimpleNamespace(plain=plain, off=off)


@needs_viewer
def test_to_model_explorer_with_unjoined_false_answers_the_view_without_the_keyword(
    views_without_unjoined,
):
    """With `unjoined=False`, `to_model_explorer` answers the view that it
    answers without the keyword."""
    assert views_without_unjoined.off == views_without_unjoined.plain


@needs_viewer
def test_a_view_with_unjoined_fields_changes_no_stage_view_kept_in_memory(
    port_cons_vfi_trellis, views_without_unjoined
):
    """A view with `unjoined=True` leaves each stage view kept in memory as
    it was, with no node that holds the text `unjoined`, since which fields
    no join reaches is a fact of the trellis and not of the stage version
    that keys a stage view."""
    kept = {key: asdict(view) for key, view in model_explorer._VIEW_CACHE.items()}
    assert kept
    assert to_model_explorer(port_cons_vfi_trellis, unjoined=True) != views_without_unjoined.plain
    assert {key: asdict(view) for key, view in model_explorer._VIEW_CACHE.items()} == kept
    assert not [
        node.id
        for view in model_explorer._VIEW_CACHE.values()
        for node in view.nodes
        if "unjoined" in json.dumps(asdict(node), ensure_ascii=False)
    ]


@needs_viewer
def test_a_view_with_unjoined_fields_writes_no_unjoined_port_into_the_cache_folder(
    port_cons_vfi_trellis, views_without_unjoined, cache_folder
):
    """A view with `unjoined=True` writes the text `unjoined` into no file of
    the cache folder, since which fields no join reaches is a fact of the
    trellis and not of the stage version that keys a stage view."""
    assert to_model_explorer(port_cons_vfi_trellis, unjoined=True) != views_without_unjoined.plain
    files = [path for path in Path(cache_folder).rglob("*") if path.is_file()]
    assert files
    assert not [path for path in files if "unjoined" in path.read_text(encoding="utf-8")]
