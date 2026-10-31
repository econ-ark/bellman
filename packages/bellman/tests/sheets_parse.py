"""Read every sheet of a stage back, as §2 of AMD-SG-015 promises a machine.

A sheet is text the package writes from the objects of a stage occurrence. This
reader takes that text alone and recovers what §2 says is in it: the address,
the stamp and its key, the subtitle, the sections under their labels, the label
and content columns of each line, the wires one to a line, and the words of the
kinds table. A card is read by its own grammar, the form of the card of the
internal developer release 0.01 (`card-redesign.md` §2): the title, the heavy
line of 78 columns under it, the sections each opened by its heading at column
zero with their content two columns in, one blank line between two sections
and between two entries of `Operations` and nowhere else, one light line across
the card before the sections of its footer, and the heavy line that closes the
card. The readers after the grammar take a section apart: an entry of
`Operations` into its number and key, its `in:` and `out:` line, its short line
and its rule lines; a row of `Source` into its line number and its statement;
a row of `Definitions referenced` into its name and key. It reads no object and
imports nothing of the package, so what it recovers is what a reader with the
sheet and no page would recover.

Run it over the corpus from `packages/bellman`:

    PYTHONPATH=. python tests/sheets_parse.py
"""
from __future__ import annotations

import re

WIDTH = 78
HEAVY, HAIRLINE, DASHED = "━", "─", "┄"
STAMP = re.compile(r"\[(?P<key>[A-Z]+) = (?P<value>[^\]]+)\]$")
STAMP_KEYS = ("VERSION", "GRAIN", "KIND", "RECORDS", "WIRES")
# a section rule: its label, a space, then the rule to column 78. A label is the
# section's word in capitals, or the name of the builder, block, sub-builder or
# primitive whose section it opens, with the arrow of its direction where it has
# one (AMD-SG-015 §§2, 4.2)
RULE = re.compile(rf"^(?P<label>(?:[←→] )?\S[^\s{HAIRLINE}{DASHED}]*(?: [A-Z][^\s{HAIRLINE}{DASHED}]*)*"
                  rf"(?: \d+)?) [{HAIRLINE}{DASHED}]+$")


# A set whose print contains a space is never broken across lines (§2), so no
# line ends in a word that opens one.
SPLIT_SET = re.compile(r"range not$")
SET_OPERAND = re.compile(r"[:×→] $")
# A wrapped set keeps an arrow or product sign with its right-hand operand, so
# a continuation may begin `→ Y` or `× Y`. The operator must not instead be
# left dangling at the end of the preceding line.
SPLIT_MAP_END = re.compile(r" [→×]$")
OPENING, CLOSING = "([{", ")]}"

# The three kinds of line a card prints (card-redesign.md §2, change 5): the
# heavy line under the title and at the foot, one light line across the card
# before the footer, and the short lines, which stand under the row of an entry
# of `Operations` and above the `out` row of `Signature` and end at the card's
# one end column. The dotted line, the double line and the rail of the earlier
# card print on no card.
LIGHT = HAIRLINE
RETIRED = {"┈": "dotted line", "═": "double line", "│": "rail"}
# the content of a section stands two columns in (change 1)
INDENT = 2
# the columns of an entry of `Operations` on a builder's card (change 2): its
# number at column two and its key at column five, its `in:`, its short line
# and the label `rule:` at column five, `out:` at column forty or on a line of
# its own, the text of the rule at column eleven
OUT, RULE_TEXT = 40, 11
# the columns of a row of `Signature`: the word `in` or `out` at column two,
# the name at column seven, where its short line starts as well
WIRE = 7
# the sections of a card that stand before the light line, and those of the
# footer after it, each opened by its heading; the heading of `Source` names
# the file after two spaces
CARD_SECTIONS = ("Signature", "Defines", "At", "Where", "Declared", "Rule", "Operations",
                 "Conditions", "Method", "Options", "Admits", "Derivation")
