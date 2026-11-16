"""Write the table of each reference page from the package's own table.

A reference page under `docs/Bellman-Sym/reference/` is written by hand around
one table, and the index of the API, `docs/Bellman-Sym/API/index.md`, around
four, each under its heading. The tables stand between the two markers

    <!-- reference-table -->
    <!-- /reference-table -->

and this script writes them from the tables the package holds, so that the
prose of the page is kept and no table is edited by hand:

- `reference/operations.md`: the operations of `PRIMITIVE_DEFINITIONS`
  (`typing/primitive_definitions.py`), the entries its module docstring
  names under "Contract", each with its defining expression and a row of that
  kind on a stage file under `applications/`: the lines that form the row,
  the builder that holds it, at the key of `stage.builder` that reads it,
  what it reads and writes, and its rule as the row's card prints it;
- `reference/laws.md`: the shock families of `FAMILY_ARGUMENTS`
  (`distributions/families.py`), each with the arguments the table gives and
  the meaning the module docstring states;
- `reference/forms.md`: the operators a stage file writes with a subscript,
  `BOUND_OPERATORS` (`typing/line_unknowns.py`), the named functions of
  `PRIMITIVE_DEFINITIONS`, the arithmetic of the grammar
  (`syntax/grammars/stage.lark`) and the laws;
- `reference/methods.md`: one entry for each method word of `METHOD_TYPES`
  (`stage/method_table.py`, whose rows stand in `stage/method_rows.py`),
  the representation families of `stage/representations.py` and those
  registered later included, and one for each grid constructor of
  `GRID_CONSTRUCTORS` (`stage/grids.py`), each printed from its record and
  its `EntryText`: the meaning, the declaration and its sites, the type
  parameters, the arguments, the compatibility, for a representation family
  the data a fitted representation stores, an example, the
  availability and the links, with an index of the methods by the place
  they stand at and an index of the grid constructors; this part of the
  page holds its section headings;
- `reference/refusals.md`: the rules of the three vocabularies of
  `refusals.py`, `VOCABULARIES` of `refusal_catalogue.py`, one table per
  vocabulary, each rule with the operation that refuses under it and the
  claim its comment states, as the catalogue answers them;
- `reference/rules.md`: the rows of `SEMANTIC_RULES`
  (`bellman/semantic_rules.py`), one table for each of the sections 2.1 to
  2.5 and of the rules R1 to R12 of the syntax-to-semantics appendix under
  the appendix's own headings, each rule with the functions that implement
  it and check it, its refusals and a test; then a sentence that links the
  table of the rules that the package does not yet check, which the
  appendix holds; then the refusal rules of `RULES_STATED_ELSEWHERE` with
  the pages that state them; this part of the page holds its section
  headings;
- `appendices/14-appendix-c-syntax-to-semantics.md`: the table of its
  section 5.3, one row for each rule that the package does not yet check,
  from the rows of `SEMANTIC_RULES` with `checked` false and from
  `UNCHECKED_ELSEWHERE`: the sections that the rule concerns, the rule and
  the other pages that state it; what the package does today; and the
  smallest text that shows it;
- `reference/types.md`: six tables, each under its heading: the objects of
  a stage, from `OBJECTS` (`typing/type_table.py`); the role words, the
  perch words with their marks and the reserved sets, from `ROLE_WORD`,
  `PERCH_WORD`, `WRITTEN_MARK` and `PRIMITIVE_SETS`
  (`syntax/vocabulary.py`); the forms of a set expression, from
  `SET_FORMS`; and the limits of the language on a type, from `LIMITS`,
  each with a line that breaks it and the rule of its refusal;
- `API/index.md`: every public name of `bellman.stage`, `bellman.period` and
  `bellman.trellis`, in one table per namespace, then the stage object. The
  functions of `bellman.stage` are printed on the corpus stage `cons`, those
  of `bellman.period` and `bellman.trellis` on the trellis file of the
  portfolio-consumption application, and the two that read a recipe on the
  durables registry; the tables of the namespaces also hold the method
  table, the three perch words and the constants of the view in Model
  Explorer. The table of the stage object holds the stage itself and every
  public attribute and verb of the handles of `stage/pieces.py` and
  `stage/elaborated.py`, with their readings by a key and by an attribute,
  and one row for each pair of perches by which `stage.builder` reads a
  builder, printed on `cons` calibrated, methodized and configured by the
  files of `docs/Bellman-Sym/API/stage/09-binding-verbs.md` §1. Each row
  holds the first sentence of its docstring, the type it answers and what
  it prints; a field of a handle, like a reading by a key that has no
  docstring, takes the first sentence of the docstring of the class it
  answers, where the package defines that class, and a constant whose class
  the package does not define takes the first sentence of the comment above
  the line that assigns it.

A row of a reference page names its object and gives three columns beside it:
`written`, how a stage file or a methods file writes it; `denotes`, a link to
the section of Appendix E.3 of the Bellman calculus
(`docs/bellman-calculus/catalogues/operators.md`) that defines the abstract
object it realizes, or a dash where E.3 defines no such object; and
`read from`, the module, the table and the key. The section is found by the
name E.3 gives the object, in the first cell of one of its table rows or else
in a heading (`calculus_term`); a name E.3 does not give leaves the cell a
dash and is reported, and the tests of `tests/test_documentation_structure.py` fail on
it where the row must link.

Run from the repository root with the project interpreter:

    PYTHONPATH=packages/bellman python docs/_hooks/reference_pages.py
    PYTHONPATH=packages/bellman python docs/_hooks/reference_pages.py --check

The first rewrites every table; `--check` reports the tables that differ and
writes nothing. `--page` names one page. `--source-ref` names the exported
revision of `econ-ark/bellman` at which the methods page and the rules page
link each definition, `EXPORTED_REVISION` by default; the generator refuses
a revision whose file does not hold the definition, and without a revision
each entry of the methods page shows the definition's location in the
checkout with its public link stated unavailable, and the rules page names
each function by its module and its qualified name and states the public
links unavailable once. The release that exports the definitions sets
`EXPORTED_REVISION` and regenerates the two pages, the script and the pages
committed together, so that `--check` agrees with the pages. Every page
is written or checked through `settle` of `stage_object_page.py`, the one
printer of the pages the package prints.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import dataclasses
import functools
import importlib
import inspect
import os
import posixpath
import re
import sys
import tempfile
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))

from markdown.extensions.toc import slugify  # noqa: E402  (the anchors MkDocs gives headings)
from stage_object_page import ROOT, settle  # noqa: E402  (the printer beside this script)

# the one listing of the stage files of the applications, `STAGE_FILES` of the
# package tests' module application_files.py
TESTS = ROOT / "packages/bellman/tests"
if str(TESTS) not in sys.path:
    sys.path.append(str(TESTS))
from application_files import STAGE_FILES  # noqa: E402

import bellman.period  # noqa: E402
import bellman.stage  # noqa: E402
import bellman.trellis  # noqa: E402
from bellman.period import (  # noqa: E402
    backward_order,
    computable_together,
    diagram_period,
    forward_order,
    forward_record,
    period_joins,
)
from bellman.stage import (  # noqa: E402
    LAYER_ID_ENDING,
    admitted_methods,
    bind_stage,
    box_attributes,
    branches,
    card_sections,
    elaborate_stage,
    elaborate_text,
    graph_refusal,
    header_fields,
    header_line,
    header_of,
    layers_to_open,
    load_stage,
    make_stage,
    node_place,
    perch_overlays,
    source_lines,
    source_spans,
    to_model_explorer,
    typing_entries,
    wire_counts,
    write_typing_entry,
)
from bellman.trellis import (  # noqa: E402
    accrete,
    append_to_mapping,
    append_to_sequence,
    assemble_trellis,
    calibrate_trellis,
    changed_positions,
    configure_trellis,
    connection_report,
    connector_entry,
    derivative_missing,
    diagram_trellis,
    elaborate_trellis,
    entry_span,
    entry_value,
    explore,
    insert_in_sequence,
    inter_period_joins,
    load_recipe,
    load_trellis,
    read_trellis_file,
    methodize_trellis,
    period_entries,
    pull_back,
    remove_from_mapping,
    remove_from_sequence,
    replace_entry,
    respecify_trellis,
    specify_trellis,
    split_entry,
    transport_atoms,
    transport_hessian,
    transport_point,
    transport_vector,
    trellis_selection,
    unjoined_fields,
    unpaired_joins,
    write_model_explorer,
    written_at,
    written_spans,
)

# the three namespaces of the public names, in the order of the API index
NAMESPACES = (bellman.stage, bellman.period, bellman.trellis)

from bellman.display.cards import WORDS as CARD_WORDS  # noqa: E402
from bellman.distributions import families  # noqa: E402
from bellman.distributions.families import FAMILY_ARGUMENTS  # noqa: E402
from bellman.fold.table import KINDS  # noqa: E402
from bellman.refusal_catalogue import VOCABULARIES, claims, operation  # noqa: E402
from bellman.refusals import METHOD_CONDITIONS, ConstructionError, FactoryError  # noqa: E402
from bellman.semantic_rules import (  # noqa: E402
    APPENDIX,
    RULES_STATED_ELSEWHERE,
    SEMANTIC_RULES,
    UNCHECKED_ELSEWHERE,
    resolve,
)
from bellman.stage import elaborated, pieces  # noqa: E402
from bellman.stage.builder_pairs import DIRECTION_WORDS  # noqa: E402
from bellman.display.cards import grid_sentence  # noqa: E402
from bellman.native.records import NO_REGISTERED_ARGUMENTS, OMISSIONS  # noqa: E402
from bellman.stage.grids import GRID_CONSTRUCTORS, HANDLER, PREDICATES  # noqa: E402
from bellman.stage.method_table import METHOD_TYPES  # noqa: E402
from bellman.stage.representations import families as registered_families  # noqa: E402
from bellman.syntax import terms as T  # noqa: E402
from bellman.syntax.lower import parse_with_spans  # noqa: E402
from bellman.syntax.source import to_source  # noqa: E402
from bellman.syntax.vocabulary import (  # noqa: E402
    MULTIPLIER,
    PERCH_WORD,
    PERCHES,
    PRIMITIVE_SETS,
    ROLE_WORD,
    WRITTEN_MARK,
)
from bellman.syntax.walk import nodes  # noqa: E402
from bellman.typing import primitive_definitions  # noqa: E402
from bellman.typing.line_unknowns import BOUND_OPERATORS, OPERATOR_MEANINGS  # noqa: E402
from bellman.typing.primitive_definitions import PRIMITIVE_DEFINITIONS  # noqa: E402
from bellman.typing.type_table import LIMITS, OBJECTS, SET_FORMS, WITH_A_SET  # noqa: E402
from bellman.typing.typed_expressions import format_expression  # noqa: E402

# the package the script imports, whose sources it reads
PACKAGE = Path(bellman.__file__).resolve().parent

# the two markers between which a page holds its generated table
MARKERS = ("<!-- reference-table -->", "<!-- /reference-table -->")

# Appendix E.3 of the Bellman calculus, the catalogue of operators
E3 = "docs/bellman-calculus/catalogues/operators.md"

OPERATIONS = "docs/Bellman-Sym/reference/operations.md"
LAWS = "docs/Bellman-Sym/reference/laws.md"
FORMS = "docs/Bellman-Sym/reference/forms.md"
METHODS = "docs/Bellman-Sym/reference/methods.md"
REFUSALS = "docs/Bellman-Sym/reference/refusals.md"
RULES_PAGE = "docs/Bellman-Sym/reference/rules.md"
APPENDIX_PAGE = "docs/" + APPENDIX
TYPES_PAGE = "docs/Bellman-Sym/reference/types.md"
API_INDEX = "docs/Bellman-Sym/API/index.md"

# the corpus stage of the API index and its three binding files, the files
# docs/Bellman-Sym/API/stage/09-binding-verbs.md §1 binds: the methods file
# is the addition beside the stage file, unioned with it by `methodize`
CONS = "applications/portfolio-choice/declaration/stages/cons/cons.bl"
CALIBRATION = "applications/portfolio-choice/declaration/calibration/portfolio.yml"
METHODS_FILE = "applications/portfolio-choice/declaration/stages/cons/methods.bl"
SETTINGS = "applications/portfolio-choice/declaration/settings/cons.yml"
# the portfolio stage of the site's running example, the second stage file of
# the corpus; its maximization is marked `!doc`, a line that reads no wire,
# which the consumption stage does not write, since its method lines stand
# in its addition
PORT = "applications/portfolio-choice/declaration/stages/port/port.bl"
# the trellis file on which the API index prints the functions of a trellis and
# of a period, and the registry and the recipe on which it prints the two
# functions that read a recipe. These examples use the variant without
# the tenure stage.
TRELLIS = "applications/cons-port/declaration/trellis.port-cons-vfi.yml"
REGISTRY = "applications/durables/declaration"
RECIPE = "spec.two-stages.yml"

# the link to a line of the package's source in the public repository, at
# an exported revision that holds the definition (`EXPORTED_REVISION`)
SOURCE = "https://github.com/econ-ark/bellman/blob/{ref}/{path}#L{line}"

NONE = "—"

# The name Appendix E.3 gives the abstract object that an operator head of a
# stage file realizes, or a method bound at an occurrence of that head. E.3
# defines no object for `exp`, `log`, `min`, `Inv` or the arithmetic, whose
# rows name no section.
HEAD_TERMS = {
    "E": "Expectation",
    "argmax": "Argmax",
    "solve": "Implicit solution",
    "D": "Differentiation",
    "max": r"\max_J",
    "evaluate": "Evaluation",
    "upper_env": "Envelope selection",
}
# an operation of PRIMITIVE_DEFINITIONS that is no kind of a row, by the name
# E.3 gives the object it defines: the relation read by every row whose
# output is its own unknown is E.3's implicit solution
OPERATION_TERMS = {"Relation": "Implicit solution"}
# a shock's law is the measure the expectation integrates against
LAW_TERM = "Expectation"


# --- the cells of a table ---


# the characters a `<code>` element writes as character references: those of
# HTML, the pipe that would end a table's cell, and those Markdown reads as
# its own marks
CODE_REFERENCES = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "|": "&#124;",
    "`": "&#96;",
    "*": "&#42;",
    "_": "&#95;",
    "\\": "&#92;",
}


def code(text):
    """A code span of `text` on one line, its runs of white space one space.
    A text that holds two opening brackets is written as a `<code>` element
    whose second bracket is the character reference `&#91;`, since the
    site's wikilink plugin reads `[[` as a wikilink even inside a code span
    and warns, which fails the strict build; the page shows the same
    characters."""
    text = " ".join(str(text).split())
    if "[[" in text:
        written = "".join(CODE_REFERENCES.get(char, char) for char in text)
        return "<code>" + written.replace("[[", "[&#91;") + "</code>"
    fence = "``" if "`" in text else "`"
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def prose(text):
    """Prose for a cell, on one line, with a pipe outside a code span escaped;
    a pipe inside a code span stays as it is, as the table reads it."""
    text = " ".join(str(text).split())
    parts = re.split(r"(`[^`]*`)", text)
    return "".join(part if part.startswith("`") else part.replace("|", r"\|") for part in parts)


def anchor_of(key):
    """The anchor of a row: its key in lower case, the words of a
    capitalized name and every other character but letters and digits one
    hyphen, `PolicyInsertion` as `policy-insertion`."""
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", key)
    return re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")


def anchored(key, shown):
    """The first cell of a row: its anchor, then what it shows."""
    return f'<a id="{anchor_of(key)}"></a>{shown}'


def read_from(module, table, key=None):
    """The `read from` cell: the module, the table and, for an entry, its key
    in double quotes."""
    cell = f"{code(module)}, {code(table)}"
    return cell if key is None else f"{cell}, {code(chr(34) + key + chr(34))}"


def table(head, rows):
    """The markdown table of `rows` under `head`."""
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


# --- the sections of Appendix E.3 ---


@dataclasses.dataclass(frozen=True)
class Section:
    """One section of Appendix E.3: its anchor, its heading, and the first cell
    of each row of its tables."""

    anchor: str
    heading: str
    first_cells: tuple


def table_cells(line):
    """The cells of a markdown table row, split at each pipe that stands
    outside a code span and is not escaped; None for a line that is no row
    and for the rule under a table's head."""
    stripped = line.strip()
    if not stripped.startswith("|") or re.fullmatch(r"\|[\s:|-]*\|?", stripped):
        return None
    cells, cell, in_code = [], "", False
    index = 1
    while index < len(stripped):
        char = stripped[index]
        if char == "\\" and index + 1 < len(stripped) and stripped[index + 1] == "|":
            cell += "|"
            index += 2
            continue
        if char == "`":
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append(cell.strip())
            cell = ""
        else:
            cell += char
        index += 1
    if cell.strip():
        cells.append(cell.strip())
    return cells


