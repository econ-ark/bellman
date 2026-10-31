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

A form the grammar admits and the lowering reads no term from — a computed
selector, a selection where a name is written, a comprehension binder typed by
a role word, a condition tail with no declared set, two items under one
address, a perch mark after a selector, a word no vocabulary holds — is
refused by `_refusal`: a `ConstructionError` under the rule `syntax`, at the
line and column of the item being lowered, whose sentence quotes the author's
text and whose `advice` says what to write, so that the author reads the
refusal in the language's words. `factory/elaboration.py` adds the file and
the marked line.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from traceback import clear_frames
from types import MappingProxyType
from typing import NamedTuple

from lark import Token, Transformer, v_args
from lark import Tree as LarkTree
from lark.exceptions import VisitError

from bellman.refusals import ConstructionError
from bellman.syntax.parse import build_parser
from bellman.syntax.source import to_source
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
    field's typing (`_component_spans`). The parse tree and the identity
    records from which the table was built are discarded on return; nothing
    is stored on the term."""
    tree = build_parser().parse(text)
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
    instead, which `factory/elaboration.py` sets beneath the marked line.
    `at` is the token or span whose line and column the refusal names;
    without one, `_ToAstWithPositions.transform` gives it the position of the
    item being lowered, and the file the parse names. `rule` is the rule the
    refusal stands under, `syntax` for a form the grammar admits nowhere and
    `marginal-role-retired` for a retired role word."""
    refusal = ConstructionError(
        sentence,
        rule=rule,
        file=getattr(at, "file", None),
        line=getattr(at, "line", None),
        column=getattr(at, "column", None),
    )
    refusal.advice = advice
    return refusal


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
    token convention)."""

    file: "str | None"
    line: int
    column: int
    end_line: int
    end_column: int


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
    is written twice. A tuple of fields inside a side has no entries.
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
            if not (isinstance(entry, Typer) and isinstance(entry.typing, Signature)):
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


@dataclass(frozen=True)
class _ConditionTail:
    """The conditions written after a declaration's typing, `, < 2`, in the
    order written."""

    conditions: list


class _Condition(NamedTuple):
    """One condition of a tail: its relation and the bound it compares with."""

    relation: object
    bound: object


@dataclass(frozen=True)
class _Word:
    """A `!`-marked word of a typing, as its token, whose line and column a
    refusal of the word names."""

    token: object


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
        does not determine and is retained."""
        subject = self._subject(children[0])
        classifiers = []
        value = None
        conds = []
        for extra in children[1:]:
            if isinstance(extra, Token):
                continue  # the trailing :: annotation, read below
            if isinstance(extra, list):
                classifiers.extend(extra)  # the typing's components
            elif isinstance(extra, _DeclaredValue):
                value = extra.value
            elif isinstance(extra, _ConditionTail):
                conds = extra.conditions
        if conds:
            classifiers = condition_tail_domain(subject, classifiers, conds)
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
            f"the declaration declares `{to_source(head)}`, a selection from {name}; a "
            f"declaration names its parameter, shock or field by its name",
            f"declare the name, `{name} : …`, and select from it where it is used",
        )

    def condition_tail(self, children):
        return _ConditionTail(list(children))

    def tail_condition(self, children):
        return _Condition(relation=RELATION_OF_SYMBOL[str(children[0])](), bound=children[1])

    def tuple_subject(self, children):
        return Subject(tuple(children))

    def coordinate(self, children):
        return self._coordinate_of(children)

    def _coordinate_of(self, children):
        """The coordinate a side or a tuple subject lists: a name typed by
        its classifiers, or a tuple of coordinates as a `Group`; a
        selection is refused."""
        head = children[0]
        classifiers = children[1] if len(children) > 1 else []
        coordinate = _coordinate(head, classifiers)
        if coordinate is not None:
            return coordinate
        if isinstance(head, Subject):
            return Group(head, tuple(classifiers))
        name = _selected_name(head)
        raise _refusal(
            f"a side of a block header lists `{to_source(head)}`, a selection from {name}; "
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
            subjects = stems(subject)
        elif isinstance(subject, Sym) and isinstance(subject.symbol, Constant):
            subjects = [subject.symbol.name]  # y[~] ~ law
        else:
            name = _selected_name(subject)
            raise _refusal(
                f"the distribution is declared for `{to_source(subject)}`, a selection from "
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
        return Coordinate(children[0], None, tuple(children[1]))

    def comprehension(self, children):
        """`{c : ℝ₊₊ | c < x}`: the comprehension of a correspondence body,
        its one binder, the set that types it as the base, and the
        conditions in the order written."""
        parts = [c for c in children if not isinstance(c, Token)]
        name, components, conds = parts[0], parts[1], parts[2:]
        if len(components) != 1 or not isinstance(components[0], Domain):
            typing = " @ ".join(self._component_text(component) for component in components)
            written = f"{{{name} : {typing} | {', '.join(to_source(cond) for cond in conds)}}}"
            raise _refusal(
                f"the binder {name} of the set `{written}` is typed by `{typing}`; the binder "
                f"of a set written by comprehension is typed by one set, with no role or "
                f"perch word",
                f"type the binder by its set alone, as in `{{{name} : ℝ₊ | …}}`",
            )
        return Comprehension(Subject((Coordinate(name),)), components[0].space, tuple(conds))

    def _component_text(self, component):
        """One component of a typing as written: a set, or a `!`-marked
        word."""
        if isinstance(component, Domain):
            return to_source(component.space)
        return next(
            ("!" + word for word, make in self._VOCAB.items() if make() == component),
            type(component).__name__,
        )

    def comprehension_condition(self, children):
        return Rel(children[0], RELATION_OF_SYMBOL[str(children[1])](), children[2])

    def comprehension_equality(self, children):
        return Rel(children[0], Eq(), children[1])

    # statements and blocks
    def block(self, children):
        return Block(children[0], tuple(children[1:]))

    def header(self, children):
        return Annotation(tuple(children))

    def key_value(self, children):
        key, val = children
        return KeyValue(key, val if isinstance(val, str) else number_value(val))

    def word_tag(self, children):
        text = str(children[0])
        return Typer(Marked(Node())) if text == "!node" else Tag(text)

    def bare_tag(self, children):
        return Tag(children[0])

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
        rest = [c for c in children if not isinstance(c, (Coordinate, Group)) and c is not None]
        types = rest[0] if rest else []
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
        subject = self._subject(children[0])
        classifiers = next(extra for extra in children[1:] if isinstance(extra, list))
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
    # components; word-types classify through the vocabulary table
    def typing(self, children):
        return children[0]

    def type(self, children):
        out = []
        for c in children:
            if isinstance(c, _Word):
                out.append(self._classifier_of_word(c.token))
            else:
                out.append(Domain(c))
        return out

    def _classifier_of_word(self, word):
        """The classifier the `!`-marked word names, or a refusal of a word
        the vocabulary does not hold.

        `word` is the TAGBANG token, so the refusal carries the line and the
        column of the word itself, which `parse_with_spans` releases and
        `factory/elaboration.py` writes as the position of the refusal. The
        sentence written after the marked line stands on the refusal as
        `advice`."""
        name = str(word)[1:]
        if name in RETIRED_ROLE_WORDS:
            raise _refusal(
                f"the file writes `!{name}` here, a role retired from the language: a "
                f"backward header lists value fields and controls alone, and a derivative "
                f"of a value is written as the term `D_{{x}}V`, with `x` a state coordinate "
                f"of the value's perch, such as `D_{{m}}V` or `D_{{a}}V[>]` (AMD-MB-001 §4.1)",
                "remove the field from the header; write the line that defined it as a "
                "derivative line, `D_{m}V = …`, and read the derivative as the term `D_{a}V[>]`",
                word,
                rule="marginal-role-retired",
            )
        try:
            return self._VOCAB[name]()
        except KeyError:
            raise _refusal(
                f"the file writes `!{name}` here, which is no word-type of the language",
                "the word-types are " + ", ".join("!" + w for w in sorted(self._VOCAB)),
                word,
            ) from None

    def word_type(self, children):
        # the token itself, whose line and column a refusal of the word names
        return _Word(children[0])

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
        else:  # name key
            expr = Select(Sym(Constant(stem)), Key(first))
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
            sel = (
                Pos(_position_literal(number_value(extra), to_source(expr), extra))
                if isinstance(extra, Token)
                else Key(extra)
            )
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
        return str(children[0])


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

    def transform(self, tree):
        try:
            return super().transform(tree)
        except VisitError as wrapped:
            refusal = wrapped.orig_exc
            meta = getattr(wrapped.obj, "meta", None)
            if isinstance(refusal, ConstructionError):
                if refusal.line is None and meta is not None and not meta.empty:
                    refusal.line, refusal.column = meta.line, meta.column
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

    def _keep(self, item, meta):
        self._positions[id(item)] = _Kept(item, meta)
        return item

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

    @v_args(meta=True)
    def type(self, meta, children):
        # a word's token carries its place; a set's place is its rule's
        components = super().type(children)
        for component, child in zip(components, children):
            place = child.token if isinstance(child, _Word) else self.part_position(child)
            if place is not None:
                self._keep_part(component, place)
        return components

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
    bare name; None for any other head."""
    if isinstance(head, str):
        return Coordinate(head, None, tuple(classifiers))
    if isinstance(head, Sym) and isinstance(head.symbol, Variable):
        return Coordinate(head.symbol.name, head.symbol.when, tuple(classifiers))
    if isinstance(head, Sym) and isinstance(head.symbol, Constant):
        return Coordinate(head.symbol.name, None, tuple(classifiers))  # c[~]
    return None


def _selected_name(term):
    """The name a selection selects from: `x` of `x[1]` and of `x[a][1]`."""
    while isinstance(term, Select):
        term = term.family
    return term.symbol.name if isinstance(term, Sym) else to_source(term)


def condition_tail_domain(subject, classifiers, conds):
    """A declaration's condition tail, `γ : ℝ₊, < 2`, as the comprehension
    `{γ ∈ ℝ₊ | γ < 2}`: the first declared set of the typing restricted by the
    conditions, the other components kept. A tail after a typing that
    declares no set is refused, since a condition restricts a declared set."""
    stem = subject.coordinates[0].stem
    rels = [Rel(Sym(Constant(stem)), condition.relation, condition.bound) for condition in conds]
    out = []
    done = False
    for c in classifiers:
        if isinstance(c, Domain) and not done:
            out.append(Domain(Comprehension(subject, c.space, tuple(rels))))
            done = True
        else:
            out.append(c)
    if not done:
        written = ", ".join(f"`{to_source(rel)}`" for rel in rels)
        raise _refusal(
            f"the declaration of {stem} writes the condition {written} after a typing that "
            f"declares no set; a condition tail restricts a declared set, and this "
            f"declaration declares none",
            f"write the set before the condition, as in `{stem} : ℝ₊, < 2`, or drop the condition",
        )
    return out


def number_value(tok):
    text = str(tok)
    if text.isdecimal():
        return int(text)
    val = float(text)
    return int(val) if val.is_integer() and "." not in text else val


def _number_literal(term):
    """Whether a member of a brace list is a number written as a literal, with
    or without a sign: an integer, a decimal, or a ratio of two integers."""
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
