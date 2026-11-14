"""The lowering: the Lark parse tree of a `.bl` text becomes the parsed AST,
a value of the classes of `terms.py`, with the span table of its items.

`parse_with_spans` parses a text and lowers it. It answers a `ParsedFile`: the
`FILE` term and a read-only table, keyed by item address, of the file, line
and column range of each authored item (`SourceSpan`, `SourceSpans`),
followed by the place of each component of the block headers'
declarations (`_component_spans`), which the classification table of
Bellman Workbench reads and no construction does. `ToAst`
is the Lark transformer that rewrites a parse tree bottom-up into the classes
of `terms.py`, which `gen_types.py` generates from
`grammars/dynspec_full.asdl`, with one callback for each rule of
`grammars/stage.lark`. `to_json` writes the JSON encoding of a term, and
`unlowered_parse_nodes` lists any parse-tree node left inside a term, none
when the lowering is total.

A typing entry types a component of an operator by the path of the
component, `policy.method : !egm(tol=tol_v)`, `evaluate[V[<]].grid :
!Cartesian(k=(k_min, k_max, n_k))`, inside a block header or at file level,
and a handler binding names the program that realizes the operator,
`policy.handler : "cons-port:egm"`. Each lowers to one `Typer`, or to one
`Declare` at file level: a `Declaration` whose subject is the `Path` of
segments the entry writes and whose one classifier is the `Method` or the
`Grid` the last segment of the path names, or a `Handler` holding the path
and the program. The word of the method is kept as written, with its keyword
arguments, for the catalogue to judge. The grid is one outer grid word: a
`Cartesian`, each keyword argument one factor read by its shape (`_factor`);
a `PointGrid`, the name of declared points after `nodes`, or none for the
empty grid; or a `Fibred`, a nested grid word after `base` and after
`fibre`. Each carries the predicate words written after `require`,
recognized by their shape alone (`_predicate_shaped`); their meaning, and
every other check of a grid, is judged at binding.

A form the grammar admits and the lowering reads no term from (a computed
selector, a selection where a name is written, a comprehension binder typed by
a role word, a bound written after a comma, several sets in one type that
no rule reads as one set, a union or a difference with a side that is no set
of numbers, a type inside the parentheses of the subject of a law, two items
under one address, a perch mark after a
selector, a word no vocabulary holds, a path whose last segment names no
component, a grid of no kind of the language or
of a kind reserved by name, a grid with a factor of no shape or an argument
its constructor does not take) is
refused by `_refusal`: a `ConstructionError` under the rule `syntax`, at the
range of the item being lowered, whose sentence quotes the author's text and
whose `write` says what to write, so that the author reads the refusal in the
language's words. `factory/elaboration.py` adds the file and the marked line.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from traceback import clear_frames
from types import MappingProxyType
from typing import NamedTuple

from lark import Token, Transformer, v_args
from lark import Tree as LarkTree
from lark.exceptions import VisitError

from bellman.refusals import ConstructionError
from bellman.syntax.parse import CASE_WORDS, CASE_WORDS_ARE_NO_NAMES, parse_text
from bellman.syntax.source import (
    GRID_WORDS,
    bound_name,
    bracket_of,
    is_infinity,
    is_interval,
    is_number,
    may_hold_infinity,
    to_source,
    union_of,
)
from bellman.syntax.terms import *  # noqa: F401,F403 — generated classes
from bellman.syntax.vocabulary import (
    ARRIVAL,
    CONTINUATION,
    CONTROL,
    DECISION,
    PERCH_OF_SIDE,
    RETIRED_ROLE_WORDS,
    ROLE_WORD,
    SHOCK,
    STATE,
    VALUE_ROLES,
    WRITTEN_MARK,
)
from bellman.syntax.walk import nodes

# --- a text parsed and lowered, and the refusal of the lowering ---


def parse_with_spans(text, filename=None):
    """Parse `.bl` text into a `ParsedFile`, the pair `(term, spans)`: `term`
    is the FILE that `ToAst().transform` yields for the same text (equal as a
    dataclass and identical under `to_json`), and `spans` is the SourceSpans
    table of its authored items, each span naming `filename` (None for text
    with no file). After the items, the table holds the place of each side
    of a block header, each field the side lists and each component of that
    field's typing, and the place of each typing entry and handler binding
    of a header, under the block's address and the subject as written,
    `policy.evaluate.method` (`_component_spans`). The span of a line of a
    block holds the place of each name the line writes (`_names_written`).
    The parse tree and the identity records from which the table was built
    are discarded on return; nothing is stored on the term."""
    tree = parse_text(text)
    lowering = _ToAstWithPositions(filename)
    term = lowering.transform(tree)
    left = unlowered_parse_nodes(term)
    if left:
        raise ValueError(f"lowering left {len(left)} parse nodes unconverted: {left[:3]}")
    table = {}
    for address, item in item_addresses(term):
        meta = lowering.position_of(item)
        span = SourceSpan(
            file=filename,
            line=meta.line,
            column=meta.column,
            end_line=meta.end_line,
            end_column=meta.end_column,
            names=_names_written(address, item, lowering.name_position),
        )
        if address in table:
            raise _refusal(
                f"the address {address!r} names two items, the first at {_at(table[address])} "
                f"and the second here; an id names one block, one line of a block or one "
                f"nested block, and a label one nested block",
                "give one of the two another id or label",
                span,
            )
        table[address] = span
    # after the items, the components of the block headers' declarations;
    # an address an item holds keeps the item's span, and a component
    # refuses nothing, so that the construction judges a listing as before
    for address, span in _component_spans(term, lowering.part_position, filename):
        table.setdefault(address, span)
    return ParsedFile(term, MappingProxyType(table))


class ParsedFile(NamedTuple):
    """The parsed AST of a `.bl` text and its span table, as `parse_with_spans`
    answers them; the pair unpacks as `term, spans`."""

    term: "FILE"
    spans: "SourceSpans"


def _refusal(sentence, advice, at=None, rule="syntax"):
    """The refusal of a form the lowering reads no term from, under the rule
    `syntax`: `sentence` says what the file writes there and why no term is
    read from it, quoting the author's text, and `advice` what to write
    instead, the refusal's `write`. `at` is the token or span whose line,
    column and end the refusal carries; without one,
    `_ToAstWithPositions.transform` gives it the range of the item being
    lowered, and the file the parse names. `rule` is the rule the refusal
    stands under, `syntax` for a form the grammar admits nowhere and
    `marginal-role-retired` for a retired role word."""
    return ConstructionError(
        sentence,
        rule=rule,
        file=getattr(at, "file", None),
        line=getattr(at, "line", None),
        column=getattr(at, "column", None),
        end_line=getattr(at, "end_line", None),
        end_column=getattr(at, "end_column", None),
        write=advice,
    )


def _predicate_shaped(value):
    """Whether a keyword argument has the shape of the predicate words of a
    grid's `require`: one `!`-word, or a tuple whose every item is one."""
    return isinstance(value, Nested) or (
        isinstance(value, Values) and all(isinstance(item, Nested) for item in value.items)
    )


def _at(span):
    """`file:line:column` of a span, for an error message."""
    return f"{span.file}:{span.line}:{span.column}"


# --- the span table of a parsed file ---


@dataclass(frozen=True, kw_only=True)
class SourceSpan:
    """The place of one authored item in its `.bl` source: `file` as the
    caller named it (None for text with no file), `line` and `column` the
    1-based line and code-point column of the item's first character,
    `end_line` and `end_column` the line and the column just after its last
    character (a one-character item at column 4 has end_column 5, Lark's
    token convention). `names`, for a line of a block, holds the place of
    each name the line writes (`_names_written`), from which `of_name`
    answers a name's own span; it takes no part in a comparison or in the
    printed form of the span."""

    file: "str | None"
    line: int
    column: int
    end_line: int
    end_column: int
    names: tuple = field(default=(), compare=False, repr=False)

    def of_name(self, written):
        """The span of the name `written`, `q` or `V[>]`, where this line
        first writes it, or None where the line writes no such name."""
        for name, line, column, end_line, end_column in self.names:
            if name == written:
                return SourceSpan(
                    file=self.file,
                    line=line,
                    column=column,
                    end_line=end_line,
                    end_column=end_column,
                )
        return None


# The transient source-span table: a read-only mapping (a MappingProxyType
# over a private dict) from term address to SourceSpan, in textual order.
# After the authored items, the table holds the place of each side of a
# block header, each field the side lists and each component of that
# field's typing (unit T of the model interface specification 0.3, the
# classification table).
SourceSpans = Mapping[str, SourceSpan]


def item_addresses(term):
    """The (address, item) pairs of a FILE's authored items in textual
    order: a top-level item is its 1-based position in `term.items` ("3"); a
    block with an `id=` header entry is that id ("policy"), a nested block,
    one branch of a block, its `label=` entry ("dcsn_to_cntn.work"), and
    otherwise its position; a statement or a declaration inside a block is
    "<block address>.<id>" when its annotation carries `id=` and otherwise
    "<block address>.<n>", n its 1-based position in the block body; the
    items of a nested block are addressed under it in the same way. Every
    address depends on the term alone."""
    out = []

    def visit(items, prefix):
        for n, it in enumerate(items, 1):
            if isinstance(it, Block):
                name = _entry(it.tag, "id") or (_entry(it.tag, "label") if prefix else None)
            elif prefix and isinstance(it, (Statement, Declare)):
                name = _entry(it.annot, "id")
            else:
                name = None
            address = prefix + (name or str(n))
            out.append((address, it))
            if isinstance(it, Block):
                visit(it.body, address + ".")

    visit(term.items, "")
    return out


