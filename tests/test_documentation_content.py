"""The pages, lessons and wiki of the documentation: their words, the cards
they show, their links, and the strict build of the site."""

import json
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest
import yaml
from application_files import ROOT, checkout_environment
from documentation_paths import FILES_LEFT_OUT_OF_SEARCHES, FRONT_MATTER, SEARCHED_PLACES, WIKI
from printed_text import sheets_of
from refusal_rules import rules_in_order
from skips import require_package
from stage_builders import stage_from_text

from bellman.native.hypergraphs import copy_native
from bellman.stage import ElaboratedStage

# the internal folder: the development repository holds a folder of notes for
# its developers, which the public repository leaves out. The files that may
# name a path under that folder: the instructions for agents, and the frozen
# records of the reference of the portfolio and consumption model, written
# when that reference was taken
MAY_NAME_THE_INTERNAL_FOLDER = ("AGENTS.md", "applications/cons-port/reference/legacy/")


# each old form that no file of the scope writes, by the id of its row: its
# pattern, and the paths of the files that may write it
OLD_FORMS = {
    # each name is written in two pieces, so that a search of the repository
    # for either name finds none in this file; the name of a page that opens
    # with `what-to-do-with-` is no use of the former name
    "the former name of the numerical toolkit, now asva, and its deleted subpackage": (
        re.compile(r"(?<!what-to-do-with-)\bkik" r"ku\b|\bdy" r"nx\b"),
        (),
    ),
    # `stage.builder`, `stage.initial`, `stage.par`, `denote()` and
    # `diagram()` answer in their place
    "a path or a verb that the stage object no longer answers": (
        re.compile(
            r"\bstage\.(builders|parameters)\b|\.initial_diagrams\b|\.denotation\(|\.draw\("
            r"|\bdraw_(trellis|period)\b|bindings\.calibration"
            r"|\bstage\.build\b|\.build\.(sol|sim)\b|\bBUILD_MEMBERS\b|\bbuilder_named\b"
        ),
        (),
    ),
    # the package now writes each row of a policy block as one of five kinds
    # of operation, `Pullback`, `Aggregation`, `Expectation`, `Argmax` and
    # `Evaluation`
    "a kind of the rows of a policy block that the package no longer writes": (
        re.compile(r":(Inversion|Solution|Selection)\b|\b(Inversion|Solution|Selection) of the\b"),
        (),
    ),
    # the pages count three spellings of the Kuhn–Tucker condition, where an
    # earlier text counted two
    "two spellings of the Kuhn-Tucker condition": (re.compile(r"(?i)\btwo spellings\b"), ()),
    # the name of the folder is written in two pieces, as above; `AI/ALL`,
    # which addresses a note to every agent, names no path
    "a path under the internal folder": (
        re.compile(r"\bAI" r"/(?!ALL\b)"),
        MAY_NAME_THE_INTERNAL_FOLDER,
    ),
    # among them the two pages that now stand in the folder `API/`
    "a page or a folder of the documentation that no longer stands": (
        re.compile(
            r"Bellman-Term|reference/primitives\.md|docs/semantics|syntax-API"
            r"|02-the-stage-object"
        ),
        (),
    ),
}


# a heavy line, which stands under a card's title and at its foot
HEAVY = re.compile(r"━+")


# a calibration, methods or settings file, as a page or a lesson names it by
# its path from the repository root
BINDING_SOURCE = re.compile(
    r"(?<![\w./-])((?:applications|tutorials|declaration)/[\w./-]+\.(?:ya?ml|bl))(?![\w/-])"
)


# a key at the top level of such a file, with the value written beside it
TOP_KEY = re.compile(r"^([A-Za-z_]\w*)[ \t]*:[ \t]*(\S*)", re.MULTILINE)


# the binding verbs in their order, each with the top-level key of the
# files it reads
VERBS = (("methodize", "methods"), ("calibrate", "calibration"), ("configure", "settings"))


