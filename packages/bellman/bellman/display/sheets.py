"""The setting of the stage sheet, a signature and a listing in 78 columns,
and `Sheet`, the text every printed view of a stage is.

A sheet is a title block, a heavy rule and sections, each a label column and
a content column. A line is broken only between complete expressions: never
between the two endpoints of an interval, and never with a product or map
sign apart from the operand after it. The width, the heavy rule and the label
column are those of `bellman.syntax.layout`, which sets a card.
"""

from __future__ import annotations

import re
from collections import namedtuple

from bellman.syntax.layout import HEAVY, LABEL_COLUMN, WIDTH

# the column the lines of a section start at
INDENT = 2
# the brackets that open and close a group, in matching order
OPENING, CLOSING = "([{", ")]}"
# the spaces after the longest label of a section whose labels do not fit the
# label column, which widens to hold them, so that a label and its content are
# never joined
SEPARATION = 3


# --- the sheet, its title block and its section headings ---


class Sheet(str):
    """The text of a printed view of a stage: the stage sheet, the
    definitions sheet or a card. It is a string whose representation is the
    text, so that a bare expression shows the sheet and not a constructor
    call.

    See `docs/Bellman-Sym/API/stage/01-the-stage.md` §3."""

    __repr__ = str.__str__


# One section of a sheet: its label, its lines, and whether its content is
# complete; a tuple of the first two, or of all three, reads as the same
# section.
Section = namedtuple("Section", "label lines complete", defaults=(True,))


def sheet(address, sections, stamp=None, subtitle=None):
    """One sheet: the title block, then the sections in order, each set off by
    a blank line. A section is a `Section`, `(label, lines)` or
    `(label, lines, complete)`. A section with no lines is omitted unless its
    heading is dashed, which says that its content is still to be supplied. A
    section with no label stands under no heading: it holds the graph's own
    wires, which are no section of it."""
    lines = list(title(address, stamp, subtitle))
    for section in (Section(*section) for section in sections):
        content = tuple(section.lines)
        if not content and section.complete:
            continue
        lines.append("")
        if section.label:
            lines.append(section_heading(section.label, section.complete))
        lines.extend(content)
    return Sheet("\n".join(lines))


def title(address, stamp=None, subtitle=None):
    """The title block: the address, the stamp against the right margin of the
    first line it fits on, a subtitle where the piece has a label, and a heavy
    rule of 78 columns.

    A subtitle is a line of the title block as the address is, so a subtitle
    wider than the width wraps under its own column rather than standing over
    it. The sentence naming a stage file breaks before the path where the path
    then fits on one line, and within the path after a `/`, so that no
    component of the path is split."""
    lines = []
    placed = False
    if stamp:
        set_out = with_margin_mark(address, stamp)
        if set_out is not None:
            lines.append(set_out)
            placed = True
    if not placed:
        # an address of more than 78 columns wraps under its own column: it is
        # a name and is never abbreviated
        lines.extend(
            line.lstrip() if index == 0 else line for index, line in enumerate(wrapped(address, 0))
        )
    if subtitle is not None:
        set_out = with_margin_mark(subtitle, stamp) if stamp and not placed else None
        if set_out is not None:
            lines.append(set_out)
            placed = True
        else:
            lines.extend(wrapped(PathLine(subtitle), 0))
    if stamp and not placed:
        lines.append(f"{stamp:>{WIDTH}}")
    lines.append(HEAVY * WIDTH)
    return tuple(lines)


def with_margin_mark(text, mark, gap=1):
    """`text` with `mark` set against the right margin, or None where the two
    do not fit in the width with `gap` columns between them: the stamp of a
    title block beside its address or its subtitle."""
    if len(text) + gap + len(mark) > WIDTH:
        return None
    return f"{text:<{WIDTH - len(mark)}}{mark}"


# the keys of a stamp, the one fact of a sheet a program reads first
STAMP_KEYS = ("VERSION", "GRAIN", "KIND", "RECORDS", "WIRES")