def _entry(annotation, key):
    """The value of the first `key=` entry of an Annotation as a string, or
    None when there is no annotation or no such entry."""
    if annotation is None:
        return None
    for e in annotation.entries:
        if isinstance(e, KeyValue) and e.key == key:
            return str(e.value)
    return None


def file_position(span):
    """`file:line` of a span, the file position of an authored item, and
    `line <n>` for text parsed under no file name.

    It is the address a definition record of a top-level item carries, and it
    is written here, beside the span table itself, so that the elaboration
    forms no source position of its own."""
    return f"{span.file}:{span.line}" if span.file else f"line {span.line}"


def span_at(address, spans):
    """The span of the authored item an address names, or None where the table
    holds no such item or was not given.

    An address is the key of the table, the term address of the item; a refusal
    raised at a definition record names instead the file position that record
    carries, and the item is then the one whose own span writes that
    position. The table is read and no address is taken apart."""
    if not spans:
        return None
    span = spans.get(address)
    if span is not None:
        return span
    return next((held for held in spans.values() if file_position(held) == address), None)


# The kind of each component a typing writes on a listed field, by the
# class of the term the lowering makes of it: a set, a role word, a perch
# word.
_COMPONENT_OF = {Domain: "domain", Role: "role", Infoset: "perch"}


def _component_spans(term, position_of, file):
    """The (address, SourceSpan) pairs of the components of the block
    headers' declarations of `term`, in textual order, which
    `parse_with_spans` writes after the items (the classification table,
    unit T of the model interface specification 0.3): for each side of a
    block's signature, `<block>.in` and `<block>.out`, the side as written,
    from its `(` to the end of its typing; for each field the side lists,
    `<block>.in.<field>`, the field as written with its typing, named with
    the perch mark the term holds (`_written_name`); and for each component
    of that typing, `<field>.domain` for its set, `<field>.role` for its
    role word and `<field>.perch` for its perch word, the first where a kind
    is written twice; and for each typing entry and handler binding of the
    header, `<block>.<subject as written>`, the entry from its subject to
    the end of its type. A tuple of fields inside a side has no entries.
    `position_of` answers the meta or the token the lowering kept for a
    part, None for a part it kept none for, which then has no entry."""

    def span(place):
        return SourceSpan(
            file=file,
            line=place.line,
            column=place.column,
            end_line=place.end_line,
            end_column=place.end_column,
        )

    for address, item in item_addresses(term):
        if not isinstance(item, Block):
            continue
        for entry in item.tag.entries:
            if not isinstance(entry, Typer):
                continue
            # a typing entry or a handler binding of the header, under the
            # block's address and its subject as written, `policy.method`
            if isinstance(entry.typing, Handler) or (
                isinstance(entry.typing, Declaration) and isinstance(entry.typing.subject, Path)
            ):
                place = position_of(entry)
                if place is not None:
                    yield f"{address}.{to_source(entry.typing.subject)}", span(place)
                continue
            if not isinstance(entry.typing, Signature):
                continue
            for side, subject in (("in", entry.typing.source), ("out", entry.typing.target)):
                side_address = f"{address}.{side}"
                place = position_of(subject)
                if place is not None:
                    yield side_address, span(place)
                for coordinate in subject.coordinates:
                    place = position_of(coordinate)
                    if not isinstance(coordinate, Coordinate) or place is None:
                        continue
                    field = f"{side_address}.{_written_name(coordinate)}"
                    yield field, span(place)
                    written = set()
                    for component in coordinate.classifiers:
                        kind = _COMPONENT_OF.get(type(component))
                        place = position_of(component)
                        if kind is None or kind in written or place is None:
                            continue
                        written.add(kind)
                        yield f"{field}.{kind}", span(place)


def _names_written(address, item, position_of):
    """The places of the names a line of a block writes, each `(name as
    written, line, column, end line, end column)` at the first place the line
    writes it, `q` or `V[>]`, in the order of the text; empty for every other
    item. `position_of` answers the meta the lowering kept for a name, None
    for a term it kept none for."""
    if "." not in address or not isinstance(item, Statement):
        return ()
    first = {}
    for symbol in nodes(item.core):
        place = position_of(symbol) if isinstance(symbol, Sym) else None
        if place is None:
            continue
        written = to_source(symbol)
        if written not in first or (place.line, place.column) < first[written][1:3]:
            first[written] = (written, place.line, place.column, place.end_line, place.end_column)
    return tuple(sorted(first.values(), key=lambda name: name[1:3]))


def _written_name(coordinate):
    """The name of a listed field as the term holds it: its stem with the
    written mark of its perch, `V[>]` or `V[<]`, or the stem alone, as a
    field of the decision perch is written, bare or `c[~]`."""
    if coordinate.at is None:
        return coordinate.stem
    return coordinate.stem + WRITTEN_MARK[PERCH_OF_SIDE[type(coordinate.at.side)]]


# --- the transformer from a parse tree to the parsed AST ---


RELATION_OF_SYMBOL = {"<": Lt, "<=": Le, "≤": Le, ">": Gt, ">=": Ge, "≥": Ge}


class _Side(NamedTuple):
    """One side of a block header's signature: the fields it lists, as a
    `Subject`, and the components of the typing written after it."""

    subject: object
    types: list


@dataclass(frozen=True)
class _DeclaredValue:
    """The value a declaration assigns after `:=`."""

    value: object


class _RetiredBound(NamedTuple):
    """The bounds a declaration writes after a comma, `γ : ℝ₊, < 2`, the
    spelling AMD-GRAM-004 retired: each a relation and the term it compares
    the declared name with, in the order written. The lowering refuses a
    declaration that carries one."""

    bounds: list


class _Word(NamedTuple):
    """A `!`-marked word of a typing, as its token, whose line and column a
    refusal of the word names, with the `Keyword` arguments written after
    it, `!egm(tol=tol_v)`."""

    token: object
    arguments: tuple = ()


class _Typing(NamedTuple):
    """A typing as written, `: ℝ @ !vlu`: its components, each a `_Word` or
    a set expression, which the consumer of the typing reads, as
    classifiers of a field through the vocabulary (`ToAst._classifiers`) or
    as the method or the grid of a typing entry (`ToAst._typer`)."""

    components: tuple


class _Path(NamedTuple):
    """A dotted subject as written, `policy.evaluate[V[<]].method`: its
    segments, each the head `subject_segment` lowers to, a bare name or the
    selection `bracketed_name` builds."""

    heads: tuple


