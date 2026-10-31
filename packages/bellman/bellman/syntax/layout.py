"""The layout engine of a card: documents, their printing at a width, the
margin notes of a rule and the lines drawn across a card.

A document is a tree of nine kinds of node. `text` is a run of characters
that is never split. `line` is a place where the text may break: printed as
its flat form (one space, or nothing) when the group around it is laid out on
one line, and as a newline followed by the indentation in force when the group
is broken. `nest` sets the indentation of every break inside it, a number
of columns. `group` marks a stretch of the
document that is printed on one line when it fits in the width and otherwise
broken at its own lines; the groups inside it are then tried on their own, so
that the outermost group breaks first and an inner group that still fits
stays on one line (Wadler, "A prettier printer", 2003). `concat` sets
documents one after another. `margin` is a note set against the right margin
of the line it ends, or on a line of its own under the text it notes when the
line has no room for it. `bounded` limits how far the nests inside it indent
a continuation past the column at which it begins, so that a deeply nested
expression keeps the rest of the line for its text. `align` continues the
breaks inside it at the column at which it begins, so that the arguments of
a call stand under the first. `operand` is a sign and the document it
applies to, after a possible break: in a broken group the break stands
before the sign, except where the document on one line would pass the width
after the sign but not at the sign's column; there the sign ends the line
and the document stands on the next line at that column, or, where it
passes the width there too, at the column of the relation the sign closes,
where it fits there.

This module lays out what it is given. It knows nothing of stages, records or
mathematics.
"""

from __future__ import annotations

from dataclasses import dataclass

# the one width of every printed form, a sheet and a card alike, and the
# label column of a sheet, eleven characters, at which every entry of a
# labeled line starts
WIDTH = 78
LABEL_COLUMN = 11

# the two kinds of line drawn on a card: the heavy line under the title and at
# the foot, and the light line, across the card before its `Source` section
# and short under an entry's row of `Operations` and above the `out` rows of
# `Signature`
HEAVY = "━"  # ━
LIGHT = "─"  # ─

# the gap kept between a line's text and a note set against the margin
MARGIN_GAP = 2


# --- the nine kinds of node of a document ---


