"""Put a lesson's process in the checkout whose package and application it is to read.

This is the set-up module of the tutorials collection. Each lesson folder holds
a symbolic link named ``checkout.py`` to this file, and a lesson's first code
cell is ``import checkout``. The application whose ``code`` folder is put on
``sys.path`` is named by the lesson's folder, so that one module serves the
lessons of every model.

The lesson's folder is the working directory at the moment of the import.
Jupyter starts a notebook's kernel in the notebook's folder, and a tool that
executes a lesson starts its kernel there too. The module's own path cannot
name the folder: with its symbolic link resolved, ``__file__`` is
``tutorials/checkout.py`` whichever lesson imported it. The module reads the
folder once, for items 3 and 6 below.

Importing this module does the first five things below and prints nothing; the
sixth is the one name it defines for a lesson, the function ``explore``, which
a lesson calls as ``checkout.explore(stage)``. It sets no display for a
drawing: the package's ``Drawing`` lays itself out, so a cell holding
``diagram()`` alone shows the picture.

1. It finds the checkout. That is the folder named by the environment variable
   ``BELLMAN_DDSL_ROOT`` when it is set, which is how a tool that executes a
   lesson names the checkout under execution, and otherwise the nearest folder
   above this file, with its symbolic link resolved, that holds
   ``packages/bellman``.
2. It refuses a ``bellman`` already imported from another checkout. A kernel
   that holds one cannot be made to read this one, so the import stops and
   says to restart the kernel.
3. It puts that checkout's ``packages/bellman`` first on ``sys.path``. When the
   lesson's folder lies under ``tutorials/models/<name>/``, it puts the
   checkout's ``applications/<name>/code`` after the package, so that the
   lesson can import the application's numerical tool, such as
   ``cons_port_tool`` for a lesson in ``tutorials/models/cons-port/``. A model
   lesson's folder is named as its application, and a folder that names no
   application stops the import; an application whose ``code`` folder is
   missing or holds no module, such as ``benhabib-2019``, whose lessons call
   the package alone, adds nothing the lesson imports. A lesson under
   ``tutorials/getting-started/`` or ``tutorials/topics/`` puts no
   application folder on the path.
4. It changes the working directory to the checkout root, so that every path a
   lesson writes is the path the repository gives, such as
   ``applications/portfolio-choice/declaration/stages/cons/cons.bl``.
5. Under IPython it sets the exception display to minimal, the setting the
   magic ``%xmode Minimal`` makes, so that a stage the construction refuses
   prints the refusal's one sentence and no stack of frames; the setting is
   made through the same call the magic makes, which prints nothing.
6. It defines ``explore(obj, graph="backward", port=None)``, which a lesson
   calls as ``checkout.explore(stage)`` or ``checkout.explore(trellis)``. The
   function writes the view of ``obj`` in Google's Model Explorer, the two
   JSON files of the package's ``write_model_explorer``, into the folder
   ``model-explorer`` of the lesson's folder. Under the environment variable
   ``BELLMAN_LESSONS_HEADLESS``, which ``tools/execute_lessons.py`` sets for
   the kernels it starts, it prints the two paths from the checkout root and
   starts no server. Otherwise it shows the view below the cell: the graph
   ``graph``, served by the viewer at ``port``, the package's port 8080 where
   none is given, with the builders of a stage, or the stage occurrences of a
   trellis, opened (the package's ``layers_to_open`` on the file written), in a
   frame under a title line and the view's address, in the colors and the type
   of ``docs/_stylesheets/bellman.css``. Where the viewer is not installed, it
   writes nothing and prints the command that installs it; where another
   program holds the port, it prints the package's sentence that says so and
   shows nothing. In either case it returns None, so that the lesson continues.
"""
import html
import importlib.util
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path


def _checkout():
    """The checkout this lesson reads: the one BELLMAN_DDSL_ROOT names, else
    the nearest folder above this file holding packages/bellman."""
    named = os.environ.get("BELLMAN_DDSL_ROOT")
    if named is not None:
        return Path(named).resolve()
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "packages" / "bellman" / "bellman" / "__init__.py").is_file():
            return candidate
    raise RuntimeError(f"No folder above {here} holds packages/bellman; export BELLMAN_DDSL_ROOT.")