class ToAst(Transformer):
    """The Lark transformer that rewrites a parse tree, bottom-up, into the
    parsed AST: one callback for each rule of `stage.lark`, named by the rule,
    which answers the term of the rule's children, or a private record that
    the callback of the enclosing rule reads."""

    # the `!`-marked words of the language: the three perches and the roles
    # of a field, spelled once in `bellman.syntax.vocabulary`; the order of a
    # value role there is the order of the `Value` it lowers to
    _VOCAB = {
        ARRIVAL: lambda: Infoset(Arrival()),
        DECISION: lambda: Infoset(Decision()),
        CONTINUATION: lambda: Infoset(Continuation()),
        ROLE_WORD[CONTROL]: lambda: Role(Control()),
        ROLE_WORD[SHOCK]: lambda: Role(Shock()),
        ROLE_WORD[STATE]: lambda: Role(State()),
        **{
            ROLE_WORD[role]: (lambda order=order: Role(Value(order)))
            for order, role in enumerate(VALUE_ROLES)
        },
    }

    # file level
    def file(self, children):
        return FILE(tuple(c for c in children if c is not None))

    def assignment(self, children):
        """A set definition or a function alias and its trailing `:: [...]`
        annotation, which the `Statement` keeps as `annot` exactly as an
        equation and a function definition keep theirs: the description an
        author writes after a set, `Xm := ℝ₊₊ :: ["cash on hand"]`, or after an
        alias is authored information the graph does not determine and is
        retained. A set body is a reserved set, a finite set, a product, a
        comprehension or an interval other than the open-open one, which the
        grammar reads as a tuple; each is wrapped as a `Space`, so that
        `Xa := [0, ā]` defines the Interval term that `a : [0, ā]` types a
        field with, and `H := {i : ℤ | i >= 0, i <= 1}` the Comprehension
        term of a correspondence body."""
        target, val = [c for c in children if not isinstance(c, Token)][:2]
        set_forms = (
            Named, Interval, FiniteSet, Product, IntegerRange, Points, Functions, Comprehension
        )
        if isinstance(val, set_forms):
            val = Space(val)
        return Statement(Assignment(Constant(target), val), self._trailing_annotation(children))

    def _trailing_annotation(self, children):
        metas = [c for c in children if isinstance(c, Token) and c.type == "STMT_META"]
        return parse_annotation(str(metas[0])) if metas else None

    def reserved_set_name(self, children):
        return Space(Named(str(children[0])))

    def metadata(self, children):
        return Metadata(str(children[0]), str(children[1]).strip())

    # declarations
    def declaration(self, children):
        """A declaration line and its trailing `:: [...]` annotation, which a
        `Declare` keeps as `annot` exactly as a `Statement` keeps a line's:
        the description an author writes on a parameter or a shock,
        `β : (0,1) :: ["discount factor"]`, is authored information the graph
        does not determine and is retained. A declaration whose subject is a
        dotted path is a typing entry at file level, `cntn_to_dcsn.evaluate.grid
        : !Cartesian(…)`, routed by its path to the operator it names."""
        head, extras = children[0], children[1:]
        typing = next((extra for extra in extras if isinstance(extra, _Typing)), None)
        if isinstance(head, _Path):
            entry = self._typer(self._path_term(head), typing, extras)
            return Declare(entry.typing, self._trailing_annotation(children))
        # the typing is read before the subject, so that a word no vocabulary
        # holds is refused before a subject that names no field
        classifiers = list(self._classifiers(typing)) if typing is not None else []
        subject = self._subject(head)
        value = next((extra.value for extra in extras if isinstance(extra, _DeclaredValue)), None)
        retired = next((extra for extra in extras if isinstance(extra, _RetiredBound)), None)
        if retired is not None:
            components = typing.components if typing is not None else ()
            raise _retired_bound_refusal(subject, components, retired.bounds)
        classifiers = intersection_of_sets(subject, classifiers)
        return Declare(
            Declaration(subject, tuple(classifiers), value), self._trailing_annotation(children)
        )

    def _subject(self, head):
        if isinstance(head, Subject):
            return head
        coordinate = _coordinate(head)
        if coordinate is not None:
            return Subject((coordinate,))
        name = _selected_name(head)
        raise _refusal(
            f"the declaration declares `{_written(head)}`, a selection from {name}; a "
            f"declaration names its parameter, shock or field by its name",
            f"declare the name, `{name} : …`, and select from it where it is used",
        )

    def retired_bound(self, children):
        signs, bounds = children[0::2], children[1::2]
        return _RetiredBound(
            [(RELATION_OF_SYMBOL[str(sign)](), bound) for sign, bound in zip(signs, bounds)]
        )

    def tuple_subject(self, children):
        return Subject(tuple(children))

    def coordinate(self, children):
        return self._coordinate_of(children)

    def _coordinate_of(self, children):
        """The coordinate a side or a tuple subject lists: a name typed by
        its classifiers, or a tuple of coordinates as a `Group`; a
        selection is refused."""
        head = children[0]
        classifiers = self._classifiers(children[1]) if len(children) > 1 else []
        coordinate = _coordinate(head, classifiers)
        if coordinate is not None:
            return coordinate
        if isinstance(head, Subject):
            return Group(head, tuple(classifiers))
        name = _selected_name(head)
        raise _refusal(
            f"a side of a block header lists `{_written(head)}`, a selection from {name}; "
            f"a side lists each field by its name",
            f"list the field by its name, `{name}`, with its perch mark where it needs one, "
            f"`{name}[>]`",
        )

    def declared_value(self, children):
        return _DeclaredValue(children[0])

    # the declaration of a distribution (rule `law`) and the function
    # definition: both are `stmt`s of `dynspec_full.asdl`, so each is wrapped
    # in Statement(core, annot) as an equation is, and a trailing `:: [...]`
    # annotation (the STMT_META token) is kept as `annot`.
    def law(self, children):
        parts = [c for c in children if not isinstance(c, Token)]
        subject, expr = parts[0], parts[1]

        def stems(s):
            out = []
            for c in s.coordinates:
                out.extend(stems(c.inner) if isinstance(c, Group) else [c.stem])
            return out

        if isinstance(subject, str):
            subjects = [subject]
        elif isinstance(subject, Subject):
            typed = _typed_names(subject)
            if typed:
                names = _subject_text(subject)
                raise _refusal(
                    f"the distribution is declared for {names}, and its subject types "
                    f"{' and '.join(typed)} inside the parentheses; a `~` line names its "
                    f"shocks, and the type of a shock is read from the shock's own declaration",
                    f"write the names alone, `{names} ~ …`, and the type of each shock on a "
                    f"line of its own, as in `{typed[0]} : ℝ`",
                )
            subjects = stems(subject)
        elif isinstance(subject, Sym) and isinstance(subject.symbol, Constant):
            subjects = [subject.symbol.name]  # y[~] ~ law
        else:
            name = _selected_name(subject)
            raise _refusal(
                f"the distribution is declared for `{_written(subject)}`, a selection from "
                f"{name}; a `~` line names its shocks by name",
                f"write the shock's name, `{name} ~ …`, or the names of shocks drawn "
                f"jointly as a tuple, `(y, z) ~ …`",
            )
        return Statement(Law(tuple(subjects), expr), self._trailing_annotation(children))

    def function_definition(self, children):
        parts = [c for c in children if not isinstance(c, Token)]
        name, params, body = parts[0], parts[1:-1], parts[-1]
        note = self._trailing_annotation(children)
        if isinstance(body, (Interval, FiniteSet, Product, Comprehension)):
            return Statement(CorrDef(name, tuple(params), body), note)
        return Statement(FuncDef(name, tuple(params), body), note)

    def function_parameter(self, children):
        return Coordinate(children[0], None, tuple(self._classifiers(children[1])))

    def comprehension(self, children):
        """`{c : ℝ₊₊ | c < x}`: the comprehension of a correspondence body,
        its one binder, the set that types it as the base, and the
        conditions in the order written."""
        parts = [c for c in children if not isinstance(c, Token)]
        name, typing, conds = parts[0], parts[1], parts[2:]
        components = self._classifiers(typing)
        if len(components) != 1 or not isinstance(components[0], Domain):
            written_typing = " @ ".join(_component_text(c) for c in typing.components)
            written = f"{{{name} : {written_typing} | {', '.join(to_source(cond) for cond in conds)}}}"
            raise _refusal(
                f"the binder {name} of the set `{written}` is typed by `{written_typing}`; the "
                f"binder of a set written by comprehension is typed by one set, with no role or "
                f"perch word",
                f"type the binder by its set alone, as in `{{{name} : ℝ₊ | …}}`",
            )
        return Comprehension(Subject((Coordinate(name),)), components[0].space, tuple(conds))

    def comprehension_condition(self, children):
        return Rel(children[0], RELATION_OF_SYMBOL[str(children[1])](), children[2])

    def comprehension_equality(self, children):
        return Rel(children[0], Eq(), children[1])

    def conditional(self, children):
        """A definition by cases, `if test then a else b`: the test, a
        comparison of two formulas, and the two branches, each a formula or
        a further conditional."""
        test, then, otherwise = children
        return Conditional(test, then, otherwise)

    # statements and blocks
    def block(self, children):
        return Block(children[0], tuple(children[1:]))

    def header(self, children):
        # the groups a `|` opens are spelling: every entry of every group is
        # an entry of the one annotation
        return Annotation(tuple(children))

    def key_value(self, children):
        key, val = children
        return KeyValue(key, val if isinstance(val, str) else number_value(val))

    def word_tag(self, children):
        text = str(children[0])
        return Typer(Marked(Node())) if text == "!node" else Tag(text)

    def bare_tag(self, children):
        if len(children) == 1:
            return Tag(children[0])
        return Tagged(Word(children[0], children[1]))

    def path(self, children):
        return _Path(tuple(children))

    def typing_entry(self, children):
        return self._typer(self._path_term(children[0]), children[1])

    def binding(self, children):
        """A handler binding, `policy.handler : "cons-port:egm"`: the path of
        the handler component and the program, the quotes removed."""
        subject = self._path_term(children[0])
        written = to_source(subject)
        if subject.segments[-1].name != "handler":
            raise _refusal(
                f"the entry `{written} : {children[1]}` binds a quoted string to "
                f"`{written}`; a quoted string names the program of the handler component "
                f"alone, and a method or a grid is typed by a !-word",
                f"write `{written}.handler : {children[1]}` for a handler, or a !-word, "
                f"`{written} : !<word>`",
            )
        return Typer(Handler(subject, str(children[1]).strip("\"'")))

    def file_binding(self, children):
        return Declare(children[0].typing, self._trailing_annotation(children))

    # --- the typing entries, and the terms their subjects and types lower to ---

    def _path_term(self, head):
        """The `Path` a subject as written names: the segments of a `_Path`,
        or the one segment of a bare head, each a name with its selectors,
        `Key` for a name, `Pos` for a number and `Term` for a term; a perch
        mark is refused, since a path names an operator's component and a
        field is named inside a selector, `evaluate[V[<]]`."""
        heads = head.heads if isinstance(head, _Path) else (head,)
        return Path(tuple(self._segment(each, heads) for each in heads))

    def _segment(self, head, heads):
        selectors = []
        while isinstance(head, Select):
            selectors.insert(0, head.sel)
            head = head.family
        if isinstance(head, str):
            return Segment(head, tuple(selectors))
        if isinstance(head, Sym) and isinstance(head.symbol, Constant):
            return Segment(head.symbol.name, tuple(selectors))
        written = ".".join(_written(each) for each in heads)
        raise _refusal(
            f"the path `{written}` carries the perch mark of `{_written(head)}`; a path names "
            f"an operator's component by names, and a field with its perch mark is named "
            f"inside a selector",
            f"write the field inside the selector of the operator that stores it, "
            f"`evaluate[{_written(head)}].method`",
        )

    _COMPONENTS = ("method", "grid")

    def _typer(self, subject, typing, extras=()):
        """The `Typer` of a typing entry: a `Declaration` of the path with
        one classifier, the `Method` or the `Grid` that the last segment of
        the path names and the one `!`-word of the typing supplies."""
        written = to_source(subject)
        component = subject.segments[-1].name
        if any(isinstance(extra, (_DeclaredValue, _RetiredBound)) for extra in extras):
            raise _refusal(
                f"the typing entry of `{written}` carries a value or a condition; a typing "
                f"entry types a component of an operator and takes neither",
                f"write the entry alone, `{written} : …`",
            )
        if component not in self._COMPONENTS:
            raise _refusal(
                f"the entry types `{written}`, whose last segment `{component}` names no "
                f"component of an operator; a typing entry types the method or the grid "
                f"component, and a handler is bound by a quoted string",
                f"write `{written}.method : !<word>`, `{written}.grid : !Cartesian(…)` or "
                f'`{written}.handler : "…"`',
            )
        if len(typing.components) != 1 or not isinstance(typing.components[0], _Word):
            written_typing = " @ ".join(_component_text(c) for c in typing.components)
            raise _refusal(
                f"the {component} component `{written}` is typed by `{written_typing}`; a "
                f"{component} component is typed by one !-word",
                f"write one word after the colon, `{written} : "
                + ("!<word>(…)`" if component == "method" else "!Cartesian(…)`"),
            )
        word = typing.components[0]
        name = str(word.token)[1:]
        if component == "method":
            classifier = Method(Word(name, word.arguments))
        else:
            classifier = Grid(self._grid(name, word.arguments, written, word.token))
        return Typer(Declaration(subject, (classifier,), None))

    # the grid words the language builds, each with the method that reads its
    # term: the words are those of the printer's table `GRID_WORDS`, by the
    # term class each method builds; and the words reserved by name for grid
    # constructors no build implements (AMD-MT-003 build contract §§1-2)
    _GRIDS = {
        GRID_WORDS[term]: method
        for term, method in (
            (Cartesian, "_cartesian"),
            (PointGrid, "_points"),
            (Fibred, "_fibred"),
        )
    }
    _GRID_LIST = ", ".join(f"!{word}" for word in tuple(GRID_WORDS.values())[:-1]) + (
        f" and !{tuple(GRID_WORDS.values())[-1]}"
    )
    _RESERVED_GRIDS = ("TensorUnion", "Image", "Smolyak")

    def _grid(self, name, arguments, written, at=None, where=""):
        """The grid term of one grid word with its keyword arguments: a
        `Cartesian`, a `PointGrid` or a `Fibred`, each with the predicate
        words written after `require`. `written` is the path of the grid
        component, `at` the token of the outer word, and `where` the words
        that place a nested grid, ` in the base of !Fibred`, empty for the
        outer word. A reserved word and a word that is no grid constructor
        are refused; the meaning of a term is judged at binding
        (`stage/grids.py`)."""
        example = f"`{written} : !Cartesian(a=(a_min, a_max, n_a))`"
        if name in self._RESERVED_GRIDS:
            raise _refusal(
                f"the grid component `{written}` is typed{where} by `!{name}`, a grid "
                f"constructor that is reserved by name and not built",
                f"the grid constructors built are {self._GRID_LIST}, {example}",
                at,
            )
        if name not in self._GRIDS:
            raise _refusal(
                f"the grid component `{written}` is typed{where} by `!{name}`, which is no "
                f"grid kind of the language",
                f"the grid kinds are {self._GRID_LIST}, {example}",
                at,
            )
        return getattr(self, self._GRIDS[name])(arguments, written, at, where)

    def _cartesian(self, arguments, written, at, where):
        """The `Cartesian` of `!Cartesian(...)`: one factor per keyword, read
        by its shape (`_factor`), and the predicate words of `require`,
        recognized by their shape alone, so that a coordinate named
        `require` keeps the forms of a factor. At least one factor is
        written."""
        factors, require = [], ()
        for keyword in arguments:
            if keyword.key == "require" and _predicate_shaped(keyword.value):
                require = self._requirements(keyword.value, "Cartesian", written)
            else:
                factors.append(self._factor(keyword, written))
        if not factors:
            raise _refusal(
                f"the grid `!Cartesian` of `{written}`{where} names no factor; a grid names "
                f"at most one factor per coordinate of the function the place holds, and at "
                f"least one",
                f"write the factors, `{written} : !Cartesian(a=(a_min, a_max, n_a))`",
                at,
            )
        return Cartesian(tuple(factors), require)

    def _points(self, arguments, written, at, where):
        """The `PointGrid` of `!Points(nodes=P)`: the name of the declared
        points and the predicate words of `require`; `!Points` alone is the
        empty grid."""
        nodes, require = None, ()
        for keyword in arguments:
            if keyword.key == "nodes" and isinstance(keyword.value, Name):
                nodes = keyword.value.name
            elif keyword.key == "require" and _predicate_shaped(keyword.value):
                require = self._requirements(keyword.value, "Points", written)
            else:
                raise _refusal(
                    f"the grid `!Points` of `{written}`{where} writes `{to_source(keyword)}`; "
                    f"`!Points` takes the name of a declared set of points, `nodes=P`, and the "
                    f"predicate words its grid satisfies, `require=!Empty`",
                    f"write `{written} : !Points(nodes=P)` with a declared set of points, or "
                    f"`!Points` alone for the empty grid",
                )
        return PointGrid(nodes, require)

    def _fibred(self, arguments, written, at, where):
        """The `Fibred` of `!Fibred(base=…, fibre=…)`: the grid of the base
        states and the grid of the control at each of them, each a nested
        grid word, and the predicate words of `require`."""
        held, require = {}, ()
        for keyword in arguments:
            if keyword.key in ("base", "fibre") and isinstance(keyword.value, Nested):
                inner = keyword.value.word
                held[keyword.key] = self._grid(
                    inner.name, inner.arguments, written, at, f" in the {keyword.key} of `!Fibred`"
                )
            elif keyword.key == "require" and _predicate_shaped(keyword.value):
                require = self._requirements(keyword.value, "Fibred", written)
            else:
                raise _refusal(
                    f"the grid `!Fibred` of `{written}`{where} writes `{to_source(keyword)}`; "
                    f"`!Fibred` takes a grid word for its base states, `base=!Points(nodes=B)`, "
                    f"a grid word for the control at each of them, "
                    f"`fibre=!Cartesian(c=(Γ_c, n_c))`, and the predicate words its grid "
                    f"satisfies, `require=!Empty`",
                    f"write `{written} : !Fibred(base=!Points(nodes=B), "
                    f"fibre=!Cartesian(c=(Γ_c, n_c)))`",
                )
        missing = tuple(name for name in ("base", "fibre") if name not in held)
        if missing:
            raise _refusal(
                f"the grid `!Fibred` of `{written}`{where} names no {' and no '.join(missing)}; "
                f"a fibred grid pairs each state of its base with the points of its fibre",
                f"write `{written} : !Fibred(base=!Points(nodes=B), "
                f"fibre=!Cartesian(c=(Γ_c, n_c)))`",
                at,
            )
        return Fibred(held["base"], held["fibre"], require)

    def _requirements(self, value, word, written):
        """The predicate words written after `require`, by their names, in
        written order: one word, `!UniformCartesian`, or a tuple of words.
        A predicate word takes no arguments."""
        words = (value,) if isinstance(value, Nested) else value.items
        for each in words:
            if each.word.arguments:
                raise _refusal(
                    f"the grid `!{word}` of `{written}` requires `{to_source(each)}`, a "
                    f"predicate word written with arguments; a predicate word takes none",
                    f"write the word alone, `require=!{each.word.name}`",
                )
        return tuple(each.word.name for each in words)

    def _factor(self, keyword, written):
        """One factor of a grid, read by the shape of its value: a name is
        the node set or the expectation operator the coordinate takes its
        nodes from, a pair is a feasible set with a count, a triple is the
        bounds and the count, a fourth element the spacing word."""
        coordinate, value = keyword.key, keyword.value
        shapes = (
            f"a factor of `{written}` is a triple, `{coordinate}=(lower, upper, count)`, with an "
            f"optional spacing word, `{coordinate}=(lower, upper, count, !expmult)`, a pair, "
            f"`{coordinate}=(set, count)`, or a name, `{coordinate}=nodes`"
        )
        if isinstance(value, Name):
            return Listed(coordinate, value.name)
        if not isinstance(value, Values) or not 2 <= len(value.items) <= 4:
            raise _refusal(
                f"the factor `{coordinate}={to_source(value)}` of `{written}` has no shape of a "
                f"factor",
                shapes,
            )
        items = value.items
        settings = items[:3] if len(items) > 2 else items[1:]
        if not all(isinstance(item, (Name, Literal)) for item in settings):
            raise _refusal(
                f"the factor `{coordinate}={to_source(value)}` of `{written}` writes a bound or "
                f"a count that is no name of a setting and no number",
                shapes,
            )
        if len(items) == 2:
            if not isinstance(items[0], Name):
                raise _refusal(
                    f"the factor `{coordinate}={to_source(value)}` of `{written}` names no set "
                    f"before its count",
                    f"a control's factor is its feasible set with a count, `{coordinate}=(Γ, n)`",
                )
            return Feasible(coordinate, items[0].name, items[1])
        spacing = None
        if len(items) == 4:
            if not isinstance(items[3], Nested):
                raise _refusal(
                    f"the factor `{coordinate}={to_source(value)}` of `{written}` writes "
                    f"`{to_source(items[3])}` as its fourth element, which is no spacing word",
                    f"a spacing is a !-word, `{coordinate}=(lower, upper, count, !expmult)`",
                )
            spacing = items[3].word
        return Spaced(coordinate, items[0], items[1], items[2], spacing)

    def quoted_tag(self, children):
        return Tag(str(children[0]).strip("\"'"))

    def signature(self, children):
        source, target = children
        return Typer(
            Signature(
                source=source.subject,
                source_types=tuple(source.types),
                target=target.subject,
                target_types=tuple(target.types),
            )
        )

    def side(self, children):
        if len(children) == 1 and isinstance(children[0], _Side):
            return children[0]  # the bare single-coordinate form
        coords = [c for c in children if isinstance(c, (Coordinate, Group))]
        rest = [c for c in children if isinstance(c, _Typing)]
        types = self._classifiers(rest[0]) if rest else []
        return _Side(subject=Subject(tuple(coords)), types=types)

    def bare_side(self, children):
        return _Side(subject=Subject((self._coordinate_of(children),)), types=[])

    def statement(self, children):
        core = children[0]
        rest = list(children[1:])
        if rest and isinstance(rest[0], (Rel, Between)):
            core = Slack(core, rest.pop(0))
        note = parse_annotation(str(rest[0])) if rest else None
        return Statement(core, note)

    def block_declaration(self, children):
        """A declaration inside a block body with its clause, `μ[>] : ℝ₊ ⟂
        a >= 0`: a `Complementary` holding the declared multiplier and its
        bound, the trailing annotation kept as a top-level declaration keeps
        it."""
        classifiers = self._classifiers(
            next(extra for extra in children[1:] if isinstance(extra, _Typing))
        )
        subject = self._subject(children[0])
        bound = next(extra for extra in children[1:] if isinstance(extra, (Rel, Between)))
        return Declare(
            Complementary(Declaration(subject, tuple(classifiers), None), bound),
            self._trailing_annotation(children),
        )

    def slackness_clause(self, children):
        """The bound of a clause: one relation, `a >= 0`, or a chain of two,
        `0 <= c_p <= w_d`, whose signs the term keeps for the typing's
        refusal of a descending, strict or mixed chain."""
        if len(children) == 3:
            return Rel(children[0], RELATION_OF_SYMBOL[str(children[1])](), children[2])
        return Between(
            lower=children[0],
            lo=RELATION_OF_SYMBOL[str(children[1])](),
            middle=children[2],
            hi=RELATION_OF_SYMBOL[str(children[3])](),
            upper=children[4],
        )

    # typing: one colon, then an unordered @-joined conjunction of
    # components, kept as written and read by the consumer of the typing:
    # a field's typing classifies its words through the vocabulary table
    # (`_classifiers`), a typing entry reads its one word as a method or a
    # grid (`_typer`)
    def typing(self, children):
        return children[0]

    def type(self, children):
        return _Typing(tuple(children))

    def _classifiers(self, typing):
        """The classifiers of a field's typing: each `!`-marked word through
        the vocabulary table, each set expression as a `Domain`."""
        return [
            self._classifier_of_word(c) if isinstance(c, _Word) else Domain(c)
            for c in typing.components
        ]

    def _classifier_of_word(self, word):
        """The classifier the `!`-marked word names, or a refusal of a word
        the vocabulary does not hold or of a word that carries arguments.

        `word.token` is the TAGBANG token, so the refusal carries the line
        and the column of the word itself, which `parse_with_spans` releases
        and `factory/elaboration.py` writes as the position of the refusal.
        The sentence written after the marked line is the action, which
        stands on the refusal in `write`."""
        token = word.token
        name = str(token)[1:]
        if name in RETIRED_ROLE_WORDS:
            raise _refusal(
                f"the file writes `!{name}` here, a role word the language has retired: a "
                f"backward header lists value fields and controls alone, and a derivative "
                f"of a value is written as the term `D_{{x}}V`, with `x` a state coordinate "
                f"of the perch at which the value stands, such as `D_{{m}}V` or `D_{{a}}V[>]`",
                "Remove the field from the header, write the line that defined it as a "
                "derivative line of the value, such as `D_{m}V = …`, and read the derivative "
                "where a line needs it as a term such as `D_{a}V[>]`",
                token,
                rule="marginal-role-retired",
            )
        if name not in self._VOCAB:
            raise _refusal(
                f"the file writes `!{name}` here, which is no word-type of the language",
                "the word-types are " + ", ".join("!" + w for w in sorted(self._VOCAB)),
                token,
            )
        if word.arguments:
            raise _refusal(
                f"the file writes `!{name}` here with arguments; a role or a perch word "
                f"takes none",
                f"write the word alone, `!{name}`",
                token,
            )
        return self._VOCAB[name]()

    def word_type(self, children):
        # the token itself, whose line and column a refusal of the word
        # names, with its keyword arguments
        return _Word(children[0], children[1] if len(children) > 1 else ())

    # the keyword arguments of a word, `(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)`
    def arguments(self, children):
        keys = [keyword.key for keyword in children]
        repeated = next((key for n, key in enumerate(keys) if key in keys[:n]), None)
        if repeated is not None:
            raise _refusal(
                f"the argument `{repeated}` is written twice in `({', '.join(to_source(k) for k in children)})`; "
                f"each keyword argument is written once",
                f"keep one `{repeated}=…`",
            )
        return tuple(children)

    def keyword(self, children):
        return Keyword(children[0], children[1])

    def argument_name(self, children):
        return Name(children[0])

    def argument_number(self, children):
        return Literal(number_value(children[0]))

    def argument_string(self, children):
        return Quoted(str(children[0]).strip("\"'"))

    def argument_tuple(self, children):
        return Values(tuple(children))

    def argument_word(self, children):
        word = children[0]
        return Nested(Word(str(word.token)[1:], word.arguments))

    # set expressions
    def open_interval_factor(self, children):
        """The two endpoints of `(a, b)` before × in a correspondence body."""
        value = children[0]
        if len(value.items) != 2:
            raise _refusal(
                f"the factor `{to_source(value)}` before × has {len(value.items)} entries; "
                "an open interval has two endpoints",
                "write an interval with two endpoints, `(a, b) × …`",
            )
        return Interval(
            Range(left=Open(), lower=value.items[0], upper=value.items[1], right=Open())
        )

    def set_product(self, children):
        factors = []
        for c in children:
            factors.extend(c.factors if isinstance(c, Product) else [c])
        return Product(tuple(factors))

    def named_set(self, children):
        return Named(str(children[0]))

    def interval_open_open(self, children):
        return Interval(Range(left=Open(), lower=children[0], upper=children[1], right=Open()))

    def interval_open_closed(self, children):
        return Interval(Range(left=Open(), lower=children[0], upper=children[1], right=Closed()))

    def interval_closed_open(self, children):
        return Interval(Range(left=Closed(), lower=children[0], upper=children[1], right=Open()))

    def interval_closed_closed(self, children):
        return Interval(Range(left=Closed(), lower=children[0], upper=children[1], right=Closed()))

    def brace_set(self, children):
        """One brace list of formulas, read as one of three sets: names alone
        are a finite set of labels, `{work, retire}`, the term the grammar
        read before the brace list admitted formulas; number literals alone
        are a set of numbers, `{0, 1}`; and a list followed by the set its
        members lie in, `{0, θ} ⊂ ℝ`, is a set of numbers whose members are
        the formulas, in authored order. A list that mixes names with numbers
        or arithmetic and names no carrier is refused: without the carrier the
        names would be labels."""
        members = [c for c in children if isinstance(c, expr)]
        supersets = [c for c in children if isinstance(c, setexpr)]
        superset = supersets[0] if supersets else None
        written = ", ".join(to_source(m) for m in members)
        if superset is not None:
            if not isinstance(superset, (Named, Interval)):
                raise _refusal(
                    f"the set `{{{written}}} ⊂ {to_source(superset)}` names after `⊂` a set that "
                    f"is no named set and no interval",
                    f"a named set or an interval after `⊂`, `{{{written}}} ⊂ ℝ`",
                )
            return Points(tuple(members), superset)
        if all(isinstance(m, Sym) and isinstance(m.symbol, Constant) for m in members):
            return FiniteSet(tuple(m.symbol.name for m in members))
        if all(_number_literal(m) for m in members):
            return Points(tuple(members), None)
        if any(isinstance(m, Sym) and isinstance(m.symbol, Constant) for m in members):
            raise _refusal(
                f"the set `{{{written}}}` lists a name beside a number or an arithmetic "
                f"expression, and names no set its members lie in; names alone are labels, "
                f"numbers alone are numbers",
                f"the set the members lie in after the braces, `{{{written}}} ⊂ ℝ`, for a set "
                f"of numbers, or names alone for a set of labels",
            )
        raise _refusal(
            f"the set `{{{written}}}` lists an arithmetic expression beside its numbers and "
            f"names no set its members lie in",
            f"each member as an integer, an integer-valued ratio or decimal, `{{0, 6/2}}`, or the "
            f"set the members lie in after the braces, `{{{written}}} ⊂ ℝ`",
        )

    def integer_range(self, children):
        lower, upper = [c for c in children if not isinstance(c, Token)]
        return IntegerRange(lower, upper)

    def set_functions(self, children):
        domain, codomain = children
        return Functions(domain, codomain)

    def set_union(self, children):
        """`A \\/ B`, the union of two sets of numbers, kept in the one form
        of `union_of`."""
        left, right = children
        _refuse_side_without_numbers("\\/", left, right)
        return union_of((left, right))

    def set_difference(self, children):
        """`A \\ B`, the difference of two sets of numbers, its sides as
        written."""
        left, right = children
        _refuse_side_without_numbers("\\", left, right)
        return SetDifference(left, right)

    # the equations and the expression ladder
    def equality(self, children):
        return Equation(*children)

    def inequality(self, children):
        return Inequality(children[0], RELATION_OF_SYMBOL[str(children[1])](), children[2])

    def add(self, children):
        return Add(*children)

    def sub(self, children):
        return Sub(*children)

    def neg(self, children):
        return Neg(children[0])

    def mul(self, children):
        return Mul(*children)

    def div(self, children):
        return Div(*children)

    def pow(self, children):
        return Pow(*children)

    # the atoms: numbers, names, tuples, selections and calls
    def number(self, children):
        return Number(number_value(children[0]))

    def infinity(self, children):
        return Sym(Constant("inf"))

    def constant(self, children):
        return Sym(Constant(children[0]))

    def tuple(self, children):
        return Tuple(tuple(children))

    def tuple_selection(self, children):
        family, sel = children
        if isinstance(sel, Sym) and isinstance(sel.symbol, Constant):
            return Select(family, Key(sel.symbol.name))
        if isinstance(sel, Number):
            return Select(family, Pos(_position_literal(sel.value, to_source(family))))
        family_text = to_source(family)
        raise _refusal(
            f"the selection `{family_text}[{to_source(sel)}]` selects by `{to_source(sel)}`, "
            f"which is computed; a selection reads a position or a name",
            f"write a position, `{family_text}[1]`, or a name declared with a finite set, "
            f"`{family_text}[d]`",
        )

    def bracketed_name(self, children):
        """A name with its selectors: in a formula, a perch mark, a name key
        or a position, `V[>]`, `x[work]`, `q[2]`; in the subject of a typing
        entry also a term, `evaluate[V[<]]`, `evaluate[D_{k}V[<]]`, which
        selects by `Term`."""
        stem, sels = children[0], children[1:]
        first = sels[0]
        if isinstance(first, Token) and first.type == "PMARK":
            if str(first) == "~":
                # the optional decision mark: a field at the decision
                # perch is written bare, so c[~] is the bare name c
                expr = Sym(Constant(stem))
            else:
                perch = Arrival() if str(first) == "<" else Continuation()
                expr = Sym(Variable(stem, At(perch), 0))
        elif isinstance(first, Token):  # NUMBER
            expr = Select(
                Sym(Constant(stem)), Pos(_position_literal(number_value(first), stem, first))
            )
        elif isinstance(first, str):  # name key
            expr = Select(Sym(Constant(stem)), Key(first))
        else:  # a term, in the subject of a typing entry
            expr = Select(Sym(Constant(stem)), Term(first))
        for extra in sels[1:]:
            if isinstance(extra, Token) and extra.type == "PMARK":
                keys = "".join(
                    f"[{selector}]"
                    for selector in sels
                    if not isinstance(selector, Token) or selector.type != "PMARK"
                )
                raise _refusal(
                    f"the perch mark `{extra}` follows the first selector",
                    f"write one perch mark first, as `{stem}[{extra}]{keys}`",
                    extra,
                )
            if isinstance(extra, Token):
                sel = Pos(_position_literal(number_value(extra), to_source(expr), extra))
            elif isinstance(extra, str):
                sel = Key(extra)
            else:
                sel = Term(extra)
            expr = Select(expr, sel)
        return expr

    def operator_call(self, children):
        head = children[0].rstrip("_")
        i = 1
        subs = []
        while i < len(children) and isinstance(children[i], (str, In)):
            subs.append(Var(children[i]) if isinstance(children[i], str) else children[i])
            i += 1
        return Operator(head, tuple(subs), tuple(children[i:]))

    def member_subscript(self, children):
        return In(children[0], children[1])

    def call(self, children):
        return Call(children[0], tuple(children[1:]))

    def name(self, children):
        """A name as its text. `if`, `then` and `else` are words of the
        language and no names: one that the parser read as a name, in a
        declaration, a definition, a binder, a header or a formula, is
        refused where it is written (AMD-GRAM-006)."""
        word = str(children[0])
        if word in CASE_WORDS:
            raise _refusal(
                f"the file writes `{word}` as a name; {CASE_WORDS_ARE_NO_NAMES}",
                f"Write another name in place of `{word}`",
                children[0],
            )
        return word


