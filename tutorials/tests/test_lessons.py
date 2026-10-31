"""The lessons keep the collection's rules, and the record tutorials/lessons.json
describes them as they are today.

Each lesson opens with its title and its list of the files it reads, imports
only in its first code cell, and holds in each code cell no definition and no
comment. Each lesson has an entry, written by tutorials/tools/execute_lessons.py
when it executed the lesson, whose digests of the notebook and of the files the
lesson executed equal the digests of those files now. A lesson whose notebook
or input has changed since then fails here until it is executed again with
``execute_lessons.py --record <name>``.

The set-up module's function ``explore`` is tested with a stand-in for the
package's module ``bellman.factory.model_explorer``, whose
``write_model_explorer`` writes a small view, whose ``layers_to_open`` is the
package's own function, imported from the package's module before the stand-in
replaces that module in ``sys.modules``, and whose ``serve`` records its
arguments and starts no server, and with a stand-in for the viewer's presence,
so that these tests need no viewer. With ``BELLMAN_LESSONS_HEADLESS`` set, as
the tool that records the lessons sets it, ``explore`` prints the paths of the
two files it writes and serves nothing; without it, the graph named is served
at the port named, the package's port 8080 by default, with its builders or its
stage occurrences opened, and a display is returned that names the view and
its graph, links the page's address and shows the page in a frame. Where
the viewer is not installed, ``explore`` prints the command that installs it
and returns None; where another program holds the port, it prints the sentence
of the package's refusal and returns None; and the set-up module imports the
package's module only when ``explore`` is called. One test runs ``explore``
without the variable on the package's own module, with the viewer installed,
for the stage ``cons`` and for the trellis of lesson 05, its ``serve`` alone
replaced by a record of its arguments.
"""
import ast
from collections import namedtuple
from collections.abc import Mapping
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import sys
import tokenize
import types

from html.parser import HTMLParser

from IPython.display import HTML
import nbformat
import pytest

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'execute_lessons.py'
_spec = importlib.util.spec_from_file_location('execute_lessons', TOOL)
execute_lessons = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(execute_lessons)

ROOT = execute_lessons.ROOT
LESSONS = execute_lessons.lessons()
RECORD = execute_lessons.read_record()
NAMES = [execute_lessons.lesson_name(path) for path in LESSONS]
AGAIN = 'execute it again with tutorials/tools/execute_lessons.py --record '
DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def nodes(source):
    """Every node of the syntax tree of a code cell's source."""
    return list(ast.walk(ast.parse(source)))


def comments(source):
    """The comments of a code cell's source."""
    return [token.string for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type == tokenize.COMMENT]


@pytest.mark.parametrize('path', LESSONS, ids=NAMES)
def test_each_lesson_opens_with_its_title_and_files_and_its_code_cells_keep_the_rules(path):
    """The title cell's first line is a heading without a colon; the second
    markdown cell lists at least one path, each naming a file of the
    repository, among them every file a code cell names; the first code cell
    begins with `import checkout` and is the only cell that imports; every code
    cell follows a markdown cell and holds no def, class, lambda or comment."""
    cells = nbformat.read(path, as_version=4).cells
    title = cells[0].source.splitlines()[0] if cells[0].cell_type == 'markdown' else ''
    assert title.startswith('# ') and ':' not in title, f'title cell: {title!r}'
    listed = execute_lessons.listed_files(nbformat.read(path, as_version=4))
    assert listed, 'the second markdown cell lists no path'
    assert [name for name in listed if not (ROOT / name).is_file()] == []
    code = [(index, cell) for index, cell in enumerate(cells) if cell.cell_type == 'code']
    named = {node.value for _, cell in code for node in nodes(cell.source)
             if isinstance(node, ast.Constant) and isinstance(node.value, str) and (ROOT / node.value).is_file()}
    assert sorted(named - set(listed)) == [], 'files a code cell names that the second markdown cell does not list'
    assert code and code[0][1].source.startswith('import checkout'), code[0][1].source if code else 'no code cell'
    assert [cell.id for _, cell in code[1:]
            if any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in nodes(cell.source))] == []
    assert [cell.id for index, cell in code if index == 0 or cells[index - 1].cell_type != 'markdown'] == []
    assert [cell.id for _, cell in code if any(isinstance(node, DEFINITIONS) for node in nodes(cell.source))] == []
    assert [(cell.id, comments(cell.source)) for _, cell in code if comments(cell.source)] == []


