"""The numbered dossier of a stage, assembled from its public queries.

The dossier contains the printed view, definitions, builders, initial
diagrams and obligations of `docs/Bellman-Sym/API/index.md`.
An anonymous dossier removes source information from the answer records
before printing them; a source-inclusive dossier keeps it.

The full dossier, `dossier_lines`, prints every card. The compact dossier,
`compact_dossier_lines`, prints each fact of the stage once, from the same
pieces, and is the form the reader-back of Matsya reads.
"""

from __future__ import annotations

import dataclasses
import os
import re
from collections.abc import Mapping
from pathlib import Path

from bellman.display.cards import Piece, Statement, card_sections
from bellman.factory.elaboration import elaborate_text
from bellman.factory.loading import load_stage, read_trellis_file
from bellman.factory.recipe import load_recipe, template_keys
from bellman.factory.trellis import elaborate_trellis
from bellman.refusals import ConstructionError, FactoryError, NotConstructed
from bellman.stage.builder_pairs import DIRECTION_WORDS
from bellman.stage.sources import read_yaml_mapping
from bellman.syntax.layout import HEAVY, LABEL_COLUMN, LIGHT, horizontal_line
from bellman.typing.typed_expressions import obligation_entry

ROOT = Path(os.environ.get("BELLMAN_DDSL_ROOT") or Path(__file__).resolve().parents[3])

# the file's `@stage` line, read for the header of a file the
# elaborator refuses
STAGE_LINE = re.compile(r"^@stage:\s*(\S+)", re.MULTILINE)

# every line after a labeled line's first is indented to the label column
CONTINUATION = " " * LABEL_COLUMN

# the neutral token that stands for the stage's own name in an anonymous
# dossier
ANONYMOUS = "stage"

# the words that stand where the anonymous dossier would name the stage file
ANONYMOUS_FILE = "the stage file"

# the characters a rule line is drawn with: a card's heavy border, a
# section's light separator, the dotted rule of the view's bindings and the
# double rule of a refusal; a line of these characters alone states nothing,
# and the compact dossier leaves it out
RULE_CHARACTERS = frozenset(HEAVY + LIGHT + "┄═")

# the sections of a definition's card the compact dossier keeps, by the kind
# of the record: a parameter, a set and a distribution by the authored line
# `Source` quotes, since `Defines` restates it; a law of motion and a value
# aggregator by the function `Defines` states, since the block line `Source`
# quotes stands under the block's card; a block line by its `Conditions`,
# since the line itself stands under the block's card; and every other
# definition, a function, a correspondence or a multiplier, by `Defines`,
# which states the derived sets, with `Source` and `Conditions`
COMPACT_DEFINITION_SECTIONS = {
    "parameter": ("source", "conditions"),
    "set": ("source", "conditions"),
    "distribution": ("source", "conditions"),
    "g": ("defines",),
    "G": ("defines",),
    "line": ("conditions",),
}
COMPACT_OTHER_DEFINITION_SECTIONS = ("defines", "source", "conditions")
# the sections of a block's card the compact dossier leaves out: the
# signature, which the view's block rows state, the conditions, which stand
# with the block's lines among the definitions, and the definitions referenced
COMPACT_BLOCK_SECTIONS_LEFT_OUT = ("signature", "conditions", "definitions")


# --- the dossier of a stage file ---


def dossier(path, period=None, with_source=False):
    """Every numbered line of the dossier of the stage file at `path`.

    A refused file answers with its numbered rule and message.
    See `docs/Bellman-Sym/API/index.md` for the queries."""
    text = path.read_text(encoding="utf-8")
    origin = origin_of(path)
    try:
        stage = elaborate_text(text, origin)
    except ConstructionError as refusal:
        name = refusal.stage or declared_name(text) or "the file declares no stage name"
        lines = [first_line(name, origin, with_source), "", "## refusal", ""] + refusal_lines(
            refusal
        )
        if not with_source and name != ANONYMOUS:
            lines = with_the_name_hidden(lines, name)
        return numbered(lines)
    return dossier_lines(stage, path, period, with_source)