# --- the transformer that keeps the position of each item ---


class _Kept(NamedTuple):
    """An item the lowering constructed and the Lark meta of its parse node."""

    item: object
    meta: object


class _ToAstWithPositions(ToAst):
    """ToAst that also keeps, for each authored item it constructs — the
    result of one of the eight item rules — the Lark meta of the parse
    node from which the item was constructed, in a dict keyed by the
    item's identity; the dict is an attribute of the instance and is not
    returned.

    `transform` also releases a refusal of the lowering as the lowering wrote
    it: the transformer wraps every exception a callback raises in a
    `VisitError` whose sentence opens `Error trying to process rule "…"`, the
    rule being Lark's and not the language's, and this class raises the
    refusal itself instead, with the position it carries, or, where it
    carries none, the position of the item the callback was lowering, in
    the file `file` names.

    It also keeps the place of each part of a block header's sides, a
    coordinate, a side's subject and each component of a typing, for
    `_component_spans`; the parts are kept apart from the items, and
    `position_of` reads the items alone."""

    def __init__(self, file=None):
        super().__init__()
        # the file the parse names; the attribute `file` would shadow the
        # callback of the grammar rule `file`
        self._file = file
        # id(item) -> _Kept(item, meta); the dict holds the item itself, so
        # id(item) is not reused while the dict exists.
        self._positions = {}
        # id(part) -> _Kept(part, place): a coordinate, a side's subject or
        # a typing's component, with the meta or the token of its text
        self._parts = {}
        # id(symbol) -> _Kept(symbol, meta): a name a formula writes, bare or
        # with its perch mark, for `_names_written`
        self._names = {}

    def transform(self, tree):
        try:
            return super().transform(tree)
        except VisitError as wrapped:
            refusal = wrapped.orig_exc
            meta = getattr(wrapped.obj, "meta", None)
            if isinstance(refusal, ConstructionError):
                if refusal.line is None and meta is not None and not meta.empty:
                    refusal.line, refusal.column = meta.line, meta.column
                    refusal.end_line, refusal.end_column = meta.end_line, meta.end_column
                refusal.file = refusal.file or self._file
            clear_frames(wrapped.__traceback__)
            raise refusal from None

    def position_of(self, item):
        """The Lark meta recorded for an item this instance constructed."""
        kept = self._positions.get(id(item))
        if kept is None or kept.item is not item:
            raise LookupError(
                f"no source position was recorded for this "
                f"{type(item).__name__}; every item rule must be listed "
                f"in {type(self).__name__}"
            )
        return kept.meta

    @v_args(meta=True)
    def metadata(self, meta, children):
        return self._keep(super().metadata(children), meta)

    @v_args(meta=True)
    def assignment(self, meta, children):
        return self._keep(super().assignment(children), meta)

    @v_args(meta=True)
    def function_definition(self, meta, children):
        return self._keep(super().function_definition(children), meta)

    @v_args(meta=True)
    def declaration(self, meta, children):
        return self._keep(super().declaration(children), meta)

    @v_args(meta=True)
    def block_declaration(self, meta, children):
        return self._keep(super().block_declaration(children), meta)

    @v_args(meta=True)
    def law(self, meta, children):
        return self._keep(super().law(children), meta)

    @v_args(meta=True)
    def block(self, meta, children):
        return self._keep(super().block(children), meta)

    @v_args(meta=True)
    def statement(self, meta, children):
        return self._keep(super().statement(children), meta)

    @v_args(meta=True)
    def file_binding(self, meta, children):
        return self._keep(super().file_binding(children), meta)

    def _keep(self, item, meta):
        self._positions[id(item)] = _Kept(item, meta)
        return item

    # --- the names a formula writes (_names_written) ---

    def name_position(self, symbol):
        """The meta kept for a name a formula writes, a `Sym` this instance
        constructed; None for a term it kept none for."""
        kept = self._names.get(id(symbol))
        return kept.meta if kept is not None and kept.item is symbol else None

    @v_args(meta=True)
    def constant(self, meta, children):
        symbol = super().constant(children)
        self._names[id(symbol)] = _Kept(symbol, meta)
        return symbol

    @v_args(meta=True)
    def bracketed_name(self, meta, children):
        # a name with its perch mark is kept; a selection, `q[2]`, is not
        term = super().bracketed_name(children)
        if isinstance(term, Sym):
            self._names[id(term)] = _Kept(term, meta)
        return term

    # --- the parts of a block header's sides (_component_spans) ---

    def part_position(self, part):
        """The meta or the token kept for a part of a block header that
        this instance constructed; None for a part it kept none for."""
        kept = self._parts.get(id(part))
        return kept.meta if kept is not None and kept.item is part else None

    def _keep_part(self, part, place):
        self._parts[id(part)] = _Kept(part, place)
        return part

    @v_args(meta=True)
    def coordinate(self, meta, children):
        return self._keep_part(super().coordinate(children), meta)

    @v_args(meta=True)
    def side(self, meta, children):
        side = super().side(children)
        self._keep_part(side.subject, meta)
        return side

    @v_args(meta=True)
    def bare_side(self, meta, children):
        # a bare side is its one coordinate, and both are kept at its place
        side = super().bare_side(children)
        self._keep_part(side.subject.coordinates[0], meta)
        self._keep_part(side.subject, meta)
        return side

    def _classifiers(self, typing):
        # a word's token carries its place; a set's place is its rule's
        classifiers = super()._classifiers(typing)
        for classifier, component in zip(classifiers, typing.components):
            place = component.token if isinstance(component, _Word) else self.part_position(component)
            if place is not None:
                self._keep_part(classifier, place)
        return classifiers

    @v_args(meta=True)
    def typing_entry(self, meta, children):
        return self._keep_part(super().typing_entry(children), meta)

    @v_args(meta=True)
    def binding(self, meta, children):
        return self._keep_part(super().binding(children), meta)

    @v_args(meta=True)
    def named_set(self, meta, children):
        return self._keep_part(super().named_set(children), meta)

    @v_args(meta=True)
    def brace_set(self, meta, children):
        return self._keep_part(super().brace_set(children), meta)

    @v_args(meta=True)
    def integer_range(self, meta, children):
        return self._keep_part(super().integer_range(children), meta)

    @v_args(meta=True)
    def set_functions(self, meta, children):
        return self._keep_part(super().set_functions(children), meta)

    @v_args(meta=True)
    def set_product(self, meta, children):
        return self._keep_part(super().set_product(children), meta)

    @v_args(meta=True)
    def set_union(self, meta, children):
        return self._keep_part(super().set_union(children), meta)

    @v_args(meta=True)
    def set_difference(self, meta, children):
        return self._keep_part(super().set_difference(children), meta)

    @v_args(meta=True)
    def interval_open_open(self, meta, children):
        return self._keep_part(super().interval_open_open(children), meta)

    @v_args(meta=True)
    def interval_open_closed(self, meta, children):
        return self._keep_part(super().interval_open_closed(children), meta)

    @v_args(meta=True)
    def interval_closed_open(self, meta, children):
        return self._keep_part(super().interval_closed_open(children), meta)

    @v_args(meta=True)
    def interval_closed_closed(self, meta, children):
        return self._keep_part(super().interval_closed_closed(children), meta)