def calculus_sections(text):
    """The sections of Appendix E.3 in page order. A section's anchor is the
    id of the `<a id>` line that stands just above its heading, or else the
    id MkDocs gives the heading."""
    sections, anchor, heading, cells, fenced = [], None, None, [], False
    pending = None
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        found = re.fullmatch(r'\s*<a id="([^"]+)"></a>\s*', line)
        if found:
            pending = found.group(1)
            continue
        titled = re.match(r"(#{2,6})\s+(.*\S)", line)
        if titled:
            if heading is not None:
                sections.append(Section(anchor, heading, tuple(cells)))
            heading = titled.group(2)
            anchor = pending or slugify(heading, "-")
            cells, pending = [], None
            continue
        if line.strip():
            pending = None
        row = table_cells(line)
        if row and heading is not None:
            cells.append(row[0])
    if heading is not None:
        sections.append(Section(anchor, heading, tuple(cells)))
    return sections


def names(cell, term):
    """Whether a cell names `term` as a whole word, a code span or emphasis
    around it read as the word itself."""
    plain = cell.replace("`", "").replace("*", "")
    return re.search(r"(?<![\w\\])" + re.escape(term) + r"(?!\w)", plain) is not None


@functools.cache
def calculus():
    """The sections of Appendix E.3 as the repository holds it."""
    return tuple(calculus_sections((ROOT / E3).read_text(encoding="utf-8")))


def calculus_term(term):
    """The section of E.3 that names `term` in the first cell of one of its
    table rows, or else in its heading; None where E.3 names it nowhere."""
    for section in calculus():
        if any(names(cell, term) for cell in section.first_cells):
            return section
    for section in calculus():
        if names(section.heading, term):
            return section
    return None


UNRESOLVED = []  # the names E.3 does not give, reported by `main`


def denotes(page, *terms):
    """The `denotes` cell of a row on `page`: a link to the section of E.3 each
    term names, or a dash for a row that names no term."""
    links = []
    for term in terms:
        section = calculus_term(term)
        if section is None:
            UNRESOLVED.append((page, term))
            continue
        numbered = re.match(r"(\d+)\.\s*(.*)", section.heading)
        label = (
            f"E.3 §{numbered.group(1)} {numbered.group(2)}"
            if numbered
            else f"E.3 {section.heading}"
        )
        target = posixpath.relpath(E3, posixpath.dirname(page))
        links.append(f"[{prose(label)}]({target}#{section.anchor})")
    return "<br>".join(links) or NONE


# --- the corpus: every stage file of the applications ---


def corpus_files():
    """The stage files under `applications/`, as `STAGE_FILES` lists them,
    the stage files of the site's running example first, `cons.bl` and
    `port.bl`, the rest by path."""
    first = [CONS, PORT]
    rest = [path.relative_to(ROOT).as_posix() for path in STAGE_FILES]
    return first + [path for path in rest if path not in first]


@functools.cache
def doc_line_stage():
    """The symbolic stage of `port.bl`, on which the API index prints the
    rows of a line that reads no wire, its maximization marked `!doc`."""
    return elaborate_stage(load_stage(PORT))


@functools.cache
def corpus():
    """(path, stage) for every stage file of the corpus that elaborates, in
    the order of `corpus_files`; a file the package refuses forms nothing."""
    stages = []
    for path in corpus_files():
        try:
            stages.append((path, elaborate_stage(load_stage(path))))
        except (ConstructionError, FactoryError):
            continue
    return tuple(stages)


def cited_lines(card):
    """The lines an operation realizes, as its card quotes them under
    `Source` and in the card's order (`bellman.stage.source_lines`):
    each authored line its kernel cites, on one line and without its
    annotation. A pullback's card quotes the law of motion it composes along,
    an expectation's the line it stands in and the law of its shock, and an
    Evaluation's the derivative lines its builder states."""
    clause = getattr(card, "kernel", None)
    held = {}
    for statement in getattr(clause, "statements", ()):
        path, _, number = statement.position.rpartition(":")
        if number.isdigit():
            held[(posixpath.basename(path), int(number))] = statement.text
    return [
        " ".join(held[line].partition("::")[0].split())
        for line in source_lines(card)
        if line in held
    ]


def signature_lines(signature):
    """The printed lines of a signature, a wrapped line joined to the one it
    continues."""
    lines = []
    for line in str(signature).splitlines():
        if line[:1].isspace() and lines:
            lines[-1] += " " + line.strip()
        elif line.strip():
            lines.append(line.strip())
    return lines


def rule_block(card):
    """The lines of the rule block of a printed card, as the card prints
    them, each without its indentation. The block opens at the line that
    starts at column zero with the card's word for it, `WORDS["rule"]` of
    `display/cards.py`, and holds what follows the word on that line and
    every indented line after it, up to the first line that is blank or
    starts at column zero: a rule across the card or the next block."""
    lines = str(card).splitlines()
    word = CARD_WORDS["rule"]
    for index, line in enumerate(lines):
        if line[:1].isspace() or line.split(maxsplit=1)[:1] != [word]:
            continue
        rest = line[len(word) :].strip()
        held = [rest] if rest else []
        for following in lines[index + 1 :]:
            if not following.strip() or not following[:1].isspace():
                break
            held.append(following.strip())
        return held
    return []


def builder_path(stage, identity):
    """The path of the way in to the builder at whose block the box of
    `identity` is rooted. The path reads the builder at its key of
    `stage.builder`: `stage.builder["cntn", "dcsn"]`, or
    `stage.builder.policy` for the policy builder. `key_suffix` writes the
    key, as it does for the rows of the API index. The path is empty where no
    key, or more than one, reads such a builder. A pair that two or more
    builders join is no key of `stage.builder`. A row of one of those
    builders therefore names no path."""
    held = [
        "stage.builder" + key_suffix(stage.builder, key)
        for key in stage.builder
        if identity.key_within(stage.builder[key].box.name) is not None
    ]
    return held[0] if len(held) == 1 else ""


@dataclasses.dataclass(frozen=True)
class Example:
    """A row of one kind on a stage file of the corpus: the file, the box that
    realizes it, the path of the builder that holds it, the lines its card
    quotes under `Source`, its signature and the lines of the rule its card
    prints."""

    path: str
    box: str
    builder: str
    lines: tuple
    signature: tuple
    rule: tuple


@functools.cache
def corpus_examples():
    """The first row of each kind on the corpus, by kind, the backward
    builders of a file before its forward builders, each builders graph read
    by the word of its direction in `DIRECTION_WORDS`, `stage.builder.bwd`
    and `stage.builder.fwd`."""
    found = {}
    for path, stage in corpus():
        for direction in ("backward", "forward"):
            try:
                graph = getattr(stage.builder, DIRECTION_WORDS[direction]).primitives
                boxes = list(graph.list())
            except ConstructionError:  # a graph the construction refused holds no row
                continue
            for name in boxes:
                handle = graph[str(name)]
                identity = getattr(handle.box, "identity", None)
                kind = getattr(identity, "kind", None)
                if kind is None or kind in found:
                    continue
                card = handle.denote()
                found[kind] = Example(
                    path=path,
                    box=str(name),
                    builder=builder_path(stage, identity),
                    lines=tuple(cited_lines(card)),
                    signature=tuple(signature_lines(handle.signature())),
                    rule=tuple(rule_block(card)),
                )
    return found


# --- the operations: PRIMITIVE_DEFINITIONS ---


def contract_names():
    """The names the docstring of `typing/primitive_definitions.py` lists
    under "Contract" as the primitive operator names with their free
    declarations, in the order it lists them."""
    doc = primitive_definitions.__doc__
    opening = re.search(r"The primitive names\s+and their free declarations\s+are:", doc)
    if opening is None:
        raise SystemExit(
            "the docstring of typing/primitive_definitions.py no longer lists the primitive "
            "names and their free declarations under Contract"
        )
    listed, started = [], False
    for line in doc[opening.end() :].splitlines()[1:]:
        if not line.strip():
            if started:
                break
            continue
        started = True
        if line.lstrip().startswith("*"):
            listed += re.findall(r"(?:\*\s+|;\s*)([A-Z][A-Za-z]*):", line)
    return listed


def rule_of(definition):
    """The defining expression of a primitive definition, on one line."""
    return format_expression(definition.equations[0], width=10_000)


def operations_table(page):
    """The table of the operations page: one row for each operation of
    `PRIMITIVE_DEFINITIONS` the contract names, in the table's order, with
    whether it is a kind of a card's row (`KINDS` of `fold/table.py`); the
    lines the card of the first row of that kind on the corpus quotes under
    `Source`, with the row, its file and the builder that holds it; what the
    row reads and writes and its
    rule, as its card prints them; and the operation's defining expression,
    under `definition`."""
    definitions = PRIMITIVE_DEFINITIONS["definitions"]
    listed = set(contract_names())
    examples = corpus_examples()
    rows = []
    for name, definition in definitions.items():
        if name not in listed:
            continue
        example = examples.get(name)
        if example is None:
            written = "no stage file under `applications/` forms a row of this kind"
            signature = rule = NONE
        else:
            place = f"{code(example.box)} of {code(example.path)}"
            if example.builder:
                place += f", in the builder {code(example.builder)}"
            written = "<br>".join([code(line) for line in example.lines] + [place])
            signature = "<br>".join(code(line) for line in example.signature)
            rule = "<br>".join(code(line) for line in example.rule) or NONE
        term = name if calculus_term(name) is not None else OPERATION_TERMS.get(name, name)
        rows.append(
            (
                anchored(name, code(name)),
                "yes" if name in KINDS else "no",
                written,
                signature,
                rule,
                code(rule_of(definition)),
                denotes(page, term),
                read_from(
                    "typing/primitive_definitions.py", 'PRIMITIVE_DEFINITIONS["definitions"]', name
                ),
            )
        )
    head = (
        "operation",
        "kind of a row",
        "written",
        "reads and writes",
        "rule",
        "definition",
        "denotes",
        "read from",
    )
    return table(head, rows)


# --- the laws: FAMILY_ARGUMENTS ---


def family_clauses():
    """The clauses of the docstring of `distributions/families.py`, each
    under every family whose call it spells: `N(μ, v)` has variance `v`, and
    so on."""
    text = " ".join(families.__doc__.split())
    clauses = [
        clause.strip() for clause in re.split(r";\s+|\.\s+(?=[A-Z`])|\.$", text) if clause.strip()
    ]
    said = {}
    for clause in clauses:
        for family in FAMILY_ARGUMENTS:
            if re.search(r"`" + re.escape(family) + r"\(", clause):
                said.setdefault(family, []).append(clause)
    return said


def spellings(family, clauses):
    """The calls of `family` the clauses spell, each once, in their order."""
    found = []
    for clause in clauses:
        for spelled in re.findall(r"`(" + re.escape(family) + r"\([^`]*)`", clause):
            if spelled not in found:
                found.append(spelled)
    return found


def laws_table(page):
    """The table of the laws page: one row for each family of
    `FAMILY_ARGUMENTS`, with its calls as the module docstring spells them,
    the arguments the table gives, the meaning the docstring states and, for
    a family `PRIMITIVE_DEFINITIONS` defines, its defining expression."""
    said = family_clauses()
    definitions = PRIMITIVE_DEFINITIONS["definitions"]
    rows = []
    for family, shape in FAMILY_ARGUMENTS.items():
        if family not in said:
            raise SystemExit(
                f"the docstring of distributions/families.py states no meaning of the family "
                f"{family!r}, which FAMILY_ARGUMENTS admits; state it there"
            )
        clauses = said[family]
        sources = [read_from("distributions/families.py", "FAMILY_ARGUMENTS", family)]
        if family in definitions:
            sources.append(
                read_from(
                    "typing/primitive_definitions.py",
                    'PRIMITIVE_DEFINITIONS["definitions"]',
                    family,
                )
            )
        rows.append(
            (
                anchored(family, code(family)),
                "<br>".join(code(spelled) for spelled in spellings(family, clauses)),
                prose(f"{shape.in_words()}: {shape.named}"),
                prose("; ".join(clauses)),
                code(rule_of(definitions[family])) if family in definitions else NONE,
                denotes(page, LAW_TERM),
                "<br>".join(sources),
            )
        )
    head = ("law", "written", "arguments", "meaning", "definition", "denotes", "read from")
    return table(head, rows)