# the names of the first column of the terminology table, the text of each
# bold span split at `;` and at ` / `; the table stands in the internal
# folder, which no test reads, so a row added to the table is added here by
# hand
TERMS = (
    "BE-DDSL",
    "DDSL",
    "dolo-plus",
    "Dolang+",
    "ADC",
    "stage",
    "stage file",
    "stage occurrence",
    "stage version",
    "perch",
    "field",
    "evaluated field",
    "intermediate function",
    "evaluation",
    "decision value function",
    "condition",
    "represents",
    "attaches at",
    "realises",
    "state",
    "initial diagram",
    "pullback",
    "semgraph",
    "view",
    "listing",
    "sheet",
    "diagram",
    "handle",
    "place",
    "segment",
    "pack",
    "grain",
    "builder at a policy",
    "coordinate of a block",
    "value bundle",
    "arvl_states",
    "dcsn_states",
    "cntn_states",
    "period",
    "trellis",
    "syntactic trellis",
    "key",
    "ASDL field",
    "connector",
    "source span",
    "span table",
    "term address",
    "JSON path",
    "term JSON encoding",
    "decoder",
    "inter-period connector",
    "block",
    "sub-block",
    "Bellman-SYM",
    "Bellman calculus",
    "Υ (Upsilon)",
    "Ρ (Rho)",
    "handler",
    "realiser id",
    "compiled Dolo model",
    "denotation",
    "representation",
    "mapping",
    "chain",
    "methodization",
    "calibration",
    "stage encoding",
    "obligation status",
    "refusal catalogue",
    "builder",
    "forward builder",
    "backward builder",
    "backward block",
    "operator",
    "primitive operator",
    "value statement",
    "line",
    "statement",
    "rule",
    "!doc",
    "Argmax",
    "property",
    "node",
    "sub-builder",
    "sub-transition",
    "occurrence",
    "wire",
    "kernel",
    "law of motion",
    "value aggregator",
    "induced aggregator",
    "shock probability distribution",
    "stochastic kernel",
    "Markov transition kernel",
    "argument",
    "coordinates",
    "value input",
    "parallel wires",
    "copy",
    "branch",
    "branch tuple",
    "selection",
    "fork",
    "label coordinate",
    "section",
    "base",
    "summand",
    "slice",
    "inputs and outputs",
    "Bellman operator",
    "parameters",
    "settings",
    "specified stage",
    "spec_factory",
    "Bellman factory",
    "native",
    "elaborated trellis",
    "registry",
    "recipe",
    "source",
    "source list",
    "slot",
    "fill",
    "method choice",
    "sweep",
    "accrete",
    "binding maps",
    "spelling",
    "complementary slackness",
    "multiplier",
    "observable",
    "observable set",
)


# the names the table writes in code: a page uses one where a code span
# holds the name alone
WRITTEN_IN_CODE = frozenset(
    {"!doc", "Argmax", "arvl_states", "dcsn_states", "cntn_states", "native"}
)


# the names of the table that the wiki's pages also write in their ordinary
# sense, which no reading of the text tells apart from the table's sense; the
# perch entry's "make an unobserved shock observable" is an instance; the
# test of the wiki's pages reads every name of the table but these
ORDINARY_WORDS = (
    "state",
    "source",
    "rule",
    "line",
    "key",
    "place",
    "section",
    "base",
    "copy",
    "fill",
    "slot",
    "view",
    "chain",
    "mapping",
    "property",
    "condition",
    "argument",
    "sweep",
    "spelling",
    "segment",
    "pack",
    "slice",
    "handle",
    "selection",
    "fork",
    "block",
    "node",
    "occurrence",
    "evaluation",
    "coordinates",
    "represents",
    "realises",
    "listing",
    "diagram",
    "representation",
    "multiplier",
    "observable",
)


# the pages that write a name of the table in another sense only, which no
# link can resolve: the semgraph entry names the effect handlers of Plotkin
# and Pretnar (2009), not the numerical routine the table calls a handler; a
# pair that no longer holds fails the test of the wiki's pages, so that the
# list shrinks
OTHER_SENSES = {("wiki/semgraph.md", "handler")}


# a fenced block, at the margin or inside a callout
FENCED = re.compile(r"^[ \t>]*(```|~~~).*?^[ \t>]*\1[^\n]*$", re.DOTALL | re.MULTILINE)


COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


DISPLAYED_MATHEMATICS = re.compile(r"\$\$.*?\$\$", re.DOTALL)


INLINE_MATHEMATICS = re.compile(r"(?<![\\$])\$[^$\n]+\$")


PICTURE = re.compile(r"!\[[^\]\n]*\]\([^)\n]*\)")


WIKILINK = re.compile(r"\[\[(?P<target>[^\]|#\n]*)(?:#[^\]|\n]*)?(?:\|(?P<alias>[^\]\n]*))?\]\]")