# --- the functions the callbacks call ---


def parse_annotation(raw):
    """The `Annotation` of a line's trailing `:: [...]` text, `:: [id=x,
    !node]`: a quoted entry and a bare word are tags, `key=value` is a
    key-value entry, and `!node` is the node mark; a text without brackets is
    one tag, its quotes removed. The grammar reads the annotation as one
    token, `STMT_META`, which this function divides into its entries."""
    text = str(raw).strip().lstrip(":").strip()
    entries = []
    if text.startswith("[") and text.endswith("]"):
        for part in _split_entries(text[1:-1]):
            part = part.strip()
            if part.startswith('"'):
                entries.append(Tag(part))
            elif "=" in part:
                k, v = (p.strip() for p in part.split("=", 1))
                entries.append(KeyValue(k, v))
            elif part == "!node":
                entries.append(Typer(Marked(Node())))
            elif part:
                entries.append(Tag(part))
    else:
        entries.append(Tag(text.strip("\"'")))
    return Annotation(tuple(entries))


def _split_entries(body):
    """The comma-separated entries of an annotation body; a comma inside a
    double-quoted explanation does not separate entries."""
    parts, buf, quoted = [], [], False
    for character in body:
        if character == '"':
            quoted = not quoted
        if character == "," and not quoted:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(character)
    parts.append("".join(buf))
    return parts