def stamp(key, value):
    """The stamp of a sheet: the one fact a reader wants first, in square
    brackets, `[VERSION = SYMBOLIC]`."""
    if key not in STAMP_KEYS:
        raise ValueError(f"a stamp key is one of {STAMP_KEYS!r}; got {key!r}")
    return f"[{key} = {value}]"


# the line of a section heading, and of the heading of a section whose content
# is still to be supplied
HAIRLINE = "─"
DASHED = "┄"


def section_heading(label, complete=True):
    """A section heading: the label in capitals, a space, then a hairline to
    column 78, or dashes while the section's content is still to be
    supplied."""
    fill = HAIRLINE if complete else DASHED
    head = f"{label} "
    return head + fill * max(0, WIDTH - len(head))


# --- the label column and the content column ---


def label_columns(entries, width=None, separation=SEPARATION, indent=INDENT):
    """Label and content in two columns, one entry per label: the label at
    `indent`, its lines in the right column, and every further line of the same
    entry under that column. An entry whose label is empty prints its content
    in the right column alone. `indent` is the column the pair is laid out
    from: two on the stage sheet, and zero for the lines of a signature.

    Where the label column leaves too few columns for the content — the widest
    part the content can be broken into is wider than what is left, and a set
    and a name are never split — the entry stands with its label on a line of
    its own and its content at `indent + INDENT` below it, and only where that
    column holds it."""
    entries = [
        (label, (content,) if isinstance(content, str) else tuple(content))
        for label, content in entries
    ]
    at = label_column_width(entries, width, separation)
    lines = []
    for label, content in entries:
        broken = [wrapped(text, indent + at) for text in content]
        if label and _over_width(broken):
            below = [wrapped(text, indent + INDENT) for text in content]
            if not _over_width(below):
                lines.append(" " * indent + label)
                lines.extend(line for one in below for line in one)
                continue
        for index, one in enumerate(broken):
            if index == 0 and label:
                head = " " * indent + f"{label:<{at}}"
                lines.append((head + one[0].lstrip()).rstrip())
                lines.extend(one[1:])
            else:
                lines.extend(one)
    return tuple(lines)


def label_column_width(entries, width=None, separation=SEPARATION):
    """The width of one label column: eleven characters, the label column of
    the stage sheet, a signature and a listing, or the longest label with
    `separation` spaces after it where a label does not fit.

    Sections that share one column pass that column as `width`: the stage
    sheet's five upper sections take the longest label of the sheet and one
    space, and a section whose own labels need more widens to its longest and
    two, which is why its graphs section stands one column to the right of its
    perches."""
    labels = [label for label, _ in entries if label]
    return max(
        [LABEL_COLUMN if width is None else width] + [len(label) + separation for label in labels]
    )


def _over_width(groups):
    """Whether any line of the wrapped groups exceeds the width."""
    return any(len(line) > WIDTH for group in groups for line in group)


def unlabeled(lines, indent=INDENT):
    """Content with no label column: one line each at `indent`, wrapped."""
    out = []
    for text in lines:
        out.extend(wrapped(text, indent))
    return tuple(out)


def filled(parts, separator, indent):
    """`parts` joined by `separator` and laid out from `indent`, broken between
    two parts and never inside one: a record's print may contain a space, as
    `(1, inf)` and `range not declared` do, and a break inside one reads as two
    records. A part wider than the line is broken at its own spaces, which is
    the case in which nothing else fits; the separator that closes such a part
    keeps the space it ends in, which `wrapped` strips from the end of a line,
    so that the next record does not run into the separator. No printed line
    ends in a space: the space stands between the separator and the record
    that follows it."""
    lines, current = [], ""
    for place, part in enumerate(parts):
        piece = part + (separator if place + 1 < len(parts) else "")
        if current and len(current + piece) + indent > WIDTH:
            lines.append(" " * indent + current.rstrip())
            current = piece
        else:
            current += piece
        if len(current) + indent > WIDTH:
            tail = current[len(current.rstrip()) :]
            broken = wrapped(current, indent)
            lines.extend(broken[:-1])
            current = broken[-1][indent:] + tail
    if current.strip():
        lines.append(" " * indent + current.rstrip())
    return tuple(lines) or (" " * indent,)


