"""The reader of printed sheets and cards, PrintedStage, what one stage
prints, and the comparison of a printed card with the card that an example
page shows."""

import functools
import re
import types
from pathlib import Path

from stage_graphs import DIRECTIONS

from bellman.typing import typed_expressions as S


def rule_text(rule):
    """The text of a `Rule`: its statement, then its `where` conditions
    joined by `and`, then the set after `on`."""
    text = S.format_expression(rule.statement, width=None)
    if rule.where:
        text += "  where " + " and ".join(
            S.format_expression(part, width=None) for part in rule.where
        )
    if rule.on is not None:
        text += "  on " + S.format_expression(rule.on, width=None)
    return text


def cards_of_every_handle(stage):
    """Every card of a version with the record it prints, in one order: the
    stage card; each builders graph's and each initial diagram's, followed by
    the same graph's cards at the primitive grain and at the sub-builder
    grain; each builder's and each block's, followed by its cards at the
    sub-builder grain and at the primitive grain and by the cards of the
    builder's primitives and of the block's lines; and each definition's.

    Unlike `PrintedStage(stage).cards`, it includes the cards of each graph's
    handle and of its `primitives` and `sub_builders`, which the printed text
    leaves out."""
    made = [("stage", stage.denote())]
    for graph in (
        stage.builder.bwd,
        stage.builder.fwd,
        stage.initial.backward,
        stage.initial.forward,
    ):
        made.append((repr(graph), graph.denote()))
        for opened in (graph.primitives, graph.sub_builders):
            made.append((repr(opened), opened.denote()))
        for name in graph.list():
            piece = graph[name]
            made.append((repr(piece), piece.denote()))
            made.append((f"{piece!r} sub_builders", piece.sub_builders.denote()))
            made.append((f"{piece!r} primitives", piece.primitives.denote()))
            opened = piece.primitives
            for key in opened.list():
                made.append((f"{piece!r} {key}", opened[key].denote()))
    listing = stage.definitions.list()
    for group in listing:
        for identity in listing[group]:
            made.append((str(identity), stage.definitions.denote(identity)))
    return [(title, str(record), record) for title, record in made]


def refusal_text(refusal):
    """The line that records a refusal in place of what was refused:
    `refused: <the refusal's class name>: <the refusal>`."""
    return f"refused: {type(refusal).__name__}: {refusal}"