def _coordinate(head, classifiers=()):
    """The coordinate a name as written declares, typed by `classifiers`: a
    bare name, a name with a perch mark, or a name marked `[~]`, which is the
    bare name; None for any other head, a selection or a dotted path."""
    if isinstance(head, str):
        return Coordinate(head, None, tuple(classifiers))
    if isinstance(head, Sym) and isinstance(head.symbol, Variable):
        return Coordinate(head.symbol.name, head.symbol.when, tuple(classifiers))
    if isinstance(head, Sym) and isinstance(head.symbol, Constant):
        return Coordinate(head.symbol.name, None, tuple(classifiers))  # c[~]
    return None


def _selected_name(term):
    """The name a selection selects from: `x` of `x[1]`, of `x[a][1]` and of
    the path `x.y`."""
    if isinstance(term, _Path):
        term = term.heads[0]
    while isinstance(term, Select):
        term = term.family
    if isinstance(term, str):
        return term
    return term.symbol.name if isinstance(term, Sym) else to_source(term)


def _written(head):
    """A subject as written: a name, a selection, or the segments of a path
    joined by dots."""
    if isinstance(head, _Path):
        return ".".join(_written(each) for each in head.heads)
    return head if isinstance(head, str) else to_source(head)


def _component_text(component):
    """One component of a typing as written: a `!`-marked word with its
    arguments, or a set."""
    if isinstance(component, _Word):
        return to_source(Word(str(component.token)[1:], component.arguments))
    return to_source(component)


