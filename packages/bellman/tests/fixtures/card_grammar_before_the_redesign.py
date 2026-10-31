"""The cards `main` printed before the redesign of the card, and the grammar
that reads them.

`cards_before_the_redesign.json` holds the card of the stage and the card of
every builder of the thirteen stages of the card sweeps, each card as its list
of lines, as the package printed them at the commit the file names, the last
commit of `main` before the redesign (`card-redesign.md` §2; the plan of the
internal developer release 0.01, §3, the paragraph on the guard). The
constants and the functions `_card_caption` to `signature_wires` below are the
card grammar of `sheets_parse.py` at that commit, copied unchanged, less the
constants of the sheets, which a card does not read: the grammar of
AMD-SG-034 §4 item 12, with its stub column of fourteen, its dotted and double
lines and its rails, which refuses the blank lines of the new form.
`entries_before` reads the entries of an `operations` block by the columns of
its header. The test `test_item_5_the_cards_keep_their_entries_rules_sources_and_definitions`
of `cat/test_card_form.py` reads the saved cards with this grammar and the
cards the package prints now with the grammar of `sheets_parse.py`, and
compares what the two recover.

The cards were printed by running this module from the tests' folder with the
package of a checkout of that commit first on the path, so that the package
printing them is the earlier one; it refuses a checkout whose package has
uncommitted changes and a package that is not the checkout's:

    PYTHONPATH=<checkout>/packages/bellman python fixtures/card_grammar_before_the_redesign.py <checkout>
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

WIDTH = 78
HEAVY = "━"
# the rules of a card's table: dotted between two blocks, double before the
# footer, heavy under the title and at the foot
DOTTED, DOUBLE, RAIL = "┈", "═", "│"
# the stub column of a card: the label stands in it and every entry starts
# after it (AMD-SG-034 §4 item 12)
STUB = 14
# the blocks of a card, in the order they may stand (§3), the definition
# card's `defines` and the method card's `admits` among them
CARD_BLOCKS = ("signature", "defines", "at", "where", "declared", "rule", "operations",
               "conditions", "method", "options", "source", "definitions", "file",
               "perches", "appendix", "admits")
CARD_FOOTERS = ("source", "definitions", "file", "perches", "appendix")
# the blocks that open with a header row naming their columns (§2 item 5)
CARD_HEADERS = {"signature": ("wire", "carrier"), "operations": ("#", "operation", "in", "out"),
                "source": ("position", "statement"), "definitions": ("name", "key")}
# the characters an entry's continuation opens with, since the engine breaks
# before a binary sign or after a comma and never before a closing bracket: a
# line at column fourteen opening with one of them is a continuation standing
# where an entry stands, and is refused (a negation `¬` opens an entry)
CONTINUATION_START = "=≤≥<>∈∉+−·/×→↦∧∨⊆⟂∘)]}│"


def _card_caption(line):
    """The label in the stub column of a line that opens a block, or None for
    an entry, a rail or a sub-heading, which start after the stub."""
    if not line or line[0].isspace():
        return None
    return line[:STUB].rstrip()


def _is_rule(line, character):
    return len(line) == WIDTH and set(line) == {character}


class Unparsed(Exception):
    """The sheet does not read as §2 says a sheet reads."""


def parse_card(text, width=WIDTH):
    """Read a card back by the grammar of AMD-SG-034 §4 item 12, independently
    of Bellman: the title, the heavy rule of 78 columns under it, the blocks
    each opened by a label of the stub column with its first entry on the
    same line, every other line an entry at column fourteen, the dotted rules
    between two blocks of the body, the double rule before the footer, the
    heavy rule closing the card, no blank line, no line over the width and
    no line that is the continuation of an entry at the stub column. With
    `width=None` the width is not read, for a reader of the blocks alone."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith(("STAGE ", "METHOD !")):
        raise Unparsed("a card names its stage or method")
    heavy = next((i for i, line in enumerate(lines) if _is_rule(line, HEAVY)), None)
    if heavy is None:
        raise Unparsed("a card separates its title from its blocks by a heavy rule of 78 columns")
    if not _is_rule(lines[-1], HEAVY):
        raise Unparsed("a heavy rule of 78 columns closes a card")
    for line in lines:
        if width is not None and len(line) > width:
            raise Unparsed(f"a card line exceeds {width} columns: {line!r}")
        if not line.strip():
            raise Unparsed("a card holds no blank line")
    sections, order, label, footer = {}, [], None, False
    for line in lines[heavy + 1:-1]:
        if _is_rule(line, DOTTED):
            if label is None:
                raise Unparsed("a dotted rule stands between two blocks, not before the first")
            label = None
            continue
        if _is_rule(line, DOUBLE):
            if footer:
                raise Unparsed("one double rule opens the footer")
            footer, label = True, None
            continue
        caption = _card_caption(line)
        if caption is not None:
            if caption not in CARD_BLOCKS:
                raise Unparsed(f"unknown card block {caption!r}")
            if caption in sections:
                raise Unparsed(f"the block {caption!r} stands twice")
            if label is not None:
                raise Unparsed(f"the block {caption!r} follows {label!r} with no rule between them")
            if footer and caption not in CARD_FOOTERS:
                raise Unparsed(f"the block {caption!r} stands in the footer")
            if not footer and caption in CARD_FOOTERS:
                raise Unparsed(f"the footer block {caption!r} stands before the double rule")
            # the first entry stands on the label's line, at column fourteen,
            # or, for a header row whose first cell is blank, after it
            if len(line) <= STUB or not line[len(caption):STUB].isspace() or not line[STUB:].strip():
                raise Unparsed(f"the first entry of {caption!r} stands at column {STUB}")
            label = caption
            order.append(caption)
            sections[label] = [line]
            continue
        if label is None:
            raise Unparsed(f"a line stands under no block: {line!r}")
        if not line.startswith(" " * STUB):
            raise Unparsed(f"an entry starts at column {STUB}: {line!r}")
        if len(line) > STUB and line[STUB] != " " and line[STUB] in CONTINUATION_START:
            # an entry's continuation stands deeper than column fourteen; a
            # line at that column opening with a sign or a closing bracket
            # continues the entry above it and is refused
            raise Unparsed(f"a continuation stands at column {STUB}: {line!r}")
        sections[label].append(line)
    return {"address": " ".join(line.strip() for line in lines[:heavy]),
            "stamp": None, "key": None, "subtitle": None,
            "sections": sections, "order": order, "complete": {key: True for key in sections}}