# --- the forms: BOUND_OPERATORS, the named functions, the arithmetic ---


def spells(node, head, subscripted):
    """Whether a term is an operator `head` written with a subscript, or a
    call of the function `head`."""
    if subscripted:
        return isinstance(node, T.Operator) and node.head == head
    return isinstance(node, T.Call) and node.fun == head


def first_spelling(head, subscripted):
    """The first spelling on the corpus of an operator `head` written with a
    subscript, or of a call of the function `head`, as the source printer
    writes it, with the file; None where no stage file writes it. A term the
    printer cannot write, one whose names the construction has resolved, is
    passed over."""
    for path, stage in corpus():
        for record in stage.definitions.values():
            if not record.equations:
                continue
            for node in nodes(record.equations[0]):
                if not spells(node, head, subscripted):
                    continue
                try:
                    return to_source(node), path
                except (TypeError, NotImplementedError):
                    continue
    return None


def written_form(head, subscripted):
    """The `written` cell of a form: its first spelling on the corpus with the
    file, or the words that no stage file writes it."""
    found = first_spelling(head, subscripted)
    if found is None:
        return "no stage file under `applications/` writes it"
    spelled, path = found
    return f"{code(spelled)}<br>in {code(path)}"


def grammar_signs():
    """The signs of the arithmetic the grammar admits, read from the rules
    `sum`, `product` and `molecule` of `syntax/grammars/stage.lark` and the
    terminal of the power, `_POW`, with the name each alternative gives its
    tree."""
    grammar = (PACKAGE / "syntax/grammars/stage.lark").read_text(encoding="utf-8")
    signs, named = [], []
    for rule in ("?sum", "?product", "?molecule", "_POW"):
        matched = re.search(
            r"^" + re.escape(rule) + r"(?:\{[^\n{}]+\})?\s*:(.*?)(?=^\S|\Z)",
            grammar,
            re.M | re.S,
        )
        if matched is None:
            raise SystemExit(f"syntax/grammars/stage.lark has no arithmetic rule {rule}")
        body = matched.group(1)
        for sign in re.findall(r'"([^"]+)"', body):
            if sign not in signs:
                signs.append(sign)
        for alias in re.findall(r"->\s*(\w+)", body):
            if alias not in named:
                named.append(alias)
    return signs, named


def forms_table(page):
    """The table of the forms page: one row for each operator a stage file
    writes with a subscript (`BOUND_OPERATORS`), for each named function of
    `PRIMITIVE_DEFINITIONS` that is neither an operation nor a law, for the
    arithmetic of the grammar and for the laws, each with its first spelling
    on the corpus."""
    definitions = PRIMITIVE_DEFINITIONS["definitions"]
    operations = set(contract_names())
    rows = []
    for head in BOUND_OPERATORS:
        definition = definitions.get(head)
        meaning = [prose(OPERATOR_MEANINGS[head])] if head in OPERATOR_MEANINGS else []
        sources = [read_from("typing/line_unknowns.py", "BOUND_OPERATORS", head)]
        if definition is not None:
            meaning.append(code(rule_of(definition)))
            sources.append(
                read_from(
                    "typing/primitive_definitions.py", 'PRIMITIVE_DEFINITIONS["definitions"]', head
                )
            )
        rows.append(
            (
                anchored(head, code(head)),
                written_form(head, True),
                "<br>".join(meaning) or NONE,
                denotes(page, *([HEAD_TERMS[head]] if head in HEAD_TERMS else [])),
                "<br>".join(sources),
            )
        )
    for name, definition in definitions.items():
        if name in operations or name in FAMILY_ARGUMENTS or name in BOUND_OPERATORS:
            continue
        rows.append(
            (
                anchored(name, code(name)),
                written_form(name, False),
                code(rule_of(definition)),
                denotes(page, *([HEAD_TERMS[name]] if name in HEAD_TERMS else [])),
                read_from(
                    "typing/primitive_definitions.py", 'PRIMITIVE_DEFINITIONS["definitions"]', name
                ),
            )
        )
    signs, named = grammar_signs()
    rows.append(
        (
            anchored("arithmetic", "arithmetic"),
            " ".join(code(sign) for sign in signs),
            prose(", ".join(named)),
            NONE,
            f"{code('syntax/grammars/stage.lark')}, the rules {code('sum')}, {code('product')}, "
            f"{code('molecule')} and {code('_POW')}",
        )
    )
    said = family_clauses()
    shown = [spellings(family, said.get(family, ()))[:1] for family in FAMILY_ARGUMENTS]
    rows.append(
        (
            anchored("laws", "laws"),
            " ".join(code(spelled[0]) for spelled in shown if spelled),
            prose(
                "the law of a shock, written after `~` in its declaration; each family, its "
                "arguments and its meaning stand on"
            )
            + " [the laws page](laws.md)",
            NONE,
            read_from("distributions/families.py", "FAMILY_ARGUMENTS"),
        )
    )
    head = ("form", "written", "meaning", "denotes", "read from")
    return table(head, rows)


# --- the methods and the grid constructors: METHOD_TYPES and
# GRID_CONSTRUCTORS ---

# The revision of the public repository `econ-ark/bellman` whose files hold
# the definitions the methods page and the rules page link. No exported
# revision holds the definitions of this build, so the methods page shows
# each definition's location in the checkout and both pages state the public
# links unavailable; the release that exports them names its revision here,
# or with `--source-ref`, and the generator then links each definition at
# the line that revision holds, refusing a revision that does not hold it.
EXPORTED_REVISION = None

# the folder of the package's modules from the repository's root, which a
# source location of the package leaves out
PACKAGE_FOLDER = "packages/bellman/bellman/"

# the sentence of a definition that no exported revision holds
NO_PUBLIC_LINK = "public link unavailable until an exported revision holds the definition"

# the module of the table that holds a record whose `EntryText.source` is
# None: a row of the method table, a registered representation family and a
# grid constructor
TABLE_MODULES = {
    "row": "bellman.stage.method_rows",
    "family": "bellman.stage.representations",
    "grid": "bellman.stage.grids",
}

# the words of the kinds of place, as `stage.places()` prints them
SITE_WORDS = {
    "builder": "a whole builder",
    "node": "a line marked `!node`",
    "statement": "a line with an id",
    "definition": "a defined function",
}

# the anchors the page kept from its earlier layout, each above the heading
# that took its place
RETAINED_ANCHORS = {"2 The methods": "2-the-table"}


@dataclasses.dataclass(frozen=True)
class SourceLocation:
    """Where a method or a grid constructor is defined: `module`, the path of
    its module from the repository's root; `definition`, the name of the
    module-level statement that holds the defining call; `line`, the line of
    that call in the checkout; and `revision`, the exported revision whose
    file holds the definition at `public_line`, or None where no exported
    revision is identified."""

    module: str
    definition: str
    line: int
    revision: str | None = None
    public_line: int | None = None


def module_path(dotted):
    """The path from the repository's root of the module `dotted`, a module of
    the package or of a registered extension, read from the module the
    interpreter holds; a module outside the repository is refused."""
    module = sys.modules.get(dotted) or importlib.import_module(dotted)
    held = Path(module.__file__).resolve()
    if not held.is_relative_to(ROOT):
        raise SystemExit(f"the definition's module {dotted} lies outside the repository")
    return held.relative_to(ROOT).as_posix()


def defining_call(source, word, term=None):
    """(the name of the module-level statement or function, the line) of the
    call that defines `word` in the text `source`: a call whose first argument
    is the word, or, for a grid constructor, the entry of the term class
    `term` in a module-level mapping; None where the text holds neither."""
    for statement in ast.parse(source).body:
        if isinstance(statement, ast.Assign):
            name = statement.targets[0].id if isinstance(statement.targets[0], ast.Name) else None
        elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            func = statement.value.func
            name = func.id if isinstance(func, ast.Name) else None
        elif isinstance(statement, ast.FunctionDef):
            name = statement.name
        else:
            continue
        for node in ast.walk(statement):
            if term is not None and isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Attribute) and key.attr == term.__name__:
                        return name, key.lineno
            if (
                term is None
                and isinstance(node, ast.Call)
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == word
            ):
                return name, node.lineno
    return None


def exported_source(revision, module):
    """The text of a module at an exported revision, or None where the
    repository holds no such revision or file. A revision whose tree holds
    the internal folder is a commit of the development repository and
    no export, whose commits hold the toolkit alone, so it is refused."""
    import subprocess

    def shown(spec):
        run = subprocess.run(
            ["git", "show", spec], cwd=str(ROOT), capture_output=True, text=True
        )
        return run.stdout if run.returncode == 0 else None

    if shown(f"{revision}:AI") is not None:
        raise SystemExit(
            f"the revision {revision} holds the internal folder, so it is no exported "
            "revision; a private commit is never linked as public"
        )
    return shown(f"{revision}:{module}")


def source_location(word, record, kind, revision=EXPORTED_REVISION):
    """The `SourceLocation` of a method or a grid constructor, read from its
    record: the module its `EntryText.source` names, or the module of the
    table that holds it, and the call in that module that defines it, so that
    a family registered from another module is found in that module. With an
    exported revision, the definition must stand in that revision's file."""
    text = record.text
    dotted = (text.source if text is not None else None) or TABLE_MODULES[kind]
    module = module_path(dotted)
    term = record.term if kind == "grid" else None
    found = defining_call((ROOT / module).read_text(encoding="utf-8"), word, term)
    if found is None:
        raise SystemExit(f"{dotted} holds no definition of !{word}")
    definition, line = found
    if revision is None:
        return SourceLocation(module, definition, line)
    held = exported_source(revision, module)
    public = defining_call(held, word, term) if held is not None else None
    if public is None:
        raise SystemExit(
            f"the exported revision {revision} holds no definition of !{word} in {module}; "
            "name a revision that holds it, or none"
        )
    return SourceLocation(module, definition, line, revision, public[1])


def source_sentence(location):
    """The source part of an entry: the module, the definition and the line in
    the checkout, then the public link at the exported revision, or the
    sentence that it is unavailable."""
    shown = location.module.removeprefix(PACKAGE_FOLDER)
    where = f"{code(shown)}, {code(location.definition)}, line {location.line}"
    if location.revision is None:
        return f"{where}; {NO_PUBLIC_LINK}"
    link = SOURCE.format(ref=location.revision, path=location.module, line=location.public_line)
    return f"{where}; [public source at {location.revision[:12]}]({link})"


def realized(row):
    """The name in E.3 of what a method type realizes: the object of the
    first operator its admitted places name. A method whose admitted places
    name no operator, such as `!deterministic`, is bound on a whole builder,
    and the method table does not state whether that builder is backward or
    forward, so its entry links no section."""
    for place in row["admits"]:
        if isinstance(place, tuple) and place[1] in HEAD_TERMS:
            return (HEAD_TERMS[place[1]],)
    return ()


def written_word(word):
    """A word as a stage file writes it, a hyphen written as an underscore."""
    return word.replace("-", "_")


def site_phrase(place):
    """An admitted kind of place in words: the occurrences of an operator by
    its head, or the kind of place."""
    if isinstance(place, tuple):
        return f"an occurrence of the operator {code(place[1])}"
    return SITE_WORDS[place]


def joined(items):
    """Items as a sentence lists them, the last after `and`."""
    items = list(items)
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def definition_link(page, definition):
    """A link from `page` to a formal definition written relative to the
    folder `docs/`."""
    target = posixpath.relpath("docs/" + definition, posixpath.dirname(page))
    return f"[formal definition]({target})"


def entry_link(word):
    """A link to the entry of a method or of a grid constructor on the same
    page."""
    if word not in METHOD_TYPES and word not in GRID_CONSTRUCTORS:
        raise SystemExit(f"an entry names the related word !{word}, which no record holds")
    return f"[{code('!' + word)}](#{anchor_of(word)})"


def argument_rows(arguments):
    """The rows of an argument table: each argument's name, the kind of value
    it takes, what leaving it out means, its restrictions and what it is."""
    rows = []
    for name, option in arguments.items():
        omission = OMISSIONS[option.omission]
        if option.default_by is not None:
            omission += f" The default is {option.default!r}, defined by {option.default_by}."
        rows.append(
            (
                code(name),
                prose(option.kind),
                prose(omission),
                prose("; ".join(option.conditions)) if option.conditions else "none",
                prose(option.description) or "none",
            )
        )
    return rows


ARGUMENT_HEAD = ("argument", "type", "when left out", "restrictions", "meaning")


def arguments_part(arguments, retained=True):
    """The arguments part of an entry: the table of the registered arguments
    with the policy for an unlisted keyword, or the sentence of an empty
    record."""
    if not arguments:
        return [f"**Arguments.** {NO_REGISTERED_ARGUMENTS}"]
    lines = ["**Arguments.**", "", table(ARGUMENT_HEAD, argument_rows(arguments)).rstrip()]
    if retained:
        lines += ["", "A keyword the record does not list is retained for the numerical handler."]
    return lines


def type_parameters_part(text):
    """The type parameters of an entry, labeled apart from the arguments, each
    with whether the attachment site supplies it."""
    if text is None or not text.type_parameters:
        return ["**Type parameters.** None."]
    held = [
        f"{code(parameter.name)} is "
        f"{'inferred from the attachment site' if parameter.inferred else 'written at the site'}. "
        f"{prose(parameter.meaning)}"
        for parameter in text.type_parameters
    ]
    return ["**Type parameters.** " + " ".join(held) + " A type parameter is no source keyword."]


def example_part(text):
    """The example of an entry: the declaration in a block, then its
    meaning."""
    return ["**Example.**", "", "```text", text.example, "```", "", prose(text.example_meaning)]


def grid_readers(row):
    """The grid constructors whose sites admit the grid a method row reads."""
    return [word for word, record in GRID_CONSTRUCTORS.items() if row.grid in record.sites.readers]


def stored_part(family):
    """The stored-data part of the entry of a registered representation
    family: the sentence of its record, `RepresentationFamily.stored`, that
    states the data a fitted representation stores."""
    return ["**Stored data.** " + prose(family.stored), ""]