def intersection_of_sets(subject, classifiers):
    """The classifiers of a declaration whose type holds several sets,
    `β : (0,1) @ (0, R^(ρ-1))`, with those sets read as the one set the
    declared name lies in, their intersection (AMD-GRAM-004 §3; `_one_set`).
    The one set stands where the first set was written, and the words of
    the type keep their places. A type with one set, or none, is returned as
    it is. Several sets that no rule reads as one set are refused
    (`_several_sets_refusal`)."""
    sets = [c.space for c in classifiers if isinstance(c, Domain)]
    if len(sets) < 2:
        return classifiers
    refusal = _several_sets_refusal(subject, sets)
    if refusal is not None:
        raise refusal
    declared = Domain(_one_set(subject, sets))
    return _with_one_set(classifiers, lambda each: isinstance(each, Domain), declared)


def _with_one_set(components, is_set, one):
    """The components of a type with `one` where its first set stood and its
    other sets left out; the words keep their places. `is_set` tells a set
    from a word."""
    out = []
    for each in components:
        if not is_set(each):
            out.append(each)
        elif one is not None:
            out.append(one)
            one = None
    return out


def _several_sets_refusal(subject, sets):
    """The refusal of several sets in one type that no rule reads as one
    set, or None where `_one_set` reads them: a declaration of more than one
    name; a name typed inside its parentheses; a set of labels, a product or
    a set of functions among the sets, which no interval restricts; two
    sets that are no intervals; and intervals that have no number in common,
    `(0,1) @ (2,3)` or `(0,1) @ (1/2, 1/3)`, which their endpoints that are
    number literals decide (`_number_literal`). Sets that are equal terms
    count once, so that `ℝ₊₊ @ ℝ₊₊` is the one set `ℝ₊₊`. They count once
    before any other rule is read, so `(a, b) : ℝ₊₊ @ ℝ₊₊` declares both
    names in `ℝ₊₊`."""
    stem = _subject_text(subject)

    def carried():
        """What the declaration carries, each set as written; the sets are
        printed for a refusal alone."""
        written = ", ".join(f"`{to_source(each)}`" for each in sets[:-1])
        return f"the declaration of {stem} carries the sets {written} and `{to_source(sets[-1])}`"

    distinct = list(dict.fromkeys(sets))
    if len(distinct) < 2:
        return None
    if bound_name(subject) is None:
        coordinates = subject.coordinates
        if len(coordinates) == 1 and isinstance(coordinates[0], Coordinate):
            name = coordinates[0].stem
            return _refusal(
                f"{carried()}, and it types {name} inside its parentheses as well; several sets "
                f"in one type restrict a name that carries no other type",
                f"write the name without parentheses, with every set and word of its type "
                f"after one colon, as in `{name} : (0, 1) @ (0, R)`",
            )
        return _refusal(
            f"{carried()}; several sets in one type restrict one declared name, and this "
            f"declaration declares more than one",
            "declare each name on its own line, with its own sets",
        )
    for each in distinct:
        kind = _UNRESTRICTED_KINDS.get(type(each))
        if kind is not None:
            return _refusal(
                f"{carried()}, and `{to_source(each)}` is {kind}; several sets in one type are "
                f"one set of numbers and the intervals that bound it",
                f"write the one set {stem} takes its values in",
            )
    other = [each for each in distinct if not is_interval(each)]
    if len(other) > 1:
        first, second = (to_source(each) for each in other[:2])
        return _refusal(
            f"{carried()}, and `{first}` and `{second}` are no intervals; several sets in one "
            f"type are read as one set restricted by intervals, so that at most one of them "
            f"is not an interval",
            f"write one set and each further bound as an interval, as in "
            f"`{stem} : {first} @ (0, 1)`",
        )
    # the greatest lower endpoint and the least upper endpoint of the
    # intervals, each among the endpoints that are number literals, `2` or
    # `1/3`; of two equal endpoints, `0.5` and `1/2`, the open one
    intervals = [each for each in distinct if is_interval(each)]
    lowers, uppers = (
        [entry for entry in _side(intervals, negative) if _number_literal(entry[0])]
        for negative in (True, False)
    )
    if lowers and uppers:
        low, left = max(
            lowers, key=lambda entry: (_endpoint_value(entry[0]), isinstance(entry[1], Open))
        )
        high, right = min(
            uppers, key=lambda entry: (_endpoint_value(entry[0]), isinstance(entry[1], Closed))
        )
        lower, upper = _endpoint_value(low), _endpoint_value(high)
        attained = isinstance(left, Closed) and isinstance(right, Closed)
        if lower > upper or (lower == upper and not attained):
            above = "at least" if isinstance(left, Closed) else "above"
            below = "at most" if isinstance(right, Closed) else "below"
            return _refusal(
                f"{carried()}, which have no number in common: no number is {above} "
                f"{to_source(low)} and {below} {to_source(high)}; several sets in one type "
                f"are read as the one set of the values that lie in each of them",
                f"write sets that have a number in common, or the one set {stem} takes its "
                f"values in",
            )
    return None


# the sets that an interval does not restrict, each by what a refusal calls it
_UNRESTRICTED_KINDS = {
    FiniteSet: "a set of labels",
    Product: "a product",
    Functions: "a set of functions",
}