class PrintedStage:
    """What one stage prints, each part computed when it is first read and
    then kept: `cards`, which iterating the object also gives, and
    `sheets`."""

    def __init__(self, stage):
        self.stage = stage

    @functools.cached_property
    def cards(self):
        """`(title, text, record)` of each card that the printed text of the
        stage holds, in this order:

        1. the stage's card, titled `stage`;
        2. for the backward and then the forward initial diagram, the card of
           each block, in the order of the diagram's `list()`, titled
           `initial <direction> <block>`, each followed by the cards of the
           bubbles that the block lists, titled
           `initial <direction> <block> / <key>`;
        3. for the backward and then the forward builders graph, each
           builder's card, titled `<direction> <name>`, then the card of each
           of its primitives, titled `<direction> <name> / <key>`, then the
           card of each of its sub-builders, titled
           `<direction> <name> / sub-builder <key>`;
        4. each definition's card, titled by its identity.

        The printed text holds no card of a graph's handle, such as
        `str(stage.builder.bwd)` or the card of its `primitives` or its
        `sub_builders`, and no card of an opened builder, such as
        `str(builder.primitives)`.

        A bubble that a block lists is an entry of the kind `block` in the
        block's `list()`, such as a group of lines marked `!node` or a branch.
        Its card follows the block's card, in the order of the listing, and
        the cards of the bubbles that it lists follow its own. The other
        entries of a block's listing are lines, whose cards the definitions'
        cards already give.

        A sub-builder is an entry of the kind `sub-builder` in the builder's
        `sub_builders.list()`. The other entries of that listing are
        primitives, whose cards the builder's primitives already give.

        The tests of the cards check these two facts on every stage file that
        elaborates: a line that a block lists prints the card of its
        definition, and a primitive that the sub-builders' listing gives
        prints the card of the builder's primitive of the same name.

        A bubble or a sub-builder inside another is reached by several keys,
        one for each level, and its title joins them with ` / `.

        Each record is computed once and its text is the record printed,
        which is what `str` of the handle prints. A graph whose construction
        is refused gives one card in place of the cards of its blocks or its
        builders: its record is the refusal, its text
        `refused: NotConstructed: <message>`, and its title
        `initial <direction>` for an initial diagram and the direction for a
        builders graph."""
        from bellman.refusals import NotConstructed

        def card(title, record):
            # the card of a record that was constructed: its text is the
            # record printed
            return (title, str(record), record)

        def bubbles(block, keys):
            """`(keys, handle)` of each bubble that `block` lists, in the
            order of its listing, each followed by the bubbles that it lists;
            `keys` are the keys that reach `block`."""
            for entry in block.list().entries:
                if entry.kind == "block":
                    inner = block[entry.key]
                    yield keys + (entry.key,), inner
                    yield from bubbles(inner, keys + (entry.key,))

        stage = self.stage
        cards = [card("stage", stage.denote())]
        diagrams = (("backward", stage.initial.backward), ("forward", stage.initial.forward))
        for direction, diagram in diagrams:
            try:
                blocks = diagram.list()
            except NotConstructed as refusal:
                cards.append((f"initial {direction}", refusal_text(refusal), refusal))
                continue
            for block in blocks:
                piece = diagram[block]
                cards.append(card(f"initial {direction} {block}", piece.denote()))
                for keys, inner in bubbles(piece, (block,)):
                    cards.append(card(f"initial {direction} {' / '.join(keys)}", inner.denote()))
        for direction, graph in (("backward", stage.builder.bwd), ("forward", stage.builder.fwd)):
            try:
                names = graph.list()
            except NotConstructed as refusal:
                cards.append((direction, refusal_text(refusal), refusal))
                continue
            for name in names:
                builder = graph[name]
                cards.append(card(f"{direction} {name}", builder.denote()))
                pieces = builder.primitives
                for key in pieces.list():
                    cards.append(card(f"{direction} {name} / {key}", pieces[key].denote()))
                opened = builder.sub_builders
                for entry in opened.list().entries:
                    if entry.kind == "sub-builder":
                        # a sub-builder inside another has a tuple of keys
                        keys = entry.key if isinstance(entry.key, tuple) else (entry.key,)
                        title = f"{direction} {name} / sub-builder {' / '.join(keys)}"
                        cards.append(card(title, opened[entry.key].denote()))
        listing = stage.definitions.list()
        for kind in listing:
            for identity in listing[kind]:
                cards.append(card(str(identity), stage.definitions.denote(identity)))
        return tuple(cards)

    @functools.cached_property
    def sheets(self):
        """Every sheet of the stage by its address, as `sheets_of` prints
        them; the mapping cannot be changed."""
        return types.MappingProxyType(sheets_of(self.stage))

    def __iter__(self):
        return iter(self.cards)


def flat(text):
    """A printed text without its white space, so that two breakings of one
    rule into lines compare equal."""
    return "".join(text.split())


def card_section_lines(card, heading):
    """The lines of one section of a printed card: the line of its heading,
    which for `Source` names the file after two spaces, and the lines of its
    content, up to the next line at column zero, which is the next section's
    heading, the light line before the footer or the heavy line that closes
    the card, without the blank line before it; `[]` where the card has no
    such section. The blank lines between two entries of `Operations` are
    kept."""
    lines = card.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line == heading or line.startswith(heading + "  ")),
        None,
    )
    if start is None:
        return []
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i][:1] not in ("", " ")), len(lines)
    )
    while end > start + 1 and not lines[end - 1]:
        end -= 1
    return lines[start:end]