def card_table(lines):
    """The rows of a block whose first line is a header row: the columns the
    header's words start at cut every row after it into cells, the first row's
    cells read after the stub; a rail row holds the rule of the row above it
    under the key `rule`, and a sub-heading (a word alone on a line at column
    fourteen, as the stage card names its directions) under `heading`."""
    if not lines:
        return []
    header = lines[0][STUB:]
    starts = [match.start() + STUB for match in re.finditer(r"\S+", header)]
    words = header.split()
    rows = []
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped.startswith(RAIL):
            if rows:
                rows[-1].setdefault("rule", []).append(stripped[len(RAIL):].strip())
            continue
        cells = [line[start:(starts[place + 1] if place + 1 < len(starts) else None)].strip()
                 for place, start in enumerate(starts)]
        if len(line) - len(stripped) == STUB and all(cell == "" for cell in cells[1:]) and " " not in stripped:
            rows.append({"heading": stripped})
            continue
        rows.append(dict(zip(words, cells)))
    return rows


def signature_wires(lines):
    """The wires of a `signature` block, one per row, `(word, name, carrier)`:
    the sub-label `in` or `out` (carried down to the rows under it), the name
    at column eighteen and the carrier after the colon; a continuation line
    joins the carrier of the row above."""
    found, word = [], None
    for line in lines[1:]:
        if len(line) - len(line.lstrip()) == STUB and line[STUB:].strip() in ("in", "out"):
            word = line.strip()
            continue
        sublabel = line[STUB:STUB + 4].strip()
        if sublabel in ("in", "out"):
            word = sublabel
        body = line[STUB + 4:]
        name, colon, carrier = body.partition(" : ")
        if colon and not body.startswith(" "):
            found.append([word, name.rstrip(), carrier.strip()])
        elif found and body.strip().startswith(": "):
            found[-1][2] = body.strip()[2:]
        elif found and colon and body.startswith(" "):
            found[-1][2] = carrier.strip()
        elif found:
            found[-1][2] = (found[-1][2] + " " + body.strip()).strip()
        elif word is not None and body.strip():
            found.append([word, body.strip(), ""])
    return [tuple(entry) for entry in found]