CARD_FOOTERS = ("Source", "Definitions referenced", "File", "Perches", "Appendix")
# the words that name a direction on the stage's card, in `Signature` and in
# `Operations`
DIRECTIONS = ("backward", "forward")
# the characters an entry's continuation opens with, since the engine breaks
# before a binary sign or after a comma and never before a closing bracket: a
# line at column two opening with one of them is a continuation standing
# where an entry stands, and is refused (a negation `¬` opens an entry)
CONTINUATION_START = "=≤≥<>∈∉+−·/×→↦∧∨⊆⟂∘)]}"
# the characters of a name, which may precede the bracket of an application:
# word characters, the perch marks, a prime and the subscript digits
NAME_CHARACTERS = "≺≻′₀₁₂₃₄₅₆₇₈₉"


def _is_line(line, character):
    """Whether `line` is the full-width line of `character`."""
    return len(line) == WIDTH and set(line) == {character}


def _is_short_line(line):
    """Whether `line` is a short line: spaces, then a light line narrower than
    the card."""
    body = line.lstrip(" ")
    return bool(body) and set(body) == {LIGHT} and line != body


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
    return any(opening in "[(" and commas == 1
               and SET_OPERAND.search(line[:place])
               for opening, place, commas in stack)


def split_sets(lines):
    """The lines of one sheet that split a set whose print contains a space: a
    line that ends in a word opening one, and a line that ends within a bracket
    where it leaves the arrow or product of the map dangling. A leading arrow
    or product remains attached to its right-hand operand and is a valid
    continuation. The depth is carried from line to line, since a set wider
    than the line stands on several, and starts again at a blank line. A card's
    `Source` rows and the keyed rows under a definitions listing's `BLOCK
    LINES` rule reproduce authored source, whose annotation may end a wrapped
    line with `[id=...,`; those rows and their continuations are not
    mathematical display rows and do not contribute bracket depth."""
    found, depth = [], 0
    card = bool(lines and lines[0].startswith(("STAGE ", "METHOD !")))
    block_lines = False
    authored = False
    for line in lines:
        rule = RULE.match(line)
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
            if _is_line(line, LIGHT) or _is_line(line, HEAVY):
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
        if (SPLIT_SET.search(line) or _split_interval(line)
                or (depth and SPLIT_MAP_END.search(line))):
            found.append(line)
    return found


class Unparsed(Exception):
    """The sheet does not read as §2 says a sheet reads."""