def operation_rules(lines):
    """The rules of the entries of an `Operations` section, in order, joined
    into one text without white space, as `flat` writes it: in each entry,
    the lines from its label `rule:` to the blank line that closes the
    entry, the region note included, without the label."""
    kept, inside = [], False
    for line in lines:
        body = line.strip()
        if body.startswith("rule:"):
            inside = True
            kept.append(body[len("rule:") :])
        elif not body:
            inside = False
        elif inside:
            kept.append(body)
    return flat("\n".join(kept))


# the width of a sheet and of a card, in columns
WIDTH = 78


# the characters of the heavy line, the hairline and the dashed line. A card
# prints the heavy line under its title and at its foot, one hairline across
# the card before the footer, the light line of the public page
# docs/Bellman-Sym/API/stage/05-piece.md, and short hairlines under the row of
# an entry of `Operations` and above the `out` row of `Signature`, which end
# at the card's one end column.
HEAVY, HAIRLINE, DASHED = "━", "─", "┄"


# the stamp: the bracketed `[KEY = value]` at the right margin of a sheet's
# title, such as the version
STAMP = re.compile(r"\[(?P<key>[A-Z]+) = (?P<value>[^\]]+)\]$")


# the keys that a stamp may hold
STAMP_KEYS = ("VERSION", "GRAIN", "KIND", "RECORDS", "WIRES")


# the line that opens a section of a sheet: its label, a space, then a
# hairline to column 78, which a section not yet complete draws in dashes; a
# label is the section's word in capitals, or the name of the builder, block,
# sub-builder or primitive whose section it opens, with the arrow of its
# direction where it has one
SECTION_HAIRLINE = re.compile(
    rf"^(?P<label>(?:[←→] )?\S[^\s{HAIRLINE}{DASHED}]*(?: [A-Z][^\s{HAIRLINE}{DASHED}]*)*"
    rf"(?: \d+)?) [{HAIRLINE}{DASHED}]+$"
)


# a line that ends in `range not`, which breaks the print `range not declared`
# in two; the package breaks a line between two prints and not inside one,
# unless the print alone is wider than the line (`filled` in
# bellman/display/sheets.py)
SPLIT_SET = re.compile(r"range not$")


# the end of a line before a set: a colon, a product sign or an arrow, then a
# space
SET_OPERAND = re.compile(r"[:×→] $")


# a wrapped set keeps an arrow or a product sign with its right-hand operand,
# so a continuation may begin `→ Y` or `× Y`, and no line ends in the sign
SPLIT_MAP_END = re.compile(r" [→×]$")


# the opening and the closing brackets
OPENING, CLOSING = "([{", ")]}"


# the glyphs of a dotted line, a double line and a rail, which no card prints
REFUSED_CARD_GLYPHS = {"┈": "dotted line", "═": "double line", "│": "rail"}


# the content of a section stands two columns in
INDENT = 2


# the sections of a card that stand before the light line, and those of the
# footer after it, each opened by its heading; the heading of `Source` names
# the file after two spaces
CARD_SECTIONS = (
    "Signature",
    "Defines",
    "At",
    "Where",
    "Declared",
    "Rule",
    "Operations",
    "Conditions",
    "Method",
    "Options",
    "Admits",
    "Derivation",
)


CARD_FOOTERS = ("Source", "Definitions referenced", "File", "Perches", "Appendix")


# the characters that open the continuation of an entry: the package's layout
# engine breaks a long line before a binary sign (`operand` of
# bellman/syntax/layout.py) or after a comma (`_listed` of
# bellman/typing/typed_expressions.py), and no entry opens with a closing
# bracket; a line at column two that opens with one of them is a continuation
# standing where an entry stands, and is refused (a negation `¬` opens an
# entry)
CONTINUATION_START = "=≤≥<>∈∉+−·/×→↦∧∨⊆⟂∘)]}"