def method_entry(page, number, word, row, revision):
    """The entry of one method word: its meaning, declaration, type
    parameters, arguments, compatibility, for a registered representation
    family the data a fitted representation stores, then the example,
    availability and links."""
    text = row.text
    if text is None:
        raise SystemExit(f"the method row !{word} carries no EntryText")
    held = registered_families().get(word)
    family = held is not None
    location = source_location(word, row, "family" if family else "row", revision)
    sites = joined(site_phrase(place) for place in row["admits"])
    compatibility = []
    if row.grid is not None:
        constructors = joined(entry_link(name) for name in grid_readers(row))
        compatibility.append(
            f"Its grid lies {prose(grid_sentence(row.grid))}; the grid constructors its place "
            f"admits are {constructors}."
        )
    else:
        compatibility.append("It reads no grid.")
    if row.evaluates:
        compatibility.append(f"The derivatives it evaluates are {prose(row.evaluates)}.")
    if row.condition:
        compatibility.append(
            f"The obligation {code(row.condition)} states that "
            f"{prose(METHOD_CONDITIONS[row.condition])}."
        )
    compatibility.append(prose(text.compatibility))
    admission = (
        "a registered representation family; registration alone establishes no numerical support"
        if family
        else "a row of the method table"
    )
    links = [definition_link(page, text.definition)]
    realized_terms = realized(row)
    if realized_terms:
        links.append(f"denotes {denotes(page, *realized_terms)}")
    if text.related:
        links.append("related entries " + joined(entry_link(name) for name in text.related))
    links.append("source " + source_sentence(location))
    links.append("read from " + read_from("stage/method_table.py", "METHOD_TYPES", word))
    lines = [
        f'<a id="{anchor_of(word)}"></a>',
        "",
        f"### 2.{number} {code('!' + word)}",
        "",
        prose(text.meaning),
        "",
        f"**Declaration.** {code(f'<place>.method : !{written_word(word)}')}, at {sites}.",
        "",
        *type_parameters_part(text),
        "",
        *arguments_part(row["keywords"]),
        "",
        "**Compatibility.** " + " ".join(compatibility),
        "",
        *(stored_part(held) if family else ()),
        *example_part(text),
        "",
        f"**Availability.** Admission: {admission}, admitted at {sites}. "
        f"Numerical implementation: {prose(text.implementation)}",
        "",
        "**Links.** " + "; ".join(links) + ".",
    ]
    return "\n".join(lines)


def operator_index():
    """The index of the methods by the place they stand at: each operator head
    and each other kind of place, with the methods admitted there."""
    by_site = {}
    for word, row in METHOD_TYPES.items():
        for place in row["admits"]:
            key = f"operator {code(place[1])}" if isinstance(place, tuple) else SITE_WORDS[place]
            by_site.setdefault(key, []).append(entry_link(word))
    ordered = sorted(by_site, key=lambda key: (not key.startswith("operator"), key))
    return table(("site", "methods"), [(key, ", ".join(by_site[key])) for key in ordered])


def factor_rows(record):
    """The rows of the factor forms of `!Cartesian`: the form, its meaning and
    its parts."""
    rows = []
    for form in record.forms:
        parts = "<br>".join(
            f"{code(name)}: {prose(option.kind)}, {prose(OMISSIONS[option.omission])}"
            for name, option in form.arguments.items()
        )
        rows.append((code(form.written), prose(form.meaning), parts))
    return rows


def grid_readers_phrase(record):
    """The places at which a grid constructor may stand, from its sites: the
    method words whose row's grid is among its readers, and a place with no
    method word where the readers hold the handler."""
    words = [word for word, row in METHOD_TYPES.items() if row.grid in record.sites.readers]
    phrase = "at the grid of " + joined(entry_link(word) for word in words)
    if HANDLER in record.sites.readers:
        phrase += ", and at a place whose entries name no method word, for its handler"
    return phrase


def grid_entry(page, number, word, record, revision):
    """The entry of one grid constructor: its meaning, declaration, type
    parameters, arguments, factor forms, compatibility, example,
    availability and links."""
    text = record.text
    location = source_location(word, record, "grid", revision)
    declaration = "<br>".join(code(form) for form in record.syntax)
    lines = [
        f'<a id="{anchor_of(word)}"></a>',
        "",
        f"### 3.{number} {code('!' + word)}",
        "",
        prose(text.meaning),
        "",
        f"**Declaration.** {declaration}; {grid_readers_phrase(record)}. "
        f"{prose(record.sites.condition)} The predicate words of `require` are written last.",
        "",
        *type_parameters_part(text),
        "",
        *arguments_part(record.arguments, retained=False),
    ]
    if record.forms:
        lines += [
            "",
            "**Factor forms.** Each factor takes one of these forms:",
            "",
            table(("form", "meaning", "parts"), factor_rows(record)).rstrip(),
        ]
    lines += [
        "",
        f"**Compatibility.** {prose(text.compatibility)}",
        "",
        *example_part(text),
        "",
        "**Availability.** Admission: a grid constructor of the language, admitted by the "
        f"lowering and the grid checks. Numerical implementation: {prose(text.implementation)}",
        "",
        "**Links.** "
        + "; ".join(
            [
                definition_link(page, text.definition),
                "related entries " + joined(entry_link(name) for name in text.related),
                "source " + source_sentence(location),
                "read from " + read_from("stage/grids.py", "GRID_CONSTRUCTORS", word),
            ]
        )
        + ".",
    ]
    return "\n".join(lines)


def grid_index():
    """The index of the grid constructors: each with its declaration forms."""
    rows = [
        (entry_link(word), "<br>".join(code(form) for form in record.syntax))
        for word, record in GRID_CONSTRUCTORS.items()
    ]
    return table(("constructor", "declaration"), rows)


def predicate_rows():
    """The predicate words a grid may require, each with its meaning."""
    return [(code("!" + word), prose(meaning)) for word, meaning in PREDICATES.items()]


def methods_table(page, source_ref=EXPORTED_REVISION):
    """The generated part of the methods page: the index of the methods by
    the place they stand at, one entry for each method word of
    `METHOD_TYPES`, registered representation families included, in the
    table's order, then the grid section with the index of the grid
    constructors, the predicate words and one entry for each constructor of
    `GRID_CONSTRUCTORS`, each entry printed from its record and its
    `EntryText` alone."""
    parts = [
        f'<a id="{RETAINED_ANCHORS["2 The methods"]}"></a>',
        "",
        "## 2 The methods",
        "",
        "Each method stands at the places this index names; the entries follow it in the "
        "order of the method table.",
        "",
        operator_index().rstrip(),
    ]
    for number, (word, row) in enumerate(METHOD_TYPES.items(), start=1):
        parts += ["", method_entry(page, number, word, row, source_ref)]
    parts += [
        "",
        "## 3 The grid",
        "",
        "A method that reads a grid takes it from the grid entry of its place, "
        "`<place>.grid : !Cartesian(…)`, a typing beside the method's. The language admits "
        "these grid constructors:",
        "",
        grid_index().rstrip(),
        "",
        "Each constructor may end with `require=`, one predicate word or a tuple of them, "
        "a condition on the resulting grid:",
        "",
        table(("predicate", "meaning"), predicate_rows()).rstrip(),
    ]
    for number, (word, record) in enumerate(GRID_CONSTRUCTORS.items(), start=1):
        parts += ["", grid_entry(page, number, word, record, source_ref)]
    return "\n".join(parts) + "\n"


# --- the refusals: the three vocabularies ---


def refusals_table(page):
    """The three tables of the refusals page, each under its heading: one
    row for each rule of each vocabulary of `VOCABULARIES`, in the order the
    catalogue writes them, with the operation that refuses under the rule
    (`operation`) and the claim its comment states (`claims`), the two the
    rule's entry answers; the anchor of a row is the rule's name, the
    fragment of its entry."""
    conditions = claims()
    head = ("rule", "written", "operation", "claim", "denotes", "read from")
    sections = []
    for number, (words, table_name, rules) in enumerate(VOCABULARIES, start=1):
        rows = [
            (
                anchored(rule, code(rule)),
                code(f"rule = {rule!r}") if table_name == "TARGET_RULES" else code(f"(rule {rule})"),
                code(operation(rule)) if operation(rule) else NONE,
                prose(conditions.get(rule) or NONE),
                denotes(page),
                read_from("refusals.py", table_name, rule),
            )
            for rule in rules
        ]
        sections.append((f"### 2.{number} {words[0].upper()}{words[1:]}", table(head, rows)))
    # a table ends with its own newline, so one more leaves one blank line
    # between a table and the next heading
    return "\n".join(f"{heading}\n\n{held}" for heading, held in sections)


# --- the rules of the language and their code: SEMANTIC_RULES ---

# a heading of the appendix `APPENDIX`: a second-level heading with its
# number, `## 3 The rules`, or the heading of one of its sections 2.1 to 2.5
# or of one of its rules R1 to R12, `### R1 Blocks and their headers`
APPENDIX_HEADING = re.compile(r"^(##|###) (\d+|2\.\d+|R\d+) (.+?)\s*$")


@dataclasses.dataclass(frozen=True)
class AppendixSection:
    """One section 2.1 to 2.5 or one rule R1 to R12 of the appendix: its
    number or label, its title, and the number and the title of the
    second-level heading it stands under."""

    label: str
    title: str
    part: str
    part_title: str

    @property
    def cited(self):
        """The section as a sentence cites it: `§2.1`, or `R1` for a rule."""
        return self.label if self.label.startswith("R") else f"§{self.label}"

    @property
    def anchor(self):
        """The anchor MkDocs gives the section's heading."""
        return slugify(f"{self.label} {self.title}", "-")


@functools.cache
def appendix_sections():
    """The sections 2.1 to 2.5 and the rules R1 to R12 of the appendix, in
    page order, read from its headings outside fenced blocks."""
    text = (ROOT / "docs" / APPENDIX).read_text(encoding="utf-8")
    sections, part, fenced = [], None, False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        found = None if fenced else APPENDIX_HEADING.match(line)
        if found is None:
            continue
        level, label, title = found.groups()
        if level == "##":
            part = (label, title)
        elif part is not None:
            sections.append(AppendixSection(label, title, *part))
    return tuple(sections)


def definition_line(source, qualified):
    """The line of the statement that defines `qualified`, a function, a
    method or a class by its dotted name, in the module text `source`; None
    where the text holds no such definition."""
    body, found = ast.parse(source).body, None
    for part in qualified.split("."):
        defined = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        found = next(
            (node for node in body if isinstance(node, defined) and node.name == part), None
        )
        if found is None:
            return None
        body = found.body
    return found.lineno


@functools.cache
def exported_module(revision, module):
    """The text of a module at an exported revision, read once in a run."""
    return exported_source(revision, module)


def function_cell(names, revision):
    """The cell of the functions a row names, each written
    `module:qualified.name`: the functions of one module on one line, after
    the module's path in the package, in the order of first mention, and a
    dash where the row names none. A name the package does not hold is
    refused. With an exported revision, each name links to its definition at
    the line that revision holds, and a revision that does not hold the
    definition is refused."""
    by_module = {}
    for name in names:
        dotted, _, qualified = name.partition(":")
        try:
            resolve(name)
        except (ImportError, AttributeError) as error:
            raise SystemExit(
                f"a row of SEMANTIC_RULES names {name}, which the package does not hold: {error}"
            )
        module = module_path(dotted)
        shown = code(qualified)
        if revision is not None:
            held = exported_module(revision, module)
            line = definition_line(held, qualified) if held is not None else None
            if line is None:
                raise SystemExit(
                    f"the exported revision {revision} holds no definition of {qualified} in "
                    f"{module}; name a revision that holds it, or none"
                )
            shown = f"[{shown}]({SOURCE.format(ref=revision, path=module, line=line)})"
        by_module.setdefault(module.removeprefix(PACKAGE_FOLDER), []).append(shown)
    lines = [f"{code(module)}: {', '.join(shown)}" for module, shown in by_module.items()]
    return "<br>".join(lines) or NONE


def refusal_links(page, rules):
    """The refusal rules of a row, each linked to its entry on the Refusals
    page, whose anchor is the rule's name; a dash where the row names none."""
    target = posixpath.relpath(REFUSALS, posixpath.dirname(page))
    return ", ".join(f"[{code(rule)}]({target}#{rule})" for rule in rules) or NONE


def page_link(page, path):
    """A link from `page` to the page at `path` under `docs/`, shown by that
    page's title, the text of its first-level heading."""
    for line in (ROOT / "docs" / path).read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            target = posixpath.relpath("docs/" + path, posixpath.dirname(page))
            return f"[{prose(line[2:].strip())}]({target})"
    raise SystemExit(f"docs/{path} holds no first-level heading")


def named_test_cell(test):
    """The test a row names, its file above its function and case; a dash
    where the row names none."""
    if test is None:
        return NONE
    file, _, function = test.partition("::")
    return f"{code(file)}<br>{code(function)}"


def section_link(page, section):
    """A link from `page` to a section or a rule of the appendix, shown as a
    sentence cites it."""
    target = posixpath.relpath("docs/" + APPENDIX, posixpath.dirname(page))
    return f"[{section.cited}]({target}#{section.anchor})"


# a numbered heading of the third level of the appendix, with its number and
# its title: `### 1.1 Stages, perches, and fields`, `### R6 Well-formedness`
APPENDIX_NUMBERED = re.compile(r"^### (\d+\.\d+|R\d+) (.+?)\s*$")


@functools.cache
def appendix_numbers():
    """The title of every numbered section of the third level of the
    appendix, by its number, in page order, with the number of the section
    that holds the opening marker of the printed table under the key None.
    The headings are read outside fenced blocks, and an appendix whose
    numbered sections hold no opening marker is refused."""
    titles, label, fenced, marked = {}, None, False, None
    for line in (ROOT / "docs" / APPENDIX).read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        found = None if fenced else APPENDIX_NUMBERED.match(line)
        if found is not None:
            label = found.group(1)
            titles[label] = found.group(2)
        elif line.strip() == MARKERS[0]:
            marked = label
    if marked is None:
        raise SystemExit(
            f"no numbered section of docs/{APPENDIX} holds the marker {MARKERS[0]} of the "
            "table of the rules that the package does not yet check"
        )
    return {**titles, None: marked}


def cited(label):
    """A section of the appendix as a sentence cites it: `§2.1`, or `R1` for
    a rule."""
    return label if label.startswith("R") else f"§{label}"


def texts_cell(example):
    """The cell of the example of a rule not yet checked, a line of the
    example to a line of the cell: each line as one code span, and an empty
    line of the cell where an empty line stands between two texts."""
    lines = example.strip("\n").split("\n")
    return "<br>".join(code(line) if line.strip() else "" for line in lines)


