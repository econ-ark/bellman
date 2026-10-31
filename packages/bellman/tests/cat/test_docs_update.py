"""The acceptance file of lane W of the internal developer release 0.01, the
documentation, the tutorials and the wiki brought to the new terminology and
semantics (the second layer of the tests, `packages/bellman/README.md` §8):
one test for each item of the lane's brief, `docs-update.md` §5, that a test
closes.

Item 1 is the sweep for old forms of the release's implementation plan (§3),
read over the pages under `docs/`, the lessons under `tutorials/` with their
outputs, the applications under `applications/` and `AGENTS.md`: every file
git tracks there and every new file git does not ignore. One path is left out:
the changelog, `docs/changelog.md`, a record of what was. The decision
records, which quote the rules of their time (RH200 of the release's
decisions), were left out as well while they stood under `docs/decisions/`;
since 29 September 2026 they stand in the internal folder, outside the scope.
The first test reads every line with the union of the patterns of lanes A, N,
K, C, R and D; the second applies lane P's rule, that every block opening
with a title `STAGE <name>` above a heavy line of `━` is a card the package
prints for the target its title names. The
plan's scope also names the rule files of the internal folder, and its other
exclusions lie in that folder; this sweep leaves it out (PL13 and BN62 of the
release's decisions), and the lane's acceptance sweeps the rule files once by
hand with the patterns below.

Item 2, every lesson executed again and up to date with its record, is closed
by `tutorials/tests/test_lessons.py` once the lane's acceptance has recorded
the lessons with `tutorials/tools/execute_lessons.py --record`. Item 3 is the
strict build of the site and lane D's test of the direction of links, item 4
of `test_docs_shape.py`, with its two allowed lists empty; the second test of
item 3 asserts that both lists are empty.
Item 4 reads every page of `docs/wiki/` against the names of the terminology
table. Items 5 and 6 are readings: each area's `econ-tribe` report in the
lane's build record, and AAS reading the guide's first three pages and one
lesson.

The card rule of item 1 and the strict build of item 3 carry the mark
`sweep`, since the first prints every card of each stage a page shows and the
second builds the whole site; a run given no marker expression leaves them
out, and `-m sweep` runs them.
"""
from __future__ import annotations

import importlib.util
import json
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote

import pytest
import yaml
from conftest import ROOT, stage_from_text
from sheets_parse import sheets_of

from bellman.stage import ElaboratedStage

# --- item 1: the places the sweep reads ---

# the pages, the lessons with their outputs, the applications and the
# project memory; `CLAUDE.md` is a symbolic link to `AGENTS.md`
SCOPE = ("docs", "tutorials", "applications", "AGENTS.md")
# the changelog, a record of what was; the decision records, which quote the
# rules of their time (RH200), stand in the internal folder since 29 September
# 2026, outside the scope, and need no exclusion
LEFT_OUT = ("docs/changelog.md",)

# the old forms, by the lane that retired them: each pattern as the lane's
# acceptance file writes it where that file sweeps the pages, and as the
# plan's §3 writes it otherwise
OLD_FORMS = {
    # the former name of the numerical toolkit, now asva, and its deleted
    # subpackage, each written in two pieces so that lane A's sweep, which
    # reads this file, finds no whole name in it
    "A": re.compile(r"(?<!what-to-do-with-)\bkik" r"ku\b|\bdy" r"nx\b"),
    # the paths and verbs lane N retired; `stage.builder`, `stage.initial`,
    # `stage.par`, `denote()` and `diagram()` answer in their place
    "N": re.compile(
        r"\bstage\.(builders|parameters)\b|\.initial_diagrams\b|\.denotation\(|\.draw\("
        r"|\bdraw_(trellis|period)\b|bindings\.calibration"
    ),
    # the kinds of a policy block's rows that lane K retired
    "K": re.compile(
        r":(Inversion|Solution|Selection)\b|\b(Inversion|Solution|Selection) of the\b"
    ),
    # the count of the spellings of the Kuhn–Tucker condition before lane C,
    # which counts three
    "C": re.compile(r"(?i)\btwo spellings\b"),
    # a path under the internal folder, written in two pieces as lane R's
    # own sweep writes it; `AI/ALL`, the addressee of AAS's notes to every
    # agent, names no path
    "R": re.compile(r"\bAI" r"/(?!ALL\b)"),
    # the pages and folders lane D retired, among them the two its last
    # commit moved into `API/`
    "D": re.compile(
        r"Bellman-Term|reference/primitives\.md|docs/semantics|syntax-API"
        r"|02-the-stage-object"
    ),
}
# for each lane, words of which every line its pattern finds holds at least
# one, lane C's in lower case: a text that holds none of a lane's words is
# not read line by line with that lane's pattern, since the stored encodings
# under `applications/` hold about seventy megabytes of text
CLUES = {
    "A": ("kik" "ku", "dy" "nx"),
    "N": ("stage.builders", "stage.parameters", ".initial_diagrams", ".denotation(", ".draw(",
          "draw_trellis", "draw_period", "bindings.calibration"),
    "K": ("Inversion", "Solution", "Selection"),
    "C": ("two spellings",),
    "R": ("AI" "/",),
    "D": ("Bellman-Term", "reference/primitives.md", "docs/semantics", "syntax-API",
          "02-the-stage-object"),
}
# the files lane R's rule allows to name a path under the internal folder:
# the agents' instructions and the frozen records of the portfolio and
# consumption reference, written when it was captured (PL13, RH60)
MAY_NAME_THE_INTERNAL_FOLDER = ("AGENTS.md", "applications/cons-port/reference/legacy/")