def _is_line(line, character):
    """Whether `line` is the full-width line of `character`."""
    return len(line) == WIDTH and set(line) == {character}


def is_short_line(line):
    """Whether `line` is a short line: spaces, then a light line narrower than
    the card."""
    body = line.lstrip(" ")
    return bool(body) and set(body) == {HAIRLINE} and line != body


def _heading_word(line):
    """The words of a line at column zero before a run of two spaces, which is
    the heading of a section where the line opens one; None for a line that
    stands in a section."""
    if not line or line[0].isspace():
        return None
    return line.split("  ", 1)[0]


def _split_interval(line):
    """Whether ``line`` ends after an interval's separating comma.

    A comma counts only for the unmatched bracket that directly contains it.
    Thus ``: (0,`` is an interrupted interval, while the commas in
    ``: ((b, u,`` belong to a nested coordinate tuple rather than the outer
    expression opened after the colon.
    """
    stack = []
    for place, character in enumerate(line):
        if character in OPENING:
            stack.append([character, place, 0])
        elif character == "," and stack:
            stack[-1][2] += 1
        elif character in CLOSING and stack:
            stack.pop()
    return any(
        opening in "[(" and commas == 1 and SET_OPERAND.search(line[:place])
        for opening, place, commas in stack
    )


def split_sets(lines):
    """The lines of one sheet that split a set whose print contains a space: a
    line that ends in a word opening one, and a line that ends within a bracket
    where it leaves the arrow or product of the map dangling. A leading arrow
    or product remains attached to its right-hand operand and is a valid
    continuation. The depth is carried from line to line, since a set wider
    than the line stands on several, and starts again at a blank line. A card's
    `Source` rows and the keyed rows under the line that opens the section
    `BLOCK LINES` of a definitions listing reproduce authored source, whose
    annotation may end a wrapped line with `[id=...,`; those rows and their
    continuations are not mathematical display rows and do not contribute
    bracket depth."""
    found, depth = [], 0
    card = bool(lines and lines[0].startswith(("STAGE ", "METHOD !")))
    block_lines = False
    authored = False
    for line in lines:
        rule = SECTION_HAIRLINE.match(line)
        if rule:
            block_lines = rule.group("label").startswith("BLOCK LINES ")
            authored = False
        if block_lines:
            keyed_source = re.match(r"^  \S+ {3,}\S", line)
            if keyed_source:
                authored = True
            elif authored and line.lstrip().startswith(("conditions ", "where ")):
                authored = False
            if authored:
                depth = 0
                continue
        if card:
            heading = _heading_word(line)
            if heading is not None:
                authored = heading == "Source"
            if _is_line(line, HAIRLINE) or _is_line(line, HEAVY):
                authored = False
                depth = 0
                continue
            if authored:
                depth = 0
                continue
        if not line.strip():
            depth = 0
        for character in line:
            depth += (character in OPENING) - (character in CLOSING)
        depth = max(depth, 0)
        if (
            SPLIT_SET.search(line)
            or _split_interval(line)
            or (depth and SPLIT_MAP_END.search(line))
        ):
            found.append(line)
    return found


class Unparsed(Exception):
    """A printed sheet or card does not follow the layout that the parser
    reads."""