def dossier_lines(stage, path, period=None, with_source=False):
    """Every numbered line of an already elaborated stage's dossier.

    See `docs/Bellman-Sym/API/index.md` for the printed view,
    definitions, builders, initial diagrams and obligations."""
    origin = origin_of(path)
    lines = [
        first_line(stage.name, origin, with_source),
        "",
        "## stage",
        "",
    ] + stage.view().splitlines()
    lines += [""] + definition_lines(stage, with_source)
    for direction in ("backward", "forward"):
        lines += [""] + builders_lines(stage, direction, with_source)
    for direction in ("backward", "forward"):
        lines += [""] + initial_diagram_lines(stage, direction, with_source)
    lines += [""] + obligation_lines(stage)
    if period is not None:
        lines += [""] + period_lines(period)
    return _finished(lines, stage, path, origin, with_source)


def compact_dossier_lines(stage, path, period=None, with_source=False):
    """Every numbered line of the compact dossier of an already elaborated
    stage, which states each fact once: the printed view; under `## fields`,
    the fields listing, each field with its perch, its role and its set, the
    one place a shock's declared set is printed; under
    `## definitions`, each definition by the sections of its card that
    `COMPACT_DEFINITION_SECTIONS` keeps for its kind, a parameter, a set and a
    distribution by the authored line, a law of motion and a value aggregator
    by the function with its sets, a block line by its conditions; under
    each builders graph, its signature and the conditions its primitives'
    cards state that no definition stated; under each initial diagram, each
    block's card with the authored lines under `Source`; and the
    obligations. It leaves out every rule line, the builders' primitives'
    cards, which restate a block's lines as composed kernels, the cards of
    the two diagrams, whose rows repeat the blocks' cards, and the
    definitions referenced of every card. The full dossier is
    `dossier_lines`.

    See `docs/Bellman-Sym/API/index.md` for the queries the pieces come
    from."""
    origin = origin_of(path)
    lines = [
        first_line(stage.name, origin, with_source),
        "",
        "## stage",
        "",
    ] + stage.view().splitlines()
    lines += ["", "## fields", ""] + str(stage.fields()).splitlines()
    definitions = compact_definition_lines(stage, with_source)
    lines += [""] + definitions
    stated = condition_keys(definitions)
    for direction in ("backward", "forward"):
        lines += [""] + compact_builders_lines(stage, direction, with_source, stated)
    for direction in ("backward", "forward"):
        lines += [""] + compact_initial_diagram_lines(stage, direction, with_source)
    lines += [""] + obligation_lines(stage)
    if period is not None:
        lines += [""] + period_lines(period)
    return _finished(without_rules(lines), stage, path, origin, with_source)


def _finished(lines, stage, path, origin, with_source):
    """The dossier's lines numbered, and, where the source is not kept, with
    the stage's file and name hidden first."""
    if not with_source:
        lines = without_path(lines, stage.name, origin, str(path), str(path.resolve()))
        if stage.name != ANONYMOUS:
            lines = with_the_name_hidden(lines, stage.name)
            check_hidden(lines, stage.name)
        check_no_file_path(lines, origin, str(path), str(path.resolve()))
    return numbered(lines)


def origin_of(path):
    """The stage file as the dossier names it: its path relative to the
    repository root where it lies inside the repository, so that the printed
    face names the same source in every checkout.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2, provenance."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def declared_name(text):
    """The stage's own name, the value of the file's `@stage` line, or None
    where the file declares none.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2, name."""
    found = STAGE_LINE.search(text)
    return found.group(1) if found else None


def first_line(name, origin, with_source):
    """The first line of the dossier: the stage's own name, and the file it
    was read from only where the source is kept.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2."""
    return f"{name}  {origin}" if with_source else ANONYMOUS


# --- the sections of the dossier ---


def definition_lines(stage, with_source):
    """The definitions table: the listing by kind, then each record's card in
    the order of the listing.

    See `docs/Bellman-Sym/API/stage/08-definitions.md`."""
    table = stage.definitions.list()
    lines = ["## definitions", ""] + str(table).splitlines()
    for identities in table.values():
        for identity in identities:
            lines += [""] + card_lines(stage.definitions.denote(identity), with_source)
    return lines


def card_lines(record, with_source):
    """One card of the dossier, from the record the piece denotes: as it
    prints where the source is kept, and with the author's own text removed
    where it is not.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""
    return str(record if with_source else without_authored_text(record)).splitlines()