def unchecked_rules_table(page):
    """The table of the section of the appendix that lists the rules the
    package does not yet check, printed from the rows of `SEMANTIC_RULES`
    with `checked` false and from `UNCHECKED_ELSEWHERE`
    (`bellman/semantic_rules.py`). The first cell of a row holds the
    sections of the appendix that the rule concerns, in page order, the
    rule, and after `See also` the other pages that state it, each linked
    with its section; the second holds what the package does today; and the
    third the example (`texts_cell`). The rows stand in the order of the
    first section each names, and the rows that begin with one section in
    the order of the tables. A section that the appendix does not hold is
    refused."""
    order = [label for label in appendix_numbers() if label is not None]
    rows = [row for row in SEMANTIC_RULES if not row.checked] + list(UNCHECKED_ELSEWHERE)
    for row in rows:
        unknown = [label for label in row.sections if label not in order]
        if unknown:
            raise SystemExit(
                f"a rule not yet checked names the section {unknown[0]}, which docs/{APPENDIX} "
                f"does not hold: {row.item}"
            )

    def placed(row):
        """The sections a row names, in page order."""
        return sorted(row.sections, key=order.index)

    def first(row):
        """The place of a row: that of the first section it names, and the
        end of the table for a row that names none."""
        return order.index(placed(row)[0]) if row.sections else len(order)

    def rule_cell(row):
        sections = ", ".join(cited(label) for label in placed(row))
        pages = joined(f"{page_link(page, path)} §{section}" for path, section in row.see_also)
        return (
            (f"{sections}. " if sections else "")
            + prose(row.item)
            + (f" See also {pages}." if pages else "")
        )

    return table(
        ("Rule", "What the package does today", "Smallest text"),
        [
            (rule_cell(row), prose(row.package_today), texts_cell(row.example))
            for row in sorted(rows, key=first)
        ],
    )


def rules_table(page, source_ref=EXPORTED_REVISION):
    """The generated part of the rules page, printed from `SEMANTIC_RULES`
    and `RULES_STATED_ELSEWHERE` of `bellman/semantic_rules.py`: a sentence
    on how a function is named and linked; then, under the numbers and the
    titles of the appendix's own headings, one table for each of its
    sections 2.1 to 2.5 and of its rules R1 to R12, with one row for each
    rule the package checks or carries out, its functions, its refusals and
    a test; then a sentence that links the section of the appendix whose
    table lists the rules that the package does not yet check
    (`unchecked_rules_table`), so that each of those rules is printed once;
    then one table of the refusal rules that other pages state. A row whose
    section the appendix does not hold is refused."""
    sections = appendix_sections()
    known = {section.label for section in sections}
    for row in SEMANTIC_RULES:
        if row.section not in known:
            raise SystemExit(
                f"a row of SEMANTIC_RULES names the section {row.section}, which docs/{APPENDIX} "
                "does not hold"
            )
    named = (
        "Each function below is named by its module, as a path under "
        f"{code(PACKAGE_FOLDER)}, and its qualified name"
    )
    if source_ref is None:
        parts = [
            f"{named}. A public link to each definition is unavailable until an exported "
            "revision holds it."
        ]
    else:
        parts = [
            f"{named}, which links to its definition in the public repository at the "
            f"exported revision {code(source_ref[:12])}."
        ]
    head = ("rule", "implemented by", "checked by", "refusals", "test")
    part = None
    for section in sections:
        if section.part != part:
            part = section.part
            parts += ["", f"## {section.part} {section.part_title}"]
        rows = [
            (
                prose(row.item),
                function_cell(row.implements, source_ref),
                function_cell(row.checks, source_ref),
                refusal_links(page, row.refusals),
                named_test_cell(row.test),
            )
            for row in SEMANTIC_RULES
            if row.section == section.label and row.checked
        ]
        parts += [
            "",
            f"### {section.label} {section.title}",
            "",
            f"The rules of Appendix C {section_link(page, section)}.",
            "",
            table(head, rows).rstrip(),
        ]
    stated = [
        (refusal_links(page, (rule,)), page_link(page, path))
        for rule, path in RULES_STATED_ELSEWHERE.items()
    ]
    number = int(part) + 1
    titles = appendix_numbers()
    listed = titles[None]
    appendix = posixpath.relpath("docs/" + APPENDIX, posixpath.dirname(page))
    anchor = slugify(f"{listed} {titles[listed]}", "-")
    parts += [
        "",
        f"## {number} Rules that the package does not yet check",
        "",
        f"[Appendix C]({appendix}#{anchor}) §{listed} lists the rules that the language has "
        "and that the package does not yet check, each with what the package does today and "
        "the smallest text that shows it. That table is printed from the package's tables of "
        "the rules, as this page is, and a test of the package runs each text.",
        "",
        f"## {number + 1} Rules that other pages state",
        "",
        "Each of these refusal rules belongs to a rule that the page named beside it states.",
        "",
        table(("refusal rule", "stated on"), stated).rstrip(),
    ]
    return "\n".join(parts) + "\n"


# --- the types: OBJECTS, SET_FORMS and LIMITS, with the vocabulary ---

# the field name on which the table of the perches shows each mark
MARKED_NAME = "V"


def record_cell(name):
    """The cell of the record a row of `OBJECTS` names, written
    `module:qualified.name`: the class after its module's path in the
    package. A name the package does not hold is refused."""
    dotted, _, qualified = name.partition(":")
    try:
        resolve(name)
    except (ImportError, AttributeError) as error:
        raise SystemExit(
            f"a row of OBJECTS names {name}, which the package does not hold: {error}"
        )
    return f"{code(module_path(dotted).removeprefix(PACKAGE_FOLDER))}: {code(qualified)}"


def interval_of(bounds):
    """The interval of a reserved set of real numbers as a file writes one,
    from its endpoints (lower, lower closed, upper, upper closed)."""
    lower, lower_closed, upper, upper_closed = bounds
    infinities = {float("-inf"): "-inf", float("inf"): "inf"}
    left, right = "[" if lower_closed else "(", "]" if upper_closed else ")"
    return f"{left}{infinities.get(lower, lower)}, {infinities.get(upper, upper)}{right}"


def reserved_set_rows():
    """One row for each reserved set of `PRIMITIVE_SETS`, in the order the
    table first names it: the set by its glyph, its other spellings, the
    kind of its numbers and, for a set of real numbers, its interval."""
    held_by_glyph = {}
    for spelling, held in PRIMITIVE_SETS.items():
        held_by_glyph.setdefault(held.glyph, (held, []))[1].append(spelling)
    return [
        (
            code(glyph),
            ", ".join(code(spelling) for spelling in spellings if spelling != glyph) or NONE,
            held.kind,
            code(interval_of(held.bounds)) if held.bounds is not None else NONE,
        )
        for glyph, (held, spellings) in held_by_glyph.items()
    ]


def read_in_cell(row):
    """The objects in whose type a form of `SET_FORMS` is read, each linked
    to its row of the objects, or one phrase where the form is read in the
    type of every object of `WITH_A_SET`. A name outside `WITH_A_SET` is
    refused."""
    beside = [name for name in row.read_in if name not in WITH_A_SET]
    if beside:
        raise SystemExit(
            f"the row {row.constructor} of SET_FORMS names {', '.join(beside)}, which "
            "WITH_A_SET does not hold"
        )
    if set(row.read_in) == set(WITH_A_SET):
        return "every object that is declared with a set"
    return joined(f"[{name}](#{anchor_of(name)})" for name in row.read_in)


def types_table(page):
    """The six tables of the types page, each under its heading: the objects
    of a stage, one row for each row of `OBJECTS`
    (`bellman/typing/type_table.py`), with its line above the name of the
    file that holds it; the role words of `ROLE_WORD` and the role
    `MULTIPLIER`, which has none (`bellman/syntax/vocabulary.py`); the perch
    words of `PERCHES` and `PERCH_WORD` with the marks of `WRITTEN_MARK`,
    each shown on the name `MARKED_NAME`; the reserved sets of
    `PRIMITIVE_SETS` (`reserved_set_rows`); the forms of a set expression,
    one row for each row of `SET_FORMS`; and the limits of the language on
    a type, one row for each row of `LIMITS`, its rule linked to its entry
    on the Refusals page. A row of the objects is anchored by its name and
    a row of the forms by its constructor."""
    files = list(dict.fromkeys(row.file for row in OBJECTS))
    objects = [
        (
            anchored(row.name, row.name),
            prose(row.denotes),
            f"{code(row.line)}<br>in {code(posixpath.basename(row.file))}",
            prose(row.written),
            record_cell(row.record),
            code(row.read_by),
        )
        for row in OBJECTS
    ]
    roles = [(role, code("!" + word)) for role, word in ROLE_WORD.items()]
    roles.append((MULTIPLIER, NONE))
    perches = [
        (
            PERCH_WORD[perch],
            code("!" + perch),
            code(MARKED_NAME + WRITTEN_MARK[perch])
            if WRITTEN_MARK[perch]
            else f"none: {code(MARKED_NAME)}",
        )
        for perch in PERCHES
    ]
    forms = [
        (
            anchored(row.constructor, code(row.constructor)),
            code(row.example),
            prose(row.denotes),
            read_in_cell(row),
        )
        for row in SET_FORMS
    ]
    limits = [
        (prose(row.limit), code(row.line), refusal_links(page, (row.rule,))) for row in LIMITS
    ]
    sections = (
        (
            "Objects of a stage",
            "Each line stands in a file of the repository and is quoted without its "
            "annotation, the part of a line after `::`. The files are "
            f"{joined(code(file) for file in files)}. A record is named by its module, as a "
            f"path under {code(PACKAGE_FOLDER)}, and its class. The expression in the last "
            "column is written for the stage that the file states; where the line stands in a "
            "methods file, the stage has that methods file read.",
            ("object", "what it is", "declared by", "type written", "record", "read by"),
            objects,
        ),
        (
            "Role words",
            "A role word follows `!` among the components of a type, as in `c : ℝ₊₊ @ !ctrl`. "
            "A field that carries no role word is a state, and the subject of a line that "
            "states a law with `~` is a shock. A multiplier takes no role word: a line inside "
            "a block declares it together with its clause, as `μ[>] : ℝ₊ ⟂ a >= 0` does "
            f"({page_link(page, 'Bellman-Sym/10-constraints.md')} §4.2).",
            ("role", "word"),
            roles,
        ),
        (
            "Perch words and marks",
            "A perch word follows `!` after a side of a block header, as in "
            "`(k : Xa) : !arvl`. A mark is written directly after a name and states the perch "
            "of that one field. A name at the decision perch is written without a mark, and "
            f"{code(MARKED_NAME + '[~]')} is read as {code(MARKED_NAME)}.",
            ("perch", "word", "mark on a name"),
            perches,
        ),
        (
            "Reserved sets",
            "The grammar reserves these names, and a file writes one without defining it. "
            f"{page_link(page, 'Bellman-Sym/reference/symbols-conventions.md')} §9.2 says "
            "what each set holds.",
            ("set", "also written", "kind of number", "interval"),
            reserved_set_rows(),
        ),
        (
            "Forms of a set expression",
            "The last column names the objects of §2.1 in whose type the package reads the "
            "form. A field is taken there as a block header lists it, and §2.6 states what a "
            "declaration on a line of its own reads.",
            ("constructor", "written", "what it holds", "read in the type of"),
            forms,
        ),
        (
            "Limits on a type",
            "The package refuses each line below, in a stage file that holds no other "
            "declaration, under the rule beside it.",
            ("limit", "a line that breaks it", "refusal"),
            limits,
        ),
    )
    # a table ends with its own newline, so one more leaves one blank line
    # between a table and the next heading
    return "\n".join(
        f"### 2.{number} {title}\n\n{sentence}\n\n{table(head, rows)}"
        for number, (title, sentence, head, rows) in enumerate(sections, start=1)
    )


# --- the index of the API ---


# the words by which `stage.builder` reads its two builders graphs, the
# backward `stage.builder.bwd` and the forward `stage.builder.fwd`, read from
# the package's table of them
BACKWARD_WORD, FORWARD_WORD = DIRECTION_WORDS["backward"], DIRECTION_WORDS["forward"]
# the handles of the stage, each by the path of the way in that reaches one
# on the corpus stage, and the members its rows show, every member of its
# class where the entry names none: the stage, its definitions table, the
# initial diagrams and one of them, the builders by the pairs of perches
# they join, each perch with the builders of the edge that leaves it, the
# two builders graphs, a builder, a piece inside it, a block of an initial
# diagram with a line read from it by its name, a line that reads no wire,
# and the three tables. The block shows its reading by a key alone, since
# its other members are those of the builder, whose class it shares. The
# line that reads no wire is the `!doc` maximization of `port.bl`
# (`doc_line_stage`), since the consumption stage writes none: its method
# lines stand in its addition, and its maximization forms an operation
LEVELS = (
    ("stage", lambda stage: stage, None),
    ("stage.definitions", lambda stage: stage.definitions, None),
    ("stage.initial", lambda stage: stage.initial, None),
    ("stage.initial.backward", lambda stage: stage.initial.backward, None),
    ("stage.builder", lambda stage: stage.builder, None),
    ("stage.arvl", lambda stage: stage.arvl, None),
    ("stage.arvl.builder", lambda stage: stage.arvl.builder, None),
    ("stage.dcsn", lambda stage: stage.dcsn, None),
    ("stage.dcsn.builder", lambda stage: stage.dcsn.builder, None),
    ("stage.cntn", lambda stage: stage.cntn, None),
    ("stage.cntn.builder", lambda stage: stage.cntn.builder, None),
    (f"stage.builder.{BACKWARD_WORD}", lambda stage: getattr(stage.builder, BACKWARD_WORD), None),
    (f"stage.builder.{FORWARD_WORD}", lambda stage: getattr(stage.builder, FORWARD_WORD), None),
    ('stage.builder["cntn", "dcsn"]', lambda stage: stage.builder["cntn", "dcsn"], None),
    (
        'stage.builder["cntn", "dcsn"]["pullback"]',
        lambda stage: stage.builder["cntn", "dcsn"]["pullback"],
        None,
    ),
    (
        'stage.initial.backward["cntn_to_dcsn"]',
        lambda stage: stage.initial.backward["cntn_to_dcsn"],
        ("__getitem__",),
    ),
    (
        'stage.initial.backward["cntn_to_dcsn"]["value"]',
        lambda stage: stage.initial.backward["cntn_to_dcsn"]["value"],
        None,
    ),
    (
        'stage.initial.backward["policy", "objective"]',
        lambda stage: doc_line_stage().initial.backward["policy", "objective"],
        None,
    ),
    ("stage.par", lambda stage: stage.par, None),
    ("stage.settings", lambda stage: stage.settings, None),
    ("stage.methods", lambda stage: stage.methods, None),
)
# the modules whose classes are the handles
HANDLE_MODULES = (pieces.__name__, elaborated.__name__)
# what a verb raises when the piece refuses it: a refusal of `refusals.py`
# (a `ValueError` or a `LookupError`), a key no piece answers, and a path at
# which the stage has no builder, such as `stage.cntn.builder.fwd` (an
# `AttributeError`); any other error is the script's own and stops it
REFUSALS_OF_THE_PACKAGE = (ValueError, LookupError, AttributeError)
# the verbs that bind a version, in the order §8 of the page of the stage
# object applies them, each with its file: each example applies the verb to
# the version the verbs before it made, the first to the symbolic stage
BINDING_VERBS = {"calibrate": CALIBRATION, "methodize": METHODS_FILE, "configure": SETTINGS}
# the argument of each verb that takes one, and the key of each handle read
# by a key, as the class of the handle names them; an entry named by a path of
# `LEVELS` in place of the class holds at that path alone, the forward
# builders graph being read by the name of a forward builder and the block by
# the name of a line
EXAMPLE_ARGUMENTS = {
    ("ElaboratedStage", "check_inputs"): ({"V[>]": abs},),
    ("Definitions", "denote"): ("cons:g:dcsn_to_cntn",),
    ("Definitions", "__getitem__"): ("cons:g:dcsn_to_cntn",),
    ("GraphHandle", "__getitem__"): ("cntn_to_dcsn",),
    (f"stage.builder.{FORWARD_WORD}", "__getitem__"): ("dcsn_to_cntn",),
    ('stage.initial.backward["cntn_to_dcsn"]', "__getitem__"): ("value",),
    ("BubbleHandle", "__getitem__"): ("pullback",),
    ("Parameters", "__getitem__"): ("ρ",),
    ("Parameters", "__getattr__"): ("ρ",),
    ("Settings", "__getitem__"): ("n_a",),
    ("Settings", "__getattr__"): ("n_a",),
    ("BoundMethods", "__getitem__"): ("policy",),
}
# the two readings of a handle by a name, each a row of its own: by a key,
# `stage.par[name]`, and by an attribute, `stage.par.<name>`, the value alone
# of a parameter or a setting
READINGS = ("__getitem__", "__getattr__")
# the handles whose reading by a key has one row for each key the handle
# answers, with the key written in the path, `stage.builder["cntn", "dcsn"]`,
# in place of the one row that names the key's parameter, `[key]`. The keys
# of `stage.builder` are the pairs of perches its builders join. Each of
# these rows shows the builder that one pair reads. A key that `key_suffix`
# writes as an attribute, `policy`, has only that attribute's row,
# `stage.builder.policy`
EVERY_KEY = ("BuilderPairs",)
# a verb that answers on the builder of one direction alone, by the class of
# the handle and the verb: the path at which its row stands and the handle
# there, which the row shows in place of the level's. The joint measure of
# state and choice is the forward decision builder's, and the backward
# decision builder answers it with an unresolved marker
VERB_PATHS = {
    ("BubbleHandle", "state_choice_measure"): (
        'stage.builder["dcsn", "cntn"]',
        lambda stage: stage.builder["dcsn", "cntn"],
    ),
}