def test_the_record_holds_one_entry_for_each_lesson_and_no_other():
    assert LESSONS
    assert sorted(RECORD) == sorted(NAMES)


@pytest.mark.parametrize('path', LESSONS, ids=NAMES)
def test_each_lesson_has_the_entry_of_a_completed_execution(path):
    name = execute_lessons.lesson_name(path)
    entry = RECORD.get(name)
    assert entry is not None, AGAIN + name
    assert entry['path'] == path.relative_to(ROOT).as_posix()
    assert entry['status'] == 'completed' and entry['failures'] == [], entry['failures']


@pytest.mark.parametrize('path', LESSONS, ids=NAMES)
def test_each_recorded_file_exists_with_its_recorded_digest(path):
    name = execute_lessons.lesson_name(path)
    for listed, recorded in RECORD[name]['inputs'].items():
        assert (ROOT / listed).is_file(), listed
        assert execute_lessons.digest(ROOT / listed) == recorded, f'{listed} changed; ' + AGAIN + name


@pytest.mark.parametrize('path', LESSONS, ids=NAMES)
def test_each_lesson_is_the_executed_version_its_entry_names(path):
    name = execute_lessons.lesson_name(path)
    assert execute_lessons.digest(path) == RECORD[name]['sha256'], AGAIN + name


@pytest.mark.parametrize('path', LESSONS, ids=NAMES)
def test_the_entry_records_the_listed_files_and_the_set_up_module(path):
    """The entry's inputs are the files the second markdown cell lists, in its
    order, then the set-up module and nothing else: the layout of a drawing is
    the package's own and is recorded as no separate input."""
    listed = execute_lessons.listed_files(nbformat.read(path, as_version=4))
    inputs = list(RECORD[execute_lessons.lesson_name(path)]['inputs'])
    assert inputs == listed + [execute_lessons.SETUP], AGAIN + execute_lessons.lesson_name(path)


SET_UP_MODULE = ROOT / 'tutorials' / 'checkout.py'
# the address the stand-in's serve answers
ADDRESS = 'http://localhost:8080/?data=stand-in'
# anything that is not a mapping is a stage to explore
A_STAGE = object()
# the namespace of each node of the stand-in's view of a stage, by graph
# (the empty namespace is that of a graph's own inputs and outputs)
STAGE_GRAPHS = {
    'backward': ['', 'cntn_to_dcsn', 'cntn_to_dcsn/risk_ce', 'policy', 'dcsn_to_arvl', ''],
    'forward': ['', 'arvl_to_dcsn', 'dcsn_to_cntn', ''],
}
# the namespace of each node of the stand-in's view of a trellis, by graph
TRELLIS_GRAPHS = {
    'backward': ['', 'periods[1]/port/cntn_to_dcsn', 'periods[1]/cons/policy',
                 'periods[1]/cons/cntn_to_dcsn/risk_ce', 'periods[0]/port/dcsn_to_arvl',
                 'periods[0]/cons/policy', ''],
    'forward': ['', 'periods[1]/port/arvl_to_dcsn', 'periods[0]/cons/dcsn_to_cntn', ''],
}
# the sentence explore prints where the viewer is not installed
NO_VIEWER = ("The interactive view needs Google's Model Explorer, the extra `explore` of the "
             'package: pip install -e "packages/bellman[explore]".')