def compact_definition_lines(stage, with_source):
    """The definitions of the compact dossier: under a heading for each kind
    of record, in the order of the definitions listing, each record's compact
    card, `compact_card_lines` with the sections of
    `COMPACT_DEFINITION_SECTIONS` for the kind; a record none of whose kept
    sections has a row, a block line without conditions, prints nothing,
    since its line stands under its block's card.

    See `docs/Bellman-Sym/API/stage/08-definitions.md`."""
    lines = ["## definitions"]
    for kind, identities in stage.definitions.list().items():
        kept = COMPACT_DEFINITION_SECTIONS.get(kind, COMPACT_OTHER_DEFINITION_SECTIONS)
        cards = []
        for identity in identities:
            card = compact_card_lines(
                stage.definitions.denote(identity), lambda label: label in kept, with_source
            )
            if len(card) > 1:
                cards += [""] + card
        if cards:
            lines += ["", f"### {kind.replace('_', ' ')}"] + cards
    return lines


def compact_card_lines(record, kept, with_source):
    """One card of the compact dossier, from the record the piece denotes:
    the card's title, then each section whose label `kept` admits and that
    has a row, its heading and its rows as the card prints them, without the
    card's rules; the author's own text is removed where the source is not
    kept, as in `card_lines`.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1 for the card."""
    shown = record if with_source else without_authored_text(record)
    lines = card_title_lines(shown)
    for label, heading, rows in card_sections(shown):
        if kept(label) and rows:
            lines.append(heading)
            lines += [line for row in rows for line in row]
    return lines


def card_title_lines(record):
    """The title of a card, the lines above its first heavy rule.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1."""
    lines = str(record).splitlines()
    return lines[: lines.index(horizontal_line(HEAVY))]


def compact_builders_lines(stage, direction, with_source, stated=frozenset()):
    """One builders graph of the compact dossier: its signature, the
    functions or measures it reads and writes with their sets, then, under
    `Conditions`, each condition the cards of its builders' primitives state
    whose key is not in `stated`, the keys of the conditions the definitions
    printed, each once; a graph that is not constructed answers its refusal.
    The primitives' cards themselves, which restate a block's lines as
    composed kernels, are left out.

    See `docs/Bellman-Sym/API/stage/03-build.md`."""
    graph = getattr(stage.builder, DIRECTION_WORDS[direction])
    lines = [f"## builders, {direction}", ""]
    try:
        names = list(graph.list())
        lines += str(graph.signature()).splitlines()
    except NotConstructed as refusal:
        return lines + refusal_lines(refusal)
    conditions, keys = [], set(stated)
    for name in names:
        primitives = graph[name].primitives
        for primitive in primitives.list():
            record = primitives[primitive].denote()
            shown = record if with_source else without_authored_text(record)
            for label, _, rows in card_sections(shown):
                if label != "conditions":
                    continue
                for row in rows:
                    key = condition_key(row)
                    if key not in keys:
                        keys.add(key)
                        conditions += list(row)
    if conditions:
        lines += ["", "Conditions"] + conditions
    return lines


def condition_rows(lines):
    """The conditions the lines print, in order: under each heading
    `Conditions`, the rows at the section's least indentation, each with the
    deeper lines that continue it."""
    found, grabbing = [], False
    for line in lines:
        if line.strip() == "Conditions":
            grabbing = True
            continue
        if grabbing and line.startswith("  ") and line.strip():
            if line.startswith("   ") and found and found[-1][-1].startswith("  "):
                found[-1].append(line)
            else:
                found.append([line])
            continue
        grabbing = False
    return found