def _application(lesson):
    """The name of the application a lesson in the folder `lesson` reads:
    `<name>` when the folder lies under tutorials/models/<name>/, else None."""
    for folder in (lesson, *lesson.parents):
        if folder.parent.name == "models" and folder.parent.parent.name == "tutorials":
            return folder.name
    return None


def _application_code(checkout, name):
    """The folder applications/<name>/code of the checkout, or None when the
    application has no such folder; a name that is no application's stops the
    import."""
    application = checkout / "applications" / name
    if not application.is_dir():
        raise RuntimeError(f"The lesson folder tutorials/models/{name} names no application: "
                           f"{application} is not a folder.")
    code = application / "code"
    return code if code.is_dir() else None


def _refuse_a_package_of_another_checkout(package):
    """Stop when this kernel already holds a bellman imported from elsewhere."""
    loaded = sys.modules.get("bellman")
    if loaded is not None and not Path(loaded.__file__).resolve().is_relative_to(package):
        raise RuntimeError(f"Restart the kernel: it holds the package of another checkout, {loaded.__file__}.")


def _display_a_refusal_in_one_line(shell):
    """Print a refused construction as its message alone, with no frames.

    This is the call the magic ``%xmode Minimal`` makes, without the magic's
    own line of output."""
    shell.InteractiveTB.set_mode(mode="Minimal")


# The brand's type for the display of a view below a cell, the stacks of
# docs/_stylesheets/bellman.css: its statement face for the title, its text
# face and its code face for the address. The display loads no face, so a
# face the reader's machine lacks gives way to the next of its stack.
_STATEMENT_FONT = "'PP Monument', Archivo, Helvetica, Arial, sans-serif"
_TEXT_FONT = "Archivo, Helvetica, Arial, sans-serif"
_CODE_FONT = "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
# the height of the frame that shows the view, in pixels
_FRAME_HEIGHT = 640


def _view(url, graph_path, graph, palette):
    """The display of the view at the address `url` below the cell, in the
    colors of `palette`, the package's palette of the brand's tokens, and in
    the brand's type: a title line on ice over an ultramarine rule, which
    names the view by the label of the collection in the file at
    `graph_path`, the stage's name with its bindings or the trellis's, and
    the graph shown, `graph`; the address, a link that opens the page in a
    tab of its own; and the page in a frame across the cell, `_FRAME_HEIGHT`
    pixels high. A navy hairline with square corners encloses the three."""
    from IPython.display import HTML

    label = json.loads(Path(graph_path).read_text(encoding="utf-8"))["label"]
    navy, slate, ice = palette["--bl-navy"], palette["--bl-slate"], palette["--bl-ice"]
    ultramarine, white = palette["--bl-ultramarine"], palette["--bf-face"]
    title, shown, address = html.escape(label), html.escape(f"{graph} graph"), html.escape(url)
    return HTML(
        f'<div style="border:1px solid {navy};border-radius:0;background:{white};color:{navy};'
        f'font-family:{_TEXT_FONT};margin:0.5em 0">'
        f'<div style="display:flex;flex-wrap:wrap;align-items:baseline;gap:0.3em 1em;'
        f'padding:0.55em 0.9em 0.5em;background:{ice};border-bottom:1px solid {ultramarine}">'
        f'<span style="font-family:{_STATEMENT_FONT};font-size:1.1em;font-weight:500">{title}</span>'
        f'<span style="font-family:{_CODE_FONT};font-size:0.7em;letter-spacing:0.1em;'
        f'text-transform:uppercase;color:{slate}">{shown}</span></div>'
        f'<div style="padding:0.35em 0.9em;border-bottom:1px solid {navy};font-family:{_CODE_FONT};'
        f'font-size:0.72em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
        f'<a href="{address}" target="_blank" rel="noopener" title="{address}" '
        f'style="color:{ultramarine};text-decoration:none">{address}</a></div>'
        f'<iframe src="{address}" title="The {shown} of {title} in Model Explorer" width="100%" '
        f'height="{_FRAME_HEIGHT}" style="display:block;width:100%;height:{_FRAME_HEIGHT}px;'
        f'border:0;border-radius:0" allowfullscreen></iframe></div>'
    )