def entries_before(lines):
    """The entries of an `operations` block, in order, each a mapping: its
    `number` (None for a sub-builder's row, which carries none) and `key`; the
    `direction` it stands under on the stage's card (None elsewhere);
    `inputs` and `outputs`, the texts of its `in` and `out` cells over all its
    lines; and `rule`, the lines behind its rails. The rows are cut by the
    columns the header's words start at, as `card_table` cuts them, with
    three readings `card_table` lacks: a number of two digits begins a column
    before the header's right-aligned `#`, so the number is read from the
    stub to the `operation` column; a direction's word is longer than the `#`
    column and is read whole; and a cell that fell under its row, which
    stands left of the `in` column, is the row's last cell, `out`, as is
    every line of the entry after it."""
    header = lines[0]
    starts = {match.group(): match.start() for match in re.finditer(r"\S+", header)
              if match.start() >= STUB}
    key_at, in_at, out_at = starts["operation"], starts["in"], starts["out"]
    entries, direction = [], None
    for line in lines[1:]:
        body = line.lstrip()
        at = len(line) - len(body)
        if body.startswith(RAIL):
            # the text behind the rail and its space, a continuation keeping
            # the columns it stands deeper by
            entries[-1]["rule"].append(body[len(RAIL) + 1:].rstrip())
            continue
        if at == STUB and body in ("backward", "forward"):
            direction = body
            continue
        number, key = line[STUB:key_at].strip(), line[key_at:in_at].strip()
        inputs, outputs = line[in_at:out_at].strip(), line[out_at:].strip()
        if number.isdigit() or (not number and key and " " not in key and inputs and outputs
                                and at >= key_at):
            entries.append({"number": number or None, "key": key, "direction": direction,
                            "inputs": inputs, "outputs": outputs, "rule": [], "fallen": False})
            continue
        entry = entries[-1]
        if at < in_at or entry["fallen"]:
            entry["outputs"] += " " + body
            entry["fallen"] = True
        else:
            entry["inputs"] += " " + inputs
            entry["outputs"] += " " + outputs
    for entry in entries:
        del entry["fallen"]
    return entries


# The stages whose cards are saved: the thirteen stages of the card sweeps,
# each by the name of its stage fixture in `conftest.py` and by its file's
# path at the commit the saved cards name, the path `save` reads in a
# checkout of that commit.
STAGE_FILES = {
    "cons": "applications/portfolio-choice/cons.bl",
    "port": "applications/portfolio-choice/port.bl",
    "ez_savings": "applications/epstein-zin-savings/ez_savings.bl",
    "cons_savings_iid": "applications/consumption-savings-iid/cons_savings_iid.bl",
    "sa_savings": "applications/smooth-ambiguity-savings/sa_savings.bl",
    "buffer_stock": "applications/buffer-stock/buffer_stock.bl",
    "adjuster_cons": "applications/durables/stages/adjuster_cons.bl",
    "worker_saving": "applications/pension-retirement/stages/worker_saving.bl",
    "retiree_saving": "applications/pension-retirement/stages/retiree_saving.bl",
    "keeper_saving": "applications/housing-frictions/stages/keeper_saving.bl",
    "adjuster_saving": "applications/housing-frictions/stages/adjuster_saving.bl",
    "tenure": "applications/durables/stages/tenure.bl",
    "worker_ageing": "applications/cagetti-denardi-2006/worker_ageing.bl",
}
SAVED = Path(__file__).resolve().parent / "cards_before_the_redesign.json"


def cards_of(stage):
    """`(title, text)` of the stage's card and of each builder's card, the
    titles as `PrintedStage.cards` of `conftest.py` gives them."""
    cards = [("stage", str(stage.denote()))]
    for direction, graph in (("backward", stage.builder.bwd), ("forward", stage.builder.fwd)):
        for name in graph.list():
            cards.append((f"{direction} {name}", str(graph[name].denote())))
    return cards


def save(checkout):
    """Print the cards of `STAGE_FILES` with the package of `checkout` and
    write them to `SAVED`, each card as its list of lines."""
    checkout = Path(checkout).resolve()
    import bellman
    from bellman.stage import elaborate_stage
    if checkout / "packages" / "bellman" not in Path(bellman.__file__).resolve().parents:
        raise SystemExit(f"the package on the path is {bellman.__file__}, not the one of {checkout}")
    changed = subprocess.run(["git", "status", "--porcelain", "--", "packages/bellman/bellman"],
                             cwd=checkout, capture_output=True, text=True, check=True).stdout
    if changed.strip():
        raise SystemExit(f"the package of {checkout} has uncommitted changes:\n{changed}")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True,
                            text=True, check=True).stdout.strip()
    stages = {}
    for name, path in STAGE_FILES.items():
        text = (checkout / path).read_text(encoding="utf-8")
        stage = elaborate_stage({"stage": {"text": text, "origin": path},
                                 "calibration": {}, "settings": {}, "methods": {}})
        stages[name] = {"file": path,
                        "cards": {title: card.split("\n") for title, card in cards_of(stage)}}
    saved = {"commit": commit, "stages": stages}
    SAVED.write_text(json.dumps(saved, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{sum(len(stage['cards']) for stage in stages.values())} cards of {len(stages)} stages "
          f"printed at {commit} written to {SAVED}")


if __name__ == "__main__":
    save(sys.argv[1])