# --- item 1: lane P's rule on the printed cards ---

# a heavy line, which stands under a card's title and at its foot
HEAVY = re.compile(r"━+")
# a calibration, methods or settings file, as a page or a lesson names it by
# its path from the repository root
BINDING_SOURCE = re.compile(
    r"(?<![\w./-])((?:applications|tutorials)/[\w./-]+\.ya?ml)(?![\w/-])"
)
# a key at the top level of such a file, with the value written beside it
TOP_KEY = re.compile(r"^([A-Za-z_]\w*)[ \t]*:[ \t]*(\S*)", re.MULTILINE)
# the binding verbs in their order, each with the top-level key of the
# files it reads
VERBS = (("calibrate", "calibration"), ("methodize", "methods"), ("configure", "settings"))

# --- item 4: the terminology table and the reading of a wiki page ---

# the names of the first column of the terminology table, the text of each
# bold span split at `;` and at ` / `, as the table stood when lane W began
# (`main` at 3e34573cf); the table lies in the internal folder, which no test
# reads (PL13, BN62), so the lane's acceptance compares this list with the
# table by hand, and a row added to the table is added here
TERMS = (
    "BE-DDSL", "DDSL", "dolo-plus", "Dolang+", "ADC", "stage", "stage file",
    "stage occurrence", "stage version", "perch", "field", "evaluated field",
    "intermediate function", "evaluation", "decision value function", "condition",
    "represents", "attaches at", "realises", "state", "initial diagram", "pullback",
    "semgraph", "view", "listing", "sheet", "diagram", "handle", "place", "segment",
    "pack", "grain", "builder at a policy", "coordinate of a block", "value bundle",
    "arvl_states", "dcsn_states", "cntn_states", "period", "trellis", "syntactic trellis",
    "key", "ASDL field", "connector", "source span", "span table", "term address",
    "JSON path", "term JSON encoding", "decoder", "inter-period connector", "block",
    "sub-block", "Bellman-SYM", "Bellman calculus", "Υ (Upsilon)", "Ρ (Rho)", "handler",
    "realiser id", "compiled Dolo model", "denotation", "representation", "mapping",
    "chain", "methodization", "calibration", "stage encoding", "obligation status",
    "refusal catalogue", "builder", "forward builder", "backward builder",
    "backward block", "operator", "primitive operator", "value statement", "line",
    "statement", "rule", "!doc", "Argmax", "property", "node", "sub-builder",
    "sub-transition", "occurrence", "wire", "kernel", "law of motion",
    "value aggregator", "induced aggregator", "shock probability distribution",
    "stochastic kernel", "Markov transition kernel", "argument", "coordinates",
    "value input", "parallel wires", "copy", "branch", "branch tuple", "selection",
    "fork", "label coordinate", "section", "base", "summand", "slice",
    "inputs and outputs", "Bellman operator", "parameters", "settings",
    "specified stage", "spec_factory", "Bellman factory", "native", "elaborated trellis",
    "registry", "recipe", "source", "source list", "slot", "fill", "method choice",
    "sweep", "accrete", "binding maps", "spelling", "complementary slackness",
    "multiplier", "observable", "observable set",
)
# the names the table writes in code: a page uses one where a code span
# holds the name alone
WRITTEN_IN_CODE = frozenset(
    {"!doc", "Argmax", "arvl_states", "dcsn_states", "cntn_states", "native"}
)
# the names of the table that the wiki's pages also write in their ordinary
# sense, which no reading of the text tells apart from the table's sense; the
# perch entry's "make an unobserved shock observable" is an instance; item 4
# reads every name of the table but these
ORDINARY_WORDS = (
    "state", "source", "rule", "line", "key", "place", "section", "base", "copy", "fill",
    "slot", "view", "chain", "mapping", "property", "condition", "argument", "sweep",
    "spelling", "segment", "pack", "slice", "handle", "selection", "fork", "block", "node",
    "occurrence", "evaluation", "coordinates", "represents", "realises", "listing",
    "diagram", "representation", "multiplier", "observable",
)
# the pages that write a name of the table in another sense only, which no
# link can resolve: the semgraph entry names the effect handlers of Plotkin
# and Pretnar (2009), not the numerical routine the table calls a handler; a
# pair that no longer holds fails item 4, so that the list shrinks
OTHER_SENSES = {("wiki/semgraph.md", "handler")}

