"""The parser of the language: a `.bl` text becomes a Lark parse tree.

The grammar is `grammars/stage.lark`. The parser is LALR and keeps the
position of every node; its postlex, `NewlinesInsideBrackets`, drops the
newline tokens inside round and square brackets, so that the declaration of
a joint distribution written over several lines parses as one declaration.
`parse_text` reads a text. A text the language does not hold is read once
more with the rules of `grammars/retired.lark`, the one retired spelling the
lowering refuses with the text to write; every other such text is refused
as the language's own parser refuses it.

Beside the parser the module holds what a refusal of a text the parser cannot
read says in the language's words: `FORMS`, one entry per terminal of the
grammar; `expected_forms`, the forms admitted at a position; `place_at` and
`grammar_sentence`, the place a position falls inside and the sentence of the
grammar's own comment for it; and `marked_line`, the line of the text with a
mark under the column. `factory/elaboration.py` raises the refusal and writes
its sentence, its marked line and its advice from these; no token name and no
rule name of Lark leaves this module.
"""

import functools
import pathlib
from typing import NamedTuple

from lark import Lark
from lark.exceptions import UnexpectedInput

_GRAMMAR = pathlib.Path(__file__).parent / "grammars" / "stage.lark"
_RETIRED = _GRAMMAR.with_name("retired.lark")


# --- the parser ---


@functools.lru_cache(maxsize=4)
def build_parser(strict=False, retired=False):
    """The parser of `stage.lark`, built once for each pair of arguments:
    LALR with the contextual lexer, the position of every node kept, an
    absent optional group a `None` child, and `NewlinesInsideBrackets` as
    its postlex. Every option is written, so that a change of a library
    default changes nothing here. The package parses with `strict=False`;
    `strict=True`, which needs `interegular`, is the certificate that the
    grammar has no parser-table conflict and no lexer collision, built by
    `tests/test_spec07_u1_grammar.py` and not re-checked at every import.
    With `retired`, the grammar is the language's with the rules of
    `retired.lark` added, which `parse_text` reads a refused text with."""
    return Lark(
        _GRAMMAR.read_text() + (_RETIRED.read_text() if retired else ""),
        parser="lalr",
        lexer="contextual",
        strict=strict,
        maybe_placeholders=True,
        propagate_positions=True,
        postlex=NewlinesInsideBrackets(),
    )


def parse_text(text):
    """The parse tree of a `.bl` text, read by the parser of the language.

    A text the language's parser refuses is read once more with the retired
    spelling added (`grammars/retired.lark`). Where that reading succeeds,
    the text holds a bound after a comma, and its tree is answered for the
    lowering to refuse with the sets to write. Where it fails as well, the
    refusal is the language's own, so the retired spelling changes neither
    the reading of a text of the language nor what a refusal of the parser
    says."""
    try:
        return build_parser().parse(text)
    except UnexpectedInput:
        try:
            return build_parser(retired=True).parse(text)
        except UnexpectedInput:
            pass
        raise


class NewlinesInsideBrackets:
    """The postlex of the parser: it drops the newline tokens inside brackets,
    so that the declaration of a joint distribution written over several lines
    is one declaration.

    One combined depth over both bracket kinds: half-open intervals
    close ( with ] or [ with ), so counting parentheses alone leaks
    depth on every open-closed interval and swallows the newlines
    that follow it.
    """

    always_accept = ("_NL",)

    def process(self, stream):
        depth = 0
        for tok in stream:
            if tok.value in ("(", "["):
                depth += 1
            elif tok.value in (")", "]"):
                depth = max(0, depth - 1)
            if tok.type == "_NL" and depth > 0:
                continue
            yield tok


# --- what a refusal of the parser says, in the language's words ---


# What each terminal of `stage.lark` is in the words an author writes, so that
# a refusal names the forms the parser admits in the language's spellings and
# never in a token name. One entry per terminal the grammar defines, the
# anonymous ones among them: `expected_forms` answers a name the table does
# not hold with nothing. No test compares the table with the parser's
# terminals, so a terminal it lacks is left out of a refusal without notice.
# It is data, not a function of the grammar.
FORMS = {
    # the brackets and the punctuation the file is written with
    "RPAR": ")",
    "LPAR": "(",
    "RSQB": "]",
    "LSQB": "[",
    "RBRACE": "}",
    "LBRACE": "{",
    "COMMA": ",",
    "_COLON": ":",
    "_AT": "@",
    "VBAR": "|",
    "DOT": ".",
    "TILDE": "~",
    "_PERP": "⟂",
    "__ANON_1": "->",
    "__ANON_0": "×",
    # the signs of a union and of a difference of sets as a refusal prints
    # them; the grammar also admits `∪` and `∖`
    "_UNION": "\\/",
    "_DIFFERENCE": "\\",
    # the arithmetic of an expression
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    # `**` and `<-` are the second spelling the grammar admits of these two;
    # a refusal names the one the corpus writes, which is what to write
    "_POW": "^",
    "EQUAL": "=",
    "RELOP": "a comparison, <=, >=, ≤, ≥, < or >",
    # what a name, a number and the reserved glyphs are called
    "NAME": "a name",
    "NUMBER": "a number",
    "INFTY": "inf",
    "BBSET": "a reserved set, ℝ, ℝ₊, ℝ₊₊, ℝ̄, ℝ_{+∞}, ℕ or ℤ",
    "RPLUS": "a reserved set, R+, R++, R_{+} or R_{++}",
    "PMARK": "a perch mark, <, ~ or >",
    "TAGBANG": "a !-marked vocabulary word",
    "STAGE_STRING": "a quoted string",
    "_ASSIGN": ":=",
    # what stands at the ends of a line
    "_NL": "the end of the line",
    "STMT_META": "an annotation, :: [ … ]",
    "METADATA_SCALAR": "the value of a metadata line",
    "SOL_COMMENT": "a comment",
    "EOL_COMMENT": "a comment",
    "WS_INLINE": "a space",
}