LINK = re.compile(
    r"(?<!!)\[(?P<text>[^\]\n]*)\]\((?P<target><[^>\n]*>|[^)\s]*)(?:\s+\"[^\"]*\")?\)"
)


ADDRESS = re.compile(r"<https?://[^>\s]+>|https?://\S+")


MARKUP = re.compile(r"</?[A-Za-z][^>\n]*>")


CODE_SPAN = re.compile(r"`([^`\n]+)`")


BOLD = re.compile(r"\*\*(.+?)\*\*")


def listed_files(*places):
    """Every file under the repository paths `places`, read from the folders,
    by its path from the repository root, without the folders and files that
    the function's own list below names. The function does not read
    `.gitignore`; its list holds, as far as it goes, what the repository's
    `.gitignore` leaves out under these folders."""
    # each folder left out by its name, with the reason that .gitignore gives
    left_out_folders = {
        "__pycache__",  # the compiled modules that Python writes
        ".ipynb_checkpoints",  # the copies of a notebook that Jupyter writes
        "model-explorer",  # the views that `explore` writes beside a stage file
        "_build",  # what the builder of MyST pages writes
        "site",  # the site that MkDocs builds
        "node_modules",  # the Node packages that npm installs
        ".git",  # the git data of a model folder that is a repository of its own
        "old",  # a folder kept outside git, as is one whose name ends in old_endings
    }
    old_endings = ("-old", "_old", ".old")
    # each file left out by its name or its ending: the folder settings that
    # macOS writes, the compiled modules of Python, the packaged extensions of
    # an editor, the logs that LaTeX writes, the copies that editors keep, and
    # the settings of a MyST build
    left_out_endings = (".DS_Store", ".pyc", ".vsix", ".log", ".bak")
    left_out_names = ("myst.yml",)
    numbered_copy = re.compile(r"\.bak[0-9]$")

    def kept(name):
        parts = name.split("/")
        if any(part in left_out_folders or part.endswith(old_endings) for part in parts[:-1]):
            return False
        # the TeX and PDF files that a MyST build writes into a page's folder
        if parts[0] == "docs" and "exports" in parts[1:-1]:
            return False
        # the model folder that the Workbench's tests write
        if parts[:2] == ["applications", "test"]:
            return False
        # what the code of a model folder writes
        if len(parts) > 3 and parts[0] == "applications" and parts[2] == "results":
            return False
        file = parts[-1]
        return not (
            file.endswith(left_out_endings) or file in left_out_names or numbered_copy.search(file)
        )

    found = set()
    for place in places:
        if (ROOT / place).is_file():
            found.add(place)
        for folder, folders, files in os.walk(ROOT / place):
            # a folder left out by its name is not read at all
            folders[:] = [
                name
                for name in folders
                if name not in left_out_folders and not name.endswith(old_endings)
            ]
            found.update((Path(folder) / file).relative_to(ROOT).as_posix() for file in files)
    return sorted(name for name in found if kept(name) and (ROOT / name).is_file())


def swept_files():
    """The files of `SEARCHED_PLACES`, apart from those of
    `FILES_LEFT_OUT_OF_SEARCHES` and the symbolic links."""
    return [
        name
        for name in listed_files(*SEARCHED_PLACES)
        if not name.startswith(FILES_LEFT_OUT_OF_SEARCHES) and not (ROOT / name).is_symlink()
    ]


def joined(value):
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
            yield f"cell {number}", joined(cell.get("source", ""))
            for output in cell.get("outputs", []):
                if "text" in output:
                    yield f"cell {number}, output", joined(output["text"])
                for kind, value in output.get("data", {}).items():
                    if kind.startswith("text/") or kind == "image/svg+xml":
                        yield f"cell {number}, output", joined(value)
                if "traceback" in output:
                    yield f"cell {number}, output", "\n".join(output["traceback"])
    elif b"\0" not in data:
        yield "", data.decode("utf-8", errors="replace")


def where(name, place, number=None):
    """A place in the scope, for a report: the file, the cell of a lesson and
    the line."""
    held = f"{name}, {place}" if place else name
    return held if number is None else f"{held}, line {number}"


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