WIKI = ROOT / "docs" / "wiki"
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
# a fenced block, at the margin or inside a callout
FENCED = re.compile(r"^[ \t>]*(```|~~~).*?^[ \t>]*\1[^\n]*$", re.DOTALL | re.MULTILINE)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
DISPLAYED_MATHEMATICS = re.compile(r"\$\$.*?\$\$", re.DOTALL)
INLINE_MATHEMATICS = re.compile(r"(?<![\\$])\$[^$\n]+\$")
PICTURE = re.compile(r"!\[[^\]\n]*\]\([^)\n]*\)")
WIKILINK = re.compile(
    r"\[\[(?P<target>[^\]|#\n]*)(?:#[^\]|\n]*)?(?:\|(?P<alias>[^\]\n]*))?\]\]"
)
LINK = re.compile(
    r"(?<!!)\[(?P<text>[^\]\n]*)\]\((?P<target><[^>\n]*>|[^)\s]*)(?:\s+\"[^\"]*\")?\)"
)
ADDRESS = re.compile(r"<https?://[^>\s]+>|https?://\S+")
MARKUP = re.compile(r"</?[A-Za-z][^>\n]*>")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")


# --- reading the files of the scope ---


def listed_files(*places):
    """Every file under the repository paths `places` that git tracks or
    would add, by its path from the repository root."""
    listed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard",
         "-z", "--", *places],
        capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    return sorted({name for name in listed if name and (ROOT / name).is_file()})


def swept_files():
    """The files of the sweep's scope, the left-out paths and the symbolic
    links aside."""
    return [name for name in listed_files(*SCOPE)
            if not name.startswith(LEFT_OUT) and not (ROOT / name).is_symlink()]


def _joined(value):
    """A notebook's text, which it stores as one string or as a list of
    lines."""
    return value if isinstance(value, str) else "".join(value)


def texts_of(name):
    """(place, text) of each text a file holds: a lesson's cells and their
    outputs one by one, an output's text, drawing or error, with no picture
    stored as encoded bytes; any other file whole, and nothing of a file that
    holds a NUL byte, which is no text file."""
    data = (ROOT / name).read_bytes()
    if name.endswith(".ipynb"):
        cells = json.loads(data.decode("utf-8")).get("cells", [])
        for number, cell in enumerate(cells):
            yield f"cell {number}", _joined(cell.get("source", ""))
            for output in cell.get("outputs", []):
                if "text" in output:
                    yield f"cell {number}, output", _joined(output["text"])
                for kind, value in output.get("data", {}).items():
                    if kind.startswith("text/") or kind == "image/svg+xml":
                        yield f"cell {number}, output", _joined(value)
                if "traceback" in output:
                    yield f"cell {number}, output", "\n".join(output["traceback"])
    elif b"\0" not in data:
        yield "", data.decode("utf-8", errors="replace")


def where(name, place, number=None):
    """A place in the scope, for a report: the file, the cell of a lesson and
    the line."""
    held = f"{name}, {place}" if place else name
    return held if number is None else f"{held}, line {number}"