class Document:
    """The base of every node of a document."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Text(Document):
    text: str


@dataclass(frozen=True, slots=True)
class Line(Document):
    flat: str = " "
    # a soft line breaks on its own, where the text up to the next possible
    # break does not fit, and stays flat otherwise, while a line of a broken
    # group breaks with the group
    soft: bool = False


@dataclass(frozen=True, slots=True)
class Nest(Document):
    prefix: str
    document: Document


@dataclass(frozen=True, slots=True)
class Group(Document):
    document: Document


@dataclass(frozen=True, slots=True)
class Concat(Document):
    parts: tuple


@dataclass(frozen=True, slots=True)
class Margin(Document):
    note: str


@dataclass(frozen=True, slots=True)
class Bounded(Document):
    depth: int
    document: Document


@dataclass(frozen=True, slots=True)
class Align(Document):
    document: Document


@dataclass(frozen=True, slots=True)
class Operand(Document):
    sign: str
    document: Document
    # the columns left of the indentation in force at which the document may
    # stand where it fits nowhere else: the column of the relation it closes
    dedent: int = 0


# --- the functions that build a document ---


def text(characters):
    """A run of characters that is never broken."""
    if not isinstance(characters, str):
        raise TypeError("text takes a string")
    if "\n" in characters:
        raise ValueError("a text node holds no newline; use line() for a break")
    return Text(characters)


def line(flat=" "):
    """A place where the text may break: `flat` is what prints when the
    enclosing group stays on one line, one space unless another flat form is
    given, and a newline with the indentation in force prints otherwise."""
    if not isinstance(flat, str) or "\n" in flat:
        raise TypeError("the flat form of a line is a string without a newline")
    return Line(flat)


def softline(flat=" "):
    """A place where the text may break on its own: inside a broken group,
    it breaks exactly where the text from it to the next possible break does
    not fit in the remaining width, and stays flat otherwise; inside a group
    laid out on one line it is flat. A product's sign stands after one, so
    that `β · 𝑑𝑉_a≻(a_nxt_adj,` keeps its factors together and breaks inside
    the argument list instead."""
    if not isinstance(flat, str) or "\n" in flat:
        raise TypeError("the flat form of a line is a string without a newline")
    return Line(flat, True)


def nest(indent, *parts):
    """`parts` with every break inside them indented by `indent` more
    columns."""
    if not isinstance(indent, int) or isinstance(indent, bool) or indent < 0:
        raise TypeError("an indentation is a non-negative number of columns")
    return Nest(" " * indent, concat(*parts))


def group(*parts):
    """`parts` printed on one line when they fit in the remaining width, and
    otherwise broken at the lines directly inside them; the groups inside are
    then decided on their own."""
    return Group(concat(*parts))


def concat(*parts):
    """`parts` in sequence; a string among them is a text node."""
    documents = tuple(_document(part) for part in parts)
    if len(documents) == 1:
        return documents[0]
    return Concat(documents)


def _document(value):
    """`value` as a document: a string is a text node, a document stands."""
    if isinstance(value, Document):
        return value
    if isinstance(value, str):
        return Text(value)
    raise TypeError(f"a document or a string is expected; got {type(value).__name__}")


def margin(note):
    """`note` set against the right margin of the line it ends, with at least
    two spaces before it, or, when the line has no room for it, on a line of
    its own at the indentation in force, under the first character of the
    text it notes: the region note of a rule, `on 𝑚_d≻(Xa)`."""
    if not isinstance(note, str) or "\n" in note:
        raise TypeError("a margin note is a string without a newline")
    return Margin(note)


def bounded(depth, *parts):
    """`parts` with the continuations inside them set at most `depth` columns
    past the column at which the parts begin: a nest that would indent a
    continuation deeper stands at that limit instead, so that a deeply nested
    expression keeps the rest of the line for its text."""
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 0:
        raise TypeError("the depth is a non-negative number of columns")
    return Bounded(depth, concat(*parts))


def align(*parts):
    """`parts` with every break inside them continuing at the column at which
    the parts begin: the arguments of a call broken over lines stand under
    the first argument, `𝑑𝑉_a≻(a_nxt_adj,` then `h_nxt_adj,` under it."""
    return Align(concat(*parts))


def operand(sign, *parts, dedent=0):
    """`sign` and the operand that `parts` form, after a possible break: in a
    group laid out on one line, one space, the sign, one space and the
    operand; in a broken group, the sign on the next line at the indentation
    in force, one space and the operand, whose groups are then decided on
    their own. Where the operand on one line would pass the width after the
    sign but not at the indentation in force, and the sign fits on the
    current line, the sign, after one space, ends that line and the operand
    stands on the next line at the indentation in force, on one line: the
    right-hand side of a relation kept whole, `μ≻(B) =` over
    `μ⊗P_ν⊗P_{Ψ|ν}({…})`. Where it would pass the width at the indentation
    in force too, but not `dedent` columns to its left, at the column of the
    relation the sign closes, it stands there on one line, under the
    relation's first character, so that the right-hand side of a rule a
    card sets at its column is kept whole where that column holds it."""
    if not isinstance(sign, str) or not sign or "\n" in sign:
        raise TypeError("a sign is a non-empty string without a newline")
    if not isinstance(dedent, int) or isinstance(dedent, bool) or dedent < 0:
        raise TypeError("the dedent is a non-negative number of columns")
    return Operand(sign, concat(*parts), dedent)


# --- the text of a document: within a width, or on one line ---


FLAT, BREAK = "flat", "break"


def render(document, width=WIDTH):
    """The text of `document` laid out within `width` columns: the outermost
    group that does not fit is broken first, an inner group is kept on one
    line where it fits, and a break indents its continuation by the nests in
    force. No printed line ends in a space. A text node wider than the
    remaining columns stands over the width, since nothing is abbreviated."""
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError("the width is a positive number of columns")
    pieces, column = [], 0
    # an item is a prefix, a mode, a node and the limit its nests of spaces
    # may indent to, None where no bound is in force
    stack = [("", BREAK, _document(document), None)]
    while stack:
        prefix, mode, node, limit = stack.pop()
        if isinstance(node, Text):
            pieces.append(node.text)
            column += len(node.text)
        elif isinstance(node, Line):
            # a soft line stays flat where the text up to the next possible
            # break fits, and where breaking would gain no column
            flat = mode == FLAT or (
                node.soft
                and (
                    len(prefix) >= column
                    or _fits_to_next_break(
                        width - column - len(node.flat),
                        [
                            (held_prefix, held_mode, held)
                            for held_prefix, held_mode, held, _ in stack
                        ],
                    )
                )
            )
            if flat:
                pieces.append(node.flat)
                column += len(node.flat)
            else:
                pieces.append("\n" + prefix)
                column = len(prefix)
        elif isinstance(node, Margin):
            if column + MARGIN_GAP + len(node.note) <= width:
                pieces.append(" " * (width - len(node.note) - column) + node.note)
                column = width
            else:
                pieces.append("\n" + prefix + node.note)
                column = len(prefix) + len(node.note)
        elif isinstance(node, Operand):
            if mode == FLAT:
                pieces.append(" " + node.sign + " ")
                column += len(node.sign) + 2
            else:
                # the operand on one line, with the text after it up to the
                # next break, tried after the sign, at the indentation in
                # force and at the column of the relation the sign closes;
                # where it fits only at the indentation, or only at the
                # relation's column, the sign ends the current line and the
                # operand is laid out there on one line
                whole = [
                    (held_prefix, held_mode, held) for held_prefix, held_mode, held, _ in stack
                ] + [(prefix, FLAT, node.document)]
                outer = prefix[: max(0, len(prefix) - node.dedent)]
                if (
                    column + 1 + len(node.sign) <= width
                    and not _fits(width - len(prefix) - len(node.sign) - 1, whole)
                    and _fits(width - len(prefix), whole)
                ):
                    pieces.append(" " + node.sign + "\n" + prefix)
                    column = len(prefix)
                    mode = FLAT
                elif (
                    node.dedent
                    and column + 1 + len(node.sign) <= width
                    and not _fits(width - len(prefix), whole)
                    and _fits(width - len(outer), whole)
                ):
                    pieces.append(" " + node.sign + "\n" + outer)
                    column = len(outer)
                    mode = FLAT
                else:
                    pieces.append("\n" + prefix + node.sign + " ")
                    column = len(prefix) + len(node.sign) + 1
            stack.append((prefix, mode, node.document, limit))
        elif isinstance(node, Nest):
            deeper = prefix + node.prefix
            if limit is not None and len(deeper) > limit:
                deeper = prefix + " " * max(0, limit - len(prefix))
            stack.append((deeper, mode, node.document, limit))
        elif isinstance(node, Bounded):
            stack.append((prefix, mode, node.document, column + node.depth))
        elif isinstance(node, Align):
            # the continuation lines stand at the column the parts begin at,
            # and no deeper than the limit of a bound in force
            aligned = column if limit is None else min(column, limit)
            stack.append(
                (prefix + " " * max(0, aligned - len(prefix)), mode, node.document, limit)
            )
        elif isinstance(node, Concat):
            stack.extend((prefix, mode, part, limit) for part in reversed(node.parts))
        elif isinstance(node, Group):
            items = [(held_prefix, held_mode, held) for held_prefix, held_mode, held, _ in stack]
            if mode == FLAT or _fits(width - column, items + [(prefix, FLAT, node.document)]):
                stack.append((prefix, FLAT, node.document, limit))
            else:
                stack.append((prefix, BREAK, node.document, limit))
        else:
            raise TypeError(f"not a document node: {type(node).__name__}")
    return "\n".join(part.rstrip() for part in "".join(pieces).split("\n"))


def flat(document):
    """The text of `document` on one line: every line as its flat form and a
    margin note after two spaces."""
    pieces = []
    stack = [_document(document)]
    while stack:
        node = stack.pop()
        if isinstance(node, Text):
            pieces.append(node.text)
        elif isinstance(node, Line):
            pieces.append(node.flat)
        elif isinstance(node, Margin):
            pieces.append(" " * MARGIN_GAP + node.note)
        elif isinstance(node, Operand):
            pieces.append(" " + node.sign + " ")
            stack.append(node.document)
        elif isinstance(node, (Nest, Group, Bounded, Align)):
            stack.append(node.document)
        elif isinstance(node, Concat):
            stack.extend(reversed(node.parts))
        else:
            raise TypeError(f"not a document node: {type(node).__name__}")
    return "".join(pieces)


def _fits(remaining, items):
    """Whether the items, laid out in their modes, reach the end of the
    current line within `remaining` columns. A line in break mode ends the
    current line, and so does an operand in break mode, whose sign ends that
    line only where it fits there; a margin note, which moves to a line of
    its own when it has no room, never decides the fit."""
    for mode, node in _in_layout_order(items):
        if isinstance(node, Text):
            remaining -= len(node.text)
        elif isinstance(node, Line):
            if mode == BREAK:
                return True
            remaining -= len(node.flat)
        elif isinstance(node, Operand):
            if mode == BREAK:
                return True
            remaining -= len(node.sign) + 2
        elif isinstance(node, Margin):
            return True
        if remaining < 0:
            return False
    return True


def _fits_to_next_break(remaining, items):
    """Whether the text from the current position to the next possible break,
    a line of any kind, an operand or a margin note, fits in `remaining`
    columns."""
    for _, node in _in_layout_order(items):
        if isinstance(node, Text):
            remaining -= len(node.text)
        elif isinstance(node, (Line, Operand, Margin)):
            return True
        if remaining < 0:
            return False
    return True


def _in_layout_order(items):
    """Each node of `items`, a stack of (prefix, mode, node) whose last item is
    laid out first, with the mode it is laid out in, in the order of the
    layout: a nest, a concatenation, a group, a bound, an alignment or an
    operand, and then the nodes inside it."""
    stack = [(mode, node) for _, mode, node in items]
    while stack:
        mode, node = stack.pop()
        yield mode, node
        if isinstance(node, Concat):
            stack.extend((mode, part) for part in reversed(node.parts))
        elif isinstance(node, (Nest, Group, Bounded, Align, Operand)):
            stack.append((mode, node.document))


# --- the lines drawn on a card ---


def horizontal_line(character=HEAVY, width=WIDTH):
    """A line of one character, across the width unless another width is
    given: the heavy line under a card's title and at its foot, the light
    line before its `Source` section, and, `width` columns long, a short
    light line."""
    if not isinstance(character, str) or len(character) != 1:
        raise TypeError("a line is drawn with one character")
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise TypeError("a line is at least one column long")
    return character * width