def binding_sources(texts, document):
    """The calibration, methods and settings files a page or a lesson names,
    by the top-level key each file writes (`calibration`, `methods`,
    `settings`), each with the stage a methods file names under `stage`."""
    named = set()
    for _, text in texts:
        for match in BINDING_SOURCE.finditer(text):
            path = match.group(1)
            if path.startswith("declaration/") and document.startswith("applications/"):
                path = "/".join(document.split("/")[:2]) + "/" + path
            if (ROOT / path).is_file():
                named.add(path)
    found = {key: [] for _, key in VERBS}
    for path in sorted(named):
        text = (ROOT / path).read_text(encoding="utf-8")
        if path.endswith(".bl"):
            header = re.search(r"^@methods:\s*(\w+)\s*$", text, re.MULTILINE)
            if header:
                found["methods"].append((path, header.group(1)))
            continue
        keys = dict(TOP_KEY.findall(text))
        for key in found:
            if key in keys:
                found[key].append((path, keys.get("stage")))
    return found


def bindings_of(stage_name, sources):
    """The bindings the verbs make in their order from the named files: a
    methods file naming the stage, then a calibration file, then a settings
    file, which binds only after methods; each a tuple of (verb, file), the
    empty tuple, the symbolic version, first."""
    calibrations = [None] + [path for path, _ in sources["calibration"]]
    methods = [None] + [path for path, named in sources["methods"] if named == stage_name]
    settings = [path for path, _ in sources["settings"]]
    for calibration in calibrations:
        for method in methods:
            for setting in [None] + (settings if method else []):
                chosen = zip([verb for verb, _ in VERBS], (method, calibration, setting))
                yield tuple((verb, path) for verb, path in chosen if path is not None)


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
        return body[match.start(group) : match.end(group)]

    texts = [
        held(match, "alias" if match.group("alias") is not None else "target")
        for match in wikilinks
    ] + [held(match, "text") for match in links]
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
        return {
            other
            for other in standing
            if simplified(posixpath.basename(other)) == simplified(address)
        }
    if not address or address.startswith("#") or re.match(r"[a-z][a-z0-9+.-]*:", address):
        return None
    relative = unquote(address.split("#")[0])
    path = posixpath.normpath(posixpath.join(posixpath.dirname(page), relative))
    return {other for other in standing if other == path or other.startswith(path + "/")}


def stages_named(name, files, request):
    """(key, symbolic stage) of each stage that the title of a card may name,
    and (key, reason) of each stage file of that name that the package
    refuses: the stage of each stage file of `files` whose first line names
    the stage, or, where no stage file names it, the stage of the shared
    fixture of that name, such as `cons_argmax`; a name that is no fixture
    gives no stage."""
    stages, refused = [], []
    for path in files.get(name, []):
        key = path.relative_to(ROOT).as_posix()
        try:
            stage = stage_from_text(path.read_text(encoding="utf-8"), key)
        except (ValueError, LookupError) as error:
            refused.append((key, str(error)))
            continue
        stages.append((key, stage))
    if name not in files:
        try:
            held = request.getfixturevalue(name)
        except pytest.FixtureLookupError:
            held = None
        if isinstance(held, ElaboratedStage):
            stages.append((f"the fixture {name}", held))
    return stages, refused


def cards_printed(key, stage, binding, printed):
    """Every sheet that the version of `stage` which `binding` makes prints,
    kept in `printed` under (key, binding); none where a verb refuses the
    binding. A version that binds is made from a copy of the stage."""
    if (key, binding) not in printed:
        version = copy_native(stage) if binding else stage
        try:
            for verb, path in binding:
                version = getattr(version, verb)(path)
        except (ValueError, LookupError):
            printed[(key, binding)] = frozenset()
        else:
            sheets = sheets_of(version).values()
            printed[(key, binding)] = frozenset(sheet.rstrip("\n") for sheet in sheets)
    return printed[(key, binding)]


def first_difference(card, candidates, printed):
    """The first line at which a card differs from the card of the same
    title that the symbolic stage prints, for the report."""
    title = card.split("\n", 1)[0]
    for key, stage in candidates:
        for sheet in cards_printed(key, stage, (), printed):
            if sheet.split("\n", 1)[0] != title:
                continue
            held, fresh = card.splitlines(), sheet.splitlines()
            number = next(
                (
                    n
                    for n in range(max(len(held), len(fresh)))
                    if held[n : n + 1] != fresh[n : n + 1]
                ),
                0,
            )
            return (
                f"line {number + 1} reads {''.join(held[number : number + 1])!r} where "
                f"the package prints {''.join(fresh[number : number + 1])!r}"
            )
    return "the symbolic stage prints no card of this title"