def test_item_1_the_pages_lessons_and_applications_hold_no_old_form_of_a_lane():
    """The union of the lanes' patterns of the plan's §3 finds nothing in the
    scope: lane A's, N's, K's, C's and D's in every line, and lane R's in
    every line of a file its rule does not allow to name the internal
    folder."""
    found = []
    for name in swept_files():
        for place, text in texts_of(name):
            lanes = [lane for lane, words in CLUES.items()
                     if any(word in (text.lower() if lane == "C" else text) for word in words)
                     and not (lane == "R" and name.startswith(MAY_NAME_THE_INTERNAL_FOLDER))]
            for number, line in enumerate(text.splitlines() if lanes else (), 1):
                found += [f"{lane}  {where(name, place, number)}: {line.strip()[:120]}"
                          for lane in lanes if OLD_FORMS[lane].search(line)]
    assert not found, f"{len(found)} lines hold an old form:\n" + "\n".join(found)


# --- item 1: lane P's rule on the printed cards ---


def cards_in(text):
    """(title, card) of each block of a text that opens with `STAGE ` at the
    start of a line and has a heavy line within its next three lines: the
    title is the lines above the heavy line, joined by a space, and the card
    runs from the title to the next heavy line, its foot, or to the end of
    the text where no foot follows."""
    lines = text.splitlines()
    for start, line in enumerate(lines):
        if not line.startswith("STAGE "):
            continue
        below = range(start + 1, min(start + 4, len(lines)))
        top = next((k for k in below if HEAVY.fullmatch(lines[k])), None)
        if top is None:
            continue
        after = range(top + 1, len(lines))
        foot = next((k for k in after if HEAVY.fullmatch(lines[k])), len(lines) - 1)
        yield " ".join(lines[start:top]), "\n".join(lines[start : foot + 1])


def stage_files():
    """Every stage file of the applications and of the lessons, by the stage
    name its first line `@stage: <name>` gives; two files may give one
    name."""
    found = {}
    for folder in ("applications", "tutorials"):
        for path in sorted((ROOT / folder).rglob("*.bl")):
            first = path.read_text(encoding="utf-8").split("\n", 1)[0]
            if first.startswith("@stage:"):
                found.setdefault(first.split(":", 1)[1].strip(), []).append(path)
    return found


def binding_sources(texts):
    """The calibration, methods and settings files a page or a lesson names,
    by the top-level key each file writes (`calibration`, `methods`,
    `settings`), each with the stage a methods file names under `stage`."""
    named = sorted({match.group(1) for _, text in texts
                    for match in BINDING_SOURCE.finditer(text)
                    if (ROOT / match.group(1)).is_file()})
    found = {key: [] for _, key in VERBS}
    for path in named:
        keys = dict(TOP_KEY.findall((ROOT / path).read_text(encoding="utf-8")))
        for key in found:
            if key in keys:
                found[key].append((path, keys.get("stage")))
    return found


def bindings_of(stage_name, sources):
    """The bindings the verbs make in their order from the named files: a
    calibration file, then a methods file naming the stage, then a settings
    file, which binds only after methods; each a tuple of (verb, file), the
    empty tuple, the symbolic version, first."""
    calibrations = [None] + [path for path, _ in sources["calibration"]]
    methods = [None] + [path for path, named in sources["methods"] if named == stage_name]
    settings = [path for path, _ in sources["settings"]]
    for calibration in calibrations:
        for method in methods:
            for setting in [None] + (settings if method else []):
                chosen = zip([verb for verb, _ in VERBS], (calibration, method, setting))
                yield tuple((verb, path) for verb, path in chosen if path is not None)