def condition_keys(lines):
    """The keys of the conditions the lines print, each row's text without
    whitespace."""
    return {condition_key(row) for row in condition_rows(lines)}


def condition_key(row):
    """The key of one condition row, its lines' text without whitespace."""
    return "".join("".join(line.split()) for line in row)


def compact_initial_diagram_lines(stage, direction, with_source):
    """One initial diagram of the compact dossier: each block's compact card,
    without the diagram's own card, whose rows repeat the blocks'.

    See `docs/Bellman-Sym/API/stage/02-initial.md`."""
    diagram = getattr(stage.initial, direction)
    lines = [f"## initial diagram, {direction}"]
    try:
        diagram.denote()
        names = list(diagram.list())
    except NotConstructed as refusal:
        return lines + [""] + refusal_lines(refusal)
    for name in names:
        lines += ["", f"### the block {name}", ""] + compact_card_lines(
            diagram[name].denote(),
            lambda label: label not in COMPACT_BLOCK_SECTIONS_LEFT_OUT,
            with_source,
        )
    return lines


def without_rules(lines):
    """The lines without the rule lines, a line drawn with the characters of
    `RULE_CHARACTERS` alone."""
    return [line for line in lines if not (line.strip() and set(line.strip()) <= RULE_CHARACTERS)]


def without_authored_text(record):
    """The record with the author's own text and the places it was written at
    removed: the statements a kernel denotes, which are the
    lines the dossier removed under the label `source`; the `header` line,
    which quotes the signature the author wrote; every file position; and the
    descriptions written on an authored line, which on a paper's stage file
    cite the paper's equations and pages.

    The authored lines of a block and the declarations of the definitions
    table stay, being the mathematics the reconstruction is to recover, and a
    parameter's and a shock's description stays, being part of the object.

    The removal is made on the record and not on the printed page, so that no
    line is taken apart to decide whether it quotes the file.
    See `docs/Bellman-Sym/API/index.md` for the answer records.
    """
    changed = {}
    kernel = getattr(record, "kernel", None)
    if kernel is not None:
        changed["kernel"] = dataclasses.replace(kernel, statements=())
    if getattr(record, "statements", ()):
        changed["statements"] = tuple(_unplaced(one) for one in record.statements)
    if getattr(record, "header", ()):
        changed["header"] = ()
    if getattr(record, "describes", ()) and getattr(record, "kind", None) == "line":
        changed["describes"] = ()
    held = getattr(record, "statement", None)
    if held is not None:
        changed["statement"] = (
            _unplaced(held)
            if isinstance(held, Statement)
            else tuple(_unplaced(one) for one in held)
        )
    if getattr(record, "pieces", ()):
        changed["pieces"] = tuple(
            Piece(piece.key, piece.name, without_authored_text(piece.record))
            for piece in record.pieces
        )
    return dataclasses.replace(record, **changed) if changed else record


def _unplaced(statement):
    """One statement with the file position it was written at removed."""
    return dataclasses.replace(statement, position="")


def builders_lines(stage, direction, with_source):
    """One builders graph: its signature, then each builder with its
    signature, its primitives and every primitive's card.

    See `docs/Bellman-Sym/API/stage/03-build.md`."""
    graph = getattr(stage.builder, DIRECTION_WORDS[direction])
    lines = [f"## builders, {direction}", "", "### the graph", ""]
    try:
        names = list(graph.list())
        lines += str(graph.signature()).splitlines()
    except NotConstructed as refusal:
        return lines + refusal_lines(refusal)
    for name in names:
        builder = graph[name]
        lines += ["", f"### the builder {name}", ""] + str(builder.signature()).splitlines()
        primitives = builder.primitives
        lines += ["", f"### the primitives of {name}", ""] + str(primitives.list()).splitlines()
        for primitive in primitives.list():
            lines += [""] + card_lines(primitives[primitive].denote(), with_source)
    return lines