# the stand-in's sentence on the viewer's SVG text renderer, which differs from
# the package's so that a test shows which one explore prints
STAND_IN_SENTENCE = 'The stand-in sentence on the SVG text renderer.'
# the stand-in's palette: the package's tokens that the display reads, with
# the values of docs/_stylesheets/bellman.css
STAND_IN_PALETTE = {'--bl-navy': '#172A52', '--bl-slate': '#4B5A7A', '--bl-ice': '#EDF7FC',
                    '--bl-ultramarine': '#214EDA', '--bf-face': '#FFFFFF'}
# One call of the stand-in's serve.
Served = namedtuple('Served', 'graph_path port graph_id layers')
# The set-up module as a lesson imported it, the stand-in and the lesson's folder.
Lesson = namedtuple('Lesson', 'checkout viewer folder')


def stand_in_viewer():
    """A stand-in for the package's module bellman.factory.model_explorer. Its
    write_model_explorer writes the two files of a view into the folder
    given, the graph file holding the graphs of STAGE_GRAPHS, or of
    TRELLIS_GRAPHS for a mapping, as the package's module tells a trellis,
    and returns their paths; its serve takes the arguments of the package's
    serve, records them in `served` and returns ADDRESS without starting a
    server; its layers_to_open is the package's own function, imported from
    the package's module before `import_set_up_module` puts the stand-in in
    that module's place; its VIEWER_PORT is the package's port, 8080, its
    SVG_TEXT_SENTENCE is STAND_IN_SENTENCE and its PALETTE is
    STAND_IN_PALETTE."""
    from bellman.factory.model_explorer import layers_to_open

    viewer = types.ModuleType('bellman.factory.model_explorer')
    viewer.served = []
    viewer.VIEWER_PORT = 8080
    viewer.SVG_TEXT_SENTENCE = STAND_IN_SENTENCE
    viewer.PALETTE = STAND_IN_PALETTE

    def write_model_explorer(stage_or_trellis, folder):
        trellis = isinstance(stage_or_trellis, Mapping)
        label, graphs = ('trellis', TRELLIS_GRAPHS) if trellis else ('cons', STAGE_GRAPHS)
        collection = {'label': label, 'graphs': [
            {'id': graph, 'nodes': [{'id': f'{graph} {index}', 'namespace': namespace}
                                    for index, namespace in enumerate(namespaces)]}
            for graph, namespaces in graphs.items()]}
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        paths = tuple(folder / f'{label}{ending}' for ending in ('.graph.json', '.edge-overlays.json'))
        paths[0].write_text(json.dumps(collection), encoding='utf-8')
        paths[1].write_text('{}', encoding='utf-8')
        return paths

    def serve(graph_path, *, port=8080, graph_id=None, layers=()):
        viewer.served.append(Served(graph_path, port, graph_id, tuple(layers)))
        return ADDRESS

    viewer.write_model_explorer = write_model_explorer
    viewer.serve = serve
    viewer.layers_to_open = layers_to_open
    return viewer


class DisplayParts(HTMLParser):
    """The parts of the display that explore returns, read from its HTML:
    the attributes of its first element, `outer`, of its link, `link`, and of
    its frame, `frame`, and its texts in order, `texts`."""

    def __init__(self, display):
        super().__init__()
        self.outer, self.link, self.frame, self.texts = None, None, None, []
        self.feed(display.data)

    def handle_starttag(self, tag, attrs):
        if self.outer is None:
            self.outer = dict(attrs)
        if tag == 'a':
            self.link = dict(attrs)
        elif tag == 'iframe':
            self.frame = dict(attrs)

    def handle_data(self, data):
        self.texts.append(data)