@pytest.mark.sweep
def test_item_1_every_card_shown_on_a_page_or_in_a_lesson_is_one_the_package_prints(
        request, monkeypatch):
    """Lane P's rule: every block of a page or of a lesson, its outputs among
    them, that opens with a title `STAGE <name>` above a heavy line equals a
    card the package prints for the target its title names, on the stage file
    of the applications or the lessons whose first line names the stage, or
    on the stage of the fixture of `conftest.py` with that name, such as
    `cons_argmax`, where no file names it. A title names no bindings, so a
    card is compared with the symbolic version and with each version the
    binding verbs make, in their order, from the calibration, methods and
    settings files the page or the lesson names, as the parameters lesson
    binds `cons`. The verbs read those files by their paths from the
    repository root, as a lesson does after `import checkout`."""
    monkeypatch.chdir(ROOT)
    files = stage_files()
    stages, refused, printed, faults = {}, {}, {}, []

    def stages_named(name):
        """(key, symbolic stage) of each stage the name may denote: a stage
        file giving the name, which the package constructs, or else the
        fixture of that name. A stage file the package refuses prints no
        card; its key and the package's reason are kept in `refused` under
        the name, for the report."""
        if name not in stages:
            stages[name] = []
            for path in files.get(name, []):
                key = path.relative_to(ROOT).as_posix()
                try:
                    stage = stage_from_text(path.read_text(encoding="utf-8"), key)
                except (ValueError, LookupError) as error:
                    refused.setdefault(name, []).append((key, str(error)))
                    continue
                stages[name].append((key, stage))
            if name not in files:
                try:
                    held = request.getfixturevalue(name)
                except pytest.FixtureLookupError:
                    held = None
                if isinstance(held, ElaboratedStage):
                    stages[name].append((f"the fixture {name}", held))
        return stages[name]

    def cards_printed(key, stage, binding):
        """Every sheet that the version of `stage` which `binding` makes
        prints; none where a verb refuses the binding."""
        if (key, binding) not in printed:
            version = stage
            try:
                for verb, path in binding:
                    version = getattr(version, verb)(path)
            except (ValueError, LookupError):
                printed[(key, binding)] = frozenset()
            else:
                sheets = sheets_of(version).values()
                printed[(key, binding)] = frozenset(sheet.rstrip("\n") for sheet in sheets)
        return printed[(key, binding)]

    def first_difference(card, candidates):
        """The first line at which a card differs from the card of the same
        title that the symbolic stage prints, for the report."""
        title = card.split("\n", 1)[0]
        for key, stage in candidates:
            for sheet in cards_printed(key, stage, ()):
                if sheet.split("\n", 1)[0] != title:
                    continue
                held, fresh = card.splitlines(), sheet.splitlines()
                number = next((n for n in range(max(len(held), len(fresh)))
                               if held[n : n + 1] != fresh[n : n + 1]), 0)
                return (f"line {number + 1} reads {''.join(held[number : number + 1])!r} where "
                        f"the package prints {''.join(fresh[number : number + 1])!r}")
        return "the symbolic stage prints no card of this title"

    shown = 0
    for name in swept_files():
        if not name.endswith((".md", ".ipynb")):
            continue
        texts = list(texts_of(name))
        blocks = [(place, title, card) for place, text in texts for title, card in cards_in(text)]
        sources = binding_sources(texts) if blocks else None
        for place, title, card in blocks:
            shown += 1
            stage_name = (title.split() + [""])[1]
            candidates = stages_named(stage_name)
            if not candidates:
                if refused.get(stage_name):
                    faults += [f"{where(name, place)}: '{title}' names the stage of {key}, "
                               f"which the package refuses: {reason}"
                               for key, reason in refused[stage_name]]
                else:
                    faults.append(f"{where(name, place)}: '{title}' names a stage that no "
                                  "stage file and no fixture holds")
                continue
            if not any(card in cards_printed(key, stage, binding) for key, stage in candidates
                       for binding in bindings_of(stage_name, sources)):
                faults.append(f"{where(name, place)}: '{title}' is not a card the package "
                              f"prints; {first_difference(card, candidates)}")
    assert shown > 0, "no printed card was found on a page or in a lesson"
    assert not faults, (f"{len(faults)} of {shown} cards differ from the package's:\n"
                        + "\n".join(faults))


# --- item 3: the strict build ---


@pytest.mark.sweep
def test_item_3_the_site_builds_in_strict_mode(tmp_path):
    """`mkdocs build --strict` builds the site that `mkdocs.yml` at the
    repository root describes, into a folder of the test's own, with no
    warning; the test is skipped where MkDocs is not installed."""
    if importlib.util.find_spec("mkdocs") is None:
        pytest.skip("MkDocs is not installed in this environment")
    run = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--config-file",
         str(ROOT / "mkdocs.yml"), "--site-dir", str(tmp_path / "site")],
        cwd=ROOT, capture_output=True, text=True, timeout=900,
    )
    reported = [line for line in (run.stdout + run.stderr).splitlines()
                if line.startswith(("WARNING", "ERROR"))]
    assert run.returncode == 0, (
        f"the strict build stopped with {len(reported)} warnings and errors:\n"
        + "\n".join(reported or [run.stderr[-3000:]])
    )