def refusal_lines(refusal):
    """A refusal as the dossier prints it: the rule and the message.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §1."""
    return [f"{'rule':<{LABEL_COLUMN}}{refusal.rule}"] + labelled("message", refusal.message)


def labelled(label, text):
    """One section of a printed view: the label in the card's label column,
    every line after the first indented to that column.

    See `docs/Bellman-Sym/API/stage/05-piece.md` §1 for the printed card."""
    lines = text.splitlines() or [""]
    return [
        (f"{label:<{LABEL_COLUMN}}" if index == 0 else CONTINUATION) + line
        for index, line in enumerate(lines)
    ]


def initial_diagram_lines(stage, direction, with_source):
    """One initial diagram: its card, then each block's.

    See `docs/Bellman-Sym/API/stage/02-initial.md`."""
    diagram = getattr(stage.initial, direction)
    lines = [f"## initial diagram, {direction}", ""]
    try:
        lines += card_lines(diagram.denote(), with_source)
        names = list(diagram.list())
    except NotConstructed as refusal:
        return lines + refusal_lines(refusal)
    for name in names:
        lines += ["", f"### the block {name}", ""] + card_lines(
            diagram[name].denote(), with_source
        )
    return lines


def obligation_lines(stage):
    """The conditions the construction assumed and did not establish, one to a
    line: the condition, its status and the definitions or lines responsible,
    with the explanation beneath where the construction states one.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §5."""
    lines = ["## obligations", ""]
    held = stage.obligations()
    if not held:
        return lines + ["none"]
    for obligation in held:
        # every entry is one of the five typed kinds of an obligation's
        # entries, and the one printer of the package writes each
        lines.append(
            f"{obligation.condition} ({obligation.status}): "
            + ", ".join(obligation_entry(entry) for entry in obligation.entries)
        )
        if obligation.explanation:
            lines.append(CONTINUATION + obligation.explanation)
    return lines


# --- the line of a period ---


def period_lines(period_file):
    """One line: whether the stages the period file names elaborate as one
    period. The package has no period object, so a period has no sheet. The
    period file is read by `read_yaml_mapping` and its stage keys by
    `template_keys`, as the factory reads a period template; a record is
    written for each key from its stage file, which `_period_stages` reads,
    and `elaborate_trellis` elaborates a trellis of that one period.

    See `docs/Bellman-Sym/API/index.md` for the
    stage's queries."""
    try:
        template = read_yaml_mapping(period_file, rule="trellis-file-shape", address="period")
        keys = template_keys(template.get("stages", []), file=str(period_file), address="period")
        stages = _period_stages(keys, period_file)
        elaborate_trellis(
            {
                "periods": [{"stages": stages, "connectors": template.get("connectors") or []}],
                "inter_connectors": [],
            }
        )
    except ConstructionError as refusal:
        outcome = f"a stage the period names is refused under the rule {refusal.rule}"
    except FactoryError as refusal:
        outcome = f"the period is refused under the rule {refusal.rule}"
    except (OSError, ValueError, TypeError) as failure:
        outcome = f"the trellis record was not elaborated ({type(failure).__name__})"
    else:
        outcome = "the stages the period names elaborate"
    return [
        "## period",
        "",
        "the package holds no period object and none answers view(), so there is no "
        f"period view to print; {outcome}",
    ]


def _period_stages(keys, period_file):
    """The source record of the stage file of each of `keys`, the keys the
    period file lists: where a recipe beside the period file names it, the
    record `load_recipe` writes for the key from the file its entry names
    under `stage`; otherwise the file `stages/<key>/<key>.bl` under the
    period file's folder, where a model folder's `declaration/` holds the
    stage file of the key."""
    folder = Path(period_file).parent
    recipe = _recipe_naming(period_file)
    if recipe is None:
        return {key: load_stage(str(folder / "stages" / key / f"{key}.bl")) for key in keys}
    records = {
        key: record
        for period in load_recipe(folder, recipe.name)["periods"]
        for key, record in period["stages"].items()
    }
    return {key: records[key] for key in keys}