def parse(text):
    """One sheet as its parts: `address`, `stamp`, `subtitle`, `sections` (label
    to its lines) and `complete` (label to whether its rule is a hairline).

    A subtitle wider than the width wraps under its own column, as the address
    does, so it stands on more than one line of the title block and is read back
    whole here: the break falls after a `/` of a path, which drops nothing, or at
    a space, which drops the space."""
    lines = text.splitlines()
    if lines and lines[0].startswith(("STAGE ", "METHOD !")):
        return parse_card(text)
    heavy = next((index for index, line in enumerate(lines) if set(line) == {HEAVY}), None)
    if heavy is None or len(lines[heavy]) != WIDTH:
        raise Unparsed("no heavy rule of 78 columns closes the title block")
    # the address wraps under its own column and so does the subtitle, and the
    # stamp stands on a line of its own where it fits on neither, so a title
    # block holds the address's lines, the subtitle's and at most one more
    if not 1 <= heavy <= 5:
        raise Unparsed(f"the title block holds {heavy} lines, not between one and five")
    for line in lines[:heavy]:
        # the address and the subtitle obey the width as every other line does
        if len(line) > WIDTH:
            raise Unparsed(f"a line of the title block is {len(line)} columns, not at most {WIDTH}")
    title = [line for line in lines[:heavy]]
    stamp, key = None, None
    for index, line in enumerate(title):
        found = STAMP.search(line)
        if found:
            if found.group("key") not in STAMP_KEYS:
                raise Unparsed(f"the stamp key {found.group('key')!r} is none of {STAMP_KEYS}")
            stamp, key = found.group("value"), found.group("key")
            title[index] = line[:found.start()].rstrip()
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
    for line in lines[heavy + 1:]:
        found = RULE.match(line)
        if found:
            label = found.group("label").strip()
            if len(line) != WIDTH:
                raise Unparsed(f"the rule of {label!r} is {len(line)} columns, not {WIDTH}")
            sections[label] = []
            complete[label] = line.rstrip()[-1] == HAIRLINE
        elif line.strip():
            if label is None:
                sections.setdefault("", []).append(line)
            else:
                sections[label].append(line)
    return {"address": address, "stamp": stamp, "key": key, "subtitle": subtitle,
            "sections": sections, "complete": complete}


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
    """Read a card back by the grammar of `card-redesign.md` §2, independently
    of Bellman: the title, the heavy line of 78 columns under it, the sections
    each opened by its heading at column zero and holding its content two
    columns in, one blank line between two sections and between two entries
    of `Operations` and nowhere else, the light line of 78 columns between the
    last section of the body and the first of the footer, with no blank line
    on either side of it, the heavy line closing the card, no line over the
    width, no dotted line, double line or rail, and no line at column two that
    is the continuation of an entry. The parts: `address`, the title;
    `sections`, each heading to the lines of its content, the blank lines
    between two entries of `Operations` kept as empty lines; `order`, the
    headings in the order they stand; and `file`, the file the heading of
    `Source` names. With `width=None` the width is not read, for a reader of
    the sections alone."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith(("STAGE ", "METHOD !")):
        raise Unparsed("a card names its stage or method")
    heavy = next((i for i, line in enumerate(lines) if _is_line(line, HEAVY)), None)
    if heavy is None:
        raise Unparsed("a card separates its title from its sections by a heavy line of 78 columns")
    if heavy == len(lines) - 1 or not _is_line(lines[-1], HEAVY):
        raise Unparsed("a heavy line of 78 columns closes a card")
    for line in lines:
        if width is not None and len(line) > width:
            raise Unparsed(f"a card line exceeds {width} columns: {line!r}")
        for glyph, name in RETIRED.items():
            if glyph in line:
                raise Unparsed(f"a card prints no {name}: {line!r}")
    sections, order, heading, footer, blank, file = {}, [], None, False, False, None
    for line in lines[heavy + 1:-1]:
        if not line:
            if heading is None or blank or not sections[heading]:
                raise Unparsed("one blank line stands between two sections or two entries, and nowhere else")
            blank = True
            continue
        if _is_line(line, LIGHT):
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
        if line[INDENT] != " " and line[INDENT] in CONTINUATION_START and not (
                heading == "Rule" and line.startswith(" " * INDENT + "∧ ")):
            # an entry's continuation stands deeper than column two; a line
            # at that column opening with a sign or a closing bracket
            # continues the entry above it and is refused. Under `Rule`, the
            # rule of a piece card, whose own column is column two, a later
            # member of a conjunction opens with `∧ ` at that column, as it
            # does at the rule's column of a builder card (CL154 of the
            # release's decisions)
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
    return {"address": " ".join(line.strip() for line in lines[:heavy]),
            "stamp": None, "key": None, "subtitle": None, "sections": sections,
            "order": order, "file": file, "complete": {key: True for key in sections}}


# the first line of an entry of `Operations`: its number, right-aligned, and its
# key after it; a sub-builder's entry carries a key and no number
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
            entries.append({"number": opened.group("number"), "key": opened.group("key"), "at": at,
                            "direction": direction, "inputs": None, "outputs": None,
                            "in_at": None, "out_at": None, "out_line": False, "short": None,
                            "rule_at": None, "rule": [], "lines": [line], "last": None})
            opening = False
            continue
        entry = entries[-1]
        entry["lines"].append(line)
        if _is_short_line(line):
            if entry["short"] is not None or entry["inputs"] is None:
                raise Unparsed(f"one short line stands under the row of {entry['key']!r}")
            entry["short"] = (at, len(line))
        elif entry["short"] is None:
            row = ROW.match(body)
            if row is not None and entry["inputs"] is None:
                entry["in_at"] = at
                entry["inputs"] = row.group("inputs")[len("in:"):].strip()
                entry["last"] = "inputs"
                if row.group("outputs") is not None:
                    entry["out_at"] = line.index("out:", at + len("in:"))
                    entry["outputs"] = row.group("outputs")[len("out:"):].strip()
                    entry["last"] = "outputs"
            elif body.startswith("out:") and entry["inputs"] is not None and entry["outputs"] is None:
                entry["out_at"], entry["out_line"] = at, True
                entry["outputs"] = body[len("out:"):].strip()
                entry["last"] = "outputs"
            elif entry["last"] is not None and at > entry["in_at"]:
                entry[entry["last"]] = (entry[entry["last"]] + " " + body).strip()
            else:
                raise Unparsed(f"a line of the row of {entry['key']!r} is no `in:` or `out:` line: {line!r}")
        elif body.startswith("rule:") and not entry["rule"]:
            entry["rule_at"] = at
            entry["rule"].append(line[at + len("rule: "):])
        elif entry["rule"] and at >= entry["rule_at"] + len("rule: "):
            entry["rule"].append(line[entry["rule_at"] + len("rule: "):])
        else:
            raise Unparsed(f"a line under the short line of {entry['key']!r} is no rule line: {line!r}")
    for entry in entries:
        del entry["last"]
    return entries


def signature_wires(lines):
    """The wires of a `Signature` section, one per row, `(word, name,
    carrier)`: the word `in` or `out`, carried down to the rows under it, the
    name five columns after the word, where every further name under the
    word stands, and the carrier after ` : `; a deeper line continues the
    carrier of the row above, and a line opening with `: ` gives the carrier
    of a name too long for its column. The short line and the words of the
    directions on the stage's card are no rows."""
    found, word, name_at = [], None, None
    for line in lines:
        body = line.strip()
        if not body or _is_short_line(line) or body in DIRECTIONS:
            continue
        at = len(line) - len(line.lstrip(" "))
        label = re.match(r"(in|out)(?: {2,}(?=\S)|$)", body)
        if label is not None and (name_at is None or at < name_at):
            word, name_at = label.group(1), at + WIRE - INDENT
        elif name_at is None or at != name_at:
            if found and body.startswith(": "):
                found[-1][2] = body[2:]
            elif found:
                found[-1][2] = (found[-1][2] + " " + body).strip()
            else:
                raise Unparsed(f"a row of `Signature` opens with `in` or `out`: {line!r}")
            continue
        name, colon, carrier = line[name_at:].partition(" : ")
        found.append([word, name.strip(), carrier.strip()])
    return [tuple(entry) for entry in found]