# --- the lines of one text ---


def wrapped(text, indent):
    """The lines of `text` laid out from column `indent`: its own line breaks
    joined by a space, then broken between the parts `break_parts` gives, each
    continuation at `indent`, and no line ending in a space. Where a part that
    opens with a product or map sign does not fit, the text after a comma of
    the line, the last comma at which the two then fit, moves down with it, so
    that the sign's left operand stands beside it."""
    # Expression formatting may already contain width-78 display breaks. A
    # sheet lays the same expression out from its own content column, so those
    # breaks are reflowed here and every resulting line receives that column's
    # indentation. Joining with one space restores the separator at which the
    # expression formatter broke; it changes no mathematical token.
    stripped = " ".join(line.strip() for line in str(text).rstrip().splitlines())
    if len(stripped) + indent <= WIDTH:
        return (" " * indent + stripped,)
    kind = (
        SetsLine if isinstance(text, SetsLine) else PathLine if isinstance(text, PathLine) else str
    )
    lines, current = [], ""
    for part in break_parts(kind(stripped), indent):
        if current.strip() and len(current + part) + indent > WIDTH:
            moved = False
            if part.lstrip().startswith(("× ", "→ ")):
                for stop in reversed(_breakable_commas(current)):
                    continuation = current[stop:].lstrip() + part
                    if len(continuation) + indent <= WIDTH:
                        lines.append((" " * indent + current[:stop]).rstrip())
                        current = continuation
                        moved = True
                        break
            if not moved:
                lines.append((" " * indent + current).rstrip())
                current = part.lstrip()
        else:
            # a line opens at its own column, so the spaces that separated two
            # columns on the line above are not carried down with it
            current = (current + part) if current.strip() else (current + part).lstrip()
        # A continuation keeps the column of its entry; a group too wide for
        # that column is broken at its own spaces by `break_parts`, since at a
        # column further left it would read as a new entry
    if current.strip():
        lines.append((" " * indent + current).rstrip())
    return tuple(lines)


def _breakable_commas(text):
    """The places after the commas at which an expression may continue on the
    next line: the commas inside a bracket that is no interval, square or
    bare and two-ended, `(0, 1)`. Each place follows its comma, so that the
    comma stays with the coordinate or set member it closes."""
    stack, found = [], []
    for place, character in enumerate(text):
        if character in OPENING:
            stack.append((place, character))
        elif character in CLOSING and stack:
            stack.pop()
        elif character == "," and stack:
            opened, opening = stack[-1]
            before = text[:opened].rstrip()
            interval = opening == "[" or (opening == "(" and (not before or before[-1] in ":∈×→|"))
            if not interval:
                found.append(place + 1)
    return tuple(found)


class SetsLine(str):
    """A line of sets, such as a wire's name and its carrier, which
    `break_parts` gives to `_broken` whole rather than divided at its spaces
    first."""


class PathLine(str):
    """A line that names a file: the subtitle of a title block, `a stage
    occurrence of applications/portfolio-choice/declaration/stages/cons/
    cons.bl`. It breaks at its spaces as any other line does, and where the
    path alone is still wider than the line it breaks after a `/`, so that no
    component of the path is split and nothing is abbreviated."""


# --- the parts a line breaks into ---