@pytest.fixture(scope="module")
def swept_texts():
    """(file, place, text) of each text of the files of `SEARCHED_PLACES` that
    `swept_files` gives, a lesson's cells and outputs one by one."""
    return [(name, place, text) for name in swept_files() for place, text in texts_of(name)]


@pytest.mark.parametrize(("pattern", "allowed"), OLD_FORMS.values(), ids=OLD_FORMS)
def test_no_page_lesson_or_application_writes_an_old_form(swept_texts, pattern, allowed):
    """No line of the pages, the lessons with their outputs, the applications
    or AGENTS.md writes the old form of the row, apart from the files that
    the row allows to write it."""
    # the first 120 characters of a line identify it in the report
    found = [
        f"{where(name, place, number)}: {line.strip()[:120]}"
        for name, place, text in swept_texts
        if not name.startswith(allowed) and pattern.search(text)
        for number, line in enumerate(text.splitlines(), 1)
        if pattern.search(line)
    ]
    assert not found, f"{len(found)} lines hold an old form:\n" + "\n".join(found)


@pytest.mark.complete_set
def test_every_card_shown_on_a_page_or_in_a_lesson_is_one_that_the_package_prints(
    request, monkeypatch
):
    """Every block of a page or of a lesson, its outputs among them, that
    opens with a title `STAGE <name>` above a heavy line is a card that the
    package prints for the stage of that name."""
    # the binding verbs read the files that a page names by their paths from
    # the repository root, as a lesson does after `import checkout`
    monkeypatch.chdir(ROOT)
    files = stage_files()
    stages_by_name, printed, faults, shown = {}, {}, [], 0
    for name in swept_files():
        if not name.endswith((".md", ".ipynb")):
            continue
        texts = list(texts_of(name))
        blocks = [(place, title, card) for place, text in texts for title, card in cards_in(text)]
        sources = binding_sources(texts, name) if blocks else None
        for place, title, card in blocks:
            shown += 1
            stage_name = (title.split() + [""])[1]
            if stage_name not in stages_by_name:
                stages_by_name[stage_name] = stages_named(stage_name, files, request)
            candidates, refused = stages_by_name[stage_name]
            # a card of a stage that no stage file and no fixture holds is a
            # fault that the test reports, and so is a card of a stage whose
            # stage file the package refuses
            if not candidates:
                if refused:
                    faults += [
                        f"{where(name, place)}: '{title}' names the stage of {key}, "
                        f"which the package refuses: {reason}"
                        for key, reason in refused
                    ]
                else:
                    faults.append(
                        f"{where(name, place)}: '{title}' names a stage that no "
                        "stage file and no fixture holds"
                    )
                continue
            # a title names no bindings, so the card is compared with the
            # symbolic version and with each version that the binding verbs
            # make, in their order, from the calibration, methods and settings
            # files that the page names, as the parameters lesson binds `cons`
            if not any(
                card in cards_printed(key, stage, binding, printed)
                for key, stage in candidates
                for binding in bindings_of(stage_name, sources)
            ):
                faults.append(
                    f"{where(name, place)}: '{title}' is not a card the package "
                    f"prints; {first_difference(card, candidates, printed)}"
                )
    assert shown > 0, "no printed card was found on a page or in a lesson"
    differ = f"{len(faults)} of {shown} cards differ from the package's:\n" + "\n".join(faults)
    assert not faults, differ


@pytest.fixture(scope="module")
def strict_site(tmp_path_factory):
    """The documentation site that `mkdocs build --strict` builds from the root
    of the repository into a new folder: the finished process and the
    folder."""
    # the test is skipped where MkDocs is not installed
    require_package("mkdocs", extra="docs")
    site = tmp_path_factory.mktemp("built") / "site"
    built = subprocess.run(
        [
            sys.executable,
            "-m",
            "mkdocs",
            "build",
            "--strict",
            "--config-file",
            str(ROOT / "mkdocs.yml"),
            "--site-dir",
            str(site),
        ],
        cwd=ROOT,
        env=checkout_environment(),
        capture_output=True,
        text=True,
        # a build that runs for fifteen minutes is stopped
        timeout=900,
    )
    return built, site


@pytest.mark.complete_set
def test_mkdocs_builds_the_site_under_the_strict_option(strict_site):
    """`mkdocs build --strict`, which stops at any warning, builds the site
    that `mkdocs.yml` at the repository root describes into a new folder."""
    run, _ = strict_site
    reported = [
        line
        for line in (run.stdout + run.stderr).splitlines()
        if line.startswith(("WARNING", "ERROR"))
    ]
    # where no line opens with WARNING or ERROR, the report shows the last
    # 3,000 characters of the error output
    assert run.returncode == 0, (
        f"the strict build stopped with {len(reported)} warnings and errors:\n"
        + "\n".join(reported or [run.stderr[-3000:]])
    )