def _refuse_side_without_numbers(sign, left, right):
    """Refuses a union, written with the sign `\\/`, or a difference, written
    with `\\`, one of whose two sides is a set of labels, a product or a set
    of functions: a union and a difference are formed among sets of numbers.
    A side that is a name is admitted here; the typing walk refuses one that
    names no set of numbers (`typing.context`). The sentence quotes the two
    sides in their printed form and says which one holds no number: a member
    of the union, or the left or the right side of the difference."""
    union = sign == "\\/"
    for place, side in (("left side", left), ("right side", right)):
        kind = _UNRESTRICTED_KINDS.get(type(side))
        if kind is not None:
            whole, place = ("union", "member") if union else ("difference", place)
            raise _refusal(
                f"the {whole} `{to_source(left)} {sign} {to_source(right)}` has the {place} "
                f"`{to_source(side)}`, which is {kind}; a union and a difference are formed "
                f"among sets of numbers",
                "write a set of numbers on each side of the sign: an interval, a reserved set, "
                "a list of integers, `{1, 2}`, or a named set of numbers",
            )


def _one_set(subject, sets):
    """The one set that several sets of one type are kept as, their
    intersection: a base restricted by conditions on the declared name,
    `{β ∈ (0,1) | β < R^(ρ-1)}` (AMD-GRAM-004 §3). Each side of the
    intervals is read on its own (`_side`), so the one set is the same in
    whatever order the sets are written and however their endpoints are
    grouped into intervals.

    The base is the set that is no interval. Where every set is an
    interval, the base is the interval of the first endpoint of each side:
    the tightest number, else the infinity of that side, else the first
    formula. Every other endpoint gives one condition, the lower ones before
    the upper ones, except the infinity of its own side, `-inf` below and
    `inf` above, which restricts only where it is open and the base may hold
    it (`source.may_hold_infinity`). Where no condition is left the one set
    is the base."""
    intervals = [each for each in sets if is_interval(each)]
    other = [each for each in sets if not is_interval(each)]
    lower, upper = _side(intervals, negative=True), _side(intervals, negative=False)
    if other:
        base = other[0]
    else:
        (low, left), (high, right) = lower.pop(0), upper.pop(0)
        base = Interval(Range(left, low, high, right))
    name = bound_name(subject)
    conditions = []
    for ends, negative, strict, weak in ((lower, True, Gt, Ge), (upper, False, Lt, Le)):
        for end, bracket in ends:
            if is_infinity(end, negative) and not (
                isinstance(bracket, Open) and may_hold_infinity(base, negative)
            ):
                continue
            relation = weak() if isinstance(bracket, Closed) else strict()
            conditions.append(Rel(name, relation, end))
    return Comprehension(subject, base, tuple(conditions)) if conditions else base


def _side(intervals, negative):
    """The endpoints that intervals write on one side, the lower one with
    `negative`, each with its bracket, in the order `_one_set` reads them:
    the tightest number, the greatest lower endpoint or the least upper one;
    where no number is written, the infinity of that side; then every other
    endpoint, a formula, in the order of its printed text.

    An endpoint written several times stands once, with an open bracket
    where one of them is open, the stricter of the two. A number that is not
    the tightest and an infinity beside a number restrict nothing and are
    left out. The numbers are compared by value and none is printed, so a
    number that has no spelling, `1e400`, is ordered with the others."""
    written = [
        (each.bounds.lower, isinstance(each.bounds.left, Open))
        if negative
        else (each.bounds.upper, isinstance(each.bounds.right, Open))
        for each in intervals
    ]
    numbers = [(end, strict) for end, strict in written if is_number(end)]
    infinities = [(end, strict) for end, strict in written if is_infinity(end, negative)]
    others = [entry for entry in written if entry not in numbers and entry not in infinities]
    # a formula written several times is one key, the first in the order of
    # the text, and is strict where one of them is
    formulas = {}
    for end, strict in sorted(others, key=lambda entry: to_source(entry[0])):
        formulas[end] = formulas.get(end, False) or strict
    first = []
    if numbers:
        values = [_endpoint_value(end) for end, _ in numbers]
        tightest = max(values) if negative else min(values)
        equal = [entry for entry, value in zip(numbers, values) if value == tightest]
        # of several spellings of the tightest number, one that does not
        # depend on the order written
        written_once = min((end for end, _ in equal), key=repr)
        first = [(written_once, any(strict for _, strict in equal))]
    elif infinities:
        first = [(infinities[0][0], any(strict for _, strict in infinities))]
    return [(end, Open() if strict else Closed()) for end, strict in [*first, *formulas.items()]]


def _endpoint_value(term):
    """The value of an endpoint that is a number literal (`_number_literal`):
    a number as written, or a ratio of two integers, each with or without a
    sign. A ratio is valued in floating-point arithmetic, as a decimal is,
    so that `1/10` and `0.1` are one number."""
    if isinstance(term, Neg):
        return -_endpoint_value(term.operand)
    if isinstance(term, Div):
        return term.left.value / term.right.value
    return term.value


def _subject_text(subject):
    """The subject of a declaration as written: one name, `β` or `V[>]`, or
    the names of a tuple in parentheses, `(β, R)`."""
    names = [
        _subject_text(each.inner) if isinstance(each, Group) else _written_name(each)
        for each in subject.coordinates
    ]
    return names[0] if len(names) == 1 else "(" + ", ".join(names) + ")"


def _typed_names(subject):
    """The coordinates of a subject that carry a type inside its
    parentheses, `y` of `(y : ℝ, z)`, each by its name as written, a tuple
    inside the tuple by its names in parentheses."""
    found = []
    for each in subject.coordinates:
        if isinstance(each, Group):
            if each.classifiers:
                found.append(_subject_text(each.inner))
            found.extend(_typed_names(each.inner))
        elif each.classifiers:
            found.append(_written_name(each))
    return found


def _retired_bound_refusal(subject, components, bounds):
    """The refusal of a declaration that writes a bound after a comma,
    `γ : ℝ₊, < 2`, the spelling AMD-GRAM-004 retired; `components` are the
    components of its type as written. It quotes each bound.

    Where the declaration's sets and one interval for each bound are read as
    one set (`_one_set`), the refusal gives the type to write: the words in
    their places and, where the first set stood, that one set as `to_source`
    writes it, `ℝ₊ @ (-inf, 2)`. The interval of a bound is closed at its
    infinite end, which restricts no set, so the type declares the set the
    retired line declared. Elsewhere the refusal says how a bound is
    written."""
    name = bound_name(subject)
    signs = {symbol: sign for sign, symbol in RELATION_OF_SYMBOL.items() if sign.isascii()}
    written = " and ".join(
        f"`{signs[type(relation)]} {to_source(bound)}`"
        if name is None
        else f"`{to_source(name)} {signs[type(relation)]} {to_source(bound)}`"
        for relation, bound in bounds
    )
    infinity = Sym(Constant("inf"))
    intervals = [
        Interval(
            Range(bracket_of(relation), bound, infinity, Closed())
            if isinstance(relation, (Gt, Ge))
            else Range(Closed(), Neg(infinity), bound, bracket_of(relation))
        )
        for relation, bound in bounds
    ]
    sets = [each for each in components if not isinstance(each, _Word)] + intervals
    advice = "write each bound as an interval after `@`, as in `γ : ℝ₊ @ (-inf, 2)`"
    if (
        name is not None
        and len(sets) > len(intervals)
        and _several_sets_refusal(subject, sets) is None
    ):
        one = _one_set(subject, sets)
        typed = _with_one_set(components, lambda each: not isinstance(each, _Word), one)
        advice = "write `" + " @ ".join(_component_text(each) for each in typed) + "`"
    return _refusal(
        f"the declaration of {_subject_text(subject)} writes the "
        f"{'bound' if len(bounds) == 1 else 'bounds'} {written} after a comma, a spelling the "
        f"language has retired; a bound on a declared name is an interval written after `@` "
        f"(AMD-GRAM-004)",
        advice,
    )


def number_value(tok):
    text = str(tok)
    if text.isdecimal():
        return int(text)
    val = float(text)
    return int(val) if val.is_integer() and "." not in text else val


def _number_literal(term):
    """Whether a member of a brace list, or an endpoint of an interval, is a
    number written as a literal, with or without a sign: an integer, a
    decimal, or a ratio of two integers."""
    if isinstance(term, Neg):
        term = term.operand
    if isinstance(term, Number):
        return True
    return (
        isinstance(term, Div)
        and all(
            isinstance(part, Number) and part.value == int(part.value)
            for part in (term.left, term.right)
        )
        and term.right.value != 0
    )


def _position_literal(value, family_text, at=None):
    """The position a literal in a selector names: its value as an integer
    where the literal is a whole number, `q[2]` and `q[2.0]`. A literal that is
    no whole number, `q[2.5]`, names no position and is refused, since a
    position is counted and a numerical key is written by a name declared on
    the index set."""
    if float(value) != int(value):
        raise _refusal(
            f"the selection `{family_text}[{value}]` selects by `{value}`, which is no whole "
            f"number; a literal in a selector counts a position, and a numerical key is a "
            f"name declared on the collection's index set",
            f"a whole position, `{family_text}[{int(value)}]`, or a name declared on the index "
            f"set, `{family_text}[j]`",
            at,
        )
    return int(value)


# --- the parse-tree nodes left in a term, and its JSON encoding ---


def unlowered_parse_nodes(node):
    """Any Lark leftovers (Tree/Token) still inside a term — none if
    the lowering is total."""
    return [value for value in nodes(node) if isinstance(value, (LarkTree, Token))]


def to_json(node):
    """The canonical JSON term encoding: each node an object tagged
    with "__class__", fields in ASDL order, absent slots explicit
    null."""
    if is_dataclass(node):
        out = {"__class__": type(node).__name__}
        for f in fields(node):
            out[f.name] = to_json(getattr(node, f.name))
        return out
    if isinstance(node, tuple):
        return [to_json(v) for v in node]
    return node