def parse_one_sheet(text):
    """One sheet as its parts: `address`, `stamp`, `subtitle`, `sections`
    (label to its lines) and `complete` (label to whether the line that opens
    its section ends in the hairline and not in dashes).

    A subtitle wider than the width wraps under its own column, as the
    address does, so it stands on more than one line of the title block and
    is read back whole here: the break falls after a `/` of a path, which
    drops nothing, or at a space, which drops the space."""
    lines = text.splitlines()
    if lines and lines[0].startswith(("STAGE ", "METHOD !")):
        return parse_card(text)
    heavy = next((index for index, line in enumerate(lines) if set(line) == {HEAVY}), None)
    if heavy is None or len(lines[heavy]) != WIDTH:
        raise Unparsed("no heavy line of 78 columns closes the title block")
    # the address wraps under its own column and so does the subtitle, and the
    # stamp stands on a line of its own where it fits on neither, so a title
    # block holds the address's lines, the subtitle's and at most one more
    if not 1 <= heavy <= 5:
        raise Unparsed(f"the title block holds {heavy} lines, not between one and five")
    for line in lines[:heavy]:
        # the address and the subtitle obey the width as every other line does
        if len(line) > WIDTH:
            raise Unparsed(
                f"a line of the title block is {len(line)} columns, not at most {WIDTH}"
            )
    title = [line for line in lines[:heavy]]
    stamp, key = None, None
    for index, line in enumerate(title):
        found = STAMP.search(line)
        if found:
            if found.group("key") not in STAMP_KEYS:
                raise Unparsed(f"the stamp key {found.group('key')!r} is none of {STAMP_KEYS}")
            stamp, key = found.group("value"), found.group("key")
            title[index] = line[: found.start()].rstrip()
    address = title[0]
    if not address.startswith("BELLMAN-SYM / "):
        raise Unparsed(f"the address {address!r} does not open with the sheet's own name")
    subtitle = None
    for line in [line for line in title[1:] if line]:
        if subtitle is None:
            subtitle = line
        else:
            subtitle += line if subtitle.endswith("/") else " " + line
    sections, complete, label = {}, {}, None
    for line in lines[heavy + 1 :]:
        found = SECTION_HAIRLINE.match(line)
        if found:
            label = found.group("label").strip()
            if len(line) != WIDTH:
                raise Unparsed(f"the hairline of {label!r} is {len(line)} columns, not {WIDTH}")
            sections[label] = []
            complete[label] = line.rstrip()[-1] == HAIRLINE
        elif line.strip():
            if label is None:
                sections.setdefault("", []).append(line)
            else:
                sections[label].append(line)
    return {
        "address": address,
        "stamp": stamp,
        "key": key,
        "subtitle": subtitle,
        "sections": sections,
        "complete": complete,
    }


def card_heading(line):
    """The heading a line at column zero opens, `(heading, file)`, the file
    being the one the heading of `Source` names after two spaces and None for
    every other heading; None for a line that stands in a section. A line at
    column zero that opens no section of `CARD_SECTIONS` or `CARD_FOOTERS` is
    refused."""
    if not line or line[0].isspace():
        return None
    if line in CARD_SECTIONS + CARD_FOOTERS:
        return line, None
    word, gap, file = line.partition("  ")
    if word == "Source" and file and file == file.strip() and " " not in file:
        return word, file
    raise Unparsed(f"unknown card section {line!r}")