def break_parts(text, indent=INDENT):
    """The parts of a line a wrap may break between, each carrying the
    separator that opens it, so that joining the parts gives the line back. A
    part wider than the line at `indent`, the column the line is laid out from,
    is broken at the spaces that stand outside every bracket, and, where that
    gives no break, at its own spaces, which is the only case in which a set or
    a name could be split and is the case in which nothing else fits. On a
    `PathLine` a part wider than the line that holds no space is broken after
    each `/`; a single component wider than the line stands over the width,
    since a name is never abbreviated."""
    if isinstance(text, SetsLine):
        # Prefer one complete map or product before considering a continuation
        # after a coordinate or before an operator and its following operand.
        inside = (text,)
    else:
        inside = outer_space_parts(text)
    return tuple(
        piece for part in inside for piece in _broken(part, indent, isinstance(text, PathLine))
    )


def _broken(part, indent, is_named):
    """One part of a line broken until each piece fits or nothing else can be
    done. The divisions are tried in the order written: at the spaces outside
    every bracket, around one parenthesized map or product, after the bar of a
    comprehension, after the commas of one group; a declared set or tuple is
    then kept whole; then at the products and arrows outside every bracket,
    and within a bracketed group that ends the part. Each part a division
    gives is broken again. Where none applies, the part is broken at the
    spaces beside no map or product sign, and on a `PathLine` after each
    `/`."""
    if len(part) + indent <= WIDTH:
        return (part,)
    divided = (
        _space_division(part)
        or _parenthesized_map_parts(part, indent)
        or _bar_parts(part)
        or _comma_group_parts(part, indent)
    )
    if divided is None:
        if _atomic_bracket(part):
            return (part,)
        divided = _map_division(part) or _within_one_bracket(part)
    if divided is None:
        return _last_division(part, is_named)
    return tuple(piece for one in divided for piece in _broken(one, indent, is_named))


def _space_division(part):
    """The parts of `part` between the spaces outside every bracket, where
    there are two or more; where one of those parts is a lone arrow or product
    sign, the parts between the spaces beside no such sign
    (`_parts_keeping_maps_whole`), where there are two or more; None
    otherwise."""
    free = outer_space_parts(part)
    if len(free) < 2:
        return None
    if any(one.strip() in ("→", "×") for one in free):
        safe = _parts_keeping_maps_whole(part)
        return safe if len(safe) > 1 else None
    return free


def outer_space_parts(text):
    """The parts of `text` between the spaces that stand outside every pair of
    brackets, parentheses and braces, each part carrying the space that opens
    it. A break at any other space would cut a subscript, a bracket or a
    coordinate tuple in two — `E_{Ψ,` above `θ}`, `𝐴𝑀𝐵(m_d,` above `c)` — and
    read as two names."""
    return _split_at(
        text, (place for place in _outer_places(text) if place and text[place] == " ")
    )


def _parts_keeping_maps_whole(text):
    """The ordinary-space parts of `text`, except that neither space beside a
    map arrow or product sign is a break. Spaces within a long operand remain
    available. Thus `A long set × B long set` may break within either set, but
    never immediately before or after `×`."""
    protected = [
        (pair.opened, pair.closed)
        for pair in _bracket_pairs(text)
        if _atomic_bracket(text[pair.opened : pair.closed + 1])
    ]
    places = []
    for place, character in enumerate(text):
        if character != " " or not place:
            continue
        if any(opened < place < closed for opened, closed in protected):
            continue
        before = text[:place].rstrip()
        after = text[place:].lstrip()
        if (before and before[-1] in "→×") or (after and after[0] in "→×"):
            continue
        places.append(place)
    return _split_at(text, places)


def _atomic_bracket(part):
    """Whether `part` is one short-form declared set or tuple, not a
    comprehension. Such an object is moved beneath its label where necessary;
    splitting its comma-separated print would read as two objects."""
    text = part.strip()
    if len(text) < 2 or text[0] not in OPENING or text[-1] not in CLOSING:
        return False
    inside = text[1:-1]
    return (
        "," in inside
        and ":" not in inside
        and not any(character in OPENING + CLOSING for character in inside)
        and not any(token in inside for token in (" | ", " ∀ ", " ∃ ", " ↦ "))
    )