# the first line of a row of `Source`: its key, the number of a line of the
# file the heading names or, on a refused graph's card, the word `rule` or
# `reason`, then the statement after a run of spaces
SOURCE_ROW = re.compile(r"^ +(?P<key>\d+|[a-z]+) {2,}(?P<statement>\S.*)$")


def source_rows(lines):
    """The rows of a `Source` section, each `(key, statement)`: the number of
    the line in the file the heading names, or the word of a refused graph's
    row, and the statement as written, with every line under the row that
    stands deeper than its key, the rest of a statement and its annotation
    `:: [...]`, joined to it by a space."""
    rows, column = [], None
    for line in lines:
        at = len(line) - len(line.lstrip(" "))
        opened = SOURCE_ROW.match(line)
        if opened is not None and (column is None or at < column):
            key = opened.group("key")
            rows.append([int(key) if key.isdigit() else key, opened.group("statement")])
            column = opened.start("statement")
        elif rows and at >= column:
            rows[-1][1] = rows[-1][1] + " " + line.strip()
        else:
            raise Unparsed(f"a line of `Source` stands under no row: {line!r}")
    return [tuple(row) for row in rows]


def definition_rows(lines):
    """The rows of `Definitions referenced`, each `(name, key)`: the name the
    card writes at column two and, after a run of spaces, the key of its
    definition."""
    rows = []
    for line in lines:
        found = re.match(r"^  (?P<name>\S(?:.*?\S)?) {2,}(?P<key>\S+)$", line)
        if found is None:
            raise Unparsed(f"a row of `Definitions referenced` is a name and a key: {line!r}")
        rows.append((found.group("name"), found.group("key")))
    return rows


def condition_rows(lines, owned):
    """The rows of a `Conditions` section, each `(owner, term)`: a row opens
    at column two, its owner (where the section has an owner column, `owned`)
    ends at the first run of two spaces, and a line that starts deeper
    continues the term of the row above; a term that does not fit beside its
    owner stands from the next line."""
    rows = []
    for line in lines:
        body = line[INDENT:]
        if line.startswith(" " * (INDENT + 1)) and rows:
            rows[-1][1] = (rows[-1][1] + " " + body.strip()).strip()
            continue
        parts = re.split(r" {2,}", body, maxsplit=1)
        if len(parts) == 2:
            rows.append([parts[0], parts[1]])
        elif owned:
            rows.append([parts[0], ""])
        else:
            rows.append(["", parts[0]])
    return [tuple(row) for row in rows]