def _recipe_naming(period_file):
    """The recipe beside the period file whose trellis file names the period
    file as a period template, found by the paths the files write and not by
    a file name: a YAML file of the period file's folder whose top keys
    include `trellis`, a path, and `stages`, a mapping; None where no such
    file names the period file."""
    period = Path(period_file).resolve()
    candidates = sorted(period.parent.glob("*.yml")) + sorted(period.parent.glob("*.yaml"))
    for candidate in candidates:
        try:
            raw = read_yaml_mapping(candidate, rule="recipe-shape", address="recipe")
            names_a_trellis = isinstance(raw.get("trellis"), str)
            if not names_a_trellis or not isinstance(raw.get("stages"), Mapping):
                continue
            periods = read_trellis_file(candidate.parent / raw["trellis"])["periods"]
        except (FactoryError, OSError):
            continue
        templates = [Path(held["template"]).resolve() for held in periods if "template" in held]
        if period in templates:
            return candidate
    return None


# --- the anonymous dossier, and the numbered lines ---


def without_path(lines, name, *paths):
    """The dossier with the file the stage was read from removed: each of
    `paths` in a line, such as the subtitle of the stage's own sheet, is
    replaced by `the stage file`, and a line `stage <name>, from <path>` by
    `stage stage`.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2 for provenance."""
    quoted = f"stage {name}, from "
    made = []
    for line in lines:
        if line.startswith(quoted):
            made.append(f"stage {ANONYMOUS}")
            continue
        for held in paths:
            if held and held in line:
                line = line.replace(held, ANONYMOUS_FILE)
        made.append(line)
    return made


def with_the_name_hidden(lines, name):
    """The dossier with the stage's own name replaced by the neutral token
    wherever it occurs, inside an identity as well: `buffer_stock:parameter:β`
    reads `stage:parameter:β`. A name such as `buffer_stock` names the model,
    which the reconstruction is to recover.

    See `docs/Bellman-Sym/API/stage/08-definitions.md` for identities."""
    # only the name as an identity prefix, `unit:parameter:x`, and never the
    # same letters inside the author's prose ("unit-level innovation")
    # an identity begins the token: not after a dot, which would be a line
    # identifier such as `arvl_to_dcsn.bequest` on a stage named bequest
    pattern = re.compile(rf"(?<![0-9A-Za-z_.]){re.escape(name)}(?=:)")
    return [pattern.sub(ANONYMOUS, line) for line in lines]


def check_hidden(lines, name):
    """Stops rather than print an anonymous dossier that still names the
    stage.

    See `docs/Bellman-Sym/API/stage/08-definitions.md` for names
    and identities."""
    # the name as an identity prefix, or the header line, is a leak; the same
    # letters as a line identifier or an ordinary word of the author's prose
    # (a stage named `bequest`, `unit`, `returns`) are not
    pattern = re.compile(rf"(?<![0-9A-Za-z_.]){re.escape(name)}(?=:)")
    for number, line in enumerate(lines, 1):
        if pattern.search(line) or line.strip() in (name, f"stage {name}"):
            raise SystemExit(f"line {number} names the stage: {line}")


def check_no_file_path(lines, *paths):
    """Stops rather than print an anonymous dossier that still names a file it
    was read from.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §2 for provenance."""
    for number, line in enumerate(lines, 1):
        for path in paths:
            if path in line:
                raise SystemExit(f"line {number} names the file the stage was read from: {line}")


def numbered(lines):
    """The lines with a consecutive number in a left margin, so that a reader
    can cite a line.

    See `docs/Bellman-Sym/API/index.md` for the
    printed answers."""
    return [f"{number:04d}  {line}".rstrip() for number, line in enumerate(lines, 1)]