def test_item_3_lane_d_test_of_the_direction_of_links_allows_no_link():
    """The second clause of item 3 (question 15): item 4 of
    `test_docs_shape.py`, lane D's test of the direction of links, holds its
    two allowed lists, `BODY_LINKS_TODAY` and `BOX_LINKS_TODAY`, empty."""
    from .test_docs_shape import BODY_LINKS_TODAY, BOX_LINKS_TODAY
    assert (len(BODY_LINKS_TODAY), len(BOX_LINKS_TODAY)) == (0, 0)


# --- item 4: the wiki against the terminology table ---


def label(text):
    """A page's or a name's label for comparison: lower case, with hyphens,
    underscores and runs of spaces read as one space."""
    return re.sub(r"[\s_-]+", " ", text.strip().lower())


def simplified(name):
    """A file name or a wikilink's target as the site's wikilink plugin,
    roamlinks, compares them: lower case, without hyphens, underscores,
    spaces or the suffix `.md`."""
    return re.sub(r"[-_ ]", "", name.lower()).replace(".md", "")


def term_pattern(name):
    """A table name written outside code, as whole words with any spacing
    between them, singular or with a plural ending; read in any case unless
    the name holds a capital after its first letter, as `ADC` and
    `Bellman-SYM` do. A name preceded by `#` is an Obsidian tag, and one
    beside `/` part of a path, neither of them a use."""
    words = r"\s+".join(re.escape(word) for word in name.split())
    flags = 0 if any(letter.isupper() for letter in name[1:]) else re.IGNORECASE
    return re.compile(rf"(?<![\w#/-]){words}(?:s|es)?(?![\w/-])", flags)


# the names read outside code, the longest first, with their patterns
LONGEST_FIRST = sorted(set(TERMS) - WRITTEN_IN_CODE, key=len, reverse=True)
TERM_PATTERNS = {name: term_pattern(name) for name in LONGEST_FIRST}


def written(text):
    """The table's names a text writes outside code, each read at its
    longest: a name inside a longer name of the table, `field` in `ASDL
    field` or `stage` in `stage file`, is part of that name and no use of its
    own; and the names the table writes in code that a code span of the text
    holds alone."""
    found = {span.strip() for span in CODE_SPAN.findall(text)} & WRITTEN_IN_CODE
    text = CODE_SPAN.sub(" ", text)
    for name in LONGEST_FIRST:
        pattern = TERM_PATTERNS[name]
        if pattern.search(text):
            found.add(name)
            text = pattern.sub(lambda match: " " * len(match.group()), text)
    return found


def reading(text):
    """(prose, bold texts, link texts, link targets) of a wiki page. The
    prose is the page without its front matter, fenced blocks, comments,
    mathematics, pictures, web addresses and markup, each link read as its
    text: a wikilink's text is its alias, or its target where it has none. A
    target is ("wiki", the wikilink's target) or ("md", the link's
    address); a link inside a code span is none."""
    body = FRONT_MATTER.sub("", text, count=1)
    for pattern in (FENCED, COMMENT, DISPLAYED_MATHEMATICS, INLINE_MATHEMATICS, PICTURE):
        body = pattern.sub(" ", body)

    def shown(match):
        """A wikilink's text: its alias, or its target where it has none."""
        alias = match.group("alias")
        return alias if alias is not None else match.group("target")

    # each code span blanked to as many spaces as it holds characters, so that
    # a link written inside a code span is none, while a link's text is read
    # from the page with the code spans it holds, `[`Argmax`](…)` among them
    outside_code = CODE_SPAN.sub(lambda match: " " * len(match.group()), body)
    wikilinks, links = list(WIKILINK.finditer(outside_code)), list(LINK.finditer(outside_code))

    def held(match, group):
        """The text of a group of a link, read from the page."""
        return body[match.start(group):match.end(group)]

    texts = [held(match, "alias" if match.group("alias") is not None else "target")
             for match in wikilinks] + [held(match, "text") for match in links]
    targets = [("wiki", match.group("target").strip()) for match in wikilinks]
    targets += [("md", match.group("target").strip("<>")) for match in links]
    body = WIKILINK.sub(lambda match: f" {shown(match)} ", body)
    body = LINK.sub(lambda match: f" {match.group('text')} ", body)
    body = MARKUP.sub(" ", ADDRESS.sub(" ", body))
    # the asterisks inside a code span, as in `load_recipe(directory, recipe,
    # **fills)`, open no bold span
    unstarred = CODE_SPAN.sub(lambda match: match.group().replace("*", " "), body)
    return body, BOLD.findall(unstarred), texts, targets