# a name: word characters, the perch marks `≺` and `≻`, a prime and an
# underscore, as `𝑔≻`, `𝐺_value≻` and `c′` are spelled, and a name after a
# comma directly following the mark, as a local abbreviation is spelled,
# `A≻,policy` (AMD-SG-034 §4 item 11)
NAME = re.compile(r"[\w≺≻′]+(?:_[\w≺≻′]+)*(?:,[\w′]+(?:_[\w′]+)*)*", re.UNICODE)


def card_body(text):
    """The body of a card, its title and its sections before the light line
    or the first section of its footer, as one text."""
    body = []
    for line in text.splitlines():
        if _is_line(line, LIGHT) or _heading_word(line) in CARD_FOOTERS:
            break
        body.append(line)
    return "\n".join(body)


def written_names(body):
    """The runs of name characters on the body of a card: a declared name
    stands as one such run; `∘` and every operator glyph separate two, and so
    does a comma followed by a space, while a comma inside a run spells an
    abbreviation at a policy."""
    cleaned = re.sub(r"[∘×→↦∈∉≤≥=+−·/^()\[\]{}|:~∀∃∧∨¬∫⊆]|, ", " ", body)
    return set(NAME.findall(cleaned))


def short_lines(text):
    """The short lines of a card, each as its first and its end column."""
    return [(len(line) - len(line.lstrip(" ")), len(line))
            for line in text.splitlines() if _is_short_line(line)]


def _head_start(line, place):
    """The column at which the head of the application whose bracket stands at
    `place` begins: over the characters of a name, the product sign of a
    measure extended by a declared law, `μ⊗P_{Ψ, θ}`, which prints as one
    name, the colons and dots of a key such as `objective:Expectation:1`,
    and every bracketed group before them, so that `(𝑉≻ ∘ 𝑔≻)(…)`,
    `solve_{c}(…)`, `P_{Ψ|ν}(ν)(…)` and `μ⊗P_{Ψ, θ}({…})` are read whole;
    None where the bracket follows no head and opens a group or a tuple."""
    start = place
    while start:
        before = line[start - 1]
        if before in CLOSING:
            opening, depth = OPENING[CLOSING.index(before)], 0
            for index in range(start - 1, -1, -1):
                depth += (line[index] == before) - (line[index] == opening)
                if depth == 0:
                    start = index
                    break
            else:
                break
        elif before.isalnum() or before in "_:.⊗" + NAME_CHARACTERS:
            start -= 1
        else:
            break
    return start if start < place else None


def broken_applications(text, column=RULE_TEXT, width=WIDTH):
    """The applications `f(…)` of a card broken inside their argument list
    whose text on one line would fit within the width at `column`, the column
    of a rule's text: each as that one-line text. An application is a bracket
    that directly follows a name or a bracketed head; its text on one line
    joins its lines by a space, with no space after the opening bracket or
    before the closing one. The lines of a section are read in runs that a
    blank line, a heading or a short line ends, and the authored statements of
    `Source` are not read."""
    lines = text.splitlines()
    heavy = next((i for i, line in enumerate(lines) if _is_line(line, HEAVY)), len(lines))
    runs, run, authored = [], [], False
    for line in lines[heavy + 1:]:
        heading = _heading_word(line)
        if heading is not None or not line.strip() or _is_short_line(line):
            if heading is not None:
                authored = heading == "Source"
            if run:
                runs.append(run)
            run = []
        elif not authored:
            run.append(line)
    if run:
        runs.append(run)
    found = []
    for run in runs:
        # each open bracket as [whether it opens an application, the run's
        # line it opens on, the text read since its head]
        stack = []
        for number, line in enumerate(run):
            if number:
                for frame in stack:
                    frame[2].append(" ")
            body = line.lstrip(" ")
            offset = len(line) - len(body)
            for place, character in enumerate(body, offset):
                if character == "(":
                    start = _head_start(line, place)
                    for frame in stack:
                        frame[2].append(character)
                    stack.append([start is not None, number,
                                  [line[place if start is None else start:place + 1]]])
                    continue
                for frame in stack:
                    frame[2].append(character)
                if character == ")" and stack:
                    application, opened, pieces = stack.pop()
                    if application and opened != number:
                        whole = re.sub(r"\s+", " ", "".join(pieces))
                        whole = whole.replace("( ", "(").replace(" )", ")")
                        if len(whole) <= width - column:
                            found.append(whole)
    return found