def _parenthesized_map_parts(part, indent):
    """The parts of `part` around one parenthesized map or product, the
    outermost and longest of those that fit at `indent`, so that it stands
    whole on a line of its own rather than a named finite set inside it being
    cut; None where there is none, or where `part` fits."""
    groups = []
    for pair in _bracket_pairs(part):
        inside = part[pair.opened + 1 : pair.closed]
        if (
            pair.opening == "("
            and any(mark in inside for mark in (" × ", " → "))
            and len(inside) + indent <= WIDTH
        ):
            groups.append((pair.depth, -(pair.closed - pair.opened), pair.opened, pair.closed))
    if not groups or len(part.lstrip()) + indent <= WIDTH:
        return None
    _, _, opened, closed = min(groups)
    return tuple(
        one for one in (part[: opened + 1], part[opened + 1 : closed], part[closed:]) if one
    )


def _bar_parts(part):
    """A set written by comprehension, `{x ∈ X | condition}`, broken after its
    bar, so that a continuation opens with the condition and never inside the
    list of bound names. The bars used are the shallowest ones inside the
    outermost bracket; `None` where there is none."""
    text = part.strip()
    if not text or text[0] not in OPENING:
        return None
    depth, bars = 0, []
    for place, char in enumerate(text):
        if char in OPENING:
            depth += 1
        elif char in CLOSING:
            depth -= 1
        elif (
            char == "|"
            and depth >= 1
            and text[place - 1 : place] == " "
            and text[place + 1 : place + 2] == " "
        ):
            bars.append((depth, place + 2))
    if not bars:
        return None
    shallowest = min(depth for depth, _ in bars)
    cuts = [place for depth, place in bars if depth == shallowest]
    lead = part[: len(part) - len(part.lstrip())]
    pieces, start = [], 0
    for cut in cuts:
        pieces.append((lead if not pieces else "") + text[start:cut])
        start = cut
    pieces.append(text[start:])
    return tuple(pieces)


def _comma_group_parts(part, indent):
    """The parts of one long subscript, tuple or argument list, broken after
    its commas: the outermost and longest group with a comma at its own depth,
    each comma on the line of the member it closes and the group's brackets
    on its first and last parts, so that joining the parts gives `part` back.
    A square-bracketed interval and a bare two-ended interval, `(0, 1)`, are
    no such group; None where there is none, or where `part` fits."""
    groups = []
    for pair in _bracket_pairs(part):
        inside = part[pair.opened + 1 : pair.closed]
        commas = [
            pair.opened + 1 + offset for offset in _outer_places(inside) if inside[offset] == ","
        ]
        if not commas or pair.opening == "[":
            continue
        before = part[: pair.opened].rstrip()
        bare_interval = (
            pair.opening == "(" and len(commas) == 1 and (not before or before[-1] in ":∈×→|")
        )
        if not bare_interval:
            groups.append(
                (pair.depth, -(pair.closed - pair.opened), pair.opened, pair.closed, commas)
            )
    if not groups or len(part.lstrip()) + indent <= WIDTH:
        return None
    _, _, opened, closed, commas = min(groups)
    stops = tuple(place + 1 for place in commas)
    starts = (opened + 1,) + stops[:-1]
    members = tuple(part[start:stop] for start, stop in zip(starts, stops))
    members += (part[stops[-1] : closed],)
    return (part[: opened + 1] + members[0],) + members[1:-1] + (members[-1] + part[closed:],)


def _map_division(part):
    """The parts of `part` between the products and arrows outside every
    bracket, where there are two or more; None otherwise. A bare product
    longer than even the body column has no comma at which it can continue;
    each operator stays with the factor to its right, so that no line ends in
    a dangling × or →."""
    maps = outer_map_parts(part)
    return maps if len(maps) > 1 else None