def reached(page, target, standing):
    """The files under `docs/` that a link of `page`, a path under `docs/`,
    reaches: a wikilink's by its target, as roamlinks resolves it, the file of
    that name wherever it stands or the path a target with a folder names; a
    link's by its relative address, a folder by the files inside it. None for
    a link that needs no file, to a heading of the same page, to another site
    or to an address, and an empty set for a link that reaches nothing."""
    kind, address = target
    if kind == "wiki":
        if not address:
            return None
        if "/" in address:
            named = address if "." in posixpath.basename(address) else address + ".md"
            return {posixpath.normpath(named)} & standing
        return {other for other in standing
                if simplified(posixpath.basename(other)) == simplified(address)}
    if not address or address.startswith("#") or re.match(r"[a-z][a-z0-9+.-]*:", address):
        return None
    relative = unquote(address.split("#")[0])
    path = posixpath.normpath(posixpath.join(posixpath.dirname(page), relative))
    return {other for other in standing if other == path or other.startswith(path + "/")}


def test_item_4_each_wiki_page_defines_or_links_its_terms_and_reaches_only_pages_that_stand():
    """Every page of `docs/wiki/`, its index among them, defines or links each
    name of the terminology table that it uses, and each of its links and
    wikilinks reaches a file that stands under `docs/`, so that none reaches
    a retired page. A page defines a name where it writes the name in bold,
    the mark of a term at its first use (the project's rule on documents,
    `docs-style.md` §1), or where the page is the name's own entry, the page
    whose file name, slug or title reads as the name; it links a name where
    the text of one of its links holds the name or one of its links reaches
    the name's entry. The test reads every name of the table but those of
    `ORDINARY_WORDS`, which the pages also write in their ordinary sense;
    whether one of those is defined where the table's sense is meant is left
    to the reading of item 5. A pair of `OTHER_SENSES`, a page that writes a
    name of the table in another sense only, is passed over, and a pair that
    the page no longer writes is a fault."""
    pages = sorted(WIKI.glob("*.md"))
    entries = {}
    for path in pages:
        found = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        front = (yaml.safe_load(found.group(1)) if found else None) or {}
        labels = {label(path.stem)}
        labels |= {label(str(front.get(key) or "")) for key in ("slug", "title")}
        for name in TERMS:
            if label(name) in labels:
                entries.setdefault(name, f"wiki/{path.name}")
    read = {name for name in TERMS if name not in ORDINARY_WORDS}
    standing = {name[len("docs/"):] for name in listed_files("docs")}
    faults, held_senses = [], set()
    for path in pages:
        page = path.relative_to(ROOT / "docs").as_posix()
        prose, bold, link_texts, targets = reading(path.read_text(encoding="utf-8"))
        defined = set().union(*(written(text) for text in bold))
        linked = set().union(*(written(text) for text in link_texts))
        reaches = {target: reached(page, target, standing) for target in targets}
        linked_pages = set().union(*(files for files in reaches.values() if files))
        for name in sorted(written(prose) & read):
            if (page, name) in OTHER_SENSES:
                held_senses.add((page, name))
                continue
            entry = entries.get(name)
            if entry in (page, *linked_pages) or name in defined or name in linked:
                continue
            faults.append(f"{page}: uses '{name}' and neither defines nor links it")
        faults.extend(f"{page}: the link to '{address}' reaches no file that stands"
                      for (_, address), files in reaches.items() if files == set())
    faults.extend(f"{page} no longer writes '{name}'; delete the pair from OTHER_SENSES"
                  for page, name in sorted(OTHER_SENSES - held_senses))
    assert not faults, f"{len(faults)} faults on the wiki's pages:\n" + "\n".join(faults)