def parse_card(text, width=WIDTH):
    """Read a card back by the layout of a card, independently of the
    package, and return its parts.

    A card has this layout:

    1. the title;
    2. the heavy line of 78 columns under it;
    3. the sections, each opened by its heading at column zero and holding
       its content two columns in;
    4. one blank line between two sections and between two entries of
       `Operations`, and nowhere else;
    5. the light line of 78 columns between the last section of the body and
       the first of the footer, with no blank line on either side of it;
    6. the heavy line that closes the card;
    7. no line over the width;
    8. no dotted line, double line or rail;
    9. no line at column two that is the continuation of an entry.

    The parts are `address`, the title; `sections`, each heading to the lines
    of its content, the blank lines between two entries of `Operations` kept
    as empty lines; `order`, the headings in the order they stand; and
    `file`, the file that the heading of `Source` names. With `width=None`
    the width is not read, for a reader of the sections alone."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith(("STAGE ", "METHOD !")):
        raise Unparsed("a card names its stage or method")
    heavy = next((i for i, line in enumerate(lines) if _is_line(line, HEAVY)), None)
    if heavy is None:
        raise Unparsed(
            "a card separates its title from its sections by a heavy line of 78 columns"
        )
    if heavy == len(lines) - 1 or not _is_line(lines[-1], HEAVY):
        raise Unparsed("a heavy line of 78 columns closes a card")
    for line in lines:
        if width is not None and len(line) > width:
            raise Unparsed(f"a card line exceeds {width} columns: {line!r}")
        for glyph, name in REFUSED_CARD_GLYPHS.items():
            if glyph in line:
                raise Unparsed(f"a card prints no {name}: {line!r}")
    sections, order, heading, footer, blank, file = {}, [], None, False, False, None
    for line in lines[heavy + 1 : -1]:
        if not line:
            if heading is None or blank or not sections[heading]:
                raise Unparsed(
                    "one blank line stands between two sections or two entries, and nowhere else"
                )
            blank = True
            continue
        if _is_line(line, HAIRLINE):
            if footer or heading is None:
                raise Unparsed("one light line stands between the body of a card and its footer")
            if blank:
                raise Unparsed("no blank line stands before the light line")
            footer, heading = True, None
            continue
        found = card_heading(line)
        if found is not None:
            word, named = found
            if word in sections:
                raise Unparsed(f"the section {word!r} stands twice")
            if heading is not None and not blank:
                raise Unparsed(f"a blank line separates the section {word!r} from {heading!r}")
            if (word in CARD_FOOTERS) != footer and not (word in CARD_FOOTERS and not sections):
                raise Unparsed(f"the section {word!r} stands on the wrong side of the light line")
            footer = footer or word in CARD_FOOTERS
            heading, blank, file = word, False, named if named is not None else file
            order.append(word)
            sections[word] = []
            continue
        if heading is None:
            raise Unparsed(f"a line stands under no section: {line!r}")
        if not line.startswith(" " * INDENT):
            raise Unparsed(f"the content of a section stands two columns in: {line!r}")
        if (
            line[INDENT] != " "
            and line[INDENT] in CONTINUATION_START
            and not (heading == "Rule" and line.startswith(" " * INDENT + "∧ "))
        ):
            # an entry's continuation stands deeper than column two; a line
            # at that column opening with a sign or a closing bracket
            # continues the entry above it and is refused. Under `Rule`, the
            # rule of a piece card, whose own column is column two, a later
            # member of a conjunction opens with `∧ ` at that column, as it
            # does at the rule's column of a builder card.
            raise Unparsed(f"a continuation stands at column {INDENT}: {line!r}")
        if blank:
            # a blank line followed by a line of the same section separates
            # two entries, which only `Operations` holds
            if heading != "Operations":
                raise Unparsed(f"a blank line stands inside the section {heading!r}")
            sections[heading].append("")
        blank = False
        sections[heading].append(line)
    if blank:
        raise Unparsed("no blank line stands before the heavy line that closes a card")
    return {
        "address": " ".join(line.strip() for line in lines[:heavy]),
        "stamp": None,
        "key": None,
        "subtitle": None,
        "sections": sections,
        "order": order,
        "file": file,
        "complete": {key: True for key in sections},
    }


# the first line of an entry of `Operations`: its number, right-aligned, and
# its key after it; a sub-builder's entry carries a key and no number
ENTRY_LINE = re.compile(r"^(?:(?P<number>\d+) +)?(?P<key>\S+)$")


# the row of an entry: `in:` and what the entry reads, then, after a run of
# spaces, `out:` and what it produces, where both stand on one line
ROW = re.compile(r"^(?P<inputs>in:(?: .*?)?)(?: {2,}(?P<outputs>out:(?: .*)?))?$")


def operations_entries(lines):
    """The entries of an `Operations` section in order, each a mapping: its
    `number` (None for a sub-builder's entry) and `key`, and `at`, the column
    its first line opens at; the `direction` it stands under on the stage's
    card (None elsewhere); `inputs` and `outputs`, the texts after `in:` and
    `out:`, a line under either continuing it; `in_at` and `out_at`, the
    columns of `in:` and `out:`, and `out_line`, whether `out:` stands on a
    line of its own; `short`, the first and the end column of its short line;
    `rule_at`, the column of the label `rule:`; `rule`, the lines of its rule
    from the column of the rule's text; and `lines`, every line of the entry
    as printed. The entries are the runs of lines between the blank lines of
    the section, a direction's word opening a run of the stage's card; a line
    an entry has no place for is refused."""
    entries, direction, opening = [], None, True
    for line in lines:
        if not line:
            opening = True
            continue
        at = len(line) - len(line.lstrip(" "))
        body = line.strip()
        if opening:
            if body in DIRECTIONS:
                direction = body
                continue
            opened = ENTRY_LINE.match(body)
            if opened is None:
                raise Unparsed(f"an entry of `Operations` opens with its number and key: {line!r}")
            entries.append(
                {
                    "number": opened.group("number"),
                    "key": opened.group("key"),
                    "at": at,
                    "direction": direction,
                    "inputs": None,
                    "outputs": None,
                    "in_at": None,
                    "out_at": None,
                    "out_line": False,
                    "short": None,
                    "rule_at": None,
                    "rule": [],
                    "lines": [line],
                    "last": None,
                }
            )
            opening = False
            continue
        entry = entries[-1]
        entry["lines"].append(line)
        if is_short_line(line):
            if entry["short"] is not None or entry["inputs"] is None:
                raise Unparsed(f"one short line stands under the row of {entry['key']!r}")
            entry["short"] = (at, len(line))
        elif entry["short"] is None:
            row = ROW.match(body)
            if row is not None and entry["inputs"] is None:
                entry["in_at"] = at
                entry["inputs"] = row.group("inputs")[len("in:") :].strip()
                entry["last"] = "inputs"
                if row.group("outputs") is not None:
                    entry["out_at"] = line.index("out:", at + len("in:"))
                    entry["outputs"] = row.group("outputs")[len("out:") :].strip()
                    entry["last"] = "outputs"
            elif (
                body.startswith("out:")
                and entry["inputs"] is not None
                and entry["outputs"] is None
            ):
                entry["out_at"], entry["out_line"] = at, True
                entry["outputs"] = body[len("out:") :].strip()
                entry["last"] = "outputs"
            elif entry["last"] is not None and at > entry["in_at"]:
                entry[entry["last"]] = (entry[entry["last"]] + " " + body).strip()
            else:
                raise Unparsed(
                    f"a line of the row of {entry['key']!r} is no `in:` or `out:` line: {line!r}"
                )
        elif body.startswith("rule:") and not entry["rule"]:
            entry["rule_at"] = at
            entry["rule"].append(line[at + len("rule: ") :])
        elif entry["rule"] and at >= entry["rule_at"] + len("rule: "):
            entry["rule"].append(line[entry["rule_at"] + len("rule: ") :])
        else:
            raise Unparsed(
                f"a line under the short line of {entry['key']!r} is no rule line: {line!r}"
            )
    for entry in entries:
        del entry["last"]
    return entries


def label_and_content(line):
    """The label and the content of one line of a section, or (None, content)
    where the line stands in the content column alone."""
    if not line.startswith("  "):
        raise Unparsed(f"a section line is indented by two columns; got {line!r}")
    body = line[2:]
    split = re.match(r"^(?P<label>\S(?:\S| (?=\S))*)(?P<gap> {1,})(?P<content>\S.*)$", body)
    if split is None:
        return None, body.strip()
    return split.group("label"), split.group("content")


def sheets_of(stage):
    """Every sheet of one stage occurrence, by its address: the stage, its
    card (`stage.denote()`), the four graphs at the builder grain and at the
    primitive grain, every builder and block, every operator, the definitions
    listing and every record."""
    made = {}

    def add(text):
        # keyed by the sheet's whole title block, since an address of more than
        # 78 columns wraps and two sheets can open with the same first line
        heavy = next(
            (index for index, line in enumerate(text.splitlines()) if set(line) == {"━"}), 1
        )
        made[" ".join(text.splitlines()[:heavy])] = text

    add(str(stage))
    add(str(stage.denote()))
    add(str(stage.definitions.list()))
    for handle in (
        stage.initial.backward,
        stage.initial.forward,
        stage.builder.bwd,
        stage.builder.fwd,
    ):
        try:
            handle.graph
        except Exception:
            continue  # a refused graph holds no sheet
        add(str(handle))
        add(str(handle.primitives))
        for name in handle.list():
            piece = handle[name]
            add(str(piece))
            inside = getattr(piece, "list", None)
            for inner in inside() if inside is not None else ():
                add(str(piece[inner]))
    for identity in stage.definitions:
        add(str(stage.definitions.denote(identity)))
    return made


def parse_every_sheet(stage):
    """Read every sheet of a stage back and report what could not be read: the
    sheets that `parse_one_sheet` cannot read, the lines wider than 78 columns,
    the lines that end in a space and the lines that split a set whose print
    contains a space."""
    return parse_sheets(sheets_of(stage))


def parse_sheets(sheets):
    """The report of `parse_every_sheet` on sheets already printed: `sheets`
    maps each sheet's address to its text, as `sheets_of` gives it."""
    unparsed, over, trailing, split = [], [], [], []
    for address, text in sheets.items():
        split.extend((address, line) for line in split_sets(text.splitlines()))
        for line in text.splitlines():
            if len(line) > WIDTH:
                over.append((address, line))
            if line != line.rstrip():
                trailing.append((address, line))
        try:
            parsed = parse_one_sheet(text)
            if "order" not in parsed:
                for label, lines in parsed["sections"].items():
                    for line in lines:
                        label_and_content(line)
            if parsed["key"] is not None and parsed["stamp"] is None:
                raise Unparsed("a stamp key with no value")
        except Unparsed as refusal:
            unparsed.append((address, str(refusal)))
    return {
        "sheets": len(sheets),
        "unparsed": unparsed,
        "over_width": over,
        "trailing": trailing,
        "split_set": split,
    }


def card_shown_on_the_page(path, title):
    """The fenced text block of the example page `path` that opens with
    `title`."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    start = lines.index(title)
    return "\n".join(
        lines[start : next(i for i in range(start, len(lines)) if lines[i].strip() == "```")]
    )


# the five sections of a card beside its operations and its signature, which
# `differing_card_sections` compares
COMPARED_CARD_SECTIONS = ("At", "Where", "Conditions", "Source", "Definitions referenced")


def differing_card_sections(builder, example):
    """The sections in which the printed card of `builder` differs from the
    card `example` that an example page shows, `[]` where none differs: the
    keys of the operations, the signature as a set of lines without white
    space, the five other sections without white space, and the rules of the
    operations joined."""
    card = str(builder)
    keys = [
        match.group(1)
        for line in card_section_lines(example, "Operations")
        for match in [re.match(r"^\s+\d+\s+(\S+)$", line)]
        if match
    ]
    found = [] if [str(key) for key in builder.primitives.list()] == keys else ["keys"]
    if {flat(line) for line in card_section_lines(card, "Signature")[1:]} != {
        flat(line) for line in card_section_lines(example, "Signature")[1:]
    }:
        found.append("signature")
    found += [
        heading
        for heading in COMPARED_CARD_SECTIONS
        if flat("\n".join(card_section_lines(card, heading)))
        != flat("\n".join(card_section_lines(example, heading)))
    ]
    return found + (
        []
        if operation_rules(card_section_lines(card, "Operations"))
        == operation_rules(card_section_lines(example, "Operations"))
        else ["rules"]
    )