def import_set_up_module(tmp_path, monkeypatch, viewer):
    """The set-up module as a lesson in tutorials/getting-started of a checkout
    made in tmp_path imports it, with `viewer` in sys.modules in place of the
    package's module: a stand-in, or None, under which that module cannot be
    imported. The working directory, sys.path, sys.modules and the
    environment are restored after the test."""
    root = tmp_path / 'checkout'
    (root / 'packages' / 'bellman').mkdir(parents=True)
    folder = root / 'tutorials' / 'getting-started'
    folder.mkdir(parents=True)
    monkeypatch.setenv('BELLMAN_DDSL_ROOT', str(root))
    monkeypatch.chdir(folder)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    # the set-up module refuses a bellman imported from another checkout
    monkeypatch.delitem(sys.modules, 'bellman', raising=False)
    monkeypatch.setitem(sys.modules, 'bellman.factory.model_explorer', viewer)
    spec = importlib.util.spec_from_file_location('checkout', SET_UP_MODULE)
    checkout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checkout)
    return Lesson(checkout, viewer, folder)


@pytest.fixture
def lesson(tmp_path, monkeypatch):
    """The set-up module imported with the stand-in (`import_set_up_module`),
    and the viewer's presence stood in for: `importlib.util.find_spec`
    answers a spec for `model_explorer`, so that the tests need no viewer."""
    find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, 'find_spec',
                        lambda name, package=None: importlib.machinery.ModuleSpec(name, None)
                        if name == 'model_explorer' else find_spec(name, package))
    return import_set_up_module(tmp_path, monkeypatch, stand_in_viewer())


def test_importing_the_set_up_module_imports_no_module_of_the_view(tmp_path, monkeypatch):
    """The set-up module imports the package's module of the view only when
    explore is called: its import succeeds where that module cannot be
    imported."""
    lesson = import_set_up_module(tmp_path, monkeypatch, None)
    assert callable(lesson.checkout.explore)


def test_a_recorded_run_prints_the_two_paths_from_the_checkout_root_and_serves_nothing(
        lesson, monkeypatch, capsys):
    """With BELLMAN_LESSONS_HEADLESS set, explore writes the two files into
    model-explorer/ of the lesson's folder, prints their paths from the
    checkout root, one to a line, returns None and serves nothing."""
    monkeypatch.setenv('BELLMAN_LESSONS_HEADLESS', '1')
    assert lesson.checkout.explore(A_STAGE) is None
    assert capsys.readouterr().out.splitlines() == [
        'tutorials/getting-started/model-explorer/cons.graph.json',
        'tutorials/getting-started/model-explorer/cons.edge-overlays.json',
    ]
    assert lesson.viewer.served == []


def test_the_variable_counts_as_set_when_it_holds_the_empty_string(lesson, monkeypatch, capsys):
    """BELLMAN_LESSONS_HEADLESS set to the empty string is set: explore prints
    the two paths and serves nothing."""
    monkeypatch.setenv('BELLMAN_LESSONS_HEADLESS', '')
    assert lesson.checkout.explore(A_STAGE) is None
    assert len(capsys.readouterr().out.splitlines()) == 2
    assert lesson.viewer.served == []


def test_a_run_by_hand_serves_the_backward_graph_on_port_8080_with_its_builders_opened_in_a_frame(
        lesson, monkeypatch, capsys):
    """Without the variable, explore serves the backward graph of the file it
    wrote on the package's port, 8080, with the stage's three builders, read
    from the file, as the layers opened; it prints the address and the
    package's sentence on the SVG text renderer and returns the display the
    cell shows: a title line that names the view by its label, `cons`, and
    the graph shown, the address as a link that opens a tab of its own, and
    the page in a frame 640 pixels high across the cell, within a navy
    hairline with square corners, in the colors of the package's palette."""
    monkeypatch.delenv('BELLMAN_LESSONS_HEADLESS', raising=False)
    display = lesson.checkout.explore(A_STAGE)
    views = lesson.folder / 'model-explorer'
    assert lesson.viewer.served == [Served(views / 'cons.graph.json', 8080, 'backward',
                                           ('cntn_to_dcsn', 'policy', 'dcsn_to_arvl'))]
    assert isinstance(display, HTML)
    parts = DisplayParts(display)
    assert parts.texts == ['cons', 'backward graph', ADDRESS]
    assert (parts.link['href'], parts.link['target']) == (ADDRESS, '_blank')
    assert (parts.frame['src'], parts.frame['width'], parts.frame['height']) == (ADDRESS, '100%', '640')
    assert parts.outer['style'].startswith('border:1px solid #172A52;border-radius:0;')
    assert 'border-radius:0' in parts.frame['style']
    printed = capsys.readouterr().out.splitlines()
    assert printed == [f'The view is at {ADDRESS}.', STAND_IN_SENTENCE]