def outer_map_parts(text):
    """The parts of a line of sets between the products and the arrows that
    stand outside every pair of brackets, parentheses and braces, each part
    carrying the separator that opens it. An arrow within a set — the map of a
    comprehension, `{f : X → Y | …}` — is no break, since a sheet holds no set
    broken across lines."""
    return _split_at(
        text,
        (
            place
            for place in _outer_places(text)
            if place and text[place] == " " and text[place + 1 : place + 3] in ("× ", "→ ")
        ),
    )


def _within_one_bracket(part):
    """The parts of the last bracketed group in a piece, where that group runs
    to the end of the piece. This includes a bare group and an application such
    as `required[condition](...)` or `𝒷({...})`.

    The wrapper, the contents and the closing bracket remain literal pieces;
    joining the result therefore gives `part` back. The contents break only at
    spaces outside their nested groups, with maps and products kept whole. A
    long comprehension can consequently wrap without splitting one of its
    maps, while a short declared set remains untouched because this function is
    reached only after the whole piece has exceeded the available width. None
    where no such group ends the piece or its contents give no part."""
    text = part.rstrip()
    last = [
        pair for pair in _bracket_pairs(text) if pair.depth == 0 and pair.closed == len(text) - 1
    ]
    if not last:
        return None
    opened, closed = last[0].opened, last[0].closed
    inside = _maps_whole(tuple(one for one in outer_space_parts(text[opened + 1 : closed]) if one))
    if not inside or not any(one.strip() for one in inside):
        return None
    return tuple(one for one in ((part[: opened + 1],) + inside + (part[closed:],)) if one)


def _maps_whole(parts):
    """`parts` with the two sides of a map and the factors of a product joined
    into one part, so that a break within a bracket never falls at an arrow or
    at a product: `{f : X × Y → Z | …}` keeps `X × Y → Z` on one line, since
    its two halves on two lines read as two sets."""
    whole = []
    for part in parts:
        if whole and (part.strip() in ("→", "×") or whole[-1].rstrip().endswith((" →", " ×"))):
            whole[-1] += part
        else:
            whole.append(part)
    return tuple(whole)


def _last_division(part, is_named):
    """A part no division applies to: broken at every space beside no map or
    product sign, so that even the last break keeps every map and product
    chain whole (deep comprehensions reach this case when several nested
    binders share one closing expression, and a bare space break would leave
    `→` or `×` at a line boundary); a part with no space on a `PathLine`
    after each `/`; otherwise whole."""
    if " " in part.strip():
        return _parts_keeping_maps_whole(part)
    if is_named and "/" in part.strip().rstrip("/"):
        return tuple(re.split(r"(?<=/)", part))
    return (part,)


# --- the brackets of a text ---


def _outer_places(text):
    """The places of the characters of `text` that stand outside every pair of
    brackets, parentheses and braces, the brackets themselves left out; a
    closing bracket with no opening one before it closes nothing."""
    depth = 0
    for place, character in enumerate(text):
        if character in OPENING:
            depth += 1
        elif character in CLOSING:
            depth = max(0, depth - 1)
        elif depth == 0:
            yield place


# One pair of brackets of a text: the places of its opening and closing
# brackets, the opening character, and the number of pairs open around it.
_BracketPair = namedtuple("_BracketPair", "opened closed opening depth")


def _bracket_pairs(text):
    """Each pair of matching brackets of `text`, in the order the pairs close;
    a closing bracket with no opening one before it closes nothing."""
    open_brackets = []
    for place, character in enumerate(text):
        if character in OPENING:
            open_brackets.append((place, character))
        elif character in CLOSING and open_brackets:
            opened, opening = open_brackets.pop()
            yield _BracketPair(
                opened=opened, closed=place, opening=opening, depth=len(open_brackets)
            )


def _split_at(text, places):
    """The parts of `text` between the places given, each part after the first
    opening with the character at its place."""
    places = tuple(places)
    return tuple(text[start:stop] for start, stop in zip((0,) + places, places + (len(text),)))