def sentences(doc):
    """The sentences of a docstring, each on one line; a path a docstring
    breaks before its dot, `stage.builder.bwd` over `.primitives`, is joined."""
    text = " ".join((doc or "").split())
    text = re.sub(r"(\w)\s+\.(\w)", r"\1.\2", text)
    return [part for part in re.split(r"(?<=\.)\s+(?=[A-Z`(\"'])", text) if part]


def first_sentence(doc):
    found = sentences(doc)
    return found[0] if found else ""


def public_type(value):
    """The name of the class a value is an instance of: for an immutable copy
    of the package, the public class it freezes (`_native_class`), else the
    first public class of its type."""
    frozen = getattr(type(value), "_native_class", None)
    if frozen is not None:
        return frozen.__name__
    for klass in type(value).__mro__:
        if not klass.__name__.startswith("_"):
            return klass.__name__
    return type(value).__name__


def one_line(text):
    """A text as the example column writes it: without a memory address, its
    runs of white space one space, and cut to its first 75 characters and the
    mark … where it runs past 76. The mark stands for what the cell leaves
    out: here the rest of a cut line, and in `printed` also the later lines
    of an answer that prints several."""
    text = re.sub(r" at 0x[0-9a-f]+", "", text)
    text = " ".join(text.split())
    return text if len(text) <= 76 else text[:75] + "…"


def printed(value):
    """What a value prints, as one line: the first of its non-blank printed
    lines, written by `one_line`. The printed lines are those of a text of
    several lines, else the representation where it is one line, else the
    lines of `str(value)`. Where the value prints more than one line, the
    first line is followed by a space and the mark …, unless `one_line` has
    cut that line and it ends with the mark already. The mark … thus stands
    for what the cell leaves out, the rest of a cut line or the later lines
    of the answer, and no first line reads as the whole answer."""
    if isinstance(value, str) and "\n" in value:
        lines = value.splitlines()
    else:
        shown = repr(value)
        lines = str(value).splitlines() if "\n" in shown else [shown]
    lines = [line for line in lines if line.strip()]
    shown = one_line(lines[0] if lines else "")
    return shown if len(lines) <= 1 or shown.endswith("…") else shown + " …"


def module_of(obj):
    """The path of the module that defines `obj`, under the package."""
    module = inspect.getmodule(obj)
    return Path(module.__file__).resolve().relative_to(PACKAGE).as_posix()


def required_parameters(function, instance=True):
    """The names of the parameters a call must give, the instance of a method
    aside."""
    parameters = list(inspect.signature(function).parameters.values())[1 if instance else 0 :]
    return [
        parameter.name
        for parameter in parameters
        if parameter.default is inspect.Parameter.empty
        and parameter.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]


@dataclasses.dataclass(frozen=True)
class Member:
    """One public attribute or verb of a handle: its name, what it is, the
    class and the object that define it, and its docstring's sentence. With
    `by_answer`, the row takes the sentence of the class of the answer where
    the package defines that class (`answer_sentence`), and `sentence` is the
    one it takes otherwise."""

    name: str
    what: str  # field, attribute or verb
    owner: type
    obj: object
    sentence: str
    by_answer: bool = False


def class_sentence(owner, word):
    """The first sentence of the docstring of `owner` that names `word` in a
    code span."""
    for sentence in sentences(inspect.getdoc(owner)):
        if f"`{word}`" in sentence:
            return sentence
    return ""


def answer_sentence(value):
    """The first sentence of the docstring of the class of `value`, where the
    package defines that class and it is none of the immutable copies of
    DisCoPy's objects that `native/hypergraphs.py` makes (`_native_class`);
    empty for a value of Python's, such as a stage's `name` or a graph's
    `level`, and for an immutable copy, such as a piece's `box`."""
    klass = type(value)
    if klass.__module__.split(".")[0] != "bellman" or hasattr(klass, "_native_class"):
        return ""
    return first_sentence(inspect.getdoc(klass))


def members(handle):
    """The public attributes and verbs of the class of `handle` that the
    handle modules define, in the order the classes define them, the class
    of the handle first: its record fields, the field `version` aside, which
    is the stage the handle was reached from; its properties and verbs, each
    with a docstring; `__getitem__`, the reading by a key; and
    `__getattr__`, the reading by an attribute, by which a parameter and a
    setting answer their values alone. A field, like a reading by a key that
    has no docstring, is described by the class of its answer (`by_answer`);
    where the package does not define that class, a field is described by
    the sentence of the docstring of the class holding it that names it, and
    a reading by the sentence of that docstring that writes a key."""
    klass, found, seen = type(handle), [], {"version"}
    if dataclasses.is_dataclass(klass):
        for field in dataclasses.fields(klass):
            if field.name.startswith("_") or field.name in seen:
                continue
            owner = next(
                k for k in klass.__mro__ if field.name in getattr(k, "__annotations__", {})
            )
            sentence = class_sentence(owner, field.name)
            if not sentence:
                continue  # a field no docstring names is no way in either
            seen.add(field.name)
            found.append(Member(field.name, "field", owner, None, sentence, by_answer=True))
    for owner in klass.__mro__:
        if owner.__module__ not in HANDLE_MODULES:
            continue
        for name, obj in vars(owner).items():
            if name in seen or (name.startswith("_") and name not in READINGS):
                continue
            if isinstance(obj, property):
                what = "attribute"
            elif inspect.isfunction(obj):
                what = "verb"
            else:
                continue
            doc = inspect.getdoc(obj.fget if isinstance(obj, property) else obj)
            sentence, by_answer = first_sentence(doc), False
            if name == "__getitem__" and not sentence:
                sentence = next(
                    (s for s in sentences(inspect.getdoc(owner)) if '["' in s),
                    first_sentence(inspect.getdoc(owner)),
                )
                by_answer = True
            if not sentence:
                continue  # a member no docstring states is a guard, not a way in
            seen.add(name)
            found.append(Member(name, what, owner, obj, sentence, by_answer))
    return found


def quoted(argument):
    """An argument as a call writes it, a string in double quotes."""
    if isinstance(argument, dict):
        entries = ", ".join(f"{quoted(key)}: {quoted(value)}" for key, value in argument.items())
        return "{" + entries + "}"
    if inspect.isbuiltin(argument) and argument.__module__ == "builtins":
        return argument.__name__
    return repr(argument).replace("'", '"')


def key_suffix(handle, key):
    """The part of the path that reads the key `key` of `handle`, written
    after the handle's own path. The operations table and the API index both
    write a key of `stage.builder` with it. A key that also names an
    attribute of the handle's class is written as that attribute, `.policy`.
    Any other key is written in brackets, a tuple of names as the names it
    holds, `["cntn", "dcsn"]`, and one name alone, `["pullback"]`."""
    if isinstance(key, str) and isinstance(getattr(type(handle), key, None), property):
        return f".{key}"
    parts = key if isinstance(key, tuple) else (key,)
    return "[" + ", ".join(quoted(part) for part in parts) + "]"


def example_arguments(member, handle, path):
    """The arguments the example gives a verb, or the key it reads a handle
    by, at `path` where `EXAMPLE_ARGUMENTS` names that path, else as it names
    the class of the handle; a verb that takes an argument no entry names is
    refused, so that the index never guesses one."""
    if member.name in BINDING_VERBS:
        return (BINDING_VERBS[member.name],)
    wanted = required_parameters(member.obj)
    if not wanted:
        return ()
    klass = type(handle).__name__
    for key in ((path, member.name), (klass, member.name)):
        if key in EXAMPLE_ARGUMENTS:
            return EXAMPLE_ARGUMENTS[key]
    raise SystemExit(
        f"{klass}.{member.name} takes {', '.join(wanted)}; name an argument for its example "
        f"in EXAMPLE_ARGUMENTS of docs/_hooks/reference_pages.py"
    )


def answer_path(member, handle, path, key=None):
    """(path suffix, the call as the example shows it, the arguments) of one
    member of the handle at `path`: `.name` for an attribute,
    `.name(parameters)` for a verb, `[parameter]` for the reading by a key,
    or the key itself as `key_suffix` writes it where `key` names one
    (`EVERY_KEY`), `["cntn", "dcsn"]`, whose example shows the answer alone,
    and `.<parameter>` for the reading by an attribute, whose example writes
    the name after the dot, `.ρ`."""
    if member.what in ("field", "attribute"):
        return f".{member.name}", "", ()
    if key is not None:
        return key_suffix(handle, key), "", (key,)
    arguments = example_arguments(member, handle, path)
    shown = ", ".join(quoted(argument) for argument in arguments)
    if member.name == "__getitem__":
        return f"[{required_parameters(member.obj)[0]}]", f"[{shown}]", arguments
    if member.name == "__getattr__":
        (name,) = arguments
        return f".<{required_parameters(member.obj)[0]}>", f".{name}", arguments
    wanted = required_parameters(member.obj)
    return (
        f".{member.name}({', '.join(wanted)})",
        f"{member.name}({shown})" if shown else "",
        arguments,
    )


def answer(member, handle, path, before, key=None):
    """(path suffix, the call as the example shows it, the answer) of one
    member on its handle at `path`, a reading by a key at `key` where it
    names one; a binding verb is applied to the version `before` holds for
    it, the version the verbs before it in `BINDING_VERBS` made."""
    suffix, call, arguments = answer_path(member, handle, path, key)
    if member.what in ("field", "attribute"):
        return suffix, call, getattr(handle, member.name)
    if member.name == "__getitem__":
        (read,) = arguments
        return suffix, call, handle[read]
    if member.name == "__getattr__":
        (name,) = arguments
        return suffix, call, getattr(handle, name)
    if member.name in BINDING_VERBS:
        return suffix, call, getattr(before[member.name], member.name)(*arguments)
    return suffix, call, getattr(handle, member.name)(*arguments)


def row_key(path, suffix, member):
    """The key a handle's row takes its anchor from (`anchor_of`): the row's
    path, and for the reading by an attribute the path with the word
    `attribute` before the name, `stage-par-attribute-name`, since the
    characters around the name are no letters and the path alone would give
    the anchor of the reading by a key, `stage-par-name`."""
    if member.name == "__getattr__":
        return f"{path}.attribute{suffix}"
    return path + suffix


def defined_in(member):
    """The module and the name that define a member."""
    if member.what == "field":
        return f"{code(module_of(member.owner))}, {code(f'{member.owner.__name__}.{member.name}')}"
    function = member.obj.fget if isinstance(member.obj, property) else member.obj
    if function.__qualname__.split(".")[0] == member.owner.__name__:
        name = f"{member.owner.__name__}.{member.name}"
    else:
        name = function.__qualname__  # a module function the class binds as its method
    return f"{code(module_of(function))}, {code(name)}"


def example_cell(call, value):
    return f"{code(call)}: {code(printed(value))}" if call else code(printed(value))


def function_row(path, function, call, value):
    """The row of one function of the package: its path, the first sentence
    of its docstring, the type of the answer, the call with the answer, and
    the module and the name that define it."""
    return (
        anchored(path.split("(")[0], code(path)),
        prose(first_sentence(inspect.getdoc(function))),
        code(public_type(value)),
        example_cell(call, value),
        f"{code(module_of(function))}, {code(function.__name__)}",
    )


@functools.cache
def stage_examples():
    """(path, function, call, answer) of the three functions that make the
    stage of a file or a text, each on `cons`."""
    record = load_stage(CONS)
    text = (ROOT / CONS).read_text(encoding="utf-8")
    return (
        ("bellman.stage.load_stage(path)", load_stage, f'load_stage("{CONS}")', record),
        (
            "bellman.stage.elaborate_stage(record)",
            elaborate_stage,
            "elaborate_stage(record)",
            elaborate_stage(record),
        ),
        (
            "bellman.stage.elaborate_text(text, origin)",
            elaborate_text,
            f'elaborate_text(text, "{CONS}")',
            elaborate_text(text, CONS),
        ),
    )


