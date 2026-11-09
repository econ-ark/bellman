"""The typing entries of a `.bl` text, located and written as text (specification
0.7 §6: the writer of the `.bl` declaration that Bellman Workbench calls).

A typing entry types one component of one place, `policy.method : !egm`,
`cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))` or the
handler binding `dcsn_to_cntn.handler : "cons-port:transition_fwd"`, at file
level or in a block's header, where its path is read relative to the block
(the union's rule 7). `typing_entry_at` answers one entry with its place in
the text, and `write_typing_entry` answers the text with the entry's value
replaced, every other character kept, or with the entry added at file level
where the text writes none; the result is parsed again, so that a value the
grammar does not read is refused before anything is written. Both read the
text through the one grammar and its span table (`parse_with_spans`) and
keep nothing.
"""

from __future__ import annotations

from typing import NamedTuple

from lark.exceptions import LarkError

from bellman.refusals import ConstructionError
from bellman.syntax import terms as T
from bellman.syntax.lower import SourceSpan, item_addresses, parse_with_spans
from bellman.syntax.source import to_source
from bellman.syntax.union import is_typing_entry

__all__ = ["TypingEntry", "typing_entries", "typing_entry_at", "write_typing_entry"]

# the separator of a statement's annotation, which may follow a file-level
# entry, `policy.handler : "cons-port:egm" :: ["the program"]`
_ANNOTATION = "::"


class TypingEntry(NamedTuple):
    """One typing entry of a `.bl` text as the text writes it: `subject`, the
    path as written, `method` in the header of `policy` or
    `cntn_to_dcsn.evaluate.method` at file level; `value`, the text after
    the colon, `!egm(tol=tol_v)`, `!Cartesian(a=(a_min, a_max, n_a))` or
    `"cons-port:egm"` with its quotes; and `span`, the entry's place in the
    text, from its subject to the end of its value, None where the span
    table records none (a header entry whose path is also the id of a line
    of its block, which holds the address in the table)."""

    subject: str
    value: str
    span: SourceSpan | None


def typing_entries(text, origin=None):
    """Every typing entry and handler binding of the `.bl` text `text`, by
    the address `<place>.<component>` it types, in textual order: a
    file-level entry by its own path, and an entry of a block's header by
    the block's address before its path, the block's own address or a nested
    block's label removed from the path's front where the path writes it
    (the union's rule 7). `origin` names the file in the spans and in a
    refusal of the parse, a `ConstructionError` under the rule `syntax` at
    the refused position (`_parsed`)."""
    term, spans = _parsed(text, origin)
    addresses = dict(item_addresses(term))
    found = {}
    for address, item in addresses.items():
        if isinstance(item, T.Declare) and is_typing_entry(item.declaration):
            typing = item.declaration
            found[to_source(typing.subject)] = _entry(text, typing, spans.get(address))
        elif isinstance(item, T.Block):
            for entry in item.tag.entries:
                if not (isinstance(entry, T.Typer) and is_typing_entry(entry.typing)):
                    continue
                key = f"{address}.{to_source(entry.typing.subject)}"
                # a line of the block whose id is the path's text holds the
                # key in the span table, and the entry's place is unrecorded
                span = None if key in addresses else spans.get(key)
                found[_absolute(address, entry.typing.subject)] = _entry(text, entry.typing, span)
    return found


def typing_entry_at(text, origin, place, component):
    """The typing entry of the `.bl` text `text` that types the `component`,
    `method`, `grid` or `handler`, of the place `place`, as a `TypingEntry`;
    None where the text writes none. A text the grammar does not read is
    refused with the parser's refusal."""
    return typing_entries(text, origin).get(f"{place}.{component}")


def write_typing_entry(text, origin, place, component, value):
    """The `.bl` text `text` with the `component` of the place `place` typed
    as `value`, the value's text as an author writes it, `!vfi`,
    `!Cartesian(a=(a_min, a_max, n_a))` or `"cons-port:egm"`: where the text
    types the component, the entry's value replaced, its subject, the
    spacing around its colon, a trailing annotation and every other
    character of the text kept; otherwise the entry appended at file level
    by the full path, `<place>.<component> : <value>`, on a line of its own.
    The text answered is parsed again, so that a value the grammar does not
    read is refused with the parser's refusal and nothing stands written.
    Refused with a ValueError where the entry's place in the text is
    unrecorded (`TypingEntry.span`)."""
    held = typing_entry_at(text, origin, place, component)
    if held is None:
        joined = text if not text or text.endswith("\n") else text + "\n"
        written = f"{joined}{place}.{component} : {value}\n"
    elif held.span is None:
        raise ValueError(
            f"the entry `{held.subject} : {held.value}` of {place} has the address of a line "
            f"of its block, so its place in the text is not recorded; write the entry in the "
            f"editor"
        )
    else:
        start, end = _offsets(text, held.span)
        head, _, rest = text[start:end].partition(":")
        spaces = rest[: len(rest) - len(rest.lstrip())]
        tail = rest[len(spaces) + len(held.value) :]
        written = f"{text[:start]}{head}:{spaces}{value}{tail}{text[end:]}"
    _parsed(written, origin)
    return written


def _parsed(text, origin):
    """The parsed `.bl` text with its span table; a text the grammar or the
    lowering does not read is refused with a `ConstructionError` under the
    rule `syntax`, at the line and the column the parser names, so that a
    caller meets the package's refusal and no parser's exception."""
    try:
        return parse_with_spans(text, origin)
    except LarkError as error:
        line, column = getattr(error, "line", None), getattr(error, "column", None)
        where = f" at line {line}, column {column}" if line is not None else ""
        raise ConstructionError(
            f"the text does not read as a .bl file{where}: {str(error).splitlines()[0]}",
            rule="syntax",
            file=origin,
            line=line,
            column=column,
        ) from None


def _entry(text, typing, span):
    """The `TypingEntry` of a typing or a handler binding: its value read
    from the text at its span, the annotation after it left out, and from
    the term where the span is unrecorded."""
    subject = to_source(typing.subject)
    if span is None:
        if isinstance(typing, T.Handler):
            return TypingEntry(subject, f'"{typing.program}"', None)
        return TypingEntry(subject, to_source(typing.classifiers[0]), None)
    start, end = _offsets(text, span)
    _, _, rest = text[start:end].partition(":")
    value = rest.strip()
    marked = value.find(_ANNOTATION)
    if marked != -1:
        value = value[:marked].rstrip()
    return TypingEntry(subject, value, span)


def _absolute(block, subject):
    """The address a header entry's path names, as the union resolves it:
    the block's address, or in a nested block its label alone, taken from
    the path's front where the path writes it, and the block's address put
    before the rest."""
    parts = block.split(".")
    segments = tuple(subject.segments)
    for prefix in (parts, parts[-1:] if len(parts) > 1 else []):
        n = len(prefix)
        if (
            n
            and len(segments) > n
            and all(s.name == name and not s.selectors for s, name in zip(segments, prefix))
        ):
            return f"{block}.{to_source(T.Path(segments[n:]))}"
    return f"{block}.{to_source(subject)}"


def _offsets(text, span):
    """The start and end indices in `text` of the characters a span covers,
    from its 1-based line and code-point column to the position after its
    last character."""
    starts = [0]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    start = starts[span.line - 1] + span.column - 1
    end = starts[span.end_line - 1] + span.end_column - 1
    return start, end