@pytest.mark.complete_set
def test_the_refusals_page_of_the_built_site_holds_an_anchor_for_every_rule(
    strict_site,
):
    """The Refusals page of the built site, which the Rule link of the
    Workbench opens, holds an anchor for every rule of the three
    vocabularies."""
    _, site = strict_site
    html = (site / "Bellman-Sym" / "reference" / "refusals" / "index.html").read_text(
        encoding="utf-8"
    )
    assert [rule for rule in rules_in_order() if f'id="{rule}"' not in html] == []


def test_the_test_of_links_from_the_calculus_into_the_language_allows_no_further_link():
    """The two lists of `tests/test_documentation_structure.py` that allow a
    link from a page of the calculus into a page of the language outside the
    lines `Builds on` and `Used by`, one for the body of a page and one for
    its intro box, are empty."""
    from test_documentation_structure import BODY_LINKS_TODAY, BOX_LINKS_TODAY

    assert (len(BODY_LINKS_TODAY), len(BOX_LINKS_TODAY)) == (0, 0)


@pytest.mark.xfail(
    strict=True,
    reason="The test expects each page of `docs/wiki/` to define or link each name of `TERMS` "
    "that it uses. Today several of its pages use such names without defining or linking "
    "them.",
)
def test_each_wiki_page_defines_or_links_its_terms_and_reaches_only_pages_that_stand():
    """Each page of `docs/wiki/`, its index among them, defines or links each
    name of `TERMS` that it uses, apart from the names of `ORDINARY_WORDS`
    and the pairs of `OTHER_SENSES`, and each of its links and wikilinks
    reaches a file that stands under `docs/`."""
    pages = sorted(WIKI.glob("*.md"))
    # the entry of a name is the page whose file name, slug or title reads as
    # the name
    entries = {}
    for path in pages:
        found = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        front = (yaml.safe_load(found.group(1)) if found else None) or {}
        labels = {label(path.stem)}
        labels |= {label(str(front.get(key) or "")) for key in ("slug", "title")}
        for name in TERMS:
            if label(name) in labels:
                entries.setdefault(name, f"wiki/{path.name}")
    # the names of ORDINARY_WORDS, which the pages also write in their
    # ordinary sense, are not read; whether one of them is defined where the
    # sense of the table is meant is left to a person who reads the pages
    read = {name for name in TERMS if name not in ORDINARY_WORDS}
    standing = {name[len("docs/") :] for name in listed_files("docs")}
    faults, held_senses = [], set()
    for path in pages:
        page = path.relative_to(ROOT / "docs").as_posix()
        prose, bold, link_texts, targets = reading(path.read_text(encoding="utf-8"))
        # a page defines a name where it writes the name in bold, the mark of
        # a term at its first use, or where the page is the name's entry; it
        # links a name where the text of one of its links holds the name, or
        # where one of its links reaches the name's entry
        defined = set().union(*(written(text) for text in bold))
        linked = set().union(*(written(text) for text in link_texts))
        reaches = {target: reached(page, target, standing) for target in targets}
        linked_pages = set().union(*(files for files in reaches.values() if files))
        for name in sorted(written(prose) & read):
            # a pair of OTHER_SENSES, a page that writes a name of the table
            # in another sense only, is passed over
            if (page, name) in OTHER_SENSES:
                held_senses.add((page, name))
                continue
            entry = entries.get(name)
            if entry in (page, *linked_pages) or name in defined or name in linked:
                continue
            faults.append(f"{page}: uses '{name}' and neither defines nor links it")
        # a link that reaches no file that stands, such as a link to a retired
        # page, is a fault
        faults.extend(
            f"{page}: the link to '{address}' reaches no file that stands"
            for (_, address), files in reaches.items()
            if files == set()
        )
    # a pair of OTHER_SENSES that its page no longer writes is a fault, so
    # that the list shrinks
    faults.extend(
        f"{page} no longer writes '{name}'; delete the pair from OTHER_SENSES"
        for page, name in sorted(OTHER_SENSES - held_senses)
    )
    assert not faults, f"{len(faults)} faults on the wiki's pages:\n" + "\n".join(faults)
