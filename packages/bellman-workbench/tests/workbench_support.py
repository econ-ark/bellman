"""The fixtures and the helpers of Bellman Workbench's tests, in one module,
by the project's rule for tests: a test file defines no load, parse or
build helper of its own. `conftest.py` imports the fixtures from here; the
test files import the helpers and the constants from here by this module's
name, which no other test folder of the repository uses.

The stages: `cons_text` is the text of
`applications/portfolio-choice/declaration/stages/cons/cons.bl` and `cons`
its stage, elaborated by `elaborate_text` with the file's path in the
repository as its origin, as the corpus fixtures of `packages/bellman/tests`
build it; `entrepreneur_death` is the elaboration of
`applications/cagetti-denardi-2006/declaration/stages/entrepreneur_death/`
`entrepreneur_death.bl`, whose forward builders graph the construction
refuses.

The folders: `model_folder`, `pension_folder`, `cagetti_folder` and
`durables_folder` are copies of `applications/portfolio-choice/`,
`applications/pension-retirement/`, `applications/cagetti-denardi-2006/`
and `applications/durables/`, each in a temporary folder that is a fresh
git repository with one commit, made once per session, so that no test
edits the checkout's files. A test that writes takes `scratch_folder`, a
fresh copy of `model_folder` per test, `scratch_pension`, a fresh copy of
`pension_folder` per test, `scratch_durables`, a fresh copy of the durables
model per test, or `cons_file`, the path of `cons.bl` in `model_folder`,
whose original text is written back at the test's end.

The page: `server_on(folder, delay_marker=None, matsya_command=MATSYA_STUB)`
starts Solara's server on the page over `folder`, on a free port, through
the console command's own command line and environment
(`command.server_environment`), once per folder, marker and client and
per session, and stops it at the session's end; `server` is the URL
of the one over `model_folder`, started with the delay marker DELAY_MARKER,
so that a test of the discard can hold a chosen revision's result back.
`browser` is one headless Chromium for the session, launched from the
executable the environment variable `BELLMAN_WORKBENCH_CHROMIUM` names when
that is set (`chromium_executable`), so that a machine with Playwright's
own Chromium needs nothing; `page` is a page in a new browser context for
one test. The functions after the fixtures read and drive the page; the
script `screenshots.py` beside this module calls the same functions.

Matsya's client: the fixture `matsya_stub`, which every test of this
folder uses, names in BELLMAN_WORKBENCH_MATSYA the stand-in
`matsya_stub.py` beside this module, run by the tests' own interpreter
(MATSYA_STUB), so that no test reaches Matsya's service or needs a token;
STUB_PASSAGES are the two passages the stand-in names; `stub_job` writes a
job into the stand-in's service and `stub_calls` reads its log (unit G2).
Every server of the page is started with the same stand-in
(`start_server`), but one a test starts with `matsya_command="off"`, the
setting that removes Matsya's column (spec 0.4 §6).

The cache folder: the fixture `cache_folder`, which every test of this
folder uses, sets `XDG_CACHE_HOME` to a temporary folder for the session,
so that no test, and no server a test starts, writes a stage view into the
user's own cache folder. A test that needs a cache folder of its own gives
it to each server it starts, `start_server(..., cache_home=<folder>)`. A
test that reads or keeps the binding of a trellis in its own process takes
`own_cache_folder`, a cache folder of its own, as `app_state` does;
`specify_calls` records the calls of `specify_trellis` the reading makes,
and `kept_bindings` lists the bindings a cache folder holds.

The skip rule for the page's tests: every test of a file whose name begins
with `test_page` is skipped, with the reason stated, when Playwright's
Chromium cannot be launched here.
`pytest_collection_modifyitems` launches Chromium once, headless, with
`chromium_executable` as its executable when that is set, and marks each
test of that file with the launch's error when the launch fails.

Node: `node` is the path of the executable `node`, and a test that takes it
is skipped when none is on the PATH; `node_output` runs a script as a Node
module on the JSON of an input and answers the JSON it prints, decoded.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import http.server
import io
import json
import math
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

# the Workbench's distribution folder, and the README of the graph's bundle,
# which records its build (unit G, G-D15)
WORKBENCH = ROOT / "packages/bellman-workbench"
FLOW_README = WORKBENCH / "js/flow/README.md"
# the files js/flow/build.sh writes, by their paths from WORKBENCH
FLOW_FILES = {
    "bundle": "bellman_workbench/public/flow/bellman-flow.js",
    "notices": "bellman_workbench/public/flow/LICENSES.txt",
    "elk": "bellman_workbench/public/flow/elk.bundled.js",
    "elk license": "bellman_workbench/public/flow/elkjs-LICENSE.md",
    "base": "bellman_workbench/public/flow/base.css",
    "stix": "bellman_workbench/public/flow/stix-two-math-latin-400-normal.woff2",
    "stix license": "bellman_workbench/public/flow/STIX-Two-Math-OFL.txt",
}
# the folder of Solara's own interface files in the Workbench's package, and
# the README that records how they were fetched (unit G, G-D12)
SOLARA_CDN = WORKBENCH / "bellman_workbench/solara-cdn"
SOLARA_CDN_README = WORKBENCH / "js/solara-cdn/README.md"
# a closed port, named as the proxy of every scheme to a process that must
# not reach the network
CLOSED = "http://127.0.0.1:9"

# The two checkout finders excluded from installed processes (unit G, R20).
EDITABLE_FINDERS = frozenset({
    "__editable___bellman_0_1_0_finder",
    "__editable___bellman_workbench_0_1_0_finder",
})

# the SHA-256 of lib/elk.bundled.js in the npm package elkjs 0.12.0
ELK_SHA256 = "1222e44f953ce7746af23801e723708f8e6f436b8b377a6a5fc7552f34a307b3"
CONS_PATH = "applications/portfolio-choice/declaration/stages/cons/cons.bl"
# the stage whose forward builders graph the construction refuses under the
# rule `not-constructed`, at line 17 (the distribution of y_n)
ENTREPRENEUR_DEATH_PATH = ("applications/cagetti-denardi-2006/declaration/stages/"
                           "entrepreneur_death/entrepreneur_death.bl")
PORTFOLIO_CHOICE = ROOT / "applications/portfolio-choice"
PENSION_RETIREMENT = ROOT / "applications/pension-retirement"
CAGETTI_DENARDI = ROOT / "applications/cagetti-denardi-2006"
RETIREMENT_CHOICE = ROOT / "applications/retirement-choice"
CONS_PORT = ROOT / "applications/cons-port"
DURABLES = ROOT / "applications/durables"
BUFFER_STOCK = ROOT / "applications/buffer-stock"
# The folder of the portfolio-consumption model written the method way, which
# the tests of units E2 to E4 open (specification 0.6 §9; SE-25), one folder
# with cons-port since 28 October 2026, and its consumption and portfolio
# stage files
DEMONSTRATION = ROOT / "applications/cons-port"
DEMONSTRATION_CONS = "declaration/stages/cons/cons.bl"
DEMONSTRATION_PORT = "declaration/stages/port/port.bl"
# the trellis file of lesson 05, relative to the copy of cons-port, the file
# the recipe PORT_CONS_RECIPE names, which lists the stage keys and writes
# the connectors; and that recipe, the source a page opens the trellis from
PORT_CONS = "declaration/trellis.port-cons.yml"
PORT_CONS_RECIPE = "declaration/spec.port-cons.yml"
# the first of cons-port's recipes in name order, on whose trellis the copy
# of cons-port opens, relative to the copy, and the trellis file it names
CONS_PORT_RECIPE = "declaration/spec.cons-port.yml"
CONS_PORT_TRELLIS = "declaration/trellis.cons-port.yml"
# the trellis file of records of the portfolio-first order that remains, read
# with no recipe, the subject of the tests of a folder of records
PORT_CONS_RECORDS = "declaration/trellis.port-cons-vfi.yml"
# the consumption stage's file, inside the folder since 28 October 2026, by
# its path from the copy of cons-port, as the editor names it
SHARED_CONS = "declaration/stages/cons/cons.bl"

# The templates of a stage the tests choose (unit C, spec 0.3 §4), by the
# ids `creation.stage_templates` gives them, and the stages of the
# demonstration of spec 0.2 §11, which spec 0.3 §13 keeps: port, cons and
# disc of the portfolio model, each under its own key.
PORT_ID = "cons-port/declaration/spec.port-cons.yml#port"
CONS_ID = "cons-port/declaration/spec.port-cons.yml#cons"
DISC_ID = "cons-port/declaration/spec.port-cons.yml#disc"
NOPORT_ID = "cons-port/declaration/trellis.reference-cons-only.yml#noport"
WORKER_ID = "pension-retirement/declaration/spec.yml#worker_saving"
# the pension model's terminal stage, which declares no parameter and
# brings no file; the tests of unit K's Task 12 copy it as a bequest
TERMINAL_ID = "pension-retirement/declaration/spec.yml#terminal"
DEMO_STAGES = (("port", PORT_ID), ("cons", CONS_ID), ("disc", DISC_ID))

# the files "new trellis" writes for the demonstration's stages, relative
# to the new folder and sorted: the one layout of a model folder, with
# answers.yml and the .gitignore at the top
DEMO_FILES = (
    ".gitignore",
    "README.md",
    "answers.yml",
    "declaration/calibration/portfolio.yml",
    "declaration/period.yml",
    "declaration/settings/cons_wide.yml",
    "declaration/settings/port_wide.yml",
    "declaration/spec.yml",
    "declaration/stages/cons/cons.bl",
    # each stage's addition, which its template brings beside its stage
    # file (decision S7-W2)
    "declaration/stages/cons/methods.bl",
    "declaration/stages/disc/disc.bl",
    "declaration/stages/disc/methods.bl",
    "declaration/stages/port/methods.bl",
    "declaration/stages/port/port.bl",
    "declaration/trellis.yml",
)

# the files `create_variant` writes for the variant `two-stages` of the
# pension model's recipe `spec.yml`, relative to the model folder, in the
# order it answers them: the recipe, the trellis file and the period file
VARIANT_FILES = (
    "declaration/spec.two-stages.yml",
    "declaration/trellis.two-stages.yml",
    "declaration/period.two-stages.yml",
)

# the source each slot of the demonstration is filled with at 4:30 (spec
# 0.2 §11), by its path from the recipe's folder `declaration/`; the
# discounting stage's settings take no source, the empty list; the methods
# are no slot, the recipe naming each stage's addition (decision S7-F3)
DEMO_FILLS = {
    "port_calibration": "calibration/portfolio",
    "port_settings": "settings/port_wide",
    "cons_calibration": "calibration/portfolio",
    "cons_settings": "settings/cons_wide",
    "disc_calibration": "calibration/portfolio",
    "disc_settings": None,
}

# the files of the page's tests, which the skip rule applies to: every test
# file whose name begins with this, test_page.py, test_page_creation.py and
# test_page_demonstration.py
PAGE_TESTS = "test_page"

# the recipe of a folder in the one layout of a model folder, by its path
# from the folder
RECIPE_FILE = "declaration/spec.yml"
# the file every page test over `model_folder` opens, relative to the folder;
# a folder "new trellis" writes with the demonstration's stages holds the
# consumption stage at the same path
CONS = "declaration/stages/cons/cons.bl"
# the portfolio stage's file in `model_folder`, relative to the folder
PORT = "declaration/stages/port/port.bl"
# the worker's stage file in `pension_folder`, relative to the folder, which
# the folder's recipe binds as `periods[0] / worker_saving`
WORKER_SAVING = "declaration/stages/worker_saving/worker_saving.bl"
# the retirement choice's stage file in `pension_folder`, relative to the
# folder
RETIRE_CHOICE = "declaration/stages/retire_choice/retire_choice.bl"
# the discount stage's file in the lifecycle registry, relative to the
# folder, the path it has in `model_folder` too
DISC = "declaration/stages/disc/disc.bl"
# The durables model's variant and three of its stage files, relative to
# `durables_folder`: the recipe `declaration/spec.yml` (RECIPE_FILE) binds
# `keeper_cons.bl` and `tenure.bl` at 51 positions, one per period, and
# `bequest.bl` at one, `periods[0]`; the variant binds `keeper_cons.bl` at
# 51 and `bequest.bl` at one, and holds no tenure stage.
TWO_STAGES = "declaration/spec.two-stages.yml"
KEEPER_CONS = "declaration/stages/keeper_cons/keeper_cons.bl"
TENURE = "declaration/stages/tenure/tenure.bl"
BEQUEST = "declaration/stages/bequest/bequest.bl"
TREE_FILE = f'.bl-tree-file[data-path="{CONS}"]'
VIEWPORT = {"width": 1600, "height": 1000}

# the editor's idle interval before the buffer is sent (specification §2.2)
PAUSE_MS = 750
# item 2 of stage A: the view shows the new graph within two seconds of the
# pause
BUDGET_MS = 2000

# the seconds the server may take to answer its first request
SERVER_SECONDS = 60

# The comment text the tests' server holds in BELLMAN_WORKBENCH_DELAY_MARKER:
# a buffer that holds it has its loop's result held back 1.5 s (the hook
# `app.py` documents), so that the test of the discard knows which
# revision's result finishes last.
DELAY_MARKER = "# a1-delay"

# The stand-in of Matsya's client, `matsya_stub.py` beside this module, as
# the command line that runs it with the tests' own interpreter, and the
# two passages it names, as the window lists them.
MATSYA_STUB = shlex.join([sys.executable, str(Path(__file__).with_name("matsya_stub.py"))])
STUB_PASSAGES = (
    "docs/overview/03-language.md",
    "docs/bellman-calculus/04-fields, functions and types.md",
)

# The status line (specification 0.3, §2.5): the file and whether it is a
# buffer or a file, the refusal count where it is not zero, the state of
# the loop, the version, the counts of the object, the time of the whole
# loop, and the digest of the text and of each binding source, each named;
# no count of the recipe's slots (unit K, K-D29).
STATUS = re.compile(
    r"^(?P<path>\S+) \((?P<file>file|buffer, unsaved)\)"
    r"(?: · (?P<refusals>\d+) refused)?"
    r" · (?P<state>not parsed|parsed, refused|constructed(?:, (?:forward|backward) refused)?)"
    r"(?: · (?P<version>symbolic|bound|partially bound|bindings refused))?"
    r"(?: · (?P<blocks>\d+) blocks(?: \((?P<backward>\d+) backward, (?P<forward>\d+) forward\),"
    r" (?P<builders>\d+) builders, (?P<wires>\d+) wires)?)?"
    r" · loop (?P<seconds>\d+\.\d\d) s · text (?P<digest>[0-9a-f]{7})"
    r"(?P<sources>(?: · \w+ [0-9a-f]{7})*)$"
)

# --- JavaScript run in the page ---

# The labels of the boxes and the names of the layers drawn by the region; a
# builder's segment in the strip of a card, which prints no text (AAS,
# L-D25), by the id its accessible name gives.
SVG_TEXTS_JS = """
() => Array.from(
  document.querySelectorAll(
    '.bl-view-host .bf-name, .bl-view-host .bf-layer-name, '
    + '.bl-view-host .bf-builder:not(:has(.bf-name))'),
  (element) => element.classList.contains('bf-builder')
    ? element.getAttribute('aria-label').replace(/^closed layer /, '') : element.textContent)
"""

# The times of keys, save clicks and layouts, selections and status texts.
RECORDERS_JS = """
() => {
  window.record = {keys: [], clicks: [], processed: [], selections: [], status: []};
  document.addEventListener('keydown', () => window.record.keys.push(performance.now()), true);
  document.addEventListener('click', (event) => {
    if (event.target.closest && event.target.closest('.bl-save')) {
      window.record.clicks.push(performance.now());
    }
  }, true);
  const region = (event) =>
    event.target.classList && event.target.classList.contains('bl-view-host');
  document.addEventListener('processed', (event) => {
    if (region(event)) window.record.processed.push(performance.now());
  }, true);
  document.addEventListener('selected', (event) => {
    if (region(event)) window.record.selections.push((event.detail || {}).nodeId || '');
  }, true);
  const read = () => {
    const line = document.querySelector('.bl-status-line');
    return line ? line.textContent : '';
  };
  window.record.status.push([performance.now(), read()]);
  new MutationObserver(() => {
    const text = read();
    const last = window.record.status[window.record.status.length - 1];
    if (text !== last[1]) window.record.status.push([performance.now(), text]);
  }).observe(document.querySelector('.bl-status'),
             {subtree: true, childList: true, characterData: true});
  return true;
}
"""

# The label and graphs of the collection held by the region.
HELD_COLLECTION_JS = """
() => {
  const host = document.querySelector('.bl-view-host');
  const held = host && host.bellmanFlow ? host.bellmanFlow.collection() : null;
  return held ? {label: held.label, graphs: held.graphs} : null;
}
"""

# The layout count, exact collection and graph at the last processed event.
LAYOUT_RECORDER_JS = """
() => {
  window.laidOut = {count: 0, length: null, collection: null, graphId: null};
  // one listener for the document: a second installation on the same document counts again from zero and
  // adds no second listener, which would count every layout twice (unit S)
  if (window.laidOutListening) return;
  window.laidOutListening = true;
  document.addEventListener('processed', (event) => {
    const host = event.target;
    if (!host.classList || !host.classList.contains('bl-view-host')) return;
    const held = host.bellmanFlow ? host.bellmanFlow.collection() : null;
    const serialized = held ? JSON.stringify(held) : null;
    window.laidOut.count += 1;
    window.laidOut.length = serialized === null ? null : serialized.length;
    window.laidOut.collection = serialized;
    window.laidOut.graphId = (event.detail || {}).graphId || null;
  }, true);
}
"""

# The collection label and whether its content and the graph the header
# names (`.bl-graph-bar`'s data-graph) were processed.
VIEW_STATE_JS = """
() => {
  const host = document.querySelector('.bl-view-host');
  const held = host && host.bellmanFlow ? host.bellmanFlow.collection() : null;
  const bar = document.querySelector('.bl-graph-bar');
  const current = held !== null && bar !== null &&
    JSON.stringify(held) === window.laidOut.collection &&
    bar.dataset.graph === window.laidOut.graphId;
  const label = held ? held.label : null;
  return {label, processed: window.laidOut.count, current, busy: !current};
}
"""

# The first underlined refusal: its line, its column counted from one in
# code points, as the package counts (the editor's document counts UTF-16
# code units, two for a character such as 𝑢, which `Array.from` reads as
# one), and the text it underlines.
LINT_RANGE_JS = """
() => {
  const mark = document.querySelector('.cm-content .cm-lintRange-error');
  if (!mark) return null;
  const line = mark.closest('.cm-line');
  const lines = Array.from(document.querySelectorAll('.cm-content .cm-line'));
  const range = document.createRange();
  range.setStart(line, 0);
  range.setEndBefore(mark);
  return {line: lines.indexOf(line) + 1, column: Array.from(range.toString()).length + 1,
          text: mark.textContent};
}
"""

# the line the gutter's refusal marker stands on, by its vertical position
GUTTER_MARKER_LINE_JS = """
() => {
  const marker = document.querySelector('.cm-lint-marker-error');
  if (!marker) return null;
  const box = marker.getBoundingClientRect();
  const lines = Array.from(document.querySelectorAll('.cm-content .cm-line'));
  return lines.findIndex((line) => {
    const b = line.getBoundingClientRect();
    return b.top <= box.top + 2 && box.top < b.bottom;
  }) + 1;
}
"""

ACTIVE_LINE_JS = """
() => {
  const gutter = document.querySelector('.cm-lineNumbers .cm-activeLineGutter');
  return gutter ? gutter.textContent.trim() : null;
}
"""

LINE_TEXT_JS = "(n) => document.querySelectorAll('.cm-content .cm-line')[n - 1].textContent"

# The status line's text: the details' line `.bl-status-line`, preceded in
# the trellis view by the trellis's line `.bl-trellis-status`, which is
# printed once, in the visible line, so that the two read as the details'
# line read before (unit J's plan, Task 21, rule 4).
STATUS_TEXT_JS = """
() => {
  const trellis = document.querySelector('.bl-trellis-status');
  const line = document.querySelector('.bl-status-line');
  return (trellis ? trellis.textContent : '') + (line ? line.textContent : '');
}
"""

VIEW_OPACITY_JS = """
() => {
  const host = document.querySelector('.bl-view-host');
  return host ? parseFloat(getComputedStyle(host).opacity) : null;
}
"""

TOOLTIP_TEXTS_JS = """
() => Array.from(document.querySelectorAll('.cm-tooltip-lint .cm-diagnosticText'))
  .map((element) => element.textContent)
"""

BOX_EVENT_JS = """
([nodeId, graphId]) => {
  const box = Array.from(document.querySelectorAll('.bl-view-host .react-flow__node'))
    .find((element) => element.dataset.id === nodeId);
  if (!box) throw new Error(`the region draws no box ${nodeId} of ${graphId}`);
  box.dispatchEvent(new MouseEvent('__event__', {bubbles: true, cancelable: true}));
}
"""

SELECT_NODE_JS = BOX_EVENT_JS.replace("__event__", "click")

# A double click on a drawn box (AMD-MI-002 §3 rule 2).
DOUBLE_CLICK_NODE_JS = BOX_EVENT_JS.replace("__event__", "dblclick")

# The graph ids of the collection held by the region, or an empty list.
HELD_GRAPH_IDS_JS = """
() => {
  const host = document.querySelector('.bl-view-host');
  const held = host && host.bellmanFlow ? host.bellmanFlow.collection() : null;
  return held ? held.graphs.map((graph) => graph.id) : [];
}
"""

# The open layers and selection at each processed or selected event.
PANE_STATE_RECORDER_JS = """
() => {
  window.viewState = null;
  const read = (event) => {
    const host = event.target;
    if (!host.classList || !host.classList.contains('bl-view-host') || !host.bellmanFlow) return;
    const open = host.bellmanFlow.openLayers();
    const deepest = open.filter((layer) => !open.some((other) => other.startsWith(layer + '/')));
    window.viewState = {
      open: deepest.map((layer) => layer + '___group___'),
      selected: host.bellmanFlow.selection() || '',
    };
  };
  document.addEventListener('processed', read, true);
  document.addEventListener('selected', read, true);
}
"""

# The last reported state: the deepest open layer of each branch and selection.
PANE_STATE_JS = "() => window.viewState"

# A recorder of the texts that elements take: for each selector of the list
# it is given, window.texts[selector] holds the text of the first element
# that matches the selector when the recorder is installed, then each new
# text that element takes.
TEXTS_RECORDER_JS = """
(selectors) => {
  window.texts = {};
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    const seen = [element.textContent];
    window.texts[selector] = seen;
    new MutationObserver(() => {
      if (element.textContent !== seen[seen.length - 1]) seen.push(element.textContent);
    }).observe(element, {subtree: true, childList: true, characterData: true});
  }
}
"""

# the focus removed from the element that holds it, which leaves the focus
# on the page's body, outside every text field
BLUR_JS = "() => { if (document.activeElement) document.activeElement.blur(); }"

# a recorder, on the browser's window, of whether the page prevented the
# browser's own reading of the last key pressed: window.keyPrevented is the
# defaultPrevented of the last keydown, read in the bubble phase of the
# window, after every listener of the page
KEY_PREVENTED_RECORDER_JS = """
() => {
  window.keyPrevented = null;
  if (!window.keyPreventedRecorded) {
    window.keyPreventedRecorded = true;
    window.addEventListener('keydown', (event) => {
      window.keyPrevented = event.defaultPrevented;
    });
  }
}
"""

# where the panel's open stage file is used, its rows `periods` and `also`:
# each recipe's path, its periods as the page prints them and the
# occurrence its link shows, in the panel's order
USED_AT_JS = """
() => Array.from(document.querySelectorAll('.bl-used-at .bl-used-recipe')).map((recipe) => [
  recipe.dataset.path,
  recipe.textContent,
  recipe.dataset.occurrence,
])
"""

# Details as the page prints it: the head's text, then each row's key as
# the row writes it, its data-key, which the page prints in sentence case
# (design pass 13 §3; C12), with the text of each of its lines, the spaces
# of every text run together and the cells of a line of a table joined by
# one space; `printed_details` gives an expected table the lines the page
# prints
DETAILS_ROWS_JS = """
() => {
  const text = (element) => element.textContent.split(/\\s+/).filter(Boolean).join(' ');
  const line = (element) => element.tagName === 'TR'
    ? Array.from(element.cells, text).join(' ') : text(element);
  const head = document.querySelector('.bl-panel .bl-panel-head');
  return [
    head ? text(head) : '',
    Array.from(document.querySelectorAll('.bl-panel .bl-details-row')).map((row) => [
      row.dataset.key,
      Array.from(row.querySelectorAll('.bl-details-line'), line),
    ]),
  ];
}
"""


def printed_details(expected: tuple) -> tuple:
    """The table `expected` of Details, `(head, rows)` with each row `(key,
    lines)` as the package answers them, with the words the page prints: the
    graph's direction that ends the head in sentence case, `Forward`, as the
    graph bar's select prints it, a join's head beginning with its kind in
    sentence case, `Join` (the fix wave Q3b of unit Q, item 19; C12), and the
    states of the row `bound` in Small joined by commas, `methodized,
    configured` (design pass 13 §3; C8)."""
    head, rows = expected
    head = re.sub(r" (backward|forward)$", lambda found: f" {found[1].capitalize()}", head)
    head = re.sub(r"^join ", "Join ", head)
    return head, [
        (key, [line.replace(" · ", ", ") for line in lines] if key == "bound" else lines)
        for key, lines in rows
    ]

# the elements of Details whose content is wider than their box, each as
# `<tag>.<class>` with its two widths
DETAILS_OVERFLOW_JS = """
() => Array.from(document.querySelectorAll('.bl-panel, .bl-panel *'))
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => [`${element.tagName.toLowerCase()}.${element.className}`,
                     element.scrollWidth, element.clientWidth])
"""

# the elements of Details whose text or hover holds the text given, each as
# `<tag>.<class>`
DETAILS_HOLDING_JS = """
(text) => Array.from(document.querySelectorAll('.bl-panel, .bl-panel *'))
  .filter((element) => element.textContent.includes(text)
    || (element.getAttribute('title') || '').includes(text))
  .map((element) => `${element.tagName.toLowerCase()}.${element.className}`)
"""

# Details of the durables model's stage occurrence periods[1]/adjuster_cons
# selected in the forward trellis graph of `declaration/spec.yml`, whose
# calibration the package refuses, and which `spec.two-stages.yml` uses
# too (design pass §2; unit K, Task 3): the head's text, then each row's
# key with the text of its lines
ADJUSTER_CONS_DETAILS = (
    "adjuster_cons periods[1] · age 69 forward",
    [
        ("file", ["declaration/stages/adjuster_cons/adjuster_cons.bl"]),
        ("bound", ["methodized · configured"]),
        ("periods", ["0–50"]),
        ("also", ["declaration/spec.two-stages.yml · periods 0–50"]),
        ("from", ["tenure (adjust) w_adj → m · z_adj → z_d"]),
        ("to", ["periods[0]/tenure a_nxt_adj → a · h_nxt_adj → h · z_nxt_adj → z"]),
        (
            "fields",
            [
                "∼ m ℝ₊₊ · z_d ℝ₊₊ · c ℝ₊₊ !ctrl · h_choice ℝ₊₊ !ctrl · V ℝ !vlu",
                "≻ a_nxt_adj ℝ₊ · h_nxt_adj ℝ₊₊ · z_nxt_adj ℝ₊₊ · V ℝ !vlu",
            ],
        ),
        # the occurrence's inputs, outputs and policies (design pass 10 §8; unit N, Task 7);
        # the stage begins at its decision perch and prints no inputs row (decision MB-U31)
        ("outputs", ["a_nxt_adj ℝ₊ · h_nxt_adj ℝ₊₊ · z_nxt_adj ℝ₊₊"]),
        ("policies", ["c ℝ₊₊ · h_choice ℝ₊₊"]),
        # each place of the version at which a component is typed, in the
        # package's order, with its method word (specification 0.7)
        ("methods", [
            "!Linear cntn_to_dcsn.evaluate[V] · !Linear cntn_to_dcsn.evaluate[D_{m}V] · "
            "!egm policy"
        ]),
        (
            "sources",
            [
                "declaration/calibration/durables.yml",
                "declaration/settings/durables.yml",
                "declaration/stages/adjuster_cons/methods.bl",
            ],
        ),
    ],
)

# Details of the join wire of the durables model's forward trellis graph
# from periods[1]/adjuster_cons to periods[0]/tenure, written by the one
# inter-period mapping of `declaration/trellis.yml`, whose other three keys
# join `keeper_cons` to the same arrival fields (design pass §2, "A join
# wire"; unit K, Task 4): the head's text, then each row's key with the
# text of its lines, a line of the table `fields` its cells
ADJUSTER_CONS_JOIN_DETAILS = ('join periods[1]/adjuster_cons → periods[0]/tenure forward',
 [('route', ['periods[1]/adjuster_cons ≻ → periods[0]/tenure ≺']),
  ('status', ['certified']),
  ('wires', ['a_nxt_adj → a ℝ₊ · authored, trellis.yml 20',
             'h_nxt_adj → h ℝ₊₊ · authored, trellis.yml 20',
             'z_nxt_adj → z ℝ₊₊ · authored, trellis.yml 20']),
  ('written', ['declaration/trellis.yml · inter_connectors[0]']),
  ('pairs', ['every adjacent pair (50)']),
  ('measure', ['μ≻', '→ μ≺']),
  ('fields', ['a_nxt_adj → a ℝ₊ 2 sources', 'h_nxt_adj → h ℝ₊₊ 2 sources', 'z_nxt_adj → z ℝ₊₊ 2 sources']),
  ('compatibility',
   ['adjuster_cons.a_nxt_adj → tenure.a: compatible; the continuation set of '
    'periods[1].adjuster_cons.a_nxt_adj and the arrival set of periods[0].tenure.a are one set, ℝ₊',
    'adjuster_cons.h_nxt_adj → tenure.h: compatible; the continuation set of '
    'periods[1].adjuster_cons.h_nxt_adj and the arrival set of periods[0].tenure.h are one set, ℝ₊₊',
    'adjuster_cons.z_nxt_adj → tenure.z: compatible; the continuation set of '
    'periods[1].adjuster_cons.z_nxt_adj and the arrival set of periods[0].tenure.z are one set, ℝ₊₊']),
  ('also', ['keeper_cons a_nxt_kp → a · h_nxt_kp → h · z_nxt_kp → z'])])
# Details of the join wire of the same graph within periods[0], from
# adjuster_cons to bequest, written by the one connector of that period,
# whose other three keys join `keeper_cons` to the same arrival fields
BEQUEST_JOIN_DETAILS = ('join periods[0]/adjuster_cons → periods[0]/bequest forward',
 [('route', ['periods[0]/adjuster_cons ≻ → periods[0]/bequest ≺']),
  ('status', ['certified']),
  ('wires', ['a_nxt_adj → a_bq ℝ₊ · authored, trellis.yml 12',
             'h_nxt_adj → h_bq ℝ₊₊ · authored, trellis.yml 12',
             'z_nxt_adj → z_bq ℝ₊₊ · authored, trellis.yml 12']),
  ('written', ['declaration/trellis.yml · periods[0].connectors[0]']),
  ('periods', ['0']),
  ('measure', ['μ≻', '→ μ≺']),
  ('fields',
   ['a_nxt_adj → a_bq ℝ₊ 2 sources', 'h_nxt_adj → h_bq ℝ₊₊ 2 sources', 'z_nxt_adj → z_bq ℝ₊₊ 2 sources']),
  ('compatibility',
   ['adjuster_cons.a_nxt_adj → bequest.a_bq: compatible; the continuation set of '
    'periods[0].adjuster_cons.a_nxt_adj and the arrival set of periods[0].bequest.a_bq are one set, ℝ₊',
    'adjuster_cons.h_nxt_adj → bequest.h_bq: compatible; the continuation set of '
    'periods[0].adjuster_cons.h_nxt_adj and the arrival set of periods[0].bequest.h_bq are one set, ℝ₊₊',
    'adjuster_cons.z_nxt_adj → bequest.z_bq: compatible; the continuation set of '
    'periods[0].adjuster_cons.z_nxt_adj and the arrival set of periods[0].bequest.z_bq are one set, ℝ₊₊']),
  ('also', ['keeper_cons a_nxt_kp → a_bq · h_nxt_kp → h_bq · z_nxt_kp → z_bq'])])
# Details of the piece that the two join wires of the same graph from
# periods[1] into periods[0]/tenure share between the two periods, which
# selects the pair's joins, every key of the one inter-period mapping (unit
# K, Task 7; K-D5): each writer's measure, the six joins, and no `also`
PAIR_JOIN_DETAILS = ('join periods[1] → periods[0]/tenure forward',
 [('route', ['periods[1]/keeper_cons ≻ → periods[0]/tenure ≺', 'periods[1]/adjuster_cons ≻ → periods[0]/tenure ≺']),
  ('status', ['certified', 'certified']),
  ('wires', ['a_nxt_kp → a ℝ₊ · authored, trellis.yml 20',
             'h_nxt_kp → h ℝ₊₊ · authored, trellis.yml 20',
             'z_nxt_kp → z ℝ₊₊ · authored, trellis.yml 20',
             'a_nxt_adj → a ℝ₊ · authored, trellis.yml 20',
             'h_nxt_adj → h ℝ₊₊ · authored, trellis.yml 20',
             'z_nxt_adj → z ℝ₊₊ · authored, trellis.yml 20']),
  ('written', ['declaration/trellis.yml · inter_connectors[0]']),
  ('pairs', ['every adjacent pair (50)']),
  ('measure', ['μ≻', 'μ≻', '→ μ≺']),
  ('fields',
   ['a_nxt_kp → a ℝ₊ 2 sources',
    'h_nxt_kp → h ℝ₊₊ 2 sources',
    'z_nxt_kp → z ℝ₊₊ 2 sources',
    'a_nxt_adj → a ℝ₊ 2 sources',
    'h_nxt_adj → h ℝ₊₊ 2 sources',
    'z_nxt_adj → z ℝ₊₊ 2 sources']),
  ('compatibility',
   ['keeper_cons.a_nxt_kp → tenure.a: compatible; the continuation set of periods[1].keeper_cons.a_nxt_kp '
    'and the arrival set of periods[0].tenure.a are one set, ℝ₊',
    'keeper_cons.h_nxt_kp → tenure.h: compatible; the continuation set of periods[1].keeper_cons.h_nxt_kp '
    'and the arrival set of periods[0].tenure.h are one set, ℝ₊₊',
    'keeper_cons.z_nxt_kp → tenure.z: compatible; the continuation set of periods[1].keeper_cons.z_nxt_kp '
    'and the arrival set of periods[0].tenure.z are one set, ℝ₊₊',
    'adjuster_cons.a_nxt_adj → tenure.a: compatible; the continuation set of '
    'periods[1].adjuster_cons.a_nxt_adj and the arrival set of periods[0].tenure.a are one set, ℝ₊',
    'adjuster_cons.h_nxt_adj → tenure.h: compatible; the continuation set of '
    'periods[1].adjuster_cons.h_nxt_adj and the arrival set of periods[0].tenure.h are one set, ℝ₊₊',
    'adjuster_cons.z_nxt_adj → tenure.z: compatible; the continuation set of '
    'periods[1].adjuster_cons.z_nxt_adj and the arrival set of periods[0].tenure.z are one set, ℝ₊₊'])])

CONTRIBUTION_JOIN_ROWS = [('route', ['periods[4]/contribution ≻ → periods[4]/allocation ≺']),
 ('status', ['certified']),
 ('wires',
  ['w_c → w_c ℝ₊ · inferred',
   'adc_c → adc_c ℝ₊ · inferred',
   'adc_pre_c → adc_pre_c ℝ₊ · inferred',
   'h_c → h_c ℝ₊ · inferred',
   'm_c → m_c ℝ₊ · inferred',
   'P_c → P_c ℝ₊₊ · inferred',
   'ξ_c → ξ_c ℝ · inferred',
   'α_c → α_c (0, 1) · inferred',
   'β_c → β_c (0, 1) · inferred',
   'plan_c → plan_c Plan · inferred']),
 ('written', ['joined by the names']),
 ('measure', ['μ≻', '→ μ≺']),
 ('fields',
  ['w_c ℝ₊',
   'adc_c ℝ₊',
   'adc_pre_c ℝ₊',
   'h_c ℝ₊',
   'm_c ℝ₊',
   'P_c ℝ₊₊',
   'ξ_c ℝ',
   'α_c (0, 1)',
   'β_c (0, 1)',
   'plan_c Plan']),
 ('compatibility',
  ['contribution.w_c → allocation.w_c: compatible; the continuation set of periods[4].contribution.w_c and '
   'the arrival set of periods[4].allocation.w_c are one set, ℝ₊',
   'contribution.adc_c → allocation.adc_c: compatible; the continuation set of periods[4].contribution.adc_c '
   'and the arrival set of periods[4].allocation.adc_c are one set, ℝ₊',
   'contribution.adc_pre_c → allocation.adc_pre_c: compatible; the continuation set of '
   'periods[4].contribution.adc_pre_c and the arrival set of periods[4].allocation.adc_pre_c are one set, ℝ₊',
   'contribution.h_c → allocation.h_c: compatible; the continuation set of periods[4].contribution.h_c and '
   'the arrival set of periods[4].allocation.h_c are one set, ℝ₊',
   'contribution.m_c → allocation.m_c: compatible; the continuation set of periods[4].contribution.m_c and '
   'the arrival set of periods[4].allocation.m_c are one set, ℝ₊',
   'contribution.P_c → allocation.P_c: compatible; the continuation set of periods[4].contribution.P_c and '
   'the arrival set of periods[4].allocation.P_c are one set, ℝ₊₊',
   'contribution.ξ_c → allocation.ξ_c: compatible; the continuation set of periods[4].contribution.ξ_c and '
   'the arrival set of periods[4].allocation.ξ_c are one set, ℝ',
   'contribution.α_c → allocation.α_c: compatible; the continuation set of periods[4].contribution.α_c and '
   'the arrival set of periods[4].allocation.α_c are one set, (0, 1)',
   'contribution.β_c → allocation.β_c: compatible; the continuation set of periods[4].contribution.β_c and '
   'the arrival set of periods[4].allocation.β_c are one set, (0, 1)',
   'contribution.plan_c → allocation.plan_c: compatible; the continuation set of '
   'periods[4].contribution.plan_c and the arrival set of periods[4].allocation.plan_c are one set, {DB, '
   'DC}'])]

# the durables model's stage file of the adjusting household's consumption
ADJUSTER_CONS_FILE = "declaration/stages/adjuster_cons/adjuster_cons.bl"

# Details of a selected box as the page prints it, outside the folds
# `cursor` and `legend`: the head's first line and its second,
# `.bl-panel-under`; each row's key as the row writes it, its data-key, which
# the page prints in sentence case (design pass 13 §3), with the text of each
# of its lines, `.bl-attribute-line`, or of its value where it has none; and
# each block of a rule or a kernel, its label with each of its lines as its
# parts; the spaces of every text run together
BOX_DETAILS_JS = """
() => {
  const text = (element) => element.textContent.split(/\\s+/).filter(Boolean).join(' ');
  const own = (element) => !element.closest('.bl-cursor-details, .bl-legend-details');
  const panel = document.querySelector('.bl-panel');
  const head = panel.querySelector('.bl-panel-head');
  let first = '', under = '';
  if (head) {
    const copy = head.cloneNode(true);
    const second = copy.querySelector('.bl-panel-under');
    if (second) {
      under = text(second);
      second.remove();
    }
    first = text(copy);
  }
  const rows = Array.from(panel.querySelectorAll('.bl-attribute')).filter(own).map((row) => {
    const value = row.querySelector('.bl-attribute-value');
    const lines = value.querySelectorAll('.bl-attribute-line');
    return [row.dataset.key, lines.length ? Array.from(lines, text) : [text(value)]];
  });
  const blocks = Array.from(panel.querySelectorAll('.bl-math')).filter(own).map((block) => [
    text(block.querySelector('.bl-math-label')),
    Array.from(block.querySelectorAll('.bl-math-line'),
               (line) => Array.from(line.querySelectorAll('.bl-math-part'), text)),
  ]);
  return [[first, under], rows, blocks];
}
"""

# the elements of Details whose content is wider than their box, each as
# `<tag>.<class>` with its two widths: every element outside the fold
# `cursor`, whose block record scrolls within its own box, and every value
# of a row, `.bl-attribute-value`, inside it or not
BOX_OVERFLOW_JS = """
() => Array.from(document.querySelectorAll('.bl-panel, .bl-panel *'))
  .filter((element) => !element.closest('.bl-cursor-details')
    || element.classList.contains('bl-attribute-value'))
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => [`${element.tagName.toLowerCase()}.${element.className}`,
                     element.scrollWidth, element.clientWidth])
"""

# the number of lines on which each port's perch and role stand in Details,
# outside the fold `cursor`, a word broken over two lines standing on two
BOX_PORT_WORD_LINES_JS = """
() => Array.from(document.querySelectorAll('.bl-panel .bl-port-perch, .bl-panel .bl-port-role'))
  .filter((element) => !element.closest('.bl-cursor-details'))
  .map((element) => [element.textContent, element.getClientRects().length])
"""

# Details of the box cntn_to_dcsn:Pullback of the durables model's
# adjuster_cons.bl, opened from the tree and bound as the folder's recipe
# binds it, with the box selected (design pass §2, "An operator box"; unit
# K, Task 5): the head's two lines, the rows, and the rule and the kernel,
# each line as the parts at which the display may break it
PULLBACK_DETAILS = (
    # the graph's direction in sentence case (design pass 13 §3)
    ["𝑉≻ ∘ 𝑔≻ Pullback Backward", "cntn_to_dcsn:Pullback ≻ → ∼"],
    [
        ["at", ["𝑐, ℎ_choice"]],
        ["lines", ["adjuster_cons.bl 18–20"]],
        ["reads", ["𝑉≻(a_nxt_adj, h_nxt_adj, z_nxt_adj)", "cntn · value"]],
        ["writes", ["𝑉≻(𝑔(m, z_d, 𝑐(m, z_d), ℎ_choice(m, z_d)))", "cntn · value"]],
        [
            "source",
            [
                "18 a_nxt_adj = m - c - (1 + τ)*h_choice",
                "19 h_nxt_adj = h_choice",
                "20 z_nxt_adj = z_d",
            ],
        ],
        ["uses", ["τ 8 · Γ_c 14 · Γ_h 15 · 𝑔≻ 18"]],
    ],
    [
        [
            "rule",
            [
                [
                    "(𝑉≻ ∘ 𝑔≻(·, ·, 𝑐, ℎ_choice))(m, z_d)",
                    "= 𝑉≻(𝑔≻(m, z_d, 𝑐(m, z_d), ℎ_choice(m, z_d)))",
                ]
            ],
        ],
        [
            "kernel",
            [
                [
                    "𝑔 of dcsn_to_cntn: 𝑔(m, z_d, c, h_choice)",
                    "= (m - c - (1 + τ)*h_choice, h_choice, z_d)",
                ],
                [
                    "outputs (a_nxt_adj≻, h_nxt_adj≻, z_nxt_adj≻);",
                    "a_nxt_adj≻ reads m, c, h_choice;",
                    "h_nxt_adj≻ reads h_choice;",
                    "z_nxt_adj≻ reads z_d",
                ],
            ],
        ],
    ],
)

# the keywords the durables model's recipe's slots take, in the order the
# recipe first writes each, as the line `slots` under the recipe's blocks
# prints them (unit K, K-D29; design pass 2 §11): `$fill` alone, since a
# methods list names additions and no slot (decision S7-F3)
DURABLES_SLOT_KEYWORDS = ["fill"]

# the verbs applied of the trellis's status line for the durables model's
# recipe, with their separator, which stand in its line after `trellis`
# where the line with them fits (spec 0.4 §5.7; unit K, Task 6)
DURABLES_STATUS_BOUND = " · methodized, configured"
# the rest of the same status line, periods 0–2, its parts after the loop's
# seconds (design pass §1 item 10; unit K, Task 6): the periods and the
# occurrences, and the unjoined fields of the forward graph
DURABLES_STATUS_REST = " · 51 periods, 154 occurrences · 0 unjoined internal entry fields"

# The trellis's status line and the checklist, read at one moment: the
# visible line's text; the text of the trellis's parts in the details'
# line, the rest headed by the verbs applied where they stand there, else
# null; whether the visible line holds the rest; and the elements of the
# visible line and of the checklist's items, each a row with its label
# (design pass 8 §6; unit M, Task 6), whose content is wider than their
# box, each as `<tag>.<class>` with its text and its two widths.
TRELLIS_STATUS_FIT_JS = """
() => {
  const line = document.querySelector('.bl-status-summary .bl-trellis-status');
  const rest = document.querySelector('.bl-status-line .bl-trellis-rest');
  const overflowing = Array.from(document.querySelectorAll(
      '.bl-trellis-status, .bl-checklist-list .bl-row, .bl-checklist-list .bl-row > span'))
    .filter((element) => element.scrollWidth > element.clientWidth)
    .map((element) => [`${element.tagName.toLowerCase()}.${element.className}`,
                       element.textContent, element.scrollWidth, element.clientWidth]);
  return [line ? line.textContent : null, rest ? rest.textContent : null,
          line !== null && line.querySelector('.bl-trellis-rest') !== null, overflowing];
}
"""

# the items of the checklist, each a row (design pass 8 §6; unit M, Task
# 6), each its text and its hover
CHECKLIST_ITEMS_JS = """
() => Array.from(document.querySelectorAll('.bl-checklist-list .bl-row'))
  .map((item) => [item.textContent.trim(), item.getAttribute('title')])
"""

# the type of the first element of each selector given, as the browser
# computes it: its family, size, weight, letter spacing and case
TYPE_FACES_JS = """
(selectors) => selectors.map((selector) => {
  const style = getComputedStyle(document.querySelector(selector));
  return [style.fontFamily, style.fontSize, style.fontWeight, style.letterSpacing,
          style.textTransform];
})
"""

# every name the tree draws, of a file or a folder (unit L, Task 22): its
# row's path, its text, the text of the words the browser draws, whether
# words follow them, the room in pixels between the last of them and the
# name's right edge, null where none is drawn, the width of an ellipsis in
# the name's face, and the width of the row's mark, git's letters and the
# word `unsaved`, with the width of its text. The name stands on one line
# of inline blocks, one word each, cut by `text-overflow` (the delegated
# acceptance of unit M, D1): where its words run past its right edge, the
# browser draws the ellipsis and hides whole each word that ends past the
# ellipsis's start, as CSS Overflow 3 has it for atomic inline boxes, so
# that the words drawn are those before the first that ends past that
# start, and all of them where the words fit.
TREE_NAMES_JS = r"""
() => {
  const canvas = document.createElement('canvas').getContext('2d');
  return Array.from(document.querySelectorAll('.bl-tree .bl-tree-name'), (name) => {
    const row = name.closest('.bl-tree-file, .bl-folder-row');
    const words = Array.from(name.querySelectorAll('.bl-name-word'), (word) => ({
      text: word.textContent, right: word.getBoundingClientRect().right,
    }));
    const style = getComputedStyle(name);
    canvas.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
    const ellipsis = canvas.measureText('…').width;
    const right = name.getBoundingClientRect().right;
    const over = words.length > 0 && words[words.length - 1].right - right > 0.01;
    const end = over ? right - ellipsis : right;
    const drawn = [];
    for (const word of words) {
      if (word.right > end + 0.5) break;
      drawn.push(word);
    }
    const mark = row.querySelector('.bl-tree-mark');
    return {path: row.dataset.path, name: name.textContent,
            shown: drawn.map((word) => word.text).join(''), cut: drawn.length < words.length,
            room: drawn.length ? right - drawn[drawn.length - 1].right : null, ellipsis,
            mark: mark ? [mark.clientWidth, mark.scrollWidth] : null};
  });
}
"""


def tree_names(page) -> list[dict]:
    """Every name the tree draws, as TREE_NAMES_JS reads it."""
    return page.evaluate(TREE_NAMES_JS)


def cut_within_a_word(name: dict) -> bool:
    """Whether the tree's name `name` (`tree_names`) is cut within a word:
    the browser draws none of its words, its first word with an ellipsis
    being wider than the name, or the last word it draws runs past the
    name's right edge (unit L, Task 22)."""
    return name["room"] is None or name["room"] < -0.5


# the editor's document, which the bundle answers, since a hidden span is
# not in the DOM
DOCUMENT_JS = "() => window.bellmanEditor.documentOf(document.querySelector('.bl-editor'))"

# the write-back of the classification table driven from the page: the
# bundle's replaceSpansOf over [edits, expected], answering whether the
# editor applied the edits
REPLACE_SPANS_JS = """
([edits, expected]) => window.bellmanEditor.replaceSpansOf(
  document.querySelector('.bl-editor'), edits, expected)
"""

# the rows of the classification table as the page shows them: each row's
# perch, group, field, set, role and line, the line the data-line of the
# field's button (unit R, R-D23)
TABLE_ROWS_JS = """
() => Array.from(document.querySelectorAll('.bl-class-row')).map((row) => ({
  perch: row.closest('.bl-class-perch').dataset.perch,
  group: row.closest('.bl-class-group').dataset.group,
  field: row.querySelector('.bl-class-field').textContent,
  set: row.querySelector('.bl-class-set').value,
  role: row.querySelector('.bl-class-role').value,
  line: row.querySelector('.bl-class-field').dataset.line || null,
}))
"""

# The text drawn under a selector, without the text of style and script elements
DRAWN_TEXT_JS = """
(selector) => {
  const out = [];
  const walk = (node) => {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) out.push(child.textContent);
      else if (child.nodeType === Node.ELEMENT_NODE) {
        const name = child.tagName.toLowerCase();
        if (name === 'style' || name === 'script') continue;
        walk(child);
      }
    }
  };
  walk(document.querySelector(selector));
  return out.join(' ');
}
"""

# each visual line of the editor's line `n`, counted from one, as
# `{count, left}`: the number of its characters and the least left edge, in
# pixels, of their boxes, a visual line being the characters whose boxes
# share a top
VISUAL_LINES_JS = """
(n) => {
  const line = document.querySelectorAll('.cm-content .cm-line')[n - 1];
  const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
  const rows = new Map();
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    for (let i = 0; i < node.length; i++) {
      const range = document.createRange();
      range.setStart(node, i);
      range.setEnd(node, i + 1);
      const box = range.getClientRects()[0];
      if (!box) continue;
      const top = Math.round(box.top);
      const row = rows.get(top) || {count: 0, left: box.left};
      row.count += 1;
      row.left = Math.min(row.left, box.left);
      rows.set(top, row);
    }
  }
  return Array.from(rows.entries()).sort((a, b) => a[0] - b[0]).map((entry) => entry[1]);
}
"""

# the width of the text of the editor's line 13, its paddings left out,
# and the width of one character of it (line 13 of cons.bl is ASCII, drawn
# in the monospaced face on one visual line)
TEXT_WIDTH_JS = """
() => {
  const line = document.querySelectorAll('.cm-content .cm-line')[12];
  const style = getComputedStyle(line);
  const width = line.clientWidth - parseFloat(style.paddingLeft)
    - parseFloat(style.paddingRight);
  const range = document.createRange();
  range.selectNodeContents(line);
  return [width, range.getBoundingClientRect().width / line.textContent.length];
}
"""

# the computed background image of the editor's content, on which no
# guide after column 78 is drawn (spec 0.4 §5.4)
GUIDE_JS = "() => getComputedStyle(document.querySelector('.cm-content')).backgroundImage"

# stand-ins of the clipboard's writeText: one records the text in
# window.copiedText, one refuses it as a browser does
CLIPBOARD_RECORDS_JS = """
() => {
  window.copiedText = null;
  navigator.clipboard.writeText = (text) => {
    window.copiedText = text;
    return Promise.resolve();
  };
}
"""
CLIPBOARD_REFUSES_JS = """
() => {
  navigator.clipboard.writeText = () =>
    Promise.reject(new DOMException('the clipboard is refused', 'NotAllowedError'));
}
"""

# An ELK stand-in that refuses every layout (G-D9).
REFUSING_ELK_JS = """
() => {
  window.ELK = class {
    layout() {
      return Promise.reject(new Error('the stand-in refuses'));
    }
  };
}
"""

# the rows of the selected piece in the panel, each as [key, value]: the
# rows outside the fold `cursor`, which holds the rows of the builder of
# the block under the cursor (unit K, Task 5)
ATTRIBUTE_ROWS_JS = """
() => Array.from(document.querySelectorAll('.bl-attribute'))
  .filter((row) => !row.closest('.bl-cursor-details'))
  .map((row) => [row.dataset.key, row.querySelector('.bl-attribute-value').textContent])
"""

# the ports of the panel, `.bl-port` items of the rows `reads` and `writes`
# or `inputs` and `outputs` (unit K, Task 5), each as its cells, [label,
# perch, type, role], the type read from the label's hover and the empty
# text for a part the port does not print, followed in the trellis view by
# the join, the rule that paired it and the occurrence outside the view
# where the port prints them; with the perch's title
PORT_ROWS_JS = """
() => Array.from(document.querySelectorAll('.bl-panel .bl-port')).map((port) => {
  const read = (selector) => {
    const found = port.querySelector(selector);
    return found ? found.textContent : null;
  };
  const joined = ['.bl-port-join', '.bl-port-paired-by', '.bl-port-outside']
    .map(read).filter((value) => value !== null);
  const perch = port.querySelector('.bl-port-perch');
  return {
    cells: [read('.bl-port-label'), read('.bl-port-perch') ?? '',
            port.querySelector('.bl-port-label').getAttribute('title') ?? '',
            read('.bl-port-role') ?? '', ...joined],
    perch_title: perch ? perch.getAttribute('title') : null,
  };
})
"""

# The elements of the page drawn in the brand's orange, #ED762D, in their
# color, their ground, a border or an outline, each as `<tag>.<class>
# <property>`; the viewer's shadow roots are not entered, since the viewer
# draws its graph on a canvas.
ORANGE_ELEMENTS_JS = """
() => {
  const orange = 'rgb(237, 118, 45)';
  const properties = ['color', 'background-color', 'border-top-color', 'border-right-color',
                      'border-bottom-color', 'border-left-color', 'outline-color'];
  const found = [];
  for (const element of document.querySelectorAll('.bl-window *')) {
    const style = getComputedStyle(element);
    for (const property of properties) {
      if (style.getPropertyValue(property) === orange) {
        const name = element.getAttribute('class');
        found.push(`${element.tagName.toLowerCase()}.${name} ${property}`);
      }
    }
  }
  return found;
}
"""

# a button as the page shows it: its text, its title (the hover text), its
# aria-label, and the face and the size of its text as the browser computes
# them
BUTTON_SHOWN_JS = """
(button) => ({
  text: button.textContent,
  title: button.getAttribute('title'),
  label: button.label === undefined ? button.getAttribute('aria-label') : button.label,
  face: getComputedStyle(button).fontFamily,
  size: getComputedStyle(button).fontSize,
})
"""

# The lines of the list under the error mark (AMD-MI-002 §6a rule 1), read
# whether the list is open or closed, newest first: each line's sentence,
# the file of its link or the file it names alone, and the line of its
# link, each null where the line names none.
ERROR_LINES_JS = """
() => Array.from(document.querySelectorAll('.bl-error-list .bl-error-line')).map((line) => {
  const link = line.querySelector('.bl-error-place');
  const file = line.querySelector('.bl-error-file');
  return [
    line.querySelector('.bl-error-sentence').textContent,
    link ? link.dataset.path : (file ? file.textContent : null),
    link ? Number(link.dataset.line) : null,
  ];
})
"""

# the lines of one group of the list under the error mark, the group named
# by its heading, `Errors`, `Connections to check` or `Headers to check`,
# each line the triple ERROR_LINES_JS gives
ERROR_GROUP_LINES_JS = """
(label) => Array.from(document.querySelectorAll('.bl-error-list .bl-problem-group'))
  .filter((group) => group.querySelector('.bl-problem-heading').textContent === label)
  .flatMap((group) => Array.from(group.querySelectorAll('.bl-error-line')).map((line) => {
    const link = line.querySelector('.bl-error-place');
    const file = line.querySelector('.bl-error-file');
    return [
      line.querySelector('.bl-error-sentence').textContent,
      link ? link.dataset.path : (file ? file.textContent : null),
      link ? Number(link.dataset.line) : null,
    ];
  }))
"""

# the color of the error mark as the browser computes it
ERROR_MARK_COLOR_JS = "() => getComputedStyle(document.querySelector('.bl-error-mark')).color"

# The brand's orange, the accent of a refusal, and ink-3, the color of a
# quiet mark (design pass 8 §6), as the browser computes a color
# (brand.css).
ORANGE = "rgb(237, 118, 45)"
INK_3 = "rgb(145, 190, 215)"


# --- the folders ---


def _git(root: Path, *arguments: str) -> None:
    """Runs `git <arguments>` in `root` and raises on a non-zero exit."""
    subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )


def init_repository(target: Path) -> Path:
    """Makes the folder `target` a git repository with one commit of every
    file; the git user is configured in that repository alone."""
    _git(target, "init", "-q")
    _git(target, "config", "user.name", "bellman-workbench tests")
    _git(target, "config", "user.email", "tests@bellman-workbench.invalid")
    _git(target, "add", "--all")
    _git(target, "commit", "-q", "-m", "the application as copied")
    return target


def repository_copy(source: Path, target: Path, ignore=("__pycache__",)) -> Path:
    """A copy of the folder `source` at `target`, the names `ignore` lists left
    out, made a git repository with one commit of every file."""
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(*ignore))
    return init_repository(target)


def filled(text: str) -> str:
    """The recipe's text with each slot of DEMO_FILLS replaced by its
    source, `[$disc_settings]` by the empty list `[]`."""
    for slot, source in DEMO_FILLS.items():
        text = text.replace(f"[${slot}]", f"[{source}]" if source else "[]")
    return text


def written_from_the_forms(folder: Path, stages=DEMO_STAGES, repeat: int = 6) -> Path:
    """`folder` holding, by the forms of `creation` alone, what "new
    trellis" writes but the companion files: the stage files of `stages`
    copied from their templates, the recipe, whose methods lists are empty
    since no addition is copied, the period file, the trellis file and
    answers.yml, each where `create_trellis` writes it
    (`creation.factory_path`, `creation.stage_file`). Answers the
    folder."""
    from bellman_workbench import creation

    keys = [key for key, _ in stages]
    for key, template_id in stages:
        target = folder / creation.factory_path(creation.stage_file(key))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(creation.template_of(template_id).stage, target)
    texts = {
        creation.factory_path(creation.RECIPE): creation.recipe_text(
            folder.name, [(key, ()) for key in keys]
        ),
        creation.factory_path(creation.PERIOD): creation.period_text("demo_period", keys),
        creation.factory_path(creation.TRELLIS): creation.trellis_text("demo", repeat),
        creation.ANSWERS: creation.answers_text(folder.name, None, "demo_period", repeat, stages),
    }
    for name, text in texts.items():
        (folder / name).write_text(text, encoding="utf-8")
    return folder


def stage_files() -> list[Path]:
    """The stage files of the applications, `STAGE_FILES` of
    `packages/bellman/tests/conftest.py`, the one listing of them: every
    tracked `.bl` file under `applications/` whose first line is `@stage:`,
    an addition beside a stage file being none. The module is loaded from
    its file under the name `bellman_tests_conftest`, since the name
    `conftest` stands for this folder's own (see `conftest.py`)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "bellman_tests_conftest", ROOT / "packages/bellman/tests/conftest.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.STAGE_FILES


def layout_faults_of(folder: Path) -> list[str]:
    """The faults of the files under `folder` against the one layout of a
    model folder, one sentence each, by the layout's own check,
    `layout_faults` of `packages/bellman/tests/test_layout.py`, which reads
    paths from the repository's root under `applications/`: each file is
    given as `applications/<the folder's name>/<its path from the
    folder>`, git's own folder left out. The module is loaded from its file
    under the name `bellman_layout_rule`. Its import `from conftest import
    ROOT` names the package tests' `conftest`, while the name `conftest`
    stands for this folder's own (see `conftest.py`); during the load the
    name stands for a module holding ROOT alone, and is given back after
    it."""
    import importlib.util
    import types

    spec = importlib.util.spec_from_file_location(
        "bellman_layout_rule", ROOT / "packages/bellman/tests/test_layout.py"
    )
    rule = importlib.util.module_from_spec(spec)
    stand_in = types.ModuleType("conftest")
    stand_in.ROOT = ROOT
    held = sys.modules.get("conftest")
    sys.modules["conftest"] = stand_in
    try:
        spec.loader.exec_module(rule)
    finally:
        if held is None:
            del sys.modules["conftest"]
        else:
            sys.modules["conftest"] = held
    paths = sorted(
        f"applications/{folder.name}/{path.relative_to(folder).as_posix()}"
        for path in folder.rglob("*")
        if path.is_file() and path.relative_to(folder).parts[0] != ".git"
    )
    return rule.layout_faults(paths)


def file_bytes(folder: Path) -> dict[str, bytes]:
    """The bytes of every file under `folder`, by its posix path from the
    folder, git's own folder left out."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file() and path.relative_to(folder).parts[0] != ".git"
    }


def without_file_provenance(answer: dict) -> dict:
    """A copy of `answer`, a syntactic trellis that `load_recipe` answers,
    without the path and the digest of the recipe and of the trellis file
    under `provenance`, which differ between a variant and its source by
    construction (ruling R24 of the model folder's layout); the answer
    names no period file. Every other value is kept as it stands."""
    copied = copy.deepcopy(answer)
    del copied["provenance"]["recipe"], copied["provenance"]["trellis"]
    return copied


@pytest.fixture(scope="session")
def cons_text() -> str:
    """The text of
    `applications/portfolio-choice/declaration/stages/cons/cons.bl`."""
    return (ROOT / CONS_PATH).read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def cons(cons_text):
    """The stage of `cons.bl`, elaborated from its text with the file's
    path in the repository as its origin."""
    from bellman.stage import elaborate_text

    return elaborate_text(cons_text, CONS_PATH)


@pytest.fixture(scope="session")
def entrepreneur_death():
    """The elaboration of `entrepreneur_death.bl` from its text with the
    file's path in the repository as its origin: its forward builders
    graph is refused and its backward graph constructed."""
    from bellman_workbench import model

    text = (ROOT / ENTREPRENEUR_DEATH_PATH).read_text(encoding="utf-8")
    return model.elaborate_buffer(text, ENTREPRENEUR_DEATH_PATH)


@pytest.fixture(scope="session")
def model_folder(tmp_path_factory) -> Path:
    """A copy of `applications/portfolio-choice/` as a fresh git repository
    with one commit, made once per session."""
    return repository_copy(PORTFOLIO_CHOICE, tmp_path_factory.mktemp("model") / "portfolio-choice")


@pytest.fixture(scope="session")
def pension_folder(tmp_path_factory) -> Path:
    """A copy of `applications/pension-retirement/` as a fresh git
    repository with one commit, made once per session; its recipe binds
    `declaration/stages/worker_saving/worker_saving.bl` as
    `periods[0] / worker_saving`."""
    return repository_copy(
        PENSION_RETIREMENT, tmp_path_factory.mktemp("pension") / "pension-retirement"
    )


@pytest.fixture(scope="session")
def cagetti_folder(tmp_path_factory) -> Path:
    """A copy of `applications/cagetti-denardi-2006/` as a fresh git
    repository with one commit, made once per session; the construction
    refuses the forward builders graph of its `entrepreneur_death.bl`."""
    return repository_copy(
        CAGETTI_DENARDI, tmp_path_factory.mktemp("cagetti") / "cagetti-denardi-2006"
    )


@pytest.fixture(scope="session")
def retirement_folder(tmp_path_factory) -> Path:
    """A copy of `applications/retirement-choice/` as a fresh git
    repository with one commit, made once per session; its stage
    `declaration/stages/ret_choice/ret_choice.bl` branches into `work` and
    `retire`."""
    return repository_copy(
        RETIREMENT_CHOICE, tmp_path_factory.mktemp("retirement") / "retirement-choice"
    )


# The pension model the post-doc of the UX simulation of 8 October 2026 built
# through the page as a second recipe of the durables folder, at its first
# construction: the recipe `spec.pensions.yml`, its trellis file of three
# periods, whose periods[0] holds `shocks` and `bequest_pa` joined by one
# connector of five pairs, its period file and its seven stage files, as the
# page wrote them (unit L, Task 14).
PENSIONS = Path(__file__).resolve().parent / "fixtures" / "pensions"
PENSIONS_RECIPE = "declaration/spec.pensions.yml"
PENSIONS_TRELLIS = "declaration/trellis.pensions.yml"
# The same pension model at its first build of the working years, which the
# post-doc read in 15.7 s (step 53 of the record): the recipe and the trellis
# file of seven periods as the record's `texts/57-spec.pensions-v3.yml` and
# `texts/56-trellis.pensions-v3.yml` write them, in which periods[4] and
# periods[5] are working years whose `contribution` and `allocation` are
# joined by equal names alone; the period file, the eleven stage files, the
# methods files and the calibration files that recipe names as the model
# was left (`model/`). The trellis file differs from the record's in one
# key: the year of retirement, periods[3], writes its own empty connectors
# list, so that a connector the working years take does not reach a period
# without those two stages (unit L, Task 15).
PENSIONS_WORKING_YEARS = Path(__file__).resolve().parent / "fixtures" / "pensions-working-years"
# The same pension model as the post-doc left it, eighty-five periods and
# 686 stage occurrences (the record's `model/`): the recipe, the trellis
# file and the renter's settings file of `model/`, laid over the files of
# PENSIONS_WORKING_YEARS, which equal those of `model/` byte for byte; the
# two files `model/` holds that no trellis reads, `period.extra_year.yml`
# and `stages/bequest_dur/`, are left out (unit L, Task 20).
PENSIONS_LIFE_CYCLE = Path(__file__).resolve().parent / "fixtures" / "pensions-life-cycle"


def pensions_copy(target: Path, fixture: Path = PENSIONS) -> Path:
    """A copy of the durables model at `target`, a fresh git repository
    with one commit (`repository_copy`), holding beside its own files the
    pension model's files of the UX simulation, at its first construction
    (PENSIONS) or as `fixture` holds them, untracked, as the page left them
    in the durables folder; answers the copy."""
    folder = repository_copy(DURABLES, target)
    shutil.copytree(fixture / "declaration", folder / "declaration", dirs_exist_ok=True)
    return folder


def pensions_life_cycle(target: Path) -> Path:
    """The copy `pensions_copy` of the pension model of eighty-five periods
    as the UX simulation's post-doc left it (PENSIONS_LIFE_CYCLE); answers
    the copy."""
    folder = pensions_copy(target, PENSIONS_WORKING_YEARS)
    shutil.copytree(
        PENSIONS_LIFE_CYCLE / "declaration", folder / "declaration", dirs_exist_ok=True
    )
    return folder


# the stages of the pension model's periods[0] as its trellis file lists them
PENSIONS_TERMINAL = "stages: [shocks, bequest_pa]"


def pensions_with_bequest_dur(target: Path) -> Path:
    """A pension connector fixture with a second bequest stage. The copied durables bequest admits zero housing, matching the pension source; authored targets identify bequest_pa explicitly where both stages use the same local name. Other stage and recipe source text is retained."""
    folder = pensions_copy(target)
    stage = folder / "declaration/stages/bequest_dur/bequest_dur.bl"
    stage.parent.mkdir(parents=True)
    durables = (folder / "declaration/stages/bequest/bequest.bl").read_text(encoding="utf-8")
    assert durables.startswith("@stage: bequest\n")
    # This connector fixture admits zero housing, as the pension source does.
    stage.write_text(durables.replace("@stage: bequest", "@stage: bequest_dur", 1)
                     .replace("h_bq : ℝ₊₊", "h_bq : ℝ₊"), "utf-8")
    recipe_file, trellis_file = folder / PENSIONS_RECIPE, folder / PENSIONS_TRELLIS
    row = (
        "  bequest_dur: {stage: stages/bequest_dur/bequest_dur.bl, calibration: {all: "
        "[$bequest_dur_calibration]}, settings: {all: [$bequest_dur_settings]}, methods: {all: "
        "[]}}\n"
    )
    text = recipe_file.read_text(encoding="utf-8")
    assert text.count("registry:") == 1
    recipe_file.write_text(text.replace("registry:", row + "registry:"), encoding="utf-8")
    text = trellis_file.read_text(encoding="utf-8")
    assert text.count(PENSIONS_TERMINAL) == 1
    trellis_file.write_text(
        text.replace(PENSIONS_TERMINAL, "stages: [shocks, bequest_pa, bequest_dur]")
            .replace("a_s: a_bq", "a_s: bequest_pa.a_bq")
            .replace("h_s: h_bq", "h_s: bequest_pa.h_bq"),
        encoding="utf-8",
    )
    return folder


def pensions_two_templates(target: Path) -> Path:
    """The copy `pensions_copy` of the pension model at its first build of
    the working years (PENSIONS_WORKING_YEARS), whose trellis file names
    two period templates: the working years, periods[4] and periods[5],
    read `period.working.yml`, a copy of `period.pensions.yml` named
    `pension_working_period`, and the other periods `period.pensions.yml`
    (unit G2), and without the stages' additions (`without_additions`),
    since the service does not accept the job for a folder that holds one
    (decision S7-W5). Answers the copy."""
    folder = without_additions(pensions_copy(target, PENSIONS_WORKING_YEARS))
    declaration = folder / "declaration"
    period = (declaration / "period.pensions.yml").read_text(encoding="utf-8")
    assert period.count("name: pension_period") == 1
    (declaration / "period.working.yml").write_text(
        period.replace("name: pension_period", "name: pension_working_period"), encoding="utf-8"
    )
    trellis_file = declaration / "trellis.pensions.yml"
    text = trellis_file.read_text(encoding="utf-8")
    working = "  - {template: period.pensions.yml, repeat: 2}\n"
    assert text.count(working) == 1
    trellis_file.write_text(
        text.replace(working, "  - {template: period.working.yml, repeat: 2}\n"), encoding="utf-8"
    )
    return folder


def applications_copy(target: Path) -> Path:
    """Copies of `applications/cons-port/`, its code, notebooks and
    `reference/` left out, and of `applications/portfolio-choice/` beside it
    under `target`: the files cons-port's trellis files read, those of its
    `declaration/` and the stage files and the discount stage's methods file
    under `../../portfolio-choice/declaration/stages/`, which resolve from
    the copy's `declaration/`, and the demonstration's `declaration/`
    (`demonstration_beside`); the cons-port copy is a fresh git repository
    with one commit. Answers the cons-port copy."""
    shutil.copytree(
        PORTFOLIO_CHOICE,
        target / "portfolio-choice",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    return demonstration_beside(
        repository_copy(
            CONS_PORT,
            target / "cons-port",
            ignore=("__pycache__", "code", "notebooks", "reference"),
        )
    )


def demonstration_beside(folder: Path) -> Path:
    """Answers `folder`. Until 28 October 2026 this copied the earlier
    demonstration folder's `declaration/` beside a copy of cons-port, whose
    trellis files named that folder's consumption stage file and block file
    outside cons-port (decision SD-39); the two folders are one, and every
    file cons-port's recipes and trellis files name stands inside it."""
    return folder


# the folders of the application corpus whose files `creation.TEMPLATE_SOURCES`
# reads, and the lines of the portfolio model's cons.bl, by their ids, that
# define its policy `c`
TEMPLATE_APPLICATIONS = ("cons-port", "portfolio-choice", "pension-retirement")
CONS_POLICY_LINES = ("[id=optimality", "[id=cons_choice]")


def refused_corpus(target: Path) -> Path:
    """A copy, under `target`, of the three folders of the application
    corpus whose files `creation.TEMPLATE_SOURCES` reads, each folder's
    `declaration/` with its pages `economics.md` and `README.md`, in which the
    portfolio model's `cons.bl` holds neither line that defines its policy
    `c` (CONS_POLICY_LINES), so that the package refuses it under
    `output-defined`, as the UX simulation of 8 October 2026 found the corpus
    (its defect 1); the demonstration's `declaration/` stands beside the
    cons-port copy (`demonstration_beside`). Answers `target`, the copy's
    corpus folder."""
    for name in TEMPLATE_APPLICATIONS:
        source = ROOT / "applications" / name
        shutil.copytree(
            source / "declaration",
            target / name / "declaration",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        for page in ("economics.md", "README.md"):
            if (source / page).is_file():
                shutil.copyfile(source / page, target / name / page)
    demonstration_beside(target / "cons-port")
    cons = target / "portfolio-choice/declaration/stages/cons/cons.bl"
    lines = cons.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if not any(mark in line for mark in CONS_POLICY_LINES)]
    cons.write_text("".join(kept), encoding="utf-8")
    return target


def corpus_startup(site: Path, corpus: Path) -> Path:
    """The folder `site` holding a `sitecustomize.py`, which Python runs at
    the start of every process whose `PYTHONPATH` names `site`, and which
    makes `corpus` the application corpus of `creation`, `creation.CORPUS`,
    so that a server started with that `PYTHONPATH` reads its templates from
    `corpus` (unit L, Task 13). The file is written for the test alone, in
    its temporary folder. Answers `site`."""
    site.mkdir(parents=True, exist_ok=True)
    (site / "sitecustomize.py").write_text(
        "# The corpus of the templates a test of Bellman Workbench names.\n"
        "from pathlib import Path\n\n"
        "from bellman_workbench import creation\n\n"
        f"creation.CORPUS = Path({str(corpus)!r})\n",
        encoding="utf-8",
    )
    return site


# The lifecycle registry of unit B's tests, the folder the form of "New
# trellis" writes (specification §4), in the one layout of a model folder:
# the portfolio model's three stage files, each with its addition beside
# it, `stages/<key>/methods.bl`, the consumption stage with a replacing
# selection `methods.vfi.bl` as well (decision S7-W2), the discount stage's
# settings a slot, the portfolio stage with no settings list, since its
# addition declares none, the discount factor of the terminal period its own, the
# connector from the portfolio stage to consumption left empty, and the
# form's answers marking the slot and the connector required (decision
# B-D2). The recipe, the period file and the trellis file stand in
# `declaration/`, and the recipe writes each path from that folder.
LIFECYCLE_RECIPE = """\
# The recipe of the lifecycle registry: for each stage and each kind, the
# ordered sources. The discount stage's settings are a slot.
trellis: trellis.yml
stages:
  port: {stage: stages/port/port.bl, calibration: {all: [calibration/portfolio]}, methods: {all: [stages/port/methods.bl]}}
  cons: {stage: stages/cons/cons.bl, calibration: {all: [calibration/portfolio]}, settings: {all: [settings/cons]}, methods: {all: [stages/cons/methods.bl]}}
  # the discount factor of the terminal period is its own
  disc: {stage: stages/disc/disc.bl, calibration: {all: [calibration/portfolio], 0-0: [calibration/terminal]}, settings: {all: [$disc_settings]}, methods: {all: [stages/disc/methods.bl]}}
"""  # noqa: E501  (the recipe writes each stage's row on one line)
LIFECYCLE_PERIOD = """\
!period
name: lifecycle_period
# The portfolio choice, consumption, then discounting; the connector from the
# portfolio stage's resources to consumption's is left to fill.
stages:
  - port
  - cons
  - disc
connectors:
  - {}
"""
LIFECYCLE_TRELLIS = """\
!trellis
name: lifecycle
# Three periods of the template; the savings that leave a period are the
# capital of the period before it in the list, the next date.
periods:
  - {template: period.yml, repeat: 3}
inter_connectors:
  - {disc.a: k}
"""
# the form's answers, written at the folder's top, where the checklist
# reads them
LIFECYCLE_ANSWERS = """\
# The entries the form of a new model holds required (decision B-D2).
required:
  slots: [disc_settings]
  connectors:
    - {file: declaration/period.yml, address: "connectors[0]"}
"""
TERMINAL_CALIBRATION = (
    "# The discount factor of the terminal period alone.\ncalibration:\n  β: 0.9\n"
)


# the additions of the lifecycle registry, the Workbench's own copies of the
# case studies' additions of the portfolio model's stages and of cons-port's
# consumption stage (specification 0.7; decision S7-W2), each beside the
# stage file it is unioned with
LIFECYCLE_ADDITIONS = Path(__file__).resolve().parent / "fixtures" / "lifecycle"


def lifecycle_registry(target: Path) -> Path:
    """The lifecycle registry at `target`, in the one layout of a model
    folder (the page Model directory layout), a fresh git repository with
    one commit. Its `declaration/` holds the stage folders `stages/port/`,
    `stages/cons/` and `stages/disc/`, each with the stage file of the
    portfolio model and the addition `methods.bl` of LIFECYCLE_ADDITIONS,
    `stages/cons/` also with the replacing selection `methods.vfi.bl`;
    `calibration/portfolio.yml` and the terminal period's
    `calibration/terminal.yml`; `settings/cons.yml`, cons-port's wide
    grids with the candidate count `n_c` the replacing selection declares;
    and
    `spec.yml`, `period.yml` and `trellis.yml` as the constants above write
    them. Its top holds `answers.yml`, which names the period file of its
    required connector by its path from the folder, `declaration/period.yml`,
    the rule `creation.answers_text` states. The consumption stage's
    additions are the portfolio model's, the endogenous grid method with its
    lines and the value function iteration; the discount stage's is the
    portfolio model's own, and the portfolio stage's declares no setting,
    so that the recipe lists no settings source for it."""
    declaration = target / "declaration"
    for key in ("port", "cons", "disc"):
        (declaration / "stages" / key).mkdir(parents=True)
        shutil.copy(
            PORTFOLIO_CHOICE / f"declaration/stages/{key}/{key}.bl",
            declaration / "stages" / key / f"{key}.bl",
        )
        for addition in sorted((LIFECYCLE_ADDITIONS / "stages" / key).glob("methods*.bl")):
            shutil.copy(addition, declaration / "stages" / key / addition.name)
    for folder in ("calibration", "settings"):
        (declaration / folder).mkdir()
    corpus = CONS_PORT / "declaration"
    shutil.copy(corpus / "calibration/portfolio.yml", declaration / "calibration/portfolio.yml")
    (declaration / "calibration/terminal.yml").write_text(TERMINAL_CALIBRATION, encoding="utf-8")
    shutil.copy(corpus / "settings/cons_wide.yml", declaration / "settings/cons.yml")
    with (declaration / "settings/cons.yml").open("a", encoding="utf-8") as settings:
        # the candidate count the replacing selection methods.vfi.bl declares
        settings.write("  n_c: 200\n")
    for name, text in (
        ("spec.yml", LIFECYCLE_RECIPE),
        ("period.yml", LIFECYCLE_PERIOD),
        ("trellis.yml", LIFECYCLE_TRELLIS),
    ):
        (declaration / name).write_text(text, encoding="utf-8")
    (target / "answers.yml").write_text(LIFECYCLE_ANSWERS, encoding="utf-8")
    return demonstration_beside(init_repository(target))


@pytest.fixture(scope="session")
def consport_folder(tmp_path_factory) -> Path:
    """The copy of cons-port of `applications_copy`, made once per session."""
    return applications_copy(tmp_path_factory.mktemp("applications"))


@pytest.fixture
def scratch_consport(tmp_path) -> Path:
    """A fresh copy of cons-port and of the portfolio model, for one test that
    writes their files."""
    return applications_copy(tmp_path / "applications")


@pytest.fixture(scope="session")
def lifecycle_folder(tmp_path_factory) -> Path:
    """The lifecycle registry, made once per session."""
    return lifecycle_registry(tmp_path_factory.mktemp("lifecycle") / "lifecycle")


@pytest.fixture
def scratch_lifecycle(tmp_path) -> Path:
    """A fresh lifecycle registry, for one test that writes its files."""
    return lifecycle_registry(tmp_path / "lifecycle")


@pytest.fixture(scope="session")
def durables_folder(tmp_path_factory) -> Path:
    """A copy of `applications/durables/` named `durables`, a fresh git
    repository with one commit, made once per session; its recipe
    `declaration/spec.yml` reads a trellis of 51 periods."""
    return repository_copy(DURABLES, tmp_path_factory.mktemp("durables") / "durables")


@pytest.fixture(scope="session")
def demonstration_folder(tmp_path_factory) -> Path:
    """A copy of `applications/cons-port/`, the folder of the model written
    the method way, a fresh git repository with one commit, made once per
    session."""
    return repository_copy(
        DEMONSTRATION, tmp_path_factory.mktemp("demonstration") / "cons-port"
    )


@pytest.fixture(scope="session")
def buffer_stock_folder(tmp_path_factory) -> Path:
    """A copy of `applications/buffer-stock/`, whose one stage file states
    the maximization alone and which no source binds: the addition beside
    it, `declaration/stages/buffer_stock/methods.bl`, is named by no recipe
    or trellis file, since the folder holds none. A fresh git repository
    with one commit, made once per session."""
    return repository_copy(BUFFER_STOCK, tmp_path_factory.mktemp("buffer") / "buffer-stock")


@pytest.fixture
def scratch_durables(tmp_path) -> Path:
    """A fresh copy of `applications/durables/` named `durables`, a fresh git
    repository with one commit, for one test that writes its files."""
    return repository_copy(DURABLES, tmp_path / "durables")


# the methods list of a recipe's row,
# `methods: {all: [stages/<key>/methods.bl]}`, which `without_additions`
# empties
_METHODS_LIST = re.compile(r"methods: \{all: \[[^\]]*\]\}")


def without_additions(folder: Path) -> Path:
    """`folder`, a model folder, with its additions taken out: every
    `methods*.bl` under `declaration/stages/` deleted and the methods list
    of every row of every recipe `declaration/spec*.yml` emptied, so that
    the Matsya job `Build declaration`, which the service does not accept
    for a folder that holds an addition (decision S7-W5), reads the folder.
    Answers `folder`."""
    declaration = folder / "declaration"
    for addition in sorted(declaration.glob("stages/*/methods*.bl")):
        addition.unlink()
    for recipe_file in sorted(declaration.glob("spec*.yml")):
        text = recipe_file.read_text(encoding="utf-8")
        recipe_file.write_text(_METHODS_LIST.sub("methods: {all: []}", text), encoding="utf-8")
    return folder


@pytest.fixture
def matsya_durables(tmp_path) -> Path:
    """A copy of `applications/durables/` without its additions
    (`without_additions`), a fresh git repository with one commit, made for
    each test of the Matsya job that takes it, since the service does not
    accept the job for a folder that holds an addition (decision S7-W5)."""
    target = tmp_path / "durables"
    shutil.copytree(DURABLES, target, ignore=shutil.ignore_patterns("__pycache__"))
    return init_repository(without_additions(target))


@pytest.fixture
def refused_pension(tmp_path) -> Path:
    """A fresh copy of the pension model whose terminal connector maps
    `y_f_wk` to `y_f_X`, a field no stage declares, so that the factory
    records `endpoint-unresolved` in its draft at `periods[0].connectors[0]`
    of `declaration/trellis.yml`; for one test that writes its files."""
    copy = repository_copy(PENSION_RETIREMENT, tmp_path / "pension-retirement")
    trellis_file = copy / "declaration/trellis.yml"
    text = trellis_file.read_text(encoding="utf-8")
    trellis_file.write_text(text.replace("y_f_wk: y_f_T", "y_f_wk: y_f_X", 1), encoding="utf-8")
    return copy


@pytest.fixture
def scratch_folder(model_folder, tmp_path) -> Path:
    """A fresh copy of `model_folder`, repository included, for one test
    that writes files."""
    target = tmp_path / "portfolio-choice"
    shutil.copytree(model_folder, target)
    return target


@pytest.fixture
def scratch_pension(pension_folder, tmp_path) -> Path:
    """A fresh copy of `pension_folder`, repository included, for one test
    that writes files."""
    target = tmp_path / "pension-retirement"
    shutil.copytree(pension_folder, target)
    return target


@pytest.fixture(scope="session")
def original(model_folder) -> str:
    """The text of `cons.bl` in the model folder as copied."""
    return (model_folder / CONS).read_text(encoding="utf-8")


@pytest.fixture
def cons_file(model_folder, original) -> Path:
    """The path of `cons.bl` in the model folder, for a test that writes
    it; the original text is written back at the test's end."""
    path = model_folder / CONS
    yield path
    path.write_text(original, encoding="utf-8")


def git(root: Path, *arguments: str) -> str:
    """The standard output of `git <arguments>` run in `root`, which must
    succeed."""
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def repository_with_destination(base: Path) -> tuple[Path, Path]:
    """A test repository with a push destination under `base`: the bare
    repository `remote.git` and its clone `work`, whose git user is
    configured in that repository alone, holding one commit of a README
    pushed to the destination, so that `work`'s branch has an upstream.
    Answers (work, the bare repository)."""
    bare, work = base / "remote.git", base / "work"
    git(base, "init", "-q", "--bare", str(bare))
    git(base, "clone", "-q", str(bare), str(work))
    git(work, "config", "user.name", "bellman-workbench tests")
    git(work, "config", "user.email", "tests@bellman-workbench.invalid")
    (work / "README.md").write_text("A test repository of Bellman Workbench.\n", encoding="utf-8")
    git(work, "add", "README.md")
    git(work, "commit", "-q", "-m", "the test repository")
    git(work, "push", "-q", "-u", "origin", "HEAD")
    return work, bare


@contextlib.contextmanager
def refusing_server():
    """A local HTTP server that answers every request with 401 and a Basic
    challenge, so that git asks for a user name: yields the URL of a
    repository on it, and stops the server at the end."""

    class Refuse(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="bellman-workbench tests"')
            self.send_header("Content-Length", "0")
            self.end_headers()

        do_POST = do_GET

        def log_message(self, *arguments):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Refuse)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/model.git"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def repository(tmp_path) -> tuple[Path, Path]:
    """A test repository with a push destination for one test
    (`repository_with_destination`): (work, the bare repository)."""
    return repository_with_destination(tmp_path)


@pytest.fixture
def git_identity(monkeypatch):
    """A git author and committer for a test that commits in a repository
    the Workbench made, whose configuration names none."""
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "bellman-workbench tests")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "tests@bellman-workbench.invalid")


@pytest.fixture
def app_state(monkeypatch, own_cache_folder):
    """A function `app_state(folder)` that makes `folder` the process's
    folder and the tab's in the page module, reads its tree, and answers
    the module; at the test's end the tab's state is cleared and its folder
    is the one it was. The test has a cache folder of its own
    (`own_cache_folder`), since the trellis's task keeps the binding it
    reads there."""
    from bellman_workbench import app, model

    original = app.tab_folder.value

    def on(folder):
        opened = model.open_folder(folder)
        monkeypatch.setattr(app, "FOLDER", opened)
        app.tab_folder.value = opened
        app.refresh_folder()
        return app

    yield on
    app.form_open.value = None
    app.form_error.value = ""
    app.git_answer.value = None
    app.buffers.value = {}
    app.results.value = {}
    app.shown.value = None
    app.open_path.value = None
    app.checklist.value = ()
    app.pending_goto.value = None
    app.desktop_pending.value = None
    app.desktop_refusal.value = None
    app.tab_folder.value = original


# --- Matsya ---


@pytest.fixture(autouse=True)
def matsya_stub(monkeypatch, tmp_path) -> str:
    """The stand-in of Matsya's client named in BELLMAN_WORKBENCH_MATSYA, the
    variable `matsya_client.COMMAND_VARIABLE` names, for every test of this
    folder, so that `matsya_client.ask` runs it and no test reaches the
    service; a test that needs the variable unset removes it with its own
    `monkeypatch`. BELLMAN_WORKBENCH_MATSYA_STUB_STATE names the stand-in's
    service, a JSON file of the test's own, absent until a command writes
    it (unit G2)."""
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA", MATSYA_STUB)
    monkeypatch.setenv("BELLMAN_MATSYA_SERVER", "http://127.0.0.1:8710")
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STATE_DIR", str(tmp_path / "matsya-sessions"))
    service = tmp_path / "matsya-service.json"
    monkeypatch.setenv("BELLMAN_WORKBENCH_MATSYA_STUB_STATE", str(service))
    return MATSYA_STUB


def stub_job(job: dict) -> None:
    """Writes `job` into the stand-in's service, the JSON file that
    BELLMAN_WORKBENCH_MATSYA_STUB_STATE names, under its identifier,
    replacing a job of that identifier (unit G2)."""
    path = Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"])
    held = (
        json.loads(path.read_text(encoding="utf-8"))
        if path.is_file()
        else {"jobs": {}, "turns": {}, "deliveries": {}, "selected": {}}
    )
    held["jobs"][job["id"]] = job
    path.write_text(json.dumps(held), encoding="utf-8")


def stub_turn(turn: dict) -> None:
    """Writes `turn` into the stand-in's service under its identifier,
    replacing the turn of that identifier, as the service holds a turn it
    has answered (unit G4)."""
    path = Path(os.environ["BELLMAN_WORKBENCH_MATSYA_STUB_STATE"])
    held = json.loads(path.read_text(encoding="utf-8"))
    held["turns"][turn["id"]] = turn
    path.write_text(json.dumps(held), encoding="utf-8")


def client_path(name: str) -> str:
    """The path in a job's model folder at which the client's `job files`
    writes the returned file the service names `name` (the client's
    `_declaration_path`): a stage file `<key>.bl` under
    `declaration/stages/<key>/`, and every other file under `declaration/`
    by its name (unit G3)."""
    if "/" not in name and name.endswith(".bl"):
        return f"declaration/stages/{name[:-3]}/{name}"
    return f"declaration/{name}"


def returned_job(
    folder: Path, session: str, number: int, cycles: int, edits=None, removed=(), files=None
) -> dict:
    """A job of the stand-in's service that has ended, written into it
    (`stub_job`), whose model folder is `files`, a mapping from a path in it
    to its text, by default the folder's own `declaration/`, with `edits`,
    `{path: (old, new)}`, each replacing `old` by `new` once in the file at
    that path, and without the files `removed`, with its prose, its report
    and a record of the service's comparison, so that a download writes a
    saved copy that the package can construct (unit G3)."""
    files = dict(files) if files is not None else {
        path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted((folder / "declaration").rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }
    for path, (old, new) in (edits or {}).items():
        assert files[path].count(old) == 1, (path, old)
        files[path] = files[path].replace(old, new)
    for path in removed:
        del files[path]
    job = {
        "id": f"job-{number}",
        "state": "converged",
        "session": session,
        "revision": 4,
        "configuration_id": "ab12cd34ef56" + "0" * 52,
        "label": {"number": number},
        "result": {"cycles_run": cycles, "comparison": {"converged": True, "differences": []}},
        "files": {
            "economics.md": f"# The model prose of job-{number}\n",
            "report.md": f"# The report of job-{number}\n",
            **files,
        },
    }
    stub_job(job)
    return job


def stub_calls(log: Path) -> list:
    """The entries of the stand-in's log `log`, one per line: the arguments
    of each run, and what a prepared submission received (unit G2)."""
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


@pytest.fixture(scope="session", autouse=True)
def cache_folder(tmp_path_factory):
    """`XDG_CACHE_HOME`, the variable that names the user's cache folder,
    set to a temporary folder for the session and restored at its end, so
    that no test writes a stage view into the user's own cache folder; a
    server or another process a test starts inherits it."""
    with pytest.MonkeyPatch.context() as patch:
        folder = tmp_path_factory.mktemp("cache")
        patch.setenv("XDG_CACHE_HOME", str(folder))
        yield folder


@pytest.fixture(scope="session", autouse=True)
def no_stage_library(tmp_path_factory):
    """`BELLMAN_STAGE_LIBRARY`, the variable that names the library of
    stages (AAS, L-D6), set for the session to a folder that does not exist,
    and restored at its end, so that no test lists the stages of the user's
    own library or of `~/.bellman/library/`; a server or another process a
    test starts inherits it, and a test that reads a library names its own
    with its own `monkeypatch`."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("BELLMAN_STAGE_LIBRARY", str(tmp_path_factory.getbasetemp() / "no-library"))
        yield


@pytest.fixture
def own_cache_folder(tmp_path, monkeypatch) -> Path:
    """`XDG_CACHE_HOME` set for one test to an empty folder of its own,
    `user-cache` under the test's temporary folder, so that the test reads
    no binding of a trellis that another test or a server kept in the
    session's folder (`cache_folder`) and keeps none that another test
    reads. Answers the folder."""
    folder = tmp_path / "user-cache"
    folder.mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(folder))
    return folder


@pytest.fixture
def specify_calls(monkeypatch) -> list:
    """The calls of `specify_trellis` that the Workbench's trellis module
    makes during one test, each recorded by the kinds it was given: the
    module's name `specify_trellis` stands for a function that records the
    call and answers what the package's function answers."""
    from bellman_workbench import trellis

    calls, specify = [], trellis.specify_trellis

    def recorded(syntactic, previous, kinds):
        calls.append(tuple(kinds))
        return specify(syntactic, previous, kinds)

    monkeypatch.setattr(trellis, "specify_trellis", recorded)
    return calls


def kept_bindings(cache: Path) -> dict[str, int]:
    """The files under the folder of the bindings the Workbench keeps in the
    cache folder `cache`, `bellman-workbench/bindings/`, by their posix
    paths from that folder, each with its modification time in
    nanoseconds; empty where the folder does not stand."""
    folder = cache / "bellman-workbench/bindings"
    if not folder.is_dir():
        return {}
    return {
        path.relative_to(folder).as_posix(): path.stat().st_mtime_ns
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def kept_binding_entry(cache: Path, folder: Path, source) -> Path:
    """The entry in which a Workbench whose `XDG_CACHE_HOME` names `cache`,
    resolved as `start_server` gives it, keeps the binding of the trellis
    of `source` in the model folder `folder` (`trellis.binding_entry`)."""
    from bellman_workbench import model, recipe, trellis

    syntactic = recipe.read_source(model.open_folder(folder), source)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("XDG_CACHE_HOME", str(Path(cache).resolve()))
        return trellis.binding_entry(syntactic)


@pytest.fixture
def matsya_state():
    """The module of the Matsya window with its state emptied before and
    after the test: no text in the field, no question sent."""
    from bellman_workbench import matsya_window

    def empty() -> None:
        matsya_window.draft.value = ""
        matsya_window.exchanges.value = ()
        matsya_window.asked.value = 0
        matsya_window.opened.value = frozenset()
        matsya_window.jobs.value = {}
        matsya_window.builds.value = {}
        matsya_window.requested.value = 0
        matsya_window.kind.value = matsya_window.ASK
        matsya_window.target.value = "Recipe"
        matsya_window.discussed.value = None

    empty()
    yield matsya_window
    empty()


# --- the server ---


def free_port() -> int:
    """A TCP port no process listens on at the moment of the call."""
    with socket.socket() as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


def _answers(url: str) -> bool:
    """Whether a GET of `url` is answered with status 200."""
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


def start_server(
    folder: Path,
    port: int,
    log_path: Path,
    delay_marker: str | None = None,
    cache_home: Path | None = None,
    matsya_command: str = MATSYA_STUB,
):
    """Solara's server on the page over `folder` at `port`, started by the
    console command's own command line and environment
    (`command.server_environment`, which sets the folder, turns Solara's
    usage reporting and its banner off, names the delay marker when one is
    given and names `matsya_command` as Matsya's client, MATSYA_STUB unless
    another is given, `off` among them, spec 0.4 §6); its output is written
    to `log_path`. Where `cache_home` is given, the server's `XDG_CACHE_HOME`
    names it, resolved, in place of the session's folder (`cache_folder`),
    since the package reads a relative path there as unset. Answers the
    process."""
    from bellman_workbench import command

    environment = {
        **command.server_environment(folder, delay_marker, matsya_command),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if cache_home is not None:
        environment["XDG_CACHE_HOME"] = str(Path(cache_home).resolve())
    with log_path.open("w", encoding="utf-8") as log:
        return subprocess.Popen(
            command.server_command(port, "localhost", False),
            cwd=ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )


def server_error(url: str, process, log_path: Path, seconds: float = SERVER_SECONDS) -> str | None:
    """None once the server answers a GET of `url` with status 200;
    otherwise the sentence of what happened, with the end of its log: the
    process exited first, or `seconds` passed."""
    started = time.perf_counter()
    while not _answers(url):
        if process.poll() is not None:
            return (
                f"the server exited with {process.returncode} before answering; its log:\n"
                f"{log_path.read_text(encoding='utf-8')[-3000:]}"
            )
        if time.perf_counter() - started > seconds:
            return (
                f"the server did not answer within {seconds} s; its log:\n"
                f"{log_path.read_text(encoding='utf-8')[-3000:]}"
            )
        time.sleep(0.25)
    return None


def stop_server(process) -> None:
    """Terminates the server's process, and kills it when it has not
    exited after ten seconds."""
    process.terminate()
    try:
        process.wait(10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope="session")
def server_on(tmp_path_factory):
    """A function `server_on(folder, delay_marker=None,
    matsya_command=MATSYA_STUB)` that answers the URL of Solara's server on
    the page over `folder`, with `matsya_command` as Matsya's client
    (`start_server`), started on a free port the first time the three are
    asked for and reused after; every server started is stopped at the
    session's end."""
    started = []
    urls = {}

    def start(
        folder: Path, delay_marker: str | None = None, matsya_command: str = MATSYA_STUB
    ) -> str:
        key = (Path(folder).resolve(), delay_marker, matsya_command)
        if key in urls:
            return urls[key]
        port = free_port()
        url = f"http://localhost:{port}/"
        log_path = tmp_path_factory.mktemp("server") / "solara.log"
        process = start_server(folder, port, log_path, delay_marker, matsya_command=matsya_command)
        started.append(process)
        error = server_error(url, process, log_path)
        if error is not None:
            pytest.fail(error)
        urls[key] = url
        return url

    yield start
    for process in started:
        stop_server(process)


@pytest.fixture(scope="session")
def server(server_on, model_folder):
    """The URL of the server over `model_folder`, started with the delay
    marker DELAY_MARKER in its environment."""
    return server_on(model_folder, DELAY_MARKER)


# --- the browser ---


@pytest.fixture(scope="session")
def chromium_executable() -> str | None:
    """The Chromium executable the environment variable
    `BELLMAN_WORKBENCH_CHROMIUM` names, None when it is not set."""
    return os.environ.get("BELLMAN_WORKBENCH_CHROMIUM")


def launch_chromium(playwright, executable: str | None = None):
    """Playwright's Chromium launched headless, from `executable` when one
    is given, else from the executable `BELLMAN_WORKBENCH_CHROMIUM` names, else
    Playwright's own."""
    executable = executable or os.environ.get("BELLMAN_WORKBENCH_CHROMIUM")
    options = {"executable_path": executable} if executable else {}
    return playwright.chromium.launch(headless=True, **options)


def _chromium_launch_error() -> str | None:
    """None when Playwright's Chromium launches headless here, with the
    executable `BELLMAN_WORKBENCH_CHROMIUM` names when that is set; otherwise
    the sentence of the error."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        return f"playwright is not installed: {error}"
    try:
        with sync_playwright() as playwright:
            browser = launch_chromium(playwright)
            browser.close()
    except Exception as error:  # the reason is the skip's sentence
        return str(error).strip().split("\n")[0]
    return None


def pytest_collection_modifyitems(config, items):
    """Marks every test of `test_page.py` as skipped, with the launch's
    error as the reason, when Playwright's Chromium cannot launch here;
    the launch is tried once, and only when such a test is collected."""
    page_tests = [item for item in items if Path(str(item.fspath)).name.startswith(PAGE_TESTS)]
    if not page_tests:
        return
    error = _chromium_launch_error()
    if error is None:
        return
    marker = pytest.mark.skip(reason=f"Playwright's Chromium cannot launch here: {error}")
    for item in page_tests:
        item.add_marker(marker)


@pytest.fixture(scope="session")
def browser(chromium_executable):
    """One headless Chromium for the session, launched from the executable
    BELLMAN_WORKBENCH_CHROMIUM names when that is set; the module is skipped,
    with the launch's error as the reason, when it cannot launch."""
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    playwright = sync_playwright().start()
    try:
        launched = launch_chromium(playwright, chromium_executable)
    except Exception as error:
        playwright.stop()
        reason = str(error).strip().split("\n")[0]
        pytest.skip(f"Playwright's Chromium cannot launch here: {reason}")
    yield launched
    launched.close()
    playwright.stop()


def new_tab(browser):
    """A page in a new browser context, a separate Solara session, with
    every page error printed."""
    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()
    page.on("pageerror", lambda error: print(f"page error: {error}"))
    return context, page


@pytest.fixture
def page(browser, server):
    """A page in a new browser context for one test, closed at its end."""
    context, opened = new_tab(browser)
    yield opened
    context.close()


# --- Node ---


@pytest.fixture(scope="module")
def node() -> str:
    """The path of the executable `node` on the PATH; a test that takes it
    is skipped when there is none."""
    found = shutil.which("node")
    if found is None:
        pytest.skip("node is not on the PATH")
    return found


def node_output(node: str, script: str, value):
    """The decoded JSON that `script`, run by `node` as a module with the
    JSON of `value` on its standard input, prints on its standard output;
    fails with Node's standard error where Node exits with a nonzero
    status."""
    completed = subprocess.run(
        [node, "--input-type=module", "-e", script],
        input=json.dumps(value),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"node exited with status {completed.returncode}; its standard error:\n"
            f"{completed.stderr}"
        )
    return json.loads(completed.stdout)


# --- the expected values, from the object ---


def digest7(text: str) -> str:
    """The first seven hexadecimal digits of the SHA-256 digest of `text`,
    as the status line prints them."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:7]


def edited(text: str, line: int, new: str) -> str:
    """The text with its line `line`, counted from one, replaced by `new`."""
    lines = text.split("\n")
    lines[line - 1] = new
    return "\n".join(lines)


def applied(text: str, edits) -> str:
    """The text with the replacements `edits` made, each with `line`,
    `column`, `end_line`, `end_column` and `text`, the positions counted
    from one in code points (`model.Replacement`), the last first, so that
    no edit moves the place of an earlier one."""
    starts = [0]
    for line in text.split("\n")[:-1]:
        starts.append(starts[-1] + len(line) + 1)
    for edit in sorted(edits, key=lambda edit: (edit.line, edit.column), reverse=True):
        start = starts[edit.line - 1] + edit.column - 1
        end = starts[edit.end_line - 1] + edit.end_column - 1
        text = text[:start] + edit.text + text[end:]
    return text


def changed_lines(before: str, after: str) -> list[int]:
    """The numbers of the lines, counted from one, that differ between
    `before` and `after`, two texts of one number of lines."""
    pairs = zip(before.split("\n"), after.split("\n"))
    return [number for number, (old, new) in enumerate(pairs, 1) if old != new]


def added_edits(text: str, path: str, perch: str, field: str, written: str) -> tuple:
    """The edits of the box `add field` of the table `perch` of the stage
    file `path`, whose text is `text`, for the state `field` with the set
    `written`, the empty text for none (rule 4, T-R6; AAS, L-D1)."""
    from bellman.stage import source_spans
    from bellman_workbench import model

    groups = model.classification(
        model.elaborate_buffer(text, path).stage, source_spans(text, path)
    )
    change = {
        "kind": "add",
        "perch": perch,
        "branch": None,
        "field": field,
        "set": written,
        "role": "state",
    }
    return model.classification_edits(groups, change)


def decision_fields(text: str, path: str) -> list[str]:
    """The identities of the decision fields of the stage that `text`
    constructs from the file `path`, in the order of its fields table."""
    from bellman_workbench import model

    stage = model.elaborate_buffer(text, path).stage
    return [str(identity) for identity, sort in stage.fields().items() if sort.perch == "dcsn"]


def stage_of(text: str):
    """The stage of `text` elaborated with the origin the page gives a
    file no recipe holds, the relative path of `cons.bl`, `CONS`."""
    from bellman.stage import elaborate_text

    return elaborate_text(text, CONS)


def tree_entries(tree: list) -> dict:
    """Every entry of a folder tree that `model.folder_tree` answers, at
    every depth, by its path relative to the folder."""
    found = {}
    for entry in tree:
        found[entry["path"]] = entry
        found.update(tree_entries(entry["children"]))
    return found


def shown_of(stage, text: str, path: str):
    """The record `app.Shown` of `stage`, elaborated from `text`, as the
    page holds it for the file `path`, with the span table the package's
    `source_spans` answers for `text` and no view, bindings or digests:
    what the classification table reads."""
    from bellman.stage import source_spans
    from bellman_workbench import app

    return app.Shown(
        path=path,
        text=text,
        revision=1,
        stage=stage,
        collection={},
        layers={},
        spans=source_spans(text, path),
        counts={},
        seconds=0.0,
        digest="",
        notes=[],
        occurrence=None,
        version="symbolic",
        digests={},
        source_digests={},
    )


def shown_panel():
    """An element of the page's panel over the object the tab shows,
    `app.Panel(None, app.shown.value)`, which reads `app.shown` at each
    render as the page does, so that a test that replaces the shown object
    sees the panel drawn for the new one; for `solara.render`."""
    import solara

    from bellman_workbench import app

    @solara.component
    def ShownPanel():
        return app.Panel(None, app.shown.value)

    return ShownPanel()


def clear_trellis_state() -> None:
    """The trellis's state of the page module's tab emptied, as a test of
    the trellis view leaves it: no source, head, trellis, outcome, digests,
    count, drawing mark, selection, restriction or text the window wrote
    into the bar, the window not writing one, and the stage's view shown."""
    from bellman_workbench import app

    app.source.value, app.head.value, app.view_mode.value = None, None, "stage"
    app.trellis_shown.value, app.trellis_outcome.value, app.trellis_seen.value = None, None, {}
    app.trellis_rebuild.value, app.drawing.value, app.selected.value = 0, False, None
    app.restriction.value, app.restriction_text.value, app.restriction_refusal.value = (
        None,
        "",
        None,
    )
    app.restriction_opening.value = ""
    app.writing_opening.value = False


def drawn_text(widget) -> str:
    """The text an element rendered by `solara.render` draws: its string
    children joined, each child element's text in its place, so that an
    element with no children, such as `<wbr>`, a break opportunity, draws
    none."""
    return "".join(
        child if isinstance(child, str) else drawn_text(child)
        for child in getattr(widget, "children", ())
    )


def graph_named(collection: dict, name: str) -> dict:
    """The graph of `collection` whose id is `name`."""
    return next(graph for graph in collection["graphs"] if graph["id"] == name)


def as_json(value) -> str:
    """One JSON text of `value`, with sorted keys, for a comparison
    character for character."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


# a row of the table of a build in the README of a bundle: a file's path,
# its size in bytes, written with commas, and its SHA-256
RECORD_ROW = re.compile(r"^\| `([^`]+)` \| ([\d,]+) \| `([0-9a-f]{64})` \|$")


def build_record(readme: Path) -> dict[str, tuple[int, str]]:
    """The record of the build in the README `readme`: each file the build
    writes, by its path from the Workbench's distribution folder, with its
    size in bytes and its SHA-256, read from the rows of the README's one
    table of the build (`RECORD_ROW`)."""
    found = {}
    for line in readme.read_text(encoding="utf-8").splitlines():
        row = RECORD_ROW.match(line)
        if row:
            found[row[1]] = (int(row[2].replace(",", "")), row[3])
    return found


# The layout's records of one graph of the graph JSON, made in the page by
# the bundle's own functions (G-D14) with the layers `opened` open: the ids
# of the boxes laid out; each wire as [writer's box, writer's port, reader's
# box, reader's port]; each port of a box as [box, "in" or "out", port, its
# title]; the place of each box, `ax` and `ay` its corner on the graph; the
# route of each wire, its points on the graph, by the wire's id; and the
# label each wire that names a join prints, with its center, by the wire's id.
LAYOUT_RECORDS_JS = """
async ([graph, opened, fault]) => {
  const flow = window.BellmanFlow.layout;
  const model = flow.model(graph);
  // the recipe's order of the stage keys the page gives the region, by which the layout ranks every period's
  // occurrences, as the page lays them out (the fix wave Q3a of unit Q, item 2)
  const host = document.querySelector('.bl-view-host');
  const order = host && host.bellmanFlow && host.bellmanFlow.stageOrder ? host.bellmanFlow.stageOrder() : null;
  let built = flow.build(model, new Set(opened), {order}, flow.measure);
  const walk = (node, visit) => {
    visit(node);
    for (const child of node.children || []) walk(child, visit);
  };
  // the page's own layout: ELK's answer, laid out again with every card of a column of a period at the
  // column's width where a column is ragged (design pass 13 §2, rule 6; Q-D25), aligned in a stage's builders
  // graph (AAS, L-D20), and settled, the period frames on one top edge and the boundary markers placed
  // (design pass 13 §1, rule 6; D13)
  const elk = new window.ELK();
  let laidOut = await elk.layout(built.elk);
  const widths = flow.columnWidths(built, laidOut);
  if (widths) {
    built = flow.build(model, new Set(opened), {widths, order}, flow.measure);
    laidOut = await elk.layout(built.elk);
  }
  const required = new Map();
  walk(built.elk, (node) => {
    for (const edge of node.edges || []) required.set(edge.id, {
      source: edge.sources[0], target: edge.targets[0],
    });
  });
  const answer = await flow.arrange(built, laidOut, elk);
  flow.settle(built, answer);
  const owned = [];
  walk(answer, (node) => {
    for (const edge of node.edges || []) owned.push({node, edge});
  });
  // Faults alter the returned layout before the region's reader sees it (§4, item 1).
  if (fault && fault !== 'exchange routes') {
    const first = owned.find(({edge}) => edge.targets[0].includes('::in::'));
    if (!first) throw new Error('the fault needs a returned edge ending at a reading port');
    if (fault === 'drop') first.node.edges.splice(first.node.edges.indexOf(first.edge), 1);
    else if (fault === 'exchange') {
      const other = owned.find(({edge}) => edge.targets[0].includes('::in::')
        && edge.targets[0] !== first.edge.targets[0] && edge.sources[0] !== first.edge.sources[0]);
      if (!other) throw new Error('the fault needs two distinct returned edge destinations');
      [first.edge.targets, other.edge.targets] = [other.edge.targets, first.edge.targets];
    } else if (fault === 'duplicate') first.node.edges.push(JSON.parse(JSON.stringify(first.edge)));
    else if (fault === 'extra') first.node.edges.push({...first.edge, id: first.edge.id + ':extra'});
    else if (fault === 'incomplete') first.edge.sections = [];
    else if (fault === 'missing box') answer.children.splice(0, 1);
    else throw new Error('unknown layout fault ' + fault);
  }
  const problems = [], boxes = [], returnedPorts = new Set(), pieces = new Map();
  const finitePoint = (point) => point && Number.isFinite(point.x) && Number.isFinite(point.y);
  walk(answer, (node) => {
    if (node !== answer) boxes.push(node.id);
    for (const port of node.ports || []) returnedPorts.add(port.id);
    for (const edge of node.edges || []) {
      if (pieces.has(edge.id)) problems.push('the edge piece ' + edge.id + ' is returned twice');
      pieces.set(edge.id, edge);
      const wanted = required.get(edge.id);
      if (!wanted) problems.push('the edge piece ' + edge.id + ' was not requested');
      if (edge.sources.length !== 1 || edge.targets.length !== 1
          || (wanted && (edge.sources[0] !== wanted.source || edge.targets[0] !== wanted.target))) {
        problems.push('the edge piece ' + edge.id + ' has different endpoints');
      }
      if (!edge.sections || edge.sections.length !== 1 || edge.sections.some((section) =>
          !finitePoint(section.startPoint) || !finitePoint(section.endPoint)
          || (section.bendPoints || []).some((point) => !finitePoint(point)))) {
        problems.push('the edge piece ' + edge.id + ' has no complete route');
      }
    }
  });
  for (const id of required.keys()) {
    if (!pieces.has(id)) problems.push('the edge piece ' + id + ' was not returned');
  }
  const ports = {}, titles = [];
  for (const [id, box] of Object.entries(built.boxes)) {
    if (!box.geom || !boxes.includes(id)) continue;
    for (const [way, list] of [['in', box.geom.ins], ['out', box.geom.outs]]) {
      for (const port of list) {
        if (!returnedPorts.has(port.handle)) {
          problems.push('the port ' + port.handle + ' was not returned');
          continue;
        }
        ports[port.handle] = [id, port.id];
        titles.push([id, way, port.id, port.full]);
      }
    }
  }
  const wires = [], wireIds = [], routeEnds = {};
  for (const wire of built.wires) {
    const path = wire.pieces.map((id) => pieces.get(id));
    if (path.some((piece) => !piece)) continue;
    let complete = true;
    for (let i = 0; i < path.length; i++) {
      const piece = path[i];
      if (!returnedPorts.has(piece.sources[0]) || !returnedPorts.has(piece.targets[0])
          || (i && path[i - 1].targets[0] !== piece.sources[0])) complete = false;
    }
    // the wire's own ports: the cables into one socket are routed to one ELK port, the first wire's, so the last
    // piece's target names that port for a wire read at a hidden port, while the route's ends are still compared
    // with ELK's endpoints below, the two ports standing at one point (design pass 13 §1, rule 4)
    const source = ports[wire.sourceHandle] || ports[path[0].sources[0]];
    const target = ports[wire.targetHandle] || ports[path[path.length - 1].targets[0]];
    if (!complete || !source || !target) {
      problems.push('the wire ' + wire.id + ' has no complete path between returned ports');
      continue;
    }
    wires.push([...source, ...target]);
    wireIds.push(wire.id);
    const firstSections = path[0].sections || [], lastSections = path[path.length - 1].sections || [];
    routeEnds[wire.id] = [firstSections[0]?.startPoint, lastSections[lastSections.length - 1]?.endPoint];
  }
  const read = flow.read(built, answer);
  // This fault damages the reader's output, while its ELK evidence stays unchanged.
  if (fault === 'exchange routes') {
    const first = wireIds[0];
    const other = wireIds.find((id) => JSON.stringify(routeEnds[id][1]) !== JSON.stringify(routeEnds[first][1]));
    if (!other) throw new Error('the route fault needs two distinct returned destinations');
    [read.routes[first], read.routes[other]] = [read.routes[other], read.routes[first]];
  }
  return {boxes, wires, titles, places: read.place, routes: read.routes, joins: read.joins,
          wireIds, routeEnds, problems, width: read.width, builderPlaces: read.builders,
          rootEdges: (answer.edges || []).map((edge) => [edge.sources[0], edge.targets[0]])};
}
"""


def attribute_of(item: dict, key: str) -> str:
    """The value of the attribute `key` of a node or a port of the graph
    JSON, the empty text where it has none (spec 0.4 §4)."""
    return next((pair["value"] for pair in item.get("attrs") or [] if pair["key"] == key), "")


def every_namespace(graph: dict) -> set[str]:
    """The namespace of every layer of a graph of the graph JSON: each
    leading part of a node's namespace, `policy` and `policy/endoggrid` for
    the namespace `policy/endoggrid` (spec 0.4 §4)."""
    return opened_namespaces(node["namespace"] for node in graph["nodes"] if node.get("namespace"))


def opened_namespaces(layers) -> set[str]:
    """The layers open where `layers` are the deepest layers open: each
    namespace of `layers` with every namespace that holds it, as the region
    reads its property `layers` and a place's layers (spec 0.4 §4)."""
    return {
        "/".join(parts[:depth])
        for parts in (layer.split("/") for layer in layers)
        for depth in range(1, len(parts) + 1)
    }


def standing_box(nodes: dict, node_id: str, opened: set[str]) -> tuple[str, bool]:
    """The box that stands for the node `node_id` of a graph whose nodes,
    by id, are `nodes`, with the layers `opened` open, and whether that box
    is a closed layer: the node itself where every layer that holds it is
    open, else the outermost closed layer that holds it, by its id, its
    namespace followed by LAYER_ID_ENDING (spec 0.4 §4)."""
    from bellman.stage import LAYER_ID_ENDING

    parts = (nodes[node_id].get("namespace") or "").split("/")
    for depth in range(1, len(parts) + 1):
        layer = "/".join(parts[:depth])
        if layer and layer not in opened:
            return layer + LAYER_ID_ENDING, True
    return node_id, False


# the namespace of a stage occurrence's layer of a trellis graph,
# `periods[h]/<key>` (spec 0.4 §2.6)
OCCURRENCE_NAMESPACE = re.compile(r"periods\[\d+\]/[^/]+")
# the namespace of a period's layer of a trellis graph, `periods[2]`
PERIOD_NAMESPACE = re.compile(r"periods\[\d+\]")


def compact_occurrences(graph: dict, opened: set[str]) -> set[str]:
    """The stage occurrences of the trellis graph `graph` drawn compact with
    the layers `opened` open (AAS, L-D7): each open occurrence, every layer
    above it open, that holds a builder's layer and no open layer."""
    namespaces = every_namespace(graph)
    found = set()
    for namespace in namespaces:
        if not OCCURRENCE_NAMESPACE.fullmatch(namespace) or namespace not in opened:
            continue
        if namespace.split("/")[0] not in opened:
            continue
        inside = [layer for layer in namespaces if layer.rsplit("/", 1)[0] == namespace]
        if inside and not any(layer in opened for layer in inside):
            found.add(namespace)
    return found


def expected_layout(graph: dict, opened: set[str], split=()) -> dict:
    """What the region lays out of the graph `graph` of the graph JSON with
    the layers `opened` open, computed from the graph JSON alone (spec 0.4
    §4, the first and the second comparisons): `boxes`, the ids of the nodes
    whose layers are all open and of the layers whose outer layers are all
    open, a layer's id its namespace followed by LAYER_ID_ENDING; `wires`,
    each wire as (writer's box, writer's port, reader's box, reader's port),
    from what stands for its writer to what stands for its reader, a closed
    layer standing for every node inside it with one port for each wire it
    carries, named by the wire's writer and output, `<node>|<output>`, a
    wire whose two ends stand in one closed layer left out, and wires that
    join the same two ports counted once; `titles`, the label the graph JSON
    gives each port of each box, by (box, "in" or "out", port), a closed
    layer's port taking the label of the first port it stands for in the
    order of the nodes and their edges. An open stage occurrence of a
    trellis graph none of whose builders is open, drawn compact (AAS,
    L-D7), is laid out as a closed layer, its builders' boxes standing
    inside it outside ELK's graph (`compact_occurrences`). The wires from
    one stage occurrence standing as a closed layer to another of the same
    period, where they come from two or more outputs, are one wire between
    the bundle's port of each, `stages::<writer>|<reader>` by the two
    namespaces, unless `split` names either occurrence or the bundle (AAS,
    L-D25); and the wires whose reading port carries a value role are
    bundled by their route, within a period or between two, from one such
    occurrence to another or between one and a boundary marker of the
    graph's root or a closed period's layer, `stages::<writer>|<reader>|<branch>`,
    the branch of the route left out where it has none, a marker named by
    its id and a closed period by the occurrence inside it that holds the
    wire's node, where
    they come from two or more outputs, whatever `split` names, each bundle
    leaving the writer at its own port and reaching a marker at the port of
    its first wire (design pass 12 §2). The bundle's ports take no title
    from the graph JSON; `cables` holds, by (box, "in" or "out", port), the
    label a port of such a bundle of values prints on its card, the names
    of the functions its wires carry, each once, in the order of its wires
    (AAS, L-D26)."""
    from bellman.factory.model_explorer import BOUNDARY_KINDS
    from bellman.stage import LAYER_ID_ENDING
    from bellman.syntax.vocabulary import VALUE_ROLES

    opened = set(opened) - compact_occurrences(graph, opened)
    nodes = {node["id"]: node for node in graph["nodes"]}

    def stands_for(node_id: str) -> tuple[str, bool]:
        return standing_box(nodes, node_id, opened)

    boxes = {node_id for node_id in nodes if not stands_for(node_id)[1]}
    for namespace in every_namespace(graph):
        outer = namespace.split("/")[:-1]
        if all("/".join(outer[:depth]) in opened for depth in range(1, len(outer) + 1)):
            boxes.add(namespace + LAYER_ID_ENDING)
    titles = {}
    for node_id, node in nodes.items():
        if not stands_for(node_id)[1]:
            for way, key in (("in", "inputsMetadata"), ("out", "outputsMetadata")):
                for port in node.get(key) or []:
                    titles[(node_id, way, port["id"])] = attribute_of(port, "label")
    # each wire of the graph JSON between two boxes: its edge, its reading
    # node's ports, and the box that stands for each end, with whether that
    # box is a closed layer
    found = []
    for node_id, node in nodes.items():
        reader, reader_closed = stands_for(node_id)
        inputs = {port["id"]: port for port in node.get("inputsMetadata") or []}
        for edge in node.get("incomingEdges") or []:
            writer, writer_closed = stands_for(edge["sourceNodeId"])
            if writer != reader:
                found.append(
                    {
                        "edge": edge,
                        "reading": node_id,
                        "inputs": inputs,
                        "writer": writer,
                        "reader": reader,
                        "closed": writer_closed and reader_closed,
                        "writer_closed": writer_closed,
                        "reader_closed": reader_closed,
                    }
                )

    # a stage's builders graph, with no period's layer and no field's box, whose
    # value wires from one box to one box are one bundle where they come from
    # two or more outputs, `boxes::<writer>|<reader>`, never split, drawn from
    # the ports of the bundle's first wire (design pass 14 §1; S-D2 to S-D4)
    boxed = not any(PERIOD_NAMESPACE.fullmatch(ns) for ns in every_namespace(graph)) and not any(
        attribute_of(node, "kind") == "field" for node in nodes.values()
    )

    def reading_port(wire: dict) -> dict:
        # the port of the graph JSON the wire reaches
        return wire["inputs"].get(wire["edge"]["targetNodeInputId"], {})

    def carries_value(wire: dict) -> bool:
        # whether the wire's reading port carries a value role, as a backward
        # trellis graph's wires do
        return attribute_of(reading_port(wire), "role") in VALUE_ROLES

    def end_of(wire: dict, way: str, value: bool) -> str | None:
        # the name of the end `way`, `writer` or `reader`, of a wire that a
        # bundle joins: a stage occurrence standing as a closed layer, by its
        # namespace, and, for a wire that carries a value role, a closed
        # period's layer, by the namespace of the occurrence inside it that
        # holds the wire's node, and a boundary marker of the graph's root,
        # by its id (design pass 12 §2); None for any other end
        box = wire[way]
        if wire[f"{way}_closed"]:
            namespace = box[: -len(LAYER_ID_ENDING)]
            if OCCURRENCE_NAMESPACE.fullmatch(namespace):
                return namespace
            if not (value and PERIOD_NAMESPACE.fullmatch(namespace)):
                return None
            held = wire["edge"]["sourceNodeId"] if way == "writer" else wire["reading"]
            inside = "/".join((nodes[held].get("namespace") or "").split("/")[:2])
            return inside if OCCURRENCE_NAMESPACE.fullmatch(inside) else None
        node = nodes.get(box) or {}
        root = not node.get("namespace") and attribute_of(node, "kind") in BOUNDARY_KINDS
        return box if value and root else None

    def key_of(wire: dict) -> str | None:
        # the key of the bundle a wire belongs to: in a stage's builders graph
        # the two boxes of a wire that carries a value role (design pass 14
        # §1); in a trellis graph its two occurrences of one period (L-D25),
        # and for a wire that carries a value role its two ends and its
        # route's branch (design pass 12 §2); None for any other wire
        if boxed:
            if not carries_value(wire) or wire["writer"] == wire["reader"]:
                return None
            return f"{wire['writer']}|{wire['reader']}"
        value = carries_value(wire)
        ends = [end_of(wire, way, value) for way in ("writer", "reader")]
        if None in ends or ends[0] == ends[1]:
            return None
        if not value:
            same = ends[0].split("/")[0] == ends[1].split("/")[0]
            return "|".join(ends) if same else None
        held = wire["edge"].get("attrs") or []
        route = next((pair["value"] for pair in held if pair["key"] == "route"), None)
        branch = route.get("branch") if route else None
        return "|".join(ends) + ("" if branch is None else f"|{branch}")

    # the bundles, each by its key: the outputs its wires come from, and
    # whether it carries values, which `split` never splits
    outputs: dict[str, set] = {}
    whole: dict[str, bool] = {}
    for wire in found:
        key = key_of(wire)
        if key:
            edge = wire["edge"]
            outputs.setdefault(key, set()).add(
                f"{edge['sourceNodeId']}|{edge['sourceNodeOutputId']}"
            )
            whole.setdefault(key, carries_value(wire))
    bundled = {
        key: f"{'boxes' if boxed else 'stages'}::{key}"
        for key, keys in outputs.items()
        if len(keys) > 1 and (whole[key] or not {*key.split("|"), f"stages::{key}"} & set(split))
    }
    # the first wire of each bundle, at whose port a bundle reaches a marker,
    # and the names of the functions each bundle of values carries
    firsts: dict[str, dict] = {}
    names: dict[str, list] = {}
    wires, cables = set(), {}
    for wire in found:
        edge, inputs = wire["edge"], wire["inputs"]
        writer, writer_closed = wire["writer"], wire["writer_closed"]
        reader, reader_closed = wire["reader"], wire["reader_closed"]
        key = key_of(wire)
        bundle = bundled.get(key) if key else None
        if bundle:
            first = firsts.setdefault(key, edge)
            wires.add(
                (
                    writer,
                    bundle if writer_closed else first["sourceNodeOutputId"],
                    reader,
                    bundle if reader_closed else first["targetNodeInputId"],
                )
            )
            if whole[key]:
                name = re.split(r"[≺≻(]", attribute_of(reading_port(wire), "label") or "")[0]
                held = names.setdefault(key, [])
                if name and name not in held:
                    held.append(name)
                for box, way, closed in ((writer, "out", writer_closed), (reader, "in", reader_closed)):
                    if closed:
                        cables[(box, way, bundle)] = ", ".join(held)
            continue
        source, output = edge["sourceNodeId"], edge["sourceNodeOutputId"]
        carried = f"{source}|{output}"
        wires.add(
            (
                writer,
                carried if writer_closed else output,
                reader,
                carried if reader_closed else edge["targetNodeInputId"],
            )
        )
        if writer_closed:
            written = next(
                (port for port in nodes[source].get("outputsMetadata") or []
                 if port["id"] == output),
                {},
            )
            titles.setdefault((writer, "out", carried), attribute_of(written, "label"))
        if reader_closed:
            port = inputs.get(edge["targetNodeInputId"], {})
            titles.setdefault((reader, "in", carried), attribute_of(port, "label"))
    # in a stage's builders graph a port of a node whose wires are all drawn at
    # another port, their bundle's first wire's, is neither drawn nor laid out,
    # while a port at which any wire is drawn, and a port no wire reaches, stand
    # (design pass 14 §1, rule 4; S-D4)
    if boxed:
        kept, moved = set(), set()
        for wire in found:
            edge, key = wire["edge"], key_of(wire)
            first = firsts.get(key) if key and key in bundled else None
            if not wire["writer_closed"]:
                own = (wire["writer"], "out", edge["sourceNodeOutputId"])
                (kept if first is None or first["sourceNodeOutputId"] == own[2] else moved).add(own)
            if not wire["reader_closed"]:
                own = (wire["reader"], "in", edge["targetNodeInputId"])
                (kept if first is None or first["targetNodeInputId"] == own[2] else moved).add(own)
        for port in moved - kept:
            titles.pop(port, None)
    return {"boxes": boxes, "wires": wires, "titles": titles, "cables": cables}


def layout_records(page, graph: dict, opened, fault: str | None = None) -> dict:
    """The layout's records of the graph `graph` with the layers `opened`
    open, made by the bundle's reader from ELK's answer (spec 0.4 §4), which
    the bundle's `arrange` aligns in a stage's builders graph as the page
    does (AAS, L-D20), among them `joins`, the label each wire that names a
    join prints and its center, `{text, x, y}`, by the wire's id (unit K's
    decision K-D4); `width`, the graph's at scale 1; `rootEdges`, the ELK
    edges of the graph's root, each [source port, target port] (K-D5); and
    `builderPlaces`, the place of each builder's box of a compact
    occurrence, which ELK does not lay out (AAS, L-D7).
    An optional fault damages that answer before the reader sees it, or
    exchanges two routes after reading while retaining the ELK evidence."""
    return page.evaluate(LAYOUT_RECORDS_JS, [graph, sorted(opened), fault])


def layout_differences(records: dict, expected: dict) -> list[str]:
    """The differences between the layout's records `records` and what the
    graph JSON makes of them, `expected` (`expected_layout`), one sentence
    each: a box missing or laid out for nothing, a wire laid out twice, a
    wire missing or laid out for nothing, a port whose title differs from
    its label, or a route that does not end at its returned ELK endpoints;
    the empty list where the records hold (spec 0.4 §4). In a stage's
    builders graph the records draw one wire for each bundle of value wires
    between two boxes, from the ports of its first wire, and lay out no port
    whose wires are all drawn elsewhere (design pass 14 §1)."""
    found = list(records.get("problems", []))
    boxes = set(records["boxes"])
    if len(boxes) != len(records["boxes"]):
        found.append("a returned box is laid out twice")
    places = records["places"]
    if set(places) != boxes:
        found.append("the returned boxes and their places differ")
    for box, place in places.items():
        if any(not isinstance(place.get(key), (int, float)) or not math.isfinite(place[key])
               for key in ("ax", "ay", "x", "y", "width", "height")):
            found.append(f"the box {box} has no complete place")
    routes = records["routes"]
    if len(records.get("wireIds", [])) != len(records["wires"]) or set(routes) != set(records.get("wireIds", [])):
        found.append("the returned wires and their routes differ")
    route_ends = records.get("routeEnds", {})
    if set(route_ends) != set(routes):
        found.append("the read routes and their ELK endpoint records differ")
    for wire, points in routes.items():
        if len(points) < 2 or any(
            not isinstance(point.get(key), (int, float)) or not math.isfinite(point[key])
            for point in points for key in ("x", "y")
        ):
            found.append(f"the wire {wire} has no complete route")
            continue
        ends = route_ends.get(wire) or []
        if len(ends) != 2 or any(
            not end or any(
                not isinstance(end.get(key), (int, float))
                or not math.isfinite(end[key])
                or not math.isclose(point[key], end[key], rel_tol=0, abs_tol=1e-6)
                for key in ("x", "y")
            )
            for point, end in zip((points[0], points[-1]), ends)
        ):
            found.append(f"the read route of {wire} does not end at its ELK endpoints")
    found += [f"the box {box} is not laid out" for box in sorted(expected["boxes"] - boxes)]
    found += [f"the box {box} stands for nothing" for box in sorted(boxes - expected["boxes"])]
    wires = [tuple(wire) for wire in records["wires"]]
    twice = sorted({wire for wire in wires if wires.count(wire) > 1})
    found += [f"the wire {wire} is laid out twice" for wire in twice]
    lost = sorted(expected["wires"] - set(wires))
    found += [f"the wire {wire} is not laid out" for wire in lost]
    stray = sorted(set(wires) - expected["wires"])
    found += [f"the wire {wire} joins no wire of the graph JSON" for wire in stray]
    titles = {(box, way, port): title for box, way, port, title in records["titles"]}
    found += [
        f"the port {key} reads {titles.get(key)!r}, its label {label!r}"
        for key, label in sorted(expected["titles"].items())
        if titles.get(key) != label
    ]
    return found


# --- reading and driving the page ---


def svg_texts(page) -> list[str]:
    """The labels of the boxes and names of the layers drawn by the region."""
    return page.evaluate(SVG_TEXTS_JS)


def wait_for_view(page, minimum: int = 12, timeout: int = 30_000) -> None:
    """Waits until the region has drawn at least `minimum` texts of boxes and layers."""
    page.wait_for_function(f"() => ({SVG_TEXTS_JS})().length >= {minimum}", timeout=timeout)


def status_settled_on(page, relpath: str) -> str | None:
    """The status line's text once it names `relpath` with a loop time and
    no pending mark (`elaborating`, `drawing`); None before. The page opens
    on the folder's first stage file, so the view holds a graph before the
    clicked file's loop has run, and a wait for the view alone would read
    that graph."""
    text = status_text(page)
    pending = "elaborating" in text or "drawing" in text
    return text if text.startswith(f"{relpath} (") and "loop" in text and not pending else None


def open_file(page, url: str, relpath: str, minimum: int = 12, timeout: int = 60_000) -> float:
    """Opens the page at `url`, opens the folders on the path of `relpath`
    (`reveal_in_tree`), clicks the file in the tree, waits for the status
    line to settle on that file and for the view to draw at least `minimum`
    texts, and installs the recorders; answers the seconds from the click to
    the drawn view."""
    page.goto(url)
    selector = f'.bl-tree-file[data-path="{relpath}"]'
    reveal_in_tree(page, relpath, timeout)
    started = time.perf_counter()
    page.click(selector)
    seconds = timeout / 1000
    wait_until(lambda: status_settled_on(page, relpath), seconds, f"the loop of {relpath}")
    wait_for_view(page, minimum, timeout)
    drawn = time.perf_counter() - started
    page.wait_for_timeout(500)
    wait_until(lambda: status_settled_on(page, relpath), seconds, f"the loop of {relpath}")
    page.evaluate(RECORDERS_JS)
    return drawn


def open_cons(page, url: str) -> float:
    """Opens the page at `url`, clicks `cons.bl` in the tree, waits for the
    view to draw and installs the recorders; answers the seconds from the
    click to the drawn view."""
    return open_file(page, url, CONS)


def select_node(page, node_id: str, graph_id: str) -> None:
    """Selects the box `node_id` as a click does: a `click` on its element."""
    page.evaluate(SELECT_NODE_JS, [node_id, graph_id])


def double_click_node(page, node_id: str, graph_id: str) -> None:
    """Double clicks the box `node_id` by a `dblclick` on its element."""
    page.evaluate(DOUBLE_CLICK_NODE_JS, [node_id, graph_id])


def held_graph_ids(page) -> list[str]:
    """The graph ids of the collection held by the region."""
    return page.evaluate(HELD_GRAPH_IDS_JS)


def record_view_state(page) -> None:
    """Records the region's open layers and selection on processed and selected events."""
    page.evaluate(PANE_STATE_RECORDER_JS)


def view_state(page) -> dict | None:
    """The region's state as its last processed or selected event left it:
    `open`, the deepest open layer of each branch, and `selected`, the selected
    node id; None before a report."""
    return page.evaluate(PANE_STATE_JS)


def record_texts(page, selectors) -> None:
    """Installs the recorder of the texts that the first element matching
    each selector of `selectors` takes (`TEXTS_RECORDER_JS`)."""
    page.evaluate(TEXTS_RECORDER_JS, list(selectors))


def recorded_texts(page, selector: str) -> list[str]:
    """The texts the element of `selector` has held since `record_texts`,
    its text at the start first."""
    return page.evaluate("(selector) => window.texts[selector]", selector)


def press_outside_fields(page, *keys: str) -> None:
    """Presses each of `keys` in turn, with no wait between them, with the
    focus on the page's body, outside every text field, where the window
    reads Alt+← and Alt+→ (AMD-MI-002 §3 rule 4; in a text field they move
    the cursor by a word on macOS and do nothing elsewhere)."""
    page.evaluate(BLUR_JS)
    for key in keys:
        page.keyboard.press(key)


def press_in_field(page, selector: str, key: str) -> bool:
    """Presses `key` with the focus in the text field of `selector` and
    answers whether the page prevented the browser's own reading of the
    key, as the event's defaultPrevented reads after every listener of the
    page (`KEY_PREVENTED_RECORDER_JS`). Headless Chromium does not act on
    the browser's own keys, such as Alt+← for a step back in the browser's
    history on Windows and Linux, so that the page's prevention is what a
    test reads (AMD-MI-002 §3 rule 4)."""
    page.evaluate(KEY_PREVENTED_RECORDER_JS)
    page.focus(selector)
    page.keyboard.press(key)
    return page.evaluate("() => window.keyPrevented")


def click_until(page, selector: str, condition, what: str, seconds: float = 6.0) -> None:
    """Clicks `selector` and waits for `condition`; a click that lands while
    the panel re-renders after a cursor event is lost by the browser, so the
    click is repeated every one and a half seconds until the condition
    holds or `seconds` have passed. A click on an element that has left the
    page, as the button of a panel the first click replaced, is a failed
    attempt and not an error: Playwright's TimeoutError after one and a half
    seconds is passed over, and the condition is waited for."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    started = time.perf_counter()
    while True:
        try:
            page.click(selector, timeout=1500)
        except PlaywrightTimeoutError:
            pass
        try:
            wait_until(condition, 1.5, what)
            return
        except AssertionError:
            if time.perf_counter() - started > seconds:
                raise


def select_until(
    page, node_id: str, graph_id: str, condition, what: str, seconds: float = 30.0
) -> None:
    """Selects the exact drawn node of the active graph and waits for
    `condition`, within `seconds` overall. A pending graph or node is
    retried; real clicks repeat every one and a half seconds (unit G, R57)."""
    started = time.perf_counter()
    selected_at = None
    while True:
        now = time.perf_counter()
        if now - started > seconds:
            raise AssertionError(f"{what} did not happen within {seconds} s")
        if selected_at is None or now - selected_at >= 1.5:
            clicked = page.evaluate(
                """([nodeId, graphId]) => {
                  const bar = document.querySelector('.bl-graph-bar');
                  if (!bar || bar.dataset.graph !== graphId) return false;
                  const drawn = Array.from(document.querySelectorAll(
                    '.bl-view-host .react-flow__node'))
                    .some(element => element.dataset.id === nodeId);
                  if (!drawn) return false;
                  (""" + SELECT_NODE_JS + """)([nodeId, graphId]);
                  return true;
                }""",
                [node_id, graph_id],
            )
            if clicked:
                selected_at = time.perf_counter()
        if selected_at is not None and condition():
            return
        time.sleep(0.05)


def click_line(page, line: int) -> None:
    """Puts the cursor on `line` of the editor with a click on it."""
    page.locator(".cm-content .cm-line").nth(line - 1).click()


def line_text(page, line: int) -> str:
    return page.evaluate(LINE_TEXT_JS, line)


def active_line(page) -> int | None:
    """The line number of the editor's active line, from the gutter."""
    text = page.evaluate(ACTIVE_LINE_JS)
    return int(text) if text else None


def status_text(page) -> str:
    return page.evaluate(STATUS_TEXT_JS)


# The selected occurrence as the main bar names it (design pass 10 §2):
# the path's two parts that name it, `periods[1] / cons`, where it marks
# them, else the note after the path, the occurrence the open file is bound
# as or the words that its source holds no occurrence of it; the empty
# string where the bar names none.
RECIPE_HEAD_JS = r"""
() => {
  const named = Array.from(document.querySelectorAll('.bl-crumbs .bl-occurrence-crumb'),
    (crumb) => crumb.textContent.trim());
  // the period and the key in either order: `periods[3] › tenure` in the
  // trellis view and at a chosen position, `tenure › periods[0]` in a stage's
  // view at no position chosen (the fix wave Q3b of unit Q, item 19; C19)
  if (named.length === 2) {
    const period = /^periods\[\d+\]$/.test(named[0]) ? 0 : 1;
    return `${named[period]} / ${named[1 - period]}`;
  }
  const note = document.querySelector('.bl-path-occurrence > .bl-path-note');
  return note ? note.textContent.trim() : '';
}
"""


def recipe_head(page) -> str:
    """The selected occurrence the main bar names, without the choice of
    positions or the links to recipes after its path (RECIPE_HEAD_JS):
    in the trellis view the occurrence selected; in a stage's view the
    occurrence the open file is bound as, which its path names in its last
    two parts since the fix wave Q3b of unit Q (item 19; C19), or the words
    that its source holds no occurrence of it; the empty string where the
    bar names none (unit K, K-D30; design pass 10 §2). The occurrence is
    written in the package's form, `periods[0] / tenure`."""
    return page.evaluate(RECIPE_HEAD_JS)


def form_field(rendered, label: str):
    """The field of a form that `rendered`, a render of `solara.render`,
    draws with the label `label`, a field of VSCode Elements (field.vue;
    design pass 8 §4; unit M, Task 6), as its finder."""
    import ipyvue

    return rendered.find(ipyvue.VueTemplate, label=label)


def enter_text(rendered, label: str, text: str) -> None:
    """Enters `text` in the field of `rendered` labeled `label`, as the
    field sends it on a keystroke, or on Enter for a field read when it is
    left (field.vue's event `entered`)."""
    form_field(rendered, label).widget.vue_entered(text)


def press_words(rendered, words: str) -> None:
    """Presses the one button of `rendered` whose words are `words`, a text
    button or a button of VSCode Elements (design pass 8 §5.3; unit M, Task
    6), as a click does."""
    import ipyvuetify

    (found,) = [
        widget
        for tag in ("button", "vscode-button")
        for widget in rendered.find(ipyvuetify.Html, tag=tag, children=[words]).widgets
    ]
    found.fire_event("click", {})


def choose_option(page, selector: str, text: str) -> None:
    """Chooses the option `text` of the select `selector` as a reader does:
    a click on the select, waited for, opens its list, which VSCode
    Elements' select draws in its own tree (design pass 8 §4), the page's
    one form of select since unit M's Task 7, and a click on the option
    that reads `text` chooses it."""
    page.locator(f"{selector} vscode-single-select").click()
    page.get_by_role("option", name=text, exact=True).click()


def used_at(page) -> list[tuple[str, str, str]]:
    """Where the panel's open stage file is used (AMD-MI-002 §3 rule 6),
    its rows `periods` and `also` (design pass §2): each recipe that holds
    the file, in the panel's order, as its path, its periods as the page
    prints them, `0–50`, after the recipe's path in `also`, and the
    occurrence its link shows, `periods[3]/tenure`; empty where the panel
    lists none."""
    return [tuple(found) for found in page.evaluate(USED_AT_JS)]


def details_until(page, expected: tuple, what: str, seconds: float = 10.0) -> None:
    """Waits until Details' head and rows, as the page prints them
    (DETAILS_ROWS_JS), the head's text and each row as `(key, lines)`,
    equal `expected` with the words the page prints (`printed_details`),
    since the page updates its elements in several messages and a new head
    can stand over the rows of the selection before it; fails with the last
    head and rows read."""
    expected = printed_details(expected)
    read = []

    def drawn() -> bool:
        head, rows = page.evaluate(DETAILS_ROWS_JS)
        read[:] = [(head, [tuple(row) for row in rows])]
        return read[0] == expected

    try:
        wait_until(drawn, seconds, what)
    except AssertionError:
        assert read[0] == expected, what


def occurrence_head(address: str) -> str:
    """The text with which Details' head begins while the stage occurrence
    `address`, `periods[1]/cons`, is selected in the trellis view: its key,
    then its period and a space (design pass §2)."""
    period, key = address.split("/")
    return f"{key} {period} "


def breadcrumb(page) -> str:
    """The text of the main bar's path, `lifecycle › spec.yml › periods[1]
    › cons`, without the buttons ← and → before it and what stands after
    it; the empty string where the page draws none."""
    path = page.locator(".bl-crumbs")
    return path.text_content() if path.count() else ""


def history_buttons(page) -> tuple[int, int]:
    """The numbers of the buttons ← and → the main bar draws enabled, each
    drawn always and disabled while no place stands behind or ahead
    (design pass 10 §3)."""
    enabled = ':not([aria-disabled="true"])'
    return (
        page.locator(f".bl-back{enabled}").count(),
        page.locator(f".bl-forward{enabled}").count(),
    )


def error_count(page) -> int:
    """The count the error mark at the end of the window's first row reads,
    0 where it reads none, as while nothing stands refused (AMD-MI-002 §6a
    rule 1); read in one call that does not wait, as `panel_heads` reads."""
    texts = page.locator(".bl-error-count").all_text_contents()
    return int(texts[0]) if texts else 0


def error_lines(page) -> list[tuple[str, str | None, int | None]]:
    """The lines of the list under the error mark, newest first, read
    whether the list is open or closed: each the triple of its sentence,
    its file and its line, the file and the line those of its link, the
    file alone where the line names no line, and None where it names
    neither (ERROR_LINES_JS); empty where nothing stands refused."""
    return [tuple(line) for line in page.evaluate(ERROR_LINES_JS)]


def error_group_lines(page, label: str) -> list[tuple[str, str | None, int | None]]:
    """The lines of the group `label` of the list under the error mark,
    `Errors`, `Connections to check` or `Headers to check`, as `error_lines`
    reads a line (ERROR_GROUP_LINES_JS); empty where the group does not
    stand."""
    return [tuple(line) for line in page.evaluate(ERROR_GROUP_LINES_JS, label)]


def toggle_errors(page) -> None:
    """Clicks the error mark, which opens the list under it where the list
    is closed and closes it where it is open, and waits until the list is
    shown, or hidden, in turn."""
    shown = page.locator(".bl-error-list").is_visible()
    page.click(".bl-error-mark")
    state = "hidden" if shown else "visible"
    page.wait_for_selector(".bl-error-list", state=state, timeout=10_000)


def panel_head(page) -> str:
    """The text of the panel's head, the empty string before a node is
    selected."""
    head = page.locator(".bl-panel-head")
    return head.text_content() if head.count() else ""


def panel_heads(page) -> str:
    """The text of every head of the panel, joined by a space, read in one
    call that does not wait, so that a head the panel removes while it is
    read gives the empty string; `panel_head` counts the heads and then
    reads one, and a head removed between the two reads makes Playwright
    wait 30 s and raise its TimeoutError."""
    return " ".join(page.locator(".bl-panel-head").all_text_contents())


def wait_until(condition, seconds: float, what: str):
    """Polls `condition` every 50 ms until it answers a true value, which
    is answered with the seconds waited; fails after `seconds` naming
    `what`."""
    started = time.perf_counter()
    while True:
        value = condition()
        if value:
            return value, time.perf_counter() - started
        if time.perf_counter() - started > seconds:
            raise AssertionError(f"{what} did not happen within {seconds} s")
        time.sleep(0.05)


def settled_status(page, digest: str, seconds: float = 8.0) -> re.Match:
    """The parsed status line once it prints `digest` and no pending
    mark."""

    def settled() -> str | None:
        found = status_text(page)
        return found if digest in found and STATUS.match(found) is not None else None

    text, _ = wait_until(settled, seconds, f"a status line with the digest {digest}")
    return STATUS.match(text)


def record(page, name: str):
    return page.evaluate(f"() => window.record.{name}")


def trellis_settled(page, relpath: str) -> str | None:
    """The status line's text once it names the trellis of the file
    `relpath` after a reading, read or refused, with no pending mark; None
    before."""
    text = status_text(page)
    pending = "elaborating" in text or "drawing" in text
    done = " · loop " in text or text.endswith(" · refused")
    return text if text.startswith(f"{relpath} · ") and done and not pending else None


def open_trellis(page, url: str, relpath: str, minimum: int = 20, timeout: int = 120_000) -> str:
    """Opens the page at `url`, opens the folders on the path of the
    trellis file or the recipe `relpath` (`reveal_in_tree`), clicks the file
    in the tree, waits for the trellis's status line and for the view to
    draw at least `minimum` texts; answers the status line."""
    page.goto(url)
    reveal_in_tree(page, relpath, timeout)
    page.click(f'.bl-tree-file[data-path="{relpath}"]')
    line, _ = wait_until(
        lambda: trellis_settled(page, relpath), timeout / 1000, f"the trellis of {relpath}"
    )
    wait_for_view(page, minimum, timeout)
    return line


# the select of the view's bar that restricts the trellis view, its text, its
# menu, an item of the menu and the field at the menu's foot (unit K, K-D17)
RESTRICTION = ".bl-restriction"
RESTRICTION_TEXT = ".bl-restriction .bl-restriction-text"
RESTRICTION_MENU = ".bl-restriction-menu"
RESTRICTION_ITEM = ".bl-restriction-item"
# the input of the field at the foot of the restriction's menu, VSCode
# Elements' text field, which Playwright's selectors reach (unit M, Task 7)
RESTRICTION_FIELD = ".bl-restriction-field input"


def restriction_shown(page) -> str:
    """The text of the restriction's select in the view's bar, `periods 0–2`,
    or `all` for the whole trellis."""
    return page.locator(RESTRICTION_TEXT).text_content().strip()


def open_restriction(page) -> None:
    """Opens the menu of the restriction's select where it is closed, the
    select waited for first."""
    page.wait_for_selector(RESTRICTION, timeout=30_000)
    if page.locator(RESTRICTION_MENU).count() == 0:
        page.click(RESTRICTION)
        page.wait_for_selector(RESTRICTION_MENU, timeout=10_000)


def restrict(page, text: str) -> None:
    """Types `text` in the field at the foot of the restriction's menu,
    opened where it is closed, and presses Enter, which applies the text
    and closes the menu."""
    open_restriction(page)
    page.fill(RESTRICTION_FIELD, text)
    page.press(RESTRICTION_FIELD, "Enter")


def choose_restriction(page, label: str) -> None:
    """Chooses the item of the restriction's menu, opened where it is
    closed, that prints `label`: a range, `0–5`, `all`, which the menu
    prints with the count of periods where a trellis is read, or a stage
    key."""
    open_restriction(page)
    count = r"( \d+)?" if label == "all" else ""
    words = re.compile(rf"^\s*{re.escape(label)}{count}\s*$")
    page.locator(RESTRICTION_ITEM).filter(has_text=words).click()


# the items of the restriction's menu as they are drawn, each its role, its
# text, whether it is checked and whether it is disabled, and the text of
# the field at the menu's foot; null while the menu is closed
RESTRICTION_MENU_JS = """
() => {
  const menu = document.querySelector('.bl-restriction-menu');
  if (!menu) return null;
  const items = Array.from(menu.querySelectorAll('.bl-restriction-item')).map((item) => [
    item.getAttribute('role'), item.textContent.trim(),
    item.getAttribute('aria-checked') === 'true', item.getAttribute('aria-disabled') === 'true']);
  return [items, menu.querySelector('.bl-restriction-field').value];
}
"""


def restriction_menu_shown(page) -> tuple[list[tuple], str] | None:
    """The items of the restriction's menu as drawn, each its role, `radio`
    for a range or `checkbox` for a stage key, its text, whether it is
    checked and whether it is disabled, and the text of the field at its
    foot; None while the menu is closed."""
    found = page.evaluate(RESTRICTION_MENU_JS)
    return None if found is None else ([tuple(item) for item in found[0]], found[1])


# the keys of a port's attributes a join adds in a trellis view
JOIN_KEYS = ("join", "paired by", "outside")


def stage_nodes(collection: dict, graph: str) -> dict:
    """The nodes of a stage view's graph `graph` but its own `Inputs` and
    `Outputs`, by id, each as its label, namespace, attributes, style,
    ports without the keys `JOIN_KEYS`, and incoming edges whose source is
    no boundary node: the part of a stage view a trellis view repeats for
    an occurrence (specification §3.1)."""
    nodes = graph_named(collection, graph)["nodes"]
    boundary = ("GraphInputs", "GraphOutputs")
    return {
        node["id"]: {
            "label": node["label"],
            "namespace": node.get("namespace") or "",
            "attrs": node.get("attrs"),
            "style": node.get("style"),
            "ports": [
                (item["id"], [pair for pair in item["attrs"] if pair["key"] not in JOIN_KEYS])
                for side in ("inputsMetadata", "outputsMetadata")
                for item in node.get(side) or []
            ],
            "edges": sorted(
                (edge["sourceNodeId"], edge["sourceNodeOutputId"], edge["targetNodeInputId"])
                for edge in node.get("incomingEdges") or []
                if edge["sourceNodeId"] not in boundary
            ),
        }
        for node in nodes
        if node["id"] not in boundary
    }


def occurrence_nodes(collection: dict, graph: str, occurrence: str) -> dict:
    """The nodes of the occurrence `occurrence`, `periods[1]/cons`, in a
    trellis view's graph `graph`, in the form of `stage_nodes`, every id and
    namespace without the occurrence's prefix, which the exporter adds, and
    no edge of a join: the incoming edges from outside the occurrence are
    left out."""
    prefix = occurrence + "/"

    def inner(text):
        return text[len(prefix) :] if text.startswith(prefix) else None

    boundary = ("GraphInputs", "GraphOutputs")
    found = {}
    for node in graph_named(collection, graph)["nodes"]:
        own = inner(node["id"])
        if own is None or own in boundary:
            continue
        namespace = node.get("namespace") or ""
        found[own] = {
            "label": node["label"],
            "namespace": "" if namespace == occurrence else inner(namespace),
            "attrs": node.get("attrs"),
            "style": node.get("style"),
            "ports": [
                (
                    inner(item["id"]),
                    [pair for pair in item["attrs"] if pair["key"] not in JOIN_KEYS],
                )
                for side in ("inputsMetadata", "outputsMetadata")
                for item in node.get(side) or []
            ],
            "edges": sorted(
                (
                    inner(edge["sourceNodeId"]),
                    inner(edge["sourceNodeOutputId"]),
                    inner(edge["targetNodeInputId"]),
                )
                for edge in node.get("incomingEdges") or []
                if inner(edge["sourceNodeId"]) not in (None, *boundary)
            ),
        }
    return found


def open_workbench(page, url: str, timeout: int = 60_000) -> None:
    """Opens the page at `url` and waits for the folder's buttons."""
    page.goto(url)
    page.wait_for_selector(".bl-new-trellis", timeout=timeout)


def fill_new_trellis(
    page, name: str, template_ids, repeat: int, parent: Path | None = None
) -> None:
    """Opens the form "new trellis", types, where `parent` is given, that
    folder as the parent folder in place of the folder that holds the open
    model folder, and waits for the form's note to name it (unit L, Task
    13); types the
    folder's name and the number of periods, chooses each template of
    `template_ids` under its own key, and presses `write the folder`."""
    page.click(".bl-new-trellis")
    page.wait_for_selector('.bl-form[data-form="new trellis"]', timeout=30_000)
    if parent is not None:
        field = ".bl-create-parent input"
        page.fill(field, str(parent))
        page.press(field, "Enter")
        named = f"writes {Path(parent).name}/<name>/"
        wait_until(
            lambda: page.locator(".bl-form .bl-form-note").first.text_content().startswith(named),
            10.0,
            "the note naming the parent folder typed",
        )
    page.fill(".bl-create-name input", name)
    page.fill(".bl-create-repeat input", str(repeat))
    for template_id in template_ids:
        page.click(f'.bl-template-button[data-template="{template_id}"]')
        page.wait_for_selector(f'.bl-template.bl-active[data-template="{template_id}"]')
    page.click(".bl-create-submit")


# The forms of the page, each by the words `open_page_form` takes: the
# value of its `data-form`, or `from a folder` for the form "add stage"
# that the stage list's item `From a folder…` opens (unit L, Task 9).
PAGE_FORMS = (
    "new trellis",
    "new variant",
    "new stage",
    "add stage",
    "from a folder",
    "add period",
    "commit",
)


def open_page_form(page, form: str) -> str:
    """Opens the form `form` of PAGE_FORMS as a reader does, over the
    forward trellis graph of a recipe of a model folder that a repository
    holds: `new trellis`, `new variant` and `new stage` by the folder bar's
    buttons; `add stage` and `add period` by Goto Anything's commands
    (`goto_command`); `from a folder` by a click on the item `From a
    folder…` of the list the button `stages` opens; `commit` by git's
    line's button, the status line's details shown first (`show_status`).
    Waits for the form and answers the selector of its element; the form's
    `cancel` closes it."""
    selector = f'.bl-form[data-form="{"add stage" if form == "from a folder" else form}"]'
    if form in ("new trellis", "new variant", "new stage"):
        page.click(f".bl-{form.replace(' ', '-')}")
    elif form in ("add stage", "add period"):
        goto_command(page, form)
    elif form == "from a folder":
        open_stage_list(page)
        page.click('.bl-view-host .bf-stage-item[data-kind="folder"]')
    elif form == "commit":
        show_status(page)
        page.click(".bl-git-commit")
    else:
        raise ValueError(f"no form {form!r} among {PAGE_FORMS}")
    page.wait_for_selector(selector, timeout=30_000)
    return selector


def replace_in_editor(page, find: str, replacement: str) -> None:
    """Replaces every occurrence of `find` in the editor's document by
    `replacement` through CodeMirror's own search panel, as a reader would:
    Mod-f opens it, its two fields are filled and committed, `replace all`
    replaces, and Escape closes it. The change is the editor's own, so the
    loop receives it after the pause, and a line the editor wraps at column
    78 is edited whole."""
    page.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+f")
    for name, text in (("search", find), ("replace", replacement)):
        field = page.locator(f".cm-search input[name={name}]")
        field.fill(text)
        field.dispatch_event("change")
    page.click(".cm-search button[name=replaceAll]")
    page.keyboard.press("Escape")


def open_tree_file(page, relpath: str, timeout: int = 30_000) -> None:
    """Opens the folders on the path of `relpath` (`reveal_in_tree`), clicks
    the file in the tree and waits until it is the open file."""
    reveal_in_tree(page, relpath, timeout)
    page.click(f'.bl-tree-file[data-path="{relpath}"]')
    page.wait_for_selector(f'.bl-tree-file.bl-open[data-path="{relpath}"]', timeout=timeout)


def show_status(page) -> None:
    """Shows the details of the status line, the line of the inputs'
    digests, counts and seconds and git's line, where they are hidden: a
    click on the icon button `More` (spec 0.4 §5.7; R-D9; design pass 8
    §6), whose `aria-expanded` says whether they are shown."""
    if page.locator(".bl-status-toggle").get_attribute("aria-expanded") == "false":
        page.click(".bl-status-toggle")
    page.wait_for_selector(".bl-git-line", state="visible")


def git_line_sentence(page) -> str:
    """The sentence git's line prints: git's own sentence of the last
    command, or the sentence of the last export, where neither was refused;
    the empty string before any command or export and after a refused one,
    whose sentence stands in the list under the error mark (`error_lines`;
    AMD-MI-002 §6a rule 1)."""
    found = page.locator(".bl-git-sentence")
    return found.text_content() if found.count() else ""


def checklist_count(page) -> int:
    """The number of entries answers.yml marks that the head of the
    checklist under the tree counts, `2 entries to check` (unit K, K-D16
    and K-D28); 0 where the head counts none or no checklist is drawn."""
    found = page.locator(".bl-problem-check")
    return int(found.get_attribute("data-count")) if found.count() else 0


# the count of the entries to check in the head of the checklist, `2
# entries to check` or `1 entry to check`
CHECKLIST_CHECK = re.compile(r"(\d+) entr(?:y|ies) to check")


# the keywords of the slots the Recipe tab's entries write, each once in
# the order the table first writes it, read at one moment (unit M, Task 10):
# the text of each slot of a row at rest and the option chosen in each
# select of the open row and of the trellis row (design pass 11 §2)
SLOT_KEYWORDS_JS = """
() => {
  const found = [];
  const entries = '.bl-recipe-table .bl-recipe-slot, '
    + '.bl-recipe-table .bl-recipe-entry vscode-single-select';
  for (const entry of document.querySelectorAll(entries)) {
    const chosen = entry.matches('vscode-single-select')
      ? entry.querySelector('vscode-option[selected]') : entry;
    const text = chosen ? chosen.textContent.trim() : '';
    if (text.startsWith('$') && !found.includes(text.slice(1))) found.push(text.slice(1));
  }
  return found;
}
"""


def slot_keywords(page) -> list[str]:
    """The keywords the recipe's slots take, `["fill"]` for the durables
    model's recipe (unit K, K-D29), read from the entries of the Recipe tab,
    which stands while the recipe is the open file (unit M, Task 10; design
    pass 9 §§3 and 5: the line `slots` left with the recipe region), each
    slot's keyword once in the order in which the table first writes it, by its
    rows, the kinds and each stage's lists, a row at rest by its texts and the
    open row by its selects (design pass 11 §2); the empty list where the tab
    is not drawn or the recipe writes no slot. The keywords are read at one
    moment, so that a table drawn again with fewer slots while it is read gives
    no keyword the page no longer holds (unit K's fix wave, §6 item 5 of the
    final judgment)."""
    return page.evaluate(SLOT_KEYWORDS_JS)


# The rows of the Recipe tab as the page draws them (design pass 11 §2), by
# the stage's key: whether the row is open, its aria-expanded; the text of
# each of its lines in the order drawn, the line's key, texts, range list's
# periods and mark `—` joined by a space, a select of the open row giving
# no text; and the number of selects the row holds.
RECIPE_ROWS_JS = r"""
() => Object.fromEntries(Array.from(
  document.querySelectorAll('.bl-recipe-table .bl-recipe-row'), (row) => [row.dataset.stage, {
    expanded: row.getAttribute('aria-expanded') === 'true',
    texts: Array.from(row.querySelectorAll('.bl-recipe-line'), (line) => Array.from(
      line.querySelectorAll('.bl-recipe-key, .bl-recipe-text, .bl-recipe-range, .bl-recipe-none'),
      (part) => part.textContent.trim()).join(' ')),
    selects: row.querySelectorAll('vscode-single-select').length,
  }]))
"""


def open_recipe_row(page, key: str) -> None:
    """Opens the Recipe tab's row of the stage `key` as a reader does (design
    pass 11 §2): a click on the row's key, then a wait of at most 10 s for
    the row's aria-expanded "true" with its controls drawn, the periods
    field among them, which can reach the page in a later message than the
    attribute."""
    row = f'.bl-recipe-row[data-stage="{key}"]'
    page.click(f"{row} .bl-recipe-key")
    page.wait_for_selector(f'{row}[aria-expanded="true"] .bl-recipe-periods', timeout=10_000)


def recipe_rows_at_rest(page) -> dict:
    """The rows of the Recipe tab as RECIPE_ROWS_JS reads them, by the
    stage's key, `{"expanded": False, "texts": ["tenure tenure.bl",
    "durables", "$fill", …, "All"], "selects": 0}` for a row at rest, the
    open row's `expanded` True (design pass 11 §2)."""
    return page.evaluate(RECIPE_ROWS_JS)


def with_each_recipe_row_open(page, read) -> dict:
    """`read(page)` answered with each row of the Recipe tab open in turn,
    by the stage's key, in the table's order (design pass 11 §2): the row
    opened as a reader opens it (`open_recipe_row`), the pointer then moved
    to the graph's canvas, so that no hover stands in the tab, and every
    other row read standing at rest, with no select, before `read` is
    called."""
    found = {}
    for key in recipe_rows_at_rest(page):
        open_recipe_row(page, key)
        page.mouse.move(1200, 500)

        def alone() -> bool:
            rows = recipe_rows_at_rest(page)
            return all(
                (row["expanded"], row["selects"] > 0) == (stage == key, stage == key)
                for stage, row in rows.items()
            )

        wait_until(alone, 10.0, f"{key}'s row open and every other at rest")
        found[key] = read(page)
    return found


def rendered_recipe_rows(rendered) -> dict:
    """The rows of the Recipe tab that `rendered`, a render of
    `solara.render`, draws, each the widget of its element by the stage's
    key, in the table's order: a row at rest has the class `bl-recipe-row`
    alone and the open row also `bl-recipe-open` (design pass 11 §2)."""
    import ipyvuetify

    (table,) = rendered.find(ipyvuetify.Html, class_="bl-recipe-table").widgets
    return {
        child.attributes["data-stage"]: child
        for child in table.children
        if getattr(child, "class_", None) in ("bl-recipe-row", "bl-recipe-row bl-recipe-open")
    }


def open_rendered_recipe_row(rendered, key: str) -> None:
    """Opens the row of the stage `key` of the Recipe tab that `rendered`
    draws, as a click on the row does (`app.open_recipe_row`; design pass
    11 §2), and checks that it alone stands open."""
    rendered_recipe_rows(rendered)[key].fire_event("click", {})
    expanded = {
        stage: row.attributes["aria-expanded"]
        for stage, row in rendered_recipe_rows(rendered).items()
    }
    assert expanded == {stage: "true" if stage == key else "false" for stage in expanded}, expanded


def open_checklist(page) -> None:
    """Unfolds the checklist under the tree with a click on its head where
    it is folded, and waits for its list (unit K, K-D16)."""
    button = page.locator(".bl-error-mark")
    if button.get_attribute("aria-expanded") != "true":
        button.click()
    page.wait_for_selector(".bl-error-list", state="visible")


def commit_form_paths(page) -> set[str]:
    """The paths the commit form lists, by their attribute data-path."""
    rows = page.locator(".bl-commit-path")
    return {rows.nth(number).get_attribute("data-path") for number in range(rows.count())}


# --- the view laid out and at rest, before a screenshot (unit C, Task 9) ---


def record_layouts(page) -> None:
    """Records each processed event's count, exact collection and graph,
    from zero; a second call on the same document counts from zero again
    with the one listener (unit S, where `lay_out_left_to_right` may have
    installed it before the test does)."""
    page.evaluate(LAYOUT_RECORDER_JS)


def layouts_recorded(page) -> int:
    """The number of layouts the region reported since `record_layouts` ran."""
    return page.evaluate(VIEW_STATE_JS)["processed"]


def view_laid_out(page, name: str, since: int = -1) -> bool:
    """Whether the region holds a collection whose label starts with `name`
    and has reported its layout since `since`, with the same collection
    and active graph now held (VIEW_STATE_JS)."""
    state = page.evaluate(VIEW_STATE_JS)
    label = (state["label"] or "").split(" ")[0]
    done = state["processed"] > since and state["current"] and not state["busy"]
    return label == name and done


def seconds_to_the_drawn_trellis(
    browser, folder: Path, cache: Path, log_path: Path, entry: Path | None = None
) -> float:
    """Unit G, item 4: seconds from navigation to the trellis drawn by the
    graph region (`view_laid_out`), counted as the trellis load's item 6
    counts them. A new server uses `folder` and the cache folder `cache`, in
    which it keeps the stage views and the bindings, and is stopped after
    the reading; where `entry`, the entry of a binding under `cache`, is
    given, the server is stopped only once that file stands, which is
    waited for after the seconds are counted."""
    port = free_port()
    url = f"http://localhost:{port}/"
    process = start_server(folder, port, log_path, cache_home=cache)
    context = None
    try:
        context, tab = new_tab(browser)
        error = server_error(url, process, log_path)
        assert error is None, error
        started = time.perf_counter()
        tab.goto(url)
        record_layouts(tab)
        tab.wait_for_function("() => window.laidOut.count > 0", timeout=120_000)
        wait_until(lambda: view_laid_out(tab, "trellis", 0), 60.0, "the trellis drawn")
        seconds = time.perf_counter() - started
        if entry is not None:
            wait_until(entry.is_file, 30.0, "the binding kept on disk")
        return seconds
    finally:
        if context is not None:
            context.close()
        stop_server(process)


# Python runs this file in the probe, command and fresh Solara interpreter.
# It is written only into the scratch install, never into either wheel.
INSTALLED_STARTUP_PY = r"""
import importlib
import json
import os
import sys
from pathlib import Path

record = {"pid": os.getpid(), "ppid": os.getppid(), "error": None}
try:
    target = Path(__file__).resolve().parent
    record.update(
        argv=sys.orig_argv,
        cwd=str(Path.cwd().resolve()),
        pythonpath=os.environ.get("PYTHONPATH"),
        bellman_root=os.environ.get("BELLMAN_DDSL_ROOT"),
        startup=str(Path(__file__).resolve()),
        cache=os.environ.get("SOLARA_ASSETS_PROXY_CACHE_DIR"),
        removed=[getattr(finder, "__module__", "") for finder in sys.meta_path
                 if getattr(finder, "__module__", "") in EDITABLE_FINDERS],
    )
    sys.meta_path[:] = [finder for finder in sys.meta_path
                       if getattr(finder, "__module__", "") not in EDITABLE_FINDERS]
    record["remaining"] = [getattr(finder, "__module__", "") for finder in sys.meta_path]
    record["cache_resolved"] = str(Path(record["cache"]).resolve()) if record["cache"] else None
    if EDITABLE_FINDERS.intersection(record["remaining"]):
        raise RuntimeError("A Bellman editable finder remains installed.")
    if record["pythonpath"] != str(target) or "BELLMAN_DDSL_ROOT" in os.environ:
        raise RuntimeError("The installed process can read a checkout from its environment.")
    if Path.cwd().resolve() != target.parent:
        raise RuntimeError("The installed process did not start outside the checkout.")
    record["packages"] = {}
    for name in ("bellman", "bellman_workbench"):
        package = importlib.import_module(name)
        origin = str(Path(package.__file__).resolve())
        paths = [str(Path(path).resolve()) for path in package.__path__]
        record["packages"][name] = {"file": origin, "paths": paths}
        if not paths or any(not Path(path).is_relative_to(target) for path in [origin, *paths]):
            raise RuntimeError(f"{name} was imported from outside the installed target.")
except BaseException as error:
    record["error"] = f"{type(error).__name__}: {error}"
try:
    directory = Path(os.environ["BELLMAN_WORKBENCH_STARTUP_RECORDS"])
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / f"{os.getpid()}.json").open("x", encoding="utf-8") as output:
        json.dump(record, output, sort_keys=True)
except BaseException as error:
    print(f"Cannot record installed-process startup: {error}", file=sys.stderr)
    raise SystemExit(86)
if record["error"] is not None:
    print(record["error"], file=sys.stderr)
    raise SystemExit(86)
"""


def installed_startup_records(site: Path, cache_home: Path) -> dict[int, dict]:
    """The successful startup records of this scratch install (R20, R65).
    Missing records and origins outside the target are refused. These are
    top-level package origins, not an inventory of later module imports."""
    target = site.resolve()
    records = {}
    for path in sorted((cache_home / "installed-startup").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["error"] is None, record
        assert path.stem == str(record["pid"]) and record["pid"] not in records, record
        assert record["pythonpath"] == str(target) and record["bellman_root"] is None, record
        assert record["cwd"] == str(target.parent), record
        assert record["startup"] == str(target / "sitecustomize.py"), record
        assert set(record["removed"]) <= EDITABLE_FINDERS, record
        assert not EDITABLE_FINDERS.intersection(record["remaining"]), record
        assert set(record["packages"]) == {"bellman", "bellman_workbench"}, record
        for package in record["packages"].values():
            assert package["paths"], record
            assert all(
                Path(value).is_relative_to(target)
                for value in [package["file"], *package["paths"]]
            ), record
        records[record["pid"]] = record
        print(f"item 5 startup record: {path.resolve()}")
    assert records, f"No installed-process startup records in {cache_home}"
    return records


def stop_installed_server(process, cache_home: Path) -> None:
    """Stops the owned installed-server process group and checks its exit
    before target permissions are restored (unit G, item 5; R65). macOS
    refuses a signal to a group whose last process is exiting with
    `PermissionError`; the group is then asked again until the deadline,
    as while it runs (G-R82)."""
    # start_installed_server creates the group with the outer command's PID.
    group = process.pid
    recorded = {group}
    for path in (cache_home / "installed-startup").glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("ppid") == group:
                recorded.add(int(record["pid"]))
        except (OSError, ValueError, KeyError, TypeError):
            # Failed startup must not prevent termination of the owned group.
            pass
    for sent in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(group, sent)
        except (ProcessLookupError, PermissionError):
            pass
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            process.poll()
            try:
                os.killpg(group, 0)
            except ProcessLookupError:
                process.wait(timeout=1)
                for pid in recorded:
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        continue
                    raise AssertionError(f"Installed process {pid} survived group cleanup")
                print(f"item 5 cleanup: processes {sorted(recorded)} exited")
                return
            except PermissionError:
                # a process of the group is exiting; ask again
                pass
            time.sleep(0.05)
    raise AssertionError(f"Installed-server process group {group} did not exit")


def installed_environment(site: Path, cache_home: Path) -> dict:
    """The environment of a process of the Workbench installed in `site`
    alone: `os.environ` without `BELLMAN_DDSL_ROOT`, with `PYTHONPATH`
    naming `site`, `XDG_CACHE_HOME` naming `cache_home`, no bytecode
    written, and every proxy variable naming CLOSED, `localhost` and
    127.0.0.1 excepted (unit G, item 5; R20)."""
    environment = {key: value for key, value in os.environ.items() if key != "BELLMAN_DDSL_ROOT"}
    environment.update(
        PYTHONPATH=str(site.resolve()),
        BELLMAN_WORKBENCH_STARTUP_RECORDS=str((cache_home / "installed-startup").resolve()),
        PYTHONDONTWRITEBYTECODE="1",
        XDG_CACHE_HOME=str(cache_home.resolve()),
        NO_PROXY="localhost,127.0.0.1",
        no_proxy="localhost,127.0.0.1",
    )
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        environment[name] = environment[name.lower()] = CLOSED
    return environment


def installed_workbench(site: Path, work: Path) -> Path:
    """`site` holding the packages `bellman` and `bellman-workbench`, each
    built as a wheel from a copy of its folder under `work` (`pip wheel
    --no-deps --no-build-isolation --no-index`, so that nothing is fetched
    and the checkout gains no build folder) and installed by `pip install
    --no-deps --no-index --target site`; every file and folder of `site` is
    then made read-only (G-D12). Answers `site`."""
    site, work = site.resolve(), work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    copies = []
    for name, skipped in (("bellman", ("tests",)), ("bellman-workbench", ("tests", "js"))):
        copy = work / name
        shutil.copytree(
            ROOT / "packages" / name,
            copy,
            ignore=shutil.ignore_patterns("__pycache__", "build", "*.egg-info", *skipped),
        )
        copies.append(str(copy))
    pip = [sys.executable, "-m", "pip", "-q", "--disable-pip-version-check"]
    wheels = work / "wheels"
    build = ["wheel", "--no-deps", "--no-build-isolation", "--no-index", "-w", str(wheels)]
    environment = {**os.environ, "PIP_CACHE_DIR": str(work / "pip-cache")}
    subprocess.run([*pip, *build, *copies], cwd=work, env=environment, check=True)
    built = [str(path) for path in sorted(wheels.glob("*.whl"))]
    install = ["install", "--no-deps", "--no-index", "--target", str(site)]
    subprocess.run([*pip, *install, *built], cwd=work, env=environment, check=True)
    # The startup file is test-only and is added after both wheels (R65).
    with (site / "sitecustomize.py").open("x", encoding="utf-8") as startup:
        startup.write(f"EDITABLE_FINDERS = {EDITABLE_FINDERS!r}\n" + INSTALLED_STARTUP_PY)
    for path in sorted(wheels.glob("*.whl")):
        print(f"item 5 wheel: {path}: {path.stat().st_size} bytes")
    try:
        for path in [site, *site.rglob("*")]:
            path.chmod(path.stat().st_mode & ~0o222)
    except BaseException:
        writable(site)
        raise
    return site


def writable(folder: Path) -> None:
    """Gives the owner write permission on `folder` and on everything under
    it, so that a read-only install can be removed."""
    for path in [folder, *folder.rglob("*")]:
        path.chmod(path.stat().st_mode | 0o200)


def unmet_requirements(site: Path, extras: dict[str, set[str]]) -> list[str]:
    """The requirements of the distributions installed in `site` that the
    running interpreter's environment does not meet: each requirement of a
    distribution's metadata, one of an extra counted where `extras` names
    that extra for the distribution, whose package is absent or whose
    installed version its specifier excludes (G-D20)."""
    from importlib import metadata

    from packaging.requirements import Requirement

    unmet = []
    for info in sorted(site.glob("*.dist-info")):
        distribution = metadata.PathDistribution(info)
        wanted = ("", *extras.get(distribution.metadata["Name"], ()))
        for text in distribution.requires or ():
            requirement = Requirement(text)
            marker = requirement.marker
            counted = marker is None or any(marker.evaluate({"extra": e}) for e in wanted)
            if not counted:
                continue
            try:
                version = metadata.version(requirement.name)
            except metadata.PackageNotFoundError:
                unmet.append(text)
                continue
            if version not in requirement.specifier:
                unmet.append(f"{text} ({version} installed)")
    return unmet


def start_installed_server(site: Path, folder: Path, port: int, log_path: Path, cache_home: Path):
    """The console command of the Workbench installed in `site`, `python -m
    bellman_workbench.command <folder> --port <port> --no-open`, run from
    `site`'s parent in `installed_environment`; its output is written to
    `log_path`. Its new process group is owned by this test (R65).
    Answers the process."""
    if os.name != "posix":
        raise RuntimeError("The installed-server cleanup requires a POSIX process group.")
    records = cache_home / "installed-startup"
    records.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "-m", "bellman_workbench.command", str(folder)]
    print(f"item 5 installed-server log: {log_path.resolve()}")
    print(f"item 5 server startup records: {records.resolve()}")
    with log_path.open("w", encoding="utf-8") as log:
        return subprocess.Popen(
            [*command, "--port", str(port), "--no-open"],
            cwd=site.resolve().parent,
            start_new_session=True,
            env=installed_environment(site, cache_home),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )


# Marks each element under the first element the selector given names that
# holds text of its own with `data-font-probe`, numbered in document order,
# and answers the elements' texts in that order; the marks of an earlier
# call are removed first, so that no number names two elements.
FONT_PROBE_JS = """
(under) => {
  for (const marked of document.querySelectorAll('[data-font-probe]')) {
    marked.removeAttribute('data-font-probe');
  }
  const host = document.querySelector(under);
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
  const elements = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const element = node.parentElement;
    if (node.textContent.trim() && element && !elements.includes(element)
        && !element.closest('style, script')) elements.push(element);
  }
  elements.forEach((element, index) => element.setAttribute('data-font-probe', String(index)));
  return elements.map((element) => element.textContent.trim());
}
"""


def fonts_drawn(page, under: str = ".bl-view-host") -> dict[str, set[str]]:
    """The faces in which Chromium drew the texts under the first element
    `under` names, the graph region's host unless another is given, by
    text: for each element FONT_PROBE_JS marks, the families
    `platform_faces` answers."""
    texts = page.evaluate(FONT_PROBE_JS, under)
    faces: dict[str, set[str]] = {}
    for text, found in zip(texts, platform_faces(page, "data-font-probe", len(texts))):
        faces.setdefault(text, set()).update(found)
    return faces


def view_still(page, pause_ms: int = 300) -> bool:
    """Whether the settled collection and rendered region remain exactly
    unchanged across `pause_ms`, including their geometry and viewport."""
    snapshot = """
    () => {
      const host = document.querySelector('.bl-view-host');
      const viewport = host && host.querySelector('.react-flow__viewport');
      if (!host || !viewport || !host.bellmanFlow || !window.laidOut) return null;
      if (document.querySelector('.bl-pending')) return null;
      const flow = host.bellmanFlow;
      const collection = flow.collection();
      const state = (""" + VIEW_STATE_JS + """)();
      if (!collection || !state.current || state.busy || state.processed <= 0 ||
          flow.layouts() <= 0 || document.fonts.status !== 'loaded') return null;
      if (host.getAnimations({subtree: true})
          .some(a => a.pending || a.playState === 'running')) return null;
      const rectangle = element => {
        const r = element.getBoundingClientRect();
        return [r.x, r.y, r.width, r.height];
      };
      const bounds = rectangle(host), view = rectangle(viewport);
      if (bounds[2] <= 0 || bounds[3] <= 0 || view[2] <= 0 || view[3] <= 0) return null;
      return {
        collection, state, layouts: flow.layouts(),
        open: flow.openLayers(), selection: flow.selection(),
        markup: host.outerHTML,
        rectangles: [bounds, ...Array.from(host.querySelectorAll('*'), rectangle)],
        transform: getComputedStyle(viewport).transform
      };
    }
    """
    first = page.evaluate(snapshot)
    page.wait_for_timeout(pause_ms)
    second = page.evaluate(snapshot)
    return first is not None and first == second


def occurrences_of(collection: dict, graph: str) -> set[str]:
    """The stage occurrences the graph `graph` of a trellis view's collection
    holds, each as `periods[h]/<key>`, read from its nodes' namespaces."""
    return {
        "/".join(node["namespace"].split("/")[:2])
        for node in graph_named(collection, graph)["nodes"]
        if node.get("namespace")
    }


def join_labels(collection: dict, graph: str) -> set[str]:
    """The labels of the joins the graph `graph` of a trellis view's
    collection draws, the values of the attribute `join` on its nodes'
    ports, such as `inter_connectors[0] a → k` and `m_next → m`."""
    return {
        pair["value"]
        for node in graph_named(collection, graph)["nodes"]
        for side in ("inputsMetadata", "outputsMetadata")
        for item in node.get(side) or []
        for pair in item["attrs"]
        if pair["key"] == "join"
    }


# the mapping that heads an entry of a join's text, `inter_connectors[1] `
JOIN_MAPPING = re.compile(r"^inter_connectors\[\d+\] ")


def joined_states(graph: dict) -> set[str]:
    """The state fields the joins of the trellis graph `graph` name, read
    from the attribute `join` of its ports, whose entries, `[mapping ]field[
    → arrival]`, the exporter joins by `; ` (unit L, Task 31)."""
    found = set()
    for node in graph["nodes"]:
        for side in ("inputsMetadata", "outputsMetadata"):
            for item in node.get(side) or []:
                text = attribute_of(item, "join")
                for entry in text.split("; ") if text else ():
                    found.update(JOIN_MAPPING.sub("", entry).split(" → "))
    return found


def carried_functions(graph: dict) -> set[str]:
    """The names of the functions the joins of the backward trellis graph
    `graph` carry, each as the package prints a function's name
    (`function_name`): the field of each reading port that names a join and
    whose role is one of the package's value roles, the last part of the
    wire's identity in the port's id,
    `periods[0]/keeper_cons/keeper_cons:function:cntn:dV_a` giving `𝑑𝑉_a`
    (AAS, L-D26; unit L, Task 31)."""
    from bellman.native.labels import function_name
    from bellman.syntax.vocabulary import VALUE_ROLES

    return {
        function_name(item["id"].rsplit(":", 1)[1])
        for node in graph["nodes"]
        for item in node.get("inputsMetadata") or []
        if attribute_of(item, "join") and attribute_of(item, "role") in VALUE_ROLES
    }


def in_function_italic(name: str) -> bool:
    """Whether `name` is written as the package writes a function's name:
    the letters before its first underscore in mathematical italic, the
    rest as the file writes it, `𝑑𝑉_a` (`bellman.native.labels.italic`)."""
    from bellman.native.labels import italic

    head = name.split("_", 1)[0]
    return bool(head) and italic(head) == head and not head.isascii()


# Each box the region draws, by its id: the text of its label, the text of
# its method mark (null where none), the colors of its symbol and of its
# mark, the color of its border, whether its label stands whole inside it,
# and its outline's color, width, offset and style.
BOX_DRAWN_JS = """
() => Object.fromEntries(Array.from(
  document.querySelectorAll('.bl-view-host .react-flow__node'), (node) => {
  const box = node.querySelector(':scope > .bf-box');
  const name = node.querySelector('.bf-name');
  const symbol = node.querySelector('.bf-symbol');
  const mark = node.querySelector('.bf-mark');
  const style = box ? getComputedStyle(box) : null;
  return [node.dataset.id, {
    text: name ? name.textContent : null,
    mark: mark ? mark.textContent : null,
    symbolColor: symbol ? getComputedStyle(symbol).color : null,
    markColor: mark ? getComputedStyle(mark).color : null,
    border: style ? style.borderTopColor : null,
    whole: name ? name.scrollWidth <= name.clientWidth + 1 : null,
    outline: style
      ? [style.outlineColor, style.outlineWidth, style.outlineOffset, style.outlineStyle]
      : null,
  }];
}))
"""

# the color a custom property of brand.css holds, as the browser computes
# the color of an element whose color is that property
PROPERTY_COLOR_JS = """
(name) => {
  const probe = document.createElement('span');
  probe.style.color = `var(${name})`;
  document.body.append(probe);
  const color = getComputedStyle(probe).color;
  probe.remove();
  return color;
}
"""


def property_color(page, name: str) -> str:
    """The color the custom property `name` of brand.css holds in the page,
    as the browser computes a color (PROPERTY_COLOR_JS)."""
    return page.evaluate(PROPERTY_COLOR_JS, name)


def bound_as_the_recipe_binds(folder: Path, text: str, relpath: str):
    """Spec 0.4 §2.1: the stage of the stage file `relpath` of the model folder `folder`,
    its text `text`, bound as the folder's first source binds it, as the
    page binds a file opened from the tree (`recipe.find_occurrence`,
    `recipe.bind_occurrence`)."""
    from bellman.stage import elaborate_text
    from bellman_workbench import model, recipe

    opened = model.open_folder(folder)
    sources = recipe.model_sources(opened)
    found = recipe.find_occurrence(opened, sources[0] if sources else None, relpath)
    return recipe.bind_occurrence(elaborate_text(text, found.origin), found).stage


# The region's viewport: the translation and the scale of React Flow's
# viewport element, and the host's width and height, in pixels.
VIEWPORT_JS = """
() => {
  const element = document.querySelector('.bl-view-host .react-flow__viewport');
  if (!element) return null;
  const matrix = new DOMMatrixReadOnly(getComputedStyle(element).transform);
  const host = document.querySelector('.bl-view-host').getBoundingClientRect();
  return {x: matrix.e, y: matrix.f, zoom: matrix.a, width: host.width, height: host.height};
}
"""

# the place of each box the region draws on the graph, by its id: the
# translation of its element, React Flow drawing every box at its place on
# the graph
NODE_POSITIONS_JS = """
() => Object.fromEntries(Array.from(
  document.querySelectorAll('.bl-view-host .react-flow__node'), (node) => {
  const matrix = new DOMMatrixReadOnly(getComputedStyle(node).transform);
  return [node.dataset.id, [matrix.e, matrix.f]];
}))
"""

# whether every box the region draws lies within the host
WHOLE_GRAPH_SHOWN_JS = """
() => {
  const host = document.querySelector('.bl-view-host').getBoundingClientRect();
  return Array.from(document.querySelectorAll('.bl-view-host .react-flow__node')).every((node) => {
    const box = node.getBoundingClientRect();
    return box.left >= host.left - 1 && box.top >= host.top - 1
      && box.right <= host.right + 1 && box.bottom <= host.bottom + 1;
  });
}
"""

# the lines of the perch overlays the region draws, each as [the perch's
# name, the line's stroke as the browser computes it]
OVERLAY_LINES_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host line.bf-perch'),
  (line) => [line.dataset.perch, getComputedStyle(line).stroke])
"""

# a recorder of the region's `opened` events, in window.openedEvents
RECORD_OPENED_JS = """
() => {
  window.openedEvents = [];
  document.addEventListener('opened', (event) => window.openedEvents.push(event.detail), true);
}
"""

# the screen's boxes, each {left, top, right, bottom}, of the region's host,
# of the open layer whose id is given, of its name and of its toggle, the
# name's text, and whether the name is the element drawn at its center;
# null where the layer is not drawn open
LAYER_IN_REGION_JS = """
(id) => {
  const host = document.querySelector('.bl-view-host');
  const node = host && host.querySelector(`.react-flow__node[data-id="${CSS.escape(id)}"]`);
  const name = node && node.querySelector('.bf-layer-name');
  if (!name) return null;
  const box = (element) => {
    const found = element.getBoundingClientRect();
    return {left: found.left, top: found.top, right: found.right, bottom: found.bottom};
  };
  const at = name.getBoundingClientRect();
  const found = document.elementFromPoint(at.left + at.width / 2, at.top + at.height / 2);
  return {host: box(host), layer: box(node), name: box(name), text: name.textContent,
          toggle: box(node.querySelector(':scope > .bf-layer > .bf-toggle')),
          drawn: found !== null && name.contains(found)};
}
"""

# the least scale of spec 0.4 §2.3 at which a label can be read, the least
# at which a trellis graph opens on its terminal period (K-D6, as AAS's
# M-D15 amends K-D22)
READING_SCALE = 0.6
# the space the region keeps at each of its sides at the opening of a
# trellis graph on its terminal period, in pixels on the screen (K-D6)
OPENING_MARGIN = 10
# the drawing's top below the bar, the region's top, in the opening and the
# fitted view, and its left edge, the text edge, in the fitted view, in
# pixels on the screen (design pass 13 §2, rule 10; D3)
OPENING_TOP = 24
TEXT_EDGE = 12


def viewport(page) -> dict | None:
    """Spec 0.4 §§2.2–2.3, item 3: the region's viewport (VIEWPORT_JS): `x`, `y` and `zoom`, and the
    host's `width` and `height`; None before the region draws."""
    return page.evaluate(VIEWPORT_JS)


def period_opening(view: dict, place: dict, extent: float) -> dict:
    """The viewport `{x, y, zoom}` at which a region of the host's size that
    `view` gives (`viewport`) opens a trellis graph `extent` wide at scale 1
    on its terminal period's layer, or the layer of a period it shows alone,
    placed at `place`, `{ax, ay, width, height}` on the graph at scale 1
    (AAS, M-D15, which amends unit K's decisions K-D6 and K-D22 and unit L's
    Task 22; design pass 13 §2, rule 10, as the fix wave Q3a of unit Q,
    item 9, amends it; D20, D3): the largest scale, at most 1 and at least
    READING_SCALE, at which the box the opening shows (below) fills the
    region less OPENING_MARGIN at each side; the box's top OPENING_TOP under
    the region's top, the bar's foot; and its nearer end on the column's
    text edge: for a layer in the graph's left half the drawing's left end,
    a backward graph's terminal-condition label, which `settle` places at
    the root's padding of 2 px, TEXT_EDGE inside the region's left, and for
    a layer in its right half the drawing's right end, a forward graph's
    terminal-marker label, `extent` less that padding, TEXT_EDGE inside the
    region's right; where the box is wider than the region less TEXT_EDGE
    at each side, the box's left edge TEXT_EDGE inside the region's: the
    graph's nearer end, the marker's label, where the layer stands in the
    graph's left half, and the layer's left edge, which holds its name,
    where it stands in the right half. The box the opening shows is the
    layer with what stands between it and the graph's nearer end, the
    boundary markers and their labels, so that each of those labels stands
    whole (N-I277): from the graph's left end to the layer's right edge, or
    from the layer's left edge to the graph's right end, `extent`. The rise
    of the scale where the far edge would cut a frame within 24 px of its
    border (`clearOfCuts` in flow-canvas.js) is not modelled; at a scale of
    1 it does not act."""
    room, width, padding = OPENING_MARGIN, view["width"], 2.0
    nearer = place["ax"] + place["width"] / 2 <= extent / 2
    if nearer:
        place = {**place, "ax": 0.0, "width": place["ax"] + place["width"]}
    else:
        place = {**place, "width": extent - place["ax"]}
    zoom = max(READING_SCALE, min(1.0, (width - 2 * room) / place["width"]))
    if nearer:
        x = TEXT_EDGE - padding * zoom
    elif place["width"] * zoom > width - 2 * TEXT_EDGE:
        x = TEXT_EDGE - place["ax"] * zoom
    else:
        x = width - TEXT_EDGE - (extent - padding) * zoom
    return {"x": x, "y": OPENING_TOP - place["ay"] * zoom, "zoom": zoom}


def opens_on(view: dict | None, place: dict, extent: float) -> bool:
    """Whether the viewport `view` (`viewport`) is the opening of a trellis
    graph `extent` wide at scale 1 on the terminal period's layer placed at
    `place` (`period_opening`), to one screen pixel."""
    if view is None or view["width"] <= 0 or view["height"] <= 0:
        return False
    opening = period_opening(view, place, extent)
    size = max(place["width"], place["height"])
    return (
        abs(view["x"] - opening["x"]) <= 1
        and abs(view["y"] - opening["y"]) <= 1
        and abs(view["zoom"] - opening["zoom"]) * size <= 1
    )


def drawn_extent(nodes: dict) -> float:
    """The width at scale 1 of the graph whose drawn boxes are `nodes`, as
    DRAWN_PLACES_JS reads them, a boundary marker's with its label (N-I277):
    the right edge of the box that reaches farthest and the 2 px of padding
    the layout keeps there."""
    return max(node["x"] + node["width"] for node in nodes.values()) + 2


# Sets the least height of Details under the graph region, `.bl-panel`, to
# its height plus `pixels`, or, where `pixels` is null, removes that least
# height; then waits for the host's size to change and for two frames: the
# region's size observer answers a new size in the frame that lays it out.
PANEL_HEIGHT_JS = """
async (pixels) => {
  const panel = document.querySelector('.bl-panel');
  const region = document.querySelector('.bl-view-host .bf-region');
  const before = region.getBoundingClientRect().height;
  const least = panel.getBoundingClientRect().height + pixels;
  panel.style.minHeight = pixels === null ? '' : `${least}px`;
  const frame = () => new Promise((done) => requestAnimationFrame(done));
  for (let n = 0; n < 60 && region.getBoundingClientRect().height === before; n++) await frame();
  await frame();
  await frame();
}
"""

# The region's fit (flow-canvas.js, fitGraph): React Flow's
# getViewportForBounds for the bounds of the boxes at `places` in the
# region's width and height, at a scale from 0.05 to 1, with ten pixels at
# each side; with the bounds' `width` and `height`.
FITTED_VIEWPORT_JS = """
(places) => {
  const region = document.querySelector('.bl-view-host .bf-region');
  const boxes = Object.values(places);
  const left = Math.min(...boxes.map((box) => box.ax));
  const top = Math.min(...boxes.map((box) => box.ay));
  const width = Math.max(...boxes.map((box) => box.ax + box.width)) - left;
  const height = Math.max(...boxes.map((box) => box.ay + box.height)) - top;
  const room = {top: '10px', right: '10px', bottom: '10px', left: '10px'};
  const fitted = window.ReactFlow.getViewportForBounds({x: left, y: top, width, height},
    region.clientWidth, region.clientHeight, 0.05, 1, room);
  return {...fitted, width, height};
}
"""


def change_panel_height(page, pixels: float | None) -> dict | None:
    """Spec 0.4 §2.3, G-R76: Details made `pixels` taller, as a drag of its
    handle makes it, or returned to its own height where `pixels` is None
    (PANEL_HEIGHT_JS); answers the region's viewport (`viewport`) once the
    region's size observer has answered the host's new size."""
    page.evaluate(PANEL_HEIGHT_JS, pixels)
    return viewport(page)


def fitted_viewport(page, places: dict) -> dict:
    """Spec 0.4 §2.2, G-R76: the viewport at which the region's own fit
    shows the boxes at `places` (the `places` of `layout_records`) in the
    region as it now stands (FITTED_VIEWPORT_JS): `x`, `y` and `zoom`, with
    the `width` and `height` of the boxes' bounds on the graph."""
    return page.evaluate(FITTED_VIEWPORT_JS, places)


def expected_overlay_lines(
    graph: dict, opened: set[str], overlays: dict
) -> set[tuple[str, str, str]]:
    """Spec 0.4 §2.1, item 3: the lines for the perch overlays `overlays`
    (`model.edge_overlays`) over the graph `graph` with the layers `opened`
    open: (the perch's name, one box, the other) for each overlay edge whose
    two ends are nodes of the graph and stand for two different boxes
    (`standing_box`), each once."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    found = set()
    for overlay in overlays["overlays"]:
        for edge in overlay["edges"]:
            ends = (edge["sourceNodeId"], edge["targetNodeId"])
            if all(end in nodes for end in ends):
                one, other = (standing_box(nodes, end, opened)[0] for end in ends)
                if one != other:
                    found.add((overlay["name"], one, other))
    return found


# where the focus stands in the region: the id of the box whose element
# holds it, whether it is that box's toggle, and the element's spoken name;
# null where the focus stands outside the region
REGION_FOCUS_JS = """
() => {
  const active = document.activeElement;
  if (!active || !active.closest || !active.closest('.bl-view-host')) return null;
  const node = active.closest('.react-flow__node');
  return {
    box: node ? node.dataset.id : null,
    toggle: active.classList.contains('bf-toggle'),
    label: active.getAttribute('aria-label'),
  };
}
"""

# each port the region draws, as [the box's id, its title, its accessible
# description]
PORT_DESCRIPTIONS_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__handle'), (port) => [
  port.closest('.react-flow__node').dataset.id,
  port.getAttribute('title'),
  port.getAttribute('aria-description'),
])
"""


def region_focus(page) -> dict | None:
    """Where the focus stands in the region (REGION_FOCUS_JS): `box`,
    `toggle` and `label`; None outside the region."""
    return page.evaluate(REGION_FOCUS_JS)


def focus_region(page) -> dict:
    """Spec 0.4 §2.4: focus the region, which focuses its selected box or
    the first box of its order, and answer where the focus stands."""
    page.focus(".bl-view-host .bf-region")
    found, _ = wait_until(
        lambda: (focus := region_focus(page)) and focus["box"] is not None and focus,
        5.0,
        "the focus on a box in the region",
    )
    return found


def press_in_region(page, key: str, seconds: float = 5.0) -> dict | None:
    """Spec 0.4 §2.4: wait for changed focus, or the same toggle after its
    completed layout. None means an unprevented Tab left the region."""
    before = region_focus(page)
    activation = before and before["toggle"] and key in ("Enter", "Space")
    handle = "document.querySelector('.bl-view-host').bellmanFlow"
    layouts = page.evaluate(f"() => {handle}.layouts()") if activation else None
    if activation:
        action, _, name = before["label"].partition(" ")
        expected = {**before, "label": ("close " if action == "open" else "open ") + name}
    page.evaluate(KEY_PREVENTED_RECORDER_JS)
    page.keyboard.press(key)
    exits = key in ("Tab", "Shift+Tab") and page.evaluate("() => window.keyPrevented") is False

    def moved():
        now = region_focus(page)
        if activation:
            completed = now == expected and page.evaluate(f"() => {handle}.layouts()") > layouts
            return (now,) if completed else None
        if now is None:
            return (None,) if exits else None
        return (now,) if now != before else None

    found, _ = wait_until(moved, seconds, f"the focus moved by {key}")
    return found[0]


def open_every_layer(page, limit: int = 3000) -> None:
    """Opens every closed layer of the graph shown through the keyboard
    (spec 0.4 §2.4): the focus put on the region, then Tab pressed through
    the region's order and Enter on each toggle that reads `open <name>`,
    until the focus leaves the region; raises where `limit` keys do not
    reach the order's end."""
    now = focus_region(page)
    for _ in range(limit):
        if now is None:
            return
        opens = now["toggle"] and (now["label"] or "").startswith("open ")
        now = press_in_region(page, "Enter" if opens else "Tab")
    raise AssertionError(f"the region's order did not end within {limit} keys")


def drawn_boxes(records: dict) -> set[str]:
    """The boxes the region draws of the layout's records `records`
    (`layout_records`): those ELK lays out and the builders' boxes of the
    compact occurrences, which it does not (AAS, L-D7)."""
    return set(records["boxes"]) | set(records["builderPlaces"])


def boxes_in_region(records: dict, view: dict) -> set[str]:
    """The boxes of the layout's records `records` (`layout_records`) that
    lie wholly or partly within the region (spec 0.4 §4) at the viewport `view`
    (`viewport`): those whose rectangle on the screen overlaps the region's
    by a positive area, the builders' boxes of the compact occurrences among
    them (AAS, L-D7)."""
    inside = set()
    for box, place in {**records["places"], **records["builderPlaces"]}.items():
        left = place["ax"] * view["zoom"] + view["x"]
        top = place["ay"] * view["zoom"] + view["y"]
        right = left + place["width"] * view["zoom"]
        bottom = top + place["height"] * view["zoom"]
        if min(right, view["width"]) > max(left, 0) and min(bottom, view["height"]) > max(top, 0):
            inside.add(box)
    return inside


def periods_held(page) -> set[str]:
    """The period addresses in the held backward trellis collection."""
    held = page.evaluate(HELD_COLLECTION_JS)
    return {address.split("/")[0] for address in occurrences_of(held, "backward")}


# --- unit R, Design brief 7 ---

# the README of the fonts' recipe, which records its build (unit R, R-D1)
FONTS_README = WORKBENCH / "js/fonts/README.md"
# the files js/fonts/build.sh writes, by their paths from WORKBENCH
FONT_FILES = {
    "archivo": "bellman_workbench/public/fonts/archivo-latin-standard-normal.woff2",
    "archivo license": "bellman_workbench/public/fonts/Archivo-OFL.txt",
    "plex": "bellman_workbench/public/fonts/ibm-plex-mono-latin-400-normal.woff2",
    "plex 500": "bellman_workbench/public/fonts/ibm-plex-mono-latin-500-normal.woff2",
    "plex 600": "bellman_workbench/public/fonts/ibm-plex-mono-latin-600-normal.woff2",
    "plex italic": "bellman_workbench/public/fonts/ibm-plex-mono-latin-400-italic.woff2",
    "plex license": "bellman_workbench/public/fonts/IBM-Plex-Mono-OFL.txt",
}

# The elements and pseudo-elements under the window and under Vuetify's
# menus that move (spec 0.4 §5.8; brief rule 10; review 8): each with a
# computed transition duration above 0 or an animation name other than
# `none`, as `<tag>.<class><pseudo-element>`; CodeMirror's caret layer,
# `.cm-cursorLayer`, which holds the caret's blink, is the one exception.
MOTION_JS = """
() => {
  const moves = (style) =>
    style.transitionDuration.split(',').some((part) => parseFloat(part) > 0) ||
    style.animationName.split(',').some((part) => part.trim() !== 'none');
  const found = [];
  for (const element of document.querySelectorAll('.bl-window *, .v-overlay-container *')) {
    if (element.matches('.cm-cursorLayer')) continue;
    for (const pseudo of [null, '::before', '::after']) {
      if (moves(getComputedStyle(element, pseudo))) {
        const name = `${element.tagName.toLowerCase()}.${element.getAttribute('class')}`;
        found.push(name + (pseudo || ''));
      }
    }
  }
  return found;
}
"""

# A record, at every frame until ANIMATIONS_STOP_JS, of the Web Animations
# that run on an element under the window or in Vuetify's menus, each once
# as `<kind> <tag>.<class>`; CodeMirror's caret layer is the one exception.
ANIMATIONS_START_JS = """
() => {
  const record = {seen: new Set(), running: true};
  window.blAnimationsRecord = record;
  const sample = () => {
    if (!record.running) return;
    for (const animation of document.getAnimations()) {
      const target = animation.effect && animation.effect.target;
      if (!target || target.matches('.cm-cursorLayer')) continue;
      if (!target.closest('.bl-window, .v-overlay-container')) continue;
      const name = `${target.tagName.toLowerCase()}.${target.getAttribute('class')}`;
      record.seen.add(`${animation.constructor.name} ${name}`);
    }
    requestAnimationFrame(sample);
  };
  sample();
}
"""

# ends the record ANIMATIONS_START_JS began and answers what it holds
ANIMATIONS_STOP_JS = """
() => {
  const record = window.blAnimationsRecord;
  record.running = false;
  return Array.from(record.seen);
}
"""


def animations_during(page, act, settle_ms: int = 1000) -> list[str]:
    """The Web Animations that run under the window or in Vuetify's menus
    while `act()` is done and for `settle_ms` after it, sampled at every
    frame (ANIMATIONS_START_JS). Vuetify opens and closes a select's menu by
    `element.animate`, which no style rule reaches and MOTION_JS does not
    read; its longest such animation lasts 450 ms."""
    page.evaluate(ANIMATIONS_START_JS)
    act()
    page.wait_for_timeout(settle_ms)
    return page.evaluate(ANIMATIONS_STOP_JS)


# The contrast of every text under the window (spec 0.4 §5.8), for the list
# of exception selectors given. A text is an element's own text nodes, an
# input's or a text area's value, a select's chosen option, or the string
# of a pseudo-element's `content`, wherever the browser draws it. The ground
# composites the background color of the root, then of each element down to
# the text's, over --bl-chrome. The text's color, the fill of an SVG text,
# is composited over the ground at its alpha times the opacity of its
# element and of every ancestor. The ratio is WCAG 2's. A color is read as
# `rgb()`, `rgba()` or `color(srgb ...)`, the form a `color-mix` computes
# to. Each row also holds its bound, 3 for a text within a button and 4.5
# otherwise, and the first exception whose selector matches the element or
# an ancestor, or null.
CONTRAST_JS = r"""
(exceptions) => {
  const parse = (text) => {
    let match = /^rgba?\((.*)\)$/.exec(text);
    if (match) {
      const parts = match[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
      return [parts[0], parts[1], parts[2], parts.length > 3 ? parts[3] : 1];
    }
    match = /^color\(srgb (.*)\)$/.exec(text);
    if (match) {
      const parts = match[1].split(/[\s\/]+/).filter(Boolean).map(Number);
      return [parts[0] * 255, parts[1] * 255, parts[2] * 255, parts.length > 3 ? parts[3] : 1];
    }
    throw new Error(`the contrast script reads no color "${text}"`);
  };
  const over = (ink, ground) =>
    [0, 1, 2].map((i) => ink[i] * ink[3] + ground[i] * (1 - ink[3])).concat([1]);
  const luminance = (color) => color.slice(0, 3).reduce((sum, value, i) => {
    const channel = value / 255;
    const linear = channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    return sum + linear * [0.2126, 0.7152, 0.0722][i];
  }, 0);
  const ratio = (a, b) => {
    const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (high + 0.05) / (low + 0.05);
  };
  const printed = (color) => `rgb(${color.slice(0, 3).map(Math.round).join(', ')})`;
  const probe = document.createElement('span');
  probe.style.color = 'var(--bl-chrome)';
  document.body.append(probe);
  const chrome = parse(getComputedStyle(probe).color);
  probe.remove();
  const grounds = new Map();
  const groundOf = (element) => {
    if (!element) return chrome;
    if (!grounds.has(element)) {
      const own = parse(getComputedStyle(element).backgroundColor);
      grounds.set(element, over(own, groundOf(element.parentElement)));
    }
    return grounds.get(element);
  };
  const opacities = new Map();
  const opacityOf = (element) => {
    if (!element) return 1;
    if (!opacities.has(element)) {
      const own = Number(getComputedStyle(element).opacity);
      opacities.set(element, own * opacityOf(element.parentElement));
    }
    return opacities.get(element);
  };
  const named = (element) => {
    const classes = Array.from(element.classList).filter((name) => !name.includes('--'));
    return element.tagName.toLowerCase() + classes.map((name) => `.${name}`).join('');
  };
  const owned = (element) => Array.from(element.classList).some((name) => name.startsWith('bl-'));
  const selectorOf = (element) => {
    let holder = element;
    while (holder && !owned(holder)) holder = holder.parentElement;
    return holder && holder !== element ? `${named(holder)} ${named(element)}` : named(element);
  };
  const drawnText = (node) => {
    const range = document.createRange();
    range.selectNodeContents(node);
    return Array.from(range.getClientRects()).some((box) => box.width > 0 && box.height > 0);
  };
  const button = 'button, [role="button"], input[type="button"], input[type="submit"], input[type="reset"]';
  const rows = [];
  const measure = (element, text, style, pseudo) => {
    const svg = element instanceof SVGElement && pseudo === null && /^(rgb|color)/.test(style.fill);
    const ink = parse(svg ? style.fill : style.color);
    ink[3] *= opacityOf(element) * (pseudo ? Number(style.opacity) : 1);
    if (ink[3] === 0) return;
    const ground = pseudo ? over(parse(style.backgroundColor), groundOf(element)) : groundOf(element);
    const color = over(ink, ground);
    rows.push({
      selector: selectorOf(element) + (pseudo || ''),
      text: text.trim().slice(0, 60),
      color: printed(color),
      ground: printed(ground),
      ratio: ratio(color, ground),
      bound: element.closest(button) ? 3 : 4.5,
      excepted: exceptions.find((selector) => element.closest(selector)) || null,
    });
  };
  for (const element of document.querySelectorAll('.bl-window *')) {
    const style = getComputedStyle(element);
    if (style.visibility !== 'visible') continue;
    const boxed = element.getClientRects().length > 0;
    const own = Array.from(element.childNodes)
      .filter((node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
    if (own.some(drawnText)) {
      measure(element, own.map((node) => node.textContent).join(''), style, null);
    }
    const valued = element.matches('textarea, input:not([type="hidden"], [type="checkbox"], [type="radio"])');
    if (boxed && valued && element.value.trim()) measure(element, element.value, style, null);
    if (boxed && element.matches('select') && element.selectedOptions.length) {
      measure(element, element.selectedOptions[0].text, style, null);
    }
    for (const pseudo of ['::before', '::after']) {
      const generated = getComputedStyle(element, pseudo);
      const content = /^"(.*)"$/s.exec(generated.content);
      if (boxed && content && content[1].trim() && generated.display !== 'none') {
        measure(element, content[1], generated, pseudo);
      }
    }
  }
  return rows;
}
"""

# The exceptions to the contrast targets that spec 0.4 §5.8 names, each a
# selector matched against a text's element and its ancestors, with its
# reason: the passive line numbers, which are every number but the current
# line's (ice-2, measured as text), the dimmed contents of a previous
# construction, and the words of an inactive control, which §5.8's target
# for active text does not bound, the disabled view tab `Stage` standing
# at the 40 percent of every disabled control since design pass 13 §5
# (E16). The quiet error mark, in ink-3 since design pass 8 §6 (unit M,
# Task 4), meets its bound and is no exception.
CONTRAST_EXCEPTIONS = {
    ".cm-lineNumbers .cm-gutterElement:not(.cm-activeLineGutter)": (
        "§5.8: the passive line numbers"
    ),
    ".bl-stale": "§5.8: the dimmed contents of the last construction",
    '[aria-disabled="true"]': "§5.8: the words of an inactive control",
}


# The promise of the end of every opening fade of a panel that runs, the
# animation `bl-panel-in` of brand.css (AAS, L-D15), a fade cancelled
# counting as ended, so that a measure reads the panel at its full ink.
PANELS_SETTLED_JS = """
() => Promise.all(document.getAnimations()
  .filter((animation) => animation.animationName === 'bl-panel-in')
  .map((animation) => animation.finished.catch(() => null))).then(() => true)
"""


def contrast_rows(page) -> list[dict]:
    """Every text under the window with its composited color, its ground
    and their contrast ratio (CONTRAST_JS), each row `{selector, text,
    color, ground, ratio}`, read once every panel's opening fade has ended
    (PANELS_SETTLED_JS)."""
    page.evaluate(PANELS_SETTLED_JS)
    keys = ("selector", "text", "color", "ground", "ratio")
    return [{key: row[key] for key in keys} for row in page.evaluate(CONTRAST_JS, [])]


def contrast_faults(page, exceptions) -> list[str]:
    """The texts under the window whose contrast ratio is under its bound,
    4.5 for text and 3 within a button (spec 0.4 §5.8), and whose element
    no selector of `exceptions` matches, each as one line naming the
    element, the text, the ratio, the bound and the two colors, read once
    every panel's opening fade has ended (PANELS_SETTLED_JS)."""
    page.evaluate(PANELS_SETTLED_JS)
    return [
        f"{row['selector']} {row['text']!r}: {row['ratio']:.2f} under {row['bound']}"
        f" ({row['color']} on {row['ground']})"
        for row in page.evaluate(CONTRAST_JS, list(exceptions))
        if row["ratio"] < row["bound"] and row["excepted"] is None
    ]


# the background color of the first element `selector` names, as the
# browser computes it
GROUND_JS = "(selector) => getComputedStyle(document.querySelector(selector)).backgroundColor"

# The elements under the window drawn on a ground of the color given, each
# as `<tag>.<class>`: an element whose computed background color is that
# color, whose own opacity is 1 and whose box has a positive area. Vuetify's
# state layers and progress tracks, whose background is the text's color at
# a lower opacity or with no height, are not grounds.
GROUNDS_OF_JS = """
(color) => Array.from(document.querySelectorAll('.bl-window *')).filter((element) => {
  const style = getComputedStyle(element);
  const box = element.getBoundingClientRect();
  return style.backgroundColor === color && style.opacity === '1' && box.width * box.height > 0;
}).map((element) => `${element.tagName.toLowerCase()}.${element.getAttribute('class')}`)
"""

# The widths in pixels of the four columns, the folder, the text, the graph
# and Matsya, that spec 0.4 §5.1 and R-D30 give, by the window's width and
# whether the reader has folded the folder: at 1600 the frames' widths; at
# 1800 the rest shared by the text and the graph in the proportion of their
# frame widths; below 1600 Matsya at its least width first, then the graph
# at its own, then the folder folded by the width function, the text taking
# what is left over (Task 12 of unit R's plan). The window has no left
# padding since the rail of icons left it (design pass 10 §2), and no right
# margin since design pass 13 §4 (Q-D6), so that at 1600 the text and the
# graph share 120 px over the frame's widths, in whole pixels (unit N, Task
# 1), and each step of the narrowing stands 120 px lower than in unit R, at
# 1460, 1446, 1416, 1380, 1220 and 1140 px; 1200 px is the narrow frame of
# R-D59. At 1416 the folder folded by the function and opened by the reader
# leaves the text 538 px.
FRAME_TRACKS = {
    (1600, False): (170, 645, 357, 320),
    (1600, True): (48, 719, 377, 348),
    (1800, False): (170, 774, 428, 320),
    (1460, False): (170, 568, 314, 300),
    (1446, False): (170, 568, 300, 300),
    (1416, False): (48, 660, 300, 300),
    (1380, False): (48, 624, 300, 300),
    (1220, False): (48, 464, 300, 300),
    (1200, False): (48, 444, 300, 300),
    (1140, False): (48, 384, 300, 300),
}
# The three columns at 1600 with Matsya folded by the reader, its column
# and the column gap before it taking no width, the rest shared by the text
# and the graph, as with the setting `off` (unit K's decision K-D19).
MATSYA_FOLDED_TRACKS = (170, 875, 483)
# The three columns while the trellis view is shown, keyed as FRAME_TRACKS:
# Matsya folded, the graph taking the width of Matsya's column and of the
# column gap before it, the folder and the text keeping their widths (unit
# K's decisions K-D6 and K-D19).
TRELLIS_TRACKS = {
    (1600, False): (170, 645, 713),
    (1220, False): (48, 464, 636),
    (1200, False): (48, 444, 636),
    (1140, False): (48, 384, 636),
}
# Matsya's two fold buttons: the one at the right end of its head, drawn
# while it is open, and the toggle `Matsya` at the right of the main bar,
# drawn always (design pass 10 §3), in place of Υ at the right end of the
# graph's bar (K-D19).
MATSYA_FOLD = '.bl-matsya-head .bl-fold[data-fold="matsya"]'
MATSYA_TOGGLE = '.bl-main-bar .bl-fold[data-fold="matsya"]'
# The three columns of a page with the setting `off` (spec 0.4 §6), keyed
# as FRAME_TRACKS: the text and the graph share Matsya's width; at 1080 the
# width function folds the folder, the step that stood at 1140 before the
# window's right margin left (design pass 13 §4; Q-D6).
OFF_TRACKS = {
    (1600, False): (170, 875, 483),
    (1600, True): (48, 970, 510),
    (1080, False): (48, 660, 300),
}

# The buttons, links and chips of Matsya's column whose text or accessible
# name is one of the words given: the proposal's actions and the context
# chip of unit Q, which the column omits (spec 0.4 §5.6).
COLUMN_ACTIONS_JS = """
(words) => Array.from(document.querySelectorAll(
  '.bl-matsya button, .bl-matsya a, .bl-matsya [role="button"], .bl-matsya .v-chip'
)).filter((element) => words.includes(element.textContent.trim()) ||
  words.includes((element.getAttribute('aria-label') || '').trim()))
  .map((element) => element.outerHTML.slice(0, 120))
"""

# the computed widths of the columns of .bl-window, in pixels
TRACKS_JS = """
() => getComputedStyle(document.querySelector('.bl-window'))
  .gridTemplateColumns.split(' ').map(parseFloat)
"""

# Whether the first element `selector` names is drawn whole within the
# viewport and is the element found at its center, so that nothing covers
# or clips it there.
VISIBLE_IN_VIEWPORT_JS = """
(selector) => {
  const element = document.querySelector(selector);
  if (!element) return false;
  const box = element.getBoundingClientRect();
  if (box.width <= 0 || box.height <= 0 || box.left < 0 || box.top < 0 ||
      box.right > innerWidth || box.bottom > innerHeight) return false;
  const found = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
  return found !== null && element.contains(found);
}
"""

# the names of the handles the page holds, each a `data-handle`
HANDLE_NAMES_JS = """
() => Array.from(document.querySelectorAll('.bl-handle')).map((handle) => handle.dataset.handle)
"""

# writes the value `value` under the key `key` of the browser's storage
STORE_JS = "([key, value]) => localStorage.setItem(key, value)"


def tracks(page) -> list[float]:
    """The computed widths of the columns of `.bl-window`, in pixels
    (TRACKS_JS)."""
    return page.evaluate(TRACKS_JS)


def tracks_near(page, expected, tolerance: float = 1.0) -> bool:
    """Whether the columns of `.bl-window` are as many as `expected` and
    each within `tolerance` pixels of its expected width."""
    found = tracks(page)
    return len(found) == len(expected) and all(
        abs(width - wanted) <= tolerance for width, wanted in zip(found, expected)
    )


def layout_record(page, folder) -> dict | None:
    """The record of the regions' sizes and folds that window.vue keeps in
    the browser's storage for the model folder `folder`, under the key
    `bellman-workbench layout <folder>` (R-D16); None where none is kept."""
    key = f"bellman-workbench layout {Path(folder).resolve()}"
    return page.evaluate("(key) => JSON.parse(localStorage.getItem(key))", key)


def drag_handle(page, name: str, dx: float, dy: float = 0) -> None:
    """Drags the handle `name` with the mouse from its center by `dx`
    pixels along the x axis and `dy` pixels along the y axis, in four
    steps, and releases it."""
    box = page.locator(f'.bl-handle[data-handle="{name}"]').bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx, y + dy, steps=4)
    page.mouse.up()


def visible_in_viewport(page, selector: str) -> bool:
    """Whether the first element `selector` names is drawn whole within the
    viewport, uncovered at its center (VISIBLE_IN_VIEWPORT_JS)."""
    return page.evaluate(VISIBLE_IN_VIEWPORT_JS, selector)


# The type sizes of spec 0.4 §5.2 and the five styles of design pass 8
# §5.1 that set them (brief rule 4; review 14; unit M, Tasks 4, 6 and 7):
# the editor's text in its own size; the graph bar's name and Matsya's head
# in Head, as the Files head and the panels' names; the tab row's toggles,
# the document tabs, the tree's rows, Matsya's prose, the view tabs and the
# words of a button of VSCode Elements, `Save`, in Label; the main bar's
# path in Code small (design pass 10 §3); and the status line's words and
# Details' keys in Small: each the face drawn first and the size in pixels.
SIZES = {
    "source": ("IBM Plex Mono", 12.5),
    "tab": ("Archivo", 13.0),
    "tree": ("Archivo", 13.0),
    "head": ("Archivo", 13.0),
    "column head": ("Archivo", 13.0),
    "label": ("Archivo", 13.0),
    "code small": ("IBM Plex Mono", 11.0),
    "small": ("Archivo", 11.0),
    "prose": ("Archivo", 13.0),
    "button": ("Archivo", 13.0),
    "control": ("Archivo", 13.0),
}

# The heights in pixels of the rows of Design brief 7 §§2 and 7 in the
# system of design pass 8 (§7 measure 2; unit M, Tasks 4, 6 and 7) as
# design pass 10 §2 joins the heads to the bars: the main bar, 36 px; the
# graph bar, 36 px; the Files bar, 36 px since design pass 13 §4 (D1),
# level with the tab row and the graph bar; the text column's bar of tabs
# with the tabs, 36 px; a row of the folder's tree; the status line, 24 px
# since design pass 8 §6 (spec 0.4 §5.1; the brief's row 8); and the space
# above it, between the regions and the status line, none since design
# pass 8 §6, the regions standing on the status line's hairline.
ROW_HEIGHTS = {
    "main bar": 36,
    "graph bar": 36,
    "column head": 36,
    "bar": 36,
    "tree": 24,
    "status": 24,
    "above status": 0,
}

# The rows of ROW_HEIGHTS that take further rows of their height where
# their column is too narrow for their items (amendment 02 ruling 5): the
# graph bar, which holds the graph's name and Problems with its controls
# since unit N's Task 1 (design pass 10 §2).
ROW_WRAPS = {"graph bar"}

# for each element `selector` names, the face its computed font-family
# names first, unquoted, and its computed font size in pixels
TYPE_OF_JS = """
(selector) => Array.from(document.querySelectorAll(selector)).map((element) => {
  const style = getComputedStyle(element);
  const face = style.fontFamily.split(',')[0].trim().replace(/^"(.*)"$/, '$1');
  return [face, parseFloat(style.fontSize)];
})
"""

# the box of each element `selector` names, as the browser draws it
BOXES_JS = """
(selector) => Array.from(document.querySelectorAll(selector)).map((element) => {
  const box = element.getBoundingClientRect();
  return {left: box.left, top: box.top, right: box.right, bottom: box.bottom,
          width: box.width, height: box.height};
})
"""

# the tabs over the text, in their order: each tab's path, whether it is
# the active tab and whether it reads `unsaved`
FILE_TABS_JS = """
() => Array.from(document.querySelectorAll('.bl-tabs .bl-tab')).map((tab) => ({
  path: tab.dataset.path,
  active: tab.classList.contains('bl-active'),
  unsaved: tab.querySelector('.bl-modified') !== null,
}))
"""

# the path that the open file's name on the active tab carries, or null
# where no file is open
OPEN_PATH_JS = """
() => {
  const name = document.querySelector('.bl-file-name');
  return name === null ? null : name.dataset.path;
}
"""

# the face, as the browser computes it, of a span set in the stack the
# custom property given names; the span is removed at once
FACE_OF_JS = """
(property) => {
  const probe = document.createElement('span');
  probe.style.fontFamily = `var(${property})`;
  document.body.append(probe);
  const face = getComputedStyle(probe).fontFamily;
  probe.remove();
  return face;
}
"""


def type_of(page, selector: str) -> list[tuple[str, float]]:
    """The face drawn first and the size in pixels of each element
    `selector` names, as the browser computes them (TYPE_OF_JS)."""
    return [tuple(found) for found in page.evaluate(TYPE_OF_JS, selector)]


def boxes(page, selector: str) -> list[dict]:
    """The box of each element `selector` names (BOXES_JS): its left, top,
    right and bottom edges, its width and its height, in pixels."""
    return page.evaluate(BOXES_JS, selector)


def file_tabs(page) -> list[dict]:
    """The tabs over the text in their order (FILE_TABS_JS), each `{path,
    active, unsaved}`."""
    return page.evaluate(FILE_TABS_JS)


def open_path_shown(page) -> str | None:
    """The path of the open file, which the name `.bl-file-name` on the
    active tab carries as `data-path` (R-D32); None where no file is
    open."""
    return page.evaluate(OPEN_PATH_JS)


# The token colors of spec 0.4 §5.2 and Design brief 7 §8, each for a token
# of cons.bl by its text: the custom property of brand.css that colors it,
# its weight and its style as the browser computes them. In order: a
# keyword, `argmax` (a keyword of Design brief 7 §8), a perch tag, a role
# tag, any other tag, a set, a number, a function, a block id, punctuation,
# an annotation and an operator. The parameter's treatment, --bl-number at
# 500, has no entry: no stage file under applications/ declares a
# parameter with `@in`, the one form the tokenizer marks.
TOKEN_COLORS = {
    "@stage": ("--bl-periwinkle", "400", "normal"),
    "argmax": ("--bl-periwinkle", "400", "normal"),
    "!arvl": ("--bl-periwinkle", "600", "normal"),
    "!ctrl": ("--bl-mint", "600", "normal"),
    "!doc": ("--bl-periwinkle", "400", "normal"),
    "ℝ₊₊": ("--bl-mint", "400", "normal"),
    "1": ("--bl-number", "400", "normal"),
    "𝑢": ("--bl-ice", "400", "italic"),
    "arvl_to_dcsn": ("--bl-ice", "600", "normal"),
    "[": ("--bl-ice-3", "400", "normal"),
    "[id=util]": ("--bl-ice-3", "400", "normal"),
    ":=": ("--bl-ice-2", "400", "normal"),
}

# the computed color, weight and style of the first token of the editor
# whose text is the text given, a token being a span of a line whose text
# is that text alone; null where no span holds it
TOKEN_STYLE_JS = """
(text) => {
  for (const span of document.querySelectorAll('.cm-content .cm-line span')) {
    if (span.textContent !== text) continue;
    const style = getComputedStyle(span);
    return {color: style.color, weight: style.fontWeight, style: style.fontStyle};
  }
  return null;
}
"""


def token_style(page, text: str) -> dict | None:
    """The computed color, weight and style, `{color, weight, style}`, of
    the first token of the editor whose text is `text` (TOKEN_STYLE_JS);
    None where no token holds it."""
    return page.evaluate(TOKEN_STYLE_JS, text)


# The style of the stage name as drawn (spec 0.4 §5.2): for each element
# that holds a text node under `.bl-stage-name`, its face drawn first, its
# size and line height in pixels, its color and its font stretch, each
# style once; the stage name's text; and the value of the custom property
# --bl-stage-name-stretch.
STAGE_NAME_JS = """
() => {
  const name = document.querySelector('.cm-content .bl-stage-name');
  if (!name) return null;
  const styles = new Map();
  const walker = document.createTreeWalker(name, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const style = getComputedStyle(node.parentElement);
    const drawn = {
      face: style.fontFamily.split(',')[0].trim().replace(/^"(.*)"$/, '$1'),
      size: parseFloat(style.fontSize),
      lineHeight: parseFloat(style.lineHeight),
      color: style.color,
      stretch: style.fontStretch,
    };
    styles.set(JSON.stringify(drawn), drawn);
  }
  const stretch = getComputedStyle(document.documentElement)
    .getPropertyValue('--bl-stage-name-stretch').trim();
  return {text: name.textContent, styles: Array.from(styles.values()), stretch};
}
"""


def stage_name(page) -> dict | None:
    """The stage name as the editor draws it (STAGE_NAME_JS): `{text,
    styles, stretch}`, each style `{face, size, lineHeight, color,
    stretch}`; None where no stage name is drawn."""
    return page.evaluate(STAGE_NAME_JS)


# The line of the stage name as drawn (unit L, Task 3; L-D3): the text of
# the line number beside it, the gutter's element whose top is the line's;
# the line's height; the heights of the lines drawn after it; the name's
# weight; the face and size of each text of the line outside the name,
# each once; and the baselines of the name and of the line number. A
# text's baseline is the top of its box plus the ascent of its font, which
# a canvas measures in the same font (`fontBoundingBoxAscent`). Null where
# no stage name is drawn.
STAGE_LINE_JS = """
() => {
  const line = document.querySelector('.cm-content .cm-line.bl-stage-line');
  if (!line) return null;
  const name = line.querySelector('.bl-stage-name');
  const top = line.getBoundingClientRect().top;
  const canvas = document.createElement('canvas').getContext('2d');
  const face = (style) => style.fontFamily.split(',')[0].trim().replace(/^"(.*)"$/, '$1');
  const texts = (element) => {
    const found = [];
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (node.data.trim()) found.push(node);
    }
    return found;
  };
  const baseline = (node) => {
    const range = document.createRange();
    range.selectNodeContents(node);
    const style = getComputedStyle(node.parentElement);
    canvas.font = `${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
    return range.getBoundingClientRect().top + canvas.measureText(node.data).fontBoundingBoxAscent;
  };
  const number = Array.from(document.querySelectorAll('.cm-lineNumbers .cm-gutterElement'))
    .find((element) => getComputedStyle(element).visibility !== 'hidden'
      && Math.abs(element.getBoundingClientRect().top - top) < 0.5);
  const source = new Map();
  for (const node of texts(line)) {
    if (name.contains(node)) continue;
    const style = getComputedStyle(node.parentElement);
    const drawn = {face: face(style), size: parseFloat(style.fontSize)};
    source.set(JSON.stringify(drawn), drawn);
  }
  const lines = Array.from(document.querySelectorAll('.cm-content .cm-line'));
  return {
    number: number ? number.textContent : null,
    height: line.getBoundingClientRect().height,
    following: lines.slice(lines.indexOf(line) + 1).map((l) => l.getBoundingClientRect().height),
    weight: getComputedStyle(name).fontWeight,
    source: Array.from(source.values()),
    nameBaseline: baseline(texts(name)[0]),
    numberBaseline: number ? baseline(texts(number)[0]) : null,
  };
}
"""


def stage_line(page) -> dict | None:
    """The line of the stage name as the editor draws it once the page's
    fonts have loaded (STAGE_LINE_JS): `{number, height, following, weight,
    source, nameBaseline, numberBaseline}`, in pixels; None where no stage
    name is drawn."""
    page.evaluate("() => document.fonts.ready.then(() => null)")
    return page.evaluate(STAGE_LINE_JS)


# The tables of the Fields tab as drawn (unit L, Task 4; L-D4), one per
# group in the page's order: the group's perch and key; the table's width;
# the widths of its three columns as their headers measure them; the
# padding before a cell after the first, `gap`; the padding and border of
# a set's box, `chrome`, and the width of six characters in a set's face,
# `six`, both read from the page's first set box; and its rows. A row
# gives the field's name, the height of its element and of one of its
# lines, whether the name is wider than its element, its text-overflow and
# its hover; the set, the width of its box and of its text, whether the
# text is wider than the box's inside, its text-overflow and its hover;
# and the width of the role's box and of its text (unit L, Task 29). A
# text's width is that of a span set in the face, size, weight and spacing
# of the element that shows it.
FIELD_TABLES_JS = """
() => {
  const measure = (element, text) => {
    const style = getComputedStyle(element);
    const probe = document.createElement('span');
    for (const name of ['fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'letterSpacing']) {
      probe.style[name] = style[name];
    }
    probe.style.position = 'absolute';
    probe.style.whiteSpace = 'pre';
    probe.textContent = text;
    document.body.append(probe);
    const width = probe.getBoundingClientRect().width;
    probe.remove();
    return width;
  };
  const sum = (style, ...names) =>
    names.reduce((total, name) => total + parseFloat(style[name]), 0);
  const sample = document.querySelector('.bl-class-tables .bl-class-set');
  const chrome = sum(getComputedStyle(sample),
    'paddingLeft', 'paddingRight', 'borderLeftWidth', 'borderRightWidth');
  const six = measure(sample, '000000');
  return Array.from(document.querySelectorAll('.bl-class-group')).map((group) => {
    const table = group.querySelector('.bl-class-table');
    return {
      perch: group.closest('.bl-class-perch').dataset.perch,
      group: group.dataset.group,
      width: table.getBoundingClientRect().width,
      columns: Array.from(table.querySelectorAll('th'),
        (head) => head.getBoundingClientRect().width),
      gap: parseFloat(getComputedStyle(table.querySelector('th + th')).paddingLeft),
      chrome,
      six,
      rows: Array.from(table.querySelectorAll('tbody tr'), (row) => {
        const field = row.querySelector('.bl-class-field');
        const set = row.querySelector('.bl-class-set');
        const fieldStyle = getComputedStyle(field);
        const setStyle = getComputedStyle(set);
        const inside = set.clientWidth - sum(setStyle, 'paddingLeft', 'paddingRight');
        const setText = measure(set, set.value);
        return {
          field: field.textContent,
          height: field.getBoundingClientRect().height,
          lineHeight: parseFloat(fieldStyle.lineHeight),
          fieldCut: measure(field, field.textContent) > field.clientWidth + 0.5,
          fieldOverflow: fieldStyle.textOverflow,
          fieldHover: field.getAttribute('title'),
          set: set.value,
          setBox: set.getBoundingClientRect().width,
          setText,
          setCut: setText > inside + 0.5,
          setOverflow: setStyle.textOverflow,
          setHover: set.getAttribute('title'),
          role: row.querySelector('.bl-class-role').getBoundingClientRect().width,
          roleText: measure(row.querySelector('.bl-class-role'),
            row.querySelector('.bl-class-role').value),
        };
      }),
    };
  });
}
"""


def field_tables(page) -> list[dict]:
    """The tables of the Fields tab as drawn once the page's fonts have
    loaded (FIELD_TABLES_JS), one per group: `{perch, group, width,
    columns, gap, chrome, six, rows}`, in pixels, each row `{field, height,
    lineHeight, fieldCut, fieldOverflow, fieldHover, set, setBox, setText,
    setCut, setOverflow, setHover, role, roleText}`."""
    page.evaluate("() => document.fonts.ready.then(() => null)")
    return page.evaluate(FIELD_TABLES_JS)


# The numbers, counted from one, of the editor's lines that carry the class
# `bl-annotated`, the lines drawn as a statement and its annotation.
ANNOTATED_LINES_JS = """
() => Array.from(document.querySelectorAll('.cm-content .cm-line'))
  .map((line, index) => (line.classList.contains('bl-annotated') ? index + 1 : 0))
  .filter((number) => number > 0)
"""

# The parts of the editor's line `n`, counted from one, that carries an
# annotation: the text and the box of the statement's mark and of the
# annotation's mark, each a child of the line; and the line's content box,
# its box without its paddings. Each box is `{left, top, right, bottom}` in
# pixels. Null where the line has no annotation's mark as its child.
ANNOTATED_LINE_JS = """
(n) => {
  const line = document.querySelectorAll('.cm-content .cm-line')[n - 1];
  const statement = line.querySelector(':scope > .bl-statement');
  const annotation = line.querySelector(':scope > .bl-annotation');
  if (!annotation) return null;
  const edges = (box) => ({left: box.left, top: box.top, right: box.right, bottom: box.bottom});
  const drawn = (element) => ({
    text: element.textContent,
    box: edges(element.getBoundingClientRect()),
  });
  const style = getComputedStyle(line);
  const box = line.getBoundingClientRect();
  return {
    statement: statement ? drawn(statement) : null,
    annotation: drawn(annotation),
    content: {
      left: box.left + parseFloat(style.paddingLeft),
      top: box.top,
      right: box.right - parseFloat(style.paddingRight),
      bottom: box.bottom,
    },
  };
}
"""


def annotated_line(page, line: int) -> dict | None:
    """The statement, the annotation and the content box of the editor's
    line `line` (ANNOTATED_LINE_JS); None where the line is not drawn as a
    statement and its annotation."""
    return page.evaluate(ANNOTATED_LINE_JS, line)


# The box of the first character of the first occurrence of a text on the
# editor's line `n`, counted from one, as drawn, `{left, top, width,
# height}` in pixels, once the character stands whole in the editor's
# scrolled view; null where the line does not draw the text or the
# character is not brought into the view. The line is scrolled into the
# view, and the box is read two frames later. By then the editor has
# applied any scroll of its own, such as the scroll to the cursor after an
# undo, and has measured the scrolled text. The editor places a click made
# before that measurement by its earlier measurement, on another line. The
# text begins with a character of the Basic Multilingual Plane, one code
# unit.
CHARACTER_BOX_JS = """
async ([n, text]) => {
  const lineOf = () => document.querySelectorAll('.cm-content .cm-line')[n - 1];
  const characterOf = (line) => {
    const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let drawn = '';
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      nodes.push([node, drawn.length]);
      drawn += node.data;
    }
    const index = drawn.indexOf(text);
    if (index < 0) return null;
    const [node, start] = nodes.filter(([, at]) => at <= index).pop();
    const range = document.createRange();
    range.setStart(node, index - start);
    range.setEnd(node, index - start + 1);
    return range;
  };
  if (characterOf(lineOf()) === null) return null;
  const frame = () => new Promise((done) => requestAnimationFrame(done));
  for (let attempt = 0; attempt < 5; attempt++) {
    lineOf().scrollIntoView({block: 'nearest'});
    await frame();
    await frame();
    const line = lineOf();
    const view = line.closest('.cm-scroller').getBoundingClientRect();
    const box = characterOf(line).getBoundingClientRect();
    if (box.height > 0 && box.top >= view.top && box.bottom <= view.bottom) {
      return {left: box.left, top: box.top, width: box.width, height: box.height};
    }
  }
  return null;
}
"""


def click_before(page, line: int, text: str) -> None:
    """Clicks the editor 1 px inside the left edge of the first character
    of `text` on its line `line`, at the character's mid-height, which puts
    the cursor before that character (CHARACTER_BOX_JS)."""
    box = page.evaluate(CHARACTER_BOX_JS, [line, text])
    assert box is not None, f"line {line} draws no {text!r} in the editor's view"
    page.mouse.click(box["left"] + 1, box["top"] + box["height"] / 2)


# The head of a bracket group that carries an identity, matched at a `[`:
# the pattern of GROUP_HEAD in js/codemirror/src/hidden_types.js. A line of
# a file is a header of the text minimap where it matches from the line's
# first character that is no white space (spec 0.4 §5.4; review 4).
GROUP_HEAD = re.compile(r"\[\s*(id|label)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")

# The colors of the text minimap (spec 0.4 §5.4), each a custom property of
# brand.css and the percent of it drawn over transparency: the mark of a
# header, of the stage name's line and of any other line, and the strip's
# ground.
MINIMAP_COLORS = {
    "header": ("--bl-ice", 60),
    "stage": ("--bl-ultramarine-light", 80),
    "line": ("--bl-ice", 22),
    "ground": ("--bl-ice", 4),
}

# The marks of the editor's text minimap in their order, each with its line
# counted from one, its kind, its box's top in the viewport, its width and
# its height in pixels, and its ground as the browser computes it.
MINIMAP_JS = """
() => Array.from(document.querySelectorAll('.bl-editor .bl-minimap > .bl-minimap-mark'))
  .map((mark) => {
    const box = mark.getBoundingClientRect();
    return {
      line: Number(mark.dataset.line),
      kind: mark.dataset.kind,
      top: box.top,
      width: box.width,
      height: box.height,
      color: getComputedStyle(mark).backgroundColor,
    };
  })
"""

# The color, as the browser computes it, of the custom property given at
# the percent given over transparency, written as the editor's theme writes
# a wash; the probe is removed at once.
WASH_COLOR_JS = """
([name, percent]) => {
  const probe = document.createElement('span');
  probe.style.color = `color-mix(in srgb, var(${name}) ${percent}%, transparent)`;
  document.body.append(probe);
  const color = getComputedStyle(probe).color;
  probe.remove();
  return color;
}
"""


def minimap_marks(page) -> list[dict]:
    """The marks of the editor's text minimap in their order (MINIMAP_JS),
    each `{line, kind, top, width, height, color}`."""
    return page.evaluate(MINIMAP_JS)


def wash_color(page, name: str, percent: float) -> str:
    """The color of the custom property `name` at `percent` percent over
    transparency, as the browser computes it (WASH_COLOR_JS)."""
    return page.evaluate(WASH_COLOR_JS, [name, percent])


# the computed color and the computed opacity of the first element the
# selector given names
COLOR_OF_JS = "(selector) => getComputedStyle(document.querySelector(selector)).color"
OPACITY_OF_JS = (
    "(selector) => parseFloat(getComputedStyle(document.querySelector(selector)).opacity)"
)

# The marks a refusal draws in the brand's orange (spec 0.4 §5.7), each by
# a class its elements carry: the error mark with its count, the refused
# span's underline and the refused line's gutter mark.
REFUSAL_MARKS = {
    "bl-error-": "error mark",
    "cm-lintRange-error": "underline",
    "cm-lint-marker-error": "gutter mark",
}


def orange_marks(page) -> set[str]:
    """The marks drawn in the brand's orange (ORANGE_ELEMENTS_JS): each
    element's entry named by the first class of REFUSAL_MARKS its classes
    hold, and an element that holds none by its own entry."""
    return {
        next((name for key, name in REFUSAL_MARKS.items() if key in entry), entry)
        for entry in page.evaluate(ORANGE_ELEMENTS_JS)
    }


def status_place(page) -> str:
    """The cursor's place the status line prints, `8:33`; the empty string
    where it prints none."""
    place = page.locator(".bl-status-place")
    return place.text_content() if place.count() else ""


def code_cell_outputs(path) -> list[str]:
    """What each code cell of the notebook `path` prints, its code cells
    run in order in one namespace in this process, in the working directory
    as it stands; no kernel is started (spec 0.4 §5.9; Task 11 of unit R's
    plan)."""
    notebook = json.loads(Path(path).read_text(encoding="utf-8"))
    namespace, printed = {"__name__": "__main__"}, []
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        text = "".join(source) if isinstance(source, list) else source
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exec(compile(text, f"{path} cell {cell.get('id')}", "exec"), namespace)
        printed.append(stream.getvalue())
    return printed


# Each folder row of the tree, by its path: whether it is closed.
FOLDER_ROWS_JS = """
() => Object.fromEntries(Array.from(
  document.querySelectorAll('.bl-folder-row'),
  (row) => [row.dataset.path, row.classList.contains('bl-closed')]))
"""


def folder_rows(page) -> dict[str, bool]:
    """Each folder row the tree draws, by its path, with whether it is
    closed (FOLDER_ROWS_JS)."""
    return page.evaluate(FOLDER_ROWS_JS)


def reveal_in_tree(page, relpath: str, timeout: int = 30_000) -> None:
    """Opens each closed folder on the path of the file `relpath`, the
    outermost first, by a click on its row, and waits for the file's row:
    the tree opens with every folder closed but those on the open file's
    path (R-D52). The page's open file, named on its active tab, is waited
    for first, so that no click is made on a folder that the page is about
    to open for that file."""
    page.wait_for_selector(".bl-file-name[data-path]", timeout=timeout)
    parts = relpath.split("/")
    for end in range(1, len(parts)):
        row = f'.bl-folder-row[data-path="{"/".join(parts[:end])}"]'
        page.wait_for_selector(row, timeout=timeout)
        if page.locator(f"{row}.bl-closed").count():
            page.click(row)
            page.wait_for_selector(f"{row}:not(.bl-closed)", timeout=timeout)
    page.wait_for_selector(f'.bl-tree-file[data-path="{relpath}"]', timeout=timeout)


def open_every_folder(page, timeout: int = 30_000) -> None:
    """Opens every closed folder of the tree by a click on its row, the
    outermost first, so that every file of the folder has its row (R-D52)."""
    closed = page.locator(".bl-folder-row.bl-closed")
    while closed.count():
        path = closed.first.get_attribute("data-path")
        closed.first.click()
        page.wait_for_selector(
            f'.bl-folder-row[data-path="{path}"]:not(.bl-closed)', timeout=timeout
        )


# Each box the region draws, by its id: its width in pixels at the scale
# of one, the role its label is set in (`label` for an operator, `boundary`
# for Inputs and Outputs, `layer` for a block or a closed layer), the width
# of its label as drawn, the whole text the box prints, and the title and
# the accessible description of each of its output ports, in their order
# (R-D49). The label's width is that of a span holding the label's text in
# the label's computed font, outside the graph's scale; it is not the
# bundle's `measure`, which the layout itself uses, and not the width of
# the label's element, which its `left` and `right` make as wide as the
# box less its borders and paddings.
BOX_MEASURES_JS = """
() => Object.fromEntries(Array.from(
  document.querySelectorAll('.bl-view-host .react-flow__node'), (node) => {
  const box = node.querySelector(':scope > .bf-box');
  const name = box ? box.querySelector('.bf-name') : null;
  if (!name) return null;
  const role = Array.from(name.classList).find((word) => word.startsWith('bf-t-')).slice(5);
  const probe = document.createElement('span');
  probe.style.cssText = 'position: absolute; white-space: pre';
  probe.style.font = getComputedStyle(name).font;
  probe.textContent = name.textContent;
  document.body.append(probe);
  const measure = probe.getBoundingClientRect().width;
  probe.remove();
  return [node.dataset.id, {
    width: node.offsetWidth,
    role,
    measure,
    text: box.textContent,
    outputs: Array.from(box.querySelectorAll('.react-flow__handle[data-handleid*="::out::"]'),
      (port) => [port.getAttribute('title'), port.getAttribute('aria-description')]),
  }];
}).filter(Boolean))
"""

# The BellmanType panel's height in pixels with the tab it shows: whether
# the tab's content stands within the panel, whether it scrolls where it is
# taller than its area, and whether it is taller (R-D51).
CLASSIFICATION_PANEL_JS = """
() => {
  const panel = document.querySelector('.bl-classification');
  const content = panel.querySelector('.bl-class-tables, .bl-values');
  const outer = panel.getBoundingClientRect();
  const inner = content.getBoundingClientRect();
  return {
    height: outer.height,
    inside: inner.top >= outer.top - 0.5 && inner.bottom <= outer.bottom + 0.5,
    scrolls: getComputedStyle(content).overflowY === 'auto',
    taller: content.scrollHeight > content.clientHeight,
  };
}
"""


# the selects of the graph's header by their accessible names (R-D56)
VIEW_SELECTS = {"graph": ".bl-view-kind", "direction": ".bl-view-direction"}

# the tabs' close controls in the tabs' order: the path of each tab, the
# control's accessible name, its hover and whether it is disabled (R-D53),
# each an icon button of VSCode Elements that marks its disabled state by
# aria-disabled (design pass 8 §§3 and 4; unit M, Task 6)
TAB_CLOSES_JS = """
() => Array.from(document.querySelectorAll('.bl-tabs .bl-tab-item'), (item) => {
  const close = item.querySelector('.bl-tab-close');
  return {
    path: item.querySelector('.bl-tab').dataset.path,
    label: close.label,
    title: close.title,
    disabled: close.getAttribute('aria-disabled') === 'true',
  };
})
"""


def view_shown(page) -> dict:
    """The word each select of the graph's bar shows, as the page reads it,
    in lowercase, by the select's name, `{"graph": "operator", "direction":
    "backward"}`; a select the bar does not hold is left out (R-D56). Each
    select is VSCode Elements' (design pass 8 §§4 and 6; unit M, Task 7),
    its word written with a capital."""
    return {
        name: page.locator(f"{selector} vscode-single-select").evaluate("(s) => s.value").lower()
        for name, selector in VIEW_SELECTS.items()
        if page.locator(selector).count()
    }


def view_options(page, name: str) -> list[str]:
    """The options of the bar's select named `name`, in their order, as a
    reader reads them, in lowercase: a click on VSCode Elements' select
    opens its list, which the select marks by its attribute `open` (design
    pass 8 §4; unit M, Task 7), the options are read from that list, and a
    second click closes it, the attribute then gone (the delegated
    acceptance of unit M, D4)."""
    select = page.locator(f"{VIEW_SELECTS[name]} vscode-single-select")
    select.click()
    wait_until(lambda: select.get_attribute("open") is not None, 5.0, f"the list of {name} open")
    options = select.get_by_role("option")
    options.first.wait_for(timeout=5_000)
    words = [text.strip().lower() for text in options.all_text_contents()]
    select.click()
    wait_until(lambda: select.get_attribute("open") is None, 5.0, f"the list of {name} closed")
    return words


def choose_view(page, kind: str | None, direction: str | None) -> None:
    """Chooses the graph shown by the two selects of the graph's header as a
    reader does (R-D56): `kind`, `operator` or `initial`, in the select
    `graph`, which stands in a stage's view alone, and `direction`,
    `backward` or `forward`, in the select `direction`; None leaves a
    select as it stands, and a select that shows its word already is left.
    A choice opens VSCode Elements' select by a click and clicks the
    option, which reads the word with a capital (`choose_option`; unit M,
    Task 7). The helper then waits until the header names the graph of the
    two words (`.bl-graph-bar`'s data-graph), the graph the page then
    draws."""
    for name, word in (("graph", kind), ("direction", direction)):
        if word is not None and view_shown(page).get(name) != word:
            choose_option(page, VIEW_SELECTS[name], word.capitalize())
    shown = view_shown(page)
    chosen = shown["direction"]
    if shown.get("graph") == "initial":
        chosen = f"{chosen} initial diagram"
    wait_until(
        lambda: page.get_attribute(".bl-graph-bar", "data-graph") == chosen,
        10.0,
        f"the graph {chosen} named by the header",
    )


def tab_closes(page) -> list[dict]:
    """The tabs' close controls in the tabs' order (TAB_CLOSES_JS), each
    `{path, label, title, disabled}`."""
    return page.evaluate(TAB_CLOSES_JS)


# The text the page selects, as the browser holds it: the editor keeps the
# page's selection on the text it selects while it holds the focus.
SELECTED_TEXT_JS = "() => document.getSelection().toString()"


def add_field(page, group: str, field: str, domain: str, role: str) -> None:
    """Adds `field` with the set `domain` and the role `role` in the box
    `add field` of the Fields group `group`, `cntn/`, as a reader does: the
    three entries filled and the button `+` clicked (unit T, rule 4)."""
    box = page.locator(f'.bl-class-group[data-group="{group}"] .bl-add-field')
    box.locator('[data-entry="field"]').fill(field)
    box.locator('[data-entry="set"]').fill(domain)
    box.locator('[data-entry="role"]').select_option(role)
    box.locator(".bl-add-button").click()


# The handles of the editor and of the graph on their host elements (R-D29;
# ruling R-P13): `bellmanEditor` of `.bl-editor`, the handle the bundle's
# `window.bellmanEditor.create` answers, and `bellmanFlow` of
# `.bl-view-host`, the handle `window.BellmanFlow.mount` answers.
EDITOR_HANDLE = "document.querySelector('.bl-editor').bellmanEditor"
FLOW_HANDLE = "document.querySelector('.bl-view-host').bellmanFlow"


def editor_handle(page, function: str, *arguments):
    """Calls the function `function` of the editor's handle (EDITOR_HANDLE)
    with `arguments` and answers what it answers (R-D29)."""
    return page.evaluate(f"(given) => {EDITOR_HANDLE}.{function}(...given)", list(arguments))


def flow_handle(page, function: str, *arguments):
    """Calls the function `function` of the graph's handle (FLOW_HANDLE)
    with `arguments` and answers what it answers (R-D29)."""
    return page.evaluate(f"(given) => {FLOW_HANDLE}.{function}(...given)", list(arguments))


# the key in the browser's storage of the page's layout direction, which
# holds `horizontal` while the layout is turned to the right and nothing
# while it is laid out downward, the default (design pass 14 §2; S-D5)
LAYOUT_KEY = "bellman-workbench layout"


def layout_button(page) -> str:
    """The layout the foot's layout button turns to, its `data-layout`:
    `horizontal` while the page is laid out downward and `vertical` while
    it is laid out to the right (design pass 14 §2)."""
    return page.get_attribute(".bl-layout-button", "data-layout")


def lay_out_left_to_right(page) -> None:
    """Turns the page's layout to the right by the foot's button `Lay out
    from left to right`, where the page is laid out downward, the default
    (design pass 14 §2; S-D5), and waits until the button offers `Lay out
    from top to bottom` and the graph drawn again stands still; a page laid
    out to the right already is left as it stands. The direction is the
    page's, one for every graph and tab, which the browser keeps under
    LAYOUT_KEY, so a test of a rule that holds in the horizontal layout
    calls this once after the page opens. The layout recorder is installed
    where none is (`record_layouts`), since the wait reads it."""
    if layout_button(page) == "vertical":
        return
    if not page.evaluate("() => !!window.laidOut"):
        record_layouts(page)
    page.click(".bl-layout-button")
    wait_until(lambda: layout_button(page) == "vertical", 10.0, "the layout button reads vertical")
    wait_until(lambda: view_still(page), 60.0, "the graph laid out to the right")


def lay_out_top_to_bottom(page) -> None:
    """Turns the page's layout back downward by the foot's button `Lay out
    from top to bottom`, where the page is laid out to the right, and waits
    until the button offers `Lay out from left to right` and the graph
    drawn again stands still; a page laid out downward already is left as
    it stands (design pass 14 §2; S-D5)."""
    if layout_button(page) == "horizontal":
        return
    if not page.evaluate("() => !!window.laidOut"):
        record_layouts(page)
    page.click(".bl-layout-button")
    wait_until(lambda: layout_button(page) == "horizontal", 10.0, "the layout button reads horizontal")
    wait_until(lambda: view_still(page), 60.0, "the graph laid out downward")


# the lines of the editor that carry the preview's class `bl-preview-line`,
# each counted from one
PREVIEW_LINES_JS = """
() => Array.from(document.querySelectorAll('.cm-content .cm-line'), (line, n) =>
  line.classList.contains('bl-preview-line') ? n + 1 : null).filter((n) => n !== null)
"""

# the editor's text scrolled to `top` pixels from its first line, as a
# reader scrolls it; answers once the browser has drawn two frames after
# the scroll
SCROLL_EDITOR_JS = """
async (top) => {
  document.querySelector('.bl-editor .cm-scroller').scrollTop = top;
  await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
}
"""

# the height in pixels of the visible area of the editor's scroller
EDITOR_HEIGHT_JS = "() => document.querySelector('.bl-editor .cm-scroller').clientHeight"

# whether the line `n` of the editor, counted from one, ends below the
# visible area of the editor's scroller
LINE_BELOW_EDITOR_JS = """
(n) => {
  const scroller = document.querySelector('.bl-editor .cm-scroller');
  const line = document.querySelectorAll('.cm-content .cm-line')[n - 1];
  return line.getBoundingClientRect().bottom > scroller.getBoundingClientRect().bottom;
}
"""

# whether the element holds the page's focus
FOCUSED_JS = "(element) => element === document.activeElement"

# the ids of the boxes the graph's region draws as selected
SELECTED_BOXES_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__node.selected'),
  (node) => node.dataset.id)
"""


def lines_holding(text: str, document: str, limit: int = 50) -> list[dict]:
    """Unit R, brief rule 9: the lines of `document` that hold `text`, the
    case ignored, in order and at most `limit` of them, each `{line,
    column, text}`, the line counted from one, the column of the first
    match counted from one in code points, as the package counts a column,
    and the line's text."""
    found = []
    for number, line in enumerate(document.split("\n"), 1):
        match = re.search(re.escape(text), line, re.IGNORECASE)
        if match:
            found.append({"line": number, "column": match.start() + 1, "text": line})
    return found[:limit]


# The results of Goto Anything in their order (spec 0.4 §5.8; unit R, brief
# rule 9): each result's text, its kind, its address and whether it is the
# current result, the one previewed.
GOTO_RESULTS_JS = """
() => Array.from(document.querySelectorAll('.bl-goto .bl-goto-result'), (result) => ({
  text: result.querySelector('.bl-goto-text').textContent,
  kind: result.querySelector('.bl-goto-kind').textContent,
  address: result.querySelector('.bl-goto-address').textContent,
  current: result.classList.contains('bl-active'),
}))
"""

# whether the palette's input holds the page's focus
GOTO_FOCUSED_JS = (
    "() => document.activeElement !== null && document.activeElement.matches('.bl-goto-input')"
)

# the element that holds the page's focus, kept on the browser's window as
# `keptFocus`; and whether the page's focus is on that element
KEEP_FOCUS_JS = "() => { window.keptFocus = document.activeElement; }"
KEPT_FOCUS_JS = "() => document.activeElement === window.keptFocus"

# a passive line number of the editor, neither the current line's nor a
# selected line's, whose color the high-contrast setting changes (spec 0.4
# §5.8)
PASSIVE_LINE_NUMBER = (
    ".cm-lineNumbers .cm-gutterElement:not(.cm-activeLineGutter, .bl-selected-line,"
    " .bl-preview-line)"
)


def goto_results(page) -> list[dict]:
    """The results of Goto Anything as the palette prints them
    (GOTO_RESULTS_JS), each `{text, kind, address, current}`."""
    return page.evaluate(GOTO_RESULTS_JS)


def open_goto(page) -> None:
    """Opens Goto Anything as a reader does, by P with the primary modifier,
    Command on macOS and Ctrl elsewhere (spec 0.4 §5.8), and waits until
    the palette's input holds the focus."""
    page.keyboard.press("ControlOrMeta+p")
    wait_until(lambda: page.evaluate(GOTO_FOCUSED_JS), 5.0, "the palette's input focused")


def goto_command(page, word: str) -> None:
    """Runs the command `word` of Goto Anything as a reader does: the
    palette opened, `>` and the word typed, the command the current result,
    and Enter."""
    open_goto(page)
    page.keyboard.type(f">{word}")
    wait_until(
        lambda: goto_results(page)[:1]
        == [{"text": word, "kind": "command", "address": "", "current": True}],
        5.0,
        f"the command {word} first",
    )
    page.keyboard.press("Enter")


# The five states in which item 1 measures the window and item 4 measures
# its contrast (Task 15 of unit R's plan): cons.bl constructed; its
# backward initial diagram; the trellis PORT_CONS of cons-port, six
# periods; a refusal of cons.bl with a previous construction, made by an
# edit; and a refusal before any construction, cons.bl holding the refused
# text on disk before the page opens.
STATES = (
    "constructed",
    "initial diagram",
    "trellis",
    "refused after a construction",
    "refused before a construction",
)
# The edit that makes the parser refuse cons.bl at line 18, as the text it
# replaces and the text it writes, `a = m_d - - c`.
REFUSING_EDIT = ("a = m_d - c", "a = m_d - - c")


def write_refused_cons(folder: Path) -> str:
    """Writes into the file CONS of the model folder `folder` its text with
    REFUSING_EDIT made once, which the parser refuses at line 18, and
    answers that text."""
    path = Path(folder) / CONS
    text = path.read_text(encoding="utf-8").replace(*REFUSING_EDIT, 1)
    path.write_text(text, encoding="utf-8")
    return text


def show_state(page, state: str, url: str, timeout: int = 60_000) -> None:
    """Brings the page into the state `state` of STATES over the server at
    `url` as a reader does, and waits until the page has drawn it. The
    server is over a copy of portfolio-choice for the first, the second
    and the fourth state; over the copy of cons-port that
    `applications_copy` writes for the third, whose trellis file PORT_CONS
    is opened from the tree; and over a copy of portfolio-choice whose
    cons.bl `write_refused_cons` wrote for the fifth, in which cons.bl is
    opened from the tree and the loop's state reads `not parsed`."""
    seconds = timeout / 1000
    if state == "trellis":
        open_trellis(page, url, PORT_CONS, timeout=timeout)
        return
    if state == "refused before a construction":
        page.goto(url)
        reveal_in_tree(page, CONS, timeout)
        page.click(f'.bl-tree-file[data-path="{CONS}"]')
        wait_until(
            lambda: " · not parsed · " in (status_settled_on(page, CONS) or ""),
            seconds,
            "cons.bl refused before a construction",
        )
        page.wait_for_selector(".cm-content .cm-lintRange-error", timeout=timeout)
        return
    open_cons(page, url)
    page.wait_for_selector(".bl-class-row", timeout=timeout)
    if state == "initial diagram":
        record_layouts(page)
        choose_view(page, "initial", "backward")
        wait_until(
            lambda: page.evaluate(VIEW_STATE_JS)["current"], seconds, "the initial diagram drawn"
        )
    elif state == "refused after a construction":
        replace_in_editor(page, *REFUSING_EDIT)
        page.wait_for_selector(".cm-content .cm-lintRange-error", timeout=timeout)
        page.wait_for_selector(".bl-view-host.bl-stale", timeout=timeout)
    elif state != "constructed":
        raise ValueError(f"no state {state!r} among {STATES}")


# The surfaces of spec 0.4 §5.2, each region by the color its table gives
# it: the lit surface, the chrome and the raised surface, on which Goto
# Anything stands as an overlay of the system since design pass 13 §5
# (E17); Matsya's column and a user's message stand on the chrome, the
# page's ground, since design pass 16 (S0-9; amendment 06 §6.1, §5.2 line
# 191; SG4-12). The headers are the Files bar, the tabs' row and the
# graph bar; the BellmanType panel's scrollbar, which the raised surface also
# holds, has no ground a script reads, and unit Q's context chips are not
# drawn.
SURFACES = {
    "editor": "#172A52",
    "graph": "#172A52",
    "active tab": "#172A52",
    "composer": "#172A52",
    "main bar": "#0F1B36",
    "headers": "#0F1B36",
    "folder": "#0F1B36",
    "BellmanType panel": "#0F1B36",
    "Details": "#0F1B36",
    "status": "#0F1B36",
    "Goto Anything": "#172A52",
    "Matsya": "#0F1B36",
    "user messages": "#0F1B36",
}

# The elements MEASURES_JS reads, each a selector by the key of the table
# that states its measure: the rows of ROW_HEIGHTS but `above status`,
# which the script computes; the regions of SURFACES; and the roles of
# SIZES, the panels' names (AAS, L-D12) among the column heads (design pass
# 8 §5.5; unit M, Task 6).
MEASURED = {
    "rows": {
        "main bar": ".bl-main-bar",
        "graph bar": ".bl-graph-bar",
        "column head": ".bl-folder-rail",
        "bar": ".bl-tab-row, .bl-tab",
        "tree": ".bl-folder-row, .bl-tree-file",
        "status": ".bl-status-summary",
    },
    "grounds": {
        "editor": ".bl-editor-frame",
        "graph": ".bl-view-host",
        "active tab": ".bl-tab.bl-active",
        "composer": ".bl-matsya-field vscode-textarea",
        "main bar": ".bl-main-bar",
        "headers": ".bl-folder-rail, .bl-tab-row, .bl-graph-bar",
        "folder": ".bl-folder",
        "BellmanType panel": ".bl-classification",
        "Details": ".bl-panel",
        "status": ".bl-status",
        "Goto Anything": ".bl-goto",
        "Matsya": ".bl-matsya, .bl-matsya-head, .bl-matsya-body",
        "user messages": ".bl-matsya-question",
    },
    "type": {
        "source": ".cm-content",
        "tab": ".bl-tab",
        "tree": ".bl-tree-file",
        "head": ".bl-graph-bar .bl-graph-name, .bl-matsya-head > h2",
        "column head": ".bl-folder-rail > h2, .bl-region-head > .bl-region-name",
        "label": ".bl-tab-actions .bl-text-button, .bl-crumbs",
        "code small": ".bl-status-summary .bl-code-small",
        "small": ".bl-status-summary",
        "prose": (
            ".bl-matsya-field vscode-textarea, .bl-matsya-question, .bl-matsya-answer,"
            " .bl-class-perch-name"
        ),
        "button": ".bl-stage-button, .bl-trellis-button",
        "control": ".bl-save",
    },
}

# The measures of the window as the browser computes them (spec 0.4 §§5.1
# and 5.2; Design brief 7 §2), for the selectors of MEASURED, each read of
# the drawn elements alone: `tracks`, the widths of the window's columns;
# `rows`, the height of each element of a row, and under `above status`
# the space from the lowest foot of the folder, the text and the graph to
# the status line's top; `grounds`, the ground of each element of a region,
# its own background composited over each ancestor's from the root down;
# and `type`, the face drawn first and the size of each element of a role.
MEASURES_JS = r"""
(measured) => {
  const parse = (text) => {
    let match = /^rgba?\((.*)\)$/.exec(text);
    if (match) {
      const parts = match[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
      return [parts[0], parts[1], parts[2], parts.length > 3 ? parts[3] : 1];
    }
    match = /^color\(srgb (.*)\)$/.exec(text);
    const parts = match[1].split(/[\s\/]+/).filter(Boolean).map(Number);
    return [parts[0] * 255, parts[1] * 255, parts[2] * 255, parts.length > 3 ? parts[3] : 1];
  };
  const over = (ink, ground) =>
    [0, 1, 2].map((i) => ink[i] * ink[3] + ground[i] * (1 - ink[3])).concat([1]);
  const groundOf = (element) => {
    const chain = [];
    for (let holder = element; holder; holder = holder.parentElement) chain.unshift(holder);
    const ground = chain.reduce(
      (below, holder) => over(parse(getComputedStyle(holder).backgroundColor), below),
      [255, 255, 255, 1]);
    return `rgb(${ground.slice(0, 3).map(Math.round).join(', ')})`;
  };
  const drawn = (selector) => Array.from(document.querySelectorAll(selector)).filter(
    (element) => element.getClientRects().length > 0 &&
      getComputedStyle(element).visibility === 'visible');
  const each = (table, read) => Object.fromEntries(Object.entries(table)
    .map(([name, selector]) => [name, drawn(selector).map(read)])
    .filter(([, found]) => found.length > 0));
  const height = (element) => Math.round(element.getBoundingClientRect().height * 100) / 100;
  const rows = each(measured.rows, height);
  const status = drawn('.bl-status-summary')[0];
  if (status) {
    const feet = drawn('.bl-folder, .bl-file, .bl-view')
      .map((element) => element.getBoundingClientRect().bottom);
    const above = status.getBoundingClientRect().top - Math.max(...feet);
    rows['above status'] = [Math.round(above * 100) / 100];
  }
  return {
    tracks: getComputedStyle(document.querySelector('.bl-window'))
      .gridTemplateColumns.split(' ').map(parseFloat),
    rows,
    grounds: each(measured.grounds, groundOf),
    type: each(measured.type, (element) => {
      const style = getComputedStyle(element);
      const face = style.fontFamily.split(',')[0].trim().replace(/^"(.*)"$/, '$1');
      return [face, parseFloat(style.fontSize)];
    }),
  };
}
"""


def measures(page) -> dict:
    """The measures of the window (MEASURES_JS over MEASURED): `{tracks,
    rows, grounds, type}`, a region or a row that draws nothing left
    out."""
    return page.evaluate(MEASURES_JS, MEASURED)


def rgb_of(hex_color: str) -> str:
    """The color `#RRGGBB` written as the browser computes a color, `rgb(r,
    g, b)`."""
    red, green, blue = (int(hex_color[at : at + 2], 16) for at in (1, 3, 5))
    return f"rgb({red}, {green}, {blue})"


def measure_faults(found: dict, tracks) -> list[str]:
    """The measures of `found` (`measures`) that differ from the tables,
    each one line: the columns from `tracks`, a row from ROW_HEIGHTS, each
    by more than 1 px; a region's ground from its color in SURFACES; a
    role's face from SIZES, or its size by more than 0.01 px. A row or a
    role that draws nothing is a fault; a region that draws nothing is not,
    since a region such as the palette is drawn in some states alone."""
    faults = []
    if len(found["tracks"]) != len(tracks) or any(
        abs(width - wanted) > 1 for width, wanted in zip(found["tracks"], tracks)
    ):
        faults.append(f"columns {found['tracks']} against {list(tracks)}")
    for row, wanted in ROW_HEIGHTS.items():
        heights = found["rows"].get(row, [])
        if not heights:
            faults.append(f"row {row}: nothing drawn")
        # a row of ROW_WRAPS takes further rows of its height where its
        # column is too narrow for its items (amendment 02 ruling 5): its
        # height a whole number of rows
        faults += [
            f"row {row}: {h} against {wanted}"
            for h in heights
            if (abs(h - wanted * max(1, round(h / wanted))) > 1 if row in ROW_WRAPS
                else abs(h - wanted) > 1)
        ]
    for region, grounds in found["grounds"].items():
        wanted = rgb_of(SURFACES[region])
        faults += [f"ground of {region}: {g} against {wanted}" for g in grounds if g != wanted]
    for role, (face, size) in SIZES.items():
        drawn = found["type"].get(role, [])
        if not drawn:
            faults.append(f"type of {role}: nothing drawn")
        faults += [
            f"type of {role}: {found_face} {found_size} against {face} {size}"
            for found_face, found_size in drawn
            if found_face != face or abs(found_size - size) > 0.01
        ]
    return faults


# The buttons and the links under the window that the browser draws with
# no accessible name, each as the start of its markup. A name is, in order,
# the text of the elements aria-labelledby names, aria-label, the text the
# element holds outside any element hidden from assistive technology, the
# alt of an image it holds, and its title.
NAMELESS_JS = r"""
() => {
  const textOf = (element) => {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    let text = '';
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (!node.parentElement.closest('[aria-hidden="true"]')) text += node.textContent;
    }
    return text.trim();
  };
  const nameOf = (element) => {
    const by = (element.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
    const labelled = by.map((id) => document.getElementById(id))
      .filter(Boolean).map(textOf).join(' ').trim();
    const images = Array.from(element.querySelectorAll('img[alt]'))
      .map((image) => image.alt.trim()).join(' ').trim();
    return labelled || (element.getAttribute('aria-label') || '').trim() || textOf(element) ||
      images || (element.getAttribute('title') || '').trim();
  };
  return Array.from(document.querySelectorAll(
    '.bl-window button, .bl-window a, .bl-window [role="button"], .bl-window [role="link"]'))
    .filter((element) => element.getClientRects().length > 0 && !nameOf(element))
    .map((element) => element.outerHTML.slice(0, 120));
}
"""

# The regions of the window, of which an element's region is the nearest
# that holds it.
REGIONS = (
    ".bl-main-bar, .bl-goto, .bl-folder, .bl-file, .bl-classification, .bl-view,"
    " .bl-panel, .bl-status, .bl-matsya"
)

# Marks each drawn element the selector given names, in the order of the
# document, with its place among them in the attribute data-bl-drawn, and
# answers the places, so that a locator finds each element by its mark.
MARK_DRAWN_JS = """
(selector) => {
  document.querySelectorAll('[data-bl-drawn]')
    .forEach((element) => element.removeAttribute('data-bl-drawn'));
  const drawn = Array.from(document.querySelectorAll(selector))
    .filter((element) => element.getClientRects().length > 0);
  drawn.forEach((element, place) => element.setAttribute('data-bl-drawn', String(place)));
  return drawn.map((element, place) => place);
}
"""


def drawn_element(page, place: int):
    """The locator of the drawn element that MARK_DRAWN_JS marked with
    `place`."""
    return page.locator(f'[data-bl-drawn="{place}"]')


def give_focus(page, place: int) -> None:
    """Gives the keyboard's focus to the drawn element marked `place`
    (MARK_DRAWN_JS), or, where it is a control of VSCode Elements, to the
    button its own tree holds, which holds its focus and draws its outline
    (design pass 8 §4); the button is reached by Playwright's selectors, so
    that no page test reaches a shadow root itself (unit G, item 4; M-I55)."""
    element = drawn_element(page, place)
    if element.evaluate("(found) => found.tagName.toLowerCase()").startswith("vscode-"):
        element = element.locator("button").first
    element.focus()

# Whether the element that holds the focus is the last drawn element the
# selector given names, and whether it stands in the region of that
# element (REGIONS).
FOCUS_PLACE_JS = """
([selector, regions]) => {
  const drawn = Array.from(document.querySelectorAll(selector))
    .filter((element) => element.getClientRects().length > 0);
  const element = drawn[drawn.length - 1];
  const region = element.closest(regions);
  const active = document.activeElement;
  const inside = active !== null && region !== null && region.contains(active);
  return {on: active === element, inside};
}
"""


def focus_faults(page, selectors) -> list[str]:
    """Spec 0.4 §5.8 and §8, R item 3: for the last drawn element of each
    selector of `selectors`, the ways in which the keyboard does not reach
    it or it traps the focus, each one line. The element is
    reached where the focus given to it stays there and, after Shift+Tab,
    Tab returns the focus to it; it does not trap the focus where Tab
    pressed from it moves the focus on within twenty presses to an element
    outside its region (REGIONS). An element that is not drawn is a
    fault."""
    faults = []
    for selector in selectors:
        places = page.evaluate(MARK_DRAWN_JS, selector)
        if not places:
            faults.append(f"{selector}: not drawn")
            continue
        give_focus(page, places[-1])
        if not page.evaluate(FOCUS_PLACE_JS, [selector, REGIONS])["on"]:
            faults.append(f"{selector}: takes no focus")
            continue
        page.keyboard.press("Shift+Tab")
        page.keyboard.press("Tab")
        if not page.evaluate(FOCUS_PLACE_JS, [selector, REGIONS])["on"]:
            faults.append(f"{selector}: Tab from the element before it does not reach it")
            continue
        for _ in range(20):
            page.keyboard.press("Tab")
            if not page.evaluate(FOCUS_PLACE_JS, [selector, REGIONS])["inside"]:
                break
        else:
            faults.append(f"{selector}: twenty presses of Tab do not leave its region")
    return faults


# For an element: whether it holds the focus, as the document's active
# element, which is a VSCode Elements control while its own button holds
# the focus; its accessible name and its classes.
HELD_JS = """
(element) => ({
  name: element.getAttribute('aria-label') || element.getAttribute('label')
    || element.label || element.textContent.trim(),
  classes: element.getAttribute('class'),
  held: document.activeElement === element,
})
"""
# Whether an element draws an outline, its computed outline style not `none`
# and its width above 0.
OUTLINE_JS = """
(element) => {
  const style = getComputedStyle(element);
  return style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0;
}
"""


# whether the editor holds the keyboard's focus
EDITOR_FOCUSED_JS = """
() => document.activeElement !== null && document.activeElement.closest('.cm-editor') !== null
"""


def outline_faults(page, selector: str) -> list[str]:
    """Spec 0.4 §5.8: the drawn elements of `selector` that, given the
    keyboard's focus as a reader gives it, do not hold it or draw no
    outline, each one line with the element's accessible name and its
    classes. The focus is given to the element, then Shift+Tab and Tab are
    pressed, so that the browser counts the focus as the keyboard's
    (`:focus-visible`). Where Shift+Tab gives the focus to the editor,
    which keeps Tab for its indentation, Escape is pressed before Tab, as a
    reader leaves the editor by the keyboard (CodeMirror's `indentWithTab`):
    the Types panel's `open wide` follows the editor since its view tabs
    stand in the bar under its head (design pass 8 §6; unit M, Task 6)."""
    faults = []
    for place in page.evaluate(MARK_DRAWN_JS, selector):
        give_focus(page, place)
        page.keyboard.press("Shift+Tab")
        if page.evaluate(EDITOR_FOCUSED_JS):
            page.keyboard.press("Escape")
        page.keyboard.press("Tab")
        element = drawn_element(page, place)
        found = element.evaluate(HELD_JS)
        # a control of VSCode Elements draws its outline on the button its
        # own tree holds (design pass 8 §4), which Playwright's selectors
        # reach
        if element.evaluate("(found) => found.tagName.toLowerCase()").startswith("vscode-"):
            element = element.locator("button").first
        found["outlined"] = element.evaluate(OUTLINE_JS)
        element = f"{found['name']!r} ({found['classes']})"
        if not found["held"]:
            faults.append(f"{element}: Tab does not return the focus to it")
        elif not found["outlined"]:
            faults.append(f"{element}: no outline under the keyboard's focus")
    return faults


# The icons of the window (spec 0.4 §5.8; Design brief 7 §16): the
# graph's controls, `Go to`, the fold buttons, the main bar's toggles and
# the panels' `×` among them, and the panels' icon `open` (AAS, L-D12;
# design pass 10 §3); and VSCode Elements' toolbar buttons, the main bar's
# and the status line's (design pass 8 §6; unit M, Task 4).
ICON_BUTTONS = (
    ".bl-graph-icon, .bl-goto-button, .bl-fold, .bl-region-wide, vscode-toolbar-button"
)
# The drawn buttons under the window that hold a drawing in SVG and that
# the selector given does not name, each as the start of its markup.
OTHER_ICONS_JS = """
(named) => Array.from(document.querySelectorAll('.bl-window button'))
  .filter((button) => button.getClientRects().length > 0 && button.querySelector('svg') &&
    !button.matches(named))
  .map((button) => button.outerHTML.slice(0, 120))
"""

# The seven symbols of brief rule 1 whose face the report and item 6 name,
# and the four stacks of brand.css that set the page's texts (Task 1).
SYMBOLS = ("Υ", "≺", "∼", "≻", "ρ", "Γ", "ℝ")
STACKS = ("--bl-mono", "--bl-text", "--bl-display", "--bl-statement")

# Appends under the window one span for each pair of a symbol and a stack
# given, the symbol its text set in the stack, with `data-symbol-probe` its
# number in the pairs' order; answers once the page's fonts have loaded.
SYMBOL_PROBE_JS = """
async ([symbols, stacks]) => {
  const holder = document.querySelector('.bl-window');
  let index = 0;
  for (const symbol of symbols) {
    for (const stack of stacks) {
      const span = document.createElement('span');
      span.textContent = symbol;
      span.style.fontFamily = `var(${stack})`;
      span.setAttribute('data-symbol-probe', String(index++));
      holder.append(span);
    }
  }
  await document.fonts.ready;
}
"""
# removes the spans SYMBOL_PROBE_JS appended
SYMBOL_PROBE_REMOVE_JS = (
    "() => document.querySelectorAll('[data-symbol-probe]').forEach((span) => span.remove())"
)


def symbol_faces(page) -> dict[str, dict[str, set[str]]]:
    """The faces in which Chromium draws each symbol of SYMBOLS in each
    stack of STACKS on the page (brief rule 1), by the symbol and then by
    the stack, each set as `platform_faces` writes it; the probe's spans
    are removed afterwards (SYMBOL_PROBE_JS)."""
    page.evaluate(SYMBOL_PROBE_JS, [list(SYMBOLS), list(STACKS)])
    try:
        found = iter(platform_faces(page, "data-symbol-probe", len(SYMBOLS) * len(STACKS)))
        return {symbol: {stack: next(found) for stack in STACKS} for symbol in SYMBOLS}
    finally:
        page.evaluate(SYMBOL_PROBE_REMOVE_JS)


def platform_faces(page, attribute: str, count: int) -> list[set[str]]:
    """For each element whose attribute `attribute` holds a number from 0
    to `count` less one, in that order, the families in which Chromium drew
    its text, as the method `CSS.getPlatformFontsForNode` of the Chrome
    DevTools Protocol answers them, each written `<family> (custom)` where
    the page loaded the face and `<family>` where the system supplied it;
    the empty set for an element the page has removed since it was
    marked, as the editor removes a line it draws again."""
    session = page.context.new_cdp_session(page)
    try:
        session.send("DOM.enable")
        session.send("CSS.enable")
        root = session.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
        faces = []
        for index in range(count):
            selector = f'[{attribute}="{index}"]'
            node = session.send("DOM.querySelector", {"nodeId": root, "selector": selector})
            if not node["nodeId"]:
                faces.append(set())
                continue
            fonts = session.send("CSS.getPlatformFontsForNode", {"nodeId": node["nodeId"]})
            faces.append(
                {
                    f"{font['familyName']} (custom)"
                    if font["isCustomFont"]
                    else font["familyName"]
                    for font in fonts["fonts"]
                }
            )
        return faces
    finally:
        session.detach()


def origin_alone(page, url: str) -> list[str]:
    """Refuses every request of the page whose scheme, host and port are
    not those of `url`, as a closed network refuses it, and answers a list
    that holds, as they are made, the addresses of the requests the page
    makes to that origin (spec 0.4 §5.2: all runtime fonts are served
    locally; §8, R item 5)."""
    from urllib.parse import urlsplit

    origin = urlsplit(url)[:2]
    requested: list[str] = []

    def route(handled) -> None:
        address = handled.request.url
        if urlsplit(address)[:2] == origin:
            requested.append(address)
            handled.continue_()
        else:
            handled.abort()

    page.route("**/*", route)
    return requested


# Every text the page draws and every hover, accessible name, accessible
# description, placeholder and image's text of a drawn element, in document
# order, for the interface-text review (the project's lean-implementation rule,
# last section; Task 16 of unit R's plan). An element is drawn where the
# browser gives it a box. A drawn text is the text nodes an element holds
# directly, joined, or the content of its ::before or ::after; the editor's
# source lines and its line numbers are the file's text, not the page's,
# and are left out. Each record names the element's classes of the page
# (`bl-`, `bf-`, `cm-`, `react-flow__`), those of its nearest ancestor that
# has some where it has none.
PAGE_TEXTS_JS = r"""
() => {
  const own = /^(bl-|bf-|cm-|react-flow__)/;
  const classOf = (element) => {
    for (let at = element; at && at !== document.documentElement; at = at.parentElement) {
      const names = (at.getAttribute('class') || '').split(/\s+/)
        .filter((name) => own.test(name));
      if (names.length) return '.' + names.join('.');
    }
    return element.tagName.toLowerCase();
  };
  const tidy = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const generated = (element, place) => {
    const content = getComputedStyle(element, place).content;
    if (!content || content === 'none' || content === 'normal') return '';
    return tidy(content.replace(/^"(.*)"$/, '$1'));
  };
  const skipped = 'SCRIPT, STYLE, NOSCRIPT, TEMPLATE';
  const records = [];
  const seen = new Set();
  const add = (kind, element, text) => {
    text = tidy(text);
    if (!text) return;
    const record = {kind, class: classOf(element), text};
    const key = JSON.stringify(record);
    if (seen.has(key)) return;
    seen.add(key);
    records.push(record);
  };
  for (const element of document.body.querySelectorAll('*')) {
    if (element.matches(skipped) || element.closest('.cm-content, .cm-gutters')) continue;
    if (element.getClientRects().length === 0 && element.tagName.toLowerCase() !== 'title') {
      continue;
    }
    if (element.tagName.toLowerCase() === 'title') {
      if (element.parentElement && element.parentElement.getClientRects().length) {
        add('title', element.parentElement, element.textContent);
      }
      continue;
    }
    const direct = Array.from(element.childNodes)
      .filter((node) => node.nodeType === Node.TEXT_NODE)
      .map((node) => node.textContent).join(' ');
    add('text', element, generated(element, '::before'));
    add('text', element, direct);
    add('text', element, generated(element, '::after'));
    add('title', element, element.getAttribute('title'));
    add('aria-label', element, element.getAttribute('aria-label'));
    add('aria-description', element, element.getAttribute('aria-description'));
    const described = (element.getAttribute('aria-describedby') || '').split(/\s+/)
      .filter(Boolean).map((id) => document.getElementById(id))
      .filter(Boolean).map((found) => found.textContent).join(' ');
    add('aria-description', element, described);
    add('placeholder', element, element.getAttribute('placeholder'));
    add('alt', element, element.getAttribute('alt'));
  }
  return records;
}
"""


def page_texts(page) -> list[dict]:
    """Every drawn text of the page and every hover, accessible name,
    accessible description, placeholder and image's text of a drawn
    element, each once, in document order, as PAGE_TEXTS_JS reads them: a
    record holds `kind` (`text`, `title`, `aria-label`, `aria-description`,
    `placeholder` or `alt`), `class`, the element's classes of the page,
    and `text`."""
    return page.evaluate(PAGE_TEXTS_JS)


# --- unit J: the gestures of the trellis graph ---


def _rewritten(path: Path, old: str, new: str) -> None:
    """Writes the file `path` with its one occurrence of `old` replaced by
    `new`; a file that holds `old` other than once is refused, so that a
    change of the repository's file is seen in the copy's builder."""
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (path, old)
    path.write_text(text.replace(old, new), encoding="utf-8")


def _committed(root: Path, message: str) -> Path:
    """Commits every change of the tracked files of the repository `root`
    with `message`; answers `root`."""
    _git(root, "commit", "-q", "-a", "-m", message)
    return root


def emptied_port_cons(target: Path) -> Path:
    """The copy of cons-port of `applications_copy` under `target` whose
    trellis file `declaration/trellis.port-cons.yml` writes its connector
    and its one inter-period mapping each emptied to `- {}`, the change
    committed; answers the copy (unit J's plan, Task 5: the first of item
    1's three copies)."""
    folder = applications_copy(target)
    _rewritten(folder / PORT_CONS, "- {w: m}", "- {}")
    _rewritten(folder / PORT_CONS, "- {disc.a: k}", "- {}")
    return _committed(folder, "the connector and the inter-period mapping emptied")


def emptied_portfolio(target: Path) -> Path:
    """A copy of `applications/portfolio-choice/` at
    `target/portfolio-choice`, a fresh git repository, whose
    `declaration/period.yml` writes its connector and whose
    `declaration/trellis.yml` writes its inter-period mapping each emptied
    to `- {}`, the change committed; answers the copy (unit J's plan,
    Task 5: the second of item 1's three copies)."""
    folder = repository_copy(PORTFOLIO_CHOICE, target / "portfolio-choice")
    _rewritten(folder / "declaration/period.yml", "- {m_next: m}", "- {}")
    _rewritten(folder / "declaration/trellis.yml", "- {disc.a: k}", "- {}")
    return _committed(folder, "the connector and the inter-period mapping emptied")


def emptied_portfolio_with_entry_connectors(target: Path) -> Path:
    """The copy `emptied_portfolio` whose entry of `declaration/trellis.yml`
    writes its own `connectors: [{}]`, which stands over the connectors of
    the period file the entry names, the change committed; answers the copy
    (unit J's plan, Task 5: the third of item 1's three copies)."""
    folder = emptied_portfolio(target)
    _rewritten(
        folder / "declaration/trellis.yml",
        "- {template: period.yml, repeat: 6}",
        "- {template: period.yml, repeat: 6, connectors: [{}]}",
    )
    return _committed(folder, "the entry's own connectors written")


def unsaved_of(folder: Path, edits: dict[str, str], revision: int = 1) -> dict:
    """The mapping of unsaved texts that `trellis.show_trellis` takes as
    `unsaved`, for the texts `edits` gives by each file's path relative to
    the folder `folder`: each file's resolved path, as a string, with
    `trellis.Unsaved(text, revision)`, the key `app.unsaved_texts` gives a
    buffer (spec 0.4 §3.1)."""
    from bellman_workbench import trellis

    return {
        str((Path(folder) / path).resolve()): trellis.Unsaved(text, revision)
        for path, text in edits.items()
    }


def collection_unjoined_ports(collection: dict, graph: str = "forward") -> set[str]:
    """The ids of the ports of the graph `graph` of a trellis view's
    collection, as a dictionary or as the graph JSON reads it, that the
    exporter marks `unjoined` (spec 0.4 §3.4)."""
    return {
        item["id"]
        for node in graph_named(collection, graph)["nodes"]
        for side in ("inputsMetadata", "outputsMetadata")
        for item in node.get(side) or []
        if any(pair["key"] == "unjoined" for pair in item["attrs"])
    }


def five_mappings_port_cons(target: Path) -> Path:
    """The copy `emptied_port_cons` whose `inter_connectors` writes one
    empty mapping for each of its five adjacent pairs, `- {}` five times,
    its connector still emptied, the change committed; answers the copy
    (unit J's plan, Task 8)."""
    folder = emptied_port_cons(target)
    _rewritten(
        folder / PORT_CONS, "inter_connectors:\n  - {}\n", "inter_connectors:\n" + "  - {}\n" * 5
    )
    return _committed(folder, "one inter-period mapping for each pair")


def emptied_records(target: Path) -> Path:
    """The folder of records `records_folder` under `target` with the
    connector and the one inter-period mapping of `PORT_CONS_RECORDS` each
    emptied to `{}`, the change committed; answers the copy. The records
    route's counterpart of `emptied_port_cons` since the two cons-port
    folders became one (28 October 2026)."""
    folder = records_folder(target)
    _rewritten(folder / PORT_CONS_RECORDS, "- {w: m}", "- {}")
    _rewritten(folder / PORT_CONS_RECORDS, "- {disc.a: k}", "- {}")
    return _committed(folder, "the connector and the inter-period mapping emptied")


def two_cons_period(target: Path) -> Path:
    """The copy `emptied_records` whose period holds `cons_one` and
    `cons_two` in place of `cons`, two occurrences of `cons.bl`, each with
    the record of `cons`, so that both arrive at `m` and both continue to
    `a`, the change committed; answers the copy (unit J's plan, Task 8). The
    records stand in `PORT_CONS_RECORDS`, the trellis file of records that
    remains (28 October 2026)."""
    folder = emptied_records(target)
    lines = (folder / PORT_CONS_RECORDS).read_text(encoding="utf-8").splitlines(keepends=True)
    (first,) = [n for n, line in enumerate(lines) if line.startswith("      cons: {")]
    # the record of `cons` is written on two lines
    record = lines[first] + lines[first + 1]
    _rewritten(
        folder / PORT_CONS_RECORDS,
        record,
        record.replace("cons: {", "cons_one: {", 1) + record.replace("cons: {", "cons_two: {", 1),
    )
    return _committed(folder, "two occurrences of the consumption stage")


COMPOSITION_STAGE = """@stage: relay
[id=arvl_to_dcsn, (INPUT : DOMAIN) : !arvl -> (d : DOMAIN) : !dcsn] {
    d = INPUT
}
[id=dcsn_to_cntn, (d) : !dcsn -> (OUTPUT : DOMAIN) : !cntn] {
    OUTPUT = d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# Two complete branch routes with distinct joint laws; the decision value states its
# derivatives by branch as derivative lines (AMD-MB-001 §4.3), and the arrival builder,
# whose law is the identity, carries them (D3).
COMPOSITION_BRANCH_STAGE = """@stage: merge
β : (0,1)
[id=arvl_to_dcsn, (x : ℝ₊, y : ℝ₊) : !arvl -> (x_d : ℝ₊, y_d : ℝ₊) : !dcsn] {
    x_d = x
    y_d = y
}
[id=dcsn_to_cntn, (x_d, y_d, d : !ctrl @ {up, down}) : !dcsn -> ()] {
    [label=up,   () -> (x_up : ℝ₊, y_up : ℝ₊) : !cntn] {
        x_up = x_d
        y_up = y_d
    }
    [label=down, () -> (x_dn : ℝ₊, y_dn : ℝ₊) : !cntn] {
        x_dn = x_d
        y_dn = y_d
    }
}
[id=cntn_to_dcsn, (V_up[>] : ℝ @ !vlu, V_dn[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V        = (V_up[>], V_dn[>])[d]
    D_{x_d}V = (D_{x_up}V_up[>], D_{x_dn}V_dn[>])[d]
    D_{y_d}V = (D_{y_up}V_up[>], D_{y_dn}V_dn[>])[d]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V_up[>], V_dn[>]) : !cntn -> (d : {up, down} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_up[>], V_dn[>])
}
"""


def composition_folder(target: Path, repeat=1, alternative_domain="ℝ₊", two_fields=False, branching=False) -> Path:
    """A small source-only model with inferred S.a → T.a and an unrelated
    stage U, for connection editing without the application experiments."""
    target.mkdir(parents=True)
    for key, incoming, outgoing, domain in (
        ("S", "x", "a", "ℝ₊"), ("T", "a", "y", "ℝ₊"),
        ("U", "z", "c", alternative_domain),
    ):
        text = (COMPOSITION_BRANCH_STAGE if branching else
                COMPOSITION_STAGE.replace("INPUT", incoming).replace("OUTPUT", outgoing).replace("DOMAIN", domain))
        if two_fields:
            second_in, second_out = {"S": ("q", "b"), "T": ("b", "v"), "U": ("w", "f")}[key]
            text = (text.replace(f"({incoming} : {domain})", f"({incoming} : {domain}, {second_in} : {domain})")
                    .replace(f"(d : {domain})", f"(d : {domain}, e : {domain})")
                    .replace("(d) : !dcsn", "(d, e) : !dcsn")
                    .replace(f"({outgoing} : {domain})", f"({outgoing} : {domain}, {second_out} : {domain})")
                    .replace(f"d = {incoming}\n", f"d = {incoming}\n    e = {second_in}\n")
                    .replace(f"{outgoing} = d\n", f"{outgoing} = d\n    {second_out} = e\n"))
        (target / f"{key}.bl").write_text(text, encoding="utf-8")
    connector = "{S.x_up: T.x, S.y_up: T.y, S.x_dn: T.x, S.y_dn: T.y}" if branching else "{}"
    (target / "period.yml").write_text(
        f"stages:\n  S: {{stage: S.bl}}\n  T: {{stage: T.bl}}\n  U: {{stage: U.bl}}\nconnectors: [{connector}]\n",
        encoding="utf-8",
    )
    (target / "trellis.yml").write_text(
        f"!trellis\nperiods:\n  - {{template: period.yml, repeat: {repeat}}}\ninter_connectors: []\n",
        encoding="utf-8",
    )
    return init_repository(target)


def field_port(shown, side: str, port: tuple) -> dict:
    """The port of the forward trellis graph `shown` draws that stands for
    the state field `port`, `(h, key, field)`, on the side `side`, `writing`
    or `reading`, joined or not, as `{"id", "node"}`: the output of the
    occurrence's own `Outputs`, or the input of its own `Inputs`, whose
    attribute `field` names the field (spec 0.4 §3.4; unit J's decisions
    J-D16 and J-D41)."""
    h, key, field = port
    writes = side == "writing"
    own, items = (
        ("GraphOutputs", "outputsMetadata") if writes else ("GraphInputs", "inputsMetadata")
    )
    node = f"periods[{h}]/{key}/{own}"
    nodes = graph_named(shown.collection, "forward")["nodes"]
    candidates = [
        [
            item["id"]
            for item in drawn.get(items) or []
            if {"key": "field", "value": field} in item["attrs"]
        ]
        for drawn in nodes
        if drawn["id"] == node
    ]
    assert candidates and len(candidates[0]) == 1, (
        f"no one port for the field {field!r} on {node}: the node's fields are "
        f"{[a['value'] for d in nodes if d['id'] == node for i in d.get(items) or [] for a in i['attrs'] if a['key'] == 'field']}, "
        f"the nodes of the occurrence {[d['id'] for d in nodes if d['id'].startswith(f'periods[{h}]/{key}/')]}"
    )
    ((found,),) = candidates
    return {"id": found, "node": node}


def connected_event(shown, folder, source: tuple, target: tuple) -> dict:
    """The record of the event `connected` the graph region sends for a
    drag from the writing port `source` to the reading port `target` of the
    forward trellis graph `shown` draws, each port named by `(h, key,
    field)` and joined or not (spec 0.4 §3.2; unit J's decision J-D41):
    `reading`, the record `trellis.reading_record` gives for the model
    folder `folder`; `source` and `target`, the ports' nodes; and
    `sourceHandle` and `targetHandle`, the ports' ids (`field_port`)."""
    from bellman_workbench import trellis

    writing, reading = field_port(shown, "writing", source), field_port(shown, "reading", target)
    return {
        "reading": trellis.reading_record(folder, shown),
        "source": writing["node"],
        "target": reading["node"],
        "sourceHandle": writing["id"],
        "targetHandle": reading["id"],
    }


def two_cons_one_joined(target: Path) -> Path:
    """The copy `two_cons_period` whose connector is the keyed connector
    from `port` to `cons_one`, so that in every period `cons_one`'s `m` is
    joined and `cons_two`'s `m` is unjoined, two occurrences of one stage
    that differ in their joins, the change committed; answers the copy
    (ruling J-P25)."""
    folder = two_cons_period(target)
    _rewritten(
        folder / PORT_CONS_RECORDS,
        "      - {}\n",
        "      - {from: port, to: cons_one, fields: {w: m}}\n",
    )
    return _committed(folder, "the connector from port to cons_one alone")


# For each port of the graph region that a drag can take (spec 0.4 §3.2;
# unit J's plan, Task 9), each `.bf-unjoined` port: its id in the graph JSON
# (`data-port`), its kind, `source` for a writing port and `target` for a
# reading port, the id of the box it stands on, and the colors of its border
# and of its ground as the browser computes them.
UNJOINED_PORTS_JS = """
() => Array.from(
  document.querySelectorAll('.bl-view-host .react-flow__handle.bf-unjoined'), (port) => {
  const style = getComputedStyle(port);
  return {
    port: port.dataset.port,
    kind: port.classList.contains('source') ? 'source' : 'target',
    box: port.closest('.react-flow__node').dataset.id,
    border: style.borderTopColor,
    fill: style.backgroundColor,
  };
})
"""

# the ids of the layers the region marks as reached by the line of a drag
# (spec 0.4 §3.2), in sorted order
REACHED_LAYERS_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__node'))
  .filter((node) => node.querySelector(':scope > .bf-reached'))
  .map((node) => node.dataset.id).sort()
"""

# What the region shows while the button of a drag is held (spec 0.4
# §3.2): the layers marked as reached, whether the region is marked as
# dragging, the color of the connection line, null where none is drawn, the
# ids of the ports React Flow marks as a valid end of the drag, and, sorted,
# the ids of the reading ports drawn that the region marks as ports that
# would take it (unit J's decision J-D41).
DRAG_STATE_JS = f"""
() => {{
  const line = document.querySelector('.bl-view-host .react-flow__connection-path');
  return {{
    reached: ({REACHED_LAYERS_JS})(),
    connecting: !!document.querySelector('.bl-view-host .bf-region.bf-connecting'),
    line: line ? getComputedStyle(line).stroke : null,
    valid: Array.from(document.querySelectorAll('.bl-view-host .react-flow__handle.valid'),
      (port) => port.dataset.port),
    admitted: Array.from(
      document.querySelectorAll('.bl-view-host .react-flow__handle.bf-admitted'),
      (port) => port.dataset.port).sort(),
  }};
}}
"""

# the hover of the port whose id in the graph JSON is the argument, null
# where the region draws no such port
PORT_TITLE_JS = """
(id) => {
  const port = Array.from(document.querySelectorAll('.bl-view-host .react-flow__handle'))
    .find((handle) => handle.dataset.port === id);
  return port ? port.getAttribute('title') : null;
}
"""

# the record of the reading the region holds and returns with the event
# `connected`; null where it holds none (spec 0.4 §3.2)
REGION_READING_JS = "() => document.querySelector('.bl-view-host').bellmanFlow.reading()"

# Holds back every DOM event `name` (J-D17): a listener on `document`, in
# the capture phase, keeps each event's detail and stops the event before
# it reaches the region's host, while the page's list for `name` stands.
HOLD_EVENTS_JS = """
(name) => {
  window.heldEvents = window.heldEvents || {};
  window.holdingEvents = window.holdingEvents || {};
  window.heldEvents[name] = [];
  if (window.holdingEvents[name]) return;
  window.holdingEvents[name] = true;
  document.addEventListener(name, (event) => {
    const held = window.heldEvents[name];
    if (!held) return;
    event.stopImmediatePropagation();
    held.push(event.detail);
  }, true);
}
"""

# the details of the events `name` held back so far, in order
HELD_EVENTS_JS = "(name) => ((window.heldEvents || {})[name] || []).slice()"

# Ends the holding of the events `name` and sends each event held, in order,
# as a new event of that name, bubbling, with the same detail, dispatched on
# the region's host (J-D17); answers the details sent.
RELEASE_EVENTS_JS = """
(name) => {
  const held = (window.heldEvents || {})[name] || [];
  window.heldEvents[name] = null;
  const host = document.querySelector('.bl-view-host');
  for (const detail of held) host.dispatchEvent(new CustomEvent(name, {detail, bubbles: true}));
  return held;
}
"""

# the promise of the second animation frame from now
TWO_FRAMES_JS = (
    "() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))"
)


def unjoined_port_ids(page) -> list[str]:
    """The ids, in the graph JSON and in sorted order, of the ports the
    region draws as ports a drag can take, `.bf-unjoined` (spec 0.4 §3.2)."""
    return sorted(port["port"] for port in page.evaluate(UNJOINED_PORTS_JS))


def ports_on_box(page, box: str) -> list[str]:
    """The ids, in the graph JSON and in sorted order, of the ports a drag
    can take that the region draws on the box `box` (spec 0.4 §3.4)."""
    return sorted(port["port"] for port in page.evaluate(UNJOINED_PORTS_JS) if port["box"] == box)


def reached_layers(page) -> list[str]:
    """The ids of the layers the region marks as reached by the line of a
    drag, `.bf-reached`, in sorted order (spec 0.4 §3.2)."""
    return page.evaluate(REACHED_LAYERS_JS)


def hold_events(page, name: str) -> None:
    """Holds back every DOM event `name` before it reaches the region's
    host, from now until `release_events` (HOLD_EVENTS_JS; J-D17)."""
    page.evaluate(HOLD_EVENTS_JS, name)


def held_events(page, name: str) -> list:
    """The details of the events `name` held back since `hold_events`."""
    return page.evaluate(HELD_EVENTS_JS, name)


def release_events(page, name: str) -> list:
    """Ends the holding of the events `name` and sends each event held to
    the region's host, as the region sends one (RELEASE_EVENTS_JS); answers
    the details sent."""
    return page.evaluate(RELEASE_EVENTS_JS, name)


def _port_on_screen(page, port: str) -> tuple[float, float, float]:
    """The center of the element of the port whose `data-port` is `port`, a
    field port's id in the graph JSON or a cable port's value (`cable_port`),
    on the screen, and the element's width in pixels."""
    box = page.locator(f'.bl-view-host .react-flow__handle[data-port="{port}"]').bounding_box()
    assert box is not None, f"the port {port} is not drawn"
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, box["width"]


# The least distance in pixels from the graph region's border of a port a
# drag ends at: React Flow pans the view while the pointer of a connection
# stands within 40 pixels of the pane's border (`calcAutoPan` of
# @xyflow/system), which would move the port from under the pointer.
AUTO_PAN_MARGIN = 48


def _in_region(page, x: float, y: float) -> bool:
    """Whether the point `(x, y)` of the screen stands inside the graph
    region, `AUTO_PAN_MARGIN` pixels or more from its border."""
    box = page.locator(".bl-view-host .bf-region").bounding_box()
    return (
        box["x"] + AUTO_PAN_MARGIN < x < box["x"] + box["width"] - AUTO_PAN_MARGIN
        and box["y"] + AUTO_PAN_MARGIN < y < box["y"] + box["height"] - AUTO_PAN_MARGIN
    )


def _bring_into_region(page, port: str) -> tuple[float, float]:
    """During a drag, the pointer moved to the middle of the graph region,
    where React Flow does not pan the view, and the wheel turned back there
    until the port whose id in the graph JSON is `port` stands in the region
    (`_in_region`); answers the port's center on the screen."""
    box = page.locator(".bl-view-host .bf-region").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=4)
    page.evaluate(TWO_FRAMES_JS)
    for _ in range(30):
        x, y, _ = _port_on_screen(page, port)
        if _in_region(page, x, y):
            break
        page.mouse.wheel(0, 300)
        page.evaluate(TWO_FRAMES_JS)
    return x, y


def drag_ports(page, source_id: str, target_id: str) -> dict:
    """A drag by the pointer from the port whose `data-port` is `source_id`
    to the port `target_id`, each a field port's id in the graph JSON or a
    cable port's value (`cable_port`; spec 0.4 §3.2), made with the
    mouse as a reader makes it: the graph fitted to the region with its
    button `fit`; the wheel turned over the first port until its element is
    six pixels wide, so that the button can be pressed on it; the button
    pressed on its center and the pointer moved by two pixels, which starts
    the drag; the pointer moved to the middle of the region and the wheel
    turned back there until the second port stands in the region, clear of
    the border where React Flow pans the view (`_bring_into_region`); the
    pointer moved in steps to the second port's center and the button
    released there. Answers what the region showed
    while the button was held over the second port (DRAG_STATE_JS):
    `reached`, `connecting`, `line`, `valid` and `admitted`."""
    page.click(".bl-zoom-button[data-zoom='fit']")
    page.evaluate(TWO_FRAMES_JS)
    for _ in range(30):
        x, y, width = _port_on_screen(page, source_id)
        if width >= 6:
            break
        page.mouse.move(x, y)
        page.mouse.wheel(0, -300)
        page.evaluate(TWO_FRAMES_JS)
    x, y, _ = _port_on_screen(page, source_id)
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 2, y + 2)
    x, y = _bring_into_region(page, target_id)
    page.mouse.move(x, y, steps=12)
    page.evaluate(TWO_FRAMES_JS)
    state = page.evaluate(DRAG_STATE_JS)
    page.mouse.up()
    page.evaluate(TWO_FRAMES_JS)
    return state


def click_toggle(page, layer: str) -> None:
    """A click by the pointer on the toggle of the open layer whose id is
    `layer`, made as `drag_ports` reaches a port: the graph fitted to the
    region with its button `fit`, and the wheel turned over the toggle until
    its element is 20 pixels wide, so that a trellis graph opened on its
    terminal period (unit K's decision K-D6) shows a toggle of any period."""
    toggle = f'.bl-view-host .react-flow__node[data-id="{layer}"] .bf-layer > .bf-toggle'
    page.click(".bl-zoom-button[data-zoom='fit']")
    page.evaluate(TWO_FRAMES_JS)
    for _ in range(30):
        box = page.locator(toggle).bounding_box()
        assert box is not None, f"the toggle of {layer} is not drawn"
        if box["width"] >= 20:
            break
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.wheel(0, -300)
        page.evaluate(TWO_FRAMES_JS)
    page.click(toggle)


def gesture_trellis(app_state, target: Path, builder=None):
    """The copy `emptied_port_cons` under `target`, or the copy the function
    `builder` makes there, made the tab's folder of the page module
    (`app_state`), lesson 05's trellis file the tab's source, the forward
    trellis graph shown, and the trellis read by the trellis's task, its
    reading not refused; answers the copy and the trellis shown (unit J's
    plan, Tasks 10 and 19)."""
    from bellman_workbench import app, recipe

    copy = (builder or emptied_port_cons)(target)
    app_state(copy)
    app.source.value = recipe.Source("recipe", PORT_CONS_RECIPE)
    app.view_mode.value = "trellis"
    app.graph.value = "forward"
    outcome = app.run_trellis()
    assert outcome is not None and outcome.refusal is None
    return copy, outcome.shown


def clear_gesture_state() -> None:
    """The gestures' state of the page module's tab emptied, as a test of
    the steps of a gesture leaves it: no gesture waiting, no note, sentence
    or text of a last gesture, no request of the editor and no answer, no
    join wire selected, no gesture that edited several files and no undo of
    one waiting (unit L, Task 17), no file listed to delete on save (unit
    L, Task 25), the Recipe tab's stage list closed with no item chosen
    (unit N, Task 5) and no row of it open (design pass 11 §2), and the
    graph `backward` shown."""
    from bellman_workbench import app

    app.gesturing.value, app.gesture_note.value, app.gesture_refusal.value = None, None, None
    app.gesture_made.value, app.edit_request.value, app.edit_answer.value = None, None, None
    app.chosen_join.value = None
    app.gesture_steps.value, app.gesture_undoing.value = (), None
    app.deleting.value = ()
    app.recipe_chooser.value, app.recipe_chooser_file.value = False, None
    app.recipe_chosen_item.value = None
    app.recipe_open_stage.value = None
    app.graph.value = "backward"


def port_joins(collection: dict, graph: str = "forward") -> dict[str, str]:
    """The join each port of the graph `graph` of a trellis view's
    collection carries, by the port's id: the value of the port's attribute
    `join`, such as `m_next → m` or `inter_connectors[2] a → k`; a port
    that carries none is left out (spec 0.4 §3.1: the join stands on its
    wire)."""
    return {
        item["id"]: pair["value"]
        for node in graph_named(collection, graph)["nodes"]
        for side in ("inputsMetadata", "outputsMetadata")
        for item in node.get(side) or []
        for pair in item["attrs"]
        if pair["key"] == "join"
    }


# the text of the status line's note of the last gesture, null where none
# stands (brief rule 7)
GESTURE_NOTE_JS = "() => (document.querySelector('.bl-gesture-note') || {}).textContent || null"

# the paths of the files the tree marks `unsaved`, in sorted order
UNSAVED_IN_TREE_JS = """
() => Array.from(document.querySelectorAll('.bl-tree-file'))
  .filter((row) => row.querySelector('.bl-tree-mark.bl-dirty'))
  .map((row) => row.dataset.path).sort()
"""

# the ids in the graph JSON of a writing port and of a reading port of
# another box, the first of each the region draws
TWO_PORTS_JS = """
() => {
  const ports = Array.from(
    document.querySelectorAll('.bl-view-host .react-flow__handle[data-port]'));
  const writing = ports.find((port) => port.classList.contains('source'));
  const box = writing.closest('.react-flow__node');
  const reading = ports.find(
    (port) => port.classList.contains('target') && port.closest('.react-flow__node') !== box);
  return [writing.dataset.port, reading.dataset.port];
}
"""


def gesture_note(page) -> str | None:
    """The status line's note of the last gesture of the trellis graph,
    `.bl-gesture-note`; None where none stands (brief rule 7)."""
    return page.evaluate(GESTURE_NOTE_JS)


def unsaved_in_tree(page) -> list[str]:
    """The paths of the files whose row in the tree carries the mark
    `unsaved`, in sorted order."""
    return page.evaluate(UNSAVED_IN_TREE_JS)


def held_joins(page, graph: str = "forward") -> dict[str, str]:
    """The join each port of the graph `graph` of the collection the region
    holds carries, by the port's id (`port_joins`); empty where the region
    holds no collection."""
    held = page.evaluate(HELD_COLLECTION_JS)
    return port_joins(held, graph) if held is not None else {}


def with_required_connectors(folder: Path, connectors) -> Path:
    """The model folder `folder`, a git repository, given an answers.yml at
    its top that requires each connector `(file, address)` of `connectors`
    and no slot, in the form of the block `required` that
    `creation.answers_text` writes, the file committed; answers the folder
    (spec 0.4 §8 J (1): where answers.yml marks the connector required, the
    checklist's count falls by one)."""
    from bellman_workbench import creation

    listed = "".join(
        f'    - {{file: {file}, address: "{address}"}}\n' for file, address in connectors
    )
    (folder / creation.ANSWERS).write_text(
        f"required:\n  slots: []\n  connectors:\n{listed}", encoding="utf-8"
    )
    _git(folder, "add", creation.ANSWERS)
    return _committed(folder, "the connectors answers.yml requires")


def save_added(folder: Path, added) -> Path:
    """The model folder `folder` with what `creation.add_stage` or
    `creation.add_period` answered, `added`, written to disk, as the
    Workbench writes the new files and the reader's saves write the files
    the tree marks `unsaved` (spec 0.4 §3.5; ruling J-P5, J-D14): each new
    file at its path relative to the folder, and each edited file's new
    text at its resolved path, line ends as given; answers the folder."""
    for relative, text in added.new_files:
        target = Path(folder) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
    for path, text in added.edits.items():
        with open(path, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
    return Path(folder)


def save_unsaved_files(page) -> list[str]:
    """Opens each file the tree marks `unsaved` (`unsaved_in_tree`) and saves
    it with the button `save`, waiting until the tree no longer marks it, as
    the reader saves the files a form or a drop leaves unsaved (spec 0.4
    §3.5; brief rule 9, J-D14); answers the paths saved, in sorted order."""
    paths = unsaved_in_tree(page)
    for path in paths:
        open_tree_file(page, path)
        page.click(".bl-save")
        wait_until(lambda path=path: path not in unsaved_in_tree(page), 10.0, f"{path} saved")
    return paths


def dropped_event(shown, folder, item, kind, target: str) -> dict:
    """The record of the event `dropped` the graph region sends for a drop
    on the forward trellis graph `shown` draws (spec 0.4 §3.2): `item`, a
    stage's key or a template's id, None for Enter on a `+ period` control;
    `kind`, `stage` or `template`, None with no item; `target`, a period's
    layer id, `periods[2]___group___`, `earliest end` or `between periods[3]
    and periods[2]`; and `reading`, the record `trellis.reading_record` gives
    for the model folder `folder`, a `model.Folder`."""
    from bellman_workbench import trellis

    reading = trellis.reading_record(folder, shown)
    return {"item": item, "kind": kind, "target": target, "reading": reading}


def old_graph_gesture(trellis_file: Path):
    """The `trellis.Gesture` of a gesture that types nothing because its
    event names no part of the graph drawn: the sentence "An old graph" of
    brief §5 at the trellis file `trellis_file`, by its resolved path, with
    no address."""
    from bellman_workbench import trellis

    sentence = (
        f"{trellis_file.name}: nothing was written. The graph was drawn from an earlier text. "
        "Drag again in the graph now drawn."
    )
    return trellis.Gesture(None, None, (), None, sentence, str(trellis_file.resolve()), None)


# the files of cons-port's two orders, each recipe with the key-listing
# trellis file it names, which a folder of records does without (28 October
# 2026): a folder that holds a recipe is opened on it, and `load_trellis`
# refuses a key-listing file
RECIPE_FILES = (
    "declaration/spec.cons-port.yml",
    "declaration/spec.port-cons.yml",
    "declaration/trellis.cons-port.yml",
    "declaration/trellis.port-cons.yml",
)


def records_folder(target: Path) -> Path:
    """A copy of cons-port as a folder of records (`applications_copy` with
    the four files of `RECIPE_FILES` removed and the removal committed), so
    that the Workbench offers its trellis files of records, the first in name
    order `PORT_CONS_RECORDS`, the portfolio-first order with consumption
    chosen by a grid search."""
    folder = applications_copy(target)
    for name in RECIPE_FILES:
        (folder / name).unlink()
    return _committed(folder, "a folder of records")


def records_without(target: Path, h: int, key: str) -> Path:
    """The copy of cons-port of `applications_copy` under `target` whose
    trellis file `declaration/trellis.port-cons.yml` writes period `h`, from
    0 to 4, in an entry of its own, its entry of six periods split by the
    package's `split_entry`, and that entry without the record of the stage
    `key`, so that period `h` alone lacks that stage, the change committed;
    answers the copy (unit J's plan, Task 14: a trellis written as records in
    which a folder stage is dropped on a period that does not hold it)."""
    from bellman.trellis import entry_span, split_entry

    folder = records_folder(target)
    path = folder / PORT_CONS_RECORDS
    text = path.read_text(encoding="utf-8")
    # periods[h] the first period of the entry at index `entry` of the list
    if h == 0:
        text, entry = split_entry(text, "periods[0]", 1), 0
    else:
        text = split_entry(split_entry(text, "periods[0]", h), "periods[1]", 1)
        entry = 1
    span = entry_span(text, f"periods[{entry}].stages.{key}")
    lines = text.splitlines(keepends=True)
    del lines[span.line - 1 : span.end_line]
    path.write_text("".join(lines), encoding="utf-8")
    return _committed(folder, f"periods[{h}] written without {key}")


# the `+ period` controls the region draws (spec 0.4 §3.6), each as [its
# target, the left and the right edge of its box on the screen], in the order
# of their places from left to right
PERIOD_CONTROLS_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .bf-add-period'), (control) => {
  const box = control.getBoundingClientRect();
  return [control.dataset.target, box.left, box.right];
}).sort((a, b) => a[1] - b[1])
"""

# the left edge on the screen of the box of the region whose id is given
BOX_LEFT_JS = """
(id) => document.querySelector(
  `.bl-view-host .react-flow__node[data-id="${CSS.escape(id)}"]`).getBoundingClientRect().left
"""

# What the region marks while a stage of the list is dragged over the graph
# (spec 0.4 §3.2): the ids of the layers marked `.bf-reached`, in sorted
# order, and the target of the `+ period` control marked, null where none is.
DROP_STATE_JS = """
() => ({
  reached: Array.from(document.querySelectorAll('.bl-view-host .react-flow__node'))
    .filter((node) => node.querySelector(
      ':scope > .bf-layer.bf-reached, :scope > .bf-box.bf-reached'))
    .map((node) => node.dataset.id).sort(),
  control: (document.querySelector('.bl-view-host .bf-add-period.bf-reached') || {dataset: {}})
    .dataset.target || null,
})
"""

# Where the keyboard's focus stands for a drop by keyboard: `item`, the id of
# the item of the stage list whose element holds it; `target`, the target of
# the `+ period` control that holds it; `box`, the id of the region's box
# whose element holds it; each null where it is not so.
KEYBOARD_PLACE_JS = """
() => {
  const active = document.activeElement;
  const data = (active && active.dataset) || {};
  const node = active && active.closest ? active.closest('.bl-view-host .react-flow__node') : null;
  const box = node ? node.dataset.id : null;
  return {item: data.item || null, target: data.target || null, box: box};
}
"""


def add_period_controls(page) -> list[str]:
    """The targets of the `+ period` controls the region draws,
    `.bf-add-period` with `data-target` (spec 0.4 §3.6): `earliest end` or
    `between periods[h] and periods[h−1]`, in the order of their places
    from left to right."""
    return [target for target, _, _ in page.evaluate(PERIOD_CONTROLS_JS)]


def controls_left_of(page, box: str) -> bool:
    """Whether every `+ period` control the region draws stands wholly left
    of the box `box`, the terminal period's layer in a forward trellis graph
    (spec 0.4 §3.6: no control at the terminal end)."""
    left = page.evaluate(BOX_LEFT_JS, box)
    return all(right <= left for _, _, right in page.evaluate(PERIOD_CONTROLS_JS))


def _drop_target(target: str) -> str:
    """The selector of the element of a drop's target: the node of a
    period's layer for the layer id `periods[h]___group___`, else the `+
    period` control whose target is `target`."""
    from bellman.stage import LAYER_ID_ENDING

    if target.endswith(LAYER_ID_ENDING):
        return f'.bl-view-host .react-flow__node[data-id="{target}"]'
    return f'.bl-view-host .bf-add-period[data-target="{target}"]'


def _drop_point(page, target: str) -> tuple[float, float]:
    """The center, on the screen, of the part of the target's element that
    stands within the graph region."""
    box = page.locator(_drop_target(target)).bounding_box()
    assert box is not None, f"the target {target} is not drawn"
    region = page.locator(".bl-view-host .bf-region").bounding_box()
    left, top = max(box["x"], region["x"]), max(box["y"], region["y"])
    right = min(box["x"] + box["width"], region["x"] + region["width"])
    bottom = min(box["y"] + box["height"], region["y"] + region["height"])
    assert left < right and top < bottom, f"the target {target} stands outside the region"
    return (left + right) / 2, (top + bottom) / 2


def open_stage_list(page) -> None:
    """Opens the stage list with the button `stages` of the graph's head,
    `.bl-stages-button`, where it is not open, and waits for its items."""
    if page.locator(".bl-view-host .bf-stage-list").count() == 0:
        page.click(".bl-stages-button")
    page.wait_for_selector(".bl-view-host .bf-stage-list .bf-stage-item", timeout=10_000)


def drop_item(page, item_id: str, target: str) -> dict:
    """A drop by the pointer (spec 0.4 §3.2; brief rule 9): the graph fitted
    to the region with its button `fit`, the stage list opened, the button
    pressed on the item whose id is `item_id`, a stage's key or a template's
    id, the pointer moved in steps to the center of the part of `target`
    within the region, `periods[h]___group___` or a `+ period` control's
    target, and released there, which the browser's own drag-and-drop
    carries. Answers what the region marked while the button was held over
    the target (DROP_STATE_JS): `reached` and `control`."""
    page.click(".bl-zoom-button[data-zoom='fit']")
    page.evaluate(TWO_FRAMES_JS)
    open_stage_list(page)
    item = page.locator(f'.bl-view-host .bf-stage-item[data-item="{item_id}"]')
    item.scroll_into_view_if_needed()
    start = item.bounding_box()
    x, y = _drop_point(page, target)
    x0, y0 = start["x"] + start["width"] / 2, start["y"] + start["height"] / 2
    page.mouse.move(x0, y0)
    page.mouse.down()
    page.mouse.move(x0 + 6, y0 + 6, steps=3)
    page.mouse.move(x, y, steps=12)
    page.evaluate(TWO_FRAMES_JS)
    state = page.evaluate(DROP_STATE_JS)
    page.mouse.up()
    page.evaluate(TWO_FRAMES_JS)
    return state


def keyboard_place(page) -> dict:
    """Where the keyboard's focus stands (KEYBOARD_PLACE_JS): `item`,
    `target` and `box`."""
    return page.evaluate(KEYBOARD_PLACE_JS)


def drop_by_keyboard(page, item_id: str | None, target: str, limit: int = 200) -> None:
    """A drop by the keyboard (spec 0.4 §3.5, §3.6; brief rule 9). With
    `item_id` None, Enter on the `+ period` control `target`, reached by Tab
    in the region's order from its first box. Otherwise the button `stages`
    pressed with Enter, which opens the list with the focus on its first
    item; ArrowDown pressed until the focus stands on the item `item_id`;
    Enter, which makes the period layers and the controls the candidates;
    ArrowRight pressed until the focus stands on `target`, a period's layer
    id or a control's target; and Enter, which sends the drop."""

    def reached() -> bool:
        place = keyboard_place(page)
        return target in (place["target"], place["box"])

    if item_id is None:
        focus_region(page)
        for _ in range(limit):
            if reached():
                break
            assert press_in_region(page, "Tab") is not None, f"Tab left the region before {target}"
        else:
            raise AssertionError(f"Tab did not reach the control {target}")
        page.keyboard.press("Enter")
        return
    page.focus(".bl-stages-button")
    page.keyboard.press("Enter")
    wait_until(lambda: keyboard_place(page)["item"] is not None, 10.0, "the focus on an item")
    for _ in range(limit):
        if keyboard_place(page)["item"] == item_id:
            break
        before = keyboard_place(page)
        page.keyboard.press("ArrowDown")
        wait_until(lambda before=before: keyboard_place(page) != before, 5.0, "the next item")
    else:
        raise AssertionError(f"ArrowDown did not reach the item {item_id}")
    page.keyboard.press("Enter")
    wait_until(lambda: keyboard_place(page)["box"] is not None, 10.0, "the focus on a candidate")
    for _ in range(limit):
        if reached():
            break
        before = keyboard_place(page)
        page.keyboard.press("ArrowRight")
        wait_until(lambda before=before: keyboard_place(page) != before, 5.0, "the next candidate")
    else:
        raise AssertionError(f"ArrowRight did not reach {target}")
    page.keyboard.press("Enter")


def control_targets(count: int) -> list[str]:
    """The targets of the `+ period` controls of a forward trellis graph of
    `count` periods drawn whole, from left to right: the earliest end, then
    between each two adjacent periods, none at the terminal end (spec 0.4
    §3.6)."""
    return ["earliest end"] + [
        f"between periods[{h}] and periods[{h - 1}]" for h in range(count - 1, 0, -1)
    ]


def period_layers(periods) -> list[str]:
    """The ids of the layers of the periods `periods`, `periods[h]___group___`,
    in sorted order."""
    from bellman.stage import LAYER_ID_ENDING

    return sorted(f"periods[{h}]{LAYER_ID_ENDING}" for h in periods)


def join_event(shown, folder, writing: str, reading: str, end=None, port=None, texts=None) -> dict:
    """The record of the event `removed` that the graph region sends for the
    join wire of the forward trellis graph `shown` draws from the stage
    occurrence `writing` to the stage occurrence `reading`, each named by
    its address, `periods[2]/port` (unit J's decision J-D33): `reading`, the
    record `trellis.reading_record` gives for the model folder `folder`, and
    `join`, the wire's two nodes and two ports (`trellis.join_wires`, read
    through the mapping of unsaved texts `texts`). Where `end` is given, the
    record of the event `moved`: `end`, the end moved, `reading` or
    `writing`, and `handle`, the id of the unjoined port `port`, `(h, key,
    field)`, on that side (`trellis.unjoined_ports`)."""
    from bellman_workbench import trellis

    (wire,) = [
        wire
        for wire in trellis.join_wires(shown, texts)
        if (wire["from"], wire["to"]) == (writing, reading)
    ]
    ids = ("source", "sourceHandle", "target", "targetHandle")
    event = {
        "reading": trellis.reading_record(folder, shown),
        "join": {name: wire[name] for name in ids},
    }
    if end is not None:
        (found,) = [
            item["id"]
            for item in trellis.unjoined_ports(shown, texts)
            if (item["side"], item["h"], item["key"], item["field"]) == (end, *port)
        ]
        event.update(end=end, handle=found)
    return event


def remove_chosen_join(shown, writing: str, reading: str) -> None:
    """The join wire of the forward trellis graph `shown` from the stage
    occurrence `writing` to the stage occurrence `reading`, each named by
    its address, `periods[2]/port`, selected in the page module's tab
    (`app.on_join_chosen`) and removed by the button `remove` of Details
    (`app.remove_join`), as the page does (unit J's decision J-D33)."""
    from bellman_workbench import app, trellis

    folder = app.tab_folder.value
    (wire,) = [
        wire
        for wire in trellis.join_wires(shown)
        if (wire["from"], wire["to"]) == (writing, reading)
    ]
    app.on_join_chosen({"reading": trellis.reading_record(folder, shown), "join": wire})
    app.remove_join()


# the join wires the region draws (unit J's decision J-D33): for each, the
# addresses of its two stage occurrences, whether it is selected, and the
# color of its line as the browser computes it
JOIN_WIRES_JS = """
() => Array.from(
  document.querySelectorAll('.bl-view-host .react-flow__edge.bf-join-wire'), (edge) => ({
  from: edge.dataset.from,
  to: edge.dataset.to,
  selected: edge.classList.contains('selected'),
  stroke: getComputedStyle(edge.querySelector('.react-flow__edge-path')).stroke,
}))
"""

# the wires the region draws that print a join's label (unit K's decision
# K-D4): for each, the label printed on it and its title, its hover text
DRAWN_JOINS_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .react-flow__edge'))
  .filter((edge) => edge.querySelector('.bf-join'))
  .map((edge) => ({
    label: edge.querySelector('.bf-join').textContent,
    title: (edge.querySelector('title') || {}).textContent || '',
  }))
"""

# the boxes the region draws, by id, each at its place at scale 1, `{x, y,
# width, height}`, read from its node's element, a boundary marker's box
# holding its mark, which is its node, and its label, which stands beside
# the mark in the room the layout keeps for it (design pass 10 §6; N-I277);
# and the pieces that the wires of an adjacent pair of periods share,
# `.bf-join-pair`, each with the addresses of its writers' period and its
# reading occurrence and the box that holds its line at scale 1 (unit K's
# decisions K-D5 and K-D13)
DRAWN_PLACES_JS = """
() => {
  const nodes = {};
  for (const node of document.querySelectorAll('.bl-view-host .react-flow__node')) {
    const found = /translate\\(\\s*(-?[\\d.]+)px,\\s*(-?[\\d.]+)px\\)/.exec(node.style.transform);
    if (!found) continue;
    let x = Number(found[1]), y = Number(found[2]);
    let width = node.offsetWidth, height = node.offsetHeight;
    const label = node.querySelector('.bf-marker > .bf-boundary-label');
    if (label) {
      const left = Math.min(0, label.offsetLeft), top = Math.min(0, label.offsetTop);
      const right = Math.max(width, label.offsetLeft + label.offsetWidth);
      const bottom = Math.max(height, label.offsetTop + label.offsetHeight);
      x += left; y += top; width = right - left; height = bottom - top;
    }
    nodes[node.dataset.id] = {x, y, width, height};
  }
  const pairs = Array.from(
    document.querySelectorAll('.bl-view-host .react-flow__edge.bf-join-pair'), (edge) => {
      const box = edge.querySelector('.react-flow__edge-path').getBBox();
      return {from: edge.dataset.from, to: edge.dataset.to,
              x: box.x, y: box.y, width: box.width, height: box.height};
    });
  return {nodes, pairs};
}
"""

# the number of wires the region lets the pointer select
SELECTABLE_WIRES_JS = (
    "() => document.querySelectorAll('.bl-view-host .react-flow__edge.selectable').length"
)

# the point of the screen at the middle of the line of the join wire from
# the stage occurrence `from` to `to`, measured along the first part of its
# path, the path's `M` and `L` points read from its `d`: for a wire of a
# bundle, the part from its writer to the piece the bundle draws (unit K's
# decision K-D5); for any other wire, its whole route; null where none is
# drawn. On a wire of a bundle between compact frames (AAS, L-D7), the part
# at the reader's frame can lie within the press circles of other wires'
# reading ends, the pair's among them, which then take a click there
# (K-D23, K-I226); row L-I54, for AAS, records the measured target.
JOIN_POINT_JS = """
([from, to]) => {
  const edge = document.querySelector(
    `.bl-view-host .react-flow__edge.bf-join-wire[data-from="${from}"][data-to="${to}"]`);
  if (!edge) return null;
  const path = edge.querySelector('.react-flow__edge-path');
  const first = [];
  for (const step of path.getAttribute('d').match(/[ML][^ML]*/g) || []) {
    if (step[0] === 'M' && first.length) break;
    const [x, y] = step.slice(1).split(',').map(Number);
    first.push({x, y});
  }
  const lengths = first.slice(1).map((at, i) => Math.hypot(at.x - first[i].x, at.y - first[i].y));
  let rest = lengths.reduce((sum, length) => sum + length, 0) / 2, point = null;
  if (lengths.every(Number.isFinite) && rest > 0) {
    for (let i = 0; i < lengths.length && !point; i++) {
      if (rest <= lengths[i]) {
        const share = rest / lengths[i];
        point = {x: first[i].x + share * (first[i + 1].x - first[i].x),
                 y: first[i].y + share * (first[i + 1].y - first[i].y)};
      }
      rest -= lengths[i];
    }
  }
  if (!point) point = path.getPointAtLength(path.getTotalLength() / 2);
  const m = path.getScreenCTM();
  return {x: m.a * point.x + m.c * point.y + m.e, y: m.b * point.x + m.d * point.y + m.f};
}
"""

# the center of the screen and the width of the element by which the end
# `end`, `source` or `target`, of the join wire from `from` to `to` is
# dragged, its end square or, on a cable, its anchor of the same place and
# size, which is not painted (the fix wave Q3a of unit Q, item 5); null
# where none is drawn
JOIN_END_JS = """
([from, to, end]) => {
  const edge = document.querySelector(
    `.bl-view-host .react-flow__edge.bf-join-wire[data-from="${from}"][data-to="${to}"]`);
  const side = end === 'source' ? 'writing' : 'reading';
  // a wire's end square, or a cable's anchor at its place, which is not painted (the fix wave Q3a, item 5)
  const anchor = edge && edge.querySelector(
    '.bf-wire-end[data-end="' + side + '"], .bf-wire-anchor[data-end="' + side + '"]');
  if (!anchor) return null;
  const box = anchor.getBoundingClientRect();
  return {x: box.x + box.width / 2, y: box.y + box.height / 2, width: box.width};
}
"""

# whether the editor draws a selected text, and the line of its cursor
EDITOR_SELECTION_JS = """
() => ({
  selected: document.querySelectorAll('.bl-editor .cm-selectionBackground').length > 0,
  line: (document.querySelector('.bl-editor .cm-activeLineGutter') || {}).textContent || null,
})
"""


def join_wires_drawn(page) -> list[dict]:
    """The join wires the region draws, each `{from, to, selected,
    stroke}` (JOIN_WIRES_JS; unit J's decision J-D33)."""
    return page.evaluate(JOIN_WIRES_JS)


def _zoom_over(page, place) -> dict:
    """Turns the wheel over the point `place()` answers until the region's
    scale is 0.5 or more, the graph first fitted to the region; answers
    the point then. The wire is awaited after the fit and after each turn
    of the wheel: a scale that crosses 0.75 lays the graph out again with
    no card unfolded (design pass 13 §1, rule 3), and the new edges take
    their records a moment after they are drawn."""
    page.click(".bl-zoom-button[data-zoom='fit']")
    page.evaluate(TWO_FRAMES_JS)
    for _ in range(40):
        point, _ = wait_until(place, 10.0, "the join wire drawn")
        if viewport(page)["zoom"] >= 0.5:
            return point
        page.mouse.move(point["x"], point["y"])
        page.mouse.wheel(0, -300)
        page.evaluate(TWO_FRAMES_JS)
    raise AssertionError("the region was not enlarged")


def click_join(page, writing: str, reading: str) -> None:
    """A click by the pointer on the middle of the line of the join wire
    from the stage occurrence `writing` to `reading`, each by its address,
    `periods[2]/port`, the region enlarged first, so that the click finds
    the line (unit J's decision J-D33; amendment 02, ruling 11)."""
    point = _zoom_over(page, lambda: page.evaluate(JOIN_POINT_JS, [writing, reading]))
    page.mouse.click(point["x"], point["y"])
    page.evaluate(TWO_FRAMES_JS)


def move_join_end(page, writing: str, reading: str, end: str, port: str) -> None:
    """A drag by the pointer of the end `end`, `source` or `target`, of the
    join wire from `writing` to `reading` to the port whose `data-port` is
    `port`, a field port's id in the graph JSON or a cable port's value
    (`cable_port`; unit J's decision J-D33; amendment 02, ruling 14): the
    region enlarged over that end, the button pressed on it and the pointer
    moved by two pixels, which starts the drag, the pointer moved to the
    middle of the region and the wheel turned back there until the port
    stands in the region, clear of the border where React Flow pans the view
    (`_bring_into_region`), the pointer moved in steps to the port's center
    and the button released there."""
    _zoom_over(page, lambda: page.evaluate(JOIN_END_JS, [writing, reading, end]))
    point = page.evaluate(JOIN_END_JS, [writing, reading, end])
    page.mouse.move(point["x"], point["y"])
    page.mouse.down()
    page.mouse.move(point["x"] + 2, point["y"] + 2)
    x, y = _bring_into_region(page, port)
    page.mouse.move(x, y, steps=12)
    page.evaluate(TWO_FRAMES_JS)
    page.mouse.up()
    page.evaluate(TWO_FRAMES_JS)


def editor_selection(page) -> dict:
    """Whether the editor draws a selected text, and the line of its
    cursor (EDITOR_SELECTION_JS; unit J's decision J-D40)."""
    return page.evaluate(EDITOR_SELECTION_JS)


def durables_without_a(target: Path) -> Path:
    """A copy of `applications/durables/` at `target/durables`, a fresh git
    repository, whose standing inter-period mapping in
    `declaration/trellis.yml` has both entries of the state `a`,
    `a_nxt_kp: a` and `a_nxt_adj: a`, taken out, so that no join reaches
    `tenure`'s arrival field `a` and none reads the two consumption stages'
    `a_nxt_kp` and `a_nxt_adj` before the terminal period, the change
    committed; answers the copy (unit J's brief, decision J-D8: the trellis
    on which item 1's time is recorded)."""
    folder = repository_copy(DURABLES, target / "durables")
    _rewritten(
        folder / "declaration/trellis.yml",
        "  - {a_nxt_kp: a, h_nxt_kp: h, z_nxt_kp: z, a_nxt_adj: a, h_nxt_adj: h, z_nxt_adj: z}\n",
        "  - {h_nxt_kp: h, z_nxt_kp: z, h_nxt_adj: h, z_nxt_adj: z}\n",
    )
    return _committed(folder, "the two entries of the state a taken out")


def emptied_pension(target: Path) -> Path:
    """A copy of `applications/pension-retirement/` at
    `target/pension-retirement`, a fresh git repository, whose one standing
    inter-period mapping in `declaration/trellis.yml` is emptied to
    `- {}`, so that in `periods[1]` and every earlier period no join reads
    `retiree_saving`'s two continuation states `y_f_ret` and `y_p_ret`, the
    change committed; answers the copy (unit J's brief, decision J-D11:
    item 4's trellis)."""
    folder = repository_copy(PENSION_RETIREMENT, target / "pension-retirement")
    _rewritten(
        folder / "declaration/trellis.yml",
        "  - {y_f_wk: y_f_w, y_p_wk: y_p_w, y_f_rt: y_f_r, y_p_rt: y_p_r, "
        "y_f_ret: y_f_r, y_p_ret: y_p_r}\n",
        "  - {}\n",
    )
    return _committed(folder, "the inter-period mapping emptied")


# --- unit N, Task 7: the cables' ports and the cable's list (design pass 10 §§6–7) ---

# The cables' ports the region draws on the cards, `.bf-cable-port`: each as
# its `data-port` (`cable_port`), its side, `writing` or `reading`, a
# writing port's branch, whether a wire joins it, whether it is hidden,
# whether a drag starts at it (React Flow's class `connectablestart`), the
# ids of its field ports that no join reaches (`data-unjoined`), the id of
# the card's node, the size on the screen of its press target and the size,
# in the card's own pixels, of the mark its `::before` draws (design pass
# 13 §1, rules 1 and 3).
CABLE_PORTS_JS = """
() => Array.from(document.querySelectorAll('.bl-view-host .bf-card > .react-flow__handle.bf-cable-port'), (port) => {
  const at = port.getBoundingClientRect();
  return {port: port.dataset.port, side: port.dataset.side, branch: port.dataset.branch ?? null,
          joined: port.classList.contains('bf-cable-joined'), hidden: port.classList.contains('bf-cable-hidden'),
          starts: port.classList.contains('connectablestart'), unjoined: (port.dataset.unjoined || '').split(' ').filter(Boolean),
          box: port.closest('.react-flow__node').dataset.id, width: at.width, height: at.height,
          mark: parseFloat(getComputedStyle(port, '::before').width)};
})
"""

# the number of ports the region draws at which a drag starts, React Flow's
# classes `connectable` and `connectablestart` (design pass 10 §7); a
# boundary marker's port, which the page declares not connectable, keeps
# React Flow's default `connectablestart` but takes no pointer
# (`.bf-marker-port` in brand.css), so it starts no drag and is not counted
STARTING_PORTS_JS = (
    "() => document.querySelectorAll("
    "'.bl-view-host .react-flow__handle.connectable.connectablestart').length"
)

# The cable's list, null where none is open (design pass 10 §7): its head,
# each row's arrival field, whether it is ticked, the text of the
# continuation field its select shows and the texts of the select's options,
# the count line's text and whether the button `join` acts.
CABLE_LIST_JS = """
() => {
  const list = document.querySelector('.bl-view-host .bf-pair-list');
  if (!list) return null;
  const count = list.querySelector('.bf-pair-count');
  return {
    head: list.querySelector('.bf-pair-head').textContent,
    rows: Array.from(list.querySelectorAll('.bf-pair-row'), (row) => {
      const select = row.querySelector('select.bf-pair-from');
      return [row.querySelector('span.bf-pair-to').textContent,
              row.querySelector('.bf-pair-tick').checked,
              select.options[select.selectedIndex].textContent,
              Array.from(select.options, (option) => option.textContent)];
    }),
    count: count ? count.textContent : null,
    join: !list.querySelector('.bf-pair-join').disabled,
  };
}
"""


def cable_ports(page) -> list[dict]:
    """The cables' ports the region draws on the cards (CABLE_PORTS_JS)."""
    return page.evaluate(CABLE_PORTS_JS)


def cable_port(page, occurrence: str, side: str, branch: str = "") -> str:
    """The `data-port` of the element of the port the region draws on the
    card of the stage occurrence `occurrence`, `periods[1]/tenure`, on the
    side `side`, `writing` for the port of the branch `branch`, the empty
    text for a stage of no branch, and `reading` for the arrival tuple's
    port (design pass 10 §6): the wire's id in the graph JSON, prefixed
    `in:` for a reading port, or the id of a port of the card's own after
    its occurrence's namespace, `periods[0]/cons/arrival`."""
    from bellman.stage import LAYER_ID_ENDING

    box = occurrence + LAYER_ID_ENDING
    (found,) = [
        port["port"]
        for port in cable_ports(page)
        if port["box"] == box and port["side"] == side and not port["hidden"]
        and (side == "reading" or (port["branch"] or "") == branch)
    ]
    return found


def cable_list(page) -> dict | None:
    """The cable's list as the region draws it, None where none is open
    (CABLE_LIST_JS; design pass 10 §7)."""
    return page.evaluate(CABLE_LIST_JS)


# The ids in the graph JSON of the field ports that no join reaches, as the
# region draws them: the unjoined ports of a closed period's box (J-D47) and
# the fields the cards' cable ports stand for that no join reaches, which
# each port names in `data-unjoined` (design pass 10 §6).
UNJOINED_FIELD_IDS_JS = """
() => {
  const found = Array.from(
    document.querySelectorAll('.bl-view-host .react-flow__handle.bf-unjoined'), (port) => port.dataset.port);
  for (const port of document.querySelectorAll('.bl-view-host .bf-cable-port:not(.bf-cable-hidden)')) {
    for (const id of (port.dataset.unjoined || '').split(' ')) if (id) found.push(id);
  }
  return found;
}
"""


def unjoined_field_ids(page) -> list[str]:
    """The ids, in the graph JSON and in sorted order, of the field ports
    that no join reaches, as the region draws them on the closed boxes and
    on the cards' cable ports (UNJOINED_FIELD_IDS_JS; design pass 10 §6)."""
    return sorted(set(page.evaluate(UNJOINED_FIELD_IDS_JS)))


def drag_cable(page, writing: str, branch: str, reading: str, pairs: dict | None = None) -> dict:
    """A drag by the pointer from the cable port of the branch `branch` of
    the stage occurrence `writing`, `periods[2]/port`, to the arrival port
    of the occurrence `reading`, made as `drag_ports` makes it (design pass
    10 §7). Where `pairs` is given, the cable's list that the drop opens is
    filled: each row named in `pairs`, by the id of its arrival field's
    port, takes the continuation field whose port id `pairs` gives, and
    `join` is pressed. Answers what the region showed while the button was
    held over the arrival port (DRAG_STATE_JS)."""
    state = drag_ports(page, cable_port(page, writing, "writing", branch), cable_port(page, reading, "reading"))
    if pairs:
        wait_until(lambda: cable_list(page), 10.0, "the cable's list")
        for arrival, field in pairs.items():
            row = page.locator(f'.bl-view-host .bf-pair-row[data-port="{arrival}"] select.bf-pair-from')
            row.select_option(value=field)
        page.click(".bl-view-host .bf-pair-join")
        wait_until(lambda: cable_list(page) is None, 5.0, "the cable's list closed")
    return state