def explore(obj, graph="backward", port=None):
    """Show the view of a stage or a trellis in Google's Model Explorer below
    the cell; in a recorded run, write it and show nothing.

    `obj` is a stage, or a trellis, the dictionary that `accrete` or
    `elaborate_trellis` returns; any mapping is a trellis here, as it is to
    the package's module. Where the viewer is not installed, the
    function prints one sentence naming the extra of the package that
    installs it and returns None, so that the lesson continues past the cell;
    it writes nothing, since the package writes the view's files with the
    viewer's own classes. Otherwise the package's `write_model_explorer`
    writes the view's two JSON files into the folder model-explorer of the
    lesson's folder. When the environment variable BELLMAN_LESSONS_HEADLESS
    is set, to any value, as tools/execute_lessons.py sets it for the kernels
    it starts, the function prints the two paths from the checkout root,
    one to a line, starts no server and returns None. Otherwise the package's
    `serve` returns the address of a page on the viewer's server at `port`,
    the package's `VIEWER_PORT`, 8080, where `port` is None, started there
    unless a server already answers, which shows the graph `graph`,
    "backward" or "forward", with the layers of its builders opened for a
    stage, or those of its stage occurrences `periods[h]/<key>` for a
    trellis, each of which opens its period around it. The package's port
    serves every view, since the browser keeps the viewer's settings for each
    address. The function prints the address, "The view is at <address>.",
    and the package's sentence on the viewer's SVG text renderer, which draws
    the mathematical labels (`SVG_TEXT_SENTENCE`), and returns the display
    the cell shows (`_view`): a title line with the view's label and the
    graph, the address as a link, and the page in a frame, in the brand's
    colors and type. Where another program holds the port, `serve`
    refuses it with a `ValueError` whose sentence names another port; the
    function prints that sentence and returns None, as where the viewer is not
    installed, so that the lesson continues past the cell."""
    if importlib.util.find_spec("model_explorer") is None:
        print("The interactive view needs Google's Model Explorer, the extra `explore` of the "
              'package: pip install -e "packages/bellman[explore]".')
        return None
    from bellman.factory.model_explorer import (
        PALETTE, SVG_TEXT_SENTENCE, VIEWER_PORT, layers_to_open, serve, write_model_explorer)

    paths = write_model_explorer(obj, _LESSON_FOLDER / "model-explorer")
    if os.environ.get("BELLMAN_LESSONS_HEADLESS") is not None:
        for path in paths:
            print(Path(path).relative_to(_CHECKOUT_ROOT).as_posix())
        return None
    graph_path, _ = paths
    # a trellis opens its stage occurrences, a stage its builders
    depth = 2 if isinstance(obj, Mapping) else 1
    layers = layers_to_open(json.loads(Path(graph_path).read_text(encoding="utf-8")), graph, depth)
    try:
        url = serve(graph_path, port=VIEWER_PORT if port is None else port,
                    graph_id=graph, layers=layers)
    except ValueError as refusal:
        # another program holds the port
        print(refusal)
        return None
    print(f"The view is at {url}.")
    print(SVG_TEXT_SENTENCE)
    return _view(url, graph_path, graph, PALETTE)


def _setup(lesson):
    """Do the first five things of the module's docstring for a lesson in the
    folder `lesson`."""
    checkout = _checkout()
    package = checkout / "packages" / "bellman"
    _refuse_a_package_of_another_checkout(package)
    name = _application(lesson)
    code = None if name is None else _application_code(checkout, name)
    if code is not None:
        sys.path.insert(0, str(code))
    sys.path.insert(0, str(package))
    os.chdir(checkout)
    try:
        from IPython import get_ipython
    except ImportError:
        return
    shell = get_ipython()
    if shell is None:
        return
    _display_a_refusal_in_one_line(shell)


# the lesson's folder, the working directory at the moment of the import
_LESSON_FOLDER = Path.cwd()
_setup(_LESSON_FOLDER)
# the checkout root, the working directory that `_setup` sets
_CHECKOUT_ROOT = Path.cwd()