def columns(line):
    """The label and the content of one line of a section, or (None, content)
    where the line stands in the content column alone."""
    if not line.startswith("  "):
        raise Unparsed(f"a section line is indented by two columns; got {line!r}")
    body = line[2:]
    split = re.match(r"^(?P<label>\S(?:\S| (?=\S))*)(?P<gap> {1,})(?P<content>\S.*)$", body)
    if split is None:
        return None, body.strip()
    return split.group("label"), split.group("content")


def wires(lines):
    """The wires of a section, one to a line: every line whose label is `in` or
    `out`, with its typed text."""
    found = []
    for line in lines:
        label, content = columns(line)
        if label in ("in", "out"):
            found.append((label, content))
    return found


def sheets_of(stage):
    """Every sheet of one stage occurrence, by its address: the stage, its
    card (`stage.denote()`), the four graphs at the two public grains,
    every builder and block, every operator, the definitions listing and
    every record."""
    made = {}

    def add(text):
        # keyed by the sheet's whole title block, since an address of more than
        # 78 columns wraps and two sheets can open with the same first line
        heavy = next((index for index, line in enumerate(text.splitlines())
                      if set(line) == {"━"}), 1)
        made[" ".join(text.splitlines()[:heavy])] = text

    add(str(stage))
    add(str(stage.denote()))
    add(str(stage.definitions.list()))
    for handle in (stage.initial.backward, stage.initial.forward, stage.builder.bwd, stage.builder.fwd):
        try:
            handle.graph
        except Exception:
            continue                          # a refused graph holds no sheet
        add(str(handle))
        add(str(handle.primitives))
        for name in handle.list():
            piece = handle[name]
            add(str(piece))
            inside = getattr(piece, "list", None)
            for inner in (inside() if inside is not None else ()):
                add(str(piece[inner]))
    for identity in stage.definitions:
        add(str(stage.definitions.denote(identity)))
    return made


def parse_every_sheet(stage):
    """Read every sheet of a stage back and report what could not be read: the
    sheets whose parts §2 does not recover, the lines wider than 78 columns, the
    lines that end in a space and the lines that split a set whose print
    contains a space."""
    return parse_sheets(sheets_of(stage))


def parse_sheets(made):
    """The report of `parse_every_sheet` on sheets already printed: `made` maps
    each sheet's address to its text, as `sheets_of` answers it and as the
    fixture `printed_cards` of `conftest.py` holds it."""
    unparsed, over, trailing, split = [], [], [], []
    for address, text in made.items():
        split.extend((address, line) for line in split_sets(text.splitlines()))
        for line in text.splitlines():
            if len(line) > WIDTH:
                over.append((address, line))
            if line != line.rstrip():
                trailing.append((address, line))
        try:
            parsed = parse(text)
            if "order" not in parsed:
                for label, lines in parsed["sections"].items():
                    for line in lines:
                        columns(line)
            if parsed["key"] is not None and parsed["stamp"] is None:
                raise Unparsed("a stamp key with no value")
        except Unparsed as refusal:
            unparsed.append((address, str(refusal)))
    return {"sheets": len(made), "unparsed": unparsed, "over_width": over,
            "trailing": trailing, "split_set": split}


def main():
    import sys
    from pathlib import Path
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    from conftest import CORPUS, corpus_stage
    total = 0
    for name in CORPUS:
        report = parse_every_sheet(corpus_stage(name))
        total += report["sheets"]
        print(f"{name}: {report['sheets']} sheets, {len(report['unparsed'])} unparsed, "
              f"{len(report['over_width'])} lines over {WIDTH} columns, "
              f"{len(report['trailing'])} lines ending in a space, "
              f"{len(report['split_set'])} lines splitting a set")
        for address, reason in report["unparsed"]:
            print(f"    {address}: {reason}")
        for address, line in report["over_width"][:5]:
            print(f"    {address}: {len(line)} columns: {line}")
    print(f"{total} sheets read back")


if __name__ == "__main__":
    main()