def stage_rows():
    """The rows of the three functions that make the stage of a file or a
    text, each on `cons`."""
    return [function_row(*example) for example in stage_examples()]


@functools.cache
def syntactic_trellis():
    """The syntactic trellis of the trellis file `TRELLIS`."""
    return load_trellis(TRELLIS)


@functools.cache
def elaborated_trellis():
    """The elaborated trellis of the trellis file `TRELLIS`."""
    return elaborate_trellis(syntactic_trellis())


def trellis_periods():
    """The periods of the elaborated trellis of `TRELLIS`."""
    return elaborated_trellis()["periods"]


def certified_route():
    """The first certified route of the elaborated trellis of `TRELLIS`, the
    portfolio stage's into the consumption stage of the terminal period, on
    one coordinate, the wealth `w` that becomes the resources `m`."""
    return next(
        route for route in trellis_selection(elaborated_trellis()).routes if route.status == "certified"
    )


def symbolic_cons():
    """The symbolic stage of `cons`, the answer of the example of
    `elaborate_stage` (`stage_examples`)."""
    return stage_examples()[1][3]


def written_in_a_temporary_folder(write):
    """The answer of `write`, a call that writes files into a folder it names
    relative to the working directory, made with a new temporary folder as
    the working directory, which is removed afterwards: the files are written
    outside the checkout, and the paths the call answers are the same on
    every machine."""
    with tempfile.TemporaryDirectory() as folder, contextlib.chdir(folder):
        return write()


# the example of each public function of `bellman.stage`, `bellman.period` and
# `bellman.trellis` that `stage_rows` does not print, by its qualified name,
# `trellis.load_trellis`: the call as its cell shows it, and the function that
# computes the answer. In a call, `record` is the source record of `cons`,
# `text` its text and `stage` its symbolic stage, `elaborate_stage(record)`;
# `syntactic` is the syntactic trellis of the trellis file `TRELLIS`,
# `elaborated` its elaborated trellis, `periods` the periods of that trellis
# and `mapping` its inter-period mapping, and `ROOT` is the repository's root;
# `load_recipe` and `assemble_trellis` read `RECIPE` in `REGISTRY`; `explore`
# and `write_model_explorer` write the view of the symbolic stage of `cons`,
# or of `elaborated`, into the folder `model-explorer` of a temporary working
# directory (`written_in_a_temporary_folder`), and `explore` opens no browser
# and starts no server. A public function with no entry is refused by
# `export_rows`
FUNCTION_EXAMPLES = {
    "trellis.read_trellis_file": (
        f'read_trellis_file("{TRELLIS}")', lambda: read_trellis_file(TRELLIS),
    ),
    "trellis.load_trellis": (f'load_trellis("{TRELLIS}")', syntactic_trellis),
    "trellis.load_recipe": (
        f'load_recipe("{REGISTRY}", "{RECIPE}")',
        lambda: load_recipe(REGISTRY, RECIPE),
    ),
    "trellis.elaborate_trellis": ("elaborate_trellis(syntactic)", elaborated_trellis),
    "stage.make_stage": (
        "make_stage(*parse_with_spans(text))",
        lambda: make_stage(*parse_with_spans((ROOT / CONS).read_text(encoding="utf-8"))),
    ),
    "trellis.calibrate_trellis": (
        "calibrate_trellis(elaborated, syntactic)",
        lambda: calibrate_trellis(elaborated_trellis(), syntactic_trellis()),
    ),
    "trellis.methodize_trellis": (
        "methodize_trellis(elaborated, syntactic)",
        lambda: methodize_trellis(elaborated_trellis(), syntactic_trellis()),
    ),
    "trellis.configure_trellis": (
        "configure_trellis(methodize_trellis(elaborated, syntactic), syntactic)",
        lambda: configure_trellis(
            methodize_trellis(elaborated_trellis(), syntactic_trellis()),
            syntactic_trellis(),
        ),
    ),
    "trellis.specify_trellis": (
        "specify_trellis(syntactic)",
        lambda: specify_trellis(syntactic_trellis()),
    ),
    "trellis.respecify_trellis": (
        "respecify_trellis(specify_trellis(syntactic), syntactic, syntactic)",
        lambda: respecify_trellis(
            specify_trellis(syntactic_trellis()), syntactic_trellis(), syntactic_trellis()
        ),
    ),
    "trellis.assemble_trellis": (
        f'assemble_trellis("{REGISTRY}", "{RECIPE}")',
        lambda: assemble_trellis(REGISTRY, RECIPE),
    ),
    "trellis.accrete": (
        'accrete({"periods": [], "inter_connectors": []}, periods[0])',
        lambda: accrete({"periods": [], "inter_connectors": []}, trellis_periods()[0]),
    ),
    "trellis.changed_positions": (
        "changed_positions(elaborated, calibrate_trellis(elaborated, syntactic))",
        lambda: changed_positions(
            elaborated_trellis(),
            calibrate_trellis(elaborated_trellis(), syntactic_trellis()),
        ),
    ),
    "period.period_joins": (
        "period_joins(periods[0])",
        lambda: period_joins(trellis_periods()[0]),
    ),
    "period.forward_order": (
        "forward_order(periods[0])",
        lambda: forward_order(trellis_periods()[0]),
    ),
    "period.backward_order": (
        "backward_order(periods[0])",
        lambda: backward_order(trellis_periods()[0]),
    ),
    "period.computable_together": (
        "computable_together(periods[0])",
        lambda: computable_together(trellis_periods()[0]),
    ),
    "period.forward_record": (
        "forward_record(periods[1], mapping, to=periods[0])",
        lambda: forward_record(
            trellis_periods()[1],
            elaborated_trellis()["inter_connectors"][0],
            to=trellis_periods()[0],
            address="periods[1]",
        ),
    ),
    "trellis.inter_period_joins": (
        "inter_period_joins(mapping, periods[1], periods[0])",
        lambda: inter_period_joins(
            elaborated_trellis()["inter_connectors"][0], trellis_periods()[1], trellis_periods()[0]
        ),
    ),
    "trellis.unjoined_fields": (
        "unjoined_fields(elaborated)",
        lambda: unjoined_fields(elaborated_trellis()),
    ),
    # the derivative readings no route of the trellis supplies; none on the
    # cons-port trellis, whose additions state every derivative read
    "trellis.derivative_missing": (
        "derivative_missing(elaborated)",
        lambda: derivative_missing(elaborated_trellis()),
    ),
    "trellis.trellis_selection": (
        "trellis_selection(elaborated)",
        lambda: trellis_selection(elaborated_trellis()),
    ),
    "trellis.connection_report": (
        "connection_report(elaborated)",
        lambda: connection_report(elaborated_trellis()),
    ),
    "trellis.transport_point": (
        "transport_point(route, (1.0,))",
        lambda: transport_point(certified_route(), (1.0,)),
    ),
    "trellis.transport_vector": (
        "transport_vector(route, (0.1,))",
        lambda: transport_vector(certified_route(), (0.1,)),
    ),
    "trellis.transport_hessian": (
        "transport_hessian(route, ((1,),))",
        lambda: transport_hessian(certified_route(), ((1,),)),
    ),
    "trellis.transport_atoms": (
        "transport_atoms(route, (((1.0,), 0.5), ((2.0,), 0.5)))",
        lambda: transport_atoms(certified_route(), (((1.0,), 0.5), ((2.0,), 0.5))),
    ),
    "trellis.pull_back": (
        "pull_back(route, lambda w: 2*w)(1.0)",
        lambda: pull_back(certified_route(), lambda w: 2 * w)(1.0),
    ),
    "period.diagram_period": (
        "diagram_period(elaborated, 0)",
        lambda: diagram_period(elaborated_trellis(), 0),
    ),
    "trellis.diagram_trellis": (
        "diagram_trellis(elaborated)",
        lambda: diagram_trellis(elaborated_trellis()),
    ),
    "stage.explore": (
        'explore(elaborate_stage(record), folder="model-explorer", open_browser=False)',
        lambda: written_in_a_temporary_folder(
            lambda: explore(symbolic_cons(), folder="model-explorer", open_browser=False)
        ),
    ),
    "stage.write_model_explorer": (
        'write_model_explorer(elaborate_stage(record), "model-explorer")',
        lambda: written_in_a_temporary_folder(
            lambda: write_model_explorer(symbolic_cons(), "model-explorer")
        ),
    ),
    "stage.source_spans": (
        f'source_spans(text, "{CONS}")',
        lambda: source_spans((ROOT / CONS).read_text(encoding="utf-8"), CONS),
    ),
    "stage.bind_stage": (
        f'bind_stage(elaborate_stage(record), {{"calibration": "{CALIBRATION}", '
        '"methods": {}, "settings": {}})',
        lambda: bind_stage(
            symbolic_cons(), {"calibration": CALIBRATION, "methods": {}, "settings": {}}
        ),
    ),
    "stage.graph_refusal": (
        'graph_refusal(elaborate_stage(record), "builders", "forward")',
        lambda: graph_refusal(symbolic_cons(), "builders", "forward"),
    ),
    "stage.admitted_methods": (
        'admitted_methods(elaborate_stage(record), "arvl_to_dcsn")',
        lambda: admitted_methods(symbolic_cons(), "arvl_to_dcsn"),
    ),
    "stage.header_line": (
        'header_line(stage.initial.backward["cntn_to_dcsn"].denote())',
        lambda: header_line(symbolic_cons().initial.backward["cntn_to_dcsn"].denote()),
    ),
    "stage.source_lines": (
        'source_lines(stage.definitions.denote("cons:g:dcsn_to_cntn"))',
        lambda: source_lines(symbolic_cons().definitions.denote("cons:g:dcsn_to_cntn")),
    ),
    "stage.to_model_explorer": (
        "to_model_explorer(elaborate_stage(record))",
        lambda: to_model_explorer(symbolic_cons()),
    ),
    "stage.perch_overlays": (
        "perch_overlays(elaborate_stage(record))",
        lambda: perch_overlays(symbolic_cons()),
    ),
    "stage.box_attributes": (
        'box_attributes(stage, "backward", '
        'stage.builder.bwd.primitives["cntn_to_dcsn:Pullback"].box)',
        lambda: box_attributes(
            symbolic_cons(),
            "backward",
            symbolic_cons().builder.bwd.primitives["cntn_to_dcsn:Pullback"].box,
        ),
    ),
    "stage.layers_to_open": (
        'layers_to_open(to_model_explorer(elaborate_stage(record)), "backward", 1)',
        lambda: layers_to_open(to_model_explorer(symbolic_cons()), "backward", 1),
    ),
    "stage.node_place": (
        'node_place(to_model_explorer(elaborate_stage(record)), "backward", '
        '"policy.optimality:Argmax")',
        lambda: node_place(
            to_model_explorer(symbolic_cons()), "backward", "policy.optimality:Argmax"
        ),
    ),
    "stage.wire_counts": (
        "wire_counts(to_model_explorer(elaborate_stage(record)))",
        lambda: wire_counts(to_model_explorer(symbolic_cons())),
    ),
    "stage.header_of": (
        'header_of(stage.initial.backward["cntn_to_dcsn"].box)',
        lambda: header_of(symbolic_cons().initial.backward["cntn_to_dcsn"].box),
    ),
    "stage.header_fields": (
        f'header_fields(text, "{CONS}")',
        lambda: header_fields((ROOT / CONS).read_text(encoding="utf-8"), CONS),
    ),
    "stage.branches": (
        "branches(elaborate_stage(record))",
        lambda: branches(symbolic_cons()),
    ),
    "stage.to_source": (
        'to_source(stage.fields()["cons:dcsn:c"].domain)',
        lambda: to_source(symbolic_cons().fields()["cons:dcsn:c"].domain),
    ),
    # the two functions that read and write a typing entry of an addition's
    # text, each on the methods file of `cons`; `addition` is that file's text
    "stage.typing_entries": (
        f'typing_entries(addition, "{METHODS_FILE}")',
        lambda: typing_entries((ROOT / METHODS_FILE).read_text(encoding="utf-8"), METHODS_FILE),
    ),
    "stage.write_typing_entry": (
        f'write_typing_entry(addition, "{METHODS_FILE}", "policy", "method", "!vfi")',
        lambda: write_typing_entry(
            (ROOT / METHODS_FILE).read_text(encoding="utf-8"), METHODS_FILE, "policy", "method", "!vfi"
        ),
    ),
    # the sections of a card, on the card of the decision builder of `cons`
    "stage.card_sections": (
        'card_sections(stage.builder["cntn", "dcsn"].denote())',
        lambda: card_sections(symbolic_cons().builder["cntn", "dcsn"].denote()),
    ),
    "trellis.to_model_explorer": (
        "to_model_explorer(elaborated)",
        lambda: to_model_explorer(elaborated_trellis()),
    ),
    "trellis.perch_overlays": (
        "perch_overlays(elaborated)",
        lambda: perch_overlays(elaborated_trellis()),
    ),
    "trellis.layers_to_open": (
        'layers_to_open(to_model_explorer(elaborated), "backward", 2)',
        lambda: layers_to_open(to_model_explorer(elaborated_trellis()), "backward", 2),
    ),
    "trellis.node_place": (
        f'node_place(to_model_explorer(elaborated), "backward", "periods[1]{LAYER_ID_ENDING}")',
        lambda: node_place(
            to_model_explorer(elaborated_trellis()), "backward", f"periods[1]{LAYER_ID_ENDING}"
        ),
    ),
    "trellis.wire_counts": (
        "wire_counts(to_model_explorer(elaborated))",
        lambda: wire_counts(to_model_explorer(elaborated_trellis())),
    ),
    "trellis.explore": (
        'explore(elaborated, folder="model-explorer", open_browser=False)',
        lambda: written_in_a_temporary_folder(
            lambda: explore(elaborated_trellis(), folder="model-explorer", open_browser=False)
        ),
    ),
    "trellis.write_model_explorer": (
        'write_model_explorer(elaborated, "model-explorer")',
        lambda: written_in_a_temporary_folder(
            lambda: write_model_explorer(elaborated_trellis(), "model-explorer")
        ),
    ),
    "trellis.unpaired_joins": (
        "unpaired_joins(elaborated)",
        lambda: unpaired_joins(elaborated_trellis()),
    ),
    "trellis.entry_span": (
        f'entry_span((ROOT / "{TRELLIS}").read_text(), "inter_connectors[0]")',
        lambda: entry_span((ROOT / TRELLIS).read_text(encoding="utf-8"), "inter_connectors[0]"),
    ),
    "trellis.entry_value": (
        f'entry_value((ROOT / "{TRELLIS}").read_text(), "inter_connectors[0]")',
        lambda: entry_value((ROOT / TRELLIS).read_text(encoding="utf-8"), "inter_connectors[0]"),
    ),
    "trellis.replace_entry": (
        f'replace_entry((ROOT / "{TRELLIS}").read_text(), "name", "cons_port_copy")',
        lambda: replace_entry(
            (ROOT / TRELLIS).read_text(encoding="utf-8"), "name", "cons_port_copy"
        ),
    ),
    "trellis.append_to_mapping": (
        f'append_to_mapping(Path("{TRELLIS}").read_text(), "inter_connectors[0]", "w_next", "w")',
        lambda: append_to_mapping(
            Path(TRELLIS).read_text(encoding="utf-8"),
            "inter_connectors[0]",
            "w_next",
            "w",
        ),
    ),
    "trellis.append_to_sequence": (
        f'append_to_sequence(Path("{TRELLIS}").read_text(), "periods[0].connectors", "{{b: k}}")',
        lambda: append_to_sequence(
            Path(TRELLIS).read_text(encoding="utf-8"), "periods[0].connectors", "{b: k}"
        ),
    ),
    "trellis.insert_in_sequence": (
        f'insert_in_sequence(Path("{TRELLIS}").read_text(), "periods[0].connectors", 0, '
        '"{b: k}")',
        lambda: insert_in_sequence(
            Path(TRELLIS).read_text(encoding="utf-8"), "periods[0].connectors", 0, "{b: k}"
        ),
    ),
    "trellis.split_entry": (
        f'split_entry(Path("{TRELLIS}").read_text(), "periods[0]", 3)',
        lambda: split_entry(Path(TRELLIS).read_text(encoding="utf-8"), "periods[0]", 3),
    ),
    "trellis.remove_from_sequence": (
        f'remove_from_sequence(Path("{TRELLIS}").read_text(), "periods[0].connectors", 0)',
        lambda: remove_from_sequence(
            Path(TRELLIS).read_text(encoding="utf-8"), "periods[0].connectors", 0
        ),
    ),
    "trellis.remove_from_mapping": (
        f'remove_from_mapping(Path("{TRELLIS}").read_text(), "inter_connectors[0]", "disc.a")',
        lambda: remove_from_mapping(
            Path(TRELLIS).read_text(encoding="utf-8"), "inter_connectors[0]", "disc.a"
        ),
    ),
    "trellis.written_at": (
        f'written_at("{TRELLIS}", "periods[3].stages.cons.methods")',
        lambda: written_at(TRELLIS, "periods[3].stages.cons.methods"),
    ),
    "trellis.written_spans": (
        f'written_spans("{TRELLIS}", ("periods[3].stages.cons.methods", "periods[4].stages.cons.methods"))',
        lambda: written_spans(
            TRELLIS, ("periods[3].stages.cons.methods", "periods[4].stages.cons.methods")
        ),
    ),
    "trellis.period_entries": (
        f'period_entries("{TRELLIS}")',
        lambda: period_entries(TRELLIS),
    ),
    # a drag between the two unjoined ports of the trellis, the savings that
    # leave the discounting stage of the terminal period and the capital the
    # portfolio stage of the earliest period arrives at, five periods apart
    "trellis.connector_entry": (
        'connector_entry(elaborated, (0, "disc", "a"), (5, "port", "k"))',
        lambda: connector_entry(elaborated_trellis(), (0, "disc", "a"), (5, "port", "k")),
    ),
}