def expected_forms(names):
    """The forms of the language the terminals `names` admit, in the order
    `FORMS` writes them and without repetition.

    `names` are the terminal names a parser refusal carries. A name `FORMS`
    does not hold is left out rather than printed, so that no token name
    reaches a message."""
    wanted = {str(getattr(name, "name", name)) for name in names}
    forms, seen = [], set()
    for name, form in FORMS.items():
        if name in wanted and form not in seen:
            seen.add(form)
            forms.append(form)
    return tuple(forms)


def marked_line(text, line, column):
    """The line of `text` at `line` and a second line marking `column` under
    it, the two indented by four spaces. The column is counted in code points,
    as the parser counts it."""
    lines = text.split("\n")
    if not 1 <= line <= len(lines):
        return ""
    source = lines[line - 1]
    return f"    {source}\n    {' ' * max(0, column - 1)}^"


# The three places of the grammar a refused position can fall inside, each
# with the rule of `stage.lark` whose comment says what may be written there.
# A header carries a signature whose sides are parenthesized, so a position
# inside those parentheses is answered by the comment of `side` and a
# position in the header itself by the comment of `word_tag`; the sentence
# stands once, in the grammar, and is read from it.
PLACES = {
    "a block header": "word_tag",
    "a side of a block header": "side",
    "an operator's subscript": "operator_call",
}


_OPENERS = "([{"


_CLOSERS = ")]}"


def place_at(text, line, column):
    """The place of the grammar the position falls inside, one of the keys of
    `PLACES`, or None where it falls in neither a block header nor an
    operator's subscript.

    The brackets open before the position are read from the text: a block
    header is the `[` that opens a line, a side of its signature the
    parentheses inside that bracket, and an operator's subscript the `{` that
    follows a name, as `operator_call` writes it. A closer of either kind
    closes the innermost bracket, since the language writes half-open
    intervals, `(a, b]` and `[a, b)`, which is the reading of the postlex
    above."""
    open_brackets = []
    for number, source in enumerate(text.split("\n")[: max(0, line)], start=1):
        stop = column if number == line else len(source) + 1
        open_brackets = _brackets_after(source, stop, open_brackets)
    inside_header = any(
        bracket.opener == "[" and bracket.opens_the_line for bracket in open_brackets
    )
    for bracket in reversed(open_brackets):
        if bracket.opener == "{" and (bracket.before.isalnum() or bracket.before == "_"):
            return "an operator's subscript"
        if bracket.opener == "(" and inside_header:
            return "a side of a block header"
        if bracket.opener == "[" and bracket.opens_the_line:
            return "a block header"
    return None


def _brackets_after(source, stop, open_brackets):
    """The brackets open after the characters of one line `source` that stand
    before column `stop`, where `open_brackets` were open before the line: an
    opener opens one, a closer of either kind closes the innermost, and the
    characters of a quoted string or of a comment open and close none."""
    open_brackets = list(open_brackets)
    indent = len(source) - len(source.lstrip())
    quote = None
    for index, character in enumerate(source[: max(0, stop - 1)], start=1):
        if quote is not None:
            quote = None if character == quote else quote
        elif character in "\"'":
            quote = character
        elif character == "#":
            break
        elif character in _OPENERS:
            open_brackets.append(
                _OpenBracket(
                    opener=character,
                    opens_the_line=index == indent + 1,
                    before=source[index - 2 : index - 1],
                )
            )
        elif character in _CLOSERS and open_brackets:
            open_brackets.pop()
    return open_brackets


class _OpenBracket(NamedTuple):
    """A bracket open before a position: the opening character, whether it
    opens its line, and the character written directly before it."""

    opener: str
    opens_the_line: bool
    before: str


@functools.lru_cache(maxsize=None)
def grammar_sentence(place):
    """The first sentence of the comment `stage.lark` writes above the rule
    that governs `place`, as `PLACES` names it, or the empty string for a
    place the grammar comments on nowhere. The sentence stands once, in the
    grammar, and is read from it."""
    rule = PLACES.get(place)
    if rule is None:
        return ""
    comment = []
    for source in _GRAMMAR.read_text().split("\n"):
        stripped = source.strip()
        if stripped.startswith("//"):
            comment.append(stripped[2:].strip())
            continue
        if stripped.lstrip("?!").startswith(f"{rule}:"):
            break
        comment = []
    sentence = " ".join(comment)
    head, stop, _ = sentence.partition(". ")
    return f"{head}." if stop else sentence