def test_a_trellis_is_served_with_its_stage_occurrences_opened(lesson, monkeypatch):
    """A dictionary is a trellis, and the layers opened are its stage
    occurrences, periods[h]/<key>, each once, in the order of the nodes."""
    monkeypatch.delenv('BELLMAN_LESSONS_HEADLESS', raising=False)
    lesson.checkout.explore({'periods': [], 'inter_connectors': []})
    assert [served.layers for served in lesson.viewer.served] == [
        ('periods[1]/port', 'periods[1]/cons', 'periods[0]/port', 'periods[0]/cons')]


def test_a_mapping_that_is_no_dictionary_is_a_trellis_as_the_package_takes_it(lesson, monkeypatch):
    """explore tells a trellis from a stage as the package's module does, by
    collections.abc.Mapping: a read-only mapping of a trellis is served with
    its stage occurrences opened."""
    monkeypatch.delenv('BELLMAN_LESSONS_HEADLESS', raising=False)
    lesson.checkout.explore(types.MappingProxyType({'periods': [], 'inter_connectors': []}))
    assert [served.layers for served in lesson.viewer.served] == [
        ('periods[1]/port', 'periods[1]/cons', 'periods[0]/port', 'periods[0]/cons')]


def test_the_keywords_graph_and_port_name_the_graph_served_and_its_port(lesson, monkeypatch):
    """explore(stage, graph="forward", port=8181) serves the forward graph,
    with the two forward builders opened, at port 8181; a name that is no
    graph of the view is refused. The display names the graph shown."""
    monkeypatch.delenv('BELLMAN_LESSONS_HEADLESS', raising=False)
    display = lesson.checkout.explore(A_STAGE, graph='forward', port=8181)
    assert [(served.graph_id, served.layers, served.port) for served in lesson.viewer.served] == [
        ('forward', ('arvl_to_dcsn', 'dcsn_to_cntn'), 8181)]
    assert DisplayParts(display).texts[:2] == ['cons', 'forward graph']
    with pytest.raises(ValueError, match='backward and forward'):
        lesson.checkout.explore(A_STAGE, graph='sideways')
    assert len(lesson.viewer.served) == 1


def test_without_the_viewer_explore_prints_the_command_that_installs_it_and_returns_none(
        lesson, monkeypatch, capsys):
    """Where the viewer is not installed, explore prints the one sentence that
    names the extra and returns None, so that the lesson continues past the
    cell; it writes and serves nothing, since the package writes the view's
    files with the viewer's own classes."""
    find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, 'find_spec',
                        lambda name, package=None: None if name == 'model_explorer' else find_spec(name, package))
    monkeypatch.delenv('BELLMAN_LESSONS_HEADLESS', raising=False)
    assert lesson.checkout.explore(A_STAGE) is None
    assert capsys.readouterr().out.splitlines() == [NO_VIEWER]
    assert lesson.viewer.served == []
    assert not (lesson.folder / 'model-explorer').exists()