def assignment_comment(module, name):
    """The first sentence of the comment on the lines just above the
    top-level statement of `module` that assigns `name`, the comment's lines
    joined. It describes a constant of the package, since a string or a
    number has no docstring of its own. The comment above a rule of `RULES`
    states that rule's claim in the same way. The answer is empty where no
    comment stands there."""
    source = Path(module.__file__).read_text(encoding="utf-8")
    lines = source.splitlines()
    for statement in ast.parse(source).body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        else:
            continue
        assigned = {
            node.id
            for target in targets
            for node in ast.walk(target)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        }
        if name not in assigned:
            continue
        comment, index = [], statement.lineno - 2
        while index >= 0 and lines[index].lstrip().startswith("#"):
            comment.insert(0, lines[index].strip().lstrip("#").strip())
            index -= 1
        return first_sentence(" ".join(comment))
    return ""


def export_rows(namespace):
    """The rows of the public names of one namespace, `bellman.stage`,
    `bellman.period` or `bellman.trellis`, in the order of its table, the
    three functions `stage_rows` writes left out: each function as
    `FUNCTION_EXAMPLES` prints it under its qualified name,
    `trellis.load_trellis`, its path written with the parameters a call must
    give, and each name that is neither a function, a class nor a module,
    the method table, the three perch words and the constants of the view,
    described by the docstring of its class where the package defines that
    class and otherwise by the first sentence of the comment above the line
    of the defining module that assigns it (`assignment_comment`). A public
    function no entry prints is refused, and so is one whose example the
    package refuses, and a constant that neither a docstring nor a comment
    describes."""
    shown = {function for _, function, _, _ in stage_examples()}
    short = namespace.__name__.rpartition(".")[2]
    rows, unprinted = [], []
    for name in namespace.__all__:
        value = getattr(namespace, name)
        qualified = f"{short}.{name}"
        if inspect.isfunction(value):
            if value in shown:
                continue
            if qualified not in FUNCTION_EXAMPLES:
                unprinted.append(qualified)
                continue
            call, make = FUNCTION_EXAMPLES[qualified]
            try:
                answered = make()
            except REFUSALS_OF_THE_PACKAGE as refusal:
                raise SystemExit(
                    f"the example of {namespace.__name__}.{name} in the API index, {call}, "
                    f"is refused: {type(refusal).__name__}: {refusal}"
                ) from refusal
            parameters = ", ".join(required_parameters(value, instance=False))
            path = f"{namespace.__name__}.{name}({parameters})"
            rows.append(function_row(path, value, call, answered))
        elif not (inspect.isclass(value) or inspect.ismodule(value)):
            module = importlib.import_module(namespace._EXPORTS[name])
            sentence = answer_sentence(value) or assignment_comment(module, name)
            if not sentence:
                raise SystemExit(
                    f"{namespace.__name__}.{name} has no text for the API index: the package "
                    "defines no class of it, and no comment stands above the line of "
                    f"{module.__name__} that assigns it; write one there"
                )
            rows.append(
                (
                    anchored(f"{namespace.__name__}.{name}", code(f"{namespace.__name__}.{name}")),
                    prose(sentence),
                    code(public_type(value)),
                    example_cell("", value),
                    f"{code(module_of(module))}, {code(name)}",
                )
            )
    if unprinted:
        raise SystemExit(
            f"the public functions {', '.join(unprinted)} have no row in the API index; give "
            "each an example in FUNCTION_EXAMPLES of docs/_hooks/reference_pages.py under its "
            "qualified name"
        )
    return rows


def stage_row(stage):
    """The row of the stage itself, `stage`, the object every path of the
    handles starts from and no member of a handle answers: the first
    sentence of the docstring of its class, its class, what it prints, and
    the module and the name of its class."""
    klass = type(stage)
    return (
        anchored("stage", code("stage")),
        prose(answer_sentence(stage)),
        code(public_type(stage)),
        example_cell("", stage),
        f"{code(module_of(klass))}, {code(klass.__name__)}",
    )


def listed_keys(member, handle):
    """The keys at which a member of `handle` has its rows. For the reading
    by a key of a handle of `EVERY_KEY`, these are the keys the handle
    answers, in its order, except a key that `key_suffix` writes as an
    attribute. The row of such a key is the attribute's own row. Every other
    member has one row, for which the key is None."""
    if member.name != "__getitem__" or type(handle).__name__ not in EVERY_KEY:
        return (None,)
    return tuple(key for key in handle if not key_suffix(handle, key).startswith("."))


def member_row(member, handle, path, before, key=None):
    """The row of one member on its handle at `path`, at `key` for a reading
    by a key of `EVERY_KEY`: its path, its sentence, the type of its answer,
    its example and where the package defines it. A refusal is its answer
    here, written as its class and its message on one line (`one_line`)
    beside the object that refuses, not as the representation of a text."""
    sentence = member.sentence
    try:
        suffix, call, value = answer(member, handle, path, before, key)
        kind, shown = code(public_type(value)), example_cell(call, value)
        if member.by_answer:
            sentence = answer_sentence(value) or sentence
    except REFUSALS_OF_THE_PACKAGE as refusal:
        suffix, call, _ = answer_path(member, handle, path, key)
        kind = NONE
        refused = one_line(f"{type(refusal).__name__}: {refusal}")
        shown = f"refused on {code(path)}: {code(refused)}"
    return (
        anchored(row_key(path, suffix, member), code(path + suffix)),
        prose(sentence),
        kind,
        shown,
        defined_in(member),
    )


def api_table(page):
    """The four tables of the API index, each under its heading: the public
    names of each namespace of `NAMESPACES`, in its order (`export_rows`),
    the three functions that make a stage first in the table of
    `bellman.stage`; then the table of the stage object: the stage itself,
    the specified version of `cons`, and the public attributes and verbs of
    each handle at the path of `LEVELS` that reaches it on that version,
    every one or those the entry names, the binding verbs applied in their
    order, a verb of `VERB_PATHS` at the path that table names, and the
    reading by a key of a handle of `EVERY_KEY` at each key it answers
    (`member_row`). A handle class of `stage/pieces.py` or
    `stage/elaborated.py` that no path reaches is refused."""
    version = elaborate_stage(load_stage(CONS))
    before = {}
    for verb, source in BINDING_VERBS.items():
        before[verb] = version
        version = getattr(version, verb)(source)
    specified = version
    handle_rows = [stage_row(specified)]
    covered = set()
    for level, reach, shown_members in LEVELS:
        held = reach(specified)
        covered.add(type(held))
        for member in members(held):
            if shown_members is not None and member.name not in shown_members:
                continue
            path, handle = level, held
            if (type(held).__name__, member.name) in VERB_PATHS:
                path, reach_verb = VERB_PATHS[(type(held).__name__, member.name)]
                handle = reach_verb(specified)
            handle_rows += [
                member_row(member, handle, path, before, key)
                for key in listed_keys(member, handle)
            ]
    handles = {
        klass
        for module in (pieces, elaborated)
        for klass in vars(module).values()
        if inspect.isclass(klass)
        and klass.__module__ == module.__name__
        and not klass.__name__.startswith("_")
        and klass.__doc__
        and any(
            isinstance(obj, (property,)) or inspect.isfunction(obj) for obj in vars(klass).values()
        )
    }
    missing = sorted(
        klass.__name__ for klass in handles - covered if not _abstract(klass, covered)
    )
    if missing:
        raise SystemExit(
            f"the handles {', '.join(missing)} stand at no path of LEVELS in "
            f"docs/_hooks/reference_pages.py; add the path by which the way in reaches each"
        )
    head = ("path", "what it answers", "type", "example", "defined in")
    sections = [
        (
            f"### 2.{number} `{namespace.__name__}`",
            (stage_rows() if namespace is bellman.stage else []) + export_rows(namespace),
        )
        for number, namespace in enumerate(NAMESPACES, start=1)
    ]
    sections.append((f"### 2.{len(sections) + 1} The stage object", handle_rows))
    # a table ends with its own newline, so one more leaves one blank line
    # between a table and the next heading
    return "\n".join(f"{heading}\n\n{table(head, rows)}" for heading, rows in sections)


def _abstract(klass, covered):
    """Whether `klass` is a base whose subclasses the levels cover, or a
    descriptor, which answers no path of its own."""
    return any(issubclass(other, klass) and other is not klass for other in covered) or hasattr(
        klass, "__get__"
    )


# --- the pages ---

TABLES = {
    OPERATIONS: operations_table,
    LAWS: laws_table,
    FORMS: forms_table,
    METHODS: methods_table,
    REFUSALS: refusals_table,
    RULES_PAGE: rules_table,
    APPENDIX_PAGE: unchecked_rules_table,
    TYPES_PAGE: types_table,
    API_INDEX: api_table,
}


def region(text):
    """(start, end) of what stands between the two markers of a page; None
    where the page holds them not exactly once."""
    opening, closing = (text.count(marker) for marker in MARKERS)
    if opening != 1 or closing != 1:
        return None
    start = text.index(MARKERS[0]) + len(MARKERS[0])
    end = text.index(MARKERS[1])
    return (start, end) if start <= end else None


def write_page(relative, make, check):
    """Write the table that `make` writes for one page between its markers,
    or with `check` report how the table it holds differs; returns 1 when
    `check` finds a difference or the page cannot hold the table, else 0."""
    page = ROOT / relative
    markers = f"{MARKERS[0]} and {MARKERS[1]}"
    if not page.is_file():
        print(f"{relative}: the page does not exist; write it around the markers {markers}")
        return 1
    text = page.read_text(encoding="utf-8")
    found = region(text)
    if found is None:
        print(f"{relative}: the page does not hold the markers {markers} once each, in that order")
        return 1
    start, end = found
    fresh = "\n\n" + make(relative) + "\n"
    held = text[start:end]
    rewritten = text[:start] + fresh + text[end:]
    return settle(page, [(1, held, fresh)], rewritten, check, what="table", numbered="table")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="report the tables that differ; write nothing"
    )
    parser.add_argument(
        "--page",
        action="append",
        choices=sorted(TABLES),
        help="a page to write; may be given more than once (default: every page)",
    )
    parser.add_argument(
        "--source-ref",
        default=EXPORTED_REVISION,
        help=(
            "the exported revision of econ-ark/bellman, held by this repository, at which the "
            "methods page and the rules page link each definition; without one, each public "
            "link is stated unavailable"
        ),
    )
    arguments = parser.parse_args()
    os.chdir(ROOT)
    tables = {
        **TABLES,
        METHODS: functools.partial(methods_table, source_ref=arguments.source_ref),
        RULES_PAGE: functools.partial(rules_table, source_ref=arguments.source_ref),
    }
    status = [
        write_page(page, tables[page], arguments.check) for page in (arguments.page or TABLES)
    ]
    for page, term in dict.fromkeys(UNRESOLVED):
        print(
            f"{page}: Appendix E.3 names no {term!r} in a table row or a heading, "
            "so the row links no section",
            file=sys.stderr,
        )
    return 1 if any(status) else 0


if __name__ == "__main__":
    sys.exit(main())