def test_a_port_another_program_holds_prints_the_packages_sentence_and_returns_none(
        lesson, monkeypatch, capsys):
    """Where another program holds the port, the package's serve refuses it
    with a ValueError; explore prints the refusal's sentence and returns None,
    as where the viewer is not installed, so that the lesson continues past
    the cell."""
    sentence = ("a program other than the viewer's server listens at the port 8080; give the "
                "view another port with port=, such as port=8081")

    def refused(graph_path, *, port=8080, graph_id=None, layers=()):
        raise ValueError(sentence)

    monkeypatch.setattr(lesson.viewer, 'serve', refused)
    monkeypatch.delenv('BELLMAN_LESSONS_HEADLESS', raising=False)
    assert lesson.checkout.explore(A_STAGE) is None
    assert capsys.readouterr().out.splitlines() == [sentence]


@pytest.mark.skipif(importlib.util.find_spec('model_explorer') is None,
                    reason='the viewer, the extra explore of the package, is not installed')
def test_a_run_by_hand_on_the_packages_module_serves_cons_and_the_trellis_of_lesson_05(
        tmp_path, monkeypatch, capsys):
    """Without the variable, explore on the package's own module writes the
    view of the stage cons, and of the trellis of two periods that lesson 05
    builds, into model-explorer/ of the lesson's folder with the package's
    write_model_explorer, and serves each through the package's serve, here a
    record of its arguments, at the package's port, with the builders of the
    stage or the stage occurrences of the trellis, read from the file written,
    as the layers opened; for each it prints the address and the package's
    sentence on the SVG text renderer and returns the display of the address,
    titled by the view's label and in the colors of the package's palette."""
    folder = tmp_path / 'lesson'
    folder.mkdir()
    monkeypatch.setenv('BELLMAN_DDSL_ROOT', str(ROOT))
    monkeypatch.delenv('BELLMAN_LESSONS_HEADLESS', raising=False)
    monkeypatch.chdir(folder)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    spec = importlib.util.spec_from_file_location('checkout', SET_UP_MODULE)
    checkout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checkout)
    from bellman.stage import elaborate_stage, load_stage
    from bellman.trellis import accrete
    from bellman.factory import model_explorer
    served = []
    monkeypatch.setattr(
        model_explorer, 'serve',
        lambda *files, **kwargs: served.append(Served(*files, **kwargs)) or ADDRESS)
    cons, port, disc = (
        elaborate_stage(load_stage(f'applications/portfolio-choice/declaration/stages/{name}/{name}.bl'))
        for name in ('cons', 'port', 'disc'))
    period = {'stages': {'port': port, 'cons': cons, 'disc': disc},
              'connectors': [{'m_next': 'm'}]}
    last = accrete({'periods': [], 'inter_connectors': []}, period)
    two = accrete(last, period, {'a': 'k'})
    displays = [checkout.explore(cons), checkout.explore(two)]
    views = folder / 'model-explorer'
    occurrences = tuple(f'periods[{h}]/{key}' for h in (1, 0) for key in ('port', 'cons', 'disc'))
    assert served == [
        Served(views / 'cons.graph.json', model_explorer.VIEWER_PORT, 'backward',
               ('cntn_to_dcsn', 'dcsn_to_arvl', 'policy')),
        Served(views / 'trellis.graph.json', model_explorer.VIEWER_PORT, 'backward', occurrences),
    ]
    assert sorted(path.name for path in views.iterdir()) == sorted(
        f'{label}{ending}' for label in ('cons', 'trellis')
        for ending in ('.graph.json', '.edge-overlays.json'))
    parts = [DisplayParts(display) for display in displays]
    assert [part.frame['src'] for part in parts] == [ADDRESS, ADDRESS]
    assert [part.texts[:2] for part in parts] == [['cons', 'backward graph'], ['trellis', 'backward graph']]
    navy = model_explorer.PALETTE['--bl-navy']
    assert all(part.outer['style'].startswith(f'border:1px solid {navy};') for part in parts)
    assert capsys.readouterr().out.splitlines() == [
        f'The view is at {ADDRESS}.', model_explorer.SVG_TEXT_SENTENCE] * 2
